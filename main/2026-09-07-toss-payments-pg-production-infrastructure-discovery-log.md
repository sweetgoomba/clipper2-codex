# TossPayments PG 운영 인프라 장비별 조사 로그

- 시작일: 2026-09-07 (Asia/Seoul)
- 목적: 실제 5대 장비 구성을 변경 없이 확인한 뒤 운영 인프라 구축·배포 절차를 확정한다.
- 장비 역할 이름: `m2-db`, `m2-proxy`, `m2-stage`, `m4-prod`, `storage`는 Chrome 원격 데스크톱에서
  사용자가 임의로 지정한 이름이다. 실제 OS hostname과 같지 않아도 된다.
- 실행 주체: 사용자가 각 장비의 터미널에서 명령을 직접 실행한다. Codex는 명령과 판정 기준만 제공한다.
- 금지: 비밀값 출력, 기존 DB write/migration, container 변경, 서버 설정 변경, 배포.

## `m2-db` read-only checkpoint

### 장비와 Docker

- 실제 hostname: `metabuzzui-Macmini.local`
- 운영체제/CPU: Darwin 23.6.0, Apple Silicon `arm64`
- Docker client/server: 28.0.4
- Docker Compose: v2.34.0-desktop.1
- 시스템 디스크: 460 GiB 중 139 GiB 사용, 288 GiB 여유, 사용률 33%

### 현재 Clipper 개발 DB

| 역할 | container | PostgreSQL DB | host bind | 상태 | 대략적 크기 |
|---|---|---|---|---|---:|
| User | `clipper-db-user-dev` | `clipper_user_dev` | `192.168.0.7:55203` | healthy | 14 MB |
| Admin | `clipper-db-admin-dev` | `clipper_admin_dev` | `192.168.0.7:55213` | healthy | 9,567 kB |
| Release | `clipper-db-release-dev` | `clipper_release_dev` | `192.168.0.7:55223` | healthy | 8,655 kB |

- 세 DB 모두 PostgreSQL 16.14 `aarch64`이다.
- 세 container 모두 `restart=unless-stopped`이다.
- 각 DB는 서로 다른 Docker named volume을 `/var/lib/postgresql/data`에 연결한다.
- 중지된 Clipper DB container는 없고 stage/prod Clipper DB container도 아직 없다.
- 다른 회사 프로젝트 DB container는 조사·변경 대상에서 제외한다.

### Compose와 저장소

- Compose project: `clipper-db-dev`
- Compose file: `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/db/compose.yml`
- 서비스: `db-user`, `db-admin`, `db-release`
- 실제 환경파일: `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/db.dev.env`
- 환경변수 이름은 Compose가 요구하는 dev DB 20개 항목이 모두 존재한다. 값은 출력하지 않았다.
- `db.dev.env` 권한은 현재 `0644`다. 비밀번호 파일이므로 변경 단계에서 `0600`으로 줄여야 한다.
- `db.stage.env`, `db.prod.local.env` 실제 파일은 아직 없다.
- server checkout: `dev`, tracked working tree clean
- server HEAD와 fetch 전 cached `origin/dev`: `d10d54ed520719811c3d1959763703bf18cc9405`
- `git ls-remote`로 확인한 실제 `origin/dev`: `4d3202263d84de9d046a1abc6eb51826a47009ae`
- 판정: 서버 checkout은 실제 원격 `dev`보다 오래됐다. read-only 단계에서는 fetch/pull하지 않았다.

### 현재 migration 위치

- User DB 마지막 migration: `DropShortformDirectorGeneratedMediaJobs1787800000000`
- Admin DB 마지막 migration: `MigrateReviewPaymentsToTossPaymentsPg1786560000000`
- Release DB 마지막 migration: `AddReleaseArtifactSha5121782790000000`
- Admin DB는 PG 전환 중간 단계까지만 적용된 상태다. `178656` 실행 당시 존재하던 review 주문·event는
  삭제됐지만, 그 뒤 현재 개발 서비스 사용으로 주문 37건과 event 49건이 다시 쌓였다.
