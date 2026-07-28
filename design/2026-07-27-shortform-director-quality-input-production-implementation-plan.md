# AI 숏폼 디렉터 품질 입력·실제 영상 제작 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사용자가 쉬운 운영 프로필 하나만 고르면 실행 시점의 Google Trends·네이버·
YouTube를 실제 조사하고, 근거가 연결된 주제와 주제별 영상 후보 10개 이상을 만든 뒤,
선택 후보를 장면별로 설계·제작해 Motion Canvas MP4로 렌더하고 기존 작업 큐와 보관함에서
확인할 수 있게 한다.

**Architecture:** 데스크톱 Nest가 워크플로와 `CLIPPER_DATA_DIR` JSON SoT를 소유하고,
credential이 필요한 모든 외부 호출은 기존 사용자 인증을 거쳐 웹 API가 대신한다.
AI Director는 기존 operation run·크레딧 차감·환불을 사용하지 않는다. credential
원문은 기존 관리자 웹에서 등록해 웹 API의 암호화 DB에만 둔다. 데스크톱 Angular는
플러그인 내부 6개 서브 페이지와 `근거·과정` 패널만 제공하며 파일시스템을 직접 읽지
않는다. 기존 AI Director 프로젝트·TTS·에셋 저장·Motion Canvas 렌더·공용
Jobs·Projects 보관함을 교체하지 않고 새 조사/후보 계보를 앞단에 연결한다.

**Tech Stack:** Angular 19 standalone/zoneless + Angular Material · NestJS 10
(desktop) · NestJS 11 + TypeORM/PostgreSQL (web API) · local JSON/files · OpenAI
Responses API · Google Gemini API · YouTube Data API v3 · Naver Search/DataLab ·
Google Trends RSS/CSV · Motion Canvas · node:test · Jest · Karma/Jasmine.

**Approved design:**

`.codex/design/2026-07-27-shortform-director-quality-input-lineage-and-production-design.md`

---

## 0. 시작 기준점

계획 작성 시 확인한 기준점은 다음과 같다. 구현 시작 직전에 같은 명령으로 다시 확인하고,
달라진 변경은 되돌리지 말고 먼저 사용자에게 보고한다.

| 저장소 | branch / HEAD | upstream | 상태 |
|---|---|---:|---|
| `clipper_docs` | `main` / `ef93c57` + 이 계획 커밋 | 작성 전 `ahead 1` | 설계 문서만 선행 |
| `desktop/clipper_angular` | `feat/shortform-director-foundation` / `c93be51` | `0/0` | clean |
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` / `d27db82` | `0/0` | clean |
| `web/clipper_web_api` | `feat/shortform-director-foundation` / `480bc30` | `0/0` | clean |
| `web/clipper_web_admin` | `feat/shortform-director-foundation` / `8a3333f` | `0/0` | clean |
| `legacy/adlight_python` | `fix/use-giphy-for-gif-search` / `46b2ada` | `0/0` | `fastapi_server.spec` 수정 보존 |

구현 전 확인:

```bash
git status --short --branch
git rev-list --left-right --count HEAD...@{upstream}
git log -5 --oneline --decorate
```

`legacy/adlight_python/fastapi_server.spec`는 이 작업의 파일이 아니다. stage, reset, revert,
format, commit 대상에 포함하지 않는다.

---

## 1. 전역 제약

- **credential 경계:** `OPENAI_API_KEY`, Google AI key, YouTube Data key, Naver Client
  Secret을 Electron 환경 파일·빌드 산출물·desktop 로컬 JSON에 넣지 않는다.
- **기존 관리자 경로 재사용:** 관리자 페이지 → `POST /admin/api-keys` → `SecretCipher`
  → admin DB의 `provider_credentials` 흐름을 확장한다. 새로 필요한 credential은
  `youtube` 하나다. Naver·OpenAI·Gemini는 현재 등록값을 재사용한다.
- **호출 경계:** desktop은 사용자 bearer token으로 AI Director 전용 웹 API endpoint를
  호출한다. AI Director request/response에는 `operationRunId`를 두지 않는다. 웹 API
  응답에는 masked/opaque credential ID와 provider request ID는 허용하지만 원문 key와
  인증 header는 절대 포함하지 않는다.
- **크레딧 제외:** 기존 AI Director 전략·영상 구성 경로의
  `OperationChargeGuardService`, `WebApiOperationRunService`,
  `OperationsService.authorizeProviderUse()` 의존을 제거한다. 새 research, candidate,
  video plan, media, quality report에도 quote/start/succeed/fail/refund 또는 operation
  policy를 추가하지 않는다. 다른 플러그인의 operations·billing 기능은 건드리지 않는다.
- **계약 우선:** 웹 API 변경은
  `web/clipper_web_api/docs/api/openapi.yaml`을 먼저 고친다. 성공 응답은 기존 규약대로
  raw object/array이며 공통 envelope를 추가하지 않는다.
- **로컬 JSON SoT:** 조사 원본, 정규화 결과, prompt, provider 공개 응답, 검증·탈락
  사유, usage, 비용 추정, 장면·미디어·렌더 계보를
  `CLIPPER_DATA_DIR/shortform-director` 아래에 저장한다.
- **binary 분리:** provider가 반환한 이미지·영상·음성 bytes는 기존 로컬 binary
  storage에 한 번만 저장한다. audit JSON에는 base64 본문 대신 artifact ID, MIME,
  byte size, SHA-256을 기록해 같은 binary를 거대한 JSON으로 중복하지 않는다.
- **민감정보 redaction:** 저장 직전에 header의 `authorization`,
  `x-goog-api-key`, `x-naver-client-secret`과 query/body의 `key`, `apiKey`,
  `clientSecret`, `accessToken` 및 그 밖의 세션 토큰 값을 제거한다.
  웹 API가 만든 공개 request ID와 provider request ID는 저장할 수 있지만 session,
  billing, credit ledger ID는 AI Director artifact에 저장하지 않는다.
- **불변 실행:** 원본 fetch/LLM attempt는 덮어쓰지 않는다. 재시도는 새 ID와 새 JSON이다.
  index/manifest/current pointer만 temp 파일 작성 후 rename으로 교체한다.
- **최신성:** Google Trends, Naver, YouTube는 병렬 발견원이다. 어느 하나도 다른
  출처가 만든 주제를 확인만 하는 보조 경로로 만들지 않는다.
- **Google Trends:** 런타임 자동 수집은 공식 RSS를 사용한다. CSV parser와 공식
  내보내기 fixture도 구현하되, 문서화된 안정적 다운로드 URL이 없는 동안 HTML·내부 RPC
  추출로 CSV를 자동화하지 않는다. CSV가 없어도 RSS 수집 성공을 실패로 바꾸지 않는다.
  알파 API는 사용자의 선정 통보 전까지 코드 경로를 만들지 않는다.
- **Google Trends 기간·시각:** `GoogleTrendsWindow`는
  `'4h' | '24h' | '48h' | '7d'`이고 `hours`는 각각 `4/24/48/168`이다. 같은 research
  run의 네 RSS 호출은 동결된 UTC `asOf` 하나를 공유하지만 각각 별도
  `SourceFetchRecordV1`이다. `collectedAt`은 각 호출의 실제 terminal UTC이며
  `window`를 항목 나이로 추론하지 않는다.
- **SourceFetch durable-before-consume:** network source client가 strict
  `SourceFetchRecordV1`을 완성하면 coordinator는 즉시 immutable JSON artifact로
  저장한다. 이후 정규화·LLM은 artifact registry에서 다시 읽어 runtime parser를 통과한
  record만 소비한다. C1의 공식 CSV parser는 parsed DTO만 만들며 network fetch record를
  꾸미지 않는다.
- **YouTube:** `order=date` lane을 만들지 않는다. `publishedAfter`가 있는
  `viewCount`/`relevance` lane을 병렬 호출하고 `videos.list` 통계로 다시 평가한다.
- **후보 수:** 첫 후보 생성은 원본 약 20개를 요청한다. 검증 후 10개 미만이면 부족한
  variation만 최대 2회 보충하고, 그래도 10개가 안 되면 성공으로 표시하지 않는다.
- **미디어 결정:** 사전 보유 파일 탐색을 시작점으로 쓰지 않는다. 장면 목적에 따라
  `official-source`, `licensed-real-media`, `generated-image`, `generated-video`,
  `programmatic-diagram`, `kinetic-typography`, `mixed-composition` 중 하나를 먼저
  고른 뒤 해당 경로만 수행한다.
- **저작권 경계:** YouTube 조사 URL은 `evidenceRef`/`referencePatternRef`다. 명시적인
  재사용 조건이 확인되지 않으면 `productionMediaRef`로 승격하지 않는다.
- **렌더:** AI Director의 실행 가능한 렌더 adapter는 Motion Canvas 하나만 등록한다.
- **기존 큐·보관함:** 렌더는 현재 `JobsService.start()`를 계속 사용한다. 성공 시
  `ProjectsService.recordCompletedJob()`이 기존 `projects/projects.json`, file ticket,
  보관함 카드/상세 재생 경로에 등록해야 한다.
- **기존 데이터 보존:** 현재 `shortform-director/projects.json`과 기존 프로젝트를
  파괴적으로 변환하지 않는다. 새 필드는 optional로 hydrate하고 새 실행부터 채운다.
- **쉬운 기본 UX:** 기본 폼의 필수값은 프로필 이름·분야·대상·목적 네 개다. 금지사항,
  필수 사실, 선택 키워드, 사용자 자료는 고급/선택 입력이다.
- **동적 결과:** 예시 인물·그룹·제품·키워드를 fixture의 정답으로 고정하지 않는다.
  테스트 fixture는 가상의 데이터와 실행 시각 상대값을 사용한다.
- **유료 실호출:** fake provider 테스트와 로컬 렌더 검증까지 자동 수행한다. 실제
  Omni/Veo/LLM 비교 직전에는 호출 수와 예상 비용을 계산해 사용자 승인을 받는다.
- **UI 규약:** desktop Angular는 `<app-page>`, standalone/zoneless/signals,
  `.ts/.html/.scss/.spec.ts` 4파일, Material·semantic token을 지킨다. raw hex를
  추가하지 않는다.
- **분리 원칙:** Angular page는 route 상태와 use-case 호출만 조정하고, 프로필 폼,
  source 상태, topic, candidate, scene, media 비교, lineage drawer처럼 독립적인 표시와
  상호작용은 작은 컴포넌트로 분리한다. Nest controller는 HTTP 변환만, application
  service는 use-case 조정만, provider·파일·HTTP 세부는 infrastructure adapter가
  담당한다. 한 클래스가 저장·외부 호출·검증·표시 모델 조립을 함께 맡지 않는다.
- **의존 역전:** application 계층은 source/inference/storage의 좁은 port에 의존하고
  module에서 실제 adapter를 주입한다. 테스트는 port의 fake로 use-case 결과를 검증하며
  page/component 테스트가 거대한 범용 mock 하나에 의존하지 않게 한다.
- **오류 규약:** desktop 화면은 기존 `AppError`/trace/catalog를 사용한다. provider의
  raw 오류 문자열을 그대로 카드·toast에 렌더하지 않는다.
- **작은 커밋:** 아래 task 단위로 관련 저장소만 commit한다. push/PR/merge는 별도
  사용자 요청 전까지 하지 않는다.

---

## 2. 최종 데이터·호출 흐름

```text
web admin
  └─ Naver / OpenAI / Gemini / YouTube credential 등록·검사
       └─ web API encrypted provider_credentials

desktop Angular
  └─ 운영 프로필 → 조사 → 주제 → 영상 후보 → 영상 제작 → 완성 영상
       └─ desktop Nest run coordinator
            ├─ Google Trends RSS (credential 없음)
            ├─ web API Naver Search/DataLab (전용 source allowlist)
            ├─ web API YouTube Data (전용 source allowlist)
            ├─ web API LLM/멀티모달 (역할별 model allowlist)
            └─ local immutable JSON + binary sidecar
                 └─ 기존 TTS/asset storage/Motion Canvas
                      └─ 기존 Jobs queue
                           └─ 기존 Projects 보관함 + file ticket 재생
```

AI Director 과금 경계:

- `shortform_director.strategy`, `shortform_director.video_plan`은 active operation
  catalog에서 제거한다.
- `shortform_director.research`, `shortform_director.candidates`,
  `shortform_director.media`, `shortform_director.quality_report` operation은 만들지
  않는다.
- 사용량·token·provider 예상 비용은 품질·모델 비교용 audit metadata일 뿐 Clipper
  크레딧 차감값이 아니다.
- 인증, credential 조회, endpoint별 source/model allowlist, rate/size/timeout 제한은
  과금 없이도 그대로 적용한다.

---

## 3. 목표 파일 구조

### `web/clipper_web_api`

```text
src/modules/
├─ provider-credentials/application/youtube-credential.service.ts
├─ shortform-director-research/
│  ├─ application/naver-research-provider.service.ts
│  ├─ application/youtube-data-provider.service.ts
│  ├─ application/shortform-director-source-fetch.service.ts
│  ├─ domain/provider-call-audit.contract.ts
│  ├─ presentation/dto/fetch-shortform-director-source.dto.ts
│  ├─ presentation/shortform-director-research.controller.ts
│  └─ shortform-director-research.module.ts
└─ shortform-director-inference/
   ├─ application/shortform-director-inference.service.ts
   ├─ domain/shortform-director-model-catalog.ts
   ├─ domain/shortform-director-inference.contract.ts
   ├─ presentation/dto/run-shortform-director-inference.dto.ts
   ├─ presentation/shortform-director-inference.controller.ts
   └─ shortform-director-inference.module.ts
```

### `desktop/clipper_nestjs`

```text
src/modules/shortform-director/
├─ domain/
│  ├─ operating-profile.ts
│  ├─ run-record.ts
│  ├─ research.ts
│  ├─ video-candidate.ts
│  ├─ scene-media-decision.ts
│  └─ lineage.ts
├─ infrastructure/
│  ├─ atomic-shortform-director-json.store.ts
│  ├─ json-shortform-director-profile.repository.ts
│  ├─ local-shortform-director-run.repository.ts
│  ├─ google-trends-trending.client.ts
│  └─ shortform-director-artifact.registry.ts
├─ application/
│  ├─ shortform-director-run.coordinator.ts
│  ├─ shortform-director-source-fetch-web-api.client.ts
│  ├─ shortform-director-inference-web-api.client.ts
│  ├─ shortform-director-research.service.ts
│  ├─ shortform-director-candidate.service.ts
│  ├─ shortform-director-video-plan-run.service.ts
│  ├─ shortform-director-scene-media.service.ts
│  ├─ shortform-director-lineage.service.ts
│  └─ shortform-director-quality-report.service.ts
└─ presentation/
   ├─ shortform-director-profile.controller.ts
   ├─ shortform-director-research.controller.ts
   ├─ shortform-director-production.controller.ts
   ├─ shortform-director-lineage.controller.ts
   └─ dto/ (각 task에 열거한 profile/research/candidate/video-plan/media/quality DTO)
```

### `desktop/clipper_angular`

```text
src/features/shortform-director/
├─ layout/shortform-director-shell/
├─ pages/
│  ├─ profiles-page/
│  ├─ ideas-page/
│  ├─ candidates-page/
│  ├─ production-page/
│  ├─ outputs-page/
│  └─ runs-page/
├─ components/
│  ├─ director-sidebar/
│  ├─ operating-profile-form/
│  ├─ research-source-status/
│  ├─ research-topic-card/
│  ├─ video-candidate-card/
│  ├─ production-scene-card/
│  ├─ media-comparison-panel/
│  ├─ evidence-process-drawer/
│  ├─ run-timeline/
│  └─ source-status-summary/
├─ services/
│  ├─ shortform-director-profile.service.ts
│  ├─ shortform-director-research.service.ts
│  ├─ shortform-director-production.service.ts
│  └─ shortform-director-lineage.service.ts
└─ models/shortform-director-workspace.ts
```

각 Angular 컴포넌트 디렉토리에는 같은 이름의 `.ts/.html/.scss/.spec.ts` 네 파일을 둔다.

---

# Slice A — credential·계약·공급자 호출 경계

## Task A1: 기존 AI Director 크레딧 차감 제거와 무과금 인증 경계 고정

**Files — web API**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify:
  `web/clipper_web_api/src/modules/operations/domain/operation-definitions.ts`
- Modify:
  `web/clipper_web_api/src/modules/operations/domain/operation-definitions.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/operations/application/operations.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/operations/application/operations.service.spec.ts`
- Add:
  `web/clipper_web_api/src/core/database/migrations/admin/1785300000000-RetireShortformDirectorCreditPolicies.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-strategy/domain/shortform-director-strategy.contract.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-strategy/presentation/dto/generate-shortform-director-strategy.dto.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-strategy/presentation/shortform-director-strategy.controller.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-strategy/presentation/shortform-director-strategy.controller.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-strategy/shortform-director-strategy.module.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-video-plan/domain/shortform-director-video-plan.contract.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-video-plan/presentation/dto/generate-shortform-director-video-plan.dto.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-video-plan/presentation/shortform-director-video-plan.controller.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-video-plan/presentation/shortform-director-video-plan.controller.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-video-plan/shortform-director-video-plan.module.ts`

**Files — desktop Nest**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-content-strategy.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-video-plan.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-strategy-web-api.client.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-video-plan-web-api.client.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-content-strategy.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-video-plan.test.js`

**Files — desktop Angular**

- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.spec.ts`

**Contract**

```ts
interface GenerateDirectorProviderRequest {
  input: Record<string, unknown>;
  bearerToken: string;
}
```

AI Director의 기존 전략·영상 구성 endpoint와 이후 추가될 전용 endpoint는
`JwtAuthGuard`를 통과한 사용자만 호출할 수 있다. 하지만 request DTO, desktop client,
local manifest 어디에도 `operationRunId`를 두지 않으며, operations quote/start/succeed/
fail/refund를 호출하지 않는다.

- [ ] Angular 실패 테스트를 먼저 바꾼다. 전략 생성과 영상 구성 버튼은
  `OperationChargeGuardService.confirm()` 없이 즉시 각 project service를 호출해야 한다.
- [ ] desktop Nest 실패 테스트를 먼저 바꾼다. 두 application service는 JWT 부재를
  계속 거부하지만 `WebApiOperationRunService`를 주입하거나 start/succeed/fail하지 않고
  bearer token과 input만 web client에 전달해야 한다.
- [ ] web API controller 실패 테스트를 먼저 바꾼다:
  - JWT 없는 요청은 거부
  - `{input}`만 있는 인증 요청은 성공
  - whitelist 후 `operationRunId`가 provider service로 전달되지 않음
  - `OperationsService.authorizeProviderUse()`를 호출하지 않음
- [ ] operations 실패 테스트를 먼저 바꾼다:
  - active definition에 `shortform_director.strategy`와
    `shortform_director.video_plan`이 없음
  - DB에 예전 policy row가 남아 있어도 list/quote/start/update 대상이 되지 않음
  - 다른 plugin operation은 종전과 동일하게 동작
- [ ] RED를 확인한다.

```bash
# desktop Angular
npm test -- --watch=false

# desktop Nest
npm run build
node --test test/shortform-director-content-strategy.test.js
node --test test/shortform-director-video-plan.test.js

# web API
npm test -- --runInBand \
  src/modules/operations/domain/operation-definitions.spec.ts \
  src/modules/operations/application/operations.service.spec.ts \
  src/modules/shortform-director-strategy \
  src/modules/shortform-director-video-plan
```

- [ ] Angular page에서 AI Director operation key 상수, charge guard 주입, 확인 modal
  분기를 제거한다. 공유 `OperationChargeGuardService` 자체와 다른 plugin 사용처는
  수정하지 않는다.
- [ ] desktop Nest 두 service/client에서 operation run 필드와 성공/실패 환불 조정을
  제거하고, `ShortformDirectorModule`이 다른 이유로 쓰지 않는
  `OperationsModule` import도 제거한다.
- [ ] web API DTO/controller/module에서 operation run과 `OperationsModule` 의존을
  제거한다. controller는 JWT와 endpoint 고정 input contract만 책임지고 credential은
  기존 provider credential service 내부에서만 해석한다.
- [ ] `OPERATION_DEFINITIONS`에서 두 AI Director key를 제거한다.
  `OperationsService`는 active definition catalog에 없는 stale DB policy를 admin
  list/quote/start/update에서 제외한다. 과거 ledger/run 조회와 다른 operation은
  유지한다.
- [ ] migration은 참조 run이 없는 두 policy row만 삭제한다. 과거 run이 참조하는 row는
  이력을 위해 남기되 active catalog 밖이라 새 차감이나 정책 화면 노출이 불가능해야
  한다. 이력 보존을 위해 operation run/ledger를 삭제하지 않는다.
- [ ] OpenAPI의 기존 AI Director request required 목록에서 `operationRunId`를 제거하고,
  이 endpoint가 인증은 필요하지만 크레딧을 차감하지 않는다고 명시한다.
- [ ] 세 저장소 build와 관련 테스트를 통과시킨다.
- [ ] Commits:
  - web API:
    `refactor(shortform-director): remove credit operations from provider calls`
  - desktop Nest:
    `refactor(shortform-director): stop creating billable operation runs`
  - desktop Angular:
    `refactor(shortform-director): remove credit confirmation`

## Task A2: YouTube Data credential을 기존 관리자 키 관리에 추가

**Files — web API**

- Modify: `src/modules/provider-credentials/domain/provider-credential.model.ts`
- Add: `src/modules/provider-credentials/application/youtube-credential.service.ts`
- Add: `src/modules/provider-credentials/application/youtube-credential.service.spec.ts`
- Modify: `src/modules/provider-credentials/provider-credentials.module.ts`
- Modify: `src/modules/api-keys/application/api-keys.service.ts`
- Modify: `src/modules/api-keys/application/api-keys.service.spec.ts`
- Modify: `src/modules/api-keys/presentation/dto/create-api-key.dto.ts`
- Modify: `src/modules/api-keys/presentation/api-keys.controller.ts`
- Modify: `src/modules/api-keys/presentation/api-keys.controller.spec.ts`
- Modify: `docs/api/openapi.yaml`

**Files — web admin**

- Modify: `src/app/core/api/models.ts`
- Modify: `src/app/core/api/api-keys-api.service.ts`
- Modify: `src/app/core/api/api-keys-api.service.spec.ts`
- Modify: `src/app/core/api/mock/mock-api.interceptor.ts`
- Modify: `src/app/core/api/mock/mock-data.ts`
- Modify: `src/app/features/portal/api-keys/api-keys.types.ts`
- Modify: `src/app/features/portal/api-keys/api-keys.view-model.ts`
- Modify: `src/app/features/portal/api-keys/api-keys.view-model.spec.ts`
- Modify: `src/app/features/portal/api-keys/api-keys.component.ts`
- Modify: `src/app/features/portal/api-keys/api-keys.component.html`
- Modify: `src/app/features/portal/api-keys/api-keys.component.scss`
- Modify: `src/app/features/portal/api-keys/api-keys.component.spec.ts`
- Modify:
  `src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.ts`
- Modify:
  `src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.html`
- Modify:
  `src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.spec.ts`
- Add:
  `src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.ts`
- Add:
  `src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.html`
- Add:
  `src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.scss`
- Add:
  `src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.spec.ts`
- Add:
  `src/app/features/portal/api-keys/services/manual-provider-credential.facade.ts`
- Add:
  `src/app/features/portal/api-keys/services/manual-provider-credential.facade.spec.ts`

**Interfaces**

```ts
export type ProviderCredentialProvider =
  | 'openai'
  | 'naver'
  | 'gemini'
  | 'youtube';

export interface YoutubeResolvedCredential {
  apiKey: string;
  source: 'database';
  providerCredentialId: string;
}
```

관리자 API:

- `GET /admin/api-keys/providers/youtube/runtime-status`
- `POST /admin/api-keys/:id/test`
  - YouTube key이면 `i18nRegions.list` 한 건으로 연결을 확인한다.
- 목록/생성/수정/활성화/삭제는 기존 generic provider credential route를 그대로 쓴다.

- [ ] OpenAPI `ApiKeyProvider`를 `naver|openai|gemini|youtube`로 고치고
  `ApiKeySource`를 실제 구현과 같은 `database` 하나로 제한한다.
- [ ] web API 실패 테스트를 먼저 추가한다: YouTube 생성, 첫 key 자동 활성, 형제 key
  수동 전환, masked tail, runtime status, 테스트 요청, 다른 provider ID 거부.
- [ ] YouTube key 원문이 list/runtime/test JSON에 한 번도 나타나지 않는 직렬화 테스트를
  추가한다.
- [ ] RED 확인:

```bash
npm test -- --runInBand src/modules/provider-credentials/application/youtube-credential.service.spec.ts
npm test -- --runInBand src/modules/api-keys
```

- [ ] `YoutubeCredentialService`를 `GoogleAiCredentialService`와 같은 DB-only 패턴으로
  구현한다. `YOUTUBE_API_KEY` env fallback은 만들지 않는다.
- [ ] `ApiKeysService`의 Gemini 전용 label/error 분기를
  `providerDisplayName(provider)` helper로 좁게 일반화한다. OpenAI 단일-key 규칙과
  Naver rotation 규칙은 바꾸지 않는다.
- [ ] `ApiKeysController`에 runtime status와 test dispatch를 추가한다.
- [ ] DB `provider` column이 varchar이고 generic index를 쓰므로 schema migration은
  추가하지 않는다.
- [ ] admin 서비스/model 테스트를 먼저 RED로 만들고 YouTube section을 추가한다.
  기존 `OpenAiKeyFormComponent`의 `providerLabel` 입력을 `YouTube`로 재사용하며
  컴포넌트 이름을 바꾸는 대규모 refactor는 하지 않는다.
- [ ] component test가 쓰는 mock interceptor/data에도 YouTube runtime·create·test
  fixture를 추가한다. mock 응답에도 key 원문을 넣지 않고 masked value만 둔다.
- [ ] 이미 큰 `ApiKeysComponent`에 Gemini 카드와 동일한 YouTube markup을 복사하지
  않는다. `ProviderCredentialSectionComponent`는 Gemini·YouTube의 header, runtime
  상태, masked-key table, 기존 credential form을 표시하고 semantic action event만
  내보내는 presentational component로 둔다. HTTP 호출·secret 암복호화·provider 분기
  orchestration은 넣지 않는다. `ManualProviderCredentialFacade`는 Gemini·YouTube의
  runtime·form·save 상태와 API 호출만 맡고 provider 인자를 받는 좁은 helper로
  공유한다. page는 전체 key 목록, 공용 test/confirm modal 조정과 facade event 연결만
  맡는다. Naver/OpenAI 흐름을 facade로 옮기는 범위 확장은 하지 않는다.
- [ ] YouTube 카드에서 상태·masked key·연결 확인·활성/대기/제외/삭제가 기존 Gemini와
  같은 규칙으로 동작하게 한다.
- [ ] 두 저장소 전체 build/test를 통과시킨다.

```bash
npm run build
npm test -- --runInBand src/modules/provider-credentials src/modules/api-keys
```

```bash
npm run build
npm test -- --watch=false
```

- [ ] Commits:
  - web API: `feat(api-keys): manage encrypted YouTube Data credentials`
  - web admin: `feat(api-keys): add YouTube credential controls`

## Task A3: Naver·YouTube 조사 gateway와 안전한 공개 audit 응답

**Files**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Add:
  `web/clipper_web_api/src/modules/api-keys/application/naver-credential-lease.service.ts`
- Add:
  `web/clipper_web_api/src/modules/api-keys/application/naver-credential-lease.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/application/search.service.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/api-keys.module.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/domain/provider-call-audit.contract.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/bounded-provider-fetch.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/bounded-provider-fetch.service.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.factory.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.factory.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/naver-research-provider.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/naver-research-provider.service.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/shortform-director-source-fetch.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/dto/fetch-shortform-director-source.dto.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/dto/test-naver-director-research.dto.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research.controller.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research.controller.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research-admin.controller.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research-admin.controller.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/shortform-director-research.module.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/models.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/api-keys-api.service.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/api-keys-api.service.spec.ts`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.types.ts`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.ts`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.spec.ts`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.ts`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.html`
