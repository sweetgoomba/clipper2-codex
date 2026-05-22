# Clipper2 Windows Build Guide - Configurable Project Root

작성일: 2026-05-20 KST  
대상: Codex 없이 Windows PC에서 사람이 직접 Clipper2 Windows installer를 빌드하는 절차  
기준 문서: `.codex/operations/windows-packaging/runbooks/windows-build-guide.md`
차이점: 프로젝트 루트를 하드코딩하지 않고 현재 PowerShell 위치에서 `$ProjectRoot`를 지정한다.

## 목적

Windows PC에서 프로젝트 루트 생성, repo clone, dependency install, Windows x64 installer build, 기본 smoke test까지 재현한다.

이 문서는 `C:\project\adlight`를 고정 경로로 쓰지 않는다. 먼저 본인 PC의 실제 프로젝트 루트로 이동한 뒤, 현재 위치를 `$ProjectRoot`로 저장하고 이후 명령은 그대로 따라간다.

PowerShell에서 이미 프로젝트 루트로 이동한 상태라면 아래 한 줄로 현재 위치를 프로젝트 루트로 지정한다.

```powershell
$ProjectRoot = (Get-Location).Path
```

## 중요 원칙

### 1. 현재 위치를 프로젝트 루트로 지정한다

모든 명령은 `$ProjectRoot`를 기준으로 실행한다. 먼저 프로젝트 루트 폴더로 이동한 뒤, 현재 위치를 `$ProjectRoot`에 저장한다.

```powershell
$ProjectRoot = (Get-Location).Path
```

다른 PC에서 다른 경로를 써도, 해당 폴더로 이동한 뒤 같은 한 줄을 실행하면 된다.

주의:

- PowerShell 창을 새로 열면 `$ProjectRoot` 값은 사라진다.
- 새 PowerShell 창을 열 때마다 프로젝트 루트로 이동한 뒤 `$ProjectRoot = (Get-Location).Path`를 다시 실행한다.
- 명령을 복사하기 전에 `Write-Output $ProjectRoot`로 현재 값이 맞는지 확인한다.

### 2. 가능하면 ASCII이고 공백 없는 경로를 쓴다

2026-05-20 Windows 세션에서는 한글 사용자명 경로에서 Node/npm native postinstall 문제가 발생했다.

확인된 증상:

- Git `.git/index.lock` permission 문제
- npm native/postinstall 실패
- `EPERM: operation not permitted, lstat 'C:\Users\<한글사용자명>'`
- `0xC0000005 Access Violation`

`C:\Users\bb\Desktop\project\clipper2`처럼 사용자명과 경로가 ASCII이고 공백이 없다면 우선 진행해도 된다. 문제가 나면 `C:\project\clipper2` 같은 더 짧은 ASCII 경로로 옮긴다.

### 3. PowerShell에서는 `npm.cmd`를 사용한다

PowerShell execution policy 때문에 `npm`이 막힐 수 있다. 이 문서는 전부 `npm.cmd`를 사용한다.

### 4. clone 대상은 4개 repo뿐이다

clone할 repo:

```text
clipper_angular
clipper_electron
clipper_nestjs
clipper_python
```

clone하지 않는 repo:

```text
adlight_python
```

현재 Windows packaging flow는 `adlight_python`에 의존하지 않는다.

## 0. PowerShell 열기

일반 PowerShell을 연다.

관리자 권한이 아닌 일반 사용자 권한으로 먼저 시도한다. 폴더 생성이나 설치 경로에서 권한 문제가 나면 그때 관리자 권한을 검토한다.

## 1. 필수 도구 확인

```powershell
git --version
node -v
npm.cmd -v
tar --version
```

2026-05-20 검증 환경:

```text
git version 2.41.0.windows.1
node v22.11.0
npm 10.9.0
bsdtar 3.8.4
```

요구사항:

- Git 설치 필요
- Node.js 22 이상 필요
- npm 사용 가능해야 함
- `tar --version`이 동작해야 함