- integration 후보 적용 시 Admin DB에는 `178660` 이후 migration이 남아 있다. 확정 정책에 따라
  `178680`은 구형 무통장 요금제·신청·이용권·장부 표를 삭제하고, `178685`는 전체 과거
  `operation_runs`와 연결된 복구 기록을 초기화한다.
- User DB에는 기존 사용자를 소급 지급하지 않고 신규가입 onboarding 작업을 지원하는 `178820`이 남아 있다.
- Release DB에는 현재 integration 후보 기준 추가 migration이 없다.

### 초기화될 개발 데이터 집계

| 대상 | 현재 행 수 | integration migration 결과 |
|---|---:|---|
| 옛 요금제 `plans` | 4 | 표와 데이터 삭제 |
| 무통장 신청 `purchase_requests` | 31 | 표와 데이터 삭제 |
| 옛 이용권 `licenses` | 20 | 표와 데이터 삭제 |
| 옛 사용량 `token_usage` | 0 | 표 삭제 |
| 옛 크레딧 장부 `credit_ledger` | 232 | 표와 데이터 삭제 |
| 작업 실행 `operation_runs` | 190 | 전체 행 삭제 |
| 기존 작업 정책 `operation_policies` | 4 | 현재 여섯 작업 정책 기준으로 교체·정리 |
| 중간 review 결제 주문 `payment_orders` | 37 | legacy review로 분류 후 삭제 |
| 중간 review 결제 event `payment_events` | 49 | 연결 주문과 함께 삭제 |

### 보존될 User DB 데이터 집계

| 대상 | 현재 행 수 | PG migration 결과 |
|---|---:|---|
| 사용자 `users` | 17 | 보존 |
| 로그인 세션 `user_sessions` | 145 | 보존 |
| 데스크톱 인증 코드 `desktop_auth_codes` | 145 | 보존 |
| 숏폼 프로젝트 `shortform_projects` | 1,481 | 보존 |
| 숏폼 작업공간 `shortform_workspaces` | 0 | 보존 |
| 숏폼 클립 `shortform_clips` | 8 | 보존 |
| 참고 분석 replay | 0 | 표는 보존, 현재 AppModule에서는 비활성 |

### 백업 상태와 다음 변경 전 차단 조건

- `clipper_infra/db` 아래에서 `.dump`, `.backup`, `.sql.gz` 백업 파일을 찾지 못했다.
- 현재 Infra의 `db/backup/README.md`도 backup worker가 아직 구현되지 않았다고 명시한다.
- 운영 DB 백업 방식은 팀 회의 뒤에 결정하기로 했고, 현재 운영 인프라 구축을 막지 않는다.
- 개발 DB 백업은 지금 만들지 않는다. 새 운영 DB 구축과 운영 환경 테스트가 끝난 뒤, 실제 개발 DB에
  파괴적 migration을 적용하기 직전에 `m2-db`의 로컬 디스크에 User/Admin/Release DB dump를 만든다.
- 같은 장비의 로컬 백업은 migration 또는 작업 실수에서 되돌리는 용도다. `m2-db` 자체의 디스크·장비
  고장에는 대비하지 못하므로 장기 운영 백업 정책과는 별개다.
- 기존 개발 DB migration 전 확정 순서:
  1. `m2-db` 로컬에 User/Admin/Release DB 각각 PostgreSQL custom-format dump 생성
  2. 파일 존재·크기·checksum 확인
  3. 폐기 가능한 별도 DB에 복원
  4. 복원본에서 integration migration과 앱 시작 seed 예행연습
  5. 사용자가 결과를 확인한 뒤에만 실제 개발 DB에 적용
- 운영 DB 생성 전에는 운영 전용 env, container 이름, DB 이름, port, volume을 dev와 완전히 분리하고
  DB 접근 방화벽 범위를 확인해야 한다.

