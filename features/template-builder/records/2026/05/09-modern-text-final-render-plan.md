# Modern Text Final Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Template Builder sample/final render consume the same modern text artifacts that artifact-backed preview uses.

**Architecture:** NestJS keeps the Template Builder render contract attached to the legacy Clipper1 payload so Python can recognize custom Template Builder renders. Python `LocalRenderAdapter` keeps existing Clipper1 legacy templates on the compatibility path, but when a Template Builder render contract is present it renders title/subtitle text through `template_builder_text_artifacts.py` and feeds those PNGs into the existing FFmpeg overlay chain.

**Tech Stack:** NestJS 10 legacy payload mapper, Python `clipper1_video_render`, pytest, Node test runner, FFmpeg overlay pipeline.

---

## File Structure

- `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
  - Add optional `template_builder_render_contract` to the legacy payload.
  - Preserve the exact render contract already used by preview/sample/published preset paths.
- `clipper_nestjs/test/template-builder-sample-render-fixture.test.js`
  - Prove exported sample render fixture includes `legacy_payload.template_builder_render_contract`.
- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - Detect Template Builder render contracts.
  - Render project text layers and timed subtitle text as modern Template Builder text artifacts.
  - Keep legacy Clipper1 payloads on the current legacy text-image path.
- `clipper_python/tests/test_clipper1_video_render_template_styles.py`
  - Add focused unit coverage for Template Builder modern overlay asset generation.
- `.codex/session-logs/2026-05-09.log`
  - Record decisions, RED/GREEN results, diagnostic numbers, and commits.

## Task 1: Carry Render Contract Into Legacy Payload

- [x] Add a failing Node assertion that `legacy_payload.json` contains `template_builder_render_contract.schemaVersion === "template-builder-render-contract.v1"`.
- [x] Run `clipper_nestjs npm run build` and `node --test test/template-builder-sample-render-fixture.test.js` to verify RED.
  - Observed RED: `Cannot read properties of undefined (reading 'schemaVersion')`.
- [x] Add optional `template_builder_render_contract` to `LegacyClipper1RenderPayload` and populate it from `templateBuilderRenderContractFor(...)` when available.
- [x] Run the same NestJS build/test to verify GREEN.
  - Observed GREEN: 2 fixture tests passed.

## Task 2: Python Modern Template Builder Overlay Assets

- [x] Add a failing pytest that calls `LocalRenderAdapter()._write_overlay_assets_for_clip(...)` with a payload containing `template_builder_render_contract`.
- [x] The test should expect:
  - project layers become roles `template_builder:subTitle`, `template_builder:mainTitleLine1`, `template_builder:mainTitleLine2`, and `template_builder:bottomTitle`,
  - subtitle text becomes one role `template_builder:subtitleText:0`,
  - overlay x/y match each artifact metadata frame,
  - no legacy per-line subtitle role such as `subtitle_0_0` is produced.
- [x] Verify RED.
  - Observed RED: roles were legacy `main_title1`, `main_title2`, `bottom_title`, `subtitle_0_0`, `subtitle_0_1`.
- [x] Implement the modern branch using `render_template_builder_text_artifact()` and `render_template_builder_subtitle_artifact()`.
- [x] Run focused Python tests to verify GREEN.
  - Observed GREEN: focused test passed.

## Task 3: Regression And Diagnostic

- [x] Run legacy text overlay tests to ensure non-Template Builder payloads still use the legacy path.
  - `uv run pytest tests/test_clipper1_video_render_template_styles.py -q`: 28 passed.
- [x] Regenerate sample render fixture, render MP4, inject text artifacts into preview screenshot, and compare preview screenshot vs sample render frame with `--channel-tolerance 4`.
  - Output root: `/tmp/template-builder-modern-final-text-20260509`.
  - Overall mismatchRatio: `0.010823902606310014`.
- [x] Record whether `text:subtitleText` drops now that both preview and sample/final render use the modern combined subtitle artifact path.
  - Overall mismatch dropped from `0.027445558984910835` to `0.010823902606310014`.
  - `text:subtitleText` remained high at `0.9865079365079366` because the category rect is now the tight modern subtitle artifact group, so most sampled pixels are glyph/box edge pixels after video encode and frame scaling.
- [x] Update `.codex/features/template-builder/records/2026/05/09-preview-final-render-parity-plan.md`, `.codex/handoff/NEXT.md`, and session log.

## Task 4: Commit

- [x] Run `git diff --check` in changed repos.
- [x] Commit NestJS and Python changes separately with focused messages.
  - `clipper_nestjs` `8b06e1f feat: carry template builder render contract`
  - `clipper_python` `ce79935 feat: render template builder text artifacts in final output`
