# 개발서버 정식 PG 전환 실행 런북

작성일: **2026-09-18 KST**

상태: **검토용 초안 / 실행 승인 아님**

이 문서는 개발서버를 정식 PG 통합 소스로 전환할 때 사용자가 각 장비에서 실행할 절차다. 에이전트는 서버에 직접 접속하지 않는다. 이 문서를 작성하거나 검토하는 행위는 DB migration, 배포, push의 승인이 아니다. 실제 실행 전 사용자가 이 런북과 실행 시점을 다시 확인해야 한다.

## 1. 이번 전환의 범위

### 바꾸는 것

- m2-stage의 개발 Customer Web, Admin Web, Web API를 현재 통합 브랜치 코드로 교체한다.
- m2-db의 개발 User/Admin/Release DB에 현재 Web API migration을 적용한다.
- 개발 API를 정식 Toss Payments PG V2 환경 계약으로 기동한다.
- 새 독립 개발판 데스크톱은 `development` 인증·릴리즈 대상으로 개발 API를 사용한다.

### 보존하는 것

- User DB의 사용자, 로그인 세션, 데스크톱 auth code, 프로젝트와 클립.
- Admin DB의 운영자, 운영자 세션, provider credential, 오류·telemetry 데이터.
- Release DB의 release version/build/artifact/event.
- 기존 `API_KEY_ENC_SECRET`, Google OAuth 설정, JWT 키 파일. 특히 `API_KEY_ENC_SECRET`을 바꾸면 보존한 provider credential을 복호화하지 못하므로 전환 과정에서 회전하지 않는다.
- m2-proxy의 기존 `dev.*` 도메인과 upstream. 이번 전환에서는 DNS/Nginx Proxy Manager를 바꾸지 않는다.

### 승인된 출시 전 정리 범위

- 구형 `licenses`, `purchase_requests`, `plans`, `credit_ledger`, `token_usage` 제거.
- 구형 operation run/resolution history 제거.
- 카드사 review 목적으로 만든 옛 payment order/event 제거.
- 새 정식 PG `user_access_grants`, `credit_grants`, `subscriptions`, `payment_orders`, `operation_runs`는 빈 상태에서 시작.
- 기존 개발 사용자는 계정·로그인은 보존되지만 무료체험을 소급 지급받지 않는다. 신규 가입자만 400 credits / 30일 무료체험을 받는다.

이는 운영 DB 전체 초기화가 아니다. 컨테이너나 volume을 삭제하지 않으며 사용자·로그인·프로젝트·운영자·provider·release 데이터는 보존한다.

### 이번 전환에서 하지 않는 것

- 운영서버·운영 DB 변경.
- 실제 ML 플러그인 실행과 Build 5 전체 QA.
- Windows 설치형 앱 실기. Windows 서버에서 별도로 검증한다.
- macOS 자동 업데이트 활성화. 현재 HOLD를 유지한다.
- 구 개발판 API 호환 보장. 출시 전 전환이므로 새 개발판과 새 개발 API를 같은 계약으로 배포한다.
- 프로젝트 자동 이관. 필수 템플릿은 검증된 `.cliptpl` 내보내기/가져오기를 사용한다.

## 2. 실행 장비와 영향

| 장비 | 역할 | 실행 위치 | 영향 |
|---|---|---|---|
| 로컬 개발 Mac | 실행 전 source/테스트 증거 확인 | `/Users/jina/project/adlight` | 서버·DB 변경 없음 |
| m2-stage `192.168.0.23` | Web/Admin/API source, image build, 서비스 중지·기동, migration runner | `/Users/metabuzz/Desktop/project/clipper2` | 점검 중 `dev`, `dev-admin`, `dev-api` 사용 불가 |
| m2-db `192.168.0.7` | 개발 DB 최종 dump, 전후 검증, 필요 시 세 DB 복원 | `/Users/metabuzz` 및 실행 중인 DB 컨테이너 | 승인 후 실제 개발 DB schema/승인된 구 데이터 변경 |
| m2-proxy `192.168.0.2` | 기존 HTTPS 진입점 | 변경하지 않음 | 조회만 필요할 수 있음 |

권장 점검 창은 60분이다. 로컬 복제본에서는 dump가 1초 미만, migration 자체는 수십 초 범위였지만 서버 상태·image build·검증·복구 여유까지 포함한다. 실제 중단 시간은 API 중지부터 최종 smoke 통과까지다.

점검 시작 전 내부 개발 사용자에게 다음을 알린다.

- 개발 웹과 개발판 앱을 종료한다.
- 진행 중 렌더·결제·카드 등록을 끝내거나 취소한다.
- 점검 중 다시 실행하거나 결제하지 않는다.
- 기존 개발판은 전환 뒤 지원 대상이 아니다. 필요한 템플릿을 미리 export한다.

## 3. 고정할 source와 선행 게이트

공통 브랜치: `integration/dev-pg-local-validation-20260917`

