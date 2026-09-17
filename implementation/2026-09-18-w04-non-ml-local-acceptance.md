# W04 비-ML 로컬 PG acceptance 결과

검증일: 2026-09-18 KST

## 결론

정식 PG 통합 브랜치의 비-ML 자동 검증과 별도 폐기 가능 PostgreSQL 검증을 통과했다. 실제 ML 플러그인 실행, Build 5 전체 QA, 개발 DB 복제본 rehearsal, 개발서버 배포·DB 변경은 수행하지 않았다. 따라서 이 결과는 **로컬 비-ML 코드/DB 경계 통과**이며 개발서버 전환 승인이나 전체 W04 완료 판정이 아니다.

## 검증 작업 공간

- 8개 원본 checkout은 `integration/dev-pg-local-validation-20260917`.
- Angular `19b407a7a6de`, Electron `6766c0645d81`, Nest `884fa8bc7abf`, Python `60417ce86549`, Web API `8b074a59a454`, Web Client `a4bc54b5852e`, Admin `3d47536b9f8c`, Infra `f975f34924bc`.
- Electron/Web API/Admin/Infra의 독립 개발판 identity·로그인·release 분리 변경은 아래 최종 검증 후 각각 `d95c050` / `36b049f` / `01d0b93` / `f0af3f5`로 커밋하고 각 원격 통합 브랜치에 push했다. 네 저장소는 로컬/원격 SHA 일치·clean이다. Angular/Nest는 템플릿 수정 로컬 커밋 뒤 clean/ahead 1이다.

## 자동 검증

### Desktop Nest

- build PASS.
- 과금 attempt/outbox/crash/restart/cancel/archive/owner isolation/Dance·Dialog·Shortform·Variation 경계: 115 PASS.
- access/credit 원격 응답 runtime 검증, terminal 알림, Shortform preflight·asset fallback 제거·retry prepare: 41 PASS.
- job enum/migration, owned child TERM→KILL, 실제 POSIX descendant 종료, Python runtime lifecycle, 짧은 ffmpeg 렌더: 37 PASS. 최초 sandbox 실행에서 PID 조회와 loopback bind 2건이 환경 제한으로 실패했으나 동일 테스트를 정상 권한으로 재실행해 17/17 PASS했다.
- 실제 ML 모델/플러그인은 실행하지 않았다.

### Angular

- 과금 service, 재시작 recovery, 공통 charge guard, account summary refresh, 프로젝트 재시도/확인 흐름: 202 PASS.
- 최초 잘못된 include 경로로 4건만 실행된 결과는 증거로 사용하지 않고, 실제 경로를 바로잡아 202건을 재실행했다.

### Web API

- build PASS.
- operation start/terminal/DB repository, access, credit summary/grant/ledger 계약: 9 suites / 61 PASS.
- access grant/free trial, credit grant, operation pool/recovery/policy/OpenAPI/Admin recovery: 11 suites / 107 PASS.
- 모든 tier의 `all` entitlement와 등록 플러그인 판정/catalog: 4 suites / 63 PASS.
- 새 격리 DB 정책 e2e: 1 PASS. 무료체험 400, access 없는 유효 credit 소비·환급, 구독 access/credit, 독립 top-up, 구독 종료 뒤 top-up credit 사용을 한 흐름으로 검증했다. Toss provider는 호출하지 않고 test client key와 합성 provider snapshot만 썼다.

### Electron

- 독립 개발판 package name 누락을 발견했다. 설계·lockfile·테스트는 `clipper-studio-dev`였지만 `package.json`만 `clipper-electron`이었다. 이 상태면 Windows updater cache가 옛 개발판과 `clipper-electron-updater`를 공유할 수 있다.
- 이미 존재하던 실패 테스트 2건으로 RED를 재현한 뒤 `package.json`의 root `name` 한 줄을 `clipper-studio-dev`로 수정했다. dependency/version 변경 없음.
- TypeScript build 및 전체 suite 975 PASS. 이후 승인된 명칭 통일에 따라 개발/운영 updater cache 계약은 각각 `clipper-studio-dev-updater` / `clipper-studio-updater`로 변경했다. 개발 protocol은 `clipperstudio-dev`, Mac 자동 업데이트 HOLD를 유지한다. 변경 후 재검증 결과는 이 문서의 후속 기록에 추가한다.
- 이 변경은 Electron의 위 커밋에 포함해 원격 통합 브랜치에 push했다.

