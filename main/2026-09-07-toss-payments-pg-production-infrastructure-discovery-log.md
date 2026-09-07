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
- `stack.dev.env.example`과 실제 `stack.dev.env`의 변수 이름만 비교했고 값은 출력하지 않았다.
- example에만 있는 `SHORTFORM_PROJECT_REPOSITORY`, `SHORTFORM_DATABASE_SYNCHRONIZE`는 현재 Web API 코드에서
  읽지 않는다. DB 설정은 `synchronize: false`로 고정하고 migration을 사용하므로 실제 env에 없는 것이 장애가 아니다.
- 특히 example의 `SHORTFORM_DATABASE_SYNCHRONIZE=true`는 현재 구조와 맞지 않는 오래된 Infra 설정이라
  integration Infra 정리 대상이다.
- 실제 env에만 남은 기존 변수 이름들도 확인했지만 이 장비에서는 삭제하거나 값을 변경하지 않았다.

### 시스템 시각

- 확인 시각: `2026-09-07 12:50:03 KST`, UTC offset `+0900`
- macOS `/usr/libexec/timed` service는 `state=running`이었다.
- 자동 시간 동기화 설정 자체는 관리자 비밀번호를 확인할 수 없어 조회하지 못했다.
- 현재 시각·시간대와 시간 관리 service는 정상이며, 이 미확인 항목은 `m4-prod` 구축을 막지 않는다.

### 아직 하지 않은 일

- repository fetch/pull/checkout
- dev image rebuild 또는 container 재시작
- stage/prod env·secret 생성
- stage/prod image build 또는 container 생성
- file permission 변경
- Docker image/cache/volume 정리

## `m4-prod` read-only checkpoint

### 장비와 네트워크

- 실제 hostname: `m4-produi-Macmini.local`
- 운영체제/CPU: Darwin 25.5.0, Apple Silicon `arm64`
- 내부 주소: `en0=192.168.0.47`, `en1=192.168.10.102`
- 기본 게이트웨이: `192.168.0.1`, 기본 interface: `en0`
- 판정: 운영 앱의 내부 주소는 `192.168.0.47`이다. 기존 Infra 문서의 운영 upstream
  `192.168.0.2`는 실제로는 `m2-proxy` 주소이므로 그대로 사용하면 안 된다.
- 시스템 디스크: 460 GiB 중 104 GiB 사용, 320 GiB 여유, 사용률 25%

### Docker와 현재 서비스

- Docker client/server: 29.4.3
- Docker Compose: v5.1.3
- Docker VM: CPU 10개, memory 약 7.75 GiB, `aarch64`, `overlayfs`
- 현재 container 전체 memory 사용량은 약 0.6 GiB로 운영 Clipper 앱을 추가할 여유가 있다.
- Docker 사용량: image 23.25 GB, build cache 22.65 GB이며 build cache 약 20.75 GB가 reclaimable이다.
  다른 회사 서비스가 함께 실행 중이므로 현재 정리하지 않았다.
- BuildingOn과 Coldmail 운영 container가 이미 실행 중이다. 조사·변경 대상에서 제외한다.
- Clipper 앱 container는 실행 중이거나 중지된 것이 모두 없고, `clipper-web-monitor`만 실행 중이다.
- 사용자가 확정한 초기 운영 배포 방식은 `m2-stage`의 개발 배포와 같은 **서버 직접 build 방식**이다.
  즉 `m4-prod`에 정확한 source commit을 준비하고 이 장비에서 image를 build한다. 현재 Infra에 남은
  GHCR pull 가정은 바로 사용하지 않고 실제 topology와 이 방식에 맞게 정리해야 한다.
- memory가 8 GiB이므로 Customer, Admin, API image를 동시에 build하지 않고 순서대로 build한다.

### 예정 포트와 현재 충돌 여부

| 역할 | 기존 Infra가 정한 prod host port | 확인 결과 |
|---|---:|---|
| Customer web | `42202` | 비어 있음 |
| Admin web | `42302` | 비어 있음 |
| Web API | `43202` | 비어 있음 |

- 이 포트들은 이번 조사에서 새로 만든 번호가 아니다. 기존 `compose.prod.yml`의
  stage=`01`, prod=`02`, dev=`03` 환경 번호 규칙에서 온 값이다.
- 현재 다른 service와 충돌하지 않으므로 유지할 수 있지만, 최종 Compose 수정 전 사용자가 다시 승인한다.

