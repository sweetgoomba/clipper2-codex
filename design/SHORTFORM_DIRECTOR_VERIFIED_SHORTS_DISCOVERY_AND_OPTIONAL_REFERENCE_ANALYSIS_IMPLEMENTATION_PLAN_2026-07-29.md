# AI 숏폼 디렉터 실제 Shorts 발견 및 선택적 정밀 분석 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 최근 30일 YouTube 검색 결과를 조회수순 40개·관련도순 40개씩 수집해 전부 실제 Shorts인지 검증하고, 확인된 모든 Shorts를 보여준 뒤 사용자가 1~5개를 정밀 분석하거나 명시적으로 분석 없이 계속할 수 있게 만든다.

**Architecture:** Web API는 인증이 필요한 YouTube Data API 호출만 담당하고, 데스크톱 Nest는 두 검색 lane의 결과를 합쳐 공개 Shorts URL을 제한 동시성으로 검증한 뒤 로컬 JSON artifact로 보존한다. 정밀 분석 선택과 시장 근거 전용 생략은 서로 다른 승인 계약으로 유지하며, Angular는 자동 선택 없이 전체 후보와 두 경로를 명확히 보여준다.

**Tech Stack:** NestJS 10 + TypeScript + `node:test`(데스크톱), NestJS 11 + TypeScript + Jest(Web API), Angular 19 standalone/zoneless + NgRx Signals + Angular Material + Karma, 로컬 JSON artifact 저장

## Global Constraints

- YouTube 검색어에 `shorts`, `쇼츠`, `챌린지`를 강제로 추가하지 않는다.
- 조회수순과 관련도순은 같은 검색어·같은 최근 30일 `publishedAfter`·`videoDuration=short`·`regionCode=KR`·`relevanceLanguage=ko`를 사용한다.
- 각 검색 lane은 `maxResults=40`이고, 중복 제거된 결과를 조기 중단 없이 전부 Shorts URL로 검증한다.
- 최종 Shorts 판정에는 `3분`, `4분` 등 영상 길이 업무 규칙을 사용하지 않는다.
- Shorts 검증은 GET, redirect 수동 처리, 동시성 8, timeout 10초, 네트워크 오류·5xx 최대 1회 재시도를 사용한다.
- 응답 HTML, cookie, 전체 header는 저장하지 않고 allowlist로 파싱한 JSON만 저장한다.
- 확인된 Shorts는 최대 6개나 채널당 개수로 자르지 않고 전부 저장하고 보여준다.
- 새 조사 결과의 정밀 분석 선택 초기값은 빈 배열이다.
- 일반 정밀 분석은 1~5개만 허용하며 선택만으로 유료 호출하지 않는다.
- 0개는 대기 상태이고, `정밀 분석 없이 계속`은 별도 preflight와 사용자 승인이 있어야 한다.
- skip 경로에서도 시장 근거는 필수이고 audience/reference 신호만 비울 수 있다.
- AI Director 크레딧 차감은 추가하지 않는다.
- 더미 provider나 fixture 결과로 실제 E2E 완료를 주장하지 않는다.
- Remotion을 도입하거나 대체 렌더러로 언급하지 않는다.
- 각 태스크는 실패 테스트 → 최소 구현 → 통과 테스트 → 즉시 커밋 순서로 진행한다.

## 파일 구조

### Web API

- `src/modules/shortform-director-research/application/youtube-data-provider.service.ts`: YouTube 검색 요청 40개 허용 및 기존 인증 호출 유지
- `src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`: 실제 URL 파라미터와 상한 검증
- `src/modules/shortform-director-research/presentation/dto/fetch-shortform-director-source.dto.ts`: `maxResults<=50`, `videoDuration=short` 계약 유지
- `src/modules/shortform-director-research/presentation/dto/fetch-shortform-director-source.dto.spec.ts`: 40개 검색 DTO 회귀 검증
- `src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`: 시장-only 입력일 때 빈 reference 배열을 설명하는 프롬프트
- `src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`: topic synthesis 입력의 조건부 reference 배열 계약
- `src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`: 분석 있음/없음 두 schema 경로 검증
- `docs/api/openapi.yaml`: YouTube 검색 계약 설명과 topic synthesis 빈 배열 조건 반영

### Desktop Nest