- Modify:
  `web/clipper_web_admin/src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.spec.ts`

**Web contract**

```ts
type ResearchSource =
  | 'naver-news'
  | 'naver-web'
  | 'naver-blog'
  | 'naver-datalab'
  | 'youtube-search'
  | 'youtube-videos'
  | 'youtube-comments';

interface ProviderCallAuditV1 {
  schemaVersion: 'shortform-director-provider-call.v1';
  provider: 'naver' | 'youtube';
  providerCredentialId: string;
  request: {
    method: 'GET' | 'POST';
    canonicalUrl: string;
    query?: Record<string, string | number | boolean>;
    body?: unknown;
    redactedFields: string[];
  };
  response: {
    status: number | null;
    contentType: string | null;
    raw: unknown | null;
  };
  failure?: {
    kind:
      | 'provider_4xx'
      | 'provider_5xx'
      | 'timeout'
      | 'network_error'
      | 'response_too_large'
      | 'invalid_response';
    message: string;
  };
  latencyMs: number;
  collectedAt: string;
}

interface NaverDirectorResearchCredentialTestResult {
  provider: 'naver';
  capability: 'director-research';
  checks: Array<{
    source: 'naver-news' | 'naver-datalab';
    ok: boolean;
    status: number | null;
    errorCode?: string;
  }>;
}

interface ShortformDirectorProviderCallError {
  statusCode: 502 | 504;
  code: 'shortform_director_provider_call_failed';
  message: string;
  audit: ProviderCallAuditV1;
}
```

`POST /shortform-director/research/source-fetch` body:

```json
{
  "source": "youtube-search",
  "query": {
    "q": "검색어",
    "order": "viewCount",
    "publishedAfter": "RFC3339",
    "regionCode": "KR",
    "relevanceLanguage": "ko",
    "maxResults": 50
  }
}
```

- [ ] OpenAPI에 source별 discriminated request와 `ProviderCallAuditV1` 응답을 먼저 쓴다.
  arbitrary URL이나 arbitrary header를 받는 필드는 만들지 않는다. nested query도
  `whitelist:true`, `forbidNonWhitelisted:true`와 source별 concrete DTO로 검증한다.
  provider 4xx/5xx·invalid/too-large/network는 sanitized audit가 포함된 502, timeout은
  sanitized audit가 포함된 504이며 위의 고정 error shape를 사용한다. 응답 자체가
  없으면 `status/raw=null`로 기록하고 message는 credential을 포함하지 않는 고정
  사용자용 문구다.
- [ ] `NaverCredentialLeaseService` 테스트를 추가한다. 기존 rotation/cipher를 재사용해
  `{keyId, clientId, clientSecret}`을 내부에만 빌리고 success/429를 현재 사용량·교체
  로직에 반영해야 한다.
- [ ] `ApiKeysModule`은 research module이 lease service만 주입받을 수 있게 해당
  service를 export한다. repository, cipher, secret 값 자체는 export하지 않는다.
- [ ] module 순환을 피하기 위해 기존
  `POST /admin/api-keys/:id/test`와 `ApiKeysController`는 그대로 둔다.
  `ShortformDirectorResearchModule`이 `OperatorJwtGuard`로 보호된
  `POST /admin/api-keys/:id/director-research-test`를 소유한다. 같은 지정 credential로
  News Search와 DataLab을 각각 검사해 위 summary를 반환하되 active pool을 바꾸거나
  Clipper credit operation을 호출하지 않는다. admin UI는 기존 media test와 새
  director-research test를 같은 modal의 명시적 capability 선택으로 분리 표시한다.
- [ ] 기존 이미지 `SearchService`가 lease service로 바뀐 뒤에도 동일한 결과·회전
  테스트를 통과하게 한다.
- [ ] Naver research provider 호출은 현재 read/update 기반 rotation의 lost-update를
  피하기 위해 web API 프로세스 안에서 직렬화한다. source-fetch API와 C2 coordinator의
  출처 독립성은 유지하되, multi-instance 원자성은 별도 repository transaction 후속
  과제로 validation report에 남긴다.
- [ ] 두 provider가 공유하는 bounded fetch와 audit/redaction을 위의 작은 adapter와
  factory로 분리한다. timeout은 body read/parse 완료까지 8초, 최대 response bytes는
  4 MiB로 고정한다. `Content-Length`와 실제 stream 누적 byte를 모두 검사하고 exact
  secret·URL encoded secret·민감 key 이름을 public audit/error/logger에서 제거한다.
- [ ] Naver provider 실패 테스트:
  - 뉴스/웹/블로그 endpoint와 `sort=date|sim`, `display`, `start` allowlist
  - DataLab `startDate`, `endDate`, `timeUnit`, 5개 이하 keywordGroups
  - Client ID/Secret이 audit JSON에 없음
  - 429 한 번만 rotation 재시도
- [ ] YouTube provider 실패 테스트:
  - `search.list`는 `viewCount|relevance`만 허용하고 `date` 거부
  - `publishedAfter`, `regionCode=KR`, `relevanceLanguage=ko`, `type=video`
  - `videos.list`는 `videoIds` 1~50개
  - `commentThreads.list`는 단일 `videoId`와 `maxResults` 1~100만 허용
    (여러 영상 fan-out은 C2 coordinator가 source-fetch를 여러 번 호출)
  - query의 `key`와 실제 API key가 audit JSON에 없음
- [ ] controller 테스트에서 JWT를 필수로 하고, 인증된 요청이라도 source별 고정
  allowlist 밖의 URL·method·query를 선택할 수 없음을 확인한다. operation run이나
  credit policy는 호출하지 않는다.
- [ ] RED 확인 후 provider/gateway를 구현한다.

```bash
npm test -- --runInBand src/modules/api-keys/application/naver-credential-lease.service.spec.ts
npm test -- --runInBand src/modules/shortform-director-research
```

- [ ] timeout, max response bytes, invalid response, provider 4xx/5xx를 구분하고 원본
  오류도 credential 제거 후 audit에 담는다. 실패를 빈 성공 응답으로 바꾸지 않는다.
- [ ] build와 전체 관련 회귀 테스트를 통과시킨다.
- [ ] Commits:
  - web API:
    `feat(shortform-director): proxy audited Naver and YouTube research calls`
  - web admin:
    `feat(api-keys): add Director research credential checks`

## Task A4: 역할별 모델 allowlist와 audit 가능한 inference gateway

**Files**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-model-catalog.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.transport.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.input-guard.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.input-guard.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.redactor.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.redactor.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/google-shortform-director-inference.transport.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/google-shortform-director-inference.transport.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/dto/run-shortform-director-inference.dto.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/shortform-director-inference.module.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`

**Model catalog**

```ts
export type InferencePurpose =
  | 'query-plan'
  | 'source-normalization'
  | 'youtube-reference-analysis'
  | 'topic-synthesis'
  | 'candidate-generation'
  | 'video-plan'
  | 'scene-media-decision'
  | 'quality-review';

export type ModelProfile =
  | 'default'
  | 'cost-comparison'
  | 'quality-comparison'
  | 'baseline';
```

아래 표는 모든 32개 조합의 총함수다. `—`는 fallback 없이 HTTP 400
`SHORTFORM_DIRECTOR_INFERENCE_PROFILE_NOT_ALLOWED`다. provider는 model 문자열에서
추론하지 않고 catalog entry에 명시한다.

| purpose | default | cost-comparison | quality-comparison | baseline |
|---|---|---|---|---|
| `query-plan` | OpenAI `gpt-5.4-nano` | OpenAI `gpt-5.4-mini` | — | — |
| `source-normalization` | OpenAI `gpt-5.4-nano` | OpenAI `gpt-5.4-mini` | — | — |
| `youtube-reference-analysis` | Google `gemini-3.6-flash` | — | — | — |
| `topic-synthesis` | OpenAI `gpt-5.6-luna` | OpenAI `gpt-5.4-mini` | Google `gemini-3.6-flash` | OpenAI `gpt-4.1` |
| `candidate-generation` | OpenAI `gpt-5.6-luna` | OpenAI `gpt-5.4-mini` | Google `gemini-3.6-flash` | OpenAI `gpt-4.1` |
| `video-plan` | OpenAI `gpt-5.6-luna` | OpenAI `gpt-5.4-mini` | Google `gemini-3.6-flash` | OpenAI `gpt-4.1` |
| `scene-media-decision` | OpenAI `gpt-5.6-luna` | OpenAI `gpt-5.4-mini` | Google `gemini-3.6-flash` | OpenAI `gpt-4.1` |
| `quality-review` | Google `gemini-3.6-flash` | — | — | — |

**서버 소유 출력 계약**

각 purpose spec은 `promptTemplateVersion`, `systemPrompt`, strict
`responseSchema`, 로컬 `validateOutput`을 모두 가진다. registry는
`satisfies Record<InferencePurpose, InferencePurposeSpec>`로 누락을 compile error로
막는다. 이 task에서는 새 JSON Schema dependency를 추가하지 않고 목적별 작은 수동
validator를 둔다. 모든 object schema는 `additionalProperties:false`이고, provider가
schema를 받았다는 사실과 별개로 응답을 로컬에서 다시 검증한다.

| purpose | output의 필수 top-level과 item 필드 |
|---|---|
| `query-plan` | `queries[]`: `source`, `query`, `rationale` |
| `source-normalization` | `items[]`: `sourceItemId`, `title`, `summary`, `publishedAt|null`, `relatedQueries[]`, `entityNames[]`, `claims[]` |
| `youtube-reference-analysis` | `videos[]`: `videoId`, `summary`, `topicSignals[]`, `audienceSignals[]`, `referencePatterns[]` |
| `topic-synthesis` | `topics[]`: `title`, `whyNow`, `angle`, `evidenceIds[]`, `audienceSignalIds[]`, `referencePatternIds[]` |
| `candidate-generation` | `candidates[]`: `title`, `hook`, `promise`, `whyNow`, `outline[]`, `format`, `targetDurationSeconds`, `evidenceIds[]`, `audienceSignalIds[]`, `referencePatternIds[]` |
| `video-plan` | `title`, `targetDurationSeconds`, `scenes[]`: `narration`, `onScreenText`, `claim`, `evidenceIds[]`, `durationSeconds` |
| `scene-media-decision` | `decisions[]`: `sceneIndex`, `medium`, `rationale`, `factualRisk`, `evidenceIds[]`, `productionSourceIds[]`, optional `generationBrief`/`programmaticBrief`, `fallbackMedium` |
| `quality-review` | `summary`, `score`, `findings[]`: `severity`, `category`, optional `sceneIndex`, `message`, `evidenceIds[]` |

이 출력은 provider draft다. desktop이 local run ID, entity ID, `generatedByCallId`와
결정적 validation 결과를 붙여 최종 도메인 snapshot으로 만든다. array/string/number
상한과 enum은 schema와 validator 양쪽에 같은 값으로 둔다.

이번 A4 JSON route는 text/JSON input 전용이다.
`youtube-reference-analysis`는 수집한 metadata·transcript·comments를 입력으로 받고,
`quality-review`는 기술 검사·scene/evidence 요약을 입력으로 받는다. local path,
base64 media, 임의 URL을 받지 않는다. 완성 MP4를 실제로 보는 multimodal review는
F3에서 인증된 bounded media-upload endpoint와 Gemini file lifecycle을 별도 계약으로
추가한다.

응답은 생성 payload만 반환하지 않고 다음 공개 audit를 함께 반환한다.

```ts
interface InferenceResultV1 {
  schemaVersion: 'shortform-director-inference-result.v1';
  output: unknown;
  audit: {
    provider: 'openai' | 'google';
    model: string;
    promptTemplateVersion: string;
    request: {
      systemPrompt: string;
      userPrompt: string;
      responseSchema: object;
      options: Record<string, unknown>;
    };
    response: {
      status: number | null;
      providerRequestId?: string;
      raw: unknown | null;
      text?: string;
      parsed?: unknown;
      validation?: {
        passed: boolean;
        issues: Array<{ path: string; keyword: string }>;
      };
    };
    usage?: {
      inputTokens?: number;
      outputTokens?: number;
      reasoningTokens?: number;
    };
    latencyMs: number;
    createdAt: string;
  };
}
```

실패는 성공 body로 꾸미지 않는다.

```ts
interface InferenceRequestFailureV1 {
  statusCode: 400;
  error: 'Bad Request';
  message: string;
  code:
    | 'SHORTFORM_DIRECTOR_INFERENCE_PROFILE_NOT_ALLOWED'
    | 'SHORTFORM_DIRECTOR_INFERENCE_INPUT_INVALID'
    | 'SHORTFORM_DIRECTOR_INFERENCE_INPUT_TOO_LARGE';
}

interface InferenceFailureV1 {
  statusCode: 502 | 503 | 504;
  error: 'Bad Gateway' | 'Service Unavailable' | 'Gateway Timeout';
  message: string;
  code:
    | 'SHORTFORM_DIRECTOR_INFERENCE_CREDENTIAL_UNAVAILABLE'
    | 'SHORTFORM_DIRECTOR_INFERENCE_PROVIDER_TIMEOUT'
    | 'SHORTFORM_DIRECTOR_INFERENCE_PROVIDER_HTTP_ERROR'
    | 'SHORTFORM_DIRECTOR_INFERENCE_PROVIDER_RESPONSE_INVALID'
    | 'SHORTFORM_DIRECTOR_INFERENCE_OUTPUT_JSON_INVALID'
    | 'SHORTFORM_DIRECTOR_INFERENCE_OUTPUT_SCHEMA_INVALID';
  audit: InferenceResultV1['audit'];
}
```

- [ ] OpenAPI에 `purpose`, `modelProfile`, bounded `input`,
  `InferenceResultV1`, `InferenceRequestFailureV1`, `InferenceFailureV1`과
  201/400/401/502/503/504를 먼저 정의하고 YAML parse contract test를 쓴다.
  provider 응답이 없으면 audit의 `response.status/raw`는 `null`이고 validation은
  생략한다.
- [ ] 입력에서 공급자명·model ID·system prompt·response schema를 임의로 받지 않는
  strict controller 테스트를 쓴다. 클라이언트는 allowlist의 `modelProfile`만
  선택한다. `input`은 credential 조회 전에 UTF-8 256 KiB, depth 16, node 10,000,
  object property 200, array item 500, string 64 KiB, key 128자로 제한하고
  prototype/credential-like key를 거부한다.
- [ ] purpose별 credential·model allowlist 매핑 테스트를 쓴다:
  - 위 32개 조합의 exact provider/model 또는 exact 400 code
  - OpenAI entry → `OpenAiCredentialService`, Google entry →
    `GoogleAiCredentialService`
  - 둘 다 active DB credential만 사용하고 env/standby fallback 없음
  - 저장 provider `gemini`를 공개 audit `google`로 명시 변환
  - 어떤 purpose도 operation quote/start/authorize/complete를 호출하지 않음
- [ ] provider별 transport를 orchestration service에서 분리하고 fake fetch로 exact
  endpoint/model/schema, OpenAI `store:false`, Gemini `generateContent`, 180초 timeout,
  4 MiB response limit, usage/provider request ID 추출을 검증한다. 자동 retry/repair는
  하지 않는다.
- [ ] provider raw 응답의 nested object/array/header/URL/Bearer 및 실제 호출에 사용한
  exact·URL-encoded credential을 fail-closed deep redactor가 제거하는 테스트를 쓴다.
- [ ] RED 확인:

```bash
npm test -- --runInBand src/modules/shortform-director-inference
```

- [ ] OpenAI/Gemini transport를 구현하되 credential은 각각 기존
  `OpenAiCredentialService`/`GoogleAiCredentialService`에서만 얻는다.
- [ ] JSON parse/schema/provider/timeout 실패는 고정된 비민감 message와 redacted raw
  response를 유지한 `InferenceFailureV1`로 변환하고, desktop이 새 attempt를 만들 수
  있는 안정 오류 code를 반환한다. controller/logger는 prompt, input, raw audit를
  기록하지 않고 `Cache-Control:no-store`를 반환한다.
- [ ] 기존 `content-strategy`와 `video-plan` route는 과거 프로젝트 호환을 위해
  제거하지 않는다.
- [ ] 전체 build/test를 통과시킨다.
- [ ] Commit:
  `feat(shortform-director): add allowlisted audited inference gateway`

---

# Slice B — 로컬 JSON 기반·프로필·서브 페이지 뼈대

## Task B1: 원자 JSON 저장소, artifact registry, run manifest

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/run-record.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/lineage.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director-run.repository.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/atomic-shortform-director-json.store.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-run.repository.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-artifact.registry.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-run-recovery.service.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-run-storage.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-artifact-security.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

**Core contract**

```ts
export interface LocalRunManifestV1 {
  schemaVersion: 'shortform-director-run-manifest.v1';
  id: string;
  kind:
    | 'research'
    | 'candidate-generation'
    | 'video-plan'
    | 'media'
    | 'render'
    | 'quality-report';
  ownerSubjectId: string;
  profileId: string;
  projectId?: string;
  status: 'running' | 'partial' | 'succeeded' | 'failed' | 'cancelled';
  startedAt: string;
  finishedAt?: string;
  inputRefs: string[];
  outputRefs: string[];
  failureRefs: string[];
  childRunIds: string[];
}
```

- [ ] 실패 테스트를 먼저 쓴다:
  - mutable JSON은 same-directory temp→file sync→rename→directory sync이고 중간
    파일을 읽지 않음
  - immutable artifact는 temp sync→hard-link no-replace publish로 완성본만
    원자 노출하고 같은 ID의 두 번째 write는 byte가 같아도 거부
  - read→validate→update→write 전체를 path별 shared queue로 직렬화해 concurrent
    index/ref update가 한 프로세스 안에서 유실되지 않음
  - 재시도 attempt가 이전 JSON checksum을 바꾸지 않음
  - producer가 만든 공개 DTO만 받고 registry persistence guard가 nested/raw/
    URL-encoded secret을 write 전에 fail closed하며 data root 전체에 secret이 없음
  - `../`, 절대 경로, symlink escape, 다른 owner artifact ID 조회 거부
  - parse/schema/checksum 손상을 missing/empty store로 바꾸지 않음
  - startup recovery가 `running`만 `failed`로 바꾸고
    `process_interrupted` failure artifact를 먼저 추가하며 두 번 실행해도 중복 없음
  - `partial|succeeded|failed|cancelled`는 terminal이고 recovery가 바꾸지 않음
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-run-storage.test.js
node --test test/shortform-director-artifact-security.test.js
```

- [ ] store root를 생성자에서 한 번
  `<CLIPPER_DATA_DIR>/shortform-director`로 고정하고 caller가 경로 문자열을 직접 넘기지
  않게 한다. ENOENT만 missing으로 처리한다.
- [ ] store의 public location은 path 문자열이 아니라 discriminated typed location이다.
  B2가 같은 singleton을 재사용할 수 있게 run/artifact 위치와 함께
  `{kind:'profile-index'}` 및 strict opaque ID를 받는
  `{kind:'profile-detail', profileId}`를 정의한다. profile schema/owner/name 규칙은
  B1 store가 알지 않는다.
- [ ] mutable JSON primitive는 `readMutableJson`, create-no-replace,
  atomic replace, `updateMutableJson`을 제공한다. 마지막 operation은
  read→parse/validate→update→write 전체를 같은 path queue에서 직렬화한다.
- [ ] reconciliation용
  `listMutableJsonIds({kind:'profile-detail-family'})`는 strict profile ID에 해당하는
  regular final file의 opaque ID만 반환한다. raw/relative/absolute path는 반환하지
  않고 `.tmp-*`, malformed filename, directory, symlink는 제외한다. caller는 각 ID를
  typed location으로 다시 읽고 자기 schema를 검증한다.
- [ ] 책임을 나눈다: atomic store는 typed location·serialize·sync·publish·path lock,
  artifact registry는 immutable payload/descriptor/checksum/owner/entity index,
  run repository는 manifest/run index와 상태 전환, recovery service는 startup
  reconciliation만 담당한다.
- [ ] artifact ID는 opaque random identity이고 checksum은 실제 serialized payload
  bytes의 SHA-256이다. descriptor/payload가 SoT이고 index는 재구축 가능한
  projection이다.
- [ ] publish 순서를 payload→descriptor→artifact index→manifest→run index로
  고정한다. owner-scoped API만 공개하고 unknown/cross-owner는 같은 404로 처리한다.
- [ ] 시작 시 남아 있는 `running` manifest는 기존 artifact를 지우지 않고 새
  `process_interrupted` failure artifact를 먼저 추가한 뒤 `failed`와 `finishedAt`으로
  전환한다. `interrupted` status는 추가하지 않는다.
- [ ] POSIX는 file/directory sync 오류를 숨기지 않는다. directory sync가
  `EPERM|EINVAL|ENOTSUP`인 Windows만 문서화된 best-effort로 허용하고, hard link를
  지원하지 않는 filesystem은 조용히 direct-write로 낮추지 않고 storage error를
  반환한다.
- [ ] build/test를 통과시킨다.
- [ ] Commit:
  `feat(shortform-director): persist immutable local runs and lineage artifacts`

## Task B2: 운영 프로필 CRUD와 soft delete

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/operating-profile.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director-profile.repository.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/json-shortform-director-profile.repository.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-profile.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/create-shortform-director-profile.dto.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-profile.dto.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-profile.controller.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-profile-api.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-profile-storage.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

**Profile**

```ts
export interface OperatingProfileV1 {
  schemaVersion: 'shortform-director-operating-profile.v1';
  id: string;
  ownerSubjectId: string;
  name: string;
  domain: string;
  targetAudience: string;
  objective: string;
  toneKeywords: string[];
  requiredFacts: string[];
  prohibitedExpressions: string[];
  region: 'KR';
  language: 'ko';
  defaultTargetDurationSec: 15 | 30 | 45 | 60;
  status: 'active' | 'archived';
  createdAt: string;
  updatedAt: string;
  archivedAt?: string;
}
```

Endpoints:

- `GET/POST /projects/shortform-director/profiles`
- `GET/PATCH/DELETE /projects/shortform-director/profiles/:profileId`
- `POST /projects/shortform-director/profiles/:profileId/duplicate`

- [ ] 선행 조건으로 B1 shared atomic store singleton과 profile index/detail typed
  location/create/update primitive가 구현돼 있어야 한다. profile repository는 그
  singleton만 주입받고 자체 `ConfigService`, `fs`, data root, raw path queue를 만들지
  않는다.
- [ ] owner 격리와 profile 입력 계약 실패 테스트를 먼저 쓴다:
  - 필수 `name` 1..120, `domain` 1..200, `targetAudience/objective` 1..500
  - optional `toneKeywords` 20×80, `requiredFacts` 30×500,
    `prohibitedExpressions` 30×300; 기본 `[]`, trim 뒤 빈 값/정규화 중복 거부
  - `region='KR'`, `language='ko'`, duration 기본 30과 `15|30|45|60`
  - DTO와 framework-independent domain normalizer/parser가 같은 불변성을 검증
  - 빈 PATCH/null/불변 필드 덮어쓰기 거부
- [ ] 같은 owner의 active profile 이름은
  `NFKC→trim→whitespace collapse→ko-KR case-fold` key로 unique다. create/rename
  충돌은 stable 409, 다른 owner와 archived 이름은 active uniqueness를 점유하지
  않는다. name check→detail→index와 reconciliation을 repository-wide profile
  catalog queue에서 직렬화해 scan/replace와 모든 profile mutation이 겹치지 않게 한다.
- [ ] CRUD/상태 테스트를 먼저 쓴다:
  - list는 active만, exact GET은 active/archived 모두
  - DELETE는 detail을 남기는 active→archived이며 반복 호출은 동일
    `archivedAt/updatedAt`을 보존
  - archived PATCH/start는 stable 409, archived duplicate는 허용
  - duplicate는 새 ID/timestamp/active status/deep-copied content와
    `<name> 복사본`, `<name> 복사본 2`의 첫 충돌 없는 이름을 사용
  - malformed/unknown/cross-owner는 동일 404
- [ ] B2 domain/service는 active 여부 확인과 detached
  `OperatingProfileSnapshotV1` 생성을 owner lock 안에서 한 번에 수행하는
  `captureActiveForRun`을 제공한다. snapshot은 `sourceProfileUpdatedAt`,
  `capturedAt`과 workflow 입력의 deep copy이며 artifact/manifest를 직접 만들지
  않는다.
