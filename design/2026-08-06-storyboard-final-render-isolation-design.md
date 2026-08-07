# Storyboard Final Render Isolation Design

## Problem

Each generated storyboard is stored as a separate Shortform Director project.
The first project's completed final render is therefore correctly isolated in
persisted data from a newly generated storyboard project.

The Angular production store does not clear execution state when
`generatePlan()` replaces the currently displayed project with a newly
generated storyboard project. The previous project's `finalRender` status and
final-video object URL remain visible until the production page is destroyed
and recreated.

An in-flight final-render status request from the previous project can also
resolve after the project switch and write the previous status back into the
store.

## Expected Behavior

- A newly generated storyboard starts with no final-render status or video.
- Its final-render section displays the prerequisite message until its own
  narration and generated shots are ready.
- Selecting the first storyboard again restores that storyboard's persisted
  completed final render.
- Responses belonging to a previously selected project cannot mutate the
  current storyboard's final-render state.

## Design

Keep final-render persistence unchanged. The Desktop API already stores the
active render revision on the correct storyboard project.

In `ShortformDirectorProductionStore`:

1. Clear execution state immediately before accepting a successfully generated
   replacement storyboard project.
2. After each awaited final-render status or download request, verify that the
   current project still matches the project that started the poll before
   mutating `finalRender` or `finalVideoUrl`.
3. Do not let a poll belonging to an old project change the current project's
   `startingFinalRender` flag.

No component template, API contract, or persisted project schema changes are
required.

## Verification

Add store regression tests that prove:

1. A completed final render and video URL are cleared when a new storyboard
   project is accepted.
2. A delayed completed status response from the previous project is ignored
   after the new storyboard project becomes current.
3. Existing storyboard-history selection behavior remains green.
