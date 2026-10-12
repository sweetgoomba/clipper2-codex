# 클리퍼 TossPayments 라이브 전환: 현재 상태와 실행 순서

> 아래 본문은 라이브 거래 전 재조사와 전환 계획의 당시 상태를 담는다. 이후 실행된 정기·단건 실결제, 승인 거절 수정, 간편결제 이메일 호칭 이슈와 최신 잔여 작업은 [10/7 라이브 검증 기록](2026-10-07-toss-live-validation-and-open-issues.md)에 갱신했다.

기준: 2026-10-07 KST. **정식 운영 DB 3개를 초기화·재생성하고 마이그레이션과 관리자 seed를 완료했다. m4-prod 정식 운영 앱 3개가 기동됐고 내부 API `/health`는 세 DB 모두 `ok`다. API 키 4종은 라이브 형식이며 공개 Client/Admin/API 주소는 모두 HTTP 200이다. 운영 가격·최신 관리자 화면·내부 직원 로그인도 확인했다. 고객 웹 `c224b44` 배포 후 브라우저에서 요금제 페이지 재경유 없이 Basic 월간 5,900원 카드 등록 확인 화면에 도달했다. 로딩 중 돌아가기 버튼을 숨기는 후속 `904005e`도 운영 배포했고 컨테이너 revision·공개 URL HTTP 200을 확인했으나 해당 버튼의 브라우저 재확인은 아직이다. 인증 토큰 fragment 일시 표시도 확인했다. 실제 MID 거래/환불은 보류 중이다. 개발 앱·DB는 유지하고 가상계좌는 제외한다.** 이 문서는 9월 29일 분석의 새 MID 정보와 운영 현황을 반영한 재조사본이다.

사용자는 계정 A의 기존 건이 **모두 테스트 키 거래이며 실결제가 없었다**고 확인했다. 따라서 아래의 구 거래 영향 설명은 키만 바꿀 때의 기술적 원리를 설명하는 것이고, 이번 실행에서는 계정 A 거래 대사를 요구하지 않는다.

**10월 7일 구현 상태:** 최신 `origin/dev` 기반 격리 브랜치에서 API의 단건결제 키 연결을 `ONE_TIME_*`로 바꾸고, 고객 웹의 일반결제를 `payment().requestPayment()`로 전환했으며, 카드·간편결제/계좌이체 선택과 필수 동의를 추가했다. 인프라는 새 키만 받도록 검사한다. API `64a6b61`, 고객 웹 최초 `d7a05f4`, 인프라 코드 `72594b8`을 원격 전환 브랜치에 push했고 정식 운영 앱·DB를 기동했다. 인프라 실행안은 `eaf0b4a`까지 갱신했다. 운영 화면 확인에서 발견된 로그아웃 구매 버튼의 Google 인증 직행은 고객 웹 `0dece7d`·`ee338d6`으로 수정·검증해 push했다. 사용자가 m4-prod에서 `ee338d6` 이미지를 빌드해 고객 웹 컨테이너만 교체했고 컨테이너 revision과 고객 공개 URL HTTP 200을 확인했다. 이후 사용자 프레임에서 확인된 요금 페이지 경유와 메뉴 깜빡임을 줄이는 고객 웹 `c224b44`를 검증해 같은 원격 브랜치에 push했다. 사용자가 m4-prod에서 `c224b44` 고객 웹만 다시 빌드·기동했고 실행 컨테이너 revision 일치와 공개 URL HTTP 200을 확인했다. **새 화면의 브라우저 재확인은 남아 있다.** 개발 앱·DB는 유지하며 사용자가 서버 명령과 실결제를 직접 진행한다.
운영 브라우저 재확인에서 `/pricing?subscribe=...` 경유가 사라지고 `/auth/callback` 안내 뒤 곧바로 결제 확인 화면에 도달했다. 로그인 화면 잔상·잠깐 빈 화면은 사용자가 이번에 허용했다. 주문 정보 로딩 때 나타나는 돌아가기 버튼을 숨기는 고객 웹 `904005e`는 같은 원격 브랜치에 push했고, 기존 결제 확인 화면 테스트 16개·운영 빌드를 통과했다. 사용자가 m4-prod에서 고객 웹만 다시 빌드·기동했고 실행 컨테이너 revision 일치와 공개 URL HTTP 200을 확인했다. **이 후속 수정의 브라우저 재확인은 아직이다.**

