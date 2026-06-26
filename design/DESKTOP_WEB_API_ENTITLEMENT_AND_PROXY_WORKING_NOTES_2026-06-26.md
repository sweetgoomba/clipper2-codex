# Desktop/Web API Entitlement and External API Proxy Working Notes

작성일: 2026-06-26  
상태: working note. 최종 설계서가 아니라, 현재 논의된 전제와 미결정 사항을 이어가기 위한 정리 문서.

## 목적

설치형 desktop 앱에 이용권, 크레딧, 외부 API key 보호 구조를 붙이기 전에 현재 이해한 방향을 정리한다.

핵심 목표는 다음과 같다.

- desktop 앱 번들에 `OPENAI_API_KEY`, Naver/Kakao/Clova key 같은 민감 key를 넣지 않는다.
- 신원, 이용권, 결제, 크레딧의 단일 출처는 `web/clipper_web_api`로 둔다.
- desktop의 로컬 실행 구조는 유지한다. 즉 Angular는 local `clipper_nestjs`를 호출하고, local `clipper_nestjs`가 필요한 경우 `clipper_web_api`를 호출한다.
- 크레딧 차감은 내부 provider API 호출 단위가 아니라 사용자가 실행하는 플러그인/작업 단위로 설계한다.

## 현재 repo 역할

### Desktop

- `desktop/clipper_angular`
  - Electron renderer UI.
  - 현재 대부분의 기능 API 호출은 local `clipper_nestjs`로 간다.
  - web_api와 직접 연결된 부분은 로그인 세션 확인(`/me`) 중심이다.

- `desktop/clipper_electron`
  - Electron shell/main process.
  - Google OAuth deep link로 받은 JWT를 저장한다.
  - packaged mode에서 local `clipper_nestjs`와 Python plugin process를 띄운다.

- `desktop/clipper_nestjs`
  - 사용자 PC 안에서 실행되는 local API/control plane.
  - 프로젝트 상태, 로컬 파일, plugin job, render, progress, 에러 처리를 담당한다.
  - 문서상 trusted-header 소비자이며, 신원/이용권의 SoT가 아니다.

- `desktop/clipper_python`
  - Python plugin runtime.
  - 현재 일부 plugin은 env에서 `OPENAI_API_KEY`, `CLIPPER_LLM_PROXY_URL`, `CLIPPER_SUBSCRIPTION_TOKEN`, Naver/Kakao key 등을 읽을 수 있다.

### Web

- `web/clipper_web_api`
  - 신원, 이용권, 결제, 크레딧, API key 관리의 SoT가 되어야 한다.
  - 현재 Google 로그인/JWT, 운영자 로그인, 구매 요청, 이용권 발급, 토큰 차감 일부가 구현되어 있다.
  - API key 관리 OpenAPI는 있으나 실제 backend module은 아직 없는 상태로 보인다.

- `web/clipper_web_client`
  - 고객용 웹.
  - 구매 요청, 이용권 상태, 다운로드 등.

- `web/clipper_web_admin`
  - 운영자 admin.
  - API key 화면은 있으나 현재 mock 중심이며, web_api 실 구현과 gap이 있다.

## 확인된 현재 구현 사실

### Packaged app key 포함 문제

현재 Electron packaged build는 다음 파일들을 app resources에 복사한다.

- `desktop/clipper_nestjs/.env.packaged`
- `desktop/clipper_python/.env.packaged`

`desktop/clipper_electron/src/main/config/bundled-env-provider.ts`는 이 env 파일들을 읽어서 local NestJS와 Python plugin process env에 주입한다.

현재 구조의 의미:

```text
packaged app
  resources/clipper_nestjs/.env.packaged
  resources/clipper_python/.env.packaged
      -> BundledEnvProvider
      -> local NestJS env
      -> Python plugin env
```

따라서 `.env.packaged`에 외부 API key가 들어가면 설치 앱 번들 안에 평문 key가 들어갈 수 있다. 이 구조는 제품 출시용으로 부적합하다.

### `clipper_web_api -> local clipper_nestjs` 직접 호출은 부적합

`clipper_nestjs`는 사용자 PC의 `127.0.0.1`에 뜨는 local server다.

사용자 PC에서 `127.0.0.1`은 사용자 PC 자신을 뜻한다. 하지만 cloud `clipper_web_api`에서 `127.0.0.1`은 cloud 서버 자신을 뜻한다.

따라서 다음 구조는 실제 제품 환경에서 성립하지 않는다.

```text
Angular
  -> clipper_web_api
      -> http://127.0.0.1:9019/v1 on user's PC
```

