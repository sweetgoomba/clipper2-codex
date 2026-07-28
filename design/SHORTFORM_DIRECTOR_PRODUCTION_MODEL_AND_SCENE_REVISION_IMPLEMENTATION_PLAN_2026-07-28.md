# AI 숏폼 디렉터 제작 모델 선택·장면 편집 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI 숏폼 디렉터에서 현재 기본 제작 모델을 확인하고, 완성된 프로젝트의 장면별
문구·미디어 방식·생성 모델을 편집하여 특정 장면 또는 전체 영상을 새 버전으로 다시
만들 수 있게 한다.

**Architecture:** `clipper_web_api`가 외부 추론·생성 모델 allowlist와 credential 준비
상태의 정본을 제공하고, `clipper_nestjs`가 이를 Supertonic·Motion Canvas 같은 로컬
도구와 합성한다. 장면 편집 초안과 append-only media/TTS revision은 기존
`CLIPPER_DATA_DIR` JSON 저장소에 보관하며, Angular는 Nest 계약만 사용한다. 생성
미디어는 provider 이름이 아니라 `implementationId`로 선택하고, 실제 호출 전
credential revision·project revision·입력 fingerprint·예상 비용을 승인한다.

**Tech Stack:** Angular 19 standalone/zoneless/signals/Material, NestJS 10 desktop
`node:test`, NestJS 11 Web API/Jest, 로컬 JSON·immutable artifacts, Google AI
generated media, Naver image search, Supertonic, Motion Canvas.

## Global Constraints

- 작업 위치는 `/Users/jina/project/adlight`이며 새 worktree를 만들지 않는다.
- 각 저장소의 기존 `feat/shortform-director-foundation` 브랜치에서 작업한다.
- `legacy/adlight_python/fastapi_server.spec`의 기존 변경은 건드리지 않는다.
- 별도의 Omni/Veo 비교 API·화면·대표 장면 선택 기능을 만들지 않는다.
- 생성 영상 기본값은 `gemini-omni-flash-preview`다.
- 초기 선택 가능 영상 모델은 실제 연결 코드가 있는 Omni와 Veo Fast뿐이다.
- Seedance·Higgsfield는 실제 credential·adapter 연결 전 선택 목록에 넣지 않는다.
- 전역 기본 모델 변경 UI는 만들지 않고 읽기 전용 기본값만 보여준다.
- API key는 관리자 페이지와 Web API credential 경계 밖으로 내보내지 않는다.
- 모든 새 실행 데이터는 구조화된 JSON으로 저장하고 응답 원문 전체는 저장하지 않는다.
- AI Director의 크레딧 조회·차감 기능을 추가하지 않는다.
- Remotion을 새 코드·UI·새 문서 흐름에 사용하지 않는다.
- Angular 컴포넌트는 TS/HTML/SCSS/spec 4파일, OnPush, Material, semantic token 규칙을
  지킨다.
- Nest 파일은 domain/application/infrastructure/presentation 책임을 분리하고 한
  서비스에 저장·외부 호출·HTTP 변환을 함께 넣지 않는다.
- runtime 코드에 fixture, 가짜 provider 응답, placeholder media를 넣지 않는다.
- 실제 유료 provider 호출은 provider/model/횟수/예상 비용을 사용자에게 먼저 알리고
  별도 승인받기 전 실행하지 않는다.
- 커밋과 push는 사용자가 명시적으로 요청하기 전 실행하지 않는다.

---

## 파일 구조

### Web API

