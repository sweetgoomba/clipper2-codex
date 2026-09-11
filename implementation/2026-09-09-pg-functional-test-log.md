# 2026-09-09 PG 기능 테스트 — 세션 A

## 범위와 기록 기준

- 담당: TASKS 1번 실제 화면, 3·4번 TEST PG 검증 및 발견 결함 수정.
- 원본 `web/*`, `desktop/*`가 작업 정본. `.integration-clones`는 조회·수정하지 않는다.
- 서버 명령은 사용자가 실행한다. 장비·경로·영향을 설명하고 한 단계의 결과를 받은 뒤 다음 명령을 안내한다.
- 운영 desktop/runner 신규 구축·호스트 안정성·라이브 준비는 세션 B 담당. 개발 전환은 양쪽 모두 제외.
- 운영 DB 초기화, 개발 앱/runner/DB/데이터/캐시 변경, 라이브키/실결제, desktop 식별자 변경을 진행하지 않는다.
- 수정 직전 현재 diff를 재확인한다. 같은 파일 수정 또는 동일 서비스 배포·재시작이 필요하면 대상·영향을 먼저 알리고 조율한다. 기존 ahead/미커밋 변경을 묶어 commit/push하지 않는다.
- 실제 결과는 `이번 세션 관찰`, `9/8 인계 증거`, `예상`, `미실행`을 구분한다. 키·토큰·원문 provider payload는 기록하지 않는다.

## 시작 시 읽은 자료

- [9/8 종료 인수인계](./2026-09-08-production-pg-session-closeout.md)
- [TASKS](./TASKS.md), 현재 미커밋 diff 포함
- [Infra 팀 운영 매뉴얼](../../web/clipper_infra/runbooks/production-deployment-team-guide.md)
- Infra 미커밋 deploy-prod/recreate-prod-databases diff 및 콘솔 설정·구축 이력의 장비/경로/PG 관련 항목
- Superpowers using-superpowers, verification-before-completion. 결함 수정에 들어가면 systematic-debugging/TDD 및 해당 구현 스킬을 추가 적용한다.

## 2026-09-09 시작 — 로컬 원본 Git 관찰

새 fetch를 하지 않은 시작 시 로컬 HEAD/추적 upstream 기준. 서버 실행 revision은 후속 사용자 출력으로 확인(A01 아래), 원격 최신 HEAD는 미확인.

| 저장소 | branch | HEAD | 작업트리/추적 상태 |
| --- | --- | --- | --- |
| web/clipper_web_client | integration/toss-payments-pg-20260903 | 888c2b96d818857306e9376c3436563c394971b1 | clean, 추적 upstream 차이 없음 |
| web/clipper_web_admin | 동일 | fb3e532b3e9b195c5c149a207fbcbf5673932245 | clean, 추적 upstream 차이 없음 |
| web/clipper_web_api | 동일 | 27103011e2e0672199721c6c3974c5bfc4e0d741 | clean, 추적 upstream 차이 없음 |
| web/clipper_infra | 동일 | 088e520260eb8f806f662c76e0732100aabfbcb5 | 아래 기존 문서 5개 보존 |
| desktop/clipper_angular | 동일 | 7f34704b614c29b3e4f4b4271f75a15739367c43 | clean, upstream 없음 |
| desktop/clipper_nestjs | 동일 | 19c667e23bbcecc7761195bf582c31a402c8e762 | clean, upstream 없음 |
| desktop/clipper_electron | 동일 | dbf55c821fbe71f1812ccf93cab3ca7bca21c649 | clean, upstream 없음 |
| desktop/clipper_python | merge/meme-overlay-into-dev | f8274ace954e271cbd511eb58982a6621caf5662 | clean, 추적 upstream 차이 없음 |
| .codex | main | 40beeda2849e2241335f8d1c557c307b084b2898 | 기존 ahead25, 수정4/신규7, staged 없음 |

Infra 기존 수정: `runbooks/deploy-prod.md`, `runbooks/recreate-prod-databases.md`.
Infra 기존 신규: `runbooks/production-console-settings.md`, `production-deployment-team-guide.md`, `production-setup-history-20260908.md`.

.codex 기존 수정: `implementation/TASKS.md`, `implementation/WORKLOG.md`, `main/2026-09-03-toss-payments-pg-release-candidate-integration-log.md`, `main/2026-09-03-toss-payments-pg-session-handoff-and-integration-readiness.md`.
.codex 기존 신규: `implementation/2026-09-08-payment-disclosure-plan.md`, closeout、handoff、`NEXT_SESSION_PG_TESTS.md`、`NEXT_SESSION_PRODUCTION_SETUP.md`、`NEXT_SESSION_PROMPT.md`、`main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md`.

현재 앱 코드 결함을 새로 재현한 것은 없다. 앱 코드 수정·테스트 실행·배포·재시작은 하지 않았다.

## 완료 증거 — 처음부터 반복하지 않는 항목

아래는 **9/8 인계 증거**이며 이번 세션 재검증 완료가 아니다.

| 항목 | 완료 범위 | 남은 구분 |
| --- | --- | --- |
| 추가충전400 `topup_2b66981ddc5c41a7b05ddc1245d862e2` | 5,900원, paid/succeeded, 지급1·원장1, 정확30일, Toss GET paymentKey 200/DONE | 상태재확인2회는 실제 지급 재실행/동시성 증거가 아님 |
| 자동갱신 취소·재개 | 고객화면/권한/기간/잔액 유지, 신규결제 없음 | Admin/DB, 경계·실패만 잔여 |
| 카드변경 | 새카드 표시, 신규결제 없음, 기간/잔액/청구일 유지 | 이전키 정리, 다음청구 사용키, 취소·실패·연체 |
| Pro 월간→연간 | 차액72,017원, 기존 구독1000 회수·새1000 지급 | 성공 당시 DB/Toss 전항목, 중복·실패 |
| 연간 환불 case `61d6c4bc-b2b3-4328-835f-b27f3eb98807` | Toss 취소, 돈/내부 완료, 구독종료, 해당 구독1000 회수 | 이번에는 read-only 교차확인만; 재환불 금지 |
| BILLING_DELETED | DELETE200, 성공 전송 기록 | 앱 inbox 저장/중복/재시도 미검증; 결제취소 이벤트와 구분 |

## A01 — 최신 화면과 실행 revision

- 사전 상태/대상: 운영 TEST, 회원 `metabuzz2023@gmail.com` / `f47e0e29-217d-40e7-bc66-b22bf4c58c72`. 9/8 마지막 상태 Trial, 사용가능5,200=topup4,800+trial400.
- 예상 결제/취소·권한/크레딧 변화: 조회로 인한 변화 없음. 이후 자연 만료/작업/다른 세션 변경은 시각·원장으로 설명해야 하며 5,200을 강제로 맞추지 않는다.
- Customer `/my/payment-history`: 요금제→결제내역→크레딧 메뉴, 단일 표, 결제금액, 상단 KST 안내 제거, 대상72,017원 환불 상태.
- Customer `/my/credits`: 지급/원장/요약의 출처색 일치; topup4,800, trial400, 구독 잔여0; 각 topup 기한 유지.
- Customer `/my`: Trial/현재 권한, 이전 Pro연간과 종료2026-09-08 16:34 표시, 종료 구독의 변경/카드/갱신 관리패널 숨김.
- Admin `/payment-operations`: 같은 회원·주문, 환불완료 표시, 대응 환불의 돈/내부 completed. 저장된 Toss 상태와 현재 Toss 조회는 구분.
- 실제 결과: 사용자 m4-prod docker inspect 출력으로 아래 3개 running/revision 확인. 사용자 화면 결과는 대기.
- 남은 검증: 최신 화면과 현 실행 revision 연결. 이번 inspect는 health/API/DB 정상 또는 화면 통과를 증명하지 않는다.

2026-09-09 사용자 실행 출력(정확한 실행시각 미제공): 프롬프트 `m4-prod@m4-produi-Macmini ~`에서 실행. 명령은 경로 독립적인 docker inspect이며 실제 cwd는 홈이다.

| 컨테이너 | 상태 | 실행 revision | imageID |
| --- | --- | --- | --- |
| clipper-web-client-prod | running | 888c2b96d818857306e9376c3436563c394971b1 | sha256:fcb0ae61a0a52c8185ea4e3ea5be64fb7e3a2868529d648f19fdfb3969431327 |
| clipper-web-admin-prod | running | fb3e532b3e9b195c5c149a207fbcbf5673932245 | sha256:c95a7f1598b5d780ff1d9e4ecdc6f37ccd20e15a8c98c92a1933f18ee4801d18 |
| clipper-web-api-prod | running | 27103011e2e0672199721c6c3974c5bfc4e0d741 | sha256:e0e3aee4d0a622301b652a22cd798ad079d73f0f818520130dc3f75335e2b696 |

판정: 실행 revision 3개가 시작 시 로컬 원본 및 9/8 마지막 배포값과 일치. 조회로 결제/취소/권한/크레딧 변화 없음.

첫 서버 조회: **m4-prod**, `/Users/m4-prod/Documents/projects/clipperstudio`. 조회만 수행하며 컨테이너·DB·env를 변경하거나 재시작하지 않는다. 다른 장비 터미널이면 실행하지 않는다.

```sh
docker inspect --format '{{.Name}} | status={{.State.Status}} | imageID={{.Image}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' clipper-web-client-prod clipper-web-admin-prod clipper-web-api-prod
```

## A02 — 완료 환불 read-only 대조

- 대상 case: `61d6c4bc-b2b3-4328-835f-b27f3eb98807`, annual_subscription.
- 대상 주문: `upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375`, 72,017원.
- 예상 상태(인계 기준): 종료/생성2026-09-08 16:34:11 KST, 내부완료16:34:21, 취소72,017/잔액0. 구독1000 회수, topup4,800/trial400 보존.
- 예상 변화: 결제·취소・회수 신규 발생 없음. 이미 완료된 환불 실행/재시도 버튼을 사용하지 않는다. Admin의 상태재확인도 저장을 수반할 수 있으므로 read-only DB/Toss GET과 구분한다.
- 조회 순서(11:18 실패 후 정정): m2-db의 운영 **Admin DB** 확인 → 짧은 READ ONLY 트랜잭션에서 case/items/internal events → 주문 누적환불/환불잔액 → 연결 구독/이용권 → 지급/원장 → 필요시 현재 Toss TEST GET 결제 요약 대조. 이 PG/권한/크레딧 테이블은 모두 admin datasource에 등록되어 있다.
- 로컬 엔티티 위치 확인: `payments/infrastructure`의 payment_refund_cases/items/internal_events, payment_orders, subscriptions; `access/infrastructure`의 user_access_grants; `credits/infrastructure`의 credit_grants/credit_ledger_entries. SQL은 실제 컬럼과 서버 대상을 확인한 후 안내한다. `SELECT *`/비밀 payload 출력 금지.
- 판정: 주문 paid는 원승인 기록이므로 단독 모순 아님. refundProcessingCaseId 잔존만으로 처리중 판정 금지. 이벤트/돈/내부/권한/크레딧을 함께 확인한다.
- 실제 결과: 11:18 User DB 오안내 조회 실패 후, 11:24 case 요약(A02-2), 17:57 item/event/order(A02-3), 18:25 subscription/access/grant/환불ledger(A02-4) 일치 확인. 특정 완료환불의 DB 대조는 완료. 현재 Toss GET/실제 화면/재실행 멱등성은 미확인.
- 남은 검증: 조회로 완료 건 정합성을 증명하며 환불 예외/복구·멱등성 검증 완료로 확대하지 않는다.

### A02-1 조회 대상 DB 안내 오류 — 원인과 정정

- 원인: 에이전트가 엔티티 테이블명만 확인하고 datasource 등록을 확인하지 않은 채 User DB를 안내했다. 사용자의 명령 실행 오류나 운영 migration 누락으로 판단하지 않는다.
- 소스 근거: `src/core/database/admin.datasource.ts`에 PaymentRefundCase/Item/InternalEvent, PaymentOrder, Subscription, UserAccessGrant, CreditGrant/Ledger 등록. `payments.module.ts`의 forFeature 연결은 `admin`, `typeorm-payment-refunds.repository.ts`는 `@InjectDataSource('admin')`. 생성 migration도 `migrations/admin/1788400000000-CreatePaymentRefundWorkflow.ts`에 있다.
- 영향: READ ONLY SELECT 실패, 결제/환불/DB 데이터 변경 없음. `ON_ERROR_STOP=1`로 psql 종료 시 열린 트랜잭션은 롤백되므로 별도 복구 명령은 필요 없다.
- 정정 명령 대상: m2-db `clipper-db-admin-prod` / 명시 DB `clipper_admin_prod`. 같은 case 요약 SELECT만 재안내했고 후속 A02-2에서 조회 성공. DB 생성·migration·환불 재실행을 안내하지 않는다.
- 적용 절차: Superpowers systematic-debugging으로 실제 DB 연결 경로를 추적. 수정은 이 전용 기록과 안내에만 적용; 앱 코드/공유 TASKS 변경 없음.

### A02-2 완료 환불 case 요약 — 운영 DB 확인

- 사용자 실행/관찰: m2-db `clipper-db-admin-prod` → `clipper_admin_prod`; `read_only=on`; checked_at `2026-09-09 11:24:14.183404+09`. 마지막 ROLLBACK 출력 확인.
- case `61d6c4bc-b2b3-4328-835f-b27f3eb98807`, 회원 `f47e0e29-217d-40e7-bc66-b22bf4c58c72`, 연결 subscription `d33a3102-2d16-446c-8422-141e4785bad9`.
- kind `annual_subscription`, money_status `completed`, internal_status `completed`, planned_total_krw=actual_total_krw=72017.
- subscription_end_mode `immediate`, subscription_end_at `2026-09-08 16:34:11.089+09`.
- created_at `2026-09-08 16:34:11.049475+09`, updated_at `2026-09-08 16:34:21.512082+09`. updated_at은 case 수정시각이며 별도 내부이벤트 완료시각으로 단정하지 않는다.
- 판정: case 요약 기대값 일치. 최초 조회 실패 원인은 DB 대상 오안내였음이 확인됨. 조회로 인한 추가결제/취소/권한/크레딧 변화 없음.
- 남은 검증: 연결 item의 실제 취소액·완료상태, refund_internal_effects 이벤트, order 누적환불/잔액, subscription/access 종료와 grant/ledger 회수 및 topup/Trial 유지, 현재 Toss GET. case의 completed만으로 이들 정합성/멱등성을 확정하지 않는다.

### A02-3 환불 항목·내부 이벤트·주문 — 운영 DB 확인

- 사용자 실행/관찰: m2-db `clipper-db-admin-prod` → `clipper_admin_prod`; read_only=on; checked_at `2026-09-09 17:57:55.065153+09`. REPEATABLE READ READ ONLY 조회, ROLLBACK 출력 확인.
- 환불 item 1건: `55ae5952-3c92-4387-b694-b0f8f3b48cbf`, payment_order_id `2851be09-ace0-4f12-b4d1-493de2dcdbfb`, purpose subscription_upgrade, status completed. 원금/요청/실제취소 모두72,017, scope full, completion_source toss_api, completed_at `2026-09-08 16:34:21+09`, error_code 빈 값.
- 내부 event 1건: `ad1d3b96-04e9-4bee-833f-08950e6bd606`, refund_internal_effects, completed, error_code 빈 값, created_at `2026-09-08 16:34:21.512082+09`.
- 연결 order 1건: 위 payment_order_id, order_no `upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375`, 회원/구독 ID가 case와 일치. purpose subscription_upgrade, status paid, fulfillment succeeded, amount/paid_amount72,017, refund_status full, cumulative_refunded72,017, refundable_balance0.
- 저장 provider_status DONE, last_refund_provider_checked_at `2026-09-08 16:34:21+09`. 현재 Toss GET 결과가 아니다. 현 `TypeOrmPaymentOrdersRepository.updateRefundSnapshot`은 누적환불/잔액/refund_status/조회시각만 갱신하고 provider_status는 갱신하지 않는다. 이 저장 DONE만으로 취소 실패라고 판단하거나 paid를 변경하지 않는다.
- 판정: 해당 case/item/event/order의 식별자·금액·환불완료 상태 일치. 이벤트1건 존재는 확인했으나 재실행/동시요청 멱등성 증거는 아니다.
- 다음: 구독·이용권 종료, 구독 지급 잔여0 및 환불회수 원장, topup/Trial의 남은 잔액/기한을 동일 read-only 스냅샷으로 확인. 현재 Toss GET과 실제 고객/Admin 화면도 남음.
- 로컬 재확인: API HEAD2710301 유지, 다른 작업의 신규 `docker-compose.pg-local.yml` 발견. 열거나 수정하지 않고 보존. 이번 응답은 전용 로그만 수정.

### A02-4 구독·이용권·지급·환불 회수 원장 — 운영 DB 확인

- 사용자 출력 출처: 첨부 `pasted-text.txt`의 조회 결과. m2-db `clipper-db-admin-prod` → `clipper_admin_prod`, read_only=on, checked_at `2026-09-09 18:25:31.963056+09`, ROLLBACK 확인. 조회 자체의 결제/취소/권한/크레딧 변화 없음.
- 구독 `d33a3102-2d16-446c-8422-141e4785bad9`: Pro 연간, canceled, next_billing_at/retry_at 비어 있음, refund_end_mode immediate, refund_end_at `2026-09-08 16:34:11.089+09`, billing_key_removal_status succeeded. refund_processing_case_id는 완료 case와 일치하며 남아 있어도 처리중을 뜻하지 않는다.
- 원래 구독 기간 `2026-09-08 13:50:57+09` → `2027-09-08 13:50:57+09`는 남아 있다. 활성 여부는 canceled 및 환불 종료/이용권 상태와 함께 판정하며 기간을 임의 수정하지 않는다.
- 이용권2건: 기존 월간 `6a1ceb3a-96a2-4b6b-907e-447789be2e8b`는 replaced, ended_at `2026-09-08 13:50:57+09`. 새 연간 `a8499ff2-143e-4c59-bd9f-95dce1a07759`는 revoked, ended_at/revoked_at 모두 환불 종료시각과 일치. 둘 다 next_credit_grant_at 비어 있음. 연간 ends_at에 원래2027년 날짜가 남아 있어도 현재 활성권한이 아니다.

| 지급 ID | 출처 | 최초/잔여 | 상태 | 지급 → 만료(KST) |
| --- | --- | --- | --- | --- |
| 6db9281f-9887-4965-85bb-e76b28d36565 | free_trial | 400/400 | active | 09-08 06:03:51.603 → 10-08 06:03:51.603 |
| 42c202d5-d39c-499c-837a-2da3aa6a3580 | subscription 월간 | 1000/0 | revoked | 09-08 06:06:55.635 → 10-08 06:06:55.635 |
| 1dcc225a-ac45-414a-ad09-31417c07a618 | topup 최초400 | 400/400 | active | 09-08 10:23:08.126 → 10-08 10:23:08.126 |
| f5ffc738-4eba-4113-b23c-ae143de59108 | subscription 연간 첫월 | 1000/0 | revoked | 09-08 13:50:57 → 10-08 13:50:57 |
| 5193342b-8226-4f73-bb56-293a45d0b839 | topup 후기400 | 400/400 | active | 09-08 15:52:47.889 → 10-08 15:52:47.889 |
| e3753266-0d64-45bc-b0e9-e752796b51ee | topup 후기4000 | 4000/4000 | active | 09-08 15:53:44.107 → 10-08 15:53:44.107 |

- 모든 표 날짜는2026년. topup3건은 subscription_id/access_grant_id/refund_case_id 비어 있음. 각 지급→만료가 정확히30일이며 조회시점에 유효함을 첨부값으로 계산 확인. 유효잔액 topup4800+free_trial400=5200, subscription0. Trial 크레딧 잔존은 확인했으나 고객 화면의 Trial 표시는 별도 확인 대상.
- 월간 지급의 refund_case_id는 비어 있고, 연간 첫월 지급만 해당 환불case와 연결. 최초 월간 주문 `e0a5cf48-3fb1-4273-8e58-2cd162bc3397`과 상향주문 `2851be09-ace0-4f12-b4d1-493de2dcdbfb`의 지급을 구분.
- 환불 회수 원장1건: `11bab7cd-e8b5-417f-8146-8716d25da418`, credit_grant_id `f5ffc738-4eba-4113-b23c-ae143de59108`, payment_refund_revoke, delta -1000, balance_after0, payment_order_id 상향주문, reference_key `refund:61d6c4bc-b2b3-4328-835f-b27f3eb98807:f5ffc738-4eba-4113-b23c-ae143de59108`, created_at `2026-09-08 16:34:21.512082+09`.
- 판정: 해당 완료환불의 case/item/event/order/subscription/access/grant/ledger 대조 통과. 돈완료→권한종료→구독크레딧회수와 독립 topup/Trial 유지가 일치. 조회1건 존재만으로 처리 재실행·동시성 멱등성 전체를 완료하지 않는다. TASKS4의 해당 DB 대조 항목만 체크.

### A03 사전 식별 — 후기 추가충전 주문

| 대상 | payment_order_id | order_no | 지급/현재잔여 |
| --- | --- | --- | --- |
| 후기400 | d8782ce3-60b9-451d-866a-903994a32f44 | topup_16485bfbf22349ec882d55b283492362 | 400/400 |
| 후기4000 | 9bce8bdd-0140-4f3b-babe-9febce1ba0ce | topup_2160ffafa7e64e7ba15274e9253577db | 4000/4000 |

지급표와 DB의 주문 연결/30일 기한까지 확인. 각 주문금액/paid/fulfillment/지급원장/Toss 대조는 미완료. A04의 첫 신규환불 후보는 위 후기400이며, 현재 유효잔액5200 기준으로 조건 충족 후400 회수 시4800 예상. 아직 환불 실행을 안내하지 않았다.

### A01 Admin 실제 화면 — 사용자 확인

