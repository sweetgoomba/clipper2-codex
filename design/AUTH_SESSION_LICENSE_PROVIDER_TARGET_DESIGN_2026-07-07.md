# Clipper Auth, Session, License, Provider Key Target Design

작성일: 2026-07-07
작성 목적: 설치형 Clipper 앱과 web/admin 플랫폼의 로그인, 인증, 권한, 이용권, 이용권 크레딧, 외부 provider 호출, API key 관리를 한 번에 이해하고 구현할 수 있도록 정리한다.

후속 구현 체크리스트: Phase 8 이후 남은 작업과 사용자가 추가 지적한 gap은 `.codex/design/AUTH_SESSION_LICENSE_PROVIDER_REMAINING_PHASES_2026-07-08.md`에 별도로 정리한다.

## 0. 문서 원칙

이 문서는 기존 구현을 그대로 유지하기 위한 문서가 아니다. 현재 구현 중 일부는 spike, dummy, 임시 guard, 문서 drift가 섞여 있으므로, 제품용 구조로 뜯어고치는 것을 전제로 한다.

민감값은 적지 않는다. env 값, OAuth secret, JWT private key, provider key 원문, DB 실제 row 값은 이 문서에 쓰지 않는다.

이 문서의 범위:

- Google 로그인과 설치형 앱 로그인 gate
- access token / refresh token / session table
- desktop deep link one-time code exchange
- user JWT와 operator JWT 분리
- local NestJS와 web_api 사이의 사용자 인증 전달
- 이용권 구매 요청, 승인, 활성화, 크레딧 차감/환불 정책
- provider-backed 기능의 권한/이용권/차감 정책
- API key/provider credential 관리
- 기존 static service token guard의 정리 방향
- 구현 순서와 검증 계획

이 문서의 비범위:

- release/version publish 재개
- 실제 PG 결제 연동
- 실제 provider key 값 정리
- production infra 세부 배포 절차
- 플랜별 플러그인 노출/잠금/상위 플랜 유도 정책
- 플러그인 스토어 목록의 web_api DB 관리
- `plugins`, `plan_plugin_entitlements`, `store_visibility` 같은 플러그인 entitlement 테이블

## 1. 한 줄 결론

`clipper_web_api`를 신원, 세션, 이용권, 이용권 크레딧, provider credential, 외부 provider 호출 권한의 단일 출처로 둔다.

설치형 앱은 로그인 후 메인 화면에 진입한다. 이후 제품 기능 시작점에서는 필요한 경우 web_api가 user/session/license/operation policy를 확인한다. 시작 권한을 통과한 뒤의 세부 로컬 편집/렌더/파일 작업은 매번 web_api를 왕복하지 않는다.

세션은 short-lived JWT access token + long-lived opaque refresh token + server-side session table로 관리한다. desktop OAuth callback은 token을 URL에 싣지 않고 one-time code만 deep link로 전달한 뒤, Electron이 web_api에 code를 교환해 access/refresh token을 받는다.

provider key는 설치형 앱에 넣지 않는다. provider key는 web_api가 보관하고, 운영자가 관리해야 하는 provider credential은 DB에 암호화 저장한다. JWT private key, DB password, API key encryption root secret 같은 bootstrap secret만 env/secret manager에 둔다.

## 2. 용어

| 용어 | 의미 |
|---|---|
| user | Google OAuth로 로그인하는 고객 사용자 |
| operator | 관리자 페이지에 로그인하는 운영자 |
| access token | API 호출에 쓰는 짧은 수명의 JWT |
| refresh token | 새 access token을 받기 위한 긴 수명의 재발급권 |
| session | 서버 DB가 관리하는 로그인 단위. 기기별로 생성된다 |
| opaque token | 문자열 자체에는 user/session 정보가 없고 서버 DB hash 조회로만 의미를 알 수 있는 랜덤 토큰 |
| JWT public key | web_api가 private key로 서명한 access JWT를 검증하기 위한 공개키. 유출되어도 JWT 위조는 할 수 없다 |
| one-time code | desktop deep link에 담기는 짧은 수명의 1회용 교환 코드 |
| license | 사용자가 보유한 이용권. 기간과 크레딧 한도를 가진다 |
| purchase request | 사용자가 플랜 구매를 신청한 내역 |
| operation | 사용자-facing 제품 실행 단위. 예: 템플릿 생성, 숏폼 생성, 대사 하이라이트 추출, 안무영상 하이라이트 추출 |
| credit cost | 제품 operation 실행 시 차감할 이용권 크레딧 수. 기존 코드/문서의 `token` 용어와 같은 과금 단위를 가리키며, 사용자-facing 표현은 `credit`으로 정리한다 |
| provider credential | Naver, OpenAI 등 외부 provider 호출에 필요한 서버 보유 자격증명 |
| provider usage | 제품 operation 내부에서 발생한 외부 provider 호출 기록. 예: Dance Highlight 실행 중 Naver 이미지 검색 |
| local-execution feature | 기능 본체가 로컬 앱/local NestJS에서 실행되는 기능. 제품 시작 권한 확인은 web_api를 거칠 수 있다 |
| provider-backed feature | 제품 실행 중 외부 provider 호출이 포함되는 기능. provider 호출은 web_api가 수행한다 |
| billable operation | 크레딧 차감/환불/audit의 기준이 되는 사용자-facing 제품 실행 단위 |

## 3. 현재 구현 상태 요약

현재 구현은 제품용 최종 설계가 아니라 여러 단계의 중간 상태다.

구현되어 있는 것:

- Google OAuth 시작/콜백/JWT 발급
- `/me` user JWT 검증
- Electron deep link 수신
- Electron `safeStorage` 기반 token 저장/조회/삭제
- Angular login page, session restore, route guard
- browser-only local dev-login + localStorage token 저장
- operator email/password login + operator JWT
- 수동 구매 요청, 운영자 승인, 이용권 발급 일부
- active license 조회와 기존 token bucket 차감 primitive. 목표 용어로는 credit bucket이다.
- Naver API key 암호화 저장/rotation 일부
- web_api provider endpoint 일부
- local NestJS -> web_api provider routing 일부

임시이거나 부족한 것:

- desktop OAuth callback이 `clipper://auth/callback?token=<JWT>`로 JWT를 URL에 직접 싣는다.
- refresh token/session table이 없다.
- `/auth/logout`은 서버 세션 revoke가 아니라 쿠키 삭제 중심이다.
- OpenAPI 문서에는 logout blocklist가 적혀 있으나 실제 구현은 아니다.
- OAuth state nonce는 생성되지만 충분히 검증되는 구조가 아니다.
- `desktop/clipper_nestjs`의 `LicensePolicyService`는 실질 정책 없이 allow에 가깝다.
- local NestJS는 user JWT를 web_api로 relay하지 않는다.
- provider endpoint 일부가 무인증이거나 static service token guard를 쓴다.
- `ScriptServiceTokenGuard`, `MediaSearchServiceTokenGuard`는 사용자 권한/이용권을 표현하지 못한다.
- OpenAI key는 env, Naver key는 DB 암호화 저장으로 provider credential 관리 방식이 섞여 있다.

기존 구현에서 유지할 방향:

- Google OAuth 단독 로그인
- Electron `safeStorage` 사용
- Angular route guard로 메인 화면 진입 전 로그인 요구
- `clipper_web_api`를 신원/이용권/provider credential의 SoT로 두는 구조
- provider key를 설치형 앱에 넣지 않는 secretless 방향

기존 구현에서 바꿀 방향:

- URL token 전달을 one-time code exchange로 변경
- access token + refresh token + session table 도입
- provider endpoint를 user JWT + entitlement/operation policy로 보호
- static service token guard를 설치형 사용자 기능 권한으로 쓰지 않음
- 이용권 credit bucket 병합/흡수 모델을 단순한 one-active-license + queue 모델로 정리
- provider credential 관리를 DB 암호화 저장 중심으로 통일

## 4. 큰 아키텍처

```text
Google OAuth
  -> web_api
     user/session/license/provider credential SoT

Electron main
  -> system browser login
  -> receives clipper:// deep link with one-time code
  -> exchanges code with web_api
  -> stores refresh token securely

Angular renderer
  -> login gate
  -> local workflow screens/actions
  -> attaches user access token only when a protected local/API call needs it

local NestJS
  -> local workflow orchestration
  -> does not own auth truth
  -> relays user access token to web_api for protected operation start/provider steps

Python plugin
  -> local media/model execution
  -> does not receive provider key
  -> does not receive refresh token
```

원칙:

- 인증과 이용권 판단은 web_api에서 한다.
- local NestJS는 사용자 컴퓨터 안에서 뜨는 backend이므로 최종 권한 판단자가 아니다.
- Python plugin에는 provider secret과 refresh token을 넘기지 않는다.
- provider-backed operation은 web_api가 provider key를 사용해 직접 호출한다.
- 이미 시작 권한을 통과한 로컬 내부 동작은 web_api 장애와 무관하게 가능한 범위에서 계속 진행할 수 있다.

## 5. 로그인과 세션 정책

### 5.1 채택 방식

채택:

```text
short-lived JWT access token
+ long-lived opaque refresh token
+ server-side session table
+ refresh token rotation
+ desktop one-time code exchange
```

비채택:

```text
long-lived JWT only
+ logout blocklist 중심 모델

opaque access token + opaque refresh token + session table을
기본 target으로 삼는 session-only 모델
```

session-only opaque 모델도 기술적으로 가능하고 기기 관리 측면에서는 매우 직관적이다. 그러나 ClipperStudio는 사용자 PC 안에서 local NestJS가 localhost HTTP server로 뜨므로, web_api에 가기 전에 local NestJS가 missing/fake/expired access token을 1차 차단할 수 있는 구조가 유리하다. 따라서 target은 JWT access token + opaque refresh token + server-side session table로 둔다.

### 5.2 access token

access token은 API 호출용 JWT다. JWT는 세션 관리를 대체하지 않는다. 짧게 쓰는 access ticket이고, 기기별 세션 관리와 revoke는 server-side session table이 담당한다.

권장:

- user access token 수명: 30분
- operator access token 수명: 15분
- 서명 알고리즘: RS256
- web_api만 private key로 access JWT를 발급
- local NestJS와 web_api는 public key로 access JWT를 검증
- local NestJS에는 public key PEM 파일을 앱 resource로 포함
- payload에 최소한 `sub`, `typ`, `sid`, `aud`, `iat`, `exp` 포함
- payload에 `iss`, `jti` 포함 권장
- user token과 operator token은 audience/type으로 명확히 구분

예시 payload:

```json
{
  "sub": "user-id",
  "typ": "user",
  "sid": "session-id",
  "aud": "clipper-user",
  "iss": "clipper-web-api",
  "jti": "token-id",
  "iat": 0,
  "exp": 0
}
```

access token은 DB에 저장하지 않는다. 서버는 JWT signature와 expiry를 검증하고, 필요한 endpoint에서는 `sid`로 session revoke 여부까지 확인한다.

검증 설정은 JWT header를 그대로 믿지 않고 코드에서 고정한다.

```text
algorithms = ["RS256"]
issuer = "clipper-web-api"
audience = "clipper-user" 또는 "clipper-operator"
typ = "user" 또는 "operator"
```

HS256 같은 대칭 서명은 설치형 앱/local NestJS에 적합하지 않다. HS256은 같은 secret으로 발급과 검증을 모두 하기 때문에, local NestJS에 secret을 넣으면 앱 패키지를 분석한 공격자가 secret을 얻어 JWT를 위조할 수 있다. RS256은 web_api가 private key로 서명하고 local NestJS는 public key로 검증만 하므로, 앱 안의 public key가 노출되어도 새 JWT를 만들 수 없다.

public key 배포:

```text
MVP:
  apps/resources/auth/jwt-public-key.pem 같은 PEM 파일을 앱 패키지에 포함
  local NestJS 시작 시 1회 읽고 메모리에 캐시

후속:
  web_api /.well-known/jwks.json에서 public key 목록을 받아와 캐시
  키 rotation이 필요해지면 JWKS로 전환
```

public key는 secret이 아니므로 숨길 수 있다고 가정하지 않는다. 다만 multi-line PEM 문자열은 env 변수보다 파일로 포함하는 편이 줄바꿈/escape 실수를 줄인다.

### 5.3 refresh token

refresh token은 새 access token을 받기 위한 재발급권이다.

권장:

- JWT가 아니라 cryptographically random opaque string
- 원문은 클라이언트에만 반환
- 서버 DB에는 refresh token 원문을 저장하지 않고 hash만 저장
- user refresh token 수명: 30일로 시작
- operator refresh token 수명: 8-12시간 또는 최대 7일 중 별도 결정
- `/auth/refresh`에서 사용할 때마다 refresh token을 새 값으로 rotation

정확한 저장 관계:

```text
클라이언트:
  access token 원문: 메모리 또는 safeStorage
  refresh token 원문: safeStorage

서버 DB:
  access token 원문: 저장 안 함
  refresh token 원문: 저장 안 함
  refresh token hash: 저장
  session row: 저장
```

### 5.4 교체와 유효기간

refresh token 교체와 유효기간은 다른 개념이다.

```text
교체:
  R1 -> R2 -> R3처럼 refresh token 문자열을 바꾸는 것
  /auth/refresh 성공 시 일어난다
  예전 refresh token 재사용을 감지하기 위한 보안 장치다

유효기간:
  이 로그인 세션을 언제까지 인정할지 정하는 것
  예: 로그인 후 30일
```

MVP 권장 정책:

```text
로그인 세션 유효기간 = 최초 로그인 시각 + 30일
refresh token은 중간에 계속 rotation
하지만 세션 만료일은 자동 연장하지 않음
```

나중에 UX를 더 좋게 하려면 sliding expiration을 도입할 수 있다.

```text
idle timeout = 마지막 사용 후 30일
absolute max = 최초 로그인 후 180일
```

MVP에서는 고정 만료 방식이 더 단순하다.

### 5.5 session table

권장 테이블: `user_sessions`

필드 예시:

```text
id
user_id
refresh_token_hash
status
device_id
device_label
platform
app_version
created_at
last_used_at
expires_at
revoked_at
rotated_at
replaced_at
revocation_reason
ip_hash
user_agent_hash
```

MVP 필수:

- `id`
- `user_id`
- `refresh_token_hash`
- `created_at`
- `last_used_at`
- `expires_at`
- `revoked_at`
- `device_label`
- `platform`
- `app_version`

### 5.6 desktop one-time code exchange

현재:

```text
clipper://auth/callback?token=<JWT>
```

문제:

- JWT 원문이 URL에 들어간다.
- URL은 브라우저 히스토리, OS protocol handler, process argv, 앱 로그, 크래시 리포트에 남을 수 있다.
- access token만 있을 때도 위험하고, refresh token을 도입하면 절대 URL에 실으면 안 된다.

목표:

```text
clipper://auth/callback?code=<one-time-code>
```

흐름:

```text
1. Electron이 system browser로 /auth/google?client=desktop 시작
2. web_api가 state에 client, nonce, login_request_id를 넣고 Google OAuth 시작
3. Google callback 성공
4. web_api가 user를 확인하거나 생성
5. web_api가 desktop_auth_codes row 생성
6. browser가 clipper://auth/callback?code=<one-time-code> 실행
7. Electron이 code를 받음
8. Electron이 POST /auth/desktop/exchange 호출
9. web_api가 code를 검증하고 used_at 처리
10. web_api가 session/access/refresh token 발급
11. Electron이 token bundle을 safeStorage에 저장
12. Angular가 /me로 session 확인 후 메인 화면 진입
```

권장 code 속성:

- 랜덤 opaque string
- 서버 DB에는 hash 저장
- TTL: 60초
- 1회 사용
- 사용 시 `used_at` 기록
- 같은 code 재사용 시 실패

### 5.7 token 저장

Electron packaged/devapp:

- `safeStorage`로 token bundle 저장
- 저장 파일은 기존 `auth.bin` 유지 가능
- 내용은 문자열 JWT 하나가 아니라 JSON token bundle을 암호화한 값으로 변경

예시 구조:

```json
{
  "accessToken": "...",
  "accessTokenExpiresAt": "...",
  "refreshToken": "...",
  "refreshTokenExpiresAt": "...",
  "sessionId": "...",
  "user": {
    "id": "...",
    "email": "...",
    "name": "..."
  }
}
```

보안 정책:

- packaged production에서 `safeStorage.isEncryptionAvailable()`가 false면 평문 저장하지 않는다.
- dev/CI에서만 평문 fallback을 허용할 수 있다.
- 로그에는 token 원문, refresh token 원문, one-time code 원문을 출력하지 않는다.

Browser-only Angular local dev:

- Electron 없이 `ng serve`를 쓰는 경우만 localStorage를 사용한다.
- local dev token은 production 구조와 섞지 않는다.
- `/auth/dev-login`은 `DEV_LOGIN_ENABLED=true`이고 production이 아닐 때만 허용한다.

### 5.8 login 시뮬레이션

첫 로그인:

```text
앱 실행
  -> 저장된 token bundle 없음
  -> 로그인 화면 표시

사용자가 Google 로그인 클릭
  -> Electron startLogin
  -> system browser 열림
  -> Google OAuth 완료
  -> web_api callback
  -> clipper://auth/callback?code=C1

Electron
  -> C1 수신
  -> POST /auth/desktop/exchange { code: C1 }

web_api
  -> C1 hash 조회
  -> 만료/사용 여부 확인
  -> user session S1 생성
  -> access token A1 발급
  -> refresh token R1 발급
  -> R1 hash 저장

Electron
  -> A1/R1/session metadata safeStorage 저장

Angular
  -> /me with A1
  -> 성공 시 /store 또는 메인 화면 진입
```

일반 API 호출:

```text
Angular/local NestJS
  -> Authorization: Bearer A1
web_api
  -> access token 검증
  -> user 확인
  -> 필요한 경우 session/license/operation policy 확인
  -> 응답
```

access token 만료 전 proactive refresh:

```text
앱이 A1 만료가 가까운 것을 확인
  -> POST /auth/refresh { refreshToken: R1 }
web_api
  -> R1 hash 조회
  -> session S1 유효성 확인
  -> R1 폐기, R2 hash 저장
  -> access token A2 발급
  -> refresh token R2 반환
Electron
  -> A1/R1 버림
  -> A2/R2 저장
```

API 호출 후 reactive refresh:

```text
앱이 A1이 유효하다고 생각하고 API 호출
web_api가 401 token_expired 반환
앱이 /auth/refresh with R1 호출
성공하면 A2/R2 저장
원래 요청을 A2로 한 번만 재시도
```

동시 refresh 방지:

- 여러 요청이 동시에 401을 받아도 refresh 요청은 하나만 보내야 한다.
- Angular/Electron auth layer에 single-flight refresh 처리를 둔다.
- 다른 요청은 진행 중인 refresh Promise를 기다린다.

앱 재실행:

```text
앱 실행
  -> safeStorage에서 token bundle 읽음

A1이 아직 유효:
  -> /me 성공
  -> 메인 화면

A1 만료, R1 유효:
  -> /auth/refresh 성공
  -> A2/R2 저장
  -> /me 성공
  -> 메인 화면

R1 만료 또는 session revoked:
  -> token bundle 삭제
  -> 로그인 화면
```

로그아웃:

```text
사용자 로그아웃 클릭
  -> POST /auth/logout with A1 또는 R1/sessionId
web_api
  -> session S1 revoked_at 기록
Electron
  -> safeStorage token bundle 삭제
Angular
  -> user null
  -> 로그인 화면
```

로그아웃 API가 네트워크 문제로 실패:

```text
클라이언트는 로컬 token bundle을 삭제
로그인 화면으로 이동
서버 revoke는 실패했을 수 있음
다음 네트워크 연결 시 재시도하거나
다음 로그인 시 같은 device session 정리 정책으로 보완
```

로그아웃 후 같은 Google 계정으로 재로그인:

```text
기존 user U1 재사용
기존 session S1은 revoked 상태 유지
새 session S2 생성
새 access token A2 발급
새 refresh token R2 발급
기존 이용권/보관함은 U1 기준으로 그대로 접근
```

로그아웃 후 다른 Google 계정으로 로그인:

```text
기존 session S1은 revoked
다른 user U2 확인 또는 생성
새 session S3 생성
앱 데이터는 U2 기준으로 동작
로컬 캐시는 userId 기준으로 분리하거나 logout 시 민감 캐시 삭제
```

refresh token 재사용 감지:

```text
정상 앱이 R1으로 refresh 성공
  -> 서버는 R1 폐기, R2 저장

나중에 R1이 다시 사용됨
  -> 이미 폐기된 token 재사용
  -> 탈취 가능성
  -> 해당 session 또는 token family revoke
  -> 클라이언트는 재로그인 필요
```

### 5.9 logout blocklist와 refresh token 비교

logout blocklist란:

```text
JWT에 jti를 넣고 긴 유효기간을 준다.
logout 시 해당 jti를 blocklist에 넣는다.
매 요청마다 JWT가 blocklist에 있는지 확인한다.
```

여기서 "긴 JWT"는 문자열 길이가 아니라 유효기간이 긴 JWT라는 뜻이다.

blocklist 장점:

- refresh token 없이도 이미 발급된 JWT를 강제로 거부할 수 있다.
- 단순한 web app에는 빠르게 붙일 수 있다.

blocklist 단점:

- access token 수명이 길면 탈취 시 위험하다.
- 매 요청마다 blocklist 조회가 필요하다.
- blocklist 저장소가 token 만료 시점까지 계속 필요하다.
- 기기별 세션 관리가 필요해지면 결국 session table이 필요하다.
- 로그인 유지 UX와 session revoke 정책이 refresh 방식보다 지저분해진다.

기기별 관리가 blocklist에서 애매한 이유:

```text
Mac 로그인 -> JWT A
Windows 로그인 -> JWT B

JWT만 검증하는 구조라면 서버는
"현재 어떤 기기들이 로그인 중인지",
"Mac만 로그아웃할지",
"Windows만 유지할지",
"마지막 사용 시각이 언제인지"
를 자연스럽게 관리하지 못한다.
```

물론 JWT에 `sid`를 넣고 DB에 발급 기록을 저장하면 가능하다. 그러나 그 순간 이미 session table을 만든 것이므로 refresh token 방식과 비슷해진다.

Clipper에 refresh token 방식이 더 적합한 이유:

- 설치형 앱은 자동 로그인 유지가 중요하다.
- 기기별 session 관리가 필요할 가능성이 높다.
- 같은 Google 계정의 여러 PC 로그인을 파악해야 한다.
- 비용이 걸리는 제품 operation은 이용권/크레딧이 연결되므로 session revoke가 중요하다.
- access token을 짧게 유지하고 refresh/session revoke로 위험을 줄일 수 있다.
- 나중에 동시 기기 수 제한, 전체 기기 로그아웃, 관리자 세션 차단으로 확장하기 쉽다.

MVP 정책:

- user access token 30분
- user refresh/session 30일
- logout은 session revoke + local storage delete
- user access token blocklist는 MVP에서 도입하지 않음
- 민감 provider/billing endpoint는 필요 시 `sid` session 유효성까지 확인
- operator는 더 짧은 access/refresh 정책 적용

## 6. 다중 기기 세션 정책

동일 Google 계정으로 여러 PC에서 로그인하면 같은 `user_id` 아래에 여러 session이 생긴다.

```text
user U1
  session S1: MacBook, active
  session S2: Windows PC, active
  session S3: Office PC, active
```

이 구조로 가능한 것:

- 현재 로그인된 기기 목록 조회
- 특정 기기만 로그아웃
- 모든 기기에서 로그아웃
- 마지막 사용 시각 표시
- 동시 활성 기기 수 제한
- 초과 로그인 시 거부 또는 오래된 세션 revoke

정책 선택지:

1. 무제한 허용

- 가장 단순하다.
- 같은 계정을 여러 사람이 공유해도 기술적으로 막지 않는다.
- 이용권 크레딧은 계정 단위로 함께 소모된다.

2. 계정당 활성 기기 수 제한

- 예: active session 2개까지 허용
- 초과 로그인 시 선택지:
  - 새 로그인 거부
  - 가장 오래된 session 자동 revoke
  - 사용자에게 기기 관리 화면 제공

3. 이용권 플랜별 기기 수 제한

- basic은 1대, pro는 2대처럼 구성 가능
- 구현 복잡도가 늘어난다.

MVP 권장:

```text
DB 구조는 기기별 active session을 지원한다.
초기에는 하드 제한을 걸지 않거나 설정값으로만 준비한다.
계정 공유/남용 이슈가 확인되면 active session limit을 켠다.
```

