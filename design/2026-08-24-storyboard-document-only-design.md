# Storyboard Document-Only Design

Date: 2026-08-24
Status: Approved for implementation

## 1. Goal

The Storyboard plugin ends at a complete, read-only production document. A user
selects a rough video candidate, generates a detailed storyboard, reviews it in
Korean, and copies either the whole document or individual production prompts
into another tool.

The storyboard must be sufficient to produce a vertical short-form video
without requiring hidden knowledge from this application. It therefore owns
the script, timing, shot direction, continuity, audio direction, external AI
prompts, image-search queries, and instructions for turning still images into
video shots.

The plugin does not generate, collect, edit, render, store, or download media.

## 2. Product Boundary

The retained flow is:

```text
operating profile
  -> research
  -> optional reference analysis
  -> research topics
  -> video candidates
  -> select one candidate
  -> approve storyboard LLM cost
  -> generate storyboard
  -> review and copy
```

The following capabilities are outside the plugin and are removed when they
exist only to turn a storyboard into media:

- generated-video and generated-image model selection;
- video and image generation jobs, provider transports, status polling,
  downloads, and local media storage;
- automatic media search, acquisition, upload, binding, and preparation;
- narration voice selection, TTS synthesis, and narration audio storage;
- render recipes, render-input staging, render jobs, final encoding, output
  download, and completed-video presentation;
- packaged rendering runtimes and environment wiring used only by this flow;
- provider administration used only by the removed generation runtimes.

Research-time reference video analysis remains. It analyzes source material and
does not produce a video. Storyboard LLM preflight, cost approval, inference
usage accounting, run history, and failure lineage also remain.

## 3. User Experience

### 3.1 Entry and generation

The candidate action remains `스토리보드 만들기`. The destination page does
not ask the user to select Gemini, Seedance, Veo, Nano Banana, or a production
mode. It shows the selected candidate, the storyboard LLM cost preflight, and a
single generation action.

The normal path uses two LLM calls. The cost preflight states both the normal
two-call path and the maximum three-call recovery path. Media-generation cost
does not appear anywhere in the plugin.

### 3.2 Read-only result

The result page is Korean-first and read-only. It contains:

1. a production overview;
2. an ordered scene and shot timeline;
3. Korean production direction for each shot;
4. an optional English prompt intended for an external video AI;
5. image-search queries and still-image usage direction;
6. whole-document and per-section copy actions;
7. storyboard history and `새 스토리보드 만들기`.

The page has no editable fields, autosave, timing editor, media picker, TTS
controls, generation status, render status, or completed-video player.

### 3.3 Copy actions

The UI provides these clipboard actions:

- `전체 스토리보드 복사`: Korean Markdown containing the production overview,
  full timeline, narration, on-screen copy, shot direction, image-search plan,
  audio direction, transitions, continuity, and constraints;
- `외부 AI용 프롬프트 복사`: an English, model-neutral master prompt containing
  the global constraints and ordered shot prompts;
- `컷 내용 복사`: the selected shot as a self-contained Korean production
  instruction;
- `AI 프롬프트 복사`: the selected shot's English video-generation prompt;
- `검색어 복사`: the selected shot's image-search queries.

Copy output excludes internal run IDs, artifact IDs, provider diagnostics,
credential data, and storage paths. Clipboard failure leaves the page intact
and presents a short retryable message.

## 4. Chosen Generation Approach

### 4.1 Considered approaches

**One-pass document generation** would be the smallest implementation, but a
single dense response is more likely to omit timing, repeat visual direction,
or contradict the narration.

**Two-pass, model-neutral generation** separates editorial structure from shot
direction. It preserves the current normal call count while producing a more
coherent and reusable document. This is the chosen approach.

**Provider-specific prompt packs** could optimize for individual external
tools, but would reintroduce the model coupling that this change removes. They
are not part of this design.

### 4.2 Pass 1: editorial plan

The first call receives the selected candidate and its grounded context. It
returns:

- title, target duration, core message, intended audience, and format;
- tone, pacing, narration direction, and overall story arc;
- ordered scenes with purpose, intent, duration, exact narration, exact
  on-screen copy, claims, and evidence references;
- a CTA appropriate to the candidate and profile.

The candidate's hook is used once at the opening. Narration contains only words
the viewer should hear. It does not contain camera, sound, editing, or visual
instructions.

### 4.3 Pass 2: shot production direction

The second call receives the validated editorial plan and returns an ordered
shot plan for every scene:

- shot timing;
- Korean visual direction;
- subject, setting, action, composition, camera, lighting, color, and texture;
- exact on-screen copy placement and emphasis;
- sound effects, ambience, music change, and transition;
- continuity rules for people, wardrobe, objects, location, and visual style;
- a self-contained, model-neutral English AI-video prompt;
- image-search queries, selection criteria, exclusions, and still-image motion
  instructions;
