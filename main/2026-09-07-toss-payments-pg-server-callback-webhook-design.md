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

## 10. 관리자 릴리스 빌드에서 소스 브랜치와 환경을 구분하는 기준

### 10.1 `sourceBranch`가 정하는 것

관리자페이지에서 입력하는 `dev`, `main`, `release/<version>`은 설치형 앱을 만들 때 어느 소스코드를 가져올지만 정한다.

현재 runner는 입력받은 브랜치 이름으로 다음 다섯 저장소의 `origin/<sourceBranch>`를 조회하고, 각 저장소의 정확한 commit SHA를 하나의 소스 스냅샷으로 고정한다.

- `clipper_angular`
- `clipper_nestjs`
- `clipper_python`
- `clipper_electron`
- `clipper_web_api`

`sourceBranch`는 개발용·운영용 API 주소, DB, S3 경로 또는 runner를 선택하지 않는다. 현재 API도 브랜치 이름이 Git 브랜치 문법에 맞는지만 검사하므로 `dev`를 운영 Admin에서 입력하는 행위 자체는 허용한다.

### 10.2 개발용인지 운영용인지 정하는 것

빌드 환경은 브랜치 이름이 아니라 빌드 요청이 통과하는 서버 사슬로 정한다.

```text
개발 Admin
-> 개발 Web API
-> 개발 Windows runner
-> 개발 API 주소·개발 JWT 공개키·개발 S3 경로·개발 Release DB

운영 Admin
-> 운영 Web API
-> 운영 Windows runner
-> 운영 API 주소·운영 JWT 공개키·운영 S3 경로·운영 Release DB
```

따라서 환경 분리가 완성된 뒤의 결과는 다음과 같다.

| 빌드를 요청한 곳 | 선택한 소스 브랜치 | 설치형 앱이 연결할 API |
| --- | --- | --- |
| 개발 Admin | `dev` | 개발 API |
| 개발 Admin | `main` | 개발 API |
| 운영 Admin | `main` | 운영 API |
| 운영 Admin | `dev` | 운영 API |

운영 Admin에서 `dev`를 선택하는 마지막 경우는 기술적으로 지원할 수 있다. 이 결과물은 `dev`의 코드를 사용하지만 운영 API와 운영 데이터에 연결된다. 검증되지 않은 개발 코드가 운영 데이터에 접근할 수 있으므로 화면에 명확한 경고를 표시하고, 빌드와 정식 배포 승인을 분리해야 한다. 기본 운영 빌드는 `main` 또는 승인된 `release/<version>`을 사용한다.

환경 값은 브라우저가 임의로 보내는 입력을 신뢰해서 선택하지 않는다. 개발 Web API와 운영 Web API가 자신에게 고정된 runner 주소·토큰과 환경 이름을 서버 설정에서 선택해야 한다.

### 10.3 현재 구현에서 실제로 분리되는 부분

- Web API는 `CLIPPER_RELEASE_WINDOWS_RUNNER_START_URL`, `CLIPPER_RELEASE_WINDOWS_RUNNER_SNAPSHOT_URL`, `CLIPPER_RELEASE_WINDOWS_RUNNER_TOKEN`으로 호출할 runner를 선택한다.
- runner의 `release-runner.dev.env`와 `release-runner.prod.env`는 작업 결과를 보고할 API, S3 prefix, runner 이름과 실행 정보를 나누기 위한 파일이다.
- Windows 환경 준비 스크립트는 runner의 API 주소를 데스크톱 NestJS용 `.env.packaged`의 `CLIPPER_WEB_API_BASE_URL`과 원격 기능 endpoint에 기록한다.
- runner는 빌드 직전에 고정된 각 저장소의 commit을 checkout하므로, 같은 브랜치 이름이 빌드 도중 움직여도 이미 만든 스냅샷의 commit을 사용한다.

### 10.4 현재 구현에서 아직 분리되지 않은 부분