하드 제한을 켤 경우 기본값은 2대를 권장한다. 초과 시 자동으로 오래된 기기를 로그아웃시키기보다, "기기 관리 필요" 오류를 반환하는 쪽이 사용자에게 설명하기 쉽다. 관리자/고객 기기 관리 UI는 후순위로 둔다.

## 7. user JWT와 operator JWT

### 7.1 user JWT

대상:

- 설치형 앱 사용자
- 고객 웹 사용자
- 보호된 제품 operation 시작/provider 단계 호출
- 이용권 조회/구매 요청/크레딧 차감/환불

payload 권장:

```json
{
  "sub": "user-id",
  "typ": "user",
  "sid": "user-session-id",
  "aud": "clipper-user"
}
```

guard:

- `JwtAuthGuard` 또는 `UserJwtGuard`
- Bearer token 또는 customer web cookie 허용 여부는 endpoint별로 결정

### 7.2 operator JWT

대상:

- 관리자 페이지
- 이용권 승인/반려
- API key 관리
- release admin
- operator 관리

payload 권장:

```json
{
  "sub": "operator-id",
  "typ": "operator",
  "sid": "operator-session-id",
  "aud": "clipper-operator"
}
```

권장 개선:

- user token과 operator token의 `aud` 분리
- operator role/status를 DB에서 실제 조회
- payload role만 믿지 않고 DB 권한 확인
- 민감 admin endpoint는 permission guard 추가
- operator/admin token은 user JWT signing key와 분리된 전용 key/secret으로 서명한다.

### 7.3 service token

service token은 사람 사용자 기능에 쓰지 않는다.

### 7.4 JWT_SECRET sunset

`JWT_SECRET`은 기존 HS256 user token과 operator/admin JWT 흐름을 지탱하던 legacy bootstrap secret이다. desktop local NestJS가 user access token을 public key로 검증해야 하므로 user token의 목표 구조는 RS256 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY`이다.

최종 목표:

- user token은 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY`로만 서명/검증한다.
- operator/admin token은 user token과 다른 `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY` 또는 최소 별도 `OPERATOR_JWT_SECRET`으로 분리한다.
- `JWT_SECRET` 기반 user/operator fallback은 제거한다.
- dev-login/web-login/cookie `/me`/desktop exchange/refresh/admin login 테스트는 모두 분리된 key 구조를 기준으로 갱신한다.

제거 순서:

1. user JWT가 `USER_JWT_PRIVATE_KEY`를 module-level `JWT_SECRET`보다 우선하도록 고정한다.
2. operator/admin JWT signing/strategy를 user token과 별도 key/secret으로 분리한다.
3. `JwtModule` 기본 `JWT_SECRET` 의존을 제거하거나 operator-only legacy alias로 축소한다.
4. `JWT_SECRET` env fallback, 기본값, 테스트 의존을 삭제한다.
5. 운영/스테이징에서 user desktop login, web login, admin login, refresh/logout을 smoke한다.

허용 대상:

- release runner callback
- infra 내부 webhook
- 명확한 server-to-server actor

비허용 대상:

- 설치형 앱에서 사용자 제품 기능 권한을 대신하는 인증
- 사용자 이용권/크레딧 차감을 대신하는 인증

이유:

- 설치형 앱에 static token을 넣으면 추출 가능하다.
- user identity가 없어서 누가 썼는지 모른다.
- 이용권/크레딧 차감을 정확히 적용할 수 없다.
- 유출되면 모든 사용자의 권한처럼 동작할 수 있다.

### 7.4 guard 설계

하나의 거대한 `TokenGuard`로 모든 것을 처리하지 않는다. 토큰 추출/검증 helper는 공유하되, actor와 정책은 분리한다.

권장:

```text
UserJwtGuard
OperatorJwtGuard
ServiceTokenGuard
OperationPolicyGuard
PermissionGuard
```

이유:

- user, operator, service는 의미가 다르다.
- endpoint별 실패 코드와 감사 로그가 달라야 한다.
- user JWT가 필요한 곳에 실수로 service token을 허용하면 위험하다.
- operator JWT가 customer endpoint에 들어오는 것도 막아야 한다.

## 8. 설치형 앱 auth 전달 정책

### 8.1 메인 화면 gate

앱 메인 화면에 진입하려면 로그인 성공이 필요하다.

```text
앱 실행
  -> token bundle 복구 또는 refresh
  -> /me 성공
  -> 메인 화면

실패
  -> 로그인 화면
```

### 8.2 제품 기능 시작점과 내부 동작 구분

설치형 앱에서는 "제품 기능 시작점"과 "제품 내부 세부 동작"을 분리한다.

제품 기능 시작점:

- 템플릿 생성 시작
- TTS 프리셋 관리 시작
- 숏폼 생성 job 시작
- 대사 중심 하이라이트 추출 job 시작
- 안무영상 하이라이트 추출 job 시작
- 플러그인 카드에서 실제 제품 실행을 시작하는 시점

정책:

```text
제품 기능 시작점에서는 web_api가 user/session/license/operation policy를 확인할 수 있다.
```

제품 내부 세부 동작:

- 텍스트 입력
- 색상 변경
- 위치 이동
- 프리뷰 렌더
- 로컬 파일 저장
- 로컬 job queue 내부 단계 전환

정책:

```text
제품 시작 권한이 통과된 뒤의 내부 로컬 동작은 매번 web_api를 왕복하지 않는다.
```

즉 "로컬 실행 기능"도 시작점에서는 web_api 확인을 거칠 수 있다. 다만 기능 본체가 로컬에서 실행된다는 뜻이지, 권한 확인도 영원히 로컬만으로 끝낸다는 뜻은 아니다.

### 8.3 decorator/guard 설계

권한 관련 decorator는 크게 두 종류다.

local NestJS 제품 시작점:

```ts
@BillableOperation('dance_highlight.extract')
@Post('/dance-highlight/jobs')
startDanceHighlightJob() {}
```

역할:

```text
1. Angular가 보낸 user access token을 읽는다.
2. web_api /operations/start를 호출한다.
3. web_api가 operation policy와 license/credit을 확인한다.
4. 통과하면 operationRunId를 local job에 저장한다.
5. 실패하면 local job을 시작하지 않는다.
```

`@BillableOperation`이라는 이름은 "항상 유료"라는 뜻이 아니라, 제품 operation 정책을 적용한다는 뜻이다. `credit_cost=0`인 기능도 이 decorator를 쓸 수 있다.

local NestJS의 access JWT 검증:

```text
1. Authorization header가 없으면 401
2. JWT signature가 public key로 검증되지 않으면 401
3. exp가 만료되었으면 401
4. typ/aud/iss가 기대값과 다르면 403
5. 1차 검증 통과 후 web_api /operations/start 또는 provider endpoint로 relay
```

이 검증은 localhost 포트로 들어오는 이상 요청을 초기에 거르는 용도다. local NestJS는 사용자 PC 안에서 `127.0.0.1:<port>`로 떠 있으므로, 정상 Clipper Angular/Electron 외에도 브라우저, 확장 프로그램, 로컬 스크립트, 다른 프로세스가 같은 포트로 HTTP 요청을 시도할 수 있다. 같은 포트에 다른 서버가 뜨는 것이 아니라, 여러 클라이언트가 local NestJS 서버에 접속할 수 있다는 의미다.

JWT local 검증이 막을 수 있는 것:

```text
Authorization 없는 요청
위조된 JWT
만료된 JWT
operator token이 user route에 들어오는 실수
다른 audience/issuer의 token
```

JWT local 검증이 판단하지 않는 것:

```text
session이 방금 revoke되었는지
user가 정지되었는지
active license가 있는지
credit이 충분한지
operation policy상 해당 실행을 허용할 수 있는지
refund 가능한 실패인지
```

이 최종 판단은 web_api가 `sid`, user, license, operation policy, credit ledger를 조회해서 한다. 즉 local NestJS JWT 검증은 최종 권한 판단자가 아니라 1차 인증 필터다.

session-only opaque access token을 쓴다면 local NestJS는 token 문자열만으로 위조/만료/session 상태를 알 수 없다. 그 경우 보호된 local endpoint마다 web_api introspection 또는 `/operations/start` relay가 필요하다. 이 방식도 가능하지만, ClipperStudio는 local NestJS에 public key PEM을 포함해 JWT access token을 1차 검증하는 쪽을 target으로 둔다.

### 8.3.1 브라우저 media request 예외

desktop renderer의 `HttpClient` 요청은 bearer token을 붙일 수 있지만, `<audio>`/`new Audio()`/`<img>`/`<video>` 같은 브라우저 media 요청은 임의 Authorization header를 붙일 수 없다. `CLIPPER_AUTH_MODE=jwt`에서는 이 경로가 `Missing bearer token`으로 실패한다.

목표 구조:

- local NestJS가 user JWT를 받은 API 응답 안에 짧은 수명의 opaque media ticket URL을 발급한다.
- media ticket은 JWT/access token/provider key 원문을 포함하지 않는다.
- media ticket은 필요한 최소 식별자와 만료 시각만 local NestJS process memory에 보관한다.
  - shortform TTS: `(ownerSubjectId, projectId, artifactId, expiresAt)`
  - project artifact file: `(ownerSubjectId, projectId, filePath, expiresAt)`
- bearer가 붙은 요청은 기존 user auth resolver를 사용하고, bearer를 붙일 수 없는 media 요청만 ticket resolver를 사용한다.
- 저장소에는 ticket URL을 영구 저장하지 않고 응답 직전에 transient URL로만 붙인다.

현재 적용 대상:

- shortform TTS wav file playback
- project artifact thumbnail/video playback: `/projects/:projectId/file?path=...`

web_api 서버 endpoint:

```ts
@RequireOperationRunProviderScope(ProviderScope.NaverImage)
@Post('/media/search')
searchMedia() {}
```

역할:

```text
1. user JWT/session을 확인한다.
2. operationRunId가 같은 user의 실행인지 확인한다.
3. operation_policies와 provider scope enum을 확인한다.
4. provider 호출이 필요한 경우 web_api가 provider credential을 선택한다.
5. 제품 operation의 billing strategy에 맞게 ledger를 처리한다.
```

다만 provider 호출이 어떤 제품 operation 내부 단계라면, provider endpoint는 별도 과금 operation으로 보지 않고 기존 `operationRunId`에 provider usage/audit만 묶는다.

### 8.4 기능별 flow 분류

local execution:

```text
Angular -> local NestJS @BillableOperation(operationKey)
local NestJS -> web_api /operations/start
web_api -> user/session/license/credit 확인 + 필요 시 charge
local NestJS -> 로컬 job/파일/렌더 실행
local NestJS -> web_api /operations/{runId}/succeed 또는 /fail
```

server/provider execution:

```text
독립 서버형 제품:
  Angular -> local NestJS @BillableOperation(operationKey)
  local NestJS -> web_api /operations/start
  web_api -> 필요 시 charge 후 operationRunId 반환
  local NestJS -> web_api provider/product endpoint with operationRunId
  web_api -> provider credential 선택
  web_api -> provider 호출
  web_api -> provider usage/audit 기록
  web_api -> response
```

mixed execution:

```text
local NestJS -> 제품 시작점에서 /operations/start
local NestJS -> 로컬 전처리/분석
local NestJS -> 필요한 단계에서 web_api provider endpoint 호출
local NestJS -> 로컬 후처리/결과 저장
local NestJS -> /operations/{runId}/succeed 또는 /fail
```

### 8.5 local NestJS의 역할

local NestJS는 다음을 한다.

- 로컬 workflow orchestration
- 파일/프로젝트/잡 관리
- Python plugin 실행
- web_api provider proxy 호출
- user access token relay
- 제품 operation start/succeed/fail 보고
- web_api 보고 실패 시 local DB에 pending report를 남기고 재시도

local NestJS는 다음을 하지 않는다.

- provider key 보관
- refresh token 보관
- 최종 이용권 판단
- 최종 credit cost 판단
- 최종 refund 여부 판단
- provider operation의 user entitlement 최종 결정

### 8.6 Authorization relay

권장 기본 흐름:

```text
Angular HTTP request to local NestJS:
  Authorization: Bearer <user access token>

local NestJS WebApiClient request to web_api:
  Authorization: Bearer <same user access token>
```

주의:

- local NestJS logs에 Authorization header를 출력하지 않는다.
- Python process env/stdin/stdout에 token을 넘기지 않는다.
- 제품 기능 시작점과 provider/web_api 호출 route에만 token을 요구한다.
- 제품 내부의 세부 로컬 동작 전체에 불필요하게 web_api 의존성을 만들지 않는다.

