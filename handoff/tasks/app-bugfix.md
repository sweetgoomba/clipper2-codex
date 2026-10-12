# W10 — 공통 버그・UI 문구・기획 보정

최종 확인: 2026-09-30 KST. 상태: **9/29 W10 변경은 Angular/Electron dev 반영·worktree 정리 완료. 9/30 W10-11도 Angular dev 병합·원격 푸시 및 격리 worktree 정리 완료.**

[전체 현황](../WORKBOARD.md) · [새 세션 프롬프트](../prompts/2026-09-29-new-sessions.md)

## 목표·범위

사용자가 앱을 실행·테스트하며 발견한 공통 버그, 버튼/안내 문구의 어색함, 기획상 흐름·상태·동작 보정. 버그 여부와 관계없이 사용자가 제시한 문제를 다룬다. 특정 플러그인의 전문 로직은 해당 카드로 연결한다.

## 현재 상태

사용자가 6개 증상을 한 번에 전달했다. W10-01~06 및 후속 모델 파일 정리/UI 보완을 구현하고 Angular/Electron 원격 dev에 반영했다. 작업 공간은 정리됐으며 [종료 기록·현재 재빌드 경로](../../implementation/2026-09-29-app-bugfix-closeout.md)를 따른다. 아래 착수/개발 문단은 당시 이력이다. 3·4·5번은 이번에 직접 전달한 UI 증상만 다뤘으며, 특정 플러그인의 전문 개선이나 W07/W11/W12의 광범위 후속 작업은 재개하지 않았다.

9/30 추가 증상 `a.zip` 반복 생성은 아래 W10-11에 별도 기록했다. Angular dev에 반영됐다.

이번 대화에서 확인된 빌드 관련 후보:

- 기존 linked worktree에서 Electron 패키징 시 Python의 `.git` **파일**이 앱 `Contents/Resources/clipper_python`에 복사됐다. `electron-builder.yml`의 `!**/.git/**`는 이 파일을 제외하지 못한다. VS Code가 패키징 복사본을 같은 Git 저장소로 인식해 삭제106건(테스트105 + `.env.example`1)을 표시했다. 원본 소스 삭제는 아니었다.
- 해당 구 산출물은 storyboard worktree 제거로 삭제됐다. **빌드 필터 자체 수정은 아직 하지 않았다.** 공통 버그 세션에서 선택해 재발 방지를 수정할 수 있다.
- 원본 Nest의 pdfkit 설치 누락은 의존성 동기화 문제였다. `npm ci --include=dev`와 bundle/앱 재빌드 명령을 안내했으며 성공 결과는 미보고다. 소스 버그로 단정하지 않는다.

## 2026-09-29 — 세션 착수·읽기 전용 조사

- 사용자 개별 증상은 아직 미수신. 기존 패키징 `.git` 복사·pdfkit 의존성 후보는 자동 수정하지 않았다.
- 원본 8repo 모두 `dev`·tracked/untracked clean·로컬 `origin/dev`와 0/0을 재확인했다. HEAD는 [오늘 기록의 Git 기준선](../../records/sessions/2026/09/29.md)과 동일하다. 이번 준비에서도 fetch하지 않았으므로 원격 최신성을 보증하지 않는다.
- 기존 worktree 등록을 읽기만 했다. 다른 세션의 checkout/branch/worktree·미커밋 작업은 변경하지 않았다. 새 브랜치·worktree는 실제 수정 대상이 정해지면 해당 repo만 fetch한 최신 `origin/dev`에서 준비한다.

### 공통 증상 추적 경로

| 영역 | 실제 코드 진입점 |
|---|---|
| 화면·라우팅·공통 셸 | Angular `src/app/app.routes.ts`, `app.config.ts`, `src/shell/`, `src/core/navigation/` |
| 한글·비동기 입력 | Angular `src/shared/forms/edit-buffer.ts`, `ime-enter.directive.ts`, `editable-text.directive.ts` |
| 안내 문구·오류·반복 알림 | Angular `src/core/errors/error-catalog.ts`, `error-notification.service.ts`, `unhandled-error-policy.service.ts`, `src/shared/ui/` |
| 실행 모드·백엔드 주소 | Angular `src/core/bridge/backend-locator.ts` → Electron `src/preload/preload.ts` → `src/main/backend/backend-ipc.ts`. local은 기본 `127.0.0.1:9019/v1`, devapp은 IPC로 개발 주소, packaged는 NestManager가 시작한 동적 포트 |
| 상태·진행 이벤트 | Angular `src/core/bridge/realtime-event.service.ts` ↔ Nest `src/core/realtime/realtime-gateway.service.ts`; Nest `src/modules/jobs/`, `operations/` |
| 로그·trace | Angular `src/core/logging/`, `src/shell/settings/logs/` → Electron `src/main/logs-ipc.ts`; Nest `src/core/logging/`, `src/core/errors/all-exceptions.filter.ts`. 현재 `main.ts`에 trace middleware·예외 filter 등록이 있음 |
| 파일 선택·앱 셸·패키징 | Electron `src/shared/ipc-contract.ts`, `src/main/dialog-ipc.ts`, `electron-builder.yml`, `scripts/build-app.mjs` |

### 증상별 처리·검증 기준

- W10-01부터 접수 순서대로 화면/실행 모드/재현 순서/현재 동작/기대 동작을 기록한다. 최초 재현, 원인, 수정 파일, 회귀 검증 결과, 사용자 화면 확인 대기를 분리한다.
- 특정 플러그인의 전문 로직과 기존 W07/W11/W12 등 후속 범위는 해당 카드·세션으로 연결하고 중복 수정하지 않는다.
- Angular: 대상 spec을 `npx ng test --watch=false --browsers=ChromeHeadless --include='<대상 spec>'`로 실행(Karma 동시 실행 금지), 관련 스타일은 `npm run test:styles`, 해당 모드 빌드·화면 스모크 확인. `npm test -- --watch=false`는 사용하지 않는다.
- Nest: `npm run build` 후 `node --test test/<대상>.test.js`. Electron: `npm run build` 및 관련 `node --test` 테스트. 실제 입력·IPC·화면 동작은 해당 실행 모드에서 별도 확인한다. Python 공통 SDK가 원인일 때만 Python repo를 추가한다.
- 이번 준비는 소스·설정 읽기와 Git 상태 확인만 수행했다. 제품 코드 수정, 의존성 설치, 서버/앱 실행, 빌드/테스트, ML/실결제, commit/push/배포는 실행하지 않았다. 따라서 버그 해결·빌드 성공을 주장하지 않는다.

## W10-01~06 — 접수·원인·수정 결과 (2026-09-29)

공통 상태: **원격 dev 반영/작업 공간 정리 완료. 모델 취소 사용자 실기 확인, 다른 미보고 실기는 실제 확인 대기**. 아래는 사용자 관측과 코드/테스트로 재현한 사실을 구분한 기록이다.

