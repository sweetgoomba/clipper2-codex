# Electron YouTube 로그인 패스키 지원 검토

기준일: 2026-07-14 KST

패스키의 정의, 공개키 인증 흐름, 종류, 역사, macOS·Windows·Android 차이와 보안 한계는 [패스키 심화 학습 노트](PASSKEY_DEEP_DIVE_2026-07-14.md)를 먼저 참고한다. 이 문서는 그 일반 개념을 Clipper Studio의 Electron YouTube 로그인 창에 적용한 제품별 검토 문서다.

## 1. 결론과 현재 결정

- 현재 Clipper Studio의 Electron `35.7.0`은 유지한다.
- 패스키 지원을 위한 Electron 메이저 업그레이드는 이번 YouTube 안정화 범위에 포함하지 않고 별도 작업으로 보류한다.
- 현재 영상용 YouTube 로그인 창에서는 Google 패스키 화면이 진행되지 않을 수 있다. 사용자에게 `다른 방법 시도`를 눌러 비밀번호 입력과 2단계 인증 등 다른 로그인 방법을 사용하도록 안내한다.
- 패스키 지원을 재개할 때는 단순 버전 변경이 아니라 Electron 업그레이드, WebAuthn 설정, macOS 서명 권한, macOS/Windows packaged QA를 하나의 작업으로 수행한다.

## 2. 현재 현상과 확인된 우회 경로

- Electron은 `persist:youtube-auth` 세션의 `BrowserWindow`로 YouTube/Google 로그인을 연다.
- Google이 `본인 확인 중... 패스키를 사용하여 로그인을 완료합니다` 화면을 표시하지만 현재 Electron 버전에서 더 이상 진행되지 않는 것을 실제 packaged 앱에서 확인했다.
- Google 화면의 `다른 방법 시도`를 누른 뒤 비밀번호를 입력하고 휴대전화/태블릿 2단계 인증을 사용하면 로그인과 관리 쿠키 생성이 성공한다.
- 이 우회는 Clipper Studio 애플리케이션 로그인과 별개인 `영상용 YouTube 계정` 로그인에만 해당한다.

## 3. Electron 버전만 바꾸면 충분하지 않은 이유

macOS Touch ID 플랫폼 인증기를 활성화하는 `app.configureWebAuthn()`은 Electron `41.5.0`에 추가됐다. 그러나 `41.5.0`에는 Touch ID 프롬프트의 문자열 리소스 누락으로 충돌할 수 있는 문제가 있었고 `41.6.0`, `42.1.0` 이상에서 수정됐다. 따라서 후속 구현 시 `41.5.0`을 대상으로 삼으면 안 된다.

버전 업그레이드 외에도 다음이 필수다.

1. 앱 시작 시 `app.configureWebAuthn({ touchID: ... })`을 호출한다.
2. Apple Team ID와 Bundle ID에 연결된 고정 `keychainAccessGroup`을 정한다.
3. 같은 값을 macOS 코드 서명 entitlement의 `keychain-access-groups`에 추가한다.
4. 복수의 발견 가능한 자격 증명이 반환되는 경우 `select-webauthn-account` 이벤트를 처리하고 callback을 정확히 한 번 호출한다.
5. 서명된 packaged 앱에서 검증한다. 서명되지 않은 로컬 `.app`만으로 최종 Touch ID/키체인 동작을 판정하지 않는다.

## 4. 패스키 범위의 제한

Electron의 `configureWebAuthn()`은 macOS Touch ID/Secure Enclave 기반 플랫폼 인증기를 활성화한다. 이것은 `Google의 모든 패스키 방식이 자동으로 성공한다`는 의미가 아니다.

- Electron Touch ID WebAuthn 자격 증명은 해당 Mac 기기에 묶인다.
- iCloud 키체인으로 동기화되지 않는다.
- Apple Silicon 또는 T2 Secure Enclave가 있는 Intel Mac에서만 사용할 수 있다.
- WebAuthn 자격 증명은 Electron 세션 파티션별로 격리된다. 현재 `persist:youtube-auth` 파티션을 그대로 유지해야 한다.
- Safari/Chrome/iCloud에서 기존에 생성한 패스키가 Electron 영상용 세션에 그대로 노출된다고 보장할 수 없다.
- 비밀번호, 휴대전화 교차 기기 인증, 2단계 인증 경로를 계속 fallback으로 유지해야 한다.