- [ ] RED 확인 후 repository/service/controller를 구현한다.
- [ ] `profiles/<profileId>.json` detail이 SoT, `profiles/index.json`은 archived entry도
  보존하는 rebuild 가능한 projection이다. create/duplicate/patch/archive는 detail을
  먼저 durable하게 만든 뒤 index를 갱신하며 index membership 전에는 operation을
  성공으로 반환하거나 public get/list에 노출하지 않는다. public get/list 모두 index
  membership 뒤 detail의 owner/status/schema를 재검증한다.
- [ ] index publish 실패는 durable orphan detail을 지우거나 성공으로 꾸미지 않고
  repository를 dirty로 표시한다. 같은 process의 다음 public read/mutation 전과
  startup/첫 load에 catalog queue 안에서 single reconciliation barrier를 완료한다.
  B1의 typed detail-ID enumeration으로 strict valid detail만 scan해 index를 replace하고,
  corrupt는 missing/empty로 바꾸지 않는다. reconciliation 실패 중에는 profile
  operation도 fail closed한다.
- [ ] public response는 allowlist mapper로 owner/index/path metadata를 제외한다. 기존
  `projects.json`은 모든 CRUD/reconcile 동안 read/write 0건이고 bytes/size/mtime/inode가
  그대로인지, error에도 local data root/path가 없는지 검증한다.
- [ ] abstract repository=`useExisting` concrete, B1 store singleton 공유를 Nest app
  context test로 확인한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): add local operating profile CRUD`

## Task B3: 플러그인 내부 6개 route와 프로필 UX

**Files**

- Modify: `desktop/clipper_angular/src/app/app.routes.ts`
- Modify: `desktop/clipper_angular/src/app/app.config.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/shortform-director-registration.spec.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-workspace.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-profile.service.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-profile.service.spec.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-profile.gateway.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/director-sidebar/director-sidebar.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-form/operating-profile-form.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-list/operating-profile-list.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/operating-profile-card/operating-profile-card.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/director-empty-state/director-empty-state.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/pages/profiles-page/profiles-page.component.{ts,html,scss,spec.ts}`
- Add empty-state-capable 4-file components:
  - `pages/ideas-page/ideas-page.component.*`
  - `pages/candidates-page/candidates-page.component.*`
  - `pages/production-page/production-page.component.*`
  - `pages/outputs-page/outputs-page.component.*`
  - `pages/runs-page/runs-page.component.*`

**Routes**

```text
/shortform/director/profiles
/shortform/director/ideas
/shortform/director/candidates
/shortform/director/production
/shortform/director/outputs
/shortform/director/runs
```

`/shortform/director`는 `/shortform/director/profiles`로 redirect한다. 선택 context는 query
param의 opaque ID만 사용한다.

- [ ] B2 profile API가 먼저 완료돼야 한다. production
  `ShortformDirectorProfileService`는 BackendLocator+HttpClient만 사용하는
  `ShortformDirectorProfileGateway` adapter이며 runtime fixture/localStorage/404
  fallback을 두지 않는다. tests만 같은 interface의 작은 fake를 주입한다.
- [ ] route/registration 실패 테스트를 먼저 수정한다. 상위 plugin guard/data는 shell에
  한 번만 있고 child가 상속해야 한다. `app.routes.ts`와 `app.config.ts`의 pipeline
  loader가 모두 새 shell을 가리키며 구 page는 G1까지 source에만 보존한다.
- [ ] sidebar active 상태, keyboard focus, 작은 viewport, 각 route navigation 테스트를
  먼저 쓴다.
- [ ] shell만 `<app-page scroll="fit">`을 한 번 소유하고 child page는 outlet
  `<section>`만 렌더한다. wide는 sidebar+content, 640px에서는 text가 남는 horizontal
  nav이며 nested `100vh`, 이중 main/scroll, 고정 min-width를 만들지 않는다.
- [ ] 프로필 페이지 테스트:
  - 기본 폼은 이름·분야·대상·목적만 먼저 보임
  - 고급 설정을 펼쳐 tone/required/prohibited 수정
  - 생성·수정·복제·보관
  - 로딩/빈 목록/실패/저장 중 중복 클릭 방지
  - `새 영상 시작`은 프로필 선택 후
    `/ideas?profileId=<selectedProfileId>&start=1`로 이동
- [ ] profile page는 load/use-case/navigation/confirm만 조정하고 form/list/card는
  presentational input/output으로 분리한다. 필수 네 값만 기본 노출하고 advanced는
  기본 collapsed다. 후속 다섯 page는 공용 empty-state에 이전 단계 action 하나만
  전달하며 실존 브랜드·keyword나 fake 결과 카드를 만들지 않는다.
- [ ] query context는 bounded opaque string으로 다루고 UUID/path로 해석하지 않는다.
  `start=1`은 조사 입력 화면을 열라는 intent일 뿐 page init/refresh에서 research
  POST를 자동 실행하지 않는다.
- [ ] RED 확인:

```bash
npm test -- --watch=false
```

- [ ] shell/sidebar/profile API 연결을 구현한다. 나머지 페이지는 가짜 카드가 아니라
  실제 실행이 없다는 empty state와 필요한 이전 단계 이동 버튼만 표시한다.
- [ ] 기존 거대 page는 아직 삭제하지 않되 route에서 분리한다. 기존 project service와
  production 로직은 Slice E까지 재사용할 수 있게 보존한다.
- [ ] Material semantic token과 `<app-page>` 규약을 확인한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): add guided subpages and profile workflow`

---

# Slice C — 실제 최신 조사·주제·근거 UI

## Task C1: Google Trends RSS와 공식 CSV parser

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/google-trends-trending.client.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-source-response.redactor.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director-sensitive-string.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/research.ts`
- Add:
  `desktop/clipper_nestjs/test/fixtures/shortform-director/google-trends-trending-rss.xml`
- Add:
  `desktop/clipper_nestjs/test/fixtures/shortform-director/google-trends-trending-export.en.csv`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-google-trends.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-sensitive-string.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-artifact-persistence.guard.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-public-artifact.validator.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-run-storage.test.js`
- Modify:
  `desktop/clipper_nestjs/package.json`
- Modify:
  `desktop/clipper_nestjs/package-lock.json`

**Interfaces**

```ts
export type GoogleTrendsWindow = '4h' | '24h' | '48h' | '7d';

export const GOOGLE_TRENDS_HOURS: Readonly<Record<GoogleTrendsWindow, number>> = {
  '4h': 4,
  '24h': 24,
  '48h': 48,
  '7d': 168,
};

export interface FetchGoogleTrendsRssInput {
  researchRunId: string;
  window: GoogleTrendsWindow;
  asOf: string;
  attempt: number;
  signal?: AbortSignal;
}

export abstract class GoogleTrendsTrendingSource {
  abstract fetchRss(
    input: FetchGoogleTrendsRssInput,
  ): Promise<GoogleTrendsSourceFetchRecordV1>;
}

export interface GoogleTrendsParsedV1 {
  schemaVersion: 'google-trends-trending.v1';
  source: 'rss' | 'official-csv';
  window: GoogleTrendsWindow;
  asOf: string;
  items: GoogleTrendsTrendingItemV1[];
}

export interface GoogleTrendsTrendingItemV1 {
  title: string;
  searchVolume: {
    sourceText: string;
    lowerBound?: number;
  };
  publishedAtRaw?: string;
  publishedAt?: string;
  started?: {
    sourceText: string;
    at?: string;
  };
  ended?: {
    sourceText: string;
    at?: string;
  };
  activity: 'active' | 'ended' | 'unknown';
  relatedQueries: string[];
  newsItems: Array<{
    title: string;
    url: string;
    source?: string;
    snippet?: string;
    pictureUrl?: string;
  }>;
  growthRatePercent?: number;
}

export function parseOfficialCsv(
  csvText: string,
  input: { window: GoogleTrendsWindow; asOf: string },
): GoogleTrendsParsedV1;

export function parseSourceFetchRecordV1(
  value: unknown,
): SourceFetchRecordV1;
```

network source record는 승인 설계 §13.4의 exact-key union을 그대로 구현한다.

```ts
export type SourceFetchStoredBodyChecksum = `sha256:${string}`;
export type SourceFetchReceivedBodyChecksum = `sha256:${string}`;

export type SourceResponseRedactionKind =
  | 'auth-scheme'
  | 'key-material'
  | 'sensitive-query';

export interface SourceResponseRedactionSummaryV1 {
  kind: SourceResponseRedactionKind;
  count: number;
}

export const AUTHORIZATION_HEADER_PATTERN =
  /["']?\bauthorization\b["']?[ \t]*(?::|=)[ \t]*["']?(bearer|basic)[ \t]+([^\s,;}"']+)/dgi;
export const STANDALONE_BEARER_PATTERN =
  /\bbearer[ \t]+([A-Za-z0-9._~+/-]+={0,2})(?=$|[^A-Za-z0-9._~+/=-])/gi;
export const STANDALONE_BASIC_PATTERN =
  /\bbasic[ \t]+([A-Za-z0-9+/]+={0,2})(?=$|[^A-Za-z0-9+/=])/gi;

export const BEARER_PREFIX_MIN_LENGTH = {
  'ya29.': 16,
  AIza: 16,
  'sk-': 16,
  ghp_: 16,
  github_pat_: 24,
} as const;

export const SHARED_SENSITIVE_STRING_MAX_UTF8_BYTES = 5 * 1024 * 1024;
export const PRIVATE_KEY_PEM_LABEL_PATTERN =
  /^(?:[A-Z0-9]+ )?PRIVATE KEY$/;
export const PRIVATE_KEY_PEM_MAX_LABEL_CODE_UNITS = 64;
export const PRIVATE_KEY_PEM_BOUNDARY_LOOKAHEAD_CODE_UNITS = 96;
export const JWT_SEGMENT_PATTERN = /^[A-Za-z0-9_-]+$/;
export const JWT_MIN_SEGMENT_LENGTHS = [8, 8, 16] as const;
export const BEARER_PUNCTUATION_PATTERN = /[._~+/-]/;
export const OPAQUE_BEARER_WITH_PUNCTUATION_MIN_LENGTH = 24;
export const OPAQUE_BEARER_MIXED_CASE_MIN_LENGTH = 32;

export type SharedSensitiveStringKind =
  | 'known-sensitive-value'
  | 'authorization'
  | 'private-key'
  | 'credential-url';

export type SharedSensitiveStringInspectionV1 =
  | {
      redactionComplete: true;
      sensitive: boolean;
      kinds: SharedSensitiveStringKind[];
      redacted: string;
      failure?: never;
    }
  | {
      redactionComplete: false;
      sensitive: true;
      kinds: SharedSensitiveStringKind[];
      redacted?: never;
      failure: 'input-too-large' | 'private-key-boundary';
    };

export function inspectAndRedactShortformDirectorSensitiveString(
  value: string,
  sensitiveValues: readonly string[],
): SharedSensitiveStringInspectionV1;

export interface SourceFetchHttpRequestV1 {
  kind: 'http';
  method: string;
  canonicalUrl: string;
  query?: Record<string, unknown>;
  body?: unknown;
  redactedFields: string[];
}

export type SourceFetchContentTypeFieldsV1 =
  | {
      contentTypeRaw: string;
      mediaType: string;
    }
  | {
      contentTypeRaw?: never;
      mediaType?: never;
    };

export type SourceFetchReceivedMetadataV1 =
  SourceFetchContentTypeFieldsV1 & {
    status: number;
    bytesReceived: number;
  };

export type SourceFetchNoResponseV1 = {
  received: false;
  complete: false;
  bytesReceived: 0;
  status?: never;
  contentTypeRaw?: never;
  mediaType?: never;
  decoded?: never;
  redactionComplete?: never;
  bodyRetention?: never;
  receivedBodyChecksum?: never;
  rawBody?: never;
  rawBodyBase64?: never;
  storedBodyChecksum?: never;
  parsed?: never;
};

export type SourceFetchIncompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: false;
    decoded?: never;
    redactionComplete?: never;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

export type SourceFetchRetainedUndecodableCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: false;
    redactionComplete?: never;
    bodyRetention: 'retained';
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64: string;
    storedBodyChecksum: SourceFetchStoredBodyChecksum;
    parsed?: never;
  };

export type SourceFetchWithheldUndecodableCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: false;
    redactionComplete?: never;
    bodyRetention: 'withheld';
    receivedBodyChecksum: SourceFetchReceivedBodyChecksum;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

export type SourceFetchRedactionFailedResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: true;
    redactionComplete: false;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody?: never;
    rawBodyBase64?: never;
    storedBodyChecksum?: never;
    parsed?: never;
  };

export type SourceFetchStoredDecodedCompleteResponseV1 =
  SourceFetchReceivedMetadataV1 & {
    received: true;
    complete: true;
    decoded: true;
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    rawBody: string;
    rawBodyBase64?: never;
    storedBodyChecksum: SourceFetchStoredBodyChecksum;
  };

export type SourceFetchFailedStoredResponseV1 =
  SourceFetchStoredDecodedCompleteResponseV1 & {
    parsed?: never;
  };

export type SourceFetchSucceededResponseV1 =
  SourceFetchStoredDecodedCompleteResponseV1 & {
    parsed: unknown;
  };

export type SourceFetchFailedResponseV1 =
  | SourceFetchNoResponseV1
  | SourceFetchIncompleteResponseV1
  | SourceFetchRetainedUndecodableCompleteResponseV1
  | SourceFetchWithheldUndecodableCompleteResponseV1
  | SourceFetchRedactionFailedResponseV1
  | SourceFetchFailedStoredResponseV1;

export type SourceFetchResponseV1 =
  | SourceFetchFailedResponseV1
  | SourceFetchSucceededResponseV1;

export type SourceFetchErrorCategory =
  | 'cancelled'
  | 'timeout'
  | 'network'
  | 'redirect'
  | 'http'
  | 'content-type'
  | 'body-too-large'
  | 'decode'
  | 'parse'
  | 'validation'
  | 'provider';

export interface SourceFetchRecordBaseV1 {
  schemaVersion: 'shortform-director-source-fetch.v1';
  id: string;
  researchRunId: string;
  provider: string;
  purpose: string;
  asOf: string;
  window?: string;
  responseRedactions: SourceResponseRedactionSummaryV1[];
  request: SourceFetchHttpRequestV1;
  attempt: number;
  latencyMs: number;
  collectedAt: string;
}

export type SourceFetchSucceededRecordV1 = SourceFetchRecordBaseV1 & {
  status: 'succeeded';
  response: SourceFetchSucceededResponseV1;
  error?: never;
};

export type SourceFetchFailedRecordV1 = SourceFetchRecordBaseV1 & {
  status: 'failed';
  response: SourceFetchFailedResponseV1;
  error: {
    category: SourceFetchErrorCategory;
    message: string;
  };
};

export type SourceFetchRecordV1 =
  | SourceFetchSucceededRecordV1
  | SourceFetchFailedRecordV1;

export type GoogleTrendsSourceFetchRecordV1 =
  | (SourceFetchSucceededRecordV1 & {
      provider: 'google-trends';
      purpose: 'trending-rss';
      window: GoogleTrendsWindow;
      response: SourceFetchStoredDecodedCompleteResponseV1 & {
        parsed: GoogleTrendsParsedV1;
      };
    })
  | (SourceFetchFailedRecordV1 & {
      provider: 'google-trends';
      purpose: 'trending-rss';
      window: GoogleTrendsWindow;
    });
```

- top-level `asOf`는 research run 시작 때 한 번 동결한 UTC 시각이다. `collectedAt`은
  각 호출이 실제로 완료되거나 실패한 UTC 시각이다. `window`는 provider별 기간
  context라서 pre-response와 parse 실패에도 남고 item 나이에서 추론하지 않는다.
- `succeeded`는 `received:true`, `complete:true`, `decoded:true`,
  `redactionComplete:true`, 2xx safe-integer status, `parsed` 존재, `error` 부재인
  경우뿐이다. `failed`는 항상 `parsed` 금지, `error` 필수다.
- status는 존재하면 `100..599` safe integer, `bytesReceived`는 safe nonnegative
  integer다. `received:false`는 `complete:false`, `bytesReceived:0`이고
  status/content-type/body 필드가 없다.
- `contentTypeRaw`은 header 원문이고 `mediaType`은 parameter 제거 후
  trim/lowercase한 비교값이다. header가 없으면 둘 다 없고, 있으면 둘 다 있어야 한다.
- incomplete body에는 decoded/raw/checksum/parsed가 없다. complete bytes는 fatal
  UTF-8 decoder로 검사한다. credential-free Google Trends의 invalid UTF-8은
  `decoded:false`, `error.category:'decode'`, `bodyRetention:'retained'`, canonical
  padded RFC 4648 `rawBodyBase64`, `storedBodyChecksum`을 갖는다. base64 decode bytes
  길이는 `bytesReceived`와 같고 decode→re-encode가 원문과 정확히 같아야 한다.
- generic union에는 credentialed source용
  `bodyRetention:'withheld'`/`receivedBodyChecksum` undecodable branch도 둔다. 이
  branch는 raw/rawBodyBase64/storedBodyChecksum/parsed/redactionComplete가 모두
  없고 non-Google refinement만 허용한다. Google refinement는 retained branch만
  허용한다.
- valid UTF-8 body는 narrow deterministic response redactor가 decoded XML과 parsed
  DTO를 모두 정제한 뒤에만 `redactionComplete:true`, `rawBody`,
  `storedBodyChecksum`을 갖는다. redactor가 안전한 두 출력을 만들지 못하면
  `redactionComplete:false`, validation failed record를 반환하고 unsafe
  raw/base64/checksum/parsed를 저장하지 않는다.
- JSON media type의 valid UTF-8 malformed text는 safely redacted `rawBody`와 그
  `storedBodyChecksum`을 보존하지만 `parsed` 없이 parse failed다.
- `responseRedactions`는 중복 없는 `{kind,count}` 배열이다. kind는
  `auth-scheme|key-material|sensitive-query`, count는 positive safe integer이며 고정
  kind 순서다. 변환 없음/body 없음/redaction 실패는 빈 배열이다.
- decoded branch checksum은 실제 저장 `rawBody` UTF-8 bytes, retained
  `decoded:false` Google branch checksum은 저장된 canonical base64의 decoded bytes를
  해시한
  `sha256:<64 lowercase hex>`다. 저장값으로 검증할 수 없는 별도 wire checksum은
  만들지 않는다. withheld non-Google `receivedBodyChecksum`은 완전 수신 wire bytes의
  nonsecret fingerprint이며 저장 body checksum과 구분한다.
- B1 artifact descriptor checksum은 `SourceFetchRecordV1` wrapper JSON 전체
  직렬화 bytes checksum이므로 `storedBodyChecksum`과 별개다.
- strict `parseSourceFetchRecordV1`은 exact keys, UTC `asOf/collectedAt`, 1 이상의
  safe-integer `attempt`, 유한한 비음수 `latencyMs`, status/error/response 조합을
  fail closed한다.

generic failed matrix는 다음과 같다. 이후 provider는 이 범위를 넓히지 않고 자기
계약에 맞게 좁힌다.

| response 형태 | 허용 failed category |
|---|---|
| `received:false, complete:false` | `cancelled`, `timeout`, `network`, `redirect` |
| `received:true, complete:false` | `cancelled`, `timeout`, `network`, `redirect`, `body-too-large` |
| `received:true, complete:true, decoded:false, bodyRetention:'retained'` | `decode` |
| `received:true, complete:true, decoded:false, bodyRetention:'withheld'` | `decode` |
| `received:true, complete:true, decoded:true, redactionComplete:false` | `validation` |
| `received:true, complete:true, decoded:true, redactionComplete:true` | `redirect`, `http`, `content-type`, `parse`, `validation`, `provider` |

Google Trends RSS는 `provider:'google-trends'`, `purpose:'trending-rss'`, 필수
top-level `window:GoogleTrendsWindow`로 더 좁힌다. request는 `kind:'http'`,
`method:'GET'`, query 없는
`canonicalUrl:'https://trends.google.com/trending/rss'`, exact
`query:{geo:'KR',hours:GOOGLE_TRENDS_HOURS[window]}`여야 한다. success의
`response.parsed.window/asOf`는 top-level `window/asOf`와 같아야 한다. CSV parser
결과에는 network request/response wrapper를 만들지 않는다. C2는 네 window를 별도
호출하고 별도 source record/artifact로 저장한다.

generic response parser는 retained/withheld `decoded:false` branch를 각각 검사한다.
Google Trends refinement는 exact request의 retained-base64 branch만 허용하고
withheld를 거부한다. non-Google refinement는 withheld-checksum branch만 허용하고
retained/base64를 거부한다.

공용 `shortform-director-sensitive-string.ts`가 persistence guard와 C1/C2 redactor의
inspect+redact semantics를 함께 소유한다. provider-specific exception/bypass는
추가하지 않는다. classifier는 다음 순서와 exact predicate를 사용한다.

1. 빈 문자열이 아닌 각 `sensitiveValues`에 대해 raw value,
   `encodeURIComponent(value)`, percent escape의 hex digit만 lowercase로 바꾼
   encodeURIComponent variant, 그리고
   `new URLSearchParams([['v', value]]).toString().slice(2)` form variant와 그
   lowercase-percent-hex variant를 만든다. 입력 원문 또는 아래 최대 2회
   percent-decode variant가 이들 중 하나를 substring으로 포함하면 길이와 관계없이
   `known-sensitive-value`다. `+`를 임의로 space로 해석하지 않는다.
2. percent-decode variant는 `/(?:%[0-9a-f]{2})+/gi` run만
   `decodeURIComponent`하고 decode 오류 run은 원문으로 남기는 변환을 직전 결과에
   최대 2회 적용한다.
3. `AUTHORIZATION_HEADER_PATTERN`은 plain header뿐 아니라
   `"authorization":"Bearer x"`, `'authorization':'Basic ...'`,
   `authorization=Bearer x`를 잡는다. optional quote는 key와 scheme 앞에만 있고
   candidate는 whitespace, comma, semicolon, closing brace, single/double quote
   전에서 끝난다. match의 scheme/candidate 길이와 관계없이 항상
   `authorization`이다. redactor가 바꾸는 span은
   `match.indices[1][0]..match.indices[2][1]`, 즉
   scheme+사이 whitespace+candidate뿐이다. key, `:`/`=`, surrounding quote는
   보존하므로 malformed JSON safe text를 더 깨뜨리지 않는다.
4. `STANDALONE_BEARER_PATTERN`의 captured candidate는 다음 중 하나일 때만
   `authorization`이다.
   - `BEARER_PREFIX_MIN_LENGTH`의 case-sensitive prefix로 시작하고 candidate 전체
     길이가 그 entry의 threshold 이상
   - `.`으로 split한 결과가 정확히 3개이고 각 segment가
     `JWT_SEGMENT_PATTERN`을 만족하며 길이가 각각 8, 8, 16 이상
   - trailing `=`를 제거한 길이가 24 이상이고 `/[A-Za-z]/`, `/[0-9]/`,
     `BEARER_PUNCTUATION_PATTERN`을 모두 만족
   - trailing `=`를 제거한 길이가 32 이상이고 `/[a-z]/`, `/[A-Z]/`,
     `/[0-9]/`을 모두 만족
   별도 entropy 계산이나 임의 사전은 사용하지 않는다.
5. `STANDALONE_BASIC_PATTERN` candidate는 trailing padding을 제거한 길이가 2
   이상이고 modulo 4가 1이 아니며, padding 복원→base64 decode→unpadded base64
   re-encode가 candidate와 byte-for-byte 같고, decoded bytes가 모두
   `0x20..0x7e`이며, 첫 `:` byte가 index `1..length-2`에 있을 때만
   `authorization`이다.
6. private-key PEM은 body regex로 찾지 않는다. UTF-8 byte 길이가
   `SHARED_SENSITIVE_STRING_MAX_UTF8_BYTES`를 넘으면 즉시
   `redactionComplete:false`, `failure:'input-too-large'`다. 그 이하 입력은 ASCII
   uppercase shadow를 만들고 한 cursor로 왼쪽→오른쪽 진행하는 boundary state
   machine이 `-----BEGIN `과 `-----END `을 찾는다. 각 boundary는 다음 `-----`까지
   최대 `PRIVATE_KEY_PEM_MAX_LABEL_CODE_UNITS`만 읽고, trim이나 Unicode folding 없이
   ASCII-uppercase label이 `PRIVATE_KEY_PEM_LABEL_PATTERN`과 일치할 때만 private-key
   boundary다. body를 `.*?` 같은 regex로 match하지 않고 각 code unit을 상수 횟수만
   방문한다.
   - depth 0의 BEGIN은 `{start,label}`을 연다. 같은 label END는 inclusive END
     delimiter까지 한 complete span으로 닫는다.
   - private-key-looking boundary는 BEGIN/END marker부터 다음 CR/LF 또는
     `PRIVATE_KEY_PEM_BOUNDARY_LOOKAHEAD_CODE_UNITS` 중 먼저 오는 지점까지의
     ASCII-uppercase slice가 `PRIVATE KEY`를 포함하는 경우다. open 상태의 두 번째
     private-key BEGIN, depth 0의 END, 다른 label END, 이 looking boundary의 closing
     delimiter 부재·label 문법/길이 위반, EOF의 open BEGIN은 각각 nested, extra,
     mismatched, malformed, missing boundary다.
   - invalid boundary가 하나라도 있으면 partial replacement를 반환하지 않고
     `redactionComplete:false`, `sensitive:true`, `kinds:['private-key']`,
     `failure:'private-key-boundary'`로 닫는다.
   - 모두 valid면 non-overlapping span을 역순으로 entire
     BEGIN+body+matching-END 단위 `[removed]` 하나로 교체한다. complete block 하나당
     `key-material` count 1이며 multiple block도 원래 순서대로 deterministic하다.
     교체 결과에는 원래 BEGIN, body, END, body 안 sentinel이 남지 않는다.
7. HTTP(S) URL candidate를 WHATWG `URL`로 parse했을 때 username/password가 있거나,
   nonempty query value의 normalized key가
   `secret|password|credential|authorization|signature`를 포함하거나
   `token|apikey`로 끝나거나 exact `key`이면 `credential-url`이다. normalized key는
   NFKC→lowercase→`[^a-z0-9]` 제거 결과다.

