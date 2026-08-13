# Toss Pay Review Checkout Design

> **공급자 전환 기록 (2026-08-13):** 이 문서는 `docs-pay.toss.im`과 `pay.toss.im`을 사용하는 토스페이 직접 연동 기준으로 작성됐고, 해당 구현은 현재 개발서버의 심사용 결제로 배포돼 있다. 실제 연동 대상은 토스페이먼츠 PG로 전환하기로 결정했다. 이 문서는 배포된 기존 구현의 역사적 기록으로만 유지하며 PG 구현 설계로 사용하지 않는다. 전환 범위와 현재 상태는 [`2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md`](../records/sessions/2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md)를 따른다.

작성일: 2026-08-10

상태: 사용자 승인 완료 (2026-08-10)

대상 저장소:

- `.codex`
- `web/clipper_web_client`
- `web/clipper_web_api`
- `web/clipper_infra`

작업 브랜치: `feat/toss-pay-review-checkout`

## 1. 목적

Toss Pay 계약 전 심사를 위해 `https://dev.clipperstudio.ai/pricing`에서 Clipper Google 로그인 없이 Toss Pay 테스트 결제창을 열 수 있게 한다.

공용 테스트 API Key를 사용해 다음 두 결제 경로를 실제로 연결하고 결과를 Clipper DB에 안전하게 저장한다.

- 일반 결제(단건 결제)
- 빌링키 기반 자동 결제 등록 및 최초 테스트 결제 1회

이번 단계는 결제 심사에 필요한 결제창과 결과 저장까지만 구현한다. 결제 완료 후 이용권·크레딧 자동 지급은 연결하지 않는다.

## 2. 배경과 현재 상태

현재 공개 요금 페이지의 모든 `구매 요청` 버튼은 `/app/purchase`로 이동한다. `/app/**`에는 인증 가드가 걸려 있으므로 비로그인 사용자는 Google 로그인으로 이동한다.

로그인 후 표시되는 `/app/purchase`는 Toss Pay 결제가 아니라 입금자명을 입력하고 무통장 입금 구매 요청을 제출하는 기존 수동 처리 화면이다. 백엔드의 `POST /purchase-requests`도 JWT 인증을 요구한다.

Toss Pay 담당자가 요청한 심사 조건은 다음과 같다.

1. 요금 페이지의 구매 버튼에서 정기결제창을 열 수 있어야 한다.
2. 단건결제창도 검토할 수 있도록 단건 결제 버튼이 필요하다.
3. 심사 기간에는 Clipper 로그인 없이 결제창을 열 수 있어야 한다.
4. 1년 상품은 정기결제가 아니라 단건결제로 연결해야 한다.

## 3. 확정된 제품 동작

### 3.1 버튼 구성

| 플랜 기간 | 정기결제 | 단건결제 |
| --- | --- | --- |
| 1개월 | 표시 | 표시 |
| 3개월 | 표시 | 표시 |
| 12개월 | 표시하지 않음 | 표시 |

12개월 정기결제는 UI에서 숨기는 것에 그치지 않고 서버에서도 거부한다.

### 3.2 비로그인 심사 동선

- 심사 모드가 활성화된 dev 환경에서는 결제 시작 API를 인증 없이 호출할 수 있다.
- Clipper 로그인을 우회하는 것이며, Toss Pay 결제창 내부의 Toss 사용자 인증은 정상적으로 진행한다.
- 실제 서비스 오픈 전에는 심사 모드를 끄고 로그인 사용자 기반 결제 흐름으로 교체한다.

### 3.3 결제 완료 범위

- 단건결제는 Toss Pay 자동 승인 결과를 검증하고 저장한다.
- 정기결제는 빌링키 활성화를 검증한 뒤 최초 테스트 결제 1회를 즉시 승인하고 저장한다.
- 다음 회차를 청구하는 반복 결제 스케줄러는 구현하지 않는다.
- 구매 요청 생성, 운영자 승인, 이용권 발급, 크레딧 지급은 호출하지 않는다.

## 4. 선택한 아키텍처

