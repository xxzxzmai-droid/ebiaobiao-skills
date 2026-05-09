# Phase A · 数据骨架 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 报表里建好 7 张电力看经济数据表（含正确字段类型）+ 灌入 ~2500 条幂等真实仿真种子数据，能在 vika UI 直观看到结构与数据。

**Architecture:** Python 3.10+ 单线程脚本，shell 调用 `ebiao_fusion.py` CLI 与 vika 通讯（重用已有工具，避免重写 HTTP 客户端）。`simulator/shared/` 下分 5 个职责清晰的模块（schema 定义 / vika 薄封装 / 表+字段创建 / 数据生成 / 幂等灌入）。TDD：每模块先写 unit test（mock subprocess），再写实现。

**Tech Stack:** Python 3.10+ / `subprocess` / `argparse` / `unittest.mock` / `pytest`（dev only） / 复用 `~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py` 作为 vika 通讯后端

---

## 前置条件

无须手动清表。新表用 `电力驾驶舱_*` 前缀（见 Task 2 `TABLE_PREFIX = "电力驾驶舱"`），跟老的 `电力看经济_*` 8 张表（配置参数/行业经济指标/重点企业用电/预警事件/新能源与充电/新能源与充电 2/新能源与充电 3/机器人洞察）共存不冲突。

老 8 张数据可保留作历史对比，将来想清随时去 vika UI 移到回收舱即可，不影响本计划。

---

## 文件结构（Phase A 末态）

```
examples/dianli-cockpit/
├── SPEC.md                                    （已存在）
├── plans/
│   └── 2026-05-09-phase-a-data.md             （此文件）
├── simulator/
│   ├── __init__.py                            空，标记 package
│   ├── shared/
│   │   ├── __init__.py                        空
│   │   ├── schema.py                          7 张表的 schema 字典 + ALL_SCHEMAS 列表
│   │   ├── vika.py                            VikaClient（薄 subprocess 封装）
│   │   ├── bootstrap.py                       create_or_get_datasheet / ensure_fields
│   │   ├── generators.py                      7 个 generate_* 函数（504/1500/168/80/210/30/15）
│   │   ├── seeder.py                          seed_table 幂等批量写
│   │   └── constants.py                       区域/行业/配色等共享常量
│   ├── cli.py                                 CLI: bootstrap 子命令入口
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                        共享 fixture
│       ├── test_schema.py                     schema 字段类型 / property 校验
│       ├── test_vika.py                       VikaClient subprocess 调用拼装
│       ├── test_bootstrap.py                  create_or_get / 字段补全
│       ├── test_generators.py                 数量、值范围、分布
│       └── test_seeder.py                     幂等 + 批量切分
└── README.md                                  Phase A 30 秒上手
```

每个文件单一职责：**schema 只定义，vika 只通讯，bootstrap 只建表/字段，generators 只产数据，seeder 只灌入**。CLI 把它们拼起来。

---

## Task 1: 项目骨架与依赖

**Files:**
- Create: `examples/dianli-cockpit/simulator/__init__.py`
- Create: `examples/dianli-cockpit/simulator/shared/__init__.py`
- Create: `examples/dianli-cockpit/simulator/tests/__init__.py`
- Create: `examples/dianli-cockpit/simulator/tests/conftest.py`
- Create: `examples/dianli-cockpit/requirements.txt`
- Create: `examples/dianli-cockpit/README.md`

- [ ] **Step 1: 建目录结构**

```bash
cd ~/projects/ebiaobiao-skills/examples/dianli-cockpit
mkdir -p simulator/shared simulator/tests
touch simulator/__init__.py simulator/shared/__init__.py simulator/tests/__init__.py
```

- [ ] **Step 2: 创建 `requirements.txt`**

```
pytest>=7.0
```

（**只有** dev 依赖。运行时 stdlib only — 这是 skill 的设计原则，便于同事开箱即用。）

- [ ] **Step 3: 创建 `simulator/tests/conftest.py`**

```python
"""Shared pytest fixtures."""
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_runner():
    """Returns a runner stub that records calls and returns canned responses.

    Tests configure responses via mock_runner.set_response(args_prefix, payload).
    Default returns success with empty data.
    """
    runner = MagicMock()
    runner.return_value = {"success": True, "code": 200, "data": {}, "message": "OK"}
    return runner
```

- [ ] **Step 4: 创建 `examples/dianli-cockpit/README.md`** （30 秒上手）

```markdown
# 电力看经济驾驶舱 · Phase A 数据骨架

设计说明见 [SPEC.md](SPEC.md)。本目录的 Phase A 只做数据层：建 7 张表 + 灌 ~2500 条仿真种子。

## 跑起来

前提：父项目已配好 `.env.local`（参见仓库根 README）；老 `电力看经济_*` 8 张表已在 vika UI 清完。

```bash
cd ~/projects/ebiaobiao-skills/examples/dianli-cockpit

# 跑测试（不连真实 vika）
python -m pytest simulator/tests -v

# 干跑：打印将要发起的 API 调用，不写
python -m simulator.cli bootstrap --dry-run

# 真灌（首次 ~3 分钟）
python -m simulator.cli bootstrap

# 重灌（清空 records 但保留 schema）
python -m simulator.cli bootstrap --reseed

# 增量补：跳过已存在的记录
python -m simulator.cli bootstrap --skip-existing
```

跑完进 vika UI 验证：左侧目录树应该有 7 张 `电力看经济_*` 新表，每张表打开能看到正确的字段类型与彩虹标签。

## 项目结构

见 [SPEC.md §4.4](../SPEC.md)。
```

- [ ] **Step 5: 提交骨架**

```bash
cd ~/projects/ebiaobiao-skills
git add examples/dianli-cockpit/simulator examples/dianli-cockpit/requirements.txt examples/dianli-cockpit/README.md
git commit -m "feat(dianli-cockpit): scaffold Phase A directory structure"
```

---

## Task 2: 共享常量 `constants.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/constants.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_constants.py`

- [ ] **Step 1: 写测试 `test_constants.py`**

```python
"""Validate shared constants are well-formed and consistent."""
from simulator.shared import constants as C


def test_districts_count_and_colors():
    assert len(C.DISTRICT_COLOR) == 7
    assert set(C.DISTRICT_COLOR.keys()) == {
        "惠城区", "惠阳区", "大亚湾区", "仲恺高新区",
        "博罗县", "惠东县", "龙门县",
    }
    # color 必须是单字符串（目标环境 schema 实测要求）
    for name, color in C.DISTRICT_COLOR.items():
        assert isinstance(color, str), f"{name} color must be str, got {type(color)}"
        assert color in C.VIKA_VALID_COLORS, f"{name}: {color}"


def test_industries_count_and_colors():
    assert len(C.INDUSTRY_COLOR) == 6
    assert set(C.INDUSTRY_COLOR.keys()) == {
        "电子信息", "石化能源", "装备制造",
        "汽车制造", "纺织食品", "新材料",
    }
    for name, color in C.INDUSTRY_COLOR.items():
        assert isinstance(color, str)
        assert color in C.VIKA_VALID_COLORS


def test_alert_levels():
    assert C.ALERT_LEVEL_COLOR == {"红色": "red", "橙色": "orange", "黄色": "yellow"}


def test_enterprise_status():
    assert set(C.ENTERPRISE_STATUS_COLOR.keys()) == {
        "稳定运行", "重点跟踪", "异常监测", "停产",
    }


def test_alert_status():
    assert set(C.ALERT_STATUS_COLOR.keys()) == {
        "处理中", "已纳入监测", "已闭环", "已忽略",
    }
```

