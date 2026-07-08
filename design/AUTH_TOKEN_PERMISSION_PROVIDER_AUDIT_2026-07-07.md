# Auth, Token, Permission, License, API Key Audit

작성일: 2026-07-07  
작성 목적: Google 로그인, JWT 저장, local/dev 저장 위치, auth/token/권한/이용권/API key/provider routing의 현재 구현 상태와 문서 상태를 한 번에 파악하기 위한 감사 문서.

## 0. 범위와 원칙

이 문서는 구현 계획서가 아니다. 현재 repo와 `clipper_docs`에 실제로 들어 있는 내용을 기준으로, 무엇이 구현되어 있고 무엇이 임시/미구현인지 구분한다. 기존 설계가 이치에 맞으면 채택하고, 아니면 뜯어고칠 수 있다는 전제로 판단한다.

민감값은 출력하지 않았다. env 파일의 실제 값은 문서에 쓰지 않는다. 아래에는 변수명과 저장 위치, 위험 유형만 적는다.

확인 대상:

- `desktop/clipper_electron`
- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `web/clipper_web_api`
- `clipper_docs`
- 기존 `.codex/design` 작업 노트

확인하지 않은 것:

- 실제 운영 env 값
- Google/OAuth/API key 실값
- 현재 서버 DB의 실제 row
- release/version publish 재개 작업

## 1. 한 줄 결론

Google 로그인과 desktop JWT 저장 흐름은 이미 실제 구현되어 있다. Electron은 `safeStorage`로 JWT를 암호화해 `auth.bin`에 저장하고, Angular는 앱 메인 라우트 진입 전에 `/me`로 세션을 검증한다.

하지만 전체 auth/permission/license/provider 보안 모델은 아직 완성된 상태가 아니다. `web_api`에는 customer JWT, operator JWT, 수동 이용권 발급, token bucket 차감, Naver API key 암호화 저장까지 일부 구현되어 있지만, provider proxy 엔드포인트에는 사용자 JWT/이용권 검증이 아직 연결되어 있지 않다. `desktop/clipper_nestjs`도 현재는 local/trusted-header context만 있고, JWT 검증/전달/이용권 정책은 stub에 가깝다.

가장 중요한 설계 판단:

- 유지할 방향: `web/clipper_web_api`를 신원/이용권/API key/외부 provider 호출의 단일 출처로 두는 방향은 맞다.
- 고칠 부분: provider proxy 호출을 임시 service token이나 무인증으로 두면 안 된다. 설치형 앱의 provider-backed 기능은 user JWT를 local NestJS가 web_api로 relay하고, web_api가 이용권/권한/차감 정책을 판단해야 한다.
- 문서 정리 필요: `clipper_docs`와 `web_api/docs/api/openapi.yaml`에는 현재 코드와 어긋난 오래된 설명이 있다.

## 2. 현재 브랜치/작업 상태

조사 시점의 주요 repo는 모두 `dev...origin/dev` 상태였다.

- `desktop/clipper_electron`: `dev...origin/dev`
- `desktop/clipper_angular`: `dev...origin/dev`
- `desktop/clipper_nestjs`: `dev...origin/dev`
- `web/clipper_web_api`: `dev...origin/dev`

`.codex`는 로컬 문서 컨텍스트로만 사용한다. 이 문서도 push 대상이 아니다.

## 3. 기존 문서가 말하는 큰 방향

`clipper_docs`의 방향성은 대체로 일관된다.

### 3.1 `clipper_web_api`가 SoT

`clipper_docs/AGENTS.md`, `clipper_docs/architecture/CLIPPER_WEB_PLATFORM_HANDOFF.md`, `clipper_docs/glossary.md`는 다음 원칙을 반복한다.

- `clipper_web_api` = 신원, 이용권, 결제의 단일 출처.
- `clipper_nestjs` = desktop 로컬 backend이며 trusted-header 소비자.
- 인증/회원/결제 로직을 desktop과 web_api 양쪽에 복제하지 않는다.

이 방향은 현재도 맞다. 다만 설치형 앱에서 web_api가 cloud에 있고 local NestJS가 사용자 PC 안에 뜨는 구조에서는, "trusted-header"만으로는 충분하지 않다. 누가 헤더를 안전하게 주입하는지가 아직 없다. 현재 설치형 앱 흐름에는 user JWT relay 설계가 별도로 필요하다.

### 3.2 Google OAuth 단독

`clipper_docs/adr/0002-google-only-auth.md`는 1차 출시에서 Google OAuth만 사용한다고 결정한다. 이메일/비밀번호와 추가 소셜은 후순위다.

