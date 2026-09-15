# 운영 도메인 심사용 전환 — 실행 명령 부록

[상태·결과·복원 런북](2026-09-15-pg-review-production-cutover-and-rollback.md)의 부록. 2026-09-15 사용자가 실행한 명령을 단계별로 보존한다. 채팅의 escape/코드펜스/들여쓰기는 정상 shell/Python 문법으로 정규화했다. 의미를 바꾸지 않는 변수명·출력 축약이 있으며 원시 터미널 전체 로그는 아니다. **과거 실행 기록이므로 전체를 다시 실행하지 않는다.** 재시도 시 기존파일 검사에서 중단되는 단계가 있다. 모든 서버 조작은 사용자가 실행했다.

공통: shell 블록은 필요할 때 `(...)` + `set -eu`로 감싸 실행했다. 비밀파일 생성에는 `umask 077`을 사용했다. 당시 zsh 주석 문제는 `setopt interactivecomments`로 해결했다. 코드펜스 자체는 복사하지 않는다.

## 1. 개발/운영 실행 버전 조사

m2-stage와 m4-prod 각각:
```sh
docker ps --filter name=clipper --format '{{.Names}}' |
while IFS= read -r c; do
  docker inspect --format '{{.Name}} | image={{.Config.Image}} | imageID={{.Image}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$c"
done
```

m2-stage, clipper_infra 폴더:
```sh
for c in clipper-web-client-dev clipper-web-admin-dev clipper-web-api-dev; do
  image_id=$(docker inspect --format '{{.Image}}' "$c")
  docker image inspect --format 'tags={{json .RepoTags}} | created={{.Created}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_id"
done
for repo in clipper_web_client clipper_web_admin clipper_web_api clipper_infra; do
  (
    cd "../$repo" || exit
    echo "=== $repo ==="
    git status --short --branch
    git log -1 --format='%H | %cI | %s'
  )
done
```

개발 API의 비밀값을 제외한 설정 조회:
```sh
docker exec clipper-web-api-dev node -e '
const keys = ["CLIPPER_ENV", "TOSS_PAYMENTS_REVIEW_MODE", "WEB_BASE_URL",
"TOSS_PAYMENTS_RETURN_BASE_URL", "CORS_ORIGIN", "CLIPPER_USER_DATABASE_NAME",
"CLIPPER_ADMIN_DATABASE_NAME", "CLIPPER_RELEASE_DATABASE_NAME"];
for (const key of keys) console.log(key + "=" + (process.env[key] ?? "(미설정)"));
'
```

## 2. m4-prod — 기존 운영 이미지 태그/환경파일 보존

```sh
(
  set -eu
  umask 077
  backup_tag="before-pg-review-$(date +%Y%m%d-%H%M%S)"
  backup_dir="$HOME/clipper-backups/$backup_tag"
  infra_dir="/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra"
  mkdir -p "$backup_dir"
  cp "$infra_dir/env/stack.prod.env" "$backup_dir/stack.prod.env"
  for service in client admin api; do
    container="clipper-web-$service-prod"
    image_id=$(docker inspect --format '{{.Image}}' "$container")
    saved_image="clipper-web-$service:$backup_tag"
    docker image tag "$image_id" "$saved_image"
    printf '%s | %s\n' "$saved_image" "$image_id" >> "$backup_dir/images.txt"
  done
  cat "$backup_dir/images.txt"
  printf '\n보존 위치: %s\n' "$backup_dir"
)
```
결과의 timestamp는20260915-161706. DBdump/image tar는 이 명령에 없다.

## 3. m4-prod — 별도 소스 clone·SHA 고정

당시 앞 단계의 안전한 비밀파일 권한 정책이 소스 clone에도 영향을 준 정황이 있어, 이후 로고 권한을 수정했다. 재구축 시 공개assets와 비밀파일 권한을 구분할 것.

