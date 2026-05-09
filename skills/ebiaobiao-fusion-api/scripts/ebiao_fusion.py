#!/usr/bin/env python3
"""Report Fusion API CLI with guarded write operations."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_HOST = ""
DEFAULT_BASE_URL = ""
WRITE_COMMANDS = {
    "create-datasheet",
    "create-field",
    "delete-field",
    "create-records",
    "update-records",
    "delete-records",
    "delete-empty-records",
    "upload-attachment",
}


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


def get_token(explicit: str | None = None) -> tuple[str | None, str | None]:
    if explicit:
        return explicit, "--token"
    if os.environ.get("EBIAOBIAO_API_TOKEN"):
        return os.environ["EBIAOBIAO_API_TOKEN"], "EBIAOBIAO_API_TOKEN"
    if os.environ.get("VIKA_API_TOKEN"):
        return os.environ["VIKA_API_TOKEN"], "VIKA_API_TOKEN"
    return None, None


def load_json_arg(value: str) -> Any:
    stripped = value.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(value)
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def chunks(items: list[Any], size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def print_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    print()


def extract_ids(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, str) and value.startswith(prefix):
        found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(extract_ids(item, prefix))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(extract_ids(item, prefix))
    return found


def is_empty_cell(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def is_empty_record(record: dict[str, Any]) -> bool:
    fields = record.get("fields") or {}
    if not isinstance(fields, dict) or not fields:
        return True
    return all(is_empty_cell(value) for value in fields.values())


class Config:
    def __init__(self, args: argparse.Namespace):
        load_env_local()
        host = args.host or os.environ.get("EBIAOBIAO_HOST") or DEFAULT_HOST
        self.host = host.rstrip("/")
        fallback_base = self.host + "/fusion/v1" if self.host else DEFAULT_BASE_URL
        self.base_url = (args.base_url or os.environ.get("EBIAOBIAO_API_BASE_URL") or fallback_base).rstrip("/")
        self.space_id = args.space_id or os.environ.get("EBIAOBIAO_SPACE_ID")
        self.profile = args.profile or os.environ.get("EBIAOBIAO_PROFILE", "")
        self.token, self.token_source = get_token(args.token)
        self.sleep = args.sleep
        self.dry_run = args.dry_run
        self.host_configured = (
            self.host.startswith("https://")
            and self.base_url.startswith("https://")
        )
        verify_raw = os.environ.get("EBIAOBIAO_SSL_VERIFY", os.environ.get("VIKA_SSL_VERIFY"))
        default_verify = "1"
        verify = (verify_raw if verify_raw is not None else default_verify).lower() not in {"0", "false", "no"}
        self.context = None if verify else ssl._create_unverified_context()

    def status(self) -> dict[str, Any]:
        write_enabled = self.profile == "dev" and bool(self.token) and bool(self.space_id) and self.host_configured
        issues = []
        if not self.token:
            issues.append("missing EBIAOBIAO_API_TOKEN or VIKA_API_TOKEN")
        if not self.space_id:
            issues.append("missing EBIAOBIAO_SPACE_ID")
        if self.profile != "dev":
            issues.append("EBIAOBIAO_PROFILE is not dev")
        if not self.host_configured:
            issues.append("missing EBIAOBIAO_HOST or EBIAOBIAO_API_BASE_URL; both must use HTTPS")
        return {
            "host": self.host,
            "api_base_url": self.base_url,
            "space_id_present": bool(self.space_id),
            "token_present": bool(self.token),
            "token_source": self.token_source,
            "profile": self.profile or None,
            "host_configured": self.host_configured,
            "write_enabled": write_enabled,
            "issues": issues,
        }

    def require_token(self) -> None:
        if not self.token:
            raise SystemExit("missing token: set EBIAOBIAO_API_TOKEN or VIKA_API_TOKEN")

    def require_write(self, command: str, explicit_space_id: str | None = None) -> None:
        if self.dry_run:
            return
        self.require_token()
        target_space = explicit_space_id or self.space_id
        if self.profile != "dev":
            raise SystemExit(f"{command} blocked: set EBIAOBIAO_PROFILE=dev for development-space writes")
        if not self.host_configured:
            raise SystemExit(f"{command} blocked: set EBIAOBIAO_HOST and EBIAOBIAO_API_BASE_URL to HTTPS values")
        if not target_space:
            raise SystemExit(f"{command} blocked: set EBIAOBIAO_SPACE_ID or pass --space-id")


class Client:
    def __init__(self, config: Config, require_token: bool = True):
        if require_token:
            config.require_token()
        self.config = config

    def request(self, method: str, path: str, params: dict[str, Any] | None = None, body: Any = None,
                headers: dict[str, str] | None = None, data: bytes | None = None, retries: int = 3) -> Any:
        url = self.config.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        req_headers = {"Authorization": f"Bearer {self.config.token}"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        if headers:
            req_headers.update(headers)
        if self.config.dry_run and method != "GET":
            return {"success": True, "dryRun": True, "method": method, "url": url, "body": body}
        for attempt in range(retries):
            req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=60, context=self.config.context) as resp:
                    raw = resp.read()
                    if raw.startswith(b"{") or "application/json" in resp.headers.get("content-type", ""):
                        result = json.loads(raw.decode("utf-8"))
                    else:
                        result = {"success": True, "raw": raw.decode("utf-8", "replace")}
                    if isinstance(result, dict) and result.get("success") is False:
                        raise RuntimeError(json.dumps(result, ensure_ascii=False))
                    return result
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", "replace")
                if exc.code == 429 and attempt + 1 < retries:
                    time.sleep((attempt + 1) * 1.5)
                    continue
                raise RuntimeError(f"HTTP {exc.code}: {raw}") from exc
            except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
                if attempt + 1 < retries:
                    time.sleep((attempt + 1) * 1.5)
                    continue
                raise RuntimeError(f"network error after {retries} attempts: {exc}") from exc
        raise RuntimeError("request failed after retries")

    def chunked(self, method: str, path: str, key: str, items: list[Any], size: int = 10, params: dict[str, Any] | None = None) -> Any:
        results = []
        for part in chunks(items, size):
            results.append(self.request(method, path, params=params, body={key: part}))
            time.sleep(self.config.sleep)
        return {"success": True, "chunks": len(results), "results": results}

    def delete_empty_records(self, datasheet_id: str, limit: int = 1000) -> Any:
        if self.config.dry_run:
            return {"success": True, "dryRun": True, "method": "DELETE", "datasheetId": datasheet_id, "target": "empty records"}
        payload = self.request("GET", f"/datasheets/{datasheet_id}/records", params={
            "fieldKey": "name",
            "cellFormat": "json",
            "pageSize": min(limit, 1000),
            "pageNum": 1,
        })
        records = payload.get("data", {}).get("records", [])
        ids = [record.get("recordId") for record in records if isinstance(record, dict) and is_empty_record(record)]
        ids = [record_id for record_id in ids if isinstance(record_id, str)]
        if not ids:
            return {"success": True, "deleted": 0, "recordIds": []}
        results = []
        for part in chunks(ids, 10):
            results.append(self.request("DELETE", f"/datasheets/{datasheet_id}/records", params={"recordIds": ",".join(part)}))
        return {"success": True, "deleted": len(ids), "recordIds": ids, "results": results}


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--token", help="API token; prefer EBIAOBIAO_API_TOKEN")
    parser.add_argument("--host", help="default: EBIAOBIAO_HOST")
    parser.add_argument("--base-url", help="default: EBIAOBIAO_API_BASE_URL or host/fusion/v1")
    parser.add_argument("--space-id", help="target space id; default EBIAOBIAO_SPACE_ID")
    parser.add_argument("--profile", help="default EBIAOBIAO_PROFILE")
    parser.add_argument("--sleep", type=float, default=0.25, help="seconds between chunked writes")
    parser.add_argument("--dry-run", action="store_true", help="print write payloads without mutation")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report Fusion API CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("config")
    psub = p.add_subparsers(dest="subcmd", required=True)
    add_common(psub.add_parser("check"))
    for name in ["spaces", "nodes"]:
        p = sub.add_parser(name)
        add_common(p)
    p = sub.add_parser("node-detail")
    add_common(p)
    p.add_argument("node_id")
    p = sub.add_parser("fields")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("--field-key", choices=["name", "id"], default="name")
    p = sub.add_parser("views")
    add_common(p)
    p.add_argument("datasheet_id")
    p = sub.add_parser("records")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("--view-id")
    p.add_argument("--field-key", choices=["name", "id"], default="name")
    p.add_argument("--fields")
    p.add_argument("--filter-by-formula")
    p.add_argument("--cell-format", choices=["json", "string"], default="json")
    p.add_argument("--page-size", type=int, default=1000)
    p.add_argument("--page-num", type=int, default=1)
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("search-nodes")
    add_common(p)
    p.add_argument("--type", choices=["Folder", "Datasheet", "Form", "Dashboard", "Mirror"], default="Datasheet")
    p.add_argument("--query")
    p.add_argument("--permissions", help="comma-separated permissions, e.g. 0,1,2,3")
    p = sub.add_parser("create-datasheet")
    add_common(p)
    p.add_argument("payload_json")
    p.add_argument("--clean-empty-records", action="store_true", help="delete blank default rows after datasheet creation")
    p = sub.add_parser("create-field")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("payload_json")
    p = sub.add_parser("delete-field")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("field_id")
    p = sub.add_parser("create-records")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("records_json")
    p.add_argument("--view-id")
    p = sub.add_parser("update-records")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("records_json")
    p = sub.add_parser("delete-records")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("record_ids")
    p = sub.add_parser("delete-empty-records")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("--limit", type=int, default=1000, help="max first-page records to inspect")
    p = sub.add_parser("upload-attachment")
    add_common(p)
    p.add_argument("datasheet_id")
    p.add_argument("file")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = Config(args)
    if args.cmd == "config":
        print_json(config.status())
        return
    if args.cmd in WRITE_COMMANDS:
        config.require_write(args.cmd, args.space_id)
    dry_run_write = config.dry_run and args.cmd in WRITE_COMMANDS
    client = Client(config, require_token=not dry_run_write)
    space_id = args.space_id or config.space_id
    if args.cmd == "spaces":
        result = client.request("GET", "/spaces")
    elif args.cmd == "nodes":
        if not space_id:
            raise SystemExit("nodes requires --space-id or EBIAOBIAO_SPACE_ID")
        result = client.request("GET", f"/spaces/{space_id}/nodes")
    elif args.cmd == "search-nodes":
        if not space_id:
            raise SystemExit("search-nodes requires --space-id or EBIAOBIAO_SPACE_ID")
        base_v2 = config.base_url.replace("/fusion/v1", "/fusion/v2")
        original_base = config.base_url
        config.base_url = base_v2
        params = {"type": args.type}
        if args.query:
            params["query"] = args.query
        if args.permissions:
            params["permissions"] = [item.strip() for item in args.permissions.split(",") if item.strip()]
        try:
            result = client.request("GET", f"/spaces/{space_id}/nodes", params=params)
        finally:
            config.base_url = original_base
    elif args.cmd == "node-detail":
        if not space_id:
            raise SystemExit("node-detail requires --space-id or EBIAOBIAO_SPACE_ID")
        result = client.request("GET", f"/spaces/{space_id}/nodes/{args.node_id}")
    elif args.cmd == "fields":
        result = client.request("GET", f"/datasheets/{args.datasheet_id}/fields", params={"fieldKey": args.field_key})
    elif args.cmd == "views":
        result = client.request("GET", f"/datasheets/{args.datasheet_id}/views")
    elif args.cmd == "records":
        params = {
            "fieldKey": args.field_key,
            "cellFormat": args.cell_format,
            "pageSize": args.page_size,
            "pageNum": args.page_num,
        }
        for key in ["view_id", "fields", "filter_by_formula"]:
            value = getattr(args, key)
            if value:
                params[{"view_id": "viewId", "filter_by_formula": "filterByFormula"}.get(key, key)] = value
        records = []
        total = None
        while True:
            payload = client.request("GET", f"/datasheets/{args.datasheet_id}/records", params=params)
            data = payload.get("data", {})
            if not args.all:
                result = payload
                break
            batch = data.get("records", [])
            records.extend(batch)
            total = data.get("total", len(records))
            if not batch or len(records) >= total or len(batch) < args.page_size:
                result = {"success": True, "data": {"total": total, "records": records}}
                break
            params["pageNum"] += 1
            time.sleep(config.sleep)
    elif args.cmd == "create-datasheet":
        if not space_id and config.dry_run:
            space_id = "spcDryRun"
        if not space_id:
            raise SystemExit("create-datasheet requires --space-id or EBIAOBIAO_SPACE_ID")
        result = client.request("POST", f"/spaces/{space_id}/datasheets", body=load_json_arg(args.payload_json))
        if args.clean_empty_records:
            ids = extract_ids(result, "dst")
            if ids:
                result = {"create": result, "cleanup": client.delete_empty_records(ids[0])}
    elif args.cmd == "create-field":
        if not space_id:
            raise SystemExit("create-field requires --space-id or EBIAOBIAO_SPACE_ID")
        result = client.request("POST", f"/spaces/{space_id}/datasheets/{args.datasheet_id}/fields", body=load_json_arg(args.payload_json))
    elif args.cmd == "delete-field":
        if not space_id:
            raise SystemExit("delete-field requires --space-id or EBIAOBIAO_SPACE_ID")
        result = client.request("DELETE", f"/spaces/{space_id}/datasheets/{args.datasheet_id}/fields/{args.field_id}")
    elif args.cmd == "create-records":
        params = {}
        if args.view_id:
            params["viewId"] = args.view_id
        result = client.chunked("POST", f"/datasheets/{args.datasheet_id}/records", "records", load_json_arg(args.records_json), params=params or None)
    elif args.cmd == "update-records":
        result = client.chunked("PATCH", f"/datasheets/{args.datasheet_id}/records", "records", load_json_arg(args.records_json))
    elif args.cmd == "delete-records":
        value = args.record_ids
        ids = load_json_arg(value) if Path(value).exists() or value.strip().startswith("[") else [item.strip() for item in value.split(",") if item.strip()]
        results = []
        for part in chunks(ids, 10):
            results.append(client.request("DELETE", f"/datasheets/{args.datasheet_id}/records", params={"recordIds": ",".join(part)}))
        result = {"success": True, "chunks": len(results), "results": results}
    elif args.cmd == "delete-empty-records":
        result = client.delete_empty_records(args.datasheet_id, limit=args.limit)
    elif args.cmd == "upload-attachment":
        file_path = Path(args.file)
        boundary = "----codex-ebiao-boundary"
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        parts = [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            file_path.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        result = client.request(
            "POST",
            f"/datasheets/{args.datasheet_id}/attachments",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            data=b"".join(parts),
        )
    else:
        raise AssertionError(args.cmd)
    print_json(result)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
