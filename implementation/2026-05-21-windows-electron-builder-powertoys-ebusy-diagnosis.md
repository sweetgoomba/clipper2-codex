# Windows electron-builder EBUSY / PowerToys Command Palette Diagnosis

작성일: 2026-05-21

## 요약

Windows packaged build 실패는 Clipper2 코드 문제가 아니었다.

직접 원인은 Microsoft PowerToys `Command Palette`의 `Microsoft.CmdPal.UI.exe`가 electron-builder가 새로 생성한 `dist-app\win-unpacked\Clipper2.exe`를 감지/매핑하면서, electron-builder가 같은 exe에 ASAR integrity 리소스를 쓰는 순간 Windows file sharing conflict가 발생한 것이다.

최종 확인:

- PowerToys `Command Palette`를 끄면 Windows build 성공.
- PowerToys `Command Palette`를 다시 켜면 같은 build가 다시 실패.
- PowerToys `Keyboard Manager`는 계속 사용 가능하다. 빌드 중 비활성화해야 하는 것은 `Command Palette`다.

## 증상

Windows에서 `clipper_electron` packaged build의 Step 5가 실패했다.

```powershell
npm run build:app:win:x64
```

실패 지점:

```text
── Step 5/5: electron-builder
> npx electron-builder --win --x64
...
EBUSY: resource busy or locked, open '...\clipper_electron\dist-app\win-unpacked\Clipper2.exe'
```

stack trace의 핵심 위치:

```text
addWinAsarIntegrity
ElectronFramework.beforeCopyExtraFiles
WinPackager.doPack
```

해석:

- Angular build, NestJS bundle, Electron TypeScript compile, uv binary 준비는 모두 끝난 상태였다.
- 실패는 env loading 문제가 아니라 electron-builder Windows packaging 중 exe resource edit 단계에서 발생했다.
- electron-builder는 Windows에서 `app.asar` integrity metadata를 `Clipper2.exe` resource에 주입하기 위해 exe를 다시 쓴다.

## 시행착오 타임라인

### 1. stale `win-unpacked` output lock 가설

초기 가설:

- 이전 빌드의 `dist-app\win-unpacked\Clipper2.exe`가 남아 있고 Windows가 그 파일을 잡고 있을 수 있다.
- 빌드 초기에 `win-unpacked`를 지우면 Step 5 실패를 피할 수 있을 수 있다.

시도:

- commit: `45718ae Handle locked Windows build output`
- 변경:
  - `scripts/build-app.mjs`에 Windows target일 때 `dist-app/win-unpacked` 사전 cleanup 추가.
  - cleanup이 lock으로 실패하면 electron-builder까지 가지 않고 일찍 실패하도록 함.

결과:

- Windows에서 여전히 Step 5 `addWinAsarIntegrity`에서 실패했다.

판단:

- 문제는 이전 빌드 산출물의 stale lock이 아니었다.
- electron-builder가 fresh `Clipper2.exe`를 생성한 직후, 그 exe를 다시 열어 쓰는 좁은 구간에서 lock이 발생했다.

최종 상태:

- 이 변경은 제거됐다.
- 현재 `build-app.mjs`에는 이 cleanup/fail-fast 로직이 없다.

### 2. Windows `asar: false` 가설

초기 가설:

- 실패 지점이 `addWinAsarIntegrity`이므로, Windows에서 ASAR packaging을 끄면 해당 exe rewrite 경로 자체를 피할 수 있다.

시도:

- commit: `c599aa6 Disable Windows asar packaging`
- 변경:
  - `electron-builder.yml`의 `win` 설정에 `asar: false` 추가.

결과:

- Windows build는 성공했다.
- 하지만 electron-builder가 다음 경고를 냈다.

```text
asar usage is disabled — this is strongly not recommended
```

판단:

- 이건 근본 해결이 아니라 packaging semantics를 바꾸는 우회였다.
- Clipper2 앱 코드 문제가 아닌 외부 file lock 때문에 app packaging 구조를 바꾸는 것은 부적절하다.

