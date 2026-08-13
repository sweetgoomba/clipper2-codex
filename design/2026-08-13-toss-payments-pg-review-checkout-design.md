# 토스페이먼츠 PG 심사용 익명 결제 전환 설계

- 작성일: 2026-08-13
- 상태: 사용자 승인 완료
- 문서 저장소/브랜치: `.codex/main`
코드 브랜치: 각 대상 저장소의 `feat/toss-payments-pg-review-checkout`

대상 저장소:

- `.codex`
- `web/clipper_web_api`
- `web/clipper_web_client`
- `web/clipper_infra`

관련 기록:

- `records/sessions/2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md`
- `design/2026-08-10-toss-pay-review-checkout-design.md`

## 1. 목적

현재 개발서버에 배포된 `pay.toss.im` 토스페이 직접 심사용 결제를 토스페이먼츠 PG V2 테스트 연동으로 교체한다.

이번 작업은 토스·카드사 심사자가 Clipper Google 로그인 없이 다음 화면과 테스트 결제를 검토하게 하기 위한 임시 심사 기능이다.

- 단건결제: Clipper 결제 페이지 안에 토스페이먼츠 주문서형 결제 UI 표시
- 정기결제: Clipper 자동결제 안내·동의 화면 뒤 토스페이먼츠 카드 등록창 표시
- 1년 상품: 정기결제가 아니라 단건결제로만 표시
- 결제 후: 테스트 결제 결과를 Clipper DB에 저장하고 공개 결과 페이지에 표시

이번 심사용 구현을 개발서버에 배포하고 토스 담당자에게 다시 확인을 요청한다. 심사 확인 뒤 실제 회원·구독·이용 권한·크레딧을 연결하는 전체 PG 연동은 별도 브랜치와 별도 계획으로 진행한다.

## 2. 확정 결정

### 2.1 심사용 임시 기능이다

- Clipper 로그인은 요구하지 않는다.
- 주문은 실제 회원과 연결하지 않는다.
- 익명 주문마다 서버가 무작위 `customerKey`를 만든다.
- `customerKey`는 Clipper 회원 ID가 아니며 개인 식별 정보를 포함하지 않는다.
- 테스트 Client Key와 Secret Key만 사용한다.
- 결제가 성공해도 이용권, 플러그인 권한, 크레딧을 지급하지 않는다.
- 정기결제 등록 후 최초 테스트 결제 1회만 실행한다.
- 다음 결제일 스케줄링과 반복 청구는 실행하지 않는다.
- 심사 종료 뒤 익명 심사용 API를 비활성화하거나 제거한다.

### 2.2 단건결제는 주문서형을 사용한다

요금 페이지의 `단건결제` 버튼은 토스 창을 즉시 열지 않고 Clipper 공개 checkout 페이지로 이동한다. checkout 페이지 안에서 토스 SDK가 결제수단과 약관 UI를 렌더링한다.

토스 담당자가 주문서형은 심사 대상이 아니라고 명시적으로 답한 경우에만 후속 변경으로 단건 UI를 결제창형으로 교체한다. 서버의 주문, 금액 검증, 승인, 결과 저장 계약은 유지한다.

### 2.3 정기결제는 자동결제 카드 등록창을 사용한다

정기결제는 일반 결제의 주문서형 UI로 처리하지 않는다. checkout 페이지에서 다음 정보를 먼저 보여주고 명시적 동의를 받은 뒤 `requestBillingAuth()`를 호출한다.

- 상품명
- 최초 결제금액
- 결제 주기
- 카드 등록 직후 최초 결제 1회가 실행된다는 사실
- 이번 기능은 테스트 심사용이며 실제 출금되지 않는다는 사실

카드 등록이 성공하면 서버가 `authKey`와 주문에 저장한 `customerKey`를 검증하고 빌링키를 발급한 뒤 같은 주문번호로 최초 결제를 승인한다.

### 2.4 공식 MCP는 개인 개발 도구로만 사용한다

토스페이먼츠 공식 MCP는 사용자 전역 `~/.codex/config.toml`에만 등록한다.

