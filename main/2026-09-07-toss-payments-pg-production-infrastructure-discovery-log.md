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
- 다음은 `m2-proxy`, 이후 `m2-stage`, `m4-prod` 순으로 실제 구성을 확인한다.
