# 운영·개발 앱 표시 이름

## 최신 결과: 새 macOS 개발판·필수 템플릿 이관 PASS

새 개발판 `Clipper Studio (dev).app`의 `ai.clipperstudio.dev` / `clipperstudio-dev` identity와 실제 Google 로그인, 무료 체험 400, 계정/access/credit 표시를 사용자 확인했다. 필수 템플릿 이관에서는 옛 번들에 함께 들어간 기본 제공 16개가 사용자 복사본으로 중복되는 결함을 발견했다. 내보내기 UI/backend는 사용자 생성 항목만 허용하고 importer는 옛 format v1을 포함해 canonical 기본 제공 템플릿과 그 전용 font를 건너뛰도록 수정했다.

잘못 생긴 로컬 복제본 16개만 백업 후 정상 API로 삭제했고 사용자 템플릿은 보존했다. 같은 17개 번들을 재가져온 뒤 기본16+사용자1=총17, 복제본0, 내보내기 사용자 항목1만 표시를 사용자 UI와 로컬 API에서 확인했다. Angular `19b407a7`, Nest `884fa8bc`에 로컬 커밋했으며 각 원격 통합 브랜치보다 1커밋 앞선 clean 상태다. [상세 구현·실기·검증](../../implementation/2026-09-17-template-transfer-dedup-validation.md). 코드 push·추가 병합·dev/main 변경·배포·원격 DB 변경은 없다.

Mac 필수 템플릿 이관은 완료했다. 2026-09-18 사용자 결정으로 소재관리·프로젝트·작업 이력의 복제/자동 이관은 구현하지 않는다. 옛 데이터 루트는 삭제·수정하지 않고 보존하지만 새 개발판과 공유하지 않는다. 같은 날 로그인 상태 재실행 유지, 로그아웃 상태 재실행 유지, Google 재로그인과 동일 계정·무료 체험·크레딧400·템플릿17 복원까지 사용자 확인했다. 남은 W09 항목은 Windows 실제 installer/identity/template 실기다. Mac 공개·자동 업데이트, 실제 ML, Build5 전체 QA HOLD를 유지한다. 아래의 “템플릿 실기 남음”, 옛 identity/데이터 경로 보존, 코드 미커밋 표현은 과거 체크포인트다.

## 최신 사용자 요구: 독립 개발판 전환 (아래 identity 보존 방침보다 우선)

최신 재개 지점: 사용자 로컬 Mac 실행 승인 후 새 DB `clipper-identity-check-20260917-*` (58433–58435) 생성·migration·실제 DB **9 PASS**. 새 컨테이너 정상 중지/볼륨 보존, 기존 5433–5435/57433–57435 및 실 env/원격 서버 변경 없음. [실제 DB 검증 결과·남은 실기](../../implementation/2026-09-17-independent-dev-real-db-validation.md). 다음은 실제 앱용 로컬 환경 설정 범위 확인 후 재패키징/Google/공존/필수 템플릿 이관. 아래 DB 미실행 표현은 이전 단계.