| ID | 사용자 증상 | 확인한 원인·수정 | 회귀 검증 |
|---|---|---|---|
| W10-01 | 첫 설치에서 다운로드 모달 취소 후 버튼·카드가 설치 중으로 남음 | consent cancel이 다운로드 서비스만 reset하고 Store의 `_pendingPlugin`/`_pendingItem`을 남김. ffmpeg·model consent에 `cancelled` 출력을 연결하고 Store가 소유 상태를 해제 | 실제 모달 취소 버튼 클릭 → 카드/설치 버튼 복원 → 재설치 시 새 동의 모달. ffmpeg 완료 뒤 model 취소도 포함 |
| W10-02 | 실패한 작업 카드에 결과 보기 버튼 표시 | 묶음 실패 카드에 산출물 유무와 무관하게 open 액션을 생성함. 산출물이 없는 실패에는 retry/delete만 표시. 일부 결과는 묶음 전체에서 확인하여 접근 유지 | 안무·대사·베리에이션의 빈 실패, 실제 부분 결과, 이전 부분 결과 + 최신 빈 실패. 최신 대표 잡의 제목/재시도 대상 보존 |
| W10-03 | 숏폼 대본 삭제 후 해당 클립·미리보기 전체 시간이 그대로 | 삭제 경로가 자막 배열만 줄이고 `durationMs`와 `mediaSlots`를 유지함. 기존 길이 계산과 슬롯 비례 압축 helper를 함께 적용 | 5초에서 4초 자막 삭제 → 클립 1초, 다음 2초 클립 포함 전체 3초. 다중 슬롯 `[0,2000],[2000,5000]` → `[0,400],[400,1000]`, 오래된 슬롯이 미리보기를 늘리지 않음 |
| W10-04 | 스토리보드 구성에서 일부 대본 버튼이 빈 텍스트 | 폭 18% 미만인 칸을 의도적으로 빈 문자열로 렌더함. 항상 `대본 N`을 표시하고 라벨 최소 폭 + 구성 막대 내부 가로 스크롤 적용 | 1% 길이 칸, 210px 폭의 동일 길이 대본 6개에서 실제 텍스트 bounds·버튼 안 표시·스크롤 접근·선택 확인 |
| W10-05 | 안무 전체 다운로드의 ZIP 내용이 불명확하고 프로젝트 삭제와 나란함 | 최종 확정 `모든 클립 다운로드` + tooltip `모든 인물의 전체 클립을 인물별 폴더로 묶어 다운로드합니다.` 적용. 사용자 요청대로 기존 헤더의 프로젝트 삭제 옆 위치 유지. 대사 화면·ZIP 생성 API/저장 동작 유지 | 최종 문구/기존 헤더·ZIP 비활성/준비/다운로드 회귀 88·스타일6 성공. 최신 기존 앱에 문구/tooltip 포함 확인, 사용자 hover 실기 미보고 |
| W10-06 | 로그 소스 칩 선택/해제가 다른 칩까지 바뀌고 불안정함 | Material 내부 선택과 직접 `(click)` 토글이 별개로 상태를 소유했고 빈 Set을 전체로 취급함. listbox `value/change` 한 경로로 연결, 초기 전체 선택·개별 선택·전체 해제=빈 목록 | 실제 Material chip harness 클릭 순서: 전체 → 일부 제외 → nest만 → 전체 해제 → main+python. 칩 상태와 실제 로그 목록 일치 |

### 변경 파일·동작 범위

- 설치: `src/core/resources/{ffmpeg-consent,model-consent}/` 출력 + `src/shell/store/store/` 소유 상태/이벤트/회귀 테스트.
- 실패 카드: `src/shell/projects/models/project-card.builder.{ts,spec.ts}` 및 `projects.component.spec.ts` 기존 기대값 보정. 실패 사유/재시도 대상은 대표 잡, 부분 결과 유무는 프로젝트 묶음 전체에서 확인한다.
- 숏폼: `src/features/shortform/pages/shortform-workflow-project-editor.{ts,spec.ts}`. 기존 최소 1초·알 수 없는 길이 폴백·마지막 대본 삭제 시 클립 제거 정책 유지. 새 자동 저장·TTS 합성은 추가하지 않음. Nest는 전달된 클립을 저장하는 기존 동작으로 충분해 수정하지 않았다.
- 스토리보드: `src/features/shortform-director/pages/scenario-page/` HTML·SCSS·spec만. 매우 짧은 대본은 가독성 최소 폭 때문에 좁은 화면에서 시각적 길이 비율이 일부 보정된다. 시간 데이터·선택 동작은 유지한다. 별도 storyboard-followups 공간의 프로필 카드/폼/프로필 페이지 수정과 겹치지 않음을 조사 시 확인했다.
- 다운로드: 현재 `src/shell/projects/projects-detail-page/` HTML·spec의 문구만 변경. 후속 요청으로 위치 변경과 추가 template/import/SCSS는 철회했다.
- 로그: `src/shell/settings/logs/` HTML·TS·spec. 기존 trace 포커스 시 전체 trace 표시 정책은 유지한다.

### 검증 근거·남은 확인

- 기준선: 관련 6개 spec **198 성공**.
- 수정 전 재현: **9 실패 / 196 성공**. 모든 실패가 위 6개 증상의 기대 행동과 맞았다.
- 1차 수정 후: 대상 spec **205 성공**, 스타일 계약 **6 성공**.
- 첫 전체 검사: **5,392 성공 / 1 실패**. 실패는 `ProjectsComponent … 완료 영상이 0건이면 [전체 ZIP]을 숨기고 다시 시도가 첫 버튼이다`의 기존 open 액션 기대값이었다. 이번 요청에 맞춰 결과 보기·ZIP이 없는 실패 카드를 기대하도록 보정했다.
- 독립 리뷰에서 이전 부분 결과 + 최신 빈 실패의 그룹 경계를 추가 확인. 회귀 **1 실패 / 247 성공**을 본 뒤 그룹 단위 산출물 판정으로 수정했고 재검토에서 주요 잔여 이슈 없음.
- 최종 전체 Angular/Karma: **5,394 성공 / 실패 0 / exit 0**.
- 설치형 앱용 Angular: `ng build --configuration=packaged` **exit 0**. `git diff --check` 통과.
- Node는 설치된 **22.22.3** 실행 파일을 명시했고 `NG_BUILD_MAX_WORKERS=2`를 사용했다. 초기 npx의 다른 Node 선택 및 sandbox 빌드 중단은 제품 실패와 구분했다. 테스트 helper 이름 충돌도 재현 검사 전에 정정했다.
- 독립 `local` dev server `127.0.0.1:4210` 기동 및 브라우저 로그인 화면 렌더 확인. 개발 API `localhost:3000/auth/dev-login`과 Nest `127.0.0.1:9019/v1/plugins`, `/app/info` 연결 실패가 관측되어 로그인 이후 실데이터 화면 스모크는 완료하지 못했다. 사용자 서버 실행 방식은 변경하지 않았다. 임시 서버/탭은 종료했다.
- 실제 설치형 앱 다운로드 동의 취소/재설치, 실패 카드, 대본 삭제/저장/재진입, 좁은 구성 버튼, 안무 ZIP 버튼의 다크/라이트 화면 및 파일 저장, 실제 로그 필터는 사용자 확인 대기다. 실제 ML/TTS/다운로드·실결제·운영 데이터 변경은 실행하지 않았다.
- 검증 로그(임시): `/private/tmp/w10-{baseline,red,green,review-red,full-tests-final,styles,build-packaged,local-smoke}.log`. 장기 보존 근거는 이 카드와 날짜 기록이다.

