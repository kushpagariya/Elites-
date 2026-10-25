# Independent technical review B

Scope: Landing.tsx, City.tsx, FallbackCity.tsx and supporting global styles. Read-only source assessment; no implementation changes. Reviewed 2026-10-24. Findings intentionally withheld from the parallel design reviewer.

Implementation integrity: coherent product-specific system. The city, dayparts, conditional infrastructure, rejection/rescue and capital frame match the documented product. No P0 or new P1 finding established. /app being a placeholder is explicitly in scope and is not a defect.

## Verified remaining findings

| Priority | Before | After recommendation | Why / evidence |
| --- | --- | --- | --- |
| P2 | “Pause motion” only replaces City with FallbackCity; the reveal IntersectionObserver continues to call element.animate. | Either name the control “Pause city” or include paused in the reveal guard and cancel pending reveal animations. | Landing.tsx lines 21, 26, 29. A visitor requesting paused motion still receives 22px text entrances on subsequent sections. Source-verified; not claimed as a WCAG failure. |
| P2 | Canvas uses an always-running frame loop for every chapter except evidence, including chapter 7 while an opaque footer covers it. Every frame rewrites all instance matrices/colors and the camera projection, even after settling. | Stop frames when the stage is fully occluded/offscreen; use demand invalidation during scene transitions and deliberate hero motion. | City.tsx useFrame and Canvas frameloop; globals.css opaque footer z-index 6 vs scene z-index 0. Unnecessary rendering/battery work on a stationary footer. No measured frame-rate regression claimed. |
| P2 | Persistent mobile view-tool buttons have minimum height 38px; chapter navigation targets are 24px square on larger touch viewports. | Make hit regions at least 44px square while keeping visible marks compact. | globals.css .view-tools button and .chapter-nav a. Smaller-than-skill target recommendation, not a claim of WCAG AA violation (24px minimum may pass). |

## Already being addressed by the main agent

Initial chapter/hash restoration synchronization, resize of the heights buffer, and restricting mouse parallax to the hero. The buffer change was observed during the review; remaining work needs final verification. These are not counted as additional findings.

## Positive evidence

Semantic main/header/navigation and heading structure; named groups and pressed states; visible keyboard focus and skip link; HTML text explains each visual; explicit illustrative/proxy labels; reduced-motion SVG path; save-data and WebGL-failure fallbacks; bounded DPR, instancing and ref-based animation instead of React per-frame state. Explicit user selection persists over automatic daypart/scenario changes.

## Checks and limits

- Impeccable detect --json components attempted. Failed: engine 0.1.16 not installed and cache directory C:\Users\ashut_2urnib0\.impeccable\bin\0.1.16 could not be created. No detector pass is claimed.
- Independent IAB navigation to ports 3000 and 3001 timed out. A visibility option was also rejected for the subagent tab. No rendered accessibility, contrast, responsive, touch or performance score is assigned.
- Read installed Impeccable skill and technical audit reference, Emil design skill, and installed taste skill guidance. PRODUCT.md and docs/LANDING_DESIGN_DECISIONS.md read. Root DESIGN.md absent.
- No source changes, test files or package changes made. This report is the only output file.

Recommended sequence: $impeccable harden for the pause control contract; $impeccable optimize for idle canvas work; $impeccable adapt for hit regions; $impeccable polish after live verification.
