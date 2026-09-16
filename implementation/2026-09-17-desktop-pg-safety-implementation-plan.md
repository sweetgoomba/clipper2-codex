# Desktop PG 안전성 구현 계획

> 이 문서는 당시 구현 계획이다. 실행·재감사·추가 수정의 현재 결과는 [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)를 따른다. 아래 실행 전제/미완료 표현을 현재 상태로 자동 해석하지 않는다.

> 실행 전제: 8개 저장소 병합안에 대한 사용자의 명시적 승인을 받고, 별도 `integration/dev-pg-local-validation-20260917` worktree에서만 수행한다.

**목표:** 정식 PG integration을 최신 dev 위에 올린 뒤 모든 유료 렌더가 같은 견적·확인·차감·terminal 성공/환급·재시도 규칙을 사용하고, 앱/네트워크 장애에도 중복 차감이나 유실된 환급이 생기지 않게 한다.

**구조:** Web API는 stable attempt key를 금융 원장의 멱등 경계로 삼는다. Desktop Nest는 삭제 가능한 프로젝트/job과 분리한 로컬 billing-attempt 저장소 및 terminal outbox를 가지며, 구성 기반 coordinator/finalizer가 기능별 렌더 수명주기를 감싼다. Job 상태는 별도 phase 없이 enum 자체를 확장한다. Angular는 access/credit 원형 모델과 새 재시도 UX만 노출한다.

**기술:** Angular, Electron, NestJS, TypeScript, JSON local storage, PostgreSQL/TypeORM migration, Node test/Jasmine/Jest.

## Task 1: 병합 baseline을 테스트로 고정

**대상**

- 8개 통합 worktree 전체
- 병합 제안의 Angular 5파일, Nest `test/variation-v2-render-service.test.js`

**절차**

1. 승인된 merge commit 뒤 각 저장소 `git status --short`와 HEAD를 기록한다.
2. Angular/Nest semantic-overlap 결과가 제안 문서와 같은지 diff로 확인한다.
3. 기존 targeted test와 build를 먼저 실행해 “병합 자체의 실패”와 “후속 정책 변경 실패”를 분리한다.
4. baseline 실패가 있으면 후속 구현에 섞지 않고 원인·영향을 먼저 보고한다.

## Task 2: Web API operation start 멱등성

**수정 파일**

- `web/clipper_web_api/src/modules/operations/presentation/dto/start-operation.dto.ts`
- `web/clipper_web_api/src/modules/operations/presentation/operations.controller.ts`
- `web/clipper_web_api/src/modules/operations/application/operations.service.ts`
- `web/clipper_web_api/src/modules/operations/domain/operations.repository.ts`
- `web/clipper_web_api/src/modules/operations/infrastructure/operation-run.entity.ts`
- `web/clipper_web_api/src/modules/operations/infrastructure/typeorm-operations.repository.ts`
- `web/clipper_web_api/src/core/database/migrations/admin/1789200000000-AddOperationRunAttemptKey.ts`
- 대응 spec 파일

**테스트 먼저**

1. 같은 사용자·같은 stable attempt key를 두 번 start하면 같은 run을 반환하고 한 번만 차감되는 service/repository test를 추가한다.
2. 서로 다른 사용자 또는 명시적 사용자 재시도의 새 attempt key는 새 run·새 차감을 만든다는 test를 추가한다.
3. 첫 요청이 commit되고 응답만 유실된 replay를 모사한다.
4. migration SQL이 `(user_id, client_attempt_key)` unique 경계를 만들고 기존 null row를 허용하는지 검증한다.

**구현**

- `clientAttemptKey`를 start 계약에 추가한다.
- transaction 안에서 기존 run을 잠금/조회하고 있으면 기존 응답을 재구성한다.
- 없을 때만 run과 ledger charge를 만든다.
- 사용자 재시도는 Desktop이 새 key를 생성하므로 서버가 과거 실패 run을 재활용하지 않는다.

