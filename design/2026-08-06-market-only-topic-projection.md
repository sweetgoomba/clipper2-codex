# Market-only Topic Projection Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept valid market-only `topic-synthesis` responses whose reference-derived ID arrays are empty while preserving evidence grounding.

**Architecture:** Keep the Desktop Nest inference response projector as the strict trust boundary. Align only its topic array bounds with the Web API schema and cover the market-only response shape through the existing real projector test suite.

**Tech Stack:** TypeScript, NestJS, Node.js `node:test`

## Global Constraints

- `evidenceIds` continues to require at least one item.
- `audienceSignalIds` and `referencePatternIds` allow zero items.
- Do not change endpoints, response envelopes, artifacts, prompts, provider calls, or UI behavior.
- Do not call a paid provider or build the packaged Electron app.
- Do not commit unless the user explicitly requests it.

---

### Task 1: Align market-only topic projection

**Files:**
- Modify: `test/shortform-director-web-api-clients.test.js`
- Modify: `src/modules/shortform-director/application/shortform-director-inference-response.projector.ts:602-604`

**Interfaces:**
- Consumes: `projectShortformDirectorInferenceResponse(purpose, value)`
- Produces: successful projection of a `topic-synthesis` output with one evidence ID and empty reference-derived ID arrays

- [x] **Step 1: Write the failing regression test**

Add this test after the table-driven inference output projection tests:

```js
test('inference projector accepts market-only topics without reference-derived ids', () => {
  const output = {
    topics: [{
      title: '종부세 개편 핵심',
      whyNow: '최근 세제 개편안이 발표됐다.',
      angle: '실거주 여부에 따른 차이를 설명한다.',
      evidenceIds: ['naver-2-1'],
      audienceSignalIds: [],
      referencePatternIds: [],
    }],
  };

  const projected = projectShortformDirectorInferenceResponse(
    'topic-synthesis',
    inferenceResponse({ output }),
  );

  assert.deepEqual(projected.output, output);
});
```

- [x] **Step 2: Build and run the focused test to verify RED**

Run:

```bash
npm run build
node --test --test-name-pattern="accepts market-only topics" test/shortform-director-web-api-clients.test.js
```

Expected: the focused test fails because the projector returns
`SHORTFORM_DIRECTOR_INFERENCE_RESPONSE_PROJECTION_INVALID`.

- [x] **Step 3: Apply the minimal projector correction**

Keep evidence grounding unchanged and remove the minimum-one argument only
from the two reference-derived arrays:

```ts
boundedStringList(item.evidenceIds, MAX_ID, 1);
boundedStringList(item.audienceSignalIds, MAX_ID);
boundedStringList(item.referencePatternIds, MAX_ID);
```

- [x] **Step 4: Build and run the focused test to verify GREEN**

Run:

```bash
npm run build
node --test --test-name-pattern="accepts market-only topics" test/shortform-director-web-api-clients.test.js
```

Expected: the focused regression test passes.

- [x] **Step 5: Run the complete affected test file**

Run:

```bash
node --test test/shortform-director-web-api-clients.test.js
```

Expected: all tests in the affected file pass with zero failures.

- [x] **Step 6: Inspect the scoped diff**

Run:

```bash
git diff --check -- \
  src/modules/shortform-director/application/shortform-director-inference-response.projector.ts \
  test/shortform-director-web-api-clients.test.js
git diff -- \
  src/modules/shortform-director/application/shortform-director-inference-response.projector.ts \
  test/shortform-director-web-api-clients.test.js
```

Expected: only the regression test and the two minimum array bounds are
changed; `evidenceIds` still requires one item.
