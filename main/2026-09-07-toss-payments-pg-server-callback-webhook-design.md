# Toss Payments PG 서버 콜백·웹훅 환경 분리 설계

작성일: 2026-09-07

상태: 사용자 방향 승인 후 구현 전 설계 기준

범위: 개발·운영 웹/API 환경에서 토스페이먼츠 결제 콜백과 웹훅을 안전하게 분리하는 방법

## 1. 확정한 결정

- 장기 운영 브랜치 이름은 `main`으로 한다.
- `dev`, `release/<version>`, `main` 같은 소스 브랜치 이름은 어떤 코드를 사용할지를 정한다.
- 개발용인지 운영용인지는 브랜치 이름이 아니라 각 환경의 Customer, Admin, API, DB, runner 및 환경 설정으로 구분한다.
- 토스페이먼츠 콜백·웹훅 전용 서브도메인은 새로 만들지 않는다.
- 개발 콜백과 웹훅은 기존 `dev-api.clipperstudio.ai`를 사용한다.
- 운영 콜백과 웹훅은 기존 `api.clipperstudio.ai`를 사용한다.
- 먼저 개발서버에 PG 코드를 배포하여 테스트 키로 전체 흐름을 검증한다.
- 운영 인프라와 라이브 키 전환은 개발서버 검증이 끝난 뒤 별도 승인 단계에서 진행한다.

## 2. 콜백과 웹훅의 차이

### 2.1 결제 콜백

결제 콜백은 사용자가 토스 결제창에서 인증을 끝내거나 취소했을 때 사용자의 브라우저가 이동하는 주소다.

`successUrl`과 `failUrl`은 Clipper API가 주문마다 생성하여 Customer에 반환하고, Customer가 그 값을 토스 SDK에 그대로 전달한다. 주문마다 `receipt` 값이 달라지므로 이 URL들을 토스 개발자센터에 고정 등록하지 않는다.

현재 구현된 경로는 다음과 같다.

- 일반결제 성공: `/payments/tosspayments/normal/success`
- 자동결제 카드 인증 성공: `/payments/tosspayments/billing/success`
- 결제 실패 또는 사용자 취소: `/payments/tosspayments/fail`

API는 성공 콜백에서 토스 승인 또는 빌링키 발급 처리를 수행한 뒤, `WEB_BASE_URL`을 기준으로 Customer의 결제 결과 화면으로 브라우저를 보낸다.

### 2.2 웹훅

웹훅은 사용자 브라우저와 무관하게 토스 서버가 Clipper API에 보내는 서버 간 HTTP POST 알림이다.

현재 고정 경로는 다음 하나다.

- `/payments/tosspayments/webhook`

이 주소는 토스 개발자센터의 웹훅 메뉴에 상점아이디(MID)별로 등록해야 한다.

현재 Clipper가 받는 이벤트는 다음 세 가지다.

- `PAYMENT_STATUS_CHANGED`
- `DEPOSIT_CALLBACK`
- `BILLING_DELETED`

웹훅 수신 API는 입력 형식을 제한해 필요한 식별 정보만 DB에 저장하고 HTTP 200을 반환한다. 실제 결제 상태 반영은 백그라운드 처리에서 토스 API를 다시 조회하여 주문과의 일치 여부를 확인한 뒤 수행한다. 중복 전송은 같은 이벤트를 한 번만 처리하도록 차단한다.

## 3. 환경별 주소

### 3.1 개발

API 환경 설정:

```dotenv
TOSS_PAYMENTS_RETURN_BASE_URL=https://dev-api.clipperstudio.ai
WEB_BASE_URL=https://dev.clipperstudio.ai
```

생성되는 콜백 주소:

```text
https://dev-api.clipperstudio.ai/payments/tosspayments/normal/success
https://dev-api.clipperstudio.ai/payments/tosspayments/billing/success
https://dev-api.clipperstudio.ai/payments/tosspayments/fail
```