- 새 개발판은 백지 상태로 시작해도 된다. 기존 개발판을 덮어쓰거나 같은 데이터 경로를 유지하는 것은 필수가 아니다. 옛 앱이 남아 있어도 새 앱의 로그인 연결을 방해해서는 안 된다. 옛 앱 탐색/삭제나 lsregister 수동 실행을 정상 로그인 전제로 삼지 않는다.
- 운영판과 새 개발판은 macOS/Windows 한 PC에서 동시 설치·실행 필수. 데이터 경로 등 가변 상태는 분리. 운영 표시명은 Clipper Studio, 개발 표시는 Clipper Studio (dev).
- 템플릿 이관은 필수이며 실제 옛 배포본→새 앱의 자산/폰트/레이아웃 보존까지 검증 완료했다. 소재관리·프로젝트·작업 이력은 조사 후 이관하지 않기로 최종 결정했다.
- 직원에게 필요한 자료를 보관한 뒤 옛 개발판 사용 중단/삭제를 공지할 수 있다. 하지만 공지 이행이나 모든 옛 사본 발견 여부에 안전성을 의존하지 않는다.
- 사용자 설정안 동의: 새 개발판 appId `ai.clipperstudio.dev`, protocol `clipperstudio-dev`, 데이터 루트 `Clipper Studio Dev`, 업데이트 채널 `dev`. 표시명 `Clipper Studio (dev)`. 운영은 `ai.clipperstudio.app` / `clipperstudio` / `Clipper` / `stable` / 표시명 `Clipper Studio`.
- [선택된 값·실제 코드 차이·연결 변경안](../../implementation/2026-09-17-independent-dev-identity-design.md)에 Mac/Windows 업데이트 URL과 검증 게이트를 기록했다. 로그인 target 구분, 관리자 stable 고정 해소, 서버 오게시 차단, runner 환경 전달이 추가로 필요하다. 설정값 동의와 이 상세 구현 범위의 승인을 구분한다.
- 사용자는 연결 변경 범위에도 동의했다. [앱·로그인 실행 계획](../../implementation/2026-09-17-independent-dev-app-plan.md), [채널·runner·관리자 실행 계획](../../implementation/2026-09-17-independent-dev-release-plan.md) 작성 완료. auth 요청 결속 및 artifact profile 기록용 nullable 컬럼 migration은 계획만 있으며 실행하지 않았다.
- M1 정정: Mac 공개·자동빌드·자동 업데이트는 기존 사용자 결정대로 HOLD. ZIP 요구는 이미 9/9 기록에 있던 사실이며 신규 필수 확장으로 제시한 것이 잘못이었다. 현재 원본 Mac 앱의 autoUpdateDisabled=true 확인. Mac 전역 차단 분기는 없으므로 모든 배포본 비활성까지 확인한 것은 아님. ZIP 지원은 이번 범위 제외, 앱 분리의 차단 게이트 아님.
- 2026-09-17 실행 체크포인트: 원본 Electron 통합 브랜치(HEAD `6766c06`) 위 Task 1–2 코드 기반 구현, 새 dev identity/데이터·캐시·로그/update profile 반영, build 및 **963/963 PASS**. **미커밋**. [상세 결과](../../implementation/2026-09-17-independent-dev-app-validation.md). 새 Mac 코드에는 전역 Darwin auto-update 차단과 빌드 disabled flag를 반영했지만 설치본을 재빌드/기동하지 않았다. 과거 설치본 상태와 구분한다.
- 2026-09-17 다음 체크포인트: Task 3–4 서버 target/서명 state/S256/원자적 code 소비 + Electron pending 요청 결속 코드 연결. Web API build/2,845 PASS/21 SKIP, Electron build/975 PASS. 독립 리뷰에서 cold-start 안내 누락을 찾아 native retry dialog로 보완. 상세 검증/한계는 위 실행 결과 문서 참조. Electron/Web API/.codex 미커밋.
- 2026-09-17 최신 체크포인트: release Task 1–3 코드·자동 검증 완료. API build/2,882 PASS·21 SKIP, Infra 51 PASS·1 SKIP, Admin build/50 PASS. 독립 리뷰의 job/build 잠금 순서 및 runner CLI 플랫폼 검증 지적 수정 후 추가 중요 지적 없음. [릴리스 검증 결과](../../implementation/2026-09-17-independent-dev-release-validation.md). API/Infra/Admin/Electron 선행 변경과 문서는 모두 미커밋이다.
- 다음은 새 격리 DB의 정확한 대상·영향을 제시하고 별도 승인받아 User 로그인 binding/Release artifact profile migration 및 실제 트랜잭션을 검증하는 것이다. 그 뒤 새 설치본 Google 로그인/동시 실행/필수 템플릿 이관을 검증한다. 실제 `.env`에는 아직 DESKTOP_AUTH_TARGET/RELEASE_TARGET을 적용하지 않았다. 실 환경파일·DB·앱 패키징/실행·커밋·푸시·병합·배포 변경 없음. Windows 실기는 사용자 장비. 주간 잔여 96% 기록, reset credit 사용 없음. 아래 identity 보존/clean/옛 worktree 경로는 역사 기록이다.

## 2026-09-17 사용자 실제 Google 로그인 후속 (아래 과거 상태보다 우선)

