# Template Builder Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the active Template Builder product path with a simplified shortform template path that creates single-ratio `1:1` or `4:3` templates, stores a shared runtime spec, captures real 9:16 thumbnails, and exposes those templates to the shortform production page.

**Architecture:** Keep the existing Template Builder repository shape during migration, but add a shortform workflow projection on top of it. The backend owns the authoritative `ShortformTemplateRuntimeSpec`; Angular consumes the same shape for UI, thumbnail capture, and shortform template catalog mapping. The browser timeline preview engine is intentionally deferred until this runtime contract is stable.

**Tech Stack:** NestJS, Angular standalone components, TypeScript, Karma/Jasmine, Node test runner.

**Progress as of 2026-06-15:** Tasks 1-7 were implemented, committed, and focused verification passed. Final cross-repo review found one blocking integration gap before browser timeline preview work: Builder shortform presets are now exposed as `template-builder.v1`, but the backend render recipe/provider path still accepts only `simplified.v1`. Fix that render path before starting the browser timeline preview engine. Do not start Project-first / Plugin / Queue cleanup.

---

## Scope

This plan implements implementation-order items 2, 7, 8, and 9 from `.codex/design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md`.

Already completed before this plan:

- Archive branches for the full Template Builder exist in `clipper_angular`, `clipper_nestjs`, and `clipper_python`.
- Shortform generated `mainTitle1` and `mainTitle2` persistence is implemented.
- The shortform production page has a horizontal template picker and no legacy sub-title/bottom-title/logo controls.

Not included in this plan:

- Browser timeline preview engine.
- Render-engine preview.
- Project-first / Plugin / Queue cleanup.

---

## File Structure

### `clipper_nestjs`

- Create `src/template-builder/shortform-template-runtime-spec.ts`
  - Converts a `TemplateBuilderVariant` into `ShortformTemplateRuntimeSpec`.
  - Exposes `SHORTFORM_TEMPLATE_BUILDER_RATIOS`.
  - Exposes guards for shortform workflow templates.

- Modify `src/template-builder/dto/template-builder.dto.ts`
  - Adds `TemplateBuilderWorkflowKind`.
  - Adds optional `workflowKind` to `TemplateBuilderFamily`.
  - Adds optional `shortformRuntimeSpec` to `TemplateBuilderVariant`.
  - Adds `ShortformTemplateRuntimeSpec` interfaces.
  - Keeps existing legacy fields in `TemplateBuilderLayers` for storage compatibility, but shortform runtime specs must not expose legacy roles.

- Modify `src/template-builder/template-builder.service.ts`
  - Creates only one selected ratio for shortform templates.
  - Allows only `1:1` and `4:3` for shortform templates.
  - Rejects adding extra ratio variants to shortform templates.
  - Refreshes `shortformRuntimeSpec` after variant updates.
  - Keeps hidden legacy storage fields from leaking into runtime specs.

- Modify `src/template-builder/template-builder-validation.service.ts`
  - Adds shortform-specific validation that requires `contentArea`, `mainTitleLine1`, `mainTitleLine2`, and `subtitleText`.
  - Adds validation error if a shortform runtime spec contains `sub_title`, `bottom_title`, or `logo`.

- Modify `src/project-manifest/template-builder-published-preset-source.ts`
  - Emits shortform workflow presets for `workflowKind: 'shortform'` families.
  - Uses slots `clip_media`, `main_title1`, `main_title2`, `caption`, and `bgm`.
  - Includes `shortformTemplateRuntimeSpec` in `defaultParams`.
  - Uses `cardThumbnailUri` or sample thumbnail as the preview image.

- Test files:
  - Create `test/shortform-template-runtime-spec.test.js`.
  - Create `test/template-builder-shortform-mode.test.js`.
  - Create `test/template-builder-shortform-preset-source.test.js`.
  - Update `test/template-builder-validation.test.js` if validation helper exports change.

### `clipper_angular`

- Modify `src/features/template-builder/models/template-builder.ts`
  - Mirrors backend workflow/runtime spec types.
  - Adds `SHORTFORM_TEMPLATE_BUILDER_RATIOS`.

- Modify `src/features/template-builder/services/template-builder.service.ts`
  - Sends `workflowKind: 'shortform'` on create/clone.
  - Keeps old method names where practical to reduce UI churn.

- Modify `src/features/template-builder/pages/template-builder-page.component.ts`
  - Defaults create ratio to `1:1`.
  - Adds create-form ratio selection for `1:1` and `4:3`.
  - Removes active-product access to admin/system-template editing and legacy all-ratio sample render flow.
  - Treats each template as one selected ratio.

- Modify `src/features/template-builder/pages/template-builder-page.component.html`
  - Removes admin/system edit button.
  - Removes full multi-ratio sample render overlay.
  - Adds ratio selection to create/clone panels.

- Modify `src/features/template-builder/components/template-builder-editor.component.ts`
  - Shows only `1:1` and `4:3` ratios.
  - Removes variant creation for missing ratios.
  - Shows only content area, layout layers, main title line 1, main title line 2, and caption rows.
  - Maps existing `subtitleText` storage layer to public `caption`.

- Modify `src/features/template-builder/components/template-builder-workspace.component.html`
  - Renames `비율 슬롯` to `템플릿 비율`.
  - Removes missing-ratio slot affordances.
  - Shows one active ratio button or simple ratio label.

- Modify `src/features/template-builder/components/template-builder-inspector.component.html`
  - Hides logo controls.
  - Hides sub-title and bottom-title controls by virtue of filtered layer rows.
  - Renames subtitle text controls as caption.

- Modify `src/features/template-builder/services/template-builder-card-thumbnail.service.ts`
  - Captures 9:16 thumbnail from the rendered canvas for any shortform template.
  - Draws only layout/content/mainTitleLine1/mainTitleLine2/subtitleText.
  - Excludes sub-title, bottom-title, logo image, and logo text.

- Modify `src/features/shortform/models/shortform-project.ts`
  - Adds `runtimeSpec` to `ShortformTemplateCatalogItem`.

- Modify `src/features/shortform/services/shortform-project.service.ts`
  - Loads `workflow=workflow.shortform&source=template_builder.custom` first.
  - Falls back to `source=shortform.simplified` while no Builder-created templates exist.
  - Maps `defaultParams.shortformTemplateRuntimeSpec`.

