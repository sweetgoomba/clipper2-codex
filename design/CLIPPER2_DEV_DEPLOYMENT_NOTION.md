# Clipper2 Dev Deployment

Last updated: 2026-06-08 KST

이 문서는 Clipper2 dev web/admin/API와 dev DB가 현재 어디에 어떻게 배포되어
있는지, 코드 수정 후 어떻게 다시 배포하는지 정리한 Notion 공유용 문서다.

Secret 값과 DB password는 이 문서에 적지 않는다.

## Current Status

Dev 배포는 완료되어 있다.

| Area | Status |
| --- | --- |
| Dev web | deployed |
| Dev admin | deployed |
| Dev API | deployed |
| Dev DB user/admin/release | deployed |
| API to DB connectivity | healthy, all three DBs connected |
| Stage/prod app deployment | not started |
| DB migrations/tables/seeds | not created yet |
| Release metadata API | placeholder, `501` |

현재 dev URL:

| URL | Purpose |
| --- | --- |
| `https://dev.clipperstudio.ai` | public web placeholder |
| `https://dev-admin.clipperstudio.ai` | admin placeholder |
| `https://dev-api.clipperstudio.ai/v1/health` | API health |

현재 placeholder 화면:

| URL | Expected content |
| --- | --- |
| `https://dev.clipperstudio.ai` | `C / CLIPPER2 WEB / Coming Soon` |
| `https://dev-admin.clipperstudio.ai` | `A / CLIPPER2 ADMIN / Coming Soon` |

API health는 세 DB 연결 상태를 확인한다.

Expected health shape:

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

## Server Roles

| Server | LAN IP | Role |
| --- | --- | --- |
| m2-proxy | `192.168.0.2` | Nginx Proxy Manager, public HTTPS entry |
| m2-stage | `192.168.0.23` | dev app containers: web/admin/API |
| m2-db | `192.168.0.7` | dev PostgreSQL containers |

Public internet traffic path:

```text
Cloudflare DNS
-> office WAN / ipTIME
-> m2-proxy Nginx Proxy Manager
-> m2-stage app container port
-> API connects to m2-db PostgreSQL ports
```

## Git Repos On m2-stage

The dev app server uses a server-side build layout.

Path:

```text
/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

The app repos are siblings of `clipper_infra`.

Current pushed commits:

| Repo | Branch | Current commit |
| --- | --- | --- |
| `clipper_infra` | `feature/infra-initial-setup` | `decdfa0 docs: document Clipper dev server-side deployment` |
| `clipper_web_client` | `main` | `e2102db fix: include Angular zone polyfill` |
| `clipper_web_admin` | `main` | `e21cabe fix: include Angular zone polyfill` |
| `clipper_web_api` | `main` | `8386865 feat: verify database connections in health checks` |

## Deployment Method

현재 dev는 server-side build 방식이다.

즉, GitHub Container Registry/GHCR에 이미지를 push/pull하지 않는다. 코드가
GitHub에 push되면 m2-stage에서 repo를 pull하고, m2-stage에서 Docker image를
직접 build한 뒤 Docker Compose로 container를 recreate한다.

Code push alone does not deploy automatically.

## App Containers On m2-stage

Docker Compose files:

```text
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.yml
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.dev.yml
```

Server-local env file:

```text
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/stack.dev.env
```

Do not commit or paste this env file because it contains real DB passwords.

Final dev containers:

| Compose service | Container name | Image | Host port |
| --- | --- | --- | --- |
| `web-client` | `clipper-web-client-dev` | `clipper-web-client:dev` | `192.168.0.23:42203 -> 80` |
| `web-admin` | `clipper-web-admin-dev` | `clipper-web-admin:dev` | `192.168.0.23:42303 -> 80` |
| `api` | `clipper-web-api-dev` | `clipper-web-api:dev` | `192.168.0.23:43203 -> 43203` |

`web-client` and `web-admin` images build Angular output and serve it through
Nginx inside each app container. This Nginx is only for static file serving and
is separate from Nginx Proxy Manager on m2-proxy.

`api` runs Node/NestJS directly. It does not include Nginx.

Important: Compose service names are `web-client`, `web-admin`, and `api`.
They are not the same as container names.

For example, this is wrong:

```sh
docker compose up -d --force-recreate clipper-web-api
```

Use this instead:

```sh
docker compose up -d --force-recreate api
```

## Nginx Proxy Manager

Nginx Proxy Manager runs on m2-proxy.

Known m2-proxy compose root:

```text
/Users/metabeojeu/Desktop/infra/proxy-server
```

Public DNS is managed in Cloudflare. The dev records point to the office WAN
through ipTIME DDNS:

```text
dev.clipperstudio.ai
dev-admin.clipperstudio.ai
dev-api.clipperstudio.ai
-> metabuzz.iptime.org
```

ipTIME forwards public HTTP/HTTPS traffic to m2-proxy:

| External port | Internal target |
| ---: | --- |
| `80` | `192.168.0.2:80` |
| `443` | `192.168.0.2:443` |

NPM proxy hosts:

| Domain | Upstream |
| --- | --- |
| `dev.clipperstudio.ai` | `http://192.168.0.23:42203` |
| `dev-admin.clipperstudio.ai` | `http://192.168.0.23:42303` |
| `dev-api.clipperstudio.ai` | `http://192.168.0.23:43203` |

NPM options used for dev:

| Option | Value |
| --- | --- |
| Force SSL | on |
| HTTP/2 Support | on |
| HSTS | on, by operator decision |
| Websockets Support | on |
| Block Common Exploits | on |
| Cache Assets | off |