현재 코드도 이 방향을 따른다.

- customer 로그인: Google OAuth + JWT
- local browser dev: dev-login endpoint
- operator/admin: 별도 email/password JWT

operator/admin은 customer Google login과 별도 축이다.

### 3.3 이용권은 구매 요청 -> 운영자 수동 발급

`clipper_docs/adr/0003-request-based-licensing.md`는 PG 자동결제 없이 구매 요청을 받고 운영자가 승인해 이용권을 발급하는 구조를 채택한다.

현재 `web_api`에는 이 흐름이 실제 코드로 일부 구현되어 있다. 다만 endpoint 이름과 상태 이름이 문서/OpenAPI와 drift가 있다.

### 3.4 secretless provider routing

`.codex/design/DESKTOP_SECRETLESS_PROVIDER_ROUTING_AND_DIALOG_PIPELINE_2026-07-01.md`와 `.codex/design/DESKTOP_WEB_API_ENTITLEMENT_AND_PROXY_WORKING_NOTES_2026-06-26.md`는 다음 원칙을 둔다.

- 설치형 앱 번들에 OpenAI/Naver/Kakao/Clova 같은 provider secret을 넣지 않는다.
- 외부 provider key는 `web_api`가 보유한다.
- desktop 기능 실행은 `Angular -> local NestJS -> web_api -> external provider`가 기본이다.
- Python plugin에는 user JWT나 provider secret을 넘기지 않는 쪽이 안전하다.
- 크레딧/이용권 차감은 provider API 호출 단위가 아니라 사용자-facing operation 단위로 판단한다.

이 원칙도 맞다. 현재 구현은 이 원칙 중 provider key 이동과 일부 routing만 반영했고, auth/entitlement/charge는 아직 반영하지 않았다.

## 4. Google 로그인과 JWT 저장 구현

### 4.1 web_api customer auth

관련 코드:

- `web/clipper_web_api/src/modules/auth/presentation/auth.controller.ts`
- `web/clipper_web_api/src/modules/auth/application/auth.service.ts`
- `web/clipper_web_api/src/modules/auth/infrastructure/google.strategy.ts`
- `web/clipper_web_api/src/modules/auth/infrastructure/jwt.strategy.ts`
- `web/clipper_web_api/src/modules/users/**`

구현된 endpoint:

- `POST /auth/dev-login`
- `GET /auth/google`
- `GET /auth/google/callback`
- `POST /auth/logout`
- `GET /me`

JWT payload:

```text
sub = web_api users.id UUID
email
name
```

중요한 점은 JWT `sub`가 Google `sub` 원문이 아니라 `web_api` user DB의 UUID라는 것이다. Google `sub`는 user row 내부 식별/연결용으로 저장되고 API 응답에서는 제거된다.

JWT 검증:

- `Authorization: Bearer <token>`
- 또는 `clipper_token` cookie

`JwtStrategy`는 JWT를 검증한 뒤 `UsersService.findById(payload.sub)`로 user DB row를 다시 조회한다. 즉 JWT 서명만 맞으면 끝나는 것이 아니라, 해당 user가 DB에 있어야 한다.

### 4.2 desktop OAuth callback

관련 코드:

- `desktop/clipper_electron/src/main/auth/google-login.ts`
- `desktop/clipper_electron/src/main/auth/deeplink.ts`
- `desktop/clipper_electron/src/main/auth/token-store.ts`
- `desktop/clipper_electron/src/main/auth/auth-ipc.ts`
- `desktop/clipper_electron/src/main/auth/log-redaction.ts`

흐름:

```text
Angular login button
  -> Electron IPC startLogin
  -> system browser opens web_api /auth/google?client=desktop
  -> Google OAuth
  -> web_api callback signs JWT
  -> browser opens clipper://auth/callback?token=<JWT>
  -> Electron deep-link handler receives token
  -> token-store.saveToken()
  -> renderer receives deep-link event
  -> Angular AuthStore calls /me with Bearer token
```

현재 desktop callback은 JWT를 `clipper://auth/callback?token=...` query string으로 전달한다. 로그에는 token 값을 redaction하는 코드가 있지만, URL token 전달 자체는 장기적으로 hardening이 필요하다. `web_api/docs/auth-setup.md`에도 one-time code 교환 방식이 후속 보안 작업으로 언급되어 있다.

### 4.3 `auth.bin`은 무엇인가

`auth.bin`은 Electron main process가 받은 JWT를 저장하는 로컬 파일이다.

코드상 경로:

```text
join(app.getPath('userData'), 'auth.bin')
```

