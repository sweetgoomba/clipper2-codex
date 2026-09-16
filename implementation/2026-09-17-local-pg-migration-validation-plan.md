# 정식 PG 로컬 DB·개발 DB 복제본 검증 계획

> 실행 전제: 코드 통합과 안전성 구현이 완료되고 targeted test/build가 통과한 뒤 수행한다. 서버에 직접 접속하거나 실제 개발 DB를 변경하지 않는다.

실행 현황(2026-09-17): Phase 1의 빈 로컬 User/Admin/Release migration·API/Web/macOS 앱 smoke와 Phase 2의 실제 pre-`DropLegacyBilling` schema fixture, 누락 replacement-table guard, 로컬 dump restore rehearsal까지 완료했다. 상세 증거는 [정식 PG 로컬 통합·검증 최종 결과](2026-09-17-local-pg-integration-validation-result.md) 참조. 다음 승인 지점은 Phase 3 개발 DB dump 복제본 inventory이며 실제 개발 DB에는 아직 적용하지 않았다.

**목표:** 별도 로컬 PostgreSQL에서 정식 PG schema와 앱 동작을 검증하고, 그다음 사용자가 만든 개발 DB dump 복제본에서 사용자·로그인을 보존하면서 구·신 금융 상태를 안전하게 정리하는 전환을 리허설한다.

## 데이터 정책 정본

### 보존

- 사용자 계정과 인증 identity.
- 사용자 session/로그인 데이터 중 새 schema와 호환되는 항목.
- 개발자의 로컬 프로젝트·미디어·terminal job 이력.
- plan/product/catalog/operation policy 같은 정식 PG 구성 데이터.
- API key, Naver, 진단, release 등 결제와 무관한 데이터.

### 초기화

- PG 전 옛 `licenses`와 purchase request 계열.
- subscription/payment/billing-key/refund/webhook 같은 개발 금융 거래 상태.
- `user_access_grants`, access events, user free-trial 사용 상태.
- `credit_grants`, `credit_ledger_entries`와 옛 credit ledger.
- `operation_runs`, evidence, resolution events처럼 기존 차감과 연결된 금융 실행 이력.

### 새로 지급하지 않음

- 기존 사용자에게 access나 credit을 소급 지급하지 않는다.
- 예전 license를 새 access/credit으로 환산하지 않는다.

### 중단 조건

- LIVE provider environment, 실제 결제 transaction key, 실제 고객 결제로 의심되는 row가 하나라도 발견되면 삭제 SQL을 실행하지 않고 사용자에게 보고한다.
- FK 또는 건수가 예상과 다르면 범위를 넓혀 삭제하지 않고 중단한다.

## Phase 1: 완전 별도 로컬 빈 DB

1. 로컬 전용 user/admin/release DB를 생성한다. 개발서버 DB URL은 사용하지 않는다.
2. 현재 dev schema에서 integration migration 전체를 forward 적용한다.
3. migration을 두 번 실행해 두 번째가 no-op인지 확인한다.
4. operator와 product/catalog seed를 적용한다.
5. Web API, Web Client, Web Admin, Desktop devapp을 모두 이 로컬 DB/API에 연결한다.
6. Toss/외부 provider는 mock 또는 테스트 키만 사용하고 실제 승인·과금은 하지 않는다.

**검증 조합**

- access 없음/활성/만료 × credit 0/충분/추가구매만 잔존.
- 구독 만료 뒤 추가구매 credit만 남은 사용자의 작업 허용.
- active access 없이 새 top-up은 차단, 이미 남은 top-up credit 사용은 허용.
- 모든 현행 tier의 `entitlement_mode=all`과 동일 plugin 접근.
- Shortform URL/paste/prompt, Dance, Dialog, Variation의 quote/confirm/start/terminal/refund.
- 댓글 오버레이·영상 랭킹은 같은 job 상태 기계지만 billing row가 없는지.
- outbox replay와 operation start 중복 요청에서 ledger가 한 번만 변하는지.
- 사용자 실패 재시도는 새 operation과 새 차감이며 원시도 환급과 분리되는지.

## Phase 2: 과거 schema fixture migration

실제 개발 DB를 쓰지 않고 다음 fixture를 만든다.

- 사용자·로그인은 존재.
- 옛 `licenses`, purchase request, 옛 operation/credit history가 존재.
- 새 PG table은 없거나 migration 일부만 적용된 두 변형.
- 신규 financial table에 개발 테스트 row가 일부 존재하는 변형.

각 fixture에서:

1. 사전 row count와 FK graph를 기록한다.
2. forward migration을 적용한다.
3. 전환용 inventory query를 실행한다.
4. 승인 정책에 맞는 금융 reset을 실행한다.
5. 사용자/auth PK와 count가 그대로인지 확인한다.
6. 금융 transactional table이 0건인지, catalog/policy는 남았는지 확인한다.
7. 새 결제를 하지 않은 기존 사용자의 access/credit이 0인지 확인한다.

## Phase 3: 개발 DB dump 복제본 inventory

서버 명령은 사용자가 실행한다. 실행 전 별도로 다음을 제공해야 한다.

- 실행 장비: 개발 DB에 접근 가능한 사용자 장비/운영 터미널.
- 목적: read-only dump 생성과 clone restore.
- 영향: 원본 DB 변경 없음, dump 파일에 개인정보가 포함될 수 있으므로 로컬 보관·권한 제한 필요.
- 사용 DB/host/name을 명시하고 production과 다른지 사용자가 직접 확인.

복제본에서만 다음을 조사한다.

- table별 전체 row count와 user별 분포.
- `licenses`, `subscriptions`, payment/refund/webhook/billing auth rows.
- `user_access_grants`, access events, free trials.
- `credit_grants`, ledger entries, operation runs/evidence/resolution.
- source/reason/provider environment, created_at 범위, 연결 payment/subscription FK.
- orphan/FK 위반과 일부 migration 적용 흔적.

이 조사의 목적은 데이터를 임의로 일부 보존할지 선택하는 것이 아니라:

1. 현재 승인 정책을 적용했을 때 삭제될 정확한 건수 산출.
2. FK 순서와 transaction rollback 가능성 검증.
3. 예외적인 실제 결제 의심 row 탐지.

## Phase 4: 전환 SQL rehearsal

**산출물 제안**

- `web/clipper_infra/runbooks/dev-pg-cutover.md`
- `web/clipper_infra/scripts/dev-pg-inventory.sql`
- `web/clipper_infra/scripts/dev-pg-reset-financial-state.sql`
- `web/clipper_infra/scripts/dev-pg-postcheck.sql`

reset SQL은 반드시 한 transaction으로 실행하고 다음 guard를 둔다.

- expected database name/environment assertion.
- production/LIVE provider row 발견 시 exception.
- 사용자/auth table에 DELETE/UPDATE 금지.
- 실행 전·후 count를 결과로 출력.
- 예상 FK/row count가 다르면 rollback.
- catalog/policy seed table은 삭제 대상에서 제외.

정확한 DELETE 순서는 clone의 실제 FK를 조회한 뒤 확정한다. 대략 child evidence/ledger/refund event에서 parent run/grant/order/subscription/license 순서지만, 실제 constraint를 보지 않고 문서에서 고정하지 않는다.

## Phase 5: 앱 통합 검증

clone reset 뒤 새 통합 앱으로:

- 기존 사용자가 로그인 또는 허용된 1회 재로그인 가능한지.
- 기존 계정은 남고 옛 이용권·잔액·결제·operation history는 보이지 않는지.
- 새 테스트 결제 전 access/credit이 없는지.
- 새 테스트 구독/top-up 뒤 grant/ledger/access가 정확히 생성되는지.
- Desktop quote/charge/refund와 Web/Admin 내역이 같은 원장을 보여주는지.
- 프로젝트·로컬 job 삭제가 금융 tombstone/outbox를 오인하지 않는지.

## Rollback rehearsal

- schema down migration을 개발 전환 rollback의 주 수단으로 사용하지 않는다.
- reset/migration 직전 dump를 별도 이름으로 보존한다.
- clone에서 migration/reset 뒤 dump restore를 수행해 사전 row count와 핵심 checksum이 돌아오는지 검증한다.
- 실제 개발 DB 전환 시 문제가 생기면 배포 앱/API를 중지하고 사전 dump를 복원하는 절차를 쓴다.

쉽게 말해 migration은 여러 table을 앞으로 바꾸므로 “한 단계 뒤로”가 원래 데이터 전체를 되살린다는 보장이 없다. dump restore는 변경 전 DB 자체를 통째로 되돌리는 복사본이므로 기존 사용자·로그인·금융 관계를 가장 확실하게 복구한다.

## 실제 개발 DB 적용 전 승인 게이트

사용자에게 다음을 모두 제시하고 별도 승인을 받는다.

- clone inventory와 삭제 예정 table/건수.
- 보존 사용자/auth table과 검증 결과.
- migration/reset/postcheck 실행 순서와 예상 downtime.
- 사전 dump 위치·복원 명령·복원 소요시간.
- 웹/API/Desktop 로컬 QA 결과.
- 남은 위험, 실제 ML/Build 5 HOLD 상태.

그 승인 전에는 실제 개발 DB migration, 금융 reset, 배포를 실행하지 않는다.