### 현재 Clipper monitor

- container: `clipper-web-monitor`, restart policy `unless-stopped`
- Infra 경로: `/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra`
- 현재 monitor 대상은 dev web/admin/API와 dev User/Admin/Release DB 여섯 개뿐이다.
- 여섯 실제 대상은 모두 `up`, `consecutiveFailures=0`이었다.
- Slack webhook은 설정돼 있다. `m2-proxy`에도 같은 dev monitor가 있으므로 알림 중복 가능성을 나중에
  확인하고 prod monitor 소유 장비를 하나로 정해야 한다.
- `state.json`에는 더 이상 target에 없는 `clipper-backup-local`의 과거 down 상태가 남아 있지만,
  현재 검사 대상은 아니다. 임의로 삭제하지 않았다.
- `ops/monitor/targets.json`과 `ops/monitor/state.json`은 둘 다 tracked file이 아니고 Git에서 무시된다.
  브랜치 checkout이나 commit에 자동으로 섞이지 않는다. 실제 브랜치 전환 직전에는 같은 경로의 tracked
  file 충돌 여부를 다시 확인하고 두 파일을 별도로 보존한다.

### source repository와 원격 branch 준비 상태

- 이 장비에 있는 Clipper Git repository는 `clipper_infra` 하나뿐이다.
- 현재 Infra branch: `feature/web-monitor`, tracked working tree clean
- server HEAD와 실제 원격 `feature/web-monitor`: `da0af4db2f32cb32dbc9f6c3e4b682eea3f9d7bf`
- fetch 전 cached `origin/dev`: `ed505b7b8a816db5d9c8c9e5f7cc3e5020569bc9`
- `git ls-remote`로 확인한 실제 `origin/dev`: `4d3202263d84de9d046a1abc6eb51826a47009ae`
- read-only 단계에서는 fetch, checkout, pull을 하지 않았다.
- GitHub HTTPS 접근은 가능하며 Web Customer/Admin/API의 실제 `dev` ref도 조회됐다.
- 네 repository 모두 원격 `integration/toss-payments-pg-20260903` branch가 아직 없다. 로컬 integration
  후보를 다시 검증하고 명시적으로 push하기 전에는 `m4-prod`에서 clone 또는 checkout할 수 없다.
- 운영 배포를 시작할 때는 `git pull`로 임의 최신 상태를 받지 않고, 승인된 integration branch의 정확한
  commit을 확인한 뒤 checkout한다.

### 운영 env와 secret 준비 상태

- Infra `env` directory에는 example 파일만 있다. 실제 `stack.prod.env`는 없다.
- `/Users/m4-prod/Documents/projects/clipperstudio/.secrets`와 `/opt/clipper/secrets` 모두 아직 없다.
- 따라서 기존 운영 secret을 덮어쓸 위험은 없지만, 배포 전에 운영 전용 JWT key와 operator secret 등
  필요한 파일을 새로 만들고 mode `0600`으로 제한해야 한다.
- secret 값, token, 결제 자격증명은 조사 과정에서 출력하지 않았다.

### 전원 복구와 보안 상태

- `sleep=0`: AC 전원에서 본체 자동 잠자기는 꺼져 있다.
- `womp=1`: network wake가 켜져 있다.
- `autorestart=0`: 정전 후 전원이 돌아와도 Mac이 자동으로 다시 켜지지 않는다.
- FileVault는 꺼져 있어 부팅 시 disk unlock은 필요 없다.
- Docker 앱과 DockerHelper가 로그인 실행 항목에 enabled로 등록된 기록을 확인했다.
- macOS 자동 로그인은 설정돼 있지 않다.
- 현재 조합에서는 정전 후 사람이 Mac을 켜고 사용자 로그인까지 해야 Docker Desktop과
  `restart=unless-stopped` container가 복구된다.
- 무인 복구를 원하면 운영 전에 `autorestart`와 로그인/Docker 시작 방식을 함께 결정해야 한다.
  자동 로그인은 FileVault도 꺼진 장비에 물리적으로 접근한 사람이 계정에 바로 들어갈 수 있다는
  보안 단점이 있으므로 사용자의 명시적 승인 없이 켜지 않는다.
- macOS application firewall과 stealth mode는 모두 꺼져 있다. 이는 공유기 port forwarding과는
  별개지만 같은 내부망에서는 열린 host port에 접근할 수 있다는 뜻이다.