`productName`이 `Clipper2`이고 별도 `app.setPath('userData', ...)`는 확인되지 않았다. 일반적인 위치는 다음과 같다.

```text
macOS   ~/Library/Application Support/Clipper2/auth.bin
Windows %APPDATA%\Clipper2\auth.bin
Linux   ~/.config/Clipper2/auth.bin
```

왜 여기에 저장하는가:

- `userData`는 Electron이 사용자별 앱 데이터를 저장하라고 제공하는 표준 writable 위치다.
- app resources는 읽기 전용이거나 앱 업데이트 때 교체될 수 있다.
- 작업 상태, plugin venv, 다운로드된 ffmpeg/model, cookie 파일 등도 userData 아래에 저장되는 구조와 맞다.

파일 내용:

- `safeStorage.isEncryptionAvailable()`가 true면 `safeStorage.encryptString(token)` 결과가 저장된다.
- false면 현재 코드는 평문 UTF-8로 저장하고 warning을 남긴다.

중요한 위험:

- 평문 fallback은 dev/CI에서는 편할 수 있지만 packaged production에서는 허용하면 안 된다.
- 현재 devapp과 packaged가 같은 `Clipper2` userData를 공유할 가능성이 높다. 그러면 dev login token과 packaged token이 섞일 수 있다.

권장:

- packaged build에서 `safeStorage` 사용 불가면 저장을 거부하거나 memory-only session으로 degrade한다.
- devapp userData를 `Clipper2 Dev`처럼 분리할지 결정한다.

### 4.4 localhost/dev 환경 저장 방식

로컬 개발에는 두 종류가 있다.

1. Electron devapp

`desktop/clipper_electron`의 `start:devapp`은 Electron을 띄운다. 이 경우 renderer는 `ElectronAuthBackend`를 사용하고, token 저장은 packaged 앱과 같은 Electron `safeStorage/auth.bin` 경로를 탄다.

2. Browser-only Angular local dev

`ng serve`처럼 Electron 없이 Angular를 띄우는 경우 `LocalAuthBackend`를 사용한다.

관련 코드:

- `desktop/clipper_angular/src/core/auth/auth-backend.ts`
- `desktop/clipper_angular/src/environments/environment.ts`
- `desktop/clipper_angular/src/environments/environment.local.ts`

저장 방식:

```text
localStorage key = clipper.devToken
```

로그인 방식:

```text
POST {webApiBaseUrl}/auth/dev-login
```

이 endpoint는 `DEV_LOGIN_ENABLED=true`이고 `NODE_ENV`가 production이 아닐 때만 동작한다.

즉 browser-only localhost 개발에서는 `auth.bin`을 쓰지 않는다.

### 4.5 Angular login gate

관련 코드:

- `desktop/clipper_angular/src/core/auth/auth.store.ts`
- `desktop/clipper_angular/src/core/auth/auth.guard.ts`
- `desktop/clipper_angular/src/app/app.routes.ts`
- `desktop/clipper_angular/src/app/app.config.ts`
- `desktop/clipper_angular/src/features/auth/pages/login/*`

현재 구조:

- 앱 초기화 시 `AuthStore.loadSession()`을 fire-and-forget으로 호출한다.
- `authGuard`는 첫 session restore가 끝날 때까지 기다린다.
- root route의 대부분은 `canActivate: [authGuard]` 아래에 있다.
- 로그인하지 않으면 `/login`으로 보낸다.
- 로그인 성공 시 `/store`로 이동한다.

사용자가 정정한 요구사항인 "메인 화면 진입 전 로그인 필요"와 현재 구조는 대체로 맞다.

주의:

- Angular route guard는 앱 UI 진입을 막는다.
- local NestJS API 자체를 보호하지는 않는다.
- local NestJS는 현재 JWT를 검증하지 않으므로, local API를 직접 호출하면 `local` subject로 처리될 수 있다.

## 5. web_api base URL과 runtime config

### 5.1 Electron auth API base

`desktop/clipper_electron/src/main/auth/google-login.ts`의 `getApiBase()` 우선순위:

```text
CLIPPER_WEB_API_BASE_URL
CLIPPER_WEB_API_URL
packaged runtime override
https://dev-api.clipperstudio.ai
```

packaged runtime override는 `packaged-runtime-config.json`의 `webApiBaseUrl`에서 온다.

`--local-api` 빌드는 다음을 runtime config에 넣는다.

```text
webApiBaseUrl = http://127.0.0.1:3000
autoUpdateDisabled = true
```

일반 packaged build는 runtime config가 비어 있고 기본 dev API 또는 env override를 따른다.

### 5.2 Angular browser local

