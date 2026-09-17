# 독립 개발판 전환 — 선택된 설정과 코드 변경안

기록일: 2026-09-17. 상태: 사용자 설정안과 아래 연결 변경 범위 동의 후 세부 계획 작성. **제품 코드 구현 전**. 실행 계획은 [앱·로그인·템플릿 검증](2026-09-17-independent-dev-app-plan.md), [업데이트 채널·runner·관리자](2026-09-17-independent-dev-release-plan.md)로 나눴다. Mac ZIP 업데이트(M1)는 기존 보류 결정을 누락해 필수 확장으로 잘못 제시한 항목이며, 사용자 지적 후 이번 범위에서 제외하고 HOLD로 정정했다.

## 1. 최신 결정

- 새 개발판은 빈 데이터로 시작한다. 옛 개발판 자동 대치·데이터 경로 유지·전체 자동 이관은 요구하지 않는다.
- 템플릿 이관은 필수다. 기존 `.cliptpl` 내보내기/가져오기를 우선 사용하되 실제 옛 배포본의 템플릿으로 검증한다.
- 소재·프로젝트 등 추가 이관은 선택 사항이다. 전체 데이터 폴더나 로그인·작업 큐를 무작정 복사하지 않는다.
- 운영판과 새 개발판은 macOS/Windows에서 동시 설치·실행 가능해야 한다.
- 옛 개발판이 남아 있거나 실행되더라도 새 개발판 로그인 연결을 가로채지 않아야 한다. 옛 앱 탐색/삭제 및 수동 `lsregister`를 정상 작동 전제로 삼지 않는다.
- `dev-next`를 사용하지 않는다. 새 개발판 업데이트 채널은 `dev`다.

## 2. 앱별 값

옛 개발판 값은 조사된 설치본 및 코드 기본값이다. 직원별 환경변수/실제 서버 게시 상태까지 확인한 것은 아니다. 새 개발판 열은 목표이며 현재 구현값이 아니다.

| 항목 | 옛 개발판 | 새 개발판 목표 | 운영판 |
|---|---|---|---|
| 설치 앱 표시명 | Clipper Studio | Clipper Studio (dev) | Clipper Studio |
| macOS 번들 파일명 | Clipper Studio.app | Clipper Studio (dev).app | Clipper Studio.app |
| appId | ai.clipperstudio.desktop | ai.clipperstudio.dev | ai.clipperstudio.app |
| 로그인 scheme | clipper | clipperstudio-dev | clipperstudio |
| 로그인 callback | clipper://auth/callback | clipperstudio-dev://auth/callback | clipperstudio://auth/callback |
| macOS userData | ~/Library/Application Support/Clipper Studio | ~/Library/Application Support/Clipper Studio Dev | ~/Library/Application Support/Clipper |
| Windows userData | %APPDATA%\Clipper Studio | %APPDATA%\Clipper Studio Dev | %APPDATA%\Clipper |
| 배포 API | https://dev-api.clipperstudio.ai | https://dev-api.clipperstudio.ai | https://api.clipperstudio.ai |
| 업데이트 채널 | stable 기본값 | dev | stable |

새 개발판과 운영판은 서로 다른 `.app` 파일명으로 /Applications에 공존한다. 옛 개발판과 운영판은 파일명이 같으므로 같은 디렉터리에 세 앱을 모두 그대로 놓을 수 있다고 보장하지 않는다. 옛 개발판 보존이 필요하면 별도 위치에 둔다. 옛/새 개발판의 동시 존재는 지원 조건이지만 옛 앱의 변경된 서버 API 기능까지 호환 지원하는 뜻은 아니다.

### 업데이트 메타데이터 주소

이 주소는 설치파일 자체가 아니라 버전·파일 URL·해시가 담긴 업데이트 정보를 받는 주소다. 주소 설계와 실제 게시/접속 검증은 다르다. **Mac 열은 비활성/보류 기능의 경로 참고값이며 활성화 결정이 아니다.** 현재 로컬 Mac 설치본은 autoUpdateDisabled=true다.

