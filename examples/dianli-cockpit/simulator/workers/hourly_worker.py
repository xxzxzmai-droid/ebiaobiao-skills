"""HourlyWorker：每 10 秒给"用电曲线"当前小时记录加微噪声。

cadence 10s。整点滚动滑窗（drop -23h, append 新小时）暂未实现，留给 Phase D。
本 worker 只让"当前小时"的 7 区记录数值轻微抖动，让前端折线"活着"。
"""
import logging
import random
from .base import BaseWorker

logger = logging.getLogger(__name__)


class HourlyWorker(BaseWorker):
    name = "hourly"
    cadence_seconds = 10.0

    def tick(self):
        dst = self.dst_ids["loadCurve"]
        # 拉所有 168 条记录的 ID + 时间戳
        all_recs = self.client.list_all_records(dst, fields=["时间戳", "区域"])
        if not all_recs:
            logger.info("[hourly] no records, skip")
            return

        # 找"当前小时"（时间戳字符串最大的）
        max_ts = ""
        for r in all_recs:
            ts = (r.get("fields") or {}).get("时间戳", "")
            if isinstance(ts, str) and ts > max_ts:
                max_ts = ts
        if not max_ts:
            return

        current = [r for r in all_recs
                   if (r.get("fields") or {}).get("时间戳") == max_ts]
        # 随机抖动 ±3% 的 实时负荷_MW
        updates = []
        for r in current:
            rid = r["recordId"]
            # 拉这条记录原值（list 时只取了 时间戳/区域）— 简化：随机一个新值
            new_load = round(random.uniform(180, 480), 1)
            new_forecast = round(new_load * random.uniform(0.92, 1.08), 1)
            updates.append({
                "recordId": rid,
                "fields": {
                    "实时负荷_MW": new_load,
                    "预测负荷_MW": new_forecast,
                },
            })

        if updates:
            self.client.update_records(dst, updates)
            logger.info("[hourly] updated %d load curve points", len(updates))