### 8.7 offline/web_api 장애 정책

앱이 이미 로그인되어 있고 token이 아직 유효하거나 refresh 가능했던 상태:

- 이미 시작되어 권한 확인을 통과한 local job은 가능한 범위에서 계속 실행 가능
- 새 제품 operation start는 web_api가 필요하면 실패
- provider-backed 단계는 web_api가 필요하므로 실패 또는 retry
- 실패 코드는 `web_api_unreachable`, `web_api_timeout`, `auth_refresh_failed` 등으로 구분

앱 첫 실행에서 web_api가 완전히 불가:

- 저장된 access token이 유효하면 제한적 진입을 허용할지 별도 결정
- refresh가 필요하면 로그인 복구 불가
- 로그인 화면 또는 "서버 연결 필요" 상태 표시

MVP 권장:

```text
첫 실행에서 /me 또는 refresh 실패 시 로그인 화면/서버 연결 오류
앱 진입 후 web_api 장애는 새 operation start와 provider-backed 단계만 실패
이미 local DB에 남아 있는 pending success/failure billing report는 web_api 복구 후 재시도
```

## 9. 이용권 정책

### 9.1 기본 사업 흐름

현재 결제 모듈이 없으므로 1차는 수동 입금/운영자 승인 흐름이다.

```text
사용자
  -> 플랜 선택
  -> 구매 요청 생성
  -> 입금

운영자
  -> 관리자 페이지에서 구매 요청 확인
  -> 입금 여부 확인
  -> 승인 또는 반려

web_api
  -> 승인 시 license 생성 또는 queue
```

### 9.2 플랜

플랜은 다음 속성을 가진다.

```text
id
name
duration_days
included_credits
price
active
display_order
```

예:

```text
1개월 / N credit
3개월 / N credit
6개월 / N credit
12개월 / N credit
```

### 9.3 license 상태

권장 상태:

```text
queued
active
active_depleted
expired
depleted
cancelled
```

MVP 최소:

```text
queued
active
active_depleted
expired
depleted
cancelled
```

상태 의미:

```text
queued
  운영자가 승인했지만 아직 시작되지 않은 이용권

active
  현재 기간이 진행 중이고 credit-required operation을 사용할 수 있는 이용권

active_depleted
  기간은 남았지만 크레딧을 모두 써서 credit-required operation을 사용할 수 없는 이용권

expired
  기간이 끝난 이용권

depleted
  크레딧 소진 후 사용자가 다음 queued license를 시작하면서 종료 확정된 이용권
```

### 9.4 one active license 정책

한 user는 동시에 active license를 최대 1개만 가진다.

기존 이용권이 active이고 크레딧이 남아 있는 상태에서 새 이용권이 승인되면:

```text
새 license는 queued 상태로 생성
기존 active license가 만료되어도 queued license는 자동 active로 전환하지 않음
사용자가 다음 이용권 시작을 명시적으로 눌러야 active로 전환
```

기존 이용권이 active이지만 credit이 0인 상태에서 새 이용권이 승인되면:

```text
새 license는 queued 상태로 생성
기존 active license는 active_depleted 상태로 남음
사용자가 다음 이용권 시작을 명시적으로 눌러야 새 license를 active로 시작
```

기존 active license가 없으면:

```text
승인 즉시 active 시작
```

하지 않을 것:

- 기존 3개월 이용권을 새 6개월 이용권에 흡수
- 남은 기간/크레딧을 임의 병합
- 여러 active license credit bucket을 동시에 소모

이유:

- 병합 정책은 설명하기 어렵고 구현이 복잡하다.
- 만료/환불/크레딧 소진/추가 구매 edge case가 크게 늘어난다.
- 고객과 운영자가 같은 상태를 이해하기 어렵다.

### 9.5 license 시작 시점

MVP 권장:

```text
운영자가 승인했을 때 active license가 없으면 즉시 active 시작
운영자가 승인했을 때 active license가 있으면 queued
queued license는 자동 시작하지 않음
queued license는 사용자가 "다음 이용권 시작"을 눌렀을 때만 active 시작
```

비권장 MVP:

- 사용자가 직접 시작일 선택
- 승인 후 며칠 내 개시하지 않으면 자동 시작
- 예약 시작일 관리
- 만료/크레딧 소진 시 queued license 자동 시작

이유:

- 제품 정책과 UX가 복잡해진다.
- 수동 입금 1차 출시에 필요한 핵심이 아니다.
- `charge_then_refund`에서 실패 환불이 발생하면 자동 시작 정책과 충돌할 수 있다.

### 9.6 크레딧 소진 정책

license 기간이 남았지만 크레딧을 먼저 다 쓴 경우:

```text
license 상태 = active_depleted
credit-required operation 사용 불가
queued license가 있어도 자동 active 처리하지 않음
```

사용자가 새 이용권을 구매하고 운영자가 승인하면:

```text
새 license는 queued
사용자가 "다음 이용권 시작"을 누르면 기존 active_depleted license를 depleted로 확정하고 새 license active
```

크레딧 추가 구매:

- MVP에서는 별도 credit top-up을 만들지 않는다.
- 나중에 필요하면 `credit_pack` 상품으로 분리한다.
- license 크레딧과 top-up 크레딧을 섞을 경우 ledger 정책이 복잡해지므로 별도 설계가 필요하다.

### 9.7 queued license 시작

queued license는 스케줄러나 조회 시점 lazy activation으로 자동 시작하지 않는다.

권장:

```text
1. active license가 expired 또는 active_depleted 상태가 됨
2. web/app이 "다음 이용권 시작" 버튼을 표시
3. 사용자가 시작을 명시적으로 요청
4. web_api가 active license가 없거나 종료 가능한 상태인지 확인
5. 기존 expired/active_depleted license를 종료 상태로 확정
6. 선택한 queued license에 starts_at/expires_at을 설정하고 active로 전환
```

시작 가능 조건:

```text
허용:
  active license가 없음
  active license가 expired
  active license가 active_depleted

불허:
  active license가 있고 remaining_credits > 0
  active license에서 아직 완료되지 않은 refundable operation이 있음
```

이 정책은 자동 전환을 없애서 `charge_then_refund`와의 충돌을 줄인다. 작업 실패로 refund가 발생해도, queued license가 이미 자동 시작되어 버리는 상황을 만들지 않는다.

## 10. 제품 operation과 크레딧 차감

### 10.1 operation policy

크레딧 차감은 provider API 호출 단위가 아니라 사용자-facing 제품 실행 단위로 한다.

예를 들어 Dance Highlight 내부에서 Naver 이미지 검색을 몇 번 쓰더라도, 유저에게 과금되는 단위는 `dance_highlight.extract` 하나다. Naver 이미지 검색은 provider usage/audit에는 남길 수 있지만 별도 유저 과금 operation으로 쪼개지 않는다.

이번 MVP에서 플러그인 스토어 노출 정책은 operation policy에 넣지 않는다.

```text
플러그인 스토어에 무엇을 보여줄지
  -> 로컬 앱 manifest/catalog/Angular visible list 기준

실제 제품 실행을 허용할지
  -> web_api operation policy + license/credit 기준
```

즉 플러그인 카드는 로컬에서 보일 수 있다. 하지만 사용자가 실제 실행을 시작하면 web_api가 `operation_key` 기준으로 이용권과 크레딧을 최종 확인한다.

권장 모델:

```text
OperationPolicy
  id
  operation_key
  display_name_ko
  requires_license
  credit_cost
  billing_strategy
  provider_scopes
  created_at
  updated_at
```

예:

```text
dance_highlight.extract
  requires_license = true
  credit_cost = 80
  billing_strategy = charge_then_refund

dialog_highlight.extract
  requires_license = true
  credit_cost = 70
  billing_strategy = charge_then_refund

shortform.create
  requires_license = true
  credit_cost = 50
  billing_strategy = charge_then_refund

template.create
  requires_license = true
  credit_cost = 0
  billing_strategy = none
```

실제 credit cost는 임시값으로 시작해도 된다. 중요한 것은 cost를 client/local NestJS가 보내지 않고 서버 정책으로 결정한다는 점이다.

필드별 의미:

| 필드 | 한국어 설명 | 예시 값 | 비고 |
|---|---|---|---|
| `id` | DB 내부 식별자 | `uuid` | web_api 기존 패턴에 맞춰 uuid surrogate key를 쓴다. 코드에서 직접 참조하지 않는다 |
| `operation_key` | 코드/API/log/ledger에서 쓰는 안정적인 제품 실행 키 | `dialog_highlight.extract` | 환경마다 달라질 수 있는 DB id 대신 이 값을 decorator와 API에서 쓴다 |
| `display_name_ko` | 운영자/로그/관리 화면에서 볼 한국어 기능 이름 | `대사 중심 하이라이트 추출` | 사용자에게 그대로 노출할지는 별도 UI 결정 |
| `requires_license` | 이 기능을 쓰려면 active license가 필요한지 | `true` | `false`면 이용권 없이도 허용되는 기능 |
| `credit_cost` | 제품 operation 시작 시 차감할 크레딧 수 | `70` | client가 보내지 않고 서버가 결정한다 |
| `billing_strategy` | 차감/환불 방식 enum | `charge_then_refund` | 문자열 직접 사용 금지. 코드/DB/DTO enum으로 관리한다 |
| `provider_scopes` | 제품 execution 중 허용되는 외부 provider scope enum 배열 | `["openai"]` | provider 사용 추적/credential 선택에 쓰지만, provider 호출 단위 과금은 하지 않는다 |

중요한 점:

```text
requires_license=true/false는
"이 함수가 web_api를 호출해야 하는가"를 정하는 값이 아니다.

이 값은 web_api가 operation start를 처리할 때
"이 기능이 이용권 검사를 받아야 하는가"를 정하는 제품 정책이다.
```

제품 기능 시작점은 decorator가 표시한다.

```text
local NestJS:
  @BillableOperation('template.create')
  @BillableOperation('dance_highlight.extract')

web_api:
  /operations/start
  operation_policies를 보고 권한/이용권/크레딧 차감 판단
```

제품 내부의 세부 로컬 동작은 매번 web_api를 호출하지 않는다.

```text
템플릿 생성 시작:
  @BillableOperation('template.create')로 web_api /operations/start 호출

템플릿 내부 편집:
  텍스트 입력, 색상 변경, 위치 이동, 프리뷰 렌더는 web_api 호출 없음
```

DB 테이블 예시:

```text
operation_policies
  id                   DB 내부 식별자. uuid primary key
  operation_key        코드/API/log/ledger에서 쓰는 안정 키. 예: dialog_highlight.extract
  display_name_ko       한국어 기능명. 예: 대사 중심 하이라이트 추출
  requires_license      이용권 필요 여부
  credit_cost           제품 operation 시작 시 차감할 크레딧 수
  billing_strategy      차감/환불 전략 enum. MVP 기본값은 charge_then_refund
  provider_scopes       제품 execution 중 허용되는 provider scope enum 배열
  created_at
  updated_at
```

샘플 데이터:

| `operation_key` | `display_name_ko` | `requires_license` | `credit_cost` | `billing_strategy` | `provider_scopes` | 한국어 설명 |
|---|---|---:|---:|---|---|---|
| `template.create` | 템플릿 생성 | true | 0 | `none` | `[]` | 시작 권한은 확인하지만 차감은 없다. 내부 편집 동작은 web_api를 거치지 않는다 |
| `tts_preset.manage` | TTS 프리셋 관리 | true | 0 | `none` | `[]` | 프리셋 관리 기능 시작 권한만 확인한다 |
| `shortform.create` | 숏폼 생성 | true | 50 | `charge_then_refund` | `["openai"]` | 숏폼 제품 실행 단위. 내부 OpenAI 단계는 이 run에 묶어 audit한다 |
| `dialog_highlight.extract` | 대사 중심 하이라이트 추출 | true | 70 | `charge_then_refund` | `["openai"]` | local 전처리와 web_api LLM 단계가 섞인다. 과금 단위는 제품 실행 1회다 |
| `dance_highlight.extract` | 안무영상 하이라이트 추출 | true | 80 | `charge_then_refund` | `["naver_image"]` | 내부에서 Naver 이미지 검색을 써도 별도 과금하지 않고 이 제품 실행에 묶는다 |

