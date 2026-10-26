# Person Highlight Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user's direct request authorizes execution in this session; repository instructions prohibit commits and pushes without a separate request.

**Goal:** Deliver a usable Person Highlight workflow for arbitrary videos, including body-assisted continuity, reviewable uncertainty, editable results, and padded MP4/ZIP exports.

**Architecture:** Rebase the uncommitted 2026-10-01 Person MVP onto the four current desktop `origin/dev` repositories without overwriting the shared face core. Keep YuNet/SFace for face evidence; use all-person YOLO pose detections as a body candidate, track within shots, and decide identity separately from visible intervals. Carry appearance bounds and export bounds separately through Python, Nest, and Angular.

**Tech Stack:** Python 3.11/OpenCV/Ultralytics, NestJS 10, Angular 19, Electron TypeScript, ffmpeg.

**Spec:** `../design/2026-10-19-person-highlight-continuity-design.md`; existing product contract `/Users/jina/project/adlight/docs/superpowers/specs/2026-10-01-person-highlight-mvp-design.md` where not superseded.

## Global Constraints

- Source footage may contain people in any genre; no category or one-video special cases.
- Keep the existing Person MVP worktrees untouched as donors; start each implementation repository at latest fetched `origin/dev` on the same feature branch.
- Reuse `clipper_face_core` YuNet/SFace observation/embedding code. Do not replace Dance's selector or shared matching policy as a side effect.
- A body box establishes presence, not identity. Preserve co-visible cannot-link and mark uncertain identity `needs_review`.
- Keep actual appearance bounds apart from padded export bounds; initial candidate padding is 0.5 seconds on each side, clamped to source duration.
- Preserve source audio and user edits in MP4/ZIP. No stitched MP4, shortform, new paid API, commit, push, or deployment.

## Review Focus

- Same person visible continuously through a face dropout or camera cut should not gain a new clip solely from that dropout or cut: Task 5 tests.
- Two people crossing or co-visible must not be merged to reduce split count: Task 5 tests.
- A body-only person should produce a reviewable appearance without a fabricated confirmed identity: Tasks 5 and 6 tests.
- Padding must not merge two adjacent appearances or clip assignments: Tasks 5 and 6 tests.
- Edits and downloads must survive project reload and preserve the bounds shown in preview: Tasks 6 and 7 tests.

---

### Task 1: Reconcile the Python Person MVP with current face core

**Files:** `desktop/clipper_python/pyproject.toml`, `uv.lock`, `plugins/person_highlight/{manifest.json,pyproject.toml,person_highlight/{__init__,__main__,app,analysis}.py,tests/*}` in the new worktree. Donor: corresponding files under `.worktrees/person-highlight-mvp-20261001`.

**Interfaces:** Retain plugin name `person_highlight`, `json/person_highlight.json`, source clip file paths, `analyze_video(...)` entrypoint. Current `clipper_face_core` 0.2.0 is the dependency; do not copy the old core package over it.

- [ ] Copy only Person-owned source and tests from donor; add workspace package/dependency entries without replacing current shared core.
- [ ] Run donor tests against current face core and record the first concrete incompatibility/failure.
- [ ] Write a failing compatibility test for each required adapter change; implement the smallest fix; rerun focused and full Person/core suites.

### Task 2: Reconcile Nest project, edit, ZIP, and workflow contracts

**Files:** Person-related donor additions in `desktop/clipper_nestjs/src/modules/{plugins,jobs,projects,sources,workflows}` and `test/person-*.test.js` plus focused donor tests.

**Interfaces:** Read `json/person_highlight.json`; expose project detail with `persons`, `clips`, `needsReview`, `sourceStartSec`, `sourceEndSec`; persist edits through existing project repository; serve per-clip MP4 and person/all ZIP from the project artifact root.

- [ ] Port Person-owned behavior to current `dev`, preserving newer project/job/plugin changes.
- [ ] Add failing tests for project detail, edit persistence, allowed paths, and ZIP membership; run red then implement/reconcile.
- [ ] Run `npm run build` and relevant `node --test` tests; record any baseline failures separately.

### Task 3: Reconcile Electron plugin installation and model files

**Files:** Person-related donor changes in `desktop/clipper_electron/src/main/{backend,plugin}` and focused `test/plugin-*.test.*`.

**Interfaces:** Register `person_highlight`; install its own venv with current `clipper-face-core` wheel and optional YOLO runtime; resolve the existing verified YuNet/SFace and `yolov8s-pose.pt` files without making Dance output a dependency.