토스 개발자센터에 등록할 웹훅 주소:

```text
https://dev-api.clipperstudio.ai/payments/tosspayments/webhook
```

콜백 처리 후 브라우저가 돌아갈 Customer 결과 화면:

```text
https://dev.clipperstudio.ai/app/payment/result
https://dev.clipperstudio.ai/app/payment-method/result
```

### 3.2 운영

API 환경 설정:

```dotenv
TOSS_PAYMENTS_RETURN_BASE_URL=https://api.clipperstudio.ai
WEB_BASE_URL=https://clipperstudio.ai
```

생성되는 콜백 주소:

```text
https://api.clipperstudio.ai/payments/tosspayments/normal/success
https://api.clipperstudio.ai/payments/tosspayments/billing/success
https://api.clipperstudio.ai/payments/tosspayments/fail
```

토스 개발자센터에 등록할 웹훅 주소:

```text
https://api.clipperstudio.ai/payments/tosspayments/webhook
```

콜백 처리 후 브라우저가 돌아갈 Customer 결과 화면:

```text
https://clipperstudio.ai/app/payment/result
https://clipperstudio.ai/app/payment-method/result
```

## 4. 프록시와 DNS 구조

PG 전용 도메인이나 외부 포트를 추가하지 않는다. 기존 HTTPS 443 요청을 `m2-proxy`의 Nginx Proxy Manager가 해당 API 서버로 전달한다.

개발 흐름:

```text
dev-api.clipperstudio.ai
-> m2-proxy
-> m2-stage의 개발 API
```

운영 흐름:

```text
api.clipperstudio.ai
-> m2-proxy
-> m4-prod의 운영 API
```

2026-09-07 read-only 확인 기준으로 개발 API Proxy Host와 HTTPS health 경로는 존재한다. 운영 API DNS는 공인 IP를 가리키지만 Nginx Proxy Manager의 운영 API Proxy Host와 인증서는 아직 구성하지 않았다. 운영 API 배포 단계에서 사용자가 직접 설정하고 검증한다.

현재 Infra 저장소의 `stack.prod.env.example`에 적힌 bind host는 과거 서버 배치 기준 값이다. `m4-prod`의 현재 내부 IP와 실제 포트 전달 구조를 확인해 새 운영 환경 파일을 만들며, 예시 파일의 IP를 그대로 복사하여 사용하지 않는다.

## 5. 상점아이디와 키 분리

Clipper API는 다음 두 자격증명 쌍을 따로 사용한다.

- 일반결제·크레딧 충전용 Widget Client/Secret Key 쌍
- 자동결제·구독용 Billing Client/Secret Key 쌍

서로 다른 종류의 키를 섞지 않는다. 테스트 키와 라이브 키도 섞지 않는다.

웹훅은 MID별 설정이므로 Widget 키와 Billing 키가 서로 다른 MID에 속한다면 각 MID의 개발자센터 웹훅 메뉴에 같은 환경의 웹훅 URL을 각각 등록한다. 어느 키가 어느 MID에 속하는지는 실제 값을 출력하지 않고 토스 개발자센터 화면에서 확인한다.

개발과 운영의 결제 데이터가 섞이지 않도록 가능한 경우 개발은 개발용 테스트 MID/키를 사용하고, 운영은 계약된 운영 MID의 테스트 키로 사전 검증한 뒤 승인된 시점에 같은 MID의 라이브 키로 전환한다.

## 6. 보안과 로그

