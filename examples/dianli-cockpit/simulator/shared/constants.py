"""Shared constants: districts, industries, color mappings, enums.

Color values are vika SingleSelect/MultiSelect color names — must be plain
strings (not {name: ...} objects), per the configured deployment schema.
"""

# vika 目标环境支持的 option color 名（实测）
VIKA_VALID_COLORS = {
    "gray", "red", "orange", "yellow", "green", "cyan",
    "blue", "purple", "pink", "brown", "dustRed", "lime",
    "magenta", "geekBlue", "gold", "volcano",
}

# 7 区固定配色
DISTRICT_COLOR = {
    "惠城区": "blue",
    "惠阳区": "green",
    "大亚湾区": "cyan",
    "仲恺高新区": "purple",
    "博罗县": "orange",
    "惠东县": "red",
    "龙门县": "yellow",
}

# 6 行业固定配色
INDUSTRY_COLOR = {
    "电子信息": "cyan",
    "石化能源": "red",
    "装备制造": "blue",
    "汽车制造": "orange",
    "纺织食品": "green",
    "新材料": "purple",
}

# 预警等级
ALERT_LEVEL_COLOR = {
    "红色": "red",
    "橙色": "orange",
    "黄色": "yellow",
}

# 预警类型（5 种）
ALERT_TYPES = ["负荷波动", "行业景气", "设备风险", "用电异常", "新能源波动"]

# 预警状态
ALERT_STATUS_COLOR = {
    "处理中": "red",
    "已纳入监测": "orange",
    "已闭环": "green",
    "已忽略": "gray",
}

# 重点企业状态
ENTERPRISE_STATUS_COLOR = {
    "稳定运行": "green",
    "重点跟踪": "blue",
    "异常监测": "orange",
    "停产": "red",
}

# 新能源类型
RENEWABLE_TYPE_COLOR = {
    "光伏": "yellow",
    "储能": "blue",
    "充电": "green",
}

# 机器人洞察类型
INSIGHT_TYPES = ["产能波动", "节能建议", "异常解释", "政策机会", "新园区监测"]

# 表名前缀（新表用 电力驾驶舱_，老的 电力看经济_ 8 张保持不动）
TABLE_PREFIX = "电力驾驶舱"
TABLE_NAMES = {
    "industry": f"{TABLE_PREFIX}_行业指标",
    "enterprise": f"{TABLE_PREFIX}_重点企业",
    "load_curve": f"{TABLE_PREFIX}_用电曲线",
    "alert": f"{TABLE_PREFIX}_预警事件",
    "renewable": f"{TABLE_PREFIX}_新能源充电",
    "insight": f"{TABLE_PREFIX}_机器人洞察",
    "config": f"{TABLE_PREFIX}_配置参数",
}
