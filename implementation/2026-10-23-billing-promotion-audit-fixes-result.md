# 프로모션·크레딧·이용권·결제 감사 수정 결과

작성: 2026-10-23 KST. **아래는 수정 완료 당시의 기록**이다. A01–A17 및 독립 리뷰 추가 2건을 구현·검증했으며 당시에는 커밋·푸시하지 않았다.

> **2026-10-26 후속 완료:** 사용자 요청으로 세 수정 브랜치와 관리자 별도 `ae9b15d`를 최신 원격 dev에 병합·푸시했다. 현재 커밋·검증 상태는 [병합 기록](2026-10-26-billing-promotion-audit-dev-merge.md)을 따른다.

[기준 감사](2026-10-23-billing-promotion-baseline-audit.md) · [수정 계획](2026-10-23-billing-promotion-audit-fixes-plan.md) · [W17](../handoff/tasks/festival-voucher.md)

## 작업 상태와 범위

세 저장소 모두 작업 시작 시 최신 `origin/dev`에서 생성한 `fix/billing-promotion-audit-20261023` 브랜치다. 원본 checkout과 분리한 다음 경로에 **미커밋 변경**으로 보관한다.

| 저장소 | 기준 SHA | 작업 경로 |
|---|---|---|
| Web API | `db0ca36` | `.worktrees/billing-promotion-audit-20261023/web/clipper_web_api` |
| 회원 웹 | `fbd4573` | `.worktrees/billing-promotion-audit-20261023/web/clipper_web_client` |
| 관리자 웹 | `090d4e7` | `.worktrees/billing-promotion-audit-20261023/web/clipper_web_admin` |

경로의 루트는 `/Users/jina/project/adlight`다. 이번 요청은 감사 결과 수정이며 새 커밋·원격 반영을 요청받은 것은 아니므로 해당 단계는 수행하지 않았다. 새로운 DB 마이그레이션이나 API 엔드포인트, 결제 금액/할인/정산 정책 변경은 없다. 원본 서버를 이 작업 트리로 교체하지 않았으므로 현재 켜진 화면이나 개발 서버에 자동 반영된 상태가 아니다.

원본 API는 `dev`와 기존 `.env.example`, `auth.controller.ts` 수정 2개를 그대로 유지한다. 원본 회원 웹은 깨끗한 `dev`, 관리자 웹은 깨끗한 기존 `fix/member-promotion-access-summary-20261023` 브랜치를 유지한다. 관리자 원격 dev에 이전 `ae9b15d` 수정이 없었으므로 이번 A12에는 프로모션 출처 타입·라벨과 pending 상태의 기존 문제까지 함께 포함했다.

## 수정한 17건

아래 경로는 각 저장소 `src` 기준이며 테스트는 같은 기능 폴더의 spec에 추가/보강했다.

| ID | 적용한 수정 | 주요 구현·검증 |
|---|---|---|
| A01 | TypeORM UPDATE 결과를 실제 행으로 정규화하고 변경 0건은 실패로 반환 | `core/database/query-result.ts`; access/free-trial repository의 반환 경로. 실제 PostgreSQL의 0행·1행과 저장 객체 동일성 |
| A02 | 환불 항목 선점 전에 부모 환불 상태를 같은 SQL 잠금 안에서 확인. 취소/완료 상태를 늦은 응답이 덮지 못하게 함 | refund repository의 부모→항목 잠금, 조건부 UPDATE. 사전 조회 지연 중 철회 성공 시 외부 환불 호출 0회 |
| A03 | 환불 때문에 갱신을 중단한 구독은 자동/수동 신규 청구에서 제외 | subscriptions repository와 renewal service에서 이중 검사. 이미 시작된 청구는 결과 확인·복구 유지 |
| A04 | 미확정 업그레이드도 저장된 주문·상품 snapshot으로 결과를 확인하고 지급 재개 | orders repository, recovery scheduler, reconciliation, plan-changes의 기존 확정 경로 재사용. 재청구 없이 승인/지급 각 1회 |
| A05 | 미확정 갱신·업그레이드가 남아 있으면 구독 만료 확정을 보류 | renewal service. 청구 시작→회원 취소→복수 만료 worker→결제 성공/실패 순서 검사 |
| A06 | 즉시 상품 변경 시 소진된 이전 크레딧도 회수 상태로 고정 | credits repository의 active/depleted 대상 조회 및 공통 revoke 처리. 이후 작업 환급으로 되살아나지 않음; 원장 회수량은 실제 양수 잔액만 기록 |
| A07 | 관리자 이용권 기간 수정 시 다음 월 크레딧 지급일을 함께 재계산·저장 | access service/repository. 정확한 월 경계·월 중 종료·단축·무기한 연장·미처리 지급일 보존 검사; 현재 월 중복 지급 없음 |
| A08 | 미래 시작 이용권의 등급 변경 시 원래 미래 시작일 보존 | access service. 이용권·크레딧의 시작 시점을 함께 보존 |
| A09 | 잔액/견적 조회와 실제 크레딧 차감의 가용 조건 통합 | credits repository의 공유 SQL 조건. 업그레이드 진행 중 잠긴 잔액을 사용 가능으로 표시하지 않음; topup 등 별도 지급분 보존 |
| A10 | 크레딧 사용 기한은 실제 `expiresAt`으로 표시 | 회원 credits 화면. 월 혜택 종료일과 구분하고 null이면 무기한 표시 |
| A11 | 첫 결제가 확정 실패한 회원도 카드 변경 영역 표시 | dashboard에서 카드 관리와 상품 변경 조건 분리. 실제 변경 버튼은 서버 `changeAllowed` 반영 |
| A12 | 예약 취소·종료된 구독 대신 현재 유효 프로모션/관리자 이용권을 헤더에 표시 | 관리자 member-detail의 단일 selector와 출처 타입/라벨. 없음·pending·canceled·ended·stopped 및 정상 유료 상태 회귀 |
| A13 | 결제 재시도 성공 후 구독·이용권·잔액·카드를 함께 갱신 | dashboard의 기존 `refreshAccountProjections` 재사용. 중복 subscription-only 함수 제거 |
| A14 | 늦게 도착한 초기 조회가 QR 등록 후 최신 참여 내역을 덮지 못하게 함 | promotions load generation으로 결과·오류 반영 보호 |
| A15 | 혜택 모달을 열기 전에 등급 카탈로그 준비를 보장 | preview와 공유 catalog 요청을 함께 완료한 뒤 기존 모달 사용; 코드 변경 보호 유지 |
| A16 | 회수 안내에서 내부 캠페인명을 숨기고 실제 등록 코드 표시 | dashboard 템플릿과 노출 회귀 검사 |
| A17 | 환불 부모 선점 직후 중단돼 pending 항목이 남으면 오래된 작업으로 복구 | refund repository. 임대 만료·다중 worker·이전 worker 응답 배제·환불/회수 각 1회 검사 |

