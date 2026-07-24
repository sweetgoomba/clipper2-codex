# AI 숏폼 디렉터 품질 입력 검증 실험 Implementation Plan

상태: Task 1~3 offline 완료 · 기존 live Vira read 취소 · corpus 전략 결정 대기

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** 승인된 네 사례의 source pack을 재현 가능한 artifact로 동결하고, 입력 축별 품질
차이를 blind 평가할 수 있는 비-production 실험 harness와 실행 결과를 만든다.

**Architecture:** production Angular/NestJS/Web API를 변경하지 않고
`.codex/experiments/shortform-director-quality-input/` 아래에 case pack, validator,
condition compiler, provider dry-run/live runner, blind evaluator를 둔다. 공개 source,
Vira read-only snapshot, provider output을 분리하며 각 외부 접근은 immutable hash와
run manifest로 고정한다.

**Tech Stack:** Node.js 22 표준 라이브러리(`node:test`, `node:crypto`, `fetch`),
PostgreSQL 15 `psql`, JSON/Markdown, OpenAI Responses API의 현재 Shortform Director
기준 모델 `gpt-4.1`, 기존 `vira-evidence.v1` 계약

정본 설계:
`.codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_PROTOCOL_2026-07-24.md`

## 2026-07-24 실행 중지·재설계 기록

이 계획의 Task 1, Task 2와 Task 3 Step 1~6은 fixture 기반으로 구현·검증했다.

```text
four packs: 4/4 sealed
full offline suite: 38/38 pass
Task 3 independent spec review: ✅
Task 3 quality review: Approved
actual Vira DB / psql / YouTube API / yt-dlp / provider calls: 0
```

Task 3 Step 7에서 사용자가 현재 Vira DB의 실제 성격을 명확히 했다. 현재 Vira는 개발
중이며 DB에는 대표 market corpus가 아니라 소량의 테스트 데이터만 있다. 따라서
`shorts_*` row 유무로 네 주제나 `V` 입력 축의 효용을 판단할 수 없다.

다음 항목은 이 계획에서 더 이상 실행하지 않는다.

- Task 3 Step 8의 현재 Vira DB export
- Task 3 Step 9의 actual case normalization·reseal
- 현재 네 주제를 Vira keyword seed로 사용
- `provider_not_called` pack을 `insufficient`로 재해석
- 실제 `V` pack 없이 C4, C5, C6와 `FULL-V`를 실행

다음 세션은 아래 선택지 문서를 먼저 검토한다.

- `.codex/design/SHORTFORM_DIRECTOR_VIRA_VALIDATION_CORPUS_OPTIONS_2026-07-24.md`

사용자가 corpus 목적과 수집 접근을 승인한 뒤 이 계획의 Task 4 이후 condition matrix를
다시 작성한다. Vira branch/worktree, migration, local DB, YouTube API, yt-dlp와 provider
실행은 각각 명시적 승인 전까지 시작하지 않는다.

## Global Constraints

- 이번 계획은 평가용 artifact와 offline harness만 만든다. production 코드·API·DB·목업을
  변경하지 않는다.
- 모든 새 파일은 `.codex` repository 안에만 둔다.
- Vira 감사 계약은
  `main@2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4` 기준이다. 2026-07-24 최종 preflight에서
  실제 clean checkout이 예상과 달리 `main@5267ac0`으로 이동한 사실을 확인했다. 이를
  compatible하다고 가정하지 않으며, 사용자가 revision 처리 방향을 정하고 필요한
  재감사가 끝날 때까지 실제 Vira DB 조회는 blocked다. Vira checkout을 reset, checkout,
  worktree 생성하거나 Vira 파일, schema, DB row를 수정하지 않는다.
- Vira DB 조회를 실행하기 전에 사용자에게 대상 query와 출력 위치를 알리고 진행 의사를
  확인한다.
- 생성 provider의 첫 live 호출과 이후 추가 batch 호출 전에 사용자에게 모델, 예상 호출
  수와 출력 위치를 알리고 진행 의사를 확인한다.
- provider runner는 기본적으로 dry-run이며 `--live`와
  `SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1`이 모두 없으면 network를 사용하지 않는다.
- API key, DB URL, JWT, cookie, provider credential ID와 원문 댓글 작성자 정보를 파일,
  stdout, 로그에 남기지 않는다.
- `store: false`를 사용하며 provider 원문 response는 gitignored run directory에만 둔다.
- source의 공통 cutoff는 `2026-07-24 KST`다. 이후 retrieval에서 원문 버전을 입증할 수
  없으면 backdate하지 않고 `partial` 또는 `unavailable`로 기록한다.
- source fact, audience observation, Vira market observation, creative pattern,
  editorial interpretation와 AI hypothesis를 서로 다른 파일과 field로 유지한다.
- 기존
  `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-quality-evaluator.ts`
  는 변경하거나 이번 semantic 점수에 합치지 않는다. 이번 Track E는 native
  `DraftVideoPlan`이 아니므로 structural proxy를 실행한 것처럼 보고하지 않는다.
- `legacy/adlight_python/fastapi_server.spec`의 기존 수정은 보존한다.
- commit, push, PR, 배포, migration, 서버 재시작과 앱 실행은 별도 사용자 지시 없이는
  실행하지 않는다. 아래 task 끝의 checkpoint도 commit을 뜻하지 않는다.

---

## 1. 파일 구조와 책임

실행 시 다음 구조를 만든다.

```text
.codex/experiments/shortform-director-quality-input/
├── README.md
├── .gitignore
├── lib/
│   ├── canonical-json.mjs
│   ├── contracts.mjs
│   ├── condition-compiler.mjs
│   ├── generation-contracts.mjs
│   ├── provider-runner.mjs
│   ├── vira-normalizer.mjs
│   └── blind-evaluation.mjs
├── scripts/
│   ├── validate-packs.mjs
│   ├── seal-packs.mjs
│   ├── export-vira-readonly.mjs
│   ├── normalize-vira-export.mjs
│   ├── compile-run.mjs
│   ├── run-provider.mjs
│   ├── create-blind-set.mjs
│   └── aggregate-scores.mjs
├── prompts/
│   ├── discovery.instructions.md
│   └── elaboration.instructions.md
├── rubric/
│   ├── rubric.v1.json
│   └── evaluation-score.schema.json
├── vira/
│   └── export-readonly.sql
├── cases/
│   ├── beauty-01/
│   ├── product-01/
│   ├── idol-01/
│   └── expert-01/
├── tests/
│   ├── contracts.test.mjs
│   ├── seal-packs.test.mjs
│   ├── condition-compiler.test.mjs
│   ├── provider-runner.test.mjs
│   ├── vira-export-command.test.mjs
│   ├── vira-normalizer.test.mjs
│   ├── blind-evaluation.test.mjs
│   └── fixtures/
└── private/
```

각 case directory는 다음 8개 파일만 가진다.

```text
manifest.json
profile.json
episodes.json
source-cards.json
audience-cards.json
reference-cards.json
vira-evidence.json
feedback-cards.json
```

- `manifest.json`: cutoff, artifact digest와 materialization 상태
- `profile.json`: `P` 축
- `episodes.json`: episode A·B의 고정 질문
- `source-cards.json`: `S` 축의 공식·권위 source와 claim
- `audience-cards.json`: `A` 축의 비식별 질문 10개
- `reference-cards.json`: `R` 축의 구조·시각 pattern 최대 2개
- `vira-evidence.json`: `V` 축의 `vira-evidence.v1` 최대 5개 또는 부족 상태
- `feedback-cards.json`: `F` 축의 episode A 편집 기억 최대 3개

`private/`에는 Vira raw export, provider raw response, blind map, evaluator identity를 둔다.
이 directory는 전체가 gitignored다.

## 2. 공통 interface

### Case bundle

```js
/**
 * @typedef {{
 *   manifest: object,
 *   profile: object,
 *   episodes: object,
 *   sources: object,
 *   audience: object,
 *   references: object,
 *   vira: object,
 *   feedback: object
 * }} CaseBundle
 */
```

### Condition package

```js
/**
 * @typedef {{
 *   schemaVersion: 'quality-input-condition.v1',
 *   id: string,
 *   caseId: 'BEAUTY-01'|'PRODUCT-01'|'IDOL-01'|'EXPERT-01',
 *   episode: 'A'|'B',
 *   condition: 'C0'|'C1'|'C2'|'C3'|'C4'|'C5'|'C6'|
 *     'B-NO-F'|'FULL-P'|'FULL-S'|'FULL-A'|'FULL-V'|'FULL-R',
 *   axes: Array<'P'|'S'|'A'|'V'|'R'|'F'>,
 *   track: 'D'|'E',
 *   runId: string,
 *   sampleId: string|null,
 *   input: object,
 *   inputDigest: string
 * }} ConditionPackage
 */
```

### Provider output

```js
/**
 * @typedef {{
 *   schemaVersion: 'quality-input-output.v1',
 *   artifactId: string,
 *   conditionPackageId: string,
 *   track: 'D'|'E',
 *   payload: object,
 *   provider: {
 *     model: string,
 *     resolvedModel: string|null,
 *     responseId: string|null,
 *     inputTokens: number|null,
 *     outputTokens: number|null,
 *     estimatedCostUsd: number|null,
 *     elapsedMs: number
 *   }
 * }} ProviderOutput
 */
```

### Evaluation score

```js
/**
 * @typedef {{
 *   schemaVersion: 'quality-input-evaluation.v1',
 *   blindId: string,
 *   evaluatorId: string,
 *   pass: 'creative'|'evidence',
 *   scores: ({
 *     specificity: 1|2|3|4|5,
 *     novelty: 1|2|3|4|5,
 *     audienceRelevance: 1|2|3|4|5,
 *     hookPayoff: 1|2|3|4|5,
 *     visualizability: 1|2|3|4|5,
 *     productionFeasibility: 1|2|3|4|5
 *   }|{
 *     evidenceAccuracy: 1|2|3|4|5
 *   }),
 *   hardFailures: string[],
 *   notes: string
 * }} EvaluationScore
 */
```

---

### Task 1: 실험 workspace와 contract validator

**Files:**

- Create:
  `.codex/experiments/shortform-director-quality-input/README.md`
- Create:
  `.codex/experiments/shortform-director-quality-input/.gitignore`
- Create:
  `.codex/experiments/shortform-director-quality-input/lib/canonical-json.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/lib/contracts.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/contracts.test.mjs`
- Test fixture:
  `.codex/experiments/shortform-director-quality-input/tests/fixtures/minimal-case-bundle.json`

**Interfaces:**

- Consumes: JSON files described in section 1
- Produces:
  `canonicalJson(value): string`,
  `sha256Json(value): string`,
  `validateCaseBundle(bundle, { sealed }): CaseBundle`,
  `loadCaseBundle(caseDirectory): Promise<CaseBundle>`

- [ ] **Step 1: Write a failing contract test**

```js
import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import {
  validateCaseBundle,
} from '../lib/contracts.mjs';

const fixtureUrl = new URL('./fixtures/minimal-case-bundle.json', import.meta.url);

test('validates the fixed case bundle shape', async () => {
  const bundle = JSON.parse(await readFile(fixtureUrl, 'utf8'));
  assert.equal(validateCaseBundle(bundle, { sealed: false }).manifest.caseId, 'BEAUTY-01');
});

test('rejects an audience set that is not exactly ten questions', async () => {
  const bundle = JSON.parse(await readFile(fixtureUrl, 'utf8'));
  bundle.audience.questions.pop();
  assert.throws(
    () => validateCaseBundle(bundle, { sealed: false }),
    /audience\.questions must contain exactly 10 items/,
  );
});

test('rejects a sealed source without content digest or locator', async () => {
  const bundle = JSON.parse(await readFile(fixtureUrl, 'utf8'));
  bundle.manifest.state = 'sealed';
  bundle.sources.cards[0].contentDigest = null;
  assert.throws(
    () => validateCaseBundle(bundle, { sealed: true }),
    /sealed source card requires contentDigest and located claims/,
  );
});
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/contracts.test.mjs
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `lib/contracts.mjs`.

- [ ] **Step 3: Implement deterministic JSON hashing**

Write `lib/canonical-json.mjs`:

```js
import { createHash } from 'node:crypto';

function normalize(value) {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, normalize(value[key])]),
    );
  }
  return value;
}

export function canonicalJson(value) {
  return JSON.stringify(normalize(value));
}

