# AI 숏폼 디렉터 장면 미디어 실패 진단 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 장면 미디어 결정 LLM 지시문을 실제 검증 규칙과 맞추고, 실패 시 provider 원문 없이 원인 판별에 필요한 안전한 진단만 로컬 JSON에 저장한다.

**Architecture:** Web API는 기존 모델·응답 스키마·최대 호출 수를 유지하면서 `scene-media-decision` 프롬프트 계약만 v2로 올린다. Desktop Nest는 `WebApiProviderError.responseBody`를 별도 순수 projector에서 허용 목록 DTO로 변환하고 후보 제작 실패 산출물에만 연결한다.

**Tech Stack:** NestJS 11/Jest (`clipper_web_api`), NestJS 10/TypeScript/`node:test` (`clipper_nestjs`), 로컬 JSON artifact registry

## Global Constraints

- 자동 재시도를 추가하지 않고 영상 기획 외부 호출은 최대 2회를 유지한다.
- 모델은 `openai/gpt-5.6-luna`, 승인 버전과 예상 비용은 변경하지 않는다.
- provider 원문, 파싱 출력, 프롬프트, 입력 본문, 인증값, 예외 원인과 스택을 저장하지 않는다.
- Web API와 Desktop Nest는 각각 별도 커밋하며 각 커밋은 관련 테스트가 통과해야 한다.

---

### Task 1: 장면 미디어 결정 프롬프트 계약 v2

**Files:**
- Create: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`

**Interfaces:**
- Consumes: `INFERENCE_PURPOSE_SPECS['scene-media-decision']`
- Produces: `promptTemplateVersion = 'shortform-director.scene-media-decision.v2'`와 검증 규칙을 명시한 `systemPrompt`

- [ ] **Step 1: 실패하는 프롬프트 계약 테스트 작성**

```ts
import { INFERENCE_PURPOSE_SPECS } from './shortform-director-inference.prompt.js';

describe('scene media decision prompt contract', () => {
  it('states every conditional validator rule and uses prompt v2', () => {
    const spec = INFERENCE_PURPOSE_SPECS['scene-media-decision'];
    expect(spec.promptTemplateVersion).toBe(
      'shortform-director.scene-media-decision.v2',
    );
    [
      'exactly one decision for every input scene',
      'zero-based sceneIndex',
      'productionSourceIds',
      'factualRisk is high',
      'official-source',
      'searchBrief',
      'generationBrief',
      'only identifiers supplied in the input',
    ].forEach((text) => expect(spec.systemPrompt).toContain(text));
  });
});
```

- [ ] **Step 2: 테스트가 현재 v1 프롬프트 때문에 실패하는지 확인**

Run:

```bash
npm test -- --runInBand src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
```

Expected: `promptTemplateVersion`이 v1이고 필수 문구가 없어 FAIL.

- [ ] **Step 3: 프롬프트 버전과 지시문 최소 수정**

`spec()`의 버전 분기에 `scene-media-decision` v2를 추가하고, 해당 system prompt를 다음 규칙으로 구성한다.

```ts
[
  'Choose the best medium independently for each scene and return exactly one decision for every input scene using its zero-based sceneIndex.',
  'Use only evidenceIds and productionSourceIds supplied in the input.',
  'When medium is official-source, fallbackMedium is official-source, or factualRisk is high, include at least one productionSourceId tied to that scene evidence.',
  'For image-search set a concrete searchBrief; otherwise set searchBrief to null.',
  'For generated-image or generated-video set a concrete generationBrief; otherwise set generationBrief to null.',
  'Use generated media only for conceptual visuals and never as factual proof.',
  'Return only JSON matching the provided schema.',
].join(' ')
```

- [ ] **Step 4: 프롬프트 및 inference 회귀 테스트**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-model-catalog.spec.ts
npm run build
```

Expected: 모든 테스트와 빌드 PASS.

- [ ] **Step 5: Web API 커밋**

```bash
git add \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
git commit -m "fix(shortform-director): align scene media prompt"
```

---

### Task 2: provider 실패 안전 진단 projector와 로컬 산출물

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-provider-failure-diagnostic.ts`
- Create: `desktop/clipper_nestjs/test/shortform-director-provider-failure-diagnostic.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`

**Interfaces:**
- Consumes: `unknown` error, 특히 `WebApiProviderError`
- Produces:

```ts
export interface ShortformDirectorProviderFailureDiagnosticV1 {
  schemaVersion: 'shortform-director-provider-failure-diagnostic.v1';
  code: string;
  webApiStatus: number;
  upstreamStatus: number | null;
  validationIssues: Array<{ path: string; keyword: string }>;
  tokenUsage: {
    inputCount: number | null;
    outputCount: number | null;
    reasoningCount: number | null;
  };
  latencyMs: number | null;
}

