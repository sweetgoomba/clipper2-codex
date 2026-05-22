# Shortform Plugin Split Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the prompt-only Clipper Studio flow with a Clipper1 production workspace where `클립 생성` creates editable clips and only `숏폼 생성` enqueues final render.

**Architecture:** Phase 1 introduces a shared Shortform Core model and scheduler, then builds a Clipper1 workspace API/UI on top of it. Existing Clipper Studio render/provider code stays available through a compatibility adapter while workspace state moves out of completed project history until final render.

**Tech Stack:** Angular 19 standalone components, NestJS 10, TypeScript strict mode, JSON file repositories, existing ProjectManifest/RenderRecipe/video.render provider layer, Node 22 built-in `node:test` smoke tests for NestJS.

---

## Scope Check

This plan implements Phase 1 from `SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`.

Included:

- Clipper1 and Variation appear as separate virtual workflow plugins in catalog/navigation.
- Clipper1 gets a production workspace with left tabbed input, center clip editor, and right 9:16 preview/settings.
- `클립 생성` creates or regenerates editable clips inside a workspace.
- Manual start creates one blank clip without AI input.
- Clip media supports multiple assets and computed media slots.
- `숏폼 생성` promotes the workspace to a renderable project and starts a render job.
- Prompt submission no longer creates a completed project shell.

Excluded from Phase 1:

- Full Variation UI.
- Scrapling production integration.
- Full timeline editor with draggable frame-accurate edits.
- Rich paste image upload parity with every browser clipboard format.
- Windows packaging changes.

## File Structure

### NestJS

- Create `clipper_nestjs/src/shortform-core/shortform-core.dto.ts`
  - Shared `ShortformWorkspace`, `ShortformClip`, `NarrationLine`, `MediaPool`, `MediaSlot`, `RenderSettings`, and `PreviewTimeline` types.
- Create `clipper_nestjs/src/shortform-core/shortform-media-slot-scheduler.ts`
  - Deterministic media slot scheduling from clip duration and media pool.
- Create `clipper_nestjs/src/shortform-core/shortform-preview-timeline.ts`
  - Converts a workspace into preview timeline DTO used by Angular.
- Create `clipper_nestjs/src/shortform-core/index.ts`
  - Barrel exports for the new core.
- Create `clipper_nestjs/src/projects/dto/clipper1-workspace.dto.ts`
  - HTTP DTOs for workspace create, patch, clip generation, and render start.
- Create `clipper_nestjs/src/projects/clipper1-workspace-repository.ts`
  - JSON-backed workspace repository separate from completed project repository.
- Create `clipper_nestjs/src/projects/clipper1-workspace.service.ts`
  - Workspace orchestration: create, manual start, prompt draft, patch, promote to render project.
- Create `clipper_nestjs/src/projects/clipper1-workspace-project-promoter.ts`
  - Converts an editing workspace into the render-capable ProjectSnapshot/ProjectManifest compatibility shape only when `숏폼 생성` is requested.
- Create `clipper_nestjs/src/projects/clipper1-workspace.controller.ts`
  - REST API under `/projects/clipper1/workspaces`.
- Modify `clipper_nestjs/src/projects/projects.module.ts`
  - Register workspace service/repository/controller.
- Modify `clipper_nestjs/src/plugins/plugin-catalog.ts`
  - Add virtual `clipper1` and `variation` workflow plugins.
  - Keep old `clipper_studio` hidden from user-visible Angular store after Angular update.
- Modify `clipper_nestjs/src/project-manifest/dto/project-manifest.dto.ts`
  - Extend Clipper Studio compatibility detail with `mediaArtifactIds` and `mediaSlots`.
- Modify `clipper_nestjs/src/project-manifest/legacy-clipper1-render-recipe-provider.ts`
  - Build render timeline from `mediaSlots` when present, falling back to legacy one-media-per-clip behavior.
- Create `clipper_nestjs/test/shortform-media-slot-scheduler.test.js`
  - Node test for deterministic scheduling.
- Create `clipper_nestjs/test/clipper1-workspace-api.test.js`
  - API smoke test proving workspace creation does not add completed project history and final render does.

### Angular

- Create `clipper_angular/src/features/clipper-studio/models/shortform-workspace.ts`
  - Frontend DTOs matching NestJS workspace responses.
- Create `clipper_angular/src/features/clipper-studio/services/clipper1-workspace.service.ts`
  - Angular API client for workspace endpoints.
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.ts`
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.html`
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.scss`
  - Left tabbed input, `클립 생성`, manual start.
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.ts`
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.html`
- Create `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.scss`
  - Center clip/narration/media pool editor.
- Create `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.ts`
- Create `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.html`
- Create `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.scss`
  - Angular-native 9:16 full shortform preview.
- Modify `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.ts`
- Modify `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.html`
- Modify `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.scss`
  - Replace prompt-only form with 3-panel workspace.
- Modify `clipper_angular/src/core/plugin-status.service.ts`
  - User-visible plugins become `clipper1`, `variation`, `dance_highlight`, `dialog_highlight`.
- Modify `clipper_angular/src/app/app.routes.ts`
  - Keep `/clipper-studio` as Clipper1 workspace route for now, add redirect alias `/clipper1`.
- Modify `clipper_angular/src/shell/nav/nav.component.html`
  - Label production route as `Clipper1` or `제작` without implying prompt-only flow.
- Create `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts`
  - Smoke test for tabs, `클립 생성`, blank clip start, and no `/projects` navigation after clip generation.

### Documentation

- Modify `.codex/implementation/TASKS.md`
  - Track Phase 1 implementation slices.
- Modify `.codex/implementation/WORKLOG.md`
  - Record each completed task and verification.
- Modify `.codex/implementation/NEXT_SESSION_PROMPT.md`
  - Keep next session pointed at this plan while work is in progress.
- Append `.codex/session-logs/2026-05-06.log`
  - Record decisions, file edits, commands, and verification summaries.

## Task 1: Add Shortform Core DTOs and Media Slot Scheduler

**Files:**
- Create: `clipper_nestjs/src/shortform-core/shortform-core.dto.ts`
- Create: `clipper_nestjs/src/shortform-core/shortform-media-slot-scheduler.ts`
- Create: `clipper_nestjs/src/shortform-core/index.ts`
- Create: `clipper_nestjs/test/shortform-media-slot-scheduler.test.js`

- [x] **Step 1: Write the failing scheduler test**

Create `clipper_nestjs/test/shortform-media-slot-scheduler.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { ShortformMediaSlotScheduler } = require('../dist/shortform-core');

