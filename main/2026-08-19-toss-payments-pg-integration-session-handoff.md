# 토스페이먼츠 PG 전체 연동 세션 인계

> 2026-08-21 후속 정본:
> `2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md`
> Task 25 이후의 명시적 상향 견적·동의 보강, 실제 수동 테스트 결과, 2026-08-21 ngrok
> delivery/400 parser 원인과 공식 envelope 정정, webhook·배포 잔여 상태는 후속 문서를
> 우선한다.

- 기록일: 2026-08-21 (Asia/Seoul)
- 설계: 사용자 승인 완료
- 실행 계획: `/Users/jina/project/adlight/.codex/main/2026-08-18-toss-payments-pg-integration-implementation-plan.md`
- 현재 단계: Task 25 전체 검증, mock-catalog fix round 1, 최종 독립 재리뷰 READY까지 완료
- 다음 작업: 승인된 Task 1~25 범위에는 남은 구현이 없음. 실제 테스트 MID/키와 webhook 관찰 환경이 제공될 때만 체크리스트를 별도 실행하며, merge·push·배포는 새 지시가 필요함

## 1. 다음 세션에서 먼저 읽을 문서

아래 순서로 전부 읽고, 추가 브레인스토밍 없이 승인된 계획을 이어서 실행한다.

1. `/Users/jina/project/adlight/.codex/main/2026-08-18-toss-payments-pg-integration-design.md`
2. `/Users/jina/project/adlight/.codex/main/2026-08-18-toss-payments-pg-integration-implementation-plan.md`
3. 이 인계 문서
4. API worktree의 `.superpowers/sdd/2026-08-18-toss-payments-pg-integration-implementation-plan/progress.md`
5. 같은 디렉터리의 `task-25-brief.md`, `task-25-report.md`, `task-25-review.md`, `task-25-fix-1-review.md`

Task 25의 최종 권위는 이 문서, `progress.md`, `task-25-report.md`, SHA-256 `0533f101ebdae37de4f8c5b662a8af9624b26feeac6cfdb21221c148650993f4`의 `task-25-fix-1-review.md`다. 최초 리뷰의 stale mock-catalog Important는 두 개의 분리 커밋으로 해결됐고, 최종 재리뷰는 원 finding Addressed, 새 Critical 0 / Important 0 / Minor 0, READY다. 개발서버 환경변수에는 이미 테스트 키가 설정돼 있고 카드사 심사용 흐름의 테스트 결제 성공 이력도 있다. 다만 Task 25의 별도 11-scenario 전체 연동 검증은 실행하지 않았고 그 실행용 MID 연결/webhook 관찰 준비를 재확인하지 않아 해당 행들은 미실행·unchecked 상태로 남는다.

## 2. 절대 조건

- 기존 `feat/access-credit-system-replacement` branch와 worktree를 수정하지 않는다.
- 어떤 저장소의 `dev` branch도 수정하지 않는다.
- `dev.clipperstudio.ai`의 익명 PG review 기능을 수정하거나 재배포하지 않는다.
- feature branch를 push하지 않는다. 초기 access-credit HEAD 보존 push만 이미 완료됐다.
- dev merge, 배포, compose 실행, 운영 환경변수 변경을 하지 않는다.
- 돈 환불 API·서비스·UI·토스 취소 호출을 추가하지 않는다.
- 작업 실패 시 서비스 내부 크레딧 반환·복구는 유지한다.
- API와 고객 웹은 Node 22에서 실행한다.
- 구현은 테스트 우선, 구현자와 독립 리뷰어 분리, 최대 5회 fix round 원칙을 유지한다.
- 과거 migration을 수정하지 않고 필요한 변경은 새 forward migration으로 추가한다. 단, 아직 feature에만 존재하고 계획이 명시한 기존 Task 3 migration 보완은 이미 종료됐다.

## 3. 현재 저장소 상태

2026-08-21 Task 25 최종 closeout에서 일곱 feature worktree를 다시 확인했다. 모두 clean index/worktree이고 `feature/toss-payments-pg-integration`에 있으며 upstream과 동일 이름 remote feature ref가 없다.

| 저장소 | branch | HEAD | 상태 |
| --- | --- | --- | --- |
| `clipper_web_api` | `feature/toss-payments-pg-integration` | `2dce869d1f1f911d5cec1ce822529b3b663f9a4e` | Task 25 전체 검증 후 test-key 기록 사실 정정 완료 |
| `clipper_web_client` | `feature/toss-payments-pg-integration` | `95218a891177ba38ad109bf29bbd510966106265` | Task 25 mock policy fix 및 최종 재리뷰 READY |
| `clipper_web_admin` | `feature/toss-payments-pg-integration` | `2ccb825d6a56c690a72a89244798caa1a8968b72` | Task 25 mock policy fix 및 최종 재리뷰 READY |
| `clipper_infra` | `feature/toss-payments-pg-integration` | `e6ae78f58b559cf3715f6acaecf6ac067a4e7930` | Task 23 및 fix round 2 독립 재리뷰 승인 완료 |
| `clipper_angular` | `feature/toss-payments-pg-integration` | `f0da4e4a4aca26bbf08ccbc16856b085c06b0404` | Task 24 one-spec contract regression 및 독립 리뷰 승인 완료 |
| `clipper_electron` | `feature/toss-payments-pg-integration` | `abdc5753741301f4bf22278a22ca8e20dc78ac24` | verify-only baseline |
| `clipper_nestjs` | `feature/toss-payments-pg-integration` | `8e131e3f601f981259c7bf00bb1a3001631c0fe5` | verify-only baseline |

보호 대상 access-credit worktree도 모두 clean이며 HEAD는 다음과 같다.

| 저장소 | 보호 HEAD |
| --- | --- |
| API | `10cf10fc1a9832cb736d85ad9d3266295a123f53` |
| 고객 웹 | `25091ec5b317a3b72a670ad86d289e3932f9ddb3` |
| 관리자 웹 | `e17c5b434b3e4240846eba1009ef026303b17d15` |
| infra | `dac0ed27a4ea035daf7ff5622a5763118b5abe53` |
| Angular | `7938350ceb033d547c76992fda56dfcbec0af993` |
| Electron | `7f5d4d31c5fbea76b6edbfba7bee96a870325e92` |
| NestJS | `2abc490efcb1f96933ab87cc9ae3c4cb3214490a` |