| 저장소 | 검증한 HEAD | 원격 상태 |
|---|---|---|
| `desktop/clipper_angular` | `19b407a7a6de56d7a43428f688e3e4e7258fdc8d` | origin과 일치 |
| `desktop/clipper_electron` | `d95c05058439a8be5c08d34ee3cb9890b2005b35` | origin과 일치 |
| `desktop/clipper_nestjs` | `884fa8bc7abf5d802a142c918568d8e606041900` | origin과 일치 |
| `desktop/clipper_python` | `60417ce865499df519971650a43a7ca1a82d9867` | origin과 일치 |
| `web/clipper_infra` | `f0af3f52be99ed19b6594f25ac81ba2375ec3a05` | origin과 일치 |
| `web/clipper_web_admin` | `01d0b93ad3c4b6803060c919ebd80d9ae656c142` | origin과 일치 |
| `web/clipper_web_api` | `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f` | origin과 일치 |
| `web/clipper_web_client` | `a4bc54b5852e82d0699f63e6198d409746dd0ee0` | origin과 일치 |

전환 전 필수 게이트:

1. Angular `19b407a7`와 Nest `884fa8bc`는 사용자 승인 후 원격 통합 브랜치에 push하고 원격 SHA 일치까지 확인했다. 이 두 커밋은 필수 템플릿 이관에서 기본 템플릿 중복을 막는다.
2. 8개 원격 branch의 HEAD가 위 표와 일치한다. 하나라도 다르면 새 변경 범위를 다시 리뷰한다.
3. m2-stage의 네 web repo가 clean이다. dirty이면 자동 stash/reset/삭제하지 않고 중단한다.
4. 현재 실행 image ID, Git branch/HEAD, env·secret 파일 hash를 기록한다.
5. 실제 개발 DB dump 리허설과 로컬 acceptance 결과를 다시 읽는다.
   - [개발 DB 복제본 리허설 결과](2026-09-18-development-db-clone-rehearsal-result.md)
   - [비-ML 로컬 acceptance](2026-09-18-w04-non-ml-local-acceptance.md)

push 직전 fresh 검증: Angular 전체 **4,494 PASS**, 스타일 계약 **6 PASS**, `build:devapp` PASS. Nest 전체 **2,685 PASS**, `npm run build` PASS. Nest 전체 테스트는 실제 개발 앱용 `.env.local`의 `CLIPPER_AUTH_MODE=jwt`를 테스트 자식 서버가 읽지 않도록 `CLIPPER_AUTH_MODE=local`을 명령에 명시했다. 인증 제품 코드는 완화하지 않았다. 이 테스트 파일이 개발자 환경파일에 의존하지 않도록 고정하는 보완은 후속 테스트 품질 항목이며, 이번 전환 source SHA에는 추가하지 않았다.

## 4. Gate A — m2-stage 사전 조사와 기존 실행물 보존

목적: 현재 개발서버를 정확히 기록하고 이전 image/env를 복구 가능하게 보존한다.

영향: 읽기와 image tag/tar 생성만 한다. 실행 중인 컨테이너와 DB는 바꾸지 않는다.

### 4-1. 현재 source와 실행 image 기록

m2-stage에서 실행한다.

```sh
set -eu
root=/Users/metabuzz/Desktop/project/clipper2
cutover_id="dev-pg-$(date +%Y%m%d-%H%M%S)"
backup_dir="$HOME/clipper-backups/$cutover_id"
umask 077
mkdir -p "$backup_dir"
printf '%s\n' "$cutover_id" | tee "$backup_dir/cutover-id.txt"
printf '%s\n' "$cutover_id" > "$HOME/clipper-backups/current-dev-pg-cutover-id.txt"

for repo in clipper_infra clipper_web_client clipper_web_admin clipper_web_api; do
  git -C "$root/$repo" status --short --branch
  git -C "$root/$repo" log -1 --format='%H | %cI | %s'
done | tee "$backup_dir/source-before.txt"

for c in clipper-web-client-dev clipper-web-admin-dev clipper-web-api-dev; do
  docker inspect --format '{{.Name}} | image={{.Config.Image}} | imageID={{.Image}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$c"
done | tee "$backup_dir/containers-before.txt"
```

`source-before.txt`에 미커밋 파일이 있으면 여기서 중단한다. `cutover-id.txt`의 값을 m2-db 작업에도 동일하게 사용한다.

### 4-2. env·secret 보존

값을 화면에 출력하지 않는다.