browser-only Angular local dev는 environment 파일의 `webApiBaseUrl`을 사용한다. 기본은 local web_api이다.

### 5.3 desktop local NestJS -> web_api

`desktop/clipper_nestjs/src/core/web-api/web-api-client.service.ts`는 `CLIPPER_WEB_API_BASE_URL`을 읽는다. 없으면 `web_api_not_configured`를 던진다.

현재 `WebApiClient`는 Authorization header를 붙이지 않는다. 이 점이 auth/entitlement track의 가장 큰 빈칸이다.

## 6. desktop NestJS auth 현황

관련 코드:

- `desktop/clipper_nestjs/src/core/auth/auth-provider.ts`
- `desktop/clipper_nestjs/src/core/auth/auth-context.service.ts`
- `desktop/clipper_nestjs/src/core/auth/license-policy.service.ts`
- `desktop/clipper_nestjs/src/core/execution/execution-scope.service.ts`
- `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts`

현재 auth mode:

```text
CLIPPER_AUTH_MODE=trusted-header 이고 x-clipper-subject가 있으면:
  subjectId = x-clipper-subject
  tenantId = x-clipper-tenant 또는 subjectId
  plan = x-clipper-plan
  authMode = trusted-header

그 외:
  subjectId = local
  tenantId = local
  plan = local
  authMode = local
```

현재 구현된 것:

- jobs/projects/variation/shortform 등 여러 endpoint에서 `AuthContextService.fromHttpHeaders()`를 호출한다.
- job 생성 시 `ownerSubjectId`를 저장한다.
- job list/get/cancel 등은 owner subject 기준으로 필터링한다.
- execution scope도 subject/tenant 기준으로 잡는다.

현재 구현되지 않은 것:

- user JWT 검증
- Angular/Electron token을 local NestJS로 전달하는 공통 interceptor
- local NestJS가 web_api로 Bearer token을 relay
- local NestJS 자체 route 보호
- license/entitlement policy

`LicensePolicyService.canStartPluginJob()`는 현재 항상 `{ allowed: true }`를 반환한다. 따라서 이름은 있지만 실제 이용권 정책은 없다.

## 7. web_api operator/admin auth 현황

관련 코드:

- `web/clipper_web_api/src/modules/auth/presentation/operator-auth.controller.ts`
- `web/clipper_web_api/src/modules/auth/application/operator-auth.service.ts`
- `web/clipper_web_api/src/modules/auth/infrastructure/operator-jwt.strategy.ts`
- `web/clipper_web_api/src/modules/auth/infrastructure/operator.entity.ts`
- `web/clipper_web_api/src/core/database/seeds/seed-operator.ts`

구현된 endpoint:

- `POST /admin/auth/login`
- `GET /admin/me`
- `POST /admin/auth/logout`
- `GET /admin/operators`

operator JWT:

- Bearer token만 받는다.
- payload에 `typ: operator`를 넣고 strategy에서 확인한다.
- customer JWT와 같은 `JWT_SECRET`을 사용하지만 `typ`로 구분한다.

한계:

- 현재 `operators` table은 email/password_hash/created_at 정도만 있다.
- `Operator` model에는 role/status가 있지만 repository는 role을 항상 `operator`, status를 항상 `active`로 만들어 반환한다.
- role별 권한 분리는 아직 실질 구현되어 있지 않다.
- logout은 `{}`만 반환하고 token blocklist는 구현되어 있지 않다.
- OpenAPI에는 logout blocklist 같은 설명이 있지만 현재 코드와 다르다.

## 8. web_api 이용권/토큰 차감 현황

관련 코드:

- `web/clipper_web_api/src/modules/billing/**`
- `web/clipper_web_api/src/core/database/migrations/admin/*CreateLicenseSchema*`
- `web/clipper_web_api/src/core/database/migrations/admin/*RenameBillingToSnakeCase*`

구현된 customer endpoint:

- `GET /plans` 공개
- `POST /purchase-requests` customer JWT 필요
- `GET /purchase-requests` customer JWT 필요
- `PATCH /purchase-requests/:id/resubmit` customer JWT 필요
- `GET /licenses/current` customer JWT 필요
- `POST /licenses/consume` customer JWT 필요

구현된 admin endpoint:

- `GET /admin/purchase-requests`
- `GET /admin/purchase-requests/pending`
- `PATCH /admin/purchase-requests/:id`
- `GET /admin/members`
- `GET /admin/stats`

데이터 위치:

- user DB: `users`
- admin DB: `plans`, `purchase_requests`, `licenses`, `token_usage`, `operators`, `naver_search_keys`
- release DB: release management 관련 table

