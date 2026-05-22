# Clipper2 Windows Packaging Discovery and Plan

작성일: 2026-05-19
상태: 1차 구현 완료, Windows PC 실기 검증 대기

## 목적

지금까지 Clipper2 설치형 빌드는 Mac mini에서 다음 명령으로 검증했다.

```bash
npm run build:app:mac:arm64
```

이제 Windows x64 설치형 빌드가 필요하다. 실제 Windows 빌드/실행 검증은 Windows PC에서 진행하고, 그 전에 필요한 구현과 구조 정리는 Mac mini 개발 환경에서 진행한다.

이번 문서는 구현 전 파악 결과와 Windows 빌드 지원 계획, 그리고 2026-05-19에 진행한 1차 구현 결과를 기록한다.

## 2026-05-19 1차 구현 결과

브랜치:

- `clipper_electron`: `feature/windows-packaging`
- `clipper_nestjs`: `feature/windows-packaging`
- `clipper_python`: `feature/windows-packaging`
- `clipper_angular`: 변경이 없어 기존 브랜치 유지

변경 요약:

- `clipper_electron/scripts/build-app.mjs`
  - Python `__pycache__` cleanup에서 Unix 전용 `find ... rm -rf`를 제거했다.
  - Node `fs.readdirSync`/`rmSync` 기반 recursive cleanup으로 교체했다.
- `clipper_electron/scripts/fetch-uv.mjs`
  - `curl`, `mv`, `unzip`, `rm -rf` shell command 의존을 제거했다.
  - Node `https`, `stream.pipeline`, `copyFileSync`, `rmSync` 기반 download/copy/cleanup으로 교체했다.
  - 압축 해제는 macOS와 Windows 10/11에 기본 제공되는 `tar` command를 사용한다.
- `clipper_nestjs/scripts/copy-assets.mjs`
  - NestJS `src/dance/data`, `src/projects/assets`를 target output으로 복사하는 cross-platform Node script를 추가했다.
- `clipper_nestjs/package.json`
  - `copy-assets`, `bundle`에서 `mkdir -p`, `cp -R`를 제거하고 `node scripts/copy-assets.mjs`를 사용하도록 바꿨다.
- `clipper_python/pyproject.toml`
  - `[tool.uv].environments`에 `sys_platform == 'win32'`를 추가했다.
- `clipper_python/uv.lock`
  - `uv lock`으로 Windows marker/wheel 정보를 추가했다.
  - Windows 조건부 dependency로 `colorama`가 추가됐다.
- `clipper_electron/electron-builder.yml`
  - `../adlight_python/fonts` extraResource를 제거했다.
  - 공식 Template Builder templates는 DB payload의 S3 font URL을 사용하므로 legacy font 파일을 앱에 번들링하지 않는다.

검증:

- `clipper_electron`
  - `node --check scripts/build-app.mjs`: passed
  - `node --check scripts/fetch-uv.mjs`: passed
  - `node scripts/prepare-uv.mjs win32 x64`: passed (`uv-win32-x64.exe -> uv.exe`)
  - `npm run build`: passed
  - `npm run build:app:mac:arm64`: passed after removing `adlight_python/fonts` dependency
- `clipper_nestjs`
  - `node --check scripts/copy-assets.mjs`: passed
  - `npm run build`: passed
  - `npm run bundle`: passed
- `clipper_python`
  - `uv lock`: passed
  - `uv lock --check`: passed

아직 남은 Windows PC 실기 검증:

1. Windows PC에서 각 repo가 `feature/windows-packaging` 상태인지 확인한다.
2. Node/npm/uv가 준비된 PowerShell 또는 cmd에서 `clipper_electron`으로 이동한다.
3. `npm run build:app:win:x64`를 실행한다.
4. `clipper_electron/dist-app`에 NSIS installer가 생성되는지 확인한다.
5. 설치 후 앱 첫 실행에서 다음을 확인한다.
   - Renderer 로딩.
   - NestJS gateway 실행.
   - Python first-run `uv sync` 및 `clipper_venv/Scripts/python.exe` 생성.
   - Template Builder 공식 템플릿 목록 조회.
   - 샘플 렌더 또는 최소 preview API 호출.