- negative constraints such as unwanted text, logos, watermarks, changing
  faces, changing wardrobe, or horizontal framing.

No generated-media model capability, provider duration rule, or production
mode is supplied to either pass.

### 4.4 Deterministic validation and assembly

Application code validates and assembles the two responses. It does not invent
creative copy to repair missing fields. Validation requires:

- scene durations sum exactly to the target duration;
- shot durations sum exactly to their parent scene;
- scene and shot order is contiguous and non-overlapping;
- the opening hook, core message, and CTA are present;
- narration length is plausible for its allotted duration;
- all factual claims use allowed evidence references;
- no unknown person, organization, event, date, number, or source reference is
  introduced;
- every shot has a concrete subject, setting, action, and visual progression;
- adjacent shots are meaningfully distinct;
- exact on-screen copy is concise and does not conflict with visual prompts;
- continuity and negative constraints do not contradict one another;
- every image query is a usable search phrase rather than a list of vague
  keywords.

## 5. Storyboard Document Contract

New results use a storyboard-specific document instead of persisting new media
production state. The illustrative contract is:

```ts
interface StoryboardDocumentV1 {
  schemaVersion: 'storyboard-document.v1';
  id: string;
  runId: string;
  profileId: string;
  researchRunId: string;
  topicId: string;
  candidateRunId: string;
  candidateId: string;
  title: string;
  targetDurationMs: number;
  aspectRatio: '9:16';
  overview: StoryboardOverviewV1;
  scenes: StoryboardSceneV1[];
  createdAt: string;
}
```

`StoryboardOverviewV1` contains human-facing production direction:

- core message and audience;
- format, tone, pacing, and story arc;
- visual style, color, and lighting direction;
- narration, music, ambience, and sound-effect direction;
- continuity rules;
- factual constraints, required facts, prohibited expressions, and general
  negative constraints.

Each scene contains:

- zero-based order, absolute start, and duration;
- purpose and intent;
- exact narration;
- exact on-screen text;
- claim and evidence references;
- ordered shots.

Each shot contains:

- zero-based order, absolute start, and duration;
- Korean visual direction;
- subject, setting, action, composition, camera, lighting, color, and texture;
- on-screen text treatment;
- audio and transition direction;
- continuity instructions;
- English AI-video prompt;
- negative constraints;
- image-search plan.

The image-search plan contains:

```ts
interface StoryboardImageSearchPlanV1 {
  recommendedSourceType:
    | 'official-image'
    | 'editorial-photo'
    | 'licensed-stock'
    | 'user-provided'
    | 'programmatic-graphic';
  queries: Array<{
    language: 'ko' | 'en';
    query: string;
  }>;
  selectionCriteria: string[];
  avoid: string[];
  usage: {
    crop: string;
    motion: string;
    durationMs: number;
    overlay: string;
    transition: string;
  };
}
```

`programmatic-graphic` shots may have no web-image query when a chart, timeline,
comparison card, or typography treatment communicates the fact more accurately.
The UI explains that search results are discovery leads, not proof that an image
may be reused. The application does not determine usage rights.

## 6. Persistence and Existing Results

New runs persist the storyboard document and inference lineage, not an asset
pack, narration audio pack, generated-media configuration, generation job, or
render state.

Previously stored successful storyboards remain readable through a narrow read
adapter. The adapter projects their title, duration, scenes, narration,
on-screen copy, and available visual direction into the read-only page. It does
not reactivate production controls or fabricate English prompts and image-search
plans that were never generated. History marks such entries as an earlier
format and omits unavailable copy actions.

New history responses no longer expose video model or production mode. Failed
and in-progress run records remain inspectable by the existing run owner and
candidate lineage.

## 7. Failure and Recovery Behavior

Normal generation performs exactly two inference calls. One automatic recovery
attempt is allowed for the failed stage when the failure is transient or the
provider response violates the output contract:

- pass 1 failure: retry pass 1 once, then continue to pass 2 on success;
- pass 2 failure: retain pass 1 and retry only pass 2;
- normal maximum: two calls;
- recovery maximum: three calls.

The preflight and approval snapshot include the three-call maximum. Actual
usage artifacts record only calls that occurred.

A new storyboard does not replace the current successful result until both
passes validate and the assembled document is committed atomically. If the new
run cannot recover, the current result remains open and the user receives a
plain retry action. Provider messages, stack traces, raw payloads, and internal
error codes are not shown in the default UI.

Application restart can resume a run from its last valid persisted stage. It
does not repeat a successful paid call solely because the page was closed.

## 8. Repository Responsibilities

### 8.1 Desktop Angular

- remove media-model and production-mode selection;
- remove image/video job, TTS, final-render, and completed-video components and
  service methods;
- replace the current production-oriented scene view with the document overview,
  detailed shot cards, and clipboard actions;
