# App Shell Layout — reference for 报表/apitable widgets

The single layout pattern that works inside apitable's widget iframes. Every widget should use this from day one. WordDeck went through 5+ release cycles fighting the symptoms before this was nailed down.

## The bug it solves

Two recurring failure modes the user has reported repeatedly:

**Mode A — short content (UI almost empty):**
The bottom tab bar (or page action bar) appears IN THE MIDDLE of the visible widget area, with a large blank gap below it.

**Mode B — long content (UI bigger than viewport):**
Content at the bottom of a page is clipped or sits below the visible area, and the user cannot scroll to reach it (e.g. a leaderboard / 排行榜 section below the fold on a Stats page).

Both symptoms are the SAME underlying bug: the scroll viewport and the visible iframe area don't match, so:
- "Bottom" (where sticky elements stick / where the tab bar is positioned by `margin-top: auto`) is the WRAPPER's bottom, not the iframe-visible bottom.
- The element that has `overflow-y: auto` is not the actual visible content area, so dragging on the visible content doesn't scroll the right thing — and content that does exist past the visible bottom is unreachable.

The apitable host wrapper is a `position: absolute` element with `overflow: hidden` at a host-controlled height. The widget sits inside that, and any attempt to rely on body / document / viewport scroll fails.

## The fix — App Shell pattern

A single flex column that exactly fills the iframe, with one scrolling middle and chrome (tabs / action bars) pinned to the column ends by flex flow.

This is the same pattern Slack, Gmail, Linear, Discord and every other "chrome + content + chrome" web/Electron app uses. The Apitable-specific gotchas are folded into the rules below.

### Root rules (always)

```css
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }

/* Lock the document to the iframe — body scroll does NOT work here. */
html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* #root is the flex column that exactly fills the iframe area. */
#root {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

### Wrapper chain (any intermediate wrappers)

If you have wrapper components between `#root` and the scrolling middle (e.g. a `PhoneFrame` that centers content on desktop), every wrapper must propagate the flex column AND allow children to shrink:

```css
.phone-frame, .phone-screen {
  display: flex;
  flex-direction: column;
  flex: 1;            /* fill parent */
  min-height: 0;      /* CRITICAL — see Gotcha 2 below */
  overflow: hidden;
}
```

### The single scroll viewport

ONE element scrolls. Typically named `.page-area`, `.content`, or `.scroll-area`:

```css
.page-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

/* Pages inside .page-area are normal blocks — let content size naturally.
 * Do NOT add flex: 1 here; the scrolling parent decides what's visible. */
.page-area > * {
  width: 100%;
  min-height: 0;
}
```

### Chrome (tabs, action bars, headers, footers)

Chrome elements live as flex siblings of `.page-area` inside the column. They use `flex-shrink: 0` so they're always at their natural height. **NEVER use `position: sticky` or `position: fixed` for these.**

```css
.tabs, .action-bar, .toolbar, .app-header {
  flex-shrink: 0;
  /* + your visual styles (background, border, padding, etc.) */
}
```

The DOM order inside `.phone-screen` (or equivalent) determines top vs bottom:

```html
<div id="root">
  <div class="phone-frame">
    <div class="phone-screen">
      <!-- Optional header: top of column, natural height -->
      <header class="app-header">...</header>

      <!-- The scrolling middle: takes all remaining space -->
      <main class="page-area">
        <!-- current page renders here -->
      </main>

      <!-- Bottom chrome: natural height, pinned at column bottom -->
      <nav class="tabs">...</nav>
    </div>
  </div>
</div>
```

### Sub-pattern — a page with its own bottom action bar

Some pages have their own bottom-pinned controls separate from the global tab bar — e.g. a Detail / Reveal page with rating buttons, or a Form page with a submit bar. These follow the SAME pattern scoped to the page:

```css
.detail-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;        /* exactly fill the parent .page-area */
  overflow: hidden;
}
.detail-hero    { flex-shrink: 0; }
.detail-body    {
  flex: 1; min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.detail-actions { flex-shrink: 0; /* submit / rating buttons */ }
```

When this sub-pattern is active, the OUTER `.page-area` no longer scrolls for this page — `.detail-body` does. That's fine: `height: 100%` makes `.detail-page` exactly fit `.page-area`, so the outer scroll has nothing to scroll.

Real example (worddeck Reveal page):
```html
<main class="page-area">
  <div class="reveal good">
    <header class="r-hero">…word, IPA, badge…</header>
    <section class="r-body">…meanings, examples, etymology (scrolls)…</section>
    <footer class="r-rate">…3 rating buttons (pinned at bottom)…</footer>
  </div>
</main>
```

## The 4 CSS gotchas

These are the specific traps that have caused recurring bugs. Memorize them.

### Gotcha 1 — Apitable's host wrapper has `overflow: hidden` at a host-controlled height