- Test files:
  - Update `src/features/template-builder/pages/template-builder-page.component.spec.ts`.
  - Update `src/features/template-builder/components/template-builder-editor.component.spec.ts`.
  - Update `src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts`.
  - Update `src/features/shortform/pages/shortform-workflow-page.component.spec.ts`.
  - Update `src/features/shortform/services/shortform-project.service.spec.ts` or add one if missing coverage is in component tests only.

---

## Task 1: Backend Runtime Spec Contract

**Files:**

- Create: `clipper_nestjs/src/template-builder/shortform-template-runtime-spec.ts`
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Test: `clipper_nestjs/test/shortform-template-runtime-spec.test.js`

- [x] **Step 1: Write the failing runtime spec test**

Add `clipper_nestjs/test/shortform-template-runtime-spec.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');

test('shortform runtime spec exposes only media, main titles, caption, and audio', () => {
  const {
    createDefaultTemplateVariant,
  } = require('../dist/template-builder/dto/template-builder.dto');
  const {
    shortformTemplateRuntimeSpecForVariant,
  } = require('../dist/template-builder/shortform-template-runtime-spec');

  const variant = createDefaultTemplateVariant('custom.template.shortform', '1:1');
  variant.layers.subTitle.visible = true;
  variant.layers.bottomTitle.visible = true;
  variant.layers.logoImage.visible = true;
  variant.layers.logoText.visible = true;

  const spec = shortformTemplateRuntimeSpecForVariant(variant);

  assert.equal(spec.schemaVersion, 'shortform-template-runtime.v1');
  assert.equal(spec.templateId, variant.id);
  assert.equal(spec.ratio, '1:1');
  assert.equal(spec.thumbnail.captureRatio, '9:16');
  assert.deepEqual(Object.keys(spec.regions).sort(), [
    'caption',
    'clip_media',
    'main_title1',
    'main_title2',
  ]);
  assert.equal(JSON.stringify(spec).includes('sub_title'), false);
  assert.equal(JSON.stringify(spec).includes('bottom_title'), false);
  assert.equal(JSON.stringify(spec).includes('logo'), false);
});

test('shortform runtime spec rejects non-shortform ratios', () => {
  const {
    createDefaultTemplateVariant,
  } = require('../dist/template-builder/dto/template-builder.dto');
  const {
    shortformTemplateRuntimeSpecForVariant,
  } = require('../dist/template-builder/shortform-template-runtime-spec');

  const variant = createDefaultTemplateVariant('custom.template.legacy', '16:9');

  assert.throws(
    () => shortformTemplateRuntimeSpecForVariant(variant),
    /Shortform templates support only 1:1 or 4:3/,
  );
});
```

- [x] **Step 2: Run the failing test**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-template-runtime-spec.test.js
```

Expected: build fails or the test fails because `shortform-template-runtime-spec` does not exist.

- [x] **Step 3: Add backend DTO types**

In `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`, add near the ratio exports:

```ts
export const SHORTFORM_TEMPLATE_BUILDER_RATIOS = ['1:1', '4:3'] as const;
export type ShortformTemplateBuilderRatio = typeof SHORTFORM_TEMPLATE_BUILDER_RATIOS[number];
export type TemplateBuilderWorkflowKind = 'legacy' | 'shortform';
```

Add runtime spec interfaces after `TemplateBuilderContentArea`:

```ts
export interface ShortformTemplateRuntimeTextStyle {
  fontFamily: string;
  fontName?: string | null;
  fontSize: number;
  fontWeight?: number | string;
  lineHeight: number;
  letterSpacing: number;
  color: string;
  textAlign: 'left' | 'center' | 'right';
  backgroundColor: string | null;
  backgroundAlpha: number;
  paddingX: number;
  borderRadius: number;
  maxLines: number;
}

export interface ShortformTemplateRuntimeRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  anchor: 'top-left';
  zIndex: number;
}

export interface ShortformTemplateRuntimeMediaRegion extends ShortformTemplateRuntimeRegion {
  fit: 'cover' | 'contain' | 'fill';
  motionPreset?: string;
}

export interface ShortformTemplateRuntimeTextRegion extends ShortformTemplateRuntimeRegion {
  textStyle: ShortformTemplateRuntimeTextStyle;
}

export interface ShortformTemplateRuntimeSpec {
  schemaVersion: 'shortform-template-runtime.v1';
  templateId: string;
  ratio: ShortformTemplateBuilderRatio;
  canvas: {
    width: number;
    height: number;
    fps: number;
    backgroundColor: string;
  };
  thumbnail: {
    url?: string | null;
    captureRatio: '9:16';
  };
  regions: {
    clip_media: ShortformTemplateRuntimeMediaRegion;
    main_title1: ShortformTemplateRuntimeTextRegion;
    main_title2: ShortformTemplateRuntimeTextRegion;
    caption: ShortformTemplateRuntimeTextRegion;
  };
  audio: {
    ttsVolume: number;
    bgmVolume: number;
  };
}
```

Add optional fields:

```ts
export interface TemplateBuilderVariant {
  // existing fields
  shortformRuntimeSpec?: ShortformTemplateRuntimeSpec;
}

export interface TemplateBuilderFamily {
  // existing fields
  workflowKind?: TemplateBuilderWorkflowKind;
}

export interface CreateTemplateBuilderFamilyRequest {
  name: string;
  ratio: TemplateBuilderRatio;
  workflowKind?: TemplateBuilderWorkflowKind;
  cloneFromFamilyId?: string | null;
  cloneFromRatio?: TemplateBuilderRatio | null;
}
```

- [x] **Step 4: Add runtime spec projector**

Create `clipper_nestjs/src/template-builder/shortform-template-runtime-spec.ts`:

```ts
import type {
  ShortformTemplateBuilderRatio,
  ShortformTemplateRuntimeSpec,
  ShortformTemplateRuntimeTextStyle,
  TemplateBuilderMediaLayer,
  TemplateBuilderRatio,
  TemplateBuilderTextLayer,
  TemplateBuilderVariant,
} from './dto/template-builder.dto';

export const SHORTFORM_TEMPLATE_RUNTIME_SCHEMA_VERSION = 'shortform-template-runtime.v1' as const;
export const SHORTFORM_TEMPLATE_BUILDER_RATIOS: readonly ShortformTemplateBuilderRatio[] = ['1:1', '4:3'];

