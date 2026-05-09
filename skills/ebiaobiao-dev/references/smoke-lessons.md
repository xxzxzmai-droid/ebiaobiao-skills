# 报表 Skill Smoke Lessons

Use this reference when a live 报表 task fails in a way that looks like a known platform or tooling issue.

## Fusion API

- Create and update record payloads should use field names in `fields` maps. Keep field IDs for reads, durable mapping, and Widget SDK operations.
- Search nodes with the Fusion v2 node query endpoint; do not invent a `/nodes/search` path.
- Field deletion needs the space-scoped path.
- Checkbox field creation needs an icon property. Record reads may represent checked and unchecked values differently across formats.
- MultiSelect record writes accept arrays of option names when using field-name payloads.
- New datasheets can include default blank rows. Delete empty records before seeding useful data so the first real record appears at the top.
- Treat HTTP 200 with `success=false` as a failed API call.

## Widget

- Widget CSS must use CSS Modules or explicit global selectors. Plain `import './style.css'` with ordinary class names can publish as unstyled HTML.
- Keep `html`, `body`, and `#root` fixed at full height with hidden overflow, then put scrolling on the top-level widget app container.
- Verify narrow embedded windows with a short fixed-height viewport. Full-page desktop screenshots do not catch bottom clipping.
- Full `widget.config.json` metadata is required for reliable start and release: entry, package ID, version, localized name/description, icon, cover, author fields, and sandbox.
- Pin the official SDK, CLI, React, and ReactDOM versions used by the template unless a new official compatibility matrix is verified.
- A new package release can still ask for confirmation even with CI flags; automation should be ready to pipe an explicit confirmation for first publish.
- Package details showing Online is the reliable publish signal when a release-history sub-query fails with a parameter error.

## Browser And Handoff

- Browser plugin timeouts are not automatically 报表 failures. Fall back to API checks, Widget build checks, bundle CSS inspection, and static viewport screenshots.
- Keep real test IDs, screenshots, tokens, and workspace-specific package IDs out of shared docs and commits.
- Prefer a reusable quality gate over ad hoc smoke commands so colleagues can reproduce the same checks.