```sh
set -eu
root=/Users/metabuzz/Desktop/project/clipper2
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
backup_dir="$HOME/clipper-backups/$cutover_id"
env_file="$root/clipper_infra/env/stack.dev.env"
secret_dir=/opt/clipper/secrets/web-api-dev

test -f "$env_file"
test -d "$secret_dir"
cp -p "$env_file" "$backup_dir/stack.dev.env"
sudo tar -C "$(dirname "$secret_dir")" -cpf "$backup_dir/web-api-dev-secrets.tar" "$(basename "$secret_dir")"
sudo chown "$(id -un):$(id -gn)" "$backup_dir/web-api-dev-secrets.tar"
chmod 600 "$backup_dir/stack.dev.env" "$backup_dir/web-api-dev-secrets.tar"
shasum -a 256 "$env_file" "$backup_dir/stack.dev.env" "$backup_dir/web-api-dev-secrets.tar" > "$backup_dir/config-sha256.txt"
sudo stat -f 'mode=%Sp owner=%Su path=%N' "$env_file" "$secret_dir" "$secret_dir"/* > "$backup_dir/config-modes.txt"
```

`current-dev-pg-cutover-id.txt`의 값이 4-1 출력과 다르면 자동 진행하지 않고 정확한 이번 ID로 고친다. secret을 읽을 권한이 없을 때 권한을 느슨하게 바꾸지 않고 `sudo tar/stat`만 사용한다.

### 4-3. 이전 image를 tag와 tar로 보존

먼저 `df -h`와 `docker system df`로 공간을 확인한다. 공간 부족 시 prune하지 말고 중단한다.

```sh
set -eu
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
backup_dir="$HOME/clipper-backups/$cutover_id"

df -h "$HOME"
docker system df

docker tag "$(docker inspect --format '{{.Image}}' clipper-web-client-dev)" "clipper-web-client:rollback-$cutover_id"
docker tag "$(docker inspect --format '{{.Image}}' clipper-web-admin-dev)" "clipper-web-admin:rollback-$cutover_id"
docker tag "$(docker inspect --format '{{.Image}}' clipper-web-api-dev)" "clipper-web-api:rollback-$cutover_id"

docker save -o "$backup_dir/dev-app-images.tar" \
  "clipper-web-client:rollback-$cutover_id" \
  "clipper-web-admin:rollback-$cutover_id" \
  "clipper-web-api:rollback-$cutover_id"
chmod 600 "$backup_dir/dev-app-images.tar"
shasum -a 256 "$backup_dir/dev-app-images.tar" | tee "$backup_dir/dev-app-images.sha256"
```

Gate A 통과 조건:

- 네 repo clean.
- 실행 중인 세 container image ID 기록 완료.
- env·secret backup 및 hash 기록 완료.
- 이전 image 세 개의 rollback tag와 tar 생성 완료.
- 이 단계까지 서비스 중단·DB 변경 0건.

## 5. Gate B — m2-stage 통합 source 고정과 새 image 사전 빌드

목적: 중단 전에 새 image 세 개를 만들고 정확한 source revision을 검증한다.

영향: Git checkout과 로컬 Docker image tag가 바뀐다. 실행 중인 컨테이너는 아직 이전 image를 계속 사용한다.

다음 함수는 자동 merge/rebase/reset을 하지 않는다. 원격 branch가 없거나 local branch가 갈라졌거나 HEAD가 다르면 중단한다.

```sh
set -eu
root=/Users/metabuzz/Desktop/project/clipper2
branch=integration/dev-pg-local-validation-20260917

prepare_repo() {
  repo="$1"
  expected="$2"
  path="$root/$repo"
  test -z "$(git -C "$path" status --porcelain)"
  git -C "$path" fetch origin "$branch"
  if git -C "$path" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$path" switch "$branch"
  else
    git -C "$path" switch --track "origin/$branch"
  fi
  git -C "$path" pull --ff-only
  actual=$(git -C "$path" rev-parse HEAD)
  test "$actual" = "$expected"
  printf '%s | %s\n' "$repo" "$actual"
}

prepare_repo clipper_infra f0af3f52be99ed19b6594f25ac81ba2375ec3a05
prepare_repo clipper_web_client a4bc54b5852e82d0699f63e6198d409746dd0ee0
prepare_repo clipper_web_admin 01d0b93ad3c4b6803060c919ebd80d9ae656c142
prepare_repo clipper_web_api fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f

cd "$root/clipper_infra"
if ! sh scripts/validate-toss-payments-env.sh env/stack.dev.env; then
  printf 'PG 환경 계약이 아직 맞지 않습니다. 값을 출력하지 말고 stack.dev.env를 수정한 뒤 이 Gate를 다시 실행하세요.\n'
  exit 1
fi
sh scripts/deploy-dev.sh all --build-only
```

`stack.dev.env`은 기존 파일을 유지하면서 최소한 다음 계약을 만족해야 한다. 값은 채팅이나 로그에 출력하지 않는다.

- `CLIPPER_ENV=dev`, `CLIPPER_RELEASE_CHANNEL=dev`
- DB: `192.168.0.7`, ports User `55203`, Admin `55213`, Release `55223`, 정확한 dev DB 이름·사용자
- `WEB_BASE_URL=https://dev.clipperstudio.ai`
- `TOSS_PAYMENTS_RETURN_BASE_URL=https://dev-api.clipperstudio.ai`
- Widget client/secret과 Billing client/secret은 각각 설정되고 서로 재사용하지 않음
- 독립된 `TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET`
- 제거된 review/direct PG 변수 없음
- `DESKTOP_AUTH_TARGET=development`
- `DESKTOP_RELEASE_TARGET=development`
- `API_KEY_ENC_SECRET`은 전환 전 값과 동일
- Google callback은 `https://dev-api.clipperstudio.ai/auth/google/callback`