export function isShortformTemplateBuilderRatio(
  ratio: TemplateBuilderRatio | string | undefined,
): ratio is ShortformTemplateBuilderRatio {
  return ratio === '1:1' || ratio === '4:3';
}

export function shortformTemplateRuntimeSpecForVariant(
  variant: TemplateBuilderVariant,
  thumbnailUrl?: string | null,
): ShortformTemplateRuntimeSpec {
  if (!isShortformTemplateBuilderRatio(variant.ratio)) {
    throw new Error('Shortform templates support only 1:1 or 4:3');
  }

  return {
    schemaVersion: SHORTFORM_TEMPLATE_RUNTIME_SCHEMA_VERSION,
    templateId: variant.id,
    ratio: variant.ratio,
    canvas: {
      width: variant.outputSize.width,
      height: variant.outputSize.height,
      fps: 30,
      backgroundColor: variant.layers.layoutImage.backgroundColor ?? '#000000',
    },
    thumbnail: {
      url: thumbnailUrl ?? null,
      captureRatio: '9:16',
    },
    regions: {
      clip_media: {
        ...regionFor(variant.layers.contentArea, 10),
        fit: 'cover',
      },
      main_title1: {
        ...regionFor(variant.layers.mainTitleLine1, 20),
        textStyle: textStyleFor(variant.layers.mainTitleLine1, 1),
      },
      main_title2: {
        ...regionFor(variant.layers.mainTitleLine2, 21),
        textStyle: textStyleFor(variant.layers.mainTitleLine2, 1),
      },
      caption: {
        ...regionFor(variant.layers.subtitleText, 30),
        textStyle: textStyleFor(variant.layers.subtitleText, 2),
      },
    },
    audio: {
      ttsVolume: 1,
      bgmVolume: 0.18,
    },
  };
}

function regionFor(
  layer: TemplateBuilderTextLayer | TemplateBuilderMediaLayer,
  zIndex: number,
) {
  return {
    x: layer.x,
    y: layer.y,
    width: layer.width,
    height: layer.height,
    anchor: 'top-left' as const,
    zIndex,
  };
}

function textStyleFor(
  layer: TemplateBuilderTextLayer,
  maxLines: number,
): ShortformTemplateRuntimeTextStyle {
  return {
    fontFamily: layer.text.fontFamily,
    fontName: layer.text.fontName ?? null,
    fontSize: layer.text.fontSize,
    fontWeight: 700,
    lineHeight: layer.text.lineHeight,
    letterSpacing: layer.text.tracking,
    color: layer.text.color,
    textAlign: layer.align,
    backgroundColor: layer.box.enabled ? layer.box.color : null,
    backgroundAlpha: layer.box.enabled ? layer.box.alpha : 0,
    paddingX: layer.box.enabled ? layer.box.paddingX : 0,
    borderRadius: 4,
    maxLines,
  };
}
```

- [x] **Step 5: Run the runtime spec test**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-template-runtime-spec.test.js
```

Expected: both tests pass.

- [x] **Step 6: Commit**

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git add src/template-builder/dto/template-builder.dto.ts src/template-builder/shortform-template-runtime-spec.ts test/shortform-template-runtime-spec.test.js
git commit -m "feat: add shortform template runtime spec"
```

---

## Task 2: Backend Shortform Template Builder Mode

**Files:**

- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-validation.service.ts`
- Test: `clipper_nestjs/test/template-builder-shortform-mode.test.js`

- [x] **Step 1: Write failing service tests**

Create `clipper_nestjs/test/template-builder-shortform-mode.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { mkdtemp } = require('node:fs/promises');
const { join } = require('node:path');
const { tmpdir } = require('node:os');

test('shortform template creation stores one selected ratio and runtime spec', async () => {
  const { TemplateBuilderService } = require('../dist/template-builder/template-builder.service');
  const { JsonTemplateBuilderRepository } = require('../dist/template-builder/template-builder.repository');
  const { TemplateBuilderValidationService } = require('../dist/template-builder/template-builder-validation.service');
  const { TemplateBuilderSampleRenderService } = require('../dist/template-builder/template-builder-sample-render.service');

  const root = await mkdtemp(join(tmpdir(), 'clipper-shortform-template-builder-'));
  const config = { get: (key) => key === 'CLIPPER_DATA_DIR' ? root : undefined };
  const service = new TemplateBuilderService(
    new JsonTemplateBuilderRepository(config),
    new TemplateBuilderValidationService(),
    new TemplateBuilderSampleRenderService(config, { resolve: async () => null }),
  );

  const family = await service.createFamily({
    name: '숏폼 템플릿',
    ratio: '1:1',
    workflowKind: 'shortform',
  });

  assert.equal(family.workflowKind, 'shortform');
  assert.deepEqual(Object.keys(family.variants), ['1:1']);
  assert.equal(family.variants['1:1'].shortformRuntimeSpec.ratio, '1:1');
  assert.equal(family.variants['1:1'].shortformRuntimeSpec.regions.caption.textStyle.maxLines, 2);
});

test('shortform template mode rejects unsupported ratios and additional variants', async () => {
  const { TemplateBuilderService } = require('../dist/template-builder/template-builder.service');
  const { JsonTemplateBuilderRepository } = require('../dist/template-builder/template-builder.repository');
  const { TemplateBuilderValidationService } = require('../dist/template-builder/template-builder-validation.service');
  const { TemplateBuilderSampleRenderService } = require('../dist/template-builder/template-builder-sample-render.service');

  const root = await mkdtemp(join(tmpdir(), 'clipper-shortform-template-builder-ratio-'));
  const config = { get: (key) => key === 'CLIPPER_DATA_DIR' ? root : undefined };
  const service = new TemplateBuilderService(
    new JsonTemplateBuilderRepository(config),
    new TemplateBuilderValidationService(),
    new TemplateBuilderSampleRenderService(config, { resolve: async () => null }),
  );

  await assert.rejects(
    () => service.createFamily({ name: '잘못된 비율', ratio: '16:9', workflowKind: 'shortform' }),
    /숏폼 템플릿은 1:1 또는 4:3만 지원합니다/,
  );

  const family = await service.createFamily({ name: '숏폼', ratio: '4:3', workflowKind: 'shortform' });

  await assert.rejects(
    () => service.createVariant(family.id, '1:1', {}),
    /숏폼 템플릿은 하나의 비율만 가질 수 있습니다/,
  );
});
```

