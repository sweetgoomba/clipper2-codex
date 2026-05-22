# Clipper2 Windows Build Guide

작성일: 2026-05-20 KST  
대상: Codex 없이 Windows PC에서 사람이 직접 처음부터 Clipper2 Windows installer를 빌드하는 절차  
검증 기준 세션: `.codex/implementation/2026-05-20-windows-build-session-report.md`

## 목적

새 Windows PC에서 프로젝트 루트 생성부터 repo clone, dependency install, Windows x64 installer build, 기본 smoke test까지 같은 순서로 재현한다.

이번 가이드는 2026-05-20 Windows PC 세션에서 실제로 통과한 절차를 기준으로 한다.

최종 목표 산출물:

```text
C:\project\adlight\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
```

## 중요 원칙

### 1. ASCII 경로를 사용한다

반드시 다음처럼 한글/공백이 없는 경로에서 진행한다.

```text
C:\project\adlight
```

피해야 할 예:

```text
C:\Users\<한글사용자명>\Desktop\project\adlight
```

2026-05-20 세션에서는 한글 사용자명 경로에서 다음 문제가 발생했다.

- Git `.git/index.lock` permission 문제
- npm native/postinstall 실패
- `node .\node_modules\esbuild\install.js`가 상위 사용자 폴더 `lstat`에서 `EPERM`
- Node/native executable `0xC0000005 Access Violation` 계열 crash

따라서 다른 Windows PC에서도 `C:\project\adlight` 같은 ASCII 경로를 우선 사용한다.

### 2. clone 대상은 4개 repo뿐이다

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

### 3. PowerShell에서는 `npm.cmd`를 사용한다

Windows PowerShell execution policy 때문에 `npm`이 `npm.ps1` 로딩 오류로 막힐 수 있다.

따라서 이 가이드에서는 전부 `npm.cmd`를 사용한다.

## 0. PowerShell 열기

일반 PowerShell을 연다.

가능하면 관리자 권한이 아닌 일반 사용자 권한으로 먼저 시도한다.  
`C:\project` 생성이 권한 문제로 실패하면 그때 관리자 권한 PowerShell을 사용하거나, File Explorer에서 `C:\project` 폴더를 만든 뒤 현재 사용자에게 쓰기 권한을 준다.

이후 모든 명령은 PowerShell 기준이다.

## 1. 필수 도구 확인

다음 명령을 실행한다.

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

### 1.1 Node.js 22 설치가 필요한 경우

다음 중 하나면 Node.js 22 이상을 먼저 설치한다.

- `node -v`가 명령을 찾지 못함.
- `node -v`가 `v18...`, `v20...`처럼 22 미만으로 나옴.
- `npm.cmd -v`가 명령을 찾지 못함.

2026-05-20 검증에 사용한 버전은 다음이다.

```text
node v22.11.0
npm 10.9.0
```

#### 설치 방법 A: 공식 MSI installer

브라우저에서 Node.js v22.11.0 Windows x64 installer를 받는다.

```text
https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi
```

설치 시 기본 옵션을 사용해도 된다.  
설치가 끝나면 기존 PowerShell을 닫고 새 PowerShell을 연다.

새 PowerShell에서 다시 확인한다.

```powershell
node -v
npm.cmd -v
where.exe node
where.exe npm
```

기대값 예:

```text
v22.11.0
10.9.0
C:\Program Files\nodejs\node.exe
C:\Program Files\nodejs\npm
C:\Program Files\nodejs\npm.cmd
```

#### 설치 방법 B: winget 사용

`winget`을 사용할 수 있으면 아래처럼 설치할 수도 있다.

```powershell
winget install --id OpenJS.NodeJS --version 22.11.0 --exact
```

설치 후 기존 PowerShell을 닫고 새 PowerShell을 열어 다시 확인한다.

```powershell
node -v
npm.cmd -v
where.exe node
where.exe npm
```

`winget`이 해당 exact version을 찾지 못하면 설치 방법 A의 공식 MSI installer를 사용한다.

주의:

- PowerShell에서 `npm -v`가 execution policy 오류로 실패할 수 있다.
- 이 경우 Node/npm 설치 실패가 아니라 `npm.ps1` 실행 정책 문제일 수 있다.
- 이 가이드에서는 항상 `npm.cmd`를 사용한다.

## 2. 프로젝트 루트 생성

```powershell
New-Item -ItemType Directory -Force C:\project\adlight
Set-Location C:\project\adlight
```

확인:

```powershell
Get-Location
```

기대값:

```text
Path
----
C:\project\adlight
```

## 3. 4개 repo clone

```powershell
git clone https://github.com/OhMyMetabuzz/clipper_angular.git clipper_angular
git clone https://github.com/OhMyMetabuzz/clipper_electron.git clipper_electron
git clone https://github.com/OhMyMetabuzz/clipper_nestjs.git clipper_nestjs
git clone https://github.com/OhMyMetabuzz/clipper_python.git clipper_python
```

확인:

```powershell
Get-ChildItem C:\project\adlight
```

기대되는 폴더:

```text
clipper_angular
clipper_electron
clipper_nestjs
clipper_python
```

## 4. branch checkout

### Angular

```powershell
Set-Location C:\project\adlight\clipper_angular
git fetch
git checkout feature/initial-scaffold
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대값:

```text
## feature/initial-scaffold...origin/feature/initial-scaffold
4501146
```

### Electron

```powershell
Set-Location C:\project\adlight\clipper_electron
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대값:

```text
## feature/windows-packaging...origin/feature/windows-packaging
e264865
```

### NestJS

```powershell
Set-Location C:\project\adlight\clipper_nestjs
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대값:

```text
## feature/windows-packaging...origin/feature/windows-packaging
c33fbd8
```

### Python

```powershell
Set-Location C:\project\adlight\clipper_python
git fetch
git checkout feature/windows-packaging
git status --short --branch
git rev-parse --short HEAD
```

2026-05-20 기준 기대값:

```text
## feature/windows-packaging...origin/feature/windows-packaging
5a61a62
```

브랜치가 없거나 checkout이 실패하면 Mac mini 쪽 commit/branch가 remote에 push되어 있는지 먼저 확인해야 한다.

## 5. NestJS env 파일 준비

Windows packaged build에는 다음 파일이 필요하다.

```text
C:\project\adlight\clipper_nestjs\.env.local
```

이 파일에는 DB/S3 등 Template Builder official data에 필요한 환경변수가 들어가야 한다.  
비밀값은 문서, 채팅, git commit에 남기지 않는다.

파일을 편집하려면:

```powershell
notepad C:\project\adlight\clipper_nestjs\.env.local
```

저장 후 존재 여부만 확인한다. 내용을 출력하지 않는다.

```powershell
Get-Item C:\project\adlight\clipper_nestjs\.env.local | Select-Object FullName,Length,LastWriteTime
```

중요:

- `clipper_python\.env`는 현재 packaged build 기준 필수 파일이 아니다.
- `clipper_nestjs\.env.local`만 있어도 2026-05-20 smoke는 통과했다.
- `%APPDATA%\Clipper2\.env`는 repo 파일이 아니라 설치된 앱의 user override 파일이다.

## 6. Node dependencies 설치

workspace 안의 npm cache를 사용한다.  
이렇게 하면 한글 사용자명 아래 npm cache/log 경로 문제를 피할 수 있다.

### Angular

```powershell
Set-Location C:\project\adlight\clipper_angular
npm.cmd install --cache C:\project\adlight\.npm-cache
```

성공하면 `added ... packages`가 출력된다.

### NestJS

```powershell
Set-Location C:\project\adlight\clipper_nestjs
npm.cmd install --cache C:\project\adlight\.npm-cache
```

성공하면 `added ... packages`가 출력된다.

### Electron

```powershell
Set-Location C:\project\adlight\clipper_electron
npm.cmd install --cache C:\project\adlight\.npm-cache
```

성공하면 `added ... packages`가 출력된다.

참고:

- `npm audit` 취약점 경고는 나올 수 있다.
- 이번 build smoke에서는 `npm audit fix`를 실행하지 않는다.
- `npm install` 후 `package-lock.json`이 변경될 수 있다. 나중에 별도로 검토한다.

## 7. uv binary 다운로드

```powershell
Set-Location C:\project\adlight\clipper_electron
npm.cmd run fetch-uv
```

기대 출력:

```text
Downloading uv-darwin-arm64...
✓ uv-darwin-arm64
Downloading uv-darwin-x64...
✓ uv-darwin-x64
Downloading uv-win32-x64.exe...
✓ uv-win32-x64.exe
```

확인:

```powershell
Get-ChildItem C:\project\adlight\clipper_electron\resources\bin
```

중요 파일:

```text
uv-win32-x64.exe
```

Windows build용 `uv.exe` 준비 smoke:

```powershell
Set-Location C:\project\adlight\clipper_electron
node scripts\prepare-uv.mjs win32 x64
```

기대 출력:

```text
✓ uv-win32-x64.exe → uv.exe
```

## 8. Preflight build

최종 installer build 전에 각 단계를 따로 실행해 실패 위치를 분리한다.

### 8.1 Angular electron build

```powershell
Set-Location C:\project\adlight\clipper_angular
npm.cmd run build:electron -- --progress=false
```

기대 출력 일부:

```text
Application bundle generation complete.
Output location: C:\project\adlight\clipper_angular\dist\clipper_angular
```

### 8.2 NestJS bundle

```powershell
Set-Location C:\project\adlight\clipper_nestjs
npm.cmd run bundle
```

기대 출력 일부:

```text
ncc build src/main.ts -o dist/bundled
copied C:\project\adlight\clipper_nestjs\src\dance\data -> ...
copied C:\project\adlight\clipper_nestjs\src\projects\assets -> ...
```

### 8.3 Electron TypeScript build

```powershell
Set-Location C:\project\adlight\clipper_electron
npm.cmd run build
```

기대 출력:

```text
tsc -p tsconfig.json
```

### 8.4 uv prepare 재확인

```powershell
Set-Location C:\project\adlight\clipper_electron
node scripts\prepare-uv.mjs win32 x64
```

기대 출력:

```text
✓ uv-win32-x64.exe → uv.exe
```

## 9. Windows installer build

최종 build는 `clipper_electron`에서 실행한다.

```powershell
Set-Location C:\project\adlight\clipper_electron
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
✓ Done. Artifacts in dist-app/
```

## 10. 산출물 확인

```powershell
Set-Location C:\project\adlight\clipper_electron
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