다음 세션 시작 시 API worktree에서 먼저 아래를 확인한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
git status --short
git branch --show-current
git rev-parse HEAD
```

예상값은 clean, `feature/toss-payments-pg-integration`, `2dce869d1f1f911d5cec1ce822529b3b663f9a4e`다. 최신 dev를 다시 merge하지 않는다.

## 4. 완료된 범위

독립 리뷰까지 종료된 범위는 Task 1~25와 Task 7A다.

- Task 1: 일곱 저장소의 보호 HEAD 보존, 격리 feature worktree, API/client/infra 최신 dev merge baseline
- Task 2: 최종 로그인 사용자용 PG OpenAPI 계약
- Task 3: 결제·구독·빌링 인증·웹훅 inbox forward migration과 실제 PostgreSQL 검증
- Task 4: Basic/Pro 월간·연간 및 topup 상품 seed, immutable 월 기념일 계산
- Task 5: 인증 사용자 결제 주문 persistence와 CAS 상태 전이
- Task 6: 구독 계약 snapshot, billing auth attempt persistence
- Task 7: durable webhook inbox, dedupe, retry claim, fencing, secret 보존·삭제
- Task 7A: 공식 Billing card snapshot과 DB/domain/OpenAPI 정렬
- Task 8: Toss Payments PG V2 HTTP provider adapter
- Task 9: owner-bound checkout session, success/fail redirect, 안전한 결과 projection
- Task 10: billing authorization issue/replay/recovery, rejected-key cleanup accounting, exact-deadline uncertainty
- Task 11: 월간·연간 최초 구독 카드 결제, 동일 주문 crash recovery, 최초 결제 전용 terminal CAS
- Task 12: 추가 크레딧 단건결제, 가상계좌 대기·만료·입금 완료, 같은 주문 재조정과 외부 취소 관찰
- Task 13: 세 종류의 Toss 웹훅 수신·durable 처리, 결제 재조회·가상계좌 secret 검증, billing-key 삭제 상관 처리
- Task 14: 결제 완료 상품 1회 지급, lease-token 기반 경합 복구, 고정 anchor 혜택, 내부 크레딧 복구 유지
- Task 15: 고정 결제일 월·연 갱신, D+1/D+2 복구, cancel/resume/retry, 예약 계약의 원자적 적용과 immutable access 혜택 snapshot
- Task 16: PG 빌링 인증 기반 카드 재등록, owner-bound 변경 흐름, atomic swap, 현재 키 보존 cleanup, billing redirect coordinator와 crash recovery
- Task 17: Basic→Pro 같은 결제 주기의 즉시 업그레이드, 정확한 가격·월 혜택 차액, 예약 변경·취소, 목적 제한 결제 복구, 구독·이용권·크레딧 원자 적용
- Task 18: 본인 결제내역의 안전한 opaque pagination, 관리자 결제·웹훅·재조정 경고 조회, 외부 취소 우선 재조회, 운영자 감사와 안전한 fulfillment 재처리
- Task 19: 최종 Nest module/DI, singleton handler alias, 최종 entity/repository/provider/controller/scheduler 배선과 review/direct legacy runtime 제거
- Task 20: 최종 customer checkout session/API/SDK, guarded portal checkout route, public checkout 제거, mock boundary 정렬
- Task 21: 실제 pricing/topup/result/history/subscription/card-change 여정, 안전한 mock pagination, 카드변경 결과 redirect, 남은 review compatibility 제거
- Task 22: 관리자 결제 주문·웹훅·재조정 경고 console, 안전한 reconcile/fulfillment retry, cursor 경합 fence, 환불 동작 없음
- Task 23: 실제 Compose dotenv 의미를 따르는 fail-closed 일곱 PG 환경변수 검증, API-only Compose wiring, runbook과 배포 전 정적 preflight
- Task 24: desktop Angular/Electron/local API access-credit 계약 전체 검증, `/app/credits` Angular bridge regression 보완, runtime 변경 없음
- Task 25: PostgreSQL 16 전체 migration, 일곱 저장소 전체 test/build 및 보안·범위 검증, 수동 test-key 체크리스트, PG production lint closure, customer/admin mock catalog 정렬, 최종 통합 재리뷰 READY

Task 10 최초 구현 커밋은 `8b1dae7 feat(payments): recover billing authorization issues`, fix round 1 커밋은 `46c34ab fix(payments): preserve billing authorization recovery`다. 최종 검증은 Node 22 focused 5 suites/127 tests, production ESLint, diff/scope/secret scan, PostgreSQL 15.13 전체 39 migrations와 live CAS/expiry/deadline-race probe를 통과했다. Full build의 112개 오류는 후속 task caller/module에 한정되고 Task 10 소유 파일 진단은 0개다.

Task 11 최초 구현 커밋은 `6fd840c feat(subscriptions): charge initial PG billing payment`, fix round 1 커밋은 `1e055f8 fix(subscriptions): recover initial payment retries`다. 최종 검증은 Node 22 exact 7 suites/130 tests, production ESLint, diff/scope/secret scan, PostgreSQL 15.13 전체 40 migrations와 initial paid/reconciliation/reclaim/unresolved one-winner 경합 probe를 통과했다. Full build의 98개 오류는 후속 task 파일 9개에 한정되고 Task 11 소유 production 파일 primary diagnostic은 0개다.

Task 12 최초 구현 커밋은 `fc60fd0 feat(payments): confirm topups and virtual accounts`, fix round 1 커밋은 `b91d844 fix(payments): reconcile completed topups safely`다. 최종 검증은 Node 22 exact 3 suites/43 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 40 migrations와 first-observed VA DONE `secret:null`, one-winner fulfillment, paid 이후 `PARTIAL_CANCELED` 관찰 probe를 통과했다. Full build의 89개 오류는 후속 task 파일 8개에 한정되고 Task 12 소유 production 파일 primary diagnostic은 0개다.

Task 13 최초 구현 커밋은 `be0ca6d feat(payments): verify Toss payment webhooks`, fix round 1 커밋은 `3a43ae8 fix(payments): reclassify deleted billing keys`다. 최종 검증은 Node 22 exact 6 suites/109 tests, Task 7 inbox 74 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 40 migrations와 retained-candidate/previous cleanup 및 install-between-lookups 경합 probe를 통과했다. Full build의 89개 오류는 동일한 후속 task 파일 8개에 한정되고 Task 13 소유 production 파일 primary diagnostic은 0개다.

Task 14 최초 구현 커밋은 `8df76fa feat(payments): fulfill paid products idempotently`, fix round 1 커밋은 `eab0e48 fix(payments): harden fulfillment lease recovery`다. 최종 검증은 Node 22 exact 7 suites/123 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 40 migrations와 claim matrix, lease-token CAS, one-grant 경합, lost-finalize transaction rollback 및 retry probe를 통과했다. Full build의 85개 오류는 후속 task 파일에 한정되고 Task 14 소유 production 파일 primary diagnostic은 0개다.

Task 15 최초 구현 커밋은 `7480d47 feat(subscriptions): renew and cancel on fixed anchors`, fix round 1 커밋은 `042eeaa fix(subscriptions): serialize renewal recovery`, fix round 2 커밋은 `109c9fc fix(access): preserve historical benefit snapshots`다. 최종 검증은 Node 22 exact 15 suites/266 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 42 migrations와 cleanup/resume 직렬화, renewal paid/failure one-winner CAS, 예약 계약·access snapshot 원자 적용, catalog drift 및 forward correction probe를 통과했다. Full build의 80개 오류는 후속 legacy/module 파일에 한정되고 Task 15/fix-2 파일 진단은 0개다.

Task 16 최초 구현 커밋은 `5c098b4 feat(subscriptions): change cards through PG billing auth`, fix round 1 커밋은 `caefb7e fix(subscriptions): fence card change recovery`다. 최종 검증은 Node 22 exact 8 suites/161 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 42 migrations와 live-current cleanup advisory-lock 경합, zero provider delete, durable retry-selector settlement probe를 통과했다. Full build의 46개 오류는 Task 19 legacy/module 파일에 한정되고 Task 16/fix 파일 진단은 0개다.

Task 17 최초 구현 커밋은 `9324327 feat(subscriptions): upgrade now and schedule plan changes`, fix round 1 커밋은 `3ee2206 fix(subscriptions): fence upgrade completion races`다. 최종 검증은 Node 22 exact 8 suites/193 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 42 migrations와 exact-period advisory-lock 경합, expiry/cancel unresolved fence, purpose terminal CAS, failed-order non-reopen, atomic one-grant/ledger/event fulfillment 및 rollback/retry probe를 통과했다. Full build의 46개 오류는 Task 19 legacy/module 파일에 한정되고 Task 17/fix 파일 진단은 0개다.

Task 18 최초 구현 커밋은 `b340dd3 feat(payments): expose safe history and operations`, fix round 1 커밋은 `2f683ca fix(payments): fence admin reconciliation`다. 최종 검증은 Node 22 exact 9 suites/185 tests, production ESLint, Prettier, diff/scope/safety scan, PostgreSQL 15.13 전체 42 migrations와 owner isolation, same-timestamp opaque cursor, 100개 경계, 관리자 warning predicate, paid/failed/external-cancel provider 재조회 우선, zero fulfillment, 운영자 감사 이벤트 probe를 통과했다. Full build의 46개 오류는 Task 19 legacy/module 파일에 한정되고 Task 18/fix 파일 진단은 0개다.

Task 19 구현 커밋은 `d6a24d1 refactor(payments): remove review and direct Toss flows`다. 최종 검증은 Node 22 module/datasource 10 tests, 결제·access·catalog·credits·operations 59 suites/857 tests, full API build 0 diagnostics, lint/format/diff/scope/security scan, PostgreSQL 15.13 전체 42 migrations와 compiled final DataSource metadata 초기화를 통과했다. 독립 리뷰는 Critical 0, Important 0, Minor 1로 승인했으며 Minor는 테스트 집합을 더 엄격히 닫는 비차단 보강점이다.

Task 20 구현 커밋은 `a80a7ea feat(web): add authenticated Toss checkout`이다. 최종 검증은 Node 22 focused 37 tests, customer full 149 tests, build 0 diagnostics, exact 20-path/package-noop/format/diff/security scan을 통과했다. 공개 checkout은 제거되고 `/app/payment/checkout?receipt=...`만 남았으며 모든 결제 권위 필드는 owner-bound API session에서만 온다. 독립 리뷰는 Critical 0, Important 0, Minor 2로 승인했다. 공식 SDK 2.7.1 payment widget에 VA due-date 요청 필드가 없어 모델에는 보존하되 unsupported cast는 하지 않았고 Task 25 수동 확인 항목으로 넘겼다.

Task 21 API 커밋은 `bf27a51 fix(payments): route card change results safely`, 고객 웹 구현 커밋은 `50d2842 feat(web): complete subscription and topup journeys`, fix round 1 커밋은 `e969fa7 fix(web): complete login and history pagination`이다. 최종 검증은 API Node 22 redirect 32 tests와 build, 고객 웹 exact 10 suites/75 tests, full 161 tests, app TypeScript와 production build, exact scope 및 review/refund/provider-cancel/secret/bundle scan을 통과했다. 최초 리뷰의 Important 2건은 실제 Google login initiator와 정규화된 pricing return path, 진전하는 opaque mock history pagination으로 수정됐고 scoped 재리뷰는 Critical/Important/Minor 0으로 승인했다.

Task 22 구현 커밋은 `9e455e4 feat(admin): add PG payment operations console`, fix round 1 커밋은 `3fac6e6 fix(admin): fence payment operations pagination`이다. 최종 검증은 Node 22 component 16 tests, exact five specs 44 tests, full admin 224 tests, app TypeScript와 production build, exact scope 및 refund/provider-cancel/secret/review/direct/bundle scan을 통과했다. 세 feed의 opaque cursor는 independent pending/generation으로 중복 요청·stale append·반복 cursor를 차단한다. 독립 재리뷰는 Critical/Important/Minor 0으로 승인했으며 기존 initial bundle budget warning과 webhook track-key Minor는 비차단 항목이다.

Task 23 구현 커밋은 `801c058 chore(infra): configure full Toss Payments PG`, fix round 1은 `cd5fad8 fix(infra): validate Toss environment safely`, fix round 2는 `e6ae78f fix(infra): enforce canonical Toss origins`다. 최종 검증은 Node 22 validator 71/71, shell syntax/mode, static Compose config와 rendered JSON의 API exact seven/customer-admin absence, exact scope와 removed-var/value-leak scan을 통과했다. Validator는 실제 Compose dotenv decoding/last-wins 값을 Node JSON/WHATWG URL로 검사하고, canonical HTTP loopback만 허용하며 임의 trimmed nonempty UTF-8 HMAC을 보존한다. 최종 재리뷰는 Critical/Important/Minor 0으로 승인됐다. 배포, operational Compose, 컨테이너, 실제 Toss/network 작업은 수행하지 않았다.

Task 24 characterization 커밋은 `f0da4e4 test(desktop): lock credit navigation contract`다. 최종 검증은 Angular Node 22.22.3 Karma 2,156 tests와 styles 6 tests/build, Electron 219 tests/build, desktop local API 803 tests/build를 통과했다. Angular production diff는 0이며 신규 spec은 실제 ledger 버튼이 exact `/app/credits` bridge를 호출함을 고정한다. 임시 wrong-path mutation에서 신규 test만 실패한 뒤 원복했고, canonical ignored Nest fixture는 값 비노출로 사용 후 제거됐다. 독립 리뷰는 Critical/Important/Minor 0으로 승인됐다.

Task 25 API 커밋은 `b8be871 style(payments): lint PG production files`, `23a3409 docs(payments): add PG test-key verification checklist`, 그리고 사실 정정 `2dce869 docs(payments): correct test-key verification record`다. clean PostgreSQL 16에서 admin/user/release `42/4/2` migration과 exact catalog seed를 검증했고, API `153` suites/`1,313` tests/build, customer `162` tests/TypeScript/build, admin `224` tests/TypeScript/build, infra `71` tests/static Compose, Angular `2,156+6` tests/build, Electron `219` tests/build, desktop local API `803` tests/build가 통과했다. 전체 API no-write lint는 안정적으로 `3,891` findings인 승인된 baseline debt라 **FAILED**로 기록하며, PG-range changed production `71` paths lint는 0이다. 개발서버의 테스트 키 설정과 카드사 심사용 테스트 결제 성공 이력은 이미 존재한다. 체크리스트 11개 행은 Task 25에서 별도 실행하지 않았고 해당 실행용 MID 연결/webhook 관찰 준비를 재확인하지 않아 미실행·unchecked이며, Toss cancel/refund API는 호출하지 않았다. 최초 통합 리뷰의 stale mock finding은 customer `95218a8 fix(web): align mock catalog policy`, admin `2ccb825 fix(admin): align mock catalog policy`로 해결됐고 최종 re-review는 READY, 새 Critical/Important/Minor 0이다.

## 5. Task 10 독립 리뷰와 fix round 1 완료

### Critical

실제 `HttpTossPaymentsProvider.issueBillingKey`가 응답의 `billingKey`를 서비스에 넘기기 전에 customer/method/card semantic parsing을 수행한다. issuer/mask/card type 등이 잘못된 성공 응답이면 adapter가 uncertainty 예외를 던져, 이미 발급된 billing key를 서비스가 암호화·지문화·cleanup 후보로 영속화하지 못한다.

필수 수정:

- `TossBillingAuthorization`의 non-key semantic fields를 untrusted 값으로 서비스 경계까지 전달할 수 있게 계약을 조정한다.
- adapter는 유효한 non-empty `billingKey`를 먼저 추출하고, 그 뒤 semantic mismatch 때문에 그 키를 버리거나 uncertainty로 숨기지 않는다.
- `BillingAuthService`가 키를 즉시 암호화·지문화한 뒤 valid candidate 또는 rejected cleanup candidate로 원자적으로 저장한다.
- 실제 `HttpTossPaymentsProvider`와 `BillingAuthService`를 연결한 regression test로 malformed customer/method/card가 있어도 returned key가 영속화되는지 검증한다.
- 수정 범위에 `domain/toss-payments.provider.ts`, `infrastructure/http-toss-payments.provider.ts`, `infrastructure/http-toss-payments.provider.spec.ts`를 추가한다.

### Important

provider 호출 중 exact 15-day scheduler가 attempt를 `reconciliation_required`로 바꾼 뒤 provider가 deterministic error를 반환할 수 있다. 현재 서비스는 `markFailed` lost-CAS가 반환한 reconciliation row를 정상 결과처럼 반환한다.

필수 수정:

- `markFailed` 결과가 `reconciliation_required`이면 반드시 `TossPaymentsUncertainResultError`를 던진다.
- 이 경합을 서비스 테스트로 먼저 RED로 만든다.

### Minor

서비스 spec의 fingerprint-conflict test double은 실제 repository와 달리 cleanup 상태를 `pending`으로 바꾼다. 실제 SQL처럼 기존 cleanup 상태를 보존하도록 고친다.

### Fix round 1 결과

1. 실제 HTTP adapter와 service를 연결한 regression, exact-deadline lost-CAS, test-double parity 테스트에서 production 수정 전 genuine RED 3 failures/124 passes를 재현했다.
2. adapter는 non-empty `billingKey`를 먼저 추출하고 나머지 성공 payload를 untrusted 값으로 전달한다. 서비스는 키를 암호화·지문화해 먼저 account한 뒤 semantic validation과 rejected-candidate cleanup을 수행한다.
3. scheduler가 provider in-flight 중 reconciliation을 선점한 뒤 deterministic error가 와도 서비스는 정상 row를 반환하지 않고 uncertainty를 던진다.
4. fingerprint-conflict test double은 실제 repository와 같이 기존 cleanup 상태를 보존한다.
5. 별도 커밋 `46c34ab0a640ce3bf2a6b6a2576ae9ec24ac8f29`을 생성했으며 기존 구현 커밋은 amend하지 않았다.
6. 독립 scoped 재리뷰는 세 finding을 모두 Addressed로 확인했고 새로운 Critical/Important는 0개다.

## 6. Task 11 완료 상태

Task 11은 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- checkout은 user lock 안에서 manager-bound catalog/access를 재조회하고 subscription/order/attempt/readiness를 한 transaction에 저장한 뒤 안전한 browser session을 반환한다.
- 자동결제 성공은 정확한 `BILLING`/카드/`DONE`/KRW와 주문·금액·카드 경계값을 검증한다.
- provider uncertainty와 crash는 동일 order/orderNo/charge key로 복구하며 15일 경계부터 lookup만 허용한다.
- 확정 decline 뒤 사용자 명시 retry만 새 logical initial order를 만든다. 이 replacement order도 crash 후 같은 주문으로 복구하며 추가 주문을 만들지 않는다.
- 초기 결제 paid/reconciliation/reclaim/fail/expiry 전이는 purpose와 상태가 제한된 one-winner CAS를 사용한다.
- 결제 성공은 paid order와 attempt 완료를 먼저 저장한 뒤 기존 Task 14 `fulfill(orderId)` 경계를 호출한다.
- 돈 환불이나 토스 결제 취소 호출은 추가하지 않았다.

Task 11 검증 중 변경되지 않은 Task 14의 `tryBeginFulfillment`가 실제 PostgreSQL 15에서 nullable `staleBefore` 파라미터 타입을 추론하지 못해 SQLSTATE `42P08`을 내는 문제가 확인됐다. Task 14 시작 시 production 수정 전 RED로 재현하고 고쳐야 한다.

## 6.1 Task 12 완료 상태

Task 12는 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- checkout은 active access를 transaction/user lock 안에서 확인하고 세 topup 상품의 서버 snapshot으로 owner-bound session을 만든다. 결제 완료와 재조정에서는 access를 다시 확인하지 않아 구매 뒤 access가 만료돼도 유효한 결제가 끝까지 수렴한다.
- 정상결제 callback은 receipt capability, 저장된 order number, payment key, amount, `NORMAL`, KRW를 상관 확인하고, 불확실성은 동일 주문·동일 key set 조회만 사용한다.
- 카드·지원 간편결제·계좌이체·가상계좌 `DONE`은 paid CAS 승자만 기존 Task 14 fulfillment 경계를 호출한다. 예상 밖 성공 수단은 안전한 경고를 기록하되 결제 완료 금액은 한 번 지급한다.
- 가상계좌 `WAITING_FOR_DEPOSIT`은 account/secret을 엄격히 요구하고, 계좌번호는 canonical mask만 저장하며 secret은 즉시 암호화한다. 만료 뒤 provider `DONE`도 paid로 수렴한다.
- 실제 GET adapter처럼 최초 관찰 `DONE`의 가상계좌 secret이 null이어도 safe account snapshot을 저장하고 paid/1회 지급으로 수렴하며, 존재하지 않는 secret을 만들거나 저장하지 않는다.
- paid 주문도 같은 결제를 조회해 외부 `CANCELED|PARTIAL_CANCELED` 메타데이터를 관찰하지만 paid 상태·이미 지급된 권한/크레딧을 자동으로 되돌리거나 토스 취소를 호출하지 않는다.

기존 `PaymentOrdersRepository.recordEvent(...orIgnore)`가 실제 PostgreSQL에서 중복 row를 하나만 보존하면서 Boolean은 두 번 모두 true로 보고하는 문제가 남아 있다. Task 12는 이 반환값을 소비하지 않고 paid CAS로 side effect를 막으므로 현재 동작은 안전하다. 최종 whole-branch review에서 strict insert-winner 의미가 필요한 후속 consumer가 있는지 다시 확인한다.

## 6.2 Task 13 완료 상태

Task 13은 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- 웹훅 요청 경로는 envelope를 검증하고 secret을 즉시 암호화 또는 HMAC 지문화해 durable inbox에 저장한 뒤 응답하며, 요청 중 provider 호출이나 결제 상태 변경을 하지 않는다.
- worker는 Task 7 lease fence 안에서 provider의 결제 상태를 다시 조회하고 저장된 주문·payment key·금액·통화·결제 유형을 상관 확인한 뒤 Task 12 reconciliation에 위임한다.
- 가상계좌 입금 callback은 저장된 암호문을 명시적 검증 경로에서만 읽고 timing-safe 비교 후 처리하며 terminal 상태에서 inbox secret을 지운다.
- billing-key 삭제는 current/candidate/previous/history를 fingerprint로 구분하고, 이미 완료된 candidate나 install-between-lookups 경합에서도 현재 키 삭제와 이전 키 cleanup을 재분류한다.
- 돈 환불, 결제 취소, provider payment-cancel 호출은 추가하지 않았다.

Task 14는 기존 `PaymentOrdersRepository.tryBeginFulfillment`의 실제 PostgreSQL SQLSTATE `42P08`을 tests-only RED와 PostgreSQL 15 probe로 먼저 재현한 뒤, paid 상품 1회 지급과 함께 수정해야 한다. Task 12에서 관찰된 `recordEvent` Boolean quirk는 Task 13에서도 반환값을 분기 조건으로 소비하지 않아 side effect 안전성에는 영향을 주지 않았다.

## 6.3 Task 14 완료 상태

Task 14는 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- fulfillment claim은 실제 저장된 시각을 lease token으로 반환하고 성공·실패 finalizer가 같은 token을 CAS해 이전 worker가 새 worker 상태를 덮어쓰지 못한다.
- 상품 지급과 성공 finalizer가 같은 manager transaction 안에서 수행돼 finalizer를 잃으면 지급도 rollback되고, retry 시 한 번만 수렴한다.
- 최초 구독과 갱신 replay는 이미 적용된 정확한 상태를 인식하며, 월 경계는 mutable period가 아니라 immutable `billingAnchorAt`에서 계산한다.
- cleanup scheduler는 최종 BillingAuthAttempt를 다시 읽고 ciphertext와 fingerprint를 함께 검증한 키만 삭제 요청하며 성공·실패를 같은 attempt repository에 기록한다.
- operation-layer `charge_then_refund`와 credit `refund`는 돈 환불이 아니라 기존 내부 크레딧 복구 의미로 유지됐다. 돈 환불이나 provider payment cancellation은 추가하지 않았다.

## 6.4 Task 15 완료 상태

Task 15는 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, 두 차례 fix round와 scoped 재리뷰까지 완료했다.

- 최초·갱신 재시도는 하나의 안전한 응답 형태로 수렴하고, 최초 주문이 정확히 없을 때만 갱신 경로로 분기한다.
- 갱신 결제는 고정 anchor, D+1/D+2/manual index, provider 상관 검증, `UNKNOWN` uncertainty, renewal 전용 paid/failure CAS를 지킨다.
- 취소 복구와 기간 종료 키 정리는 같은 DB lock과 database time 경계로 직렬화되어 복구된 현재 키를 삭제하지 않는다.
- 결제된 예약 계약은 구독과 access grant에 원자적으로 승격되고, 월별 혜택은 결제 당시 snapshot을 사용해 이후 catalog 변경에 흔들리지 않는다.
- 기존 subscription access grant의 잘못된 catalog 기반 backfill은 새 forward `178780` migration으로만 보정하며, admin grant는 그대로 유지한다.
- 돈 환불이나 provider payment cancellation은 추가하지 않았다.

## 6.5 Task 16 완료 상태

Task 16은 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- 카드 변경은 최종 `billing_auth_attempts`와 DB safe-card snapshot만 사용하며, 존재하지 않는 billing-key status 조회나 legacy change repository를 호출하지 않는다.
- active는 자동 청구 없이 교체하고, pending은 결정적 최초 결제 실패와 unresolved 부재를 확인한 전용 CAS만 허용하며, past_due는 서버 계약 snapshot과 명시적 동의를 요구한 뒤 원래 renewal order/key로 재시도한다.
- 발급 후보는 HMAC fingerprint를 검증한 뒤 subscription lock 안에서 atomic swap하고, 이전 키 cleanup은 commit 뒤 같은 final-attempt 상태로 복구 가능하다.
- 동일 카드 재등록으로 후보와 현재 fingerprint가 같아도 현재 키를 이전/후보 cleanup 대상으로 삭제하지 않는다. 즉시 처리와 PaymentRecoveryScheduler 모두 transaction/advisory lock에서 live subscription을 다시 읽고 동일 fingerprint는 provider 삭제 없이 안전하게 정리한다.
- 완료된 past_due 재시도가 구독 상태 변경 또는 charge claim 전 실패로 끝나면 기존 retry/consent 상태를 completed-only CAS로 정리해 bounded completion selector를 영구 점유하지 않는다.
- billing redirect coordinator는 initial/card-change 목적을 최종 business completion으로 분기하고, non-overlapping scheduler가 response-loss와 terminal initial settlement를 수렴시킨다.
- 돈 환불이나 provider payment cancellation은 추가하지 않았다.

## 6.6 Task 17 완료 상태

Task 17은 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- 같은 결제 주기의 Basic→Pro만 즉시 변경하고, 월간은 월간·연간은 연간으로 유지한다. 가격 차액은 현재 결제 기간, 추가 크레딧은 immutable `benefitAnchorAt`의 현재 월 혜택 구간을 기준으로 각각 올림 계산한다.
- 100원 미만 즉시 차액, Pro→Basic, 월간↔연간 변경은 현재 계약과 분리된 하나의 immutable 예약 snapshot으로 저장·교체하며 DELETE가 정확히 그 예약을 취소한다.
- 응답 유실 중에는 같은 upgrade order와 billing charge idempotency key를 복구하고, 확정 실패 뒤 새 요청은 `changedAt`이 포함된 새 logical key를 사용한다. direct/lookup terminal 결과는 같은 purpose-fenced CAS를 거치고 failed order는 다시 열리지 않는다.
- 결제 완료 이행은 subscription lock 다음 access-user lock 순서를 지키며, 구독 계약·기존 subscription access snapshot·차액 credit grant·fulfillment finalizer를 한 transaction에서 처리한다. 기존 기간, billing/benefit/credit anchor, access 시작·종료, 다음 월 지급일은 유지된다.
- 미해결 또는 paid-unfulfilled upgrade가 있으면 정기 갱신, 기간 종료 access 처리, 구독 취소가 상태를 앞서 바꾸지 않는다. 기간 경계에서도 기존 upgrade는 새 plan-change 요청보다 먼저 복구된다.
- 돈 환불이나 provider payment cancellation은 추가하지 않았다.

## 6.7 Task 18 완료 상태

Task 18은 tests-only genuine RED, 최소 구현, 실제 PostgreSQL 검증, 독립 리뷰, fix round 1, scoped 재리뷰까지 완료했다.

- 고객 결제내역은 owner-scoped SQL과 정규 opaque `(created_at,id)` cursor를 사용하고, 최대 100개씩 안전한 명시 필드만 반환한다. receipt capability/hash, 내부 주문 UUID, provider key, idempotency key, secret ciphertext, fingerprint, raw payload, 전체 계좌번호는 노출하지 않는다.
- OpenAPI는 hash-only receipt 저장과 충돌하던 단건 주문 DTO 재사용을 제거하고 closed `PaymentHistoryItem`을 사용한다. 영수증 URL과 가상계좌 정보는 HTTPS Toss host와 마스킹 형식을 통과한 값만 반환한다.
- 관리자는 bounded order/webhook/reconciliation warning 조회와 단건 재조정만 사용하며 기존 `OperatorJwtGuard`를 재사용한다. warning은 reconciliation-required 또는 외부 취소 관찰만 포함한다.
- paid/failed 주문에 외부 취소 관찰이 있으면 fulfillment retry보다 provider 재조회를 우선하고, 직접 fulfillment retry 경계도 이를 거부한다. provider 재조회 전에 안전한 operator-attributed audit event를 기록한다.
- 돈 환불, provider payment cancellation, generic subscription charge/retry, 새 역할은 추가하지 않았다.

## 6.8 Task 19 완료 상태

Task 19는 tests-only genuine RED, 최종 module/DI 구현, review/direct legacy 제거, 실제 PostgreSQL 검증, 독립 리뷰까지 완료했다.

- final PaymentsModule은 Task 7~18의 controller/service/scheduler/repository/entity를 정확히 한 번 등록하고, normal·billing·order reconciliation handler를 `useExisting` singleton으로 연결한다.
- `SubscriptionsController`의 type-only DI import 결함을 value import로 바로잡아 실제 Nest compile에서 네 constructor token이 정확한 service class로 해석된다.
- review service/controller/rate limiter, 구형 direct callback/DTO, legacy payment-method-change runtime model/repository/entity가 제거됐다. 역사 migration `178720`은 그대로 유지되고 runtime datasource metadata에서만 legacy entity가 빠졌다.
- `.env.example`은 `WEB_BASE_URL`, 여섯 final `TOSS_PAYMENTS_*`, 기존 `API_KEY_ENC_SECRET`만 final 결제 계약으로 설명하며 client key와 API-only secret을 구분한다.
- 돈 환불, provider payment cancellation, push, merge, deploy, compose, 실제 Toss 호출은 수행하지 않았다.

## 6.9 Task 20 완료 상태

Task 20은 tests-only genuine RED, 최소 구현, 전체 customer 회귀/build, 독립 리뷰까지 완료했다.

- 구독·topup checkout은 상품 code만 서버에 보내며, owner-bound receipt session이 client/customer key, order id/name, amount, return URL을 공급한다.
- checkout page는 인증 guard 아래 있고 URL에서 정확한 43자 `receipt`만 받는다. 다른 query 값은 결제 입력으로 사용하지 않는다.
- billing auth는 공식 SDK의 `payment({ customerKey })`와 CARD 요청만 사용하고, normal payment widget은 서버 금액으로 한 번 render한 뒤 사용자 클릭 때만 요청하고 teardown/error에서 해제된다.
- public checkout 파일/route가 제거됐고 mock mode도 실제 create→owner-session 응답 형태를 따른다.
- 결제 review 결합은 checkout에서 제거됐다. Task 21 소유 pricing/result compatibility만 임시로 남아 있으며 Task 21과 Task 25에서 완전히 제거해야 한다.
- 돈 환불, provider payment cancellation, 실제 Toss 호출, push/merge/deploy는 수행하지 않았다.

## 6.10 Task 21 완료 상태

Task 21은 고객/API 분리 tests-only genuine RED, 최소 구현, 전체 customer 회귀/build, 독립 리뷰, fix round 1과 scoped 재리뷰까지 완료했다.

- pricing은 active server catalog만 표시하고 상품 code만 checkout 생성에 보낸다. 로그아웃 선택은 기존 Google login initiator를 즉시 호출하며, 실제 OAuth URL builder는 exact `/pricing`, 단일 `subscribe`, no hash, bounded code grammar만 return path로 허용한다. 복귀 뒤 code는 active catalog와 다시 대조되고 URL의 가격·금액·ID는 신뢰하지 않는다.
- topup은 active access를 요구하고 credit product code만 보낸다. checkout과 결과는 인증된 portal 아래 정확한 43자 receipt capability만 사용한다.
- 결제 결과는 owner GET을 bounded polling하고 서버가 지원하는 topup 상태에서만 reconciliation을 호출한다. subscription 결과는 provider hammer 없이 owner GET으로 수렴한다. 영수증 URL은 승인된 Toss HTTPS host, 가상계좌는 canonical masked 값만 표시한다.
- dashboard는 서버 subscription snapshot과 safe CARD 필드만 사용해 cancel/resume/manual retry, 즉시·예약 plan change, 예약 취소, final consent 기반 카드변경을 제공한다. issuer 이름이나 last-four를 추론하지 않고 nested server checkout을 SDK에 직접 전달한다.
- payment-method result는 final attempt status/field만 사용하고, API redirect는 `payment_method_change`를 immutable attempt id의 guarded result로 보내며 initial/topup은 receipt result로 유지한다.
- history는 safe `PaymentHistoryItem`과 opaque cursor만 사용한다. mock도 첫 페이지의 exact cursor만 terminal second page로 진전시키고 임의 cursor를 권한처럼 수용하지 않는다.
- 남은 review/config/old checkout runtime과 public payment result route는 제거됐다. 법률 문서 `/refund`는 유지하며 돈 환불 동작, provider payment cancellation, 실제 Toss 호출은 추가하지 않았다.

## 6.11 Task 22 완료 상태

Task 22는 tests-only genuine RED, 최소 구현, 전체 admin 회귀/build, 독립 리뷰, fix round 1과 scoped 재리뷰까지 완료했다.

- 관리자 console은 Task 18 final OpenAPI의 `AdminPaymentOrder`, `PaymentWebhook`, `ReconciliationWarning`과 `{items,nextCursor}` page만 사용하며 stale illustrative alias를 만들지 않는다.
- 세 paged feed는 bounded limit와 opaque cursor를 사용한다. 각 feed의 independent pending/generation fence가 rapid double-click의 같은 cursor 재사용, refresh 뒤 stale append, stale error/pending release, 반복 next cursor를 차단한다.
- 변경 동작은 주문 상태 재확인과 기존 fulfillment retry뿐이다. fulfillment retry는 paid + failed + external cancellation 없음 조건을 UI와 runtime에서 모두 확인한다.
- webhook retry/manual-review 상태, billing-key deletion, external cancellation warning은 safe projection만 표시한다. raw payload, secret, billing key, fingerprint, 전체 계좌번호는 표시하지 않는다.
- `/payment-operations`는 `adminGuard` 아래 있고 실제 header navigation에서 접근 가능하다. 기존 plans production은 이미 Basic/Pro/topup catalog 편집을 지원해 no-op으로 유지하고 final fixture만 보강했다.
- 돈 환불, provider payment cancellation, generic charge, webhook mutation, 실제 Toss 호출은 추가하지 않았다.
- 비차단 항목: webhook row tracking은 `receivedAt + eventType`이 완전한 unique key가 아닐 수 있어 final review에서 `$index` 등 local unique strategy를 재검토한다. 기존 initial bundle budget은 34.64 kB 초과 warning이지만 production build는 통과한다.

## 6.12 Task 23 완료 상태

Task 23은 tests-only genuine RED, 최소 구현, 정적 Compose 검증, 독립 리뷰, 두 차례 fix round와 scoped 재리뷰까지 완료했다.

- API에만 일곱 final Toss 환경변수가 전달되고 customer/admin service 및 browser build args에는 노출되지 않는다.
- validator는 env 파일을 source/eval하지 않고 Docker Compose가 실제로 decode한 last-wins JSON을 검증하며, missing tooling·필수값·removed name·placeholder·재사용 credential은 값 비노출로 fail-closed한다.
- return/web base는 HTTPS 또는 raw canonical `localhost`, `127.0.0.1`, `[::1]` HTTP origin만 허용하고 malformed authority, 비정규 loopback alias, path/query/hash/credential/encoded/backslash 형태를 거부한다.
- HMAC은 API와 같이 trimmed nonempty UTF-8을 허용하며 별도 encoding/length 규칙을 만들지 않는다. `=#literal`과 `= # comment`는 Compose 의미대로 구분한다.
- dev/stage/prod examples와 runbook은 secret-free이며 V2 `2024-06-01`, exact webhook path/events, key separation, API recreation, Task 25 checklist를 기록한다.
- `deploy-dev.sh`, operational Compose, 컨테이너, 네트워크, 실제 Toss, push/merge/deploy는 실행하지 않았다.

