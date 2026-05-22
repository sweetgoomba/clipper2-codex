# 2026-05-20 Windows Build Session Report

작성일: 2026-05-20 KST  
작업 PC: Windows  
최종 상태: Windows x64 installer build 및 기본 packaged smoke 통과

## 목적

Windows PC에서 Clipper2 4개 repo만 사용해 Windows x64 NSIS installer를 생성하고, 설치 후 최소 실행 smoke까지 확인한다.

이번 세션은 다음 handoff 문서를 기준으로 진행했다.

- `.codex/implementation/2026-05-19-windows-build-codex-cli-handoff.md`
- `.codex/implementation/NEXT_SESSION_PROMPT.md`
- `.codex/session-logs/2026-05-19.log`
- `.codex/implementation/2026-05-19-template-builder-font-artifact-fix.md`

중요 전제:

- clone 대상은 `clipper_angular`, `clipper_electron`, `clipper_nestjs`, `clipper_python` 4개뿐이다.
- `adlight_python`은 clone하지 않는다.
- 공식 Template Builder font는 DB/S3 URL 정책을 사용한다.
- Windows build entrypoint는 `clipper_electron`의 `npm run build:app:win:x64`다.

## 최종 작업 경로

최종 build는 다음 ASCII 경로에서 진행했다.

```text
C:\project\adlight
```

초기에는 현재 Codex workspace인 아래 경로에 clone했다.

```text
C:\Users\메타버즈-신사업\Desktop\project\adlight
```

하지만 이 경로는 사용자명에 한글이 포함되어 있고, Node/npm native postinstall 및 Node script 실행에서 문제가 재현됐다. 따라서 handoff 문서의 권장 경로인 `C:\project\adlight`로 새 workspace를 만들고 그곳에서 build를 완료했다.

## 초기 경로에서 발생한 문제

처음에는 사용자의 요청에 따라 현재 경로에 4개 repo를 clone했다.

```text
C:\Users\메타버즈-신사업\Desktop\project\adlight
```

clone 자체는 성공했지만 다음 문제가 이어졌다.

1. Git `dubious ownership`
   - network/escalated context로 clone된 repo를 현재 Codex sandbox 사용자가 열 때 Git이 ownership을 의심했다.
   - 4개 repo를 `safe.directory`에 등록했다.

2. Git checkout 권한 문제
   - `.git/index.lock` 생성이 `Permission denied`로 실패했다.
   - repo ACL 조정도 시도했지만 Git checkout은 계속 막혔다.

3. npm install / Node script 문제
   - PowerShell에서 `npm`은 execution policy 때문에 `npm.ps1`을 로드하지 못했다.
   - 이후 `npm.cmd`를 사용했다.
   - `npm install` 중 native/postinstall 단계에서 실패했다.
   - 주요 실패 예:
     - `esbuild@0.25.4 postinstall`
     - `@parcel/watcher`
     - `lmdb`
     - `msgpackr-extract`
   - exit code `3221225477` 또는 `-1073741819` 형태가 확인됐다.
   - `-1073741819`는 Windows `0xC0000005 Access Violation`에 해당한다.

추가 진단:

- `node .\node_modules\esbuild\install.js` 실행 시 `C:\Users\메타버즈-신사업`에 대한 `lstat`이 `EPERM`으로 실패했다.
- `esbuild.exe` 자체는 직접 실행 시 정상적으로 version을 출력했다.
- 즉 package binary 문제가 아니라, 한글 사용자명 및 상위 사용자 폴더 접근/realpath 처리와 Node/npm native script 실행이 결합된 환경 문제로 판단했다.

사용자가 이전에 Codex CLI 설치 시에도 같은 계열의 문제가 있었다고 알려줬다.

- 기존 npm global prefix가 `C:\Users\메타버즈-신사업\AppData\Roaming\npm`일 때 `codex`가 `0xC0000005`로 crash.
- npm global prefix를 `C:\npm-global`로 바꾸고 PATH 우선순위를 조정하자 `codex --help`가 정상 출력됨.