File Explorer에서 다음 파일을 실행한다.

```text
C:\project\adlight\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
```

가능하면 설치 경로를 다음처럼 지정한다.

```text
C:\project\adlight\clipper2-smoke-install
```

설치 후 확인:

```powershell
Test-Path 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
```

기대값:

```text
True
```

### 옵션 B. silent install

2026-05-20 세션에서는 silent install command가 timeout에 걸렸지만 설치 결과물은 정상 생성됐다.  
다른 PC에서도 command가 오래 걸리면 중단 후 설치 폴더 존재 여부를 확인한다.

```powershell
$installer = 'C:\project\adlight\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe'
$installDir = 'C:\project\adlight\clipper2-smoke-install'
Start-Process -FilePath $installer -ArgumentList "/S /D=$installDir" -Wait
```

확인:

```powershell
Test-Path 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
Get-ChildItem 'C:\project\adlight\clipper2-smoke-install'
```

## 12. 앱 첫 실행 smoke

설치된 앱 실행:

```powershell
Start-Process 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
```

첫 실행은 Python venv 생성 때문에 시간이 걸릴 수 있다.  
2분 정도 기다린 뒤 확인한다.

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

이 단계는 app을 자동으로 실행하고, 새로 찍힌 log에서 backend base URL을 찾아 `/v1/health`와 Template Builder family list를 확인한다.

먼저 기존 Clipper2 process가 있으면 종료한다.

```powershell
Get-Process Clipper2 -ErrorAction SilentlyContinue | Stop-Process -Force
```

그 다음 아래 script를 PowerShell에 붙여넣어 실행한다.

