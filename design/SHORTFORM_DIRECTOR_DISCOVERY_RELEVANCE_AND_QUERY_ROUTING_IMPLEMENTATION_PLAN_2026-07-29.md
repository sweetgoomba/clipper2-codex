# AI 숏폼 디렉터 조사 관련성·검색어 라우팅 교정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** 실제 Google Trends·네이버·YouTube 조사에서 운영 프로필과 관련된 자료만 AI
정리와 영상 후보에 사용하고, 공급자별 검색어를 올바르게 라우팅하며, YouTube 페이지
토큰 때문에 발생한 502를 제거하고 조사 근거를 사람이 이해할 수 있게 보여준다.

**Architecture:** Web API는 `query-plan.v2` 구조화 출력과 프롬프트를 소유한다. Nest는
Trends 신호 ID, 검색어 계획 검증, 공급자별 라우팅, 관련 근거만 포함한 정규화 입력과
로컬 JSON artifact 저장을 소유한다. Angular는 승인 비용 상한, 공급자별 실제 검색어,
활용된 근거와 부분 완료 수량을 읽기 쉬운 형태로 표시하고 JSON 원문은 기존 상세
패널에서 계속 제공한다.

**Tech Stack:** NestJS·TypeScript, Node.js 22 `node:test`, Angular standalone
components·Jasmine, Web API NestJS·Jest, OpenAI Responses structured output,
YouTube Data API v3, Naver Search/DataLab API, Google Trends KR Trending RSS,
로컬 JSON artifact 저장소

정본 설계:
`.codex/design/SHORTFORM_DIRECTOR_DISCOVERY_RELEVANCE_AND_QUERY_ROUTING_DESIGN_2026-07-29.md`

## Global Constraints

- 안전하게 투영한 source payload는 관련성 여부와 무관하게 로컬 JSON artifact로
  보존한다. 공급자 HTTP 응답 원문 전체는 저장하지 않는다.
- 선택되지 않은 Google Trends 항목은 source-normalization 입력과 이후 영상 후보 근거에
  포함하지 않는다.
- 네이버 뉴스 검색어는 1~2개, YouTube 검색어는 정확히 1개, DataLab 핵심 키워드는
  1~3개다.
- YouTube는 동일한 YouTube 검색어를 `viewCount`와 `relevance` 두 lane에서 사용한다.
- 검색어 계획 계약이 잘못되면 다른 공급자 검색어로 대체하거나 승인되지 않은 재호출을
  하지 않는다.
- YouTube `nextPageToken`과 `prevPageToken`은 저장 DTO에서 제거하고 credential 보안
  검사는 완화하지 않는다.
- discovery 단계에서는 Gemini 정밀 분석을 호출하지 않는다.
- 실제 공급자 응답 원문 전체, API key, authorization header, credential 원문은 저장하지
  않는다.
- 화면은 `예상 최대 비용`의 maximum만 표시한다. 실제 비용은 확인 가능한 사용량과
  단가가 모두 있을 때만 계산한다.
- fixture와 테스트 더블은 자동 회귀 테스트에만 사용한다. 최종 수용 검증은 사용자가
  등록한 실제 자격 증명과 실제 공급자 응답으로 수행한다.
- 크레딧 차감, Google Trends HTML 스크래핑, Google Trends 공식 API 알파,
  YouTube 페이지네이션, Remotion은 범위 밖이다.
- 기존 `legacy/adlight_python/fastapi_server.spec` 변경은 건드리지 않는다.
- 각 task가 통과하면 변경을 미루지 않고 해당 저장소에 바로 커밋한다.

---

## 파일 구조와 책임

### `desktop/clipper_nestjs`

- Modify:
  `src/modules/shortform-director/application/shortform-director-source-fetch-response.projector.ts`
  - YouTube 응답에서 영속에 필요한 필드만 투영한다.
- Create:
  `src/modules/shortform-director/application/shortform-director-research-query-plan.ts`
  - `query-plan.v2` 결과를 공급자별 실행 계획으로 검증·변환한다.
- Modify:
  `src/modules/shortform-director/application/shortform-director-research-input.builder.ts`
  - Trends ID가 포함된 계획 입력과 선택된 Trends만 포함한 정규화 입력을 만든다.
- Modify:
  `src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
  - Web API의 `query-plan.v2` 출력 구조를 경계에서 검증한다.
- Modify:
  `src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
  - 네이버 뉴스 검색어와 DataLab 키워드를 별도 인자로 받고 source별 오류 단계를
    보존한다.