이 정보와 이번 npm/native postinstall 실패 양상이 일치하여, 사용자 폴더 ACL을 더 건드리지 않고 `C:\project\adlight`로 전환했다.

## 새 ASCII workspace 구성

새 경로:

```text
C:\project\adlight
```

clone한 repo:

```text
C:\project\adlight\clipper_angular
C:\project\adlight\clipper_electron
C:\project\adlight\clipper_nestjs
C:\project\adlight\clipper_python
```

branch 및 commit:

| Repo | Branch | HEAD |
| --- | --- | --- |
| `clipper_angular` | `feature/initial-scaffold` | `4501146` |
| `clipper_electron` | `feature/windows-packaging` | `e264865` |
| `clipper_nestjs` | `feature/windows-packaging` | `c33fbd8` |
| `clipper_python` | `feature/windows-packaging` | `5a61a62` |

`clipper_nestjs` `c33fbd8`에는 Template Builder bare legacy font filename normalization fix가 포함되어 있다.

## Windows build tool 확인

확인한 버전:

```text
git version 2.41.0.windows.1
node v22.11.0
npm 10.9.0
bsdtar 3.8.4
```

PowerShell execution policy 때문에 `npm` 대신 `npm.cmd`를 사용했다.

## env 파일 처리

최종 build에 사용한 env 파일:

```text
C:\project\adlight\clipper_nestjs\.env.local
```

처음에는 이 파일이 `C:\project\adlight\clipper_nestjs`에 없었고, 이전 Desktop clone 쪽에만 있었다.

```text
C:\Users\메타버즈-신사업\Desktop\project\adlight\clipper_nestjs\.env.local
```

사용자가 env 준비를 완료했다고 알려준 뒤 실제 build 경로에는 파일이 없음을 확인했고, 비밀값을 출력하지 않고 다음 위치로 복사했다.

```text
C:\project\adlight\clipper_nestjs\.env.local
```

복사 후 확인:

```text
C:\project\adlight\clipper_nestjs\.env.local
Length: 423
```

비밀값은 출력하거나 문서에 기록하지 않았다.

### `clipper_python\.env` 관련 결론

현재 Windows packaged build 기준으로 `clipper_python\.env`는 필수 파일이 아니다.

Electron packaged mode의 `BundledEnvProvider`는 env를 다음 순서로 병합한다.

1. `resources\clipper_python\.env`
2. `resources\clipper_nestjs\.env`
3. `resources\clipper_nestjs\.env.local`
4. `%APPDATA%\Clipper2\.env`

없는 파일은 `{}`로 처리된다.

이번 smoke에서는 `clipper_python\.env` 없이도 다음이 통과했다.

- app launch
- Python venv creation
- NestJS `/v1/health`
- Template Builder families API

따라서 현재 build/smoke 기준에서는 `clipper_nestjs\.env.local`만 있어도 된다.  
다만 실제 plugin 기능 중 OpenAI/Naver/Kakao 등 env가 필요한 기능은 해당 값이 `clipper_nestjs\.env.local` 또는 `%APPDATA%\Clipper2\.env`에 있어야 한다.

`%APPDATA%`는 repo 경로가 아니라 Windows 사용자별 app data root다.

현재 PC 기준:

```text
%APPDATA% = C:\Users\메타버즈-신사업\AppData\Roaming
%APPDATA%\Clipper2\.env = C:\Users\메타버즈-신사업\AppData\Roaming\Clipper2\.env
```

## npm install

ASCII 경로에서 아래 방식으로 설치했다.

```powershell
npm.cmd install --cache C:\project\adlight\.npm-cache
```

실행 repo:

- `C:\project\adlight\clipper_angular`
- `C:\project\adlight\clipper_nestjs`
- `C:\project\adlight\clipper_electron`

결과:

- Angular install passed.
- NestJS install passed.
- Electron install passed.

참고:

- `npm audit` 취약점 출력은 있었지만 이번 Windows build smoke 범위 밖이라 수정하지 않았다.
- `npm install` 결과 `clipper_angular/package-lock.json`와 `clipper_electron/package-lock.json`가 수정된 상태다.
- 이 lockfile 변경은 아직 검토/커밋하지 않았다.