```sh
(
  set -eu
  source_root="/Users/m4-prod/Documents/projects/clipperstudio"
  review_root="/Users/m4-prod/Documents/projects/clipper-pg-review-20260915"
  if [ -e "$review_root" ]; then
    printf '이미 존재하는 폴더입니다: %s\n' "$review_root"
    exit 1
  fi
  mkdir -p "$review_root"
  prepare_repo() {
    repo="$1"
    revision="$2"
    remote_url=$(git -C "$source_root/$repo" remote get-url origin)
    git clone --no-checkout "$remote_url" "$review_root/$repo"
    git -C "$review_root/$repo" checkout --detach "$revision"
    actual=$(git -C "$review_root/$repo" rev-parse HEAD)
    [ "$actual" = "$revision" ]
    printf '준비 완료: %s | %s\n' "$repo" "$actual"
  }
  prepare_repo clipper_web_client 4b361efc742db797e85848c5aea90eb1736194c5
  prepare_repo clipper_web_admin beda584fde924a9a97aa69f1856cbddafe69c94c
  prepare_repo clipper_web_api fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6
)
```

## 4. m4-prod — 프런트엔드 주소 변경·3개 빌드

```sh
(
  set -eu
  review_root="/Users/m4-prod/Documents/projects/clipper-pg-review-20260915"
  python3 - "$review_root" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
old, new = "https://dev-api.clipperstudio.ai", "https://api.clipperstudio.ai"
files = [root / repo / "src/environments/environment.production.ts"
         for repo in ["clipper_web_client", "clipper_web_admin"]]
for path in files:
    if path.read_text().count(old) != 1:
        raise SystemExit(f"예상과 다른 설정: {path}")
for path in files:
    path.write_text(path.read_text().replace(old, new))
    print(f"API 주소 변경: {path}")
PY
  for service in client admin api; do
    repo="$review_root/clipper_web_$service"
    revision=$(git -C "$repo" rev-parse HEAD)
    docker build --label "org.opencontainers.image.revision=$revision" \
      --label "ai.clipper.deployment.variant=pg-review-production-domain" \
      -t "clipper-web-$service:pg-review-20260915" "$repo"
  done
  for service in client admin api; do
    docker image inspect --format '{{json .RepoTags}} | {{.Id}}' "clipper-web-$service:pg-review-20260915"
  done
)
```

## 5. m2-db — 개발DB dump·전송검사

```sh
(
  set -eu
  umask 077
  dump_dir="$HOME/clipper-backups/pg-review-dev-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$dump_dir"
  for kind in user admin release; do
    container="clipper-db-$kind-dev"
    expected_db="clipper_${kind}_dev"
    actual_db=$(docker exec "$container" printenv POSTGRES_DB)
    if [ "$actual_db" != "$expected_db" ]; then
      printf 'DB 이름 불일치: %s\n' "$container"
      exit 1
    fi
    docker exec "$container" sh -eu -c \
      'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl' \
      > "$dump_dir/$kind.dump.part"
    docker exec -i "$container" pg_restore --list < "$dump_dir/$kind.dump.part" > /dev/null
    mv "$dump_dir/$kind.dump.part" "$dump_dir/$kind.dump"
    printf '백업 파일 생성 완료: %s\n' "$kind"
  done
  du -h "$dump_dir/"*.dump
  printf '백업 위치: %s\n' "$dump_dir"
)
shasum -a 256 /Users/metabuzz/clipper-backups/pg-review-dev-20260915-162252/*.dump
```
파일 전송은 사용자가 수행. 실제 수단은 미기록. 전송 후 m4-prod:
```sh
cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/db-backup
ls -la
chmod 700 /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/db-backup
chmod 600 /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/db-backup/*.dump
shasum -a 256 /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/db-backup/*.dump
```

## 6. m4-prod — DB3개 생성·복원

첫 시도 `zsh: command not found: #`. `setopt interactivecomments` 후 아래 전체 재실행 성공.

