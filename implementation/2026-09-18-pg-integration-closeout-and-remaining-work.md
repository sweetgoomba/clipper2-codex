# 정식 PG 통합 종료 감사와 남은 작업

날짜: 2026-09-18 KST

판정: **개발환경 PG 통합·DB 전환·독립 개발판 Windows 0.0.35 게시는 완료. 실제 결제/유료 작업 전체 E2E와 플랫폼별 설치·업데이트 검증은 별도 잔여 작업.**

이 문서는 여러 날짜의 계획·중간 체크포인트보다 우선하는 현재 정본이다. 과거 문서의 `미커밋`, `dev 미반영`, `Gate A 대기`, `Windows 빌드 전` 표현은 당시 이력으로만 읽는다.

## 1. 완료된 범위

### 소스 통합

- 8개 저장소의 정식 PG 통합 결과는 모두 원격 `dev`에 포함됐다. 2026-09-18 fresh fetch 뒤 각 `origin/integration/dev-pg-local-validation-20260917`이 `origin/dev`의 ancestor임을 확인했다.
- 현재 원격 `dev` HEAD:

| 저장소 | `origin/dev` |
| --- | --- |
| `clipper_angular` | `40d9096c3cb598e952b81532d81e0c929e9ae405` |
| `clipper_electron` | `3fca00b6a9e91ecb304333b45ca1f3443d4df7d1` |
| `clipper_nestjs` | `1adb62fc50119a96f22d3bc9ee62600588477dab` |
| `clipper_python` | `60417ce865499df519971650a43a7ca1a82d9867` |
| `clipper_infra` | `8adbfcdedb95fc0a56efcd7bb7154752c49b23f6` |
| `clipper_web_admin` | `bdcbae3b0d3fbb581506ba1686ed97dcefa9cfa4` |
| `clipper_web_api` | `9886f9681718b26ef4959aeab4e156bbb9fdaf5e` |
| `clipper_web_client` | `72829210ecbe2d56b61bfc132f2b6e7e886b933a` |

- 로컬 checkout은 모두 `dev`일 필요가 없다. 일부는 보존용 integration branch에 머물러 있지만 원격 `dev` 포함 여부와는 별개다. 이번 종료 감사에서는 원격 ancestry를 정본으로 사용한다.

### 개발 DB와 웹 서비스 전환

- cutover `dev-pg-20260918-035446`으로 Gate A–G를 완료했다.
- 기존 env·secret·실행 image와 User/Admin/Release DB dump를 보존한 뒤 User → Admin → Release migration 및 no-op 재실행을 완료했다.
- 사용자·세션·프로젝트·운영자/provider·release 데이터의 count+ID hash가 전후 일치했다.
- 승인된 출시 전 범위의 옛 finance/operation 데이터만 정리했고 새 plan·operation policy를 확인했다.
- 기존 사용자 20명에게 무료 체험을 소급하지 않았고, 신규 사용자는 Trial/400크레딧/30일을 한 번만 받았다.
- `/health`, catalog, Customer/Admin 외부 HTTPS, Google 로그인과 계정·이용권·크레딧 화면을 확인했다.
- stale `index.html`이 삭제된 JS를 가리키던 문제는 Customer/Admin Nginx cache 규칙으로 수정·재배포했고 사용자가 일반 새로고침·로그인·메뉴 이동을 재확인했다.

상세 증거는 [개발서버 PG 전환 실행 기록](2026-09-18-development-pg-cutover-execution-log.md)과 [전환 런북](2026-09-18-development-pg-cutover-runbook.md)에 있다.

### 독립 개발판

- 새 개발판 identity는 `Clipper Studio (dev)` / `ai.clipperstudio.dev` / `clipperstudio-dev://` / `Clipper Studio Dev` / update channel `dev`로 분리했다.
- 운영판은 `Clipper Studio` / `ai.clipperstudio.app` / `clipperstudio://` / `Clipper` / channel `stable`을 유지한다.
- macOS 로컬 실기에서 실제 Google 로그인, session 재실행, 로그아웃 유지, 재로그인, 무료체험 400, 계정·이용권·크레딧, 템플릿 17개 유지를 확인했다.
- 템플릿 export/import는 사용자 생성 템플릿만 내보내고 기본 16개 및 동일 사용자 템플릿을 중복 생성하지 않도록 수정했다. 프로젝트·소재관리·작업 이력 자동 이관은 사용자 결정으로 범위에서 제외했다.
- 옛 개발판의 일반 로그인을 다시 허용하는 서버 호환 보완 `9886f96`을 개발 API에 배포했고, API health와 세 DB 연결은 정상이다. 이는 옛 앱의 모든 신규 API 계약 호환을 보장하는 기능은 아니다.

### Release Coordinator와 Windows 0.0.35

