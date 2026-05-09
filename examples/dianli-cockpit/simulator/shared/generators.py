"""Realistic record generators for the 7 dianli-cockpit tables.

Determinism: every function takes a `seed` for reproducibility. Seed=1 default
matches the spec's expected counts.
"""
import datetime
import random
from typing import List, Dict
from simulator.shared.constants import (
    DISTRICT_COLOR, INDUSTRY_COLOR, ALERT_TYPES, INSIGHT_TYPES,
)

DISTRICTS = list(DISTRICT_COLOR.keys())
INDUSTRIES = list(INDUSTRY_COLOR.keys())

DISTRICT_WEIGHT = {
    "惠城区": 1.4, "惠阳区": 1.2, "大亚湾区": 1.5, "仲恺高新区": 1.6,
    "博罗县": 0.9, "惠东县": 0.7, "龙门县": 0.5,
}
INDUSTRY_WEIGHT = {
    "电子信息": 1.3, "石化能源": 1.6, "装备制造": 1.2,
    "汽车制造": 1.0, "纺织食品": 0.8, "新材料": 0.9,
}


def generate_industry_metrics(seed: int = 1) -> List[Dict]:
    """504 = 12 月 × 7 区 × 6 行业。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    records = []
    # 最近 12 个月（按月初）
    base_month = today.replace(day=1)
    months = []
    for offset in range(11, -1, -1):
        # 直接用 (month - offset) 计算，处理跨年
        y = base_month.year
        m = base_month.month - offset
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")

    for month_str in months:
        for d in DISTRICTS:
            for i in INDUSTRIES:
                base = 1500 * DISTRICT_WEIGHT[d] * INDUSTRY_WEIGHT[i]
                records.append({
                    "月份": month_str,
                    "区域": d,
                    "行业": i,
                    "行业用电_MWh": round(base * rng.uniform(0.85, 1.15), 1),
                    "同比_%": round(rng.uniform(-15, 25), 1),
                    "景气指数": round(rng.uniform(50, 95), 1),
                    "产出指数": round(rng.uniform(50, 100), 1),
                })
    return records


def generate_enterprises(seed: int = 1) -> List[Dict]:
    """1500 = 50 企业 × 30 天。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    statuses_weighted = ["稳定运行"] * 4 + ["重点跟踪"] * 2 + \
                        ["异常监测"] + ["停产"]

    companies = []
    for i in range(50):
        d = rng.choice(DISTRICTS)
        ind = rng.choice(INDUSTRIES)
        companies.append({
            "name": f"{d}{ind}示范企业{i+1:03d}",
            "district": d,
            "industry": ind,
            "base_status": rng.choice(statuses_weighted),
            "base_power": rng.uniform(80, 380),
        })

    records = []
    for c in companies:
        for day_offset in range(-29, 1):
            date = (today + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            records.append({
                "企业名称": c["name"],
                "日期": date,
                "区域": c["district"],
                "行业": c["industry"],
                "今日用电_MWh": round(c["base_power"] * rng.uniform(0.80, 1.20), 1),
                "同比_%": round(rng.uniform(-15, 20), 1),
                "开工指数": round(rng.uniform(60, 100), 1),
                "风险指数": round(rng.uniform(10, 90), 1),
                "状态": (c["base_status"] if rng.random() > 0.05
                         else rng.choice(statuses_weighted)),
            })
    return records


def generate_load_curve(seed: int = 1) -> List[Dict]:
    """168 = 7 区 × 24 小时。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    records = []
    for h in range(24):
        ts = datetime.datetime.combine(today, datetime.time(h, 0)) \
                              .strftime("%Y-%m-%d %H:%M")
        # 早高峰 8-10、晚高峰 19-21
        if 8 <= h <= 10 or 19 <= h <= 21:
            diurnal = 1.0
        elif 7 <= h <= 22:
            diurnal = 0.85
        else:
            diurnal = 0.55
        for d in DISTRICTS:
            base = 350 * DISTRICT_WEIGHT[d] * diurnal
            load = round(base * rng.uniform(0.90, 1.10), 1)
            records.append({
                "时间戳": ts,
                "区域": d,
                "实时负荷_MW": load,
                "预测负荷_MW": round(load * rng.uniform(0.95, 1.05), 1),
                "累计用电_MWh": round(load * (h + 1) * rng.uniform(0.95, 1.05), 1),
            })
    return records


def generate_alerts(seed: int = 1) -> List[Dict]:
    """~80。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    levels = ["黄色"] * 50 + ["橙色"] * 25 + ["红色"] * 8
    statuses = ["处理中"] * 30 + ["已纳入监测"] * 35 + ["已闭环"] * 18
    rng.shuffle(levels)
    rng.shuffle(statuses)
    n = min(len(levels), len(statuses))

    records = []
    for i in range(n):
        offset_min = rng.randint(-7 * 24 * 60, 0)
        ts = (datetime.datetime.combine(today, datetime.time(8, 0))
              + datetime.timedelta(minutes=offset_min)).strftime("%Y-%m-%d %H:%M")
        d = rng.choice(DISTRICTS)
        atype = rng.choice(ALERT_TYPES)
        records.append({
            "事件编号": f"AL-{i+1:04d}",
            "时间": ts,
            "区域": d,
            "等级": levels[i],
            "类型": atype,
            "标题": f"{d}{atype}指标偏离阈值",
            "说明": f"仿真机器人检测到{d}{atype}与历史曲线出现偏离，建议纳入电力看经济专题观察。",
            "状态": statuses[i],
        })
    return records


def generate_renewable(seed: int = 1) -> List[Dict]:
    """210 = 7 区 × 30 天。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    types = ["光伏", "储能", "充电"]
    records = []
    for d in DISTRICTS:
        for day_offset in range(-29, 1):
            records.append({
                "日期": (today + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d"),
                "区域": d,
                "光伏出力_MW": round(rng.uniform(20, 120), 1),
                "储能电量_MWh": round(rng.uniform(10, 80), 1),
                "充电次数": rng.randint(50, 600),
                "类型": rng.choice(types),
            })
    return records


def generate_insights(seed: int = 1) -> List[Dict]:
    """~30。"""
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    n = 30
    templates = {
        "产能波动": "{d}{ind}行业近{w}周用电同比波动 {p}%，结合历史曲线判断为产能爬坡期，建议持续观察。",
        "节能建议": "{d}{ind}行业开工指数 {oi} 高位，但单位用电产出比偏低，建议联合园区做能耗优化排查。",
        "异常解释": "{d}{ind}行业本周用电骤降 {drop}%，与计划检修档期吻合，非异常事件。",
        "政策机会": "{d}{ind}行业景气指数突破 {pi}，符合战略性新兴产业扶持条件，可推荐政策对接。",
        "新园区监测": "{d}新落地{ind}产业园近 30 天用电增长 {g}%，建议纳入重点监测名单。",
    }
    records = []
    for i in range(n):
        ts = (datetime.datetime.combine(today, datetime.time(rng.randint(8, 20), 0))
              - datetime.timedelta(days=rng.randint(0, 14))).strftime("%Y-%m-%d %H:%M")
        d = rng.choice(DISTRICTS)
        ind = rng.choice(INDUSTRIES)
        itype = rng.choice(INSIGHT_TYPES)
        content = templates[itype].format(
            d=d, ind=ind,
            w=rng.randint(2, 6), p=rng.randint(-15, 18),
            oi=rng.randint(70, 95), pi=rng.randint(85, 95),
            drop=rng.randint(15, 45), g=rng.randint(20, 80),
        )
        records.append({
            "时间": ts,
            "区域": d,
            "类型": itype,
            "洞察内容": content,
            "置信分": rng.choices([3, 4, 5], weights=[2, 5, 3])[0],
        })
    return records


def generate_config() -> List[Dict]:
    """~12 KV，硬编码不依赖 seed。"""
    return [
        {"参数": "红色预警阈值", "值": "80", "说明": "风险指数 ≥ 此值触发红色预警"},
        {"参数": "橙色预警阈值", "值": "60", "说明": "风险指数 ≥ 此值触发橙色预警"},
        {"参数": "黄色预警阈值", "值": "40", "说明": "风险指数 ≥ 此值触发黄色预警"},
        {"参数": "KPI_今日总用电_目标", "值": "30000", "说明": "MWh，对照线"},
        {"参数": "KPI_平均景气指数_警戒线", "值": "50", "说明": "低于此值变红"},
        {"参数": "KPI_活跃预警_警戒数", "值": "10", "说明": "超过此数 KPI 卡片闪烁"},
        {"参数": "演示模式", "值": "on", "说明": "on/off。on 时模拟器后台跑剧本"},
        {"参数": "更新频率_秒", "值": "10", "说明": "用电曲线 worker 周期"},
        {"参数": "色板_红色预警", "值": "#FF3D5F", "说明": "前端读，不在 vika options 里"},
        {"参数": "色板_橙色预警", "值": "#FF6B35", "说明": ""},
        {"参数": "色板_主背景", "值": "#0A1929", "说明": "驾驶舱底色"},
        {"参数": "色板_主强调", "值": "#00D9FF", "说明": "霓虹青"},
    ]
