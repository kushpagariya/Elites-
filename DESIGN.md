---
name: StoreScout
description: Retail expansion decisions with traceable assumptions
colors:
  paper: "#f7f7f4"
  ink: "#18181b"
  muted: "#62616a"
  purple: "#7244e5"
  purple-hover: "#6031cf"
  tint: "#e9e1f8"
  surface: "#eeede9"
  white: "#ffffff"
  border: "#dfded8"
typography:
  display:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "clamp(48px, 6vw, 84px)"
    fontWeight: 550
    lineHeight: 1.05
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "clamp(34px, 4.2vw, 56px)"
    fontWeight: 550
    lineHeight: 1.05
  body:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "16px"
    lineHeight: 1.6
spacing:
  page: "clamp(24px, 5vw, 80px)"
  mobile-page: "20px"
components:
  button-primary:
    backgroundColor: "{colors.purple}"
    textColor: "{colors.white}"
    padding: "16px 28px"
  button-primary-hover:
    backgroundColor: "{colors.purple-hover}"
---

# Design System: StoreScout

## Overview

**Creative North Star: “The Retail Atlas.”** This describes the existing landing page rather than a new brand direction. A quiet paper surface, precise black typography and a purple hexagonal city explain location, time, risk and investment choices. Preserve this identity when extending the product.

The landing page persuades and explains; the workspace supports repeated decisions. Share palette, type and controls, but use compact headings and readable tables in the workspace. Do not copy full-screen marketing compositions into analytical modules.

Extracted from the former frontend/landing_page/storescout implementation. Current sources are frontend/src/features/landing and frontend/src/app/(marketing)/landing.css. Historical screenshots and review notes live in frontend/docs/landing-reference; they describe an earlier build and are not current verification evidence.

## Colors

Purple is the primary action and selection color. Paper, ink, white and a small tonal step establish hierarchy. Use muted ink for secondary explanations, never disabled-looking financial values. Tint supports selection without competing with the city.

