# W14 testable MVP implementation plan (2026-10-01)

User-approved scope: existing source input and queue; anonymous all-person results; one-page people, clips, source preview; view timeline and edit handles; per-person ZIP, per-clip MP4, all ZIP. No stitched MP4 or shortform.

1. Python: add independent optional face core with explicit model/source/config provenance and all-face observations. Add a person plugin that samples source video, tracks multiple faces within shots, clusters tracks with same-frame cannot-link, emits intervals and representative images, and exports original-sound clips. Use existing YuNet/SFace verified files; no automatic new model download in this task.
2. Nest: parse person manifest into a many-to-many project detail; persist person labels, merges, clip reassignment, exclusion/restore, representative changes, and trims in a sidecar. Keep clip paths under project root and ZIP selection membership explicit.
3. Angular: add person setup based on existing shared source input/confirmation; route through home queue; add a three-column result workspace with all groups visible. Reuse page shell, Material buttons, semantic tokens, media tickets, and current download service.
4. Electron: register plugin runtime/model presence with existing per-plugin venv and model consent. Include common package in plugin source fingerprint. Keep ML optional for default SDK installs.
5. Verification: deterministic synthetic observation/contract tests, Nest endpoint/detail tests, Angular focused tests, build/style checks. Real video inference needs the separately specified input/GT/model/resource manifest; no performance claim from unit tests.

Implementation repositories are isolated worktrees at `.worktrees/person-highlight-mvp-20261001/desktop/*`, each from fetched `origin/dev` on branch `feature/person-highlight-mvp-20261001`. No commits or pushes without explicit request.
