---
name: ebiaobiao-widget
description: "Develop, preview, test, and publish 报表 self-built widget mini-programs using React and @apitable/widget-sdk. Use when Codex needs to build a vika/报表 mini-program UI, field-mapping tool, dashboard, reporting assistant, responsive phone/desktop/embedded interface, widget-cli project, local HTTPS preview, configured-host release, or widget permission-safe data mutation."
---

# 报表自建小程序

Use for 报表 "小程序" unless the user explicitly means another mini-program platform. These are vika self-built widgets inside the 报表 container.

## App Shell Layout (REQUIRED PATTERN — required for ALL widgets)

The apitable host wraps each widget in a fixed-height iframe with `overflow: hidden`. Body-level scrolling does NOT work. Sticky positioning relative to the document does NOT reliably hit the visible bottom of the widget area.

This is the same pattern Slack/Gmail/Linear/etc use for `header + content + footer`: a flex column whose middle child is the SOLE scroll viewport. Do this even if you don't think you need it — content grows, viewports shrink, and any other pattern produces "tab bar in the middle of empty space" or "content clipped, unreachable" bugs.

**Required architecture:**

```css
html, body { margin: 0; height: 100%; overflow: hidden; }
#root {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
/* Wrapper chain — every inner wrapper between #root and the scrolling
 * middle must propagate `flex: 1; min-height: 0; overflow: hidden`.
 * `min-height: 0` is the critical CSS gotcha — without it, flex children
 * cannot shrink below their content size and the scroll viewport cannot
 * constrain. */
.outer-wrapper, .inner-wrapper {
  display: flex; flex-direction: column;
  flex: 1; min-height: 0; overflow: hidden;
}
/* The ONE scrolling region — the visible content area. */
.scroll-area {
  flex: 1; min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
/* Chrome (header, footer, tabs, action bars). flex-shrink: 0 keeps them
 * at their natural height; they sit at the column ends. NEVER use
 * position: sticky or fixed for these — they break silently in nested
 * iframes. */
.tabs, .action-bar, .toolbar { flex-shrink: 0; }
```

**Sub-pattern — page with its own bottom action bar (e.g. a Reveal / Detail page with rating buttons):**

A page that has its own bottom-pinned controls (separate from the global tab bar) follows the same pattern scoped to itself. The page becomes a flex column inside the scrolling page area, with its own internal scrolling middle:

```css
.detail-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;       /* fill the parent page area */
  overflow: hidden;
}
.detail-hero  { flex-shrink: 0; }
.detail-body  { flex: 1; min-height: 0; overflow-y: auto; }
.detail-actions { flex-shrink: 0; /* rating / submit buttons */ }
```

When this sub-pattern is active, the OUTER `.page-area` does not scroll for this page (the inner `.detail-body` does). That's fine — `height: 100%` makes the page exactly fit the page area, so the outer scroll has nothing to scroll.

**The 4 CSS gotchas that have caused recurring bugs:**

1. **Apitable's host wrapper has `overflow: hidden` at a host-controlled height.** You cannot rely on window/body scroll. The scroll viewport MUST be inside your widget — typically `.page-area`.

2. **`flex: 1` alone is not enough.** Inner flex children need `min-height: 0` to shrink. Without it, `flex: 1` resolves to `flex: 1 1 auto` where `auto = content size`, so a tall content child blows the parent past the viewport instead of allowing the scrolling middle to constrain.

3. **`position: sticky` is unreliable in apitable widgets.** Sticky elements stick to the nearest SCROLLING ancestor — but if your scroll container is several wrappers deep and any ancestor has `overflow: hidden`, sticky breaks silently. Use flex layout instead (header at top, scrolling middle, footer at bottom — all in a flex column).

4. **`min-height: 100vh` is wrong inside the widget.** `100vh` = the host page's viewport, NOT your widget's iframe area. Use `height: 100%` against the apitable wrapper (which is itself sized by the host). Then your widget exactly fills the widget area, whatever size it is (panel ~280px, expanded ~600px, fullscreen ~1080px).

**Verification checklist (run after every change):**

