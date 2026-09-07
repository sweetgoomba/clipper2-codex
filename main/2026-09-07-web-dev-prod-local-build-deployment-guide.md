# 개발·운영 웹 배포 명령과 검증 기록

## 현재 상태 — 아직 서버에서 실행하지 않는다

2026-09-07, 원본 저장소의 integration 브랜치에서 로컬 구현했다. 서버의 파일·컨테이너·DB는 변경하지 않았다. 운영 `main`에 반영하거나 원격으로 push하지 않았다.

이 문서는 새 사용법이다. `web/clipper_infra/runbooks/deploy-prod.md`의 GHCR pull·예전 서버 배치는 이번 결정과 다르므로 실행 기준으로 사용하지 않는다. 새 문서는 사용자 요청대로 `.codex`에만 둔다.

로컬 체크포인트: Customer `53de1d5`, Admin `0315e9d`, API `2f19cc0`, Infra `26faf08`. 모두 기존 integration 브랜치의 커밋이며 운영 main 반영/원격 push는 하지 않았다.

## 매번 같은 명령을 사용한다

서버에서 해당 `clipper_infra` 폴더로 이동한 상태의 명령이다. 아래는 사용법 설명이며 지금 서버에서 실행하라는 지시가 아니다.

| 대상 | 개발 서버(m2-stage) | 운영 서버(m4-prod) |
|---|---|---|
| Customer만 | `./scripts/deploy-dev.sh web` | `./scripts/deploy-prod.sh web` |
| Admin만 | `./scripts/deploy-dev.sh admin` | `./scripts/deploy-prod.sh admin` |
| API만 | `./scripts/deploy-dev.sh api` | `./scripts/deploy-prod.sh api` |
| 셋 모두 | `./scripts/deploy-dev.sh all` | `./scripts/deploy-prod.sh all` |

`client`, `web-client`는 web 별칭, `web-admin`은 admin 별칭이다. 대상 생략 시 all이다.

기본 동작은 다음과 같다.

1. 명령·환경 파일·브랜치·미커밋 변경을 확인한다. 개발은 dev, 운영은 main이다. 다른 브랜치를 자동 checkout하거나 파일을 삭제/stash하지 않는다.
2. infra를 fast-forward로 갱신한다. 실행부가 갱신되면 새 실행부로 재실행한다.
3. 해당 환경의 Compose 설정을 읽고 로컬 이미지 이름을 검증한다. API 선택 시 DB 대상과 PG 설정도 확인한다. 설정값 전체나 비밀은 출력하지 않는다.
4. 선택한 소스 저장소를 갱신하고, 그 서버에서 Docker 이미지를 하나씩 빌드한다. 모두 성공한 다음 선택한 컨테이너만 다시 실행한다. 다른 회사 프로젝트는 대상에 넣지 않는다.
5. 컨테이너 상태를 표시한다. 이것은 결제·로그인·웹훅까지 검증됐다는 뜻이 아니다. 별도 기능 확인이 필요하다.

이미지의 기본 태그는 dev/prod다. 추가로 `환경-소스SHA` 태그와 소스 SHA 라벨을 자동으로 붙인다. 사용자가 매번 커밋번호를 명령에 입력하지 않는다. 과거 이미지의 자동 삭제는 하지 않는다.

## DB가 바뀌는 배포는 3단계로 나눈다

예: 운영 API의 새 DB 구조가 필요한 경우.

```sh
./scripts/deploy-prod.sh api --build-only
# 실제 DB 대상·백업/복구 준비·기존 앱 쓰기 중단 여부를 먼저 확인한다.
./scripts/migrate-db.sh prod
./scripts/deploy-prod.sh api --start-only
```

- `--build-only`: 소스를 갱신하고 이미지만 만든다. 앱 시작과 DB 변경은 하지 않는다.
- `migrate-db.sh`: 이미 만들어 둔 로컬 API 이미지를 사용한다. 이미지가 없으면 멈춘다. 소스 갱신·이미지 다운로드·빌드·앱 배포·관리자 seed는 하지 않는다.
- 실행 전 User/Admin/Release DB의 접속 호스트·포트·이름을 표시한다(비밀번호/사용자명 제외). 사용자가 `migrate prod` 또는 `migrate dev`를 입력해야 진행한다.
- User → Admin → Release 순서로, 각 DB의 등록된 migration 중 아직 적용되지 않은 것만 실행한다. 기존 API migration 실행기를 재사용한다. 기존 DB를 만드는 명령 자체는 아니므로 빈 운영 DB 3개는 먼저 별도로 준비해야 한다.
- `--start-only`: 새 소스를 받거나 다시 빌드하지 않고, 준비한 이미지를 실행한다. migration 직후 코드가 바뀌는 것을 피하기 위한 옵션이다.
- 개발도 prod 대신 dev로 같은 사용법이다. **그러나 기존 개발 DB의 백업·migration은 운영 DB 구축과 테스트가 끝난 뒤에 진행한다는 기존 결정은 그대로다.**

주의: 세 DB는 하나의 트랜잭션이 아니다. Admin 단계에서 실패하면 User 변경은 이미 끝났을 수 있다. 다음 Release 단계는 실행하지 않는다. 자동 되돌리기도 하지 않는다. 실패한 DB와 적용 이력을 확인한 후 대응한다.

## 웹 API 주소는 빌드 때 결정한다

| 빌드 설정 | 결과물에 들어가는 API |
|---|---|
| 기존 `production` | `https://dev-api.clipperstudio.ai` |
| `production,deployment-prod` | `https://api.clipperstudio.ai` |

