# StoreScout workspace design

This guide covers the shared identity of the landing page and /app, /app/scenarios and /app/portfolio. Product and financial semantics remain governed by the PRD and API contracts.

## Direction

Preserve the established retail identity: Manrope, cream #f5f0e6, forest #203c32 and terracotta #a83d24. The landing introduces the product with a two-line headline, a physical expansion pass, readable interactive charts and relevant due-diligence/network illustrations. The workspace continues this palette with a forest navigation rail, warm paper and clear result panels. Shared tokens live in base.css; scoped layouts and refresh styles live beneath their route groups. Risk states retain separate colours and text labels. No new dependencies or calculation changes.

## Three tasks

- **Explore Locations:** a real city map alongside a compact shortlist; focus a location, select exactly two for comparison, then read backend financial results. Keep the full financial table inside Detailed Comparison.
- **Test Changes:** budget, demand change, rental change and infrastructure first. Advanced Assumptions contains the supported base-rent and absolute reference-sales overrides and infrastructure timing. Fixed margins and OPEX remain dataset assumptions. Display before/after saved results and all remaining failure reasons. A rescue action creates an immutable scenario and requests evaluation.
- **Investment Plan:** show saved network value, investment, remaining budget and selected stores before solver details. Retain risk review, store-count cap, empty/partial/unavailable outcomes and backend-generated reports.

## Real map and evidence

Retain MapLibre GL JS with OpenFreeMap Positron: https://tiles.openfreemap.org/styles/positron. Streets and place names come from vector tiles; retain native OpenFreeMap, OpenMapTiles and OpenStreetMap attribution. No paid key, bulk download or offline cache is used. The local MapLibre worker is prepared by the existing build script.

Project coordinates place terracotta candidates and forest existing stores. Current demo locations remain explicitly SYNTHETIC; streets do not validate those businesses. Selection is shared with accessible cards and comparisons. Zoom, pan, fit selection and reset are available. Loading, WebGL and tile errors expose retry while the shortlist remains usable; no artificial geographic fallback is displayed.

POIs, catchments and DaypartDNA halos use only matching current backend evidence. Missing scores have no halo; supported zero is distinct from unknown. Infrastructure renders only supplied, validated Point/LineString/Polygon geometry and retains hypothetical/source labels. Mapped OSM competitor POIs have their own working toggle; their attraction is assumed. Changing the saved scenario or shared period refreshes supported analytical layers.

## Hierarchy and accessibility

Keep results prominent and IDs inside Data and analysis details / Technical Details. Use concise headings, labelled INR amounts, readable status text, visible focus, native labelled controls and local table scrolling. Primary DaypartDNA choices are Morning, Lunch, Evening and Weekend, with all six canonical periods in a disclosure. Identify it as POI-derived opportunity, never measured footfall.

Responsive grids collapse to one column on phones; comparison and map controls remain available. Marketing uses a short, already-visible hero entrance, restrained scroll depth and 200ms content transitions. Pause, reduced-motion and offscreen suspension remain available. The analytical app uses brief interaction feedback without entrance delays. Secondary labels have a 14px floor; primary text is 16–18px and phone inputs are 16px. Large direct values, horizontal daypart bars and a shared zero-centred cash-flow scale improve comparison. Exact cash flows remain in an accessible table. Unknown values are never drawn as zero.

## State and calculation boundaries

Formatting and percentage/multiplier input conversion are presentation only. Financial outputs, ranks, thresholds and network totals come from saved backend responses. Null is unknown, never zero. Preserve source/model/scenario/evaluation identities, request cancellation and incrementing response tokens. Edits mark derived results stale and disable portfolio/export until the matching completed evaluation arrives. Preserve prior successful values with a stale notice.

## Verification scope

The visual refresh passed 30 frontend tests and the production build with TypeScript. Browser review covered 1440px, 768px and 390px with no page overflow, including live local backend evaluation, two-site charts, scenario controls and portfolio optimisation. Taste source checks had zero failures; intentional control-border and analytical-shadow warnings remain. The standalone browser inspector was not run. See docs/FRONTEND_VISUAL_REFRESH.md for the exact scope and limitations. The delivered synthetic-trained CatBoost model is connected; real-store accuracy is unvalidated.

## Workspace feature navigation

Keep the three page links and pair each with a labelled expand/collapse button. The current page opens by default. Feature links point to existing heading anchors: Explore exposes rankings, DaypartDNA and comparison; Test Changes exposes the scenario builder, Future Infrastructure and FailFast; Investment Plan exposes Budget Optimisation and Investment Reports. Retain separate page/section active states, keyboard focus at the destination, browser history and delayed-content deep links. On phones, expanded links wrap beneath the three main page links. No new routes or backend behavior.