- 현재 Admin과 Customer의 Angular `environment.production.ts`는 개발 API 주소를 고정해서 사용한다. Docker 컨테이너 실행 시 넣는 `CLIPPER_ENV=prod`만으로는 이미 만들어진 정적 JavaScript 안의 주소가 바뀌지 않는다.
- 설치형 앱 내부 NestJS는 `.env.packaged`의 API 주소를 사용하지만, Electron 로그인과 자동 업데이트는 설정이 없으면 개발 API 주소로 돌아간다.
- runner가 빌드하는 `packaged-runtime-config.json`에는 일반 빌드의 환경별 API 주소가 들어가지 않는다. 그래서 설치형 앱 전체가 하나의 동일한 환경을 바라본다는 보장이 없다.
- 개발 runner와 운영 runner가 같은 작업 폴더를 사용하면 공용 `.env.packaged`, JWT 공개키, 출력 폴더를 서로 덮어쓸 수 있다.
- runner 컨테이너의 기본 이름과 기본 포트가 같고, 현재 Docker 포트 연결도 `19029:19029`로 고정되어 있어 두 환경을 그대로 동시에 실행할 수 없다.
- 실제 `storage`에는 현재 개발용 runner 하나만 있다. 운영용 runner는 아직 구축하지 않았다.

따라서 현재 상태에서는 운영 Admin에서 `dev`를 선택해 빌드가 성공하더라도, 그 설치파일의 모든 기능이 운영 API만 바라본다고 보장할 수 없다. 아래 환경 분리를 먼저 구현하고 검사해야 한다.

### 10.5 구현해야 할 최종 분리 구조

- Admin과 Customer 웹은 개발용·운영용 API 주소를 각각 빌드할 수 있어야 한다.
- 개발 Web API는 개발 runner만 호출하고 운영 Web API는 운영 runner만 호출해야 한다.
- 개발·운영 runner는 서로 다른 컨테이너 이름, host port, 작업 폴더, 환경 파일, 출력 폴더와 JWT 공개키를 사용해야 한다.
- runner가 빌드마다 환경별 API 주소와 자동 업데이트 주소를 Electron runtime config에 명시적으로 넣어야 한다.
- 설치형 앱의 로그인, 포함된 NestJS, 원격 기능 호출과 자동 업데이트가 모두 같은 환경의 API를 바라보는지 빌드 결과물을 검사해야 한다.
- 개발·운영 S3 prefix와 Release DB를 분리하고, runner가 자신의 환경이 아닌 곳에 결과를 보고하거나 업로드하지 못하게 해야 한다.
- 운영 Admin에서 `dev`처럼 기본 정책 밖의 브랜치를 선택하면 경고와 별도 확인을 요구하되, 사용자가 명시적으로 승인하면 빌드는 가능하게 한다.

## 11. 현재 확인된 배포 차단 요소

다음 항목은 콜백·웹훅 주소만 설정한다고 해결되지 않는다. 개발 PG 검증과 운영 배포 계획에서 함께 해결해야 한다.

- Customer와 Admin의 현재 운영용 빌드 설정이 아직 개발 API 주소를 가리키는 부분이 있다. 개발 빌드는 `dev-api.clipperstudio.ai`, 운영 빌드는 `api.clipperstudio.ai`만 사용하도록 빌드 설정과 검사 절차를 분리해야 한다.
- 설치형 앱에도 로그인 API와 업데이트 주소의 개발용 기본값이 남아 있다. 운영 설치 파일이 개발 API나 개발 릴리즈 목록을 바라보지 않도록 빌드 입력과 결과물을 검사해야 한다.
- 현재 Windows runner는 개발용 한 개만 운영 중이다. 개발용과 운영용 runner의 컨테이너 이름, 포트, 작업 폴더, 환경 파일과 자격증명을 나누기 전에는 운영 빌드를 요청하면 안 된다.
- `m2-proxy`에는 개발 Customer, Admin, API의 Proxy Host만 확인되었다. 운영용 세 Proxy Host와 인증서가 마련되기 전에는 외부 운영 트래픽을 열면 안 된다.
- 운영 Infra 환경 예시에는 예전 서버 구조의 주소가 남아 있다. 현재 `m2-proxy`, `m2-db`, `m4-prod` 구조에 맞춰 값을 하나씩 확인해서 새 실제 환경 파일을 만들어야 한다.