PEM scan을 원문에서 먼저 완결한 뒤 complete span을 제거하고 나머지
authorization/exact-value/URL span을 deterministic `[removed]` 또는 query-pair
제거로 바꾼다. `redactionComplete:false`면 redactor는 whole response를 withhold하고
persistence guard는 complete/incomplete 여부와 무관하게 원문을 reject한다.
`kinds`는 중복 없이
`known-sensitive-value→authorization→private-key→credential-url` 고정 순서다.
`redactionComplete:true, sensitive:true`인 complete PEM 원문도 guard에서는 reject되고,
C1/C2 redactor가 만든 `[removed]` 결과를 다시 inspect해
`redactionComplete:true, sensitive:false`일 때만 codec→registry로 보낸다. 따라서
실제 `Authorization: Bearer x`, JWT, opaque mixed token,
`Basic dXNlcjpwYXNz`, complete/incomplete private-key PEM, credential URL은
차단하지만 `Bearer Stearns outlook`, `Basic skincare guide`는 byte-for-byte 그대로
보존한다.

shared classifier refinement 외 forbidden DTO key set은 넓히지 않는다. C1 JSON key는
`sourceText`, `rawBody`, `rawBodyBase64`, `responseRedactions`처럼 guard를 통과하는
이름만 사용한다. exact `raw`, `rawresponse`, `headers`,
secret/password/private-key 계열, credential/authorization 포함 key,
token/API-key suffix key를 만들지 않는다.

**Runtime rule**

- 자동 GET:
  `https://trends.google.com/trending/rss?geo=KR&hours=<4|24|48|168>`
- `Accept: application/rss+xml, application/xml, text/xml`
- client는 fetch, monotonic clock, wall clock, 고정 HTTP policy를 주입받는 side-effect
  없는 기본 singleton이다. Nest bootstrap·constructor·`onModuleInit`은 GET을
  시작하지 않는다.
- redirect는 fetch `redirect:'manual'`과 GET으로 처리하며
  `301/302/303/307/308`만 redirect로 인정한다. `new URL(location, currentUrl)`로 다음
  URL을 만들고 Location 부재·parse 오류를 실패시킨다. 최초 URL과 매 hop은
  `https:`, hostname exact `trends.google.com`, username/password 없음, port가
  empty 또는 `443`, hash 없음, pathname exact `/trending/rss`여야 한다.
- query key는 `geo`, `hours`가 각각 정확히 한 번만 있어야 하고 extra/duplicate key를
  거부한다. `geo=KR`, `hours=GOOGLE_TRENDS_HOURS[input.window]`를 매 hop 다시
  검증하며 original window를 redirect가 바꾸지 못한다. canonical href loop를
  거부하고 최대 3개 redirect만 따라가며 네 번째 redirect response에서 실패한다.
  허용 redirect 뒤 method도 항상 GET이다.
- timeout 10초는 redirect와 body streaming을 합친 전체 deadline이다. caller의
  `AbortSignal`과 결합해 timeout과 사용자 cancel을 구분한다.
- body 최대값은 5 MiB bytes다. `Content-Length`는 조기 거부 힌트일 뿐 신뢰하지 않고
  stream을 읽는 동안 실제 bytes를 세며 초과 즉시 abort한다.
- Content-Type header 원문은 `contentTypeRaw`에 보존하고, parameter를 제거한 뒤
  trim/lowercase한 값은 `mediaType`에 둔다. 비교에는 `mediaType`만 사용하며
  `application/rss+xml`, `application/xml`, `text/xml`만 허용한다.
- terminal non-redirect HTTP 응답은 non-2xx이거나 content-type이 허용 목록 밖이어도
  전체 deadline과 streaming byte cap 안에서 body 수신을 시도한다. 제한 안에서
  받고 valid UTF-8로 decode·정제한 실패 응답은
  rawBody/storedBodyChecksum/responseRedactions를 보존한다. invalid UTF-8 complete
  응답은 rawBodyBase64/checksum으로 보존하고 중단·초과 응답에는 body를 만들지 않는다.
- response를 완전히 받은 뒤 client 내부 XML parser와 schema validation까지 끝내
  success/failed `GoogleTrendsSourceFetchRecordV1`을 반환한다. 별도 source-response
  redactor는 decoded XML을 항상 받고 parser가 fixed DTO를 만들었으면 그 DTO도 함께
  받아 auth scheme/key material/sensitive URL query를 `[removed]` 또는 query pair
  제거로 정제한다. 무해한 title/sourceText/news URL/snippet은 의미를 보존한다.
- redactor는 두 safe output과 deterministic summary를 함께 반환하거나 fail closed한다.
  실패하면 unsafe value를 record/logger에 넣지 않고
  `error.category:'validation'`, fixed public message
  `The source response could not be safely stored.`의 failed record를 만든다.
- XML은 실제 namespace URI
  `https://trends.google.com/trending/rss`를 기준으로 읽는다. literal `ht` prefix에
  의존하지 않으며 RSS news item은 반복 항목을 모두 보존한다. DOCTYPE/ENTITY 선언은
  fail closed하되 XML 기본 entity reference는 정상 decode한다.
- Google Trends UI의 공식 `Download CSV` parser가 C1에서 필수 지원하는 sanitized
  header는 영문 `Trends, Search volume, Started, Ended, Trend breakdown` exact
  5개다. 한국어 header alias는 실제 sanitized export를 확보해 fixture로 고정하기
  전에는 추측해 추가하지 않는다.
- 별도 status 열을 전제하지 않는다. RFC 4180 decode 뒤 trim한 `Ended`가 nonblank면
  `ended`, `Ended`가 blank이고 trim한 `Started`가 nonblank면 `active`, 둘 다
  blank면 `unknown`이다. Started/Ended `sourceText`는 항상 보존한다.
- optional `started.at`/`ended.at`은 sanitized official fixture에서 실제 확인한
  timezone-bearing absolute 또는 relative 문법만 exact parser/test로 추가한다.
  현재 확보한 CSV capture가 없으므로 C1 필수 범위에서는 해석 시각을 추측하거나
  assertion하지 않는다. 실제 status 열도 capture 뒤 fixture-backed exact alias로만
  optional 보조 입력에 추가할 수 있다.
- 문서화된 안정적 CSV URL이 없으므로 이 task에서 UI HTML, 내부 RPC, Google Trends
  alpha API를 호출하지 않는다. CSV parser는 parsed DTO만 반환하고 가짜
  URL/status/latency의 `SourceFetchRecordV1`을 만들지 않는다. 사용자가 CSV를 첨부해야
  기본 조사가 되는 흐름도 만들지 않는다.
- runtime dependency는 namespace-aware XML용 `saxes`와 RFC 4180 CSV용
  `csv-parse`를 사용한다. regex XML parser와 `split(',')` parser는 금지한다.

- [ ] 독립 review가 확정한 영문 5-header sanitized fixture와 고정 `asOf`를 사용하되,
  capture 없는 시간 문법의 `at` 해석 assertion은 두지 않고 parser 실패 테스트를 먼저
  쓴다:
  - RSS root의 실제 namespace URI와 다른 prefix/같은 URI 허용
  - 같은 local name/잘못된 URI, DOCTYPE/ENTITY 선언, malformed XML 거부와 XML 기본
    entity reference 정상 decode
  - item title, traffic sourceText/lowerBound, RFC-822 pubDate, 반복 news item
  - 영문 exact 5-header CSV, UTF-8 BOM, LF/CRLF, quoted comma/newline/escaped quote
  - Started/Ended sourceText를 항상 보존하고 capture 없는 상대/absolute 값을 추측해
    `at`으로 해석하지 않음
  - nonblank Ended→ended, blank Ended+nonblank Started→active, 둘 다 blank→unknown
  - 실제 capture 없는 한국어/status header alias는 추측해 허용하지 않음
  - trend breakdown 관련 검색어
  - `4h/24h/48h/7d`가 `4/24/48/168`로만 매핑되고 row 나이로 바뀌지 않음
  - `K`/`M`/구분자를 포함한 검색량은 sourceText를 항상 보존하고 lowerBound는 해석
    가능할 때만 둠
  - 소스에 없거나 불명확한 growth는 `growthRatePercent`를 생략하고 `0`을 만들지 않음
- [ ] injected fake fetch/clock 기반 HTTP 실패 테스트를 먼저 쓴다:
  - 네 window의 정확한 URL·GET·Accept와 서로 다른 네 record
  - 네 window 각각의 pre-response network 실패와 complete malformed XML parse 실패가
    같은 top-level `asOf`, 해당 `window`, exact request hours를 보존
  - `301/302/303/307/308` redirect 3회까지 GET 성공, 그 밖 3xx 거부
  - Location을 current URL 기준으로 resolve하고 Location 부재/parse 오류, canonical
    loop, 네 번째 redirect 실패
  - 매 hop의 scheme/hostname/username/password/port/hash/path 변조 차단
  - query의 extra/duplicate/missing `geo|hours`, `geo!=KR`, original window와 다른
    hours 차단
  - 전체 10초 deadline, caller cancel, header 뒤 중단
  - 거짓/누락 `Content-Length`에서도 실제 streaming bytes 5 MiB 제한
  - `contentTypeRaw` 보존, `mediaType` case/parameter 정규화와 누락/비 XML 실패
  - valid UTF-8 complete parse 실패는 deterministic-redacted rawBody,
    responseRedactions, storedBodyChecksum을 보존
  - invalid UTF-8 complete body는 `decoded:false`/decode error, canonical padded
    rawBodyBase64, `bodyRetention:'retained'`, decoded-byte stored checksum을 보존하고
    decoded length가 bytesReceived와 일치
  - base64 whitespace/noncanonical padding/alphabet/re-encode mismatch 거부.
    Google refinement는 withheld branch를 거부하고 non-Google refinement는
    retained/base64 branch를 거부
  - incomplete/oversize는 실제 `bytesReceived`, `complete:false`만 가지며 raw/checksum
    없음
  - client latency는 injected monotonic clock, `collectedAt`은 injected wall clock 사용
- [ ] runtime 계약·DI 실패 테스트를 먼저 쓴다:
  - `parseSourceFetchRecordV1` exact-key, status `100..599` safe integer,
    safe-nonnegative `bytesReceived`, success/error/response union 불변식
  - 각 union branch가 `?:never` 필드를 runtime에서 거부하고
    contentTypeRaw/mediaType이 both-or-neither임
  - generic response 형태별 category matrix와 failed parsed 금지
  - Google C1 category 우선순위와 형태:
    - header 전 cancel/timeout/network→`received:false`
    - header 뒤 cancel/timeout/network 및 cap 초과→incomplete
    - redirect policy 실패→3xx status의 incomplete redirect
    - complete invalid UTF-8→decode
    - complete valid UTF-8의 non-2xx→http, invalid media type→content-type,
      malformed XML→parse, namespace/schema mismatch→validation
    - valid 2xx/media type/XML/schema→succeeded
  - C1은 generic `provider` category를 만들지 않지만 generic parser의 future provider
    범위는 유지
  - Google Trends provider/purpose/window와 canonicalUrl/query/parsed window·asOf
    일치, pre-response 실패도 가짜 status 없음
  - decoded/rawBody와 retained-undecodable/rawBodyBase64 branch별 stored-body checksum
    재계산, withheld-undecodable received-body fingerprint와 B1 artifact descriptor
    checksum 대상 구분
  - valid XML/parsed DTO의 auth-scheme, key material, credential-bearing news
    URL/title/snippet fixture를 정제하고 responseRedactions kind/count 고정
  - harmless title/sourceText/news URL/snippet은 byte/value 의미 보존
  - shared classifier fixture로 actual `Authorization: Bearer`/prefix/JWT/
    24자 punctuation-mixed opaque/32자 mixed-case opaque Bearer/canonical
    `user:password` Basic/credential URL, raw·percent·form-encoded exact sensitive
    value를 위 상수·regex·threshold 그대로 차단
  - single/multiple `PRIVATE KEY`, `RSA PRIVATE KEY`, `EC PRIVATE KEY` complete PEM은
    BEGIN+body+same-label END 전체를 block당 `[removed]` 하나로 바꾸며 original
    header/body/end/sentinel이 결과에 0건
  - missing END, mismatched label END, nested BEGIN, extra END, malformed/oversize
    boundary는 `redactionComplete:false`이고 partial redacted text가 없음
  - complete/incomplete PEM 원문은 B1 guard가 모두 reject하며, complete PEM을 C1
    redactor로 제거한 source artifact만 actual codec→registry→reload를 통과하고
    incomplete PEM은 response 전체를 withhold
  - 5 MiB bounded input에서 PEM scanner가 body wildcard/backtracking regex 없이
    single forward state-machine으로 결정됨
  - header context의 짧은 token과 explicit `sensitiveValues`의 짧은 standalone token도
    차단하지만 `Bearer Stearns outlook`, `Basic skincare guide`는 정확히 보존
  - plain `Authorization: Bearer x`, JSON
    `"authorization":"Bearer x"`, single-quoted
    `'authorization':'Basic dTpw'`, `authorization=Bearer x`, closing brace가 빠진
    malformed JSON text에서도 scheme+candidate만 `[removed]`로 바꾸고
    quote/separator와 나머지 text를 보존
  - key context가 없는 `"note":"Bearer Stearns outlook"`과
    `"note":"Basic skincare guide"`는 redaction 없이 byte-for-byte 보존
  - 같은 fixture table을 shared classifier, B1 persistence guard, C1 redactor에
    통과시켜 classify/redact decision drift가 없음
  - redactor failure는 unsafe body/checksum/parsed 없이 fixed validation failed record
  - actual B1 artifact codec→registry publish integration이 credential-like fixture와
    injected sentinel을 통과하고 persisted wrapper/descriptor/index 어디에도 sentinel,
    원문 auth/key/query value가 없음
  - C1 artifact DTO key를 실제 B1 forbidden-key set과 대조해 exact `raw`,
    `rawresponse`, `headers`, secret/password/private-key 계열,
    credential/authorization 포함, token/API-key suffix key가 0개임
  - `source-fetch` public artifact validator가 기존 `run-failure` validator를 대체하지
    않고 목록에 append됨
  - `GoogleTrendsTrendingSource`가 concrete client에 `useExisting`으로 묶이고 같은
    singleton이며 transport token/concrete는 module export가 아님
  - 실제 compiled `dist`를 require하고 Nest application context를 bootstrap해도 fake
    fetch 호출 수가 0임
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-sensitive-string.test.js
node --test test/shortform-director-run-storage.test.js
node --test test/shortform-director-google-trends.test.js
```

- [ ] `saxes`, `csv-parse`를 production dependency와 lockfile에 추가한 뒤
  `GoogleTrendsTrendingClient.fetchRss(input)`, `parseOfficialCsv(csvText, input)`,
  `parseSourceFetchRecordV1(value)`를 최소 구현한다.
- [ ] shared sensitive-string classifier를 persistence guard에서 작은 pure domain
  파일로 추출하고 C1 response redactor가 같은 inspect+redact API를 사용하게 한다.
  provider-specific exception은 만들지 않고 forbidden DTO key set은 그대로 둔다.
  guard는 `!redactionComplete || sensitive` 원문을 reject한다. redactor는 complete PEM
  full span을 제거한 결과를 재검사해 complete+non-sensitive일 때만 반환하고
  input-too-large/unmatched/mismatched/nested/extra/malformed PEM에는 partial result 없이
  fail closed한다.
- [ ] source-response redactor를 client와 분리해 구현하고 transport/redactor token은
  feature 내부 provider로만 둔다.
- [ ] domain의 좁은 `GoogleTrendsTrendingSource` port와 concrete client를
  `useExisting`으로 묶는다. fetch/clock/policy token은 feature 내부 provider로만 두고
  export하지 않는다.
- [ ] `ShortformDirectorSourceFetchArtifactValidator`를 기존 public artifact validator
  목록에 append하고 `source-fetch` 저장값이 strict runtime parser를 반드시 통과하게
  한다.
- [ ] build/focused test와 production bundle을 통과시킨다.

```bash
npm run build
node --test test/shortform-director-sensitive-string.test.js
node --test test/shortform-director-run-storage.test.js
node --test test/shortform-director-google-trends.test.js
npm run bundle
```

- [ ] Commit:
  `feat(shortform-director): collect official Google Trends exports`

## Task C2: 조사 coordinator와 다중 출처 정규화

**Files**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/domain/provider-call-audit.contract.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/bounded-provider-fetch.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/bounded-provider-fetch.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.factory.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.factory.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.redactor.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/application/provider-call-audit.redactor.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/naver-research-provider.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/naver-research-provider.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research.controller.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research.openapi.spec.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-source-fetch-web-api.client.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-provider-audit.mapper.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-provider-failure-body.projector.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-web-api.client.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-query-planner.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-normalizer.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-topic-validator.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-run.coordinator.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-run-pipeline-failure.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/non-google-source-fetch.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/provider-failure-evidence.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/user-source.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-non-google-response.redactor.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/create-shortform-director-user-source.dto.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-research.dto.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-research-run.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-non-google-source-fetch.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-provider-failure-body.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-topic-validation.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-research-api.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/research.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-public-artifact.validator.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-lineage-publisher.service.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-run-storage.test.js`

**Local API**

- `POST /projects/shortform-director/research-runs`
- `GET /projects/shortform-director/research-runs`
- `GET /projects/shortform-director/research-runs/:runId`
- `DELETE /projects/shortform-director/research-runs/:runId`
- `GET /projects/shortform-director/research-runs/:runId/topics`

Start body:

```ts
interface StartResearchRequest {
  profileId: string;
  keyword?: string;
  userSourceIds?: string[];
}
```

**A3 transport audit → local artifact boundary**

C2가 실제 wire/decode/parse 상태를 합성하지 않도록 A3의 web-only
`ProviderCallAuditV1.response`를 exact discriminated union으로 바꾼다.

```ts
export type ProviderReceivedBodyChecksum = `sha256:${string}`;

export type ProviderCallFailureKind =
  | 'cancelled'
  | 'provider_4xx'
  | 'provider_5xx'
  | 'timeout'
  | 'network_error'
  | 'response_too_large'
  | 'invalid_response';

export type ProviderCallReceivedMetadataV1 = {
  received: true;
  status: number;
  contentType: string | null;
  bytesReceived: number;
};

export type ProviderCallNoResponseV1 = {
  received: false;
  complete: false;
  bytesReceived: 0;
  status?: never;
  contentType?: never;
  decoded?: never;
  parseState?: never;
  redactionComplete?: never;
  bodyRetention?: never;
  receivedBodyChecksum?: never;
  raw?: never;
};

export type ProviderCallIncompleteResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: false;
    decoded?: never;
    parseState?: never;
    redactionComplete?: never;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw?: never;
  };

export type ProviderCallUndecodableResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: false;
    parseState?: never;
    redactionComplete?: never;
    bodyRetention: 'withheld';
    receivedBodyChecksum: ProviderReceivedBodyChecksum;
    raw?: never;
  };

export type ProviderCallDecodedSafeTextResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'not-attempted' | 'failed';
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw: string;
  };

export type ProviderCallParsedResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'parsed';
    redactionComplete: true;
    bodyRetention?: never;
    receivedBodyChecksum?: never;
    raw: unknown;
  };

export type ProviderCallDecodedRedactionFailedResponseV1 =
  ProviderCallReceivedMetadataV1 & {
    complete: true;
    decoded: true;
    parseState: 'not-attempted' | 'failed' | 'parsed';
    redactionComplete: false;
    bodyRetention: 'withheld';
    receivedBodyChecksum?: never;
    raw?: never;
  };

export type ProviderCallAuditResponseV1 =
  | ProviderCallNoResponseV1
  | ProviderCallIncompleteResponseV1
  | ProviderCallUndecodableResponseV1
  | ProviderCallDecodedSafeTextResponseV1
  | ProviderCallParsedResponseV1
  | ProviderCallDecodedRedactionFailedResponseV1;
```

`BoundedProviderFetchService`의 internal result도 같은 transport discriminant를
사용하되 valid decoded body는 transient `bodyText`와 optional parsed value로만
factory에 넘긴다. public `raw`는 별도
`provider-call-audit.redactor.ts`가 exact/encoded secrets, sensitive keys, auth/private
key/credential URL을 fail-closed 정제한 뒤에만 만든다. web package 경계상 desktop
pure file을 import하지 않지만 PEM byte/label/lookahead constants와 linear boundary
algorithm, `redactionComplete` union, fixture table을 exact mirror하고 contract test가
drift를 막는다.

- fetch가 response header를 받기 전 network/timeout/caller abort면
  `received:false`, `complete:false`, `bytesReceived:0`이고
  status/contentType/decode/body field가 없다.
- header를 받은 뒤 timeout/abort/stream error/declared-or-streaming oversize면
  `received:true`, status와 nullable contentType, 실제 지금까지 읽은
  `bytesReceived`, `complete:false`만 남긴다. `Content-Length` 조기 거부는
  `bytesReceived:0`인 received-incomplete다.
- 완전 수신 bytes는 `new TextDecoder('utf-8', {fatal:true})`로 decode한다.
  invalid UTF-8은 raw/base64 없이 `decoded:false`, `bodyRetention:'withheld'`,
  complete bytes의 nonsecret `receivedBodyChecksum`만 가진다.
- JSON media type의 valid UTF-8 malformed text는 `decoded:true`,
  `parseState:'failed'`이고 safely redacted text를 `raw`로 보존한다.
  non-JSON text는 `parseState:'not-attempted'`, parsed JSON은
  `parseState:'parsed'`다.
- decoded text/parsed value를 안전하게 redaction하지 못하면 decode/parse state는
  유지하되 `redactionComplete:false`, `bodyRetention:'withheld'`, raw 없음과 fixed
  `invalid_response` failure로 닫는다.
- `ProviderCallFailureV1`은 response union과 함께 검사한다. no-response는
  `cancelled|timeout|network_error`, incomplete는 여기에
  `response_too_large`, undecodable/parse-failed/redaction-failed는
  `invalid_response`, complete safe text/parsed는 HTTP status에 따라
  `provider_4xx|provider_5xx|invalid_response|none`만 허용한다.

이 audit wrapper는 desktop transport와 mapper 사이의 일시 입력일 뿐 artifact DTO가
아니다. `schemaVersion`, `providerCredentialId`, `response.raw`를 포함한 A3 wrapper
전체나 provider payload object를 B1에 직접 전달하지 않는다. adapter는 HTTP/JWT와
A3 exact success/error union만 담당하고, source별 mapper가 allowlist projection한
뒤에만 local record를 만든다.

A3 `parseState`는 transport-only discriminator다. local `SourceFetchRecordV1`
interface 어느 branch에도 넣지 않고 local runtime parser는 `parseState` key를
unknown key로 reject한다. mapper는 다음 priority를 위에서 아래로 처음 match한 한
branch에 적용한 뒤 `parseState`를 소거한다.

| priority | A3 조건 | exact local 결과 |
|---:|---|---|
| 1 | `received:false` | status/content/body 없는 `SourceFetchNoResponseV1`; A3 failure에 따라 `cancelled|timeout|network` |
| 2 | `received:true, complete:false` | 같은 status/content/actual `bytesReceived`의 `SourceFetchIncompleteResponseV1`; `cancelled|timeout|network|body-too-large` |
| 3 | `complete:true, decoded:false` | 같은 status/content/bytes와 `receivedBodyChecksum`의 withheld branch, `error.category:'decode'`; raw/base64/stored checksum 없음 |
| 4 | decoded이고 A3 redactor 또는 이 branch에 필요한 local success/failure projector가 `redactionComplete:false` | 같은 status/content/bytes/decoded의 body 없는 branch, `error.category:'validation'`; HTTP status보다 먼저 적용 |
| 5 | decoded complete이고 status `100..199` 또는 `300..399` | A3 source adapter가 terminal provider result로 만들 수 없는 status이므로 body/checksum/parsed 없는 validation failure |
| 6 | decoded complete이고 status `400..599` | parseState와 무관하게 `error.category:'http'`. `not-attempted|failed` safe text는 safely redacted `rawBody`, `parsed` raw object는 아래 failure-body projector의 canonical JSON `rawBody`; 둘 다 post-redaction `storedBodyChecksum`, `parsed` 없음 |
| 7 | status `200..299`, `parseState:'failed'` | safely redacted text `rawBody`+stored checksum, `parsed` 없음, `error.category:'parse'` |
| 8 | status `200..299`, expected JSON source, `parseState:'not-attempted'` | safely redacted text `rawBody`+stored checksum, `parsed` 없음, `error.category:'content-type'` |
| 9 | status `200..299`, `parseState:'parsed'`, exact known Naver/YouTube error envelope | provider failure projector의 canonical `rawBody`+stored checksum, `parsed` 없음, `error.category:'provider'` |
| 10 | status `200..299`, `parseState:'parsed'`, exact source success DTO | source success projector의 canonical `rawBody`, same exact DTO `parsed`, stored checksum, `status:'succeeded'` |
| 11 | status `200..299`, `parseState:'parsed'`, known error도 exact success DTO도 아님 | body/checksum/parsed 없는 `redactionComplete:false`, `error.category:'validation'` |

priority 6의 정책은 Naver/YouTube 모두 `http` 하나이며 4xx/5xx를 provider category로
바꾸지 않는다. `provider`는 오직 priority 9의 2xx known provider error envelope다.
failure kind rename은 exact
`cancelled→cancelled`, `timeout→timeout`, `network_error→network`,
`response_too_large→body-too-large`이며 다른 조합은 mapper가 reject한다.
local에는 해당 branch가 정의한 `status`, wire `bytesReceived`, `complete`, `decoded`만
정직하게 보존한다. A3 `contentType`만 local `contentTypeRaw`과 normalized
`mediaType` both-or-neither로 변환한다. canonical local body 길이로 wire
`bytesReceived`를 만들지 않는다. branch 선택 뒤 `parseState`를 폐기하며 local
artifact schema에는 이 field가 없다.

**B1-safe provider failure evidence**

success DTO mapper와 failure-body projector는 별도 책임이다. status `400..599`의
parsed raw object와 status `200..299`의 known error envelope만
`shortform-director-provider-failure-body.projector.ts`가 받는다.

projection/drop 전에 parsed value 전체를 iterative own-data preflight한다. A3의
4 MiB cap 안에서 accessor/inherited/symbol/cycle/non-JSON value를 reject하고 root
depth 0, 최대 depth 32로 every string key/value를 방문해 shared PEM boundary scan을
실행한다. allowlist 밖이거나 sensitive name이라 나중에 drop할 subtree도 이 preflight는
생략하지 않는다. complete PEM은 허용하되 실제 보존 field projection에서 full span을
제거하고, incomplete boundary가 하나라도 있으면 whole projection이 incomplete다.