## 작업 공간

이번 수정 repo는 **Angular만**이다. `git fetch origin dev` 후 기준 SHA `797782e8f8e1c8488d024d23e6291e91c2b1e30e`에서 준비했다.

- branch: `fix/app-bugfix-20260929`
- 격리 Angular 작업 경로(종료 후 삭제): `/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_angular`
- tracked 변경: 소스·회귀 테스트 18파일, 미커밋. 원본 Angular의 기존 `node_modules`를 읽기용 symlink로 재사용하고 의존성 설치는 하지 않았다.
- 최초 수정은 Angular만 격리했다. 후속 설치형 앱 재빌드 요청에 따라 최신 origin/dev 기반 Electron/Nest 형제 worktree를 같은 branch로 준비했다. Python은 `.git` 파일 패키징 문제를 피하려고 최신 origin/dev의 Git 없는 빌드용 소스 복사본으로 준비했다. Web API는 수정·격리하지 않았다.
- [당시 설치형 앱 빌드 안내 이력](../../records/builds/2026/09/29-app-bugfix-local-build-history.md) — 아래 worktree 경로는 종료 후 삭제됨: 격리 Electron에서 `nvm use 24.19.0` 후 `npm run build:app:mac:arm64:local-api`. Electron/Nest/Python 기준 SHA, 로컬 설정·의존성 재사용 방법은 안내에 기록했다. 후속 W10-07에서 native 앱 전체 재빌드·실행 성공(아래 기록).
- 원본 및 다른 세션 checkout/branch/worktree는 보존했다. commit/push/merge/배포는 실행하지 않았다. 원본 설치 앱에 자동 반영된 것으로 보지 않는다. W10 격리 재빌드 앱은 후속 W10-07에서 실행 확인했다.

## 다음 행동·완료 기준

1. W10-01~06의 실제 설치형 앱 확인 결과를 받아 같은 ID에 추가한다. 현재 앱은 원본/기존 패키지이므로 격리 수정이 자동 반영됐다고 보지 않는다.
2. 재현이 남으면 원인 → 최소 수정 → 회귀/화면 확인을 이어간다. 실제 다운로드·TTS·ML이 필요한 확인은 사용자의 실행 범위를 먼저 확인한다.
3. 다음 증상은 W10-09부터 접수한다. 소스 검증 완료와 사용자 확인 완료를 구분하고, commit/push/통합/배포는 사용자 요청 시 진행한다.

## 제약

기획이 불명확한 부분만 필요한 선택을 묻는다. 이미 충분히 지정된 버그 수정의 권한을 반복 확인하지 않는다. 다른 세션의 branch/worktree·수정을 변경하지 않는다.

## 후속 — 다운로드 문구·설치형 빌드 준비

- 사용자 지정 문구 `개별 클립 전체 다운로드`로 HTML과 기존 회귀 기대값을 변경했다. 관련 화면 Karma 88 성공, `git diff --check` 성공. 로그: `/private/tmp/w10-wording.log`. 앞선 전체 5,394 성공 이후 이 문구 변경은 해당 화면만 재검증했다.
- 빌드용 Electron/Nest worktree와 Python 소스 복사본에 기존 packaged 설정·공개 키·uv 파일을 복사했다. `assert-no-packaged-secrets.mjs`, Electron builder/TypeScript 및 Nest pdfkit 의존성 해석 사전 검사 성공. 설정 값은 출력하지 않았다. 네이티브 앱 재빌드/실행은 사용자 확인 대기다.

## 후속 — 기존 팀 수정·중복 작업 보완 점검

- 최초 dev 최신화·재현은 확인했지만 원격 미병합 브랜치 전체 대조는 수정 후 사용자 질문에 따라 보완했다. Angular origin 56/로컬 49 브랜치와 접근 가능한 다른 작업 공간을 확인했으며 6개 동일 수정은 발견하지 못했다. 같은 파일의 다른 기능 변경과 미푸시 외부 작업의 한계는 [점검 기록](../../diagnostics/2026-09-29-w10-duplicate-fix-audit.md)에 정리했다.
- 다음 증상부터 수정 전에 dev 재현·관련 미병합 수정·다른 worktree 미커밋 겹침을 확인한다. 동일 수정 발견 시 재사용/통합 검토 대상으로 기록한다.

## W10-07 — 격리 재빌드 앱 시작 시 fs-extra 누락

- 접수: 안내한 `.app` 실행 시 main process Uncaught Exception `Cannot find module 'fs-extra'`, electron-updater require stack.
- 원인: W10 빌드 공간 준비 때 Electron node_modules 전체를 원본의 symlink로 둔 에이전트 설정 오류. 원본 파일은 있었지만 npm prod graph가 symlink 경로에서 2,543 dependency problems를 보고했고 updater의 fs-extra가 missing으로 나왔다. 최초 asar에는 electron-log/electron-updater/semver의 manifest 3개만 있었다. 런타임에서 오류가 재현된 사용자 증거와 패키지 구성/의존성 그래프를 대조했다.
- 기존 수정 점검: Electron origin 전체 fetch 후 관련 로컬/원격 미병합 커밋 및 접근 가능한 worktree 변경 확인. 동일 fs-extra/symlink 오류 수정 없음. 별도 Python `.git` 필터 수정은 **이미 로컬 feat/meme-overlay/merge 계열 d686393에 존재**, origin/dev에는 없음. 이전 카드의 필터 미수정 표현은 dev 상태에 대한 것이며 이 별도 수정은 중복 구현하지 않았다.
- 수정: W10 Electron node_modules symlink만 제거한 뒤 원본의 실제 의존성 디렉터리를 APFS clone copy했다. 원본 보존, 제품 코드/package-lock 변경 없음. 재검사 npm prod graph problems 0.
- 검증: Node 24.19.0, NG_BUILD_MAX_WORKERS=2로 `npm run build:app:mac:arm64:local-api` 전체 성공(exit 0). 새 asar manifest 17개, 필수 하위 의존성 누락 0. 앱 안의 실제 Electron 런타임으로 updater/fs-extra require 성공. 네이티브 앱 실행 후 CUA가 격리 renderer 경로의 홈 화면·프로젝트 목록을 확인했다. 앱은 사용자 테스트용으로 열어둠. 자동 테스트 비용을 발생시키는 생성/다운로드 동작은 실행하지 않았다.
- 증거: `/private/tmp/w10-electron-symlink-deps.json`, `/private/tmp/w10-electron-local-deps.json`, `/private/tmp/w10-native-rebuild.log`, `/private/tmp/w10-asar-green.log`, `/private/tmp/w10-native-launch.log`. node_modules는 ignored 실제 디렉터리, 원본/Electron 격리 tracked clean, Angular diff check 성공. commit/push/배포 없음.
- 재발 방지: LOCAL-BUILD.md에 Electron packaging의 node_modules symlink 금지와 npm ci 재설치 방법을 기록했다. 최초 소스 의존성 해석 사전 검사만으로 패키지 완전성을 확인할 수 없었으므로 실제 asar 의존성 및 네이티브 시작을 함께 확인했다.