주의: 과거 문서에는 user DB에 license/credit이 들어가는 듯한 표현이 있지만 현재 구현은 billing이 admin DB에 있다. cross-DB FK는 걸 수 없고, billing row의 `user_id`는 user DB의 UUID를 앱 레벨로 참조한다.

token 차감:

- `LicensesService.consume(userId, tokens, source)`
- active license bucket을 만료 임박순으로 잠근다.
- 충분한 token balance가 있으면 `tokens_used`를 늘리고 `token_usage` row를 저장한다.
- 부족하면 409 Conflict.

구현되지 않은 것:

- provider-backed operation 시작 시 자동 entitlement check
- operation 단위 reserve/capture/refund ledger
- provider 호출과 token 차감의 일관된 transaction/outbox 정책
- 어떤 기능이 몇 token을 쓰는지에 대한 서버 정책
- local NestJS job id와 web_api charge id/idempotency key 연결

즉 web_api에는 "차감 primitive"는 있지만, 설치형 앱 workflow에 붙은 "이용권/차감 정책"은 아직 없다.

## 9. API key와 외부 provider 호출 현황

### 9.1 API key admin

관련 코드:

- `web/clipper_web_api/src/modules/api-keys/**`
- `web/clipper_web_api/src/shared/crypto/secret-cipher.ts`

구현된 admin endpoint:

- `GET /admin/api-keys`
- `POST /admin/api-keys`
- `PATCH /admin/api-keys/:id`
- `DELETE /admin/api-keys/:id`
- `POST /admin/api-keys/:id/activate`
- `POST /admin/api-keys/test`

guard:

- `OperatorJwtGuard`

구현 내용:

- 현재 모델은 Naver image search key 중심이다.
- `clientSecret`은 `SecretCipher`로 AES-256-GCM 암호화 후 DB에 저장한다.
- 암호화 key는 `API_KEY_ENC_SECRET`에서 온다.
- API 응답은 secret을 반환하지 않고 mask만 준다.
- active/standby/exhausted/disabled 상태와 daily usage/rotation이 있다.

한계:

- OpenAI key는 이 admin API key storage에 들어가 있지 않고 `OPENAI_API_KEY` env를 직접 사용한다.
- OpenAPI는 Naver/OpenAI 모두를 다루는 일반 API key 모델처럼 설명하지만 현재 구현은 Naver 중심이다.
- operator role 세분화는 없다.

### 9.2 provider proxy endpoint

현재 provider 관련 endpoint 상태:

| endpoint | 현재 guard | provider key 위치 | 상태 |
|---|---|---|---|
| `POST /media/search` | 없음 | admin DB의 Naver key, `API_KEY_ENC_SECRET`으로 복호화 | desktop auth 설계 전까지 무인증으로 열려 있음 |
| `POST /llm/script` | 없음 | `OPENAI_API_KEY` env | prompt shortform script용, 무인증 |
| `POST /llm/variation` | `ScriptServiceTokenGuard` | `OPENAI_API_KEY` env | static bearer token guard 사용 |
| `POST /dialog-highlight/llm` | 없음 | `OPENAI_API_KEY` env | dialog LLM operation용, 무인증 |

`MediaSearchServiceTokenGuard`는 존재하지만 현재 `MediaSearchController`에 붙어 있지 않다. 코드 주석도 "사용자/서비스 인증은 desktop auth 설계에서 일괄 도입"이라고 말한다.

`ScriptServiceTokenGuard`는 `/llm/variation`에만 붙어 있다. 이 guard는 static shared secret을 Bearer token으로 비교한다. 이 방식은 "진짜 사용자 권한/이용권"을 표현하지 못하므로 최종 설계로 보기 어렵다.

정리:

- provider key를 desktop에서 web_api로 옮기는 방향은 구현되고 있다.
- 그러나 provider proxy surface 보호는 아직 임시 상태다.
- user JWT/entitlement/license check가 provider endpoint에 들어가야 한다.

## 10. desktop -> web_api provider routing 현황

관련 코드:

- `desktop/clipper_nestjs/src/core/web-api/web-api-client.service.ts`
- `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/web-api-member-image-source.ts`
- `desktop/clipper_nestjs/src/modules/projects/infrastructure/web-api-clipper-studio-script-generator.ts`
- `desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-web-api.client.ts`
- `desktop/clipper_nestjs/src/modules/variation/infrastructure/remote-variation-copy-rewriter.ts`

구현된 routing:

- Dance member image search -> local NestJS -> `web_api /media/search`
- Shortform prompt script generation -> local NestJS -> `web_api /llm/script`
- Dialog Highlight LLM operations -> local NestJS -> `web_api /dialog-highlight/llm`