### 아직 하지 않은 일

- repository fetch/pull/checkout
- env 권한 또는 내용 변경
- stage/prod env 생성
- 백업 생성 또는 복원
- container 생성·삭제·재시작
- DB write/migration
- 방화벽·포트포워딩 변경
- 운영 DB 생성

## 다음 조사

- `storage`라고 부른 장비는 DB/NAS storage가 아니라 Windows 설치형 파일을 build하는 runner PC다.
  DB 인프라 조사 대상에서 제외하고, 추후 Windows release runner 검증 때 별도로 확인한다.
- 다음은 `m2-stage`, `m4-prod` 순으로 실제 구성을 확인한다.

## `m2-proxy` read-only checkpoint

### 장비와 네트워크

- 실제 hostname: `metabuzz-staging.local`
- 운영체제/CPU: Darwin 23.5.0, Apple Silicon `arm64`
- Docker client/server: 28.0.4
- Docker Compose: v2.34.0-desktop.1
- 내부 주소: `en0=192.168.0.2`, `en1=192.168.10.113`
- 기본 게이트웨이: `192.168.0.1`, 기본 interface: `en0`
- 판정: `192.168.0.2`가 Clipper 서버망과 인터넷 기본 경로에 연결된 proxy 주소다.
- 시스템 디스크: 228 GiB 중 106 GiB 사용, 88 GiB 여유, 사용률 55%
- Docker 사용량: image 18.96 GB, build cache 19.58 GB. 약 35 GB가 reclaimable이지만 현재 정리하지 않았다.

### 실행 중 서비스

- `nginx-proxy-manager`
  - image 설정: `jc21/nginx-proxy-manager:latest`
  - 실제 앱 버전: 2.14.0
  - restart: `always`
  - host port: `81`, `18080`, `18443`
  - Compose project: `proxy-server`
  - Compose file: `/Users/metabeojeu/Desktop/infra/proxy-server/docker-compose.yml`
  - `/data`와 `/etc/letsencrypt`는 host directory bind mount다.
- `clipper-web-monitor`
  - restart: `unless-stopped`
  - Compose project: `monitor`
  - Compose file: `/Users/metabeojeu/Desktop/project/clipper2/clipper_infra/ops/monitor/compose.yml`
  - 실제 `targets.json`, `state.json`을 host에서 bind mount한다.
- 같은 장비의 `angular-prod`, `nestjs-prod`는 Clipper가 아닌 다른 회사 프로젝트이므로 조사·변경 대상에서 제외한다.
- Nginx 전체 설정에 대해 `nginx -t`가 성공했다.

### 현재 Clipper proxy와 DNS

| 공개 주소 | 현재 proxy target | HTTPS 상태 |
|---|---|---|
| `dev.clipperstudio.ai` | `192.168.0.23:42203` | 200 |
| `dev-admin.clipperstudio.ai` | `192.168.0.23:42303` | 200 |
| `dev-api.clipperstudio.ai` | `192.168.0.23:43203` | `/health` 200 |

- 위 세 개발 주소만 Nginx Proxy Manager에 등록돼 있다.
- `dev-api` server level에는 기본 access log 선언 뒤 `access_log off`가 있고, Nginx 규칙상 뒤 설정이
  같은 level의 access log를 취소한다. 실제 access log 파일도 크기 0이고 2026-08-16 이후 변경되지 않았다.
- 실제 DNS:
  - `clipperstudio.ai` -> `112.169.113.138`
  - `www.clipperstudio.ai` -> `clipperstudio.ai` -> `112.169.113.138`
  - 개발 주소 세 개 -> `metabuzz.iptime.org` -> `112.169.113.138`
  - `admin.clipperstudio.ai`, `api.clipperstudio.ai`, stage 주소 세 개는 현재 record가 없다.
