# 토스페이먼츠 PG 요금제 상향 동의 보강 및 수동 검증 인계

> **최신 상태 안내 (2026-08-26):** 이 문서는 기존 PG·수동 검증·환불 사전조사의 정본이다.
> 가격·무료체험·권한 구현 이후의 최신 HEAD, 테스트, worktree, 프로세스, DB 상태는
> `2026-08-26-toss-payments-pg-pricing-trial-entitlements-session-handoff.md`를 우선한다.

- 기록일: 2026-08-21 (Asia/Seoul)
- 상태: 승인된 무환불 PG Task 1~25와 후속 상향 동의·webhook 보강은 구현돼 있으나 전체
  PG 제품은 완료되지 않았다. 일부 핵심 test-key 시나리오, `BILLING_DELETED` transport,
  dedupe, installed-current와 과거 fingerprint 안전 처리는 확인했다. timestamp 역전은
  수정했고, exact issued-candidate/extant-previous DB 통합 테스트, 나머지 수동 시나리오,
  돈 환불/provider payment cancellation 설계·구현은 남아 있다
- 브랜치: 일곱 저장소 모두 `feature/toss-payments-pg-integration`
- merge/push/PR/dev 배포: 수행하지 않음
- 최신 선행 인계: `2026-08-19-toss-payments-pg-integration-session-handoff.md`
- 이번 세션 설계·계획:
  - API `docs/superpowers/specs/2026-08-21-subscription-upgrade-consent-and-dashboard-design.md`
  - API `docs/superpowers/plans/2026-08-21-subscription-upgrade-consent-and-dashboard.md`
  - API `docs/superpowers/plans/2026-08-21-payment-webhook-timestamp-invariant.md`

## 1. 이번 세션의 결론

전체 PG 연동 Task 1~25 위에 다음 보강을 완료했다.

1. Basic→Pro 즉시 상향 전에 서버가 계산한 정확한 차액을 사용자에게 보여준다.
2. 사용자가 그 금액이 적힌 버튼을 눌러야만 저장된 빌링키 결제가 시작된다.
3. 견적은 최대 5분 동안만 유효하고, 그 사이 구독 계약·기간·혜택 기준·결제수단이
   바뀌면 결제 전에 거부된다.
4. 같은 견적을 동시에 확정해도 결제 진입은 한 건만 성공한다.
5. 결제 완료 화면에 상품, 결제 금액, 주문번호, 결제시각을 표시한다.
6. 성공 직후 이용권·크레딧·구독·결제수단 projection을 모두 다시 읽어 새로고침 없이
   Pro 상태를 보여준다.
7. `/app`의 구독 결제 정보 영역을 요약, 결제수단, 요금제 변경 패널로 재배치해 큰 빈
   공간과 우측 쏠림을 없앴다.

테스트 모드의 카드 승인과 청구는 가상으로만 이루어지므로 카드사 문자나 실제 명세는
생기지 않았다. 이는 정상이다. 다만 세션 종료 직전 확인 결과, MID-scoped billing key로
실행한 결제 네 건은 토스 개발자센터 테스트 결제내역에 정상 표시됐고 webhook POST도
ngrok에 다섯 건 도착해 있었다. 가장 최근 `BILLING_DELETED`는 공식 문서 예시와 동일하게
`billingKey`와 `reason`을 `data` 아래에 담았지만, 기존 API parser가 문서를 오독해 두
필드를 최상위에서 찾으면서 400으로 거절했다. API는 이제 공식 `data` envelope만 받아
안전한 내부 DTO로 정규화하며 문서에 없는 평면 입력은 거부한다. 수정본으로 개발자센터
재전송을 실행해 HTTP 200과 fingerprint-only durable inbox 저장을 확인했다. 이때 행이
`received`에 머무르면서 webhook recovery의 cron 등록 누락을 발견했고, 매분 실행을
복원한 뒤 실제 다음 tick에서 `manual_review`/`WEBHOOK_BILLING_KEY_UNMATCHED`로 분류됐다.
새 disposable admin DB에는 과거 빌링키 record가 없으므로 unmatched는 예상된 결과다.

### 1.1 전체 범위의 현재 분류

여기서 `구현 완료`는 원래 승인된 **돈 환불 제외** Task 1~25와 이번 후속 보강 범위만
뜻한다. 전체 PG 제품 완료 여부는 사용자가 판단하며, 아래 네 범주를 섞지 않는다.

#### 구현 완료

- 최종 인증 사용자 OpenAPI, 결제 주문·구독 계약·billing auth attempt·durable webhook
  inbox migration/domain/repository와 Basic/Pro 월·연 상품 및 topup catalog
- widget/billing key set을 분리한 Toss Payments V2 provider, 고정 idempotency, 결과 재조회,
  crash/retry recovery, secret-safe persistence/projection과 exactly-once fulfillment
- 월·연 카드 구독 최초 결제, 카드·간편결제·계좌이체·가상계좌 topup 코드 경로, 고정 anchor
  갱신과 D+1/D+2 retry, cancel/resume, active/past_due 카드 변경 코드 경로
- 즉시 Basic→Pro 상향, 예약 변경·취소, server quote/5분 만료/source-state 결박/사용자 명시
  동의와 subscription/access/credit 원자 반영
- 고객 pricing/checkout/result/history/subscription/payment-method 화면, 관리자 payment/webhook/
  reconciliation console, infra 일곱 환경변수 fail-closed 검증과 desktop access-credit 호환
- `BILLING_DELETED` 공식 `data` envelope, fingerprint-only inbox, 매분 recovery cron,
  current/candidate/previous 분류·경합 방어와 exact-delivery dedupe
- 이번 timestamp bugfix: 운영 호출에서 claim과 terminal clock을 분리하고 retry 기준을 실제
  전이 시각으로 계산하며, 저장소가 `received_at <= processing_started_at <= processed_at`
  하한을 강제한다. migration은 추가하지 않았다

#### 검증 완료

- 이번 timestamp 수정의 RED 6건: 서비스 성공/재시도 시각 2건과 저장소 SQL ordering 4건이
  기존 코드에서 예상대로 실패했다. 수정 후 focused 98/98, API 전체 154/154 suites와
  1,330/1,330 tests, `npm run build`가 통과했다
- 이전 자동 검증: PostgreSQL 16 전체 43 migration, PG 경합·CAS·복구 probe, 고객 웹 전체
  170 tests/tsc/build, 관리자 224 tests/tsc/build, infra 71 tests/static Compose, desktop
  Angular/Electron/local API 전체 회귀와 build. 이들은 해당 기록 시점의 결과이며 이번
  timestamp 수정에서 다시 실행한 것은 API뿐이다
- 수동 test-key: Basic Monthly 최초 결제, 카드·토스페이 topup, distinct-card active 결제수단 변경,
  Basic→Pro 즉시 차액 결제, cancel/resume, Pro→Basic 예약 변경, 안전한 결제내역/projection
- `BILLING_DELETED`: 공식 envelope 200, fingerprint-only persistence, cron claim, unmatched
  manual review, 원본 exact replay dedupe, previous cleanup 뒤 과거 기록 안전 처리, installed
  current 직접 분류·제거. raw key/암호문은 출력·문서화·직접 DB 삽입하지 않았다