- `src/modules/shortform-director/domain/youtube-shorts-validation.ts`: 검증 outcome과 artifact 공개 타입
- `src/modules/shortform-director/application/shortform-director-youtube-shorts.validator.ts`: GET 판정·동시성·timeout·재시도
- `src/modules/shortform-director/application/shortform-director-research-source.collector.ts`: 40×2 검색과 최대 80개 중복 제거
- `src/modules/shortform-director/application/shortform-director-reference-candidate.collector.ts`: Shorts 검증 통과 ID만 상세 후보로 투영
- `src/modules/shortform-director/application/shortform-director-reference-candidate.ranker.ts`: 전체 확인 Shorts 정렬, 표시/채널 제한 제거
- `src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`: 검증 artifact 발행, 상세 조회 batch, 대기 상태 결정
- `src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`: 검증/skip artifact 읽기
- `src/modules/shortform-director/infrastructure/shortform-director-artifact.registry.ts`: 검증/skip artifact 등록
- `src/modules/shortform-director/infrastructure/shortform-director-public-artifact.validator.ts`: allowlist 검증
- `src/modules/shortform-director/presentation/dto/update-shortform-director-reference-selection.dto.ts`: 선택 1~5 검증
- `src/modules/shortform-director/application/shortform-director-reference-selection.service.ts`: 후보 포함 여부·중복·1~5 검증
- `src/modules/shortform-director/application/shortform-director-reference-analysis-preflight.service.ts`: 선택 N 기반 호출·비용 산출
- `src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`: 선택 N 실행
- `src/modules/shortform-director/application/shortform-director-reference-analysis.runner.ts`: 선택 N 완료·계속 조건
- `src/modules/shortform-director/application/shortform-director-run-recovery.service.ts`: 선택 revision의 N 기준 복구
- `src/modules/shortform-director/application/shortform-director-reference-analysis-skip.service.ts`: 시장-only preflight·승인·synthesis
- `src/modules/shortform-director/application/shortform-director-research-topic.builder.ts`: 선택적 reference 입력
- `src/modules/shortform-director/application/shortform-director-grounded-candidate-context.builder.ts`: 시장-only 후보 생성 문맥
- `src/modules/shortform-director/presentation/dto/start-shortform-director-reference-analysis-skip.dto.ts`: skip 승인 DTO
- `src/modules/shortform-director/presentation/shortform-director-research.controller.ts`: skip preflight/실행 route
- `src/modules/shortform-director/shortform-director.module.ts`: 새 validator·skip service DI 조립

### Angular

- `src/features/shortform-director/models/shortform-director-research.ts`: Shorts 검증·선택 0~5·skip preflight 공개 모델
- `src/features/shortform-director/services/shortform-director-research.gateway.ts`: skip API 계약
- `src/features/shortform-director/services/shortform-director-research.service.ts`: skip preflight/실행 HTTP
- `src/features/shortform-director/state/shortform-director-research.store.ts`: 자동 선택 제거, 0~5 선택, 분석/skip 상태
- `src/features/shortform-director/components/research-reference-candidate-list/*`: 전체 Shorts 목록과 N/5 선택
- `src/features/shortform-director/components/research-reference-analysis-preflight/*`: 선택 N 동적 비용 표시
- `src/features/shortform-director/components/research-artifact-summary/*`: Shorts 검증 사람이 읽는 요약
- `src/features/shortform-director/pages/ideas-page/*`: 두 진행 버튼과 상태 전환

---

### Task 1: Web API에서 YouTube 검색 40개를 그대로 전달

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-research/presentation/dto/fetch-shortform-director-source.dto.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-research/presentation/shortform-director-research.openapi.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**
- Consumes: `YoutubeSearchResearchQueryDto.maxResults: number` with DTO range `1..50`
- Produces: YouTube `search.list` query whose `maxResults` is `Math.min(request.maxResults, 50)`

- [ ] **Step 1: 40개 요청이 6개로 잘리지 않는 실패 테스트 작성**

```ts
it('forwards forty recent short-video results per search lane', async () => {
  await provider.fetch({
    source: 'youtube-search',
    query: {
      q: '르세라핌',
      order: 'viewCount',
      publishedAfter: '2026-06-29T00:00:00.000Z',
      regionCode: 'KR',
      relevanceLanguage: 'ko',
      videoDuration: 'short',
      maxResults: 40,
    },
  }, credential);
  expect(requestedUrl.searchParams.get('maxResults')).toBe('40');
});
```

- [ ] **Step 2: Web API 단위 테스트가 기존 6개 상한 때문에 실패하는지 확인**

Run: `cd web/clipper_web_api && npm test -- --runInBand src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts`

Expected: FAIL — 요청 URL의 `maxResults`가 `6`