`clipper_web_api`에 기존 `billing` 모듈과 분리된 `payments` 모듈을 추가한다.

분리 이유:

- 기존 `billing` 모듈은 무통장 구매 요청과 수동 라이선스 발급을 관리한다.
- Toss Pay 주문 상태와 공급자 콜백은 별도의 생명주기와 보안 경계를 가진다.
- 추후 결제 완료 후 fulfillment를 연결할 때 `payments`가 기존 라이선스 발급 use case를 호출하는 방향으로 확장할 수 있다.
- Toss 전용 요청·응답은 provider adapter 내부에 가두어 상위 결제 정책과 UI에 누출하지 않는다.

의존 방향:

```text
Angular pricing/payment result UI
  -> web_api payments controller
    -> payment application service
      -> payment orders/events repository
      -> active plan lookup
      -> Toss Pay provider port
        -> Toss Pay HTTP adapter
```

`payments` 모듈은 현재 활성 플랜을 조회하기 위해 `billing` 모듈의 플랜 조회 경계를 사용한다. 가격, 상품명, 기간, 크레딧 수량은 클라이언트 요청값이 아니라 서버 DB에서 결정한다.

## 5. 프런트엔드 설계

### 5.1 요금 페이지

각 버튼은 `planId`와 결제 방식만 결제 시작 API에 전달한다.

- `one_time`: 단건결제
- `recurring`: 정기결제

요금 페이지는 서버의 공개 capability API로 결제 UI 모드를 먼저 확인한다.

- `checkout`: dev에서 안전한 심사 설정이 모두 충족된 상태다. Toss Pay 버튼을 표시하고 실제 테스트 checkout을 시작한다.
- `local_notice`: `WEB_BASE_URL`이 loopback(`localhost`, `127.0.0.1`, `::1`)인 로컬 실행이다. dev와 동일한 Toss Pay 버튼 구성을 표시하지만, 클릭하면 API를 호출하지 않고 `토스페이 결제는 로컬 환경에서 사용할 수 없습니다. 실제 결제 테스트는 dev 환경에서 진행해 주세요.`라고 안내한다.
- `legacy_purchase`: stage/prod 또는 안전한 심사 설정이 충족되지 않은 비로컬 환경이다. 기존 `구매 요청` 버튼과 `/app/purchase` 동선을 유지한다.

capability 조회가 실패하면 안전하게 `legacy_purchase`로 처리한다. 로컬에서도 1·3개월은 정기/단건, 12개월은 단건 버튼을 표시해 배포 UI와 동일한 구성을 확인할 수 있어야 한다.

버튼 클릭 중에는 중복 요청을 막고 로딩 상태를 표시한다. 성공 응답의 `checkoutUrl`로 `window.location.assign()`을 사용해 브라우저 전체를 이동한다. Toss Pay 결제창을 iframe으로 열지 않는다.

결제 시작 실패 시 현재 요금 페이지에 오류를 표시하며 로그인 페이지나 기존 `/app/purchase`로 이동하지 않는다.

### 5.2 공개 결과 페이지

다음 공개 라우트를 추가한다.

- 결제 완료/처리 중 페이지
- 결제 취소/실패 페이지

결과 페이지는 URL에 포함된 임의 조회 토큰으로 Clipper 주문 상태만 조회한다. 주문 UUID나 `orderNo`만으로 공개 조회할 수 없게 한다.

브라우저 리다이렉트와 서버 콜백 순서가 엇갈릴 수 있으므로 결과 페이지는 Clipper API를 제한된 시간 동안만 재조회한다. 이는 Toss Pay 문서의 필수 요구가 아니라 결과 처리 순서 차이를 흡수하기 위한 Clipper UX 정책이다.

- 첫 조회에서 최종 상태면 즉시 표시한다.
- 처리 중이면 2초 간격으로 최대 10회(총 20초)만 재조회한다.
- 제한을 넘으면 무한 폴링하지 않고 `결제 확인 중`과 수동 새로고침 안내를 표시한다.

표시 정보:

- 테스트 결제 여부
- 플랜명과 기간
- 결제 방식
- 결제 금액
- Clipper 주문번호
- `결제 확인 중`, `테스트 결제 완료`, `취소`, `실패` 상태

이용권 또는 크레딧이 지급됐다는 표현은 표시하지 않는다.

## 6. API 설계

다음 경로와 필드명을 OpenAPI 계약의 기준으로 사용한다.

### 6.1 `GET /payments/review/config`

응답:

```json
{
  "mode": "checkout"
}
```

API Key나 내부 설정값은 반환하지 않는다. `mode`는 `checkout | local_notice | legacy_purchase` 중 하나다. loopback `WEB_BASE_URL`이면 `local_notice`, dev·심사 모드·`sk_test_` 키·안전한 HTTPS callback/web base URL이 모두 유효하면 `checkout`, 그 밖에는 `legacy_purchase`를 반환한다. 이 표시 모드와 무관하게 실제 checkout API의 보안 조건은 완화하지 않는다.

### 6.2 `POST /payments/review/checkout`

요청:

```json
{
  "planId": "uuid",
  "paymentType": "one_time"
}
```

응답:

```json
{
  "checkoutUrl": "https://pay.toss.im/..."
}
```

정책:

- 공개 capability와 동일한 안전 조건을 모두 충족할 때만 인증 없이 허용한다.
- 활성 플랜만 구매할 수 있다.
- 정확한 허용 조합은 1·3개월의 `one_time | recurring`과 12개월의 `one_time`이다. 그 밖의 기간·방식 조합은 400으로 거부한다.
- 클라이언트가 가격, 상품명, 크레딧 수량을 전달하지 않는다.
- IP당 10분에 최대 10개의 checkout 생성만 허용한다.

### 6.3 `POST /payments/toss/normal/result-callback`

일반 결제 callback V2에서 다음 필드를 받는다. Toss Pay가 추가 필드를 보내도 무시할 수 있어야 한다.

- `status`
- `payToken`
- `orderNo`
- `payMethod`
- `amount`
- `discountedAmount`
- `paidAmount`
- `paidTs`
- `transactionId`

### 6.4 `POST /payments/toss/billing/result-callback`

빌링키 처리 결과에서 다음 필드를 받는다. Toss Pay가 추가 필드를 보내도 무시할 수 있어야 한다.

- `action`
- `userId`
- `billingKey`
- `payMethod`

### 6.5 callback 공통 정책

콜백 엔드포인트는 브라우저 인증에 의존하지 않는다. 콜백만 신뢰해 주문을 완료하지 않고 Toss Pay 상태 조회로 주문번호, 상태, 금액을 검증한다.

심사 모드가 꺼져도 이미 시작된 주문의 결과가 유실되지 않도록 callback 엔드포인트는 `TOSS_PAY_API_KEY`가 설정된 동안 유지한다. `TOSS_PAY_REVIEW_MODE`는 비로그인 checkout 생성만 제어한다.

중복 콜백은 멱등하게 처리한다. 이미 처리한 이벤트라면 추가 승인이나 상태 변경 없이 성공 응답한다.

### 6.6 `GET /payments/review/orders/:receiptToken`

추측 불가능한 조회 토큰으로 제한된 주문 요약만 반환한다.

응답:

```json
{
  "status": "checkout_ready",
  "paymentType": "one_time",
  "planName": "Pro 1개월",
  "months": 1,
  "amountKrw": 19900,
  "orderNo": "clipper-review-...",
  "testPayment": true,
  "errorMessage": null
}
```

`status`는 `created | checkout_ready | billing_active | payment_pending | paid | canceled | failed` 중 하나다. `errorMessage`는 사용자에게 공개해도 되는 정제된 메시지만 사용한다.

결과 조회는 IP당 1분에 최대 60회로 제한한다. 한 브라우저의 정상적인 10회 제한 폴링은 허용하면서 비정상 조회는 제한한다.

반환하지 않는 정보:

- Toss API Key
- 빌링키
- 내부 암호문
- 전체 provider callback payload
- 내부 DB 식별자와 운영 정보