Node.js가 없거나 22 미만이면 Node.js 22 x64를 설치한 뒤 PowerShell을 새로 열고 다시 확인한다.

## 2. 프로젝트 루트 생성 및 설정

본인 PC의 실제 프로젝트 루트 폴더로 이동한다.

```powershell
Set-Location '<본인 프로젝트 루트 경로>'
```

예를 들어 이미 File Explorer나 터미널에서 프로젝트 루트로 이동해 있다면 `Set-Location`은 생략하고 아래부터 실행한다. 현재 위치를 프로젝트 루트로 지정한다.

```powershell
$ProjectRoot = (Get-Location).Path
```

확인:

```powershell
Write-Output $ProjectRoot
Get-Location
```

둘 다 같은 경로를 가리켜야 한다.

## 3. 4개 repo clone

이미 clone했다면 이 단계는 건너뛰고 4번으로 간다.

```powershell
Set-Location $ProjectRoot
git clone https://github.com/OhMyMetabuzz/clipper_angular.git clipper_angular
git clone https://github.com/OhMyMetabuzz/clipper_electron.git clipper_electron
git clone https://github.com/OhMyMetabuzz/clipper_nestjs.git clipper_nestjs
git clone https://github.com/OhMyMetabuzz/clipper_python.git clipper_python
```

확인:

```powershell
Get-ChildItem $ProjectRoot
```

기대되는 폴더:

```text
clipper_angular
clipper_electron
clipper_nestjs
clipper_python
```

## 4. Branch checkout

### Angular

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_angular')
git fetch
git checkout feature/initial-scaffold
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대 HEAD:

```text
4501146
```

### Electron

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대 HEAD:

```text
e264865
```

### NestJS

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대 HEAD:

```text
c33fbd8
```

### Python

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_python')
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대 HEAD:

```text
5a61a62
```

브랜치가 없거나 checkout이 실패하면 해당 branch/commit이 remote에 push되어 있는지 먼저 확인한다.

## 5. NestJS env 파일 준비

Windows packaged build에는 다음 파일이 필요하다.

```powershell
$NestEnv = Join-Path $ProjectRoot 'clipper_nestjs\.env.local'
Write-Output $NestEnv
```

파일을 편집한다.

```powershell
notepad $NestEnv
```

이 파일에는 DB/S3 등 Template Builder official data에 필요한 환경변수가 들어가야 한다. 비밀값은 문서, 채팅, git commit에 남기지 않는다.

저장 후 존재 여부만 확인한다. 내용을 출력하지 않는다.

```powershell
Get-Item $NestEnv | Select-Object FullName,Length,LastWriteTime
```

중요:

- `clipper_python\.env`는 현재 packaged build 기준 필수 파일이 아니다.
- `clipper_nestjs\.env.local`만 있어도 2026-05-20 smoke는 통과했다.
- `%APPDATA%\Clipper2\.env`는 repo 파일이 아니라 설치된 앱의 user override 파일이다.

## 6. Node dependencies 설치

workspace 안의 npm cache를 사용한다.

```powershell
$NpmCache = Join-Path $ProjectRoot '.npm-cache'
Write-Output $NpmCache
```

### Angular

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_angular')
npm.cmd install --cache $NpmCache
```

### NestJS

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
npm.cmd install --cache $NpmCache
```

### Electron

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
npm.cmd install --cache $NpmCache
```

참고:

- `npm audit` 취약점 경고는 나올 수 있다.
- 이번 build smoke에서는 `npm audit fix`를 실행하지 않는다.
- `npm install` 후 `package-lock.json`이 변경될 수 있다. 나중에 별도로 검토한다.

## 7. uv binary 다운로드

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
npm.cmd run fetch-uv
```

확인:

```powershell
Get-ChildItem (Join-Path $ProjectRoot 'clipper_electron\resources\bin')
```

중요 파일:

```text
uv-win32-x64.exe
```