`execution_mode`는 MVP operation policy에서 제거한다. `local/server/mixed`는 구현 설명에는 도움이 되지만 권한/과금 판단 값으로 쓰기에는 애매하고, 플러그인 스토어 정책과도 쉽게 섞인다. 실행 위치는 코드 구조와 각 product service가 알면 된다.

`enabled`도 MVP operation policy에서 제거한다. 현재는 플러그인 카드와 제품 operation이 대부분 1:1에 가깝고, 기능 중단 정책을 별도 DB flag로 넣으면 플러그인 표시 정책과 섞일 수 있다. 운영 중 긴급 차단이 필요해지면 후속으로 `operation_availability` 또는 `plugins.enabled` 같은 별도 설계를 추가한다.

`billing_strategy` 값 의미:

```text
none
  credit_cost가 0인 기능. 권한 확인만 하고 차감/환불 ledger는 만들지 않는다.

charge_then_refund
  시작 시 크레딧을 즉시 차감한다.
  local job이 성공하면 그대로 확정된다.
  local job이 실패하면 실패 보고를 받아 refund ledger를 만든다.
```

MVP 기본 전략은 `charge_then_refund`다. `upfront_hold`는 reserve/release/heartbeat/stale reservation 처리가 필요해 더 복잡하므로 MVP 기본값으로 두지 않는다.

enum 관리:

```ts
export enum OperationBillingStrategy {
  None = 'none',
  ChargeThenRefund = 'charge_then_refund',
}

export enum OperationRunStatus {
  Running = 'running',
  Succeeded = 'succeeded',
  Failed = 'failed',
  Refunded = 'refunded',
  NeedsReview = 'needs_review',
}

export enum CreditLedgerType {
  Debit = 'debit',
  Refund = 'refund',
}

export enum CreditLedgerReason {
  OperationStarted = 'operation_started',
  SystemFailure = 'system_failure',
  ProviderFailure = 'provider_failure',
  UserCancelled = 'user_cancelled',
}

export enum ProviderScope {
  OpenAi = 'openai',
  NaverImage = 'naver_image',
}
```

DB도 가능한 범위에서 enum/check constraint로 잠근다.

```sql
CREATE TYPE operation_billing_strategy AS ENUM (
  'none',
  'charge_then_refund'
);

CREATE TYPE operation_run_status AS ENUM (
  'running',
  'succeeded',
  'failed',
  'refunded',
  'needs_review'
);

CREATE TYPE credit_ledger_type AS ENUM (
  'debit',
  'refund'
);
```

`provider_scopes`는 PostgreSQL enum array나 JSONB + application enum validation 둘 중 하나로 구현한다. MVP에서는 TypeORM migration 난이도를 낮추기 위해 JSONB 배열 + DTO/service enum validation으로 시작해도 된다. 중요한 것은 코드에서 `'naver-image'`, `'naver_image'` 같은 문자열을 직접 흩뿌리지 않는 것이다.

operation policy 생성/수정 정책:

```text
Create
  개발자가 코드에 operation을 추가한다.
  web_api의 canonical registry에 기본 정책을 추가한다.
  seed/upsert가 DB에 없는 operation_key만 insert한다.

Read
  관리자 페이지에서 조회 가능하다.

Update
  관리자 페이지에서 제한된 정책값만 수정 가능하다.

Delete
  하지 않는다.
```

canonical registry 예:

```ts
export const OPERATION_DEFINITIONS = [
  {
    operationKey: 'dance_highlight.extract',
    displayNameKo: '안무영상 하이라이트 추출',
    requiresLicense: true,
    creditCost: 80,
    billingStrategy: OperationBillingStrategy.ChargeThenRefund,
    providerScopes: [ProviderScope.NaverImage],
  },
  {
    operationKey: 'dialog_highlight.extract',
    displayNameKo: '대사 중심 하이라이트 추출',
    requiresLicense: true,
    creditCost: 70,
    billingStrategy: OperationBillingStrategy.ChargeThenRefund,
    providerScopes: [ProviderScope.OpenAi],
  },
] as const;
```

seed/upsert 원칙:

```sql
INSERT INTO operation_policies (
  operation_key,
  display_name_ko,
  requires_license,
  credit_cost,
  billing_strategy,
  provider_scopes
)
VALUES (...)
ON CONFLICT (operation_key) DO NOTHING;
```

`DO NOTHING`이 핵심이다. 이미 존재하는 row를 배포 때 덮어쓰면 운영자가 관리자 페이지에서 바꾼 `credit_cost` 같은 정책값이 사라진다.

소유권:

| 값 | 소유자 | 설명 |
|---|---|---|
| `operation_key` | 개발 코드 | decorator/API/log/ledger가 참조하는 안정 키. 변경 금지에 가깝다 |
| 최초 기본값 | code registry | 새 operation 생성 시 기본 정책을 제공한다 |
| 생성 후 정책값 | DB/admin | 운영자가 `credit_cost`, `requires_license`, `billing_strategy`를 조정할 수 있다 |
| `provider_scopes` | 개발 코드 우선 | 실제 provider 호출 코드와 맞아야 하므로 MVP에서는 관리자 임의 수정 대상에서 제외한다 |

관리자 수정 허용값:

```text
display_name_ko
requires_license
credit_cost
billing_strategy
```

관리자 수정 비허용값:

```text
operation_key
provider_scopes
id
```

새 operation 추가 흐름:

```text
1. local NestJS 제품 시작점에 @BillableOperation('variation.generate') 추가
2. web_api OPERATION_DEFINITIONS에 operationKey='variation.generate' 기본 정책 추가
3. admin DB migration으로 operation_policies 테이블이 없으면 생성
4. npm run db:seed:operations 같은 명시적 seed 실행
5. DB에 없으면 insert, 있으면 그대로 둠
6. 관리자 페이지에서 필요하면 credit_cost 등 제한된 정책값 수정
```

앱 부팅 시 자동 sync는 MVP에서 하지 않는다. 운영 DB 정책을 서버 부팅 때 자동으로 바꾸면 예측하기 어렵다. 명시적 seed 명령이 더 안전하다.

관련 실행/ledger 테이블 예시:

```text
operation_runs
  id                         제품 실행 ID
  user_id                    사용자 ID
  session_id                 실행을 시작한 로그인 세션 ID
  device_id                  실행 기기 ID
  license_id                 차감 대상 이용권 ID
  operation_key              어떤 제품 operation인지
  local_job_id               local NestJS job ID
  status                     running/succeeded/failed/refunded/needs_review
  credit_cost                시작 시 차감한 크레딧 수
  billing_strategy           적용된 차감 전략
  idempotency_key            중복 start 방지 키
  started_at
  finished_at

credit_ledger
  id                         ledger ID
  operation_run_id           operation_runs.id
  user_id
  license_id
  type                       debit/refund
  credits                    크레딧 수
  reason_code                operation_started/system_failure/provider_failure 등
  created_at
```

`operation_runs` 샘플 데이터:

| `id` | `user_id` | `session_id` | `operation_key` | `status` | `credit_cost` | 한국어 설명 |
|---|---|---|---|---|---:|---|
| `run_001` | `usr_123` | `sess_mac` | `dance_highlight.extract` | `running` | 80 | Mac에서 안무 하이라이트 시작, 80크레딧 차감 후 실행 중 |
| `run_002` | `usr_123` | `sess_mac` | `dialog_highlight.extract` | `succeeded` | 70 | 대사 하이라이트 성공, 시작 시 차감된 70크레딧 유지 |
| `run_003` | `usr_456` | `sess_win` | `shortform.create` | `refunded` | 50 | 숏폼 생성 실패 후 50크레딧 환불 |

`credit_ledger` 샘플 데이터:

| `id` | `operation_run_id` | `type` | `credits` | `reason_code` | 한국어 설명 |
|---|---|---|---:|---|---|
| `cl_001` | `run_001` | `debit` | 80 | `operation_started` | 안무 하이라이트 시작 시 80크레딧 차감 |
| `cl_002` | `run_003` | `debit` | 50 | `operation_started` | 숏폼 생성 시작 시 50크레딧 차감 |
| `cl_003` | `run_003` | `refund` | 50 | `system_failure` | local job 실패 보고를 받아 50크레딧 환불 |

provider credential 테이블 예시:

```text
provider_credentials
  id                  provider credential ID
  provider            provider 종류. 예: openai, naver
  label               운영자가 구분하는 이름
  credential_type     key 종류. 예: api_key, naver_search
  public_id           노출 가능한 식별자. 예: Naver client id 또는 masked key
  secret_enc          암호화된 secret. 원문 저장/노출 금지
  status              active/standby/exhausted/disabled
  daily_used          일일 사용량
  daily_limit         일일 제한량
  usage_date          사용량 집계 날짜
  priority            rotation 우선순위
  deleted_at          soft delete 시각. null이면 운영 목록/rotation 후보
  last_tested_at
  last_error_code
```

`provider_credentials` 샘플 데이터:

| `id` | `provider` | `label` | `credential_type` | `public_id` | `secret_enc` | `status` | `daily_used` | `daily_limit` | 한국어 설명 |
|---|---|---|---|---|---|---|---:|---:|---|
| `pc_001` | `naver` | `naver-main-1` | `naver_search` | `naver-client-main` | `<encrypted>` | `active` | 120 | 25000 | 네이버 이미지 검색에 우선 사용하는 key |
| `pc_002` | `naver` | `naver-standby-1` | `naver_search` | `naver-client-standby` | `<encrypted>` | `standby` | 0 | 25000 | main key 한도 소진 시 대기 key |
| `pc_003` | `openai` | `openai-prod-main` | `api_key` | `masked-openai-key` | `<encrypted>` | `active` | 0 | 0 | OpenAI 호출용 key. 사용량 제한 방식은 provider strategy가 판단 |

provider 사용 audit 테이블 예시:

```text
  provider_usage
  id                         provider usage ID
  operation_run_id           어떤 제품 실행 내부에서 발생한 provider 호출인지. setup/manual 호출은 null 가능
  user_id
  session_id                 가능하면 호출한 session
  usage_context              operation_run_id가 없을 때의 audit context
  provider_scope             naver_image/openai 등 provider scope
  provider_name              실제 호출 provider name
  provider_credential_id     사용한 provider_credentials.id. admin UI/API에는 raw UUID를 표시하지 않음
  unit_count                 provider 호출 단위 수
  metadata                   endpoint 등 non-secret context
  created_at
```

`provider_usage`는 비용/audit/rotation 분석용이다. 사용자 크레딧 차감의 원장은 `credit_ledger`이고, provider 호출 횟수 자체가 별도 사용자 과금 단위가 되지는 않는다.

### 10.2 operation quote와 사용자 확인 모달

크레딧이 차감되는 제품은 사용자가 실행 전에 비용을 알아야 한다.

권장 흐름:

```text
Angular
  -> local NestJS GET /operations/dance_highlight.extract/quote

local NestJS
  -> web_api GET /operations/dance_highlight.extract/quote
     Authorization: Bearer <user access token>

web_api
  -> user/session 확인
  -> operation_policies 조회
  -> active license와 remaining credit 확인
  -> credit_cost, can_start, insufficient reason 반환

Angular
  -> "안무영상 하이라이트 추출은 80크레딧이 차감됩니다. 진행할까요?" 모달 표시
```

quote는 안내용이다. 실제 차감 판단은 반드시 `/operations/start`에서 다시 한다. quote 후 다른 기기에서 크레딧을 먼저 써버릴 수 있기 때문이다.

### 10.3 사용 예시 1: 템플릿 생성

템플릿 생성은 로컬 실행 기능이고 `credit_cost=0`이다. 그래도 제품 정책상 "로그인한 활성 이용권 사용자만 템플릿 기능을 쓸 수 있다"면 제품 시작점에서 operation policy를 확인할 수 있다.

```text
사용자 클릭: 템플릿 생성
Angular -> local NestJS @BillableOperation('template.create')
local NestJS -> web_api /operations/start
  operation_key = template.create
  Authorization = user access token

web_api
  -> user/session 확인
  -> operation_policies에서 template.create 조회
  -> requires_license=true이면 active license 확인
  -> credit_cost=0, billing_strategy=none 확인
  -> debit/refund ledger 없음
  -> allowed 반환

local NestJS
  -> 템플릿 파일/프로젝트 데이터 처리

제품 내부 편집:
  텍스트 입력, 색상 변경, 위치 이동, 프리뷰 렌더, 로컬 저장은 web_api 호출 없음
```

