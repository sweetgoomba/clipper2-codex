# AI 숏폼 디렉터 부분 레퍼런스 성공 자동 진행 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선택한 레퍼런스 영상 중 한 개 이상이 정밀 분석에 성공하면 성공 결과만으로 조사 종합을 완료하고, 전부 실패한 경우에는 사용자가 재시도·교체·정밀 분석 없이 계속 중 하나를 선택하게 한다.

**Architecture:** Desktop NestJS의 부모 조사 재개 조건을 “선택 영상 전부 통과”에서 “검증 통과 분석 한 개 이상”으로 변경하고, 종합 입력은 기존 `passedReferenceAnalyses` 결과만 사용한다. Angular store는 부분 성공 attempt에서 부모 종합이 끝날 때까지 폴링하며, 진행 컴포넌트는 부모의 완료 상태와 별개로 영상별 성공·실패 집계를 표시한다.

**Tech Stack:** NestJS 10, TypeScript, 로컬 JSON artifact/run 저장소, Node `node:test`, Angular 19 standalone components/signals, Jasmine/Karma

## Global Constraints

- 검증 통과 분석이 한 개 이상이면 성공 결과만으로 자동 종합한다.
- 검증 통과 분석이 없으면 부모 run을 `awaiting_reference_selection`에 유지한다.
- 부모 종합이 정상 완료되면 레퍼런스 일부 실패만으로 `partial`을 사용하지 않고 `succeeded`로 완료한다.
- 분석 attempt의 실제 `partial` 상태와 실패 artifact·비용 기록은 보존한다.
- 전부 실패한 경우 기존 market-only skip preflight와 실행 경로를 재사용한다.
- 새 결제·크레딧 차감·run status·데이터 저장소는 추가하지 않는다.
- 실제 외부 provider를 테스트에서 호출하지 않는다.
- 기존 일반 checkout에서 작업하며 새 worktree를 만들지 않는다.
- 각 코드 저장소의 변경은 관련 테스트 통과 직후 별도 커밋한다.

---

### Task 1: Desktop NestJS 부분 성공 조사 재개

**Files:**
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js:2102-2260`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts:208-260`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts:520-555`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts:784-796`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts:963-972`

**Interfaces:**
- Consumes: `ShortformDirectorResearchArtifactService.passedReferenceAnalyses(run, selection): PassedReferenceAnalysis[]`
- Produces: `resumeAfterReferenceAnalyses()`가 통과 분석 `1..5`개면 종합을 실행하고, `0`개면 기존 대기 run을 반환한다.
- Preserves: `reference-pattern-synthesis` 입력의 `referenceAnalyses`에는 통과 분석만 들어간다.

- [ ] **Step 1: 부분 성공 재개 실패 테스트 작성**

기존 `all five selected reference analyses...` 테스트를 전부 성공과 부분 성공을 분리해 다음 동작을 검증한다.

```js
test('successful subset resumes research with only passed reference analyses', async () => {
  // 선택 5개, passedReferenceAnalyses는 앞의 4개만 반환한다.
  const result = await harness.service.resumeAfterReferenceAnalyses(
    RUN_ID,
    auth,
    synthesisCredential(),
  );

  assert.equal(result.status, 'succeeded');
  const patternRequest = harness.inferenceRequests.find(
    ({ purpose }) => purpose === 'reference-pattern-synthesis',
  );
  assert.deepEqual(
    patternRequest.input.referenceAnalyses.map(({ videoId }) => videoId),
    analyses.slice(0, 4).map(({ videoId }) => videoId),
  );
  assert.equal(harness.runs.get(RUN_ID).status, 'succeeded');
});
```

- [ ] **Step 2: 전부 실패 대기 실패 테스트 작성**

```js
test('zero passed reference analyses keeps research awaiting user choice', async () => {
  harness.records.passedReferenceAnalyses = async () => [];

  const result = await harness.service.resumeAfterReferenceAnalyses(
    RUN_ID,
    auth,
    synthesisCredential(),
  );

  assert.equal(result.status, 'awaiting_reference_selection');
  assert.equal(
    harness.inferenceRequests.some(
      ({ purpose }) => purpose === 'reference-pattern-synthesis',
    ),
    false,
  );
});
```

- [ ] **Step 3: 부분 실패가 부모 완료 상태를 낮추지 않는 실패 테스트 작성**

부분 성공 분석의 `attemptRunId`가 가리키는 child manifest를 `partial`로 만들고, 부모
`failureRefs`는 비운 상태에서 종합 결과가 `succeeded`인지 검증한다. 기존
`an optional discovery failure makes the resumed parent partial` 테스트는 부모 자체의
`failureRefs`가 있을 때 `partial`을 유지하는 회귀 테스트로 남긴다.

- [ ] **Step 4: RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-orchestrator.test.js
```