## 12. 이번 설계에서 하지 않는 것

- 서버 배포
- DNS 또는 Nginx Proxy Manager 변경
- 토스 개발자센터 웹훅 등록 변경
- 개발·운영 DB migration 또는 write
- 테스트·라이브 결제와 환불 실행
- secret key, token, 빌링키 또는 민감 결제 데이터 출력
- PG 전용 서브도메인 추가

## 13. 구현 계획으로 넘길 작업

이 설계가 최종 승인되면 별도 구현 계획에서 다음을 구체적인 테스트와 작은 checkpoint 단위로 나눈다.

- 개발·운영 웹 빌드의 API 주소 분리
- 설치형 앱의 개발·운영 API 및 자동 업데이트 주소 분리
- `sourceBranch`와 빌드 환경을 독립된 값으로 유지하고 운영의 비기본 브랜치 선택에 경고·승인 절차 추가
- 개발·운영 Windows runner의 이름, 포트, 작업 폴더, 환경 파일과 자격증명 분리
- 개발·운영 runner를 동시에 실행해도 `.env.packaged`, JWT 공개키와 산출물을 공유하지 않는 구조
- 빌드 결과물 안의 로그인·NestJS·업데이트 주소가 한 환경으로 일치하는지 검사하는 preflight
- 운영 API Proxy Host 수동 설정 체크리스트
- 개발 PG 배포 전 환경변수·MID·웹훅 preflight
- 개발서버 콜백·웹훅·중복 처리 검증 절차
- 개발 검증 통과 후 운영 적용과 되돌리기 절차

## 14. 확인 근거

현재 구현을 확인한 파일:

- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/application/payment-checkout-session.service.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/presentation/toss-payments-redirect.controller.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/presentation/toss-payments-webhook.controller.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/application/payment-webhook.service.ts`
- `/Users/jina/project/adlight/web/clipper_infra/runbooks/deploy-dev.md`
- `/Users/jina/project/adlight/web/clipper_infra/env/stack.dev.env.example`
- `/Users/jina/project/adlight/web/clipper_infra/env/stack.prod.env.example`
- `/Users/jina/project/adlight/web/clipper_web_admin/src/environments/environment.production.ts`
- `/Users/jina/project/adlight/web/clipper_web_admin/angular.json`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/http-release-source-snapshot.provider.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/http-release-runner-start.client.ts`
- `/Users/jina/project/adlight/web/clipper_infra/runner/release-runner.mjs`
- `/Users/jina/project/adlight/web/clipper_infra/runner/windows/prepare-windows-env.ps1`
- `/Users/jina/project/adlight/web/clipper_infra/runner/windows/run-windows-runner-container.ps1`
- `/Users/jina/project/adlight/desktop/clipper_electron/scripts/build-runtime-config.mjs`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/auth/api-base.ts`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/update/update-feed.ts`

공식 확인 자료:

- [토스페이먼츠 웹훅 연결하기](https://docs.tosspayments.com/guides/v2/webhook)
- [토스페이먼츠 successUrl 이해하기](https://docs.tosspayments.com/blog/what-is-successurl)
- [토스페이먼츠 리다이렉트 이해하기](https://docs.tosspayments.com/blog/redirect)
- [토스페이먼츠 빌링키 발급 흐름](https://docs.tosspayments.com/blog/subscription-service-1)
- [토스페이먼츠 배포 체크리스트](https://docs.tosspayments.com/guides/v2/deploy-checklist)
