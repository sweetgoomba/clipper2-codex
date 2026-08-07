# Shortform Director Storyboard-Only Design

Date: 2026-08-04
Status: Implemented locally; awaiting review and integration decision

## Implementation Result

Implemented on the uncommitted local branch
`feat/shortform-director-storyboard-only` in Web API, Desktop Nest, and Angular.
The user flow now ends after the selected candidate's read-only storyboard is
generated, persisted, reloaded, and displayed.

Generated-media, asset preparation, narration synthesis, scene mutation,
rendering, output, and vault runtime paths were removed. The persisted
`ShortformDirectorProject` compatibility shape remains unchanged as designed.

Automated verification on 2026-08-04:

- Web API: 116 suites / 986 tests passed; production build passed.
- Desktop Nest: clean production build passed; 505 Director tests and 16
  directly affected `ProjectsService` tests passed.
- Angular: 1,720 tests passed; production build passed.
- Desktop Nest's repository-wide legacy suite is not green independently of
  this boundary. Current failures are in unrelated legacy shortform
  authentication fixtures and variation/TTS mocks. They are not included in
  the storyboard-only change.
- No external paid provider call was made.

## 1. Goal

Create a new branch from `feat/shortform-director-foundation` that preserves the
existing Shortform Director flow through video candidate generation and
candidate-specific storyboard creation, then removes every downstream path that
prepares media or produces a rendered video.

The new shared branch name is:

`feat/shortform-director-storyboard-only`

The implementation touches:

- `web/clipper_web_api`
- `desktop/clipper_nestjs`
- `desktop/clipper_angular`

`web/clipper_web_admin`, `desktop/clipper_electron`, and
`desktop/clipper_python` stay unchanged.

## 2. Product Boundary

The retained user flow is:

```text
operating profile
  → research
  → optional reference analysis
  → research topic
  → at least 10 video candidates
  → select one candidate
  → approve storyboard-generation cost
  → generate VideoPlan
  → generate scene media decisions
  → compile and persist ShortformDirectorProject
  → display the storyboard
```

The boundary ends when the compiled `ShortformDirectorProject` is persisted and
displayed. The first version of the storyboard screen is read-only.

The following capabilities are removed:

- asset search, acquisition, upload, binding, rights confirmation, and automatic
  preparation
- generated image and generated video execution
- scene layer regeneration and project-wide production regeneration
- narration preset selection, TTS synthesis, and narration regeneration
- render recipe and render-input staging
- render jobs, retry, cancellation, output download, and vault publication
- completed-video and output screens

## 3. Compatibility Decision

The existing `ShortformDirectorProject` model, candidate-production pipeline,
project repository, compiler, and stored JSON remain unchanged.

This deliberately keeps existing fields such as `assetPack`,
`narrationAudio`, and production readiness data in persisted projects. They are
compatibility fields only:

- the storyboard-only application does not execute them;
- the default UI does not display them;
- no new migration rewrites existing local JSON;
- existing successful candidate-production results remain readable.

Internal names such as `candidate-production` and `ShortformDirectorProject`
also remain to keep the change surgical. User-facing text uses “스토리보드”.

## 4. Repository Changes

### 4.1 Desktop Angular

The existing profile, research, reference analysis, topic, candidate, run, and
artifact behavior remains unchanged.

The candidate action changes from video production to storyboard creation or
viewing. The current production page is reduced to:

- storyboard preflight and cost approval;
- generation progress and retryable generation failure;
- title, expected duration, and ordered scenes;
- each scene's visual intent, narration, captions, and planned media treatment.

The page does not show production capability catalogs, production state,
provider internals, artifact inspectors, asset readiness, layer regeneration,
narration controls, render controls, or output controls.

The `/shortform/director/outputs` route and completed-video navigation are
removed. The current production route becomes the contextual storyboard route.
The existing upstream screens and their navigation remain otherwise unchanged.

### 4.2 Desktop Nest

The candidate-production preflight, run, inference, compiler, result, project,
and artifact lineage required to create a storyboard remain.

The project planning boundary remains available through VideoPlan. Project
storage and read APIs required by candidate-production and storyboard display
remain.

Controllers, providers, storage adapters, and tests dedicated to these
downstream concerns are removed:

- automatic asset preparation and asset mutation;
- generated media execution;
- scene and layer production regeneration;
- narration synthesis and regeneration;
- render recipe and render-input staging;
- Motion Canvas render execution;
- render operations and output storage;
- vault publication.

Imports of `TtsSynthesisModule`, `JobsModule`, or `PluginsModule` are removed
from `ShortformDirectorModule` when no retained provider requires them.
`SourcesModule` remains because research and reference processing still need
source integrations.

Deleted HTTP endpoints must no longer be registered. Requests to those paths
return the normal Nest 404 response.

### 4.3 Web API

Research, source fetch, reference analysis, generic inference,
candidate-generation inference, `video-plan`, and `scene-media-decision`
capabilities remain.

The generated-media runtime and `/shortform-director/assets/generate` endpoint
are removed. Production capability source that is still used as an internal
inference model catalog may remain as non-routable shared code; its UI-facing
controller and application module registration are removed when no retained
caller needs them.

Credential administration remains unchanged because research, reference
analysis, candidate generation, and storyboard generation still use the same
Web API credential path.

## 5. Data and Cost Flow

Storyboard creation continues to use the existing candidate-production
preflight. The user approves the existing two-call maximum:

1. `video-plan`
2. `scene-media-decision`

The approval snapshot, provider credential revision, estimated cost, actual
provider usage artifacts, run manifest, compiler artifact, and lineage remain
unchanged.

No cost or operation is offered after the storyboard result succeeds.

## 6. Error Behavior

- Invalid candidate lineage, missing credentials, approval snapshot changes,
  provider unavailability, timeouts, and invalid inference output keep their
  current candidate-production behavior.
- A failed storyboard run remains inspectable and retryable through the existing
  candidate-production flow.
- There are no partial asset, narration, or render states because those
  operations no longer exist.
- Historical local projects that contain downstream production data remain
  readable, but the storyboard-only UI ignores that data.

## 7. Verification

The implementation is complete only when:

1. all three target repositories are based on the exact current
   `feat/shortform-director-foundation` heads;
2. candidate generation still returns at least ten candidates;
3. selecting a candidate can preflight, approve, generate, persist, reload, and
   display a storyboard;
4. no UI route or action can prepare assets, synthesize narration, render, or
   open completed outputs;
5. removed Desktop Nest and Web API endpoints return 404;
6. retained project JSON from the foundation branch still loads without
   migration;
7. targeted tests, full relevant test suites, and production builds pass in
   Web API, Desktop Nest, and Angular.

No external provider E2E call is part of automated verification. Any paid
provider E2E requires a separate cost review and explicit user approval.

## 8. Non-Goals

- renaming the complete internal production domain to storyboard terminology;
- changing the persisted `ShortformDirectorProject` schema;
- redesigning profile, research, reference, topic, candidate, run, or artifact
  screens;
- adding storyboard editing;
- adding a new persistent queue or notification system;
- changing credential administration;
- changing Electron packaging or Python plugins.
