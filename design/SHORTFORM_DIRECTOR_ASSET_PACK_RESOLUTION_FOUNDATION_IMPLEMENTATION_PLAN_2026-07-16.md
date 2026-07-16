# AI 숏폼 디렉터 — AssetPack/AssetRef resolution foundation 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`

## Task 1 — RED domain contract

- [x] 대표 45초 VideoPlan으로 requirement/status/summary expected를 고정한다.
- [x] programmatic, missing ref, unresolved route를 구분하는 실패 테스트를 작성한다.
- [x] 합성 ref/binding의 호환성, availability, rights 회귀를 추가한다.
- [x] resolver 부재 RED를 확인한다.

## Task 2 — project lifecycle

- [x] `asset-pack.v1`, `asset-ref.v1`, requirement/binding 타입을 추가한다.
- [x] 순수 AssetPack resolver를 구현한다.
- [x] 새 project와 strategy reset에 empty AssetPack을 저장한다.
- [x] VideoPlan 저장 시 새 plan 기준 AssetPack을 함께 저장한다.
- [x] assetPack 없는 구형 JSON을 read-only hydration한다.

## Task 3 — Angular readiness UX

- [x] Angular model에 AssetPack 계약을 반영한다.
- [x] 준비/전체, missing, unresolved 요약을 표시한다.
- [x] pending visual layer의 위치, role, route와 다음 행동을 구분한다.
- [x] render/provider/picker control이 없음을 테스트한다.

## Task 4 — 문서·회귀 검증

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 집중 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] raw color, secret-like token, trailing whitespace를 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.