test('splits a long clip across multiple media assets deterministically', () => {
  const scheduler = new ShortformMediaSlotScheduler();
  const slots = scheduler.scheduleClip({
    clipId: 'clip.0',
    durationMs: 9000,
    mediaAssetIds: ['asset.a', 'asset.b', 'asset.c'],
    minSlotMs: 2500,
    seed: 'variation-a',
  });

  assert.equal(slots.length, 3);
  assert.deepEqual(
    slots.map((slot) => ({
      assetId: slot.assetId,
      startMs: slot.startMs,
      endMs: slot.endMs,
    })),
    [
      { assetId: 'asset.a', startMs: 0, endMs: 3000 },
      { assetId: 'asset.b', startMs: 3000, endMs: 6000 },
      { assetId: 'asset.c', startMs: 6000, endMs: 9000 },
    ],
  );
});

test('repeats available assets when the clip needs more slots than assets', () => {
  const scheduler = new ShortformMediaSlotScheduler();
  const slots = scheduler.scheduleClip({
    clipId: 'clip.1',
    durationMs: 11000,
    mediaAssetIds: ['asset.a', 'asset.b'],
    minSlotMs: 3000,
    seed: 'repeat',
  });

  assert.equal(slots.length, 4);
  assert.equal(slots[0].startMs, 0);
  assert.equal(slots.at(-1).endMs, 11000);
  assert.deepEqual(slots.map((slot) => slot.assetId), ['asset.a', 'asset.b', 'asset.a', 'asset.b']);
});

test('uses one slot when only one media asset exists', () => {
  const scheduler = new ShortformMediaSlotScheduler();
  const slots = scheduler.scheduleClip({
    clipId: 'clip.2',
    durationMs: 5200,
    mediaAssetIds: ['asset.only'],
    minSlotMs: 2500,
    seed: 'single',
  });

  assert.deepEqual(slots, [
    {
      id: 'slot.clip.2.0',
      clipId: 'clip.2',
      assetId: 'asset.only',
      startMs: 0,
      endMs: 5200,
      fit: 'cover',
    },
  ]);
});
```

- [x] **Step 2: Run the test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/shortform-media-slot-scheduler.test.js
```

Expected:

```text
not ok 1 - test/shortform-media-slot-scheduler.test.js
Error: Cannot find module '../dist/shortform-core'
```

- [x] **Step 3: Create core DTOs**

Create `clipper_nestjs/src/shortform-core/shortform-core.dto.ts`:

```ts
export type ShortformWorkflowKind = 'clipper1' | 'variation';
export type ShortformSourceMode = 'url' | 'prompt' | 'paste' | 'manual';
export type ShortformWorkspaceStatus =
  | 'editing'
  | 'generating_clips'
  | 'ready'
  | 'rendering'
  | 'rendered'
  | 'failed';

export interface ShortformNarrationLine {
  id: string;
  text: string;
  ttsArtifactId?: string;
  durationMs?: number;
}

export interface ShortformMediaAssetRef {
  artifactId: string;
  label?: string;
  kind?: 'media.image' | 'media.video' | string;
}

export interface ShortformMediaSlot {
  id: string;
  clipId: string;
  assetId: string;
  startMs: number;
  endMs: number;
  fit: 'cover' | 'contain' | 'fill';
  motionPreset?: string;
}

export interface ShortformClip {
  id: string;
  order: number;
  title?: string;
  narrationLines: ShortformNarrationLine[];
  mediaPool: {
    assets: ShortformMediaAssetRef[];
    selectionPolicy: 'sequential' | 'seeded-shuffle';
  };
  mediaSlots: ShortformMediaSlot[];
  searchHints: string[];
  durationMs: number;
}

export interface ShortformRenderSettings {
  ratio: '9:16';
  templateId?: string;
  ttsProviderId?: string;
  ttsSpeakerId?: string;
  ttsSpeed?: number;
  bgmArtifactId?: string;
  logoArtifactId?: string;
  logoText?: string;
  titleVisibility: {
    subTitle: boolean;
    mainTitle: boolean;
    bottomTitle: boolean;
    logo: boolean;
  };
}

export interface ShortformPreviewTimelineItem {
  id: string;
  clipId: string;
  assetId: string;
  startMs: number;
  endMs: number;
  text: string[];
}

export interface ShortformPreviewTimeline {
  durationMs: number;
  items: ShortformPreviewTimelineItem[];
}

export interface ShortformWorkspace {
  id: string;
  ownerSubjectId: string;
  workflowKind: ShortformWorkflowKind;
  status: ShortformWorkspaceStatus;
  title: string;
  source: {
    mode: ShortformSourceMode;
    text?: string;
    url?: string;
    html?: string;
    language?: string;
  };
  clips: ShortformClip[];
  renderSettings: ShortformRenderSettings;
  previewTimeline: ShortformPreviewTimeline;
  createdAt: string;
  updatedAt: string;
  lastError?: string;
  promotedProjectId?: string;
}
```

- [x] **Step 4: Implement deterministic scheduler**

Create `clipper_nestjs/src/shortform-core/shortform-media-slot-scheduler.ts`:

```ts
import { Injectable } from '@nestjs/common';
import type { ShortformMediaSlot } from './shortform-core.dto';

export interface ScheduleShortformClipRequest {
  clipId: string;
  durationMs: number;
  mediaAssetIds: string[];
  minSlotMs?: number;
  seed?: string;
}

@Injectable()
export class ShortformMediaSlotScheduler {
  scheduleClip(request: ScheduleShortformClipRequest): ShortformMediaSlot[] {
    const durationMs = Math.max(0, Math.round(request.durationMs));
    const assets = this.nonEmptyStrings(request.mediaAssetIds);
    if (durationMs === 0 || assets.length === 0) return [];

    const minSlotMs = Math.max(1000, Math.round(request.minSlotMs ?? 2500));
    const slotCount = assets.length === 1
      ? 1
      : Math.max(1, Math.ceil(durationMs / minSlotMs));
    const orderedAssets = this.assetOrder(assets, request.seed ?? request.clipId);
    const baseDuration = Math.floor(durationMs / slotCount);
    let cursor = 0;

    return Array.from({ length: slotCount }, (_, index) => {
      const endMs = index === slotCount - 1 ? durationMs : cursor + baseDuration;
      const slot: ShortformMediaSlot = {
        id: `slot.${request.clipId}.${index}`,
        clipId: request.clipId,
        assetId: orderedAssets[index % orderedAssets.length],
        startMs: cursor,
        endMs,
        fit: 'cover',
      };
      cursor = endMs;
      return slot;
    });
  }

  private assetOrder(assetIds: string[], seed: string): string[] {
    if (assetIds.length <= 1) return assetIds;
    const scored = assetIds.map((assetId) => ({
      assetId,
      score: this.hash(`${seed}:${assetId}`),
    }));
    return scored
      .sort((a, b) => a.score - b.score || a.assetId.localeCompare(b.assetId))
      .map((item) => item.assetId);
  }

  private hash(value: string): number {
    let hash = 0;
    for (let index = 0; index < value.length; index += 1) {
      hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
    }
    return hash;
  }

  private nonEmptyStrings(values: string[]): string[] {
    return values.map((value) => value.trim()).filter((value) => value.length > 0);
  }
}
```

