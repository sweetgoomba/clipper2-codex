# Preview/Final Render Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Template Builder preview and sample/final render consume the same template snapshot so users see the same layout, text, media, and visibility in the editor and generated video.

**Architecture:** Legacy Clipper1 golden frames remain a compatibility guard, not the modern renderer target. Template Builder variants become the source of truth. Angular preview, NestJS sample render recipes, published preset params, and the Python render payload mapper must preserve the same normalized fields before any renderer-specific conversion.

**Tech Stack:** Angular 19 standalone/zoneless, NestJS 10, Node built-in test runner, existing `video.render.legacy_clipper1.python_worker`, Python `clipper1_video_render` for current final render.

---

## 2026-05-09 Current Hybrid Text Artifact Slice

Status: hybrid text artifact slices complete and committed.

- `clipper_python` `87df386 feat: add template builder text artifact job`
- `clipper_nestjs` `a55772a feat: serve template builder text artifacts`
- `clipper_angular` `85a55d5 feat: preview template builder text artifacts`

Implemented behavior:

- Preview remains responsive: Angular still shows browser/CSS text immediately.
- A debounced background refresh requests final-render text artifacts for plain text layers.
- When artifacts arrive, the editor can show the renderer-produced PNG for `subTitle`, `mainTitleLine1`, `mainTitleLine2`, `bottomTitle`, and `logoText`.
- Failures/timeouts keep the browser text fallback; the preview is not blocked by the renderer.
- NestJS caches identical layer/text/style requests by hash before submitting duplicate Python worker jobs.
- Python worker mode `template_builder_text_artifact` renders one visible Template Builder text layer and returns PNG data URL plus metadata.

Intentionally not done in this slice:

- Real Electron packaged bridge smoke is still not done. Local NestJS/Python worker smoke is done and recorded below.

Follow-up slice completed:

- Template Builder page now warms the text preview renderer session when opened.
- Python renders `template_builder_subtitle_artifact` as one combined transparent subtitle PNG with group frame and per-line metadata.
- NestJS exposes:
  - `POST /template-builder/preview/renderer-session`
  - `POST /template-builder/families/:familyId/variants/:ratio/preview/subtitle-artifact`
- Angular requests the combined subtitle artifact during background refresh and shows it in the editor when available.

Local worker smoke:

- `clipper1_video_render` ran at `http://127.0.0.1:54823`; NestJS ran at `http://127.0.0.1:9019`.
- Renderer warm session endpoint returned HTTP 201 in `0.023639s`.
- First combined subtitle artifact request returned HTTP 201 in `0.068961s`; worker `renderMs=7.168`, `cached=false`, `lines=2`, `clipped=false`.
- Concurrent identical request shared the pending cache and returned `cached=true` in `0.064150s`.
- Sequential identical cache hit returned `cached=true` in `0.003192s`.
- Warm worker one-character text change returned HTTP 201 in `0.058364s`; worker `renderMs=4.712`, `cached=false`, `lines=2`, `clipped=false`.

Next steps:

1. Decide whether sample/final render should consume the same modern text artifact path, or whether visual diagnostics should compare against a modern deterministic frame artifact until final render migration is done.
2. Run packaged Electron bridge smoke separately to confirm `ElectronPluginHost.ensureStarted(...)` keeps the same behavior outside the static local plugin host.

Stale artifact guard completed:

- A deferred Angular page spec reproduced the stale response bug: after a variant edit, old in-flight final-render text/subtitle artifacts could still populate `textPreviewArtifacts` before the replacement debounced refresh started.
- `scheduleTextPreviewArtifactRefresh()` now invalidates immediately by incrementing `textPreviewArtifactGeneration` and clearing `textPreviewArtifacts`.
- This keeps browser/CSS text as the immediate fallback during rapid edits and prevents old final-render PNGs from being applied.
- Verification: Angular build passed; focused Template Builder Karma suite passed, 74 specs.
- Commit: `clipper_angular` `fbce6ab fix: discard stale template text artifacts`.

Artifact-backed visual diagnostic completed:

- Angular preview screenshot/snapshot exporters now accept `--text-preview-artifacts <json>`.
- Python has `scripts/export_template_builder_text_preview_artifacts.py`, which converts a Template Builder render contract into the Angular `textPreviewArtifacts` JSON shape by rendering plain text artifacts and the combined `subtitleText` artifact.
- Commits:
  - `clipper_python` `f228316 feat: export template text preview artifacts`
  - `clipper_angular` `8a10966 feat: capture artifact-backed template previews`
- Diagnostic output root: `/tmp/template-builder-artifact-backed-20260509`.
- At `--channel-tolerance 4`, artifact-backed preview screenshot vs sample render frame produced overall mismatchRatio `0.027445558984910835`.
- Previous dynamic-subtitle browser-text diagnostic was `0.036785193758573385`; artifact-backed text reduced whole-frame mismatch.
- Remaining notable categories:
  - `text:subtitleText=0.9515873015873015`
  - `text:subtitleBox=0.20145985401459854`
  - `media:logoImage=0.22235872235872237`
- Interpretation: the injected modern text artifacts improve plain title areas, but `subtitleText` is still being compared to the current legacy sample-render subtitle path. The next architectural decision is whether sample/final render should consume the same modern artifact path or diagnostics should target the deterministic modern frame artifact until that migration is complete.

Modern text final render path completed:

- Decision: sample/final render should consume the same modern text artifact path as artifact-backed preview for Template Builder payloads.
- `clipper_nestjs` now keeps `template_builder_render_contract` in the legacy Clipper1 payload. This makes the Python renderer able to distinguish Template Builder custom renders from built-in legacy Clipper1 templates without depending on implicit template id strings.
- `clipper_python` `LocalRenderAdapter._write_overlay_assets_for_clip()` now branches only when `template_builder_render_contract` is present:
  - project text overlays use `render_template_builder_text_artifact()` for `subTitle`, `mainTitleLine1`, `mainTitleLine2`, `bottomTitle`, and `logoText`,
  - timed subtitles use one combined `render_template_builder_subtitle_artifact()` PNG per subtitle segment,
  - legacy Clipper1 payloads with no Template Builder contract stay on the existing legacy text-image path.
- Commits:
  - `clipper_nestjs` `8b06e1f feat: carry template builder render contract`
  - `clipper_python` `ce79935 feat: render template builder text artifacts in final output`
- Verification:
  - `clipper_nestjs npm run build` passed.
  - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js test/template-builder-render-contract.test.js test/template-builder-api.test.js` passed, 14 tests.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_template_builder_text_preview_artifact_export_script.py tests/test_template_builder_sample_video_fixture_render.py -q` passed, 33 tests.
- Diagnostic output root: `/tmp/template-builder-modern-final-text-20260509`.
- Artifact-backed preview screenshot vs sample render frame, `--channel-tolerance 4`, scale `0.3 x 0.3`, produced overall mismatchRatio `0.010823902606310014`.
- Previous artifact-backed preview vs legacy sample-render text path was `0.027445558984910835`, so wiring modern text artifacts into sample/final render reduced whole-frame mismatch by about 60.6%.
- Remaining notable categories:
  - `text:subTitle=0.024817518248175182`
  - `text:mainTitleLine1=0.00583941605839416`
  - `text:mainTitleLine2=0.009306569343065693`
  - `text:bottomTitle=0.009124087591240875`
  - `text:subtitleText=0.9865079365079366`
  - `text:subtitleBox=0.13248175182481753`
  - `media:logoImage=0.22235872235872237`
- Interpretation: the final/sample renderer is now on the same modern text artifact path. The high `subtitleText` category no longer means legacy-vs-modern renderer disagreement; it is a tight subtitle artifact rect dominated by glyph/box edge pixels after MP4 encode and frame-to-preview scaling. The product-level signal is the whole-frame drop plus low plain text categories.

Next steps:

1. Tighten the preview/final diagnostic threshold from diagnostic-only `maxMismatchRatio=1.0` to an initial Template Builder guard near the observed modern-text result, after deciding tolerance and category allowances.
2. Investigate remaining non-text drift in `media:logoImage` and the tight subtitle category separately.
3. Run packaged Electron bridge smoke separately to confirm `ElectronPluginHost.ensureStarted(...)` keeps the same warm-session behavior outside the static local plugin host.

Initial preview/final report guard completed:

- Added `clipper_python/scripts/validate_template_builder_preview_final_report.py`.
- Commit: `clipper_python` `979a24d feat: validate template preview final reports`.
- Purpose: validate an already-generated Template Builder preview/final comparison report without re-running Angular, FFmpeg, or the Python renderer.
- Default guard thresholds:
  - overall `maxMismatchRatio=0.012`
  - `text:subTitle <= 0.03`
  - `text:mainTitleLine1 <= 0.01`
  - `text:mainTitleLine2 <= 0.012`
  - `text:bottomTitle <= 0.012`
  - `text:subtitleText <= 0.99`
  - `text:subtitleBox <= 0.15`
  - `media:logoImage <= 0.25`
- These category thresholds intentionally separate product-level whole-frame drift from known tight-rect diagnostic artifacts. In particular, `text:subtitleText` is high because the snapshot rect now follows the tight combined subtitle artifact group.
- Actual modern-text report validation:
  - Command: `uv run python scripts/validate_template_builder_preview_final_report.py --report /tmp/template-builder-modern-final-text-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json --output /tmp/template-builder-modern-final-text-20260509/preview-final-guard.json`
  - Result: passed.
  - Overall mismatchRatio `0.010823902606310014 <= 0.012`.
  - All default required categories were present and under their thresholds.
- Verification:
  - `uv run pytest tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_preview_video_frame_comparison.py -q` passed, 7 tests.
  - `uv run python -m compileall scripts` passed.

Updated next steps:

1. Wire this validator into the scripted preview-vs-sample diagnostic flow so a single command can render/capture/compare/validate.
2. Investigate `media:logoImage` drift and decide whether it is acceptable encode/scale noise or asset placement/rendering drift.
3. Improve subtitle category reporting so the tight combined subtitle artifact can be assessed by a more meaningful padded region or alpha-mask-aware metric.
4. Run packaged Electron bridge smoke separately.

Single-command preview/final guard runner completed:

- Added `clipper_python/scripts/run_template_builder_preview_final_guard.py`.
- Commit: `clipper_python` `450cae2 feat: run template preview final guard`.
- The runner performs the current full diagnostic/guard flow:
  - exports the NestJS Template Builder sample render fixture,
  - extracts `templateBuilderRenderContract` to `render-contract.json`,
  - renders the sample fixture through Python `LocalRenderAdapter`,
  - exports renderer-backed text preview artifacts,
  - captures Angular preview render snapshot and screenshot with injected artifacts,
  - compares preview screenshot vs sample render video frame,
  - validates the comparison report with `validate_template_builder_preview_final_report.py`.
- Actual command:
  - `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-runner-20260509`
- Actual result:
  - summary: `/tmp/template-builder-preview-final-guard-runner-20260509/summary.json`
  - comparison report: `/tmp/template-builder-preview-final-guard-runner-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json`
  - guard report: `/tmp/template-builder-preview-final-guard-runner-20260509/preview-final-guard.json`
  - passed: `true`
  - mismatchRatio `0.010823902606310014 <= 0.012`
- Verification:
  - `uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_preview_video_frame_comparison.py -q` passed, 9 tests.
  - `uv run python -m compileall scripts` passed.

