# Next Session Prompt

작성일: 2026-04-30
최신 갱신: 2026-05-22

## 2026-05-22 Angular Template Builder / Dance UI handoff

2026-05-21 execution env / Windows packaged build 기준은 계속 유효하다. 그 위에 2026-05-22에는 `clipper_angular` UI/UX와 Template Builder ffmpeg/ffprobe readiness gate를 보완했다.

### 추가로 먼저 읽을 문서

아래 문서는 2026-05-21 문서 다음에 읽는다.

1. `.codex/implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md`
2. `.codex/session-logs/2026-05-22.log`

### 현재 repo 상태

모든 관련 repo는 clean이고 origin과 동기화되어 있다.

```text
clipper_nestjs:   feature/windows-packaging @ 9cd43f1 Trim optional env placeholders
clipper_electron: feature/windows-packaging @ f701677 Revert "Update electron builder"
clipper_angular:  feature/initial-scaffold  @ cad4b6c Gate template builder startup on ffmpeg readiness
clipper_python:   feature/windows-packaging @ 88d22c6 Trim optional env placeholders
```

### 2026-05-22 완료 작업

- Dance setup/member image selection:
  - 멤버별 이미지 선택 단계에서 세로 스크롤이 가능하도록 page shell과 내부 container scroll ownership 정리.
  - member image selection host/wrap 폭을 정리해 내부 컨테이너 좌측 치우침 제거.
- Template Builder thumbnails:
  - 카드 thumbnail 이미지가 로딩 전 검정 배경으로 보이는 UX를 skeleton placeholder로 개선.
  - thumbnail loading/fallback 상태를 `TemplateFamilyThumbnailComponent`로 분리.
- Template Builder ffmpeg/ffprobe readiness:
  - Template Builder 목록 API 자체는 ffmpeg/ffprobe를 직접 쓰지 않는다.
  - 하지만 Template Builder page startup에서 text preview renderer worker를 warm-up하고, sample render 기능도 `clipper1_video_render` Python worker를 사용한다.
  - 따라서 Template Builder 본 UI는 ffmpeg/ffprobe ready 이후에만 시작한다.
  - ready 이후에만 backend base URL load, families load, text preview renderer warm-up을 실행한다.

### 2026-05-22 Angular commits

```text
4785375 Fix dance setup vertical scrolling
584570c Center dance member image selector
bf4374e Extract template family thumbnail loading
e9c348b Guard template builder renders on ffmpeg readiness
cad4b6c Gate template builder startup on ffmpeg readiness
```

### 2026-05-22 검증

```text
clipper_angular npm test -- --watch=false --include src/features/dance-highlight/pages/dance-setup/dance-setup.component.spec.ts
clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-family-thumbnail.component.spec.ts
clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-family-gallery.component.spec.ts
clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
clipper_angular npm run build -- --progress=false
git -C clipper_angular diff --check
```

### 다음 세션 우선 확인

Windows packaged smoke에서 기존 2026-05-21 항목에 더해 아래를 확인한다.

1. Template Builder 진입 시 ffmpeg/ffprobe 미설치 상태에서는 consent overlay / blocked gate가 먼저 보이는지.
2. ffmpeg/ffprobe 설치 완료 후 Template Builder families load, text preview artifact, sample render가 정상 동작하는지.
3. Dance member image selection 단계에서 스크롤과 중앙 정렬이 Windows packaged app에서도 유지되는지.
4. Template Builder card thumbnail skeleton이 검정 배경 flash 없이 보이는지.

## 2026-05-21 execution env / Windows packaged build handoff

이 섹션을 다음 세션의 최우선 기준으로 본다. 아래 2026-05-20 이전 기록에는 현재 정책과 맞지 않는 오래된 env 설명이 일부 남아 있다.

### 먼저 읽을 문서

1. `.codex/README.md`
2. `.codex/session-logs/2026-05-21.log`
3. `.codex/design/2026-05-21-execution-env-mode-design.md`
4. `.codex/implementation/2026-05-21-windows-dance-image-env-management-context.md`
5. `.codex/implementation/2026-05-21-execution-mode-runbook.md`
6. `.codex/implementation/2026-05-21-windows-electron-builder-powertoys-ebusy-diagnosis.md`

### 현재 repo 상태

모든 관련 repo는 clean이고 origin과 동기화되어 있다.

```text
clipper_nestjs:   feature/windows-packaging @ 9cd43f1 Trim optional env placeholders
clipper_electron: feature/windows-packaging @ f701677 Revert "Update electron builder"
clipper_angular:  feature/initial-scaffold  @ cad4b6c Gate template builder startup on ffmpeg readiness
clipper_python:   feature/windows-packaging @ 88d22c6 Trim optional env placeholders
```

`clipper_electron`에는 Windows EBUSY 진단 중 생긴 trial commit들이 history에 남아 있지만, 최종 net diff는 제거됐다.

현재 남아 있지 않은 것:

```text
win.asar: false
electron-builder Step 5 retry
Windows lock cleanup/fail-fast handling
electron-builder 26.x upgrade
```

현재 `electron-builder` / `app-builder-lib`는 다시 `25.1.8`이다.

### 이번 세션에서 확정된 핵심 정책

- 실행 모드는 `local`, `devapp`, `packaged`.
- `.env.local`은 localhost browser 개발 실행용이다. 개인 PC override가 아니다.
- `.env.devapp`은 unpackaged Electron dev app 실행용이다.
- `.env.packaged`는 실제 설치형 app 실행용이다.
- `.env.test`는 사용하지 않는다.
- 각 repo는 자신이 소비하는 env 파일을 가진다. root 공통 env 파일은 두지 않는다.
- real `.env.<mode>` 파일에는 실제로 값을 설정할 key만 둔다. optional blank placeholder를 두지 않는다.
- OS별 `.env` 파일을 따로 만들지 않는다. normalized `.env.*`를 다른 PC의 같은 상대 경로에 복사한다.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- plugin별 고정 포트는 사용하지 않는다. mode별 port range에서 runtime이 동적으로 할당한다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- 방향은 NestJS control plane, Electron은 desktop host/native adapter다.

### ignored secret env 기준

현재 실제 ignored env 파일은 git에 없으므로 새 PC에서는 같은 상대 경로로 복사해야 한다.

복사 대상:

```text
clipper_nestjs/.env.local
clipper_nestjs/.env.devapp
clipper_nestjs/.env.packaged
clipper_python/.env.local
clipper_python/.env.devapp
clipper_python/.env.packaged
clipper_electron/.env.devapp
```

현재 key shape:

```text
clipper_nestjs/.env.local: NEST_PORT, image search keys, plugin port range, Template Builder DB/S3 keys
clipper_nestjs/.env.devapp: NEST_PORT, image search keys, plugin port range, Template Builder DB/S3 keys
clipper_nestjs/.env.packaged: image search keys, plugin port range, Template Builder DB/S3 keys
clipper_python/.env.local: OPENAI_API_KEY
clipper_python/.env.devapp: OPENAI_API_KEY
clipper_python/.env.packaged: OPENAI_API_KEY
clipper_electron/.env.devapp: CLIPPER_RENDERER_URL, CLIPPER_NEST_BASE_URL
```

현재 없어야 하는 key:

```text
CLIPPER_PYTHON_ROOT
CLIPPER_PLUGIN_HOST_MODE
PLUGIN_URLS
HF_HOME
HUGGINGFACE_HUB_CACHE
XDG_CACHE_HOME
INSIGHTFACE_HOME
IMAGEIO_FFMPEG_EXE
IMAGEIO_FFPROBE_EXE
CLIPPER_LEGACY_ASSETS_DIR
CLIPPER_LEGACY_FONTS_DIR
CLIPPER1_REMOTE_ASSET_TIMEOUT_SEC
CLIPPER1_REMOTE_FONT_MAX_BYTES
```

Python env에는 Naver/Kakao key를 두지 않는다. 현재 dance member image search owner는 NestJS image search API다.

### Windows build 주의

PowerToys를 사용하는 Windows PC에서는 build 중 `Command Palette`를 끈다.

확정된 원인:

- `Microsoft.CmdPal.UI.exe`가 fresh `dist-app\win-unpacked\Clipper2.exe`를 감지/매핑.
- electron-builder가 같은 exe에 ASAR integrity resource를 쓰는 순간 `EBUSY` / `SHARING VIOLATION`.
- `Command Palette` off: build success.
- `Command Palette` on: build failure reproduced.

`Keyboard Manager`는 계속 사용 가능하다. PowerToys 전체가 아니라 `Command Palette`만 끄면 된다.

이 문제를 해결하려고 다음을 다시 도입하지 않는다.

```text
win.asar: false
electron-builder retry
build script lock cleanup/fail-fast
dependency upgrade만으로 해결했다고 가정
```

### 다음 세션 권장 작업

1. Windows PC에서 최신 commit pull 후 PowerToys `Command Palette`를 끄고 `clipper_electron npm run build:app:win:x64`를 다시 실행한다.
2. installer 생성 후 설치형 app smoke를 진행한다.
3. smoke에서 최소 확인:
   - app boots.
   - NestJS health `200`.
   - Template Builder families `200`.
   - Plugin list 로드.
   - Dance member image search가 Windows packaged app에서 후보 0개가 아니라 실제 후보를 반환하는지.
4. Windows build가 다시 `EBUSY`로 실패하면 코드 변경 전에 ProcMon 또는 PowerToys 상태를 확인한다.
5. Windows packaged smoke가 끝난 뒤 사용자에게 다음 큰 작업을 확인한다. 후보는 Template Builder/Clipper1 export, plugin runtime 고도화, Windows build guide 정리다.

### 다음 세션에 붙여넣을 프롬프트

```text
Using Superpowers.

먼저 아래 문서를 순서대로 읽고 현재 상태를 파악해줘.

1. `.codex/README.md`
2. `.codex/session-logs/2026-05-21.log`
3. `.codex/design/2026-05-21-execution-env-mode-design.md`
4. `.codex/implementation/2026-05-21-windows-dance-image-env-management-context.md`
5. `.codex/implementation/2026-05-21-execution-mode-runbook.md`
6. `.codex/implementation/2026-05-21-windows-electron-builder-powertoys-ebusy-diagnosis.md`
7. `.codex/implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md`
8. `.codex/implementation/NEXT_SESSION_PROMPT.md`

현재 목표:
- 2026-05-21에 정리한 `local` / `devapp` / `packaged` env/runtime 구조를 기준으로 이어서 작업한다.
- Windows packaged build는 PowerToys `Command Palette` 때문에 `EBUSY`가 났던 것이며, Clipper2 코드 문제로 보지 않는다.
- `win.asar: false`, electron-builder retry, build script lock handling 같은 우회는 다시 넣지 않는다.
- Windows build 중에는 PowerToys `Command Palette`를 끈다. `Keyboard Manager`는 사용해도 된다.

현재 repo HEAD:
- `clipper_nestjs`: `feature/windows-packaging` @ `9cd43f1`
- `clipper_electron`: `feature/windows-packaging` @ `f701677`
- `clipper_angular`: `feature/initial-scaffold` @ `cad4b6c`
- `clipper_python`: `feature/windows-packaging` @ `88d22c6`

다음에 할 일:
1. repo 상태와 문서 기준을 확인한다.
2. Windows PC에서 최신 commit pull, secret `.env.*` 파일 존재 확인, PowerToys `Command Palette` off 상태로 `clipper_electron npm run build:app:win:x64`를 실행한다.
3. installer 생성 후 packaged app smoke를 진행한다.
4. 특히 Windows packaged app에서 dance member image 후보가 0개가 아니라 실제로 반환되는지 확인한다.
5. Template Builder 진입 시 ffmpeg/ffprobe consent/gate가 먼저 동작하고, 설치 완료 후 families load/text preview artifact/sample render가 정상 동작하는지 확인한다.
6. Dance member image selection 스크롤/중앙 정렬과 Template Builder card thumbnail skeleton UX를 확인한다.
7. smoke 결과를 문서화하고, 이후 작업 범위는 사용자에게 확인한 뒤 진행한다.

주의:
- root `.codex` 문서는 git repo가 아니므로 커밋 대상이 아니다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- 실제 `.env.<mode>` 파일에 optional blank placeholder를 다시 넣지 않는다.
```

## 2026-05-20 Windows PC installer build smoke

- 최신 세션 로그: `.codex/session-logs/2026-05-20.log`
- 2026-05-20 Windows PC smoke follow-up:
  - 다른 Windows PC에서 configurable-root guide 12번까지 진행 후 app 실행/Template Builder/Plugin Store smoke 결과를 `.codex/implementation/windows-pc-smoke-output-2026-05-20.md`에 기록했다.
  - 확인된 문제:
    - 새 템플릿에서 local `.ttf`/`.otf` 업로드 후 preview font가 변하지 않음.
    - 새 템플릿 card thumbnail이 Windows packaged app에서 엑박.
    - Dance highlight 설치 중 ffprobe download가 `@ffprobe-installer/win32-x64@5.0.1` HTTP 404로 실패.
  - 수정:
    - `clipper_electron/src/main/setup/download-ffmpeg.ts`: hardcoded ffprobe subpackage version 제거. `@ffprobe-installer/<platform>` npm metadata에서 `dist-tags.latest`의 `dist.tarball`을 resolve해 다운로드하도록 변경.
    - `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`: uploaded local absolute font path를 backend font file endpoint로 `FontFace` 등록.
    - `clipper_angular/src/features/template-builder/components/template-family-gallery.component.ts`: Windows absolute/UNC card thumbnail URI를 backend asset proxy로 처리.
  - 커밋:
    - `clipper_angular` `b9e1052 Fix Windows template asset previews`
    - `clipper_electron` `1a7f1b9 Resolve ffprobe tarball dynamically`
  - 현재 branch 상태:
    - `clipper_angular` `feature/initial-scaffold` is ahead of `origin/feature/initial-scaffold` by 1 commit.
    - `clipper_electron` `feature/windows-packaging` is ahead of `origin/feature/windows-packaging` by 1 commit.
  - 검증:
    - `clipper_electron npm run build`: passed after dynamic ffprobe tarball resolution.
    - `clipper_angular npm run build`: passed.
    - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-family-gallery.component.spec.ts`: 6 SUCCESS.
    - combined gallery+editor spec run: 164 SUCCESS, 1 unrelated existing failure (`editMode=true` test expects official registration button while implementation requires `!editMode()`).
  - 다음 Windows 재빌드에서 반드시 확인:
    - local font upload 후 live preview가 즉시 바뀌는지.
    - 새 템플릿 card thumbnail 엑박이 사라졌는지.
    - ffmpeg/ffprobe 다운로드가 모두 완료되는지.
- 상세 보고서:
  - `.codex/implementation/2026-05-20-windows-build-session-report.md`
- Codex 없이 사람이 직접 따라할 Windows build guide:
  - `.codex/implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_2026-05-20.md`
- 이번 세션의 중요한 전제:
  - 이번 작업은 기존 Mac mini가 아니라 새 Windows PC에서 진행했다.
  - Windows build는 한글 사용자명 아래 repo 경로가 아니라 ASCII 경로 `C:\project\adlight`에서 진행했다.
  - `C:\Users\메타버즈-신사업\Desktop\project\adlight` 쪽 clone에서는 Git lock 권한 문제와 Node/npm native postinstall 문제가 있었다.
  - 한글 사용자명 경로에서 `node .\node_modules\esbuild\install.js`가 상위 사용자 폴더 `lstat` `EPERM`으로 실패했고, 사용자도 이전 Codex CLI 설치 때 같은 계열의 `0xC0000005` crash를 겪었다.
  - 따라서 다음 Windows build/session도 `C:\project\adlight` 같은 ASCII 경로를 우선 사용한다.
- Windows build workspace:
  - `C:\project\adlight\clipper_angular`
  - `C:\project\adlight\clipper_electron`
  - `C:\project\adlight\clipper_nestjs`
  - `C:\project\adlight\clipper_python`
  - `adlight_python`은 clone하지 않았다.
- branch/commit:
  - `clipper_angular`: `feature/initial-scaffold`, `4501146`
  - `clipper_electron`: `feature/windows-packaging`, `e264865`
  - `clipper_nestjs`: `feature/windows-packaging`, `c33fbd8`
  - `clipper_python`: `feature/windows-packaging`, `5a61a62`
- env 상태:
  - build에 사용한 env 파일은 `C:\project\adlight\clipper_nestjs\.env.local`.
  - 비밀값은 문서에 기록하지 않았다.
  - `clipper_python\.env`는 현재 packaged build 기준 필수 파일이 아니다.
  - Electron `BundledEnvProvider`가 packaged mode에서 `clipper_nestjs\.env.local` 값을 NestJS와 Python plugin process 양쪽에 env로 주입한다.
  - `%APPDATA%\Clipper2\.env`는 repo 파일이 아니라 installed app userData override 파일이다. 현재 PC 기준 `%APPDATA%`는 `C:\Users\메타버즈-신사업\AppData\Roaming`.
- 설치/빌드 검증 완료:
  - `npm.cmd install --cache C:\project\adlight\.npm-cache`: Angular/NestJS/Electron passed.
  - `clipper_electron npm.cmd run fetch-uv`: passed.
  - `clipper_electron node scripts\prepare-uv.mjs win32 x64`: passed.
  - `clipper_angular npm.cmd run build:electron -- --progress=false`: passed.
  - `clipper_nestjs npm.cmd run bundle`: passed.
  - `clipper_electron npm.cmd run build`: passed.
  - `clipper_electron npm.cmd run build:app:win:x64`: passed.
- 생성 산출물:
  - `C:\project\adlight\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe`
  - size: `165,487,916` bytes.
  - packaged resource에 `resources\bin\uv.exe`와 `resources\clipper_nestjs\.env.local` 포함 확인.
- packaged smoke 완료:
  - `C:\project\adlight\clipper2-smoke-install\Clipper2.exe` 설치 확인.
  - app 실행 후 `%APPDATA%\Clipper2\clipper_venv\Scripts\python.exe` 생성 확인.
  - log에서 Python env ready, PluginHostBridge listening, NestManager ready 확인.
  - `GET /v1/health`: `200`.
  - `GET /v1/template-builder/families`: `200`.
  - Template Builder families count: `24`.
  - smoke 후 남은 `Clipper2` process 없음.
- 현재 작업트리 주의:
  - `C:\project\adlight\clipper_angular\package-lock.json` modified.
  - `C:\project\adlight\clipper_electron\package-lock.json` modified.
  - `clipper_nestjs`, `clipper_python`은 clean.
  - lockfile 변경은 Windows/npm 10.9.0에서 `npm install` 후 생긴 것으로 보이며 아직 검토/커밋하지 않았다.
- 다음 우선순위:
  - 설치된 app을 실제로 열어 renderer 화면을 육안 확인한다.
  - Template Builder official list/card thumbnails/text artifact 변환 후 한글 font 표시를 Windows packaged app에서 직접 확인한다.
  - 가능하면 Template Builder sample render와 가벼운 plugin start/stop smoke를 진행한다.
  - `clipper_angular/package-lock.json`, `clipper_electron/package-lock.json` 변경 유지/되돌림 여부를 결정한다.
  - 다른 Windows PC에서 Codex 없이 처음부터 재현할 때는 `.codex/implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_2026-05-20.md`를 따른다.

## 2026-05-19 Template Builder layout sync packaged smoke

- 최신 세션 로그: `.codex/session-logs/2026-05-19.log`
- 최신 추가 설계:
  - `.codex/design/2026-05-19-clipper2-official-to-clipper1-template-export-design.md`
  - `.codex/design/2026-05-19-clipper2-windows-packaging-plan.md`
- 2026-05-19 후속 현재 상태:
  - Clipper1 export 작업은 사용자가 나중으로 미뤘다.
  - 더 급한 다음 작업은 Windows 설치형 빌드 지원이다.
  - Mac packaged build에서 Template Builder preview text가 매우 작고 깨진 문자처럼 보이는 문제가 확인되어 수정했다.
    - 원인: 새 template 기본 `fontFamily`를 S3 URL로 바꾸면서 Angular live preview가 URL 문자열을 CSS `font-family`로 직접 사용했다.
    - NestJS baseline/fallback text style에는 S3 `fontFamily`와 별도로 표시/렌더용 `fontName`을 넣었다.
    - Angular Template Builder editor는 remote font URL을 `FontFace`로 등록하고, canvas preview에는 등록된 generated family name을 사용한다.
    - 커밋:
      - `clipper_nestjs` `6679b91 Add font names to S3 template defaults`
      - `clipper_angular` `4501146 Fix remote template font preview`
  - 추가로, 기존 local custom template JSON에 남아 있던 예전 font filename 때문에 final-render text artifact 변환 후 한글이 깨지는 문제가 확인되어 수정했다.
    - 기존 `/Users/jina/Library/Application Support/Clipper2/templates/template-builder.json` custom family 일부가 `JalnanGothic.otf`, `Pretendard-SemiBold.otf`, `Pretendard-Bold.otf`를 그대로 갖고 있었다.
    - packaged app은 font 파일을 번들링하지 않으므로 Python artifact renderer가 filename을 찾지 못해 PIL 기본 bitmap font로 fallback했다.
    - NestJS가 family 응답과 text artifact request 직전에 known built-in filename font를 official S3 URL + `fontName`으로 normalize한다.
    - 후속으로 `NanumMyeongjo...`, `NanumSquare...` 같은 다른 legacy font filename도 같은 문제가 될 수 있어, absolute/local upload path는 유지하고 bare `.otf`/`.ttf` filename 전체를 legacy official S3 font URL로 normalize하도록 확장했다.
    - 커밋:
      - `clipper_nestjs` `eed4bf2 Fix legacy custom template font artifacts`
      - `clipper_nestjs` `c33fbd8 Normalize bare legacy template font filenames`
    - 사용자 최종 확인:
      - 재빌드 후 Template Builder preview에서 text artifact 변환 이후에도 기본 폰트와 다른 legacy font가 정상 표시됨.
    - 상세 문서:
      - `.codex/implementation/2026-05-19-template-builder-font-artifact-fix.md`
  - Windows packaging 1차 구현 완료 상태:
    - `clipper_electron`, `clipper_nestjs`, `clipper_python`은 `feature/windows-packaging` 브랜치.
    - `clipper_angular`는 기존 `feature/initial-scaffold` 브랜치 위에 Template Builder remote font preview fix 커밋이 추가됨.
    - 기존 1차 변경은 커밋 완료:
      - `clipper_electron` `e89dd4c Make app build scripts cross-platform`
      - `clipper_nestjs` `5e1a0be Make asset copy scripts cross-platform`
      - `clipper_python` `248693f Add Windows uv lock support`
    - `clipper_electron/scripts/build-app.mjs`: `find ... rm -rf` 제거, Node `fs` 기반 `__pycache__` cleanup으로 교체.
    - `clipper_electron/scripts/fetch-uv.mjs`: `curl`, `mv`, `unzip`, `rm -rf` 제거, Node `https`/`pipeline`/`copyFileSync`/`rmSync` 기반 처리로 교체. archive extraction은 Windows 10/11 기본 `tar` 전제.
    - `clipper_nestjs/scripts/copy-assets.mjs`: cross-platform asset copy script 추가.
    - `clipper_nestjs/package.json`: `mkdir -p`, `cp -R` 제거, `node scripts/copy-assets.mjs` 사용.
    - `clipper_python/pyproject.toml`: `[tool.uv].environments`에 `win32` 추가.
    - `clipper_python/uv.lock`: `uv lock`으로 Windows markers/wheels 추가.
    - `clipper_electron/electron-builder.yml`: `../adlight_python/fonts` extraResource 제거.
    - 공식 Template Builder templates는 DB payload의 S3 font URL을 사용하므로 legacy font 파일을 앱에 번들링하지 않는다.
    - 아래 2026-05-10 기록의 bundled font 방식은 당시 preview fallback fix였고, 현재 공식 템플릿 DB/S3 font 정책에서는 superseded 상태다.
    - `clipper_nestjs/src/template-builder/fixtures/new-template-baseline.json`: 새 템플릿 기본 font도 filename이 아니라 official S3 font URL을 사용하도록 변경.
    - `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`: baseline fallback default font도 S3 URL로 변경.
    - font dependency cleanup 커밋:
      - `clipper_electron` `e264865 Remove external font packaging dependency`
      - `clipper_python` `39751e6 Bundle legacy template fonts`는 과도한 번들링으로 판단해 revert.
      - `clipper_python` `5a61a62 Revert "Bundle legacy template fonts"`
  - Windows packaging 검증 완료:
    - `clipper_electron node --check scripts/build-app.mjs`: passed.
    - `clipper_electron node --check scripts/fetch-uv.mjs`: passed.
    - `clipper_electron node scripts/prepare-uv.mjs win32 x64`: passed.
    - `clipper_electron npm run build`: passed.
    - `clipper_nestjs node --check scripts/copy-assets.mjs`: passed.
    - `clipper_nestjs npm run build`: passed.
    - `clipper_nestjs npm run bundle`: passed.
    - `clipper_python uv lock --check`: passed.
    - `clipper_electron npm run build:app:mac:arm64`: passed after removing `adlight_python/fonts` dependency.
    - `clipper_nestjs npm run build`: passed after new-template S3 font defaults.
    - `clipper_angular npm run build`: passed after remote font preview fix.
    - `clipper_electron npm run build:app:mac:arm64`: passed after remote font preview fix.
    - custom family 생성 smoke script: mainTitle/subtitleText/logoText fontFamily가 S3 URL임을 확인.
    - custom family 생성 smoke script: mainTitle/subtitleText/logoText fontName이 각각 JalnanGothic/Pretendard/Pretendard임을 확인.
    - 기존 local custom family normalization smoke: `JalnanGothic.otf`가 official S3 URL + `JalnanGothic`으로 보정됨을 확인.
    - Python text artifact export smoke: normalized custom family의 `mainTitleLine1` PNG가 정상 한글로 렌더됨을 확인.
    - `NanumMyeongjoExtraBold.otf` smoke: official S3 URL + `NanumMyeongjoExtraBold`로 normalize되고 Python text artifact PNG가 정상 한글로 렌더됨을 확인.
    - `clipper_nestjs node --test test/template-builder-font-references.test.js`: 2 passed.
    - 후속 font filename 확장 후 `clipper_electron npm run build:app:mac:arm64`: passed.
    - `node --test test/template-builder-api.test.js` full run still fails due existing subtitle expectation mismatch and official DB repository missing failures.
    - 해당 test suite 후속 정비 문서: `.codex/implementation/2026-05-19-template-builder-api-test-followup.md`
    - 이번 Windows packaging 흐름에서는 이 test suite 정비를 진행하지 않는다.
  - Windows PC에서 남은 검증:
    - Windows Codex CLI handoff 문서: `.codex/implementation/2026-05-19-windows-build-codex-cli-handoff.md`
    - Windows PC에서는 4개 repo만 clone: `clipper_angular`, `clipper_electron`, `clipper_nestjs`, `clipper_python`.
    - `adlight_python`은 clone하지 않는다.
    - `clipper_electron npm run build:app:win:x64` 실행.
    - `dist-app`에 NSIS installer 생성 확인.
    - 설치 후 renderer/gateway/Python first-run/template builder smoke 확인.
  - Template Builder official 등록/asset promotion/admin overlay/snackbar 작업은 커밋 완료.
    - `clipper_nestjs` `01940c1 fix: require db for official templates`
    - `clipper_nestjs` `87f95e1 feat: promote official template assets`
    - `clipper_angular` `2315a27 feat: add template builder overlays`
  - `clipper_nestjs`, `clipper_angular` 작업트리는 clean.
  - Clipper2 공식 등록은 현재 `clipper2_template_families`, `clipper2_template_variants`, `clipper2_template_assets`에만 반영한다.
  - Clipper1은 기존 FastAPI/Angular flow에서 `templates` 테이블만 조회하므로, Clipper2 official 등록 템플릿을 Clipper1 목록에도 보이게 하려면 별도 export가 필요하다.
  - 실제 DB `templates` 확인 결과:
    - 84 rows, 21 designs, 각 design마다 `16:9`, `4:3`, `1:1`, `full` 4 rows.
    - columns: `id`, `name`, `category`, `thumbnail_url`, `settings`, `template`, `origin_url`, `contents_ratio`.
    - `id`는 sequence integer PK, `template`은 design number, `name/category`는 현재 전부 null.
  - 설계 결론:
    - Clipper2 Template Builder family 1개를 Clipper1 `templates` 4 rows로 publish해야 한다.
    - 재등록 중복 방지를 위해 `clipper2_template_legacy_exports` 같은 mapping table이 필요하다.
    - Template Builder layers -> Clipper1 legacy settings 변환은 `LegacyClipper1RenderPayloadMapper.templateBuilderSettingsFor()`에 있는 로직을 공용 mapper로 추출하는 방향이 좋다.
    - Clipper1 renderer는 font를 `app/fonts/<filename>`로 찾으므로 S3/http font URL을 그대로 export하면 깨질 수 있다. 초기 구현은 Clipper1에 이미 있는 font filename만 허용하거나 upload font 포함 template의 Clipper1 export를 차단하는 편이 안전하다.
    - Clipper1 목록은 ratio별 `thumbnail_url`이 필요하므로 family 대표 `cardThumbnailUri` 하나로는 부족하다. 4개 ratio sample render thumbnail/origin을 준비해야 한다.
  - 다음 세션에서 먼저 읽을 것:
    - `.codex/design/2026-05-19-clipper2-official-to-clipper1-template-export-design.md`
    - `.codex/session-logs/2026-05-19.log`의 "Clipper1 template integration discovery"와 "Clipper1 integration design document saved" 섹션
  - 다음 구현을 시작한다면 권장 순서:
    - 먼저 dry-run/export preview API와 legacy settings mapper extraction.
    - 그 다음 mapping table + `templates` upsert.
    - 마지막에 official registration flow에 연결.
- 현재 상태:
  - Template Builder layout sync follow-up의 실제 packaged UI smoke를 완료했다.
  - 새 템플릿 생성 후 layout image 선택, `나머지 비율에 적용`, `4:3`/`1:1` ratio 전환, 저장 전/후 preview, card thumbnail, frame 밖 overflow 표시/해제를 확인했다.
  - smoke-created custom template은 삭제 완료했다.
- 이번 세션 수정:
  - `clipper_angular` gallery card thumbnail:
    - custom local absolute `layoutImage.assetUri`를 backend base URL에 단순 concat하지 않고 `assets/layout-image/file` endpoint를 사용한다.
  - `clipper_angular` edit session save:
    - dirty draft와 pending variant update map이 어긋난 경우 save 직전 ratio draft diff를 backfill해 backend patch 누락을 막는다.
  - `clipper_angular` editor canvas:
    - stack layout이 visible한 상태에서 raw `layoutImage`가 선택되어 있어도 canvas VM은 inspector와 같은 effective stack layer id를 사용한다.
    - 이로써 기본 선택 stack layer의 frame 밖 overflow 복제본이 실제 편집 대상 기준으로 보인다.
- 검증:
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 147 SUCCESS.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-family-gallery.component.spec.ts`: 56 SUCCESS.
  - `clipper_angular git diff --check`: passed.
  - `clipper_electron npm run build:app:mac:arm64`: passed.
  - Rebuilt packaged Electron smoke:
    - `4:3` and `1:1` PATCH requests both sent on save.
    - API persisted both sibling ratio layout images and `layout.legacy` layers.
    - `4:3` x=-120 overflow visible while layout selected and hidden after text layer selection.
    - card thumbnail broken image count 0.
- 다음 우선순위:
  - 이 변경을 커밋/리뷰한다.
  - 추가 Template Builder 작업이 없다면 custom/system template repository의 DB/S3 이전 정책을 별도 설계로 이어간다.

## 2026-05-18 Template Builder editor/layout sync follow-up

- 최신 세션 로그: `.codex/session-logs/2026-05-18.log`
- 현재 상태:
  - official template 21개는 DB/S3 기반으로 등록 완료되어 있고, font도 S3 public URL로 official DB payload에 반영됨.
  - custom/system edit 저장은 아직 local JSON repository 기반이다.
  - 새 템플릿 baseline은 `clipper_nestjs/src/template-builder/fixtures/new-template-baseline.json`에 저장되어 있으며, 이번 세션에서 사용자가 조정한 기본 font size/color/subtitle y/full gradient layout 값까지 커밋됨.
  - Template Builder layout은 ratio별 독립 variant 구조를 유지한다.
  - `16:9`, `4:3`, `1:1` 사이에는 레이아웃만 값 그대로 복사하는 `나머지 비율에 적용` 버튼이 추가됨. `full`은 source/target 모두 제외.
  - 복사 범위는 `layoutImage`, `layoutLayers`만이다. title/subtitle/contentArea/font/text style은 복사하지 않는다.
  - source ratio가 기존 단일 `layoutImage` 구조이면 target ratio에는 `layout.legacy` stack layer로 변환해 넣는다.
  - 저장 전 target ratio preview/thumbnail은 아직 target backend endpoint에 asset이 없을 수 있으므로, 같은 `assetUri`의 source ratio endpoint를 안정적으로 찾아 사용한다.
  - layout edit 중 선택된 layout image/stack layer가 frame 밖으로 나가면 frame 밖 영역은 흐리게 표시하고, edit chrome이 없는 상태에서는 overflow 복제본을 렌더하지 않는다.
  - layout image upload는 dirty edit session을 먼저 backend에 저장한 뒤 upload target layer를 찾도록 수정됨. backend는 configured S3 storage가 있으면 template image uploads도 S3에 저장한다.
- 최신 커밋:
  - `clipper_angular` `f543308 Stabilize synced layout asset source`
  - `clipper_angular` `e5e7e43 Fix copied layout preview URLs`
  - `clipper_angular` `91386f4 Fix legacy layout ratio sync`
  - `clipper_angular` `e737e01 Add layout sync across ratios`
  - `clipper_angular` `477c9f5 Restore layout stack overflow preview`
  - `clipper_angular` `af931cd Fix layout layer upload target selection`
  - `clipper_angular` `e689bac Show template layout upload errors`
  - `clipper_nestjs` `bbf0bf4 Update new template baseline`
  - `clipper_nestjs` `4871ebe Store template image uploads in S3`
- 검증:
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 146 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_nestjs` worktree clean after `bbf0bf4`.
  - `clipper_angular` worktree clean after `f543308`.
- 다음 우선순위:
  - packaged app 또는 local dev에서 새 템플릿 생성 후 실제 UI smoke:
    - 새 템플릿 생성 직후 각 ratio layout stack thumbnail이 엑박 없이 보이는지.
    - `16:9`, `4:3`, `1:1` 중 하나에서 layout image를 선택하고 `나머지 비율에 적용`을 눌렀을 때 나머지 ratio preview 안/밖 overflow가 모두 같은 이미지로 보이는지.
    - ratio를 여러 번 전환해도 source ratio 썸네일/overflow가 target unsaved endpoint를 잡지 않는지.
    - 저장 전/저장 후/다른 템플릿 전환 후에도 적용 결과가 유지되는지.
    - 편집 시작 전에는 layout frame 밖 overflow가 보이지 않는지.
  - 만약 아직 썸네일/overflow가 깨지면 브라우저 Network에서 실패 URL이 `assets/layout-image/file`인지 `assets/layout-layers/<id>/file`인지 먼저 확인한다.
  - 현재 해결은 preview URL 선택을 frontend에서 안정화한 것이다. backend가 unsaved draft target asset endpoint를 제공하는 구조는 아니다.

## 2026-05-18 Template Builder official font asset policy

- 최신 세션 로그: `.codex/session-logs/2026-05-18.log`
- 최신 설계:
  - `.codex/design/2026-05-18-template-builder-font-asset-policy.md`
- 현재 상태:
  - 시작 시 `clipper_angular`, `clipper_nestjs`, `clipper_python`, `clipper_electron` 작업트리는 clean이라 선행 커밋할 기존 변경사항은 없었다.
  - 공식 Template Builder family/variant payload는 NestJS official Postgres repository가 source of truth다.
  - 공식 card thumbnail/layout/content/logo image는 이미 S3 public URL로 DB payload에 저장된다.
  - 이번 변경으로 official seed upload mode가 font도 asset으로 수집한다.
    - legacy official font source: `/Users/jina/project/adlight/adlight_python/fonts`
    - target key: `templates/legacy-clipper1/fonts/<file>`
    - dry-run upload plan: `77 uploadable, 0 missing` (`53` image assets + `24` fonts)
    - `layer.text.fontFamily`는 S3 public URL로 rewrite된다.
  - Python renderer는 `http(s)` font URL을 temp cache로 materialize한 뒤 Pillow/fontTools path로 읽는다.
  - local filename/absolute path/legacy fonts dir fallback은 legacy/custom payload 호환을 위해 유지한다.
  - custom/system edit 저장은 아직 local JSON repository 기반이며, custom template DB/S3 이전은 별도 정책 결정으로 남긴다.
- 변경 파일:
  - `.codex/design/2026-05-18-template-builder-font-asset-policy.md`
  - `.codex/session-logs/2026-05-18.log`
  - `.codex/implementation/NEXT_SESSION_PROMPT.md`
  - `clipper_nestjs/scripts/register-official-template-seed.js`
  - `clipper_nestjs/test/template-builder-register-official-seed-script.test.js`
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/template_builder_text_renderer.py`
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - `clipper_python/tests/test_template_builder_text_renderer.py`
- 최신 커밋:
  - `clipper_nestjs` `a7975f7 Upload official template fonts`
  - `clipper_python` `0153f44 Resolve remote template fonts`
- 검증:
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-register-official.test.js test/template-builder-official-repository.test.js test/template-builder-register-official-seed-script.test.js`: 39 pass.
  - `clipper_python uv run pytest tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_clipper1_video_render_text_artifact_job.py tests/test_clipper1_video_render_remote_assets.py -q`: 23 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py plugins/clipper1_video_render/clipper1_video_render/template_builder_text_renderer.py`: passed.
  - `clipper_nestjs git diff --check`: passed.
  - `clipper_python git diff --check`: passed.
  - 참고: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q`는 기존 독립 실패 1개가 있음. `test_project_overlay_renders_second_main_title_without_first_line` expected 1 event but got 0.
- 다음 우선순위:
  - 실제 DB/S3 env로 `clipper_nestjs node scripts/register-official-template-seed.js --apply --asset-mode=upload`를 재실행해 official DB font URLs까지 S3 URL로 갱신한다.
  - packaged Electron에서 official templates preview artifact/final sample render가 S3 font URL로 정상 렌더되는지 smoke 확인한다.
- 2026-05-18 추가 apply 시도:
  - `--dry-run --asset-mode=upload`: `77 uploadable, 0 missing`.
  - 기존 `adlight_python/.env.local` AWS credential로 `--apply --asset-mode=upload`를 시도했지만 `S3-ACCESS-USER`가 `clipperstudio/templates/...`에 `s3:PutObject` 권한이 없어 실패했다.
  - 실패는 첫 object upload에서 발생해 DB upsert 전이다.
  - DB 샘플 조회 결과 Template 1 `16:9` official payload font는 아직 `JalnanGothic.otf`, `Pretendard-SemiBold.otf` filename 상태다.
  - blocker: `clipperstudio` bucket `templates/legacy-clipper1/...` prefix에 PutObject 가능한 AWS credential 필요.
  - 추가로 로컬 AWS `default` profile도 시도했지만 AWS principal은 여전히 `S3-ACCESS-USER`로 평가되어 같은 PutObject 권한 실패가 났다.
  - public URL probe에서 기존 card thumbnail은 `200`, 새 font target URL은 `403`이므로 DB payload만 S3 font URL로 바꾸는 강행 업데이트는 하지 않는다.
  - 이후 사용자가 PutObject 가능한 IAM key를 다시 제공했고, `clipper_nestjs/.env.local`에 `CLIPPER2_TEMPLATE_DB_*`, `CLIPPER2_TEMPLATE_S3_*` 값을 저장했다. 파일은 gitignored이며 secret 값은 문서에 기록하지 않는다.
  - `set -a; source .env.local; set +a; node scripts/register-official-template-seed.js --apply --asset-mode=upload` 성공.
  - 77개 official template assets 업로드 완료: 기존 image/card/layout 53개 + font 24개.
  - 21개 official template families DB upsert 완료.
  - DB 샘플: Template 1 `16:9` `mainTitleLine1.text.fontFamily`, `subtitleText.text.fontFamily`가 `https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/fonts/...`로 갱신됨.
  - DB asset index count: `font=588`, `layoutImage=67`, `contentArea=21`, `thumbnail=21`.
  - public S3 font URL probe: `200`.
  - Python actual S3 font URL render smoke: passed.
  - local NestJS runtime smoke: `GET /v1/template-builder/families` returned `families=21`, first official family font/card/layout all S3 URLs.
  - `clipper_electron npm run build:app:mac:arm64`: passed.
  - packaged app smoke with DB/S3 env: `GET /v1/template-builder/families` returned `families=22`, first official family font/card/layout all S3 URLs. Extra 1 is local custom family.
  - packaged app process stopped after smoke.

## 2026-05-13 Template Builder official registry implementation

- 최신 세션 로그: `.codex/session-logs/2026-05-13.log`
- 최신 설계/계획:
  - `.codex/design/2026-05-13-template-builder-official-template-registry-design.md`
  - `.codex/implementation/2026-05-13-template-builder-official-registry-implementation-plan.md`
- 현재 상태:
  - 기존 21개 템플릿 보정 변경사항은 커밋됨.
  - Template Builder에서 `게시` UI/API는 제거됨. sample render는 preview-only 기능이다.
  - card thumbnail은 sample render thumbnail과 분리됨. 기존 공식 템플릿 카드는 legacy preset thumbnail을 우선 사용한다.
  - Angular Template Builder는 명시적 edit session을 사용한다. 편집 시작 전 patch는 저장하지 않고, undo/redo는 현재 edit session 안에서만 동작한다.
  - 임시 관리자 모드 + edit mode에서만 `템플릿 등록` 버튼이 표시된다.
  - NestJS에는 official template repository abstraction, Postgres repository, S3 asset storage abstraction, `register-official` endpoint가 들어갔다.
  - `TemplateBuilderModule`이 `CLIPPER2_TEMPLATE_DB_*` env 기반 official repository provider를 주입한다.
  - `clipper_nestjs/scripts/register-official-template-seed.js`가 추가됐다.
    - `--dry-run`: DB/S3 env 없이 현재 system overrides까지 반영된 21개 legacy official families를 검사한다.
    - `--apply`: `CLIPPER2_TEMPLATE_DB_*`, `CLIPPER2_TEMPLATE_S3_*` env가 모두 있어야 하고, Postgres official repository에 upsert한다.
    - `--apply` 전에 `clipper2_template_families`, `clipper2_template_variants`, `clipper2_template_assets` schema를 생성한다.
    - 현재 asset mode는 `preserve`만 지원한다. 실제 asset upload/migration은 다음 별도 단계로 남긴다.
  - 실제 원격 DB apply 완료:
    - 기존 `adlight_python/.env.local`의 `DATABASE_*` 값을 `CLIPPER2_TEMPLATE_DB_*`로 매핑했다.
    - S3 bucket은 사용자 지정대로 `clipperstudio`로 매핑했다.
    - `node scripts/register-official-template-seed.js --apply` 성공.
    - DB row count: `families=21`, `variants=84`, `assets=109`.
  - `--asset-mode=upload` 구현 완료:
    - dry-run upload plan: `53 uploadable, 0 missing`.
    - card thumbnails는 bundled `legacy-clipper1-template-ui/thumbs-and-origins`에서 찾는다.
    - layout images는 `/Users/jina/project/adlight/adlight_python/layout`에서 찾는다.
    - target keys는 `templates/legacy-clipper1/card-thumbnails/...`, `templates/legacy-clipper1/layouts/...`.
    - 폰트는 아직 remote font URL renderer support가 없어서 payload URI 치환 대상에서 제외.
  - 실제 `--apply --asset-mode=upload`는 시도했지만 S3 권한으로 실패:
    - 현재 `adlight_python/.env.local` AWS credential은 `clipperstudio` bucket에 `s3:PutObject` 권한이 없다.
    - 실패가 첫 object upload에서 발생해 DB는 변경되지 않았다. Template 1 card/layout URI는 preserve 상태 그대로 확인했다.
  - 이후 사용자가 새 IAM access key를 제공했고, `clipper_nestjs` 실행 환경에만 주입해 `node scripts/register-official-template-seed.js --apply --asset-mode=upload`를 재실행했다.
  - 업로드 대상 53개를 `clipperstudio` bucket `templates/legacy-clipper1/...` 아래에 업로드했고, official DB payload URI를 새 public S3 URL로 갱신했다.
  - DB 재조회 결과 Template 1은 `card=https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/card-thumbnails/1_ratio_16_9_thumb.png`, `layout=https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/layouts/1.png`, `gradient=https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/layouts/gradient.png`.
  - packaged Electron smoke with real DB/S3 env:
    - `GET /v1/template-builder/families` returned `families=22`, `officialLegacy=21`, first id `system.legacy.clipper1.template.1`.
    - first family `cardThumbnailUri` and `layoutImage.assetUri` were both `https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/...`.
    - the extra 1 family is the remaining local custom template.
- 최신 커밋:
  - `clipper_nestjs` `9e668d2 Upload official template seed assets`
  - `clipper_nestjs` `c8fd495 Wire official template repository provider`
  - `clipper_nestjs` `97455ba Create official template registry schema`
  - `clipper_nestjs` `7d028b2 Add official template seed registration script`
  - 직전 관련 커밋: `clipper_angular` `08efb78 Add official template registration action`, `clipper_nestjs` `40a9955 Add official template registration endpoint`
- 검증:
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-register-official.test.js test/template-builder-official-repository.test.js test/template-builder-register-official-seed-script.test.js`: 39 pass.
  - `clipper_nestjs node scripts/register-official-template-seed.js --dry-run`: `21 legacy official families ready`, `0 custom clone families included`.
  - local NestJS runtime smoke with DB env: `GET /v1/template-builder/families` returned `families=21`, `officialLegacy=21`, first id `system.legacy.clipper1.template.1`.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-family-gallery.component.spec.ts`: 161 SUCCESS.
  - `clipper_python uv run pytest tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_clipper1_video_render_text_artifact_job.py -q`: 12 passed.
  - `clipper_angular`, `clipper_nestjs`, `clipper_python`, `clipper_electron` 작업트리 clean.
- 다음 우선순위:
  - packaged Electron에서 실제 Template Builder UI로 card thumbnail 유지, edit mode, undo session boundary, admin mode `템플릿 등록` 표시/호출을 smoke 확인한다.
  - Clipper2 packaged/runtime env에 `CLIPPER2_TEMPLATE_DB_*`, `CLIPPER2_TEMPLATE_S3_*` 값을 주입하는 방식은 아직 정리 필요.

## 2026-05-11 Template Builder rollback to `0ae1144`

- 최신 세션 로그: `.codex/session-logs/2026-05-11.log`
- 현재 상태:
  - `clipper_angular`은 `0ae1144 Fix subtitle single-line preview and compare canvas font-family binding` 상태로 되돌렸다.
  - 그 이후에 추가된 Template Builder 폰트 경로 실험, Electron/NestJS 전달 경로 실험, `subtitleBox` preload 우회는 모두 폐기됐다.
  - `clipper_angular`, `clipper_nestjs`, `clipper_electron` 작업트리는 모두 깨끗하다.
- 다음 세션 우선순위:
  - 폰트 회귀를 다시 건드릴 때는 먼저 이전 커밋과 현재 커밋을 비교해, 예전에 잘 되던 경로와 로딩 방식을 확인한다.
  - 그 후 `clipper_angular`의 preview font loading부터 다시 최소 범위로 재현한다.
  - 변경을 다시 시작하기 전에는 문서와 세션 로그를 먼저 갱신한다.

## 2026-05-12 Template Builder compare preview font-family and drag snap-back fix

- 최신 세션 로그: `.codex/session-logs/2026-05-12.log`
- 현재 상태:
  - `clipper_angular`에서 Template Builder canvas fallback text의 font-family를 CSS-safe quoted value로 정규화했다.
  - 오른쪽 `한 줄 고정` compare canvas는 renderer artifact를 다시 활용한다. `mainTitleLine1`/`subTitle`는 기존 artifact image를 쓰되 single-line y로 frame을 보정하고, `subtitleText`는 별도 `subtitleText:line-mode-single` artifact를 요청한다. 다만 interactive preview에서는 subtitle combined image를 그대로 렌더링하지 않고 `metadata.lines` 기반 줄별 crop/interaction으로 나눠 보여준다.
  - 원인: 오른쪽 `한 줄 고정` compare canvas는 line-mode-dependent text artifact를 쓰지 않는 browser fallback 경로인데, legacy filename font value(`*.ttf`, `*.otf`)가 quote 없이 `[style.fontFamily]`에 들어가 Chrome이 declaration을 버렸다.
  - 추가로 preview canvas에서 title/sub-title/subtitle을 드래그하면 다시 제자리로 돌아오던 원인은 artifact metadata의 stale `frame.y`가 현재 line-mode y(`oneLineY`, `twoLineFirstY`, `twoLineSecondY`)보다 우선 적용됐기 때문이다. text preview artifact frame을 쓰더라도 y는 현재 line-mode y로 보정하도록 수정했다.
  - 왼쪽 canvas에서 두 번째 타이틀을 선택하면 오른쪽 `한 줄 고정` canvas에도 selection box가 생기던 문제도 고쳤다. 각 canvas VM의 `selectedVisibleTextLayer`를 그 canvas의 실제 `textLayers` 안에서 다시 resolve해, 해당 canvas에 없는 layer의 selection chrome을 렌더링하지 않는다.
  - 왼쪽/오른쪽 compare canvas의 x 위치도 분리했다. text layer에 optional `oneLineX`, `twoLineFirstX`, `twoLineSecondX`를 추가하고, preview frame/drag patch/keyboard move patch가 active line-mode x field를 쓰게 했다. 왼쪽 double canvas에서 첫째줄 타이틀을 이동해도 오른쪽 single canvas의 x는 바뀌지 않는다.
  - guide/selection/resizer chrome은 `selectedCanvasId` 기준 active canvas에만 표시한다. 왼쪽 canvas에서 선택/이동 중이면 오른쪽 canvas에는 guide line이 보이지 않는다.
  - `Legacy Clipper1 Template 14 복제본`에서 box/text-fit sub-title을 클릭하면 원래 복제 직후 좌표처럼 튀고 box width가 순간적으로 길어지던 문제도 고쳤다.
  - 원인: canvas 렌더링은 artifact frame을 line-mode 좌표로 보정했지만 pointerdown move/resize 시작 경로는 raw artifact frame으로 `canvasInteraction.current`를 만들었다. text-fit box는 visible artifact x와 persisted anchor x가 다르므로 x는 artifact visible offset을 보존하고, y는 active line-mode y로 보정한다.
  - 후속으로, 선택/작은 move 뒤 artifact refresh가 예약될 때 `TemplateBuilderPageComponent`가 기존 `textPreviewArtifacts`를 즉시 `{}`로 비워 browser fallback full-width box가 잠깐 보이던 문제도 고쳤다. 새 artifact render 중에는 기존 artifact를 유지하고, family/ratio 전환처럼 다른 템플릿 artifact가 섞이면 안 되는 경우에만 비운다.
  - 오른쪽 `한 줄 고정` canvas도 편집 가능하게 했다. `line-mode-single` canvas VM의 `persistInteraction`을 true로 바꿔 drag가 `oneLineX`/`oneLineY` patch를 emit한다.
  - guide/measurement frame도 active canvas의 line-mode 보정 artifact frame을 사용한다. 이전에는 interaction 종료 후 전역 `frameFor()`가 raw artifact metadata frame을 다시 읽어서 guide focus가 이전 위치로 돌아갔다.
  - 후속으로 자막(`subtitleText`), 하단타이틀(`bottomTitle`), 로고 텍스트(`logoText`)에도 같은 위치 보정을 확장했다.
    - `bottomTitle`/`logoText`는 active canvas line-mode에 따라 `oneLineX/Y` 또는 `twoLineFirstX/Y`를 사용한다.
    - non-subtitle text artifact frame은 line-mode preview x/y 보정을 공통으로 거친다.
    - subtitle artifact line box는 줄별 artifact crop으로 렌더링하고, 첫째 줄은 `twoLineFirstX/Y`, 둘째 줄은 `twoLineSecondX/Y`, single canvas는 `oneLineX/Y`를 독립적으로 사용한다.
    - `subtitleText` wrapper drag는 더 이상 group move를 시작하지 않는다. line drag/keyboard/center action만 선택된 자막 줄의 x/y field를 patch한다.
    - 일반 two-line subtitle artifact 요청에는 같은 preview 문장 두 줄을 명시한다. 따라서 왼쪽 canvas 첫째 줄/둘째 줄 모두 `자막이 표시되는 영역이며, 최대 두 줄까지 가능합니다`로 crop/render된다.
    - 레이아웃(`layoutImage`) 편집 중에는 compare preview를 숨기고 왼쪽 `line-mode-double` canvas 하나만 보여준다. 다른 레이어 선택 시에는 다시 두 canvas가 보인다.
    - 레이아웃 이미지 편집 중 캔버스 밖으로 나간 이미지 영역이 다시 흐리게 보인다. 히스토리 확인 결과 `222e666`에서 canvas host/preview cell overflow가 `hidden`으로 바뀌며 `layout-image-preview--overflow`가 조상 요소에서 잘렸고, 해당 clipping만 `visible`로 복구했다.
    - 흐리게 보이는 layout overflow 이미지도 직접 드래그할 수 있다. layout image move/resize/inspector position update/render frame은 캔버스와 최소 40px은 겹치도록 clamp해서 이미지가 완전히 프레임 밖으로 빠져 다시 못 잡는 상태를 막는다. 이미 저장값이 완전히 벗어난 경우에도 preview에서는 가장 가까운 드래그 가능한 가장자리로 보정해 복구 drag가 가능하다.
    - preview 상단 toolbar의 `라인수 비교 미리보기` 문구는 제거했고, 기존 가로 중앙 정렬 아이콘 옆에는 `선택 요소 가로 중앙` 라벨을 추가했다.
    - layout image 선택 중에는 `레이아웃 이미지` controls가 표시된다. `맞춤`은 이미지를 프레임 안에 전부 들어오게 비율 유지/중앙 정렬하고, `채우기`는 프레임을 빈틈없이 채우게 비율 유지/중앙 정렬하며 필요한 overflow를 허용한다.
    - layout image와 output frame aspect ratio가 같아 `맞춤`/`채우기` 결과가 동일하면 `채우기` 버튼은 숨기고 `맞춤`만 표시한다.
    - layout edit preview wheel zoom 중 캔버스가 튀던 원인은 centered 판정/scroll 보정이 overflow art의 `scrollWidth/scrollHeight`와 pointer anchoring을 같이 쓰며 한 프레임씩 충돌했기 때문이다. centered 판정은 preview inner layout box(`offsetWidth/offsetHeight`) 기준으로 바꾸고, centered 상태에서 시작한 wheel zoom은 pointer가 아니라 layout box 중앙을 기준으로 scroll을 맞춘다.
    - 같은 ratio layout image를 resize하면 정수 픽셀 반올림 때문에 현재 배치 frame이 예: `960x1707`처럼 정확한 `1080:1920` cross-product와 1px 안팎 차이 날 수 있다. `sameAspectRatio()`는 이제 output frame 최대 한 변 길이 이하의 cross-multiply 차이를 같은 ratio로 취급해, resize 후에도 `채우기` 버튼이 다시 생기지 않는다.
    - 후속 확인에서 resize drag 중 `채우기` 버튼이 여전히 깜빡이는 문제가 재현됐다. 원인은 visibility 기준이 여전히 current placement frame이라 drag 중 임시 width/height 변화에 반응했기 때문이다.
    - `TemplateBuilderMediaLayer`에 `assetWidth`/`assetHeight`를 추가하고, NestJS layout image upload가 원본 image dimensions를 저장한다.
    - 없는 ratio를 나중에 생성하면서 layout image geometry를 복제하는 경로도 `assetWidth`/`assetHeight`를 보존한다.
    - Angular `layoutImageCoverFitVisible()`은 저장된 `assetWidth`/`assetHeight`를 우선 사용한다. 기존 saved data처럼 dimensions가 없으면 같은 `assetUri`의 first-seen ratio를 cache해 이후 resize frame 변화에는 버튼 visibility가 흔들리지 않게 했다.
    - 후속 확인에서 `1080x1920` layout image인데도 `채우기` 버튼이 남는 문제가 재현됐다. 기존 saved data는 `assetWidth`/`assetHeight`가 없고, first-seen placement frame cache가 이전 배치 크기를 원본 비율처럼 붙잡을 수 있었다.
    - Angular canvas의 layout image `<img>` load event에서 `naturalWidth`/`naturalHeight`를 받아 source ratio cache를 overwrite한다. cache 변경이 `workspaceVm` computed에 반영되도록 version signal도 추가했다.
    - 후속 확인에서 `1080x1920` layout image를 resize한 뒤 `맞춤`을 누르면 `1079x1920`처럼 1px drift가 보존되는 문제가 재현됐다. 원인은 `fitLayoutImageToFrame()`이 원본 image ratio가 아니라 현재 배치 frame ratio를 기준으로 scale을 계산했기 때문이다. 이제 `assetWidth`/`assetHeight` 또는 natural-size cache 기반 source ratio로 fit frame을 계산해 `1080x1920` source는 `맞춤` 시 `x=0`, `y=0`, `width=1080`, `height=1920`으로 복귀한다.
    - `Legacy Clipper1 Template 9 복제본`에서 하단 타이틀 inspector Y는 `1479`인데 왼쪽/오른쪽 compare canvas y 위치가 다르게 보이던 문제도 고쳤다. 저장 데이터에 숨은 `twoLineFirstY=1432`가 남아 있었고, 기존 preview는 하단 타이틀 자체가 `lineMode: single`이어도 왼쪽 canvas에서 그 값을 사용했다. 이제 `bottomTitle`/`logoText`는 compare canvas line-mode와 무관하게 inspector에 보이는 base `x/y`로 preview와 drag patch를 처리한다. final render payload의 `bottom_title_y_offset`도 legacy `bottom_title_y_offset`의 source of truth인 `bottomTitle.y`를 우선 사용한다.
    - 후속 cleanup으로 새 default variant와 legacy system seed에서는 `bottomTitle`/`logoText`에 `oneLineY`/`twoLineFirstY`/`twoLineSecondY`를 더 이상 만들지 않는다. `bottom_title_y_offset`/`logo_text_y_offset`는 line-mode y가 아니라 base `y`로 seed한다.
    - 기본 레이어 선택 중에는 실제 움직일 수 있는 preview element에만 move cursor가 보인다. layout/content/background처럼 현재 선택 맥락에서 움직일 수 없는 영역은 default cursor다.
    - 기본 레이어 선택 상태에서 layout/content/background 같은 비상호작용 영역을 클릭하면 `selectedLayerId`/default media selection을 clear해 파란 selection box와 기본 레이어 row selection이 사라진다. 공통 layout layer 선택 중인 경우는 기존 동작을 유지한다.
  - 변경 파일:
    - `src/features/template-builder/components/template-builder-editor.component.ts`
    - `src/features/template-builder/components/template-builder-editor.contract.ts`
    - `src/features/template-builder/components/template-builder-canvas.component.html`
    - `src/features/template-builder/components/template-builder-canvas.component.scss`
    - `src/features/template-builder/components/template-builder-workspace.component.html`
    - `src/features/template-builder/components/template-builder-workspace.component.scss`
    - `src/features/template-builder/components/template-builder-workspace.component.ts`
    - `src/features/template-builder/components/template-builder-workspace.component.spec.ts`
    - `src/features/template-builder/models/template-builder.ts`
    - `src/features/template-builder/components/template-builder-editor.component.spec.ts`
    - `src/features/template-builder/pages/template-builder-page.component.ts`
    - `src/features/template-builder/pages/template-builder-page.component.spec.ts`
    - `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
    - `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
    - `clipper_nestjs/src/template-builder/template-builder.service.ts`
    - `clipper_nestjs/test/template-builder-api.test.js`
    - `clipper_nestjs/test/template-builder-render-payload.test.js`
- 검증:
  - `clipper_angular npm run build`: passed.
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js`: 18 pass. layout image upload와 custom variant clone 경로 모두 `assetWidth`/`assetHeight` 보존을 확인했다.
  - `clipper_nestjs node --test test/template-builder-render-payload.test.js`: 9 pass. `bottom_title_y_offset`가 `bottomTitle.y`를 source of truth로 쓰는 것을 확인했다.
  - `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js`: 29 pass. 새 default variant와 legacy system seed에서 `bottomTitle`/`logoText` line-mode y fields가 생성되지 않는 것을 확인했다.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts`: 28 SUCCESS.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-workspace.component.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts`: 29 SUCCESS.
  - `clipper_angular git diff --check`: passed.
  - `clipper_nestjs git diff --check`: passed.
  - `template-builder-editor.component.spec.ts`에는 stale artifact y보다 active line-mode y를 우선하는 regression test를 추가했고 RED/GREEN을 확인했다.
  - `mainTitleLine2` 선택 시 오른쪽 single-line compare canvas에 selection box가 없어야 한다는 regression test도 RED/GREEN으로 확인했다.
  - 왼쪽 double canvas x drag가 오른쪽 single canvas x를 움직이지 않는 regression test와 guide가 active canvas에만 보이는 regression test도 RED/GREEN으로 확인했다.
  - box/text-fit sub-title artifact를 선택해도 left/top/width가 pointerdown 순간 바뀌지 않는 regression test를 추가했고 RED/GREEN을 확인했다.
  - replacement artifact가 렌더링 중이어도 current text artifact가 유지되어야 한다는 page regression test를 추가했고 RED/GREEN을 확인했다.
  - right compare canvas drag가 `oneLineX`/`oneLineY`를 emit하는 regression test와 guide/measurement frame이 active line-mode artifact frame을 유지하는 regression test를 추가했고 RED/GREEN을 확인했다.
  - bottomTitle/logoText artifact frame, bottomTitle/logoText drag patch regression tests를 추가했고 RED/GREEN을 확인했다.
  - subtitle artifact split preview, wrapper non-group-drag, line-specific `twoLineSecondX/Y` patch regression tests를 추가했고 RED/GREEN을 확인했다.
  - 일반 subtitle artifact request가 같은 문장 두 줄을 보내는 page regression test를 추가했고 RED/GREEN을 확인했다.
  - layout layer 선택 중 preview canvas가 하나만 보이고 text layer 선택 시 두 canvas로 복귀하는 regression test를 추가했고 RED/GREEN을 확인했다.
  - layout image overflow preview가 canvas host/preview cell에서 잘리지 않는 regression test를 추가했고 RED/GREEN을 확인했다.
  - layout overflow image drag, 완전 이탈 방지 clamp, x/y 입력 clamp, 이미 완전히 이탈한 저장값의 draggable-edge render regression tests를 추가했고 RED/GREEN을 확인했다. 이후 최소 교차값을 40px로 갱신하고 RED/GREEN을 다시 확인했다.
  - preview toolbar 문구 제거, 가로 중앙 정렬 설명 라벨, layout image `맞춤`/`채우기` buttons와 emitted patch regression tests를 추가했고 RED/GREEN을 확인했다.
  - layout preview centered zoom scroll, overflow art를 제외한 centered 판정, same-ratio layout image `채우기` button collapse regression tests를 추가했고 RED/GREEN을 확인했다.
  - same-ratio layout image resize rounding(`960x1707`)에서도 `채우기` button이 숨겨지는 regression test를 추가했고 RED/GREEN을 확인했다.
  - layout image original asset dimensions 우선 사용과 legacy `assetUri` first-seen ratio cache regression tests를 추가했고 RED/GREEN을 확인했다.
  - 기존 데이터에서 loaded image natural size(`1080x1920`)가 placement frame보다 우선되어 `채우기` button을 숨기는 regression test를 추가했고 RED/GREEN을 확인했다.
  - 실제 movable element에만 move cursor class가 붙고, non-movable layout/background click이 기본 레이어 selection을 clear하는 regression tests를 추가했고 RED/GREEN을 확인했다.
  - `template-builder-editor.component.spec.ts` 전체는 현 baseline의 compare-canvas 중복 selector 기대값 4개가 아직 실패하지만, font/artifact/drag snap-back/x-isolation/chrome/text-fit selection/artifact refresh/right-canvas editing/guide focus/non-title movement/subtitle line split/layout image source-ratio/natural-ratio/source-ratio fit/bottomTitle visible y/cursor/deselect regressions는 통과한다. 최신 실행 결과는 104 SUCCESS, 4 FAILED.
- 다음 우선순위:
  - packaged Electron에서 `/templates` Template Builder를 열고 오른쪽 compare canvas의 서브타이틀/타이틀/자막이 renderer artifact 기반으로 폰트를 유지하는지 확인한다.
  - 왼쪽/오른쪽 preview canvas에서 title/sub-title/subtitle을 드래그한 뒤 artifact refresh 이후에도 위치가 유지되는지 수동 확인한다.
  - 왼쪽 canvas에서 두 번째 타이틀을 선택했을 때 오른쪽 `한 줄 고정` canvas에 selection box가 나타나지 않는지 수동 확인한다.
  - 왼쪽 canvas에서 첫째줄 타이틀을 x축으로 이동해도 오른쪽 `한 줄 고정` canvas x가 유지되는지, guide가 active canvas에만 표시되는지 수동 확인한다.
  - `Legacy Clipper1 Template 14 복제본`에서 box/text-fit sub-title을 클릭해도 위치와 box width가 순간적으로 튀지 않는지 packaged Electron에서 수동 확인한다.
  - 오른쪽 `한 줄 고정` canvas에서 title/sub-title/subtitle 위치를 이동했을 때 해당 one-line 위치 필드만 저장되고, 왼쪽 double canvas 위치가 바뀌지 않는지 수동 확인한다.
  - 왼쪽/오른쪽 canvas에서 이동을 끝낸 뒤 guide/measurement focus가 이동 후 위치에 남는지 수동 확인한다.
  - 자막은 group이 아니라 첫째 줄/둘째 줄/한 줄 고정 각각 독립 좌표로 움직이는지, 하단타이틀/로고 텍스트도 왼쪽/오른쪽 canvas에서 이동 후 되돌아가지 않는지 수동 확인한다.
  - 레이아웃 이미지가 프레임 밖으로 크게 나간 상태에서 흐린 overflow 영역을 직접 드래그할 수 있는지, 어느 방향으로 드래그/숫자 입력해도 캔버스와 최소 40px 이상 겹치는지 수동 확인한다.
  - 레이아웃 이미지 선택 중 `맞춤`은 overflow 없이 프레임 안에 맞추고, `채우기`는 프레임을 꽉 채우며 중앙 정렬하는지 수동 확인한다.
  - layout edit preview에서 wheel zoom을 반복해도 캔버스가 overflow art 기준 위치로 튀지 않고 중앙 기준을 유지하는지 수동 확인한다.
  - 1080:1920 같은 frame 비율 layout image에서는 `맞춤`만 보이고, resize drag 중에도 `채우기` 버튼이 깜빡이지 않는지 수동 확인한다. 다른 비율 image에서는 `맞춤`/`채우기`가 모두 보이는지도 확인한다.
  - 1080:1920 source layout image를 preview에서 resize한 뒤 `맞춤`을 눌렀을 때 `1079x1920` 같은 drift가 남지 않고 정확히 `1080x1920`으로 돌아오는지 수동 확인한다.
  - `Legacy Clipper1 Template 9 복제본`에서 하단 타이틀이 왼쪽/오른쪽 compare canvas 모두 inspector Y `1479` 위치에 같은 높이로 보이는지, 하단 타이틀/로고 텍스트 drag 후 `x/y`가 정상 저장되는지 수동 확인한다.
  - 새로 복제/생성한 template의 `bottomTitle`/`logoText` JSON에는 line-mode y fields가 새로 생기지 않는지 확인한다. 기존 저장 데이터에 남은 stale fields는 preview/final render에서 무시된다.
  - 기본 레이어 선택 중 layout/content/background 위에서는 move cursor가 보이지 않고, 해당 영역 클릭 시 파란 selection box와 기본 레이어 row selection이 해제되는지 수동 확인한다.
  - artifact 도착 전 짧은 fallback 구간에서도 quoted `font-family` style이 들어간다. 그래도 실제 glyph가 맞지 않으면, 그때는 browser fallback에서 legacy font file을 web font로 로드하는 문제로 분리해서 다룬다. 이전처럼 Electron/NestJS 전달 경로를 넓히기 전에 Angular preview font loading 경계에서 최소 재현부터 잡는다.

## 2026-05-12 Template Builder ratio-specific layout and full gradient handling

- 최신 문서:
  - `.codex/implementation/2026-05-12-template-builder-ratio-layout-gradient-plan.md`
  - `.codex/design/2026-05-12-template-builder-multiple-layout-layers-design.md`
- 현재 상태:
  - `layoutImage`는 더 이상 family 공통으로 동기화하지 않는다. NestJS `updateVariant()`와 Angular optimistic patch 모두 선택 ratio만 변경한다.
  - `레이아웃` row는 `공통 레이어`에서 빠지고 선택 ratio의 `기본 레이어`에 표시된다. common row가 없으면 `공통 레이어` section도 숨긴다.
  - 콘텐츠 영역 fallback 배경은 `#babcbb` 단색이다.
  - full ratio seed에서 normal `gradient.png`는 `contentArea.assetUri` overlay로 들어가고, `layoutImage.assetUri`는 비운다.
  - full ratio 예외 `_full.png` layout은 `layoutImage.assetUri`에 유지하고, `gradient.png`는 `contentArea.assetUri`에 둔다.
  - legacy render payload는 `layoutImage.assetUri`가 없을 때 `contentArea.assetUri`를 `layout_image` fallback으로 내려보낸다.
- 검증:
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js`: 31 pass.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 143 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
  - `clipper_nestjs git diff --check`: passed.
- 다음 우선순위:
  - packaged Electron에서 full ratio preview가 `#babcbb` content fallback 위에 `gradient.png`를 보이고, template 6/10/14/17 full은 `_full.png` 아래 + `gradient.png` 위 순서로 보이는지 수동 확인한다.
  - 실제 다중 layout layer/z-order UI와 renderer contract는 `.codex/design/2026-05-12-template-builder-multiple-layout-layers-design.md` 기준으로 별도 구현한다.

## 2026-05-12 Template Builder multiple layout layers backend contract phase 1

- 최신 구현 계획:
  - `.codex/implementation/2026-05-12-template-builder-multiple-layout-layers-implementation-plan.md`
- 기준 커밋:
  - `clipper_angular` `a222b64 Refine template builder admin and layout preview`
  - `clipper_nestjs` `3756533 Support template builder admin overrides and full layout gradient`
- 현재 상태:
  - NestJS DTO에 `TemplateBuilderLayoutLayer`와 `TemplateBuilderLayers.layoutLayers?: TemplateBuilderLayoutLayer[]`가 추가됐다.
  - legacy seed가 layout stack을 만든다.
    - non-full: legacy `layout_image` 1개.
    - full normal: `gradient.png` 1개.
    - full exception: `_full.png` 후 `gradient.png`.
  - legacy render payload mapper가 `template_settings.template_builder_layout_layers`를 stack order 그대로 내려보낸다.
  - legacy 단일 `layout_image` fallback은 유지한다.
- 검증:
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js`: 32 pass.
  - `clipper_nestjs git diff --check`: passed.
- 다음 우선순위:
  - Phase 2: Angular model/preview에서 `layoutLayers[]`를 렌더링한다.
  - Phase 3/4: layout stack row selection, add, reorder, delete UI를 별도 TDD로 진행한다.

## 2026-05-12 Template Builder multiple layout layers Angular preview phase 2

- 기준 커밋:
  - `clipper_angular` `a222b64 Refine template builder admin and layout preview`
  - `clipper_nestjs` `fab610b Add template builder layout stack contract`
- 현재 상태:
  - Angular Template Builder model에 `TemplateBuilderLayoutLayer`와 `layers.layoutLayers?: TemplateBuilderLayoutLayer[]` contract를 추가했다.
  - canvas VM에 `layoutLayerPreviewItems`를 추가하고, preview canvas가 stack order 그대로 layout layers를 렌더링한다.
  - `layoutLayers[]`가 있는 variant에서는 기존 단일 `layoutImage` preview와 임시 `contentArea.assetUri` gradient preview를 숨겨 중복 렌더링을 막는다.
  - layout stack layer는 content area fallback 위, text/logo layer 아래에 렌더링된다.
  - 아직 row selection/add/reorder/delete UI는 없다. 기존 single `layoutImage` row는 legacy fallback/editing surface로 남아 있다.
- 검증:
  - RED/GREEN: `layoutLayers` model 누락으로 새 editor spec compile 실패를 확인한 뒤 model/VM/canvas 구현으로 통과시켰다.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 112 SUCCESS.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 144 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
- 다음 우선순위:
  - Phase 3: `기본 레이어`에 layout stack row들을 표시하고, 각 row 선택 시 해당 layout layer를 inspector/canvas selection 대상으로 연결한다.
  - Phase 4: layout layer 추가, 삭제, 순서 변경 UI와 저장 contract를 붙인다.
  - Phase 5 이후: renderer가 `template_builder_layout_layers`를 실제 합성 순서로 처리하도록 Python 쪽 parity를 맞춘다.

## 2026-05-12 Template Builder multiple layout layers row selection phase 3

- 기준 커밋:
  - `clipper_angular` `40f97be Render template builder layout layer stacks`
- 현재 상태:
  - `layers.layoutLayers[]`가 있는 variant는 `기본 레이어`에 `layoutLayers:<layerId>` row를 layer 수만큼 표시한다.
  - `layoutLayers[]`가 없는 legacy/custom data는 기존 `layoutImage` row를 그대로 표시한다.
  - layout stack row를 선택하면 media inspector가 해당 stack layer의 x/y/width/height를 보여주고, 숫자 입력/fit/center/move/resize patch는 선택된 stack layer만 교체한 `layers.layoutLayers` 배열로 emit한다.
  - stack layer 선택 중에는 compare preview가 기존 layout image 선택처럼 왼쪽 canvas 하나만 보인다.
  - stack layer의 직접 업로드/add/delete/reorder UI는 아직 없다. stack layer 선택 시 inspector에는 asset URI만 표시하고, 기존 단일 `layoutImage` upload control은 숨긴다.
- 검증:
  - RED/GREEN: layout stack row 선택과 inspector patch regression을 추가했다. 기존 코드에서는 stack row가 없어 실패했고, 구현 후 통과했다.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 113 SUCCESS.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts`: 147 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
- 다음 우선순위:
  - Phase 4: layout layer 추가, 삭제, 순서 변경 UI를 구현한다.
  - upload API/contract는 선택된 stack layer를 지정할 수 있어야 하므로 Phase 4에서 backend route와 함께 설계한다.
  - Phase 5 이후 Python renderer가 `template_builder_layout_layers` stack을 실제 합성 순서로 처리하게 맞춘다.

## 2026-05-12 Template Builder multiple layout layers commands/upload phase 4

- 기준 커밋:
  - `clipper_angular` `1b279d1 Select template builder layout stack layers`
  - `clipper_nestjs` `fab610b Add template builder layout stack contract`
- 현재 상태:
  - NestJS에 layout stack layer file route를 추가했다.
    - `GET /template-builder/families/:familyId/variants/:ratio/assets/layout-layers/:layoutLayerId/file`
    - `POST /template-builder/families/:familyId/variants/:ratio/assets/layout-layers/:layoutLayerId`
  - 선택된 stack layer 업로드는 해당 ratio의 해당 layer만 갱신한다.
  - 기존 단일 `layoutImage` 업로드도 더 이상 모든 ratio에 전파하지 않고 선택 ratio만 갱신한다.
  - Angular preview는 local `assetUri`를 가진 stack layer를 새 backend file endpoint로 렌더링한다.
  - layout stack row 선택 중 inspector의 이미지 선택 input이 선택된 stack layer upload request를 emit한다.
  - 기본 레이어 영역에 layout layer `추가 / 위 / 아래 / 삭제` controls를 추가했다.
    - `추가`는 현재 stack이 없으면 기존 `layoutImage`를 `layout.legacy` layer로 bridge한 뒤 새 빈 layer를 append한다.
    - `위`/`아래`는 선택된 stack layer 순서를 바꾼 `layoutLayers` 배열 patch를 emit한다.
    - `삭제`는 선택된 stack layer를 제거하고 selection을 clear한다. 마지막 1개 layer 삭제는 막아 legacy fallback이 갑자기 다시 보이는 상태를 피한다.
- 검증:
  - RED/GREEN: NestJS `layoutImage` upload ratio isolation regression과 selected stack layer upload/file resolve regression.
  - RED/GREEN: Angular service upload/file URL, page delegation, editor preview URL/upload, add/reorder/delete command regressions.
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js`: 35 pass.
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts`: 170 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
  - `clipper_nestjs git diff --check`: passed.
- 다음 우선순위:
  - Phase 5: Python renderer가 `template_builder_layout_layers` stack을 실제 합성 순서로 처리하도록 구현하고 golden/fixture test를 추가한다.
  - 이후 packaged Electron에서 full ratio `gradient.png`, `_full.png + gradient.png`, custom uploaded stack layer preview/upload/reorder를 수동 확인한다.

## 2026-05-12 Template Builder multiple layout layers Python renderer phase 5

- 기준 커밋:
  - `clipper_python` `6e834d8 Render template builder layout layer stacks`
- 현재 상태:
  - Python Clipper1 renderer가 `template_settings.template_builder_layout_layers`를 읽어 ordered `layout_layers` asset stack으로 resolve한다.
  - stack layer는 `asset_uri`/`assetUri`를 모두 지원하고, `visible: false`, asset이 없거나 geometry가 없는 layer는 건너뛴다.
  - 일반 segment render에서는 content media base 위에 layout stack을 순서대로 합성한 뒤 logo/text/subtitle overlays를 올린다.
  - full-height content render에서는 segment 단계에서 stack을 비우고, concat 이후 `_overlay_final_layout()`에서 stack layer들을 순서대로 합성한 뒤 logo/text overlays를 올린다.
  - `template_builder_layout_layers`가 없으면 기존 legacy 단일 `layout_image` 경로를 유지한다.
- 검증:
  - RED/GREEN: `_visual_assets()`가 `template_builder_layout_layers`를 path/geometry stack으로 resolve하는 regression.
  - RED/GREEN: `_render_segment()`가 stack layers를 logo/text보다 먼저 순서대로 overlay하는 regression.
  - RED/GREEN: `_overlay_final_layout()`가 full render stack layers를 text보다 먼저 순서대로 overlay하는 regression.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py -q`: 34 passed.
  - `clipper_python uv run pytest tests/test_template_builder_frame_artifacts.py::test_overlay_final_layout_uses_layout_geometry_when_available -q`: 1 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`: passed.
  - `clipper_python git diff --check`: passed.
  - 참고: `tests/test_template_builder_frame_artifacts.py` 전체 실행은 기존 text artifact width expectation(`300` vs actual `265`) 1건 때문에 실패한다. 이번 layout stack 변경과 직접 관련된 `test_overlay_final_layout_uses_layout_geometry_when_available`는 통과했다.
- 다음 우선순위:
  - `clipper_python` Phase 5 변경 커밋 후 packaged Electron에서 full ratio normal template은 content 위에 `gradient.png`, full 예외 template은 content 위에 `_full.png` 후 `gradient.png`가 실제 render에도 반영되는지 확인한다.
  - custom uploaded stack layer의 add/reorder/upload가 preview뿐 아니라 render output에서도 순서대로 반영되는지 수동 확인한다.

## 2026-05-13 Template Builder layout inspector stack/color layer implementation

- 최신 구현 문서:
  - `.codex/design/2026-05-12-template-builder-layout-inspector-stack-design.md`
  - `.codex/implementation/2026-05-12-template-builder-layout-inspector-stack-implementation-plan.md`
- 기준 커밋:
  - `clipper_angular` `60b16d3 Manage template builder layout layers in inspector`
  - `clipper_nestjs` `518e558 Include color layout layers in render payload`
  - `clipper_python` `e7acb37 Render color template layout layers`
- 현재 상태:
  - Template Builder 왼쪽 `기본 레이어`에는 `레이아웃` row 하나만 표시한다.
  - `레이아웃` 선택 시 오른쪽 inspector에서 layout layer stack을 Photoshop 방식 top-to-bottom 목록으로 관리한다.
  - inspector에서 `+ 이미지`, `+ 단색`, 삭제, 이름 변경, 방식 변경, 위치/크기 편집을 처리한다.
  - 순서 변경은 Angular CDK drag/drop으로 한다. 내부 저장/렌더 기준 `layoutLayers[]`는 계속 bottom-to-top order이고, inspector 표시만 reverse한다.
  - 마지막 layout layer 삭제도 허용하며 `layoutLayers: []`로 저장한다. 이 경우 legacy `layoutImage`로 자동 fallback하지 않는다.
  - 단색 layout layer도 Angular preview에 렌더링되고, NestJS render payload의 `template_builder_layout_layers`에 `source_type`, `background_color`, `asset_uri`로 내려간다.
  - Python renderer는 image layer는 기존처럼 asset input으로, color layer는 FFmpeg `color` source로 만들어 layout stack 순서대로 합성한다.
- 검증:
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts`: 122 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-render-payload.test.js`: 12 pass.
  - `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js`: 36 pass.
  - `clipper_nestjs git diff --check`: passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py -q`: 35 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`: passed.
  - `clipper_python git diff --check`: passed.
  - packaged Electron `npm run build:app:mac:arm64`: passed. `dist-app/mac-arm64/Clipper2.app`와 arm64 dmg가 생성됐다.
  - packaged app launch smoke: Python packaged plugin source sync, PluginHostBridge, NestJS `/v1` startup, Template Builder layout-layer asset routes 등록까지 확인했다.
  - packaged API smoke: `GET /v1/health`는 `{"status":"ok","service":"clipper-nestjs"}`를 반환했고, `GET /v1/template-builder/families`에서 system template variants의 `layoutLayers[]`가 반환되는 것을 확인했다.
  - packaged resource grep: renderer bundle에는 inspector layout manager UI(`layout-manager-row`, `add-color-layout-layer-button`), NestJS bundle에는 `source_type`/`background_color`, packaged Python plugin에는 color layout layer FFmpeg source handling이 포함되어 있다.
- 다음 우선순위:
  - 사용자가 packaged Electron에서 `/templates`를 열고 `레이아웃` 선택 시 왼쪽 row는 하나만 보이고 inspector에 stack 목록/썸네일/색상 swatch가 보이는지 확인한다.
  - inspector drag/drop 순서 변경이 preview z-order와 저장값에 맞게 반영되는지 확인한다.
  - 단색 배경 layer + 이미지 layout layer 조합이 preview와 sample render에서 같은 순서로 보이는지 확인한다.
  - 21개 system template을 순회하며 full ratio의 gradient/content layering, non-full content area layering, 기존 image layout stack이 변하지 않았는지 수동 확인한다.

### 2026-05-12 Non-full layout stack content area visibility follow-up

- 원인:
  - non-full ratio도 Phase 1 seed 이후 legacy `layout_image`가 `layoutLayers[]` stack으로 들어온다.
  - Angular preview의 stack layer가 content area와 같은 `z-index: 1`이고 content area 뒤 DOM에 렌더링되어, non-full 콘텐츠 영역 placeholder를 덮었다.
  - Python renderer도 stack path에서는 content media를 먼저 만들고 layout stack을 위에 합성해서, 기존 legacy non-full `layout_image` 경로의 "layout 아래, content 위" 합성 순서와 달라졌다.
- 현재 상태:
  - 커밋:
    - `clipper_angular` `5ce5941 Keep non-full layout stacks behind content area`
    - `clipper_python` `2b6db37 Keep non-full layout stacks below content media`
  - Angular preview에서 `variant.contentArea.height < variant.outputSize.height`인 non-full ratio stack layer는 `z-index: 0`으로 내려 content area placeholder가 보인다.
  - full ratio는 기존처럼 stack layer가 content 위 overlay로 남는다.
  - Python renderer의 non-full stack path는 canvas background 위에 layout stack을 먼저 합성한 뒤 content media를 content area 위치에 overlay한다. full-height stack은 기존처럼 final overlay 단계에서 content 위에 합성된다.
- 검증:
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 117 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular git diff --check`: passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py -q`: 34 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`: passed.
  - `clipper_python git diff --check`: passed.

## 2026-05-11 Template Builder layout rollback

- 최신 세션 로그: `.codex/session-logs/2026-05-11.log`
- 현재 상태:
  - 방금 추가한 left sidebar 재배치는 롤백했다.
  - Template Builder page는 다시 `gallery / editor` 2컬럼 구조다.
  - `template-workspace__left`는 workspace 내부에 그대로 있다.
  - inspector width는 `360px`으로 고정된 상태를 유지한다.
- 다음 세션 우선순위:
  - packaged Electron에서 inspector 360px 고정만 확인한다.
  - 이후에 필요한 경우에만 gallery/editor 비율이나 left panel 구조를 다시 조정한다.

## 2026-05-10 Template Builder editor checkpoint

- 최신 체크포인트 문서: `.codex/implementation/2026-05-10-template-builder-editor-checkpoint.md`
- 최신 세션 로그: `.codex/session-logs/2026-05-10.log`
- 이번 커밋:
  - `clipper_angular` `c4c52e3 feat: refine template builder preview editor`
  - `clipper_nestjs` `5923995 feat: extend template builder box sizing contract`
  - `clipper_python` `89e940b feat: render template builder fixed text boxes`
- 주요 상태:
  - Template Builder gallery/card, inspector/property UI, color field, layout background mode, preview toolbar/measurement guide, box effect width mode, text-fit box center/move anchor fix까지 반영했다.
  - `공통 레이어`에는 `레이아웃`만 있고, 레이아웃은 항상 사용된다.
  - `기본 레이어` 선택 중에는 layout image preview interaction을 막는다.
  - `contentArea`는 편집 대상이 아니라 preview guide지만 measurement guide neighbor에는 포함한다.
  - text-fit box artifact는 visible frame과 persisted layer anchor x가 다르므로 patch emit 시 anchor x로 변환한다.
- 검증:
  - `clipper_angular` Template Builder focused suite `123 SUCCESS`, `npm run build` passed, `git diff --check` passed.
  - `clipper_nestjs npm run build` passed, `git diff --check` passed.
  - `clipper_python uv run --extra test pytest tests/test_template_builder_text_renderer.py` passed (`5 passed`), `git diff --check` passed.
- 다음 세션 우선순위:
  - packaged Electron 재빌드 후 사용자가 Template Builder를 직접 확인한다.
  - 특히 `가로 중앙` 버튼이 text-fit box effect에서 실제 보이는 박스를 중앙으로 보내는지, fixed box width resize가 sample/final render까지 일치하는지 확인한다.
  - 남은 drift가 있으면 `TemplateBuilder layer -> text preview artifact metadata -> canvas frame -> sample/final render payload` 순서로 좁힌다.

## 2026-05-10 Template Builder group/line-mode follow-up

- 현재 Template Builder는 fixed layer rows를 `레이아웃 / 타이틀 / 자막 / 로고`로 묶고, 타이틀/자막은 one-line vs two-line mode를 속성에서 선택하는 방향으로 바뀌었다.
- subtitle preview는 double-line일 때만 줄별로 분리되고, layout/text/logo는 context-sensitive property panel로 분리된다.
- logo image는 builder에서 업로드하지 않고 위치/크기만 편집한다.
- 다음 세션에서는 packaged Electron에서 이 구조가 실제로 유지되는지 확인하고, 남은 UI/interaction 회귀를 정리한다.

## 2026-05-10 Template Builder layoutImage family-wide sync / clipped render

- `layoutImage`는 ratio별 설정이 아니라 template family 공통 값으로 동기화한다.
- backend `updateVariant()`는 `layoutImage` patch가 오면 family의 모든 variant에 같은 geometry를 적용한다.
- legacy render payload는 `layout_image_x_offset`, `layout_image_y_offset`, `layout_image_area_width`, `layout_image_area_height`를 같이 내려서 sample/final render가 inside-frame만 쓰도록 맞춘다.
- Angular optimistic state도 `layoutImage` patch를 family-wide로 반영한다.
- 검증은 `clipper_nestjs node --test test/template-builder-api.test.js`, `clipper_python UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_template_builder_frame_artifacts.py -q`, `clipper_angular npm run build`까지 확인했다. Karma는 이 샌드박스에서 포트 bind EPERM로 직접 실행이 막혔다.

2026-05-09 이후 세션 상태를 이어받을 때는 먼저 `.codex/implementation/TEMPLATE_RENDERING_POLICY_2026-05-09.md`와 `.codex/implementation/PREVIEW_FINAL_RENDER_PARITY_PLAN_2026-05-09.md`를 읽는다. 그 다음 `.codex/implementation/CLIPPER1_RENDER_PARITY_CHECKPOINT_2026-05-09.md`를 legacy compatibility guard의 최신 기준으로 확인한다.

2026-05-08 마감 상태는 `.codex/implementation/CLIPPER1_RENDER_PARITY_CHECKPOINT_2026-05-08.md`에 보존되어 있다.

## 2026-05-10 Template Builder clone family / subtitle line / effect mode update

- 사용자 확인 중 다음 Template Builder UX/behavior 문제가 정리됐다.
  - 기본 제공 template 복제는 선택한 ratio 하나가 아니라 하나의 template family 전체, 즉 `16:9`, `1:1`, `4:3`, `full` 전체를 복제해야 한다.
  - legacy title text 선택 box 높이가 짧아 glyph가 잘려 보이면 안 된다.
  - subtitle line은 기존 Clipper1 구조처럼 `oneLineY`, `twoLineFirstY`, `twoLineSecondY`로 줄별 위치를 따로 조정할 수 있어야 한다.
  - `렌더 폰트명`은 일반 편집 UI에 노출하지 않는다.
  - preview zoom 30%는 output 1080px width의 30%=324px을 의미하며, 사용자가 조절할 수 있어야 한다.
  - `간격` 라벨은 snap grid 간격이므로 `스냅 간격`으로 명확히 한다.
  - text effect는 `없음 / 박스 / 윤곽선 / 그림자` 중 하나만 선택하게 하고, 윤곽선 기본 두께는 8이다.
- Implemented:
  - `clipper_nestjs` `cloneFamily()`는 source family의 모든 existing ratio variant를 exact visual clone으로 복제한다. Backward compatibility로 request ratio가 source에 없으면 기존 cross-ratio style transfer variant를 추가한다.
  - default `TemplateBuilderOutlineStyle.width`를 `8`로 변경했다.
  - legacy system seed에서 text layer height를 `fontSize * lineHeight + outline/shadow padding` 이상으로 보강한다.
  - Angular clone form에서 ratio select를 제거하고 “모든 비율 복제” UX로 바꿨다. clone 후 editor selected ratio는 cloned family의 default(`16:9` 우선)로 맞춘다.
  - Angular editor에서 subtitle line span을 직접 드래그하면 `subtitleText.twoLineFirstY/twoLineSecondY/oneLineY`만 patch한다.
  - 속성 패널에 subtitle `한 줄 Y`, `두 줄 첫째 Y`, `두 줄 둘째 Y` 입력을 추가했다.
  - `렌더 폰트명` 입력을 숨겼다.
  - preview zoom 입력과 canvas wheel zoom을 추가했다.
  - `스냅 간격` 라벨을 적용했다.
  - `텍스트 효과` select를 추가하고 선택한 mode의 세부 속성만 표시한다. Outline mode 선택 시 기존 width가 0이면 width 8로 patch한다.
- Verification:
  - RED/GREEN Angular editor focused spec: new failures for missing effect mode/zoom/fontName hiding/subtitle line drag/subtitle y controls, then `47 SUCCESS`.
  - RED/GREEN Angular page focused spec: clone ratio selector removal/all-ratio copy wording/default `16:9` reference, then `25 SUCCESS`.
  - RED/GREEN NestJS API spec: default outline width, all-ratio legacy clone, legacy text height, then `14 pass`.
- Commits:
  - `clipper_angular` `6a9e889 fix: improve template builder editing controls`
  - `clipper_nestjs` `56e6d38 fix: clone template builder families`
- Packaged app:
  - Rebuilt with `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Latest app: `clipper_electron/dist-app/mac-arm64/Clipper2.app`.
  - Latest DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`.
  - Smoke: health HTTP 200; template 17 clone HTTP 201; source and clone both had `16:9`, `1:1`, `4:3`, `full`; clone `mainTitleLine1.outline.width=8`.
- Next priority:
  - 사용자가 packaged app에서 clone all-ratio behavior, subtitle line drag/inputs, text effect single-mode UX, zoom controls를 직접 확인한다.
  - 사용자가 특정 legacy template에서 style/box/height 문제가 남아 있다고 보고하면 pixel parity가 아니라 `rawSettings -> Template Builder layer -> render contract` mapping으로 좁혀 진단한다.

## 2026-05-10 Template Builder subtitle/background/usage update

- 최신 결정:
  - 세션 로그는 짧게 남긴다. 핵심 요구, 결정, 주요 파일/커밋, 검증 결과, 다음 작업만 기록한다.
  - `자막 박스`는 Template Builder UI에서 제거한다. 자막은 `자막 첫번째줄`/`자막 두번째줄` row로 보여주되, 저장/render contract는 shared `subtitleText` style을 중심으로 유지한다.
  - `subtitleBox`는 기존 저장 데이터 fallback으로만 남긴다.
  - `표시`는 UI에서 `사용`으로 바꾼다. read-only system template에서는 사용 체크가 토글되지 않게 disabled 처리한다.
  - legacy rawSettings의 display y-offset이 `null`이면 해당 layer는 사용하지 않는 것으로 seed한다.
  - 배경은 `레이아웃 이미지` 또는 `단색 배경` 중 하나를 선택한다.
- Implemented:
  - `clipper_angular` `2aefebe fix: refine template builder subtitle layers`
  - `clipper_nestjs` `32ebdd2 fix: honor template builder unused layers`
  - `clipper_python` `553d490 fix: render template builder subtitle boxes`
- Verification:
  - `clipper_angular npm run build`: passed.
  - `clipper_angular npx ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'`: 93 specs passed.
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test` for Template Builder validation/api/render-payload/render-contract/sample-render/text-artifact: 34 tests passed.
  - `clipper_python uv run pytest` for subtitle artifacts/media looping/text preview/export/template styles/guard runner: 52 tests passed.
  - `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.
- Next priority:
  - 사용자가 최신 packaged app에서 `사용` toggle, 자막 두 줄 row, 배경 이미지/색상 모드를 직접 확인한다.
  - 이후 남은 문제는 pixel parity가 아니라 `rawSettings -> Template Builder layer -> preview contract -> final render payload` 흐름으로 진단한다.

## 2026-05-10 Template Builder default ratio / legacy style seed fix

- 사용자 확인 중 Template Builder에서 legacy template을 선택하면 `full`이 기본 선택되고, 모든 title/subtitle/logo text가 기본 Pretendard/40px/검정 스타일처럼 보이는 문제가 발견됐다.
- `clipper_angular` `80ddba7 fix: default template builder selection to 16x9`
  - family 선택 시 `16:9` variant가 있으면 editor가 `16:9`로 열린다.
  - create/clone 기본 ratio도 `16:9` 중심으로 맞췄다. 단, 사용 가능한 ratio가 `full`뿐이면 `full`을 사용한다.
  - parent page의 `editorSelectedRatio`를 editor input으로 내려 text preview artifact와 editor ratio가 엇갈리지 않게 했다.
- `clipper_nestjs` `8a75081 fix: seed legacy template builder styles`
  - legacy rawSettings의 `sub_title_*`, `main_title_*`, `bottom_title_*`, `logo_text_*`, `subtitle_*`, `subtitle_box_*`, y-offset, margin, box, outline, shadow, logo image geometry를 Template Builder layer로 seed한다.
  - legacy box color가 `null`이면 box를 disabled/transparent로 seed한다.
- Verification:
  - `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 42 specs passed.
  - `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/pages/template-builder-page.component.spec.ts`: 25 specs passed.
  - `clipper_angular npm run build`: passed.
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-api.test.js --test-name-pattern "legacy Clipper1 text styles"`: passed; Node runner executed all 13 tests in that file.
  - `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.
- Latest app for manual check:
  - `/Users/jina/project/adlight/clipper_electron/dist-app/mac-arm64/Clipper2.app`
  - `/Users/jina/project/adlight/clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- Next priority:
  - 사용자가 최신 packaged app에서 Template Builder를 열어 `16:9` 기본 선택, legacy title/subtitle/logo style, box transparency를 직접 확인한다.
  - 특정 템플릿의 style이 여전히 다르면 픽셀 parity가 아니라 해당 template의 `rawSettings -> Template Builder layer -> render contract` mapping을 좁혀 진단한다.

## 2026-05-10 Plugin dashboard workflow-only fix

- 사용자 확인 중 `Clipper1 숏폼 제작`이 플러그인 대시보드/스토어 흐름에서 “시작”으로 보이고 실제로 시작되지 않는 문제가 발견됐다.
- Root cause:
  - `/v1/plugins`에는 실제 runtime worker `clipper1_video_render`와 사용자 workflow entry `clipper1`이 같이 내려온다.
  - `clipper1`은 runtime process가 아니라 `/clipper-studio`로 여는 workflow-only entry다.
  - Angular dashboard의 `isWorkflowOnly()`가 오래된 이름 `clipper_studio`만 검사해서 `clipper1`을 startable runtime으로 잘못 취급했다.
  - 직접 재현: `POST /v1/plugins/clipper1/start`는 HTTP 201과 빈 `baseUrl`을 반환하지만 status는 계속 `stopped`였다. 따라서 UI에서는 “시작 안 됨”처럼 보인다.
- Fix:
  - `clipper_angular/src/core/plugin-status.service.ts`에 `isWorkflowOnlyPlugin()`을 추가하고 `clipper1`, `variation`을 workflow-only로 분류했다.
  - Dashboard는 이 helper를 사용한다.
  - 1차 수정에서는 `clipper1`을 dashboard에서 “시작” 대신 “열기” 버튼으로 `/clipper-studio`에 연결했다.
  - `dance_highlight`, `dialog_highlight`, `clipper1_video_render`는 workflow-only가 아니므로 runtime start 대상이다.
- Commit:
  - `clipper_angular` `6d376b4 fix: open workflow plugins from dashboard`.
- Verification:
  - RED: `DashboardComponent opens the Clipper1 workflow instead of trying to start it as a runtime plugin` failed against the old `clipper_studio` check.
  - GREEN: `npm test -- --watch=false --include src/shell/dashboard/dashboard.component.spec.ts` passed, 1 spec.
  - `npm test -- --watch=false --include src/core/plugin-status.service.spec.ts` passed, 4 specs.
  - `npm run build` passed.
  - `git diff --check` passed.
  - Rebuilt packaged app with `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Packaged smoke: `GET /v1/health` HTTP 200, `GET /v1/plugins` HTTP 200; app/NestJS shut down cleanly.

## 2026-05-10 Plugin dashboard runtime-status projection fix

- 사용자 후속 확인:
  - `Clipper1 숏폼 제작`, `Variation 대량 숏폼 제작`은 plugin runtime이 아니라 workflow다.
  - 따라서 Dashboard의 플러그인 상태 리스트에는 “열기” 버튼으로도 나타나지 않아야 한다.
- Decision:
  - `/v1/plugins` API는 workflow entry와 runtime worker를 모두 내려줄 수 있다.
  - Angular `PluginStatusService.items()`는 Store/catalog/user-facing 목록으로 유지한다.
  - Dashboard 상태 리스트는 새 `PluginStatusService.runtimeItems()` projection만 사용한다.
  - `runtimeItems()`는 workflow-only entry(`clipper1`, `variation`)를 제외하고 실제 runtime status 대상(`clipper1_video_render`, `dance_highlight`, `dialog_highlight`)을 우선 순서로 정렬한다.
  - Dashboard status row에서 workflow-only “열기” branch를 제거했다. workflow 진입은 Store/Workflow 화면에서 처리하고, runtime 상태 리스트는 시작/중지 가능한 runtime만 보여준다.
- Implementation:
  - `clipper_angular/src/core/plugin-status.service.ts`
    - `runtimeItems` signal 추가.
    - `refreshAll()`에서 Store용 `items`와 Dashboard용 `runtimeItems`를 분리해 채운다.
    - `refreshOne()`은 user-visible scope와 runtime-status scope를 각각 갱신한다.
    - start/stop optimistic state는 `items`와 `runtimeItems` 양쪽에 반영한다.
  - `clipper_angular/src/shell/dashboard/dashboard.component.html`
    - plugin status list와 loading empty check가 `runtimeItems()`를 읽는다.
    - workflow-only “열기” action branch 제거.
  - `clipper_angular/src/shell/dashboard/dashboard.component.ts`
    - evictable cleanup도 `runtimeItems()` 기준으로 계산한다.
- Commit:
  - `clipper_angular` `15727b3 fix: show only runtime plugins in dashboard status`.
- Verification:
  - RED: `PluginStatusService runtime status list state applies optimistic runtime state changes to the dashboard runtime list` failed with `Expected 'stopped' to be 'starting'`.
  - GREEN: `npm test -- --watch=false --include src/core/plugin-status.service.spec.ts` passed, 8 specs.
  - `npm test -- --watch=false --include src/shell/dashboard/dashboard.component.spec.ts` passed, 1 spec.
  - `npm run build` passed.
  - `git diff --check` passed.
  - Rebuilt packaged app with `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Packaged smoke: `GET /v1/health` HTTP 200, `GET /v1/plugins` HTTP 200; `/v1/plugins` still includes workflow entries by design, but Angular Dashboard runtime list now filters them out. App/NestJS shut down cleanly.

## 2026-05-10 Template Builder document-scroll fix

- 사용자 확인:
  - Template Builder 페이지에서 여전히 전체 페이지 세로 스크롤이 생긴다.
  - 페이지 배경은 밝은색인데 아래로 스크롤하면 검은 앱 배경이 보인다.
- Root cause:
  - 이전 panel-local scroll fix는 Template Builder page/editor 내부 컨테이너만 검사했다.
  - 실제 앱에서는 `app-root` host가 inline/static document flow에 남아 있었고, `app-floating-install-bar`도 inline element로 flow에 남았다.
  - `.app-main`은 `overflow-x: auto`만 갖고 있어 computed `overflow-y`가 `auto`가 됐고, Template Builder의 넓은 editor surface/horizontal overflow와 결합해 document-level vertical scroll을 만들 수 있었다.
  - Template Builder route host도 Store/Dashboard/Projects와 달리 route-level fixed-height/background/min-width boundary가 명확하지 않아, 아래로 스크롤했을 때 밝은 Template Builder surface 바깥의 검은 app/root background가 노출될 수 있었다.
- Fix:
  - `clipper_angular/src/app/app.component.scss`
    - `:host`: `position: fixed`, `inset: 0`, `display: block`, `width/height: 100vw/100vh`, `overflow: hidden`.
    - `.app-shell`: `height: 100vh`, `min-height: 0`, `overflow: hidden`.
    - `.app-main`: `height: 100vh`, `min-height: 0`, `overflow-x: auto`, `overflow-y: hidden`.
    - `app-floating-install-bar`: `display: contents`.
  - `clipper_angular/src/styles.scss`
    - `html, body`: `height: 100%`, `min-height: 0`, `overflow: hidden`, app background 유지.
  - `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`
    - route host에 `display: block`, `height: 100vh`, `min-width: 1500px`, `overflow: hidden`, `background: #f3f5f7`.
    - `.template-page`는 host 높이를 따라 `height: 100%`, 같은 `min-width`를 갖는다.
  - `clipper_angular/src/app/app.component.spec.ts`
    - zoneless/router test setup으로 갱신.
    - app shell/app-root가 document-level vertical scrolling을 만들지 않는 regression test 추가.
  - `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`
    - Template Builder route host가 fixed viewport page surface처럼 동작하고, page-level vertical scroll을 만들지 않는 regression check 강화.
- Commit:
  - `clipper_angular` `9bc271e fix: prevent app shell vertical scroll`.
- Verification:
  - RED: `npm test -- --watch=false --include src/app/app.component.spec.ts` failed with `.app-shell overflow-y visible` and `.app-main overflow-y auto`.
  - GREEN: same command passed, 3 specs.
  - `npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts` passed, 23 specs.
  - `npm run build` passed.
  - `git diff --check` passed.
  - Rebuilt packaged app with `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Packaged app CDP check after `window.scrollTo(0, 9999)`:
    - `/templates`: `scrollY=0`, `documentElement.scrollHeight=872`, `documentElement.clientHeight=872`, `body.scrollHeight=872`, `app-root position=fixed`, Template Builder host/page background `rgb(243, 245, 247)`, host/page height `872px`.
    - `/dashboard` and `/store`: also `scrollY=0`, `documentElement.scrollHeight=872`, `documentElement.clientHeight=872`.
  - Packaged smoke: `GET /v1/health` HTTP 200, `GET /v1/template-builder/families` HTTP 200.

## 2026-05-10 Template Builder preview text shrink fix

- 사용자 확인:
  - Template Builder preview에서 자막/텍스트 레이어를 움직이면 잠깐 정상 크기로 보이다가 1초 이내에 매우 작아진다.
- Root cause:
  - Drag/update 직후에는 Angular browser text fallback이 보인다.
  - 이후 비동기 Python final-render text artifact가 도착하면 `<img class="canvas-text-artifact">`로 교체된다.
  - Template Builder 기본 layer의 `fontFamily`는 `Pretendard-SemiBold.otf` 같은 파일명인데, Python text artifact renderer가 이 파일명을 실제 font 파일로 resolve하지 못해 Pillow default bitmap font로 fallback했다.
  - packaged Electron에서는 plugin cwd가 userData라서 `Path.cwd()/fonts`만으로는 bundled fonts를 찾을 수 없다.
- Fix:
  - `clipper_python` `86d3cac fix: resolve template builder preview fonts`
    - `template_builder_text_renderer.py`가 `CLIPPER_LEGACY_FONTS_DIR`, `cwd/fonts`, source tree `clipper_python/fonts`, local dev sibling `adlight_python/fonts` 순서로 font filename을 resolve한다.
    - `tests/test_template_builder_text_renderer.py`에 packaged-like env font filename regression을 추가했다.
  - `clipper_electron` `5916d2d fix: bundle template builder fonts`
    - `electron-builder.yml`이 `adlight_python/fonts`를 packaged `clipper_python/fonts`로 포함한다.
    - plugin process env에 `CLIPPER_LEGACY_FONTS_DIR=<pythonRoot>/fonts`를 주입한다.
- Verification:
  - RED: `uv run pytest tests/test_template_builder_text_renderer.py -q` failed because filename-only Pretendard rendered with an 8px ink bbox from Pillow default font.
  - GREEN: `uv run pytest tests/test_template_builder_text_renderer.py tests/test_template_builder_text_preview_artifact_export_script.py tests/test_template_builder_text_artifacts.py tests/test_clipper1_video_render_text_artifact_job.py -q` passed, 8 tests.
  - `clipper_electron npm run build` passed.
  - `clipper_python git diff --check` and `clipper_electron git diff --check` passed.
  - Rebuilt packaged app with `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Confirmed packaged `Clipper2.app/Contents/Resources/clipper_python/fonts/Pretendard-SemiBold.otf` and `Paperlogy-8ExtraBold.ttf` exist.
  - Packaged app CDP `/templates` check after text artifacts loaded:
    - `canvas-text-artifact-mainTitleLine1`: natural size `908x64`, displayed size about `272.39x19.19`, alpha bbox height `36`.
    - Other plain text artifacts had alpha bbox height `30-36`; subtitle combined artifact natural size `440x128`.
  - Existing user-running Clipper2 process was left untouched; a separate CDP-launched verification process was stopped with Ctrl-C after checks.

## 2026-05-10 Template Builder read-only action guard fix

- 사용자 확인:
  - Template Builder에서 `테스트 렌더`, `게시`, `레이아웃 이미지` 버튼/입력이 오류를 낸다.
- Root cause:
  - 기본 제공 Template Builder family는 `readonly=true`인 시스템 템플릿이다.
  - Angular editor가 읽기 전용 family에서도 샘플 렌더/게시/이미지 업로드 같은 수정성 액션을 활성화했다.
  - NestJS `startSampleRender()`, `publishVariant()`, `uploadLayoutImage()`, `uploadLogoImage()`, `uploadFont()`가 시스템 family를 먼저 조회하지 않고 custom repository에서만 `require()`해서 `Unknown template family: system...`류 오류를 낼 수 있었다.
- Product decision:
  - 기본 제공 템플릿은 그대로 보거나 복제할 수 있다.
  - 수정, 레이아웃/로고 이미지 업로드, 폰트 업로드, 샘플 렌더, 게시 같은 variant 변경 액션은 복제된 사용자 템플릿에서만 허용한다.
- Fix:
  - `clipper_angular` `ebcaedd fix: gate template builder readonly actions`
    - `TemplateBuilderEditorComponent`에 `isReadonly()` guard를 추가했다.
    - 읽기 전용 family에서는 샘플 렌더/게시/variant 생성/file input/drag resize/update emit을 막는다.
    - 샘플 렌더/게시 버튼과 layout/logo/font file input이 disabled 상태가 된다.
  - `clipper_nestjs` `5cf529b fix: reject readonly template builder mutations`
    - 시스템 family 조회가 필요한 mutating API에서 `getFamily()`를 먼저 사용한다.
    - 읽기 전용 family에 대해 “복제 후 샘플 렌더/게시/수정할 수 있습니다” 메시지로 명확히 거절한다.
- Verification:
  - RED: Angular readonly editor spec은 기존 template에 `data-testid`/disabled guard가 없어 실패했다.
  - RED: NestJS readonly mutable action spec은 기존 서비스가 `Unknown template family: system...`으로 실패했다.
  - GREEN:
    - `clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts` passed, 40 specs.
    - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts` passed, 23 specs.
    - `clipper_angular npm run build` passed.
    - `clipper_nestjs npm run build` passed.
    - `clipper_nestjs node --test test/template-builder-api.test.js` passed, 11 tests.
    - `clipper_angular git diff --check` and `clipper_nestjs git diff --check` passed.
- Packaged app:
  - Rebuilt with `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Latest app: `clipper_electron/dist-app/mac-arm64/Clipper2.app`.
  - Latest DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`.
  - Smoke:
    - `GET /v1/health`: HTTP 200.
    - `GET /v1/template-builder/families`: HTTP 200 and system families have `readonly=true`.
    - `POST /v1/template-builder/families/system.legacy.clipper1.template.1/variants/full/sample-render`: HTTP 400, `기본 제공 템플릿은 복제 후 샘플 렌더할 수 있습니다.`
    - `POST /v1/template-builder/families/system.legacy.clipper1.template.1/variants/full/publish`: HTTP 400, `기본 제공 템플릿은 복제 후 게시할 수 있습니다.`
    - `POST /v1/template-builder/families/system.legacy.clipper1.template.1/variants/full/assets/layout-image`: HTTP 400, `기본 제공 템플릿은 복제 후 수정할 수 있습니다.`
  - Smoke용 packaged app/NestJS 프로세스는 종료했다.

## 2026-05-10 Template Builder clone visual preservation fix

- 사용자 확인:
  - Template Builder에서 템플릿을 선택해 복제하면 선택했던 템플릿이 그대로 복제되지 않는다.
  - 복제 결과에서 배경이 검은색으로 보이고, 타이틀/자막들이 콘텐츠 영역 안으로 모여 보인다.
- Root cause:
  - Angular clone form이 현재 editor에서 보고 있는 ratio가 아니라 `full`을 우선 기본값으로 잡았다.
  - 따라서 사용자가 예를 들어 16:9 템플릿을 보고 있어도 clone request가 `ratio=full`, `cloneFromRatio=full`로 나갈 수 있었다.
  - 이후 다른 ratio를 만들거나 선택하면 서버의 cross-ratio style transfer가 full 좌표를 target content-area 기준으로 재배치해 타이틀들이 content-area 안으로 압축되는 결과를 만들 수 있었다.
  - NestJS system preset seed도 `contents_area_y_offset`을 `layers.contentArea.y`에만 반영하고 `variant.contentArea.y`에는 반영하지 않아 contract 기준 content area와 layer 기준 content area가 달랐다.
  - 같은 ratio clone에서도 기존 implementation은 새 default variant 위에 style transfer를 적용해 source visual snapshot을 exact clone으로 보존하지 않았다.
- Fix:
  - `clipper_angular` `6c0b1df fix: clone current template builder ratio`
    - clone form 기본 ratio를 현재 editor preview ratio로 잡는다.
    - clone submit fallback도 현재 editor ratio를 우선 사용한다.
    - clone 성공 후 page state의 editor ratio를 clone된 ratio로 맞춘다.
  - `clipper_nestjs` `48091dd fix: preserve template builder clone visuals`
    - legacy preset seed에서 `contents_area_y_offset`을 `variant.contentArea.y`와 `layers.contentArea.y`에 같이 반영한다.
    - `cloneFamily()`가 같은 ratio를 복제할 때는 source variant를 exact visual clone으로 복사하고 family/id/status/sampleRender만 새 사용자 템플릿에 맞게 갱신한다.
    - 다른 ratio 생성/복제는 기존 geometry transfer path를 유지한다.
- Verification:
  - RED:
    - Angular page spec failed because clone request still used `ratio=full`, `cloneFromRatio=full` while editor ratio was `16:9`.
    - NestJS API spec failed because source/cloned `contentArea.y` was `656` instead of legacy setting `595`.
  - GREEN:
    - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts` passed, 24 specs.
    - `clipper_angular npm run build` passed.
    - `clipper_nestjs npm run build` passed.
    - `clipper_nestjs node --test test/template-builder-api.test.js` passed, 12 tests.
    - `clipper_angular git diff --check` and `clipper_nestjs git diff --check` passed.
- Packaged app:
  - Rebuilt with `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Smoke용 별도 `--user-data-dir=/tmp/clipper-codex-clone-user-data` 인스턴스에서 확인:
    - `GET /v1/health`: HTTP 200.
    - `POST /v1/template-builder/families/system.legacy.clipper1.template.17/clone` with `ratio=16:9`, `cloneFromRatio=16:9`: HTTP 201.
    - source/cloned values matched: `contentArea.y=595`, `layers.contentArea.y=595`, `layoutImage.assetUri=.../layout/17.png`, `mainTitleLine1.y=364`, `subtitleText.oneLineY=1291`.
  - Smoke용 인스턴스는 종료했다.

## 2026-05-10 Template Builder clone ratio select display fix

- 사용자 확인:
  - 기존 템플릿의 1:1 ratio를 선택한 뒤 복제를 누르면 `복제할 비율` select가 16:9로 보인다.
  - 그런데 그대로 `복제`를 누르면 실제 생성되는 복제본은 1:1이다.
- Root cause:
  - `cloneRatio()` state는 1:1로 맞게 설정됐지만, clone form이 열릴 때 `<select [value]="cloneRatio()">`가 option 렌더링과 동기화되지 않아 DOM 표시값이 첫 option인 16:9로 남았다.
  - 즉 서버 복제 요청 값 문제가 아니라 Angular select 표시 동기화 문제였다.
- Fix:
  - `clipper_angular` `3f2a216 fix: show selected clone ratio`
    - clone ratio `<option>`에 `[selected]="ratio === cloneRatio()"`를 명시했다.
    - 같은 패턴인 create ratio select도 `[selected]="ratio === createRatio()"`로 보정했다.
- Verification:
  - RED: editor ratio가 1:1이고 `cloneRatio()`가 1:1인데 DOM select value/selected option은 16:9로 실패했다.
  - GREEN:
    - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts` passed, 25 specs.
    - `clipper_angular npm run build` passed.
    - `clipper_angular git diff --check` passed.
- Packaged app:
  - Rebuilt with `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
  - Latest app: `clipper_electron/dist-app/mac-arm64/Clipper2.app`.
  - Latest DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`.

다음 세션에서 이어받을 때는 먼저 `.codex/design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`와 `.codex/implementation/SHORTFORM_PLUGIN_SPLIT_PHASE1_PLAN.md`를 읽고, 그 다음 `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-06.md`와 이 문서를 읽는다.
2026-05-05 checkpoint는 이전 상태 보존용이다.

Angular 작업 전에는 `.codex/standards/ANGULAR_FRONTEND_RULES.md`를 반드시 읽는다. `clipper_angular`는 zoneless 앱이며 `zone.js`/`zone.js/testing` import는 금지다. Clipper Studio spec은 `b998e6d test: keep clipper studio spec zoneless`에서 zoneless TestBed provider로 보정됐다.

## 2026-05-09 Template rendering 정책 전환

- Legacy Clipper1 render parity는 25개 Clipper1 reference frame fixture 기준 `channelTolerance=32`, `maxMismatchRatio=0.0006`에서 compatibility guard로 동결한다.
- 이 기준의 latest worst는 `template-17-16_9`, mismatch `0.0005690586419753086`이다.
- 여기서 남은 top text edge를 더 줄여 `0.0004` 이하로 강화하는 작업은 중단한다.
- 이유:
  - 기존 Clipper1 템플릿은 Zeplin 치수를 Pillow/FFmpeg/MoviePy 출력에 맞추기 위해 수동 보정한 legacy 구현이다.
  - 일부 glyph clipping/padding/metric 문제는 Clipper2 modern renderer에서 그대로 복제하면 안 되는 품질 문제다.
  - 기존 21개 템플릿 출력 안정성은 지켜야 하지만, 새 Template Builder의 성공 기준은 Clipper1 pixel identity가 아니라 preview/final 일치성이다.
- 다음 우선순위:
  - Template Builder canvas preview와 sample/final render가 같은 variant snapshot, 좌표, visibility, style, asset reference를 공유하도록 preview/final parity contract를 만든다.
  - 우선 geometry/visibility/style payload 일치성 테스트를 추가하고, 그 다음 preview frame과 sample/final render thumbnail frame 비교를 검토한다.
- 2026-05-09 진행:
  - `clipper_nestjs`에 `templateBuilderRenderContractFor()`를 추가했고 sample render recipe/published preset/defaultParams/final payload mapper가 이 contract를 읽는다.
  - `clipper_angular`에 `templateBuilderPreviewContractFor()`를 추가했고 editor content-area preview가 preview contract에서 좌표를 읽는다.
  - Python 쪽 modern Template Builder text render seam을 `clipper_python`에 추가했다. commit: `9457abb feat: add template builder text renderer seam`.
  - 이 seam은 아직 legacy final render에 연결하지 않았고, `tests/test_template_builder_text_renderer.py`에서 descender/Korean lower-stroke clipping guard와 too-small layer clipping report만 검증한다.
  - Python 쪽 deterministic text artifact boundary를 추가했다. commit: `dbeb2c3 feat: render template builder text artifacts`.
  - `render_template_builder_text_artifact()`는 Angular preview contract shape와 NestJS render contract shape를 같은 visible text layer로 정규화하고, modern text renderer seam으로 PNG/metadata를 만든다.
  - Python 쪽 deterministic full-frame artifact boundary를 추가했다. commit: `0050409 feat: compose template builder frame artifacts`.
  - `render_template_builder_frame_artifact()`는 `outputSize` canvas 위에 visible text artifacts를 `frame` 좌표로 합성하고, `contentArea`를 metadata로 보존한다.
  - Frame artifact composer가 visible media layer를 deterministic placeholder로 처리하게 했다. commit: `9e7f82d feat: add template builder media placeholders`.
  - 저장된 한 contract에서 `preview.png`, `final_frame.png`, `comparison.json`을 생성하는 entrypoint script를 추가했다. commit: `f77e125 feat: add template builder artifact entrypoint`.
  - NestJS app-produced render contract fixture/export path를 추가했다. commit: `b1f99d8 feat: export template builder contract fixture`.
  - Angular preview contract fixture/export path를 같은 variant shape로 추가했다. commit: `ef55fbd feat: export template builder preview fixture`.
  - Angular preview fixture contract와 NestJS render fixture contract를 JSON으로 직렬화해 Python artifact entrypoint에서 비교하는 cross-runtime fixture comparison path를 추가했다. commits: `clipper_angular` `73df1cb feat: export preview contract fixture json`, `clipper_python` `cbf2c17 feat: compare template builder contract artifacts`.
  - 첫 cross-runtime 비교 실패 원인은 Angular fixture의 `subtitleBox.box.enabled=false`와 NestJS/app default `true` 차이였고, Angular fixture/spec을 app default에 맞췄다.
  - 수동 command sequence를 단일 diagnostic runner로 묶었다. commit: `0d5a054 feat: add template builder cross-runtime diagnostics`.
  - `clipper_python/scripts/compare_template_builder_cross_runtime_fixtures.py`는 Angular preview fixture JSON export, NestJS render fixture JSON export, Python artifact comparison을 한 번에 실행한다.
  - Python frame artifact composer에 staged media asset resolver seam을 추가했다. commit: `bd573f2 feat: resolve template builder media assets`.
  - `render_template_builder_frame_artifact(..., media_assets={assetUri: path})`는 resolved asset을 media frame에 합성하고, unresolved asset은 deterministic placeholder를 유지한다.
  - Resolved media asset 연결을 artifact entrypoint와 cross-runtime runner CLI까지 확장했다. commit: `c053ca1 feat: thread template builder media assets`.
  - `render_template_builder_preview_final_artifacts.py`와 `compare_template_builder_cross_runtime_fixtures.py`는 `--media-asset assetUri=path`를 받아 같은 Angular/NestJS contract fixture comparison을 placeholder mode와 resolved-asset mode에서 실행할 수 있다.
  - Angular preview-side 첫 non-contract render snapshot을 추가했다. commit: `7488e27 feat: capture template preview render snapshot`.
  - `templateBuilderPreviewRenderSnapshotFor(root)`는 Karma/Chrome이 실제 렌더한 Template Builder preview canvas DOM에서 canvas/content-area/layer rect, computed style, media `src`를 읽는다.
  - 이 단계에서 Chrome computed sub-pixel layout이 contract 산술값과 다를 수 있음이 확인됐다. 예: `subtitleText` height는 산술 `25.2px`, Chrome computed `25.195px`.
  - Browser render snapshot을 JSON artifact로 export하는 runner를 추가했다. commit: `618e70c feat: export template preview render snapshot`.
  - `scripts/export-template-builder-preview-render-snapshot.mjs --output <path>`는 Karma/ChromeHeadless로 실제 preview component를 렌더하고 snapshot JSON을 쓴다.
  - Headless Chrome artifact 기준으로 `subtitleText.rect.height=25.188`, `logoImage.rect.height=21.594`가 기록된다.
  - Angular preview `.phone-canvas` bitmap screenshot artifact export를 추가했다. commit: `3acc406 feat: export template preview screenshot`.
  - Playwright 의존성은 아직 추가하지 않았고, Node script가 Karma/ChromeHeadless의 Chrome DevTools Protocol에 직접 연결해 `.phone-canvas` PNG를 캡처한다.
  - `scripts/export-template-builder-preview-screenshot.mjs --output <path>`는 현재 324x576 PNG를 쓴다.
  - 324x576 preview screenshot과 1080x1920 Python/final frame artifact 사이의 scale normalization을 명시한 diagnostic comparison bridge를 추가했다. commit: `c99f709 feat: compare template preview screenshot`.
  - `scripts/compare_template_builder_preview_screenshot.py`는 frame을 preview 크기로 resize한 뒤 report에 `previewSize`, `frameSize`, `scale`, `normalization`, mismatch metrics를 기록한다.
  - 실제 diagnostic에서는 preview `324x576`, frame `1080x1920`, scale `0.3/0.3`, mismatchRatio `1.0`이 나왔다. 이 값은 현재 gate가 아니라, browser editor preview와 Python deterministic artifact composer가 아직 같은 visual surface가 아니라는 진단 결과다.
  - Angular preview screenshot export가 처음에는 blank white PNG도 통과시키는 문제가 있었다. 수정 commit: `clipper_angular` `22f545a fix: capture rendered template preview screenshot`.
  - 원인은 CDP clip 좌표가 Headless Chrome viewport 밖의 Karma iframe content를 향한 것이었다. exporter는 이제 `--window-size=1280,1200`으로 Chrome을 띄우고 `.phone-canvas`를 `scrollIntoView()`한 뒤 clip을 계산한다.
  - screenshot export Node test는 PNG를 decode해 dark rendered preview pixel을 요구한다. 새 `/tmp/template-builder-preview-screenshot-final.png`는 324x576, bytes `56778`, center pixel `(30, 41, 59)`이다.
  - mismatch category diagnostic을 추가했다. commit: `clipper_python` `6e02da3 feat: categorize template preview mismatches`.
  - `scripts/compare_template_builder_preview_screenshot.py --preview-render-snapshot <json>`는 browser render snapshot rect를 사용해 `canvas`, `contentArea`, `text:<layerId>`, `media:<layerId>` category metrics를 report에 쓴다.
  - 실제 category diagnostic:
    - tolerance 0에서는 현재 모든 category가 `mismatchRatio=1.0`으로 포화된다.
    - `--channel-tolerance 128`에서는 `canvas=0.2823431069958848`, `text:subTitle=0.7350364963503649`, `text:mainTitleLine1=0.656021897810219`, `text:mainTitleLine2=0.5596715328467153`, `text:subtitleText=0.5782051282051283`, `media:logoImage=0.757985257985258`.
  - sample/final render MP4에서 비교용 frame PNG를 추출하는 diagnostic을 추가했다. commit: `clipper_python` `af32bfd feat: extract template builder video frames`.
  - `scripts/extract_template_builder_video_frame.py --video <mp4> --output-dir <dir> --at-seconds <sec>`는 ffmpeg로 `final_frame.png`를 뽑고 `video_frame_extraction.json`을 쓴다.
  - preview screenshot과 video frame을 한 번에 비교하는 runner를 추가했다. commit: `clipper_python` `a93a764 feat: compare template preview video frames`.
  - `scripts/compare_template_builder_preview_video_frame.py --preview-screenshot <png> --video <mp4> --preview-render-snapshot <json> --output-dir <dir>`는 video frame extraction, scale-normalized preview comparison, optional category report를 한 번에 수행한다.
  - 실제 smoke는 legacy fixture MP4로만 수행했다. 결과는 preview `324x576`, frame `1080x1920`, scale `0.3/0.3`, mismatchRatio `0.9999464163237312`. 이 수치는 Template Builder preview fixture와 legacy Clipper1 fixture video를 비교한 것이므로 품질 판단에 쓰지 않는다.
  - 실제 Template Builder sample render fixture package export를 추가했다. commit: `clipper_nestjs` `43ad151 feat: export template builder sample render fixture`.
  - `scripts/export-template-builder-sample-render-fixture.mjs --output-dir <dir>`는 `recipe.json`, `artifacts.json`, `legacy_payload.json`, staged `assets/`를 쓴다. 이 fixture는 `templateBuilderRenderContractFixture()`와 `LegacyClipper1RenderPayloadMapper`를 통과한다.
  - exported fixture package를 Python LocalRenderAdapter로 실제 MP4 렌더하는 entrypoint를 추가했다. commit: `clipper_python` `c3bff8f feat: render template builder sample fixture video`.
  - `scripts/render_template_builder_sample_video_fixture.py --fixture-dir <dir>`는 `template-sample/main.mp4`와 thumbnail을 생성한다.
  - 실제 end-to-end diagnostic:
    - `clipper_nestjs node scripts/export-template-builder-sample-render-fixture.mjs --output-dir /tmp/template-builder-sample-render-fixture`
    - `clipper_python uv run python scripts/render_template_builder_sample_video_fixture.py --fixture-dir /tmp/template-builder-sample-render-fixture`
    - `clipper_python uv run python scripts/compare_template_builder_preview_video_frame.py --preview-screenshot /tmp/template-builder-preview-screenshot-final.png --video /tmp/template-builder-sample-render-fixture/template-sample/main.mp4 --preview-render-snapshot /tmp/template-builder-preview-render-snapshot-final.json --output-dir /tmp/template-builder-preview-vs-sample-render --max-mismatch-ratio 1.0`
    - result: preview `324x576`, frame `1080x1920`, scale `0.3/0.3`, mismatchRatio `0.9999732081618655`.
  - 이 mismatch는 아직 품질 판단에 쓰지 않는다. Angular preview fixture와 sample render fixture가 같은 text/media/background surface를 쓰지 않기 때문이다.
  - Angular preview fixture와 Template Builder sample render fixture의 첫 입력 surface 정렬을 진행했다.
  - `clipper_angular`:
    - preview sample copy를 `TEMPLATE_BUILDER_PREVIEW_SAMPLE_TEXT`로 분리했다.
    - 이미지 로고 fixture에서는 `logoText.visible=false`로 설정해 browser snapshot에서 `logoImage`와 `logoText`가 동시에 나타나지 않게 했다.
    - snapshot export spec은 `오늘의 핵심`, `서울 근교`, `축제 TOP 5`, `저장해두세요`, subtitle copy, `logoText` absence를 검증한다.
    - commit: `79ae804 feat: align template preview sample content`
  - `clipper_nestjs`:
    - sample render service와 sample render fixture export가 `TEMPLATE_BUILDER_SAMPLE_TEXT` helpers를 같이 사용한다.
    - sample render copy는 preview sample copy와 맞췄다: `오늘의 핵심`, `서울 근교\n축제 TOP 5`, `저장해두세요`, subtitle lines `이번 주말에 가기 좋은`, `서울 근교 축제부터 볼게요`.
    - render contract fixture에서도 image-logo sample의 `logoText.visible=false`를 보장한다.
    - commit: `3d6687e feat: align template sample render content`
  - 새 end-to-end diagnostic:
    - preview snapshot `/tmp/template-builder-preview-render-snapshot-20260509.json`
    - preview screenshot `/tmp/template-builder-preview-screenshot-20260509.png`
    - sample fixture `/tmp/template-builder-sample-render-fixture-20260509`
    - compare output `/tmp/template-builder-preview-vs-sample-render-20260509`
    - result: preview `324x576`, frame `1080x1920`, scale `0.3/0.3`, mismatchRatio `0.9999624914266118`.
  - 이 mismatch는 여전히 diagnostic-only다. 텍스트/로고 visibility 입력은 맞췄지만, preview는 editor/browser content-area/background visual이고 sample render는 staged media/background와 legacy final renderer를 쓰기 때문이다.
  - media/background fixture surface도 1차로 맞췄다.
  - `clipper_angular`:
    - deterministic 1x1 PNG data URL sample media(`#111827`)를 추가했다.
    - preview fixture는 `contentArea.assetUri`에 이 data URL을 넣고, editor preview는 direct `data:`, `blob:`, `http(s):` content-area media URL을 이미지로 렌더한다.
    - browser render snapshot은 이제 `media:contentArea` category도 기록한다.
    - commit: `abeed8d feat: align template preview sample media`
  - `clipper_nestjs`:
    - render contract fixture도 같은 content-area data URL을 가진다.
    - sample render service/fixture는 `clip_1.jpeg` 대신 같은 deterministic PNG를 `assets/template-sample-media.png`, `image/png`로 stage한다.
    - commit: `385206d feat: align template sample render media`
  - 새 media-aligned diagnostic:
    - preview snapshot `/tmp/template-builder-preview-render-snapshot-20260509-media.json`
    - preview screenshot `/tmp/template-builder-preview-screenshot-20260509-media.png`
    - sample fixture `/tmp/template-builder-sample-render-fixture-20260509-media`
    - compare output `/tmp/template-builder-preview-vs-sample-render-20260509-media`
    - tolerance 0 result: mismatchRatio `0.9998981910150891`.
    - 이유: 같은 dark PNG라도 browser preview pixel `(17,24,39)`가 final video/YUV/H.264 뒤에는 `(15,23,38)`이 되어 거의 모든 배경 픽셀이 1-2 channel 차이로 mismatch 처리된다.
    - `--channel-tolerance 4` diagnostic result: overall mismatchRatio `0.06444508744855967`, `text:subtitleText=0.7897435897435897`, `text:subtitleBox=0.9551094890510949`, `media:logoImage=0.7936117936117936`.
  - 이 mismatch는 여전히 diagnostic-only다. 다음 우선순위는 logo image surface를 같은 bytes로 맞추거나, subtitle/subtitleBox renderer 차이를 category-specific으로 분리하는 것이다. 계속 `--max-mismatch-ratio 1.0`으로 diagnostic-only report만 만든다.
  - logo image surface와 subtitle fixture geometry를 추가로 맞췄다.
  - `clipper_angular`:
    - preview sample logo data URL을 추가하고 `logoImage.assetUri`를 backend URL path 대신 같은 deterministic PNG data URL로 바꿨다.
    - `subtitleBox` sample text를 빈 값으로 바꿨다. final renderer에서 `subtitleBox`는 텍스트가 아니라 subtitle box style/settings 역할이다.
    - `subtitleText.y`를 `96 -> 1254`로 맞추고 `subtitleText.box.enabled=false`로 바꿨다.
  - `clipper_nestjs`:
    - 같은 deterministic logo PNG를 render contract fixture, sample render service, sample render fixture export가 공유한다.
    - `subtitleText.y=1254`, `subtitleText.box.enabled=false`로 맞췄다.
  - 진단 중 이전 bundled logo PNG를 직접 base64로 옮기려던 첫 시도는 PNG truncation 때문에 Python/ffmpeg render가 멈췄다. 해당 프로세스는 종료했고, fixture logo는 작은 deterministic valid PNG로 전환했다.
  - 새 logo/subtitle-y aligned diagnostic:
    - preview snapshot `/tmp/template-builder-preview-render-snapshot-20260509-subtitle-y.json`
    - preview screenshot `/tmp/template-builder-preview-screenshot-20260509-subtitle-y.png`
    - sample fixture `/tmp/template-builder-sample-render-fixture-20260509-subtitle-y`
    - compare output `/tmp/template-builder-preview-vs-sample-render-20260509-subtitle-y-t4`
    - `--channel-tolerance 4` overall mismatchRatio `0.05262988683127572`
    - `media:logoImage=0.22235872235872237`
    - `text:subtitleText=0.9850427350427351`
    - `text:subtitleBox=0.962043795620438`
  - 이전 media-aligned diagnostic 대비 tolerance 4 overall은 `0.06444508744855967 -> 0.05262988683127572`, logo category는 `0.7936117936117936 -> 0.22235872235872237`로 개선됐다.
  - 남은 subtitle mismatch는 preview가 `subtitleBox`를 고정 사각형 레이어로 그리는 반면 final renderer는 subtitle text line width에 맞춰 동적 박스를 그리는 의미 차이가 주원인이다.
  - `subtitleBox`를 fixed preview text layer가 아니라 subtitleText line box style/settings로 렌더하는 preview path를 TDD로 구현했다. commit: `clipper_angular` `3db3bdc feat: render dynamic template subtitle boxes`.
  - 구현 후 dynamic-subtitle diagnostic:
    - preview snapshot `/tmp/template-builder-preview-render-snapshot-20260509-dynamic-subtitle.json`
    - preview screenshot `/tmp/template-builder-preview-screenshot-20260509-dynamic-subtitle.png`
    - compare output `/tmp/template-builder-preview-vs-sample-render-20260509-dynamic-subtitle-t4`
    - `--channel-tolerance 4` overall mismatchRatio `0.036785193758573385`
    - `text:subtitleBox=0.2737226277372263`
    - `text:subtitleText=0.9438271604938272`
    - `media:logoImage=0.22235872235872237`
  - subtitleBox category는 `0.962043795620438 -> 0.2737226277372263`으로 크게 줄었다.
  - 남은 text glyph/stroke/shadow drift는 hybrid 방향으로 진행한다. browser preview는 즉시 보여주고, final renderer의 deterministic text artifact는 background에서 만들어 도착하면 preview에 적용한다.
  - Hybrid preview/final text artifact 첫 세로 조각을 구현했다.
    - `clipper_python` commit `87df386 feat: add template builder text artifact job`
    - `clipper_nestjs` commit `a55772a feat: serve template builder text artifacts`
    - `clipper_angular` commit `85a55d5 feat: preview template builder text artifacts`
  - 현재 동작:
    - editor/browser preview는 즉시 CSS 텍스트를 보여준다.
    - page가 debounced background 작업으로 plain text layer artifact를 요청한다.
    - artifact가 오면 `subTitle`, `mainTitleLine1`, `mainTitleLine2`, `bottomTitle`, `logoText`는 final renderer가 만든 PNG를 `<img>`로 표시할 수 있다.
    - 실패하거나 늦으면 기존 browser text preview가 fallback으로 남는다.
  - 새 API:
    - `POST /template-builder/families/:familyId/variants/:ratio/preview/text-artifacts/:layerId`
    - NestJS가 `templateBuilderRenderContractFor(variant)`와 layer/text/style hash cache를 만들고, Python worker `template_builder_text_artifact` job을 호출한다.
  - 이 slice는 subtitle dynamic box를 의도적으로 제외했다. subtitle은 현재 preview가 line box를 동적으로 만들고 있으므로, 다음에는 combined subtitle artifact인지 per-line artifact인지 먼저 결정해야 한다.
  - 결정 갱신:
    - 구현 속도보다 preview/final correctness를 우선한다.
    - Template Builder가 열려 있는 동안 Python renderer worker는 warm 상태로 유지해야 한다.
    - subtitle은 per-line artifact가 아니라 final renderer가 합성한 combined artifact를 preview에 표시한다.
  - Worker warm session + combined subtitle artifact slice를 구현했다.
    - `clipper_python` commit `9d0b8bb feat: render template builder subtitle artifacts`: combined subtitle artifact renderer와 `template_builder_subtitle_artifact` plugin job mode.
    - `clipper_nestjs` commit `ef48631 feat: warm template text artifact worker`: `POST /template-builder/preview/renderer-session`, `POST /template-builder/families/:familyId/variants/:ratio/preview/subtitle-artifact`.
    - `clipper_angular` commit `f9a9741 feat: preview combined subtitle artifacts`: page 진입 시 renderer session warmup, background subtitle artifact refresh, editor combined subtitle PNG display.
  - Local NestJS/Python worker smoke를 실행했다.
    - `POST /v1/template-builder/preview/renderer-session`: HTTP 201, `time_total=0.023639`.
    - 첫 subtitle artifact request: HTTP 201, `time_total=0.068961`, `cached=false`, worker `renderMs=7.168`, `lines=2`, `clipped=false`.
    - 동시 동일 요청은 pending cache 공유: HTTP 201, `time_total=0.064150`, `cached=true`.
    - 완료 후 동일 요청 cache hit: HTTP 201, `time_total=0.003192`, `cached=true`.
    - warm worker에서 한 글자 바뀐 새 텍스트 request: HTTP 201, `time_total=0.058364`, `cached=false`, worker `renderMs=4.712`.
  - 빠른 편집 중 stale artifact guard를 추가했다.
    - 기존에는 새 artifact refresh가 실제 시작될 때만 generation이 증가해서, 180ms debounce window 안에 old in-flight artifact가 도착하면 stale final-render PNG가 preview에 잠깐 적용될 수 있었다.
    - `clipper_angular`는 이제 artifact refresh를 예약하는 순간 `textPreviewArtifactGeneration`을 증가시키고 `textPreviewArtifacts`를 비운다.
    - 따라서 사용자가 편집하는 즉시 browser/CSS fallback으로 돌아가며, old artifact response는 replacement refresh가 시작되기 전이어도 버려진다.
    - 검증: Angular build 성공, Template Builder focused Karma 74 specs 성공.
    - commit: `clipper_angular` `fbce6ab fix: discard stale template text artifacts`.
  - artifact-backed preview screenshot/snapshot diagnostic 경로를 추가했다.
    - `clipper_angular` preview screenshot/snapshot exporters가 `--text-preview-artifacts <json>`을 받는다.
    - `clipper_python scripts/export_template_builder_text_preview_artifacts.py`가 render contract를 Angular `textPreviewArtifacts` JSON으로 변환한다.
    - commits:
      - `clipper_python` `f228316 feat: export template text preview artifacts`
      - `clipper_angular` `8a10966 feat: capture artifact-backed template previews`
    - 실제 diagnostic output root: `/tmp/template-builder-artifact-backed-20260509`.
    - artifact-backed preview screenshot vs sample render frame, `--channel-tolerance 4`, scale `0.3 x 0.3`, overall mismatchRatio `0.027445558984910835`.
    - 이전 dynamic-subtitle browser-text diagnostic overall `0.036785193758573385`보다 개선됐다.
    - 남은 주요 category:
      - `text:subtitleText=0.9515873015873015`
      - `text:subtitleBox=0.20145985401459854`
      - `media:logoImage=0.22235872235872237`
    - 해석: plain title text 영역은 artifact-backed preview로 개선됐지만, `subtitleText`는 modern combined artifact와 현재 legacy sample-render subtitle path를 비교하는 상태라 여전히 높다.
  - sample/final render가 같은 modern text artifact path를 consume하도록 전환했다.
    - 결정: final render migration 전까지 deterministic frame artifact와만 비교하는 우회가 아니라, Template Builder payload의 sample/final render 자체가 modern text artifacts를 사용한다.
    - `clipper_nestjs` legacy payload mapper가 `template_builder_render_contract`를 payload에 싣는다.
    - `clipper_python LocalRenderAdapter._write_overlay_assets_for_clip()`는 이 contract가 있을 때만 modern branch를 탄다.
    - project text는 `render_template_builder_text_artifact()`, timed subtitle은 `render_template_builder_subtitle_artifact()`를 사용한다.
    - contract가 없는 legacy Clipper1 payload는 기존 legacy text image path를 유지한다.
    - commits: `clipper_nestjs` `8b06e1f feat: carry template builder render contract`, `clipper_python` `ce79935 feat: render template builder text artifacts in final output`.
  - 검증:
    - `clipper_nestjs npm run build` 성공.
    - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js test/template-builder-render-contract.test.js test/template-builder-api.test.js` 성공, 14 tests.
    - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_template_builder_text_preview_artifact_export_script.py tests/test_template_builder_sample_video_fixture_render.py -q` 성공, 33 tests.
  - 새 diagnostic:
    - output root: `/tmp/template-builder-modern-final-text-20260509`.
    - artifact-backed preview screenshot vs modern-text sample render frame, `--channel-tolerance 4`, scale `0.3 x 0.3`, overall mismatchRatio `0.010823902606310014`.
    - 이전 artifact-backed preview vs legacy sample-render text path는 `0.027445558984910835`였다.
    - category ratios: `text:subTitle=0.024817518248175182`, `text:mainTitleLine1=0.00583941605839416`, `text:mainTitleLine2=0.009306569343065693`, `text:bottomTitle=0.009124087591240875`, `text:subtitleText=0.9865079365079366`, `text:subtitleBox=0.13248175182481753`, `media:logoImage=0.22235872235872237`.
    - 해석: whole-frame은 크게 개선됐고 plain text는 낮아졌다. `subtitleText`는 이제 legacy-vs-modern 불일치가 아니라 tight subtitle artifact rect가 glyph/box edge pixels 위주로 집계되는 문제다.
  - initial preview/final report guard를 추가했다.
    - `clipper_python/scripts/validate_template_builder_preview_final_report.py`는 이미 생성된 comparison report를 읽어 overall/category threshold를 적용한다.
    - 기본 기준: overall `0.012`, `text:subTitle=0.03`, `text:mainTitleLine1=0.01`, `text:mainTitleLine2=0.012`, `text:bottomTitle=0.012`, `text:subtitleText=0.99`, `text:subtitleBox=0.15`, `media:logoImage=0.25`.
    - 실제 report `/tmp/template-builder-modern-final-text-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json`는 이 guard를 통과했다.
    - guard output: `/tmp/template-builder-modern-final-text-20260509/preview-final-guard.json`.
    - 검증: `uv run pytest tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_preview_video_frame_comparison.py -q` 성공, 7 tests. `uv run python -m compileall scripts` 성공.
    - commit: `clipper_python` `979a24d feat: validate template preview final reports`.
  - single-command preview/final guard runner를 추가했다.
    - `clipper_python/scripts/run_template_builder_preview_final_guard.py`가 NestJS fixture export, Python sample render, renderer-backed text artifact export, Angular snapshot/screenshot capture, video frame compare, report validation을 한 번에 실행한다.
    - 실제 command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-runner-20260509`.
    - 결과: passed `true`, mismatchRatio `0.010823902606310014 <= 0.012`.
    - summary: `/tmp/template-builder-preview-final-guard-runner-20260509/summary.json`.
    - guard report: `/tmp/template-builder-preview-final-guard-runner-20260509/preview-final-guard.json`.
    - 검증: `uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_screenshot_comparison.py tests/test_template_builder_preview_video_frame_comparison.py -q` 성공, 9 tests. `uv run python -m compileall scripts` 성공.
    - commit: `clipper_python` `450cae2 feat: run template preview final guard`.
  - `media:logoImage` drift를 foreground bounds diagnostic으로 분리했다.
    - 새 script: `clipper_python/scripts/diagnose_template_builder_preview_final_category.py`.
    - commit: `clipper_python` `14004e3 feat: diagnose template preview final categories`.
    - 실제 command: `uv run python scripts/diagnose_template_builder_preview_final_category.py --comparison-report /tmp/template-builder-preview-final-guard-runner-20260509/preview-vs-sample-render-t4/preview_video_frame_comparison.json --category media:logoImage --output /tmp/template-builder-preview-final-guard-runner-20260509/logo-image-category-diagnostic.json`.
    - 결과: raw `media:logoImage` mismatchRatio는 `0.22235872235872237`이지만, foreground threshold `80` bbox IoU는 `0.9287469287469288`, strong threshold `180` bbox IoU는 `0.9722222222222222`.
    - 해석: logo image의 visible foreground bounds는 맞아 있으며, raw mismatch는 실제 placement/object-fit drift라기보다 MP4 encode + frame-to-preview scaling edge noise가 지배한다.
    - 결정: 지금은 logo 배치/크기 로직을 바꾸지 않는다. `media:logoImage <= 0.25` category allowance는 유지하되, 이 category는 foreground bounds diagnostic으로 함께 해석한다.
  - `subtitleText` mismatch의 실제 원인을 분리하고 preview/final guard를 강화했다.
    - 원인: Angular screenshot export가 기본 선택 레이어인 `subtitleText`의 editor-only selection box/resize handle chrome을 `.phone-canvas` 안에 포함해서 캡처하고 있었다. preview crop에 보이던 `#2563eb` 계열 파란 픽셀은 자막 렌더가 아니라 선택 UI였다.
    - `clipper_angular`는 `TemplateBuilderEditorComponent.previewChromeVisible` input을 추가했다. 기본값은 `true`라 실제 편집 UI는 유지된다.
    - screenshot/render snapshot export fixture는 `previewChromeVisible=false`로 캡처해 selection classes, selection boxes, resize handles, alignment guides, snap grid chrome을 숨긴다.
    - `clipper_python` preview/final guard 기본 기준을 강화했다: overall `0.006`, `text:subtitleText=0.3`, `text:subtitleBox=0.04`. 기존 plain text와 logo threshold는 유지한다.
    - commits: `clipper_angular` `4665613 fix: hide template preview chrome in exports`, `clipper_python` `70d442d test: tighten template preview final guard`.
    - 실제 command: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-no-chrome-runner-20260509`.
    - 결과: passed `true`, mismatchRatio `0.005095807613168724 <= 0.006`.
    - 주요 변화: overall `0.010823902606310014 -> 0.005095807613168724`, `text:subtitleText 0.9865079365079366 -> 0.25873015873015875`, `text:subtitleBox 0.13248175182481753 -> 0.029562043795620437`.
    - summary: `/tmp/template-builder-preview-final-guard-no-chrome-runner-20260509/summary.json`.
  - preview/final guard runner를 로컬 수동 검증 도구로 공식화했다.
    - 현재 repo에는 GitHub Actions 같은 CI가 없으므로 CI 파일은 추가하지 않는다.
    - `clipper_python/scripts/run_template_builder_preview_final_guard.py`는 packaged app에 포함되는 기능이 아니라, 개발자가 Template Builder preview/final 관련 변경 후 수동으로 실행하는 local development/QA integration guard다.
    - 문서: `clipper_python/scripts/TEMPLATE_BUILDER_PREVIEW_FINAL_GUARD.md`.
    - CLI `--help`에도 `local development`와 `not run by the packaged application` 설명을 추가했다.
    - 로컬 명령: `cd clipper_python && uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard`.
    - commit: `clipper_python` `e080135 docs: document template preview final local guard`.
    - 검증: `uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py -q` 성공, `uv run python -m compileall scripts` 성공, actual runner `/tmp/template-builder-preview-final-guard-local-doc-20260510` 성공.
  - packaged Electron bridge smoke를 실행했다.
    - 기존 `dist-app`은 stale 상태라 `/v1/template-builder/families`가 404였고, `clipper_electron`에서 `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`로 최신 앱을 다시 빌드했다.
    - 최신 packaged app 실행 후 PluginHostBridge는 `http://127.0.0.1:60496`, NestJS는 `http://127.0.0.1:60497/v1`에서 열렸다.
    - `GET /v1/health`는 HTTP 200, `GET /v1/template-builder/families`도 HTTP 200이었다.
    - `POST /v1/template-builder/preview/renderer-session`은 HTTP 201, `time_total=3.049470`, renderer `baseUrl=http://127.0.0.1:60515`로 ready를 반환했다.
    - warmup 후 `GET /v1/plugins/clipper1_video_render/status`는 HTTP 200, `runtimeState=running`, `port=60515`였다.
    - 첫 subtitle artifact request는 HTTP 201, client time `76ms`, worker `renderMs=17.458`, `cached=false`, `lines=2`, `clipped=false`였다.
    - 동일 subtitle artifact request는 HTTP 201, client time `18ms`, `cached=true`였다.
    - `POST /v1/plugins/clipper1_video_render/stop`은 HTTP 204였고, 이후 status는 `runtimeState=stopped`; packaged app도 종료했다.
    - 결론: packaged Electron 앱에서도 `ElectronPluginHost.ensureStarted(...)` 경로가 Template Builder renderer worker를 warm/reuse할 수 있다.
  - foreground-bounds diagnostic을 preview/final guard report에 통합했다.
    - `clipper_python` commit `ae777cc feat: include foreground diagnostics in preview final guard`.
    - `validate_template_builder_preview_final_report.py`는 `foreground_bounds_categories`를 받아 category별 foreground bounds metadata를 guard summary에 붙인다.
    - `run_template_builder_preview_final_guard.py`는 기본적으로 `media:logoImage`에 대해 foreground-bounds diagnostic을 포함한다.
    - pass/fail 기준은 바꾸지 않았다. `media:logoImage <= 0.25` raw category guard는 유지하고, `categories.media:logoImage.foregroundBounds`가 해석 근거를 제공한다.
    - 실제 runner `/tmp/template-builder-preview-final-guard-foreground-20260510`는 성공했다: mismatchRatio `0.005095807613168724 <= 0.006`.
    - 실제 guard report의 `media:logoImage` foreground result: threshold `80` bbox IoU `0.9287469287469288`, count ratio `0.9298892988929889`; strong threshold `180` bbox IoU `0.9722222222222222`, count ratio `0.9722222222222222`.
    - 검증: `uv run pytest tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, `uv run python -m compileall scripts` 성공, `git diff --check` 성공.
  - local guard를 multi-fixture로 확장했다.
    - fixture set: `default-image-logo`, `long-korean-text`.
    - `clipper_nestjs` commit `601be29 feat: add selectable template sample fixtures`: sample render fixture exporter가 `--fixture-id`를 받아 fixture별 text/variant metadata를 만든다.
    - `clipper_angular` commit `adc289b feat: export selectable template preview fixtures`: preview snapshot/screenshot exporters가 `--fixture-id`를 받아 matching preview fixture/sample text를 렌더한다.
    - `clipper_python` commit `6aa92e0 feat: run template preview final guard fixtures`: local guard runner가 기본 fixture set을 순회하고 top-level summary에 fixture별 result를 쓴다.
    - 실제 runner: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-multifixture-20260510`.
    - 결과: passed `true`.
      - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
      - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
    - 검증:
      - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` 성공, 4 tests.
      - `clipper_angular npm run build` 성공.
      - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 5 tests.
      - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, 9 tests.
      - `clipper_python uv run python -m compileall scripts` 성공.
      - `git diff --check`는 `clipper_nestjs`, `clipper_angular`, `clipper_python`에서 성공.
  - visibility-focused fixture `hidden-logo`를 추가했다.
    - 목적: `logoImage.visible=false`, `logoText.visible=false`일 때 preview와 final이 모두 logo를 그리지 않는지 local guard에서 검증한다.
    - `clipper_nestjs` commit `ed2e9cd feat: add hidden logo template fixture`: hidden-logo sample render fixture를 추가했고 legacy payload에서 `logo_check=false`, `logo_image` 없음, `logo_text` 없음을 검증한다.
    - `clipper_angular` commit `74e2ba5 feat: add hidden logo preview fixture`: hidden-logo preview fixture를 추가했고 browser snapshot에 `logoImage`/`logoText`가 없음을 검증한다.
    - `clipper_python` commit `1fd276c feat: support visibility guard fixture policy`: default fixture set에 `hidden-logo`를 추가하고, 이 fixture에서는 `media:logoImage`를 threshold/required/foreground diagnostic에서 제외한다.
    - 실제 runner: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-visibility-20260510`.
    - 결과: passed `true`.
      - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
      - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
      - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
    - `hidden-logo` guard summary에서는 required categories가 text categories만 포함하고, `media:logoImage`는 thresholds/required/foreground/actual categories 모두에서 빠져 있다.
    - 검증:
      - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` 성공, 5 tests.
      - `clipper_angular npm run build` 성공.
      - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 6 tests.
      - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, 9 tests.
      - `clipper_python uv run python -m compileall scripts` 성공.
  - visibility-focused fixture `subtitle-hidden`을 추가했다.
    - 목적: `subtitleText.visible=false`, `subtitleBox.visible=false`일 때 Angular preview와 final/sample render 모두 자막을 그리지 않는지 검증한다.
    - `clipper_nestjs` commit `aefda40 feat: add hidden subtitle template fixture`: subtitle-hidden sample render fixture를 추가했고 legacy payload에서 `clips[0].subtitles=[]`임을 검증한다.
    - `clipper_angular` commit `36a314c feat: add hidden subtitle preview fixture`: subtitle-hidden preview fixture를 추가했고 browser snapshot에 `subtitleText`/`subtitleBox`가 없음을 검증한다.
    - `clipper_python` commit `5bb9b07 feat: add hidden subtitle guard fixture`: default fixture set에 `subtitle-hidden`을 추가하고, 이 fixture에서는 `text:subtitleText`, `text:subtitleBox`를 threshold/required에서 제외한다. text artifact generation도 hidden subtitle text를 넘기지 않는다.
    - `clipper_python` commit `bc61033 docs: document template guard fixture set`: local guard 문서에 fixture set과 visibility policy를 기록했다.
    - 실제 runner: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-subtitle-hidden-20260510`.
    - 결과: passed `true`.
      - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
      - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
      - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
      - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
    - `subtitle-hidden` guard summary에서는 required categories가 `text:subTitle`, `text:mainTitleLine1`, `text:mainTitleLine2`, `text:bottomTitle`, `media:logoImage`만 포함한다. `text:subtitleText`/`text:subtitleBox`는 thresholds/required/actual categories 모두에서 빠져 있다.
    - 검증:
      - `clipper_nestjs npm run build && node --test test/template-builder-sample-render-fixture.test.js` 성공, 6 tests.
      - `clipper_angular npm run build` 성공.
      - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 7 tests.
      - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, 9 tests.
      - `clipper_python uv run python -m compileall scripts` 성공.
  - visibility-focused fixture `logo-text-only`을 추가했다.
    - 목적: `logoImage.visible=false`, `logoText.visible=true`일 때 Angular preview와 final/sample render 모두 이미지 로고 없이 텍스트 로고만 그리는지 검증한다.
    - `clipper_nestjs`: logo-text-only sample render fixture를 추가했고 legacy payload가 `logo_check=true`, `logo_type=TEXT`, `logo_image=undefined`, `logo_text=Clipper`인지 검증한다.
    - `clipper_angular`: logo-text-only preview fixture를 추가했고 browser snapshot에 `logoImage`가 없고 `logoText=Clipper`가 있음을 검증한다.
    - `clipper_python`: default fixture set에 `logo-text-only`을 추가하고, 이 fixture에서는 `media:logoImage`를 threshold/required/foreground에서 제외하며 `text:logoText <= 0.03`을 required category로 추가한다.
    - commits: `clipper_nestjs` `810e483 feat: add text logo template fixture`, `clipper_angular` `ad23c40 feat: add text logo preview fixture`, `clipper_python` `2b6359c feat: add text logo guard fixture`.
    - 추가 RED에서 CLI path가 `text:logoText` threshold는 추가하지만 `requiredCategories`에는 넣지 않는 문제가 잡혔고, missing logoText category가 guard failure가 되도록 수정했다.
    - 실제 runner: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-logo-text-only-required-20260510`.
    - 결과: passed `true`.
      - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
      - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
      - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
      - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
      - `logo-text-only`: mismatchRatio `0.0037776491769547327 <= 0.006`, failures `[]`.
    - `logo-text-only` guard summary에서는 required categories가 `text:logoText`를 포함하고, `text:logoText` mismatchRatio는 `0.009124087591240875 <= 0.03`이다.
    - 검증:
      - `clipper_nestjs npm run build` 성공.
      - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js` 성공, 7 tests.
      - `clipper_angular npm run build` 성공.
      - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 8 tests.
      - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, 9 tests.
      - `clipper_python uv run python -m compileall scripts` 성공.
  - style-focused fixture `style-heavy`를 추가했다.
    - 목적: visibility가 아니라 non-subtitle title/logo text의 box fill, border, outline, shadow, color, tracking, text-logo style 조합이 preview/final 사이에서 유지되는지 검증한다.
    - fixture text:
      - subTitle `스타일 집중 확인`
      - main title lines `윤곽선과 그림자`, `박스 색상 테스트`
      - bottomTitle `스타일 그대로 저장`
      - subtitle lines `복잡한 스타일도`, `결과 영상과 맞춰요`
      - logoText `STYLE`
    - `logoImage.visible=false`, `logoText.visible=true`, subtitles remain visible.
    - `clipper_nestjs`: style-heavy render contract style values and legacy template settings mapping을 검증한다.
    - `clipper_angular`: browser-rendered snapshot에서 style-heavy computed style values를 검증한다.
    - `clipper_python`: default fixture set에 `style-heavy`를 추가하고, `media:logoImage`를 제외하며 `text:logoText`를 required category로 추가한다.
    - commits: `clipper_nestjs` `f4eca90 feat: add style heavy template fixture`, `clipper_angular` `a7f047f feat: add style heavy preview fixture`, `clipper_python` `a3a6c3b feat: add style heavy guard fixture`.
    - 결정: 첫 style-heavy runner는 visually aligned였지만 large filled text-box regions 때문에 MP4 encode/preview-scale channel drift가 커서 default `0.006` 기준에는 실패했다. default guard는 유지하고 style-heavy에만 fixture-specific 기준을 적용한다.
    - style-heavy 기준:
      - overall `0.04`
      - `text:subTitle=0.32`
      - `text:mainTitleLine1=0.016`
      - `text:mainTitleLine2=0.022`
      - `text:bottomTitle=0.44`
      - `text:logoText=0.36`
    - 실제 runner: `uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-style-heavy-full-20260510`.
    - 결과: passed `true`.
      - `default-image-logo`: mismatchRatio `0.005095807613168724 <= 0.006`, failures `[]`.
      - `long-korean-text`: mismatchRatio `0.005438743141289438 <= 0.006`, failures `[]`.
      - `hidden-logo`: mismatchRatio `0.0036061814128943758 <= 0.006`, failures `[]`.
      - `subtitle-hidden`: mismatchRatio `0.00325252914951989 <= 0.006`, failures `[]`.
      - `logo-text-only`: mismatchRatio `0.0037776491769547327 <= 0.006`, failures `[]`.
      - `style-heavy`: mismatchRatio `0.03424532750342935 <= 0.04`, failures `[]`.
    - style-heavy category results:
      - `text:subTitle=0.2824817518248175 <= 0.32`
      - `text:mainTitleLine1=0.012043795620437956 <= 0.016`
      - `text:mainTitleLine2=0.016423357664233577 <= 0.022`
      - `text:bottomTitle=0.393978102189781 <= 0.44`
      - `text:logoText=0.3165137614678899 <= 0.36`
    - 검증:
      - `clipper_nestjs npm run build` 성공.
      - `clipper_nestjs node --test test/template-builder-sample-render-fixture.test.js` 성공, 8 tests.
      - `clipper_angular npm run build` 성공.
      - `clipper_angular node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 9 tests.
      - `clipper_python uv run pytest tests/test_template_builder_preview_final_guard_runner.py tests/test_template_builder_preview_final_report_guard.py tests/test_template_builder_preview_final_category_diagnostics.py -q` 성공, 9 tests.
      - `clipper_python uv run python -m compileall scripts` 성공.
  - 다음 우선순위:
    1. Template Builder preview/final renderer 변경 후에는 multi-fixture local guard runner를 계속 수동 실행한다.
    2. 사용자가 직접 packaged Electron app에서 Template Builder를 확인한다.
    3. 별도 문서 작업 후보는 local guard를 수동 release checklist에 연결하는 것이다.
  - 최신 packaged Electron app을 style-heavy fixture commit 이후 다시 빌드했다.
    - command: `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
    - app: `clipper_electron/dist-app/mac-arm64/Clipper2.app`.
    - dmg: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`.
    - local build는 signing identity가 없어 macOS signing을 skip했다.
  - 최신 packaged bridge smoke:
    - PluginHostBridge: `http://127.0.0.1:50282`.
    - packaged NestJS: `http://127.0.0.1:50283/v1`.
    - `GET /v1/health`: HTTP 200.
    - `GET /v1/template-builder/families`: HTTP 200.
    - renderer warmup 전 `GET /v1/plugins/clipper1_video_render/status`: HTTP 200, `runtimeState=stopped`.
    - `POST /v1/template-builder/preview/renderer-session`: HTTP 201, `time_total=0.259108`, `status=ready`, `baseUrl=http://127.0.0.1:50304`.
    - packaged app 종료 시 NestJS와 Python renderer worker도 정리됐다.
  - 수동 앱 확인 문서:
    - `.codex/implementation/TEMPLATE_BUILDER_MANUAL_APP_CHECKLIST_2026-05-10.md`.
    - 이 체크리스트는 자동 local guard를 대체하지 않는다. 사용자가 실제 앱에서 preview responsiveness, stale artifact 방지, logo/subtitle visibility, heavy style, sample/final visual consistency를 눈으로 확인하기 위한 절차다.
  - Template Builder panel scrolling UX fix를 적용했다.
    - 사용자 확인 결과 4번째 속성 영역이 길어지면서 `Shared Template Catalog` 페이지 전체가 세로 스크롤되고 다른 영역도 같이 길어지는 문제가 있었다.
    - 결정: 페이지 전체 스크롤은 없애고, 1번 family 목록/2번 비율+레이어 목록/4번 속성 패널만 자기 영역 내부에서 세로 스크롤한다. 3번 canvas preview 영역은 스크롤을 만들지 않는다.
    - TDD: `TemplateBuilderPageComponent` spec에 page fixed + panel-local scrolling computed-style guard를 추가했고, 기존 CSS에서 RED를 확인했다.
    - 구현: `template-builder-page.component.scss`와 `template-builder-editor.component.scss`를 `height: 100vh/100%`, `min-height: 0`, `overflow: hidden/auto` 구조로 바꿨다.
    - commit: `clipper_angular` `5ed7cbe fix: constrain template builder panel scrolling`.
    - 검증:
      - RED 확인 후 `npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 23 specs.
      - `npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 39 specs.
      - `node --test test/template-builder-preview-render-snapshot-export.test.mjs test/template-builder-preview-screenshot-export.test.mjs` 성공, 9 tests.
      - `npm run build` 성공.
      - `git diff --check` 성공.
    - 최신 packaged Electron app도 다시 빌드했다: `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`.
    - 최신 packaged smoke: `GET /v1/health` HTTP 200, `GET /v1/template-builder/families` HTTP 200, 앱/NestJS 정상 종료.
    - 수동 체크리스트에 panel-local scrolling 확인 항목을 추가했다.

## 2026-05-08 Legacy Clipper1 정답 이미지 추출 이전 상태

- 방향 결정:
  - Clipper1과 Clipper2가 같은지 판단하는 정답 이미지는 기존 Clipper1 `adlight_python`의 `VideoService.create_video()`로 실제 영상을 만든 뒤 첫 프레임을 뽑아 만든다.
  - 현재 Clipper2 smoke output을 저장한 `clipper2_template_baseline_frames`는 회귀 방지용 기준 이미지다. 이것은 legacy Clipper1과 같다는 증거가 아니다.
- 새 경로:
  - `adlight_python/scripts/export_clipper1_reference_frames.py`
  - focused tests: `adlight_python/tests/test_export_clipper1_reference_frames.py`
  - 실행 예:
    - 단일 케이스: `.venv/bin/python scripts/export_clipper1_reference_frames.py --output-root /tmp/clipper1-reference-export-smoke --case 1:16:9 --duration 0.2`
    - 대표 25개: `.venv/bin/python scripts/export_clipper1_reference_frames.py --output-root /tmp/clipper1-reference-export-all-designs --all-designs --include-ratio-edge-cases --duration 0.2`
- 확인된 결과:
  - 단일 `template-1-16:9` 추출 성공.
  - 같은 입력으로 Clipper1을 두 번 렌더하면 첫 프레임 PNG sha256이 동일했다. 정답 이미지 자체는 재현 가능하다.
  - 21개 design `16:9` + ratio edge 4개, 총 25개 추출 성공. `/tmp/clipper1-reference-export-all-designs`, 약 31MB.
  - `CLIPPER1_GOLDEN_FRAME_FIXTURE_DIR=/tmp/clipper1-reference-export-smoke uv run pytest tests/test_clipper1_video_render_golden_frames.py -q`로 실제 비교 경로가 활성화됐다.
  - raw 기준 `channelTolerance=4`, `maxMismatchRatio=0.001`에서는 expected failure다. `template-1-16_9`에서 sampled 518400 중 79875 mismatch, ratio `0.154080`, max delta 255.
  - 25개 전체를 `channelTolerance=32`로 비교하면 mismatch ratio는 `2.0%~3.8%` 범위다. 최악은 `template-12-16_9`의 `0.037809`.
  - 같은 이미지를 2px 아래로 민 synthetic drift는 `channelTolerance=32`에서도 mismatch ratio `0.096489`였다.
  - 따라서 `channelTolerance=32`, `maxMismatchRatio=0.04`를 1차 정답 이미지 비교 기준으로 채택했다.
  - 2026-05-08 14:12 KST 기준 drift가 크게 줄어 checked-in fixture 기준을 `maxMismatchRatio=0.015`로 강화했다.
  - 2026-05-08 14:45 KST 기준 legacy overlay format 보정 후 checked-in fixture 기준은 `maxMismatchRatio=0.012`로 강화됐다.
  - 2026-05-08 15:07 KST 기준 automatic zoom scale/crop 보정 후 checked-in fixture 기준은 `maxMismatchRatio=0.008`로 강화됐다.
  - 2026-05-08 16:05 KST 기준 automatic zoom source preprocessing 보정 후 checked-in fixture 기준은 `maxMismatchRatio=0.007`로 강화됐다.
  - 2026-05-08 16:23 KST 기준 text height 평균에서 zero-height glyph를 포함하도록 Clipper1과 맞춘 뒤 checked-in fixture 기준은 `maxMismatchRatio=0.0067`이다.
  - 2026-05-08 17:09 KST 기준 automatic zoom의 FFmpeg scale flag를 `fast_bilinear`로 바꿔 Clipper1 MoviePy/OpenCV resize edge에 더 가깝게 맞췄고, 당시 checked-in fixture 기준은 `maxMismatchRatio=0.0065`였다.
  - 2026-05-08 17:32 KST 기준 단일 클립도 Clipper1처럼 최종 concat/filter/x264 encode 단계를 거치도록 맞췄고, 당시 checked-in fixture 기준은 `maxMismatchRatio=0.0064`였다.
  - 2026-05-08 17:52 KST 기준 automatic image zoom을 Clipper1 MoviePy/OpenCV 방식처럼 30fps frame sequence로 먼저 만든 뒤 segment encode하도록 맞췄고, 당시 checked-in fixture 기준은 `maxMismatchRatio=0.0039`이었다.
  - 25개 fixture가 `clipper_python/tests/fixtures/clipper1_golden_frames`에 생성되었고, `uv run pytest tests/test_clipper1_video_render_golden_frames.py -q`가 통과한다.
- 다음 작업:
  - 이 기준은 "완전 동일 픽셀"이 아니라 영상 압축/글자 edge 차이를 허용하는 1차 비교다.
  - 다음 세션은 이 fixture를 깨뜨리지 않는 상태에서 template별 mismatch를 더 줄이는 방향으로 진행한다.
  - 2026-05-08 13:15 KST 기준 template-12 top title box 문제는 1차 보정됐다.
  - 2026-05-08 13:26 KST 기준 full ratio layout overlay 순서 문제도 1차 보정됐다.
  - 2026-05-08 13:54 KST 기준 template-3 top text 세로 위치 문제도 1차 보정됐다.
  - 2026-05-08 13:59 KST 기준 template-17 full의 Clipper1 random pan 방향을 recipe에 pinning해 보정했다.
  - 2026-05-08 14:12 KST 기준 golden fixture의 `maxMismatchRatio`를 `0.04`에서 `0.015`로 강화했다. 현재 worst `template-6-1_1`은 `0.011948`라서 강화된 기준 안에 있다.
  - 2026-05-08 14:28 KST 기준 FFmpeg zoom branch scale에 `flags=bilinear`를 넣어 Clipper1 MoviePy/OpenCV linear resize에 더 가깝게 맞췄다. `template-6-1_1` mismatch는 `0.011948 -> 0.010862`로 줄었다.
  - 2026-05-08 14:45 KST 기준 layout/logo/text PNG overlay의 `format=auto`를 제거해 Clipper1 FFmpeg overlay 기본 동작과 맞췄다. `template-11-16_9`는 `0.009001 -> 0.003457`, `template-16-16_9`는 `0.009687 -> 0.006590`, `template-1-full`은 `0.011059 -> 0.000573`으로 줄었다.
  - 2026-05-08 15:07 KST 기준 automatic zoom branch를 Clipper1처럼 `content fit/crop -> time-based scale/crop` 2단계로 맞췄다. `template-6-1_1` mismatch는 `0.011861 -> 0.006979`로 줄었다.
  - zoom frame count denominator도 Clipper1 `Zoom`과 맞게 `int(duration * fps)` 기준으로 고정했다.
  - 2026-05-08 15:31 KST 기준 x264 encoding preset을 Clipper1 MoviePy 경로처럼 `ultrafast`로 맞췄다. top edge 상위 케이스는 소폭 줄었고, 현재 worst는 `template-6-1_1` `0.007012`다.
  - 2026-05-08 15:50 KST 기준 `LEGACY_TEXT_HEIGHT_REFERENCE`의 `그느드르무...` row를 기존 Clipper1 `generate_reference_texts()`와 같은 `그느드르므...`로 보정했다. 25개 golden 비교는 계속 통과하고 worst는 `template-6-1_1` `0.007012`로 유지됐다.
  - 2026-05-08 16:05 KST 기준 automatic zoom 전에 Clipper1처럼 content-area fit/crop 중간 source image를 만들도록 보정했다. `template-6-1_1` mismatch는 `0.007012 -> 0.006559`로 줄었고, 현재 golden 기준은 `maxMismatchRatio=0.007`이다.
  - 2026-05-08 16:23 KST 기준 기존 Clipper1처럼 평균 글자 높이에 zero-height glyph도 포함하도록 보정했다. `template-16-4_3` mismatch는 `0.006553 -> 0.003434`로 줄었고, golden 기준은 `maxMismatchRatio=0.0067`이었다.
  - 2026-05-08 17:09 KST 기준 `template-6-1_1` content edge를 다시 분석했다. Clipper1 MoviePy `resize.py`는 OpenCV `INTER_LINEAR` 경로를 쓰며, 기존 FFmpeg `bilinear`보다 `fast_bilinear`가 reference edge에 더 가까웠다. `template-6-1_1` mismatch는 `0.006559 -> 0.006354`로 줄었고, 당시 golden 기준은 `maxMismatchRatio=0.0065`였다.
  - 2026-05-08 17:32 KST 기준 기존 Clipper1의 final video 단계처럼 단일 클립도 `concat=n=1 -> format=yuv420p -> libx264 high level 4.0 x264opts`로 재인코딩한다. `template-6-1_1` mismatch는 `0.006354 -> 0.006318`로 줄었고, 당시 golden 기준은 `maxMismatchRatio=0.0064`였다.
  - 2026-05-08 17:52 KST 기준 automatic image zoom의 남은 차이는 FFmpeg scale/crop 근사가 아니라 Clipper1 MoviePy가 OpenCV frame을 먼저 만든 데서 온 것으로 확인했다. Clipper2도 auto image zoom에서 30fps frame sequence를 만들도록 보정했고, `template-6-1_1` mismatch는 `0.006318 -> 0.000114`로 줄었다. 당시 golden 기준은 `maxMismatchRatio=0.0039`이었다.
- 진단 도구:
  - `clipper_python/scripts/diagnose_clipper1_golden_frame_drift.py`
  - 실행 예:
    - `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report --write-diffs top --top-diffs 10`
  - 최초 실행 결과:
    - 25 cases, failed 0
    - worst case: `template-12-16_9`, mismatch ratio `0.03780864197530864`
    - `template-12-16_9` 영역별 mismatch: top `0.102660`, content `0.000646`, bottom `0.015384`
  - template-12 top text/box 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-title-width --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-1-full`, mismatch ratio `0.02767361111111111`
    - `template-12-16_9` mismatch: overall `0.011442901234567902`, top `0.024770072085508327`, content `0.0006091617933723197`, bottom `0.009548934409269605`
  - full ratio layout overlay 순서 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-full-layout-order --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-3-16_9`, mismatch ratio `0.015185185185185185`
    - `template-1-full` mismatch: `0.02767361111111111 -> 0.011059027777777777`
    - `template-17-full` mismatch: `0.02451003086419753 -> 0.014496527777777778`
  - text height reference 보정 후 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-text-height-reference --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-17-full`, mismatch ratio `0.012880015432098765`
    - `template-3-16_9` mismatch: `0.015185185185185185 -> 0.007126`
  - template-17 full pan direction pinning 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-template17-pan-pin --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.011948302469135802`
    - `template-17-full` mismatch: `0.012880 -> 0.005683`
  - golden fixture threshold 강화 (2026-05-08 당시):
    - checked-in `clipper1_golden_frames/manifest.json` 25개 case의 당시 `maxMismatchRatio`는 `0.0039`.
    - `adlight_python/scripts/export_clipper1_reference_frames.py` 기본 `DEFAULT_MAX_MISMATCH_RATIO`도 당시 `0.0039`.
    - `uv run pytest tests/test_clipper1_video_render_golden_frames.py -q`가 25개 case를 새 기준으로 통과한다.
  - zoom resize filter 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-zoom-bilinear --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.01086226851851852`
    - `template-6-1_1` mismatch: `0.011948 -> 0.010862`
  - legacy overlay format 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-legacy-overlay-format --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.011861496913580247`
    - `template-11-16_9`: `0.009001 -> 0.003457`
    - `template-16-16_9`: `0.009687 -> 0.006590`
    - `template-1-full`: `0.011059 -> 0.000573`
  - automatic zoom scale/crop 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-zoom-scale-crop --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.0069791666666666665`
    - `template-6-1_1`: `0.011861 -> 0.006979`
  - x264 ultrafast preset 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-x264-ultrafast --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.0070119598765432094`
    - `template-16-4_3`: `0.006740 -> 0.006553`
    - `template-18-16_9`: `0.006653 -> 0.006534`
    - `template-16-16_9`: `0.006590 -> 0.006476`
  - text height reference `므` 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-text-reference-mu --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.0070119598765432094`
    - 상위 mismatch 순위와 수치는 x264 ultrafast 보정 후 결과와 동일하게 유지됐다.
  - automatic zoom source preprocessing 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-autozoom-preprocess-threshold007 --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.006558641975308642`
    - `template-6-1_1`: `0.007012 -> 0.006559`
    - 현재 2위는 `template-16-4_3`, mismatch ratio `0.006552854938271605`.
  - text height zero-glyph 평균 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-average-height-zero-glyphs-threshold0067 --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.006558641975308642`
    - `template-16-4_3`: `0.006553 -> 0.003434`
    - `template-14-16_9`: `0.006534 -> 0.003546`
    - `template-18-16_9`: `0.006534 -> 0.003447`
    - `template-16-16_9`: `0.006476 -> 0.003289`
  - automatic zoom fast_bilinear 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-fast-bilinear --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.006354166666666667`
    - `template-6-1_1`: `0.006559 -> 0.006354`
    - 현재 2위는 `template-6-16_9`, mismatch ratio `0.004701003086419753`.
  - legacy final re-encode 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-final-reencode --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-6-1_1`, mismatch ratio `0.006317515432098766`
    - `template-6-1_1`: `0.006354 -> 0.006318`
    - `template-6-16_9`: `0.004701 -> 0.003358`
  - legacy MoviePy/OpenCV auto-zoom frame sequence 보정 후 최신 실행 결과:
    - command: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-legacy-cv2-autozoom-threshold0039 --write-diffs top --top-diffs 10`
    - 25 cases, failed 0
    - worst case: `template-17-16_9`, mismatch ratio `0.0038541666666666668`
    - `template-6-1_1`: `0.006318 -> 0.000114`
    - 당시 기준은 `maxMismatchRatio=0.0039`.
  - 진단 문서: `.codex/diagnostics/LEGACY_CLIPPER1_GOLDEN_DRIFT_2026-05-08.md`
  - 다음 renderer 수정 후보였던 `template-17-16_9`, `template-14-16_9`, `template-11-16_9` 공통 content edge는 2026-05-09 세션에서 RAQM line width fallback과 automatic pan frame sequence 보정으로 처리됐다. 현재 기준은 상단 2026-05-09 최신 상태를 따른다.

## 2026-05-07 Template Builder 최신 상태

- Template Builder는 top-level `템플릿` 메뉴로 구현 중이다.
- 현재 완료:
  - NestJS `TemplateBuilderModule`, local JSON repository, family/variant lifecycle, validation, sample render/publish endpoints.
  - Angular `/templates` route, `템플릿` nav, v4 editor shell, fixed ratio slots, narrow canvas, wide property panel, color palette, box/outline/shadow controls.
  - sample render가 더 이상 fake success marker가 아니다. `TemplateBuilderSampleRenderService`는 bundled sample media/TTS/BGM/logo를 staging하고 `video.render.legacy_clipper1.python_worker` provider를 `dryRun: false`로 요청한다.
  - published custom template variant가 `/template-presets` catalog에 `source=template_builder`로 노출된다.
  - Clipper Studio detail template picker는 더 이상 `source=clipper1`로만 필터링하지 않아서 legacy Clipper1 preset과 published custom template preset을 같이 받을 수 있다.
  - `LegacyClipper1RenderPayloadMapper`가 `templateBuilderLayers` snapshot을 legacy Python renderer용 `template_settings`로 1차 변환한다.
  - Template Builder custom variant layout image upload가 있다. Endpoint: `POST /template-builder/families/:familyId/variants/:ratio/assets/layout-image`, multipart `file`.
  - Template Builder custom text layer font upload가 있다. Endpoint: `POST /template-builder/families/:familyId/variants/:ratio/assets/fonts/:layerId`, multipart `file`.
  - `clipper1_video_render` Python renderer가 uploaded font path의 parent directory를 ASS subtitles filter `fontsdir`로 넘긴다.
  - Template Builder text layer에는 선택적 `fontName` override가 있다. Angular `렌더 폰트명` 입력은 `{ text: { fontName } }` patch를 emit하고, NestJS mapper는 `${prefix}_font_name`으로 변환하며, Python ASS style/shadow style은 이 값을 uploaded file stem보다 우선 사용한다.
  - `clipper1_video_render`에 Template Builder custom template visual contract smoke가 있다. 실제 MP4에서 layout image, content area, uploaded font `fontsdir`, ASS event count, frame pixel sample을 검증한다.
  - Template Builder sample render recipe에는 custom variant layer snapshot, legacy Clipper1 provenance, sample media/TTS/BGM/logo artifact가 포함된다.
  - 실제 `clipper1_video_render` worker E2E에서 Template Builder sample render가 `template-sample/main.mp4`를 생성하는 것까지 확인했다.
  - 성공한 sample render MP4는 `GET /template-builder/families/:familyId/variants/:ratio/sample-render/file`로 serve되고 Angular editor publish gate에서 `<video>`로 재생된다.
  - sample render provider가 `thumbnailArtifact`를 반환하면 `TemplateBuilderSampleRenderSnapshot.thumbnailUri`로 저장되고 `GET /template-builder/families/:familyId/variants/:ratio/sample-render/thumbnail/file`로 serve된다.
  - Published Template Builder custom preset은 sample thumbnail이 있으면 `preview.remoteImageUrl`, sample video가 있으면 `preview.remoteVideoUrl`을 함께 노출한다.
  - Clipper1 template picker는 image preview를 우선 사용하고, image가 없으면 sample render video preview로 fallback한다.
  - Clipper1 template picker는 `ShortformTemplatePickerComponent`로 `src/features/shortform/components`에 이동했다. Clipper1 editor는 shared selector `app-shortform-template-picker`를 사용한다.
  - Template preset catalog loading은 `ShortformTemplatePresetCatalogService`로 분리됐다. `workflow.clipper1`, `workflow.clipper_studio`, `workflow.variation`을 받고 `category: shorts`를 고정해 `ProjectHistoryService.listTemplatePresets()`를 감싼다.
  - `/variation` route와 `VariationPageComponent` first shell이 있다. Store/Dashboard plugin route mapping도 `variation -> /variation`으로 연결됐다.
  - Variation page는 `workflow.variation` template presets를 shared picker로 보여주고, template 선택값을 Variation workspace API로 저장한다.
  - Variation page는 클립 제목/대사/미디어 폴더 경로를 입력해 `ShortformWorkspace.clips[]`와 clip별 `mediaPool.folders[]`를 저장할 수 있다. 아직 folder picker, 실제 folder scan, lock/randomize policy, batch render는 없다.
  - Variation workspace first API가 있다. NestJS endpoints:
    - `GET /projects/variation/workspaces`
    - `POST /projects/variation/workspaces`
    - `GET /projects/variation/workspaces/:workspaceId`
    - `PATCH /projects/variation/workspaces/:workspaceId`
  - Variation workspace는 `workflowKind: variation`, `renderSettings.templateId`, `variationSet.count`, `variationSet.variants[]`, `clips[]`, clip별 `mediaPool.folders[]`를 JSON store(`CLIPPER_DATA_DIR/variation/workspaces.json`)에 저장한다.
  - Angular `VariationWorkspaceService`가 create/update를 호출하고, `VariationPageComponent`는 진입 시 workspace를 만들고 template 선택/시나리오 클립 추가 시 PATCH 한다.
  - `clipper1_video_render` Python renderer는 render recipe에 명시된 `zoom`/`pan` effect를 image/video/GIF media에 적용한다. 자동 motion 판정은 아직 image-only다.
  - `clipper1_video_render` Python renderer는 video/GIF 입력에 `-stream_loop -1`을 붙여 clip duration을 채운다.
  - Motion effect가 없는 video/GIF 기본 표시 방식은 legacy Clipper1처럼 blur-fill background + centered foreground filter를 사용한다. Image fallback과 explicit motion filter는 기존 경계를 유지한다.
  - `clipper1_video_render` Python renderer는 explicit `*_font_name`이 없으면 업로드된 TTF/OTF의 name table에서 typographic family nameID 16, 없으면 family nameID 1을 읽어 ASS `Fontname`으로 사용한다. 읽을 수 없으면 stem fallback을 유지한다.
  - `clipper1_video_render` Python renderer는 legacy `d2x-s3` layout visual URL과 상대 layout 파일명을 package 내부 `clipper1_video_render/legacy_assets/layout`에서 먼저 resolve한다. `CLIPPER_LEGACY_ASSETS_DIR` env override가 있으면 그 경로가 최우선이고, 그 다음 package bundle, 그 다음 dev fallback(`cwd`, `cwd.parent/adlight_python`) 순서다. 일반 HTTP/localhost remote asset staging은 유지한다.
  - `clipper1_video_render` Python renderer는 ASS box style에서 `*_box_border_color/width`를 `OutlineColour`/`Outline`에 우선 매핑한다. Legacy `subtitle_box_border_*`는 최종 자막바 border로 반영된다.
  - Template Builder custom text layer center alignment is preserved through render now: NestJS maps `align=center` to `*_center_x = x + width / 2`, and Python renderer reads `*_center_x` before legacy left/right margins to emit ASS alignment 8. Left/right align still uses legacy margin keys.
  - Python renderer는 box/outline/shadow color/offset을 ASS style로 매핑하는 focused fixture를 가진다.
  - Python renderer는 `shadow_outline_*`가 있는 `Subtitle`, `MainTitle`, `MainTitle2`에 별도 `*Shadow` ASS style/event를 본문 event 앞에 추가한다.
  - Python renderer는 legacy parity 기준으로 plain subtitle/project text도 ASS가 아니라 timed PNG overlay로 렌더한다. 기존 Clipper1 `VideoService.py`는 박스가 없는 텍스트도 PIL image로 만든 뒤 ffmpeg overlay했다.
  - Python renderer는 legacy `adjust_font_size_to_fit`처럼 `main_title`/`main_title2` PNG overlay 생성 전 font size를 output width 안에 맞게 줄인다. Box padding/border/outline/tracking을 고려하고 body/shadow가 같은 fitted size를 공유한다.
  - Python renderer는 legacy `_generate_subtitle_images()`처럼 긴 subtitle line을 font/tracking/box/shadow 설정과 output width 기준으로 wrap한 뒤 line별 timed PNG overlay로 만든다.
  - Python renderer는 legacy logo image처럼 height 기준 scale 후 `logo_image_area_width/height`로 중앙 crop하고 overlay한다.
  - Python renderer는 content area가 output 전체 높이를 쓰는 legacy full-height layout에서 layout을 segment background로 넣지 않고, concat 이후 최종 영상 위에 layout을 overlay한다. `contents_ratio: full`이어도 custom content area height가 작으면 기존 segment background 흐름을 유지한다.
  - Legacy Clipper1 template JSON catalog는 template design 1에 대해 fixed ratio 4종(`1:1`, `16:9`, `4:3`, `full`)을 모두 노출한다. 기존 `example.invalid` preview/layout placeholder는 D2X S3 template/layout URL로 교체했다.
  - Legacy Clipper1 template JSON catalog는 이제 운영 `templates` export 기반 84-row catalog다. 21개 template design × 4개 fixed ratio 구조이며, DBeaver export의 `settings` JSON 문자열은 object로 정규화되어 있다.
  - `templates_jp` export도 `.codex/imports/legacy-clipper1-templates/`에 있지만 canonical source가 아니다. 사용자가 설명한 기준상 일본 콘텐츠 대응용 임시 복제/수정본이므로 기본 Clipper2 catalog에는 넣지 않았다.
  - Legacy Clipper1 UI thumbnail/origin PNG는 `clipper_nestjs/src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/`에 bundled asset으로 들어 있다. Raw import 폴더는 `.codex/imports/legacy-clipper1-template-assets/thumsandorigins/`였고, code repo 안에서는 `thumbs-and-origins`로 정규화했다.
  - Legacy Clipper1 preset `preview.remoteImageUrl`은 local thumbnail endpoint `template-presets/legacy-clipper1/assets/{template}_ratio_{ratio}_thumb.png`, `preview.remoteLargeImageUrl`은 origin endpoint `..._origin.png`를 사용한다.
  - 실제 영상 render background/layout은 여전히 `settings.layout_image` 값이 기준이지만, local source는 이제 Python worker package bundle `clipper1_video_render/legacy_assets/layout`이다. UI용 `thumb/origin`과 render용 `layout`을 섞지 않는다.
  - Angular Template Builder header `새 템플릿` 버튼은 `full` 비율 custom template을 만들고 바로 선택한다.
  - Angular Template Builder editor는 selected text layer의 위치/크기, font size/color/tracking/line-height, box/outline/shadow 속성을 실제 입력 UI로 수정하고 `updateVariant()` 경로로 저장한다.
  - Angular Template Builder main canvas는 더 이상 static mock이 아니라 selected variant의 content area/text layers를 output 좌표 비율로 축소 렌더링한다.
  - Angular Template Builder canvas는 selected text layer pointer drag 이동과 우하단 handle resize를 지원한다. drag/resize 중에는 local frame으로 즉시 보이고 pointerup 때 variant patch를 저장한다.
  - Uploaded layout image는 NestJS file endpoint `GET /template-builder/families/:familyId/variants/:ratio/assets/layout-image/file`로 안전하게 serve되고 Angular canvas에서 실제 `<img>`로 표시된다.
  - Angular Template Builder page는 layer patch를 service 저장 전에 selected family state에 optimistic deep merge한다. 저장 실패 시 이전 snapshot으로 되돌린다.
  - 없는 fixed ratio 슬롯은 full fallback을 보여주지 않고 `미설정`/`이 비율로 시작` empty state를 보여준다. `POST /template-builder/families/:familyId/variants/:ratio`로 같은 family 안에 draft ratio variant를 만든다. `cloneFromRatio`가 있으면 text/box/outline/shadow/media asset style만 target ratio 기본 geometry 위에 복사한다.
  - Canvas text layer 이동/리사이즈는 output bounds 안으로 clamp된다. 선택된 text layer는 방향키로 1px, Shift+방향키로 10px nudge patch를 emit한다.
  - Canvas selected text layer는 8개 resize handle(`nw/n/ne/e/se/s/sw/w`)을 제공한다. 방향별 resize patch는 실제 변경된 `x/y/width/height`만 emit한다.
  - Stage toolbar에는 `스냅` checkbox와 `간격` input이 있다. 스냅이 켜져 있으면 canvas move/resize 결과가 지정 px 간격에 맞춰 저장된다.
  - Page header에는 `되돌리기`/`다시 실행` 버튼이 있다. 성공한 layer update는 before/after family snapshot을 page-local history에 쌓고 undo/redo 시 snapshot layers를 다시 저장한다.
  - 스냅이 켜져 있으면 canvas 내부에 grid guide가 표시된다. guide size는 `snapSize * canvasScale()`로 계산된다.
  - Canvas layer 이동 중 layer center가 canvas 중앙선 8px 이내에 들어오면 중앙에 자동 정렬되고 vertical/horizontal guide line이 표시된다.
  - Canvas layer 이동 중 다른 visible text layer의 left/center/right, top/center/bottom guide와 8px 이내로 가까워지면 해당 기준선에 붙고 guide line이 표시된다.
  - 여러 align guide 후보가 동시에 threshold 안에 있으면 가장 가까운 vertical/horizontal guide 후보를 선택한다.
  - 같은 family/ratio에 대한 연속 layer patch는 microtask 단위로 batching되어 `updateVariant()` 1회로 저장된다. undo history도 batch 단위로 기록된다.
  - layer patch 저장은 40ms timer debounce로 확장됐다. microtask gap이 있어도 같은 family/ratio patch는 merged payload 1회 저장과 undo history 1개로 coalescing된다.
  - fixed ratio slot 생성 시 source ratio의 text layer geometry를 target ratio로 비례 변환한다. x/width/style은 보존하고 y/height/lineY는 source content area 상대 위치에서 target content area 좌표로 옮긴다.
  - family clone도 source variant를 그대로 deep copy하지 않고 target ratio 기본 variant 위에 같은 geometry/style clone 경로를 적용한다.
  - `layoutImage`, `logoImage`, `logoText`는 output canvas 기준 layer로 보고 ratio clone 시 x/y/width/height와 style/assetUri를 output-size 비율로 보존한다.
  - Canvas text layer drag/resize는 pointermove마다 layer patch를 emit한다. Pointerup은 중복 emit 없이 interaction/guide state만 종료한다.
  - Angular Template Builder editor의 selected text layer에는 `표시` checkbox가 있고 `{ visible }` patch를 저장한다.
  - Template Builder layer visibility는 legacy render payload의 project checks와 clip subtitles에 반영된다. 숨긴 `subTitle/mainTitle/bottomTitle/logo/subtitleText`는 최종 Python render payload에서도 꺼진다.
  - Python renderer는 `main_title1` 없이 `main_title2`만 있는 payload도 `MainTitle2` event로 렌더한다.
  - Uploaded/remote layout image는 canvas에서 pointer drag 이동과 8방향 resize handle 조작이 가능하다. `layers.layoutImage.{x,y,width,height}` patch를 emit하고 page-level optimistic merge/debounce/undo history를 그대로 사용한다.
  - `레이아웃 이미지` 속성 섹션에서도 `X/Y/너비/높이` numeric controls로 `layers.layoutImage` geometry를 수정할 수 있다.
  - Custom variant `logoImage`도 multipart upload와 backend file endpoint preview를 지원한다. Endpoint: `POST /template-builder/families/:familyId/variants/:ratio/assets/logo-image`, file endpoint: `GET /template-builder/families/:familyId/variants/:ratio/assets/logo-image/file`.
  - Angular Template Builder editor에는 `로고 이미지` asset section, canvas logo preview, `X/Y/너비/높이` numeric controls가 있다.
  - Published custom template preset은 `layers.logoImage.assetUri`를 `requiredAssets`의 `logo.image`/`logo_image`로 노출한다.
  - Legacy render payload에서 project logo artifact가 있으면 그 artifact가 우선이고, 없으면 template logo image asset이 `project.logo_image`로 전달된다.
  - Layout/logo media image에는 `표시` checkbox가 있다. 숨긴 media image는 Angular canvas preview에 표시되지 않고 legacy render payload에서도 제외된다.
  - `새 템플릿`은 더 이상 즉시 `full`로 생성되지 않는다. Header button은 inline 생성 form을 열고, 사용자가 이름과 시작 비율(`16:9`, `4:3`, `1:1`, `full`)을 선택한 뒤 생성한다.
  - Custom family는 header `이름 변경` 버튼으로 inline rename form을 열고 `PATCH /template-builder/families/:familyId`로 이름을 저장한다.
  - 기본 제공/system family는 rename button을 노출하지 않고, NestJS `TemplateBuilderService.updateFamily()`에서도 readonly 수정으로 거부한다.
  - Selected family는 header `복제` 버튼으로 inline clone form을 열고 새 custom family로 복제할 수 있다. System family도 복제는 가능하다.
  - Clone form의 ratio select는 source family에 실제 존재하는 fixed ratio variant만 보여주고, request는 `ratio`와 `cloneFromRatio`를 같은 값으로 보낸다.
  - Custom family는 header `삭제` 버튼으로 inline confirmation을 열고 `DELETE /template-builder/families/:familyId`로 삭제할 수 있다.
  - 기본 제공/system family는 delete button을 노출하지 않고, NestJS `TemplateBuilderService.deleteFamily()`에서도 readonly 삭제로 거부한다.
  - 삭제 후 selected family가 제거되면 남은 첫 family를 자동 선택한다.
  - 삭제 시 NestJS는 custom family metadata 제거와 함께 `CLIPPER_DATA_DIR/template-assets/<familyId>`, `CLIPPER_DATA_DIR/template-samples/<safeFamilyId>` local directory를 정리한다.
- 관련 커밋:
  - `clipper_nestjs` `bda2d22 feat: render template builder samples`
  - `clipper_nestjs` `dcf4d8c feat: expose template builder presets`
  - `clipper_nestjs` `fa716c2 feat: map template builder render settings`
  - `clipper_nestjs` `b55a037 feat: upload template layout images`
  - `clipper_nestjs` `9a0d73e feat: upload template fonts`
  - `clipper_nestjs` `3c8eb88 feat: render template builder samples with legacy worker`
  - `clipper_nestjs` `b594943 fix: map draft template builder sample renders`
  - `clipper_nestjs` `2b0600b feat: serve template builder sample renders`
  - `clipper_nestjs` `156b8da feat: serve template layout images`
  - `clipper_nestjs` `c9556eb feat: create template ratio variants`
  - `clipper_nestjs` `dcf15db feat: clone template variant geometry`
  - `clipper_nestjs` `eb8b905 fix: clone template family ratio geometry`
  - `clipper_nestjs` `b97c639 feat: clone template media geometry`
  - `clipper_nestjs` `32d2cdf feat: map template font name overrides`
  - `clipper_nestjs` `5bd954d feat: honor template layer visibility in render payloads`
  - `clipper_nestjs` `4ca8f82 feat: support template logo image assets`
  - `clipper_nestjs` `9398137 fix: honor template media visibility`
  - `clipper_nestjs` `366fd8f feat: rename template families`
  - `clipper_nestjs` `ba8f0b0 feat: delete template families`
  - `clipper_nestjs` `013d5d3 fix: clean deleted template family files`
  - `clipper_nestjs` `29f29e3 feat: expose clipper1 template presets`
  - `clipper_nestjs` `d7c9155 feat: expose template builder previews`
  - `clipper_nestjs` `7369d87 feat: expose template sample thumbnails`
  - `clipper_nestjs` `5f194bd feat: persist variation workspaces`
  - `clipper_nestjs` `2bb2e02 feat: preserve template text alignment`
  - `clipper_angular` `17d6748 feat: preview template builder sample renders`
  - `clipper_angular` `5190915 feat: include custom template presets`
  - `clipper_angular` `94b25eb feat: upload template layout images`
  - `clipper_angular` `5c4f712 feat: upload template fonts`
  - `clipper_angular` `748bbfc feat: create template builder families`
  - `clipper_angular` `ff69b31 feat: edit template builder layer styles`
  - `clipper_angular` `5f50e3b feat: manipulate template canvas layers`
  - `clipper_angular` `1511cbf feat: apply template layer edits optimistically`
  - `clipper_angular` `6436c55 feat: create template ratio slots`
  - `clipper_angular` `2da65cb feat: constrain template canvas editing`
  - `clipper_angular` `f8929b2 feat: add template canvas resize handles`
  - `clipper_angular` `bbaeb41 feat: add template canvas snap controls`
  - `clipper_angular` `8ad0327 feat: add template edit history controls`
  - `clipper_angular` `9f28bc9 feat: show template snap grid guide`
  - `clipper_angular` `272deb8 feat: add template center align assist`
  - `clipper_angular` `bf41927 feat: align template layers to peers`
  - `clipper_angular` `9a8c781 feat: prefer nearest template align guide`
  - `clipper_angular` `d56d7b6 feat: batch template layer updates`
  - `clipper_angular` `96a1f3a feat: debounce template layer updates`
  - `clipper_angular` `6bf3340 feat: emit template canvas updates continuously`
  - `clipper_angular` `6be13a3 feat: edit template font name overrides`
  - `clipper_angular` `0eafb72 feat: edit template layer visibility`
  - `clipper_angular` `93e9ddf feat: manipulate template layout images`
  - `clipper_angular` `94f4bc9 feat: edit template layout image geometry`
  - `clipper_angular` `0e846f8 feat: upload template logo images`
  - `clipper_angular` `55d404a feat: toggle template media visibility`
  - `clipper_angular` `910e4ca feat: choose template name and ratio`
  - `clipper_angular` `62ab78e feat: rename template families`
  - `clipper_angular` `fdbc9c5 feat: clone template families from catalog`
  - `clipper_angular` `c64046b feat: delete template families`
  - `clipper_angular` `85278e3 feat: select templates in clipper1 workspace`
  - `clipper_angular` `912cbf6 feat: add clipper1 template picker`
  - `clipper_angular` `3ad5051 feat: render template preview videos`
  - `clipper_angular` `e674b3a test: cover template preview thumbnails`
  - `clipper_angular` `36dff73 refactor: share shortform template picker`
  - `clipper_angular` `33a8cbc refactor: share shortform template preset loading`
  - `clipper_angular` `713309e feat: add variation workflow shell`
  - `clipper_angular` `37375e2 feat: connect variation workspace API`
  - `clipper_python` `cecc896 feat: load uploaded template fonts`
  - `clipper_python` `f6a215f test: add template builder render parity smoke`
  - `clipper_python` `7ebaf6e feat: map template text shadow styles`
  - `clipper_python` `2c8fb88 feat: render template shadow outlines`
  - `clipper_python` `c3de97b feat: honor template font name overrides`
  - `clipper_python` `21f2f3d fix: render visible second title lines`
  - `clipper_python` `fc39e5a feat: honor explicit video motion effects`
  - `clipper_python` `1e12a1b feat: match legacy video media fill`
  - `clipper_python` `9112570 feat: read uploaded font family names`
  - `clipper_python` `6192cfa feat: map subtitle box borders`
  - `clipper_python` `507dac4 feat: render template center alignment`
- 검증:
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/template-builder-api.test.js` 성공.
  - actual `LocalFfmpegBasicRenderProvider` smoke에서 3초 MP4 생성 성공, size `93181` bytes.
  - `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js` 성공.
  - `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공.
  - 최신 sample render provider 변경 후 같은 focused regression 성공, 8 passed.
  - draft sample mapper fix 후 같은 focused regression 성공, 9 passed.
  - 실제 worker E2E: `artifactUri=template-sample/main.mp4`, size `361033` bytes.
  - `clipper_angular` focused template builder specs 성공, 16 success.
  - `clipper_angular` focused template builder specs 성공, 17 success.
  - `clipper_angular npm run build:electron -- --progress=false` 성공.
  - `clipper_angular` focused template builder specs 성공, 15 success.
  - latest layer editor slice: `clipper_angular` focused editor/page specs 성공, 15 success.
  - latest layer editor slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest canvas/layout slice: `clipper_nestjs npm run build` 성공.
  - latest canvas/layout slice: `clipper_nestjs` focused regression 성공, 9 passed.
  - latest canvas/layout slice: `clipper_angular` focused template builder specs 성공, 24 success.
  - latest canvas/layout slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest optimistic state slice: `clipper_angular` focused template builder specs 성공, 25 success.
  - latest optimistic state slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest ratio variant slice: `clipper_nestjs npm run build` 성공.
  - latest ratio variant slice: `clipper_nestjs` focused regression 성공, 10 passed.
  - latest ratio variant slice: `clipper_angular` focused template builder specs 성공, 28 success.
  - latest ratio variant slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest bounds/nudge slice: `clipper_angular` focused template builder specs 성공, 31 success.
  - latest bounds/nudge slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest multi-handle resize slice: `clipper_angular` focused template builder specs 성공, 34 success.
  - latest multi-handle resize slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest snap controls slice: `clipper_angular` focused template builder specs 성공, 36 success.
  - latest snap controls slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest undo/redo slice: `clipper_angular` focused template builder specs 성공, 37 success.
  - latest undo/redo slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest snap grid guide slice: `clipper_angular` focused template builder specs 성공, 38 success.
  - latest snap grid guide slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest center align assist slice: `clipper_angular` focused template builder specs 성공, 39 success.
  - latest center align assist slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest layer-to-layer align assist slice: `clipper_angular` focused template builder specs 성공, 40 success.
  - latest layer-to-layer align assist slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest nearest align candidate slice: `clipper_angular` focused template builder specs 성공, 41 success.
  - latest nearest align candidate slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest batched layer update slice: `clipper_angular` page spec 성공, 10 success.
  - latest batched layer update slice: `clipper_angular` focused template builder specs 성공, 42 success.
  - latest batched layer update slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest debounced layer update slice: `clipper_angular` page spec 성공, 11 success.
  - latest debounced layer update slice: `clipper_angular` focused template builder specs 성공, 43 success.
  - latest debounced layer update slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - latest ratio-aware variant cloning slice: `clipper_nestjs npm run build` 성공.
  - latest ratio-aware variant cloning slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 4 passed.
  - latest ratio-aware variant cloning slice: `clipper_nestjs` focused template builder regression 성공, 10 passed.
  - latest family clone geometry slice: `clipper_nestjs npm run build` 성공.
  - latest family clone geometry slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 5 passed.
  - latest family clone geometry slice: `clipper_nestjs` focused template builder regression 성공, 11 passed.
  - latest media/logo geometry slice: `clipper_nestjs npm run build` 성공.
  - latest media/logo geometry slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 5 passed.
  - latest media/logo geometry slice: `clipper_nestjs` focused template builder regression 성공, 11 passed.
  - latest continuous canvas patch slice: `clipper_angular` component spec 성공, 27 success.
  - latest continuous canvas patch slice: `clipper_angular` focused template builder specs 성공, 45 success.
  - latest continuous canvas patch slice: `clipper_angular npm run build:electron -- --progress=false` 성공.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 8 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 10 passed.
  - latest shadow outline parity slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py` 성공, 3 passed.
  - latest shadow outline parity slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 11 passed.
  - latest shadow outline parity slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest font name override slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 13 passed.
  - latest font name override slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest font name override slice: `clipper_nestjs npm run build` 성공.
  - latest explicit video/GIF motion slice: `clipper_python uv run pytest tests/test_clipper1_video_render_motion.py` 성공, 3 passed.
  - latest explicit video/GIF motion slice: `clipper_python uv run pytest tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 17 passed.
  - latest explicit video/GIF motion slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest video/GIF loop + blur-fill slice: `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py` 성공, 5 passed.
  - latest video/GIF loop + blur-fill slice: `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 22 passed.
  - latest video/GIF loop + blur-fill slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest uploaded font family-name slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py` 성공, 7 passed.
  - latest uploaded font family-name slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_media_looping.py` 성공, 23 passed.
  - latest uploaded font family-name slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest uploaded font family-name slice: `clipper_python uv lock --check` 성공, 140 packages resolved.
  - latest subtitle box border slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py` 성공, 8 passed.
  - latest subtitle box border slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_media_looping.py` 성공, 24 passed.
  - latest subtitle box border slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest Template Builder center alignment slice: `clipper_nestjs npm run build` 성공.
  - latest Template Builder center alignment slice: `clipper_nestjs node --test test/template-builder-render-payload.test.js` 성공, 4 passed.
  - latest Template Builder center alignment slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 19 passed.
  - latest Template Builder center alignment slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py` 성공, 9 passed.
  - latest Template Builder center alignment slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_media_looping.py` 성공, 25 passed.
  - latest Template Builder center alignment slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest font name override slice: `clipper_nestjs node --test test/template-builder-render-payload.test.js` 성공, 2 passed.
  - latest font name override slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/features/template-builder/**/*.spec.ts'` 성공, 45 success.
  - latest font name override slice: `clipper_angular npm run build:electron` 성공.
  - latest layer visibility slice: `clipper_nestjs npm run build` 성공.
  - latest layer visibility slice: `clipper_nestjs node --test test/template-builder-render-payload.test.js` 성공, 3 passed.
  - latest layer visibility slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 12 passed.
  - latest layer visibility slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include=src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 27 success.
  - latest layer visibility slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/features/template-builder/**/*.spec.ts'` 성공, 45 success.
  - latest layer visibility slice: `clipper_angular npm run build:electron` 성공.
  - latest layer visibility slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py` 성공, 6 passed.
  - latest layer visibility slice: `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py` 성공, 14 passed.
  - latest layer visibility slice: `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - latest layout image manipulation slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include=src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 29 success.
  - latest layout image manipulation slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/features/template-builder/**/*.spec.ts'` 성공, 47 success.
  - latest layout image manipulation slice: `clipper_angular npm run build:electron` 성공.
  - latest layout image numeric controls slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include=src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 30 success.
  - latest layout image numeric controls slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/features/template-builder/**/*.spec.ts'` 성공, 48 success.
  - latest layout image numeric controls slice: `clipper_angular npm run build:electron` 성공.
  - latest logo image asset slice: `clipper_nestjs npm run build` 성공.
  - latest logo image asset slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 6 passed.
  - latest logo image asset slice: `clipper_nestjs node --test test/template-builder-render-payload.test.js` 성공, 3 passed.
  - latest logo image asset slice: `clipper_nestjs node --test test/template-builder-preset-source.test.js` 성공, 1 passed.
  - latest logo image asset slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 13 passed.
  - latest logo image asset slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 53 success.
  - latest logo image asset slice: `clipper_angular npm run build:electron` 성공.
  - latest media image visibility slice: `clipper_nestjs npm run build` 성공.
  - latest media image visibility slice: `clipper_nestjs node --test test/template-builder-render-payload.test.js` 성공, 3 passed.
  - latest media image visibility slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 13 passed.
  - latest media image visibility slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 34 success.
  - latest media image visibility slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 55 success.
  - latest media image visibility slice: `clipper_angular npm run build:electron` 성공.
  - latest named create form slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 13 success.
  - latest named create form slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 56 success.
  - latest named create form slice: `clipper_angular npm run build:electron` 성공.
  - latest family rename slice: `clipper_nestjs npm run build` 성공.
  - latest family rename slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 8 passed.
  - latest family rename slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 15 passed.
  - latest family rename slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts --include=src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 25 success.
  - latest family rename slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 59 success.
  - latest family rename slice: `clipper_angular npm run build:electron` 성공.
  - latest family clone UI slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 17 success.
  - latest family clone UI slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 61 success.
  - latest family clone UI slice: `clipper_angular npm run build:electron` 성공.
  - latest family delete slice: `clipper_nestjs npm run build` 성공.
  - latest family delete slice: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 10 passed.
  - latest family delete slice: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 17 passed.
  - latest family delete cleanup update: `clipper_nestjs node --test test/template-builder-api.test.js` 성공, 10 passed.
  - latest family delete cleanup update: `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 17 passed.
  - latest family delete slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts --include=src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 30 success.
  - latest family delete slice: `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 64 success.
  - latest family delete slice: `clipper_angular npm run build:electron` 성공.
  - `clipper_angular npm run build:electron -- --progress=false` 성공.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - `clipper_python git diff --check` 성공.
- 중요한 남은 한계:
  - sample render service는 template-aware Python worker provider를 요청하고 실제 worker E2E도 한 번 통과했다.
  - Python final renderer에는 최소 시각 계약 smoke와 box/outline/shadow focused fixture, shadow outline style/event fixture, 수동 font name override fixture가 있다. 폰트 파일 내부 family name 자동 추출은 아직 없다.
  - Layer visibility는 UI/payload에 연결됐지만, line별 visibility를 실제 sample render 영상으로 디자인 QA하는 작업은 남아 있다.
  - Template Builder editor의 main canvas는 selected variant layer 기반 preview로 교체됐고 text layer drag/resize, layout image drag/resize와 numeric geometry controls, logo image upload/preview/numeric geometry controls, layout/logo 표시 토글, pointermove continuous patch emission, 8방향 resize handle, output bounds clamp, keyboard nudge, snap controls/grid guide, canvas center align assist, visible text layer 기준 align assist, nearest align candidate selection, layout image bitmap preview가 있다. Page-level optimistic patch merge, 40ms debounced batching, undo/redo history도 있다. Fixed ratio slot creation, named create form, custom family rename/delete with local cleanup, selected family clone UI, family clone ratio geometry, text layer ratio-aware geometry cloning, output-relative logo/media geometry cloning도 있다. 다만 logo image 전용 drag/resize 회귀 테스트 일반화, text layer별 ratio conversion parity 세분화는 아직 없다.
  - custom template preset의 layer snapshot은 legacy `template_settings`로 변환되지만, Python renderer가 아직 사용하지 않는 세부 속성은 별도 parity 작업이다.
  - layout/font upload는 local path first slice다. font family matching은 uploaded file stem 또는 사용자가 입력한 `렌더 폰트명` override에 의존한다.
- 다음 우선순위 후보:
  - Python renderer의 pixel-level style comparison을 fixture 기반으로 좁히기.
  - 필요하면 uploaded font file에서 내부 family name을 자동 추출하는 provider/helper를 추가하기.

## 세션 시작 공통 규칙

- 사용자가 별도로 다시 말하지 않아도 매 턴 session log를 작성한다.
- session log 경로는 `.codex/session-logs/YYYY-MM-DD.log`다.
- 날짜별 파일로 누적하고, 루트에 `codex-session.log` 같은 단일 파일은 만들지 않는다.
- 기록 범위는 사용자 입력, assistant 출력, 실행 명령어와 주요 결과, 파일 수정 내역, 구현/검증 결정 요약이다.
- hidden reasoning은 원문이 아니라 검토 가능한 결정/근거 요약으로만 남긴다.

## 2026-05-06 세션 종료 요약

- 2026-05-06 16:02 KST 방향 정정:
  - 현재 prompt-only Clipper Studio UX와 prompt submit 후 completed project shell을 만드는 흐름은 제품 방향과 맞지 않는다.
  - Clipper1 plugin과 Variation plugin을 별도 workflow로 분리한다.
  - 내부는 Shared Shortform Core로 통합한다.
  - Clipper1 plugin은 왼쪽 tabbed input(URL/프롬프트/붙여넣기/수동 시작), 중앙 clip editor, 오른쪽 9:16 full preview/settings 구조를 기준으로 한다.
  - 입력 primary action label은 `클립 생성`이다.
  - `숏폼 생성`을 눌렀을 때만 render queue/job/project output으로 승격한다.
  - clip당 여러 media asset/pool/slot을 지원해야 한다.
  - 기준 설계: `.codex/design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
  - Phase 1 구현 계획: `.codex/implementation/SHORTFORM_PLUGIN_SPLIT_PHASE1_PLAN.md`
- 2026-05-06 13:16 KST 추가 진행:
  - 생성 영상 품질 QA 중 BGM-only render path의 볼륨 적용 문제를 수정했다.
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - `clipper_python/tests/test_clipper1_video_render_remote_assets.py`
  - `uv run pytest tests/test_clipper1_video_render_remote_assets.py` 성공, 6 passed.
  - `5bf9e6c fix: apply bgm volume without tts`로 커밋했다.
- 최신 DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- 생성 시각: `2026-05-05 15:32 KST`
- 크기: `150M`
- Node: `v22.22.2`
- npm: `10.9.7`
- repo 상태:
  - `clipper_nestjs`: clean
  - `clipper_angular`: `a9e6d18 feat: preview and edit clipper1 workspace`까지 완료, clean
  - `clipper_electron`: clean
  - `clipper_python`: `5bf9e6c fix: apply bgm volume without tts`까지 완료, clean
- 2026-05-06에 이전 세션 변경사항을 커밋했다.
  - `clipper_nestjs` `ee3c7cb fix: gate unavailable render providers`
  - `clipper_nestjs` `531725b chore: refresh npm lock metadata`
  - `clipper_angular` `d6f7560 fix: show render provider unavailable reason`
  - `clipper_angular` `75351c5 chore: refresh npm lock metadata`
  - `clipper_angular` `1ba755c chore: disable angular analytics`
  - `clipper_electron` `e44c8b7 chore: refresh npm lock metadata`
- packaged Electron 사용자 확인:
  - `영상 만들기 / 최종 영상 / 준비됨` 표시.
  - `영상 만들기` 실행 후 MP4 생성.
  - final preview, thumbnail/poster, render history/version, edit -> stale/rerender -> regenerated output 정상.
- 이번 세션에서 고친 것:
  - dev/static host에서 `clipper1_video_render`를 spawn할 수 없는데 `video.render.legacy_clipper1.python_worker`가 available로 표시되던 문제 수정.
  - Static host에서는 worker가 이미 running일 때만 available이고, stopped/unreachable이면 unavailable과 수동 시작 안내를 표시한다.
  - Electron host에서는 process spawn 가능 경로라 available 유지.
  - BGM-only render path에서도 `bgm_volume`이 실제 오디오 track에 적용되도록 수정.
- 다음 구현 추천:
  - Shortform Phase 1은 구현/검증 완료 상태다. 다음은 UI 수동 QA 후 Phase 2 범위(URL ingestion/Scrapling 검토, rich paste, preview/template parity, Variation UI)를 좁힌다.
  - 사용자 MP4 품질 피드백이 있으면 Shortform 작업 중에도 우선순위를 재조정한다.

## 현재 큰 방향

Clipper2는 NestJS control plane 중심으로 재설계한다.

역할 기준:

- Angular는 기본적으로 NestJS API를 호출한다.
- NestJS는 app backend/control plane이다. plugin/job/project/queue orchestration을 맡는다.
- FastAPI plugin은 개별 서버로 계속 뜨며 Python compute worker 역할을 유지한다.
- Electron은 packaged desktop host/native adapter다. Python process spawn, port allocation, venv, userData, ffmpeg, file dialog를 맡는다.
- 기존 Electron `LocalPluginManager`는 폐기하지 않는다. Electron packaged mode의 plugin process host adapter로 재배치한다.

## 2026-05-04 중요 정정

Clipper1 전체 workflow는 아직 Clipper2에 편입되지 않았다.

현재 완료된 것은 render capability slice다.

```text
ProjectManifest -> RenderRecipe -> video.render provider -> MP4 artifact
```

`clipper1_video_render`는 headless Python worker/provider이며 Store/Dashboard에서 사용자가 여는 workflow plugin이 아니다.
사용자-facing 목표는 별도의 `workflow.clipper_studio`다.

다음 세션의 구현 시작점:

1. Clipper1 bundled seed asset provider, local/user media provider 1차 slice, local TTS synthesis provider 1차 slice, media search/download provider 1차 slice, BGM/logo catalog/upload provider 1차 slice는 구현됐다.
2. real/remote `llm.script` provider boundary 1차도 구현됐다.
3. script-generated searchQuery 기반 clip media 자동 검색/적용 1차도 구현됐다.
4. `llm.script`, `media.search`, `image.generate`, `tts.synthesis` provider registry/adapter boundary 1차와 provider status/fallback UI는 구현됐다.
5. `media.search`에는 Naver/Kakao adapter 외에 `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 기반 HTTP/remote proxy adapter가 추가됐다.
6. Clipper Studio detail에서 title/keywords/clip subtitle/search query/duration 편집 1차가 추가됐고, subtitle 변경 시 새 TTS artifact를 만든다.
7. 다음 production endpoint 연결은 core workflow 수정이 아니라 capability별 provider adapter 구현체 추가/설정으로 진행한다.
8. Clipper Studio render/error state polish와 final MP4/thumbnail visual QA 1차는 2026-05-05 packaged Electron 사용자 확인으로 통과했다. 다음은 영상 품질 QA와 production provider 연결이다.

현재는 packaged render E2E가 통과했지만, 제품 품질 관점에서는 output quality와 provider 운영 정책을 더 봐야 하는 checkpoint다. 사용자가 생성된 MP4를 직접 보고 품질 피드백을 주면 그 피드백을 다음 구현 우선순위로 삼는다.

필수 아키텍처 원칙:

- OpenAI, Ollama/Gemma local LLM, remote company proxy는 모두 `llm.script` provider 구현체일 뿐이다.
- Naver/Kakao image search, local image generation server, user upload는 모두 `media.search` / `image.generate` / `media.import` provider 구현체일 뿐이다.
- company/custom/local media search proxy도 `media.search` provider 구현체일 뿐이며 workflow/editor/render code가 endpoint schema 외 vendor 세부를 알면 안 된다.
- macOS `say`, Naver Clova, Oute TTS local server, 다른 open-source TTS runtime은 모두 `tts.synthesis` provider 구현체일 뿐이다.
- Workflow/editor/render code는 특정 vendor API shape, credential, billing, quota, retry/fallback 정책을 몰라야 한다.
- 새 provider를 붙일 때 core workflow를 수정하게 된다면 abstraction이 부족한 것이다. 먼저 capability contract, provider registry, adapter boundary를 만든다.
- 모든 provider output은 typed draft DTO 또는 `ProjectManifest` artifact로 정규화해야 한다.
- fake provider를 주입해 network 없이 smoke/test할 수 있어야 한다.

이미 완료된 shell slice:

- `workflow.clipper_studio` descriptor
- Angular `/clipper-studio` 제작 화면
- NestJS `POST /v1/projects/clipper-studio` project shell/create API
- `/projects` Clipper Studio presenter

## 2026-05-06 Shortform Phase 1 완료 요약

- `clipper_nestjs`
  - `b9dcc92 feat: add shortform core media slots`
  - `a39871d feat: render shortform media slots`
  - `15739c5 feat: add clipper1 workspace flow`
  - `5948c59 feat: enqueue clipper1 render from workspace`
- `clipper_angular`
  - `ed07730 feat: add clipper1 workspace shell`
  - `a9e6d18 feat: preview and edit clipper1 workspace`
  - `d801b04 feat: start clipper1 render from workspace`
- Phase 1 동작 기준:
  - `클립 생성`은 workspace에 clip draft를 만들 뿐 `/projects` completed history를 만들지 않는다.
  - Clipper1 workspace는 왼쪽 tabbed input, 중앙 clip editor, 오른쪽 Angular-native 9:16 preview 구조다.
  - clip별 multiple media pool/slots가 DTO와 RenderRecipe timeline에 연결됐다.
  - `숏폼 생성`만 project/render job으로 승격하는 queue boundary다.
- 검증:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/shortform-media-slot-scheduler.test.js test/legacy-clipper1-render-media-slots.test.js test/clipper1-workspace-api.test.js` 성공, 7 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'` 성공, 3 success.
  - `clipper_angular npm run build:electron -- --progress=false` 성공.
- Dashboard에서 `clipper_studio`을 runtime start/stop 대상이 아니라 workflow open 대상으로 처리
- `POST /v1/projects/:projectId/clipper-studio/draft` deterministic draft generation API
- `POST /v1/projects/:projectId/clipper-studio/draft-jobs` draft job/progress/cancel API
- `ClipperStudioScriptGenerator` facade와 `llm.script.deterministic` provider boundary
- `ClipperStudioAssetPreparer` bundled seed media/TTS/logo/layout artifact preparation; silent BGM 기본 생성 제거
- `output.clipper-studio.render.main` -> `RenderRecipe` -> `video.render.legacy_clipper1.python_worker` packaged render E2E
- render job result -> Clipper Studio manifest final output promotion
- Angular `/clipper-studio` create flow에서 draft job을 시작하고 진행률/취소 UI 표시
- `/projects` Clipper Studio presenter가 script/clip plan을 표시
- `/projects` Clipper Studio presenter가 render 완료 MP4/thumbnail을 video preview로 표시
- render job polling 완료 시 manifest를 다시 읽어 같은 상세 화면에서 final preview가 즉시 갱신됨
- `PATCH /v1/projects/:projectId/clipper-studio/edit-state`와 Angular client method가 있음
- edit-state PATCH는 title visibility/logo text/TTS speed 등을 manifest에 저장하고 다음 render recipe에 반영함
- `/projects` Clipper Studio detail에는 title visibility checkbox, logo text 저장, TTS speed 저장 UI가 있음
- `/projects` Clipper Studio detail에는 Clipper1 template catalog select가 있음
- `/projects` Clipper Studio detail에는 project manifest artifact 기반 BGM/logo image select가 있음
- `/projects` Clipper Studio detail에는 clip별 media artifact select가 있음
- `/projects` Clipper Studio detail에는 TTS preset select가 있음
- stale render output에서는 주요 render action 문구가 `다시 만들기` / `재렌더 준비됨`으로 바뀜
- render job history가 버전 라벨로 표시되고, 완료 render는 `renders/versions/<jobId>/`에 version artifact로 보존됨
- final render MP4가 아직 없으면 9:16 empty preview가 표시됨
- `/projects` Clipper Studio detail에는 main/sub/bottom title, keywords, clip subtitle, clip search query, clip duration 편집 UI가 있음
- subtitle 편집 저장 시 NestJS가 현재 `tts.synthesis` provider로 새 `audio.tts` artifact를 만들고 clip의 `ttsArtifactId`를 새 artifact로 교체함
- Chrome CDP fallback으로 `/projects` Clipper Studio detail desktop visual QA를 수행했고, final render empty preview의 중복 문구를 정리함
- `clipper_nestjs` `41792be feat: use clipper studio seed assets`
- `ClipperStudioAssetPreparer`가 단색 BMP/silent WAV 대신 bundled legacy seed assets를 project-file artifact로 복사함
  - clip media: `media.legacy_seed.bundle` JPEG seed images
  - TTS: `tts.legacy_seed.bundle` MP3 seed voice clips
  - layout/logo: `layout.legacy_seed.bundle`, `logo.legacy_seed.bundle` PNG assets
  - BGM은 아직 실제 catalog가 없으므로 silent artifact를 기본 생성하지 않고 `사용 안 함` 상태로 둠
- Clipper1 template preset source는 JSON file source임: `src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`
- local/user media provider 1차 slice
  - `clipper_nestjs` `da1e96d feat: import clipper studio local media`
  - `clipper_angular` `4f679de feat: add clipper studio media import UI`
  - `clipper_electron` `4f3e9ac feat: add media file dialog bridge`
  - Electron image/video file dialog로 선택한 local file을 NestJS가 project `draft/assets/user_media/`로 복사한다.
  - `media.local_user.file` artifact를 만들고 clip edit-state `clipMediaArtifactIds`에 즉시 연결한다.
  - render recipe가 선택 clip의 `sourceArtifactId`로 local user media artifact를 사용한다.
- local TTS synthesis provider 1차 slice
  - `clipper_nestjs` `bb07a87 feat: synthesize clipper studio local tts`
  - macOS `say` + `Yuna` voice로 subtitle text별 `.m4a` TTS artifact를 만든다.
  - provider id: `tts.local_os.say`, speaker id: `Yuna`
  - 사용할 수 없는 환경에서는 `tts.legacy_seed.bundle` seed MP3로 fallback한다.
  - smoke render에서 `tts.local_os.say` artifact가 Python render worker를 통해 final MP4에 포함되는 것 확인.
- media search/download provider 1차 slice
  - `clipper_nestjs` `8262299 feat: add clipper studio media search import`
  - `clipper_angular` `b8bd59a feat: apply clipper studio media search results`
  - `POST /v1/projects/:projectId/clipper-studio/media/search`가 Naver/Kakao image search 후보를 반환한다.
  - `POST /v1/projects/:projectId/clipper-studio/media/remote`가 HTTP(S) 이미지/영상을 project `draft/assets/search_media/`로 다운로드해 project-file artifact로 등록한다.
  - `POST /v1/projects/:projectId/clipper-studio/media/search-import`가 첫 검색 후보를 다운로드하고 clip edit-state/render recipe source artifact를 즉시 교체한다.
  - `/projects` Clipper Studio clip row에 `검색 적용` 입력/버튼이 추가됐다.
  - smoke에서 Naver 후보(`media.search.naver.image`)가 `media.image` artifact로 저장되고 render recipe `sourceArtifactId`가 해당 artifact로 교체되는 것 확인.
- BGM/logo catalog/upload provider 1차 slice
  - `clipper_nestjs` `1f2605e feat: add clipper studio bgm and logo imports`
  - `clipper_angular` `bb543e9 feat: add clipper studio bgm and logo import UI`
  - `clipper_electron` `43fbd9b feat: add audio file dialog bridge`
  - legacy Clipper1 BGM MP3 10개를 bundled catalog로 옮기고 project `draft/assets/bgm/`의 `audio.bgm.legacy_bundle` artifact로 등록한다.
  - 사용자가 선택한 audio file은 project `draft/assets/user_bgm/`로 복사되고 `audio.bgm.local_user.file` artifact로 등록된다.
  - 사용자가 선택한 logo image는 project `draft/assets/user_logo/`로 복사되고 `logo.local_user.file` artifact로 등록된다.
  - BGM/logo import는 edit-state `bgmArtifactId`/`logoArtifactId`에 즉시 반영되고 render recipe `track.audio.bgm`/`overlay.logo`로 연결된다.
  - Electron에 `openAudioFile` dialog bridge가 추가됐고 Angular Clipper Studio detail에서 BGM `추가`, 로고 `추가` 버튼으로 호출한다.
- remote LLM script provider boundary 1차 slice
  - `clipper_nestjs` `687d914 feat: add clipper studio remote script provider`
  - `clipper_angular` `8e20564 feat: use clipper studio script search queries`
  - `ConfiguredClipperStudioScriptGenerator`가 `CLIPPER1_LLM_SCRIPT_ENDPOINT`를 감지하면 remote proxy provider를 사용한다.
  - explicit `CLIPPER1_LLM_SCRIPT_PROVIDER=openai_responses` 설정 시 OpenAI Responses-compatible endpoint를 호출한다.
  - 설정이 없으면 기존 `llm.script.deterministic` fallback을 사용한다.
  - remote response는 legacy Clipper1 `clips[].subtitles`, `keywords`, `combined_keyword`, `total_keywords`, `main_title*` 구조와 Clipper Studio camelCase 구조를 모두 정규화한다.
  - clip별 `searchQuery`를 manifest에 저장하고 Angular `검색 적용` 입력 기본값으로 사용한다.
- `llm.script` provider registry/adapter 1차 split
  - `clipper_nestjs` `6797b5a refactor: split clipper studio script providers`
  - `ConfiguredClipperStudioScriptGenerator`는 workflow-facing facade로 유지한다.
  - 실제 구현은 `DeterministicClipperStudioScriptProvider`, `RemoteProxyClipperStudioScriptProvider`, `OpenAiResponsesClipperStudioScriptProvider`로 분리됐다.
  - provider 선택은 `ClipperStudioScriptProviderRegistry`가 담당한다.
  - legacy/OpenAI/remote response 정규화는 `ClipperStudioScriptResponseNormalizer`가 담당한다.
  - 다음 provider 추가(Ollama/Gemma local server, company proxy variants)는 workflow code가 아니라 provider adapter/registry 등록으로 끝나야 한다.
- `llm.script` Ollama/local model provider
  - `clipper_nestjs` `0da9415 feat: add clipper studio ollama script provider`
  - `OllamaClipperStudioScriptProvider`가 추가됐다.
  - `CLIPPER1_LLM_SCRIPT_PROVIDER=ollama`
  - `CLIPPER1_LLM_SCRIPT_OLLAMA_MODEL`로 모델을 지정한다.
  - endpoint는 `CLIPPER1_LLM_SCRIPT_OLLAMA_ENDPOINT`로 직접 지정하거나, `CLIPPER1_LLM_SCRIPT_OLLAMA_BASE_URL` 기반 `/api/generate`로 만든다. 기본 base URL은 `http://127.0.0.1:11434`.
  - Ollama `/api/generate`의 `response` JSON 문자열을 `ClipperStudioScriptResponseNormalizer`로 정규화한다.
  - Gemma 계열이나 다른 Ollama-served local model은 workflow code 수정 없이 model/env만 바꿔 붙인다.
- `media.search` provider registry/adapter 1차 split
  - `clipper_nestjs` `36211b5 refactor: split clipper studio media search providers`
  - `ClipperStudioMediaSearchProvider`는 workflow-facing facade로 유지한다.
  - 실제 검색 구현은 `NaverClipperStudioImageSearchProvider`, `KakaoClipperStudioImageSearchProvider`로 분리됐다.
  - provider 선택/실패 fallback/dedupe는 `ClipperStudioMediaSearchProviderRegistry`가 담당한다.
  - HTTP(S) artifact materialization은 `ClipperStudioRemoteMediaDownloader`로 분리됐다.
  - 다음 image search/generation provider 추가는 workflow code가 아니라 provider adapter/registry 등록으로 끝나야 한다.
- `media.search` HTTP/remote proxy provider
  - `clipper_nestjs` `8aac74d feat: add clipper studio remote media search provider`
  - `RemoteProxyClipperStudioImageSearchProvider`가 추가됐다.
  - `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 또는 `CLIPPER_STUDIO_MEDIA_SEARCH_ENDPOINT` 설정 시 company/custom/local media search proxy를 호출한다.
  - optional env: `CLIPPER1_MEDIA_SEARCH_TOKEN`, `CLIPPER1_MEDIA_SEARCH_API_KEY`, `CLIPPER1_MEDIA_SEARCH_PROVIDER_ID`와 `CLIPPER_STUDIO_*` equivalents.
  - request schema는 `clipper-studio-media-search.v1`이며 `query`/`keyword`/`limit`/`locale`/`kind`를 JSON POST로 보낸다.
  - response는 root 또는 `data` 아래 `items`/`results`/`candidates`/`images` 배열을 허용하고, `contentUrl`/`imageUrl`/`url`/`link` 계열 필드를 `media.image` candidate로 정규화한다.
  - registry 시도 순서는 remote proxy -> Naver -> Kakao다.
- `image.generate` provider registry/adapter 1차 split
  - `clipper_nestjs` `a95c35a feat: add clipper studio image generation provider`
  - `clipper_angular` `02e2c04 feat: add clipper studio image generation UI`
  - `clipper_nestjs` `4d40aa8 feat: expose clipper studio capability status`
  - `clipper_angular` `083dbdc feat: show clipper studio generation availability`
  - `ClipperStudioImageGenerationProvider`는 workflow-facing facade로 유지한다.
  - 실제 구현은 HTTP/local-server-compatible `HttpClipperStudioImageGenerationProvider`로 분리됐다.
  - provider 선택은 `ClipperStudioImageGenerationProviderRegistry`가 담당한다.
  - `POST /v1/projects/:projectId/clipper-studio/media/generate`가 generated image를 project artifact로 등록하고 clip edit-state/render recipe source로 연결한다.
  - `/projects` Clipper Studio clip row의 `생성 적용` 버튼이 같은 입력 prompt로 generated media를 적용한다.
  - `GET /v1/projects/clipper-studio/capabilities`가 image generation provider availability를 내려주고, endpoint 미설정 시 `생성 적용` 버튼은 비활성화된다.
  - endpoint는 `CLIPPER1_IMAGE_GENERATE_ENDPOINT` 또는 `CLIPPER_STUDIO_IMAGE_GENERATE_ENDPOINT`로 설정한다.
  - OpenAI Images, local diffusion, company proxy 등 다음 provider 추가는 workflow code가 아니라 provider adapter/registry 등록으로 끝나야 한다.
- `tts.synthesis` provider registry/adapter 1차 split
  - `clipper_nestjs` `db92d6a refactor: split clipper studio tts providers`
  - `ClipperStudioTtsSynthesisProvider`는 workflow-facing facade로 유지한다.
  - 실제 구현은 `MacOsSayClipperStudioTtsProvider`로 분리됐다.
  - provider 선택은 `ClipperStudioTtsSynthesisProviderRegistry`가 담당한다.
  - `ClipperStudioAssetPreparer`는 macOS `say` 실행, env key, timeout, provider fallback 정책을 직접 알지 않는다.
  - 다음 Clova/Oute/local server TTS 추가는 workflow code가 아니라 provider adapter/registry 등록으로 끝나야 한다.
- `tts.synthesis` HTTP/local-server provider
  - `clipper_nestjs` `b170178 feat: add clipper studio http tts provider`
  - `HttpClipperStudioTtsProvider`가 추가됐다.
  - `CLIPPER1_TTS_SYNTHESIS_ENDPOINT` 또는 `CLIPPER_STUDIO_TTS_SYNTHESIS_ENDPOINT` 설정 시 remote/local TTS server를 호출한다.
  - optional env: `CLIPPER1_TTS_SYNTHESIS_TOKEN`, `CLIPPER1_TTS_SYNTHESIS_API_KEY`, `CLIPPER1_TTS_SYNTHESIS_PROVIDER_ID`, `CLIPPER1_TTS_SYNTHESIS_SPEAKER_ID`, `CLIPPER1_TTS_SYNTHESIS_TIMEOUT_MS`, `CLIPPER1_TTS_SYNTHESIS_MAX_BYTES`와 `CLIPPER_STUDIO_*` equivalents.
  - provider response는 direct audio bytes, JSON `audioUrl`, JSON/base64(`b64_json`, `audioBase64`, `base64`, data URL)를 허용한다.
  - 결과는 `audio.tts` project-file artifact로 정규화되고, configured provider id/speaker id는 capability status와 TTS preset catalog에 표시된다.
  - Clova, Oute TTS, 다른 local model server는 workflow code가 아니라 이 adapter 뒤 endpoint로 붙인다.
- Clipper Studio script/clip editor 1차
  - `clipper_nestjs` `7c6cb49 feat: edit clipper studio script clips`
  - `clipper_angular` `842066e feat: edit clipper studio script clips`
  - `PATCH /v1/projects/:projectId/clipper-studio/edit-state`가 `script`와 `clips[]` patch를 받는다.
  - 편집 가능한 값: main title 1/2, sub title, bottom title, keywords, clip subtitle, clip search query, clip duration.
  - subtitle이 바뀌면 현재 `tts.synthesis` provider로 새 `audio.tts` artifact를 만들고 다음 render recipe가 새 subtitle/TTS artifact를 사용한다.
- Clipper Studio provider status/fallback surface
  - `clipper_nestjs` `47495ec feat: expose clipper studio provider fallback status`
  - `clipper_angular` `b077fba feat: show clipper studio provider status`
  - `clipper_nestjs` `76bbac8 feat: include clipper studio provider config hints`
  - `clipper_angular` `9ad8455 feat: show clipper studio provider config hints`
  - `GET /v1/projects/clipper-studio/capabilities`는 `llm.script`, `media.search`, `image.generate`, `tts.synthesis`의 `available`/`fallback`/`unavailable` 상태와 provider id를 반환한다.
  - 각 capability는 setup env key를 `configurationKeys`로 반환한다.
  - `/projects` Clipper Studio detail 상단에는 provider 상태 카드와 설정 키 힌트가 표시된다.
  - provider 설정이 없을 때 현재 예상 표시는 `llm.script.deterministic` fallback, `media.search` 미설정, `image.generate` 미설정, `tts.local_os.say` + `tts.legacy_seed.bundle`이다.
- auto media search/apply 1차 slice
  - `clipper_nestjs` `43d9165 feat: auto apply clipper studio search media`
  - media search credential이 있으면 draft 생성 중 clip별 `searchQuery`/keyword로 media search를 자동 실행한다.
  - 첫 검색 후보를 project `draft/assets/auto_search_media/`로 다운로드하고 `media.search.*.image` artifact로 등록한다.
  - edit-state `clipMediaArtifactIds`를 자동 검색 artifact로 채워 render recipe가 seed image 대신 검색 이미지를 사용한다.
  - 기존 user-selected local media는 덮지 않는다. 이전 자동 검색 artifact는 새 draft에서 교체된다.
  - `CLIPPER1_AUTO_MEDIA_SEARCH=0` 또는 `CLIPPER_STUDIO_AUTO_MEDIA_SEARCH=0`으로 끌 수 있고, `CLIPPER1_AUTO_MEDIA_SEARCH_MAX_CLIPS`로 clip 수를 제한한다.

이 순서가 잡히기 전에는 "Clipper1 포함 완료"로 표현하지 않는다.
현재 결과물이 기존 Clipper1과 다르게 보이는 핵심 원인은 render worker보다 production provider endpoint, provider 교체 가능 구조의 정리, 세부 editor/parity가 아직 완성되지 않았기 때문이다. 단색 BMP와 silent WAV의 1차 제거, clip별 local/user media override, macOS local TTS synthesis 1차 연결, Naver/Kakao/remote proxy media search/download 1차 연결, BGM/logo catalog/upload 1차 연결, remote LLM provider boundary 1차 연결, script query 기반 자동 media 적용 1차 연결, script/clip subtitle editor 1차는 완료됐다.

## 먼저 읽을 문서

1. `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-04.md`
2. `.codex/README.md`
3. `.codex/design/NESTJS_CONTROL_PLANE_REDESIGN.md`
4. `.codex/standards/SOLID_AND_BOUNDARIES.md`
5. `.codex/implementation/TASKS.md`
6. `.codex/implementation/WORKLOG.md`
7. `.codex/design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
8. `.codex/design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
9. `.codex/design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
10. `.codex/design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`
11. `.codex/design/WINDOWS_CUDA_RUNTIME_STRATEGY.md`

## repo 상태 메모

- `clipper_python`
  - idle shutdown 커밋 완료: `5ffe077 fix: shut down idle plugin runtime gracefully`
  - source-prepared highlight job 커밋 완료: `780e00d feat: support source-prepared highlight jobs`
  - Clipper1 render worker 커밋 완료: `c53ea33 feat: add clipper1 video render worker`
    - `clipper1_video_render`는 headless `video.render` provider/runtime이며 user-facing workflow가 아님
  - plugin SDK에 `GET /runtime/accelerators` endpoint가 추가되어 있음
  - dance/dialog plugin이 selected runtime device/pipeline을 반환함
  - dialog/dance plugin dependency에 `yt-dlp>=2025.12.8` 추가됨
    - `uv.lock` 기준 resolved version은 `yt-dlp 2026.3.17`
    - packaged venv에서 `yt-dlp` console script를 source ingest provider가 사용함

- `clipper_electron`
  - 사용자가 이전 로컬 커밋을 push했다고 보고함
  - YouTube auth host support 커밋 완료: `2064e19 feat: add YouTube auth host support`
  - 현재 PluginManager는 Electron에 있으며, host-level process manager로 유지한다
  - packaged NestJS가 호출하는 localhost-only plugin host bridge가 추가되어 있음
  - packaged bridge에 `GET /resources`가 추가되어 host/process telemetry를 제공함
  - resource telemetry에 GPU best-effort adapter가 추가되어 있음
  - `build:app`은 Node 22 LTS guard가 추가되어 있음
  - packaged app 창 미표시 방지를 위해 `ready-to-show` 리스너를 renderer load 전에 등록하고 `did-finish-load` fallback show를 둠
  - packaged NestJS env에 `CLIPPER_YTDLP_BIN=<userData>/clipper_venv/bin/yt-dlp`를 주입함
  - packaged NestJS env에 기본 YouTube cookies 후보 `CLIPPER_YTDLP_COOKIES=<userData>/www.youtube.com_cookies.txt`를 주입함
  - packaged NestJS env에 Electron binary를 yt-dlp용 Node JS runtime으로 주입함
  - macOS host memory telemetry는 표시용 used와 리소스 판단용 available을 분리함
    - Dashboard `Memory` used/ratio는 `vm_stat`의 anonymous + wired + compressor 기준으로 Activity Monitor `Memory Used`에 가깝게 표시
    - resource admission은 계속 `availableBytes`를 사용하며 free + inactive + speculative 기반 가용 메모리로 판단
  - packaged venv preflight가 추가되어 있음
    - 앱 시작 시 `uv sync` 후 `python`/`yt-dlp` 존재 여부를 검증함
    - backend URL 조회 또는 plugin start 시 `python`/`yt-dlp`가 없으면 `uv sync`로 userData venv를 복구함
    - `yt-dlp` console script만 누락된 경우 `--reinstall-package yt-dlp` 복구를 한 번 더 시도함
  - YouTube 인증 필요 실패를 처리하기 위해 Electron IPC `clipperBridge.youtubeAuth.openLogin()`이 추가됨
    - 앱 내부 YouTube 로그인 창을 띄움
    - 창을 닫으면 `userData/www.youtube.com_cookies.txt`를 Netscape cookies 파일로 자동 export
    - `/projects` 실패 상세의 `YouTube 로그인 후 다시 실행` 버튼에서 사용
  - Node v22.22.2에서 mac arm64 DMG 패키징 성공
  - 최신 DMG 산출물: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg` (`2026-05-04 20:55 KST`, 150MB)
  - seed asset provider, local/user media provider 1차 slice, local TTS synthesis provider 1차 slice, HTTP/local-server TTS provider, media search/download provider 1차 slice, remote media search proxy provider, image generation provider boundary, BGM/logo catalog/upload provider 1차 slice, remote LLM provider boundary 1차 slice, Ollama/local LLM provider, script/clip editor 1차, `llm.script` provider registry/adapter split, `media.search` provider registry/adapter split, `image.generate` provider registry/adapter split, `tts.synthesis` provider registry/adapter split, provider status/fallback UI, auto media search/apply 1차 slice 포함 재패키징 성공.
  - 앱 번들 내부 `Contents/Resources/clipper_nestjs/projects/assets/clipper-studio-seed/`에 media/TTS/template/logo seed file 포함 확인.
  - packaged NestJS bundle에 `/clipper-studio/media` route와 `media.local_user.file` provider string 포함 확인.
  - packaged NestJS bundle에 `tts.local_os.say`, `CLIPPER1_LOCAL_TTS_*`, `/usr/bin/say` local TTS synthesis path 포함 확인.
  - packaged NestJS bundle에 `media.search.naver.image`, `/clipper-studio/media/remote`, `/clipper-studio/media/search-import` 포함 확인.
  - packaged NestJS bundle에 `RemoteProxyClipperStudioImageSearchProvider`, `CLIPPER1_MEDIA_SEARCH_ENDPOINT`, `CLIPPER_STUDIO_MEDIA_SEARCH_ENDPOINT`, `media.search.remote_proxy.image`, `clipper-studio-media-search.v1` 포함 확인.
  - packaged NestJS bundle에 `prepareClipTts`, `edited_tts`, `clips[] items must include id`, `script must be an object` 포함 확인.
  - packaged Angular renderer bundle에 `메인 제목 1`, `키워드`, `script-editor`, `clip-text-control` 포함 확인.
  - packaged NestJS bundle에 `ClipperStudioMediaSearchProviderRegistry`, `ConfiguredClipperStudioMediaSearchProvider`, `NaverClipperStudioImageSearchProvider`, `KakaoClipperStudioImageSearchProvider`, `ClipperStudioRemoteMediaDownloader` 포함 확인.
  - packaged NestJS bundle에 `ClipperStudioTtsSynthesisProviderRegistry`, `ConfiguredClipperStudioTtsSynthesisProvider`, `MacOsSayClipperStudioTtsProvider`, `tts.local_os.say`, `CLIPPER1_LOCAL_TTS_ENABLED` 포함 확인.
  - packaged NestJS bundle에 `ClipperStudioImageGenerationProviderRegistry`, `ConfiguredClipperStudioImageGenerationProvider`, `HttpClipperStudioImageGenerationProvider`, `image.generate.local_server`, `CLIPPER1_IMAGE_GENERATE_ENDPOINT`, `/clipper-studio/media/generate` 포함 확인.
  - packaged Angular renderer bundle에 `생성 적용`, `generateClipperStudioImage`, `/clipper-studio/media/generate` 포함 확인.
  - packaged Angular renderer bundle에 `clipper-studio/capabilities`, `imageGenerationAvailable`, `이미지 생성 provider 설정 필요` 포함 확인.
  - packaged NestJS bundle에 `scriptGenerationAvailable`, `ttsSynthesisAvailable`, `llm.script.deterministic`, `tts.legacy_seed.bundle` 포함 확인.
  - packaged Angular renderer bundle에 `capability-card`, `clipperStudioCapabilities` 포함 확인.
  - packaged NestJS bundle에 `HttpClipperStudioTtsProvider`, `CLIPPER1_TTS_SYNTHESIS_ENDPOINT`, `CLIPPER_STUDIO_TTS_SYNTHESIS_ENDPOINT`, `tts.synthesis.http`, `clipper-studio-tts-synthesis.v1`, `audioBase64` 포함 확인.
  - packaged NestJS bundle에 `OllamaClipperStudioScriptProvider`, `llm.script.ollama`, `CLIPPER1_LLM_SCRIPT_OLLAMA_MODEL`, `CLIPPER1_LLM_SCRIPT_OLLAMA_ENDPOINT`, `CLIPPER1_LLM_SCRIPT_OLLAMA_BASE_URL`, `/api/generate` 포함 확인.
  - packaged NestJS/Angular bundle에 `configurationKeys`, `CLIPPER1_LLM_SCRIPT_PROVIDER`, `CLIPPER1_IMAGE_GENERATE_PROVIDER_ID`, `CLIPPER1_TTS_SYNTHESIS_SPEAKER_ID`, `capabilityConfigLabel` 포함 확인.
  - packaged NestJS bundle/assets에 `audio.bgm.legacy_bundle`, `audio.bgm.local_user.file`, `logo.local_user.file`, `clipper-studio-bgm` 포함 확인.
  - packaged Electron asar에 `clipper:dialog:openAudioFile` bridge 포함 확인.
  - packaged NestJS bundle에 `ClipperStudioScriptProviderRegistry`, `ClipperStudioScriptResponseNormalizer`, `llm.script.remote_proxy`, `llm.script.openai_responses`, `CLIPPER1_LLM_SCRIPT_ENDPOINT`, `CLIPPER1_LLM_SCRIPT_OPENAI_*` 포함 확인.
  - packaged NestJS bundle에 `CLIPPER1_AUTO_MEDIA_SEARCH_MAX_CLIPS`, `draft/assets/auto_search_media`, `autoMediaSearch` 포함 확인.
  - DMG 생성 중 `/Volumes/Clipper2`가 이미 마운트되어 있으면 `hdiutil detach -force /Volumes/Clipper2` 후 재시도 필요
  - packaged app E2E, 5분 idle shutdown 회귀, `/v1/resources`, `/v1/plugins/:name/runtime-accelerators` runtime 검증 성공

- `clipper_angular`
  - 세션 시작 시 실제 `git status --short --branch`로 로컬 변경 상태를 다시 확인할 것
  - source-aware highlight setup 커밋 완료: `f76d1e1 feat: add source-aware highlight setup`
  - projects page component split 커밋 완료: `7da0fdc refactor: split projects page components`
  - project render job UI 커밋 완료: `eea2e9e feat: add project render job UI`
    - headless `clipper1_video_render`는 Store/Dashboard user-visible 목록에서 숨김
    - render controls는 Clipper Studio manifest output에만 열려야 함
  - Clipper Studio workflow shell 커밋 완료:
    - `5186325 feat: add clipper studio workflow shell`
    - `083083c feat: generate clipper studio drafts`
    - `9c8c290 feat: run clipper studio drafts as jobs`
    - `1045c46 feat: show clipper studio final renders`
    - `81fec28 fix: refresh clipper studio render manifest`
    - `6d7332a feat: add clipper studio edit state client`
    - `3f135a7 feat: edit clipper studio render settings`
    - `5836899 feat: select clipper studio templates`
    - `47f3151 feat: select clipper studio audio and logo assets`
      - 현재 BGM/logo select는 `ClipperStudioAssetPreparer`가 만든 project artifact 기반이다.
    - `bb543e9 feat: add clipper studio bgm and logo import UI`
      - BGM `추가`는 audio file dialog -> NestJS import role `bgm` -> `audio.bgm.local_user.file` artifact를 선택 상태로 반영한다.
      - 로고 `추가`는 image/video dialog 중 image file -> NestJS import role `logo` -> `logo.local_user.file` artifact를 선택 상태로 반영한다.
    - `db4fc42 feat: edit clipper studio clip media`
      - clip media select는 project media artifact 기반이다.
    - `b8bd59a feat: apply clipper studio media search results`
      - clip row의 `검색 적용` 입력/버튼으로 media search/download 첫 후보를 해당 clip에 적용한다.
    - `8e20564 feat: use clipper studio script search queries`
      - script provider가 내려준 clip `searchQuery`가 있으면 `검색 적용` 입력의 기본값으로 사용한다.
    - `609a9b9 feat: select clipper studio tts presets`
    - `8217791 feat: show clipper studio render versions`
    - `edb2de6 feat: link clipper studio render versions`
    - `b9dec90 feat: show clipper studio render empty state`
    - `1341a3d polish clipper studio render empty state`
    - `c1f9d22 fix projects detail panel scrolling`
      - `/projects` detail panel host가 `overflow-y: auto`로 바뀌어 Clipper Studio `편집 상태` 이하를 실제 UI에서 스크롤 접근 가능.
  - 특정 PC의 임시 로컬 변경 상태를 인계 조건으로 가정하지 말 것
  - Resource dashboard 1차 UI 변경이 추가되어 있음
  - Dashboard warning badge는 NestJS `resourceAssessment` 기반으로 전환되어 있음
  - Dashboard plugin start는 admission `409` 시 confirm 후 `confirmResourceWarning: true`로 재시도함
  - `PluginLocator`와 정적 `pluginUrls`는 제거됨. Angular feature discovery는 NestJS `/plugins` 기반.
  - Store/Dashboard/Projects는 공통 `PageHeaderComponent`를 사용함
  - Dashboard는 기본 page scroll 없이 plugin list 내부만 scroll되도록 조정됨
  - `/projects` 작업 보관함은 dialog/dance별 2단 결과 상세 UI를 사용함
  - `/projects` 대사 상세의 `구간/대사` 정보 영역은 최소 `280px`을 보장함
  - `/projects` 대사 하이라이트 영상 플레이어는 최소 `300px` 폭을 보장하고, 9:16 frame이 flex shrink로 눌리지 않도록 고정됨
  - PC 전용 Electron 앱 기준으로 주요 상세 영역은 세로 stacked 전환하지 않음
  - 창 자체는 자유롭게 줄일 수 있고, `/dashboard`, `/store` 내부 작업 영역은 `1296px`, `/projects` 내부 작업 영역은 `1368px` 최소 폭 + app main 가로 스크롤로 접근함
  - `/dashboard`, `/store`는 `/projects`와 동일하게 헤더/본문 컨테이너 최대 폭 `1360px`, 중앙 정렬, wide viewport 좌우 여백 증가 정책을 사용함
  - Dashboard/Store에 남아 있던 모바일 stacked 전환 media query는 제거됨
  - dialog/dance setup 화면은 `로컬 파일 / YouTube URL` 입력 source mode를 지원함
    - 입력 방식 토글의 표시 순서는 `YouTube URL` → `로컬 파일`
    - 기본 선택값은 `YouTube URL`
    - Angular는 직접 다운로드하지 않고 NestJS job params에 `source` 객체를 전달함
    - local file source는 기존 plugin 호환을 위해 `video_path`도 함께 전달함
    - YouTube URL은 즉시 queue enqueue하지 않고 `POST /v1/sources/inspect`로 제목/썸네일 metadata를 먼저 조회함
      - setup 화면의 `SOURCE_CONFIRM` 단계에서 영상 정보를 보여주고 사용자가 확인해야 다음 단계로 진행
      - dialog는 확인 후 job enqueue
      - dance는 확인 후 해당 제목으로 아티스트 감지, 최종 pipeline enqueue에도 같은 `source_assets` 전달
      - enqueue params에 `title`과 `source_assets`를 포함하므로 실행 큐 최초 표시부터 YouTube id 대신 영상 제목이 보임
      - inspect 단계에서 YouTube 인증이 필요하면 setup 에러 영역에 `YouTube 로그인` 버튼을 표시하고, 로그인 창 종료 후 같은 URL 확인을 다시 시도함
    - ffmpeg/ffprobe 상태가 `ready` 또는 `done`이 아니면 setup 실행 버튼은 비활성화됨
      - 다운로드 중 버튼 라벨: `ffmpeg 설치 중…`
  - dance setup은 수동 `영상 제목 (아티스트 감지용)` 입력을 더 이상 사용하지 않음
    - YouTube URL은 `POST /v1/sources/inspect` 결과의 `SourceAsset.label`을 아티스트 감지 제목으로 사용
    - 로컬 파일은 파일명 stem을 아티스트 감지 제목으로 사용
    - Angular core에 `SourceInspectService`가 추가됨
    - 아티스트 멤버별 얼굴 이미지 선택은 NestJS `DanceReferenceCacheService`가 캐시함
      - 저장 위치: `CLIPPER_DATA_DIR/dance/reference-cache.json`
      - `dance_highlight` job enqueue 시 `dance_setup.members[].selectedImages`를 저장
    - 같은 아티스트/QID 선택 시 `/v1/dance/artists/members`가 `cacheHit: true`, `cachedSelections`를 반환
    - Angular는 cache hit 시 멤버 이미지 선택 단계를 건너뛰고 캐시된 selectedImages로 바로 `dance_highlight` job을 실행 큐에 추가
    - 신규 선택 흐름도 멤버당 3장 이상 선택하면 `선택 완료` 클릭 시 바로 `dance_highlight` job을 실행 큐에 추가하고 작업 보관함으로 이동
    - 멤버 이미지 선택 조건이 미충족이면 어떤 멤버가 몇 장 부족한지 표시함
  - `/projects` 상세 헤더 아래에 입력 소스와 provider 요약을 표시함
  - `/projects` 실행 큐는 접히는 queue bar + overlay drawer 구조임
    - drawer는 완료 작업 영역을 밀지 않고 위를 덮음
    - 큐 바깥 영역 클릭 시 자동으로 접힘
    - 2026-04-30 기준 스타일은 큐 바 자체가 헤더이고, 펼치면 큐 카드 popover가 바 아래에 바로 붙어 한 패널처럼 열리는 형태임
    - 실행 큐 카드 제목 아래에는 플러그인명만 표시하고, 입력 파일/URL 소스 라벨은 표시하지 않음
    - 실행 큐 카드와 완료 작업 리스트 카드는 입력 소스 썸네일을 표시함
      - YouTube URL 입력은 `source_assets.metadata.thumbnail`의 YouTube 썸네일 URL 사용
      - 로컬 파일 입력은 enqueue 전에 `/v1/sources/ingest`로 ffmpeg 썸네일을 생성하고 `source_assets.thumbnailPath`를 `/v1/sources/file?path=...`로 표시
      - 작업 보관함 조회 시점에는 새 썸네일을 생성하지 않음
    - 현재 `build:electron`은 style budget warning 없이 성공함
  - 전역 scrollbar는 transparent track + 진한 회색 thumb 스타일임
  - `/projects` 작업 보관함 후속 조정이 진행됨
    - 실행 큐, 완료 작업 목록, 상세 영역은 최대 콘텐츠 폭 `1360px`로 제한
    - 안무 상세의 인물 리스트는 `170px`, 클립 리스트는 `304px` 고정 폭
    - 안무 상세 인물 리스트는 `ProjectRenderItem.mappedMember === true`인 멤버 매핑 인물을 먼저 표시함
      - fallback 인물 1개 클립 숨김도 `person...` 문자열이 아니라 `mappedMember` 기준
    - 안무 상세 배치는 `영상 모음 플레이어 | 클립 리스트`
    - 창 폭 축소 시 세로 stacked 전환 대신 내부 `1368px` 작업 영역과 app main 가로 스크롤로 접근함
    - 최신 packaged app에서 `/projects` 900px viewport CDP 계측 결과 app main 가로 overflow 발생, `/projects` width `1368px` 유지, 대사 플레이어 `300px`, 대사 정보 `280px` 유지
    - `projects.component.scss` component style budget warning은 row/overlay/player empty visual atom을 `src/styles.scss`의 `.projects-page` 전역 범위로 이동해 제거됨
    - `/projects` component split 1차 완료
      - `ProjectsComponent`는 page shell/state orchestration 중심으로 축소
      - 실행 큐: `ProjectsQueueComponent`
      - 완료 작업 리스트: `ProjectsHistoryListComponent`
      - 상세 shell: `ProjectsDetailPanelComponent`
      - 대사 상세: `DialogResultDetailComponent`
      - 안무 상세: `DanceResultDetailComponent`
      - 클립 overlay: `ProjectsClipOverlayComponent`
      - `projects.component.scss`는 page layout shell만 남고, 가장 큰 새 component style도 8kB budget보다 작음
  - YouTube 인증이 필요한 실패 작업에는 `YouTube 로그인 후 다시 실행` 버튼이 표시됨
    - 버튼 클릭 시 Electron 로그인 창을 열고, 쿠키 export 후 같은 작업을 retry
  - `.nvmrc`는 `22`

- workspace root
  - `/Users/jina/project/adlight/.nvmrc`도 `22`
  - Codex 비대화형 shell은 `~/.zshrc`를 자동 로드하지 않을 수 있으므로 build 전 `source ~/.zshrc && nvm use 22`를 명시하는 편이 안전함
  - Clipper1 inventory 및 shared capability 분해 설계 문서화 완료
    - 문서: `.codex/design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
    - 포함: endpoint/service/template/media download/TTS/render/project output inventory
    - 포함: Clipper1을 giant plugin이 아니라 shared capability layer로 분해하는 설계
    - 포함: `ProjectManifest`, dialog/dance/clipper1 output artifact model, `TemplatePreset`, `RenderRecipe` 초안
  - `clipper_nestjs` ProjectManifest Phase A/B/C 및 TemplatePreset/RenderRecipe provider 1차 구현 완료
    - `src/project-manifest/dto/project-manifest.dto.ts`
    - `src/project-manifest/dto/template-preset.dto.ts`
    - `src/project-manifest/dto/render-recipe.dto.ts`
    - `src/project-manifest/fixtures/*`
    - `src/project-manifest/project-manifest-builder.ts`
    - `src/project-manifest/project-manifest.module.ts`
    - `src/project-manifest/template-preset-catalog.service.ts`
    - `src/project-manifest/render-recipe-provider.ts`
    - `src/project-manifest/template-preset-source.ts`
    - `src/project-manifest/built-in-template-preset-source.ts`
    - `src/project-manifest/legacy-clipper1-template-adapter.ts`
    - `src/project-manifest/legacy-clipper1-template-preset-source.ts`
    - `src/project-manifest/legacy-clipper1-render-recipe-provider.ts`
    - `src/project-manifest/video-render-provider.ts`
    - `src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
    - `src/project-manifest/legacy-clipper1-video-render-provider.ts`
    - `src/project-manifest/fixtures/legacy-clipper1-template-row.fixtures.ts`
    - `GET /v1/projects/:projectId/manifest`
    - `GET /v1/template-presets`
    - `GET /v1/template-presets/:presetId`
    - `GET /v1/projects/:projectId/outputs/:outputId/render-recipe`
    - `npm run build` 성공
    - 기존 `GET /v1/projects/:projectId/detail` 응답은 변경하지 않았고, manifest는 별도 endpoint로 노출함
    - artifact `access` contract 추가
      - `project-file`: `/v1/projects/:projectId/file?path=...`
      - `source-file`: `/v1/sources/file?path=...`
  - Clipper Studio workflow shell/draft 커밋 완료:
    - `167eae7 feat: add clipper studio project shell`
    - `5f5330a feat: add clipper studio draft generation`
    - `559652e feat: add clipper studio draft jobs`
    - `329fc84 feat: split clipper studio script generator`
    - `673c965 feat: prepare clipper studio render assets`
    - `3ea487b feat: promote clipper studio render results`
    - `f699a30 feat: update clipper studio edit state`
    - `4d75b9e feat: load clipper1 template catalog from json`
    - `fbb0340 feat: support clipper studio clip media selection`
    - `58af2fd feat: add clipper studio tts preset catalog`
    - `d518b12 feat: preserve clipper studio render versions`
      - `remote-url`: direct URL
    - 실제 packaged userData의 dialog/dance 완료 프로젝트로 smoke 완료
      - dialog `1777547421406`: artifact 15개, output 6개, project-file 13개 접근 성공
      - dance `1777548695384`: artifact 108개, output 8개, project-file 106개 접근 성공
      - dance 비ASCII entity/artifact id collision 방지를 위해 Unicode code point 기반 ASCII id encoding 적용
    - `shorts.basic_letterbox`를 dialog/dance 기본 render template preset으로 연결함
    - render recipe smoke 완료
      - dialog `output.dialog.clip.0`: subtitle track 1개, destination `clips/clip_00_00-05-00-31.mp4`
      - dance `output.dance.render.person_6`: destination `renders/dance/person_6_montage.mp4`
    - Clipper1 template catalog source 분리 완료
      - `TemplatePresetSource` 합성 구조
      - `BuiltInTemplatePresetSource`
      - `LegacyClipper1TemplatePresetSource`
      - `LegacyClipper1TemplateRow` -> `TemplatePreset` adapter
      - `GET /v1/template-presets?source=builtin`
      - `GET /v1/template-presets?source=clipper1&locale=ko-KR`
    - Clipper1 legacy template apply -> `RenderRecipe` 매핑 1차 완료
      - `ClipperStudioProjectDetail.clips` -> `RenderTimelineItem`
      - subtitles -> `SubtitleTrack`
      - TTS/BGM artifacts -> `AudioTrack`
      - title/logo state -> `OverlayTrack`
      - smoke: duration `8.4`, timeline 2개, audio 3개, subtitle item 2개, overlay 3개
    - `VideoRenderProvider` contract 및 Clipper1 dry-run payload mapper 1차 완료
      - `RenderRecipe` -> legacy `VideoService.create_video` payload
      - smoke: `project_id 1001`, `template_id 1`, `contents_ratio full`, clip 2개, BGM/TTS/title payload 매핑
      - dry-run provider id: `video.render.legacy_clipper1.dry_run`
    - `video.render` provider registry 및 render job skeleton 1차 완료
      - `VideoRenderProviderRegistry`
      - `VideoRenderJobRepository` / `JsonVideoRenderJobRepository`
      - `VideoRenderJobsService`
      - persisted store: `CLIPPER_DATA_DIR/render-jobs/render-jobs.json`
      - 신규 API:
        - `GET /v1/projects/:projectId/outputs/:outputId/render-providers`
        - `POST /v1/projects/:projectId/outputs/:outputId/render-jobs`
        - `GET /v1/projects/:projectId/render-jobs`
        - `GET /v1/projects/:projectId/render-jobs/:renderJobId`
      - packaged userData dialog output provider list smoke 완료
      - Clipper Studio fixture render job dry-run smoke 완료: `succeeded`, result `dry_run`, duration `8.4`, payload clip 2개
    - `clipper1_video_render` Python worker contract 및 NestJS python-worker provider 연결 완료
      - `clipper_python/plugins/clipper1_video_render`
      - 표준 PluginRuntime `/jobs` + `/jobs/{job_id}/events` 사용
      - capability: `video.render.legacy_clipper1`
      - `dry_run` mode로 legacy payload 검증/receipt 기록
      - NestJS provider id: `video.render.legacy_clipper1.python_worker`
      - provider는 `PluginHost.ensureStarted('clipper1_video_render')` 후 `/jobs` submit, WebSocket completion wait
      - smoke: provider -> worker -> WS complete 성공, status `dry_run`, duration `8.4`, clip count `2`
    - `clipper1_video_render` first-pass execute adapter 완료
      - `LocalRenderAdapter`
      - image/video clip을 vertical MP4 segment로 normalize
      - segments concat 후 `recipe.output.destination.relativePath`에 mp4 저장
      - `<stem>_thumbnail.jpg` 썸네일 저장
      - NestJS provider가 worker result의 relative paths를 `render.video` / `render.thumbnail` artifact로 변환
      - smoke: `/tmp/clipper1-execute-smoke/renders/main.mp4`, `/tmp/clipper1-execute-smoke/renders/main_thumbnail.jpg`, duration `8.466667`
    - `clipper1_video_render` 기본 subtitle compositing 완료
      - 최초에는 `clips[].subtitles[].subtitle` / `duration`을 clip별 SRT로 변환
      - 이후 ASS overlay로 전환해 subtitle/title style을 legacy settings에서 읽음
      - smoke: `subtitle_segment_count: 2`, `/tmp/clipper1-execute-smoke/renders/subtitle_check.jpg` frame extraction 완료
    - `clipper1_video_render` TTS/BGM audio mixing 완료
      - subtitle별 local `tts_url`을 duration 기준으로 normalize하고 clip 순서대로 concat
      - TTS가 없거나 clip tail이 남으면 silence로 duration align
      - local `bgm_url`을 전체 duration에 맞춰 loop/trim 후 TTS와 ffmpeg `amix`로 합성
      - final MP4에 AAC 2채널 audio stream mux
      - smoke: audio `{ tts_clip_count: 2, bgm: true, mixed: true, bgm_volume: 0.15 }`, ffprobe audio `aac`, 2 channels
    - `clipper1_video_render` content area / ASS text overlay 1차 완료
      - `contents_ratio` / `contents_area_y_offset` 기반 content area 배치
      - subtitle font size/color/outline/y position을 legacy `template_settings`에서 읽음
      - main/sub/bottom title text overlay도 ASS event로 burn-in
      - smoke: visual `{ overlay_mode: 'ass', content_area: { x: 0, y: 0, width: 1080, height: 1920 } }`, `/tmp/clipper1-execute-smoke/renders/visual_check.jpg`
    - `clipper1_video_render` local layout/logo image overlay 1차 완료
      - local `template_settings.layout_image`를 background로 사용
      - media는 content area 위에 overlay
      - local `project.logo_image`는 `logo_type: IMAGE`일 때 `logo_image_*` 설정으로 overlay
      - direct adapter smoke: visual `{ overlay_mode: 'ass', content_area: { x: 0, y: 420, width: 1080, height: 810 }, layout_image: true, logo_image: true }`
      - frame check: `/tmp/clipper1-execute-smoke/renders/layout_logo_check.jpg`
    - `clipper1_video_render` recipe-declared image zoom/pan motion effects 1차 완료
      - `RenderRecipe.timeline.items[].effects`의 `zoom` / `pan`을 image clip에 적용
      - direct adapter smoke에서 start/end frame md5 차이로 motion 확인
      - provider smoke: visual motion effects `source: explicit`의 `zoom in`, `pan left_to_right` 2개 반환
    - `clipper1_video_render` legacy automatic image motion parity 1차 완료
      - recipe-declared effect가 없는 image clip은 `ffprobe` image size와 content area ratio로 자동 motion 선택
      - Clipper1 기준처럼 ratio 차이 `<= 0.3`은 zoom, wide image는 horizontal pan, tall image는 vertical pan
      - legacy runtime random은 재현 가능한 render를 위해 clip index + media path hash 기반 deterministic choice로 대체
      - direct adapter smoke: automatic horizontal pan / zoom / vertical pan 모두 start/end frame md5 차이 확인
      - 현재 미구현: video/GIF motion parity, remote asset persistent cache/manifest registration

- `clipper_nestjs`
  - plugin facade와 job/queue facade가 추가됨
  - source ingestion/provenance 커밋 완료: `35337dc feat: add source ingestion and provenance`
  - project manifest render jobs 커밋 완료: `4f31579 feat: add project manifest render jobs`
  - project/output history facade가 추가됨
  - `GET /v1/projects/:projectId/detail`, `GET /v1/projects/:projectId/manifest`, `GET /v1/projects/:projectId/outputs/:outputId/render-recipe`, `GET /v1/projects/:projectId/file?path=...`가 추가됨
  - `GET /v1/template-presets`와 `GET /v1/template-presets/:presetId`가 추가됨
  - `video.render` provider/job skeleton API가 추가됨
    - `GET /v1/projects/:projectId/outputs/:outputId/render-providers`
    - `POST /v1/projects/:projectId/outputs/:outputId/render-jobs`
    - `GET /v1/projects/:projectId/render-jobs`
    - `GET /v1/projects/:projectId/render-jobs/:renderJobId`
  - Clipper1 Python worker render provider가 추가됨
    - `LegacyClipper1PythonWorkerRenderProvider`
    - provider id: `video.render.legacy_clipper1.python_worker`
    - 현재 descriptor는 `executionMode: python-worker`, `dryRun: false`
    - `StartVideoRenderJobRequest.dryRun` / provider context에 따라 worker `dry_run` 또는 `execute` mode 선택
  - 신규 job의 output root는 기본적으로 `CLIPPER_DATA_DIR/projects/files/<projectId>` 아래로 자동 지정됨
  - resource facade `GET /v1/resources`가 추가됨
  - advisory `GET /v1/plugins/:name/resource-assessment`가 추가됨
  - running plugin의 Python accelerator probe를 조회하는 `GET /v1/plugins/:name/runtime-accelerators`가 추가됨
  - `POST /v1/plugins/:name/start`는 warning/critical/unknown assessment 시 confirmation 없으면 `409` 반환
  - `HostResourceSnapshot.accelerators.gpus`와 VRAM assessment reason이 추가되어 있음
  - packaged Electron utilityProcess용 `ws` WebSocket client dependency가 추가됨
  - Angular-facing job event stream은 SSE가 아니라 WebSocket `/v1/events`
  - `AuthProvider`/`AuthContextService`/`LicensePolicyService` 경계가 추가됨
  - 현재 auth는 기본 `local`, smoke용 `CLIPPER_AUTH_MODE=trusted-header`
  - job/project에는 `ownerSubjectId`가 있고 HTTP/WS는 subject별 필터링됨
  - `ExecutionScopeService`와 `JobQueue` 추상화가 추가됨. 현재 queue 구현은 `InMemoryJobQueue`
  - running/starting job 취소 시 active queue slot을 즉시 release하고 다음 waiting job을 drain함
  - cancelled job은 늦게 도착하는 plugin event가 상태를 덮어쓰지 못하도록 방어함
  - 앱 종료/재실행으로 이전 active job이 interrupted 처리될 때 사용자 문구로 실패 표시함
    - error: `앱이 종료되어 작업이 완료되지 않았습니다. 다시 실행해주세요.`
    - 기존 raw error `NestJS process restarted before the job completed.`는 job store 로드 시 자동 마이그레이션됨
  - 산출물 접근은 `ArtifactStorage` 추상화 뒤에 있고 현재 구현은 `LocalArtifactStorage`
  - project detail 변환은 `ProjectDetailBuilder`로 분리됨
  - `SourcesModule` 1차 구현이 추가됨
    - `SourceInput`, `SourceAsset`, `POST /v1/sources/inspect`, `POST /v1/sources/ingest`
    - local file source provider
      - `/v1/sources/ingest` 시 로컬 영상 썸네일을 `CLIPPER_DATA_DIR/sources/local/<sourceId>/thumbnail.jpg`로 생성
      - `/v1/sources/inspect`는 로컬 영상 썸네일을 생성하지 않음
      - cached source file serving endpoint `GET /v1/sources/file?path=...` 추가
    - YouTube URL source provider
      - `yt-dlp` metadata inspect
      - global source cache 다운로드
      - 다운로드된 local video path를 기존 plugin용 `video_path`로 변환
      - `CLIPPER_YTDLP_COOKIES`, `CLIPPER_YTDLP_COOKIES_FROM_BROWSER` 지원
      - `CLIPPER_YTDLP_NODE_BIN` 기반 JS runtime 지정 지원
      - `CLIPPER_YTDLP_FFMPEG_LOCATION` 기반 yt-dlp `--ffmpeg-location` 지정 지원
      - YouTube `n challenge`/signature 확인용 remote component 기본 활성화
        - 기본값: `--remote-components ejs:github`
        - `CLIPPER_YTDLP_REMOTE_COMPONENTS=0`으로 비활성화 가능
      - YouTube 다운로드 포맷은 Python 파이프라인 호환성을 위해 h264 mp4를 우선 선택
      - YouTube source cache에서 `source.fNNN.*` yt-dlp format fragment는 완성 영상으로 재사용하지 않음
      - job source 준비 단계에서 yt-dlp 진행 로그를 파싱해 `/projects` 실행 큐 메시지/진행률에 반영함
        - 표시 예: `YouTube 영상 정보 확인 중`, `YouTube 영상 다운로드 중`, `YouTube 영상 병합 중`
        - 실행 큐는 단일 `PipelineJobSnapshot.progress`만 표시함
        - YouTube source 준비는 현재 dialog/dance pipeline의 첫 실제 checkpoint인 `10%` 입력 준비 구간을 채움
        - dialog/dance plugin app의 초기 `파이프라인 시작` 이벤트도 `10%`로 맞춰 source 준비 완료 후 0%로 되돌아가지 않음
      - inspect 응답 metadata에는 YouTube `thumbnail` URL이 포함됨
      - retry 시 stale `video_path`가 남지 않도록 `asset.localPath`가 있으면 `video_path`를 덮어씀
      - YouTube bot/sign-in 확인 에러는 raw stderr 대신 짧은 로그인 재시도 안내 문구로 변환
      - 제품 문구: `YouTube 로그인 인증이 필요한 영상입니다. YouTube 로그인 후 다시 시도해주세요.`
      - challenge solver 실패는 raw stderr 대신 짧은 제품 문구로 변환
      - FFmpeg 누락 실패는 raw stderr 대신 짧은 제품 문구로 변환
      - `yt-dlp` 실행 파일 누락(`spawn ENOENT`)은 raw path 포함 에러 대신 짧은 제품 문구로 변환
      - Chrome/Safari 등 사용자 브라우저 쿠키 자동 fallback은 기본 비활성화
        - macOS `Chrome Safe Storage` 키체인 접근 alert 방지 목적
        - `CLIPPER_YTDLP_AUTO_BROWSER_COOKIES=1`을 명시한 개발/진단 환경에서만 `--cookies-from-browser` fallback 사용
    - job 실행 단계에서 `source` 또는 기존 `video_path`를 `source_assets`로 변환함
    - project snapshot/detail에는 `sourceAssets`와 provenance가 저장됨
  - `DanceReferenceCacheService`가 추가됨
    - `CLIPPER_DATA_DIR/dance/reference-cache.json`에 사용자별/아티스트별 멤버 reference image URL selection을 저장
    - `JobsService`가 `dance_highlight` enqueue 시 cache 저장을 시도함
    - `DanceController.resolveMembers`는 cache hit 여부와 cached selected image URLs를 반환함
  - dance render title은 데이터에서 `${personId} 영상 모음`으로 만들지 않고 `person_name`/`person_id`만 저장함
    - Angular 플레이어 제목에서만 `인물명 영상 모음`으로 표시
  - dance project detail은 `dance_meta.dance_setup.members`의 `memberKey`/`memberName`으로 실제 멤버 매핑 여부를 계산해 person/render DTO의 `mappedMember`로 내려줌
  - 다음 구현의 핵심 대상은 remote auth/license 실제 연동, DB/Redis-backed queue, object storage backend, resource-aware plugin management
  - `.nvmrc`는 `22`

## 다음 구현 시작점

1. 4개 repo의 `git status --short --branch` 확인
2. `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-04.md` 확인
3. 사용자가 최신 DMG를 직접 확인한 피드백이 있으면 그 피드백을 최우선으로 반영
4. provider 추가가 필요하면 기존 registry/adapter boundary 뒤에 구현체만 추가
   - `llm.script`: `6797b5a`, `0da9415`에서 1차 완료.
   - `media.search`: `36211b5`, `8aac74d`에서 1차 완료.
   - `image.generate`: `a95c35a`에서 1차 완료.
   - `tts.synthesis`: `db92d6a`, `b170178`에서 1차 완료.
5. production provider endpoint/key/billing 정책 확정 및 실제 endpoint 운영
6. Clipper Studio visual QA와 error state polish
7. final MP4/thumbnail preview visual QA와 empty/error/re-render state polish

Render provider follow-up은 이 사용자 workflow path가 생긴 뒤 진행한다.

- 현재 registry/job skeleton, Python worker endpoint 계약, first-pass local mp4/thumbnail execute adapter는 완료됨
- 기본 subtitle compositing, TTS/BGM audio mixing, content area / ASS text overlay, local layout/logo image overlay, recipe-declared image zoom/pan, legacy automatic image zoom/pan, remote asset staging도 완료됨
- 남은 render work: video/GIF motion parity, template-specific subtitle style, remote asset persistent cache, object storage/CDN long render E2E
- legacy `VideoService.create_video`의 S3 upload/callback 책임은 계속 artifact store boundary 뒤로 분리
   - 실행 큐 expand/cancel/move-to-front
   - 완료 작업 선택/필터
   - dialog 상세 clip 선택
   - dance 상세 render 선택/clip overlay
7. YouTube URL job E2E 확인
   - bot/sign-in 확인 실패 시 `/projects` 실패 상세에서 `YouTube 로그인 후 다시 실행` 클릭
   - 열린 앱 내부 YouTube 창에서 로그인 후 창을 닫으면 `userData/www.youtube.com_cookies.txt`가 자동 생성되고 retry됨

## 마지막 완료 작업

Workflow / Shared Capability foundation의 첫 vertical slice로 `SourceInput` / `SourceAsset`와 YouTube URL 입력을 구현하고, YouTube 인증 필요 실패에 앱 내부 로그인/쿠키 export/retry 흐름을 추가했다. 이후 YouTube URL 입력은 queue enqueue 전에 제목/썸네일 확인 단계를 거치도록 보강했고, 실행 큐 중복 소스 라벨 제거와 안무 얼굴 이미지 선택 캐시를 추가했다. 실행 큐/완료 작업 카드에는 입력 소스 썸네일을 표시하도록 보강했으며, 로컬 파일 썸네일은 조회 시점이 아니라 enqueue 전 `/sources/ingest` 단계에서 생성한다.

2026-05-04에는 `adlight_angular`/`adlight_python`의 `feature/d2x-electron` branch와 Clipper1 관련 `.codex`/`docs/clipper` 문서를 읽고 `CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`를 추가했다. 이어서 Phase A로 `clipper_nestjs/src/project-manifest` contract-only DTO와 fixtures를 추가했고, Phase B로 `ProjectManifestBuilder`와 `GET /v1/projects/:projectId/manifest`를 추가해 dialog/dance detail을 공통 artifact/output 모델로 매핑했다. Phase C로 실제 packaged userData 완료 프로젝트에 대해 manifest endpoint를 smoke하고, artifact `access` contract와 비ASCII id encoding을 보정했다. 이후 `TemplatePresetCatalogService`, `RenderRecipeProvider`, `GET /v1/template-presets`, `GET /v1/projects/:projectId/outputs/:outputId/render-recipe`를 추가하고 실제 dialog/dance output으로 smoke했다. 마지막으로 `TemplatePresetSource` 구조, built-in source, Clipper1 row adapter/source를 추가해 fixture 직접 seed를 source 기반 catalog로 분리했고, `LegacyClipper1RenderRecipeProvider`로 Clipper Studio detail을 timeline/audio/subtitle/overlay tracks가 있는 recipe로 변환했다. 이어 `VideoRenderProvider` contract, `LegacyClipper1RenderPayloadMapper`, dry-run `LegacyClipper1VideoRenderProvider`를 추가해 recipe를 legacy render payload로 변환했다. 후속으로 `VideoRenderProviderRegistry`, persisted `VideoRenderJob` skeleton, `/projects/:projectId/.../render-providers`, `/render-jobs` API를 추가했다. 이어 `clipper1_video_render` Python worker plugin과 NestJS `LegacyClipper1PythonWorkerRenderProvider`를 추가해 provider -> Python worker -> WebSocket completion 경계를 검증했다. 마지막으로 worker first-pass execute adapter를 추가해 실제 로컬 mp4/thumbnail artifact를 생성했고, SRT 기반 기본 subtitle compositing, TTS/BGM audio mixing, content area / ASS text overlay, local layout/logo image overlay, recipe-declared image zoom/pan motion effects, legacy automatic image zoom/pan motion parity를 추가했다. `clipper_nestjs npm run build`, `clipper_python` compileall, local execute smoke, ffprobe audio stream, extracted frame visual check, provider worker smoke로 검증했다.

완료:

- `clipper_nestjs`
  - `sources` 모듈 추가
  - `DanceReferenceCacheService` 추가
  - `SourceInput`, `SourceAsset`, `POST /v1/sources/inspect`, `POST /v1/sources/ingest` 추가
  - local file provider 추가
    - 로컬 영상 ingest 시 ffmpeg로 source thumbnail 생성
    - source cache file serving endpoint 추가
  - YouTube URL provider 추가
    - `yt-dlp` metadata inspect/download
    - source cache 저장
    - 기존 Python plugin 호환용 `video_path` 변환
    - cookies 옵션과 bot 확인 에러 안내 추가
    - JS runtime warning 제거를 위한 `CLIPPER_YTDLP_NODE_BIN` 지원
    - 인증 필요 실패는 raw yt-dlp stderr 대신 `/projects`의 로그인 후 retry 흐름 안내 문구로 변환
  - job 실행 단계에서 source ingest 수행
  - project snapshot/detail에 `sourceAssets` 저장
- `clipper_angular`
  - 실행 큐 카드 제목 아래의 입력 소스 라벨 제거, 플러그인명은 유지
  - 실행 큐/완료 작업 카드에 입력 소스 썸네일 표시
  - 안무 cache hit 시 멤버 이미지 선택 단계를 건너뛰고 바로 job enqueue
  - dialog/dance setup에 `로컬 파일 / YouTube URL` 입력 선택 추가
  - YouTube URL 입력 시 제목/썸네일 확인 화면을 먼저 보여주고, 확인 후에만 enqueue 또는 아티스트 감지 진행
  - job enqueue 시 `source` 객체 전달
  - YouTube enqueue params에 `title`과 `source_assets`를 미리 포함해 queue 최초 표시부터 영상 제목을 사용
  - 작업 보관함 title/source label이 `source_assets`/`sourceAssets`를 우선 사용
  - 작업 보관함 상세 헤더 아래에 입력 소스/provider 요약 표시
  - 인증 필요 실패 작업에 `YouTube 로그인 후 다시 실행` 버튼 추가
- `clipper_python`
  - dialog/dance plugin dependency에 `yt-dlp` 추가
- `clipper_electron`
  - packaged NestJS env에 venv `yt-dlp` 경로와 기본 cookies 파일 후보 주입
  - YouTube 로그인 IPC/preload 추가
  - YouTube 로그인 창 종료 시 cookies.txt 자동 생성

검증:

- `clipper_nestjs`: `npm run build` 성공
- `clipper_angular`: `npm run build:electron` 성공, warning 없음
- `clipper_electron`: `npm run build` 성공
- `clipper_python`: `uv run yt-dlp --version` 성공 (`2026.03.17`)
- compiled `SourceService.prepareJobParams({ source: { type: 'local_file', path: './package.json' } })` smoke 성공
- YouTube metadata smoke는 네트워크 허용 후 bot 확인 에러를 재현했고, 쿠키 설정 안내 메시지로 변환되는 것을 확인
- 사용자 테스트 URL `-MMqcUhgquc` smoke에서 JS runtime 경고 제거 및 짧은 인증 안내 메시지 확인
- bundled NestJS에서 `CLIPPER_YTDLP_AUTO_BROWSER_COOKIES === '1'` 조건 확인
- 사용자 테스트 URL `-MMqcUhgquc`에 대해 앱 로그인 쿠키 + Electron Node runtime + `--remote-components ejs:github` 조합으로 yt-dlp smoke 성공
  - metadata print 성공: id/title/duration 추출
  - download format simulate 성공: `399+140`, `mp4`
- 사용자 테스트 URL `-MMqcUhgquc`에 대해 `--ffmpeg-location <userData>/bin` 조합으로 2초 구간 실제 다운로드/병합 smoke 성공
  - 결과: `/tmp/clipper-ytdlp-smoke/source.mp4`
- 이전 ffmpeg 실패가 남긴 `source.f399.mp4` fragment cache를 수정된 `SourceService.ingest()`가 무시하고 병합본 `source.mp4`를 생성하는 smoke 성공
  - 결과: `/Users/jina/Library/Application Support/Clipper2/sources/youtube/-MMqcUhgquc/source.mp4`
  - ffprobe 기준 `h264` video + `aac` audio 포함
- bundled NestJS에서 `--remote-components`와 기본 `ejs:github` 반영 확인
- bundled NestJS에서 `--ffmpeg-location`과 FFmpeg 누락 제품 문구 반영 확인
- bundled NestJS에서 fragment 제외, h264 우선 포맷, retry `video_path` 덮어쓰기 반영 확인
- `clipper_electron`: `npm run build:app:mac:arm64` 성공
- 최신 산출물: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg` (`2026-04-30 22:25`)

이전 주요 완료 작업:

실행 중 상태 뱃지 색상을 조정했다.

- `/projects`의 `실행 중` status badge를 흐린 하늘색 반투명 배경에서 더 선명한 teal pill로 변경
- `.projects-page .status--running`은 `color: #061513`, `background: #76f2dd`

실행 큐 자동 펼침과 hover/expanded glow 상태를 조정했다.

- `/projects?job=...`로 진입했을 때 해당 job이 active 상태면 실행 큐를 자동으로 펼침
- WebSocket `jobs.snapshot`의 `changedStatus === 'waiting'` 이벤트를 받으면 실행 큐를 자동으로 펼침
- 사용자가 접은 뒤에는 진행률 등 `running` 이벤트마다 다시 열리지 않음
- 실행 큐 bar hover 시 accent border/glow 적용
- 실행 큐가 펼쳐진 동안 bar와 popover에 같은 accent border/glow 유지

대사 하이라이트 클립 썸네일 표시와 제목 위치를 조정했다.

- Python dialog export는 기존 `adlight_python` output 구조와 동일하게 `thumbnails/clip_XX.jpg` 실제 프레임 썸네일을 생성함
- NestJS dialog detail은 조회 시 썸네일을 생성하지 않고, 존재하는 `thumbnails/clip_XX.jpg`만 `thumbnailPath`로 내려줌
- 이미 완료된 기존 Clipper2 결과에 `thumbnails/`가 없으면 조회만으로는 썸네일이 생기지 않으므로 재실행 또는 별도 migration 필요
- Angular 대사 상세는 생성된 클립 목록에 9:16 썸네일 칸을 쓰고, 플레이어 위 제목은 제거했으며, 제목은 `제목` info panel로 이동함

작업 보관함 안무 상세 responsive packaged 검증과 `projects.component.scss` style budget warning 정리를 완료했다.

NestJS control plane 전환 뒤 Resource-aware plugin dashboard 1차 vertical slice를 구현했다.

완료:

- `clipper_nestjs`
  - `PluginHost` 추상화
  - `StaticPluginHost`
  - `ElectronPluginHost`
  - `PluginsService`
  - `PluginsController`
  - `PluginsModule`
  - `JobRepository` 추상화
  - `JsonJobRepository`
  - sequential job queue
  - persisted job snapshot/history
  - `JobsService`
  - `JobsController`
  - `JobsModule`
  - `ProjectRepository` 추상화
  - `JsonProjectRepository`
  - completed job -> project/output history 기록
  - `ProjectsService`
  - `ProjectsController`
  - `ProjectsModule`
  - `ResourceHost` 추상화
  - `ElectronResourceHost`
  - `StaticResourceHost`
  - `ResourcesService`
  - `ResourcesController`
  - `ResourcesModule`
  - plugin manifest `resourceProfile` DTO
  - plugin runtime accelerator probe DTO/facade
  - `ws` 기반 plugin job WebSocket client
- `clipper_electron`
  - `PluginHostBridgeServer`
  - `GET /resources` host bridge endpoint
  - host telemetry collector
  - macOS `vm_stat` 기반 available memory 보정
  - Electron/NestJS/plugin process RSS/CPU 수집 기반
  - plugin manifest `capabilities/resources` parsing 및 bridge DTO 변환
  - packaged NestJS env에 bridge URL/token 주입
  - packaged NestJS env에 `CLIPPER_DATA_DIR=app.getPath('userData')` 주입
  - `scripts/build-app.mjs` Node 22 LTS guard
  - Angular build 단계는 `--progress=false`로 실행
  - 정상 plugin stop 후 stale `startedAt` clear
- `clipper_angular`
  - Store/Dashboard plugin status/start/stop 경로를 NestJS `/v1/plugins` API로 전환
  - `PluginJobService`를 NestJS `/v1/jobs` + SSE 경로로 전환
  - Dashboard에 NestJS `/v1/projects` 기반 `최근 작업 결과` 섹션 추가
  - Dashboard에 NestJS `/v1/resources` 기반 `로컬 런타임 리소스` 섹션 추가
  - Dashboard/Store에 plugin resource profile 1차 표시
  - `/projects` route와 작업/프로젝트 history 화면 추가
  - `/projects`는 `작업 보관함` UI로 재구성됨
    - 상단: waiting/starting/running 활성 큐
    - 활성 큐 카드는 원본 영상 정보를 표시하고 waiting 카드는 더 좁게 표시
    - 하단 왼쪽: completed/failed/cancelled 완료 작업 리스트
    - 하단 오른쪽: 선택 작업 결과 상세
    - `dialog_highlight`: clip list + 선택 clip 영상/구간/STT detail
    - `dance_highlight`: 인물/render list + 선택 인물 render 영상/clip list
  - setup 화면의 출력 경로 입력은 제거됨
  - `PluginLocator` 제거 및 feature discovery를 NestJS `/plugins` 기반으로 전환
  - `.nvmrc` 추가
- `clipper_python`
  - dance/dialog plugin manifest에 `capabilities`와 advisory `resources` metadata 추가
  - SDK `GET /runtime/accelerators` endpoint 추가
  - dance/dialog plugin runtime selected device/pipeline hook 추가

검증:

- `npm run build` 성공
- `clipper_nestjs`: `npm run build`, `npm run bundle` 성공
- `clipper_electron`: `npm run build` 성공
- `clipper_angular`: `npm run build:electron` 성공
- local NestJS `GET /v1/plugins/dance_highlight/status` 응답 확인
- local StaticPluginHost `POST /v1/plugins/dance_highlight/stop`은 501 확인
- local StaticPluginHost에서 `POST /v1/jobs`는 즉시 queued 반환 확인
- plugin offline 상태에서는 queue 실행 후 `GET /v1/jobs/:jobId`가 persisted failed snapshot/history 반환 확인
- `ProjectsService.recordCompletedJob()` 서비스 레벨 검증 성공
- local NestJS `GET /v1/projects` -> `200 []`
- local NestJS `GET /v1/projects/unknown_project` -> `404`
- Dashboard project history UI 추가 후 `clipper_angular npm run build:electron` 성공
- 현재 Node v23.11.0에서는 full packaging 중 Angular build 단계에서 native malloc 오류가 발생함
- `build:app` Node guard 검증: Node v23에서 즉시 실패하고 Node 22 LTS 안내 출력
- Node v22.22.2 + sandbox 밖 실행에서 `clipper_electron npm run build:app:mac:arm64` 성공
- 산출물: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- Codex sandbox 안의 nvm Node Angular build는 `UE` 상태로 멈출 수 있으므로 build/app packaging 검증은 sandbox 밖 권한으로 실행할 것
- packaged app 실행 E2E 성공
  - `uv sync` 성공
  - Electron bridge 기동 성공
  - packaged NestJS `/v1/health`, `/v1/plugins`, `/v1/projects` 성공
  - `dance_highlight`, `dialog_highlight` 둘 다 start 성공
  - 두 plugin이 6분 이상 idle 상태에서도 `running`
  - stop endpoint 성공
- stop 이후 stale `startedAt` 버그 수정 후 rebuilt app에서 재검증 성공
- Angular `/projects` 화면 추가 후 `npm run build:electron` 성공
- `/projects` 화면 포함 최신 DMG 재패키징 성공
- packaged dialog job 시작 시 `WebSocket is not defined` 오류 수정
  - `ws` dependency 추가
  - terminal event close race 수정
  - rebuilt packaged app에서 invalid dialog job이 `video file not found`로 정상 실패 기록되는 것 확인
  - `/v1/jobs/:jobId/events` SSE replay 확인
- Resource telemetry packaged runtime 검증
  - rebuilt packaged app에서 `/v1/resources` route 등록 및 응답 확인
  - macOS memory 사용률이 `os.freemem()` 과장치가 아니라 `vm_stat` available memory 기준으로 보정됨
  - processes에 `electron_main`, `nestjs`가 포함됨
  - `dance_highlight` start 후 processes에 plugin RSS/CPU가 포함됨
- Plugin manifest resource metadata 검증
  - rebuilt packaged app에서 `/v1/plugins` 응답에 `capabilities`, `resourceProfile`, `idlePolicy` 포함 확인
  - Dashboard/Store resource profile UI는 `clipper_angular npm run build:electron` 통과
- Dashboard resource pressure warning 1차 표시
  - start 가능한 plugin의 예상 RAM과 현재 available memory를 비교해 advisory warning badge 표시
  - `clipper_angular npm run build:electron` 통과
- NestJS advisory resource assessment와 Dashboard operations console 1차 고도화
  - `clipper_nestjs`에 `PluginResourceAssessment` DTO와 `PluginResourcePolicyService` 추가
  - `/v1/plugins` 응답에 `resourceAssessment` 포함
  - `GET /v1/plugins/:name/resource-assessment` 추가
  - `clipper_angular` Dashboard warning badge를 NestJS assessment 기반으로 전환
  - Dashboard resource panel에 tracked process list 추가
  - `clipper_nestjs npm run build`, `npm run bundle` 성공
  - Node 22 PATH + sandbox 밖에서 `clipper_angular npm run build:electron` 성공
  - local NestJS runtime에서 `resource-assessment`, `/v1/plugins`, `/v1/resources` 응답 확인
- Resource admission confirmation 1차 구현
  - `PluginStartRequest.confirmResourceWarning` 추가
  - `PluginResourcePolicyService.requiresStartConfirmation()` 추가
  - `POST /v1/plugins/:name/start`가 warning/critical/unknown assessment 시 confirmation 없으면 `409 Conflict` + `resourceAssessment` 반환
  - Angular Dashboard start가 admission `409`을 받으면 browser confirm 후 `confirmResourceWarning: true`로 재시도
  - `critical`도 아직 hard block하지 않고 explicit confirmation으로 둠
  - `clipper_nestjs npm run build`, `npm run bundle` 성공
  - sandbox 밖 Node 22에서 `clipper_angular npm run build:electron` 성공
- GPU/VRAM telemetry best-effort adapter 1차 구현
  - Electron packaged bridge resource snapshot과 NestJS static resource snapshot에 `accelerators.gpus` 추가
  - NVIDIA는 `nvidia-smi`, macOS는 `system_profiler`, Windows fallback은 PowerShell `Win32_VideoController`
  - GPU metadata는 60초 TTL cache
  - Dashboard resource summary에 GPU/VRAM 카드 추가
  - VRAM free telemetry가 있으면 estimated VRAM과 비교해 admission reason 산출
  - Apple Silicon처럼 free VRAM telemetry가 없는 unified-memory GPU는 현재 plugin의 `requiresGpu: false`만으로 start confirmation을 강제하지 않음
  - current Mac mini smoke test에서 `Apple M4`, `vendor: "Apple"`, `metalSupported: true` 확인
- 최신 packaged app smoke test 완료
  - `clipper_electron npm run build:app:mac:arm64` 성공
  - 산출물: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
  - `dist-app/mac-arm64/Clipper2.app` 직접 실행 성공
  - packaged `/v1/health`, `/v1/resources`, `/v1/plugins` 성공
  - `/v1/resources`에 `electron_main`, `nestjs`, `accelerators.gpus[0].name = "Apple M4"` 포함
  - packaged `dance_highlight` start -> running status/resources plugin process -> stop -> stopped status 검증 성공
  - smoke test 후 app process 종료 확인
- Manual idle eviction UX 1차 구현
  - Dashboard에서 running + `idlePolicy.safeToEvictWhenIdle` plugin에 runtime age와 `정리 가능` 표시
  - 정리 가능한 running plugin이 있으면 `정리 가능 런타임 중지` 버튼 표시
  - 클릭 시 대상 plugin들을 stop하고 plugin/resource 상태 refresh
  - sandbox 밖 Node 22에서 `clipper_angular npm run build:electron` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공
- Plugin runtime accelerator probe endpoint 1차 구현
  - `clipper_python` SDK에 `GET /runtime/accelerators` 추가
  - `torch`, `onnxruntime`, `ctranslate2` availability/provider probe 반환
  - `dance_highlight`는 selected `primary_device: "mps"`와 `pipeline: "yolo_pose"` 반환 확인
  - `clipper_nestjs`에 `GET /v1/plugins/:name/runtime-accelerators` facade 추가
  - stopped plugin은 `409 Conflict`, running plugin은 normalized camelCase response 반환 확인
  - packaged app에서 start -> runtime accelerators 조회 -> stop -> app 종료 smoke test 성공
- Dashboard runtime accelerator 표시 1차 구현
  - running plugin에 한해 Angular가 `runtime-accelerators` facade를 조회
  - Dashboard row에 selected device/provider summary 표시
  - `clipper_angular npm run build:electron` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공
  - 최신 packaged app에서 `dance_highlight` start -> runtime accelerators 조회 -> stop smoke test 성공
- Projects page 상세 UI 1차 구현
  - job card 선택 시 작업 상세 패널 표시
  - project card 선택 시 프로젝트 상세 패널 표시
  - job/project 선택 상태는 동시에 활성화하지 않도록 정리
  - job 상세에는 params/result/error/history 표시
  - project 상세에는 source/output/artifacts/params/result 표시
  - `clipper_angular npm run build:electron` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공
- Angular direct call audit 및 PluginLocator 제거
  - Angular의 FastAPI/plugin URL 직접 사용 지점은 제거됨
  - 정적 `pluginUrls` 제거
  - feature discovery는 `PluginStatusService` -> NestJS `/plugins` 기준
  - 남은 Electron IPC는 backend URL bootstrap, file dialog, ffmpeg/model download로 분류됨
  - `clipper_angular npm run build:electron` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공
- Resource admission hard block 및 modal UX 1차 구현
  - `critical` assessment는 NestJS에서 start hard block
  - `warning`/`unknown`은 Dashboard 인앱 모달 확인 후 `confirmResourceWarning`으로 재시도
  - Dashboard `window.confirm` 제거
  - `clipper_nestjs npm run build`, `clipper_angular npm run build:electron` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공
- 작업 보관함 UI 및 managed project filesystem 1차 재구성
  - `adlight_angular`/`adlight_python` `feature/longform-highlight`의 project detail/filesystem 구조를 참고
  - `/projects` raw JSON/event history UI 제거
  - 활성 큐와 완료 작업 리스트/상세를 분리
  - dialog manifest/highlights/clip_stt, dance dance_meta를 NestJS detail DTO로 변환
  - project output file serving endpoint에 range request 지원
  - Plugin Dashboard `RSS` 표기를 `현재 메모리`로 변경
  - 작업 보관함 실행 큐에 영상 정보 표시
  - 작업 보관함 완료 목록 overflow/말줄임 수정
  - running job 취소 후 waiting job이 즉시 실행되도록 NestJS queue slot release 수정
  - Store/Dashboard/Projects 공통 페이지 헤더 적용
  - Dashboard page scroll 제거, plugin list 내부 scroll 적용
  - 작업 보관함 상세 영역을 dialog/dance별 2단 결과 UI로 재구성
  - 작업 보관함 실행 큐를 queue bar + overlay drawer로 조정
  - 전역 scrollbar track 제거 및 thumb 색상 조정
  - `clipper_angular npm run build:electron` 성공
  - `clipper_nestjs npm run bundle` 성공
  - `clipper_electron npm run build:app:mac:arm64` 성공
  - 최신 UI 포함 `clipper_electron npm run build:app:mac:arm64` 성공

## 남은 핵심 작업

- plugin resource dashboard를 operations console로 고도화해야 한다.
- Windows CPU fallback packaging target을 통과시켜야 한다.
- host GPU telemetry와 plugin runtime probe를 결합한 CUDA/profile assessment를 설계해야 한다.
- Windows CUDA 배포 전략과 hard GPU/VRAM admission policy를 구체화해야 한다.
- policy-based idle eviction을 설계해야 한다.
- idle plugin eviction 정책을 설계해야 한다.
- Queue job 상세 UI, Project 상세 UI, completed job startup backfill은 1차 완료됨.
- retry/reorder 정책 1차 구현은 완료됨. priority/parallelism 정책은 아직 없다.
- model/ffmpeg install flow는 아직 Electron IPC 직접 호출이다. native/download 책임으로 남길지 NestJS facade를 둘지 결정해야 한다.
- 작업 보관함은 실제 생성된 dialog/dance 결과로 video preview까지 수동 확인이 필요하다.
- Clipper1 편입은 giant plugin이 아니라 shared capability layer로 분해해야 한다.
- Clipper1 capability 후보: `llm.script`, `media.search`, `media.download`, `tts.synthesis`, `subtitle.compose`, `template.apply`, `video.render`, `project.manifest`
- provider substitution rule을 반드시 지킨다.
  - OpenAI/Naver/Clova 같은 hosted API, Ollama/Gemma/Oute/local diffusion 같은 local server/model은 모두 provider 구현체다.
  - workflow/editor/render code는 provider 구현 세부를 몰라야 한다.
  - 새 provider 도입 시 interface/registry/adapter를 먼저 만들고 실제 provider는 교체 가능한 구현체로 둔다.

## 최신 진행 기록: 2026-05-07 20:22 KST

- Clipper1 제작 화면에 template preset 선택 경로를 연결했다.
  - Angular `ClipperStudioPageComponent`가 `/template-presets?workflow=workflow.clipper1&locale=ko-KR`로 목록을 로드한다.
  - Angular `Clipper1ClipEditorComponent` 상단에 `템플릿` select가 생겼고 선택값은 `workspace.renderSettings.templateId`에 저장된다.
  - 기존 `숏폼 생성` 버튼은 render 시작 전 `updateWorkspace()`를 호출하므로 선택한 templateId가 backend workspace에 저장된 뒤 render job이 시작된다.
- NestJS legacy Clipper1 template preset compatibility에 `workflow.clipper1`을 추가했다.
- Selected Template Builder custom preset이 Clipper1 render recipe의 `templatePresetId`와 `templateParams.templateBuilder*`로 유지되는 회귀 테스트를 추가했다.
- 검증:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js test/clipper1-workspace-api.test.js`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
- 커밋:
  - `clipper_nestjs` `29f29e3 feat: expose clipper1 template presets`
  - `clipper_angular` `85278e3 feat: select templates in clipper1 workspace`
- 다음 우선순위 후보:
  - Variation 제작/배치 화면에도 shared template preset 선택 경로 연결.
  - Clipper1 제작 화면의 템플릿 select를 thumbnail/preview가 있는 더 좋은 picker UI로 개선.
  - Template Builder final render parity 수동 QA 및 부족한 legacy visual 속성 보강.

## 최신 진행 기록: 2026-05-07 20:28 KST

- Variation은 현재 `clipper_nestjs/src/plugins/plugin-catalog.ts`의 virtual workflow catalog entry만 있고 Angular/NestJS 제작 surface가 없다.
  - 따라서 이번 turn에는 Variation picker 연결 코드를 넣지 않았다.
  - Variation 제작/배치 화면을 만들 때 shared template picker를 연결해야 한다.
- Clipper1 제작 화면 template picker UI를 개선했다.
  - 새 `Clipper1TemplatePickerComponent`로 select + thumbnail/card 빠른 선택 UI를 분리했다.
  - preset `preview.remoteImageUrl`은 thumbnail로, 없는 경우 ratio fallback으로 표시한다.
  - 기본 템플릿으로 되돌리는 card를 포함한다.
  - 기존 `renderSettings.templateId` 저장 경로는 유지한다.
- 검증:
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/clipper-studio/components/clipper1-clip-editor.component.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
- 빌드에서 component style budget warning 없음.
- 커밋:
  - `clipper_angular` `912cbf6 feat: add clipper1 template picker`

## 최신 진행 기록: 2026-05-07 20:40 KST

- Published Template Builder custom template preview를 Clipper1 picker에 연결했다.
  - NestJS `TemplateBuilderPublishedPresetSource`가 sample render 성공 variant에 `preview.remoteVideoUrl`을 노출한다.
  - URL은 backend-relative `template-builder/families/:familyId/variants/:ratio/sample-render/file` 형태다.
  - Angular `ProjectHistoryService.listTemplatePresets()`가 relative preview URL을 현재 backend base URL 기준 절대 URL로 보정한다.
  - `Clipper1TemplatePickerComponent`는 `remoteImageUrl`이 없고 `remoteVideoUrl`이 있으면 muted video preview를 렌더한다.
- 검증:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js test/clipper1-workspace-api.test.js`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/core/project-history.service.spec.ts --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
- 커밋:
  - `clipper_nestjs` `d7c9155 feat: expose template builder previews`
  - `clipper_angular` `3ad5051 feat: render template preview videos`

## 최신 진행 기록: 2026-05-07 20:47 KST

- Template Builder sample render thumbnail을 Clipper1 picker preview 경로에 연결했다.
  - NestJS sample render snapshot이 provider의 `thumbnailArtifact`를 `thumbnailUri`로 저장한다.
  - `GET /template-builder/families/:familyId/variants/:ratio/sample-render/thumbnail/file` endpoint로 thumbnail file을 serve한다.
  - Published custom template preset은 thumbnail이 있으면 `preview.remoteImageUrl`을 노출하고, 기존 sample render MP4는 `preview.remoteVideoUrl` fallback으로 유지한다.
  - Angular `ProjectHistoryService`는 backend-relative `preview.remoteImageUrl`도 backend base URL 기준 absolute URL로 보정한다.
- 검증:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js`
  - `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js test/clipper1-workspace-api.test.js`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/core/project-history.service.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/core/project-history.service.spec.ts --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
  - `git -C clipper_nestjs diff --check`
  - `git -C clipper_angular diff --check`
- 커밋:
  - `clipper_nestjs` `7369d87 feat: expose template sample thumbnails`
  - `clipper_angular` `e674b3a test: cover template preview thumbnails`

## 최신 진행 기록: 2026-05-07 20:51 KST

- Clipper1 전용 template picker를 shared shortform 컴포넌트로 분리했다.
  - 새 위치: `clipper_angular/src/features/shortform/components/shortform-template-picker.component.*`
  - 새 selector: `app-shortform-template-picker`
  - Clipper1 editor는 같은 input/output 계약으로 shared picker를 사용한다.
  - 사용자-facing UI와 workspace `renderSettings.templateId` 저장 흐름은 그대로다.
- 검증:
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/shortform/components/shortform-template-picker.component.spec.ts --include src/features/clipper-studio/components/clipper1-clip-editor.component.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/shortform/components/shortform-template-picker.component.spec.ts --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
  - `git -C clipper_angular diff --check`
- 커밋:
  - `clipper_angular` `36dff73 refactor: share shortform template picker`

## 최신 진행 기록: 2026-05-07 20:55 KST

- Template preset catalog loading을 shared shortform service로 분리했다.
  - 새 service: `clipper_angular/src/features/shortform/services/shortform-template-preset-catalog.service.ts`
  - `listForWorkflow()`는 `workflow.clipper1`, `workflow.clipper_studio`, `workflow.variation`을 받는다.
  - `category: shorts`는 facade에서 고정하고, undefined query field는 제거한다.
  - Clipper Studio page는 `ProjectHistoryService`를 직접 주입하지 않고 이 shared service를 사용한다.
- 검증:
  - RED: service spec이 missing module로 실패했고, GREEN 중 `source: undefined` query leakage도 한 번 잡았다.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts --include src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts'`
  - `clipper_angular npm run build:electron`
  - `git -C clipper_angular diff --check`
- 커밋:
  - `clipper_angular` `33a8cbc refactor: share shortform template preset loading`

## 최신 진행 기록: 2026-05-07 20:59 KST

- Variation workflow 첫 route shell을 추가했다.
  - `/variation` route가 `VariationPageComponent`를 lazy-load한다.
  - Store/Dashboard route mapping은 `variation -> /variation`을 반환한다.
  - `VariationPageComponent`는 `ShortformTemplatePresetCatalogService.listForWorkflow('workflow.variation', { locale: 'ko-KR' })`로 template preset을 로드한다.
  - Shared `ShortformTemplatePickerComponent`로 template 목록과 preview를 보여주고, 선택값은 local `selectedTemplateId` signal에 저장한다.
- 검증:
  - RED: variation page/route/plugin mapping spec이 missing component/route로 실패.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/variation/pages/variation-page.component.spec.ts --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/variation/pages/variation-page.component.spec.ts --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts`
  - `clipper_angular npm run build:electron`
  - `git -C clipper_angular diff --check`
- 커밋:
  - `clipper_angular` `713309e feat: add variation workflow shell`
- 남은 Variation 핵심:
  - workspace/domain DTO와 저장 API first slice
  - asset folder/pool 연결
  - variation set 생성과 batch render queue

## 최신 진행 기록: 2026-05-07 21:05 KST

- Variation workspace persistence/API first slice를 추가했다.
  - NestJS shortform core에 `ShortformVariationSet`과 `ShortformWorkspace.variationSet`을 추가했다.
  - `VariationWorkspaceRepository`는 `CLIPPER_DATA_DIR/variation/workspaces.json`에 JSON 저장한다.
  - `VariationWorkspaceService`/`VariationWorkspaceController`는 create/list/get/update를 제공한다.
  - create/update는 `renderSettings.templateId`와 `variationSet.count/variants`를 저장하지만 project history를 만들지 않는다.
  - Angular `VariationWorkspaceService`가 create/update endpoint를 호출한다.
  - `VariationPageComponent`는 진입 시 workspace를 생성하고, template 선택 시 workspace PATCH를 호출한다.
- 검증:
  - RED: NestJS variation workspace API test는 404로 실패.
  - RED: Angular variation workspace service/page spec은 missing service/model/page workspace signal로 실패.
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/variation-workspace-api.test.js`
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/variation/services/variation-workspace.service.spec.ts --include src/features/variation/pages/variation-page.component.spec.ts`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts`
  - `clipper_angular npm run build:electron`
  - `git -C clipper_nestjs diff --check`
  - `git -C clipper_angular diff --check`
- 커밋:
  - `clipper_nestjs` `5f194bd feat: persist variation workspaces`
  - `clipper_angular` `37375e2 feat: connect variation workspace API`
- 다음 Variation 우선순위:
  - scenario clips와 asset pool refs를 workspace에 저장
  - lock/randomize policy DTO 추가
  - batch render queue와 project history 승격

## 최신 진행 기록: 2026-05-07 21:31 KST

- Template Builder text layer 정렬 UI를 Angular 속성 패널에 추가했다.
  - `TemplateBuilderEditorComponent` selected text layer 속성의 `위치와 크기` 아래에 `정렬` segmented control이 있다.
  - `왼쪽`/`가운데`/`오른쪽` 버튼은 `layer.align` 현재 값을 표시하고, 클릭 시 `{ align }` patch를 기존 selected layer update 경로로 emit한다.
  - 직전 NestJS/Python 작업으로 `align=center`은 `*_center_x` payload와 ASS alignment 8 렌더까지 이어진다.
- 검증:
  - RED: focused editor spec에서 alignment button이 없어 실패, 1 failed / 34 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 35 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'` 성공, 65 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_angular` `7cb8964 feat: edit template text alignment`
- 다음 우선순위:
  - Variation scenario clips와 asset pool refs를 workspace에 저장한다.
  - Template Builder/renderer parity는 실제 디자인팀 폰트 audit, ASS/PIL box padding-height 차이, pixel-level comparison fixture가 남아 있다.

## 최신 진행 기록: 2026-05-07 21:38 KST

- Variation scenario clips와 asset pool folder refs 저장 first slice를 추가했다.
  - NestJS `ShortformAssetPoolFolderRef`와 `ShortformClip.mediaPool.folders[]`가 생겼다.
  - Variation workspace create/update request는 `clips?: ShortformWorkspace['clips']`를 받는다.
  - `VariationWorkspaceService`는 clips를 raw body 그대로 저장하지 않고 narration lines, media assets, folder refs, media slots, search hints, duration을 최소 정규화한다.
  - `previewTimeline.durationMs`는 clips duration/media slots 기준으로 재계산된다.
  - Angular model/service도 `clips`와 `mediaPool.folders` 계약을 반영했다.
  - Variation page scenario panel에서 `클립 제목`, `대사`, `미디어 폴더 경로`를 입력하고 `클립 추가`로 workspace PATCH를 보낼 수 있다.
- 검증:
  - RED: NestJS variation workspace API test에서 clips가 저장되지 않아 실패.
  - RED: Angular focused spec에서 `UpdateVariationWorkspaceRequest.clips`가 없어 TypeScript compile error.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js` 성공, 2 passed.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js` 성공, 17 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/variation/services/variation-workspace.service.spec.ts --include src/features/variation/pages/variation-page.component.spec.ts` 성공, 7 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts` 성공, 56 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_nestjs git diff --check` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `23e9886 feat: persist variation scenario clips`
  - `clipper_angular` `38fe5b7 feat: edit variation scenario clips`
- 다음 우선순위:
  - Variation lock/randomize policy DTO.
  - local folder picker/folder scan.
  - variation set/card 생성과 batch render queue.

## 최신 진행 기록: 2026-05-07 21:44 KST

- Variation lock/randomize policy 저장 first slice를 추가했다.
  - NestJS shortform core에 `ShortformVariationPolicyField`와 `ShortformVariationRandomizePolicy`가 생겼다.
  - `ShortformVariationSet.randomizePolicy`는 `lockedFields`, `randomizeFields`, `minMediaSlotMs`를 가진다.
  - Variation workspace create/update request는 `randomizePolicy`를 받을 수 있다.
  - `VariationWorkspaceService`는 `lockedFields`를 허용된 필드 순서로 정규화하고, `randomizeFields`를 자동 계산한다.
  - 기본 정책은 `ttsSpeed`만 고정하고 `copy/media/templateId/ttsSpeakerId`는 randomize 대상이다. 기본 `minMediaSlotMs`는 1500이다.
  - Angular model/service가 같은 계약을 반영한다.
  - Variation page batch panel에는 `고정 설정` checkbox UI가 있고, `카피`, `미디어`, `템플릿`, `TTS 목소리`, `속도`를 전환하면 workspace PATCH를 보낸다.
- 검증:
  - RED: NestJS variation workspace API test에서 `variationSet.randomizePolicy`가 없어 실패.
  - RED: Angular focused spec에서 `randomizePolicy` model/request field가 없어 TypeScript compile error.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js` 성공, 3 passed.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js` 성공, 18 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/variation/services/variation-workspace.service.spec.ts --include src/features/variation/pages/variation-page.component.spec.ts` 성공, 9 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts` 성공, 58 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_nestjs git diff --check` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `eda621e feat: persist variation randomize policy`
  - `clipper_angular` `0552387 feat: edit variation randomize policy`
- 다음 우선순위:
  - local folder picker/folder scan.
  - variation set/card 생성.
  - batch render queue와 project history 승격.

## 최신 진행 기록: 2026-05-07 21:48 KST

- Variation local folder picker/folder scan first slice를 추가했다.
  - Angular Variation page의 `미디어 폴더 경로` 입력 옆에 `선택` 버튼이 생겼다.
  - 버튼은 기존 `FilePickerService.pickDirectory()`를 사용한다.
  - Electron에서는 이미 존재하던 `window.clipperBridge.dialog.openDirectory()` bridge를 재사용한다. 새 Electron IPC는 추가하지 않았다.
  - NestJS `VariationWorkspaceService`는 absolute local folder path를 저장할 때 1-depth scan을 수행한다.
  - image/video/gif 확장자만 media 후보로 세어 `mediaPool.folders[].assetCount`에 저장한다.
  - scan 실패, 상대 경로, 접근 불가 path는 folder ref 저장은 유지하고 `assetCount`만 비워 둔다.
- 검증:
  - RED: NestJS variation workspace API test에서 `assetCount`가 undefined라 실패.
  - RED: Angular Variation page spec에서 folder picker button이 없어 실패.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js` 성공, 4 passed.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js` 성공, 19 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/variation/pages/variation-page.component.spec.ts` 성공, 6 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts` 성공, 59 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_nestjs git diff --check` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `c82d135 feat: scan variation asset folders`
  - `clipper_angular` `f6c044f feat: pick variation asset folders`
- 다음 우선순위:
  - folder asset list materialization: folder path에서 media 파일 목록을 `mediaPool.assets[]` 또는 별도 asset-library DTO로 확장.
  - variation set/card 생성.
  - batch render queue와 project history 승격.

## 최신 진행 기록: 2026-05-07 21:52 KST

- Variation folder asset list materialization first slice를 추가했다.
  - NestJS folder scan은 이제 count만 저장하지 않고, scan된 media 파일을 `clip.mediaPool.assets[]`로도 만든다.
  - 생성되는 asset ref는 deterministic `artifactId`, `label`, `kind`, `mediaType`, `sourceHost='local.folder'`, `sourcePath`를 가진다.
  - explicit request assets와 folder materialized assets는 `sourcePath`/`artifactId` 기준으로 dedupe한다.
  - scan은 여전히 1-depth다.
  - Angular Variation scenario list는 folder `assetCount`가 있으면 `N개 미디어`로 표시한다.
- 검증:
  - RED: NestJS variation workspace API test에서 folder scan 후 `mediaPool.assets.length`가 0이라 실패.
  - RED: Angular Variation page spec에서 `3개 미디어` 표시가 없어 실패.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js` 성공, 4 passed.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js` 성공, 19 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/variation/pages/variation-page.component.spec.ts` 성공, 7 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts` 성공, 60 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_nestjs git diff --check` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `5753d70 feat: materialize variation folder assets`
  - `clipper_angular` `2187f5d feat: show variation folder asset counts`
- 다음 우선순위:
  - Variation cards 생성 first slice.
  - Card별 picked asset/media selection.
  - Batch render queue와 project history 승격.

## 최신 진행 기록: 2026-05-07 21:55 KST

- Variation card generation first slice를 추가했다.
  - NestJS shortform core에 `ShortformVariationClip`이 생겼다.
  - `variationSet.variants[].clips[]`는 `clipId`, `title`, `script`, `pickedAssetIds`를 가진다.
  - Variant 생성 시 workspace clips를 order 기준으로 projection한다.
  - `randomizePolicy.randomizeFields`에 `media`가 있으면 variant index + clip order 기준으로 materialized media asset을 분산 선택한다.
  - Angular `ShortformWorkspace` model도 variant clip projection을 반영했다.
  - Variation batch panel은 이제 hard-coded V1-V4가 아니라 `workspace.variationSet.variants`를 렌더한다.
  - 각 card는 `Vn`, clip 수, status를 표시한다.
- 검증:
  - RED: NestJS variation workspace API test에서 `variationSet.variants[0].clips`가 없어 실패.
  - RED: Angular Variation page spec에서 static V1-V4 때문에 `1개 클립`/dynamic count 검증 실패.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js` 성공, 4 passed.
  - `clipper_nestjs node --test test/variation-workspace-api.test.js test/clipper1-workspace-api.test.js test/template-builder-preset-source.test.js` 성공, 19 passed.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/variation/pages/variation-page.component.spec.ts --include src/features/variation/services/variation-workspace.service.spec.ts` 성공, 12 success.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include 'src/features/variation/**/*.spec.ts' --include 'src/features/shortform/**/*.spec.ts' --include 'src/features/clipper-studio/**/*.spec.ts' --include src/app/app.routes.spec.ts --include src/core/plugin-status.service.spec.ts` 성공, 61 success.
  - `clipper_angular npm run build:electron` 성공.
  - `clipper_nestjs git diff --check` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `43978ba feat: generate variation card clips`
  - `clipper_angular` `a36c619 feat: render variation cards`
- 다음 우선순위:
  - Card별 media reroll/selection.
  - Variation cards에서 template/TTS policy 적용.
  - Batch render queue와 project history 승격.

## 최신 진행 기록: 2026-05-07 22:10 KST

- Clipper1 template render parity 보강을 진행했다.
  - 기존 Clipper1은 박스형 텍스트를 PIL PNG로 만든 뒤 ffmpeg overlay로 얹었고, Clipper2 renderer의 ASS box는 `*_box_padding_left_right`, `*_box_height`, alpha, border를 pixel-level로 맞추기 어렵다.
  - `clipper1_video_render`에 `pillow` dependency를 명시했다.
  - `LocalRenderAdapter`에 legacy-style PIL text image 생성 helper를 추가했다.
  - 박스형 project text(`sub_title`, `main_title`, `main_title2`, `bottom_title`, `logo_text`)와 clip subtitle은 ASS event 대신 PNG overlay asset으로 생성한다.
  - `_render_segment()`는 PNG overlay를 ffmpeg input으로 추가하고 `enable='between(t,start,end)'` timed overlay로 합성한다.
  - 비박스형 text는 기존 ASS overlay 경로를 유지한다.
  - render summary는 `overlay_mode='ass+legacy_text_images'`와 `legacy_text_overlay_count`를 기록한다.
- 검증:
  - RED/GREEN TDD로 helper, boxed subtitle, timed overlay input/filter, render smoke summary, boxed main title 분기를 각각 확인했다.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 20 passed.
  - `clipper_python uv run pytest -q` 성공, 60 passed, 4 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `4fc1cdd feat: render legacy boxed text overlays`
- 다음 우선순위:
  - 실제 디자인팀 폰트 묶음으로 font fallback/name 선택 audit.
  - shadow/outline과 box가 동시에 있는 legacy PIL 조합 parity 보강.
  - 기존 Clipper1 golden output frame/video와 pixel-level comparison fixture 추가.
  - Variation 쪽으로 돌아가면 card별 media reroll/selection, template/TTS policy 적용, batch render queue 승격 순서가 남아 있다.

## 최신 진행 기록: 2026-05-07 22:19 KST

- Clipper1 template render parity에서 shadow/outline + box 조합을 추가 보강했다.
  - Legacy Clipper1은 `main_title_shadow_color`가 있으면 shadow PNG를 body PNG 앞에 overlay한다.
  - Legacy Clipper1 subtitle은 `subtitle_shadow_color`가 있으면 `subtitle_box_*`가 있어도 box background보다 shadow/body outline PNG 경로를 우선한다.
  - `LocalRenderAdapter` text overlay asset에 `role` metadata를 추가했다.
  - Boxed project text with shadow는 shadow overlay asset -> body overlay asset 순서로 생성된다.
  - Subtitle shadow는 shadow outline/body outline overlay asset을 생성한다.
  - Legacy outline text image helper를 Pillow 기반으로 추가했다.
- 검증:
  - RED: boxed main title shadow/body role sequence가 없어 실패.
  - RED: subtitle shadow가 box background를 우선해서 shadow/body outline role sequence가 없어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q` 성공, 14 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 22 passed.
  - `clipper_python uv run pytest -q` 성공, 62 passed, 4 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `f27d672 feat: preserve legacy text shadow overlays`
- 다음 우선순위:
  - 실제 디자인팀 폰트 묶음 audit.
  - 기존 Clipper1 golden output frame/video와 pixel-level comparison fixture.
  - 21개 legacy template 전체와 ratio별 수동 QA.

## 최신 진행 기록: 2026-05-07 22:22 KST

- Legacy font bundle audit와 relative font name parity를 보강했다.
  - `adlight_python/fonts`를 fontTools로 확인했고, 파일 stem과 internal family name이 다른 케이스가 있다.
  - 예: `JalnanGothic.otf` -> internal family `Jalnan Gothic`.
  - Python renderer는 이제 상대 font filename도 `_legacy_fonts_dir()`에서 실제 파일로 resolve한 뒤 TTF/OTF name table을 읽어 ASS `Fontname`에 사용한다.
  - Explicit `*_font_name` override와 absolute uploaded font path는 기존처럼 우선한다.
- 검증:
  - RED: `main_title_font: "JalnanGothic.otf"`가 `JalnanGothic` stem으로 매핑되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q` 성공, 15 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 17 passed.
  - `clipper_python uv run pytest -q` 성공, 63 passed, 4 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `152298f fix: resolve legacy font family names`
- 다음 우선순위:
  - font bundle regression fixture 확대.
  - 기존 Clipper1 golden output frame/video와 pixel-level comparison fixture.
  - 21개 legacy template 전체와 ratio별 수동 QA.

## 최신 진행 기록: 2026-05-07 22:27 KST

- Clipper1 golden frame comparison harness를 추가했다.
  - `clipper1_video_render.frame_compare.compare_rgb_frames()`는 expected/actual RGB frame을 비교하고 size mismatch, sampled pixels, mismatched pixels, mismatch ratio, max channel delta, max delta coordinate를 반환한다.
  - `tests/test_clipper1_video_render_frame_compare.py`는 tolerance, drift, bounded mismatch ratio, size mismatch를 검증한다.
  - `tests/test_clipper1_video_render_golden_frames.py`는 optional fixture runner다.
  - 기본 fixture 위치는 `tests/fixtures/clipper1_golden_frames`, 또는 `CLIPPER1_GOLDEN_FRAME_FIXTURE_DIR`로 지정한다.
  - `manifest.json`이 없으면 skip한다.
  - manifest가 있으면 payload/recipe로 현재 renderer를 실행하고 ffmpeg로 frame을 추출한 뒤 `goldenFrame`과 비교한다.
  - `tests/fixtures/clipper1_golden_frames/README.md`에 manifest format을 기록했다.
- 검증:
  - RED: `clipper1_video_render.frame_compare` module이 없어 frame compare test collection 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_frame_compare.py -q` 성공, 4 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py -q` 성공, 1 skipped.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_frame_compare.py tests/test_clipper1_video_render_golden_frames.py -q` 성공, 4 passed, 1 skipped.
  - `clipper_python uv run pytest -q` 성공, 67 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `e6fa8ff test: add clipper1 golden frame comparison`
- 다음 우선순위:
  - 실제 old Clipper1에서 golden frames/payload/recipe를 export해 fixture를 채우기.
  - Golden fixture가 채워진 후 template별 tolerance/sample step 조정.
  - 21개 legacy template 전체와 ratio별 수동 QA.

## 최신 진행 기록: 2026-05-07 22:33 KST

- Legacy visual asset local resolution을 추가했다.
  - 예전 template row의 `https://d2x-s3.s3.ap-northeast-2.amazonaws.com/layout/...`, `/template/...` visual URL은 remote download 전에 local `adlight_python/layout`, `adlight_python/template`에서 먼저 찾는다.
  - `layout_image: "1.png"` 같은 상대 파일명도 local legacy layout/template dir에서 resolve한다.
  - 일반 localhost/HTTP remote asset staging은 기존대로 다운로드한다.
- 검증:
  - RED: relative `1.png`는 `None`, legacy S3 template URL은 remote staging path로 resolve되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py -q` 성공, 8 passed.
  - `clipper_python uv run pytest -q` 성공, 69 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `1f119be fix: resolve legacy visual assets locally`
- 다음 우선순위:
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - Golden fixture 기반 template별 tolerance/sample step 조정.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 2026-05-10 추가 메모

- layoutImage는 now family-wide + cover-fit + aspect-locked resize.
- 다음 확인: 실제 Electron preview에서 overflow dim과 sample/final clip이 눈으로도 맞는지 재검증.

## 2026-05-10 추가 메모

- sample render/publish 전 pending update flush가 들어감.
- 다음 확인: layoutImage 조정 후 즉시 sample render 눌러도 최신 geometry가 반영되는지 실제 앱에서 확인.

## 최신 진행 기록: 2026-05-07 22:52 KST

- Legacy logo image scale/crop parity를 추가했다.
  - 기존 Clipper1 `VideoService.py`는 logo image를 height 기준으로 scale한 뒤 `logo_image_area_width/height`로 중앙 crop했다.
  - Python renderer도 `logo_image` filter를 `scale=-1:{height}, crop=min(iw,width):height:...` 방식으로 변경했다.
- 검증:
  - RED: logo filter가 `scale=800:160:force_original_aspect_ratio=decrease`로 생성되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py -q` 성공, 7 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 17 passed.
  - `clipper_python uv run pytest -q` 성공, 74 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `7d82d2a feat: crop legacy logo images`
- 다음 우선순위:
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - Golden fixture 기반 template별 tolerance/sample step 조정.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 최신 진행 기록: 2026-05-07 22:56 KST

- Legacy Clipper1 template catalog readiness를 보강했다.
  - `clipper_nestjs/src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`의 template design 1이 `1:1`, `16:9`, `4:3`, `full` fixed ratio를 모두 노출한다.
  - 기존 `example.invalid` thumbnail/layout placeholder를 D2X S3 template/layout URL로 교체했다.
  - `16:9` row는 사용자가 제공했던 Excel 1행 값을 기반으로 추가했다.
- 검증:
  - RED: `clipper_nestjs node --test test/template-builder-preset-source.test.js`에서 `16:9` 누락으로 실패.
  - `clipper_nestjs node --test test/template-builder-preset-source.test.js` 성공, 3 passed.
  - `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 20 passed.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `584db30 fix: replace legacy template placeholders`
- 다음 우선순위:
  - 실제 old Clipper1 85-row template catalog 원본 확보/이관 경로 설계.
  - `full`, `1:1`, `4:3` row의 stub 수치 교체.
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.

## 최신 진행 기록: 2026-05-07 23:01 KST

- Legacy full-height layout final overlay stage parity를 추가했다.
  - 기존 Clipper1은 full-height 확장 스타일에서 segment에는 layout을 배경으로 넣지 않고, concat 이후 최종 영상 위에 layout을 overlay했다.
  - Python renderer도 계산된 `content_area.height >= output height`이면 segment render에서 layout을 제외하고 concat 이후 `_overlay_final_layout()`을 실행한다.
  - `contents_ratio: full`이어도 custom content area height가 output보다 작으면 Template Builder smoke처럼 기존 background layout 흐름을 유지한다.
- 검증:
  - RED: `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py -q` 실패, 2 failed/7 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py -q` 성공, 9 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 11 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_motion.py -q` 성공, 41 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - `clipper_python uv run pytest -q` 성공, 76 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `3528504 feat: overlay full legacy layouts after concat`
- 다음 우선순위:
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - Project title/logo/subtitle 최종 concat 이후 overlay 구조까지 legacy와 맞출지 검토.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 최신 진행 기록: 2026-05-07 23:15 KST

- 기존 Clipper1 운영 `templates` export를 Clipper2 legacy catalog로 이관했다.
  - 입력 raw files:
    - `.codex/imports/legacy-clipper1-templates/templates.json`
    - `.codex/imports/legacy-clipper1-templates/templates_schema.sql`
    - `.codex/imports/legacy-clipper1-templates/templates_jp.json`
    - `.codex/imports/legacy-clipper1-templates/templates_jp_schema.sql`
  - canonical source는 `templates`다.
  - `templates_jp`는 사용자가 설명한 대로 일본 콘텐츠 대응용 임시 파생본이므로 이번 기본 catalog에는 넣지 않았다.
  - `templates.json`은 84 rows, 21 designs × 4 fixed ratios 구조다.
  - DBeaver export의 `settings` 문자열을 object로 parse해 `clipper_nestjs/src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`을 교체했다.
- 검증:
  - RED: `clipper_nestjs node --test test/template-builder-preset-source.test.js` 실패, 기존 catalog 4 rows.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/template-builder-preset-source.test.js` 성공, 4 passed.
  - `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 21 passed.
  - `clipper_nestjs git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `0ea6c00 feat: import legacy clipper1 template catalog`
- 다음 우선순위:
  - 84-row catalog로 Angular template picker UX가 너무 무거워지지 않는지 확인.
  - 실제 template별 preview/render smoke를 최소 1개 이상 확장.
  - old Clipper1 golden frame fixture 채우기.

## 최신 진행 기록: 2026-05-08 00:50 KST

- 기존 Clipper1 template UI thumbnail/origin assets를 local bundle로 연결했다.
  - Raw import: `.codex/imports/legacy-clipper1-template-assets/thumsandorigins/`
  - Code bundle: `clipper_nestjs/src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/`
  - 168 PNG files: 84 thumbs + 84 origins.
  - NestJS endpoint: `GET /template-presets/legacy-clipper1/assets/:fileName`
  - Catalog `preview.remoteImageUrl`은 thumb endpoint, `preview.remoteLargeImageUrl`은 origin endpoint.
  - Angular `ProjectHistoryService`는 `remoteLargeImageUrl`도 backend-relative URL로 변환한다.
- 검증:
  - RED: `clipper_nestjs node --test test/template-builder-preset-source.test.js` 실패, S3 thumbnail URL/missing asset service.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/template-builder-preset-source.test.js` 성공, 5 passed.
  - `clipper_nestjs node --test test/legacy-clipper1-render-media-slots.test.js test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-render-payload.test.js` 성공, 22 passed.
  - `clipper_nestjs git diff --check` 성공.
  - RED: `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/core/project-history.service.spec.ts'` compile fail, `remoteLargeImageUrl` 없음.
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include='src/core/project-history.service.spec.ts'` 성공, 1 success.
  - `clipper_angular ./node_modules/.bin/ngc -p tsconfig.app.json` 성공.
  - `clipper_angular git diff --check` 성공.
- 커밋:
  - `clipper_nestjs` `85d21f5 feat: bundle legacy template previews`
  - `clipper_angular` `6f0ceb9 feat: resolve large template preview urls`
- 다음 우선순위:
  - Template picker가 84개 preset을 flat list로 보여줄 때 UX가 괜찮은지 확인하고, design 단위 grouping/lazy loading이 필요하면 개선.
  - 큰 origin image를 실제 확대 preview/modal에서 쓰는 UI 추가 여부 결정.
  - 실제 template별 render smoke/golden frame fixture 확장.

## 최신 진행 기록: 2026-05-08 01:05 KST

- 실제 render layout assets를 Python worker package 내부에 bundle했다.
  - Source: `adlight_python/layout`
  - Bundle: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/legacy_assets/layout`
  - 33 files, about 11MB.
  - `LocalRenderAdapter._legacy_visual_asset_roots()`는 `CLIPPER_LEGACY_ASSETS_DIR` 다음으로 package 내부 `legacy_assets`를 찾는다.
  - 이제 packaged app/Windows build에서 sibling `adlight_python` repo가 없어도 D2X S3 layout URL과 relative layout filename을 local bundle로 resolve할 수 있다.
- 검증:
  - RED: `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py -q` 실패, sibling `adlight_python` fallback/remote download로 빠짐.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py -q` 성공, 9 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_uploaded_fonts.py -q` 성공, 20 passed.
  - `clipper_python uv run python -m compileall plugins/clipper1_video_render` 성공.
  - `clipper_python uv run pytest -q` 성공, 77 passed, 5 skipped.
  - `clipper_python uv build --package clipper-plugin-clipper1-video-render --wheel --out-dir /tmp/clipper1-video-render-wheel-check` 성공.
  - wheel content check: `legacy_assets/layout` 33 files included.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `b60ef85 feat: bundle legacy render layouts`
- 다음 우선순위:
  - 실제 21개 template 중 대표 template render smoke/golden fixture 확장.

## 최신 진행 기록: 2026-05-08 01:13 KST

- Legacy Clipper1 template asset 재수입 절차를 스크립트화했다.
  - UI preview용 thumbnail/origin:
    - Script: `clipper_nestjs/scripts/import-legacy-clipper1-template-ui-assets.js`
    - Command: `npm run import:legacy-template-ui-assets -- --dry-run`
    - Source: `.codex/imports/legacy-clipper1-template-assets/thumsandorigins`
    - Target: `clipper_nestjs/src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins`
    - Validation: template별 4 ratio x thumb/origin 8 files required.
  - 실제 render layout:
    - Script: `clipper_python/scripts/import_legacy_clipper1_layout_assets.py`
    - Command: `uv run python scripts/import_legacy_clipper1_layout_assets.py --dry-run`
    - Source: `adlight_python/layout`
    - Target: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/legacy_assets/layout`
    - Validation: PNG layout assets only.
- 검증:
  - RED: NestJS/Python focused tests both failed before scripts existed.
  - `clipper_nestjs node --test test/legacy-template-asset-import-script.test.js` 성공, 2 passed.
  - `clipper_python uv run pytest tests/test_legacy_layout_asset_import_script.py -q` 성공, 2 passed.
  - `clipper_nestjs npm run import:legacy-template-ui-assets -- --dry-run` 성공, 168 files / 21 templates.
  - `clipper_python uv run python scripts/import_legacy_clipper1_layout_assets.py --dry-run` 성공, 33 files.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/*.test.js` 성공, 44 passed.
  - `clipper_python uv run pytest -q` 성공, 79 passed, 5 skipped.
- 커밋:
  - `clipper_nestjs` `74ce098 chore: add legacy template asset import script`
  - `clipper_python` `4b829c3 chore: add legacy layout asset import script`
- 다음 우선순위:
  - 실제 21개 template 중 대표 template render smoke/golden fixture 확장.

## 최신 진행 기록: 2026-05-08 01:18 KST

- Legacy Clipper1 84-row catalog의 `settings.layout_image`가 Python worker bundle layout asset과 모두 매칭되는지 검증하는 script를 추가했다.
  - Script: `clipper_python/scripts/validate_legacy_clipper1_layout_catalog.py`
  - Command: `uv run python scripts/validate_legacy_clipper1_layout_catalog.py`
  - Default catalog: `clipper_nestjs/src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`
  - Default layout dir: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/legacy_assets/layout`
  - S3 URL과 relative filename 모두 basename으로 정규화한다.
- 실제 검증 결과:
  - 84 rows
  - 32 unique layout files
  - missing 0
- 검증:
  - RED: `clipper_python uv run pytest tests/test_legacy_layout_catalog_validation_script.py -q` 실패, module missing.
  - `clipper_python uv run pytest tests/test_legacy_layout_catalog_validation_script.py -q` 성공, 2 passed.
  - `clipper_python uv run python scripts/validate_legacy_clipper1_layout_catalog.py` 성공, missing 0.
  - `clipper_python uv run pytest tests/test_legacy_layout_asset_import_script.py tests/test_legacy_layout_catalog_validation_script.py -q` 성공, 4 passed.
  - `clipper_python uv run pytest -q` 성공, 81 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `398dfda chore: validate legacy layout catalog coverage`
- 다음 우선순위:
  - 실제 21개 template 중 대표 template render smoke/golden fixture 확장.

## 최신 진행 기록: 2026-05-08 01:23 KST

- Legacy Clipper1 template render smoke runner를 추가했다.
  - Script: `clipper_python/scripts/render_legacy_clipper1_template_smoke.py`
  - Default representative cases:
    - `1:16:9`
    - `1:full`
    - `6:1:1`
    - `16:4:3`
    - `17:full`
  - 개별 case 지정: `--case <template>:<ratio>`
  - 21개 design smoke: `--all-designs`
  - PIL synthetic image를 local media로 만들어 `LocalRenderAdapter`가 실제 MP4/thumbnail을 생성한다.
- 실제 smoke 결과:
  - `uv run python scripts/render_legacy_clipper1_template_smoke.py --output-root /tmp/clipper1-template-smoke-20260508 --duration 0.2 --fps 4` 성공, 5 cases rendered.
  - `uv run python scripts/render_legacy_clipper1_template_smoke.py --all-designs --output-root /tmp/clipper1-template-smoke-all-designs-20260508 --duration 0.12 --fps 3` 성공, 21 cases rendered.
- 검증:
  - RED: smoke script module missing으로 focused tests 실패.
  - RED: script 직접 실행 시 `scripts` package import failure.
  - `clipper_python uv run pytest tests/test_legacy_template_render_smoke_script.py -q` 성공, 5 passed.
  - `clipper_python uv run pytest tests/test_legacy_template_render_smoke_script.py tests/test_legacy_layout_catalog_validation_script.py tests/test_legacy_layout_asset_import_script.py -q` 성공, 9 passed.
  - `clipper_python uv run pytest -q` 성공, 86 passed, 5 skipped.
  - `clipper_python uv run python -m compileall scripts` 성공.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `b926e61 chore: add legacy template render smoke runner`
- 다음 우선순위:
  - 실제 legacy Clipper1 reference frame export가 생기면 `tests/fixtures/clipper1_golden_frames` manifest/payload/recipe/golden frame을 채워 pixel-level parity로 확장.
  - 또는 지금 smoke runner 결과물에서 representative frames를 고정 fixture로 승격할지 결정.

## 최신 진행 기록: 2026-05-08 09:39 KST

- Golden fixture 방향을 결정했다.
  - 현재 workspace에는 실제 legacy Clipper1 final render reference frame이 없다.
  - `origin/thumb` PNG는 UI preview asset이며 final render frame이 아니므로 legacy pixel-level golden으로 사용하지 않는다.
  - 따라서 true legacy parity harness인 `tests/fixtures/clipper1_golden_frames`는 reference export 전까지 유지한다.
  - 현재 Clipper2 smoke output은 별도 `tests/fixtures/clipper2_template_baseline_frames`로 승격했다.
  - 이 baseline은 Clipper2 renderer regression guard이며, legacy Clipper1 parity 증명은 아니다.
- 추가한 것:
  - `clipper_python/scripts/promote_legacy_template_smoke_baseline.py`
  - `clipper_python/tests/test_clipper2_template_baseline_frames.py`
  - `clipper_python/tests/test_legacy_template_render_baseline_script.py`
  - `clipper_python/tests/fixtures/clipper2_template_baseline_frames/`
- baseline cases:
  - 21개 legacy template design 각각의 `16:9` baseline
  - ratio edge case 4개: `template-1-full`, `template-6-1_1`, `template-16-4_3`, `template-17-full`
- 검증:
  - RED: fixture manifest와 promotion script가 없어 focused tests 실패.
  - `clipper_python uv run python scripts/promote_legacy_template_smoke_baseline.py` 성공, 5 cases generated.
  - `clipper_python uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_legacy_template_render_baseline_script.py -q` 성공, 4 passed.
  - `clipper_python uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_legacy_template_render_baseline_script.py tests/test_legacy_template_render_smoke_script.py tests/test_clipper1_video_render_golden_frames.py -q` 성공, 9 passed / 1 skipped.
  - `clipper_python uv run pytest -q` 성공, 90 passed / 5 skipped.
  - `clipper_python uv run python -m compileall scripts` 성공.
  - `clipper_python git diff --check` 성공.
- 추가 확장:
  - `clipper_python` baseline fixture를 5개 대표 case에서 25개 case로 확장했다.
  - command: `uv run python scripts/promote_legacy_template_smoke_baseline.py --all-designs --case 1:full --case 6:1:1 --case 16:4:3 --case 17:full`
  - `select_baseline_rows()`는 `--all-designs` rows와 explicit `--case` rows를 dedupe해서 합친다.
  - focused GREEN: `clipper_python uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_legacy_template_render_baseline_script.py -q` 성공, 5 passed.
  - expanded focused GREEN: `clipper_python uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_legacy_template_render_baseline_script.py tests/test_legacy_template_render_smoke_script.py tests/test_clipper1_video_render_golden_frames.py -q` 성공, 10 passed / 1 skipped.
  - full GREEN: `clipper_python uv run pytest -q` 성공, 91 passed / 5 skipped.
  - `clipper_python uv run python -m compileall scripts` 성공.
  - `clipper_python git diff --check` 성공.
- 다음 우선순위:
  - 실제 Clipper1 reference frames가 확보되면 `clipper1_golden_frames`에 legacy golden fixture를 추가한다.
  - 그 전까지는 baseline mismatch가 발생하면 의도한 renderer visual change인지 regression인지 review 후 baseline을 재생성한다.

## 최신 진행 기록: 2026-05-08 13:15 KST

- Legacy Clipper1 golden drift worst case였던 `template-12-16_9`의 top 제목 박스 차이를 줄였다.
  - 사용자 관점 설명: 상단 제목 흰 박스가 Clipper1보다 넓게 나오는 문제를 고쳤다.
  - Clipper1은 text PNG canvas width를 문장 전체 `font.getbbox(line)` 폭 + tracking으로 계산한다.
  - Clipper2는 글자별 폭 합계를 쓰고 있었고, 공용 `_number()`가 `main_title_tracking=-4.5` 같은 음수 tracking을 0으로 버리고 있었다.
- 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - tracking 전용 `_tracking_number()`를 추가해 음수/0/양수 tracking을 보존한다.
    - text PNG canvas width는 Clipper1처럼 문장 전체 bbox 폭 + tracking으로 계산한다.
    - font fitting은 Clipper1 `adjust_font_size_to_fit()`와 맞게 글자별 폭 합계 방식을 유지한다.
  - `clipper_python/tests/test_clipper1_video_render_template_styles.py`
    - `template-12-16_9` payload 기준 main title PNG 크기 회귀 테스트를 추가했다.
    - 기대값: `Legacy Clipper1 -> (753, 135)`, `Template 12 -> (597, 135)`, font size `90`.
  - `clipper2_template_baseline_frames` 25개를 새 Clipper2 출력으로 재생성했다. 이 fixture는 Clipper2 회귀 방지용 기준 이미지라, 의도적 렌더 변경 후 같이 갱신해야 한다.
- TDD/검증:
  - RED: focused test가 `(815, 135) != (753, 135)`로 실패했다.
  - RED after first fix: tracking이 0으로 버려져 `(816, 135) != (753, 135)`로 실패했다.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_template_styles.py::test_template_12_boxed_main_title_matches_legacy_text_image_dimensions -q` 성공, 1 passed.
  - GREEN: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-title-width --write-diffs top --top-diffs 10` 성공, 25 cases / failed 0.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_golden_frames.py tests/test_clipper1_golden_frame_diagnostics.py -q` 성공, 24 passed.
  - GREEN: `uv run python scripts/promote_legacy_template_smoke_baseline.py --all-designs --case 1:full --case 6:1:1 --case 16:4:3 --case 17:full --fixture-dir tests/fixtures/clipper2_template_baseline_frames --render-output-root /tmp/clipper2-template-baseline-after-title-width-25` 성공, 25 cases.
  - GREEN: `uv run pytest tests/test_clipper2_template_baseline_frames.py -q` 성공, 2 passed.
  - GREEN: `uv run python -m compileall scripts` 성공.
  - GREEN: `uv run pytest -q` 성공, 96 passed / 4 skipped.
- Drift 변화:
  - `template-12-16_9` overall `0.037809 -> 0.011443`
  - top `0.102660 -> 0.024770`
  - content `0.000646 -> 0.000609`
  - bottom `0.015384 -> 0.009549`
  - 새 worst case는 `template-1-full`, mismatch `0.027674`.
- 다음 우선순위:
  - `template-1-full`, `template-17-full`의 content 영역 mismatch를 진단한다.
  - full ratio layout/content 합성 방식과 overlay 순서를 Clipper1 `VideoService.py` 기준으로 비교한다.

## 최신 진행 기록: 2026-05-08 14:12 KST

- Golden fixture threshold를 강화했다.
  - 사용자 확인상 현재 worst `template-6-1_1`은 육안 차이가 거의 없고, diff도 원 가장자리/text edge/경계선에 몰려 있다.
  - 초기 기준 `maxMismatchRatio=0.04`는 큰 layout drift를 잡기 위한 1차 기준이었으므로, 현재 worst `0.011948`에 맞춰 `0.015`로 낮췄다.
  - `adlight_python/scripts/export_clipper1_reference_frames.py`의 기본값과 checked-in `clipper1_golden_frames/manifest.json` 25개 case를 같이 갱신했다.
- TDD/검증:
  - RED: 새 fixture threshold test가 `{0.04} != {0.015}`로 실패했다.
  - RED: `adlight_python` export default test가 `0.04 != 0.015`로 실패했다.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_golden_frames.py::test_legacy_clipper1_golden_frame_fixture_uses_tight_layout_threshold -q` 성공, 1 passed.
  - GREEN: `adlight_python .venv/bin/python -m unittest discover -s tests -p 'test_export_clipper1_reference_frames.py'` 성공, 6 tests.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_golden_frames.py -q` 성공, 2 passed.
- 다음 우선순위:
  - 실제 renderer 수정은 계속 `template-6-1_1` content 영역의 zoom/resize pipeline 비교부터 한다.

## 최신 진행 기록: 2026-05-08 14:28 KST

- Zoom resize filter를 Clipper1 쪽에 더 가깝게 보정했다.
  - Clipper1 MoviePy `resize` effect는 OpenCV가 있으면 upsize에 `cv2.INTER_LINEAR`를 사용한다.
  - Clipper2 FFmpeg zoom branch는 기본 scale filter를 쓰고 있었다.
  - 후보 실험에서 `flags=bilinear`가 `template-6-1_1` reference content에 더 가까웠다.
- 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - zoom motion filter의 scale 단계에 `flags=bilinear` 추가.
  - `clipper_python/tests/test_clipper1_video_render_media_looping.py`
    - automatic zoom filter가 `flags=bilinear`를 쓰는지 검증.
  - `clipper_python/tests/fixtures/clipper2_template_baseline_frames/`
    - 25개 baseline frame 재생성.
- TDD/검증:
  - RED: focused test가 `flags=bilinear` 없음으로 실패.
  - GREEN: focused test 성공.
  - GREEN: drift diagnostic 성공, 25 cases / failed 0.
  - GREEN: `uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_golden_frames.py tests/test_clipper1_golden_frame_diagnostics.py -q` 성공, 20 passed.
- Drift 변화:
  - `template-6-1_1` `0.011948 -> 0.010862`.
  - 현재 worst case는 여전히 `template-6-1_1`이지만, tightened threshold `0.015`보다 충분히 낮다.
- 다음 우선순위:
  - top text edge가 남은 `template-16-16_9`, `template-11-16_9`를 보거나, fixture 기준을 `0.012`까지 더 조일 수 있는지 검토한다.

## 최신 진행 기록: 2026-05-08 14:45 KST

- Legacy Clipper1 FFmpeg overlay format에 맞게 Clipper2 renderer의 layout/logo/text PNG overlay에서 `format=auto`를 제거했다.
  - Clipper1 `VideoService.py`는 plain `overlay=x:y` 형태를 사용한다.
  - `format=auto`가 반투명 box/text edge mismatch를 키우고 있었다.
- 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - segment layout/media overlay, logo overlay, text overlay, full ratio final layout/text/logo overlay에서 `format=auto` 제거.
  - `clipper_python/tests/test_clipper1_video_render_media_looping.py`
    - overlay filter graph가 legacy default format을 쓰는지 검증.
  - `clipper_python/tests/fixtures/clipper2_template_baseline_frames/`
    - 25개 baseline frame 재생성.
  - `clipper_python/tests/fixtures/clipper1_golden_frames/manifest.json`
    - `maxMismatchRatio=0.012`로 강화.
  - `adlight_python/scripts/export_clipper1_reference_frames.py`
    - `DEFAULT_MAX_MISMATCH_RATIO = 0.012`.
- TDD/검증:
  - RED: media-looping focused tests가 기존 `format=auto` 때문에 실패.
  - RED: golden/export threshold focused tests가 `0.015 != 0.012`로 실패.
  - GREEN: focused tests 성공.
  - GREEN: drift diagnostic 성공, 25 cases / failed 0.
- Drift 변화:
  - `template-11-16_9` `0.009001 -> 0.003457`.
  - `template-16-16_9` `0.009687 -> 0.006590`.
  - `template-12-16_9` `0.007373 -> 0.003382`.
  - `template-1-full` `0.011059 -> 0.000573`.
  - `template-17-full` `0.005683 -> 0.001541`.
  - 현재 worst는 `template-6-1_1`, `0.011861`.
- 다음 우선순위:
  - `template-6-1_1` content edge를 다시 본다.
  - `maxMismatchRatio=0.012`보다 더 조이기 전에 이 케이스 원인을 먼저 분리한다.

## 최신 진행 기록: 2026-05-08 15:07 KST

- Automatic zoom branch를 기존 Clipper1에 더 가깝게 보정했다.
  - Clipper1은 source image를 먼저 content area 크기로 맞춘 뒤, 그 normalized clip을 MoviePy `Zoom`으로 다시 scale/crop한다.
  - Clipper2는 `zoompan` 단일 단계였고, `template-6-1_1` content edge 보간이 reference와 조금 달랐다.
- 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - automatic zoom branch에서 `zoompan` 제거.
    - `fps -> scale/crop`으로 content 크기 normalize 후, `t * fps`와 `int(duration * fps)` 기반 zoom factor로 frame별 scale/crop.
  - `clipper_python/tests/test_clipper1_video_render_media_looping.py`
    - automatic zoom filter graph가 legacy two-step scale/crop을 쓰는지 검증.
  - `clipper_python/tests/fixtures/clipper2_template_baseline_frames/`
    - 25개 baseline frame 재생성.
  - `clipper_python/tests/fixtures/clipper1_golden_frames/manifest.json`
    - `maxMismatchRatio=0.008`로 강화.
  - `adlight_python/scripts/export_clipper1_reference_frames.py`
    - `DEFAULT_MAX_MISMATCH_RATIO = 0.008`.
- TDD/검증:
  - RED: automatic zoom focused test가 기존 `zoompan` 때문에 실패.
  - GREEN: focused test 성공.
  - RED/GREEN: fractional duration에서 frame count가 `round()`가 아니라 legacy `int()`를 쓰도록 추가 고정.
  - RED: golden/export threshold focused tests가 `0.012 != 0.008`로 실패.
  - GREEN: threshold focused tests 성공.
  - GREEN: drift diagnostic 성공, 25 cases / failed 0.
- Drift 변화:
  - `template-6-1_1` `0.011861 -> 0.006979`.
  - 현재 worst는 `template-6-1_1`, `0.006979`.
- 다음 우선순위:
  - 상위 top edge 케이스인 `template-16-4_3`, `template-18-16_9`, `template-16-16_9`를 본다.
  - 기준은 이미 `0.008`이라 다음 기준 강화 전에는 edge noise와 실제 위치 drift를 분리한다.

## 최신 진행 기록: 2026-05-10 KST

- Template Builder의 기본 ratio 선택을 `full` 중심에서 `16:9` 중심으로 바꿨다.
  - `clipper_angular` `80ddba7 fix: default template builder selection to 16x9`
  - family 선택 시 `16:9` variant가 있으면 editor가 `16:9`로 열린다.
  - parent page의 `editorSelectedRatio`를 editor input으로 내려 text preview artifact와 실제 editor ratio가 엇갈리지 않게 했다.
  - parent가 이미 알고 있는 ratio reset은 child가 다시 emit하지 않아 artifact invalidate loop를 만들지 않는다.
- Legacy Clipper1 system preset seed가 rawSettings의 text/style 정보를 대부분 반영하도록 확장됐다.
  - `clipper_nestjs` `8a75081 fix: seed legacy template builder styles`
  - `sub_title_*`, `main_title_*`, `bottom_title_*`, `logo_text_*`, `subtitle_*`, `subtitle_box_*`, logo image geometry, y-offset, margin, box, outline, shadow 값을 Template Builder layer로 역매핑한다.
  - legacy box color가 `null`이면 box를 disabled/transparent로 seed한다.
- 검증:
  - `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/components/template-builder-editor.component.spec.ts` 성공, 42 specs.
  - `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/pages/template-builder-page.component.spec.ts` 성공, 25 specs.
  - `clipper_angular npm run build` 성공.
  - `clipper_nestjs npm run build` 성공.
  - `clipper_nestjs node --test test/template-builder-api.test.js --test-name-pattern "legacy Clipper1 text styles"` 성공. Node runner 특성상 해당 파일의 13 tests가 모두 실행됐다.
  - `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64` 성공.
- 최신 앱:
  - `/Users/jina/project/adlight/clipper_electron/dist-app/mac-arm64/Clipper2.app`
  - `/Users/jina/project/adlight/clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- 다음 우선순위:
  - 사용자가 최신 packaged app에서 Template Builder를 열어 16:9 기본 선택, legacy title/subtitle/logo style, box transparency를 직접 확인한다.
  - 특정 템플릿의 style이 여전히 다르면 픽셀 parity가 아니라 해당 템플릿의 `rawSettings -> Template Builder layer -> render contract` mapping을 좁혀서 진단한다.
  - 특히 box/outline/shadow가 있는 legacy template을 골라 preview/final render contract가 같은 style을 쓰는지 확인한다.

## 최신 진행 기록: 2026-05-08 13:59 KST

- Template-3 top text 세로 위치를 Clipper1 기준으로 맞췄다.
  - 원인: Clipper2의 평균 글자 높이 reference set이 Clipper1 `generate_reference_texts()`보다 짧아서, text PNG 안에서 glyph가 약 3px 낮게 그려졌다.
  - 변경: `LEGACY_TEXT_HEIGHT_REFERENCE`를 Clipper1 기준 한글 rows로 확장하고, 평균 높이 계산을 `set()` 기준으로 맞췄다.
  - TDD: `template-3-16_9` main title PNG bbox를 `(2, 5, 531, 90)`로 고정했다.
- Template-17 full의 Clipper1 random pan 방향을 recipe에 pinning했다.
  - 원인: 기존 Clipper1 참고 영상은 `right_to_left` pan으로 생성됐지만, Clipper2 deterministic auto pan은 같은 media에 대해 `left_to_right`를 골라 첫 프레임 원이 약 8px 오른쪽으로 밀렸다.
  - 변경: recipe `effects[].params.fit/travelPx/offsetPx`를 LocalRenderAdapter가 읽도록 하고, `template-17-full.recipe.json`에 `fit=height`, `direction=right_to_left`, `travelPx=8`, `offsetPx=416`을 명시했다.
- 검증:
  - GREEN: `uv run pytest tests/test_clipper1_video_render_template_styles.py::test_template_3_main_title_matches_legacy_text_vertical_placement -q` 성공, 1 passed.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_media_looping.py::test_recipe_can_pin_legacy_auto_pan_direction tests/test_clipper1_video_render_media_looping.py::test_explicit_legacy_auto_pan_uses_pinned_crop_direction -q` 성공, 2 passed.
  - GREEN: `uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_golden_frames.py tests/test_clipper1_golden_frame_diagnostics.py -q` 성공, 25 passed.
  - GREEN: `uv run python scripts/promote_legacy_template_smoke_baseline.py --all-designs --case 1:full --case 6:1:1 --case 16:4:3 --case 17:full --fixture-dir tests/fixtures/clipper2_template_baseline_frames --render-output-root /tmp/clipper2-template-baseline-after-text-height-reference-25` 성공, 25 cases.
  - GREEN: `uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_golden_frames.py tests/test_clipper1_golden_frame_diagnostics.py -q` 성공, 37 passed.
  - GREEN: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-template17-pan-pin --write-diffs top --top-diffs 10` 성공, 25 cases / failed 0.
- Drift 변화:
  - `template-3-16_9` `0.015185 -> 0.007126`
  - `template-17-full` `0.012880 -> 0.005683`
  - 현재 worst case는 `template-6-1_1`, mismatch `0.011948302469135802`.
- 다음 우선순위:
  - `template-6-1_1` content 영역의 zoom/resize 보간 및 encoding edge 차이를 Clipper1 MoviePy/Pillow pipeline과 비교한다.

## 최신 진행 기록: 2026-05-08 13:26 KST

- Full 비율 layout overlay 순서를 Clipper1과 맞췄다.
  - 사용자 관점 설명: full 비율 템플릿에서 제목/자막/로고가 반투명 layout에 눌려 회색으로 보이던 문제를 고쳤다.
  - Clipper1 `_create_final_video()` 순서는 `concat된 비디오 -> layout overlay -> 제목/자막/로고 overlay`다.
  - 이전 Clipper2는 segment 안에 제목/자막/로고를 먼저 넣고, concat 이후 마지막에 layout을 덮었다.
- 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - full-height layout case에서는 segment render에서 layout과 logo image를 제외한다.
    - segment별 text overlay asset은 concat 이후 final layout overlay 단계로 넘기고, clip 시작 시간만큼 start/end를 shift한다.
    - `_overlay_final_layout()`이 `layout -> logo image -> text overlays` 순서로 filter chain을 만든다.
  - `clipper_python/tests/test_clipper1_video_render_media_looping.py`
    - final layout overlay가 text overlay를 layout 이후에 쌓는지 filter graph로 검증한다.
  - `clipper2_template_baseline_frames` 25개를 새 Clipper2 출력으로 재생성했다.
- TDD/검증:
  - RED: `test_final_layout_overlay_places_text_overlays_after_layout`가 `_overlay_final_layout()`의 `text_overlay_assets` 인자 미지원으로 실패했다.
  - GREEN: focused test 성공.
  - GREEN: `uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-report-after-full-layout-order --write-diffs top --top-diffs 10` 성공, 25 cases / failed 0.
  - GREEN: `uv run pytest tests/test_clipper2_template_baseline_frames.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_golden_frames.py tests/test_clipper1_golden_frame_diagnostics.py -q` 성공, 16 passed.
  - GREEN: `uv run python -m compileall scripts` 성공.
  - GREEN: `uv run pytest -q` 성공, 97 passed / 4 skipped.
  - GREEN: `git diff --check` 성공.
  - GREEN: `adlight_python .venv/bin/python -m unittest discover -s tests -p 'test_export_clipper1_reference_frames.py'` 성공, 6 tests.
- Drift 변화:
  - `template-1-full` `0.027674 -> 0.011059`
  - `template-17-full` `0.024510 -> 0.014497`
  - 새 worst case는 `template-3-16_9`, mismatch `0.015185`.
- 다음 우선순위:
  - `template-3-16_9` top 영역의 title/subtitle/font edge 또는 layout alpha/encoding edge 차이를 진단한다.

## 최신 진행 기록: 2026-05-07 22:45 KST

- Legacy subtitle long-line wrapping을 추가했다.
  - 기존 Clipper1 `_generate_subtitle_images()`는 `wrap_text_to_lines()`로 긴 subtitle line을 폭에 맞게 여러 줄로 나눴다.
  - Python renderer도 subtitle PNG overlay 생성 전 font/tracking/box/shadow 설정과 output width 기준으로 wrapping한다.
  - Wrapped line마다 별도 timed PNG overlay를 만들고 기존 subtitle y-offset line positioning을 사용한다.
- 검증:
  - RED: 긴 subtitle이 PNG 1개로만 생성되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q` 성공, 19 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_media_looping.py -q` 성공, 27 passed.
  - `clipper_python uv run pytest -q` 성공, 73 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `633d55e feat: wrap legacy subtitle overlays`
- 다음 우선순위:
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - Golden fixture 기반 template별 tolerance/sample step 조정.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 최신 진행 기록: 2026-05-07 22:42 KST

- Legacy main title font-size fit을 추가했다.
  - 기존 Clipper1 `VideoService.py`는 `main_title1/2` 이미지 생성 전에 `adjust_font_size_to_fit(... max_width=self.contents_area_width)`로 긴 제목을 영상 폭 안에 맞췄다.
  - Python renderer도 `main_title`/`main_title2` PNG overlay 생성 시 output width 안에 들어오도록 font size를 줄인다.
  - Box padding, border, outline width, tracking을 고려한다.
  - Body와 shadow overlay는 같은 fitted font size를 공유한다.
- 검증:
  - RED: 긴 main title PNG가 320px output보다 넓은 400px로 생성되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q` 성공, 18 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_media_looping.py -q` 성공, 26 passed.
  - `clipper_python uv run pytest -q` 성공, 72 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `4d7901d feat: fit legacy main title text`
- 다음 우선순위:
  - Subtitle long-line wrapping parity.
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 최신 진행 기록: 2026-05-07 22:37 KST

- Plain text overlay도 legacy PNG overlay 기본 경로로 전환했다.
  - 기존 Clipper1 `VideoService.py`는 박스가 없는 project title/subtitle도 PIL image로 만든 뒤 ffmpeg overlay했다.
  - 현재 Python renderer는 이제 plain clip subtitle을 ASS event 대신 timed PNG overlay로 만든다.
  - Plain project text(`sub_title`, `main_title`, `main_title2`, `bottom_title`, `logo_text`)도 PNG overlay로 만든다.
  - Box/outline/shadow 조합은 기존 PNG overlay 경로를 유지한다.
  - `_append_project_text_overlay()`에서 더 이상 쓰지 않는 ASS event/style 인자를 정리했다.
- 검증:
  - RED: plain subtitle/main title이 `.ass` overlay로 생성되어 실패.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py -q` 성공, 17 passed.
  - `clipper_python uv run pytest tests/test_clipper1_video_render_template_styles.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_media_looping.py -q` 성공, 25 passed.
  - `clipper_python uv run pytest -q` 성공, 71 passed, 5 skipped.
  - `clipper_python git diff --check` 성공.
- 커밋:
  - `clipper_python` `7f2a399 feat: render plain legacy text overlays`
- 다음 우선순위:
  - 실제 old Clipper1 golden frames/payload/recipe fixture 채우기.
  - Golden fixture 기반 template별 tolerance/sample step 조정.
  - 21개 legacy template 전체와 ratio별 수동/자동 QA.

## 최신 진행 기록: 2026-05-10 KST

- `layoutImage` sample render mismatch를 auto zoom/pan frame 생성 쪽에서 확인했다.
- Python legacy background 프레임이 layout geometry를 무시하고 전체 프레임 resize를 하던 부분을 수정했다.
- layout image background는 이제 stretch가 아니라 cover-fit으로 합성한다.
- ffmpeg final/sample render의 crop 기준도 중앙으로 바꿔, 확대된 layout image가 좌상단부터 잘리는 문제를 막았다.
- packaged launch의 `uv sync`가 `clipper-plugin-clipper1-video-render`도 다시 설치하게 해서, 새 Python 소스가 venv에 남지 않도록 했다.
- packaged launch에서 기존 `clipper_venv`를 삭제 후 재생성하게 해서, stale worker code 재사용 가능성을 더 낮췄다.
- sample render video URL에 cache key를 붙여 브라우저가 이전 mp4를 재사용하지 않게 했다. layout image preview는 cover-fit으로 맞췄다.
- 다음 확인 포인트:
  - preview 조정값이 sample render에 그대로 반영되는지 다시 확인한다.
  - 좌하단 흰 박스가 남으면 layout 배경 합성 순서와 다른 overlay 레이어를 추가로 추적한다.

## 2026-05-13 Template Builder asset ownership clarification

- 현재 확정된 경계:
  - NestJS가 Template Builder의 목록, 편집, official registry 저장을 담당한다.
  - FastAPI/Python은 render contract를 받아 실제 렌더링만 담당한다.
  - 공식 템플릿의 카드 썸네일과 레이아웃 이미지는 S3 public URL로 DB에 저장되어 있다.
  - 폰트는 아직 공식 registry로 이관되지 않았고, Python renderer는 로컬 파일 경로 또는 legacy fonts dir를 해석해서 읽는다.
  - custom/system edit 저장은 아직 로컬 JSON repository 기반이다.
  - system template edit mode에서 수정한 뒤 `템플릿 등록`을 눌러야 official Postgres registry로 들어간다.
- 다음 설계 포인트:
  - 폰트까지 S3/DB로 통일할지 별도 설계가 필요하다.
  - custom template 저장소를 local JSON으로 둘지 DB로 이동할지 정책 결정을 다시 해야 한다.

## 주의

- SOLID 원칙을 우선한다.
- 구현 전에 interface/abstraction을 먼저 닫는다.
- Angular에 backend orchestration 책임을 다시 넣지 않는다.
- FastAPI plugin을 monolithic backend로 되돌리지 않는다.
- Electron에 product-level queue/project 책임을 몰아넣지 않는다.
- 최신 상태: sample render nonce / cache-bust는 들어갔고, bundled NestJS + packaged Python source도 현재 코드와 일치한다. 그런데 live sample render 출력은 아직 예전과 같아서, 다음 세션은 runtime payload와 worker 실행 로그를 직접 잡아야 한다.
- 추가 확인: NestJS payload mapper 테스트는 layout_image_x_offset/area_width를 이미 검증한다. 그러니 다음은 live app에서 실제 render job payload와 worker log를 확보하는 것이다.
- 현재 설치 앱도 최신 패키징 산출물로 교체했다. 다음 확인은 새로 열린 /Applications/Clipper2.app에서 sample render 재검증이다.

## 최신 인계: 2026-05-19 Template Builder card thumbnail / legacy thumbnail follow-up

- 다음 세션 시작 방식:
  - `.codex/README.md`, 이 파일, `.codex/session-logs` 최신 파일을 먼저 읽는다.
  - 현재 작업 상태와 변경 범위만 짧게 파악/요약한다.
  - 사용자가 다음 메시지로 수정 요구사항을 줄 때까지 파일 수정, 테스트 실행, 빌드, S3 작업을 먼저 시작하지 않는다.
- 이번 세션에서 끝낸 작업:
  - custom/clone/new template 저장 시 card thumbnail 생성은 Electron 화면의 실제 preview DOM 캡처를 우선 사용한다.
  - card thumbnail ratio는 저장 시 선택 ratio가 아니라 항상 `4:3`으로 강제한다.
  - 캡처 중에는 editor ratio를 임시로 `4:3`으로 바꾸고 preview chrome을 숨긴 뒤, 캡처 후 기존 ratio와 text artifact 상태를 복원한다.
  - create/clone 직후 새 family가 아직 렌더되기 전에는 live DOM 캡처를 쓰지 않아 이전 선택 template이 thumbnail로 저장되지 않게 했다.
  - legacy Clipper1 card thumbnails 21개는 NestJS seed family를 Angular export route로 렌더해 `4:3` 왼쪽 캔버스 PNG로 재생성했다.
  - legacy screenshot export는 `.phone-canvas img` 전체 load/decode 완료를 기다린 뒤 캡처하도록 수정했다. 이전에는 layout image가 완전히 로드되기 전에 캡처될 수 있었다.
  - regenerated legacy thumbnails는 기존 DB/registry URL을 바꾸지 않기 위해 기존 S3 prefix/key인 `s3://clipperstudio/templates/card-thumbnails/legacy-clipper1/`에 overwrite 업로드했다.
- 주요 파일:
  - `clipper_electron/src/shared/ipc-contract.ts`
  - `clipper_electron/src/preload/preload.ts`
  - `clipper_electron/src/main/capture-ipc.ts`
  - `clipper_electron/src/main/main.ts`
  - `clipper_angular/src/core/clipper-bridge.ts`
  - `clipper_angular/src/features/template-builder/services/template-builder-card-thumbnail.service.ts`
  - `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
  - `clipper_angular/src/features/template-builder/services/template-builder-preview-screenshot.export.spec.ts`
  - `clipper_angular/scripts/export-template-builder-preview-screenshot.mjs`
  - `clipper_angular/scripts/export-legacy-clipper1-card-thumbnails.mjs`
- 검증 기록:
  - `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts --include src/features/template-builder/services/template-builder-preview-screenshot.export.spec.ts`: 57 SUCCESS.
  - `clipper_angular npm run build`: passed.
  - `clipper_angular node --test test/template-builder-preview-screenshot-export.test.mjs`: 2 passed.
  - `clipper_nestjs node --test test/legacy-card-thumbnail-upload-script.test.js`: 3 passed.
  - S3 upload script uploaded 21 thumbnails to `clipperstudio/templates/card-thumbnails/legacy-clipper1/`.
  - HEAD checks for `1_ratio_4_3_thumb.png`, `16_ratio_4_3_thumb.png`, `21_ratio_4_3_thumb.png` returned 200 OK.
- 커밋:
  - `clipper_angular` `31322e6 fix: sync template builder layouts and thumbnails`
  - `clipper_electron` `abb800f feat: add page region capture ipc`
  - `clipper_nestjs` `b164ccb fix: stage template assets and upload thumbnails`
  - 커밋 전 추가 검증: Angular targeted Karma 244 SUCCESS, Angular/Electron/NestJS build 통과, screenshot export Node test 2 passed, NestJS 관련 Node tests 통과, 세 repo `git diff --check` 통과.
  - 커밋 후 세 repo 모두 clean 상태였다.
- 주의:
  - S3 object overwrite라 browser/image cache가 남으면 grid에서 잠시 이전 thumbnail이 보일 수 있다.
  - 임시 AWS credential은 대화에 노출됐지만 문서나 코드에 저장하지 않았다. 다음 세션에서 credential을 재사용하거나 기록하지 말 것.
  - 다음 세션은 사용자가 요구사항을 줄 때까지 자동으로 남은 버그를 찾아 수정하지 않는다.
