# Meme overlay checkpoint — 2026-08-21

## Scope completed

- Plan 1: Web API catalog, NestJS download/cache/local Range streaming, plugin registration, and Python authoring tool.
- Plan 2: Angular source intake, catalog/library, two-overlay timeline, transform/settings UI, and layered real-time preview.
- Preview width regression fixed so the preview host fills `setup__editor` instead of collapsing to about 140–156px.
- Authoring tool computes the union of every frame's alpha bounding box, applies 16px safe padding and even alignment, and uses one static crop for both card and overlay output.

## Checkpoint commits

- `clipper_web_api`, branch `feat/meme-overlay`: `eab77ea feat: add meme asset catalog API`
- `clipper_nestjs`, branch `feat/meme-overlay`: `2c60b6d feat: add meme asset cache and local endpoints`
- `clipper_python`, branch `feat/meme-overlay`: `4a58972 feat: add transparent meme asset authoring`
- `clipper_angular`, branch `feat/meme-overlay`: `e5528e9 feat: add meme overlay editor preview`
- `clipper_electron`: no source commit was required.
- No feature branch was pushed or merged. Worktrees remain because Plan 3 is pending.

## Local test catalog separation

- The tracked production catalog remains empty: `meme-assets.catalog.json` has `assets: []`.
- Non-production Web API can load an explicit local catalog through `MEME_ASSETS_CATALOG_PATH`.
- Production mode ignores this override even when the variable is present.
- This worktree's ignored `.env` points to `/Users/jina/Library/Application Support/Clipper Studio/meme-assets/local-catalog.json`.
- Local API startup must explicitly use `NODE_ENV=development` and `DEV_LOGIN_ENABLED=true`; otherwise the production safety gate ignores the local catalog and disables dev-login.

## Local test assets retained outside git

Root: `/Users/jina/Library/Application Support/Clipper Studio/meme-assets/`

- `hitting-cat/v1`: 때리는 고양이, 748×930
- `crunchy-cat/v1`: 크런치 고양이, 628×956
- `angry-cat/v1`: 화난 고양이, 532×982

Each version retains `card-preview.webm`, `overlay.webm`, and cache metadata. These files and the local catalog are not bundled into the Electron app and are not tracked by an application repository. They are local technical-test assets only; rights approval and production CDN publication remain separate work.

## Verification at checkpoint

- Web API: 97 suites, 609 tests passed; build passed.
- NestJS: build passed; meme/shared Range focused suite 71/71 passed.
- NestJS full suite: 956/957 passed. The single failure is the pre-existing `shortform-clip-generation-events` fixture using an outdated `ShortformProjectService` constructor; it is outside the meme-overlay diff.
- Python: 464 passed, 4 skipped; focused authoring tests 18 passed; Ruff and `py_compile` passed.
- Angular: ChromeHeadless full suite 2753/2753 passed; production build and breakpoint stylesheet suite 6/6 passed.
- The local Web API returned exactly the three local meme IDs after the tracked production catalog was emptied.

## Deliberately preserved state

- Angular's pre-existing mechanical `package-lock.json` change was not included in the feature commit and remains unstaged.
- `.codex` is a standalone Git repository. This checkpoint and the four meme-overlay design/plan documents are committed there separately from the application repositories.
- `clipper_docs` was not modified.
- Temporary build symlinks and packaging-only copied key/binary files were removed. The local catalog and six WebM files were retained.

## Remaining work

- Plan 3: final FFmpeg render, render job/status UX, output save/export, project persistence, and reopen/re-edit flow.
- Manual acceptance should be repeated after Plan 3 because the current checkpoint proves editing and preview, not final result generation.

## Documentation collision rule

- Do not use one shared live scratch file across sessions.
- Each session creates or appends only to its uniquely scoped task/report file.
- Before editing an existing tracked `.codex` document, inspect repository status and verify that no other active session owns that file.
- Stage exact paths only; do not use `git add .` while unrelated session documents are present.
- Prefer a new date/task-specific checkpoint file for cross-plan summaries, as done here.
