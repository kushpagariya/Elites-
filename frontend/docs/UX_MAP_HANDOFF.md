# Workspace UX and real-map handoff

## Completed

- Explore: dot-only surface replaced by interactive MapLibre/OpenFreeMap Positron streets and neighbourhoods, purple candidates, black stores, selection details, fit/reset, zoom/pan, legend, attribution and loading/error/retry states. Shortlist, side-by-side comparison, DaypartDNA and detailed financial table share the existing context.
- Test Changes: compact primary inputs and advanced assumptions; Today / Project Opens / Project Delayed; saved before/after results, business-language FailFast and threshold actions. Existing immutable scenario and evaluation semantics retained.
- Investment Plan: financial outcomes and selected locations first, allocation meter and map, natural risk review and store limit, saved report/export controls and expandable solver details.
- Landing page, routes, APIs and financial algorithms are unchanged. No new dependencies or application fixture mode.

## Changed files

- src/app/(workspace)/workspace.css: workspace-only design system and responsive layouts.
- src/components/WorkspaceShell.tsx, StatusBadge.tsx: navigation/context and readable risk labels.
- src/features/explore/{Explore,LocationMap,DaypartSelector,InvestmentCard}.tsx: map-first discovery and comparison.
- src/features/scenarios/Scenarios.tsx and src/features/portfolio/Portfolio.tsx: simplified task screens.
- src/lib/{workspace,types,presentation,map-data}.ts(x): shared focus/period UI state, optional infrastructure geometry, formatting and geometry validation.
- tests/analytical-ui.test.cjs, tests/presentation.test.cjs: focused rendering/state-presentation/geometry checks.
- tests/map-preview-server.cjs: isolated test-only source inputs for map review; returns no financial results. Never imported by the application.
- DESIGN.md and this handoff.

## Provider and data limitations

Provider: MapLibre GL JS + OpenFreeMap Positron. Official setup: https://openfreemap.org/quick_start/ . Style: https://tiles.openfreemap.org/styles/positron . Verified HTTP 200 JSON and rendered real roads/place labels. Native provider/source attribution remains visible. No API key or bulk tile download; online access is required and no offline map is bundled.

Demo candidates, branches and infrastructure remain labelled synthetic/hypothetical. A real basemap does not make these observed businesses. POI/catchment/daypart layers consume matching evaluation geographic context only; these analytical overlays have not been verified against a live integrated computation in this increment. Observed competitor inventory is absent, so its layer remains disabled. No routes, catchments, financial outputs or opportunity values are invented in React.

## Compatibility and dependencies

Only additive optional frontend InfrastructureEvent fields were introduced: type and geometry (GeoJSON Point, LineString or Polygon). Missing geometry leaves projects in the evidence list without a geographic overlay. No HTTP paths, required payload fields or backend schemas changed. Backend owns the canonical contract/OpenAPI and any future geometry producer.

TODO: needs backend — provide matching completed evaluation, ranking, six-period DaypartDNA, geographic context, verified rescue result, saved portfolio run and report export through existing adapters.
TODO: needs backend — supply source-labelled competitor inventory/geometry before enabling competition overlays; retain exact saved identities for all analytical layers.
TODO: needs ML — integrate only an approved model artifact with compatible feature schema, otherwise retain explicit assumption mode. No prediction accuracy claims were added.

## Commands and actual results

The installed pnpm CLI was invoked through Node at C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs.

- node --test frontend/tests/analytical-ui.test.cjs frontend/tests/presentation.test.cjs: 8 passed, 0 failed (targeted checks).
- pnpm --dir frontend typecheck: route generation passed; initially failed on one nullable before/after scenario reference. The reference was fixed; no standalone typecheck rerun.
- pnpm --dir frontend build: passed compilation, full TypeScript validation and all six static pages. This verified the nullable fix.
- pnpm dlx prettier@3.6.2 --write [changed source/test paths]: completed; no dependency changes.
- Taste inspect.mjs --app http://127.0.0.1:3002/app --widths 1440,768,390 --allow palette-purple,palette-cream --out [visualization folder]/storescout-workspace --json: final zero failures, no page overflow, no console errors. One compact-secondary-text warning remains (minimum 11px). Separate phone reviews of scenarios/portfolio also had no failures/overflow/console errors. Disabled-label contrast warnings were subsequently corrected; contrast measured 5.92:1.
- Focused browser checks: actual streets/labels, candidate selection synchronized with comparison, fit selection, zoom, pan, reset, three routes, demand input/unsaved state, infrastructure selection and disabled export/plan actions without saved evaluation. No financial submission or final end-to-end acceptance test.
- Production chunk search for test server 8400 / Map preview: zero matches.
- git diff --check: passed (only repository line-ending notices).

The isolated preview used tests/map-preview-server.cjs on 8400 and a temporary Next server on 3002. It read canonical labelled demo inputs, supplied a neutral synthetic baseline, and returned HTTP 501 for analytical requests. It was solely a UI/map verification tool; these are not computed financial results. Temporary preview servers were stopped; existing user servers on 3000/8000 were left intact.

## Design skills used

Loaded and applied the installed design-taste-frontend, impeccable and emil-design-eng SKILL.md instructions. Continued the existing Framed sheet direction; applied map-first hierarchy, progressive disclosure, simple business copy, responsive/focus states and reduced-motion behavior. Screenshots were opened for visual review; no generated geographic imagery was used.

## Next integration steps

1. Restart the frontend from this checkout with pnpm dev; default API remains http://127.0.0.1:8000/api/v1. Do not point the normal app at the test input server.
2. Backend supplies the above existing contracts with matching saved identities; frontend checks one completed evaluation across map, comparison, scenario and plan.
3. ML verifies artifact/schema compatibility and evidence labels; assumption mode remains explicit until then.
4. After integration, exercise risk acknowledgement, empty/partial portfolios, rescue preserving unrelated failures, report reopening and rapid scenario switching. Final end-to-end financial/ML acceptance remains deferred.
