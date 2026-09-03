# TossPayments PG 5대 PC read-only 확인표

- 작성일: 2026-09-03 (Asia/Seoul)
- 대상: `m2-db`, `m2-proxy`, `m2-stage`, `m4-prod`, `storage`
- 목적: 현재 실제 구성을 먼저 알아낸 뒤, 각 장비에 맞는 설치·설정·배포 절차를 별도로 설계한다.
- 실행 주체: 사용자가 각 PC 터미널에서 직접 실행한다. Codex는 명령과 판정 기준만 제공한다.

## 안전 규칙

- 지금 단계에서는 조회 명령만 실행한다. 설치, 수정, 재시작, container 생성/삭제, migration은 하지 않는다.
- `.env`, secret 파일, token, private key, Toss key의 값을 `cat`, `printenv`, `docker inspect`로 출력하지 않는다.
- 결과에 public IP, 사용자 이름, 홈 경로, 이메일, token 또는 key 값이 보이면 공유 전에 가린다.
- DB 명령은 `SELECT`와 `SHOW`만 허용한다. `CREATE`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, `DELETE`,
  migration 명령은 실행하지 않는다.
- 한 장비 결과를 확인하기 전에는 다음 장비의 설정 절차를 추측해서 실행하지 않는다.

## 공통 1차 확인

각 PC에서 먼저 아래 명령을 한 줄씩 실행하고 결과를 전달한다. 일부 명령이 없으면 오류 문구만
전달하고 설치하지 않는다.

```bash
hostname
uname -a
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}'
docker compose version
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
df -h
git --version
```

판정 기준:

- hostname이 사용자가 접속하려던 장비와 일치하는지 확인한다.
- Docker server가 없거나 접근 거부가 나면 그 사실부터 해결 계획에 반영한다. 즉시 `sudo`를 붙이지 않는다.
- `docker ps`에서는 container 이름·image·상태·공개 port만 본다. 환경 변수는 출력하지 않는다.
- 디스크 사용률이 80% 이상인 volume은 배포 전에 별도 용량 계획이 필요하다.

## `m2-db`

공통 결과를 본 뒤 Codex가 실제 DB 실행 형태를 확인해 다음 명령을 하나씩 선택한다.

초기 read-only 후보:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
ss -lnt
```

`ss`가 없는 macOS라면 설치하지 말고 다음을 사용한다.

```bash
lsof -nP -iTCP -sTCP:LISTEN
```

확인할 것:

- PostgreSQL이 host service인지 container인지
- user/admin/release DB의 실제 host·port·DB 이름은 무엇인지
- 5433/5434/5435가 현재 개발 DB인지와 별도 disposable DB를 어디에 만들 수 있는지
- backup 위치와 최근 복구 검증 일시

아직 하지 않을 것: DB 생성, schema 변경, migration 실행, 기존 무통장 데이터 수정.

## `m2-proxy`

초기 read-only 후보:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
ss -lnt
```

확인할 것:

- Nginx Proxy Manager가 container인지 host service인지
- dev/stage/prod web·API hostname이 각각 어느 upstream으로 가는지
- API access log에 query string이 기록되는지, `access_log off` 또는 안전한 log format이 실제로 적용됐는지
- webhook URL이 통과할 route와 TLS 인증서 상태

주의: 전체 proxy config나 access log를 그대로 공유하지 않는다. URL query, cookie, authorization header는
민감 정보일 수 있으므로 Codex가 다음에 제공할 필터 명령으로 필요한 설정 존재 여부만 확인한다.

## `m2-stage`

공통 결과 뒤 실제 checkout/compose 경로를 사용자에게 확인한 후에만 그 경로에서 아래를 실행한다.

```bash
git status --short --branch
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
docker compose config --services
docker compose ps
```

remote URL은 credential이 섞여 나올 수 있으므로 이 단계에서는 조회하지 않는다.

확인할 것:

- stage가 실행하는 API/Admin/Customer image와 source revision
- compose project 이름과 env 파일 위치(값이 아니라 경로만)
- secret mount 파일의 존재 여부와 권한(내용은 읽지 않음)
- stage DB가 `m2-db`의 어느 disposable/non-production DB를 보는지

## `m4-prod`

초기 명령은 `m2-stage`와 같지만, production에서는 확인만 하고 어떤 변경도 하지 않는다.

```bash
git status --short --branch
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
docker compose config --services
docker compose ps
```

확인할 것:

- 실제 production 역할과 실행 중인 revision
- 배포·rollback 단위, health check, 무중단 전환 방식
- env/secret 주입 위치와 소유권(내용은 읽지 않음)
- production DB와 storage 연결 방식

아직 하지 않을 것: production DB 생성, container 재생성, DNS/NPM 수정, Toss 운영 key 설정, 라이브 결제.

## `storage`

초기 read-only 후보:

```bash
df -h
mount
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

확인할 것:

- storage가 제공하는 실제 protocol/NFS/SMB/object storage 역할
- stage/prod가 마운트하는 경로와 read/write 주체
- 결제 영수증·민감 데이터가 저장되는지 여부와 보존 정책
- backup/복구와 용량 경보 방식

파일 목록이나 고객 데이터 내용은 공유하지 않는다.

## 진행 방식

1. 사용자가 한 대에 접속했다고 알린다.
2. Codex가 그 장비의 공통 1차 명령 중 필요한 것만 한 단계씩 안내한다.
3. 사용자는 민감 값을 가린 결과를 전달한다.
4. Codex가 결과를 해석하고 다음 read-only 명령을 제시한다.
5. 다섯 장비의 실제 구성이 확정된 뒤에야 장비별 설정 계획을 작성한다.
6. 설정과 배포 명령도 사용자가 직접 실행하며, 각 변경 전 rollback과 검증 기준을 먼저 확인한다.

현재 상태: 어떤 PC에도 위 명령을 실행하지 않았고, 서버 구성은 전부 미확인이다.