- 사용자 확인: 72,017원 환불내역의 완료 표시에 대해 확인 응답. 회원 링크로 이동한 결제표는 상향 차액 / Pro 연간 / 전액 환불, 결제72,017·환불72,017·잔액0·저장상태DONE·전액 환불 완료, 환불완료2026-09-08 16:34 표시.
- 회원 상세 환불표: 연간 구독 / 완료 / 계획72,017·실제72,017 / 구독종료16:34 / 마지막변경16:34.
- 해당 case 상세: 돈 완료, 내부 처리 완료, 계획/실제72,017, 이용종료16:34:11, 생성16:34:11, 마지막변경16:34:21. 주문2851be09-ace0-4f12-b4d1-493de2dcdbfb 취소 성공, 요청/실제72,017. 최초 요청 시작16:34:20 → 성공16:34:21, refund_internal_effects 완료16:34:21.
- 판정: 사용자가 제공한 Admin 결제표/환불표/환불 상세 표시가 DB 대조 결과와 일치. 요청 시작의 취소금액 미확정 표시는 후속 성공 이력과 구분하며 현재 미완료로 오해하지 않는다.
- 상세의 취소 가능 잔액72,017은 `refund-case-detail.component.html`의 `item.refundableBeforeKrw` 표시로, 취소 전 잔액이다. 현재 주문 환불잔액0과 모순되지 않는다. 시점이 모호한 라벨은 향후 문구 개선 후보이며 이번 응답에서 앱 코드를 수정하지 않았다.
- 화면 관찰시각은 미제공. Customer 실제 화면은 아직 미확인. 별도 구독 요약 배지 자체의 텍스트는 이번 인용에 없으므로 확인 완료로 확대하지 않는다. 원본 메모/사유와 IDE 비밀값은 기록하지 않는다.

## 남은 테스트 실행 순서

아래는 실행 계획이다. 주문·견적·실행 직전 상태를 실제로 확인한 뒤 사용자가 실행한다. 금액 미확정 항목은 서버 견적을 기록하며 임의 계산으로 확정하지 않는다. 신규 환불·구독 등 변화가 생기면 A01의 기준 잔액도 갱신한다.

| 순서/ID | 사전 상태·대상 | 예상 결제/취소 | 예상 권한·크레딧 | 실제 결과 | 남은 검증 |
| --- | --- | --- | --- | --- | --- |
| 1/A01 | 위 회원, 최신 고객/Admin 화면 | 없음 | 인계 기준 Trial/5,200, 구독0 | 사용자 출력으로 3개 running/revision 일치 | 실제 화면 |
| 2/A02 | 완료 연간환불 특정case | 신규취소 없음; 기존72,017/잔액0 확인 | 종료/회수 완료·topup/Trial 유지 | 특정case 전체 DB 대조 통과、유효잔액5200 | 현재 Toss GET·실제 화면·예외/멱등성 별도 |
| 3/A03 | 후기 topup400/4,000, 위 식별표 주문2건 | 조회만; snapshot상5,900/29,900 여부 대조 | 각 미사용 잔액·정확30일 | 지급/주문연결/잔여/30일 DB 확인 | paid/fulfillment/금액/원장/Toss 대조 |
| 4/A04 | A03의 후기400을 첫 별도환불 후보로 선정; 미사용/미만료/미환불·Toss 잔액 확인 | 조건 충족시5,900 전액취소 | 대상400만 회수; 기준5,200 유지 중이면4,800; 구독/Trial/다른topup 불변 | 미실행·대상 미확정 | 자격·최종동의/확정·돈/내부/회수·중복방지 |
| 5/A05 | 월간환불용 별도 신규 TEST 주문; 기존 최초 월간은 이미 상향에 연결되어 재사용하지 않음 | 현 카탈로그/견적 확인; Pro월간10,900 유지시 신규승인 후 조건충족시 같은 금액취소 | 신규 구독1000 지급 후 해당1000 회수·권한종료; 기존topup/Trial 유지 | 미실행 | 계정/상품 확정, 지급미사용, 금액/동의/기간, DB/Toss |
| 6/A06 | 예약/갱신용 활성 구독을 별도로 확보; 변경 전 기간/청구시각/카드/잔액 저장 | 예약확정·취소 자체 신규청구 없음; 다음갱신은 확정 견적금액1회 | 즉시 권한 불변, 예약정보 반영/취소; 갱신 때 예약상품 권한/지급1회 | 모달만 인계됨 | 확정→취소→재예약→실제적용, 금지조합, 실패 유지 |
| 7/A07 | 기존 성공 상향주문 조회 및 별도 실패/중복 대상 | 기존72,017 건 조회만; 실패 시 불필요 승인/중복승인 없음 | 기존성공1000 회수/1000 지급 대조, 실패는 기존권한·크레딧 유지 | 성공화면만 인계됨 | DB/Toss, 실패 주입 가능 범위·동시성 |
| 8/A08 | 정상/연체 구독 별도 대상; 카드·다음회차 식별정보는 마스킹 | 정상카드변경/취소 자체청구 없음; 연체는 표시된 미납청구 조건대로 | 정상변경 권한/기간/잔액 유지; 연체성공 복구 | 정상성공만 인계됨 | 취소/실패, 이전키 정리, 다음청구 새키, 해지재개 Admin/DB·경계 |
| 9/A09 | 월간갱신/연간월별지급/실패재시도 대상 구독과 worker 일정 확인 | 월간/연간갱신 각1회, 연간 중간 월별지급은 청구0; 실패/재시도 중복승인0 | 지급1회, 유예/만료/복구는 현재 코드 정책·시각에 대조 | 미실행 | 예정/실제시각, 유예기간·재시도간격 확정, worker 재기동 세션B 조율 |
| 10/A10 | 사용량있는 월/연/추가충전 및 부분취소/내부실패 복구용 별도 주문 | 자격차단은 취소0; 부분지원/복구는 실제 정책·견적 먼저 확정 | 차단 시 변화0; 돈완료/내부실패 시 내부효과만 복구·중복회수0 | 미실행 | 사용량 조건, provider 불확정, 재시도, 환불중 자연기간종료 UI |
| 11/A11 | TEST Widget/Billing별 MID·실제 inbox/event/callback 식별, 승인된 대상 이벤트 | 재전달로 추가청구/취소0 | 지급/회수/갱신 같은 내부효과1회 | BILLING_DELETED 전송만 인계됨 | PAYMENT_STATUS_CHANGED/DEPOSIT_CALLBACK/BILLING_DELETED 앱저장, 중복/재시도, 지급함수 재실행·동시성, 옛ngrok 설정 조회 |
| 12/A12 | TEST에서 가상계좌를 실제 제공하는 경우만 | 입금대기는 미승인/미지급, 입금확정1회, 미입금만료 청구0 | 입금 후1회 지급, 만료/중복은 추가지급0 | 제공여부 미확인 | 미제공이면 이유와 제외기록 |
| 상시/A13 | 최초구독·추가충전·즉시/예약변경·재개·카드변경 최종동의 화면 | 금액/주기/자동갱신·연체청구 안내가 서버 확정값과 일치; 미동의 실행 차단 | 명시된 권한/크레딧 변화와 일치 | 구현/배포 인계, 최종증거 미확인 | 운영 화면증거; 전략팀 전달은 별도 요청 시, 약관/FAQ·법무 완료로 기록하지 않음 |

현재 코드상 환불 자격 근거: [payment-refund-eligibility.service.ts](../../web/clipper_web_api/src/modules/payments/application/payment-refund-eligibility.service.ts). additional_credit는 해당 주문의 active·미사용·미만료 지급 건을 검사한다. 구독은 연결 구독 지급 건의 사용량을 검사한다. 사용량있는 연간환불을 성공시켜야 한다고 가정하지 않는다. provider 최신확인은 별도 필요하다.

시간 이동/강제 worker 실행은 이 계획으로 승인된 것이 아니다. 정기갱신을 앞당길 필요가 생기면 실제 기능/격리된 검증 방법을 먼저 확인하고 운영 데이터 변경 여부·영향을 제시한다. 개발 서버/DB로 전환하지 않는다.

## 개별 실행 결과 추가 양식

- ID / KST 관찰시각 / 실행자 / 실행장비·경로:
- 실행 전 회원·주문·case·subscription 식별자와 상태:
- 금액·취소·권한·크레딧 기대값(견적/정책 근거):
- 실제 사용자 액션/명령과 결과(비밀값 제외):
- Customer / Admin / DB / Toss 각각의 증거:
- 통과·실패·부분확인 및 차이:
- 남은 검증 / 다음 실행:
- 코드 수정·테스트·배포가 있으면 대상파일·SHA·실행revision·세션B 조율:

### A01 Customer 마이페이지 — 사용자 확인

- 사용자에게 Trial 표시, 이전 Pro 연간과 환불 종료시각, 종료 구독의 요금제 변경·카드변경·갱신 관리 버튼 숨김을 안내했고, 사용자가 “응 확인”으로 확인했다. 실제 관찰시각은 미제공.
- 위 마이페이지 항목을 사용자 확인 완료로 기록. Admin 환불 표시 확인과 함께 TASKS1의 환불 회원 최종 화면 항목을 체크했다.
- 결제내역 표/메뉴/문구 및 크레딧 출처색은 이번 응답에 포함된 확인 항목이 아니므로 별도 대기. 새 결제·환불·서비스 변경 없음.

### A01 Customer 결제내역·크레딧 화면 — 사용자 확인

- 메뉴 요금제→결제내역→크레딧, 단일 표와 결제금액 표시, 상단 KST 안내 없음, 크레딧 잔액5,200 및 지급/원장/상단요약 출처색 일치에 대해 사용자가 “확인.”으로 응답했다. 관찰시각은 미제공.
- TASKS1의 마지막 수정본 실제 화면 확인 체크 완료. 앞서 확인한 Customer 마이페이지와 Admin 환불 표시를 합쳐 요청된 최신 화면 항목의 사용자 확인을 마쳤다. 예외/멱등성/현재 Toss 조회 완료로 확대하지 않는다.
- 다음 A03: 이미 식별한 후기400/4000의 주문금액/paid/fulfillment/환불상태/상품 snapshot 및 지급원장 대조. 최초400 대조는 반복하지 않는다. 예상 금액5,900/29,900, 지급400/4000, 각 주문당 지급1건/지급원장1건, 환불0, 잔여400/4000, 30일 기한. 실행 결과는 아직 대기.

### A03 후기 추가충전400/4000 — 주문·지급·원장 DB 확인

- 사용자 m2-db 운영 Admin DB 출력: checked_at `2026-09-09 19:18:59.812894+09`, database_name clipper_admin_prod, read_only on, 마지막 ROLLBACK 확인. 조회에 따른 결제/취소/권한/잔액 변화 없음.
- 후기400: 주문 d8782ce3-60b9-451d-866a-903994a32f44 / topup_16485bfbf22349ec882d55b283492362, 추가 크레딧400, credit_topup, paid/succeeded, 금액/승인5,900, snapshot400/30일, refund none/누적0/잔액5,900. paid_at `2026-09-08 15:52:47.889+09`.
- 후기4000: 주문9bce8bdd-0140-4f3b-babe-9febce1ba0ce / topup_2160ffafa7e64e7ba15274e9253577db, 추가 크레딧4,000, credit_topup, paid/succeeded, 금액/승인29,900, snapshot4000/30일, refund none/누적0/잔액29,900. paid_at `2026-09-08 15:53:44.107+09`.
- 각 주문의 topup active 지급1건, 최초/잔여400 및4000, 지급시각은 해당 내부 paid_at과 일치. 만료는 각각 `2026-10-08 15:52:47.889+09`, `2026-10-08 15:53:44.107+09`, validity30 days 확인.
- 원장 각각 grant1건: 400 원장 d1d873fa-8b5e-4cd2-bf13-c820b5085dc4, delta/balance400, created_at `2026-09-08 15:52:48.00275+09`; 4000 원장 d102bc64-def1-4e80-b640-a4866c69c626, delta/balance4000, created_at `2026-09-08 15:53:44.225524+09`. 지급 ID는 A03 사전 식별과 일치. 조회된 두 주문의 지급에 차감/회수 원장 없음.
- 판정: 후기2건의 DB 대조 통과. 내부 paid/지급시각과 원장생성시각을 구분하며 Toss 승인시각은 아직 미확인. 현재 Toss 외부 상태를 대조하기 전 DB/Toss 전체 체크는 유지한다.
- 다음 조회 방법: 사용자가 Toss 관리자 테스트 결제내역에서 후기400/4000 및 완료 연간환불 주문을 열어 주문번호·승인금액·현재상태·누적취소·잔액을 제공. API GET으로 확인한 증거와 관리자 화면 증거는 구분해 기록한다. 결제 취소/환불 실행은 하지 않는다.

### 2026-09-10 Toss 관리자 목록 확인 및 조회 방법 변경

- 사용자 화면: `fc8d0_upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375`, Pro 연간72,017원, 상태 취소, 표시시각2026-09-08 13:50:57. 현재 목록에서 연간 취소 상태 확인. 별도 취소액/잔액 필드는 제공되지 않았고 표시시각을 취소시각으로 해석하지 않는다.
- 후기 추가충전2건은 해당 목록에 보이지 않는다고 보고. Toss 전체에서 거래가 없다는 증거가 아니다.
- 코드 확인: topup 주문은 widget, 구독상향은 billing 키 세트를 사용하며 provider는 각기 다른 SECRET_KEY 변수로 조회한다. 9/8 인계에도 공용 Widget TEST키의 orderId조회404/저장 paymentKey조회200 이력이 있다. 이를 고려하지 않고 동일 관리자 목록에3건 모두 보일 것으로 안내한 점을 정정한다. 정확한 현재 MID/공용키 여부는 아직 미확정.
- 다음: m4-prod의 실행 API 컨테이너에서 운영 Admin DB를 READ ONLY 조회해 대상3건의 paymentKey/key_set을 메모리에서만 사용하고 해당 TEST키로 Toss GET 호출. 출력은 주문번호/금액/상태/취소합계/잔액 등만 허용. paymentKey/SECRET_KEY/env 원문 출력 금지. 취소POST/DB snapshot갱신/서비스재시작 없음.

### 2026-09-10 공용 TEST키 확인 및 직접 조회 명령 준비

- 사용자 명시 확인: 추가충전은 단건결제로 아직 공용 TEST키를 사용하므로 해당 관리자 테스트 목록에 보이지 않음. 공용키 여부 미확정이라는 앞선 기록은 이 확인으로 해소. 동일 목록을 다시 찾도록 안내하지 않는다.
- 다음 대상을 후기 추가충전2건으로 한정. m4-prod의 clipper-web-api-prod 컨테이너 /app에서 node로 실행. 실제 Admin DB 환경변수와 test_ Widget secret을 검증하고, DB READ ONLY SELECT 후 연결을 닫고 저장 paymentKey로 Toss GET2회. 출력 필드는 주문번호/HTTP/상태/결제일치 여부/금액/승인시각만 사용.
- 명령 초안 `/private/tmp/clipper-pg-topup-readonly.cjs` 로컬 node --check 통과. 실제 서버/DB/Toss 요청은 실행하지 않았으며 사용자 출력 대기. 파일은 로컬 안내 초안이고 서버에 존재한다고 가정하지 않는다.
- 키/env/paymentKey/응답원문 출력, API 부팅, migration, 결제승인/취소, DB snapshot갱신, 재시작 없음. 서버에서 실행할 명령은 본 대화에 heredoc으로 제공.

### A03 Toss GET 결과 — 후기 두 건 DB/Toss 대조 완료

- 사용자 m4-prod 출력. 공용 Widget TEST키/저장 paymentKey로 GET 조회, DB 조회는 READ ONLY. 원문 키 노출 없이 요약 수신.
- 후기400 `topup_16485bfbf22349ec882d55b283492362`: checkedAt `2026-09-09T15:08:41.877Z` = `2026-09-10 00:08:41.877 KST`, HTTP200, DONE, samePayment true, Toss orderId와 내부 주문번호 일치, DB/Toss금액5,900, 잔액5,900, 취소0. approvedAt `2026-09-08T15:52:47+09:00`.
- 후기4000 `topup_2160ffafa7e64e7ba15274e9253577db`: checkedAt `2026-09-09T15:08:42.297Z` = `2026-09-10 00:08:42.297 KST`, HTTP200, DONE, samePayment true, 주문번호 일치, DB/Toss금액29,900, 잔액29,900, 취소0. approvedAt `2026-09-08T15:53:43+09:00`.
- Toss 승인시각과 내부 paid/지급시각은 구분. 후기4000은 Toss15:53:43, 내부15:53:44.107로 서로 다른 처리 시점이다. 타임스탬프를 같다고 기록하지 않는다.
- 판정: A03 두 주문의 DB/Toss 대조 통과. TASKS4 해당 항목 체크. 단순 조회이며 승인/취소/지급 재실행 없음.

### A04 후기400 별도 환불 — 사전 미리보기 안내

- 대상 회원 f47e0e29-217d-40e7-bc66-b22bf4c58c72, 주문 d8782ce3-60b9-451d-866a-903994a32f44 / topup_16485bfbf22349ec882d55b283492362, 지급5193342b-8226-4f73-bb56-293a45d0b839.
- 사전 증거: DB paid/succeeded, 지급active·최초/잔여400·사용원장없음, 만료2026-10-08 15:52:47.889 KST; 최신 Toss DONE/5,900/취소0. 실제 실행 전 미리보기로 최신 자격/대상을 다시 확인한다.
- 예정 영향: TEST결제5,900 전액취소, 해당400만 회수; 직전 총잔액5,200 유지 중이면4,800=다른topup4,400+Trial400. 현재Trial 및 이미 종료된 구독, 다른 지급 기한은 유지. 최초400/후기4000/기존 연간환불을 대상으로 선택하지 않는다.
- 다음 UI: 회원 상세의 환불 처리에서 추가 구매 크레딧 대상을 선택하고 미리보기 조회. 관련 결제 UUID가 위 대상인지, 금액5,900, 연결 지급400/400/0, 잠금·회수 대상인지 확인한다. 같은 이름의 대상이 여러 개면 미리보기의 UUID로 판별한다.
- 이번 단계는 미리보기만 안내. 새 환불case 생성/실제취소 결과는 아직 없음. 사용자 화면의 자격과 실제 대상 결과를 받은 뒤 실행 단계로 진행한다.

### A04 후기400 환불 미리보기 — 사용자 결과

- 관련 결제: 추가 크레딧 구매 d8782ce3-60b9-451d-866a-903994a32f44, 원결제/취소가능/환불금액 모두5,900원.
- 연결 지급: 추가 구매5193342b-8226-4f73-bb56-293a45d0b839, 최초/잔여/사용400/400/0, active, 잠금·회수 대상.
- 판정: 이번 신규환불 대상·금액·사용량·회수 지급이 사전 계획과 일치. 전체 자격 배지 및 최종확인창 내용은 사용자 인용에 없으므로 별도 확인. 실제 취소/회수는 아직 미실행으로 기록.
- 다음 사용자 단계: 환불 사유 입력 → 입력 내용 확인 → 최종창의 같은 주문/5,900/400 회수/구독종료 없음 조건 확인 후 해당 신규 TEST환불1회 실행. 차이가 있거나 실행불가 안내면 실행하지 않고 표시 내용 공유. 이는 기존 완료연간환불 재실행이 아니다.
- 예상 결과: 신규 additional_credit case 생성, 돈/내부 완료, 해당 지급400 회수, 기존 잔액5,200 유지 중이면4,800, Trial/다른topup 기한 유지. 실제 결과로 case ID/완료상태/잔액을 받고 DB/Toss 후속 대조. 배포/worker재시작 없음.

### A04 신규 환불 접수 — 대기 상태 관찰

- 사용자 환불 실행 후 신규 case `6ae2147f-5a19-474a-8dae-e3c656445127` 생성. 회원 환불표에 추가 구매 크레딧 / 대기 / 계획5,900·실제0 / 구독종료 해당없음 / 마지막변경2026-09-10 00:12 표시.
- 회원 화면은 이미 환불 처리중 안내와 위 신규case 상세 링크를 표시. 사용자 화면 사용가능 크레딧은5,200. 오류는 없었다고 보고.
- 판정: 접수는 확인, 취소/내부회수 완료는 아직 미확인. 잔액5,200 표시만으로 현재 DB의 잠금/사용가능 잔액이나 실패 원인을 단정하지 않는다.
- 다음: 신규case 상세의 새로 조회로 돈/내부 상태·취소 항목·오류/처리이력 확인 후 고객 잔액 새로고침. 대기가 유지되면 읽기전용 DB/worker 상태·로그 확인. 새 환불 생성·재시도 버튼·worker 재시작을 안내하지 않는다.

### A04 新규 추가충전 환불 — Admin 상세/회원 화면 완료 확인

- 사용자 새로 조회 후 case6ae2147f-5a19-474a-8dae-e3c656445127: 추가 구매 크레딧, 돈 완료/내부 처리 완료, 계획/실제5,900, 이용종료 해당없음. 생성2026-09-10 00:12:35, 마지막변경00:12:36. 관찰시각 자체는 미제공.
- 취소 항목: 주문d8782ce3-60b9-451d-866a-903994a32f44, 취소성공, 원결제/취소전잔액/요청/실제5,900, 표시시각00:12:40. item869ed4cd-2732-421c-a529-aad11a2556da의 요청시작/성공 기록은 모두00:12:36, refund_internal_effects 완료도00:12:36.
- 시간차 관찰: 취소 항목00:12:40과 내부/요청기록00:12:36을 그대로 보존. 서로 다른 시각 필드일 수 있으므로 완료시각을 일괄36초나40초로 덮어 기록하지 않는다. 후속 DB/Toss로 각 필드 출처 대조.
- Admin 회원 상세: 사용가능4,800=free_trial400+topup4,400. 추가충전 환불표 완료5,900/5,900, 구독종료 해당없음. 주문표 추가크레딧400 전액환불, 결제/환불5,900/5,900, 잔액0, 저장DONE, 전액환불완료. 기존 연간환불은 완료 유지.
- 판정: 실행 후 UI 예상 결과 일치. 앞선 대기 화면은 접수 직후 상태로 보이며 영구 대기/worker 장애로 확정할 증거 없음. 새로 조회 이후 완료됐다는 관찰이며 새로 조회가 환불을 실행했다고 해석하지 않는다.
- 남은 검증: 신규case/item/event/order의 DB대조, 해당400 회수원장1건/다른topup·Trial 잔액과기한 유지, 현재 Toss GET 취소5,900/잔액0. 실제 고객웹 화면 확인과 이 Admin 회원 상세 증거는 구분한다. 부분실패/복구/동시성/중복실행 검증은 별도.

### A04 신규 추가충전 환불 — DB 대조 통과