You don't control the iframe's `height`. The host does. Your widget must fit whatever it gets — panel (~280px wide × ~500px tall), expanded (~600 × 900), or fullscreen (~1080+).

**Implication:** `100vh`, `100dvh`, `window.innerHeight`, and "scroll the body" all give you the host page's viewport, not your widget's iframe. They do NOT work.

**Right answer:** `height: 100%` against your widget's wrapper chain, which is itself sized by the host iframe.

### Gotcha 2 — `flex: 1` alone is not enough; need `min-height: 0`

This is the most common silent breakage. Inside a flex column, a child with `flex: 1` resolves to `flex: 1 1 auto`. The `auto` for the flex BASIS means "use the content's natural height as the minimum." A tall content child therefore inflates the parent past the viewport instead of being constrained by the scrolling middle.

**Right answer:** every flex child in the wrapper chain — including the scrolling middle — must set `min-height: 0`. This overrides `min-height: auto` and lets the parent's `flex: 1` actually shrink the child.

```css
/* WRONG — content overflows the column and you can't scroll */
.wrapper { display: flex; flex-direction: column; flex: 1; }

/* RIGHT — content constrained, scroll viewport works */
.wrapper { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }
```

### Gotcha 3 — `position: sticky` is unreliable in apitable widgets

Sticky sticks to the nearest SCROLLING ancestor. Inside an apitable iframe several wrappers deep, with `overflow: hidden` on intermediate elements, sticky frequently sticks to the wrong place — usually the host wrapper's bottom, not the iframe-visible bottom. The element appears in the middle of the visible area instead of pinned to the bottom.

`position: fixed` is worse — fixed elements are positioned relative to the viewport (which is the host page, not your widget), so the element can fly outside the iframe entirely.

**Right answer:** never use `sticky` / `fixed` for chrome elements. Use flex layout (this whole file).

### Gotcha 4 — `min-height: 100vh` is wrong inside the widget

`vh` is the host PAGE's viewport unit, not your widget's iframe. A panel widget at 280×500 with `min-height: 100vh` (assuming the host page is 1080px tall) gives the widget a 1080px tall content that overflows the 500px iframe by 580px — exactly the "content clipped at bottom" bug.

**Right answer:** `height: 100%` (or `min-height: 100%`) against the apitable wrapper. Optional: use `100vh` only for explicitly expand/fullscreen-only chrome that has guards.

## Mobile viewport — the "blank area below tabs" host limitation

### What the user sees

On a mobile phone (iPhone, Android), the widget renders correctly: `#root` exactly fills its iframe, `.tabs` sits flush at the iframe's bottom edge. **But the iframe itself is shorter than the device viewport.** Below the iframe boundary is empty apitable host UI (page header, watermark, footer chrome). The visual effect: tabs appear in the middle of the screen with blank host space below.

This is **NOT a widget CSS bug** — `#root: height: 100%` correctly fills the iframe area. The iframe is host-sized.

### Why it happens

The apitable host on mobile embeds widgets in iframes sized by host layout rules, not the device viewport. The host page has:

1. A top navigation / breadcrumb bar
2. The widget iframe (host-sized — often ~60-70% of the visible area)
3. Page footer / watermarks below the iframe

There is no public API to make the iframe fill the device viewport in non-fullscreen mode.

### What you can try (WordDeck v0.4.0 attempted, in order of effectiveness)

**1. Auto-trigger fullscreen on mobile (RECOMMENDED — works on hosts that support it).**

```ts
import { useViewport } from '@apitable/widget-sdk';

function useAutoFullscreenOnMobile() {
  const { isFullscreen, toggleFullscreen } = useViewport();
  const triedRef = useRef(false);
  useEffect(() => {
    if (triedRef.current) return;
    triedRef.current = true;
    if (sessionStorage.getItem('autofs-tried') === '1') return; // one-shot
    if (window.innerWidth > 480) return;                         // mobile only
    if (isFullscreen) return;
    try {
      toggleFullscreen(true);
      sessionStorage.setItem('autofs-tried', '1');
    } catch {}
  }, []);
}
```

When fullscreen is active, the apitable host gives the widget the full device viewport. Make this one-shot per page load (sessionStorage) so the user can explicitly exit fullscreen without your code re-toggling it.

**2. Promote `#root` to `100dvh` when fullscreen is active.**

```ts
useEffect(() => {
  const root = document.getElementById('root');
  if (!root) return;
  root.style.height = isFullscreen ? '100dvh' : '100%';
  if (!CSS.supports('height: 100dvh')) root.style.height = isFullscreen ? '100vh' : '100%';
}, [isFullscreen]);
```

`100dvh` accounts for mobile Safari's URL bar collapsing. `100vh` is the safari < 15.4 fallback.

**3. postMessage resize nudge (mostly cosmetic — most hosts ignore it).**