- [x] **Step 5: Export core module**

Create `clipper_nestjs/src/shortform-core/index.ts`:

```ts
export * from './shortform-core.dto';
export * from './shortform-media-slot-scheduler';
```

- [x] **Step 6: Run scheduler test and build**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/shortform-media-slot-scheduler.test.js
```

Expected:

```text
ok 1 - test/shortform-media-slot-scheduler.test.js
```

- [x] **Step 7: Commit NestJS core slice**

Run:

```bash
cd clipper_nestjs
git status --short
git add src/shortform-core test/shortform-media-slot-scheduler.test.js
git commit -m "feat: add shortform core media slots"
```

## Task 2: Add Multi-Media Slots to RenderRecipe Builder

**Files:**
- Modify: `clipper_nestjs/src/project-manifest/dto/project-manifest.dto.ts`
- Modify: `clipper_nestjs/src/project-manifest/legacy-clipper1-render-recipe-provider.ts`
- Create: `clipper_nestjs/test/legacy-clipper1-render-media-slots.test.js`

- [x] **Step 1: Write the failing render recipe test**

Create `clipper_nestjs/test/legacy-clipper1-render-media-slots.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { LegacyClipper1RenderRecipeProvider } = require('../dist/project-manifest/legacy-clipper1-render-recipe-provider');

const templateCatalog = {
  require() {
    return {
      id: 'legacy.default',
      aspectRatio: 'full',
      canvas: { width: 1080, height: 1920, fps: 30 },
      defaultParams: { fit: 'cover', legacySettings: { bgm_volume: 0.15 } },
      legacy: { source: 'clipper1', templateRowId: 1, contentsRatio: 'full', rawSettings: {} },
    };
  },
  list() {
    return [{ id: 'legacy.default' }];
  },
  get() {
    return undefined;
  },
};

test('builds one timeline item per media slot when a clip has multiple media slots', () => {
  const provider = new LegacyClipper1RenderRecipeProvider(templateCatalog);
  const manifest = {
    schemaVersion: 'project-manifest.v1',
    projectId: 'project.1',
    workflow: { id: 'workflow.clipper1' },
    title: 'demo',
    status: 'completed',
    createdAt: '2026-05-06T00:00:00.000Z',
    updatedAt: '2026-05-06T00:00:00.000Z',
    sourceAssets: [],
    outputs: [{
      id: 'output.render',
      kind: 'render',
      label: 'render',
      artifactIds: ['artifact.render'],
      primaryArtifactId: 'artifact.render',
      createdAt: '2026-05-06T00:00:00.000Z',
      width: 1080,
      height: 1920,
    }],
    artifacts: [
      { id: 'asset.a', kind: 'media.image', uri: 'a.jpg', storage: 'local', createdAt: '2026-05-06T00:00:00.000Z' },
      { id: 'asset.b', kind: 'media.image', uri: 'b.jpg', storage: 'local', createdAt: '2026-05-06T00:00:00.000Z' },
      { id: 'tts.1', kind: 'audio.tts', uri: 'tts.m4a', storage: 'local', createdAt: '2026-05-06T00:00:00.000Z' },
      { id: 'artifact.render', kind: 'render.video', uri: 'main.mp4', storage: 'local', createdAt: '2026-05-06T00:00:00.000Z' },
    ],
    summary: {},
    detail: {
      kind: 'clipper_studio',
      input: { mode: 'prompt', text: 'demo' },
      editState: { titleVisibility: { subTitle: true, mainTitle: true, bottomTitle: true, logo: false } },
      clips: [{
        id: 'clip.0',
        order: 0,
        mediaArtifactId: 'asset.a',
        mediaArtifactIds: ['asset.a', 'asset.b'],
        mediaSlots: [
          { id: 'slot.clip.0.0', clipId: 'clip.0', assetId: 'asset.a', startMs: 0, endMs: 3000, fit: 'cover' },
          { id: 'slot.clip.0.1', clipId: 'clip.0', assetId: 'asset.b', startMs: 3000, endMs: 6000, fit: 'cover' },
        ],
        subtitles: [{ text: ['첫 문장'], durationSec: 6, ttsArtifactId: 'tts.1' }],
      }],
    },
    provenance: {},
  };

  const recipe = provider.buildForManifest(manifest, 'output.render');

  assert.equal(recipe.timeline.items.length, 2);
  assert.deepEqual(
    recipe.timeline.items.map((item) => ({
      id: item.id,
      clipId: item.clipId,
      sourceArtifactId: item.sourceArtifactId,
      startSec: item.startSec,
      durationSec: item.durationSec,
    })),
    [
      { id: 'timeline.clip.0.slot.0', clipId: 'clip.0', sourceArtifactId: 'asset.a', startSec: 0, durationSec: 3 },
      { id: 'timeline.clip.0.slot.1', clipId: 'clip.0', sourceArtifactId: 'asset.b', startSec: 3, durationSec: 3 },
    ],
  );
  assert.equal(recipe.tracks.subtitles[0].items[0].startSec, 0);
  assert.equal(recipe.tracks.subtitles[0].items[0].durationSec, 6);
});
```

- [x] **Step 2: Run the render recipe test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/legacy-clipper1-render-media-slots.test.js
```

Expected:

```text
not ok
AssertionError: Expected values to be strictly equal:
1 !== 2
```

- [x] **Step 3: Extend manifest detail types**