Expected: 부분 성공 테스트는 `awaiting_reference_selection`을 받아 실패하고, 부분 child
상태 테스트는 부모가 `partial`이 되어 실패한다.

- [ ] **Step 5: 부모 재개 조건 최소 수정**

`resumeAfterReferenceAnalyses()`와 `hasCurrentReferenceAnalysisContinuation()`에서
선택 수와 통과 수의 완전 일치 조건을 제거하고 다음 경계만 유지한다.

```ts
if (passed.length === 0) {
  return { parent, resumed: null, selection: null, passed: null };
}
```

선택 revision 일치와 `passedReferenceAnalyses()`의 검증된 artifact 판정은 그대로
사용한다.

- [ ] **Step 6: 부모 최종 상태 의미 수정**

`completeReferenceSynthesis()`는 레퍼런스 child attempt의 `partial`을 부모 상태에
전파하지 않는다. 부모 run 자체의 discovery `failureRefs`가 있을 때만 기존처럼
`partial`을 유지한다.

```ts
const terminalStatus =
  run.failureRefs.length > 0 ? 'partial' : 'succeeded';
```

불필요해진 child run 조회 로직은 제거한다.

- [ ] **Step 7: GREEN 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-research-orchestrator.test.js
node --test test/shortform-director-reference-analysis-orchestrator.test.js
```

Expected: 두 테스트 파일 모두 실패 `0`.

- [ ] **Step 8: Desktop NestJS 커밋**

```bash
git add \
  src/modules/shortform-director/application/shortform-director-research.service.ts \
  test/shortform-director-research-orchestrator.test.js
git commit -m "fix(shortform-director): continue after partial reference success"
```

---

### Task 2: Angular 부분 성공 부모 폴링

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts:870-1015`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts:810-855`

**Interfaces:**
- Consumes: `listReferenceAnalyses(runId)`가 반환하는 검증 통과 분석 목록
- Produces: partial attempt에 성공 분석이 있으면 `getRun()` 폴링을 계속하고, 성공 분석이 없으면 기존 후보 교체 상태로 돌아간다.

- [ ] **Step 1: 부분 성공 폴링 실패 테스트 작성**

partial attempt, 통과 분석 2개, 첫 부모 응답 `awaiting_reference_selection`, 다음 부모 응답
`succeeded`를 준비한다.

```ts
gateway.listReferenceAnalyses.and.resolveTo({
  schemaVersion: 'shortform-director-reference-analyses.v1',
  runId: awaitingRun.id,
  analyses: [acceptedEntryOne, acceptedEntryTwo],
});
gateway.getRun.and.returnValues(
  Promise.resolve(awaitingRun),
  Promise.resolve(terminalParent),
);

expect(store.selectedRun()).toEqual(terminalParent);
expect(store.topics()).toEqual(terminalTopics);
```

첫 partial 응답 뒤에도 `getReferenceAnalysisAttempt()`가 다시 호출되는지 함께 검증한다.

- [ ] **Step 2: 전부 실패 시 사용자 선택 대기 회귀 테스트 작성**

기존 `does not retain an approval after a partial attempt...` 테스트의
`listReferenceAnalyses()` 결과를 빈 배열로 명시하고 다음을 유지한다.

```ts
expect(store.selectionRevision()).toBeNull();
expect(store.referencePreflight()).toBeNull();
expect(store.referenceCandidates()).toEqual(replacementCandidates);
expect(store.lockedReferenceVideoIds()).toEqual([]);
```

- [ ] **Step 3: RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts'
```

Expected: 부분 성공 테스트에서 store가 partial attempt 직후 폴링을 멈춰 실패한다.

- [ ] **Step 4: partial attempt 분기 최소 수정**

`pollReferenceAttempt()`에서 attempt가 `partial`일 때 이미 불러온 검증 통과 분석 수를
확인한다.

```ts
if (attempt.status === 'partial') {
  const passedCount = this.referenceAnalyses()?.analyses.length ?? 0;
  if (passedCount > 0) {
    this.pollReferenceAttempt(session);
    return;
  }
  this.clearReferenceApproval();
  await this.loadReferenceCandidates(session.runId, session);
  return;
}
```

부모가 먼저 terminal이 된 경우의 기존 topic 로딩 분기는 그대로 우선한다.

- [ ] **Step 5: GREEN 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/state/shortform-director-research.store.spec.ts'
```

Expected: 대상 store 테스트 전체 통과.

- [ ] **Step 6: Angular 폴링 커밋**

```bash
git add \
  src/features/shortform-director/state/shortform-director-research.store.ts \
  src/features/shortform-director/state/shortform-director-research.store.spec.ts