#### 구현 남음

- 돈 환불/provider payment cancellation은 원 Task 1~25에서 명시적으로 제외됐고 현재
  설계·API·서비스·provider cancel 호출·고객/관리자 UI가 없다. 전체 제품 범위에 포함하려면
  전액/부분 환불 가능 조건, Toss 취소 idempotency, 구독·access·이미 지급/소비된 credit
  처리, 권한, 감사, webhook/reconciliation, 실패 복구를 먼저 설계한 뒤 별도 구현해야 한다
- 공유 DB에 `178665`가 이미 적용된 경우에만 새 forward compatibility migration이 필요하다.
  기존 migration history를 고치거나 수정된 과거 migration을 재실행하지 않는다
- feature push/PR/dev merge, 개발서버 migration·배포는 코드 구현과 별도의 미실행 운영 작업이다

#### 검증 남음

- 실제 PostgreSQL repository와 제어 가능한 fake provider를 사용하는 exact issued-candidate와
  extant-previous `BILLING_DELETED` 통합 테스트. 상태는 service/repository를 통해 만들고 raw
  key 직접 INSERT, 운영 cleanup 지연, fault injection 수동 통과는 하지 않는다
- Basic Annual, Pro Monthly/Annual 최초 결제, topup의 카카오·네이버/계좌이체,
  가상계좌 발급·입금·만료, `past_due` 카드 변경, 실제 시간 기반 renewal/retry
- user-MID widget key의 `PAYMENT_STATUS_CHANGED`/`DEPOSIT_CALLBACK`과 duplicate delivery,
  provider 실제 데이터가 있는 관리자 console, 5분 견적 만료와 실제 동시 클릭
- 라이브키·카드사 심사 뒤 실제 승인/청구/알림, 개발서버 backup·migration dry-run·env
  preflight·배포 후 전체 체크리스트. 환불은 설계·구현 뒤 별도 검증 범위를 새로 정해야 한다

## 2. 저장소 기준점

2026-08-21 세션 종료 직전에 직접 확인한 값이다. 일곱 worktree 모두 clean이었다.

| 저장소 | 경로 | HEAD |
| --- | --- | --- |
| API | `.worktrees/clipper_web_api-toss-payments-pg-integration` | `b498b22004f3b1e3e838037fd1a02e8b558f516e` |
| 고객 웹 | `.worktrees/clipper_web_client-toss-payments-pg-integration` | `022f107185d6a5e0f9595bfa2876837bb338f25a` |
| 관리자 웹 | `.worktrees/clipper_web_admin-toss-payments-pg-integration` | `2ccb825d6a56c690a72a89244798caa1a8968b72` |
| infra | `.worktrees/clipper_infra-toss-payments-pg-integration` | `e6ae78f58b559cf3715f6acaecf6ac067a4e7930` |
| Desktop Angular | `.worktrees/clipper_angular-toss-payments-pg-integration` | `f0da4e4a4aca26bbf08ccbc16856b085c06b0404` |
| Electron | `.worktrees/clipper_electron-toss-payments-pg-integration` | `abdc5753741301f4bf22278a22ca8e20dc78ac24` |
| Desktop local API | `.worktrees/clipper_nestjs-toss-payments-pg-integration` | `8e131e3f601f981259c7bf00bb1a3001631c0fe5` |

다음 세션은 모든 경로에서 `git status --short --branch`와 `git rev-parse HEAD`를 다시
확인한다. 위 값은 인계 기준점이지 reset 대상으로 사용하지 않는다.

## 3. API 구현

### 3.1 명시적 차액 견적

신규 endpoint:

```text
POST /subscriptions/current/plan-change/quote
body: { billingProductCode }
```

즉시 상향 견적은 기존 `payment_orders`에 `purpose=subscription_upgrade`,
`status=created`인 주문을 만든다. 이 단계에서는 Toss provider 호출, 빌링키 복호화,
카드 청구가 모두 0회다.

견적 응답은 다음 사용자 표시 정보를 반환한다.

- 현재 상품명
- 변경 상품명·상품 코드
- 지금 결제할 차액
- 이번 기간 추가 크레딧
- 적용 시각
- 견적 주문번호
- 만료 시각

같은 source/target의 아직 유효한 `created` 견적은 재사용하고, 대체 견적을 만들 때 기존
`created` 견적은 만료시킨다. `created` 견적은 실제 돈의 불확실 상태가 아니므로 미해결
upgrade payment로 분류하지 않는다.

### 3.2 견적 상태 결박

`payment_orders.upgrade_quote_source_fingerprint char(64) NULL`을 추가했다. fingerprint는
다음 서버 상태의 SHA-256이다.

- 구독 계약 snapshot
- 현재 결제 기간
- 혜택 anchor
- 현재 billing-key fingerprint

견적 유효기간은 최대 5분이다. 확정 시 owner, target, status, purpose, 만료, source
fingerprint를 모두 다시 검증한다. 견적 후 카드 변경, 계약 변경, 기간 경계 진입, catalog
변경이 있으면 provider 호출 전에 거부한다.

### 3.3 확정 결제

기존 endpoint는 이제 견적 주문번호를 필수로 받는다.

```text
POST /subscriptions/current/plan-change
body: { billingProductCode, quoteOrderId }
```

서버는 사용자에게 제시한 그 주문의 금액과 크레딧 snapshot만 결제한다. 저장소의
조건부 상태 전이로 동시 확정 중 정확히 한 요청만 charge claim을 얻는다. 기존 billing
charge idempotency, provider reconciliation, 목적 제한 CAS, 원자적 구독·access·credit
fulfillment를 그대로 재사용한다.

성공 응답은 다음 형태다.

```text
{
  kind,
  subscription,
  payment: { productName, amountKrw, orderId, paidAt } | null
}
```

OpenAPI schema는 closed object로 갱신했고 `paymentKey`, `billingKey`, fingerprint,
provider payload를 외부 응답에 넣지 않는다.

### 3.4 마이그레이션 호환성 보강

로컬 5433 admin DB에는 다른 기능 세션이 만든 다음 legacy policy가 존재했다.

- `shortform_director.strategy`
- `shortform_director.video_plan`

기존 `1786650000000-AddOperationPluginEntitlements`는 이 두 키를 매핑하지 않아
`plugin_key SET NOT NULL`에서 실패했다. 행을 삭제하거나 마이그레이션을 건너뛰지 않고
두 키를 `shortform_director`로 보존 매핑하도록 보강했다.

주의: 기존 5433 DB의 전체 pending migration 실행은 과거 `shortform.create` run과 관련
credit ledger 삭제를 포함하므로 안전 검토가 차단했다. 이 세션에서는 기존 DB를 수정하지
않고 새 격리 PostgreSQL로 수동 테스트했다. 다음 세션도 백업과 명시적 승인 없이 기존
5433 DB에 전체 admin migration을 실행하면 안 된다.