기존 설정의 `production`은 최적화 빌드라는 Angular 이름이며, 이 프로젝트에서는 이미 개발 서버용 주소로 사용 중이었다. 이름만 보고 운영 서버용이라고 판단하면 안 된다. 기존 동작을 바꾸지 않고, 운영 주소 교체 설정을 추가했다. 배포 스크립트가 위 설정을 선택하므로 사용자가 외울 필요는 없다.

Customer/Admin Dockerfile의 `ANGULAR_CONFIGURATION` 인자로 전달한다. 웹 컨테이너 시작 후 환경변수로 SPA의 API 주소를 바꾸는 방식이 아니다. 개발·운영의 로그인/결제 요청이 상대 환경으로 섞이지 않도록 실제 빌드 결과물에서 확인했다.

## 저장소별 변경 이유와 보존한 것

### Infra

- 문제: 개발 배포만 있었고 운영 예제는 GHCR/프록시 PC 배치를 가정했다. 앱 배포와 별도 migration 사용법은 대화에만 있었다.
- 보존: web/admin/api/all, 기존 별칭, fast-forward 갱신, 개발 포트, 개발 monitor·다른 서버 설정.
- 해결: dev/prod 얇은 wrapper와 공통 Node 실행부, 명시적인 migration 명령, build-only/start-only. 운영 예제는 로컬 이미지와 관찰된 m4-prod IP `192.168.0.47`로 변경했다.
- 보안: shell source로 env 파일을 실행하지 않는다. Compose JSON과 실패 상세 출력은 비밀 노출 방지를 위해 표시하지 않는다. 실패 단계는 출력한다. 조사할 때도 원문 로그를 채팅에 그대로 붙이지 않는다.
- 한계: 현재 승인된 자체 호스팅 DB 이름/포트(User 55202/3, Admin 55212/3, Release 55222/3)에 맞춰 검사한다. 추후 클라우드 DB나 명명 변경 시 검증 규칙도 명시적으로 수정해야 한다. IP/DB 이름 검사는 실제 DB의 신원·백업 존재까지 보장하지 않는다.

### Customer / Admin

- 문제: 동일한 기본 빌드가 개발 API를 가리켰다.
- 보존: 기존 production/development 설정과 화면/API 계약. 데스크톱 앱은 수정하지 않았다.
- 해결: 운영 전용 environment 파일, Angular 설정, Docker 빌드 인자만 추가했다.

### API

- 문제: runtime Docker 이미지에는 TypeScript 빌드 결과만 있고 기존 migration 실행기 파일이 없었다. 기존 npm DB 명령은 컨테이너에 없는 개발용 빌드 도구를 먼저 실행한다.
- 해결: 기존 `scripts/typeorm-run-migration.mjs` 파일을 runtime 이미지에 복사한다. 이미 컴파일한 datasource를 node로 직접 실행한다.
- 보존: 모든 migration 파일·등록 목록·데이터 정책·서비스 시작 동작. 이번 변경은 DB 삭제 범위를 추가하거나 변경하지 않는다.

## 검증과 남은 일

- 최종 종합 실행: 배포/PG/Compose/웹 빌드 테스트 97개 통과(2026-09-07). 실행 명령은 `node --test scripts/deployment.test.mjs scripts/validate-toss-payments-env.test.mjs scripts/web-build.integration.test.mjs`(infra 폴더)다. 로컬 Node 24에서 검증했고 Dockerfile의 Node 22 runtime 빌드는 별도 확인이 남아 있다.
- 별도 read-only 코드 리뷰: Critical/Important 지적 없음. Minor 제안인 infra 갱신 후 1회 재실행·반복 갱신 차단 테스트 2개를 추가해 통과했다.
- TDD: 배포 동작 테스트 실패를 먼저 확인하고 구현했다. start-only 테스트도 추가 후 실패→통과 순서로 검증했다.
- 기존 쉘 소스의 특정 문구를 찾던 테스트 1개는, 실제 공통 실행부가 PG 검증 실패 시 빌드를 중단하는 동작 테스트로 교체했다.
- 웹 빌드 테스트: Customer/Admin 각각 개발/운영 빌드를 임시 경로에 생성하고 JavaScript의 올바른 API 주소 포함·반대 환경 주소 부재를 검사한다. 기존 untracked build 폴더는 건드리지 않는다.
- API: `npm run build`, datasource 단위 테스트 6개, compiled datasource 3개와 migration 실행기 구문 확인. DB 연결·migration 실행은 하지 않았다.
- 외부 Git/Docker 명령은 배포 테스트에서 가짜 실행파일로 대체한다. PG 설정 테스트는 가짜 값으로 실제 `docker compose config`만 사용한다.
- 실제 Docker 이미지 빌드/runtime 검증, 서버에서의 main 갱신, 서비스 재기동과 health 확인, 실제 신규 DB migration은 아직 하지 않았다.
- 동시에 두 배포 명령을 실행하지 않는다. all 빌드가 중간에 실패하면 일부 로컬 태그만 갱신될 수 있으므로 성공적으로 준비를 마치기 전 start-only를 실행하지 않는다. 현재 자동 잠금/자동 rollback은 범위에 넣지 않았다.
- prod env example은 완성된 실서버 설정이 아니다. 비밀키·Google callback·JWT·CORS·S3 권한·독립 runner 주소·보류 중인 데스크톱 로그인 프로토콜을 따로 검토해야 한다. 기존 개발 runner/protocol을 그대로 운영에 연결하지 않는다.
- 신규 운영 DB, TLS/NPM/DNS, 운영 main의 준비는 다음 수동 단계다. 운영 앱 이름·아이콘 결정은 기다리되 웹/DB 준비 자체는 계속할 수 있다.