## W10-08 — 구성 버튼 동일 너비 (후속 사용자 요청으로 철회)

- 사용자 요청: 라벨은 모두 보이지만 구성 버튼 너비가 다르다. 기존 의도를 확인하고 모든 너비를 동일하게 변경.
- 원인·의도: 9/21 `b38dcfa09` 커밋 설명과 `docs/superpowers/plans/2026-09-21-storyboard-v2-ui-refinement-fe.md` Task 6에 대본 길이 비례 타임라인으로 명시됐다. `durationMs / total`의 백분율을 flex-basis로 사용했다. W10-04 라벨 숨김 수정 때는 기존 비율 의도를 유지했지만 이번 사용자가 선택 버튼의 동일 너비를 명시해 변경했다.
- 사전 중복 점검: origin 전체 fetch 성공, dev 기준 SHA 동일. local/remote 미병합 scenario-page 변경 없음. W07 같은 spec 파일의 프로필 settingsV2 fixture 변경은 발견했으나 구성 버튼 테스트와 다른 영역이다. W07 수정은 복사/덮어쓰기하지 않았다. 향후 통합 시 양쪽 spec 변경 보존 필요.
- 변경: 시간 비율 inline binding 및 TimelineCell.widthPercent 제거. 구성 막대를 grid-auto-columns `minmax(4rem, 1fr)`로 변경해 모든 버튼을 같은 너비로 배치한다. 좁은 화면에서는 최소 너비를 유지해 막대 안에서 가로 스크롤. 시작 시간 tooltip/접근성 이름, 선택 상태는 유지. ts/html/scss/spec 4파일 최소 수정.
- RED: 실제 DOM geometry 테스트 2 실패/17 성공. 다른 시간 길이 세 버튼 폭 차이 88.6875px, 좁은 화면 한/두 자리 번호 폭 차이 6.96875px. GREEN: 같은 화면 19 성공. 전체 Angular 5,395 성공, 스타일 6 성공, diff check 성공. 로그 `/private/tmp/w10-equal-tabs-{red,green,full,style}.log`.
- 빌드: packaged Angular 및 Electron --dir 패키징 성공. 기존 실행 앱을 보존하려고 별도 출력 `desktop/clipper_electron/dist-app/equal-tabs/mac-arm64/Clipper Studio (dev).app`에 생성했다. 새 renderer JS에 동일 너비 CSS 포함 확인. asar 필수 의존성 누락 0 및 새 앱 실제 Electron의 updater/fs-extra require 성공. 새 앱 UI는 기존 앱을 종료한 뒤 사용자 확인 필요.
- 새 앱 실행: `open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/equal-tabs/mac-arm64/Clipper Studio (dev).app"`. 표준 build:app 재실행 시 기본 dist-app/mac-arm64에도 최신 수정이 반영된다. commit/push/배포 없음.

### W10-08 철회 — 대본 길이 비례 너비 복원

- 사용자가 시간 비례 타임라인 의도를 수용하여 동일 너비 변경만 되돌리도록 지시했다. widthPercent 계산과 flex-basis binding, flex 비례 배치를 W10-04 수정 직후 상태로 복원했다. W10-04의 항상 대본 N 표시·라벨 최소 폭·구성 막대 내부 스크롤·선택 상태와 다른 5개 수정은 유지했다.
- 동일 너비 기대 테스트와 추가 테스트만 제거하고 기존 시간 비례 테스트를 복원했다. scenario-page.ts는 dev 기준과 다시 동일; W10 전체 미커밋 tracked 20파일. 이번 회귀 화면 18 성공, 스타일 6 성공, diff check 성공. 로그 `/private/tmp/w10-revert-equal-tabs.log`, `/private/tmp/w10-revert-equal-tabs-style.log`. 전체 테스트는 동일 너비 변경 때 5,395 성공 이후 이번 철회에서는 해당 화면만 재검증했다.
- 설치형 테스트는 기본 `dist-app/mac-arm64/Clipper Studio (dev).app`을 사용한다. 이 앱은 W10-07에서 빌드한 시간 비례+라벨 수정 버전으로, 현재 패키지 renderer에서도 flex-basis/widthPercent와 라벨 최소 폭 포함을 재확인했다. `dist-app/equal-tabs`는 철회한 변경의 이전 산출물이므로 현행 검증에 사용하지 않는다. 현재 열려 있는 앱과 이전 산출물은 삭제/종료하지 않았다.
- 빌드 안내·보드에 철회 반영. commit/push/배포 없음.

## W10-05 후속 — 문구 유지·버튼 위치 변경 철회

- 사용자 요청으로 `개별 클립 전체 다운로드` 문구만 유지하고 프로젝트 삭제와 분리한 변경을 되돌렸다. 안무 다운로드 버튼은 기존 appPageActions 헤더에서 프로젝트 삭제 앞에 표시된다. 결과 영역 ZIP toolbar/멤버별 폴더 설명, 재사용 zipAction template/NgTemplateOutlet import, 관련 SCSS를 제거하여 원래 구조로 복원했다.
- 현재 이 화면의 제품 코드 diff는 HTML의 안무 문구 한 줄뿐이다. TS/SCSS는 dev와 동일. 기존 헤더 액션 테스트의 안무 문구 기대값만 변경했다. 화면 Karma 88 성공, 스타일 6 성공, diff check 성공. 증거 `/private/tmp/w10-revert-download-placement.log`, `/private/tmp/w10-revert-download-placement-style.log`. W10 전체 tracked 변경 18파일.
- 다른 5개 증상 수정 및 W10-08 시간 비례 복원은 유지했다. 기존 패키지 앱은 이번 버튼 위치 철회 전 산출물이다. 이번 턴 native 앱 재빌드는 미실행; 격리 Electron에서 기본 local-api 빌드 명령을 실행해야 반영된다. 사용자 요청에 따라 답변에 정확한 빌드/실행 명령을 함께 안내한다.
- 카드/보드/LOCAL-BUILD.md 갱신. 원본·타 세션 작업 보존, commit/push/배포 없음.

## W10-09 — 제거 시 다운로드한 모델 파일 삭제 옵션 (UI 선택 대기)

