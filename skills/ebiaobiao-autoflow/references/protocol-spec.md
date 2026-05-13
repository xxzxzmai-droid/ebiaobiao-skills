# AutoFlow × e报表 Protocol Specification

This is a snapshot from `docs/specs/2026-05-12-ebiaobiao-bridge-design.md` sections 2.1. The spec document is the source-of-truth; this is duplicated here so the skill is self-contained.

## 2.1 六张表的完整 schema

### `af_config` — 配置 + 心跳

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| record_id | (vika 自动) | - | 主键 |
| instance_id | text | 内网 | 一个 AutoFlow 实例的唯一 ID(UUID,首次启动生成) |
| host_name | text | 内网 | 内网机器名,便于多客户端区分 |
| version | text | 内网 | AutoFlow 版本号 |
| schema_version | number | 内网 | 协议版本 |
| last_seen_at | datetime | 内网 | 内网每次心跳更新(每 30s 一次) |
| status | single_select | 内网 | active / idle / error |
| enabled_features | text | 内网 | JSON 字符串: `["recording", "nlp_workflow"]` |

**用途**: 外网 AI 看到这张表就知道"内网在不在线 / 能做什么"。

### `af_commands` — AI → AutoFlow 指令队列

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| cmd_id | text | 外网 | UUID,幂等性关键 |
| target_instance | text | 外网 | 给哪个内网实例(对应 af_config.instance_id) |
| cmd | single_select | 外网 | start_recording / stop_recording / inspect_page / save_workflow / run_workflow / cancel / list_workflows |
| params | text(JSON) | 外网 | 命令参数 |
| priority | number | 外网 | 高优先级先处理 |
| status | single_select | 双向 | pending(AI 写) / picked(内网拿到) / done(内网做完) / error |
| picked_at | datetime | 内网 | 拿到的时间 |
| created_at | datetime | 外网 | AI 创建时间 |
| processed_at | datetime | 内网 | 处理完时间 |
| result_ref | text | 内网 | 关联到 af_command_results 的 record_id |

### `af_command_results` — 命令执行结果

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| result_id | text | 内网 | UUID |
| command_id | text | 内网 | 关联 af_commands.cmd_id |
| ok | checkbox | 内网 | 成功否 |
| error | text | 内网 | 失败时的错误 + 智能诊断(沿用 FailureDetail 那一套) |
| payload | text(JSON) | 内网 | 成功时的结构化结果 |
| screenshot_attachment | attachment | 内网 | 失败时的页面截图(可选) |
| duration_ms | number | 内网 | 耗时 |
| at | datetime | 内网 | 完成时间 |

### `af_workflows` — AI 提交的工作流 / 内网最终版

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| wf_id | text | 双向 | AI 起草时分配,内网保存后 = 内网 workflow id |
| name | text | 双向 | 工作流名字 |
| version | text | 双向 | |
| json | text(超长) | 双向 | Workflow JSON |
| source | single_select | 双向 | ai_draft / human_edited / ai_after_review |
| status | single_select | 双向 | draft / pending_review / approved / rejected |
| risk_level | single_select | 内网 | 风险评估后回写 |
| reject_reason | text | 双向 | 内网拒绝时填,或 AI 撤回 |
| updated_at | datetime | 双向 | |

### `af_page_info` — 内网把当前页面"扔"上去给 AI 看

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| info_id | text | 内网 | UUID |
| related_command_id | text | 内网 | 关联触发它的命令(通常是 inspect_page) |
| url | text | 内网 | 当前 URL |
| title | text | 内网 | 页面标题 |
| html_snippet | text(超长) | 内网 | 关键区域的 HTML(尽量小,默认 body 的前 32KB) |
| elements_json | text(超长) | 内网 | AutoFlow 已识别的可交互元素 + 候选 selector |
| screenshot_attachment | attachment | 内网 | 整页截图 |
| at | datetime | 内网 | |

### `af_audit_mirror` — 审计日志精简镜像

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| audit_id | text | 内网 | |
| workflow_id | text | 内网 | |
| run_id | text | 内网 | |
| method | text | 内网 | |
| url | text | 内网 | 域名 + 路径,不带 query(隐私) |
| status | number | 内网 | |
| duration_ms | number | 内网 | |
| dry_run | checkbox | 内网 | |
| at | datetime | 内网 | |

> ⚠️ **不镜像** 请求体、响应体 — 那些可能含敏感数据。外网 AI 只看到"何时 调谁 是否成功",看不到内容。

#### `af_chat` — 用户 ↔ AI 对话通道(v1.0+ 新增)

| 字段 | 类型 | 谁写 | 说明 |
|------|------|------|------|
| chat_id | SingleText | 双向 | 每条消息 UUID |
| conversation_id | SingleText | 双向 | 多轮对话分组 |
| role | SingleSelect | 双向 | `user` / `ai` / `system` |
| text | Text | 双向 | 消息内容 (多行长文) |
| attachments | Attachment | 双向 | 截图 / 文件 (单文件 ≤20MB) |
| related_command_id | SingleText | 双向 | 关联到 af_commands.cmd_id (如果是命令的反馈) |
| suggested_wf_id | SingleText | AI 写 | AI 推荐工作流 id - 用户点链接直跳详情 |
| status | SingleSelect | 双向 | `pending` (user 刚发 / AI 没回) / `answered` / `in_progress` / `failed` |
| at | DateTime | 双向 | ISO 时间戳 |

**自动反馈环**: 当 AI 建工作流 (`source='ai_draft'`) 跑挂时, AutoFlow 自动写一条 `role='system'` 到对话, 内容包含失败步骤 + 错误。下次轮询 AI 看到就主动给修复版。

**安全合约**:
- AI 写到 `af_chat` 的 `status` 只用 `answered`/`in_progress`/`failed` — `pending` 永远是 user 的
- AI **必须 PATCH** user 消息的 status 从 `pending` 改 `answered` 后才算"处理完",否则会一直被重新匹配