```sh
(
  set -eu
  umask 077
  review_root="/Users/m4-prod/Documents/projects/clipper-pg-review-20260915"
  cd "$review_root"
  test ! -e db.compose.json
  for kind in user admin release; do
    test -s "db-backup/$kind.dump"
    if docker volume inspect "clipper-pg-review-$kind-data" >/dev/null 2>&1; then
      printf '기존 심사용 볼륨 발견: %s\n' "$kind"; exit 1
    fi
    if docker container inspect "clipper-pg-review-db-$kind" >/dev/null 2>&1; then
      printf '기존 심사용 컨테이너 발견: %s\n' "$kind"; exit 1
    fi
  done
  python3 <<'PY'
import json, secrets
from pathlib import Path
config = {"services": {}, "volumes": {},
          "networks": {"default": {"name": "clipper-pg-review"}}}
for kind in ["user", "admin", "release"]:
    volume = f"{kind}-data"
    config["volumes"][volume] = {"name": f"clipper-pg-review-{kind}-data"}
    config["services"][f"db-{kind}"] = {
        "image": "postgres:16-alpine",
        "container_name": f"clipper-pg-review-db-{kind}",
        "restart": "unless-stopped",
        "environment": {"POSTGRES_DB": f"clipper_{kind}_review",
                        "POSTGRES_USER": "clipper_review",
                        "POSTGRES_PASSWORD": secrets.token_hex(32)},
        "volumes": [f"{volume}:/var/lib/postgresql/data"],
        "healthcheck": {
            "test": ["CMD-SHELL", 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'],
            "interval": "5s", "timeout": "3s", "retries": 20}}
path = Path("db.compose.json")
with path.open("x") as file:
    json.dump(config, file, indent=2)
path.chmod(0o600)
print("심사용 DB 설정 생성 완료")
PY
  docker compose -p clipper-pg-review-db -f db.compose.json up -d --wait --wait-timeout 120
  for kind in user admin release; do
    container="clipper-pg-review-db-$kind"
    docker exec -i "$container" sh -eu -c \
      'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl --exit-on-error --single-transaction' \
      < "db-backup/$kind.dump"
    printf '\n복원 완료: %s\n' "$kind"
    docker exec "$container" sh -eu -c \
      'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT current_database(), count(*) AS public_tables FROM information_schema.tables WHERE table_schema = '\''public'\'';"'
  done
)
```

## 7. m2-stage — 테스트키/암호화 키만 비공개 추출

```sh
(
  set -eu
  umask 077
  export_dir="$HOME/clipper-backups/pg-review-keys-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$export_dir"
  docker exec clipper-web-api-dev node -e '
const prefixes = {
 TOSS_PAYMENTS_WIDGET_CLIENT_KEY: "test_gck_",
 TOSS_PAYMENTS_WIDGET_SECRET_KEY: "test_gsk_",
 TOSS_PAYMENTS_BILLING_CLIENT_KEY: "test_ck_",
 TOSS_PAYMENTS_BILLING_SECRET_KEY: "test_sk_"
};
const result = {};
for (const [key, prefix] of Object.entries(prefixes)) {
 const value = process.env[key]?.trim();
 if (!value?.startsWith(prefix)) {
  console.error(key + ": 테스트키 확인 실패"); process.exit(1);
 }
 result[key] = value;
}
const encryptionKey = process.env.API_KEY_ENC_SECRET;
if (!encryptionKey?.trim()) { console.error("DB 암호화 키 누락"); process.exit(1); }
result.API_KEY_ENC_SECRET = encryptionKey;
process.stdout.write(JSON.stringify(result, null, 2));
' > "$export_dir/review-secrets.json.part"
  mv "$export_dir/review-secrets.json.part" "$export_dir/review-secrets.json"
  shasum -a 256 "$export_dir/review-secrets.json"
  printf '전송할 파일: %s/review-secrets.json\n' "$export_dir"
)
```
사용자 전송 후 m4-prod:
```sh
chmod 600 /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/review-secrets.json
shasum -a 256 /Users/m4-prod/Documents/projects/clipper-pg-review-20260915/review-secrets.json
```

## 8. m4-prod — API 설정 생성·임시 포트 실행

