# Windows Release Runner Docker + Code Signing Verification

Date: 2026-06-29

Status update, 2026-06-30:

- This document preserves the Windows container and CodeSignTool verification
  history from 2026-06-29.
- The old pull/claim runner architecture described below was superseded on
  2026-06-30.
- Current flow is direct start:
  `Admin UI -> clipper_web_api -> Windows runner container /jobs/start`, with
  runner callbacks to `clipper_web_api /release-runner/jobs/:id/report`.
- Latest operational handoff is
  [../../handoff/NEXT.md](../../handoff/NEXT.md), and the full cross-day session
  record is [../../records/sessions/2026/06/30.md](../../records/sessions/2026/06/30.md).

## Purpose

관리자 버전관리 페이지의 `빌드 시작` 흐름을 실제 Windows runner까지 연결하기 전에,
Windows PC에서 Docker Windows container와 SSL.com `CodeSignTool-v1.3.2-windows`가
무인 서명에 사용할 수 있는지 검증했다.

이번 문서는 구현 완료 문서가 아니라 검증 결과와 다음 구현 기준을 남기는 runbook이다.

## Current Repo Branches

작업 기준 브랜치:

```text
web/clipper_web_admin: feat/release-management-runtime
  latest local/origin: 7b9a21e feat: connect version console to release runtime

web/clipper_web_api: feat/release-management-runtime
  latest local/origin: 86289a0 feat: add release management runtime

web/clipper_infra: feat/release-management-runtime
  latest local/origin: 2d61769 fix: allow node 22 for windows runner
```

`dev`/`main`은 이 작업 중 건드리지 않았다.

## Important Architecture Point

현재 `web/clipper_infra/runner/release-runner.mjs`는 runner가 API에
`/release-runner/jobs/claim`을 호출해 작업을 가져오는 pull 방식이다.

사용자는 이 네트워크 흐름은 아직 더 고민하겠다고 했다. 따라서 다음 구현에서는
새로운 push 방식으로 바꾸기 전에 반드시 사용자와 다시 합의한다.

현재 확인된 release runner 목표 흐름:

```text
admin UI
  -> clipper_web_api build job 생성

Windows runner container
  -> API에서 job claim
  -> source snapshot commit으로 checkout
  -> Windows installer build
  -> CodeSignTool로 signing
  -> artifact upload/report
```

## Windows Container Requirements Learned

Windows container는 Windows Home/Core에서 사용할 수 없다.

확인 결과:

- Windows 11 Home/Core PC:
  - Docker CLI/host build는 가능할 수 있으나 Windows containers 불가.
  - Windows release runner Docker 검증용으로는 부적합.
- Windows 10 Pro 19045 PC:
  - Docker Desktop all-users install + `Allow Windows Containers` 필요.
  - `Containers` Windows feature enabled 필요.
  - `Microsoft-Hyper-V-All` enabled 필요.
  - Docker engine 전환 후 `docker info --format '{{.OSType}}'`가 `windows`여야 한다.

Windows 10 Pro 19045에서는 `servercore:ltsc2022`가 맞지 않았다.
검증 기준 image는 `mcr.microsoft.com/windows/servercore:ltsc2019`다.

검증 명령:

```powershell
docker info --format '{{.OSType}}'
docker run --rm --isolation=hyperv mcr.microsoft.com/windows/servercore:ltsc2019 cmd /c ver
```

통과 결과:

```text
docker OSType: windows
container: Microsoft Windows [Version 10.0.17763.8880]
```

## Verified Windows Runner Candidate

검증된 runner 후보 PC 경로:

```text
C:\Users\Metabuzz00\Desktop\project\clipper
```

CodeSignTool 경로:

```text
C:\tools\CodeSignTool-v1.3.2-windows
```

CodeSignTool 구조:

```text
C:\tools\CodeSignTool-v1.3.2-windows\CodeSignTool.bat
C:\tools\CodeSignTool-v1.3.2-windows\conf\
C:\tools\CodeSignTool-v1.3.2-windows\jar\
C:\tools\CodeSignTool-v1.3.2-windows\jdk-11.0.2\
```

Node:

```text
v22.22.2
npm 10.9.7
```

Node 24 was present on the PC, but runner checks and build flow use Node 22.x.

## Host Workspace Setup Commands

