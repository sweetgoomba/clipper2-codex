# 운영 도메인 카드사 심사용 전환 — 상세 실행 기록·복원 런북

기준일: **2026-09-15 / Asia/Seoul**. 심사용 운영 전환과 사용자 결제 검증 완료. **기존 운영 복원은 아직 실행하지 않았다.**

이 문서는 사용자가 서버에서 실행하고 대화에 제공한 결과를 정리한 정본이다. 에이전트가 서버에 재접속하여 검증한 문서는 아니다. 앞으로도 **서버 명령은 사용자가 실행하고 에이전트는 방법만 안내한다.** 초기에 에이전트가 개발/운영 SSH 포트 연결을 시도했지만 모두 timeout이었다. 사용자 정정 이후 직접 서버 접속을 하지 않았다.

[실행 명령 전체 부록](2026-09-15-pg-review-production-cutover-commands.md)을 함께 읽는다. 부록은 과거 실행 기록이며 다시 전체 실행하는 설치 스크립트가 아니다. 아래 복원 명령은 향후 사용할 절차로 미실행이다.

## 1. 목적·승인 범위

- 카드사 한 곳이 `dev.clipperstudio.ai`의 `dev` 때문에 운영 도메인 제출을 요구했다. 다른 카드사는 이미 심사를 통과했다는 사용자 설명.
- 개발 고객페이지는 Google 로그인 없이 심사용 단건·정기결제를 진행할 수 있었지만, 기존 운영은 PG 전체 구현으로 비로그인 결제를 차단했다.
- 운영은 실제 이용자 없이 사용자 본인의 PG 테스트용이었다. 사용자가 심사 기간 운영 Client/Admin/API 전체 교체와 기존 로그인·구매 화면 미사용을 승인했다.
- `https://clipperstudio.ai` 주소를 유지하면서 심사용 화면을 제공한다. dev 주소로 보내는 리다이렉트는 사용하지 않는다.
- 심사 종료 후 `integration/main-unification-20260911` 배포 예정. **기존 운영 이미지로 복원하는 것과 integration 신규 배포는 다르다.**

## 2. 장비·작업 위치

| 역할 | 장비/IP | 경로·설명 |
|---|---|---|
| 개발 Client/Admin/API | m2-stage / 192.168.0.23 | 형제 repo가 있는 clipper_infra에서 조사. 이번 출력에는 소스 절대경로 없음 |
| 기존 개발·운영 DB | m2-db / 192.168.0.7 | 사용자 /Users/metabuzz |
| 기존 운영 + 새 심사 앱/DB | m4-prod / 192.168.0.47 | 기존 소스 `/Users/m4-prod/Documents/projects/clipperstudio` |
| HTTPS 진입점 | m2-proxy / 192.168.0.2 | 기존 Nginx Proxy Manager upstream 그대로. 이번에 변경하지 않음 |
| 새 심사 작업 폴더 | m4-prod | `/Users/m4-prod/Documents/projects/clipper-pg-review-20260915` |

이하 **심사 root**는 위 새 심사 작업 폴더를 의미한다. 기존 운영 소스를 전환하지 않고 별도 Git clone 3개를 만들었다. Infra dev는 조사만 했으며, 심사 root에 복제·배포하지 않았다. 심사 설정은 별도 Compose JSON으로 생성했다.

## 3. 개발 버전 조사

실행한 조사: docker ps → container inspect → image inspect → git status/log. 개발 repo 4개 모두 미커밋 변경 없이 dev였고 다음 HEAD였다.

| 저장소 | 소스 HEAD | 실행 이미지 생성 시각(KST) |
|---|---|---|
| Client | `4b361efc742db797e85848c5aea90eb1736194c5` | 8/14 11:46:31 |
| Admin | `beda584fde924a9a97aa69f1856cbddafe69c94c` | 9/15 08:42:38 |
| API | `fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6` | 9/15 08:42:55 |
| Infra | `6cc7a3796409b931b7e13240826496fd3e8f5b73` | 해당 없음 |

개발 이미지와 컨테이너의 revision label은 비어 있었다. **위 소스 HEAD가 원래 개발 실행 이미지를 만든 정확한 커밋이라는 증거는 없다.** 이미지 생성 시각과 clean 소스를 대조하여 이 SHA들을 심사 재빌드 기준으로 선택했다. 새 이미지에는 기준 revision label을 추가했지만, 프런트엔드 주소 수정은 미커밋이므로 label만으로 최종 이미지의 모든 내용을 재현하지는 못한다.

