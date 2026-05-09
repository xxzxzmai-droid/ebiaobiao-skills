#!/usr/bin/env python3
"""Validate private e报表 development configuration without making network calls."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_HOST = "https://app.ehv.csg.cn:7886"
DEFAULT_BASE = DEFAULT_HOST + "/fusion/v1"


def host_configured(host: str, base_url: str) -> bool:
    return host.startswith("https://") and base_url.startswith("https://")


def load_env_local(start_dir: str | None = None) -> str | None:
    current = Path(start_dir or os.getcwd()).resolve()
    for directory in [current, *current.parents]:
        path = directory / ".env.local"
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return str(path)
    return None


def collect() -> dict:
    env_file = load_env_local()
    token_source = "EBIAOBIAO_API_TOKEN" if os.environ.get("EBIAOBIAO_API_TOKEN") else (
        "VIKA_API_TOKEN" if os.environ.get("VIKA_API_TOKEN") else None
    )
    token = os.environ.get("EBIAOBIAO_API_TOKEN") or os.environ.get("VIKA_API_TOKEN")
    host = os.environ.get("EBIAOBIAO_HOST", DEFAULT_HOST).rstrip("/")
    base_url = os.environ.get("EBIAOBIAO_API_BASE_URL", host + "/fusion/v1").rstrip("/")
    space_id = os.environ.get("EBIAOBIAO_SPACE_ID")
    profile = os.environ.get("EBIAOBIAO_PROFILE", "")
    configured_host = host_configured(host, base_url)
    can_write = profile == "dev" and bool(token) and bool(space_id) and configured_host
    issues = []
    if not token:
        issues.append("missing EBIAOBIAO_API_TOKEN or VIKA_API_TOKEN")
    if not space_id:
        issues.append("missing EBIAOBIAO_SPACE_ID; write commands will be blocked")
    if not configured_host:
        issues.append("EBIAOBIAO_HOST and EBIAOBIAO_API_BASE_URL must use HTTPS")
    if profile != "dev":
        issues.append("EBIAOBIAO_PROFILE is not dev; write commands will be blocked")
    return {
        "env_file": env_file,
        "host": host,
        "api_base_url": base_url,
        "space_id_present": bool(space_id),
        "token_present": bool(token),
        "token_source": token_source,
        "profile": profile or None,
        "host_configured": configured_host,
        "write_enabled": can_write,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check e报表 local configuration")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result = collect()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("e报表 configuration")
    print(f"- env file: {result['env_file'] or '(none)'}")
    print(f"- host: {result['host']}")
    print(f"- api base: {result['api_base_url']}")
    print(f"- token: {'present via ' + result['token_source'] if result['token_present'] else 'missing'}")
    print(f"- space id: {'present' if result['space_id_present'] else 'missing'}")
    print(f"- profile: {result['profile'] or '(unset)'}")
    print(f"- write enabled: {'yes' if result['write_enabled'] else 'no'}")
    if result["issues"]:
        print("issues:")
        for issue in result["issues"]:
            print(f"- {issue}")


if __name__ == "__main__":
    main()
