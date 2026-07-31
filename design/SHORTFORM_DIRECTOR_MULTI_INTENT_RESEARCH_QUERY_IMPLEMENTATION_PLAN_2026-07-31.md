# Shortform Director Multi-Intent Research Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** 운영 프로필에 여러 목적이 있어도 이를 하나의 긴 YouTube 검색어로 합치지 않고 최대 2개의 독립된 조사 범위로 나눈 뒤, 각 범위를 조회수순·관련도순으로 모두 수집하고 그 과정을 화면과 JSON에서 확인할 수 있게 한다.

**Architecture:** Web API의 `query-plan` 출력 계약을 명시적인 Naver 검색어와 YouTube 조사 범위 구조로 바꾼다. 데스크톱 Nest는 최대 2개의 YouTube 범위를 받아 범위마다 같은 검색어로 `viewCount`와 `relevance`를 각각 호출하고, 최대 160개의 중복 제거 후보를 전부 Shorts URL로 확인한다. 기존 v1 레퍼런스 후보 스냅샷은 유지하되, 조회 근거는 이미 저장되는 source-call artifact와 새 v2 Shorts 검증 artifact로 연결한다. Angular는 이 artifact를 사람이 읽기 쉬운 범위·검색어·정렬·결과 수로 표시하고 원문 JSON은 기존처럼 접어서 제공한다.

**Tech Stack:** NestJS 11, TypeScript, Jest, Node test runner, Angular, Jasmine/Karma, 로컬 JSON artifact 저장소.

---

## 구현 불변 조건

- 운영 프로필은 하나의 목적만 갖도록 제한하지 않는다.
- `focusKeyword`가 있으면 조사 범위 구성에서 가장 우선한다.
- YouTube 조사 범위는 1개 또는 2개다.
- 각 범위는 같은 검색어로 `viewCount` 40개와 `relevance` 40개를 모두 요청한다.
- 최대 4회의 `search.list`, 최대 160개의 중복 제거 전 원시 결과를 허용한다.
- 검색 결과를 일부에서 조기 중단하지 않고 모든 고유 video ID를 Shorts URL로 검증한다.
- 검색어에 `shorts`, `쇼츠` 같은 단어를 기계적으로 덧붙이지 않는다.
- 최근 30일, KR, 한국어, `videoDuration=short` 조건은 유지한다.
- 기존 로컬 JSON은 append-only로 보존한다. 기존 실행 기록을 수정하거나 덮어쓰지 않는다.
- 기존 `shortform-director-reference-candidates.v1` 읽기 호환성을 깨지 않는다.
- 레퍼런스를 아직 선택하지 않은 기존 조사 실행의 분석 목록은 정상적인 빈 배열이다. 존재하지 않는 조사 실행만 404다.
- 외부 API 호출은 구현 검증에 사용하지 않는다. 실제 호출은 기존 사전 점검·비용 승인 흐름을 통해서만 실행한다.
- 관리자 페이지의 credential 구조를 그대로 사용하고 환경변수에 키를 추가하지 않는다.
- 크레딧 차감은 추가하지 않는다.
- `legacy/adlight_python/fastapi_server.spec`는 수정하지 않는다.

## Task 1: Web API query-plan v3 계약과 프롬프트

**Files:**

- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.spec.ts`

### Step 1: 실패하는 계약 테스트 작성

`query-plan`의 성공 fixture를 다음 구조로 바꾼다.

```ts
{
  naverNewsQueries: [
    {
      query: '원룸 수납 인테리어',
      rationale: '꾸미기 목적의 최신 기사와 사례를 찾는다.',
    },
  ],
  youtubeScopes: [
    {
      label: '원룸 인테리어와 수납',
      query: '원룸 인테리어 수납',
      rationale: '좁은 공간을 꾸미는 실제 Shorts 구성을 찾는다.',
    },
    {
      label: '자취방 계약 전 확인',
      query: '자취방 구하기 체크리스트',
      rationale: '방을 구할 때 확인할 항목을 다룬 Shorts를 찾는다.',
    },
  ],
  datalabKeywords: ['원룸 인테리어', '자취방 구하기'],
  selectedTrendSignals: [],
}
```

다음 거부 사례도 추가한다.

- `youtubeScopes`가 0개 또는 3개
- label/query/rationale 중 하나가 빈 문자열
- 두 범위의 query가 대소문자·공백 정규화 후 중복
- YouTube query에 `site:youtube.com` 포함
- Naver 검색어가 0개 또는 3개

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts
```

Expected: 기존 `queries` 계약 때문에 새 fixture가 실패한다.

### Step 3: 최소 계약 구현

