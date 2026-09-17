# 독립 개발판 — Electron 기반·로그인 결속 구현 검증

날짜: 2026-09-17. 작업 위치: 원본 `desktop/clipper_electron`, 브랜치 `integration/dev-pg-local-validation-20260917`, 기준 HEAD `6766c0645d8151eac1ea075e08f89871cb4ad4df`. 이 문서의 변경은 **미커밋**이다.

## 판정

후속 DB 게이트: 승인된 새 로컬 컨테이너에서 실제 nullable migration/로그인 동시 소비/release 검증 **9 PASS**. [실제 DB 결과](2026-09-17-independent-dev-real-db-validation.md). 기존 앱이 쓰는 DB·실 `.env`에는 적용하지 않았으므로 아래 실제 로그인/설치형 검증 대기는 유지한다.

Task 1–2 기반에 이어 Task 3–4의 Web API/Electron 로그인 요청 결속을 코드로 연결했다. 후속 release 서버/runner/Admin의 코드·자동 테스트도 [릴리스 검증 결과](2026-09-17-independent-dev-release-validation.md)대로 완료했다. **실제 DB migration 및 새 설치본 Google 로그인/템플릿 이관/동시 실행은 미완료**다. 코드 테스트 통과를 배포 완료로 해석하지 않는다. 기존 `dist-app`은 이번 수정으로 다시 만들거나 실행하지 않았다. 아래 1차 Electron 기반 검증 기록은 보존하며, 최신 로그인 변경은 다음 절을 따른다.

## 2차: 로그인 요청 결속 (2026-09-17)

- 작업 브랜치: 원본 Electron/Web API 모두 `integration/dev-pg-local-validation-20260917`; HEAD는 각각 `6766c0645d8151eac1ea075e08f89871cb4ad4df`, `8b074a59a454b47323f9e490d9bfd8d6c2a51ec5` 그대로. 모든 새 변경 미커밋.
- Web API: desktopTarget/requestId/S256 challenge 필수, 서버 `DESKTOP_AUTH_TARGET=development|production`와 일치 검사. 없으면 desktop login 503, 웹 로그인은 별도 계약 유지. 사용자 실 `.env`는 수정하지 않았다. `.env.example`만 새 설정으로 갱신했다.
- desktop OAuth state: 기존 USER_JWT RS256 키, 별도 audience/type, 5분 TTL. 변조/만료/잘못된 대상·서명·스키마/옛 무서명 desktop state 거부. 잘못된 desktop state를 web session 발급으로 폴백하지 않는다. 옛 DESKTOP_REDIRECT로 callback을 선택하지 않는다.
- 완료 주소: 개발 `clipperstudio-dev://auth/callback`, 운영 `clipperstudio://auth/callback`, 코드와 requestId 전달. 언패키징 loopback IP/port/path 제한 유지, 부적합 returnUrl은 조용한 폴백 대신 거부.
- 코드 교환: target/requestId/verifier 해시 확인 후 `used_at IS NULL AND expires_at > :at` 조건 UPDATE로 1회 소비. 동시 2요청에서 1세션만 허용. 잘못된 proof는 code 미소비, 소비 뒤 세션 저장 실패는 새 로그인 필요. web_handoff는 이번 변경 범위 밖이며 기존 회귀 유지.
- User DB migration `1789600000000-AddDesktopLoginBinding` 작성/등록: desktop_auth_codes에 nullable desktop_target/request_id/code_challenge 3개만 추가. 옛 code 행 backfill/사용자·금융 데이터 삭제 없음. **SQL/매핑 테스트만 실행, 실제 DB migration 미실행.**
- Electron: process-memory PendingDesktopLogin, UUID+랜덤 verifier+S256, 5분 유효. verifier를 디스크/renderer/URL에 전달하지 않는다. 같은 target/requestId의 콜백만 1회 교환. 엄격한 scheme/host/path와 중복 query·token fallback 거부. 앱 재시작은 pending을 복원하지 않음.
- logout/새 로그인/브라우저 열기 실패/timeout으로 pending 무효화. 늦은 exchange 응답은 토큰 저장 및 renderer 로그인 전달 전에 재검사해 계정을 덮어쓰지 않는다. loopback도 requestId 일치 및 GET만 수신, 잘못된 요청은 정상 대기를 소비하지 않는다. 로그의 state/challenge/verifier를 마스킹.
- 사용자 취소(브라우저 닫기)는 OS 이벤트로 감지하지 못하므로 5분 만료 또는 새 로그인/로그아웃으로 정리한다. cold-start/임의 callback은 교환하지 않는다. 현재 유효한 pending이 없으면 app.whenReady 이후 native dialog로 앱에서 로그인 재시도를 안내한다. 이미 진행 중인 다른 요청은 안내/실패 이벤트로 방해하지 않고 저장된 토큰도 변경하지 않는다. 실제 설치형 안내 UX는 실기 확인 대상이다.

### 검증과 한계

