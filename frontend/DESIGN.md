# StoreScout workspace design

This guide extends the root DESIGN.md's landing identity for the implemented workspace. The root guide's references to a connection diagnostic describe the previous consolidation baseline; current operational routes are implemented here. Product flow follows the user-supplied StoreScout PRD PDF, especially sections 3.1, 5.1 and 9.

## Direction and users

Taste direction: Framed sheet, seed 940076972, no redraw. Expansion and finance users compare ten grocery candidates with four fictional branches, test an immutable scenario, and review a full-network portfolio. Retain the existing Manrope, paper/ink/purple palette and hexagonal mark. The framed white sheet and neutral navigation suit repeated analytical work; no entrance animation is needed.

Questions answered first:

- Explore: which sites should I compare, and what value and evidence does the saved evaluation support?
- Scenario: what would have to change, and which failures remain after evaluating a new assumption snapshot?
- Portfolio: which eligible set fits the evaluated budget, and is the search exact, partial or unknown?

## System

Use the shared shell and workspace provider. At desktop widths the frame has a 228px sidebar, 64px top bar, 8px right/bottom inset and a 16px sheet radius. Content uses 24px padding and gaps; mobile uses a compact three-column navigation row and 16px content margins. Tables scroll within a labelled focusable region rather than overflowing the page.

Manrope headings are 26px/650 for the desktop screen title, 24px on phones, 18px for sections and 16px for local groups. Body UI is 14px; supporting data labels are 12–13px. Tabular figures, right-aligned monetary columns and visible INR units make comparisons readable. Quiet borders distinguish data rows; no shadows are used on resting panels.

Colors are inherited from src/app/base.css. Purple marks candidate geometry and the product mark. Black marks fictional branches. Financial states use text with restrained semantic ink; color never replaces VIABLE / AT_RISK / REJECTED / REVIEW_REQUIRED. Disabled actions retain readable contrast. Native focus rings and the skip link remain visible.

MapLibre draws API coordinate inputs over the local SYNTHETIC GeoJSON boundary. It is not a real basemap, footfall visualization or financial result. Its locally prepared worker avoids CDN dependencies; the candidate table remains available on loading or WebGL failure.

## Interaction and truth

Use actual links for routes and native labelled inputs. Comparison selection is shared with map pins and limited to two sites. Checkbox labels have 44px hit regions. Repeated action feedback uses 160ms transitions, fine-pointer hover gating and reduced-motion overrides. No page-load choreography delays the task.

An edit immediately marks previous results stale, cancels pending work and disables portfolio/report actions. Numeric formatting never converts null into zero. Financial values, ranks, rescue thresholds and full-network totals come from saved backend responses. Backend errors name the recovery action; HTTP 501 remains unavailable rather than a sample result.

ASSUMED budget/rent/demand inputs and SYNTHETIC project/source labels stay visible. Technical identities live in a disclosure, not release badges. Missing DaypartDNA evidence is distinct from zero opportunity; missing sensitivity remains unavailable rather than estimated in React.

## Render review

All three screens were inspected at 1440, 768 and 390px; final reports show 0 FAIL and 0 WARN, with explicit allowances only for the preserved purple/paper palette. All final fold and page screenshots were opened. This verifies the current unavailable-computation state, not backend analytical correctness or a full accessibility audit.

| Before | After | Why |
| --- | --- | --- |
| Connection diagnostic | Three task-specific screens on one shared context | Preserve the complete investment journey |
| Blank MapLibre canvas after worker load failure | Version-matched worker served locally | The map renders without a CDN |
| Small checkbox click regions | 44px comparison labels | Improve touch and keyboard usability |
| Disabled secondary export resembled an enabled control | Consistent disabled fill and readable ink | Make unavailable actions apparent |
| Long mobile context/header | Compact budget row and fully visible workflow navigation | Keep the task closer to the first viewport |

The largest blocks carry the screen's questions: candidate inputs, scenario edits and portfolio selection. Frames align and columns collapse without page overflow; only actual data tables scroll. Financial unavailable states remain intentional until computation is connected. There are no invented totals, chart series, customers, fitted-model results or found photographs to credit.