만약 나중에 템플릿 생성은 로그인만 필요하고 이용권은 필요 없다고 결정되면 `requires_license=false`, `credit_cost=0`으로 정책 row만 바꾸면 된다.

### 10.4 사용 예시 2: Dance Highlight 제품 실행

Dance Highlight는 제품 실행 1회가 과금 단위다. 내부에서 Naver 이미지 검색을 쓰더라도 Naver 검색 1회마다 사용자 크레딧을 따로 차감하지 않는다.

```text
사용자 클릭: 안무영상 하이라이트 추출 시작
Angular -> quote 요청
web_api -> credit_cost=80, remaining_credit=100, can_start=true 반환
Angular -> "80크레딧 차감" 확인 모달
사용자 -> 확인

Angular -> local NestJS POST /dance-highlight/jobs
local NestJS @BillableOperation('dance_highlight.extract')
  -> web_api POST /operations/start
     operation_key = dance_highlight.extract
     Idempotency-Key = local_job_id 기반 key

web_api /operations/start
  -> user/session 확인
  -> operation_policies 조회
  -> active license 확인
  -> DB transaction에서 license row 또는 credit bucket row lock
  -> remaining_credit >= 80 확인
  -> credit_ledger debit 80 생성
  -> operation_runs status=running 생성
  -> operationRunId 반환

local NestJS
  -> operationRunId를 local job에 저장
  -> 로컬 queue에 job enqueue
  -> 로컬 전처리/분석 시작
```

내부 Naver 이미지 검색 단계:

```text
local NestJS -> web_api POST /media/search
  Authorization = user access token
  operationRunId = run_001
  purpose = dance_highlight_reference_search

web_api
  -> user/session 확인
  -> operationRunId가 같은 user의 실행인지 확인
  -> operation_key=dance_highlight.extract 정책에서 ProviderScope.NaverImage 허용 확인
  -> provider_credentials에서 active Naver credential 선택
  -> Naver API 호출
  -> provider_usage 기록
  -> credit_ledger 추가 차감 없음
  -> 검색 결과 반환
```

성공:

```text
local NestJS
  -> 결과 파일 저장 성공
  -> web_api POST /operations/run_001/succeed

web_api
  -> operation_runs status=succeeded
  -> 추가 차감 없음
```

실패:

```text
local NestJS
  -> job 실패 인식
  -> web_api POST /operations/run_001/fail
     failure_reason = system_failure/provider_failure/invalid_input 등

web_api
  -> refund 가능한 실패인지 정책 확인
  -> credit_ledger refund 80 생성
  -> operation_runs status=refunded 또는 failed
```

### 10.5 멀티 디바이스 동시 실행

한 계정의 여러 session은 같은 active license credit bucket을 공유한다. 한 기기 안의 local queue만으로는 다른 PC에서 동시에 시작하는 요청을 막을 수 없다. 따라서 최종 방어는 web_api의 `/operations/start` DB transaction에서 한다.

예:

```text
초기 remaining_credit = 100

Mac session A:
  dance_highlight.extract 시작 요청
  credit_cost = 70
  DB lock 안에서 remaining 100 확인
  debit 70
  remaining_credit = 30

Windows session B:
  shortform.create 시작 요청
  credit_cost = 50
  DB lock 안에서 remaining 30 확인
  insufficient_credits 반환
  local job 시작 안 함
```

이 lock/transaction이 없으면 A와 B가 동시에 100을 보고 각각 시작해서 크레딧이 음수가 되는 문제가 생길 수 있다.

### 10.6 실패, 앱 종료, 보고 재시도

`charge_then_refund`는 "시작 시 차감, 실패 시 환불"이다. 이 전략에서 중요한 것은 local job 결과와 web_api credit ledger를 `operationRunId`로 연결하는 것이다.

정상 실패:

```text
local job 실행 중 오류 발생
local NestJS가 실패를 인식
web_api /operations/{runId}/fail 호출 성공
web_api가 refund ledger 생성
```

web_api 장애 중 실패:

```text
local job 실행 중 오류 발생
local NestJS가 실패를 인식
web_api /operations/{runId}/fail 호출 실패
local DB에 pending_failure_report 저장
앱이 살아 있으면 retry worker가 재시도
web_api 복구 후 refund ledger 생성
```

web_api 장애 중 성공:

```text
local job 성공, 결과 파일 저장 완료
web_api /operations/{runId}/succeed 호출 실패
local DB에 pending_success_report 저장
retry worker가 나중에 성공 보고
성공 보고 누락만으로 자동 환불하지 않음
```

앱/PC 종료:

```text
local job running 상태에서 앱 종료 또는 PC 정전
앱 재실행
local NestJS recovery가 running job 중 실제 process가 없는 job 탐지
결과 파일/상태를 확인
성공 결과가 없으면 interrupted/failed로 정리
web_api /operations/{runId}/fail 보고
보고 실패 시 pending_failure_report로 남김
```

사용자가 앱을 다시 열지 않거나 local DB가 삭제된 경우:

```text
web_api에는 running operation_run만 남음
local에서 성공/실패 보고가 오지 않음
MVP에서는 admin review 대상으로 표시
후속으로 stale detector를 두어 needs_review 또는 refund_pending으로 전환
```

자동 환불은 신중해야 한다. 결과 파일은 생성됐는데 성공 보고만 실패했을 수도 있기 때문이다. `output_exists_but_report_missing` 같은 상태는 자동 환불보다 `needs_review`가 더 안전하다.

### 10.7 credit balance 계산

남은 크레딧은 ledger에서 계산하거나 집계값을 transaction 안에서 갱신한다.

개념식:

```text
remaining_credit
  = license.total_credits
  - sum(credit_ledger.type = debit)
  + sum(credit_ledger.type = refund)
```

성능을 위해 `licenses.remaining_credits` 같은 집계 컬럼을 둘 수 있지만, `/operations/start`에서는 반드시 같은 transaction 안에서 lock을 잡고 debit까지 끝내야 한다.

## 11. provider endpoint 정책

### 11.1 목표

provider endpoint는 "비용이 발생할 수 있는 서버 자원"이므로 반드시 user identity와 operation policy 또는 operationRunId를 거친다.

현재 임시 상태:

- `/media/search`: 무인증
- `/llm/script`: 무인증
- `/llm/variation`: static service token guard
- `/dialog-highlight/llm`: 무인증

목표:

- 모두 user JWT 필요
- 필요한 경우 active license 필요
- 제품 시작점은 operation policy로 credit cost 결정
- 제품 내부 provider 단계는 operationRunId에 묶어 provider usage만 기록
- provider credential은 web_api가 선택

### 11.2 endpoint matrix 초안

| endpoint | actor | auth | license/operation 확인 | credit 처리 | provider key |
|---|---|---|---|---|---|
| `POST /operations/start` | user app | user JWT | operation policy + active license | 필요 시 debit | 없음 |
| `POST /operations/:runId/succeed` | user app | user JWT + run ownership | 기존 run 확인 | 추가 차감 없음 | 없음 |
| `POST /operations/:runId/fail` | user app | user JWT + run ownership | 기존 run 확인 | 필요 시 refund | 없음 |
| `POST /media/search` | user app | user JWT + operationRunId | run owner + provider scope 확인 | 별도 차감 없음, provider_usage 기록 | DB encrypted Naver credential |
| `POST /llm/script` | user app | user JWT + operationRunId | run owner + provider scope 확인 | 별도 차감 없음, provider_usage 기록 | DB encrypted OpenAI credential |
| `POST /llm/variation` | user app | user JWT + operationRunId | run owner + provider scope 확인 | 별도 차감 없음, provider_usage 기록 | DB encrypted OpenAI credential |
| `POST /dialog-highlight/llm` | user app | user JWT + operationRunId | run owner + provider scope 확인 | 별도 차감 없음, provider_usage 기록 | DB encrypted OpenAI credential |
| admin API key CRUD | operator | operator JWT + permission | 불필요 | 없음 | DB encrypted |
| release runner callback | runner | service token | 불필요 | 없음 | 없음 |

예외:

```text
Naver 이미지 검색 자체를 독립 유료 제품으로 판매하기로 결정하면
media.search.naver를 별도 operation policy로 만들고 /operations/start에서 charge한다.

현재 Dance Highlight 내부 단계로 쓰는 Naver 검색은
dance_highlight.extract run에 묶이는 provider usage일 뿐이다.
```

2026-07-08 구현 transition:

```text
POST /media/search는 기존 dance setup/manual media search 호환을 위해
operationRunId가 없는 요청을 아직 허용한다.

operationRunId가 포함된 요청은 user JWT가 있어야 하며,
run owner + provider scope(naver_image)를 확인한 뒤 provider_usage를 기록한다.

최종 목표는 모든 비용 발생 provider 호출을 user JWT + operationRunId로 묶는 것이지만,
dance setup 단계가 제품 operation run 전에도 검색할 수 있어 바로 필수화하지 않았다.
```

`POST /llm/variation`은 아직 static service token guard 상태다. 이를 user JWT + operationRunId로 전환하려면 먼저 variation AI copy generation의 제품 operation key를 확정해야 한다. 현재 구현의 `ai-cards`는 렌더가 아니라 미리보기 카드 생성 성격이 있으므로, `variation.generate`를 새 billable operation으로 추가할지 또는 별도 preview/free 정책으로 둘지 결정한 뒤 endpoint authz를 전환한다.

2026-07-08 결정: Variation 기능/UX와 과금 기준을 아직 충분히 파악하지 못했으므로 `/llm/variation` provider routing은 이번 구현 범위에서 의도적으로 defer한다. 이 기간에는 새 `variation.generate` billable operation을 추가하지 않는다.

### 11.3 error classification

provider-backed 단계와 operation start/fail/succeed는 사용자가 이해할 수 있는 실패로 분류한다.

권장 코드:

```text
auth_required
auth_expired
auth_refresh_failed
license_required
license_expired
license_depleted
insufficient_credits
web_api_not_configured
web_api_unreachable
web_api_timeout
operation_run_not_found
operation_run_not_owned
operation_already_finished
provider_unavailable
provider_rate_limited
provider_auth_failed
provider_quota_exhausted
provider_invalid_response
```

보안 주의:

- provider key 오류 세부값을 client에 노출하지 않는다.
- provider 응답 원문에 secret이 포함될 수 있으므로 로그 sanitize를 적용한다.
- Authorization, refresh token, one-time code, provider key는 로그 금지.

## 12. provider credential/API key 관리

### 12.1 원칙

provider credential은 다음 두 그룹으로 나눈다.

운영자가 관리해야 하는 provider credential:

- Naver image search key
- OpenAI API key
- 나중의 Kakao/Clova/Supertonic 등
- rotation, quota, usage, 비용 관리가 필요한 key

bootstrap secret:

- JWT private signing key
- DB password
- `API_KEY_ENC_SECRET`
- OAuth client secret
- infra service token

정책:

```text
운영자 관리 provider credential -> DB encrypted storage
bootstrap secret -> env/secret manager
```

### 12.2 DB encrypted provider credential

현재 Naver key 저장 구조는 유지하되 일반화한다.

권장 모델:

```text
provider_credentials
  id
  provider
  label
  credential_type
  public_id
  secret_enc
  status
  daily_used
  daily_limit
  usage_date
  priority
  last_tested_at
  last_error_code
  deleted_at
  created_at
  updated_at
```

provider별 확장이 필요하면 JSON metadata를 둘 수 있다.

```text
metadata_json
```

단, secret 원문은 metadata에 넣지 않는다.

`status='disabled'`와 `deleted_at IS NOT NULL`은 구분한다. `disabled`는 일시 제외 상태로 나중에 다시 `standby` 또는 `active`로 바꿀 수 있다. delete는 row를 보존한 soft delete이며, 운영 목록/runtime candidate/rotation 대상에서 제외한다. provider usage 과거 로그는 FK로 soft-deleted credential row를 join하되, admin 화면에는 label/status/deleted 여부만 보여주고 raw provider credential UUID나 key id는 표시하지 않는다.

### 12.3 OpenAI key 처리

현재 OpenAI key가 env에 있다면 migration 기간에는 명시적 opt-in flag가 켜진 경우에만 fallback을 허용할 수 있다.

권장 migration:

1. DB provider credential model에 `openai` 추가
2. admin API key page에서 OpenAI credential CRUD/테스트 추가
3. provider call은 DB active credential 우선
4. DB credential이 없고 `OPENAI_API_KEY_ENV_FALLBACK_ENABLED=true`이면 env fallback
5. 운영 안정화 후 opt-in flag와 env fallback branch 제거