주의:

- `scripts/fetch-uv.mjs`는 Windows에서도 `tar` command가 있다고 가정한다. Windows 10/11 기본 `bsdtar` 기준으로는 동작해야 하지만, 실제 Windows PC에서 `tar --version` 또는 build 실행으로 확인해야 한다.
- 이번 1차 목표는 unsigned internal Windows x64 NSIS installer다. code signing, auto-update, CUDA runtime packaging은 아직 범위 밖이다.
- Windows PC에는 4개 Clipper2 repo만 clone한다. `adlight_python`은 이 build flow에 필요하지 않다.

## 브랜치 전략

질문: "브랜치를 4개 레포지토리 전부 다 새로 파야 하나?"

결론:

- 구현 시작 시 새 브랜치는 파는 것이 맞다.
- 하지만 4개 repo 전부를 무조건 같은 브랜치로 시작할 필요는 없다.
- 변경 가능성이 높은 순서는 다음과 같다.

필수 가능성 높음:

1. `clipper_electron`
   - 설치형 빌드 entrypoint.
   - `scripts/build-app.mjs`, `scripts/fetch-uv.mjs`, `electron-builder.yml`, Windows smoke/guide가 걸려 있다.
2. `clipper_python`
   - packaged app 첫 실행 시 `uv sync` 대상.
   - 현재 `pyproject.toml`이 `darwin`, `linux`만 허용하고 Windows를 제외한다.
   - `uv.lock`도 Windows marker가 없어서 Windows venv 생성이 가장 큰 blocker다.

변경 가능성 있음:

3. `clipper_nestjs`
   - `npm run bundle`이 `mkdir -p`, `cp -R` shell command를 쓴다.
   - Windows에서 `npm run bundle`이 그대로 실패할 수 있으므로 cross-platform copy script로 바꾸게 될 가능성이 높다.

변경 가능성 낮음:

4. `clipper_angular`
   - Angular build 자체는 CLI 기반이라 Windows에서도 상대적으로 안전하다.
   - Windows 관련 UI/문구/installer 안내를 넣지 않는 한 코드 변경 가능성은 낮다.

추천:

- 실제 구현 브랜치명은 repo마다 동일하게 맞춘다.
  - 예: `feature/windows-packaging`
- 단, 처음에는 `clipper_electron`, `clipper_python`, `clipper_nestjs`만 브랜치를 파도 충분하다.
- `clipper_angular`는 변경이 필요해지는 시점에 같은 이름으로 브랜치를 파면 된다.
- 4개 repo를 한 번에 checkout해야 협업/기록이 편하다면 전부 같은 브랜치를 만들어도 문제는 없다. 다만 실제 변경 없는 repo까지 커밋을 만들 필요는 없다.

## 현재 repo 역할

### `clipper_electron`

역할:

- Electron shell.
- packaged app entrypoint.
- Angular renderer, NestJS gateway bundle, Python plugin workspace, fonts, uv binary를 `extraResources`로 포함.
- packaged mode에서 Python venv를 `userData/clipper_venv`에 생성.
- packaged mode에서 NestJS gateway를 `utilityProcess.fork()`로 실행.

주요 파일:

- `clipper_electron/package.json`
- `clipper_electron/scripts/build-app.mjs`
- `clipper_electron/scripts/prepare-uv.mjs`
- `clipper_electron/scripts/fetch-uv.mjs`
- `clipper_electron/electron-builder.yml`
- `clipper_electron/src/main/main.ts`
- `clipper_electron/src/main/setup/first-run.ts`
- `clipper_electron/src/main/setup/download-ffmpeg.ts`
- `clipper_electron/src/main/plugin/plugin-process.ts`
- `clipper_electron/src/main/backend/nest-process.ts`
- `clipper_electron/src/main/config/bundled-env-provider.ts`

### `clipper_angular`

역할:

- Electron packaged renderer.
- `ng build --configuration=electron` 결과물이 `clipper_angular/dist/clipper_angular/browser`에 생기고 Electron resource로 포함된다.

주요 파일:

- `clipper_angular/package.json`
- `clipper_angular/angular.json`

현재 electron build config:

- `baseHref: "./"`
- `environment.electron.ts` replacement
- output: `dist/clipper_angular/browser`

### `clipper_nestjs`

역할:

- packaged app 내부 local gateway.
- `npm run bundle`로 `dist/bundled/index.js`를 만들고 Electron이 resource로 포함한다.
- packaged mode에서 Electron `utilityProcess.fork()`로 실행된다.

주요 파일:

- `clipper_nestjs/package.json`
- `clipper_nestjs/src/main.ts`
- `clipper_nestjs/src/sources/source.service.ts`

현재 build scripts:

```json
"build": "tsc -p tsconfig.json && npm run copy-assets",
"copy-assets": "mkdir -p dist/dance/data dist/projects/assets && cp -R src/dance/data/. dist/dance/data/ && cp -R src/projects/assets/. dist/projects/assets/",
"bundle": "ncc build src/main.ts -o dist/bundled && mkdir -p dist/bundled/dance/data dist/bundled/projects/assets && cp -R src/dance/data/. dist/bundled/dance/data/ && cp -R src/projects/assets/. dist/bundled/projects/assets/"
```

Windows에서 `mkdir -p`, `cp -R`는 기본 `cmd.exe` 환경에서 실패할 가능성이 높다.

### `clipper_python`

역할:

- packaged app에 source workspace로 포함된다.
- packaged 첫 실행 시 Electron이 bundled `uv`로 `uv sync --directory <resources/clipper_python>` 실행.
- plugin packages:
  - `clipper-plugin-sdk`
  - `clipper-plugin-dialog-highlight`
  - `clipper-plugin-dance-highlight`
  - `clipper-plugin-clipper1-video-render`

주요 파일:

- `clipper_python/pyproject.toml`
- `clipper_python/uv.lock`
- `clipper_python/clipper_plugin_sdk/pyproject.toml`
- `clipper_python/plugins/dialog_highlight/pyproject.toml`
- `clipper_python/plugins/dance_highlight/pyproject.toml`
- `clipper_python/plugins/clipper1_video_render/pyproject.toml`

현재 root `pyproject.toml`:

```toml
[tool.uv]
environments = ["sys_platform == 'darwin'", "sys_platform == 'linux'"]
```

이 설정은 Windows packaged first-run에서 가장 먼저 볼 blocker다.

## 현재 설치형 빌드 파이프라인

`clipper_electron/scripts/build-app.mjs` 기준:

1. Python `__pycache__` 제거
2. Angular build
   - `npm run build:electron -- --progress=false`
3. NestJS bundle
   - `npm run bundle`
4. Electron TypeScript compile
   - `npx tsc -p tsconfig.json`
5. uv binary 준비
   - `node scripts/prepare-uv.mjs <platform> <arch>`
6. electron-builder
   - `npx electron-builder --mac --arm64`
   - 또는 Windows target이면 `npx electron-builder --win --x64`

`clipper_electron/package.json`에는 이미 Windows command가 있다.

```json
"build:app:win:x64": "node scripts/build-app.mjs win32 x64"
```

## 현재 electron-builder 설정

`clipper_electron/electron-builder.yml`:

공통:

- output: `dist-app`
- build resources: `build-resources`
- asar files:
  - `dist-electron/**/*`
  - `package.json`
- extraResources:
  - Angular renderer
  - NestJS bundled output
  - `clipper_nestjs/.env.local`
  - Python workspace

Mac:

```yaml
mac:
  target:
    - target: dmg
  extraResources:
    - from: resources/bin/uv
      to: bin/uv
```

Windows:

```yaml
win:
  target:
    - target: nsis
      arch:
        - x64
  extraResources:
    - from: resources/bin/uv.exe
      to: bin/uv.exe

nsis:
  oneClick: false
  perMachine: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  runAfterFinish: true
```

