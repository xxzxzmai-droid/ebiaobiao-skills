"""seed_table: 幂等批量写。"""
import unittest
from unittest.mock import MagicMock
from simulator.shared.seeder import seed_table


class TestSeedTable(unittest.TestCase):
    def test_seeds_all_when_empty(self):
        client = MagicMock()
        client.list_all_records.return_value = []
        records = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        n = seed_table(client, "dst1", records, key_fields=["a"])
        self.assertEqual(n, 2)
        client.create_records.assert_called_once_with("dst1", records)

    def test_skips_existing(self):
        client = MagicMock()
        client.list_all_records.return_value = [
            {"recordId": "rec1", "fields": {"a": 1, "b": "x"}}
        ]
        new_records = [
            {"a": 1, "b": "ignored"},
            {"a": 2, "b": "y"},
        ]
        n = seed_table(client, "dst1", new_records, key_fields=["a"])
        self.assertEqual(n, 1)
        args = client.create_records.call_args[0]
        self.assertEqual(args[0], "dst1")
        self.assertEqual(args[1], [{"a": 2, "b": "y"}])

    def test_composite_key(self):
        client = MagicMock()
        client.list_all_records.return_value = [
            {"recordId": "r", "fields": {"日期": "2026-05-09", "区域": "惠城区"}}
        ]
        records = [
            {"日期": "2026-05-09", "区域": "惠城区", "v": 1},
            {"日期": "2026-05-09", "区域": "惠阳区", "v": 2},
        ]
        n = seed_table(client, "dst1", records, key_fields=["日期", "区域"])
        self.assertEqual(n, 1)

    def test_dry_run(self):
        client = MagicMock()
        client.list_all_records.return_value = []
        n = seed_table(client, "dst1", [{"a": 1}],
                       key_fields=["a"], dry_run=True)
        self.assertEqual(n, 1)
        client.create_records.assert_not_called()


if __name__ == "__main__":
    unittest.main()
