#!/usr/bin/env python3
"""Repository quality gate for the reusable e报表 skills package."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SETUP = SKILLS / "ebiaobiao-setup" / "scripts" / "ebiao_setup.py"
FUSION = SKILLS / "ebiaobiao-fusion-api" / "scripts" / "ebiao_fusion.py"
WIDGET = SKILLS / "ebiaobiao-widget" / "assets" / "widget-app-template"
QUICK_VALIDATE = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
SMOKE_TABLE_NAME = "Codex Skill Quality Gate Smoke"
TEMP_FILES: list[str] = []


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def redact(value: str) -> str:
    value = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer <redacted>", value)
    value = re.sub(r"(EBIAOBIAO_API_TOKEN|VIKA_API_TOKEN)=([^\s\n]+)", r"\1=<redacted>", value)
    value = re.sub(r"\bspc[A-Za-z0-9]{8,}\b", "spc<redacted>", value)
    value = re.sub(r"\bdst[A-Za-z0-9]{8,}\b", "dst<redacted>", value)
    value = re.sub(r"\brec[A-Za-z0-9]{8,}\b", "rec<redacted>", value)
    value = re.sub(r"\bfld[A-Za-z0-9]{8,}\b", "fld<redacted>", value)
    value = re.sub(r"\bviw[A-Za-z0-9]{8,}\b", "viw<redacted>", value)
    value = re.sub(r"\bwpk[A-Za-z0-9]{10}\b", "wpk<redacted>", value)
    return value


def run(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    result = subprocess.run(cmd, cwd=cwd, env=merged, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(redact((result.stdout + result.stderr).strip()))
    return result


def add(checks: list[Check], name: str, fn) -> None:
    try:
        detail = fn() or ""
        checks.append(Check(name, True, redact(str(detail))))
    except Exception as exc:  # noqa: BLE001 - quality gate should report all failures.
        checks.append(Check(name, False, redact(str(exc))))


def git_files() -> list[Path]:
    try:
        result = run(["git", "ls-files"], check=True)
        files = [ROOT / line for line in result.stdout.splitlines() if line.strip()]
        if files:
            return files
    except Exception:
        pass

    excluded_dirs = {".git", "node_modules", "dist", "__pycache__", "widgets", "docs"}
    excluded_suffixes = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".ico"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in rel.parts):
            continue
        if path.suffix.lower() in excluded_suffixes:
            continue
        if path.name == "package-lock.json":
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_skills() -> str:
    if not QUICK_VALIDATE.exists():
        raise RuntimeError(f"missing quick_validate.py: {QUICK_VALIDATE}")
    names = []
    for skill in sorted(SKILLS.glob("ebiaobiao-*")):
        if not (skill / "SKILL.md").exists():
            continue
        run([sys.executable, str(QUICK_VALIDATE), str(skill)])
        names.append(skill.name)
    return f"validated {len(names)} skills"


def check_python_compile() -> str:
    files = sorted([*SKILLS.glob("**/*.py"), *ROOT.glob("tools/*.py")])
    run([sys.executable, "-m", "py_compile", *[str(path) for path in files]])
    return f"compiled {len(files)} python files"


def check_sensitive_text() -> str:
    failures: list[str] = []
    suspicious_id = re.compile(r"\b(?:spc|dst|rec|fld|viw)(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{8,}\b|\bwpk(?!Replace001\b)(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{10}\b")
    screenshot_marker = "docs/" + "screenshots/"
    for path in git_files():
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico"}:
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(ROOT)
        for match in suspicious_id.finditer(text):
            token = match.group(0)
            if "Replace" not in token and "XXXX" not in token and "redacted" not in token:
                failures.append(f"{rel} contains real-looking id {token}")
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(r"^(EBIAOBIAO_API_TOKEN|VIKA_API_TOKEN)=\S+", line) and "<redacted>" not in line:
                failures.append(f"{rel}:{line_no} contains token-like env assignment")
            if screenshot_marker in line:
                failures.append(f"{rel}:{line_no} references local screenshot output")
    if failures:
        raise RuntimeError("; ".join(failures))
    return "tracked text is sanitized"


def check_install_scripts() -> str:
    with tempfile.TemporaryDirectory(prefix="ebiao-install.") as tmp:
        target = Path(tmp) / "skills"
        run(["bash", "install.sh", "--target", str(target), "--force"])
        count = len(list(target.glob("ebiaobiao-*")))
        if count != 6:
            raise RuntimeError(f"install.sh installed {count} skills, expected 6")
        forbidden = ["node_modules", "dist", "__pycache__", "package-lock.json"]
        copied_forbidden = [path for path in target.rglob("*") if path.name in forbidden or path.suffix == ".pyc"]
        if copied_forbidden:
            raise RuntimeError(f"install.sh copied generated artifacts: {copied_forbidden[:3]}")
    ps = ROOT / "install.ps1"
    text = read_text(ps)
    required = ["param(", "Copy-Item", "Get-ChildItem", "ebiaobiao-*"]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"install.ps1 missing markers: {missing}")
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if pwsh:
        with tempfile.TemporaryDirectory(prefix="ebiao-install-ps.") as tmp:
            target = Path(tmp) / "skills"
            run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps), "-Target", str(target), "-Force"])
        return "bash install passed; PowerShell install executed"
    return "bash install passed; PowerShell static check only"


def no_secret_env() -> dict[str, str]:
    env = {"EBIAOBIAO_NO_OPEN": "1"}
    for key in [
        "EBIAOBIAO_API_TOKEN",
        "VIKA_API_TOKEN",
        "EBIAOBIAO_SPACE_ID",
        "EBIAOBIAO_PROFILE",
        "EBIAOBIAO_HOST",
        "EBIAOBIAO_API_BASE_URL",
    ]:
        env[key] = ""
    return env


def check_setup_flow() -> str:
    with tempfile.TemporaryDirectory(prefix="ebiao-setup.") as tmp:
        target = Path(tmp)
        env = no_secret_env()
        run([sys.executable, str(SETUP), "init", "--target", str(target), "--skip-widget-env", "--no-open"], env=env)
        run([sys.executable, str(SETUP), "space", "add", "finance", "--target", str(target), "--no-open"], env=env)
        run([sys.executable, str(SETUP), "space", "list", "--target", str(target)], env=env)
        run([sys.executable, str(SETUP), "space", "use", "finance", "--target", str(target)], env=env)
    return "init and space switching work without chat secrets"


def check_fusion_dry_run() -> str:
    env = os.environ.copy()
    for key in no_secret_env():
        env.pop(key, None)
    config = run([sys.executable, str(FUSION), "config", "check"], cwd=Path(tempfile.gettempdir()), env=env)
    status = json.loads(config.stdout)
    if status.get("write_enabled"):
        raise RuntimeError("no-secret config unexpectedly enables writes")
    result = run(
        [
            sys.executable,
            str(FUSION),
            "create-records",
            "dstXXXXXXXX",
            '[{"fields":{"标题":"离线测试"}}]',
            "--dry-run",
        ],
        cwd=Path(tempfile.gettempdir()),
        env=env,
    )
    payload = json.loads(result.stdout)
    if not payload.get("dryRun") and not payload.get("results"):
        raise RuntimeError("dry-run output missing dryRun marker")
    cleanup = run(
        [sys.executable, str(FUSION), "delete-empty-records", "dstXXXXXXXX", "--dry-run"],
        cwd=Path(tempfile.gettempdir()),
        env=env,
    )
    cleanup_payload = json.loads(cleanup.stdout)
    if not cleanup_payload.get("dryRun"):
        raise RuntimeError("delete-empty-records dry-run output missing dryRun marker")
    return "no-token config is blocked; write dry-run works"


def check_widget_template(run_build: bool) -> str:
    package = json.loads(read_text(WIDGET / "package.json"))
    config = json.loads(read_text(WIDGET / "widget.config.json"))
    app = read_text(WIDGET / "src" / "App.tsx")
    css = read_text(WIDGET / "src" / "style.css")

    expected = {
        "@apitable/widget-sdk": "1.10.1",
        "react": "18.2.0",
        "react-dom": "18.2.0",
    }
    for dep, version in expected.items():
        if package.get("dependencies", {}).get(dep) != version:
            raise RuntimeError(f"{dep} must be pinned to {version}")
    if package.get("devDependencies", {}).get("@apitable/widget-cli") != "1.3.0":
        raise RuntimeError("@apitable/widget-cli must be pinned to 1.3.0")
    required_config = ["packageId", "spaceId", "version", "entry", "name", "description", "icon", "cover", "authorName", "authorIcon", "authorLink", "authorEmail", "sandbox"]
    missing = [key for key in required_config if key not in config]
    if missing:
        raise RuntimeError(f"widget.config.json missing {missing}")
    if not re.fullmatch(r"wpk[A-Za-z0-9]{10}", config["packageId"]):
        raise RuntimeError("packageId must be wpk + 10 letters/numbers")
    if "import styles from './style.css'" not in app or "import './style.css'" in app:
        raise RuntimeError("template must use CSS Modules import")
    for marker in [":global(html)", ":global(body)", ":global(#root)", "height: 100vh", "overflow: auto", "-webkit-overflow-scrolling: touch"]:
        if marker not in css:
            raise RuntimeError(f"style.css missing scroll marker: {marker}")
    detail = "static widget checks passed"
    if run_build:
        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("npm not found for widget build")
        run([npm, "install", "--no-audit", "--no-fund", "--package-lock=false"], cwd=WIDGET)
        run([npm, "run", "build"], cwd=WIDGET)
        detail += "; npm build passed"
    return detail


def extract_ids(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        if re.fullmatch(prefix + r"[A-Za-z0-9]{8,}", value):
            found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(extract_ids(item, prefix))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(extract_ids(item, prefix))
    return found


def write_json_temp(value: Any) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
    with handle:
        json.dump(value, handle, ensure_ascii=False)
    TEMP_FILES.append(handle.name)
    return handle.name


def fusion(args: list[str]) -> Any:
    result = run([sys.executable, str(FUSION), *args])
    return json.loads(result.stdout)


def live_status() -> dict[str, Any]:
    return fusion(["config", "check"])


def find_or_create_smoke_datasheet() -> str:
    try:
        search = fusion(["search-nodes", "--type", "Datasheet", "--query", SMOKE_TABLE_NAME])
        ids = extract_ids(search, "dst")
        if ids:
            return ids[0]
    except Exception:
        pass
    payload = {
        "name": SMOKE_TABLE_NAME,
        "description": "Reusable development-space smoke table for e报表 skill validation.",
        "fields": [
            {"type": "SingleText", "name": "标题", "property": {"defaultValue": ""}},
            {"type": "SingleText", "name": "状态", "property": {"defaultValue": ""}},
            {"type": "Checkbox", "name": "确认", "property": {"icon": "white_check_mark"}},
        ],
    }
    created = fusion(["create-datasheet", write_json_temp(payload), "--clean-empty-records"])
    ids = extract_ids(created, "dst")
    if not ids:
        raise RuntimeError(f"could not extract datasheet id from create response: {redact(json.dumps(created, ensure_ascii=False))}")
    return ids[0]


def check_live_write() -> str:
    status = live_status()
    if not status.get("write_enabled"):
        raise RuntimeError("live write requested but config is not write_enabled")
    fusion(["spaces"])
    fusion(["nodes"])
    datasheet_id = find_or_create_smoke_datasheet()
    fusion(["fields", datasheet_id])
    fusion(["views", datasheet_id])
    fusion(["records", datasheet_id, "--page-size", "10"])

    field_name = "临时质量门字段_" + str(int(time.time()))
    field_payload = {"type": "SingleText", "name": field_name, "property": {"defaultValue": ""}}
    field = fusion(["create-field", datasheet_id, write_json_temp(field_payload)])
    field_ids = extract_ids(field, "fld")

    record_payload = [{"fields": {"标题": "quality gate smoke", "状态": "待处理", "确认": True}}]
    created = fusion(["create-records", datasheet_id, write_json_temp(record_payload)])
    record_ids = extract_ids(created, "rec")
    if not record_ids:
        raise RuntimeError("create-records did not return a record id")
    record_id = record_ids[0]
    update_payload = [{"recordId": record_id, "fields": {"状态": "已完成"}}]
    fusion(["update-records", datasheet_id, write_json_temp(update_payload)])
    fusion(["delete-records", datasheet_id, record_id])

    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as handle:
        handle.write("e报表 skill quality gate attachment smoke\n")
        attachment_path = handle.name
    TEMP_FILES.append(attachment_path)
    fusion(["upload-attachment", datasheet_id, attachment_path])

    if field_ids:
        fusion(["delete-field", datasheet_id, field_ids[0]])
    return f"live smoke passed on {redact(datasheet_id)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run e报表 skills repository quality checks")
    parser.add_argument("--live", choices=["auto", "never", "write"], default="auto", help="live-write policy")
    parser.add_argument("--widget-build", action="store_true", help="install widget deps without package-lock and run npm build")
    args = parser.parse_args()

    checks: list[Check] = []
    add(checks, "skill frontmatter", check_skills)
    add(checks, "python compile", check_python_compile)
    add(checks, "sensitive text scan", check_sensitive_text)
    add(checks, "install scripts", check_install_scripts)
    add(checks, "setup flow", check_setup_flow)
    add(checks, "fusion dry-run", check_fusion_dry_run)
    add(checks, "widget template", lambda: check_widget_template(args.widget_build))

    if args.live != "never":
        try:
            status = live_status()
            if args.live == "write" or status.get("write_enabled"):
                add(checks, "live fusion smoke", check_live_write)
            else:
                checks.append(Check("live fusion smoke", True, "skipped: config is not write_enabled"))
        except Exception as exc:  # noqa: BLE001
            if args.live == "write":
                checks.append(Check("live fusion smoke", False, redact(str(exc))))
            else:
                checks.append(Check("live fusion smoke", True, "skipped: " + redact(str(exc))))

    failed = [check for check in checks if not check.ok]
    for check in checks:
        marker = "PASS" if check.ok else "FAIL"
        print(f"[{marker}] {check.name}: {check.detail}")
    print(f"summary: {len(checks) - len(failed)} passed, {len(failed)} failed")
    for path in TEMP_FILES:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
