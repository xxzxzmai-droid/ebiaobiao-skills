# e报表 Configuration

## One-Entry Setup

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py init --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py check --target .
```

The initializer creates `.env.local`, `.env.local.example`, `.gitignore`, `.ebiaobiao/profiles/<profile>.env`, and a widget starter under `widgets/_ebiaobiao_widget_starter`. If token or space ID is missing, it opens `.env.local` for manual editing.

## Profiles

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space add dev-a --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py profile import current --target . --use
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space list --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py space use dev-a --target .
```

Use spaces/profiles to switch target spaces or user tokens. `profile import` saves an existing `.env.local` as a named profile. Profile `.env` files are ignored by git.

## Variables

- `EBIAOBIAO_HOST`: default `https://app.ehv.csg.cn:7886`.
- `EBIAOBIAO_API_BASE_URL`: default `https://app.ehv.csg.cn:7886/fusion/v1`.
- `EBIAOBIAO_SPACE_ID`: target development space. Required for writes.
- `EBIAOBIAO_API_TOKEN`: personal API token. Required for API calls.
- `VIKA_API_TOKEN`: legacy fallback only.
- `EBIAOBIAO_PROFILE`: use `dev` to allow direct development-space writes.
- `EBIAOBIAO_SSL_VERIFY`: set `0` only for the private host when internal certificates break local smoke tests.

## Safety Policy

Read-only commands may run with a token and API base. Write commands must pass all checks:

- `EBIAOBIAO_PROFILE=dev`
- private host contains `app.ehv.csg.cn:7886`
- token present
- target `spaceId` present from env or explicit command argument

If any check fails, generate code or dry-run output instead of mutating e报表.

## Setup Checklist

1. Log in to private e报表.
2. Generate a personal API token from user/developer settings.
3. Copy the target space ID from the space cockpit or use the spaces API.
4. Store token and space ID in project-local `.env.local`.
5. Run `check_config.py`.
6. Run `ebiao_fusion.py spaces` to verify token permissions.

## Project Initialization

Use `scripts/ebiao_setup.py init --target <project-dir>` to create:

- `.env.local.example`: safe placeholder configuration.
- `.env.local`: active local profile.
- `.ebiaobiao/profiles/<name>.env`: saved token/space profile.
- `.gitignore`: ignores `.env.local`.
- `widgets/_ebiaobiao_widget_starter`: optional prepared Widget starter with dependencies.

The initializer writes secrets only to the current project config file. Prefer manual editing over passing tokens in command history or chat.