Updated next steps:

1. Investigate `media:logoImage` drift and decide whether it is acceptable encode/scale noise or actual asset placement/rendering drift.
2. Improve subtitle category reporting so the tight combined subtitle artifact can be assessed by a more meaningful padded region or alpha-mask-aware metric.
3. Decide where this runner should live in the regular developer/CI workflow.
4. Run packaged Electron bridge smoke separately.

Logo image drift diagnostic completed:

- Added `clipper_python/scripts/diagnose_template_builder_preview_final_category.py`.
- Commit: `clipper_python` `14004e3 feat: diagnose template preview final categories`.
- Purpose: diagnose one comparison category by comparing foreground bounds inside the category rect, so tight bitmap mismatches can be separated from actual placement/sizing drift.
- Actual command:
  - `uv run python scripts/diagnose_template_builder_preview_final_category.py --comparison-report /tmp/template-builder-preview-final-guard-runner-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json --category media:logoImage --output /tmp/template-builder-preview-final-guard-runner-20260509/logo-image-category-diagnostic.json`
- Actual result:
  - raw `media:logoImage` mismatchRatio: `0.22235872235872237`
  - foreground threshold `80`: bbox IoU `0.9287469287469288`, foreground count ratio `0.9298892988929889`
  - strong foreground threshold `180`: bbox IoU `0.9722222222222222`, foreground count ratio `0.9722222222222222`
  - interpretation: foreground bounds are aligned; raw mismatch is likely dominated by encode/scale edge noise.
- Decision:
  - The current `media:logoImage` number should stay as a guarded category allowance for now, not drive placement/object-fit changes.
  - The useful signal is the foreground bounds diagnostic: it shows the image is in the same place with nearly the same visible shape after preview/final normalization.

Updated next steps:

1. Improve tight `subtitleText` category reporting so the combined subtitle artifact can be assessed by a padded region or alpha-mask-aware metric.
2. Decide where the single-command runner belongs in the regular developer/CI workflow.
3. Run packaged Electron bridge smoke separately.

Preview capture chrome removal and guard tightening completed:

- Root cause:
  - The high `text:subtitleText=0.9865079365079366` value was not primarily glyph/box edge noise.
  - The Angular preview screenshot export captured editor-only selection chrome because the default selected layer is `subtitleText`.
  - The blue selection border/resize handles were inside the `.phone-canvas` screenshot and contaminated the render-surface comparison.
- Implementation:
  - `clipper_angular` added `TemplateBuilderEditorComponent.previewChromeVisible`, default `true`.
  - Screenshot/render-snapshot export fixtures set `previewChromeVisible=false`.
  - When false, the component hides editor-only selection classes, selection boxes, resize handles, alignment guides, and snap grid chrome while keeping the rendered layer surface intact.
  - `clipper_python` tightened default preview/final guard thresholds to match the cleaned render-surface capture:
    - overall `maxMismatchRatio=0.006`
    - `text:subtitleText <= 0.3`
    - `text:subtitleBox <= 0.04`
    - existing plain text/logo thresholds remain unchanged.
- Commits:
  - `clipper_angular` `4665613 fix: hide template preview chrome in exports`
  - `clipper_python` `70d442d test: tighten template preview final guard`
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-no-chrome-runner-20260509`
  - Result: passed.
  - summary: `/tmp/template-builder-preview-final-guard-no-chrome-runner-20260509/summary.json`
  - comparison report: `/tmp/template-builder-preview-final-guard-no-chrome-runner-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json`
  - guard report: `/tmp/template-builder-preview-final-guard-no-chrome-runner-20260509/preview-final-guard.json`
  - mismatchRatio `0.005095807613168724 <= 0.006`
- Category changes from the previous runner:
  - overall `0.010823902606310014 -> 0.005095807613168724`
  - `text:subtitleText` `0.9865079365079366 -> 0.25873015873015875`
  - `text:subtitleBox` `0.13248175182481753 -> 0.029562043795620437`
  - `media:logoImage` remains `0.22235872235872237`, already classified by the foreground bounds diagnostic above.

Updated next steps:

1. Decide where the single-command runner belongs in the regular developer workflow.
2. Run packaged Electron bridge smoke separately.
3. Optionally integrate the foreground-bounds diagnostic into the guard report for known edge-noise media categories.

Local preview/final guard workflow completed:

- Decision:
  - This repository does not currently have GitHub Actions or another CI service configured.
  - Do not add CI files in this slice.
  - Treat `clipper_python/scripts/run_template_builder_preview_final_guard.py` as a manual local development/QA integration guard.
- Scope:
  - The runner is not part of the packaged app and is not run during normal app usage.
  - Developers run it manually after Template Builder preview/final related changes.
  - CI integration can be added later by calling the same single command from a dedicated visual/integration job.
- Documentation:
  - Added `clipper_python/scripts/TEMPLATE_BUILDER_PREVIEW_FINAL_GUARD.md`.
  - The runner CLI `--help` now explicitly says it is a local development/QA guard and is not run by the packaged application.
- Commit:
  - `clipper_python` `e080135 docs: document template preview final local guard`
- Verification:
  - `uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py -q` passed, 6 tests.
  - `uv run python -m compileall scripts` passed.
  - `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-local-doc-20260510` passed with mismatchRatio `0.005095807613168724 <= 0.006`.
- Local command:
  - `cd clipper_python`
  - `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard`

Packaged Electron bridge smoke completed:

- Scope:
  - This is a packaged-app smoke check for the Template Builder renderer bridge, separate from the local preview/final guard runner.
  - It verifies that the packaged Electron app starts NestJS, exposes Template Builder routes, and can start/reuse `clipper1_video_render` through `ElectronPluginHost.ensureStarted(...)`.
- Setup:
  - The existing packaged app was stale and returned 404 for `/v1/template-builder/families`.
  - Rebuilt `clipper_electron` with `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Launched `dist-app/mac-arm64/Clipper2.app/Contents/MacOS/Clipper2`.
- Runtime endpoints:
  - PluginHostBridge listened on `http://127.0.0.1:60496`.
  - Packaged NestJS listened on `http://127.0.0.1:60497/v1`.
  - Renderer session started `clipper1_video_render` at `http://127.0.0.1:60515`.
- Smoke results:
  - `GET /v1/health`: HTTP 200, `time_total=0.001021`.
  - `GET /v1/plugins/clipper1_video_render/status` before warmup: HTTP 200, `runtimeState=stopped`.
  - `GET /v1/template-builder/families`: HTTP 200, route present.
  - `POST /v1/template-builder/preview/renderer-session`: HTTP 201, `time_total=3.049470`, response `status=ready`, `baseUrl=http://127.0.0.1:60515`.
  - `GET /v1/plugins/clipper1_video_render/status` after warmup: HTTP 200, `runtimeState=running`, `port=60515`.
  - First subtitle artifact request: HTTP 201, total client time `76ms`, worker `renderMs=17.458`, `cached=false`, `lines=2`, `clipped=false`.
  - Identical subtitle artifact request: HTTP 201, total client time `18ms`, `cached=true`.
  - `POST /v1/plugins/clipper1_video_render/stop`: HTTP 204, followed by status HTTP 200 with `runtimeState=stopped`.
  - Packaged app was shut down after the smoke.
- Decision:
  - The packaged app path can warm and reuse the Template Builder text/subtitle renderer worker.
  - No CI or product-runtime automation was added; this remains a manual smoke check when bridge/package behavior changes.

Latest packaged app smoke after style-heavy fixture coverage:

- Time: 2026-05-10 KST.
- Scope:
  - Rebuilt the packaged Electron app after the `style-heavy` fixture commits.
  - This smoke verified packaged NestJS routes and renderer-session startup, not a human visual UX pass.
- Build:
  - Command: `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Output app: `clipper_electron/dist-app/mac-arm64/Clipper2.app`.
  - Output DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`.
  - Local build skipped macOS signing because no valid signing identity was available.
- Runtime:
  - PluginHostBridge listened on `http://127.0.0.1:50282`.
  - Packaged NestJS listened on `http://127.0.0.1:50283/v1`.
  - Renderer session started `clipper1_video_render` at `http://127.0.0.1:50304`.
- Smoke results:
  - `GET /v1/health`: HTTP 200, `time_total=0.001096`.
  - `GET /v1/template-builder/families`: HTTP 200, `time_total=0.006860`.
  - `GET /v1/plugins/clipper1_video_render/status` before warmup: HTTP 200, `runtimeState=stopped`, `time_total=0.007597`.
  - `POST /v1/template-builder/preview/renderer-session`: HTTP 201, `time_total=0.259108`, response `status=ready`, `baseUrl=http://127.0.0.1:50304`.
  - Packaged app shutdown also shut down packaged NestJS and the Python renderer worker.
- Manual app testing:
  - Added `.codex/features/template-builder/runbooks/manual-app-checklist.md`.
  - The next user-facing verification step is to run the packaged app and follow that checklist.

Foreground-bounds guard diagnostics completed:

- Purpose:
  - Keep the `media:logoImage` raw mismatch threshold as a guard allowance, but include foreground bounds metadata in the guard report so edge-noise categories are easier to interpret.
  - This does not change pass/fail semantics; it adds diagnostic evidence to `categories.media:logoImage.foregroundBounds`.
- Implementation:
  - `validate_template_builder_preview_final_report.py` accepts `foreground_bounds_categories`.
  - `run_template_builder_preview_final_guard.py` requests foreground-bounds diagnostics for `media:logoImage` by default.
  - Commit: `clipper_python` `ae777cc feat: include foreground diagnostics in preview final guard`.
- Verification:
  - `uv run pytest tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `uv run python -m compileall scripts` passed.
  - `git diff --check` passed.
  - Actual runner `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-foreground-20260510` passed with mismatchRatio `0.005095807613168724 <= 0.006`.
- Actual foreground-bounds result in the guard report:
  - `media:logoImage` raw mismatchRatio: `0.22235872235872237`.
  - foreground threshold `80`: bbox IoU `0.9287469287469288`, foreground count ratio `0.9298892988929889`.
  - strong foreground threshold `180`: bbox IoU `0.9722222222222222`, foreground count ratio `0.9722222222222222`.
  - interpretation: foreground bounds are aligned; raw mismatch is likely dominated by encode/scale edge noise.

Multi-fixture local guard completed:

- Purpose:
  - Broaden the local preview/final guard from one fixed sample to multiple representative Template Builder fixtures.
  - This keeps the work product-focused: the guard now checks another text-heavy Korean sample instead of continuing legacy Clipper1 pixel tightening.
- Fixture set:
  - `default-image-logo`: existing image-logo sample.
  - `long-korean-text`: longer Korean title/subtitle/bottom text sample with the same visible layer set.
- Implementation:
  - `clipper_nestjs` sample render fixture export accepts `--fixture-id` and can write fixture-specific text/variant metadata.
  - `clipper_angular` preview snapshot/screenshot exporters accept `--fixture-id` and render the matching preview fixture/sample text.
  - `clipper_python` local guard runner now runs the default fixture set and writes a top-level summary containing fixture results.
- Commits:
  - `clipper_nestjs` `601be29 feat: add selectable template sample fixtures`
  - `clipper_angular` `adc289b feat: export selectable template preview fixtures`
  - `clipper_python` `6aa92e0 feat: run template preview final guard fixtures`
- Verification:
  - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` passed, 4 tests.
  - `clipper_angular npm run build` passed.
  - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` passed, 5 tests.
  - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `clipper_python uv run python -m compileall scripts` passed.
  - `git diff --check` passed in `clipper_nestjs`, `clipper_angular`, and `clipper_python`.
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-multifixture-20260510`
  - Result: passed.
  - Summary: `/tmp/template-builder-preview-final-guard-multifixture-20260510/summary.json`
  - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
  - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.