개발 실행 이미지 ID:
- Client `sha256:da9c6d0810a178f00e47bf59b6f7ffa882fe8d43baf0c732b5ac5495db110d4a`
- Admin `sha256:6d73ecc5c3a138878be986302e4345eda2033e2c9dc64da24f34f93cbd293f91`
- API `sha256:f23eca69f8930daf8287aa3f24170f2681392bc6adb5a72616b8b4e2c64d8310`

## 4. 기존 운영 버전과 백업

| 컨테이너 | 기존 운영 revision |
|---|---|
| clipper-web-client-prod | `4d95a963cde6f4e4067244c6cc8c148bb66709ce` |
| clipper-web-admin-prod | `cd3a3069310bdae13f123615e1a1a2a8972187cd` |
| clipper-web-api-prod | `e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5` |

백업 태그: **before-pg-review-20260915-161706**.
백업 폴더: `/Users/m4-prod/clipper-backups/before-pg-review-20260915-161706`.

| 백업 image tag | image ID |
|---|---|
| clipper-web-client:before-pg-review-20260915-161706 | `sha256:4270bdf3ecbf3691525769e27f0a6b3c20aa2e4eff11673ad5f6e542969605b7` |
| clipper-web-admin:before-pg-review-20260915-161706 | `sha256:adc94fac13d57703d631c1fb44aca6a3316acbfb09b8d28762e2bd74e07376a5` |
| clipper-web-api:before-pg-review-20260915-161706 | `sha256:e045583c57aedb73ec1557ab95ea6eaa95b71592be5fc49837fe22dd641fb22c` |

보존한 것:
- 실행 이미지 ID에 백업 태그 추가, images.txt에 이름/ID 저장.
- 기존 `clipperstudio/clipper_infra/env/stack.prod.env`를 백업 폴더로 복사.
- 기존 운영 컨테이너 3개는 전환 시 stop만 수행. 삭제·재생성하지 않음.
- m2-db의 기존 prod DB/볼륨과 개발 DB는 변경하지 않고 유지.
- 기존 운영 소스와 secret mount 파일은 변경하지 않음.

한계:
- **Docker image tar export는 하지 않았다.** 백업 태그는 m4-prod Docker 안의 보존이며 별도 매체 백업은 아니다.
- **기존 운영 DB dump는 이번에 만들지 않았다.** 아래 dump는 개발 DB의 복사본이다.
- `.secrets` 자체를 이번 백업 폴더로 복사하지 않았다. 기존 컨테이너 재시작에는 원래 mount 파일이 계속 필요하다.
- `clipper-web-monitor`는 변경하지 않았다. image ID=`sha256:5747f1ec60b36cbd3d018a20611d50450243174030a28e4242fc736b436bacf5`. 감시 대상이 예전 컨테이너 이름일 경우의 영향은 미확인.

## 5. 심사용 소스·이미지

심사 root의 clipper_web_client/admin/api를 별도 clone하고 §3의 SHA로 detached checkout했다. Client/Admin 각각 `src/environments/environment.production.ts`의 API 주소만 `https://dev-api.clipperstudio.ai` → `https://api.clipperstudio.ai`로 변경했다.

태그: `clipper-web-{client,admin,api}:pg-review-20260915`.
label: 기준 commit의 `org.opencontainers.image.revision`, 변형 표시 `ai.clipper.deployment.variant=pg-review-production-domain`.
기존 :prod 태그는 덮어쓰지 않았다.

| 첫 빌드 이미지 | ID |
|---|---|
| Client | `sha256:f82c9fc0db4abf5f99e60848e6a53233c3d92d325a8fe73cfa569e5824b970a2` |
| Admin | `sha256:3b922e6635a92064875637da3c221f2c15ffe3cc6ee88e8b00a77750ec6832fc` |
| API | `sha256:5d136721f63f833494539461a1dbb85b775b4ed58b1c585c4856949751fe20b2` |

Client는 로고 권한 수정 후 같은 태그로 재빌드했다. **최종 Client image ID는 사용자 출력에 없어 미기록**이다. 위 첫 ID를 현재 ID로 오인하지 않는다.