- 프로젝트 `.codex/config.toml`은 만들지 않는다.
- MCP 설정은 Git에 추가하거나 push하지 않는다.
- Claude Code를 사용하는 다른 팀원에게 설치를 요구하지 않는다.
- 프로젝트 소스와 빌드는 MCP 실행 여부에 의존하지 않는다.
- 설계와 구현 근거는 공식 문서 URL과 `.md` 원본으로 `.codex` 문서에 기록한다.

## 3. 현재 구현과 교체 경계

현재 `dev`에는 다음 토스페이 직접 구현이 있다.

- API 호스트: `https://pay.toss.im`
- 서버가 checkout URL을 만들고 Angular가 해당 URL로 이동
- `payToken`, `displayId`, `resultCallback` 기반 결과 처리
- 빌링키 생성 시 공급자가 먼저 checkout URL과 빌링키를 반환
- `payment_orders`, `payment_events` 저장
- 공개 결과 페이지와 비밀 조회 토큰
- 심사용 단건·정기결제 조합 제한

재사용한다.

- 공개 요금 페이지의 상품 선택과 버튼 조합
- 익명 주문 생성과 비밀 조회 토큰
- `payment_orders`, `payment_events`의 주문·이벤트 분리 원칙
- 공개 결과 조회와 제한된 상태 확인
- dev 전용 capability와 요청 횟수 제한
- 1·3개월 정기/단건, 12개월 단건 제한

교체한다.

- `TossPayProvider`와 `HttpTossPayProvider`
- `pay.toss.im` 요청·응답 DTO
- `payToken`, `displayId`, `resultCallback` 흐름
- 공급자 checkout URL로 즉시 이동하는 고객 웹 동작
- 토스페이 직접용 환경변수와 OpenAPI 계약

## 4. 사용자 흐름

### 4.1 단건결제

```text
/pricing
  -> 단건결제 클릭
  -> POST /payments/review/checkout
  -> 익명 주문과 receiptToken 생성
  -> /payment/checkout?receiptToken=... 이동
  -> GET /payments/review/orders/:receiptToken/checkout
  -> Clipper 상품·금액 + 토스 주문서형 결제수단·약관 렌더링
  -> 결제하기
  -> 토스/카드사 인증
  -> API successUrl로 브라우저 리다이렉트
  -> 서버가 orderId·amount·paymentKey 검증 및 승인
  -> payment_orders/payment_events 저장
  -> /payment/result?receiptToken=... 리다이렉트
```

`successUrl` 도착은 결제 인증 성공일 뿐 최종 결제 성공이 아니다. 서버의 승인 API가 `DONE`을 반환하거나 주문 조회로 `DONE`을 확인한 경우에만 주문을 `paid`로 기록한다.

### 4.2 정기결제

```text
/pricing
  -> 정기결제 클릭
  -> POST /payments/review/checkout
  -> 익명 주문과 무작위 customerKey, receiptToken 생성
  -> /payment/checkout?receiptToken=... 이동
  -> 상품·금액·결제 주기·최초 즉시 결제 안내
  -> 사용자가 동의 후 카드 등록 및 결제 클릭
  -> payment.requestBillingAuth({ method: "CARD", successUrl, failUrl })
  -> 토스 카드 등록창에서 카드 인증
  -> API successUrl로 authKey·customerKey와 함께 브라우저 리다이렉트
  -> 서버가 주문 customerKey와 일치 여부 확인
  -> POST /v1/billing/authorizations/issue
  -> billingKey 암호화 저장
  -> POST /v1/billing/{billingKey}로 최초 결제
  -> payment_orders/payment_events 저장
  -> /payment/result?receiptToken=... 리다이렉트
```

심사 주문의 빌링키는 실제 갱신 스케줄러에 등록하지 않는다. 같은 빌링키로 두 번째 결제를 자동 실행하지 않는다.

### 4.3 실패와 취소

- SDK 인증 취소·실패는 API `failUrl`을 거쳐 공개 결과 페이지로 돌아간다.
- 공급자 오류 메시지 원문을 그대로 사용자에게 표시하지 않는다.
- 사용자가 취소한 경우 `canceled`, 명확한 요청·승인 실패는 `failed`, 결과가 불확실하면 처리 중 상태를 유지한다.
- 실패 URL만으로 이미 승인된 결제를 실패로 덮어쓰지 않는다.
- 결과 페이지의 `다시 확인`은 결제를 다시 승인하지 않고 기존 주문 상태만 조회·복구한다.

## 5. 시스템 구조