이를 가능하게 하려면 사용자 PC 공개 포트, 터널링, long-lived WebSocket command channel 같은 별도 구조가 필요하다. 현재 이용권/크레딧 검증 목적에는 과하다.

현실적인 방향은 다음이다.

```text
Angular
  -> local clipper_nestjs
  -> clipper_web_api
```

또는 계정/이용권 조회처럼 local project context가 필요 없는 화면은 Angular가 web_api를 직접 호출할 수 있다. 다만 desktop 기능 실행 흐름은 local NestJS를 거치는 것이 더 일관적이다.

## 합의된 방향

### 1. 외부 API key는 web_api 쪽으로 이동한다

Naver, Kakao, OpenAI, Gemini, Clova 등 provider key는 desktop app bundle이나 Python process env에 넣지 않는 방향으로 간다.

목표 구조:

```text
local NestJS or Python
  -> web_api proxy
  -> external provider API
```

web_api만 외부 provider key를 보유한다.

### 2. desktop 기능 실행은 local NestJS 중심으로 유지한다

desktop 앱에서 사용자가 버튼을 누르면 기본 흐름은 다음처럼 본다.

```text
user event
  -> Angular
  -> local clipper_nestjs
  -> web_api when entitlement, credit, or external provider call is needed
```

이유:

- local NestJS가 프로젝트 상태, 파일 경로, plugin job, render context를 알고 있다.
- 기존 desktop 에러 처리와 progress 흐름이 local NestJS 중심이다.
- Angular가 web_api와 local NestJS를 기능별로 직접 오가면 에러 처리와 상태 경계가 흐려질 수 있다.

### 3. 크레딧 차감은 provider API 호출 단위가 아니다

중요한 제품 전제:

```text
크레딧 차감 단위 = 내부 Naver/OpenAI/Gemini 호출 단위가 아님
크레딧 차감 단위 = 사용자가 실행하는 플러그인/작업 액션 단위
```

예시:

- Naver 이미지 API 1회 호출마다 크레딧 차감하지 않는다.
- Gemini/OpenAI 호출 1회마다 사용자 크레딧 차감하지 않는다.
- pipeline 내부에서 캐시 미스 때문에 Naver 이미지를 여러 번 가져와도 그것은 내부 수행 비용이다.
- 사용자에게 보이는 "하이라이트 추출 실행", "숏폼 생성하기" 같은 작업 단위에서 차감한다.

web_api는 provider 사용량을 운영 비용 분석용으로 기록할 수 있다. 하지만 그 기록이 곧 사용자 크레딧 차감 이벤트는 아니다.

### 4. 차감량은 클라이언트가 보내면 안 된다

Angular나 local NestJS가 다음처럼 요청하면 안 된다.

```json
{
  "feature": "shortform.render",
  "credits": 50
}
```

클라이언트 값은 조작 가능하다. 차감량 정책은 web_api에 있어야 한다.

권장 요청 형태:

```json
{
  "operation": "shortform.render",
  "context": {
    "projectId": "local-project-id",
    "clipCount": 8
  }
}
```

web_api가 내부 정책으로 판단한다.

```text
shortform.render = N credits
dance_highlight.run = N credits
dialog_highlight.run = N credits
```

## JWT 역할

JWT는 web_api가 "이 요청이 어느 로그인 유저의 요청인지" 확인하기 위한 서명된 티켓이다.

JWT가 증명하는 것:

```text
이 요청은 user-123의 요청이다.
```

JWT가 증명하지 않는 것:

```text
user-123이 현재 이용권을 가지고 있다.
user-123의 크레딧이 충분하다.
이 작업을 실행해도 된다.
```

이용권과 크레딧은 web_api DB가 판단해야 한다.

현재 desktop 흐름:

```text
Google login
  -> web_api
  -> JWT 발급
  -> Electron deep link
  -> Electron token-store 저장
  -> Angular /me 검증
```

앞으로 local NestJS가 web_api를 호출하려면 web_api가 사용자를 알 수 있어야 한다.

기본 흐름 후보:

```text
Angular
  -> local NestJS
      Authorization: Bearer <user JWT>

local NestJS
  -> web_api
      Authorization: Bearer <same user JWT>
```

web_api는 JWT를 검증하고 user id를 얻은 뒤, 이용권/크레딧 정책을 적용한다.

## 주요 흐름 후보

### Shortform 계열

사용자가 `클립 생성하기` 또는 `숏폼 생성하기`를 누른다.

```text
Angular
  -> local NestJS
      operation = shortform.clip.generate or shortform.render

local NestJS
  -> web_api
      entitlement/credit check or charge

local NestJS
  -> Python/plugin/local services
      perform pipeline
```