- [ ] **Step 2: 跑测试，确认 fail（模块还没建）**

```bash
cd ~/projects/ebiaobiao-skills/examples/dianli-cockpit
python -m pytest simulator/tests/test_constants.py -v
```

Expected: `ModuleNotFoundError: No module named 'simulator.shared.constants'` 或类似 import error。

- [ ] **Step 3: 写 `simulator/shared/constants.py`**

```python
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

# 表名前缀
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
```

- [ ] **Step 4: 跑测试，pass**

```bash
python -m pytest simulator/tests/test_constants.py -v
```

Expected: `5 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/constants.py simulator/tests/test_constants.py
git commit -m "feat(dianli-cockpit): shared constants for districts/industries/statuses"
```

---

## Task 3: Schema 定义 `schema.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/schema.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_schema.py`

- [ ] **Step 1: 写测试 `test_schema.py`**

```python
"""Validate the 7 datasheet schema definitions."""
import pytest
from simulator.shared import schema, constants as C


def test_seven_schemas():
    assert len(schema.ALL_SCHEMAS) == 7


def test_schema_names_match_constants():
    expected_names = set(C.TABLE_NAMES.values())
    actual_names = {s["name"] for s in schema.ALL_SCHEMAS}
    assert expected_names == actual_names


def test_every_field_has_name_and_type():
    for s in schema.ALL_SCHEMAS:
        for f in s["fields"]:
            assert "name" in f and isinstance(f["name"], str)
            assert "type" in f and isinstance(f["type"], str)


def test_singleselect_options_use_string_color():
    """报表目标环境要求 color 是字符串，不是 {name: ...} 对象。"""
    for s in schema.ALL_SCHEMAS:
        for f in s["fields"]:
            if f["type"] in ("SingleSelect", "MultiSelect"):
                opts = f.get("property", {}).get("options", [])
                assert opts, f"{s['name']}.{f['name']} has no options"
                for opt in opts:
                    assert isinstance(opt["color"], str), \
                        f"{s['name']}.{f['name']} option {opt['name']} color must be str"


def test_datetime_dateformat_in_enum():
    """报表目标环境 dateFormat 必须是枚举集之一。"""
    valid_formats = {
        "YYYY/MM/DD", "YYYY-MM-DD", "DD/MM/YYYY",
        "YYYY-MM", "MM-DD", "YYYY", "MM", "DD",
    } | {str(i) for i in range(8)}
    for s in schema.ALL_SCHEMAS:
        for f in s["fields"]:
            if f["type"] in ("DateTime", "CreatedTime", "LastModifiedTime"):
                fmt = f.get("property", {}).get("dateFormat")
                assert fmt in valid_formats, \
                    f"{s['name']}.{f['name']} dateFormat={fmt!r}"


def test_number_defaultvalue_is_string():
    """报表目标环境要求 Number.defaultValue 是字符串。"""
    for s in schema.ALL_SCHEMAS:
        for f in s["fields"]:
            if f["type"] == "Number":
                dv = f.get("property", {}).get("defaultValue")
                if dv is not None:
                    assert isinstance(dv, str), \
                        f"{s['name']}.{f['name']} defaultValue must be str"


def test_rating_icon_is_emoji_slug():
    valid_slugs = {"star", "heart", "fire", "thumbs_up", "white_check_mark"}
    for s in schema.ALL_SCHEMAS:
        for f in s["fields"]:
            if f["type"] == "Rating":
                icon = f.get("property", {}).get("icon")
                assert icon in valid_slugs, \
                    f"{s['name']}.{f['name']} icon={icon!r} not a slug"


def test_industry_metrics_has_required_fields():
    s = next(s for s in schema.ALL_SCHEMAS if s["name"] == C.TABLE_NAMES["industry"])
    field_names = {f["name"] for f in s["fields"]}
    assert {"月份", "区域", "行业", "行业用电_MWh",
            "同比_%", "景气指数", "产出指数"} <= field_names


def test_enterprise_has_required_fields():
    s = next(s for s in schema.ALL_SCHEMAS if s["name"] == C.TABLE_NAMES["enterprise"])
    field_names = {f["name"] for f in s["fields"]}
    assert {"企业名称", "日期", "区域", "行业", "今日用电_MWh",
            "同比_%", "开工指数", "风险指数", "状态"} <= field_names


def test_alert_status_options_match_constants():
    s = next(s for s in schema.ALL_SCHEMAS if s["name"] == C.TABLE_NAMES["alert"])
    status_field = next(f for f in s["fields"] if f["name"] == "状态")
    opts = {o["name"]: o["color"] for o in status_field["property"]["options"]}
    assert opts == C.ALERT_STATUS_COLOR
```

- [ ] **Step 2: 跑测试，确认 fail**

```bash
python -m pytest simulator/tests/test_schema.py -v
```

Expected: ImportError on `simulator.shared.schema`.

- [ ] **Step 3: 写 `simulator/shared/schema.py`**

```python
"""Datasheet schema definitions for the 7 dianli-cockpit tables.

Each schema is a dict with `name` (str) and `fields` (list of field dicts).
Each field has `name`, `type`, and optional `property`.

Schema field types and property formats are calibrated for the 报表 configured
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
        # 企业名称是 primary，由 vika 自动创建（标题字段），我们后续 rename via UI 或保留默认
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
    "primary_alias": "企业名称",  # spec 要求 primary 叫 企业名称（用 update 把 vika 默认"标题"改名 — 但 API 不支持改字段名。我们填 primary 列时把内容当企业名即可。）
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
        # 主字段我们用作 事件编号 (AL-XXXX)
        {"name": "时间", "type": "DateTime",
         "property": {"dateFormat": "YYYY-MM-DD", "includeTime": True,
                      "timeFormat": "HH:mm", "autoFill": False}},
        {"name": "区域", "type": "SingleSelect", "property": {"options": _DISTRICT_OPTIONS}},
        {"name": "等级", "type": "SingleSelect", "property": {"options": _options(ALERT_LEVEL_COLOR)}},
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
        {"name": "类型", "type": "SingleSelect", "property": {"options": _options(RENEWABLE_TYPE_COLOR)}},
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
        # primary 字段当作"参数"
        {"name": "值", "type": "Text"},
        {"name": "说明", "type": "Text"},
    ],
    "primary_alias": "参数",
}


ALL_SCHEMAS = [INDUSTRY_METRICS, ENTERPRISE, LOAD_CURVE, ALERT, RENEWABLE, INSIGHT, CONFIG]
```

- [ ] **Step 4: 跑测试，pass**

```bash
python -m pytest simulator/tests/test_schema.py -v
```

Expected: `9 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/schema.py simulator/tests/test_schema.py
git commit -m "feat(dianli-cockpit): 7-table schema with configured-deployment-correct property formats"
```

---

## Task 4: VikaClient 薄封装 `vika.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/vika.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_vika.py`

