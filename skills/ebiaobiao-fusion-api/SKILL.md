---
name: ebiaobiao-fusion-api
description: "Build and operate 报表/vika Fusion API automations. Use when Codex needs to create datasheets or fields, inspect spaces/nodes/views/fields, query records, import or export records, create/update/delete records, upload attachments, validate schemas, write audit/status fields, or automate table-driven reporting against a configured host."
---

# 报表 Fusion API

Use for local/server automation against the configured 报表 host. Translate public examples to the local `EBIAOBIAO_API_BASE_URL`.

## Workflow

1. Validate config with `ebiaobiao-setup`.
2. For new tables/reports, follow `ebiaobiao-dev` Creation Flow before writes.
3. Discover first: `config check`, `spaces`, `nodes`, `fields`, `views`, small `records` query.
4. Read with `fieldKey=id` after mapping fields.
5. Create/update record payloads use field names in `fields` maps.
6. Chunk writes: records max 10 per request; reads max 1000 per page; upload one attachment per request.
7. New datasheets may contain default blank rows; run `delete-empty-records` or use `create-datasheet --clean-empty-records` before seeding.
8. Final report: table name, datasheet ID, fields, sample records, smoke checks, skipped cleanup.

## CLI

```bash
python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py config check
python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py spaces
python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py nodes --space-id "$EBIAOBIAO_SPACE_ID"
python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py fields dstXXXXXXXX --field-key id
python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py records dstXXXXXXXX --field-key id --all
```

Writes require development profile and target space; the CLI enforces this. Use `--dry-run` to inspect payloads without mutation.

## References

- `references/fusion-api.md`: endpoint map, payloads, limits, safety rules.
- `scripts/ebiao_fusion.py`: guarded CLI.