- [x] **Step 2: Run failing tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-shortform-mode.test.js
```

Expected: tests fail because service does not handle `workflowKind: 'shortform'`.

- [x] **Step 3: Implement shortform mode in service**

In `clipper_nestjs/src/template-builder/template-builder.service.ts`, import:

```ts
import {
  isShortformTemplateBuilderRatio,
  shortformTemplateRuntimeSpecForVariant,
} from './shortform-template-runtime-spec';
```

Add helper methods inside `TemplateBuilderService`:

```ts
  private isShortformFamily(family: Pick<TemplateBuilderFamily, 'workflowKind'>): boolean {
    return family.workflowKind === 'shortform';
  }

  private requireShortformRatio(ratio: TemplateBuilderRatio): void {
    if (!isShortformTemplateBuilderRatio(ratio)) {
      throw new BadRequestException('숏폼 템플릿은 1:1 또는 4:3만 지원합니다.');
    }
  }

  private withShortformRuntimeSpec(
    variant: TemplateBuilderVariant,
    cardThumbnailUri?: string | null,
  ): TemplateBuilderVariant {
    if (!isShortformTemplateBuilderRatio(variant.ratio)) return variant;
    return {
      ...variant,
      shortformRuntimeSpec: shortformTemplateRuntimeSpecForVariant(variant, cardThumbnailUri),
    };
  }
```

Update `createFamily()`:

```ts
    const workflowKind = request.workflowKind === 'shortform' ? 'shortform' : 'legacy';
    if (workflowKind === 'shortform') {
      this.requireShortformRatio(request.ratio);
    }
```

Replace the unconditional `for (const ratio of TEMPLATE_BUILDER_RATIOS)` loop with:

```ts
    const ratios = workflowKind === 'shortform'
      ? [request.ratio]
      : TEMPLATE_BUILDER_RATIOS;
    for (const ratio of ratios) {
      const sourceVariant = baseline.variants[ratio];
      const baseVariant = sourceVariant
        ? createVariantFromNewTemplateBaseline(sourceVariant, familyId, ratio, now)
        : createDefaultTemplateVariant(familyId, ratio, now);
      const variant = applyFamilyCommonStylesToVariant(baseVariant, baseline.commonStyles);
      const prepared = prepareClonedVariant(variant, this.validation, now);
      variants[ratio] = workflowKind === 'shortform'
        ? this.withShortformRuntimeSpec(prepared)
        : prepared;
    }
```

Add to the created family:

```ts
      workflowKind,
```

Update `cloneFamily()` so a shortform request clones only `request.cloneFromRatio ?? request.ratio`, adds `workflowKind: 'shortform'`, and calls `withShortformRuntimeSpec()`.

Update `createVariant()`:

```ts
    if (this.isShortformFamily(family)) {
      throw new BadRequestException('숏폼 템플릿은 하나의 비율만 가질 수 있습니다.');
    }
```

Update `updateVariant()` before assigning `nextVariants[ratio] = next`:

```ts
      nextVariants[variantRatio] = this.isShortformFamily(family)
        ? this.withShortformRuntimeSpec(next, family.cardThumbnailUri)
        : next;
```

- [x] **Step 4: Add shortform validation**

In `clipper_nestjs/src/template-builder/template-builder-validation.service.ts`, add validation during `validateVariant()`:

```ts
    if (variant.shortformRuntimeSpec) {
      const runtimeJson = JSON.stringify(variant.shortformRuntimeSpec);
      for (const forbidden of ['sub_title', 'bottom_title', 'logo']) {
        if (runtimeJson.includes(forbidden)) {
          issues.push({
            path: `shortformRuntimeSpec.${forbidden}`,
            message: '숏폼 템플릿 runtime spec에는 legacy title/logo 역할을 포함할 수 없습니다.',
            severity: 'error',
          });
        }
      }
      for (const key of ['clip_media', 'main_title1', 'main_title2', 'caption']) {
        if (!(key in variant.shortformRuntimeSpec.regions)) {
          issues.push({
            path: `shortformRuntimeSpec.regions.${key}`,
            message: '숏폼 템플릿 runtime spec 필수 영역이 없습니다.',
            severity: 'error',
          });
        }
      }
    }
```

- [x] **Step 5: Run backend shortform mode tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-template-runtime-spec.test.js test/template-builder-shortform-mode.test.js
```

Expected: all listed tests pass.

- [x] **Step 6: Commit**

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git add src/template-builder/template-builder.service.ts src/template-builder/template-builder-validation.service.ts test/template-builder-shortform-mode.test.js
git commit -m "feat: support shortform template builder mode"
```

---

## Task 3: Backend Shortform Preset Catalog From Builder Templates

**Files:**

- Modify: `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`
- Test: `clipper_nestjs/test/template-builder-shortform-preset-source.test.js`

- [x] **Step 1: Write failing preset source test**

Create `clipper_nestjs/test/template-builder-shortform-preset-source.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { mkdtemp, mkdir, writeFile } = require('node:fs/promises');
const { join } = require('node:path');
const { tmpdir } = require('node:os');

