"""模拟器入口：启动 4 个 worker + playbook scheduler，Ctrl-C 优雅退出。

用法：
    python -m simulator.main [--no-playbook] [--workers monthly,daily,hourly,alert_stream]
"""
import argparse
import logging
import signal
import sys
import threading
from typing import List

from simulator.shared.vika import VikaClient
from simulator.shared.constants import TABLE_NAMES
from simulator.workers.monthly_worker import MonthlyWorker
from simulator.workers.daily_worker import DailyWorker
from simulator.workers.hourly_worker import HourlyWorker
from simulator.workers.alert_stream_worker import AlertStreamWorker
from simulator.playbooks.engine import PlaybookScheduler


WORKER_CLASSES = {
    "monthly": MonthlyWorker,
    "daily": DailyWorker,
    "hourly": HourlyWorker,
    "alert_stream": AlertStreamWorker,
}


def resolve_dst_ids(client: VikaClient) -> dict:
    """通过 search-nodes 查 7 张表的实际 dst_id（按表名）。"""
    out = {}
    for key, name in TABLE_NAMES.items():
        nodes = client.search_nodes(query=name, type="Datasheet")
        match = [n for n in nodes if n.get("name") == name]
        if not match:
            raise RuntimeError(f"找不到表：{name}（请先跑 bootstrap 创建）")
        out[_camel(key)] = match[0]["id"]
    return out


def _camel(snake: str) -> str:
    """industry -> industry; load_curve -> loadCurve"""
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def main(argv: List[str] = None) -> int:
    p = argparse.ArgumentParser(prog="simulator.main")
    p.add_argument("--no-playbook", action="store_true",
                   help="只跑背景 worker，不跑剧本")
    p.add_argument("--workers", default="monthly,daily,hourly,alert_stream",
                   help="逗号分隔的 worker 名（默认全部）")
    p.add_argument("--playbook-interval", type=float, default=90.0,
                   help="剧本之间间隔秒数（默认 90s）")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)s] %(name)s %(message)s",
    )

    client = VikaClient()
    print("→ 解析 7 张表 dst_id...")
    dst_ids = resolve_dst_ids(client)
    print("  ✓", dst_ids)

    stop_event = threading.Event()

    # 启动选中的 workers
    selected = [w.strip() for w in args.workers.split(",") if w.strip()]
    workers = []
    for name in selected:
        cls = WORKER_CLASSES.get(name)
        if not cls:
            print(f"  ⚠ 未知 worker: {name}")
            continue
        w = cls(client, dst_ids, stop_event)
        w.start()
        workers.append(w)
    print(f"  ✓ 启动 {len(workers)} 个 worker: {', '.join(w.name for w in workers)}")

    # 启动 playbook scheduler（默认开）
    if not args.no_playbook:
        scheduler = PlaybookScheduler(client, dst_ids, stop_event,
                                       interval=args.playbook_interval)
        scheduler.start()
        workers.append(scheduler)
        print(f"  ✓ Playbook scheduler 启动（每 {args.playbook_interval}s 触发一段剧本）")

    print("\n→ 按 Ctrl-C 退出...")

    def shutdown(signum, frame):
        print("\n→ 收到中断，停止 workers...")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 主线程等到 stop_event
    try:
        while not stop_event.is_set():
            stop_event.wait(1)
    except KeyboardInterrupt:
        stop_event.set()

    # 等 workers 收尾（最多 8 秒）
    for w in workers:
        w.join(timeout=8)
    print("✓ 已退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