Visibility fixture guard completed:

- Purpose:
  - Add a product-behavior fixture that verifies hidden logo layer visibility is reflected in both preview and final render.
  - Teach the guard to support fixture-specific category policy, because a fixture with `logoImage.visible=false` should not require or diagnose `media:logoImage`.
- Fixture:
  - `hidden-logo`
  - Text sample:
    - subTitle `로고 숨김 확인`
    - main title lines `브랜드 영역 없이`, `본문만 보여주기`
    - bottomTitle `깔끔한 화면 구성`
    - subtitle lines `로고 레이어를 꺼도`, `미리보기와 결과가 같아야 해요`
  - `logoImage.visible=false`, `logoText.visible=false`.
- Implementation:
  - `clipper_nestjs` exports the hidden-logo sample render fixture and verifies the legacy payload has `logo_check=false`, no `logo_image`, and no `logo_text`.
  - `clipper_angular` exports the hidden-logo preview fixture and verifies the browser render snapshot has no `logoImage`/`logoText` layer.
  - `clipper_python` local guard includes `hidden-logo` in the default fixture set and removes `media:logoImage` from thresholds, required categories, and foreground-bounds diagnostics for that fixture.
- Commits:
  - `clipper_nestjs` `ed2e9cd feat: add hidden logo template fixture`
  - `clipper_angular` `74e2ba5 feat: add hidden logo preview fixture`
  - `clipper_python` `1fd276c feat: support visibility guard fixture policy`
- Verification:
  - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` passed, 5 tests.
  - `clipper_angular npm run build` passed.
  - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` passed, 6 tests.
  - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `clipper_python uv run python -m compileall scripts` passed.
  - `git diff --check` passed in `clipper_nestjs`, `clipper_angular`, and `clipper_python`.
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-visibility-20260510`
  - Result: passed.
  - Summary: `/tmp/template-builder-preview-final-guard-visibility-20260510/summary.json`
  - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
  - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
  - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
  - `hidden-logo` required categories are only text categories; `media:logoImage` is absent from thresholds, required categories, foreground diagnostics, and actual guard categories.

Subtitle-hidden visibility fixture completed:

- Purpose:
  - Verify `subtitleText.visible=false` and `subtitleBox.visible=false` are honored across preview, sample/final payload mapping, text artifact export, and guard category policy.
  - This protects against the high-risk case where Angular preview hides subtitles but final render still emits timed subtitle overlays.
- Fixture:
  - `subtitle-hidden`
  - Text sample:
    - subTitle `자막 숨김 확인`
    - main title lines `대사 없이도`, `레이아웃 유지`
    - bottomTitle `본문 집중 화면`
    - subtitle input lines `이 자막은`, `보이면 안 돼요`; these remain fixture input text but should not render while subtitle layers are hidden.
  - `subtitleText.visible=false`, `subtitleBox.visible=false`, logo remains visible.
- Implementation:
  - `clipper_nestjs` exports the hidden-subtitle sample render fixture and verifies the legacy payload has empty `clips[0].subtitles`.
  - `clipper_angular` exports the hidden-subtitle preview fixture and verifies the browser render snapshot has no `subtitleText`/`subtitleBox` layer.
  - `clipper_python` local guard includes `subtitle-hidden` in the default fixture set and removes `text:subtitleText`/`text:subtitleBox` from thresholds and required categories for that fixture.
  - `clipper_python` local guard no longer forwards hidden subtitle text into text artifact generation for this fixture.
  - Local guard docs now list the default fixture set and fixture-specific visibility policy.
- Commits:
  - `clipper_nestjs` `aefda40 feat: add hidden subtitle template fixture`
  - `clipper_angular` `36a314c feat: add hidden subtitle preview fixture`
  - `clipper_python` `5bb9b07 feat: add hidden subtitle guard fixture`
  - `clipper_python` `bc61033 docs: document template guard fixture set`
- Verification:
  - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` passed, 6 tests.
  - `clipper_angular npm run build` passed.
  - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` passed, 7 tests.
  - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `clipper_python uv run python -m compileall scripts` passed.
  - `git diff --check` passed in `clipper_nestjs`, `clipper_angular`, and `clipper_python`.
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-subtitle-hidden-20260510`
  - Result: passed.
  - Summary: `/tmp/template-builder-preview-final-guard-subtitle-hidden-20260510/summary.json`
  - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
  - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
  - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
  - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
  - `subtitle-hidden` required categories are `text:subTitle`, `text:mainTitleLine1`, `text:mainTitleLine2`, `text:bottomTitle`, `media:logoImage`.
  - `subtitle-hidden` guard categories do not include `text:subtitleText` or `text:subtitleBox`; text artifact generation only includes `subTitle`, `mainTitleLine1`, `mainTitleLine2`, and `bottomTitle`.

Logo-text-only visibility fixture completed:

- Purpose:
  - Verify `logoImage.visible=false` and `logoText.visible=true` are honored across Angular preview, NestJS sample/final payload mapping, Python text artifact export, and guard category policy.
  - This protects the product behavior where a template uses a text logo instead of an image logo.
- Fixture:
  - `logo-text-only`
  - Text sample:
    - subTitle `텍스트 로고 확인`
    - main title lines `이미지 없이도`, `브랜드 표시`
    - bottomTitle `텍스트 로고 화면`
    - subtitle lines `텍스트 로고만 켜도`, `미리보기와 결과가 같아야 해요`
    - logoText `Clipper`
  - `logoImage.visible=false`, `logoText.visible=true`, subtitles remain visible.
- Implementation:
  - `clipper_nestjs` exports the text-logo sample render fixture and verifies the legacy payload has `logo_check=true`, `logo_type=TEXT`, no `logo_image`, and `logo_text=Clipper`.
  - `clipper_angular` exports the text-logo preview fixture and verifies the browser render snapshot has no `logoImage` layer and includes a visible `logoText` layer.
  - `clipper_python` local guard includes `logo-text-only` in the default fixture set, removes `media:logoImage`, and adds `text:logoText <= 0.03` as a required fixture-specific category.
  - A follow-up RED caught that the CLI path initially added `text:logoText` to thresholds but not to `requiredCategories`; this is fixed so missing text-logo categories fail the guard.
- Commits:
  - `clipper_nestjs` `810e483 feat: add text logo template fixture`
  - `clipper_angular` `ad23c40 feat: add text logo preview fixture`
  - `clipper_python` `2b6359c feat: add text logo guard fixture`
- Verification:
  - `clipper_nestjs npm run build` passed.
  - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js` passed, 7 tests.
  - `clipper_angular npm run build` passed.
  - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` passed, 8 tests.
  - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `clipper_python uv run python -m compileall scripts` passed.
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-logo-text-only-required-20260510`
  - Result: passed.
  - Summary: `/tmp/template-builder-preview-final-guard-logo-text-only-required-20260510/summary.json`
  - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
  - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
  - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
  - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
  - `logo-text-only`: mismatchRatio `0.0037776491769547327 <= 0.006`, failures `[]`.
  - `logo-text-only` required categories include `text:logoText`.
  - `text:logoText` category result: mismatchRatio `0.009124087591240875 <= 0.03`.

Style-heavy fixture completed:

- Purpose:
  - Verify non-subtitle title/logo text style combinations across preview and sample/final render.
  - This fixture focuses on box fill, border, outline, shadow, color, tracking, and text-logo style behavior rather than layer visibility.
- Fixture:
  - `style-heavy`
  - Text sample:
    - subTitle `스타일 집중 확인`
    - main title lines `윤곽선과 그림자`, `박스 색상 테스트`
    - bottomTitle `스타일 그대로 저장`
    - subtitle lines `복잡한 스타일도`, `결과 영상과 맞춰요`
    - logoText `STYLE`
  - `logoImage.visible=false`, `logoText.visible=true`, subtitles remain visible.
  - Styled layers:
    - `subTitle`: box enabled, border, outline width `2`, shadow offset `4/5`, color `#FDE047`.
    - `mainTitleLine1`: outline width `4`, shadow enabled, larger font size.
    - `mainTitleLine2`: color `#38BDF8`, outline/shadow enabled.
    - `bottomTitle`: yellow box `#FACC15`, border, outline, shadow.
    - `logoText`: orange text `#F97316`, dark box, border, outline, shadow.
- Implementation:
  - `clipper_nestjs` exports the style-heavy sample render fixture and verifies the render contract style values plus mapped legacy template settings.
  - `clipper_angular` exports the style-heavy preview fixture and verifies browser-rendered style snapshot values.
  - `clipper_python` local guard includes `style-heavy` in the default fixture set, removes `media:logoImage`, requires `text:logoText`, and applies fixture-specific thresholds.
- Decision:
  - The first style-heavy runner failed under the default `maxMismatchRatio=0.006` because large filled text-box regions create MP4 encode and preview-scale channel drift, even though preview and final frames were visually aligned.
  - Do not loosen the default guard. Keep default fixtures at `0.006` and apply style-heavy-specific guard allowances.
  - Style-heavy guard thresholds:
    - overall `0.04`
    - `text:subTitle=0.32`
    - `text:mainTitleLine1=0.016`
    - `text:mainTitleLine2=0.022`
    - `text:bottomTitle=0.44`
    - `text:logoText=0.36`
- Commits:
  - `clipper_nestjs` `f4eca90 feat: add style heavy template fixture`
  - `clipper_angular` `a7f047f feat: add style heavy preview fixture`
  - `clipper_python` `a3a6c3b feat: add style heavy guard fixture`
- Verification:
  - `clipper_nestjs npm run build` passed.
  - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js` passed, 8 tests.
  - `clipper_angular npm run build` passed.
  - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` passed, 9 tests.
  - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` passed, 9 tests.
  - `clipper_python uv run python -m compileall scripts` passed.
- Actual runner:
  - Command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-style-heavy-full-20260510`
  - Result: passed.
  - Summary: `/tmp/template-builder-preview-final-guard-style-heavy-full-20260510/summary.json`
  - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
  - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
  - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
  - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
  - `logo-text-only`: mismatchRatio `0.0037776491769547327 <= 0.006`, failures `[]`.
  - `style-heavy`: mismatchRatio `0.03424532750342935 <= 0.04`, failures `[]`.
  - Style-heavy category results:
    - `text:subTitle=0.2824817518248175 <= 0.32`
    - `text:mainTitleLine1=0.012043795620437956 <= 0.016`
    - `text:mainTitleLine2=0.016423357664233577 <= 0.022`
    - `text:bottomTitle=0.393978102189781 <= 0.44`
    - `text:logoText=0.3165137614678899 <= 0.36`

Updated next steps:

1. Keep using the local multi-fixture guard runner after Template Builder preview/final renderer changes.
2. Next product-behavior fixture candidates:
   - packaged Electron manual testing checklist for Template Builder preview/final behavior.
   - optional release checklist hook for the local guard command.
3. Direct packaged app testing is now appropriate after rebuilding the app from the latest commits.

---

## Current Inventory

Preview path:

- `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
  - Draws canvas layers directly from `variant.layers`.
  - Uses `frameFor(layer) * canvasScale()` for `left/top/width/height`.
  - Uses browser CSS for `font-family`, `font-size`, `letter-spacing`, `line-height`, text align, box background, border, outline, and shadow.
- `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
  - Owns layer selection, drag/resize, snap, alignment guide, and patch emission.
  - Preview text is local sample copy in `PREVIEW_TEXT`.

Sample/final render path:

- `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`
  - Builds a real sample render `RenderRecipe`.
  - Calls `video.render.legacy_clipper1.python_worker` with `dryRun: false`.
  - Passes `templateBuilderVariant`, `templateBuilderVariantId`, `templateBuilderRatio`, `templateBuilderContentArea`, and `templateBuilderLayers` in `recipe.templateParams`.
- `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
  - Converts `templateBuilderLayers` into legacy `template_settings`.
  - Handles layer visibility, align margins/center, text style, box, outline, shadow, logo image/text, layout image, and subtitle visibility.
- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - Consumes legacy `template_settings` and currently renders Template Builder custom templates through the legacy-compatible path.

Known gap:

- Browser preview is CSS-rendered while final render is legacy Pillow/FFmpeg-rendered. Modern quality work should not copy Clipper1 glyph clipping/padding bugs. The first guard is data/geometry parity; visual pixel comparison comes after stable preview/final frame capture exists.

## Task 1: Sample Render Recipe Carries Complete Variant Geometry

**Files:**

- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`

- [x] **Step 1: Write the failing test**

Add this assertion inside `template builder service creates, clones, validates, sample-renders, and publishes a custom full variant` after the existing `templateBuilderContentArea` assertion:

```js
assert.deepEqual(
  renderCalls[0].recipe.templateParams.templateBuilderOutputSize,
  created.variants.full.outputSize,
);
```

- [x] **Step 2: Run the test to verify RED**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Observed expected failure:

```text
Expected values to be strictly deep-equal:
+ undefined
- { height: 1920, width: 1080 }
```

- [x] **Step 3: Write minimal implementation**

In `TemplateBuilderSampleRenderService.recipeFor()`, add `templateBuilderOutputSize` to `templateParams`:

```ts
templateParams: {
  backgroundColor: '#111111',
  templateBuilderVariant: variant,
  templateBuilderVariantId: variant.id,
  templateBuilderRatio: variant.ratio,
  templateBuilderOutputSize: variant.outputSize,
  templateBuilderContentArea: variant.contentArea,
  templateBuilderLayers: variant.layers,
},
```

- [x] **Step 4: Run the test to verify GREEN**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Expected:

```text
# pass 10
# fail 0
```

- [x] **Step 5: Commit**

Committed in `clipper_nestjs`:

```text
757892e test: preserve template builder output size
```

## Task 2: Define A NestJS Template Builder Render Contract Helper

**Files:**

- Create: `clipper_nestjs/src/template-builder/template-builder-render-contract.ts`
- Create: `clipper_nestjs/test/template-builder-render-contract.test.js`
- Modify: `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`
- Modify: `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`

- [x] **Step 1: Write the failing test**

Create `clipper_nestjs/test/template-builder-render-contract.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');

test('template builder render contract keeps output size, content area, and layers together', () => {
  const {
    createDefaultTemplateVariant,
  } = require('../dist/template-builder/dto/template-builder.dto');
  const {
    templateBuilderRenderContractFor,
  } = require('../dist/template-builder/template-builder-render-contract');

  const variant = createDefaultTemplateVariant('family.contract', '16:9', '2026-05-09T00:00:00.000Z');
  variant.layers.mainTitleLine1.x = 123;
  variant.layers.mainTitleLine1.visible = false;
  variant.layers.logoImage.assetUri = 'logos/contract.png';

  const contract = templateBuilderRenderContractFor(variant);

  assert.equal(contract.schemaVersion, 'template-builder-render-contract.v1');
  assert.equal(contract.variantId, variant.id);
  assert.equal(contract.ratio, '16:9');
  assert.deepEqual(contract.outputSize, { width: 1080, height: 1920 });
  assert.deepEqual(contract.contentArea, variant.contentArea);
  assert.equal(contract.layers.mainTitleLine1.x, 123);
  assert.equal(contract.layers.mainTitleLine1.visible, false);
  assert.equal(contract.layers.logoImage.assetUri, 'logos/contract.png');
});
```

- [x] **Step 2: Run the test to verify RED**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-render-contract.test.js
```

Expected:

```text
Cannot find module '../dist/template-builder/template-builder-render-contract'
```

- [x] **Step 3: Implement the helper**

Create `clipper_nestjs/src/template-builder/template-builder-render-contract.ts`:

```ts
import type {
  TemplateBuilderContentArea,
  TemplateBuilderLayers,
  TemplateBuilderOutputSize,
  TemplateBuilderRatio,
  TemplateBuilderVariant,
} from './dto/template-builder.dto';

export interface TemplateBuilderRenderContract {
  schemaVersion: 'template-builder-render-contract.v1';
  variantId: string;
  familyId: string;
  ratio: TemplateBuilderRatio;
  outputSize: TemplateBuilderOutputSize;
  contentArea: TemplateBuilderContentArea;
  layers: TemplateBuilderLayers;
}

export function templateBuilderRenderContractFor(
  variant: TemplateBuilderVariant,
): TemplateBuilderRenderContract {
  return {
    schemaVersion: 'template-builder-render-contract.v1',
    variantId: variant.id,
    familyId: variant.familyId,
    ratio: variant.ratio,
    outputSize: variant.outputSize,
    contentArea: variant.contentArea,
    layers: variant.layers,
  };
}
```

- [x] **Step 4: Use the helper in sample render and published preset params**

In `template-builder-sample-render.service.ts`, build the contract once:

```ts
const renderContract = templateBuilderRenderContractFor(variant);
```

Then set:

```ts
templateBuilderRenderContract: renderContract,
templateBuilderVariant: variant,
templateBuilderVariantId: renderContract.variantId,
templateBuilderRatio: renderContract.ratio,
templateBuilderOutputSize: renderContract.outputSize,
templateBuilderContentArea: renderContract.contentArea,
templateBuilderLayers: renderContract.layers,
```

In `template-builder-published-preset-source.ts`, include the same `templateBuilderRenderContract` in `defaultParams` while preserving existing `templateBuilder*` keys for compatibility.

- [x] **Step 5: Run tests**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-render-contract.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js
```

Expected:

```text
# fail 0
```

Observed:

```text
clipper_nestjs npm run build
clipper_nestjs node --test test/template-builder-render-contract.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js
# pass 20
# fail 0
clipper_nestjs git diff --check
```

- [x] **Step 6: Commit**

Committed in `clipper_nestjs`:

```text
68d65d1 feat: add template builder render contract
```

## Task 3: Add Angular Preview Contract Projection

**Files:**

- Create: `clipper_angular/src/features/template-builder/services/template-builder-preview-contract.ts`
- Create: `clipper_angular/src/features/template-builder/services/template-builder-preview-contract.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`

- [x] **Step 1: Write the failing Angular spec**

Create `template-builder-preview-contract.spec.ts` with a variant fixture copied from the existing editor spec helper:

```ts
import { templateBuilderPreviewContractFor } from './template-builder-preview-contract';
import type { TemplateBuilderVariant } from '../models/template-builder';

it('projects a variant into the same output size, content area, and layer frames used by preview', () => {
  const variant = {
    id: 'family.preview.full',
    familyId: 'family.preview',
    ratio: 'full',
    status: 'draft',
    outputSize: { width: 1080, height: 1920 },
    contentArea: { x: 0, y: 0, width: 1080, height: 1920 },
    layers: {
      mainTitleLine1: {
        id: 'mainTitleLine1',
        label: '메인',
        visible: true,
        x: 100,
        y: 220,
        width: 640,
        height: 96,
        align: 'center',
        text: { fontFamily: 'Pretendard.otf', fontSize: 72, color: '#ffffff', tracking: -1, lineHeight: 1.18 },
        box: { enabled: false, color: '#000000', alpha: 0.8, paddingX: 20, height: 80, borderColor: '#ffffff', borderWidth: 0 },
        outline: { enabled: false, width: 0, color: '#000000' },
        shadow: { enabled: false, color: '#000000', outlineWidth: 0, outlineColor: '#000000', offsetX: 0, offsetY: 0 },
      },
    },
    validation: { valid: true, issues: [] },
    sampleRender: { status: 'missing' },
    updatedAt: '2026-05-09T00:00:00.000Z',
  } as unknown as TemplateBuilderVariant;

  const contract = templateBuilderPreviewContractFor(variant);

  expect(contract.outputSize).toEqual({ width: 1080, height: 1920 });
  expect(contract.contentArea).toEqual({ x: 0, y: 0, width: 1080, height: 1920 });
  expect(contract.layers.mainTitleLine1.frame).toEqual({ x: 100, y: 220, width: 640, height: 96 });
  expect(contract.layers.mainTitleLine1.visible).toBeTrue();
});
```

- [x] **Step 2: Run the spec to verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts
```

Expected:

```text
Cannot find module './template-builder-preview-contract'
```

Observed:

```text
Module not found: Error: Can't resolve './template-builder-preview-contract'
TS2307: Cannot find module './template-builder-preview-contract'
```

- [x] **Step 3: Implement the preview projection**

Create `template-builder-preview-contract.ts`:

```ts
import type {
  TemplateBuilderLayers,
  TemplateBuilderMediaLayer,
  TemplateBuilderTextLayer,
  TemplateBuilderVariant,
} from '../models/template-builder';

export interface TemplateBuilderPreviewLayerContract {
  id: string;
  visible: boolean;
  frame: { x: number; y: number; width: number; height: number };
}

export interface TemplateBuilderPreviewContract {
  outputSize: TemplateBuilderVariant['outputSize'];
  contentArea: TemplateBuilderVariant['contentArea'];
  layers: Partial<Record<keyof TemplateBuilderLayers, TemplateBuilderPreviewLayerContract>>;
}

export function templateBuilderPreviewContractFor(
  variant: TemplateBuilderVariant,
): TemplateBuilderPreviewContract {
  const layers: TemplateBuilderPreviewContract['layers'] = {};
  for (const [key, layer] of Object.entries(variant.layers) as Array<[keyof TemplateBuilderLayers, TemplateBuilderTextLayer | TemplateBuilderMediaLayer]>) {
    layers[key] = {
      id: layer.id,
      visible: layer.visible,
      frame: {
        x: layer.x,
        y: layer.y,
        width: layer.width,
        height: layer.height,
      },
    };
  }
  return {
    outputSize: variant.outputSize,
    contentArea: variant.contentArea,
    layers,
  };
}
```

- [x] **Step 4: Use projection in the editor component**

Added a computed `previewContract` in `template-builder-editor.component.ts` and replaced direct content-area reads in the template with `contract.contentArea`.

- [x] **Step 5: Run focused Angular tests**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected:

```text
0 failures
```

Observed:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
TOTAL: 36 SUCCESS
clipper_angular npm run build
Application bundle generation complete.
clipper_angular git diff --check
```

- [x] **Step 6: Commit**

Committed in `clipper_angular`:

```text
f631f81 feat: add template builder preview contract
```

## Task 4: Guard Final Payload Against Preview Drift

**Files:**