즉 Windows target 설정 자체는 이미 들어 있다.

## 현재 Windows 관련으로 이미 반영된 런타임 코드

### packaged venv path

`clipper_electron/src/main/setup/first-run.ts`:

- Windows binary path:
  - `<userData>/clipper_venv/Scripts/python.exe`
  - `<userData>/clipper_venv/Scripts/yt-dlp.exe`
- macOS/Linux binary path:
  - `<userData>/clipper_venv/bin/python`

### bundled uv

`prepare-uv.mjs`:

- target `win32 x64`이면:
  - source: `resources/bin/uv-win32-x64.exe`
  - dest: `resources/bin/uv.exe`

`electron-builder.yml`:

- Windows resource includes `resources/bin/uv.exe` -> `resources/bin/uv.exe`

### ffmpeg/ffprobe runtime download

`download-ffmpeg.ts`:

- `win32-x64` key 존재.
- Windows ffmpeg path는 `ffmpeg.exe`.
- Windows ffprobe path는 `ffprobe.exe`.
- ffprobe extraction uses `tar.exe`.
  - Windows 10/11 기본 `tar.exe`가 있으면 동작 가능.
  - 일부 환경에서 tar가 없거나 PATH에서 안 잡히면 실패 가능.

### Python plugin process

`plugin-process.ts`:

- packaged Windows Python:
  - `<venvPath>/Scripts/python.exe`
- PATH delimiter:
  - `node:path.delimiter` 사용. Windows `;`, POSIX `:`.
- ffmpeg env:
  - `IMAGEIO_FFMPEG_EXE`
  - `IMAGEIO_FFPROBE_EXE`

### NestJS source ingest

`clipper_nestjs/src/sources/source.service.ts`:

- Windows ffmpeg candidate:
  - `ffmpeg.exe`
- browser cookie fallback order:
  - `chrome`, `edge`, `brave`, `firefox`

### Resource telemetry

문서와 코드상 Windows fallback telemetry가 일부 존재한다.

- Electron resource monitor: Windows process/GPU collection path 있음.
- NestJS static resource host도 Windows GPU collection path 있음.
- 기존 문서: `.codex/design/WINDOWS_CUDA_RUNTIME_STRATEGY.md`

## 현재 Windows 빌드 blocker / risk

### 1. `build-app.mjs`의 Unix-only cleanup

현재:

```js
execSync("find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +", {
  cwd: pythonDir, stdio: 'inherit',
});
```

Windows 기본 shell에서 실패 가능성이 높다.

필요:

- Node fs 기반 recursive cleanup으로 변경.
- `.venv`, `.uv`, `node_modules` 같은 excluded directories는 skip.

변경 repo:

- `clipper_electron`

### 2. `clipper_nestjs` package scripts의 Unix commands

현재:

```json
"copy-assets": "mkdir -p ... && cp -R ...",
"bundle": "ncc build ... && mkdir -p ... && cp -R ..."
```

Windows 기본 `cmd.exe`에서 `mkdir -p`, `cp -R`는 실패한다.

필요:

- Node script로 asset copy를 대체.
  - 예: `scripts/copy-assets.mjs`
  - `fs.cpSync(src, dest, { recursive: true })`
  - `fs.mkdirSync(dest, { recursive: true })`
- package scripts는 Node script 호출로 변경.

변경 repo:

- `clipper_nestjs`

### 3. `clipper_python` uv environments가 Windows를 제외

현재:

```toml
[tool.uv]
environments = ["sys_platform == 'darwin'", "sys_platform == 'linux'"]
```

이 상태에서는 Windows `uv sync`가 workspace environment resolution 대상이 아니거나 lock이 Windows packages를 갖지 못할 가능성이 높다.

실제로 `uv.lock`도 거의 모든 package marker가 `sys_platform == 'darwin' or sys_platform == 'linux'`로 잠겨 있다.

필요:

- `pyproject.toml`에 Windows environment 추가.
  - 예: `"sys_platform == 'win32'"`
