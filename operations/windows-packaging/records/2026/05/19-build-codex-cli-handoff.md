# Windows PC Codex CLI Handoff: Clipper2 Installer Build

작성일: 2026-05-19

## 목적

Windows PC에서 처음부터 Clipper2 개발/빌드 환경을 구성하고, Windows x64 NSIS installer를 생성한 뒤 최소 smoke test까지 진행한다.

이 문서는 Windows PC에서 새 Codex CLI 세션을 열었을 때 그대로 전달하기 위한 작업 지시서다.

## 중요한 전제

- repo는 4개만 클론한다.
  - `clipper_angular`
  - `clipper_electron`
  - `clipper_nestjs`
  - `clipper_python`
- `adlight_python`은 클론하지 않는다.
  - `clipper_electron/electron-builder.yml`은 더 이상 `../adlight_python/fonts`를 참조하지 않는다.
  - 공식 Template Builder templates의 font는 DB payload의 S3 URL을 사용한다.
  - 앱 설치 파일에 legacy font 파일을 번들링하지 않는다.
- 실제 빌드 entrypoint는 `clipper_electron`이다.
- Windows PC의 실제 build command는 `clipper_electron` 폴더에서 실행하는 `npm run build:app:win:x64`다.
- DB/S3 secret 값은 문서에 기록하지 않는다. 필요한 값은 사용자에게 받아 `clipper_nestjs/.env.local`에 둔다.

## Mac 쪽에서 먼저 완료되어 있어야 하는 것

Windows PC에서 진행하기 전에 Mac mini 쪽 변경사항이 remote에 push되어 있어야 한다.

필수 브랜치/커밋:

- `clipper_electron`
  - branch: `feature/windows-packaging`
  - includes:
    - cross-platform build scripts
    - no `adlight_python/fonts` packaging dependency
- `clipper_nestjs`
  - branch: `feature/windows-packaging`
  - includes:
    - cross-platform `scripts/copy-assets.mjs`
- `clipper_python`
  - branch: `feature/windows-packaging`
  - includes:
    - Windows uv lock support
    - no bundled legacy font files
- `clipper_angular`
  - branch: `feature/initial-scaffold`
  - no Windows-specific change in this task

If any branch is missing on Windows, stop and ask the user to push the Mac-side commits first.

## Windows PC Required Tools

Use PowerShell unless there is a reason to use cmd.

Install/verify:

```powershell
git --version
node -v
npm -v
tar --version
```

Recommended Node/npm baseline from Mac mini:

```text
node v24.3.0
npm 11.4.2
```

Exact match is not mandatory for first smoke, but use Node 22+ at minimum unless the repo documents otherwise.

Windows 10/11 normally includes `tar`. If `tar --version` fails, `clipper_electron npm run fetch-uv` may fail because uv archive extraction uses `tar`.

## Target Folder Structure

Create this sibling repo layout:

```text
C:\project\adlight\
  clipper_angular\
  clipper_electron\
  clipper_nestjs\
  clipper_python\
```

Commands:

```powershell
mkdir C:\project
mkdir C:\project\adlight
cd C:\project\adlight
```

## Clone Repos

```powershell
git clone https://github.com/OhMyMetabuzz/clipper_angular.git
git clone https://github.com/OhMyMetabuzz/clipper_electron.git
git clone https://github.com/OhMyMetabuzz/clipper_nestjs.git
git clone https://github.com/OhMyMetabuzz/clipper_python.git
```

Do not clone `adlight_python` for this build flow.

## Checkout Branches

```powershell
cd C:\project\adlight\clipper_electron
git fetch
git checkout feature/windows-packaging

cd C:\project\adlight\clipper_nestjs
git fetch
git checkout feature/windows-packaging

cd C:\project\adlight\clipper_python
git fetch
git checkout feature/windows-packaging

cd C:\project\adlight\clipper_angular
git fetch
git checkout feature/initial-scaffold
```

Verify:

```powershell
cd C:\project\adlight\clipper_electron
git status --short --branch

cd C:\project\adlight\clipper_nestjs
git status --short --branch

cd C:\project\adlight\clipper_python
git status --short --branch

cd C:\project\adlight\clipper_angular
git status --short --branch
```

Expected:

- first three repos on `feature/windows-packaging`
- Angular on `feature/initial-scaffold`
- clean worktrees

## Install Node Dependencies

```powershell
cd C:\project\adlight\clipper_angular
npm install

cd C:\project\adlight\clipper_nestjs
npm install

cd C:\project\adlight\clipper_electron
npm install
```

No npm install is needed in `clipper_python`.

