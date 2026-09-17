# 독립 개발판 — 릴리스 API·runner·관리자 연결 검증

날짜: 2026-09-17 KST. 기준: [릴리스 실행 계획](2026-09-17-independent-dev-release-plan.md), [앱·로그인 선행 결과](2026-09-17-independent-dev-app-validation.md).

**후속 완료:** 사용자 로컬 실행 승인 후 새 전용 PostgreSQL에서 migration/실제 DB 검증 **9 PASS**. [최신 DB 실행 결과](2026-09-17-independent-dev-real-db-validation.md). 아래 migration 미실행·승인 대기는 코드 완료 당시 기록이며, 기존 DB/실 env/원격 서버는 후속에서도 변경하지 않았다. 설치형/Google/템플릿 실기는 여전히 남아 있다.

## 판정

승인된 release 계획 Task 1–3의 코드와 자동 테스트를 연결했다. **실제 DB migration, 원격 빌드·업로드·게시, 설치형 앱의 새 로그인·템플릿 이관·동시 실행은 아직 검증하지 않았다.** 코드 완료 체크포인트이며 배포 가능 판정이 아니다.

원본 checkout의 `integration/dev-pg-local-validation-20260917`에서 작업했다. 기준 HEAD: API `8b074a59a454b47323f9e490d9bfd8d6c2a51ec5`, Infra `f975f34924bcf6c483dc16ba7acb08917b127fd4`, Admin `3d47536b9f8c3e8bf0dfd71dd78805a98f775475`. 이전 Electron/auth 변경은 보존했고 이번 릴리스 변경과 문서도 **미커밋**이다. 커밋·push·병합·배포·실제 환경파일/DB 변경 없음.

## 구현 내용

### 1. API: 개발판과 운영판의 잘못된 빌드·게시·복원 차단

- 채널 `dev` 추가. 개발 profile: `development / ai.clipperstudio.dev / clipperstudio-dev / dev / https://dev-api.clipperstudio.ai`.
- 운영 profile: `production / ai.clipperstudio.app / clipperstudio / stable / https://api.clipperstudio.ai`. 운영 빌드 후보 `rc`, `alpha`도 이 profile이며 앱 runtime 채널은 stable이다.
- `DESKTOP_RELEASE_TARGET=development|production`를 명시해야 새 build/publish/rollback이 가능하다. 미설정이면 구성 오류, 서버 target과 채널/profile 불일치면 거부. NODE_ENV로 추정하지 않는다.
- 서버 build job에 profile을 저장한다. runner 성공 보고는 job과 보고 profile의 다섯 필드를 검사한 후에만 artifact와 성공 상태를 저장한다. 잘못된 보고는 성공 상태를 쓰지 않는다.
- release artifact에 nullable JSONB `desktop_profile` 추가 migration 작성·등록. 기존 이력 삭제/backfill 없음. **실행하지 않았다.** 같은 숫자의 User DB 로그인 migration과 Release DB artifact migration은 서로 다른 DataSource다.
- publish/rollback은 트랜잭션 안에서 profile·대상 platform/arch·build 채널을 검사한다. 게시 대상이 아직 없을 때의 동시 생성은 target tuple advisory lock, 기존 target/build는 row lock으로 보호한다. 테스트는 mock transaction/lock 조건 확인이며 실제 PostgreSQL 경쟁 검증은 남아 있다.
- 성공 보고의 row lock 순서를 기존 start/fail과 같은 **job → build**로 맞췄다. 독립 리뷰가 발견한 역순 잠금 위험을 수정하고 회귀 테스트를 추가했다.
- `dev` feed는 검증된 dev profile만 반환하고 stable로 대체하지 않는다. 기존 null-profile stable/rc/alpha 게시 이력의 읽기는 보존하지만 새 게시/rollback에는 사용할 수 없다. 과거 데이터를 채널명만 보고 새 개발판으로 분류하지 않는다.
- 새 Mac target은 `autoUpdateEnabled=false`. 현재 public `/downloads/latest`도 같은 활성 target 조회를 사용하므로 이 새 비활성 Mac target은 그 경로에서 제공되지 않는다. Mac 공개 HOLD와 일치하는 제한이며 공개 재개 때 다운로드와 업데이트 정책을 별도로 검토한다. 기존 원격 target 상태는 확인/변경하지 않았다.
- DTO/OpenAPI/job payload/report/entity/console 응답을 함께 맞췄다. raw 응답 계약 유지.

### 2. Runner: 지시한 앱과 실제 산출물이 같은지 확인