## 서버 구성을 한눈에 보면

| 장비 | 현재 배포 | 이 전환에서의 역할 |
|---|---|---|
| m2-stage (`192.168.0.23`) | 개발 앱 `clipper-web-{client,admin,api}-dev` 실행. 이번 전환에서 변경하지 않음 | 기존 개발 앱과 키 유지 |
| m2-db (`192.168.0.7`) | 정식 운영 `clipper-db-prod`의 user/admin/release DB 컨테이너·볼륨 3개를 빈 상태로 재생성하고 migration 완료. 개발 DB 3개는 별도 실행 중 | 운영 상품 가격·실거래 데이터 확인 |
| m4-prod (`192.168.0.47`) | 정식 운영 Client/Admin/API 앱 3개가 공개 포트 42202/42302/43202에서 실행 중. 고객 웹 화면 전환 수정 `c224b44` 배포 완료. 임시 심사 앱은 중지, 같은 장비의 `_review` DB 3개는 보존 중 | 새 화면 전환을 브라우저에서 확인하고 라이브 거래를 검증한 뒤 임시 심사 앱·DB 정리 |

따라서 **m2-db에 심사용 DB를 따로 배포한 것은 아니다.** `_prod`와 `_review`는 서로 다른 장비에 있는 별도 DB 세트이며, 각 세트 안의 “3개”는 user/admin/release로 나눈 앱 DB 역할을 뜻한다.

10월 7일 m2-db의 개발 관리자 DB를 읽기 전용으로 조회한 결과, `subscriptions`는 `active` 4건·`canceled` 1건이고 `payment_orders`는 `checkout_ready` 1건·`expired` 1건·`paid` 4건이다. m2-db 컨테이너·볼륨 목록에는 `_dev`와 `_prod`만 있고 별도 `_stage` DB는 없다. 이 개발 DB에 계정 B의 새 테스트 키만 덮어쓰면 기존 구독의 재청구와 구 주문의 조회·취소가 다른 MID의 키로 시도될 수 있다. 심사용 스택도 구 비로그인 심사 앱·구 테스트 데이터를 사용해 최신 로그인 기반 결제 검증에는 재구성이 필요하다. 따라서 개발·심사 DB는 유지하고, **이번 전환에서는 새 테스트 키 종단 간 거래를 생략한 채 빈 운영 DB에서 내부 직원의 라이브 거래를 한 건씩 검증한다.** 이 검증 공백은 사라지지 않으므로 첫 라이브 거래에서 토스 MID·금액·앱 주문/지급 상태를 대조하고 불일치하면 다음 거래를 중단한다.

## 먼저 알아야 할 결론

