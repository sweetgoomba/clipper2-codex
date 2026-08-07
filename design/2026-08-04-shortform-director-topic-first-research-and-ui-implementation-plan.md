# Shortform Director Topic-First Research and UI Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Make new research proceed directly from market-source normalization to topics, make topics and candidates the primary UI content, and preserve legacy reference-analysis data and storyboard-only behavior.

**Architecture:** Keep existing run/artifact persistence as the audit source of truth. Add read projections that aggregate topics and candidates across runs, add a topic-only reuse operation that consumes one stored normalization artifact, and adapt the Angular stores/pages to those projections. The Web API remains the inference boundary and receives updated candidate-generation instructions that no longer depend on reference patterns.

**Tech Stack:** NestJS, Angular standalone components/signals, TypeScript, local JSON repositories, Jest/Node test runner, Karma/Jasmine.

**Execution status:** Tasks 1–7 implemented. Relevant builds and tests passed;
see the design document's implementation notes for exact verification results
and the unrelated pre-existing Desktop Nest full-suite failures.

---

### Task 1: Make candidate inference autonomous from reference patterns

**Files:**

- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify if required by version validation: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify if required by version validation: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`

**Steps:**

1. Add a failing prompt test proving candidate generation accepts empty audience/reference inputs and explicitly asks for materially different hooks, formats, structures, promises, outlines, and CTAs.
2. Run the focused Web API prompt test and confirm the expected failure.
3. Update the candidate prompt/version with the smallest contract-compatible change.
4. Run the focused prompt and contract tests.

### Task 2: Include topic synthesis in research approval and complete new research without reference selection

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/research-cost-estimate.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research-discovery.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-cost-estimate.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

**Steps:**

1. Add failing tests proving the research estimate covers topic synthesis and that a newly started run publishes market-only topics without entering `awaiting_reference_selection`.
2. Run the focused estimate/orchestrator tests and confirm the intended failures.
3. Reuse the approved preflight snapshot during discovery, then invoke the existing market-only topic builder/publisher immediately after normalized evidence is persisted.
4. Keep legacy resume/reference-analysis methods intact for historical runs.
5. Run the focused Nest tests and ensure YouTube metadata remains part of source normalization.

### Task 3: Add topic-first research projections and stored-evidence topic regeneration

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.models.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-research.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-research.controller.ts`
- Add: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-topic-regeneration.dto.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-research-orchestrator.test.js`

**Steps:**

1. Add failing service/controller tests for:
   - aggregating all readable topics for one profile newest first with run metadata;
   - preflighting and starting topic regeneration from exactly one research run;
   - using the stored normalization artifact without invoking source collectors;
   - excluding existing topics and preserving the original research provenance.
2. Run the focused tests and confirm the missing projection/operation failures.
3. Add public topic-card and eligible-research-run projections containing focus keyword, date, run ID, topic/evidence counts, and readable summary.
4. Add a topic-synthesis-only approval/start path that validates the selected run and its stored normalized evidence.
5. Publish an additional immutable topic artifact associated with the source research run, without rewriting prior artifacts.
6. Run the focused research tests.

### Task 4: Support reference-free candidate validation and aggregate candidates per topic

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-validator.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-generation.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-candidate-generation.controller.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-validator.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-generation.test.js`

**Steps:**

1. Add failing tests proving empty reference/audience IDs are accepted when the grounded context has none, while unknown market-evidence IDs still fail.
2. Add failing tests for a topic-level candidate projection sorted newest first and duplicate exclusion across prior successful generation runs for that topic.
3. Run the focused tests and confirm the intended failures.
4. Make reference/audience requirements conditional on their availability and load prior candidate sets into duplicate validation.
5. Add a read endpoint returning candidates with generation-run metadata.
6. Run the focused candidate tests.

### Task 5: Replace the Ideas page run-first UI with a topic-first UI

**Files:**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-research.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-research.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-research.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-topic-list/research-topic-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-topic-list/research-topic-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-topic-list/research-topic-list.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/research-topic-list/research-topic-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/ideas-page/ideas-page.component.spec.ts`

**Steps:**

1. Add failing service/store/component/page tests for the aggregated topics, selected profile summary, topic metadata, research detail surface, and two-path `주제 추가 생성` flow.
2. Run the focused Angular tests and confirm the intended failures.
3. Add gateway/store calls for topic projections and one-run stored-evidence regeneration.
4. Render profile context and topics as the default page content; remove run/reference-selection controls from the new default page without deleting legacy components/services.
5. Implement the contextual research detail with human-readable report first and collapsed technical information.
6. Implement an exactly-one-run reuse selector plus the existing new-research keyword/preflight flow.
7. Run the focused Angular tests.

### Task 6: Replace the Candidates page run-first UI while preserving the full grid

**Files:**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-candidate.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-candidate.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-candidate.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-candidate.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-candidate.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-candidate.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/video-candidate-set/video-candidate-set.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/video-candidate-set/video-candidate-set.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/video-candidate-set/video-candidate-set.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/video-candidate-set/video-candidate-set.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.spec.ts`

**Steps:**

1. Add failing service/store/component/page tests for aggregated candidates, header provenance, `영상 후보 더 만들기`, and collapsed technical IDs.
2. Run the focused Angular tests and confirm the intended failures.
3. Load every successful candidate set for the selected research topic and render candidates newest first.
4. Preserve the existing `repeat(auto-fit, minmax(320px, 1fr))` grid and all current candidate content/actions.
5. Add generation metadata/detail actions and move raw IDs into a closed `<details>` section.
6. Run the focused Angular tests.

### Task 7: Compatibility and full verification

**Files:**

- Modify: `.codex/design/2026-08-04-shortform-director-topic-first-research-and-ui-design.md`
- Modify if behavior discoveries require it: `.codex/todos/2026-08-04-shortform-director-research-and-shorts-analysis-followups.md`

**Steps:**

1. Run all relevant Web API tests and its production build.
2. Run the complete Desktop Nest test suite and production build.
3. Run the complete Angular test suite and production build.
4. Confirm no paid provider E2E call was made.
5. Confirm existing reference-analysis and storyboard-only boundary tests still pass.
6. Update the design status and implementation notes with verified behavior and any deliberately deferred item.
7. Review `git diff --check` and per-repository status. Do not commit or push unless the user asks.