test('template builder published preset source emits shortform templates with simplified slots', async () => {
  const { createDefaultTemplateVariant } = require('../dist/template-builder/dto/template-builder.dto');
  const { shortformTemplateRuntimeSpecForVariant } = require('../dist/template-builder/shortform-template-runtime-spec');
  const { TemplateBuilderPublishedPresetSource } = require('../dist/project-manifest/template-builder-published-preset-source');

  const root = await mkdtemp(join(tmpdir(), 'clipper-shortform-builder-preset-'));
  await mkdir(join(root, 'templates'), { recursive: true });

  const familyId = 'custom.template.shortform.preset';
  const variant = createDefaultTemplateVariant(familyId, '4:3', '2026-06-15T00:00:00.000Z');
  variant.status = 'published';
  variant.shortformRuntimeSpec = shortformTemplateRuntimeSpecForVariant(variant, 'template-builder/families/custom.template.shortform.preset/card-thumbnail/file');

  await writeFile(join(root, 'templates', 'template-builder.json'), JSON.stringify({
    version: 1,
    families: [{
      id: familyId,
      name: '빌더 숏폼',
      workflowKind: 'shortform',
      ownerType: 'user',
      source: 'custom',
      readonly: false,
      createdAt: '2026-06-15T00:00:00.000Z',
      updatedAt: '2026-06-15T00:00:00.000Z',
      cardThumbnailUri: 'template-builder/card-thumbnails/custom.template.shortform.preset.png',
      commonStyles: {},
      variants: { '4:3': variant },
    }],
  }));

  const source = new TemplateBuilderPublishedPresetSource({ get: (key) => key === 'CLIPPER_DATA_DIR' ? root : undefined });
  const presets = source.list();

  assert.equal(presets.length, 1);
  assert.equal(presets[0].aspectRatio, '4:3');
  assert.deepEqual(presets[0].compatibility.workflows, ['workflow.shortform']);
  assert.deepEqual(presets[0].slots.map((slot) => slot.id), [
    'clip_media',
    'main_title1',
    'main_title2',
    'caption',
    'bgm',
  ]);
  assert.equal(presets[0].defaultParams.shortformTemplateRuntimeSpec.schemaVersion, 'shortform-template-runtime.v1');
  assert.equal(JSON.stringify(presets[0]).includes('sub_title'), false);
  assert.equal(JSON.stringify(presets[0]).includes('bottom_title'), false);
  assert.equal(JSON.stringify(presets[0]).includes('logo'), false);
});
```

- [x] **Step 2: Run failing test**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-shortform-preset-source.test.js
```

Expected: test fails because `TemplateBuilderPublishedPresetSource` still emits legacy slots/workflows.

- [x] **Step 3: Add shortform preset branch**

In `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`, add slots:

```ts
const shortformTemplateBuilderSlots: TemplateSlot[] = [
  { id: 'clip_media', type: 'video', required: true, accepts: ['image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'image/gif'], defaultBinding: 'clip.media' },
  { id: 'main_title1', type: 'text', required: true, defaultBinding: 'project.mainTitle1' },
  { id: 'main_title2', type: 'text', required: true, defaultBinding: 'project.mainTitle2' },
  { id: 'caption', type: 'subtitle', required: true, defaultBinding: 'clip.subtitles' },
  { id: 'bgm', type: 'audio', required: false, defaultBinding: 'project.bgm' },
];
```

In `presetFor()`, branch by `family.workflowKind`:

```ts
    if (family.workflowKind === 'shortform') {
      const runtimeSpec = variant.shortformRuntimeSpec;
      if (!runtimeSpec) {
        throw new Error(`Shortform template ${family.id}/${variant.ratio} is missing runtime spec`);
      }
      return {
        schemaVersion: 'template-preset.v1',
        id: this.presetIdFor(family, variant),
        displayName: family.name,
        category: 'shorts',
        locale: 'ko-KR',
        aspectRatio: variant.ratio,
        canvas: {
          width: runtimeSpec.canvas.width,
          height: runtimeSpec.canvas.height,
          fps: runtimeSpec.canvas.fps,
          backgroundColor: runtimeSpec.canvas.backgroundColor,
        },
        preview: this.previewFor(family, variant),
        slots: shortformTemplateBuilderSlots,
        defaultParams: {
          shortformTemplateModel: 'template-builder.v1',
          shortformTemplateRatio: variant.ratio,
          shortformTemplateRuntimeSpec: runtimeSpec,
          templateBuilderFamilyId: family.id,
          templateBuilderVariantId: variant.id,
        },
        requiredAssets: this.requiredAssetsFor(variant.layers),
        capabilities: {
          requires: ['subtitle.compose', 'template.apply', 'video.render'],
        },
        compatibility: {
          workflows: ['workflow.shortform'],
          sourceMediaTypes: ['image', 'video'],
        },
      };
    }
```

Keep the existing legacy branch for `workflowKind !== 'shortform'`.

- [x] **Step 4: Run preset source tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-shortform-preset-source.test.js test/simplified-shortform-template-preset-source.test.js
```

Expected: tests pass.

- [x] **Step 5: Commit**

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git add src/project-manifest/template-builder-published-preset-source.ts test/template-builder-shortform-preset-source.test.js
git commit -m "feat: publish builder shortform templates as presets"
```

---

## Task 4: Angular Runtime Types And Shortform Catalog Mapping

**Files:**

- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/shortform/models/shortform-project.ts`
- Modify: `clipper_angular/src/features/shortform/services/shortform-project.service.ts`
- Test: `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.spec.ts`

- [x] **Step 1: Write failing Angular catalog expectation**

In `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.spec.ts`, update the template catalog test setup so one fixture includes:

```ts
const runtimeSpec = {
  schemaVersion: 'shortform-template-runtime.v1',
  templateId: 'custom.template.one.1x1',
  ratio: '1:1',
  canvas: { width: 1080, height: 1080, fps: 30, backgroundColor: '#000000' },
  thumbnail: { url: 'https://assets.example.test/template.png', captureRatio: '9:16' },
  regions: {
    clip_media: { x: 0, y: 0, width: 1080, height: 1080, anchor: 'top-left', zIndex: 10, fit: 'cover' },
    main_title1: { x: 80, y: 80, width: 920, height: 80, anchor: 'top-left', zIndex: 20, textStyle: { fontFamily: 'Pretendard', fontSize: 56, fontWeight: 700, lineHeight: 1.1, letterSpacing: 0, color: '#fff', textAlign: 'center', backgroundColor: null, backgroundAlpha: 0, paddingX: 0, borderRadius: 0, maxLines: 1 } },
    main_title2: { x: 80, y: 160, width: 920, height: 80, anchor: 'top-left', zIndex: 21, textStyle: { fontFamily: 'Pretendard', fontSize: 56, fontWeight: 700, lineHeight: 1.1, letterSpacing: 0, color: '#fff', textAlign: 'center', backgroundColor: null, backgroundAlpha: 0, paddingX: 0, borderRadius: 0, maxLines: 1 } },
    caption: { x: 120, y: 860, width: 840, height: 140, anchor: 'top-left', zIndex: 30, textStyle: { fontFamily: 'Pretendard', fontSize: 38, fontWeight: 700, lineHeight: 1.2, letterSpacing: 0, color: '#fff', textAlign: 'center', backgroundColor: '#000', backgroundAlpha: 0.75, paddingX: 20, borderRadius: 4, maxLines: 2 } },
  },
  audio: { ttsVolume: 1, bgmVolume: 0.18 },
};
```

Assert:

```ts
expect(component.shortformTemplates()[0].runtimeSpec?.schemaVersion)
  .toBe('shortform-template-runtime.v1');
