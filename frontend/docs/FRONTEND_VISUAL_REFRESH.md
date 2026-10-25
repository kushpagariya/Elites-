# Frontend visual refresh

The landing page and analytical workspace now share cream, forest and terracotta with Manrope. The landing has shorter headlines, larger body text, prominent actions, relevant retail illustrations and a clearer explore → test → plan sequence. Removed obsolete marketing CSS rather than retaining competing visual systems.

The workspace has a forest navigation rail, larger controls/results, warm panels and matching map colours. Route changes expand the current feature group and collapse previous groups, keeping phone navigation compact. Existing route links, section anchors and disclosure controls remain available.

## Charts and motion

- The illustrative landing chart uses direct labels and a shared 0–100 scale. Time-of-day and infrastructure controls update visible explanations. Its synthetic disclosure remains explicit.
- Saved analytical daypart profiles use horizontal bars and direct values for all six periods. Missing evidence remains distinct from zero.
- Annual cash flows are visible immediately below the two-location comparison. A common symmetric scale preserves positive/negative direction and relative magnitude. Compact INR labels fit phone screens; exact amounts remain accessible in labels and the expandable table. Browser calculations position bars only.
- Hero entrance, physical lanyard interaction, scroll depth and brief content transitions guide exploration. Native reduced-motion CSS, static scene fallbacks, a global pause control and offscreen suspension remain supported. Paused/static entrances render at full opacity.

## Verification

- `pnpm test`: 30 passing tests, including signed, zero, missing and unavailable cash-flow presentation.
- `pnpm build`: production compilation, TypeScript and all four routes pass.
- Taste source checks: zero failures for marketing and app scopes. Remaining warnings concern intentional control borders and existing analytical/overlay shadows. The standalone browser inspector was not run; visual review used the connected browser.
- Browser review at 1440×900, 768×1024 and 390×844: landing, charts, navigation and responsive composition checked; no page overflow after toolbar fixes. Workspace review included real local backend evaluation, two-site comparison, scenario editing surface and successful portfolio optimisation. Phone map cards use compact amounts with exact tooltips. Exact comparison tables scroll locally.
- Mobile menu, landing time/financial controls and pause/resume were exercised. Reduced-motion handling was inspected in source; OS preference emulation was not available through the connected browser.

Saved inputs, financial outputs, risk classifications, source labels, cancellation/stale-result guards and scenario/evaluation identities are preserved. No backend, dependency or API contract changes. The active engine remains assumption-based; this work makes no trained-ML or prediction-accuracy claim.

The committed desktop/phone hero captures are in `frontend/.impeccable/review/`. Follow the shared identity and boundaries in `frontend/DESIGN.md` and `frontend/PRODUCT.md` for subsequent changes.
