"""Validate generated record counts, fields, ranges, distributions."""
import unittest
from simulator.shared import generators as G
from simulator.shared.constants import (
    DISTRICT_COLOR, INDUSTRY_COLOR, ALERT_LEVEL_COLOR,
)


class TestIndustryMetrics(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(G.generate_industry_metrics(seed=1)), 504)

    def test_fields_complete(self):
        rec = G.generate_industry_metrics(seed=1)[0]
        self.assertTrue({
            "月份", "区域", "行业", "行业用电_MWh",
            "同比_%", "景气指数", "产出指数",
        } <= set(rec.keys()))

    def test_districts_industries_covered(self):
        rec = G.generate_industry_metrics(seed=1)
        self.assertEqual({r["区域"] for r in rec}, set(DISTRICT_COLOR.keys()))
        self.assertEqual({r["行业"] for r in rec}, set(INDUSTRY_COLOR.keys()))

    def test_value_ranges(self):
        rec = G.generate_industry_metrics(seed=1)
        for r in rec:
            self.assertGreaterEqual(r["行业用电_MWh"], 100)
            self.assertLessEqual(r["行业用电_MWh"], 5000)
            self.assertGreaterEqual(r["同比_%"], -30)
            self.assertLessEqual(r["同比_%"], 30)
            self.assertGreaterEqual(r["景气指数"], 30)
            self.assertLessEqual(r["景气指数"], 100)


class TestEnterprises(unittest.TestCase):
    def test_count(self):
        # 30 企业 × 14 天 = 420（原本 1500 太大易超时）
        self.assertEqual(len(G.generate_enterprises(seed=1)), 420)

    def test_unique_companies(self):
        rec = G.generate_enterprises(seed=1)
        self.assertEqual(len({r["标题"] for r in rec}), 30)


class TestLoadCurve(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(G.generate_load_curve(seed=1)), 168)

    def test_24_distinct_timestamps(self):
        rec = G.generate_load_curve(seed=1)
        self.assertEqual(len({r["时间戳"] for r in rec}), 24)


class TestAlerts(unittest.TestCase):
    def test_count_in_range(self):
        n = len(G.generate_alerts(seed=1))
        self.assertGreaterEqual(n, 70)
        self.assertLessEqual(n, 90)

    def test_levels_distribution(self):
        rec = G.generate_alerts(seed=1)
        levels = [r["等级"] for r in rec]
        self.assertTrue(set(levels) <= set(ALERT_LEVEL_COLOR.keys()))
        # 红色应该是少数
        self.assertLess(levels.count("红色"), len(levels) * 0.3)

    def test_event_codes_unique_and_formatted(self):
        rec = G.generate_alerts(seed=1)
        # 主字段是 标题（vika auto-primary），值为 AL-XXXX
        codes = [r["标题"] for r in rec]
        self.assertEqual(len(set(codes)), len(codes))
        for c in codes:
            self.assertTrue(c.startswith("AL-"))


class TestRenewable(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(G.generate_renewable(seed=1)), 210)


class TestInsights(unittest.TestCase):
    def test_count(self):
        n = len(G.generate_insights(seed=1))
        self.assertGreaterEqual(n, 25)
        self.assertLessEqual(n, 35)

    def test_long_content(self):
        for r in G.generate_insights(seed=1):
            self.assertGreaterEqual(
                len(r["洞察内容"]), 30,
                f"洞察内容 too short: {r['洞察内容']!r}",
            )


class TestConfig(unittest.TestCase):
    def test_kv_pairs(self):
        rec = G.generate_config()
        # 主字段是 标题（vika auto-primary），值为参数名
        keys = {r["标题"] for r in rec}
        self.assertIn("红色预警阈值", keys)
        self.assertIn("橙色预警阈值", keys)
        self.assertIn("黄色预警阈值", keys)
        self.assertIn("演示模式", keys)


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_result(self):
        a = G.generate_enterprises(seed=42)
        b = G.generate_enterprises(seed=42)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