- Modify:
  `src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
  - 계획 결과를 공급자별로 라우팅하고 관련 Trends 선택을 정규화 입력에 전달한다.
- Modify:
  `src/modules/shortform-director/domain/research-cost-estimate.ts`
  - 네이버 뉴스 1~2개 계약과 일치하는 최대 호출 수를 계산한다.
- Test:
  `test/shortform-director-web-api-clients.test.js`
- Create:
  `test/shortform-director-research-query-plan.test.js`
- Modify:
  `test/shortform-director-reference-candidates.test.js`
- Modify:
  `test/shortform-director-research-orchestrator.test.js`
- Modify:
  `test/shortform-director-research-cost-estimate.test.js`

### `web/clipper_web_api`

- Modify:
  `src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
  - `query-plan.v2` JSON Schema와 로컬 validator를 소유한다.
- Modify:
  `src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
  - 프로필 우선, Trends 선택적 활용, 공급자별 검색어 규칙을 명시한다.
- Modify:
  `src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify:
  `src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Modify:
  `src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts`

### `desktop/clipper_angular`

- Modify:
  `src/features/shortform-director/components/research-preflight-card/research-preflight-card.component.ts`
- Modify:
  `src/features/shortform-director/components/research-preflight-card/research-preflight-card.component.spec.ts`
- Modify:
  `src/features/shortform-director/models/shortform-director-research-artifact-presentation.ts`
- Modify:
  `src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts`
- Modify:
  `src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html`
- Modify:
  `src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.ts`
- Modify:
  `src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.html`
- Modify:
  `src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.spec.ts`
- Modify:
  `src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.html`
- Modify:
  `src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts`
- Modify:
  `src/features/shortform-director/state/shortform-director-research.store.ts`
- Modify:
  `src/features/shortform-director/state/shortform-director-research.store.spec.ts`

---

### Task 1: YouTube 페이지 토큰을 저장 DTO에서 제거

**Files:**

- Modify:
  `desktop/clipper_nestjs/test/shortform-director-web-api-clients.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-source-fetch-response.projector.ts`

**Interfaces:**

- Consumes: Web API가 반환하는 YouTube list 응답
- Produces: `pageInfo`와 `items`만 포함하고 `nextPageToken`,
  `prevPageToken`이 없는 `ShortformDirectorSourceFetchResponse`

- [ ] **Step 1: 페이지 토큰 제거 기대값으로 회귀 테스트를 변경한다**

`youtube-search`, `youtube-videos`, `youtube-comments` raw fixture에는
`nextPageToken`과 `prevPageToken`을 모두 넣고, `expectedData`에서는 두 필드를 제거한다.
각 case의 결과에도 다음 assertion을 추가한다.

```js
assert.equal('nextPageToken' in result.response.data, false);
assert.equal('prevPageToken' in result.response.data, false);
```

- [ ] **Step 2: 테스트가 현재 코드에서 실패하는지 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-web-api-clients.test.js
```

Expected: YouTube projection 결과에 `nextPageToken`이 남아 있어 FAIL.

- [ ] **Step 3: 세 YouTube projector에서 페이지 토큰 투영을 제거한다**

`projectYoutubeSearch`, `projectYoutubeVideos`, `projectYoutubeComments`의 반환 object에서
다음 두 property 작성문만 삭제한다.

```ts
nextPageToken: optionalString(root.nextPageToken),
prevPageToken: optionalString(root.prevPageToken),
```

`youtubeListRoot`, `projectYoutubePageInfo`, item 투영 로직과 artifact credential 차단
규칙은 변경하지 않는다.

- [ ] **Step 4: 대상 테스트와 전체 Shortform Director 테스트를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-web-api-clients.test.js
node --test test/shortform-director*.test.js
```

Expected: 모두 PASS.

- [ ] **Step 5: Nest 저장소에 즉시 커밋한다**

```bash
git add \
  src/modules/shortform-director/application/shortform-director-source-fetch-response.projector.ts \
  test/shortform-director-web-api-clients.test.js
git commit -m "fix: omit YouTube page tokens from research artifacts"
```

---

### Task 2: Web API `query-plan.v2` 구조화 출력 계약

**Files:**

- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts`

**Interfaces:**

- Consumes:
  `{ operatingProfile, focusKeyword, researchWindow, trendingSignals, constraints }`
- Produces:

```ts
interface QueryPlanV2 {
  queries: Array<{
    source: 'naver-news' | 'youtube';
    query: string;
    rationale: string;
  }>;
  datalabKeywords: string[];
  selectedTrendSignals: Array<{
    trendSignalId: string;
    rationale: string;
  }>;
}
```

- [ ] **Step 1: 완전한 v2 출력과 잘못된 공급자 구성을 검증하는 테스트를 작성한다**

`validOutputs['query-plan']`을 다음 의미로 변경한다.