- [ ] `grep -rn "position: sticky" src/` → no matches in chrome / tab / footer styles
- [ ] `grep -rn "100vh\|100dvh" src/` → only in optional desktop-only chrome (rare)
- [ ] `grep -rn "flex: 1 0 auto" src/` → no matches (use `flex: 1; min-height: 0`)
- [ ] In dev, resize the widget panel to 3 sizes (panel ~280, expanded ~600, fullscreen ~1080). Tabs / action bars must be at the visible bottom in all sizes.
- [ ] Force content > viewport height. Page must scroll inside `.page-area` (or the page's own scrolling middle). Tabs stay at bottom (do NOT scroll away).
- [ ] Force content < viewport height. Tabs still at bottom (no gap below).
- [ ] Headless smoke check (optional): use `tests/layout-smoke.html` + `tests/layout-smoke.mjs` from the WordDeck widget as a template. It loads the actual CSS files and asserts tab/action-bar position + scroll reachability across 3 viewports × short/long content.

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

**Fix:** Apply the App Shell Layout pattern at the top of this file. NOT `100vh`, NOT body scroll, NOT sticky for chrome — flex column with `min-height: 0` and a scrolling middle. See also G6.

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

### 6. Sticky tab bar / floating action bar bugs (the recurring layout bug)

**Symptom A (short content):** BottomTabs (or action bar) appears in the MIDDLE of the visible widget area with empty white space below it.
**Symptom B (long content):** Content at the bottom of a page is clipped/unreachable; user CANNOT scroll to it (e.g. a 排行榜 / leaderboard section sitting below the visible area).

**Why:** Patterns like `#root { overflow-y: auto; min-height: 100vh }` + `.tabs { position: sticky; bottom: 0 }` LOOK right but break in apitable hosts. The host's iframe wrapper has its own `overflow: hidden` at a height the widget didn't pick, so:
- Sticky tabs stick to the wrong bottom (the wrapper bottom, not the iframe-visible bottom).
- The scroll container is the wrong element, so dragging on the apparent bottom of the iframe does not actually scroll.

**Fix:** Apply the App Shell Layout pattern from the top of this file. The single fix that resolves both symptoms is:
- `html, body { height: 100%; overflow: hidden }` — kill body scroll
- `#root` → flex column, `height: 100%`, `overflow: hidden`
- Wrapper chain → `flex: 1; min-height: 0; overflow: hidden`
- The ONE scrolling region: `.page-area { flex: 1; min-height: 0; overflow-y: auto }`
- Tabs / action bars: `flex-shrink: 0` (NOT sticky, NOT fixed)

See `references/layout-app-shell.md` for the full pattern, the Reveal-style sub-pattern (page with its own bottom action bar), and copy-pasteable CSS.

### 7. `release` prompts for VERSION before the create-package prompt — naive `printf 'Y\n'` answers the wrong prompt

**Symptom:** `printf 'Y\n' | widget-cli release ...` (the literal `release:confirm`) dies with `npm error Invalid version: Y` / `npm version Y` → `Y: command not found`. Nothing is uploaded.

**Why:** `widget-cli release` asks **two** questions, in this order:
1. `release version [0.1.1]:` — it auto-bumps and asks you to confirm/override the version.
2. `Release a new widget with Id: wpkXXX Y/n?` — the create-package prompt (only for a new packageId).

A piped `Y` lands on prompt **1**, so widget-cli runs `npm version Y` and aborts. The `:confirm` one-liner only works if the version prompt is suppressed.

**Fix — pass the version as a flag, pipe `Y` only for create-package:**
```bash
printf 'Y\n' | widget-cli release --version 0.1.0 \
  --host "$EBIAOBIAO_HOST" --uploadHost "$EBIAOBIAO_HOST" --token "$EBIAOBIAO_API_TOKEN"
```
- `--version <v>` (or `-v`) skips prompt 1 entirely.
- Do **NOT** add `--ci` for a *new* packageId: `--ci` suppresses BOTH prompts, which silently skips create-package (Gotcha 1). Use `--ci` only for *subsequent* releases of an already-registered package.
- Self-signed host (internal e报表): export `NODE_TLS_REJECT_UNAUTHORIZED=0` before the release, or widget-cli's upload fails on the cert.
- Success looks like: `Successful create widgetPackage from server` → `Compile Succeed` → `successful release widget wpkXXX@<v>`.

## Recipe: embed a Dify chatflow (or any external chat / web app) as a widget

A common ask is "把我们的 Dify 智能体做成 e报表小程序". The widget is just a thin React shell that **iframes** the Dify chatbot URL; the chatflow itself stays in Dify. This is ~120 lines (one component + app-shell CSS). Full copyable source: `examples/dify-assistant-widget/` (component, settings panel, cert-hint bar, app-shell CSS, release script).

**The one hard gate — self-signed cert / mixed content (read before promising it works):**
The widget runs inside e报表 (https) in the user's browser. To show the chat, that browser must load the Dify URL **directly** — the widget has no server-side proxy. If Dify is an internal IP with a self-signed cert (the common case, e.g. `https://10.x.x.x:5030`), the browser **silently** blocks the iframe (cert-untrusted + mixed-content) — blank panel, and `iframe` fires **no** `onError`, so you cannot detect it in JS.
- **Clean fix:** expose Dify behind a valid cert at a browser-reachable URL.
- **Workaround (internal/self-signed):** the user opens the Dify origin once in a new tab and clicks "proceed (unsafe)" to register a cert exception, then reloads the widget. Build this into the UI: a hint bar with an `<a target="_blank" href={difyOrigin}>` link + a "reload" button (bump an iframe `key`). A desktop-app Go client sidesteps all this with a same-origin reverse proxy; a widget cannot.
- A native React chat UI calling the Dify REST API instead of an iframe does **not** help — same origin still has the cert/mixed-content/CORS wall.

**Config, not hardcode:** never bake the Dify URL/token into source (offline-first rule). Store them with `useCloudStorage('difyBaseUrl' | 'difyToken' | ...)` (space-shared, admin sets once) and expose a settings panel via `useSettingsButton`. Build the src as `` `${base}/chatbot/${token}` `` (standard embed; identity defaults to the chatflow's built-in demo identity) or `` `${base}/chat/${token}?mat_role=...&mat_org_id=...` `` (plaintext identity params). `/chatbot/` needs gzip+base64-encoded param values; `/chat/` accepts plaintext — prefer `/chat/` when you must pass identity from a widget (no backend to sign a token).

**Layout:** app-shell flex column — fixed header + optional cert-hint bar (`flex-shrink: 0`) and the `<iframe className="...">` filling the `flex: 1; min-height: 0` middle. Never `100vh`/sticky (Gotchas 3 & 6).

**Publish:** new packageId → Gotcha 7 (`--version` flag + pipe `Y`, no `--ci`). Working example shipped to production: `wpkMatAssist1` (物资智能助手), space `spcjCWa40legH`.

## Workflow

1. Validate setup and follow `ebiaobiao-dev` Creation Flow.
2. Start from `assets/widget-app-template/` unless an existing widget project is present.
3. **Before first release**, edit `widget.config.json`:
   - Replace `packageId: "wpkReplace001"` with a unique `wpk[A-Za-z0-9]{10}` value.
   - Set `sandbox: true` unless you have a specific reason for `sandbox: false` (and have refactored to CSS Modules / `:global(...)`).
4. Keep tokens out of frontend code; privileged Fusion API calls belong in a backend.
5. Build compact operational UI: mapping controls, summary, preview, action bar, progress, result log.
   **Apply the App Shell Layout pattern from the top section of this file** when laying out the widget. Use it from day one — retrofitting is painful and the bug has hit WordDeck 5+ times.
6. Persist mappings with `useCloudStorage`; for datasheet selection use `useSettingsButton` + `useFields`.
7. Check permissions before mutation.
8. Verify 390px, 768px, 1440px, AND the 3 apitable widget panel sizes (~280px panel, ~600px expanded, ~1080px fullscreen). Run the layout verification checklist from the App Shell Layout section. Avoid `100vh` / `overflow:hidden` on root containers (Gotchas 3 & 6). The release script reads `EBIAOBIAO_HOST` and `EBIAOBIAO_API_TOKEN` from local configuration.
9. **First release of a new packageId:** pass `--version <v>` and pipe `Y` for the create-package prompt — do NOT use `--ci`, and do NOT rely on a bare `printf 'Y\n'` (it answers the version prompt, not create-package — see Gotcha 7). Grep output for `Successful create widgetPackage from server` to confirm registration. If that line is missing, the package was NOT created in the space.
10. Final report: widget name, package ID, version, status, target space, table/view, key UI, responsive checks, container/browser verification.

## Commands

```bash
npm install
npm run build
# first release of a NEW packageId — version via flag, pipe Y for create-package, no --ci (Gotcha 7):
NODE_TLS_REJECT_UNAUTHORIZED=0 bash -c 'printf "Y\n" | widget-cli release --version 0.1.0 \
  --host "$EBIAOBIAO_HOST" --uploadHost "$EBIAOBIAO_HOST" --token "$EBIAOBIAO_API_TOKEN"'
npm run release           # subsequent releases of an already-registered package (--ci is fine here)
```

## UI Rules

- First screen is the tool, not a landing page.
- Support phone, desktop, and embedded windows.
- Show loading, empty, permission-denied, validation-error, progress, success, and partial-failure states.
- Prefer official widget components: `FieldPicker`, `ViewPicker`, `CellValue`, buttons, theme variables.
- Do not assume mobile viewport in CSS — widget panels are small iframes (see Gotchas 3 & 6, and the App Shell Layout section).

## References

- `references/layout-app-shell.md`: the App Shell Layout pattern in full — copy-pasteable CSS templates for the standard `tabs + page-area` layout, the `Reveal`-style page with its own bottom action bar, the 4 CSS gotchas in detail, and the verification checklist + headless smoke template.
- `references/widget-development.md`: release rules, responsive checklist, live smoke lessons.
- `assets/widget-app-template/`: responsive React starter (uses `:global(...)` + CSS Modules pattern).