- 방화벽을 바로 켜면 함께 운영 중인 BuildingOn·Coldmail에 영향을 줄 수 있으므로 변경하지 않았다.
  Clipper는 지정된 `192.168.0.47` port에만 bind하고, 인터넷 공개는 `m2-proxy`를 거치며, 공유기가
  Clipper port를 `m4-prod`로 직접 forwarding하지 않는지 go-live 전에 확인해야 한다.
- 시스템 시각은 `2026-09-07 13:22 KST`, UTC offset `+0900`이었고 macOS `timed` service가 실행 중이었다.

### 현재 운영 준비 판정

- 장비 자원, 내부 IP, 예정 port에는 운영 앱을 올릴 수 있는 여유가 있다.
- 그러나 아직 운영 DB, 실제 prod env, prod secret, 앱 source checkout, 앱 image/container, proxy host,
  DNS가 모두 없다.
- 정전 후 자동 복구도 구성되지 않았다.
- 다음 변경 단계로 넘어가기 전에 로컬 integration 후보 네 개를 재검증하고 원격 branch를 준비하며,
  실제 `m2-proxy` + `m4-prod` 분리 구조와 서버 직접 build 방식에 맞춘 구체적 실행 설계를 사용자에게
  쉬운 말로 제시하고 승인받아야 한다.

### 아직 하지 않은 일

- repository fetch/pull/checkout/clone 또는 integration branch push
- monitor target/state 삭제 또는 수정
- Docker image build, container 생성·재시작, cache 정리
- prod env·secret 생성 또는 permission 변경
- 전원, 자동 로그인, 방화벽 설정 변경
- 운영 DB 생성 또는 migration
- Nginx Proxy Manager, router, DNS 변경
- 서버 배포와 결제·환불 실행

## 2026-09-07 데스크톱 이름 논의 보류 후 재개 지점

- 운영판 앱 이름·아이콘은 결정권자 답변 대기다. [별도 결정 대기 기록](./2026-09-07-desktop-dev-prod-app-identity-decision-pending.md)에 현재 개발판 보존 원칙과 검토 후보를 정리했다.
- 이름 결정을 기다리는 동안 운영 인프라 준비를 계속한다. 기존 직원들의 개발판 데이터 이전이나 앱 설정 변경을 진행하지 않는다.
- 장기 운영 브랜치는 대화에서 `main`으로 결정했다. 앞선 조사 기록의 integration branch는 당시 원격에 없던 통합 테스트 후보를 뜻하며, 운영 브랜치명으로 사용하라는 뜻이 아니다. 실제 `main` 생성·반영·push 상태는 배포 준비 단계에서 다시 확인한다.
- 사용자는 개발·운영 모두 서버에서 직접 이미지를 빌드하고, `web`, `admin`, `api`, `all`을 같은 방식으로 선택하기를 원한다. DB migration은 앱 배포와 별도 명령으로 실행하는 방향이다.
- 이번 로컬 파일 확인에서 `scripts/deploy-dev.sh`의 위 서비스 선택 기능은 존재한다. `scripts/deploy-prod.sh`와 `scripts/migrate-db.sh`는 아직 없으며, 앞선 대화의 해당 명령은 구현할 사용법이었다.
- 로컬 `runbooks/deploy-prod.md`도 여전히 이미지 `pull`과 예전 장비 배치를 설명한다. 서버에서 바로 실행할 최신 절차로 간주하지 않는다.
- 다음 작업은 로컬 배포 후보 상태 확인 후 서버 직접 빌드·웹 API 주소 분리·migration 별도 실행을 위한 변경과 검증 범위를 구체화하는 것이다. 이미 확인한 장비 기본 정보는 반복 조사하지 않고 실제 변경 직전에 변동 가능한 항목만 재확인한다.
- 서버 변경 명령은 사용자가 직접 실행한다. 개발 DB 백업·migration은 지금 수행하지 않는 기존 방침을 유지한다.

## 2026-09-07 웹 배포 실행부 로컬 구현