현재 사용자 설명 기준으로는 `숏폼 생성하기`는 크레딧 차감 대상일 가능성이 높다. `클립 생성하기`는 차감 대상인지 아직 결정되지 않았다.

내부 pipeline에서 일어날 수 있는 작업:

- Naver image search로 clip별 asset 후보 수집
- Gemini/OpenAI로 대본 또는 프롬프트 생성
- TTS 생성
- ffmpeg render

이 내부 provider 호출들은 별도 사용자 크레딧 차감 단위가 아니다. 작업 단위 차감 정책 안에 포함된 내부 비용으로 본다.

### Dance highlight plugin

사용자가 안무 영상 하이라이트 추출을 실행한다.

```text
Angular
  -> local NestJS
      start dance_highlight job

local NestJS
  -> web_api
      dance_highlight.run entitlement/credit decision

local NestJS
  -> Python plugin
      run pipeline
```

pipeline 내부에서 멤버 이미지 임베딩 캐시가 없으면 Naver image API proxy를 사용할 수 있다.

```text
Python or local NestJS
  -> web_api provider proxy
  -> Naver API
```

이 Naver 호출은 사용자 크레딧 별도 차감 이벤트가 아니다. `dance_highlight.run` 작업 비용 안에 포함되는 내부 provider 사용이다.

### Dialog highlight plugin

현재 `clipper_python` 쪽에 `OPENAI_API_KEY` 또는 `CLIPPER_LLM_PROXY_URL + CLIPPER_SUBSCRIPTION_TOKEN` 흐름이 있다.

목표는 직접 `OPENAI_API_KEY`를 desktop/Python env에 넣지 않는 것이다.

가능한 최종 방향:

```text
Python dialog_highlight
  -> local NestJS proxy or web_api proxy
  -> OpenAI/Gemini provider
```

여기서 Python이 web_api를 직접 호출할지, local NestJS를 거칠지는 아직 미결정이다.

## Python 내부 외부 API 호출 방식 후보

### 방식 A: Python -> web_api 직접 호출

```text
Python plugin
  -> web_api proxy
  -> external provider
```

장점:

- Python 코드가 OpenAI-compatible proxy를 쓰는 경우 `base_url` 교체로 비교적 작게 갈 수 있다.
- local NestJS 중계 endpoint를 많이 만들지 않아도 된다.

단점:

- Python process에 사용자 JWT 또는 job-scoped token을 전달해야 한다.
- plugin이 사용자 인증 토큰을 직접 들고 provider proxy를 호출하게 된다.
- 장기적으로 third-party plugin까지 고려하면 권한 범위가 넓다.

보완책:

- 사용자 JWT 대신 job-scoped operation token을 Python에 전달한다.
- operation token은 job id, operation, 허용 proxy scope, 만료 시간을 가진다.

### 방식 B: Python -> local NestJS -> web_api

```text
Python plugin
  -> local NestJS
  -> web_api proxy
  -> external provider
```

장점:

- Python에 사용자 JWT를 넘기지 않아도 된다.
- local NestJS가 job context, user context, 로그, 에러, timeout을 중앙에서 다룰 수 있다.
- desktop 구조에서 local NestJS가 control plane이라는 방향과 잘 맞는다.

단점:

- local NestJS에 proxy 중계 endpoint가 필요하다.
- OpenAI SDK 호환 proxy를 그대로 쓰기 어렵거나, local NestJS가 OpenAI-compatible endpoint를 흉내 내야 할 수 있다.
- LLM streaming, 대용량 응답, timeout 처리가 한 계층 더 늘어난다.
- provider error가 `provider -> web_api -> local NestJS -> Python` 순서로 감싸지므로 trace/error contract 설계가 필요하다.
- local NestJS가 provider proxy 변환까지 담당하면 역할이 커질 수 있다.

방식 B의 단점은 "불가능하다"가 아니라 구현 범위와 경계 설계가 커진다는 의미다.

### 방식 C: Python에 provider API key를 계속 env로 전달

```text
Python plugin
  -> external provider directly
```

제품 출시 구조로는 피해야 한다. key가 desktop bundle 또는 local process env에 남는다.

## Entitlement/Credit API 형태 초안

아직 확정은 아니지만, 작업 단위 차감 모델에는 다음 개념이 필요하다.

### Operation

사용자에게 보이는 실행 단위.

예시:

- `shortform.clip.generate`
- `shortform.render`
- `dance_highlight.run`
- `dialog_highlight.run`
- `tts.generate` if exposed as standalone paid action