export function sha256Json(value) {
  return `sha256:${createHash('sha256').update(canonicalJson(value)).digest('hex')}`;
}
```

- [ ] **Step 4: Implement the bundle validator**

`contracts.mjs` must enforce these exact invariants:

```js
export const CASE_IDS = ['BEAUTY-01', 'PRODUCT-01', 'IDOL-01', 'EXPERT-01'];
export const SOURCE_CLASSES = [
  'official_fact',
  'authority_explanation',
  'audience_observation',
  'market_observation',
  'creative_pattern',
  'editorial_interpretation',
  'ai_hypothesis',
];
export const AVAILABILITY = [
  'verified',
  'partial',
  'insufficient',
  'unavailable',
  'provider_not_called',
];
export const VIRA_STATES = [
  'provider_not_called',
  'sufficient',
  'partial',
  'insufficient',
  'unavailable',
];
export const DIGESTED_CASE_FILES = [
  'profile.json',
  'episodes.json',
  'source-cards.json',
  'audience-cards.json',
  'reference-cards.json',
  'vira-evidence.json',
  'feedback-cards.json',
];

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function sha256Digest(value) {
  return typeof value === 'string' && /^sha256:[0-9a-f]{64}$/.test(value);
}

function isoTimestamp(value) {
  return nonEmpty(value) && !Number.isNaN(Date.parse(value));
}

export function validateCaseBundle(bundle, { sealed }) {
  invariant(bundle && typeof bundle === 'object', 'case bundle must be an object');
  invariant(CASE_IDS.includes(bundle.manifest?.caseId), 'manifest.caseId is invalid');
  invariant(
    bundle.manifest.schemaVersion === 'quality-input-pack-manifest.v1'
      && isoTimestamp(bundle.manifest.cutoffAt),
    'manifest schemaVersion and cutoffAt are required',
  );
  invariant(
    bundle.profile?.profileSchemaVersion === 'quality-input-profile.v1'
      && bundle.profile.caseId === bundle.manifest.caseId
      && nonEmpty(bundle.profile.operatorRole)
      && nonEmpty(bundle.profile.audience)
      && nonEmpty(bundle.profile.desiredAfterState)
      && Array.isArray(bundle.profile.toneRules)
      && bundle.profile.toneRules.length > 0
      && bundle.profile.toneRules.every(nonEmpty)
      && Array.isArray(bundle.profile.prohibitedClaims)
      && bundle.profile.prohibitedClaims.length > 0
      && bundle.profile.prohibitedClaims.every(nonEmpty),
    'profile contract is invalid',
  );
  invariant(
    bundle.episodes?.episodeSchemaVersion === 'quality-input-episodes.v1'
      && bundle.episodes.caseId === bundle.manifest.caseId
      && nonEmpty(bundle.episodes.episodeA?.id)
      && nonEmpty(bundle.episodes.episodeA?.question)
      && nonEmpty(bundle.episodes.episodeB?.id)
      && nonEmpty(bundle.episodes.episodeB?.question)
      && bundle.episodes.episodeA.id === `${bundle.manifest.caseId}-A`
      && bundle.episodes.episodeB.id === `${bundle.manifest.caseId}-B`,
    'episodes A and B require fixed IDs and questions',
  );
  invariant(
    Array.isArray(bundle.sources?.cards)
      && bundle.sources.cards.length >= 3
      && bundle.sources.cards.length <= 5,
    'source cards must contain 3 to 5 items',
  );
  invariant(
    Array.isArray(bundle.audience?.questions)
      && bundle.audience.questions.length === 10,
    'audience.questions must contain exactly 10 items',
  );
  invariant(
    Array.isArray(bundle.references?.cards)
      && bundle.references.cards.length >= 1
      && bundle.references.cards.length <= 2,
    'reference cards must contain 1 to 2 items',
  );
  invariant(VIRA_STATES.includes(bundle.vira?.state), 'vira.state is invalid');
  invariant(
    Array.isArray(bundle.vira?.evidence) && bundle.vira.evidence.length <= 5,
    'vira.evidence must contain at most 5 items',
  );
  for (const question of bundle.audience.questions) {
    invariant(
      nonEmpty(question.id)
        && nonEmpty(question.question)
        && ['general_reader_question', 'audience_observation'].includes(question.originClass),
      'audience question is invalid',
    );
    invariant(
      !('author' in question) && !('handle' in question) && !('profileUrl' in question),
      'audience question must not contain identity fields',
    );
    if (question.originClass === 'audience_observation') {
      invariant(
        nonEmpty(question.sourceId) && nonEmpty(question.evidenceLocator),
        'audience observation requires sourceId and evidenceLocator',
      );
    }
  }
  for (const reference of bundle.references.cards) {
    invariant(
      nonEmpty(reference.id)
        && nonEmpty(reference.pattern)
        && nonEmpty(reference.allowedInfluence)
        && nonEmpty(reference.forbiddenUse)
        && nonEmpty(reference.rightsNote),
      'reference card is invalid',
    );
  }
  for (const evidence of bundle.vira.evidence) {
    invariant(
      evidence.schemaVersion === 'vira-evidence.v1'
        && ['market.video-observation', 'market.peer-growth'].includes(evidence.kind)
        && evidence.source?.system === 'vira'
        && ['sufficient', 'partial', 'insufficient', 'unavailable']
          .includes(evidence.observation?.state),
      'Vira evidence is invalid for this experiment',
    );
  }
  invariant(
    ['not_collected', 'ready'].includes(bundle.feedback?.state)
      && Array.isArray(bundle.feedback?.cards)
      && bundle.feedback.cards.length <= 3,
    'feedback must be not_collected or ready with at most 3 cards',
  );
  if (bundle.feedback.state === 'not_collected') {
    invariant(bundle.feedback.cards.length === 0, 'not_collected feedback must be empty');
  }
  if (bundle.feedback.state === 'ready') {
    invariant(
      bundle.feedback.cards.length >= 1
        && bundle.feedback.cards.every((card) => (
          nonEmpty(card.id)
          && nonEmpty(card.sourceOutputArtifactId)
          && ['approve', 'revise', 'reject'].includes(card.decision)
          && ['hook', 'thesis', 'claim', 'evidence', 'visual', 'feasibility', 'tone']
            .includes(card.appliesTo)
          && nonEmpty(card.observedProblem)
          && nonEmpty(card.preferredRule)
          && nonEmpty(card.evidenceOrExample)
          && ['route', 'topic_family', 'global'].includes(card.scope)
        )),
      'ready feedback requires 1 to 3 complete cards',
    );
  }

  for (const card of bundle.sources.cards) {
    invariant(nonEmpty(card.id), 'source card requires id');
    invariant(SOURCE_CLASSES.includes(card.sourceClass), 'sourceClass is invalid');
    invariant(
      nonEmpty(card.title)
        && nonEmpty(card.publisher)
        && nonEmpty(card.originalUrl)
        && (card.publishedAt === null || isoTimestamp(card.publishedAt))
        && isoTimestamp(card.retrievedAt)
        && isoTimestamp(card.cutoffAt)
        && Array.isArray(card.permittedUse)
        && card.permittedUse.length > 0
        && card.permittedUse.every((item) => (
          ['fact', 'audience', 'market', 'creative', 'editorial'].includes(item)
        ))
        && nonEmpty(card.rightsNote)
        && typeof card.notes === 'string',
      'source card metadata is invalid',
    );
    invariant(AVAILABILITY.includes(card.availability), 'availability is invalid');
    invariant(Array.isArray(card.claims), 'source card claims must be an array');
    if (['unavailable', 'insufficient'].includes(card.availability)) {
      invariant(card.claims.length === 0, 'unavailable source card claims must be empty');
    }
    if (sealed && !['unavailable', 'insufficient'].includes(card.availability)) {
      invariant(
        sha256Digest(card.contentDigest)
          && card.claims.length > 0
          && card.claims.every((claim) => (
            nonEmpty(claim.id)
            && nonEmpty(claim.statement)
            && nonEmpty(claim.evidenceLocator)
            && ['paraphrase', 'short_quote'].includes(claim.excerptMode)
            && nonEmpty(claim.evidenceExcerpt)
          )),
        'sealed source card requires contentDigest and located claims',
      );
    }
  }

  if (sealed) {
    invariant(bundle.manifest.state === 'sealed', 'sealed bundle requires sealed manifest');
    const digestKeys = Object.keys(bundle.manifest.fileDigests ?? {}).sort();
    invariant(
      JSON.stringify(digestKeys) === JSON.stringify([...DIGESTED_CASE_FILES].sort())
        && digestKeys.every((key) => sha256Digest(bundle.manifest.fileDigests[key])),
      'sealed manifest requires every file digest',
    );
  }
  return bundle;
}
```

`loadCaseBundle()` reads the eight exact filenames from a supplied directory and returns the shape
shown in section 2. It must not follow symlinks outside the experiment directory.

- [ ] **Step 5: Add the CLI and safe ignore rules**

`.gitignore`:

```gitignore
private/
runs/
*.local.json
```

`validate-packs.mjs` accepts `--sealed` and the four case directories, loads each bundle, prints only
`caseId`, state and pass/fail, and never prints source text or environment variables.

- [ ] **Step 6: Run GREEN verification**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/contracts.test.mjs
node .codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs --help
```

Expected:

```text
3 tests passed
usage: validate-packs.mjs [--sealed] cases/beauty-01 cases/product-01 cases/idol-01 cases/expert-01
```

- [ ] **Step 7: Review checkpoint**

Run `git -C .codex status --short`. Confirm only the validation document, this plan and the new
experiment workspace are listed. Do not stage or commit.

---

### Task 2: 네 case pack의 공개 source materialization

**Files:**

- Create the eight case files listed in section 1 under each of:
  - `.codex/experiments/shortform-director-quality-input/cases/beauty-01/`
  - `.codex/experiments/shortform-director-quality-input/cases/product-01/`
  - `.codex/experiments/shortform-director-quality-input/cases/idol-01/`
  - `.codex/experiments/shortform-director-quality-input/cases/expert-01/`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/seal-packs.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/seal-packs.test.mjs`

**Interfaces:**

- Consumes: approved protocol sections 3 and 4, public source pages only
- Produces: four sealed case bundles with `sha256:` file digests

- [ ] **Step 1: Create RED tests for case identity and exact source inventory**

The test must assert these source IDs:

```js
const EXPECTED_SOURCE_IDS = {
  'BEAUTY-01': ['B-S01', 'B-S02', 'B-S03'],
  'PRODUCT-01': ['P-S01', 'P-S02', 'P-S03', 'P-S04', 'P-S05'],
  'IDOL-01': ['I-S01', 'I-S02', 'I-S03', 'I-E01'],
  'EXPERT-01': ['E-S01', 'E-S02', 'E-S03'],
};
```

It must also assert 10 audience questions, 1~2 reference cards, `provider_not_called` Vira state
and `not_collected` feedback state per case.

- [ ] **Step 2: Run RED**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/seal-packs.test.mjs
```

Expected: FAIL because the case JSON files do not exist.

- [ ] **Step 3: Materialize profile and episode files**

Copy the four evaluation profiles and episode A·B questions exactly from approved protocol sections
4.1~4.4. Use these schema versions:

```json
{
  "profileSchemaVersion": "quality-input-profile.v1",
  "episodeSchemaVersion": "quality-input-episodes.v1"
}
```

Every profile must contain:

```text
caseId
operatorRole
audience
desiredAfterState
toneRules[]
prohibitedClaims[]
```

Every episodes file must contain:

```text
caseId
episodeA.id
episodeA.question
episodeB.id
episodeB.question
```

Use this exact ID map:

```js
const EPISODE_IDS = {
  'BEAUTY-01': ['BEAUTY-01-A', 'BEAUTY-01-B'],
  'PRODUCT-01': ['PRODUCT-01-A', 'PRODUCT-01-B'],
  'IDOL-01': ['IDOL-01-A', 'IDOL-01-B'],
  'EXPERT-01': ['EXPERT-01-A', 'EXPERT-01-B'],
};
```

- [ ] **Step 4: Materialize official and authority source cards**

Use only the following inventory.