`32f5f74`는 현재 로컬 5433에는 아직 적용되지 않은 `178665` migration 파일을 보강한
커밋이다. merge/deploy 전에 각 대상 환경의 migration history를 확인한다. 어떤 공유
환경에서든 `178665`가 이미 실행됐다면 수정된 과거 파일을 다시 실행하거나 history를
조작하지 말고, 필요한 데이터 보정은 새 forward migration으로 작성해야 한다.

## 4. 고객 웹 구현

### 4.1 견적 확인과 완료 정보

요금제 버튼을 누르면 먼저 quote endpoint를 호출한다. Basic→Pro 같은 즉시 상향이면
구조화된 확인창에 다음을 표시한다.

- 현재 상품
- 변경 상품
- 지금 결제할 금액
- 이번 기간 추가 크레딧
- `₩금액 결제하고 변경` 확인 버튼

확정 전에는 결제하지 않는다는 설명을 함께 표시한다. 성공 뒤에는 대시보드 안에 다음
완료 정보를 표시한다.

- 상품
- 결제 금액
- 주문번호
- 결제시각

409는 견적 만료·상태 변경으로, 503은 결제 결과 미확정으로 구분해 다시 확인할 행동을
안내한다.

### 4.2 projection 동기화

성공 뒤 `Promise.allSettled`로 다음 네 projection을 다시 읽는다.

1. current access
2. credit summary
3. current subscription
4. current payment method

일부 projection만 실패하면 성공한 결제 자체를 실패처럼 뒤집지 않고 부분 재조회 경고를
표시한다.

### 4.3 구독 카드 레이아웃

기존 한쪽 정렬 구조를 다음으로 분리했다.

- `subscription-overview`: 제목과 4개 요약 행
- `subscription-panels`: 결제수단 패널과 요금제 변경 패널
- `subscription-panel`: 각 기능의 독립 카드

760px 이하에서는 한 열로 접힌다. 기존 `.subscription-meta` 구조는 제거했다.

### 4.4 예약 변경 확인창의 현재 계약

Pro→Basic 같은 예약 변경 확인창에는 현재 다음 두 상세값만 표시된다.

- 변경 상품
- 다음 결제 금액

적용일은 상세 행이 아니라 `다음 갱신일부터 적용됩니다`라는 문장으로 안내한다. 예약 후
대시보드에는 실제 적용일과 예약 취소 버튼이 표시된다. 이는 이번 세션에서 발견한 버그가
아니라 현재 UI 계약이다. 날짜를 확인창에도 명시하려면 별도 UX 보강으로 다룬다.

## 5. 이번 세션 커밋

### API

- `a4f23c9` `docs(payments): design explicit upgrade consent`
- `cec6eaf` `docs(payments): bind upgrade quote state`
- `9bf7c97` `docs(payments): plan explicit upgrade consent`
- `f1cc503` `feat(payments): persist upgrade quote state`
- `a0f14bf` `feat(subscriptions): require upgrade quote consent`
- `314a84e` `feat(payments): expose upgrade quote confirmation`
- `b5e3002` `style(payments): format upgrade quote paths`
- `32f5f74` `fix(migrations): preserve director policy compatibility`
- `f01d38d` `fix(payments): accept nested billing deletion webhooks`
- `004af85` `fix(payments): enforce billing deletion envelope`
- `bf35efd` `fix(payments): schedule webhook inbox recovery`
- `d995a4d` `docs(payments): record billing deletion verification`
- `1e90575` `fix(payments): preserve webhook timestamp ordering`
- `6585e3a` `docs(payments): close timestamp fix plan`
- `b498b22` `docs(payments): record Toss Pay topup verification`

### 고객 웹

- `415813d` `feat(web): consume subscription upgrade quotes`
- `caadc6a` `fix(web): confirm exact plan upgrade charge`
- `bb87a9a` `fix(web): balance subscription dashboard layout`
- `022f107` `fix(payments): open redirect checkout in top-level window`

## 6. 자동 검증

### 6.1 API

- 전체 Jest: `154/154` suites, `1,328/1,328` tests PASS
- `npm run build`: PASS
- 변경 production TypeScript 대상 ESLint: 0 findings
- webhook controller/DTO 대상 ESLint: 0 findings
- 실제 관측 `BILLING_DELETED.data` envelope 회귀 테스트: RED 재현 후 PASS
- 실제 Nest schedule 등록·tick 실행 회귀 테스트: RED 재현 후 PASS
- 견적 service/repository focused: `84/84` PASS
- endpoint/OpenAPI 포함 focused: `8` suites, `188/188` PASS
- migration focused: `2/2` PASS
- diff check와 신규 응답 secret scan: PASS

테스트 로그의 의도된 error/warn fixture 메시지는 suite 실패가 아니다.

### 6.2 고객 웹

- 전체 Karma/ChromeHeadless: `170/170` PASS
- `tsc -p tsconfig.app.json --noEmit`: PASS
- production `npm run build`: PASS, initial bundle 약 `492.50 kB`, 신규 warning 없음
- API/mock/confirm/dashboard focused: `4` suites, `49/49` PASS
- dashboard focused: `22/22` PASS
- diff check와 browser secret scan: PASS

### 6.3 실제 PostgreSQL probe

새 PostgreSQL 16에서 admin migration `43`개를 적용했고 최신 timestamp는
`1787900000000`이었다. 실제 compiled service/repository를 사용한 probe 결과:

- quote 생성 중 provider 호출: `0`
- quote 생성 중 billing-key cipher 호출: `0`
- 동시에 같은 upgrade charge를 claim한 승자: `1`
- billing fingerprint 변경 뒤 확정: provider 전에 거부
- 만료 견적: 거부
- 다른 사용자 견적: 거부
- renewal order를 upgrade quote CAS가 만료시키지 못함
- `created` quote는 unresolved upgrade money로 분류되지 않음

probe용 컨테이너와 임시 스크립트는 종료 후 삭제했다.

## 7. 사용자가 직접 확인한 수동 테스트

### 7.1 기존 테스트 환경에서 확인

- Basic Monthly 최초 정기구독 결제와 상품 지급
- 100 Credits `₩5,900` 단건 카드 결제와 지급
- 다른 카드 등록을 통한 구독 결제수단 변경
- 최초 결제 중 한 차례 `503 initial payment result is pending` 응답 후 최종 지급 완료 수렴
- 토스 개발자센터 테스트 결제내역에서 billing 결제 네 건 확인
- ngrok inspector에서 등록 endpoint로 들어온 webhook POST 다섯 건 확인
- 가장 최근 `BILLING_DELETED`가 기존 API에서 400으로 거절된 사실과 공식 `data` payload
  형식 확인

### 7.2 이번 격리 DB에서 다시 확인

기존 user DB는 유지하고 admin/payment DB만 PostgreSQL 16 격리 컨테이너의 55420 포트로
연결했다. 같은 계정으로 로그인했을 때 활성 이용권이 없던 것은 계정은 user DB에,
구독·access·credit은 비어 있는 새 admin DB에 있었기 때문이다.

이 환경에서 사용자가 직접 확인한 결과:

1. Basic Monthly 최초 결제 `₩19,900` 성공
2. Basic→Pro 견적에 정확히 `₩20,000`, 추가 크레딧 `600` 표시
   - Basic 월 크레딧 `400`, Pro 월 크레딧 `1,000`
3. 금액이 적힌 확정 버튼을 누른 뒤 Pro Monthly 차액 결제 성공
4. 완료 영역에 상품, `₩20,000`, `upgrade_*` 주문번호, 결제시각 표시
5. 새로고침 없이 이용권·크레딧·구독 정보가 Pro로 갱신
6. 다음 자동 결제 취소 후 기간 종료까지 Pro 이용권 유지
7. 자동 갱신 다시 시작 후 active 상태와 다음 결제일 복원
8. Pro→Basic Monthly 예약 변경, 현재 Pro 유지, 실제 적용일과 예약 취소 버튼 표시
9. 예약 취소 후 Pro 계약 유지
10. 결제내역에 Basic `₩19,900`과 Pro 상향 `₩20,000` 두 건만 표시
11. 자동 결제 취소/재시작과 예약/예약 취소는 결제내역을 만들지 않음
12. 변경된 구독 결제 정보 레이아웃에서 모든 동작 수행 가능

공용 테스트키의 승인 결과는 가상 승인이다. 로컬 DB의 `paid`는 test PG 성공을 뜻하며
실제 카드 한도·잔액·명세를 변경하지 않는다. 카드사 문자나 앱 알림이 없던 것은 정상이다.

## 8. 아직 남은 검증

### 8.1 수정본 webhook 재전송 결과와 남은 분류 검증

delivery 자체는 이미 확인했다. 다섯 POST가 ngrok에 도착했고, 그중 직접 검사한 최신
`BILLING_DELETED`는 다음 provider envelope였다. 실제 빌링키 값은 기록하지 않는다.

```text
{ eventType, createdAt, data: { billingKey, reason } }
```

토스 공식 webhook JSON 예시와 실제 ngrok 요청은 모두 `billingKey`와 `reason`을 `data`
아래에 둔다. 최초 parser가 필드 설명을 최상위 구조로 오독한 것이 400의 원인이었다.
정정된 parser는 공식 `data` envelope만 받아 내부의 기존 평면 DTO로 정규화하고, 문서에
없는 최상위 `billingKey`/`reason` 입력은 거부한다. raw billing key는 durable inbox에
저장하지 않고 HMAC fingerprint만 저장하는 기존 보안 경계를 유지한다.

새 disposable migrated DB로 API를 다시 실행하고 개발자센터에서 해당 delivery를 재시도한
결과는 다음과 같다.

- 개발자센터 delivery 상태: 성공
- ngrok/API 응답: HTTP 200
- durable inbox: `BILLING_DELETED` fingerprint-only row 한 건
- 최초 상태: `received`
- 추가로 발견한 결함: `PaymentWebhookRecoveryScheduler.recover()`의 cron 등록 누락
- 수정: 기존 background recovery와 같은 매분 Nest cron 연결
- 실제 다음 tick 결과: `manual_review`, `WEBHOOK_BILLING_KEY_UNMATCHED`

마지막 결과는 결함이 아니다. 재전송 대상 빌링키는 이전 테스트 DB에서 생성됐지만 replay는
결제 record가 없는 새 disposable admin DB로 받았으므로 일치 대상을 찾을 수 없다. 이
검증으로 transport, 공식 envelope parsing, fingerprint-only persistence, cron claim과
terminal classification까지 확인했다.

같은 날 후속 세션에서 다음을 추가 확인했다.

- 성공 delivery에는 개발자센터 `다시 시도` 버튼이 제공되지 않았다. 이는 2xx 성공 뒤에는
  실패 재전송을 하지 않는 Toss 정책과 일치한다. 따라서 기존 개발자센터 성공 기록은
  그대로 두고 ngrok Agent API로 captured request를 정확히 한 번 replay했다.
- 원본과 replay의 transmission ID/time/retry count, body SHA-256, `eventType`, `createdAt`,
  `data` key set과 reason이 모두 같았고 둘 다 API HTTP 200이었다.
- replay 뒤 original dedupe row는 계속 한 건이었다. row ID, fingerprint,
  `manual_review`/`WEBHOOK_BILLING_KEY_UNMATCHED`, retry count 0, received/processed/updated
  timestamp가 전부 변하지 않았다.
- 같은 55420 DB에서 Basic Monthly 최초 결제 `sub_b0a06d714cff47579625111fd87e2e3a`가
  `paid`/fulfillment `succeeded`로 끝났고 active access 한 건과 400-credit grant 한 건을
  만들었다.
- 다른 카드의 distinct fingerprint로 정상 결제수단 변경을 완료했다. old key는 정상
  previous cleanup을 통해 Toss DELETE됐고 새 `BILLING_DELETED`가 개발자센터 성공,
  ngrok/API HTTP 200, inbox `processed`/error 없음으로 끝났다.
- provider webhook은 synchronous previous cleanup이 `succeeded`로 pair를 지운 약 246ms
  뒤 도착했다. 따라서 exact previous slot이 남아 있지는 않았고 completed attempt의
  candidate/current history를 통한 installed-or-previous reclassification fallback으로
  안전하게 처리됐다. 이를 `previous slot 직접 관찰`로 과장하지 않는다.
- 정상 lifecycle이 만든 installed current fingerprint를 read-only로 조회하고 메모리에서만
  복호화·fingerprint 검증한 one-use probe로 Toss test DELETE를 호출했다. raw key와 암호문은
  출력·저장하지 않았고 probe 파일도 즉시 제거했다. 새 delivery는 개발자센터 성공,
  ngrok/API HTTP 200, inbox `processed`/error 없음이었으며 subscription current fingerprint가
  제거되고 removal status가 `succeeded`가 됐다.
- 세 durable `BILLING_DELETED` row 모두 normalized payload에 `billingKey`나 provider `data`
  object를 저장하지 않았고 deposit ciphertext도 없다.

현재 남은 exact slot 범위는 다음과 같다.

- issued candidate: 정상 browser redirect는 key 발급 직후 같은 요청에서 atomic completion을
  수행하므로 안정적인 candidate interval을 만들 수 없었다.
- extant previous: 관찰된 provider ordering은 local previous cleanup 완료 뒤 webhook을
  전달해 exact previous pair가 이미 지워져 있었다.
- 두 slot 모두 raw key 직접 DB 삽입, DB 상태 조작, 인위적 fault injection으로 통과시키지
  않았다. 현재 unit 회귀는 두 분류를 포함한다. 후속 TODO는 실제 PostgreSQL repository와
  제어 가능한 fake provider로 service/repository를 경유해 두 상태를 만들고 terminal 전이를
  확인하는 통합 테스트다. 정상 운영 cleanup 순서를 늦추지는 않는다.