- keep candidate context, generation preflight, progress, history, failure
  recovery, and earlier-result reading;
- keep all visible terminology centered on `스토리보드`.

### 8.2 Desktop Nest

- make candidate-to-storyboard generation independent of generated-media
  configuration and provider capabilities;
- replace media decisions and the production compiler with the storyboard
  direction contract, validator, assembler, repository, and read adapter;
- remove plugin-owned image/video execution, TTS, media acquisition, render,
  output, and generated-media storage controllers and providers;
- keep research, reference analysis, candidate generation, storyboard preflight,
  inference clients, run lineage, and artifacts;
- ensure removed HTTP paths are not registered.

### 8.3 Web API

- replace the two retained storyboard inference schemas and prompts with the
  editorial-plan and shot-direction contracts;
- keep GPT-5.6 Luna as the internal default without exposing model choice in the
  desktop UI;
- remove image/video generation controllers, services, transports, repositories,
  job entities, runtime registration, and OpenAPI paths;
- remove generated-media capability data when no retained inference path uses it;
- remove generation job entities from active data-source registration;
- preserve already-applied migration history and add a forward migration that
  drops the dedicated `shortform_director_ai_video_jobs` and
  `shortform_director_ai_image_jobs` tables after their runtime modules and
  active entity registrations are removed;
- retain credentials required by research, reference analysis, and storyboard
  inference.

### 8.4 Desktop Electron

- remove Storyboard-specific Motion Canvas packaging, runtime discovery,
  environment injection, build steps, packaged resources, and their tests;
- leave the normal Nest process and unrelated plugin-process management intact.

### 8.5 Desktop Python

- remove renderer behavior, assets, and tests whose only consumer is the removed
  Storyboard media-production path;
- retain shared rendering behavior that has an active non-Storyboard consumer;
- verify this boundary from actual call sites rather than reverting a historical
  commit wholesale.

### 8.6 Web Admin

- remove provider controls and API contracts used only by removed media
  generation, including the fal.ai generation credential path when it has no
  other consumer;
- retain Gemini administration required by reference analysis or another active
  capability;
- retain OpenAI administration required by research, candidate generation, and
  storyboard generation.

## 9. API and Naming Compatibility

User-facing copy and new document names use Storyboard terminology. A complete
rename of all existing internal module directories, historical artifact kinds,
and stored run kinds is not required to deliver this boundary. Internal names
may remain where changing them would add migration risk without affecting the
user experience.

New or changed HTTP contracts remain raw Nest responses. The Web API OpenAPI
document, Desktop gateway types, and Angular models change together. Removed
endpoints return the normal Nest 404 response.

## 10. Security, Accuracy, and Rights

- Provider credentials and raw responses never enter copy output.
- External AI prompts treat supplied facts as data, not instructions.
- Real people, products, events, dates, and numbers must remain tied to supplied
  evidence.
- The plan prefers an official or editorial source image for identity-sensitive
  facts and does not ask an AI model to fabricate documentary proof.
- Search queries must not be described as licensed or reusable assets.
- The UI tells users to verify source and usage rights before using an image.
- English prompts must not add facts that are absent from the Korean storyboard.

## 11. Verification and Acceptance

Implementation is complete only when all of the following hold:

1. A candidate can preflight, generate, persist, reload, and display a new
   storyboard without any media model selection.
2. A normal successful run records two inference calls; a recovery run records
   no more than three and does not repeat a successful first pass.
3. The document passes timing, grounding, narration-density, shot-specificity,
   continuity, and image-query validation.
4. Whole-document, external-AI, per-shot, and search-query clipboard outputs are
   self-contained and contain no internal identifiers.
5. Earlier successful storyboards remain readable without exposing removed
   production actions.
6. No Storyboard UI route or action can generate an image, synthesize audio,
   generate a video, render, or download a completed video.
7. Removed Desktop and Web API generation endpoints return 404.
8. The packaged desktop app contains no Storyboard-specific Motion Canvas
   runtime or corresponding environment variables.
9. Active Web API data-source metadata does not register image/video generation
   job entities after the forward database migration.
10. Search queries and usage instructions are displayed as planning guidance;
    no image-search, download, or rights-check API is called.
11. Relevant unit, contract, controller-boundary, persistence, migration,
    Angular component, build, and packaged-runtime tests pass in every affected
    repository.
12. Automated verification makes no paid external media-generation call.

## 12. Non-Goals

- editing storyboard fields;
- autosave or collaborative editing;
- automatic Google Images or other web-image search;
- image download, storage, rights validation, or attribution management;
- generated images, generated videos, TTS, rendering, or media export;
- provider-specific prompt optimization;
- a downloadable PDF, DOCX, JSON, or project file;
- changing research, topic-discovery, candidate-generation, or reference-analysis
  product behavior beyond the data needed by storyboard generation.