## 6. 개발 DB 백업·전송·복원

m2-db의 `clipper-db-{user,admin,release}-dev`에서 POSTGRES_DB가 예상 dev 이름인지 확인하고 `pg_dump -Fc --no-owner --no-acl` 실행. `.part`로 받은 뒤 `pg_restore --list` 성공 시 `.dump`로 변경했다.

원본 폴더: `/Users/metabuzz/clipper-backups/pg-review-dev-20260915-162252`.
전송 목적지: 심사 root의 `db-backup`. 전송 수단의 실제 종류는 보고되지 않았으며, 양쪽 해시가 일치했다. 목적지 폴더700/파일600 설정. `.DS_Store`는 있었지만 복원 대상이 아니다.

| 파일 | bytes | SHA256 |
|---|---:|---|
| admin.dump | 127755 | `f39dfab4470b2c58537a885e619bdb4341ab11b6f3565b34b14a7b8243612458` |
| release.dump | 76420 | `1bd83d707ba037959f18f9df526bfaa1e8fb03377f6efe53a635dc89730ff408` |
| user.dump | 482549 | `ec893088944beb54084e28a1b3ab0569434d8e0570771529bd41e14c90d6d330` |

순서대로 DB를 dump했으므로 세 DB 전체가 하나의 동일 시점 스냅샷인 것은 아니다. --list는 목록 읽기 검사이며, 실제 복원 성공은 다음 결과로 별도 확인했다.

새 DB는 **m4-prod**에 생성. project=`clipper-pg-review-db`, 설정=`db.compose.json`, network=`clipper-pg-review`. postgres:16-alpine, 외부 포트 없음, role=clipper_review, DB마다 새 random 64자리 hex 비밀번호.

| 컨테이너 | DB | 볼륨 | 복원 후 public 테이블 수 |
|---|---|---|---:|
| clipper-pg-review-db-user | clipper_user_review | clipper-pg-review-user-data | 8 |
| clipper-pg-review-db-admin | clipper_admin_review | clipper-pg-review-admin-data | 19 |
| clipper-pg-review-db-release | clipper_release_review | clipper-pg-review-release-data | 9 |

`pg_restore --no-owner --no-acl --exit-on-error --single-transaction` 사용. 기존 dev/prod DB에 restore/DDL/삭제를 하지 않았다. 별도 초기 migration도 실행하지 않았다.

초기 명령은 zsh에서 `#`가 명령으로 해석되어 중단됐다. `setopt interactivecomments` 후 재실행하여 성공했다. 코드 블록 테두리인 백틱은 터미널에 붙이지 않는다.

## 7. 비밀값 전송과 API 설정

개발 API 조회 결과:
```text
CLIPPER_ENV=dev
TOSS_PAYMENTS_REVIEW_MODE=true
WEB_BASE_URL=https://dev.clipperstudio.ai
TOSS_PAYMENTS_RETURN_BASE_URL=https://dev-api.clipperstudio.ai
CORS_ORIGIN=https://dev.clipperstudio.ai,https://dev-admin.clipperstudio.ai
DB=clipper_user_dev / clipper_admin_dev / clipper_release_dev
```

API fdd0cb6의 심사 기능은 dev/local 및 테스트키일 때만 활성화된다. 따라서 **호스트/공개 주소는 운영이어도 내부 CLIPPER_ENV=dev를 유지**했다. 기존 deploy-prod.sh는 환경·DB명·포트·주소 검사가 있어 이 구성을 거부하므로 사용하지 않았다.

개발 실행 API에서 아래 5개만 JSON으로 추출했다. 키 값은 화면/문서/Git에 기록하지 않았다.
- TOSS_PAYMENTS_WIDGET_CLIENT_KEY: test_gck_ 접두사 확인
- TOSS_PAYMENTS_WIDGET_SECRET_KEY: test_gsk_ 접두사 확인
- TOSS_PAYMENTS_BILLING_CLIENT_KEY: test_ck_ 접두사 확인
- TOSS_PAYMENTS_BILLING_SECRET_KEY: test_sk_ 접두사 확인
- API_KEY_ENC_SECRET: 복사한 DB의 암호화 값과 호환하기 위해 유지

