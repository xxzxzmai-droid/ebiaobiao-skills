---
name: ebiaobiao-script
description: "Write and adapt 报表/vika Script mini-programs for in-table automation. Use when Codex needs quick JavaScript scripts inside the Script widget for find/replace, required-field validation, duplicate checks, batch updates, record matching, attachment-to-URL conversion, user prompts, output tables, lodash helpers, fetch calls, or lightweight one-off data processing without building a full widget."
---

# 报表脚本小程序

Use scripts for fast in-table processing when a full Widget project is unnecessary. Scripts run inside the 报表 Script mini-program and use the platform-provided `space`, `input`, `output`, `fetch`, and lodash APIs.

## When To Choose Script

- One-off or repeatable table cleanup.
- Find/replace, validation, duplicate detection, record matching.
- Batch status updates after user confirmation.
- Lightweight API calls that do not require a custom UI.

Choose `ebiaobiao-widget` instead when the user needs a polished multi-step UI, persistent field mapping, dashboards, or distribution through the self-built widget center.

## Workflow

1. Ask the user-facing script to select datasheet, view, and fields through `input.*Async` APIs.
2. Read records from the active datasheet or selected view.
3. Validate inputs and show counts before mutation.
4. Batch updates and print a concise result summary.
5. Do not paste API tokens into scripts. If an external privileged service is needed, call a backend endpoint that handles credentials server-side.

## Templates

- `assets/script-templates/validate-required-fields.js`
- `assets/script-templates/find-replace.js`
- `assets/script-templates/batch-status-update.js`

## References

- `references/script-api.md`: available APIs, script structure, and safety patterns.
