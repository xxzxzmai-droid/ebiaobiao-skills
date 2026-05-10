# Widget Development Reference

## Production Gotchas (release-blocking)

These are real bugs hit during the WordDeck widget release. Each one prints `successful release` while leaving the widget broken in a different way.

### G1. `wpkReplace001` placeholder + `--ci` = silent skip of create-package

`widget.config.json` ships with `"packageId": "wpkReplace001"`. With `--ci`, widget-cli auto-skips the interactive `Release a new widget with Id: wpkReplace001 Y/n?` prompt. The bundle uploads, but the create-package step never runs, so the package never appears in the space's "空间站自建" tab.

Fix:
1. Set `packageId` to a unique `wpk[A-Za-z0-9]{10}` (literal `wpk` + exactly 10 alphanumerics) BEFORE first release. Example: `wpkWdMaiMai01`.
2. Run `npm run release:confirm` — the `:confirm` script in `package.json` pipes `Y\n` so the prompt is answered.
3. Confirm registration by grepping the output for `Successful create widgetPackage from server`. Without that line, the package is NOT registered in the space, regardless of any `successful release` output.

### G2. `sandbox: false` rewrites every CSS class with the packageId prefix

By default the starter has `"sandbox": false`. widget-cli's css-loader (in `node_modules/@apitable/widget-cli/lib/webpack.config.js`) prefixes every local class with the packageId:

```js
modules: {
  getLocalIdent: (context, localIdentName, localName) => {
    return (widgetConfig.sandbox ? '' : packageId) + localName;
  }
}
```

So `.phone-frame` in source becomes `.wpkWdMaiMai01phone-frame` in the bundle. JSX written as `className="phone-frame"` no longer matches anything, and the widget renders as unstyled HTML.

Fix — pick ONE pattern:
- `"sandbox": true` (recommended): no prefix, plain `import './style.css'` + `className="phone-frame"` works. Widget runs in `/widget-stage?widgetId=...` (separate iframe), which is what apitable expects for typical React widgets.
- `"sandbox": false` + CSS Modules: `import styles from './style.css'` and `className={styles['phone-frame']}`, OR wrap selectors in `:global(...)`. Only choose this path if the widget specifically needs to manipulate parent DOM.

### G3. `min-height: 100vh` traps in widget panel mode

Widget panels are small iframes (≈280px wide on the right side panel, or floating expanded panels at variable size). They are NOT a phone viewport. CSS that assumes mobile (`min-height: 100vh`, `overflow: hidden` on body, `position: fixed` for tab bars) clips content and disables scrolling.

Fix:
- Use `min-height: 100%` instead of `100vh` on top-level containers.
- Do NOT put `overflow: hidden` on `body` / `#root`. Allow `body { overflow-y: auto; overflow-x: hidden; }`.
- For sticky bottom bars use `position: sticky; bottom: 0;` not `position: fixed;`.
- Pages with a sticky tab bar need ~70–80px bottom padding so content does not slide under it.
- Verify scrolling in a fixed 390×520 viewport, not just full-page screenshots.

### G4. SSO redirect breaks naive "logged in" URL checks

Login on these deployments is QR scan via an external SSO host (e.g. `<sso-host>/wwopen/sso/qrConnect`). That URL is on a different host from the configured `EBIAOBIAO_HOST` and does not contain the substring `/login`, so a check like `!url.includes('/login')` returns true even though the user is not yet authed.

Fix — gate auth detection on the configured host AND exclude SSO paths:
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

### G5. No external dstId injection point — embed or use settings panel

`window.WORDDECK_DSTIDS` and similar host-page globals do NOT reach the widget iframe (especially with `sandbox: true`). There is no documented inject-from-outside mechanism.

Fix:
- v0.1 (smoke / single-tenant): hardcode dstIds in a `dst-config.ts` module. Keep real IDs out of git via `*.local.ts` + `.gitignore`.
- v1.0 (production): use `useSettingsButton(...)` + `useFields(...)` to let users pick datasheets, persist with `useCloudStorage`.

## Official Workflow