전송 원본: `/Users/metabuzz/clipper-backups/pg-review-keys-20260915-163205/review-secrets.json`.
목적지: 심사 root의 `review-secrets.json`, 권한600.
양쪽 SHA256: `8cbb91a9d4fc0ce43ed78c3b314bddf68126ffe65d7361148e134c9e18464ea9`.

API 설정=`api.compose.json`, project=`clipper-pg-review-app`, container=`clipper-pg-review-api`.
- NODE_ENV=production / PORT=3000 / CLIPPER_ENV=dev / TOSS_PAYMENTS_REVIEW_MODE=true.
- WEB_BASE_URL=https://clipperstudio.ai.
- TOSS_PAYMENTS_RETURN_BASE_URL=https://api.clipperstudio.ai.
- CORS_ORIGIN=https://clipperstudio.ai,https://admin.clipperstudio.ai.
- USER_JWT: 새 RSA2048 키 쌍. OPERATOR_JWT: 새 random secret. 각각 만료30m. 개발 JWT 키는 복사하지 않음.
- DB: clipper-pg-review-db-{kind}:5432, _review DB, 생성한 role/password.
- Google OAuth 값은 넣지 않았다. 로그인 없는 심사를 위한 구성이다. Admin 계정은 DB 복사에 포함되지만 Admin 로그인 자체의 성공 보고는 없었다.
- runner/S3/외부 AI 환경설정을 통째로 가져오지 않았다. 앱 모든 기능이 개발 환경과 같다는 뜻은 아니다.
- Compose의 `$` 변수 치환 방지를 위해 환경값의 `$`를 `$$`로 저장.

먼저 API만 127.0.0.1:43212→3000에서 실행했다. /health DB3개ok, /payments/review/config는 {"mode":"checkout"}. API 자체 초기화/telemetry retention 등이 복사 DB를 수정할 수 있지만 기존 DB에는 연결하지 않는다.

## 8. 공개 서비스 교체

api.compose.json에서 live.compose.json 생성. 기존 prod3개가 running이고 §4 image ID와 일치하는지 검사했다. HostConfig.PortBindings를 읽어 호스트IP/포트를 그대로 사용하고 API 내부 포트만3000으로 지정했다.

| 외부 주소 | 새 컨테이너 | 실제 포트 |
|---|---|---|
| https://clipperstudio.ai | clipper-pg-review-client | 192.168.0.47:42202→80 |
| https://admin.clipperstudio.ai | clipper-pg-review-admin | 192.168.0.47:42302→80 |
| https://api.clipperstudio.ai | clipper-pg-review-api | 192.168.0.47:43202→3000 |

기존 prod3개 stop → 같은 심사 project의 live 설정으로 up. 시작 실패 시 새 서비스를 stop하고 기존 prod를 start하는 fallback을 넣었다. 실제로는 새3개 healthy로 성공했고 fallback은 실행되지 않았다. 이 재생성으로 API 임시 포트43212는 사라졌다. NPM/DNS/SSL은 변경하지 않았다.

**앞으로 심사 앱은 live.compose.json으로 조작한다. api.compose.json으로 up하면 API가 임시 포트로 돌아가 공개 연결이 끊길 수 있다.**

## 9. 확인된 결과

- Client/Admin 운영 도메인 HTTP200.
- API health: {"status":"ok","service":"clipper_web_api","db":{"user":"ok","release":"ok","admin":"ok"}}.
- 심사 config: {"mode":"checkout"}.
- 사용자 단건·정기결제 성공 및 Clipper 주소가 dev로 바뀌지 않음 확인.
- 결제번호/카드정보/receiptToken은 수집하지 않았다. 에이전트가 거래내역을 직접 대조한 것은 아니다.
- 사용자가 https://clipperstudio.ai를 카드사 쪽에 전달했다고 보고.
- 이번 수동 검증은 integration 버전의 테스트 결과가 아니다. 자동 테스트 suite는 새로 실행하지 않았다.

## 10. 로고 403 원인·복구·영구 반영

HTML 경로=/assets/brand/logo_clipper_w.png. Git에 PNG9298bytes 존재. Angular public assets 포함 설정 정상.
원본 SHA256=`e8aa345cb2af1eed71e90c9e1ed610da5b6d68c8fb51acda99ef1e78b6df92d5`.