추가 관찰로 current-key row의 `processed_at`이 DB `received_at`보다 약 28ms 빨랐다.
`processNext()`가 async claim SQL 실행 전에 application time을 잡고 receipt는 DB time을
사용해 같은 초 경합에서 생긴 timestamp invariant 결함이다. terminal 분류와 dedupe에는
영향이 없었다. 이번 후속 수정에서 production clock을 claim/terminal로 분리하고 retry를
terminal time 기준으로 계산했으며, repository SQL이 receipt/lease timestamp 하한을 강제하게
했다. 서비스 회귀 2건과 저장소 SQL 회귀 4건은 RED를 확인한 뒤 GREEN이 됐고, 최종 API
154/154 suites, 1,330/1,330 tests와 build가 통과했다.

이 확인에는 새 widget key가 필수는 아니다. 반면 공용 `_docs` widget pair로 수행한 topup의
`PAYMENT_STATUS_CHANGED`, 가상계좌의 `DEPOSIT_CALLBACK`을 사용자 MID에서 의미 있게
관찰하려면 user-MID-scoped widget key 발급 후 별도 테스트가 필요하다.

같은 날 토스페이 topup 수동 검증에서 다음을 추가 확인했다.

- Chrome 151의 PC 결제에서 휴대폰 토스페이 인증은 끝났지만 provider iframe이 최상위
  `localhost:4201` 창을 `localhost:3000` callback으로 이동하려다 user-activation/cross-origin
  제한으로 차단됐다. CSP 메시지는 report-only였고 실제 실패는 `SecurityError`였다.
- 일회성 redirect checkout에 Toss SDK 공식 옵션 `windowTarget: 'self'`를 추가했다. embedded
  결제수단 선택 UI는 유지하고, `결제하기` 이후 provider 인증만 최상위 창에서 진행한다.
  billing authorization 흐름은 변경하지 않았다.
- 고객 웹 TDD에서 옵션 누락으로 focused test가 먼저 실패했고, 수정 후 focused 3/3, 전체
  170/170 tests와 production build가 통과했다. 커밋은
  `022f107 fix(payments): open redirect checkout in top-level window`이다.
- 새 500-credit 토스페이 주문 `topup_3a04e581d598488b9f2cef14c53db54d`가 callback을 거쳐
  `paid`/provider `DONE`/fulfillment `succeeded`로 끝났다. 결제수단은 `간편결제`, provider는
  `토스페이`, 승인 금액은 KRW 27,900이었다.
- 해당 주문에는 active 500-credit grant 한 건, +500 ledger 한 건, checkout-created와 paid
  event가 각각 한 건만 생겼다. 공용 `_docs` widget pair이므로 연관 webhook inbox row는 0건이며
  user-MID payment webhook 검증으로 과장하지 않는다.

### 8.2 키 또는 운영 조건이 생겨야 가능한 것

- user-MID-scoped widget key로 `PAYMENT_STATUS_CHANGED`, `DEPOSIT_CALLBACK` 실제 수신
- webhook inbox dedupe/retry/manual-review의 운영 화면 확인
- 라이브키와 카드사 심사 완료 뒤 실제 카드 승인·청구·카드사 알림 확인

webhook endpoint는 이미 다음으로 구현돼 있다.

```text
POST /payments/tosspayments/webhook
```

로컬 확인 시 ngrok target은 API가 듣는 3000 포트여야 한다. 개발자센터에는 HTTPS ngrok
URL 뒤에 위 path를 붙이고 세 이벤트를 구독한다. billing key와 widget key set의 귀속과
각 이벤트 발생 조건을 구분해 기록한다.

### 8.3 선택적·운영성 수동 테스트

아래는 자동 테스트와 PostgreSQL probe로는 검증했지만 실제 시간 경과 또는 별도 장애
주입을 사용한 사용자 수동 테스트는 하지 않았다.

- 5분 견적 만료 후 재견적 UX
- 동일 확정 버튼의 실제 다중 클릭/동시 요청
- 다음 결제일의 자동 월간·연간 갱신
- 갱신 실패, D+1/D+2 retry, `past_due`, `stopped`, 카드 변경 후 미결제 복구
- 가상계좌 발급, 입금 callback, 만료
- 연간 상품의 최초 결제와 예약 변경 조합
- 운영자 payment/webhook/reconciliation console의 실제 provider 데이터 확인

이 항목들은 현재 구현 미완료를 의미하지 않는다. 자동 회귀 범위에는 포함돼 있으나
별도 key set 또는 시간·장애 제어가 필요한 production-like 수동 확인이 남았다는 뜻이다.

## 9. 브랜치 통합·배포에서 남은 일

- feature branch push
- dev merge 또는 PR
- access-credit 등 선행 feature와의 merge 순서 확정
- 개발서버 DB backup과 migration dry-run
- 대상 공유 DB에서 `178665` 적용 여부 확인과 필요 시 새 forward compatibility migration
- 개발서버 API/client/admin/infra 배포
- 배포 환경의 일곱 Toss 환경변수와 canonical URL preflight
- 배포 전 repository-backed `BILLING_DELETED` exact candidate/extant-previous 통합 테스트
- 배포 후 test-key 체크리스트 재실행과 widget key가 발급되면 payment/deposit 이벤트 확인

사용자 지시 없이 위 작업을 자동 수행하지 않는다. 환불 API, provider payment cancellation,
임의 운영 데이터 수정도 범위 밖이다.

## 10. 로컬 DB와 종료 상태

- 기존 localhost:5433 admin DB는 이번 세션에서 수정하지 않았다.
- 해당 DB의 migration 기록은 관찰 당시 `28`개, 최신 `1786600000000`이었고 subscription
  테이블이 없었다.
- 전체 pending migration에는 legacy run/ledger 삭제가 포함돼 자동 실행이 차단됐다.
- 수동 테스트용 `clipper-upgrade-manual-pg-20260821` 컨테이너와 그 테스트 데이터는 사용자
  확인 후 삭제했다. 별도 volume이 없어 복구되지 않는다.
- 후속 수동 검증을 위해 API 3000과 고객 웹 4201, disposable PostgreSQL 55420이 실행
  중이다. admin/payment만 55420을 사용하며 기존 user와 release DB는 각각 기존 연결을
  사용한다.
- 가상계좌 due-date 수정 build 반영을 위해 API를 다시 시작했다. 현재 API PID는 `71764`,
  실행 session은 `4592`이며 health는 HTTP 200이다. 고객 웹 4201도 HTTP 200, ngrok inspector 4040과
  PostgreSQL 55420 listener도 유지 중이다.
- 55420에는 Basic Monthly active subscription, paid initial order, active access와 400-credit
  grant, completed initial/card-change attempt가 있다. current-key 분류 검증으로 subscription
  billing fingerprint는 제거됐고 removal status는 `succeeded`다.
- 같은 55420에서 500-credit 토스페이 topup 한 건이 `paid`/`DONE`/fulfillment `succeeded`로
  완료됐고 grant/ledger/event 중복이 없었다. 이후 생성된 별도 1000-credit checkout 한 건은
  마지막 관찰 시 `checkout_ready`/fulfillment `pending`이므로 성공 범위에 포함하지 않는다.