### Credit policy

web_api가 가지고 있는 서버 정책.

예시:

```text
operation -> required credits
operation -> required license plan
operation -> allowed provider scopes
operation -> refund policy
```

### Charge timing 후보

1. 실행 시작 전에 즉시 차감
2. 실행 시작 전에 예약(reserve), 성공 시 확정(capture), 실패 시 해제(refund)
3. 성공 후 차감

각 방식은 UX와 장애 처리 정책이 다르다.

현재 느낌상 긴 작업/실패 가능성이 있는 plugin job은 `reserve -> capture/refund`가 안전할 수 있다. 다만 MVP에서는 즉시 차감 후 실패 시 수동/자동 환급 정책으로 단순화할 수도 있다.

### Idempotency

사용자가 버튼을 두 번 누르거나 network retry가 발생하면 중복 차감이 생길 수 있다.

따라서 차감 요청에는 idempotency key 또는 operation id가 필요하다.

예시:

```text
desktopOperationId = uuid generated by local NestJS
userId + operation + desktopOperationId = unique charge
```

## API key 관리 상태

현재 `web_admin`에는 API key 화면과 mock data가 있다.

현재 `web_api/docs/api/openapi.yaml`에도 `/admin/api-keys` 계약이 있다.

하지만 `web_api/src/modules` 기준으로 API key backend module은 아직 구현되지 않은 것으로 보인다.

필요한 backend 설계:

- provider key 저장 entity
- secret encryption at rest
- masked key display
- provider별 status
- rotation/active key selection
- usage metrics
- operator permission
- audit log

주의:

- API key 관리 화면은 운영자용 기능이다.
- 사용자는 provider key를 절대 보지 않는다.
- desktop app은 provider key를 절대 받지 않는다.

## 현재 계약 drift

현재 OpenAPI, web client/admin, web_api 구현 사이에 이름 차이가 있다.

예시:

- OpenAPI: `/license-requests`
- 구현/client/admin: `/purchase-requests`

상태 이름도 혼재되어 있다.

- OpenAPI/client 모델: `issued`
- 구현 DB/entity: `approved`

이용권/결제/크레딧 설계 전에 외부 API contract 용어를 정리해야 한다.

결정 방향 후보:

- 외부 계약은 `license-requests`로 통일하고 DB 내부만 `purchase_requests` 유지
- 외부 계약도 `purchase-requests`로 유지하고 문서/프론트 모델을 구현에 맞춤
- "구매 요청"과 "이용권 발급"을 분리해서 endpoint를 재정의

## 미결정 사항

### 1. 크레딧 차감 대상 operation

아직 정확히 정해지지 않았다.

후보:

- `shortform.clip.generate`
- `shortform.render`
- `dance_highlight.run`
- `dialog_highlight.run`
- standalone `tts.generate`
- standalone image generation if exposed

현재 사용자 의견:

- shortform의 `숏폼 생성하기`는 차감 대상일 가능성이 높다.
- shortform의 `클립 생성하기`는 차감 대상인지 미정이다.
- dance highlight는 plugin 실행 시작 시 차감하는 방향으로 보인다.

### 2. 차감 시점

후보:

- 시작 전 즉시 차감
- 시작 전 예약 후 성공 시 확정
- 성공 후 차감

정해야 할 것:

- 사용자가 취소하면 환급할지
- provider 실패면 환급할지
- local ffmpeg 실패면 환급할지
- 입력 검증 실패면 차감하지 않을지
- app crash/network error 때 reserve를 어떻게 만료할지

### 3. Python 외부 API proxy 경로

후보:

- Python -> web_api 직접 호출
- Python -> local NestJS -> web_api
- provider별로 혼합

현재 방향성:

- 사용자 JWT를 Python에 직접 넘기는 것은 조심해야 한다.
- local NestJS를 control plane으로 유지하려면 방식 B가 자연스럽다.
- OpenAI-compatible SDK 호환을 중시하면 방식 A 또는 local NestJS OpenAI-compatible proxy가 필요할 수 있다.

### 4. local NestJS가 web_api에 user identity를 전달하는 방식

후보:

1. Angular가 local NestJS 요청마다 `Authorization: Bearer <JWT>`를 붙이고, local NestJS가 web_api에 전달한다.
2. Electron main process가 token-store의 JWT를 local NestJS에 안전하게 제공한다.
3. local NestJS가 desktop session token을 별도로 발급/보관하고 web_api와 교환한다.

현재 가장 단순한 후보:

```text
Angular -> local NestJS: Authorization Bearer user JWT
local NestJS -> web_api: Authorization Bearer same user JWT
```

