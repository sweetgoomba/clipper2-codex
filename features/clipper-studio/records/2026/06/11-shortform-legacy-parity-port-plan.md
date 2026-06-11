# Shortform Legacy Parity Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the legacy Clipper shortform production UI/behavior into Clipper2 exactly, stopping at payload logging before video generation.

**Architecture:** Keep the current `work/clipper1-input-workflow-split` plugin split and Clipper2 Angular/NestJS boundaries. Build a legacy-parity Angular editor using the legacy UI/assets as source of truth, with tested adapters from Clipper2 shortform state to the legacy video-create payload. Do not wire render jobs, queues, or `/projects` navigation in this phase.

**Tech Stack:** Angular 19 standalone components, Jasmine/Karma, NestJS only for pre-render shortform project/clip APIs if needed, legacy `adlight_angular` assets/CSS, legacy `adlight_python` payload schema references.

---

## Branches

- `clipper_angular`: create/use `work/shortform-legacy-parity-port` from `work/clipper1-input-workflow-split`.
- `clipper_nestjs`: create/use `work/shortform-legacy-parity-port` from `work/clipper1-input-workflow-split` only if URL/paste or pre-render clip APIs need backend support.
- `.codex`: document on the current docs branch for this plan.

Do not restart from `feature/initial-scaffold`; it drops required plugin split and project terminology work.

## 2026-06-11 Progress Update

This plan has been partially executed on the existing
`work/clipper1-input-workflow-split` branches.

Completed or substantially implemented:

- Legacy shortform editor assets/styles were ported into Clipper2.
- Legacy editor styles were scoped to the shortform page instead of leaking into
  the whole Clipper2 app.
- Plugin Store detail/open behavior was restored after the style port.
- The shortform editor opens inside the normal Clipper2 shell with the sidebar
  visible.
- `shortform_url`, `shortform_paste`, and `shortform_prompt` remain separate
  user-visible plugins.
- Clip-generation modal updates now come from WebSocket events, not SSE.
- The backend clip-generation path uses provider integrations for LLM script
  generation, Naver Clova TTS, and Naver image search instead of normal-path
  dummy clip data.
- Clip drag/drop and subtitle drag/drop were added.
- Subtitle hover action lingering and clip-drag temporary scrollbars were
  improved.
- The `숏폼 생성하기` boundary remains log-only; render/queue/navigation wiring
  is still intentionally excluded.
- The left panel font regression from legacy `rem` variables was fixed with
  scoped px-based font variables.

Verification already performed:

- Focused Angular shortform/style tests passed.
- Angular build passed.
- NestJS build passed.
- NestJS shortform/WebSocket event tests passed.
- Browser computed-style check confirmed the shortform left panel font sizes.

Do not treat Phase 1 as complete yet. The remaining tasks below still need a
strict visual/behavior parity pass against `adlight_angular`, especially for
the left input panel, center clip/subtitle editor, right controls, modal states,
preview states, packaged runtime behavior, and full manual plugin flows.

Project-first / Plugin / Queue cleanup is not part of this plan and has not
started. Keep that work deferred until the shortform legacy parity phase is
finished and approved.

## Task 1: Baseline And Contracts

**Files:**
- Read: `clipper_angular/src/app/app.routes.ts`
- Read: `clipper_angular/src/core/plugin-status.service.ts`
- Read: `clipper_angular/src/features/shortform/**`
- Read: `clipper_nestjs/src/plugins/plugin-catalog.ts`
- Read: `clipper_nestjs/src/shortform/**`
- Read: `adlight_angular/src/modules/d2x-client/pages/shortform/**`
- Read: `adlight_angular/src/modules/d2x-client/components/contents-input/**`
- Read: `adlight_angular/src/modules/d2x-client/components/content-input-components/**`
- Read: `adlight_angular/src/modules/d2x-client/components/clip-and-subtitle/**`
- Read: `adlight_angular/src/modules/d2x-client/components/subtitle-row/**`
- Read: `adlight_angular/src/modules/d2x-client/components/title-check/**`
- Read: `adlight_angular/src/modules/d2x-client/components/shorform-buttons/**`
- Read: `adlight_python/app/schemas/ShortsProjectSchema.py`
- Read: `adlight_python/app/schemas/ClipSchema.py`
- Read: `adlight_python/app/services/VideoService.py`