| 앱 | Mac ARM64 | Windows x64 |
|---|---|---|
| 옛 개발판 기본값 | https://dev-api.clipperstudio.ai/releases/updates/stable/macos/arm64/latest-mac.yml | https://dev-api.clipperstudio.ai/releases/updates/stable/windows/x64/latest.yml |
| 새 개발판 | https://dev-api.clipperstudio.ai/releases/updates/dev/macos/arm64/latest-mac.yml | https://dev-api.clipperstudio.ai/releases/updates/dev/windows/x64/latest.yml |
| 운영판 | https://api.clipperstudio.ai/releases/updates/stable/macos/arm64/latest-mac.yml | https://api.clipperstudio.ai/releases/updates/stable/windows/x64/latest.yml |

로컬 API 빌드는 새 개발판과 동일한 identity를 사용하고 API 주소만 로컬로 바꾸며 자동 업데이트는 끈다. 별도 네 번째 앱으로 만들지 않는다.

## 3. 실제 코드 조사 결과와 변경 경계

### A. Electron: 설치 identity와 실행 상태 격리

주요 파일:

- `desktop/clipper_electron/electron-builder.yml`
- `desktop/clipper_electron/scripts/build-runtime-config.mjs`
- `desktop/clipper_electron/src/main/config/production-identity.ts`
- `desktop/clipper_electron/src/main/config/packaged-runtime-config.ts`
- `desktop/clipper_electron/src/main/main.ts`
- `desktop/clipper_electron/src/main/update/update-feed.ts`

현재 개발 빌드는 이름만 `(dev)`이고 appId=desktop, scheme=clipper, userData=Clipper Studio다. 이를 위 새 개발판 값으로 바꾼다. production builder 생성기는 옛 appId/protocol 문자열을 엄격하게 치환하므로 개발 base만 수정하면 운영 빌드가 깨질 수 있다. 생성기와 양쪽 계약 테스트를 함께 바꾼다.

userData/sessionData/auth.bin/로컬 Nest dataRoot/플러그인 runtime의 실제 경로를 새 루트로 연결한다. 운영에 적용 중인 가변 모델 캐시 격리도 새 개발판에 적용한다. 옛 데이터의 자동 fallback 읽기/쓰기는 넣지 않는다. OS 공유 폰트 같은 읽기 전용 자산까지 복사하거나 분리하지 않는다.

패키지 Nest는 이미 동적 포트를 사용하므로 무조건 고정 포트를 새로 만들지 않는다. plugin 포트·single-instance lock·자식 프로세스 종료·Windows NSIS 프로세스 검사에서 다른 앱을 막거나 종료하지 않는지 검증한다. 로그인 저장소는 재로그인 후 앱별 분리와 로그아웃 상호 비간섭을 검증한다.

### B. 로그인: 새 요청을 새 프로토콜로만 반환

주요 파일:

- `desktop/clipper_electron/src/main/auth/google-login.ts`
- `desktop/clipper_electron/src/main/auth/deeplink.ts`
- `web/clipper_web_api/src/modules/auth/presentation/auth.controller.ts`
- `web/clipper_web_api/src/modules/auth/presentation/desktop-redirect.ts`
- `web/clipper_web_api/src/modules/auth/application/auth.service.ts`
- `web/clipper_web_api/src/modules/auth/dto/auth-state.ts`
- `web/clipper_infra/apps/compose.yml` 및 배포 환경 예제

현재 packaged 앱은 `client=desktop`만 보내며 서버는 전역 `DESKTOP_REDIRECT`로 돌아간다. 이 환경값만 새 scheme으로 바꾸면 옛 앱이 시작한 로그인도 새 앱으로 보낼 수 있다. 따라서 환경값 교체만으로 완료하지 않는다.