**검증**

- operations controller/service/repository/migration spec
- Web API build
- 중복 동시 요청 test

## Task 3: Desktop runtime contract validation과 옛 refund client 제거

**수정 파일**

- `desktop/clipper_nestjs/src/core/web-api/web-api-operation-run.service.ts`
- access/credit Web API client/service 파일
- `desktop/clipper_nestjs/test/web-api-operation-run.test.js`
- access/credit proxy 관련 test

**테스트 먼저**

- 정상 access/credit/page envelope가 명시적 Desktop model로 projection되는지.
- 필수 필드 누락, 잘못된 enum, 음수/소수 credit, 잘못된 page shape는 502 계열 upstream-contract 오류가 되는지.
- 모르는 추가 필드는 버리고 Desktop 응답에 새지 않는지.
- operation start가 stable `clientAttemptKey`를 Web API에 전달하는지.
- 사용되지 않는 독립 `refund()`가 public client surface에서 사라지는지.

**구현**

- TypeScript generic cast 대신 작은 runtime parser/projector를 경계에 둔다.
- 환급은 독립 사용자 refund endpoint가 아니라 `fail(runId, reason)` terminal 경로만 사용한다.

## Task 4: 로컬 billing attempt 저장소와 30일 정리

**신규/수정 파일 제안**

- `desktop/clipper_nestjs/src/modules/operations/domain/billable-job-attempt.ts`
- `desktop/clipper_nestjs/src/modules/operations/domain/billing-attempt.repository.ts`
- `desktop/clipper_nestjs/src/modules/operations/infrastructure/json-billing-attempt.repository.ts`
- `desktop/clipper_nestjs/src/modules/operations/application/billing-attempt-retention.service.ts`
- `desktop/clipper_nestjs/src/modules/operations/operations.module.ts`
- 대응 test

**저장 필드 최소안**

- local attempt ID, client attempt key, operation key, opaque job/feature reference
- Web API run ID, lifecycle state, terminal intent, timestamps
- user-deleted tombstone 여부, server terminal confirmation 시각
- bearer/access token, 프로젝트 입력, 미디어 경로·내용은 저장하지 않는다.

**테스트 먼저**

- atomic temp-write + rename 뒤 crash에도 이전 또는 새 JSON 중 하나만 읽히는지.
- 프로젝트/job 삭제 뒤에도 billing tombstone이 남는지.
- unresolved/pending/ambiguous는 나이와 무관하게 보존되는지.
- server-confirmed terminal metadata/tombstone만 확인 시각부터 30일이 지나면 정리되는지.
- 29일 23:59는 유지, 30일 경계 이후 정리되는지 clock fixture로 고정한다.

## Task 5: durable terminal outbox

**신규/수정 파일 제안**

- `desktop/clipper_nestjs/src/modules/operations/domain/billing-terminal-command.ts`
- `desktop/clipper_nestjs/src/modules/operations/infrastructure/json-billing-terminal-outbox.ts`
- `desktop/clipper_nestjs/src/modules/operations/application/billing-terminal-outbox.service.ts`
- `desktop/clipper_nestjs/src/core/web-api/web-api-operation-run.service.ts`
- 대응 test

**원칙**

1. `succeed/fail` 전송 전에 terminal intent를 로컬에 원자적으로 기록한다.
2. 성공 응답 뒤 server-confirmed로 표시한다.
3. timeout/앱 종료이면 pending을 남긴다.
4. 로그인 세션과 네트워크가 복구되면 같은 run ID와 같은 terminal intent로 재전송한다.
5. 반대 terminal intent로 바꾸지 않는다. 모호한 실행은 Admin recovery로 보낸다.

**테스트 먼저**

- write 직후 process crash, request 전/후 timeout, 성공 응답 유실, 두 번 replay.
- fail replay가 크레딧을 두 번 환급하지 않는 Web API contract.
- user project 삭제가 outbox fail을 새로 만들지 않는 경계.