设计：`VikaClient` 通过子进程调用 `~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py`，避免重写 HTTP 客户端。`runner` 依赖注入便于测试。

- [ ] **Step 1: 写测试 `test_vika.py`**

```python
"""VikaClient 调子进程的命令拼装与响应解析。"""
import json
import pytest
from unittest.mock import MagicMock, patch
from simulator.shared.vika import VikaClient, VikaError


@pytest.fixture
def fake_runner():
    runner = MagicMock()
    return runner


def test_search_nodes_calls_correct_args(fake_runner):
    fake_runner.return_value = {
        "success": True, "code": 200,
        "data": {"nodes": [{"id": "dst123", "name": "T"}]},
    }
    c = VikaClient(runner=fake_runner)
    result = c.search_nodes(query="电力看经济", type="Datasheet")
    fake_runner.assert_called_once()
    args = fake_runner.call_args[0][0]
    assert "search-nodes" in args
    assert "--query" in args and "电力看经济" in args
    assert "--type" in args and "Datasheet" in args
    assert result == [{"id": "dst123", "name": "T"}]


def test_create_datasheet_returns_dst_id(fake_runner):
    fake_runner.return_value = {
        "success": True, "code": 200,
        "data": {"id": "dstNew", "fields": [{"id": "fldA", "name": "标题"}]},
    }
    c = VikaClient(runner=fake_runner)
    result = c.create_datasheet("电力看经济_测试")
    assert result["id"] == "dstNew"
    args = fake_runner.call_args[0][0]
    # CLI 签名: create-datasheet <payload_json>
    assert args[0] == "create-datasheet"
    payload = json.loads(args[1])
    assert payload["name"] == "电力看经济_测试"


def test_list_fields(fake_runner):
    fake_runner.return_value = {
        "success": True,
        "data": {"fields": [{"id": "fld1", "name": "区域", "type": "SingleSelect"}]},
    }
    c = VikaClient(runner=fake_runner)
    fields = c.list_fields("dstABC")
    args = fake_runner.call_args[0][0]
    # CLI 签名: fields <datasheet_id>
    assert args == ["fields", "dstABC"]
    assert fields[0]["name"] == "区域"


def test_create_field_with_property(fake_runner):
    fake_runner.return_value = {"success": True, "data": {"id": "fldNew"}}
    c = VikaClient(runner=fake_runner)
    c.create_field("dstABC", "区域", "SingleSelect",
                   property={"options": [{"name": "惠城区", "color": "blue"}]})
    args = fake_runner.call_args[0][0]
    # CLI 签名: create-field <datasheet_id> <payload_json>
    assert args[0] == "create-field"
    assert args[1] == "dstABC"
    payload = json.loads(args[2])
    assert payload["name"] == "区域"
    assert payload["type"] == "SingleSelect"
    assert payload["property"]["options"][0]["color"] == "blue"


def test_create_records_chunks_to_10(fake_runner):
    """单批硬上限 10 条，client 必须自动切分。"""
    fake_runner.return_value = {"success": True, "data": {"records": []}}
    c = VikaClient(runner=fake_runner)
    records = [{"区域": "惠城区"} for _ in range(25)]
    c.create_records("dstABC", records)
    # 25 → 10/10/5，应调 3 次
    assert fake_runner.call_count == 3
    # 每次都是: create-records <dst> <records_json>
    first = fake_runner.call_args_list[0][0][0]
    assert first[0] == "create-records"
    assert first[1] == "dstABC"
    payload = json.loads(first[2])
    assert isinstance(payload, list)
    assert payload[0] == {"fields": {"区域": "惠城区"}}


def test_list_records_paginates(fake_runner):
    page1 = [{"recordId": f"rec{i}", "fields": {}} for i in range(1000)]
    page2 = [{"recordId": f"recX{i}", "fields": {}} for i in range(50)]
    fake_runner.side_effect = [
        {"success": True, "data": {"records": page1, "total": 1050}},
        {"success": True, "data": {"records": page2, "total": 1050}},
    ]
    c = VikaClient(runner=fake_runner)
    all_records = c.list_all_records("dstABC")
    assert len(all_records) == 1050


def test_failure_raises_vikaerror(fake_runner):
    fake_runner.return_value = {
        "success": False, "code": 400,
        "message": "Invalid value for fields[X].property",
    }
    c = VikaClient(runner=fake_runner)
    with pytest.raises(VikaError) as exc:
        c.create_datasheet("X")
    assert "Invalid value" in str(exc.value)


def test_subprocess_runner_calls_ebiao_fusion(monkeypatch):
    """默认 runner 真的去调 ebiao_fusion.py（不实际跑，mock subprocess.run）。"""
    from simulator.shared import vika
    captured = {}

    class FakeProc:
        returncode = 0
        stdout = '{"success": true, "data": {"nodes": []}}'
        stderr = ""

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(vika, "EBIAO_FUSION_SCRIPT", "/fake/ebiao_fusion.py")
    result = vika._subprocess_runner(["search-nodes", "--query", "X"])
    assert result["success"] is True
    assert "/fake/ebiao_fusion.py" in captured["cmd"]
    assert "search-nodes" in captured["cmd"]
```

- [ ] **Step 2: 跑测试 fail**

```bash
python -m pytest simulator/tests/test_vika.py -v
```

Expected: ImportError.

- [ ] **Step 3: 写 `simulator/shared/vika.py`**

