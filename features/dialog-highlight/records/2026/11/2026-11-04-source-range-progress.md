# Progress
Plan: 2026-11-04-source-range-plan.md
State: implementation, review and verification complete; changes retained uncommitted.

## Result
- Dialog uses SourceSceneOverlayComponent and ClipTrimmerComponent already shared by Person/Dance. Edit-only mode, min 3s, numeric fields.
- Initial viewport existing clip plus 5s context each side, min12s, clamped source bounds. Widen2x, narrow0.5x and pan preserve draft; display range does not alter saved selection.
- UI absolute source times adapt to persisted original-clip relative offsets (negative front extension allowed). Exact original bounds alone trigger revert.
- Backend source recut writes clips/raw derived media, preserving manifest and sidecar contract. Existing preview/download/render consume derived media; full STT supplies newly included words.
- Dialog authenticated __source__ tickets check ownership/local file availability. Missing source ticket clears stale availability and uses clip-only fallback.
- If an already-expanded edit loses source, fallback draft is clamped to remaining original clip; persisted selection stays intact until explicit save/restore.

## Review
- Independent cross-repo reviewer approved after two P2 fixes: IEEE source-boundary epsilon/clamp; expanded trim normalization when source disappears.
- Both fixes have observed failing regressions followed by passing tests. No further important findings.

## Verification
- Frontend baseline219 passed; initial six new failures observed before implementation.
- Related final frontend suite309 passed, styles21 passed, final local app build passed.
- First full frontend run10725 passed before source-missing follow-ups. Latest full10728:10726 passed,2 failures unrelated to changed code:
  - StoreComponent: [모두 설치]가 사라져도(N=0) 카드가 움직이지 않는다 (3px layout discrepancy). Already passed in related309 isolation.
  - TemplateBuilderEditorComponent: 배경 추가가 실패하면(서버 거부 등) 에러 토스트를 올리고 자동으로 사라지지 않는다 (toast spy call not settled).
- Both unrelated frontend failure files passed together in isolation:276/276, /private/tmp/dialog-source-fe-unrelated-rerun.log. Latest full-suite run still recorded as2 failures; do not describe it as green.
- Backend final build passed; focused113 passed0 skipped including actual ffmpeg source extension, manifest immutability and revert.
- Full backend5404:5381 passed14 failed9 skipped initially.13 font/load failures recovered in48-test isolated rerun after supplying sibling bundled font assets. One unrelated fixture gap remains: ignored .env.packaged absent (template-builder-no-s3-storage.test.js). Full suite is not green.
- Actual ng serve route/nav/provider smoke with isolated synthetic1800s video and mock API: initial600..630 viewport595..635; edit590..650 and widen575..655 retains60s draft; save request signed -10..50; saved detail updates; restore returns600..630. Dark and light checked.
- Smoke temporarily pointed local web API at fixture9019; original environment.local.ts restored byte-for-byte. Test browser/API/ng serve stopped; original application data untouched.
- Screenshots /private/tmp/dialog-source-smoke/editor-dark.jpg and editor-light.jpg. Reports /private/tmp/dialog-source-backend-report.txt and dialog-source-review.txt.
- Both repos git diff --check clean. No commit, merge, push or deploy.

## Worktrees
- Angular /Users/jina/project/adlight/.worktrees/dialog-source-range/desktop/clipper_angular (feat/dialog-source-range, base7b559706c)
- Nest /Users/jina/project/adlight/.worktrees/dialog-source-range/desktop/clipper_nestjs (feat/dialog-source-range, basea5f8db6f)
- Dependencies linked to existing node_modules; backend sibling clipper_python symlink only supplies bundled fonts. Worktrees retained.
