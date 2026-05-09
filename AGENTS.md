# Agent Instructions

This repository provides 报表 development skills for coding agents.

## Start Here

When a user asks for 报表 work, first read:

```text
skills/ebiaobiao-dev/SKILL.md
```

Then load only the sub-skill needed for the task:

- Setup and space switching: `skills/ebiaobiao-setup/SKILL.md`
- Fusion API tables/records/attachments: `skills/ebiaobiao-fusion-api/SKILL.md`
- Self-built Widget mini-programs: `skills/ebiaobiao-widget/SKILL.md`
- Script mini-programs: `skills/ebiaobiao-script/SKILL.md`
- Embedded apps and backend workflows: `skills/ebiaobiao-workflows/SKILL.md`

## Required Workflow

For create/build requests:

1. Ask 3-5 core questions about the business goal, users, data fields, actions/statuses, target space, and publish need.
2. Give a short plan.
3. Run setup check and read-only discovery before writes.
4. Create, test, publish if requested, then report the result clearly.

Never ask the user to paste an API Token into chat. Use local `.env.local` or `.ebiaobiao/profiles/*.env`.

## Local Commands

Initialize a project:

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py init --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py check --target .
```

Run repository quality checks:

```bash
python3 tools/ebiao_quality_gate.py --live never
```