- job의 profile로 빌드 환경·API·업데이트 채널을 지정하며 runner 주변 환경값이 이를 덮지 못한다.
- HTTP 진입뿐 아니라 공통 `runReleaseJob`에서 플랫폼/아키텍처를 검사한다. direct CLI 우회는 독립 리뷰 후 수정했다. 잘못된 job은 workspace/checkout 전에 거부한다.
- job마다 별도 출력 폴더를 사용한다. 출력 루트 밖 symlink, 다른 빌드의 남은 파일, 여러 installer 후보를 정상 결과로 채택하지 않는다.
- Windows: 출력 `builder-effective-config.yaml`의 appId/protocol과 `win-unpacked/resources/packaged-runtime-config.json`의 profile/build 정보를 검사한다. **설치된 Windows registry 검사가 아니다.**
- Mac: 최종 `.app`의 Info.plist와 resources runtime을 검사하고 `autoUpdateDisabled=true`를 요구한다. Mac 공개·자동빌드·업데이트 HOLD, ZIP 추가 없음.
- 검증한 profile을 성공 보고에 포함한다. 최종 installer 해시/크기를 다시 확인하고 불일치 시 업로드를 막는다.
- 테스트는 임시 파일·모형 빌드·모형 HTTP/업로드를 사용했다. 일부 소스 스냅샷 회귀는 임시 로컬 Git 저장소를 clone한다. 실제 원격 checkout/runner/AWS/서명/빌드 배포를 실행하지 않았다.

### 3. Admin·배포 예제: 사용자가 선택한 채널 그대로 요청

- Windows 빌드는 `dev/stable/rc/alpha`를 명시적으로 선택해야 한다. 숨겨진 rc 기본값 제거.
- 검증된 개발 artifact에는 dev 게시만 제공한다. 운영 artifact는 stable/rc/alpha 선택. null/malformed profile 이력은 조회만 가능하고 새 게시 불가.
- 확인창에 실제 게시 대상·파일·버전·플랫폼 정보를 표시한다. store/HTTP 요청도 선택 채널을 보존한다. 서버 거부 시 오류를 표시하며 성공으로 표시하지 않는다.
- compose에 `DESKTOP_AUTH_TARGET`, `DESKTOP_RELEASE_TARGET` 전달. dev 예제=development, prod=production, stage 예제=빈 값(목적을 정하기 전 desktop login/publication 차단). 실제 `.env`는 수정/출력하지 않았다.
- 활성 소비자가 제거된 `DESKTOP_REDIRECT`를 배포 예제에서 제거했다. 옛 fallback을 거부하는 API 테스트의 fixture 문자열은 테스트 목적상 유지했다.

## 검증 증거

| 대상 | 새로 실행한 결과 | 한계 |
|---|---|---|
| Web API build + 전체 Jest | build PASS, **271 suites / 2,882 PASS / 21 SKIP** | 실제 DB migration/경쟁 검증 아님 |
| Infra runner + Windows script 계약 | **51 PASS / 1 SKIP / 0 FAIL** | Mac에서 실제 PowerShell 검증 1건 skip, 실제 EXE/registry/서명 미실행 |
| Admin versions 대상 ChromeHeadless | **50 PASS / 0 FAIL** | 모형 API, 실제 게시 미실행 |
| Admin build | PASS | initial bundle **582.50 kB**, warning 기준 500 kB 초과. 오류는 아니며 이번 범위에서 budget을 높여 숨기지 않음 |
| API/Infra/Admin git diff --check | PASS | 커밋 아님 |

로그:

- `/tmp/clipper-release-profile-web-api-20260917-final.log`
- `/tmp/clipper-release-profile-runner-20260917-final.log`
- `/tmp/clipper-release-profile-admin-20260917.log`
- `/tmp/clipper-release-profile-admin-build-20260917.log`

TDD: 정책/DTO·거부 시 무변경·profile propagation·산출물 불일치·UI 채널·예제 계약을 RED→GREEN으로 확인했다. 추가 lock-order 및 direct CLI 플랫폼 불일치도 회귀 테스트 후 수정했다. Admin 최초 sandbox build는 진단 메시지 없이 exit 134였으나 동일 명령을 허용된 로컬 권한으로 재실행해 exit 0을 확인했다. 이를 코드 오류라고 추정해 수정하지 않았다.

독립 읽기 전용 리뷰: 위 두 중요 지적을 해결한 후 Task 2–3 최종 재리뷰에서 추가 Critical/Important 없음. 리뷰어는 파일/테스트 코드를 읽었으며 위 실행 결과는 주 에이전트가 실행했다. 이 판정은 실제 DB/OS/배포 검증을 대체하지 않는다.

## 다음 순서·승인 게이트

1. **별도 승인 후 새 격리 PostgreSQL fixture**에서 User 로그인 binding 및 Release artifact migration을 실행하고 실제 트랜잭션/동시 요청/rollback/profile 차단을 검증한다. 기존 개발용 DB 3개 및 운영 DB를 수정하지 않는다. 정확한 새 컨테이너·포트·DB·환경변수 범위를 먼저 제시한다.
2. 위 DB에 연결하는 로컬 API와 새 패키징 앱으로 Google 로그인, 구 개발/신 개발/운영 동시 실행, 서로 다른 데이터/프로토콜/로그인 복귀를 검증한다. 현재 `dist-app`은 이번 릴리스 작업에서 재패키징하지 않았다. 과거 로그인 성공을 새 identity 검증으로 재사용하지 않는다.
3. **필수:** 옛 배포 앱에서 실제 `.cliptpl` 내보내기 → 새 빈 데이터 앱으로 가져오기, 포함 자산/폰트/레이아웃/편집 재열기를 검증한다. 소재·프로젝트 이관은 선택이며 전체 데이터 복사는 하지 않는다.
4. Windows 실제 설치·앱 공존·registry·업데이트/삭제 격리는 사용자가 Windows 장비에서 실행한다. 서버 직접 접속 금지. Mac 자동업데이트/ZIP 및 실제 ML·Build 5 전체 QA HOLD 유지.
5. 이후 원래 PG 로컬 실기·개발 DB 복제본 리허설·배포 계획 승인 순서로 이어간다. 원격 old stable target 처분은 사용자 실행 조회 및 별도 승인 뒤 결정한다. 자동 삭제/backfill 없음.