## 6.13 Task 24 완료 상태

Task 24는 세 desktop feature worktree의 계약·전체 테스트·build 검증과 scoped one-spec 보완, 독립 리뷰까지 완료했다.

- Angular는 locked-plugin pricing, settings pricing/credits navigation, access/credit 표시, 내부 credit restoration 관련 전체 회귀를 통과한다. `/app/credits`는 actual ledger button 기반 exact bridge assertion으로 고정됐다.
- Electron은 known web-client path resolution/handoff를 포함한 전체 219 tests와 build를 통과했다.
- desktop local API는 authenticated `/access/current`, `/credits/*`, `/operations/*`, operation failure/internal credit refund를 포함한 전체 803 tests와 build를 통과했다.
- `LicensePolicyService`를 포함한 production runtime은 바뀌지 않았고 Electron/NestJS commit도 생성하지 않았다.
- package/lock, protected worktree, push/merge/deploy/Compose/Toss 동작은 건드리지 않았다.

## 7. 남은 전체 작업

- 승인된 Task 1~25 구현·검증·독립 리뷰 범위에는 남은 작업이 없다.
- 개발서버에 설정된 테스트 키를 사용하되 현재 전체 연동 브랜치의 test MID 연결과 webhook delivery 관찰 준비를 재확인한 뒤 `docs/payments/toss-payments-test-key-checklist.md`의 11개 unchecked 시나리오를 별도 운영 승인 아래 실행한다. 카드사 심사용 테스트 결제 성공 이력과 이 11개 전체 연동 검증은 별개다.
- feature push, dev merge, PR, 배포는 수행하지 않았으며 후속으로 자동 실행하지 않는다.