```text
Angular pricing
  -> Review Payments API: 심사용 주문 생성
  -> Angular public checkout
       -> Toss Payments V2 SDK
       -> 주문서형 UI 또는 billing auth 창
  -> browser redirect to API success/fail endpoint
       -> ReviewPaymentsService
       -> TossPaymentsProvider
       -> https://api.tosspayments.com/v1
       -> PaymentOrdersRepository
  -> Angular public result
```

### 5.1 Angular 책임

- 공개 checkout 라우트 렌더링
- 서버가 반환한 상품명·금액·결제 방식 표시
- 토스 SDK를 Client Key로 초기화
- 단건 주문서형 결제수단·약관 렌더링
- 정기결제 안내와 사용자 동의
- 서버가 제공한 `orderId`, `customerKey`, `successUrl`, `failUrl`로 SDK 호출
- SDK 초기화·렌더링 실패의 안전한 안내

Angular는 결제 완료 상태를 결정하지 않는다. Secret Key, 빌링키, 서버 승인 응답 원문을 보관하지 않는다.

토스 SDK 호출은 `TossPaymentsSdkService` 한 곳에 격리한다. UI 컴포넌트가 전역 SDK 객체나 공급자 세부 타입에 직접 의존하지 않게 한다.

### 5.2 API 책임

- 심사용 capability와 테스트 키 검증
- 상품·결제 방식 조합 검증
- 주문번호, `customerKey`, 조회 토큰, 멱등키 생성
- checkout session의 정본 제공
- 리다이렉트 결과와 DB 주문 스냅샷 대조
- 단건결제 승인과 결과 불확실성 복구
- 빌링키 발급·암호화 저장과 최초 결제
- 주문·이벤트의 멱등 저장
- 결과 페이지로 303 리다이렉트

### 5.3 공급자 adapter 책임

새 `TossPaymentsProvider`는 다음 서버 API만 감싼다.

- `POST /v1/payments/confirm`: 단건결제 승인
- `GET /v1/payments/orders/{orderId}`: 승인 결과 복구·조회
- `POST /v1/billing/authorizations/issue`: `authKey`로 빌링키 발급
- `POST /v1/billing/{billingKey}`: 최초 자동결제 승인
- `DELETE /v1/billing/{billingKey}`: 실패·취소된 불필요 빌링키 정리

API Base URL은 코드에서 `https://api.tosspayments.com`으로 고정한다. 사용자 입력이나 환경변수로 공급자 호스트를 바꾸지 않는다.

## 6. 공개 API 계약

### 6.1 심사 capability

`GET /payments/review/config`

```json
{
  "mode": "checkout"
}
```

기존 `checkout | local_notice | legacy_purchase` 상태는 유지한다. PG 로컬 테스트가 가능한 설정에서는 로컬도 `checkout`을 반환하고, 키가 없거나 안전 조건을 충족하지 않으면 기존 fallback을 사용한다.

### 6.2 주문 생성

`POST /payments/review/checkout`

요청:

```json
{
  "planId": "plan-id",
  "paymentType": "one_time"
}
```

응답:

```json
{
  "checkoutUrl": "https://dev.clipperstudio.ai/payment/checkout?receiptToken=..."
}
```

응답 URL은 토스 URL이 아니라 Clipper 공개 checkout URL이다.

### 6.3 checkout session 조회

`GET /payments/review/orders/{receiptToken}/checkout`

단건 응답:

```json
{
  "paymentType": "one_time",
  "planName": "Pro 1개월",
  "months": 1,
  "amount": { "value": 19900, "currency": "KRW" },
  "orderId": "clipper-review-...",
  "customerKey": "clipper-review-...",
  "clientKey": "test_ck_...",
  "successUrl": "https://api.dev.clipperstudio.ai/payments/tosspayments/review/normal/success?receiptToken=...",
  "failUrl": "https://api.dev.clipperstudio.ai/payments/tosspayments/review/fail?receiptToken=..."
}
```

정기결제는 같은 계약에서 `paymentType`만 `recurring`이며 checkout 화면이 billing auth를 선택한다.

Client Key는 브라우저에 노출하도록 발급되는 공개 키다. Secret Key는 이 응답과 Angular 번들에 포함하지 않는다.

### 6.4 공급자 리다이렉트

