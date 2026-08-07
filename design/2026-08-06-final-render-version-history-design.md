# Final Render Version History Design

## Goal

Allow a completed Shortform Director storyboard to create another final render
without regenerating its storyboard, narration, or AI shot videos. Preserve
every completed final video and let the user reopen an earlier version.

## User Experience

The final-render step has three states:

1. Before the first render, it shows `최종 영상 만들기`.
2. After a completed render, it keeps the current video preview visible and
   shows `최종 영상 다시 만들기`.
3. During a rerender, it keeps the previous completed preview playable, shows
   the new render's progress, and disables the rerender button.

When the new render completes, it becomes the default preview. If it fails or
is cancelled, the previous completed video remains the default preview and
the current error is shown.

Below the preview, `이전 최종 영상 N개` exposes completed render versions in
newest-first order. Selecting one downloads and displays that version. Failed
and cancelled jobs are not shown in this completed-video history.

This change does not add version deletion, custom version names, or concurrent
final renders.

## Persisted Production State

Keep `activeRenderRevisionId`, but define it as the latest successfully
completed render used as the default video.

Add:

```ts
pendingRenderRevisionId: string | null;
completedRenderRevisions: Array<{
  renderId: string;
  completedAt: string;
}>;
```

Only one pending render is allowed. Starting a render sets
`pendingRenderRevisionId` but does not change `activeRenderRevisionId`.

When a render completes and its MP4 has been materialized:

1. append it to `completedRenderRevisions` if absent;
2. set `activeRenderRevisionId` to the new render;
3. clear `pendingRenderRevisionId`.

When a render fails or is cancelled, clear only
`pendingRenderRevisionId`. The active and completed revisions remain
unchanged.

Existing projects that contain only `activeRenderRevisionId` remain valid.
The active ID is treated as a completed historical revision even when the new
array is absent. Its fallback `completedAt` is the project's `updatedAt`, and
it is backfilled on the next successful render-state update.

## Desktop API

Keep the existing endpoints:

- `POST /projects/shortform-director/projects/:projectId/final-renders`
- `GET /projects/shortform-director/projects/:projectId/final-renders/:renderId`
- `GET /projects/shortform-director/projects/:projectId/final-renders/:renderId/file`

Add:

- `GET /projects/shortform-director/projects/:projectId/final-renders`

The list response contains:

```ts
{
  activeRenderRevisionId: string | null;
  pendingRenderRevisionId: string | null;
  items: Array<{
    renderId: string;
    completedAt: string;
    active: boolean;
  }>;
}
```

The list contains completed versions only, newest first.

Status and file endpoints accept:

- the pending render;
- any completed historical render;
- the legacy active render of an older project.

Unknown or foreign render IDs continue to return not found.

## Render Lifecycle And Concurrency

`start()` rejects a second request while `pendingRenderRevisionId` is set.
It prepares the same storyboard project using its existing narration and AI
video assets, creates a new render ID, and reserves it as pending.

If the renderer cannot start, the pending reservation is cleared and the
previous active video is untouched.

`status()` remains the point that observes a terminal job:

- completed: materialize the MP4, then atomically promote the render;
- failed or cancelled: atomically clear the matching pending ID;
- waiting or running: leave production state unchanged.

Compare-and-swap project writes must verify the pending ID before changing
state so a stale poll cannot promote or clear another render.

## Angular State

Add:

- completed final-render history;
- selected completed render ID;
- a loading state for switching historical videos.

Loading a storyboard fetches final-render history. It downloads the active
completed render for the default preview and resumes polling the pending
render, if present.

Starting a rerender:

- leaves the current object URL and selected completed render intact;
- sets the pending status and begins polling;
- switches to the new video only after successful completion;
- refreshes the completed history after promotion.

Object URLs are still revoked when replaced, switching storyboards, or
destroying the store.

## Error Handling

- A failed start preserves the current completed preview and history.
- A failed or cancelled asynchronous render preserves the active revision and
  re-enables the rerender button.
- A missing legacy render job is omitted without preventing the storyboard
  from loading.
- Failure to download a selected historical MP4 reports the existing
  presentation error and leaves the currently displayed video unchanged.

## Verification

Backend tests prove:

1. rerender start keeps the previous active revision;
2. completion promotes and records the new revision;
3. start/terminal failure preserves previous completed revisions;
4. a concurrent start is rejected;
5. historical status and file access work while unknown IDs are rejected;
6. legacy active-only state appears as one completed history item.

Angular tests prove:

1. a completed preview exposes `최종 영상 다시 만들기`;
2. clicking it emits the existing render request while preserving the preview;
3. completion selects the new version and refreshes history;
4. failure preserves the previous preview;
5. historical version selection downloads and displays that render;
6. storyboard switching still clears the previous storyboard's render state.
