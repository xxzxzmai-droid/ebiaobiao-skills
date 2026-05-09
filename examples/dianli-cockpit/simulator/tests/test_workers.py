"""Worker tick 行为：mock vika，验证读+写流程。"""
import threading
import unittest
from unittest.mock import MagicMock
from simulator.workers.hourly_worker import HourlyWorker
from simulator.workers.alert_stream_worker import AlertStreamWorker
from simulator.workers.daily_worker import DailyWorker
from simulator.workers.monthly_worker import MonthlyWorker


def _stop_event():
    return threading.Event()


def _client_with_records(records):
    c = MagicMock()
    c.list_all_records.return_value = records
    c.update_records.return_value = []
    c.create_records.return_value = []
    return c


class TestHourlyWorker(unittest.TestCase):
    def test_updates_current_hour_records(self):
        # 168 records spanning 24h × 7 districts；最大时间戳那一刻是"当前小时"
        recs = []
        for h in range(24):
            ts = f"2026-05-09 {h:02d}:00"
            for d in ["惠城区", "惠阳区", "大亚湾区", "仲恺高新区",
                      "博罗县", "惠东县", "龙门县"]:
                recs.append({"recordId": f"r{h}{d}",
                             "fields": {"时间戳": ts, "区域": d}})
        client = _client_with_records(recs)
        w = HourlyWorker(client, {"loadCurve": "dst1"}, _stop_event())
        w.tick()
        # 最大时间戳是 "2026-05-09 23:00"，对应 7 个区
        client.update_records.assert_called_once()
        args = client.update_records.call_args[0]
        self.assertEqual(args[0], "dst1")
        self.assertEqual(len(args[1]), 7)

    def test_empty_table_no_writes(self):
        client = _client_with_records([])
        w = HourlyWorker(client, {"loadCurve": "dst1"}, _stop_event())
        w.tick()
        client.update_records.assert_not_called()


class TestDailyWorker(unittest.TestCase):
    def test_skips_when_no_today_records(self):
        # 全是历史日期
        recs = [{"recordId": f"r{i}", "fields": {"日期": "2020-01-01"}}
                for i in range(10)]
        client = _client_with_records(recs)
        w = DailyWorker(client, {"enterprise": "dst1"}, _stop_event())
        w.tick()
        client.update_records.assert_not_called()


class TestAlertStreamWorker(unittest.TestCase):
    def test_creates_new_alert_with_incremented_code(self):
        recs = [
            {"recordId": "r1", "fields": {"标题": "AL-0001"}},
            {"recordId": "r2", "fields": {"标题": "AL-0083"}},
            {"recordId": "r3", "fields": {"标题": "AL-0050"}},
        ]
        client = _client_with_records(recs)
        w = AlertStreamWorker(client, {"alert": "dstA"}, _stop_event())
        w.tick()
        client.create_records.assert_called_once()
        args = client.create_records.call_args[0]
        new_record = args[1][0]
        self.assertEqual(new_record["标题"], "AL-0084")
        self.assertIn(new_record["等级"], ["红色", "橙色", "黄色"])
        self.assertEqual(new_record["状态"], "处理中")


class TestMonthlyWorker(unittest.TestCase):
    def test_skips_when_no_current_month(self):
        recs = [{"recordId": "r1", "fields": {"月份": "2020-01"}}]
        client = _client_with_records(recs)
        w = MonthlyWorker(client, {"industry": "dst1"}, _stop_event())
        w.tick()
        client.update_records.assert_not_called()


if __name__ == "__main__":
    unittest.main()
