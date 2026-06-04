# Clipper2 Infra Technical Guide

작성일: 2026-06-02

## Scope

이 문서는 Clipper2 web/backend 인프라를 dev, stage, prod 3환경으로 구성하기 위한 기술 설계 초안이다.

설계 문서는 `.codex`에 둔다. 2026-06-02 기준으로 `clipper_infra`에는 초기 compose/env/runbook 구성을 만들었다. 실제 IP, 도메인, S3 bucket, image tag, DB password 같은 운영 값은 아직 placeholder다.

## Assumptions

- 운영 서버는 Mac mini 3대다.
- Windows 설치형 앱 빌드는 사무실 Windows PC self-hosted runner에서 수행한다.
- Windows code signing 인증서는 사무실 Windows PC에 설치되어 있다.
- macOS 설치형 앱 빌드는 별도 Mac mini self-hosted runner에서 수행한다.
- 설치파일 저장소는 기존 S3를 유지한다.
- 코드 push/main merge는 설치파일 release trigger가 아니다.
- Windows release와 macOS release는 플랫폼별로 독립 관리한다.
- dev, stage, prod 3환경을 모두 설계한다.

## Current Initial Setup

`clipper_infra` initial setup:

```text
apps/
  compose.yml
  compose.dev.yml
  compose.stage.yml
  compose.prod.yml
db/
  compose.yml
  backup/README.md
env/
  stack.dev.env.example
  stack.stage.env.example
  stack.prod.env.example
  db.env.example
ops/monitor/
  targets.example.json
proxy/
  routes.md
release-metadata/
  dev.example.json
  stage.example.json
  prod.example.json
runbooks/
  deploy-db.md
  deploy-dev.md
  deploy-stage.md
  deploy-prod.md
  release-installer.md
```

Validation already performed:

```text
docker compose config --quiet for dev/stage/prod app stacks: passed
docker compose config --quiet for DB stack: passed
release metadata JSON parse: passed
monitor targets JSON parse: passed
```

## High-Level Architecture

```text
Developer laptops
  -> GitHub repos
  -> CI/CD controller
      -> office Windows PC runner
          -> npm run build:app:win:x64
          -> Windows code signing
          -> S3 upload
      -> Mac mini runner
          -> npm run build:app:mac:arm64
          -> macOS signing/notarization
          -> S3 upload
      -> optional web/admin/API image build
  -> S3 release storage
  -> release metadata/update feed
  -> dev/stage/prod web client download pages
```

```text
External users/internal testers
  -> edge proxy
  -> web client/admin/API containers
  -> environment-specific DB
  -> S3 installer downloads
```

## Server Roles

### Mac mini 1: proxy/prod app host

Recommended containers:

```text
edge proxy
clipper-web-client-prod
clipper-web-admin-prod
clipper-web-api-prod
```

Role:

- Public ingress for Clipper domains.
- Prod download/product web.
- Prod admin web.
- Prod API.

### Mac mini 2: dev/stage app host

Recommended containers:

```text
clipper-web-client-dev
clipper-web-admin-dev
clipper-web-api-dev
clipper-web-client-stage
clipper-web-admin-stage
clipper-web-api-stage
```

Role:

- Dev integration environment.
- Stage release-candidate validation environment.
- Internal access only, or protected by auth/IP allowlist.

### Mac mini 3: DB/backup/monitor host

Recommended containers:

```text
clipper-db-dev
clipper-db-stage
clipper-db-prod
clipper-backup-dev
clipper-backup-stage
clipper-backup-prod
clipper-health-monitor
```

Role:

- Dedicated DB host.
- Environment-specific PostgreSQL containers and volumes.
- Backup workers.
- Health monitoring.

## Environment Semantics

| Environment | Purpose | Stability | Data Policy | Installer Channel |
| --- | --- | --- | --- | --- |
| `dev` | developer integration | can break | reset allowed | `dev` |
| `stage` | release candidate validation | prod-like | reset carefully | `stage` |
| `prod` | real users | stable | protected | `prod` |

## Service Inventory

### Web client

Repo: `clipper_web_client`

Purpose:

- Download/product page.
- OS/platform-specific installer buttons.
- Release notes.
- Public-facing product information.

Containers:

```text
clipper-web-client-dev
clipper-web-client-stage
clipper-web-client-prod
```

### Admin web

Repo: `clipper_web_admin`

Purpose:

- Release management.
- Installer metadata verification.
- User/license/admin operations.

Containers:

```text
clipper-web-admin-dev
clipper-web-admin-stage
clipper-web-admin-prod
```

### Web API

Repo: `clipper_web_api`

Purpose:

- Release metadata API.
- Update feed API.
- S3 download URL resolution.
- Auth/license/admin backend.

Containers:

```text
clipper-web-api-dev
clipper-web-api-stage
clipper-web-api-prod
```

### PostgreSQL

Recommended containers:

```text
clipper-db-dev
clipper-db-stage
clipper-db-prod
```

Recommended DB names:

```text
clipper_dev
clipper_stage
clipper_prod
```

Recommended volumes:

```text
clipper_postgres_data_dev
clipper_postgres_data_stage
clipper_postgres_data_prod
```