- 사용자 m2-db 출력: clipper_admin_prod / read_only on / checked_at `2026-09-10 00:18:08.358666+09`, ROLLBACK 확인.
- case6ae2147f-5a19-474a-8dae-e3c656445127: additional_credit, money/internal completed, actual_total5900, subscription_id/end_at 비어 있음, end_mode none. item869ed4cd-2732-421c-a529-aad11a2556da completed, actual_canceled5900, completed_at `2026-09-10 00:12:40+09`. 주문topup_16485bfbf22349ec882d55b283492362 full/누적5900/환불잔액0.
- 내부 event281c5efe-af4a-4ef0-a9a9-f22b0e0c28c0: refund_internal_effects completed, 오류코드 빈 값, created_at `2026-09-10 00:12:36.763848+09`.
- 대상 지급5193342b-8226-4f73-bb56-293a45d0b839: topup revoked, 최초400/잔여0, 해당 신규case 연결. 원장 grant+400 기존1건, payment_refund_revoke-400 신규1건(6aaea822-5c82-4879-8bc0-b7a113c21fa0), balance_after0, 주문/지급/case reference 일치, created_at `2026-09-10 00:12:36.763848+09`.
- 다른 지급은 기존상태 유지: free_trial400 active 만료10-08 06:03:51.603, 최초topup400 active 만료10-08 10:23:08.126, 후기topup4000 active 만료10-08 15:53:44.107(모두2026년 KST). 기존 월간/연간 구독지급 잔여0/revoked 유지. 잔액4800=topup4400+free_trial400, 타 지급 기한 변경 없음.
- 판정: 신규 추가충전환불의 case/item/event/order/grant/ledger 정합성과 독립 크레딧 보존 확인. 시각 차이40초/36.763848초는 별도 필드로 유지하고 Toss 취소시각과 후속 대조. 실제 재실행/동시성 검증은 아님.
- 다음: 앞서 사용자 실행이 성공한 m4-prod Toss GET2건 명령을 그대로 재실행. 이 명령은 취소POST나 DB 쓰기 없이 조회만 한다. 후기400은 CANCELED/누적취소5900/잔액0, 후기4000은 DONE/누적취소0/잔액29900 예상. 서버에 임시 초안 파일이 있다고 가정하지 않는다.

### A04 환불 후 Toss GET — Admin/DB/Toss 대조 완료

- 사용자 m4-prod 읽기전용 GET 출력: 후기400 checkedAt `2026-09-09T15:20:34.370Z` = `2026-09-10 00:20:34.370 KST`, HTTP200/CANCELED/samePayment true, 주문번호 일치, DB/Toss원승인5,900, 누적취소5,900, 잔액0.
- 후기4000 checkedAt `2026-09-09T15:20:34.657Z` = `2026-09-10 00:20:34.657 KST`, HTTP200/DONE/samePayment true, 주문번호 일치, DB/Toss금액29,900, 누적취소0, 잔액29,900. 다른 추가충전 결제에 취소 영향 없음.
- 승인시각은 환불 전 조회와 동일. 이 출력에는 canceledAt이 없으므로00:12:40 취소 항목시각의 provider 직접 재대조 완료로 기록하지 않는다.
- 판정: 미사용 추가충전400 환불1건의 Admin 화면/DB/Toss 확인 완료. 기존paid 기록과 별도full 환불상태,400 회수1건, 다른topup/Trial4800과 기한 보존. TASKS4에 이 제한된 완료범위만 추가하고 전체 환불 매트릭스는 미완료 유지.
- 남은 A04 화면 확인: 실제 Customer `/my/credits` 잔액4,800(추가구매4,400+무료체험400), 해당400 지급회수 및 `/my/payment-history`의5,900원 전액환불 표시. 지금까지 환불 후 잔액/주문표 증거는 Admin 회원 상세였다.
- 다음 계획: 위 고객 화면 확인 후 신규 월간 구독/미사용 월간환불 A05 준비. 과거 최초 월간 주문은 상향/환불 이력에 연결되어 재환불 대상으로 쓰지 않는다. 신규 주문은 현재 카탈로그/견적/최종동의/실제 청구금액을 확인한 뒤 사용자 실행. 아직 신규 구독 결제 지시/실행 없음.

### A04 고객웹 환불 결과 — 사용자 확인

- 고객웹 사용가능4,800, 무료체험400/추가충전4,400 사용자 확인. 결제내역의 정확한 주문topup_16485bfbf22349ec882d55b283492362, 추가크레딧400, 결제5,900/환불5,900/남은0, 전액환불완료, 환불완료2026-09-10 00:12 확인.
- 고객 주문행 결제수단은 계좌이체로 표시됨. 이번 완료 케이스를 카드 추가충전 환불로 기록하지 않는다. 지급표의 개별 회수 배지 텍스트 자체는 이번 인용에 없지만 해당 지급 revoked/0은 앞선 DB로 확인했다.
- 판정: 이번 미사용 추가충전400 환불의 고객/Admin/DB/Toss 대조 완료. 전체 환불정책/부분실패/동시성 검증으로 확대하지 않는다.

### A05 새 Pro 월간 구독 미사용 환불 — 신규 결제 단계 준비

- 대상: 같은 회원 f47e0e29-217d-40e7-bc66-b22bf4c58c72. 직전 증거 기준 현재Trial, 유효4800=topup4400+free_trial400, 기존 구독 종료/구독 지급잔여0. 기존 최초 월간/상향/완료환불 주문은 재사용하지 않는다.
- 새 Pro 월간 선택 후 최종동의/결제 화면에서 월10,900원·월1000 지급·월간 자동갱신 및 다음청구 안내를 확인. 실제 표시가 다르거나 상향/연간 경로이면 결제하지 않고 화면 결과를 받는다. 동일 조건이면 사용자가 TEST 신규 구독 결제1회 실행하도록 안내.
- 예상: 새 월간 주문/승인10,900, 월간 구독활성, 신규 구독1000 지급1회, 잔액4800→5800. 기존Trial/topup 기한·잔액 유지. 정확한 시작/다음청구시각과 구독ID는 결과 수신 후 확정.
- 새 지급은 사용하지 않고 유지. 새 결제 결과/주문번호/잔액/다음청구 확인 뒤 월간환불 미리보기로 진행. 환불이 자격충족/성공하면 해당1000 회수 및 유료권한종료, 기존4800 유지 예상. 아직 신규 결제/환불 결과 없음.

### A05 새 Pro 월간 결제 — 고객 화면 결과

- 사용자 고객화면: Pro 월간10,900원, 새 주문번호 `sub_85c03506dbd04d979f808b1c418986ed`, 결제시각2026-09-10 00:25(분 단위).
- 자동 갱신 중, 현재상품Pro월간, 요금/혜택10,900원·1개월마다·월1000. 현재 이용기간 종료와 다음결제 예정 모두2026-10-10 00:25. 한국시간/KST 및 예정시각 이후 순차결제 안내도 확인.
- 판정: 신규 월간 결제/활성 구독 고객표시 확인. 현재 총잔액5800, 신규 지급/원장1건, DB/Toss 승인대조는 아직 미확인. 최종동의 체크박스/미동의차단 직접 증거로 확대하지 않는다.
- 다음: m2-db 운영 Admin DB에서 해당 order_no로 새 주문ID/구독ID/원승인/환불상태/기간/다음결제 및 연결 지급/원장을 READ ONLY 조회. 회원 출처별 현재 유효잔액도 함께 확인해 기존4800+신규구독1000=5800 기대값 대조. 완료된 과거 월간/연간/추가충전 주문을 새 환불 대상으로 쓰지 않는다.
- 신규 월간환불은 아직 미실행. 크레딧 사용 없이 기준선 확인 후 이 새 주문의 환불 미리보기로 진행.

### A05 새 월간 구독 — DB 사전 상태 확인

- 사용자 m2-db READ ONLY 출력: clipper_admin_prod, checked_at `2026-09-10 00:26:20.663077+09`, ROLLBACK 확인.
- 주문be117e3a-4e30-4dc8-affe-b0efac676487 / sub_85c03506dbd04d979f808b1c418986ed: paid/succeeded, paid_amount10900, refund none/잔액10900.
- 구독27308873-d541-44cb-aeb5-4579635f71df: active, 기간 `2026-09-10 00:25:16.236+09` → `2026-10-10 00:25:16.236+09`, 다음청구 동일 종료시각.
- 지급96f54551-4677-4e68-87e0-aba90451fd44: subscription active, 최초/잔여1000/1000, 지급/만료는 구독 기간과 일치. 주문/구독 연결 일치.
- 원장f2a559fc-c761-43fc-a826-63a374d5ee16: grant1건, delta/balance1000, created_at `2026-09-10 00:25:12.187871+09`. 지급시각16.236초보다 원장생성시각12.187871초가 앞서는 관찰은 그대로 보존. 각 시각의 생성원/장비 시계 차이 여부는 아직 검증하지 않았으며 지급 이전 처리 순서를 추정하지 않는다.
- 유효합계 free_trial400+subscription1000+topup4400=5800. 금액/연결/지급1건/미사용상태 기대값 일치. 현재 Toss 직접 조회는 아직 미실행.
- 다음: Admin 회원 상세 환불 대상 중 월간 정기구독을 선택해 미리보기 조회. 새 결제ID be117e3a-4e30-4dc8-affe-b0efac676487, 금액10900, 연결 지급96f54551-4677-4e68-87e0-aba90451fd44 및1000/1000/0 회수대상 확인. 이번 단계는 미리보기이며 환불 실행하지 않음.
- 환불 성공시 예상: 해당10900 전액취소, 새 월간 유료권한 종료/다음청구 중단, 신규1000 회수, 기존topup/Trial4800과기한 유지. 실제 미리보기/최종조건 확인 후 사용자 실행 안내.

### A05 월간 환불 미리보기 — 사용자 확인

- 관련 결제: 최초 구독 결제be117e3a-4e30-4dc8-affe-b0efac676487, 원결제/취소가능/환불금액 모두10,900원.
- 연결 지급96f54551-4677-4e68-87e0-aba90451fd44: 정기구독 지급, 최초/잔여/사용1000/1000/0, active, 잠금·회수 대상.
- 판정: 새 월간 결제/미사용 지급 대상과 예상금액 일치. 최종확인창의 종료/다음청구 안내와 실행 결과는 아직 미확인.
- 다음 사용자 실행: 사유 TEST 월간 구독 미사용 전액환불 검증 입력, 입력 내용 확인, 최종창의 같은 결제ID/총10900/회수1000/이용종료/다음청구 중단을 확인해 일치하면 신규 TEST환불1회 실행. 다르거나 오류면 실행/재실행하지 않고 화면내용을 받는다.
- 완료 예상: 새 환불case 돈/내부completed10900, 신규 월간권한 종료/다음청구중단, 해당1000 회수, 나머지4800 및 기한 유지. case ID/화면/DB/Toss 사후대조는 결과 수신 후 진행. 과거 완료환불은 재실행하지 않는다.

### A05 월간환불 실행 후 Admin 상세·잔액 — 사용자 확인

- 신규case `c7aa3c09-6a9c-48a2-b3e9-4aa1fd9ae16a`, 월간 정기구독, 회원f47e0e29-217d-40e7-bc66-b22bf4c58c72. 돈 완료/내부 처리 완료, 계획/실제10,900원 사용자 확인.
- 화면시각: 이용종료2026-09-10 00:29:12, 생성00:29:08, 마지막변경00:29:17. 표시 시각들의 차이는 보존하며 원인/정확한 DB 필드는 후속 조회로 확인.
- 사용자가 환불 상세의 잔액 위치를 물어 회원 상세 링크→사용가능 크레딧으로 안내를 정정함. 환불 상세는 돈/내부 상태, 회원 상세는 크레딧 잔액을 확인하는 서로 다른 화면이다. 이후 안내는 실제 버튼/행명·금액을 명시한다.
- 회원 상세 사용자 확인: 사용가능4800, 무료체험400, 추가구매4400. 구독1000 회수 후 기대합계와 일치. 이 화면만으로 회수원장1건·다른기한 보존을 확정하지 않는다.
- 판정: 신규 미사용 월간환불의 Admin 돈/내부완료와 회원 잔액 기대값 일치. DB/Toss 및 환불 후 실제 고객웹 종료/잔액/결제내역은 미확인.
- 다음: m2-db 운영 Admin DB READ ONLY에서 위case/item/order/연결subscription과access, 내부event, 대상지급96f54551-4677-4e68-87e0-aba90451fd44/회수원장 및 기타 지급잔액·기한 대조. 환불 재실행/재시작 없음.

### A05 월간환불 — 운영 DB 사후 대조 통과

- 사용자 m2-db READ ONLY 출력: clipper_admin_prod, checked_at `2026-09-10 00:32:49.269488+09`, ROLLBACK 확인.
- case c7aa3c09-6a9c-48a2-b3e9-4aa1fd9ae16a: monthly_subscription, money/internal completed, actual_total10900, immediate, 종료 `2026-09-10 00:29:12.835+09`. item completed/actual_canceled10900, 주문sub_85c03506dbd04d979f808b1c418986ed full/누적10900/잔액0.
- 구독27308873-d541-44cb-aeb5-4579635f71df canceled, next_billing_at/retry_at 비어 있음, refund_end_at case종료와 일치, billing_key_removal_status succeeded.
- 이용권44950884-ed90-4598-b218-628c965ece55 revoked, ended_at/revoked_at 모두 case종료와 일치, next_credit_grant_at 비어 있음.
- 내부event7d142bf2-2696-4377-a206-74f2427d83e1: refund_internal_effects completed, 오류코드 빈 값, created_at `2026-09-10 00:29:17.175556+09`.
- 신규 월간지급96f54551-4677-4e68-87e0-aba90451fd44 revoked/잔여0/해당case연결. 기존 grant+1000원장1건 유지, 신규 payment_refund_revoke-1000원장1건 ec5fff39-7652-400e-885f-19864f4e7431, balance_after0, reference의case/지급일치, created_at `2026-09-10 00:29:17.175556+09`.
- 기타 지급: free_trial400 및 topup400/4000 active/잔여보존, 만료는 각각10-08 06:03:51.603/10:23:08.126/15:53:44.107(2026년 KST)로 불변. 과거 회수된 구독/추가충전은 revoked/0 유지. 유효잔액4800 확인.
- 판정: 이번 월간환불의 Admin/DB 대조 통과. 재실행/동시성·실패복구 검증으로 확대하지 않는다. 현재 Toss상태 및 환불 후 실제 고객웹은 아직 미확인.
- 다음: Toss 관리자 테스트 결제내역에서 주문sub_85c03506dbd04d979f808b1c418986ed, Pro월간10,900, 결제09-10 00:25 건의 취소상태/취소금액/잔액을 확인. Billing 전용키 거래이므로 공용Widget 추가충전과 구분. 고객웹 /my 종료표시와 /my/credits4800, /my/payment-history 해당10,900 전액환불도 확인한다. 이번 단계는 열람만 한다.

### A05 Toss 관리자 — 월간 주문 취소 확인

- 사용자 Toss 테스트 결제목록: `fc8d0_sub_85c03506dbd04d979f808b1c418986ed`, Pro 월간, 신용·체크카드,10,900원, 상태 취소. 두 표시시각은2026-09-10 00:25:15. 관찰시각 및 표의 시각열 제목은 미제공이므로 취소시각으로 기록하지 않는다.
- 판정: 새 월간 주문과 일치하는 Toss 외부 취소상태 확인. 별도 취소액/잔액 필드는 이 목록에 없으며 그 수치는 앞선 DB10900/0 증거와 구분. API GET 직접 대조 완료로 기록하지 않는다.
- 남은 사용자 화면: 고객 /my Trial·이전Pro월간 환불종료·관리버튼숨김, /my/credits4800, /my/payment-history 이번10900 전액환불 표시. 지금까지 환불 후4800 증거는 Admin 회원 상세 및 DB였다.

### A05 고객 화면 최종 확인 — 미사용 월간환불 완료 범위

- 사용자 고객웹: 이용권 활성 / Trial / 무료체험, 사용가능4800 확인. Trial의 활성표시는 유료Pro가 유지된다는 뜻이 아니며 DB의 월간 canceled/이용권revoked와 모순되지 않는다.
- 결제내역: 정확한 주문sub_85c03506dbd04d979f808b1c418986ed, 구독시작Pro월간/카드, 주문09-10 00:24·결제00:25·환불완료00:29, 결제10900/환불10900/남은0/전액환불완료 사용자 확인. 관찰시각은 미제공. 이전상품영역/관리버튼 자체는 이번 인용에 없으므로 직접 텍스트 증거로 확대하지 않는다.
- 판정: A05 미사용 월간환불1건은 고객/Admin/DB와 Toss관리자 취소표시까지 대조 완료. Toss 취소액/잔액 API GET 직접대조, 재실행/동시성/부분실패/복구는 별도이며 전체 환불매트릭스는 미완료. TASKS4에 이 케이스의 완료범위만 추가.

### A06 예약변경·갱신 테스트 — 활성 구독 준비

- 사전상태: 현재Trial, 유효4800=topup4400+free_trial400. A05의 월간구독은 환불종료됐으므로 예약변경 대상으로 재사용하지 않는다.
- 다음 사용자 단계: 같은 계정에서 새 Pro월간을 선택, 최종10,900/월1000/월간자동갱신 조건이 일치하면 TEST결제1회. 이 구독은 예약확정→취소→재예약 및 갱신확인용으로 유지한다. 예상 잔액5800, 현재권한Pro월간 활성. 아직 결제 결과 없음.
- 결과로 새 주문번호/기간/다음청구/잔액을 기록한 뒤 Basic월간 하향변경의 서버견적과 예약시점을 확인한다. 예약 자체는 즉시청구/현재권한 변경 없이 다음갱신부터 적용해야 한다.
- 실제 갱신은 예정시각과 현재 worker 구조를 확인한 후 진행방법을 정한다. 이 안내는 운영DB 날짜변경/강제worker/재시작 승인이 아니다. 서비스 조작 필요시 세션B와 대상/영향 조율. 새 결제나 예약 성공을 미리 기록하지 않는다.

### A06 예약변경용 새 Pro월간 — 사용자 결제 완료

- 고객 완료화면: 결제와 상품 지급 완료, Pro월간10,900, 새 주문 `sub_713fd8b04d0e49f5b97cc6b7eee9e70b`, 결제2026-09-10 00:37, 다음결제2026-10-10 00:37, 사용가능5800. 시각은 화면 분 단위이며 정확한 초/DB ID는 미확인.
- 사전상태 기대와 일치: 기존4800에 새구독1000이 더해진 총5800. 개별 지급/원장 및 현재Toss 대조는 아직 완료하지 않음. 직전 환불한sub_85c03506dbd04d979f808b1c418986ed와 구분한다.
- 다음 고객 UI: 마이페이지 요금제 변경에서 월간 선택→Basic의 변경 선택→서버견적/최종동의 모달 확인. 견적 조회만 진행하며 예약확정은 아직 안 함. 예상은 다음갱신2026-10-10 00:37부터 Basic월간 적용, 지금 추가청구/크레딧회수 없음, 현재Pro/5800 유지. Basic 가격/지급량은 실제견적을 받아 확정한다.
- 수신할 증거: 대상상품, 변경 적용시점, 이번/다음청구 금액, Basic 크레딧 혜택, 자동갱신·필수동의 안내. 다른값이면 실제문구를 기록하고 비교한다.

### A06 월간 요금제 비교표 — 사용자 확인

- 사용자 화면: 월간 비교에서 Basic5,900/다음갱신일부터/변경예약보기, Pro10,900/현재이용중, Business29,900/차액결제후즉시/차액확인.
- 비교표 표시 확인이며 Basic 예약 상세 견적/정확한 적용일/동의/예약확정은 아직 미확인. 다음 클릭은 Basic 행의 변경 예약 보기. 비교표 열람에 따른 청구/권한/크레딧 변화 없음.

### A06 Basic 월간 예약 상세·필수동의 — 사용자 확인

- 제목 요금제 변경 예약. 현재 이용권/크레딧 유지, 지금 결제되지 않으며 다음갱신 적용 안내 확인.
- 상품Basic월간, 적용·결제예정2026-10-10 00:37, 다음금액5900, 이후매월자동결제. 적용 전 마이페이지에서 예약취소 가능 안내.
- 필수동의: 위 적용시각부터 Basic월간으로 변경하며 해지 전까지 매월5900 자동결제. 사용자 인용으로 내용 확인했으며 미동의 상태 버튼 차단 동작 자체는 아직 미확인.
- 다음: 미동의 상태 확정버튼이 비활성인지 확인 후 동의 체크/예약확정1회. 예약후 Basic월간 예약정보/적용시각/5900 표시, 현재Pro월간/잔액5800 유지, 신규 결제완료 내역 없음 확인. 예약확정 결과는 아직 수신 전이며 실제갱신적용 완료로 확대하지 않는다.

### A06 예약확정·미동의 버튼차단 — 사용자 확인

- 사용자 명시 확인: 동의 체크 전 변경예약 버튼 비활성.
- 확정후 고객화면: 현재Pro월간, 예약됨Basic월간/2026-10-10부터/5900/매월결제, 변경예약취소 버튼, 다음갱신 요금제를 예약했다는 성공안내.
- 판정: 미동의버튼차단 및 예약확정 고객표시 확인. 이번 응답에 잔액/결제내역 결과는 없으므로 유지 여부를 추가 확인한다. 실제 다음갱신 적용 완료로 확대하지 않는다.
- 다음: m2-db 운영Admin DB에서 새 주문sub_713fd8b04d0e49f5b97cc6b7eee9e70b로 연결구독을 식별하고 scheduled_* snapshot/현재상품/기간/다음청구, 관련 주문내역, 출처별유효잔액을 READ ONLY 대조. 예약취소 전 DB 증거 확보.

### A06 하향 예약확정 — 운영 DB 대조

- 사용자 m2-db 출력: clipper_admin_prod/read_only on, checked_at `2026-09-10 00:42:47.152506+09`, ROLLBACK 확인.
- 구독89ba75e8-111b-4935-a131-069eddc4e3b4 active, 현재Pro월간10900/월1000. 현재기간 `2026-09-10 00:37:44.944+09` → `2026-10-10 00:37:44.944+09`, next_billing_at 종료시각과 동일.
- 예약snapshot: Basic월간5900/주기1개월/월400, scheduled_change_effective_at `2026-10-10 00:37:44.944+09`. 고객견적/확정화면과 일치.
- 연결 주문 조회1건: 7aef3244-c50c-415f-a377-c1b330cf192d / sub_713fd8b04d0e49f5b97cc6b7eee9e70b, subscription_initial paid/succeeded10900, paid_at `2026-09-10 00:37:44.944+09`. 예약으로 새 결제주문이 추가된 흔적 없음.
- 유효잔액 free_trial400+subscription1000+topup4400=5800. 현재권한/금액/월지급량 유지 및 예약저장 기대값 일치. 실제갱신/예약취소/동시성 검증은 아님.
- 다음 고객 UI: 마이페이지의 예약됨Basic월간 아래 변경 예약 취소 버튼 클릭. 확인창이 있으면 Basic 변경예약 취소인지 확인해 진행. 예상은 Basic예약 표시 제거, 현재Pro월간/자동갱신/다음결제10-10 00:37 유지, 다음회차는 기존Pro10900, 잔액5800, 새청구없음. 사용자 결과 후 DB 예약필드 해제 대조, 재예약 순으로 진행.