- 뒤이어 카카오페이 1000-credit, 네이버페이 100-credit, 퀵계좌이체 100-credit topup도
  각각 `paid`/`DONE`/fulfillment `succeeded`로 완료됐다. 각 주문의 grant, ledger,
  checkout-created/paid event는 모두 정확히 한 건이었다. 퀵계좌이체는 provider/local method
  `계좌이체`로 저장됐고 easy-pay provider는 없었다.
- 사용자가 별도로 띄운 ngrok은 수정하거나 종료하지 않았다.
- 테스트키가 들어 있는 `.env` 값은 읽거나 이 문서에 기록하지 않았다.

## 11. 다음 세션 첫 작업

1. 이 문서와 `2026-08-19-toss-payments-pg-integration-session-handoff.md`를 읽는다.
2. 일곱 feature worktree의 branch, HEAD, dirty state를 다시 확인한다.
3. 첫 목표는 **돈 환불/provider payment cancellation 설계**다. 구현이나 provider 취소 호출부터
   시작하지 않는다.
4. 아래 14절의 과거 환불 관련 문서를 다시 검색·읽고, 현재 코드·DB·OpenAPI·Toss 최신 공식
   계약과 대조한다. 과거 문서를 그대로 채택하지 않고 `유효`, `폐기/충돌`, `미결정`,
   `법률·운영 확인 필요`로 나눈다.
5. 다음 세 개를 같은 말로 취급하지 않는다.
   - 다음 자동결제 취소: 현재 이용기간은 유지하고 다음 갱신만 중단
   - 돈 환불/provider payment cancellation: 실제 승인 금액의 전액·부분 취소
   - 내부 크레딧 반환·복구: 실패한 서비스 작업에 사용된 크레딧을 원래 grant로 복원
6. Superpowers brainstorming으로 요구사항과 정책 결정을 한 번에 하나씩 확인하고, 2~3개 설계
   대안을 비교한다. 사용자가 설계를 승인하기 전에는 구현 계획이나 코드를 확정하지 않는다.
7. refund 설계와 별개인 exact candidate/extant-previous `BILLING_DELETED` repository 통합 테스트,
   user-MID webhook, 가상계좌 발급·입금·만료, branch 통합·배포는 잔여 TODO로 유지한다.
8. 기존 5433 admin DB에는 backup과 명시적 승인 없이 전체 migration을 실행하지 않는다.
9. 공유 DB에 `178665`가 이미 적용됐다면 history를 고치지 말고 새 forward migration을
   설계한다.
10. merge/deploy/live charge/refund/provider cancel은 각각 별도 사용자 승인을 받는다.

## 12. 다음 세션 시작 프롬프트

```text
Using Superpowers.

토스페이먼츠 PG 연동 작업을 이어서 진행해줘.

먼저 아래 인수인계 문서를 완전히 읽고 현재 worktree/프로세스/DB 상태를 read-only로
재확인해줘.
- /Users/jina/project/adlight/.codex/main/2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md
- /Users/jina/project/adlight/.codex/main/2026-08-19-toss-payments-pg-integration-session-handoff.md

이번 세션의 첫 목표는 돈 환불과 provider payment cancellation 설계야. 구현부터 시작하지
말고, 예전에 환불을 설계하거나 논의하다 남긴 문서를 먼저 모두 찾아서 현재 상태를 파악해줘.
아래 문서를 우선 확인하되 `rg`로 환불/refund/결제취소/payment cancellation/CANCELED/
PARTIAL_CANCELED를 다시 검색해서 빠진 기록도 찾아줘.
- /Users/jina/project/adlight/.codex/main/2026-08-19-clipper-product-policy-business-meeting.md
- /Users/jina/project/adlight/.codex/main/2026-08-19-clipper-pg-product-policy-meeting-brief.md
- /Users/jina/project/adlight/.codex/main/2026-08-18-toss-payments-pg-integration-design.md
- /Users/jina/project/adlight/.codex/main/2026-08-18-toss-payments-pg-integration-session-handoff.md
- /Users/jina/project/adlight/.codex/implementation/2026-08-12-billing-product-catalog-foundation-plan.md
- /Users/jina/project/adlight/.codex/records/sessions/2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md

과거 문서를 그대로 가져다 쓰지는 마. 현재 코드, OpenAPI, DB 모델, 구현된 구독·topup·credit
lifecycle과 토스페이먼츠 최신 공식 문서를 read-only로 대조해서 다음처럼 분류해줘.
1. 지금도 그대로 참고할 수 있는 정책·제약
2. 현재 구현과 충돌하거나 폐기해야 하는 가정
3. 아직 결정되지 않은 제품·운영 선택
4. 법률·약관·회계·CS 담당자 확인이 필요한 항목
5. 새 설계에서 추가로 다뤄야 하는 누락

`다음 자동결제 취소`, `실제 결제금의 전액·부분 환불(provider 취소)`, `실패한 작업의 내부
크레딧 반환·복구`는 서로 다른 개념이므로 절대 섞지 마. 현재 CANCELED/
PARTIAL_CANCELED 관찰·경고 기능이 실제 환불 실행 기능은 아니라는 것도 확인해줘.

Superpowers brainstorming 방식으로 먼저 현황과 과거 설계의 유효성을 요약한 뒤, 필요한
질문을 한 번에 하나씩 물어봐. 2~3개 설계 대안과 장단점을 제안하고 내가 설계를 승인하기
전에는 구현하지 마. 설계 범위에는 최소한 다음을 포함해줘.
- 월간·연간 구독, topup, 즉시 상향 차액, 가상계좌의 전액·부분 취소 가능 조건
- 청약철회/디지털콘텐츠 사용 개시, 경과 기간, 사용·잔여 크레딧을 반영하는 정책 경계
- 구독·access·credit grant/ledger를 언제 유지·회수·조정할지
- Toss 취소 멱등성, 응답 유실, webhook/reconciliation, 재시도와 중복 방지
- 사용자 접수, 운영자 검토, 최종 승인, CS 창구/SLA, 감사 로그와 보존기간
- 요청·승인·완료·실패 단계의 이메일/알림톡 등 외부 알림
- 관리자/고객 UI, 권한, 보안, 수동 운영 fallback

법률 판단을 임의로 확정하지 말고 공식 최신 자료와 법률 검토가 필요한 항목을 분리해줘.
이번 첫 단계에서는 DB 변경, migration, provider 취소/환불 호출, live 결제, merge, deploy를
하지 마.

raw billing key는 출력·문서화하지 마. 이전 대화에 사용자가 붙여 넣은 test key 값도
재사용하거나 기록하지 마.

API feature worktree는
/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration 이고
현재 기준 HEAD는 a47a971 이야. 고객 웹 HEAD는
fd71462 이야. 새 세션에서
branch/HEAD/dirty state를 다시 확인해줘.

종료 시점에는 API 3000, 고객 웹 4201, disposable PostgreSQL admin DB 55420이 실행
중인 listener를 확인했다. 이 세션의 최종 sandbox HTTP probe는 환경 제약으로 응답을
확인하지 못했으므로 새 세션에서 건강 상태를 반드시 다시 확인해. 기존 localhost:5433
admin DB에는 backup과 내 명시적 승인 없이 접속하거나 pending admin migration을 실행하지 마.

환불 설계와 별개로 남아 있는 BILLING_DELETED exact candidate/extant-previous repository
통합 테스트, user-MID payment/deposit webhook, 가상계좌 발급·입금·만료 검증은 TODO에서
지우지 말되 이번 세션의 첫 작업으로 끌어오지 마.
```

