# Widget Development Reference

## Official Workflow

- Self-built widgets are installed under the space's self-built mini-program area.
- Local development usually uses `widget-cli start`, which serves an HTTPS local bundle.
- Browsers may require manually allowing the local HTTPS certificate before 报表 can load the local bundle.
- Before `widget-cli start` or release, use the full `widget.config.json` shape: `packageId`, `spaceId`, `version`, `entry`, localized `name` and `description`, `icon`, `cover`, `authorName`, `authorIcon`, `authorLink`, `authorEmail`, and `sandbox`.
- `widget-cli start` fails with `TypeError: The "path" argument must be of type string. Received undefined` when `entry` is missing.
- The released package fails with `Code: 473` and `小程序发布失败，发布参数不完整` when required author/icon/cover metadata is missing.
- The CLI may auto-increment the released version. After release, run `widget-cli list-release <packageId>` and align local `package.json`, `package-lock.json`, and `widget.config.json` with the package details version.
- `packageId` must be `wpk` plus exactly 10 English letters or digits. Longer values fail late with `Package ID format error`; use a valid placeholder and replace it before release.
- On first release of a new widget package, `widget-cli release --ci` may still prompt `Release a new widget with Id ... Y/n?`. In automation, pipe an explicit `Y` for new packages and keep the release log.
- Before release, provide a 64x64 PNG icon and a 16:9 cover image. Reuse the icon for `authorIcon` if no author avatar is available.
- Non-public deployments can publish with `widget-cli release --host <host> --uploadHost <host>`.
- Use `npm run release`; the template release script reads the host from `EBIAOBIAO_HOST`.
- A self-built widget can only be published/updated by the creator account unless ownership is transferred by the creator or space admin.
- Pin `@apitable/widget-sdk@1.10.1`, `@apitable/widget-cli@1.3.0`, and React/ReactDOM `18.2.0`. Newer React currently causes peer dependency conflicts with the official SDK.
- The CLI enables CSS Modules for `.css` imports. Do not use `import './style.css'` with plain `className="app"`; styles will compile but not match the DOM. Use `import styles from './style.css'` and `className={styles.app}`, or wrap selectors in `:global(...)`.
- Embedded windows may clip the widget iframe instead of scrolling the page. Set `html`, `body`, and `#root` to `height: 100%; overflow: hidden`, then make the top-level app container `height: 100vh; overflow: auto; -webkit-overflow-scrolling: touch`. Do not rely on page/body scrolling.

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
- `widget.config.json` includes `entry`, `version`, package ID, localized metadata, icon, cover, and author metadata.
- `package_icon.png` exists.
- `cover.png` exists.
- Local preview verified inside 报表.
- Release command targets the configured host.
- After release, `widget-cli list-release <packageId>` may show package details as `Online` and still fail the release-history section with `Code: 221 参数有误`; treat the package details status as the reliable signal.
- If Browser cannot attach to an authenticated 报表 window, still run build, bundle scoped-class checks, package status checks, and static viewport screenshots as fallback evidence.
- Non-developer mode install verified from widget center when possible.

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