### A06 변경 예약 취소 — 고객 화면 확인

- 사용자 확인: 변경 예약 취소 실행 후 `예약된 요금제 변경을 취소했습니다.` 안내. 새로고침 후 이용권 활성 / Pro / 정기구독·월간 / 사용 가능 크레딧5800 유지.
- 사전상태: 구독89ba75e8-111b-4935-a131-069eddc4e3b4에 Basic월간5900/월400 예약 저장. 예상은 예약 해제, 현재Pro/5800 유지, 추가 결제·취소·크레딧 변동 없음.
- 판정: 취소 성공 안내와 새로고침 후 현재상품·총잔액 유지 확인. 예약필드 해제 및 추가 주문 유무는 아직 DB 확인 전이며 실제 갱신 검증과 구분한다.
- 다음: 동일 구독을 운영 Admin DB READ ONLY로 조회하여 예약필드 해제, next_billing_at 유지, 연결 주문 및 유효잔액 대조. 서버 변경·재시작 없음.

### A06 변경 예약 취소 — 운영 DB 대조 완료

- 앞부분00:42:47은 예약확정 당시 기존 결과. 취소 후 신규 조회는 `2026-09-10 00:46:46.386641+09`, clipper_admin_prod/read_only on, ROLLBACK 확인.
- 구독89ba75e8-111b-4935-a131-069eddc4e3b4 active/Pro월간10900/월1000, next_billing_at 2026-10-10 00:37:44.944+09 유지. 조회한 scheduled_product_name/price_krw/monthly_credits/change_effective_at 모두 NULL.
- 연결 주문 기존7aef3244-c50c-415f-a377-c1b330cf192d 한 건, paid/succeeded10900/refund_status none. 유효잔액 free_trial400+subscription1000+topup4400=5800 유지.
- 판정: 예약확정→취소 고객화면/DB 대조 통과. 실제갱신 및 동시성/실패복구는 미검증.
- 다음 검증: 고객 Basic월간 재예약(2026-10-10 00:37부터5900) 1회. 즉시결제/현재권한/크레딧 변화 없음 예상. 아래 인계의 예약필드 해제 대기는 이 결과로 완료됐으며, 다음 단계는 재예약/갱신 준비다. DB일정조정/worker재시작 없음.

### A06 Basic 월간 재예약 — 고객 화면 확인

- 사전상태: 예약 취소의 UI/DB 대조 완료, 현재Pro월간/5800 유지.
- 사용자 재예약 후 성공안내 및 예약됨Basic월간/2026-10-10부터5900/매월결제 표시 확인. 현재Pro월간10900/월1000, 자동갱신 중, 이용기간종료/다음결제2026-10-10 00:37, 총5800 유지.
- 판정: 再예약 고객표시 확인. DB 재저장/추가주문 유무 및 실제갱신 시 Basic권한/400지급은 아직 미검증. 결제수단의 식별정보는 기록하지 않는다.
- 다음: m2-db에서 직전 READ ONLY SQL을 다시 실행하여 예약Basic/5900/400/적용시각, 기존주문1건, 총5800 대조. 이후 운영 갱신 검증 절차를 원본 코드/매뉴얼에서 확인한다. DB날짜조정·worker재시작 없음.

### A06 재예약 — 운영 DB 확인

- 사용자 조회시각2026-09-10 00:50:07.481584+09, clipper_admin_prod/read_only on. 이번 붙여넣기에는 마지막 ROLLBACK 출력이 없으므로 실행완료 출력 확인과 구분한다.
- 같은 구독 active/Pro월간10900/월1000, 다음청구2026-10-10 00:37:44.944+09 유지. Basic월간5900/월400/같은 적용시각 재저장 확인.
- 연결 주문은 기존 최초결제1건 paid/succeeded10900/refund none. free_trial400+subscription1000+topup4400=5800 유지.
- 예약 확정→취소→재예약의 UI/DB 대조 완료. 실제갱신 미검증. 원본 repository는 active 구독 next_billing_at이 조회시각 이하인 대상을 선택하므로 현재 예약은 아직 갱신대상이 아니다.
- 다음: m4-prod의 worker 컨테이너 상태를 읽기 전용 확인하고 실제갱신 시험 방법/영향을 정리한다. 현재 예정일은10월10일이며 이 단계에서 운영DB일정 변경이나 강제 갱신을 실행하지 않는다.

### A06 운영 프로세스 구조 확인

- 사용자 m4-prod docker ps 결과: Customer/Admin Up32hours, API Up34hours. 별도 Clipper 결제worker 컨테이너 없음. 다른 서비스 컨테이너는 이번 범위 밖으로 조작하지 않음.
- 원본 코드 확인: PaymentsModule에 PaymentRecoveryScheduler 등록, AppModule의 ScheduleModule.forRoot 및 EVERY_MINUTE cron. 갱신은 별도 worker 컨테이너가 아닌 API 내부 스케줄러 구조다. 컨테이너 목록만으로 cron 실제 성공을 입증하지는 않는다.
- 다음 검증: 배포 API의 스케줄러 파일을 읽기 전용으로 확인. API 재시작은 갱신 예정일을 앞당기지 않으며 현재10월10일 구독은 정상 현재시각에서 대상이 아니다. 강제갱신/DB시각변경 전 대상과 영향을 구체화해야 한다.

### A06 배포 스케줄러 확인 및 조기 갱신 사전 조사

- 사용자 m4-prod의 배포 JS 조회: processRenewals 호출50행, dueSubscriptionIds73행, EVERY_MINUTE126행 확인. 파일 존재/구현 확인이며 cron 실행 성공 증거는 아니다.
- 원본 renewal 서비스는 currentPeriodEnd로 갱신 멱등키와 다음 기간을 만들고, 예약 effectiveAt이 currentPeriodEnd 이하일 때 예약상품을 채택한다. next_billing_at 한 필드만 앞당기는 방식으로는 원하는 기간경계를 재현할 수 없다.
- 다음: 대상 구독의 billing/benefit anchor 및 연결 active 이용권/구독크레딧 시각을 READ ONLY로 확보해 조기갱신 조정안을 구체화한다. 예상 Basic TEST5900 1회/월400 지급 외 기존1000 만료처리도 함께 검증해야 한다. 운영DB 변경 명령·강제갱신·재시작은 아직 제공/실행하지 않는다.

### A06 조기 갱신 대상과 조정안 — 실행 전

- 사용자 READ ONLY 2026-09-10 00:53:10.921689+09, ROLLBACK 확인. 대상구독의 현재시작/billing_anchor/benefit_anchor는09-10 00:37:44.944, 종료/다음청구/예약적용은10-10 00:37:44.944(KST).
- 연결 이용권87de6afb-e741-4dac-8762-2f0bec1b697f active, 같은 시작/종료, next_credit_grant_at NULL. 연결 구독지급6ffd88b2-3ec7-4322-98c5-f8bf65f4990d active1000, 같은 지급/만료시각.
- 제안: 실행시각+5분을 T로 정하고 대상구독 current_period_end/next_billing_at/scheduled_change_effective_at, 해당 이용권 ends_at, 해당 구독지급 expires_at/benefit_period_end를 T로 맞추는 단일 트랜잭션. 기존값/대상건수/미사용1000 등 사전조건 검증 및 원복용 이전값 보존 필요. 현재시작/기준일 및 원결제 스냅샷은 유지. 아직 변경 SQL 실행 안 함.
- 예상: T 이후 자동스케줄러가 TEST Basic5900 갱신1건 생성, Basic권한과400지급, 기존Pro1000 사용기한 종료. 기존free_trial400+topup4400 보존 시 최종유효5200. 기존 기준일을 유지하므로 다음기간 종료는 정상 계산 시10-10 00:37:44.944. 이는 기간을 압축한 검증이며 실제 한 달 경과 검증이 아님.
- API/호스트 재시작 불필요. T 이후 자동청구가 가능하므로 운영DB 날짜조정은 사용자 확인 후 명령 제공. 결제발생 후에는 날짜만 원복해 취소된 것으로 처리하지 않는다. 다음 검증은 이 조정안에 대한 사용자 결정이며 미승인 상태.

### A06 조기 갱신 날짜조정 승인

- 사용자가 다른 회원 영향에 대한 설명을 받은 뒤 `응 조정해`로 대상 세 건의 날짜조정을 승인했다. 서버 명령 직접 실행 원칙은 유지한다.
- 제공 명령은 운영 Admin DB에서 단일 트랜잭션, lock_timeout3초/statement_timeout15초, 정확한 회원/구독/이용권/지급 ID 및 기존 날짜·상품·잔액 조건, UPDATE 각1건 검증을 사용한다. 실패하면 ON_ERROR_STOP으로 종료되어 미커밋 변경이 롤백된다. 정상 COMMIT 이후 T=실행시각+5분부터 자동 TEST 갱신 가능.
- 기존 크레딧 benefit_period_end는 변경 전 출력하여 보존한다. 재실행은 기존 종료일 조건 불일치로 차단한다. API 재시작/다른회원 변경/원결제 수정 없음. 실행 결과 아직 미수신이며 다음은 출력의 COMMIT 및 새 적용시각 확인이다.

### A06 조기 갱신 날짜조정 — 사용자 COMMIT 확인

- 사용자 실행 결과 BEGIN/SET3건/NOTICE/DO/SELECT/COMMIT 확인. 원래 종료 및 credit benefit_period_end는 모두2026-10-10 00:37:44.944+09.
- 새 경계 T=`2026-09-10 01:00:39.613512+09`. 구독89ba75e8-111b-4935-a131-069eddc4e3b4의 current_period_end/next_billing_at/scheduled_change_effective_at 일치, 현재Pro월간 및 예약Basic5900 유지. 제공 DO의 각1건 조건을 통과해 연결 이용권/구독크레딧의 종료시각도 함께 커밋됨.
- 갱신 결제 성공이나 Basic 지급 완료는 아직 확인 전. 다음은01:02 KST 이후 고객 마이페이지/결제내역 새로고침으로 Basic월간/예약해소/신규5900 주문/유효5200 확인 후 DB/Toss 대조. 미반영이면 상태를 먼저 읽고 날짜조정 명령을 반복하지 않는다.

### A06 자동 갱신 — 고객 화면 결과

- 사용자 고객화면: Basic월간5900/월400, 자동갱신 중, 현재이용기간종료/다음결제2026-10-10 00:37. 예약표시 해소 및 유효잔액5200 확인.
- 신규 결제내역: 주문 `renewal-mq8vZp1uBPcFrXET_pcFYPpJ`, 구독갱신Basic월간/카드5900/결제완료/환불없음。주문·결제2026-09-10 01:01(화면 분 단위).
- 조정한 경계01:00:39 이후 고객표시는 예상과 일치. 신규갱신 주문·지급/원장 건수·기존1000 만료 및 Toss 외부 대조는 아직 미확인. 총잔액만으로 지급 멱등성 완료를 주장하지 않는다.
- 다음: m2-db READ ONLY로 동일 구독/신규주문, 연결지급·원장 및 유효잔액 확인. 이어 Toss의 해당5900 거래 확인. 추가 날짜변경/재시작 없음.

### A06 갱신 DB 部分確認・原帳조회訂正

- 사용자01:04:07.961563 KST READ ONLY 결과: Basic월간active5900/월400, 현재시작09-10 01:00:39.613, 종료/다음청구10-10 00:37:44.944, 예약필드NULL.
- 신규주문7c6816eb-2dce-4ca8-a879-6e8718792252 / renewal-mq8vZp1uBPcFrXET_pcFYPpJ paid/succeeded5900, paid_at01:01:01.236. 구독 연결 주문은 기존최초1건+갱신1건.
- 신규지급a28c9d03-89ef-4af7-b29c-62884f3288f5 active400/잔여400, 지급01:00:39.613, 만료10-10 00:37:44.944, 같은access연결, payment_order_id NULL.
- 기존Pro지급6ffd88b2-3ec7-4322-98c5-f8bf65f4990d active/잔여1000이나 expires_at01:00:39.613512 경과. 사용가능 쿼리는 expires_at도 검사하므로 상태만으로 가용1000이라고 판단하면 안 된다. JS 밀리초 경계와 수동조정 마이크로초 차이는 만료상태 정리 조사 후보이며 미확정.
- assistant SQL 오류: public.credit_ledger는 존재하지 않음. 원본 entity 확인 결과 public.credit_ledger_entries가 정확함. 앞 SELECT 증거는 유효하지만 원장/합계 조회는 실행되지 않음. READ ONLY 세션 종료로 변경 없음. 다음은 정확한 원장테이블로 미완료 조회 및 유효잔액 대조; 날짜재조정 안 함.

### A06 갱신 원장 및 유효잔액 대조

- 사용자01:05:00.190168+09 READ ONLY/ROLLBACK 확인. 신규원장3f1bf7fc-b7a4-4482-8618-de56cb2ffbe7, grant+400/balance400, 참조monthly:87de6afb-e741-4dac-8762-2f0bec1b697f:2026-09-09T16:00:39.613Z, 생성01:02:00.036288. 기존최초+1000 원장1건과 신규+400 원장1건 확인. 유효free_trial400+subscription400+topup4400=5200.
- 원본 MonthlyCreditGrantService가 월별 지급에 paymentOrderId:null 및 monthly 참조를 사용하므로 이번 신규지급의 주문ID NULL은 코드 경로와 일치. 관찰한1회 지급이며 강제중복/동시성 검증은 아님.
- 기존1000 active 잔존 설명: 원본 만료정리는 expires_at <= periodStart 비교. assistant 조정SQL은 마이크로초 .613512를 넣었으나 JS Date를 거친 신규기간은 .613으로 정밀도가 낮아져 기존만료가 비교경계보다0.512ms 늦다. 이번 테스트 날짜설정이 만든 경계 불일치로 설명되며 정상기간 만료처리 완료로 간주하지 않는다. 다음 날짜조정은 밀리초 정밀도로 맞춰야 한다. 기존1000은 가용잔액에서 제외되었고 자동 재조정은 하지 않음.
- 다음: Toss 관리자 TEST 거래에서 renewal-mq8vZp1uBPcFrXET_pcFYPpJ / Basic월간5900 /09-10 01:01 확인. 만료상태 정리 및 정상경계 재검증은 별도 남김.

### A06 Toss 갱신 승인 대조

- 사용자 Toss 관리자 표: fc8d0_renewal-mq8vZp1uBPcFrXET_pcFYPpJ / 완료 /5900원/신용·체크카드/Basic월간. 표시시각2026-09-10 01:01:00. 조회시각 및 별도 API GET 증거로 확대하지 않는다.
- 예약확정→취소→재예약 및 기간압축 후 자동갱신1건은 고객/DB/Toss관리자 대조 완료. Basic active, 신규5900 paid/succeeded, 월별400 지급원장1건, 유효5200. 강제중복/동시성/실패재시도와 정상 한달경과 검증은 별도다.
- 다음은 Admin 회원 상세의 현재Basic/5200/이번갱신결제5900 표시 확인. 기존Pro1000의 active 잔존은 assistant 날짜설정 정밀도 문제로 별도 정리/재검증 대기하며 재청구나 갱신재실행하지 않는다.

### A06 Admin 확인 및 만료 표시 결함

- 사용자 Admin: Basic월간/활성, 종료·다음청구10-10 00:37, 해지예약/예약변경/환불없음, 유효5200=무료400+구독400+추가4400 확인. 결제 표는 이번 인용에 없어 별도 미확인.
- 수동 조정 가능 지급분 표에서 기존Pro1000/잔여1000/유효기간09-10이 사용 가능으로 표시됨. 총액에는 제외되어 실제 가용잔액과 행 상태표시 불일치.
- 원본 Admin 작업트리 clean 확인. member-detail.component.html이 creditStatusLabel(grant.status)만 전달하고 함수가 active를 사용 가능으로 매핑하여 expiresAt을 고려하지 않는 원인 확인. 이번 수동조정 정밀도 이슈와 구분해 표시 결함으로 기록. 코드수정/배포/DB정리 아직 없음.
- 다음: Admin 결제 표의 갱신5900 확인과 만료표시 수정·테스트, 기존기간정리 후 정상정밀도 경계 검증. 다른 회원/서비스 조작 없음.

### A06 Admin 결제 확인 및 만료 표시 로컬 수정

- 사용자 Admin 결제표: 갱신Basic월간5900/누적환불0/잔액5900/저장Toss DONE/결제완료/09-10 01:01. 최초Pro10900 결제는 유지. 기간압축 자동갱신1건 고객/Admin/DB/Toss관리자 대조 완료.
- 원본 Admin clean 확인 후 member-detail.component.ts/html/spec.ts 세 파일만 수정. 수동조정 지급표의 active 행은 expiresAt <= Date.now()일 때 만료 표시. 회수·소진 등의 상태는 보존. DB 상태/잔액은 변경하지 않는다.
- 테스트 우선: 렌더링 회귀테스트에서 만료 전/정각/경과/무기한/회수 비교. 수정 전 만료정각·경과 두 assertion 실패 확인(20성공/1실패), 수정 후 회원상세21테스트 통과. Node22.22.3/ChromeHeadless. 최초 sandbox의 Karma 포트 제한 후 승인된 로컬 테스트 실행, 운영/개발 서버·DB 접근 없음. git diff --check 통과.
- Admin 앱수정 미커밋/미푸시/미배포. 운영 표시에는 아직 반영되지 않음. 브라우저 시각을 이용한 조회/화면갱신 시 표시이며 서버 유효잔액 계산은 그대로다.
- 다음 검증: 기존Pro1000 DB 만료상태 정리 및 정상 밀리초 경계 재검증. 표시수정은 배포 전 다른 세션과 대상/영향 조율 필요. 갱신/환불 완료건 재실행 없음.

### A06 기존 Pro 만료 상태 정리 안내

- 사용자 다음단계 요청에 따라 기간압축 테스트로 남은 지급6ffd88b2-3ec7-4322-98c5-f8bf65f4990d 한 건을 정리하는 명령 제공. 회원/구독/이용권/원주문 ID, active/1000, 기존만료01:00:39.613512, 현재시각 경과, 환불잠금없음 조건 검증.
- 원본 expireActiveForAccess와 동일하게 status=expired/updated_at만 변경. 잔여1000/만료시각/원장은 이력 보존, 청구/현재구독/다른지급은 변경하지 않는다. 가용잔액은 이미 제외되어5200 유지 예상.
- UPDATE 정확1건 아니면 예외로 전체롤백. 실행 결과 미수신. 다음은 사용자 COMMIT 및 상태/출처별잔액 확인, 이후 Admin 새로고침의 만료 표시 대조. 이 수동정리는 자동 만료경계 재검증 완료가 아니다.

### A06 기존 Pro 만료 상태 정리 완료

- 사용자 BEGIN/SET3건/DO/SELECT/COMMIT 확인. 지급6ffd88b2-3ec7-4322-98c5-f8bf65f4990d status=expired, remaining_credits1000 및 expires_at2026-09-10 01:00:39.613512+09 보존. 실행시각은 출력에 없어 추정하지 않음.
- 유효free_trial400+subscription400+topup4400=5200 유지. 이력상잔여1000은 가용잔액이 아니다. 단일 지급 상태 수동정리 완료이며 자동만료경계 재검증과 구분.
- 다음: Admin 회원상세 새로고침 후09-10 00:37 지급1000 행이 만료 표시인지 확인. 이번 변화는 DB정리 결과이며 미배포 Admin 표시수정의 운영검증이 아니다. 정상 밀리초 경계 자동만료/나머지 PG 예외검증은 이후 진행.

### A06 만료 정리 후 Admin 표 확인

- 사용자 Admin 크레딧표: 새Basic400/사용0/잔여400/10-10 00:37까지/사용가능, 기존Pro1000/사용0/잔여1000/09-10 01:00까지/만료 확인. 이번 표는 연결결제 열이 있는 상세표이며 수동조정 지급표와 구분. DB expired 정리 후 화면 반영 확인이며 미배포 코드 검증은 아니다.
- A06 기간압축 갱신 정상흐름 및 정리 완료. 정상정밀도 자동만료·예외/강제중복은 남음. 다음은 기존 주문 관련 payment_webhook_inbox 저장/처리상태를 운영Admin DB READ ONLY로 확인. 신규결제/이벤트재전송은 아직 안 함.

### A07 웹훅 최초 DB 대조

- 사용자 READ ONLY checked_at2026-09-10 01:14:55.289585+09/ROLLBACK 확인. 해당회원 주문과 연결된 PAYMENT_STATUS_CHANGED 2건 조회.
- 월간환불sub_85c03506dbd04d979f808b1c418986ed: inbox60fa8baf-ea89-4e8a-80f5-1870f3574f5b processed/provider CANCELED, 주문be117e3a-4e30-4dc8-affe-b0efac676487 연결. 웹훅 실제저장/처리1건 증거.
- 연간환불upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375: inbox778c9ef6-554a-43c2-8316-fac26393491f manual_review/provider CANCELED, 주문2851be09-ace0-4f12-b4d1-493de2dcdbfb 연결. 완료환불 상태와 웹훅 검토상태는 구분. 원인/발생시점 미확인.
- 이 조회에서 추가충전/신규갱신 이벤트는 보이지 않았으며 모든웹훅 미수신이나 설정실패로 단정하지 않는다. 중복전달/재시도 멱등성은 미검증.
- 다음: 두 inbox의 last_error_code/수신·처리시각/재시도정보 READ ONLY 비교. 완료환불 재실행, 웹훅 강제처리, DB 상태수정 없음.

### A07 연간 환불 웹훅 검토 사유 조사

- 사용자 DB: 연간 inbox778c9ef6-554a-43c2-8316-fac26393491f manual_review/WEBHOOK_ORDER_PURPOSE_MISMATCH/retry0, 수신09-08 16:34:21.615019, 처리시작16:35:00.022, processed/updated16:35:00.061, next_retry NULL. processed_at 존재만으로 성공이라고 보지 않는다.
- 월간 inbox60fa8baf-ea89-4e8a-80f5-1870f3574f5b processed/오류없음/retry0, 수신09-10 00:29:17.288062, 처리00:30:00.018→00:30:00.509, next_retry NULL. 사용자 Toss표 전송성공 PAYMENT_STATUS_CHANGED00:29:21/BILLING_DELETED00:30:00과 별도 증거로 기록. BILLING_DELETED 앱처리는 아직 미확인.
- 원본 API HEAD2710301, 기존 미추적 docker-compose.pg-local.yml 보존. subscription-plan-changes.service.ts는 upgrade를 paymentType one_time으로 생성. payment-webhook.service.ts는 subscription_upgrade를 허용목적에 포함하지만 paymentType recurring/billing 조건을 공통 요구한다. 코드간 계약 불일치 발견, 실제 DB payment_type/key_set 확인이 다음 단계.
- 환불 money/internal 완료 증거는 유지. 웹훅만 자동분류에 실패했으며 원주문 변경/환불재실행/강제웹훅 처리 없음. 다음: 대상 연간/월간 주문 payment_type/key_set READ ONLY 대조 후 회귀테스트와 최소수정.