- `shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
  - 외부 추론·이미지·영상 implementation ID와 model ID의 단일 정본.
- `shortform-director-inference/domain/shortform-director-model-catalog.ts`
  - 기존 purpose/profile 표가 단일 정본의 implementation ID를 가리키게 한다.
- `shortform-director-assets/application/shortform-director-generated-media.service.ts`
  - implementation을 resolve한 뒤 기존 Google AI adapter를 호출한다.
- `shortform-director-production/application/shortform-director-production-capability.service.ts`
  - 추론·생성 catalog와 credential 준비 상태를 합성한다.
- `shortform-director-production/presentation/shortform-director-production-capability.controller.ts`
  - 인증된 안전한 catalog endpoint.

### Desktop Nest

- `shortform-director/domain/production-capability.ts`
  - Angular로 반환할 통합 capability 계약과 parser.
- `shortform-director/application/shortform-director-production-capability-web-api.client.ts`
  - Web API의 외부 capability 응답 검증.
- `shortform-director/application/shortform-director-production-capability.service.ts`
  - 외부 catalog에 Naver·Supertonic·Motion Canvas 로컬 도구를 합성.
- `shortform-director/domain/production-state.ts`
  - 프로젝트의 catalog snapshot, 장면 편집 설정, 활성 media/TTS/render revision 포인터.
- `shortform-director/domain/scene-media-revision.ts`
  - append-only media revision과 상태 전이.
- `shortform-director/domain/scene-media-revision.repository.ts`
  - append-only revision repository 추상.
- `shortform-director/infrastructure/artifact-shortform-director-scene-media-revision.repository.ts`
  - 기존 immutable artifact registry 위의 typed revision 구현.
- `shortform-director/application/shortform-director-scene-edit.service.ts`
  - ownership, scene/layer 존재, 전략·implementation 조합을 검증하고 초안 저장.
- `shortform-director/application/shortform-director-layer-asset-executor.ts`
  - 한 레이어의 source/search/generated/programmatic 준비만 담당.
- `shortform-director/application/shortform-director-scene-media.service.ts`
  - preflight, 승인 검증, revision 생성, 성공 시 binding 전환, 과거 revision 활성화.
- `shortform-director/application/shortform-director-narration-cue-synthesizer.ts`
  - Supertonic cue 하나의 WAV 생성·검증·저장.
- `shortform-director/application/shortform-director-scene-narration.service.ts`
  - 바뀐 cue만 재합성하고 전체 timing을 다시 정렬.
- `shortform-director/presentation/shortform-director-production-capability.controller.ts`
  - 통합 catalog endpoint.
- `shortform-director/presentation/shortform-director-scene-edit.controller.ts`
  - 편집·revision·단일/전체 재생성 endpoint.

### Angular

- `models/shortform-director-production-capability.ts`
  - 통합 catalog UI 계약.
- `models/shortform-director-scene-edit.ts`
  - 초안, revision, preflight, 편집 요청 계약.
- `services/shortform-director-project.service.ts`
  - catalog·편집·재생성·revision HTTP 호출.
- `state/shortform-director-production.store.ts`
  - candidate/project 직접 진입과 현재 project snapshot, 기존 제작·렌더 workflow.
- `services/shortform-director-scene-production.gateway.ts`
  - project-scoped scene editing HTTP 계약.
- `services/shortform-director-scene-production.service.ts`
  - scene editing HTTP 구현.
- `state/shortform-director-scene-production.store.ts`
  - catalog, scene draft, layer별 revision·pending·error 상태.
- `components/production-model-summary/*`
  - 읽기 전용 기본 모델·도구 요약.
- `components/production-scene-card/*`
  - 장면의 문구 편집과 시각 레이어 card 조립.
- `components/production-scene-content-form/*`
  - 내레이션 cue와 화면 문구 편집.
- `components/production-layer-card/*`
  - 레이어 요약·편집·제작 정보 action.
- `components/production-layer-editor/*`
  - 전략별 입력과 AI model dropdown.
- `components/production-source-strategy-form/*`
  - 근거 자료 선택.
- `components/production-search-strategy-form/*`
  - 검색어·검색 결과·권리 상태.
- `components/production-generated-media-strategy-form/*`
  - 이미지/영상 capability 기반 prompt·model 선택.
- `components/production-programmatic-strategy-form/*`
  - 지원되는 도식 primitive 입력.
- `components/production-revision-history/*`
  - 제작 정보와 이전 revision 활성화.
- `pages/production-page/*`
  - 비용 승인 dialog와 전체 workflow 조립.
- `pages/outputs-page/*`
  - `이 영상 편집` 링크와 project lineage 유지.

---

### Task 1: Web API 외부 제작 implementation catalog

**Files:**

- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-model-catalog.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-model-catalog.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/application/shortform-director-generated-media.service.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/application/shortform-director-generated-media.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/presentation/generate-shortform-director-asset.dto.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-assets/presentation/shortform-director-generated-media.openapi.spec.ts`

**Interfaces:**

- Produces:

```ts
export type GeneratedMediaImplementationId =
  | 'google_ai/gemini-3.1-flash-image'
  | 'google_ai/gemini-omni-flash-preview'
  | 'google_ai/veo-3.1-fast-generate-preview';

export interface GeneratedMediaImplementation {
  id: GeneratedMediaImplementationId;
  capabilityId: 'media.image-generation' | 'media.video-generation';
  providerId: 'google_ai';
  modelId: string;
  mediaKind: 'image' | 'video';
  adapter: 'google-interactions-image' | 'google-interactions-video' | 'google-veo';
  isDefault: boolean;
}

export function generatedMediaImplementation(
  id: string,
): GeneratedMediaImplementation | null;
```

- 텍스트 inference profile 표도 model 문자열을 복제하지 않고 같은 registry의
  implementation ID를 참조한 뒤 기존 `{ provider, model }` 결과로 투영한다.
- `quality-review` inference purpose는 기존 동작을 보존하지만 승인된 공개 capability가
  아니므로 이번 catalog 응답에는 노출하지 않는다.
- `GenerateShortformDirectorAssetDto`는 `videoModel` 대신 필수
  `implementationId`를 받는다.
- `expectedModelId`와 credential ID/revision 검증은 그대로 유지한다.

- [ ] **Step 1: catalog 실패 테스트 작성**

```ts
expect(generatedMediaImplementations()).toEqual([
  expect.objectContaining({
    id: 'google_ai/gemini-3.1-flash-image',
    modelId: 'gemini-3.1-flash-image',
    isDefault: true,
  }),
  expect.objectContaining({
    id: 'google_ai/gemini-omni-flash-preview',
    modelId: 'gemini-omni-flash-preview',
    isDefault: true,
  }),
  expect.objectContaining({
    id: 'google_ai/veo-3.1-fast-generate-preview',
    modelId: 'veo-3.1-fast-generate-preview',
    isDefault: false,
  }),
]);
```

- [ ] **Step 2: RED 확인**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-model-catalog.spec.ts
```

Expected: catalog module 또는 export가 없어 실패.

- [ ] **Step 3: immutable catalog 최소 구현**

모델 ID·adapter 선택을 service에서 제거하고 catalog의 `implementationId` 조회 결과만
사용한다. image capability에 video implementation을 전달하거나 알 수 없는 ID를
전달하면 400으로 거부한다.

- [ ] **Step 4: generated-media service·DTO 실패 테스트 추가**

```ts
await expect(service.generate({
  mediaKind: 'video',
  implementationId: 'google_ai/veo-3.1-fast-generate-preview',
  expectedModelId: 'veo-3.1-fast-generate-preview',
  expectedCredentialId,
  expectedCredentialRevision,
  prompt: 'portrait product motion',
  durationMs: 6_000,
})).resolves.toMatchObject({
  providerId: 'google_ai',
  modelId: 'veo-3.1-fast-generate-preview',
});
```

알 수 없는 ID, media kind 불일치, 승인 model 불일치, credential revision 불일치도 각각
400/409를 검증한다.

- [ ] **Step 5: service·DTO·OpenAPI 최소 구현**

`implementation.adapter`로 기존 Omni/Veo/image private method를 선택한다. provider
HTTP request와 응답 parsing은 변경하지 않는다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-assets/domain/shortform-director-generated-media-catalog.spec.ts \
  src/modules/shortform-director-assets/application/shortform-director-generated-media.service.spec.ts \
  src/modules/shortform-director-assets/presentation/shortform-director-generated-media.openapi.spec.ts
npm run build
```

Expected: 대상 suite와 build 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 2: Web API 안전한 production capability endpoint

**Files:**

- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/application/shortform-director-production-capability.service.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/application/shortform-director-production-capability.service.spec.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.controller.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.controller.spec.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.openapi.spec.ts`
- Create:
  `web/clipper_web_api/src/modules/shortform-director-production/shortform-director-production.module.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-model-catalog.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**

- Produces authenticated
  `GET /shortform-director/production-capabilities`:

```ts
interface ProductionCapabilityCatalogV1 {
  schemaVersion: 'production-capability-catalog.v1';
  generatedAt: string;
  capabilities: Array<{
    capabilityId: string;
    label: string;
    defaultImplementationId: string;
    implementations: Array<{
      id: string;
      providerId: 'openai' | 'google_ai';
      modelId: string;
      label: string;
      selectable: boolean;
      ready: boolean;
      unavailableReason: 'credential_missing' | null;
    }>;
  }>;
}
```

- API key, secret, encrypted value는 응답에 포함하지 않는다.
- `ready`는 OpenAI/Google AI 활성 credential 상태에서 계산한다.

- [ ] **Step 1: service RED 테스트**

텍스트 기본값과 generated-media 기본값, Omni/Veo 선택 가능 여부, credential 없는 경우
`ready=false`를 검증한다.

- [ ] **Step 2: RED 확인**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-production/application/shortform-director-production-capability.service.spec.ts
```

Expected: 새 service가 없어 실패.

- [ ] **Step 3: service 최소 구현**

기존 inference catalog와 Task 1 media catalog를 import해 투영하고
`OpenAiCredentialService.inspectRuntime()`과
`GoogleAiCredentialService.inspectRuntime()`만 사용한다.

- [ ] **Step 4: controller·JWT·OpenAPI RED 테스트**

인증 없이는 401, 인증 시 raw catalog 반환, OpenAPI 응답에 `secret/apiKey`가 없음을
검증한다.

- [ ] **Step 5: module/controller 최소 구현**

`ProviderCredentialsModule`을 import하고 root app module에 새 module을 등록한다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-production
npm run build
```

Expected: 대상 suite와 build 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 3: Desktop 통합 capability catalog와 기본값 endpoint

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-capability.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-production-capability-web-api.client.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-production-capability.service.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-production-capability.controller.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-production-capability.test.js`

**Interfaces:**

- Produces:
  `GET /v1/projects/shortform-director/production-capabilities`
- Output schema:

```ts
interface ProductionCapabilityCatalogV1 {
  schemaVersion: 'production-capability-catalog.v1';
  generatedAt: string;
  capabilities: ProductionCapabilityEntryV1[];
}

interface ProductionCapabilityEntryV1 {
  capabilityId: string;
  label: string;
  defaultImplementationId: string;
  implementations: Array<{
    id: string;
    providerId: string;
    modelId: string | null;
    label: string;
    selectable: boolean;
    ready: boolean;
    unavailableReason: 'credential_missing' | 'not_connected' | null;
  }>;
}
```

- Local implementations:
  - `naver.image-search`
  - `local.tts.supertone`
  - `local.render.motion-canvas`
- Web API 응답에 없는 외부 model ID를 Desktop에서 새로 정의하지 않는다.

- [ ] **Step 1: parser/client RED 테스트**

잘못된 schema, duplicate implementation ID, default 미존재, secret-like key가 포함된
응답을 거부하는 테스트를 작성한다.

- [ ] **Step 2: RED 확인**

Run:

```bash
npm run build
node --test test/shortform-director-production-capability.test.js
```

Expected: 새 dist module이 없어 실패.

- [ ] **Step 3: domain parser와 Web API client 최소 구현**

`WebApiClient.getJson('/shortform-director/production-capabilities')`을 사용하고 bearer
token을 전달한다.

- [ ] **Step 4: local 합성·ownership controller RED 테스트**

Omni가 video default이고, Veo가 selectable이며, local tool에는 model이 null일 수 있음을
검증한다.

- [ ] **Step 5: service/controller/module 최소 구현**

controller는 `AuthContextService`로 현재 사용자를 확인한 뒤 service에 bearer token을
전달한다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
npm run build
node --test test/shortform-director-production-capability.test.js
```

Expected: 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 4: Angular 기본 제작 모델 표시와 비교 전용 스캐폴드 제거

**Files:**

- Create:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production-capability.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-model-summary/production-model-summary.component.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-model-summary/production-model-summary.component.html`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-model-summary/production-model-summary.component.scss`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-model-summary/production-model-summary.component.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-project.service.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-project.service.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.{ts,html,scss,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-video-model-comparison.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-video-model-comparison.gateway.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-video-model-comparison.service.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-video-model-comparison.service.spec.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-video-model-comparison.store.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-video-model-comparison.store.spec.ts`
- Delete:
  `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-video-model-comparison.fixtures.ts`

**Interfaces:**

- `ShortformDirectorProjectService.getProductionCapabilities()`.
- Store signals:

```ts
readonly productionCapabilities =
  signal<ProductionCapabilityCatalogV1 | null>(null);
readonly loadingProductionCapabilities = signal(false);
readonly productionCapabilityError =
  signal<ResolvedPresentation | null>(null);
```

- [ ] **Step 1: service/store RED 테스트**

endpoint URL, catalog load, 실패 표시, production selection load와 병렬 실행을 검증한다.

- [ ] **Step 2: RED 확인**

Run:

```bash
npm test -- --watch=false \
  --include='src/features/shortform-director/services/shortform-director-project.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: 새 method/signal이 없어 실패.

- [ ] **Step 3: service/store 최소 구현**

catalog 실패는 영상 계획 자체를 지우지 않고 요약 영역에만 오류를 표시한다.

- [ ] **Step 4: component RED 테스트**

다음을 검증한다.

```ts
expect(text).toContain('현재 제작 모델');
expect(text).toContain('gemini-omni-flash-preview');
expect(text).toContain('기본');
expect(text).toContain('veo-3.1-fast-generate-preview');
expect(text).toContain('기본값 변경 기능은 추후 제공');
```

credential이 없으면 `설정 필요`, local tool은 정상 표시한다.

- [ ] **Step 5: 4파일 component와 production page 조립**

Material expansion/button/chip 계열과 semantic tokens만 사용한다.

- [ ] **Step 6: 비교 스캐폴드 삭제와 fixture 정정**

모든 import를 제거하고 production fixture의 기본 generated image/video를
`gemini-3.1-flash-image`와 `gemini-omni-flash-preview`로 맞춘다.

- [ ] **Step 7: GREEN 확인**

Run:

```bash
npm test -- --watch=false \
  --include='src/features/shortform-director/components/production-model-summary/production-model-summary.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
npm run build
```

Expected: 통과하고 삭제 파일 import 0건.

- [ ] **Step 8: 변경 검토 준비**

Run:

```bash
rg -n "video-model-comparison|ShortformDirectorVideoModelProfile" src
git diff --check
```

Expected: 검색 결과와 whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 5: Desktop 장면 편집 초안과 JSON 저장

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/scene-production.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-edit.service.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-scene.dto.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-layer.dto.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-scene-edit.controller.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director-project.repository.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/json-shortform-director-project.repository.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-project.mapper.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-project-production-state.test.js`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-scene-edit.test.js`

**Interfaces:**

```ts
interface ShortformDirectorProductionStateV1 {
  schemaVersion: 'shortform-director-production-state.v1';
  catalogSnapshot: ProductionCapabilityCatalogV1 | null;
  activeSceneMediaRevisions: Array<{ layerId: string; revisionId: string }>;
  activeNarrationRevisions: Array<{ cueId: string; revisionId: string }>;
  activeRenderRevisionId: string | null;
}

interface SceneLayerProductionSettingsV1 {
  schemaVersion: 'scene-layer-production-settings.v1';
  prompt: string | null;
  searchQuery: string | null;
  implementationId: string | null;
}
```

- `ShortformDirectorProject.production`이 pointer와 catalog snapshot을 저장한다.
- `VideoPlanLayer.production?`이 prompt/search query/implementation override를 저장한다.
- strategy는 기존 `assetStrategy`, source IDs는 기존 `productionSourceIds`, 문구는 기존
  `content`를 계속 단일 출처로 사용한다.
- `GET .../:projectId/scene-production-state`는 project에서 편집용 view를 투영한다.
- `PATCH .../:projectId/scenes/:sceneId`
- `PATCH .../:projectId/scenes/:sceneId/layers/:layerId`

- [ ] **Step 1: legacy/new project state RED 테스트**

기존 `projects.json`은 production/layer settings를 메모리에서 안전하게 hydrate하되 읽기
시 파일을 다시 쓰지 않고, 신규 candidate project에는 empty production state가 생기는지
검증한다.

- [ ] **Step 2: RED 확인**

Run:

```bash
npm run build
node --test \
  test/shortform-director-project-production-state.test.js \
  test/shortform-director-scene-edit.test.js
```

Expected: 새 module이 없어 실패.

- [ ] **Step 3: project production state·CAS 저장 최소 구현**

project JSON에는 작은 pointer·settings만 저장한다. repository에
`replaceIfCurrent(project, expectedUpdatedAt)`를 추가하고 temp+rename 기반 atomic
replace로 동시 render/regeneration lost update를 막는다.

- [ ] **Step 4: service/controller RED 테스트**

다음을 검증한다.

- owner가 아니면 404
- 없는 scene/layer는 404
- unsupported strategy/model 조합은 400
- 편집 저장만으로 기존 active asset binding을 바꾸지 않음
- prompt/search query의 불필요한 필드는 null로 정규화
- scene PATCH는 narration cue와 text layer content만 바꾸며 ID/order/timing을 받지 않음
- text layer만 변경하면 visual active revision과 binding을 유지
- narration text 변경은 narration을 stale로 표시하되 이전 WAV는 성공 재합성 전 보존

- [ ] **Step 5: service/controller/module 최소 구현**

`ShortformDirectorProductionCapabilityService`를 통해 implementation을 검증하고 API key나
credential 값을 project에 저장하지 않는다. `owned/unresolved`는 편집 선택에서
거부한다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
npm run build
node --test \
  test/shortform-director-project-production-state.test.js \
  test/shortform-director-scene-edit.test.js
```

Expected: 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 6: 단일 레이어 실제 재생성·append-only revision

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/scene-media-revision.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/scene-media-revision.repository.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/artifact-shortform-director-scene-media-revision.repository.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-scene-media-revision-artifact.validator.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-layer-asset-executor.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-media.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-automatic-asset.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-generated-media-web-api.client.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-scene-edit.controller.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/regenerate-shortform-director-layer.dto.ts`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-scene-media-revision.test.js`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-scene-media-regeneration.test.js`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-scene-media-revision-activation.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-automatic-asset-preparation.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-generated-media-client.test.js`

**Interfaces:**

- `GET .../layers/:layerId/regeneration-preflight`
- `POST .../layers/:layerId/regenerations`
- `GET .../layers/:layerId/revisions`
- `POST .../layers/:layerId/revisions/:revisionId/activate`
- Web API client request:

```ts
interface GenerateShortformDirectorMediaRequest {
  mediaKind: 'image' | 'video';
  implementationId: string;
  prompt: string;
  durationMs?: number;
  bearerToken: string;
  expectedCredentialId: string;
  expectedCredentialRevision: string;
  expectedModelId: string;
}
```

- [ ] **Step 1: revision 상태 전이 RED 테스트**

queued→running→succeeded/failed만 허용하고 성공 revision의 result와 실패 revision의
failure를 필수로 검증한다. revision ID에는 project/layer/input fingerprint를 포함한
stable digest를 사용한다.

- [ ] **Step 2: RED 확인**

Run:

```bash
npm run build
node --test test/shortform-director-scene-media-revision.test.js
```

Expected: 새 domain module이 없어 실패.

- [ ] **Step 3: revision domain·immutable JSON 저장 최소 구현**

기존 `ShortformDirectorArtifactRegistry` 위에 typed repository를 만들고
`queued/running/succeeded|failed` 상태마다 서로 다른 immutable snapshot artifact를
append한다. 같은 revision ID에서는 가장 높은 sequence가 현재 상태이고 이전 sequence는
그대로 남는다. public artifact validator는 owner/project/scene/layer/revision/status
entity refs와 secret/raw/base64 부재를 검증한다.

- [ ] **Step 4: layer materializer 추출 회귀 테스트**

기존 batch auto-prepare에서 source/search/generated-image/generated-video/programmatic
결과와 rights 차단이 변하지 않음을 기존 테스트로 고정한다.

- [ ] **Step 5: materializer 최소 추출**

`ShortformDirectorAutomaticAssetService`의 한 레이어 준비 책임을
`ShortformDirectorLayerAssetExecutor.execute()`로 옮긴다. executor는 provider 호출과
binary materialization 결과만 반환하고 project/revision/binding 저장은 하지 않는다.
batch service는 requirement loop와 승인 조율만 유지한다.

- [ ] **Step 6: implementationId client RED/GREEN**

Desktop client가 `videoModel`을 보내지 않고 `implementationId`를 보내며 Web API 응답의
model·credential revision을 계속 대조하게 한다.

- [ ] **Step 7: preflight RED 테스트**

preflight approval ID는 다음의 canonical JSON digest여야 한다.

```ts
{
  approvalVersion: 'scene-media-regeneration-cost.v1',
  projectId,
  projectUpdatedAt,
  sceneId,
  layerId,
  inputFingerprint,
  implementationId,
  providerId,
  modelId,
  credentialId,
  credentialRevision,
  maxCalls: 1,
  estimatedCostUsd,
}
```

project/draft/model/credential revision이 바뀌면 기존 승인을 거부한다.

- [ ] **Step 8: 실제 단일 레이어 orchestration 최소 구현**

실패 시 기존 binding을 유지하고 failed revision을 저장한다. 성공 시 새 asset ref와
revision을 먼저 저장한 뒤 binding과 active pointer를 새 결과로 전환한다.

`programmatic`은 provider 호출과 binary asset이 없으므로 `status:'succeeded'`,
`result:null`로 기록하고 layer 설정 snapshot을 결과 근거로 사용한다. search는 파일
준비에 성공해도 권리가 확인되지 않았으면 succeeded revision만 보존하고 active
pointer/binding을 바꾸지 않는다.

- [ ] **Step 9: 과거 revision 활성화·재사용 테스트와 구현**

성공 revision의 artifact가 존재하고 checksum이 맞을 때 provider 호출 0회로 다시
활성화한다. search revision은 `rightsConfirmed:true` 이후에만 활성화한다. checksum
불일치면 409로 거부한다. 과거 revision 재활성화를 위해 unbound assetRef를 prune하지
않는다.

- [ ] **Step 10: GREEN 확인**

Run:

```bash
npm run build
node --test \
  test/shortform-director-generated-media-client.test.js \
  test/shortform-director-automatic-asset-preparation.test.js \
  test/shortform-director-scene-media-revision.test.js \
  test/shortform-director-scene-media-regeneration.test.js \
  test/shortform-director-scene-media-revision-activation.test.js
```

Expected: 통과.

- [ ] **Step 11: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 7: Angular 장면·레이어 편집과 revision UI

**Files:**

- Create:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-scene-edit.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-scene-production.gateway.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-scene-production.service.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-scene-production.service.spec.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-scene-production.store.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-scene-production.store.spec.ts`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-scene-card/production-scene-card.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-scene-content-form/production-scene-content-form.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-layer-card/production-layer-card.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-layer-editor/production-layer-editor.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-source-strategy-form/production-source-strategy-form.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-search-strategy-form/production-search-strategy-form.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-generated-media-strategy-form/production-generated-media-strategy-form.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-programmatic-strategy-form/production-programmatic-strategy-form.component.{ts,html,scss,spec.ts}`
- Create:
  `desktop/clipper_angular/src/features/shortform-director/components/production-revision-history/production-revision-history.component.{ts,html,scss,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/production-scene-plan/production-scene-plan.component.{ts,html,scss}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/production-scene-plan/production-scene-plan.component.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.{ts,html,scss,spec.ts}`

**Interfaces:**

- Store methods:

```ts
loadSceneProductionState(): Promise<void>;
updateScene(sceneId: string, request: UpdateSceneRequest): Promise<void>;
updateLayer(
  sceneId: string,
  layerId: string,
  request: UpdateLayerRequest,
): Promise<void>;
loadLayerPreflight(sceneId: string, layerId: string): Promise<void>;
regenerateLayer(
  sceneId: string,
  layerId: string,
  approvalVersion: string,
  approvalId: string,
): Promise<void>;
activateLayerRevision(
  sceneId: string,
  layerId: string,
  revisionId: string,
): Promise<void>;
```

- `ShortformDirectorSceneProductionStore`가 위 메서드와 layer별 pending/error를 소유한다.
- `ShortformDirectorProductionStore`는 현재 project snapshot의 단일 출처이며
  `acceptProjectSnapshot(project)`에서 project ID를 검증한다.
- Scene store는 성공한 응답만 Production store에 전달하고 candidate-run gateway에
  project-scoped 편집 API를 섞지 않는다.

- [ ] **Step 1: HTTP service RED 테스트**

모든 URL segment가 `encodeURIComponent`되고 PATCH/GET/POST body가 계약과 일치하는지
검증한다.

- [ ] **Step 2: store RED 테스트**

편집 중복 실행 차단, 다른 레이어 상태 보존, 재생성 실패 시 기존 project 유지, 성공 후
project/state/revision 재조회, stale approval 무시를 검증한다.

- [ ] **Step 3: RED 확인**

Run:

```bash
npm test -- --watch=false \
  --include='src/features/shortform-director/services/shortform-director-scene-production.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-scene-production.store.spec.ts'
```

Expected: 새 method/type이 없어 실패.

- [ ] **Step 4: models/service/store 최소 구현**

레이어별 pending/error map을 사용해 한 장면 작업이 다른 장면 editor를 막지 않게 한다.

- [ ] **Step 5: layer editor RED 테스트**

다음을 검증한다.

- `programmatic`: model dropdown 없음
- `search`: 검색어 입력과 Naver provider 표시
- `generated-image`: image capability 구현만 표시
- `generated-video`: Omni 기본 선택, Veo Fast 선택 가능
- `ready=false`: 선택은 보이지만 다시 만들기 비활성
- 저장만으로 외부 호출 confirm dialog가 열리지 않음

- [ ] **Step 6: scene/layer editor 4파일 구현**

기존 `production-scene-plan`은 목록 container로 유지하고 scene card에 위임한다. scene
content, layer card/editor, source/search/generated/programmatic form을 위 파일 경계대로
분리한다. Material form-field/select/input/button/expansion을 사용하고 raw 색상을
추가하지 않는다.

- [ ] **Step 7: revision history RED 테스트와 구현**

현재 revision, provider/model/tool, prompt/search query, artifact checksum, 생성 시각,
실패 상태를 표시하고 성공한 과거 revision에만 `이 버전 사용`을 제공한다.

- [ ] **Step 8: 비용 승인 dialog 연결**

dialog에는 provider, model, 최대 1회, credential revision label, 예상 USD 범위,
approval ID를 표시한다. 확인 전 POST를 호출하지 않는다.

- [ ] **Step 9: GREEN 확인**

Run:

```bash
npm test -- --watch=false \
  --include='src/features/shortform-director/components/production-scene-card/production-scene-card.component.spec.ts' \
  --include='src/features/shortform-director/components/production-scene-content-form/production-scene-content-form.component.spec.ts' \
  --include='src/features/shortform-director/components/production-layer-card/production-layer-card.component.spec.ts' \
  --include='src/features/shortform-director/components/production-layer-editor/production-layer-editor.component.spec.ts' \
  --include='src/features/shortform-director/components/production-*-strategy-form/*.spec.ts' \
  --include='src/features/shortform-director/components/production-revision-history/production-revision-history.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-scene-production.store.spec.ts'
npm run build
```

Expected: 통과.

- [ ] **Step 10: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 8: 장면 내레이션·화면 문구 편집과 부분 TTS 재생성

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/narration-revision.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration-cue-synthesizer.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-narration.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-scene-edit.controller.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/regenerate-shortform-director-scene-narration.dto.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-narration-regeneration.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-narration-audio.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-tts-timing-alignment.test.js`
- Modify Angular scene editor/store/service files from Task 7.

**Interfaces:**

- `GET .../scenes/:sceneId/narration-regeneration-preflight`
- `POST .../scenes/:sceneId/narration-regenerations`
- Preflight에는 changed cue IDs, provider `tts.supertone`, model null, 외부 유료 호출 0을
  표시한다.

- [ ] **Step 1: cue synthesizer 추출 회귀 테스트**

전체 narration synthesize의 WAV/mediaType/checksum/duration validation과 실패 시 현재
project 유지가 변하지 않음을 고정한다.

- [ ] **Step 2: cue synthesizer 최소 추출**

full narration service와 scene narration service가 같은
`ShortformDirectorNarrationCueSynthesizer`를 사용하게 한다.

- [ ] **Step 3: 부분 재생성 RED 테스트**

한 cue 문구만 바꾸면 해당 cue provider 호출 1회, 나머지 artifact ID 유지, 새 cue
artifact 생성, 전체 timing alignment 갱신, 시각 asset binding 유지가 되는지 검증한다.

- [ ] **Step 4: old artifact 보존과 revision audit 구현**

현재 full narration service의 성공 후 이전 WAV 삭제를 중단하고, narration operation
artifact와 scene production state에 이전/현재 cue revision 연결을 남긴다.

- [ ] **Step 5: Nest GREEN 확인**

Run:

```bash
npm run build
node --test \
  test/shortform-director-narration-audio.test.js \
  test/shortform-director-tts-timing-alignment.test.js \
  test/shortform-director-narration-regeneration.test.js
```

Expected: 통과.

- [ ] **Step 6: Angular narration edit RED 테스트**

내레이션 저장은 외부 호출 없이 draft만 갱신하고, `음성 다시 만들기`에서 영향 cue를
보여준 뒤 해당 endpoint만 호출하는지 검증한다.

- [ ] **Step 7: Angular 최소 구현과 GREEN**

Run:

```bash
npm test -- --watch=false \
  --include='src/features/shortform-director/components/production-scene-content-form/production-scene-content-form.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-scene-production.store.spec.ts'
npm run build
```

Expected: 통과.

- [ ] **Step 8: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 9: 완성 영상에서 편집 복귀·새 render revision

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/render-revision.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/outputs-page/outputs-page.component.{ts,html,scss,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.{ts,html,spec.ts}`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-operation.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-workflow.executor.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-vault-publisher.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-vault.storage.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-vault-thumbnail.generator.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/render-operation.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-render-operation.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-director-vault-publish.test.js`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-render-revision.test.js`
- Modify test:
  `desktop/clipper_nestjs/test/shortform-project-generation-assets.test.js`

**Interfaces:**

- Production route supports `?projectId=<id>` without candidateRunId/candidateId/profileId.
- `ShortformDirectorProductionStore.loadProject(projectId)` loads project, capability catalog,
  scene production state, asset preflight, narration presets, render history, artifacts.
- terminal render operation이 있어도 새 render input stage와 operation을 만들 수 있다.
- 각 render revision은 실행에 사용한 scene media revision IDs와 narration revision IDs를
  snapshot으로 가진다.
- 보관함 MP4 경로는
  `renders/revisions/<renderRevisionId>/main.mp4`이며 기존 revision 파일을 덮어쓰지
  않는다.

- [ ] **Step 1: project 직접 로드 RED 테스트**

candidate selection 없이 projectId만으로 production page가 기존 project를 불러오고 편집
UI를 표시하는지 검증한다.

- [ ] **Step 2: output edit link RED 테스트**

`이 영상 편집`이
`/shortform/director/production?projectId=<encoded>`로 이동하는지 검증한다.

- [ ] **Step 3: Angular 최소 구현**

selection과 projectId가 동시에 있으면 projectId 직접 편집을 우선하고, 둘 다 없을 때만
empty state를 보여준다.

- [ ] **Step 4: re-render RED 테스트**

완료된 operation이 이미 있어도 새 stage와 새 operation/output ID가 생성되고 기존
output 파일을 덮어쓰지 않는지 검증한다. 두 번 성공한 렌더는 서로 다른
`renders/revisions/<id>/main.mp4`와 thumbnail을 남기고, 최신 pointer만 새 revision을
가리켜야 한다.

- [ ] **Step 5: Nest/store 최소 구현**

waiting/starting/running operation이 있을 때만 중복 시작을 막고
succeeded/failed/cancelled는 render history로 유지한다. Jobs queue와 unique render
output storage는 재사용하고 vault publication만 versioned no-replace 경로로 바꾼다.
실패/cancel은 이전 active render revision과 MP4를 유지한다. `ProjectsService`는 literal
`renders/main.mp4`가 아니라 검증된 versioned relative path를 사용한다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-render-operation.test.js \
  test/shortform-director-vault-publish.test.js \
  test/shortform-director-render-revision.test.js \
  test/shortform-project-generation-assets.test.js
cd ../clipper_angular
npm test -- --watch=false \
  --include='src/features/shortform-director/pages/outputs-page/outputs-page.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
npm run build
```

Expected: 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 10: 전체 다시 만들기와 변경 없는 artifact 재사용

**Files:**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-scene-media.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-scene-edit.controller.ts`
- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/regenerate-shortform-director-project.dto.ts`
- Test:
  `desktop/clipper_nestjs/test/shortform-director-project-regeneration.test.js`
- Modify Angular production store/page/scene editor files.

**Interfaces:**

- `GET .../:projectId/regeneration-preflight`
- `POST .../:projectId/regenerations`
- Preflight는 changed/reused layer 수, provider별 최대 호출 수, credential revisions,
  implementation IDs, 총 예상 비용을 반환한다.

- [ ] **Step 1: full preflight RED 테스트**

동일 input fingerprint+존재하는 artifact+일치 checksum은 `reused`, 변경 draft나 사용자가
명시적으로 다시 만들기를 선택한 레이어는 `regenerated`로 분류하는지 검증한다.

- [ ] **Step 2: project regeneration RED 테스트**

레이어 3개 중 1개만 변경하면 provider 호출 1회, 나머지 artifact ID 유지, operation
audit에는 reused 2/regenerated 1이 남는지 검증한다.

- [ ] **Step 3: Nest 최소 구현**

단일 레이어 service를 순차 호출하되 모든 레이어를 한 거대한 transaction으로 숨기지
않는다. 각 revision 성공/실패를 독립 보존하고 최종 요약을 저장한다.

- [ ] **Step 4: Angular 전체 다시 만들기 RED 테스트**

비용 dialog 승인 전 POST 0회, 승인 뒤 한 번 호출, 완료 후 project/state/artifact/render
readiness 새로고침을 검증한다.

- [ ] **Step 5: Angular 최소 구현**

`전체 다시 만들기`는 production page 상단 workflow action으로 제공하고 진행 중 장면
편집을 잠그되 기존 미리보기는 유지한다.

- [ ] **Step 6: GREEN 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-scene-media-revision.test.js \
  test/shortform-director-project-regeneration.test.js
cd ../clipper_angular
npm test -- --watch=false \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
npm run build
```

Expected: 통과.

- [ ] **Step 7: 변경 검토 준비**

Run: `git diff --check`

Expected: whitespace 오류 없음. 커밋은 하지 않는다.

---

### Task 11: 통합 회귀·런타임 검증

**Files:**

- No files planned. 검증 실패가 나오면 `superpowers:systematic-debugging`으로 Tasks 1–10의
  변경에서 비롯된 원인을 먼저 확인하고, 원인 파일만 별도 RED/GREEN 사이클로 수정한다.
  unrelated pre-existing failure는 수정하지 않는다.

- [ ] **Step 1: 금지·불변식 정적 검사**

Run:

```bash
rg -n "video-model-comparison|ShortformDirectorVideoModelProfile" \
  desktop/clipper_angular/src \
  desktop/clipper_nestjs/src \
  web/clipper_web_api/src
rg -n "credit|consumeCredit|deductCredit" \
  desktop/clipper_angular/src/features/shortform-director \
  desktop/clipper_nestjs/src/modules/shortform-director
git -C web/clipper_web_api diff --check
git -C desktop/clipper_nestjs diff --check
git -C desktop/clipper_angular diff --check
```

Expected: 비교 전용·credit 신규 경로 없음, whitespace 오류 없음.

- [ ] **Step 2: Web API 전체 회귀**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand
npm run build
```

Expected: 전체 통과.

- [ ] **Step 3: Desktop Nest 전체 Director 회귀**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-*.test.js
```

Expected: 전체 Director 테스트 통과. 기존 명시적 render integration skip만 허용.

- [ ] **Step 4: Angular 전체 회귀**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false
npm run build
```

Expected: 전체 통과.

- [ ] **Step 5: 로컬 런타임 smoke**

실제 provider를 호출하지 않는 상태로 Web API와 Desktop Nest를 기동해 다음을 확인한다.

- production capability endpoint 200
- Angular production route에서 기본 모델 요약 렌더
- 기존 projectId 직접 진입
- 장면 draft 저장 후 앱 재시작에도 JSON 유지
- 실제 외부 호출 버튼은 preflight 승인 dialog 전까지 호출 0회

- [ ] **Step 6: 실제 유료 호출 전 중지·보고**

다음 실호출 세트를 실행하기 전에 사용자에게 정확히 보고하고 승인받는다.

- generated image 1회
- Omni generated video 1회
- 필요하면 동일 장면 Veo Fast 1회
- Naver image search 1회 이상
- 최종 Motion Canvas render 1회

보고에는 provider, model, duration, 최대 호출 수, 현재 가격 기준 예상 USD 범위를
포함한다.

- [ ] **Step 7: 최종 변경 검토**

각 repository의 status, diff stat, 관련 테스트 결과, 미실행 실호출을 정리한다. 커밋과
push는 사용자가 요청하기 전 실행하지 않는다.
