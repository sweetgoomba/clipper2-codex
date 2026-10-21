# 개발 서버 TossPayments 새 MID 동기화 조사

> **후속 상태(2026-10-16):** 아래 ‘배포 전·DB 초기화 전’ 설명은 10월 15일 조사 당시의 스냅샷이다. 이후 W06 세션에서 개발 DB 초기화·테스트 MID 키 전환·API/고객 웹 배포·테스트 거래 검증을 진행했다. 최신 코드 병합과 개발서버 실행 상태는 [2026-10-16 `dev` 병합·배포 스냅샷](../../clipper_docs/status/2026-10-16-dev-merge-and-deployment-snapshot.md)을 참조한다.

기준: 2026-10-15 KST. 이 문서는 개발 환경의 **코드 및 배포 준비 상태**를 조사한 기록이다. 운영 결제 취소 잔여 건의 후속 처리와는 별도 작업이다.

## 확인된 사실

- 10/7 운영 전환 때 개발 앱·DB·테스트 키는 유지했다. 당시 m2-stage 실행 revision은 인프라 `8adbfcd`, 고객 웹 `7282921`, 관리자 웹 `bdcbae3`, API `31f4482`였다. 10/7 개발 관리자 DB에는 활성 구독 4건, 취소 구독 1건, 결제 준비 주문 1건이 있었다. 10/15 현재 수량은 아래에서 재조회했다.
- **10/15 사용자 제공 m2-stage 실행 상태:** `clipper-dev` 프로젝트의 API revision은 `9c4f7a75c48ff61100c79067365cf01653c0ee67`, 고객 웹은 `934f851766a62ee44fd8b2f797f825875746a8b8`로 현재 원격 `dev`와 각각 일치한다. API `CLIPPER_ENV=dev`; 구 `WIDGET` 키는 `test/gck`·`test/gsk`, 빌링 키는 `test/ck`·`test/sk`, 새 `ONE_TIME` 두 변수는 미설정이다. 고객 웹 컨테이너에는 PG 키가 주입되지 않았다. 출력은 키 형식만 보여주므로 두 기존 키 세트의 MID 소속은 확인되지 않았고, 비공개 서버 환경파일 원문도 보지 않았다.
- **10/15 사용자 제공 m2-db 읽기 전용 결과:** `clipper_admin_dev`의 구독은 `active` 4건·`canceled` 1건, 빌링키가 있는 구독 4건·없는 구독 1건이다. 다음 청구 시각이 설정된 구독은 4건, 조회 시각 기준 이미 도래한 것은 0건, 가장 이른 시각은 **2026-10-18 10:59:40.673+09**이다. `billing_key_removal_status=not_requested` 5건. 주문은 `credit_topup/checkout_ready/widget` 1건, `subscription_initial/expired/billing` 1건, `subscription_initial/paid/billing` 4건이다. 개인 식별자·결제키·빌링키 값은 조회하지 않았다. 이 출력은 현재 DB 건수를 확인하지만 결제키의 실제 MID나 스케줄러의 향후 성공 여부는 증명하지 않는다.
- **10/15 사용자 결정:** 기존 개발 환경 데이터는 전부 삭제해도 된다. User/Admin/Release 개발 DB의 회원·구독·빌링키·주문·프로젝트·크레딧·릴리스 데이터를 새로 시작한다. 백업이나 기존 개발 결제 이력 보존은 요구하지 않는다. **지금 초기화하지 않고**, 최신 원격 `dev`에서 분기한 작업 브랜치의 변경을 검증해 `dev`에 병합하고 개발서버에 배포하는 전환 시점에 초기화한다. 이 결정은 운영 DB와 운영 결제에는 적용하지 않는다. 아직 삭제하거나 키를 교체한 것은 아니다.
- 10/15 원격 조회에서 Web API `dev=9c4f7a75`, `main=c6ef00b`; 고객 웹 `dev=934f851`, `main=0053af8`; 인프라 `dev=be2f9f5`, `main=3cf915d`다. 운영 전환의 API `c22d90f`, 고객 웹 `a27c346`, 인프라 `3cf915d`는 각각 현재 원격 `dev`의 조상이 아니다. 같은 기능이 별도 커밋으로 들어왔는지도 파일별로 대조했으며 아래 차이가 남는다.
- API `dev`는 단건 결제에 `TOSS_PAYMENTS_WIDGET_*`를 읽고 `customerEmail`을 체크아웃 세션이나 정기 청구에 전달하지 않는다. 운영 `main`은 새 단건 `TOSS_PAYMENTS_ONE_TIME_*`를 읽고 로그인 이메일을 단건 결제창, 정기 카드 등록, 첫 정기 청구, 자동 갱신, 즉시 요금제 변경 청구에 조건부로 전달한다. 승인 거절 처리와 만료 주문 정리도 운영 쪽에 추가됐다.
- 고객 웹 `dev`는 위젯 결제와 구 `WIDGET` 키 계약을 사용하고 토스 SDK 요청에 `customerEmail`을 전달하지 않는다. 운영 `main`은 일반/계좌이체 결제창과 이메일 전달을 사용한다. 인프라 `dev`도 `WIDGET_*` 변수와 구 preflight를 사용하고, 운영 `main`은 `ONE_TIME_*` 및 test/live 형식 검사와 상속 환경변수 차단을 사용한다.
- 고객 웹 `dev`에는 10/13 `bed65a3`의 **복귀한 빌링 인증창 정리** 수정이 이미 들어왔지만 운영 `main`의 결제창 구현에는 없다. 개발 동기화 때 운영 커밋으로 고객 웹 전체를 덮거나 이 수정을 되돌리지 않고, 새 단건 결제창 경로와 빌링 인증창 정리 경로를 함께 유지·검증해야 한다.
- 토스의 구매자 안내 메일은 단건 `requestPayment()`의 `customerEmail` 전달과 연결된다. 운영에서 이를 반영했으며, 개발 `dev` 코드에는 없다. 토스 관리자 화면의 별도 이메일 입력 토글만으로 이 코드 경로를 대체한다고 보지 않는다. 테스트 환경의 실제 메일 수신은 새 테스트 거래로 별도 확인해야 한다.