### A07 상향 주문 웹훅 불일치 — 원인 확인 및 로컬 수정

- 사용자 DB 확인: 월간최초 recurring/billing, 연간상향 subscription_upgrade/one_time/billing, 두 주문 모두paid/full. 정상 상향주문 생성계약과 웹훅검증이 불일치한 결함 확정.
- API payment-webhook.service.ts 및 payment-reconciliation.service.ts에서 상향은one_time, 최초/갱신은recurring/billing으로 검증하도록 수정. 웹훅 Toss응답 type은 결제횟수 대신 keySet에 맞춰 BILLING/NORMAL 판별. 기존 키셋/금액/주문/결제키 대조 유지.
- 테스트 우선: 상향 DONE/CANCELED 웹훅2건이 수정 전 실패, 실제one_time으로 고친 reconciliation fixture도 수정 전 실패 확인. 수정 후 잘못된 키셋/최초·갱신one_time 거부 포함 관련3suite166테스트 통과. API nest build 및 git diff --check 통과.
- API 변경4파일(서비스2/테스트2), 미추적docker-compose.pg-local.yml 보존. 운영DB/webhook manual_review/완료환불 변경 없음. 미커밋/미푸시/미배포. Admin 만료표시3파일도 별도 미배포 유지.
- 다음: BILLING_DELETED 저장·처리 READ ONLY 대조 및 수정 배포/재처리 절차 준비. 배포시 API재시작 영향과 다른 세션 조율 필요. 기존 연간환불 재실행 금지. manual_review 복구는 수정 배포만으로 완료됐다고 판단하지 않는다.

### A07 BILLING_DELETED 저장·처리 확인

- 사용자 READ ONLY/ROLLBACK: inbox9a0346a4-0472-4c94-a33a-9eb3d30850a3 BILLING_DELETED processed/오류없음/retry0, 수신2026-09-10 00:29:56.133354+09, 처리00:30:00.535, next_retry NULL.
- 시간범위 조회로 찾은 결과이므로 월간환불 회원의 이벤트라고 아직 확정하지 않음. 다음: 해당inbox와 월간종료구독27308873-d541-44cb-aeb5-4579635f71df의 fingerprint 일치 여부만 boolean 조회, 실제 키/지문 출력 없음. 환불재실행/키삭제/웹훅재처리 없음.

### A07 BILLING_DELETED 대상 구독 일치

- 사용자 결과: subscription27308873-d541-44cb-aeb5-4579635f71df canceled, billing_key_removal_status succeeded, matches_billing_auth_history=t. inbox9a0346a4-0472-4c94-a33a-9eb3d30850a3의 지문이 해당구독 카드등록 이력과 일치. 키/지문 값 출력 없음. 이번 붙여넣기에 ROLLBACK 줄은 없으며 앞서 제공한 명령은 READ ONLY.
- 월간환불의 PAYMENT_STATUS_CHANGED processed 및 BILLING_DELETED processed/대상일치 확인 완료. 전달성공/내부처리/대상연결 증거를 확보했으며 강제중복전달/재시도 검증은 아직 미완료.
- 다음: Toss 전송기록에서09-10 00:29:21 PAYMENT_STATUS_CHANGED 상세를 열어 재전송 기능 유무/응답상태 확인. 이 단계는 열람만, 연간manual_review 이벤트 및 완료환불 재실행 안 함. 중복전송 실행 전 정상처리 월간inbox 기준값을 사용한다.

### A07 Toss 재전송 UI 미제공 및 대체 검증 준비

- 사용자 성공전송 상세는 본문과 닫기만 제공, 재전송버튼 없음. 월간주문 CANCELED/BILLING/취소10900/잔액0 확인. 본문에 포함된 secret/결제키/거래키 등은 로그에 저장하지 않는다.
- 대체는 앱 DB에 저장된 월간processed 이벤트의 createdAt/providerEventId/orderNo/paymentKey/status를 그대로 복원하여 기존dedupe_key와 해시일치를 먼저 검증한 뒤 동일 요청2회 전송. 원본코드의 HTTP webhook 경로로 테스트하며 Toss 자체 재전송/외부네트워크 재시도와 구분한다.
- 정상기대는 기존inbox1건/processed/재처리없음. DB 조회는 READ ONLY 연결, HTTP POST는 이벤트수신검증이며 결제취소 API가 아니다. 실행 결과 아직 없으며 새 결제/환불을 요청하지 않는다.

### A07 동일 웹훅 HTTP 중복수신 검증 완료

- 사용자 m4-prod 실행 결과: attempt1/2 모두 HTTP200, inboxCount1/sameInbox true/status processed/retryCount0/processedAtUnchanged true/updatedAtUnchanged true.
- 대상은 정상처리된 월간환불 inbox60fa8baf-ea89-4e8a-80f5-1870f3574f5b. 저장된 동일식별자의 해시일치를 사전검사하고 컨테이너 loopback HTTP에2회전송한 검증. 동일dedupe 이벤트 추가저장/상태변경/재처리 없음 확인.
- 완료범위는 이미processed인 동일전송식별자의 순차중복2회. Toss 외부재전송/다른전송ID/동시요청/실패후재시도/지급함수직접멱등성은 아직 미검증. 연간manual_review 및 완료환불 변경 없음.
- 다음 검증: 다른 전송식별자로 같은 월간 취소사실을 재수신했을 때 재조회가 기존환불/현재구독/원장에 미치는 영향을 코드로 확인하고 시험 설계. API 수정 배포/연간manual_review 복구는 다른 세션 재시작 조율 후 별도로 진행.

### A07 다른 전송 ID 검증 — 사전 상태 준비

- 사용자 다음 검증 진행 동의. 대상은 정상처리된 월간취소 이벤트/주문be117e3a-4e30-4dc8-affe-b0efac676487, 환불c7aa3c09-6a9c-48a2-b3e9-4aa1fd9ae16a. 새 전송ID는 새inbox를 만들므로 이전 동일ID 중복차단과 구분.
- 코드 확인: 취소 재조회 경로는 observeExternalCancellation을 통해 주문providerStatus/externalCancelStatus/detectedAt 및 업데이트시각을 갱신한다. 주문 모든필드 불변을 기대하면 안 됨. 환불금액/구독/크레딧을 직접 변경하거나 취소 API를 호출하는 경로는 아니다.
- 다음 사용자 단계는 m2-db READ ONLY 기준값 확보: 환불completed/10900, 주문full/환불10900/잔액0, 대상원장 건수/순합, 현재Basic 및 유효5200. 이어 새전송ID로1회 수신 후 동일항목 대조 예정. 아직 새로운 이벤트 전송 안 함.

### A07 다른 전송 ID 검증 — 기준값 확인 및 전송 안내

- 사용자 READ ONLY 결과 checked_at2026-09-10 01:24:35.339627+09/ROLLBACK. 월간환불c7aa3c09-6a9c-48a2-b3e9-4aa1fd9ae16a money/internal completed10900, 주문be117e3a-4e30-4dc8-affe-b0efac676487 paid/succeeded/full/누적10900/잔액0. 대상지급 원장2건/순합0.
- 현재구독89ba75e8-111b-4935-a131-069eddc4e3b4 active Basic월간/다음청구10-10 00:37:44.944. 유효free_trial400+subscription400+topup4400=5200.
- 다음 제공 명령은 저장된 월간processed 이벤트를 복원, 원래해시 일치 검증 후 전송ID `clipper-pg-a07-monthly-cancel-redelivery-20260910-01`로1회 loopback HTTP POST. 해당 전송ID가 이미 있으면 중단하여 실수 재실행 방지. 실제키/지문/본문은 출력하지 않음.
- 새inbox1건 수신 후 매분worker 처리예정. HTTP200만으로 처리완료 판정하지 않고 후속READ ONLY로 위기준값 유지 확인. 취소 API 호출/원환불 재실행 없음. 아직 전송 결과 미수신.

### A07 다른 전송 ID — 수신 확인

- 사용자 m4-prod 결과: transmissionId clipper-pg-a07-monthly-cancel-redelivery-20260910-01 / HTTP200 / inboxCount1.
- 신규inbox b490edc9-e55d-431d-a282-673a6e93c95e received/retry0/processed_at NULL, received_at2026-09-09T16:25:14.273Z(09-10 01:25:14.273 KST).
- 수신만 완료, 처리/불변검증은 아직 미완료. 다음은01:27 KST 이후 m2-db READ ONLY로 신규inbox 상태 및 01:24:35 기준값(환불10900완료/원장2·순합0/현재Basic·유효5200) 대조. 이벤트 재전송/환불재실행 안 함.

### A07 다른 전송 ID — 처리 및 불변 대조 완료

- 사용자 READ ONLY 두 조회/ROLLBACK: 2026-09-10 01:26:10.527765+09 및01:27:46.319827+09. 신규inbox b490edc9-e55d-431d-a282-673a6e93c95e processed/오류없음/retry0/next_retry NULL, processed_at01:26:00.980 동일.
- 두 조회 모두 기준값 유지: 월간환불 money/internal completed10900, 원주문paid/succeeded/full/누적환불10900/잔액0, 대상지급원장2건/순합0, 현재Basic active/다음청구10-10 00:37:44.944, 유효free_trial400+subscription400+topup4400=5200.
- 완료범위: 앱loopback에서 다른전송ID로 동일월간 취소사실1회 수신 후 자동재조회 처리, 환불·대상회수원장·현재구독·유효잔액 불변. 01:27 재조회에서도 추가처리 없음. 동시성/실패후재시도/제공자 외부재전송 및 지급함수직접멱등성은 미검증.
- 다음: 실패재시도 시험의 격리 가능한 방법을 검토. 전역PG키/네트워크/운영서비스를 끊는 방식은 사용하지 않는다. API/Admin 수정 미배포와 연간manual_review 복구는 별도 남음. 이번 SQL은 재실행 불필요.

### A08 주문 미도착 웹훅 재시도 시험 준비

- 원본 확인: 존재하지 않는 orderNo는 provider 조회 이전 WEBHOOK_ORDER_NOT_READY로 종료. 재시도 지연1/4/16/64분 후 소진시WEBHOOK_RETRY_EXHAUSTED/manual_review. 실제Toss 장애 후 회복 검증과 구분.
- 시험 전용 orderNo pg_retry_probe_20260910_a08, transmissionId clipper-pg-a08-order-not-ready-20260910-01 사용. 운영Admin DB에서 해당주문/전송ID 부재를 확인한 뒤 합성 PAYMENT_STATUS_CHANGED 1건을 API loopback에 접수하는 명령 제공. 실제주문/회원/결제키 사용 안 함, 주문 생성 안 함.
- 영향은 테스트용 inbox1건 및 예정된 조회 재시도에 한정. 현재회원 구독/크레딧/환불 및 전역설정 변경 없음. 처리한계 도달시 수동검토 행이 남음을 안내하며 임의삭제하지 않는다.
- 다음: 접수 결과 및 첫실패 retry1/다음재시도, 이후 자동retry2/다음간격4분 확인. 아직 접수 결과 미수신. 재시도 성공복구/동시성/결제실패 검증 완료로 확대하지 않는다.

### A08 합성 이벤트 접수 확인

- 사용자 HTTP200/inboxCount1. 신규inbox41151647-ec2b-40ec-8853-7e55bce8ef40 received/retry0/next_retry NULL, received_at2026-09-09T16:29:13.094Z(09-10 01:29:13.094 KST).
- 다음:01:30:10 KST 이후 READ ONLY로 status/last_error_code/retry_count/updated_at/next_retry_at 조회, 첫실패와1분 재시도간격 확인. 처리시각 경계에 따라 실제실행은 다음 분으로 늦어질 수 있어 기록값을 기준으로 다음조회 안내. 수신성공만으로 재시도 검증 완료 아님.

### A08 첫 실패 및 재시도 예약 확인

- 사용자 READ ONLY/ROLLBACK, checked_at2026-09-10 01:30:17.387764+09. inbox41151647-ec2b-40ec-8853-7e55bce8ef40 retryable_failed/WEBHOOK_ORDER_NOT_READY/retry1/payment_order_id NULL.
- 수신01:29:13.094032, updated01:30:00.038, next_retry01:31:00.038 KST. scheduled_delay 정확1분. 첫실패 저장·재시도 예약까지 완료, 실제재시도 실행은 아직 미확인.
- 다음:01:32:10 이후 같은READ ONLY 조회로 retry2/다음간격4분 확인. 매분스케줄러의 조회시각이 next_retry보다 빠르면01:31분에 대상이 안 될 수 있으므로01:32분 조회로 여유 확보. 새이벤트/주문 생성·날짜수정 없음.

### A08 첫 자동 재시도 실행 및 간격 증가 확인

- 사용자 READ ONLY/ROLLBACK, checked_at2026-09-10 01:32:18.427907+09. 동일inbox41151647-ec2b-40ec-8853-7e55bce8ef40 retryable_failed/WEBHOOK_ORDER_NOT_READY/retry2/payment_order_id NULL.
- updated01:32:00.042, next_retry01:36:00.042 KST, scheduled_delay4분. 최초실패(retry1) 이후 실제 자동재시도1회가 실행됐고 다음간격1분→4분 증가 확인. retry2는 자동재시도2회 성공을 뜻하지 않음.
- 다음은01:37:10 이후 동일READ ONLY로 retry3/16분 간격 확인. 최종소진manual_review까지 자연실행은 계속되며 아직 성공복구·최종소진 검증 완료 아님. 주문생성/PG호출/이벤트추가전송/스케줄변경 안 함.

### A08 두 번째 자동 재시도 및 16분 간격 확인

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 01:37:07.480638+09. inbox41151647-ec2b-40ec-8853-7e55bce8ef40 retryable_failed/WEBHOOK_ORDER_NOT_READY/retry3/payment_order_id NULL.
- updated01:37:00.055, next_retry01:53:00.055 KST, scheduled_delay16분. 최초실패+자동재시도2회 확인, 예약간격1→4→16분 관찰 완료.
- 다음조회01:54:10 KST 이후 동일READ ONLY로 retry4/64분 예약 확인. 그후 next_retry_at을 기준으로 최종소진manual_review/WEBHOOK_RETRY_EXHAUSTED/next_retry NULL 대조가 남음. 자동관찰/알림은 설정하지 않았으며 서버시간·재시도시각 조작 없음.

### A09 현재 TEST 결제창의 가상계좌 미제공 확인

- 재시도 대기 중 사용자 추가충전 결제창 확인: 퀵계좌이체/신용체크카드/토스페이/페이코/카카오페이/네이버페이만 표시. 가상계좌·무통장입금 없음.
- 현재 공용TEST Widget 설정에서는 가상계좌 입금대기/입금/만료 E2E 제외 사유 확보. 제공자 전체 또는 향후전용키에서 불가능하다는 뜻은 아님. 결제확정/계좌발급 증거 없음. DEPOSIT_CALLBACK 처리 기능 검증완료로 기록하지 않는다.
- 다음: 결제창 닫기 후 현재Basic 구독 요금제변경의 연간 비교표를 열람하여 실제 제공 조건 확인. 결제/예약확정 없이 견적표만 확인. A08 재시도 조회는01:54:10 이후 유지.

### A10 Basic월간 → Business월간 즉시변경 견적 화면

- 연간비교표 요청 후 사용자가 실제 제공한 것은 Business월간 즉시변경 최종견적. 현재Basic월간, 새가격29900, 기간공제5894/크레딧공제5900 중 작은5894 적용, 즉시결제24006(29900-5894), 첫달4000 표시. 계산 산술 및 작은공제 선택은 일치. 견적생성시각/정확한기간분모가 없어 시간비례금액 자체를 독립 검산한 것은 아님.
- 안내: 결제완료부터 새1개월, 기존구독잔여 회수/4000신규지급, 무료체험·추가충전 유지, 월별4000/각월말만료, 다음매월29900자동결제 및 취소경로. 필수동의에 즉시변경24006/매월29900 명시.
- 결제 또는 동의체크 실행 증거 없음. 새 결제 없이 미동의버튼 비활성 확인→모달닫기→Basic/5200 유지 확인을 다음단계로 안내. 기대상 현재구독400회수+신규4000이라 확정결제시 총8800이지만 아직 결제실행 안 함. A08 재시도01:54:10 조회 예정 유지.

### A10 즉시변경 견적 취소·미동의 차단 확인

- 직전 두 확인 요청(필수동의 미체크 결제버튼 비활성, 모달닫기 후Basic월간/5200 유지)에 사용자 `확인했어` 응답. 고객 UI 확인으로 기록, 실제결제/PG실패/DB불변 직접대조 완료로 확대하지 않음.
- 다음: 마이페이지 변경 가능한 요금제 보기에서 연간탭의 상품별가격/변경시점/버튼문구 확인. 견적열람 단계이며 결제/예약확정 없음. A08 재시도는01:54:10 이후 동일조회 예정 유지.

### A10 Basic월간에서 연간 비교표 확인

- 사용자 연간탭: Basic58800/Pro82800/Business234000, 모두 차액결제후즉시·차액확인 표시. 현재Basic월간에서 월→연 동급/상위변경의 비교표 확인. 실제견적/동의/결제완료 증거로 확대하지 않음.
- 다음: Basic연간 행의 차액확인만 열어 공제액/즉시결제액/새기간/월400 지급·유효기간/다음연간청구/필수동의 문구 확인. 결제확정 안 함. A08 조회01:54:10 이후 유지.

### A10 Basic 연간 최종 견적 확인 및 검증 대상 준비

- 사용자견적: 현재Basic월간, Basic연간58800, 기간공제5894/크레딧공제5900 중5894 적용, 지금52906. 첫달400, 결제완료부터12개월, 기존구독잔여회수/첫달400재지급, 무료·추가충전유지, 이후월400/각월종료까지, 이후매년58800 및 필수동의 표시.
- 산술·최종안내 확인. 시각비례 공제액은 견적시각 미제공으로 독립검산 미완료. 다음은 미동의버튼 차단 확인 후 TEST 연간변경1회로 연간월별지급/연→월금지조합 검증 대상 마련. 과거Pro연간환불 반복 목적 아님.
- 예상: 현재Basic월간400회수/새연간첫달400지급으로 합계5200 유지, 신규차액주문1건, 새12개월구독/다음연간청구. 실제결제는 아직 미수신. 시각경과에 따라 최종견적 변동 가능, 변경결과의 실제금액으로 대조한다. A08 01:54:10 이후 재시도조회 유지. 배포/DB날짜조정은 이 단계에 포함하지 않는다.

### A10 Basic 연간 변경 — 고객 완료 화면

- 사용자 성공안내: 요금제 변경과 차액결제 완료. 새로고침 후Basic/정기구독연간/활성/자동갱신중/유효5200. 상품Basic연간58800·12개월마다·월400, 종료/다음결제2027-09-10 01:43(분단위) 확인.
- 실제차액 결제금액/주문번호 및 지급교체 DB는 아직 미확인. 앞선52906 견적을 확정결제금액으로 간주하지 않는다. 이번 응답에 동의미체크 비활성 확인은 명시되지 않아 별도미확인 유지.
- 다음: 고객 결제내역에서 새Basic연간 상향차액 주문번호/실제금액/결제상태 확보 후 DB/Toss 대조. 현재구독/잔액 보존, 추가결제/환불 없음. A08 retry3 이후01:54:10 조회는 별도로 유지.

### A10 Basic 연간 실제 차액 주문 확인

- 사용자 고객결제내역: upgrade_9e8f2c700ef10d20c59dafe8f7788b003d3003d5394141556f6c1c9a / 요금제상향Basic연간/카드52906/결제완료/환불없음, 생성09-10 01:42·결제01:43. 견적52906과 실제금액 일치.
- 다음: 해당주문으로 연결구독/이용권/기존월간400 및 새연간400 지급·원장, next_credit_grant_at READ ONLY 조회. 기존Pro연간환불 주문과 구분. 현재 고객5200, 실제월별지급은 아직 검증 전.

### A10 Basic 연간 변경 DB 대조

- 사용자 조회2026-09-10 01:47:37.278141+09. 주문21a547f3-3f79-437d-8530-dcba03bba8fa paid/succeeded52906/refund none, 기존구독89ba75e8-111b-4935-a131-069eddc4e3b4 Basic연간active58800/월400, 기간09-10 01:43:21→2027-09-10 01:43:21/다음청구종료동일.
- 기존access87de6afb-e741-4dac-8762-2f0bec1b697f replaced/다음지급NULL. 새access f34fc47d-72fd-4765-9973-d5dd94e7ed87 active/새연간기간, next_credit_grant_at2026-10-10 01:43:21.
- 월간지급a28c9d03-89ef-4af7-b29c-62884f3288f5 revoked/0, payment_adjustment -400원장1건/balance0, reference plan-change:새주문:기존지급. 새지급d2b7017e-3662-4de3-b2cb-ef678c872a68 active400/잔여400, 새access/주문연결, 만료10-10 01:43:21, grant+400원장1건. 두원장 created_at01:43:22.073763 동일.
- 이전수동정리Pro1000 expired 유지. 이번 출력 끝에ROLLBACK 줄은 없으며 제공명령은READ ONLY. 현재까지 고객/DB 변경결과 일치, 실제다음월400지급·Toss/Admin 최종대조는 미완료.
- 다음: Toss관리자 TEST의01:43 Basic연간52906/주문upgrade_9e8f2c700ef10d20c59dafe8f7788b003d3003d5394141556f6c1c9a 완료확인. A08 01:54:10 조회도 유지. 연간결제를 반복하지 않는다.

### A10 Basic 연간 Toss 승인 확인

- 사용자 Toss표: fc8d0_upgrade_9e8f2c700ef10d20c59dafe8f7788b003d3003d5394141556f6c1c9a /완료/52906/신용·체크카드/Basic연간/2026-09-10 01:43:21. 고객/DB의실제차액과일치. API GET 직접대조는 아님.
- 다음: 고객마이페이지 변경가능요금제보기→월간탭에서 현재연간→월간 금지표시/변경버튼 비활성 또는 미제공 확인. 결제/예약/해지 실행 안 함. Admin 새연간표시와 실제월별지급검증은 남음. A08 retry3의 다음조회01:54:10 유지.