```ts
export const PROVIDER_FAILURE_EVIDENCE_LIMITS = {
  maxDepth: 6,
  maxNodesIncludingEntries: 48,
  maxEntriesPerContainer: 16,
  maxNameCodePoints: 64,
  maxTextCodePoints: 160,
  maxCanonicalUtf8Bytes: 64 * 1024,
  maxKnownSummaryCodePoints: 2_048,
  maxKnownCodeCodePoints: 128,
  maxKnownReasons: 16,
} as const;

export type ProviderFailureEvidenceNodeV1 =
  | { kind: 'null' }
  | { kind: 'boolean'; value: boolean }
  | { kind: 'number'; value: number }
  | { kind: 'text'; value: string }
  | { kind: 'list'; items: ProviderFailureEvidenceNodeV1[] }
  | { kind: 'map'; entries: ProviderFailureEvidenceEntryV1[] };

export interface ProviderFailureEvidenceEntryV1 {
  name: string;
  value: ProviderFailureEvidenceNodeV1;
}

export interface ProviderFailureProjectionCountsV1 {
  omittedEntries: number;
  redactedValues: number;
  truncatedValues: number;
}

export interface NaverProviderFailureEvidenceV1
  extends ProviderFailureProjectionCountsV1 {
  schemaVersion: 'shortform-director-naver-provider-failure.v1';
  source: 'naver-provider-failure';
  code: string;
  summary: string;
}

export interface YouTubeProviderFailureReasonV1 {
  domain?: string;
  reason?: string;
  summary?: string;
}

export interface YouTubeProviderFailureEvidenceV1
  extends ProviderFailureProjectionCountsV1 {
  schemaVersion: 'shortform-director-youtube-provider-failure.v1';
  source: 'youtube-provider-failure';
  httpCode?: number;
  statusText?: string;
  summary: string;
  reasons: YouTubeProviderFailureReasonV1[];
}

export interface GenericProviderFailureEvidenceV1
  extends ProviderFailureProjectionCountsV1 {
  schemaVersion: 'shortform-director-generic-provider-failure.v1';
  source: 'generic-provider-failure';
  provider: 'naver' | 'youtube';
  root: ProviderFailureEvidenceNodeV1;
}

export type ProviderFailureEvidenceV1 =
  | NaverProviderFailureEvidenceV1
  | YouTubeProviderFailureEvidenceV1
  | GenericProviderFailureEvidenceV1;

export type ProviderFailureBodyProjectionV1 =
  | {
      redactionComplete: true;
      evidence: ProviderFailureEvidenceV1;
      rawBody: string;
      storedBodyChecksum: SourceFetchStoredBodyChecksum;
      responseRedactions: SourceResponseRedactionSummaryV1[];
    }
  | {
      redactionComplete: false;
      evidence?: never;
      rawBody?: never;
      storedBodyChecksum?: never;
      responseRedactions: [];
    };

export function projectProviderFailureBodyV1(input: {
  provider: 'naver' | 'youtube';
  status: number;
  value: unknown;
  sensitiveValues: readonly string[];
}): ProviderFailureBodyProjectionV1;

export function parseProviderFailureEvidenceV1(
  value: unknown,
): ProviderFailureEvidenceV1;

export function canonicalStringifyProviderFailureEvidenceV1(
  value: ProviderFailureEvidenceV1,
): string;
```

known envelope recognition과 projection은 exact하다.

- Naver는 own-data plain object의 own `errorCode`와 `errorMessage`가 둘 다 string일
  때만 known이다. `code`와 `summary`로 rename하고 나머지 own property는 값 전체를
  projection 단계에서 재귀 방문하지 않고 property당 `omittedEntries` 1로 센다.
- YouTube는 own-data plain root의 own `error`가 own-data plain object이고,
  `error.message`가 string이며, `error.code` safe integer, nonempty
  `error.status` string, `error.errors` array 중 하나 이상이 있을 때 known이다.
  `httpCode/statusText/summary`와 최대 16개의 plain `errors` item에서
  string `domain/reason/message→summary`만 projection한다. malformed item, 초과 item,
  root의 `error` 외 property, error object/item의 allowlist 밖 property는 각각
  `omittedEntries` 1이다. omitted subtree 내부를 다시 세지 않는다.
- known projector의 omitted property name이 아래 generic sensitive-name predicate에
  걸리면 `redactedValues`와 `key-material` summary도 1 올리고 원래 name/value는
  evidence에 넣지 않는다. safe unknown extension은 omitted count만 올린다.
- projected `httpCode`는 원문이 safe integer `100..599`일 때만 존재하며 그 밖의
  `error.code`는 omitted 1이다. `statusText`는 original status가 nonempty일 때만
  존재하고 empty status는 omitted 1이다. 보존할 status가 redaction 뒤 empty가 되면
  whole projection failure다. Naver code/summary와 YouTube summary는 string이면
  empty도 evidence로 허용하고 exact 원문 의미를 합성하지 않는다.
- known string은 shared sensitive classifier로 inspect/redact한 뒤 Unicode code
  point 기준 code/status/reason/domain 128, summary 2,048에서
  `…[truncated]` suffix를 포함하도록 자르고 field당 `truncatedValues` 1이다.
  classifier incomplete이면 whole projection이 `redactionComplete:false`다.
- status `400..599` parsed value가 known envelope가 아니면 generic projector를 쓴다.
  status `200..299` unknown shape에는 generic fallback을 쓰지 않고 priority 11
  validation-withheld로 닫는다.

generic projector는 위 preflight를 통과한 JSON-safe own-data tree만 받는다.
traversal은 다음 exact 규칙이다.

1. depth는 root 0이며 6보다 깊은 subtree, container의 17번째 이후 item/entry,
   node 또는 entry를 합친 49번째 이후 값은 방문하지 않고 각각
   `omittedEntries` 1이다. pre-order로 root node, container entry, value node 순서로
   budget을 reserve하고 entry+value 중 하나라도 48을 넘으면 그 entry/subtree 전체를
   omitted 1로 처리한다. omitted subtree 내부를 다시 세지 않는다.
2. object own string key를 UTF-16 code-unit ascending으로 정렬하고 JSON object key로
   재사용하지 않는다. `{name,value}` entries array에만 넣는다. key normalization은
   B1과 같은 NFKC→lowercase→`[^a-z0-9]` 제거다. normalized name이 exact
   `raw`, `rawresponse`, `headers`, `requestheaders`, `responseheaders`, `cookie`,
   `setcookie`, `cause`, `stack`, `config` 중 하나이거나
   `secret|password|privatekey|credential|authorization|signature`를 포함하거나
   `token|apikey`로 끝나면 sensitive name이다. 따라서
   `raw`, `nextPageToken`, `accessToken`, `clientSecret` 등은 entry 전체를 drop하고
   `omittedEntries`와 `redactedValues`를 각각 1 올린다.
3. safe key name과 string scalar는 shared classifier로 inspect한다. incomplete PEM/
   oversize inspection은 whole projection failure다. complete result의 sensitive
   span은 `[removed]`/safe URL pair removal 결과만 보존하고 logical value당
   `redactedValues` 1을 올린다. summary는 authorization replacement마다
   `auth-scheme`, complete PEM 또는 `known-sensitive-value` replacement마다
   `key-material`, credential URL pair removal마다 `sensitive-query` count 1이고 kind
   order는 이 순서다.
4. safe name은 64, text는 160 Unicode code point를 넘으면
   `…[truncated]` suffix를 포함한 길이로 자르고 logical value당
   `truncatedValues` 1이다. boolean/null과 finite JSON number는 그대로다.
5. projection 뒤 exact runtime parser를 통과한 evidence를
   `canonicalStringifyProviderFailureEvidenceV1`로 한 번 stringify한다. 이 함수는
   null/boolean/finite number/string을 `JSON.stringify` 결과로, array를 기존 순서로,
   plain object own key를 UTF-16 code-unit ascending 순서로 재귀 직렬화하고 whitespace를
   넣지 않는다. UTF-8 길이가 64 KiB를 넘거나 JSON.parse→runtime parse→canonical
   re-stringify가 byte-for-byte 다르면 whole projection을 fail closed한다.

known/generic result 모두 `rawBody`는 이 post-redaction evidence의 canonical JSON,
`storedBodyChecksum`은 그 UTF-8 bytes의 SHA-256이다. local failed response의
`parsed`는 반드시 없고 A3 wrapper/`response.raw` object 자체를 stringify하거나
저장하지 않는다. runtime parser는 각 union branch의 exact keys, count의 nonnegative
safe integer, 모든 위 길이/shape limit를 재검증한다. complete PEM은 block 전체 제거
후 evidence가 남고 incomplete PEM은 whole response withheld다.

**B1-safe non-Google parsed DTO**

```ts
export interface NaverPageV1 {
  start: number;
  returned: number;
  total: number;
}

export interface NaverNewsParsedV1 {
  schemaVersion: 'shortform-director-naver-news.v1';
  source: 'naver-news';
  page: NaverPageV1;
  items: Array<{
    title: string;
    url: string;
    sourceUrl?: string;
    summary: string;
    publishedAtSourceText: string;
    publishedAt?: string;
  }>;
}

export interface NaverWebParsedV1 {
  schemaVersion: 'shortform-director-naver-web.v1';
  source: 'naver-web';
  page: NaverPageV1;
  items: Array<{
    title: string;
    url: string;
    summary: string;
  }>;
}

export interface NaverBlogParsedV1 {
  schemaVersion: 'shortform-director-naver-blog.v1';
  source: 'naver-blog';
  page: NaverPageV1;
  items: Array<{
    title: string;
    url: string;
    summary: string;
    authorName: string;
    authorUrl?: string;
    publishedAtSourceText: string;
    publishedAt?: string;
  }>;
}

export interface NaverDataLabParsedV1 {
  schemaVersion: 'shortform-director-naver-datalab.v1';
  source: 'naver-datalab';
  phase: 'initial' | 'discovered';
  startDate: string;
  endDate: string;
  timeUnit: 'date';
  series: Array<{
    title: string;
    terms: string[];
    points: Array<{ period: string; ratio: number }>;
  }>;
}

export interface YouTubeSearchParsedV1 {
  schemaVersion: 'shortform-director-youtube-search.v1';
  source: 'youtube-search';
  lane: YouTubeSearchLane;
  pageCursor?: string;
  totalResults: number;
  resultCount: number;
  items: Array<{
    videoId: string;
    publishedAt: string;
    channelId: string;
    title: string;
    description: string;
    thumbnailUrl?: string;
  }>;
}

export interface YouTubeVideosParsedV1 {
  schemaVersion: 'shortform-director-youtube-videos.v1';
  source: 'youtube-videos';
  lane: YouTubeSearchLane;
  items: Array<{
    videoId: string;
    publishedAt: string;
    channelId: string;
    channelTitle: string;
    title: string;
    description: string;
    thumbnailUrl?: string;
    durationSeconds: number;
    viewCount: number;
    likeCount?: number;
    commentCount?: number;
  }>;
}

export interface YouTubeCommentsParsedV1 {
  schemaVersion: 'shortform-director-youtube-comments.v1';
  source: 'youtube-comments';
  videoId: string;
  pageCursor?: string;
  items: Array<{
    threadId: string;
    commentId: string;
    authorName: string;
    text: string;
    publishedAt: string;
    updatedAt: string;
    likeCount: number;
    replyCount: number;
  }>;
}

export type NonGoogleParsedV1 =
  | NaverNewsParsedV1
  | NaverWebParsedV1
  | NaverBlogParsedV1
  | NaverDataLabParsedV1
  | YouTubeSearchParsedV1
  | YouTubeVideosParsedV1
  | YouTubeCommentsParsedV1;

export type NonGoogleSourceRecordForV1<
  Provider extends 'naver' | 'youtube',
  Purpose extends string,
  Parsed extends NonGoogleParsedV1,
> =
  | (SourceFetchSucceededRecordV1 & {
      provider: Provider;
      purpose: Purpose;
      response: SourceFetchStoredDecodedCompleteResponseV1 & {
        parsed: Parsed;
      };
    })
  | (SourceFetchFailedRecordV1 & {
      provider: Provider;
      purpose: Purpose;
    });

export type NaverNewsSourceFetchRecordV1 =
  NonGoogleSourceRecordForV1<'naver', 'naver-news', NaverNewsParsedV1>;
export type NaverWebSourceFetchRecordV1 =
  NonGoogleSourceRecordForV1<'naver', 'naver-web', NaverWebParsedV1>;
export type NaverBlogSourceFetchRecordV1 =
  NonGoogleSourceRecordForV1<'naver', 'naver-blog', NaverBlogParsedV1>;
export type NaverDataLabSourceFetchRecordV1 = NonGoogleSourceRecordForV1<
  'naver',
  'naver-datalab-initial' | 'naver-datalab-discovered',
  NaverDataLabParsedV1
>;
export type YouTubeSearchSourceFetchRecordV1 = NonGoogleSourceRecordForV1<
  'youtube',
  `youtube-search-${YouTubeSearchLane}`,
  YouTubeSearchParsedV1
>;
export type YouTubeVideosSourceFetchRecordV1 = NonGoogleSourceRecordForV1<
  'youtube',
  `youtube-videos-${YouTubeSearchLane}`,
  YouTubeVideosParsedV1
>;
export type YouTubeCommentsSourceFetchRecordV1 =
  NonGoogleSourceRecordForV1<
    'youtube',
    'youtube-comments',
    YouTubeCommentsParsedV1
  >;

export type NonGoogleSourceFetchRecordV1 =
  | NaverNewsSourceFetchRecordV1
  | NaverWebSourceFetchRecordV1
  | NaverBlogSourceFetchRecordV1
  | NaverDataLabSourceFetchRecordV1
  | YouTubeSearchSourceFetchRecordV1
  | YouTubeVideosSourceFetchRecordV1
  | YouTubeCommentsSourceFetchRecordV1;

export function parseNonGoogleSourceFetchRecordV1(
  value: unknown,
): NonGoogleSourceFetchRecordV1;
```

`parseNonGoogleSourceFetchRecordV1`은 generic parser 뒤
provider/purpose/request/parsed schema를 함께 좁힌다. DataLab purpose와
`parsed.phase`, YouTube purpose suffix와 `parsed.lane`, comments input/parsed
`videoId`가 일치해야 한다. 각 DTO는 exact keys, bounded array/string, safe
nonnegative integer/finite ratio, UTC/date/URL 형식을 검사한다. arbitrary provider
field나 arbitrary nested object를 허용하지 않는다.

failed refinement도 priority contract를 재검증한다. `provider` category는 2xx와
known failure evidence canonical `rawBody`만, `http`은 4xx/5xx만 허용한다.
`http` rawBody가 JSON parse되어 recognized failure-evidence schemaVersion을 가지면
`parseProviderFailureEvidenceV1`→canonical re-stringify→checksum을 모두 검증하고,
그 외 safely redacted text/HTML/malformed JSON은 string body로 허용한다.
`decode|validation` withheld branch에는 body/checksum/parsed가 없고 모든 failed
branch의 `parsed`는 없다. 어떤 local branch에도 transport `parseState` key를
허용하지 않는다.

`ShortformDirectorSourceFetchArtifactValidator`도 generic parse 결과에 멈추지 않는다.
artifact registry encode 경계에서 `provider/purpose`를 읽어 exact Google Trends
refinement 또는 `parseNonGoogleSourceFetchRecordV1`로 dispatch한다. producer가
refinement를 빼먹거나 forged generic success를 넘겨도 registry publication 자체가
실패해야 한다.

A3→local 변환은 명시적 allowlist projection이다.

| A3/provider input | local 저장 |
|---|---|
| parsed 2xx success `ProviderCallAuditV1.response.raw` | 직접 저장 금지. success mapper가 exact source DTO로 projection한 뒤 canonical JSON `rawBody`와 same `parsed` 생성 |
| parsed 4xx/5xx 또는 parsed 2xx known error `response.raw` | 직접 저장 금지. 별도 failure-body projector가 known evidence 또는 generic tagged tree를 만든 뒤 canonical JSON `rawBody`만 생성; local `parsed` 없음 |
| YouTube `nextPageToken` | `pageCursor` |
| Naver `originallink` | `sourceUrl` |
| Naver `bloggername` / `bloggerlink` | `authorName` / `authorUrl` |
| provider `pageInfo.resultsPerPage` | `resultCount` |
| `providerCredentialId`, provider `accessToken`, arbitrary extension keys | drop; artifact에 없음 |

search/comments는 source별 첫 page를 한 번만 호출한다. output `pageCursor`는 그 응답의
`nextPageToken`이 존재했다는 근거를 보여 주기 위한 필드일 뿐 후속 호출에 사용하지
않는다. `YouTubeSearchCallInputV1`, `YouTubeCommentsCallInputV1`과 기존 A3
request DTO/OpenAPI에는 cursor field를 추가하지 않는다.

success mapper도 allowlist projection 전에 failure projector와 같은 iterative
own-data/PEM preflight를 raw object 전체에 적용한다. 나중에 drop할 extension 안의
incomplete boundary도 validation-withheld를 만들고 complete block은 보존되는
allowlist field에서 full-span 제거한다.

success mapper는 projected DTO를 narrow deterministic response redactor에 한 번
전달한다. redactor는 auth scheme/complete private-key PEM/credential-bearing URL을
C1과 같은 B1-compatible marker·query-pair removal로 정제하고 고정 순서
`responseRedactions`를 만든다. 정제된 projected DTO를 canonical stringify한 값만
`rawBody`가 되고 `parsed`는 같은 정제 DTO다. 따라서
`JSON.parse(rawBody)`와 `parsed`가 exact deep-equal이고
`storedBodyChecksum`은 그 `rawBody` UTF-8 bytes로 재계산할 수 있어야 한다.
한 projected field의 redaction은 canonical body와 parsed 복제 때문에 두 번 세지
않는다.

success projection 또는 redaction이 safe body와 safe parsed를 함께 만들지 못하면
`redactionComplete:false`, `error.category:'validation'`의 failed record를 만들고
unsafe `rawBody`/checksum/parsed를 모두 생략한다. A3 wrapper, provider payload,
credential ID, original `nextPageToken` key를 fallback으로 저장하지 않는다. B1 guard,
codec에 provider-specific exception을 추가하지 않는다. C1에서 추출한 shared
sensitive-string classifier를 non-Google redactor도 사용하며 forbidden DTO key set은
그대로 유지한다. failure projector도 같은 classifier를 사용하고 incomplete PEM이나
generic projection failure에는 safe text/object fallback을 만들지 않고 body 전체를
withhold한다.

**Source port and pipeline failure contracts**

```ts
export interface ResearchSourceCallContextV1 {
  researchRunId: string;
  asOf: string;
  attempt: number;
  signal: AbortSignal;
}

export interface ExpectedSourceRecordIdentityV1 {
  researchRunId: string;
  asOf: string;
  attempt: number;
  provider: string;
  purpose: string;
  window?: string;
}

export interface NaverSearchCallInputV1
  extends ResearchSourceCallContextV1 {
  query: string;
  sort: 'date' | 'sim';
  start: number;
  display: number;
}

export interface NaverDataLabCallInputV1
  extends ResearchSourceCallContextV1 {
  phase: 'initial' | 'discovered';
  queryGroups: Array<{ name: string; terms: string[] }>;
  startDate: string;
  endDate: string;
  timeUnit: 'date';
}

export abstract class NaverResearchSource {
  abstract fetchNews(
    input: NaverSearchCallInputV1,
  ): Promise<NaverNewsSourceFetchRecordV1>;
  abstract fetchWeb(
    input: NaverSearchCallInputV1,
  ): Promise<NaverWebSourceFetchRecordV1>;
  abstract fetchBlog(
    input: NaverSearchCallInputV1,
  ): Promise<NaverBlogSourceFetchRecordV1>;
  abstract fetchDataLab(
    input: NaverDataLabCallInputV1,
  ): Promise<NaverDataLabSourceFetchRecordV1>;
}

export type YouTubeSearchLane =
  | 'recent-popular'
  | 'current-popular'
  | 'current-relevant';

export interface YouTubeSearchCallInputV1
  extends ResearchSourceCallContextV1 {
  lane: YouTubeSearchLane;
  query: string;
  publishedAfter: string;
  order: 'viewCount' | 'relevance';
  maxResults: number;
}

export interface YouTubeVideosCallInputV1
  extends ResearchSourceCallContextV1 {
  lane: YouTubeSearchLane;
  videoIds: string[];
}

export interface YouTubeCommentsCallInputV1
  extends ResearchSourceCallContextV1 {
  videoId: string;
  maxResults: number;
}

export abstract class YouTubeResearchSource {
  abstract search(
    input: YouTubeSearchCallInputV1,
  ): Promise<YouTubeSearchSourceFetchRecordV1>;
  abstract fetchVideos(
    input: YouTubeVideosCallInputV1,
  ): Promise<YouTubeVideosSourceFetchRecordV1>;
  abstract fetchComments(
    input: YouTubeCommentsCallInputV1,
  ): Promise<YouTubeCommentsSourceFetchRecordV1>;
}

// Current scope is exactly one first-page call per search/comment input.
// Parsed pageCursor is evidence only; it is never accepted as an input.

export interface ResearchInferenceCallInputV1 {
  purpose:
    | 'query-plan'
    | 'source-normalization'
    | 'youtube-reference-analysis'
    | 'topic-synthesis';
  modelProfile:
    | 'default'
    | 'cost-comparison'
    | 'quality-comparison'
    | 'baseline';
  input: unknown;
  signal: AbortSignal;
}

export abstract class ShortformDirectorResearchInference {
  abstract run(
    input: ResearchInferenceCallInputV1,
  ): Promise<InferenceResultV1>;
}

export const RESEARCH_PIPELINE_FAILURE_ARTIFACT_KIND =
  'research-pipeline-failure' as const;
export const RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE =
  'The research source collection could not be persisted safely.' as const;

export type ResearchPipelineFailureStage =
  | 'source-client'
  | 'record-validation'
  | 'artifact-publish'
  | 'artifact-reload';

export interface ResearchPipelineFailureV1 {
  schemaVersion: 'shortform-director-research-pipeline-failure.v1';
  id: string;
  runId: string;
  code: 'source_collection_pipeline_failed';
  category: 'infrastructure';
  stage: ResearchPipelineFailureStage;
  message: typeof RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE;
  detectedAt: string;
}

export function parseResearchPipelineFailureV1(
  value: unknown,
): ResearchPipelineFailureV1;
```

`signal`은 desktop transport-only field라 A4 JSON body에는 serialize하지 않는다.
query plan, source normalization/query enrichment, YouTube reference analysis, topic
synthesis를 호출하는 모든 application port가 이 input을 사용하고 web API client는
signal을 actual fetch에 전달한다.

`parseResearchPipelineFailureV1`은 exact keys, local run ID, UTC `detectedAt`,
`failure.director.<32 lowercase hex>` ID, 고정 code/category/message와 stage enum을
검사한다. `ShortformDirectorResearchPipelineFailureArtifactValidator`는
`research-pipeline-failure` kind에 이 parser를 적용하고 기존 `run-failure`와
`source-fetch` validator 목록에 append된다.

현재 B1 `publishAndTransitionFailure`는 artifact publish 뒤
`transitionRunning()` 결과가 `null`이어도 성공 descriptor를 반환한다. C2 전에
publisher가 이 값을 fixed
`ShortformDirectorRunTerminalTransitionConflictError`로 표면화하도록 최소 수정한다.
오류는 owner/run/status나 내부 reason/stack을 public payload에 담지 않는다. resolved
publication만 요청한 terminal transition이 실제 적용됐음을 뜻하고, typed conflict를
받은 C2는 durable manifest를 재로드해 이미 이긴 terminal status를 그대로 반환한다.

Start는 active profile admission과 detached snapshot capture를 한 번에 수행하고,
snapshot artifact를 먼저 durable하게 등록한 뒤 snapshot ID를 `inputRefs`로 가진
manifest→run index 순서로 publish한 다음 raw run을 반환한다. 실제 실행은
`ShortformDirectorRunCoordinator`가 owner/run별 `AbortController`와 단일 실행 lock으로
진행한다.

B1 경계는 artifact→manifest→run-index 순서이며 하나의 원자 transaction이 아니다.
publisher rejection 직후 상태를 `running`이나 `failed`로 단정하지 않는다.

| fault 지점 | 가능한 durable state | startup 순서와 결과 |
|---|---|---|
| artifact publish rejection | manifest/run-index는 transition 전 상태다. payload-only orphan, 또는 payload+descriptor가 durable하지만 artifact index만 stale일 수 있다. | artifact reconciliation은 durable descriptor+payload만 index에 복원하고 payload-only orphan은 공개하지 않는다. 이어 run-index reconciliation 뒤 durable manifest가 `running`인 경우에만 recovery가 `process_interrupted`를 기록한다. |
| artifact 성공 뒤 manifest replace rejection | failure artifact는 durable하다. rename/fsync 경계 때문에 manifest는 이전 `running`, 이미 `failed`, 또는 외부 winner의 다른 terminal일 수 있고 run index도 그에 따라 stale할 수 있다. | 두 index를 먼저 reconcile한다. durable manifest가 `running`일 때만 existing recovery marker를 재사용하거나 새 `process_interrupted`를 만든다. 이미 terminal이면 그대로 보존한다. |
| manifest failed replace 성공 뒤 run-index replace rejection | manifest는 requested `failed`+failureRef이고 run index는 old `running` projection이거나 이미 새 projection일 수 있다. | run-index reconciliation이 manifest SoT에서 `failed` projection을 복구한다. 이후 `listRunningForRecovery`가 제외하므로 `process_interrupted`를 추가하지 않는다. |
| `transitionRunning() === null` | 다른 cancel/failure/success transition이 먼저 terminal manifest를 만들었다. 새 failure artifact는 durable orphan일 수 있다. | publisher가 typed terminal-conflict를 reject하고 C2가 consistent terminal manifest를 reload한다. 요청한 failure가 이겼다고 보고하지 않는다. |

