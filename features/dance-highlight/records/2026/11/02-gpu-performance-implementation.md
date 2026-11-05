# Dance GPU performance implementation plan

> Execution: superpowers:executing-plans, inline implementation and one final independent review. User approved the preceding GPU audit sequence on 2026-11-02 and added Windows acceleration.

**Goal:** Reduce packaged-app runtime for the same three YouTube videos without degrading named clips, boundaries, or person-highlight behavior.
**Architecture:** Inject a dance-only ONNX session factory into the unchanged shared AuraFace recognizer. Use CoreML on macOS and DirectML on Windows (CUDA when present), CPU fallback. Reuse identical computations only; keep quality thresholds, sample rates, and SAM CPU semantics until GPU parity is demonstrated.
**Spec:** [GPU audit and measured constraints](02-gpu-performance-audit.md).

## Global constraints
- Existing projects and results preserved; new projects use their original YouTube URLs and reference selections.
- Shared face core and person plugin behavior/dependencies unchanged.
- Windows acceleration must be installed as well as selected; no claim of Windows hardware validation on this Mac.
- Work in original Python checkout on a dedicated branch; build original sibling repos with `npm run build:app:mac:arm64:local-api` per prior user preference.
- No commits, pushes, merges, or relaxed classification thresholds requested.

## Tasks
- [x] 1. Add tests then dance-only session selection/cache/fallback in `services/face_runtime.py`; inject through `FaceClusterService`. Test Mac CoreML, Windows DirectML options, absent GPU, load/run failure, and unchanged shared CPU default. Update Windows dance dependency and lock; verify isolated install resolution.
- [x] 2. Add tests then bounded exact-input detector/embedding reuse and completed SAM sequence reuse only. Keep prompts, frame order, precision, rejection checks and final classifications unchanged. Add per-stage timing and per-model runtime provenance.
- [x] 3. Run related dance/shared/person regressions, a real-model CPU/GPU comparison, and inspect the full diff. SAM MPS must stay disabled if full product verdicts differ; pursue exact reuse instead.
- [x] 4. Build and launch the packaged local-API app. Submit the original three YouTube URLs with preserved artist/reference selections into new projects through the app workflow. Record start/completion, app hashes/providers, pipeline stage timings and final clip differences against preserved baseline.
- [x] 5. Independently review isolation/fallback/cache correctness. Document measured gains, changed outputs, limitations and Windows hardware follow-up. Do not claim quality parity without comparing classifications and boundaries.

## Review focus
- Fallback after GPU initialization or inference failure must return a valid CPU result and report actual provider.
- Cache keys must include all relevant input and geometry; returned arrays cannot mutate retained values.
- SAM cache keys include the complete ordered frame sequence and prompts. Prefix reuse is prohibited: the model uses the total frame count in temporal attention.
- Windows installation must avoid installing CPU and GPU ORT distributions into the same plugin environment.
- Test fixtures and three-video quality comparisons must catch missing short main changes and changed member identities, not only count clips.

## Ledger
- 2026-11-02: Audit established existing YOLO MPS, CPU AuraFace/SAM, no-profile AuraFace 1.63x pilot; SAM MPS ownership differences. Plan approved in scope by explicit user instruction to proceed in that order.
- Ruling: original checkout branch instead of managed worktree follows prior explicit original-repository build preference. Preserve other repositories and existing documentation changes.

- Implemented: dance-only CoreML/CUDA/DirectML session factory, validated CPU fallback, exact embedding/detector caches, completed SAM mask-sequence cache, validated source-transition reuse, stage timings and per-model providers. SAM weights, sample cadence, thresholds and clip logic unchanged.
- Concurrency regressions found and fixed: DirectML same-session runs serialize; detector requested input size is thread-local. Cached outputs are copied and bounded.
- Focused verification: 1,255 dance/shared-face/person tests passed in 35.26 seconds. Broader suite: 2,365 passed, 4 skipped, 10 failed, 17 errors; local server sandbox restrictions caused several failures/errors. Elevated focused rerun passed 31 tests. Six unrelated rendering checks still failed in the broad run; other plugin boot tests have not been rerun outside the sandbox. Do not call the full suite green.
- Real-model hybrid SAM experiment: moving only the image encoder to MPS still changed ownership outcomes (ANTIFRAGILE 2/23, NEON 4/23, Made My Night 0/23). Product SAM remains on CPU. Exact repeated sequences were reused losslessly; probe timings are not a whole-pipeline benchmark.
- Independent implementation review completed with no actionable code defects. Actual packaged-app three-video validation and Windows physical-device validation remain outstanding.
- Build succeeded from original sibling repositories using Node 24.19.0 and `npm run build:app:mac:arm64:local-api`. App launched; user completed browser login. Existing LE SSERAFIM reference choices restored (8/6/5/6/6 images). Actual extraction has not started: app now requests 40 credits for Made My Night, awaiting user approval for a three-video spending cap.
- Evidence and logs: `/private/tmp/dance-gpu-implementation-20261102/` (baseline snapshots, build/test logs, hybrid-SAM JSON). Final results must be copied to durable evidence storage after runs finish.
- App-wide audit received: [GPU architecture audit](../../../../../operations/accelerators/records/2026/11/02-app-gpu-architecture-audit.md). Packaged per-plugin exact frozen uv sync replaces Windows CPU ORT with DirectML for dance; person dependency closure remains CPU ORT. Global lock hash may trigger a person environment re-sync despite unchanged person product code. Windows YOLO/PyTorch acceleration and physical DirectML parity remain separate gaps; dashboard currently lacks a DirectML label.

- User approved credit consumption for these measurements. Three UI-created jobs submitted with all reference selections and bytes equal to baseline: Made My Night `dance_1793558808114`, ANTIFRAGILE `dance_1793558865224`, NEON `dance_1793558916550`. Total displayed charge: 120 credits.
- First packaged-app result: Made My Night active wall time 719.981 seconds vs 1079.866 seconds (33.33% reduction); pipeline 710.2 vs 1058.4 seconds. All 83 full clip rows, person cards, and 2,324 diagnostic frames equal baseline exactly. Same source/model/config hashes, zero CoreML fallbacks. ANTIFRAGILE running; NEON queued. This is partial evidence, not completion of the three-video task.
- Baseline source audit: every recorded service matches the unmodified branch base; `sampled_face_link` differs only by one trailing blank line (AST equal). Actual packaged `face_runtime.py` hash matches the modified source. Canonical baseline active times exclude queue waits: 1079.866 / 1512.350 / 2669.802 seconds.
- Durable small evidence: [run manifest](02-gpu-performance-app-evidence/run-manifest.json), [baseline timings](02-gpu-performance-app-evidence/baseline-timings.json), [runtime acceleration](02-gpu-performance-app-evidence/packaged-runtime-accelerators.json). Full original and new app projects preserved in the app data directory.

- All three packaged-app runs completed on 2026-11-02. Active wall seconds: Made My Night 719.981 (-33.33%), ANTIFRAGILE 1104.987 (-26.94%), NEON 2238.808 (-16.14%). All 406 clip rows, person cards, 9,266 diagnostic frames and thumbnail bytes exactly match baseline. Same input/model/config/reference hashes.
- NEON still spends 1279.728 seconds (21m 20s) in CPU mask continuity. Its full cluster stage fell only 1542.1 → 1479.432 seconds. Performance is improved, but NEON's major CPU bottleneck is not solved. No claim of Windows real-device speed/quality validation.
- [Final measured report and limitations](02-gpu-performance-results.md). Original/new projects preserved. No commit, push or merge performed.