- 사용자 보고: 플러그인 제거 후에도 모델 파일이 남아 재설치 시 다운로드 동의 창이 나타나지 않는다. 원하면 모델 파일도 삭제하도록 추가 요청. 이후 실제 구현 전에 두 방식의 클릭 가능한 UI 목업 비교 요청.
- 현행 조사: Nest uninstall은 플러그인 비활성화/런타임 정지이며 모델 파일을 삭제하지 않는다. Electron 모델 준비 판정은 ready marker와 실제 파일을 확인한다. 모델 파일 삭제 후 재설치는 `AI 모델 필요` 동의 창을 재현한다. 최초 보고의 `다운로드 필요` 창은 공통 ffmpeg/ffprobe가 없는 별도 조건이므로 이번 모델 삭제만으로 그 창까지 재현되지는 않는다.
- 사전 중복 점검: Angular/Electron origin fetch 후 dev 기준 SHA 유지 확인. 관련 로컬/원격 미병합 변경 및 접근 가능한 worktree에서 동일 선택 삭제 기능은 발견하지 못했다. 외부 미푸시 작업은 확인 범위 밖이다. 제품 소스는 수정하지 않았다.
- 목업: A는 제거 창의 기본 해제 체크박스로 모델 파일 함께 삭제. B는 제거 후 별도 모델 파일 삭제 버튼과 확인 창. 프로젝트/공통 영상 도구 보존, 파일 유지 시 즉시 재설치, 파일 삭제 시 모델 다운로드 동의/취소/재시도를 두 방식 모두 로컬 상태로 시뮬레이션한다. 실제 파일 삭제/다운로드는 실행하지 않는다.
- 목업 경로: `/Users/jina/.codex/visualizations/2026/09/29/01a0ec05-3683-7fa0-8cf7-47676418e1cb/plugin-removal-options.html`. 736px/320px 화면 확인, A 체크/미체크 제거·B 별도 삭제·재설치 취소/재시도 클릭 확인, JS 구문 검사 성공.
- 다음: 사용자가 UI 방식을 선택하면 실제 모델 삭제 경로/공유 파일 보호/설치 상태 갱신을 구현·검증한다. 이번 턴 앱 재빌드 없음. 기존 W10 수정·다른 세션 작업 보존, commit/push/배포 없음.

## W10-05 후속 — 전체 클립 문구·툴팁 확정

- 사용자 승인: 안무 ZIP 버튼은 `모든 클립 다운로드 (ZIP)`, 기존 Material 방식 툴팁은 `모든 인물의 전체 클립을 인물별 폴더로 묶어 다운로드합니다.`로 적용. 버튼은 프로젝트 삭제 옆 기존 위치 유지. 다른 카테고리의 다운로드 문구·동작은 유지.
- 사전 확인: Angular origin 전체 fetch 후 origin/dev `797782e8f8e1c8488d024d23e6291e91c2b1e30e` 유지. 관련 파일의 로컬/원격 미병합 커밋 및 접근 가능한 타 worktree 미커밋 변경 없음. 기존 W10 격리 branch/worktree에서 이어서 수정.
- 변경: 결과 화면 HTML의 안무 문구·조건부 matTooltip, TS의 MatTooltipModule import, 기존 헤더 액션 테스트 기대값만 갱신. 기존 공통 버그 수정 유지. 전체 Angular tracked 미커밋 변경 19파일.
- 검증: 기존 문구 기대 변경 후 RED 1 실패/87 성공(이전 버튼 문구 불일치), 적용 후 GREEN 화면 88 성공. 스타일 6 성공, packaged Angular build exit 0, diff check 성공. 로그 `/private/tmp/w10-zip-tooltip-{red,green,style,build}.log`. 최초 sandbox 테스트 프로세스 exit 134 후 같은 검증을 승인된 실행으로 재시도했다. 이번에 별도 툴팁 동작 테스트는 추가하지 않았으며 실제 앱 호버 확인은 native 재빌드 후 사용자 확인 필요.
- Angular 화면 빌드만 수행. native `.app` 재빌드/실행은 미실행. 반영 명령: 격리 Electron에서 `nvm use 24.19.0`, `npm run build:app:mac:arm64:local-api`. commit/push/배포 없음.

### W10-09 후속 — 두 방식 병행 문의

- 사용자 `두 가지 다는?` 문의에 A/B를 함께 제공 가능하다고 답변. 제거 창의 기본 해제 체크박스는 즉시 정리, 미설치 플러그인의 별도 모델 파일 삭제 버튼은 이미 남겨둔 파일의 사후 정리 역할로 구분한다. 동일 파일 삭제 처리/보호 규칙을 공유하는 방향을 제안했다.
- 이번 턴 실제 모델 파일 삭제 기능 구현/사용자 파일 삭제는 미실행. 두 방식 병행 확정 및 실제 기능 구현은 후속 진행 대상이다.

## W10-09 구현 — 제거 시 선택 삭제 + 남은 파일 별도 정리

- 사용자 승인: 실제 모델 위치를 찾아 삭제 가능한지 확인하고 가능하면 두 흐름 구현. 기존 bounded A/B 설계에 따라 구현을 진행했다.
- 경로 확인: Electron 설치 판정의 `getModelNameToPath`를 삭제에서도 재사용. 안무는 userData의 `yolov8s-pose.pt` 및 plugin_models/dance_highlight의 YuNet/SFace ONNX 2개와 정확한 `.onnx.tmp` 2개. 대사는 현재 앱의 HF 환경 우선순위를 사용하는 hub의 `models--Systran--faster-whisper-small`, `models--laion--CLIP-ViT-B-32-laion2B-s34B-b79K` 폴더(각 snapshots/blobs·부분 다운로드 포함). 각 플러그인의 `.ready` 표시도 제거한다. Python 기본 모델 경로 및 앱/플러그인의 동일 cache isolation env 적용을 대조했다. 삭제 가능성을 임시 디스크 데이터와 실제 패키지 런타임에서 검증했다. 실제 사용자 캐시 파일 목록/내용은 읽거나 삭제하지 않았다.
- 보호: renderer는 플러그인 이름만 보내며 경로는 main에서 결정한다. 알려진 두 모델 플러그인만 지원, 모든 대상의 상위 심볼릭 링크를 삭제 전 검사, leaf 링크는 대상 내용을 따라가지 않고 링크만 삭제. 프로젝트, ffmpeg/ffprobe, Python venv, 다른 모델 폴더와 공통 캐시는 유지. 앱 밖 HF 캐시가 지정된 환경은 공유 여부를 확인 창에 설명한다.
- 동시성: main의 기존 플러그인 start/stop 직렬화 체인에서 파일 삭제를 수행한다. live process·시작/정지·설치 중인 플러그인은 삭제 거절. UI는 확인/처리 중 설치·중복 제거·중복 파일 삭제를 잠근다. uninstall 실패 시 삭제를 호출하지 않는다. 부분 실패도 상태를 재조회하고 다시 시도 가능하게 한다.
- UI: 모델을 쓰는 플러그인의 제거 창에 기본 해제 `다운로드한 모델 파일도 삭제` 체크박스. 확인 후 먼저 기존 uninstall 성공을 기다리고 선택 시 파일 삭제. 미설치 상태의 필요한 것 영역에 `모델 파일 삭제` 별도 버튼을 제공하며, 남은 파일(부분/임시 포함)이 없으면 비활성화. 별도 확인 창은 재다운로드와 프로젝트/공통 도구 보존을 안내. 브리지 기능이 없는 웹/구버전 환경에는 삭제 컨트롤을 노출하지 않는다.
- 사전 겹침 확인: Angular/Electron origin 전체 fetch 후 기준 SHA 유지. 관련 미병합 변경은 리소스/권한/기존 런타임 관련이며 동일 파일 삭제 기능 없음. 접근 가능한 타 worktree의 관련 미커밋 변경 없음. W10 Angular/Electron 격리에서만 수정, Nest/Python 소스 변경 없음. 구현 계획은 격리 Electron `docs/superpowers/plans/2026-09-29-plugin-model-removal.md`.
- 검증: 파일 경계·ready 초기화·재다운로드 필요·부분/임시 파일·링크·live process/queued start 테스트. 스토어 기본 미체크/체크, 취소, uninstall 실패, 별도 삭제 취소/실패 후 재시도, 정리 중 새 선택 보존 테스트. 파일 기능 최초 RED(모듈 없음) → GREEN 6; UI RED 5 실패 → GREEN; 리뷰에서 `.tmp` 누락/선택 덮어쓰기 발견, 각각 RED 재현 후 수정. 최종 Angular 전체 **5,400 성공**, 스타일 **6 성공**, Electron 전체 **989 성공**, TS/packaged Angular build 및 양 repo diff check 성공. 독립 리뷰의 두 지적 수정 확인 완료.
- 패키징: 기존 실행/기본 앱을 보존하고 `desktop/clipper_electron/dist-app/model-removal/mac-arm64/Clipper Studio (dev).app`에 별도 미서명 mac arm64 local-api 앱 생성 성공. 최신 Angular/Electron과 변경 없는 기존 Nest/Python 빌드 입력을 사용했다. actual packaged Electron Node 모드에서 임시 모델 삭제 후 files 없음/needed=true 및 updater/fs-extra 로드 성공. 최초 Node-mode 검증의 plugin-manager import는 app-mode electron-log가 electron builtin을 요구해 제외했으며 제품 시작 오류로 분류하지 않는다. 실제 새 앱 UI 실행/호버/사용자 모델 삭제 및 실다운로드는 미실행.
- 사용: 기존 Clipper 앱을 종료하고 위 별도 앱을 열면 된다. 이미 제거한 대사 플러그인 선택 → 모델 파일 삭제 → 설치하기 → `AI 모델 필요` 취소로 W10-01을 확인할 수 있다. 공통 ffmpeg/ffprobe는 유지하므로 최초 `다운로드 필요` 공통 도구 창은 별도 조건이다. 일반 재빌드는 기존 Electron local-api build 명령이며 기본 경로에 출력된다.
- 증거 로그: `/private/tmp/w10-model-{files-red,files-green,host-green,ui-red,ui-green,tmp-red,tmp-green,selection-red,angular-full,electron-full,style,packaged-build,native-package,packaged-smoke}.log`. 원본·타 세션·기존 앱/사용자 모델 보존, commit/push/배포 없음.

