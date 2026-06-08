# Clipper2 Dev 배포 현황과 운영 가이드

마지막 업데이트: 2026-06-08 KST

이 문서는 Clipper2 dev web/admin/API와 dev DB가 현재 어느 서버에 어떤 구조로
배포되어 있는지, 코드 수정 후 어떻게 다시 배포하는지 정리한 Notion 공유용
문서다.

DB 비밀번호, 토큰, secret 값은 이 문서에 적지 않는다.

## 현재 상태

dev 환경 배포는 완료되어 있다.

| 영역 | 상태 |
| --- | --- |
| dev web | 배포 완료 |
| dev admin | 배포 완료 |
| dev API | 배포 완료 |
| dev user/admin/release DB | 배포 완료 |
| API와 DB 연결 | 정상, DB 3개 모두 connected |
| stage/prod app 배포 | 아직 시작 안 함 |
| DB migration/table/seed | 아직 없음 |
| release metadata API | placeholder, `501` |

현재 dev URL:

| URL | 용도 |
| --- | --- |
| `https://dev.clipperstudio.ai` | public web placeholder |
| `https://dev-admin.clipperstudio.ai` | admin placeholder |
| `https://dev-api.clipperstudio.ai/v1/health` | API health |

현재 placeholder 화면:

| URL | 기대 화면 |
| --- | --- |
| `https://dev.clipperstudio.ai` | `C / CLIPPER2 WEB / Coming Soon` |
| `https://dev-admin.clipperstudio.ai` | `A / CLIPPER2 ADMIN / Coming Soon` |

API health는 DB 3개의 실제 연결 상태를 확인한다.

정상 응답 예:

```json
{
  "status": "ok",
  "service": "clipper-web-api",
  "environment": "dev",
  "releaseChannel": "dev",
  "databases": {
    "userConfigured": true,
    "adminConfigured": true,
    "releaseConfigured": true,
    "userConnected": true,
    "adminConnected": true,
    "releaseConnected": true
  }
}
```

## 서버 역할

| 서버 | LAN IP | 역할 |
| --- | --- | --- |
| m2-proxy | `192.168.0.2` | Nginx Proxy Manager, public HTTPS 진입점 |
| m2-stage | `192.168.0.23` | dev app 컨테이너 실행 서버 |
| m2-db | `192.168.0.7` | dev PostgreSQL 컨테이너 실행 서버 |

외부 요청 흐름:

```text
Cloudflare DNS
-> 사무실 WAN / ipTIME
-> m2-proxy Nginx Proxy Manager
-> m2-stage app 컨테이너 포트
-> API가 m2-db PostgreSQL 포트로 연결
```

## m2-stage의 Git repo 배치

dev app 서버는 server-side build 방식으로 운영한다.

경로:

```text
/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

app repo 3개는 `clipper_infra` 안에 넣지 않고 같은 폴더에 sibling으로 둔다.

현재 push된 기준 commit:

| Repo | Branch | 현재 commit |
| --- | --- | --- |
| `clipper_infra` | `feature/infra-initial-setup` | `f0cb1f1 fix: use per-database password envs` |
| `clipper_web_client` | `main` | `7bdaeae chore: move local web port to 4700` |
| `clipper_web_admin` | `main` | `db26f4d chore: move local admin port to 4701` |
| `clipper_web_api` | `main` | `0eab250 fix: require per-database passwords` |

## 배포 방식

현재 dev 환경은 server-side build 방식이다.

즉, GitHub Container Registry/GHCR에 Docker image를 push/pull하지 않는다.
코드가 GitHub에 push되면 m2-stage에서 해당 repo를 pull하고, m2-stage에서
Docker image를 직접 build한 뒤 Docker Compose로 컨테이너를 recreate한다.

코드를 push했다고 자동으로 배포되지는 않는다.

## m2-stage app 컨테이너

Docker Compose 파일:

```text
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.yml
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.dev.yml
```

서버 로컬 env 파일:

```text
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/stack.dev.env
```

이 env 파일에는 실제 DB password가 들어 있으므로 commit하거나 채팅/문서에
붙여넣지 않는다.

DB 접속값은 URL이 아니라 split 변수 형식이다. user/admin/release 각각
`CLIPPER_*_DATABASE_PORT/NAME/USER/PASSWORD`로 나눈다.

현재 dev 컨테이너:

| Compose service | Container name | Image | Host port |
| --- | --- | --- | --- |
| `web-client` | `clipper-web-client-dev` | `clipper-web-client:dev` | `192.168.0.23:42203 -> 80` |
| `web-admin` | `clipper-web-admin-dev` | `clipper-web-admin:dev` | `192.168.0.23:42303 -> 80` |
| `api` | `clipper-web-api-dev` | `clipper-web-api:dev` | `192.168.0.23:43203 -> 43203` |

`web-client`, `web-admin` 이미지는 Angular build output을 만들고, 컨테이너
내부 Nginx로 정적 파일을 서빙한다. 이 Nginx는 정적 파일 서빙용이고,
m2-proxy의 Nginx Proxy Manager와 별개다.

`api` 이미지는 Node/NestJS runtime이다. API 컨테이너에는 Nginx가 없다.

주의: Compose service 이름과 container name은 다르다.

Compose service 이름:

```text
web-client
web-admin
api
```

컨테이너 이름:

```text
clipper-web-client-dev
clipper-web-admin-dev
clipper-web-api-dev
```

예를 들어 아래 명령은 틀린 명령이다.

```sh
docker compose up -d --force-recreate clipper-web-api
```

API만 recreate하려면 service 이름인 `api`를 써야 한다.

```sh
docker compose up -d --force-recreate api
```

## Nginx Proxy Manager

Nginx Proxy Manager는 m2-proxy에서 실행 중이다.

확인된 m2-proxy compose root:

```text
/Users/metabeojeu/Desktop/infra/proxy-server
```

DNS는 Cloudflare에서 관리한다. dev record는 ipTIME DDNS를 통해 사무실 WAN으로
향한다.

```text
dev.clipperstudio.ai
dev-admin.clipperstudio.ai
dev-api.clipperstudio.ai
-> metabuzz.iptime.org
```

ipTIME은 외부 HTTP/HTTPS를 m2-proxy로 포워딩한다.

| External port | Internal target |
| ---: | --- |
| `80` | `192.168.0.2:80` |
| `443` | `192.168.0.2:443` |

NPM proxy host 설정:

| Domain | Upstream |
| --- | --- |
| `dev.clipperstudio.ai` | `http://192.168.0.23:42203` |
| `dev-admin.clipperstudio.ai` | `http://192.168.0.23:42303` |
| `dev-api.clipperstudio.ai` | `http://192.168.0.23:43203` |

dev NPM 옵션:

| 옵션 | 값 |
| --- | --- |
| Force SSL | on |
| HTTP/2 Support | on |
| HSTS | on, 운영자 결정 |
| Websockets Support | on |
| Block Common Exploits | on |
| Cache Assets | off |

명시적인 cutover 승인 전에는 legacy route를 변경하지 않는다.

| Domain | 현재 용도 |
| --- | --- |
| `api.clipperstudio.ai` | legacy Clipper API |
| `demo.clipperstudio.ai` | legacy Clipper demo |

## m2-db dev 데이터베이스

dev DB는 PostgreSQL 컨테이너 3개로 나뉘어 있다.

| DB 역할 | Container | Host/port | Database | User |
| --- | --- | --- | --- | --- |
| user | `clipper-db-user-dev` | `192.168.0.7:55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| admin | `clipper-db-admin-dev` | `192.168.0.7:55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| release | `clipper-db-release-dev` | `192.168.0.7:55223` | `clipper_release_dev` | `clipper_release_dev_user` |