최종 상태:

- 사용자 판단에 따라 즉시 폐기.
- `win.asar: false`는 현재 존재하지 않는다.

### 3. electron-builder Step 5 retry 가설

초기 가설:

- lock이 매우 짧은 transient lock이면, Step 5를 다시 실행하면 성공할 수 있다.

시도:

- commit: `71c3323 Restore Windows asar packaging`
- 변경:
  - `win.asar: false` 제거.
  - Windows에서 electron-builder Step 5 전체를 최대 3회 재시도.
  - retry 전 `win-unpacked` cleanup.

결과:

- 사용자가 이 접근을 거부했다.

판단:

- retry는 외부 원인을 숨기는 예외처리에 가깝다.
- 한 번에 실패하는 이유를 찾아야지 build script가 반복 실행으로 성공을 기대하면 안 된다.

최종 상태:

- commit: `f729451 Remove Windows builder retry`
- retry 로직은 제거됐다.
- 현재 Step 5는 단일 `npx electron-builder ...` 호출이다.

### 4. lock cleanup/fail-fast도 제거

상태:

- retry 제거 후에도 사전 cleanup/fail-fast 로직 일부가 남아 있었다.

사용자 판단:

- lock이 왜 생기는지 알아야지 build script에서 lock을 다루는 코드 자체가 방향이 아니다.

시도/정리:

- commit: `c4ff41c Remove Windows lock handling`
- 변경:
  - `cleanTargetBuildOutput()`, `failLockedBuildOutput()` 제거.
  - Windows lock handling 전부 제거.

최종 상태:

- 현재 `scripts/build-app.mjs`에는 Windows EBUSY 관련 특수 처리, retry, cleanup 우회가 없다.

### 5. env/run-mode 변경 원인 여부 확인

확인:

- 사용자 Windows PC에서 env/run-mode 대규모 변경 이전 commit도 테스트했다.
- tested commit: `19dafd3 Fix dialog model install detection on Windows`

결과:

- `19dafd3`에서도 동일하게 Step 5 `addWinAsarIntegrity` / `Clipper2.exe` EBUSY가 발생했다.
- `Get-Process Clipper2,electron` 결과는 비어 있었다.

판단:

- 이번 env/run-mode 구조 변경이 직접 원인은 아니었다.
- 실행 중인 `Clipper2.exe` 또는 `electron.exe` 프로세스가 파일을 잡고 있는 문제도 아니었다.

### 6. electron-builder version 가설

초기 가설:

- electron-builder 25.x의 Windows ASAR integrity resource edit 동작 문제일 가능성.

시도:

- commit: `aa07784 Update electron builder`
- 변경:
  - `electron-builder`를 `25.1.8`에서 `26.9.1`로 업데이트.
  - `app-builder-lib`도 lockfile상 `26.9.1`로 변경.

결과:

- Windows에서 `electron-builder 26.9.1`로도 동일하게 실패했다.
- 실패 지점은 여전히 `addWinAsarIntegrity`의 `writeFile(Clipper2.exe)`.

판단:

- electron-builder version 문제가 아니었다.
- 업그레이드는 root cause 제거에 효과가 없었으므로 남길 이유가 없다.

최종 상태:

- commit: `f701677 Revert "Update electron builder"`
- `electron-builder`와 `app-builder-lib`는 다시 `25.1.8`.

## 진단 도구 사용 흐름

### `handle64.exe`

목적:

- 실패 후에도 누가 `Clipper2.exe` handle을 잡고 있는지 확인.

결과:

```text
No matching handles found.
```

판단:

- 실패 후 정적 handle 조회로는 원인이 보이지 않았다.
- lock은 빌드 도중 짧게 생겼다가 풀리는 transient event일 가능성이 높았다.

### Process Monitor

목적:

- 빌드 도중 `Clipper2.exe`에 대한 file operation을 capture.

필터:

```text
Path contains \clipper_electron\dist-app\win-unpacked\Clipper2.exe Include
```