```

- [x] **Step 2: Run failing Angular spec**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts
```

Expected: fails because `runtimeSpec` is not modeled/mapped.

- [x] **Step 3: Add Angular runtime spec model**

In `clipper_angular/src/features/shortform/models/shortform-project.ts`, add:

```ts
export interface ShortformTemplateRuntimeSpec {
  schemaVersion: 'shortform-template-runtime.v1';
  templateId: string;
  ratio: ShortformTemplateRatio;
  canvas: {
    width: number;
    height: number;
    fps: number;
    backgroundColor: string;
  };
  thumbnail: {
    url?: string | null;
    captureRatio: '9:16';
  };
  regions: Record<string, unknown>;
  audio: {
    ttsVolume: number;
    bgmVolume: number;
  };
}
```

Update `ShortformTemplateCatalogItem`:

```ts
export interface ShortformTemplateCatalogItem {
  id: string;
  name: string;
  ratio: ShortformTemplateRatio;
  thumbnailUrl: string;
  order?: number;
  runtimeSpec?: ShortformTemplateRuntimeSpec;
}
```

- [x] **Step 4: Map runtime spec in service**

In `clipper_angular/src/features/shortform/services/shortform-project.service.ts`, extend `TemplatePresetResponse`:

```ts
interface TemplatePresetResponse {
  // existing fields
  defaultParams?: Record<string, unknown>;
}
```

Update `shortformTemplateForPreset()`:

```ts
    const runtimeSpec = this.shortformRuntimeSpecParam(
      preset.defaultParams?.['shortformTemplateRuntimeSpec'],
    );
    return {
      id: preset.id,
      name: preset.displayName,
      ratio: preset.aspectRatio,
      thumbnailUrl,
      order: this.numberParam(preset.defaultParams?.['shortformTemplateOrder']),
      ...(runtimeSpec ? { runtimeSpec } : {}),
    };
```

Add:

```ts
  private shortformRuntimeSpecParam(value: unknown): ShortformTemplateRuntimeSpec | undefined {
    if (!value || typeof value !== 'object') return undefined;
    const spec = value as ShortformTemplateRuntimeSpec;
    if (spec.schemaVersion !== 'shortform-template-runtime.v1') return undefined;
    if (!this.isShortformTemplateRatio(spec.ratio)) return undefined;
    if (spec.thumbnail?.captureRatio !== '9:16') return undefined;
    return spec;
  }
```

- [x] **Step 5: Prefer Builder shortform presets with fallback**

Replace `listShortformTemplates()` with:

```ts
  async listShortformTemplates(): Promise<ShortformTemplateCatalogItem[]> {
    const builderTemplates = await this.listShortformTemplatesFromSource('template_builder.custom');
    if (builderTemplates.length) return builderTemplates;
    return this.listShortformTemplatesFromSource('shortform.simplified');
  }

  private async listShortformTemplatesFromSource(source: string): Promise<ShortformTemplateCatalogItem[]> {
    const base = await this.backend.getBaseUrl();
    const presets = await firstValueFrom(
      this.http.get<TemplatePresetResponse[]>(`${base}/template-presets`, {
        params: {
          workflow: 'workflow.shortform',
          source,
        },
      }),
    );
    return presets
      .map((preset) => this.shortformTemplateForPreset(base, preset))
      .filter((template): template is ShortformTemplateCatalogItem => !!template)
      .sort((a, b) => (a.order ?? Number.MAX_SAFE_INTEGER) - (b.order ?? Number.MAX_SAFE_INTEGER));
  }
```

- [x] **Step 6: Run Angular spec**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts
```

Expected: focused spec passes.

- [x] **Step 7: Commit**

```bash
cd /Users/jina/project/adlight/clipper_angular
git add src/features/shortform/models/shortform-project.ts src/features/shortform/services/shortform-project.service.ts src/features/shortform/pages/shortform-workflow-page.component.spec.ts
git commit -m "feat: load builder shortform template specs"
```

---

## Task 5: Angular Template Builder Single-Ratio Shortform UI

**Files:**

- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`
- Test: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [x] **Step 1: Write failing page spec for create ratio**

In `template-builder-page.component.spec.ts`, add:

```ts
it('creates shortform templates with a single selected ratio', async () => {
  await setup();
  fixture.detectChanges();

  const element = fixture.nativeElement as HTMLElement;
  (element.querySelector('[data-testid="template-create-open-button"]') as HTMLButtonElement).click();
  fixture.detectChanges();

  expect(element.querySelector('[data-testid="template-create-ratio-1-1"]')).toBeTruthy();
  expect(element.querySelector('[data-testid="template-create-ratio-4-3"]')).toBeTruthy();
  expect(element.querySelector('[data-testid="template-create-ratio-16-9"]')).toBeNull();
  expect(element.querySelector('[data-testid="template-create-ratio-full"]')).toBeNull();

  (element.querySelector('[data-testid="template-create-ratio-4-3"]') as HTMLButtonElement).click();
  (element.querySelector('[data-testid="template-create-submit-button"]') as HTMLButtonElement).click();
  await fixture.whenStable();

  expect(service.createFamily).toHaveBeenCalledWith({
    name: '새 템플릿',
    ratio: '4:3',
    workflowKind: 'shortform',
  });
});
```

- [x] **Step 2: Write failing editor spec for visible layers**

In `template-builder-editor.component.spec.ts`, add:

```ts
it('shows only shortform template layers in the active product editor', () => {
  setupEditor({ workflowKind: 'shortform' });
  fixture.detectChanges();

  const element = fixture.nativeElement as HTMLElement;
  expect(element.textContent).toContain('메인 타이틀 1줄');
  expect(element.textContent).toContain('메인 타이틀 2줄');
  expect(element.textContent).toContain('대사 자막');
  expect(element.textContent).toContain('콘텐츠 영역');
  expect(element.textContent).not.toContain('서브 타이틀');
  expect(element.textContent).not.toContain('하단 타이틀');
  expect(element.textContent).not.toContain('로고');
  expect(element.textContent).not.toContain('16:9');
  expect(element.textContent).not.toContain('full');
});
```

