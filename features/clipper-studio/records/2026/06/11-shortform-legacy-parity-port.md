# Shortform Legacy Parity Port

Date: 2026-06-11

## Decision

Clipper2 shortform production must match the legacy Clipper shortform screen from
`adlight_angular` exactly from the user's point of view. "Close enough" is not an
accepted result. Any visual or behavioral difference from the legacy screen is a
bug unless the user explicitly approves the difference.

This work is separate from the later project/job/queue terminology and model
cleanup. The current branch base should keep the `shortform_url`,
`shortform_paste`, and `shortform_prompt` plugin split from
`work/clipper1-input-workflow-split`.

Current sequencing:

1. Finish this shortform legacy UI/pre-render parity work first.
2. After it is stable and approved, start Project-first / Plugin / Queue model
   cleanup.

The Project-first / Plugin / Queue cleanup has not started yet. Do not combine
that refactor with this legacy UI port.

## Phase 1 Scope

Phase 1 implements everything up to, but not including, actual video generation.

Included:

- Plugin Store still shows `shortform_url`, `shortform_paste`, and
  `shortform_prompt` as separate user-visible plugins.
- Each shortform plugin opens a shortform production editor with the legacy
  Clipper UI and behavior for its input mode.
- The editor layout, colors, fonts, spacing, panel widths, icons, hover states,
  focus states, disabled states, empty states, and button affordances must match
  the legacy screen exactly.
- URL input, prompt input, paste input, prompt recommendation, clip generation,
  clip editing, subtitle editing, TTS UI behavior, media/thumbnail editing,
  style controls, title/logo controls, preview, and the shortform generation
  button must work up to the video-generation boundary.
- The shortform generation button must build and log the legacy video-generation
  request payload.

Excluded from Phase 1:

- No ffmpeg render call.
- No `/projects` navigation after pressing the shortform generation button.
- No render job creation.
- No queue insertion.
- No completed Project promotion for rendered video output.
- No project/job/queue terminology refactor beyond what is already present on
  the branch.

## Hard Boundary For The Generate Button

The legacy `숏폼 생성하기` button must remain visually and behaviorally identical
until click, but click handling stops before backend video generation.

Required click behavior:

1. Build the payload that would be sent to the legacy video creation API.
2. `console.log` that payload with a stable label.
3. Do not call any backend render/video/queue endpoint.
4. Do not navigate to `/projects`.
5. Do not create or mutate render jobs.

If a future implementation adds `startRender()`, `/render-jobs`,
`/create-video-sse`, queue insertion, or `/projects` navigation during Phase 1,
that is a scope violation.

## Payload Contract

The payload logged by the frontend must use the legacy Python request shape used
before media-server/ffmpeg rendering.

Primary schema references:

- `adlight_python/app/schemas/ShortsProjectSchema.py`
  - `ShortsVideoCreateRequestSchema`
  - `ShortsVideoCreateRequestProjectSchema`
  - `CommonProjectDataSchema`
- `adlight_python/app/schemas/ClipSchema.py`
  - `ClipResponseSchema`
  - `SubtitleSchema`
- `adlight_python/app/routers/v1/ShortsProjectRouter.py`
  - `PATCH /projects/{id}/create-video-sse`
  - `PATCH /projects/{id}/create-video`
- `adlight_python/app/services/ShortsProjectService.py`
  - `prepare_media_server_payload()`
- `adlight_python/app/services/VideoService.py`
  - `VideoService.create_video()`

Frontend log payload shape:

```ts
interface LegacyShortformVideoCreatePayload {
  project: {
    bgm_id: number;
    template_id: number;
    tts_speaker_id: number;
    tts_speed: number;
    sub_title_check: boolean;
    main_title_check: boolean;
    bottom_title_check: boolean;
    logo_check: boolean;
    logo_type: 'IMAGE' | 'TEXT';
    sub_title?: string | null;
    main_title1?: string | null;
    main_title2?: string | null;
    bottom_title?: string | null;
    logo_image?: string | null;
    logo_text?: string | null;
    language?: string | null;
  };
  clips: Array<{
    id?: number | null;
    project_id: number;
    media_url: string;
    thumbnail_url?: string | null;
    subtitles: Array<{
      subtitle: string[];
      tts_url?: string | null;
      duration?: number | null;
    }>;
    order_num: number;
  }>;
  contents_input: {
    input_type: 0 | 1 | 2;
    input_content: string;
  };
}
```