### A10 연간→월간 제한 확인 및 월간 탭 표시 개선

- 사용자 연간구독 요금제변경 화면: 연간탭만 표시, 연간이용중 월간으로 직접변경불가 안내. 월간탭을 보이되 비활성화하는 개선 제안 수용.
- 원본Customer의 다른세션 auth-api.service.ts/spec.ts 미커밋 변경 보존. dashboard.component.html/spec.ts만 수정: 월간버튼 항상표시, 연간구독일때 native disabled, 기존제한안내/선택된연간/변경거부로직 유지.
- 모달은 테스트에서mock되어 template을 직접 렌더링하도록 테스트 보완. 수정전 월간탭부재 assertion 실패 확인, 수정후 대시보드45테스트 통과 및 git diff --check 통과. 연간선택유지/월간클릭차단/견적호출없음 확인. 미커밋/미푸시/미배포.
- 다음: A08 01:54:10이후 retry4/64분 조회, Basic연간 Admin대조 및 월별지급 검증 준비. Customer/Admin/API 수정은 배포조율 전까지 운영반영 안 됨.

### A08 64분 재시도 예약 확인

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 01:55:40.338416+09. inbox41151647-ec2b-40ec-8853-7e55bce8ef40 retryable_failed/WEBHOOK_ORDER_NOT_READY/retry4/payment_order_id NULL.
- updated01:54:00.048, next_retry02:58:00.048 KST, scheduled_delay64분. 예약간격1/4/16/64분 확인. retry4는 최초실패와자동재시도3회의 결과, 최종소진은 아직 미확인.
- 다음 최종조회02:59:10 이후 예상manual_review/WEBHOOK_RETRY_EXHAUSTED/next_retry NULL/retry4 유지. 그전 재전송/시간조정 없이 Basic연간 Admin 표시 대조를 병행. 알림/예약작업 생성 안 함.

### A10 Basic 연간 Admin 대조 및 추가 표시 결함

- 사용자 Admin: Basic연간/활성, 현재구독월종료2026-10-10 01:43/다음청구2027-09-10 01:43, 해지예약/변경예약/환불없음. 신규400활성/10-10 01:43만료/주문21a547f3연결, 기존월간400잔여0. 유효5200=무료400+구독400+추가4400.
- 원장 기존월간400 payment_adjustment-400/새연간grant+400 각1건, 연간차액52906/DONE/결제완료 확인. Business월간 견적24006은만료됨/결제일없음, 추가400 checkout5900은결제준비/결제일없음이며 승인완료로 오인하지 않는다.
- 추가표시결함: 자동요금제교체 회수를 수동회수로 표시(API members.service의 refundCaseId없는revoked를 모두admin으로 분류). 환불회수 원장 유형 빈칸(Admin AccountCreditLedgerEntry와ledgerTypeLabel에 payment_refund_revoke 누락). 이번 조사에서 원인확인, 추가코드수정은 아직 안 함.
- 다른세션의 API/Admin API키 관련 다수미커밋 변경 및 Admin models.ts 수정 확인. 공유models 수정 전 대상/영향 고지 및 최신diff 확인 필요. 기존변경 보존.
- A10 정상 연간전환 고객/Admin/DB/Toss 대조 완료. 다음은 연간 월별400 지급 사전상태·시험방법 준비, 표시결함2건 수정 및 배포조율. A08 최종소진 조회02:59:10 이후 유지.

### A11 연간 월별 지급 시험 사전 조회 안내

- 사용자 다음검증 진행 동의. 현재연간구독89ba75e8-111b-4935-a131-069eddc4e3b4/이용권f34fc47d-72fd-4765-9973-d5dd94e7ed87/첫달지급d2b7017e-3662-4de3-b2cb-ef678c872a68을 대상으로 조회.
- 다음 READ ONLY는 access credit_anchor_at/next_credit_grant_at, grant benefit_period_start/end/expires_at 및 현재구독 next_billing_at 확인. 현재날짜변경 승인이나 실행은 아니며, 결과로 대상/조건/영향을 구체화한다.
- 시험 설계는 연간결제일/연간종료 유지, 월별지급 경계만 단축하여 기존400자동만료+새400지급/총5200/신규결제없음을 검증. 조정시각은date_trunc('milliseconds', ...)로 정밀도일치 필수. A08 최종조회02:59:10 이후 유지.

### A11 연간 월별 지급 기준값 및 조정안

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 01:59:03.439805+09. 구독89ba75e8 active Basic연간, 시작09-10 01:43:21/종료·다음청구2027-09-10 01:43:21. 이용권f34fc47d active/같은기간/credit_anchor09-10 01:43:21/next_credit_grant10-10 01:43:21.
- 지급d2b7017e active400/잔여400, granted_at 및benefit_start09-10 01:43:21, expires_at 및benefit_end10-10 01:43:21(2026년 KST).
- 제안: T=date_trunc('milliseconds',clock_timestamp()+interval '5 minutes'), 이용권next_credit_grant_at 및 해당지급expires_at/benefit_period_end를T로 맞춤. 구독/연간종료/결제일/기준일 변경없음. 자동월별worker가 첫400을expired로 만들고 새400지급, 유효5200/추가청구0 예상. 기존기준일 유지시 새400만료·다음지급은2026-10-10 01:43:21.
- 기간압축은 실제월경과 검증이 아니며 추가지급 이력이 한 건 생긴다. 정확한회원/구독/이용권/지급/기존시각/잔여400 조건검증 후 단일트랜잭션 계획. 이번2건 날짜변경은 사용자 확인 전이며 실행 안 함. 승인 후 명령을 사용자가 실행한다.

### A11 월별 지급 기간압축 승인 및 명령 안내

- 사용자는 운영TEST회원 두건 실제변경/추가지급이력/실패시일시4800 가능성을 안내받고 `진행해봐` 승인. 서버명령 직접실행 원칙 유지.
- 제공SQL은 구독행잠금 및 active Basic연간/기간·다음결제일 검증 후 이용권f34fc47d next_credit_grant_at와 지급d2b7017e expires_at/benefit_period_end만T(실행+5분,밀리초절삭)로변경. 회원/구독/원주문/시각/active·미사용400/환불잠금없음 및 각1건 확인, 불일치전체롤백.
- 시작/기준일/연간종료/다음결제일/다른회원/다른지급 변경없음. 재시작 없음. 실행결과미수신, 다음은COMMIT/T 확인 후 자동만료·새400지급/유효5200/추가결제없음 대조. 이 승인으로 다른날짜조정까지 확대하지 않는다.

### A11 월별 지급 경계 조정 COMMIT 확인

- 사용자 실행 결과 COMMIT. 기존 월경계2026-10-10 01:43:21+09 → T=2026-09-10 02:06:45.238+09. 이용권f34fc47d next_credit_grant_at와 지급d2b7017e expires_at 동일T, 기존잔여400 유지.
- 연간종료 및 next_billing_at2027-09-10 01:43:21+09 유지 확인. 자동지급 결과는 아직 미확인.
- 다음:02:08 이후 m2-db READ ONLY로 해당access 지급/원장, 구독기간, 결제주문, 유효잔액 대조. 예상 기존400 expired/새400 한건/총5200/추가결제없음. 날짜조정 재실행 없음. A08 최종소진은02:59:10 이후 별도조회.

### A11 후속 조회 테이블명 오류 정정

- 사용자02:09:59.54996+09 조회에서 Basic연간active/연간종료·다음결제2027-09-10 01:43:21 유지 확인. 이후 assistant가 잘못 제시한 public.access_grants로 조회 중단. 읽기전용 조회이며 자동지급 결과는 미확인.
- 원본 user-access-grant.entity.ts의 @Entity 및 repository SQL에서 정확한 public.user_access_grants 확인. 수정한 읽기전용 전체조회 재안내. 기간조정 재실행 불필요.

### A11 연간 월별400 자동 지급 DB 검증 통과

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 02:10:51.664671+09. 기존지급d2b7017e expired/잔여400(만료 이력), 새지급c152cdcd-319c-47d7-a5b9-0c2798d000c8 active400/잔여400, 시작02:06:45.238/만료2026-10-10 01:43:21. 새지급 payment_order_id NULL.
- 새grant 원장+400 한건, reference monthly:f34fc47d-72fd-4765-9973-d5dd94e7ed87:2026-09-09T17:06:45.238Z, 생성02:06:59.880848. 밀리초로 맞춘 경계에서 자동만료·지급 확인. 강제 재실행/동시성 시험은 아님.
- Basic연간active, 연간종료·다음청구2027-09-10 01:43:21 유지. access 다음월지급2026-10-10 01:43:21. 결제목록 기존승인10900/5900/52906과 미결제만료견적만 존재, 신규결제 없음. 유효5200=무료400+구독400+추가4400.
- 다음: Admin 회원상세 새로고침 후 기존01:43 지급의 만료/새02:06 지급400 사용가능 및 합계5200 화면 대조. 기간압축으로 확인한 결과이며 실제1개월 경과 전체 검증으로 확대하지 않음. A08 최종소진02:59:10 이후 별도조회 유지.

### A11 Admin 월별 지급 화면 대조 완료

- 사용자 Admin 화면: 09-10 02:06 신규400/잔여400/10-10 01:43만료/사용가능/연결결제없음, 09-10 01:43 기존400/잔여400/09-10 02:06만료/만료/원주문21a547f3 연결. DB와 일치.
- 유효5200=무료체험400+구독400+추가4400 확인. 다음은 고객 /my/credits 새로고침 후 동일 두 지급의 상태·만료시각과 총잔액 확인. A08 소진 조회02:59:10 이후 유지.

### A11 고객 확인 및 크레딧 화면 개선

- 사용자 고객 지급내역에서 신규400 사용가능/10-10 01:43 만료, 기존400 만료/09-10 02:06 확인. 원장02:06 +400 표시로 DB/Admin과 일치. 이번 붙여넣기에 고객 총잔액은 없으므로 새로 확인했다고 기록하지 않는다.
- 사용자 개선 승인에 따라 Customer credits.component.ts/html/scss/spec.ts 및 core/api/models.ts 수정. 지급일시 KST 추가, 지급원장 사유 표시(없는 경우 출처별 일반지급 안내), 연결 지급원장에 결제ID가 있을 때 결제내역 목록 링크, 만료·회수 잔여량의 합계제외 안내 추가. 모바일 날짜 레이아웃 보완.
- 기존 monthly access credit grant를 표시 시 정기구독 월별 크레딧 지급으로 번역. payment_refund_revoke 타입/라벨/필터 추가로 빈 환불회수 유형 수정. 저장된 원장이나 서버/DB 변경 없음. 원장은 페이지 단위 로딩이므로 연결 사유·링크는 불러온 지급원장에서 확인되는 경우만 표시하며 추정하지 않는다.
- 테스트 수정전2실패/11통과 확인 후 수정후13통과(ChromeHeadless), git diff --check 통과. 다른세션 auth 변경 및 기존 dashboard 변경 보존. 로컬수정이며 운영 미배포. 다음은 배포조율 후 실제화면 확인, A08 소진02:59:10 이후 READ ONLY 조회. Admin 별도 환불유형/자동회수 표시 결함은 남음.

## 이번 응답 종료 시 인계 / 바로 다음 검증

현재 TEST회원은 Basic연간active, 다음연간청구2027-09-10 01:43:21, 유효5200(무료400/구독400/추가4400). A04 추가충전환불/A05 월간환불/A06 예약·취소·재예약·기간압축갱신/A10 연간전환/A11 월별400 자동지급 대조 완료. A11 고객 지급상태·원장 확인, 고객 합계 최신 출력은 미수신. 기간압축 검증을 실제 한달 경과나 동시성 검증으로 확대하지 않는다.
A07 동일/다른전송ID 월간취소 재전달 처리 및 환불금액·원장불변 확인. A08 inbox41151647-ec2b-40ec-8853-7e55bce8ef40은 retry4/64분대기, 02:59:10 이후 manual_review/WEBHOOK_RETRY_EXHAUSTED/next_retry NULL READ ONLY 확인 필요. 완료환불 재실행 금지.
로컬 미배포 수정: API 상향주문 웹훅/재조회 분류, Admin 만료표시, Customer 연간중 월간탭 비활성 및 크레딧화면 개선, 아래 Admin 회수표시 수정. 다른세션 변경 보존, commit/push/배포/재시작 없음. 이후 배포 대상·영향을 운영구축 세션과 조율하고 사용자가 서버명령 실행. 실패결제재시도·유예/만료·복구/동시성 등 남은 예외는 계속 검증해야 한다.

### A12 실패·유예 검증 사전 조사

- 사용자 진행동의 후 원본 subscription-renewal.service/retry-policy 및 Infra 문서 조사. 확정실패와 결과불명확 경로가 구분되며 첫실패시 정책의 gracePeriodDays/retryDays를 구독에 스냅샷으로 저장. 날짜간격은 첫실패시각 기준. 정책변경은 공통영향이므로 시험을 위해 변경하지 않는다.
- 운영 제공자의 실패강제 옵션은 이번 조사에서 확인되지 않음. Toss 공식 자동결제/API문서에서도 원하는 승인실패 강제방법은 아직 확보하지 못함. 임의카드/빌링키손상·전역설정변경은 실행하지 않음.
- 다음 m2-db READ ONLY로 subscription_renewal_policies id1의 grace_period_days/retry_days 및 TEST구독89ba75e8 현재 복구필드 조회. 실패주입 방법/대상/영향은 결과와 함께 구체화해야 하며, 실패·복구 실행 완료로 기록하지 않는다.

### A12 정책 실제값 및 공식 실패 재현 방법 확인

- 사용자 READ ONLY/ROLLBACK 2026-09-10 02:37:19.193802+09: grace_period_days3/retry_days[1,2]. 구독89ba75e8 Basic연간active/다음청구2027-09-10 01:43:21, first_payment_failed_at/grace_ends_at/retry_days_snapshot/next_retry_index/retry_at 모두NULL. 실패가 발생한 상태가 아님.
- 공식 https://docs.tosspayments.com/guides/v2/get-started/environment 및 /resources/glossary/http-header 에서 TossPayments-Test-Code 헤더를 통한 TEST키 전용 오류 재현 확인. 라이브키에서는 헤더가 무시되므로 적용 전 TEST키 강제검증 필요. 이전 조사에서 찾지 못했던 방법을 이번에 확인한 것임.
- 현재 HttpTossPaymentsProvider.chargeBillingKey는 이 헤더 전달 기능 없음. Toss API 단독 실패호출만으로는 Clipper의 갱신실패/유예 전체 검증이 되지 않음. 다음은 특정TEST회원/구독/승인요청에 한정한 주입 방법 및 복구·만료 각 시나리오 설계. 전역실패설정·키손상·서버변경·결제호출은 수행하지 않음.

### A12 대상 선택 대기 및 시험 조건 구체화

- 사용자 진행동의 후 실패주입 구조 조사. 정상API의 전역설정에 오류헤더를 넣는 방식은 사용하지 않는다. 특정TEST키·구독·갱신주문을 검증하고 그 요청에만 공식테스트헤더를 적용하는 방법이 필요하다. 현재 실행가능한 서버스크립트는 아직 작성되지 않았으며 실행/배포/재시작 없음.
- 실패→복구 시험: 확정실패 후 past_due/정책스냅샷3일·[1,2]/추가승인·추가지급없음 확인, 실패주입 해제 후 같은구독 재시도성공/정상권한·지급 복구 대조. 실패지속 시험: D+1/D+2 실패, 이후 retry_at NULL, D+3 stopped·이용권종료·추가청구없음 대조. 정책전역값 변경 금지. 기간압축이 필요하면 정확한행/변경전후/복구계획을 제시해야 함.
- 사용자에게 별도TEST회원 ID/이메일 또는 기존Basic연간 계속사용 의사를 비동기 질문. 별도월간시험을 권장하는 이유는 만료시험이 현재계약을 정지시키기 때문. 대상 미정이므로 날짜조정/새결제 명령을 안내하지 않음.
- 로컬 subscription-renewal.service.spec.ts 및 subscription-retry-policy.spec.ts 2suite50통과. 외부PG/운영DB 검증으로 간주하지 않는다. A08은02:59:10이후 소진조회 계속 남음.

### A12 별도 TEST 회원 선택

- 사용자가 가입된 회원9e7035f5-9b99-4ac1-88b5-c654133725f3(가입일2026-09-08 15:20)을 실패·유예 시험 대상으로 제시. 기존Basic연간 회원f47e0e29의 계약은 이번시험 대상에서 제외.
- 다음은 별도회원의 subscriptions/payment_orders/user_access_grants/credit_grants READ ONLY 사전조회. 현재구독/미완료결제/이용권 상태 미확인이므로 신규결제나 기간압축은 아직 안내하지 않는다. 실패주입 스크립트 준비도 미완료이며 실행 전 대상제한·TEST키 검증 필요.

### A12 별도회원 사전상태 확인

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 02:42:21.29565+09: 회원9e7035f5의 구독/결제/이용권 모두0건. 무료체험지급0fd9a922-3b59-41a0-8f70-e80312cc2be2 active400/잔여400, 만료2026-10-08 15:20:35.986+09.
- 다음 준비는 이 회원으로 Basic월간 TEST5900 최초구독1건. 예상 월구독권한/구독400 지급/총800(무료400유지), 다음결제1개월후. 결제완료 주문번호·실제금액·잔액 확보 후 DB대조. 실패주입 구현/검증 전 날짜조정 없음. 신규결제는 아직 결과 미수신.

### A12 Basic 월간 최초 TEST 결제 화면 확인

- 사용자 고객 결제내역: sub_18f2b7e96157498d8cd8ef27a5de6ba4 / 구독시작 Basic월간 / 카드5900 / 결제완료·환불없음 / 생성·결제2026-09-10 02:47.
- 고객 유효800=구독400+무료400. 구독사용기한2026-10-10 02:47, 무료체험2026-10-08 15:20. 지급표를 두번 붙여넣은 것은 중복지급 증거로 간주하지 않음.
- 다음은 해당주문과 회원9e7035f5를 모두 조건으로 구독·이용권·지급·원장 READ ONLY 대조. 정확한ID/기간 확보 전 날짜조정없음. 실패주입 기능은 여전히 준비중이며 실행완료 아님.

### A12 최초구독 DB 대조 및 대상ID 확보

- 사용자 checked_at2026-09-10 02:50:04.272092+09. 주문d77cb994-67cb-483e-830a-f2f7c8bad80c/sub_18f2b7e96157498d8cd8ef27a5de6ba4 paid/succeeded5900/refund none. 구독be09b51b-4a00-4df9-a9b7-9ba74ae6c5a5 active Basic월간, 기간2026-09-10 02:47:34.695→2026-10-10 02:47:34.695/다음결제종료동일.
- 이용권7b810398-0a78-41dd-aedd-0e2301bf23f4 active/동일기간/credit_anchor開始同時刻/next_credit_grant_at NULL. 구독지급0fc2d1bc-8385-4500-b6aa-ffa48fda8111 active400/잔여400/동일기간/해당주문·구독·이용권연결. subscription-initial 원장+400 한건, 무료체험400 및 원장한건 유지. 고객800과일치.
- 출력에ROLLBACK줄 미포함이나 제공명령은READ ONLY. 다음 Toss TEST목록에서02:47 Basic월간5900/해당주문 승인완료 대조. 실패주입 준비완료 전 갱신일 조정하지 않는다. A08 소진조회02:59:10 이후 유지.

### A12 최초구독 Toss 승인 대조 완료

- 사용자 Toss TEST목록에서2026-09-10 02:47:34/fc8d0_sub_18f2b7e96157498d8cd8ef27a5de6ba4/완료/5900/신용·체크카드/Basic월간 확인. 고객·DB와 일치. 최초구독 준비 완료이며 갱신실패·복구 검증 완료는 아님.
- 다음 A08 02:59:10이후 최종소진 READ ONLY 확인. A12 특정구독 실패주입 실행도구 준비는 여전히 미완료, 날짜조정·실패요청 미실행.

### A12 특정 구독 TEST 실패 주입 코드 준비

- 사용자 진행동의 후 원본API 5파일 수정: Toss provider input에 내부 renewalScope(userId/subscriptionId) 추가, SubscriptionRenewalService만 해당DB식별자 전달, HttpTossPaymentsProvider의 billing POST에서만 범위설정 확인. 기존초기구독/상향/환불/삭제/조회는 주입대상 아님.
- 설정이름 CLIPPER_PG_RENEWAL_FAILURE_<subscriptionId의 하이픈을 밑줄로 치환>. 이번대상은 CLIPPER_PG_RENEWAL_FAILURE_be09b51b_4a00_4df9_a9b7_9ba74ae6c5a5. JSON필드는 userId(9e7035f5-9b99-4ac1-88b5-c654133725f3), amountKrw(5900), issuedAt/expiresAt(적용시UTC ISO지정). 유효기간최대1시간. 설정 자체는 어떤서버에도 추가하지 않았음.
- 설정없는 구독은 정상경로. 설정된 대상은 TEST billing키(test_sk_), 회원/금액/renewal주문 및 시각검증 후 고정 TossPayments-Test-Code: REJECT_CARD_PAYMENT 전송. 설정이잘못됐거나만료·live키이면 네트워크전 PG_TEST_SCOPE_REJECTED. 만료후 정상청구로 자동통과시키지 않으며 정상재시도 전에 설정제거가 필요. 이 로컬보호오류를 Toss결제실패 증거로 혼동하지 말 것.
- TDD provider수정전7실패72통과. 수정후 provider/renewal/retry정책3suite129통과 및 nestbuild/diff--check통과. 무설정·다른구독·초기결제 헤더없음, live/회원/금액불일치/만료/장기설정/JSON오류 네트워크차단 확인. 기존renewal서비스 호출테스트에 내부scope전달 기대값 추가. 다른세션 변경보존.
- 다음: API배포 및 대상설정적용/제거 시 서비스재시작 조율 필요. 아직 미커밋/미푸시/미배포이며 운영날짜·설정·결제 변경없음. 적용 revision/TEST설정 확인 후 별도승인된 대상기간압축과 실패시험 진행. A08 소진조회는 별도 유지.

### API 배포본 분리 검증 및 푸시 승인 대기