DB compose project:

```text
clipper-db-dev
```

m2-db의 DB compose 파일:

```text
clipper_infra/db/compose.yml
clipper_infra/env/db.dev.env
```

실제 dev DB bind host는 `192.168.0.7`이다. 그래서 m2-stage에서 LAN으로 DB에
접근할 수 있다. example env 파일에는 placeholder/default 값이 있을 수 있으니,
실제 운영 값은 m2-db 서버 로컬의 `db.dev.env`를 기준으로 본다.

DB 컨테이너는 PostgreSQL database/user와 persistent Docker volume을 만든다.
애플리케이션 테이블은 아직 만들지 않는다. 테이블은 추후 migration으로 생성한다.

현재 DB 연결 상태:

| From | Result |
| --- | --- |
| m2-stage -> `192.168.0.7:55203` | reachable |
| m2-stage -> `192.168.0.7:55213` | reachable |
| m2-stage -> `192.168.0.7:55223` | reachable |
| `clipper_web_api /v1/health` -> DB 3개 | connected |
| local Mac mini -> `192.168.0.7:55203` | LAN IP direct access timed out |
| local Mac mini -> `metabuzz.iptime.org:55203` | succeeded after ipTIME forwarding |
| local Mac mini -> `metabuzz.iptime.org:55213` | succeeded after ipTIME forwarding |
| local Mac mini -> `metabuzz.iptime.org:55223` | succeeded after ipTIME forwarding |

local Mac mini에서 `192.168.0.7`로 timeout이 나는 것은 password 문제가 아니라
LAN IP 네트워크 도달성 문제다. 포트포워딩 적용 후에는
`metabuzz.iptime.org`로 접속한다.

초기 원칙은 Clipper DB 포트를 WAN port forwarding으로 열지 않는 것이었지만,
로컬 Mac에서 DBeaver와 로컬 `clipper_web_api`를 dev DB에 붙여야 하므로
임시로 dohit과 같은 ipTIME 포트포워딩 방식을 사용하기로 했다. 이 방식은
나중에 VPN/SSH tunnel 방식으로 교체하는 것이 목표다.

임시 ipTIME 포트포워딩 규칙:

| 규칙 이름 | 프로토콜 | 외부 포트 | 내부 IP | 내부 포트 | 대상 |
| --- | --- | ---: | --- | ---: | --- |
| `clipper_dev_user_db` | TCP | `55203` | `192.168.0.7` | `55203` | user dev DB |
| `clipper_dev_admin_db` | TCP | `55213` | `192.168.0.7` | `55213` | admin dev DB |
| `clipper_dev_release_db` | TCP | `55223` | `192.168.0.7` | `55223` | release dev DB |

적용 후 로컬 Mac mini에서 확인 완료:

```sh
nc -vz metabuzz.iptime.org 55203
nc -vz metabuzz.iptime.org 55213
nc -vz metabuzz.iptime.org 55223
```

결과: 3개 모두 `succeeded`.

포트포워딩 추가 후 외부/로컬 개발 환경에서는 LAN IP가 아니라 DDNS host를
사용한다.

```text
metabuzz.iptime.org:55203 -> 192.168.0.7:55203 -> clipper-db-user-dev
metabuzz.iptime.org:55213 -> 192.168.0.7:55213 -> clipper-db-admin-dev
metabuzz.iptime.org:55223 -> 192.168.0.7:55223 -> clipper-db-release-dev
```

이 방식은 PostgreSQL 포트를 인터넷에서 직접 접근 가능하게 만드는 구조다.
강한 DB password를 사용하고, secret을 문서/채팅에 노출하지 않는다. ipTIME이
source IP 제한을 지원한다면 허용 IP를 개발자 공인 IP로 제한한다.

## DBeaver 접속

권장 방식:

1. Google Remote Desktop으로 m2-stage에 접속한다.
2. m2-stage 안에서 DBeaver를 실행한다.
3. DBeaver에서 `192.168.0.7`의 DB 포트로 접속한다.

DBeaver 접속 값:

| Connection name | Host | Port | Database | User |
| --- | --- | ---: | --- | --- |
| Clipper user dev | `192.168.0.7` | `55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| Clipper admin dev | `192.168.0.7` | `55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| Clipper release dev | `192.168.0.7` | `55223` | `clipper_release_dev` | `clipper_release_dev_user` |

로컬 DBeaver에서 접속하려면 원래는 VPN 또는 SSH tunnel이 더 안전하다. 다만
현재는 dohit과 같은 임시 운영 방식으로 ipTIME 포트포워딩을 사용한다.

아직 application table이 없으므로 DBeaver에서 기본 PostgreSQL schema만
보이는 것은 정상이다.

임시 ipTIME 포트포워딩 적용 후 로컬 DBeaver에서 접속할 때는 host를
`metabuzz.iptime.org`로 둔다.

| Connection name | Host | Port | Database | User |
| --- | --- | ---: | --- | --- |
| Clipper user dev WAN | `metabuzz.iptime.org` | `55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| Clipper admin dev WAN | `metabuzz.iptime.org` | `55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| Clipper release dev WAN | `metabuzz.iptime.org` | `55223` | `clipper_release_dev` | `clipper_release_dev_user` |

사용자 로컬 DBeaver에서 위 3개 연결 모두 성공 확인됐다.

## 로컬 개발

dev 서버는 push된 결과를 m2-stage에서 확인하는 용도다. 실제 개발은 로컬에서
각 repo를 localhost로 실행한다. DB는 로컬에 새로 띄우지 않고 공유 dev DB를
사용한다.

로컬 repo 위치:

```text
/Users/jina/project/adlight/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

로컬 실행 포트:

| App | Local URL | Command |
| --- | --- | --- |
| web | `http://localhost:4700` | `npm run start:local` |
| admin | `http://localhost:4701` | `npm run start:local` |
| API | `http://localhost:43203` | `npm run start:local` |

API는 로컬 개발 전용 env 파일을 사용한다.

```text
/Users/jina/project/adlight/clipper_web_api/env/local.dev.env
```

최초 1회:

```sh
cd /Users/jina/project/adlight/clipper_web_api
cp env/local.dev.env.example env/local.dev.env
```

`env/local.dev.env`에 실제 dev DB password를 DB별로 채운다. 이 파일은
commit하지 않는다. DB host는 `metabuzz.iptime.org`를 사용한다.

```text
DATABASE_HOST=metabuzz.iptime.org
USER_DATABASE_PORT=55203
USER_DATABASE_NAME=clipper_user_dev
USER_DATABASE_USER=clipper_user_dev_user
USER_DATABASE_PASSWORD='<USER_DB_PASSWORD>'
```

admin/release도 같은 형식으로 port/name/user/password가 다르다. password에
shell 특수문자가 있으면 작은따옴표로 감싼다. URL-encode는 하지 않는다.

web 실행:

```sh
cd /Users/jina/project/adlight/clipper_web_client
npm install
npm run start:local
```

admin 실행:

```sh
cd /Users/jina/project/adlight/clipper_web_admin
npm install
npm run start:local
```

API 실행:

```sh
cd /Users/jina/project/adlight/clipper_web_api
npm install
npm run start:local
```

## 코드 수정 후 재배포

기본 흐름:

1. 개발자가 로컬에서 코드를 수정한다.
2. commit/push 한다.
3. m2-stage에서 `clipper_infra`와 해당 repo를 pull 한다.
4. m2-stage에서 Docker image를 build 한다.
5. Docker Compose service를 recreate 한다.
6. URL/health를 확인한다.