| Case | ID | URL | Permitted use |
|---|---|---|---|
| BEAUTY-01 | `B-S01` | `https://romand.co.kr/product/detail.html?product_no=994` | product identity, option and official use fact |
| BEAUTY-01 | `B-S02` | `https://amusemakeup.com/product/%EC%A0%A4%ED%95%8F-%ED%8B%B4%ED%8A%B8-12%EC%A2%85-%ED%83%9D1/359` | product identity, option and official description |
| BEAUTY-01 | `B-S03` | `https://www.hince.co.kr/product/%EB%A1%9C-%EA%B8%80%EB%A1%9C%EC%9A%B0-%EC%A0%A4-%ED%8B%B4%ED%8A%B8/1112/` | volume, official use description and claim |
| PRODUCT-01 | `P-S01` | `https://smartcara.com/web/upload/download/SMARTCARA_2024_Brochure.pdf?v3=` | 2 L, method, official time range, features |
| PRODUCT-01 | `P-S02` | `https://smartcara.com/article/%EC%A0%9C%ED%92%88-%EB%A7%A4%EB%89%B4%EC%96%BC/5/46619/` | model, safe use, prohibited input, care |
| PRODUCT-01 | `P-S03` | `https://smartcara.com/article/%EA%B3%B5%EC%A7%80%EC%82%AC%ED%95%AD/1/46425/` | filter and container compatibility |
| PRODUCT-01 | `P-S04` | `https://www.seocho.go.kr/site/seocho/ex/bbs/View.do?bcIdx=409216&cbIdx=57` | dated local subsidy conditions |
| PRODUCT-01 | `P-S05` | `https://smartcara.com/article/%EC%9E%90%EC%A3%BC-%EB%AC%BB%EB%8A%94-%EC%A7%88%EB%AC%B8/6/46424/` | municipality-specific subsidy caveat |
| IDOL-01 | `I-S01` | `https://weverse.io/lesserafim/notice/34880` | official release and message |
| IDOL-01 | `I-S02` | `https://www.youtube.com/watch?v=a2grcJdfXmY` | official MV scene observations and timestamps |
| IDOL-01 | `I-S03` | `https://magazine.weverse.io/article/view/1874?artist=LE+SSERAFIM` | attributed artist statements |
| IDOL-01 | `I-E01` | `https://magazine.weverse.io/article/view/1881?artist=LE+SSERAFIM&lang=en` | editorial interpretation only |
| EXPERT-01 | `E-S01` | `https://www.bok.or.kr/portal/bbs/B0000217/view.do?menuNo=200144&nttId=10073634` | authority explanation |
| EXPERT-01 | `E-S02` | `https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/what-are` | 3%/4% example and interest-rate risk |
| EXPERT-01 | `E-S03` | `https://www.finra.org/investors/investing/investment-products/bonds` | pricing, inverse movement and duration |

Use these exact evidence classes:

```js
const SOURCE_CLASS_BY_ID = {
  'B-S01': 'official_fact',
  'B-S02': 'official_fact',
  'B-S03': 'official_fact',
  'P-S01': 'official_fact',
  'P-S02': 'official_fact',
  'P-S03': 'official_fact',
  'P-S04': 'official_fact',
  'P-S05': 'official_fact',
  'I-S01': 'official_fact',
  'I-S02': 'official_fact',
  'I-S03': 'official_fact',
  'I-E01': 'editorial_interpretation',
  'E-S01': 'authority_explanation',
  'E-S02': 'authority_explanation',
  'E-S03': 'authority_explanation',
};
```

For each card, record exactly:

```text
id
sourceClass
title
publisher
originalUrl
publishedAt
retrievedAt
cutoffAt
availability
permittedUse[]
claims[{id, statement, evidenceLocator, excerptMode, evidenceExcerpt}]
contentDigest
rightsNote
notes
```

`permittedUse` uses only `fact`, `audience`, `market`, `creative` or `editorial`; `I-E01` uses only
`editorial` and must never be cited as an official fact.

Rules:

- Use paraphrased claim text; keep any direct quote under 25 words per source.
- `excerptMode` is `paraphrase` or `short_quote`. `evidenceExcerpt` stores the smallest text needed
  to audit the claim and never stores a whole article, page or transcript.
- `evidenceLocator` is a PDF page, page heading, paragraph label or MV timestamp, not a search result
  line number.
- A source that cannot be version-confirmed gets `partial`; a source that cannot be opened gets
  `unavailable` and an empty `claims` array.
- Product review text never enters an official fact card.
- `I-E01` remains `editorial_interpretation`.
- `P-S04` always includes region, notice date and closed status in the same claim card.

- [ ] **Step 5: Materialize audience and reference cards**

Copy the 10 normalized questions for each case exactly from the approved protocol. Each question has:

```json
{
  "id": "B-AQ01",
  "question": "공식 색상표와 내 입술 위 발색이 다른 이유는 무엇인가?",
  "originClass": "general_reader_question",
  "sourceId": null,
  "evidenceLocator": null
}
```

When a public review or question directly supports an intent, switch only that item to
`originClass: "audience_observation"` and record a non-identifying locator. Do not store account
names, handles, profile URLs or verbatim comment text.

Use these reference IDs:

```js
const REFERENCE_IDS = {
  'BEAUTY-01': ['B-R01', 'B-R02'],
  'PRODUCT-01': ['P-R01'],
  'IDOL-01': ['I-R01'],
  'EXPERT-01': ['E-R01'],
};
```

Use this exact reference inventory:

| ID | Source | Pattern only |
|---|---|---|
| `B-R01` | `https://lululandtvblog.blogspot.com/2022/04/romand-blur-fudge-tint-910-11-swatches.html` | fixed comparison order and condition grid |
| `B-R02` | `https://www.janelku.com/2024/09/makeup-staples-rom-juicy-lip-tint-and.html` | disclose lip condition before product observations |
| `P-R01` | `P-S01` brochure layout | two-model comparison table and pre-purchase checklist |
| `I-R01` | `I-S02` official MV | timestamp → official statement → labeled interpretation |
| `E-R01` | `https://www.khanacademy.org/v/relationship-between-bond-prices-and-interest-rates?playlist=Finance` | one-number-at-a-time whiteboard explanation |

Each reference card contains `pattern`, `allowedInfluence`, `forbiddenUse` and `rightsNote`.
`allowedInfluence` permits structure, pacing and explanation order only. `forbiddenUse` rejects
copying wording, product facts, frames, images or brand identity. It contains no new product or
market fact.

- [ ] **Step 6: Implement pack sealing**

`seal-packs.mjs` must:

1. load the seven axis files,
2. validate their unsealed form,
3. calculate each source card’s `contentDigest` from
   `{id,title,publisher,originalUrl,publishedAt,retrievedAt,claims,rightsNote}`,
4. atomically rewrite `source-cards.json` with those calculated digests,
5. calculate `sha256Json()` for each of the seven finalized axis files,
6. write `manifest.json` through a temporary sibling file and atomic rename,
7. set `manifest.state` to `sealed`,
8. re-run `validateCaseBundle(bundle, { sealed: true })`.

Before sealing, use this exact manifest shape:

```json
{
  "schemaVersion": "quality-input-pack-manifest.v1",
  "caseId": "BEAUTY-01",
  "cutoffAt": "2026-07-24T23:59:59+09:00",
  "state": "materializing",
  "fileDigests": {
    "profile.json": null,
    "episodes.json": null,
    "source-cards.json": null,
    "audience-cards.json": null,
    "reference-cards.json": null,
    "vira-evidence.json": null,
    "feedback-cards.json": null
  }
}
```

The sealing result replaces every null with `sha256:` followed by 64 lowercase hexadecimal
characters. The validator rejects null, truncated and non-hex digest values when state is `sealed`.

- [ ] **Step 7: Verify four sealed packs**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/seal-packs.test.mjs
node .codex/experiments/shortform-director-quality-input/scripts/seal-packs.mjs
node .codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs --sealed
```

Expected: all tests pass and all four case IDs report `sealed valid`. No provider or Vira access
occurs in this task.

- [ ] **Step 8: Record materialization burden**

Write gitignored `private/materialization-metrics.json` with actual elapsed minutes:

```json
{
  "schemaVersion": "quality-input-materialization-metrics.v1",
  "state": "collecting",
  "cases": {
    "BEAUTY-01": {
      "profileMinutes": null,
      "sourceMinutes": null,
      "audienceMinutes": null,
      "retrievalFailures": []
    },
    "PRODUCT-01": {
      "profileMinutes": null,
      "sourceMinutes": null,
      "audienceMinutes": null,
      "retrievalFailures": []
    },
    "IDOL-01": {
      "profileMinutes": null,
      "sourceMinutes": null,
      "audienceMinutes": null,
      "retrievalFailures": []
    },
    "EXPERT-01": {
      "profileMinutes": null,
      "sourceMinutes": null,
      "audienceMinutes": null,
      "retrievalFailures": []
    }
  }
}
```

Set `state` to `complete` and replace every null with the measured non-negative number before
leaving Task 2; do not estimate unobserved time. Keep `retrievalFailures` as exact source IDs and
error classes without response bodies.

- [ ] **Step 9: Review checkpoint**

Inspect source class, rights note and locator fields manually. Do not stage or commit.

---

### Task 3: Vira read-only snapshot export와 normalization

> **2026-07-24 상태:** Step 1~6 offline fixture work만 완료했다. Step 7에서 현재 DB가
> 대표 corpus가 아니라는 전제가 확인돼 Step 8~9는 취소했다. 아래 live 명령은 실행
> 기록과 기존 설계 보존을 위한 것이며 다음 세션에서 실행하지 않는다.

**Files:**

- Create:
  `.codex/experiments/shortform-director-quality-input/vira/export-readonly.sql`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/export-vira-readonly.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/lib/vira-normalizer.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/normalize-vira-export.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/vira-export-command.test.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/vira-normalizer.test.mjs`
- Test fixtures:
  - `.codex/experiments/shortform-director-quality-input/tests/fixtures/vira-export-sufficient.json`
  - `.codex/experiments/shortform-director-quality-input/tests/fixtures/vira-export-empty.json`
- Modify after approved read:
  - each case `vira-evidence.json`
  - each case `manifest.json`

**Interfaces:**

- Consumes: read-only JSON result from current Vira `shorts_*` tables
- Produces:
  `buildPsqlInvocation({ databaseUrl, sqlFile, baseEnv }): object`,
  `normalizeViraExport(raw, { materializedAt, codeRevision }): Map<caseId, ViraPack>`

- [ ] **Step 1: Write RED tests**

Test these behaviors:

```js
test('keeps at most three market and two growth records per case', () => {
  const result = normalizeViraExport(sufficientFixture, {
    materializedAt: '2026-07-24T12:00:00.000Z',
    codeRevision: '2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4',
  });
  assert.equal(result.get('BEAUTY-01').evidence.length, 5);
});

test('does not invent evidence when a topic has no rows', () => {
  const result = normalizeViraExport(emptyFixture, {
    materializedAt: '2026-07-24T12:00:00.000Z',
    codeRevision: '2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4',
  });
  assert.deepEqual(result.get('EXPERT-01'), {
    schemaVersion: 'quality-input-vira-pack.v1',
    caseId: 'EXPERT-01',
    state: 'insufficient',
    evidence: [],
  });
});

test('never carries comment author or text fields', () => {
  const serialized = JSON.stringify(normalizeViraExport(sufficientFixture, {
    materializedAt: '2026-07-24T12:00:00.000Z',
    codeRevision: '2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4',
  }));
  assert.doesNotMatch(serialized, /author|commentText/);
});

test('keeps the database URL and password out of psql arguments', () => {
  const result = buildPsqlInvocation({
    databaseUrl: 'postgresql://reader:secret-value@db.example:5432/vira?sslmode=require',
    sqlFile: '/absolute/export-readonly.sql',
  });
  assert.doesNotMatch(JSON.stringify(result.args), /secret-value|postgresql:/);
  assert.equal(result.env.PGUSER, 'reader');
  assert.equal(result.env.PGPASSWORD, 'secret-value');
  assert.equal(result.env.PGSSLMODE, 'require');
});
```

- [ ] **Step 2: Run RED**

Run:

```bash
node --test \
  .codex/experiments/shortform-director-quality-input/tests/vira-export-command.test.mjs \
  .codex/experiments/shortform-director-quality-input/tests/vira-normalizer.test.mjs
```

Expected: FAIL because the export wrapper and `vira-normalizer.mjs` do not exist.

- [ ] **Step 3: Add the read-only SQL**

The SQL must start and end with:

```sql
BEGIN TRANSACTION READ ONLY;

WITH case_terms(case_id, term) AS (
  VALUES
    ('BEAUTY-01', '메이크업'),
    ('BEAUTY-01', '립'),
    ('BEAUTY-01', '틴트'),
    ('BEAUTY-01', '젤광'),
    ('PRODUCT-01', '음식물처리기'),
    ('PRODUCT-01', '자취'),
    ('PRODUCT-01', '꿀템'),
    ('IDOL-01', '르세라핌'),
    ('IDOL-01', 'LE SSERAFIM'),
    ('IDOL-01', 'CELEBRATION'),
    ('EXPERT-01', '재테크'),
    ('EXPERT-01', '채권')
),
matched AS (
  SELECT DISTINCT ON (ct.case_id, v.id)
    ct.case_id,
    v.id AS row_id,
    v.platform_video_id,
    v.title,
    v.channel,
    v.keyword,
    v.naver_category,
    v.tags,
    v.discovery_views,
    v.upload_date
  FROM case_terms ct
  JOIN shorts_videos v
    ON lower(concat_ws(' ', v.title, v.description, v.keyword, v.tags::text))
       LIKE '%' || lower(ct.term) || '%'
  WHERE v.discovered_at < TIMESTAMPTZ '2026-07-25 00:00:00+09:00'
    AND (v.upload_date IS NULL OR v.upload_date <= DATE '2026-07-24')
  ORDER BY ct.case_id, v.id, length(ct.term) DESC
),
ranked_snapshots AS (
  SELECT
    s.video_id,
    s.snapshot_date,
    s.view_count,
    s.like_count,
    s.comment_count,
    row_number() OVER (
      PARTITION BY s.video_id ORDER BY s.snapshot_date DESC
    ) AS rn
  FROM shorts_snapshots s
  WHERE s.snapshot_date <= DATE '2026-07-24'
),
latest_snapshot AS (
  SELECT *
  FROM ranked_snapshots
  WHERE rn = 1
),
sentiment AS (
  SELECT
    video_id,
    count(*) FILTER (WHERE label = '긍정')::int AS positive,
    count(*) FILTER (WHERE label = '부정')::int AS negative,
    count(*) FILTER (WHERE label = '중립')::int AS neutral,
    count(*) FILTER (WHERE label IS NOT NULL)::int AS classified
  FROM comment_sentiments
  WHERE EXISTS (
    SELECT 1
    FROM shorts_comments c
    WHERE c.video_id = comment_sentiments.video_id
      AND c.comment_id = comment_sentiments.comment_id
      AND c.snapshot_date <= DATE '2026-07-24'
  )
  GROUP BY video_id
),
market_ranked AS (
  SELECT
    m.*,
    ls.snapshot_date,
    ls.view_count,
    ls.like_count,
    ls.comment_count,
    se.positive,
    se.negative,
    se.neutral,
    se.classified,
    row_number() OVER (
      PARTITION BY m.case_id
      ORDER BY coalesce(ls.view_count, m.discovery_views) DESC NULLS LAST,
               m.platform_video_id
    ) AS case_rank
  FROM matched m
  LEFT JOIN latest_snapshot ls ON ls.video_id = m.row_id
  LEFT JOIN sentiment se ON se.video_id = m.row_id
),
last_three AS (
  SELECT
    video_id,
    max(view_count) FILTER (WHERE rn = 1) AS view_new,
    max(snapshot_date) FILTER (WHERE rn = 1) AS date_new,
    max(view_count) FILTER (WHERE rn = 3) AS view_old,
    max(snapshot_date) FILTER (WHERE rn = 3) AS date_old,
    count(*) FILTER (WHERE rn <= 3) AS snapshot_count
  FROM ranked_snapshots
  WHERE rn <= 3
  GROUP BY video_id
  HAVING count(*) FILTER (WHERE rn <= 3) >= 3
),
growth_base AS (
  SELECT
    v.id AS row_id,
    v.platform_video_id,
    (DATE '2026-07-24' - v.upload_date)::int AS age_days,
    CASE
      WHEN DATE '2026-07-24' - v.upload_date <= 7 THEN '0-7'
      WHEN DATE '2026-07-24' - v.upload_date <= 30 THEN '8-30'
      WHEN DATE '2026-07-24' - v.upload_date <= 90 THEN '31-90'
      WHEN DATE '2026-07-24' - v.upload_date <= 365 THEN '91-365'
      ELSE '365+'
    END AS age_bucket,
    l.date_old,
    l.date_new,
    round(
      (l.view_new - l.view_old)::numeric
      / nullif(l.date_new - l.date_old, 0)
    )::double precision AS daily_view_delta
  FROM last_three l
  JOIN shorts_videos v ON v.id = l.video_id
  WHERE l.view_old IS NOT NULL
    AND v.discovered_at < TIMESTAMPTZ '2026-07-25 00:00:00+09:00'
    AND v.upload_date IS NOT NULL
    AND v.upload_date <= DATE '2026-07-24'
),
growth_scored AS (
  SELECT
    gb.*,
    round(
      percent_rank() OVER (
        PARTITION BY gb.age_bucket ORDER BY gb.daily_view_delta
      ) * 100
    )::int AS percentile,
    count(*) OVER (PARTITION BY gb.age_bucket)::int AS peer_sample_size
  FROM growth_base gb
  WHERE gb.daily_view_delta IS NOT NULL
),
growth_ranked AS (
  SELECT
    m.case_id,
    m.row_id,
    m.platform_video_id,
    m.keyword,
    m.naver_category,
    gs.date_old,
    gs.date_new,
    gs.daily_view_delta,
    gs.age_days,
    gs.age_bucket,
    gs.percentile,
    gs.peer_sample_size,
    row_number() OVER (
      PARTITION BY m.case_id
      ORDER BY gs.percentile DESC, gs.daily_view_delta DESC,
               m.platform_video_id
    ) AS case_rank
  FROM matched m
  JOIN growth_scored gs ON gs.row_id = m.row_id
)
SELECT jsonb_build_object(
  'market',
  coalesce((
    SELECT jsonb_agg(jsonb_build_object(
      'caseId', mr.case_id,
      'rowId', mr.row_id,
      'platformVideoId', mr.platform_video_id,
      'title', mr.title,
      'channel', mr.channel,
      'keyword', mr.keyword,
      'category', mr.naver_category,
      'tags', coalesce(mr.tags, '[]'::jsonb),
      'snapshotDate', mr.snapshot_date,
      'views', coalesce(mr.view_count, mr.discovery_views),
      'viewsSource', CASE WHEN mr.view_count IS NULL THEN 'discovery' ELSE 'snapshot' END,
      'likes', mr.like_count,
      'comments', mr.comment_count,
      'positive', coalesce(mr.positive, 0),
      'negative', coalesce(mr.negative, 0),
      'neutral', coalesce(mr.neutral, 0),
      'classified', coalesce(mr.classified, 0)
    ) ORDER BY mr.case_id, mr.case_rank)
    FROM market_ranked mr
    WHERE mr.case_rank <= 3
  ), '[]'::jsonb),
  'growth',
  coalesce((
    SELECT jsonb_agg(jsonb_build_object(
      'caseId', gr.case_id,
      'rowId', gr.row_id,
      'platformVideoId', gr.platform_video_id,
      'keyword', gr.keyword,
      'category', gr.naver_category,
      'snapshotFrom', gr.date_old,
      'snapshotTo', gr.date_new,
      'snapshotCount', 3,
      'dailyViewDelta', gr.daily_view_delta,
      'ageDays', gr.age_days,
      'ageBucket', gr.age_bucket,
      'percentile', gr.percentile,
      'peerSampleSize', gr.peer_sample_size,
      'risingThreshold', 90,
      'isRising', gr.percentile >= 90,
      'isNewRising', gr.percentile >= 90 AND gr.age_days <= 7
    ) ORDER BY gr.case_id, gr.case_rank)
    FROM growth_ranked gr
    WHERE gr.case_rank <= 2
  ), '[]'::jsonb)
);

ROLLBACK;
```

The query selects counts and aggregate sentiment only. It must not select `shorts_comments.text`,
`shorts_comments.author`, credentials or analysis provider output.

- [ ] **Step 4: Implement the secret-safe psql wrapper**

The wrapper reads `DATABASE_URL` from its own environment, converts it to libpq environment
variables and never places the URL or password in child arguments.

```js
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, rename, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const PSQL = '/opt/homebrew/opt/postgresql@15/bin/psql';
const ROOT = resolve('.codex/experiments/shortform-director-quality-input');

export function buildPsqlInvocation({ databaseUrl, sqlFile, baseEnv = process.env }) {
  if (!databaseUrl) throw new Error('DATABASE_URL is required');
  const parsed = new URL(databaseUrl);
  const childEnv = { ...baseEnv };
  delete childEnv.DATABASE_URL;
  delete childEnv.PGSERVICE;
  delete childEnv.PGSERVICEFILE;
  delete childEnv.PGSSLMODE;
  childEnv.PGHOST = parsed.hostname;
  childEnv.PGPORT = parsed.port || '5432';
  childEnv.PGDATABASE = decodeURIComponent(parsed.pathname.slice(1));
  childEnv.PGUSER = decodeURIComponent(parsed.username);
  childEnv.PGPASSWORD = decodeURIComponent(parsed.password);
  const sslMode = parsed.searchParams.get('sslmode');
  if (sslMode) childEnv.PGSSLMODE = sslMode;
  return {
    command: PSQL,
    args: [
      '--no-psqlrc',
      '--set=ON_ERROR_STOP=1',
      '--quiet',
      '--tuples-only',
      '--no-align',
      `--file=${sqlFile}`,
    ],
    env: childEnv,
  };
}

export async function exportViraReadonly({ databaseUrl, sqlFile, outputFile }) {
  const invocation = buildPsqlInvocation({ databaseUrl, sqlFile });
  const stdout = await new Promise((resolve, reject) => {
    const child = spawn(invocation.command, invocation.args, {
      env: invocation.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    let err = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => { out += chunk; });
    child.stderr.on('data', (chunk) => { err += chunk; });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(`read-only psql failed with exit ${code}: ${err.trim()}`));
    });
  });
  JSON.parse(stdout);
  await mkdir(dirname(outputFile), { recursive: true });
  const temporary = `${outputFile}.tmp`;
  await writeFile(temporary, `${stdout}\n`, { mode: 0o600 });
  await rename(temporary, outputFile);
  return `sha256:${createHash('sha256').update(stdout).digest('hex')}`;
}

if (process.argv[1]
  && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const digest = await exportViraReadonly({
    databaseUrl: process.env.DATABASE_URL,
    sqlFile: resolve(ROOT, 'vira/export-readonly.sql'),
    outputFile: resolve(ROOT, 'private/vira-export.raw.json'),
  });
  process.stdout.write(`Vira read-only export saved ${digest}\n`);
}
```

The CLI uses the fixed SQL and output paths declared in this task. On success it prints only
`Vira read-only export saved` and the SHA-256 digest, never row content.

- [ ] **Step 5: Implement normalization**

For every case:

- map up to three `market` rows to `market.video-observation`,
- map up to two `growth` rows to `market.peer-growth`,
- preserve `rowId` only as `recordRefs`,
- set `codeRevision` to the pinned full Vira SHA,
- use `sufficient` for 3 market rows or 2 growth rows,
- use `partial` for a non-zero smaller set,
- use `insufficient` and an empty evidence array when neither kind exists,
- never synthesize a legacy or `analysis.video-8d` record.

Use this mapping:

```js
const CASE_IDS = ['BEAUTY-01', 'PRODUCT-01', 'IDOL-01', 'EXPERT-01'];

function marketEnvelope(row, { materializedAt, codeRevision, state, sampleSize }) {
  const views = Number.isFinite(row.views) ? Number(row.views) : undefined;
  const likes = Number.isFinite(row.likes) ? Number(row.likes) : undefined;
  const comments = Number.isFinite(row.comments) ? Number(row.comments) : undefined;
  const engagementRate = views > 0 && likes !== undefined && comments !== undefined
    ? Math.min(1, (likes + comments) / views)
    : undefined;
  const observation = { materializedAt, state, sampleSize };
  if (row.snapshotDate) {
    observation.window = {
      from: String(row.snapshotDate),
      to: String(row.snapshotDate),
    };
  }
  const payload = {
    title: row.title,
    channel: row.channel,
    keyword: row.keyword,
    naverCategory: row.category,
    tags: Array.isArray(row.tags) ? row.tags.slice(0, 5) : [],
    metrics: {
      snapshotDate: row.snapshotDate ?? undefined,
      views,
      viewsSource: row.viewsSource,
      likes,
      comments,
      engagementRate,
    },
  };
  if (Number(row.classified) > 0) {
    payload.commentSentiment = {
      positive: Number(row.positive ?? 0),
      negative: Number(row.negative ?? 0),
      neutral: Number(row.neutral ?? 0),
      classified: Number(row.classified),
    };
  }
  return {
    schemaVersion: 'vira-evidence.v1',
    id: `evidence.market.${row.caseId.toLowerCase()}.${row.platformVideoId}`,
    kind: 'market.video-observation',
    evidenceClass: 'observed',
    source: {
      system: 'vira',
      surface: 'shorts-market',
      lifecycle: 'active',
      codeRevision,
      recordRefs: [{ kind: 'shorts-video', id: row.rowId }],
    },
    subject: {
      platform: 'youtube_shorts',
      platformVideoId: row.platformVideoId,
      keyword: row.keyword,
      category: row.category ?? undefined,
    },
    observation,
    method: {
      id: 'shorts-market-cutoff-observation',
      version: '1',
      parameters: { cutoffDate: '2026-07-24' },
    },
    payload,
  };
}

function growthEnvelope(row, { materializedAt, codeRevision, state }) {
  return {
    schemaVersion: 'vira-evidence.v1',
    id: `evidence.growth.${row.caseId.toLowerCase()}.${row.platformVideoId}`,
    kind: 'market.peer-growth',
    evidenceClass: 'derived',
    source: {
      system: 'vira',
      surface: 'shorts-growth-lab',
      lifecycle: 'lab',
      codeRevision,
      recordRefs: [{ kind: 'shorts-video', id: row.rowId }],
    },
    subject: {
      platform: 'youtube_shorts',
      platformVideoId: row.platformVideoId,
      keyword: row.keyword,
      category: row.category ?? undefined,
    },
    observation: {
      materializedAt,
      state,
      sampleSize: Number(row.peerSampleSize),
      window: {
        from: String(row.snapshotFrom),
        to: String(row.snapshotTo),
      },
    },
    method: {
      id: 'last3-endpoint-daily-delta-age-bucket-percentile',
      version: '1',
      parameters: {
        snapshotCount: 3,
        risingThreshold: 90,
        cutoffDate: '2026-07-24',
      },
    },
    payload: {
      snapshotFrom: String(row.snapshotFrom),
      snapshotTo: String(row.snapshotTo),
      snapshotCount: 3,
      dailyViewDelta: Number(row.dailyViewDelta),
      ageDays: Number(row.ageDays),
      ageBucket: row.ageBucket,
      percentile: Number(row.percentile),
      risingThreshold: 90,
      isRising: row.isRising === true,
      isNewRising: row.isNewRising === true,
    },
  };
}

export function normalizeViraExport(raw, context) {
  const result = new Map();
  for (const caseId of CASE_IDS) {
    const marketRows = raw.market.filter((row) => row.caseId === caseId).slice(0, 3);
    const growthRows = raw.growth.filter((row) => row.caseId === caseId).slice(0, 2);
    const marketState = marketRows.length >= 3
      ? 'sufficient'
      : marketRows.length > 0 ? 'partial' : 'insufficient';
    const growthState = growthRows.length >= 2
      ? 'sufficient'
      : growthRows.length > 0 ? 'partial' : 'insufficient';
    const evidence = [
      ...marketRows.map((row) => marketEnvelope(row, {
        ...context,
        state: marketState,
        sampleSize: marketRows.length,
      })),
      ...growthRows.map((row) => growthEnvelope(row, {
        ...context,
        state: growthState,
      })),
    ];
    result.set(caseId, {
      schemaVersion: 'quality-input-vira-pack.v1',
      caseId,
      state: evidence.length === 0
        ? 'insufficient'
        : marketState === 'sufficient' || growthState === 'sufficient'
          ? 'sufficient'
          : 'partial',
      evidence,
    });
  }
  return result;
}
```