```python
"""Thin wrapper around ebiao_fusion.py CLI.

Uses subprocess to delegate Vika REST calls to the existing CLI tool. This
avoids reimplementing HTTP/auth/retries — the CLI already handles them.

For tests, inject a custom `runner` callable that takes argv list and returns
the parsed JSON response dict.
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

EBIAO_FUSION_SCRIPT = os.environ.get(
    "EBIAO_FUSION_SCRIPT",
    str(Path.home() / ".codex" / "skills" / "ebiaobiao-fusion-api" / "scripts" / "ebiao_fusion.py"),
)


class VikaError(RuntimeError):
    def __init__(self, code, message, payload=None):
        self.code = code
        self.message = message
        self.payload = payload
        super().__init__(f"vika [{code}] {message}")


Runner = Callable[[List[str]], dict]


def _subprocess_runner(args: List[str]) -> dict:
    """Default runner: shell out to ebiao_fusion.py, parse its JSON stdout.

    Inherits parent env (so EBIAOBIAO_API_TOKEN etc. flow through).
    """
    cmd = ["python3", EBIAO_FUSION_SCRIPT, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise VikaError(
            code="subprocess",
            message=f"exit={proc.returncode}, stderr={proc.stderr.strip()[:200]}",
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise VikaError(
            code="parse",
            message=f"non-JSON output: {proc.stdout[:200]}",
        )


def _chunks(seq, size):
    seq = list(seq)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


class VikaClient:
    """High-level operations against vika via the ebiao_fusion CLI."""
    BATCH_SIZE = 10
    PAGE_SIZE_MAX = 1000

    def __init__(self, runner: Optional[Runner] = None):
        self._runner = runner or _subprocess_runner

    def _call(self, args: List[str]) -> dict:
        resp = self._runner(args)
        if not resp.get("success"):
            raise VikaError(
                code=resp.get("code", "?"),
                message=resp.get("message", "unknown"),
                payload=resp,
            )
        return resp.get("data") or {}

    # ---------- nodes ----------
    def search_nodes(self, *, query=None, type="Datasheet", permissions=None):
        # CLI: search-nodes [--query X] [--type T] [--permissions 0,1,...]
        args = ["search-nodes"]
        if query: args += ["--query", query]
        if type: args += ["--type", type]
        if permissions is not None: args += ["--permissions", str(permissions)]
        return self._call(args).get("nodes", [])

    # ---------- datasheets ----------
    def create_datasheet(self, name: str, *, folder_id=None, fields=None) -> dict:
        # CLI: create-datasheet <payload_json>
        payload = {"name": name}
        if folder_id: payload["folderId"] = folder_id
        if fields: payload["fields"] = fields
        return self._call(["create-datasheet", json.dumps(payload, ensure_ascii=False)])

    # ---------- fields ----------
    def list_fields(self, dst_id: str) -> list:
        # CLI: fields <datasheet_id>
        return self._call(["fields", dst_id]).get("fields", [])

    def create_field(self, dst_id: str, name: str, type: str,
                     property: Optional[dict] = None) -> dict:
        # CLI: create-field <datasheet_id> <payload_json>
        payload = {"name": name, "type": type}
        if property is not None: payload["property"] = property
        return self._call(["create-field", dst_id,
                           json.dumps(payload, ensure_ascii=False)])

    def delete_field(self, dst_id: str, field_id: str) -> None:
        # CLI: delete-field <datasheet_id> <field_id>
        self._call(["delete-field", dst_id, field_id])

    # ---------- records ----------
    def list_records(self, dst_id: str, *, page_num=1, page_size=1000,
                     filter_formula=None, fields=None, view_id=None,
                     field_key="name") -> dict:
        # CLI: records <datasheet_id> [--page-num N] [--page-size N] ...
        args = ["records", dst_id, "--page-num", str(page_num),
                "--page-size", str(min(page_size, self.PAGE_SIZE_MAX)),
                "--field-key", field_key]
        if filter_formula: args += ["--filter-by-formula", filter_formula]
        if view_id: args += ["--view-id", view_id]
        if fields: args += ["--fields", ",".join(fields)]
        return self._call(args)

    def list_all_records(self, dst_id: str, **kwargs) -> list:
        out = []
        page = 1
        while True:
            resp = self.list_records(dst_id, page_num=page, **kwargs)
            recs = resp.get("records", [])
            out.extend(recs)
            total = resp.get("total", 0)
            if len(out) >= total or not recs:
                break
            page += 1
        return out

    def create_records(self, dst_id: str, records: list) -> list:
        # CLI: create-records <datasheet_id> <records_json>
        # records_json 是 [{fields: {...}}, ...] 数组（CLI 会自动 wrap 成 {records: [...]}）
        out = []
        for chunk in _chunks(records, self.BATCH_SIZE):
            payload = [{"fields": r} for r in chunk]
            data = self._call(["create-records", dst_id,
                               json.dumps(payload, ensure_ascii=False)])
            out.extend(data.get("records", []))
        return out

    def update_records(self, dst_id: str, records: list) -> list:
        # CLI: update-records <datasheet_id> <records_json>
        # records_json 是 [{recordId: ..., fields: {...}}, ...]
        out = []
        for chunk in _chunks(records, self.BATCH_SIZE):
            data = self._call(["update-records", dst_id,
                               json.dumps(chunk, ensure_ascii=False)])
            out.extend(data.get("records", []))
        return out

    def delete_records(self, dst_id: str, record_ids: list) -> None:
        # CLI: delete-records <datasheet_id> <comma-separated-ids>
        for chunk in _chunks(record_ids, self.BATCH_SIZE):
            self._call(["delete-records", dst_id, ",".join(chunk)])
```

> ✅ **CLI 签名实测确认**（写本计划时跑 `--help` 验证过）：
> - `create-datasheet <payload_json>` — 单个位置参，JSON 含 name/fields
> - `create-field <dst_id> <payload_json>` — JSON 含 name/type/property
> - `create-records <dst_id> <records_json>` — JSON 是 `[{fields:{...}}]` 数组，CLI 自动 wrap
> - `update-records <dst_id> <records_json>` — `[{recordId:..., fields:{...}}]`
> - `delete-records <dst_id> <comma-list>` — 逗号串
> - `delete-field <dst_id> <field_id>` — 两个位置参
> - `fields <dst_id>` — 一个位置参
> - `search-nodes` — 全 flag
>
> Task 4 测试和实现按此处实现。命令行 `--data` 这种 inline-JSON-vs-file 的纠结**不存在**，CLI 一律是 JSON 位置参，省事。

- [ ] **Step 4: 跑测试，pass**

```bash
python -m pytest simulator/tests/test_vika.py -v
```

Expected: `8 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/vika.py simulator/tests/test_vika.py
git commit -m "feat(dianli-cockpit): VikaClient thin wrapper over ebiao_fusion CLI"
```

---

## Task 5: 表 + 字段 创建逻辑 `bootstrap.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/bootstrap.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_bootstrap.py`

逻辑：
1. 对每张表，先 `search_nodes` 查同名是否存在
2. 不存在 → `create_datasheet`
3. 存在 → 复用其 ID
4. 对每个 schema 字段，查 `list_fields`，缺啥加啥
5. 返回 `{table_key: dst_id}` 映射

- [ ] **Step 1: 写测试 `test_bootstrap.py`**

```python
"""bootstrap_schemas: 创建/复用 datasheet + 补齐缺失字段。"""
from unittest.mock import MagicMock, call
from simulator.shared.bootstrap import bootstrap_schemas
from simulator.shared.schema import ALL_SCHEMAS, INDUSTRY_METRICS


def test_creates_datasheet_when_not_exists():
    client = MagicMock()
    client.search_nodes.return_value = []  # 不存在
    client.create_datasheet.return_value = {"id": "dstNEW",
                                             "fields": [{"id": "fldT", "name": "标题"}]}
    client.list_fields.return_value = [{"id": "fldT", "name": "标题", "type": "SingleText"}]
    client.create_field.return_value = {"id": "fldX"}

    result = bootstrap_schemas(client, [INDUSTRY_METRICS])
    assert result[INDUSTRY_METRICS["name"]] == "dstNEW"
    client.create_datasheet.assert_called_once_with(INDUSTRY_METRICS["name"])
    # 7 个 schema 字段 - 0 已存在 = 7 次 create_field
    assert client.create_field.call_count == len(INDUSTRY_METRICS["fields"])


def test_reuses_existing_datasheet():
    client = MagicMock()
    client.search_nodes.return_value = [{"id": "dstEXIST", "name": INDUSTRY_METRICS["name"]}]
    client.list_fields.return_value = [
        {"id": "fldT", "name": "标题", "type": "SingleText"},
        # 已经有这两个字段，应该跳过
        {"id": "fldA", "name": "月份", "type": "DateTime"},
        {"id": "fldB", "name": "区域", "type": "SingleSelect"},
    ]
    bootstrap_schemas(client, [INDUSTRY_METRICS])
    client.create_datasheet.assert_not_called()
    # 7 个 schema 字段 - 2 已存在 = 5 次 create_field
    assert client.create_field.call_count == len(INDUSTRY_METRICS["fields"]) - 2


def test_passes_property_to_create_field():
    client = MagicMock()
    client.search_nodes.return_value = []
    client.create_datasheet.return_value = {"id": "dst1", "fields": []}
    client.list_fields.return_value = []
    client.create_field.return_value = {"id": "fldX"}

    bootstrap_schemas(client, [INDUSTRY_METRICS])
    # 第一次 create_field（月份字段）应该带正确 property
    first_call = client.create_field.call_args_list[0]
    assert first_call.kwargs.get("name") == "月份"
    assert first_call.kwargs.get("type") == "DateTime"
    assert first_call.kwargs.get("property", {}).get("dateFormat") == "YYYY-MM"


def test_handles_all_seven_schemas():
    client = MagicMock()
    client.search_nodes.return_value = []
    client.create_datasheet.side_effect = [
        {"id": f"dst{i}", "fields": []} for i in range(len(ALL_SCHEMAS))
    ]
    client.list_fields.return_value = []
    client.create_field.return_value = {"id": "fldX"}

    result = bootstrap_schemas(client, ALL_SCHEMAS)
    assert len(result) == 7
    assert client.create_datasheet.call_count == 7
```

