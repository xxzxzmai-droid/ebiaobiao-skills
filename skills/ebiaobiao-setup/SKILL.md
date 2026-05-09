---
name: ebiaobiao-setup
description: "Initialize, validate, switch, and troubleshoot private e报表/vika development configuration. Use when Codex needs one-click project setup, personal token setup, target space/workstation switching, saved profiles, .env.local generation, widget development dependency preparation, EBIAOBIAO_HOST/API_BASE/SPACE_ID/API_TOKEN checks, or readiness before Fusion API and Widget work."
---

# e报表配置初始化

Use before live API calls or widget release. Secrets stay in project-local files, never chat.

## Commands

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py init --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py check --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space list --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space add finance --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space use finance --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py widget-env --target .
```

If token or space ID is missing, setup opens a local config file. Ask the user to save it, then rerun `check`.

## Model

- `.env.local`: active config.
- `.ebiaobiao/profiles/<name>.env`: saved user/space profile, ignored by git.
- `.ebiaobiao/config.json`: active profile name only.

Natural language space switching maps to `space list/add/use`.

## Guardrails

- Defaults: private host, private Fusion base, `EBIAOBIAO_PROFILE=dev`.
- Writes require profile `dev`, token, private host, and space ID.
- Use `EBIAOBIAO_API_TOKEN`; `VIKA_API_TOKEN` is legacy fallback.

## References

- `scripts/ebiao_setup.py`: init/profile/widget-env tool.
- `scripts/check_config.py`: compatibility checker.
- `references/configuration.md`: config details and failures.