- 사용자가 운영작업 겹침없음 확인. m4-prod API clean/27103011e2e0672199721c6c3974c5bfc4e0d741/upstream origin/integration/toss-payments-pg-20260903 확인.
- 원본HEAD archive로 임시검증본을 구성하고 이번PG16파일 변경만 적용. 공유repository.ts는 listFinalRevocations만, openapi는plan_change enum만 포함. 다른세션 Naver 및 credit-ledger-display 변경 제외. 임시검증본8suite275테스트/build통과.
- PG패치만 index적용·확인 후 커밋88ae3f153950b83370ac723cf96ccbf5f6ad16e2 생성. 타세션32개 tracked변경 및 untracked 보존, index비어있음. Customer/Admin/.codex커밋없음. 서버배포없음.
- 일반push DNS실패 후 네트워크권한push 자동검토 거부: mixed-session가능성/원격승인부족 사유. 원격푸시완료 아님. 사용자에게 커밋88ae3f1을 OhMyMetabuzz/clipper_web_api의 integration/toss-payments-pg-20260903에 푸시하는 명시승인 요청. 우회실행하지 않음. 다음 승인후push/원격확인, 서버build-only 단계 안내.

### API PG 커밋 푸시 완료

- 사용자가 커밋88ae3f1의 지정원격/브랜치 푸시를 명시승인. git push origin 88ae3f153950b83370ac723cf96ccbf5f6ad16e2:refs/heads/integration/toss-payments-pg-20260903 성공, 원격출력2710301..88ae3f1 확인.
- 다음 사용자가 m4-prod에서 deploy-prod.sh api --build-only 실행. upstream최신화/이미지빌드만, 실행컨테이너 재생성·migration없음. 빌드로그SHA가 승인커밋인지 확인한 후 start-only는 별도단계 안내. 실패주입설정은 아직 적용안함.

### API 88ae3f1 운영 이미지 빌드 완료

- 사용자 m4-prod api --build-only 출력: 인프라/API fast-forward 후 clipper-web-api:prod(88ae3f153950b83370ac723cf96ccbf5f6ad16e2) 빌드완료, Images built. No application or DB changes performed. 승인SHA일치.
- 다음 api --start-only로 API컨테이너만 재생성. API 일시중단 및 내장 scheduler 재기동 영향 고지. DB migration/날짜조정/실패주입설정없음. 실행후 revision·health 확인이 남으므로 운영반영완료로 아직 기록하지 않음.

### API 컨테이너 교체 실행 확인

- 사용자 m4-prod api --start-only 실행: clipper-web-api-prod 재생성/Up Less than a second/192.168.0.47:43202→43202, DB migrations were not run 출력. 정상health 및 실제컨테이너 revision은 아직 미확인.
- 다음 docker inspect revision/status/restartcount 및 API /health 읽기전용 확인. 예상revision88ae3f153950b83370ac723cf96ccbf5f6ad16e2, health status와User/Admin/Release DB ok. 실패주입 설정/날짜조정은 아직없음.

### API 88ae3f1 운영 정상 기동 확인

- 사용자 inspect: running/restarts0/revision88ae3f153950b83370ac723cf96ccbf5f6ad16e2. 내부 /health HTTP200/status ok/service clipper_web_api/User·Release·Admin DB 모두ok. API 배포 정상기동 확인 완료. Customer/Admin 프런트 수정은 이번배포에 포함되지 않음.
- 다음 A12 실패설정 적용 전 API컨테이너에서 billing TEST키 여부 및 대상실패설정 미적용 여부를 값노출없이 확인. 이 조회로 DB/설정/결제 변경하지 않음. A08 소진결과는 아직미수신이며 API재시작시점의 영향도 실제조회결과와 함께 기록해야 함.

### A12 TEST키 확인 및 임시 설정파일 준비 안내

- 사용자 컨테이너조회 billingTestKey=true/targetFailureSettingPresent=false 확인. Compose는 환경변수를 명시적으로 전달하므로 stack.env에 임의키만 추가해서는 컨테이너로 전달되지 않음.
- 다음 m4-prod /tmp/clipper-pg-a12-failure.override.json에 특정구독용 Compose override를 새파일(wx/0600)로 작성하도록 안내. 회원9e7035f5/구독be09b51b/금액5900/생성시각부터1시간범위만 포함, 비밀키없음. 파일생성만으로 적용되지 않으며 기존env/원본Compose 변경없음.
- 생성후 내용중 기간·대상 확인 및 원본Compose와 병합검증을 거쳐 별도단계에서 API재생성 필요. 만료되면 승인차단이 유지되므로 성공재시도 전 override없이 원래배포명령으로 재생성해야 함. 현재파일생성결과/설정적용/갱신일조정은 미수신·미실행.

### A12 임시 override 생성 확인

- 사용자 /tmp/clipper-pg-a12-failure.override.json 생성확인. 회원9e7035f5/5900, issued2026-09-09T18:10:33.621Z/expires19:10:33.621Z(KST09-10 03:10:33.621→04:10:33.621). 컨테이너에 아직 적용되지 않음.
- 다음 m4-prod 원본compose2개/stack.prod.env와 override 병합을 메모리에서 검증. 대상키1개 이외 API환경불변 및 TEST키/구독범위/유효기간 확인, 원본설정과secret출력금지. 성공후 별도 API재생성 안내. A08 소진조회는 이제 예정시각이 지났으나 결과미수신.

### A12 override 병합 검증 통과

- 사용자 valid=true/onlyTargetSettingAdded=true/expiresAt2026-09-09T19:10:33.621Z 확인. 원본Compose 서비스와 대상환경키 제거후 병합서비스 동일, TEST키/대상/금액/기간 검증통과.
- 다음 m4-prod에서 동일project clipper-prod/원본env·Compose2개+임시override로 up -d --no-deps --force-recreate --no-build api. API만 재생성하며 짧은중단·내장scheduler재시작 영향 안내. 날짜조정·migration없음. 실행후실제설정·revision·health 검증까지 대기.

### A12 override 적용 컨테이너 시작 확인

- 사용자 Compose출력 clipper-web-api-prod Started(1.4s). 대상설정 포함 재생성명령 실행확인, 실제프로세스의 설정/health 검증은 아직미완료.
- 다음 m4-prod inspect revision/restarts 및 컨테이너내 TEST키·대상scope·유효기간 참거짓/만료시각만 출력, /health 확인. 갱신일조정 아직안함. 설정만료04:10:33.621 KST이며 실제유효여부를 조회시각으로 판정한다.

### A12 설정 적용 정상 확인 및 기간압축 안내

- 사용자 running/restarts0/revision88ae3f1, billingTestKey/targetMatches/validNow 모두true, 만료19:10:33.621Z, health200/모든DBok 확인.
- 다음 대상be09b51b 구독종료·다음결제와 access7b810398 ends_at, grant0fc2d1bc expires_at/benefit_period_end를 실행+5분(T,밀리초절삭)로 맞추는 단일트랜잭션 안내. 기존끝10-10 02:47:34.695/상태/회원/연결ID 및 각1행 검증, T는실패설정만료10분전보다이르도록 제한. 현재실행결과미수신.
- 예상: 다음scheduler에서REJECT_CARD_PAYMENT 실패주문, past_due 및첫실패기준3일유예/1일후재시도, 신규지급없음. 기존구독400은기한경과로유효잔액제외되어무료400만사용가능; 이용권은유예기간연장. 코드 startSubscriptionGrace는기존credit만료를연장하지않음. DB직접기간조정이며다른회원/무료체험/정책변경없음.

### A12 갱신 경계 압축 COMMIT 확인

- 사용자 NOTICE 기존2026-10-10 02:47:34.695+09→신규2026-09-10 03:20:40.205+09/DO/COMMIT 확인. 대상한진아 구독be09b51b의3행기간압축실행완료. 실패결과는아직미확인.
- 다음03:22이후 READ ONLY로 subscription past_due/first_failure/grace/retry, renewal주문status/error_code/paid_amount, access상태/기한, 유효잔액 확인. 기대REJECT_CARD_PAYMENT이며 PG_TEST_SCOPE_REJECTED나기타오류를동일통과로취급하지않는다. 실패설정만료04:10:33.621KST/해제작업남음. 기존A08 소진조회도추가대기없이같은READ ONLY에서확인가능.

### A08 최종소진 확인 및 A12 갱신 전 조회

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 03:17:41.344398+09. A12는 예정03:20:40.205 이전이므로 active/실패필드NULL/최초paid5900만1건/access active/유효무료400+구독400 정상. 실패검증결과가아니며03:22이후동일조회필요. 기간조정재실행없음.
- A08 inbox41151647-ec2b-40ec-8853-7e55bce8ef40 manual_review/WEBHOOK_RETRY_EXHAUSTED/retry_count4/processed_at02:59:00.045+09/next_retry_atNULL 확인. 주문미도착 합성웹훅의1/4/16/64분 backoff 및 최종자동중단 검증완료. 성공복구·다른오류·동시성은 별도. 이 이벤트 재전송/상태수정 불필요.

### A12 최초 갱신 실패·유예 진입 DB 확인

- 사용자 READ ONLY/ROLLBACK checked_at2026-09-10 03:23:13.644183+09. 구독be09b51b past_due, first_payment_failed_at09-10 03:21:00.045, grace_ends_at09-13 03:21:00.045, retry_days_snapshot[1,2]/next_retry_index0/retry_at09-11 03:21:00.045(KST). next_billing_at압축경계09-10 03:20:40.205유지.
- 실패갱신주문11de13d2-83f1-4169-b7a7-36a86dffb870/renewal-3KcBcj7YTkOLDKkK69TK07NS failed/paid_amount NULL/REJECT_CARD_PAYMENT, 생성03:21:00.103899. 최초주문paid5900유지. 로컬보호오류가 아닌 의도한Toss에러코드 확인.
- access7b810398 active/ends_at유예끝09-13 03:21:00.045/next_credit_grant_atNULL. 유효잔액무료체험400만. 신규지급원장중복검증은이번집계만으로확대하지않음.
- 다음 한진아 고객 /my 새로고침 후 결제실패·재시도·유예 안내 및400표시 확인. 재시도/카드변경버튼 아직누르지않음. 이후실패설정제거·API재생성·미적용검증 후성공복구시험. 설정유효기한04:10:33.621KST/제거미완료, 자연만료로설정이제거되지는않음. 자동D+1/D+2 및최종유예만료검증은별도남음.

### A12 고객 실패·유예 화면 확인

- 사용자 올바른 한진아계정에서 Basic월간/이용권활성/사용가능400/갱신결제실패, 2026-09-13까지이용/다음자동재시도09-11/결제다시시도버튼 확인. DB와핵심상태일치. 앞서붙여넣은Basic연간5200은기존회원화면으로구분.
- 표시개선후보: past_due에서도 다음결제예정09-10 03:20(과거경계)과 예정후순차결제 안내가 표시됨. 자동재시도 날짜/유예끝은시각없이표시. 실패안내핵심상태확인은통과지만 후속표시정리필요.
- 다음 m4-prod 원본 deploy-prod.sh api --start-only(override없음)로 실패환경설정제거. API짧은중단/재생성고지, DB날짜조정없음. 실제대상설정없음·health확인전 고객재시도실행금지. 이단계는성공복구준비이며복구결과미확인.

### A12 실패 설정 제거·정상 기동 확인

- 사용자 원본 api --start-only 재생성 후 billingTestKey=true/targetFailureSettingPresent=false, health HTTP200/status ok/User·Release·Admin DBok 확인. 실행중API 실패설정 제거완료. /tmp override파일 삭제는 하지 않았으며 다시적용하지않는다.
- 다음 한진아 계정 /my의 결제다시시도 한 번 실행. TEST5900 승인·구독active복구·구독400신규지급/유효총800 기대, 실제주문/기간/원장대조필요. 수동재시도 성공시험이며자동D+1/D+2 성공시험으로간주하지않음. 실행결과미수신.

### A12 수동 재시도 후 실패 유지 확인

- 사용자 2026-09-10 03:30:21.879644+09 조회: 갱신 주문11de13d2는 failed/fulfillment pending/REJECT_CARD_PAYMENT/paid_amount NULL, updated_at03:27:42.728952. 구독be09b51b는 past_due, 유예끝09-13 03:21/자동재시도09-11 03:21/index0 유지, 유효잔액무료400. 성공복구 미완료.
- 고객은 ‘기존 결제 주문을 확인하고 있습니다’ 표시. Customer retrySubscription은 paid+succeeded 외 모든 응답에 이 문구를 사용하므로 확정실패에도 처리중 안내가 나오는 결함 확인.
- 원본 코드 조사: tryBeginRenewalCharge는 실패 주문을 payment_pending으로 바꾸고 시도메타데이터를 기록하지만 billingChargeIdempotencyKey는 유지. chargeOrReconcile은 같은 키로 PG 요청. 최초 실패 응답 재사용 가능성은 가설이며 PG 원인 확정 아님. 다음 renewal_attempt_kind/renewal_attempted_at/failed_at을 읽기 전용으로 확인. 추가 버튼 클릭·DB 상태변조·결제키 변경 없음.

### A12 수동 재시도 실행 메타데이터 및 멱등키 조사

- 사용자 03:31:51.688471 조회에서 renewal_attempt_kind=manual, attempted_at03:27:42.547, failed_at03:27:42.722, REJECT_CARD_PAYMENT 확인. 버튼 무반응이나 처리대기가 아니라 수동 시도 후 실패 저장이다. 자동 retry index는 소비되지 않았다.
- 토스 공식 인증/헤더 문서 https://docs.tosspayments.com/reference/using-api/authorization 는 같은 멱등키/API키/주소/메서드에 최초 응답을 반환하며 키 유효기간15일이라고 설명한다. 현재 재시도는 동일 billingChargeIdempotencyKey를 유지하므로 최초 TEST 실패 응답 재사용이 유력하다. 응답 재사용 자체를 서버 응답메타데이터로 직접 확인한 것은 아니다.
- 다음 검증: 해당 주문의 PG 조회로 승인 유무 확인 후 확정 거절 재시도와 결과 불명 재조회를 분리하는 수정·회귀테스트. 결과불명/timeout에서 키를 바꾸면 안 된다. 운영 DB의 키 수동변경이나 새 결제 실행은 하지 않음. 고객 실패 안내 결함도 수정 대상. 성공복구는 미완료로 유지한다.

### A12 Toss 주문 조회 결과

- 사용자 m4 API 컨테이너에서 TEST billing 키로 GET 주문 조회. checkedAt2026-09-09T18:33:51.036Z(09-10 03:33:51.036KST), renewal-3KcBcj7YTkOLDKkK69TK07NS에 HTTP404/NOT_FOUND_PAYMENT. 조회 시점 승인 결제 미확인, DB failed/paid NULL과 일치. sameOrder=false는 오류응답에 orderId가 없기 때문이며 다른 주문이 조회됐다는 뜻이 아니다.
- 원인 가설: 최초 강제거절에 사용한 멱등키를 수동재시도도 재사용하여 기존 거절 응답 반환. 현재 증거만으로 토스 내부 캐시 여부까지 확정하지 않는다.
- 다음 작업: 확정 거절 후 새 결제 시도와 timeout/결과불명 재조회를 구분하는 API 수정 및 회귀테스트, Customer 실패 안내 수정. 승인·처리중·조회실패에는 새 키로 결제하지 않는 조건, 동시 재시도 중복 청구/지급 방지 검증 필요. DB 키 수동변경·추가결제·배포 없음. 성공복구 미완료.

### A12 확정 거절 재시도 및 고객 안내 로컬 수정

- 사용자 진행 승인 후 원본 API payments diff가 비어 있음을 확인하고 수정. Customer dashboard spec의 기존 연간 탭 테스트 변경은 보존. 다른 세션의 API keys/Naver/credits 및 Customer auth 변경 보존, 커밋·푸시·배포 없음.
- API: failed + REJECT_CARD_PAYMENT 주문만 구독 잠금 안에서 Toss 주문 GET. NOT_FOUND_PAYMENT일 때만 새 billingChargeIdempotencyKey를 생성하여 payment_pending claim과 같은 UPDATE로 저장한다. 주문 ID/주문번호/지급 단위는 유지한다. 조회 오류 또는 결제 발견 시 추가 청구 차단. 다른 오류·결과불명·기존 pending 복구는 기존 키 유지. 적용 범위는 확인한 거절 코드에 한정하며 모든 PG 오류 복구를 완료한 것으로 보지 않는다.
- Customer: retry 응답 status=failed면 ‘결제에 실패했습니다. 결제수단을 확인해 주세요.’ 표시. 성공/처리중 경로 유지.
- TDD: API 신규 검증4개 실패/기존100개 통과로 재현한 뒤 수정. 최종 수동·자동 거절 재시도, 조회 오류/기존 결제 시 청구 차단, 다른 오류의 키 유지 및 기존 provider/renewal/repository 포함3suite185개 통과. API build 통과. Customer 신규 실패안내 테스트1실패/기존45통과 후 수정, 최종46개 통과. 양 repo diff --check 통과.
- 제한: 실제 PG의 새 시도 승인과 동시 요청 실환경 검증은 아직 안 됨. 토스 결제가 발견된 불일치 건은 자동 복구하지 않고 차단한다. 조회는 구독 잠금 트랜잭션 안에서 실행되므로 해당 구독 작업은 조회 타임아웃 동안 대기할 수 있다.
- 다음: 이번 API 변경만 분리한 릴리스 검증·배포 후 health/실패설정없음 확인, 한진아 기존 갱신 주문 수동 재시도1회 및 DB/Toss/원장/총800 대조. Customer 안내 수정은 Customer 배포 후 확인. 운영의 기존 주문/키를 SQL로 수정하지 않는다.

### A12 API 릴리스 분리 및 푸시 승인 대기

- HEAD88ae3f1 원본 아카이브에 이번 payments5파일만 적용한 임시 릴리스에서185테스트/API build 통과. 해당 패치만 index에 적용하고 커밋8acbb90 생성. 다른 세션 미커밋 변경 및 Customer 변경은 포함하지 않았다.
- origin https://github.com/OhMyMetabuzz/clipper_web_api.git 의 integration/toss-payments-pg-20260903 브랜치로 푸시 시 자동 승인 검토가 ‘이 정확한 변경을 해당 원격으로 내보내는 명확한 승인 부족’으로 거절. 푸시 미완료, 운영 빌드·배포 아직 진행 불가. 우회 실행 없음.
- 다음 사용자에게 해당 원격/브랜치/커밋 푸시 승인 요청 후 진행. 운영 API는88ae3f1 유지. 승인 후 푸시 확인→m4 api --build-only부터 한 단계씩 안내.

### A12 API 푸시 완료

- 사용자 원격/브랜치/커밋 명시 승인 후 8acbb90을 origin integration/toss-payments-pg-20260903에 푸시 성공(88ae3f1..8acbb90). 운영 배포는 아직 하지 않았다.
- 다음 m4-prod 원본 Infra deploy-prod.sh api --build-only 실행 결과에서 빌드 revision8acbb90 확인. 이 단계는 이미지 빌드이며 실행 컨테이너/DB 변경 없음. 이후 start-only와 health/실패설정없음 확인을 별도 단계로 진행한다.

### A12 수정 API 배포 및 수동 재시도 복구 DB 확인

- 사용자 m4 build-only/start-only 후 revision8acbb90bcd85f5c942c56dfcc1b00c91af071c9c/running/restarts0, billingTestKey=true/targetFailureSettingPresent=false, health200 및3DBok 확인. DB migration 없음.
- 고객 한진아 계정에서 수동 재시도1회 후 성공 문구. 처음 잔액400에서 다음 scheduler 이후800으로 변경, Basic월간 활성/자동갱신/다음결제10-10 02:47 확인. Customer 코드 배포는 하지 않았다.
- 사용자 DB checked_at09-10 03:45:30.704642+09: 기존 주문11de13d2/renewal-3KcBcj7YTkOLDKkK69TK07NS paid/succeeded5900/paid_at03:44:44.062/error NULL. 신규 별도 갱신 주문 없이 기존 실패 주문 복구. 최초 주문d77cb994 paid5900 유지.
- 구독be09b51b active/next_billing_at10-10 02:47:34.695, first_failure/grace/retry/index 모두NULL. access7b810398 active/ends_at동일/next_credit_grant_atNULL.
- 기존400 grant0fc2d1bc expired/rem400/만료03:20:40.205. 신규0b89028e-604e-4972-aa5d-058cb4e172f0 active400/rem400, 기간03:20:40.205~10-10 02:47:34.695. 월별 지급 원장+400 한 건, reference monthly:7b810398-0a78-41dd-aedd-0e2301bf23f4:2026-09-09T18:20:40.205Z, 실제생성03:45:00.022622. 이번 조회에서 중복 지급 없음. granted_at은이용기간경계, 실제원장생성은결제후다음분으로구분.
- 다음 토스의 동일 renewal 주문5900 승인 내역 확인. 자동D+1/D+2 재시도/최종유예만료 및실환경동시성은별도남음. 완료 환불 재실행 없음.

### A12 수동 재시도 복구 Toss 최종 대조

- 사용자 Toss 테스트 결제내역에서 fc8d0_renewal-3KcBcj7YTkOLDKkK69TK07NS / Basic월간 / 카드 / 완료5900 / 2026-09-10 03:44:43 확인. 기존 실패 주문의 수동 재시도 성공을 고객 화면·DB·Toss로 대조 완료. DB paid_at03:44:44.062와 승인시각은 별도 기록값으로 보존.
- 현재 한진아 Basic월간 활성/유효800, 다음결제10-10 02:47:34.695, 실패환경설정 없음. API8acbb90 배포 완료. Customer 실패문구 수정은 미배포.
- 다음 검증: 자동D+1/D+2 실패재시도 및 유예최종만료 시 권한/크레딧 처리. 사전 상태를 새로 조회하고 대상 한정 TEST 설정·시간조정 절차를 준비한 뒤 진행하며 이번 수동복구와 구분한다. 기존 완료환불 및이번승인 재실행 없음. 연간상향 웹훅 manual_review 복구와 Customer/Admin 미배포 UI 재검증도 남음.

### A13 자동 재시도 2회 소진 확인

- 한진아 be09b51b 구독, A13 override 생성/Compose 비교 통과/적용 후 API8acbb90 running/restarts0/TEST키·대상·유효시간true/health200 사용자 확인. 설정 만료2026-09-10 04:49:05.132KST, 아직 제거 전.
- 대상 구독/access/현재구독400 지급분 경계를03:53:36.504로 압축 COMMIT. 최초03:54:00.056 실패, 신규주문e8309db5-0c68-492d-b811-0eca90eddaeb / renewal-X2JRmp0KCWUgEmhytwRR8z_u, REJECT_CARD_PAYMENT/paid NULL. past_due/유예끝09-13 03:54:00.056/정책[1,2], 무료400 유지.
- 첫 retry_at만03:58:10.062로 압축. 사용자 중복실행은 사전상태 불일치로 롤백. 04:00:41 조회에서03:59 scheduled 실패/attempt index0, 구독next index1/예약09-12 03:54 확인.
- 두 번째 retry_at만04:03:19.726로 압축 COMMIT. 04:05:12.344695 조회에서04:04:00.059 scheduled 실행/04:04:00.376 REJECT_CARD_PAYMENT 실패/attempt index1, 구독next index2/retry_atNULL. past_due 및 유예끝 유지, 유효무료400. 같은 실패주문 재사용. 실제1·2일 대기 대신시각압축한 검증으로 구분.
- 다음 한진아 고객 화면에서 유예중/자동재시도 예약없음/잔액400 확인 후 대상구독·이용권 유예종료 경계압축 및 자동만료 검증. A13 실패환경설정 제거와health검증 필수 잔여작업. 수동 재시도 클릭 없음.

