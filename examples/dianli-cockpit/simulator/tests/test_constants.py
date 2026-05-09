"""Validate shared constants are well-formed and consistent."""
import unittest
from simulator.shared import constants as C


class TestDistricts(unittest.TestCase):
    def test_count_and_color_validity(self):
        self.assertEqual(len(C.DISTRICT_COLOR), 7)
        self.assertEqual(set(C.DISTRICT_COLOR.keys()), {
            "惠城区", "惠阳区", "大亚湾区", "仲恺高新区",
            "博罗县", "惠东县", "龙门县",
        })
        for name, color in C.DISTRICT_COLOR.items():
            self.assertIsInstance(color, str, f"{name} color must be str")
            self.assertIn(color, C.VIKA_VALID_COLORS, f"{name}: {color}")


class TestIndustries(unittest.TestCase):
    def test_count_and_color_validity(self):
        self.assertEqual(len(C.INDUSTRY_COLOR), 6)
        self.assertEqual(set(C.INDUSTRY_COLOR.keys()), {
            "电子信息", "石化能源", "装备制造",
            "汽车制造", "纺织食品", "新材料",
        })
        for name, color in C.INDUSTRY_COLOR.items():
            self.assertIsInstance(color, str)
            self.assertIn(color, C.VIKA_VALID_COLORS)


class TestEnums(unittest.TestCase):
    def test_alert_levels(self):
        self.assertEqual(C.ALERT_LEVEL_COLOR,
                         {"红色": "red", "橙色": "orange", "黄色": "yellow"})

    def test_enterprise_status(self):
        self.assertEqual(set(C.ENTERPRISE_STATUS_COLOR.keys()),
                         {"稳定运行", "重点跟踪", "异常监测", "停产"})

    def test_alert_status(self):
        self.assertEqual(set(C.ALERT_STATUS_COLOR.keys()),
                         {"处理中", "已纳入监测", "已闭环", "已忽略"})


class TestTableNames(unittest.TestCase):
    def test_use_new_prefix(self):
        """老的 电力看经济_ 8 张表保持不动，新表用 电力驾驶舱_"""
        self.assertEqual(C.TABLE_PREFIX, "电力驾驶舱")
        for key, name in C.TABLE_NAMES.items():
            self.assertTrue(name.startswith("电力驾驶舱_"), f"{key} = {name}")


if __name__ == "__main__":
    unittest.main()