```ts
{
  queries: [
    {
      source: 'naver-news',
      query: '르세라핌 최근 컴백 신곡 뮤직비디오',
      rationale: '최근 공식 발표와 보도를 확인한다.',
    },
    {
      source: 'youtube',
      query: '르세라핌 최신 안무 직캠 쇼츠',
      rationale: '최근 인기 영상과 표현 형식을 확인한다.',
    },
  ],
  datalabKeywords: ['르세라핌'],
  selectedTrendSignals: [],
}
```

다음 경우가 `{ ok: false }`인지 각각 검증한다.

```ts
// YouTube 검색어 없음
{ queries: [{
    source: 'naver-news',
    query: '르세라핌 최근 컴백',
    rationale: '최근 보도를 확인한다.',
  }],
  datalabKeywords: ['르세라핌'], selectedTrendSignals: [] }

// 공급자 enum 위반
{ queries: [
    {
      source: 'google',
      query: '르세라핌 최근 컴백',
      rationale: '지원하지 않는 공급자다.',
    },
    {
      source: 'youtube',
      query: '르세라핌 최신 안무 직캠 쇼츠',
      rationale: '최근 인기 영상을 확인한다.',
    },
  ], datalabKeywords: ['르세라핌'], selectedTrendSignals: [] }

// DataLab 키워드 4개
// Trends 선택 4개
// 중복 trendSignalId
```

prompt version 기대값은 `shortform-director.query-plan.v2`로 변경한다.

- [ ] **Step 2: 계약 테스트가 현재 v1에서 실패하는지 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts
```

Expected: 새 필드와 v2 prompt version을 v1 schema가 거부해 FAIL.

- [ ] **Step 3: JSON Schema와 로컬 validator를 v2로 변경한다**

`QUERY_PLAN_SCHEMA`는 다음 경계를 갖는다.

```ts
queries: arraySchema(queryItemSchema, 3, 2)
datalabKeywords: arraySchema(stringSchema(80), 3, 1)
selectedTrendSignals: arraySchema(selectedTrendSchema, 3, 0)
```

각 `source`는 `enumSchema(['naver-news', 'youtube'])`로 제한한다.
`validateQueryPlan`은 다음 교차 필드 조건도 검사한다.

```ts
const naverCount = queries.filter((query) =>
  query.source === 'naver-news').length;
const youtubeCount = queries.filter((query) =>
  query.source === 'youtube').length;

// naverCount: 1..2, youtubeCount: exactly 1
// datalabKeywords: 1..3, NFKC·trim 기준 중복 없음
// selectedTrendSignals: 0..3, trendSignalId 중복 없음
```

- [ ] **Step 4: query-plan 시스템 프롬프트를 v2로 교체한다**

`spec()`에서 `query-plan`도 v2 version 대상에 포함한다. 시스템 프롬프트에는 다음 규칙을
모두 명시한다.

```text
Treat operatingProfile and focusKeyword as the authority.
Trending signals are optional broad KR signals; select at most three only
when directly relevant, and return an empty selection when none are relevant.
Return one or two naver-news queries, exactly one youtube query, one to three
short DataLab keywords, and the selected trend signal IDs with reasons.
Do not put site:youtube.com or web-search Boolean syntax in the YouTube query.
Do not invent trend signal IDs.
Use the supplied researchWindow for recency and avoid stale example topics.
```

호출 모델 `gpt-5.4-nano`, 최대 출력 토큰 `2_000`, 호출 횟수는 변경하지 않는다.

- [ ] **Step 5: 대상 테스트와 Web API 빌드를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts \
  src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.spec.ts
npm run build
```

Expected: 모두 PASS.

- [ ] **Step 6: Web API 저장소에 즉시 커밋한다**

```bash
git add \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts
git commit -m "feat: define provider-specific research query plan"
```

---

### Task 3: Nest 검색어 계획 검증과 관련 Trends 정규화

**Files:**

- Create:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-query-plan.ts`
- Create:
  `desktop/clipper_nestjs/test/shortform-director-research-query-plan.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-input.builder.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`

**Interfaces:**

- Produces:

```ts
export interface ResearchQueryPlanContext {
  input: Record<string, unknown>;
  knownTrendSignalIds: ReadonlySet<string>;
}

export interface ResearchQueryPlan {
  naverNewsQueries: readonly string[];
  youtubeQuery: string;
  datalabKeywords: readonly string[];
  selectedTrendSignals: readonly {
    trendSignalId: string;
    rationale: string;
  }[];
}