`WebApiClient` error code:

- `web_api_not_configured`
- `web_api_unreachable`
- `web_api_timeout`
- `provider_failed`

Angular error catalog도 위 코드 일부를 사용자 문구로 매핑한다.

아직 다른 패턴인 곳:

- Variation copy rewrite는 `CLIPPER1_VARIATION_ENDPOINT`와 `CLIPPER1_LLM_SCRIPT_API_KEY`를 직접 읽고, endpoint가 없으면 deterministic fallback을 쓴다.
- 이 경로는 최신 `WebApiClient` 패턴과 다르다.

큰 한계:

- `WebApiClient`는 Authorization header를 붙이지 않는다.
- 따라서 web_api는 현재 provider call을 어느 사용자 요청인지 알 수 없다.
- 이용권/차감 정책을 적용할 수 없다.

## 11. OpenAPI와 문서 drift

### 11.1 `clipper_web_api/docs/api/openapi.yaml`

중요한 drift:

- OpenAPI: `/license-requests`
- 현재 코드: `/purchase-requests`

상태 이름 drift:

- OpenAPI/client 과거 모델: `issued`
- 현재 코드/DB: `approved`, `rejected`, `returned`, `pending`

logout 설명 drift:

- OpenAPI는 token blocklist를 언급한다.
- 현재 `/auth/logout`은 cookie clear만 하고 server-side blocklist는 없다.

Google callback 설명 drift:

- OpenAPI는 JSON debug response와 error redirect를 자세히 설명한다.
- 현재 controller는 desktop이면 HTML completion page를 반환하고 JS로 `clipper://...`를 연다.

provider proxy drift:

- OpenAPI에 `/media/search`, `/llm/script`, `/llm/variation`, `/dialog-highlight/llm` 계약은 확인되지 않았다.
- 현재 설치형 앱은 이 endpoint들을 실제로 사용한다.

### 11.2 `web_api/docs/auth-setup.md`

유용한 부분:

- OAuth env 변수명
- web/desktop flow 설명
- JWT URL 전달 hardening follow-up
- nonce validation follow-up
- refresh token 미구현 설명

낡은 부분:

- in-memory user store 설명이 남아 있다. 현재는 TypeORM user repository가 사용된다.

### 11.3 `clipper_docs`

`clipper_docs`는 방향성과 결정 기록에는 유용하다. 다만 6월 초 status 문서는 당시 snapshot이라 현재 구현 상태와 맞지 않는 부분이 있다.

설계 이어갈 때 신뢰 우선순위:

1. 현재 코드
2. 최신 `.codex/design` working note
3. `clipper_docs/AGENTS.md`, ADR, glossary
4. 오래된 status report와 OpenAPI 상세 설명은 drift 확인 후 사용

## 12. 구현 상태 분류

### 구현됨

- Customer Google OAuth 시작/콜백/JWT 발급
- `/me` JWT 검증
- Electron deep link 수신
- Electron `safeStorage` token 저장/조회/삭제
- Angular login page, session restore, route guard
- Browser local dev-login + localStorage token 저장
- Operator email/password login + operator JWT
- 수동 구매 요청/운영자 승인/이용권 발급
- active license 조회
- token bucket 차감 primitive
- Naver API key 암호화 저장/rotation
- web_api provider call 일부: Naver image, OpenAI script/variation/dialog
- desktop secretless routing 일부: Dance/Shortform/Dialog
- provider routing error code 일부
- packaged provider secret key-name scan 일부

### 부분 구현

- `clipper_nestjs` AuthContext/ownerSubjectId 분리
- trusted-header mode
- OpenAPI auth/billing/admin 계약
- operator role/status 모델
- API key admin 모델
- provider error classification
- web_api base URL runtime config

### dummy 또는 임시

- `desktop/clipper_nestjs` `LicensePolicyService`: 항상 allowed
- `ScriptServiceTokenGuard`: 사용자 권한/이용권이 아닌 static shared token
- `MediaSearchServiceTokenGuard`: 존재하지만 현재 media search에 미사용
- provider endpoints 무인증 상태
- operator logout: server-side invalidation 없음
- OAuth state nonce: 생성은 있으나 desktop/client에서 동일성 검증 구조는 불완전

### 미구현