- lock refresh.
  - Windows PC에서 `uv lock` 또는 Mac에서 Windows target lock 가능 여부 확인.
  - 최종적으로 `uv.lock`에 Windows wheels/markers가 들어와야 packaged first-run이 안정적이다.

변경 repo:

- `clipper_python`

### 4. Python dependency Windows wheel/runtime 리스크

현재 plugin dependencies:

`dialog_highlight`:

- `faster-whisper`
- `open-clip-torch`
- `scenedetect[opencv]`
- `openai`
- `numpy`
- `librosa`
- `Pillow`
- `yt-dlp`

`dance_highlight`:

- `onnxruntime`
- `insightface`
- `ultralytics`
- `opencv-python`
- `numpy`
- `scikit-learn`
- `yt-dlp`

`clipper1_video_render`:

- `fonttools`
- `opencv-python-headless`
- `pillow`
- `uharfbuzz`

위 패키지는 Windows wheel availability, MSVC build tool 요구, torch CPU/CUDA wheel 선택, onnxruntime provider 차이의 영향을 받는다.

초기 목표는 "Windows CPU fallback packaged build"로 잡는 게 맞다.

- CUDA acceleration은 이 단계의 목표에서 제외.
- 이미 `.codex/design/WINDOWS_CUDA_RUNTIME_STRATEGY.md`에 CUDA는 별도 profile로 분리하는 방향이 기록되어 있다.

### 5. `fetch-uv.mjs`도 Unix command 의존

현재:

- `curl`
- `tar`
- `mv`
- `unzip`
- `rm -rf`

다만 현재 `resources/bin/uv-win32-x64.exe`는 Mac mini workspace에 존재한다. 그러나 `.gitignore`에 의해 tracked file이 아닐 가능성이 높다.

Windows PC에서 repo를 새로 clone하면 uv binaries가 없을 수 있다.

필요:

- Windows PC에서 `npm run fetch-uv`가 동작해야 한다.
- 따라서 `fetch-uv.mjs`도 Node https/zip/tar 처리로 cross-platform화하거나, uv binaries를 별도 artifact/cache로 전달하는 운영 절차가 필요하다.

추천:

- 구현 단계에서는 `fetch-uv.mjs`도 cross-platform Node script로 바꾸는 게 낫다.
- 최소 임시안은 Windows PC에 `resources/bin/uv-win32-x64.exe`를 수동 배치하고 `prepare-uv.mjs`만 사용.

변경 repo:

- `clipper_electron`

### 6. electron-builder Windows icon/signing

현재:

- `build-resources/.gitkeep`만 존재.
- `icon.ico`는 주석 처리되어 있다.
- code signing 설정 없음.

초기 내부 테스트용 Windows installer는 unsigned NSIS로 가능하다.

추후 배포용에는 필요:

- `build-resources/icon.ico`
- Windows code signing certificate
- publisherName/signing config
- SmartScreen 평판 대응

이번 1차 목표에서는 signing은 제외해도 된다.

### 7. Bundled env 보안/운영 리스크

현재:

- `electron-builder.yml`이 `clipper_nestjs/.env.local`을 resource에 포함한다.
- `BundledEnvProvider`는 `clipper_python/.env`, `clipper_nestjs/.env`, `clipper_nestjs/.env.local`, `userData/.env`를 읽는다.

이 구조는 Mac packaged에서도 이미 쓰고 있지만, Windows installer 배포 시에도 secrets가 평문으로 포함된다.

초기 내부 테스트 빌드에서는 유지 가능.

외부 배포 전에는:

- RemoteConfigProvider
- userData `.env` provisioning
- installer-time config injection

중 하나로 바꿔야 한다.

## Windows PC에서 필요한 환경

초기 build 검증 기준:

- Windows 10/11 x64
- Git
- Node.js 22 LTS
  - root `.nvmrc`는 `22`
  - Mac mini 현재 확인: Node `v22.22.2`, npm `10.9.7`
- npm install 완료:
  - `clipper_angular`
  - `clipper_nestjs`
  - `clipper_electron`
