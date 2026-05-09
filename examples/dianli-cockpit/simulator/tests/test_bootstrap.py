"""bootstrap_schemas: 创建/复用 datasheet + 补齐缺失字段。"""
import unittest
from unittest.mock import MagicMock
from simulator.shared.bootstrap import bootstrap_schemas
from simulator.shared.schema import ALL_SCHEMAS, INDUSTRY_METRICS


class TestBootstrap(unittest.TestCase):
    def test_creates_datasheet_when_not_exists(self):
        client = MagicMock()
        client.search_nodes.return_value = []
        client.create_datasheet.return_value = {
            "id": "dstNEW",
            "fields": [{"id": "fldT", "name": "标题"}],
        }
        client.list_fields.return_value = [
            {"id": "fldT", "name": "标题", "type": "SingleText"},
        ]
        client.create_field.return_value = {"id": "fldX"}

        result = bootstrap_schemas(client, [INDUSTRY_METRICS])
        self.assertEqual(result[INDUSTRY_METRICS["name"]], "dstNEW")
        client.create_datasheet.assert_called_once_with(INDUSTRY_METRICS["name"])
        # 7 schema fields, 0 already exist with matching name → all 7 created
        self.assertEqual(client.create_field.call_count, len(INDUSTRY_METRICS["fields"]))

    def test_reuses_existing_datasheet(self):
        client = MagicMock()
        client.search_nodes.return_value = [
            {"id": "dstEXIST", "name": INDUSTRY_METRICS["name"]},
        ]
        client.list_fields.return_value = [
            {"id": "fldT", "name": "标题", "type": "SingleText"},
            {"id": "fldA", "name": "月份", "type": "DateTime"},
            {"id": "fldB", "name": "区域", "type": "SingleSelect"},
        ]
        bootstrap_schemas(client, [INDUSTRY_METRICS])
        client.create_datasheet.assert_not_called()
        # 7 schema fields - 2 already exist (月份, 区域) = 5 created
        self.assertEqual(client.create_field.call_count,
                         len(INDUSTRY_METRICS["fields"]) - 2)

    def test_passes_property_to_create_field(self):
        client = MagicMock()
        client.search_nodes.return_value = []
        client.create_datasheet.return_value = {"id": "dst1", "fields": []}
        client.list_fields.return_value = []
        client.create_field.return_value = {"id": "fldX"}

        bootstrap_schemas(client, [INDUSTRY_METRICS])
        first_call = client.create_field.call_args_list[0]
        self.assertEqual(first_call.kwargs.get("name"), "月份")
        self.assertEqual(first_call.kwargs.get("type"), "DateTime")
        self.assertEqual(first_call.kwargs.get("property", {}).get("dateFormat"),
                         "YYYY-MM")

    def test_handles_all_seven_schemas(self):
        client = MagicMock()
        client.search_nodes.return_value = []
        client.create_datasheet.side_effect = [
            {"id": f"dst{i}", "fields": []} for i in range(len(ALL_SCHEMAS))
        ]
        client.list_fields.return_value = []
        client.create_field.return_value = {"id": "fldX"}

        result = bootstrap_schemas(client, ALL_SCHEMAS)
        self.assertEqual(len(result), 7)
        self.assertEqual(client.create_datasheet.call_count, 7)


if __name__ == "__main__":
    unittest.main()