- `QUERY_PLAN_SCHEMA`를 `naverNewsQueries`, `youtubeScopes`, `datalabKeywords`, `selectedTrendSignals`로 분리한다.
- Naver 항목은 query/rationale, YouTube 항목은 label/query/rationale를 갖는다.
- 각각 1–2개만 허용한다.
- 수동 validator도 같은 경계와 필드를 검사한다.
- `query-plan` 템플릿 버전을 `shortform-director.query-plan.v3`로 올린다.
- 프롬프트에 다음을 명시한다.
  - 프로필의 여러 목적을 한 검색어에 이어 붙이지 않는다.
  - 의미가 다른 목적은 최대 2개의 독립 범위로 나눈다.
  - 각 범위의 query는 하나의 검색 의도만 표현한다.
  - focusKeyword가 있으면 모든 범위보다 우선한다.
  - Shorts 형식 단어를 억지로 추가하지 않는다.

### Step 4: 전체 Web API 검증

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand
npm run build
```

Expected: 모든 테스트와 빌드 통과.

### Step 5: 커밋

```bash
git -C /Users/jina/project/adlight/web/clipper_web_api add src/modules/shortform-director-inference
git -C /Users/jina/project/adlight/web/clipper_web_api commit -m "feat(director): plan multi-intent research scopes"
```

## Task 2: 데스크톱 query-plan v3 투영과 입력 제약

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-query-plan.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-input.builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-query-plan.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-web-api-clients.test.js`

### Step 1: 실패하는 투영 테스트 작성

다음을 검증한다.

```ts
assert.deepEqual(plan.youtubeScopes, [
  {
    scopeId: 'youtube-scope-1',
    label: '원룸 인테리어와 수납',
    query: '원룸 인테리어 수납',
    rationale: '...',
  },
  {
    scopeId: 'youtube-scope-2',
    label: '자취방 계약 전 확인',
    query: '자취방 구하기 체크리스트',
    rationale: '...',
  },
]);
```

- LLM은 scope ID를 만들지 않고 서버가 배열 순서대로 안정적인 ID를 부여한다.
- 공백 정규화 후 중복 query는 거부한다.
- v2 응답은 새 실행에서 허용하지 않는다.
- Web API 응답의 템플릿 버전은 v3만 수락한다.
- query-plan 입력의 `maximumYoutubeScopes`는 2다.

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-query-plan.test.js test/shortform-director-web-api-clients.test.js
```

Expected: 기존 단일 `youtubeQuery` 투영 때문에 실패한다.

### Step 3: 최소 투영 구현

```ts
interface ResearchYoutubeScope {
  scopeId: `youtube-scope-${1 | 2}`;
  label: string;
  query: string;
  rationale: string;
}

interface ResearchQueryPlan {
  naverNewsQueries: readonly string[];
  youtubeScopes: readonly ResearchYoutubeScope[];
  datalabKeywords: readonly string[];
  selectedTrendSignals: readonly ResearchTrendSelection[];
}
```

- query-plan 입력의 제약 설명도 최대 2개 범위로 맞춘다.
- 화면/저장용 query-plan inference artifact에는 Web API가 반환한 label/query/rationale가 그대로 남는다.

### Step 4: GREEN 확인

Task 2의 두 테스트를 다시 실행하고 통과를 확인한다.

### Step 5: 커밋

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs add src/modules/shortform-director/application test/shortform-director-research-query-plan.test.js test/shortform-director-web-api-clients.test.js
git -C /Users/jina/project/adlight/desktop/clipper_nestjs commit -m "feat(director): project multi-intent research scopes"
```

## Task 3: 범위별 YouTube 4개 lane 수집과 비용 사전 점검

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-cost-estimate.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-cost-estimate.test.js`

### Step 1: 실패하는 수집 테스트 작성

두 범위 fixture에 대해 source call이 정확히 다음 순서로 저장되는지 검증한다.

1. `원룸 인테리어 수납` + `viewCount` + 40
2. `원룸 인테리어 수납` + `relevance` + 40
3. `자취방 구하기 체크리스트` + `viewCount` + 40
4. `자취방 구하기 체크리스트` + `relevance` + 40

한 범위일 때는 2회만 호출하고, 첫 범위가 0개여도 두 번째 범위 호출을 생략하지 않는 테스트를 추가한다.

사전 점검은 다음 상한을 표시해야 한다.

- YouTube search: 최대 4회
- Search Queries: 최대 4/100 calls
- video details: 최대 4회
- YouTube Data API: 최대 4 quota units

`search.list`와 `videos.list`의 현재 비용 기준은 2026-07-31 확인한 공식 문서를 따른다.

- https://developers.google.com/youtube/v3/docs/search/list
- https://developers.google.com/youtube/v3/docs/videos/list

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-orchestrator.test.js test/shortform-director-research-cost-estimate.test.js
```

Expected: 기존 단일 query의 2회 호출과 기존 비용 상한 때문에 실패한다.