## 8. 현재 build 의미

Task 19에서 이전 46개 legacy/module diagnostics를 모두 제거했고, Node 22 full API build는 0 diagnostics로 통과한다. Task 25의 fresh API build와 `153/153` suites, `1,313/1,313` tests도 통과했다. 다만 whole-repository no-write ESLint는 안정적으로 `3,891` findings인 controller-approved baseline debt이며 PASS로 표현하지 않는다. PG-range changed non-spec production TypeScript `71` paths의 lint는 0이다.

## 9. ngrok과 직접 결제 테스트

사용자가 ngrok 3.39.11을 설치했다. 세션 중 `ngrok http 4040`을 실행했으며 출력은 Web Interface와 forwarding target이 모두 `localhost:4040`이었다. 확인 당시 4040 listener는 ngrok뿐이고 API 기본 포트 3000 listener는 없었다.

- 포트 번호 자체가 고정 전용이라는 뜻은 아니다. ngrok의 target port는 실제 로컬 API가 듣는 port와 같아야 한다.
- 이 API는 `process.env.PORT ?? 3000`이고 `.env.example`은 `PORT=3000`이므로 기본 실행 시 `ngrok http 3000`을 쓴다.
- `PORT=8080`으로 API를 실행하면 Toss 문서 예시처럼 `ngrok http 8080`을 쓸 수 있다.
- OpenAPI/controller/service와 final runtime module에는 `POST /payments/tosspayments/webhook`이 연결돼 있다.
- 개발자센터에는 `https://<ngrok-domain>/payments/tosspayments/webhook`을 등록하고 세 이벤트를 선택한다.
- 브라우저 checkout 경로와 pricing/topup/result/subscription/history 실제 사용자 흐름은 Task 20~21에서 연결됐다.
- Task 25는 자동 검증과 11-scenario 체크리스트 문서화를 완료했다. 개발서버에는 테스트 키 설정과 카드사 심사용 테스트 결제 성공 이력이 있지만, Task 25는 현재 전체 연동 브랜치에 대한 11개 수동 시나리오와 그 MID/webhook 관찰 준비를 별도로 실행·재검증하지 않았다. 향후 실행하더라도 돈 취소·환불 API는 체크리스트 범위에 없다.