export function projectShortformDirectorProviderFailureDiagnostic(
  error: unknown,
): ShortformDirectorProviderFailureDiagnosticV1 | null;
```

- [ ] **Step 1: projector 실패 테스트 작성**

테스트는 `WebApiProviderError`에 안전 필드와 함께 `raw`, `text`, `parsed`, 프롬프트 및 인증 문자열을 넣는다. 결과가 코드·상태·검증 위치·토큰·지연 시간만 포함하고 금지 문자열을 포함하지 않는다고 검증한다. 알 수 없는 코드나 비정상 타입은 `null`을 반환해야 한다.

```js
const error = new WebApiProviderError('safe', 502, {
  code: 'SHORTFORM_DIRECTOR_INFERENCE_OUTPUT_SCHEMA_INVALID',
  audit: {
    request: { userPrompt: 'MUST_NOT_PERSIST' },
    response: {
      status: 200,
      raw: 'MUST_NOT_PERSIST',
      parsed: { secret: 'MUST_NOT_PERSIST' },
      validation: {
        passed: false,
        issues: [{ path: '/decisions/0/productionSourceIds', keyword: 'minItems' }],
      },
    },
    usage: { inputTokens: 4100, outputTokens: 900, reasoningTokens: 80 },
    latencyMs: 7200,
  },
});
```

- [ ] **Step 2: projector 테스트 RED 확인**

Run:

```bash
npm run build
node --test test/shortform-director-provider-failure-diagnostic.test.js
```

Expected: 모듈이 존재하지 않아 FAIL.

- [ ] **Step 3: 허용 목록 projector 구현**

구현은 다음만 수행한다.

- `WebApiProviderError`인지 확인한다.
- 알려진 `SHORTFORM_DIRECTOR_INFERENCE_*` 실패 코드만 허용한다.
- HTTP 상태는 100~599 정수만 허용한다.
- 검증 이슈는 최대 20개, path 256자, keyword 80자로 제한한다.
- 토큰 수와 latency는 음수가 아닌 안전한 정수만 허용하고 나머지는 `null`로 둔다.
- 응답 본문 전체를 반환 객체에 spread하지 않는다.

- [ ] **Step 4: candidate production 실패 산출물 연결 테스트 작성**

`createProductionHarness`가 안전한 Web API schema failure body를 던지게 하고,
`candidate-production-failure.v2`에 `providerFailure`가 포함되는지 검증한다.
일반 `Error` 실패에는 `providerFailure`가 없어야 한다.

- [ ] **Step 5: 연결 테스트 RED 확인**

Run:

```bash
npm run build
node --test --test-name-pattern='candidate production persists safe provider diagnostics' \
  test/shortform-director-candidate-production.test.js
```

Expected: 기존 v1 실패 산출물에 `providerFailure`가 없어 FAIL.

- [ ] **Step 6: 실패 산출물 연결**

`failRun()`에서 projector를 한 번 호출하고 결과가 있을 때만 다음을 추가한다.

```ts
const providerFailure =
  projectShortformDirectorProviderFailureDiagnostic(error);

value: {
  schemaVersion: 'shortform-director-candidate-production-failure.v2',
  runId,
  code: 'candidate_production_failed',
  category: failureCategory(error),
  stage,
  detectedAt: this.clock(),
  ...(providerFailure ? { providerFailure } : {}),
}
```

- [ ] **Step 7: Desktop Nest 관련 회귀 검증**

Run:

```bash
npm run build
node --test \
  test/shortform-director-provider-failure-diagnostic.test.js \
  test/shortform-director-artifact-security.test.js \
  test/shortform-director-candidate-generation.test.js \
  test/shortform-director-candidate-production.test.js
```

Expected: 모든 테스트 PASS, artifact 보안 가드가 새 진단 DTO를 허용.

- [ ] **Step 8: Desktop Nest 커밋**

```bash
git add \
  src/modules/shortform-director/application/shortform-director-provider-failure-diagnostic.ts \
  src/modules/shortform-director/application/shortform-director-candidate-production.service.ts \
  test/shortform-director-provider-failure-diagnostic.test.js \
  test/shortform-director-candidate-production.test.js
git commit -m "fix(shortform-director): preserve safe provider diagnostics"
```

---

### Task 3: 통합 확인과 사용자 재실행 준비

**Files:**
- Verify only: `web/clipper_web_api`
- Verify only: `desktop/clipper_nestjs`

**Interfaces:**
- Consumes: Task 1 프롬프트 v2, Task 2 실패 진단 DTO
- Produces: 재실행 가능한 빌드와 정확한 수동 확인 절차

- [ ] **Step 1: 두 저장소 상태와 최종 빌드 확인**

```bash
git -C web/clipper_web_api status --short --branch
git -C desktop/clipper_nestjs status --short --branch
npm --prefix web/clipper_web_api run build
npm --prefix desktop/clipper_nestjs run build
```

Expected: 두 저장소 worktree clean, 두 빌드 PASS.

- [ ] **Step 2: 런타임 반영 절차 안내**

- `clipper_web_api npm run start:dev`는 Task 1 변경을 watch 재시작으로 반영한다.
- Desktop Nest 변경은 Electron 번들에 포함되어야 하므로 앱 종료 후
  `desktop/clipper_electron`에서 `npm run build:app:mac:arm64:local-api`를 실행한다.
- 기존 조사·후보는 재사용하고 같은 후보에서 영상 기획 승인만 다시 실행한다.
- 성공 시 상세 영상 계획과 장면 미디어 결정 두 산출물을 확인한다.
- 실패 시 새 실행의 `candidate-production-failure.v2.providerFailure`만 확인하면 추가 진단 호출 없이 원인을 분류할 수 있다.
