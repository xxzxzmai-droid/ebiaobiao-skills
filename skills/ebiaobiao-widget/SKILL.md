---
name: ebiaobiao-widget
description: "Develop, preview, test, and publish private e报表 self-built widget mini-programs using React and @apitable/widget-sdk. Use when Codex needs to build a vika/e报表 mini-program UI, field-mapping tool, dashboard, reporting assistant, responsive phone/desktop/enterprise-WeChat embedded interface, widget-cli project, local HTTPS preview, private host release, or widget permission-safe data mutation."
---

# e报表自建小程序

Use for e报表 "小程序" unless the user explicitly means WeChat mini-program. These are vika self-built widgets inside the e报表 container.

## Workflow

1. Validate setup and follow `ebiaobiao-dev` Creation Flow.
2. Start from `assets/widget-app-template/` unless an existing widget project is present.
3. Keep tokens out of frontend code; privileged Fusion API calls belong in a backend.
4. Build compact operational UI: mapping controls, summary, preview, action bar, progress, result log.
5. Persist mappings with `useCloudStorage`.
6. Check permissions before mutation.
7. Verify 390px, 768px, 1440px, and narrow embedded windows.
8. Publish with `widget-cli release --host https://app.ehv.csg.cn:7886 --uploadHost https://app.ehv.csg.cn:7886 --token "$EBIAOBIAO_API_TOKEN" --ci`; first package release may still need `printf 'Y\n' | npm run release`.
9. Final report: widget name, package ID, version, status, target space, table/view, key UI, responsive checks, container/browser verification.

## Commands

```bash
npm install
npm run build
npm run release
```

## UI Rules

- First screen is the tool, not a landing page.
- Support phone, desktop, and enterprise WeChat embedded windows.
- Show loading, empty, permission-denied, validation-error, progress, success, and partial-failure states.
- Prefer official widget components: `FieldPicker`, `ViewPicker`, `CellValue`, buttons, theme variables.

## References

- `references/widget-development.md`: release rules and responsive checklist.
- `assets/widget-app-template/`: responsive React starter.
