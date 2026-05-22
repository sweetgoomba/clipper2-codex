# Hybrid Text Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Template Builder preview use the same final-render text output that generated videos use, without blocking live editing.

**Architecture:** Angular keeps browser-rendered text as an immediate fallback, but opens a Template Builder renderer session that keeps the Python worker warm while the editor is active. NestJS owns the session lifecycle and artifact request API. Python renders both single text layer artifacts and combined subtitle artifacts with metadata so Angular can display exact final-render PNGs and keep interaction overlays separate.

**Tech Stack:** Angular 19 zoneless standalone components, NestJS 10, existing PluginHost/Electron plugin bridge, Python `clipper1_video_render`, pytest, Node test runner, Karma/ChromeHeadless.

---

## File Structure

- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/template_builder_text_artifacts.py`
  - Add combined subtitle artifact rendering.
  - Keep single text layer artifact API intact.
- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/app.py`
  - Route `template_builder_subtitle_artifact` jobs to the new renderer.
- `clipper_python/tests/test_template_builder_subtitle_artifacts.py`
  - TDD coverage for combined subtitle PNG and metadata.
- `clipper_nestjs/src/template-builder/template-builder-text-artifact.service.ts`
  - Add `ensureWarm()`.
  - Add subtitle artifact worker/service path.
  - Keep request cache keyed by variant/layer/text/style snapshot.
- `clipper_nestjs/src/template-builder/template-builder.controller.ts`
  - Add renderer session warmup endpoint and subtitle artifact endpoint.
- `clipper_nestjs/test/template-builder-text-artifact.test.js`
  - TDD coverage for warmup and subtitle request/cache behavior.
- `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
  - Add warmup and subtitle artifact API client methods.
- `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
  - Warm worker when Template Builder page initializes.
  - Request plain text artifacts plus combined subtitle artifact in the debounced background refresh.
- `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts/html/scss`
  - Render combined subtitle artifact image for `subtitleText` while keeping selection/move/resize overlays.
- `.codex/session-logs/2026-05-09.log`
  - Record decisions, commands, commits, and remaining work.

## Task 1: Python Combined Subtitle Artifact

- [x] Write a failing pytest that calls `render_template_builder_subtitle_artifact(contract, text, output_dir)` and expects:
  - one PNG file exists,
  - `metadata.layerId === "subtitleText"`,
  - `metadata.frame` is the union of visible subtitle line boxes,
  - `metadata.lines` contains per-line `text`, `frame`, `boxFrame`, and `inkBBox`,
  - `metadata.clipped` is false for a normal two-line sample.
- [x] Run `uv run pytest tests/test_template_builder_subtitle_artifacts.py` and verify RED with import/function missing.
- [x] Implement the renderer in `template_builder_text_artifacts.py`.
  - Normalize `subtitleText` and `subtitleBox`.
  - Use `oneLineY`, `twoLineFirstY`, `twoLineSecondY`, and `subtitleBox.box.height/paddingX`.
  - Render each line into a transparent line image with subtitleText style and subtitleBox box style.
  - Compose line images into one transparent group PNG.
- [x] Add plugin job mode `template_builder_subtitle_artifact` in `app.py`.
- [x] Run focused Python tests.

## Task 2: NestJS Warm Session And Subtitle API

- [x] Add failing Node tests for:
  - `TemplateBuilderTextArtifactWorkerClient.ensureWarm()` calls `PluginHost.ensureStarted("clipper1_video_render")`.
  - `TemplateBuilderTextArtifactService.renderSubtitle(...)` submits `mode: "template_builder_subtitle_artifact"` and caches identical requests.
- [x] Run `npm run build && node --test test/template-builder-text-artifact.test.js` and verify RED.
- [x] Implement `ensureWarm()`, subtitle worker request/response types, service cache key, and endpoint:
  - `POST /template-builder/preview/renderer-session`
  - `POST /template-builder/families/:familyId/variants/:ratio/preview/subtitle-artifact`
- [x] Run NestJS build/tests.

## Task 3: Angular Warmup And Combined Subtitle Preview

- [x] Add failing Angular service tests for `ensureTextPreviewRendererSession()` and `renderSubtitlePreviewArtifact(...)`.
- [x] Add failing page/editor tests:
  - page warms renderer after load,
  - page requests subtitle artifact in background refresh,
  - editor displays `[data-testid="canvas-subtitle-artifact"]` and does not render duplicate browser subtitle line boxes when artifact exists.
- [x] Run focused Karma tests and verify RED.
- [x] Implement service methods, page warmup/background refresh, editor subtitle artifact display, and fallback behavior.
- [x] Run Angular build/focused tests.

## Task 4: Documentation And Verification

- [x] Update `.codex/session-logs/2026-05-09.log`, `.codex/implementation/NEXT_SESSION_PROMPT.md`, and `.codex/implementation/PREVIEW_FINAL_RENDER_PARITY_PLAN_2026-05-09.md`.
- [x] Run:
  - `clipper_python uv run pytest tests/test_template_builder_subtitle_artifacts.py tests/test_clipper1_video_render_text_artifact_job.py tests/test_template_builder_text_artifacts.py`
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-text-artifact.test.js test/template-builder-render-contract.test.js test/template-builder-api.test.js`
  - `clipper_angular npm run build`
  - `clipper_angular npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts --include=src/features/template-builder/pages/template-builder-page.component.spec.ts`
  - `git diff --check` in each repo.
- [x] Commit each repo and record commits/remaining risk.

## Task 5: Local Worker Smoke

- [x] Start `clipper1_video_render` on `127.0.0.1:54823` and NestJS on `127.0.0.1:9019`.
- [x] Verify `POST /v1/template-builder/preview/renderer-session` reaches the live plugin host.
  - HTTP 201, `time_total=0.023639`.
- [x] Verify combined subtitle artifact endpoint against `system.legacy.clipper1.template.1`, ratio `16:9`.
  - First request: HTTP 201, `time_total=0.068961`, `cached=false`, worker `renderMs=7.168`, `lines=2`, `clipped=false`.
  - Concurrent identical request: HTTP 201, `time_total=0.064150`, `cached=true`.
  - Sequential cache hit: HTTP 201, `time_total=0.003192`, `cached=true`.
  - Warm new-text request: HTTP 201, `time_total=0.058364`, `cached=false`, worker `renderMs=4.712`.
- [x] Stop smoke processes and confirm no listeners remain on `54823` or `9019`.
