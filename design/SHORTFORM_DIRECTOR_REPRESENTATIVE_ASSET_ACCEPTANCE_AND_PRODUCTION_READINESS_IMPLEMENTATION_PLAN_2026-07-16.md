# AI 숏폼 디렉터 — 대표 AssetPack acceptance와 production readiness 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`

## Task 1 — RED acceptance fixture

- [x] 대표 45초 project-artifact AssetRef/binding fixture를 추가한다.
- [x] planned local, manual replacement, provider-required 집계를 고정한다.
- [x] 전부 수동 해소한 ready 변형을 고정한다.
- [x] pending/retryable/non-retryable/succeeded-without-binding 변형을 고정한다.
- [x] evaluator 입력 불변성을 검증한다.

## Task 2 — NestJS readiness contract

- [x] `asset-production-readiness.v1` model을 추가한다.
- [x] 순수 production readiness evaluator를 구현한다.
- [x] `AssetPackV1.productionReadiness`를 추가한다.
- [x] empty/build/hydration lifecycle에서 report를 결정적으로 재계산한다.
- [x] 기존 exact AssetPack 기대값을 새 계약에 맞게 갱신한다.

## Task 3 — Angular summary

- [x] production readiness model을 반영한다.
- [x] ready/waiting/blocked/empty 상태 문구를 추가한다.
- [x] resolved/local/provider/blocking summary를 표시한다.
- [x] render/provider control 부재를 회귀 검증한다.

## Task 4 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] raw color, secret-like token, trailing whitespace를 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.

## 구현 결과

- 대표 acceptance fixture는 visual 10개 중 9개 해결, local resolution 8개, provider-required 1개를 고정한다.
- 마지막 search layer를 manual replacement하면 10/10 ready와 `renderable: true`가 된다.
- running/retryable failure는 waiting, non-retryable failure와 materialization 불일치는 blocked다.
- desktop Nest build와 director 테스트 43/43 통과
- Angular production build와 director 테스트 19/19 통과
- 기존 Angular/Nest/web shortform 경로 `origin/dev` 대비 diff 0
- raw color, whitespace, 고신뢰 secret-like pattern 검사 통과
- provider 실행, renderer, operation charge, server/Electron, migration, commit/push 없음
