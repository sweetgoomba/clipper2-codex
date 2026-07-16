# AI 숏폼 디렉터 — RenderRecipe compiler foundation 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`

## Task 1 — representative compiler RED

- [x] ready AssetPack + tts_aligned plan + ready narration fixture를 조립한다.
- [x] 기존 `render-recipe.v1` identity/output/track 수를 검증한다.
- [x] external visual, TTS, subtitle, overlay mapping을 검증한다.
- [x] 모든 20개 Layer의 hierarchy/timing/source metadata를 검증한다.
- [x] path/URL/provider secret이 없고 동일 입력이 deterministic함을 검증한다.

## Task 2 — compile gate RED

- [x] estimated/empty plan을 거부한다.
- [x] waiting/blocked/stale AssetPack을 거부한다.
- [x] empty/stale/mismatched narrationAudio를 거부한다.
- [x] cue measurement와 artifact mismatch를 거부한다.
- [x] invalid Layer containment와 missing binding/ref를 거부한다.

## Task 3 — Nest implementation

- [x] 기존 `RenderRecipe`를 출력하는 Director compiler를 추가한다.
- [x] current plan 기반 AssetPack recompute gate를 추가한다.
- [x] narration exact-set/alignment gate를 추가한다.
- [x] Director composition metadata와 최소 programmatic primitive를 추가한다.
- [x] owner-scoped read-only compile service/controller endpoint를 추가한다.

## Task 4 — Angular RED와 최소 UI

- [x] Director render-recipe GET service 테스트를 추가한다.
- [x] asset+narration ready에서만 compile action을 활성화한다.
- [x] duration/visual/programmatic/TTS/caption summary를 표시한다.
- [x] operation charge와 renderer/render control 부재를 검증한다.
- [x] semantic token 기반 작은 compile summary panel을 추가한다.

## Task 5 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] whitespace, raw color, secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] server/Electron/renderer/provider/commit/push/deploy를 실행하지 않는다.
