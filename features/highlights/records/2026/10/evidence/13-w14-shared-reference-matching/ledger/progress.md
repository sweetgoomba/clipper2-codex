# SDD ledger — plan: /Users/jina/project/adlight/docs/superpowers/plans/2026-10-13-shared-reference-face-matching.md

User approved plan and Native execution: 니 추천대로 진행해.
Base: fetched origin/dev 47782953228861f4bdbdc135265d067c2a826b0e.
Ruling: Native worktree API returned Not a git repository at shared root; used Git worktree in the Python repository, preserving sibling layout — necessary fallback; no automatic app worktree attachment.
Ruling: No commits or cleanup of ledger until explicitly requested — repository rule takes precedence; review must include untracked files and uncommitted diff.
Pre-flight: Task1 DTO → Task2 gallery → Task3 matching → Task4 consensus: signatures consistent. Task5 imports those APIs; Task6 consumes them without Dance types.
Ruling: zero valid results retain failures; constructor metadata validation must not erase invalid embedding results — distinguish malformed provenance from ML failure; misuse otherwise becomes exception rather than per-query invalid.
Task 1: in progress
Task 1: RED 9 failed/1 passed (missing contracts/eager cv2), GREEN 20 passed. Baseline copied 10 passed.
Ruling: ReferenceMatch includes evidence_fingerprint beyond the initial field list — bind decisions to exact vector/provenance, not just observation ID; otherwise stale results could validate a changed query.
Task 1: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests -p no:cacheprovider -q → 20 passed in 0.39s)
Task 2: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests -p no:cacheprovider -q → 32 passed in 0.47s)
Task 3: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests -p no:cacheprovider -q → 47 passed in 0.64s)
Task 4: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests -p no:cacheprovider -q → 60 passed in 0.63s)
Task 5: RED 6 expected missing-module failures; GREEN core+replay 66 passed. Actual replay: 23 references/54 queries, all 5 centroids array-equal, all 54 assigned IDs/unknown reproduced, distance max delta 0. Three saved512 track3 observations agree on 해린 vs previous final 하니. Not held-out accuracy. Model calls 0. Supervisor success 0.194s/RSS sampled 37,371,904 bytes; result worker metrics archived outside Git source.
Task 5: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests evaluation/reference_matching/tests -p no:cacheprovider -q → 66 passed in 0.75s)
Task 6: complete (commits 4778295..4778295, tests: env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=clipper_face_core:clipper_plugin_sdk /Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python -m pytest clipper_face_core/tests evaluation/reference_matching/tests -p no:cacheprovider -q → 68 passed in 0.60s)

Task 6: consumer tests RED 2 missing-file failures → GREEN full selected 68; donor core+Person compatibility 27 passed using new core path. Ruff passed. README/handoff API ready; final .codex status to be reconciled after review.

Final review: independent fresh-context review; 0 Critical, 3 Important, 0 Minor. All three accepted as Important by observable consumer impact.
Final: fixed invalid centroid poisoning valid references — test_nearly_cancelled_reference_does_not_invalidate_other_references RED→GREEN.
Final: fixed conflicting observation IDs across scopes — test_consumer_rejects_conflicting_observation_ids_across_batch (two cases) and test_consumer_deduplicates_identical_observations RED→GREEN.
Final: fixed missing ownership silently confirmed — test_missing_ownership_is_not_assumed_confirmed RED→GREEN.
Final selected suite: 73 passed in 0.77s. Final wider suite: 617 passed/3 skipped in 33.72s, 11 plugin boot smoke cases excluded. Final donor compatibility: 27 passed in 0.25s. Ruff passed. Review source fixes done in one pass; no second reviewer.
Final: Ruling: independent recognition and face ownership accuracy remains unverified — stored diagnostic rows prove reproducibility only; claiming improvement could hide wrong-member errors.
Final: Ruling: actual Dance/Person integration and plugin installation remain W13's next consumption step — example and API are ready, but no production adapter changed; deploying without that step could leave old mapping or miss package installation.
Final: Ruling: Windows remains unverified — current evidence is macOS; package imports, paths or runtime dependencies could differ.
Final: Ruling: donor grouping and detector selection behavior are preserved — this slice isolates reference matching; prior grouping/face-selection limitations still apply.
Final: Ruling: broader suite first stopped at sandbox localhost binds (4 failed/16 errors), not product assertions — reran allowed localhost tests with existing env and no synchronization; all 9 affected non-boot cases passed in the wider run. Eleven model-boot smoke cases remain unverified because this package-only slice has no new model startup manifest; do not call this full product E2E coverage.
Final: Ruling: supervisor runs verified by parent, not reviewer — final stored-feature replay stopped on no limit and exited 0 under 120s/2GiB/25MiB caps; RSS is polled, so transient between-poll peaks are not an OS-enforced hard cap.
Final: Ruling: keep branch, worktree and ledger without commit/merge/cleanup — no commit authorization and W13 has yet to consume this uncommitted package; loss risk until committed, so durable hash inventory/evidence are saved.
Final: minor (deferred): none.