- [ ] **Step 2: fail**

```bash
python -m pytest simulator/tests/test_bootstrap.py -v
```

- [ ] **Step 3: 写 `simulator/shared/bootstrap.py`**

```python
"""Create or reuse datasheets and ensure all schema fields exist."""
from typing import Iterable, Dict
import logging

logger = logging.getLogger(__name__)


def bootstrap_schemas(client, schemas: Iterable[dict]) -> Dict[str, str]:
    """For each schema, create the datasheet if missing and add any missing fields.

    Returns: {table_name: datasheet_id}
    """
    result: Dict[str, str] = {}

    for s in schemas:
        name = s["name"]
        existing = client.search_nodes(query=name, type="Datasheet")
        existing_match = [n for n in existing if n.get("name") == name]
        if existing_match:
            dst_id = existing_match[0]["id"]
            logger.info("reuse datasheet: %s -> %s", name, dst_id)
        else:
            created = client.create_datasheet(name)
            dst_id = created["id"]
            logger.info("created datasheet: %s -> %s", name, dst_id)

        result[name] = dst_id

        # 补字段
        existing_field_names = {f["name"] for f in client.list_fields(dst_id)}
        for field in s["fields"]:
            if field["name"] in existing_field_names:
                continue
            client.create_field(
                dst_id,
                name=field["name"],
                type=field["type"],
                property=field.get("property"),
            )
            logger.info("  + field: %s (%s)", field["name"], field["type"])

    return result
```

- [ ] **Step 4: pass**

```bash
python -m pytest simulator/tests/test_bootstrap.py -v
```

Expected: `4 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/bootstrap.py simulator/tests/test_bootstrap.py
git commit -m "feat(dianli-cockpit): bootstrap_schemas — create/reuse datasheets, ensure fields"
```

---

## Task 6: 数据生成器 `generators.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/generators.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_generators.py`

七个 generator 函数，每个返回 list[dict]。使用 `random.Random(seed)` 保证可复现。

- [ ] **Step 1: 写测试 `test_generators.py`**

```python
"""Validate generated record counts, value ranges, distributions."""
import datetime
from simulator.shared import generators as G
from simulator.shared.constants import (
    DISTRICT_COLOR, INDUSTRY_COLOR, ALERT_LEVEL_COLOR, ALERT_TYPES,
    ALERT_STATUS_COLOR, INSIGHT_TYPES, RENEWABLE_TYPE_COLOR,
)


def test_industry_metrics_count():
    """12 月 × 7 区 × 6 行业 = 504"""
    rec = G.generate_industry_metrics(seed=1)
    assert len(rec) == 504


def test_industry_metrics_fields_complete():
    rec = G.generate_industry_metrics(seed=1)
    r0 = rec[0]
    assert {"月份", "区域", "行业", "行业用电_MWh",
            "同比_%", "景气指数", "产出指数"} <= set(r0.keys())


def test_industry_metrics_districts_industries_covered():
    rec = G.generate_industry_metrics(seed=1)
    assert {r["区域"] for r in rec} == set(DISTRICT_COLOR.keys())
    assert {r["行业"] for r in rec} == set(INDUSTRY_COLOR.keys())


def test_industry_metrics_value_ranges():
    rec = G.generate_industry_metrics(seed=1)
    for r in rec:
        assert 100 <= r["行业用电_MWh"] <= 5000
        assert -30 <= r["同比_%"] <= 30
        assert 30 <= r["景气指数"] <= 100
        assert 30 <= r["产出指数"] <= 100


def test_enterprise_count_50_x_30():
    rec = G.generate_enterprises(seed=1)
    assert len(rec) == 1500  # 50 enterprises × 30 days


def test_enterprise_unique_companies():
    rec = G.generate_enterprises(seed=1)
    names = {r["企业名称"] for r in rec}
    assert len(names) == 50


def test_load_curve_count():
    """7 区 × 24 小时 = 168"""
    rec = G.generate_load_curve(seed=1)
    assert len(rec) == 168


def test_load_curve_timestamps_span_24h():
    rec = G.generate_load_curve(seed=1)
    timestamps = sorted(set(r["时间戳"] for r in rec))
    assert len(timestamps) == 24


def test_alerts_count():
    rec = G.generate_alerts(seed=1)
    assert 70 <= len(rec) <= 90  # ~80


def test_alerts_levels_distribution():
    rec = G.generate_alerts(seed=1)
    levels = [r["等级"] for r in rec]
    assert set(levels) <= set(ALERT_LEVEL_COLOR.keys())
    # 红色应该是少数（合理分布）
    assert levels.count("红色") < len(levels) * 0.3


def test_alerts_event_codes_unique_and_formatted():
    rec = G.generate_alerts(seed=1)
    codes = [r["事件编号"] for r in rec]
    assert len(set(codes)) == len(codes)
    for c in codes:
        assert c.startswith("AL-")


def test_renewable_count():
    """7 区 × 30 天 = 210"""
    rec = G.generate_renewable(seed=1)
    assert len(rec) == 210


def test_insights_count():
    rec = G.generate_insights(seed=1)
    assert 25 <= len(rec) <= 35  # ~30


def test_insights_have_long_content():
    rec = G.generate_insights(seed=1)
    for r in rec:
        assert len(r["洞察内容"]) >= 80, f"洞察内容太短: {r['洞察内容']}"


def test_config_kv_pairs():
    rec = G.generate_config()
    keys = {r["参数"] for r in rec}
    assert "红色预警阈值" in keys
    assert "橙色预警阈值" in keys
    assert "黄色预警阈值" in keys
    assert "演示模式" in keys


def test_seed_determinism():
    """同 seed 必须产同样结果。"""
    a = G.generate_enterprises(seed=42)
    b = G.generate_enterprises(seed=42)
    assert a == b
```

- [ ] **Step 2: fail**

- [ ] **Step 3: 写 `simulator/shared/generators.py`**

