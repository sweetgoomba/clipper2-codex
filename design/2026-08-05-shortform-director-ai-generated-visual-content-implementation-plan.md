# Shortform Director AI-Generated Visual Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every newly generated storyboard request exact scene text, numbers, charts, names, logos, and concrete subject matter inside the AI-generated video while Clipper retains only narration TTS and its spoken-word subtitle.

**Architecture:** Keep the existing two-call `video-plan` plus `scene-media-decision` flow and the existing generated-video-only output schema. Change only the versioned Web API prompt contract: narrow `captions: false` to spoken-word subtitles, explicitly require scene-native text and factual graphics in `generationBrief`, and require concrete visual variety. The Desktop compiler and final render path remain unchanged because `overlayMode: none` already prevents programmatic diagrams and the final Clipper adapter derives subtitles from narration cues rather than storyboard informational text layers.

**Tech Stack:** NestJS, TypeScript, Jest, Desktop NestJS Node tests

## Global Constraints

- Every scene keeps `baseMedium: generated-video`, `overlayMode: none`, `searchBrief: null`, and `programmaticBrief: null`.
- Exact text, numbers, charts, names, logos, and factual-looking graphics are allowed inside AI-generated video pixels even when distorted.
- `audioPolicy.captions: false` forbids only subtitles synchronized with narration; it does not forbid scene-native visible text.
- `clipper-template` mode keeps Clipper narration TTS and its spoken-word subtitle.
- No additional LLM call, provider call, programmatic data overlay, dependency, migration, or cost approval change.
- Existing stored storyboards and generated assets are not rewritten.
- Do not run paid AI provider smoke tests.
- Do not commit implementation changes until the user asks.

---

### Task 1: Version the scene-media prompt contract

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts:26-52`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts:176-194`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts:37-50`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts:109-122`

**Interfaces:**
- Consumes: `INFERENCE_PURPOSE_SPECS['scene-media-decision']`
- Produces: prompt contract version `shortform-director.scene-media-decision.v6`
- Preserves: existing `SCENE_MEDIA_DECISION_SCHEMA` and `validateSceneMediaDecision`

- [ ] **Step 1: Write failing prompt-contract tests**

Change the scene-media prompt test to require the new version and positive
policy:

```ts
expect(spec.promptTemplateVersion).toBe(
  'shortform-director.scene-media-decision.v6',
);
[
  'exactly one decision for every input scene',
  'generated-video',
  'overlayMode none',
  'videoPlan.scenes[sceneIndex].onScreenText',
  'exact visible text',
  'numbers',
  'charts',
  'names',
  'logos',
  'scene-native visible text',
  'spoken-word subtitles',
  'concrete subject',
  'setting',
  'action',
  'camera',
  'Do not replace',
  'abstract metaphor',
  'visually distinct',
  'ambient sound effects',
].forEach((text) => expect(spec.systemPrompt).toContain(text));
expect(spec.systemPrompt).not.toContain(
  'must not request visible text',
);
expect(spec.systemPrompt).not.toContain(
  'must never be presented as factual proof',
);
```

Update the all-purpose version assertion in
`shortform-director-inference.contract.spec.ts` so
`scene-media-decision` expects `v6`.

- [ ] **Step 2: Run the tests and verify the intended failure**

Run:

```bash
npm test -- --runInBand shortform-director-inference.prompt.spec.ts shortform-director-inference.contract.spec.ts
```

Expected: the prompt test fails because the current contract is `v5`, still
contains `must not request visible text`, and lacks the new scene-native text
and concrete-visual instructions.

- [ ] **Step 3: Implement the minimal versioned prompt change**

In the prompt-version selector, change only the scene-media version:

```ts
: purpose === 'scene-media-decision'
? `shortform-director.${purpose}.v6`
```

Replace the scene-media system instructions with:

```ts
[
  'Choose the best generated-video direction independently for each scene and return exactly one decision for every input scene using its zero-based sceneIndex.',
  'Every scene must use baseMedium generated-video, overlayMode none, searchBrief null, programmaticBrief null, and a concrete generationBrief.',
  'Treat aiVideoProduction.modelConstraints as mandatory, including minimumShotDurationSec and maximumShotDurationSec.',
  'Treat aiVideoProduction.audioPolicy as mandatory when writing each generationBrief.',
  'When narration or dialogue is false, the generationBrief must not request speech. When captions is false, it must not request spoken-word subtitles synchronized with narration. Scene-native visible text is still allowed and required when relevant. When backgroundMusic is false, it must not request music. It may request ambient sound effects only when ambientSoundEffects is true.',
  'Include every exact string from the corresponding videoPlan.scenes[sceneIndex].onScreenText in the generationBrief and ask the video model to render that exact visible text inside the generated video.',
  'The generationBrief may request exact visible text, numbers, charts, rankings, timelines, dashboards, headlines, signs, interfaces, names, logos, album art, recognizable people, products, and platforms even when the generated result may be distorted.',
  'Describe a concrete subject, setting, action, camera treatment, and visual progression for every scene.',
  'Do not replace scene-relevant people, objects, events, data, or interfaces with an abstract metaphor merely because factualRisk is medium or high.',
  'Keep adjacent scenes visually distinct. Do not reuse waves, light streaks, particles, silhouettes, or another generic abstract motif as the primary visual across scenes unless the input explicitly requires that motif.',
  'Use only identifiers supplied in the input for evidenceIds and productionSourceIds.',
  'Return only JSON matching the provided schema.',
].join(' ')
```

Do not change the response schema, validator, call count, or model catalog.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run:

```bash
npm test -- --runInBand shortform-director-inference.prompt.spec.ts shortform-director-inference.contract.spec.ts
```

Expected: both suites pass with the v6 prompt and unchanged schema validation.

---

### Task 2: Verify unchanged cost, compilation, and Clipper subtitle boundaries

**Files:**
- Verify only: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`
- Verify only: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
- Verify only: `desktop/clipper_nestjs/test/shortform-director-clipper-render-adapter.test.js`
- Verify only: `desktop/clipper_nestjs/test/shortform-director-ai-video-service.test.js`

**Interfaces:**
- Consumes: `shortform-director.scene-media-decision.v6`
- Preserves: maximum two storyboard inference calls
- Preserves: generated-video visual layers and `overlayMode: none`
- Preserves: narration-cue-driven Clipper TTS and spoken-word subtitles

- [ ] **Step 1: Verify the Web API inference service**

Run:

```bash
npm test -- --runInBand shortform-director-inference.service.spec.ts
npm run build
```

Expected: the service uses the updated prompt contract dynamically, all tests
pass, and TypeScript compilation succeeds.

- [ ] **Step 2: Verify the Desktop storyboard and render boundaries**

Run:

```bash
npm run build
node --test test/shortform-director-candidate-production.test.js test/shortform-director-clipper-render-adapter.test.js test/shortform-director-ai-video-service.test.js
```

Expected: candidate production still performs only `video-plan` and
`scene-media-decision`; compiled shots remain generated-video; Clipper render
still uses narration cues for TTS; AI shot prompts still use the compiled
visual brief; all selected tests pass.

- [ ] **Step 3: Inspect the implementation diff**

Run in `web/clipper_web_api`:

```bash
git diff --check
git diff -- src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts
```

Expected: no whitespace errors and no changes outside the prompt contract and
its version assertions.

- [ ] **Step 4: Record the manual smoke-test boundary**

After the user builds the packaged app, generate a new storyboard and inspect
its per-scene generation briefs before paying for videos. A passing smoke test
contains concrete, different subjects per scene and directly requests exact
scene text or data such as `1주 → 3주 → 5주` and `톱50`. Existing storyboards
are expected to remain unchanged.