In `clipper_nestjs/src/project-manifest/dto/project-manifest.dto.ts`, extend each clip item inside `ClipperStudioProjectDetail.clips`:

```ts
    mediaArtifactId?: string;
    mediaArtifactIds?: string[];
    mediaSlots?: Array<{
      id: string;
      clipId: string;
      assetId: string;
      startMs: number;
      endMs: number;
      fit?: 'cover' | 'contain' | 'fill';
      motionPreset?: string;
    }>;
```

Keep existing fields and add these directly after `mediaArtifactId?: string;`.

- [x] **Step 4: Update render recipe clip planning**

In `clipper_nestjs/src/project-manifest/legacy-clipper1-render-recipe-provider.ts`, replace the single-item `clipPlansFor()` implementation with a version that expands slot plans:

```ts
interface LegacyClipper1ClipPlan {
  clip: ClipperStudioProjectDetail['clips'][number];
  timelineItem: RenderTimelineItem;
}
```

Keep the interface and replace only the body of `clipPlansFor()`:

```ts
  private clipPlansFor(
    manifest: ProjectManifest,
    detail: ClipperStudioProjectDetail,
    clips: ClipperStudioProjectDetail['clips'],
    fitParam: unknown,
  ): LegacyClipper1ClipPlan[] {
    let clipCursorSec = 0;
    const plans: LegacyClipper1ClipPlan[] = [];
    for (const clip of clips) {
      const clipDurationSec = this.clipDurationSec(clip);
      const slots = this.mediaSlotsFor(manifest, detail, clip, clipDurationSec, fitParam);
      for (const slot of slots) {
        const timelineItem: RenderTimelineItem = {
          id: slot.id,
          clipId: clip.id,
          sourceArtifactId: slot.sourceArtifactId,
          mediaType: slot.mediaType,
          startSec: clipCursorSec + slot.startOffsetSec,
          durationSec: slot.durationSec,
          fit: slot.fit,
        };
        plans.push({ clip, timelineItem });
      }
      clipCursorSec += clipDurationSec;
    }
    return plans;
  }
```

Add the helper below `clipPlansFor()`:

```ts
  private mediaSlotsFor(
    manifest: ProjectManifest,
    detail: ClipperStudioProjectDetail,
    clip: ClipperStudioProjectDetail['clips'][number],
    clipDurationSec: number,
    fitParam: unknown,
  ): Array<{
    id: string;
    sourceArtifactId: string;
    mediaType: RenderMediaType;
    startOffsetSec: number;
    durationSec: number;
    fit: RenderFitMode;
  }> {
    const fit = this.fitModeFor(fitParam) ?? 'cover';
    if (Array.isArray(clip.mediaSlots) && clip.mediaSlots.length > 0) {
      return clip.mediaSlots.map((slot, index) => {
        const artifact = this.artifactFor(manifest, slot.assetId);
        const startOffsetSec = Math.max(0, Math.round(slot.startMs) / 1000);
        const endOffsetSec = Math.max(startOffsetSec, Math.round(slot.endMs) / 1000);
        return {
          id: `timeline.${safeManifestId(clip.id)}.slot.${index}`,
          sourceArtifactId: slot.assetId,
          mediaType: this.mediaTypeFor(artifact),
          startOffsetSec,
          durationSec: Math.max(0, endOffsetSec - startOffsetSec),
          fit: slot.fit ?? fit,
        };
      }).filter((slot) => slot.durationSec > 0);
    }

    const mediaArtifactId = detail.editState.clipMediaArtifactIds?.[clip.id] ?? clip.mediaArtifactId;
    if (!mediaArtifactId) {
      throw new NotFoundException(`Clipper Studio clip has no media artifact: ${clip.id}`);
    }
    const artifact = this.artifactFor(manifest, mediaArtifactId);
    return [{
      id: `timeline.${safeManifestId(clip.id)}`,
      sourceArtifactId: mediaArtifactId,
      mediaType: this.mediaTypeFor(artifact),
      startOffsetSec: 0,
      durationSec: clipDurationSec,
      fit,
    }];
  }
```

- [x] **Step 5: Run render recipe and scheduler tests**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/shortform-media-slot-scheduler.test.js test/legacy-clipper1-render-media-slots.test.js
```

Expected:

```text
ok 1 - test/shortform-media-slot-scheduler.test.js
ok 2 - test/legacy-clipper1-render-media-slots.test.js
```

- [x] **Step 6: Commit render slot slice**

Run:

```bash
cd clipper_nestjs
git status --short
git add src/project-manifest/dto/project-manifest.dto.ts src/project-manifest/legacy-clipper1-render-recipe-provider.ts test/legacy-clipper1-render-media-slots.test.js
git commit -m "feat: render shortform media slots"
```

## Task 3: Add Clipper1 Workspace API Separate From Project History

**Files:**
- Create: `clipper_nestjs/src/projects/dto/clipper1-workspace.dto.ts`
- Create: `clipper_nestjs/src/projects/clipper1-workspace-repository.ts`
- Create: `clipper_nestjs/src/projects/clipper1-workspace.service.ts`
- Create: `clipper_nestjs/src/projects/clipper1-workspace.controller.ts`
- Modify: `clipper_nestjs/src/projects/projects.module.ts`
- Modify: `clipper_nestjs/src/plugins/plugin-catalog.ts`
- Create: `clipper_nestjs/test/clipper1-workspace-api.test.js`

Execution note:

- Task 3 implements workspace create/list/get/update/clip generation only.
- `clipper1-workspace-project-promoter.ts` and `/render-jobs` endpoint move to Task 6 so Task 3 does not introduce an unused render method.

- [x] **Step 1: Write API smoke test**

Create `clipper_nestjs/test/clipper1-workspace-api.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { mkdtemp, rm } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join } = require('node:path');