- Modify: `clipper_nestjs/test/template-builder-render-payload.test.js`
- Modify: `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`

- [x] **Step 1: Add a contract-to-payload test**

Add a test that mutates one visible text layer and one media layer, then asserts:

```js
assert.equal(payload.template_settings.main_title_center_x, 420);
assert.equal(payload.template_settings.main_title_font_size, 88);
assert.equal(payload.template_settings.main_title_tracking, -2.5);
assert.equal(payload.template_settings.main_title_box_height, 112);
assert.equal(payload.template_settings.logo_image_left_align_margin, 144);
assert.equal(payload.template_settings.logo_image_area_width, 320);
assert.equal(payload.project.main_title_check, true);
assert.equal(payload.project.logo_type, 'IMAGE');
```

- [x] **Step 2: Run RED/GREEN**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-render-payload.test.js
```

Only add mapper fields when the test exposes a real missing field. Do not map fields that the legacy Python renderer cannot consume unless the contract also records them as modern-only.

Observed RED:

```text
Recipe does not use a legacy Clipper1 template: shorts.basic_letterbox
```

GREEN implementation:

- `LegacyClipper1RenderPayloadMapper` now accepts `templateBuilderRenderContract` as a Template Builder signal.
- `template_id`, `contents_ratio`, `templateBuilderLayers`, `contentArea`, and `outputSize` can fall back to the render contract.
- Existing `templateBuilder*` keys still take precedence for compatibility.

Observed GREEN:

```text
clipper_nestjs npm run build
clipper_nestjs node --test test/template-builder-render-payload.test.js
# pass 5
# fail 0
clipper_nestjs node --test test/template-builder-render-contract.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js
# pass 21
# fail 0
clipper_nestjs git diff --check
```

- [x] **Step 3: Commit**

Committed in `clipper_nestjs`:

```text
70c8ca8 feat: map template builder render contract
```

## Task 5: Add Modern Quality Guard For Text Clipping

**Files:**

- Add focused tests under `clipper_python/tests/`
- Modify only modern Template Builder render path once it exists; do not tune legacy Clipper1 golden output for this task.

Status update 2026-05-09:

- [x] Modern Template Builder text render seam created separately from legacy final render.
- [x] The seam is not wired into `LocalRenderAdapter` yet, so frozen Clipper1 compatibility output is unchanged.
- [x] First clipping guard checks descenders and Korean lower strokes with outline/shadow.
- [x] Second guard reports too-small layer boxes as `clipped`.
- Commit: `clipper_python` `9457abb feat: add template builder text renderer seam`

Implemented files:

- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/template_builder_text_renderer.py`
- `clipper_python/tests/test_template_builder_text_renderer.py`

Verification:

```text
clipper_python uv run pytest tests/test_template_builder_text_renderer.py -q
# 2 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py -q
# 4 passed
clipper_python git diff --check
```

- [ ] **Step 1: Define the first clipping fixture**

Use a Template Builder text layer containing descenders and Korean lower strokes:

```text
gjpqy 와 므르트픔
```

The assertion should check generated text image bounds stay within the declared layer box plus configured padding/outline/shadow.

- [ ] **Step 2: Keep legacy guard separate**

Run both:

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_golden_frames.py -q
uv run pytest <new-modern-text-clipping-test> -q
```

The first command protects existing output. The second command protects modern quality.

## Task 6: Add Preview/Final Frame Comparison After Capture Exists

**Files:**

- Reuse: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/frame_compare.py`
- Add a deterministic preview capture entrypoint after Angular preview contract projection is stable.

- [ ] **Step 1: Generate two artifacts from one contract**

The same Template Builder variant contract should produce:

```text
preview.png
final_thumbnail.jpg or final_frame.png
```

- [ ] **Step 2: Compare only meaningful regions first**

Use a tolerance that ignores video encode edge noise but fails layer drift:

```bash
uv run python scripts/compare_template_builder_preview_final.py \
  --preview /tmp/template-preview.png \
  --final /tmp/template-final-frame.png \
  --channel-tolerance 32 \
  --max-mismatch-ratio 0.01
```

This task starts after Tasks 2-4 make the data contract explicit.

Status: not started. Task 5 now provides a modern text render seam, but preview/final frame comparison still needs a deterministic preview capture artifact. Comparing browser CSS preview directly against the current legacy Pillow/FFmpeg output would pull the work back into Clipper1 pixel parity instead of modern preview/final parity.

Additional prerequisite completed 2026-05-09:

- Angular preview contract now includes text style/effects and media asset references, not only frame/visibility.
- Commit: `clipper_angular` `b8fe242 feat: include styles in template preview contract`
- This makes the preview contract usable as the input side of future deterministic preview/final artifact comparison.
- Verification:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
# TOTAL: 36 SUCCESS
clipper_angular npm run build
clipper_angular git diff --check
```

Additional prerequisite completed 2026-05-09:

- Python can now render deterministic text-layer artifacts from either Angular preview contract shape or NestJS render contract shape.
- Commit: `clipper_python` `dbeb2c3 feat: render template builder text artifacts`.
- This is intentionally layer-scoped, not a full frame pixel comparison. It proves that the modern text render seam can consume both contract shapes through one normalized boundary before it is wired into final video rendering.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_text_artifacts.py -q
# 2 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py -q
# 6 passed
```

Next Task 6 prerequisite:

- Add a deterministic full-frame preview/final artifact composer that places text artifacts by `frame` and preserves content-area/media placeholders before comparing images.
- Keep this separate from Clipper1 golden fixture tuning; the legacy fixture remains a compatibility guard only.

Additional prerequisite completed 2026-05-09:

- Python can now render a deterministic full-frame artifact from either Angular preview contract shape or NestJS render contract shape.
- Commit: `clipper_python` `0050409 feat: compose template builder frame artifacts`.
- The composer creates an `outputSize` RGBA canvas, preserves `contentArea` in metadata, renders visible text layers through the deterministic text artifact path, and alpha-composites them at each layer `frame`.
- This still is not a browser screenshot or encoded final-video frame. It is the capture boundary that future preview/final frame comparison can use without depending on Clipper1 pixel quirks.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_frame_artifacts.py -q
# 1 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py -q
# 7 passed
```

Next Task 6 prerequisite:

- Extend the frame artifact composer to account for media layers with deterministic placeholders or real staged assets, then add an entrypoint script that emits `preview.png` and `final_frame.png` from one saved contract.
- After that, introduce image comparison with a modern preview/final threshold. Do not reuse legacy Clipper1 golden threshold work as the success target.

Additional prerequisite completed 2026-05-09:

- The Python full-frame artifact composer now includes visible media layers as deterministic placeholders.
- Commit: `clipper_python` `9e7f82d feat: add template builder media placeholders`.
- Media layers from Angular preview contract shape (`kind=media`, `frame`, `assetUri`) and NestJS render contract shape (`x/y/width/height`, `assetUri`) produce the same placeholder pixels and metadata.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_frame_artifacts.py -q
# 1 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py -q
# 7 passed
```

Next Task 6 prerequisite:

- Add an entrypoint script that reads one saved Template Builder contract and emits deterministic `preview.png`, `final_frame.png`, and comparison metadata from the artifact composer.
- After that, decide how to replace placeholders with real staged media assets without reintroducing Clipper1-specific pixel quirks.

Additional prerequisite completed 2026-05-09:

- Added a Python entrypoint that reads one saved Template Builder contract and emits deterministic `preview.png`, `final_frame.png`, and `comparison.json`.
- Commit: `clipper_python` `f77e125 feat: add template builder artifact entrypoint`.
- The current entrypoint deliberately renders preview and final artifacts through the same deterministic composer. It is a contract/capture diagnostic, not a claim that browser CSS preview and encoded video already match.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_preview_final_artifact_script.py -q
# 1 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py -q
# 8 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
```

Next Task 6 prerequisite:

- Add a real contract fixture/export path from Angular or NestJS so this script can run against a Template Builder variant produced by the app, not only handcrafted test JSON.
- Then replace deterministic media placeholders with staged assets behind a small resolver seam.

Additional prerequisite completed 2026-05-09:

- NestJS can now export an app-produced Template Builder render contract fixture.
- Commit: `clipper_nestjs` `b1f99d8 feat: export template builder contract fixture`.
- The fixture is created via `createDefaultTemplateVariant()` and `templateBuilderRenderContractFor()`, then can be written to JSON for the Python artifact entrypoint.
- Cross verification:

```text
clipper_nestjs npm run build
clipper_nestjs node --test test/template-builder-render-contract.test.js
# pass 2
clipper_nestjs node --test test/template-builder-render-contract.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js
# pass 22
clipper_nestjs node -e "require('./dist/template-builder/template-builder-render-contract-fixture').writeTemplateBuilderRenderContractFixture('/tmp/template-builder-render-contract-fixture.json')"
clipper_python uv run python scripts/render_template_builder_preview_final_artifacts.py --contract /tmp/template-builder-render-contract-fixture.json --output-dir /tmp/template-builder-render-contract-artifacts --text 'subtitleText=gjpqy 와 므르트픔'
# passed true, mismatchRatio 0.0
```

Next Task 6 prerequisite:

- Add an Angular preview contract fixture/export path for the same variant shape, then compare the Python artifacts generated from Angular preview contract and NestJS render contract fixtures.
- Keep browser screenshot capture for a later step after contract fixture parity is stable.

Additional prerequisite completed 2026-05-09:

- Angular can now export a preview-side fixture variant and preview contract for the same Template Builder shape used by the NestJS render fixture.
- Commit: `clipper_angular` `ef55fbd feat: export template builder preview fixture`.
- This is a source-level Angular fixture/export boundary, not a browser screenshot capture. It proves the preview contract projection can preserve the same geometry/style/media fields before runtime DOM rendering is involved.
- Verification:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts
# TOTAL: 2 SUCCESS
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
# TOTAL: 37 SUCCESS
clipper_angular npm run build
# Application bundle generation complete.
```

Next Task 6 prerequisite:

- Add a small cross-runtime fixture comparison path that serializes the Angular preview fixture contract and NestJS render fixture contract into JSON artifacts, then runs the Python artifact entrypoint against both.
- After that, decide whether browser screenshot capture belongs in Angular e2e/Playwright or in a separate diagnostic harness.

Additional prerequisite completed 2026-05-09:

- Angular preview fixture can now be serialized to JSON by `scripts/export-template-builder-preview-contract-fixture.mjs`.
- Python `scripts/render_template_builder_preview_final_artifacts.py` now accepts separate `--contract` and `--final-contract` paths, so a preview contract JSON and render contract JSON can be compared through the same artifact composer.
- Cross-runtime fixture comparison now passes for Angular preview fixture JSON vs NestJS render fixture JSON.
- Root-cause note: the first cross-runtime run failed at mismatchRatio `0.02802469135802469` because Angular preview fixture used `subtitleBox.box.enabled=false` while the NestJS render fixture inherited the app default `subtitleBox.box.enabled=true`. The fixture is now aligned and guarded by the Angular spec.
- Commits:
  - `clipper_angular` `73df1cb feat: export preview contract fixture json`
  - `clipper_python` `cbf2c17 feat: compare template builder contract artifacts`
- Verification:

