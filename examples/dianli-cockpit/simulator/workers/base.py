"""BaseWorker：daemon thread + sleep cadence + 优雅停。

每个 worker 子类只实现 tick()。run() 包了异常隔离 + stop_event 检查。
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)


class BaseWorker(threading.Thread):
    """基类：周期触发 tick()，stop_event 设置后下次循环退出。"""

    cadence_seconds: float = 30.0
    name: str = "base"

    def __init__(self, client, dst_ids: dict, stop_event: threading.Event,
                 cadence_seconds: float | None = None):
        super().__init__(daemon=True, name=f"Worker-{self.name}")
        self.client = client
        self.dst_ids = dst_ids
        self.stop_event = stop_event
        if cadence_seconds is not None:
            self.cadence_seconds = cadence_seconds

    def run(self):
        logger.info("[%s] start (cadence=%.1fs)", self.name, self.cadence_seconds)
        while not self.stop_event.is_set():
            t0 = time.time()
            try:
                self.tick()
                logger.info("[%s] tick OK %.1fs", self.name, time.time() - t0)
            except Exception:
                logger.exception("[%s] tick failed", self.name)
            # 用 stop_event.wait 而非 time.sleep —— 可被立刻唤醒
            self.stop_event.wait(self.cadence_seconds)
        logger.info("[%s] stopped", self.name)

    def tick(self):
        """子类必须实现。一次循环要做的事。"""
        raise NotImplementedError