`normalize-vira-export.mjs` writes only the four normalized `vira-evidence.json` files. It must first
copy the previous files into the gitignored `private/pre-vira-normalization/` directory, then reseal
the pack manifests.

- [ ] **Step 6: Run fixture tests**

Run:

```bash
node --test \
  .codex/experiments/shortform-director-quality-input/tests/vira-export-command.test.mjs \
  .codex/experiments/shortform-director-quality-input/tests/vira-normalizer.test.mjs
```

Expected: all tests pass without a DB connection.

- [ ] **Step 7: Stop and notify before the actual Vira read**

Report:

```text
Vira read-only query 준비 완료
- 감사 기준 revision: 2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4
- 실제 checkout revision: preflight에서 다시 읽은 full SHA
- 대상: shorts_videos, shorts_snapshots, comment_sentiments
- 쓰기: 없음, BEGIN TRANSACTION READ ONLY + ROLLBACK
- 댓글 본문/작성자: 조회하지 않음
- 출력: .codex/experiments/shortform-director-quality-input/private/vira-export.raw.json
```

If the two revisions differ, stop before the DB command. Report the exact mismatch and ask the user
to choose between a separate current-revision re-audit and an explicitly authorized baseline
strategy; do not choose, reset, checkout or create a Vira worktree. Even after revision
reconciliation, do not run the next command until the user explicitly allows this read.

- [ ] **Step 8: Execute the approved read-only export**

From `/Users/jina/project/adlight`, with `DATABASE_URL` already available in the process
environment:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/export-vira-readonly.mjs
```

Expected: exit 0. Do not print `DATABASE_URL` or raw output.

- [ ] **Step 9: Normalize, seal and validate**

Run:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/normalize-vira-export.mjs \
  .codex/experiments/shortform-director-quality-input/private/vira-export.raw.json
node .codex/experiments/shortform-director-quality-input/scripts/seal-packs.mjs
node .codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs --sealed
```

Expected: four valid packs. A case with no matching records reports `insufficient`, not a fabricated
score.

---

### Task 4: Condition compiler와 축 누출 방지

**Files:**

- Create:
  `.codex/experiments/shortform-director-quality-input/lib/condition-compiler.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/condition-compiler.test.mjs`

**Interfaces:**

- Consumes: sealed `CaseBundle`
- Produces:
  `compileCondition(bundle, { episode, condition, track, runId, sampleId }): ConditionPackage`
  and a private run manifest

- [ ] **Step 1: Write RED tests for the exact ladder**

```js
const EXPECTED_AXES = {
  C0: [],
  C1: ['P'],
  C2: ['P', 'S'],
  C3: ['P', 'S', 'A'],
  C4: ['P', 'S', 'A', 'V'],
  C5: ['P', 'S', 'A', 'V', 'R'],
  C6: ['P', 'S', 'A', 'V', 'R', 'F'],
  'B-NO-F': ['P', 'S', 'A', 'V', 'R'],
  'FULL-P': ['S', 'A', 'V', 'R'],
  'FULL-S': ['P', 'A', 'V', 'R'],
  'FULL-A': ['P', 'S', 'V', 'R'],
  'FULL-V': ['P', 'S', 'A', 'R'],
  'FULL-R': ['P', 'S', 'A', 'V'],
};
```

Tests must prove:

- C0 contains only episode intent and `evidenceState: "none_available"`.
- C2 contains source claims but no audience, Vira or reference pattern.
- C3 adds audience questions without source review text.
- C4 adds only normalized Vira envelopes.
- C4 and C5 reject `vira.state === "provider_not_called"`.
- C5 adds pattern descriptions without new fact claims.
- C6 refuses episode A.
- C6 refuses `feedback.state !== "ready"`.
- `B-NO-F` contains episode B and no feedback.
- every package digest changes when one included axis changes.
- equal inputs in different sample runs keep the same `inputDigest` but receive different package IDs.

- [ ] **Step 2: Run RED**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/condition-compiler.test.mjs
```

Expected: FAIL because the compiler does not exist.

- [ ] **Step 3: Implement the compiler**

Use one inclusion map and no condition-specific duplicate builders:

```js
import { sha256Json } from './canonical-json.mjs';

export const CONDITION_AXES = Object.freeze({
  C0: [],
  C1: ['P'],
  C2: ['P', 'S'],
  C3: ['P', 'S', 'A'],
  C4: ['P', 'S', 'A', 'V'],
  C5: ['P', 'S', 'A', 'V', 'R'],
  C6: ['P', 'S', 'A', 'V', 'R', 'F'],
  'B-NO-F': ['P', 'S', 'A', 'V', 'R'],
  'FULL-P': ['S', 'A', 'V', 'R'],
  'FULL-S': ['P', 'A', 'V', 'R'],
  'FULL-A': ['P', 'S', 'V', 'R'],
  'FULL-V': ['P', 'S', 'A', 'R'],
  'FULL-R': ['P', 'S', 'A', 'V'],
});

export function compileCondition(
  bundle,
  { episode, condition, track, runId, sampleId = null },
) {
  if (typeof runId !== 'string' || runId.trim() === '') {
    throw new Error('runId is required');
  }
  const axes = CONDITION_AXES[condition];
  if (!axes) throw new Error(`unknown condition: ${condition}`);
  if (condition === 'C6' && episode !== 'B') {
    throw new Error('C6 is valid only for episode B');
  }
  if (condition === 'C6' && bundle.feedback.state !== 'ready') {
    throw new Error('C6 requires ready feedback cards');
  }
  if (axes.includes('V') && bundle.vira.state === 'provider_not_called') {
    throw new Error('Vira axis requires a materialized or explicit insufficient state');
  }

  const intent = episode === 'A'
    ? bundle.episodes.episodeA
    : bundle.episodes.episodeB;
  const input = {
    episodeIntent: intent,
    evidenceState: axes.includes('S') ? 'provided' : 'none_available',
  };
  if (axes.includes('P')) input.profile = bundle.profile;
  if (axes.includes('S')) input.sourceClaims = bundle.sources.cards;
  if (axes.includes('A')) input.audienceQuestions = bundle.audience.questions;
  if (axes.includes('V')) input.viraEvidence = bundle.vira;
  if (axes.includes('R')) input.creativePatterns = bundle.references.cards;
  if (axes.includes('F')) input.feedbackCards = bundle.feedback.cards;

  const id = [
    runId.toLowerCase(),
    ...(sampleId ? [sampleId.toLowerCase()] : []),
    bundle.manifest.caseId.toLowerCase(),
    episode.toLowerCase(),
    condition.toLowerCase(),
    track.toLowerCase(),
  ].join('.');
  return {
    schemaVersion: 'quality-input-condition.v1',
    id,
    caseId: bundle.manifest.caseId,
    episode,
    condition,
    axes,
    track,
    runId,
    sampleId,
    input,
    inputDigest: sha256Json(input),
  };
}
```

- [ ] **Step 4: Implement phase-aware run compilation**

`compile-run.mjs` supports:

```text
--phase ladder-a
--phase feedback-b
--phase ablation
--run-id quality-input-2026-07-24-ladder-a
--sample-id s1
--pricing-snapshot runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json
```

- `ladder-a`: four cases × C0~C5 × D/E = 48 packages
- `feedback-b`: four cases × (`B-NO-F`, C6) × D/E = 16 packages
- `ablation`: selection file의 각 pair에 대해 `withAxisCondition`과
  `withoutAxisCondition`을 모두 D/E로 생성

It rejects a missing `--run-id` and writes packages plus `run-manifest.json` under a directory named
by that value, for example `runs/quality-input-2026-07-24-ladder-a/prepared/`. It refuses to
overwrite an existing run directory. Task 5 Steps 1~6 and Task 7 Steps 1~5 are prerequisites:
compilation refuses missing generation prompt/schema files or evaluation rubric/schema files.

The manifest records:

```js
{
  schemaVersion: 'quality-input-run-manifest.v1',
  runId,
  sampleId,
  phase,
  createdAt,
  caseManifestDigests,
  provider: {
    name: 'openai',
    api: 'responses',
    endpointHost: 'api.openai.com',
    model: 'gpt-4.1',
    store: false,
  },
  sampling: {
    temperature: 0.2,
    seedMode: 'unsupported_not_sent',
    maxOutputTokens: 4000,
  },
  generation: {
    language: 'ko',
    targetDurationSec: 45,
    promptDigests: { D: discoveryPromptDigest, E: elaborationPromptDigest },
    schemaDigests: { D: discoverySchemaDigest, E: elaborationSchemaDigest },
  },
  evaluation: {
    rubricDigest,
    scoreSchemaDigest,
    evaluatorCount: 2,
    passes: ['creative', 'evidence'],
  },
  conditionCount,
  pricingSnapshotDigest: null,
  liveApproved: false,
  providerCalls: 0,
  failures: [],
  retries: [],
}
```

`createdAt` is UTC. All digests are calculated from the frozen local files. No automatic retry is
performed; if an operator later performs an explicitly authorized retry, the original failure and
new attempt are both appended rather than replaced.

`--sample-id` is required for `ablation`, forbidden for the two initial phases and recorded in both
the package and run manifest. It makes repeated-sample artifact IDs unique without changing the
underlying `inputDigest`.

When `--pricing-snapshot` is supplied, the compiler validates `state: "ready"`, model equality and
numeric non-negative rates, then copies the snapshot into the new run directory and records its
digest. It never edits the original pricing file.

- [ ] **Step 5: Run GREEN and compile the non-feedback phase**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/condition-compiler.test.mjs
node .codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs \
  --phase ladder-a \
  --run-id quality-input-2026-07-24-ladder-a
```

Expected: tests pass and the latest manifest reports exactly 48 prepared packages and zero provider
calls.

- [ ] **Step 6: Review checkpoint**

Open one case’s C0, C2, C4 and C5 prepared JSON. Confirm axis-only differences and no provider output.

---

### Task 5: Generation contract와 provider dry-run/live runner

**Files:**

- Create:
  `.codex/experiments/shortform-director-quality-input/lib/generation-contracts.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/lib/provider-runner.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/prompts/discovery.instructions.md`
- Create:
  `.codex/experiments/shortform-director-quality-input/prompts/elaboration.instructions.md`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/provider-runner.test.mjs`

**Interfaces:**

- Consumes: prepared `ConditionPackage`
- Produces:
  `buildProviderRequest(package, { instructions, schema }): object`,
  `parseProviderResponse(value, package, elapsedMs, pricing): ProviderOutput`,
  `runProviderRequest(package, options): Promise<ProviderOutput>`

Task 5 Steps 1~6 create the frozen generation contract before Task 4 compiles any run. Step 7
resumes only after compilation.

- [ ] **Step 1: Write RED tests for network safety**

Tests must verify:

```js
const requestOptions = {
  instructions: 'Return the supplied strict JSON shape.',
  schema: {
    type: 'object',
    properties: {},
    required: [],
    additionalProperties: false,
  },
};

