# 운영·개발 앱 표시 이름

최종 확인: 2026-09-17 KST. 상태: **이름·환경별 identity 보존 / R06·R07 수정·회귀 통과·로컬 커밋 / 실제 Google OAuth·Windows NSIS 실기 대기**.

[전체 현황](../WORKBOARD.md)

## 목표·범위

통합판의 운영 앱은 macOS·Windows 모두 `Clipper Studio`, 개발 앱은 macOS·Windows 모두 `Clipper Studio (dev)`로 구분한다. 설치파일도 같은 이름을 사용한다. **운영은 기존 `appId=ai.clipperstudio.app`, protocol `clipperstudio://`, `Application Support/Clipper`를, 개발은 기존 `appId=ai.clipperstudio.desktop`, protocol `clipper://`, `Application Support/Clipper Studio`를 각각 유지한다.** 캐시·포트·업데이트 구조도 환경별 기존 값을 보존한다. 변경 대상은 사용자에게 보이는 앱·패키지 이름뿐이다.

사용자는 2026-09-16 기존 운영 macOS 앱이 정식 배포된 적 없고 본인 테스트 설치만 있었으므로 옛 `Clipper.app`과의 공존 문제는 고려하지 않아도 된다고 확정했다. 운영 macOS 설치 앱 이름을 `Clipper.app`으로 유지하는 안은 명시적으로 거부했으며, 목표는 `Clipper Studio.app`이다.

사용자는 운영·개발 macOS 앱 동시 설치를 전제로 개발 설치 앱을 `Clipper Studio (dev).app`으로 분리하는 안에 동의했다. Windows도 같은 운영/개발 이름 규칙을 적용하는 것이 요구사항이다.

## 현재 상태·중단 지점

사용자 승인 후 Electron `6766c0645d8151eac1ea075e08f89871cb4ad4df`, Nest `fda1eda586fe2b80a444691303fb1e52fef57a34`에 보완을 로컬 커밋했다. fresh build와 Electron955/Nest2,678 테스트 PASS, 두 worktree clean이다. [커밋 결과](../../implementation/2026-09-17-integration-commit-proposal.md)가 아래 커밋 전 기록의 미커밋/옛 HEAD 표현보다 우선한다. 코드 push·추가 병합·원본 dev 변경·배포는 없다.

### 커밋 전 조사·검증 기록

최신 [Astra 수정 결과](../../implementation/2026-09-17-astra-fix-result.md)에서 R06 spawn 이후 PID/identity 확보와 R07 Nest/Electron 자식 identity 계약을 수정했다. Electron 전체 955/955 및 build, 실제 일회용 Nest writer→Electron cleanup 프로세스 회귀가 통과했다. 실제 설치형 앱 crash/Windows 전체 실기를 대신하는 것은 아니다. 이번 변경은 Electron/Nest 미커밋 상태이며 이름·환경별 appId/protocol/data path는 변경하지 않았다.

2026-09-17 현재 Electron 통합 HEAD는 `827fcda8b12a34232c2574983afff6284b69d949`이다(이전 전체 SHA 오기 정정). formal-PG, 앱 이름 2커밋, child-process 종료 보완과 환경별 identity 복구를 포함하고, 그 위에 이번 R06/R07 수정이 미커밋으로 남아 있다. 이전 macOS arm64 local-api 개발 `Clipper Studio (dev).app` 생성·실행 증거는 보존하되 이번 수정본의 패키지 실기로 재사용하지 않는다. Windows NSIS 실제 설치파일은 arm64 Mac에서 x64 `makensis` 실행이 OS error `-86`으로 막혔으므로 사용자가 Windows 서버에서 확인한다. 이름 계약 테스트는 개발 `Clipper Studio (dev) Setup`, 운영 `Clipper Studio Setup`을 통과했다. push·배포는 하지 않았다.

기존 보존 커밋 위에 후속 로컬 구현을 완료했다. 운영은 `Clipper Studio.app`/`Clipper Studio.dmg`와 `Clipper Studio Setup ${version}.exe`, 개발은 `Clipper Studio (dev).app`/`Clipper Studio (dev).dmg`와 `Clipper Studio (dev) Setup ${version}.exe`를 사용한다. Windows 설치 후 실행파일·바로가기 표시도 builder `productName`을 따라 각각 구분된다. 로그인 화면은 기존 AppInfo 연결을 그대로 사용하므로 Angular 변경 없이 런타임 표시명을 따른다.

후속 수정은 개발 base `productName=Clipper Studio (dev)`, 운영 생성 config `productName=Clipper Studio`로 바꿨다. `1930ad4`가 운영 identity를 개발 identity로 잘못 통일한 결함은 사용자 지적 뒤 `827fcda`에서 바로잡았다. 최종 테스트는 위 환경별 appId·protocol·data path가 각각 유지되는 계약을 고정한다.

이후 재감사에서 `applyDesktopIdentity()`가 시작 초기에 `app.setName()`을 바꾸기 때문에 macOS `safeStorage`의 기존 Keychain 항목으로 암호화된 `auth.bin`을 새 이름의 앱이 복호화하지 못할 수 있음을 확인했다. 사용자는 2026-09-16 새 앱에서 1회 재로그인하면 되므로 기존 Keychain session을 보존하거나 migration하지 않아도 된다고 결정했다. 사용자 계정·프로젝트·설정 데이터 경로는 그대로 보존하고, 새 앱이 복호화 실패를 로그인 없음으로 안전하게 처리한 뒤 로그인 완료 시 새 이름의 Keychain identity로 `auth.bin`을 덮어쓰는 흐름을 검증한다.