```sh
(
  set -eu
  umask 077
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  python3 <<'PY'
import hashlib, json, secrets, subprocess
from pathlib import Path
output = Path("api.compose.json")
if output.exists():
    raise SystemExit("api.compose.json이 이미 있습니다.")
secret_file = Path("review-secrets.json")
expected = "8cbb91a9d4fc0ce43ed78c3b314bddf68126ffe65d7361148e134c9e18464ea9"
if hashlib.sha256(secret_file.read_bytes()).hexdigest() != expected:
    raise SystemExit("키 파일 해시 불일치")
env = json.loads(secret_file.read_text())
db_config = json.loads(Path("db.compose.json").read_text())
private_key = subprocess.run(
    ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048"],
    capture_output=True, text=True, check=True).stdout
public_key = subprocess.run(["openssl", "pkey", "-pubout"], input=private_key,
                            capture_output=True, text=True, check=True).stdout
env.update({
    "NODE_ENV": "production", "PORT": "3000", "CLIPPER_ENV": "dev",
    "TOSS_PAYMENTS_REVIEW_MODE": "true", "WEB_BASE_URL": "https://clipperstudio.ai",
    "TOSS_PAYMENTS_RETURN_BASE_URL": "https://api.clipperstudio.ai",
    "CORS_ORIGIN": "https://clipperstudio.ai,https://admin.clipperstudio.ai",
    "USER_JWT_PRIVATE_KEY": private_key, "USER_JWT_PUBLIC_KEY": public_key,
    "USER_JWT_EXPIRES_IN": "30m", "OPERATOR_JWT_SECRET": secrets.token_hex(32),
    "OPERATOR_JWT_EXPIRES_IN": "30m"})
for kind in ["user", "admin", "release"]:
    db = db_config["services"][f"db-{kind}"]["environment"]
    if db["POSTGRES_DB"] != f"clipper_{kind}_review":
        raise SystemExit(f"DB 이름 불일치: {kind}")
    prefix = f"CLIPPER_{kind.upper()}_DATABASE_"
    env.update({prefix + "HOST": f"clipper-pg-review-db-{kind}", prefix + "PORT": "5432",
                prefix + "NAME": db["POSTGRES_DB"], prefix + "USER": db["POSTGRES_USER"],
                prefix + "PASSWORD": db["POSTGRES_PASSWORD"]})
env = {key: value.replace("$", "$$") for key, value in env.items()}
health_script = """
fetch('http://127.0.0.1:3000/health').then(async r => {
 const b = await r.json();
 const ok = r.ok && b.status === 'ok' && b.db &&
   ['user','admin','release'].every(k => b.db[k] === 'ok');
 process.exit(ok ? 0 : 1);
}).catch(() => process.exit(1));
"""
config = {
 "services": {"api": {
  "image": "clipper-web-api:pg-review-20260915", "container_name": "clipper-pg-review-api",
  "restart": "unless-stopped", "environment": env, "ports": ["127.0.0.1:43212:3000"],
  "networks": ["review"], "healthcheck": {"test": ["CMD", "node", "-e", health_script],
   "interval": "5s", "timeout": "4s", "retries": 15, "start_period": "15s"}}},
 "networks": {"review": {"external": True, "name": "clipper-pg-review"}}}
with output.open("x") as file:
    json.dump(config, file, indent=2)
output.chmod(0o600)
print("심사용 API 설정 생성 완료")
PY
  docker compose -p clipper-pg-review-app -f api.compose.json up -d --pull never --wait --wait-timeout 120
  curl --fail --silent --show-error --max-time 10 http://127.0.0.1:43212/health
  printf '\n'
  curl --fail --silent --show-error --max-time 10 http://127.0.0.1:43212/payments/review/config
  printf '\n'
)
```

## 9. m4-prod — 공개 포트로 교체