평소에는 아래 helper script를 사용한다. 이 스크립트가 `clipper_infra`를
먼저 pull하고, infra가 업데이트되면 새 스크립트로 다시 실행한 뒤, 선택한 app
repo pull, Docker build, Compose config 확인, service recreate를 모두
실행한다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh web
./scripts/deploy-dev.sh admin
./scripts/deploy-dev.sh api
./scripts/deploy-dev.sh all
```

아래 긴 명령어들은 helper script가 내부에서 하는 일을 이해하거나, 문제가
생겼을 때 수동으로 확인할 때 사용한다.

### Web client 재배포

m2-stage에서 실행:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_client
git pull --ff-only
docker build -t clipper-web-client:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-client
```

확인:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps web-client
curl -I https://dev.clipperstudio.ai
```

### Admin 재배포

m2-stage에서 실행:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_admin
git pull --ff-only
docker build -t clipper-web-admin:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-admin
```

확인:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps web-admin
curl -I https://dev-admin.clipperstudio.ai
```

### API 재배포

m2-stage에서 실행:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_api
git pull --ff-only
docker build -t clipper-web-api:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate api
```

확인:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps api
curl -s https://dev-api.clipperstudio.ai/v1/health
```

DB 연결 확인이 포함된 API health 기대값:

```text
status: ok
userConnected: true
adminConnected: true
releaseConnected: true
checks.user/admin/release.status: ok
```

### 전체 app service 재배포

m2-stage에서 실행:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_client
git pull --ff-only
docker build -t clipper-web-client:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_admin
git pull --ff-only
docker build -t clipper-web-admin:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_api
git pull --ff-only
docker build -t clipper-web-api:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml config --quiet
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate
```

확인:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps
curl -I https://dev.clipperstudio.ai
curl -I https://dev-admin.clipperstudio.ai
curl -s https://dev-api.clipperstudio.ai/v1/health
```

## 자주 쓰는 명령어

dev helper script:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh web
./scripts/deploy-dev.sh admin
./scripts/deploy-dev.sh api
./scripts/deploy-dev.sh all
```

`--env-file ../env/stack.dev.env`는 helper script가 내부에서 넣어준다.

Compose service 이름 확인:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml config --services
```

기대값:

```text
web-client
api
web-admin
```

app 컨테이너 확인:

```sh
docker ps --filter name=clipper-web-client-dev
docker ps --filter name=clipper-web-admin-dev
docker ps --filter name=clipper-web-api-dev
```

m2-stage에서 DB 접근 확인:

```sh
nc -vz 192.168.0.7 55203
nc -vz 192.168.0.7 55213
nc -vz 192.168.0.7 55223
```

m2-db에서 DB 컨테이너 확인:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/db
docker compose --env-file ../env/db.dev.env -f compose.yml ps
```

## 현재 한계

- 아직 DB migration이 없다.
- 아직 application table이나 seed data가 없다.
- `GET /v1/releases/latest`는 아직 `501 release_metadata_not_implemented`를
  반환한다.
- 실제 client-facing download/login/signup 페이지는 별도로 개발 중이다.
- admin 운영 기능은 아직 구현되지 않았다.
- S3 installer artifact와 update feed 연동은 아직 완료되지 않았다.
- stage/prod app 배포는 아직 시작하지 않았다.

## 운영 규칙

- DB password, token, secret 값을 채팅이나 문서에 붙여넣지 않는다.
- `stack.dev.env`, `db.dev.env`를 commit하지 않는다.
- Clipper dev DB 포트 `55203/55213/55223`만 임시로 ipTIME 포트포워딩을
  사용한다. 이 방식은 추후 VPN/SSH tunnel로 교체한다.
- Clipper stage/prod DB 포트는 WAN에 공개하지 않는다.
- Clipper 배포 중 dohit 컨테이너, 파일, 포트를 건드리지 않는다.
- 명시적인 cutover 승인 없이 legacy `api.clipperstudio.ai`,
  `demo.clipperstudio.ai`를 변경하지 않는다.