- [ ] **Step 3: provider 내부 검색 상한을 DTO와 같은 50으로 올리고 40을 그대로 전달**

```ts
const MAX_RESEARCH_SEARCH_RESULTS = 50;
params.set(
  'maxResults',
  String(Math.min(query.maxResults, MAX_RESEARCH_SEARCH_RESULTS)),
);
```

- [ ] **Step 4: DTO/OpenAPI 테스트에 40, 최근 30일, `videoDuration=short` 계약 고정**

```ts
expect(parsed.query).toMatchObject({
  maxResults: 40,
  videoDuration: 'short',
});
```

- [ ] **Step 5: 관련 Web API 테스트와 빌드 통과**

Run: `cd web/clipper_web_api && npm test -- --runInBand src/modules/shortform-director-research/application/youtube-data-provider.service.spec.ts src/modules/shortform-director-research/presentation/dto/fetch-shortform-director-source.dto.spec.ts src/modules/shortform-director-research/presentation/shortform-director-research.openapi.spec.ts && npm run build`

Expected: PASS

- [ ] **Step 6: Web API 커밋**

```bash
git -C web/clipper_web_api add src/modules/shortform-director-research docs/api/openapi.yaml
git -C web/clipper_web_api commit -m "feat: expand shortform YouTube discovery"
```

### Task 2: 공개 Shorts URL 판별기와 안전한 JSON artifact

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/domain/youtube-shorts-validation.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-youtube-shorts.validator.ts`
- Create: `desktop/clipper_nestjs/test/shortform-director-youtube-shorts-validation.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-artifact.registry.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-public-artifact.validator.ts`

**Interfaces:**
- Produces:

```ts
export type YoutubeShortsValidationOutcome =
  | 'shorts'
  | 'not-shorts'
  | 'unverified';

export interface YoutubeShortsValidationRequest {
  videoId: string;
  searchLanes: ReferenceCandidateSearchLane[];
  sourceArtifactIds: string[];
}

export interface YoutubeShortsValidationArtifactV1 {
  schemaVersion: 'shortform-director-youtube-shorts-validation.v1';
  runId: string;
  query: string;
  checkedAt: string;
  results: YoutubeShortsValidationResult[];
}

validateAll(
  input: readonly YoutubeShortsValidationRequest[],
  context: { runId: string; query: string; checkedAt: string },
): Promise<YoutubeShortsValidationArtifactV1>;
```

- [ ] **Step 1: 200, watch redirect, 예상 밖 응답, timeout, 재시도를 재현하는 실패 테스트 작성**

```js
assert.equal(resultsById.short.outcome, 'shorts');
assert.equal(resultsById.regular.outcome, 'not-shorts');
assert.equal(resultsById.unknown.outcome, 'unverified');
assert.equal(resultsById.retry.attemptCount, 2);
assert.equal(maxObservedConcurrency, 8);
```

- [ ] **Step 2: 빌드 후 신규 테스트가 모듈 부재로 실패하는지 확인**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-youtube-shorts-validation.test.js`

Expected: FAIL — validator module not found

- [ ] **Step 3: 주입 가능한 HTTP fetch 경계와 판정 함수 구현**

```ts
export const SHORTS_VALIDATION_FETCH = Symbol(
  'SHORTS_VALIDATION_FETCH',
);

function classifyResponse(
  videoId: string,
  status: number,
  location: string | null,
): YoutubeShortsValidationOutcome {
  if (status === 200 && location === null) return 'shorts';
  if (isRedirect(status) && isSameVideoWatchLocation(videoId, location)) {
    return 'not-shorts';
  }
  return 'unverified';
}
```

`fetch` 옵션은 `{ method: 'GET', redirect: 'manual', signal }`로 고정하고 응답 body를 읽지 않는다.

- [ ] **Step 4: 작업 큐 8개, timeout 10초, 네트워크·5xx 1회 재시도 구현**

```ts
const CONCURRENCY = 8;
const TIMEOUT_MS = 10_000;
const MAX_ATTEMPTS = 2;
```

4xx, 예상하지 않은 redirect, 200 외 성공 코드는 재시도하지 않고 `unverified`로 기록한다.

- [ ] **Step 5: artifact allowlist 테스트 작성 및 구현**

artifact에 `videoId`, `searchLanes`, `sourceArtifactIds`, `requestedUrl`, `attemptCount`, `status`, `redirectLocation`, `outcome`만 허용하며 `body`, `html`, `cookie`, `headers`가 있으면 validator가 거부한다.