## Prepare Environment File

The packaged NestJS gateway expects this file to exist:

```text
C:\project\adlight\clipper_nestjs\.env.local
```

Create it from the same secret/config values used on Mac mini.

It must include the DB/S3 env needed by Template Builder official templates. Do not print or commit secret values.

After creating it:

```powershell
cd C:\project\adlight\clipper_nestjs
dir .env.local
```

If `.env.local` is missing, `electron-builder` may fail while copying `extraResources`, or the installed app may fail to load official Template Builder data.

## Prepare uv Binaries

The uv binaries are not tracked in git. Download them on Windows:

```powershell
cd C:\project\adlight\clipper_electron
npm run fetch-uv
```

Verify:

```powershell
dir C:\project\adlight\clipper_electron\resources\bin
```

Expected important file:

```text
uv-win32-x64.exe
```

The final build command will copy it to:

```text
resources\bin\uv.exe
```

## Preflight Builds

Run these before the installer build to isolate failures.

Angular:

```powershell
cd C:\project\adlight\clipper_angular
npm run build:electron -- --progress=false
```

NestJS:

```powershell
cd C:\project\adlight\clipper_nestjs
npm run bundle
```

Electron TypeScript:

```powershell
cd C:\project\adlight\clipper_electron
npm run build
```

uv prepare smoke:

```powershell
cd C:\project\adlight\clipper_electron
node scripts\prepare-uv.mjs win32 x64
```

Expected:

```text
uv-win32-x64.exe -> uv.exe
```

## Build Windows Installer

Run from `clipper_electron`:

```powershell
cd C:\project\adlight\clipper_electron
npm run build:app:win:x64
```

This command performs:

1. Clean Python `__pycache__`.
2. Build Angular renderer from `..\clipper_angular`.
3. Bundle NestJS gateway from `..\clipper_nestjs`.
4. Compile Electron TypeScript.
5. Prepare `resources\bin\uv.exe`.
6. Run `electron-builder --win --x64`.

Expected output directory:

```text
C:\project\adlight\clipper_electron\dist-app\
```

Expected artifact:

```text
Clipper2 Setup 0.0.1.exe
```

Exact filename may vary based on package version.

## Install and Smoke Test

Install the generated `.exe`.

Then verify:

1. App launches without blank white renderer.
2. Main UI loads.
3. Local NestJS gateway starts.
4. Template Builder opens.
5. Official template list loads from DB.
6. Card thumbnails load.
7. Python first-run creates venv:

```text
C:\Users\<USER>\AppData\Roaming\Clipper2\clipper_venv\Scripts\python.exe
```

8. If practical, run one Template Builder preview/sample render smoke.

## Failure Triage

If checkout fails:

- Confirm Mac-side branches were pushed.
- Run `git branch -a`.

If `npm run fetch-uv` fails:

- Check network access to GitHub release downloads.
- Check `tar --version`.
- Check whether antivirus blocked downloaded `.exe`.

If `npm run bundle` fails in `clipper_nestjs`:

- Confirm branch is `feature/windows-packaging`.
- Confirm `scripts/copy-assets.mjs` exists.
- Confirm `src/dance/data` and `src/projects/assets` exist.

If `electron-builder` fails copying `.env.local`:

- Confirm `C:\project\adlight\clipper_nestjs\.env.local` exists.

If installed app opens but Template Builder does not load official templates:

- Inspect packaged NestJS logs.
- Confirm `.env.local` was bundled.
- Confirm DB host is reachable from Windows PC.
- Confirm S3 public URLs are reachable.
- Confirm official template payload font values are S3/http URLs, not local filename-only fonts.

If Python first-run fails:

- Confirm `resources\bin\uv.exe` was included in packaged app.
- Confirm `clipper_python\pyproject.toml` includes `sys_platform == 'win32'`.
- Confirm `clipper_python\uv.lock` includes Windows markers.

## What To Report Back

Report:

- Branch and commit hash of each repo:

```powershell
git -C C:\project\adlight\clipper_electron rev-parse --short HEAD
git -C C:\project\adlight\clipper_nestjs rev-parse --short HEAD
git -C C:\project\adlight\clipper_python rev-parse --short HEAD
git -C C:\project\adlight\clipper_angular rev-parse --short HEAD
```

- Whether `npm run build:app:win:x64` passed.
- Installer filename under `dist-app`.
- Whether installed app launched.
- Whether Template Builder official list loaded.
- Whether Python venv was created under `%APPDATA%\Clipper2\clipper_venv`.
- Any exact error message and the command that produced it.
