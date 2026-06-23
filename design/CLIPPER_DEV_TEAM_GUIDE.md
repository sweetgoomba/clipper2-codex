# Clipper Dev 협업 가이드

마지막 업데이트: 2026-06-08 KST

팀원이 dev 환경에서 개발/확인/재배포할 때 필요한 최소 정보만 정리한다.
비밀번호, 토큰, secret 값은 이 문서에 적지 않는다.

## 현재 Dev URL

| URL | 용도 |
| --- | --- |
| `https://dev.clipperstudio.ai` | 사용자용 web placeholder |
| `https://dev-admin.clipperstudio.ai` | admin placeholder |
| `https://dev-api.clipperstudio.ai/v1/health` | API health |

현재 web/admin은 실제 화면 개발 전 placeholder다.

API health가 정상이라면 DB 3개가 모두 connected로 나온다.

```text
userConnected: true
adminConnected: true
releaseConnected: true
```

## Repo 위치

m2-stage 서버:

```text
/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

현재 dev는 m2-stage에서 직접 Docker image를 build하는 방식이다.
GitHub에 push했다고 자동 배포되지는 않는다.

로컬 개발 repo 위치:

```text
/Users/jina/project/adlight/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

## 로컬 개발

로컬 개발은 배포된 dev 서버와 별개로, 각 repo를 localhost로 띄우는 방식이다.
DB는 로컬에 새로 띄우지 않고 공유 dev DB를 사용한다.

| App | Local URL | Command |
| --- | --- | --- |
| web | `http://localhost:4700` | `npm run start:local` |
| admin | `http://localhost:4701` | `npm run start:local` |
| API | `http://localhost:43203` | `npm run start:local` |

API는 로컬 개발 전용 env 파일을 사용한다.

최초 1회:

```sh
cd /Users/jina/project/adlight/web/clipper_web_api
cp env/local.dev.env.example env/local.dev.env
```

`env/local.dev.env`에 실제 dev DB password를 DB별로 채운다. 이 파일은
commit하지 않는다.

web 실행:

```sh
cd /Users/jina/project/adlight/web/clipper_web_client
npm install
npm run start:local
```

admin 실행:

```sh
cd /Users/jina/project/adlight/web/clipper_web_admin
npm install
npm run start:local
```

API 실행:

```sh
cd /Users/jina/project/adlight/web/clipper_web_api
npm install
npm run start:local
```

## App 컨테이너

| Compose service | Container name | Host port |
| --- | --- | --- |
| `web-client` | `clipper-web-client-dev` | `192.168.0.23:42203 -> 80` |
| `web-admin` | `clipper-web-admin-dev` | `192.168.0.23:42303 -> 80` |
| `api` | `clipper-web-api-dev` | `192.168.0.23:43203 -> 43203` |

주의: 재배포할 때는 container name이 아니라 Compose service 이름을 쓴다.

예:

```sh
docker compose up -d --force-recreate api
```

## 코드 수정 후 재배포

공통 흐름:

1. 로컬에서 코드 수정
2. commit/push
3. m2-stage에서 `clipper_infra`와 해당 repo pull
4. m2-stage에서 Docker build
5. Compose service recreate
6. URL/health 확인

일반적으로는 아래 한 줄 명령만 사용하면 된다. 이 스크립트가 내부에서
`clipper_infra`를 먼저 pull하고, infra가 업데이트되면 새 스크립트로 다시
실행한 뒤, 선택한 app repo pull, Docker build, Compose config 확인,
컨테이너 recreate를 모두 실행한다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh web
./scripts/deploy-dev.sh admin
./scripts/deploy-dev.sh api
./scripts/deploy-dev.sh all
```

아래 긴 명령어들은 스크립트가 내부에서 하는 일을 이해하거나, 문제가 생겼을
때 수동으로 확인할 때만 사용한다.

### Web 재배포

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_client
git pull --ff-only
docker build -t clipper-web-client:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-client
curl -I https://dev.clipperstudio.ai
```