## 목표 계약과 전환 순서

계정 B의 일반결제 MID `clidevxzdd`에는 단건용 `test_ck_`/`test_sk_` 한 쌍, 정기결제 MID `bill_cldevp14i`에는 빌링용 `test_ck_`/`test_sk_` 한 쌍을 사용한다. 키 접두사 검사만으로 실제 MID 소속이나 client/secret 짝을 증명할 수 없으므로 토스 개발자센터에서 **MID와 테스트 환경을 선택한 화면**을 기준으로 대조한다. 시크릿 키 전체를 채팅·문서·Git에 남기지 않는다.

1. **현재 개발 서버 읽기 전용 확인 — 완료:** m2-stage 실행 API/고객 웹 image revision, `CLIPPER_ENV`, 구 `WIDGET_*`와 새 `ONE_TIME_*` 및 빌링 키의 존재·test/live 형식, 실제 Compose 작업 경로를 확인했다. 키의 MID 소속은 별도 확인한다.
2. **개발 DB 현재 상태 확인 및 처리 결정 — 방침 확정, 실행 보류:** 활성 구독, 빌링키 존재, 다음 청구 시각이 각각 4건이고 가장 이른 청구가 10/18이다. 집계만으로 이 세 조건이 동일한 네 행에 속한다고 단정하지 않는다. 사용자는 개발 데이터 전체 삭제를 선택했지만 전환 전까지 현재 DB를 유지한다. 구 `paymentKey`/`billingKey`는 새 MID로 이전하거나 재사용하지 않는다.
3. **작업 브랜치에서 코드 동기화·검증:** 구현 착수 시 각 대상 저장소의 **최신 원격 `dev`**를 확인해 거기서 작업 브랜치를 분기한다. 운영의 단건 결제창·키 계약, 이메일 전달, 승인 실패·만료 주문 처리, 고객 카드/결제내역 표시, 인프라 validator 중 필요한 변경을 충돌을 검토하며 반영한다. 운영 `main` 전체를 개발 `dev`에 덮어쓰지 않는다. 기존 결제 테스트·API/웹 빌드·인프라 preflight 테스트를 통과시키고 변경 내용을 검토한다. 이 단계에서는 개발서버 DB와 키를 변경하지 않는다.
4. **`dev` 병합 후 개발서버 전환:** 검증된 작업 브랜치를 `dev`에 병합한 뒤 병합된 `dev` revision의 개발 이미지를 먼저 빌드한다. 개발서버 배포 창에서 실제 `_dev` DB 3개의 Compose 프로젝트·컨테이너·볼륨을 읽기 전용으로 확인한다. 개발 API를 중지해 구 DB에 대한 자동 청구를 멈추고, **개발 DB 3개만** 재생성한다. 운영·다른 스택의 DB와 볼륨은 대상이 아니다. m2-stage의 ignored `env/stack.dev.env`에 계정 B의 두 MID별 **테스트** 키 4개를 사용자가 입력한다. 새 `ONE_TIME_*` 변수로 바꾸고 구 `WIDGET_*`는 제거한다. `TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET`과 `API_KEY_ENC_SECRET`, DB 연결, dev 반환 URL은 보존한다. 빈 개발 DB 3개에 새 이미지의 마이그레이션·필요한 seed를 적용한 뒤 API·고객 웹을 기동한다. Git 병합 자체는 DB 초기화를 실행하지 않는다.
5. **외부 설정 및 종단 간 검증:** 계정 B의 각 MID에서 `https://dev-api.clipperstudio.ai/payments/tosspayments/webhook`과 필요한 이벤트를 확인한다. 새 테스트 계정으로 정기 카드 등록·첫 청구와 단건 결제·취소를 각각 1건씩 수행하고, 토스 테스트 결제내역의 MID·앱 주문/지급·웹훅·이메일 수신을 대조한다. 테스트 거래도 기존 구독과 섞지 않는다.

