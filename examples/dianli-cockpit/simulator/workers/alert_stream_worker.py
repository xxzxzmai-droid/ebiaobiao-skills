"""AlertStreamWorker：每 20-60 秒（随机）创建一条新预警事件。

模拟"实时事件流"。等级按权重黄/橙/红 = 50/35/15。
"""
import logging
import random
import datetime
from .base import BaseWorker
from simulator.shared.constants import (
    DISTRICT_COLOR, ALERT_TYPES,
)

logger = logging.getLogger(__name__)

DISTRICTS = list(DISTRICT_COLOR.keys())
LEVEL_WEIGHTS = [("黄色", 50), ("橙色", 35), ("红色", 15)]


class AlertStreamWorker(BaseWorker):
    name = "alert_stream"
    cadence_seconds = 30.0  # 平均 30s（实际每次 randomize 20-60）

    def tick(self):
        dst = self.dst_ids["alert"]
        # 拉 max 事件编号 → 下一个递增
        all_recs = self.client.list_all_records(dst, fields=["标题"])
        max_n = 0
        for r in all_recs:
            title = (r.get("fields") or {}).get("标题", "")
            if isinstance(title, str) and title.startswith("AL-"):
                try:
                    n = int(title[3:])
                    if n > max_n:
                        max_n = n
                except ValueError:
                    pass

        # 随机生成
        level = random.choices(
            [w[0] for w in LEVEL_WEIGHTS],
            weights=[w[1] for w in LEVEL_WEIGHTS],
        )[0]
        district = random.choice(DISTRICTS)
        atype = random.choice(ALERT_TYPES)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_code = f"AL-{max_n + 1:04d}"

        record = {
            "标题": new_code,
            "时间": now,
            "区域": district,
            "等级": level,
            "类型": atype,
            "说明": f"【{district}{atype}指标偏离阈值】"
                    f"实时监测：{atype}指标在 {now} 产生波动，"
                    f"建议运营值班人员复核。",
            "状态": "处理中",
        }

        self.client.create_records(dst, [record])
        logger.info("[alert_stream] new alert %s [%s] %s", new_code, level, district)

        # 下一次 cadence randomize 20-60s
        self.cadence_seconds = random.uniform(20, 60)