`prepare_media_server_payload()` later turns this request into the media-server
payload consumed by `VideoService.create_video()`:

```ts
interface LegacyMediaServerVideoPayload {
  project_id: number;
  project: {
    sub_title_check: boolean;
    main_title_check: boolean;
    bottom_title_check: boolean;
    logo_check: boolean;
    logo_type: 'IMAGE' | 'TEXT';
    sub_title?: string | null;
    main_title1?: string | null;
    main_title2?: string | null;
    bottom_title?: string | null;
    logo_image?: string | null;
    logo_text?: string | null;
  };
  contents_ratio: '16:9' | '4:3' | '1:1' | 'full';
  template_id: number;
  template_settings: Record<string, unknown>;
  bgm_url: string;
  clips: LegacyShortformVideoCreatePayload['clips'];
}
```

Phase 1 logs the first payload shape, not the media-server payload.

## UI Source Of Truth

Legacy visual and behavior source:

- `adlight_angular/src/modules/d2x-client/pages/shortform/shortform.component.*`
- `adlight_angular/src/modules/d2x-client/components/contents-input/*`
- `adlight_angular/src/modules/d2x-client/components/content-input-components/prompt-input/*`
- `adlight_angular/src/modules/d2x-client/components/content-input-components/url-input/*`
- `adlight_angular/src/modules/d2x-client/components/content-input-components/load-input/*`
- `adlight_angular/src/modules/d2x-client/components/clip-and-subtitle/*`
- `adlight_angular/src/modules/d2x-client/components/subtitle-row/*`
- `adlight_angular/src/modules/d2x-client/components/title-check/*`
- `adlight_angular/src/modules/d2x-client/components/shorform-buttons/*`
- `adlight_angular/src/modules/d2x-client/components/video-preview/*`
- `adlight_angular/src/assets/d2x/new/css/*`
- `adlight_angular/src/assets/d2x/new/img/*`
- `adlight_angular/src/assets/d2x/clip/*`

Clipper2 implementation can use different internals, but it must not change the
user-visible result.

## Implementation Boundary

Use Clipper2 app boundaries:

- Angular calls NestJS APIs, not Python plugin/runtime URLs directly.
- The editor must not depend on legacy `D2XDataService`.
- A Clipper2 adapter/view-model layer may translate `ShortformProject` and
  editor state into the legacy UI shape.
- The generation payload builder must be a tested frontend unit.
- Real video generation wiring belongs to a later phase after UI/behavior parity
  is approved.

## Completion Criteria

Phase 1 is complete only when all of these are true:

- The three shortform plugins remain split and user-visible.
- Each shortform plugin opens the correct input-mode editor.
- The editor is visually identical to the legacy Clipper screen in the required
  states:
  - initial empty editor
  - prompt helper collapsed
  - prompt helper expanded
  - URL input filled
  - paste input filled
  - clips generated
  - subtitle row hover/focus/edit
  - media thumbnail empty/filled/video
  - right style panel
  - preview panel
  - generate button enabled/disabled
- Legacy behavior before video generation works for URL, prompt, and paste.
- Pressing `숏폼 생성하기` logs a legacy schema-compatible payload.
- Pressing `숏폼 생성하기` does not call backend video generation, does not enqueue
  anything, and does not navigate to `/projects`.

## 2026-06-11 Implementation Snapshot

The first implementation pass has been applied on top of
`work/clipper1-input-workflow-split`; do not restart from
`feature/initial-scaffold`.

Current checked heads:

```text
clipper_angular: work/clipper1-input-workflow-split @ 8d9d0a5 Fix shortform legacy font sizing
clipper_nestjs:  work/clipper1-input-workflow-split @ 06e3123 Implement shortform clip generation providers
```

Implemented so far:

- `shortform_url`, `shortform_paste`, and `shortform_prompt` remain separate
  Store plugins.
- The shortform editor opens inside the normal Clipper2 app shell, keeping the
  Clipper2 sidebar visible.
- Store cards are selected first; plugin open action lives in the right detail
  panel. A legacy `.actions` CSS collision was fixed so Store styling is not
  changed by the shortform editor styles.
- Legacy shortform assets and editor styles were ported into the Clipper2
  shortform editor.