```sh
(
  set -eu
  umask 077
  cd /Users/m4-prod/Documents/projects/clipper-pg-review-20260915
  python3 <<'PY'
import json, subprocess
from pathlib import Path
output = Path("live.compose.json")
if output.exists():
    raise SystemExit("live.compose.json이 이미 있습니다.")
config = json.loads(Path("api.compose.json").read_text())
expected_images = {
 "client": "sha256:4270bdf3ecbf3691525769e27f0a6b3c20aa2e4eff11673ad5f6e542969605b7",
 "admin": "sha256:adc94fac13d57703d631c1fb44aca6a3316acbfb09b8d28762e2bd74e07376a5",
 "api": "sha256:e045583c57aedb73ec1557ab95ea6eaa95b71592be5fc49837fe22dd641fb22c"}
expected_ports = {"client": "42202", "admin": "42302", "api": "43202"}
for kind in ["client", "admin", "api"]:
    name = f"clipper-web-{kind}-prod"
    info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
    if not info["State"]["Running"] or info["Image"] != expected_images[kind]:
        raise SystemExit(f"기존 운영 상태/이미지 불일치: {name}")
    ports = []
    for container_port, entries in (info["HostConfig"].get("PortBindings") or {}).items():
        if not container_port.endswith("/tcp"):
            raise SystemExit(f"예상하지 않은 포트: {name}")
        for entry in entries or []:
            if entry["HostPort"] != expected_ports[kind]:
                raise SystemExit(f"예상하지 않은 호스트 포트: {name}")
            ports.append({"target": 3000 if kind == "api" else 80,
                          "published": entry["HostPort"],
                          "host_ip": entry.get("HostIp") or "0.0.0.0", "protocol": "tcp"})
    if not ports:
        raise SystemExit(f"포트 없음: {name}")
    if kind == "api":
        config["services"]["api"]["ports"] = ports
    else:
        config["services"][kind] = {
            "image": f"clipper-web-{kind}:pg-review-20260915",
            "container_name": f"clipper-pg-review-{kind}", "restart": "unless-stopped",
            "ports": ports, "networks": ["review"],
            "healthcheck": {"test": ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1/"],
                            "interval": "5s", "timeout": "4s", "retries": 12}}
with output.open("x") as file:
    json.dump(config, file, indent=2)
output.chmod(0o600)
print("기존 운영 포트를 유지하는 심사용 교체 설정 생성 완료")
PY
  docker compose -p clipper-pg-review-app -f live.compose.json config --quiet
  restore_original() {
    printf '심사용 시작 실패. 기존 운영 복구\n'
    docker compose -p clipper-pg-review-app -f live.compose.json stop || true
    docker start clipper-web-api-prod clipper-web-client-prod clipper-web-admin-prod
  }
  if ! docker stop clipper-web-client-prod clipper-web-admin-prod clipper-web-api-prod; then
    restore_original; exit 1
  fi
  if ! docker compose -p clipper-pg-review-app -f live.compose.json up -d --pull never --wait --wait-timeout 120; then
    restore_original; exit 1
  fi
  docker compose -p clipper-pg-review-app -f live.compose.json ps
)
```
실제 새3개 healthy. 자동fallback은 발동하지 않았다.

## 10. 외부 주소·수동 결제 검증

m4-prod:
```sh
(
  set -eu
  for url in https://clipperstudio.ai https://admin.clipperstudio.ai; do
    curl --fail --silent --show-error --max-time 20 -o /dev/null \
      -w 'HTTP=%{http_code} | %{url_effective}\n' "$url"
  done
  curl --fail --silent --show-error --max-time 20 https://api.clipperstudio.ai/health
  printf '\n'
  curl --fail --silent --show-error --max-time 20 https://api.clipperstudio.ai/payments/review/config
  printf '\n'
)
```
사용자 시크릿창 확인 안내: 비로그인 가격화면, 단건결제 주문서, 정기 동의/카드등록, dev주소로 돌아가지 않음. 사용자는 단건/정기 **결제 성공**과 주소유지를 보고했다. 카드정보/거래ID는 기록하지 않았다.

## 11. 로고 오류 조사

