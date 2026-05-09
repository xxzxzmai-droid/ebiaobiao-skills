"""Playbook 引擎：解析 JSON 剧本（用 JSON 而非 YAML，避开依赖），按 step.at 时刻分发动作。

每个剧本是一组 {at, action, payload} 步骤。Scheduler 每 interval 秒选一个剧本启动，
独立线程跑完所有 step。
"""
import json
import logging
import random
import threading
import time
from pathlib import Path
from typing import List, Dict
import datetime

logger = logging.getLogger(__name__)


def load_playbooks() -> List[Dict]:
    """读 playbooks/*.json（除 engine.py 自己）。"""
    here = Path(__file__).parent
    out = []
    for f in sorted(here.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            out.append(data)
        except Exception:
            logger.exception("failed to load %s", f)
    return out


class PlaybookScheduler(threading.Thread):
    """每 interval 秒随机选一个剧本，开新线程跑它的 step。"""

    name = "playbook_sched"

    def __init__(self, client, dst_ids: dict, stop_event: threading.Event,
                 interval: float = 90.0):
        super().__init__(daemon=True, name="Playbook-Scheduler")
        self.client = client
        self.dst_ids = dst_ids
        self.stop_event = stop_event
        self.interval = interval
        self.playbooks = load_playbooks()
        self._last_pick = -1

    def run(self):
        if not self.playbooks:
            logger.warning("[playbook] no playbooks found, scheduler idle")
            return
        logger.info("[playbook] %d playbooks loaded; interval=%.1fs",
                    len(self.playbooks), self.interval)
        # 启动后等 5 秒再开始（让 worker 先跑起来）
        self.stop_event.wait(5)
        while not self.stop_event.is_set():
            self._pick_and_run()
            self.stop_event.wait(self.interval)
        logger.info("[playbook] scheduler stopped")

    def _pick_and_run(self):
        # 不连续选同一个剧本
        candidates = list(range(len(self.playbooks)))
        if self._last_pick in candidates and len(candidates) > 1:
            candidates.remove(self._last_pick)
        idx = random.choice(candidates)
        self._last_pick = idx
        pb = self.playbooks[idx]
        logger.info("[playbook] === 触发剧本：%s ===", pb.get("name", pb["_file"]))
        runner = threading.Thread(
            target=_run_playbook,
            args=(pb, self.client, self.dst_ids, self.stop_event),
            daemon=True,
            name=f"PB-{pb.get('id', idx)}",
        )
        runner.start()


def _run_playbook(pb: Dict, client, dst_ids: dict, stop_event: threading.Event):
    """按 step.at（秒）顺序执行。stop_event 可中断。"""
    start = time.time()
    name = pb.get("name", "?")
    for step in pb.get("steps", []):
        if stop_event.is_set():
            return
        at = float(step.get("at", 0))
        wait_for = at - (time.time() - start)
        if wait_for > 0:
            stop_event.wait(wait_for)
        if stop_event.is_set():
            return
        try:
            _execute_action(step, client, dst_ids)
        except Exception:
            logger.exception("[playbook %s] step at %ss failed", name, at)
    logger.info("[playbook %s] 完成（耗时 %.1fs）", name, time.time() - start)


def _execute_action(step: Dict, client, dst_ids: dict):
    """支持的 action：
    - create_alert: payload 是要创建的预警 fields
    - create_insight: payload 是机器人洞察 fields
    """
    action = step.get("action")
    payload = step.get("payload", {})

    if action == "create_alert":
        # 自动算 AL-XXXX 编号
        dst = dst_ids["alert"]
        all_recs = client.list_all_records(dst, fields=["标题"])
        max_n = 0
        for r in all_recs:
            t = (r.get("fields") or {}).get("标题", "")
            if isinstance(t, str) and t.startswith("AL-"):
                try:
                    max_n = max(max_n, int(t[3:]))
                except ValueError:
                    pass
        record = {
            "标题": f"AL-{max_n + 1:04d}",
            "时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "状态": "处理中",
            **payload,
        }
        client.create_records(dst, [record])
        logger.info("[playbook] +alert %s [%s] %s",
                    record["标题"], payload.get("等级", "?"),
                    payload.get("区域", "?"))

    elif action == "create_insight":
        dst = dst_ids["insight"]
        record = {
            "标题": f"{payload.get('区域', '')} · {payload.get('类型', '')}",
            "时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            **payload,
        }
        client.create_records(dst, [record])
        logger.info("[playbook] +insight %s", record["标题"])

    else:
        logger.warning("[playbook] 未知 action: %s", action)