원본 checkout의 새 개발 빌드에서 실제 Google 로그인·무료 체험 400 표시를 사용자 확인. macOS 기본 `clipper://` 핸들러가 /Applications의 옛 개발 앱이었음을 조회하고 옛 앱/이전 worktree 등록만 해제, 원본 새 개발 앱 재등록 후 사용자 재로그인 확인창 이름까지 정상 확인했다. 앱 파일·데이터 삭제 없음. 이 로컬 조치는 배포 업그레이드 해결책이 아니며, 파일명 변경으로 인한 구·신 개발 앱 공존과 콜백 대상 문제는 배포 전 설계/실기 잔여 항목이다. [조회 명령·실행 이력·배포 잔여 과제](../../implementation/2026-09-17-macos-dev-oauth-handler-validation.md) 참조. Windows NSIS·서명/공증·DMG 업그레이드 실기는 여전히 대기.

최종 확인: 2026-09-18 KST. 상태: **독립 개발 identity 적용 / 실제 Google OAuth·session 재실행·로그아웃·재로그인·무료체험·필수 템플릿 이관 PASS / Windows NSIS 실기 대기 / 프로젝트·소재·작업 이력 이관 제외**.

[전체 현황](../WORKBOARD.md)

## 목표·범위

통합판의 운영 앱은 macOS·Windows 모두 `Clipper Studio`, 개발 앱은 macOS·Windows 모두 `Clipper Studio (dev)`로 구분한다. 설치파일도 같은 이름을 사용한다. 운영은 `appId=ai.clipperstudio.app`, protocol `clipperstudio://`, `Application Support/Clipper`; 개발은 `appId=ai.clipperstudio.dev`, protocol `clipperstudio-dev://`, `Application Support/Clipper Studio Dev`로 분리한다. 두 앱은 로그인·데이터·업데이트 identity를 공유하지 않는다.

사용자는 2026-09-16 기존 운영 macOS 앱이 정식 배포된 적 없고 본인 테스트 설치만 있었으므로 옛 `Clipper.app`과의 공존 문제는 고려하지 않아도 된다고 확정했다. 운영 macOS 설치 앱 이름을 `Clipper.app`으로 유지하는 안은 명시적으로 거부했으며, 목표는 `Clipper Studio.app`이다.

사용자는 운영·개발 macOS 앱 동시 설치를 전제로 개발 설치 앱을 `Clipper Studio (dev).app`으로 분리하는 안에 동의했다. Windows도 같은 운영/개발 이름 규칙을 적용하는 것이 요구사항이다.

## 현재 상태·중단 지점

2026-09-18 검증에서 독립 개발판 설계·`package-lock.json`·테스트는 root package name `clipper-studio-dev`를 요구하지만 실제 `package.json`만 `clipper-electron`으로 남아 있음을 발견했다. 이대로면 Windows updater cache가 옛 개발판의 `clipper-electron-updater`와 겹칠 수 있다. 기존 실패 테스트 2건을 재현한 뒤 `package.json` 한 줄만 `clipper-studio-dev`로 보완했고 Electron build·전체 975 PASS를 확인했다. dependency/version 변경 없음. 후속 승인으로 독립 개발판 전체 변경은 Electron `d95c050`, Web API `36b049f`, Web Admin `01d0b93`, Infra `f0af3f5`에 커밋하고 각 원격 통합 브랜치에 push했다. 네 저장소는 로컬/원격 SHA 일치·clean이고, 새 병합·배포는 없다. [검증 상세](../../implementation/2026-09-18-w04-non-ml-local-acceptance.md).

같은 날 후속 리뷰에서 운영 package/cache의 과거 내부명 `clipper` / `clipper-updater`도 공개 배포 전 정리하기로 사용자가 승인했다. 최종 계약은 개발 `clipper-studio-dev` / `clipper-studio-dev-updater`, 운영 `clipper-studio` / `clipper-studio-updater`다. Web API는 Windows/x64 보고가 exe인지, macOS/arm64 보고가 dmg인지 성공 저장 전에 검사한다. Infra runner는 Windows 최종 `app-update.yml`의 정확한 feed/cache와 effective package name을 업로드 전에 검사한다. 후속 검증은 Electron build·전체 975, Web API build·전체 2,884 PASS(21 SKIP), Web Admin build·전체 571 PASS, Infra 전체 36 PASS다. 실제 Windows EXE/NSIS 설치 실기는 아직 사용자 Windows 장비에서 수행해야 한다.