```python
"""Realistic record generators for the 7 dianli-cockpit tables.

Determinism: every function takes a `seed` for reproducibility. Seed=1 by
default matches the spec's expected counts.
"""
import datetime
import random
from typing import List, Dict
from simulator.shared.constants import (
    DISTRICT_COLOR, INDUSTRY_COLOR, ALERT_LEVEL_COLOR, ALERT_TYPES,
    ALERT_STATUS_COLOR, INSIGHT_TYPES, RENEWABLE_TYPE_COLOR,
)

DISTRICTS = list(DISTRICT_COLOR.keys())
INDUSTRIES = list(INDUSTRY_COLOR.keys())

# 区域基准（跑量大致比例：仲恺/惠城是工业重镇）
DISTRICT_WEIGHT = {
    "惠城区": 1.4, "惠阳区": 1.2, "大亚湾区": 1.5, "仲恺高新区": 1.6,
    "博罗县": 0.9, "惠东县": 0.7, "龙门县": 0.5,
}
# 行业基准
INDUSTRY_WEIGHT = {
    "电子信息": 1.3, "石化能源": 1.6, "装备制造": 1.2,
    "汽车制造": 1.0, "纺织食品": 0.8, "新材料": 0.9,
}


def generate_industry_metrics(seed: int = 1) -> List[Dict]:
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    records = []
    # 最近 12 个月（2025-06 ~ 2026-05）
    for m_offset in range(-11, 1):
        month_date = (today.replace(day=1) + datetime.timedelta(days=m_offset * 31)).replace(day=1)
        month_str = month_date.strftime("%Y-%m")
        for d in DISTRICTS:
            for i in INDUSTRIES:
                base = 1500 * DISTRICT_WEIGHT[d] * INDUSTRY_WEIGHT[i]
                power = round(base * rng.uniform(0.85, 1.15), 1)
                yoy = round(rng.uniform(-15, 25), 1)
                prosperity = round(rng.uniform(50, 95), 1)
                output = round(rng.uniform(50, 100), 1)
                records.append({
                    "月份": month_str,
                    "区域": d,
                    "行业": i,
                    "行业用电_MWh": power,
                    "同比_%": yoy,
                    "景气指数": prosperity,
                    "产出指数": output,
                })
    return records


def generate_enterprises(seed: int = 1) -> List[Dict]:
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    statuses = ["稳定运行", "稳定运行", "稳定运行", "稳定运行",
                "重点跟踪", "重点跟踪", "异常监测", "停产"]  # 加权偏稳定

    # 50 家企业（区/行业分配）
    companies = []
    for i in range(50):
        d = rng.choice(DISTRICTS)
        ind = rng.choice(INDUSTRIES)
        companies.append({
            "name": f"{d}{ind}示范企业{i+1:03d}",
            "district": d,
            "industry": ind,
            "base_status": rng.choice(statuses),
            "base_power": rng.uniform(80, 380),
        })

    records = []
    for c in companies:
        for day_offset in range(-29, 1):
            date = (today + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            power = round(c["base_power"] * rng.uniform(0.80, 1.20), 1)
            records.append({
                "企业名称": c["name"],
                "日期": date,
                "区域": c["district"],
                "行业": c["industry"],
                "今日用电_MWh": power,
                "同比_%": round(rng.uniform(-15, 20), 1),
                "开工指数": round(rng.uniform(60, 100), 1),
                "风险指数": round(rng.uniform(10, 90), 1),
                "状态": c["base_status"] if rng.random() > 0.05 else rng.choice(statuses),
            })
    return records


def generate_load_curve(seed: int = 1) -> List[Dict]:
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    records = []
    for h in range(24):
        ts = datetime.datetime.combine(today, datetime.time(h, 0)).strftime("%Y-%m-%d %H:%M")
        # 用电曲线日内规律：早高峰 8-10、晚高峰 19-21
        diurnal = 0.7 + 0.3 * (1 if 8 <= h <= 10 or 19 <= h <= 21
                                else (0.6 if 7 <= h <= 22 else 0.3))
        for d in DISTRICTS:
            base = 350 * DISTRICT_WEIGHT[d] * diurnal
            load = round(base * rng.uniform(0.90, 1.10), 1)
            forecast = round(load * rng.uniform(0.95, 1.05), 1)
            cumulative = round(load * (h + 1) * rng.uniform(0.95, 1.05), 1)
            records.append({
                "时间戳": ts,
                "区域": d,
                "实时负荷_MW": load,
                "预测负荷_MW": forecast,
                "累计用电_MWh": cumulative,
            })
    return records


def generate_alerts(seed: int = 1) -> List[Dict]:
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
    rng = random.Random(seed)
    today = datetime.date(2026, 5, 9)
    types = ["光伏", "储能", "充电"]
    records = []
    for d in DISTRICTS:
        for day_offset in range(-29, 1):
            date = (today + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            records.append({
                "日期": date,
                "区域": d,
                "光伏出力_MW": round(rng.uniform(20, 120), 1),
                "储能电量_MWh": round(rng.uniform(10, 80), 1),
                "充电次数": rng.randint(50, 600),
                "类型": rng.choice(types),
            })
    return records


def generate_insights(seed: int = 1) -> List[Dict]:
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
    return [
        {"参数": "红色预警阈值", "值": "80", "说明": "风险指数 ≥ 此值触发红色预警"},
        {"参数": "橙色预警阈值", "值": "60", "说明": "风险指数 ≥ 此值触发橙色预警"},
        {"参数": "黄色预警阈值", "值": "40", "说明": "风险指数 ≥ 此值触发黄色预警"},
        {"参数": "KPI_今日总用电_目标", "值": "30000", "说明": "MWh，对照线"},
        {"参数": "KPI_平均景气指数_警戒线", "值": "50", "说明": "低于此值变红"},
        {"参数": "KPI_活跃预警_警戒数", "值": "10", "说明": "超过此数 KPI 卡片闪烁"},
        {"参数": "演示模式", "值": "on", "说明": "on/off。on 时模拟器后台跑剧本"},
        {"参数": "更新频率_秒", "值": "10", "说明": "用电曲线 worker 周期"},
        {"参数": "色板_红色预警", "值": "#FF3D5F", "说明": "前端读取，不在 vika options 里"},
        {"参数": "色板_橙色预警", "值": "#FF6B35", "说明": ""},
        {"参数": "色板_主背景", "值": "#0A1929", "说明": "驾驶舱底色"},
        {"参数": "色板_主强调", "值": "#00D9FF", "说明": "霓虹青"},
    ]
```

- [ ] **Step 4: pass**

```bash
python -m pytest simulator/tests/test_generators.py -v
```

Expected: `15 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/generators.py simulator/tests/test_generators.py
git commit -m "feat(dianli-cockpit): realistic data generators for all 7 tables (~2500 records)"
```

---

## Task 7: 幂等灌入 `seeder.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/shared/seeder.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_seeder.py`

策略：用复合键查重。每张表的 `key_fields` 不同：
- industry: `(月份, 区域, 行业)`
- enterprise: `(企业名称, 日期)`
- load_curve: `(时间戳, 区域)`
- alert: `(事件编号,)`
- renewable: `(日期, 区域)`
- insight: `(时间, 区域, 类型)`  （没绝对唯一，约莫够用）
- config: `(参数,)`

