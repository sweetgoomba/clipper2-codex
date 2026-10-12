> 종료 후 보존한 개발 당시 빌드 이력입니다. 아래 `.worktrees/app-bugfix-20260929` 및 앱 경로는 정리돼 사용할 수 없습니다. 현재 재빌드는 `.codex/implementation/2026-09-29-app-bugfix-closeout.md`를 따릅니다.

# W10 설치형 앱 로컬 빌드

이번 6개 수정과 사용자 지정 다운로드 문구가 포함된 빌드 공간이다.

```sh
cd /Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron
nvm use 24.19.0
npm run build:app:mac:arm64:local-api
open "dist-app/mac-arm64/Clipper Studio (dev).app"
```

`local-api`는 Web API `http://127.0.0.1:3000`에 연결하며 실행 가능한 `.app`을 생성한다. Web API는 기존 로컬 실행 방식으로 켜둔다. dev 서버 연결용 DMG가 필요하면 `npm run build:app:mac:arm64`를 사용한다.

## 준비한 구성

- Angular: `fix/app-bugfix-20260929`, dev `797782e8f8e1c8488d024d23e6291e91c2b1e30e` 기반, W10 수정 미커밋.
- Electron: 같은 브랜치의 격리 worktree, 최신 origin/dev `0cd7ed7b9444bb00c6372bdcff47a356f5520c35`.
- Nest: 같은 브랜치의 격리 worktree, 최신 origin/dev `824a7a9f71dde8aa44c8692eadacb6ba6e4961b8`.
- Python: 최신 origin/dev `47782953228861f4bdbdc135265d067c2a826b0e`의 Git 없는 빌드용 소스 복사본. 기존 패키징 필터가 worktree의 `.git` 파일을 앱에 복사하는 문제를 피한다. Python 소스 수정용 checkout은 아니다.
- Angular/Nest `node_modules`는 기존 원본 의존성을 symlink로 재사용한다. **Electron은 실제 디렉터리여야 한다.** 최초 symlink 구성은 npm/electron-builder가 하위 런타임 의존성을 누락시켜 앱 시작 시 fs-extra 오류를 냈다. W10 Electron은 원본 의존성을 실제 디렉터리로 복사하여 수정했다. 이후 깨끗한 의존성 설치가 필요하면 격리 Electron에서 `npm ci`를 실행한다. Nest/Python `.env.packaged`, Electron 공개 인증 키와 mac arm64 uv 파일은 빌드 공간에 복사했다.
- 설정의 packaged secrets 검사 통과. 사용자 시작 오류 후 전체 mac arm64 local-api 빌드 성공, app.asar 런타임 의존성 17개 manifest의 필수 의존성 누락 0 확인, 앱 안의 실제 Electron에서 electron-updater/fs-extra 로딩 성공. 네이티브 앱 홈 화면과 기존 프로젝트 목록 표시까지 확인했다. 앞선 6개 수정의 실제 UI 동작 검증은 사용자 확인 대기다.

원본 repo나 다른 세션의 작업은 변경하지 않았다. commit/push/배포는 하지 않았다.

## W10-08 동일 너비 변경 철회

사용자 요청으로 동일 너비 변경을 되돌렸다. 현재는 대본 시간 비례 너비와 항상 라벨 표시를 적용한다. 기존 앱을 종료한 뒤 **기본 경로 앱**을 사용한다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"
```

기본 경로 앱은 W10-07의 시간 비례+라벨 수정 버전이며 패키지 renderer를 다시 확인했다. 철회 후 화면 18/스타일 6 검증 성공. `dist-app/equal-tabs`는 철회한 동일 너비 변경의 이전 산출물이다. 표준 build:app 명령을 다시 실행해도 현재 소스의 시간 비례 너비가 반영된다.

## 최신 W10-05 다운로드 버튼 위치 철회

문구 `개별 클립 전체 다운로드`는 유지하고 버튼을 기존 헤더의 프로젝트 삭제 옆으로 복원했다. 이 후속 소스 변경은 기존 앱 산출물에 아직 반영되지 않았다. 기존 테스트 앱을 종료하고 이 안내 맨 위의 기본 local-api 빌드 명령을 실행한 뒤 기본 dist-app/mac-arm64 앱을 연다. 같은 화면 테스트 88/스타일 6 성공.

## 최신 W10-09 — 모델 파일 삭제 및 안무 문구·툴팁

`모든 클립 다운로드 (ZIP)`과 툴팁, 모델 제거 시 체크박스/남겨둔 파일의 별도 삭제 버튼까지 포함한 새 앱을 별도 경로에 패키징했다. 기존 기본 앱은 보존되어 이 변경이 들어 있지 않다. 기존 Clipper 앱을 종료한 뒤 다음 새 앱을 연다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/model-removal/mac-arm64/Clipper Studio (dev).app"
```