## 독립 리뷰에서 보강한 중단·만료 경계

### R1 — 만료 직전 승인된 업그레이드의 지연 복구

승인은 기존 이용권 만료 전 완료됐지만, 결과 확인 전에 월 지급 worker가 그 이용권을 종료하면 원래 수정본도 `paid / fulfillment failed`로 남았다. 실제 월 지급·재조정·지급 서비스와 PostgreSQL로 재현했다.

`replaceSubscriptionForImmediatePlanChange`와 repository의 교체 조건을 맞췄다. **구독 이용권이 자연 만료(`period_expired`)됐고, 승인 시각이 기존 이용 기간 안에 있는 경우**에는 확인된 주문에 따라 교체한다. 환불·관리자 회수·이미 교체된 이용권, 기간 밖 승인은 허용하지 않는다. 실제 월 지급 worker가 종료한 뒤 복구하고 중복 재조정해도 유효 교체 이용권·지급 크레딧·교체 이벤트는 각각 1건이다.

### R2 — 마지막 환불 항목 저장 직후 중단

PG 환불과 마지막 항목/주문 저장은 끝났지만 부모 환불 완료 저장 전에 중단되면 기존 선택 조건으로는 영구 누락됐다. `processing`, `partially_completed`, `manual_action_required` 중 **항목이 1개 이상이고 모두 완료된 건**을 기존 부모 실행 경로가 다시 선택하게 했다.

완료된 항목은 외부 환불을 반복하지 않고, 기존 실행 서비스가 합계·부모 완료·내부 효과를 마무리한다. 기존 실행 담당자와 completed/voided 상태 보호를 유지한다. 실제 DB에서 중단 후 동시·반복 scheduler 실행을 검증했으며 외부 환불·크레딧 회수 원장·내부 이벤트 모두 1회였다. 빈 환불, 미완료 항목, 이미 종결된 환불은 새 복구 대상에서 제외된다.

독립 API 리뷰는 최초 위 2건을 발견했고 수정 후 둘 다 해결됐음을 재검토했다. 회원/관리자 변경의 독립 리뷰에는 추가 수정 지적이 없었다. **이번 변경 범위의 리뷰 미해결 지적은 0건**이다.

## 구조·재사용 개선

- 실제 TypeORM 반환 형식 정규화를 공용 함수로 이동해 이용권·무료체험·크레딧 repository가 같은 계약을 지키게 했다.
- 프로모션 회수와 구독 교체 회수의 공통 상태/원장 처리를 `revokeGrants`로 통합했다. 대상 조회·원장 종류/참조 등 출처별 차이는 유지한다.
- 크레딧 가용성 SQL을 조회/합산/차감에 공유한다.
- 업그레이드 결과 복구는 기존 검증·확정·지급 경로를 재사용한다. PG 결과별 별도 복제 구현을 만들지 않았다.
- 화면의 현재 이용권 판단과 카드 관리 가능 여부를 각 책임에 맞는 selector로 분리했다. 결제 성공 후 갱신은 기존 공통 projection을 쓴다.
- 테스트용 DB 헬퍼는 제품 빌드에서 제외되는 `test/helpers/isolated-billing-postgres.ts`에 둔다. 명시한 로컬 Unix socket/port/user만 사용하고 실행별 무작위 DB 생성→기존 관리자 migration 적용→종료/삭제한다. 운영 환경 URL·자격 증명은 상속하지 않는다.