- [ ] **Step 1: 写测试 `test_seeder.py`**

```python
"""seed_table: 幂等批量写。"""
from unittest.mock import MagicMock
from simulator.shared.seeder import seed_table


def test_seeds_all_when_empty():
    client = MagicMock()
    client.list_all_records.return_value = []
    client.create_records.return_value = []
    records = [
        {"a": 1, "b": "x"},
        {"a": 2, "b": "y"},
    ]
    n = seed_table(client, "dst1", records, key_fields=["a"])
    assert n == 2
    client.create_records.assert_called_once_with("dst1", records)


def test_skips_existing():
    client = MagicMock()
    # 已经有 a=1 的记录了
    client.list_all_records.return_value = [
        {"recordId": "rec1", "fields": {"a": 1, "b": "x"}}
    ]
    new_records = [
        {"a": 1, "b": "ignored"},  # 跳
        {"a": 2, "b": "y"},        # 灌
    ]
    n = seed_table(client, "dst1", new_records, key_fields=["a"])
    assert n == 1
    args, kwargs = client.create_records.call_args
    assert args[0] == "dst1"
    assert args[1] == [{"a": 2, "b": "y"}]


def test_composite_key():
    client = MagicMock()
    client.list_all_records.return_value = [
        {"recordId": "r", "fields": {"日期": "2026-05-09", "区域": "惠城区"}}
    ]
    records = [
        {"日期": "2026-05-09", "区域": "惠城区", "v": 1},
        {"日期": "2026-05-09", "区域": "惠阳区", "v": 2},
    ]
    n = seed_table(client, "dst1", records, key_fields=["日期", "区域"])
    assert n == 1


def test_dry_run():
    client = MagicMock()
    client.list_all_records.return_value = []
    n = seed_table(client, "dst1", [{"a": 1}], key_fields=["a"], dry_run=True)
    assert n == 1
    client.create_records.assert_not_called()
```

- [ ] **Step 2: fail**

- [ ] **Step 3: 写 `simulator/shared/seeder.py`**

```python
"""Idempotent batch seeding.

Strategy: pull existing records (key fields only), build a set of composite
keys, filter input records to those not already present, then write in
batches of 10 (vika REST limit) — handled by VikaClient.
"""
import logging
from typing import List, Sequence

logger = logging.getLogger(__name__)


def seed_table(client, dst_id: str, records: List[dict],
               key_fields: Sequence[str], *, dry_run: bool = False) -> int:
    """Seed `records` into `dst_id`, skipping any whose composite key already
    exists. Returns count of records actually inserted (or that would be on
    a real run, when dry_run=True)."""
    existing_keys = set()
    try:
        existing = client.list_all_records(dst_id, fields=list(key_fields))
        for r in existing:
            f = r.get("fields") or {}
            key = tuple(f.get(k) for k in key_fields)
            existing_keys.add(key)
    except Exception as e:  # noqa: BLE001
        logger.warning("could not list existing records for %s: %s; will treat as empty",
                       dst_id, e)

    to_insert = []
    for rec in records:
        key = tuple(rec.get(k) for k in key_fields)
        if key in existing_keys:
            continue
        to_insert.append(rec)

    logger.info("table %s: %d new / %d total / %d existing",
                dst_id, len(to_insert), len(records), len(existing_keys))

    if dry_run:
        return len(to_insert)

    if to_insert:
        client.create_records(dst_id, to_insert)
    return len(to_insert)
```

- [ ] **Step 4: pass**

Expected: `4 passed`.

- [ ] **Step 5: 提交**

```bash
git add simulator/shared/seeder.py simulator/tests/test_seeder.py
git commit -m "feat(dianli-cockpit): idempotent seed_table — composite-key dedup, dry-run support"
```

---

## Task 8: CLI 入口 `cli.py`

**Files:**
- Create: `examples/dianli-cockpit/simulator/cli.py`
- Create: `examples/dianli-cockpit/simulator/__main__.py`
- Create: `examples/dianli-cockpit/simulator/tests/test_cli.py`

- [ ] **Step 1: 写测试 `test_cli.py`**

```python
"""CLI 主流程：argparse + 调用各模块的串接。"""
from unittest.mock import patch, MagicMock
from simulator import cli


def test_bootstrap_runs_schemas_then_seeds_all_tables():
    with patch("simulator.cli.VikaClient") as MockClient, \
         patch("simulator.cli.bootstrap_schemas") as mock_boot, \
         patch("simulator.cli.seed_table") as mock_seed:
        mock_boot.return_value = {f"电力看经济_{k}": f"dst_{k}" for k in [
            "行业指标", "重点企业", "用电曲线", "预警事件",
            "新能源充电", "机器人洞察", "配置参数",
        ]}
        mock_seed.return_value = 100
        cli.main(["bootstrap"])

        mock_boot.assert_called_once()
        # 7 张表都该 seed
        assert mock_seed.call_count == 7


def test_dry_run_passes_flag_through():
    with patch("simulator.cli.VikaClient"), \
         patch("simulator.cli.bootstrap_schemas") as mock_boot, \
         patch("simulator.cli.seed_table") as mock_seed:
        mock_boot.return_value = {f"电力看经济_{k}": f"dst_{k}" for k in [
            "行业指标", "重点企业", "用电曲线", "预警事件",
            "新能源充电", "机器人洞察", "配置参数",
        ]}
        cli.main(["bootstrap", "--dry-run"])
        for call in mock_seed.call_args_list:
            assert call.kwargs.get("dry_run") is True
```

- [ ] **Step 2: fail**

- [ ] **Step 3: 写 `simulator/cli.py`**

```python
"""dianli-cockpit Phase A CLI.

Subcommands:
  bootstrap [--dry-run] [--reseed] [--skip-existing]   build schemas + seed data
"""
import argparse
import logging
import sys
from typing import List, Optional

from simulator.shared import generators
from simulator.shared.bootstrap import bootstrap_schemas
from simulator.shared.constants import TABLE_NAMES
from simulator.shared.schema import ALL_SCHEMAS
from simulator.shared.seeder import seed_table
from simulator.shared.vika import VikaClient


SEEDERS = [
    # (table_name, generator_func, key_fields)
    (TABLE_NAMES["industry"], generators.generate_industry_metrics, ["月份", "区域", "行业"]),
    (TABLE_NAMES["enterprise"], generators.generate_enterprises, ["企业名称", "日期"]),
    (TABLE_NAMES["load_curve"], generators.generate_load_curve, ["时间戳", "区域"]),
    (TABLE_NAMES["alert"], generators.generate_alerts, ["事件编号"]),
    (TABLE_NAMES["renewable"], generators.generate_renewable, ["日期", "区域"]),
    (TABLE_NAMES["insight"], generators.generate_insights, ["时间", "区域", "类型"]),
    (TABLE_NAMES["config"], generators.generate_config, ["参数"]),
]


def cmd_bootstrap(args, client: VikaClient):
    print("→ Phase A: 创建 / 复用 7 张数据表的 schema...")
    dst_ids = bootstrap_schemas(client, ALL_SCHEMAS)
    print(f"  ✓ {len(dst_ids)} 张表 schema 就位:")
    for name, dst in dst_ids.items():
        print(f"    {name:30} {dst}")

    print("\n→ 灌入种子数据 (幂等)...")
    total_new = 0
    for table_name, gen_func, key_fields in SEEDERS:
        gen_args = {"seed": args.seed} if "seed" in gen_func.__code__.co_varnames else {}
        records = gen_func(**gen_args)
        n = seed_table(client, dst_ids[table_name], records,
                       key_fields=key_fields, dry_run=args.dry_run)
        total_new += n
        print(f"  {table_name:30} 新增 {n:5d} / 共生成 {len(records):5d}")

    print(f"\n{'(dry-run) ' if args.dry_run else ''}总计新增 {total_new} 条记录")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="simulator", description="dianli-cockpit Phase A CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    bs = sub.add_parser("bootstrap", help="create schemas + seed data")
    bs.add_argument("--dry-run", action="store_true", help="print actions without writing")
    bs.add_argument("--reseed", action="store_true",
                    help="(reserved for future) wipe records before seed")
    bs.add_argument("--skip-existing", action="store_true",
                    help="skip records whose key already exists (default behavior)")
    bs.add_argument("--seed", type=int, default=1, help="random seed (default 1)")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    client = VikaClient()
    if args.cmd == "bootstrap":
        cmd_bootstrap(args, client)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 写 `simulator/__main__.py`**

```python
"""Allow `python -m simulator ...`."""
from simulator.cli import main
import sys

