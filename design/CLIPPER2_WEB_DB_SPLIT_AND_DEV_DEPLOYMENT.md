# Clipper2 Web DB Split And Dev Deployment

작성일: 2026-06-05 KST

마지막 갱신: 2026-06-08 KST

## Scope

이 문서는 2026-06-05 세션에서 정한 Clipper2 web/admin/API scaffold,
server DB split, dev DB deployment 기준을 정리한다.

이 문서는 확정된 운영 기준과 아직 미정인 설계 항목을 분리해서 기록한다.

## Today Completed

- `.codex`와 `clipper_infra`의 기존 diverged branch 상태를 정리했다.
- `clipper_web_admin`, `clipper_web_api`, `clipper_web_client`의 비어 있던
  `main` 브랜치를 initial commit으로 publish했다.
- `clipper_infra`에 user/admin/release 3-way DB split compose/env/runbook을
  추가했다.
- `clipper_web_api`에 최소 API scaffold를 추가했다.
- `clipper_web_client`에 최소 public web/download scaffold를 추가했다.
- `clipper_web_admin`에 최소 admin web scaffold를 추가했다.
- 로컬에서 app/db compose config, Node tests, Docker image build, local smoke를
  검증했다.
- `clipper_infra`, `clipper_web_api`, `clipper_web_client`,
  `clipper_web_admin` 변경을 commit/push했다.
- `.codex`의 이전 문서 커밋은 사용자가 직접 push했다.
- m2-db에서 Clipper dev DB 3개를 실제 배포했다.
- m2-stage에서 m2-db의 dev DB port `55203`, `55213`, `55223` 접근을
  확인했다.
- m2-stage에 Clipper2 dev web/admin/API real services를 server-side build로
  배포했다.
- dev 도메인 3개를 health/browser 기준으로 확인했다.
- Angular blank screen 원인이 `zone.js` polyfill 누락임을 확인하고
  `clipper_web_client`, `clipper_web_admin`에 수정 커밋을 반영했다.

## DB Split Decision

Clipper2 server DB는 환경별로 세 PostgreSQL 컨테이너로 나눈다.

```text
user DB
admin DB
release DB
```

이 split은 "관리자 권한 유저"와 "일반 유저"를 완전히 다른 사람으로 보는
기준이 아니다. 기준은 데이터의 source of truth와 운영 표면이다.

### User DB

User DB는 Clipper 서비스를 사용하는 고객/기업/유저가 실제 서비스에서 쓰는
현재 상태와 데이터의 source of truth다.

Examples:

```text
users
organizations / companies
memberships
roles / permissions
social login accounts
subscription current state
credit balances
credit transactions
bank transfer requests
official templates and template metadata
user-facing service settings
```

공식 템플릿은 user DB 쪽이다. 이유는 공식 템플릿 등록 권한은 관리자 권한
체크를 거치지만, 등록된 템플릿 자체는 모든 유저가 조회하고 사용하는
user-facing service data이기 때문이다.

무통장입금 신청도 유저가 만든 요청 상태이므로 user DB에 둔다. 관리자가
승인하면 user DB의 이용권/크레딧 현재 상태가 변경된다.

### Admin DB

Admin DB는 관리자 페이지 전용 운영 데이터와 audit data를 둔다.

Examples:

```text
admin action logs
admin internal notes
bank transfer review logs
manual credit adjustment audit
subscription change audit
permission change audit
admin-page-only workflow state
```

중요한 기준:

```text
현재 이용권 상태, 만료일, 크레딧 잔액의 source of truth는 user DB다.
관리자가 그 상태를 변경했다는 처리 이력과 내부 메모는 admin DB다.
```

같은 데이터가 user DB와 admin DB에 동시에 source of truth로 존재하면 안 된다.

### Release DB

Release DB는 설치형 앱 배포/update feed 데이터를 둔다.

Examples:

```text
app versions
installer artifacts
release notes
update feed metadata
platform latest version state
rollout state
```