- Python은 시스템에 없어도 uv가 관리하는 것이 목표.
  - 단, 일부 package가 source build를 요구하면 Visual Studio Build Tools가 필요할 수 있다.
  - 이 경우는 dependency/lock 전략 문제로 보고 별도 처리.
- Network access:
  - electron-builder Electron binary/cache download
  - uv Python/runtime package download
  - ffmpeg/ffprobe first-run download
  - model download

## 목표 범위

### 1차 목표: Windows x64 unsigned internal installer

성공 기준:

1. Windows PC에서:

```powershell
cd clipper_electron
npm run build:app:win:x64
```

2. `clipper_electron/dist-app`에 NSIS installer 생성.
3. installer 실행 후 앱 설치 가능.
4. 첫 실행에서:
   - Angular renderer 로드.
   - packaged NestJS starts.
   - packaged `uv sync` creates `userData/clipper_venv`.
   - `/v1/health` OK.
   - `/v1/resources` OK.
5. 최소 plugin start:
   - `clipper1_video_render` 또는 가장 가벼운 plugin start.
   - 가능하면 `dance_highlight` start/stop까지 확인.

### 1차 제외 범위

- Windows code signing.
- Windows CUDA acceleration.
- installer auto-update.
- NSIS web installer.
- 외부 사용자용 secrets/config delivery.
- 모든 모델 다운로드 완료까지 보장하는 full E2E.

## 구현 계획

### Phase 0. Branch 준비

권장:

```bash
git -C clipper_electron checkout -b feature/windows-packaging
git -C clipper_python checkout -b feature/windows-packaging
git -C clipper_nestjs checkout -b feature/windows-packaging
```

`clipper_angular`는 변경 필요가 확인되면:

```bash
git -C clipper_angular checkout -b feature/windows-packaging
```

### Phase 1. Build scripts cross-platform화

`clipper_electron`:

- `build-app.mjs`
  - `find ... rm -rf` 제거.
  - Node fs recursive cleanup으로 교체.
- `fetch-uv.mjs`
  - `curl/tar/mv/unzip/rm -rf` 제거 또는 Windows fallback 추가.
  - 최소한 Windows PC에서 uv-win32 binary를 받을 수 있게 보장.

`clipper_nestjs`:

- `scripts/copy-assets.mjs` 추가.
- `package.json`:
  - `copy-assets`를 Node script로 교체.
  - `bundle` 후 asset copy도 Node script로 교체.

검증:

- Mac에서 기존 `npm run build:app:mac:arm64`가 계속 통과.
- Mac에서 `node scripts/build-app.mjs win32 x64`는 electron-builder Windows target까지 실제 성공 여부를 보장하지 않아도, 최소 Step 0~4가 platform arg 기준으로 통과하는지 확인.

### Phase 2. Python uv Windows environment/lock

`clipper_python`:

- root `pyproject.toml`에 Windows environment 추가.
- `uv.lock` refresh.

예상 변경:

```toml
[tool.uv]
environments = [
  "sys_platform == 'darwin'",
  "sys_platform == 'linux'",
  "sys_platform == 'win32'",
]
```

검증:

- Mac:
  - 기존 `uv sync`가 깨지지 않는지 확인.
- Windows:
  - `uv sync --directory clipper_python` 성공.
  - generated venv에 local workspace packages install.
  - `python -m clipper1_video_render <port>` 같은 lightweight plugin start 가능 여부 확인.

주의:

- lock refresh가 Windows dependency set을 크게 바꿀 수 있으므로 diff를 꼼꼼히 확인해야 한다.
- `torch`, `onnxruntime`, `insightface`, `opencv` 쪽에서 Windows wheel/source build 문제가 나올 수 있다.

### Phase 3. Windows installer build

Windows PC:

```powershell
cd clipper_angular
npm ci
npm run build:electron

cd ..\clipper_nestjs
npm ci
npm run bundle

cd ..\clipper_electron
npm ci
npm run fetch-uv
npm run build:app:win:x64
```