Windows build용 `uv.exe` 준비 smoke:

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
node scripts\prepare-uv.mjs win32 x64
```

기대 출력:

```text
uv-win32-x64.exe -> uv.exe
```

## 8. Preflight build

최종 installer build 전에 각 단계를 따로 실행해 실패 위치를 분리한다.

### 8.1 Angular electron build

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_angular')
npm.cmd run build:electron -- --progress=false
```

기대 출력 일부:

```text
Application bundle generation complete.
```

### 8.2 NestJS bundle

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
npm.cmd run bundle
```

기대 출력 일부:

```text
ncc build src/main.ts -o dist/bundled
```

### 8.3 Electron TypeScript build

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
npm.cmd run build
```

기대 출력:

```text
tsc -p tsconfig.json
```

### 8.4 uv prepare 재확인

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
node scripts\prepare-uv.mjs win32 x64
```

## 9. Windows installer build

최종 build는 `clipper_electron`에서 실행한다.

```powershell
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
npm.cmd run build:app:win:x64
```

내부적으로 다음이 실행된다.

1. Python `__pycache__` cleanup
2. Angular build
3. NestJS bundle
4. Electron TypeScript compile
5. `resources\bin\uv.exe` 준비
6. `electron-builder --win --x64`

성공 시 마지막 출력:

```text
Done. Artifacts in dist-app/
```

## 10. 산출물 확인

```powershell
$ElectronRoot = Join-Path $ProjectRoot 'clipper_electron'
Set-Location $ElectronRoot
Get-ChildItem .\dist-app
```

기대 파일:

```text
Clipper2 Setup 0.0.1.exe
Clipper2 Setup 0.0.1.exe.blockmap
latest.yml
win-unpacked
```

installer 확인:

```powershell
Get-Item '.\dist-app\Clipper2 Setup 0.0.1.exe' | Select-Object FullName,Length,LastWriteTime
```

2026-05-20 기준 size:

```text
165,487,916 bytes
```

packaged resource 확인:

```powershell
Test-Path '.\dist-app\win-unpacked\resources\bin\uv.exe'
Test-Path '.\dist-app\win-unpacked\resources\clipper_nestjs\.env.local'
```

기대값:

```text
True
True
```

## 11. 설치 smoke

### 옵션 A. GUI로 설치

File Explorer에서 installer를 실행한다.

```powershell
$Installer = Join-Path $ProjectRoot 'clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe'
Write-Output $Installer
```

가능하면 설치 경로를 프로젝트 루트 아래 smoke 폴더로 지정한다.

```powershell
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
Write-Output $InstallDir
```

설치 후 확인:

```powershell
Test-Path (Join-Path $InstallDir 'Clipper2.exe')
```

기대값:

```text
True
```

### 옵션 B. silent install

2026-05-20 세션에서는 silent install command가 timeout에 걸렸지만 설치 결과물은 정상 생성됐다. 오래 걸리면 중단 후 설치 폴더 존재 여부를 확인한다.

```powershell
$Installer = Join-Path $ProjectRoot 'clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe'
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
Start-Process -FilePath $Installer -ArgumentList "/S /D=$InstallDir" -Wait
```

확인:

```powershell
Test-Path (Join-Path $InstallDir 'Clipper2.exe')
Get-ChildItem $InstallDir
```

## 12. 앱 첫 실행 smoke

설치된 앱 실행:

```powershell
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
$ClipperExe = Join-Path $InstallDir 'Clipper2.exe'
Start-Process $ClipperExe
```

첫 실행은 Python venv 생성 때문에 시간이 걸릴 수 있다. 2분 정도 기다린 뒤 확인한다.

```powershell
Test-Path "$env:APPDATA\Clipper2\clipper_venv\Scripts\python.exe"
Test-Path "$env:APPDATA\Clipper2\logs\main.log"
```

기대값:

```text
True
True
```

log 확인:

```powershell
Get-Content "$env:APPDATA\Clipper2\logs\main.log" -Tail 120
```

기대되는 line:

```text
[setup] Python env ready.
[PluginHostBridge] listening on http://127.0.0.1:<port>
[window] showing main window
[NestManager] ready at http://127.0.0.1:<port>/v1
```

## 13. API smoke

먼저 기존 Clipper2 process가 있으면 종료한다.

```powershell
Get-Process Clipper2 -ErrorAction SilentlyContinue | Stop-Process -Force
```

그 다음 아래 script를 PowerShell에 붙여넣어 실행한다. `$ProjectRoot`가 현재 PowerShell에 설정되어 있어야 한다.

```powershell
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
$exe = Join-Path $InstallDir 'Clipper2.exe'
$log = Join-Path $env:APPDATA 'Clipper2\logs\main.log'