컨테이너 파일 해시는 일치했지만 외부403/text/html. 내부 직접 요청도403이었다. nginx/1.31.5, 외부 openresty 응답. 디렉터리들은755였고 PNG는root:root/600이라 nginx worker가 읽지 못했다.

clone 명령에 umask077을 적용한 영향으로 추정했다. clone 직후 권한 기록은 없지만 **파일 권한이 직접 원인인 것은 chmod 후200으로 확인**했다.

1. 컨테이너 PNG chmod644 → 외부200/image/png.
2. 심사 Client public 디렉터리755, 파일644.
3. Client만 같은 태그로 --no-cache 재빌드.
4. 임시 컨테이너에서 PNG mode644 검사.
5. live compose의 client만 --no-deps --force-recreate --wait로 재생성.
6. 재생성 후healthy, 외부200/image/png.

API/Admin/DB는 이 수정으로 재생성하지 않았다. 비밀파일/dump의600은 유지. 최종 Client ID와 Admin 전체 정적파일 권한 검증은 미확보.

## 11. 웹훅 제한

기존 Toss 개발자센터 등록(사용자 제시):
- 이름: clipper-prod-test-webhook
- 이벤트: BILLING_DELETED, DEPOSIT_CALLBACK, PAYMENT_STATUS_CHANGED
- URL: https://api.clipperstudio.ai/payments/tosspayments/webhook

이번에 수정/추가 등록하지 않았다. 심사 API fdd0cb6에는 해당 route가 없어 **코드상404가 예상**된다. 실제 웹훅 전송/배달기록 확인은 하지 않았다. 심사 결제는 브라우저 success redirect를 받아 서버가 승인하므로 성공할 수 있다.

기존 운영/integration에는 같은 webhook route가 있다. 복원 후 URL은 유지하되 배달기록과 실제 처리 결과를 확인해야 한다. 심사 주문은 별도 DB에 있으므로 지연 재전송을 기존 운영 주문과 혼동하지 않는다. 200만 응답하는 더미 route는 추가하지 않았다.