## 13. 2026-08-21 가상계좌 만료시각 correction

- 주문서형 SDK는 유지했다. 결제창형이나 legacy direct payment 방식으로 바꾸지 않았다.
- 최초 승인과 snapshot이 없는 first-observed reconciliation에서 `order.createdAt + 24h`를
  저장하던 구현을 제거하고 Toss provider 응답의 `virtualAccount.dueDate`를 공통 검증 후
  `dueAt`으로 저장한다.
- due date는 offset이 있는 ISO timestamp, 주문 생성 이후, 최대 90일 이내여야 한다. 위반 시
  secret/account snapshot을 저장하지 않고 기존 `TOPUP_VIRTUAL_ACCOUNT_RESPONSE_INVALID`
  reconciliation 경계로 보낸다.
- 주문서형 widget 요청에 실제로 사용되지 않던 `CheckoutSession.virtualAccountDueDate`는
  API interface, OpenAPI, 고객 웹 model/mock/test에서 제거했다. DB migration은 없다.
- API focused 126/126, 전체 154/154 suites 및 1,334/1,334 tests, 변경 production source
  ESLint, API build가 통과했다. 고객 웹 전체 170/170 tests와 production build도 통과했다.
- API commit은 `b80b31e`, 고객 웹 commit은 `fd71462`다.
- 체크리스트 범위 명확화 문서 commit은 API `a47a971`이다.
- 수정 전 자체 24시간 계산으로 생성된 실제 가상계좌 row는 없고 이 코드는 배포된 적도 없다.
  따라서 legacy waiting/expired row backfill이나 migration은 추가하지 않았고 55420의 다른
  수동 검증 데이터도 삭제하지 않았다.
- 공용 `_docs` widget pair에는 사용자가 관리할 수 있는 결제 UI가 연결되지 않아 가상계좌
  노출 및 페이코 제거는 수행하지 않았다. user-MID 주문서형 key/variant가 준비된 뒤 결제
  어드민에서 가상계좌를 추가하고 페이코를 제거해야 한다.
- 실제 가상계좌 발급, `WAITING_FOR_DEPOSIT`, `DEPOSIT_CALLBACK`, `DONE`, exactly-once 지급,
  만료는 아직 미검증이다. 입금 완료 후 돈 환불/provider cancellation도 설계·구현되지 않았다.

## 14. 세션 종료와 환불 설계 사전 조사

- 환불만을 위한 완성된 상세 설계서나 실행 계획은 찾지 못했다. 대신 아래 문서에 중단된 정책
  논의와 범위 경계가 흩어져 있다. 다음 세션에서 전체 검색을 다시 실행해 누락 여부를 확인한다.
  - `2026-08-19-clipper-product-policy-business-meeting.md` 7절: 환불 자격, 기한, 전액·부분,
    경과 기간, 사용 크레딧, 연간 중도 종료, 승인자, 통지, 보존기간과 CS 최소 항목
  - `2026-08-19-clipper-pg-product-policy-meeting-brief.md` 6절·10.10절: 미구현 기능 목록과
    수동 접수/수동 Toss 처리, 앱 접수+운영 처리, 자동·반자동 처리의 세 선택지
  - `2026-08-18-toss-payments-pg-integration-design.md` 14.3절·15절·22절: 외부
    `CANCELED`/`PARTIAL_CANCELED`는 현재 관찰·경고만 하며 provider 취소, access/credit 자동
    조정, 환불 UI/승인은 의도적으로 제외했다는 현재 경계
  - `2026-08-12-billing-product-catalog-foundation-plan.md` Phase 8: 법률 검토된 환불 산식과
    운영 runbook이 필요하다는 roadmap 수준의 메모
  - `2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md`: 환불·해지·알림을 후속으로
    남긴 짧은 기록이며 상세 설계는 아님
- 과거 문서에서 계속 참고할 수 있는 핵심은 `정책·법률·운영 승인 전에 임의 산식을 코드로
  확정하지 않는다`, `돈 환불과 내부 크레딧 복구를 분리한다`, `중복 취소와 감사 이력을
  설계한다`는 경계다. 구체 산식, 자동화 수준, 승인 권한, CS/알림 채널은 아직 결정된 것으로
  보지 않는다.
- 다음 세션은 과거 문서의 유효성 평가와 현재 구현 대조부터 시작하며, 사용자 승인 전에는
  환불 구현이나 provider 취소 호출을 하지 않는다.
- 종료 직전 read-only 확인에서 API worktree는 `a47a971e744d07b5b3d0435ee4c17133e526a615`,
  고객 웹 worktree는 `fd714624a80813b53fae2fdc4a155f6bf1250bbb`였고 둘 다 clean이었다.
  `lsof`로 3000·4201·55420 listener를 확인했지만 sandbox 내부 `curl`은 연결할 수 없었으므로
  프로세스의 실제 건강 상태는 다음 세션에서 새로 확인한다.

## 15. 2026-08-24 가격·무료체험·권한 정책 구현

환불 설계에 들어가기 전에 전략팀 가격표와 사용자가 확정한 무료체험·크레딧·플러그인
정책을 PG feature branch의 API, 고객 웹, 관리자 웹에 반영했다. 설계와 실행 계획은 다음에
남아 있다.

- `docs/superpowers/specs/2026-08-24-pricing-trial-and-entitlements-design.md`
- `docs/superpowers/plans/2026-08-24-pricing-catalog-and-discounts.md`
- `docs/superpowers/plans/2026-08-24-free-trial-credit-and-plan-lifecycle.md`
- `docs/superpowers/plans/2026-08-24-pricing-and-catalog-clients.md`

### 15.1 확정 가격과 표시 할인율

| 요금제 | 월간 결제 | 월 크레딧 | 연간 일시 결제 | 연간 월 환산 | 전략팀 표시 할인율 | 실제 할인율(반올림) |
|---|---:|---:|---:|---:|---:|---:|
| Basic | 5,900원 | 400 | 58,800원 | 4,900원 | 15% | 17% |
| Pro | 10,900원 | 1,000 | 82,800원 | 6,900원 | 30% | 37% |
| Business | 29,900원 | 4,000 | 234,000원 | 19,500원 | 35% | 35% |

- 연간 상품은 12개월분을 한 번에 승인하며 크레딧은 월별로 지급한다.
- 할인율 표시 모드는 전역 설정 `actual | configured`다. `actual`은 월간 가격과 연간 총액으로
  계산하며 고객 화면에는 정수 반올림 값을, 관리자 화면에는 실제·설정·최종 적용 값을 함께
  보여준다. 초기 모드는 `actual`이다.
- 고객 가격 페이지는 카드별 토글 대신 상단의 전역 월간/연간 selector 하나로 세 요금제를
  함께 전환한다. 연간 카드에는 월 환산액과 연간 일시 결제 총액을 모두 표시한다.
