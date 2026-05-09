"""MonthlyWorker：每 60 秒给行业指标"本月"的同比/景气指数加微扰。"""
import logging
import random
import datetime
from .base import BaseWorker

logger = logging.getLogger(__name__)


class MonthlyWorker(BaseWorker):
    name = "monthly"
    cadence_seconds = 60.0

    def tick(self):
        dst = self.dst_ids["industry"]
        this_month = datetime.date.today().strftime("%Y-%m")
        all_recs = self.client.list_all_records(dst, fields=["月份"])
        if not all_recs:
            return

        this_month_recs = [
            r for r in all_recs
            if (r.get("fields") or {}).get("月份") == this_month
        ]
        if not this_month_recs:
            logger.info("[monthly] no records for %s; skip", this_month)
            return

        # 随机抽 3-8 条更新（同比 ±0.3 漂移、景气指数 ±0.5）
        sample = random.sample(this_month_recs, min(6, len(this_month_recs)))
        updates = []
        for r in sample:
            rid = r["recordId"]
            updates.append({
                "recordId": rid,
                "fields": {
                    "同比_%": round(random.uniform(-15, 25), 1),
                    "景气指数": round(random.uniform(55, 95), 1),
                },
            })

        if updates:
            self.client.update_records(dst, updates)
            logger.info("[monthly] updated %d industry rows", len(updates))