1. 새 토스 계정 B에는 **일반결제 MID `clidevxzdd`**, **정기결제 MID `bill_cldevp14i`**가 발급됐다. 계정 A의 예전 키·거래와 별개로 취급한다. 한 MID의 테스트/라이브 클라이언트·시크릿 키는 반드시 같은 환경의 한 세트로 사용한다.
2. **전환 전 조사:** 공개 포트 42202/42302/43202는 임시 심사 앱이 점유했고 심사 API는 별도 `_review` DB와 구 테스트 키를 사용했다. 심사판 어드민의 “입금 승인 대기” 표는 최신 코드와 달랐다. **현재:** 심사 앱을 중지하고 정식 운영 Client/Admin/API 3개를 같은 포트에 기동했다. 운영 API는 `CLIPPER_ENV=prod`, m2-db의 세 `_prod` DB(55202/55212/55222)에 연결되고 키 4종은 라이브 형식이다. 사용자는 관리자 대시보드의 최신 지표 카드와 고객 요금·내부 직원 로그인을 확인했다. 심사 DB는 라이브 검증 후 정리한다.
3. **전환 전 문제:** 구 단건결제 브라우저 코드는 `widgets()`와 다른 계정의 `gck/gsk` 키를 썼다. 새 일반 MID의 `live_ck_` 키에 맞춰 현재 운영 고객 웹은 `payment().requestPayment()` 결제창 방식으로 바뀌었고 정기결제는 `payment().requestBillingAuth()`를 사용한다. 로그아웃 상태에서 요금제를 선택하면 Google 인증이 안내 없이 바로 시작되는 별도 UX 문제는 수정 커밋 `0dece7d`·`ee338d6`으로 고쳐 운영 배포했으며, 로그인 안내와 선택 상품으로의 복귀를 사용자 브라우저에서 확인했다. 복귀 중 요금 페이지 경유를 없애고 OAuth 확인 중 단일 안내를 보이는 `c224b44`도 운영 배포했으나 해당 화면 흐름의 브라우저 재확인은 남아 있다. [토스 키 종류](https://docs.tosspayments.com/reference/using-api/api-keys), [SDK 키·메서드](https://docs.tosspayments.com/sdk/v2/js/environment).
4. 계정 B의 일반결제 MID `clidevxzdd`에서 사용자가 확인한 계약 수단은 **신용·체크카드, 계좌이체, 카카오페이, 토스페이, 네이버페이**다. **가상계좌는 제공된 활성 목록에 없다.** 따라서 현재 계약 상태로 라이브 가상계좌 발급·실입금 검증을 성공 가능한 단계로 간주하지 않는다. 토스에서 해당 MID의 가상계좌 계약·활성화를 확인한 뒤 별도 검증한다. [계약 수단 확인·미계약 문의 안내](https://docs.tosspayments.com/resources/faq).
5. **DB 구조상** 주문에는 `paymentKey`와 `key_set`(`widget`/`billing`), 구독에는 암호화된 `billingKey`를 저장하지만 MID·test/live·키 세대는 저장하지 않는다. 구 거래가 남은 DB에서 키만 바꾸면 다른 MID의 키로 조회·환불·재청구를 시도할 수 있다. 이번 운영 `_prod` DB는 전체 초기화했으므로 구 테스트 거래를 이 DB에서 재사용하지 않는다.

## 연결 구조를 간단히 보면

| 업무 | 브라우저 | 서버 | 우리 DB |
|---|---|---|---|
| 추가 크레딧 1회 구매 | 일반결제 MID의 **clientKey**로 결제창 호출 | 같은 MID·환경의 **secretKey**로 승인·조회·취소 | `payment_orders`에 주문번호·`paymentKey`·금액·상태·`key_set` 저장. 지급 성공 시 크레딧 원장 생성 |
| 구독 시작·월/년 재청구 | 정기결제 MID의 **clientKey**로 카드 등록 | 같은 MID·환경의 **secretKey**로 `billingKey` 발급·첫 청구·다음 청구 | `subscriptions`에 암호화된 `billingKey`·다음 청구일, 주문에 결제별 `paymentKey`. 성공 시 이용권·월 크레딧 지급 |
| 가상계좌 | 일반결제 MID에서 계좌 발급 | 발급은 `WAITING_FOR_DEPOSIT`; 입금 후 `DONE` 이벤트를 재조회·처리 | 입금 전 크레딧 지급 없음. 입금 확인과 지급은 webhook·worker에 의존 |

`paymentKey`는 **결제 한 건**의 식별자이고 `billingKey`는 **등록 카드 재청구**에 쓰는 토큰이다. 둘은 MID나 API 키가 아니다. 토스 Payment/Billing 응답에는 `mId`가 있지만 현재 provider/DB는 이를 보존하지 않는다. [Payment·Billing 객체](https://docs.tosspayments.com/reference).

### 헷갈리기 쉬운 이름 세 가지

- **계좌이체와 가상계좌는 별도 결제수단:** 계좌이체는 구매자가 결제 과정에서 자신의 은행 계좌로 즉시 출금·이체한다. 가상계좌는 먼저 입금 전용 계좌를 발급받고 구매자가 나중에 입금한다. 가상계좌 발급 직후 상태는 `WAITING_FOR_DEPOSIT`이며, 실제 입금 후 `DONE`이 된다. 따라서 계약 목록의 **계좌이체**만으로 **가상계좌**도 사용할 수 있다고 판단하지 않는다. [토스 결제수단 정책](https://docs.tosspayments.com/guides/v2/get-started/payment-methods), [가상계좌 연동](https://docs.tosspayments.com/guides/v2/payment-window/integration-virtual-account).
- **`WIDGET_*`와 `ONE_TIME_*`는 우리 서버의 설정 항목 이름:** 현재 코드의 `TOSS_PAYMENTS_WIDGET_CLIENT_KEY`/`SECRET_KEY`에는 구 단건결제 키를 넣어 쓰고 있다. 새 일반결제 키가 `live_ck_`여서 SDK 호출을 `widgets()`에서 `payment()`로 바꿔야 한다. 사용자는 설정 이름도 실제 용도에 맞게 `TOSS_PAYMENTS_ONE_TIME_CLIENT_KEY`/`SECRET_KEY`로 변경하는 방향을 선택했다. 이 이름은 토스에서 발급하는 키 이름이 아니다. API 코드·서버 비공개 환경파일·배포 전 검사를 함께 맞춰야 한다. [토스 SDK 키 종류](https://docs.tosspayments.com/sdk/v2/js/environment).
- **DB의 `key_set='widget'`은 주문 처리용 내부 분류:** 크레딧 1회 구매 주문을 만들 때 코드는 `widget`을 적고, 정기결제 주문에는 `billing`을 적는다. 결제 화면을 준비할 때 이 값을 검사해 각각 일반결제 또는 정기결제 **클라이언트 키**를 돌려준다. 승인·조회·환불 시에는 결제 종류에 따라 일반결제 또는 정기결제 **시크릿 키**를 쓴다. `widget`이라는 과거 이름이 남아 있을 뿐, 그 주문에 사용한 실제 MID·키 값·test/live 환경을 저장한 것은 아니다. [주문 생성](../../web/clipper_web_api/src/modules/payments/application/topup-payments.service.ts), [현재 키 선택 코드](../../web/clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts).

예를 들어 크레딧 구매는 `주문 생성(key_set='widget') → 브라우저에 일반결제 clientKey 전달 → 구매자 결제 → 서버가 일반결제 secretKey로 승인 → 이후 조회·환불에도 같은 종류의 secretKey 선택` 순서다. 구독은 같은 자리의 표시가 `billing`이고 정기결제 키를 선택한다. 실제 전환 코드에서는 내부 `widget` 표시가 **새 `ONE_TIME_*` 설정 항목**을 가리키도록 연결해야 한다.

**왜 내부 표시를 바로 바꾸지 않나:** 운영 DB는 비울 예정이지만 개발 DB에는 기존 마이그레이션과 주문이 있고, 서버의 주문 생성·검증·webhook·조회·환불 여러 경로도 `widget`/`billing` 두 값을 전제로 한다. DB 표시를 `one_time`으로 바꾸려면 기존 마이그레이션을 고치는 것만으로는 부족하다. 새 마이그레이션과 모든 참조·테스트를 함께 바꿔야 한다. 라이브 전환에 필요한 동작은 `widget → 새 단건결제 키` 연결만으로 가능하므로 **사용자는 이번 릴리스에서 내부 값을 유지하는 추천안에 동의했다.** 내부 이름 정리는 추후 별도 마이그레이션으로 할 수 있다. [DB 제약](../../web/clipper_web_api/src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.ts).

토스 문서의 현재 **주문서형·결제창형 결제**는 `widgets()`와 `gck/gsk` 키를 사용한다. 계정 B에서 제공된 `ck/sk` 키로 제안한 `payment()` 방식의 공식 명칭은 **결제창(구버전)**이다. 여기서 “구버전”은 토스의 제품명이며, 새 MID의 `ck/sk` 키를 쓰면 안 된다는 뜻은 아니다. [키 구분](https://docs.tosspayments.com/sdk/v2/js/environment), [결제창(구버전)](https://docs.tosspayments.com/guides/v2/payment-window).

## 왜 기존 DB를 그대로 둔 채 키만 바꾸면 안 되나

| 남아 있는 것 | 키만 바꾼 뒤 예상 영향 |
|---|---|
| 계정 A의 예전 주문·결제내역 | 화면에는 계속 보이지만, 현재 서버는 계정 B의 새 secret으로 조회·환불을 시도한다. 다른 MID의 거래 접근은 이관이 확인되지 않았으므로 성공을 가정할 수 없다. |
| 예전 구독의 `billingKey` | 다음 청구 worker가 이 값을 새 정기결제 secret으로 사용한다. 키 변경만으로 카드가 새 MID에 등록되지 않는다. 새 MID에서 카드 재등록이 필요하다. |
| 미완료 주문·카드 등록·가상계좌 | 이전 키로 시작한 흐름이 새 키로 끝날 수 있다. 구 가상계좌는 DB 초기화만으로 취소되지 않는다. 완료/만료/취소를 먼저 대사해야 한다. |
| webhook·환불 작업 | 토스 webhook은 MID별 등록이다. 계정 B의 새 MID에 URL과 이벤트를 다시 등록해야 한다. 구 webhook 재전송이나 DB의 환불 재시도는 현재 secret으로 재조회해 실패할 수 있다. [토스 webhook](https://docs.tosspayments.com/guides/v2/webhook). |
| 이용권·크레딧 | 우리 DB의 지급 기록이어서 키 변경 시 자동 삭제되지 않는다. 주문만 지우면 지급 기록과 잔액이 불일치할 수 있다. |

**10월 7일 사용자 지시로 위의 선별 삭제안은 폐기했다.** 운영 회원·관리자·결제·구독·환불·이용권·크레딧·프로젝트·릴리스 데이터와 DB 저장 설정을 모두 초기화한다. 계획은 m2-db의 정식 `_prod` DB **한 세트**를 구성하는 user/admin/release 컨테이너 3개와 각 데이터 볼륨을 제거하고, 같은 이름의 빈 컨테이너·볼륨을 다시 만든 후 마이그레이션과 최고 관리자 생성을 실행하는 것이다. 심사 종료로 더는 필요 없는 m4-prod 심사 앱·`_review` DB 세트도 새 운영 앱 정상 확인 뒤 제거한다. **m2-db의 개발 `_dev` DB 세트는 대상이 아니다.** 새 운영 계정은 다시 가입해야 하고 최고 관리자를 다시 만들어야 한다. 마이그레이션이 넣는 기본 상품·정책은 다시 생기지만 수동 수정값과 기존 권한·프로젝트는 돌아오지 않는다.

DB를 지워도 토스 측 테스트 거래·webhook 전송 이력, S3 파일과 외부 백업은 사라지지 않는다. 사용자 확인상 계정 A에 실결제는 없으므로 그 거래의 정산·환불 대사는 생략한다. 과거 결제의 앱 내부 조회·취소 경로는 삭제 후 사용할 수 없다. 삭제 대상 볼륨은 현재 서버의 Compose label·mount로 식별했다.

### 서버 출력으로 식별한 초기화·제거 대상 DB 볼륨

| 호스트 | Compose 프로젝트 | DB 컨테이너 | `/var/lib/postgresql/data` 볼륨 | 처리 |
|---|---|---|---|---|
| m2-db | `clipper-db-prod` | `clipper-db-user-prod` | `clipper_postgres_data_user_prod` | 빈 볼륨으로 재생성 |
| m2-db | `clipper-db-prod` | `clipper-db-admin-prod` | `clipper_postgres_data_admin_prod` | 빈 볼륨으로 재생성 |
| m2-db | `clipper-db-prod` | `clipper-db-release-prod` | `clipper_postgres_data_release_prod` | 빈 볼륨으로 재생성 |
| m4-prod | `clipper-pg-review-db` | `clipper-pg-review-db-user` | `clipper-pg-review-user-data` | 정식 운영 앱 확인 후 제거 |
| m4-prod | `clipper-pg-review-db` | `clipper-pg-review-db-admin` | `clipper-pg-review-admin-data` | 정식 운영 앱 확인 후 제거 |
| m4-prod | `clipper-pg-review-db` | `clipper-pg-review-db-release` | `clipper-pg-review-release-data` | 정식 운영 앱 확인 후 제거 |

위 이름은 사용자가 제공한 각 호스트의 `docker inspect` label·mount 출력과 일치한다. **개발 DB 볼륨과 다른 서비스의 볼륨은 대상이 아니다.** 아직 삭제 명령을 실행하지 않았다.

## 코드·배포에서 바뀔 가능성이 높은 부분

현행 `payment-checkout.component`는 일반결제에서 위젯 영역 두 개를 먼저 렌더링하고 `TossPaymentsSdkService.mountOneTime()`의 `widgets.requestPayment()`를 호출한다. 서버의 `PaymentCheckoutSessionService`는 일반결제 clientKey를 `TOSS_PAYMENTS_WIDGET_CLIENT_KEY`에서, `HttpTossPaymentsProvider`는 승인·조회·취소용 secret을 `TOSS_PAYMENTS_WIDGET_SECRET_KEY`에서 읽는다. 결과 화면에는 이미 가상계좌 **입금 대기**와 계좌 정보 표시가 있다. 주문의 내부 `key_set='widget'`는 DB 제약과 여러 업무 경로에 쓰이므로, 결제창 전환에서 바꿀지 여부는 별도 migration 영향으로 판단한다.

- **고객 웹:** 새 일반결제 키가 `ck`인 것이 확인됐으므로 `widgets()` 화면을 `payment().requestPayment()` 결제창으로 교체한다. 확인된 계약 수단은 카드·간편결제 통합창(`CARD`)과 계좌이체(`TRANSFER`)로 제공한다. 각 간편결제를 별도 자체창으로 직연동하는 범위는 아니다. 서버의 기존 승인·금액 검증·지급 계약을 유지한다. [카드·간편결제](https://docs.tosspayments.com/guides/v2/payment-window/integration), [계좌이체](https://docs.tosspayments.com/guides/v2/payment-window/integration-quick).
- **계약 수단 확인:** 토스 계정 B의 상점관리자 **계약・운영 → 이용정보 → MID `clidevxzdd` → 결제・부가서비스**에서 사용자가 신용·체크카드, 계좌이체, 카카오페이·토스페이·네이버페이를 확인했다. 가상계좌는 목록에 없으므로 UI에 노출하거나 라이브 발급을 시도하기 전에 계약 여부를 토스에 확인해야 한다. 현행 API는 가상계좌 처리 경로를 갖고 있지만 **코드가 있다는 것과 해당 MID로 실제 결제가 가능하다는 것은 다르다.** [토스 공식 FAQ](https://docs.tosspayments.com/resources/faq).
- **API·Infra:** 일반/정기결제 키를 서로 다른 MID와 test/live 환경으로 설정하고, 현재 `WIDGET_*`로 붙은 일반결제 변수명과 키 종류 사전 검사를 새 방식에 맞춘다. 현행 `validate-toss-payments-env.sh`는 네 키가 비어 있지 않고 일반/정기 값이 서로 다른지만 검사한다. **`test/live`와 `ck/sk`의 짝이나 실제 MID는 검사하지 않는다.** 따라서 배포 전 새 키의 접두사·환경·용도 검증을 보강하되 전체 키를 출력하지 않는다. 서버가 checkout 응답에 clientKey를 전달하므로 **키 값만 바꾸는 경우 API 컨테이너 재생성**이 필요하다. 결제창 코드가 바뀌면 고객 웹 이미지는 재빌드해야 한다. `CLIPPER_ENV=prod`만으로 토스 라이브 모드가 선택되지는 않는다.
- **정기결제:** 카드 등록 코드는 새 개별 연동 키와 방향이 맞는다. 운영 DB 전체 초기화로 구 `billingKey`와 자동 재청구 대상도 사라진다. 계정 B의 새 정기 MID에서 카드를 다시 등록한다.
- **가상계좌:** 이번 작업의 코드 변경·UI·테스트·라이브 실기에서 제외한다. 현 MID의 제공된 활성 계약 목록에도 없다. 9월 코드 조사에서 확인한 마스킹·환불 제약은 별도 후속 작업을 시작할 때 다시 사용한다. [가상계좌 연동·모의 입금](https://docs.tosspayments.com/guides/v2/payment-window/integration-virtual-account).
- **webhook:** 계정 B의 일반·정기 MID에서 현재 사용하는 이벤트의 등록·배달을 확인한다. 가상계좌 `DEPOSIT_CALLBACK`은 해당 수단의 계약·활성화가 확인된 뒤 등록·검증한다. 일반 상태와 입금 이벤트를 함께 등록한다면 중복 지급이 없는지도 확인한다. [토스 이벤트별 설명](https://docs.tosspayments.com/reference/using-api/webhook-events).
- **운영 배포:** 9월 15일 심사판은 정식 운영 컨테이너 3개를 중지하고 같은 공개 포트에 별도 Compose 프로젝트로 올렸다. 심사판이 그대로라면 표준 `deploy-prod.sh all`을 바로 실행하면 포트가 충돌한다. 현재 사용자가 없으므로 점검 시간 조율 없이 최신 이미지·설정 준비 → 심사 앱 중지 → 정식 운영 DB 3개 재생성·마이그레이션·최고 관리자 재생성 → 정식 앱 기동 → 도메인·라이브 결제 검증 → 심사 DB·볼륨 정리 순으로 진행한다. 심사 DB는 정식 DB로 복원하지 않는다. 9월 8일 [운영 DB 재생성 런북](../../web/clipper_infra/runbooks/recreate-prod-databases.md)은 정식 운영 앱만 실행 중인 상태를 전제로 하므로 현재 서버에서 그대로 실행하면 안 된다. [심사판 실행 기록](2026-09-15-pg-review-production-cutover-and-rollback.md).

## 실행 순서와 확인 문턱

1. **현황 확인:** 운영 도메인의 심사 앱과 양 DB 세트의 컨테이너·볼륨, m2-stage의 개발 앱 3개 실행과 소스 SHA, m4-prod의 배포 소스·운영 이미지 SHA를 확인했다. 인프라 실행안 커밋 `f5749a4`도 m4-prod checkout에 fast-forward됐다.
2. **초기화 전 확인:** 계정 A의 실결제 대사는 생략한다. 삭제 대상 Compose 프로젝트·컨테이너·볼륨의 실제 mount와 재생성 설정을 확인한다. 운영 회원·결제내역 등은 **전부 삭제**한다.
3. **격리 개발:** 최신 `origin/dev` 기준 새 브랜치·worktree에서 일반결제 UI와 필요한 API/Infra 검증을 수정한다. 가상계좌 특화 변경은 계약 확인 후 별도 범위로 다룬다. 새 테스트 키는 사용자가 비공개 서버 환경파일에 입력한다. 비밀 키는 코드·문서·대화·Git에 남기지 않는다.
4. **새 테스트 키 종단 간 거래는 이번 전환에서 보류:** 분리된 stage DB가 없고 기존 개발 DB에는 활성 구독·주문이 있다. 심사용 스택 재구성도 필요하므로 기존 개발·심사 앱/DB/키는 유지한다. 새 화면·수단은 정식 운영 앱 기동 후 결제 전에 확인하고, 실제 MID·승인·취소·webhook은 라이브 거래로 한 건씩 검증한다. 이 검증 공백을 테스트 성공으로 표현하지 않는다.
5. **운영 전환:** 준비된 최신 앱 이미지와 계정 B의 일반·정기 **라이브 키**를 비공개 설정에서 확인한다. 현재 사용자가 없으므로 별도 점검 시간 조율 없이 심사 앱을 중지해 새 주문·가입을 막고 정식 앱도 중지 상태인지 확인한다. m2-db 정식 운영 DB 3개를 재생성한 뒤 마이그레이션·최고 관리자 생성을 수행한다. 충돌 포트가 비었는지 확인한 후 정식 앱을 기동한다. 새 계정 가입·헬스·상품 가격·수단·원장·worker와 양 MID의 라이브 webhook을 확인하고, 실결제·환불 검증까지 마친 뒤 m4-prod 심사 DB/볼륨을 제거한다. B 계정의 API 키 접근 정책이 설정돼 있다면 m4-prod의 **외부로 나가는 공인 IP**가 허용됐는지 확인한다. 사설 IP `192.168.0.47`을 허용 IP로 착각하지 않는다. [토스 API 키 접근 정책](https://docs.tosspayments.com/reference/using-api/api-key-access-policy).
6. **사용자 실결제:** 운영 가격표와 대상 직원 계정을 확인한 후 사용자가 카드 등록/첫 구독 결제 → 추가 크레딧 카드 결제·환불 → 필요 시 계좌이체 결제를 실행한다. **가상계좌 발급·실입금·환불은 현 계약 목록에 없으므로 별도 계약 확인·활성화 후에만 진행한다.** 10/7 공개 **개발** API의 Basic 월간과 400 크레딧 상품 가격은 각각 **5,900원**으로 확인했다. **정식 운영 DB 가격 확인 전에는 실결제 금액으로 확정하지 않는다.** 카드 등록은 바로 첫 청구를 일으킨다. 가상계좌가 활성화되면 입금 전 크레딧 지급 금지와 입금 후 webhook·원장·환불을 대사한다. 각 결제의 실제 MID·상태·원장 건수와 환불 완료/은행 반환을 별도로 대사한다.

실결제 후 DB만 과거 상태로 되돌리면 토스 승인·입금이 사라지는 것은 아니다. 문제가 생기면 새 결제를 멈추고 이미 발생한 거래를 환불/대사한 뒤 앱·DB 복구 순서를 정해야 한다. 토스 문서의 시크릿 키 **재발급** 7일 중첩 기간은 이번 **다른 계정·다른 MID** 전환의 자동 롤백 보장이 아니다. [토스 API 키 재발급 정책](https://docs.tosspayments.com/reference/using-api/api-keys).

**개발서버 별도 주의:** 이번 전체 초기화 지시는 운영 `_prod`에 적용되고 임시 `_review`는 정식 운영 검증 후 정리한다. m2-db의 `_dev` 관리자 DB에는 활성 구독 4건·결제 준비 주문 1건이 확인됐다. 현행 결제 복구 scheduler는 매분 재청구·오래된 주문 복구·빌링키 삭제를 시도하므로 새 테스트 키를 개발 앱에 덮어쓰지 않는다. 개발 DB를 운영 DB 초기화 명령에 포함하지 않는다.

## 확인 완료와 다음 입력

- **완료:** 사용자가 m4-prod의 `hostname`·`docker ps -a`와 두 API 컨테이너의 비밀값 없는 `docker inspect` 요약을 제공했다. 심사판 3개 실행, 정식 운영 3개 중지, 별도 심사용 DB 3개 실행을 확인했다. 심사 API는 세 `_review` DB와 구 테스트 키를 쓰며, 중지된 정식 API는 `192.168.0.7`의 세 `_prod` DB와 구 테스트 키를 설정했다. 두 DB 세트의 Compose 프로젝트와 실제 데이터 볼륨 6개를 위 표대로 확인했다. m2-stage 개발 앱 3개가 모두 실행 중인 것도 확인했다. 계정 B 일반결제 MID의 라이브 클라이언트 키 접두사는 `live_ck_`로 확인됐다. 계약 수단은 카드·계좌이체 및 카카오·토스·네이버페이이고, 가상계좌는 제공된 목록에 없다. 사용자는 **운영 DB 전체 초기화** 및 심사 종료 후 `_review` 스택 폐기를 지시했다.
- **다음 입력:** 운영 이미지 3개와 비공개 라이브 키의 사전 검사는 끝났고 m4-prod의 인프라 checkout도 실행안 커밋 `f5749a4`로 갱신됐다. 사용자가 m4-prod에서 라이브 키 검사를 다시 통과한 뒤 심사용 앱 3개를 중지했다. 심사용 DB 3개와 `clipper-web-monitor`는 실행 중이다. m2-db의 정식 운영 DB 3개와 재생성 설정을 확인한 뒤 운영 컨테이너와 정확한 운영 볼륨 3개를 제거했고, 볼륨 부재도 확인했다. 같은 Compose 설정으로 **빈 운영 DB 3개와 전용 볼륨을 재생성**했다. User/Admin/Release 포트 55202/55212/55222가 맞고 운영·개발 DB 각 3개가 모두 healthy다. m4-prod에서 `clipper-web-api:prod`로 User → Admin → Release migration을 모두 완료했고 대상 DB명·포트를 확인했다. 최고 관리자 seed도 `created operator:`로 완료했으며 계정 정보는 문서에 적지 않았다. 다음은 임시 입력파일 삭제와 정식 앱 기동이다. 계정 A 거래 대사는 생략한다. 가상계좌 실기는 별도 후속 작업이다. 전체 키·설정 파일은 공유하지 않는다.

이 문서는 현황·근거 기록이다. 선택한 설계와 검증 기준은 [10/7 라이브 전환 설계](../../clipper_docs/architecture/2026-10-07-toss-live-cutover-design.md), 작업 순서는 [구현계획](../../clipper_docs/architecture/2026-10-07-toss-live-cutover-implementation-plan.md)에 정리했다. **사용자 결정으로 가상계좌는 이번 작업에서 제외한다.** 서버 확인 결과와 실제 테스트 증거가 들어오면 미확인 항목을 확정하거나 수정한다.