## 한도

이번 재개 시 주간 잔여 100%, 최종 기록 시 **96%** 확인. reset credit은 호출하지 않았다. 다음 재개 때는 한도를 다시 조회하며, 부족하면 검증된 체크포인트를 남기고 사용자에게 알린다.

## 후속: 실제 로컬 DB 검증안 — 승인 대기

2026-09-17 사용자 `이어서 진행하자` 후 읽기 전용 조사. Docker container/volume 목록, 로컬 리스너, 실제 migration runner/DB 환경변수 해석을 확인했다. DB 접속·생성·SQL 실행 없음. 앱용 실 `.env`/`.env.local`도 읽거나 변경하지 않았다.

### 기존 대상은 보존

- 기존 dev DB: `clipper_web_api-clipper-db-{admin,release,user}-dev-1`, 각각 5433/5434/5435, 실행 중.
- 오늘의 로그인 검증 DB: `clipper-pg-validation-20260917-{admin,release,user}`, 각각 loopback 57433/57434/57435, 실행 중. 앞서 사용자 로그인 확인에 사용한 환경이므로 이번 합성 데이터/동시성 테스트로 덮지 않는다.
- 9/9 검증 DB 56433/56434/56435는 중지 상태 유지. 다른 프로젝트 컨테이너/볼륨도 범위 밖.

### 승인 요청할 새 대상

| 용도 | 컨테이너 | 연결 | DB |
|---|---|---|---|
| Admin | clipper-identity-check-20260917-admin | 127.0.0.1:58433 | clipper_identity_admin |
| Release | clipper-identity-check-20260917-release | 127.0.0.1:58434 | clipper_identity_release |
| User | clipper-identity-check-20260917-user | 127.0.0.1:58435 | clipper_identity_user |

- 각 전용 named volume은 컨테이너 이름 뒤 `-data`. 조회 시 이름 충돌 없음. 포트 리스너도 발견되지 않았으나 생성 직전에 다시 확인하고 점유되면 덮지 않는다.
- 이미 설치된 `postgres:16` linux/arm64 이미지 사용; 로컬 ID `sha256:081f1bc7bd5e143dbb6e487b710bbc27712cdcfaced4c071b8e47349aa1b4171`. 이미지 pull 없음. loopback에만 공개하고 기존 볼륨/호스트 데이터 디렉터리를 마운트하지 않는다.
- 새 빈 3개 DB에 각 named DataSource의 migration 체인을 적용한다. User binding·Release profile 새 컬럼과 pending migration 없음, 반복 실행 시 추가 변경 없음을 확인한다. 기존 migration에는 테이블 삭제/정리도 있으므로 **기존 데이터 DB에서는 실행하지 않는다.** 빈 DB 초기화는 개발 DB 복제본 전환 리허설을 대체하지 않는다.
- Release 컨테이너에 별도 `clipper_identity_release_prod_test` DB를 만들어 production profile 검증을 격리한다. 실제 운영 DB/운영 API에 접속한다는 뜻이 아니다.
- 새 DB에만 합성 사용자·로그인 코드·빌드/게시 이력을 넣고, 1회 code 동시 소비·잘못된 대상 거절·게시/rollback 원자성·잘못된 profile 무변경을 검증한다. 테스트 데이터 수정/정리는 새 전용 DB 안으로 제한한다. 금융 API/Google/원격 runner/업로드는 호출하지 않는다.
- 테스트 프로세스에만 모든 `CLIPPER_{USER,ADMIN,RELEASE}_DATABASE_{HOST,PORT,NAME,USER,PASSWORD}`를 명시한다. `DOTENV_CONFIG_PATH=/dev/null`로 migration의 기본 `.env` 로딩을 차단하며 접속 직전 실제 resolved host/port/database를 allowlist와 대조한다. 실 `.env`를 바꾸거나 일반 앱 서버를 무심코 시작하지 않는다.
- 이 단계 종료 후 새 컨테이너는 중지 가능하며 전용 볼륨은 보존한다. 기존 컨테이너/볼륨 삭제·정리 없음. 실제 앱과 연결할 환경 설정/Google 로그인 실기는 다음 단계에서 범위를 다시 설명한다.

아직 컨테이너·DB·볼륨 생성, migration, 테스트 fixture 구현/실행을 하지 않았다. 승인 뒤 이 범위로 진행한다. 제품 코드·커밋·push·배포 변경 없음. 주간 잔여 96% 재확인, reset 호출 없음.