## 5. 재개 시 버전 선택 원칙

2026-07-14 기준 안정 버전은 Electron `43.1.0`, `42.6.1`, `41.10.1`이다. 지원 종료 예정일은 각각 `43`: 2027-01-05, `42`: 2026-10-20, `41`: 2026-08-25이다. 현재 `35` 계열은 이미 지원이 종료됐다.

후속 작업에서는 문서에 적은 `43.1.0`을 무조건 사용하지 않고, 작업 시점의 현재 지원 중인 안정 버전과 EOL을 다시 확인한다. 업그레이드는 별도 브랜치에서 정확한 버전을 pin하고 수행한다.

## 6. 개발용 Node.js와 Electron 내장 Node.js의 관계

두 Node.js는 서로 다른 실행 파일이지만, 같은 소스 코드·의존성·테스트를 공유하므로 완전히 무관하지 않다.

| 구분 | 개발·CI Node.js | Electron 내장 Node.js |
| --- | --- | --- |
| 실행 주체 | 터미널의 `node`, `npm` | Electron 실행 파일 |
| Clipper 주요 용도 | `npm install`, TypeScript/Angular 빌드, 일반 Node 테스트, `electron-builder` | Electron main/preload, `utilityProcess` 로컬 NestJS, `ELECTRON_RUN_AS_NODE=1` yt-dlp EJS runtime |
| 사용자 PC | 별도 Node.js 설치가 필요하지 않음 | packaged Electron 앱에 포함 |

현재 Clipper Studio는 개발·CI Node 22, Electron `35.7.0`의 내장 Node `22.16.0`, `@types/node` 22로 메이저 버전이 정렬되어 있다. Electron 40 이상은 Node 24를 내장하므로, Electron만 먼저 업그레이드하면 개발 Node 22와 Electron runtime Node 24를 함께 관리하게 된다.

정확한 패치 버전까지 맞출 필요는 없지만 다음 호환성은 반드시 관리한다.

- **Node API 차이:** 개발 Node에서 통과한 코드가 Electron 내장 Node에 없는 API를 쓰면 packaged 앱에서만 실패할 수 있다. 반대로 Node 24 전용 API를 Electron main에 추가하면 Node 22로 돌리는 일반 테스트에서 실패할 수 있다.
- **TypeScript 타입:** `@types/node`는 컴파일 시 존재한다고 가정할 Node API를 정한다. 타입은 통과하지만 실제 Electron runtime에 API가 없는 조합을 피한다.
- **npm 의존성:** 개발 Node는 `npm install`과 빌드 도구의 `engines` 요구를 충족해야 한다. Electron이 Node 24를 내장한다고 개발 Node도 즉시 24로 변경해야 하는 것은 아니다.
- **네이티브 모듈:** 일반 Node와 Electron은 ABI가 다르므로 Node 메이저 버전을 맞춰도 충분하지 않다. Electron 버전과 플랫폼에 맞게 다시 빌드해야 한다.
- **renderer 경계:** 현재 Angular renderer는 `nodeIntegration: false`이므로 주로 Chromium 환경에서 실행된다. Node 버전 회귀의 주요 대상은 main, preload, utility process와 yt-dlp EJS runtime이다.

Electron 40 이상으로 올릴 때의 초기 전략은 개발·CI Node 22를 유지한 상태에서 Electron Node 24 경로를 별도로 검증하는 것이다.

1. Node 22에서 install, 일반 테스트, Angular/TypeScript 빌드, packaging을 검증한다.
2. 실제 Electron에서 main/preload/utility process 테스트를 실행한다.
3. packaged 앱에서 Electron 내장 Node 24를 쓰는 yt-dlp EJS metadata/download를 검증한다.
4. Angular, `electron-builder`, CI, 공유 코드가 Node 24에서 안정적인 것을 확인한 뒤 개발 Node와 `@types/node`를 24로 정렬할지 결정한다.

결론은 `정확히 같아야만 한다`도 `서로 아예 상관없다`도 아니다. 메이저 버전을 맞추면 운영이 단순해지지만, 다르게 유지할 경우에는 두 실행 환경을 모두 테스트해야 한다.