## Port Plan

Use a separate range from dohit.

| Env | web client | admin web | API | DB |
| --- | ---: | ---: | ---: | ---: |
| stage | 42201 | 42301 | 43201 | 55201 |
| prod | 42202 | 42302 | 43202 | 55202 |
| dev | 42203 | 42303 | 43203 | 55203 |

Notes:

- These are host ports for server containers.
- They are not desktop plugin ports.
- Desktop plugin-specific fixed port/env lists remain forbidden.

## Domain Plan

`clipperstudio.ai` is registered at Hosting.KR, but its authoritative name
servers are Cloudflare:

```text
adele.ns.cloudflare.com
owen.ns.cloudflare.com
```

Therefore DNS record changes are managed in Cloudflare, not Hosting.KR.

Current office WAN IPv4 confirmed from `m2-proxy`:

```text
112.169.113.138
```

ipTIME reports this WAN address as dynamic DHCP. ipTIME DDNS is configured:

```text
metabuzz.iptime.org -> 112.169.113.138
```

For dev/stage records, prefer Cloudflare DNS-only CNAME records to
`metabuzz.iptime.org`. A records to `112.169.113.138` work only while the WAN
IP remains unchanged.

Current ipTIME forwarding:

```text
80  -> 192.168.0.2:80
443 -> 192.168.0.2:443
```

Existing dohit DB WAN forwards `55101/55102/55103` point to `192.168.0.7`.
Do not add Clipper DB ports `55201/55202/55203` to WAN port forwarding.

Existing legacy Clipper records must be preserved until legacy cutover:

```text
api.clipperstudio.ai   -> 3.34.33.3
demo.clipperstudio.ai  -> 121.138.93.3
```

Dev domain layout:

```text
dev.clipperstudio.ai          -> clipper-web-client-dev
dev-admin.clipperstudio.ai    -> clipper-web-admin-dev
dev-api.clipperstudio.ai      -> clipper-web-api-dev
```

Stage domain layout:

```text
stage.clipperstudio.ai        -> clipper-web-client-stage
stage-admin.clipperstudio.ai  -> clipper-web-admin-stage
stage-api.clipperstudio.ai    -> clipper-web-api-stage
```

Prod domain layout after Clipper2 cutover:

```text
clipperstudio.ai                -> clipper-web-client-prod
www.clipperstudio.ai            -> clipper-web-client-prod
admin.clipperstudio.ai          -> clipper-web-admin-prod
api.clipperstudio.ai            -> clipper-web-api-prod after legacy cutover
```

`clipperstudio.ai` currently points to a Cloudflare Pages holding page. Replace
that only when the Clipper2 prod product/download page is ready.

Do not move `api.clipperstudio.ai` to Clipper2 until the legacy Clipper API is
retired or a cutover window is approved.

## Container Layout By Server

### Mac mini 1

```text
edge-proxy
clipper-web-client-prod  : host 42202
clipper-web-admin-prod   : host 42302
clipper-web-api-prod     : host 43202
```

### Mac mini 2

```text
clipper-web-client-dev    : host 42203
clipper-web-admin-dev     : host 42303
clipper-web-api-dev       : host 43203

clipper-web-client-stage  : host 42201
clipper-web-admin-stage   : host 42301
clipper-web-api-stage     : host 43201
```

### Mac mini 3

```text
clipper-db-dev       : host 55203
clipper-db-stage     : host 55201
clipper-db-prod      : host 55202
clipper-backup-dev
clipper-backup-stage
clipper-backup-prod
clipper-health-monitor
```

## Compose Project Names

Use separate Compose project names.

```text
clipper-dev
clipper-stage
clipper-prod
clipper-db
clipper-monitor
```

Avoid sharing dohit networks, volumes, DB users, backup paths, or secrets.

## Image Build And Deploy Model

For web/admin/API, prefer image-based deployment.

```text
CI/CD
  -> build clipper_web_client image
  -> build clipper_web_admin image
  -> build clipper_web_api image
  -> push images to registry
  -> target server pulls images
  -> docker compose up -d
```

Server-side source builds should be avoided for prod if possible.

## Desktop Installer Release Model

Installer release is separate from web/admin/API deployment.

### Windows

Runner:

```text
office Windows PC self-hosted runner
```

Command:

```text
npm run build:app:win:x64
```

Responsibilities:

- Build Windows installer.
- Apply Windows code signing.
- Upload artifact to S3.
- Update platform-specific release metadata.

### macOS

Runner:

```text
Mac mini self-hosted runner
```

Command:

```text
npm run build:app:mac:arm64
```

Responsibilities:

- Build macOS arm64 installer.
- Apply signing/notarization.
- Upload artifact to S3.
- Update platform-specific release metadata.

## Release Trigger Policy

Do not release installers on ordinary push/merge.

```text
push/main merge
  -> tests
  -> build checks
  -> no installer release
  -> no S3 installer upload
  -> no update feed change
```

Installer release requires explicit trigger.

```text
dev windows release trigger
stage windows release trigger
prod windows release trigger

dev macos release trigger
stage macos release trigger
prod macos release trigger
```