- [ ] Verify worktree branches and clean status.
- [ ] Install dependencies if the Angular/NestJS worktrees do not have `node_modules`.
- [ ] Run current focused Angular route/plugin tests before edits.
- [ ] Run current focused NestJS shortform/plugin tests before edits if backend changes are planned.
- [ ] Record any pre-existing failures before touching code.

## Task 2: Legacy Assets And Style Scope

**Files:**
- Create/modify: `clipper_angular/public/assets/d2x/**`
- Modify: `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.scss`
- Possible create: `clipper_angular/src/features/shortform/styles/legacy-shortform.scss`

- [ ] Copy required `adlight_angular/src/assets/d2x` assets into `clipper_angular/public/assets/d2x` so existing `assets/d2x/...` paths resolve.
- [ ] Include only assets needed by the legacy shortform editor unless exact parity requires a broader copy.
- [ ] Import or scope the legacy edit CSS so it affects the shortform editor without breaking Store, Dashboard, Projects, or Template Builder.
- [ ] Add a focused style/DOM test that confirms the shortform page contains the legacy panel shell classes and that app-wide routes do not receive the shortform-only root class.
- [ ] Run the focused Angular test and confirm it fails before implementation, then passes after implementation.

## Task 3: Input Mode Routing While Keeping Plugin Split

**Files:**
- Modify: `clipper_angular/src/app/app.routes.ts`
- Modify: `clipper_angular/src/app/app.routes.spec.ts`
- Modify: `clipper_angular/src/core/plugin-status.service.ts` only if route mapping changes are needed.
- Modify: `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.ts`

- [ ] Write a failing route test proving `/shortform/prompt`, `/shortform/url`, and `/shortform/paste` all load the legacy-parity editor instead of the unavailable page.
- [ ] Keep `shortform_prompt`, `shortform_url`, and `shortform_paste` as separate plugin store entries.
- [ ] Make the loaded editor derive its fixed input mode from the route/plugin entry.
- [ ] Do not reintroduce a single user-visible `clipper1` plugin.
- [ ] Run the route/plugin tests and confirm they pass.

## Task 4: Legacy Payload Builder

**Files:**
- Create: `clipper_angular/src/features/shortform/services/legacy-shortform-video-payload.ts`
- Create: `clipper_angular/src/features/shortform/services/legacy-shortform-video-payload.spec.ts`
- Modify: `clipper_angular/src/features/shortform/models/shortform-project.ts` if numeric legacy IDs or mode typing need explicit fields.

- [ ] Write failing tests that build a legacy payload with:
  - `project.bgm_id`
  - `project.template_id`
  - `project.tts_speaker_id`
  - `project.tts_speed`
  - title/logo checks and values
  - `clips[].project_id`
  - `clips[].media_url`
  - `clips[].thumbnail_url`
  - `clips[].subtitles[].subtitle`
  - `clips[].subtitles[].tts_url`
  - `clips[].subtitles[].duration`
  - `clips[].order_num`
  - `contents_input.input_type`
  - `contents_input.input_content`
- [ ] Write a failing test proving prompt/url/paste modes map to input types `0`, `1`, `2`.
- [ ] Implement the payload builder with no HTTP dependency.
- [ ] Run the payload tests and confirm they pass.

## Task 5: Generate Button Must Log Only

**Files:**
- Modify/create: shortform legacy right-panel/generate-button component files under `clipper_angular/src/features/shortform/**`
- Test: corresponding component spec.

- [ ] Write a failing component test that clicks `숏폼 생성하기` and verifies `console.log` receives the legacy payload.
- [ ] In the same test, verify no `ShortformProjectService.startRender()` call occurs.
- [ ] Verify no router navigation to `/projects` occurs.
- [ ] Implement click handling with payload logging only.
- [ ] Run the focused test and confirm it passes.