## uv 준비

`clipper_electron`에서 실행:

```powershell
npm.cmd run fetch-uv
```

결과:

```text
Downloading uv-darwin-arm64...
✓ uv-darwin-arm64
Downloading uv-darwin-x64...
✓ uv-darwin-x64
Downloading uv-win32-x64.exe...
✓ uv-win32-x64.exe
```

Windows build용 준비 smoke:

```powershell
node scripts\prepare-uv.mjs win32 x64
```

결과:

```text
✓ uv-win32-x64.exe → uv.exe
```

## Preflight build

### Angular

```powershell
cd C:\project\adlight\clipper_angular
npm.cmd run build:electron -- --progress=false
```

결과:

```text
Application bundle generation complete.
Output location: C:\project\adlight\clipper_angular\dist\clipper_angular
```

### NestJS

```powershell
cd C:\project\adlight\clipper_nestjs
npm.cmd run bundle
```

결과:

```text
ncc build src/main.ts -o dist/bundled
copied src\dance\data -> dist\bundled\dance\data
copied src\projects\assets -> dist\bundled\projects\assets
```

### Electron TypeScript

```powershell
cd C:\project\adlight\clipper_electron
npm.cmd run build
```

결과:

```text
tsc -p tsconfig.json
```

exit code 0.

## 최종 Windows installer build

실행:

```powershell
cd C:\project\adlight\clipper_electron
npm.cmd run build:app:win:x64
```

내부 단계:

1. Python `__pycache__` cleanup
2. Angular electron build
3. NestJS bundle
4. Electron TypeScript compile
5. `uv.exe` 준비
6. `electron-builder --win --x64`

결과:

```text
✓ Done. Artifacts in dist-app/
```

생성 산출물:

```text
C:\project\adlight\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
```

산출물 확인:

| Path | Size |
| --- | ---: |
| `dist-app\Clipper2 Setup 0.0.1.exe` | `165,487,916` bytes |
| `dist-app\win-unpacked\Clipper2.exe` | `188,784,128` bytes |
| `dist-app\win-unpacked\resources\bin\uv.exe` | `62,574,080` bytes |
| `dist-app\win-unpacked\resources\clipper_nestjs\.env.local` | `423` bytes |

electron-builder notes:

- Windows NSIS target 생성 성공.
- code signing 정보가 없어 signing은 skip됐다.
- app icon이 설정되지 않아 default Electron icon이 사용됐다.

이 둘은 이번 내부 smoke 범위에서는 blocker가 아니다.

## Installer smoke

생성된 NSIS installer를 다음 위치로 silent install 시도했다.

```text
C:\project\adlight\clipper2-smoke-install
```

명령은 300초 timeout에 걸렸지만, 이후 확인 결과 설치 디렉터리와 executable은 정상 생성되어 있었다.

확인된 파일:

```text
C:\project\adlight\clipper2-smoke-install\Clipper2.exe
C:\project\adlight\clipper2-smoke-install\Uninstall Clipper2.exe
C:\project\adlight\clipper2-smoke-install\resources\
```

installer process는 남아 있지 않았다.  
타임아웃은 설치 실패라기보다 NSIS silent/wait/finish 동작 쪽으로 보이며, 설치 결과물은 존재했다.

## Packaged app smoke

설치된 app을 실행했다.

```text
C:\project\adlight\clipper2-smoke-install\Clipper2.exe
```

첫 실행 확인:

- `Clipper2` process가 120초 동안 유지됨.
- `%APPDATA%\Clipper2\clipper_venv\Scripts\python.exe` 생성 확인.
- `%APPDATA%\Clipper2\logs\main.log` 생성 확인.

main log에서 확인한 주요 line:

```text
[setup] Python env ready.
[PluginHostBridge] listening on http://127.0.0.1:<port>
[window] showing main window
[NestManager] ready at http://127.0.0.1:<port>/v1
```

첫 API smoke에서 이전 log line의 stale port를 잡아 `/v1/health`가 실패했다.  
이후 실행 전 log line count를 기록하고 새로 추가된 `NestManager ready` line만 읽도록 고쳐 다시 확인했다.