### 6.7 `POST /payments/review/orders/:receiptToken/reconcile`

취소 URL로 돌아온 브라우저가 비밀 조회 토큰을 사용해 한 번의 provider 상태 재검증을 요청한다. Toss Pay가 `PAY_CANCEL`을 반환한 경우에만 `canceled`를 저장하고, `PAY_COMPLETE`가 확인되면 `paid`가 우선한다. 확인할 수 없는 상태나 일시 장애는 결론을 추측하지 않고 처리 중 상태로 둔다.

### 6.8 브라우저 return/cancel URL

Toss Pay에 전달하는 브라우저 복귀 URL은 공개 Angular 라우트이며, 주문에 매핑된 `receiptToken`을 포함한다.

- 성공/처리 중: `https://dev.clipperstudio.ai/payment/result?receiptToken=<opaque-token>`
- 취소/실패: `https://dev.clipperstudio.ai/payment/cancel?receiptToken=<opaque-token>`

브라우저가 취소 URL에 도착했다는 사실만으로 금융 상태를 `canceled`로 변경하지 않는다. 화면에는 취소 안내를 표시하되, DB의 `canceled` 상태는 Toss Pay 상태 조회로 취소가 확인된 경우에만 기록한다. 이후 provider 검증에서 `PAY_COMPLETE`가 확인되면 항상 `paid`가 우선한다.

## 7. 데이터 모델

결제 데이터는 `admin` Postgres에 저장한다. 컬럼은 snake_case를 사용하고 TypeORM 엔티티에 실제 컬럼명을 명시한다.

### 7.1 `payment_orders`

핵심 필드:

- 내부 주문 UUID
- 가맹점 `order_no`(고유)
- 결제 방식 `one_time | recurring`
- 심사용 익명 Toss `user_id`(정기결제만 사용)
- `plan_id`
- 주문 시점 플랜명, 개월 수, 가격, 크레딧 수량 스냅샷
- Toss `pay_token`
- 암호화한 `billing_key_enc`
- 결제수단
- 요청 금액과 실제 결제 금액
- Toss 거래 ID
- Toss 모드(`TEST` 예상)
- 오류 코드와 안전한 오류 메시지
- 상태
- 생성, checkout 준비, 빌링 활성화, 결제 완료, 실패 시각
- 공개 조회 토큰 해시

주문 상태:

```text
created
  -> checkout_ready
  -> billing_active       (recurring only)
  -> payment_pending
  -> paid

terminal alternatives:
  canceled
  failed
```

상태 전이는 application service가 통제하며 DB 트랜잭션과 고유 제약으로 중복 완료를 막는다.

### 7.2 `payment_events`

한 주문에서 발생한 provider 상호작용과 콜백 처리 이력을 저장한다.

- 이벤트 UUID
- 주문 UUID
- 이벤트 종류
- provider 상태
- 비밀 값을 제거한 필요한 응답 정보
- 중복 이벤트 식별 정보
- 수신/생성 시각

저장 이벤트 예:

- 일반 결제 생성
- 빌링키 생성
- 빌링키 활성화
- 최초 자동결제 승인
- 결제 완료
- 사용자 취소
- 결제 실패
- 상태 재검증

API Key와 평문 빌링키는 이벤트 payload에 저장하지 않는다.

## 8. 단건결제 흐름

1. Angular가 `planId`, `one_time`으로 결제 시작을 요청한다.
2. 서버가 활성 플랜을 조회하고 주문 스냅샷과 고유 `orderNo`를 생성한다.
3. 서버가 Toss Pay 일반 결제 생성 API를 호출한다.
4. `autoExecute=true`, `callbackVersion=V2`를 사용하고 외부 접근 가능한 result callback, return, cancel URL을 전달한다.
5. 응답의 `payToken`과 `checkoutPage` 생성 이벤트를 저장한다.
6. Angular가 `checkoutPage`로 전체 페이지 이동한다.
7. Toss Pay가 결제를 자동 승인하고 결과 콜백을 보낸다.
8. 서버가 Toss Pay 결제 상태 조회 API로 `PAY_COMPLETE`, 주문번호, 금액을 재검증한다.
9. 검증이 일치하면 주문을 `paid`로 변경하고 결과를 저장한다.
10. 공개 결과 페이지가 Clipper 서버에 저장된 최종 상태를 표시한다.