- 최종 정리: 이번 변경으로 미사용이 된 refreshItem helper를 제거한 후 스토어 34 성공·packaged FE build 성공을 재확인하고 별도 앱을 다시 패키징했다. 최종 패키지 임시 파일 smoke도 성공. 전체 5400/989 결과는 이 미사용 helper 정리 전의 동일 동작 코드에서 얻었으며 이후 동작 변경은 없다.


## W10-10 — 스토어 모델 용량/실제 파일 상태 구분

- 사용자 실기: 대사 플러그인 제거 창에서 모델도 삭제했는데 상세에 `1.1 GB 내려받음`/`파일 있음`이 남고 비활성 삭제 버튼과 없음 안내가 동시에 노출됨. 필요한 다운로드 여부와 실제 파일 보관 여부 혼동, 프로젝트 보존/남은 모델 정리 문구 및 공통 단위 개선 요청.
- 원인: 내려받음 문구는 다운로드 완료량이 아니라 manifest.totalModelSizeBytes의 예상 총량이었다. MB/GB 문구는 이미 공통 formatter였으나 GB/KB 분기에 약이 누락돼 불일치. 실제 파일 배지는 Nest assetsPresent 캐시(TTL 3초)에서 읽고, 새 파일 삭제 IPC의 hasFiles는 별도 삭제 버튼에만 사용해 같은 화면이 서로 다른 시점의 상태를 표시했다. 삭제 후 즉시 refresh는 서버 캐시를 재사용하므로 이후에도 화면 값이 남을 수 있다. 용량 숫자는 카탈로그의 모델별 예상치이며 실측 저장량은 아니다.
- UI: 설치 정보의 `상태`→`설치 상태`, `다운로드`→`모델 용량`; 현재 PC의 `모델 파일` 행을 별도로 추가(모두 있음/일부 있음/없음/확인되지 않음). 모델 용량은 모든 크기에 약을 사용하는 공통 formatter로 표시, hero도 `모델 용량 약 1.1 GB` 등으로 변경. 모델 없는 플러그인은 `추가 다운로드 없음`으로 통일. 필요한 것→필요한 모델, 기존 파일 있음 칩은 제거. 설치 상태/모델 용량/모델 파일 레이블은 hover 또는 keyboard focus로 Material tooltip 설명을 표시한다.
- 실제 상태: ModelFilesInfo에 구버전 호환 optional allFilesPresent 추가. Electron 설치 판정의 isModelPresent를 재사용해 완전한 모델과 HF 부분 cache/미완료 파일을 구분; 준비 마커만 남은 경우는 hasFiles=false. 파일 상태의 fresh IPC가 서버 캐시보다 우선한다. 삭제 결과를 즉시 반영하고 파일 재조회는 서버 refresh 실패와 독립적으로 수행. 설치 완료 2경로에서도 재조회한다. 파일 없음은 별도 삭제 버튼/안내뿐 아니라 제거 창의 모델 삭제 옵션도 숨긴다.
- 문구: 두 삭제 확인 창 모두 `프로젝트와 작업 결과는 삭제되지 않습니다.`로 변경. 공통 영상 처리 도구(ffmpeg/ffprobe)는 실제 유지하지만 제품 안내에서 제외. 별도 정리 안내 `모델 파일을 삭제해 저장 공간을 확보할 수 있습니다. 재설치 시 다시 다운로드합니다.`; 미체크 유지 안내 `모델 파일을 유지하면 다시 설치할 때 재사용합니다.`(부분 파일의 추가 다운로드 가능성을 부정하지 않음).
- 사전 확인: Angular/Electron origin fetch 후 기준 797782e8/0cd7ed7b 유지. 관련 미병합 커밋은 권한/IPC 등 기존 별도 작업이며 동일 상태 표시 수정 없음. 접근 가능한 타 worktree 관련 미커밋 없음. 기존 fix/app-bugfix-20260929의 두 repo만 수정. Nest/Python 및 원본/타 세션/사용자 모델 파일 수정·삭제 없음.
- 검증: stale assetsPresent=true 삭제/partial 파일/재설치 회귀 RED→GREEN. 실제 임시 HF cache의 전체/부분/없음 및 marker-only RED→GREEN. 독립 리뷰의 파일 없는 제거창/서버 재조회 실패 2건도 각각 실패 재현 후 보완하고 재검토 완료. 최종 Angular 전체 **5,404 성공**, Electron **991 성공**, 스타일 **6 성공**, focused store/detail **55 성공**, TS 및 packaged FE build·diff check 성공. 기존 테스트 미디어 404 경고는 있으나 테스트 실패 없음.
- 패키징: 최신 Angular/Electron과 변경 없는 기존 Nest/Python 빌드 입력으로 `desktop/clipper_electron/dist-app/store-file-status/mac-arm64/Clipper Studio (dev).app` 별도 생성 성공. 기존 실행 테스트 앱 보존. 실제 packaged Electron Node-mode에서 임시 파일 allFilesPresent true→false/hasFiles false/needed true, updater/fs-extra 로딩 성공. renderer 최신 문구 포함 확인 성공. 최초 renderer 검사에서 asar 안을 검색했으나 renderer는 extraResources/renderer에 있어 올바른 경로로 재검사; 제품 패키지 누락은 아님. 실제 UI 화면(다크/라이트)/사용자 모델 삭제/실다운로드는 사용자 확인 대상.
- 실행/직접 재빌드: 기존 앱 종료 후 위 store-file-status 앱 open. 일반 전체 재빌드는 격리 Electron에서 `nvm use 24.19.0` → `npm run build:app:mac:arm64:local-api`, 기본 dist-app/mac-arm64 경로에 최신 앱 출력. LOCAL-BUILD.md 최신 W10-10 참고.
- 로그: `/private/tmp/w10-store-{files-red,files-green,status-red,status-red2,status-green,status-review-red,status-review-green,status-angular-full,status-angular-final,status-electron-full,status-style-final,status-build-final,status-native-package,status-packaged-smoke}.log`. 계획 격리 Electron docs/superpowers/plans/2026-09-29-store-model-file-status.md. commit/push/배포 없음.