sys.exit(main())
```

- [ ] **Step 5: pass**

```bash
python -m pytest simulator/tests/test_cli.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: 提交**

```bash
git add simulator/cli.py simulator/__main__.py simulator/tests/test_cli.py
git commit -m "feat(dianli-cockpit): bootstrap CLI — schemas + seeders wired together"
```

---

## Task 9: 真实集成跑（Phase A 验收）

**Pre-requisite:** 用户已在 vika UI 清空老 `电力看经济_*` 8 张表（见前置条件章节）。

- [ ] **Step 1: 在工作目录确认配置**

```bash
cd ~/projects/ebiaobiao-skills/examples/dianli-cockpit
# 父项目 .env.local 已有 token + spaceId（之前的会话已配好）
ls -la <project>/.env.local
# 让 simulator 读父项目的 env
export $(grep -v '^#' <project>/.env.local | xargs)
echo "token=${EBIAOBIAO_API_TOKEN:0:8}... space=$EBIAOBIAO_SPACE_ID"
```

- [ ] **Step 2: 干跑（不写）**

```bash
python -m simulator bootstrap --dry-run 2>&1 | tee /tmp/dianli-dryrun.log
```

Expected: 看到 7 张表的预期 dst_id（mock 状态都是 `"dstNEW"` 之类）和 7 条 "新增 N / 共生成 M" 输出。**注意**：dry-run 也会真创建 schema（因为 schema bootstrap 不被 dry-run 控制——这是设计意图，schema 是确定性的；只有 seeder 是 dry）。如果不希望干跑动 schema，下次迭代加个 `--no-bootstrap` 选项。

- [ ] **Step 3: 真灌（一次性 ~3 分钟）**

```bash
python -m simulator bootstrap 2>&1 | tee /tmp/dianli-seed.log
```

Expected:
- 看到每张表"新增 N"递增
- 总耗时 2-5 分钟
- 中间可能出现 429（QPS 限流），CLI 内部会重试，正常

**预期会踩的坑（spec §9）：**
- 创建 SingleSelect 字段时报 `"options[0].color must be a string"`：说明 schema 漏了哪个 option 用了对象。grep schema.py 修
- 创建带 property 的字段时报 `"Invalid value for fields[X].property"`：通常是 SingleSelect 漏了 options，或 DateTime dateFormat 不在枚举集，或 Number defaultValue 是数字
- `ebiao_fusion.py create-records --data <inline-json>` 不接受字符串：见 Task 4 末尾备注，可能需要先扩展 CLI 支持

每踩一个坑：
1. 立即定位
2. 改对应 schema 或 vika.py
3. 把根因 + 解决写到 `~/projects/ebiaobiao-skills/skills/ebiaobiao-fusion-api/references/pitfalls.md` 末尾
4. 单独 commit "fix(...) + docs(pitfalls): ..."

- [ ] **Step 4: UI 验证**

打开 `<configured-host>`，进测试空间根目录：

- [ ] 看到 7 张新表 `电力看经济_*`
- [ ] 打开 `电力驾驶舱_行业指标`：
  - [ ] 504 条记录（顶部计数）
  - [ ] "区域" 列显示彩色 chip（蓝/绿/青/紫/橙/红/黄）
  - [ ] "行业" 列同样彩色
  - [ ] "行业用电_MWh" 是数字带单位
  - [ ] "月份" 列格式 `2025-06` 等
- [ ] 打开 `电力驾驶舱_预警事件`：
  - [ ] ~80 条
  - [ ] "等级" 红/橙/黄三色 chip
  - [ ] "状态" 处理中/已纳入监测/已闭环/已忽略 四色 chip
- [ ] 打开 `电力驾驶舱_机器人洞察`：
  - [ ] "置信分" 列显示 ★ 星星，1-5 颗
- [ ] 任一张表"3 条空占位记录"（vika 自动加的）正常存在，且 fields 都是空——这是预期，模拟器接管后可清理

通不过的项立即修，迭代 schema/generator，重跑直到全绿。

- [ ] **Step 5: 提交跑通后的最终调整**

如果上面任何一步发现 schema 或 generator 要修，做完修改后：

```bash
git add -p   # review 改动
git commit -m "fix(dianli-cockpit): <具体修了什么>"
```

---

## Task 10: 跑质量门 + push

- [ ] **Step 1: 跑离线质量门**

```bash
cd ~/projects/ebiaobiao-skills
ebiao-quality
```

Expected: 7 项全 PASS。如果新增的 simulator/shared/*.py 让 `python compile` 检查多扫几个文件，summary 应该是 `8 passed` 或 `9 passed`。

- [ ] **Step 2: 推所有 commits**

```bash
git push origin main
```

- [ ] **Step 3: 在 GitHub 上确认**

打开 `https://github.com/xxzxzmai-droid/ebiaobiao-skills/tree/main/examples/dianli-cockpit`：

- [ ] 看到 `simulator/shared/*.py` 5 个模块
- [ ] 看到 `simulator/tests/*.py` 5 个测试
- [ ] 看到 `simulator/cli.py` + `__main__.py`
- [ ] 看到 `requirements.txt`、`README.md`
- [ ] 看到 `plans/2026-05-09-phase-a-data.md` 这份计划文件

---

## 完成标准（DoD）

Phase A 视为完成当且仅当：

1. [ ] 所有 5 个测试模块 `pytest simulator/tests` 全 pass（≥ 40 个 assertion）
2. [ ] `python -m simulator bootstrap --dry-run` 不报错且打印预期数量
3. [ ] `python -m simulator bootstrap` 真灌成功，UI 验收所有勾选项绿
4. [ ] `ebiao-quality` 全 PASS
5. [ ] commits 按 task 拆分清晰（每个 task 末尾一次 commit），git log 可读
6. [ ] 至少 1 条 `pitfalls.md` 新增（如果有踩坑——大概率会有）
7. [ ] push 到 main 分支
