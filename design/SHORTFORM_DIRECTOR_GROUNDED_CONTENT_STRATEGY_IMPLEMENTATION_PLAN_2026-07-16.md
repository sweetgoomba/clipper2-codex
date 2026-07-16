# AI 숏폼 디렉터 — grounded ContentStrategy 구현 계획

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_GROUNDED_CONTENT_STRATEGY_DESIGN_2026-07-16.md`

## Task 1 — 계약과 RED

- [x] Nest `BrandProfileV1`, expanded `CampaignBriefV1`, `SourcePackV1` 타입/validator RED
- [x] ContentStrategy shape와 grounding/reference validator RED
- [x] web API JWT·operation identity·structured output RED
- [x] Angular 입력/전략 실행 RED

## Task 2 — desktop Nest input/store

- [x] create DTO와 PlanningContext normalize/validation 구현
- [x] claim id uniqueness와 bounded input 적용
- [x] 기존 prompt-only request의 보수적 기본값 유지

## Task 3 — web API strategy endpoint

- [x] `shortform_director.strategy` operation definition과 seed migration 추가
- [x] 독립 controller/module/service/prompt 구현
- [x] DB OpenAI credential, strict JSON Schema, `store: false` 적용
- [x] output shape/reference validation 구현

## Task 4 — desktop Nest orchestration

- [x] 전용 web API client 구현
- [x] strategy endpoint와 owner/auth 확인 구현
- [x] operation start/succeed/fail 흐름 구현
- [x] validated ContentStrategy project 저장 구현

## Task 5 — Angular UI

- [x] expanded brief와 brand/source claim 입력 구현
- [x] operation quote/confirm 후 strategy 생성 구현
- [x] strategy 상태와 핵심 결과 표시 구현

## Task 6 — 검증·문서화

- [x] web API focused tests/build
- [x] desktop Nest focused tests/build
- [x] Angular focused tests/build
- [x] 기존 shortform 경로 diff 0
- [x] Vira read-only clean 확인
- [x] `.codex` session/handoff 갱신
- [x] commit/push/server/migration 실행 없이 보고

## RED/GREEN 결과

RED:

- desktop Nest는 `planning-context.v2`가 없어 foundation assertion 1건이 실패했다.
- ContentStrategy contract module 부재로 grounding test 4건이 실패했다.
- strategy orchestration service 부재로 billing/persistence test 2건이 실패했다.
- web API는 operation definition과 controller/service module 부재로 3 suite가 실패했다.
- Angular는 expanded input signal과 strategy API 부재로 compile 단계에서 실패했다.

GREEN:

- desktop Nest director/plugin 집중 묶음 18/18 통과, TypeScript build 통과
- web API strategy/operation 집중 묶음 33/33 통과, Nest build 통과
- Angular director/route/navigation/plugin 집중 묶음 44/44 통과, production build 통과
- web API 새 production source ESLint error/warning 0
- 세 저장소 whitespace/diff 검사 통과
- 기존 Angular/Nest/web API shortform 경로 `origin/dev` 대비 diff 0
- Vira `main@2f1d1fd` clean, read-only 유지

실제 OpenAI credential/provider 호출, migration 실행, server/Electron 실행, commit/push/deploy는 수행하지 않았다.