최초 구현 `99444d8`, 후속 패키지 이름 변경 `7aed9f6`은 이력으로 보존한다. 현재 통합 결과에 이미 포함됐으므로 다시 merge/cherry-pick하지 않는다. push·배포는 하지 않았다.

## 작업 공간

- 현재 branch: `integration/dev-pg-local-validation-20260917`.
- 현재 worktree: `/Users/jina/project/adlight/.worktrees/dev-pg-local-validation-20260917/desktop/clipper_electron`.
- 현재 HEAD: `6766c0645d8151eac1ea075e08f89871cb4ad4df`, R06/R07 수정 로컬 커밋 완료, clean.
- 옛 feature worktree는 이력 보존용이며 현재 정본이 아니다. 원본 checkout과 다른 작업 worktree는 변경하지 않았다.

## 이전 패키징·실행 검증 기록

- 기존 TDD RED 기록 유지.
- 2026-09-16 커밋 직전 Node `v24.3.0`, TypeScript `npm run build`: PASS.
- 전체 Electron `npm test`: **950 PASS, 0 FAIL**.
- builder 이름과 운영·개발 각각의 기존 appId/protocol/data path·업데이트·캐시 구조 보존 계약 PASS.
- macOS arm64 local-api `Clipper Studio (dev).app` 실제 생성·실행 PASS.
- 실제 실행에서 표시명, 로그인 화면, 옛 토큰 복호화 실패의 안전한 로그아웃 처리, 검증용 일회성 desktop auth code를 통한 session 설정, 프로젝트/Variation/설정 진입과 access·credit 표시를 확인했다. 격리 API에는 Google OAuth client ID/secret을 넣지 않았으므로 실제 Google OAuth 브라우저 재로그인은 확인하지 않았다.
- 앱 종료 시 Nest child process가 exit code 0, intentional shutdown으로 끝나고 관련 프로세스가 남지 않음을 확인했다.

## 다음 행동

앱 이름 커밋은 이미 승인된 통합에 포함됐고 R06/R07 수정·회귀도 위 최신 기록대로 통과했다. 새 수정본의 설치형 종료 실기, Windows 서버의 NSIS 실물 설치·업그레이드와 배포 전 서명·공증 smoke는 남아 있다. 운영·개발은 서로 다른 기존 appId·protocol·데이터 경로와 서로 다른 표시명을 유지하므로 독립 설치 대상으로 다룬다.

macOS 실기 smoke는 다음 순서를 필수 게이트로 고정한다.

1. 옛 개발판에서 로그인하고 식별 가능한 로컬 프로젝트·설정을 만든 뒤 정상 종료한다.
2. `Clipper Studio (dev).dmg`의 새 앱을 `/Applications`에 설치한다. 파일명이 달라 옛 `Clipper Studio.app`과 공존할 수 있지만, 두 앱을 번갈아 실행하는 것은 지원하지 않는다.
3. 새 앱 첫 실행에서 옛 `auth.bin` 복호화 실패가 크래시·네이티브 Keychain 반복 프롬프트·무한 로그인 루프 없이 **로그아웃 상태**로 귀결되는지 확인한다. 현재 `getTokenBundle()`은 decrypt 예외를 잡아 `null`을 반환하도록 구현돼 있으나 실제 서명 앱/Keychain 동작은 별도 확인한다.
4. 같은 개발 `userData` 경로에서 기존 프로젝트·설정이 그대로 보이는지 확인한다.
5. 다시 로그인해 새 identity로 토큰을 저장하고 앱을 완전히 종료·재실행한 뒤 로그인 유지 여부를 확인한다.
6. 로그아웃 후 토큰 파일 정리, protocol 딥링크, 자동 업데이트 대상, DMG 앱 이름·Dock/Finder 표시를 함께 확인한다.

3의 복호화 실패가 크래시 없이 로그아웃 상태로 귀결되는 것과 검증용 일회성 code session·정상 종료는 확인했다. 그러나 옛 개발판에서 직접 만든 상태를 이어받는 1~2, 실제 Google OAuth 재로그인, 4의 식별 가능한 기존 프로젝트 표시, 새 session의 재실행 유지, 실제 서명·공증·업데이트는 배포 전 남은 smoke다.

## 제약·미확인

- Windows 설치/업데이트와 운영 배포는 미실행. Windows는 사용자가 Windows 서버에서 직접 검증한다.
- 운영 appId/protocol/data path(`ai.clipperstudio.app`, `clipperstudio`, `Clipper`)와 개발 값(`ai.clipperstudio.desktop`, `clipper`, `Clipper Studio`)을 각각 보존한다. 캐시·포트·자동 업데이트 구조도 유지한다. macOS 개발판 표시명 변경에 따른 기존 암호화 로그인 session은 보존 대상에서 제외하고 1회 재로그인을 허용한다.
- 실제 ML 플러그인 실행과 Build 5 전체 QA HOLD 유지. 서버 직접 접속 없음.

## 상세 근거

- [2026-09-16 세션 기록](../../records/sessions/2026/09/16.md)
- [통합 결과](../../implementation/2026-09-15-main-integration-result.md)