```powershell
$exe = 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
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

2026-05-20 세션의 성공 예:

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
Start-Process 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
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
git -C C:\project\adlight\clipper_angular status --short --branch
git -C C:\project\adlight\clipper_electron status --short --branch
git -C C:\project\adlight\clipper_nestjs status --short --branch
git -C C:\project\adlight\clipper_python status --short --branch
```

`npm install` 후 다음 파일이 modified로 표시될 수 있다.

```text
C:\project\adlight\clipper_angular\package-lock.json
C:\project\adlight\clipper_electron\package-lock.json
```

2026-05-20 세션에서도 이 두 lockfile이 modified 상태였다.  
이 변경은 바로 커밋하지 말고 별도 검토 후 유지/되돌림을 결정한다.

## 16. 결과 보고 시 포함할 내용

다른 PC에서 직접 실행한 뒤 결과를 공유할 때는 아래를 적는다.

```powershell
git -C C:\project\adlight\clipper_angular rev-parse --short HEAD
git -C C:\project\adlight\clipper_electron rev-parse --short HEAD
git -C C:\project\adlight\clipper_nestjs rev-parse --short HEAD
git -C C:\project\adlight\clipper_python rev-parse --short HEAD
```

보고 항목:

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

### `npm` 실행이 PowerShell policy로 막힘

증상:

```text
npm : 이 시스템에서 스크립트를 실행할 수 없으므로 npm.ps1 파일을 로드할 수 없습니다.
```

해결:

```powershell
npm.cmd -v
npm.cmd install --cache C:\project\adlight\.npm-cache
```

이 가이드의 모든 npm command는 `npm.cmd`를 사용한다.

### 한글 사용자명 경로에서 Node/npm이 crash

증상:

- `0xC0000005`
- `-1073741819`
- `EPERM: operation not permitted, lstat 'C:\Users\<한글사용자명>'`
- `esbuild`, `@parcel/watcher`, `lmdb`, `msgpackr-extract` postinstall 실패

해결:

- repo workspace를 `C:\project\adlight` 같은 ASCII 경로로 만든다.
- npm cache도 `--cache C:\project\adlight\.npm-cache`처럼 ASCII 경로를 사용한다.

### `tar --version`이 실패

`fetch-uv`나 Windows runtime download path에서 archive extraction이 실패할 수 있다.

해결:

- Windows 10/11 기본 `tar.exe`가 PATH에 있는지 확인한다.
- Git Bash나 다른 tar가 PATH를 이상하게 가로채면 PowerShell에서 `where.exe tar`로 확인한다.

### `.env.local` 없음

증상:

- build 중 `clipper_nestjs\.env.local` extraResource copy 실패 가능
- app은 떠도 Template Builder official data가 로드되지 않을 수 있음

해결:

```powershell
notepad C:\project\adlight\clipper_nestjs\.env.local
Get-Item C:\project\adlight\clipper_nestjs\.env.local | Select-Object FullName,Length,LastWriteTime
```

비밀값은 출력하지 않는다.

### API smoke가 stale port를 읽음

이전 실행 log의 `NestManager ready` line을 읽으면 이미 종료된 port로 health check를 시도해 실패할 수 있다.

해결:

- API smoke script처럼 실행 전 log line count를 저장한다.
- app 실행 후 새로 추가된 line에서만 base URL을 찾는다.

### installer silent install이 오래 걸림

2026-05-20 세션에서는 silent install command가 timeout에 걸렸지만, 설치 디렉터리와 `Clipper2.exe`는 생성되어 있었다.

해결:

```powershell
Test-Path 'C:\project\adlight\clipper2-smoke-install\Clipper2.exe'
Get-Process | Where-Object { $_.ProcessName -like '*Clipper*' -or $_.ProcessName -like '*Setup*' }
```

GUI 설치로 다시 확인해도 된다.

## 이 가이드에서 아직 보장하지 않는 것

다음은 Windows installer build 이후 별도 QA가 필요하다.

- code signing
- app icon
- SmartScreen 대응
- auto-update
- CUDA acceleration
- full Dialog/Dance workflow E2E
- Template Builder sample render 전체 성공
- plugin start/stop 전체 matrix