validator가 실패하면 기존 env를 example로 덮어쓰지 않는다. `vi -n env/stack.dev.env`로 실패 메시지에 나온 변수만 수정하고, 위 validator부터 다시 실행한다. 신규 HMAC secret이 필요한 경우에만 비공개 터미널에서 `openssl rand -hex 32`로 만들며 그 값을 채팅·문서에 남기지 않는다. 기존 Google/Toss/JWT/API 암호화 값은 임의로 재발급하지 않는다.

새 image revision을 확인한다.

```sh
for image in clipper-web-client:dev clipper-web-admin:dev clipper-web-api:dev; do
  docker image inspect --format '{{index .RepoTags 0}} | imageID={{.Id}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$image"
done

test "$(git -C /Users/metabuzz/Desktop/project/clipper2/clipper_infra rev-parse HEAD)" = f0af3f52be99ed19b6594f25ac81ba2375ec3a05
test "$(git -C /Users/metabuzz/Desktop/project/clipper2/clipper_web_client rev-parse HEAD)" = a4bc54b5852e82d0699f63e6198d409746dd0ee0
test "$(git -C /Users/metabuzz/Desktop/project/clipper2/clipper_web_admin rev-parse HEAD)" = 01d0b93ad3c4b6803060c919ebd80d9ae656c142
test "$(git -C /Users/metabuzz/Desktop/project/clipper2/clipper_web_api rev-parse HEAD)" = fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f
```

Gate B 통과 조건:

- source SHA 네 개가 표와 정확히 일치.
- Toss env preflight 통과.
- image 세 개 build 성공.
- image revision label이 각 source SHA와 일치.
- 기존 컨테이너는 아직 이전 image ID로 실행 중.

## 6. Gate C — 점검 시작과 쓰기 정지

목적: 세 DB의 최종 dump가 같은 서비스 정지 구간을 반영하도록 모든 정상 쓰기 경로를 차단한다.

영향: 이 시점부터 개발 Web/Admin/API와 새·옛 개발판의 서버 기능을 사용할 수 없다.

m2-stage에서 실행한다.

```sh
docker stop clipper-web-client-dev clipper-web-admin-dev clipper-web-api-dev
docker ps --filter 'name=clipper-web-' --format 'table {{.Names}}\t{{.Status}}'
```

세 컨테이너가 실행 목록에서 없어야 한다. monitor, DB 컨테이너, proxy는 중지하지 않는다.

다음도 확인한다.

- Release runner나 수동 SQL처럼 세 dev DB에 직접 쓰는 다른 작업이 없어야 한다.
- Toss 테스트 결제·카드 등록을 시작하지 않는다.
- 이미 시작된 결제 callback이 의심되면 dump/migration으로 진행하지 말고 먼저 provider 상태와 DB 반영 여부를 확인한다.

## 7. Gate D — m2-db 전환 직전 최종 dump와 기준값

목적: destructive migration 전 정확한 복구점과 보존 대상 해시를 만든다.

영향: DB 읽기만 한다. API가 중지된 동안 수행한다.

### 7-1. 세 DB dump

m2-db에서 실행한다. `cutover_id`에는 m2-stage 4-1에서 출력된 같은 값을 넣는다.

```sh
set -eu
umask 077
printf 'm2-stage에서 출력된 이번 cutover ID를 입력하세요: '
read -r cutover_id
printf '%s\n' "$cutover_id" | grep -Eq '^dev-pg-[0-9]{8}-[0-9]{6}$'
mkdir -p "$HOME/clipper-backups"
printf '%s\n' "$cutover_id" > "$HOME/clipper-backups/current-dev-pg-cutover-id.txt"
dump_dir="$HOME/clipper-backups/$cutover_id"
test ! -e "$dump_dir"
mkdir -p "$dump_dir"

for kind in user admin release; do
  container="clipper-db-$kind-dev"
  expected_db="clipper_${kind}_dev"
  actual_db=$(docker exec "$container" printenv POSTGRES_DB)
  test "$actual_db" = "$expected_db"
  docker exec "$container" sh -eu -c \
    'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl' \
    > "$dump_dir/$kind.dump.part"
  docker exec -i "$container" pg_restore --list < "$dump_dir/$kind.dump.part" > /dev/null
  mv "$dump_dir/$kind.dump.part" "$dump_dir/$kind.dump"
done

chmod 700 "$dump_dir"
chmod 600 "$dump_dir"/*.dump
(cd "$dump_dir" && shasum -a 256 admin.dump release.dump user.dump | tee dump-sha256.txt)
ls -lh "$dump_dir"/*.dump
```