- [ ] Port Person registration/model-presence code onto latest `dev`.
- [ ] Add failing tests for Person's face/pose model readiness, source fingerprint and venv package list; run red then implement.
- [ ] Run Electron build and focused tests.

### Task 4: Reconcile Angular setup, result, edit, and download UI

**Files:** Person donor additions in `desktop/clipper_angular/src/features/person-highlight`, `src/shell/projects/person-result-detail`, routing/navigation/readiness/project detail models and focused specs.

**Interfaces:** Use the Nest project detail contract from Task 2; the setup enters the normal jobs queue. Result UI shows every detected person and review state; selects clips, previews source, edits bounds and membership, and downloads MP4/person ZIP/all ZIP.

- [ ] Port Person UI to current `dev` with existing Material tokens and project shell.
- [ ] Write failing specs for route/readiness, `needsReview` display, result selection/edit/download events, and source preview; reconcile implementation.
- [ ] Run focused specs, Angular build, and style checks.

### Task 5: Replace face-only interval inference with body-assisted continuity

**Files:** `desktop/clipper_python/plugins/person_highlight/person_highlight/{body_detector.py,tracking.py,occurrences.py,analysis.py,app.py,manifest.json,pyproject.toml}` and focused tests. Keep responsibilities separate: detection adapter, shot-local tracks, identity/occurrences, orchestration.

**Interfaces:** `BodyDetection(bbox_px, score)` for every person; face observations remain from core. Output groups carry `person_id`, `status`, nullable representative image, intervals; clips carry `appearance_start_sec`, `appearance_end_sec`, `source_start_sec`, `source_end_sec`, `person_ids`, paths. `source_*` are padded export bounds.

- [ ] Create failing sequence tests for face dropout, turn to back, scene cut showing the same person, true departure, two people crossing/co-visible, and body-only person.
- [ ] Add a YOLO pose adapter that returns every person box and confidence, with a fake detector for deterministic tests; run tests red then green.
- [ ] Compare existing greedy IoU with a ByteTrack-style low-score second association on the fixed sequences; retain it only if false splits fall without false merges. Use BoT-SORT elements only for demonstrated remaining failures.
- [ ] Implement face-to-body association and identity decisions with explicit `confirmed/ambiguous/none` evidence; rerun focused tests.
- [ ] Derive appearances across shots based on evidence rather than always splitting at shot boundaries; preserve `needs_review` and co-visible cannot-link.
- [ ] Add 0.5-second initial export padding after appearances are final; do not merge assignments when padded windows overlap. Test boundaries and adjacency.
- [ ] Run full Python plugin/core tests and one bounded real-input analysis, recording source/model hashes, runtime and peak memory.

### Task 6: Carry new review and appearance/export bounds through the product

**Files:** Python manifest writer, Nest Person detail/edit/ZIP builder, Angular Person result view, and their focused tests in the new worktrees.

**Interfaces:** Python manifest `person-highlight.v2` includes appearance and padded export bounds; Nest detail maps both to distinct fields; edits modify the appearance and regenerate export bounds; UI labels review-only identities and previews/downloads the same padded export range.

- [ ] Write failing Python/Nest/Angular contract tests for body-only review, nullable representative, original versus padded bounds, overlapping padding, trim/restore, and ZIP.
- [ ] Implement schema mapping and edit/export regeneration while keeping old v1 project reads compatible.
- [ ] Run focused suites, all four builds, and Dance/Dialog regression tests touched by registration or shared files.

### Task 7: Verify and show the workflow

**Files:** bounded evaluation script/report under the new Python worktree; no product file changes unless a failing case identifies a defect.

**Interfaces:** Compare old face-only 37-minute result with candidate on source-checked intervals, plus distinct previously unseen human-containing videos. Preserve false-split, false-merge, misses, review cases, subsecond outputs, runtime, and hashes.

- [ ] Run bounded source-first evaluations; inspect failures on original frames, not only model predictions.
- [ ] Start the local product or an isolated preview and run source input → job → Person result → edit → MP4/person ZIP/all ZIP; check media and reload persistence.
- [ ] Fix only concrete failures with red/green tests; rerun affected suites and one end-to-end scenario.
- [ ] Show the user the running result or local preview and report verified behavior and remaining limits. Do not claim arbitrary-video accuracy from a single clip.
