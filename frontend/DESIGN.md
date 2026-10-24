# StoreScout workspace design

This guide covers only /app, /app/scenarios and /app/portfolio. The landing page, its components and shared base styles are unchanged. Product and financial semantics remain governed by the PRD and API contracts.

## Direction

Continue Taste's existing Framed sheet direction (seed 940076972; no redraw), Manrope typography and black/white/purple identity. Apply Impeccable's hierarchy, progressive disclosure and accessibility guidance, and Emil's restrained interactions. Workspace tokens and every visual override live in src/app/(workspace)/workspace.css beneath .workspace. Warm paper, flat white panels, charcoal text and purple actions support repeated analysis; risk states always have text labels.

## Three tasks

- **Explore Locations:** a real city map alongside a compact shortlist; focus a location, select exactly two for comparison, then read backend financial results. Keep the full financial table inside Detailed Comparison.
- **Test Changes:** budget, demand change, rental change and infrastructure first. Advanced Assumptions contains margin, operating costs, competition and location overrides. Display before/after saved results and all remaining failure reasons. A rescue action creates an immutable scenario and requests evaluation.
- **Investment Plan:** show saved network value, investment, remaining budget and selected stores before solver details. Retain risk review, store-count cap, empty/partial/unavailable outcomes and backend-generated reports.

## Real map and evidence

Retain MapLibre GL JS with OpenFreeMap Positron: https://tiles.openfreemap.org/styles/positron. Streets and place names come from vector tiles; retain native OpenFreeMap, OpenMapTiles and OpenStreetMap attribution. No paid key, bulk download or offline cache is used. The local MapLibre worker is prepared by the existing build script.

Project coordinates place purple candidates and black existing stores. Current demo locations remain explicitly SYNTHETIC; streets do not validate those businesses. Selection is shared with accessible cards and comparisons. Zoom, pan, fit selection and reset are available. Loading, WebGL and tile errors expose retry while the shortlist remains usable; no artificial geographic fallback is displayed.

POIs, catchments and DaypartDNA halos use only matching current backend evidence. Missing scores have no halo; supported zero is distinct from unknown. Infrastructure renders only supplied, validated Point/LineString/Polygon geometry and retains hypothetical/source labels. Competitor inventory is unavailable and its layer stays disabled. Changing the saved scenario or shared period refreshes supported analytical layers.

## Hierarchy and accessibility

Keep results prominent and IDs inside Data and analysis details / Technical Details. Use concise headings, labelled INR amounts, readable status text, visible focus, native labelled controls and local table scrolling. Primary DaypartDNA choices are Morning, Lunch, Evening and Weekend, with all six canonical periods in a disclosure. Identify it as POI-derived opportunity, never measured footfall.

Responsive grids collapse to one column on phones; comparison and map controls remain available. There is no entrance choreography; reduced-motion preferences are respected. Secondary map and evidence labels have a minimum 11px size, while primary controls and results are larger. Disabled text uses 5.92:1 contrast against its fill.

## State and calculation boundaries

Formatting and percentage/multiplier input conversion are presentation only. Financial outputs, ranks, thresholds and network totals come from saved backend responses. Null is unknown, never zero. Preserve source/model/scenario/evaluation identities, request cancellation and incrementing response tokens. Edits mark derived results stale and disable portfolio/export until the matching completed evaluation arrives. Preserve prior successful values with a stale notice.

## Verification scope

Focused map interactions and navigation were inspected with labelled synthetic input data and real online tiles. Desktop 1440px, tablet 768px and phone 390px reviews found no horizontal page overflow or browser console errors. Taste inspection had zero failures; its small-text warning remains for compact secondary labels. Full financial/ML acceptance and live analytical overlay integration remain deferred. See docs/UX_MAP_HANDOFF.md for exact commands and results.

## Workspace feature navigation

Keep the three page links and pair each with a labelled expand/collapse button. The current page opens by default. Feature links point to existing heading anchors: Explore exposes rankings, DaypartDNA and comparison; Test Changes exposes the scenario builder, Future Infrastructure and FailFast; Investment Plan exposes Budget Optimisation and Investment Reports. Retain separate page/section active states, keyboard focus at the destination, browser history and delayed-content deep links. On phones, expanded links wrap beneath the three main page links. No new routes or backend behavior.