export function projectResearchQueryPlan(
  result: ShortformDirectorInferenceResult,
  knownTrendSignalIds: ReadonlySet<string>,
): ResearchQueryPlan;
```

- Consumes later:
  `buildNormalizationInput(calls, selectedTrendSignalIds, publishedAfter)`

- [ ] **Step 1: 검색어 계획 projector의 실패 테스트를 작성한다**

다음 성공 결과를 provider별 배열로 변환하는지 검증한다.

```js
assert.deepEqual(plan, {
  naverNewsQueries: ['르세라핌 최근 컴백 신곡 뮤직비디오'],
  youtubeQuery: '르세라핌 최신 안무 직캠 쇼츠',
  datalabKeywords: ['르세라핌'],
  selectedTrendSignals: [{
    trendSignalId: 'trend-2',
    rationale: '걸그룹 프로필과 직접 관련된 신호',
  }],
});
```

다음 입력은 throw해야 한다.

- YouTube 검색어 없음
- YouTube 검색어 2개
- 네이버 뉴스 검색어 없음
- 중복 query
- `site:youtube.com`이 포함된 YouTube 검색어
- 81자를 넘는 DataLab 키워드
- 입력에 없던 `trend-999` 선택
- 중복 Trends 선택

- [ ] **Step 2: Trends ID와 정규화 필터의 실패 테스트를 작성한다**

`buildQueryPlanInput()` 결과 중 다음 필드를 검증한다.

```js
assert.equal(context.input.focusKeyword, '르세라핌');
assert.deepEqual(context.input.researchWindow, {
  startDate: '2026-06-29',
  endDate: '2026-07-29',
});
assert.deepEqual(context.input.trendingSignals, [
  {
    trendSignalId: 'trend-1',
    title: '군대',
    approximateTraffic: '10K+',
    publishedAt: '2026-07-29T00:00:00Z',
    relatedHeadlines: ['전국 급상승 기사'],
  },
  {
    trendSignalId: 'trend-2',
    title: '르세라핌',
    approximateTraffic: '20K+',
    publishedAt: '2026-07-29T00:01:00Z',
    relatedHeadlines: ['르세라핌 최근 활동 기사'],
  },
]);
assert.deepEqual(
  [...context.knownTrendSignalIds],
  ['trend-1', 'trend-2'],
);
```

정규화 입력은 `selectedTrendSignalIds = new Set(['trend-2'])`일 때
`trend-2`만 포함하고 `trend-1`은 포함하지 않아야 한다. `publishedAfter`보다 오래된
네이버 뉴스는 source artifact에는 남지만 정규화 입력에서는 제외되어야 한다. 각
`sourceItems`에는 추적용 `sourceArtifactId`가 있어야 한다.

- [ ] **Step 3: Nest 빌드와 새 테스트가 실패하는지 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-query-plan.test.js
node --test test/shortform-director-reference-candidates.test.js
```

Expected: 새 interface와 필터가 없어 FAIL.

- [ ] **Step 4: `query-plan.v2` 경계 검증을 추가한다**

Nest inference projector의 `query-plan` case는 root exact keys를 다음으로 제한한다.

```ts
['queries', 'datalabKeywords', 'selectedTrendSignals']
```

항목 필드, 배열 상한, source enum을 Web API와 동일하게 검증한다. 보안 clone 이후의
값만 새 projector에 전달한다.

- [ ] **Step 5: 순수 검색어 계획 projector를 구현한다**

새 파일은 다음 책임만 갖는다.

```ts
export function projectResearchQueryPlan(result, knownTrendSignalIds) {
  // NFKC + 공백 정규화
  // source별 분리
  // 1~2 Naver, exactly 1 YouTube
  // DataLab 1~3, 80 code points 이하
  // selected trend ID가 known set의 부분집합인지 확인
  // 다른 공급자의 query를 fallback으로 사용하지 않음
}
```

잘못된 계약은 안전한 일반 `Error`로 종료해 discovery failure artifact에 stage와 함께
기록되게 한다. 추가 LLM 호출은 하지 않는다.

- [ ] **Step 6: input builder에 stable Trends ID와 선택 필터를 구현한다**

`buildQueryPlanInput`은 `ResearchCollectionWindow`를 받아
`researchWindow.startDate/endDate`를 입력에 포함하고 반환형을
`ResearchQueryPlanContext`로 변경한다. 한 실행의 RSS 순서에 따라 `trend-1`부터
`trend-20`까지 부여한다.

`buildNormalizationInput` signature는 다음으로 바꾼다.

```ts
buildNormalizationInput(
  calls: readonly CollectedResearchSourceCall[],
  selectedTrendSignalIds: ReadonlySet<string>,
  publishedAfter: string,
): ResearchNormalizationContext
```

Google Trends source item은 ID가 선택 set에 있을 때만 append한다. 네이버·DataLab·YouTube
항목은 기존 상한을 유지한다. 네이버 뉴스와 YouTube 항목은 유효한 게시 시각이
`publishedAfter` 이상인 것만 정규화 입력에 append한다. 게시 시각이 없거나 파싱할 수
없는 항목도 최신 근거로 가장하지 않고 제외한다. 각 source item에 해당
`sourceArtifactId`를 포함하고 기존 `artifactIdBySourceItemId`도 유지한다.