변경안: 새 앱 로그인 요청에 대상 구분(`desktopTarget=development|production`)을 명시하고, 서버가 배포 환경에 허용된 대상만 고정 callback으로 연결한다. callback 도착 시 시작한 대상 정보의 변조·소실을 검증한다. target 미지정 옛 desktop 요청은 새 앱으로 자동 연결하지 않고 업데이트 안내로 종료한다. 일반 웹 로그인과 별도 web handoff는 유지한다. 임의 returnUrl이나 잘못된 target을 clipper로 fallback시키지 않는다.

현재 OAuth state는 base64url JSON이며 서명된 상태가 아니다. 후속 세부 계획은 기존 RSA 키의 별도 audience로 서명한 desktop state(5분)와 앱 메모리의 PKCE verifier, 일회성 code의 target/requestId/challenge 저장 및 원자적 소비로 계약을 구체화했다. user DB nullable 컬럼 추가가 필요하지만 사용자/세션/금융 데이터 삭제는 없다. 계획 작성이지 구현·DB 적용 완료가 아니다.

### C. 업데이트: dev 채널과 오게시 방지

주요 파일:

- `web/clipper_web_api/src/modules/releases/domain/release.model.ts`
- `web/clipper_web_api/src/modules/releases/presentation/dto/start-build.dto.ts`
- `web/clipper_web_api/src/modules/releases/presentation/dto/publish-artifact.dto.ts`
- `web/clipper_web_api/src/modules/releases/presentation/dto/release-update-feed-params.dto.ts`
- `web/clipper_web_api/src/modules/releases/infrastructure/typeorm-releases.repository.ts`
- `web/clipper_web_api/docs/api/openapi.yaml`
- `web/clipper_web_admin/src/app/features/portal/versions/` 아래 모델·store·게시 UI
- `web/clipper_infra/runner/release-runner.mjs`

현재 서버 허용 채널은 stable/rc/alpha, DB 채널은 varchar다. **dev enum/검증 선택지 추가만으로는 채널 DB migration이 필요하지 않다.** 다른 auth/메타데이터 변경의 migration 여부와 혼동하지 않는다.

현재 관리자 게시 동작은 stable 고정이고 Windows 빌드는 rc 고정이다. 새 dev 빌드/게시를 명시적으로 선택하고 확인창에 실제 대상 채널을 표시하도록 한다.

현재 서버는 artifact의 앱 종류와 게시 채널의 적합성을 검사하지 않는다. 새 개발판을 dev만으로 제한하고 운영 산출물을 dev에 게시하지 못하게 서버에서 막는다. 정상 운영 rc→stable 승격은 보존한다. 게시뿐 아니라 rollback/feed에서도 부적합 파일을 제공하지 않도록 한다. 파일명만 신뢰하지 않고 빌드 설정과 산출물 identity의 일치를 검사한다. 옛 개발판 stable 대상에 새 개발판 파일을 공급하지 않는다.

현재 runner의 build env whitelist에는 앱 환경/채널 전달이 없다. 서버 build job→runner→Electron builder/runtime config까지 명시적으로 환경/채널을 전달해야 한다. 단순히 runner 환경파일에 값 하나 추가하는 것으로 끝내지 않는다. 앱에서도 새 개발판이 stable로 기본 fallback하지 않게 채널을 빌드 identity와 결속한다.

### D. 템플릿: 새 이관 기능보다 실제 왕복 검증 우선

현재 export/import 서비스는 `.cliptpl` ZIP의 템플릿·이미지·배경·포함 가능한 폰트를 처리한다. 누락 자산 경고 및 중복 ID skip이 있으므로 구현 존재만으로 보존을 보장하지 않는다. 옛 다중 variant 데이터는 flatten 단계에서 하나가 선택되는 경로도 확인했다. 실제 옛 export 파일에 해당 데이터가 있는지 먼저 검사한다.

