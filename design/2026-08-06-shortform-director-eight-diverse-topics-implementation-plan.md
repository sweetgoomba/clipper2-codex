# Shortform Director Eight Diverse Topics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every new topic-synthesis operation return exactly eight
grounded, meaningfully different topics, all directly related to the optional
focus keyword.

**Architecture:** Web API owns the v5 prompt and exact-eight structured-output
contract. Desktop Nest forwards the focus keyword, mirrors the output bound,
and accepts v5 for new calls while retaining v3/v4 persisted-run compatibility.

**Tech Stack:** NestJS 11 + Jest in `clipper_web_api`; NestJS 10 + TypeScript +
`node:test` in `clipper_nestjs`.

## Global Constraints

- Produce exactly eight topics for initial research and stored-evidence
  regeneration.
- Every topic cites at least one supplied market-evidence identifier.
- When `focusKeyword` is present, every topic directly addresses it.
- Do not add unrelated or unsupported topics merely to fill the batch.
- Keep one normal topic-synthesis provider call and the existing 8,000-token
  output ceiling.
- Preserve reads and recovery for persisted topic-synthesis v3 and v4
  contracts.
- Do not change Angular UI, source collection, candidate generation, or paid
  provider behavior.
- Do not run paid provider calls or package the desktop application.
- Do not commit or push unless the user explicitly requests it.

---

### Task 1: Web API v5 Exact-Eight Topic Contract

**Files:**

- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify:
  `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`

**Interfaces:**

- Consumes: `INFERENCE_PURPOSE_SPECS['topic-synthesis']`.
- Produces: provider-input contract
  `shortform-director.topic-synthesis.v5`; `topics` array with
  `minItems: 8` and `maxItems: 8`.

- [x] **Step 1: Write failing prompt and contract tests**

Update the topic prompt test to expect v5 and assert the behavioral
requirements:

```ts
expect(spec.promptTemplateVersion).toBe(
  'shortform-director.topic-synthesis.v5',
);
[
  'exactly eight',
  'meaningfully distinct',
  'focusKeyword',
  'directly',
  'do not add unrelated or unsupported topics',
].forEach((text) => expect(spec.systemPrompt).toContain(text));
```

Build a literal eight-topic fixture from the existing valid topic body, assert
that schema bounds are exactly eight, and verify manual validation accepts
eight while rejecting seven and nine:

```ts
const eight = Array.from({ length: 8 }, (_, index) => ({
  ...topic,
  title: `주제 ${index + 1}`,
  angle: `서로 다른 관점 ${index + 1}`,
}));
expect(topicSchema).toEqual(expect.objectContaining({
  minItems: 8,
  maxItems: 8,
}));
expect(spec.validateOutput({ topics: eight })).toEqual({ ok: true });
expect(spec.validateOutput({ topics: eight.slice(0, 7) }).ok).toBe(false);
expect(spec.validateOutput({
  topics: [...eight, { ...topic, title: '주제 9', angle: '서로 다른 관점 9' }],
}).ok).toBe(false);
```

Update complete-output and market-only fixtures to contain eight literal,
grounded topic records so unrelated contract tests remain valid.

- [x] **Step 2: Run focused tests and verify RED**

Run:

```bash
npm test -- --runInBand \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts
```

Expected: failures report v4 instead of v5 and current topic bounds `0..100`
instead of exactly eight.

- [x] **Step 3: Implement the minimal v5 prompt and contract**

Advance only topic synthesis to v5:

```ts
purpose === 'topic-synthesis'
  ? `shortform-director.${purpose}.v5`
```

Replace the topic prompt with explicit count, diversity, focus, and grounding
instructions. Change only the top-level topic array:

```ts
topics: arraySchema(topicObjectSchema, 8, 8)
```

Mirror it in manual validation:

```ts
const topics = validator.array(root?.topics, '/topics', 8, 8);
```

- [x] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: both suites pass with no warnings.

---

### Task 2: Desktop v5 Projection and Persisted Compatibility

**Files:**

- Modify:
  `desktop/clipper_nestjs/test/shortform-director-web-api-clients.test.js`
- Modify:
  `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-source-fetch-response.projector.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-run-recovery.service.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-artifact.service.ts`

**Interfaces:**

- Consumes: Web API topic-synthesis v5 response and runtime contract.
- Produces: exact-eight fresh-response projection plus persisted v3/v4/v5
  parsing and recovery.

- [x] **Step 1: Write failing fresh-response and compatibility tests**

In the Web API client projection test, create eight distinct topic objects and
verify the response is accepted. Then feed seven and nine topics and assert the
bounded public projection error:

```js
assert.doesNotThrow(() =>
  projectShortformDirectorInferenceResponse('topic-synthesis', {
    ...source,
    output: { topics: eightTopics },
  }));
for (const topics of [eightTopics.slice(0, 7), [...eightTopics, ninthTopic]]) {
  assert.throws(
    () => projectShortformDirectorInferenceResponse('topic-synthesis', {
      ...source,
      output: { topics },
    }),
    BadGatewayException,
  );
}
```

Advance current fixtures to v5. Retain the existing v3 recovery fixture and add
or preserve a v4 fixture proving old persisted contracts remain readable.

- [x] **Step 2: Build and run focused tests to verify RED**

Run:

```bash
npm run build
node --test \
  test/shortform-director-web-api-clients.test.js \
  test/shortform-director-research-orchestrator.test.js
```

Expected: v5 is rejected by current allowlists and seven/nine topics are still
accepted by the response projector.

- [x] **Step 3: Implement exact-eight projection and v5 compatibility**

Change the topic-synthesis output projection to:

```ts
validateObjectList(output, 'topics', topicKeys, 8, 8, validateTopic);
```

Add v5 to runtime and persisted-contract allowlists while leaving v3 and v4 in
place:

```ts
[
  'shortform-director.topic-synthesis.v3',
  'shortform-director.topic-synthesis.v4',
  'shortform-director.topic-synthesis.v5',
]
```

- [x] **Step 4: Build and run focused tests to verify GREEN**

Run the Step 2 commands. Expected: build and both test files pass.

---

### Task 3: Forward the Focus Keyword to Every Topic-Synthesis Path

**Files:**

- Modify:
  `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-topic.builder.ts`
- Modify:
  `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`

**Interfaces:**

- Consumes: normalized `focusKeyword: string | null` from research provenance.
- Produces:
  `buildMarketOnlyInput(..., focusKeyword)` and
  `buildInput(..., focusKeyword)` topic-synthesis inputs containing the same
  normalized value.

- [x] **Step 1: Write failing orchestration tests**

Extend the focused initial-research test:

```js
assert.equal(
  harness.inferenceRequests.find(
    ({ purpose }) => purpose === 'topic-synthesis',
  ).input.focusKeyword,
  'AI 광고',
);
```

Extend stored-evidence regeneration to assert that the regeneration
topic-synthesis request receives the source run's original focus keyword, not a
new or null value. Add a builder assertion proving a broad run forwards
`focusKeyword: null`.

- [x] **Step 2: Build and run the orchestration test to verify RED**

Run:

```bash
npm run build
node --test --test-name-pattern="focus keyword|stored evidence|market-only" \
  test/shortform-director-research-orchestrator.test.js
```

Expected: the topic-synthesis input has no `focusKeyword`.

- [x] **Step 3: Implement focus-keyword propagation**

Extend both topic-context builders with a final optional parameter:

```ts
focusKeyword: string | null = null
```

Include it in the provider input:

```ts
input: {
  operatingProfile: inferenceProfile(profile),
  focusKeyword,
  evidence,
  audienceSignals,
  referencePatterns,
}
```

At each service call site, read the current or source research provenance and
pass its normalized `focusKeyword`. Stored-evidence regeneration must use
`sourceProvenance.focusKeyword`.

- [x] **Step 4: Build and run the orchestration test to verify GREEN**

Run the Step 2 commands. Expected: focused and broad topic-synthesis inputs
contain the correct string or `null`.

---

### Task 4: Cross-Repository Regression Verification

**Files:**

- Verify all files changed in Tasks 1–3.
- Update design status only after automated verification passes:
  `.codex/design/2026-08-06-shortform-director-eight-diverse-topics-design.md`

**Interfaces:**

- Consumes: completed Web API v5 contract and Desktop v5 consumer.
- Produces: build and test evidence without a paid provider call.

- [x] **Step 1: Run Web API verification**

```bash
npm run build
npm test -- --runInBand \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts
```

Expected: build succeeds and all selected suites pass.

- [x] **Step 2: Run Desktop Nest verification**

```bash
npm run build
node --test \
  test/shortform-director-web-api-clients.test.js \
  test/shortform-director-research-orchestrator.test.js \
  test/shortform-director-reference-analysis-skip.test.js \
  test/shortform-director-reference-analysis-orchestrator.test.js
```

Expected: build succeeds and all selected tests pass.

- [x] **Step 3: Review the diff and document verification**

Run `git diff --check` in both repositories. Confirm that:

- all changed production lines trace to exact-eight output, focus forwarding,
  or v5 compatibility;
- existing unrelated working-tree changes were preserved;
- no generated build artifact, secret, provider response body, or credential
  was added;
- no paid call or app packaging command ran.

Change the design status from `Proposed` to `Implemented; relevant verification
passed` only when Steps 1 and 2 are green. Do not commit or push.