사용자 승인 후 Electron `6766c0645d8151eac1ea075e08f89871cb4ad4df`, Nest `fda1eda586fe2b80a444691303fb1e52fef57a34`에 보완을 로컬 커밋했다. fresh build와 Electron955/Nest2,678 테스트 PASS, 두 worktree clean이다. [커밋 결과](../../implementation/2026-09-17-integration-commit-proposal.md)가 아래 커밋 전 기록의 미커밋/옛 HEAD 표현보다 우선한다. 코드 push·추가 병합·원본 dev 변경·배포는 없다.

### 커밋 전 조사·검증 기록

최신 [Astra 수정 결과](../../implementation/2026-09-17-astra-fix-result.md)에서 R06 spawn 이후 PID/identity 확보와 R07 Nest/Electron 자식 identity 계약을 수정했다. Electron 전체 955/955 및 build, 실제 일회용 Nest writer→Electron cleanup 프로세스 회귀가 통과했다. 실제 설치형 앱 crash/Windows 전체 실기를 대신하는 것은 아니다. 이번 변경은 Electron/Nest 미커밋 상태이며 이름·환경별 appId/protocol/data path는 변경하지 않았다.

2026-09-17 현재 Electron 통합 HEAD는 `827fcda8b12a34232c2574983afff6284b69d949`이다(이전 전체 SHA 오기 정정). formal-PG, 앱 이름 2커밋, child-process 종료 보완과 환경별 identity 복구를 포함하고, 그 위에 이번 R06/R07 수정이 미커밋으로 남아 있다. 이전 macOS arm64 local-api 개발 `Clipper Studio (dev).app` 생성·실행 증거는 보존하되 이번 수정본의 패키지 실기로 재사용하지 않는다. Windows NSIS 실제 설치파일은 arm64 Mac에서 x64 `makensis` 실행이 OS error `-86`으로 막혔으므로 사용자가 Windows 서버에서 확인한다. 이름 계약 테스트는 개발 `Clipper Studio (dev) Setup`, 운영 `Clipper Studio Setup`을 통과했다. push·배포는 하지 않았다.

기존 보존 커밋 위에 후속 로컬 구현을 완료했다. 운영은 `Clipper Studio.app`/`Clipper Studio.dmg`와 `Clipper Studio Setup ${version}.exe`, 개발은 `Clipper Studio (dev).app`/`Clipper Studio (dev).dmg`와 `Clipper Studio (dev) Setup ${version}.exe`를 사용한다. Windows 설치 후 실행파일·바로가기 표시도 builder `productName`을 따라 각각 구분된다. 로그인 화면은 기존 AppInfo 연결을 그대로 사용하므로 Angular 변경 없이 런타임 표시명을 따른다.

후속 수정은 개발 base `productName=Clipper Studio (dev)`, 운영 생성 config `productName=Clipper Studio`로 바꿨다. `1930ad4`가 운영 identity를 개발 identity로 잘못 통일한 결함은 사용자 지적 뒤 `827fcda`에서 바로잡았다. 최종 테스트는 위 환경별 appId·protocol·data path가 각각 유지되는 계약을 고정한다.

이후 재감사에서 `applyDesktopIdentity()`가 시작 초기에 `app.setName()`을 바꾸기 때문에 macOS `safeStorage`의 기존 Keychain 항목으로 암호화된 `auth.bin`을 새 이름의 앱이 복호화하지 못할 수 있음을 확인했다. 사용자는 2026-09-16 새 앱에서 1회 재로그인하면 되므로 기존 Keychain session을 보존하거나 migration하지 않아도 된다고 결정했다. 사용자 계정·프로젝트·설정 데이터 경로는 그대로 보존하고, 새 앱이 복호화 실패를 로그인 없음으로 안전하게 처리한 뒤 로그인 완료 시 새 이름의 Keychain identity로 `auth.bin`을 덮어쓰는 흐름을 검증한다.

