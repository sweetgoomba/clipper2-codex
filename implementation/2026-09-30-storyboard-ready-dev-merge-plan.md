# W07 completed work → dev integration plan

> **For agentic workers:** Use Superpowers TDD, verification-before-completion, and finishing-a-development-branch. This plan tracks only the independently complete work selected for integration; keep the original W07 worktrees untouched.

**Goal:** Merge the narrow, user-requested and locally verified W07 bug/UI fixes into current `origin/dev` without treating the team's legacy plan or W07 checkboxes as user approval.

**Architecture:** Prepare clean Angular/Nest integration worktrees from current `origin/dev`. Port cohesive completed changes with tests, then merge each verified branch into local and remote `dev` only after checking the final diff and preserving unrelated original checkout edits. Keep the W07 source branch for unfinished work.

**Tech Stack:** Angular/Material, NestJS/node:test, Electron package smoke, Git worktrees.

**Spec:** `.codex/handoff/tasks/storyboard.md`, `.codex/implementation/2026-09-30-storyboard-v2-design-audit.md`, and current user request.

## Global constraints

- Preserve user data and historical storyboards; do not run real generation, billing, or destructive migrations.
- Include only: read-only deleted-record boot compatibility (Nest), Korean keyword IME fix (Angular), purpose deselection/save fix (Angular), name 50/purpose 150 and purpose explanation/placeholders (Angular + Nest). The 50-character rule also requires duplicate-name truncation (Angular).
- Exclude the deletion UI/API, legacy cleanup, progress meter/messages, settings alignment, card hover tint and completed-count vertical centering, shared dialog focus, deleted-profile duplicate tooltip, Web ledger, all performance instrumentation/optimization, and anything else not necessary for the included behavior. The card treatment is awaiting final user visual confirmation.
- The read-only deleted-profile record parser is necessary to let `dev` boot with already-written deletion records. It must not expose a delete endpoint or resurrect profiles.
- Do not touch the unrelated dirty Angular design spec in original `dev`.
- Do not erase or reset the W07 worktree; integration is a separate branch in each affected repo.

## Review focus

- Two deleted-profile records in an otherwise valid catalog: startup succeeds, active list/index excludes both, detail bytes remain.
- Stale index referencing a deleted record repairs without making it active; malformed records still fail closed.
- Preserved batch snapshot/results and home project data remain readable after startup.
- Angular's selected change set does not accidentally expose unfinished selection deletion, legacy UI, or progress changes.
- Latest Angular `dev` changes remain present after integration.

## Tasks

### 1. Nest boot compatibility

- [x] Baseline clean integration worktree, write deleted-record startup regression against the existing repository, and observe RED with the original schema-validation error.
- [x] Port only the W07 deleted-record reader/catalog reconciliation, leaving delete mutation/API out; run focused GREEN and profile API/storage tests + build.
- [x] Recheck the selected Nest parser against an isolated copy of the actual profile directory: startup OK, active 6/deleted 2, deleted IDs absent, all 8 detail-file checksums unchanged. Build this branch's Nest ncc bundle and run it in packaged mode with packaged env/public key, Electron's dance data path, and the same isolated profile-data copy; `/v1/health` returned `status: ok`. The earlier W07 batch/project preservation check is documented separately; this narrow integration has not rerun the whole Electron GUI package.

### 2. Narrow completed bug/UI changes

- [x] Inventory exact Angular/Nest hunks and dependencies for the four included behaviors, excluding mixed W07 delete/legacy/progress files; affected code is the Angular form and duplicate-name method, Nest profile service/DTO and read-only catalog parser.
- [x] Port selected behavior with regressions, including API/UI contracts. Deleted-record startup, service name limit, and duplicate suffix tests were observed RED→GREEN; form tests 29/29 PASS.
- [x] Initial Angular full Karma 5413/5413, styles 6/6, local build; Nest profile API/storage 41/41 and TypeScript build. Review found old stored values, Unicode input, and duplicate-data regressions; these were fixed. Final Angular full Karma **5418/5418**, styles **6/6**, local build; Nest profile API/storage **38/38**, TypeScript build and ncc bundle. DTOs retain the stored 120/500 schema; HTTP and service tests prove the new 50/150 write policy. A new Electron GUI package was not built; do not represent the previous W07 package as this branch's package.

### 3. Integration

- [x] Review final diffs for unfinished deletion, ledger, performance optimization, secrets, and conflicts with latest `dev`. Independent review found old-value/Unicode issues, then a distinct-objective duplicate regression; all were fixed and final review found no blocker.
- [x] Commit isolated Angular `5570f8ca` and Nest `c8b8b07`; fast-forward local `dev`. The original Angular design-spec edit remained untouched. Post-merge Angular Karma **5418/5418**; Nest initially loaded stale `dist`, then `npm run build` and profile API/storage **38/38** passed.
- [x] Push both `dev` branches after confirming no remote movement; `git ls-remote` matches each local SHA. Nest checkout is clean; Angular retains only the pre-existing design-spec edit. Update W07 board/card with exact partial-merge scope and exclusions.