- 루트와 `www`는 DNS만 public IP에 연결돼 있고 Nginx host/certificate가 없어 TLS SNI 단계에서 거절된다.
- 기존 Infra 문서의 `api.clipperstudio.ai -> 3.34.33.3 legacy API` 설명은 현재 실제 DNS와 다르다.

### 현재 감시 상태

- monitor 대상은 dev web/admin/API 세 개와 dev User/Admin/Release DB 세 개뿐이다.
- 검사 주기 30초, 연속 실패 2회에 장애 판정, recovery cooldown 5분이다.
- 확인 시점에 여섯 대상은 모두 `up`, `consecutiveFailures=0`이었다.
- stage/prod 대상은 아직 없다. 해당 환경 구축·검증 후 별도로 추가해야 한다.

### 저장소와 로컬 설정 보존 위험

- `clipper_infra` server checkout은 `dev`, tracked working tree clean이다.
- server HEAD와 fetch 전 cached `origin/dev`: `da0af4db2f32cb32dbc9f6c3e4b682eea3f9d7bf`
- `git ls-remote`로 확인한 실제 `origin/dev`: `4d3202263d84de9d046a1abc6eb51826a47009ae`
- 판정: server checkout은 실제 원격 `dev`보다 오래됐다. read-only 단계에서는 fetch/pull하지 않았다.
- `/Users/metabeojeu/Desktop/infra/proxy-server`는 Git 저장소가 아니다.
- 핵심 로컬 상태 파일:
  - `data/database.sqlite`: mode `0644`, 163,840 bytes
  - `data/keys.json`: mode `0644`, 2,190 bytes
  - `docker-compose.yml`과 기존 `docker-compose.yml.bak`도 mode `0644`
- `database.sqlite`와 `keys.json`은 같은 Mac의 다른 local account가 읽을 수 있으므로 변경 전에 mode `0600`으로
  줄이는 것이 안전하다. 현재는 변경하지 않았다.
- 기존 `.bak`는 Compose 파일만 보존하며 실제 proxy host·account·certificate 상태 백업이 아니다.
- 운영 proxy 변경 직전에는 `database.sqlite`, `keys.json`, `letsencrypt`를 함께 보존하고 복구 방법을 확인해야 한다.

### 현재 구조와 기존 Infra 문서의 중요한 차이

- 통합 Infra 문서는 proxy와 prod 앱이 같은 `192.168.0.2` 장비에서 실행된다는 이전 가정이 남아 있다.
- 실제 목표 구조에서는 `m2-proxy`와 `m4-prod`가 별도 장비다.
- 따라서 문서의 prod upstream `192.168.0.2:42202/42302/43202`를 그대로 등록하면 안 된다.
- `m4-prod`의 실제 내부 IP와 앱 port를 먼저 확인한 후 prod upstream과 runbook을 고쳐야 한다.
- `api.clipperstudio.ai` 등 DNS/Nginx 변경은 운영 앱과 DB가 준비되고 내부 health 검증까지 끝난 뒤에만 한다.

### 아직 하지 않은 일

- proxy/monitor repository fetch 또는 pull
- Nginx Proxy Manager Compose·DB·key·certificate 변경 또는 백업
- file permission 변경
- Nginx host 추가·수정·삭제 또는 reload/restart
- DNS, router port-forwarding, firewall 변경
- stage/prod monitor target 추가
- Docker image/cache 정리

## `m2-stage` read-only checkpoint

### 실제 역할 정정

- Chrome 원격 데스크톱 이름은 `m2-stage`지만, 이 장비는 현재 Clipper 개발 웹 서버다.
- 이번 운영 배포 대상은 `m4-prod`이며 이 장비에 별도 stage 또는 prod 앱을 배포하지 않는다.
- Infra 저장소에 `compose.stage.yml`이 존재한다는 이유만으로 이 장비에 stage 환경을 만들면 안 된다.
- 앞으로 이 장비는 기존 dev 상태와 prod 구성에 필요한 네트워크 참고 정보만 확인하고 변경하지 않는다.