DB host 한 대에만 두면 디스크 장애 때 복구점이 사라진다. migration 전에 세 dump와 hash 파일을 m2-stage의 같은 cutover 폴더 아래에도 복사한다. m2-db에서 실행한다.

```sh
set -eu
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
dump_dir="$HOME/clipper-backups/$cutover_id"
ssh metabuzz@192.168.0.23 "umask 077; mkdir -p /Users/metabuzz/clipper-backups/$cutover_id/db-final"
scp -p "$dump_dir"/user.dump "$dump_dir"/admin.dump "$dump_dir"/release.dump "$dump_dir"/dump-sha256.txt \
  "metabuzz@192.168.0.23:/Users/metabuzz/clipper-backups/$cutover_id/db-final/"
ssh metabuzz@192.168.0.23 \
  "cd /Users/metabuzz/clipper-backups/$cutover_id/db-final && shasum -a 256 -c dump-sha256.txt"
```

SSH/SCP가 설정되지 않았다면 임의로 계정·방화벽을 바꾸지 않는다. 사용자가 기존의 안전한 파일 전송 수단으로 m2-stage 또는 로컬 개발 Mac에 복사하고, 수신 측에서 `shasum -a 256 -c dump-sha256.txt`가 세 파일 모두 `OK`일 때만 진행한다.

### 7-2. 보존 대상 ID hash

행 내용이나 개인정보를 출력하지 않고 count와 ID 집합 hash만 저장한다.

```sh
set -eu
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
dump_dir="$HOME/clipper-backups/$cutover_id"

docker exec -i clipper-db-user-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-user-before.txt" <<'SQL'
SELECT 'users|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM users;
SELECT 'user_sessions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM user_sessions;
SELECT 'desktop_auth_codes|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM desktop_auth_codes;
SELECT 'shortform_projects|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM shortform_projects;
SQL

docker exec -i clipper-db-admin-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-admin-before.txt" <<'SQL'
SELECT 'operators|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM operators;
SELECT 'operator_sessions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM operator_sessions;
SELECT 'provider_credentials|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM provider_credentials;
SQL

docker exec -i clipper-db-release-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-release-before.txt" <<'SQL'
SELECT 'release_versions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_versions;
SELECT 'release_builds|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_builds;
SELECT 'release_artifacts|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_artifacts;
SELECT 'release_events|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_events;
SQL
```

### 7-3. 삭제 대상 재확인

Admin DB에서 count만 확인한다.

```sh
docker exec -i clipper-db-admin-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -P pager=off' <<'SQL'
SELECT 'licenses' AS table_name, count(*) FROM licenses
UNION ALL SELECT 'purchase_requests', count(*) FROM purchase_requests
UNION ALL SELECT 'credit_ledger', count(*) FROM credit_ledger
UNION ALL SELECT 'operation_runs', count(*) FROM operation_runs
UNION ALL SELECT 'payment_orders', count(*) FROM payment_orders
UNION ALL SELECT 'payment_events', count(*) FROM payment_events
UNION ALL SELECT 'user_access_grants', count(*) FROM user_access_grants
UNION ALL SELECT 'credit_grants', count(*) FROM credit_grants
UNION ALL SELECT 'credit_ledger_entries', count(*) FROM credit_ledger_entries
UNION ALL SELECT 'user_free_trials', count(*) FROM user_free_trials
UNION ALL SELECT 'subscriptions', count(*) FROM subscriptions;
SELECT status, toss_mode, count(*)
FROM payment_orders
GROUP BY status, toss_mode
ORDER BY status, toss_mode;
SQL
```

다음이면 중단하고 다시 승인받는다.

- `toss_mode`가 `LIVE`인 paid row가 하나라도 있음.
- rehearsal과 달리 `user_access_grants`, `credit_grants`, `credit_ledger_entries`, `user_free_trials`, `subscriptions` 중 하나라도 0이 아니거나, 새 PG로 보존해야 할 실제 구독·결제·grant/ledger 데이터가 발견됨.
- dump 생성, `pg_restore --list`, hash 기록 중 하나라도 실패.
- API 중지 뒤에도 예상하지 못한 DB 쓰기가 계속됨.

Gate D 통과 조건:

- 세 dump가 모두 non-empty이고 `pg_restore --list` 통과.
- SHA256 파일 생성.
- DB host 밖의 두 번째 복사본에서 SHA256 재검증 통과.
- 보존 대상 before hash 세 파일 생성.
- 삭제 대상이 승인 범위와 일치.

## 8. Gate E — 실제 migration

목적: 미리 빌드한 정확한 Web API image로 User → Admin → Release migration을 실행한다.

영향: 실제 개발 DB schema가 바뀌며 Admin migration은 승인된 구 이용권·크레딧·operation 이력을 파괴적으로 제거한다.