관찰된 핵심 이벤트:

```text
node.exe CreateFile ...\Clipper2.exe SHARING VIOLATION
Desired Access: Generic Write, Disposition: OverwriteIf
```

의미:

- electron-builder를 실행 중인 `node.exe`가 `Clipper2.exe`를 쓰려고 했지만 Windows sharing conflict로 실패했다.

동일 시간대에 관찰된 이벤트:

```text
Microsoft.CmdPal.UI.exe CreateFile ...\Clipper2.exe SUCCESS
Microsoft.CmdPal.UI.exe CreateFileMapping ...\Clipper2.exe FILE LOCKED WITH ONLY READERS
```

의미:

- PowerToys Command Palette가 새 exe를 감지하고 read-only mapping을 만들었다.
- 그 순간 electron-builder의 write open과 충돌했다.

## 최종 root cause

원인 프로세스:

```text
Microsoft.CmdPal.UI.exe
```

소속:

```text
Microsoft PowerToys Command Palette
```

문제 메커니즘:

```text
electron-builder가 Clipper2.exe 생성
-> PowerToys Command Palette가 새 exe를 감지/조회/매핑
-> electron-builder가 같은 exe에 ASAR integrity resource를 쓰려고 재open
-> Windows file sharing conflict
-> EBUSY / SHARING VIOLATION
```

검증:

- `Command Palette` off: build success.
- `Command Palette` on: build failure reproduced.

## 현재 코드 상태

현재 Clipper2 codebase에는 Windows EBUSY 관련 우회 코드가 남아 있지 않다.

남아 있지 않은 것:

- `win.asar: false`
- electron-builder Step 5 retry
- `dist-app/win-unpacked` lock cleanup/fail-fast special handling
- electron-builder 26.x upgrade

현재 유지되는 것:

- env/run-mode 구조 개선
- packaged env copy/read 정리
- `.env.packaged` preflight
- LocalPluginHost / plugin dynamic port range
- Electron packaged resources env policy

즉, 현재 남아 있는 코드는 원래 목표였던 실행 모드/env/plugin runtime 구조 개선이고, PowerToys EBUSY 시행착오용 변경은 제거됐다.

## Windows build 운영 기준

Windows에서 PowerToys를 사용하는 경우:

- `Keyboard Manager`는 사용할 수 있다.
- `Command Palette`는 packaged build 중 비활성화한다.

빌드 전 확인:

```powershell
Get-Process Microsoft.CmdPal.UI -ErrorAction SilentlyContinue
```

빌드 중 강제 종료가 필요하면:

```powershell
Stop-Process -Name Microsoft.CmdPal.UI -Force -ErrorAction SilentlyContinue
```

이것은 Clipper2 build script가 처리할 문제가 아니라 Windows build 환경 전제조건이다.

## 이후 같은 증상 발생 시 판단 순서

1. `Get-Process Clipper2,electron`으로 앱 자체가 실행 중인지 확인한다.
2. 앱 프로세스가 없는데 `EBUSY`가 계속 나면 `handle64.exe`로 persistent handle을 확인한다.
3. handle이 안 나오면 Process Monitor로 build 중 transient file operation을 capture한다.
4. `SHARING VIOLATION` 행의 `Process Name`, `Operation`, `Desired Access`, `ShareMode`를 확인한다.
5. 외부 process가 원인이면 build script를 바꾸지 말고 해당 process나 Windows 설정을 조정한다.

## 교훈

- Windows `EBUSY`는 항상 앱 프로세스가 실행 중이라는 뜻이 아니다.
- 실패 후 handle 조회가 비어 있어도 빌드 중 transient lock은 존재할 수 있다.
- electron-builder의 `addWinAsarIntegrity` 실패는 ASAR 자체가 문제라는 뜻이 아니라, exe resource write 시점에 외부 process가 끼어들었다는 뜻일 수 있다.
- 외부 file watcher/indexer/launcher가 원인일 때 app packaging 구조를 바꾸는 것은 잘못된 해결이다.