test('dry-run never calls fetch', async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls += 1;
    throw new Error('network must not be called');
  };
  const result = await runProviderRequest(condition, {
    live: false,
    fetchImpl,
    apiKey: null,
    ...requestOptions,
  });
  assert.equal(result.mode, 'dry-run');
  assert.equal(calls, 0);
});

test('live mode requires the explicit environment gate', async () => {
  await assert.rejects(
    runProviderRequest(condition, {
      live: true,
      liveApproved: false,
      apiKey: 'not-a-real-key',
      fetchImpl: async () => new Response('{}'),
      ...requestOptions,
    }),
    /live provider call is not approved/,
  );
});

test('request disables provider storage and freezes the model', () => {
  const request = buildProviderRequest(condition, requestOptions);
  assert.equal(request.model, 'gpt-4.1');
  assert.equal(request.store, false);
  assert.equal(request.temperature, 0.2);
  assert.equal(request.max_output_tokens, 4000);
});

test('rejects a provider output that invents an evidence id', () => {
  assert.throws(
    () => validateEvidenceReferences({
      opportunities: [{
        evidenceIds: ['invented-evidence'],
      }],
    }, condition),
    /unknown evidence id: invented-evidence/,
  );
});
```

- [ ] **Step 2: Run RED**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/provider-runner.test.mjs
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Define strict Track D and Track E schemas**

`DISCOVERY_OUTPUT_SCHEMA` requires exactly three opportunities. Each has:

```text
id
thesis
audienceTension
hook
payoff
evidenceIds[]
visualProofIdea
unsupportedClaims[]
```

`ELABORATION_OUTPUT_SCHEMA` requires:

```text
directorBrief{
  episodeQuestion, thesis, audienceState, desiredAfterState, hook, payoff,
  evidenceIds[], uncertaintyNotes[], rightsNotes[], safetyNotes[]
}
script{targetDurationSec:45, narration}
beats[5..7]{
  order, role, narration, claim, evidenceIds[],
  visualIntent, assetIntent, fallback
}
```

Both schemas set `additionalProperties: false`. When a condition has
`evidenceState: "none_available"`, evidence arrays must be empty and unsupported factual needs must
go into `unsupportedClaims` or `uncertaintyNotes`.

Tests also reject a changed `directorBrief.episodeQuestion`, duplicate Track D opportunity IDs and a
Track E beat order other than contiguous `0..n-1`.

Build both schemas from these exact reusable definitions:

```js
const NON_EMPTY_STRING = { type: 'string', minLength: 1 };
const STRING_ARRAY = {
  type: 'array',
  items: NON_EMPTY_STRING,
};

const OPPORTUNITY_SCHEMA = {
  type: 'object',
  properties: {
    id: NON_EMPTY_STRING,
    thesis: NON_EMPTY_STRING,
    audienceTension: NON_EMPTY_STRING,
    hook: NON_EMPTY_STRING,
    payoff: NON_EMPTY_STRING,
    evidenceIds: STRING_ARRAY,
    visualProofIdea: NON_EMPTY_STRING,
    unsupportedClaims: STRING_ARRAY,
  },
  required: [
    'id',
    'thesis',
    'audienceTension',
    'hook',
    'payoff',
    'evidenceIds',
    'visualProofIdea',
    'unsupportedClaims',
  ],
  additionalProperties: false,
};

export const DISCOVERY_OUTPUT_SCHEMA = {
  type: 'object',
  properties: {
    schemaVersion: {
      type: 'string',
      enum: ['quality-input-discovery.v1'],
    },
    opportunities: {
      type: 'array',
      minItems: 3,
      maxItems: 3,
      items: OPPORTUNITY_SCHEMA,
    },
  },
  required: ['schemaVersion', 'opportunities'],
  additionalProperties: false,
};

const DIRECTOR_BRIEF_SCHEMA = {
  type: 'object',
  properties: {
    episodeQuestion: NON_EMPTY_STRING,
    thesis: NON_EMPTY_STRING,
    audienceState: NON_EMPTY_STRING,
    desiredAfterState: NON_EMPTY_STRING,
    hook: NON_EMPTY_STRING,
    payoff: NON_EMPTY_STRING,
    evidenceIds: STRING_ARRAY,
    uncertaintyNotes: STRING_ARRAY,
    rightsNotes: STRING_ARRAY,
    safetyNotes: STRING_ARRAY,
  },
  required: [
    'episodeQuestion',
    'thesis',
    'audienceState',
    'desiredAfterState',
    'hook',
    'payoff',
    'evidenceIds',
    'uncertaintyNotes',
    'rightsNotes',
    'safetyNotes',
  ],
  additionalProperties: false,
};

const BEAT_SCHEMA = {
  type: 'object',
  properties: {
    order: { type: 'integer', minimum: 0 },
    role: NON_EMPTY_STRING,
    narration: NON_EMPTY_STRING,
    claim: NON_EMPTY_STRING,
    evidenceIds: STRING_ARRAY,
    visualIntent: NON_EMPTY_STRING,
    assetIntent: NON_EMPTY_STRING,
    fallback: NON_EMPTY_STRING,
  },
  required: [
    'order',
    'role',
    'narration',
    'claim',
    'evidenceIds',
    'visualIntent',
    'assetIntent',
    'fallback',
  ],
  additionalProperties: false,
};

export const ELABORATION_OUTPUT_SCHEMA = {
  type: 'object',
  properties: {
    schemaVersion: {
      type: 'string',
      enum: ['quality-input-elaboration.v1'],
    },
    directorBrief: DIRECTOR_BRIEF_SCHEMA,
    script: {
      type: 'object',
      properties: {
        targetDurationSec: { type: 'integer', enum: [45] },
        narration: NON_EMPTY_STRING,
      },
      required: ['targetDurationSec', 'narration'],
      additionalProperties: false,
    },
    beats: {
      type: 'array',
      minItems: 5,
      maxItems: 7,
      items: BEAT_SCHEMA,
    },
  },
  required: ['schemaVersion', 'directorBrief', 'script', 'beats'],
  additionalProperties: false,
};

function assertSchema(value, schema, path = '$') {
  if (schema.enum && !schema.enum.includes(value)) {
    throw new Error(`${path} is not an allowed value`);
  }
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw new Error(`${path} must be an object`);
    }
    const keys = Object.keys(value);
    for (const key of schema.required ?? []) {
      if (!keys.includes(key)) throw new Error(`${path}.${key} is required`);
    }
    if (schema.additionalProperties === false) {
      for (const key of keys) {
        if (!(key in schema.properties)) {
          throw new Error(`${path}.${key} is not allowed`);
        }
      }
    }
    for (const [key, child] of Object.entries(schema.properties ?? {})) {
      if (keys.includes(key)) assertSchema(value[key], child, `${path}.${key}`);
    }
    return;
  }
  if (schema.type === 'array') {
    if (!Array.isArray(value)) throw new Error(`${path} must be an array`);
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      throw new Error(`${path} has too few items`);
    }
    if (schema.maxItems !== undefined && value.length > schema.maxItems) {
      throw new Error(`${path} has too many items`);
    }
    value.forEach((item, index) => assertSchema(item, schema.items, `${path}[${index}]`));
    return;
  }
  if (schema.type === 'integer') {
    if (!Number.isInteger(value)) throw new Error(`${path} must be an integer`);
    if (schema.minimum !== undefined && value < schema.minimum) {
      throw new Error(`${path} is below minimum`);
    }
    return;
  }
  if (schema.type === 'string') {
    if (typeof value !== 'string') throw new Error(`${path} must be a string`);
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      throw new Error(`${path} is too short`);
    }
  }
}

export function validateGenerationOutput(track, value) {
  const schema = track === 'D'
    ? DISCOVERY_OUTPUT_SCHEMA
    : track === 'E'
      ? ELABORATION_OUTPUT_SCHEMA
      : null;
  if (!schema) throw new Error(`unknown generation track: ${track}`);
  assertSchema(value, schema);
  return value;
}
```

- [ ] **Step 4: Write the two instruction files**

Both prompts must contain these invariant rules:

```text
Use only the supplied input package.
Never invent a source id, Vira metric, quote, product result, audience observation, or right.
Keep official fact, audience observation, market observation, editorial interpretation,
creative pattern, and AI hypothesis distinct.
Do not turn correlation into causation.
If evidence is absent or insufficient, expose the limitation instead of filling it.
Do not assume a referenced image or clip is licensed for reuse.
Return only the strict JSON shape supplied by the request.
```

Discovery adds “return exactly three materially different opportunities.” Elaboration adds “do not
change the locked episode question; return a 45-second plan with 5~7 beats.”

- [ ] **Step 5: Implement request building and live guard**

```js
import { sha256Json } from './canonical-json.mjs';
import { validateGenerationOutput } from './generation-contracts.mjs';

const ENDPOINT = 'https://api.openai.com/v1/responses';
const MODEL = 'gpt-4.1';

export function buildProviderRequest(conditionPackage, { instructions, schema }) {
  return {
    model: MODEL,
    instructions,
    input: JSON.stringify(conditionPackage.input),
    store: false,
    temperature: 0.2,
    max_output_tokens: 4000,
    text: {
      format: {
        type: 'json_schema',
        name: conditionPackage.track === 'D'
          ? 'quality_input_discovery_v1'
          : 'quality_input_elaboration_v1',
        strict: true,
        schema,
      },
    },
  };
}