최초 구현 `99444d8`, 후속 패키지 이름 변경 `7aed9f6`은 이력으로 보존한다. 현재 통합 결과에 이미 포함됐으므로 다시 merge/cherry-pick하지 않는다. push·배포는 하지 않았다.

## 작업 공간

- 현재 branch: `integration/dev-pg-local-validation-20260917`.
- 현재 worktree: `/Users/jina/project/adlight/.worktrees/dev-pg-local-validation-20260917/desktop/clipper_electron`.
- 현재 HEAD: `6766c0645d8151eac1ea075e08f89871cb4ad4df`, R06/R07 수정 로컬 커밋 완료, clean.
- 옛 feature worktree는 이력 보존용이며 현재 정본이 아니다. 원본 checkout과 다른 작업 worktree는 변경하지 않았다.

## 이전 패키징·실행 검증 기록

- 기존 TDD RED 기록 유지.
- 2026-09-16 커밋 직전 Node `v24.3.0`, TypeScript `npm run build`: PASS.
- 전체 Electron `npm test`: **950 PASS, 0 FAIL**.
- builder 이름과 운영·개발 각각의 기존 appId/protocol/data path·업데이트·캐시 구조 보존 계약 PASS.
- macOS arm64 local-api `Clipper Studio (dev).app` 실제 생성·실행 PASS.
- 실제 실행에서 표시명, 로그인 화면, 옛 토큰 복호화 실패의 안전한 로그아웃 처리, 검증용 일회성 desktop auth code를 통한 session 설정, 프로젝트/Variation/설정 진입과 access·credit 표시를 확인했다. 격리 API에는 Google OAuth client ID/secret을 넣지 않았으므로 실제 Google OAuth 브라우저 재로그인은 확인하지 않았다.
- 앱 종료 시 Nest child process가 exit code 0, intentional shutdown으로 끝나고 관련 프로세스가 남지 않음을 확인했다.

## 다음 행동

앱 이름 커밋은 이미 승인된 통합에 포함됐고 R06/R07 수정·회귀도 위 최신 기록대로 통과했다. 새 수정본의 session 재실행·로그아웃 실기, Windows 서버의 NSIS 실물 설치·업그레이드와 배포 전 서명·공증 smoke는 남아 있다. 운영·개발은 서로 다른 appId·protocol·데이터 경로와 표시명을 유지하므로 독립 설치 대상으로 다룬다. 옛 개발판 프로젝트·소재·작업 이력은 새 개발판으로 가져오지 않는다.

macOS 새 개발판 자체의 session 수명주기는 다음과 같이 확인 완료했다.

1. 로그인 상태 앱 완전 종료·재실행: 동일 계정, access, 크레딧 400, 템플릿 17개 유지 PASS.
2. 로그아웃 후 앱 완전 종료·재실행: 로그인 화면 유지 PASS.
3. Google 재로그인: 연결창 `Clipper Studio (dev).app`, 동일 계정·access·크레딧·템플릿 복원 PASS.
4. 운영판과 새 개발판의 동시 설치·실행, 각 protocol 딥링크, 분리된 데이터 경로는 별도 실기로 남는다.
5. 실제 서명·공증·DMG 및 Windows NSIS 실기는 배포 전 별도 게이트로 유지한다.

옛 개발판 데이터 이어받기는 더 이상 smoke 항목이 아니다. 옛 앱 데이터는 보존만 하며 새 앱에서 읽거나 수정하지 않는다.

## 제약·미확인

- Windows 설치/업데이트와 운영 배포는 미실행. Windows는 사용자가 Windows 서버에서 직접 검증한다.
- 운영 appId/protocol/data path는 `ai.clipperstudio.app` / `clipperstudio` / `Clipper`, 새 개발판은 `ai.clipperstudio.dev` / `clipperstudio-dev` / `Clipper Studio Dev`로 분리한다. macOS 개발판의 옛 암호화 로그인 session은 보존 대상에서 제외하고 1회 재로그인을 허용한다.
- 실제 ML 플러그인 실행과 Build 5 전체 QA HOLD 유지. 서버 직접 접속 없음.

## 상세 근거

- [2026-09-16 세션 기록](../../records/sessions/2026/09/16.md)
- [통합 결과](../../implementation/2026-09-15-main-integration-result.md)