## 10. 세션 종료 상태

- Task 25 구현·fix·독립 재리뷰가 종료됐고 최종 verdict는 READY다.
- API feature worktree clean at `2dce869d1f1f911d5cec1ce822529b3b663f9a4e`
- 고객 웹 feature worktree clean at `95218a891177ba38ad109bf29bbd510966106265`
- 관리자 웹 feature worktree clean at `2ccb825d6a56c690a72a89244798caa1a8968b72`
- infra feature worktree clean at `e6ae78f58b559cf3715f6acaecf6ac067a4e7930`
- Angular feature worktree clean at `f0da4e4a4aca26bbf08ccbc16856b085c06b0404`
- Electron feature worktree clean at `abdc5753741301f4bf22278a22ca8e20dc78ac24`
- desktop local API feature worktree clean at `8e131e3f601f981259c7bf00bb1a3001631c0fe5`
- 일곱 원본 dev 및 일곱 access-credit 보호 worktree는 모두 clean이고 보존 HEAD가 변하지 않았다.
- exact PostgreSQL test container는 없고 port `55432`는 비활성이다. desktop feature의 임시 `.env.packaged`도 없다.
- feature upstream과 동일 이름 remote feature ref가 없으며 push, PR, dev merge, deploy, operational Compose, 실제 Toss/network 호출은 없었다.
- ngrok 프로세스는 사용자가 시작한 외부 프로세스이므로 Codex가 종료하거나 수정하지 않았다.
- 실제 test-key 체크리스트 실행과 branch integration/deployment는 새 환경·권한·지시가 있을 때만 별도 수행한다.

