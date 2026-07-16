# AI 숏폼 디렉터 — asset acquisition과 수동 대체 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`

## Task 1 — RED domain contract

- [x] search/generated layer별 acquisition 초기 snapshot 테스트를 추가한다.
- [x] queue/start/succeed/fail/cancel/retry 상태 전이 테스트를 추가한다.
- [x] non-retryable 실패와 잘못된 전이 거부 테스트를 추가한다.
- [x] manual replacement media/origin 호환성과 reason 테스트를 추가한다.
- [x] 구형 AssetPack read-only hydration 테스트를 추가한다.

## Task 2 — NestJS foundation

- [x] `asset-acquisition.v1`과 binding mode 계약을 추가한다.
- [x] 순수 acquisition state machine을 구현한다.
- [x] `buildAssetPack()`이 acquisition을 생성·보존·prune하도록 확장한다.
- [x] JSON repository가 acquisitions와 기존 binding mode를 read-only 보강하도록 한다.
- [x] owned/source binding과 search/generated manual replacement를 서버가 구분한다.
- [x] 수동 대체 해제 후 기존 acquisition 상태를 보존한다.

## Task 3 — Angular UX

- [x] acquisition과 binding mode model을 반영한다.
- [x] search/generated pending requirement에 acquisition 상태를 표시한다.
- [x] search/generated에 기존 project artifact 수동 대체 picker를 제공한다.
- [x] media compatibility로 후보를 필터링한다.
- [x] 연결된 카드에 수동 대체를 표시한다.
- [x] provider 실행·재시도·render control 부재를 회귀 검증한다.

## Task 4 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] raw color, secret-like token, trailing whitespace를 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.

## 구현 결과

- desktop Nest build와 `test/shortform-director-*.test.js` 39/39 통과
- Angular production build와 `features/shortform-director/**/*.spec.ts` 19/19 통과
- 기존 Angular/Nest/web shortform 경로는 `origin/dev` 대비 diff 0
- Angular 새 SCSS raw color 0, 변경 diff whitespace·고신뢰 secret pattern 검사 통과
- 실제 acquisition endpoint, provider 호출, operation charge, renderer control은 추가하지 않음
