---
name: ebiaobiao-dev
description: "Route and coordinate private e报表/vika/AITable development work. Use when Codex is asked to build or maintain e报表 solutions, choose between Fusion API, self-built widget mini-programs, script mini-programs, automation workflows, eLink or enterprise WeChat embedded apps, private deployment host configuration, table creation, data processing, widget release, or reporting tools backed by vika datasheets."
---

# e报表开发总入口

Private host: `https://app.ehv.csg.cn:7886`. Public vika docs are syntax references only. Never expose API tokens in chat, source, screenshots, commits, widget frontend code, or shared links.

## Start

For a new project/user:

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py init --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py check --target .
```

If config is missing, setup opens a local file. Ask the user to fill and save it there, then rerun `check`.

## Creation Flow

For "create report/table/widget/script/workflow" requests:

1. Ask 3-5 core questions: goal, users, data/fields, actions/statuses, target space/profile, publish need.
2. Give a short plan: artifacts, schema/UI/workflow, tests, publish target.
3. Execute end to end unless stopped: config check, read-only discovery, create/update, seed useful samples, build/test, publish if needed.
4. Final report: created names, target space/profile, IDs or publish status, where to find it, what was tested, cleanup/follow-up. Never include tokens.

## Route

- Setup/token/space switching: `ebiaobiao-setup`.
- Tables, fields, records, nodes, attachments: `ebiaobiao-fusion-api`.
- Self-built Widget mini-programs: `ebiaobiao-widget`.
- In-table scripts: `ebiaobiao-script`.
- eLink, enterprise WeChat, backend gateways, scheduled jobs: `ebiaobiao-workflows`.

Load only the chosen sub-skill and needed references.

## Defaults

- Fusion API base: `https://app.ehv.csg.cn:7886/fusion/v1`
- Env keys: `EBIAOBIAO_HOST`, `EBIAOBIAO_API_BASE_URL`, `EBIAOBIAO_SPACE_ID`, `EBIAOBIAO_API_TOKEN`, `EBIAOBIAO_PROFILE`
- Legacy token key: `VIKA_API_TOKEN`
- Writes require `EBIAOBIAO_PROFILE=dev`, private host, token, and target space ID.

## Guardrails

- Treat "e报表小程序" as vika self-built Widget unless explicitly told otherwise.
- Treat "工作站", "空间站", and "space" as target `EBIAOBIAO_SPACE_ID`.
- Run read-only discovery before writes.
- Keep business UIs click-first and responsive for phone, desktop, and enterprise WeChat embedded windows.
- For known live-test failures, read `references/smoke-lessons.md`.