- [x] **Step 3: Run failing Angular Template Builder specs**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: specs fail because UI still exposes legacy ratios/layers.

- [x] **Step 4: Add Angular model constants**

In `models/template-builder.ts`:

```ts
export const SHORTFORM_TEMPLATE_BUILDER_RATIOS = ['1:1', '4:3'] as const;
export type ShortformTemplateBuilderRatio = typeof SHORTFORM_TEMPLATE_BUILDER_RATIOS[number];
export type TemplateBuilderWorkflowKind = 'legacy' | 'shortform';
```

Add `workflowKind?: TemplateBuilderWorkflowKind` to `TemplateBuilderFamily`.

Add `workflowKind?: TemplateBuilderWorkflowKind` to `CreateTemplateBuilderFamilyRequest`.

- [x] **Step 5: Update create form state**

In `template-builder-page.component.ts`, add:

```ts
  readonly createRatio = signal<TemplateBuilderRatio>('1:1');
  readonly shortformTemplateRatios = SHORTFORM_TEMPLATE_BUILDER_RATIOS;
```

Update `openCreateFamilyForm()`:

```ts
    this.createName.set('새 템플릿');
    this.createRatio.set('1:1');
    this.openOverlay('create');
```

Add:

```ts
  selectCreateRatio(ratio: TemplateBuilderRatio): void {
    if (ratio !== '1:1' && ratio !== '4:3') return;
    this.createRatio.set(ratio);
  }
```

Update `handleCreateFamily()`:

```ts
      const created = await this.service.createFamily({
        name: this.createName().trim() || '새 템플릿',
        ratio: this.createRatio(),
        workflowKind: 'shortform',
      });
```

- [x] **Step 6: Update create form HTML**

In `template-builder-page.component.html`, add inside the create form before actions:

```html
<div class="segmented-field">
  <span>비율</span>
  <div class="segmented-control segmented-control--two" role="group" aria-label="템플릿 비율">
    @for (ratio of shortformTemplateRatios; track ratio) {
      <button
        [attr.data-testid]="'template-create-ratio-' + ratio.replace(':', '-')"
        type="button"
        [class.is-active]="createRatio() === ratio"
        [attr.aria-pressed]="createRatio() === ratio"
        (click)="selectCreateRatio(ratio)"
      >{{ ratio }}</button>
    }
  </div>
</div>
```

Add `data-testid="template-create-open-button"` to the gallery create button output if the button is owned by `TemplateFamilyGalleryComponent`; otherwise add the test id to the existing create request button in that component.

- [x] **Step 7: Limit editor ratios and layer rows**

In `template-builder-editor.component.ts`, replace:

```ts
readonly ratios = TEMPLATE_BUILDER_RATIOS;
```

with:

```ts
readonly ratios = SHORTFORM_TEMPLATE_BUILDER_RATIOS;
```

Replace `TEXT_LAYER_KEYS`:

```ts
const TEXT_LAYER_KEYS: TemplateBuilderTextLayerKey[] = [
  'mainTitleLine1',
  'mainTitleLine2',
  'subtitleText',
];
```

Ensure `defaultLayerRows` includes only:

```ts
[
  mediaLayerRow(variant.layers.contentArea, '콘텐츠 영역'),
  textLayerRow(variant.layers.mainTitleLine1, '메인 타이틀 1줄'),
  textLayerRow(variant.layers.mainTitleLine2, '메인 타이틀 2줄'),
  textLayerRow(variant.layers.subtitleText, '대사 자막'),
]
```

Keep `layoutImage` and `layoutLayers` available through the layout manager because they are renderer-required layout controls.

- [x] **Step 8: Remove legacy controls from active HTML**

In `template-builder-page.component.html`, remove or guard out:

```html
data-testid="template-system-admin-mode-button"
data-testid="template-register-official-button"
```

In `template-builder-workspace.component.html`, rename:

```html
<h3>템플릿 비율</h3>
```

In `template-builder-inspector.component.html`, guard logo blocks so they never render for `workflowKind === 'shortform'`. The simplest condition is to make `selectedMediaLayerId === 'logoImage'` unreachable in the editor filtered rows. Also remove visible text that says `로고` from any branch that can be reached in shortform mode.

- [x] **Step 9: Run focused Angular specs**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: focused specs pass.

- [x] **Step 10: Commit**

```bash
cd /Users/jina/project/adlight/clipper_angular
git add src/features/template-builder/models/template-builder.ts src/features/template-builder/pages/template-builder-page.component.ts src/features/template-builder/pages/template-builder-page.component.html src/features/template-builder/components/template-builder-editor.component.ts src/features/template-builder/components/template-builder-workspace.component.html src/features/template-builder/components/template-builder-inspector.component.html src/features/template-builder/pages/template-builder-page.component.spec.ts src/features/template-builder/components/template-builder-editor.component.spec.ts
git commit -m "feat: simplify template builder for shortform templates"
```

---

## Task 6: Angular Real 9:16 Shortform Thumbnail Capture

**Files:**

- Modify: `clipper_angular/src/features/template-builder/services/template-builder-card-thumbnail.service.ts`
- Test: `clipper_angular/src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts`

- [x] **Step 1: Write failing thumbnail test**

In `template-builder-card-thumbnail.service.spec.ts`, add:

```ts
it('captures shortform card thumbnails in 9:16 and excludes removed legacy layers', async () => {
  const service = TestBed.inject(TemplateBuilderCardThumbnailService);
  const family = shortformFamilyFixture({
    ratio: '1:1',
    visibleLegacyLayers: true,
  });

  const file = await service.createCardThumbnailFile(family, '1:1');

  expect(file).toBeTruthy();
  const bitmap = await createImageBitmap(file!);
  expect(bitmap.height / bitmap.width).toBeCloseTo(16 / 9, 1);
  expect(drawTextSpy).toHaveBeenCalledWith(jasmine.anything(), family.variants['1:1']!.layers.mainTitleLine1, jasmine.any(String), jasmine.any(Number));
  expect(drawTextSpy).not.toHaveBeenCalledWith(jasmine.anything(), family.variants['1:1']!.layers.subTitle, jasmine.any(String), jasmine.any(Number));
  expect(drawTextSpy).not.toHaveBeenCalledWith(jasmine.anything(), family.variants['1:1']!.layers.bottomTitle, jasmine.any(String), jasmine.any(Number));
  expect(drawTextSpy).not.toHaveBeenCalledWith(jasmine.anything(), family.variants['1:1']!.layers.logoText, jasmine.any(String), jasmine.any(Number));
});
```