- Toss Secret Key, 빌링키 HMAC 비밀값과 결제 자격증명은 API 서버에만 둔다.
- 브라우저에는 Client Key만 전달한다.
- 콜백 URL에는 `receipt`, `paymentKey`, `authKey` 같은 민감하거나 단기적인 값이 포함될 수 있다.
- 개발 API Proxy Host에 적용된 `access_log off;` 정책을 운영 API Proxy Host에도 적용한다.
- 애플리케이션 로그에도 전체 콜백 URL이나 원문 웹훅 본문을 남기지 않는다.
- 웹훅 본문만 믿고 이용권이나 크레딧을 지급하지 않는다. 저장한 주문과 연결하고 토스 API를 다시 조회한 결과를 기준으로 처리한다.
- 웹훅은 10초 안에 HTTP 200을 반환할 수 있어야 한다. 무거운 처리와 재시도는 백그라운드 작업에서 수행한다.

## 7. 리다이렉트 Origin 주의사항

토스 공식 문서는 `successUrl`에 서버 엔드포인트를 사용하는 방식을 지원한다고 설명한다. 동시에 결제창을 호출한 페이지와 같은 Origin 사용을 안내하는 내용도 있다.

현재 Clipper 구현은 Customer와 API를 서로 다른 서브도메인으로 사용한다.

```text
Customer: dev.clipperstudio.ai
callback: dev-api.clipperstudio.ai
```

로컬 테스트에서는 이 서버 콜백 방식이 실제로 동작했지만, 운영 근거로 간주하지 않는다. 먼저 실제 개발 도메인과 실제 테스트 MID/키 조합으로 검증한다.

개발 도메인 테스트가 성공하면 현재 구조를 유지한다. 실제로 Origin 제한 문제가 재현될 때만 Customer 도메인의 `/payments/tosspayments/*` 경로를 API로 전달하는 프록시 방식으로 변경한다. 그 경우에도 새 서브도메인은 만들지 않는다.

## 8. 개발서버 검증 순서

1. 최신 PG 코드와 테스트를 release candidate에서 다시 확인한다.
2. 개발 API 환경에 일치하는 테스트 Client/Secret Key 쌍과 URL 설정을 준비한다.
3. 개발 DB를 백업하고 승인된 migration 절차를 실행한다.
4. PG가 포함된 개발 API와 Customer를 배포한다.
5. API health와 결제 관련 공개 경로가 HTTPS로 접근 가능한지 확인한다.
6. 해당 테스트 MID마다 개발 웹훅 URL과 세 이벤트를 등록한다.
7. 일반 카드, 간편결제, 계좌이체와 자동결제 카드 등록을 테스트한다.
8. 성공·실패·사용자 취소 콜백이 올바른 개발 결과 화면으로 돌아오는지 확인한다.
9. 결제·구독·크레딧이 개발 Admin DB에 정확히 한 번 기록되는지 확인한다.
10. 웹훅 전송 기록이 HTTP 200인지 확인한다.
11. 같은 웹훅을 재전송해도 상태 변경이나 크레딧 지급이 중복되지 않는지 확인한다.
12. 가상계좌를 사용할 수 있는 테스트 MID라면 발급·입금·취소·만료를 별도로 검증한다.
13. 콜백 URL의 쿼리 값이 프록시·애플리케이션 로그에 남지 않는지 확인한다.

## 9. 운영 적용 전 통과 조건

- 실제 개발 도메인에서 일반결제 성공·실패·취소가 통과한다.
- 자동결제 카드 등록, 최초 결제와 결제수단 변경이 통과한다.
- 등록한 세 웹훅 이벤트가 수신·중복제거·재처리된다.
- 가상계좌를 운영 결제수단으로 사용할 경우 관련 비동기 흐름이 통과한다.
- Customer, Admin, API와 설치형 앱이 모두 개발 환경에서는 개발 API만 가리킨다.
- 운영 빌드가 운영 API만 가리키도록 하는 별도 배포 차단 문제를 해결한다.
- 운영 API Proxy Host, HTTPS 인증서와 민감 쿼리 로그 차단을 검증한다.
- 운영용 키 쌍과 MID 연결을 토스 개발자센터에서 확인한다.
- 라이브 결제·환불은 이번 세션에서 실행하지 않으며, 별도로 승인된 최종 점검 단계에서만 실행한다.