## Task 6: Left Panel Legacy-Parity Input UI

**Files:**
- Replace or create shortform input panel components under `clipper_angular/src/features/shortform/components/**`.
- Use legacy sources from:
  - `contents-input`
  - `prompt-input`
  - `url-input`
  - `load-input`

- [ ] Write focused tests for the fixed input mode per route.
- [ ] Implement URL input visual behavior exactly.
- [ ] Implement prompt helper collapsed/expanded behavior exactly.
- [ ] Implement prompt recommendation UI behavior using current Clipper2 prompt recommendation API where available.
- [ ] Implement paste input visual behavior. If Quill is not retained, the replacement must still match legacy user-visible behavior.
- [ ] Preserve legacy labels, disabled states, and button affordances.
- [ ] Run focused component tests.

## Task 7: Clip Generation And Center Editor

**Files:**
- Replace or create shortform center editor components under `clipper_angular/src/features/shortform/components/**`.
- Use legacy sources from:
  - `clip-and-subtitle`
  - `subtitle-row`
  - clip/media controls.

- [ ] Write tests for generated clips rendering in legacy clip-card layout.
- [ ] Write tests for subtitle add/delete/edit behavior.
- [ ] Write tests for active/focus/hover class behavior where practical.
- [ ] Implement clip generation wiring for prompt/url/paste up to pre-render project state.
- [ ] Implement subtitle edit behavior and duration updates using Clipper2 state.
- [ ] Implement media empty/filled/video thumbnail states.
- [ ] Run focused component/service tests.

## Task 8: Right Panel Style, Preview, And Controls

**Files:**
- Replace or create shortform right panel components under `clipper_angular/src/features/shortform/components/**`.
- Use legacy sources from:
  - `title-check`
  - `video-preview`
  - `shorform-buttons`
  - `d2x-custom-select` behavior as needed.

- [ ] Write tests for BGM, TTS, speed, ratio, title, and logo control state mapping.
- [ ] Implement legacy right panel layout exactly.
- [ ] Implement BGM/TTS play/stop UI behavior.
- [ ] Implement title/logo check state and text/image/text mode state.
- [ ] Implement preview shell and marker layout.
- [ ] Keep `숏폼 생성하기` as log-only from Task 5.
- [ ] Run focused component tests.

## Task 9: URL/Paste Backend Gap Audit

**Files:**
- Inspect/modify: `clipper_nestjs/src/shortform/**`
- Inspect/modify: `clipper_angular/src/features/shortform/services/shortform-project.service.ts`
- Test: `clipper_nestjs/test/shortform-project-api.test.js` if backend changes are required.

- [ ] Confirm whether current NestJS shortform APIs can create/generate projects for `url` and `paste`.
- [ ] If not supported, add only the pre-render API support needed for legacy parity.
- [ ] Do not add render queue integration.
- [ ] Do not add video generation integration.
- [ ] Run backend tests for shortform project creation/generation.

## Task 10: Visual Parity Verification

**Files:**
- Possible create: `clipper_angular/e2e` or local screenshot script if the repo already has a suitable pattern.
- No production code changes unless parity failures require fixes.

- [ ] Run the Clipper2 Angular app.
- [ ] Capture screenshots for:
  - initial empty editor
  - prompt helper collapsed
  - prompt helper expanded
  - URL input filled
  - paste input filled
  - generated clips
  - subtitle edit focus
  - media empty/filled/video
  - right style panel
  - preview
  - generate button enabled/disabled
- [ ] Compare against `adlight_angular` legacy reference screenshots.
- [ ] Fix every visual/behavior mismatch unless the user explicitly approves a difference.

## Task 11: Final Verification

- [ ] Angular focused tests pass.
- [ ] Angular build passes.
- [ ] NestJS focused tests/build pass if backend files changed.
- [ ] Manual app check confirms pressing `숏폼 생성하기` logs payload only.
- [ ] Manual app check confirms no `/projects` navigation and no queue/render request.
- [ ] Document remaining approved exceptions, if any. Unapproved differences are bugs.
