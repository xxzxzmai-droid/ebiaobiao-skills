"""Playbook 引擎：加载 + step 执行。"""
import threading
import unittest
from unittest.mock import MagicMock
from simulator.playbooks.engine import load_playbooks, _execute_action


class TestLoadPlaybooks(unittest.TestCase):
    def test_loads_six_playbooks(self):
        pbs = load_playbooks()
        self.assertEqual(len(pbs), 6)
        ids = {pb["id"] for pb in pbs}
        self.assertEqual(ids, {"P01", "P02", "P03", "P04", "P05", "P06"})

    def test_each_playbook_has_required_fields(self):
        for pb in load_playbooks():
            self.assertIn("name", pb)
            self.assertIn("steps", pb)
            self.assertIsInstance(pb["steps"], list)
            for step in pb["steps"]:
                self.assertIn("at", step)
                self.assertIn("action", step)


class TestExecuteAction(unittest.TestCase):
    def test_create_alert_increments_code(self):
        client = MagicMock()
        client.list_all_records.return_value = [
            {"fields": {"标题": "AL-0123"}},
        ]
        client.create_records.return_value = []
        step = {
            "action": "create_alert",
            "payload": {"等级": "红色", "类型": "用电异常", "区域": "惠阳区",
                         "说明": "test"},
        }
        _execute_action(step, client, {"alert": "dstA"})
        client.create_records.assert_called_once()
        new = client.create_records.call_args[0][1][0]
        self.assertEqual(new["标题"], "AL-0124")
        self.assertEqual(new["等级"], "红色")

    def test_create_insight(self):
        client = MagicMock()
        step = {
            "action": "create_insight",
            "payload": {"区域": "惠城区", "类型": "节能建议", "置信分": 4,
                         "洞察内容": "..."},
        }
        _execute_action(step, client, {"insight": "dstI"})
        client.create_records.assert_called_once()
        new = client.create_records.call_args[0][1][0]
        self.assertIn("惠城区", new["标题"])
        self.assertIn("节能建议", new["标题"])


if __name__ == "__main__":
    unittest.main()