- [ ] fake provider 기반 실패 테스트를 먼저 쓴다:
  - profile snapshot을 첫 artifact로 동결
  - archive가 capture보다 먼저 선형화되면 stable 409이고 artifact/manifest/index 0건
  - capture가 먼저 선형화되면 뒤 PATCH/archive와 무관하게 frozen snapshot으로 진행
  - 과거 run 표시가 live/archived profile을 다시 읽지 않고 snapshot만 사용
  - 선택적으로 등록한 user source만 `UserPinnedSource`로 포함하고 없어도 완주
  - query-plan inference 결과와 실제 source별 query 저장
  - research run 시작 때 UTC `asOf`를 한 번 동결하고 모든 source parse에 같은 값 전달
  - Google Trends `4h/24h/48h/7d`가 서로 독립 호출되고 각기 별도
    `SourceFetchRecordV1`과 immutable artifact를 가짐
  - Naver news/web/blog/initial·discovered DataLab 각각에
    researchRunId/asOf/attempt/signal과 query/phase를 전달하고 반환 record identity가
    input과 일치
  - YouTube search 3 lane 각각, lane별 videos.list 1..50 ID batch 각각, ranking 뒤
    선택 video의 comments single-video 호출 각각이 별도 fetch→persist→reload
  - `fetchAllLanes` 또는 adapter 한 메서드 안에서 여러 HTTP 호출을 숨기지 않음
  - YouTube search/comments는 first page 한 번만 호출하고 input/A3 DTO에 cursor가
    없으며 output `pageCursor`로 follow-up 요청을 만들지 않음
  - A3 no-response/received-incomplete/complete-undecodable/
    decoded-not-attempted/parse-failed/parsed/redaction-failed branch가 exact-key와
    `?:never`를 지킴
  - A3 audit의 actual `received/status/contentType/bytesReceived/complete/decoded`는
    선택된 local branch에 정직하게 보존하고 C2가 wire metadata를 canonical body
    길이로 합성하지 않음. transport-only `parseState`는 local response/artifact 어디에도
    없고 extra key로 주입하면 runtime parser가 reject
  - priority table의 모든 overlap fixture: undecodable 500은 decode, redaction-failed
    500은 validation, safe decoded 400/500은 parseState와 무관하게 http, 2xx
    parse-failed는 parse, 2xx not-attempted는 content-type, 2xx known error는 provider,
    2xx valid DTO는 succeeded, 2xx schema mismatch는 validation
  - A3 status 4xx/5xx와 `provider_4xx/provider_5xx` failure kind 불일치는 transport
    parser가 reject하고 C2 category는 failure message가 아니라 validated status/priority로
    결정
  - response header 뒤 partial read·timeout·caller abort·stream oversize가 실제
    accumulated bytes와 incomplete를 보존하고 no-response에는 status/content/body
    metadata가 없음
  - `application/json` invalid UTF-8 complete bytes는 fatal decode 뒤 raw/base64 없이
    withheld+`receivedBodyChecksum`; valid UTF-8 malformed JSON은 safely redacted text,
    decoded/parse-failed와 local rawBody/stored checksum을 보존
  - malformed JSON raw text의 `"authorization":"Bearer x"`,
    `'authorization':'Basic dTpw'`, `authorization=Bearer x`가 web A3 redactor에서
    scheme+candidate만 제거되고 key/quote/separator/나머지 text는 보존
  - complete one/multiple PEM은 web A3/C1/C2 redactor에서 BEGIN+body+matching END
    전체가 block당 `[removed]` 하나이고 missing/mismatched/nested/extra/malformed
    boundary는 redaction incomplete로 whole body withheld
  - success/failure allowlist가 drop할 unknown extension 안 incomplete PEM도 full-tree
    preflight가 검출해 validation-withheld이고 partial projected body가 없음
  - A3 public audit, local payload/descriptor/index 어디에도 invalid credentialed bytes
    또는 그 base64가 없음
  - A3 `ProviderCallAuditV1`, `providerCredentialId`, `response.raw` object를 artifact로
    직접 저장하지 않고 source별 exact mapper만 통과
  - Naver 4xx/5xx `{errorCode,errorMessage,...extension}`와 YouTube 4xx/5xx
    `{error:{code,status,message,errors,...extension},...extension}`가 known failure
    DTO로 projection되고 local category는 모두 http, safe code/summary/reason은 보존,
    extension은 omitted count에 반영, local `parsed`는 없음
  - 같은 known Naver/YouTube error envelope가 2xx면 category provider이고 exact
    success DTO보다 먼저 판정하며, 2xx unknown object는 generic fallback 없이
    validation-withheld
  - parsed 4xx/5xx unknown JSON은 bounded generic tagged scalar/list/map
    `{entries:[{name,value}]}` evidence가 되고 arbitrary provider key가 local JSON key로
    승격하지 않음
  - generic limits depth 6/nodes+entries 48/container 16/name 64/text 160/canonical
    64 KiB와 deterministic omission/truncation counters를 exact boundary fixture로 검증
  - failure fixture의 `raw`, `nextPageToken`, `accessToken`, `clientSecret`, credential
    URL, auth string, complete PEM, injected sentinel과 unknown extension을 넣는다.
    known projector는 extension/sensitive normalized key를 drop/redact하고 generic
    projector는 forbidden name을 entry째 drop한다. incomplete PEM은 projection 실패
  - Naver news/web/blog/DataLab과 YouTube search/videos/comments fixture를 각각
    allowlist DTO로 projection하고 `nextPageToken→pageCursor`,
    `originallink→sourceUrl`, `bloggername/link→authorName/Url` 변환
  - success fixture의 unknown provider extension, credential/token suffix key,
    credential-bearing URL, auth/PEM을 drop/redact하고 harmless title/text/URL/count는
    보존
  - C1의 exact shared fixture table—짧은 Authorization header, prefix/JWT/
    24자 punctuation-mixed/32자 mixed-case Bearer, canonical printable
    `user:password` Basic, complete/incomplete PEM, credential URL,
    raw·percent·form exact sensitive value—을 B1 guard/C1/C2 redactor에 그대로
    적용해 같은 민감 판정을 내림
  - 같은 fixture를 web A3 redactor에도 적용하고 natural-language
    `"note":"Bearer Stearns outlook"`, `"note":"Basic skincare guide"`는 모든
    redactor에서 byte/value 그대로 보존
  - 각 Naver 4개·YouTube 3개 source method가 actual B1
    codec→registry publish→reload를 통과하며 persisted payload/descriptor/index에
    transport wrapper, original forbidden key, secret sentinel이 없음
  - Naver/YouTube known/generic 4xx/5xx failure evidence도 actual B1
    codec→registry→reload 뒤 safe code/message/reason, omission/redaction summary와
    post-redaction checksum을 보존하고 original sensitive field/value/sentinel,
    `response.raw`, fake success `parsed`가 없음
  - `source-fetch` public artifact validator가 provider/purpose에 따라
    Google/non-Google refinement를 dispatch하고 forged generic success, wrong
    purpose/schema/lane/phase/videoId를 registry encode 시점에 거부
  - non-Google success는 `JSON.parse(rawBody)`와 exact parsed DTO가 deep-equal이고
    responseRedactions와 post-redaction rawBody checksum을 reload 뒤 재검증
  - mapper/redactor 어느 한쪽이라도 safe rawBody+parsed pair를 만들지 못하면
    redactionComplete false validation failed record이고 unsafe body/checksum/parsed가
    동시에 없음
  - 모든 non-Google source의 expected network/HTTP/content/parser/provider 실패는
    rejected promise가 아니라 strict failed SourceFetchRecord로 반환
  - fulfilled failed source record는 다른 출처를 막지 않지만 rejected settlement는
    source collection/persistence pipeline failure로 run을 abort하고 `failed` 전환
  - source client가 반환한 success/failed record를 완료 즉시 저장하고 registry에서
    재로드·runtime parse한 값 중 succeeded record만 normalizer가 소비
  - fulfilled failed record는 별도 failure collection과 manifest failureRefs/status
    계산에만 사용하고 normalizer 입력에서 제외
  - Google Trends XML parser 실패도 valid UTF-8 complete
    rawBody/storedBodyChecksum과 top-level asOf/window를 가진 failed artifact로 남고
    다른 window/source는 계속
  - 저장 또는 재로드 검증 실패는 rejected settlement가 되어 메모리 record로
    우회하거나 ordinary partial로 낮추지 않음
  - unexpected client throw, runtime record parser, artifact publish/reload rejection은
    first-failure latch가 stage/detectedAt만 고정하고 raw rejection message/stack은
    artifact/logger에 저장하지 않음
  - pipeline rejection은 exact `research-pipeline-failure` artifact를
    `publishAndTransitionFailure(...status:'failed')`로 먼저 저장·전환
  - artifact/manifest/run-index 각 publish fault에서 rejection 직후 status를
    단정하지 않고 startup artifact→run-index reconciliation 뒤 durable manifest가
    running인 경우에만 `process_interrupted`
  - manifest는 failed지만 run index가 stale running인 fault는 reconciliation이 failed
    projection을 복구하고 recovery artifact를 추가하지 않음
  - `transitionRunning()===null`을 publisher가 fixed typed terminal conflict로
    reject하고 coordinator가 실제 terminal manifest를 reload해 requested failure를
    성공으로 오인하지 않음
  - owner/run coordinator 중복 실행은 single execution lock으로 거부하고 cancel은
    controller를 즉시 abort한 뒤 같은 terminalization 경계에 합류
  - abort intent first-writer-wins: cancel 먼저면 뒤 unexpected rejection이
    pipeline-failure로 승격하지 않고, pipeline-failure 먼저면 뒤 DELETE가 cancel로
    덮지 않으며, repeated cancel은 idempotent
  - common abort-or-terminal gate를 각 source wave 직후, normalization 직전,
    query-enrichment inference 직전/직후, topic inference 직전/직후, artifact
    publication 직전, final terminal transition 직전에 호출
  - query plan/source normalization/YouTube reference/topic synthesis 모든 inference
    port input이 필수 signal을 받고 transport가 actual fetch에 전달
  - inference pre-gate 직후 cancel은 transport abort로 중단되고 provider가 거의 동시에
    반환해도 post-gate가 새 inference/output artifact publication을 막음
  - durable cancel/external terminal winner 뒤에는 normalization, 새 LLM 호출,
    output/failure attach, final status overwrite가 0건
  - profile archive는 snapshot admission 전에 이기면 stable 409, snapshot capture 뒤
    이기면 frozen run을 바꾸지 않으며, 외부/cancel terminal transition이 먼저 이기면
    C2는 그 durable status를 보존
  - fulfilled cancelled record가 하나라도 있으면 새 작업을 중단하고 manifest를
    `cancelled`로 전환하며 normalizer/LLM을 시작하지 않음
  - 새 연관 검색어를 모은 뒤 second DataLab 호출
  - initial/discovered DataLab 모두 최근 기간과 직전 비교 기간을 같은 길이로 조회
  - top 20~30 YouTube만 reference analysis
  - 발견 entity/claim마다 `공식`, `공식 발표`, `보도자료`, `출시` query를 자동
    확장하고 official/authoritative source를 교차 확인
  - cancel이 새 provider call을 중단하고 manifest를 `cancelled`로 전환
  - 프로세스 재시작 recovery가 `running`을 성공으로 꾸미지 않음
- [ ] YouTube ranking 테스트:
  - 7일/viewCount, 30일/viewCount, 14일/relevance lane
  - `order=date` 없음
  - 시간당 조회, engagement, channel cap, 중복 URL/title 제거
  - 오래된 누적 인기 영상은 `background/reference`만 가능
- [ ] 정규화 테스트:
  - source별 `EvidenceItemV1`
  - publishedAt/collectedAt/asOf/freshness
  - fact/market/audience/reference role 분리
  - YouTube 기본 `rightsRole='analysis-only'`
  - official/primary source 자동 분류와 claim 연결
- [ ] topic validator 테스트:
  - evidence 없는 topic 거부
  - `whyNow`가 최근 evidence ID와 연결되지 않으면 거부
  - 프로필 무관/중복 topic 거부
  - rejected topic과 이유도 파일에 남음
- [ ] RED 확인:

```bash
# web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-research/application/bounded-provider-fetch.service.spec.ts \
  src/modules/shortform-director-research/application/provider-call-audit.factory.spec.ts \
  src/modules/shortform-director-research/application/provider-call-audit.redactor.spec.ts \
  src/modules/shortform-director-research/application/naver-research-provider.service.spec.ts \
  src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts \
  src/modules/shortform-director-research/presentation/shortform-director-research.controller.spec.ts \
  src/modules/shortform-director-research/presentation/shortform-director-research.openapi.spec.ts

# desktop/clipper_nestjs
npm run build
node --test test/shortform-director-run-storage.test.js
node --test test/shortform-director-non-google-source-fetch.test.js
node --test test/shortform-director-provider-failure-body.test.js
node --test test/shortform-director-research-run.test.js
node --test test/shortform-director-topic-validation.test.js
node --test test/shortform-director-research-api.test.js
```

- [ ] 모든 credential 필요 호출에는 bearer token만 넘긴다. local research run ID는
  로컬 계보의 상위 ID로만 쓰고 billing/operation API에는 전달하지 않는다.
- [ ] 실행 순서를 다음으로 구현한다.

```ts
const {
  id: runId,
  ownerSubjectId,
  startedAt: asOf,
} = researchRunIdentitySnapshot;
const signal = runAbortController.signal;
const sourceIdentity = {
  researchRunId: runId,
  asOf,
  attempt: 1,
};
const sourceContext: ResearchSourceCallContextV1 = {
  ...sourceIdentity,
  signal,
};

type RunAbortIntent = 'active' | 'cancel' | 'pipeline-failure';
type AbortOrTerminalGateResult =
  | { kind: 'continue' }
  | { kind: 'pipeline-failure' }
  | { kind: 'terminal'; manifest: LocalRunManifestV1 };

let runAbortIntent: RunAbortIntent = 'active';
let firstPipelineFailure:
  | { stage: ResearchPipelineFailureStage; detectedAt: string }
  | undefined;

const latchRunAbortIntent = (
  requested: Exclude<RunAbortIntent, 'active'>,
): RunAbortIntent => {
  if (runAbortIntent === 'active') runAbortIntent = requested;
  return runAbortIntent;
};

const rejectPipeline = (stage: ResearchPipelineFailureStage): never => {
  firstPipelineFailure ??= { stage, detectedAt: wallClock() };
  latchRunAbortIntent('pipeline-failure');
  runAbortController.abort();
  throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
};

const parseSourceRecordForExpected = (
  value: unknown,
  expected: ExpectedSourceRecordIdentityV1,
): SourceFetchRecordV1 => (
  expected.provider === 'google-trends'
    ? parseSourceFetchRecordV1(value)
    : parseNonGoogleSourceFetchRecordV1(value)
);

const requireDurableTerminalManifest = async (
  expectedOwnerSubjectId: string,
  expectedRunId: string,
): Promise<LocalRunManifestV1> => {
  const manifest = await runRepository.get(
    expectedOwnerSubjectId,
    expectedRunId,
  );
  if (manifest === null || manifest.status === 'running') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }
  return manifest;
};

const abortOrTerminalGateUnlocked =
  async (): Promise<AbortOrTerminalGateResult> => {
    const manifest = await runRepository.get(ownerSubjectId, runId);
    if (manifest === null) {
      throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
    }
    if (manifest.status !== 'running') {
      runAbortController.abort();
      return { kind: 'terminal', manifest };
    }
    if (!signal.aborted) return { kind: 'continue' };
    if (runAbortIntent === 'pipeline-failure') {
      return { kind: 'pipeline-failure' };
    }
    if (runAbortIntent !== 'cancel') {
      throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
    }
    const transitioned = await runRepository.transitionRunning(
      ownerSubjectId,
      runId,
      'cancelled',
      { finishedAt: wallClock() },
    );
    return {
      kind: 'terminal',
      manifest: transitioned ?? await requireDurableTerminalManifest(
        ownerSubjectId,
        runId,
      ),
    };
  };

const abortOrTerminalGate = (): Promise<AbortOrTerminalGateResult> => (
  runTerminalizationLock.with(
    ownerSubjectId,
    runId,
    abortOrTerminalGateUnlocked,
  )
);

class ResearchRunTerminalGateError extends Error {
  constructor(readonly manifest: LocalRunManifestV1) {
    super('Research run is already terminal.');
  }
}

const withRunningPublicationGate = async <T>(
  publish: () => Promise<T>,
): Promise<T> => runTerminalizationLock.with(
  ownerSubjectId,
  runId,
  async () => {
    const gate = await abortOrTerminalGateUnlocked();
    if (gate.kind === 'terminal') {
      throw new ResearchRunTerminalGateError(gate.manifest);
    }
    if (gate.kind === 'pipeline-failure') {
      throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
    }
    return publish();
  },
);

const fetchPersistReload = async (
  expected: ExpectedSourceRecordIdentityV1,
  fetchRecord: () => Promise<unknown>,
): Promise<SourceFetchRecordV1> => {
  const beforeFetch = await abortOrTerminalGate();
  if (beforeFetch.kind === 'terminal') {
    throw new ResearchRunTerminalGateError(beforeFetch.manifest);
  }
  if (beforeFetch.kind === 'pipeline-failure') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }

  let returned: unknown;
  try {
    returned = await fetchRecord();
  } catch {
    return rejectPipeline('source-client');
  }

  let record: SourceFetchRecordV1;
  try {
    record = parseSourceRecordForExpected(returned, expected);
    assertSourceRecordIdentity(record, expected);
  } catch {
    return rejectPipeline('record-validation');
  }

  let descriptor: PublicArtifactDescriptorV1;
  try {
    descriptor = await withRunningPublicationGate(
      () => lineagePublisher.publishAndAttachJson({
        ownerSubjectId,
        runId,
        kind: 'source-fetch',
        value: record,
        entityRefs: [{
          entityType: 'source-fetch',
          entityId: record.id,
          role: 'contains',
        }],
        target: record.status === 'failed' ? 'failure' : 'output',
      }),
    );
  } catch (error) {
    if (error instanceof ResearchRunTerminalGateError) throw error;
    return rejectPipeline('artifact-publish');
  }

  try {
    const persisted = await artifactRegistry.readJson(
      ownerSubjectId,
      descriptor.id,
    );
    const reloaded = parseSourceRecordForExpected(
      persisted.value,
      expected,
    );
    assertSourceRecordIdentity(reloaded, expected);
    return reloaded;
  } catch {
    return rejectPipeline('artifact-reload');
  }
};

const publishPipelineFailure = async (
  failure: { stage: ResearchPipelineFailureStage; detectedAt: string },
): Promise<{ terminal: true; manifest: LocalRunManifestV1 }> => {
  const value = parseResearchPipelineFailureV1({
    schemaVersion: 'shortform-director-research-pipeline-failure.v1',
    id: failureIdFactory(),
    runId,
    code: 'source_collection_pipeline_failed',
    category: 'infrastructure',
    stage: failure.stage,
    message: RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE,
    detectedAt: failure.detectedAt,
  });
  let descriptor: PublicArtifactDescriptorV1 | undefined;
  let gateWinner: LocalRunManifestV1 | undefined;
  let terminalRace = false;
  try {
    await runTerminalizationLock.with(ownerSubjectId, runId, async () => {
      const gate = await abortOrTerminalGateUnlocked();
      if (gate.kind === 'terminal') {
        gateWinner = gate.manifest;
        return;
      }
      if (gate.kind !== 'pipeline-failure') {
        throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
      }
      descriptor = await lineagePublisher.publishAndTransitionFailure({
        ownerSubjectId,
        runId,
        kind: RESEARCH_PIPELINE_FAILURE_ARTIFACT_KIND,
        value,
        entityRefs: [{
          entityType: 'run',
          entityId: runId,
          role: 'failure',
        }],
        status: 'failed',
        finishedAt: failure.detectedAt,
      });
    });
  } catch (error) {
    if (!(error instanceof ShortformDirectorRunTerminalTransitionConflictError)) {
      throw error;
    }
    terminalRace = true;
  }

  if (gateWinner !== undefined) {
    return { terminal: true, manifest: gateWinner };
  }
  const manifest = await requireDurableTerminalManifest(
    ownerSubjectId,
    runId,
  );
  if (
    !terminalRace
    && (
      manifest.status !== 'failed'
      || descriptor === undefined
      || !manifest.failureRefs.includes(descriptor.id)
    )
  ) {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }
  return { terminal: true, manifest };
};

const requestResearchCancel = async (): Promise<{
  terminal: true;
  manifest: LocalRunManifestV1;
}> => {
  const winningIntent = latchRunAbortIntent('cancel');
  runAbortController.abort();
  if (winningIntent === 'pipeline-failure') {
    if (firstPipelineFailure === undefined) {
      throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
    }
    return publishPipelineFailure(firstPipelineFailure);
  }
  const gate = await abortOrTerminalGate();
  if (gate.kind !== 'terminal') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }
  return { terminal: true, manifest: gate.manifest };
};

type GatedValue<T> =
  | { terminal: true; manifest: LocalRunManifestV1 }
  | { terminal: false; value: T };

const runSynchronousStageUnderGate = async <T>(
  stage: () => T,
): Promise<GatedValue<T>> => runTerminalizationLock.with(
  ownerSubjectId,
  runId,
  async () => {
    const gate = await abortOrTerminalGateUnlocked();
    if (gate.kind === 'terminal') {
      return { terminal: true, manifest: gate.manifest };
    }
    if (gate.kind === 'pipeline-failure') {
      throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
    }
    return { terminal: false, value: stage() };
  },
);

const runInferenceBetweenGates = async (
  input: Omit<ResearchInferenceCallInputV1, 'signal'>,
): Promise<GatedValue<InferenceResultV1>> => {
  const before = await abortOrTerminalGate();
  if (before.kind === 'terminal') {
    return { terminal: true, manifest: before.manifest };
  }
  if (before.kind === 'pipeline-failure') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }

  let returned: InferenceResultV1;
  try {
    returned = await researchInference.run({ ...input, signal });
  } catch (error) {
    const afterError = await abortOrTerminalGate();
    if (afterError.kind === 'terminal') {
      return { terminal: true, manifest: afterError.manifest };
    }
    throw error;
  }

  const after = await abortOrTerminalGate();
  if (after.kind === 'terminal') {
    return { terminal: true, manifest: after.manifest };
  }
  if (after.kind === 'pipeline-failure') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }

  const persisted = await withRunningPublicationGate(
    () => publishAndReloadInferenceResult(returned),
  );
  return { terminal: false, value: persisted };
};

const settleDurableWave = async (
  tasks: Array<Promise<SourceFetchRecordV1>>,
): Promise<
  | { terminal: true; manifest: LocalRunManifestV1 }
  | {
      terminal: false;
      succeeded: SourceFetchSucceededRecordV1[];
      failed: SourceFetchFailedRecordV1[];
    }
> => {
  const settled = await Promise.allSettled(tasks);
  const gatedTerminal = settled.find(
    (entry): entry is PromiseRejectedResult => (
      entry.status === 'rejected'
      && entry.reason instanceof ResearchRunTerminalGateError
    ),
  );
  if (gatedTerminal !== undefined) {
    return {
      terminal: true,
      manifest: gatedTerminal.reason.manifest,
    };
  }
  if (settled.some(({ status }) => status === 'rejected')) {
    return publishPipelineFailure(firstPipelineFailure ?? {
      stage: 'source-client',
      detectedAt: wallClock(),
    });
  }

  const records = settled.map((entry) => {
    if (entry.status === 'rejected') {
      throw new Error('unreachable after rejected settlement gate');
    }
    return entry.value;
  });
  const cancelled = records.filter(
    (record): record is SourceFetchFailedRecordV1 =>
      record.status === 'failed' && record.error.category === 'cancelled',
  );
  if (cancelled.length > 0) {
    return requestResearchCancel();
  }

  const postWaveGate = await abortOrTerminalGate();
  if (postWaveGate.kind === 'terminal') {
    return { terminal: true, manifest: postWaveGate.manifest };
  }
  if (postWaveGate.kind === 'pipeline-failure') {
    return publishPipelineFailure(firstPipelineFailure ?? {
      stage: 'source-client',
      detectedAt: wallClock(),
    });
  }

  return {
    terminal: false,
    succeeded: records.filter(
      (record): record is SourceFetchSucceededRecordV1 =>
        record.status === 'succeeded',
    ),
    failed: records.filter(
      (record): record is SourceFetchFailedRecordV1 =>
        record.status === 'failed',
    ),
  };
};

const trendsWindows = ['4h', '24h', '48h', '7d'] as const;
const youtubeSearchSpecs = [
  {
    lane: 'recent-popular',
    publishedAfter: sevenDaysAgo,
    order: 'viewCount',
  },
  {
    lane: 'current-popular',
    publishedAfter: thirtyDaysAgo,
    order: 'viewCount',
  },
  {
    lane: 'current-relevant',
    publishedAfter: fourteenDaysAgo,
    order: 'relevance',
  },
] as const;

const queryPlanStep = await runInferenceBetweenGates({
  purpose: 'query-plan',
  modelProfile: 'default',
  input: buildQueryPlanInput(frozenProfileSnapshot),
});
if (queryPlanStep.terminal) return queryPlanStep.manifest;
const parsedQueryPlanStep = await runSynchronousStageUnderGate(
  () => parseQueryPlan(queryPlanStep.value.output),
);
if (parsedQueryPlanStep.terminal) return parsedQueryPlanStep.manifest;
const queryPlan = parsedQueryPlanStep.value;

const discoveryWave = await settleDurableWave([
  ...trendsWindows.map((window) => fetchPersistReload({
    ...sourceIdentity,
    provider: 'google-trends',
    purpose: 'trending-rss',
    window,
  }, () => trends.fetchRss({ ...sourceContext, window }))),
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'naver',
    purpose: 'naver-news',
  }, () => naver.fetchNews({ ...queryPlan.naverNews, ...sourceContext })),
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'naver',
    purpose: 'naver-web',
  }, () => naver.fetchWeb({ ...queryPlan.naverWeb, ...sourceContext })),
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'naver',
    purpose: 'naver-blog',
  }, () => naver.fetchBlog({ ...queryPlan.naverBlog, ...sourceContext })),
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'naver',
    purpose: 'naver-datalab-initial',
  }, () => naver.fetchDataLab({
    ...queryPlan.initialDataLab,
    phase: 'initial',
    ...sourceContext,
  })),
  ...youtubeSearchSpecs.map((spec) => fetchPersistReload({
    ...sourceIdentity,
    provider: 'youtube',
    purpose: `youtube-search-${spec.lane}`,
  }, () => youtube.search({
    ...spec,
    query: queryPlan.youtube,
    maxResults: 50,
    ...sourceContext,
  }))),
]);
if (discoveryWave.terminal) return discoveryWave.manifest;

const youtubeSearchResults = discoveryWave.succeeded.filter(
  isYouTubeSearchRecord,
);
const videoBatches = youtubeSearchResults.flatMap((record) => (
  chunk(extractVideoIds(record), 50).map((videoIds) => ({
    lane: extractYouTubeLane(record),
    videoIds,
  }))
));
const videosWave = await settleDurableWave(videoBatches.map((batch) => (
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'youtube',
    purpose: `youtube-videos-${batch.lane}`,
  }, () => youtube.fetchVideos({ ...batch, ...sourceContext }))
)));
if (videosWave.terminal) return videosWave.manifest;

const rankedVideosStep = await runSynchronousStageUnderGate(
  () => rankYouTubeVideos(videosWave.succeeded).slice(0, 30),
);
if (rankedVideosStep.terminal) return rankedVideosStep.manifest;
const selectedVideos = rankedVideosStep.value;

const youtubeReferenceStep = await runInferenceBetweenGates({
  purpose: 'youtube-reference-analysis',
  modelProfile: 'default',
  input: buildYouTubeReferenceAnalysisInput(selectedVideos),
});
if (youtubeReferenceStep.terminal) return youtubeReferenceStep.manifest;
const parsedYouTubeReferencesStep = await runSynchronousStageUnderGate(
  () => parseYouTubeReferenceAnalysis(
    youtubeReferenceStep.value.output,
    selectedVideos,
  ),
);
if (parsedYouTubeReferencesStep.terminal) {
  return parsedYouTubeReferencesStep.manifest;
}
const youtubeReferences = parsedYouTubeReferencesStep.value;

const commentsWave = await settleDurableWave(selectedVideos.map(({ videoId }) => (
  fetchPersistReload({
    ...sourceIdentity,
    provider: 'youtube',
    purpose: 'youtube-comments',
  }, () => youtube.fetchComments({
    videoId,
    maxResults: 100,
    ...sourceContext,
  }))
)));
if (commentsWave.terminal) return commentsWave.manifest;

const preliminarySucceeded = [
  ...discoveryWave.succeeded,
  ...videosWave.succeeded,
  ...commentsWave.succeeded,
];
const beforeDiscoveryNormalization = await abortOrTerminalGate();
if (beforeDiscoveryNormalization.kind === 'terminal') {
  return beforeDiscoveryNormalization.manifest;
}
if (beforeDiscoveryNormalization.kind === 'pipeline-failure') {
  return (await publishPipelineFailure(firstPipelineFailure!)).manifest;
}
const discoveredGroupsStep = await runSynchronousStageUnderGate(
  () => buildDiscoveredDataLabGroups(
    normalizer.normalize(preliminarySucceeded),
  ),
);
if (discoveredGroupsStep.terminal) return discoveredGroupsStep.manifest;
const discoveredGroups = discoveredGroupsStep.value;
const discoveredDataLabWave = await settleDurableWave(
  chunk(discoveredGroups, NAVER_DATALAB_GROUP_LIMIT).map((queryGroups) => (
    fetchPersistReload({
      ...sourceIdentity,
      provider: 'naver',
      purpose: 'naver-datalab-discovered',
    }, () => naver.fetchDataLab({
      ...queryPlan.dataLabPeriod,
      phase: 'discovered',
      queryGroups,
      ...sourceContext,
    }))
  )),
);
if (discoveredDataLabWave.terminal) {
  return discoveredDataLabWave.manifest;
}

const succeededRecords = [
  ...preliminarySucceeded,
  ...discoveredDataLabWave.succeeded,
];
const failedSourceRecords = [
  ...discoveryWave.failed,
  ...videosWave.failed,
  ...commentsWave.failed,
  ...discoveredDataLabWave.failed,
];
const beforeNormalization = await abortOrTerminalGate();
if (beforeNormalization.kind === 'terminal') {
  return beforeNormalization.manifest;
}
if (beforeNormalization.kind === 'pipeline-failure') {
  return (await publishPipelineFailure(firstPipelineFailure!)).manifest;
}
const evidenceStep = await runSynchronousStageUnderGate(
  () => normalizer.normalize(succeededRecords),
);
if (evidenceStep.terminal) return evidenceStep.manifest;
const evidence = evidenceStep.value;
const enrichmentStep = await runInferenceBetweenGates({
  purpose: 'source-normalization',
  modelProfile: 'default',
  input: buildQueryEnrichmentInput(evidence, youtubeReferences),
});
if (enrichmentStep.terminal) return enrichmentStep.manifest;
const enrichedStep = await runSynchronousStageUnderGate(
  () => parseEnrichedEvidence(enrichmentStep.value.output, evidence),
);
if (enrichedStep.terminal) return enrichedStep.manifest;
const enriched = enrichedStep.value;

const topicStep = await runInferenceBetweenGates({
  purpose: 'topic-synthesis',
  modelProfile: 'default',
  input: buildTopicSynthesisInput(enriched),
});
if (topicStep.terminal) return topicStep.manifest;
const topicsStep = await runSynchronousStageUnderGate(
  () => validateTopics(topicStep.value.output, enriched),
);
if (topicsStep.terminal) return topicsStep.manifest;
const topics = topicsStep.value;

return runTerminalizationLock.with(ownerSubjectId, runId, async () => {
  const beforeFinalTransition = await abortOrTerminalGateUnlocked();
  if (beforeFinalTransition.kind === 'terminal') {
    return beforeFinalTransition.manifest;
  }
  if (beforeFinalTransition.kind === 'pipeline-failure') {
    throw new Error(RESEARCH_PIPELINE_FAILURE_PUBLIC_MESSAGE);
  }
  return finalizeResearchRunStatus({ topics, failedSourceRecords });
});
```