최종 API smoke:

```text
BASE_URL=http://127.0.0.1:64441/v1
HEALTH_STATUS=200
FAMILIES_STATUS=200
FAMILIES_COUNT=24
```

확인한 endpoint:

```text
GET /v1/health
GET /v1/template-builder/families
```

smoke 후 남은 `Clipper2` process는 없었다.

## 최종 repo 상태

`C:\project\adlight` 기준:

| Repo | Status |
| --- | --- |
| `clipper_angular` | `feature/initial-scaffold`, `package-lock.json` modified |
| `clipper_electron` | `feature/windows-packaging`, `package-lock.json` modified |
| `clipper_nestjs` | `feature/windows-packaging`, clean |
| `clipper_python` | `feature/windows-packaging`, clean |

`package-lock.json` 수정은 `npm install`이 Windows/npm 10.9.0 환경에서 lock metadata를 갱신하면서 생긴 것으로 보인다. 아직 검토하거나 커밋하지 않았다.

## 이번 세션에서 확인한 것

- Windows PC에서 4개 repo만으로 Windows x64 installer build 가능.
- `adlight_python` 없이 build 가능.
- `clipper_python\.env` 없이 build 및 기본 packaged smoke 가능.
- `clipper_nestjs\.env.local`은 installer build/resource 포함 및 Template Builder official API smoke에 필요.
- `resources\bin\uv.exe`가 packaged app에 포함됨.
- packaged app first-run에서 Windows Python venv가 생성됨.
- packaged NestJS gateway가 `/v1/health`에 응답함.
- Template Builder family list API가 응답하고 24개 family를 반환함.
- Mac 세션에서 마무리한 Template Builder font artifact fix commit들이 Windows build 대상 branch에 포함된 상태로 build됨.

## 아직 확인하지 않은 것

이번 세션에서는 다음을 아직 완전 smoke하지 않았다.

- installer UI를 사람이 직접 클릭해서 설치하는 흐름.
- installed app의 실제 renderer 화면 육안 확인.
- Template Builder 화면에서 card thumbnail/image/font가 실제 UI에 모두 보이는지.
- Template Builder text artifact 변환이 Windows packaged app에서도 눈으로 정상인지.
- Template Builder sample render 실행.
- plugin start/stop.
- Dialog/Dance workflow end-to-end.
- ffmpeg/ffprobe 다운로드 및 plugin render path.
- code signing, app icon, SmartScreen 대응.
- Windows CUDA acceleration.

## 다음 권장 작업

1. `C:\project\adlight\clipper2-smoke-install\Clipper2.exe`를 직접 열어 UI를 확인한다.
2. Template Builder 화면을 열고 official list/card thumbnails가 보이는지 확인한다.
3. 템플릿 하나를 선택해 text artifact 변환 후에도 한글 폰트가 정상인지 확인한다.
4. 가능하면 Template Builder sample render를 한 번 실행한다.
5. 가벼운 plugin start/stop smoke를 진행한다.
6. `clipper_angular/package-lock.json`, `clipper_electron/package-lock.json` 변경이 필요한 변경인지 확인한다.
   - 단순 npm 버전 metadata churn이면 되돌릴지 결정한다.
7. Windows build 성공 후 별도 사용자용 guide가 필요하면 `.codex/operations/windows-packaging/runbooks/windows-build-guide.md` 같은 문서로 정리한다.

## 주의사항

- Windows에서는 한글 사용자명 아래 workspace에서 Node/npm native script가 깨질 수 있다.
- 이번 build처럼 `C:\project\adlight` 같은 ASCII 경로를 쓰는 것이 안전하다.
- PowerShell에서 `npm`이 execution policy로 막히면 `npm.cmd`를 사용한다.
- 비밀값은 repo 문서나 로그에 남기지 않는다.
- 현재 packaged env 방식은 `.env.local`이 app resource에 평문 포함되는 구조다. 내부 테스트용으로는 유지했지만 외부 배포 전에는 별도 secrets delivery 정책이 필요하다.
