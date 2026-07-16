# AI 숏폼 디렉터 — Diagram step copy 소유권 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`

## Task 1 — Web API contract RED

- [x] strict response schema가 모든 Layer에 `programmaticPayload`를 요구하는지 검증한다.
- [x] diagram payload가 exact schema/primitive/step id와 authored label을 보존하는지 검증한다.
- [x] non-diagram payload가 null이 아니면 거부하는지 검증한다.
- [x] diagram payload의 누락, 잘못된 순서, 중복 label, prohibited expression을 거부하는지 검증한다.

## Task 2 — Web API GREEN

- [x] draft Layer type과 JSON schema에 nullable programmatic payload를 추가한다.
- [x] prompt에 headline/step ownership과 grounding 제한을 명시한다.
- [x] parser가 diagram object/non-diagram null을 fail-closed로 검증한다.
- [x] renderer/provider/path/URL/artifact 정보를 생성 계약에 추가하지 않는다.

## Task 3 — Desktop VideoPlan RED와 GREEN

- [x] stored VideoPlan Layer에 optional diagram payload type을 추가한다.
- [x] 새 diagram draft는 payload를 필수로 검증한다.
- [x] exact step identity/order, label length/uniqueness, prohibited expression을 검증한다.
- [x] non-diagram payload를 거부하고 정상화 결과에서는 null을 생략한다.
- [x] 대표 45초 fixture에 authored diagram copy를 추가한다.

## Task 4 — Compiler와 preview RED/GREEN

- [x] motion builder가 caller-provided step copy만 받도록 바꾼다.
- [x] compiler가 authored payload를 motion content에 그대로 전달한다.
- [x] payload 없는 legacy stored plan에만 `상황/확인/행동` fallback을 적용한다.
- [x] malformed stored payload는 compile error로 중단한다.
- [x] Angular 모델에 payload를 반영하고 기존 preview가 recipe copy를 그대로 표시하는지 검증한다.

## Task 5 — 회귀와 문서

- [x] Nest Director 전체 테스트와 build를 실행한다.
- [x] web API video-plan/관련 전체 테스트와 build를 실행한다.
- [x] Angular Director 전체 테스트와 production build를 실행한다.
- [x] 기존 shortform 경로 working-tree 변경 0을 확인한다.
- [x] whitespace, raw color, secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] renderer/provider/server/Electron/migration/DB/runner/commit/push/deploy를 실행하지 않는다.