### Step 3: 최소 수집 구현

- `collectYoutubeCandidateSearches(scopes, ...)`가 범위마다 두 order를 호출하게 한다.
- 각 source-call JSON의 request에 실제 `q`, `order`, 기간, region, language, duration, maxResults를 그대로 보존한다.
- 고유 video ID 상한을 80에서 160으로 올린다.
- `videos.list`는 50개씩 최대 4회로 나눈다.
- discovery service는 단일 `primaryQuery` 대신 `plan.youtubeScopes`를 전달한다.
- 한 호출의 검색 결과가 0개여도 나머지 호출은 계속한다.

### Step 4: GREEN 확인

Task 3의 두 테스트를 다시 실행한다.

### Step 5: 커밋

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs add src/modules/shortform-director/application/shortform-director-research-source.collector.ts src/modules/shortform-director/application/shortform-director-research-discovery.service.ts src/modules/shortform-director/domain/research-cost-estimate.ts test/shortform-director-research-orchestrator.test.js test/shortform-director-research-cost-estimate.test.js
git -C /Users/jina/project/adlight/desktop/clipper_nestjs commit -m "feat(director): collect every research scope lane"
```

## Task 4: 160개 Shorts 검증과 범위 근거 보존

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/youtube-shorts-validation.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-youtube-shorts.validator.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-source.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/reference-candidate.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.collector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-candidate.ranker.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-candidates.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-youtube-shorts-validator.test.js`

### Step 1: 실패하는 검증·랭킹 테스트 작성

- 네 search call에서 나온 160개 고유 ID가 전부 검증 요청으로 전달된다.
- 같은 영상이 여러 범위/order에서 발견되면 video ID는 한 번만 검증하고 모든 source artifact ID를 보존한다.
- v2 검증 artifact는 `youtubeScopes`를 저장하고 결과를 최대 160개 허용한다.
- v1 검증 artifact는 계속 읽을 수 있다.
- 후보의 query relevance는 후보가 실제 발견된 검색어 중 가장 높은 점수를 사용한다.
- 후보 v1 스냅샷의 공개 필드는 변경하지 않는다.

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-candidates.test.js test/shortform-director-youtube-shorts-validator.test.js
```

Expected: 80개 제한과 단일 query artifact 때문에 실패한다.

### Step 3: 최소 구현

- `shortform-director-youtube-shorts-validation.v2`를 추가한다.
- v2는 `youtubeScopes`의 scopeId/label/query/rationale와 최대 160개 결과를 저장한다.
- parser는 v1과 v2를 모두 읽되 새 실행은 v2만 쓴다.
- 검증 요청은 모든 search call 결과를 중복 제거하며 source artifact 연결을 합친다.
- 후보 수집 내부 타입에 `matchedQueries`를 둔다.
- 랭커는 `matchedQueries` 중 최대 관련도 점수를 사용한다.
- 영속화되는 `shortform-director-reference-candidates.v1`에는 내부 필드를 포함하지 않는다.
- `primaryQuery`는 v1 호환 표시용으로 첫 번째 범위 query를 사용하고, 정확한 전체 근거는 query-plan/source-call/validation v2 artifact로 보존한다.

### Step 4: GREEN 확인

Task 4의 두 테스트를 다시 실행한다.

### Step 5: 커밋

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs add src/modules/shortform-director/domain src/modules/shortform-director/application test/shortform-director-reference-candidates.test.js test/shortform-director-youtube-shorts-validator.test.js
git -C /Users/jina/project/adlight/desktop/clipper_nestjs commit -m "feat(director): preserve multi-scope Shorts evidence"
```

## Task 5: 레퍼런스 미선택 상태를 정상 빈 목록으로 처리

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-reference-analysis.orchestrator.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-reference-analysis-orchestrator.test.js`

### Step 1: 실패하는 회귀 테스트 작성

```js
it('returns an empty analysis collection before reference selection', async () => {
  const response = await orchestrator.listAnalyses(existingRunId, auth);
  assert.deepEqual(response.analyses, []);
});
```

별도 테스트에서 존재하지 않는 run ID는 계속 404인지 검증한다.

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
```

Expected: 선택 artifact가 없어서 404가 발생한다.

### Step 3: 최소 구현

- artifact service에 nullable `findLatestReferenceSelection()`을 추가한다.
- 기존 strict 메서드는 nullable 메서드를 사용하되 선택 필수 흐름에서는 계속 404를 낸다.
- 분석 목록 조회만 선택이 없을 때 `{ analyses: [] }`를 반환한다.
- 부모 run 존재 여부와 소유권 검사는 먼저 수행한다.