### Release/profile 후속 리뷰 보완

- 운영 package/cache의 과거 내부명 `clipper` / `clipper-updater`는 공개 배포 전 정리하기로 승인했다. 최종 계약은 개발 `clipper-studio-dev` / `clipper-studio-dev-updater`, 운영 `clipper-studio` / `clipper-studio-updater`다. appId, protocol, userData 및 업데이트 채널 값은 바꾸지 않았다.
- Web API는 runner 성공 보고를 저장하기 전에 job target을 기준으로 Windows/x64=`exe`, macOS/arm64=`dmg`인지 검사한다. 불일치 시 job/build/artifact/attempt 성공 mutation을 수행하지 않는다.
- Infra runner는 Windows 업로드 전에 effective package name과 최종 `win-unpacked/resources/app-update.yml`의 provider, 정확한 API/channel/platform/arch feed, updater cache를 대조한다. 불일치 fixture에서 업로드가 추가되지 않고 failed 보고가 생성됨을 검증했다.
- 보완 후 Electron TypeScript build와 전체 975 PASS, Web API build와 전체 271 suites/2,884 PASS·21 SKIP, Web Admin build와 전체 571 PASS, Infra 전체 36 PASS. 최초 일반 샌드박스 실행의 loopback `EPERM`은 같은 명령을 루프백 허용 환경에서 재실행해 전부 통과했다. Web Admin build의 기존 initial bundle 예산 경고는 있었지만 exit 0이다.
- 실제 Windows EXE/NSIS 생성·설치와 updater cache 실기는 수행하지 않았다. Mac 자동업데이트 HOLD도 유지한다.

## 실제 격리 DB

- 새 컨테이너: `clipper-pg-w04-20260918-{admin,release,user}`.
- loopback port: Admin 55433, Release 55434, User 55435.
- 전용 volume: 같은 이름에 `-data` suffix.
- migration: Admin 64, Release 3, User 10 PASS.
- 실제 DB 조회: `trial`, `basic`, `pro`, `business` 모두 `entitlement_mode=all`. 기존 entitlement row 16개가 남아 있어도 `all` 모드에서는 기능을 제한하지 않는 계약을 unit test와 함께 확인했다.
- 검증 뒤 컨테이너 3개는 `exited`, volume은 보존했다.
- 기존 개발 DB 5433–5435, 실제 로그인 검증 DB 57433–57435, 원격 DB에는 SQL을 실행하지 않았다.

## 기존 사용자 실기와 함께 확인된 항목

- macOS 새 개발판 Google 로그인, 무료체험/access/credit 표시, 사용 가능 400.
- 로그인 상태 재실행 유지, 로그아웃 상태 재실행 유지, 재로그인 복원.
- 사용자 템플릿 export/import 및 기본 16개 중복 방지.

## 남은 항목

1. 설치형 앱에서 실제 렌더를 쓰지 않는 방식의 네트워크 offline→online terminal outbox/잔액 UI 실기는 자동화 증거로 대체 가능한 범위를 더 판단해야 한다. 실제 렌더 실패·성공은 ML HOLD 때문에 이번에 실행하지 않았다.
2. 개발 DB 복제본에서 데이터 분류·전환 rehearsal 및 dump 복원 rollback 검증.
3. 결과를 사용자와 확인한 뒤에만 개발서버 전환 계획 작성. 서버 명령은 사용자가 실행한다.
4. Windows 설치파일/동시 설치·로그인·업데이트 cache 실기는 사용자 Windows 서버에서 수행한다.
5. 운영판과 새 개발판 macOS 동시 설치·실행 및 각 protocol 딥링크 실기는 W09에 남아 있다.

## 변경·배포 상태

- 새 병합 0, push 0, dev/main 변경 0, 배포 0, 원격 DB 변경 0.
- 코드 커밋: Electron `d95c050`, Web API `36b049f`, Web Admin `01d0b93`, Infra `f0af3f5`. 모두 원격 통합 브랜치 push·로컬/원격 SHA 일치·clean.
- `.codex` 결과/인계 문서도 승인된 `main` push로 보존한다.
- 실제 ML/Build 5 전체 QA, Mac 공개·자동빌드·자동업데이트 HOLD 유지.