- Self-built widgets are installed under the space's self-built mini-program area.
- Local development usually uses `widget-cli start`, which serves an HTTPS local bundle.
- Browsers may require manually allowing the local HTTPS certificate before 报表 can load the local bundle.
- Before `widget-cli start` or release, use the full `widget.config.json` shape: `packageId`, `spaceId`, `version`, `entry`, localized `name` and `description`, `icon`, `cover`, `authorName`, `authorIcon`, `authorLink`, `authorEmail`, and `sandbox`.
- `widget-cli start` fails with `TypeError: The "path" argument must be of type string. Received undefined` when `entry` is missing.
- The released package fails with `Code: 473` and `小程序发布失败，发布参数不完整` when required author/icon/cover metadata is missing.
- The CLI may auto-increment the released version. After release, run `widget-cli list-release <packageId>` and align local `package.json`, `package-lock.json`, and `widget.config.json` with the package details version.
- `packageId` must be `wpk` plus exactly 10 English letters or digits. Longer values fail late with `Package ID format error`. The starter ships with placeholder `wpkReplace001` — REPLACE it with a unique value BEFORE first release (see G1).
- On first release of a new widget package, `widget-cli release --ci` SKIPS the `Release a new widget with Id ... Y/n?` prompt by default, which silently skips create-package. Always run `npm run release:confirm` (which pipes `Y\n`) for the first release of a packageId, and verify by grepping for `Successful create widgetPackage from server` in the output. See G1.
- Before release, provide a 64x64 PNG icon and a 16:9 cover image. Reuse the icon for `authorIcon` if no author avatar is available.
- Non-public deployments can publish with `widget-cli release --host <host> --uploadHost <host>`.
- Use `npm run release`; the template release script reads the host from `EBIAOBIAO_HOST`.
- A self-built widget can only be published/updated by the creator account unless ownership is transferred by the creator or space admin.
- Pin `@apitable/widget-sdk@1.10.1`, `@apitable/widget-cli@1.3.0`, and React/ReactDOM `18.2.0`. Newer React currently causes peer dependency conflicts with the official SDK.
- With `sandbox: false` the CLI prefixes every CSS class with the packageId (see G2). Either set `sandbox: true` (no prefix; recommended), or use CSS Modules (`import styles from './style.css'` + `className={styles.app}`) or `:global(...)` selectors. Do NOT mix `sandbox: false` with plain `import './style.css'` + `className="app"`.
- Embedded windows clip the widget iframe instead of scrolling the page. The two viable patterns:
  1. Sandbox=true / panel widgets: use `min-height: 100%` (NOT `100vh`), let `body` scroll naturally (`overflow-y: auto`), use `position: sticky; bottom: 0;` for action bars (see G3).
  2. Sandbox=false / embedded full-iframe: set `html`, `body`, and `#root` to `height: 100%; overflow: hidden`, then make the top-level app container `height: 100vh; overflow: auto; -webkit-overflow-scrolling: touch`.
  Do not mix the two patterns or rely on page/body scrolling outside the iframe.

## SDK Patterns

- Use `useDatasheet`, `useFields`, `useViewsMeta`, `useActiveViewId`, `useRecords`, `useRecord`, `useSelection`, `useCloudStorage`, `useSession`, and `useViewport`.
- Use `FieldPicker` and `ViewPicker` for field/view binding instead of hand-typed IDs in user UI.
- Use field IDs for mutation maps.
- Avoid writing `isComputed` fields.
- Always check permissions before mutation and show an actionable error.

## Responsive Acceptance

Check all of these before handoff:

- 390px width: single-column controls, no clipped labels, action bar reachable.
- 390px narrow embedded window: vertical scrolling works inside the widget, and wide preview tables can be swiped horizontally.
- 768px width: two-column layout where useful, preview table horizontally scrolls inside its own container instead of overflowing or clipping.
- 1440px width: tool is dense and scan-friendly, not stretched into a marketing page.
- Embedded window: supports dynamic height/width changes without hiding primary actions.
- Dark theme or host theme variables do not break contrast.