## 7. Clipper Studio 회귀 점검 범위

Electron `35` → 지원 중인 신규 메이저 버전 업그레이드는 Chromium, Node.js, V8을 함께 변경한다. 다음을 패스키 기능과 같은 브랜치에서 검증한다.

- Electron main/preload/contextBridge IPC
- Angular renderer와 Google/YouTube 로그인 화면
- `utilityProcess`로 실행하는 로컬 NestJS의 시작, 종료, 로그 flush
- Electron 내장 Node.js를 JavaScript runtime으로 쓰는 yt-dlp/EJS metadata와 download
- `persist:youtube-auth` 세션, 관리 쿠키 내보내기, 계정 변경, 전체 초기화
- `Cmd+Q`, macOS 메뉴, Windows/Linux `X` 종료 확인과 자식 runtime 정리
- `safeStorage`, 딥링크, single-instance, electron-updater
- `electron-builder` 호환성, macOS 서명/공증, Windows 설치 산출물
- 기존 `userData`를 유지한 업데이트와 새 사용자 최초 실행
- macOS 최소 지원 버전 정책. Electron 38 이상은 macOS 11을 지원하지 않는다.

## 8. 재개 시 권장 순서와 완료 기준

1. Electron 업그레이드/패스키 전용 브랜치를 만든다.
2. Electron과 `electron-builder`, Node 타입, lockfile 호환성을 확인한다.
3. 패스키 코드 없이 기존 빌드/테스트/packaged 스모크를 먼저 통과시킨다.
4. `configureWebAuthn`, entitlement, 복수 계정 선택 처리를 추가한다. 계정 이메일은 제품 로그에 남기지 않는다.
5. 서명된 Apple Silicon packaged 앱에서 Touch ID, 취소, 복수 계정, 비밀번호/2단계 인증 fallback을 확인한다.
6. Windows packaged 앱에서 Windows Hello, 로밍 FIDO2/휴대전화 경로, 비밀번호/2단계 인증 fallback을 별도로 확인한다.
7. 업데이트 전후 YouTube 쿠키 세션이 예상대로 유지되고 metadata/download가 통과해야 완료로 본다.

## 9. 현재 제품 UI 계약

아래 YouTube 로그인 액션 오류는 기존의 인증 사유별 안내에 다음 공통 문구를 덧붙인다.

> 현재 영상용 YouTube 로그인 창은 패스키 로그인을 지원하지 않습니다. Google 로그인 화면에서 "다른 방법 시도"를 누르고 비밀번호 입력과 2단계 인증 등 다른 로그인 방법을 사용해주세요.

적용 코드:

- `AUTH_REQUIRED`
- `YOUTUBE_LOGIN_REQUIRED`
- `YOUTUBE_MEMBERSHIP_REQUIRED`
- `YOUTUBE_AGE_VERIFICATION_REQUIRED`
- `YOUTUBE_PRIVATE_ACCESS_REQUIRED`
- `YOUTUBE_PREMIUM_REQUIRED`
- `YOUTUBE_BOT_VERIFICATION_REQUIRED`
- `YOUTUBE_BROWSER_COOKIE_ERROR`

후속에서 패스키를 실제 지원하게 되면 이 문구와 테스트를 같이 갱신해야 한다.

## 10. 공식 참고

- Electron `app.configureWebAuthn()`: https://www.electronjs.org/docs/latest/api/app#appconfigurewebauthnoptions-macos
- Electron `select-webauthn-account`: https://www.electronjs.org/docs/latest/api/session#event-select-webauthn-account
- Electron 41.5.0 WebAuthn 추가: https://releases.electronjs.org/release/v41.5.0
- Touch ID 프롬프트 충돌 수정: https://releases.electronjs.org/pr/51592
- 안정 버전: https://releases.electronjs.org/?channel=stable
- 릴리스/EOL 일정: https://releases.electronjs.org/schedule
- 메이저 변경 점검: https://www.electronjs.org/docs/latest/breaking-changes
- Electron process model: https://www.electronjs.org/docs/latest/tutorial/process-model
- Electron native Node modules/ABI: https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules
- Electron npm ecosystem의 개발 Node 최소 기준: https://www.electronjs.org/blog/ecosystem-node-22/