관리자 페이지에는 모든 provider credential이 보이되 secret 원문은 보여주지 않는다.

표시 예:

```text
Provider | Label | Source | Status | Usage | Last tested | Actions
Naver    | main  | DB     | active | 120/25000 | ...
OpenAI   | prod  | DB     | active | ...       | ...
OpenAI   | env   | env fallback | active | unknown | read-only
```

### 12.4 rotation

Naver처럼 quota가 명확한 provider는 rotation이 필요하다.

정책:

- active credential 우선
- daily limit 도달 시 exhausted
- standby credential로 전환
- 날짜 변경 시 usage reset
- disabled credential은 선택하지 않음
- provider auth failure가 반복되면 credential status를 degraded/exhausted로 전환

OpenAI는 Naver와 quota 형태가 다를 수 있으므로 동일 rotation 모델을 억지로 적용하지 않는다. provider별 credential strategy를 둔다.

## 13. OpenAPI와 route 용어 정리

현재 drift:

- 문서 일부: `/license-requests`
- 현재 코드: `/purchase-requests`
- 문서 일부: logout blocklist
- 현재 코드: blocklist 미구현
- 문서 일부: desktop `?token=<JWT>`
- 목표 설계: desktop `?code=<one-time-code>`

권장 계약:

- 외부 API 이름은 `/purchase-requests`로 통일
- 사용자 화면 용어는 "구매 요청"
- `license`는 승인 후 발급되는 실제 사용권에만 사용
- OpenAPI, web client, admin client, backend controller를 같은 용어로 맞춤

새/변경 endpoint 초안:

```text
GET  /auth/google
GET  /auth/google/callback
POST /auth/desktop/exchange
POST /auth/refresh
POST /auth/logout
POST /auth/logout-all
GET  /auth/sessions
DELETE /auth/sessions/:id

GET  /me

GET  /plans
POST /purchase-requests
GET  /purchase-requests
PATCH /purchase-requests/:id/resubmit
GET  /licenses/current

GET  /operations/:operationKey/quote
POST /operations/start
POST /operations/:runId/succeed
POST /operations/:runId/fail
provider별 endpoint는 operationRunId를 받아 provider usage로 기록

GET/POST/PATCH/DELETE /admin/api-keys
GET/PATCH /admin/purchase-requests
GET /admin/members
```

## 14. 권한 정책

### 14.1 customer user

가능:

- 본인 `/me`
- 본인 구매 요청 생성/조회/재제출
- 본인 현재 이용권 조회
- 본인 제품 operation 시작/결과 보고/provider 단계 실행
- 본인 session 조회/로그아웃

불가:

- 다른 user license 조회
- provider credential 조회
- admin purchase approval
- operator 관리

### 14.2 operator

기본 operator:

- 구매 요청 조회
- 구매 요청 승인/반려
- 회원 조회
- stats 조회

privileged operator 또는 admin:

- API key create/update/delete
- release publish 관련 write
- operator 생성/권한 변경
- 강제 session revoke

MVP에서는 role을 최소 두 개로 시작한다.

```text
operator
admin
```

나중에 permission bitset으로 확장 가능하다.

## 15. 구현 계획

### Phase 0. 문서와 contract drift 정리

목표:

- OpenAPI가 현재/목표 route를 정확히 말하게 한다.
- `/license-requests` vs `/purchase-requests`를 정리한다.
- logout blocklist 문구를 제거하거나 refresh/session 설계로 바꾼다.
- desktop callback을 `token`에서 `code`로 바꿀 예정임을 계약에 반영한다.

검증:

- OpenAPI lint/build
- client 타입 생성이 있다면 생성 성공
- 문서에서 `clipper://auth/callback?token=<JWT>`가 목표 흐름으로 남지 않음

### Phase 1. web_api session/refresh backend

목표:

- user session table 추가
- desktop auth code table 추가
- access JWT RS256 signing key 설정
- JWT public key PEM 산출물 정의
- refresh token hash 저장/rotation
- `/auth/desktop/exchange`
- `/auth/refresh`
- `/auth/logout`
- `/auth/sessions` 최소 구현

검증:

- 로그인 성공 시 session row 생성
- access JWT가 RS256으로 발급됨
- HS256/alg none/잘못된 issuer/audience token 거부
- refresh 성공 시 refresh token hash 교체
- 이전 refresh token 재사용 실패
- logout 후 refresh 실패
- 만료된 refresh token 실패
- no secret logs

### Phase 2. Electron token store와 deep link 변경

목표:

- deep link payload를 token에서 code 중심으로 변경
- Electron이 `/auth/desktop/exchange` 호출
- `auth.bin`에 token bundle 저장
- local NestJS가 사용할 JWT public key PEM을 앱 resource에 포함
- packaged production에서 safeStorage unavailable이면 평문 저장 금지
- logout 시 server logout + local clear

검증:

- packaged/devapp login 성공
- 앱 재실행 후 refresh 또는 /me로 복구
- 로그에 access/refresh/code 원문 없음
- 기존 token-only auth.bin을 발견하면 migration 또는 clear 처리
- packaged app에서 public key PEM을 읽을 수 있음

### Phase 3. Angular auth refresh layer

목표:

- access token 만료 전/후 refresh 처리
- single-flight refresh
- `/me` session restore 개선
- logout/relogin branch 처리
- local browser dev-login과 Electron auth backend 분기 유지

검증:

- access token 만료 시 자동 refresh
- refresh 실패 시 로그인 화면
- 동시에 여러 401 발생해도 refresh 한 번만 호출
- 로그아웃 후 같은 계정 재로그인 성공
- 다른 계정 로그인 시 user state 분리

### Phase 4. local NestJS user token relay와 operation start/report

목표:

- 제품 시작점 local NestJS route가 Authorization header를 받음
- local NestJS가 JWT public key PEM을 시작 시 1회 로드하고 메모리에 캐시
- local NestJS가 RS256 access JWT를 1차 검증
- WebApiClient가 web_api로 Bearer relay
- `@BillableOperation(operationKey)` decorator 또는 동등한 interceptor 도입
- 제품 시작 시 web_api `/operations/start` 호출
- 반환받은 `operationRunId`를 local job에 저장
- local job 성공/실패 시 `/operations/{runId}/succeed` 또는 `/fail` 보고
- 보고 실패 시 local DB에 `pending_success_report` 또는 `pending_failure_report` 저장 후 재시도
- 제품 내부 세부 로컬 동작에는 불필요한 web_api dependency를 만들지 않음
- token을 Python plugin에 넘기지 않음

검증:

- 보호된 제품 시작 route가 user token 없이 실패
- fake/expired/wrong audience JWT가 local NestJS에서 실패
- user token 있으면 web_api로 Authorization 전달
- `/operations/start` 실패 시 local job 시작 안 함
- 성공한 start의 `operationRunId`가 local job에 저장됨
- local job 성공/실패 보고가 web_api에 전달됨
- web_api 장애 시 pending report가 남고 재시도됨
- 제품 내부 세부 로컬 동작은 web_api down이어도 이미 시작된 job 범위에서 동작
- logs에 Authorization header 없음

### Phase 5. web_api operation policy와 credit ledger

목표:

- operation policy table과 code registry 도입
- `OperationBillingStrategy`, `OperationRunStatus`, `CreditLedgerType`, `ProviderScope` enum 도입
- `OPERATION_DEFINITIONS` 기반 seed/upsert 도입
- `/operations/:operationKey/quote`
- `/operations/start`
- `/operations/:runId/succeed`
- `/operations/:runId/fail`
- `operation_runs`, `credit_ledger`, `provider_usage` 도입
- license required/credit cost/billing strategy 판단
- `/operations/start`에서 DB transaction + lock으로 멀티 디바이스 초과 차감 방지
- `charge_then_refund` 적용
- `/media/search`, `/llm/script`, `/dialog-highlight/llm`에 user JWT + operationRunId 검증 적용
- `/llm/variation`은 variation 기능/UX와 과금 기준 파악 전까지 별도 defer
- provider endpoint는 별도 credit 차감 없이 provider_usage 기록
- provider error classification 정리

검증:

- 무토큰 operation start/provider call 401
- license 없음 403 또는 policy error
- credit 부족 409
- operation start 성공 시 credit_ledger debit 1회 기록
- 같은 idempotency key 재시도 시 중복 debit 없음
- local job 실패 보고 시 refund ledger 1회 기록
- provider endpoint 호출은 provider_usage만 남기고 추가 debit 없음
- 같은 계정의 두 session이 동시에 시작할 때 transaction lock으로 초과 차감 방지

### Phase 6. 이용권 정책 정리

구현 상태: 2026-07-08 `web/clipper_web_api` commit `4b89ec6`에서 서버 측 lifecycle 1차 구현 완료.

목표:

- one active license max
- queued license
- active_depleted license
- depleted license 종료 확정
- active license가 없을 때만 승인 즉시 시작
- active license가 있으면 승인된 license는 queued
- queued license user-start endpoint
- 만료/active_depleted 처리
- 자동 queued activation 제거

검증:

- active license 없는 승인은 즉시 active
- active license가 있고 credit 남음이면 queued
- active license credit 0이어도 새 승인은 queued
- 만료 시 queued license가 자동 활성화되지 않음
- active_depleted 시 queued license가 자동 활성화되지 않음
- 사용자가 다음 이용권 시작을 누르면 queued license가 active
- active license에 remaining credit이 있으면 queued license 시작 불가
- 남은 credit 병합 없음

### Phase 7. provider credential 통합

구현 상태: 2026-07-08 `web/clipper_web_api` commit `78907c6`에서 OpenAI DB credential resolver 1차 구현 완료, commit `93ea025`와 `web/clipper_web_admin` commit `df5d6f2`에서 admin API/source-status 표시 완료, `web/clipper_web_admin` commit `79a631c`에서 OpenAI credential create/edit UI 연결 완료, `web/clipper_web_api` commit `d7797d1`에서 Naver key runtime을 `provider_credentials` 기반 adapter로 전환 완료, commit `5e14ae9`에서 OpenAI env fallback을 명시적 opt-in flag 기반으로 제한 완료, commit `c246366`에서 legacy Naver key runtime entity/repository cleanup 완료, commit `4501b36`에서 OpenAI runtime credential status API 추가 완료, `web/clipper_web_admin` commit `a1f8ba4`에서 OpenAI runtime status 표시 완료, `web/clipper_web_api` commit `9191dab`에서 Naver runtime credential status API 추가 완료, `web/clipper_web_admin` commit `961f18c`에서 Naver runtime status 표시 완료. 다음은 provider credential 운영/스테이징 검증 절차 또는 OpenAI env fallback 완전 제거 여부 결정.

목표:

- Naver 중심 API key 모델을 provider credential 모델로 일반화
- OpenAI DB encrypted credential 추가
- env fallback migration
- admin API key page에서 provider source/status 표시

검증:

- Naver 기존 key migration 또는 호환
- OpenAI DB credential로 provider call 성공
- secret 원문 API 응답/로그 없음
- disabled/exhausted credential 미선택

### Phase 8. operator permission hardening

목표:

- operator role/status DB 반영
- admin permission guard
- operator/admin JWT signing/strategy를 user token과 별도 key/secret으로 분리
- legacy `JWT_SECRET` user/operator fallback 제거
- API key write/release write/operator management 보호
- operator session/refresh 정책 적용 여부 결정

검증:

- inactive operator login/usage 실패
- 일반 operator가 API key delete 불가
- admin은 가능
- `JWT_SECRET` 없이 user desktop login/web login/admin login smoke 통과
- operator logout/refresh 정책 정상

## 16. 테스트 계획

web_api:

- auth controller/service unit tests
- RS256 access JWT signing tests
- JWT issuer/audience/algorithm rejection tests
- session repository tests
- refresh rotation tests
- desktop exchange one-time tests
- logout/session revoke tests
- provider authz tests
- license queue/depleted tests
- operation quote/start/succeed/fail tests
- credit ledger debit/refund tests
- operation idempotency tests
- multi-session credit transaction lock tests
- provider_usage audit tests
- provider credential encryption/masking tests

Electron:

- deep link `code` parse tests
- exchange API call tests
- token-store encrypted bundle tests
- legacy `auth.bin` migration/clear tests
- logout server+local clear tests
- redaction tests

Angular:

- auth store restore tests
- refresh single-flight tests
- guard tests
- logout/relogin tests
- local dev backend tests

local NestJS:

- protected operation start route requires Authorization
- JWT public key PEM load/cache tests
- local JWT prefilter rejects missing/fake/expired/wrong audience token
- WebApiClient relays Authorization
- `operationRunId` saved on local job after start
- success/failure report sent to web_api
- pending success/failure report retry
- interrupted running job recovery after app restart
- web_api error classification mapping
- no token to Python plugin

Manual smoke:

```text
1. clean install app
2. Google login
3. app enters main page
4. app restart restores session
5. force access token expiry
6. refresh succeeds
7. credit-required product shows quote/confirmation
8. product start debits credit once
9. internal provider call records provider_usage but does not debit again
10. local job failure refunds credit
11. second device with insufficient remaining credit is blocked
12. already-started local job can continue local-only steps during temporary web_api outage
13. logout clears local token and revokes server session
14. login again creates new session
```

## 17. 예상 공수

MVP 기준 대략:

- web_api session/refresh/exchange: 2-3일
- Electron deep link/token-store/logout: 1-2일
- Angular refresh/session restore: 1-2일
- local NestJS token relay + operation start/report: 2-3일
- web_api operation policy/credit ledger/provider authz: 3-5일
- 이용권 one-active/queue 정리: 2-4일
- provider credential OpenAI migration: 1-3일
- 테스트/수동 검증/문서: 2-3일

총합은 10-20일 범위다. 단, 모든 admin UI와 기기 관리 UI까지 한 번에 넣으면 더 커진다.

권장 MVP cut:

1. user session/refresh/desktop exchange
2. operation quote/start/succeed/fail + credit ledger
3. provider endpoint user JWT + operationRunId 보호
4. one active license + queued/depleted
5. OpenAI DB credential migration은 provider authz 이후 진행

## 18. 결정된 정책

이 문서 기준으로 결정된 정책:

- Google OAuth 단독 유지
- 메인 화면 진입 전 로그인 필요
- JWT access token + opaque refresh token + session table 방식 채택
- access JWT는 RS256으로 서명
- local NestJS에는 JWT public key PEM을 앱 resource로 포함
- local NestJS JWT 검증은 1차 인증 필터이며 최종 권한 판단은 web_api가 수행
- session-only opaque access token 모델은 가능하지만 target 기본값으로 두지 않음
- logout blocklist 중심 모델 비채택
- desktop deep link에는 token 대신 one-time code만 전달
- packaged production에서 token 평문 저장 금지
- user JWT와 operator JWT 분리
- static service token은 설치형 사용자 기능 인증에 쓰지 않음
- MVP에서 플랜별 플러그인 노출/잠금/사용 가능 여부는 제외
- MVP에서 플러그인 스토어 목록은 web_api DB가 아니라 로컬 앱 manifest/catalog/visible list 기준으로 유지
- 제품 시작점은 user JWT + operation policy + license/credit check를 거친다.
- 제품 내부 세부 로컬 동작은 매번 web_api를 호출하지 않는다.
- operation policy는 `operation_key`를 안정 식별자로 쓰고 DB 내부 id는 코드에서 직접 참조하지 않음
- operation policy 생성은 code registry + 명시적 seed/upsert로 처리
- operation policy seed는 기존 row를 덮어쓰지 않고 `ON CONFLICT DO NOTHING` 원칙을 따른다
- `billing_strategy`, `operation_run.status`, `credit_ledger.type`, `provider_scope`는 enum으로 관리하고 문자열 직접 사용을 피한다
- 크레딧 차감 단위는 provider API 호출이 아니라 사용자-facing 제품 operation이다.
- MVP billing strategy는 `charge_then_refund`다.
- local job 성공 시 시작 차감을 유지하고, local job 실패 시 refund ledger를 만든다.
- provider endpoint는 제품 run의 `operationRunId`에 묶어 provider_usage를 기록하며 별도 크레딧 차감은 하지 않는다.
- 멀티 디바이스 초과 차감 방지는 web_api `/operations/start`의 DB transaction/lock으로 처리한다.
- provider key는 설치형 앱에 넣지 않음
- provider credential은 DB 암호화 저장 중심으로 통일
- bootstrap secret은 env/secret manager에 둠
- 한 user의 active license는 최대 1개
- 추가 승인 license는 queued
- credit 소진 시 active license는 active_depleted, queued license는 자동 active 되지 않음
- queued license는 사용자가 명시적으로 시작할 때만 active
- queued license 시작 시 기존 active_depleted license는 depleted로 종료 확정
- active license가 있고 remaining credit이 남아 있으면 queued license 시작 불가
- 남은 기간/크레딧 병합 없음
- MVP에서 credit top-up은 만들지 않음

## 19. 남은 의사결정

아직 정해야 하는 것:

- user refresh/session 유효기간을 30일 고정으로 할지, sliding으로 할지
- 계정당 동시 active session 하드 제한을 MVP에서 켤지
- 제한을 켠다면 초과 로그인 시 거부할지, 오래된 session을 revoke할지
- operator refresh token을 도입할지, access-only 짧은 세션으로 시작할지
- JWT public key rotation을 언제 JWKS로 전환할지
- RS256으로 시작할지 EdDSA까지 검토할지
- operation별 임시 credit cost
- refund 가능한 failure_reason 범위
- user cancel, invalid input, provider failure, system failure의 환불 정책
- stale running operation을 자동 refund할지, admin review로 둘지
- stale 판단 시간 기준
- provider endpoint를 현재 provider별 route로 유지할지, 내부적으로 `/operations/:runId/provider/*` 형태로 묶을지
- devapp과 packaged의 userData/token 저장소를 분리할지
- OpenAI env fallback 제거 시점

권장 기본값:

```text
user refresh/session = 30일 고정
active session 제한 = 일단 DB 구조와 설정값만 준비, hard limit은 off
operator = access 15분 + refresh는 후속 또는 짧은 refresh
JWT signing = RS256
JWT public key distribution = MVP는 앱 resource PEM, 후속은 JWKS
operation route = 현재 provider별 route 유지 후 policy layer 추가
차감 = charge_then_refund
stale operation = MVP에서는 admin review
devapp userData = packaged와 분리
OpenAI env fallback = 기본 off, `OPENAI_API_KEY_ENV_FALLBACK_ENABLED=true`에서만 임시 허용, DB credential 안정화 후 제거
```

## 20. 팀원이 처음 읽을 때의 이해 순서

1. `clipper_web_api`가 신원/이용권/provider key의 단일 출처다.
2. 설치형 앱은 로그인해야 메인 화면에 들어간다.
3. 로그인 세션은 access token, refresh token, session table로 관리한다.

## 20. Session/device privacy hardening addendum (2026-07-08)

이 섹션은 로그인 기기 표시, 기기별 세션 로그아웃, credit ledger/session attribution을 준비하기 위한 개인정보/로그 보안 보강 범위다.

### 20.1 이번 구현 범위

- web Google login도 `user_sessions` row를 생성한다.
- web access JWT에는 `sid`를 넣고, refresh token은 URL/localStorage에 노출하지 않는다.
- web refresh token은 HttpOnly cookie로만 내려준다.
- `/auth/refresh`는 desktop body refresh token 방식과 web HttpOnly cookie 방식을 모두 지원한다.
- `/auth/sessions`는 본인 세션만 조회한다.
- `DELETE /auth/sessions/:id`는 같은 user의 다른 세션만 revoke한다. 현재 세션은 `/auth/logout`으로만 종료한다.
- web client `/app/account`의 로그인 기기 섹션은 실제 세션 목록을 보여준다.
- 화면에는 session id, refresh token hash, IP hash, raw IP, raw device identifier를 표시하지 않는다.
- 현재 수집하는 IP 정보는 원문이 아니라 `ip_masked`와 선택적 `ip_hash`다.
- `ip_hash`는 `SESSION_IP_HASH_SECRET`이 있을 때만 HMAC-SHA256으로 생성한다. secret이 없으면 저장하지 않는다.
- Electron child logs, Electron main JSONL, local NestJS JSON logs에는 token, refresh token, provider key 형태, local absolute path가 redaction된다.

### 20.2 개인정보 처리방침 반영 초안

아래 항목은 운영 개인정보 처리방침에 반영할 초안이다. 실제 공개 문구는 법무/운영 검토 후 확정한다.

수집 항목:

- 계정 정보: 이메일, 이름, 프로필 이미지 URL
- 로그인/세션 정보: 로그인 시각, 최근 사용 시각, 만료 시각, 로그아웃/폐기 시각, 앱 버전, 플랫폼, 브라우저명, OS명, 표시용 기기명
- 보안/부정사용 방지 정보: 마스킹된 IP, IP HMAC hash(원문 IP는 저장하지 않음)
- 이용권/크레딧 사용 정보: 구매 요청, 이용권 상태, credit ledger, billable operation 실행 내역

이용 목적:

- 로그인 유지와 기기별 세션 관리
- 본인 계정의 로그인 기기 조회 및 원격 로그아웃 제공
- 계정 도용/비정상 접근 탐지
- 이용권/크레딧 차감 내역과 고객 지원 이력 확인
- provider credential/API 사용량 운영 진단

표시/접근 제한:

- 사용자는 본인 계정의 세션/기기 정보만 조회한다.
- 관리자는 운영상 필요한 범위의 세션/기기/ledger 정보만 조회한다.
- admin 화면에는 raw IP, raw device identifier, refresh token hash, IP hash 원문을 표시하지 않는다.
- admin 화면이 IP 기준 진단을 제공해야 할 경우에도 masked IP 또는 hash prefix/검색 결과 형태로 제한한다.

### 20.3 다음에 정할 운영 정책

이번 구현에서는 아래 결정을 하지 않는다. 다음 privacy/retention phase에서 확정한다.

- session/device 보관기간: 예를 들어 active session + 만료 후 N일, 보안 로그는 별도 N개월.
- 회원 탈퇴/삭제 시 session/device/log 처리 정책: 즉시 삭제, 식별자 제거 후 보안 로그 보관, 법정 보관 데이터 분리 여부.
- 관리자의 세션/ledger 조회 감사 로그: 누가 어떤 사용자 세션/ledger를 조회했는지 남길지 여부.
- IP hash secret rotation 정책과 기존 hash 재계산/폐기 정책.
4. desktop deep link에는 token을 넣지 않고 one-time code만 넣는다.
5. MVP에서 플러그인 스토어 목록은 로컬 앱 기준으로 유지하고, 플랜별 플러그인 잠금/노출 정책은 제외한다.
6. 제품 기능 시작점은 필요 시 web_api가 operation policy와 이용권/크레딧을 확인한다.
7. local NestJS는 user access token을 web_api로 relay하지만 refresh token이나 provider key는 갖지 않는다.
8. 크레딧 차감 단위는 provider API 호출이 아니라 사용자-facing 제품 operation이다.
9. operation policy는 code registry + seed/upsert로 생성하고, 운영 정책값은 DB/admin이 소유한다.
10. 이용권은 한 번에 하나만 active이고, 추가 구매는 queue된다.
11. queued 이용권은 자동 시작하지 않고, 사용자가 다음 이용권 시작을 눌러야 active가 된다.
12. 제품 기능별 credit cost는 서버 operation policy가 결정한다.
13. provider 호출은 web_api가 수행하고 provider_usage로 audit한다.
14. provider key는 DB 암호화 저장으로 관리하고, env는 bootstrap secret 또는 migration fallback에만 쓴다.

## 21. 관련 문서

현황 감사:

- `.codex/design/AUTH_TOKEN_PERMISSION_PROVIDER_AUDIT_2026-07-07.md`

기존 방향성:

- `clipper_docs/adr/0002-google-only-auth.md`
- `clipper_docs/adr/0003-request-based-licensing.md`
- `clipper_docs/architecture/CLIPPER_WEB_PLATFORM_HANDOFF.md`

관련 working notes:

- `.codex/design/DESKTOP_SECRETLESS_PROVIDER_ROUTING_AND_DIALOG_PIPELINE_2026-07-01.md`
- `.codex/design/DESKTOP_WEB_API_ENTITLEMENT_AND_PROXY_WORKING_NOTES_2026-06-26.md`

현재 구현 참고:

- `web/clipper_web_api/src/modules/auth/**`
- `web/clipper_web_api/src/modules/billing/**`
- `web/clipper_web_api/src/modules/api-keys/**`
- `desktop/clipper_electron/src/main/auth/**`
- `desktop/clipper_angular/src/core/auth/**`
- `desktop/clipper_nestjs/src/core/web-api/**`