Prod should require manual approval or promote from a stage-validated artifact.

## S3 Layout

Recommended prefix layout:

```text
s3://<bucket>/clipper2/dev/windows/
s3://<bucket>/clipper2/dev/macos/

s3://<bucket>/clipper2/stage/windows/
s3://<bucket>/clipper2/stage/macos/

s3://<bucket>/clipper2/prod/windows/
s3://<bucket>/clipper2/prod/macos/
```

Artifacts should include version/platform in filename.

```text
Clipper2-0.9.12-windows-x64.exe
Clipper2-0.9.10-macos-arm64.dmg
```

## Release Metadata

Release metadata must be environment-specific and platform-specific.

Example:

```json
{
  "environment": "stage",
  "platforms": {
    "windows-x64": {
      "version": "0.9.12",
      "channel": "stage",
      "s3Key": "clipper2/stage/windows/Clipper2-0.9.12-windows-x64.exe",
      "downloadUrl": "https://...",
      "sha256": "...",
      "releasedAt": "2026-06-02T00:00:00Z"
    },
    "macos-arm64": {
      "version": "0.9.10",
      "channel": "stage",
      "s3Key": "clipper2/stage/macos/Clipper2-0.9.10-macos-arm64.dmg",
      "downloadUrl": "https://...",
      "sha256": "...",
      "releasedAt": "2026-06-02T00:00:00Z"
    }
  }
}
```

The storage backend can be DB or manifest files. Decide before implementing `clipper_web_api`.

## Update Feed

The update feed can be served by `clipper_web_api`.

```text
GET /v1/releases/latest?env=stage&platform=windows-x64
GET /v1/releases/latest?env=stage&platform=macos-arm64
```

Public download pages can call the same API, or consume a simplified endpoint.

```text
GET /v1/downloads/latest/windows
GET /v1/downloads/latest/macos
```

## Deployment Flows

### Dev web/API deploy

```text
developer branch/main integration
  -> build web/admin/API images
  -> deploy to Mac mini 2
  -> use dev DB
```

### Stage web/API deploy

```text
stage deploy trigger
  -> build or select image tags
  -> deploy to Mac mini 2
  -> use stage DB
```

### Prod web/API deploy

```text
prod deploy approval
  -> select release image tags
  -> deploy to Mac mini 1
  -> use prod DB
```

### Dev installer release

```text
dev release trigger
  -> selected platform runner builds installer
  -> upload to S3 dev prefix
  -> update dev release metadata
```

### Stage installer release

```text
stage release trigger
  -> selected platform runner builds installer
  -> upload to S3 stage prefix
  -> update stage release metadata
  -> QA verifies installer
```

### Prod installer release

```text
stage verified
  -> prod release approval
  -> promote stage artifact or rebuild prod artifact
  -> upload to S3 prod prefix
  -> update prod release metadata
```

## DB And Backup

Recommended:

```text
clipper-db-dev
  DB: clipper_dev
  Backup: optional or short retention

clipper-db-stage
  DB: clipper_stage
  Backup: daily

clipper-db-prod
  DB: clipper_prod
  Backup: daily minimum
```

Backup destinations:

```text
local backup path
NAS backup path
optional offsite backup
```

Prod and stage restore drills should be documented before launch.

## Monitoring

Initial monitor targets:

```text
dev web health
dev API health
stage web health
stage API health
prod web health
prod API health
dev DB TCP/pg_isready
stage DB TCP/pg_isready
prod DB TCP/pg_isready
backup freshness
S3 release metadata availability
```

Avoid duplicate Slack alerts from multiple monitor instances.

## Security Rules

- Do not commit real secrets.
- Do not commit runtime state.
- Do not share dohit DB users or backup paths.
- DB ports should be reachable only from required app hosts/admin IPs.
- Admin web should be protected by auth and ideally IP allowlist/VPN.
- Windows signing certificate stays on the designated Windows PC.
- macOS signing/notarization credentials must be managed on the Mac runner or secure secret storage.

## Initial Implementation Order

1. Decide exact domains and server IPs.
2. Decide S3 bucket/prefix layout.
3. Decide release metadata storage: DB vs manifest files.
4. Replace placeholder env values in server-local `env/*.env`.
5. Define `clipper_web_api` release metadata endpoints.
6. Deploy DB containers on DB server.
7. Deploy dev web/admin/API containers.
8. Wire dev download page to dev release metadata.
9. Deploy stage web/admin/API containers.
10. Set up Windows PC runner release trigger for `npm run build:app:win:x64`.
11. Set up Mac mini runner release trigger for `npm run build:app:mac:arm64`.
12. Add stage release flow.
13. Deploy prod web/admin/API containers.
14. Add prod release approval/promote flow.
15. Implement backup worker and monitor.

## Open Decisions

- Exact domain names.
- Whether prod app containers live on proxy server or a separate app server later.
- Proxy tool: existing Nginx Proxy Manager vs config-as-code proxy.
- Release metadata storage backend.
- Whether prod installer release rebuilds or promotes stage artifacts.
- Whether Windows/macOS product versions must always match.
- Whether dev/stage/prod apps have separate app IDs/update channels.