이후 직접 전체 재빌드하려면 맨 위 local-api 명령을 실행한다. 그 명령은 기본 `dist-app/mac-arm64` 경로에 최신 수정 앱을 만든다. 이번 별도 앱은 최신 Angular/Electron을 빌드하고 기존 변경 없는 Nest/Python 입력으로 패키징했다. Angular 5400·스타일 6·Electron 989 및 패키지 런타임의 임시 파일 삭제/updater/fs-extra 검증 성공. 실제 앱 화면/사용자 모델 삭제는 직접 확인 필요.

이미 미설치인 대사 플러그인의 `모델 파일 삭제`를 확인한 뒤 설치하기를 누르면 `AI 모델 필요` 모달을 테스트할 수 있다. ffmpeg/ffprobe는 지우지 않으므로 공통 도구의 `다운로드 필요` 모달은 이 작업으로 재현하지 않는다.

## 최신 W10-10 — 모델 용량과 실제 파일 상태 구분

W10-09의 모델 삭제 기능을 포함해 스토어 후속 수정까지 적용한 별도 앱을 빌드했다. 기존 model-removal/기본 앱은 보존했으며 이번 변경이 들어 있지 않다. 기존 Clipper 앱을 종료하고 다음 앱을 연다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/store-file-status/mac-arm64/Clipper Studio (dev).app"
```

모델 용량(카탈로그 예상 총량)과 모델 파일(현재 PC: 모두 있음/일부 있음/없음)을 분리했다. 최신 파일 IPC가 서버의 캐시보다 우선한다. 삭제할 모델이 없으면 별도 삭제 컨트롤과 제거 창의 모델 삭제 옵션을 숨긴다. 제거/재설치/서버 새로고침 실패 후에도 파일 상태를 갱신한다. 안내는 프로젝트/작업 결과 보존과 재설치 시 다운로드를 설명한다.

Angular 5,404·Electron 991·스타일 6 성공, packaged FE/TS build와 별도 native 패키징 성공. 실제 패키지 Electron에서 임시 파일 상태/삭제와 updater/fs-extra 로드를 검증했고 renderer의 최신 문구 포함을 확인했다. 실제 앱 화면의 다크/라이트 및 사용자 모델 파일 동작은 사용자 확인 대상이다.

직접 전체 재빌드할 때는 이 문서 맨 위의 `npm run build:app:mac:arm64:local-api`를 사용한다. 해당 명령은 최신 소스로 기본 `dist-app/mac-arm64`에 출력한다. 별도 store-file-status 앱은 지금 생성한 테스트 산출물이다. commit/push/배포 없음.

## W10-10 후속 — 생성한 프로젝트 보존 안내

제거 확인 창(모델 옵션 유무 모두)과 모델 파일 삭제 확인 창의 안내를 `이 플러그인으로 만든 프로젝트는 삭제되지 않습니다.`로 변경했다. `프로젝트와 작업 결과`를 사용자에게 별개 보관 대상으로 나열하지 않는다. 현재 모델 용량 필드는 manifest.models 및 totalModelSizeBytes의 예상치이며, 설치 과정의 ffmpeg/ffprobe 또는 Python 실행환경 다운로드 전체 용량을 뜻하지 않는다. 이전 설명의 서버는 앱이 PC 내부에서 실행하는 로컬 NestJS 백엔드다.

새 앱은 기존 앱 종료 후 다음 경로로 실행한다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/store-copy/mac-arm64/Clipper Studio (dev).app"
```

직접 전체 재빌드는 문서 맨 위의 local-api 명령으로 기본 dist-app/mac-arm64에 출력한다. 이번에는 안내 문구만 수정해 스토어/detail 기존 55개 테스트와 packaged FE 빌드를 확인했다. 기존 전체 회귀 결과(FE5404/Electron991/style6)는 직전 동작 변경 검증이며 이번 문구 변경 후 재실행한 결과가 아니다.

## 최신 — 작업물 보존 안내 두 문장 적용

제거 확인 창(모델 옵션 유무 모두)과 모델 파일 삭제 확인 창에 사용자 확정 문구를 적용했다.

> 이 플러그인으로 만든 작업물은 삭제되지 않습니다. 보관함의 프로젝트와 생성된 영상은 그대로 유지됩니다.