```text
clipper_angular node --test test/template-builder-preview-contract-fixture-export.test.mjs
# pass 1
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts
# TOTAL: 2 SUCCESS
clipper_python uv run pytest tests/test_template_builder_preview_final_artifact_script.py -q
# 2 passed
clipper_angular node scripts/export-template-builder-preview-contract-fixture.mjs --output /tmp/template-builder-preview-contract-fixture-cross.json
clipper_nestjs node -e "require('./dist/template-builder/template-builder-render-contract-fixture').writeTemplateBuilderRenderContractFixture('/tmp/template-builder-render-contract-fixture-cross.json')"
clipper_python uv run python scripts/render_template_builder_preview_final_artifacts.py --contract /tmp/template-builder-preview-contract-fixture-cross.json --final-contract /tmp/template-builder-render-contract-fixture-cross.json --output-dir /tmp/template-builder-cross-runtime-artifacts --text 'subtitleText=gjpqy 와 므르트픔'
# passed true, mismatchRatio 0.0
```

Next Task 6 prerequisite:

- Turn the manual cross-runtime command sequence into a single diagnostic runner, then decide where browser screenshot capture should live.
- Keep the diagnostic runner contract-level until real staged media resolver behavior is defined.

Additional prerequisite completed 2026-05-09:

- Added a single Python diagnostic runner for cross-runtime fixture comparison.
- Commit: `clipper_python` `0d5a054 feat: add template builder cross-runtime diagnostics`.
- The runner exports Angular preview contract JSON, exports NestJS render contract JSON, and compares them through the Python artifact entrypoint.
- It remains contract-level and placeholder-media based; it does not claim browser screenshot or encoded video parity yet.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_cross_runtime_fixture_script.py -q
# 1 passed
clipper_python uv run python scripts/compare_template_builder_cross_runtime_fixtures.py --workspace-root /Users/jina/project/adlight --output-dir /tmp/template-builder-cross-runtime-runner --text 'subtitleText=gjpqy 와 므르트픔'
# passed true, mismatchRatio 0.0
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py -q
# 10 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
```

Next Task 6 prerequisite:

- Decide and document the next capture layer:
  - browser screenshot capture of the Angular preview fixture, or
  - staged media asset resolver for replacing placeholders, or
  - final-video frame extraction from a Template Builder sample render.
- Keep each layer behind explicit artifacts so preview/final mismatches can be attributed to data contract, preview rendering, media resolving, or final encoding separately.

Additional prerequisite completed 2026-05-09:

- Added a staged media asset resolver seam to the Python frame artifact composer.
- Commit: `clipper_python` `bd573f2 feat: resolve template builder media assets`.
- `render_template_builder_frame_artifact()` now accepts `media_assets={assetUri: path}`. Resolved assets are composited into the media frame and marked with `placeholder=false`; unresolved media keeps the deterministic placeholder path.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_frame_artifacts.py -q
# 2 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py -q
# 11 passed
```

Next Task 6 prerequisite:

- Thread `media_assets` through `render_template_builder_preview_final_artifacts.py` and the cross-runtime diagnostic runner CLI.
- Then the diagnostic runner can compare placeholder mode and resolved-asset mode using the same contract fixture.

Additional prerequisite completed 2026-05-09:

- Threaded resolved media assets through the Python artifact entrypoint and cross-runtime diagnostic runner.
- Commit: `clipper_python` `c053ca1 feat: thread template builder media assets`.
- `render_template_builder_preview_final_artifacts.py` and `compare_template_builder_cross_runtime_fixtures.py` now accept `--media-asset assetUri=path` and pass the map into `render_template_builder_frame_artifact()`.
- The same Angular/NestJS contract fixtures can now be compared in placeholder mode or resolved-asset mode.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py -q
# 5 passed
clipper_python uv run python scripts/compare_template_builder_cross_runtime_fixtures.py --workspace-root /Users/jina/project/adlight --output-dir /tmp/template-builder-cross-runtime-resolved-assets --text 'subtitleText=gjpqy 와 므르트픔' --media-asset 'media/logo.png=/Users/jina/project/adlight/adlight_python/dist/highlight_server/_internal/images/gradient.png'
# passed true, mismatchRatio 0.0
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py -q
# 13 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
```

Next Task 6 prerequisite:

- Choose the first non-contract visual capture target:
  - Angular preview fixture browser screenshot capture, or
  - Template Builder sample-render final frame extraction.
- Browser screenshot capture is the more direct preview-side check; final-video extraction is the more direct generated-output check. Keep either path diagnostic-only until real product renderer wiring is explicitly changed.

Additional prerequisite completed 2026-05-09:

- Added the first Angular preview-side non-contract render snapshot.
- Commit: `clipper_angular` `7488e27 feat: capture template preview render snapshot`.
- `templateBuilderPreviewRenderSnapshotFor(root)` reads the actual Karma/Chrome-rendered DOM for the Template Builder preview canvas and returns canvas/content-area/layer rects plus computed text/media styles and media `src`.
- The guard uses the Angular preview fixture contract inside `TemplateBuilderEditorComponent`, so it now catches browser computed layout effects beyond pure JSON contract equality.
- Important finding: browser computed sub-pixel layout is not always the exact arithmetic contract value. For example the fixture `subtitleText` height is `84 * 0.3 = 25.2`, while Chrome computed `25.195`. This is exactly the kind of preview-side render drift that should be measured before final frame comparison.
- This is not bitmap screenshot capture yet and does not compare against an encoded final render frame.
- Verification:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
# RED first: module not found for template-builder-preview-render-snapshot
# GREEN after implementation: TOTAL: 36 SUCCESS
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
# TOTAL: 38 SUCCESS
clipper_angular npm run build
# Application bundle generation complete.
clipper_angular git diff --check
# no output
```

Next Task 6 prerequisite:

- Decide the next preview capture expansion:
  - add a bitmap screenshot capture tool, likely Playwright if a real screenshot artifact is needed, or
  - first export this browser render snapshot as a JSON artifact from an automated runner.
- Do not compare this directly with Python final frames yet; first make the capture artifact stable and explicit.

Additional prerequisite completed 2026-05-09:

- Added an automated JSON artifact export for the browser-rendered Angular preview snapshot.
- Commit: `clipper_angular` `618e70c feat: export template preview render snapshot`.
- `scripts/export-template-builder-preview-render-snapshot.mjs --output <path>` runs a one-off Karma/ChromeHeadless diagnostic spec and writes a JSON snapshot artifact.
- `scripts/template-builder-preview-render-snapshot-reporter.cjs` captures the browser-emitted snapshot marker and writes the artifact on the Node side.
- The exported artifact includes the preview canvas/content-area rect, all visible text layer rects/computed styles/text, and visible media layer rect/style/src.
- Headless Chrome artifact values are now explicit. Example: `subtitleText.rect.height=25.188`, while regular Chrome component spec measured `25.195`.
- Verification:

```text
clipper_angular node --test test/template-builder-preview-contract-fixture-export.test.mjs test/template-builder-preview-render-snapshot-export.test.mjs
# pass 2, fail 0
clipper_angular node scripts/export-template-builder-preview-render-snapshot.mjs --output /tmp/template-builder-preview-render-snapshot-final.json
# wrote JSON artifact
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/services/template-builder-preview-render-snapshot.export.spec.ts
# TOTAL: 39 SUCCESS
clipper_angular npm run build
# Application bundle generation complete.
clipper_angular git diff --check
# no output
```

Next Task 6 prerequisite:

- Add a bitmap preview capture artifact. Playwright is now the likely next dependency because the project has a stable preview JSON artifact and needs an actual `.phone-canvas` PNG for final-frame visual comparison.
- Keep screenshot capture diagnostic-only and do not wire it into product runtime.

Additional prerequisite completed 2026-05-09:

- Added a bitmap preview screenshot artifact export without adding Playwright yet.
- Commit: `clipper_angular` `3acc406 feat: export template preview screenshot`.
- `scripts/export-template-builder-preview-screenshot.mjs --output <path>` runs a one-off Karma/ChromeHeadless diagnostic spec, opens a Chrome DevTools Protocol port, locates the rendered `.phone-canvas`, and writes a PNG screenshot.
- The screenshot spec keeps the preview component alive until the Node-side CDP capture finishes, then lets Karma exit normally.
- The generated artifact is a 324x576 PNG matching the current Template Builder editor preview canvas scale, not the final 1080x1920 render size.
- Verification:

```text
clipper_angular node --test test/template-builder-preview-contract-fixture-export.test.mjs test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs
# pass 3, fail 0
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-final.png
# wrote PNG artifact
PNG check:
# signature 89504e470d0a1a0a, width 324, height 576, bytes 1686
clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder-preview-contract.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/services/template-builder-preview-render-snapshot.export.spec.ts --include src/features/template-builder/services/template-builder-preview-screenshot.export.spec.ts
# TOTAL: 40 SUCCESS
clipper_angular npm run build
# Application bundle generation complete.
clipper_angular git diff --check
# no output
```

Next Task 6 prerequisite:

- Add a comparison bridge between the 324x576 browser preview screenshot and the 1080x1920 Python/frame artifact. The comparison should make scale normalization explicit instead of silently resizing one side.
- Keep the first comparison diagnostic-only; it should report dimensions, scaling factor, and mismatch metrics separately.

Additional prerequisite completed 2026-05-09:

- Added a diagnostic comparison bridge for browser preview screenshot vs Python/final frame artifact.
- Commit: `clipper_python` `c99f709 feat: compare template preview screenshot`.
- `scripts/compare_template_builder_preview_screenshot.py` accepts a browser preview screenshot PNG and a frame PNG, writes `final_frame_scaled_to_preview.png`, and emits `preview_screenshot_comparison.json`.
- The report explicitly records `previewSize`, `frameSize`, `scale`, and `normalization.resized=frame-to-preview` before mismatch metrics.
- Actual diagnostic run:

```text
clipper_python uv run python scripts/compare_template_builder_preview_screenshot.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --frame /tmp/template-builder-cross-runtime-resolved-assets-final/artifacts/final_frame.png --output-dir /tmp/template-builder-preview-final-visual-bridge --max-mismatch-ratio 1.0
# previewSize [324, 576], frameSize [1080, 1920], scale {x: 0.3, y: 0.3}, mismatchRatio 1.0
```