m2-stage에서 실행한다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
sh scripts/migrate-db.sh dev
```

표시 대상이 정확히 다음과 같을 때만 `migrate dev`를 입력한다.

| DB | host:port | 이름 |
|---|---|---|
| User | `192.168.0.7:55203` | `clipper_user_dev` |
| Admin | `192.168.0.7:55213` | `clipper_admin_dev` |
| Release | `192.168.0.7:55223` | `clipper_release_dev` |

순서는 도구가 고정한 User → Admin → Release다. 세 DB 전체가 하나의 transaction은 아니므로 중간 실패 시 서비스를 시작하지 않는다. 어디까지 적용됐는지 기록한 뒤 §12의 세 DB 전체 복원으로 되돌린다. `migration:revert`는 삭제된 데이터를 복원하지 못하므로 사용하지 않는다.

## 9. Gate F — migration 직후 DB 검증

m2-db에서 실행한다. API는 계속 중지 상태다.

### 9-1. 최신 migration과 no-op

```sh
for c in clipper-db-user-dev clipper-db-admin-dev clipper-db-release-dev; do
  printf '\n%s\n' "$c"
  docker exec "$c" sh -lc '
    psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "
      SELECT current_database();
      SELECT name FROM migrations ORDER BY timestamp DESC LIMIT 5;
    "
  '
done
```

반드시 확인할 최신 migration:

- User: `AddDesktopLoginBinding1789600000000`
- Admin: `NormalizeAllTierPluginEntitlements1789300000000`
- Release: `AddArtifactDesktopProfile1789600000000`

그 후 m2-stage에서 같은 migration 명령을 한 번 더 실행한다. 오류 없이 끝나야 한다. 첫 실행과 다른 추가 schema/data 변화가 생기면 중단한다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
sh scripts/migrate-db.sh dev
```

대상 세 DB를 다시 확인하고 `migrate dev` 입력.

### 9-2. 보존 hash 재계산과 diff

다음은 §7-2와 같은 조회를 `after` 파일에 저장한다.

```sh
set -eu
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
dump_dir="$HOME/clipper-backups/$cutover_id"

docker exec -i clipper-db-user-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-user-after.txt" <<'SQL'
SELECT 'users|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM users;
SELECT 'user_sessions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM user_sessions;
SELECT 'desktop_auth_codes|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM desktop_auth_codes;
SELECT 'shortform_projects|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM shortform_projects;
SQL

docker exec -i clipper-db-admin-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-admin-after.txt" <<'SQL'
SELECT 'operators|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM operators;
SELECT 'operator_sessions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM operator_sessions;
SELECT 'provider_credentials|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM provider_credentials;
SQL

docker exec -i clipper-db-release-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' \
  > "$dump_dir/preserve-release-after.txt" <<'SQL'
SELECT 'release_versions|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_versions;
SELECT 'release_builds|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_builds;
SELECT 'release_artifacts|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_artifacts;
SELECT 'release_events|'||count(*)||'|'||coalesce(md5(string_agg(id::text,',' ORDER BY id::text)),md5('')) FROM release_events;
SQL

diff -u "$dump_dir/preserve-user-before.txt" "$dump_dir/preserve-user-after.txt"
diff -u "$dump_dir/preserve-admin-before.txt" "$dump_dir/preserve-admin-after.txt"
diff -u "$dump_dir/preserve-release-before.txt" "$dump_dir/preserve-release-after.txt"
```

세 diff 모두 출력 없이 exit 0이어야 한다.

### 9-3. 정리·정책 결과

```sh
docker exec -i clipper-db-admin-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -P pager=off' <<'SQL'
SELECT to_regclass('public.licenses') AS licenses,
       to_regclass('public.purchase_requests') AS purchase_requests,
       to_regclass('public.plans') AS plans,
       to_regclass('public.credit_ledger') AS old_credit_ledger,
       to_regclass('public.token_usage') AS token_usage;
SELECT 'user_access_grants' AS table_name, count(*) FROM user_access_grants
UNION ALL SELECT 'credit_grants', count(*) FROM credit_grants
UNION ALL SELECT 'credit_ledger_entries', count(*) FROM credit_ledger_entries
UNION ALL SELECT 'user_free_trials', count(*) FROM user_free_trials
UNION ALL SELECT 'subscriptions', count(*) FROM subscriptions
UNION ALL SELECT 'payment_orders', count(*) FROM payment_orders
UNION ALL SELECT 'operation_runs', count(*) FROM operation_runs;
SELECT code, entitlement_mode FROM plan_tiers ORDER BY code;
SELECT count(*) AS stored_all_mode_entitlements
FROM plan_plugin_entitlements ppe
JOIN plan_tiers pt ON pt.id = ppe.plan_tier_id
WHERE pt.entitlement_mode = 'all';
SELECT operation_key, credit_cost, billing_strategy
FROM operation_policies
ORDER BY operation_key;
SQL

docker exec clipper-db-user-dev sh -eu -c \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -P pager=off -c "SELECT count(*) AS onboarding_jobs FROM user_onboarding_jobs;"'
```