- 빌드 채널 드롭다운을 제거하고 개발/운영 서버가 자신의 release target으로 build profile을 결정하도록 수정했다.
- 선택된 릴리즈와 다른 버전을 빌드하던 fallback을 제거했다. 실패한 Build 52는 감사 이력으로 보존했다.
- Windows runner는 job별 source/work/output 디렉터리를 사용하도록 분리했다. 공유 checkout의 `esbuild.exe` 잠금으로 실패한 경로를 더 이상 사용하지 않는다.
- runner image에 `desktop-build-profile.mjs`가 빠진 문제와 `builder-effective-config.yaml` 위치 가정을 보완하고, non-interactive Windows build 검증을 추가했다.
- `release/0.0.35`의 고정 source snapshot으로 Build 54, 산출물 버전 `0.0.35.54`, 설치 파일 `Clipper Studio (dev) Setup 0.0.35.exe` 빌드가 성공했다.
- 개발 관리자에서는 별도 게시 대상 선택 없이 서버가 정한 개발 정식 배포 대상으로 직접 게시하도록 복원했다.
- 2026-09-18 현재 공개 읽기 검증:
  - `https://dev-api.clipperstudio.ai/health`: API와 User/Admin/Release DB 모두 `ok`.
  - `https://dev-api.clipperstudio.ai/downloads/latest`: Windows x64 `0.0.35`, Build 54 설치 파일을 반환.
  - `https://dev-api.clipperstudio.ai/releases/updates/dev/windows/x64/latest.yml`: version `0.0.35`와 같은 Build 54 파일을 반환.
- 처음 다운로드 페이지가 0.0.31을 반환한 문제는 환경별 정식 게시 대상을 조회하도록 API를 보완한 뒤 해소됐다. API 재배포 직후의 502는 앱 기동 전 요청이었고, 같은 컨테이너가 재시작 없이 정상 기동한 뒤 내부·외부 health 200을 확인했다.

## 2. 0.0.35에 포함된 source와 이후 변경의 경계

`release/0.0.35`는 릴리즈 생성 시점의 source를 고정한 브랜치다.

| 빌드 source | `release/0.0.35` |
| --- | --- |
| Angular | `428ed1f95483a3b7dd7a534360ed7e8259043fb2` |
| Electron | `3fca00b6a9e91ecb304333b45ca1f3443d4df7d1` |
| NestJS | `1adb62fc50119a96f22d3bc9ee62600588477dab` |
| Python | `60417ce865499df519971650a43a7ca1a82d9867` |
| Runtime Web API snapshot | `eeab27d2673e5f5a4cfbd1b63b2292d4b8d6edd8` |

- 이후의 Angular 홈 카드 변경과 이번 `BlockingProgress` 변경은 0.0.35에 포함되지 않는다.
- 현재 개발 API에는 release snapshot 이후 다운로드 대상 수정과 옛 개발판 로그인 허용 보완까지 배포됐다. 데스크톱 릴리즈 source와 서버 runtime source가 반드시 같은 SHA일 필요는 없지만, 이 차이를 릴리즈 이력에서 숨기지 않는다.
- 0.0.34는 사용하지 않기로 했지만 관리자 DB에서 실제 `폐기` 처리됐는지는 확인하지 않았다. Build 52/53 실패 이력을 삭제하거나 고쳐 쓰지 않는다.

## 3. 지금 남은 필수 확인

다음 항목은 완료 증거가 없으므로 자동으로 완료 처리하지 않는다.

### A. 설치형 앱 수용 테스트

1. 다른 Windows PC에서 공개 페이지가 내려주는 **0.0.35 설치 파일**을 새로 다운로드하고 설치한다.
2. 설치 후 표시명, 실행 파일, Google 로그인 복귀, 운영판과 동시 설치·실행, 분리된 데이터 경로를 확인한다.
3. 이미 설치된 옛 개발판이 있는 Windows에서 새 개발판 설치·실행·제거가 서로 영향을 주지 않는지 확인한다.
4. 개발 updater가 `dev` feed의 0.0.35를 읽는 것은 확인했지만, 실제 구버전 → 0.0.35 자동 업데이트 설치 실기는 별도다.
5. macOS는 로컬 빌드 실기는 통과했지만 공개된 서명·공증 DMG/업데이트 산출물이 없다. 다른 Mac 사용자에게 배포하려면 서명·공증·설치·로그인 복귀를 별도로 확인해야 한다.

### B. 전환된 개발환경의 실제 PG E2E

1. 테스트 카드 등록과 최초 월/연 구독.
2. 추가 크레딧 구매, 요금제 즉시/예약 변경, 카드 변경, 해지·재개, 갱신 성공·실패·재시도.
3. webhook 수신·중복·순서 역전·재전송과 reconcile.
4. 관리자 환불과 외부 취소 성공/실패 뒤 access·credit·ledger·결제내역 일치.

과거 로컬/심사/운영 테스트 증거는 유효하지만, 이번에 전환한 개발 DB와 현재 배포 조합의 실제 카드 E2E를 대신하지 않는다.