- [ ] **Step 7: 대상 테스트와 전체 Shortform Director 테스트를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-query-plan.test.js
node --test test/shortform-director-reference-candidates.test.js
node --test test/shortform-director*.test.js
```

Expected: 모두 PASS.

- [ ] **Step 8: Nest 저장소에 즉시 커밋한다**

```bash
git add \
  src/modules/shortform-director/application/shortform-director-research-query-plan.ts \
  src/modules/shortform-director/application/shortform-director-research-input.builder.ts \
  src/modules/shortform-director/application/shortform-director-inference-response.projector.ts \
  test/shortform-director-research-query-plan.test.js \
  test/shortform-director-reference-candidates.test.js
git commit -m "feat: validate relevant research query plans"
```

---

### Task 4: Nest 공급자별 라우팅과 실패 단계 구분

**Files:**

- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-cost-estimate.ts`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-research-cost-estimate.test.js`

**Interfaces:**

- Consumes `ResearchQueryPlan` from Task 3
- Changes:

```ts
export interface ResearchMarketQueries {
  naverNewsQueries: readonly string[];
  datalabKeywords: readonly string[];
}

collectMarketSources(
  queries: ResearchMarketQueries,
  window: ResearchCollectionWindow,
  credentials: ResearchMarketCollectionCredentials,
  bearerToken: string,
  record: RecordCollectedResearchSourceCall,
): Promise<CollectedResearchSourceCall[]>
```

- [ ] **Step 1: provider 라우팅 회귀 테스트를 작성한다**

다음 plan으로 collector와 orchestrator를 실행한다.

```js
{
  naverNewsQueries: [
    '르세라핌 최근 컴백 신곡',
    '르세라핌 인터뷰 공식 발표',
  ],
  youtubeQuery: '르세라핌 최신 안무 직캠 쇼츠',
  datalabKeywords: ['르세라핌', '르세라핌 신곡'],
  selectedTrendSignals: [],
}
```

요청을 다음처럼 단언한다.

```js
assert.deepEqual(
  naverNewsRequests.map(({ query }) => query.query),
  ['르세라핌 최근 컴백 신곡', '르세라핌 최근 컴백 신곡',
   '르세라핌 인터뷰 공식 발표', '르세라핌 인터뷰 공식 발표'],
);
assert.deepEqual(dataLabRequest.query.keywordGroups, [
  { groupName: '르세라핌', keywords: ['르세라핌'] },
  { groupName: '르세라핌 신곡', keywords: ['르세라핌 신곡'] },
]);
assert.deepEqual(
  youtubeSearchRequests.map(({ query }) => query.q),
  ['르세라핌 최신 안무 직캠 쇼츠', '르세라핌 최신 안무 직캠 쇼츠'],
);
```

focusKeyword가 `르세라핌`이어도 YouTube query가 단어 하나로 덮이지 않는 assertion을
포함한다.

- [ ] **Step 2: fetch와 persistence 실패 단계 테스트를 작성한다**

YouTube client가 throw한 경우 failure artifact stage가
`youtube-search-fetch`인지 검증한다. client 응답 후 `record`가 throw한 경우 stage가
`youtube-search-persistence`인지 검증한다.

- [ ] **Step 3: 현재 코드에서 대상 테스트가 실패하는지 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-candidates.test.js
node --test test/shortform-director-research-orchestrator.test.js
```

Expected: 현재 문자열 배열 공유와 focus 우선 선택 때문에 FAIL.

- [ ] **Step 4: market collector 인자를 분리한다**

뉴스 요청 loop는 `naverNewsQueries.slice(0, 2)`만 사용한다. DataLab request는
`datalabKeywords.slice(0, 3)`만 keyword group으로 만든다.

기존 `marketSources()` compatibility helper가 production에서 쓰이지 않으면 제거한다.
쓰이는 호출자가 있으면 새 `ResearchMarketQueries`를 받도록 함께 변경하며 문자열 배열
fallback은 두지 않는다.

- [ ] **Step 5: discovery orchestration을 새 계획으로 연결한다**

흐름을 다음처럼 교체한다.

```ts
const queryContext = this.inputs.buildQueryPlanInput(
  prepared.profile,
  trends,
  window,
  prepared.publicView.focusKeyword,
);
const published = await this.inferAndPublish(
  'query-plan',
  queryContext.input,
  bearerToken,
  auth.subjectId,
  runId,
  input.profileId,
  requiredResearchCredential(prepared.publicView, 'openai'),
);
const plan = projectResearchQueryPlan(
  published.result,
  queryContext.knownTrendSignalIds,
);

await this.sources.collectMarketSources(
  {
    naverNewsQueries: plan.naverNewsQueries,
    datalabKeywords: plan.datalabKeywords,
  },
  window,
  {
    naver: requiredResearchCredential(
      prepared.publicView,
      'naver',
    ),
  },
  bearerToken,
  recordSource,
);
await this.sources.collectYoutubeCandidateSources(
  plan.youtubeQuery,
  window,
  requiredResearchCredential(prepared.publicView, 'youtube'),
  bearerToken,
  recordSource,
);
const normalizationContext = this.inputs.buildNormalizationInput(
  collected,
  new Set(plan.selectedTrendSignals.map(({ trendSignalId }) =>
    trendSignalId)),
  window.publishedAfter,
);
```