### Step 4: GREEN 확인 및 커밋

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-reference-analysis-orchestrator.test.js
git add src/modules/shortform-director/application test/shortform-director-reference-analysis-orchestrator.test.js
git commit -m "fix(director): treat unselected references as empty"
```

## Task 6: 조사 범위와 수집 근거를 사람이 읽을 수 있게 표시

**Files:**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research-artifact-presentation.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-candidate-list/research-reference-candidate-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts`

### Step 1: 실패하는 화면 테스트 작성

요약 카드에서 다음 문구를 검증한다.

- `조사 범위 1 · 원룸 인테리어와 수납`
- `검색어 · 원룸 인테리어 수납`
- `조회수순 40개 요청 · 관련도순 40개 요청`
- `검색 결과 0개 · 확인된 Shorts 0개` 또는 실제 개수

후보 상세에서는 raw artifact ID만 보여주지 않고 다음처럼 표시한다.

- `원룸 인테리어 수납 · 조회수순`
- `자취방 구하기 체크리스트 · 관련도순`

원문 JSON은 기존 접기 영역에 그대로 남긴다.

### Step 2: RED 확인

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/**/*research*spec.ts'
```

Expected: 기존 단일 YouTube query 표시 때문에 실패한다.

### Step 3: 최소 표시 구현

- query-plan v3 presentation을 범위 배열로 투영한다.
- Shorts validation v1/v2를 모두 표시한다.
- source-call artifact의 실제 request `q`와 `order`를 읽어 범위별 결과 수를 집계한다.
- store에서 후보의 `sourceArtifactIds`와 source-call presentation을 연결해 검색어·정렬 근거 map을 만든다.
- 후보 컴포넌트에는 계산된 표시용 데이터만 입력한다.
- 사용자에게 내부 ID를 주 정보로 노출하지 않고, ID와 JSON은 상세 영역에 둔다.
- 레퍼런스 선택 전 빈 분석 목록은 오류 배너를 만들지 않는다.

### Step 4: 전체 Angular 검증

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

Expected: 모든 테스트와 빌드 통과.

### Step 5: 커밋

```bash
git -C /Users/jina/project/adlight/desktop/clipper_angular add src/features/shortform-director
git -C /Users/jina/project/adlight/desktop/clipper_angular commit -m "feat(director): explain multi-scope research evidence"
```

## Task 7: 통합 회귀 검증과 기록

**Files:**

- Modify: `.codex/records/sessions/2026/07/31.md`
- Modify: `.codex/handoff/NEXT.md`

### Step 1: 세 저장소 검증

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand
npm run build

cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-*.test.js

cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

Expected: 0 failures. 기존 환경 의존 테스트가 별도 명령에서 실패하면 이번 변경과 분리해서 정확히 기록하고, 관련 테스트가 실패한 상태로 완료 처리하지 않는다.

### Step 2: diff·금지 파일 확인

Run:

```bash
git -C /Users/jina/project/adlight/web/clipper_web_api status --short
git -C /Users/jina/project/adlight/desktop/clipper_nestjs status --short
git -C /Users/jina/project/adlight/desktop/clipper_angular status --short
git -C /Users/jina/project/adlight/.codex status --short
git -C /Users/jina/project/adlight/legacy/adlight_python diff -- fastapi_server.spec
```

Expected: 구현 저장소는 계획된 변경만 존재하고 `fastapi_server.spec`는 건드리지 않았다.

### Step 3: 세션·handoff 기록

- 구현 커밋과 검증 명령의 실제 결과를 기록한다.
- 기존 `run.director.02239be5d8d84cc880b02c9030dd7830`는 변경하지 않았음을 기록한다.
- 새 빌드에서 새 조사 실행을 만들어 실제 사용자 승인 흐름으로 확인해야 함을 NEXT에 남긴다.
- 실제 API 호출·비용 검증은 사용자의 사전 점검 승인 후 진행하도록 남긴다.

### Step 4: 문서 커밋

```bash
git -C /Users/jina/project/adlight/.codex add records/sessions/2026/07/31.md handoff/NEXT.md
git -C /Users/jina/project/adlight/.codex commit -m "docs: record multi-intent research implementation"
```

## 완료 기준

- 새 query-plan은 자취방 꾸미기와 방 구하기를 하나의 긴 검색어로 합치지 않는다.
- 한 범위면 2회, 두 범위면 4회의 YouTube 검색을 수행한다.
- 네 lane의 모든 고유 결과를 Shorts URL로 검증한다.
- 검색어, 정렬 방식, 결과 수, Shorts 확인 수를 사람이 읽을 수 있는 UI와 원문 JSON 양쪽에서 확인할 수 있다.
- 레퍼런스를 선택하기 전 분석 목록 조회가 일반 404 오류를 띄우지 않는다.
- 기존 v1 artifact와 과거 실행 기록을 계속 읽을 수 있다.
- 외부 API 실제 호출 없이 자동 테스트와 빌드가 모두 통과한다.