- [ ] 위 `researchRunIdentitySnapshot`는 B1 repository에서 manifest를 durable
  create한 뒤 재로드해 얻은 immutable `id/ownerSubjectId/startedAt` snapshot이다.
  manifest JSON 전체가 immutable하다는 뜻이 아니며 status/outputRefs/failureRefs는 B1
  전환 계약으로 갱신된다. `runAbortController`는 caller cancel을 결합한 run-level
  controller고, `asOf`는 snapshot의 `startedAt` 외 다른 clock에서 다시 만들지 않는다.
- [ ] A3 OpenAPI/domain/bounded fetch/factory/redactor/test를 먼저 갱신한다.
  bounded fetch는 header 전 no-response, header 뒤 actual accumulated-byte incomplete,
  fatal UTF-8 complete을 구분한다. factory는 위 exact response union만 만들며 invalid
  UTF-8은 raw/base64 없는 withheld+received checksum, valid UTF-8 malformed JSON은
  safely redacted text+parse-failed, redaction 실패는 body 없는 withheld state다.
  desktop web API client는 JWT transport와 fixed A3 success/error parsing만 담당하며
  web audit wrapper를 artifact registry에 노출하지 않는다.
- [ ] `shortform-director-provider-audit.mapper.ts`는 source별 provider payload
  allowlist projection, request/identity 조립, 위 표의 A3 exact
  no-response/incomplete/undecodable/decoded-unparsed/parse-failed/parsed/
  redaction-failed→local state/category priority 변환만 담당한다. wire status, actual
  bytesReceived, complete/decoded를 바꾸거나 canonical body 길이로 합성하지 않는다.
  A3 `parseState`는 branch 선택 뒤 소거하고 local DTO에 넣지 않는다. non-Google
  redactor는 shared B1 classifier를 호출한 string/URL/PEM 정제와 summary만, domain
  refinement는 exact DTO/identity/checksum만 담당한다. 서로 provider HTTP 호출이나
  artifact I/O를 수행하지 않는다.
- [ ] `shortform-director-provider-failure-body.projector.ts`는 4xx/5xx parsed body와
  2xx known error envelope만 맡는다. Naver/YouTube known allowlist projector 뒤
  4xx/5xx unknown shape에만 bounded tagged-tree fallback을 적용한다. canonical failure
  evidence, checksum, redaction summary를 함께 반환하거나 whole body를 withhold하며
  success DTO mapper, transport, artifact I/O는 수행하지 않는다. failed local record에
  `parsed`를 만들지 않고 arbitrary `response.raw` object를 stringify하지 않는다.
- [ ] 각 network source client는 transport와 parser/schema validation까지 끝낸 strict
  `SourceFetchRecordV1`을 반환한다. expected network/HTTP/content/parser/provider
  실패와 caller cancel은 rejected promise가 아니라 strict failed record다.
  unexpected client throw만 `source-client` pipeline rejection이다. coordinator는 각
  promise 내부에서 반환값을 runtime parse하고
  `researchRunId/asOf/attempt/provider/purpose/window` identity를 call input과 비교한
  뒤 즉시 immutable JSON으로 기록한다. registry에서 재로드한 값도 같은 parser와
  identity 검사를 통과해야 한다. required query/lane/phase/batch/video input과 실제
  provider request 일치는 각 adapter contract test가 검증한다.
  저장 전 client 반환값이나 저장 실패 뒤 메모리 fallback으로
  정규화·inference를 시작하지 않는다.
- [ ] non-Google success는 source별 exact `NonGoogleParsedV1` branch만 허용한다.
  provider response의 임의 key를 재귀 복사하지 않고 source allowlist field와
  `nextPageToken→pageCursor` 같은 명시 rename만 적용한다. canonical safe body와
  parsed는 동일 projected DTO에서 파생하고 redaction summary/checksum을 reload 시
  재검증한다. pair 정제에 실패하면 둘 다 생략한 validation failed record다. B1
  persistence guard와 codec에는 예외를 추가하지 않는다.
- [ ] `ShortformDirectorSourceFetchArtifactValidator`는 `source-fetch` kind에서
  provider/purpose를 fail-closed로 분기해 Google refinement 또는 non-Google
  refinement를 호출한다. producer-only validation에 의존하지 않으며 wrong
  source/schema/purpose fixture가 actual registry `registerJson`에서 reject되는
  contract test를 둔다.
- [ ] `fetchPersistReload` rejection은 즉시 `runAbortController`를 abort해 sibling
  network 작업을 중단한다. `Promise.allSettled` rejected가 하나라도 있으면
  first-failure latch의 고정 stage/detectedAt으로
  `parseResearchPipelineFailureV1`을 통과한 exact artifact를 만들고 실제 B1
  `publishAndTransitionFailure(..., status:'failed')` 한 경계에서
  artifact publish·failureRefs·manifest status/finishedAt을 전환한다. rejected reason
  원문과 stack은 artifact/logger에 복사하지 않으며 ordinary source partial로
  낮추거나 이후 정규화로 진행하지 않는다. publisher I/O rejection은 durable status를
  단정하지 않고 outer coordinator로 전파한다. startup은 artifact index→run index
  순서로 reconcile한 뒤 durable manifest가 `running`일 때만
  `process_interrupted`를 적용한다. durable manifest가 terminal이면 그 status를
  보존한다.
- [ ] B1 publisher는 `transitionRunning()`의 nullable result를 검사하고 `null`이면
  fixed typed terminal-conflict를 reject한다. C2는 이 오류만 actual manifest reload로
  해소하고, 다른 rejection을 terminal success로 바꾸지 않는다. artifact/manifest/index
  fault injection과 concurrent cancel/failure/success winner test를 B1 storage test에
  추가한다.
- [ ] fulfilled record는 persisted `status/error.category`로 다시 나눈다.
  cancelled가 하나라도 있으면 `requestResearchCancel`이 first-writer-wins abort
  intent를 latch하고 common terminal gate에서 `cancelled/finishedAt`을 B1 repository
  계약으로 저장한다. cancel intent가 먼저면 뒤 rejection은 pipeline-failure로
  승격하지 않고, pipeline-failure intent가 먼저면 뒤 DELETE/cancelled record가
  cancel로 덮지 않는다. 나머지 failed record는 `failedSourceRecords`로 상태 요약에만
  쓰고 normalizer에는 `succeededRecords`만 전달한다.
- [ ] owner/run single execution lease는 coordinator 하나만 source wave를 실행하게
  한다. `DELETE` cancel은 active controller를 즉시 abort하고 terminalization은 같은
  run CAS 경계가 결정한다. profile archive는 admission 전이면 start를 막고 snapshot
  capture 뒤이면 frozen input을 바꾸지 않는다. 어떤 external terminal winner도
  `transitionRunning:null`/typed conflict 경로로 표면화하고 API는 reload한 manifest
  status만 반환한다.
- [ ] source fetch admission, 각 wave 뒤, 모든 synchronous
  parse/rank/normalize/validate stage, 네 inference의 직전·직후, 모든 artifact
  publication, final transition은 위 common gate/terminalization lock을 사용한다.
  inference port 네 종류는 모두 필수 `signal`을 받고 actual fetch로 전달한다. terminal
  winner가 생긴 뒤에는 새 source/inference 호출, normalization, output/failure attach,
  final status overwrite가 없어야 한다.
- [ ] source fetch와 inference 응답은 각각 받은 즉시 JSON으로 기록하고 재로드한
  artifact만 다음 단계가 소비한다.
- [ ] Naver는 news/web/blog/initial DataLab/discovered DataLab을 호출마다 분리한다.
  YouTube는 search 3 lane 각각, 각 lane 결과의 videos.list 1~50 ID batch 각각,
  ranking 뒤 선택한 video의 commentThreads.list 각각을 하나의
  fetch→persist→reload 단위로 실행한다. aggregate source 메서드 안에 여러 HTTP
  호출을 숨기지 않으며 다음 wave는 직전 wave의 reloaded succeeded record에서만
  만든다.
- [ ] rejected/cancelled terminal gate를 통과한 뒤 성공 topic이 있고
  `failedSourceRecords`가 있으면 `partial`, 모두 충족하면 `succeeded`, topic 근거가
  부족하면 `failed`로 종료한다. `finalizeResearchRunStatus`는 이 계산만 수행한다. 이
  상태 전환은 local manifest에만 기록하며 nullable CAS result를 실제 terminal
  manifest로 해소한 뒤 그 durable manifest를 반환한다. credit operation을 시작하거나
  닫지 않는다.
- [ ] API는 owner 격리와 raw success 규약을 지킨다.
- [ ] 선택 자료용
  `POST /projects/shortform-director/user-sources`를 같은 controller에 추가한다.
  URL/text/file을 bounded artifact로 저장하고 opaque `userSourceId`만 start request에
  넣는다. 자료 첨부 없이도 이 route를 호출하지 않은 기본 조사가 동일하게 동작해야
  한다.
- [ ] build/test 통과.
- [ ] Commits:
  - web API:
    `fix(shortform-director): expose bounded source response byte state`
  - desktop Nest:
    `feat(shortform-director): orchestrate current multi-source research`

## Task C3: 아이디어 찾기·근거 과정·실행 기록 UI

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-lineage.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-lineage.controller.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-lineage-api.test.js`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.spec.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-lineage.service.ts`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-lineage.service.spec.ts`
- Replace implementation in:
  `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.{ts,html,scss,spec.ts}`
- Replace implementation in:
  `desktop/clipper_angular/src/features/shortform-director/pages/runs-page/runs-page.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/evidence-process-drawer/evidence-process-drawer.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/source-status-summary/source-status-summary.component.{ts,html,scss,spec.ts}`
- Add:
  `desktop/clipper_angular/src/features/shortform-director/components/run-timeline/run-timeline.component.{ts,html,scss,spec.ts}`

**Lineage API**

- `GET /projects/shortform-director/lineage/:entityType/:entityId`
- `GET /projects/shortform-director/runs?profileId=&kind=&provider=&model=&status=&from=&to=`
- `GET /projects/shortform-director/runs/:runId`
- `GET /projects/shortform-director/artifacts/:artifactId/json`

artifact API는 path를 받지 않고 registry의 opaque ID만 받는다.

- [ ] Nest 테스트를 먼저 쓴다: topic → evidence → source fetch/LLM call 역추적, owner
  격리, unknown artifact 404, path traversal 불가능, JSON과 checksum 일치.
- [ ] Angular service와 화면 실패 테스트를 먼저 쓴다.
- [ ] `아이디어 찾기`는 다음 상태를 명확히 렌더한다:
  - 프로필 선택/선택 키워드/조사 시작
  - 고급 설정에서만 보이는 선택 자료 URL/text/file 추가
  - source별 waiting/running/succeeded/failed
  - 기준 시각과 `partial` 안내
  - topic 카드의 제목·요약·왜 지금·출처 구성
  - 각 카드 `근거·과정`과 `영상 후보 만들기`
- [ ] drawer는 `요약/근거/처리 과정/AI 호출/원본 JSON/파일 정보` 탭을 가진다.
  기본 카드는 원본 JSON을 펼치지 않는다.
- [ ] `실행 기록`은 profile/kind/provider/model/status/date filter와 parent-child timeline,
  오류·재시도, artifact JSON 복사를 제공한다.
- [ ] polling은 페이지가 살아 있고 run이 terminal이 아닐 때만 2초 간격으로 수행하고
  destroy 시 중단한다.
- [ ] RED 확인 후 구현하고 desktop Nest/Angular build/test를 통과시킨다.
- [ ] Commits:
  - desktop Nest: `feat(shortform-director): expose safe lineage and run history`
  - desktop Angular: `feat(shortform-director): show current topics with full evidence trail`

---

# Slice D — 주제별 영상 후보 10개 이상

## Task D1: 후보 생성·중복 제거·보충 실행

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-candidate.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-validator.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-candidates.dto.ts`
- Add endpoints to:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-candidate-run.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-candidate-api.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

**Local API**

- `POST /projects/shortform-director/research-runs/:researchRunId/topics/:topicId/candidate-runs`
- `GET /projects/shortform-director/candidate-runs/:candidateRunId`
- `POST /projects/shortform-director/candidate-runs/:candidateRunId/more`

```ts
export interface VideoCandidateV1 {
  schemaVersion: 'shortform-director-video-candidate.v1';
  id: string;
  candidateRunId: string;
  topicId: string;
  title: string;
  hook: string;
  promise: string;
  whyNow: string;
  outline: string[];
  format: string;
  targetDurationSeconds: number;
  evidenceIds: string[];
  audienceSignalIds: string[];
  referencePatternIds: string[];
  generatedByCallId: string;
  validation: {
    passed: boolean;
    uniqueness: number;
    issues: string[];
  };
}
```

- [ ] 실패 테스트를 먼저 쓴다:
  - 첫 inference 요청은 `requestedCount:20`
  - profile/topic/frozen evidence/audience/reference만 입력
  - evidence ID가 실제 snapshot에 없는 후보 거부
  - prohibited expression, 한 편에 과도한 주장, duration 부적합 거부
  - title+hook+promise의 normalized Korean 3-gram Jaccard가 `>=0.72`면 중복 군집
  - 통과 7개면 탈락 variation axis를 제외한 refill 요청
  - 최대 2회 후 10개 미만이면 run 실패
  - 10개 이상일 때만 `video-candidates.json` 성공 snapshot
  - `more`는 기존 ID/요약을 입력하고 새로운 통과 후보 10개를 추가
- [ ] raw candidates, rejected candidates, 각 inference attempt, 최종 candidates가 서로
  다른 immutable JSON인지 검증한다.
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-candidate-run.test.js
node --test test/shortform-director-candidate-api.test.js
```

- [ ] default=`gpt-5.6-luna`,
  비교=`gpt-5.4-mini|gemini-3.6-flash|gpt-4.1` allowlist만 사용하고 candidate
  생성 전후에 credit operation을 호출하지 않는다.
- [ ] topic의 `근거 수`를 후보가 임의 claim 수로 바꾸지 못하게 validator에서 ID를
  역참조한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): generate at least ten grounded video candidates`

## Task D2: 영상 후보 페이지와 후보 선택→기존 프로젝트 연결

**Files — desktop Nest**

- Modify:
  `src/modules/shortform-director/domain/shortform-director.model.ts`
- Modify:
  `src/modules/shortform-director/application/shortform-director-project.service.ts`
- Add:
  `src/modules/shortform-director/application/shortform-director-candidate-selection.service.ts`
- Add endpoint to:
  `src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Add:
  `test/shortform-director-candidate-selection.test.js`
- Modify:
  `test/shortform-director-foundation.test.js`

**Files — desktop Angular**

- Add:
  `src/features/shortform-director/services/shortform-director-production.service.ts`
- Add:
  `src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Replace implementation in:
  `src/features/shortform-director/pages/candidates-page/candidates-page.component.{ts,html,scss,spec.ts}`
- Modify:
  `src/features/shortform-director/components/evidence-process-drawer/evidence-process-drawer.component.{ts,html,scss,spec.ts}`

Endpoint:

- `POST /projects/shortform-director/candidate-runs/:candidateRunId/candidates/:candidateId/select`

프로젝트에 optional origin을 추가한다.

```ts
interface ShortformDirectorProjectOriginV1 {
  schemaVersion: 'shortform-director-project-origin.v1';
  profileId: string;
  researchRunId: string;
  topicId: string;
  candidateRunId: string;
  videoCandidateId: string;
  selectionId: string;
}
```

- [ ] Nest 실패 테스트:
  - 다른 run의 candidate 선택 거부
  - 선택 시 `candidate-selections/<selectionId>.json` 동결
  - profile snapshot→기존 planning context V2 mapping
  - candidate hook/outline/evidence가 프로젝트 origin과 sourcePack에 연결
  - 기존 origin 없는 project hydrate가 그대로 성공
- [ ] Angular 실패 테스트:
  - 10개 이상 카드 렌더/format·duration·whyNow 표시
  - sort/filter는 결과를 잃지 않음
  - 카드별 `근거·과정`
  - 선택 확인 후 반환된 project ID로
    `/production?projectId=<createdProjectId>` 이동
  - `더 만들기`가 기존 카드를 덮어쓰지 않고 append
- [ ] RED 확인 후 구현한다.
- [ ] 현재 `contentStrategy`/`videoPlan`/asset/TTS/render 필드를 제거하지 않는다.
  새 프로젝트는 기존 파이프라인이 읽을 수 있는 empty plan으로 시작한다.
- [ ] 두 저장소 build/test 통과.
- [ ] Commits:
  - desktop Nest: `feat(shortform-director): bridge selected candidates into projects`
  - desktop Angular: `feat(shortform-director): add grounded video candidate selection`

---

# Slice E — 선택 후보의 장면 설계·장면별 미디어 준비

## Task E1: 후보 기반 VideoPlan과 SceneMediaDecision 동결

**Files — web API**

- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Files — desktop Nest**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/scene-media-decision.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-media-validator.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-video-plan-run.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-video-plan.dto.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-production.controller.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-contract.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-recipe.compiler.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-candidate-video-plan.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-scene-media-decision.test.js`

Endpoint:

- `POST /projects/shortform-director/projects/:projectId/video-plan-runs`
- `GET /projects/shortform-director/projects/:projectId/video-plan-runs/:runId`

```ts
export type SceneMedium =
  | 'official-source'
  | 'licensed-real-media'
  | 'generated-image'
  | 'generated-video'
  | 'programmatic-diagram'
  | 'kinetic-typography'
  | 'mixed-composition';

export interface SceneMediaDecisionV1 {
  schemaVersion: 'shortform-director-scene-media-decision.v1';
  id: string;
  videoPlanRunId: string;
  sceneId: string;
  medium: SceneMedium;
  rationale: string;
  factualRisk: 'low' | 'medium' | 'high';
  evidenceIds: string[];
  productionSourceIds: string[];
  generationBrief?: string;
  programmaticBrief?: {
    primitive: 'source-card' | 'comparison' | 'sequence' | 'metric' | 'kinetic-text';
    labels: string[];
    values?: number[];
  };
  fallbackMedium: Exclude<SceneMedium, 'mixed-composition'>;
  generatedByCallId: string;
}
```

- [ ] web inference schema 테스트를 먼저 확장한다. video plan output은 의미 변화 지점으로
  scene을 나누고, 각 scene의 narration/on-screen text/claim/evidence/duration과
  별도 media decision을 반환해야 한다.
- [ ] desktop 실패 테스트:
  - candidate/profile/topic/evidence가 모두 input에 포함
  - 내레이션 단어 예산과 전체 duration 일치
  - scene evidence ID 실존
  - 사실 주장 scene이 근거 없이 생성 미디어로 표현되면 거부
  - 제품/인물/기사 사실 증명을 사실처럼 보이는 생성 영상으로 대체하면 거부
  - 도식·정확한 한국어 문구는 programmatic/typography
  - 어떤 decision도 `owned` medium을 만들지 않음
  - fallback은 고정 provider 순서가 아니라 의미상 안전한 medium 한 개
- [ ] `DraftVideoPlan.derivation`을 호환 union으로 확장한다.

```ts
type VideoPlanDerivation =
  | {
      kind: 'native';
      planningContextId: string;
      contentStrategyId: string;
      matrixEntryId: string;
      hypothesisId: string;
    }
  | {
      kind: 'video-candidate';
      planningContextId: string;
      researchRunId: string;
      topicId: string;
      candidateRunId: string;
      videoCandidateId: string;
    };
```

- [ ] 기존 native plan validator/compiler 회귀 테스트와 새 candidate derivation 테스트를
  같이 통과시킨다.
- [ ] RED 확인:

```bash
npm test -- --runInBand src/modules/shortform-director-inference
```

```bash
npm run build
node --test test/shortform-director-candidate-video-plan.test.js
node --test test/shortform-director-scene-media-decision.test.js
node --test test/shortform-director-video-plan.test.js
node --test test/shortform-director-render-recipe-compiler.test.js
```

- [ ] credit operation 없이 video plan local run을 시작하고 성공 시 다음 파일을
  동결한다:
  `input.json`, `llm-calls/<id>.json`, `video-plan.json`,
  `scene-media-decisions.json`.
- [ ] 기존 project에는 현재 선택된 `videoPlanRunId`와 호환 `videoPlan`을 원자 갱신한다.
- [ ] web/desktop build/test 통과.
- [ ] Commits:
  - web API: `feat(shortform-director): return grounded scene and media plans`
  - desktop Nest: `feat(shortform-director): persist candidate-based scene plans`

## Task E2: 생성 미디어 호출에 인증·모델 비교·audit 적용

**Files — web API**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/presentation/generate-shortform-director-asset.dto.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/presentation/shortform-director-generated-media.controller.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-assets/presentation/shortform-director-generated-media.controller.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/application/shortform-director-generated-media.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/application/shortform-director-generated-media.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/shortform-director-assets.module.ts`