기대 결과:

- 구형 테이블 다섯 개는 `NULL`.
- 새 grant/free-trial/subscription/payment/operation 데이터는 모두 0.
- `user_onboarding_jobs` 0. 기존 사용자에게 무료체험 소급 없음.
- trial/basic/pro/business 모두 `entitlement_mode=all`.
- all-mode 저장 entitlement row 0.
- operation policy는 정확히 여섯 개: Shortform 3경로, Dance, Dialog, Variation.

하나라도 다르면 서비스를 시작하지 않고 §12로 간다.

## 10. Gate G — 새 서비스 시작과 smoke

### 10-1. m2-stage 서비스 시작

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
sh scripts/deploy-dev.sh all --start-only
```

내부 확인:

```sh
docker ps -a --filter 'label=com.docker.compose.project=clipper-dev' \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

curl --connect-timeout 3 --max-time 10 -fsS http://192.168.0.23:43203/health
curl --connect-timeout 3 --max-time 10 -fsS http://192.168.0.23:43203/catalog

for c in clipper-web-client-dev clipper-web-admin-dev clipper-web-api-dev; do
  docker inspect --format '{{.Name}} | imageID={{.Image}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$c"
done
```

기대 결과:

- User/Admin/Release DB health 모두 `ok`.
- 실행 image revision이 Gate B의 SHA와 일치.
- `/catalog`의 Basic/Pro/Business가 모두 현재 여섯 plugin key를 반환.

외부 HTTPS 확인:

```sh
for domain in dev.clipperstudio.ai dev-admin.clipperstudio.ai dev-api.clipperstudio.ai; do
  curl --connect-timeout 5 --max-time 15 -sS -o /dev/null \
    -w "$domain | HTTP=%{http_code} | TLS=%{ssl_verify_result}\n" \
    "https://$domain/health"
done
```

HTTP 200, TLS 0이어야 한다. `-k`로 인증서 오류를 숨기지 않는다.

### 10-2. 사용자 UI smoke

실제 결제·ML/Build 5로 확대하지 않고 다음만 확인한다.

1. 기존 개발 사용자 Google 로그인 성공.
2. 기존 사용자 계정은 남아 있고 무료체험/access/credit가 소급 생성되지 않음.
3. 신규 테스트 계정은 최초 가입 뒤 무료체험 400 credits / 30일과 계정 정보가 표시됨.
4. Customer Web `/my`, credit ledger, 요금제/credit 상품 표시.
5. Admin 로그인, 사용자·catalog·provider credential 목록 표시. secret 값은 노출하지 않음.
6. 새 개발판 로그인 callback은 `clipperstudio-dev://auth/callback`, 운영 callback은 받지 않음.
7. 새 개발판 account/access/credit 표시와 필수 템플릿 `.cliptpl` import. 기본 16개가 중복되지 않고 사용자 템플릿만 추가됨.
8. 실제 카드 승인 대신 Toss test checkout 진입 전 화면·키셋만 확인. 실제 결제와 webhook 검증은 별도 승인된 테스트로 진행.

smoke 도중 새 사용자 무료체험 지급처럼 의도된 쓰기가 발생하므로, Gate F의 0건 기준은 서비스 시작 전까지만 적용한다.

## 11. 성공 판정과 관찰

성공 조건:

- Gate A~G 전부 통과.
- 보존 hash 세 그룹 전후 일치.
- 구 금융/operation 데이터만 승인 범위대로 제거.
- 기존 사용자 로그인이 유지되고 무료체험 비소급.
- 신규 가입자 무료체험 지급.
- health/catalog/Web/Admin/새 개발판 smoke 통과.
- 실행 image revision과 기록한 source SHA 일치.

성공 뒤 30~60분 동안 다음을 관찰한다.

- API 5xx와 DB 연결 오류.
- onboarding job 반복 실패.
- payment webhook inbox/reconciliation 오류.
- operation이 이유 없이 `running`에 남는지.
- desktop telemetry retry 급증.

로그에는 개인정보·결제 식별정보가 있을 수 있으므로 원문 전체를 채팅에 붙이지 않는다. 오류 코드·시각·영향 범위만 마스킹해 공유한다.

## 12. 실패 시 rollback — 세 DB와 세 image를 한 세트로 복원

rollback은 별도 실행 결정 후 사용자가 수행한다. migration down은 사용하지 않는다.

### 12-1. m2-stage 새 서비스 정지

```sh
docker stop clipper-web-client-dev clipper-web-admin-dev clipper-web-api-dev
```

### 12-2. m2-db 세 DB 복원

이 단계는 현재 DB를 drop하고 전환 직전 dump로 재생성하는 파괴적 복원이다. 세 DB를 모두 같은 cutover dump 세트로 복원한다. 하나만 옛 상태로 돌리지 않는다.