if (-not (Test-Path -LiteralPath $exe)) {
  throw "Clipper2.exe not found: $exe"
}

$lineCount = 0
if (Test-Path -LiteralPath $log) {
  $lineCount = (Get-Content -LiteralPath $log).Count
}

$p = Start-Process -FilePath $exe -PassThru

try {
  $baseUrl = $null

  for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 1

    if (Test-Path -LiteralPath $log) {
      $newLines = Get-Content -LiteralPath $log | Select-Object -Skip $lineCount
      foreach ($line in $newLines) {
        if ($line -match 'NestManager\] ready at (http://127\.0\.0\.1:\d+/v1)') {
          $baseUrl = $Matches[1]
        }
      }
      if ($baseUrl) {
        break
      }
    }
  }

  if (-not $baseUrl) {
    throw 'BASE_URL_NOT_FOUND'
  }

  Write-Output "BASE_URL=$baseUrl"

  $health = Invoke-WebRequest -UseBasicParsing "$baseUrl/health" -TimeoutSec 10
  Write-Output "HEALTH_STATUS=$($health.StatusCode)"

  $familiesResponse = Invoke-WebRequest -UseBasicParsing "$baseUrl/template-builder/families" -TimeoutSec 30
  Write-Output "FAMILIES_STATUS=$($familiesResponse.StatusCode)"

  $families = $familiesResponse.Content | ConvertFrom-Json
  if ($families -is [array]) {
    Write-Output "FAMILIES_COUNT=$($families.Count)"
  } else {
    Write-Output 'FAMILIES_COUNT=1'
  }
}
finally {
  $running = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
  if ($running) {
    Stop-Process -Id $p.Id -Force
  }
}
```

성공 예:

```text
BASE_URL=http://127.0.0.1:64441/v1
HEALTH_STATUS=200
FAMILIES_STATUS=200
FAMILIES_COUNT=24
```

port는 실행마다 달라질 수 있다.

## 14. UI smoke

API smoke 후 사람이 직접 확인한다.

```powershell
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
Start-Process (Join-Path $InstallDir 'Clipper2.exe')
```

확인할 것:

1. 앱이 흰 화면에서 멈추지 않고 열린다.
2. 메인 UI가 표시된다.
3. Template Builder 화면을 열 수 있다.
4. official template list가 로드된다.
5. card thumbnails가 보인다.
6. 템플릿 하나를 선택했을 때 preview text가 보인다.
7. text artifact 변환 이후에도 한글 font가 정상 표시된다.
8. 가능하면 sample render를 한 번 실행한다.

## 15. 최종 repo 상태 확인

```powershell
$AngularRoot = Join-Path $ProjectRoot 'clipper_angular'
$ElectronRoot = Join-Path $ProjectRoot 'clipper_electron'
$NestRoot = Join-Path $ProjectRoot 'clipper_nestjs'
$PythonRoot = Join-Path $ProjectRoot 'clipper_python'

git -C $AngularRoot status --short --branch
git -C $ElectronRoot status --short --branch
git -C $NestRoot status --short --branch
git -C $PythonRoot status --short --branch
```

`npm install` 후 다음 파일이 modified로 표시될 수 있다.

```text
clipper_angular\package-lock.json
clipper_electron\package-lock.json
```

2026-05-20 세션에서도 이 두 lockfile이 modified 상태였다. 이 변경은 바로 커밋하지 말고 별도 검토 후 유지/되돌림을 결정한다.

## 16. 결과 보고 시 포함할 내용

```powershell
$AngularRoot = Join-Path $ProjectRoot 'clipper_angular'
$ElectronRoot = Join-Path $ProjectRoot 'clipper_electron'
$NestRoot = Join-Path $ProjectRoot 'clipper_nestjs'
$PythonRoot = Join-Path $ProjectRoot 'clipper_python'