- `GET /payments/tosspayments/review/normal/success`
- `GET /payments/tosspayments/review/billing/success`
- `GET /payments/tosspayments/review/fail`

세 엔드포인트는 브라우저 리다이렉트를 받고 서버 처리를 수행한 뒤 공개 결과 페이지로 `303 See Other`를 반환한다. 리다이렉트 파라미터가 없거나 주문과 일치하지 않으면 공급자 API를 호출하지 않는다.

### 6.5 결과 조회

기존 계약을 유지한다.

- `GET /payments/review/orders/{receiptToken}`
- `POST /payments/review/orders/{receiptToken}/reconcile`

reconcile은 기존 주문 조회와 불확실한 승인 복구만 수행한다. 새 결제 의도나 새 주문번호를 만들지 않는다.

## 7. 데이터 변경

이미 적용된 과거 migration 파일은 수정하지 않는다. 새 migration에서 출시 전 테스트 주문·이벤트를 비우고 토스페이먼츠 PG 의미에 맞는 열을 만든다.

- `pay_token`을 `payment_key`로 교체
- `review_user_id`를 `customer_key`로 교체
- `billing_key_enc` 유지
- 처리 중 복구용 `billing_auth_key_enc` 추가
- `confirmation_idempotency_key` 추가
- `billing_issue_idempotency_key` 추가
- `billing_charge_idempotency_key` 추가
- `last_transaction_key` 추가

각 멱등키는 주문 생성 시 UUID v4로 한 번만 만들고 같은 공급자 동작을 재시도할 때 재사용한다.

Secret Key, 평문 빌링키, 평문 `authKey`, 전체 카드번호, CVC는 DB와 `payment_events.payload`에 저장하지 않는다. `authKey`는 복구가 필요한 짧은 구간에만 `SecretCipher`로 암호화 저장하고 빌링키 발급이 확정되면 제거한다.

## 8. 상태와 멱등성

기존 상태를 유지한다.

```text
created
  -> checkout_ready
  -> billing_active
  -> payment_pending
  -> paid | canceled | failed
```

### 8.1 단건결제

1. success redirect가 주문을 잠근다.
2. DB의 `orderNo`, `amountKrw`와 리다이렉트 값을 비교한다.
3. `paymentKey`를 조건부 저장하고 `payment_pending`으로 claim한다.
4. DB에 저장한 금액으로 승인 API를 호출한다.
5. `DONE`, `orderId`, 금액이 모두 일치할 때만 `paid`로 전이한다.
6. timeout·5xx·응답 파싱 실패는 주문번호 조회로 확인한다.
7. 확인되지 않으면 실패로 추측하지 않고 `payment_pending`을 유지한다.

### 8.2 정기결제

1. billing success redirect가 주문을 잠근다.
2. 리다이렉트 `customerKey`와 DB 값을 비교한다.
3. `authKey`를 암호화 저장하고 같은 issue 멱등키로 빌링키를 발급한다.
4. 빌링키를 암호화 저장하고 `billing_active`로 전이한다.
5. 같은 charge 멱등키와 주문번호로 최초 결제를 한 번만 실행한다.
6. 승인 결과가 불확실하면 주문번호 조회로 확인한다.
7. `DONE`, `BILLING`, 주문번호, 금액이 일치할 때만 `paid`로 전이한다.

중복 브라우저 리다이렉트와 결과 새로고침은 같은 DB 주문과 같은 멱등키를 사용한다. 이미 `paid`인 주문은 공급자 승인 API를 다시 호출하지 않는다.

## 9. 보안 경계

심사용 checkout은 다음 조건을 모두 충족할 때만 활성화한다.

- `CLIPPER_ENV=dev` 또는 명시적으로 허용한 로컬 환경
- `TOSS_PAYMENTS_REVIEW_MODE=true`
- Client Key가 `test_ck_` 형식
- Secret Key가 `test_sk_` 형식
- dev에서는 안전한 HTTPS `WEB_BASE_URL`과 API return base URL
- 로컬에서는 loopback origin만 허용

추가 규칙:

- 주문 가격은 서버 상품 데이터만 사용한다.
- URL의 `amount`, `orderId`, `customerKey`를 DB와 비교한다.
- `receiptToken`은 256비트 무작위 값이며 DB에는 SHA-256 hash만 저장한다.
- `orderId`와 `customerKey`는 순차번호·이메일·전화번호·회원 ID를 사용하지 않는다.
- checkout 생성, session 조회, 결과 조회, redirect endpoint에 요청 횟수 제한을 둔다.
- 외부 오류 메시지는 길이와 문자 집합을 제한하고 사용자 화면에는 안전한 문구로 변환한다.
- Secret Key와 암호화 전 민감 값을 로그, 예외, 이벤트 payload에 남기지 않는다.

## 10. 환경변수

서버에만 설정한다.

```text
TOSS_PAYMENTS_CLIENT_KEY
TOSS_PAYMENTS_SECRET_KEY
TOSS_PAYMENTS_REVIEW_MODE
TOSS_PAYMENTS_RETURN_BASE_URL
WEB_BASE_URL
```

Client Key는 서버 config API가 checkout session에 포함해 브라우저로 전달한다. 정적 Angular environment에 키를 하드코딩하지 않는다. Secret Key는 API 컨테이너 밖으로 노출하지 않는다.

기존 항목은 PG 전환 배포에서 제거한다.

```text
TOSS_PAY_API_KEY
TOSS_PAY_REVIEW_MODE
TOSS_PAY_CALLBACK_BASE_URL
```

## 11. 로컬 개발

PG 심사용 기본 흐름은 공급자 서버 callback이 아니라 사용자의 브라우저 `successUrl`/`failUrl` 리다이렉트와 서버 승인 API를 사용한다. 따라서 로컬 Angular와 API가 모두 실행되고 문서용 또는 상점 테스트 키가 설정돼 있으면 공개 터널 없이 로컬 결제를 시도할 수 있게 구현한다.

- Angular: `http://localhost:4201`
- API: 기존 로컬 API origin
- success/fail URL: loopback API origin
- Secret Key: 로컬 API 환경변수

실제 카드사·브라우저 조합의 리다이렉트 호환성은 자동 테스트와 별도로 로컬 스모크 테스트한다. 로컬 설정이 없으면 결제 버튼은 유지하되 현재처럼 dev에서 테스트하라는 안내를 표시한다.

## 12. 오류 처리

| 상황 | 서버 처리 | 사용자 표시 |
| --- | --- | --- |
| SDK 로드 실패 | 공급자 호출 없음 | 결제 화면을 불러오지 못했다는 안내와 재시도 |
| 잘못된 receiptToken | 404 | 주문을 찾을 수 없음 |
| 금액·주문번호 불일치 | 승인 호출 금지, 보안 이벤트 | 결제를 확인할 수 없음 |
| 사용자 인증 취소 | canceled 이벤트 | 결제가 취소됨 |
| 인증 실패 | 안전한 오류코드 저장 | 다른 결제수단 또는 재시도 안내 |
| 승인 timeout·5xx | 주문번호 조회 | 확인 중, 다시 확인 가능 |
| 승인 결과 DONE | paid 멱등 저장 | 테스트 결제 완료 |
| 빌링키 발급 실패 | billing key 미발급 상태 유지 또는 terminal 실패 | 카드 등록을 완료하지 못함 |
| 최초 빌링 승인 실패 | billing key 유지, 주문 실패 또는 불확실 상태 | 최초 결제 실패·확인 중 구분 |
| DB 저장 실패 | 같은 주문·멱등키로 복구 가능 | 확인 중 |

## 13. 테스트 전략

### 13.1 API

- review mode와 test key prefix capability
- 허용된 기간·결제 방식 조합
- checkout session에 Secret Key가 없는지 검증
- 주문번호·금액·customerKey 불일치 시 공급자 미호출
- 단건 승인 성공·실패·timeout 후 조회 복구
- 중복 success redirect의 단일 승인
- billing authKey 발급과 암호화 저장·삭제
- customerKey 불일치 시 빌링키 미발급
- 최초 빌링 승인 성공·실패·불확실 결과 복구
- 이미 paid인 주문 재처리 금지
- fail redirect의 취소·실패 분류
- migration 적용·rollback과 민감정보 열 검증
- OpenAPI 파싱

provider 테스트는 실제 네트워크 대신 fetch를 대체해 URL, Basic 인증, 요청 body, Idempotency-Key, timeout, 안전한 오류 변환을 검증한다.

