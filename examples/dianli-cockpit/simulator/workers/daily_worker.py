"""DailyWorker：每 30 秒给重点企业"今日"记录的用电/风险加随机游走。"""
import logging
import random
import datetime
from .base import BaseWorker

logger = logging.getLogger(__name__)


class DailyWorker(BaseWorker):
    name = "daily"
    cadence_seconds = 30.0

    def tick(self):
        dst = self.dst_ids["enterprise"]
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        all_recs = self.client.list_all_records(dst, fields=["日期"])
        if not all_recs:
            return

        # 取今日所有记录
        today_recs = [
            r for r in all_recs
            if (r.get("fields") or {}).get("日期") == today_str
        ]
        if not today_recs:
            # 没有今日记录，跳过（数据可能是历史的）
            logger.info("[daily] no records dated %s; skip", today_str)
            return

        # 随机抽 5-10 条更新
        sample = random.sample(today_recs, min(8, len(today_recs)))
        updates = []
        for r in sample:
            rid = r["recordId"]
            updates.append({
                "recordId": rid,
                "fields": {
                    "今日用电_MWh": round(random.uniform(80, 380), 1),
                    "风险指数": round(random.uniform(15, 88), 1),
                    "开工指数": round(random.uniform(60, 100), 1),
                },
            })

        if updates:
            self.client.update_records(dst, updates)
            logger.info("[daily] updated %d enterprise rows", len(updates))
