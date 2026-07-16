# AI 숏폼 디렉터 — Programmatic motion과 deterministic preview PoC 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`

## Task 1 — Nest motion contract RED

- [x] `diagram.sequence-card.v1` motion spec identity/content/layout/animation을 검증한다.
- [x] start/reveal/hold/exit/end reference frame을 검증한다.
- [x] sampler determinism, input immutability와 progress boundary를 검증한다.
- [x] color/font/path/URL/provider 정보가 없음을 검증한다.

## Task 2 — RenderRecipe embedding RED

- [x] 대표 diagram overlay에 motion spec이 들어가는지 검증한다.
- [x] duration과 headline이 source Layer와 일치하는지 검증한다.
- [x] text overlay에는 motion spec이 없는지 검증한다.
- [x] 같은 project snapshot의 recipe가 deep equal인지 유지한다.

## Task 3 — Nest GREEN

- [x] 순수 programmatic motion domain contract와 sampler를 추가한다.
- [x] RenderRecipe compiler의 diagram overlay에 motion spec을 연결한다.
- [x] renderer/provider/service/endpoint는 추가하지 않는다.

## Task 4 — Angular RED와 GREEN

- [x] RenderRecipe model에 지원 motion contract를 추가한다.
- [x] 4파일 standalone sequence-card preview component를 추가한다.
- [x] normalized layout과 reference frame state를 DOM에 적용한다.
- [x] hold frame을 기본 선택하고 기준 frame 선택을 지원한다.
- [x] Director page가 compiled recipe의 지원 primitive만 preview한다.
- [x] autoplay/render/audio/operation charge가 없음을 검증한다.

## Task 5 — 회귀와 문서

- [x] Nest Director 전체 테스트와 build를 실행한다.
- [x] Angular Director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform working-tree 변경 0을 확인한다.
- [x] whitespace, raw color, secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] server/Electron/renderer/provider/commit/push/deploy를 실행하지 않는다.
