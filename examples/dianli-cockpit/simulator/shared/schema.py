"""Datasheet schema definitions for the 7 dianli-cockpit tables.

Each schema is a dict with `name` (str) and `fields` (list of field dicts).
Each field has `name`, `type`, and optional `property`.

Schema field types and property formats are calibrated for the e报表 private
deployment (color is string, dateFormat is enum, Number defaultValue is str,
Rating icon is emoji slug, etc. — see SPEC.md §10).
"""
from simulator.shared.constants import (
    DISTRICT_COLOR, INDUSTRY_COLOR, ALERT_LEVEL_COLOR, ALERT_TYPES,
    ALERT_STATUS_COLOR, ENTERPRISE_STATUS_COLOR, RENEWABLE_TYPE_COLOR,
    INSIGHT_TYPES, TABLE_NAMES,
)


def _options(mapping):
    """Convert {name: color} dict to vika options list."""
    return [{"name": n, "color": c} for n, c in mapping.items()]


def _options_from_list(names, color="gray"):
    return [{"name": n, "color": color} for n in names]


_DISTRICT_OPTIONS = _options(DISTRICT_COLOR)
_INDUSTRY_OPTIONS = _options(INDUSTRY_COLOR)


# ---------- ① 行业指标 ----------
INDUSTRY_METRICS = {
    "name": TABLE_NAMES["industry"],
    "fields": [
        {"name": "月份", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM", "includeTime": False, "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "行业", "type": "SingleSelect", "property": {"options": _INDUSTRY_OPTIONS}},
        {"name": "行业用电_MWh", "type": "Number", "property": {"precision": 1, "symbol": "MWh"}},
        {"name": "同比_%", "type": "Number", "property": {"precision": 1, "symbol": "%"}},
        {"name": "景气指数", "type": "Number", "property": {"precision": 1}},
        {"name": "产出指数", "type": "Number", "property": {"precision": 1}},
    ],
}


# ---------- ② 重点企业 ----------
ENTERPRISE = {
    "name": TABLE_NAMES["enterprise"],
    "fields": [
        # 企业名称是 primary（vika 自动创建的"标题"字段我们当企业名用）
        {"name": "日期", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": False, "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "行业", "type": "SingleSelect", "property": {"options": _INDUSTRY_OPTIONS}},
        {"name": "今日用电_MWh", "type": "Number", "property": {"precision": 1, "symbol": "MWh"}},
        {"name": "同比_%", "type": "Number", "property": {"precision": 1, "symbol": "%"}},
        {"name": "开工指数", "type": "Number", "property": {"precision": 1}},
        {"name": "风险指数", "type": "Number", "property": {"precision": 1}},
        {"name": "状态", "type": "SingleSelect",
         "property": {"options": _options(ENTERPRISE_STATUS_COLOR)}},
    ],
    "primary_alias": "企业名称",
}


# ---------- ③ 用电曲线 ----------
LOAD_CURVE = {
    "name": TABLE_NAMES["load_curve"],
    "fields": [
        {"name": "时间戳", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": True,
                      "timeFormat": "HH:mm", "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "实时负荷_MW", "type": "Number", "property": {"precision": 1, "symbol": "MW"}},
        {"name": "预测负荷_MW", "type": "Number", "property": {"precision": 1, "symbol": "MW"}},
        {"name": "累计用电_MWh", "type": "Number", "property": {"precision": 1, "symbol": "MWh"}},
    ],
}


# ---------- ④ 预警事件 ----------
ALERT = {
    "name": TABLE_NAMES["alert"],
    "fields": [
        {"name": "时间", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": True,
                      "timeFormat": "HH:mm", "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "等级", "type": "SingleSelect",
         "property": {"options": _options(ALERT_LEVEL_COLOR)}},
        {"name": "类型", "type": "SingleSelect",
         "property": {"options": _options_from_list(ALERT_TYPES, color="gray")}},
        {"name": "标题", "type": "Text"},
        {"name": "说明", "type": "Text"},
        {"name": "状态", "type": "SingleSelect",
         "property": {"options": _options(ALERT_STATUS_COLOR)}},
    ],
    "primary_alias": "事件编号",
}


# ---------- ⑤ 新能源充电 ----------
RENEWABLE = {
    "name": TABLE_NAMES["renewable"],
    "fields": [
        {"name": "日期", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": False, "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "光伏出力_MW", "type": "Number", "property": {"precision": 1, "symbol": "MW"}},
        {"name": "储能电量_MWh", "type": "Number", "property": {"precision": 1, "symbol": "MWh"}},
        {"name": "充电次数", "type": "Number", "property": {"precision": 0}},
        {"name": "类型", "type": "SingleSelect",
         "property": {"options": _options(RENEWABLE_TYPE_COLOR)}},
    ],
}


# ---------- ⑥ 机器人洞察 ----------
INSIGHT = {
    "name": TABLE_NAMES["insight"],
    "fields": [
        {"name": "时间", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": True,
                      "timeFormat": "HH:mm", "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "类型", "type": "SingleSelect",
         "property": {"options": _options_from_list(INSIGHT_TYPES, color="cyan")}},
        {"name": "洞察内容", "type": "Text"},
        {"name": "置信分", "type": "Rating", "property": {"icon": "star", "max": 5}},
    ],
}


# ---------- ⑦ 配置参数 ----------
CONFIG = {
    "name": TABLE_NAMES["config"],
    "fields": [
        {"name": "值", "type": "Text"},
        {"name": "说明", "type": "Text"},
    ],
    "primary_alias": "参数",
}


ALL_SCHEMAS = [INDUSTRY_METRICS, ENTERPRISE, LOAD_CURVE, ALERT, RENEWABLE, INSIGHT, CONFIG]
