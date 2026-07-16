# AI 숏폼 디렉터 — Vira evidence policy와 strategy input 구현 계획

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_DESIGN_2026-07-16.md`

## Task 1 — 실제형 fixture와 RED

- [x] Vira active Market 합성 fixture 추가
- [x] Tmarket last-3 peer growth 합성 fixture 추가
- [x] 성공한 8차원 analysis compact fixture 추가
- [x] payload validator와 duplicate id RED 테스트
- [x] admission policy RED 테스트

## Task 2 — Nest domain/application

- [x] current payload validation 구현
- [x] lifecycle/observation admission policy 구현
- [x] PlanningContext에 policy/admission 추가
- [x] `ContentStrategyV1 | null` 경계 추가
- [x] DTO/service/repository 저장 흐름 반영

## Task 3 — Angular manual handoff

- [x] director model/request 타입 확장
- [x] optional evidence JSON 입력과 client parse 오류 구현
- [x] lab/legacy opt-in 구현
- [x] admission count와 전략 미생성 표시
- [x] focused tests GREEN

## Task 4 — 검증·문서화

- [x] Nest focused/plugin tests와 build
- [x] Angular focused/plugin tests와 build
- [x] 기존 shortform 경로 diff 0
- [x] whitespace/status 확인
- [x] session/handoff 갱신
- [x] commit/push 없이 보고

## RED/GREEN 결과

RED:

- current payload validator가 percentile 101과 빈 analysis modules를 허용해 실패
- admission module이 없어 module-not-found 실패
- Angular evidence textarea가 없어 manual handoff UI 테스트 실패

GREEN:

- Nest director fixture/policy/foundation 6개 테스트 통과
- Nest plugin catalog/install/workflow registry 포함 18개 통과
- Angular director 등록/API/page 6개 통과
- Angular plugin status 회귀 포함 19개 통과
- Nest TypeScript build 통과
- Angular production build 통과
- 기존 Angular/Nest shortform 경로 `origin/dev` 대비 diff 0
- Vira `main@2f1d1fd` clean, read-only 유지
- commit/push/server/Electron 실행 없음