- [ ] **Step 6: 빌드와 신규 테스트 통과**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-youtube-shorts-validation.test.js test/shortform-director-artifact-security.test.js`

Expected: PASS

- [ ] **Step 7: Desktop Nest 커밋**

```bash
git -C desktop/clipper_nestjs add src/modules/shortform-director test/shortform-director-youtube-shorts-validation.test.js test/shortform-director-artifact-security.test.js
git -C desktop/clipper_nestjs commit -m "feat: verify public YouTube Shorts"
```

### Task 3: 40×2 검색 결과 전부 검증하고 확인된 Shorts 전부 상세 조회

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-cost-estimate.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-cost-estimate.test.js`

**Interfaces:**
- Consumes: Task 2 `validateAll(...)`
- Produces:

```ts
interface CollectReferenceCandidatesInput {
  primaryQuery: string;
  window: ResearchCollectionWindow;
  generatedAt: string;
  calls: readonly CollectedResearchSourceCall[];
  shortsValidation: YoutubeShortsValidationArtifactV1;
}
```

- [ ] **Step 1: 두 lane이 같은 30일 범위와 40개를 요청하는 실패 테스트 작성**

```js
assert.deepEqual(searchCalls.map(({ query }) => ({
  order: query.order,
  publishedAfter: query.publishedAfter,
  videoDuration: query.videoDuration,
  maxResults: query.maxResults,
})), [
  { order: 'viewCount', publishedAfter, videoDuration: 'short', maxResults: 40 },
  { order: 'relevance', publishedAfter, videoDuration: 'short', maxResults: 40 },
]);
```

- [ ] **Step 2: 최대 80개 중복 제거 결과를 전부 validator에 전달하는 실패 테스트 작성**

40개+40개 응답에 중복 10개를 넣고 `validateAll` 입력 길이가 70이며 각 ID가 정확히 한 번인지 검증한다.

- [ ] **Step 3: source collector의 검색 상한과 상세 조회 batching 구현**

```ts
const YOUTUBE_RESULTS_PER_LANE = 40;
const YOUTUBE_DETAILS_BATCH_SIZE = 50;

for (const batch of chunk(verifiedShortVideoIds, YOUTUBE_DETAILS_BATCH_SIZE)) {
  await sourceFetch.fetch({ source: 'youtube-videos', query: { videoIds: batch }});
}
```

상세 조회는 확인된 Shorts만 대상으로 하며 최대 80개이면 50+30 두 번이다.

- [ ] **Step 4: candidate collector의 길이 최종 컷 제거**

`MAX_RAW_VIDEO_IDS=12`와 `MAX_SHORT_VIDEO_DURATION_SECONDS=240`을 제거한다. `publishedAt` 최근 30일 재검사는 유지하고 `shortsValidation.results`에서 `outcome==='shorts'`인 ID만 후보로 받는다.

- [ ] **Step 5: 검증 artifact 발행과 lineage 연결 구현**

각 후보 `sourceArtifactIds`에 검색 call, 상세 call, Shorts validation artifact ID를 포함한다. `unverified`와 `not-shorts`는 상세 후보에서 제외하되 검증 artifact에는 남긴다.

- [ ] **Step 6: discovery preflight 최대 호출 수 수정**

YouTube 최대 호출을 search 2회 + details 최대 2회로 표시하고 URL 검증은 과금 없는 공개 HTTP 작업으로 별도 표시한다.

