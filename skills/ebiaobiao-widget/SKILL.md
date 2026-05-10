---
name: ebiaobiao-widget
description: "Develop, preview, test, and publish 报表 self-built widget mini-programs using React and @apitable/widget-sdk. Use when Codex needs to build a vika/报表 mini-program UI, field-mapping tool, dashboard, reporting assistant, responsive phone/desktop/embedded interface, widget-cli project, local HTTPS preview, configured-host release, or widget permission-safe data mutation."
---

# 报表自建小程序

Use for 报表 "小程序" unless the user explicitly means another mini-program platform. These are vika self-built widgets inside the 报表 container.

## 已知坑点 (Production Gotchas)

Real production bugs hit during the WordDeck release. Read these BEFORE first release — every one of them prints `successful release` while silently leaving the widget broken.

### 1. `packageId: "wpkReplace001"` is a placeholder, not a real ID

**Symptom:** `npm run release` prints `successful release` but the widget never appears under "空间站自建" (Space self-built) in the widget center.

**Why:** The starter ships with `"packageId": "wpkReplace001"` in `widget.config.json`. With `--ci`, widget-cli uploads the bundle but auto-skips the interactive `Release a new widget with Id: wpkReplace001 Y/n?` prompt — so the **create-package** step is never executed. The bundle is in the CDN but the package is not registered to the space.

**Fix (must do BEFORE first release):**
1. Edit `widget.config.json` and set `packageId` to a UNIQUE value matching `wpk[A-Za-z0-9]{10}` (literal `wpk` + exactly 10 alphanumerics). Example: `wpkWdMaiMai01`.
2. Run `npm run release:confirm` — NOT `npm run release`. The `:confirm` variant pipes `Y\n` so the create-package prompt is answered.
3. Confirm registration by grepping the output for: `Successful create widgetPackage from server`. Without that exact line, the package is NOT in the space and you will not see it in the widget center.

### 2. `sandbox: false` silently rewrites every CSS class with the packageId prefix

**Symptom:** Widget renders as unstyled HTML even though CSS imports compile fine and the bundle is published.

**Why:** With `"sandbox": false`, widget-cli's css-loader prefixes every local class with the packageId. Source `.phone-frame` becomes `.wpkWdMaiMai01phone-frame` in the bundle. JSX written as `className="phone-frame"` no longer matches anything. The relevant code in `node_modules/@apitable/widget-cli/lib/webpack.config.js`:

```js
modules: {
  getLocalIdent: (context, localIdentName, localName) => {
    return (widgetConfig.sandbox ? '' : packageId) + localName;
  }
}
```

With `sandbox: true`, the prefix is empty and classes render as-is. The widget runs in `/widget-stage?widgetId=...` (separate iframe), which is what apitable expects for ordinary React widgets.

**Fix — pick ONE pattern and stick to it:**
- **Easy path (recommended):** set `"sandbox": true` in `widget.config.json`. Then plain `import './style.css'` + `className="phone-frame"` works.
- **Sandbox=false path (rare, only if widget must touch parent DOM):** use CSS Modules:
  ```tsx
  import styles from './style.css';
  <div className={styles['phone-frame']}>...</div>
  ```
  Or wrap selectors in `:global(...)` (see `assets/widget-app-template/src/style.css`).

### 3. `min-height: 100vh` and `overflow: hidden` on root containers clip widget panels

**Symptom:** Bottom of the UI is cut off; cannot scroll to action button or footer; sticky tab bar hides content; expand/collapse panel breaks.

**Why:** Widget panels are NOT phones. They are small iframes (~280px wide on the right side panel, or floating panels at variable size). CSS that assumes a mobile viewport (`100vh`, `overflow:hidden` on body, `position:fixed` for tab bars) traps content inside an unscrollable iframe.

**Fix:**
- Use `min-height: 100%` instead of `100vh` on top-level containers.
- Do NOT put `overflow: hidden` on `body` / `#root` / `.app-root`. Allow `body { overflow-y: auto; overflow-x: hidden; }`.
- For sticky bars, prefer `position: sticky; bottom: 0;` over `position: fixed;`.
- Pages with a sticky tab bar need ~70–80px bottom padding so content does not slide under it.
- Verify scrolling in a fixed 390×520 viewport — full-page screenshots can hide the clipping.