git -C $AngularRoot rev-parse --short HEAD
git -C $ElectronRoot rev-parse --short HEAD
git -C $NestRoot rev-parse --short HEAD
git -C $PythonRoot rev-parse --short HEAD
```

보고 항목:

- `$ProjectRoot` 값
- Node/npm/tar version
- 각 repo branch/HEAD
- `npm install` 성공 여부
- `npm.cmd run fetch-uv` 성공 여부
- preflight build 성공 여부
- `npm.cmd run build:app:win:x64` 성공 여부
- installer 파일명과 size
- app 실행 여부
- `%APPDATA%\Clipper2\clipper_venv\Scripts\python.exe` 생성 여부
- `/v1/health` status
- `/v1/template-builder/families` status 및 count
- UI에서 Template Builder list/thumbnail/text artifact가 보이는지
- 실패 시 정확한 command와 error message

## Troubleshooting

### `$ProjectRoot`가 비어 있거나 명령이 이상한 경로로 감

확인:

```powershell
Write-Output $ProjectRoot
Get-Location
```

해결:

```powershell
$ProjectRoot = (Get-Location).Path
```

PowerShell을 새로 열었다면 `$ProjectRoot`를 다시 설정해야 한다.

### `npm` 실행이 PowerShell policy로 막힘

증상:

```text
npm : 이 시스템에서 스크립트를 실행할 수 없으므로 npm.ps1 파일을 로드할 수 없습니다.
```

해결:

```powershell
npm.cmd -v
npm.cmd install --cache $NpmCache
```

이 문서의 모든 npm command는 `npm.cmd`를 사용한다.

### 한글 사용자명 경로에서 Node/npm이 crash

증상:

- `0xC0000005`
- `-1073741819`
- `EPERM: operation not permitted, lstat 'C:\Users\<한글사용자명>'`
- `esbuild`, `@parcel/watcher`, `lmdb`, `msgpackr-extract` postinstall 실패

해결:

- `$ProjectRoot`를 `C:\project\clipper2` 같은 짧은 ASCII 경로로 바꾼다.
- npm cache도 `$NpmCache = Join-Path $ProjectRoot '.npm-cache'`를 사용한다.

### `.env.local` 없음

증상:

- build 중 `clipper_nestjs\.env.local` extraResource copy 실패 가능
- app은 떠도 Template Builder official data가 로드되지 않을 수 있음

해결:

```powershell
$NestEnv = Join-Path $ProjectRoot 'clipper_nestjs\.env.local'
notepad $NestEnv
Get-Item $NestEnv | Select-Object FullName,Length,LastWriteTime
```

비밀값은 출력하지 않는다.

### API smoke가 stale port를 읽음

이전 실행 log의 `NestManager ready` line을 읽으면 이미 종료된 port로 health check를 시도해 실패할 수 있다.

해결:

- API smoke script처럼 실행 전 log line count를 저장한다.
- app 실행 후 새로 추가된 line에서만 base URL을 찾는다.

### installer silent install이 오래 걸림

확인:

```powershell
$InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
Test-Path (Join-Path $InstallDir 'Clipper2.exe')
Get-Process | Where-Object { $_.ProcessName -like '*Clipper*' -or $_.ProcessName -like '*Setup*' }
```

GUI 설치로 다시 확인해도 된다.

## 이 문서에서 아직 보장하지 않는 것

다음은 Windows installer build 이후 별도 QA가 필요하다.

- code signing
- app icon
- SmartScreen 대응
- auto-update
- CUDA acceleration
- full Dialog/Dance workflow E2E
- Template Builder sample render 전체 성공
- plugin start/stop 전체 matrix