### C. 유료 operation 실제 E2E

1. Shortform 3경로, Dance, Dialog 각 50크레딧과 Variation 영상당 20크레딧 차감.
2. 성공, 제출 전 실패, 실행 실패, 취소, 프로젝트 삭제, 재시도에서 정확히 한 번 차감·필요 시 환급.
3. 앱/로컬 API 재시작, outbox replay, 장시간 `preparing`/`running` 복구.
4. 실제 ML plugin과 생성 산출물 확인. 이 항목과 Build 5 전체 QA는 계속 HOLD이며 별도 실행 승인이 필요하다.

### D. 전환 후 관찰

- 전용 30–60분 API 로그 관찰 결과가 아직 없다. onboarding 재시도, 5xx, 결제/webhook/reconcile, operation 장기 실행·환급 outbox 이상을 비밀값 없이 점검한다.
- cutover backup에는 DB dump와 env/secret archive가 포함돼 있다. 접근권한을 유지하고, 보관 기한·암호화·안전한 폐기 시점을 별도로 결정한다. 채팅이나 Git에 내용을 복사하지 않는다.

## 4. 확인된 후속 결함·미완료 UX

- Angular 유료 작업의 과금 확인창 전후 대기 동안 화면이 다시 조작되던 문제는 공용 전체 화면 스피너로 수정했고, 사용자 숏폼 실기 뒤 크기를 `40px/3px`로 축소했다. Angular feature branch `feature/billable-operation-blocking-progress-20260918`에 `58eafe60`까지 push했고 관련 452 tests와 production build를 통과했다. 0.0.35에는 포함되지 않으며 dev merge·앱 재릴리즈 및 숏폼 외 진입점 수동 확인은 아직 남았다.
- 크레딧의 잘못된 `300 / 300`, `보류 0` 표시는 Desktop Angular에서 제거했고, Web API가 현재 무료 체험/이용권 혜택을 `currentBenefit`으로 제공하도록 구현했다. 이후 실기에서 Desktop NestJS의 허용 목록 투영이 새 필드를 제거하는 계층 누락을 발견했다. 별도 `fix/desktop-credit-summary-proxy-20260918` 작업공간에서 유효 필드 전달, 구버전 Web API의 필드 부재/null 호환, 잘못된 variant 거부 테스트와 보완을 완료했으며 아직 커밋·dev 반영·앱 재빌드는 하지 않았다. 상세 원인과 호환 행렬은 [데스크톱 크레딧 잔액 표시 후속](2026-09-18-desktop-credit-balance-presentation-followup.md)에 기록했다.
- Release 페이지에서 새 릴리즈 생성 후 버전·브랜치·릴리즈 노트 입력값이 그대로 남는 UI 문제는 사용자가 나중에 수정하기로 했고 현재 미수정이다.
- 옛 개발판 로그인 차단은 서버에서 해제했지만 `9886f96` 배포 뒤 실제 옛 앱 Google 로그인을 다시 시도한 사용자 확인 기록은 없다. 로그인 허용은 옛 앱의 전체 API 호환 보장이 아니므로 편집/다운로드 등은 각 계약 차이로 실패할 수 있다.
- API 배포 직후 health가 준비되기 전에 외부 요청하면 일시 502가 발생한다. 현재 서비스 장애는 아니지만 `deploy-dev.sh`가 application readiness 완료까지 기다리지 않는 운영 UX는 필요하면 별도 개선한다.

## 5. 의도적으로 하지 않는 일

- 프로젝트·소재관리·작업 이력의 자동 이관.
- 옛 앱 자동 탐색·삭제 또는 사용자 PC의 LaunchServices 전체 초기화.
- macOS 자동 업데이트 활성화. 현재 비활성은 결함이 아니라 승인된 HOLD다.
- 0.0.35의 고정 snapshot을 최신 `dev`로 조용히 바꾸거나 실패 Build 이력을 수정하는 일.
- 실제 ML/Build 5를 별도 승인 없이 실행하는 일.

## 6. 종료 판정

다른 팀에 새 개발판 사용을 안내할 수 있는 핵심 전환은 완료됐다. 다만 이 판정은 “모든 결제·환불·ML·설치·자동 업데이트 시나리오가 끝났다”는 뜻이 아니다. 다음 실무 우선순위는 다음과 같다.

1. Windows 0.0.35 공개 설치본의 설치·로그인·운영판 공존 확인.
2. 이번 `BlockingProgress` 후속 변경의 수동 UX 확인과 dev 반영 여부 결정.
3. 전환된 개발환경에서 테스트 카드 기반 PG 핵심 E2E.
4. 실제 유료 operation 차감·환급 E2E와 30–60분 로그 관찰.
5. 필요할 때 macOS 서명·공증 배포와 자동 업데이트 정책을 별도 프로젝트로 재개.