## 11. 2026-08-21 후속 가상계좌 correction

- 카카오페이, 네이버페이, 퀵계좌이체 topup 수동 실행이 모두 `paid`/`DONE`/fulfillment
  `succeeded`와 exactly-once grant/ledger/event로 통과했다. 퀵계좌이체는 계좌이체 방식이다.
- 주문서형 SDK는 유지하고, 가상계좌 만료는 최초 승인과 snapshot이 없는 first-observed
  reconciliation에서 Toss가 반환한 `virtualAccount.dueDate`를 검증·저장하도록 바꿨다.
  자체 `order.createdAt + 24h` 계산은 제거했다.
- 사용되지 않던 `CheckoutSession.virtualAccountDueDate` API/client 계약도 제거했다.
- API `b80b31e`, 고객 웹 `fd71462`; API 1,334 tests와 고객 웹 170 tests, 양쪽 build가
  통과했다.
- 체크리스트 범위 명확화 뒤 API HEAD는 `a47a971`이다.
- 공용 `_docs` widget pair에서는 가상계좌 노출/페이코 제거를 설정할 수 없다. user-MID
  widget key/variant 준비 후 결제 어드민 설정과 가상계좌 발급·입금·만료 수동 검증이 남는다.
- 수정 전 방식으로 생성된 실제 가상계좌 row와 배포 이력이 없으므로 legacy backfill이나
  migration은 추가하지 않았고 disposable 55420의 다른 검증 데이터도 삭제하지 않았다.
- 가상계좌 포함 돈 환불/provider payment cancellation은 여전히 설계·구현되지 않았다.
