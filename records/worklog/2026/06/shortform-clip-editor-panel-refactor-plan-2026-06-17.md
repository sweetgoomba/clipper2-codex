# Shortform Clip Editor Panel Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the center clip/narration editor UI from `ShortformWorkflowPageComponent` without changing template selection, preview playback, caption TTS, or render payload behavior.

**Architecture:** Add a presentational `ShortformLegacyClipEditorPanelComponent` under `src/features/shortform/components/workflow`. The page continues to own project state, TTS orchestration, media failure tracking, and preview seek/playback requests; the child component receives immutable inputs and emits typed user actions.

**Tech Stack:** Angular standalone components, Angular signals `input`/`output`, Angular CDK drag-drop, Jasmine/Karma.

---

### Task 1: Add Clip Editor Panel Contract Tests

**Files:**
- Create: `src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.spec.ts`

- [x] **Step 1: Write the failing test**

Create a component spec that imports `ShortformLegacyClipEditorPanelComponent`, passes a sample project with two clips and narration lines, and verifies:
- the center title renders as `클립 편집`
- clip thumbnails and durations render
- focus on a narration input emits `{ clip, lineId, text }`
- blur emits `{ clipId, lineId, event }`
- line add/delete/play buttons emit their ids
- add clip button emits
- media image error emits the failed URL

- [x] **Step 2: Run test to verify it fails**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.spec.ts'
```

Expected: FAIL because the component file does not exist yet.

### Task 2: Implement Clip Editor Panel

**Files:**
- Create: `src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.ts`
- Create: `src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.html`
- Create: `src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.scss`
- Modify: `src/features/shortform/pages/shortform-workflow-page.component.ts`
- Modify: `src/features/shortform/pages/shortform-workflow-page.component.html`
- Modify: `src/features/shortform/pages/shortform-workflow-page.component.scss`

- [x] **Step 1: Write minimal implementation**

Move the center panel markup from the page template into the new child component. Keep method bodies minimal: helper methods compute media URL, video state, and duration; event handlers emit output payloads without mutating project state.

- [x] **Step 2: Wire the page**

Replace the center panel markup with:
```html
<app-shortform-legacy-clip-editor-panel
  [project]="currentProject"
  [failedMediaUrls]="failedMediaUrls()"
  [synthesizingLineId]="synthesizingLineId()"
  (clipSelected)="selectPreviewClip($event)"
  (lineFocused)="selectPreviewLineById($event.clip, $event.lineId, $event.text)"
  (lineTextBlurred)="updateNarrationLineText($event.clipId, $event.lineId, $event.event)"
  (lineEnterPressed)="handleNarrationLineEnter($event)"
  (lineAddedAfter)="addNarrationLineAfter($event.clipId, $event.lineId)"
  (lineDeleted)="deleteNarrationLine($event.clipId, $event.lineId)"
  (linePlaybackRequested)="playPreviewLine($event)"
  (clipDeleted)="deleteClip($event)"
  (clipDropped)="onClipDrop($event)"
  (lineDropped)="onNarrationLineDrop($event.clipId, $event.event)"
  (clipAdded)="addClip()"
  (mediaFailed)="markMediaFailed($event)"
/>
```

- [x] **Step 3: Move styles**

Move clip/list/line/button/drag styles from the page stylesheet into the child stylesheet. Leave only page layout, empty state, right panel, and preview sizing styles in the page stylesheet.

- [x] **Step 4: Run tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/components/workflow/shortform-legacy-clip-editor-panel.component.spec.ts'
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts'
```

Expected: PASS.

### Task 3: Verify Refactor Safety

**Files:**
- Modify only if verification reveals a regression in files changed by Task 2.

- [x] **Step 1: Run full shortform tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/**/*.spec.ts'
```

Expected: PASS.

- [x] **Step 2: Run build**

Run:
```bash
npm run build
```

Expected: PASS.

- [x] **Step 3: Run diff check**

Run:
```bash
git diff --check
```

Expected: no output.