1. TDD: 정책/서명 state/잘못된 redirect/HTTP 로그인 흐름/동시 교환/앱 pending·callback·proof 전송·redaction RED → GREEN. 추가 회귀에 DTO validation, nullable entity 매핑, 세션 저장 실패 뒤 재사용 거부 포함.
2. Web API `npm run build` PASS. 인증 22 suites / **224 PASS**. 전체 **265 suites / 2,845 PASS / 21 SKIP** (기존 DB 의존 skip 포함), 로그 `/tmp/clipper-independent-dev-web-api-20260917-verified.log`.
3. 전체 첫 실행의 migration 마지막 항목 기대값 1건은 새 migration 등록에 맞춰 갱신. 후속 샌드박스 실행의 loopback EPERM은 코드 결함으로 수정하지 않고 로컬 포트 허용 환경에서 재실행했다.
4. Electron build 및 전체 **975 PASS / 0 FAIL / 0 SKIP**. 최초 로그 `/tmp/clipper-independent-dev-login-electron-20260917.log`; catch 만료 처리와 cold-start 안내 보완 후 최종 전체 재실행 **975 PASS**를 `/tmp/clipper-independent-dev-login-electron-20260917-final.log`에 보존했다.
5. 읽기 전용 독립 리뷰: 중요한 인증 결속/계정 변경 결함 미발견, Task 4의 cold-start 재시도 안내 누락(P2) 발견. Angular는 login() 내부에서만 deep-link listener를 등록하므로 renderer 이벤트만 보내면 cold-start에 보이지 않는 점을 확인하고 native dialog로 보완했다. RED→GREEN, 좁은 재리뷰에서 P2 해소/새 지적 없음. release/설치형 실기까지 완료됐다는 판정은 아니다.
6. RED 실행 주의 기록: desktop-exchange 함수 인자를 테스트에서 먼저 바꾸면서 구 구현이 mock deps를 받지 못해 기본 API에 모형 code 3요청이 나갔고 모두 HTTP 401이었다. 사용자 token/OAuth credential을 사용하거나 token을 저장하지 않았다. 테스트의 global fetch를 기본 차단하도록 고쳐 이후 주입 누락은 외부 요청 없이 즉시 실패하게 했다. 이후 인증 테스트는 주입 fixture와 로컬 loopback만 사용했다.
7. Google 실제 OAuth·서명/공증 설치본·OS 앱 연결·실제 DB 경쟁 UPDATE는 아직 검증하지 않았다. 계정 보호 테스트는 모형 HTTP/storage와 실제 crypto/메모리 생명주기/SQL 조건을 검증한 것이며 사용자 설치 실기를 대체하지 않는다.

### 당시 한도와 재개 — 과거 체크포인트

사용자는 주간 한도 소진 시 중단·고지하고 직접 reset 후 이어가기를 요청했다. 마지막 조회는 잔여 **2%**(usedPercent 98), reset credit 사용 없음. 소진으로 인계 자체가 끊기지 않도록 Task 3–4 검증/리뷰 완료 지점에서 정리한다. 아직 0% 소진은 아니다. 사용자 reset 후 `계속`하면 이 문서·NEXT·WORKBOARD와 실제 git diff를 읽고 release 계획 Task 1부터 이어간다. 실 환경파일을 출력하지 않는다.

## 구현한 값

| 항목 | 새 개발판 | 운영판 |
|---|---|---|
| 표시명 | Clipper Studio (dev) | Clipper Studio |
| appId / Windows AppUserModelId | ai.clipperstudio.dev | ai.clipperstudio.app |
| 프로토콜 | clipperstudio-dev | clipperstudio |
| appData 아래 userData/sessionData | Clipper Studio Dev | Clipper |
| 업데이트 채널 | dev | stable |
| Windows x64 feed | https://dev-api.clipperstudio.ai/releases/updates/dev/windows/x64 | https://api.clipperstudio.ai/releases/updates/stable/windows/x64 |
| updater cache | clipper-studio-dev-updater | clipper-updater |