**혼동 정정:** 개발 DB의 기존 구독·빌링키가 새 MID로 복사되거나 토스에 자동 등록되는 일은 없다. 다만 현재 갱신 코드는 DB에 저장된 빌링키를 읽어 현재 설정된 빌링 시크릿 키로 청구 요청을 보낸다. DB를 그대로 두고 키만 교체하면 구 데이터와 새 MID 인증 정보가 뒤섞인 요청이 생길 수 있다. 정확한 토스 오류 응답은 검증하지 않았다. User/Admin/Release 개발 DB를 빈 상태로 재생성하면 그 구 기록을 읽어 청구하는 경로 자체가 사라진다.

**빌링키와 서버 키의 구분:** `TOSS_PAYMENTS_BILLING_CLIENT_KEY`/`TOSS_PAYMENTS_BILLING_SECRET_KEY`는 MID별로 발급된 서버 연동용 설정이고, `billingKey`는 고객의 카드 등록 후 토스가 발급해 `customerKey`와 연결하는 결제수단 토큰이다. API는 이 값을 암호화해 저장한다(`billing-auth.service.ts`). 자동 갱신 대상 조회는 `billing_key_enc`와 `billing_key_fingerprint`가 모두 있는 구독만 선택하고, 직접 갱신도 둘 중 하나가 없으면 토스 청구 전에 `SUBSCRIPTION_NOT_RENEWABLE`로 중단한다(`typeorm-subscriptions.repository.ts`, `subscription-renewal.service.ts`). 따라서 두 값을 지우면 해당 구독의 Clipper 자동 청구는 막히지만 `active` 구독과 `next_billing_at` 등 다른 기록은 남는다. 선택한 개발 DB 전체 재생성은 이 기록까지 제거한다. DB 삭제만으로 토스 측 빌링키가 삭제되는 것은 아니다. 토스 측 키도 무효화하려면 기존 MID 인증으로 별도 빌링키 삭제 API가 필요하며, DB를 지우기 전에 처리해야 한다.

**선택한 데이터 처리:** User/Admin/Release 개발 DB 3개만 **작업 브랜치 검증과 `dev` 병합이 끝난 개발서버 배포 시점에** 새로 만든다. 그때 기존 개발 회원·프로젝트·이용권·크레딧·릴리스·결제 이력과 구 빌링키를 보존하지 않는다. 기존 구독의 빌링키 삭제를 토스에 요청하는 작업이나 구 거래의 환불·취소는 DB 초기화에 포함되지 않는다. 전환 전까지 현재 개발 DB와 테스트키를 유지한다. 실제 DB 서버의 `_dev` 컨테이너·볼륨 명칭과 Compose 소속을 확인한 뒤 삭제 명령을 작성·실행하고, 빈 DB에 마이그레이션과 필요한 seed를 적용한다. 서버 작업과 테스트 거래는 아직 실행하지 않았다.

**개발서버 배포 직전** m2-db에서 읽기 전용으로 정확한 삭제 대상을 확인하는 명령이다. 이 출력에는 DB 비밀번호나 PG 키가 포함되지 않는다. 결과의 세 컨테이너 모두 Compose 프로젝트 `clipper-db-dev`, DB 이름과 볼륨 이름 모두 `_dev`여야 한다. 실제 출력과 맞춰 개발 DB만 삭제·재생성할 명령을 확정한다.