### W10-10 후속 — 용량 범위/로컬 서버 설명과 프로젝트 보존 안내

- 사용자 지적: 모든 다운로드가 모델인지, 서버가 무엇인지, 프로젝트/작업 결과를 왜 구분했는지 및 해당 플러그인으로 만든 프로젝트 보존 의도를 재확인. 현재 용량은 manifest.models/totalModelSizeBytes의 모델 카탈로그 합계다. 설치 도구(ffmpeg/ffprobe), Python 실행환경 등 전체 다운로드를 뜻하지 않는다. 이전 설명의 서버는 앱 내부 로컬 NestJS 백엔드이며 원격 운영 서버의 파일 조회가 아니다.
- 문구 수정: `이 플러그인으로 만든 프로젝트는 삭제되지 않습니다.`로 모델 옵션 제거 창/일반 제거 창/별도 모델 삭제 확인 창 모두 적용. 프로젝트와 결과를 별개 사용자 보관 항목처럼 나열하지 않는다. 다른 동작 변경 없음.
- 검증: 기존 store/detail 55 성공, packaged FE build 및 diff check 성공. 기존 전체 FE5404/Electron991/style6 결과는 직전 동작 수정 검증이며 이번 문구 수정 후 재실행한 결과는 아니다. 별도 `dist-app/store-copy/mac-arm64/Clipper Studio (dev).app` 패키징 성공 및 실제 packaged renderer의 새 안내 포함/기존 안내 제거 확인 성공. Electron/Nest/Python 소스·기존 앱·사용자 파일 보존.
- 실행: 기존 앱 종료 후 store-copy 앱 open. 직접 전체 재빌드는 동일 local-api 명령, 기본 dist-app/mac-arm64에 최신 소스 출력. LOCAL-BUILD.md에 기록. 로그 `/private/tmp/w10-store-copy-{test,build,native}.log`. commit/push/배포 없음.


### W10-10 후속 — 작업물 보존 문구 확정

- 사용자 `좋아 그렇게 수정해`에 따라 세 확인 경로(모델 옵션 제거창/일반 제거창/별도 파일 삭제 확인창)에 `이 플러그인으로 만든 작업물은 삭제되지 않습니다. 보관함의 프로젝트와 생성된 영상은 그대로 유지됩니다.` 적용. 기존 행동 변경 없음.
- 주석 1의 다운로드 표현에 대한 질문은 추천안으로 답변: 현재 집계 범위를 유지한 `AI 모델 파일 용량`/`AI 모델 파일`, 모델 본체와 관련 파일 전체 예상치를 tooltip에서 설명. 이 추천 레이블은 아직 코드에 적용하지 않음. Python 실행 패키지 등까지 합산한 전체 설치 용량으로 확장하지 않음.
- 검증: 기존 store/detail 55 성공, packaged FE build 및 diff check 성공. 별도 dist-app/store-work-preservation/mac-arm64/Clipper Studio (dev).app 생성, 실제 renderer에 두 문장 포함/이전 프로젝트-only 안내 제거 확인 성공. 기존 전체 회귀 검증과 이번 문구 확인은 구분. 기존 실행 앱과 사용자 파일, Electron/Nest/Python 소스 보존.
- LOCAL-BUILD.md에 새 앱 실행 경로와 기존 local-api 전체 재빌드 명령 기록. 로그 /private/tmp/w10-store-work-preservation-{test,build,native}.log. commit/push/배포 없음.


### W10-10 후속 — 현재 레이블 유지/용량 툴팁 한 문장

- 사용자 확정: AI 모델 파일 용량 및 필요한 파일 용량 추천안 모두 적용하지 않고 현재 레이블 유지. 모델 용량 tooltip의 뒷문장만 삭제해 `필요한 모델 전체의 예상 용량입니다.` 적용. 기존 보존 두 문장과 동작 유지. 변경은 plugin-detail HTML의 tooltip 1줄.
- 검증: packaged FE build와 diff check 성공. 새 dist-app/store-tooltip-short/mac-arm64/Clipper Studio (dev).app 별도 패키징 및 actual renderer 새 tooltip 포함/이전 긴 tooltip 제거 확인 성공. 문구만 수정해 테스트 추가/전체 회귀 재실행 없음. 기존 앱·사용자 파일·다른 repo 소스 보존. LOCAL-BUILD에 실행/직접 전체 재빌드 안내. 로그 /private/tmp/w10-store-tooltip-short-{build,native}.log. commit/push/배포 없음.


### W10-01 사용자 모델 취소 실기 / W10-10 설치 상태 툴팁 정리

- 사용자 실기 보고: 설치됐던 대사 플러그인을 모델 포함 제거 → 설치하기 → AI 모델 필요(버튼 설치 확인 대기 중) → 취소 → 설치하기 복원·미설치 유지. 모델 취소 실기 성공으로 기록. 사용자 보고에 목록 카드나 재클릭/새 모달 확인은 명시되지 않아 완료로 확장하지 않음.
- 원래 보고의 다운로드 필요는 ffmpeg/ffprobe 공통 도구 미설치 경로. AI 모델 필요와 서로 다른 dialog/service지만 cancelled 출력과 Store.onInstallCancelled의 소유 상태 해제는 공통. 기존 회귀는 두 경로 실제 컴포넌트 모달 버튼 취소/카드·버튼 복원/재시도 및 ffmpeg 완료 후 모델 취소를 포함. 실제 바이너리 미설치/최초 설치 native E2E와는 구분. 현재 PC 초기화나 바이너리 삭제 없이 별도 깨끗한 환경에서 최초 ffmpeg 취소 실기 추가 확인 권장.
- 현재 소스로 기존 store 37 성공(위 취소 회귀 포함) 재확인. 설치 상태 tooltip의 `제거해도 프로젝트는 남습니다.`만 삭제, `플러그인을 설치하면 왼쪽 메뉴에서 사용할 수 있습니다.` 유지. UI 행동 변경 없음. packaged FE build/diff check 및 별도 dist-app/install-status-tooltip/mac-arm64/Clipper Studio (dev).app 패키징과 renderer의 제거 문장 부재 확인 성공.
- LOCAL-BUILD에 최신 앱 경로/기존 local-api 전체 재빌드 명령·검증 범위 기록. 로그 /private/tmp/w10-install-cancel-confirm-test.log 및 /private/tmp/w10-install-status-tooltip-{build,native}.log. 기존 앱/사용자 파일/타 repo 소스 보존. commit/push/배포 없음.