## Release Checklist

- No API token in source or bundle.
- `widget.config.json` `packageId` is a UNIQUE `wpk[A-Za-z0-9]{10}` value — NOT the starter placeholder `wpkReplace001` (G1).
- `widget.config.json` `sandbox` matches the CSS strategy in use — `true` for plain `import './style.css'`, `false` only with CSS Modules / `:global(...)` (G2).
- `widget.config.json` includes `entry`, `version`, package ID, localized metadata, icon, cover, and author metadata.
- `package_icon.png` exists.
- `cover.png` exists.
- No `min-height: 100vh` or `overflow: hidden` on root containers (G3).
- Local preview verified inside 报表.
- Release command targets the configured host.
- First release of a packageId: use `npm run release:confirm`, then grep output for `Successful create widgetPackage from server`. If that line is absent the package was NOT registered, regardless of any `successful release` output (G1).
- Subsequent releases of an already-registered packageId can use `npm run release`.
- After release, `widget-cli list-release <packageId>` may show package details as `Online` and still fail the release-history section with `Code: 221 参数有误`; treat the package details status as the reliable signal.
- If Browser cannot attach to an authenticated 报表 window, still run build, bundle scoped-class checks, package status checks, and static viewport screenshots as fallback evidence.
- Non-developer mode install verified from widget center when possible — confirms create-package actually ran (G1).

## Live Smoke Lessons

- A hand-written minimal widget config is not enough for the CLI. Use the full standard config or initialize through `widget-cli init`.
- If the rendered widget looks like unstyled HTML, inspect CSS Modules first. The fix is to import the CSS module object and use exported class names in JSX.
- The CLI can create the widget package and upload bundle/assets, then fail only at the final release step. Check server error codes before changing app code.
- `Code: 473` was fixed by adding complete author metadata and cover/author icon paths.
- `list-release` returning package status `Online` confirms the package is published even if the history sub-query returns `Code: 221`.
- A published smoke version verified scoped CSS in `widget_bundle.min.js` (`wpk...app`, `wpk...hero`, `linear-gradient`, `overscroll-behavior`) and static 390/768/1440 screenshots plus a 390x520 fixed-height scroll check.
- If bottom content is clipped and cannot be reached, the root scroll container is wrong. Move scrolling to the widget `.app` container and keep body/root overflow hidden; verify with a short fixed-height viewport, not only full-page screenshots.
- For operational dashboard widgets, filter out empty smoke-test records before computing metrics. Fusion/API tests can leave blank records that make a polished widget look broken.
- For select updates, prefer resolving option IDs from `useFields(viewId).property.options` at runtime; fall back to option names only when the field options cannot be read.
- WordDeck release: `npm run release` with placeholder `wpkReplace001` printed `successful release` but the widget never appeared in the space — bundle was uploaded, package was never registered. Required setting a unique `wpkWdMaiMai01` and switching to `release:confirm`. The `Successful create widgetPackage from server` log line is the only reliable confirmation (G1).
- WordDeck CSS regression: with `sandbox: false`, source class `.phone-frame` was rewritten to `.wpkWdMaiMai01phone-frame` in the bundle but JSX still used `className="phone-frame"`. Widget rendered unstyled. Switching to `sandbox: true` fixed it without touching JSX (G2).
- WordDeck panel clipping: `min-height: 100vh` + `overflow: hidden` made the bottom tab bar unreachable in the right-side panel iframe. Replaced with `min-height: 100%`, `body { overflow-y: auto }`, and `position: sticky; bottom: 0;` for the tab bar (G3).
- WordDeck Playwright auth: `!url.includes('/login')` returned true on the external SSO `qrConnect` URL and the script raced past the QR scan. Fix is to gate on the configured host (from `EBIAOBIAO_HOST`) AND exclude `qrConnect` and `/sso/` (G4).
- WordDeck dstId injection: `window.WORDDECK_DSTIDS` from the host page never reached the iframe. v0.1 hardcoded IDs in `dst-config.ts`; v1.0 should use `useSettingsButton` + `useFields` (G5).