## 10. 현재 확인된 배포 차단 요소

다음 항목은 콜백·웹훅 주소만 설정한다고 해결되지 않는다. 개발 PG 검증과 운영 배포 계획에서 함께 해결해야 한다.

- Customer와 Admin의 현재 운영용 빌드 설정이 아직 개발 API 주소를 가리키는 부분이 있다. 개발 빌드는 `dev-api.clipperstudio.ai`, 운영 빌드는 `api.clipperstudio.ai`만 사용하도록 빌드 설정과 검사 절차를 분리해야 한다.
- 설치형 앱에도 로그인 API와 업데이트 주소의 개발용 기본값이 남아 있다. 운영 설치 파일이 개발 API나 개발 릴리즈 목록을 바라보지 않도록 빌드 입력과 결과물을 검사해야 한다.
- 현재 Windows runner는 개발용 한 개만 운영 중이다. 개발용과 운영용 runner의 컨테이너 이름, 포트, 작업 폴더, 환경 파일과 자격증명을 나누기 전에는 운영 빌드를 요청하면 안 된다.
- `m2-proxy`에는 개발 Customer, Admin, API의 Proxy Host만 확인되었다. 운영용 세 Proxy Host와 인증서가 마련되기 전에는 외부 운영 트래픽을 열면 안 된다.
- 운영 Infra 환경 예시에는 예전 서버 구조의 주소가 남아 있다. 현재 `m2-proxy`, `m2-db`, `m4-prod` 구조에 맞춰 값을 하나씩 확인해서 새 실제 환경 파일을 만들어야 한다.

## 11. 이번 설계에서 하지 않는 것

- 서버 배포
- DNS 또는 Nginx Proxy Manager 변경
- 토스 개발자센터 웹훅 등록 변경
- 개발·운영 DB migration 또는 write
- 테스트·라이브 결제와 환불 실행
- secret key, token, 빌링키 또는 민감 결제 데이터 출력
- PG 전용 서브도메인 추가

## 12. 구현 계획으로 넘길 작업

이 설계가 최종 승인되면 별도 구현 계획에서 다음을 구체적인 테스트와 작은 checkpoint 단위로 나눈다.

- 개발·운영 웹 빌드의 API 주소 분리
- 설치형 앱의 개발·운영 API 및 자동 업데이트 주소 분리
- 개발·운영 Windows runner의 이름, 포트, 작업 폴더, 환경 파일과 자격증명 분리
- 운영 API Proxy Host 수동 설정 체크리스트
- 개발 PG 배포 전 환경변수·MID·웹훅 preflight
- 개발서버 콜백·웹훅·중복 처리 검증 절차
- 개발 검증 통과 후 운영 적용과 되돌리기 절차

## 13. 확인 근거

현재 구현을 확인한 파일:

- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/application/payment-checkout-session.service.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/presentation/toss-payments-redirect.controller.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/presentation/toss-payments-webhook.controller.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/application/payment-webhook.service.ts`
- `/Users/jina/project/adlight/web/clipper_infra/runbooks/deploy-dev.md`
- `/Users/jina/project/adlight/web/clipper_infra/env/stack.dev.env.example`
- `/Users/jina/project/adlight/web/clipper_infra/env/stack.prod.env.example`

공식 확인 자료:

- [토스페이먼츠 웹훅 연결하기](https://docs.tosspayments.com/guides/v2/webhook)
- [토스페이먼츠 successUrl 이해하기](https://docs.tosspayments.com/blog/what-is-successurl)
- [토스페이먼츠 리다이렉트 이해하기](https://docs.tosspayments.com/blog/redirect)
- [토스페이먼츠 빌링키 발급 흐름](https://docs.tosspayments.com/blog/subscription-service-1)
- [토스페이먼츠 배포 체크리스트](https://docs.tosspayments.com/guides/v2/deploy-checklist)
