# macOS 개발 앱 OAuth 연결 진단·실기 및 배포 잔여 과제

## 확인 결과 (2026-09-17)

- 사용자 실기: 새 local-api 개발 앱의 파일명·창 이름 `Clipper Studio (dev)`, Google 로그인, 무료 체험·사용 가능 400크레딧·최초 지급 내역 확인.
- Google 로그인 화면의 서비스명은 OAuth 프로젝트 Branding이다. 사용자가 `Clipper Studio`로 저장했다고 보고했다. 실제 Google 화면 반영은 별도 확인 대상. 클라이언트 관리용 이름은 사용자 표시명과 다르다.
- 새 빌드 Info.plist: 표시명 `Clipper Studio (dev)`, ID `ai.clipperstudio.desktop`, scheme `clipper`.
- `/Applications/Clipper Studio.app`은 이름과 달리 기존 개발판 identity(ID `ai.clipperstudio.desktop`, scheme `clipper`)였다.
- macOS에는 위 옛 앱, 이전 통합 worktree 빌드, 원본 checkout 새 빌드가 중복 등록되어 있었다.
- 조치 직전 OS 기본 핸들러 조회는 `/Applications/Clipper Studio.app`을 반환했다. 최초 로그인 순간의 이벤트 전달 경로를 추적한 것은 아니므로 당시 성공 이유까지 단정하지 않는다.
- 사용자 승인 후 아래 두 옛 앱의 등록만 해제하고 원본 새 앱 재등록. 파일·사용자 데이터·DB 삭제 없음.
- 조치 후 기본 핸들러는 원본 새 빌드 경로. 사용자가 로그아웃→로그인 후 브라우저 확인창에도 `Clipper Studio (dev).app`이 표시됨을 확인했다.

## 진단 명령: 실제 실행 없이 OS 기본 핸들러 조회

macOS NSWorkspace.URLForApplicationToOpenURL을 사용한다. URL은 조회용이며 실제 인증 code나 token을 넣지 않는다.

```bash
osascript -l JavaScript -e 'ObjC.import("AppKit"); var u = $.NSWorkspace.sharedWorkspace.URLForApplicationToOpenURL($.NSURL.URLWithString("clipper://auth/callback")); u ? u.path.js : "NO_HANDLER"'
```

변경 전: `/Applications/Clipper Studio.app`

변경 후: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`

이 검사는 OS 기본 대상만 확인한다. 브라우저 문구·실제 앱 복귀는 별도 실기해야 한다.

## 이번 로컬에서 실행한 등록 정리

아래는 진단 당시 확인된 정확한 경로에 대한 이력이며 일반 사용자용 설치 절차가 아니다. 다른 PC에서는 앱 identity·경로를 먼저 확인하고 승인받아야 한다.

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u '/Applications/Clipper Studio.app' '/Users/jina/project/adlight/.worktrees/dev-pg-local-validation-20260917/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app'
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f '/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app'
```

`-u`는 해당 번들 등록 해제, `-f`는 재등록/강제 갱신이다. 앱 자체 삭제가 아니며 옛 앱 실행·재탐색으로 등록될 수 있다. 전체 LaunchServices DB 초기화는 하지 않았다.

## 설치·공존 문제와 미확정 개선안

- Finder에서 같은 폴더라도 옛 `Clipper Studio.app`과 새 `Clipper Studio (dev).app`은 파일명이 달라 공존한다. bundle ID가 같다고 자동으로 옛 파일을 대치하지 않는다.
- 같은 이름의 새 개발판이 이미 같은 목적지에 있으면 Finder 대치 확인 대상이다. 다른 위치에 복사하면 같은 이름이어도 별도 사본이다. 자동 업데이터의 교체 동작은 DMG 드래그와 별도로 검증해야 한다.
- 구·신 개발판은 같은 데이터 경로도 사용한다. 동시 실행, 구버전의 새 데이터 읽기/쓰기, 로그인 콜백 오배달을 안전하다고 간주하지 않는다. 운영·개발의 분리와 구·신 개발판 공존은 별개다.
- 이번 `lsregister` 처리는 로컬 문제를 확인/정리한 것이며 모든 사용자에게 명령 실행을 요구하는 배포 해법이 아니다.
- 단기 배포안(제안, 미구현): 기존 개발판 종료 및 앱 번들만 교체/제거하는 안내, 새 앱 표준 설치 위치 유도, 중복 설치 감지·정확한 대상 안내. 사용자 데이터 삭제나 앱 자동 삭제는 승인 없이 하지 않는다.
- 다중 사본까지 허용할 경우 로그인 시작 인스턴스로 콜백을 돌려주는 설계 필요. Electron `src/main/auth/google-login.ts`는 packaged=custom scheme, unpackaged=loopback으로 분기한다. Web API `desktop-redirect.ts`는 제한된 loopback returnUrl을 이미 허용한다.
- 기존 `loopback-callback-server.ts`에는 요청별 비밀/state 결속이 없어 로그인 CSRF 위험이 명시되어 있다. packaged에 단순 활성화 금지. 로그인 요청·일회용 코드·교환을 시작 인스턴스에 결속(state/PKCE 등 설계), timeout/cancel/replay/동시 로그인/잘못된 콜백 테스트를 포함해 별도 승인 후 구현한다. 기존 protocol 자체 변경은 승인된 것이 아니다.
- 옛 앱의 바이너리를 새 앱이 소급 변경할 수 없다. 서버 최소 지원 버전 정책은 서버 사용을 제한할 뿐 로컬 실행이나 OS 등록을 막지 않는다. 버전 값만으로 강한 차단을 보장하지 않는다. 현재 정책 미구현/미승인.

## 배포 전 검증 항목

- 옛 개발 앱이 /Applications에 있는 상태에서 새 DMG 설치(서명·공증 포함).
- 같은 폴더의 다른 파일명, 다른 폴더 사본, 옛 앱 재실행, 두 앱 동시 존재.
- 앱이 모두 종료된 상태와 새 앱 실행 중 각각 Google 로그인 실제 수신 앱 확인.
- 기존 개발 데이터 보존, 중복 인스턴스·구버전 재실행 영향.
- 운영판 `clipperstudio://`와 개발판 `clipper://`의 상호 독립 확인.
- 자동 업데이트 설치 경로·번들 이름 변경은 별도 실기, 이번 결과로 통과 처리 금지.

제품 코드·DB·배포 변경 없음. 이번 기록은 로컬 진단 및 사용자 실기 결과이고 일반 배포 문제 전체 해결 판정이 아니다. 사용자 메시지에 노출된 OAuth 비밀값은 이 문서에 기록하지 않았으며 교체 필요를 안내했다.

참고: https://developer.apple.com/documentation/appkit/nsworkspace/urlforapplication(toopen:)-7qkzf , https://www.rfc-editor.org/rfc/rfc8252.html