candidate collector의 `primaryQuery`도 `plan.youtubeQuery`를 사용한다.
기존 `selectUniqueQueries`와 `selectPrimaryYoutubeQuery`는 삭제한다.
`researchWindow(this.clock())`는 query-plan 입력을 만들기 전에 한 번만 계산한다.

- [ ] **Step 6: source fetch와 artifact persistence 오류를 구분한다**

collector에 안전한 stage를 가진 오류를 추가한다.

```ts
export class ResearchSourceCollectionError extends Error {
  constructor(
    readonly stage:
      | `${ShortformDirectorResearchSource}-fetch`
      | `${ShortformDirectorResearchSource}-persistence`,
    options: { cause: unknown },
  ) {
    super('Shortform Director research source collection failed.', options);
  }
}
```

`fetchAndRecord()`는 client 실패와 record 실패를 각각 감싼다. discovery catch는 이
오류일 때 `error.stage`를 failure artifact stage로 사용한다. provider error 본문이나
credential은 message에 복사하지 않는다.

- [ ] **Step 7: 후보 부족 상태가 구체적인 수량을 보존하는지 검증한다**

0개와 2개 결과 case에서 reference-candidates artifact가 각각 다음 수량을 보존하고 run은
`partial`인지 검증한다.

```js
{
  availability: 'insufficient',
  rawVideoCount: 0,
  eligibleVideoCount: 0,
  recommendedVideoIds: [],
}
```

이 상태는 provider 오류로 바꾸지 않는다.

- [ ] **Step 8: 사전 점검 호출 상한을 실제 라우팅 계약과 맞춘다**

`research-cost-estimate` 테스트의 네이버 기대값을 뉴스 최대 4회와 DataLab 1회, 합계
5회로 바꾼다.

```js
assert.deepEqual(naver.operations, [
  { name: 'news search (date and relevance)', maxCalls: 4 },
  { name: 'DataLab keyword trend', maxCalls: 1 },
]);
assert.equal(naver.maxCalls, 5);
```

`research-cost-estimate.ts`의 같은 수치를 변경한다. OpenAI 최대 2회와 승인 비용 상한
`USD 0.05`는 유지한다.

- [ ] **Step 9: Nest 전체 검증을 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-candidates.test.js
node --test test/shortform-director-research-orchestrator.test.js
node --test test/shortform-director-research-cost-estimate.test.js
node --test test/shortform-director*.test.js
```

Expected: 모두 PASS.

- [ ] **Step 10: Nest 저장소에 즉시 커밋한다**

```bash
git add \
  src/modules/shortform-director/application/shortform-director-research-source.collector.ts \
  src/modules/shortform-director/application/shortform-director-research-discovery.service.ts \
  src/modules/shortform-director/domain/research-cost-estimate.ts \
  test/shortform-director-reference-candidates.test.js \
  test/shortform-director-research-orchestrator.test.js \
  test/shortform-director-research-cost-estimate.test.js
git commit -m "fix: route discovery queries by provider"
```

---

### Task 5: 비용 상한·조사 근거·부분 완료 UI

**Files:**

- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-preflight-card/research-preflight-card.component.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-preflight-card/research-preflight-card.component.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.html`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.html`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts`
- Modify:
  `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts`

**Interfaces:**

- Extends the `inference` presentation with:

```ts
queryPlan?: {
  naverNewsQueries: string[];
  youtubeQuery: string | null;
  datalabKeywords: string[];
  selectedTrendSignals: Array<{
    trendSignalId: string;
    title: string;
    rationale: string;
  }>;
};
inputSources: Array<{
  sourceItemId: string;
  source: string;
  title: string;
  sourceArtifactId: string;
}>;
usage?: {
  inputTokens?: number;
  outputTokens?: number;
  reasoningTokens?: number;
};
```

- [ ] **Step 1: 비용 표시 실패 테스트를 변경한다**

preflight component test는 다음을 검증한다.

```ts
expect(text).toContain('예상 최대 비용');
expect(text).toContain('USD 0.05');
expect(text).not.toContain('USD 0.00–0.05');
```

- [ ] **Step 2: query plan과 정규화 입력 presentation 테스트를 작성한다**