### 장비와 네트워크

- 실제 hostname: `metabuzzs-Mac-mini-2.local`
- 운영체제/CPU: Darwin 23.6.0, Apple Silicon `arm64`
- Docker client/server: 28.0.4
- Docker Compose: v2.34.0-desktop.1
- 내부 주소: `en0=192.168.0.23`, `en1=192.168.10.111`
- 기본 게이트웨이: `192.168.0.1`, 기본 interface: `en0`
- 판정: Nginx Proxy Manager의 현재 dev upstream `192.168.0.23`과 일치한다.
- 시스템 디스크: 228 GiB 중 133 GiB 사용, 69 GiB 여유, 사용률 66%
- Docker 사용량: images 55.44 GB, build cache 21.14 GB, inactive volumes 1.786 GB.
- 이 장비에는 다른 회사 프로젝트 container/image도 있으므로 `prune` 또는 임의 정리를 하지 않는다.

### 현재 Clipper 개발 서비스

| 역할 | container | image | host bind | 상태 |
|---|---|---|---|---|
| Customer web | `clipper-web-client-dev` | `clipper-web-client:dev` | `192.168.0.23:42203` | Up |
| Admin web | `clipper-web-admin-dev` | `clipper-web-admin:dev` | `192.168.0.23:42303` | Up |
| Web API | `clipper-web-api-dev` | `clipper-web-api:dev` | `192.168.0.23:43203` | Up |

- 중지된 Clipper container는 없고 stage/prod Clipper container도 없다.
- 세 container 모두 Compose project `clipper-dev`, restart policy `unless-stopped`다.
- Compose files:
  - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.yml`
  - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/apps/compose.dev.yml`
- API만 `/Users/metabuzz/Desktop/project/clipper2/.secrets/web-api-dev`를
  `/run/clipper-web-api-secrets`로 bind mount한다.

### source repository 상태

| repository | branch | server HEAD | 실제 `origin/dev` | 판정 |
|---|---|---|---|---|
| Infra | `dev` | `4d3202263d84de9d046a1abc6eb51826a47009ae` | 동일 | clean, 최신 |
| Customer | `dev` | `4b361efc742db797e85848c5aea90eb1736194c5` | 동일 | clean, 최신 |
| Web API | `dev` | `468466e63811076092229ca09223bc01f6671a2b` | `557da3fd22c47009d222d18a231a2b4848d9e5e9` | clean, 원격보다 2개 뒤 |
| Web Admin | `dev` | `eae522f4908c65a55680be09353dd95df2a71190` | 동일 | clean, 최신 |

- Web API 서버 checkout에만 있는 commit은 없다. `rev-list --left-right --count HEAD...origin/dev`는 `0 2`다.
- 서버에 아직 없는 두 commit은 데스크톱 Google 로그인 후 loopback callback으로 돌아오는 기능 commit과 merge commit이다.
- 현재 dev container는 그대로 두고, 이 장비에서 fetch/pull/rebuild/redeploy하지 않았다.

### env와 secret 준비 상태

- 실제 app env는 `env/stack.dev.env`만 있다. `stack.stage.env`, `stack.prod.env`는 없다.
- `.secrets` 아래 실제 secret directory도 `web-api-dev`만 있다.
- `stack.dev.env` mode는 `0644`다. 민감값이 있으므로 향후 승인된 dev 변경 시 `0600`으로 줄여야 한다.
- `user-jwt-private.pem`과 `operator-jwt-secret`은 `0600`, `user-jwt-public.pem`은 `0644`로 적절하다.
- 이번 운영 배포를 위해 이 장비에 stage/prod env나 secret을 만들지 않는다.

### 아직 하지 않은 일

- repository fetch/pull/checkout
- dev image rebuild 또는 container 재시작
- stage/prod env·secret 생성
- stage/prod image build 또는 container 생성
- file permission 변경
- Docker image/cache/volume 정리