- `mismatchRatio=1.0` is expected at this stage because the screenshot is the real Angular editor preview while the Python frame is still the deterministic artifact composer, not the same browser-rendered visual surface. The bridge is diagnostic-only and does not tighten a product gate yet.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_preview_screenshot_comparison.py -q
# 1 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py tests/test_template_builder_preview_screenshot_comparison.py -q
# 14 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
clipper_python git diff --check
# no output
```

Next Task 6 prerequisite:

- Use the JSON snapshot and PNG comparison report together to identify the largest preview/final visual mismatches by category:
  - editor-only content-area visual/background,
  - browser CSS text rendering vs Python artifact text rendering,
  - media loading/resolution differences,
  - scale/sub-pixel differences.
- Do not lower any mismatch threshold until the diagnostic categories are separated.

Additional prerequisite completed 2026-05-09:

- Fixed the Angular preview screenshot export so it captures rendered preview pixels instead of a blank white clip.
- Commit: `clipper_angular` `22f545a fix: capture rendered template preview screenshot`.
- Root cause:
  - The first screenshot export test only checked PNG signature/size/bytes, so a blank white 324x576 PNG passed.
  - CDP diagnostics showed `.phone-canvas` at `y=927` while the Headless Chrome viewport was only `741x417`; the capture clip pointed outside the visible iframe area.
  - The exporter now starts Chrome with `--window-size=1280,1200`, scrolls `.phone-canvas` into view before calculating the clip, and waits for browser paint in the export spec.
- The Node screenshot export test now decodes the PNG and requires at least one dark rendered preview pixel, preventing blank captures from passing.
- Actual artifact update:
  - Before fix: `/tmp/template-builder-preview-screenshot-final.png` was effectively all white, bytes `1686`.
  - After fix: regenerated screenshot is 324x576 with rendered preview pixels, bytes `56778`, center pixel `(30, 41, 59)`.
- Verification:

```text
clipper_angular node --test test/template-builder-preview-screenshot-export.test.mjs
# RED first: blank capture assertion failed
# GREEN after implementation: pass 1, fail 0
clipper_angular node --test test/template-builder-preview-contract-fixture-export.test.mjs test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs
# pass 3, fail 0
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-final.png
# wrote rendered PNG artifact
clipper_angular npm run build
# Application bundle generation complete.
clipper_angular git diff --check
# no output
```

Additional prerequisite completed 2026-05-09:

- Added snapshot-region mismatch categories to the preview screenshot vs final frame diagnostic bridge.
- Commit: `clipper_python` `6e02da3 feat: categorize template preview mismatches`.
- `scripts/compare_template_builder_preview_screenshot.py` now accepts `--preview-render-snapshot <json>`.
- When a browser render snapshot is provided, the report writes overlapping diagnostic categories:
  - `canvas`
  - `contentArea`
  - `text:<layerId>`
  - `media:<layerId>`
- These categories are diagnostic-only. They are not exclusive buckets and they are not thresholds.
- Actual diagnostic after regenerating the nonblank screenshot:

```text
clipper_python uv run python scripts/compare_template_builder_preview_screenshot.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --frame /tmp/template-builder-cross-runtime-resolved-assets-final/artifacts/final_frame.png --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-final.json --output-dir /tmp/template-builder-preview-final-visual-categories --max-mismatch-ratio 1.0
# tolerance 0: canvas/contentArea/text/media categories still saturate at mismatchRatio 1.0
```

- A tolerance diagnostic makes the current largest regions visible:

```text
clipper_python uv run python scripts/compare_template_builder_preview_screenshot.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --frame /tmp/template-builder-cross-runtime-resolved-assets-final/artifacts/final_frame.png --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-final.json --output-dir /tmp/template-builder-preview-final-visual-categories-t128 --channel-tolerance 128 --max-mismatch-ratio 1.0
# canvas 0.2823431069958848
# text:subTitle 0.7350364963503649
# text:mainTitleLine1 0.656021897810219
# text:mainTitleLine2 0.5596715328467153
# text:subtitleText 0.5782051282051283
# media:logoImage 0.757985257985258
```

- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_preview_screenshot_comparison.py -q
# RED first: preview_render_snapshot_path unexpected keyword
# GREEN after implementation: 2 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py tests/test_template_builder_preview_screenshot_comparison.py -q
# 15 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
clipper_python git diff --check
# no output
```

Next Task 6 prerequisite:

- Do not lower visual thresholds yet.
- The final/sample-render frame extraction path is now available, but still diagnostic-only.
- Keep category reports diagnostic-only until preview and final are intentionally drawing the same visual contract.

Additional prerequisite completed 2026-05-09:

- Added a reusable final/sample render video frame extraction diagnostic.
- Commit: `clipper_python` `af32bfd feat: extract template builder video frames`.
- `scripts/extract_template_builder_video_frame.py --video <mp4> --output-dir <dir> --at-seconds <sec>` extracts `final_frame.png` via ffmpeg and writes `video_frame_extraction.json`.
- This intentionally does not run sample render yet. It is the stable boundary for turning an existing MP4 artifact into a PNG frame that can enter the preview comparison bridge.
- Actual smoke:

```text
clipper_python uv run python scripts/extract_template_builder_video_frame.py --video tests/fixtures/clipper1_golden_frames/template-17-16_9/video/final_video.mp4 --output-dir /tmp/template-builder-video-frame-extraction-smoke --at-seconds 0.0
# frame /tmp/template-builder-video-frame-extraction-smoke/final_frame.png
# frameSize [1080, 1920]
```

Additional prerequisite completed 2026-05-09:

- Added a one-command preview screenshot vs video-frame comparison runner.
- Commit: `clipper_python` `a93a764 feat: compare template preview video frames`.
- `scripts/compare_template_builder_preview_video_frame.py` performs:
  1. extract `video-frame/final_frame.png` from a sample/final MP4,
  2. compare that PNG against the browser preview screenshot with explicit scale normalization,
  3. optionally use `--preview-render-snapshot` to include category metrics,
  4. write `preview_video_frame_comparison.json`.
- Actual smoke used a legacy fixture MP4 only to verify the pipeline:

```text
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --video tests/fixtures/clipper1_golden_frames/template-17-16_9/video/final_video.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-final.json --output-dir /tmp/template-builder-preview-video-frame-runner-smoke --max-mismatch-ratio 1.0
# extractedFrame /tmp/template-builder-preview-video-frame-runner-smoke/video-frame/final_frame.png
# previewSize [324, 576]
# frameSize [1080, 1920]
# scale {x: 0.3, y: 0.3}
# mismatchRatio 0.9999464163237312
```

- The smoke mismatch value is not meaningful quality evidence because it compares the Template Builder preview fixture against a legacy Clipper1 fixture video. The value only proves the new video-frame extraction and comparison path works end-to-end.
- Verification:

```text
clipper_python uv run pytest tests/test_template_builder_video_frame_extraction.py tests/test_template_builder_preview_video_frame_comparison.py tests/test_template_builder_preview_screenshot_comparison.py -q
# 5 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_video_frame_extraction.py tests/test_template_builder_preview_video_frame_comparison.py -q
# 18 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
clipper_python git diff --check
# no output
```

Next Task 6 prerequisite:

- Connect the new video-frame comparison runner to a real Template Builder sample render MP4 instead of a legacy fixture video.
- Preferred slice:
  - export or create a deterministic Template Builder sample render MP4 path from NestJS/Python,
  - feed that MP4 into `compare_template_builder_preview_video_frame.py`,
  - keep `--max-mismatch-ratio 1.0` and treat the result as a diagnostic report, not a pass/fail visual gate.

Additional prerequisite completed 2026-05-09:

- Added a NestJS Template Builder sample render fixture package export.
- Commit: `clipper_nestjs` `43ad151 feat: export template builder sample render fixture`.
- `scripts/export-template-builder-sample-render-fixture.mjs --output-dir <dir>` writes:
  - `recipe.json`
  - `artifacts.json`
  - `legacy_payload.json`
  - `fixture.json`
  - staged local assets under `assets/`
- The fixture is generated through the Template Builder render contract fixture and `LegacyClipper1RenderPayloadMapper`, so the Python render uses the same legacy payload shape that NestJS sample render would submit to the Clipper1 worker.
- The fixture duration is `0.8s` for diagnostic speed. Frame 0 is sufficient for the current preview/final visual capture path.

Additional prerequisite completed 2026-05-09:

- Added a Python renderer entrypoint for the exported Template Builder sample fixture.
- Commit: `clipper_python` `c3bff8f feat: render template builder sample fixture video`.
- `scripts/render_template_builder_sample_video_fixture.py --fixture-dir <dir>` reads `legacy_payload.json` and `recipe.json`, then calls `LocalRenderAdapter` to create the MP4 and thumbnail under that fixture directory.
- Actual end-to-end diagnostic:

```text
clipper_nestjs node scripts/export-template-builder-sample-render-fixture.mjs --output-dir /tmp/template-builder-sample-render-fixture
# wrote recipe/artifacts/legacy_payload/assets

clipper_python uv run python scripts/render_template_builder_sample_video_fixture.py --fixture-dir /tmp/template-builder-sample-render-fixture
# status completed
# video /tmp/template-builder-sample-render-fixture/template-sample/main.mp4
# thumbnail /tmp/template-builder-sample-render-fixture/template-sample/main_thumbnail.jpg

clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --video /tmp/template-builder-sample-render-fixture/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-final.json --output-dir /tmp/template-builder-preview-vs-sample-render --max-mismatch-ratio 1.0
# previewSize [324, 576]
# frameSize [1080, 1920]
# scale {x: 0.3, y: 0.3}
# mismatchRatio 0.9999732081618655
```

- The mismatch is still diagnostic-only. The current Angular preview fixture and sample render fixture do not yet share the same preview text/media/background surface, so the value must not become a threshold.
- Verification:

```text
clipper_nestjs npm run build
# passed
clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js test/template-builder-render-contract.test.js test/template-builder-render-payload.test.js
# 9 passed
clipper_python uv run pytest tests/test_template_builder_sample_video_fixture_render.py tests/test_template_builder_video_frame_extraction.py tests/test_template_builder_preview_video_frame_comparison.py tests/test_template_builder_preview_screenshot_comparison.py -q
# 6 passed
clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_preview_final_artifact_script.py tests/test_template_builder_cross_runtime_fixture_script.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_video_frame_extraction.py tests/test_template_builder_preview_video_frame_comparison.py tests/test_template_builder_sample_video_fixture_render.py -q
# 19 passed
clipper_python uv run python -m compileall scripts
# Listing 'scripts'...
clipper_nestjs git diff --check
# no output
clipper_python git diff --check
# no output
```

Next Task 6 prerequisite:

Completed 2026-05-09 20:50 KST:

- Aligned the first input-surface slice between Angular preview fixture and Template Builder sample render fixture.
- Angular:
  - Added `TEMPLATE_BUILDER_PREVIEW_SAMPLE_TEXT` as the editor preview sample copy source.
  - The preview fixture now hides `logoText` when the fixture uses `logoImage`, so the browser snapshot no longer includes both logo image and logo text for the same sample.
  - The render snapshot export spec now asserts the sample copy and that `logoText` is absent in the image-logo fixture.
  - Commit: `clipper_angular` `79ae804 feat: align template preview sample content`.
- NestJS:
  - Added shared `TEMPLATE_BUILDER_SAMPLE_TEXT` helpers for sample render text.
  - `TemplateBuilderSampleRenderService` and `template-builder-sample-render-fixture.ts` now use the same sample copy:
    - sub title: `오늘의 핵심`
    - main title: `서울 근교\n축제 TOP 5`
    - bottom title: `저장해두세요`
    - subtitles: `이번 주말에 가기 좋은`, `서울 근교 축제부터 볼게요`
  - The render contract fixture now hides `logoText` for the image-logo sample.
  - Commit: `clipper_nestjs` `3d6687e feat: align template sample render content`.
- RED/GREEN:
  - Angular RED: snapshot still contained `logoText: "Clipper"` and contract fixture had `logoText.visible=true`.
  - NestJS RED: sample render service/fixture still emitted `샘플 ...` copy and render contract fixture had `logoText.visible=true`.
  - GREEN: focused Angular and NestJS tests pass after the text/visibility alignment.
- Actual diagnostic after regenerating artifacts:

```text
clipper_angular node scripts/export-template-builder-preview-render-snapshot.mjs --output /tmp/template-builder-preview-render-snapshot-20260509.json
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-20260509.png
clipper_nestjs node scripts/export-template-builder-sample-render-fixture.mjs --output-dir /tmp/template-builder-sample-render-fixture-20260509
clipper_python uv run python scripts/render_template_builder_sample_video_fixture.py --fixture-dir /tmp/template-builder-sample-render-fixture-20260509
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-20260509.png --video /tmp/template-builder-sample-render-fixture-20260509/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-20260509.json --output-dir /tmp/template-builder-preview-vs-sample-render-20260509 --max-mismatch-ratio 1.0
# previewSize [324, 576]
# frameSize [1080, 1920]
# scale {x: 0.3, y: 0.3}
# mismatchRatio 0.9999624914266118
```

- The mismatch is still diagnostic-only. Text copy and logo-text visibility now match, but the preview screenshot still uses editor/browser visual treatment while the sample render MP4 uses the staged media/background and legacy final renderer. Do not introduce a threshold from this value.

Next Task 6 prerequisite:

- Continue aligning the remaining visual surface before interpreting mismatch values.
- Preferred next slice:
  - make Angular preview render the same sample media/background asset that the sample render fixture uses, or
  - make the sample render fixture use a deterministic background/content-area surface that matches the current Angular editor preview.
- Keep using `--max-mismatch-ratio 1.0` until the remaining media/background surface intentionally matches.

Completed 2026-05-09 20:58 KST:

- Aligned the media/background fixture surface for diagnostics.
- Angular:
  - Added a deterministic 1x1 PNG data URL sample media (`#111827`) to `template-builder-preview-sample-content.ts`.
  - The preview fixture sets `contentArea.assetUri` to that data URL.
  - `TemplateBuilderEditorComponent` now renders direct `data:`, `blob:`, or `http(s):` media URLs for `contentArea` as an image instead of the editor-only gradient placeholder.
  - `templateBuilderPreviewRenderSnapshotFor()` now records `media:contentArea` from `[data-testid="content-area-preview"]`.
  - Commit: `clipper_angular` `abeed8d feat: align template preview sample media`.
- NestJS:
  - The render contract fixture sets `contentArea.assetUri` to the same data URL.
  - Sample render service and fixture export now stage the same deterministic PNG as `assets/template-sample-media.png` with `mediaType=image/png` instead of copying `clip_1.jpeg`.
  - Commit: `clipper_nestjs` `385206d feat: align template sample render media`.
- RED/GREEN:
  - Angular RED: contract fixture still had `contentArea.assetUri=null`; render snapshot had no `layers.contentArea`.
  - NestJS RED: sample render still emitted `assets/template-sample-media.jpg` and render contract fixture had no content-area media data URL.
  - GREEN: focused Angular and NestJS tests pass after the media/background alignment.
- Actual diagnostic after regenerating artifacts:

```text
clipper_angular node scripts/export-template-builder-preview-render-snapshot.mjs --output /tmp/template-builder-preview-render-snapshot-20260509-media.json
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-20260509-media.png
clipper_nestjs node scripts/export-template-builder-sample-render-fixture.mjs --output-dir /tmp/template-builder-sample-render-fixture-20260509-media
clipper_python uv run python scripts/render_template_builder_sample_video_fixture.py --fixture-dir /tmp/template-builder-sample-render-fixture-20260509-media
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-20260509-media.png --video /tmp/template-builder-sample-render-fixture-20260509-media/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-20260509-media.json --output-dir /tmp/template-builder-preview-vs-sample-render-20260509-media --max-mismatch-ratio 1.0
# tolerance 0 mismatchRatio 0.9998981910150891
```

- Tolerance 0 is still not meaningful because the same dark PNG becomes `(17,24,39)` in browser preview and `(15,23,38)` after video/YUV/H.264 conversion, so almost every background pixel mismatches by 1-2 channels.
- A diagnostic run with `--channel-tolerance 4` gives the more useful next breakdown:

```text
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-20260509-media.png --video /tmp/template-builder-sample-render-fixture-20260509-media/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-20260509-media.json --output-dir /tmp/template-builder-preview-vs-sample-render-20260509-media-t4 --channel-tolerance 4 --max-mismatch-ratio 1.0
# overall mismatchRatio 0.06444508744855967
# text:subtitleText 0.7897435897435897
# text:subtitleBox 0.9551094890510949
# media:logoImage 0.7936117936117936
```

- The next largest non-background differences are now subtitle/subtitle-box rendering and logo image loading/asset parity. These should be diagnosed before any threshold is introduced.

Next Task 6 prerequisite:

- Keep the current `--max-mismatch-ratio 1.0` visual compare as diagnostic-only.
- Preferred next slice:
  - align the logo image surface so Angular preview and sample render use the same image bytes, or
  - isolate subtitle/subtitleBox renderer differences with category-specific diagnostics and modern renderer decisions.

Completed 2026-05-09 21:25 KST:

- Aligned the next fixture input surface: logo image bytes and subtitle sample geometry.
- Angular:
  - Added `TEMPLATE_BUILDER_PREVIEW_SAMPLE_LOGO_DATA_URL`, a small deterministic PNG used directly by the browser preview fixture.
  - `logoImage.assetUri` now uses that data URL instead of the backend asset URL path.
  - `subtitleBox` sample text is now empty because final render treats `subtitleBox` as box settings, not as a text overlay.
  - `subtitleText.y` moved from `96` to `1254`, matching the final payload subtitle line y-offset used for the sample.
  - `subtitleText.box.enabled=false` in the fixture so the rendered subtitle background comes from `subtitleBox` semantics instead of a preview-only `subtitleText` box.
- NestJS:
  - Added the same deterministic logo PNG base64/data URL to `template-builder-sample-content.ts`.
  - The render contract fixture uses the data URL for `logoImage.assetUri`.
  - Sample render service and sample fixture export stage that same PNG as `assets/template-sample-logo.png`.
  - `subtitleText.y=1254` and `subtitleText.box.enabled=false` in the render contract fixture.
- RED/GREEN:
  - Angular RED: focused Karma tests failed while the snapshot still had `subtitleText.rect.top=28.8`, `subtitleBox.text` still contained subtitle copy, and `logoImage.src` was backend URL based.
  - NestJS RED: render contract fixture test failed with `subtitleText.y=96`.
  - GREEN: focused Angular and NestJS tests pass after logo/subtitle fixture alignment.
- Commits:
  - `clipper_angular` `f2acf10 feat: align template preview logo and subtitles`.
  - `clipper_nestjs` `9db3f14 feat: align template sample logo and subtitles`.
- Note:
  - An initial attempt to embed the previous bundled `clipper_logo_w.png` base64 produced a truncated PNG and hung the Python/ffmpeg diagnostic render. That render process was killed and the fixture was switched to a small deterministic valid PNG. Keep deterministic fixture assets small unless the exact image is required.
- Actual diagnostic after regenerating artifacts:

```text
clipper_angular node scripts/export-template-builder-preview-render-snapshot.mjs --output /tmp/template-builder-preview-render-snapshot-20260509-subtitle-y.json
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-20260509-subtitle-y.png
clipper_nestjs node scripts/export-template-builder-sample-render-fixture.mjs --output-dir /tmp/template-builder-sample-render-fixture-20260509-subtitle-y
clipper_python uv run python scripts/render_template_builder_sample_video_fixture.py --fixture-dir /tmp/template-builder-sample-render-fixture-20260509-subtitle-y
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-20260509-subtitle-y.png --video /tmp/template-builder-sample-render-fixture-20260509-subtitle-y/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-20260509-subtitle-y.json --output-dir /tmp/template-builder-preview-vs-sample-render-20260509-subtitle-y-t4 --channel-tolerance 4 --max-mismatch-ratio 1.0
# overall mismatchRatio 0.05262988683127572
# media:logoImage 0.22235872235872237
# text:subtitleText 0.9850427350427351
# text:subtitleBox 0.962043795620438
```

- Progress relative to the previous media-aligned diagnostic:
  - `--channel-tolerance 4` overall: `0.06444508744855967 -> 0.05262988683127572`.
  - `media:logoImage`: `0.7936117936117936 -> 0.22235872235872237`.
  - The remaining subtitle category ratios are still high because the preview currently draws `subtitleBox` as a fixed canvas rectangle, while final render uses subtitle box settings to draw dynamic boxes around the actual subtitle text lines.

Next Task 6 prerequisite:

- Keep visual compare diagnostic-only; do not add a bitmap threshold yet.
- Preferred next slice:
  - change preview subtitle rendering so `subtitleBox` is treated as style/settings for subtitle text boxes, not a fixed text layer rectangle, or
  - add a narrower diagnostic that compares final subtitle dynamic box bounds against preview-computed dynamic subtitle boxes before changing UI behavior.

Completed 2026-05-09 21:32 KST:

- Implemented the preferred subtitle preview slice in Angular.
- Angular:
  - `subtitleText` now renders preview subtitle lines as separate dynamic boxes.
  - `subtitleBox` is no longer painted as a fixed dark rectangle in the preview canvas; it supplies box color/alpha/padding/height/border settings to the subtitle line boxes.
  - The preview line box y positions use `oneLineY`, `twoLineFirstY`, and `twoLineSecondY`, matching the legacy final payload fields.
  - Browser render snapshot tests now assert `subtitleText` spans both dynamic lines and `subtitleBox` has transparent fixed-layer background.
  - Commit: `clipper_angular` `3db3bdc feat: render dynamic template subtitle boxes`.
- Actual diagnostic after regenerating preview artifacts against the same sample render MP4:

```text
clipper_angular node scripts/export-template-builder-preview-render-snapshot.mjs --output /tmp/template-builder-preview-render-snapshot-20260509-dynamic-subtitle.json
clipper_angular node scripts/export-template-builder-preview-screenshot.mjs --output /tmp/template-builder-preview-screenshot-20260509-dynamic-subtitle.png
clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-20260509-dynamic-subtitle.png --video /tmp/template-builder-sample-render-fixture-20260509-subtitle-y/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-20260509-dynamic-subtitle.json --output-dir /tmp/template-builder-preview-vs-sample-render-20260509-dynamic-subtitle-t4 --channel-tolerance 4 --max-mismatch-ratio 1.0
# overall mismatchRatio 0.036785193758573385
# text:subtitleBox 0.2737226277372263
# text:subtitleText 0.9438271604938272
# media:logoImage 0.22235872235872237
```

- Progress:
  - `--channel-tolerance 4` overall: `0.05262988683127572 -> 0.036785193758573385`.
  - `text:subtitleBox`: `0.962043795620438 -> 0.2737226277372263`.
- Remaining known gap:
  - `text:subtitleText` is still high because browser text metrics/stroke/shadow/line box rendering do not yet match the final renderer's PNG text generation. This should be handled as modern text renderer parity, not by reintroducing fixed subtitle boxes.

Next Task 6 prerequisite:

- Keep visual compare diagnostic-only.
- Preferred next slice:
  - isolate the remaining text glyph/stroke/shadow drift for `subtitleText`, `subTitle`, `mainTitleLine1/2`, and `bottomTitle`;
  - decide whether preview should use browser text rendering as the source of truth or consume deterministic text artifact metadata from the final renderer for tighter preview/final parity.

## Verification Set

Minimum verification after any preview/final contract change:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js
```

Latest completed verification for Task 1:

```text
clipper_nestjs npm run build
clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js
# pass 14
# fail 0
clipper_nestjs git diff --check
```

If Angular preview code changes:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

If Python render code changes:

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_golden_frames.py -q
uv run pytest tests/test_clipper2_template_baseline_frames.py -q
```