- 설치형 앱 local NestJS API에 user JWT 전달
- local NestJS의 JWT 자체 검증 또는 안전한 token relay 정책
- `WebApiClient` Authorization header relay
- provider endpoint의 `JwtAuthGuard`
- provider operation별 entitlement/license check
- operation 단위 reserve/capture/refund/ledger
- idempotency key 기반 중복 차감 방지
- refresh token 또는 장기 session 갱신
- desktop OAuth one-time code 교환
- dev/prod token 저장소 분리
- OpenAPI와 현재 route의 contract 정합화
- role-based admin authorization

## 13. 설계 평가

### 13.1 채택해도 되는 방향

`web_api`를 신원/이용권/API key/provider 호출의 SoT로 두는 방향은 맞다. 설치형 앱에 provider key를 넣지 않고, provider-backed 기능은 web_api를 거치는 구조도 맞다.

Electron `safeStorage`로 JWT를 저장하는 방식도 방향은 맞다. JWT는 bearer credential이기 때문에 클라이언트에 저장할 수밖에 있지만, 저장 위치와 로그/노출 정책을 엄격히 해야 한다.

사용자가 정정한 요구사항처럼, 로그인은 "메인 화면 진입 gate"로 두고, 이후 기능별로 web_api 필요 여부를 나누는 것이 맞다.

```text
로그인 성공 -> 메인 화면 진입

로컬 기능:
  web_api 호출 없이 계속 사용 가능

provider/이용권/권한 필요한 기능:
  local NestJS -> web_api 검증/호출 필요
  web_api 장애 시 해당 기능만 실패
```

이 모델은 UX와 보안의 균형이 좋다.

### 13.2 바꿔야 하는 방향

static service token으로 desktop provider call을 보호하는 방식은 최종 설계로 부적합하다.

이유:

- user identity가 없다.
- 이용권/차감 정책을 적용할 수 없다.
- 설치형 앱에 static token을 넣으면 추출 가능하다.
- token이 유출되면 모든 사용자/기능을 대표하는 권한이 된다.

따라서 provider proxy endpoint는 user JWT 기반으로 보호해야 한다. service token은 release runner 같은 진짜 server-to-server actor에는 쓸 수 있지만, 설치형 앱 사용자 기능 권한으로 쓰면 안 된다.

### 13.3 권장 target 흐름

로그인:

```text
Angular
  -> Electron startLogin
  -> web_api Google OAuth
  -> Electron safeStorage auth.bin
  -> Angular /me
  -> 메인 화면
```

로컬-only 기능:

```text
Angular
  -> local NestJS
  -> local JSON/file/plugin/render
```

provider-backed 기능:

```text
Angular
  -> local NestJS
     Authorization: Bearer <user JWT>
  -> web_api
     Authorization: Bearer <same user JWT>
  -> web_api checks:
     user exists
     license/entitlement/operation policy
     idempotency/reserve if needed
  -> web_api calls provider with server-held key
  -> local NestJS continues workflow
```

Python plugin:

```text
local NestJS
  -> Python media stage
```

Python에는 user JWT와 provider key를 넘기지 않는 것이 기본값으로 안전하다. 꼭 필요하면 job-scoped operation token을 별도 설계해야 한다.

### 13.4 web_api 장애/offline 정책

권장 정책:

- 앱 메인 진입은 저장된 session이 valid하면 가능.
- web_api가 일시적으로 끊긴 상태에서 이미 앱에 들어와 있다면, 로컬-only 기능은 계속 사용 가능.
- provider-backed 기능, 이용권 확인, 크레딧 차감, API key 필요한 기능은 "서버에 연결할 수 없음"으로 실패.
- 실패 코드는 `web_api_unreachable` 또는 `web_api_timeout`처럼 구분한다.

단, 앱 첫 실행/login gate에서 web_api가 완전히 안 되면 로그인 자체가 불가능하다.

## 14. 보안상 즉시 주의할 점

### 14.1 JWT in URL

현재 desktop callback은 JWT를 URL query로 넘긴다. log redaction은 되어 있지만, URL에 bearer credential을 담는 구조 자체는 production hardening 대상이다.

권장:

```text
clipper://auth/callback?code=<one-time-code>
Electron -> web_api POST /auth/desktop/exchange
web_api -> JWT
```

이때 state/nonce/PKCE까지 같이 정리해야 한다.

### 14.2 `safeStorage` fallback

현재 encryption unavailable이면 평문 저장한다.

권장:

- dev/CI에서는 허용 가능.
- packaged production에서는 hard fail 또는 memory-only.

### 14.3 dev/prod token 저장소 혼합

devapp과 packaged가 같은 `Clipper2` userData를 쓰면 token과 local state가 섞인다.

권장:

- devapp에서 `app.setPath('userData', <Clipper2 Dev path>)` 적용 여부 결정.
- 최소한 문서에 경로와 reset 방법 명시.