git commit -m "fix(shortform-director): keep polling after partial reference success"
```

---

### Task 3: 레퍼런스 성공·실패 집계와 전부 실패 안내

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.ts:20-55`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.html:1-12`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.spec.ts:5-80`

**Interfaces:**
- Consumes: 기존 `videos`, `progress`, `attemptRunId` inputs
- Produces: `completionSummary(): { total: number; succeeded: number; failed: number } | null`
- Produces: 완료 시 `레퍼런스 N개 중 M개 분석 성공 · F개 실패` 문구

- [ ] **Step 1: 부분 성공 집계 실패 테스트 작성**

기존 컴포넌트 테스트의 2개 성공·1개 실패 fixture에 다음 검증을 추가한다.

```ts
expect(
  root.querySelector('[data-reference-completion-summary]')?.textContent,
).toContain('레퍼런스 3개 중 2개 분석 성공 · 1개 실패');
```

- [ ] **Step 2: 전부 실패 안내 실패 테스트 작성**

세 영상 모두 failed인 fixture를 추가하고 다음 문구를 검증한다.

```ts
expect(text).toContain(
  '정밀 분석 없이 계속하거나, 실패 영상을 다시 시도하거나, 다른 영상을 선택할 수 있습니다.',
);
```

- [ ] **Step 3: RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.spec.ts'
```

Expected: 집계와 전부 실패 안내 요소가 없어 실패한다.

- [ ] **Step 4: 집계 계산과 템플릿 구현**

모든 영상 상태가 `completed`, `reused`, `failed` 중 하나일 때만 집계를 반환한다.
진행 중에는 완료 집계를 표시하지 않는다.

```ts
completionSummary(): {
  total: number;
  succeeded: number;
  failed: number;
} | null {
  const statuses = this.videos.map(({ videoId }) => this.status(videoId));
  if (statuses.some((value) => value === 'pending' || value === 'running')) {
    return null;
  }
  return {
    total: statuses.length,
    succeeded: statuses.filter(
      (value) => value === 'completed' || value === 'reused',
    ).length,
    failed: statuses.filter((value) => value === 'failed').length,
  };
}
```

템플릿은 `data-reference-completion-summary` 속성으로 결과를 표시하고,
`summary.succeeded === 0`일 때만 세 가지 다음 행동 안내를 추가한다. SCSS는 기존
semantic token만 사용한다.

- [ ] **Step 5: GREEN 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false \
  --include='src/features/shortform-director/components/research-reference-analysis-progress/research-reference-analysis-progress.component.spec.ts'
```

Expected: 컴포넌트 테스트 전체 통과.

- [ ] **Step 6: Angular 표시 커밋**

```bash
git add \
  src/features/shortform-director/components/research-reference-analysis-progress/
git commit -m "feat(shortform-director): show partial reference analysis summary"
```

---

### Task 4: 전체 회귀 검증과 작업 기록

**Files:**
- Modify: `.codex/handoff/NEXT.md`
- Modify: `.codex/records/sessions/2026/07/31.md`

**Interfaces:**
- Consumes: Task 1~3의 커밋과 테스트 결과
- Produces: 다음 세션이 재현할 수 있는 기준점, 실제 앱 재검증 순서

- [ ] **Step 1: Desktop NestJS 전체 AI 디렉터 검증**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-*.test.js
```

Expected: 실패 `0`; 환경 의존 skip은 기존 수와 사유를 기록한다.

- [ ] **Step 2: Angular 전체 검증**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
./node_modules/.bin/ng test --watch=false
npm run build
```

Expected: 테스트와 build 모두 성공.

- [ ] **Step 3: diff와 저장소 상태 확인**

Run:

```bash
git -C /Users/jina/project/adlight/desktop/clipper_nestjs diff --check
git -C /Users/jina/project/adlight/desktop/clipper_angular diff --check
git -C /Users/jina/project/adlight/.codex diff --check
```

Expected: 출력 없음.

- [ ] **Step 4: `.codex` 작업 기록 갱신**

다음을 실제 결과와 함께 기록한다.

- 부분 성공 시 부모 `succeeded`, child `partial`
- 전부 실패 시 부모 `awaiting_reference_selection`
- 성공 분석만 OpenAI 종합 입력에 포함
- 화면 집계 문구와 전부 실패 선택지
- 테스트 개수, commit ID, 외부 provider 미호출
- 실제 앱에서는 새 partial attempt 또는 기존 재현 가능한 조사로 확인할 것

- [ ] **Step 5: `.codex` 커밋**

```bash
git add \
  handoff/NEXT.md \
  records/sessions/2026/07/31.md \
  design/SHORTFORM_DIRECTOR_PARTIAL_REFERENCE_CONTINUATION_EXECUTION_PLAN_2026-07-31.md
git commit -m "docs: record partial reference continuation"
```

