#!/usr/bin/env python3
"""One-entry setup and profile manager for report projects."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_HOST = ""
DEFAULT_BASE = ""
SKILL_ROOT = Path(__file__).resolve().parents[2]
SETUP_ROOT = SKILL_ROOT / "ebiaobiao-setup"
WIDGET_TEMPLATE = SKILL_ROOT / "ebiaobiao-widget" / "assets" / "widget-app-template"


def project_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def env_quote(value: str) -> str:
    if not value:
        return ""
    if any(ch.isspace() for ch in value) or "#" in value:
        return json.dumps(value, ensure_ascii=False)
    return value


def read_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = [
        "EBIAOBIAO_HOST",
        "EBIAOBIAO_API_BASE_URL",
        "EBIAOBIAO_SPACE_ID",
        "EBIAOBIAO_API_TOKEN",
        "EBIAOBIAO_PROFILE",
        "EBIAOBIAO_SSL_VERIFY",
    ]
    lines = [
        "# Report platform configuration",
        "# Do not commit this file when it contains a real token.",
        "",
    ]
    for key in ordered:
        if key in values:
            lines.append(f"{key}={env_quote(values.get(key, ''))}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def profile_dir(target: Path) -> Path:
    return target / ".ebiaobiao" / "profiles"


def profile_path(target: Path, name: str) -> Path:
    safe = name.strip()
    if not safe or "/" in safe or "\\" in safe or safe.startswith("."):
        raise SystemExit("profile name must be a simple file-safe name")
    return profile_dir(target) / f"{safe}.env"


def update_gitignore(target: Path) -> None:
    path = target / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    for item in [
        ".env.local",
        ".env.*.local",
        ".ebiaobiao/profiles/*.env",
        "node_modules/",
        "dist/",
        "*.log",
    ]:
        if item not in lines:
            lines.append(item)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_example(target: Path) -> None:
    write_env(target / ".env.local.example", {
        "EBIAOBIAO_HOST": DEFAULT_HOST,
        "EBIAOBIAO_API_BASE_URL": DEFAULT_BASE,
        "EBIAOBIAO_SPACE_ID": "",
        "EBIAOBIAO_API_TOKEN": "",
        "EBIAOBIAO_PROFILE": "dev",
        "EBIAOBIAO_SSL_VERIFY": "0",
    })


def profile_values(args: argparse.Namespace, old: dict[str, str] | None = None) -> dict[str, str]:
    base = dict(old or {})
    host = (args.host or base.get("EBIAOBIAO_HOST") or DEFAULT_HOST).rstrip("/")
    api_base_url = args.api_base_url or base.get("EBIAOBIAO_API_BASE_URL") or (host + "/fusion/v1" if host else DEFAULT_BASE)
    values = {
        "EBIAOBIAO_HOST": host,
        "EBIAOBIAO_API_BASE_URL": api_base_url.rstrip("/"),
        "EBIAOBIAO_SPACE_ID": args.space_id if args.space_id is not None else base.get("EBIAOBIAO_SPACE_ID", ""),
        "EBIAOBIAO_API_TOKEN": args.token if args.token is not None else base.get("EBIAOBIAO_API_TOKEN", ""),
        "EBIAOBIAO_PROFILE": args.write_profile or base.get("EBIAOBIAO_PROFILE") or "dev",
        "EBIAOBIAO_SSL_VERIFY": args.ssl_verify if args.ssl_verify is not None else base.get("EBIAOBIAO_SSL_VERIFY", "0"),
    }
    return values


def set_active_profile(target: Path, name: str) -> None:
    state = target / ".ebiaobiao" / "config.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"active_profile": name}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def active_profile(target: Path) -> str | None:
    state = target / ".ebiaobiao" / "config.json"
    if not state.exists():
        return None
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("active_profile")
    except json.JSONDecodeError:
        return None


def install_widget_env(target: Path, install: bool) -> None:
    widget_dir = target / "widgets" / "_ebiaobiao_widget_starter"
    if not widget_dir.exists():
        shutil.copytree(WIDGET_TEMPLATE, widget_dir)
    if install:
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=widget_dir, check=True)
    print(f"widget_starter={widget_dir}")


def open_config_file(path: Path) -> None:
    if os.environ.get("EBIAOBIAO_NO_OPEN") == "1":
        print(f"edit_config={path}")
        return
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-t", str(path)])
            print(f"opened_config={path}")
            return
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            print(f"opened_config={path}")
            return
        editor = os.environ.get("EDITOR")
        if editor:
            subprocess.run([*shlex.split(editor), str(path)], check=False)
            print(f"opened_config={path}")
            return
        if shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(path)])
            print(f"opened_config={path}")
            return
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"open_config_warning={exc}", file=sys.stderr)
    print(f"edit_config={path}")


def maybe_open_missing_config(path: Path, values: dict[str, str], no_open: bool) -> None:
    missing = []
    if not values.get("EBIAOBIAO_API_TOKEN"):
        missing.append("EBIAOBIAO_API_TOKEN")
    if not values.get("EBIAOBIAO_HOST") or not values.get("EBIAOBIAO_API_BASE_URL"):
        missing.append("EBIAOBIAO_HOST")
    if not values.get("EBIAOBIAO_SPACE_ID"):
        missing.append("EBIAOBIAO_SPACE_ID")
    if not missing:
        return
    print("missing=" + ",".join(missing))
    if not no_open:
        open_config_file(path)


def cmd_init(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    target.mkdir(parents=True, exist_ok=True)
    update_gitignore(target)
    write_example(target)
    values = profile_values(args)
    write_env(profile_path(target, args.profile), values)
    write_env(target / ".env.local", values)
    set_active_profile(target, args.profile)
    if not args.skip_widget_env:
        try:
            install_widget_env(target, install=not args.no_npm_install)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"widget_env_warning={exc}", file=sys.stderr)
    print(f"target={target}")
    print(f"active_profile={args.profile}")
    print("token=present" if values.get("EBIAOBIAO_API_TOKEN") else "token=missing")
    print("space_id=present" if values.get("EBIAOBIAO_SPACE_ID") else "space_id=missing")
    maybe_open_missing_config(target / ".env.local", values, args.no_open)


def cmd_profile_set(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    old = read_env(profile_path(target, args.name))
    values = profile_values(args, old)
    write_env(profile_path(target, args.name), values)
    if args.use:
        write_env(target / ".env.local", values)
        set_active_profile(target, args.name)
    update_gitignore(target)
    print(f"profile={args.name}")
    print("updated=true")
    if args.use:
        print("active=true")
        maybe_open_missing_config(target / ".env.local", values, args.no_open)
    else:
        maybe_open_missing_config(profile_path(target, args.name), values, args.no_open)


def cmd_profile_use(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    path = profile_path(target, args.name)
    if not path.exists():
        raise SystemExit(f"profile not found: {args.name}")
    write_env(target / ".env.local", read_env(path))
    set_active_profile(target, args.name)
    print(f"active_profile={args.name}")
    print(f"env_file={target / '.env.local'}")


def cmd_profile_list(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    active = active_profile(target)
    profiles = sorted(profile_dir(target).glob("*.env"))
    if not profiles:
        print("(no profiles)")
        return
    for path in profiles:
        name = path.stem
        values = read_env(path)
        marker = "*" if name == active else " "
        token = "token" if values.get("EBIAOBIAO_API_TOKEN") else "no-token"
        space = values.get("EBIAOBIAO_SPACE_ID") or "no-space"
        print(f"{marker} {name}\t{space}\t{token}")


def cmd_profile_import(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    env_file = target / ".env.local"
    values = read_env(env_file)
    if not values:
        raise SystemExit(f"cannot import profile: {env_file} is missing or empty")
    write_env(profile_path(target, args.name), values)
    if args.use:
        set_active_profile(target, args.name)
    update_gitignore(target)
    print(f"profile={args.name}")
    print(f"imported_from={env_file}")
    if args.use:
        print("active=true")


def cmd_check(args: argparse.Namespace) -> None:
    target = project_root(args.target)
    check = SETUP_ROOT / "scripts" / "check_config.py"
    extra = ["--json"] if args.json else []
    subprocess.run([sys.executable, str(check), *extra], cwd=target, check=True)


def cmd_widget_env(args: argparse.Namespace) -> None:
    install_widget_env(project_root(args.target), install=not args.no_npm_install)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize and switch report development profiles")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_profile_fields(p: argparse.ArgumentParser) -> None:
        p.add_argument("--token", help="personal API token")
        p.add_argument("--space-id", help="target space id")
        p.add_argument("--host", default=DEFAULT_HOST)
        p.add_argument("--api-base-url")
        p.add_argument("--write-profile", default="dev", help="EBIAOBIAO_PROFILE value; dev enables guarded writes")
        p.add_argument("--ssl-verify", choices=["0", "1"], help="0 when local certificate verification blocks development checks")
        p.add_argument("--no-open", action="store_true", help="do not open config file when token or space id is missing")

    p = sub.add_parser("init", help="create .env.local, profile storage, gitignore, and widget starter")
    p.add_argument("--target", default=".")
    p.add_argument("--profile", default="dev")
    p.add_argument("--skip-widget-env", action="store_true")
    p.add_argument("--no-npm-install", action="store_true", help="copy widget starter but do not run npm install")
    add_profile_fields(p)
    p.set_defaults(func=cmd_init)

    profile = sub.add_parser("profile", help="manage saved token/space profiles")
    psub = profile.add_subparsers(dest="profile_cmd", required=True)
    p = psub.add_parser("set")
    p.add_argument("name")
    p.add_argument("--target", default=".")
    p.add_argument("--use", action="store_true", help="also make this profile active")
    add_profile_fields(p)
    p.set_defaults(func=cmd_profile_set)
    p = psub.add_parser("use")
    p.add_argument("name")
    p.add_argument("--target", default=".")
    p.set_defaults(func=cmd_profile_use)
    p = psub.add_parser("list")
    p.add_argument("--target", default=".")
    p.set_defaults(func=cmd_profile_list)
    p = psub.add_parser("import")
    p.add_argument("name")
    p.add_argument("--target", default=".")
    p.add_argument("--use", action="store_true", help="make imported profile active")
    p.set_defaults(func=cmd_profile_import)

    space = sub.add_parser("space", help="friendly aliases for multi-space profile management")
    ssub = space.add_subparsers(dest="space_cmd", required=True)
    p = ssub.add_parser("add")
    p.add_argument("name")
    p.add_argument("--target", default=".")
    p.add_argument("--use", action="store_true", help="also make this space active")
    add_profile_fields(p)
    p.set_defaults(func=cmd_profile_set)
    p = ssub.add_parser("use")
    p.add_argument("name")
    p.add_argument("--target", default=".")
    p.set_defaults(func=cmd_profile_use)
    p = ssub.add_parser("list")
    p.add_argument("--target", default=".")
    p.set_defaults(func=cmd_profile_list)

    p = sub.add_parser("check")
    p.add_argument("--target", default=".")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("widget-env", help="copy widget starter and optionally install dependencies")
    p.add_argument("--target", default=".")
    p.add_argument("--no-npm-install", action="store_true")
    p.set_defaults(func=cmd_widget_env)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