- recurring product와 top-up pack의 가격·크레딧·활성 상태, 요금제 entitlement mode와
  allowlist, 무료체험 정책, 할인율 모드를 관리자 화면에서 편집한다. Trial은 내부 무료체험
  tier이므로 유료 recurring product 생성·활성화·checkout 대상이 될 수 없다.

### 15.2 무료체험·크레딧·플러그인 정책

- Trial은 계정당 한 번 400 크레딧을 지급하며 만료하지 않는다. 무료체험 잔액은 유료 전환
  때 삭제하지 않고, 유료 크레딧을 먼저 사용한 뒤 Trial 잔액을 fallback으로 사용한다.
- 유료 월 크레딧은 다음 월 benefit window로 이월하지 않는다. 연간 결제도 월별 benefit
  window마다 해당 요금제의 월 크레딧을 새로 지급한다.
- Trial과 Basic은 서로 독립된 allowlist이며 초기 허용 키는 각각 정확히
  `shortform_url`, `shortform_paste`, `shortform_prompt`, `dialog_highlight`,
  `dance_highlight`다. 새 플러그인은 자동 허용하지 않는다.
- Pro와 Business는 `all` 모드다. 현재와 미래의 **등록된** 플러그인은 자동 허용하지만 알 수
  없는 임의 키는 fail closed한다. 두 tier의 권한 정책은 나중에 독립적으로 바꿀 수 있다.
- 활성 유료 access가 있으면 그 tier의 플러그인 정책이 우선한다. 유료 access가 끝난 뒤
  Trial 잔액이 남아 있으면 Trial 권한으로 돌아가며, Trial을 renewable subscription처럼
  취급하지 않는다.
- 같은 결제 주기에서 rank가 높은 요금제로 바꾸는 것은 즉시 변경이고, 하향 또는 월간↔연간
  변경은 예약 변경이다. 유료 top-up은 half-open 유료 이용기간
  `start <= now < end` 안의 현재 유료 구독에만 허용한다.

### 15.3 구현·검증 결과

- API: `feature/toss-payments-pg-integration` at
  `a85e2fa665a8497ff66c4939e417fb10fc48df8d`, tracked clean.
  Node 22에서 161 suites, 1,486 tests와 build가 통과했다.
- 고객 웹: 같은 branch at `2fbd5e9c6c43b1efefd334cf57dc6bc80254cb43`.
  207 tests와 production build가 통과했다. 세션 시작 전부터 있던 untracked `build/`는
  삭제·수정·stage하지 않고 보존했다.
- 관리자 웹: 같은 branch at `cbf7c52a20555ff736e0be7711dd3645fdfe59c4`, clean.
  258 tests와 production build가 통과했다. build는 성공했지만 기존 initial bundle budget을
  39.58 kB 초과한다는 warning은 남아 있다.
- 최종 교차 리뷰에서 Critical/Important/fix-caused Minor는 없었다. 별도 reviewer가 Trial 유료
  상품 차단, 현재 유료 구독 기반 top-up gating, 고객/관리자 계약을 다시 검증했다.
- 실제 브라우저 evidence는 고객 1280px/390px, 관리자 actual/manual/failure/reload/Trial을
  포함한 9장이다. customer CDP 기록 53개 URL에서 Toss 요청은 0건이었고, 관리자 실패/지연
  evidence도 server-authoritative reload를 확인했다. 경로는 API worktree의
  `.superpowers/sdd/2026-08-24-pricing-and-catalog-clients/task-5-visual-evidence/`다.
- disposable PostgreSQL 16의 55462에서 admin migration 45개(최신 178810), user migration
  4개를 적용하고 admin down/up, 실제 partial unique constraint, 두 연결을 이용한 무료체험 및
  크레딧 동시성 경쟁을 확인했다. 검증 컨테이너는 종료 후 삭제했으며 live Toss 요청은 하지
  않았다.

### 15.4 설계상 판단과 남은 hardening

- 관리자 UI는 기존 API의 plugin PUT과 tier PATCH를 사용한다. `all → allowlist` 전환 때 비어
  있지 않은 검증된 목록을 먼저 dormant row로 저장하고 mode를 바꾸므로 실패해도 실제 권한은
  `all`로 유지되고 authority를 reload한다. 보안상 안전하지만 두 HTTP 요청을 하나의 DB
  transaction으로 묶은 것은 아니다. dormant 설정 변경 자체도 all-or-nothing이어야 한다면
  추후 결합 endpoint가 필요하다.
- review에서 남긴 deferred minor는 controller/summary snapshot/lifecycle/legacy quote의 더 좁은
  회귀 테스트와 기존 관리자 bundle warning이다. transactional debit authorization,
  paid-period eligibility, annual grant scheduling, legacy quote 안전성의 필수 동작은 구현 및
  전체 회귀 테스트로 확인했다.
- SDD ledger와 task report는 최종 판단·명령·리뷰 근거이므로 환불 설계 인수인계가 끝날 때까지
  삭제하지 않는다.

## 16. 2026-08-24 worktree·프로세스·DB 정리 상태

- 모든 `access-credit` worktree를 제거했다. `feat/access-credit-system-replacement` 브랜치는
  API/client/admin/infra repository에 안전하게 남겼으며 삭제하지 않았다. 그 worktree에서
  필요했던 credit/access 설계는 현재 PG branch의 더 최신 catalog, ledger, grant,
  entitlement, lifecycle 구현에 포함돼 있다.
- 다음 임시 review/foundation worktree도 사용자 승인 후 제거했다. 브랜치는 삭제하지 않았다.
  - `clipper_infra-toss-payments-pg-review-checkout`
  - `clipper_web_api-toss-payments-pg-review-checkout`
  - `clipper_web_client-toss-payments-pg-review-checkout`
  - `clipper_web_api-billing-product-catalog-foundation`
- 남은 `.worktrees`는 PG integration 7개, 별도 `meme-overlay` 작업 5개,
  `clipper_web_api-operator-jwt-expiry-test` 1개뿐이다.
- read-only 재확인 시 API 3000은 PID 23631, 고객 웹 4201은 PID 65249이며 둘 다 HTTP 200이다.
  두 프로세스의 cwd는 feature worktree가 아니라 각각 `web/clipper_web_api`와
  `web/clipper_web_client`다. 따라서 현재 listener가 이번 feature HEAD를 서비스한다고
  간주하면 안 된다. admin dev listener는 없다.
- Docker에는 기존 PostgreSQL 16 개발 DB 세 개만 있다: admin 5433, release 5434, user 5435.
  read-only transaction으로 확인한 migration 상태는 admin 28/최신 1786600000000,
  user 7/최신 1786100000000, release 2/최신 1782790000000이다. 이번 세션에는 기존 개발 DB에
  migration이나 쓰기를 실행하지 않았다. 이전 55420 및 이번 55462 disposable DB는 없다.
- 다음 본 작업은 14절의 경계를 유지한 돈 환불/provider payment cancellation 설계다.
  구현, provider 취소 호출, merge, push, deploy는 아직 하지 않았다.