- Legacy styles were scoped to the shortform editor instead of staying global.
  This protects Store, Dashboard, Projects, and Template Builder from Clipper1
  reset/common/edit CSS.
- The shortform editor has clip drag/drop and subtitle drag/drop support.
- Subtitle row hover action behavior was tightened so add/delete/preview buttons
  do not visibly linger across many rows during fast mouse movement.
- Clip drag no longer creates temporary scrollbars inside the clip container.
- The clip-generation modal is updated by NestJS WebSocket events. Clipper2 does
  not use legacy SSE for this pre-render clip generation path.
- `숏폼 생성하기` remains log-only for Phase 1. It must not enqueue, render, or
  navigate.
- The scoped legacy font variable fix restored left-panel text sizing without
  reintroducing the legacy global `html { font-size: 62.5%; }` reset.

Backend/pre-render status:

- The normal clip-generation path now uses configured provider integrations
  instead of hard-coded dummy clip data:
  - configured LLM script provider
  - Naver Clova TTS
  - Naver image search
- NestJS broadcasts clip-generation progress events over WebSocket.
- Naver image no-result cases should not break the whole clip list.
- Local `.clipper_data/` is runtime data and is ignored by git. Packaged app
  runtime data belongs under the OS app-data directory, e.g.
  `/Users/jina/Library/Application Support/Clipper2` on macOS.

Verification already run:

- Focused Angular tests passed after the legacy port/style isolation work.
- Angular build passed.
- NestJS build passed.
- NestJS shortform/event tests passed.
- Browser computed-style check confirmed the left panel font regression fix:
  tab `16px`, input `13px`, button `16px`, root `html` `16px`.

Known gap:

- A full Angular run still had an unrelated pre-existing Template Builder
  snapshot failure around `layoutImage` being undefined. It is not part of this
  shortform parity pass.

## 2026-06-12 Modal Follow-Up

During the shortform regenerate-clips confirmation work, Clipper2 app-wide
modal usage was inventoried. No broad modal migration should be mixed into the
shortform legacy parity work.

Reference:

- [Clipper2 Modal Usage Inventory](../../../../../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)

Current decision:

- Keep the shortform regenerate-clips confirmation on the shared confirmation
  modal.
- Do not convert ffmpeg/model consent, progress dialogs, preview overlays, or
  Template Builder form overlays as part of this phase.
- Future candidates are Template Builder native dirty-cancel `window.confirm`
  and the Template Builder delete confirmation overlay.

## Remaining Work After Snapshot

Phase 1 is still not complete. The remaining work is to close every visible and
behavioral mismatch against the legacy `adlight_angular` shortform screen.

Manual browser checks still required:

- Plugin Store selection/detail/open flow for all three shortform plugins.
- URL input mode.
- Prompt input mode and prompt helper expanded/collapsed behavior.
- Paste input mode.
- Clip-generation modal progression from WebSocket events. The first visible
  stage must be text analysis, then later stages should advance from backend
  events.
- Generated clip cards, thumbnail placeholders, image/video preview states, and
  broken-asset fallback.
- Clip drag/drop order and subtitle drag/drop order.
- Subtitle add/delete/edit/preview hover and focus behavior.
- TTS/BGM controls and preview/play/stop behavior.
- Title, logo, template/style controls.
- Empty states, disabled states, active states, hover states, focus states, and
  responsive layout.
- `숏폼 생성하기` click behavior:
  - logs the legacy payload
  - does not call render/video/queue APIs
  - does not navigate to `/projects`

Implementation still needed:

- Continue legacy parity fixes in the left input panel, center clip/subtitle
  editor, right control panel, modal states, and preview panel.
- Harden local/devapp/packaged env setup for LLM, Naver Clova TTS, and Naver
  image search so configuration errors are clear.
- Validate packaged app behavior separately, especially data paths, bundled env,
  and WebSocket delivery.
- Only after user approval of the UI/pre-render parity, start the Project-first
  / Plugin / Queue cleanup. That later phase should make Project the queue and
  archive unit, separate user plugins from hidden runtime workers, and add a
  ProjectRun/ProjectProgress facade over `/jobs` and `VideoRenderJob`.
- Actual video-generation queue/archive wiring is after that cleanup, not part
  of this legacy UI parity phase.