- [ ] **Step 7: 관련 테스트와 빌드 통과**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-reference-candidates.test.js test/shortform-director-research-orchestrator.test.js test/shortform-director-research-cost-estimate.test.js`

Expected: PASS

- [ ] **Step 8: Desktop Nest 커밋**

```bash
git -C desktop/clipper_nestjs add src/modules/shortform-director test/shortform-director-reference-candidates.test.js test/shortform-director-research-orchestrator.test.js test/shortform-director-research-cost-estimate.test.js
git -C desktop/clipper_nestjs commit -m "feat: collect all verified Shorts references"
```

### Task 4: 전체 Shorts 후보 저장과 자동 선택 제거

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.ranker.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.models.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

**Interfaces:**
- Produces: `ReferenceCandidateSetV1.candidates` with every verified and valid observation, sorted by `rankScore`
- Compatibility: `recommendedVideoIds` remains readable but is advisory only; new UI never initializes selection from it

- [ ] **Step 1: 17개 확인 Shorts가 17개 모두 남고 같은 채널 4개도 보존되는 실패 테스트 작성**

```js
assert.equal(ranked.candidates.length, 17);
assert.equal(
  ranked.candidates.filter(({ channelId }) => channelId === 'same').length,
  4,
);
assert.equal(ranked.availability, 'ready');
```

- [ ] **Step 2: 1개 후보는 ready, 0개만 insufficient인 실패 테스트 작성**

```js
assert.equal(rank(oneCandidate).availability, 'ready');
assert.equal(rank(noCandidates).availability, 'insufficient');
```

- [ ] **Step 3: ranker의 표시·채널 제한 제거**

점수 산정과 정렬은 유지한다. `MAX_CANDIDATES`, `MAX_PER_CHANNEL`을 제거하고 `candidates=ranked`로 반환한다. `recommendedVideoIds`는 호환을 위해 상위 다양화 3개를 계산할 수 있지만 선택 상태로 사용하지 않는다.

- [ ] **Step 4: parser 허용 후보 수를 80으로 올리고 fewer-than-3 partial 종료 제거**

`candidates.length<=80`을 허용하고, 확인 Shorts가 1개 이상이면 run을 `awaiting_reference_selection`으로 둔다. 0개여도 502가 아니라 빈 후보와 skip 가능한 대기 상태를 반환한다.

- [ ] **Step 5: 관련 테스트와 빌드 통과**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-reference-candidates.test.js test/shortform-director-research-orchestrator.test.js`

Expected: PASS

- [ ] **Step 6: Desktop Nest 커밋**

```bash
git -C desktop/clipper_nestjs add src/modules/shortform-director test/shortform-director-reference-candidates.test.js test/shortform-director-research-orchestrator.test.js
git -C desktop/clipper_nestjs commit -m "feat: retain all verified Shorts candidates"
```

### Task 5: 정밀 분석 선택을 1~5개로 변경

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/update-shortform-director-reference-selection.dto.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-selection.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.models.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.runner.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-run-recovery.service.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-selection.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-cost.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-orchestrator.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

**Interfaces:**
- Selection: `selectedVideoIds.length` must be `1..5`
- Completion: every ID in the current selection revision has one passed validated analysis
- Cost: comments/STT/Gemini counts derive from selection length N

- [ ] **Step 1: DTO와 service 경계 실패 테스트 작성**

1개와 5개는 통과하고 0개, 6개, 중복 ID, snapshot 외 ID는 거부한다. 기존 3개 revision은 계속 읽을 수 있어야 한다.

- [ ] **Step 2: 선택 DTO와 application validation을 1~5로 변경**

```ts
@ArrayMinSize(1)
@ArrayMaxSize(5)
selectedVideoIds!: string[];
```

서비스에도 프레임워크 독립 검증을 남겨 내부 호출이 DTO를 우회해도 같은 규칙을 적용한다.

- [ ] **Step 3: preflight N 동적 호출 수 실패 테스트와 구현**

N=1과 N=5에 대해 댓글 최대 호출 N, 로컬 STT N, Gemini 기본 N/최대 2N, OpenAI pattern 1/최대2, topic 1/최대2를 검증한다.

- [ ] **Step 4: runner·orchestrator의 `length===3`을 selection revision N 비교로 교체**

```ts
const selectedIds = selection.selectedVideoIds;
const passedIds = new Set(validatedAnalyses.map(({ videoId }) => videoId));
const complete = selectedIds.every((videoId) => passedIds.has(videoId));
```

- [ ] **Step 5: comments 수집의 `.slice(0, 3)`을 최대 5개 선택 전체로 교체**

검색 후보 전체가 아니라 현재 selection revision의 ID에 대해서만 영상당 댓글 1회 호출한다.

- [ ] **Step 6: 복구 테스트를 N=1, N=5, revision 불일치로 확장**

현재 revision의 모든 N개가 성공해야 재개하고 과거 revision artifact가 섞이면 재개하지 않는다.

- [ ] **Step 7: 관련 테스트와 빌드 통과**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-reference-selection.test.js test/shortform-director-reference-analysis-cost.test.js test/shortform-director-reference-analysis-orchestrator.test.js test/shortform-director-research-orchestrator.test.js`

Expected: PASS

- [ ] **Step 8: Desktop Nest 커밋**

```bash
git -C desktop/clipper_nestjs add src/modules/shortform-director test/shortform-director-reference-selection.test.js test/shortform-director-reference-analysis-cost.test.js test/shortform-director-reference-analysis-orchestrator.test.js test/shortform-director-research-orchestrator.test.js
git -C desktop/clipper_nestjs commit -m "feat: support one to five reference analyses"
```

### Task 6: 명시적 시장-only skip와 빈 reference 조건부 계약

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis-skip.service.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-reference-analysis-skip.dto.ts`
- Create: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-skip.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-topic.builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-grounded-candidate-context.builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-artifact.registry.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/shortform-director-public-artifact.validator.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**
- New local endpoints:

```text
GET  /v1/projects/shortform-director/research/runs/:runId/reference-analysis/skip-preflight
POST /v1/projects/shortform-director/research/runs/:runId/reference-analysis/skip
```

- Approval contract:

```ts
const SHORTFORM_DIRECTOR_REFERENCE_ANALYSIS_SKIP_APPROVAL_VERSION =
  'reference-analysis-skip-cost-2026-07-29.v1';

interface StartReferenceAnalysisSkipInput {
  candidateSnapshotId: string;
  approvalVersion: typeof SHORTFORM_DIRECTOR_REFERENCE_ANALYSIS_SKIP_APPROVAL_VERSION;
  approvalId: string; // /^reference-analysis-skip-approval-[a-f0-9]{64}$/
  confirmed: true;
}
```

- Skip artifact: `shortform-director-reference-analysis-skip.v1`

- [ ] **Step 1: 0개 선택이 자동 skip되지 않는 실패 테스트 작성**

빈 선택을 저장하거나 일반 분석 endpoint로 보내면 400이며 run은 `awaiting_reference_selection`에 남고 provider 호출이 0회인지 검증한다.

- [ ] **Step 2: skip preflight가 OpenAI topic synthesis만 계산하는 실패 테스트 작성**

YouTube comments, STT, Gemini, reference-pattern 호출은 0이고 topic synthesis 기본 1회·최대 재시도 포함 2회만 표시한다.

- [ ] **Step 3: skip 승인 DTO와 service 구현**

현재 run 소유권, `awaiting_reference_selection`, 최신 candidate snapshot, preflight approval ID/version/confirmed를 검증한 뒤 skip artifact를 먼저 저장하고 시장 근거 topic synthesis를 실행한다.

- [ ] **Step 4: Web inference topic schema의 조건부 빈 배열 테스트 작성**

```ts
expect(parseTopicSynthesis(marketOnlyResponse, {
  hasReferenceAnalysis: false,
})).toMatchObject({
  audienceSignalIds: [],
  referencePatternIds: [],
});
expect(() => parseTopicSynthesis(missingReferencesResponse, {
  hasReferenceAnalysis: true,
})).toThrow();
```

시장-only에서도 `evidenceIds`는 최소 1개를 요구한다.

- [ ] **Step 5: Desktop topic builder와 grounded candidate context를 조건부로 변경**

reference analysis가 없으면 `audienceSignals=[]`, `referencePatterns=[]`를 실제 요청 body에 넣고 topic의 두 ID 배열이 빈 것을 허용한다. 분석 artifact가 존재하면 기존 최소 1개와 ID 포함 검증을 그대로 유지한다.

- [ ] **Step 6: skip route와 artifact allowlist 등록**

skip artifact에는 `schemaVersion`, `runId`, `candidateSnapshotId`, `decision:'user-skipped'`, `decidedAt`만 저장한다.

- [ ] **Step 7: Desktop/Web 관련 테스트와 빌드 통과**

Run: `cd web/clipper_web_api && npm test -- --runInBand src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts && npm run build`

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-reference-analysis-skip.test.js test/shortform-director-research-orchestrator.test.js test/shortform-director-candidate-grounding.test.js`

Expected: PASS

- [ ] **Step 8: 저장소별 커밋**

```bash
git -C web/clipper_web_api add src/modules/shortform-director-inference docs/api/openapi.yaml
git -C web/clipper_web_api commit -m "feat: support market-only topic synthesis"
git -C desktop/clipper_nestjs add src/modules/shortform-director test/shortform-director-reference-analysis-skip.test.js test/shortform-director-research-orchestrator.test.js test/shortform-director-candidate-grounding.test.js
git -C desktop/clipper_nestjs commit -m "feat: continue research without reference analysis"
```

### Task 7: Angular 전체 후보·0~5 선택·명시적 skip UI

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts`

**Interfaces:**
- `selectedReferenceVideoIds: Signal<readonly string[]>`, 초기값 `[]`
- `toggleReferenceVideo(videoId)`는 최대 5개만 허용
- `prepareReferenceAnalysis()`는 1~5개일 때만 selection 저장과 preflight 호출
- `prepareReferenceAnalysisSkip()`은 선택 수와 무관하게 명시적 skip preflight 호출