```powershell
cd C:\Users\Metabuzz00\Desktop\project\clipper
New-Item -ItemType Directory -Force desktop
New-Item -ItemType Directory -Force web

cd C:\Users\Metabuzz00\Desktop\project\clipper\desktop
git clone -b dev https://github.com/OhMyMetabuzz/clipper_angular.git
git clone -b dev https://github.com/OhMyMetabuzz/clipper_electron.git
git clone -b dev https://github.com/OhMyMetabuzz/clipper_nestjs.git
git clone -b dev https://github.com/OhMyMetabuzz/clipper_python.git

cd C:\Users\Metabuzz00\Desktop\project\clipper\web
git clone -b feat/release-management-runtime https://github.com/OhMyMetabuzz/clipper_infra.git
git clone -b dev https://github.com/OhMyMetabuzz/clipper_web_api.git
```

Runner preflight:

```powershell
cd C:\Users\Metabuzz00\Desktop\project\clipper\web\clipper_infra
powershell -ExecutionPolicy Bypass -File runner\windows\check-windows-runner.ps1 -WorkspaceRoot C:\Users\Metabuzz00\Desktop\project\clipper -FailOnMissingRepos
```

Initial failure was expected until Node and env files were prepared.

Env setup:

```powershell
powershell -ExecutionPolicy Bypass -File runner\windows\prepare-windows-env.ps1 -WorkspaceRoot C:\Users\Metabuzz00\Desktop\project\clipper -RunnerToken <RUNNER_TOKEN>
```

After setup, `check-windows-runner.ps1 -FailOnMissingRepos` passed.

Dependency install and host smoke build:

```powershell
powershell -ExecutionPolicy Bypass -File runner\windows\install-windows-deps.ps1 -WorkspaceRoot C:\Users\Metabuzz00\Desktop\project\clipper
powershell -ExecutionPolicy Bypass -File runner\windows\build-windows-smoke.ps1 -WorkspaceRoot C:\Users\Metabuzz00\Desktop\project\clipper
```

Host smoke build passed and produced:

```text
desktop\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
```

Note: electron-builder printed `no signing info identified, signing is skipped`.
That is expected for this smoke step because SSL.com signing is tested separately.

## Electron Builder Symlink Issue

First host smoke build failed while extracting `winCodeSign-2.6.0.7z`:

```text
ERROR: Cannot create symbolic link ... libcrypto.dylib
ERROR: Cannot create symbolic link ... libssl.dylib
```

Cause:

- electron-builder's `winCodeSign` cache contains symlinks.
- Current Windows session lacked symlink creation permission.

Resolution used:

- Run PowerShell with elevated/admin permissions or enable Developer Mode.
- Delete corrupted cache before retry:

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -ErrorAction SilentlyContinue
```

The subsequent smoke build passed.

## CodeSignTool Findings

`CodeSignTool-v1.3.2-windows` is not tied to local Windows certificate store,
USB token, or GUI prompt in the tested flow.

It is a CLI wrapper:

```text
CodeSignTool.bat -> bundled JDK -> jar\code_sign_tool-1.3.2.jar
```

It uses SSL.com remote CSC signing:

```text
OAuth2 endpoint: https://login.ssl.com/oauth2/token
CSC endpoint:   https://cs.ssl.com
TSA URL:        http://ts.ssl.com
```

`sign --help` requires:

```text
-username
-password
-credential_id
-totp_secret
-input_file_path
-output_dir_path
```

Required runner env variable names for our automation:

```text
CLIPPER_CODESIGN_USERNAME
CLIPPER_CODESIGN_PASSWORD
CLIPPER_CODESIGN_CREDENTIAL_ID
CLIPPER_CODESIGN_TOTP_SECRET
```

Do not commit these values.

The old `sign-and-publish.js` copied into the Mac workspace contained the
needed values. That file is secret-bearing and must not be committed or printed.

## Docker CodeSignTool Help Test

Command:

```powershell
docker run --rm --isolation=hyperv -v "C:\tools\CodeSignTool-v1.3.2-windows:C:\host-tools\codesign:ro" mcr.microsoft.com/windows/servercore:ltsc2019 powershell -NoProfile -Command "Copy-Item -Recurse 'C:\host-tools\codesign' 'C:\tools\codesign'; New-Item -ItemType Directory -Force -Path 'C:\tools\codesign\logs' | Out-Null; Set-Location 'C:\tools\codesign'; .\CodeSignTool.bat --help; .\CodeSignTool.bat sign --help"
```

Result:

```text
CodeSignTool --help: pass
CodeSignTool sign --help: pass
logs permission error: none
```

The tool is mounted read-only from host and copied to a writable container path
before execution, because the tool writes under its own `logs` directory.

## Docker Code Signing Test

Test input was copied from the smoke build output:

```powershell
New-Item -ItemType Directory -Force C:\codesign-test\input
New-Item -ItemType Directory -Force C:\codesign-test\output
Copy-Item "C:\Users\Metabuzz00\Desktop\project\clipper\desktop\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe" "C:\codesign-test\input\Clipper2-Setup-unsigned.exe" -Force
```

Secrets were set only in the current PowerShell session:

```powershell
$env:CLIPPER_CODESIGN_USERNAME="..."
$env:CLIPPER_CODESIGN_PASSWORD="..."
$env:CLIPPER_CODESIGN_CREDENTIAL_ID="..."
$env:CLIPPER_CODESIGN_TOTP_SECRET="..."
```

Signing command:

```powershell
docker run --rm --isolation=hyperv -v "C:\tools\CodeSignTool-v1.3.2-windows:C:\host-tools\codesign:ro" -v "C:\codesign-test:C:\work" -e CLIPPER_CODESIGN_USERNAME -e CLIPPER_CODESIGN_PASSWORD -e CLIPPER_CODESIGN_CREDENTIAL_ID -e CLIPPER_CODESIGN_TOTP_SECRET mcr.microsoft.com/windows/servercore:ltsc2019 powershell -NoProfile -Command "Copy-Item -Recurse 'C:\host-tools\codesign' 'C:\tools\codesign'; New-Item -ItemType Directory -Force -Path 'C:\tools\codesign\logs','C:\work\output' | Out-Null; Set-Location 'C:\tools\codesign'; .\CodeSignTool.bat sign -username=$env:CLIPPER_CODESIGN_USERNAME -password=$env:CLIPPER_CODESIGN_PASSWORD -credential_id=$env:CLIPPER_CODESIGN_CREDENTIAL_ID -totp_secret=$env:CLIPPER_CODESIGN_TOTP_SECRET -input_file_path='C:\work\input\Clipper2-Setup-unsigned.exe' -output_dir_path='C:\work\output'"
```

Result:

```text
Code signed successfully: C:\work\output\Clipper2-Setup-unsigned.exe
```

Host signature check:

```powershell
Get-AuthenticodeSignature "C:\codesign-test\output\Clipper2-Setup-unsigned.exe" | Format-List
```

Result:

```text
Status: Valid
Signer: CN="METABUZZ Co.,Ltd", O="METABUZZ Co.,Ltd", L=Gangnam-gu, S=Seoul, C=KR
Timestamp: present, SSL.com Timestamping Unit 2025 E1
```

This verifies Windows container + CodeSignTool actual signing end-to-end.

## Temporary Files Created On Mac

For copying commands to the Windows PC, these non-secret helper files were
created at workspace root:

```text
/Users/jina/project/adlight/docker-codesign-help-command.txt
/Users/jina/project/adlight/docker-codesign-sign-command.txt
```

They contain commands only and no secret values.

The old files copied from the prior runner PC are secret-sensitive:

```text
/Users/jina/project/adlight/sign-and-publish.js
/Users/jina/project/adlight/code_signing_tool-2025-11-03.log
```

Do not commit them. The log contains credential IDs and signature material; the
script contains actual SSL.com credentials.

## Next Implementation Work

Implement in `web/clipper_infra`:

1. Windows runner Dockerfile based on `mcr.microsoft.com/windows/servercore:ltsc2019`.
2. Container entrypoint script.
3. Artifact signing script that:
   - copies mounted CodeSignTool to writable container path,
   - signs installer artifacts,
   - verifies Authenticode status,
   - fails loudly if signing status is not valid.
4. Runner launch script/runbook that mounts:
   - workspace root,
   - CodeSignTool directory,
   - runner env/secrets,
   - optional artifact output directory.
5. Integrate signing after `npm run build:app:win:x64` in the release runner flow.
6. Report `signatureStatus=signed` only after Authenticode verification passes.
7. Keep secret values out of repo and logs.

Open decisions before end-to-end implementation:

- Pull claim flow vs. direct push command from API/admin to runner.
- Where to store runner secrets for operations:
  - local env file,
  - Windows Credential Manager,
  - Docker secret-like mounted file,
  - another secret manager.
- S3/public artifact upload details for dev/stage/prod buckets.
- macOS runner signing/notarization is separate and still needs macOS host work.