### 13.2 고객 웹

- 요금 페이지 버튼과 12개월 정기결제 미노출
- 단건결제 checkout 라우팅
- 주문서형 결제수단·약관 render 순서
- 서버 금액으로만 `setAmount()` 호출
- 정기결제 동의 전 `requestBillingAuth()` 미호출
- 동의 후 `CARD`, customerKey, success/fail URL 전달
- SDK 로드·렌더링 실패 안내
- 결과 페이지 paid/canceled/failed/processing 표시
- Secret Key 또는 평문 빌링키가 bundle 모델에 없는지 검증

SDK는 wrapper를 fake로 교체해 Angular 단위 테스트를 실행한다. 실제 토스 SDK와 카드창은 로컬·dev 수동 스모크 테스트로 검증한다.

### 13.3 검증 명령 기준

- API: Node 22, 전체 Jest와 `npm run build`
- 고객 웹: Node 22, 전체 Angular 테스트와 `npm run build`
- Infra: dev compose config와 배포 스크립트 정적 검증
- 빈 PostgreSQL 16에서 전체 admin migration 적용과 두 번째 실행 무변경 확인

## 14. 브랜치와 작업 격리

심사용 PG 전환은 각 코드 저장소의 최신 `dev`에서 시작한다.

```text
feat/toss-payments-pg-review-checkout
```

기존 `feat/access-credit-system-replacement` worktree와 로컬 커밋은 수정, rebase, reset, 삭제하지 않는다.

심사용 기능이 `dev`에 배포되고 토스 담당자의 확인을 받은 뒤, 실제 전체 PG 연동은 별도 기능 브랜치에서 진행한다. 전체 연동에서는 익명 `customerKey`를 제거하고 로그인 회원별 지속 가능한 `customerKey`, 구독, fulfillment, 갱신, 결제수단 관리와 연결한다.

## 15. 배포와 심사 전달

1. API·고객 웹·인프라 최신 `dev`에서 기능 브랜치 생성
2. 테스트 우선으로 PG 심사용 흐름 구현
3. 전체 테스트·빌드·migration·compose 검증
4. 각 기능 브랜치를 `dev`에 병합
5. m2-stage 개발서버 DB migration 및 API·고객 웹 배포
6. 로그아웃 브라우저에서 단건 주문서형 결제 완료 확인
7. 로그아웃 브라우저에서 정기결제 카드 등록과 최초 결제 완료 확인
8. `payment_orders`, `payment_events` 저장 확인
9. Secret Key와 평문 빌링키가 로그·DB 이벤트에 없는지 확인
10. 토스 담당자에게 PG 심사용 URL과 단건·정기결제 동선을 전달

## 16. 완료 기준

- 비로그인 사용자가 dev 요금 페이지에서 단건·정기결제 버튼을 볼 수 있다.
- 단건결제는 Clipper checkout 페이지 안에 토스페이먼츠 주문서형 UI가 표시된다.
- 정기결제는 안내·동의 뒤 토스페이먼츠 카드 등록창이 열린다.
- 1년 상품에는 단건결제만 표시된다.
- 두 흐름 모두 테스트 PG 결과가 DB와 결과 페이지에 일치하게 저장된다.
- 주문·금액·customerKey 변조와 중복 리다이렉트가 이중 결제나 오지급을 만들지 않는다.
- 이용권·플러그인 권한·크레딧은 지급되지 않는다.
- 전체 기능 브랜치와 Angular/Electron 버전은 변경되지 않는다.
- 토스 담당자에게 PG 화면으로 다시 검토를 요청할 수 있다.

## 17. 공식 근거

- AI 도구 연동 가이드: https://docs.tosspayments.com/guides/v2/get-started/llms-guide
- LLM Quick Reference: https://docs.tosspayments.com/guides/v2/get-started/llms-quick-reference
- 전체 문서 색인: https://docs.tosspayments.com/llms.txt
- 주문서형 결제: https://docs.tosspayments.com/guides/v2/payment-widget/integration
- 자동결제 카드 등록: https://docs.tosspayments.com/guides/v2/billing/integration
- JavaScript SDK V2: https://docs.tosspayments.com/sdk/v2/js
- 코어 API: https://docs.tosspayments.com/reference
- API 인증: https://docs.tosspayments.com/reference/using-api/authorization
