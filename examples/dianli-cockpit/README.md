# 电力看经济驾驶舱 demo

旗舰 demo 展示 `ebiaobiao-skills` 对私有部署 e报表（vika）的全套能力。设计说明见 [SPEC.md](SPEC.md)，分阶段实施计划见 [plans/](plans/)。

新表用 `电力驾驶舱_*` 前缀，不动老的 `电力看经济_*` 8 张表。

## Phase A · 数据骨架

建 7 张表 + 灌 ~2500 条仿真种子。前提：父项目（这个仓库的同事或 ebiaobiao-skills 用户）已经按根 README 配好 `.env.local`（含 `EBIAOBIAO_API_TOKEN` + `EBIAOBIAO_SPACE_ID`）。

### 跑起来

```bash
cd ~/projects/ebiaobiao-skills/examples/dianli-cockpit

# 跑测试（不连真实 vika）
python -m pytest simulator/tests -v

# 干跑：打印将要发起的 API 调用，不写
python -m simulator bootstrap --dry-run

# 真灌（首次 ~3 分钟）
python -m simulator bootstrap

# 增量补：只补缺失记录
python -m simulator bootstrap --skip-existing
```

跑完进 vika UI 验证：左侧目录树应该有 7 张 `电力驾驶舱_*` 新表，每张表打开能看到正确的字段类型与彩虹标签。

## 项目结构（Phase A 末态）

```
examples/dianli-cockpit/
├── SPEC.md                    设计说明
├── README.md                  本文件
├── requirements.txt           pytest（dev only）
├── plans/                     分阶段实施计划
└── simulator/
    ├── __init__.py
    ├── __main__.py            python -m simulator 入口
    ├── cli.py                 CLI 子命令分发
    ├── shared/
    │   ├── constants.py       districts/industries/colors/enums
    │   ├── schema.py          7 张表的 schema 定义
    │   ├── vika.py            VikaClient（薄 ebiao_fusion CLI 封装）
    │   ├── bootstrap.py       create-or-reuse datasheets + ensure fields
    │   ├── generators.py      realistic data generators
    │   └── seeder.py          idempotent batch seeding
    └── tests/
        ├── conftest.py
        └── test_*.py          ~40 assertions
```

## 后续阶段（不在 Phase A 范围）

- Phase B：cockpit-widget 静态版（多端自适应布局 + ECharts + SVG 地图，连真表读取展示）
- Phase C：simulator 多线程 worker + 6 段剧本 + widget 写回预警状态
- Phase D：webhook receiver + Script 小部件 + vika 出站 HTTP 自动化

每阶段结束跑 `ebiao-quality` + commit + push，把踩到的坑写到 `skills/ebiaobiao-*/references/pitfalls.md`。