### 14.4 committed env hygiene

환경 파일 값은 이 문서에 출력하지 않는다. 이전 조사 기록상 예시 env에 placeholder가 아닌 실제 OAuth 값처럼 보이는 항목이 관찰된 적이 있으므로, committed example env는 placeholder만 남기고 실제 값은 rotate/sanitize하는 것이 안전하다.

### 14.5 provider endpoint 무인증

현재 `/media/search`, `/llm/script`, `/dialog-highlight/llm`는 provider 비용을 발생시킬 수 있는데 사용자 인증이 없다.

권장:

- auth 설계가 확정되기 전까지 public exposure/routing을 인프라에서 제한한다.
- 코드 레벨에서는 `JwtAuthGuard` 또는 별도 desktop user operation guard를 붙인다.
- provider operation에는 entitlement/usage policy를 같이 묶는다.

## 15. 다음 설계에서 결정해야 할 것

1. local NestJS가 user JWT를 다루는 방식

권장 기본값:

```text
Angular -> local NestJS: Authorization Bearer user JWT
local NestJS -> web_api: same Bearer relay
```

local NestJS가 JWT를 완전 검증할지, web_api에 맡길지는 별도 결정이다. 최소한 local logs에 token이 남지 않도록 해야 한다.

2. provider endpoint auth policy matrix

각 endpoint별로 다음을 정해야 한다.

- customer JWT 필요 여부
- operator JWT 필요 여부
- service token 허용 여부
- entitlement check 여부
- token/credit reserve 여부
- rate limit/audit 여부

3. 이용권/크레딧 operation model

필요 개념:

- operation name
- idempotency key
- required plan/credits
- reserve/capture/refund 상태
- failure policy
- audit ledger

4. API contract 용어 정리

`license-requests`와 `purchase-requests`, `issued`와 `approved` 중 무엇을 외부 계약으로 쓸지 결정해야 한다.

권장:

- 사용자 화면 용어는 "구매 요청".
- 서버 내부 DB table은 `purchase_requests` 유지 가능.
- 외부 API는 한 가지 이름으로 통일한다.
- OpenAPI, Angular, admin, backend controller를 한 번에 맞춘다.

5. admin role/permission

현재 operator JWT는 있으나 role-based 권한은 없다.

권장:

- release publish, API key write, operator management는 `super-admin` 또는 명시 permission 필요.
- 일반 operator는 승인/조회 중심으로 제한.

6. OpenAI key 관리 방식

현재 Naver key는 DB 암호화 저장, OpenAI는 env다.

결정 필요:

- OpenAI도 admin API key storage로 옮길지
- model/provider 설정도 admin에서 관리할지
- provider별 rotation/usage metrics 범위

## 16. 권장 다음 작업 순서

1. OpenAPI/route drift 정리 spec 작성

특히 `/purchase-requests` vs `/license-requests`, provider proxy endpoint 문서화를 먼저 맞춘다.

2. 설치형 auth/token relay spec 작성

목표는 다음 한 문장으로 잡는다.

```text
로그인한 user JWT를 Electron/Angular가 안전하게 보관하고, provider/entitlement가 필요한 local NestJS 요청에만 Bearer로 붙이며, local NestJS는 이를 web_api로 relay한다.
```

3. provider endpoint authz matrix 작성

현재 무인증 provider endpoint를 어떤 guard/policy로 닫을지 endpoint별 표로 결정한다.

4. entitlement/operation ledger 설계

MVP에서 즉시 차감으로 갈지, reserve/capture/refund로 갈지 결정한다.

5. 구현

구현 시에는 release/version publish track과 분리한다. 현재 사용자 지시대로 release/version publish는 재개하지 않는다.

## 17. 요약 판단

기존 팀원의 safeStorage 기반 Google login 구현은 폐기할 수준은 아니다. 방향은 맞고, 실제로 Angular login gate까지 이어져 있다. 다만 다음 세 가지는 고쳐야 한다.

1. production에서 `auth.bin` 평문 fallback을 허용하지 않는다.
2. devapp과 packaged token 저장소를 분리할지 결정한다.
3. JWT URL 전달을 one-time code 교환으로 harden한다.

auth/permission/license/provider 전체 설계는 아직 완성된 것이 아니다. 현재는 secretless provider routing의 1차 기반만 있고, 사용자 JWT/이용권/차감이 provider 호출에 연결되어 있지 않다. 다음 설계는 기존 dummy/static service token 계열을 중심으로 이어가기보다, user JWT relay + web_api entitlement policy로 다시 잡는 것이 맞다.