export async function runProviderRequest(conditionPackage, options) {
  const request = buildProviderRequest(conditionPackage, options);
  if (!options.live) {
    return {
      mode: 'dry-run',
      conditionPackageId: conditionPackage.id,
      requestDigest: sha256Json(request),
    };
  }
  if (!options.liveApproved) {
    throw new Error('live provider call is not approved');
  }
  if (!options.apiKey) {
    throw new Error('SHORTFORM_DIRECTOR_EVAL_OPENAI_API_KEY is required');
  }
  const startedAt = Date.now();
  const response = await options.fetchImpl(ENDPOINT, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${options.apiKey}`,
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`provider request failed with HTTP ${response.status}`);
  }
  return parseProviderResponse(
    await response.json(),
    conditionPackage,
    Date.now() - startedAt,
    options.pricing ?? null,
  );
}

function outputTextOf(value) {
  if (typeof value?.output_text === 'string') return value.output_text;
  const parts = [];
  for (const item of Array.isArray(value?.output) ? value.output : []) {
    for (const content of Array.isArray(item?.content) ? item.content : []) {
      if (typeof content?.text === 'string') parts.push(content.text);
    }
  }
  return parts.join('\n').trim();
}

function collectEvidenceIds(payload) {
  const ids = [];
  for (const opportunity of payload.opportunities ?? []) {
    ids.push(...opportunity.evidenceIds);
  }
  if (payload.directorBrief) ids.push(...payload.directorBrief.evidenceIds);
  for (const beat of payload.beats ?? []) ids.push(...beat.evidenceIds);
  return ids;
}

export function validateConditionConstraints(payload, conditionPackage) {
  if (conditionPackage.track === 'E'
    && payload.directorBrief.episodeQuestion
      !== conditionPackage.input.episodeIntent.question) {
    throw new Error('episode question changed');
  }
  if (conditionPackage.input.evidenceState === 'none_available'
    && collectEvidenceIds(payload).length > 0) {
    throw new Error('evidence ids must be empty when evidenceState is none_available');
  }
  if (conditionPackage.track === 'D') {
    const ids = payload.opportunities.map((opportunity) => opportunity.id);
    if (new Set(ids).size !== ids.length) {
      throw new Error('opportunity ids must be unique');
    }
  }
  if (conditionPackage.track === 'E') {
    const orders = payload.beats.map((beat) => beat.order);
    const expected = payload.beats.map((_, index) => index);
    if (JSON.stringify(orders) !== JSON.stringify(expected)) {
      throw new Error('beat order must be contiguous from zero');
    }
  }
  return payload;
}

function allowedInputIds(conditionPackage) {
  const input = conditionPackage.input;
  return new Set([
    ...(input.sourceClaims ?? []).flatMap((card) => (
      (card.claims ?? []).map((claim) => claim.id)
    )),
    ...(input.audienceQuestions ?? []).map((question) => question.id),
    ...(input.viraEvidence?.evidence ?? []).map((evidence) => evidence.id),
    ...(input.creativePatterns ?? []).map((reference) => reference.id),
    ...(input.feedbackCards ?? []).map((feedback) => feedback.id),
  ]);
}

export function validateEvidenceReferences(payload, conditionPackage) {
  const allowed = allowedInputIds(conditionPackage);
  for (const id of collectEvidenceIds(payload)) {
    if (!allowed.has(id)) throw new Error(`unknown evidence id: ${id}`);
  }
  return payload;
}

export function parseProviderResponse(value, conditionPackage, elapsedMs, pricing) {
  const text = outputTextOf(value);
  if (!text) throw new Error('provider response had no output text');
  const payload = validateEvidenceReferences(
    validateConditionConstraints(
      validateGenerationOutput(
        conditionPackage.track,
        JSON.parse(text),
      ),
      conditionPackage,
    ),
    conditionPackage,
  );
  const inputTokens = Number.isInteger(value?.usage?.input_tokens)
    ? value.usage.input_tokens
    : null;
  const outputTokens = Number.isInteger(value?.usage?.output_tokens)
    ? value.usage.output_tokens
    : null;
  const estimatedCostUsd = pricing && inputTokens !== null && outputTokens !== null
    ? Number((
      inputTokens * pricing.inputUsdPerMillionTokens / 1_000_000
      + outputTokens * pricing.outputUsdPerMillionTokens / 1_000_000
    ).toFixed(8))
    : null;
  return {
    schemaVersion: 'quality-input-output.v1',
    artifactId: `${conditionPackage.id}.output`,
    conditionPackageId: conditionPackage.id,
    track: conditionPackage.track,
    payload,
    provider: {
      model: MODEL,
      resolvedModel: typeof value?.model === 'string' ? value.model : null,
      responseId: typeof value?.id === 'string' ? value.id : null,
      inputTokens,
      outputTokens,
      estimatedCostUsd,
      elapsedMs,
    },
  };
}
```

The schema walker rejects wrong opportunity count, beat count, evidence ID type and unknown
properties. Neither the parser nor its error messages may include request headers or the API key.

- [ ] **Step 6: Implement sequential CLI execution**

`run-provider.mjs`:

- defaults to dry-run,
- accepts exactly one prepared run directory,
- processes sorted package IDs sequentially,
- writes one response JSON per package through atomic rename,
- records elapsed time and token usage,
- stops on the first schema or HTTP failure,
- updates `providerCalls` only after a valid response is durably written,
- never retries automatically.

Live mode also refuses a missing or non-ready `pricing-snapshot.json`; dry-run does not require
pricing.

Live mode requires both:

```text
--live
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1
```

The credential comes only from `SHORTFORM_DIRECTOR_EVAL_OPENAI_API_KEY`.

- [ ] **Step 7: Run tests and the 48-call dry-run**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/provider-runner.test.mjs
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a
```

Expected: 48 request digests, zero network calls, zero provider responses.

- [ ] **Step 8: Freeze the provider pricing snapshot**

From the official OpenAI API pricing page, record the currently published `gpt-4.1` input and output
rates in:

```text
.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json
```

Use this exact shape:

```json
{
  "schemaVersion": "quality-input-provider-pricing.v1",
  "provider": "openai",
  "model": "gpt-4.1",
  "currency": "USD",
  "inputUsdPerMillionTokens": null,
  "outputUsdPerMillionTokens": null,
  "sourceUrl": "https://openai.com/api/pricing/",
  "retrievedAt": null,
  "state": "collecting"
}
```

Before any live call, replace both rates and `retrievedAt` with observed values and set
`state: "ready"`. If the official page does not list the pinned model, stop and report the mismatch
instead of copying a third-party price.

Write the ready snapshot through a temporary sibling and atomic rename, calculate its digest and
set only `run-manifest.json.pricingSnapshotDigest` through the same atomic-write pattern. The live
runner rejects a missing digest or any snapshot whose current digest differs from the manifest.

- [ ] **Step 9: Stop and notify before the first provider batch**

Before reporting readiness, verify Task 7 Steps 1~5 have frozen the rubric, score schema and blind
packet behavior, and verify their digests match the run manifest.

Report exact model `gpt-4.1`, endpoint host `api.openai.com`, 48 calls, `store:false`, output
directory, and the fact that no app/server is started. Do not run live without the user’s explicit
go-ahead.

- [ ] **Step 10: Execute the approved episode A live batch**

After approval:

```bash
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1 \
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --live \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a
```

The API key must already exist in the environment. Expected: 48 valid response files, no automatic
retry, manifest `providerCalls: 48`.

---

### Task 6: Feedback card와 episode B 대조군

**Files:**

- Modify:
  each case `feedback-cards.json`
- Modify:
  each case `manifest.json`
- Reuse:
  `lib/condition-compiler.mjs`,
  `scripts/compile-run.mjs`,
  `scripts/run-provider.mjs`
- Test:
  `tests/condition-compiler.test.mjs`

**Interfaces:**

- Consumes: episode A C5 D/E outputs and human editorial decisions
- Produces: four ready feedback packs and 16 episode B provider outputs

- [ ] **Step 1: Prepare the feedback review sheet**

For each case, show only C5 D/E outputs, the approved rubric and the original case pack. The editor
selects at most three repeatable lessons. Each card must match:

```json
{
  "id": "BEAUTY-01-F01",
  "sourceOutputArtifactId": "quality-input-2026-07-24-ladder-a.beauty-01.a.c5.e.output",
  "decision": "revise",
  "appliesTo": "evidence",
  "observedProblem": "광택 유지와 착색 지속을 같은 결과처럼 설명했다.",
  "preferredRule": "광택과 착색을 별도 claim과 별도 시각 비교로 나눈다.",
  "evidenceOrExample": "B-S03의 공식 사용 설명과 audience question B-AQ04를 분리한다.",
  "scope": "topic_family"
}
```

The example fixes the shape only. Actual cards must cite the actual output artifact and observed
problem. Do not use provider self-critique as the editorial decision.

- [ ] **Step 2: Validate and reseal feedback**

Set `feedback.state` to `ready`, keep 1~3 cards, run:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/seal-packs.mjs
node .codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs --sealed
node --test .codex/experiments/shortform-director-quality-input/tests/condition-compiler.test.mjs
```

Expected: C6 compilation is now allowed only for episode B.

- [ ] **Step 3: Compile and dry-run B-NO-F and C6**

Run:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs \
  --phase feedback-b \
  --run-id quality-input-2026-07-24-feedback-b \
  --pricing-snapshot=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-feedback-b
```

Expected: 16 request digests and zero provider calls.

- [ ] **Step 4: Stop and notify before the second provider batch**

Report exact model, 16 calls, four `B-NO-F`/`C6` pairs and output directory. Wait for explicit
go-ahead.

- [ ] **Step 5: Execute the approved episode B live batch**

```bash
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1 \
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --live \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-feedback-b
```

Expected: 16 valid outputs. Combined minimum experiment count is now 32 case-condition cells, 64
track-specific condition packages and 64 provider calls.

---

### Task 7: Blind two-pass 평가와 score aggregation

**Files:**

- Create:
  `.codex/experiments/shortform-director-quality-input/rubric/rubric.v1.json`
- Create:
  `.codex/experiments/shortform-director-quality-input/rubric/evaluation-score.schema.json`
- Create:
  `.codex/experiments/shortform-director-quality-input/lib/blind-evaluation.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/create-blind-set.mjs`
- Create:
  `.codex/experiments/shortform-director-quality-input/scripts/aggregate-scores.mjs`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/blind-evaluation.test.mjs`

**Interfaces:**

- Consumes: 64 provider outputs, materialization metrics and two evaluator score files
- Produces:
  128 blind scoring artifacts의 creative/evidence packets, private blind map, 64 package-level
  aggregate JSON, operational cost summary and disagreement list

`create-blind-set.mjs` accepts one or more repeatable `--run=<run-directory>` options. For the
initial phase it also supports the named `--ladder-run` and `--feedback-run` aliases shown below;
mixing aliases with `--run` is rejected.

Steps 1~5 are an execution prerequisite for Task 4 compilation and the first live provider gate.
Steps 6~8 run only after provider outputs exist.

- [ ] **Step 1: Write RED tests**

Tests must verify:

- condition ID, axis list, source count and input digest do not appear in blind creative packets,
- every creative-pass evidence array becomes the same `["evidence-redacted"]` sentinel,
- evidence-pass IDs become neutral `ev-01`, `ev-02` tokens,
- the private map reverses blind IDs and evidence tokens,
- creative pass accepts only the six non-evidence dimensions,
- evidence pass accepts only `evidenceAccuracy`,
- scores outside 1~5 are rejected,
- a 2-point evaluator difference enters adjudication,
- any hard-fail mismatch enters adjudication,
- weighted totals use exactly 15/10/15/20/15/15/10,
- provider token, estimated cost and latency sums equal the source outputs,
- materialization minutes stay separate from provider latency.
- each Track D output becomes three independently scored opportunity artifacts while each Track E
  output remains one scored artifact.

- [ ] **Step 2: Run RED**

Run:

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/blind-evaluation.test.mjs
```

Expected: FAIL because blind evaluation code does not exist.

- [ ] **Step 3: Define the rubric JSON**

```json
{
  "schemaVersion": "quality-input-rubric.v1",
  "weights": {
    "specificity": 0.15,
    "novelty": 0.10,
    "audienceRelevance": 0.15,
    "evidenceAccuracy": 0.20,
    "hookPayoff": 0.15,
    "visualizability": 0.15,
    "productionFeasibility": 0.10
  },
  "hardFailures": [
    "unsupported_or_contradicted_core_claim",
    "fabricated_vira_source_quote_or_metric",
    "correlation_presented_as_causation",
    "evidence_class_conflation",
    "privacy_safety_regulatory_or_financial_boundary",
    "payoff_depends_on_unusable_rights_asset"
  ],
  "disagreementThreshold": 2
}
```

Add the approved 1·3·5 anchors from protocol section 6.2 as `anchors` without changing their meaning.

Define `evaluation-score.schema.json` as a strict JSON Schema for an evaluator submission object:

```text
schemaVersion = quality-input-evaluator-submission.v1
evaluatorId = non-empty pseudonym
scores = array of EvaluationScore
```

The `scores` item schema is a `oneOf` union: creative items require exactly the six non-evidence
dimensions, while evidence items require exactly `evidenceAccuracy`. Both variants require
`blindId`, `evaluatorId`, `pass`, `hardFailures` and `notes`, reject unknown properties and restrict
scores to integers 1~5. The outer `evaluatorId` must equal every item’s `evaluatorId`. Tests compile
one fixture submission for each pass and reject mixed or incomplete score objects. This schema is
the frozen two-evaluator score-sheet contract recorded in every run manifest.

- [ ] **Step 4: Implement deterministic blind IDs**

Generate a random 32-byte salt once per run and store it only in
`private/quality-input-2026-07-24/blind-salt`. Derive:

```js
import { createHash } from 'node:crypto';

export function blindId(salt, artifactId) {
  return `blind-${createHash('sha256')
    .update(`${salt}:${artifactId}`)
    .digest('hex')
    .slice(0, 12)}`;
}
```

Use a second hash namespace for evidence token order. The creative packet excludes source details;
every evidence array in that packet uses the fixed sentinel so source count is not leaked. The
evidence packet exposes only the referenced source cards with neutral IDs and locators.

- [ ] **Step 5: Implement score validation and aggregation**

```js
const WEIGHTS = {
  specificity: 0.15,
  novelty: 0.10,
  audienceRelevance: 0.15,
  evidenceAccuracy: 0.20,
  hookPayoff: 0.15,
  visualizability: 0.15,
  productionFeasibility: 0.10,
};

export function weightedTotal(scores) {
  return Number(Object.entries(WEIGHTS)
    .reduce((sum, [key, weight]) => sum + scores[key] * weight, 0)
    .toFixed(3));
}

export function mergePasses(creative, evidence) {
  if (creative.pass !== 'creative' || evidence.pass !== 'evidence') {
    throw new Error('creative and evidence passes are both required');
  }
  if (creative.blindId !== evidence.blindId
    || creative.evaluatorId !== evidence.evaluatorId) {
    throw new Error('pass identity mismatch');
  }
  return {
    blindId: creative.blindId,
    evaluatorId: creative.evaluatorId,
    scores: {
      ...creative.scores,
      evidenceAccuracy: evidence.scores.evidenceAccuracy,
    },
    hardFailures: [...new Set([
      ...creative.hardFailures,
      ...evidence.hardFailures,
    ])].sort(),
    notes: [creative.notes, evidence.notes].filter(Boolean).join('\n'),
  };
}

export function needsAdjudication(left, right) {
  const scoreMismatch = Object.keys(WEIGHTS)
    .some((key) => Math.abs(left.scores[key] - right.scores[key]) >= 2);
  const hardFailMismatch = JSON.stringify([...left.hardFailures].sort())
    !== JSON.stringify([...right.hardFailures].sort());
  return scoreMismatch || hardFailMismatch;
}
```

Validate that creative score objects contain exactly
`specificity`, `novelty`, `audienceRelevance`, `hookPayoff`, `visualizability`,
`productionFeasibility`, while evidence score objects contain exactly `evidenceAccuracy`.
`needsAdjudication()` receives the two evaluators' already-merged `mergePasses()` results, never a
single-pass score.
For Track D, aggregate each of the three opportunities separately and use the dimension median as
the package score. Keep Track D and Track E totals separate.

- [ ] **Step 6: Create blind packets**

Run:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/create-blind-set.mjs \
  --ladder-run=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a \
  --feedback-run=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-feedback-b
```

Expected: the 32 Track D outputs split into 96 opportunity artifacts and the 32 Track E outputs stay
as 32 plan artifacts, yielding 128 creative packets, 128 evidence packets and one gitignored
private map.

- [ ] **Step 7: Collect two independent evaluator files**

Each evaluator submits one JSON array with exactly 256 `EvaluationScore` entries: creative and
evidence passes for all 128 blind artifacts. They complete all creative passes before receiving the
evidence packets. Evaluator IDs are pseudonyms stored in the private directory; no personal contact
data is recorded. The aggregator rejects a missing pass or duplicate
`blindId`/`evaluatorId`/`pass` tuple.

- [ ] **Step 8: Aggregate and adjudicate**

Run:

```bash
node .codex/experiments/shortform-director-quality-input/scripts/aggregate-scores.mjs \
  --scores=.codex/experiments/shortform-director-quality-input/private/evaluations/evaluator-a.json,.codex/experiments/shortform-director-quality-input/private/evaluations/evaluator-b.json \
  --materialization-metrics=.codex/experiments/shortform-director-quality-input/private/materialization-metrics.json
```

Expected output has this shape with a concrete non-negative integer on the second line:

```text
128 scoring artifacts / 64 provider packages aggregated
adjudication required: 0
```

The displayed zero illustrates the no-disagreement case; a positive integer is valid. Resolve every
listed disagreement against the frozen evidence locator and write a third
`adjudicated-scores.json`. Do not overwrite either evaluator’s original file.

---

### Task 8: Targeted ablation, three-sample confirmation과 decision report

**Files:**

- Modify:
  `.codex/experiments/shortform-director-quality-input/lib/condition-compiler.mjs`
  only if tests expose a missing already-defined `FULL-*` branch
- Modify:
  `.codex/experiments/shortform-director-quality-input/scripts/aggregate-scores.mjs`
- Create after evaluation:
  `.codex/records/shortform-director-quality-input-validation-result-2026-07-24.md`
- Test:
  `.codex/experiments/shortform-director-quality-input/tests/blind-evaluation.test.mjs`

**Interfaces:**

- Consumes: adjudicated ladder scores
- Produces:
  selected ablation conditions, three-sample confirmation results and input disposition

- [ ] **Step 1: Write RED selection tests**

```js
test('selects an axis when target dimension changes by at least 0.5', () => {
  assert.deepEqual(
    selectAblations([{ caseId: 'BEAUTY-01', axis: 'A', delta: 0.5 }]),
    [{
      caseId: 'BEAUTY-01',
      episode: 'A',
      withAxisCondition: 'C5',
      withoutAxisCondition: 'FULL-A',
      reason: 'delta>=0.5',
    }],
  );
});

test('selects an axis when a hard fail changes', () => {
  assert.deepEqual(
    selectAblations([{
      caseId: 'PRODUCT-01',
      axis: 'S',
      delta: 0.1,
      hardFailChanged: true,
    }]),
    [{
      caseId: 'PRODUCT-01',
      episode: 'A',
      withAxisCondition: 'C5',
      withoutAxisCondition: 'FULL-S',
      reason: 'hard-fail-change',
    }],
  );
});

test('selects the fixed episode B feedback pair without inventing FULL-F', () => {
  assert.deepEqual(
    selectAblations([{ caseId: 'IDOL-01', axis: 'F', delta: 0.6 }]),
    [{
      caseId: 'IDOL-01',
      episode: 'B',
      withAxisCondition: 'C6',
      withoutAxisCondition: 'B-NO-F',
      reason: 'delta>=0.5',
    }],
  );
});

test('does not select a low-delta axis without another trigger', () => {
  assert.deepEqual(
    selectAblations([{ caseId: 'EXPERT-01', axis: 'V', delta: 0.2 }]),
    [],
  );
});
```

- [ ] **Step 2: Implement the pre-registered selector**

Select a case-axis pair when any of these is true:

```text
absolute target-dimension delta >= 0.5
hard fail appeared or disappeared
evaluator disagreement reached 2 before adjudication
evidenceAccuracy or productionFeasibility decreased
```

Map P/S/A/V/R to a same-sample `C5`/`FULL-*` pair. Feedback always uses its same-sample episode B
`C6`/`B-NO-F` pair and never a `FULL-F` condition.

```js
const CONFIRMATION_PAIRS = {
  P: { episode: 'A', withAxisCondition: 'C5', withoutAxisCondition: 'FULL-P' },
  S: { episode: 'A', withAxisCondition: 'C5', withoutAxisCondition: 'FULL-S' },
  A: { episode: 'A', withAxisCondition: 'C5', withoutAxisCondition: 'FULL-A' },
  V: { episode: 'A', withAxisCondition: 'C5', withoutAxisCondition: 'FULL-V' },
  R: { episode: 'A', withAxisCondition: 'C5', withoutAxisCondition: 'FULL-R' },
  F: { episode: 'B', withAxisCondition: 'C6', withoutAxisCondition: 'B-NO-F' },
};

export function selectAblations(rows) {
  const seen = new Set();
  return rows.flatMap((row) => {
    const key = `${row.caseId}:${row.axis}`;
    if (seen.has(key)) {
      throw new Error(`duplicate consolidated ablation row: ${key}`);
    }
    seen.add(key);
    const pair = CONFIRMATION_PAIRS[row.axis];
    if (!pair) return [];
    let reason = null;
    if (row.hardFailChanged === true) reason = 'hard-fail-change';
    else if (row.evidenceAccuracyDecreased === true) {
      reason = 'evidence-accuracy-regression';
    } else if (row.productionFeasibilityDecreased === true) {
      reason = 'production-feasibility-regression';
    } else if (row.preAdjudicationDisagreement >= 2) {
      reason = 'evaluator-disagreement>=2';
    } else if (Math.abs(row.delta) >= 0.5) {
      reason = 'delta>=0.5';
    }
    return reason ? [{
      caseId: row.caseId,
      ...pair,
      reason,
    }] : [];
  });
}
```

The aggregator must first consolidate D/E results to exactly one row per case-axis: `delta` is the
largest absolute target-dimension change with its sign preserved, boolean triggers are OR-combined,
and `triggerTracks` records which tracks caused selection. The selector rejects duplicate
case-axis rows so a pair cannot be compiled twice.

- [ ] **Step 3: Compile selected ablations and dry-run**

```bash
node .codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs \
  --phase ablation \
  --run-id quality-input-2026-07-24-ablation-s1 \
  --sample-id s1 \
  --pricing-snapshot=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json \
  --selection=.codex/experiments/shortform-director-quality-input/private/ablation-selection.json
node .codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs \
  --phase ablation \
  --run-id quality-input-2026-07-24-ablation-s2 \
  --sample-id s2 \
  --pricing-snapshot=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json \
  --selection=.codex/experiments/shortform-director-quality-input/private/ablation-selection.json
node .codex/experiments/shortform-director-quality-input/scripts/compile-run.mjs \
  --phase ablation \
  --run-id quality-input-2026-07-24-ablation-s3 \
  --sample-id s3 \
  --pricing-snapshot=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ladder-a/pricing-snapshot.json \
  --selection=.codex/experiments/shortform-director-quality-input/private/ablation-selection.json
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s1
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s2
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s3
```

Expected: each manifest condition count equals the selection file count × 2 conditions × 2 tracks;
all three manifests report zero provider calls. The two conditions in a selected pair share a
sample ID, so every comparison is within the same independent sample.

- [ ] **Step 4: Stop and notify before the ablation provider batch**

Report exact selected pairs, calls per sample (`pair count × 4`), total calls for three independent
samples (`pair count × 12`), model and output path. Wait for explicit go-ahead.

- [ ] **Step 5: Run three independent approved samples**

The Responses API path used here has no experiment seed contract, so record:

```json
{
  "samplingMode": "three_independent_samples",
  "sampleIds": ["s1", "s2", "s3"],
  "temperature": 0.2
}
```

After approval, run:

```bash
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1 \
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --live \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s1
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1 \
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --live \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s2
SHORTFORM_DIRECTOR_EVAL_LIVE_APPROVED=1 \
node .codex/experiments/shortform-director-quality-input/scripts/run-provider.mjs \
  --live \
  --run-dir=.codex/experiments/shortform-director-quality-input/runs/quality-input-2026-07-24-ablation-s3
```

Never replace one failed sample with an unrecorded retry.

- [ ] **Step 6: Blind-score and aggregate the confirmation pairs**

Run `create-blind-set.mjs` with each of the three confirmation run directories through its
repeatable `--run` option. This produces one new private map namespace and splits Track D outputs
into three opportunities exactly as in Task 7. Both evaluators repeat the same creative-first,
evidence-second procedure. Compare within-sample pair deltas first, then compare the median of the
three sample deltas. Do not compare a new `FULL-*` result against the original one-sample C5 result,
and do not pool Track D and Track E into one number.

- [ ] **Step 7: Produce the decision report**

The result document contains:

```text
run identities and digests
source/Vira sufficiency by case
quality and cost deltas by input axis
hard failures and adjudications
Track D and Track E results separately
default / conditional / excluded disposition for P,S,A,V,R,F
limitations
production recommendation with no implementation
existing structural proxy was not run against non-DraftVideoPlan outputs
```

Apply the exact thresholds from protocol section 7:

- default candidate: 2+ cases with target dimension median gain at least 0.5 or repeated hard-fail
  removal, without evidence/feasibility regression
- conditional: one route only, sufficiency-dependent or high review/rights cost
- excluded from default: gain under 0.25 with meaningful burden, redundant in ablation, or repeated
  evidence/feasibility regression

The report must not claim statistical causality or actual published-video performance.

---

### Task 9: Final verification and documentation handoff

**Files:**

- Modify:
  `.codex/records/sessions/2026/07/24.md`
- Modify:
  `.codex/handoff/NEXT.md`
- Do not modify any production repository

**Interfaces:**

- Consumes: all experiment tests, manifests and result report
- Produces: reproducible handoff with explicit remaining boundaries

- [ ] **Step 1: Run the complete offline test suite**

```bash
node --test .codex/experiments/shortform-director-quality-input/tests/*.test.mjs
```

Expected: all tests pass and no network request occurs.

- [ ] **Step 2: Revalidate sealed packs and run manifests**

```bash
node .codex/experiments/shortform-director-quality-input/scripts/validate-packs.mjs --sealed
node .codex/experiments/shortform-director-quality-input/scripts/aggregate-scores.mjs \
  --verify-only
```

Expected: four sealed packs; every provider output, blind score and aggregate references a known
digest.

- [ ] **Step 3: Run safe secret and placeholder scans**

```bash
rg -l 'sk-[A-Za-z0-9_-]{12,}|DATABASE_URL=|authorization: Bearer|BEGIN (RSA|OPENSSH) PRIVATE KEY' \
  .codex/experiments/shortform-director-quality-input \
  .codex/records/shortform-director-quality-input-validation-result-2026-07-24.md
rg -n '\b(T[B]D|T[O]DO|F[I]XME)\b|미[정]|추후[ ]선택' \
  .codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_EXECUTION_PLAN_2026-07-24.md \
  .codex/records/shortform-director-quality-input-validation-result-2026-07-24.md
```

Expected: no matches. The literal header name `authorization` in source code is allowed only when
the value is constructed from the environment at runtime and no credential value is present.

- [ ] **Step 4: Confirm repository boundaries**

For each repository listed in `.codex/handoff/NEXT.md`, run:

```bash
git status --short --branch
git rev-list --left-right --count HEAD...@{upstream}
git log -3 --oneline --decorate
```

Expected:

- production repositories have no new experiment changes,
- `.codex` contains only the approved validation documents, experiment files and records,
- `legacy/adlight_python/fastapi_server.spec` remains modified and untouched,
- Vira remains clean at the explicitly reconciled read-only revision; if revision reconciliation was
  not authorized, Vira execution remains blocked and the observed mismatch is recorded,
- every repository remains `0 0` against its upstream unless an external change is reported.

- [ ] **Step 5: Update session and handoff records**

Record:

- exact test commands and results,
- actual Vira state by case without raw private data,
- provider model and call counts without credential IDs,
- result report path,
- files intentionally gitignored,
- remaining product decisions,
- confirmation that no production code, commit, push, PR, deploy, migration, server or app action
  occurred.

- [ ] **Step 6: Final review checkpoint**

Present the result and repository status to the user. Do not commit, push or start production
implementation without a separate explicit request.

---

## Execution order and stop points

```text
Task 1 contracts — complete
  → Task 2 public source packs — complete
  → Task 3 Vira fixture tests — complete
  → STOP: current Vira DB is non-representative test data
  → NEXT SESSION: decide corpus purpose and collection approach
  → write a replacement design and implementation plan
  → explicit approval before Vira branch/worktree, DB, API or provider action
```

Task 1~3의 완료 범위는 offline이다. 이 계획에 있던 Task 3 live SQL과 Task 4 이후
provider experiment는 새 corpus 설계가 승인될 때까지 실행하지 않는다.