```ts
window.parent.postMessage({ type: 'resize', height: window.innerHeight }, '*');
```

Some bespoke embed wrappers listen for this. Public apitable hosts do not. Cheap to try, fine to leave in.

**4. Visual transition — soften the iframe boundary.**

```css
.tabs {
  box-shadow: inset 0 -24px 0 0 rgba(238, 242, 255, 0.6);
}
```

A subtle gradient or solid block at the tabs' bottom edge makes the boundary between widget and host less abrupt even when the iframe doesn't fill the screen.

**5. Provide a "全屏" affordance.**

A floating top-right chip that calls `toggleFullscreen()` lets the user opt into fullscreen if auto-trigger didn't take, or if they previously exited.

```tsx
function FullscreenChip() {
  const { isFullscreen, toggleFullscreen } = useViewport();
  return (
    <button onClick={() => toggleFullscreen()}>
      {isFullscreen ? '⤡ 退出' : '⤢ 全屏'}
    </button>
  );
}
```

### The documented limitation

> **On mobile, apitable embeds widgets in iframes sized by the host page. Even in fullscreen mode the iframe may not fill the entire device viewport on every host. The best UX is to:**
>
> 1. Auto-trigger fullscreen on first mobile load (with a sessionStorage guard so it doesn't loop).
> 2. Provide a visible 全屏 chip so users can re-trigger fullscreen at will.
> 3. Promote `#root` to `100dvh` while in fullscreen mode so the widget uses the full device viewport.
> 4. Visually soften the tabs' bottom boundary with a subtle gradient or shadow so the "blank area below tabs" is less jarring.
> 5. Accept that on hosts where fullscreen still doesn't fill the device viewport, the blank area exists and is **outside the widget's control**.

### Verification — quick mobile checklist

- [ ] Open the widget on a phone (or Chrome devtools mobile emulation @ 375×812).
- [ ] On first load, fullscreen should auto-toggle (sessionStorage flag prevents re-trigger).
- [ ] After exiting fullscreen, the chip should be visible top-right.
- [ ] Tabs should sit at the iframe's bottom in BOTH normal and fullscreen modes.
- [ ] In fullscreen mode, the widget should use the full device viewport (no host UI below tabs).

## Verification checklist

Run after every CSS / layout change:

- [ ] `grep -rn "position: sticky" src/` → no matches in chrome / tab / action-bar CSS
- [ ] `grep -rn "position: fixed" src/` → no matches for chrome (modals are fine)
- [ ] `grep -rn "100vh\|100dvh" src/` → no matches outside optional desktop-only chrome with guards
- [ ] `grep -rn "flex: 1 0 auto" src/` → no matches (use `flex: 1; min-height: 0`)
- [ ] `grep -rn "overflow-y: auto" src/components/*.css src/styles/*.css` → exactly ONE primary match (the scroll viewport)
- [ ] In dev, resize the widget panel to 3 sizes (panel ~280, expanded ~600, fullscreen ~1080). Tabs / action bars must be at the visible bottom in all sizes.
- [ ] Force content > viewport height. Page scrolls inside `.page-area` (or page's own scroll middle). Tabs stay at bottom, never scroll away.
- [ ] Force content < viewport height. Tabs still at bottom (no gap below).
- [ ] All sections of every page are reachable by scrolling (especially the LAST section, often a leaderboard / list).

## Headless smoke template

The WordDeck widget includes a static layout smoke test template that loads the actual CSS files and asserts:
- Tab / action-bar position equals the host wrapper's visible bottom
- `.page-area` (or page-specific scroll middle) is scrollable when content overflows
- Maximum scroll position equals `scrollHeight - clientHeight` (no content unreachable)

Files: `widgets/worddeck/tests/layout-smoke.html` (the static page) and `widgets/worddeck/tests/layout-smoke.mjs` (the headless Chromium driver). Copy them as a starting template for any new widget; replace the page CSS imports and content factories.

Run: `node tests/layout-smoke.mjs`. Exits 0 on all-pass.

## Quick-start CSS — copy this into a new widget

```css
/* styles/reset.css */
*, *::before, *::after { box-sizing: border-box; }
html, body, #root { margin: 0; padding: 0; }
html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
  -webkit-font-smoothing: antialiased;
  -webkit-tap-highlight-color: transparent;
}
#root {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

```css
/* components/AppShell.css */
.app-frame {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.app-screen {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}
.page-area {
  width: 100%;
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}
.page-area > * {
  width: 100%;
  min-height: 0;
}
.tabs, .action-bar {
  flex-shrink: 0;
}
```

```jsx
// App.tsx — DOM order matters: page-area above tabs
<div className="app-frame">
  <div className="app-screen">
    <main className="page-area">
      {/* current page */}
    </main>
    <nav className="tabs">{/* … */}</nav>
  </div>
</div>
```

That's the entire pattern. Use it from the first commit on every new widget.