`projectShortformDirectorResearchArtifact()`에 실제 저장 형태의
`research-inference-call`을 전달한다.

query-plan case는:

- request `userPrompt.trendingSignals`에 `trendSignalId`와 title 포함
- output에 공급자별 queries, DataLab 키워드, 선택 Trends ID와 rationale 포함
- presentation에 네이버·YouTube·DataLab 구분과 선택 Trends title·이유 포함

source-normalization case는:

- request `userPrompt.sourceItems`에 `sourceItemId`, `source`, `title`,
  `sourceArtifactId` 포함
- presentation `inputSources`에 같은 네 필드 포함
- audit usage가 있으면 presentation에 입력·출력·추론 token 수 포함

prompt 원문 전체나 credential 관련 값은 presentation에 포함하지 않는다.

- [ ] **Step 3: 보고서와 부분 완료 실패 테스트를 작성한다**

보고서는 다음 문구와 실제 값이 보이는지 검증한다.

```text
전국 급상승 참고 자료
이번 조사에 사용한 급상승 항목
네이버 뉴스 검색어
DataLab 핵심 키워드
YouTube 검색어
AI 정리에 실제 사용한 근거
```

insufficient 후보 fixture는 다음 수량 문구를 검증한다.

```text
검색 결과 2개 · 조건 통과 1개 · 추천 0개
```

store test는 `partial` run 선택 시 `getReferenceCandidates(runId)`가 호출되고 snapshot이
화면 상태에 저장되는지 검증한다.

- [ ] **Step 4: 현재 UI 테스트가 실패하는지 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/components/research-preflight-card/research-preflight-card.component.spec.ts' \
  --include='src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts' \
  --include='src/features/shortform-director/components/research-evidence-report/research-evidence-report.component.spec.ts' \
  --include='src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts'
```

Expected: 기존 범위 비용, generic inference summary, partial candidate 미조회 때문에 FAIL.

- [ ] **Step 5: 비용은 maximum만 표시한다**

```ts
costLabel(): string {
  return `USD ${this.preflight.estimatedCostUsd.maximum.toFixed(2)}`;
}
```

template의 `예상 최대 비용` label은 유지한다.

- [ ] **Step 6: inference artifact를 사람이 읽는 구조로 투영한다**

`projectInference`는 `audit.request.userPrompt`를 한 번 안전하게 JSON parse한다.

- purpose가 `query-plan`이면 output query를 source별로 분류한다.
- 선택 Trends ID를 input의 `trendingSignals`와 join해 title과 rationale을 만든다.
- purpose가 `source-normalization`이면 `sourceItems`의 추적 필드만 투영한다.
- 파싱이 실패하면 기존 summary와 `inputSources: []`로 안전하게 폴백한다.
- userPrompt 문자열 자체는 반환하지 않는다.

- [ ] **Step 7: 보고서를 공급자·활용 단계별로 렌더링한다**

Google Trends summary title을 `Google Trends 전국 급상승 참고 자료`로 바꾼다.
query-plan summary는 공급자별 검색어, DataLab 키워드, 선택 Trends와 이유를 분리한다.
source-normalization summary는 실제 입력 source의 title·source·artifact ID를 보여준다.
AI inference summary는 공급자 audit에 존재하는 token 사용량을 보여주되, 서버가 계산한
확정 비용 필드가 없으면 실제 USD 비용을 만들어 표시하지 않는다.
기존 artifact 상세 패널과 `JSON 원문 보기` 동작은 유지한다.

- [ ] **Step 8: partial run에서도 후보 snapshot과 수량을 표시한다**

store의 `selectRun()`은 `partial`일 때 topics와 reference candidates를 모두 조회한다.
두 로드는 순차 실행하되 `loadReferenceCandidates` 내부 오류 처리가 topics 로드를
막지 않도록 현재처럼 오류를 state에 저장하고 throw하지 않는다.

insufficient alert는 다음 값을 사용한다.

```html
검색 결과 {{ candidates?.rawVideoCount }}개 ·
조건 통과 {{ candidates?.eligibleVideoCount }}개 ·
추천 {{ candidates?.recommendedVideoIds?.length ?? 0 }}개
```

- [ ] **Step 9: Angular 대상 테스트와 전체 빌드를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/**/*.spec.ts'
npm run build:electron
```

Expected: 모두 PASS.

- [ ] **Step 10: Angular 저장소에 즉시 커밋한다**

```bash
git add src/features/shortform-director
git commit -m "feat: explain research evidence and cost cap"
```

---

### Task 6: 교차 저장소 검증과 실제 앱 수용 테스트

**Files:**

- Create:
  `.codex/records/sessions/2026/07/29.md`
- Modify:
  `.codex/handoff/NEXT.md`

**Interfaces:**