정해야 할 것:

- local NestJS가 JWT를 자체 검증할지, 단순 전달만 할지
- local NestJS 로그에 token이 남지 않도록 어떻게 막을지
- WebSocket/realtime에도 identity를 실을지
- 다운로드/파일 조회 같은 비과금 local API에도 token을 요구할지

### 5. operation token 도입 여부

Python에 사용자 JWT를 넘기지 않으려면 job-scoped token이 필요할 수 있다.

예시:

```text
operationToken:
  jobId
  userId or subject
  operation
  allowedProxyScopes
  expiresAt
```

정해야 할 것:

- operation token을 누가 발급하는가: local NestJS or web_api
- Python에는 operation token만 줄 것인가
- operation token으로 web_api proxy를 직접 호출할 수 있게 할 것인가
- token 만료와 retry 정책

### 6. web_api proxy API contract

provider별 endpoint를 어떻게 나눌지 정해야 한다.

후보:

- operation 중심
  - `/desktop/operations/:operationId/proxy/llm`
  - `/desktop/operations/:operationId/proxy/media-search`
- provider 중심
  - `/provider-proxy/openai/responses`
  - `/provider-proxy/naver/image-search`
- OpenAI-compatible 중심
  - `/openai/v1/responses`
  - `/openai/v1/chat/completions`

정해야 할 것:

- local NestJS가 provider request/response를 얼마나 알아야 하는가
- Python SDK 호환을 얼마나 유지할 것인가
- streaming을 지원할 것인가
- web_api가 provider 응답을 그대로 pass-through할 것인가, normalized response로 바꿀 것인가

### 7. API key admin backend 구현 범위

정해야 할 것:

- 1차 provider 범위: Naver, Kakao, OpenAI, Gemini, Clova 중 어디까지인가
- key encryption 방식
- active/standby/exhausted rotation 정책
- usage counter는 provider 실제 quota와 어떻게 맞출 것인가
- OpenAI/Gemini 비용 잔액을 admin에서 어떻게 보여줄 것인가

### 8. offline behavior

web_api가 unreachable이면 어떻게 할지 정해야 한다.

후보:

- 과금/외부 API 필요한 기능은 실행 불가
- 순수 local 기능만 허용
- 이미 reserve된 operation만 일정 시간 재시도 허용

API key가 web_api에만 있으면 외부 provider 의존 기능은 offline에서 실행할 수 없다.

### 9. 실패/환급/audit

크레딧을 차감하는 작업은 audit이 필요하다.

정해야 할 것:

- charge ledger table 구조
- reserve/capture/refund 상태
- 실패 사유 분류
- 운영자 수동 조정 기능
- 사용자에게 보여줄 이력

### 10. 용어 정리

현재 문서/구현에서 다음 용어가 섞인다.

- token
- credit
- tokenAllowance
- includedCredits
- license request
- purchase request
- approved
- issued

설계 전에 user-facing 용어와 DB/internal 용어를 분리해야 한다.

## 권장되는 다음 설계 순서

한 번에 전체를 구현하지 말고, 다음 순서로 쪼개는 편이 안전하다.

1. 용어/계약 정리
   - `credit` vs `token`
   - `license-request` vs `purchase-request`
   - `approved` vs `issued`

2. desktop identity propagation
   - Angular -> local NestJS -> web_api로 JWT를 어떻게 전달할지 결정
   - local NestJS auth boundary 정리

3. operation-based entitlement/credit design
   - operation id
   - credit policy
   - reserve/capture/refund
   - idempotency

4. web_api external provider proxy design
   - provider key storage
   - proxy endpoint contract
   - admin key management
   - provider usage logging

5. Python proxy migration strategy
   - dialog_highlight OpenAI path
   - dance image search path
   - shortform provider calls
   - 방식 A/B 혼합 여부 결정

## 현재까지의 핵심 결론

```text
web_api는 사용자 PC의 local NestJS를 직접 호출하지 않는다.

desktop 기능 실행은 Angular -> local NestJS가 기본이다.

local NestJS는 이용권/크레딧 판단 또는 외부 provider 호출이 필요할 때 web_api를 호출한다.

외부 API key는 web_api만 보유한다.

사용자 크레딧은 내부 provider API 호출 단위가 아니라 플러그인/작업 operation 단위로 차감한다.

차감량은 클라이언트가 보내지 않고 web_api 정책이 결정한다.

Python provider 호출은 가능하지만, user JWT를 직접 넘길지 local NestJS를 거칠지 아직 결정해야 한다.
```