스토어/detail 기존 55개 검증, packaged FE build, 별도 native 패키징 및 실제 renderer 문구 포함 확인 성공. 기존 앱을 종료한 뒤 아래 앱을 실행한다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/store-work-preservation/mac-arm64/Clipper Studio (dev).app"
```

직접 전체 재빌드는 맨 위 local-api 명령을 사용하며 기본 dist-app/mac-arm64에 출력한다. 다운로드 항목의 `AI 모델 파일 용량`/`AI 모델 파일`은 이번 답변의 추천안이며 아직 소스에 적용하지 않았다. 이번 변경은 보존 안내 두 문장만이다.

## 최신 — 모델 용량 툴팁 한 문장

현재 모델 용량/모델 파일 레이블은 그대로 유지하고 모델 용량 tooltip을 `필요한 모델 전체의 예상 용량입니다.`로 줄였다. 뒷문장만 삭제했다. 기존 작업물 보존 두 문장 등 수정은 유지한다. packaged FE build·diff check, 별도 native 패키징 및 actual renderer의 새 tooltip/이전 긴 tooltip 제거 확인 성공. 단순 문구 변경으로 테스트를 추가하거나 전체 회귀를 재실행하지 않았다.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/store-tooltip-short/mac-arm64/Clipper Studio (dev).app"
```

기존 Clipper 앱을 종료한 뒤 실행한다. 직접 전체 재빌드는 맨 위 local-api 명령이며 기본 dist-app/mac-arm64에 최신 소스로 출력한다.

## 최신 — 설치 상태 툴팁 정리/설치 취소 확인

설치 상태 tooltip을 `플러그인을 설치하면 왼쪽 메뉴에서 사용할 수 있습니다.`로 줄였다. 모델 용량 tooltip 1문장과 작업물 보존 두 문장은 유지한다. 기존 스토어 회귀 37 성공(ffmpeg 취소/모델 취소/재시도 포함), packaged FE build 및 별도 native 패키징·renderer 문구 확인 성공.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/install-status-tooltip/mac-arm64/Clipper Studio (dev).app"
```

기존 앱을 종료한 뒤 실행한다. 직접 전체 재빌드는 맨 위 local-api 명령이며 기본 dist-app/mac-arm64에 출력한다. 사용자 실기로 모델 삭제 후 AI 모델 필요 취소 시 설치하기/미설치 복원 확인. 반복 설치 요청 시 모달 재표시와 ffmpeg 미설치의 다운로드 필요 취소 실기는 아직 미보고. 현재 사용자 바이너리를 삭제하지 않고 별도 깨끗한 환경에서 최초 설치 확인을 권장한다.

## 최신 소스 — 설치 정보 툴팁 제거 / 빌드 중단

사용자 요청으로 설치 상태/모델 용량/모델 파일의 tooltip과 tooltip용 tabindex, PluginDetailComponent의 MatTooltipModule import를 제거했다. 기존 detail 테스트 18 성공 및 diff check 성공. 시작했던 packaged FE build는 후속 `빌드 하지 마` 지시를 받고 SIGINT로 중단(exit130, 로그 Building...); native 패키징은 실행하지 않았다. 최신 설치형 앱 install-status-tooltip에는 이 제거가 아직 반영되지 않았다. 사용자가 빌드를 요청하기 전에는 추가 빌드하지 않는다.

## 최신 — 모든 클립 다운로드 / 사용자 요청 빌드 완료

사용자 요청으로 안무 버튼 `(ZIP)`만 제거해 `모든 클립 다운로드` 적용. 다운로드 tooltip/기존 위치/ZIP 동작 유지. 설치 정보 tooltip 제거 등 최신 소스 변경을 함께 포함한 새 앱을 별도로 빌드했다. 기존 결과/detail 화면 검증 106 성공, packaged FE/native build 및 실제 renderer에서 새 버튼/설치 정보 tooltip 제거 확인 성공. 실제 패키지 Electron Node-mode에서 updater/fs-extra 및 임시 모델 상태/삭제 확인 성공.

```sh
open "/Users/jina/project/adlight/.worktrees/app-bugfix-20260929/desktop/clipper_electron/dist-app/zip-label-final/mac-arm64/Clipper Studio (dev).app"
```

기존 앱을 종료한 뒤 실행한다. 직접 전체 재빌드는 맨 위 local-api 명령으로 기본 dist-app/mac-arm64에 출력한다. 이번 사용자 명시 요청으로만 추가 빌드했으며 이후 추가 빌드는 다시 요청할 때 진행한다.
