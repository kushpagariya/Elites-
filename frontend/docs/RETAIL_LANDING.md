# StoreScout retail landing

Scope: marketing landing only. `frontend/DESIGN.md` continues to govern the analytical workspace.

## Direction and tokens

A local retail street: brick storefronts, striped awnings, warm windows and a floating SALE sign make the expansion story tangible. The scene is illustrative, not geographic or analytical evidence.

| Token | Value | Use |
| --- | --- | --- |
| Paper | `#f5f0e6` | Marketing background |
| Ink | `#203c32` | Text, capability strip, dark sections |
| Accent | `#a83d24` | Headline emphasis and actions; existing CSS token `--purple` |
| Font | Manrope Variable, sans-serif | Marketing headings and body |

The desktop hero uses two columns with an oversized street illustration. At 1024px it stacks; at 600px the scene is 340px high and the capability strip uses two columns. The hero title scales from 48px to 80px. Use the shared storefront/location mark and native links.

## Scene and accessibility

`City.tsx` builds geometry locally with Three.js primitives and creates sign textures with canvas. No downloaded models, photos or remote textures are required. Warm directional lighting and restrained pointer response support the storefront forms.

`RetailBackdrop.tsx` supplies a static CSS street before readiness, for reduced motion, data saver, `?flat`, scene failure or WebGL context loss. Decorative scenery is hidden from assistive technology. The visible Pause/Resume motion button exposes `aria-pressed` and has a 44px minimum height.

The scene uses demand rendering when paused or offscreen; visibility tracking suspends animation in hidden tabs. Reduced-motion CSS also removes landing transitions and animations. Pixel ratio is capped at 1.5 and shadow maps at 1024px.

## Boundaries and verification

Preserve existing `/app/` links, section anchors, product routes, API contracts and backend financial calculations. Storefront names and SALE lettering are decoration; they must never become rankings, predictions or business claims.

Implementation-owner verification, run from `frontend/` on this change:

- `node node_modules/next/dist/bin/next build` — succeeded.
- `node node_modules/typescript/bin/tsc --noEmit` — succeeded.
- `node --test tests/*.test.cjs` — 23 passed.

Owner browser checks: no overflow or runtime exceptions at 1440/768/390px; canvas rendered; pause toggled `aria-pressed`; reduced motion rendered fallback without canvas; `/app` loaded. Existing analytics unavailable states remain preserved.

Baseline: `d694ef2`; changes remain uncommitted. These checks do not establish analytical correctness, measured performance or complete accessibility acceptance.

## Scroll narrative refinement

The shared BrandMark is now a restrained storefront inside a location outline, used on the landing page and workspace. Marketing retains forest ink, cream, brick accents and muted brass.

Three lightweight CSS 3D shop scenes respond to scroll and fine-pointer movement. A global Pause/Resume control freezes decoration; reduced motion and data saver keep a static presentation. Links and buttons have press feedback, navigation has underline feedback, and pointer clicks produce a brief ring. A top line tracks reading progress.

The risk and financial sections now explain rent, competition, network overlap, store economics, scenarios and portfolio planning through working selectors. Diagnoses and financial outputs still require saved evaluations. The neighbourhood graph reuses the existing labelled synthetic scores; the panel and footer also identify it as illustrative. Map pins support keyboard selection, infrastructure selectors expose pressed state, and the delay illustration uses 24 months.

Checks at 1440, 768 and 390px: no horizontal overflow or runtime exceptions; eight additional shop objects; risk/planning selectors change content; pause works; reduced motion shows the static hero. All 23 existing frontend tests pass. Visual evidence is in docs/retail-review-v2/. Source changes remain uncommitted on baseline d694ef2.


## Expansion pass and varied imagery

The hero now uses the user-supplied Lanyard component, adapted into a matte cream StoreScout expansion pass with a forest strap and brass hardware. It mounts anew on refresh, drops from above, supports pointer drag/flip and freezes on global pause or offscreen/hidden state. Reduced motion, data saver, the flat override and WebGL failure render a branded static pass. Canvas interaction is decorative; the primary navigation and actions remain native links.

The single 3D neighbourhood model now appears in the process section. Due diligence and portfolio sections use two distinct generated editorial assets, with a brand seal at the final call to action. See LANDING_ASSETS.md for files, source and exact generation prompts. Images have descriptive alternative text, responsive sizing, lazy loading and explicit concept captions.

Navigation uses pill fill/label-rollover feedback, active-section dots and a compact mobile disclosure. Escape and outside clicks close it. The visual system remains cream, forest, terracotta and brass. Evidence is in docs/retail-review-v3/; source changes remain uncommitted.

Final verification: production build (including TypeScript) passed; existing frontend test suite passed 23/23; desktop/tablet/phone checks found no horizontal overflow or runtime exceptions, generated images loaded, mobile navigation opened and closed with Escape, global pause worked, and reduced motion used a static pass. The intro now waits for its textures to avoid a blank card/loading overlap. Final source baseline is d694ef2 with uncommitted changes.
