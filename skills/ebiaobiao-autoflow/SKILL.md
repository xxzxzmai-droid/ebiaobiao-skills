---
name: ebiaobiao-autoflow
description: Build, debug, and operate AutoFlow desktop RPA workflows from an *external* environment by writing commands to vika datasheets. Use when the user (typically the Claude on an internet-connected machine) is asked to create or fix automation flows for an AutoFlow instance running on an isolated internal network. Triggers include "build an AutoFlow workflow", "inspect a page for the internal AutoFlow", "diagnose a failed workflow", or any request that requires coordinating with internal-network RPA.
---

# ebiaobiao-autoflow

**Goal:** Let an external AI build / diagnose / run AutoFlow workflows by writing commands to a shared vika space. The internal AutoFlow polls these tables and executes locally with all safety checks (§5 10-layer model) in force.

## When to use

- User has both an external Claude environment AND an internal-network AutoFlow desktop installation
- User wants natural-language → automation workflow but the target system is air-gapped
- User asks for help diagnosing why a specific AutoFlow workflow failed (you read `af_audit_mirror` + `af_command_results`)

## Seven tables you'll work with

See [protocol-spec.md](./references/protocol-spec.md) for full schema. Quick reference:

| Table | You write | You read |
|-------|-----------|----------|
| af_config | ❌ | ✅ — check `status='active'` and `last_seen_at` within 2 min · **pick MOST RECENT instance**, old test rows may linger |
| af_commands | ✅ — your only way to ask AutoFlow to do something | ✅ — to see your command's status |
| af_command_results | ❌ | ✅ — the answer to your command |
| af_workflows | ✅ — draft (`source='ai_draft', status='draft'`) | ✅ — see existing workflows |
| af_page_info | ❌ | ✅ — when you issued `inspect_page`, the result lands here |
| af_audit_mirror | ❌ | ✅ — what AutoFlow has been doing |
| **af_chat** | ✅ — `role='ai'` replies + suggested_wf_id | ✅ — `role='user'` messages + attachments (user's actual question) |

## Chat-driven workflow building (new in v1.0)

The primary user surface is now **AI 对话** (chat panel). Real-world flow:

1. User writes natural-language request to `af_chat` (role='user', status='pending')
2. **You** poll `af_chat` for `role='user' AND status='pending'`
3. Acknowledge: post `role='ai'` message saying "I see, let me inspect first"
4. Write `inspect_page` cmd → poll `af_page_info` for result → analyse DOM
5. Build a complete workflow JSON (use nested condition/loop-over/loop-while
   for complex logic — fully supported)
6. Write a `save_workflow` cmd with the workflow as params
7. Wait for `af_command_results` to confirm save
8. Post final `role='ai'` reply with `suggested_wf_id` pointing at saved workflow
9. **MARK user message status='answered'** so it doesn't get re-processed

The user then opens the workflow in 🏠 我的工具, sees the 🤖 AI 建议 badge,
must click "🤖✓ 标记已审" to unlock running. If it fails, AutoFlow will
auto-write a `role='system'` message to the same conversation telling
you what broke — you write a fix and post a new save_workflow.

## Quick start

1. Check `af_config`: is there a row with `last_seen_at` < 2 min ago and `status='active'`? If not, ask the user to open AutoFlow.
2. Read user's intent + screenshot.
3. Issue `inspect_page` (write to `af_commands`) → wait for matching `af_page_info` row.
4. Draft a workflow → write to `af_workflows` with `source='ai_draft', status='draft'`.
5. Issue `save_workflow` referencing the draft.
6. Tell the user "草稿已保存,请去 AutoFlow 客户端点 ▶ 跑一次 来审查并执行".

## Command catalog

See [command-catalog.md](./references/command-catalog.md). The 7 commands:
inspect_page, start_recording, stop_recording, save_workflow, run_workflow (always dry-run from bridge), list_workflows, cancel.

## Rules

- All `cmd_id` MUST be UUIDs (crypto.randomUUID-style). The internal worker tracks processed IDs to deduplicate.
- `target_instance` MUST match the `instance_id` from `af_config`. Skip rows where it doesn't match — they belong to another AutoFlow.
- You CANNOT write to `af_command_results`, `af_page_info`, or `af_audit_mirror`. Those tables are internally written.
- For destructive workflows: the `save_workflow` command will SUCCEED only if the workflow JSON includes `acknowledgements.destructiveConfirmed: true` — but even then, the human must run it manually via UI.
- For `run_workflow`: the result will always carry `dryRun: true`. Real execution requires the human in the loop on the AutoFlow side.

## Diagnosing a failed workflow

1. Read latest rows from `af_audit_mirror` (filter by `workflow_id` if known)
2. Look at the failed step / error
3. Issue `inspect_page` against the failing URL to see current DOM
4. Compare selectors in the workflow JSON to what's actually on the page
5. Issue `save_workflow` with a corrected version

## See also

- [protocol-spec.md](./references/protocol-spec.md) — full table schemas and field types
- [command-catalog.md](./references/command-catalog.md) — every command + params + expected payload