브라우저 return URL 도착만으로 `paid`를 기록하지 않는다.

## 9. 정기결제 흐름

1. Angular가 1개월 또는 3개월 플랜과 `recurring`으로 결제 시작을 요청한다.
2. 서버가 주문과 충돌 가능성이 없는 심사용 익명 Toss `userId`를 생성한다.
3. 서버가 Toss Pay 빌링키 생성 API를 호출한다.
4. 응답의 `billingKey`는 즉시 암호화하고, `checkoutUri`는 해당 결제 시작 응답에만 사용한다.
5. Angular가 `checkoutUri`로 전체 페이지 이동한다.
6. 사용자가 Toss 앱에서 자동결제 수단 등록을 마치면 Toss Pay가 활성화 콜백을 보낸다.
7. 서버가 빌링키 상태 조회 API로 동일 `userId`가 `ACTIVE`인지 재검증한다.
8. 검증이 끝나면 해당 빌링키로 최초 테스트 결제 1회를 승인한다.
9. 승인 응답의 `payToken`, 결제수단, 결제 금액, 거래 ID를 저장하고 주문을 `paid`로 변경한다.
10. 공개 결과 페이지가 저장된 결과를 표시한다.

최초 결제 시작은 주문 단위 PostgreSQL advisory lock과 조건부 상태 전이로 직렬화한다. 잠금 안에서는 동일 transaction manager의 repository만 사용해 커넥션 풀 교착을 피한다. 활성화 콜백이 중복되거나 네트워크 응답이 불확실하면 같은 주문번호로 재승인하기 전에 Toss Pay 결제 상태를 조회한다. `payment_pending`이 된 지 2분 이내면 기존 요청의 결과를 기다리고, 그 이후에만 상태 미존재를 확인한 뒤 같은 고유 주문번호로 복구 시도한다.

반복 청구 스케줄러, 해지, 다음 회차 결제는 이번 범위 밖이다.

## 10. 보안과 무결성

### 10.1 설정과 노출 제어

- 공용 테스트 키는 `TOSS_PAY_API_KEY` 환경변수로 `clipper_web_api`에만 주입한다.
- `clipper_web_client` 번들에는 API Key를 넣지 않는다.
- 비로그인 결제 시작은 dev·심사 모드뿐 아니라 `sk_test_` 키와 안전한 HTTPS URL 설정까지 모두 충족될 때만 활성화한다.
- 콜백과 상태 조회에서 검증된 provider 결과의 `mode`가 `TEST`가 아니면 결제 완료로 기록하지 않는다.
- 심사 모드가 꺼지면 공개 결제 시작 엔드포인트는 존재 여부를 드러내지 않는 방식으로 차단한다.

### 10.2 고유 식별자

공용 테스트 키를 다른 개발사도 사용할 수 있으므로 `orderNo`와 빌링 `userId`는 `clipper-review-<20자 base64url random>` 형식을 사용한다. 120비트 무작위 값으로 만들며 사용자 입력이나 순차 번호를 사용하지 않는다. 전체 길이는 Toss Pay의 50자 제한 안에 둔다.

### 10.3 비밀 저장

- `billingKey`는 결제를 실행할 수 있는 자격 증명으로 취급한다.
- 기존 `SecretCipher` AES-256-GCM 구현을 재사용해 암호화 저장한다.
- 로그, 이벤트 JSON, API 응답에는 평문 빌링키를 남기지 않는다.
- API Key도 일반 로그, 오류 응답, DB 이벤트에 남기지 않는다.

### 10.4 콜백 검증과 멱등성