Do not modify legacy routes without explicit cutover approval:

| Domain | Current purpose |
| --- | --- |
| `api.clipperstudio.ai` | legacy Clipper API |
| `demo.clipperstudio.ai` | legacy Clipper demo |

## Dev Databases On m2-db

Dev DBs are split into three PostgreSQL containers.

| DB role | Container | Host/port | Database | User |
| --- | --- | --- | --- | --- |
| user | `clipper-db-user-dev` | `192.168.0.7:55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| admin | `clipper-db-admin-dev` | `192.168.0.7:55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| release | `clipper-db-release-dev` | `192.168.0.7:55223` | `clipper_release_dev` | `clipper_release_dev_user` |

DB compose project:

```text
clipper-db-dev
```

DB compose files on m2-db are from:

```text
clipper_infra/db/compose.yml
clipper_infra/env/db.dev.env
```

Actual dev DB bind host is `192.168.0.7`, so m2-stage can access the DBs over
the LAN. Example env files may contain placeholder/default values; use the
server-local `db.dev.env` on m2-db as the source of truth.

The DB containers create PostgreSQL databases/users and persistent Docker
volumes. They do not create application tables. Tables will be created later by
migrations.

Current DB connection status:

| From | Result |
| --- | --- |
| m2-stage -> `192.168.0.7:55203` | reachable |
| m2-stage -> `192.168.0.7:55213` | reachable |
| m2-stage -> `192.168.0.7:55223` | reachable |
| `clipper_web_api /v1/health` -> all DBs | connected |
| local Mac mini -> `192.168.0.7:55203` | timed out in user test |

The local Mac mini timeout is a network reachability issue, not a password
issue. A wrong password would normally produce an authentication error after TCP
connection succeeds.

Do not add Clipper DB ports to WAN port forwarding:

```text
55203
55213
55223
```

## DBeaver Access

Recommended:

1. Open Google Remote Desktop to m2-stage.
2. Run DBeaver on m2-stage.
3. Connect to `192.168.0.7` DB ports from there.

DBeaver targets:

| Connection name | Host | Port | Database | User |
| --- | --- | ---: | --- | --- |
| Clipper user dev | `192.168.0.7` | `55203` | `clipper_user_dev` | `clipper_user_dev_user` |
| Clipper admin dev | `192.168.0.7` | `55213` | `clipper_admin_dev` | `clipper_admin_dev_user` |
| Clipper release dev | `192.168.0.7` | `55223` | `clipper_release_dev` | `clipper_release_dev_user` |

If local DBeaver must be used, use VPN or SSH tunnel. Do not expose DB ports on
the router.

There are no application tables yet, so seeing only default PostgreSQL schemas
is normal.

## Redeploy After Code Changes

General flow:

1. Developer changes code locally.
2. Commit and push to GitHub.
3. On m2-stage, pull the changed repo.
4. Build the local Docker image on m2-stage.
5. Recreate the corresponding Docker Compose service.
6. Verify URL/health.

### Redeploy Web Client

Run on m2-stage:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_client
git pull --ff-only
docker build -t clipper-web-client:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-client
```

Verify:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps web-client
curl -I https://dev.clipperstudio.ai
```

### Redeploy Admin

Run on m2-stage:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_admin
git pull --ff-only
docker build -t clipper-web-admin:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate web-admin
```

Verify:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps web-admin
curl -I https://dev-admin.clipperstudio.ai
```

### Redeploy API

Run on m2-stage:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_web_api
git pull --ff-only
docker build -t clipper-web-api:dev .

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate api
```

Verify:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps api
curl -s https://dev-api.clipperstudio.ai/v1/health
```

Expected API health after DB connection checks:

```text
status: ok
userConnected: true
adminConnected: true
releaseConnected: true
checks.user/admin/release.status: ok
```

### Rebuild And Recreate All App Services

Run on m2-stage:

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

Verify:

```sh
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml ps
curl -I https://dev.clipperstudio.ai
curl -I https://dev-admin.clipperstudio.ai
curl -s https://dev-api.clipperstudio.ai/v1/health
```

## Useful Commands

List compose service names:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml config --services
```

Expected:

```text
web-client
api
web-admin
```

Check app containers:

```sh
docker ps --filter name=clipper-web-client-dev
docker ps --filter name=clipper-web-admin-dev
docker ps --filter name=clipper-web-api-dev
```

Check DB reachability from m2-stage:

```sh
nc -vz 192.168.0.7 55203
nc -vz 192.168.0.7 55213
nc -vz 192.168.0.7 55223
```

Check DB containers on m2-db:

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra/db
docker compose --env-file ../env/db.dev.env -f compose.yml ps
```

## Current Limitations

- No DB migrations yet.
- No application tables or seed data yet.
- `GET /v1/releases/latest` still returns `501 release_metadata_not_implemented`.
- Real client-facing download/login/signup pages are being developed separately.
- Admin operational features are not implemented yet.
- S3 installer artifact and update feed integration is not complete yet.
- Stage/prod app deployment has not started.

## Rules

- Do not print or paste DB passwords in chat or docs.
- Do not commit `stack.dev.env` or `db.dev.env`.
- Do not open Clipper DB ports to WAN.
- Do not touch dohit containers, files, or ports during Clipper deployment.
- Do not change legacy `api.clipperstudio.ai` or `demo.clipperstudio.ai`
  without explicit cutover approval.
