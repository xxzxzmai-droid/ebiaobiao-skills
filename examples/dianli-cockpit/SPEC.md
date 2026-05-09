# 电力看经济驾驶舱 demo · 设计 spec

**日期**: 2026-05-09
**作者**: xxzxzmai-droid（驱动） + Claude Code（执行）
**目标仓库**: [`ebiaobiao-skills`](https://github.com/xxzxzmai-droid/ebiaobiao-skills) `examples/dianli-cockpit/`
**目标空间站**: 由 `.env.local` 中 `EBIAOBIAO_SPACE_ID` 指定（开发期=测试空间）
**目标域名**: `<configured-host>`

## 1. 目标与范围

### 1.1 目标

为 `ebiaobiao-skills` 提供一个**旗舰级 demo**，全面展示该 skill 包对目标环境 报表（vika）的 Fusion API、Widget 自建小程序、Script 小部件、Webhook 自动化、多空间 profile、全局发布等能力。

成果同时服务两个用途：

1. **业务上**：可演示给领导/同事看的"惠州市电力看经济实时驾驶舱"，看上去是个真产品
2. **工程上**：把 skill 真用一遍，把所有踩到的坑沉淀回 `skills/ebiaobiao-*/references/pitfalls.md`、`field-types.md`、`widget-development.md`，每改一处 commit 一次

### 1.2 关键决策（已经过 brainstorming 确认）

| 维度 | 决策 |
|---|---|
| demo 完整度 | C 重量版（schema + seed + widget + simulator + Script + webhook + 全局发布） |
| 主视觉风格 | A 大屏驾驶舱风（深色 + 霓虹 + 数字跳变 + 发光折线） |
| 数据时间粒度 | D 混合（行业月度 / 重点企业日度 / 用电曲线时度 / 预警秒级流） |
| 地理 + 行业 | C 全惠州 7 区 × 6 行业 |
| 屏幕布局 | 4 行经典：顶栏 / KPI 行 / 地图+曲线+预警三栏 / donut+Top10 双栏 + 底栏 ticker |
| Schema 重建 | 新建 7 张『电力驾驶舱_*』表，老『电力看经济_*』8 张保留不动 |
| 交互深度 | C 深度交互（含 widget 写回预警状态，欢迎 Race Condition） |
| 数据剧情感 | B 预编排剧情 + 背景扰动（6 段 90 秒剧本） |
| 工程方案 | 中量旗舰：放进 `examples/dianli-cockpit/`，多线程模拟器，ECharts 图表，每个坑反哺 skill |

### 1.3 范围之外

- 真实 GDP/工业用电数据建模（用合理仿真，不爬真数据）
- Playwright/Cypress 自动化前端测试（手工目视）
- Docker Compose 容器化（本机长跑即可）
- TypeScript monorepo 共享类型（widget 用 TS，simulator 用 Python，自然语言契约约定字段名即可）
- 真发企微/钉钉（webhook receiver 只 log，不做真发）

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│  报表 vika 目标环境  <configured-host>                │
│                                                                  │
│  7 张数据表（详见 §3 schema）                                    │
└────┬─────────────────────────────────────────────────────┬───────┘
     │ Fusion API                                          │ widget-sdk
     │                                                     │
     ▼                                                     ▼
┌────────────────────────┐                       ┌────────────────────────┐
│ Simulator (Python)     │                       │ Cockpit Widget (React) │
│ ─────────────          │                       │ ─────────────          │
│ 4 worker threads:      │                       │ 大屏 / 紧凑 / 手机      │
│  - monthly  60s        │ 写              读   │ 自适应布局              │
│  - daily    30s        ├──→ vika ←───────────┤ ECharts + SVG 地图     │
│  - hourly   10s        │                       │                        │
│  - alerts   20-60s     │                       │ 写回：仅预警状态字段    │
│ + playbook engine      │                       │                        │
│   6 剧本 yaml          │                       │ 详见 §4                │
└────┬───────────────────┘                       └────────────────────────┘
     │                                                       ▲
     │ vika 自动化"发送 HTTP 请求"动作（红色预警时触发）     │
     ▼                                                       │
┌────────────────────────┐                                    │
│ Webhook Receiver       │ Flask :8765 /alert                 │
│ (Flask 80 行)          │ 接收推送 → 打日志 → 模拟发企微     │
└────────────────────────┘                                    │
                                                              │
ScriptWidget 兜底（贴 vika Script 小部件，手动跑） ──────────┘
   batch-handle-alerts.js: 7 天前已纳入监测的预警批量闭环
```

### 2.1 关键原则

1. **Widget 直接读 vika**：通过 widget-sdk hooks 响应式订阅，无中间层
2. **Widget 写回限制**：仅预警事件的"状态"字段，最低风险范围
3. **Simulator 多线程并发**：4 worker 独立 cadence 互不阻塞，Race Condition 故意保留
4. **Webhook 单向**：vika → Flask，禁止 Flask 反过来改 vika（避免循环）
5. **Script Widget 是兜底工具**：演示给"运维"用，不参与实时循环

## 3. 数据 Schema（7 张新表）

> 用 `电力驾驶舱_*` 前缀，跟老 `电力看经济_*` 8 张表共存不冲突。所有字段类型按 报表目标环境实测格式（color 字符串 / icon slug / dateFormat 枚举 / Number defaultValue 字符串 / Formula 不带 valueType 等）。

### 3.1 区域配色（7 区固定映射）

| 区 | color |
|---|---|
| 惠城区 | blue |
| 惠阳区 | green |
| 大亚湾区 | cyan |
| 仲恺高新区 | purple |
| 博罗县 | orange |
| 惠东县 | red |
| 龙门县 | yellow |

### 3.2 行业配色（6 行业固定映射）

| 行业 | color |
|---|---|
| 电子信息 | cyan |
| 石化能源 | red |
| 装备制造 | blue |
| 汽车制造 | orange |
| 纺织食品 | green |
| 新材料 | purple |

### 3.3 表 ① `电力驾驶舱_行业指标` （504 条 = 12 月 × 7 区 × 6 行业）

| 字段 | 类型 | property |
|---|---|---|
| 标题 | SingleText（auto-primary） | 自动 `2026-MM·区·行业` |
| 月份 | DateTime | `dateFormat=YYYY-MM, includeTime=false` |
| 区域 | SingleSelect | 见 3.1 |
| 行业 | SingleSelect | 见 3.2 |
| 行业用电_MWh | Number | `precision=1, symbol=MWh` |
| 同比_% | Number | `precision=1, symbol=%` |
| 景气指数 | Number | `precision=1`（0-100） |
| 产出指数 | Number | `precision=1`（0-100） |

### 3.4 表 ② `电力驾驶舱_重点企业` （~1500 条 = 50 企业 × 30 天）

| 字段 | 类型 |
|---|---|
| 企业名称 | SingleText（primary） |
| 日期 | DateTime（YYYY-MM-DD） |
| 区域 / 行业 | SingleSelect（同 3.1/3.2） |
| 今日用电_MWh | Number `precision=1` |
| 同比_% | Number `precision=1, symbol=%` |
| 开工指数 | Number `precision=1` |
| 风险指数 | Number `precision=1` |
| 状态 | SingleSelect: 稳定运行=green / 重点跟踪=blue / 异常监测=orange / 停产=red |

### 3.5 表 ③ `电力驾驶舱_用电曲线` （168 条滑窗 = 7 区 × 24 小时）

| 字段 | 类型 |
|---|---|
| 标题 | SingleText `2026-MM-DD HH:00 区` |
| 时间戳 | DateTime（`YYYY-MM-DD includeTime=true timeFormat=HH:mm`） |
| 区域 | SingleSelect |
| 实时负荷_MW | Number `precision=1` |
| 预测负荷_MW | Number `precision=1`（next-hour 预测，画虚线） |
| 累计用电_MWh | Number `precision=1` |

模拟器每 10s 更新"当前小时"该区记录的负荷字段；每整点 rotate 滑窗（drop -23h, append 新小时）。

### 3.6 表 ④ `电力驾驶舱_预警事件` （~80 初始 + 流式增长）

| 字段 | 类型 |
|---|---|
| 事件编号 | SingleText（primary, AL-XXXX） |
| 时间 | DateTime（含时分） |
| 区域 | SingleSelect |
| 等级 | SingleSelect: 红色=red / 橙色=orange / 黄色=yellow |
| 类型 | SingleSelect: 负荷波动 / 行业景气 / 设备风险 / 用电异常 / 新能源波动 |
| 标题 | Text |
| 说明 | Text |
| 状态 | SingleSelect: 处理中=red / 已纳入监测=orange / 已闭环=green / 已忽略=gray |

**Widget 唯一允许写回的字段是 `状态`。**

### 3.7 表 ⑤ `电力驾驶舱_新能源充电` （210 条 = 7 区 × 30 天）

| 字段 | 类型 |
|---|---|
| 标题 | SingleText |
| 日期 | DateTime |
| 区域 | SingleSelect |
| 光伏出力_MW / 储能电量_MWh / 充电次数 | Number |
| 类型 | SingleSelect: 光伏=yellow / 储能=blue / 充电=green |

### 3.8 表 ⑥ `电力驾驶舱_机器人洞察` （~30 初始 + 剧情触发增长）

| 字段 | 类型 |
|---|---|
| 标题 | SingleText（primary） |
| 时间 | DateTime |
| 区域 | SingleSelect |
| 类型 | SingleSelect: 产能波动 / 节能建议 / 异常解释 / 政策机会 / 新园区监测 |
| 洞察内容 | Text（≥100 字描述） |
| 置信分 | Rating（icon=star, max=5） |

### 3.9 表 ⑦ `电力驾驶舱_配置参数` （~15 条 KV）

| 字段 | 类型 |
|---|---|
| 参数 | SingleText |
| 值 | Text |
| 说明 | Text |

预填 KV：

```
红色预警阈值 = 80
橙色预警阈值 = 60
黄色预警阈值 = 40
KPI_今日总用电_目标 = 30000
KPI_平均景气指数_警戒线 = 50
演示模式 = on
更新频率_秒 = 10
```

Widget 启动从这表读，不重启即可调阈值。

### 3.10 灌入策略

总数据量 ≈ **2500 条**。按 10/批 + QPS 5 写入 → ~125 秒。模拟器启动前先跑 `seed_data.py`，幂等（用复合键查重不重复写）。

## 4. Cockpit Widget（详细）

### 4.1 技术栈

| 组件 | 选型 |
|---|---|
| 框架 | React 16.14 |
| Widget SDK | `@apitable/widget-sdk` |
| UI 组件 | `@apitable/components` 部分复用 |
| 图表 | **ECharts 5**（dark theme + cyan/orange 调色） |
| 动画 | Framer Motion（KPI counter / 红色脉动） |
| 地图 | SVG 7 区惠州轮廓。优先：找开源 [GeoJSON](https://datav.aliyun.com/portal/school/atlas/area_selector) 转 SVG path；fallback：手画近似 mosaic（7 个圆角矩形按地理大致排布即可，大屏风格不要求精确） |

### 4.2 主题（固定深色，不跟随 vika）

```ts
export const theme = {
  bg: '#0A1929',              // 主底
  bgPanel: '#0F1F35',          // 面板
  border: 'rgba(0,217,255,0.2)',
  primary: '#00D9FF',          // 主强调（青蓝）
  warning: '#FF6B35',          // 警示橙
  success: '#00FF94',          // 正向绿
  danger: '#FF3D5F',           // 红色预警
  textPrimary: '#FFFFFF',
  textSecondary: '#8AA1B6',
  glow: (color: string) => `drop-shadow(0 0 8px ${color})`,
};
```

### 4.3 响应式断点

| 宽度 | 模式 | 布局 |
|---|---|---|
| ≥ 1600 | 大屏 | 4 行经典布局 |
| 768–1600 | 紧凑桌面 | KPI 5→3 / 三栏改两栏 / 地图缩 |
| < 768 | 手机 / 企微 | 单列纵向，KPI 改 2×3 网格 |

### 4.4 文件结构

```
cockpit-widget/
├── widget.config.json
├── package.json
├── tsconfig.json
├── package_icon.png / cover.png / author_icon.png
└── src/
    ├── index.tsx                   initializeWidget(App, ...)
    ├── App.tsx                     主壳，按响应式切布局
    ├── theme.ts                    上面的常量
    ├── hooks/
    │   ├── useResponsive.ts        从 skill 模板复用
    │   ├── useDistrictFilter.ts    选中区/行业 → 联动所有面板
    │   ├── useNarrativeData.ts     包装 useRecords，归一化 7 张表
    │   └── useConfigKV.ts          读 ⑦ 配置表
    ├── components/
    │   ├── HeaderBar.tsx           标题 + 时钟 + 整点 flash
    │   ├── KpiRow.tsx              5 KPI 容器
    │   ├── KpiCard.tsx             counter 动画卡片
    │   ├── HuizhouMap.tsx          手画 SVG 7 区，亮度=用电量
    │   ├── LoadCurve.tsx           ECharts line（24h 发光渐变）
    │   ├── AlertStream.tsx         预警流，红色脉动
    │   ├── AlertStatusEditor.tsx   抽屉式状态切换（写回）
    │   ├── IndustryDonut.tsx       ECharts donut
    │   ├── EnterpriseTop10.tsx     Top10 表格
    │   ├── InsightTicker.tsx       底部跑马灯
    │   └── primitives/
    │       ├── GlowText.tsx
    │       ├── Pill.tsx            (skill 模板复用)
    │       └── PulseIcon.tsx
    ├── utils/
    │   ├── colors.ts               (复用)
    │   ├── dates.ts                (复用)
    │   └── narrative.ts            判断剧情活跃 → 触发屏幕特效
    └── locales/
        ├── zh-CN.json
        ├── en-US.json
        └── index.ts
```

### 4.5 关键交互

- 点地图区 / donut 行业 → `useDistrictFilter` 切状态 → 所有面板 useMemo 重算
- 点预警条目 → `AlertStatusEditor` 抽屉弹出
- "重置过滤"按钮始终在右上角
- 时间范围切换：今日 / 7 天 / 30 天

### 4.6 写回流程（仅预警状态）

```
点预警 → AlertStatusEditor 弹出 →
    optimistic: dispatch OPTIMISTIC_UPDATE (本地立即变)
    ↓
    datasheet.updateRecordsAsync([{ recordId, fields: { 状态: '已纳入监测' } }])
    ↓
    成功 → toast "已更新"
    失败 → dispatch ROLLBACK + 错误 toast + "重试"按钮
```

预期会踩的坑（要的）：

1. `updateRecordsAsync` 签名跟文档可能不一致 → 探索 → 写到 `skills/ebiaobiao-widget/references/widget-development.md`
2. 同一记录同时被 simulator 改其他字段 → vika 偶发"记录已被修改" → 加重试 → `pitfalls.md`
3. widget 权限不够：`checkPermission('updateRecord')` 失败 → 禁用编辑 UI 加提示
4. 网络中断 / SSL → 错误恢复 UI

### 4.7 动效预算（避免炫晕）

- KPI counter：500ms 跳变
- 折线新点：300ms 滑入
- 红色预警进场：脉动最多 3 轮停下
- 地图区域亮度过渡：1s

## 5. Simulator

### 5.1 文件结构

```
simulator/
├── main.py                            python -m simulator.main
├── workers/
│   ├── __init__.py
│   ├── monthly_worker.py              60s, 行业指标加 ±0.3% 微扰
│   ├── daily_worker.py                30s, 重点企业用电 ±2%, 风险指数随机游走
│   ├── hourly_worker.py               10s, 用电曲线"当前小时"+小噪, 整点 rotate
│   └── alert_stream_worker.py         20-60s 随机, 新建黄/橙预警, 概率升级红色
├── playbooks/
│   ├── _engine.py                     YAML 解析 + 调度 + 分发动作
│   ├── 01_huiyang_drop.yml            惠阳电子信息骤降
│   ├── 02_zhongkai_surge.yml          仲恺夜间用电飙升
│   ├── 03_dayawan_chemical.yml        大亚湾石化景气向上
│   ├── 04_boluo_risk.yml              博罗某企业风险破 80
│   ├── 05_longmen_charge.yml          龙门充电翻倍
│   └── 06_nightload_storm.yml         全市夜间多区联动
├── shared/
│   ├── __init__.py
│   ├── vika_client.py                 薄封装 fusion-api CLI 或直 HTTPS
│   ├── seed_data.py                   2500 条幂等种子
│   ├── locks.py                       文件锁工具
│   └── models.py                      数据类（区域、行业、记录 ID 缓存）
├── tests/
│   ├── test_workers.py                每 worker mock vika 单测
│   └── test_playbook_engine.py        yaml 加载 + 触发顺序
└── README.md
```

### 5.2 调度模型

`main.py`：

```python
def main():
    stop = threading.Event()
    workers = [
        MonthlyWorker(stop, cadence=60),
        DailyWorker(stop, cadence=30),
        HourlyWorker(stop, cadence=10),
        AlertStreamWorker(stop, cadence_min=20, cadence_max=60),
    ]
    playbook = PlaybookScheduler(stop, workers, interval=90)

    for w in workers + [playbook]:
        w.start()

    try:
        stop.wait()  # blocked until Ctrl-C
    except KeyboardInterrupt:
        stop.set()
        for w in workers + [playbook]:
            w.join(timeout=5)
```

### 5.3 Worker 模板

```python
class BaseWorker(threading.Thread):
    def __init__(self, stop, cadence):
        super().__init__(daemon=True)
        self.stop = stop
        self.cadence = cadence

    def run(self):
        while not self.stop.is_set():
            try:
                self.tick()
            except Exception as e:
                logging.exception(f"{self.__class__.__name__} tick failed")
            self.stop.wait(self.cadence)

    def tick(self): raise NotImplementedError
```

### 5.4 Playbook 例（YAML）

```yaml
# 01_huiyang_drop.yml
id: P01
name: 惠阳区电子信息行业用电骤降
duration_seconds: 90
steps:
  - at: 0
    action: modify_industry_metric
    target: { 区域: 惠阳区, 行业: 电子信息 }
    delta: { 行业用电_MWh: -35%, 同比_%: -12 }

  - at: 5
    action: create_alert
    payload:
      等级: 红色
      类型: 用电异常
      区域: 惠阳区
      标题: 惠阳区电子信息行业用电骤降 35%
      说明: "仿真机器人检测到惠阳区电子信息行业今日用电较昨日同期骤降 35%，疑与某园区计划检修有关，建议立即核实生产状态。"

  - at: 10
    action: create_insight
    payload:
      区域: 惠阳区
      类型: 异常解释
      置信分: 4
      洞察内容: "结合气象与历史规律，本次惠阳区电子信息行业用电骤降特征更接近 [计划检修] 而非 [意外停产]，建议先行确认生产计划再决策。"

  - at: 60
    action: restore  # 恢复扰动
```

### 5.5 Race Condition 保留策略

worker 之间不加锁、不做读改写事务。掉到的具体表现写到 `skills/ebiaobiao-fusion-api/references/pitfalls.md`：

- 同一记录两个 worker 同时 update：vika 行为？（推测：last-write-wins per-field）
- 大批量并发写：QPS 如何？429 怎么回？
- 网络抖动重试：有没有重复写

### 5.6 幂等启动

```bash
python -m simulator.main                      # 只跑 worker（不重灌种子）
python -m simulator.main --reseed             # 先清空再灌（小心）
python -m simulator.main --reseed --skip-existing  # 增量补全
```

种子函数 `seed_industry_metrics()` 等都先 `filterByFormula` 查存在再写。

## 6. Webhook Receiver

### 6.1 代码（Flask 80 行）

```
webhook-receiver/
├── app.py                             Flask
├── requirements.txt                   flask, requests
├── alerts.log                         运行时生成
└── README.md                          配置 vika 自动化的步骤
```

`app.py`：

```python
from flask import Flask, request
import logging, time, json
app = Flask(__name__)
logging.basicConfig(filename='alerts.log', level=logging.INFO,
                    format='%(asctime)s %(message)s')

@app.post('/alert')
def alert():
    payload = request.get_json(silent=True) or request.form.to_dict()
    logging.info(json.dumps(payload, ensure_ascii=False))
    print(f"📢 [{time.strftime('%H:%M:%S')}] 模拟企微推送: {payload.get('标题', payload)}")
    return {'ok': True}, 200

@app.get('/health')
def health():
    return {'ok': True, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765)
```

### 6.2 vika 自动化配置（UI 一次性）

README 写明步骤：
1. 进 `电力驾驶舱_预警事件` 表
2. 顶部 "+" → 自动化
3. 触发器：记录满足条件 → `等级 = 红色`
4. 动作：发送网络请求 → `POST http://<本机 LAN IP>:8765/alert`
5. body 选 raw json，引用字段：`{"事件编号": "{事件编号}", "标题": "{标题}", "区域": "{区域}", "等级": "{等级}"}`
6. 启用

## 7. Script 小部件

### 7.1 文件

```
script-widgets/
├── batch-handle-alerts.js            主示例
├── recompute-risk-index.js           次示例：批量重算风险指数
└── README.md                          贴入 vika 的步骤
```

### 7.2 `batch-handle-alerts.js` 关键逻辑

把 `电力驾驶舱_预警事件` 中所有 `状态=已纳入监测` 且 `时间 < now-7d` 的批量改 `已闭环`。带二次确认（`input.buttonsAsync`）。代码 ~50 行，参考 skill 的 `script generate bulk-update` 模板。

## 8. 工程化

### 8.1 目录最终位置

`~/projects/ebiaobiao-skills/examples/dianli-cockpit/` 全套放进去。

### 8.2 构建顺序（spec 后的 plan 会展开）

1. ~~UI 清空老 8 张~~（取消，用 `电力驾驶舱_*` 新前缀避开冲突）
2. Fusion CLI 跑 schema 创建 + 种子灌入（~3 分钟）
3. cockpit-widget 脚手架 + npm install + 写代码 + 本地 dev
4. simulator 写 + smoke run
5. webhook-receiver 写 + 在 vika 配自动化（UI 协助）
6. Script 小部件写 + 贴入测试
7. 各组件本地联调
8. 踩到的坑写到 `skills/ebiaobiao-*/references/pitfalls.md`
9. quality gate 全绿
10. commit + push 到 ebiaobiao-skills `main`

### 8.3 测试

- 模拟器：每 worker 独立 unit test（mock vika client）
- Widget：手工目视
- 集成：跑半小时观察屏，记录所有意外行为

### 8.4 质量门

- 每次提交前 `ebiao-quality`（已配的别名）
- 新增检查：
  - `examples/dianli-cockpit/cockpit-widget/widget.config.json` 不含真 spaceId
  - simulator 不含 hardcoded token
  - webhook-receiver 不含 hardcoded token

### 8.5 README

`examples/dianli-cockpit/README.md` 写清"30 秒跑起来"：

```bash
# 1. 项目目录 = examples/dianli-cockpit
cd examples/dianli-cockpit
cp ../../path-to-env-template .env.local
# 填 token + spaceId

# 3. 灌种子（一次性 ~3 分钟）
python -m simulator.main --reseed

# 4. 启 simulator + webhook
python -m simulator.main &
python webhook-receiver/app.py &

# 5. cockpit widget
cd cockpit-widget
npm install
npm start    # https://localhost:9000/widget_bundle.js

# 6. 在 报表 UI 任意数据表 → 小部件 → 开发模式 → 输入上面 URL
# 7. 在"电力驾驶舱_预警事件"表配自动化触发 webhook（README 内有图示步骤）
```

## 8.6 推荐 MVP 顺序（实施计划展开时参考）

为避免摊子太大失焦，建议分 4 期：

**Phase A · 数据骨架**（~1 天）：清表 + schema 7 张 + 种子灌入。能在 vika UI 看到数据。
**Phase B · 静态 widget**（~2 天）：cockpit-widget 跑起来，连真表，所有面板**静态**渲染。无动态、无写回。
**Phase C · 动态 + 写回**（~2 天）：simulator 4 worker + 6 剧本 + widget 写回流程。**核心 demo 在这里成形**。
**Phase D · 自动化扩展**（~1 天）：webhook receiver + Script 小部件 + 在 vika 配自动化。

每期结束都跑 `ebiao-quality` + commit + push。每期都把踩到的坑写到对应 skill 的 `references/pitfalls.md`。

## 9. 风险与开放问题

| 风险 | 影响 | 缓解 |
|---|---|---|
| ECharts 在 widget iframe 内渲染问题 | 图表可能不显示 | 先做 minimal demo 验证；fallback 到手写 SVG |
| vika 自动化 "发送 HTTP 请求" 在目标环境可能不开放 | webhook 演示走不通 | fallback：simulator 直接调 webhook receiver |
| widget-sdk 1.10.x 在 React 16.14 上某些 API 行为不一致 | 写回流程出问题 | 故意保留，写到 pitfalls.md |
| 模拟器多线程并发写 vika 触发 429 | 部分写丢失 | 加退避；测出真实 QPS 上限并写文档 |
| 1500 条种子灌入慢 | 启动时间长 | 进度条 UI；并行 worker 灌种 |

## 10. 后续可扩展（不在本次范围内）

- 真实数据接入（统计局 / 电网 API）
- 多空间 profile demo（dev / staging / prod 切换）
- widget 全局发布（`--global`）+ 在其他空间安装试用
- 历史回放（拖时间轴 scrubber）
- PDF 导出报告

---

## 附 · 已知 报表目标环境 schema 实测要点（直接抄进实施）

- 创建 datasheet 的 fields 数组里**复杂字段必须发完整 property**（SingleSelect 必须有 options，否则报"Invalid value for fields[X].property"）。**推荐流程**：先建空表只带 name → field add 一个个补复杂字段
- SingleSelect/MultiSelect 的 `options[].color` 用**字符串** `"red"` 而非 `{name:"red"}`
- Rating / Checkbox 的 `icon` 用 GitHub 风格 emoji slug（`star`、`white_check_mark`）
- Number 的 `defaultValue` 是**字符串** `"0"`
- DateTime 的 `dateFormat` 必须是枚举集之一：`YYYY/MM/DD, YYYY-MM-DD, DD/MM/YYYY, YYYY-MM, MM-DD, YYYY, MM, DD, 0..7`，**不含**时间部分
- Formula 不能传 `valueType`，只发 `expression`
- 创建 datasheet 后会自动生成 标题/选项/附件 三个字段 + **3 条空占位记录**，需要的话清掉
- 单批写记录 ≤ **10 条**；列表 pageSize ≤ 1000；QPS ≈ 5–20

完整列表见 `skills/ebiaobiao-fusion-api/references/`。