## Task 6: 공통 attempt coordinator/finalizer

**신규 파일 제안**

- `desktop/clipper_nestjs/src/modules/operations/application/billable-job-attempt.coordinator.ts`
- `desktop/clipper_nestjs/src/modules/operations/application/billing-terminal-finalizer.ts`
- 대응 test

**수정 호출부**

- `src/modules/shortform/application/shortform-render-orchestrator.ts`
- `src/modules/jobs/application/jobs.service.ts` (Dance와 공통 retry)
- `src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts`
- `src/modules/variation-v2/application/variation-v2-render.service.ts`

**테스트 먼저**

- preflight 전 start 0회.
- 사용자 확인 취소 시 start 0회.
- 확인 뒤 start는 한 logical attempt에 1회.
- `preparing/queued/starting/running` 실패·취소 각각 fail/refund 1회.
- terminal success에서만 succeed 1회.
- fail/succeed API 오류는 outbox pending.
- 사용자 재시도는 현재 설정으로 새 quote/confirmation과 새 attempt key.

**구현 경계**

- coordinator는 금융 수명주기만 소유한다.
- 각 feature는 operation key, billing input, preflight, prepare/execute callback을 제공한다.
- URL/paste/prompt는 세 별도 class로 나누지 않고 기존 하나의 Shortform workflow와 작은 mode resolver를 유지한다.

## Task 7: Job status enum 직접 확장

**수정 파일**

- `desktop/clipper_nestjs/src/modules/jobs/domain/job.model.ts`
- `desktop/clipper_nestjs/src/modules/jobs/domain/job-repository.ts`
- `desktop/clipper_nestjs/src/modules/jobs/domain/job-queue.ts`
- `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts`
- `desktop/clipper_nestjs/src/modules/jobs/infrastructure/json-job-repository.ts`
- `desktop/clipper_nestjs/src/modules/jobs/infrastructure/in-memory-job-queue.ts`
- `desktop/clipper_nestjs/src/modules/video-render/video-render.service.ts`
- Angular job status 소비 파일과 관련 tests

**테스트 먼저**

- 허용 전이 table: `preparing -> queued -> starting -> running -> terminal`.
- 잘못된 역전이/건너뛰기를 거부한다.
- reserve는 `preparing`, payload 저장 뒤 activate만 `queued`, queue claim만 `starting`, executor 진입만 `running`.
- reorder는 `queued`만 가능하고 preparing은 queue 순번이 없다.
- 신규 JSON에 `render_prepare_pending`이 없다.
- 옛 terminal 이력은 보존하고 옛 active `waiting/starting/running`은 새 failed 기록을 만들지 않고 제거한다.

## Task 8: 네 prepare 경로와 재시도 연결

**수정 파일**

- `src/modules/shortform/application/shortform-render-orchestrator.ts`
- `src/modules/variation-v2/application/variation-v2-render.service.ts`
- `src/modules/comment-overlay-render/application/comment-overlay-render.service.ts`
- `src/modules/ranking-render/application/ranking-render.service.ts`
- `src/modules/jobs/domain/render-job-preparer.ts`
- `src/modules/jobs/application/render-job-preparer.registry.ts`
- `src/modules/jobs/application/jobs.service.ts`
- 대응 tests

**기대 동작**

- 네 기능 모두 prepare callback이 `preparing -> queued`를 완료한다.
- 준비 실패 재시도는 payload 없는 old job을 직접 queue에 넣지 않고 새 attempt로 preparation을 다시 수행한다.
- Shortform/Variation 유료 재시도는 새 견적/확인/차감, 댓글 오버레이/영상 랭킹은 같은 상태 기계의 무료 재시도다.

## Task 9: Shortform authoritative preflight와 fallback 제거

**수정/신규 파일**