최종 command는 `clipper_electron`에서 한 번에:

```powershell
npm run build:app:win:x64
```

단, 각 repo의 `npm ci`는 사전에 필요하다.

### Phase 4. Windows packaged smoke

설치 후 확인:

1. 앱 실행.
2. 로그 위치 확인.
   - Electron `app.getPath('logs')`
   - userData under `%APPDATA%` 또는 Electron default path.
3. Backend URL 확인.
4. health:
   - Angular에서 backend locator가 정상 동작하는지.
   - 또는 logs에서 NestJS port 확인.
5. Python venv:
   - `%APPDATA%/.../clipper_venv/Scripts/python.exe`
   - `%APPDATA%/.../clipper_venv/Scripts/yt-dlp.exe`
6. ffmpeg:
   - first plugin start 시 `%APPDATA%/.../bin/ffmpeg.exe`, `ffprobe.exe` 생성.
7. plugin:
   - start/stop.
   - `/v1/resources` process list.
   - model download marker state.

## Windows-specific smoke checklist 초안

빌드:

- [ ] `npm ci` completed in `clipper_angular`
- [ ] `npm ci` completed in `clipper_nestjs`
- [ ] `npm ci` completed in `clipper_electron`
- [ ] `npm run fetch-uv` completed or `resources/bin/uv-win32-x64.exe` present
- [ ] `npm run build:app:win:x64` completed
- [ ] NSIS installer exists under `clipper_electron/dist-app`

설치/실행:

- [ ] Installer opens
- [ ] Install completes
- [ ] App launches after finish
- [ ] Renderer loads without blank screen
- [ ] Packaged NestJS starts
- [ ] Python venv sync starts on first run
- [ ] Python venv sync completes
- [ ] App relaunch skips expensive venv recreation

기능:

- [ ] Backend health OK
- [ ] `/v1/resources` OK
- [ ] ffmpeg download overlay or flow works
- [ ] plugin start works for at least one plugin
- [ ] plugin stop works
- [ ] logs contain no path separator errors
- [ ] paths with Korean/space user profile do not fail

## 문서/운영 TODO

Windows 빌드가 처음 성공하면 다음 문서를 추가하는 것이 좋다.

- `.codex/operations/windows-packaging/runbooks/windows-build-guide.md`
  - Windows PC setup
  - commands
  - expected output
  - smoke checklist
  - known issues

## 현재 조사에서 확인한 요약

이미 준비된 것:

- `build:app:win:x64` npm script가 있다.
- `electron-builder.yml`에 Windows NSIS target이 있다.
- `prepare-uv.mjs`가 `uv-win32-x64.exe` -> `uv.exe`를 지원한다.
- Electron runtime은 Windows venv `Scripts` path를 고려한다.
- ffmpeg downloader는 `win32-x64` key를 갖고 있다.
- plugin process PATH delimiter는 cross-platform API를 쓴다.

아직 필요한 것:

- Unix-only build scripts 제거.
- Windows uv environment/lock 추가.
- Windows dependency resolution 검증.
- Windows PC에서 unsigned NSIS installer build/smoke.
- 성공 후 Windows build guide 작성.

가장 높은 blocker:

1. `clipper_python` `tool.uv.environments`가 Windows를 제외한다.
2. `clipper_nestjs` bundle script가 Unix shell command를 쓴다.
3. `clipper_electron` build/fetch scripts가 Unix command를 쓴다.

## 다음 세션 시작 시 추천 순서

1. 이 문서를 먼저 읽는다.
2. 새 branch를 `clipper_electron`, `clipper_python`, `clipper_nestjs`에 만든다.
3. `clipper_electron` build scripts를 Node fs 기반으로 바꾼다.
4. `clipper_nestjs` asset copy를 Node script로 바꾼다.
5. `clipper_python` Windows environment 추가와 lock refresh를 별도 commit으로 처리한다.
6. Mac에서 기존 Mac build가 깨지지 않는지 확인한다.
7. Windows PC에서 `npm run build:app:win:x64`와 smoke checklist를 수행한다.
