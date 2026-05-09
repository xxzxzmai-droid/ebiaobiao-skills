"""VikaClient: 子进程命令拼装与响应解析。"""
import json
import unittest
from unittest.mock import MagicMock, patch
from simulator.shared.vika import VikaClient, VikaError


class TestSearchNodes(unittest.TestCase):
    def test_calls_with_correct_args(self):
        runner = MagicMock(return_value={
            "success": True, "data": {"nodes": [{"id": "dst123", "name": "T"}]},
        })
        c = VikaClient(runner=runner)
        result = c.search_nodes(query="电力驾驶舱", type="Datasheet")
        runner.assert_called_once()
        args = runner.call_args[0][0]
        self.assertIn("search-nodes", args)
        self.assertIn("--query", args)
        self.assertIn("电力驾驶舱", args)
        self.assertEqual(result, [{"id": "dst123", "name": "T"}])


class TestCreateDatasheet(unittest.TestCase):
    def test_returns_dst_id(self):
        runner = MagicMock(return_value={
            "success": True,
            "data": {"id": "dstNew", "fields": [{"id": "fldA", "name": "标题"}]},
        })
        c = VikaClient(runner=runner)
        result = c.create_datasheet("电力驾驶舱_测试")
        self.assertEqual(result["id"], "dstNew")
        args = runner.call_args[0][0]
        self.assertEqual(args[0], "create-datasheet")
        payload = json.loads(args[1])
        self.assertEqual(payload["name"], "电力驾驶舱_测试")


class TestListFields(unittest.TestCase):
    def test_correct_args_and_parse(self):
        runner = MagicMock(return_value={
            "success": True,
            "data": {"fields": [{"id": "fld1", "name": "区域", "type": "SingleSelect"}]},
        })
        c = VikaClient(runner=runner)
        fields = c.list_fields("dstABC")
        self.assertEqual(runner.call_args[0][0], ["fields", "dstABC"])
        self.assertEqual(fields[0]["name"], "区域")


class TestCreateField(unittest.TestCase):
    def test_with_property(self):
        runner = MagicMock(return_value={"success": True, "data": {"id": "fldNew"}})
        c = VikaClient(runner=runner)
        c.create_field("dstABC", "区域", "SingleSelect",
                       property={"options": [{"name": "惠城区", "color": "blue"}]})
        args = runner.call_args[0][0]
        self.assertEqual(args[0], "create-field")
        self.assertEqual(args[1], "dstABC")
        payload = json.loads(args[2])
        self.assertEqual(payload["name"], "区域")
        self.assertEqual(payload["type"], "SingleSelect")
        self.assertEqual(payload["property"]["options"][0]["color"], "blue")


class TestRecordsBatch(unittest.TestCase):
    def test_create_chunks_to_10(self):
        runner = MagicMock(return_value={"success": True, "data": {"records": []}})
        c = VikaClient(runner=runner)
        records = [{"区域": "惠城区"} for _ in range(25)]
        c.create_records("dstABC", records)
        self.assertEqual(runner.call_count, 3)  # 10 / 10 / 5
        first = runner.call_args_list[0][0][0]
        self.assertEqual(first[0], "create-records")
        self.assertEqual(first[1], "dstABC")
        payload = json.loads(first[2])
        self.assertIsInstance(payload, list)
        self.assertEqual(payload[0], {"fields": {"区域": "惠城区"}})

    def test_update_chunks_to_10(self):
        runner = MagicMock(return_value={"success": True, "data": {"records": []}})
        c = VikaClient(runner=runner)
        c.update_records("dstABC", [{"recordId": f"r{i}", "fields": {"x": 1}} for i in range(15)])
        self.assertEqual(runner.call_count, 2)  # 10 / 5

    def test_delete_chunks_to_10(self):
        runner = MagicMock(return_value={"success": True, "data": {}})
        c = VikaClient(runner=runner)
        c.delete_records("dstABC", [f"r{i}" for i in range(12)])
        self.assertEqual(runner.call_count, 2)


class TestPagination(unittest.TestCase):
    def test_list_all_records_paginates(self):
        page1 = [{"recordId": f"rec{i}", "fields": {}} for i in range(1000)]
        page2 = [{"recordId": f"recX{i}", "fields": {}} for i in range(50)]
        runner = MagicMock(side_effect=[
            {"success": True, "data": {"records": page1, "total": 1050}},
            {"success": True, "data": {"records": page2, "total": 1050}},
        ])
        c = VikaClient(runner=runner)
        all_records = c.list_all_records("dstABC")
        self.assertEqual(len(all_records), 1050)


class TestErrorHandling(unittest.TestCase):
    def test_failure_raises_vikaerror(self):
        runner = MagicMock(return_value={
            "success": False, "code": 400,
            "message": "Invalid value for fields[X].property",
        })
        c = VikaClient(runner=runner)
        with self.assertRaises(VikaError) as ctx:
            c.create_datasheet("X")
        self.assertIn("Invalid value", str(ctx.exception))


class TestSubprocessRunner(unittest.TestCase):
    """默认 runner 真的去调 ebiao_fusion.py（mock subprocess.run）。"""
    @patch("simulator.shared.vika.EBIAO_FUSION_SCRIPT", "/fake/ebiao_fusion.py")
    @patch("subprocess.run")
    def test_calls_ebiao_fusion(self, mock_run):
        from simulator.shared import vika
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = '{"success": true, "data": {"nodes": []}}'
        proc.stderr = ""
        mock_run.return_value = proc
        result = vika._subprocess_runner(["search-nodes", "--query", "X"])
        self.assertTrue(result["success"])
        cmd = mock_run.call_args[0][0]
        self.assertIn("/fake/ebiao_fusion.py", cmd)
        self.assertIn("search-nodes", cmd)


if __name__ == "__main__":
    unittest.main()