Shared CSS tokens live in frontend/src/app/base.css. The landing stylesheet retains local tokens; the Three.js scene uses features/landing/motion.ts. When a brand value changes, update these consumers together. Scene-only lavender (#c6b5ef) and ground (#e9e8e5) are illustrative materials, not financial statuses.

Status always includes text: VIABLE, AT_RISK, REJECTED or REVIEW_REQUIRED. A color or dot alone is insufficient. Maintain 4.5:1 contrast for body text and 3:1 for large text and meaningful controls. Do not infer that every historical label already passes contrast.

## Typography

Self-host Manrope Variable through the installed font package; keep a sans-serif fallback. The observed landing scale is recorded in frontmatter. Section headings use the headline role; h3 uses clamp(20px, 2.2vw, 28px), weight 600. The compact workspace starts with 28px h1, 18px h2 and 16px body text.

Use tabular figures for financial comparisons. Keep units in labels: INR, INR/month, years, square metres. Format decimal fractions as percentages only for display. Preserve null with its explanation; never format it as zero. Avoid tiny uppercase labels in new modules; historical illustration annotations are not a pattern for operational UI.

## Layout

One Next.js application, one frontend/package.json and one pnpm lockfile:

- /: src/app/(marketing)/page.tsx renders features/landing/Landing.
- /app: src/app/(workspace)/app/page.tsx renders the existing API connectivity screen.
- Future /app/scenarios and /app/portfolio routes belong under (workspace)/app.
- src/features/explore: candidate table, map, selection and comparison.
- src/features/scenarios: immutable assumptions, infrastructure and rescue workflow.
- src/features/portfolio: full-network selection and saved report views.
- src/components: shared controls once reused by more than one feature.
- src/lib/api.ts and types.ts: shared transport and contract mirrors; backend owns schema changes.

Route groups do not appear in URLs. Landing components must not import workspace internals. Route-specific CSS is nested under .landing and .workspace to prevent generic main, section, button and heading rules from leaking during client navigation. Shared base CSS contains only brand primitives and browser defaults. CSS nesting requires a modern browser supported by Next.js.

Landing breakpoints are 1024px and 768px; mobile uses 20px page margins and single-column content. The workspace uses a 1120px maximum frame, 24px side margins and 16px at 700px or below. Tables may scroll horizontally within their own region; preserve equivalent keyboard/table access to map information. New modules should retain these frames rather than inventing unrelated widths.

The landing narrative is opportunity → dayparts → conditional infrastructure → failure/rescue → portfolio → evidence → action. All primary calls to action open /app. Workspace branding links home. Navigation must remain functional without analytics.

## Elevation & Depth

Prefer flat surfaces and tonal separation. Reserve elevation for genuinely floating menus or dialogs. The hex city supplies the landing page's depth; do not add decorative glass, neon, gradients or glow around analytical controls. Existing borders inside interface diagrams do not justify boxed marketing sections everywhere.

## Shapes

The hexagon represents geographic opportunity and anchors the brand. Use it in the mark and explanatory city, not as a mask around every control. Buttons are rectangular; avoid introducing a separate rounded-card system. Use circles only for compact indicators, with accompanying text.

## Components

**Primary action:** purple fill, white text, 16px × 28px padding; hover uses purple-hover. Preserve visible 3px purple focus outlines with 4px offset. Use actual links for navigation and buttons for state changes. Operational controls should have at least 44px touch targets.

**Secondary action:** transparent surface, existing border and readable label. Keep pressed, focus, disabled and pending states explicit. Inputs require a visible label and units; range controls need a readable current value and keyboard operation.

**Data surfaces:** candidate tables and comparisons render backend results. Show loading, empty, unavailable, validation error, request failure and stale states separately. Keep the last successful values during refresh only with a stale notice. Disable portfolio/export when the matching saved evaluation is missing.

**Source and identity:** persist SYNTHETIC, ASSUMED and REAL labels through screens and exports. Keep project_id, scenario_id, evaluation_id, source snapshot and model identity together in one active context. Cancel superseded requests and reject late responses by request token and identity. Never combine a new scenario with old rankings or portfolio values.

**Feature communication:** share the active evaluation context at the workspace boundary when analytical modules are implemented; do not maintain independent copies in each panel. Save the complete assumption snapshot before evaluation. Portfolio consumes evaluation_id, not browser-summed NPVs. Rescue creates a new scenario; it does not mutate baseline. Use docs/CONTRACT.md and backend OpenAPI rather than inventing payloads or endpoint semantics. A future provider is an integration seam, not an already implemented feature.

**Motion:** current tokens in features/landing/motion.ts are press 160ms, reveal 500ms, fade 200ms, stagger 60ms and ease cubic-bezier(0.23, 1, 0.32, 1). Keep repeated workspace feedback around 150–250ms and interruptible. Prefer transform and opacity; do not animate layout. Gate hover movement to fine pointers. Respect reduced motion in CSS and scene code; retain a static, no-WebGL alternative and all explanatory text. Do not block actions behind animation.

## Do's and Don'ts

- Preserve the paper/ink/purple identity, Manrope and subject-specific hex geometry. Existing palette and reference design take precedence over generic skill palette bans.
- Separate marketing examples from actual project evidence. Daypart drawings are illustrative, not measured footfall or model predictions; their synthetic scores are not product analytics.
- Never calculate revenue, NPV, ROI, payback, rescue thresholds or investment rankings in React. The imported sample financial calculator and hardcoded rescue results were replaced with unavailable states for this reason.
- Do not claim the three analytical screens, trained-model outputs, report export or full PRD acceptance are implemented by this folder consolidation. The workspace remains a connection diagnostic.
- Keep mandatory F01–F08 and H4 dependencies ahead of P1/P2 expansion. Do not alter backend contracts without integration-owner agreement.
- Verify / → /app → / navigation, backend success/failure, keyboard focus, reduced motion and 390/768/1440px layouts after interface changes. Build success does not prove analytics or visual acceptance.

| Before | After | Why |
| --- | --- | --- |
| Two Next apps; demo CTA ends at placeholder | One app; CTA opens existing connection screen | Future modules share routes and transport |
| Browser-calculated finance and canned rescue results | Explicit pending state | Preserve backend ownership and truthful output |
| Competing global styles | Shared base plus scoped marketing/workspace rules | Prevent navigation-dependent styling |