m4-prod, 원본 해시와 응답 비교:
```sh
(
  set -eu
  docker exec clipper-pg-review-client sha256sum /usr/share/nginx/html/assets/brand/logo_clipper_w.png
  downloaded_logo=$(mktemp /tmp/clipper-logo-check.XXXXXX)
  trap 'rm -f "$downloaded_logo"' EXIT
  curl --silent --show-error --max-time 20 -o "$downloaded_logo" \
    -w 'HTTP=%{http_code} | Content-Type=%{content_type}\n' \
    https://clipperstudio.ai/assets/brand/logo_clipper_w.png
  file "$downloaded_logo"
  shasum -a 256 "$downloaded_logo"
)
```
container SHA정상, 외부403/text/html. 받은HTML SHA=`925f98379b7b21206f72236ee5e1ad6668bffbcdaa0e41c72c802c1a549e7c01`.

추가 비교:
```sh
curl --silent --show-error --max-time 10 -D - -o /dev/null \
  -H 'Host: clipperstudio.ai' http://192.168.0.47:42202/assets/brand/logo_clipper_w.png
curl --silent --show-error --max-time 20 -D - -o /dev/null \
  https://clipperstudio.ai/assets/brand/logo_clipper_w.png
docker exec clipper-pg-review-client ls -ld \
  /usr/share/nginx/html /usr/share/nginx/html/assets \
  /usr/share/nginx/html/assets/brand /usr/share/nginx/html/assets/brand/logo_clipper_w.png
```
양쪽403, 디렉터리755/파일600 확인. 임시복구:
```sh
docker exec --user root clipper-pg-review-client chmod 644 /usr/share/nginx/html/assets/brand/logo_clipper_w.png
curl --silent --show-error --max-time 20 -o /dev/null \
  -w 'HTTP=%{http_code} | Content-Type=%{content_type}\n' \
  https://clipperstudio.ai/assets/brand/logo_clipper_w.png
```
HTTP200/image/png 확인. 단일소스 chmod644도 안내했으나 별도 실행출력은 없고, 다음 전체public 권한 수정 명령 실행으로 포함됐다.

## 12. 로고 권한을 이미지에 반영

```sh
(
  set -eu
  review_root="/Users/m4-prod/Documents/projects/clipper-pg-review-20260915"
  client_repo="$review_root/clipper_web_client"
  find "$client_repo/public" -type d -exec chmod 755 {} +
  find "$client_repo/public" -type f -exec chmod 644 {} +
  docker build --no-cache \
    --label "org.opencontainers.image.revision=$(git -C "$client_repo" rev-parse HEAD)" \
    --label "ai.clipper.deployment.variant=pg-review-production-domain" \
    -t clipper-web-client:pg-review-20260915 "$client_repo"
  docker run --rm --entrypoint sh clipper-web-client:pg-review-20260915 \
    -c 'test "$(stat -c %a /usr/share/nginx/html/assets/brand/logo_clipper_w.png)" = 644'
  cd "$review_root"
  docker compose -p clipper-pg-review-app -f live.compose.json \
    up -d --no-deps --force-recreate --pull never --wait --wait-timeout 120 client
  curl --fail --silent --show-error --max-time 20 -o /dev/null \
    -w 'HTTP=%{http_code} | Content-Type=%{content_type}\n' \
    https://clipperstudio.ai/assets/brand/logo_clipper_w.png
)
```
새Client healthy, HTTP200/image/png 확인. 최종image ID 출력은 이 명령에 없어 미확보.

## 13. 향후 선택적으로 남길 증거 (미실행)

최종Client ID를 보완할 때 m4-prod에서 다음 출력만 기록하면 된다. 비밀환경 전체 inspect 출력은 보내지 않는다.
```sh
for c in clipper-pg-review-client clipper-pg-review-admin clipper-pg-review-api; do
  docker inspect --format '{{.Name}} | image={{.Image}} | revision={{index .Config.Labels "org.opencontainers.image.revision"}}' "$c"
done
```

복원은 이 부록을 역순 실행하는 방식이 아니다. **본문 §13(기존 운영) 또는 §14(integration 신규 배포)** 절차를 따른다.