async function withServer(fn) {
  const dataDir = await mkdtemp(join(tmpdir(), 'clipper1-workspace-'));
  const port = 19131;
  const child = spawn(process.execPath, ['dist/main.js'], {
    cwd: process.cwd(),
    env: { ...process.env, PORT: String(port), CLIPPER_DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  try {
    await waitForHealth(port);
    await fn(`http://127.0.0.1:${port}`);
  } finally {
    child.kill('SIGTERM');
    await new Promise((resolve) => child.once('exit', resolve));
    await rm(dataDir, { recursive: true, force: true });
  }
}

async function waitForHealth(port) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error('server did not start');
}

async function json(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(`${response.status} ${JSON.stringify(body)}`);
  }
  return body;
}

test('manual workspace creates a blank clip without creating completed project history', async () => {
  await withServer(async (baseUrl) => {
    const created = await json(await fetch(`${baseUrl}/projects/clipper1/workspaces`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mode: 'manual', title: '수동 제작' }),
    }));
    assert.equal(created.workflowKind, 'clipper1');
    assert.equal(created.status, 'editing');
    assert.equal(created.clips.length, 1);
    assert.equal(created.clips[0].narrationLines.length, 1);

    const projects = await json(await fetch(`${baseUrl}/projects`));
    assert.equal(projects.length, 0);
  });
});

test('prompt workspace clip generation stays in workspace until render is requested', async () => {
  await withServer(async (baseUrl) => {
    const created = await json(await fetch(`${baseUrl}/projects/clipper1/workspaces`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mode: 'prompt', title: '축제 추천', prompt: '서울 근교 축제 top5', language: 'ko' }),
    }));

    const generated = await json(await fetch(`${baseUrl}/projects/clipper1/workspaces/${created.id}/clips`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({}),
    }));

    assert.equal(generated.status, 'ready');
    assert.ok(generated.clips.length >= 1);
    assert.ok(generated.previewTimeline.durationMs > 0);

    const projects = await json(await fetch(`${baseUrl}/projects`));
    assert.equal(projects.length, 0);
  });
});
```

- [x] **Step 2: Run API smoke test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/clipper1-workspace-api.test.js
```

Expected:

```text
not ok
Error: 404
```

- [x] **Step 3: Add workspace DTOs**

Create `clipper_nestjs/src/projects/dto/clipper1-workspace.dto.ts`:

```ts
import type { ShortformWorkspace } from '../../shortform-core';

export interface CreateClipper1WorkspaceRequest {
  mode: 'manual' | 'prompt' | 'url' | 'paste';
  title?: string;
  prompt?: string;
  url?: string;
  text?: string;
  html?: string;
  language?: string;
}

export interface UpdateClipper1WorkspaceRequest {
  title?: string;
  clips?: ShortformWorkspace['clips'];
  renderSettings?: Partial<ShortformWorkspace['renderSettings']>;
}

export interface GenerateClipper1WorkspaceClipsRequest {
  regenerate?: boolean;
}

```

- [x] **Step 4: Implement JSON workspace repository**

Create `clipper_nestjs/src/projects/clipper1-workspace-repository.ts`:

```ts
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import type { ShortformWorkspace } from '../shortform-core';

interface StoreFile {
  version: 1;
  workspaces: ShortformWorkspace[];
}

export abstract class Clipper1WorkspaceRepository {
  abstract list(ownerSubjectId: string): Promise<ShortformWorkspace[]>;
  abstract get(workspaceId: string): Promise<ShortformWorkspace | null>;
  abstract upsert(workspace: ShortformWorkspace): Promise<ShortformWorkspace>;
}

@Injectable()
export class JsonClipper1WorkspaceRepository extends Clipper1WorkspaceRepository {
  private loaded = false;
  private readonly workspaces = new Map<string, ShortformWorkspace>();
  private readonly storePath: string;

  constructor(config: ConfigService) {
    super();
    const dataRoot = config.get<string>('CLIPPER_DATA_DIR') ?? join(process.cwd(), '.clipper_data');
    this.storePath = join(dataRoot, 'clipper1', 'workspaces.json');
  }

  async list(ownerSubjectId: string): Promise<ShortformWorkspace[]> {
    await this.ensureLoaded();
    return [...this.workspaces.values()]
      .filter((workspace) => workspace.ownerSubjectId === ownerSubjectId)
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  }

  async get(workspaceId: string): Promise<ShortformWorkspace | null> {
    await this.ensureLoaded();
    return this.workspaces.get(workspaceId) ?? null;
  }

  async upsert(workspace: ShortformWorkspace): Promise<ShortformWorkspace> {
    await this.ensureLoaded();
    this.workspaces.set(workspace.id, workspace);
    await this.flush();
    return workspace;
  }

  private async ensureLoaded(): Promise<void> {
    if (this.loaded) return;
    try {
      const parsed = JSON.parse(await readFile(this.storePath, 'utf-8')) as StoreFile;
      for (const workspace of parsed.workspaces ?? []) {
        this.workspaces.set(workspace.id, workspace);
      }
    } catch {}
    this.loaded = true;
  }

  private async flush(): Promise<void> {
    await mkdir(dirname(this.storePath), { recursive: true });
    await writeFile(
      this.storePath,
      JSON.stringify({ version: 1, workspaces: [...this.workspaces.values()] }, null, 2),
      'utf-8',
    );
  }
}
```

- [x] **Step 5: Implement workspace service**

Create `clipper_nestjs/src/projects/clipper1-workspace.service.ts`.

Use this exact public surface:

```ts
@Injectable()
export class Clipper1WorkspaceService {
  constructor(
    private readonly repository: Clipper1WorkspaceRepository,
    private readonly scriptGenerator: ClipperStudioScriptGenerator,
    private readonly scheduler: ShortformMediaSlotScheduler,
  ) {}

  list(auth: AuthContext): Promise<ShortformWorkspace[]>;
  create(request: CreateClipper1WorkspaceRequest, auth: AuthContext): Promise<ShortformWorkspace>;
  get(workspaceId: string, auth: AuthContext): Promise<ShortformWorkspace>;
  update(workspaceId: string, request: UpdateClipper1WorkspaceRequest, auth: AuthContext): Promise<ShortformWorkspace>;
  generateClips(workspaceId: string, request: GenerateClipper1WorkspaceClipsRequest, auth: AuthContext): Promise<ShortformWorkspace>;
}
```

Implementation rules:

- `create({ mode: 'manual' })` returns one blank clip:

```ts
{
  id: 'clip.0',
  order: 0,
  title: '클립 1',
  narrationLines: [{ id: 'line.clip.0.0', text: '', durationMs: 3000 }],
  mediaPool: { assets: [], selectionPolicy: 'seeded-shuffle' },
  mediaSlots: [],
  searchHints: [],
  durationMs: 3000,
}
```

- `create({ mode: 'prompt' })` stores source text but creates no project history.
- `generateClips()` calls existing `ClipperStudioScriptGenerator.generate()`, maps each draft clip to `ShortformClip`, and computes empty media slots until assets exist.
- [x] **Step 6: Implement workspace controller**