```sh
set -eu
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
dump_dir="$HOME/clipper-backups/$cutover_id"

for kind in user admin release; do
  container="clipper-db-$kind-dev"
  test -s "$dump_dir/$kind.dump"
  docker exec -i "$container" pg_restore --list < "$dump_dir/$kind.dump" > /dev/null
done

for kind in user admin release; do
  container="clipper-db-$kind-dev"
  docker exec "$container" sh -eu -c '
    psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '\''$POSTGRES_DB'\'' AND pid <> pg_backend_pid();"
    dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB"
    createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$POSTGRES_DB"
  '
  docker exec -i "$container" sh -eu -c \
    'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl --exit-on-error --single-transaction' \
    < "$dump_dir/$kind.dump"
done
```

§7-2의 before hash를 다시 계산해 복원 결과와 비교한다. 하나라도 다르면 앱을 시작하지 않는다.

### 12-3. m2-stage 이전 env·secret·image 복원

env/secret을 실제로 수정하지 않았다면 덮어쓰지 않고 hash만 확인한다. 수정했다면 backup에서 되돌린다.

```sh
set -eu
root=/Users/metabuzz/Desktop/project/clipper2
cutover_id=$(cat "$HOME/clipper-backups/current-dev-pg-cutover-id.txt")
backup_dir="$HOME/clipper-backups/$cutover_id"

# stack.dev.env를 이번 준비에서 수정했을 때만 실행
cp -p "$backup_dir/stack.dev.env" "$root/clipper_infra/env/stack.dev.env"

# JWT secret 파일을 이번 준비에서 수정했을 때만 실행
sudo tar -C /opt/clipper/secrets -xpf "$backup_dir/web-api-dev-secrets.tar"

docker tag "clipper-web-client:rollback-$cutover_id" clipper-web-client:dev
docker tag "clipper-web-admin:rollback-$cutover_id" clipper-web-admin:dev
docker tag "clipper-web-api:rollback-$cutover_id" clipper-web-api:dev

cd "$root/clipper_infra"
sh scripts/deploy-dev.sh all --start-only
```

rollback tag가 없으면 tar hash를 확인한 뒤 `docker load -i "$backup_dir/dev-app-images.tar"`로 복원하고 위 tag/start 절차를 실행한다.

마지막으로 이전 `/health`, 로그인, 사용자·프로젝트 수를 확인한다. rollback 완료 후에도 새 PG 전환을 자동 재시도하지 않는다. 실패 원인과 어느 Gate에서 중단됐는지를 먼저 기록하고 새 승인을 받는다.

서비스 복구 후 source checkout도 4-1의 `source-before.txt`에 기록한 각 branch/HEAD로 돌려놓는다. 이때도 repo가 clean인지 확인하고 `git switch`만 사용하며 reset/merge/rebase는 하지 않는다. 기록한 branch가 원격과 달라졌다면 임의로 맞추지 말고 다시 확인한다.

## 13. 즉시 중단 조건

- 지정한 branch/SHA 불일치 또는 dirty source.
- env validator 실패, `API_KEY_ENC_SECRET`/JWT key 예상치 않은 변경.
- 개발이 아닌 DB host/port/name 표시.
- dump 검증 실패 또는 보존 hash 생성 실패.
- `LIVE` 결제나 보존해야 할 실제 새 PG 금융 데이터 발견.
- migration 중간 실패.
- 보존 hash 불일치.
- 기존 사용자에게 무료체험/access/credit가 소급 생성됨.
- `/health`의 DB 하나라도 `ok`가 아님.
- `/catalog`가 모든 유료 tier에 동일 여섯 plugin key를 반환하지 않음.
- 기존 사용자 로그인·프로젝트 또는 provider credential 사용 불가.
- 승인 범위를 벗어난 새 문제 발견.

## 14. 실행 기록 양식

실행 후 아래를 `.codex`에 기록한다.

- 작업자, KST 시작/종료 시각, 실제 중단 시간.
- m2-stage 네 repo branch/upstream/SHA, 기존·신규 image ID/revision.
- dump 경로·bytes·SHA256. 비밀번호나 row 내용은 기록하지 않음.
- migration 전후 최신 migration 이름, 보존 hash diff.
- 승인 범위에서 삭제된 count와 새 정책 seed 결과.
- 내부/외부 health, catalog, 로그인/UI smoke 결과.
- 발생한 오류, 중단 Gate, rollback 여부와 복구 검증.
- commit/push/deploy/DB 변경을 각각 구분.
- 실제 ML/Build 5, Windows 실기, macOS 자동 업데이트 HOLD 상태.

## 15. 현재 다음 행동

1. 이 런북을 사용자와 검토해 명령·중단 범위·복구 방식을 확정한다.
2. 실제 전환 날짜와 60분 점검 창을 정한다.
3. 그때 사용자에게 Gate A부터 한 블록씩 안내한다. 각 Gate 출력 확인 전 다음 블록을 주지 않는다.
4. Gate G와 사용자 확인까지 끝나기 전 운영서버 전환으로 넘어가지 않는다.