기존 repository 추상 경계를 유지했다. SOLID를 이유로 상속 계층이나 모든 결제 목적을 한 분기로 합치는 구조를 추가하지 않았다.

## 최종 검증

| 검사 | 결과 |
|---|---|
| API 전체 Jest | **430 suites / 4,490 tests 통과**, snapshot 5 통과. 10 suites / 69 tests는 opt-in 또는 기존 제외 |
| 추가 실제 PostgreSQL | **5 suites / 48 tests 통과**: access 13, credit availability 7, 기존 ledger 5, refund races 16, subscription recovery 7 |
| 회원 웹 전체 ChromeHeadless | **513/513 통과** |
| 관리자 웹 전체 ChromeHeadless | **2,393/2,393 통과** |
| API·회원·관리자 빌드 | 모두 통과 |
| 독립 API·화면 리뷰 | 확인된 추가 2건 수정 후 미해결 지적 0 |
| 신규 공용 DB 함수·부모 담당 PG spec ESLint | 통과 |
| 환불 담당 변경의 Prettier/집중 검사 | 통과; 기존 환불 12 suites / 103 tests 통과 |
| 세 저장소 `git diff --check` | 통과 |
| 관리자 raw color 검사 | 통과 |

69개 기본 제외 중 48개는 위 별도 DB 실행으로 확인했다. 나머지 21개 기존 제외 검사를 실행했다고 주장하지 않는다. 집중 검사의 수치는 전체 검사와 겹치므로 합산하지 않는다.

수정 전 실패도 보존했다: 회원 집중 9개 실패→101개 통과, 관리자 집중 5개 실패→96개 통과, A01 실제 DB 10개 실패→통과, A06/A09 DB 4개 실패→7개 통과. R1은 서비스/저장소 2개 및 실제 월 지급 포함 PG 1개 실패 후 통과, R2는 실제 DB 3개 실패 후 통과했다.

주요 실행 로그는 `/private/tmp/billing-final-api-full.log`, `billing-final-api-postgres.log`, `billing-final-ledger-postgres.log`, `billing-final-api-build.log`, `billing-client-full.log`, `billing-admin-full.log`, `billing-client-build.log`, `billing-admin-build.log`다. 검증 코드 자체는 각 작업 트리에 보관돼 재실행 가능하다. API Node 22.22.3, 웹 Node 24.19.0/ChromeHeadless를 사용했다.

### 다시 실행할 때

- API: `node node_modules/jest/bin/jest.js --runInBand`, `node node_modules/@nestjs/cli/bin/nest.js build`.
- 웹: `NG_BUILD_MAX_WORKERS=2 node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless`, 이어서 `build`. 두 웹 테스트는 Karma 기본 포트를 공유하므로 순서대로 실행한다.
- 실제 DB: 격리 로컬 PostgreSQL에 대해 `CREDITS_TEST_PG_SOCKET/PORT`, `SUBSCRIPTION_TEST_PG_SOCKET/PORT/USER`, `REFUND_TEST_PG_SOCKET/PORT/USER`를 지정한다. credits/access TEMP-table 검사는 `ledger_test` 사용자를 사용한다. 5개 spec 이름은 `access-mutations-postgres`, `credit-availability-postgres`, `credit-ledger-balance-postgres`, `payment-refund-races.postgres`, `subscription-recovery.postgres`다.

## 데이터·실행 환경과 남는 한계

검증은 `/private/tmp/clipper-billing-audit-k82_4cl7`의 별도 PostgreSQL만 사용했다. 새로운 회귀 DB의 잔존 수 0건을 확인하고 **검증 전용 서버를 정상 종료**했다. 기존 Docker·개발 서버·기존 로컬 및 운영 DB·실제 결제는 변경하지 않았다. 업무용 DB 초기화나 데이터 삭제는 이번 작업에 없다.

회원/관리자 빌드의 initial bundle 경고는 남는다(503.64kB / 860.44kB, 경고 기준 500kB, 오류 기준 1MB 미만). 이번 결함 수정과 별개의 번들 크기 문제다.

실제 Toss망의 승인·청구·환불, 실제 배포 revision, 운영 데이터, 다중 서버 부하·대량 XLSX, 데스크톱 전체 빌드는 이번 검증에 포함하지 않았다. 실제 PG와 같은 결과/지연/실패를 주는 가짜 결제 제공자로 복구 및 중복 방지를 검증했다. 이 결과가 모든 가능한 결함의 부재를 보증하지는 않는다.

기준 감사의 **로컬 저장 완료 수량 정산 신뢰 경계**와 **대량 성과 조회 집계 비용**은 별도 검토 사항으로 유지한다. 전자는 기존 정책과 증거 정의가 필요한 문제이며 이번에 임의 과금 규칙으로 바꾸지 않았다. 후자는 부하 측정 전 실제 성능 장애라고 단정하지 않는다.