### 4. SSO redirect breaks naive "logged in" detection

**Symptom:** Playwright auth helper thinks user is logged in, then opens a datasheet and gets bounced back to QR scan.

**Why:** Login on this kind of deployment is QR scan via an external SSO host (e.g. `<sso-host>/wwopen/sso/qrConnect`) — a different host from the configured `EBIAOBIAO_HOST` — and the path is `qrConnect`, which does not contain `/login`. A check like `!url.includes('/login')` returns true on the SSO page even though the user is not authed yet.

**Fix:** gate auth detection on the configured host AND exclude SSO paths:
```js
const HOST = new URL(process.env.EBIAOBIAO_HOST).host;  // e.g. app.example.cn:7886
function isAuthedUrl(u) {
  return u.includes(HOST) &&  // post-login host only
         !u.includes('/login') &&
         !u.includes('qrConnect') &&
         !u.includes('/sso/');
}
```

Use Playwright `launchPersistentContext` with a profile dir so the QR-scan session persists across runs.

### 5. No clean external "inject dstIds" point in apitable widgets

**Symptom:** `window.WORDDECK_DSTIDS = [...]` style external injection from the host page does not reach the widget iframe in any predictable way.

**Why:** The widget runs in an isolated iframe (especially with `sandbox: true`). There is no documented mechanism to read globals from the parent host.

**Fix:**
- **v0.1 (smoke / single-tenant):** embed dstIds directly in code (e.g. `dst-config.ts` returns hardcoded IDs). Keep them out of the public repo via a `*.local.ts` file + `.gitignore`.
- **v1.0 (production / multi-tenant):** use the widget settings panel — `useSettingsButton(...)` + `useFields(...)` to let users pick datasheets, then persist with `useCloudStorage`.

## Workflow

1. Validate setup and follow `ebiaobiao-dev` Creation Flow.
2. Start from `assets/widget-app-template/` unless an existing widget project is present.
3. **Before first release**, edit `widget.config.json`:
   - Replace `packageId: "wpkReplace001"` with a unique `wpk[A-Za-z0-9]{10}` value.
   - Set `sandbox: true` unless you have a specific reason for `sandbox: false` (and have refactored to CSS Modules / `:global(...)`).
4. Keep tokens out of frontend code; privileged Fusion API calls belong in a backend.
5. Build compact operational UI: mapping controls, summary, preview, action bar, progress, result log.
6. Persist mappings with `useCloudStorage`; for datasheet selection use `useSettingsButton` + `useFields`.
7. Check permissions before mutation.
8. Verify 390px, 768px, 1440px, and narrow embedded windows. **Avoid `100vh` / `overflow:hidden` on root containers** (see Gotcha 3). The release script reads `EBIAOBIAO_HOST` and `EBIAOBIAO_API_TOKEN` from local configuration.
9. **Publish with `npm run release:confirm`** (NOT `npm run release`) for the first release of any new packageId. The `:confirm` variant pipes `Y\n` to the create-package prompt. Grep output for `Successful create widgetPackage from server` to confirm registration. If that line is missing, the package was NOT created in the space.
10. Final report: widget name, package ID, version, status, target space, table/view, key UI, responsive checks, container/browser verification.

## Commands

```bash
npm install
npm run build
npm run release:confirm   # first release of a new packageId — answers Y to create-package prompt
npm run release           # subsequent releases of an already-registered package
```

## UI Rules

- First screen is the tool, not a landing page.
- Support phone, desktop, and embedded windows.
- Show loading, empty, permission-denied, validation-error, progress, success, and partial-failure states.
- Prefer official widget components: `FieldPicker`, `ViewPicker`, `CellValue`, buttons, theme variables.
- Do not assume mobile viewport in CSS — widget panels are small iframes (see Gotcha 3).

## References

- `references/widget-development.md`: release rules, responsive checklist, live smoke lessons.
- `assets/widget-app-template/`: responsive React starter (uses `:global(...)` + CSS Modules pattern).