If the existing test cannot spy on private drawing helpers, assert through public behavior instead by adding a package-visible helper:

```ts
export function shortformThumbnailLayerIdsForTest(): readonly string[] {
  return SHORTFORM_CARD_THUMBNAIL_LAYER_IDS;
}
```

Then assert:

```ts
expect(shortformThumbnailLayerIdsForTest()).toEqual([
  'layoutLayers',
  'contentArea',
  'mainTitleLine1',
  'mainTitleLine2',
  'subtitleText',
]);
```

- [x] **Step 2: Run failing test**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts
```

Expected: fails because thumbnail height follows template canvas ratio and legacy layers are still drawn.

- [x] **Step 3: Update thumbnail constants and drawing**

In `template-builder-card-thumbnail.service.ts`, change constants:

```ts
const CARD_THUMBNAIL_WIDTH = 360;
const CARD_THUMBNAIL_HEIGHT = 640;
const CARD_THUMBNAIL_BACKGROUND = '#000000';
const CARD_THUMBNAIL_RATIO_ORDER: TemplateBuilderRatio[] = ['1:1', '4:3'];
const SHORTFORM_CARD_THUMBNAIL_LAYER_IDS = [
  'layoutLayers',
  'contentArea',
  'mainTitleLine1',
  'mainTitleLine2',
  'subtitleText',
] as const;
```

Update canvas sizing:

```ts
    canvas.width = CARD_THUMBNAIL_WIDTH;
    canvas.height = CARD_THUMBNAIL_HEIGHT;
    const scale = Math.min(
      CARD_THUMBNAIL_WIDTH / variant.outputSize.width,
      CARD_THUMBNAIL_HEIGHT / variant.outputSize.height,
    );
    const offsetX = Math.round((CARD_THUMBNAIL_WIDTH - variant.outputSize.width * scale) / 2);
    const offsetY = Math.round((CARD_THUMBNAIL_HEIGHT - variant.outputSize.height * scale) / 2);
```

Update drawing signatures to accept offsets:

```ts
await this.drawVariant(context, variant, scale, true, offsetX, offsetY);
```

Draw only:

```ts
    if (variant.layers.layoutLayers?.length) {
      for (const layer of variant.layers.layoutLayers) {
        await this.drawMediaLayer(context, layer, scale, includeImages, offsetX, offsetY);
      }
    } else {
      await this.drawMediaLayer(context, variant.layers.layoutImage, scale, includeImages, offsetX, offsetY);
    }
    await this.drawMediaLayer(context, variant.layers.contentArea, scale, includeImages, offsetX, offsetY);
    this.drawTextLayer(context, variant.layers.mainTitleLine1, TEMPLATE_BUILDER_PREVIEW_SAMPLE_TEXT.mainTitleLine1, scale, offsetX, offsetY);
    this.drawTextLayer(context, variant.layers.mainTitleLine2, TEMPLATE_BUILDER_PREVIEW_SAMPLE_TEXT.mainTitleLine2, scale, offsetX, offsetY);
    this.drawTextLayer(context, variant.layers.subtitleText, TEMPLATE_BUILDER_PREVIEW_SAMPLE_TEXT.subtitleText, scale, offsetX, offsetY);
```

- [x] **Step 4: Run thumbnail tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts
```

Expected: tests pass.

- [x] **Step 5: Commit**

```bash
cd /Users/jina/project/adlight/clipper_angular
git add src/features/template-builder/services/template-builder-card-thumbnail.service.ts src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts
git commit -m "feat: capture shortform template thumbnails"
```

---

## Task 7: End-To-End Verification And Cleanup

**Files:**

- Verify changed files only unless a failure points to a required fix.
- Update: `.codex/handoff/NEXT.md` only if the session handoff needs the new implementation status.

- [x] **Step 1: Run backend focused tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-template-runtime-spec.test.js test/template-builder-shortform-mode.test.js test/template-builder-shortform-preset-source.test.js test/simplified-shortform-template-preset-source.test.js
```

Expected: build succeeds and all listed tests pass.

- [x] **Step 2: Run frontend focused tests**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts --include=src/features/template-builder/services/template-builder-card-thumbnail.service.spec.ts --include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts
```

Expected: focused specs pass.

- [x] **Step 3: Run frontend build**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run build
```

Expected: Angular build succeeds.

- [x] **Step 4: Check diffs**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git diff --check
git status --short
cd /Users/jina/project/adlight/clipper_angular
git diff --check
git status --short
```

Expected: no whitespace errors. Status shows only files touched by this plan plus pre-existing shortform work.

- [x] **Step 5: Record next handoff if implementation is not completed in one session**

If implementation stops before all tasks are complete, update `/Users/jina/project/adlight/.codex/handoff/NEXT.md` with:

```md
## Current Focus

Template Builder simplified shortform mode.

## Completed

- Runtime contract: <done or pending>
- Backend shortform builder mode: <done or pending>
- Builder shortform preset catalog: <done or pending>
- Angular Builder UI simplification: <done or pending>
- 9:16 thumbnail capture: <done or pending>

## Next

Continue from `.codex/design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md`.
Do not start Project-first / Plugin / Queue cleanup.
Do not build the browser preview engine until Builder-created shortform templates are flowing through the catalog.
```

- [x] **Step 6: Commit handoff if changed**

```bash
cd /Users/jina/project/adlight/.codex
git add handoff/NEXT.md
git commit -m "docs: update template builder handoff"
```

Skip this commit if `NEXT.md` was not changed.

---

## Self-Review

- Spec coverage: The plan covers the runtime contract, Builder simplification, 9:16 thumbnails, and replacement of temporary shortform catalog data with Builder-produced templates. It intentionally does not cover the browser timeline preview engine, matching the agreed sequence.
- Placeholder scan: The plan avoids deferred placeholders. Each task names files, test commands, expected failure/pass states, and concrete code shapes.
- Type consistency: Backend and frontend both use `shortform-template-runtime.v1`, `workflowKind: 'shortform'`, `1:1 | 4:3`, and `shortformTemplateRuntimeSpec`.
