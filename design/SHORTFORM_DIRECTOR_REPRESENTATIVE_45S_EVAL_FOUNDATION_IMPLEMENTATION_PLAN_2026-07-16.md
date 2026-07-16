# AI 숏폼 디렉터 — 대표 45초 품질 eval foundation 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`

## Task 1 — RED fixture contract

- [x] 45초 eval case JSON과 expected report를 먼저 추가한다.
- [x] 기존 Vira evidence, ContentStrategy, VideoPlan validator를 한 번에 통과하는 테스트를 작성한다.
- [x] evaluator 부재로 실패하는 RED를 확인한다.

## Task 2 — deterministic evaluator

- [x] `video-plan-quality-report.v1` 타입과 순수 evaluator를 추가한다.
- [x] blocking check와 warning check를 분리한다.
- [x] structural metrics를 결정적으로 계산한다.
- [x] manual review 축은 점수 없이 명시한다.

## Task 3 — mutation regression

- [x] hook이 3초 뒤 시작하는 변형이 blocking fail인지 확인한다.
- [x] grounding 누락과 잘못된 authenticity route를 fail로 확인한다.
- [x] narration 과밀과 unresolved asset을 warning으로 확인한다.
- [x] 입력 객체를 변경하지 않는지 확인한다.

## Task 4 — 문서·회귀 검증

- [x] desktop Nest 관련 테스트와 build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] secret-like token, trailing whitespace를 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.