- Consumes Task 1~5의 커밋
- Produces 실제 실행 ID, artifact ID, 공급자 호출 수, 검증 결과가 기록된 세션 문서

- [ ] **Step 1: 각 저장소가 예상 branch이고 task 변경 외 dirty file이 없는지 확인한다**

Run:

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs status --short --branch
git -C /Users/jina/project/adlight/web/clipper_web_api status --short --branch
git -C /Users/jina/project/adlight/desktop/clipper_angular status --short --branch
git -C /Users/jina/project/adlight/desktop/clipper_electron status --short --branch
git -C /Users/jina/project/adlight/.codex status --short --branch
```

Expected: 기존 `feat/shortform-director-foundation` 또는 각 저장소의 현재 작업 branch를
유지하며 예상 밖 변경이 없음. 예상 밖 변경은 reset/revert하지 않고 사용자에게 보고.

- [ ] **Step 2: 세 코드 저장소의 전체 검증을 다시 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand
npm run build

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director*.test.js

cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/**/*.spec.ts'
npm run build:electron
```

Expected: 모두 exit 0.

- [ ] **Step 3: 최신 Electron 앱을 빌드한다**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
npm run build:app:mac:arm64:local-api
```

Expected: `dist-app/mac-arm64/Clipper Studio.app` 생성 성공.

- [ ] **Step 4: 실제 프로필의 discovery preflight를 확인한다**

앱에서 엔터테인먼트·걸그룹 활성 프로필을 열고 추가 범위 없이 사전 점검한다.

확인값:

- `예상 최대 비용 USD 0.05`
- Google Trends 1회
- 네이버 최대 5회
- YouTube 최대 3회
- OpenAI 최대 2회
- Gemini 없음

- [ ] **Step 5: 추가 범위 없는 실제 discovery를 한 번 승인·실행한다**

사용자가 UI의 `이대로 조사 시작`을 눌러 비용 승인을 확정한다. 완료 후 다음을 확인한다.

- run이 `failed`가 아닌 `awaiting_reference_selection` 또는 설명 가능한 `partial`
- Google Trends 전체 원본이 `전국 급상승 참고 자료`에 표시됨
- 무관한 Trends 항목이 `이번 조사에 사용한 급상승 항목`과 AI 정리 입력에 없음
- 네이버·DataLab·YouTube의 실제 검색어가 서로 구분됨
- YouTube source artifact에 `nextPageToken`, `prevPageToken`이 없음

- [ ] **Step 6: `르세라핌` 추가 범위로 실제 discovery를 한 번 승인·실행한다**

확인값:

- generic 502가 발생하지 않음
- YouTube 검색어가 `르세라핌` 한 단어가 아니라 query-plan이 만든 검색어임
- YouTube 검색 결과와 상세 결과가 로컬 JSON artifact에 저장됨
- 결과가 3개 이상이면 추천 3개와 교체 가능한 최대 6개 후보가 표시됨
- 후보가 3개 미만이면 검색·조건 통과·추천 수량이 표시됨
- Gemini 정밀 분석 호출은 아직 발생하지 않음

- [ ] **Step 7: 실제 JSON과 UI의 일치 여부를 검증한다**

`/Users/jina/Library/Application Support/Clipper Studio/shortform-director`에서 두 최신
run manifest와 연결 artifact를 읽는다. API key나 authorization 값을 출력하지 않고
다음만 세션 문서에 기록한다.

- run ID와 최종 status
- query-plan inference artifact ID
- source artifact ID 목록
- 공급자별 실제 안전한 검색어
- selected Trends ID·title
- normalization sourceItem ID·source artifact 연결
- raw/eligible/recommended video count
- token usage가 공급자 audit에 존재하는지 여부

- [ ] **Step 8: 세션 기록과 NEXT 기준점을 갱신한다**

`.codex/records/sessions/2026/07/29.md`에 실제 실행 증거와 남은 다음 단계를 기록한다.
`.codex/handoff/NEXT.md`에는 각 저장소 branch·HEAD, clean 여부, 다음 작업인 레퍼런스
정밀 분석 승인·실행 또는 실제 후보 품질 보정을 기록한다.

- [ ] **Step 9: 문서 저장소에 즉시 커밋한다**

```bash
git add \
  records/sessions/2026/07/29.md \
  handoff/NEXT.md
git commit -m "docs: record corrected discovery acceptance"
```

- [ ] **Step 10: 최종 상태를 보고한다**

보고에는 다음을 포함한다.

- 각 저장소 커밋 hash
- 실행한 테스트와 실제 앱 run ID
- 비용 표시는 무엇이 바뀌었는지
- 두 502의 원인과 해결 내용
- 실제로 수집·활용된 Trends, 네이버, DataLab, YouTube 근거 요약
- 다음 사용자 단계인 레퍼런스 영상 3개 선택과 정밀 분석 비용 승인
