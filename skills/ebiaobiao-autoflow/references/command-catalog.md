# AutoFlow × e报表 Command Catalog

This is a snapshot from `docs/specs/2026-05-12-ebiaobiao-bridge-design.md` section 2.2. The spec document is the source-of-truth; this is duplicated here so the skill is self-contained.

## 2.2 命令目录(cmd 枚举)

| cmd | params 例 | 内网行为 | 回写到 |
|-----|-----------|----------|--------|
| `inspect_page` | `{url, region?}` | 打开浏览器到 url,抓 HTML+screenshot,生成 elements_json | af_page_info + af_command_results |
| `start_recording` | `{url}` | 开始录制(同 🪄 教小流) | af_command_results(状态) |
| `stop_recording` | `{}` | 停止录制 | af_command_results + af_workflows(草稿) |
| `save_workflow` | `{workflow}` | 走 risk-analyzer + 敏感数据扫描器(自动脱敏),保存 | af_command_results,带 credWarnings 字段 |
| `run_workflow` | `{wf_id, params?}` | 跑工作流, **桥路径强制 dry-run**(无真实写入) | af_command_results + af_audit_mirror |
| `list_workflows` | `{}` | 列本地所有工作流元数据(id/name/risk/stepCount/whitelist) | af_command_results.payload |
| `get_workflow` | `{wf_id}` | 拉完整工作流 JSON(diff 前用) | af_command_results.payload |
| `patch_workflow` | `{wf_id, ops}` | JSON-Patch-lite 增量修改(add/replace/remove/set-meta)→ 重算 risk → 保存,destructive 重审 | af_command_results,opsApplied + new riskLevel |
| `dry_run_workflow` | `{wf_id, params?}` | 显式 dry-run,异常也返回结构化 payload(player 抛出异常: ...) | af_command_results.payload(含 success/error) |
| `list_workflow_logs` | `{wf_id, limit?, since?}` | 最近的审计行(URL/method/status/duration/response 前1KB) | af_command_results.payload.rows |
| `cancel` | `{cmd_id?}` | 取消正在跑的命令或工作流 | af_command_results |

### Iteration loop (v1.1+)

External AI 的典型迭代闭环:

```
save_workflow → dry_run_workflow → 失败?
                ↓ 是
                list_workflow_logs (看每步发了什么请求)
                ↓
                patch_workflow ops:[替换错的 selector / URL / config]
                ↓
                dry_run_workflow → 通过 ✓ → 在 af_chat 写 suggested_wf_id
```

### 敏感数据自动脱敏

`save_workflow` 时,内网会扫描每个步骤 config:
- 命中 `password / token / api-key / cookie / private-key / 中国身份证 / 中国手机号 / 银行卡` → 自动替换为 `[REDACTED:<kind>]`
- 回执 `payload.credWarnings` 列出哪些步骤被脱敏
- AI 应在最终回复中提示用户:"已自动脱敏 X 个字段,请在 UI 用变量替换"

## Chat-flow conventions (v1.0+)

When user request comes via `af_chat` (role=user, status=pending):

1. **DO NOT** immediately fire commands — first post a `role=ai` message
   acknowledging what you understood. Reduces user anxiety waiting.
2. If user gave a URL, ALWAYS `inspect_page` first to learn the real DOM.
   Don't guess selectors blindly from screenshots alone.
3. After building workflow, post final AI reply with `suggested_wf_id` so
   user can one-click open it from chat.
4. **CRITICAL**: PATCH the user message's `status` to `answered` after you
   handle it (or it will keep showing as pending and trigger reprocessing).

### Reading af_config to find active AutoFlow instance

```js
const rows = await listRecords('af_config')
const active = rows
  .filter(r => r.fields.status === 'active' && r.fields.instance_id)
  .sort((a, b) => (b.fields.last_seen_at || 0) - (a.fields.last_seen_at || 0))[0]
// active.fields.instance_id is your target_instance for af_commands
```

Test/stale heartbeats may exist — always pick MOST RECENT `last_seen_at`.

### Self-test reference

See `scripts/r24-e2e-bridge-test.mjs` in the autoflow repo for a complete
working example of the full chat → inspect → save_workflow → reply loop.
