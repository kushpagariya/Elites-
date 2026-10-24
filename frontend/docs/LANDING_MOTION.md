# Landing motion

An additive motion pass over the existing retail identity. Copy, colours, typography, section order, routes, charts and analytical behaviour are preserved.

- **Expansion field:** decorative cartographic paths unfold behind the existing physical pass. A travelling signal and four catchment pulses connect the visual to retail expansion. These shapes are not geographic evidence or model results; the entire scene remains hidden from assistive technology.
- **Depth:** fine mouse pointers move the pass and map in opposing layers through Motion values and a spring (mass 1, stiffness 100, damping 10). Scrolling adds a small depth/rotation change. Existing drag and flip controls remain available. Touch input keeps normal scrolling and the pass's existing gesture behaviour.
- **Opening:** each existing headline line rises through a mask, with the lede and actions following. Text and line positions settle into the original layout.
- **Story:** native Web Animations reveal headings, stagger the three workflow steps and evidence columns, and uncover the two retail illustrations. They run once per visit, use the existing ease-out curve and never conceal content in the underlying document.
- **Actions:** primary buttons gain a light sweep and a small arrow response on fine-pointer hover.

Continuous CSS work uses transforms and opacity. Finite image/path entrances also use clip-path. Pointer/scroll values do not set React state per frame or animate layout dimensions. No dependency was added. Desktop/phone browser review is not a claim of measured frame rate on physical phones.

Pause cancels finite Web Animations, stops the decorative field and existing scenes, removes entrance transforms and leaves all content readable. Hidden tabs pause active finite animations. The hero's field and pass stop when it leaves view. OS reduced motion removes the field and positional choreography; `?flat` and data-saving mode also retain a static presentation. All pointer handlers, observers, media-query listeners and animation instances clean up when their components unmount.

Implementation: `features/landing/LandingMotion.tsx` and `app/(marketing)/landing-motion.css`. The workspace and backend are outside this change.

## Cinematic street sequence

The hero's Watch the story action opens an inline, full-width 24-second 3D sequence. It films the existing conceptual retail street along a smooth camera path, with a close-up, a moving view and a pullback. Three large titles crossfade inside a solid forest letterbox; playback controls stay clear of the text.

Play/pause, replay and a labelled native timeline work with pointer and keyboard input. Scrubbing pauses playback and renders the requested camera position. Global Pause overrides the local player. Playback suspends offscreen or in a hidden tab, finishes on its final frame, and does not loop automatically. No audio, video download or new dependency is required.

The WebGL scene is loaded lazily and released offscreen. Its pixel ratio is capped at 1.25 and its shadow map at 1024px. A matching poster remains visible during loading or if WebGL fails. Reduced motion uses the poster and a static title. Renderer-loss listeners clean up before intentional disposal, so scrolling away does not permanently disable the film.

The hero also gains an aperture reveal and a stronger, bounded camera-like movement of the pass on scroll. Brand colours, typography, navigation and backend behaviour remain intact. Implementation: `RetailFilm.tsx`, the `CinematicCity` export in `City.tsx`, and `retail-film.css`.