- [ ] **Step 1: store가 추천 3개를 자동 선택하지 않는 실패 테스트 작성**

```ts
await store.loadReferenceCandidates();
expect(store.selectedReferenceVideoIds()).toEqual([]);
```

- [ ] **Step 2: 0~5 선택 상태와 6번째 선택 거부 테스트 작성**

선택은 `0/5`에서 시작하고 5개까지 추가·해제되며 6번째는 상태를 바꾸지 않고 사용자 메시지를 제공해야 한다.

- [ ] **Step 3: service/gateway skip API 실패 테스트와 구현**

skip preflight GET과 승인 POST가 Task 6의 exact route/body를 사용하고 raw 응답을 그대로 모델로 받는지 검증한다.

- [ ] **Step 4: 전체 후보 렌더와 선택 UI 구현**

`candidates`를 slice하지 않고 rank 순서 전체를 렌더한다. 체크박스, `N/5`, 게시 시각, 조회수, 참여율, lane, rank 이유, `근거와 과정 보기`를 표시한다.

- [ ] **Step 5: 두 진행 버튼 상태 구현**

- `선택한 N개 정밀 분석`: N=1~5이고 저장 중이 아닐 때 활성화
- `정밀 분석 없이 계속`: 후보 0개여도 활성화
- 0개 상태에서는 분석 버튼만 비활성화하고 skip을 자동 실행하지 않음
- skip preflight 후 OpenAI 모델·credential·최대 호출·예상 비용을 승인 카드에 표시

- [ ] **Step 6: 관련 Angular 테스트와 빌드 통과**

Run: `cd desktop/clipper_angular && npm test -- --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/services/shortform-director-research.service.spec.ts' --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts' --include='src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts' --include='src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts'`

Run: `cd desktop/clipper_angular && npm run build`

Expected: PASS

- [ ] **Step 7: Angular 커밋**

```bash
git -C desktop/clipper_angular add src/features/shortform-director
git -C desktop/clipper_angular commit -m "feat: choose optional Shorts references"
```

### Task 8: Shorts 검증 근거를 사람이 읽는 화면으로 표시

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-panel/research-artifact-panel.component.html`

**Interfaces:**
- Produces:

```ts
interface YoutubeShortsValidationPresentation {
  type: 'youtube-shorts-validation';
  searchedCount: number;
  uniqueCheckedCount: number;
  shortsCount: number;
  notShortsCount: number;
  unverifiedCount: number;
  rows: Array<{
    videoId: string;
    lanes: string[];
    outcome: 'shorts' | 'not-shorts' | 'unverified';
    status: number | null;
    attemptCount: number;
  }>;
}
```

- [ ] **Step 1: raw JSON보다 요약이 먼저 나오는 실패 테스트 작성**

검증 artifact를 projector에 넣었을 때 수치 요약과 영상별 판정 row가 생성되고 `body`, `cookie`, `headers` 필드는 노출되지 않는지 검증한다.

- [ ] **Step 2: artifact presentation projector 구현**

schemaVersion으로 Shorts validation artifact를 식별하고 `results`에서 수치를 결정적으로 계산한다.

- [ ] **Step 3: 요약 표와 접힌 raw JSON UI 구현**

기본 화면에는 검색 수, 중복 제거 후 검사 수, Shorts/일반/미확인 수와 영상별 상태를 표시한다. 전체 JSON은 기존 disclosure를 사용해 기본 접힘 상태로 둔다.

- [ ] **Step 4: 관련 테스트와 빌드 통과**

Run: `cd desktop/clipper_angular && npm test -- --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts' --include='src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts' && npm run build`

Expected: PASS

- [ ] **Step 5: Angular 커밋**

```bash
git -C desktop/clipper_angular add src/features/shortform-director
git -C desktop/clipper_angular commit -m "feat: explain YouTube Shorts validation"
```

### Task 9: 전체 회귀 검증과 실제 앱 E2E 준비

**Files:**
- Modify: `.codex/handoff/NEXT.md`
- Modify: `.codex/records/sessions/2026/07/29.md`

**Interfaces:**
- Consumes: Tasks 1~8의 각 커밋
- Produces: 자동 검증 결과와 실제 유료 호출 전 승인 가능한 앱 빌드

- [ ] **Step 1: 각 저장소 상태와 diff 범위 확인**