- Mac ARM64 feed 경로는 각각 `https://dev-api.clipperstudio.ai/releases/updates/dev/macos/arm64`, `https://api.clipperstudio.ai/releases/updates/stable/macos/arm64`로 해석됨을 단위 검증했다. **이 주소가 있다고 Mac 업데이트를 켠 것이 아니다.** 모든 새 Mac 빌드 설정에 autoUpdateDisabled=true, 실행 코드에 Darwin 차단, 생성 builder config에 mac.publish=null을 넣었다. ZIP 추가 없음. Mac 공개/자동빌드/업데이트 HOLD 유지.
- local-api는 같은 development/dev identity, loopback API, 업데이트 비활성이다. 별도 네 번째 앱이 아니다.
- 패키지 config에 identity/channel/API가 없거나 서로 맞지 않으면 시작을 거절한다. 구 개발판 identity로 조용히 되돌아가는 fallback 없음. unpackaged 진입은 명시적 development 설정을 사용한다.
- HF/Torch/uv/XDG 캐시는 각 userData/cache로 지정한다. 운영 plugin 포트 범위 55000–55199 유지, 개발은 상속된 고정 범위를 제거하고 기존 동적 할당을 사용한다. main/자식 환경에 동일하게 반영한다.
- 로그는 각 userData/logs로 명시 지정했다. 임시 로그 fallback도 PID/개별 임시 디렉터리로 분리해 공통 temp 루트 파일에 기록하지 않는다. 옛 로그·캐시·프로젝트·auth.bin을 이동/삭제하지 않았다.
- auth.bin, Nest 루트, telemetry consent/install ID/outbox, 관리 Python 경로가 userData 기반인 기존 배선을 점검했다. 실제 세 앱 동시 실행과 Keychain 검증을 대신하지 않는다.
- Windows generic publish 설정을 profile의 API/channel에서 생성한다. `--publish never`를 빌드 인자에 명시했으며 실제 업로드하지 않았다. 설치 프로그램의 cache define과 app-update.yml 생성기가 모두 AppInfo.updaterCacheDirName을 사용하는 것을 설치된 builder 코드에서 확인했다.
- production 전용 builder 생성 함수를 **prepareDesktopBuilderConfig**로 바꾸고 dev/prod 모두 완전한 설정을 생성한다. 기존 함수 alias는 남기지 않았다. protocol 배열 상속으로 옛 scheme이 섞이지 않는다. dependency/version 변경 없이 package/lock의 root name만 변경했다.
- packaged secret allowlist에는 공개 routing 필드 updateChannel만 추가했다. telemetry 기능/전송키 정책은 변경하지 않았다.

## 검증 근거

1. 변경 전 `npm run build` PASS. 기본 병렬 테스트는 Electron lazy unpack 경합과 sandbox loopback 제한 등으로 실패했으나, 코드 변경 전 `node --test --test-concurrency=1 test/*.js test/*.mjs`를 허용된 로컬 테스트 권한으로 재실행해 **955/955 PASS**를 확인했다. 이를 이번 코드 회귀로 오인해 다른 코드를 수정하지 않았다.
2. 새 identity/명시적 config/cache/channel/Mac HOLD 테스트 **6건 RED → GREEN**. Windows builder generic config 부재 **RED → GREEN**. 명시 logs 경로와 프로세스별 fallback **RED → GREEN**.
3. 실제 설치된 electron-builder의 getConfig/validateConfiguration/AppInfo/getAppUpdatePublishConfiguration으로 dev/prod Windows 설정을 생성하고 임시 app-update.yml을 직렬화/재로딩했다. 두 cache 이름과 정확한 URL 확인. **실제 Windows EXE/NSIS 설치본을 생성한 테스트는 아니다.**
4. 추가 profile config 6개 조합(Windows/Mac × dev/prod/local-api) 파일 read roundtrip, 잘못된 API/프로필 거절, 오류 메시지 비밀값 비노출 확인.
5. 최종 `npm run build` PASS. 최종 `node --test --test-concurrency=1 test/*.js test/*.mjs`: **963 PASS / 0 FAIL / 0 SKIP**. 로그 `/tmp/clipper-independent-dev-foundation-final-20260917.log`. 앞선 전체 실행도 962 PASS였으나 추가 roundtrip 테스트와 logs 변경 후 963으로 재실행했다.
6. `git diff --check` PASS. main/dev 참조·다른 제품 저장소·환경파일·실제 DB·OS 프로토콜 등록 변경 없음.

## 남은 순서

1. 앱 계획 Task 3–4: 독립 리뷰 지적 및 설치형 UX/실기 게이트 확인. 서버·앱 코드는 연결했지만 실제 로그인 검증 전, 별도 승인된 로컬 User DB에 새 nullable migration 적용 및 실 환경의 DESKTOP_AUTH_TARGET 설정이 필요하다. 자동 실행하지 않는다.
2. release 계획: API/runner/Admin 코드·자동 검증은 후속 완료. [릴리스 결과](2026-09-17-independent-dev-release-validation.md)의 새 격리 DB 승인 및 실제 DB/배포 검증 게이트를 따른다. 원격 서버에 적용됐다는 뜻은 아니다.
3. Task 5: 옛 배포 앱의 실제 템플릿 export → 새 빈 데이터 앱 import(자산/폰트/레이아웃 포함), Mac 세 앱 공존/양방향 로그인, Windows 사용자 장비 설치·업데이트·삭제 격리 확인. 다른 자료 이관은 선택이며 미구현.
4. 새 앱·설치본을 실제 빌드한 다음 프로토콜/데이터 경로/PKCE/채널 검증. 과거 이름 변경 빌드의 성공 증거를 재사용하지 않는다.
5. PG 로컬 실기 및 개발 DB 복제본 리허설은 원래 승인 게이트를 유지한다. 서버 직접 접속/실제 DB 변경/배포 없음. 실제 ML/Build 5 전체 QA HOLD.

## 변경·커밋·푸시·배포

- 제품 변경: Electron + Web API, 원본 통합 브랜치 위 미커밋.
- 문서: `.codex` 계획 상태·이 결과·작업카드·NEXT·WORKBOARD 갱신, 미커밋.
- commit / push / merge / rebase / cherry-pick / deploy: **없음**.
- 실제 앱 재빌드/설치/실행, 서버·DB 작업: **없음**. `npm run build`는 Electron TypeScript 컴파일이다.