- 브라우저 redirect와 callback payload만으로 결제를 완료 처리하지 않는다.
- provider status API로 현재 상태와 금액을 재검증한다.
- 상태 변경은 허용된 전이만 수행한다.
- `orderNo`, `payToken`, 거래 ID와 이벤트 식별자에 필요한 고유 제약을 둔다.
- 중복 콜백은 최초 결제나 완료 처리를 반복하지 않는다.

### 10.5 공개 API 보호

- 결제 시작 API에 IP 기준 rate limit를 적용한다.
- 외부 Nginx reverse proxy 한 홉만 신뢰하도록 Express `trust proxy=1`을 설정해 심사자별 실제 IP 기준으로 제한한다.
- 완료 조회 토큰은 32바이트 난수를 base64url로 인코딩해 생성하고 DB에는 SHA-256 해시만 저장한다.
- 공개 결과 API는 화면에 필요한 최소 정보만 반환한다.

## 11. 오류 처리

- Toss Pay 결제 생성 실패: 주문을 `failed`로 기록하고 Angular에 안전한 오류를 반환한다.
- 빌링키 활성화 실패: 활성화되지 않은 주문으로 유지하거나 명시적 실패 상태를 기록하고 결제를 실행하지 않는다.
- 최초 자동결제 승인 실패: 오류 코드와 안전한 메시지를 기록하고 `failed`로 종료한다.
- Toss Pay 요청 timeout 또는 불확실한 승인 응답: 재승인 전에 상태 조회로 결과를 복구한다.
- Toss Pay HTTP 요청은 10초 timeout을 사용한다. 결제 생성처럼 안전하게 다시 시도할 수 있는 호출만 제한적으로 재시도하고, 승인 호출은 상태 조회 없이 자동 재시도하지 않는다.
- 중복 콜백: 추가 부작용 없이 200 응답한다.
- 일시적 DB/provider 장애: 콜백에 실패 응답해 Toss Pay 재시도를 허용한다.
- 알 수 없는 주문의 콜백: 비밀 값을 로그에 남기지 않고 운영 로그로 식별 가능하게 기록한다.

## 12. 설정과 배포

`clipper_web_api`와 `clipper_infra`에 다음 설정을 추가한다.

```text
TOSS_PAY_API_KEY=<official shared test key>
TOSS_PAY_REVIEW_MODE=true
TOSS_PAY_CALLBACK_BASE_URL=https://dev-api.clipperstudio.ai
```

원칙:

- 실제 값은 배포용 비밀 환경 파일에만 둔다.
- 예제 env에는 변수명과 안전한 설명만 둔다.
- 공용 테스트 키가 공식 문서에 공개된 값이어도 애플리케이션 구조에서는 서버 비밀과 동일하게 취급한다.
- dev 배포에서 callback/return/cancel URL은 모두 `dev-api.clipperstudio.ai`와 `dev.clipperstudio.ai`의 외부 접근 가능한 HTTPS URL을 사용한다.
- 서버 callback URL은 `TOSS_PAY_CALLBACK_BASE_URL`, 브라우저 return/cancel URL은 기존 `WEB_BASE_URL`에서 조합한다.
- 운영 전용 키로 전환할 때 코드 변경 없이 환경변수만 교체할 수 있어야 한다.

## 13. 계약과 테스트 전략

### 13.1 계약 우선

`clipper_web_api/docs/api/openapi.yaml`에 다음 계약을 먼저 추가한다.

- 심사용 결제 시작
- 공개 결제 결과 조회
- Toss Pay callback endpoint 계약

그 다음 FE API 모델/service와 backend controller를 같은 계약에 맞춘다.

### 13.2 백엔드 자동 테스트

실제 Toss Pay 네트워크 대신 fake provider adapter를 주입한다.

필수 테스트:

- 클라이언트가 가격을 조작할 수 없고 서버 플랜 스냅샷을 사용한다.
- 비활성 플랜은 거부한다.
- 12개월 정기결제 요청은 거부한다.
- 심사 모드가 꺼지거나 dev가 아니면 공개 결제 시작을 거부한다.
- 단건결제 생성 성공 시 주문과 `payToken`을 저장한다.
- 빌링키는 평문이 아니라 암호문으로 저장한다.
- 콜백 후 provider 재검증이 성공해야만 `paid`가 된다.
- 금액이나 주문번호가 다르면 `paid`가 되지 않는다.
- 중복 일반 결제 콜백이 상태를 중복 변경하지 않는다.
- 중복 빌링 활성화 콜백이 최초 결제를 두 번 실행하지 않는다.
- 최초 결제 응답이 불확실하면 상태 조회 후 결정한다.
- 결제 완료가 기존 구매 요청·라이선스·크레딧 서비스를 호출하지 않는다.
- 공개 결과 조회가 비밀 필드를 반환하지 않는다.

### 13.3 프런트엔드 자동 테스트

- 1개월과 3개월 카드에 정기/단건 버튼이 표시된다.
- 12개월 카드에는 단건 버튼만 표시된다.
- 결제 시작 중 중복 클릭이 방지된다.
- 응답받은 checkout URL로 전체 페이지 이동한다.
- 시작 실패 시 오류를 표시한다.
- 결과 페이지가 처리 중, 완료, 취소, 실패 상태를 올바르게 표시한다.
- 결과 조회는 제한된 횟수만 재시도한다.
- 화면에 이용권/크레딧 지급 완료 문구가 없다.

### 13.4 빌드와 런타임 검증

- `clipper_web_api`: 관련 unit/integration test, 전체 test, build, 애플리케이션 부팅과 `/health`
- `clipper_web_client`: 관련 component/service test, 전체 test, production build
- `clipper_infra`: compose config와 env 전달 검증

### 13.5 dev 공용 테스트 키 스모크 테스트

1. 비로그인 브라우저에서 1개월 단건결제창 진입 및 테스트 결제 완료
2. 비로그인 브라우저에서 1개월 정기결제 등록 및 최초 테스트 결제 완료
3. 3개월의 두 버튼 확인
4. 12개월에 정기결제 버튼이 없고 서버 직접 요청도 거부되는지 확인
5. DB의 주문·이벤트·암호화 빌링키·결제 결과 확인
6. 구매 요청, 라이선스, 크레딧 데이터가 바뀌지 않았는지 확인
7. 중복 callback 재전송 시 결제가 중복 실행되지 않는지 확인

## 14. 비범위

- 결제 완료 후 이용권·크레딧 자동 지급
- 결제와 기존 Google 회원 연결
- 정기결제 다음 회차 스케줄링
- 구독 해지와 빌링키 삭제 UI
- 환불과 부분 취소
- 운영자 결제 관리 화면
- 영수증 UI
- 운영 실거래 키 전환
- 12개월 정기결제
- 기존 무통장 입금 구매 요청 제거

## 15. 심사 배포 후 확인할 사항

dev 배포와 내부 스모크 테스트가 끝나면 Toss Pay 담당자에게 다음을 전달하고 후속 요구사항을 확인한다.

- 비로그인 상태에서 정기결제창과 단건결제창 진입 가능
- 1년 상품은 단건결제로만 연결
- 공용 테스트 키를 사용한 테스트 결제 결과 저장 완료
- 결제 후 이용권·크레딧 자동 지급은 아직 연결하지 않았음
- 다음 심사 단계에 자동 지급, 반복 청구, 해지, 환불 중 무엇이 필요한지 확인 요청

## 16. 공식 문서

- AI 도구용 인덱스: https://docs-pay.toss.im/llms.txt
- 일반 결제 시작: https://docs-pay.toss.im/tutorial
- 결제 생성: https://docs-pay.toss.im/reference/normal/create
- 결제창 연결: https://docs-pay.toss.im/tutorial/step-3
- 승인과 콜백: https://docs-pay.toss.im/tutorial/step-5
- 자동 결제 시작: https://docs-pay.toss.im/tutorial/billing
- 빌링키 생성: https://docs-pay.toss.im/reference/billing/create
- 빌링키 활성화 확인: https://docs-pay.toss.im/tutorial/billing-step-3
- 최초 자동결제 승인: https://docs-pay.toss.im/tutorial/billing-step-4