Run: `git -C web/clipper_web_api status --short && git -C desktop/clipper_nestjs status --short && git -C desktop/clipper_angular status --short && git -C .codex status --short`

Expected: 계획된 문서 갱신 전까지 코드 저장소 clean

- [ ] **Step 2: Web API shortform 관련 전체 테스트와 빌드**

Run: `cd web/clipper_web_api && npm test -- --runInBand src/modules/shortform-director-research src/modules/shortform-director-inference && npm run build`

Expected: PASS

- [ ] **Step 3: Desktop Nest shortform 전체 테스트와 빌드**

Run: `cd desktop/clipper_nestjs && npm run build && node --test test/shortform-director-*.test.js`

Expected: PASS

- [ ] **Step 4: Angular AI Director 전체 테스트와 빌드**

Run: `cd desktop/clipper_angular && npm test -- --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/**/*.spec.ts' && npm run build`

Expected: PASS

- [ ] **Step 5: 정적 금지 규칙 검사**

Run: `rg -n "MAX_CANDIDATES\\s*=\\s*6|MAX_PER_CHANNEL|selectedVideoIds\\.length\\s*!==\\s*3|ArrayMinSize\\(3\\)|ArrayMaxSize\\(3\\)|slice\\(0,\\s*3\\)" desktop/clipper_nestjs/src/modules/shortform-director desktop/clipper_angular/src/features/shortform-director`

Expected: 이번 흐름을 제한하는 결과 0개

Run: `rg -n "shorts|쇼츠|챌린지" desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-query-plan.ts`

Expected: YouTube 검색어에 suffix를 강제로 추가하는 코드 0개

- [ ] **Step 6: 앱 재빌드 전 사용자와 실행 프로세스 상태 확인**

실행 중인 Clipper 앱을 임의 종료하지 않는다. 사용자가 종료했다고 확인한 뒤 `desktop/clipper_electron`에서 기존 local-api 패키징 명령을 실행한다.

Run: `cd desktop/clipper_electron && npm run build:app:mac:arm64:local-api`

Expected: PASS

- [ ] **Step 7: 실제 유료 E2E는 화면 preflight를 사용자에게 먼저 제시**

다음 순서에서 매 유료 단계는 사용자의 화면 승인을 받은 뒤 실행한다.

1. 실제 운영 프로필+집중 키워드 discovery
2. 두 search call의 `maxResults=40`, 같은 30일 필터 확인
3. Shorts validation artifact의 전체 중복 제거 ID 검사 확인
4. 전체 확인 Shorts 목록 확인
5. 사용자가 1~5개 선택
6. 분석 preflight 비용 승인
7. 실제 미디어 획득, 기존 로컬 STT, Gemini 영상 분석
8. reference pattern, topic, 최소 10개 영상 후보 생성
9. 영상 제작과 보관함 큐 진입 확인

- [ ] **Step 8: handoff와 세션 기록 갱신**

자동 검증의 실제 명령·통과 수, 미실행된 라이브 단계, 다음 사용자 액션을 `.codex/handoff/NEXT.md`와 `.codex/records/sessions/2026/07/29.md`에 기록한다.

- [ ] **Step 9: 문서 커밋**

```bash
git -C .codex add handoff/NEXT.md records/sessions/2026/07/29.md
git -C .codex commit -m "docs: record verified Shorts implementation"
```

## 완료 판정

다음 조건을 모두 만족해야 구현 완료라고 보고한다.

1. 조회수순·관련도순 검색이 각각 최근 30일과 40개를 실제 요청한다.
2. 중복 제거된 ID 전부에 Shorts URL 검증을 시도했다는 artifact가 남는다.
3. 길이 컷이 아니라 Shorts URL 결과만으로 후보 포함 여부를 결정한다.
4. 확인된 Shorts 전체가 JSON과 화면에 남고 임의 표시 제한이 없다.
5. 기본 선택은 0개이며 1~5개 분석과 명시적 skip이 각각 동작한다.
6. 선택 N에 맞춰 실제 호출 수와 비용이 달라진다.
7. 분석 경로는 형식 근거를 topic·영상 후보 생성에 전달하고, skip 경로는 시장 근거만 전달한다.
8. 모든 조사·검증·LLM 결과는 기존 로컬 JSON 저장 규칙과 사람이 읽는 근거 화면 양쪽에서 확인된다.
9. 관련 자동 테스트와 세 저장소 빌드가 모두 통과한다.
10. 실제 provider E2E는 사용자 승인 후 실제 호출로 검증하며 fixture로 대체하지 않는다.