[Toss 공식 웹훅 안내](https://docs.tosspayments.com/guides/v2/webhook): 실패 시 재전송/실패 통지가 발생할 수 있다. 이번 결제 성공은 웹훅 정상 수신 증거가 아니다.

## 12. 현재 파일과 주의할 구분

심사 root에 다음이 있다:
- clipper_web_client/admin/api: 고정 커밋 clone. 프런트엔드 API주소 변경 및 Client public 권한 수정.
- db-backup/*.dump: 최초 개발 DB 복사본.
- review-secrets.json: 개발 테스트키/암호화 키.
- db.compose.json: 심사 DB3개 설정/비밀번호. project clipper-pg-review-db.
- api.compose.json: API 임시 포트 검증 설정(현재 공개 운영에 사용하지 않음).
- live.compose.json: 현재 공개 Client/Admin/API 설정. project clipper-pg-review-app.

JSON과 dump는 비밀정보를 포함하므로 Git/채팅에 올리지 않는다. 기존 운영 소스에서 일반 deploy/start를 하면 심사 서비스와 포트 충돌할 수 있다. 기존 운영 DB와 심사 DB는 별개이며 심사 데이터가 기존 DB로 자동 반영되지 않는다. image/volume prune, down -v는 사용하지 않았다.

## 13. 복원 A — 직전 PG 운영 버전으로 되돌리기 (미실행)

이 절차는 §4의 **예전 운영 이미지 + 그대로 남은 prod DB**로 돌아가는 방법이다. integration 신규 배포가 아니며 DB migration도 필요하지 않다. 모든 명령은 m4-prod에서 사용자가 실행한다.

### 13.1 상태 확인

```sh
cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
docker compose -p clipper-pg-review-app -f live.compose.json ps
docker compose -p clipper-pg-review-db -f db.compose.json ps
for c in clipper-web-client-prod clipper-web-admin-prod clipper-web-api-prod; do
  docker inspect --format '{{.Name}} | status={{.State.Status}} | image={{.Image}}' "$c"
done
```

기존 컨테이너3개가 존재하고 image ID가 §4와 일치하는지 확인한다. 달라졌거나 삭제됐다면 단순start를 하지 말고13.4를 따른다.

### 13.2 심사 종료 시점의 기록 보존

API를 stop해 신규 쓰기를 중단한 뒤 새 dump를 만든다. dump 실패 시 그대로 중단하고 원인을 확인한다. 최초 dev dump는 심사 후 발생한 거래 기록을 담지 않으므로 종료 시점 dump를 별도로 만든다.

```sh
(
  set -eu
  umask 077
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  docker compose -p clipper-pg-review-app -f live.compose.json stop api
  archive_dir="$HOME/clipper-backups/pg-review-final-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$archive_dir"
  cp db.compose.json api.compose.json live.compose.json review-secrets.json "$archive_dir/"
  for kind in user admin release; do
    docker exec "clipper-pg-review-db-$kind" sh -eu -c \
      'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' \
      > "$archive_dir/$kind.dump.part"
    docker exec -i "clipper-pg-review-db-$kind" pg_restore --list \
      < "$archive_dir/$kind.dump.part" > /dev/null
    mv "$archive_dir/$kind.dump.part" "$archive_dir/$kind.dump"
  done
  shasum -a 256 "$archive_dir/"*.dump
  printf '종료 시점 백업: %s\n' "$archive_dir"
)
```

### 13.3 기존 컨테이너 재시작

13.1의 기존 ID 확인, 13.2의 dump 성공 후 실행한다. 심사 서비스를 먼저 멈춰 포트를 비운다.

```sh
(
  set -eu
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  docker compose -p clipper-pg-review-app -f live.compose.json stop client admin api
  docker start clipper-web-api-prod clipper-web-client-prod clipper-web-admin-prod
  docker ps --filter name=clipper-web- --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
)
```

§15 외부·로그인·웹훅 검증을 수행한다. 기존 DB를 지우거나 심사 dump로 덮어쓰지 않는다.

복원 실패 시 기존prod3개를 다시 stop한 뒤 심사 root에서 다음으로 심사 서비스를 되살릴 수 있다(심사DB는 아직 실행 중이라는 전제):
```sh
(
  set -eu
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  docker stop clipper-web-api-prod clipper-web-client-prod clipper-web-admin-prod
  docker compose -p clipper-pg-review-app -f live.compose.json up -d --pull never --wait --wait-timeout 120
)
```

기존 운영 정상 확인 후 필요하면 심사DB를 `docker compose -p clipper-pg-review-db -f db.compose.json stop`으로 중지한다. volume/파일/container는 보존한다. 삭제는 별도 판단이다.

### 13.4 기존 컨테이너가 삭제된 경우

백업 image tag, 기존prod Compose/환경파일/secret mount, m2-db prod DB가 필요하다. image inspect로 §4의 ID를 확인한다. 자동pull/build하는 deploy-prod.sh all을 이전 버전 복원 용도로 사용하지 않는다.

기존 구성과 project명이 clipper-prod임을 확인하고, 아래 image override 파일을 만들어 기존 compose와 함께 사용한다. 파일 위치는 아직 정해지지 않았으므로 아래 예시 경로는 실제 생성한 절대경로로 바꿔야 한다.

```yaml
services:
  web-client:
    image: clipper-web-client:before-pg-review-20260915-161706
  web-admin:
    image: clipper-web-admin:before-pg-review-20260915-161706
  api:
    image: clipper-web-api:before-pg-review-20260915-161706
```

심사 서비스를 먼저 stop하고, 기존 환경/마운트/Compose가 백업 당시와 일치할 때만 다음 형식을 사용한다. 환경파일 백업을 현재 파일에 무조건 덮어쓰지 않는다.
```sh
docker compose -p clipper-prod \
  --env-file /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/env/stack.prod.env \
  -f /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/apps/compose.yml \
  -f /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/apps/compose.prod.yml \
  -f /확인한/절대경로/restore-images.override.yml \
  up -d --no-deps --pull never web-client web-admin api
```

## 14. 복원 B — integration 버전 신규 배포 (미실행)

기존 컨테이너를 start하는 것으로 통합 버전이 되지는 않는다. [통합 기록](2026-09-15-main-integration-result.md)의 보존된 web4 SHA:

| repo | integration 기준 |
|---|---|
| Client | 4d95a963cde6f4e4067244c6cc8c148bb66709ce |
| Admin | dade0ee63c2ab1f2461da693eccf1d36200ce705 |
| API | 31e014b6182a93b12a3899fd49cfc821269c28f2 |
| Infra | 948e8a12c7549fd418a066f672d2cb50af5dd808 |

진행 순서:
1. 심사 종료 확인. 기존 m4-prod source의 미커밋 변경 확인.
2. integration 브랜치 fetch 후 위 고정 버전 또는 이후 최신 변경 포함 여부를 결정하고 SHA 확정. 임의로 최신을 섞지 않는다.
3. 통합 결과의 필요한 테스트·빌드 검증. 이번 심사 버전 검증을 통합 검증으로 대체하지 않는다.
4. CLIPPER_ENV=prod, 기존prod DB3개/URL/JWT/암호화/HMAC키/secret mount 확인. review JSON을 재사용하지 않는다. API_KEY_ENC_SECRET와 TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET는 기존 데이터에 쓰던 값 유지.
5. **m2-db의 기존prod DB3개를 새로 백업**하고 복원 방법 확보. 개발dump는 대체재가 아니다.
6. 확정 버전으로 API/Admin/Client 이미지를 준비. 일반 `deploy-prod.sh all --build-only`는 내부 git pull이 있으므로 고정SHA 재현 시 개별 docker build를 사용한다(front는 ANGULAR_CONFIGURATION=prod).
7. 심사API 중지와 종료시점dump(§13.2). 기존prod API도 멈춰 있는지, prod DB에 쓰는 다른 작업이 없는지 확인.
8. **새 integration API 이미지**로 prod DB pending migration 적용. `migrate-db.sh prod`는 User→Admin→Release를 처리하며 대상 이름/포트를 확인하고 `migrate prod` 입력. 이전API 이미지를 잘못 사용하지 않는다.
9. 심사3개 서비스를 stop하고 prod설정으로 새3개 시작. 빌드가 끝난 일반 운영 구성이라면 `deploy-prod.sh all --start-only`는 재pull/build하지 않는다.
10. §15 검증 후 운영 정상 전환 판단. 심사 DB/파일은 보존한다.

### 14.1 기존 prod DB 백업 명령 형태 (미실행, m2-db)

integration migration 직전 확보하는 백업이다. 기존 운영API와 prod DB에 쓰는 작업을 멈춘 뒤 수행한다. 개발dump와 파일 위치를 구분한다.

```sh
(
  set -eu
  umask 077
  prod_backup_dir="$HOME/clipper-backups/prod-before-integration-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$prod_backup_dir"
  for kind in user admin release; do
    c="clipper-db-$kind-prod"
    actual_db=$(docker exec "$c" printenv POSTGRES_DB)
    test "$actual_db" = "clipper_${kind}_prod"
    docker exec "$c" sh -eu -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' > "$prod_backup_dir/$kind.dump.part"
    docker exec -i "$c" pg_restore --list < "$prod_backup_dir/$kind.dump.part" > /dev/null
    mv "$prod_backup_dir/$kind.dump.part" "$prod_backup_dir/$kind.dump"
  done
  shasum -a 256 "$prod_backup_dir/"*.dump
  printf 'prod DB 백업: %s\n' "$prod_backup_dir"
)
```

--list만으로 완전한 복원 가능성을 보증하지 않는다. 중요한 전환이면 별도 DB에 복원 검증 후 진행한다. 이 문서는 기존prod DB를 지우는 명령을 제공하지 않는다.

### 14.2 고정 integration 이미지 빌드 형태 (미실행, m4-prod)

기존 source repo를 승인한 integration SHA로 전환한 **후** 사용한다. 아래는 §14 표의 고정 SHA만 허용한다. 최신 integration을 선택하면 승인된 SHA로 기대값을 바꾼다. 코드가 다르면 빌드하지 않는다. 기존 :prod 태그는 바뀌지만 §4의 별도 백업 태그는 유지된다. 기존 container는 아직 재생성하지 않는다.

```sh
(
  set -eu
  source_root="/Users/m4-prod/Documents/projects/clipperstudio"
  build_fixed() {
    service="$1"
    expected="$2"
    repo="$source_root/clipper_web_$service"
    test -z "$(git -C "$repo" status --porcelain)"
    test "$(git -C "$repo" rev-parse HEAD)" = "$expected"
    if [ "$service" = api ]; then
      docker build --label "org.opencontainers.image.revision=$expected" -t "clipper-web-$service:prod" -t "clipper-web-$service:prod-$expected" "$repo"
    else
      find "$repo/public" -type d -exec chmod 755 {} +
      find "$repo/public" -type f -exec chmod 644 {} +
      docker build --build-arg ANGULAR_CONFIGURATION=prod --label "org.opencontainers.image.revision=$expected" -t "clipper-web-$service:prod" -t "clipper-web-$service:prod-$expected" "$repo"
    fi
  }
  test "$(git -C "$source_root/clipper_infra" rev-parse HEAD)" = 948e8a12c7549fd418a066f672d2cb50af5dd808
  build_fixed client 4d95a963cde6f4e4067244c6cc8c148bb66709ce
  build_fixed admin dade0ee63c2ab1f2461da693eccf1d36200ce705
  build_fixed api 31e014b6182a93b12a3899fd49cfc821269c28f2
)
```

### 14.3 migration·시작

준비1~8이 끝난 뒤 사용하는 실행 형태(이번에 미실행):
```sh
sh /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/migrate-db.sh prod
```
```sh
(
  set -eu
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  docker compose -p clipper-pg-review-app -f live.compose.json stop client admin api
  sh /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/deploy-prod.sh all --start-only
)
```

migration 후 실패했다면 예전이미지만 재시작해도 schema 호환이 보장되지는 않는다. 역migration을 무작정 실행하지 말고 새로 확보한 prod백업과 실제 schema 변경을 기준으로 복구한다. **심사dump를 prod DB에 복원하지 않는다.**

## 15. 복원 후 확인 (미실행)

```sh
for url in https://clipperstudio.ai https://admin.clipperstudio.ai; do
  curl --fail --silent --show-error --max-time 20 -o /dev/null \
    -w 'HTTP=%{http_code} | %{url_effective}\n' "$url"
done
curl --fail --silent --show-error --max-time 20 https://api.clipperstudio.ai/health
curl --silent --show-error --max-time 20 -o /dev/null -w 'review HTTP=%{http_code}\n' \
  https://api.clipperstudio.ai/payments/review/config
```

- 기존prod/integration은 익명심사 route404가 예상된다. checkout mode가 나오면 아직 심사API인지 조사.
- DB3개ok, Client/Admin 자산·로그인·인증 필수 구매 동작.
- 실제 container revision과 DB접속대상(비밀값 제외)이 선택 버전/prod인지 확인.
- Toss 동일 webhook URL의 배달기록과 실제 업무 처리 결과 확인. 단순200과 처리는 구분.
- monitor가 실제 운영컨테이너를 감시하는지 확인.
- 복원 일시/SHA/imageID/DB백업 위치/검증 결과를 본 문서에 추가.

## 16. 당일 후속 로컬 작업 (서버와 구분)

사용자 PC `/Users/jina/project/adlight`에서 통합API 실행 시 HMAC키 누락, 이어 operation_policies.plugin_key 누락 발생. 당시 .env Admin DB는 localhost:5433, .env.local은127.0.0.1:56433이었다. 마이그레이션 방법을 안내했지만 실행 완료 보고는 없었다.

사용자 요청으로 **원본8repo를 최신origin/dev로 전환**했다. integration branch/remote와 ignored env는 유지. 서버·DB는 변경하지 않았다. 이후 사용자가 API오류 해소·설치형앱 실행 정상 보고.

원본dev: Angular019687d9 / Electron0b43737 / Nest e99b396 / Python88b1da2 / Infra6cc7a37 / Adminbeda584 / APIfdd0cb6 / Client4b361ef. 이것은 서버의 integration 배포가 아니다.

## 17. 미확인·보존해야 할 사항

- 서버 상태는 사용자 실행 결과 근거. 이번 문서화 중 서버 접속 없음.
- 최종 로고수정 Client image ID, webhook실전송, Admin로그인, 전체정적asset, monitor대상 상태 미확보.
- 기존prod DB dump·Docker image tar 백업은 이번 작업에서 미실행.
- 심사clone의 소스 변경/Compose JSON을 commit·push한 보고 없음. 비밀JSON은 Git 대상이 아님.
- 복원A/B 모두 미실행. 위 문서 작성 자체로 추가 배포/DB작업을 하지 않는다.