Release data는 admin이 등록/관리하지만, web client가 다운로드 정보로 읽고
desktop app이 update feed로 읽는다. 접근자 기준으로는 user/admin 모두가
관련되므로 별도 release DB가 더 명확하다.

## Environment Layout

### Dev

```text
compose project: clipper-db-dev

db-user    -> clipper-db-user-dev    -> 192.168.0.7:55203 -> clipper_user_dev
db-admin   -> clipper-db-admin-dev   -> 192.168.0.7:55213 -> clipper_admin_dev
db-release -> clipper-db-release-dev -> 192.168.0.7:55223 -> clipper_release_dev
```

### Stage

```text
compose project: clipper-db-stage

db-user    -> clipper-db-user-stage    -> 55201 -> clipper_user_stage
db-admin   -> clipper-db-admin-stage   -> 55211 -> clipper_admin_stage
db-release -> clipper-db-release-stage -> 55221 -> clipper_release_stage
```

### Prod Self-Hosted

```text
compose project: clipper-db-prod

db-user    -> clipper-db-user-prod    -> 55202 -> clipper_user_prod
db-admin   -> clipper-db-admin-prod   -> 55212 -> clipper_admin_prod
db-release -> clipper-db-release-prod -> 55222 -> clipper_release_prod
```

### Prod External DB

Prod may use an external PostgreSQL service instead of self-hosted containers.
No provider is fixed.

In this mode, do not run DB Compose for prod. Create the external PostgreSQL
databases with the selected provider/tooling and set the prod app env:

```text
CLIPPER_USER_DATABASE_URL=postgresql://...
CLIPPER_ADMIN_DATABASE_URL=postgresql://...
CLIPPER_RELEASE_DATABASE_URL=postgresql://...
```

Docker Compose only creates self-hosted containers on the Docker host where it
is executed. It does not create external/cloud database services.

## What DB Compose Creates

Running DB Compose creates:

```text
PostgreSQL containers
Docker named volumes
Docker network
initial PostgreSQL database/user/password inside each container
healthchecks
```

It does not create app tables, migrations, seed data, accounts, templates, or
release rows.

Tables must be created later through `clipper_web_api` migration tooling or
explicit SQL scripts.

## Data Persistence

This keeps data:

```sh
docker compose --env-file ../env/db.dev.env -f compose.yml down
docker compose --env-file ../env/db.dev.env -f compose.yml up -d
```

This deletes database data:

```sh
docker compose --env-file ../env/db.dev.env -f compose.yml down -v
```

Use `down -v` only for intentional reset.

## Schema Promotion

Creating stage DB containers does not copy dev schema or dev data.

Expected workflow:

```text
write migration files in source control
run migrations against dev
run the same migrations against stage
run the same migrations against prod during approved release/deploy window
```

Dev data is not promoted to stage by default. If stage needs realistic data,
use explicit seed scripts or approved sanitized backup restore.

## Web Repositories

### clipper_web_client

Role:

```text
public product/download page
installer download buttons
release notes
login/signup entry point
future user portal for account, entitlement, credit, or payment-related flows
```

Current scaffold:

```text
Angular 19 app
placeholder root page only
includes zone.js polyfill
Docker image builds Angular output and serves it with Nginx
Docker-buildable and deployable
```

The real client-facing download/login/signup pages are being developed
separately. Until those changes are merged, the deployed page should remain a
plain placeholder.

### clipper_web_admin

Role:

```text
admin page
user/account/permission management
entitlement/credit/payment operation handling
bank transfer review
installer release management
admin audit and internal operation tools
```

Current scaffold:

```text
Angular 19 app
placeholder root page only
includes zone.js polyfill
Docker image builds Angular output and serves it with Nginx
Docker-buildable and deployable
```

### clipper_web_api

Role:

```text
remote server API called by web client/admin and, when needed, desktop local backend
login/signup/social login backend
permission and entitlement checks
official template publish/read API
release/update feed API
central DB access
```

Current scaffold:

```text
NestJS app
GET /healthz
GET /v1/health
GET /v1/info
GET /v1/releases/latest -> 501 placeholder
Docker-buildable and deployable
```

`/healthz` and `/v1/health` connect to all three PostgreSQL URLs and run
`SELECT 1`.

Health behavior:

```text
200 -> user/admin/release DB URLs are configured and reachable
503 -> at least one DB URL is missing or unreachable
```

The health response reports non-secret connection status only. It does not
expose database URLs.

The current NestJS scaffold is still intentionally minimal. It validates infra,
proxy, runtime env, and Docker wiring before migrations/auth/release metadata
are implemented.

## Dev App Deployment Strategy

2026-06-08 decision: dev web/admin/API uses server-side builds on m2-stage.
Registry/GHCR push-pull is not the current dev deployment path.

Recommended m2-stage layout:

```text
/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

The app repos are siblings of `clipper_infra`, not ignored subdirectories
inside the infra repo.

Deployment flow:

```text
git pull each app repo
docker build -t clipper-web-client:dev ./clipper_web_client
docker build -t clipper-web-admin:dev ./clipper_web_admin
docker build -t clipper-web-api:dev ./clipper_web_api
docker compose --env-file ../env/stack.dev.env -f compose.yml -f compose.dev.yml up -d --force-recreate
```

The Angular web/admin images include Nginx only to serve static Angular build
output inside their own containers. This is separate from the edge Nginx Proxy
Manager on m2-proxy.

## Desktop Local Backend vs Web API

`clipper_nestjs` inside the Electron app is the local backend.

Responsibilities:

```text
local project data
local filesystem state
local template drafts
local render/preview workflows
Python renderer and plugin orchestration
desktop Angular local API
```

`clipper_web_api` is the remote server backend.

Responsibilities:

```text
central login/signup
social login coordination
account/permission/entitlement/credit server state
official template publish/read
release/update metadata
server DB access
```

The desktop local NestJS should not connect directly to central server DBs.
When central data is needed, it should call `clipper_web_api` and cache locally
only where appropriate.

## Social Login And Deep Link Notes

Social login for a desktop app generally uses the system browser instead of
embedding provider login inside the app UI.

Potential callback strategies:

```text
custom protocol deep link, e.g. clipper2://auth/callback
loopback redirect, e.g. http://127.0.0.1:<random-port>/callback
```

The exact auth/deep-link design is not finalized.

Web flows likely include login/signup and may later include account,
entitlement, credit, payment request, or payment status pages. Which flows
remain inside desktop and which flows open the web client is not finalized.

## Dev DB Deployment Completed

On m2-db:

```text
clipper-db-user-dev     healthy, 192.168.0.7:55203
clipper-db-admin-dev    healthy, 192.168.0.7:55213
clipper-db-release-dev  healthy, 192.168.0.7:55223
```

From m2-stage:

```text
nc -vz 192.168.0.7 55203 -> succeeded
nc -vz 192.168.0.7 55213 -> succeeded
nc -vz 192.168.0.7 55223 -> succeeded
```

## DBeaver And Direct DB Access

The dev DB ports are intended to be reachable from m2-stage to m2-db, not from
arbitrary local machines or the public internet.

Known access behavior:

```text
m2-stage -> 192.168.0.7:55203/55213/55223 works
local Mac mini -> 192.168.0.7:55203 timed out in user test
```

If DBeaver shows:

```text
Connection attempt timed out
```

that means TCP network reachability failed before PostgreSQL authentication.
It is not a database password error. A wrong password would normally produce an
authentication failure after a connection is established.

Recommended options:

- Run DBeaver on m2-stage through Google Remote Desktop.
- Or use VPN/SSH tunneling for local DBeaver access.
- Later decision: temporarily use ipTIME WAN port forwarding for Clipper dev DB
  only, matching the current dohit convenience pattern. Replace this with
  VPN/SSH tunneling later.
- Do not WAN-forward Clipper stage/prod DB ports.

DBeaver connection targets:

```text
User DB:    192.168.0.7:55203 / clipper_user_dev    / clipper_user_dev_user
Admin DB:   192.168.0.7:55213 / clipper_admin_dev   / clipper_admin_dev_user
Release DB: 192.168.0.7:55223 / clipper_release_dev / clipper_release_dev_user
```

Temporary WAN-forwarded dev targets:

```text
User DB:    metabuzz.iptime.org:55203 / clipper_user_dev    / clipper_user_dev_user
Admin DB:   metabuzz.iptime.org:55213 / clipper_admin_dev   / clipper_admin_dev_user
Release DB: metabuzz.iptime.org:55223 / clipper_release_dev / clipper_release_dev_user
```

## Dev App Deployment Completed

On m2-stage:

```text
/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/
```

Deployment strategy:

```text
server-side build on m2-stage
no GHCR/registry push-pull for this first dev deployment
```

Server-local env:

```text
clipper_infra/env/stack.dev.env
```

The env file was copied from `stack.dev.env.example`. The user filled the DB
passwords manually. No secret values were repeated in chat/logs.

Final m2-stage containers:

```text
clipper-web-client-dev healthy 192.168.0.23:42203->80/tcp
clipper-web-admin-dev  healthy 192.168.0.23:42303->80/tcp
clipper-web-api-dev    healthy 192.168.0.23:43203->43203/tcp
```

NPM routes:

```text
dev.clipperstudio.ai        -> http://192.168.0.23:42203
dev-admin.clipperstudio.ai  -> http://192.168.0.23:42303
dev-api.clipperstudio.ai    -> http://192.168.0.23:43203
```

The user corrected an NPM route mismatch where `dev.clipperstudio.ai` was
initially pointing to the admin upstream.

Final verification:

```text
https://dev.clipperstudio.ai        -> C / CLIPPER2 WEB / Coming Soon
https://dev-admin.clipperstudio.ai  -> A / CLIPPER2 ADMIN / Coming Soon
https://dev-api.clipperstudio.ai/v1/health -> JSON health response
```

Chrome/CDP verification showed no remaining Angular runtime errors after
adding the `zone.js` polyfill.

## Commits And Pushes

Pushed:

```text
clipper_infra       49faa91 feat: split Clipper DB stack into user admin release
clipper_web_api     ec13be7 feat: add minimal web API scaffold
clipper_web_client  791c935 feat: add minimal web client scaffold
clipper_web_admin   fef456a feat: add minimal web admin scaffold
clipper_infra       decdfa0 docs: document Clipper dev server-side deployment
clipper_web_api     d641942 feat: scaffold NestJS web API
clipper_web_client  6fa1ffc feat: scaffold Angular dev client
clipper_web_admin   ffba705 feat: scaffold Angular dev admin
clipper_web_client  e2102db fix: include Angular zone polyfill
clipper_web_admin   e21cabe fix: include Angular zone polyfill
clipper_web_api     8386865 feat: verify database connections in health checks
```

`.codex` documentation commits include:

```text
e09fa2e docs: record Clipper web scaffold and DB split
f4207ad docs: hand off Clipper2 dev deploy session
a289b03 docs: update m2-stage deploy handoff
```

This document was updated again after the m2-stage dev deployment was
completed; verify latest `.codex` HEAD with `git log -1 --oneline`.

## Still Not Done

- No app DB migrations exist yet.
- No app tables or seed data exist yet.
- `clipper_web_api` health checks now connect to PostgreSQL, but no query layer,
  migrations, tables, or seed data exist yet.
- `clipper_web_api` `8386865` is deployed to m2-stage and dev API health
  reports all three DBs connected.
- `GET /v1/releases/latest` is still a `501` placeholder.
- Social login/deep-link design is not finalized.
- Payment module integration is not finalized. Current payment direction is
  manual bank transfer request/review.
- Real client-facing download/login/signup pages are being developed separately
  and are not part of the deployed placeholders yet.
- Stage/prod web/admin/API deployment has not started.
