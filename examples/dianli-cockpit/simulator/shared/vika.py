"""Thin wrapper around ebiao_fusion.py CLI.

Uses subprocess to delegate Vika REST calls to the existing CLI tool. This
avoids reimplementing HTTP/auth/retries — the CLI already handles them.

For tests, inject a custom `runner` callable that takes argv list and returns
the parsed JSON response dict.
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

EBIAO_FUSION_SCRIPT = os.environ.get(
    "EBIAO_FUSION_SCRIPT",
    str(Path.home() / ".codex" / "skills" / "ebiaobiao-fusion-api"
        / "scripts" / "ebiao_fusion.py"),
)


class VikaError(RuntimeError):
    def __init__(self, code, message, payload=None):
        self.code = code
        self.message = message
        self.payload = payload
        super().__init__(f"vika [{code}] {message}")


Runner = Callable[[List[str]], dict]


def _subprocess_runner(args: List[str], *, timeout: int = 120) -> dict:
    """Default runner: shell out to ebiao_fusion.py, parse its JSON stdout."""
    cmd = ["python3", EBIAO_FUSION_SCRIPT, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise VikaError(
            code="subprocess",
            message=f"exit={proc.returncode}, stderr={proc.stderr.strip()[:200]}",
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise VikaError(
            code="parse",
            message=f"non-JSON output: {proc.stdout[:200]}",
        )


def _chunks(seq, size):
    seq = list(seq)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


class VikaClient:
    """High-level operations against vika via the ebiao_fusion CLI.

    All write methods auto-batch by 10 (vika REST hard limit).
    """
    BATCH_SIZE = 10
    PAGE_SIZE_MAX = 1000

    def __init__(self, runner: Optional[Runner] = None):
        self._runner = runner or _subprocess_runner

    def _call(self, args: List[str], *, timeout: int = 120) -> dict:
        # Custom-timeout path: pass timeout to subprocess runner if it accepts it
        try:
            resp = self._runner(args, timeout=timeout)
        except TypeError:
            # mock runners in tests don't accept timeout kwarg
            resp = self._runner(args)
        if not resp.get("success"):
            raise VikaError(
                code=resp.get("code", "?"),
                message=resp.get("message", "unknown"),
                payload=resp,
            )
        return resp.get("data") or {}

    # ---------- nodes ----------
    def search_nodes(self, *, query=None, type="Datasheet", permissions=None):
        args = ["search-nodes"]
        if query: args += ["--query", query]
        if type: args += ["--type", type]
        if permissions is not None: args += ["--permissions", str(permissions)]
        return self._call(args).get("nodes", [])

    # ---------- datasheets ----------
    def create_datasheet(self, name: str, *, folder_id=None, fields=None) -> dict:
        # CLI: create-datasheet <payload_json>
        payload = {"name": name}
        if folder_id: payload["folderId"] = folder_id
        if fields: payload["fields"] = fields
        return self._call(["create-datasheet", json.dumps(payload, ensure_ascii=False)])

    # ---------- fields ----------
    def list_fields(self, dst_id: str) -> list:
        return self._call(["fields", dst_id]).get("fields", [])

    def create_field(self, dst_id: str, name: str, type: str,
                     property: Optional[dict] = None) -> dict:
        # CLI: create-field <datasheet_id> <payload_json>
        payload = {"name": name, "type": type}
        if property is not None:
            payload["property"] = property
        return self._call(["create-field", dst_id,
                           json.dumps(payload, ensure_ascii=False)])

    def delete_field(self, dst_id: str, field_id: str) -> None:
        self._call(["delete-field", dst_id, field_id])

    # ---------- records ----------
    def list_records(self, dst_id: str, *, page_num=1, page_size=1000,
                     filter_formula=None, fields=None, view_id=None,
                     field_key="name") -> dict:
        args = ["records", dst_id, "--page-num", str(page_num),
                "--page-size", str(min(page_size, self.PAGE_SIZE_MAX)),
                "--field-key", field_key]
        if filter_formula: args += ["--filter-by-formula", filter_formula]
        if view_id: args += ["--view-id", view_id]
        if fields: args += ["--fields", ",".join(fields)]
        return self._call(args)

    def list_all_records(self, dst_id: str, **kwargs) -> list:
        out = []
        page = 1
        while True:
            resp = self.list_records(dst_id, page_num=page, **kwargs)
            recs = resp.get("records", [])
            out.extend(recs)
            total = resp.get("total", 0)
            if len(out) >= total or not recs:
                break
            page += 1
        return out

    def create_records(self, dst_id: str, records: list, *,
                       sleep_seconds: float = 0.3) -> list:
        """Create records. CLI auto-chunks by 10 internally; we pass full payload.

        For large batches (>50), single CLI call may take minutes — we
        compute a generous timeout based on record count.
        """
        if not records:
            return []
        # 单次传全量给 CLI，让它自己 chunk + sleep
        payload = [{"fields": r} for r in records]
        n_chunks = (len(records) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        timeout = max(60, int(n_chunks * (1.5 + sleep_seconds) + 30))
        args = ["create-records", dst_id, json.dumps(payload, ensure_ascii=False),
                "--sleep", str(sleep_seconds)]
        data = self._call(args, timeout=timeout)
        return data.get("records", [])

    def update_records(self, dst_id: str, records: list, *,
                       sleep_seconds: float = 0.3) -> list:
        if not records:
            return []
        n_chunks = (len(records) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        timeout = max(60, int(n_chunks * (1.5 + sleep_seconds) + 30))
        args = ["update-records", dst_id, json.dumps(records, ensure_ascii=False),
                "--sleep", str(sleep_seconds)]
        data = self._call(args, timeout=timeout)
        return data.get("records", [])

    def delete_records(self, dst_id: str, record_ids: list, *,
                       sleep_seconds: float = 0.3) -> None:
        if not record_ids:
            return
        # delete-records CLI uses positional comma-list; CLI may not auto-chunk this one
        for chunk in _chunks(record_ids, self.BATCH_SIZE):
            self._call(["delete-records", dst_id, ",".join(chunk)])