### W10-10 후속 — 설치 정보 툴팁 코드 제거 / 빌드 금지

- 설치 정보의 세 행(설치 상태/모델 용량/모델 파일) matTooltip·tabindex 및 사용하지 않는 MatTooltipModule import/컴포넌트 imports를 제거. 다른 페이지의 툴팁은 유지. 기존 detail 테스트 18 성공, diff check 성공.
- 작업 중 사용자 `빌드 하지 마` 지시 수신. 앞서 시작한 packaged FE build는 즉시 SIGINT 중단(exit130, 로그 Building...). native 패키징 미실행, 기존 install-status-tooltip 앱 보존(이번 제거 미반영). 이후 사용자 빌드 요청 전 추가 빌드하지 않음. 로그 /private/tmp/w10-store-no-tooltips-{test,build}.log. 원본/타 세션/사용자 파일 보존, commit/push/배포 없음.


### W10-05 최종 상태 재확인

사용자 완료 여부 질문에 source 및 기존 최신 install-status-tooltip 앱 renderer에서 `모든 클립 다운로드 (ZIP)`/tooltip 확인. 문구·위치의 결론 및 구현 완료, 추가 수정 대기 없음. summary 표의 예전 개별 클립 전체 다운로드 문구를 최종 확정과 일치시킴. 문서만 정정, 추가 빌드/소스 변경 없음. 사용자 실제 hover 실기는 미보고, commit/push/배포 없음.


### W10-05 후속 — (ZIP) 제거 및 명시 요청 재빌드

- 사용자 `(ZIP)` 제거 지시로 안무 버튼 문구를 `모든 클립 다운로드`로 변경. 기존 tooltip과 프로젝트 삭제 옆 위치, 실제 ZIP 생성/다운로드 동작 유지. 기존 spec 기대값/테스트명만 갱신.
- 사용자 빌드 요청으로 이전 빌드 중단 지시의 이번 요청 예외로 재빌드 수행. 설치 정보 tooltip/import 제거 등 최신 소스도 포함. 기존 결과/detail 테스트 106 성공, packaged FE build 및 diff check 성공. Electron/Nest/Python의 변경 없는 검증된 기존 빌드 입력으로 별도 dist-app/zip-label-final/mac-arm64/Clipper Studio (dev).app 패키징 성공. 실제 renderer 새 문구/기존 ZIP suffix 없음/설치 정보 tooltip 제거 확인, packaged Electron Node-mode updater/fs-extra 로드 및 임시 파일 상태/삭제 성공.
- 기존 실행 앱/사용자 파일/다른 repo 소스 보존. 카드 요약·보드·LOCAL-BUILD에 최종 문구/앱 경로 기록. 로그 /private/tmp/w10-zip-label-final-{test,build,native,smoke}.log. 추가 빌드는 사용자 요청 시만, commit/push/배포 없음.


## 종료 — 커밋·푸시·dev 병합 및 정리

사용자 요청 완료. Angular 작업48155221 → dev3850ece8, Electron 작업776fd28 → dev9d5ea55. 각각 origin/fix/app-bugfix-20260929에 먼저 푸시 후 충돌 없이 dev 병합, 실제 dev에서 전체 FE5404/style6/Electron991 검증 성공 후 origin/dev 푸시. 실제 원격 SHA/조상·clean0/0 확인. 원격 작업 브랜치는 보존, 로컬 branch 및 worktree3개/Python 빌드 복사본/빌드 산출물은 정리. 다른 세션 작업 공간과 원본 의존성/사용자 데이터 보존. LOCAL-BUILD 이력은 records/builds로 옮김. 상세 [종료 기록](../../implementation/2026-09-29-app-bugfix-closeout.md). 이후 재빌드는 원본 desktop/clipper_electron에서 기존 local-api 명령. 이번 종료에서는 새 native 빌드/배포 없음.

## W10-11 — Angular 테스트가 다운로드 폴더에 `a.zip` 생성 (2026-09-30)

- 사용자 증상: 정확한 시점은 불명확하나 Downloads에 `a.zip`, `a (N).zip` 반복 생성.
- 조사: 9/29 생성된 7개는 모두 크기 1바이트·내용 `x`. macOS 다운로드 출처는 Chrome의 `http://127.0.0.1:<Karma port>/context.html`. Angular `FileDownloadService`의 브라우저 폴백 spec 마지막 테스트가 `new Blob(['x'])`를 응답으로 사용하고 `service.save('http://x/a.zip', 'a.zip')`를 호출하면서 실제 `HTMLAnchorElement.click()`은 가로채지 않았음. 따라서 Angular/Karma 테스트 실행 시 실제 Chrome 다운로드가 발생. 제품 다운로드 코드나 설치형 앱의 자동 다운로드로 볼 근거는 없음.
- 변경: `src/core/download/file-download.service.spec.ts`의 해당 테스트에서 앵커 `click()`만 Jasmine spy로 가로채고 호출 여부를 검증. 테스트 응답·실제 폴백 로직은 유지. 변경은 테스트 파일 1개뿐.
- 검증: 수정 후 대상 테스트 5/5 및 전체 Angular 5,404/5,404 성공. 두 실행 후 Downloads의 기존 `a*.zip` 개수 7개로 동일, 신규 파일 없음. 첫 제한 환경 시도는 Node 번들 단계 SIGABRT로 끝나 테스트가 시작되지 않았고, 재실행은 정상 완료. `git diff --check` 성공.
- 격리: origin/dev `3850ece8`에서 `fix/zip-test-download-20260930` 격리 작업 공간 생성. 타 세션 변경 없음. 기존 7개 다운로드 파일은 사용자 폴더에 보존. 작업 커밋 `5bb44d08`을 `origin/fix/zip-test-download-20260930`으로 푸시한 뒤 Angular dev에 --no-ff 병합·푸시(병합 `6bb4ab34`). 병합 tree는 검증한 작업 tree와 동일. 원본 dev clean/0·0, 해당 격리 worktree 및 로컬 branch 정리, 원격 작업 branch 보존. **설치형 앱 빌드/배포 없음.**
- 병합 후 원본 checkout에서도 Angular 5,404개가 두 번 모두 성공으로 출력됐으나 CLI 프로세스가 결과 출력 후 종료되지 않아 각각 종료 신호로 정리(종료 코드 143). 커밋 전 같은 tree의 격리 브랜치 전체 5,404개는 종료 코드 0. 종료 문제는 수정과 분리해 기록하며 원본 dev의 전체 테스트 종료 코드 0으로 보고하지 않는다. 병합 전후 다운로드 파일 수 7개 그대로.