### A13 유예 만료 및 실패 설정 제거 최종 확인

- 사용자 대상구독 grace_ends_at/access ends_at만04:08:41.667로 압축 COMMIT. DB04:11:38.264154: be09b51b stopped/next_billing_atNULL/retry_atNULL/index2, access7b810398 ended/ends_at=ended_at04:08:41.667/next_credit_grant_atNULL. 기존paid2건 유지, 새갱신e8309db5 failed/REJECT_CARD_PAYMENT/paid NULL, 유효무료400만.
- 사용자 m4 원본 api --start-only 후 running/restarts0/revision8acbb90, billingTestKeytrue/targetFailureSettingPresentfalse, health200/3DBok 확인. A13 override 실행환경 제거 완료. 임시파일 자체는 삭제하지 않음.
- 고객 최종화면 Trial/무료체험/이용권활성/잔액400, ‘갱신 실패로 정지’, 유예종료·새구독시작 안내, 이전 Basic월간/기존기간끝09-10 03:53/다음결제중단 표시. Trial 활성은 남아있는 무료체험 권한이며 종료된 Basic 권한과 구분. 고객/DB 핵심상태 대조 완료.
- 완료범위: 대상 TEST 자동재시도2회 소진 및 유예최종만료(시각압축), 무추가승인·무료체험잔액유지. 실제일수경과/다른거절코드/동시성/모든회원 영향 검증으로 확대하지 않음.
- 다음 검증: Admin 회원상세의 구독정지·이용권종료·무료400 대조. 이어 기존 연간상향 webhook manual_review 복구와 Customer/Admin 미배포 UI 변경 검증, 사용량있는 환불/부분실패 복구 등 남은 TEST 범위를 진행. 완료환불 재실행 및 새구독 생성 불필요.

### A13 종료 시 크레딧 만료 상태 누락 로컬 수정

- Admin은구독중단/청구중단/총400을표시하나03:53만료구독400을사용가능으로표시. 사용자04:15:31 DB 조회에서grant0b89028e active/rem400/past_expirytrue/usable_by_timefalse 확인. 잔액오류와상태정리누락을구분.
- 원인경로: MonthlyCreditGrantService는자연종료시access.endExpired만호출하고크레딧정리누락. AccessGrantsService.endSubscriptionPeriod는이미ended면조기반환하므로월별작업이먼저종료한경우정리가빠질수있음. 실제운영실행순서로그까지확인한것은아님.
- 수정: 월별작업의최종종료직전에expireAccessCredits 호출. 구독종료의already-ended경로도기존endedAt기준만료정리실행하되종료이벤트중복추가없음. 기존Repository는대상이용권/active/기한경과만업데이트하며잔량·원장변경없음.
- TDD2실패27통과로재현후수정. nextCreditGrantAtNULL 유예종료케이스도추가. 최종API4suite104통과/build통과, 기존Admin시간기준만료표시22테스트통과, 양repo diff--check통과.
- 현재원본API HEAD3b6d68d는다른세션Naver/원장표시커밋을포함. 이번4파일만로컬수정했고커밋/푸시/배포안함. 다른세션커밋을묶어배포하지않는다.
- 다음: API이번수정과Admin기존수정의분리릴리스준비. 이미stopped인현재건은자동재처리대상아니므로배포만으로DB가정리된다고약속하지않음. 대상1건의기한/상태/잔량검증후별도상태정리절차필요. 실제회수나추가결제없이총400유지검증.

### 만료 수정 분리 릴리스 준비

- 운영기준API8acbb90/Adminfb3e532 아카이브에 각이번4파일패치만적용. 분리후API104테스트/build,Admin22테스트통과.
- 원본checkout/index변경없이 별도 release/pg-expiry-20260910 브랜치 생성: API37cdcdb2c37d24bc56c4f7dc86eb9bc3afb78adf(parent8acbb90), Adminc31924959cf75af65da5fb8360305f3eed54785f(parentfb3e532). 다른세션3b6d68d/cafebe3 제외. 원본미커밋작업은그대로보존.
- API해당브랜치푸시는자동승인검토에서새릴리스브랜치/대상으로의명시적전송승인부족으로차단. API/Admin모두푸시·운영배포미완료. 사용자에게두저장소/브랜치/커밋명시승인요청. 승인후푸시,운영checkout분기방법확인후사용자서버명령단계안내필요.

### 만료 수정 릴리스 브랜치 푸시 완료

- 사용자가 별도브랜치목적 설명후진행승인. API37cdcdb/Adminc319249를 각각OhMyMetabuzz 원격의 release/pg-expiry-20260910에푸시성공. 기존통합브랜치/checkout변경없음. 운영배포미실행.
- 다음사용자m4의API/Admin원본저장소현재branch/HEAD/미커밋변경을읽기전용확인. 이후릴리스브랜치선택및build-only절차안내. 현재서버상태를확인하기전에checkout/pull하지않는다.

### Admin 상단 지급 표 만료 표시 누락 추가 수정

- 사용자 API37cdcdb/Adminc319249 배포·running/restarts0/HTTP200 확인. API TEST키true/실패설정false. Admin 강력새로고침 결과 하단수동조정표는만료이나상단지급표는사용가능 잔존, 총무료400유지.
- 상단은detailCreditStatusLabel, 하단은creditStatusLabel로별도함수이며상단의시간조건누락을확인. 캐시문제로취급하지않음. 상단active+expiresAt경과에도만료표시추가,refund_locked/회수표시우선순위유지.
- 실제상단DOM렌더링 회귀테스트(경계시각/미래/환불잠금)추가로1실패22통과 재현후수정,최종23통과/diff--check통과. 기존다른세션변경보존. 이추가수정은아직로컬이며커밋/푸시/배포전.
- 다음Admin릴리스c319249위에이번추가수정만반영후배포및두표재확인. 현재DB active만료1건정리및API종료경로실환경재검증은별도남음.

### Admin 상단 표 추가 수정 릴리스

- 사용자 진행승인후c319249아카이브에상단함수/DOM테스트2파일만추가한후보23테스트통과. 원본checkout/index와다른변경보존. release/pg-expiry-20260910에b3492e2ec895cca82fb52856f97612c39a404a9b 생성·푸시완료(c319249..b3492e2).
- 다음m4 admin --build-only 출력b3492e2 확인후start-only/기동검증/상하단만료표시 재검증. API와DB재변경없음. 기존DB1건정리는여전히미완료.

### 만료 표시 실환경 확인 및 기존 지급 건 상태 정리 완료

- 사용자 Admin b3492e2 배포 running/restarts0/HTTP200 확인. 한진아 상세 상단지급표·하단수동조정표 모두03:20지급/03:53만료 구독400을‘만료’로표시,총가용무료400유지. 상단표누락수정 실환경검증완료.
- 사용자 승인한 조건부SQL로 grant0b89028e-604e-4972-aa5d-058cb4e172f0 한건만 active→expired 및updated_at변경. 사용자출력DO/expired/remaining400/expires_at09-10 03:53:36.504/가용무료400/COMMIT 확인. 잔량·원장·결제변경없는상태정리이며 API자동처리성공증거로간주하지않는다.
- 현재운영API37cdcdb/Adminb3492e2,둘다release/pg-expiry-20260910. 고객은기존배포유지. A13실패설정없음. 한진아구독stopped/Trial400. 다른세션커밋은해당릴리스에포함하지않았다.
- 다음 검증: 수정API 만료경로의 실제scheduler 재현(새 TEST 상황의사전상태확인필요). 기존연간상향웹훅manual_review 복구,미배포Customer개선,잔여환불예외검증도남음. 완료환불·A12복구·A13소진테스트는처음부터반복하지않는다.

### 수정 API 자동만료 해지예약 경로 DB 검증 완료

- 새 TEST Basic월간: order1439ec71-bcdb-4978-a9b1-60839f498755/sub_b808b670b5a14d7c8846336005658064 paid/succeeded5900. subscription65a5a240-573e-466b-accc-f6b3e28fb201, access6c8e6368-1b09-4a42-ae56-c5f1223a7b45, credit c6d4a96f-1e6a-4fae-b76f-f4b32a87154e active400, 原기간09-10 04:42:16.372~10-10동시각. 고객800 확인.
- 고객다음자동결제취소후DB04:45:02 cancel_at_period_end/next_billing·retryNULL 확인. 승인한3행경계압축SQL로period_end/cancel_at/access ends_at/credit expires_at·benefit_period_end만09-10 04:47:46.828로변경COMMIT. 상태직접변경없음.
- 사용자04:52:51.744051 DB: subscription ended/next_billing·retryNULL, access ended/ends_at=ended_at경계/next_creditNULL, credit expired/rem400. 주문은최초paid5900 한건만, 가용무료400. API37cdcdb에서해지예약후자동종료·만료회귀검증완료.
- 범위제한: 실제한달대기대신시간압축. 어느scheduler가먼저종료했는지는이조회로확정하지않음. 수정후past_due유예종료경로실환경재현과동시실행순서는별도. 새주문Toss직접대조도이번출력에없음.
- 다음고객/Admin새로고침하여무료체험400/유료구독종료/신규400만료표시확인. 이후기존연간상향웹훅manual_review 복구등미완료PG검증진행. 완료결제·환불재실행불필요.

### 자동만료 회귀검증 고객·Admin 최종 대조

- 사용자 고객화면Trial/무료체험400/구독종료/다음결제중단,04:47만료 신규구독400 및기존구독지급분모두만료확인. Admin도구독종료/청구중단/상하단지급표만료/가용무료400 일치. DB와함께해지예약종료경로의자동크레딧만료검증완료.
- 별도미완료관찰: 종료된구독에도Admin ‘04:47 해지 예약’ 문구잔존. 제공한이용권이력에는종료이벤트가없고크레딧원장에는지급만보임. 상태자동만료통과와구분하여종료감사이력·만료원장정책/구현추가확인필요. 영어원장사유는Customer미배포개선과별도세션커밋범위를확인후처리.
- 다음검증은기존연간상향웹훅manual_review 복구의읽기전용사전대조부터진행가능. 이번종료결제재환불·재가입·상태수동변경불필요. 수정후유예종료실환경재현/동시성/환불예외는남은범위로유지.

### 연간 상향 환불 웹훅 수동 검토 복구 검증 (2026-09-10 05:02 KST)

- 사용자 실행 결과 기준. Inbox `778c9ef6-554a-43c2-8316-fac26393491f`는 기존 `manual_review / WEBHOOK_ORDER_PURPOSE_MISMATCH`에서 정확한 ID·기존 상태를 조건으로 04:59:42.039219에 `received`로 변경하고 COMMIT. 05:02:46.721414 조회에서 `processed`, 처리 시각 05:00:01.070, 오류 없음, retry_count=0, next_retry_at=NULL 확인.
- 환불 케이스 `61d6c4bc-b2b3-4328-835f-b27f3eb98807` money/internal 모두 completed, 실제 72,017원 유지. 주문 `2851be09-ace0-4f12-b4d1-493de2dcdbfb` paid/full, 누적 환불 72,017원 및 환불 가능 잔액 0원 유지.
- 지급 `f5ffc738-4eba-4113-b23c-ae143de59108` 원장 2건·합계 0으로 사전 기준과 동일. 해당 웹훅 재처리에서 환불 금액·크레딧 원장 중복 반영 없음 확인. 다른 웹훅이나 환불 예외 전체의 검증 완료를 의미하지 않음.

### 연간 변경 후 월별 지급분 포함 전액환불 검증 (2026-09-10 05:28 KST)

- 사용자 실행·화면·읽기 전용 DB 결과 기준. 환불 `4caa171c-43f8-414f-ae9c-8e54d984dee6` money/internal completed, 실제 52,906원. 변경 결제 `21a547f3-3f79-437d-8530-dcba03bba8fa` paid/full, 누적 환불 52,906원, 환불 가능 잔액 0원.
- 구독 `89ba75e8-111b-4935-a131-069eddc4e3b4` canceled, next_billing_at/retry_at=NULL, billing_key_removal_status=succeeded. 이용권 `f34fc47d-72fd-4765-9973-d5dd94e7ed87` revoked, ended_at=05:15:17.383, next_credit_grant_at=NULL.
- 만료된 최초 지급 `d2b7017e-3662-4de3-b2cb-ef678c872a68`은 expired/잔여400 그대로 보존. 월별 지급 `c152cdcd-319c-47d7-a5b9-0c2798d000c8`은 revoked/잔여0/해당 환불 연결. 원장에 payment_refund_revoke -400이 05:15:21.531286 한 건만 기록됨. 가용 무료400+topup4400=4800으로 고객 화면과 일치.
- 월별 지급 시점을 앞당긴 테스트 상태에서의 검증임. 사용자 토스 관리자 전송 결과에서 `fc8d0_upgrade_9e8f2c700ef10d20c59dafe8f7788b003d3003d5394141556f6c1c9a`, Basic 연간, 52,906원, 취소 확인. 고객·Admin·DB·토스 관리자 결과 일치.
- 사용자 05:31:49.723922 읽기 전용 조회에서 취소 웹훅 `6461a476-cd6e-421e-9765-95e321874ffd` PAYMENT_STATUS_CHANGED/CANCELED/processed 확인. received_at=05:15:21.630018, processed_at=05:16:00.656, last_error_code=NULL, retry_count=0, next_retry_at=NULL. 기존 상향 결제 웹훅 목적 불일치가 이번 신규 취소에서는 재현되지 않음.
- 별도 UI 문제: 접수 후 모달·워크벤치가 닫히면서 안내가 화면 밖으로 이동하고 신규 접수에도 ‘이미 처리 중’ 공통 안내가 표시됨. onRefundAccepted가 acceptedRefundCaseId 설정 후 워크벤치를 닫고 회원을 재조회하는 경로 확인. 접수 성공 시 생성된 환불 상세로 이동하는 개선 제안, 아직 구현·배포하지 않음.

### 환불 접수 후 상세 이동 개선 (로컬 수정)

- 사용자 승인 후 회원 상세의 RefundWorkbench navigateOnAccepted=false를 true로 변경. 기존 컴포넌트의 접수 성공 후 생성된 환불 상세 이동과 모달 닫기 시 포커스 복원 생략 경로를 사용한다. 기존 처리 중 환불 차단 및 접수 후 회원 재조회/링크 fallback은 유지.
- 회원 상세의 이동 설정 회귀 assertion 추가, 수정 전 false 때문에 1실패22통과 확인. 수정 후 회원 상세와 환불 워크벤치 테스트 합계38통과. git diff --check 통과. Angular build는 sandbox에서 exit134 두 번 후 escalated 로컬 실행 성공(initial bundle 566.39kB/500kB 경고). 운영 서버·DB 변경 없음, 커밋·push·배포 미실행.

### 환불 상세 이동 릴리스 커밋·푸시

- 기존 Admin release/pg-expiry-20260910의 b3492e2 위에 이번 HTML 설정·테스트 두 파일만 담은 `4367fa8442afced1af62a11a5dc4d5563a39076e` 생성. 원본 작업트리/인덱스와 다른 세션 변경 보존. 정확한 커밋을 임시 디렉터리에 추출해 관련 테스트38통과 및 프로덕션 build 성공(초기 번들565.90kB 경고).
- 자동 승인 검토가 짧은 동의를 인정하지 않아 푸시가 차단됐으나, 사용자가 저장소·브랜치·커밋·두 파일 내용을 직접 명시한 후 푸시 성공. origin OhMyMetabuzz/clipper_web_admin release/pg-expiry-20260910이 b3492e2→4367fa8로 전진했음을 push 출력 확인. m4 운영 배포는 아직 실행 전.

### 환불 상세 이동 Admin 운영 배포 확인

- 사용자 m4-prod 실행 결과: admin --build-only에서 `4367fa8442afced1af62a11a5dc4d5563a39076e` 빌드 완료 후 admin --start-only로 컨테이너 교체. docker inspect에서 running/restarts=0/revision=4367fa8442afced1af62a11a5dc4d5563a39076e, 192.168.0.47:42302 HTTP=200 확인.
- Admin 배포 및 기본 응답 확인 완료. 이번 배포로 API·DB migration 실행하지 않음. 실제 신규 환불 접수 후 상세 자동 이동의 운영 화면 검증은 아직 미실행이며 다음 필요한 TEST 환불에서 확인할 항목으로 유지.

### 전액 환불 완료 미리보기 오분류 및 안내 수정 (로컬)

- 사용자 보고 대상 d8782ce3-60b9-451d-866a-903994a32f44는 기존 5,900원 전액 환불 건. 일부 환불 테스트로 안내한 것은 오류이며, 전액 환불 완료 건의 재접수 UI 차단만 확인. 사유 입력 및 실행 버튼은 없음.
- 원인: paid topup 조회에 완료 환불도 포함되고, eligibility가 refundStatus!=none 등 모든 기존 환불을 PARTIALLY_REFUNDED로 반환. Admin은 0원도 금액 미확정 오류로 처리하고, 구독 설명/실행 전 provider 확인 문구를 추가 구매·불가 상태에도 표시.
- FULLY_REFUNDED 사유 추가(API/OpenAPI/Admin model). full/잔액0/누적환불=결제액을 확인한 완료 상태와 partial/양수잔액/누적+잔액 일치 상태 분리. 금액 없음·상태 불일치는 PROVIDER_STATE_REFRESH_REQUIRED로 차단. 완료 건의 providerRefreshRequired=false. 완료 건도 관련 결제로 조회 가능하게 유지하되 목록 문구를 ‘관련 결제’로 변경.
- Admin 완료 제목·완료 금액 표시, 0원/미확인 안내 분리, 실행 가능한 상태에서만 실행 전 안내, 상품별 설명, 크레딧 상태 한글 및 이미 회수됨/만료 기록 유지 표시. 실행 차단 유지.
- API 신규3테스트 실패, Admin 신규1테스트 실패로 기존 증상 재현 후 수정. 불일치·부분환불·금액미확인 테스트 보강. API 관련4suite95통과, Admin 회원 상세/워크벤치41통과. 두 앱 build 성공, diff--check 통과(Admin 초기 번들566.39kB 경고). 공유 변경 보존. 이번 수정 커밋·push·운영 배포 및 DB 변경 없음.

### 전액 환불 안내 릴리스 준비

- 기존 release/pg-expiry-20260910 기반에서 이번 변경만 별도 추출해 API 95테스트/Admin41테스트 및 양쪽 build 성공. API `923c9cbf224ac5ed08eac3af276e718c5c9dac80`(부모37cdcdb, eligibility·테스트·OpenAPI·계약테스트4파일), Admin `62a56690b338567aa8882e6b7aabb523d2db2df0`(부모4367fa8, 모델·워크벤치·템플릿·테스트4파일) 생성. 공유 원본 인덱스/작업트리 보존.
- API push는 자동 승인 검토가 정확한 외부 목적지/페이로드의 사용자 명시 승인 부족으로 거절. API 원격 변경 없음, Admin push 미시도. 두 저장소·커밋·브랜치를 명시한 사용자 승인 대기. 운영 배포 없음.

### 전액 환불 안내 릴리스 원격 반영

- 사용자가 두 저장소·커밋·브랜치·수정 내용을 명시해 승인한 후 push 성공. API origin release/pg-expiry-20260910 37cdcdb→923c9cb, Admin origin 동일 브랜치 4367fa8→62a5669. 각 push exit0 및 원격 갱신 출력 확인. m4 운영 배포는 아직 실행 전.

### 전액 환불 안내 운영 배포·화면 검증 완료

- 사용자 배포 결과 API923c9cb running/restarts0/health200 및 DB3항목ok, Admin62a5669 running/restarts0/HTTP200 확인. DB migration 없음.
- 처음 조회는 API의 전액 환불 사유와 이전 Admin 문구가 함께 보였으나 강력 새로고침 안내 후 최신 화면 확인. 브라우저 캐시의 정확한 계층은 별도 추적하지 않음.
- 대상 d8782ce3-60b9-451d-866a-903994a32f44: 전액 환불 완료/추가 환불 없음, 원결제5900·잔액0·환불완료5900 표시. 연결 지급5193342b-8226-4f73-bb56-293a45d0b839는400/0/0, 회수 완료/이미 회수됨·추가 처리 없음. 기존 구독 설명·금액 확정 실패·raw revoked 문구 사라짐 확인.
- 가용 무료400+topup4400=4800 유지. 별도 연간환불 월별지급 c152cdcd 원장도 결제 환불 회수 -400/잔액0 한글 표시 확인. 이번 조회로 새로운 환불 실행하지 않음. 실제 부분 환불 건 검증과 환불 접수 후 상세 이동 운영 검증은 별도 미완료 항목.

### Admin 회수 분류 및 환불 원장 유형 수정

- 사용자 대기중 남은작업 승인. API 회원조회가 refundCaseId없는 revoked를 admin으로 분류하던 문제를 수정. 대상지급별 잔여0을 만든 음수 회수원장 중 최신건을 읽어 payment_adjustment→plan_change, admin_revoke→admin, payment_refund_revoke→refund로 분류하며 근거없음은NULL. refundCaseId는 기존환불분류 유지. DB/원장 쓰기 없음.
- CreditsRepository/TypeOrm 구현에 대상ID일괄조회 추가, MembersService/model 및 OpenAPI enum 보완. Admin models와 회원상세라벨에 plan_change→요금제 변경 회수 및 payment_refund_revoke→결제 환불 회수 추가.
- 공유 Admin models/API openapi의 Naver 관련 다른세션diff를 확인·보존하고 해당열거값만 수정. API 테스트 수정전1실패16통과, Admin1실패21통과로 재현. 수정후 API 관련3suite98통과/Admin22통과/API nest build 및 양repo diff--check 통과. DB에서 신규조회SQL을 실제실행한 검증과 운영화면 검증은 배포후 필요.
- 다음 A08 최종소진 읽기전용확인, 배포조율 및 수정화면 재검증. 이 작업으로 환불·결제·worker 재실행하지 않음.