Create `clipper_nestjs/src/projects/clipper1-workspace.controller.ts`:

```ts
import { Body, Controller, Get, Headers, Param, Patch, Post } from '@nestjs/common';
import type { IncomingHttpHeaders } from 'node:http';
import { AuthContextService } from '../auth/auth-context.service';
import type { ShortformWorkspace } from '../shortform-core';
import {
  CreateClipper1WorkspaceRequest,
  GenerateClipper1WorkspaceClipsRequest,
  UpdateClipper1WorkspaceRequest,
} from './dto/clipper1-workspace.dto';
import { Clipper1WorkspaceService } from './clipper1-workspace.service';

@Controller('projects/clipper1/workspaces')
export class Clipper1WorkspaceController {
  constructor(
    private readonly workspaces: Clipper1WorkspaceService,
    private readonly authContext: AuthContextService,
  ) {}

  @Get()
  list(@Headers() headers: IncomingHttpHeaders): Promise<ShortformWorkspace[]> {
    return this.authContext.fromHttpHeaders(headers).then((auth) => this.workspaces.list(auth));
  }

  @Post()
  create(
    @Body() body: CreateClipper1WorkspaceRequest,
    @Headers() headers: IncomingHttpHeaders,
  ): Promise<ShortformWorkspace> {
    return this.authContext.fromHttpHeaders(headers).then((auth) => this.workspaces.create(body, auth));
  }

  @Get(':workspaceId')
  get(
    @Param('workspaceId') workspaceId: string,
    @Headers() headers: IncomingHttpHeaders,
  ): Promise<ShortformWorkspace> {
    return this.authContext.fromHttpHeaders(headers).then((auth) => this.workspaces.get(workspaceId, auth));
  }

  @Patch(':workspaceId')
  update(
    @Param('workspaceId') workspaceId: string,
    @Body() body: UpdateClipper1WorkspaceRequest,
    @Headers() headers: IncomingHttpHeaders,
  ): Promise<ShortformWorkspace> {
    return this.authContext.fromHttpHeaders(headers).then((auth) => this.workspaces.update(workspaceId, body, auth));
  }

  @Post(':workspaceId/clips')
  generateClips(
    @Param('workspaceId') workspaceId: string,
    @Body() body: GenerateClipper1WorkspaceClipsRequest = {},
    @Headers() headers: IncomingHttpHeaders,
  ): Promise<ShortformWorkspace> {
    return this.authContext.fromHttpHeaders(headers).then((auth) => this.workspaces.generateClips(workspaceId, body, auth));
  }
}
```

- [x] **Step 7: Register providers and plugin catalog entries**

Modify `clipper_nestjs/src/projects/projects.module.ts`:

```ts
import { ShortformMediaSlotScheduler } from '../shortform-core';
import {
  Clipper1WorkspaceRepository,
  JsonClipper1WorkspaceRepository,
} from './clipper1-workspace-repository';
import { Clipper1WorkspaceController } from './clipper1-workspace.controller';
import { Clipper1WorkspaceService } from './clipper1-workspace.service';
```

Add `Clipper1WorkspaceController` to controllers and add providers:

```ts
Clipper1WorkspaceService,
ShortformMediaSlotScheduler,
{
  provide: Clipper1WorkspaceRepository,
  useClass: JsonClipper1WorkspaceRepository,
},
```

Modify `clipper_nestjs/src/plugins/plugin-catalog.ts`:

```ts
export const VIRTUAL_WORKFLOW_PLUGINS = new Set(['clipper1', 'variation']);
```

Add catalog entries for `clipper1` and `variation`. `clipper1` provides `workflow.clipper1`; `variation` provides `workflow.variation`. Both require shared shortform capabilities; `variation` description must state that the workflow surface is staged after Clipper1 Phase 1.

- [x] **Step 8: Run API smoke test**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/clipper1-workspace-api.test.js
```

Expected:

```text
ok 1 - test/clipper1-workspace-api.test.js
```

- [x] **Step 9: Commit workspace API slice**

Run:

```bash
cd clipper_nestjs
git status --short
git add src/shortform-core src/projects src/plugins/plugin-catalog.ts test/clipper1-workspace-api.test.js
git commit -m "feat: add clipper1 workspace flow"
```

## Task 4: Build Angular Clipper1 Workspace Shell

**Files:**
- Create: `clipper_angular/src/features/clipper-studio/models/shortform-workspace.ts`
- Create: `clipper_angular/src/features/clipper-studio/services/clipper1-workspace.service.ts`
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.ts`
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.html`
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.scss`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.ts`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.html`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.scss`
- Modify: `clipper_angular/src/core/plugin-status.service.ts`
- Modify: `clipper_angular/src/app/app.routes.ts`

- [x] **Step 1: Write Angular page smoke test**

Create `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts`:

```ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ClipperStudioPageComponent } from './clipper-studio-page.component';
import { Clipper1WorkspaceService } from '../services/clipper1-workspace.service';

class FakeClipper1WorkspaceService {
  created = false;
  async createWorkspace() {
    this.created = true;
    return {
      id: 'workspace.1',
      workflowKind: 'clipper1',
      status: 'editing',
      title: '수동 제작',
      source: { mode: 'manual' },
      clips: [{
        id: 'clip.0',
        order: 0,
        title: '클립 1',
        narrationLines: [{ id: 'line.clip.0.0', text: '', durationMs: 3000 }],
        mediaPool: { assets: [], selectionPolicy: 'seeded-shuffle' },
        mediaSlots: [],
        searchHints: [],
        durationMs: 3000,
      }],
      renderSettings: {
        ratio: '9:16',
        titleVisibility: { subTitle: true, mainTitle: true, bottomTitle: true, logo: false },
      },
      previewTimeline: { durationMs: 3000, items: [] },
      createdAt: '2026-05-06T00:00:00.000Z',
      updatedAt: '2026-05-06T00:00:00.000Z',
    };
  }
}