주요 파일: `desktop/clipper_nestjs/src/modules/template-builder/application/template-builder-export.service.ts`, `template-builder-import.service.ts`, `domain/template-builder-store-flatten.ts` 및 기존 template bundle/font 테스트.

직원용 흐름은 옛 앱에서 템플릿 내보내기→새 앱에서 가져오기→결과 확인이다. 실제 옛 배포본에 내보내기 UI가 있는지도 확인한다. 가져오기 후 레이아웃/비율/이미지/배경/폰트/편집 후 저장/재시작 복원이 유지되어야 통과다. 폰트 라이선스상 포함 불가·누락/손상 파일·ID 중복은 조용한 성공으로 처리하지 않고 구분해 안내한다. 보존 결함 발견 시 별도 수정 범위를 제시한다. 사용자 샘플은 아직 검사하지 않았다.

## 4. 구현 순서와 통과 기준

1. 위 연결 경계를 포함한 변경안 확인 완료. 저장소별 세부 TDD 계획 작성 완료, Mac 업데이트 ZIP 확장은 기존 정책대로 HOLD이며 필수 게이트 아님.
2. Electron dev/prod 설정 및 로컬 API 빌드 계약 수정. 생산 앱 값 불변·새 dev 값·feed 선택·가변 경로 독립 자동 테스트.
3. Web API/Electron 로그인 대상 계약 구현. 구/신/운영 로그인 동시 시도, 잘못된 target/콜백, 재전송, 앱 종료 후 콜백 시나리오 검증.
4. Web API/Admin/Infra dev 빌드·게시·feed 연결. dev→stable 오게시 및 잘못된 rollback 차단 테스트. runner가 실제 산출물에 새 identity/채널을 넣는지 검증.
5. macOS 패키지에서 옛/새 앱 동시 존재 및 운영/새 dev 동시 실행 검증. 단순 plist 검사와 실제 로그인 성공을 각각 기록. 이 단계에 실제 ML 실행은 포함하지 않는다.
6. 실제 옛 템플릿→빈 새 데이터 루트 이관 검증. 이후 Windows NSIS 설치·실행·로그인·업데이트는 사용자 Windows 장비에서 실행할 안내 제공.

자동 테스트 통과만으로 Windows 설치·서명/공증·실제 업데이트가 통과했다고 쓰지 않는다. 새 scheme은 지정 앱 사이의 충돌을 없애기 위한 것으로, 제3의 악성 앱이 같은 scheme을 등록할 수 없는 OS 보안 보장을 뜻하지 않는다. 모든 환경에서 문제 절대 없음 대신 위 실패 경계를 검증한다.

## 5. 조사 결과와 이번 변경 내역

- 원본 8개 제품 저장소: integration/dev-pg-local-validation-20260917, 조사 시 clean. 이번 조사에서 fetch/pull/checkout/merge/제품 수정 없음.
- 변경은 `.codex` 설계·계획·인계 기록뿐. 제품 전체/대상 테스트·패키징·서버 API 호출·DB 작업은 이번 조사에서 실행하지 않음. 설치된 updater의 순수 findFile 함수에 모형 DMG/ZIP 입력을 넣는 읽기 전용 검증만 실행: DMG-only 후보 없음, ZIP 포함 시 ZIP 선택 PASS.
- 서버 직접 접속·개발/운영 DB 변경·배포 없음. 실제 ML 및 Build 5 전체 QA HOLD.
- 다음: Mac 자동 업데이트 보류를 유지한 승인 범위의 계획 실행. ZIP 확장 승인을 다시 요구하지 않는다. 독립 개발판 전환 완료 전 DB 복제본 리허설로 자동 진행하지 않음.
- 이전 macOS `clipper://` 등록 정리의 조회 명령/실행 이력은 [별도 기록](2026-09-17-macos-dev-oauth-handler-validation.md)을 따른다. 새 독립 프로토콜 전환 구현 증거로 재사용하지 않는다.
