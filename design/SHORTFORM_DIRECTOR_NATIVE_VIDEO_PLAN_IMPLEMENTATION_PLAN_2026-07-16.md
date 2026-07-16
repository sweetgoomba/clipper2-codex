# AI 숏폼 디렉터 — native VideoPlan planner 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`

## 구현 원칙

- 기존 `shortform_prompt` 경로를 건드리지 않는다.
- 새 `shortform_director` 모듈과 feature 안에서만 구현한다.
- 먼저 실패 테스트로 public input, provider output, timeline, grounding, 과금 경계를 고정한다.
- renderer/provider/AssetRef/compiler를 미리 만들지 않는다.
- 문서는 `.codex`에만 둔다.

## Task 1 — desktop VideoPlan 계약 RED/GREEN

- [x] generated draft fixture와 validator 실패 테스트를 추가한다.
- [x] target duration, 0-based order, scene/beat/shot coverage를 검증한다.
- [x] layer route/role, grounding coverage, hook/CTA, prohibited expression을 검증한다.
- [x] server-owned id/derivation과 narration cue 조립을 구현한다.

검증:

```bash
npm run build
node --test test/shortform-director-video-plan.test.js
```

## Task 2 — desktop orchestration/API

- [x] `matrixEntryId` DTO와 director 전용 endpoint를 추가한다.
- [x] owner, ContentStrategy, matrix↔hypothesis, JWT, preflight를 확인한다.
- [x] 선택 hypothesis에 필요한 candidate evidence/claims만 web API input으로 만든다.
- [x] `shortform_director.video_plan` operation start/succeed/fail을 연결한다.
- [x] 성공만 전용 project store에 저장하고 실패 시 이전 plan을 유지한다.

## Task 3 — web API structured planner

- [x] 독립 `shortform-director-video-plan` module을 추가한다.
- [x] public input runtime validator를 추가한다.
- [x] strict `video-plan-draft.v1` JSON Schema와 prompt를 추가한다.
- [x] provider output을 timeline/grounding/quality 규칙으로 다시 검증한다.
- [x] JWT, OpenAI scope와 정확한 operation key를 요구한다.
- [x] input/provider diagnostic을 log에 남기지 않는다.

검증:

```bash
npm test -- --runInBand src/modules/shortform-director-video-plan
npm run build
```

## Task 4 — operation policy

- [x] definition에 `shortform_director.video_plan` 10 credit 초기값을 추가한다.
- [x] admin migration을 추가하고 DataSource에 등록한다.
- [x] migration 코드는 테스트하되 실행하지 않는다.

## Task 5 — Angular 선택·요약 UI

- [x] dedicated service에 VideoPlan 생성 endpoint를 추가한다.
- [x] matrix entry별 생성 액션과 billing confirm을 추가한다.
- [x] 생성 중 상태와 plan hierarchy 개수 요약을 표시한다.
- [x] render/asset/provider control은 추가하지 않는다.

검증:

```bash
npm test -- --watch=false --include='src/features/shortform-director/**/*.spec.ts'
npm run build
```

## Task 6 — 회귀·문서화

- [x] 세 저장소 관련 테스트와 build를 실행한다.
- [x] 기존 shortform 코드 경로가 `origin/dev` 대비 diff 0인지 확인한다.
- [x] raw hex/rgba, whitespace error, secret-like 값 유입을 확인한다.
- [x] `.codex` session, handoff와 상위 방향 문서를 현재 구현 상태로 갱신한다.
- [x] 서버/Electron을 실행하지 않고, commit/push/migration/deploy를 하지 않는다.

## 완료 상태 — 2026-07-16

- desktop Nest director 4개 파일: 20/20 통과, TypeScript build 통과
- web API strategy/video-plan/operations 8 suite: 53/53 통과, build 통과
- web API 관련 production source ESLint error/warning 0
- Angular director feature: 11/11 통과, production build warning 없이 통과
- 기존 Angular shortform, Nest shortform/shortform-core, web API shortform-script는 `origin/dev` 대비 diff 0
- migration, 실제 provider 호출, server/Electron, commit/push/deploy는 실행하지 않음