### Admin 재배포

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_admin
git pull --ff-only
docker build -t clipper-web-admin:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-admin
curl -I https://dev-admin.clipperstudio.ai
```

### API 재배포

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_api
git pull --ff-only
docker build -t clipper-web-api:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate api
curl -s https://dev-api.clipperstudio.ai/v1/health
```

### 전체 재배포

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

## 왜 `--env-file`을 직접 입력하지 않아도 되는가

Docker Compose는 기본적으로 compose 파일 옆 또는 project 기준의 `.env`만
자동으로 읽는다. 그런데 dev 실제 env 파일은 secret을 분리하기 위해
`clipper_infra/env/stack.dev.env`에 둔다.

이 파일의 DB 접속값도 URL이 아니라 split 변수다. user/admin/release 각각
`CLIPPER_*_DATABASE_PORT/NAME/USER/PASSWORD`로 나눈다.

그래서 수동 compose 명령에서는 원래 아래 옵션이 필요하다.

```sh
--env-file ../env/stack.dev.env
```

하지만 `./scripts/deploy-dev.sh`가 이 옵션을 내부에서 넣어주므로 팀원은 직접
입력하지 않아도 된다. 이 스크립트는 실행 초기에 `clipper_infra`도 pull한다.

## DB 접속

dev DB는 3개로 분리되어 있다.

| 역할 | Host | Port | Database | User |
| --- | --- | ---: | --- | --- |
| user | `metabuzz.iptime.org` | `55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| admin | `metabuzz.iptime.org` | `55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| release | `metabuzz.iptime.org` | `55223` | `clipper_release_dev` | `clipper_release_dev_user` |

DBeaver에서도 위 값으로 연결한다.
password는 팀 내부에서 별도 공유받는다. 채팅이나 문서에 붙여넣지 않는다.

현재 application table은 아직 없으므로 기본 PostgreSQL schema만 보여도 정상이다.

연결 확인:

```sh
nc -vz metabuzz.iptime.org 55203
nc -vz metabuzz.iptime.org 55213
nc -vz metabuzz.iptime.org 55223
```

## 로컬 API env

로컬 API는 아래 파일을 읽는다.

```text
/Users/jina/project/adlight/web/clipper_web_api/env/local.dev.env
```

예시 파일은 `env/local.dev.env.example`이다.

형식은 URL이 아니라 split 변수다.

```text
DATABASE_HOST=metabuzz.iptime.org
USER_DATABASE_PORT=55203
USER_DATABASE_NAME=clipper_user_dev
USER_DATABASE_USER=clipper_user_dev_user
USER_DATABASE_PASSWORD='<USER_DB_PASSWORD>'
```

admin/release도 같은 형식으로 port/name/user/password가 다르다. password에
shell 특수문자가 있으면 작은따옴표로 감싼다. URL-encode는 하지 않는다.

## Proxy

Nginx Proxy Manager는 m2-proxy에서 실행 중이다.

| Domain | Upstream |
| --- | --- |
| `dev.clipperstudio.ai` | `http://192.168.0.23:42203` |
| `dev-admin.clipperstudio.ai` | `http://192.168.0.23:42303` |
| `dev-api.clipperstudio.ai` | `http://192.168.0.23:43203` |

일반 개발자는 보통 NPM 설정을 건드릴 필요가 없다.

## 주의사항

- `stack.dev.env`, `db.dev.env`는 commit하지 않는다.
- DB password, token, secret 값은 문서/채팅에 남기지 않는다.
- dohit 컨테이너, 파일, 포트는 건드리지 않는다.
- legacy `api.clipperstudio.ai`, `demo.clipperstudio.ai`는 건드리지 않는다.
- dev DB 포트 `55203/55213/55223`은 임시로 열려 있다.
- stage/prod DB 포트는 WAN에 열지 않는다.
- stage/prod 배포는 아직 시작하지 않았다.

## 아직 없는 것

- DB migration
- application table
- seed data
- 실제 release metadata API
- 실제 사용자 다운로드/login/signup 화면
- admin 운영 기능
