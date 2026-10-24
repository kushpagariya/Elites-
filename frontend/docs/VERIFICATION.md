# Frontend consolidation verification

Baseline: e56dd84. No commit was created; changes remain reviewable in the working tree. The deletion of frontend/Elites and the untracked frontend/landing_page folder existed before this task.

## Changes

One frontend package now serves / and /app. Route groups separate marketing and workspace styling. Landing components moved to src/features/landing; shared API/types stay in src/lib. The old nested app, static-export hosting config, duplicate npm lockfile and generated .next-dev cache were removed. Historical visual evidence was moved to docs/landing-reference.

FinancialPlanner and FailFastCards now show unavailable states instead of browser-computed finance and hardcoded viability/rescue results. DaypartMap is explicitly labelled SYNTHETIC and illustrative. It is not analytics.

## Commands and results

The pnpm wrapper's bundled Node failed with ENOENT while opening a temporary file. Running pnpm's installed entry point with system Node succeeded:

- node C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs install: passed.
- pnpm typecheck via that entry point: passed after declaring the existing three-stdlib import as a direct dependency.
- pnpm build via that entry point: passed; routes /, /app and /_not-found generated.
- Browser click: landing Explore Demo opened /app; StoreScout branding returned to /. Both layouts retained their styles through client navigation.
- Backend was not running during browser verification. The workspace displayed API unavailable with a retry action and did not invent project data. Backend success and analytical outputs were not verified.
- Taste inspect at 1440, 768 and 390px: completed with 13 FAIL categories and 6 WARN categories. Report and all nine screenshots are in docs/verification/landing; all captures were visually opened.

## Visual limitations

This task preserves the supplied landing composition rather than replacing it. The inspector flags inherited long headings, small labels, step badges, borders, card patterns and a resting shadow. It also rejects the pinned purple/paper palette, lack of photographs and absence of DOM entrance animation (the city uses canvas). Those findings are recorded, not reported as a visual pass. Screenshots show the preserved composition; mobile labels and long headings need a separate polish pass. No performance, accessibility certification or model accuracy is claimed.

## Next integration dependency

Implement Explore/Compare, Scenario/Rescue and Portfolio/Report against agreed backend schemas, with one shared active evaluation context and explicit unavailable/error/stale states. Backend owns financial outputs, immutable evaluation persistence, model identity and portfolio enumeration. See root DESIGN.md and docs/handoffs/FRONTEND.md. Health success alone does not establish analytical readiness.

Skills actually consulted: Impeccable document/craft-floor, Emil Design Engineering and Taste. Impeccable context loader could not run; project context was read directly. No subagents were used.