**Files — desktop Nest**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-generated-media-web-api.client.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-media-search-web-api.client.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-generated-media-operation.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-automatic-asset.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-automatic-asset-preparation.test.js`

**Generated media request**

```ts
interface GenerateDirectorMediaRequest {
  mediaKind: 'image' | 'video';
  modelProfile:
    | 'image-default'
    | 'image-quality'
    | 'video-omni'
    | 'video-fast'
    | 'video-quality';
  prompt: string;
  durationMs?: number;
}
```

allowlist:

- `image-default` → `gemini-3.1-flash-image`
- `image-quality` → `gemini-3-pro-image`
- `video-omni` → `gemini-omni-flash-preview`
- `video-fast` → `veo-3.1-fast-generate-preview`
- `video-quality` → `veo-3.1-generate-preview`

- [ ] OpenAPI에서 임의 model ID를 받지 않고 위 `modelProfile`만 받도록 먼저 수정한다.
- [ ] controller 실패 테스트를 쓴다:
  JWT 필수, allowlist 밖 profile/media kind 거부, operation run·credit policy 호출 없음.
- [ ] service 실패 테스트를 쓴다:
  profile→model 정확 매핑, image/video request 차이, long-running poll, timeout/cancel,
  최대 byte, provider error detail redaction.
- [ ] 응답에 media와 함께 model ID, provider request/operation ID, 공개 request options,
  공개 raw response metadata, latency를 포함하되 API key/download signed query는 제거하는
  audit 테스트를 쓴다.
- [ ] desktop client가 bearer token과 allowlisted request만 보내고 audit를 그대로
  local record로 넘기는 테스트를 쓴다.
- [ ] 기존 automatic asset entry도 operation을 시작하거나 성공/실패로 닫지 않는
  회귀 테스트를 쓴다. local media run ID와 provider request ID만 계보에 남긴다.
- [ ] RED 확인 후 구현한다.
- [ ] 기존 이미지/영상 기본 route를 호출하던 과거 project가 깨지지 않도록 DTO의
  `modelProfile`은 legacy 호출에서 media kind별 현재 기준선으로 normalize한다. 새 UI는
  항상 명시한다.
- [ ] 관련 build/test 통과.
- [ ] Commits:
  - web API: `feat(shortform-director): authorize and audit generated media`
  - desktop Nest: `feat(shortform-director): preserve generated media provider records`

## Task E3: SceneMediaDecision별 fulfillment, TTS, sidecar

**Files**

- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-media.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-quality-report.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-media.dto.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-production.controller.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-automatic-asset.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-asset.storage.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/asset-pack.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-scene-media-fulfillment.test.js`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-media-sidecar.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-automatic-asset-preparation.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

Endpoints:

- `POST /projects/shortform-director/projects/:projectId/media-runs`
- `GET /projects/shortform-director/projects/:projectId/media-runs/:mediaRunId`
- `POST /projects/shortform-director/projects/:projectId/media-runs/:mediaRunId/selections`

Start body는 `comparisonMode:'none'|'representative'|'quality'`와 scene별 사용자가 고른
override만 받는다. 기본은 `representative`: 생성 영상이 필요한 대표 scene 한 개에서
Omni와 빠른 Veo를 비교하고, 나머지는 선택된 winner 또는 default를 쓴다.

- [ ] 실패 테스트를 먼저 쓴다:
  - programmatic/typography는 외부 미디어 API를 호출하지 않음
  - official-source는 production-eligible source만 materialize
  - licensed-real-media는 명시된 license/rights 없으면 사용하지 않고 안전 medium
    재결정 기록
  - generated-image는 image endpoint만 호출
  - generated-video는 선택 profile만 호출
  - mixed는 decision에 선언된 구성 요소만 호출
  - 검색 실패가 자동으로 AI 생성으로 넘어가지 않고 새 `redecision` JSON을 요구
  - 조사 YouTube URL이 download/binding 입력으로 넘어가지 않음
  - local owned-library candidate lookup이 새 origin project에서 호출되지 않음
- [ ] media batch가 Naver image search와 generated media를 호출할 때 bearer token만
  사용하고, 어느 경로도 operation/credit API를 호출하지 않는 테스트를 쓴다.
- [ ] 기존 local asset storage와 binding을 재사용하되 각 binary 옆 sidecar가 다음을
  갖는지 테스트한다:

```ts
interface ProductionMediaSidecarV1 {
  schemaVersion: 'shortform-director-production-media.v1';
  artifactId: string;
  sceneId: string;
  mediaDecisionId: string;
  mediaType: string;
  relativePath: string;
  sizeBytes: number;
  checksum: string;
  provider?: string;
  model?: string;
  prompt?: string;
  sourceEvidenceIds: string[];
  rightsRole: 'production-eligible';
  llmCallId?: string;
  providerCallArtifactId?: string;
  createdAt: string;
}
```

- [ ] TTS는 현재 local Supertonic 경로와 timing alignment를 재사용하고 새 API key를
  요구하지 않는 회귀 테스트를 유지한다.
- [ ] 대표 모델 비교 결과는 두 binary/sidecar와 선택 이유를 모두 보존한다. 탈락
  결과도 삭제하지 않는다.
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-scene-media-fulfillment.test.js
node --test test/shortform-director-media-sidecar.test.js
node --test test/shortform-director-tts-timing-alignment.test.js
```

- [ ] `ShortformDirectorAutomaticAssetService`의 legacy entry는 기존 project 호환용으로
  유지하되, origin이 있는 새 project는 explicit decision service로 위임한다.
- [ ] media run manifest와 project current pointer를 원자 갱신한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): fulfill each scene with its chosen medium`

## Task E4: 영상 제작 페이지에 장면·비용·모델 비교 연결

**Files**

- Replace implementation in:
  `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.{ts,html,scss,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/evidence-process-drawer/evidence-process-drawer.component.{ts,html,scss,spec.ts}`
- Reuse:
  `desktop/clipper_angular/src/features/shortform-director/components/sequence-card-preview/sequence-card-preview.component.{ts,html,scss,spec.ts}`

- [ ] 화면 실패 테스트를 먼저 쓴다:
  - 선택 후보 요약과 현재 video plan/media/TTS 상태
  - scene별 narration/on-screen text/purpose/duration/medium
  - medium 선택 이유와 evidence count
  - `근거·과정`에서 scene claim→evidence→source와 생성 prompt/model/sidecar
  - 예상 이미지/영상 호출 수와 비교 mode 표시
  - `미디어 준비` 실행 중 재클릭 방지·부분 실패·재시도
  - 비교 결과를 나란히 preview하고 winner 선택
  - `렌더 시작`은 plan/media/TTS readiness가 모두 통과해야 활성
- [ ] 기본 화면에는 내부 JSON을 노출하지 않고 쉬운 상태 문구와 다음 행동 하나를
  우선 표시한다.
- [ ] 사용자가 scene medium을 바꾸면 원본 decision을 수정하지 않고 override/redecision
  artifact를 만든 뒤 새 media run을 시작한다.
- [ ] RED 확인 후 구현한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): connect scene production and model comparison UI`

---

# Slice F — Motion Canvas 완성 영상·공용 큐·보관함

## Task F1: Motion Canvas 단일 실행과 새 scene 표현 렌더

**Files**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-renderer-adapter.registry.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-recipe.compiler.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-motion-canvas-renderer.adapter.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-motion-canvas.worker.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-renderer-adapter-foundation.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-motion-canvas-renderer.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-motion-canvas-render-integration.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-renderer-conformance.test.js`

- [ ] registry 테스트를 먼저 바꿔 실행 가능한 adapter가
  `director.adapter.motion-canvas-local.v1` 하나뿐인지 확인한다.
- [ ] 대표 fixture를 새 scene medium별로 만든다:
  source card, metric, comparison, sequence, kinetic text, generated image/video,
  mixed composition.
- [ ] renderer 테스트:
  1080×1920, H.264/AAC, narration 포함, caption safe area, 정확한 한국어 text,
  media missing 시 명시 실패, cancel 시 temp cleanup.
- [ ] visual golden/conformance에서 검은 화면, text overflow, evidence card 가독성,
  scene duration과 TTS timing을 확인한다.
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-renderer-adapter-foundation.test.js
node --test test/shortform-director-motion-canvas-renderer.test.js
node --test test/shortform-director-motion-canvas-render-integration.test.js
node --test test/shortform-director-renderer-conformance.test.js
```

- [ ] module provider array와 default resolve를 Motion Canvas 하나로 고정한다.
- [ ] 기존 native project fixture도 계속 렌더되는지 회귀 테스트한다.
- [ ] build/test 통과.
- [ ] Commit:
  `feat(shortform-director): render all scene media with Motion Canvas`

## Task F2: 렌더 결과를 기존 Jobs 완료→Projects 보관함으로 연결

**Files — desktop Nest**

- Modify:
  `src/modules/shortform-director/domain/render-operation.ts`
- Modify:
  `src/modules/shortform-director/application/shortform-director-render-workflow.executor.ts`
- Modify:
  `src/modules/shortform-director/application/shortform-director-render-operation.service.ts`
- Modify:
  `src/modules/shortform-director/infrastructure/local-shortform-director-render-output.storage.ts`
- Modify:
  `src/modules/projects/application/projects.service.ts`
- Modify:
  `src/modules/projects/domain/project.model.ts`
- Modify:
  `src/modules/projects/application/project-detail-builder.ts`
- Modify:
  `test/shortform-director-render-operation.test.js`
- Add:
  `test/shortform-director-vault-integration.test.js`
- Modify:
  `test/shortform-project-api.test.js`

**Files — desktop Angular**

- Modify:
  `src/shell/projects/projects/projects.component.ts`
- Modify:
  `src/shell/projects/projects/projects.component.spec.ts`
- Modify:
  `src/shell/projects/models/projects-view.ts`
- Modify:
  `src/shell/projects/projects-detail-page/projects-detail-page.component.{ts,html,spec.ts}`
- Add:
  `src/shell/projects/shortform-director-result-detail/shortform-director-result-detail.component.{ts,html,scss,spec.ts}`

완료 job result가 현재 보관함 계약에 필요한 값을 명시적으로 제공한다.

```ts
interface ShortformDirectorVaultResult {
  schemaVersion: 'shortform-director-render-result.v2';
  workflow: 'shortform_director';
  stage: 'render_completed';
  project_id: string;
  director_project_id: string;
  title: string;
  output_root: string;
  video_relative_path: string;
  duration_sec: number;
  width: number;
  height: number;
  checksum: string;
  render_run_id: string;
  output_artifact_id: string;
}
```

`project_id`는 render job ID를 사용해 재렌더도 보관함의 별도 결과 카드가 되게 하고,
`director_project_id`가 제작 workspace로 돌아가는 연결을 맡는다.

- [ ] 현재 “Director render면 `recordCompletedJob()`에서 null”인 테스트를 먼저 뒤집는다.
  성공 render는 정확히 한 `ProjectSnapshot`을 만들어야 한다.
- [ ] executor 테스트를 먼저 수정한다:
  - resolved output directory와 relative MP4
  - recipe output label 기반 title
  - run/artifact/checksum/technical metadata
  - job result에 credential/provider secret 없음
- [ ] 새 origin project는 render job ID를 `renderRunId`로 사용해
  `render-runs/<jobId>/manifest.json`과 input/result artifact를 기록하고 lineage의
  media run→render run→output을 연결한다. 기존 origin 없는 project는 현재 렌더
  동작을 유지하되 존재하지 않는 profile ID를 지어내지 않는다.
- [ ] 저장돼 있는 V1 render result와 새 V2 result를 모두 읽는 compatibility union을
  추가하고 기존 완료 job 조회 테스트를 유지한다.
- [ ] 통합 실패 테스트:
  - render start가 기존 `JobsService.start({pluginName:'shortform_director'})`
  - queue snapshot에 waiting/running/completed 진행
  - completed event가 `projects/projects.json` 등록
  - `GET /projects/:id`, detail, file ticket, range-capable MP4 route가 같은 파일을 반환
  - 다른 owner는 조회/재생 불가
  - 재렌더는 이전 카드/파일을 덮어쓰지 않음
- [ ] `ProjectDetail['category']`에 `shortform_director`를 추가하고 output 한 건을
  `renders`에 넣는 builder 테스트를 쓴다.
- [ ] Angular 실패 테스트:
  - plugin label `AI 숏폼 디렉터`
  - 일반 클리퍼 section과 구분
  - thumbnail이 없어도 video preview/play 가능
  - detail에서 제목·duration·생성 시각·재생·Director workspace 이동
- [ ] RED 확인:

```bash
npm run build
node --test test/shortform-director-render-operation.test.js
node --test test/shortform-director-vault-integration.test.js
node --test test/shortform-project-api.test.js
```

```bash
npm test -- --watch=false
```

- [ ] `ProjectsService`의 Director skip만 제거하고 다른 plugin의 project ID/title/artifact
  계산은 건드리지 않는다.
- [ ] `output_root`는 desktop 로컬 Projects 저장·file resolver에만 사용한다. 웹 API,
  LLM prompt, provider audit에는 보내지 않는다.
- [ ] 두 저장소 build/test 통과.
- [ ] Commits:
  - desktop Nest: `feat(shortform-director): publish rendered videos to the project vault`
  - desktop Angular: `feat(projects): show AI Director outputs in the vault`

## Task F3: 완성 영상 페이지와 quality report

**Files — web API**

- Modify:
  `web/clipper_web_api/docs/api/openapi.yaml`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/dto/run-shortform-director-multimodal-review.dto.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-multimodal-review.controller.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-multimodal-review.controller.spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-multimodal-review.service.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-multimodal-review.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/shortform-director-inference.module.ts`

**Files — desktop**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-quality-report.service.ts`
- Add:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-quality-report.dto.ts`
- Add endpoints to:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-production.controller.ts`
- Add:
  `desktop/clipper_nestjs/test/shortform-director-quality-report-run.test.js`
- Replace implementation in:
  `desktop/clipper_angular/src/features/shortform-director/pages/outputs-page/outputs-page.component.{ts,html,scss,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.spec.ts`

Endpoints:

- `POST /projects/shortform-director/projects/:projectId/quality-report-runs`
- `GET /projects/shortform-director/projects/:projectId/quality-report-runs/:runId`

- [ ] web API에 bearer JWT 전용
  `POST /shortform-director/inference/quality-review-media` multipart route를 추가한다.
  클라이언트는 local path/provider URL/file ID를 보내지 않고 `video` MP4 stream과
  bounded JSON `input`만 보낸다. MP4 최대 250 MiB, MIME/signature 불일치 거부,
  request/provider temp file은 성공·실패·cancel 모두 정리한다.
- [ ] web API가 DB-only Google credential로 Gemini file upload→processing wait→
  quality-review inference→provider file delete를 내부에서 조율한다. provider file
  URI와 credential은 공개 audit에 넣지 않고, fake transport 테스트에서 upload/body
  read timeout, processing timeout, failure audit, cleanup을 검증한다. 실제 provider
  smoke는 G3 승인 전 실행하지 않는다.
- [ ] technical report 테스트: MP4 존재/checksum, duration 오차, 9:16, H.264/AAC,
  audio stream, black/frozen frame sample, caption safe-area summary.
- [ ] grounded content report 테스트: scene claim/evidence coverage, prohibited expression,
  on-screen text/narration mismatch, selected media가 decision과 일치.
- [ ] Gemini quality review를 쓸 때도 audit JSON과 model/usage/cost가 남고 credential이
  남지 않는 테스트를 쓴다.
- [ ] multimodal review는 bearer token으로 전용 inference endpoint만 호출하며
  operation quote/start/succeed/fail/refund를 전혀 호출하지 않는 테스트를 쓴다.
  기술 검사만 수행하면 provider 호출 자체도 하지 않는다.
- [ ] 완성 영상 화면 테스트:
  video player, vault 이동, 기술 검사, scene별 근거/미디어/prompt, 총 token·예상 비용·
  소요 시간, 실패 항목의 production scene 이동.
- [ ] quality report 실패가 성공 MP4 자체를 지우거나 보관함 등록을 취소하지 않게 한다.
- [ ] RED 확인 후 구현하고 build/test 통과.
- [ ] Commits:
  - web API: `feat(shortform-director): add bounded multimodal quality review`
  - desktop Nest: `feat(shortform-director): persist output quality reports`
  - desktop Angular: `feat(shortform-director): add traceable finished video review`

---

# Slice G — 구 UI 제거·통합 검증·실제 품질 비교

## Task G1: 구 단일 페이지를 제거하고 호환 경로 정리

**Files**

- Delete after all replacement tests are green:
  - `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.html`
  - `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.scss`
  - `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-page.component.spec.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/shortform-director-page/shortform-director-complete-examples.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-project.service.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-project.service.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-project.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/shortform-director-registration.spec.ts`

- [ ] `rg`로 구 page selector/import/예시 데이터를 찾는 실패 test/check를 먼저 만든다.
- [ ] 새 services가 실제로 사용하지 않는 구 method만 제거한다. candidate 이후
  project/TTS/render method는 새 production service가 위임하므로 유지한다.
- [ ] 예시 정답 데이터가 production bundle에 남지 않는지 확인한다.

```bash
rg -n "ShortformDirectorPageComponent|shortform-director-complete-examples" src
```

기대 결과: 사용처 0건.

- [ ] Angular build/test 통과.
- [ ] Commit:
  `refactor(shortform-director): retire the single-page prototype`

## Task G2: fake-provider end-to-end와 secret/package 회귀

**Files**

- Add:
  `desktop/clipper_nestjs/test/shortform-director-quality-e2e.test.js`
- Add:
  `desktop/clipper_nestjs/test/fixtures/shortform-director/current-market-relative.fixture.js`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-research/shortform-director-research.e2e-spec.ts`
- Add:
  `web/clipper_web_api/src/modules/shortform-director-inference/shortform-director-inference.e2e-spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/shortform-director-registration.spec.ts`
- Add:
  `clipper_docs/reviews/2026-07-27-shortform-director-quality-validation-report.md`

fixture는 특정 실존 키워드를 정답으로 두지 않고 `clock.now` 기준 최근 4h/7d/30d 자료와
가상 분야·가상 제목을 생성한다.

- [ ] 한 e2e가 다음 전체를 완주하게 한다:

```text
profile create
→ research start/poll
→ Trends+Naver+YouTube raw JSON
→ topics
→ candidate run with >=10
→ select candidate
→ video plan + scene media decisions
→ media/TTS
→ Motion Canvas render through Jobs
→ Projects vault file ticket
→ lineage and quality report
```

- [ ] 한 source 실패 variant가 `partial`로 완주하고 UI/API에 실패 source가 보이는지
  검증한다.
- [ ] provider API key 값을 눈에 띄는 sentinel로 넣고 다음 전체 scan에서 0건인지
  검증한다:
  - desktop JSON data root
  - desktop Nest response snapshots/log capture
  - desktop Angular build output
  - Electron packaged resources
- [ ] desktop source/config에 provider secret env name을 새로 추가하지 않았는지 검사한다.

```bash
rg -n "YOUTUBE_API_KEY|OPENAI_API_KEY|GOOGLE_API_KEY|NAVER_CLIENT_SECRET" \
  desktop/clipper_nestjs/src desktop/clipper_angular/src
```

기대 결과: 새 AI Director credential 경로 0건. 기존 다른 기능의 발견 항목이 있으면
파일·용도를 보고서에 기록하고 이 작업에서 몰래 삭제하지 않는다.

- [ ] AI Director 경로에 credit operation 의존이 다시 들어오지 않았는지 검사한다.

```bash
rg -n "OperationChargeGuardService|WebApiOperationRunService|operationRunId|shortform_director\\.(strategy|video_plan)" \
  desktop/clipper_angular/src/features/shortform-director \
  desktop/clipper_nestjs/src/modules/shortform-director \
  web/clipper_web_api/src/modules/shortform-director-*
```

기대 결과: billing/operation 의존 0건. 로그 메시지나 역사적 migration처럼 실행 의존이
아닌 발견 항목은 파일·이유를 validation report에 구분해 적는다.

- [ ] 네 코드 저장소 전체 build/test를 실행한다.

```bash
# web/clipper_web_api
npm run build
npm test -- --runInBand

# web/clipper_web_admin
npm run build
npm test -- --watch=false

# desktop/clipper_nestjs
npm run build
node --test test/*.test.js

# desktop/clipper_angular
npm run build
npm test -- --watch=false
```

- [ ] validation report에 테스트 commit, fixture asOf 규칙, source 성공/실패, 후보 수,
  render 기술 정보, lineage completeness, secret scan 결과를 기록한다.
- [ ] 각 저장소 `git status --short --branch`, upstream divergence, 최근 log를 다시
  기록하고 예상 밖 변경을 보고한다.
- [ ] Commits:
  - web API: `test(shortform-director): cover research provider boundaries end to end`
  - desktop Nest: `test(shortform-director): cover quality workflow end to end`
  - desktop Angular: `test(shortform-director): cover guided workflow integration`
  - docs: `docs: record AI Director quality workflow verification`

## Task G3: 사용자 승인 뒤 실제 최신 데이터·모델·영상 검증

이 task만 유료 실호출을 포함한다. 자동으로 시작하지 않는다.

- [ ] 관리자 페이지에서 Naver/OpenAI/Gemini/YouTube runtime status와 test가 모두
  성공하는지 확인한다. key 원문은 화면 캡처·로그·보고서에 넣지 않는다.
- [ ] 사용자가 실제 테스트할 운영 프로필을 선택하거나 새로 만든다. 특정 키워드는
  정답으로 미리 고르지 않고 선택 입력으로만 둔다.
- [ ] 실행 전 예상 호출 표를 표시한다:
  source별 API 호출 수, LLM model별 호출 수/token 상한, image/video 생성 횟수,
  예상 USD/KRW 범위.
- [ ] 사용자의 비용 승인을 받은 뒤 research를 한 번 실행한다.
- [ ] `asOf` 기준을 확인해 오래된 자료가 `왜 지금인가` 근거로 올라오지 않았는지
  사람이 표본 검사한다.
- [ ] 한 topic에서 후보가 10개 이상이고 hook/promise/angle이 실질적으로 다른지
  사람이 blind rubric으로 평가한다.
- [ ] 같은 frozen snapshot에서 `gpt-4.1` baseline과 default/cost comparison을
  생성해 근거 정확성·중복·한국어·구조 성공률·비용·지연을 비교한다.
- [ ] 대표 generated-video scene에서 Omni와 빠른 Veo를 비교하고, 필요할 때만 품질
  Veo 한 건을 추가한다.
- [ ] 선택 candidate 한 편을 끝까지 렌더한다.
- [ ] global queue에서 진행 상태, 보관함 카드, MP4 재생, Director workspace 링크,
  `근거·과정`, 실행 기록 JSON을 화면으로 확인한다.
- [ ] 최근 입력 개선 전 영상과 새 영상을 같은 rubric으로 blind 비교한다:
  첫 2초 hook, 정보 정확성, 시의성, 장면-내레이션 일치, 자막 가독성, visual variety,
  전체 완성도.
- [ ] 실제 결과를
  `clipper_docs/reviews/2026-07-27-shortform-director-quality-validation-report.md`에
  추가하되 URL·prompt·응답은 저작권/민감정보 범위에 맞게 요약하고 원본은 local
  artifact ID로만 참조한다.
- [ ] 실제 검증 실패는 fixture로 숨기지 않는다. 원인별로 source, inference,
  candidate validation, media, render 중 하나에 배정하고 해당 slice의 테스트부터
  추가한다.

---

## 4. 완료 판정

다음 항목이 모두 충족되어야 이 계획을 완료로 표시한다.

- [ ] 새 provider secret은 관리자 웹에서만 등록되고 웹 API DB에 암호화된다.
- [ ] Electron 환경/빌드와 local run JSON에 credential 원문이 없다.
- [ ] AI Director의 기존 전략·영상 구성과 새 조사·후보·미디어·품질 검사 어디에서도
  크레딧 확인, operation start, 차감, 환불이 일어나지 않는다.
- [ ] 운영 프로필 CRUD와 soft archive가 동작한다.
- [ ] `새 영상 시작`이 프로필 선택→선택 키워드→실제 조사로 이어진다.
- [ ] Google Trends RSS, Naver Search/DataLab, YouTube Data가 실제 독립 호출된다.
- [ ] source별 raw/parsed/error JSON과 모든 LLM request/response/usage JSON이 남는다.
- [ ] 최근 근거가 연결된 topic 여러 개가 나오고 topic이 영상 한 편으로 오인되지 않는다.
- [ ] 선택 topic에서 검증된 영상 후보가 최소 10개 나온다.
- [ ] 선택 candidate만 상세 scene/video plan 비용을 쓴다.
- [ ] scene별 medium이 목적에 맞게 정해지고 고정 fallback/owned-library 전제가 없다.
- [ ] 조사 YouTube 영상이 권리 확인 없이 제작 파일로 사용되지 않는다.
- [ ] TTS·이미지·영상·도식·자막이 Motion Canvas MP4에 합성된다.
- [ ] render job이 기존 queue에 보이고 성공 MP4가 기존 보관함에서 재생된다.
- [ ] topic/candidate/scene/output에서 `근거·과정`과 원본 JSON을 역추적할 수 있다.
- [ ] 실제 최신 데이터와 실제 provider로 한 편을 완주하고 baseline 대비 품질 보고서가
  작성된다.
- [ ] 네 코드 저장소 full build/test가 통과하고 보존 대상 legacy 변경이 그대로다.

---

## 5. 구현 중지·보고 조건

다음 상황에서는 임의 우회하지 말고 사용자에게 근거와 선택지를 보고한다.

- Google Trends RSS가 한국에서 더 이상 데이터를 반환하지 않고, 해결에 HTML/internal
  endpoint가 필요할 때
- Naver 등록 앱에서 Search 또는 DataLab 권한이 활성화되지 않았을 때
- YouTube quota가 계획한 lane/분석 규모를 감당하지 못할 때
- model ID가 provider에서 실제 사용 불가하거나 Preview 계약이 바뀌었을 때
- 실제 유료 비교 예상 비용이 승인 범위를 넘을 때
- 기존 `projects.json`/보관함 계약 변경이 다른 plugin output을 깨뜨릴 때
- 예상 밖 worktree 변경이 이 계획 파일과 겹칠 때

막힘이 아닌 부분 실패는 JSON에 남기고 가능한 source/scene으로 계속 진행한다.