- `desktop/clipper_nestjs/src/modules/shortform/application/shortform-render-preflight.service.ts`
- `src/modules/shortform/presentation/shortform-project.controller.ts`
- `src/modules/shortform/application/shortform-render-orchestrator.ts`
- `src/modules/projects/infrastructure/clipper-studio-asset-preparer.ts`
- `src/modules/shortform/application/shortform-manifest.builder.ts`
- Angular Shortform workflow page/service/store와 tests
- `test/clipper-studio-asset-preparer.test.js`
- 신규 `test/shortform-render-preflight.test.js`

**테스트 먼저**

- TTS ID 누락, 파일 누락, 손상, 대사 수정 뒤 재합성 실패, 빈/새 줄.
- media/slot 누락, 로컬 파일 누락, remote materialization 불가.
- preflight 실패 시 quote/start/reserve/navigation 모두 0회.
- UI preflight 뒤 파일이 사라져도 authoritative start preflight가 차감 전에 막는지.
- 정상 manifest에 fallback/sample/silent TTS와 seed media placeholder가 0개인지.
- 정상 BGM MP3와 `legacy-bgm.*` identity는 변하지 않는지.

## Task 10: Angular 옛 license adapter 제거

**수정 파일**

- `desktop/clipper_angular/src/shell/settings/settings/settings-account.service.ts`
- `src/shell/account/account-summary.store.ts`
- `src/shell/settings/settings/settings.component.ts`
- `src/shell/settings/settings/settings.component.html`
- `src/shell/projects/home-side-panel/home-side-panel.component.ts`
- 관련 spec 전체

**테스트 먼저**

- access와 credit 응답을 독립 조회해 UI view model을 만든다.
- 구독 만료 + 유효한 추가구매 credit에서 작업 가능/잔액 표시.
- active access 없음 + credit 0, active access + credit 0, access/credit API 오류.
- 코드 검색에서 `CurrentLicenseSummary`, `currentLicense`, `_license`, queued/expired license adapter가 0건.

## Task 11: 앱 재시작 reconciliation과 process 종료

**수정 후보**

- `desktop/clipper_electron/src/main/backend/nest-process.ts`
- `desktop/clipper_electron/src/main/backend/nest-manager.ts`
- Electron process lifecycle tests
- `desktop/clipper_nestjs/src/main.ts`
- ffmpeg/provider/executor child registry 관련 파일
- Python subprocess ownership 관련 파일과 tests

**검증 먼저**

- fake child/짧은 ffmpeg로 normal shutdown, TERM timeout, KILL fallback, parent crash.
- macOS/Windows에서 descendant PID가 종료 후 남지 않는지.
- 신규 active job은 앱 시작 시 자동 재개하지 않는다.
- 결과가 명확히 실패면 fail/refund; 성공 evidence가 있으면 succeed; 모호하면 outbox를 반대 terminal로 쓰지 않고 Admin recovery 대기.
- job/billing metadata에 로그인 token이 기록되지 않는다.

## Task 12: 앱 이름 패키징 검증

**대상**

- Electron 앱 이름 feature의 10파일

**검증**

- dev: `Clipper Studio (dev).app`, `Clipper Studio (dev)-<version>-<arch>.dmg`, `Clipper Studio (dev) Setup <version>.exe`.
- prod: `Clipper Studio.app`, `Clipper Studio-<version>-<arch>.dmg`, `Clipper Studio Setup <version>.exe`.
- dev/prod appId, protocol, data path, cache/port/update 값은 병합 전 identity와 동일.
- macOS 기존 암호문 복호화 실패는 로그아웃 상태, 재로그인 뒤 재실행 유지.

## 완료 게이트

- targeted unit/contract/build 전부 통과.
- 실제 ML 플러그인과 Build 5 전체 QA는 계속 HOLD로 명시.
- 로컬 DB migration/앱 통합 검증 전에는 “배포 가능”으로 판정하지 않는다.
- push·dev server 전환은 별도 승인 전 0건.
