"""Validate the 7 datasheet schema definitions."""
import unittest
from simulator.shared import schema, constants as C


class TestSchemaShape(unittest.TestCase):
    def test_seven_schemas(self):
        self.assertEqual(len(schema.ALL_SCHEMAS), 7)

    def test_schema_names_match_constants(self):
        expected = set(C.TABLE_NAMES.values())
        actual = {s["name"] for s in schema.ALL_SCHEMAS}
        self.assertEqual(expected, actual)

    def test_every_field_has_name_and_type(self):
        for s in schema.ALL_SCHEMAS:
            for f in s["fields"]:
                self.assertIn("name", f)
                self.assertIsInstance(f["name"], str)
                self.assertIn("type", f)
                self.assertIsInstance(f["type"], str)


class TestConfiguredDeploymentQuirks(unittest.TestCase):
    def test_singleselect_options_use_string_color(self):
        """报表目标环境要求 color 是字符串，不是 {name: ...} 对象。"""
        for s in schema.ALL_SCHEMAS:
            for f in s["fields"]:
                if f["type"] in ("SingleSelect", "MultiSelect"):
                    opts = f.get("property", {}).get("options", [])
                    self.assertTrue(opts, f"{s['name']}.{f['name']} has no options")
                    for opt in opts:
                        self.assertIsInstance(
                            opt["color"], str,
                            f"{s['name']}.{f['name']} option {opt['name']} color must be str",
                        )

    def test_datetime_dateformat_in_enum(self):
        valid = {
            "YYYY/MM/DD", "YYYY-MM-DD", "DD/MM/YYYY",
            "YYYY-MM", "MM-DD", "YYYY", "MM", "DD",
        } | {str(i) for i in range(8)}
        for s in schema.ALL_SCHEMAS:
            for f in s["fields"]:
                if f["type"] in ("DateTime", "CreatedTime", "LastModifiedTime"):
                    fmt = f.get("property", {}).get("dateFormat")
                    self.assertIn(fmt, valid, f"{s['name']}.{f['name']} dateFormat={fmt!r}")

    def test_number_defaultvalue_is_string(self):
        for s in schema.ALL_SCHEMAS:
            for f in s["fields"]:
                if f["type"] == "Number":
                    dv = f.get("property", {}).get("defaultValue")
                    if dv is not None:
                        self.assertIsInstance(dv, str)

    def test_rating_icon_is_emoji_slug(self):
        valid_slugs = {"star", "heart", "fire", "thumbs_up", "white_check_mark"}
        for s in schema.ALL_SCHEMAS:
            for f in s["fields"]:
                if f["type"] == "Rating":
                    icon = f.get("property", {}).get("icon")
                    self.assertIn(icon, valid_slugs)


class TestSpecificSchemas(unittest.TestCase):
    def test_industry_metrics_required_fields(self):
        s = next(s for s in schema.ALL_SCHEMAS
                 if s["name"] == C.TABLE_NAMES["industry"])
        names = {f["name"] for f in s["fields"]}
        self.assertTrue({"月份", "区域", "行业", "行业用电_MWh",
                         "同比_%", "景气指数", "产出指数"} <= names)

    def test_enterprise_required_fields(self):
        s = next(s for s in schema.ALL_SCHEMAS
                 if s["name"] == C.TABLE_NAMES["enterprise"])
        names = {f["name"] for f in s["fields"]}
        self.assertTrue({"日期", "区域", "行业", "今日用电_MWh",
                         "同比_%", "开工指数", "风险指数", "状态"} <= names)

    def test_alert_status_options_match_constants(self):
        s = next(s for s in schema.ALL_SCHEMAS if s["name"] == C.TABLE_NAMES["alert"])
        status_field = next(f for f in s["fields"] if f["name"] == "状态")
        opts = {o["name"]: o["color"] for o in status_field["property"]["options"]}
        self.assertEqual(opts, C.ALERT_STATUS_COLOR)


if __name__ == "__main__":
    unittest.main()