describe('ClipperStudioPageComponent', () => {
  let fixture: ComponentFixture<ClipperStudioPageComponent>;
  let service: FakeClipper1WorkspaceService;

  beforeEach(async () => {
    service = new FakeClipper1WorkspaceService();
    await TestBed.configureTestingModule({
      imports: [ClipperStudioPageComponent],
      providers: [
        provideRouter([]),
        { provide: Clipper1WorkspaceService, useValue: service },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ClipperStudioPageComponent);
    fixture.detectChanges();
  });

  it('shows tabbed input and clip generation action', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('URL');
    expect(text).toContain('프롬프트');
    expect(text).toContain('붙여넣기');
    expect(text).toContain('수동 시작');
    expect(text).toContain('클립 생성');
    expect(text).toContain('숏폼 생성');
  });
});
```

- [x] **Step 2: Run Angular smoke test and verify it fails**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
```

Expected:

```text
Error: Cannot find module '../services/clipper1-workspace.service'
```

- [x] **Step 3: Add frontend workspace models and service**

Create `clipper_angular/src/features/clipper-studio/models/shortform-workspace.ts` mirroring the NestJS DTO shape.

Create `clipper_angular/src/features/clipper-studio/services/clipper1-workspace.service.ts`:

```ts
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { BackendLocator } from '../../../core/backend-locator';
import type { ShortformWorkspace } from '../models/shortform-workspace';

export interface CreateClipper1WorkspaceRequest {
  mode: 'manual' | 'prompt' | 'url' | 'paste';
  title?: string;
  prompt?: string;
  url?: string;
  text?: string;
  html?: string;
  language?: string;
}

@Injectable({ providedIn: 'root' })
export class Clipper1WorkspaceService {
  private readonly http = inject(HttpClient);
  private readonly backend = inject(BackendLocator);

  async createWorkspace(request: CreateClipper1WorkspaceRequest): Promise<ShortformWorkspace> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(
      this.http.post<ShortformWorkspace>(`${base}/projects/clipper1/workspaces`, request),
    );
  }

  async generateClips(workspaceId: string): Promise<ShortformWorkspace> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(
      this.http.post<ShortformWorkspace>(`${base}/projects/clipper1/workspaces/${encodeURIComponent(workspaceId)}/clips`, {}),
    );
  }
}
```

- [x] **Step 4: Build input panel component**

Create the input panel as a focused component with:

- `activeTab = signal<'url' | 'prompt' | 'paste' | 'manual'>('prompt')`
- outputs:
  - `createClips = output<CreateClipper1WorkspaceRequest>()`
- visible tabs: `URL`, `프롬프트`, `붙여넣기`, `수동 시작`
- primary button text: `클립 생성`

The component must emit:

```ts
{ mode: 'prompt', prompt, title, language: 'ko' }
{ mode: 'url', url, title, language: 'ko' }
{ mode: 'paste', text, html, title, language: 'ko' }
{ mode: 'manual', title, language: 'ko' }
```

- [x] **Step 5: Replace page with 3-panel workspace shell**

Modify the page component:

- Remove `Router` navigation to `/projects` after clip generation.
- Use `Clipper1WorkspaceService`.
- Hold `workspace = signal<ShortformWorkspace | null>(null)`.
- `handleCreateClips(request)` creates workspace and, for non-manual modes, calls `generateClips(workspace.id)`.
- Keep the user on `/clipper-studio`.

The template must contain:

```html
<section class="workspace-grid">
  <app-clipper1-input-panel class="workspace-left" (createClips)="handleCreateClips($event)" />
  <section class="workspace-center">...</section>
  <section class="workspace-right">...</section>
</section>
```

- [x] **Step 6: Split plugin catalog visibility**

Modify `clipper_angular/src/core/plugin-status.service.ts`:

```ts
const PLUGIN_ROUTES: Record<string, string> = {
  clipper1: '/clipper-studio',
  variation: '/variation',
  dance_highlight: '/dance',
  dialog_highlight: '/dialog',
};

const KNOWN_PLUGINS = ['clipper1', 'variation', 'dance_highlight', 'dialog_highlight'];
```

Keep `clipper_studio` out of `USER_VISIBLE_PLUGINS`.

- [x] **Step 7: Add route alias**

Modify `clipper_angular/src/app/app.routes.ts`:

```ts
{
  path: 'clipper1',
  redirectTo: 'clipper-studio',
  pathMatch: 'full',
},
```

- [x] **Step 8: Run Angular checks**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
npm run build:electron -- --progress=false
```

Expected:

```text
TOTAL: 1 SUCCESS
Application bundle generation complete
```

- [x] **Step 9: Commit Angular workspace shell**

Run:

```bash
cd clipper_angular
git status --short
git add src/features/clipper-studio src/core/plugin-status.service.ts src/app/app.routes.ts
git commit -m "feat: add clipper1 workspace shell"
```

## Task 5: Add Clip Editor and 9:16 Preview Player

**Files:**
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.ts`
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.html`
- Create: `clipper_angular/src/features/clipper-studio/components/clipper1-clip-editor.component.scss`
- Create: `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.ts`
- Create: `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.html`
- Create: `clipper_angular/src/features/clipper-studio/components/shortform-preview-player.component.scss`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.*`

- [x] **Step 1: Extend page spec with editor and preview assertions**

Append to `clipper-studio-page.component.spec.ts`:

```ts
it('renders generated workspace clips and a 9:16 preview area', async () => {
  await fixture.componentInstance.handleCreateClips({ mode: 'manual', title: '수동 제작' });
  fixture.detectChanges();

  const text = fixture.nativeElement.textContent;
  expect(text).toContain('클립 1');
  expect(text).toContain('9:16');
  expect(text).toContain('렌더 전');
});
```

- [x] **Step 2: Run the spec and verify it fails**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
```

Expected:

```text
Expected ... to contain '클립 1'
```

- [x] **Step 3: Implement clip editor**

The editor must:

- Render each clip row with stable height and no nested cards.
- Show narration text input for each line.
- Show media pool count and slot count.
- Provide buttons for `클립 추가`, `삭제`, and `미디어 추가`.
- Emit a full `ShortformWorkspace` patch through `workspaceChange`.

- [x] **Step 4: Implement preview player**

The preview player must:

- Render a 9:16 stage with `aspect-ratio: 9 / 16`.
- Use `workspace.previewTimeline.items`.
- Show current item based on local `currentMs` signal.
- Provide play/pause and a range input.
- Show subtitles from current item text.
- Avoid real ffmpeg/browser encoding.

- [x] **Step 5: Wire editor and preview into page**

The page center uses:

```html
<app-clipper1-clip-editor
  [workspace]="workspace()"
  (workspaceChange)="workspace.set($event)"
/>
```

The page right uses:

```html
<app-shortform-preview-player [workspace]="workspace()" />
<button class="btn primary" type="button" [disabled]="!workspace()" (click)="startRender()">
  숏폼 생성
</button>
```

- [x] **Step 6: Run Angular checks**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
npm run build:electron -- --progress=false
```

Expected:

```text
TOTAL: 2 SUCCESS
Application bundle generation complete
```

- [x] **Step 7: Commit editor/preview slice**

Run:

```bash
cd clipper_angular
git status --short
git add src/features/clipper-studio
git commit -m "feat: preview and edit clipper1 workspace"
```

## Task 6: Connect `숏폼 생성` to Render Queue Only

**Files:**
- Modify: `clipper_nestjs/src/projects/clipper1-workspace.service.ts`
- Modify: `clipper_angular/src/features/clipper-studio/services/clipper1-workspace.service.ts`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.ts`
- Modify: `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.html`
- Modify: `.codex/implementation/TASKS.md`
- Modify: `.codex/implementation/WORKLOG.md`

- [x] **Step 1: Extend API smoke test for final render promotion**

Append to `clipper_nestjs/test/clipper1-workspace-api.test.js`:

```js
test('render request promotes workspace to project history and creates a render job', async () => {
  await withServer(async (baseUrl) => {
    const workspace = await json(await fetch(`${baseUrl}/projects/clipper1/workspaces`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mode: 'manual', title: '수동 제작' }),
    }));

    const renderResponse = await json(await fetch(`${baseUrl}/projects/clipper1/workspaces/${workspace.id}/render-jobs`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ dryRun: true }),
    }));

    assert.equal(renderResponse.workspace.promotedProjectId, renderResponse.project.projectId);
    assert.equal(renderResponse.renderJob.projectId, renderResponse.project.projectId);

    const projects = await json(await fetch(`${baseUrl}/projects`));
    assert.equal(projects.length, 1);
    assert.equal(projects[0].pluginName, 'clipper1');
  });
});
```

- [x] **Step 2: Run API smoke test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/clipper1-workspace-api.test.js
```