- 사용자 “응 진행해줘” 승인으로 원본 웹 저장소의 integration 브랜치에서 구현했다. 새로운 worktree/복제본은 만들지 않았다.
- 작업 시작 HEAD: infra `fa92eda`, Customer `bedafa3`, Admin `ed1b5a4`, API `25520c6`. 네 저장소는 시작 시 clean이었다. `.codex`의 기존 변경과 무관한 dialog-highlight 문서는 보존했다.
- 개발/운영 `web/admin/api/all` 공통 실행부, 운영 서버 직접 빌드, API 주소 분리, 별도 migration 명령을 추가했다. 실행 시 dev/main 브랜치를 검사하지만 이번에 dev/main을 checkout·merge·push하지 않았다.
- `--build-only`로 이미지를 준비하고 별도 migration 후 `--start-only`로 그 이미지를 실행할 수 있다. 일반 배포에는 migration이 포함되지 않는다.
- 배포/PG/Compose/실제 웹 빌드 최종 97 tests, API datasource 6 tests 및 API build 통과. 실제 DB 접속 없이 검증했다. 별도 read-only 리뷰의 Critical/Important 지적은 없었고 infra 재실행 테스트 제안도 반영했다.
- 운영 env 예제의 이미지와 앱 bind IP만 현재 결정에 맞췄다. 실제 비밀/환경 파일, DB, DNS/NPM, 서버 컨테이너는 변경하지 않았다. 데스크톱 이름·아이콘·runner 분리도 이번 구현에서 제외했다.
- [구체적 계획](./2026-09-07-web-dev-prod-local-build-deployment-plan.md), [사용법·검증·남은 위험](./2026-09-07-web-dev-prod-local-build-deployment-guide.md).
- 저장소별 로컬 checkpoint commit: Customer `53de1d5`, Admin `0315e9d`, API `2f19cc0`, Infra `26faf08`. 원격 push와 dev/main 반영 없음.

## 2026-09-07 웹 환경 이름 정리 후속 작업

- 사용자가 기존 production(개발 서버)/deployment-prod(운영 서버) 명명의 혼동을 지적했고 local/dev/prod 통일을 승인했다.
- Customer/Admin 모두 Angular build/serve 설정과 환경 파일을 local/dev/prod로 통일. package watch=local, 기본 build/Docker ARG=dev, 운영 배포 인자=prod로 변경했다. 화면·API 계약과 실제 연결 대상은 유지했다.
- 기존 production/development/deployment-prod 설정 별칭을 제거했다. 수동 명령을 사용하는 경우 새 local/dev/prod를 사용해야 한다. npm start/build와 deploy-dev/deploy-prod 사용자 명령 형태는 유지된다.
- 테스트101개 통과. 실제 웹 빌드8종 포함. 기존 서버, API, DB, 데스크톱, runner에는 변경 없음.
- [구체적 변경 및 검증 기록](./2026-09-07-web-environment-naming-cleanup.md). 기존 배포 사용법 문서도 현재 명칭으로 갱신했다.
- 후속 checkpoint: Customer `70ac16b`, Admin `472e35e`, Infra `ea57a1a`. 원격 push/서버 반영 없음.

## 2026-09-08 배포 소스 브랜치 강제 제거

- 사용자 요청으로 개발=dev/운영=main 브랜치명 검사와 `git pull --ff-only origin dev/main` 지정을 제거했다. 앞선 9월 7일 기록의 브랜치 검사 설명은 현재 동작이 아니다.
- infra와 선택한 각 웹 저장소에서 현재 체크아웃한 브랜치의 연결된 원격을 대상으로 `git pull --ff-only`를 실행한다. 자동 checkout, 원격/브랜치 fallback은 없다. 갱신 실패 시 중단한다.
- 배포 환경은 여전히 deploy-dev/deploy-prod 명령으로 선택한다. 소스 브랜치명과 독립적으로 Angular 설정, API 주소, 이미지 태그, Compose/DB 대상이 dev/prod로 구분된다.
- 미커밋 변경 보호, 선택 서비스만 빌드·재시작, 별도 migration, build-only/start-only 동작은 유지했다. migration에도 main/dev 브랜치 검사를 강제하지 않으며 pull/build는 하지 않는다.
- TDD: 변경 전 임의 브랜치의 dev/prod 배포 및 migration 테스트 3개가 기존 브랜치 제한 때문에 실패함을 확인했다. 최소 수정 후 배포 테스트 24개 + PG/Compose 71개, 총 95개 통과. Git/Docker 실행은 배포 테스트의 대역으로 검증했고 실제 서버 배포/DB migration은 하지 않았다. Angular 코드는 변경하지 않아 실제 웹 빌드는 이번에 재실행하지 않았다.
- 현재 사용법은 [배포 가이드](./2026-09-07-web-dev-prod-local-build-deployment-guide.md)에 반영했다.