```sh
docker inspect clipper-db-user-dev clipper-db-admin-dev clipper-db-release-dev | python3 -c '
import json, sys
for item in json.load(sys.stdin):
    config = item.get("Config") or {}
    labels = config.get("Labels") or {}
    db_name = next((entry.split("=", 1)[1] for entry in config.get("Env", []) if entry.startswith("POSTGRES_DB=")), None)
    mounts = [{"type": mount.get("Type"), "name": mount.get("Name"), "destination": mount.get("Destination")} for mount in item.get("Mounts", [])]
    print(json.dumps({"container": item.get("Name"), "composeProject": labels.get("com.docker.compose.project"), "composeService": labels.get("com.docker.compose.service"), "database": db_name, "mounts": mounts}, ensure_ascii=False))
'
```

## m2-stage에서 실행한 읽기 전용 확인 명령

사용자가 아래 명령을 실행해 앞의 10/15 결과를 제공했다. 키 값과 전체 `docker inspect` 결과는 공유하지 않았다. 이 출력은 환경 종류와 코드 revision을 알려주지만 **MID 소속은 증명하지 않는다**.

```sh
docker inspect clipper-web-api-dev clipper-web-client-dev | python3 -c '
import json, re, sys
items = json.load(sys.stdin)
names = ["TOSS_PAYMENTS_WIDGET_CLIENT_KEY", "TOSS_PAYMENTS_WIDGET_SECRET_KEY", "TOSS_PAYMENTS_ONE_TIME_CLIENT_KEY", "TOSS_PAYMENTS_ONE_TIME_SECRET_KEY", "TOSS_PAYMENTS_BILLING_CLIENT_KEY", "TOSS_PAYMENTS_BILLING_SECRET_KEY"]
for item in items:
    config = item.get("Config") or {}
    values = dict(x.split("=", 1) for x in config.get("Env", []) if "=" in x)
    labels = config.get("Labels") or {}
    def kind(value):
        match = re.match(r"^(test|live)_(gck|gsk|ck|sk)_", value or "")
        return "/".join(match.groups()) if match else ("present/other" if value else "unset")
    print(json.dumps({"container": item.get("Name"), "revision": labels.get("org.opencontainers.image.revision"), "composeProject": labels.get("com.docker.compose.project"), "composeDirectory": labels.get("com.docker.compose.project.working_dir"), "clipperEnv": values.get("CLIPPER_ENV"), "pgKeyKinds": {name: kind(values.get(name)) for name in names}}, ensure_ascii=False))
'
```

참고: [토스 API 키와 MID별 키 세트](https://docs.tosspayments.com/reference/using-api/api-keys), [결제 결과 이메일](https://docs.tosspayments.com/guides/v2/learn/payment-results), [MID별 웹훅](https://docs.tosspayments.com/guides/v2/webhook).

## m2-db에서 실행한 개발 관리자 DB 읽기 전용 확인 명령

사용자가 **m2-db**에서 다음 명령을 실행해 앞의 10/15 집계 결과를 제공했다. 구독·주문의 상태별 건수, 다음 자동 청구 시각과 빌링키 존재 건수만 출력했다. 사용자 ID, 결제키, 빌링키, 카드정보는 조회하지 않았다.

```sh
docker exec -i clipper-db-admin-dev sh -lc 'exec psql -X -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' <<'SQL'
BEGIN TRANSACTION READ ONLY;
SELECT 'database', current_database();
SELECT 'subscription_status', status, count(*) FROM subscriptions GROUP BY status ORDER BY status;
SELECT 'billing_schedule', count(*) FILTER (WHERE next_billing_at IS NOT NULL), count(*) FILTER (WHERE next_billing_at <= now()), min(next_billing_at)::text FROM subscriptions;
SELECT 'billing_key_presence', count(*) FILTER (WHERE billing_key_enc IS NOT NULL), count(*) FILTER (WHERE billing_key_enc IS NULL) FROM subscriptions;
SELECT 'billing_key_removal', billing_key_removal_status, count(*) FROM subscriptions GROUP BY billing_key_removal_status ORDER BY billing_key_removal_status;
SELECT 'order_status', purpose, status, key_set, count(*) FROM payment_orders GROUP BY purpose, status, key_set ORDER BY purpose, status, key_set;
COMMIT;
SQL
```