Expected:

```text
not ok
Error: 404
```

- [x] **Step 3: Implement render promotion**

In `Clipper1WorkspaceService.startRender()`:

- Validate workspace owner.
- Build a `ProjectSnapshot` only inside this method.
- Use `pluginName: 'clipper1'`.
- Build a ProjectManifest with:
  - `workflow.id: 'workflow.clipper1'`
  - `detail.kind: 'clipper_studio'` as Phase 1 compatibility detail
  - `clips[].mediaArtifactIds`
  - `clips[].mediaSlots`
  - `outputs[]` containing `output.clipper1.render.main`
- Call existing render job start path with `dryRun` respected.
- Update workspace status to `rendering` and store `promotedProjectId`.

- [x] **Step 4: Add Angular render client method**

In `Clipper1WorkspaceService` add:

```ts
async startRender(workspaceId: string, request: { dryRun?: boolean } = {}): Promise<{
  workspace: ShortformWorkspace;
  project: unknown;
  renderJob: unknown;
}> {
  const base = await this.backend.getBaseUrl();
  return firstValueFrom(
    this.http.post<{
      workspace: ShortformWorkspace;
      project: unknown;
      renderJob: unknown;
    }>(`${base}/projects/clipper1/workspaces/${encodeURIComponent(workspaceId)}/render-jobs`, request),
  );
}
```

- [x] **Step 5: Wire page `숏폼 생성`**

In the page:

- `startRender()` calls service `startRender(workspace.id, { dryRun: false })`.
- Shows render job progress label from response.
- Navigates to `/projects?project=<projectId>` only after `숏폼 생성` is clicked.

- [x] **Step 6: Run full Phase 1 checks**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/shortform-media-slot-scheduler.test.js test/legacy-clipper1-render-media-slots.test.js test/clipper1-workspace-api.test.js
```

Expected:

```text
ok 1 - test/shortform-media-slot-scheduler.test.js
ok 2 - test/legacy-clipper1-render-media-slots.test.js
ok 3 - test/clipper1-workspace-api.test.js
```

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
npm run build:electron -- --progress=false
```

Expected:

```text
TOTAL: 2 SUCCESS
Application bundle generation complete
```

- [x] **Step 7: Update docs**

Update:

- `.codex/implementation/TASKS.md`
- `.codex/implementation/WORKLOG.md`
- `.codex/implementation/NEXT_SESSION_PROMPT.md`
- `.codex/session-logs/2026-05-06.log`

Record:

- Workspace API prevents completed project history before render.
- `클립 생성` stays in workspace.
- `숏폼 생성` is the queue boundary.
- Multi-media slot render path is in place.
- Remaining Phase 2 work: URL ingestion, paste ingestion, richer template preview parity, Variation UI.

- [x] **Step 8: Commit render boundary slice**

Run:

```bash
cd clipper_nestjs
git status --short
git add src test
git commit -m "feat: enqueue clipper1 render from workspace"

cd ../clipper_angular
git status --short
git add src/features/clipper-studio
git commit -m "feat: start clipper1 render from workspace"
```

## Verification Summary

Required before calling Phase 1 complete:

```bash
cd clipper_nestjs
npm run build
node --test test/shortform-media-slot-scheduler.test.js test/legacy-clipper1-render-media-slots.test.js test/clipper1-workspace-api.test.js

cd ../clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts'
npm run build:electron -- --progress=false
```

Manual visual QA:

- Open `/clipper-studio`.
- Confirm left input tabs remain visible after clip generation.
- Confirm button label is `클립 생성`.
- Confirm manual start creates one blank clip.
- Confirm center editor allows clip/narration/media pool inspection.
- Confirm right preview is 9:16, not a longform layout.
- Confirm no completed project appears after `클립 생성`.
- Confirm project/render queue appears only after `숏폼 생성`.

## Plan Self-Review

- Spec coverage: Phase 1 covers plugin split visibility, tabbed input, `클립 생성`, manual blank clip, multi-media slot schema/render path, 9:16 preview, and final render queue boundary.
- Deferred spec items are explicitly outside Phase 1: full Variation UI, Scrapling production integration, rich paste parity, and full timeline editing.
- Type consistency: NestJS `ShortformWorkspace` is the canonical workspace DTO; Angular mirrors it. Render compatibility remains through `ClipperStudioProjectDetail` with added `mediaArtifactIds` and `mediaSlots`.
- Documentation path follows project preference under `.codex/implementation` rather than the Superpowers default plan directory.
