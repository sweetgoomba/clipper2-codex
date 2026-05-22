# Template Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-shaped Template Builder slice: a top-level Angular `템플릿` screen backed by a NestJS Shared Template Catalog with draft/published lifecycle, fixed ratio slots, legacy-compatible settings editing, validation, and sample-render publish gate plumbing.

**Architecture:** NestJS owns template catalog orchestration through repository/adapter boundaries, with a local filesystem repository for now and DB/API adapters left as replaceable implementations. Angular is a zoneless standalone UI that calls NestJS only, renders the approved v4 three-column editor, and keeps local UI state in signals. Existing `TemplatePresetCatalogService` remains available for render consumers, while the new builder introduces family/variant lifecycle and later bridges published custom variants into the preset catalog.

**Tech Stack:** Angular 19 standalone + zoneless signals, NestJS 10, Node built-in test runner, JSON local repositories under `CLIPPER_DATA_DIR`, existing `video.render` provider contracts.

---

## Scope Boundary

This plan implements a first complete Template Builder slice, not the full renderer parity migration.

Included:

- Top-level `템플릿` route and nav item.
- NestJS `TemplateBuilderModule`.
- Local filesystem `TemplateRepository` adapter.
- System/custom template family model.
- Fixed ratio slots for `16:9`, `4:3`, `1:1`, `full`.
- Draft save/load/update.
- Validation endpoint.
- Publish gate that requires validation and a successful sample-render marker.
- Sample render status plumbing that uses the existing video render job contract shape, with a deterministic dry-run result in the first slice.
- Angular v4 editor shell with left ratio/layer panel, narrower canvas, wider properties panel, color palette, and box/outline/shadow fields.

Deferred:

- Arbitrary free layers.
- Export/import.
- Arbitrary ratios.
- Custom font upload.
- DB/API repository implementation.
- Pixel-perfect renderer parity for every legacy template.
- Replacing Clipper1/Variation template selection with custom published templates in the same commit. The backend data shape must make this possible, but final consumer switch can be a follow-up after published template fixtures exist.

## File Structure

### NestJS

- Create: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
  - Shared DTOs for family, variant, layer settings, validation, and sample render snapshots.
- Create: `clipper_nestjs/src/template-builder/template-builder.repository.ts`
  - `TemplateBuilderRepository` abstract class and `JsonTemplateBuilderRepository` local filesystem adapter.
- Create: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
  - Converts existing legacy preset rows into read-only system families.
- Create: `clipper_nestjs/src/template-builder/template-builder-validation.service.ts`
  - Validates fixed ratios, coordinates, colors, alpha, required layer settings, and publish eligibility.
- Create: `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`
  - Starts/records sample render status through a narrow service boundary.
- Create: `clipper_nestjs/src/template-builder/template-builder.service.ts`
  - Orchestrates repository, seed data, create/clone/update/validate/sample-render/publish.
- Create: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
  - REST API under `/v1/template-builder`.
- Create: `clipper_nestjs/src/template-builder/template-builder.module.ts`
  - Feature module wiring.
- Modify: `clipper_nestjs/src/app.module.ts`
  - Import `TemplateBuilderModule`.
- Test: `clipper_nestjs/test/template-builder-repository.test.js`
- Test: `clipper_nestjs/test/template-builder-api.test.js`
- Test: `clipper_nestjs/test/template-builder-validation.test.js`

### Angular

- Create: `clipper_angular/src/features/template-builder/models/template-builder.ts`
  - Frontend model interfaces matching NestJS DTOs.
- Create: `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
  - NestJS API client.
- Create: `clipper_angular/src/features/template-builder/services/template-builder.service.spec.ts`
  - API URL and request tests.
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`
  - Top-level page and data loading.
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
  - Approved v4 editor UI.
- Modify: `clipper_angular/src/app/app.routes.ts`
  - Add `/templates`.
- Modify: `clipper_angular/src/shell/nav/nav.component.html`
  - Add `템플릿` nav entry.
- Modify: `clipper_angular/src/shell/nav/nav.component.scss`
  - Add template nav icon styling if needed.

### Docs

- Modify: `.codex/implementation/TASKS.md`
  - Add Template Builder implementation section.
- Modify: `.codex/implementation/WORKLOG.md`
  - Record implementation progress after tasks are executed.
- Modify: `.codex/session-logs/YYYY-MM-DD.log`
  - Continue session-level logging.

## API Contract

Base path: `/v1/template-builder`.

Endpoints:

```text
GET    /families
GET    /families/:familyId
POST   /families
POST   /families/:familyId/clone
PATCH  /families/:familyId/variants/:ratio
POST   /families/:familyId/variants/:ratio/validate
POST   /families/:familyId/variants/:ratio/sample-render
POST   /families/:familyId/variants/:ratio/publish
```

## Tasks

### Task 1: NestJS DTO And Fixture Contract

**Files:**

- Create: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Test: `clipper_nestjs/test/template-builder-validation.test.js`

- [ ] **Step 1: Write the failing DTO shape test**

Create `clipper_nestjs/test/template-builder-validation.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');

test('template builder dto module exports fixed ratio and default variant helpers', () => {
  const dto = require('../dist/template-builder/dto/template-builder.dto');

  assert.deepEqual(dto.TEMPLATE_BUILDER_RATIOS, ['16:9', '4:3', '1:1', 'full']);
  assert.equal(dto.contentHeightForRatio('16:9'), 608);
  assert.equal(dto.contentHeightForRatio('4:3'), 810);
  assert.equal(dto.contentHeightForRatio('1:1'), 1080);
  assert.equal(dto.contentHeightForRatio('full'), 1920);

  const variant = dto.createDefaultTemplateVariant('family.test', 'full');
  assert.equal(variant.ratio, 'full');
  assert.equal(variant.status, 'draft');
  assert.deepEqual(variant.outputSize, { width: 1080, height: 1920 });
  assert.equal(variant.contentArea.height, 1920);
  assert.equal(variant.layers.subtitleBox.visible, true);
  assert.equal(variant.layers.subtitleText.text.fontSize, 40);
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js
```

Expected:

```text
Error: Cannot find module '../dist/template-builder/dto/template-builder.dto'
```

- [ ] **Step 3: Add the DTO and helper implementation**

Create `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`:

```ts
export const TEMPLATE_BUILDER_RATIOS = ['16:9', '4:3', '1:1', 'full'] as const;

export type TemplateBuilderRatio = typeof TEMPLATE_BUILDER_RATIOS[number];
export type TemplateBuilderOwnerType = 'system' | 'user';
export type TemplateBuilderSource = 'built_in' | 'custom';
export type TemplateBuilderVariantStatus = 'draft' | 'published';
export type TemplateBuilderSampleRenderStatus = 'missing' | 'queued' | 'running' | 'succeeded' | 'failed';

export interface TemplateBuilderOutputSize {
  width: number;
  height: number;
}

export interface TemplateBuilderContentArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TemplateBuilderColor {
  value: string;
  alpha: number;
}

export interface TemplateBuilderTextStyle {
  fontFamily: string;
  fontSize: number;
  color: string;
  tracking: number;
  lineHeight: number;
}

export interface TemplateBuilderBoxStyle {
  enabled: boolean;
  color: string;
  alpha: number;
  paddingX: number;
  height: number;
  borderColor: string;
  borderWidth: number;
}

export interface TemplateBuilderOutlineStyle {
  enabled: boolean;
  width: number;
  color: string;
}

export interface TemplateBuilderShadowStyle {
  enabled: boolean;
  color: string;
  outlineWidth: number;
  outlineColor: string;
  offsetX: number;
  offsetY: number;
}

export interface TemplateBuilderTextLayer {
  id: string;
  label: string;
  visible: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  oneLineY?: number;
  twoLineFirstY?: number;
  twoLineSecondY?: number;
  leftMargin?: number;
  rightMargin?: number;
  align: 'left' | 'center' | 'right';
  text: TemplateBuilderTextStyle;
  box: TemplateBuilderBoxStyle;
  outline: TemplateBuilderOutlineStyle;
  shadow: TemplateBuilderShadowStyle;
}

export interface TemplateBuilderMediaLayer {
  id: string;
  label: string;
  visible: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  assetUri?: string | null;
}

export interface TemplateBuilderLayers {
  layoutImage: TemplateBuilderMediaLayer;
  contentArea: TemplateBuilderMediaLayer;
  subTitle: TemplateBuilderTextLayer;
  mainTitleLine1: TemplateBuilderTextLayer;
  mainTitleLine2: TemplateBuilderTextLayer;
  bottomTitle: TemplateBuilderTextLayer;
  subtitleText: TemplateBuilderTextLayer;
  subtitleBox: TemplateBuilderTextLayer;
  logoImage: TemplateBuilderMediaLayer;
  logoText: TemplateBuilderTextLayer;
}

export interface TemplateBuilderValidationIssue {
  path: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface TemplateBuilderValidationResult {
  valid: boolean;
  issues: TemplateBuilderValidationIssue[];
}

export interface TemplateBuilderSampleRenderSnapshot {
  status: TemplateBuilderSampleRenderStatus;
  jobId?: string | null;
  artifactUri?: string | null;
  message?: string | null;
  updatedAt?: string | null;
}

export interface TemplateBuilderVariant {
  id: string;
  familyId: string;
  ratio: TemplateBuilderRatio;
  status: TemplateBuilderVariantStatus;
  outputSize: TemplateBuilderOutputSize;
  contentArea: TemplateBuilderContentArea;
  layers: TemplateBuilderLayers;
  validation: TemplateBuilderValidationResult;
  sampleRender: TemplateBuilderSampleRenderSnapshot;
  updatedAt: string;
}

export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: TemplateBuilderOwnerType;
  source: TemplateBuilderSource;
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}

export interface CreateTemplateBuilderFamilyRequest {
  name: string;
  ratio: TemplateBuilderRatio;
  cloneFromFamilyId?: string | null;
  cloneFromRatio?: TemplateBuilderRatio | null;
}

export interface UpdateTemplateBuilderVariantRequest {
  layers?: Partial<TemplateBuilderLayers>;
}

export function contentHeightForRatio(ratio: TemplateBuilderRatio): number {
  switch (ratio) {
    case '16:9': return 608;
    case '4:3': return 810;
    case '1:1': return 1080;
    case 'full': return 1920;
  }
}

export function isTemplateBuilderRatio(value: unknown): value is TemplateBuilderRatio {
  return typeof value === 'string' && TEMPLATE_BUILDER_RATIOS.includes(value as TemplateBuilderRatio);
}

export function createDefaultTemplateVariant(
  familyId: string,
  ratio: TemplateBuilderRatio,
  now = new Date().toISOString(),
): TemplateBuilderVariant {
  const contentHeight = contentHeightForRatio(ratio);
  return {
    id: `${familyId}.${ratio.replace(':', 'x')}`,
    familyId,
    ratio,
    status: 'draft',
    outputSize: { width: 1080, height: 1920 },
    contentArea: { x: 0, y: Math.max(0, Math.round((1920 - contentHeight) / 2)), width: 1080, height: contentHeight },
    layers: defaultLayers(contentHeight),
    validation: { valid: false, issues: [] },
    sampleRender: { status: 'missing' },
    updatedAt: now,
  };
}

function defaultTextLayer(id: string, label: string, y: number): TemplateBuilderTextLayer {
  return {
    id,
    label,
    visible: true,
    x: 86,
    y,
    width: 908,
    height: 64,
    oneLineY: y,
    twoLineFirstY: y,
    twoLineSecondY: y + 60,
    leftMargin: 86,
    rightMargin: 86,
    align: 'center',
    text: {
      fontFamily: 'Pretendard-SemiBold.otf',
      fontSize: 40,
      color: '#FFFFFF',
      tracking: -1.2,
      lineHeight: 1.18,
    },
    box: {
      enabled: false,
      color: '#000000',
      alpha: 0.8,
      paddingX: 20,
      height: 59,
      borderColor: '#FFFFFF',
      borderWidth: 0,
    },
    outline: {
      enabled: false,
      width: 0,
      color: '#000000',
    },
    shadow: {
      enabled: false,
      color: '#000000',
      outlineWidth: 0,
      outlineColor: '#000000',
      offsetX: 0,
      offsetY: 0,
    },
  };
}

function defaultMediaLayer(id: string, label: string, y: number, height: number): TemplateBuilderMediaLayer {
  return {
    id,
    label,
    visible: true,
    x: 0,
    y,
    width: 1080,
    height,
    assetUri: null,
  };
}

function defaultLayers(contentHeight: number): TemplateBuilderLayers {
  const contentY = Math.max(0, Math.round((1920 - contentHeight) / 2));
  return {
    layoutImage: defaultMediaLayer('layoutImage', '레이아웃 이미지', 0, 1920),
    contentArea: defaultMediaLayer('contentArea', '콘텐츠 영역', contentY, contentHeight),
    subTitle: defaultTextLayer('subTitle', '서브 타이틀', 286),
    mainTitleLine1: defaultTextLayer('mainTitleLine1', '메인 타이틀 1줄', 364),
    mainTitleLine2: defaultTextLayer('mainTitleLine2', '메인 타이틀 2줄', 462),
    bottomTitle: defaultTextLayer('bottomTitle', '하단 타이틀', 1432),
    subtitleText: defaultTextLayer('subtitleText', '대사 자막', 1254),
    subtitleBox: {
      ...defaultTextLayer('subtitleBox', '자막 박스', 1254),
      box: {
        enabled: true,
        color: '#000000',
        alpha: 0.8,
        paddingX: 20,
        height: 59,
        borderColor: '#FFFFFF',
        borderWidth: 0,
      },
    },
    logoImage: {
      ...defaultMediaLayer('logoImage', '로고 이미지', 1599, 160),
      x: 140,
      width: 800,
    },
    logoText: defaultTextLayer('logoText', '로고 텍스트', 1656),
  };
}
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js
```

Expected:

```text
ok 1 - template builder dto module exports fixed ratio and default variant helpers
```

- [ ] **Step 5: Commit**

Run:

```bash
cd clipper_nestjs
git add src/template-builder/dto/template-builder.dto.ts test/template-builder-validation.test.js
git commit -m "feat: add template builder dto contract"
```

### Task 2: NestJS Local Template Repository

**Files:**

- Create: `clipper_nestjs/src/template-builder/template-builder.repository.ts`
- Test: `clipper_nestjs/test/template-builder-repository.test.js`

- [ ] **Step 1: Write failing repository test**

Create `clipper_nestjs/test/template-builder-repository.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { mkdtemp, rm } = require('node:fs/promises');
const { join } = require('node:path');
const { tmpdir } = require('node:os');

test('json template repository persists custom families', async () => {
  const {
    JsonTemplateBuilderRepository,
  } = require('../dist/template-builder/template-builder.repository');
  const {
    createDefaultTemplateVariant,
  } = require('../dist/template-builder/dto/template-builder.dto');

  const root = await mkdtemp(join(tmpdir(), 'clipper-template-builder-'));
  const config = { get: (key) => key === 'CLIPPER_DATA_DIR' ? root : undefined };
  const repository = new JsonTemplateBuilderRepository(config);
  const now = '2026-05-07T00:00:00.000Z';
  const family = {
    id: 'tpl.user.news',
    name: '뉴스 강조형',
    ownerType: 'user',
    source: 'custom',
    readonly: false,
    createdAt: now,
    updatedAt: now,
    variants: {
      full: createDefaultTemplateVariant('tpl.user.news', 'full', now),
    },
  };

  await repository.upsert(family);

  const reloaded = new JsonTemplateBuilderRepository(config);
  const loaded = await reloaded.require('tpl.user.news');
  assert.equal(loaded.name, '뉴스 강조형');
  assert.equal(loaded.variants.full.ratio, 'full');

  await rm(root, { recursive: true, force: true });
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-repository.test.js
```

Expected:

```text
Error: Cannot find module '../dist/template-builder/template-builder.repository'
```

- [ ] **Step 3: Add repository implementation**

Create `clipper_nestjs/src/template-builder/template-builder.repository.ts`:

```ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import type { TemplateBuilderFamily } from './dto/template-builder.dto';

interface TemplateBuilderStoreFile {
  version: 1;
  families: TemplateBuilderFamily[];
}

export abstract class TemplateBuilderRepository {
  abstract list(): Promise<TemplateBuilderFamily[]>;
  abstract get(familyId: string): Promise<TemplateBuilderFamily | null>;
  abstract require(familyId: string): Promise<TemplateBuilderFamily>;
  abstract upsert(family: TemplateBuilderFamily): Promise<TemplateBuilderFamily>;
}

@Injectable()
export class JsonTemplateBuilderRepository extends TemplateBuilderRepository {
  private loaded = false;
  private readonly families = new Map<string, TemplateBuilderFamily>();
  private readonly storePath: string;

  constructor(config: ConfigService) {
    super();
    const dataRoot = config.get<string>('CLIPPER_DATA_DIR') ?? join(process.cwd(), '.clipper_data');
    this.storePath = join(dataRoot, 'templates', 'template-builder.json');
  }

  async list(): Promise<TemplateBuilderFamily[]> {
    await this.ensureLoaded();
    return [...this.families.values()].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  }

  async get(familyId: string): Promise<TemplateBuilderFamily | null> {
    await this.ensureLoaded();
    return this.families.get(familyId) ?? null;
  }

  async require(familyId: string): Promise<TemplateBuilderFamily> {
    const family = await this.get(familyId);
    if (!family) {
      throw new NotFoundException(`Unknown template family: ${familyId}`);
    }
    return family;
  }

  async upsert(family: TemplateBuilderFamily): Promise<TemplateBuilderFamily> {
    await this.ensureLoaded();
    this.families.set(family.id, family);
    await this.flush();
    return family;
  }

  private async ensureLoaded(): Promise<void> {
    if (this.loaded) return;
    try {
      const raw = await readFile(this.storePath, 'utf-8');
      const parsed = JSON.parse(raw) as TemplateBuilderStoreFile;
      for (const family of parsed.families ?? []) {
        this.families.set(family.id, family);
      }
    } catch {
      // Missing or corrupt store starts empty; system seed is supplied by service.
    }
    this.loaded = true;
  }

  private async flush(): Promise<void> {
    const payload: TemplateBuilderStoreFile = {
      version: 1,
      families: [...this.families.values()],
    };
    await mkdir(dirname(this.storePath), { recursive: true });
    await writeFile(this.storePath, JSON.stringify(payload, null, 2), 'utf-8');
  }
}
```

- [ ] **Step 4: Run repository and DTO tests**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js test/template-builder-repository.test.js
```

Expected:

```text
# tests 2
# pass 2
```

- [ ] **Step 5: Commit**

Run:

```bash
cd clipper_nestjs
git add src/template-builder/template-builder.repository.ts test/template-builder-repository.test.js
git commit -m "feat: persist template builder families"
```

### Task 3: NestJS Service, Validation, Controller, Module

**Files:**

- Create: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder-validation.service.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder.module.ts`
- Modify: `clipper_nestjs/src/app.module.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`

- [ ] **Step 1: Write failing API smoke test**

Create `clipper_nestjs/test/template-builder-api.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { mkdtemp, rm } = require('node:fs/promises');
const { join } = require('node:path');
const { tmpdir } = require('node:os');

test('template builder service creates, validates, sample-renders, and publishes a custom full variant', async () => {
  const {
    TemplateBuilderService,
  } = require('../dist/template-builder/template-builder.service');
  const {
    TemplateBuilderValidationService,
  } = require('../dist/template-builder/template-builder-validation.service');
  const {
    TemplateBuilderSampleRenderService,
  } = require('../dist/template-builder/template-builder-sample-render.service');
  const {
    JsonTemplateBuilderRepository,
  } = require('../dist/template-builder/template-builder.repository');

  const root = await mkdtemp(join(tmpdir(), 'clipper-template-builder-api-'));
  const config = { get: (key) => key === 'CLIPPER_DATA_DIR' ? root : undefined };
  const repository = new JsonTemplateBuilderRepository(config);
  const service = new TemplateBuilderService(
    repository,
    new TemplateBuilderValidationService(),
    new TemplateBuilderSampleRenderService(),
  );

  const created = await service.createFamily({
    name: '뉴스 강조형 A',
    ratio: 'full',
  });

  assert.equal(created.ownerType, 'user');
  assert.equal(created.source, 'custom');
  assert.equal(created.variants.full.status, 'draft');

  const validation = await service.validateVariant(created.id, 'full');
  assert.equal(validation.valid, true);

  const rendered = await service.startSampleRender(created.id, 'full');
  assert.equal(rendered.variants.full.sampleRender.status, 'succeeded');

  const published = await service.publishVariant(created.id, 'full');
  assert.equal(published.variants.full.status, 'published');

  await rm(root, { recursive: true, force: true });
});
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Expected:

```text
Error: Cannot find module '../dist/template-builder/template-builder.service'
```

- [ ] **Step 3: Implement seed conversion**

Create `clipper_nestjs/src/template-builder/template-builder-seed.ts`:

```ts
import { safeManifestId } from '../project-manifest/project-manifest.constants';
import type { TemplatePreset } from '../project-manifest/dto/template-preset.dto';
import {
  createDefaultTemplateVariant,
  isTemplateBuilderRatio,
  TemplateBuilderFamily,
  TemplateBuilderRatio,
  TemplateBuilderVariant,
} from './dto/template-builder.dto';

export function systemFamiliesFromPresets(presets: TemplatePreset[]): TemplateBuilderFamily[] {
  const families = new Map<number, TemplateBuilderFamily>();
  const now = '1970-01-01T00:00:00.000Z';
  for (const preset of presets) {
    const designId = preset.legacy?.templateDesignId;
    const ratio = preset.legacy?.contentsRatio;
    if (!designId || !isTemplateBuilderRatio(ratio)) continue;
    const familyId = `system.legacy.clipper1.template.${safeManifestId(String(designId))}`;
    const family = families.get(designId) ?? {
      id: familyId,
      name: `Legacy Clipper1 Template ${designId}`,
      ownerType: 'system',
      source: 'built_in',
      readonly: true,
      createdAt: now,
      updatedAt: now,
      variants: {},
    };
    family.variants[ratio] = variantFromPreset(familyId, ratio, preset, now);
    families.set(designId, family);
  }
  return [...families.values()].sort((a, b) => a.id.localeCompare(b.id));
}

function variantFromPreset(
  familyId: string,
  ratio: TemplateBuilderRatio,
  preset: TemplatePreset,
  now: string,
): TemplateBuilderVariant {
  const variant = createDefaultTemplateVariant(familyId, ratio, now);
  const settings = preset.legacy?.rawSettings ?? {};
  const numberSetting = (key: string, fallback: number) => {
    const value = settings[key];
    return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
  };
  const stringSetting = (key: string, fallback: string) => {
    const value = settings[key];
    return typeof value === 'string' && value.trim() ? value : fallback;
  };

  variant.id = preset.id;
  variant.status = 'published';
  variant.layers.contentArea.y = numberSetting('contents_area_y_offset', variant.layers.contentArea.y);
  variant.layers.layoutImage.assetUri = stringSetting('layout_image', '');
  variant.layers.subtitleText.text.fontFamily = stringSetting('subtitle_font', variant.layers.subtitleText.text.fontFamily);
  variant.layers.subtitleText.text.fontSize = numberSetting('subtitle_font_size', variant.layers.subtitleText.text.fontSize);
  variant.layers.subtitleText.text.color = stringSetting('subtitle_font_color', variant.layers.subtitleText.text.color);
  variant.layers.subtitleText.oneLineY = numberSetting('subtitle_1st_y_offset_subtitle_line_1', variant.layers.subtitleText.oneLineY ?? variant.layers.subtitleText.y);
  variant.layers.subtitleText.twoLineFirstY = numberSetting('subtitle_1st_y_offset_subtitle_line_2', variant.layers.subtitleText.twoLineFirstY ?? variant.layers.subtitleText.y);
  variant.layers.subtitleText.twoLineSecondY = numberSetting('subtitle_2nd_y_offset_subtitle_line_2', variant.layers.subtitleText.twoLineSecondY ?? variant.layers.subtitleText.y + 60);
  variant.validation = { valid: true, issues: [] };
  variant.sampleRender = { status: 'succeeded', message: '기본 제공 템플릿' };
  return variant;
}
```

- [ ] **Step 4: Implement validation service**

Create `clipper_nestjs/src/template-builder/template-builder-validation.service.ts`:

```ts
import { Injectable } from '@nestjs/common';
import {
  isTemplateBuilderRatio,
  TemplateBuilderValidationIssue,
  TemplateBuilderValidationResult,
  TemplateBuilderVariant,
} from './dto/template-builder.dto';

@Injectable()
export class TemplateBuilderValidationService {
  validateVariant(variant: TemplateBuilderVariant): TemplateBuilderValidationResult {
    const issues: TemplateBuilderValidationIssue[] = [];
    if (!isTemplateBuilderRatio(variant.ratio)) {
      issues.push({ path: 'ratio', message: '지원하지 않는 비율입니다.', severity: 'error' });
    }
    if (variant.outputSize.width !== 1080 || variant.outputSize.height !== 1920) {
      issues.push({ path: 'outputSize', message: '출력 크기는 1080x1920이어야 합니다.', severity: 'error' });
    }
    this.checkBox('layers.subtitleText', variant.layers.subtitleText.x, variant.layers.subtitleText.y, variant.layers.subtitleText.width, variant.layers.subtitleText.height, issues);
    this.checkColor('layers.subtitleText.text.color', variant.layers.subtitleText.text.color, issues);
    this.checkColor('layers.subtitleText.box.color', variant.layers.subtitleText.box.color, issues);
    this.checkAlpha('layers.subtitleText.box.alpha', variant.layers.subtitleText.box.alpha, issues);
    return { valid: issues.every((issue) => issue.severity !== 'error'), issues };
  }

  private checkBox(
    path: string,
    x: number,
    y: number,
    width: number,
    height: number,
    issues: TemplateBuilderValidationIssue[],
  ): void {
    const valid = [x, y, width, height].every((value) => Number.isFinite(value))
      && x >= 0
      && y >= 0
      && width > 0
      && height > 0
      && x + width <= 1080
      && y + height <= 1920;
    if (!valid) {
      issues.push({ path, message: '레이어 좌표가 1080x1920 범위를 벗어났습니다.', severity: 'error' });
    }
  }

  private checkColor(path: string, value: string, issues: TemplateBuilderValidationIssue[]): void {
    if (!/^#[0-9A-Fa-f]{6}$/.test(value)) {
      issues.push({ path, message: '색상은 #RRGGBB 형식이어야 합니다.', severity: 'error' });
    }
  }

  private checkAlpha(path: string, value: number, issues: TemplateBuilderValidationIssue[]): void {
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      issues.push({ path, message: '투명도는 0 이상 1 이하이어야 합니다.', severity: 'error' });
    }
  }
}
```

- [ ] **Step 5: Implement sample render service**

Create `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`:

```ts
import { Injectable } from '@nestjs/common';
import type {
  TemplateBuilderSampleRenderSnapshot,
  TemplateBuilderVariant,
} from './dto/template-builder.dto';

@Injectable()
export class TemplateBuilderSampleRenderService {
  async start(variant: TemplateBuilderVariant): Promise<TemplateBuilderSampleRenderSnapshot> {
    return {
      status: 'succeeded',
      jobId: `sample.${variant.id}`,
      artifactUri: `template-samples/${variant.id}.mp4`,
      message: '샘플 렌더 완료',
      updatedAt: new Date().toISOString(),
    };
  }
}
```

- [ ] **Step 6: Implement service**

Create `clipper_nestjs/src/template-builder/template-builder.service.ts`:

```ts
import { BadRequestException, Injectable } from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import type { TemplatePresetCatalogService } from '../project-manifest/template-preset-catalog.service';
import {
  createDefaultTemplateVariant,
  CreateTemplateBuilderFamilyRequest,
  isTemplateBuilderRatio,
  TemplateBuilderFamily,
  TemplateBuilderRatio,
  UpdateTemplateBuilderVariantRequest,
} from './dto/template-builder.dto';
import { systemFamiliesFromPresets } from './template-builder-seed';
import { TemplateBuilderRepository } from './template-builder.repository';
import { TemplateBuilderSampleRenderService } from './template-builder-sample-render.service';
import { TemplateBuilderValidationService } from './template-builder-validation.service';

@Injectable()
export class TemplateBuilderService {
  constructor(
    private readonly repository: TemplateBuilderRepository,
    private readonly validation: TemplateBuilderValidationService,
    private readonly sampleRender: TemplateBuilderSampleRenderService,
    private readonly presetCatalog?: TemplatePresetCatalogService,
  ) {}

  async listFamilies(): Promise<TemplateBuilderFamily[]> {
    const custom = await this.repository.list();
    return [...this.systemFamilies(), ...custom].sort((a, b) => a.name.localeCompare(b.name));
  }

  async getFamily(familyId: string): Promise<TemplateBuilderFamily> {
    return this.systemFamilies().find((family) => family.id === familyId)
      ?? await this.repository.require(familyId);
  }

  async createFamily(request: CreateTemplateBuilderFamilyRequest): Promise<TemplateBuilderFamily> {
    if (!isTemplateBuilderRatio(request.ratio)) {
      throw new BadRequestException('지원하지 않는 비율입니다.');
    }
    const now = new Date().toISOString();
    const familyId = `custom.template.${randomUUID()}`;
    const family: TemplateBuilderFamily = {
      id: familyId,
      name: request.name.trim() || '새 템플릿',
      ownerType: 'user',
      source: 'custom',
      readonly: false,
      createdAt: now,
      updatedAt: now,
      variants: {
        [request.ratio]: createDefaultTemplateVariant(familyId, request.ratio, now),
      },
    };
    return this.repository.upsert(family);
  }

  async cloneFamily(
    sourceFamilyId: string,
    request: CreateTemplateBuilderFamilyRequest,
  ): Promise<TemplateBuilderFamily> {
    if (!isTemplateBuilderRatio(request.ratio)) {
      throw new BadRequestException('지원하지 않는 비율입니다.');
    }
    const source = await this.getFamily(sourceFamilyId);
    const sourceRatio = request.cloneFromRatio && isTemplateBuilderRatio(request.cloneFromRatio)
      ? request.cloneFromRatio
      : request.ratio;
    const sourceVariant = source.variants[sourceRatio];
    if (!sourceVariant) {
      throw new BadRequestException('복제할 비율 템플릿이 없습니다.');
    }
    const now = new Date().toISOString();
    const familyId = `custom.template.${randomUUID()}`;
    const clonedVariant = {
      ...sourceVariant,
      id: `${familyId}.${request.ratio.replace(':', 'x')}`,
      familyId,
      ratio: request.ratio,
      status: 'draft' as const,
      sampleRender: { status: 'missing' as const },
      updatedAt: now,
    };
    const family: TemplateBuilderFamily = {
      id: familyId,
      name: request.name.trim() || `${source.name} 복제본`,
      ownerType: 'user',
      source: 'custom',
      readonly: false,
      createdAt: now,
      updatedAt: now,
      variants: {
        [request.ratio]: clonedVariant,
      },
    };
    return this.repository.upsert(family);
  }

  async updateVariant(
    familyId: string,
    ratio: TemplateBuilderRatio,
    request: UpdateTemplateBuilderVariantRequest,
  ): Promise<TemplateBuilderFamily> {
    const family = await this.repository.require(familyId);
    if (family.readonly) {
      throw new BadRequestException('기본 제공 템플릿은 직접 수정할 수 없습니다.');
    }
    const current = family.variants[ratio] ?? createDefaultTemplateVariant(familyId, ratio);
    const next = {
      ...current,
      layers: {
        ...current.layers,
        ...(request.layers ?? {}),
      },
      status: 'draft',
      sampleRender: { status: 'missing' as const },
      updatedAt: new Date().toISOString(),
    };
    next.validation = this.validation.validateVariant(next);
    const updated = {
      ...family,
      variants: {
        ...family.variants,
        [ratio]: next,
      },
      updatedAt: next.updatedAt,
    };
    return this.repository.upsert(updated);
  }

  async validateVariant(familyId: string, ratio: TemplateBuilderRatio) {
    const family = await this.getFamily(familyId);
    const variant = family.variants[ratio];
    if (!variant) {
      throw new BadRequestException('해당 비율 템플릿이 없습니다.');
    }
    return this.validation.validateVariant(variant);
  }

  async startSampleRender(familyId: string, ratio: TemplateBuilderRatio): Promise<TemplateBuilderFamily> {
    const family = await this.repository.require(familyId);
    const variant = family.variants[ratio];
    if (!variant) {
      throw new BadRequestException('해당 비율 템플릿이 없습니다.');
    }
    const validation = this.validation.validateVariant(variant);
    if (!validation.valid) {
      throw new BadRequestException('검증 오류가 있어 샘플 렌더를 시작할 수 없습니다.');
    }
    const sampleRender = await this.sampleRender.start(variant);
    const updatedVariant = {
      ...variant,
      validation,
      sampleRender,
      updatedAt: new Date().toISOString(),
    };
    return this.repository.upsert({
      ...family,
      variants: { ...family.variants, [ratio]: updatedVariant },
      updatedAt: updatedVariant.updatedAt,
    });
  }

  async publishVariant(familyId: string, ratio: TemplateBuilderRatio): Promise<TemplateBuilderFamily> {
    const family = await this.repository.require(familyId);
    const variant = family.variants[ratio];
    if (!variant) {
      throw new BadRequestException('해당 비율 템플릿이 없습니다.');
    }
    const validation = this.validation.validateVariant(variant);
    if (!validation.valid) {
      throw new BadRequestException('검증 오류가 있어 게시할 수 없습니다.');
    }
    if (variant.sampleRender.status !== 'succeeded') {
      throw new BadRequestException('샘플 렌더가 성공해야 게시할 수 있습니다.');
    }
    const updatedVariant = {
      ...variant,
      validation,
      status: 'published' as const,
      updatedAt: new Date().toISOString(),
    };
    return this.repository.upsert({
      ...family,
      variants: { ...family.variants, [ratio]: updatedVariant },
      updatedAt: updatedVariant.updatedAt,
    });
  }

  private systemFamilies(): TemplateBuilderFamily[] {
    return this.presetCatalog ? systemFamiliesFromPresets(this.presetCatalog.list({ workflow: 'workflow.clipper_studio' })) : [];
  }
}
```

- [ ] **Step 7: Implement controller**

Create `clipper_nestjs/src/template-builder/template-builder.controller.ts`:

```ts
import { Body, Controller, Get, Param, Patch, Post } from '@nestjs/common';
import type {
  CreateTemplateBuilderFamilyRequest,
  TemplateBuilderRatio,
  UpdateTemplateBuilderVariantRequest,
} from './dto/template-builder.dto';
import { TemplateBuilderService } from './template-builder.service';

@Controller('template-builder')
export class TemplateBuilderController {
  constructor(private readonly service: TemplateBuilderService) {}

  @Get('families')
  list() {
    return this.service.listFamilies();
  }

  @Get('families/:familyId')
  get(@Param('familyId') familyId: string) {
    return this.service.getFamily(familyId);
  }

  @Post('families')
  create(@Body() request: CreateTemplateBuilderFamilyRequest) {
    return this.service.createFamily(request);
  }

  @Post('families/:familyId/clone')
  clone(
    @Param('familyId') familyId: string,
    @Body() request: CreateTemplateBuilderFamilyRequest,
  ) {
    return this.service.cloneFamily(familyId, request);
  }

  @Patch('families/:familyId/variants/:ratio')
  updateVariant(
    @Param('familyId') familyId: string,
    @Param('ratio') ratio: TemplateBuilderRatio,
    @Body() request: UpdateTemplateBuilderVariantRequest,
  ) {
    return this.service.updateVariant(familyId, ratio, request);
  }

  @Post('families/:familyId/variants/:ratio/validate')
  validateVariant(
    @Param('familyId') familyId: string,
    @Param('ratio') ratio: TemplateBuilderRatio,
  ) {
    return this.service.validateVariant(familyId, ratio);
  }

  @Post('families/:familyId/variants/:ratio/sample-render')
  startSampleRender(
    @Param('familyId') familyId: string,
    @Param('ratio') ratio: TemplateBuilderRatio,
  ) {
    return this.service.startSampleRender(familyId, ratio);
  }

  @Post('families/:familyId/variants/:ratio/publish')
  publishVariant(
    @Param('familyId') familyId: string,
    @Param('ratio') ratio: TemplateBuilderRatio,
  ) {
    return this.service.publishVariant(familyId, ratio);
  }
}
```

- [ ] **Step 8: Implement module and wire AppModule**

Create `clipper_nestjs/src/template-builder/template-builder.module.ts`:

```ts
import { Module } from '@nestjs/common';
import { ProjectManifestModule } from '../project-manifest';
import { TemplateBuilderController } from './template-builder.controller';
import {
  JsonTemplateBuilderRepository,
  TemplateBuilderRepository,
} from './template-builder.repository';
import { TemplateBuilderSampleRenderService } from './template-builder-sample-render.service';
import { TemplateBuilderService } from './template-builder.service';
import { TemplateBuilderValidationService } from './template-builder-validation.service';

@Module({
  imports: [ProjectManifestModule],
  controllers: [TemplateBuilderController],
  providers: [
    TemplateBuilderService,
    TemplateBuilderValidationService,
    TemplateBuilderSampleRenderService,
    {
      provide: TemplateBuilderRepository,
      useClass: JsonTemplateBuilderRepository,
    },
  ],
  exports: [TemplateBuilderService],
})
export class TemplateBuilderModule {}
```

Modify `clipper_nestjs/src/app.module.ts`:

```ts
import { TemplateBuilderModule } from './template-builder/template-builder.module';
```

Add `TemplateBuilderModule` to `imports` after `ProjectManifestModule`.

- [ ] **Step 9: Run backend tests**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js
```

Expected:

```text
# tests 3
# pass 3
```

- [ ] **Step 10: Commit**

Run:

```bash
cd clipper_nestjs
git add src/app.module.ts src/template-builder test/template-builder-api.test.js
git commit -m "feat: add template builder catalog api"
```

### Task 4: Angular Template Builder API Client

**Files:**

- Create: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Create: `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
- Test: `clipper_angular/src/features/template-builder/services/template-builder.service.spec.ts`

- [ ] **Step 1: Write failing Angular service test**

Create `clipper_angular/src/features/template-builder/services/template-builder.service.spec.ts`:

```ts
import { provideExperimentalZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { BackendLocator } from '../../../core/backend-locator';
import { TemplateBuilderService } from './template-builder.service';

class TestBackendLocator extends BackendLocator {
  async getBaseUrl(): Promise<string> {
    return 'http://127.0.0.1:9019/v1';
  }
}

describe('TemplateBuilderService', () => {
  let service: TemplateBuilderService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideExperimentalZonelessChangeDetection(),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: BackendLocator, useClass: TestBackendLocator },
      ],
    });
    service = TestBed.inject(TemplateBuilderService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('loads template families from NestJS', async () => {
    const promise = service.listFamilies();
    const req = http.expectOne('http://127.0.0.1:9019/v1/template-builder/families');
    expect(req.request.method).toBe('GET');
    req.flush([]);
    await expectAsync(promise).toBeResolvedTo([]);
  });

  it('updates a ratio variant', async () => {
    const promise = service.updateVariant('family.1', 'full', {
      layers: {
        subtitleText: { text: { color: '#111827' } },
      },
    });
    const req = http.expectOne('http://127.0.0.1:9019/v1/template-builder/families/family.1/variants/full');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body.layers.subtitleText.text.color).toBe('#111827');
    req.flush({ id: 'family.1', variants: {} });
    await expectAsync(promise).toBeResolved();
  });
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts
```

Expected:

```text
Cannot find module './template-builder.service'
```

- [ ] **Step 3: Add frontend models**

Create `clipper_angular/src/features/template-builder/models/template-builder.ts`:

```ts
export const TEMPLATE_BUILDER_RATIOS = ['16:9', '4:3', '1:1', 'full'] as const;

export type TemplateBuilderRatio = typeof TEMPLATE_BUILDER_RATIOS[number];
export type TemplateBuilderVariantStatus = 'draft' | 'published';
export type TemplateBuilderSampleRenderStatus = 'missing' | 'queued' | 'running' | 'succeeded' | 'failed';

export interface TemplateBuilderTextStyle {
  fontFamily: string;
  fontSize: number;
  color: string;
  tracking: number;
  lineHeight: number;
}

export interface TemplateBuilderBoxStyle {
  enabled: boolean;
  color: string;
  alpha: number;
  paddingX: number;
  height: number;
  borderColor: string;
  borderWidth: number;
}

export interface TemplateBuilderOutlineStyle {
  enabled: boolean;
  width: number;
  color: string;
}

export interface TemplateBuilderShadowStyle {
  enabled: boolean;
  color: string;
  outlineWidth: number;
  outlineColor: string;
  offsetX: number;
  offsetY: number;
}

export interface TemplateBuilderTextLayer {
  id: string;
  label: string;
  visible: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  oneLineY?: number;
  twoLineFirstY?: number;
  twoLineSecondY?: number;
  leftMargin?: number;
  rightMargin?: number;
  align: 'left' | 'center' | 'right';
  text: TemplateBuilderTextStyle;
  box: TemplateBuilderBoxStyle;
  outline: TemplateBuilderOutlineStyle;
  shadow: TemplateBuilderShadowStyle;
}

export interface TemplateBuilderMediaLayer {
  id: string;
  label: string;
  visible: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  assetUri?: string | null;
}

export interface TemplateBuilderLayers {
  layoutImage: TemplateBuilderMediaLayer;
  contentArea: TemplateBuilderMediaLayer;
  subTitle: TemplateBuilderTextLayer;
  mainTitleLine1: TemplateBuilderTextLayer;
  mainTitleLine2: TemplateBuilderTextLayer;
  bottomTitle: TemplateBuilderTextLayer;
  subtitleText: TemplateBuilderTextLayer;
  subtitleBox: TemplateBuilderTextLayer;
  logoImage: TemplateBuilderMediaLayer;
  logoText: TemplateBuilderTextLayer;
}

export interface TemplateBuilderValidationIssue {
  path: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface TemplateBuilderVariant {
  id: string;
  familyId: string;
  ratio: TemplateBuilderRatio;
  status: TemplateBuilderVariantStatus;
  outputSize: { width: number; height: number };
  contentArea: { x: number; y: number; width: number; height: number };
  layers: TemplateBuilderLayers;
  validation: { valid: boolean; issues: TemplateBuilderValidationIssue[] };
  sampleRender: {
    status: TemplateBuilderSampleRenderStatus;
    jobId?: string | null;
    artifactUri?: string | null;
    message?: string | null;
    updatedAt?: string | null;
  };
  updatedAt: string;
}

export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: 'system' | 'user';
  source: 'built_in' | 'custom';
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}

export interface CreateTemplateBuilderFamilyRequest {
  name: string;
  ratio: TemplateBuilderRatio;
  cloneFromFamilyId?: string | null;
  cloneFromRatio?: TemplateBuilderRatio | null;
}

export interface UpdateTemplateBuilderVariantRequest {
  layers?: Partial<TemplateBuilderLayers>;
}
```

- [ ] **Step 4: Add API service**

Create `clipper_angular/src/features/template-builder/services/template-builder.service.ts`:

```ts
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { BackendLocator } from '../../../core/backend-locator';
import type {
  CreateTemplateBuilderFamilyRequest,
  TemplateBuilderFamily,
  TemplateBuilderRatio,
  UpdateTemplateBuilderVariantRequest,
} from '../models/template-builder';

@Injectable({ providedIn: 'root' })
export class TemplateBuilderService {
  private readonly http = inject(HttpClient);
  private readonly backend = inject(BackendLocator);

  async listFamilies(): Promise<TemplateBuilderFamily[]> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.get<TemplateBuilderFamily[]>(`${base}/template-builder/families`));
  }

  async getFamily(familyId: string): Promise<TemplateBuilderFamily> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.get<TemplateBuilderFamily>(`${base}/template-builder/families/${encodeURIComponent(familyId)}`));
  }

  async createFamily(request: CreateTemplateBuilderFamilyRequest): Promise<TemplateBuilderFamily> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.post<TemplateBuilderFamily>(`${base}/template-builder/families`, request));
  }

  async updateVariant(
    familyId: string,
    ratio: TemplateBuilderRatio,
    request: UpdateTemplateBuilderVariantRequest,
  ): Promise<TemplateBuilderFamily> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.patch<TemplateBuilderFamily>(
      `${base}/template-builder/families/${encodeURIComponent(familyId)}/variants/${encodeURIComponent(ratio)}`,
      request,
    ));
  }

  async validateVariant(familyId: string, ratio: TemplateBuilderRatio): Promise<TemplateBuilderFamily['variants'][TemplateBuilderRatio]['validation']> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.post<TemplateBuilderFamily['variants'][TemplateBuilderRatio]['validation']>(
      `${base}/template-builder/families/${encodeURIComponent(familyId)}/variants/${encodeURIComponent(ratio)}/validate`,
      {},
    ));
  }

  async startSampleRender(familyId: string, ratio: TemplateBuilderRatio): Promise<TemplateBuilderFamily> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.post<TemplateBuilderFamily>(
      `${base}/template-builder/families/${encodeURIComponent(familyId)}/variants/${encodeURIComponent(ratio)}/sample-render`,
      {},
    ));
  }

  async publishVariant(familyId: string, ratio: TemplateBuilderRatio): Promise<TemplateBuilderFamily> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.post<TemplateBuilderFamily>(
      `${base}/template-builder/families/${encodeURIComponent(familyId)}/variants/${encodeURIComponent(ratio)}/publish`,
      {},
    ));
  }
}
```

- [ ] **Step 5: Run service test**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts
```

Expected:

```text
TOTAL: 2 SUCCESS
```

- [ ] **Step 6: Commit**

Run:

```bash
cd clipper_angular
git add src/features/template-builder/models/template-builder.ts src/features/template-builder/services/template-builder.service.ts src/features/template-builder/services/template-builder.service.spec.ts
git commit -m "feat: add template builder api client"
```

### Task 5: Angular Route, Nav, And Page Loader

**Files:**

- Modify: `clipper_angular/src/app/app.routes.ts`
- Modify: `clipper_angular/src/shell/nav/nav.component.html`
- Modify: `clipper_angular/src/shell/nav/nav.component.scss`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Write failing page test**

Create `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`:

```ts
import { provideExperimentalZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TemplateBuilderPageComponent } from './template-builder-page.component';
import { TemplateBuilderService } from '../services/template-builder.service';
import type { TemplateBuilderFamily } from '../models/template-builder';

class TestTemplateBuilderService {
  async listFamilies(): Promise<TemplateBuilderFamily[]> {
    return [{
      id: 'family.1',
      name: '뉴스 강조형 A',
      ownerType: 'user',
      source: 'custom',
      readonly: false,
      createdAt: '2026-05-07T00:00:00.000Z',
      updatedAt: '2026-05-07T00:00:00.000Z',
      variants: {},
    }];
  }
}

describe('TemplateBuilderPageComponent', () => {
  let fixture: ComponentFixture<TemplateBuilderPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TemplateBuilderPageComponent],
      providers: [
        provideExperimentalZonelessChangeDetection(),
        { provide: TemplateBuilderService, useClass: TestTemplateBuilderService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TemplateBuilderPageComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('loads template families and selects the first family', () => {
    expect(fixture.componentInstance.families().length).toBe(1);
    expect(fixture.componentInstance.selectedFamily()?.name).toBe('뉴스 강조형 A');
    expect(fixture.nativeElement.textContent).toContain('템플릿');
    expect(fixture.nativeElement.textContent).toContain('뉴스 강조형 A');
  });
});
```

- [ ] **Step 2: Run and verify failing import**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
```

Expected:

```text
Cannot find module './template-builder-page.component'
```

- [ ] **Step 3: Add page component**

Create `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`:

```ts
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { TemplateBuilderService } from '../services/template-builder.service';
import type { TemplateBuilderFamily } from '../models/template-builder';

@Component({
  selector: 'app-template-builder-page',
  standalone: true,
  templateUrl: './template-builder-page.component.html',
  styleUrl: './template-builder-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TemplateBuilderPageComponent {
  private readonly service = inject(TemplateBuilderService);

  readonly families = signal<TemplateBuilderFamily[]>([]);
  readonly selectedFamilyId = signal<string | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly selectedFamily = computed(() => {
    const selectedId = this.selectedFamilyId();
    return this.families().find((family) => family.id === selectedId) ?? this.families()[0] ?? null;
  });

  constructor() {
    void this.loadFamilies();
  }

  async loadFamilies(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const families = await this.service.listFamilies();
      this.families.set(families);
      if (!this.selectedFamilyId() && families[0]) {
        this.selectedFamilyId.set(families[0].id);
      }
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : '템플릿 목록을 불러오지 못했습니다.');
    } finally {
      this.loading.set(false);
    }
  }

  selectFamily(family: TemplateBuilderFamily): void {
    this.selectedFamilyId.set(family.id);
  }
}
```

Create `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`:

```html
<section class="template-page">
  <header class="template-page__header">
    <div>
      <p class="template-page__eyebrow">Shared Template Catalog</p>
      <h1>템플릿</h1>
    </div>
    <button type="button">새 템플릿</button>
  </header>

  @if (error()) {
    <div class="template-page__error">{{ error() }}</div>
  }

  <div class="template-page__body">
    <aside class="template-page__list" aria-label="템플릿 목록">
      @for (family of families(); track family.id) {
        <button
          type="button"
          class="template-page__family"
          [class.template-page__family--active]="selectedFamily()?.id === family.id"
          (click)="selectFamily(family)"
        >
          <span>{{ family.name }}</span>
          <small>{{ family.ownerType === 'system' ? '기본 제공' : '사용자 템플릿' }}</small>
        </button>
      }
    </aside>
    <main class="template-page__editor">
      @if (selectedFamily(); as family) {
        <h2>{{ family.name }}</h2>
        <p>템플릿 생성기 편집 화면이 여기에 표시됩니다.</p>
      } @else {
        <p>템플릿이 없습니다.</p>
      }
    </main>
  </div>
</section>
```

Create `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`:

```scss
.template-page {
  min-height: 100vh;
  background: #f3f5f7;
  color: #1c2430;
  padding: 20px;
}

.template-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.template-page__eyebrow {
  margin: 0 0 4px;
  color: #667085;
  font-size: 12px;
  font-weight: 800;
}

h1,
h2 {
  margin: 0;
}

button {
  height: 36px;
  border: 1px solid #d9dee5;
  border-radius: 6px;
  background: #fff;
  color: #1c2430;
  font-weight: 800;
}

.template-page__body {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
}

.template-page__list,
.template-page__editor {
  min-height: 520px;
  border: 1px solid #d9dee5;
  border-radius: 8px;
  background: #fff;
  padding: 12px;
}

.template-page__list {
  display: grid;
  align-content: start;
  gap: 8px;
}

.template-page__family {
  height: auto;
  min-height: 54px;
  padding: 10px;
  display: grid;
  gap: 4px;
  text-align: left;
}

.template-page__family small {
  color: #667085;
}

.template-page__family--active {
  border-color: #2563eb;
  box-shadow: inset 3px 0 0 #2563eb;
}

.template-page__error {
  margin-bottom: 12px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #991b1b;
  border-radius: 8px;
  padding: 10px 12px;
}
```

- [ ] **Step 4: Add route and nav entry**

Modify `clipper_angular/src/app/app.routes.ts` by adding before `clipper-studio`:

```ts
  {
    path: 'templates',
    loadComponent: () =>
      import('../features/template-builder/pages/template-builder-page.component').then(
        (m) => m.TemplateBuilderPageComponent,
      ),
  },
```

Modify `clipper_angular/src/shell/nav/nav.component.html` by adding before dashboard:

```html
  <a class="nav-item" routerLink="/templates" routerLinkActive="active" aria-label="템플릿" title="템플릿">
    <span class="nav-icon nav-icon--templates" aria-hidden="true"></span>
    <span class="nav-text">템플릿</span>
  </a>
```

Modify `clipper_angular/src/shell/nav/nav.component.scss` by adding:

```scss
.nav-icon--templates::before {
  content: "T";
  font-weight: 900;
}
```

- [ ] **Step 5: Run page test and build**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build:electron -- --progress=false
```

Expected:

```text
TOTAL: 1 SUCCESS
Application bundle generation complete
```

- [ ] **Step 6: Commit**

Run:

```bash
cd clipper_angular
git add src/app/app.routes.ts src/shell/nav/nav.component.html src/shell/nav/nav.component.scss src/features/template-builder/pages
git commit -m "feat: add template builder route"
```

### Task 6: Angular Approved V4 Editor Component

**Files:**

- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.scss`
- Test: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`

- [ ] **Step 1: Write failing editor tests**

Create `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`:

```ts
import { provideExperimentalZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TemplateBuilderEditorComponent } from './template-builder-editor.component';
import type { TemplateBuilderFamily } from '../models/template-builder';

describe('TemplateBuilderEditorComponent', () => {
  let fixture: ComponentFixture<TemplateBuilderEditorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TemplateBuilderEditorComponent],
      providers: [provideExperimentalZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(TemplateBuilderEditorComponent);
    fixture.componentRef.setInput('family', familyFixture());
    fixture.detectChanges();
  });

  it('renders fixed ratio slots without variant wording', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('16:9');
    expect(text).toContain('4:3');
    expect(text).toContain('1:1');
    expect(text).toContain('full');
    expect(text).not.toContain('variant 추가');
    expect(text).not.toContain('없는 비율 만들기');
  });

  it('shows the color palette and box outline shadow controls', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('컬러 팔레트');
    expect(text).toContain('박스');
    expect(text).toContain('윤곽선');
    expect(text).toContain('그림자');
  });

  it('computes uniform canvas scale from output size', () => {
    expect(fixture.componentInstance.canvasScale()).toBeCloseTo(0.3, 2);
  });
});

function familyFixture(): TemplateBuilderFamily {
  const now = '2026-05-07T00:00:00.000Z';
  return {
    id: 'family.1',
    name: '뉴스 강조형 A',
    ownerType: 'user',
    source: 'custom',
    readonly: false,
    createdAt: now,
    updatedAt: now,
    variants: {
      full: {
        id: 'variant.full',
        familyId: 'family.1',
        ratio: 'full',
        status: 'draft',
        outputSize: { width: 1080, height: 1920 },
        contentArea: { x: 0, y: 0, width: 1080, height: 1920 },
        validation: { valid: true, issues: [] },
        sampleRender: { status: 'missing' },
        updatedAt: now,
        layers: {
          layoutImage: { id: 'layoutImage', label: '레이아웃 이미지', visible: true, x: 0, y: 0, width: 1080, height: 1920 },
          contentArea: { id: 'contentArea', label: '콘텐츠 영역', visible: true, x: 0, y: 0, width: 1080, height: 1920 },
          logoImage: { id: 'logoImage', label: '로고 이미지', visible: true, x: 140, y: 1599, width: 800, height: 160 },
          subTitle: textLayer('subTitle', '서브 타이틀'),
          mainTitleLine1: textLayer('mainTitleLine1', '메인 타이틀 1줄'),
          mainTitleLine2: textLayer('mainTitleLine2', '메인 타이틀 2줄'),
          bottomTitle: textLayer('bottomTitle', '하단 타이틀'),
          subtitleText: textLayer('subtitleText', '대사 자막'),
          subtitleBox: textLayer('subtitleBox', '자막 박스'),
          logoText: textLayer('logoText', '로고 텍스트'),
        },
      },
    },
  };
}

function textLayer(id: string, label: string) {
  return {
    id,
    label,
    visible: true,
    x: 86,
    y: 1254,
    width: 908,
    height: 59,
    oneLineY: 1254,
    twoLineFirstY: 1224,
    twoLineSecondY: 1293,
    leftMargin: 86,
    rightMargin: 86,
    align: 'center' as const,
    text: { fontFamily: 'Pretendard-SemiBold.otf', fontSize: 40, color: '#FFFFFF', tracking: -1.2, lineHeight: 1.18 },
    box: { enabled: true, color: '#000000', alpha: 0.8, paddingX: 20, height: 59, borderColor: '#FFFFFF', borderWidth: 0 },
    outline: { enabled: false, width: 0, color: '#000000' },
    shadow: { enabled: true, color: '#000000', outlineWidth: 1, outlineColor: '#000000', offsetX: 0, offsetY: 4 },
  };
}
```

- [ ] **Step 2: Run and verify failing import**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected:

```text
Cannot find module './template-builder-editor.component'
```

- [ ] **Step 3: Implement editor component class**

Create `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`:

```ts
import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import {
  TEMPLATE_BUILDER_RATIOS,
  TemplateBuilderFamily,
  TemplateBuilderRatio,
  TemplateBuilderTextLayer,
} from '../models/template-builder';

@Component({
  selector: 'app-template-builder-editor',
  standalone: true,
  templateUrl: './template-builder-editor.component.html',
  styleUrl: './template-builder-editor.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TemplateBuilderEditorComponent {
  readonly family = input.required<TemplateBuilderFamily>();
  readonly ratios = TEMPLATE_BUILDER_RATIOS;
  readonly selectedRatio = signal<TemplateBuilderRatio>('full');
  readonly selectedLayerId = signal('subtitleText');

  readonly selectedVariant = computed(() =>
    this.family().variants[this.selectedRatio()]
      ?? this.family().variants.full
      ?? this.family().variants['1:1']
      ?? null,
  );

  readonly textLayers = computed(() => {
    const variant = this.selectedVariant();
    if (!variant) return [];
    return [
      variant.layers.subTitle,
      variant.layers.mainTitleLine1,
      variant.layers.mainTitleLine2,
      variant.layers.bottomTitle,
      variant.layers.subtitleText,
      variant.layers.subtitleBox,
      variant.layers.logoText,
    ];
  });

  readonly selectedTextLayer = computed<TemplateBuilderTextLayer | null>(() =>
    this.textLayers().find((layer) => layer.id === this.selectedLayerId()) ?? null,
  );

  canvasScale(): number {
    const variant = this.selectedVariant();
    if (!variant) return 0;
    return 324 / variant.outputSize.width;
  }

  selectRatio(ratio: TemplateBuilderRatio): void {
    this.selectedRatio.set(ratio);
  }

  selectLayer(layerId: string): void {
    this.selectedLayerId.set(layerId);
  }

  slotState(ratio: TemplateBuilderRatio): string {
    const variant = this.family().variants[ratio];
    if (!variant) return '+ 생성';
    if (ratio === this.selectedRatio()) return '편집 중';
    return variant.status === 'published' ? '게시됨' : '초안';
  }
}
```

- [ ] **Step 4: Implement editor template**

Create `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`:

```html
<section class="template-editor">
  <aside class="template-editor__left">
    <header>
      <h2>{{ family().name }}</h2>
      <span>{{ family().ownerType === 'system' ? '기본 제공' : '사용자 템플릿' }}</span>
    </header>

    <h3>비율 슬롯</h3>
    <div class="ratio-slots">
      @for (ratio of ratios; track ratio) {
        <button
          type="button"
          class="ratio-slot"
          [class.ratio-slot--active]="ratio === selectedRatio()"
          (click)="selectRatio(ratio)"
        >
          <strong>{{ ratio }}</strong>
          <small>{{ slotState(ratio) }}</small>
        </button>
      }
    </div>

    <h3>고정 레이어</h3>
    <div class="layer-list">
      @for (layer of textLayers(); track layer.id) {
        <button
          type="button"
          class="layer-row"
          [class.layer-row--selected]="layer.id === selectedLayerId()"
          (click)="selectLayer(layer.id)"
        >
          <span>{{ layer.label }}</span>
          <small>{{ layer.visible ? '표시' : '숨김' }}</small>
        </button>
      }
    </div>
  </aside>

  <main class="template-editor__stage">
    <div class="stage-toolbar">
      <span>1080 × 1920</span>
      <span>{{ (canvasScale() * 100).toFixed(0) }}%</span>
    </div>
    <div class="stage-grid">
      <div class="phone-canvas">
        <div class="title-main">서울 근교<br>축제 TOP 5</div>
        <div class="subtitle-box">이번 주말에 가기 좋은<br>서울 근교 축제부터 볼게요</div>
        <div class="selection-box"></div>
      </div>
    </div>
    <footer>게시 전 샘플 렌더가 필요합니다.</footer>
  </main>

  <aside class="template-editor__props">
    <header>
      <h2>속성 · {{ selectedTextLayer()?.label ?? '레이어' }}</h2>
      <span>{{ selectedRatio() }}</span>
    </header>

    <div class="prop-tabs">
      <button type="button">위치</button>
      <button type="button">텍스트</button>
      <button type="button">색상</button>
      <button type="button">박스</button>
      <button type="button">효과</button>
    </div>

    @if (selectedTextLayer(); as layer) {
      <section class="prop-section">
        <h3>위치와 크기</h3>
        <div class="prop-grid">
          <label>X <span>{{ layer.x }} px</span></label>
          <label>Y <span>{{ layer.y }} px</span></label>
          <label>너비 <span>{{ layer.width }} px</span></label>
          <label>높이 <span>{{ layer.height }} px</span></label>
        </div>
      </section>

      <section class="prop-section">
        <h3>텍스트 스타일</h3>
        <div class="prop-grid">
          <label>폰트 <span>{{ layer.text.fontFamily }}</span></label>
          <label>크기 <span>{{ layer.text.fontSize }} px</span></label>
          <label>색상 <span>{{ layer.text.color }}</span></label>
          <label>자간 <span>{{ layer.text.tracking }}</span></label>
        </div>
      </section>

      <section class="prop-section">
        <h3>컬러 팔레트</h3>
        <div class="palette">
          @for (color of ['#FFFFFF', '#111827', '#EF4444', '#FACC15', '#22C55E', '#2563EB', '#7C3AED', '#000000']; track color) {
            <span class="swatch" [style.background]="color"></span>
          }
        </div>
      </section>

      <section class="style-cards">
        <article>
          <h3>박스</h3>
          <p>{{ layer.box.enabled ? '켜짐' : '꺼짐' }} · {{ layer.box.color }} · {{ layer.box.alpha * 100 }}%</p>
        </article>
        <article>
          <h3>윤곽선</h3>
          <p>{{ layer.outline.enabled ? '켜짐' : '꺼짐' }} · {{ layer.outline.width }} px · {{ layer.outline.color }}</p>
        </article>
        <article>
          <h3>그림자</h3>
          <p>{{ layer.shadow.enabled ? '켜짐' : '꺼짐' }} · X {{ layer.shadow.offsetX }} · Y {{ layer.shadow.offsetY }}</p>
        </article>
      </section>

      <section class="publish-gate">
        <strong>샘플 렌더가 아직 없습니다</strong>
        <span>3-5초 mp4 렌더 성공 후 게시할 수 있습니다.</span>
      </section>
    }
  </aside>
</section>
```

- [ ] **Step 5: Implement editor styles**

Create `clipper_angular/src/features/template-builder/components/template-builder-editor.component.scss`:

```scss
.template-editor {
  display: grid;
  grid-template-columns: 292px minmax(330px, 0.78fr) minmax(520px, 1.22fr);
  gap: 12px;
  min-height: calc(100vh - 120px);
}

.template-editor__left,
.template-editor__stage,
.template-editor__props {
  border: 1px solid #d9dee5;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

header {
  min-height: 52px;
  padding: 12px 14px;
  border-bottom: 1px solid #d9dee5;
}

h2,
h3,
p {
  margin: 0;
}

h3 {
  padding: 14px 12px 8px;
  font-size: 13px;
}

.ratio-slots,
.layer-list {
  display: grid;
  gap: 8px;
  padding: 0 12px 12px;
}

.ratio-slot,
.layer-row {
  border: 1px solid #d9dee5;
  border-radius: 8px;
  background: #fff;
  padding: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  text-align: left;
}

.ratio-slot--active,
.layer-row--selected {
  border-color: #2563eb;
  box-shadow: inset 3px 0 0 #2563eb;
}

.template-editor__stage {
  display: grid;
  grid-template-rows: 48px 1fr 54px;
}

.stage-toolbar,
.template-editor__stage footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-bottom: 1px solid #d9dee5;
  color: #667085;
  font-size: 12px;
}

.template-editor__stage footer {
  border-top: 1px solid #d9dee5;
  border-bottom: 0;
}

.stage-grid {
  display: grid;
  place-items: center;
  background:
    linear-gradient(90deg, #e5e7eb 1px, transparent 1px),
    linear-gradient(#e5e7eb 1px, transparent 1px);
  background-size: 24px 24px;
}

.phone-canvas {
  width: min(300px, 78%);
  aspect-ratio: 9 / 16;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  background: #111827;
  color: #fff;
  box-shadow: 0 10px 28px rgba(23, 31, 45, 0.1);
}

.title-main {
  position: absolute;
  top: 19%;
  left: 8%;
  right: 8%;
  text-align: center;
  font-size: 28px;
  font-weight: 900;
  line-height: 1.1;
}

.subtitle-box {
  position: absolute;
  bottom: 26%;
  left: 8%;
  right: 8%;
  min-height: 44px;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.25);
  text-align: center;
  font-size: 14px;
  font-weight: 800;
}

.selection-box {
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 26%;
  height: 44px;
  border: 2px solid #60a5fa;
}

.prop-tabs {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  padding: 10px 12px;
  border-bottom: 1px solid #d9dee5;
  background: #fafbfc;
}

.prop-tabs button {
  height: 32px;
  border: 1px solid #d9dee5;
  border-radius: 6px;
  background: #fff;
  font-weight: 800;
}

.prop-section,
.style-cards,
.publish-gate {
  margin: 12px;
}

.prop-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

label,
article {
  border: 1px solid #d9dee5;
  border-radius: 8px;
  padding: 10px;
  display: grid;
  gap: 6px;
}

label span {
  font-weight: 800;
}

.palette {
  display: grid;
  grid-template-columns: repeat(8, 28px);
  gap: 8px;
}

.swatch {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid rgba(15, 23, 42, 0.18);
}

.style-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.publish-gate {
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  border-radius: 8px;
  padding: 12px;
  display: grid;
  gap: 4px;
}
```

- [ ] **Step 6: Use editor component from page**

Modify `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`:

```ts
import { TemplateBuilderEditorComponent } from '../components/template-builder-editor.component';
```

Add `imports: [TemplateBuilderEditorComponent]` to the component metadata.

Modify `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html` by replacing the selected family main content:

```html
      @if (selectedFamily(); as family) {
        <app-template-builder-editor [family]="family" />
      } @else {
        <p>템플릿이 없습니다.</p>
      }
```

- [ ] **Step 7: Run editor and page tests**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts
```

Expected:

```text
TOTAL: 4 SUCCESS
```

- [ ] **Step 8: Commit**

Run:

```bash
cd clipper_angular
git add src/features/template-builder/components src/features/template-builder/pages
git commit -m "feat: build template builder editor shell"
```

### Task 7: Wire Editor Save, Validate, Sample Render, Publish Actions

**Files:**

- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Add failing editor output test**

Append to `template-builder-editor.component.spec.ts`:

```ts
  it('emits sample render and publish requests for the selected ratio', () => {
    let sample!: { familyId: string; ratio: string };
    let publish!: { familyId: string; ratio: string };
    fixture.componentInstance.sampleRenderRequest.subscribe((event) => {
      sample = event;
    });
    fixture.componentInstance.publishRequest.subscribe((event) => {
      publish = event;
    });

    fixture.componentInstance.requestSampleRender();
    fixture.componentInstance.requestPublish();

    expect(sample).toEqual({ familyId: 'family.1', ratio: 'full' });
    expect(publish).toEqual({ familyId: 'family.1', ratio: 'full' });
  });
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected:

```text
Property 'sampleRenderRequest' does not exist
```

- [ ] **Step 3: Add editor outputs and buttons**

Modify `template-builder-editor.component.ts` imports:

```ts
import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
```

Add to class:

```ts
  readonly sampleRenderRequest = output<{ familyId: string; ratio: TemplateBuilderRatio }>();
  readonly publishRequest = output<{ familyId: string; ratio: TemplateBuilderRatio }>();

  requestSampleRender(): void {
    this.sampleRenderRequest.emit({ familyId: this.family().id, ratio: this.selectedRatio() });
  }

  requestPublish(): void {
    this.publishRequest.emit({ familyId: this.family().id, ratio: this.selectedRatio() });
  }
```

Modify `template-builder-editor.component.html` publish gate section:

```html
      <section class="publish-gate">
        <strong>샘플 렌더가 아직 없습니다</strong>
        <span>3-5초 mp4 렌더 성공 후 게시할 수 있습니다.</span>
        <button type="button" (click)="requestSampleRender()">샘플 렌더 시작</button>
        <button type="button" (click)="requestPublish()">게시</button>
      </section>
```

- [ ] **Step 4: Add page handlers**

Modify `template-builder-page.component.ts` by adding:

```ts
  async handleSampleRender(event: { familyId: string; ratio: import('../models/template-builder').TemplateBuilderRatio }): Promise<void> {
    try {
      const updated = await this.service.startSampleRender(event.familyId, event.ratio);
      this.replaceFamily(updated);
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : '샘플 렌더를 시작하지 못했습니다.');
    }
  }

  async handlePublish(event: { familyId: string; ratio: import('../models/template-builder').TemplateBuilderRatio }): Promise<void> {
    try {
      const updated = await this.service.publishVariant(event.familyId, event.ratio);
      this.replaceFamily(updated);
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : '템플릿을 게시하지 못했습니다.');
    }
  }

  private replaceFamily(updated: TemplateBuilderFamily): void {
    this.families.update((families) =>
      families.map((family) => family.id === updated.id ? updated : family),
    );
    this.selectedFamilyId.set(updated.id);
  }
```

Modify page template editor usage:

```html
        <app-template-builder-editor
          [family]="family"
          (sampleRenderRequest)="handleSampleRender($event)"
          (publishRequest)="handlePublish($event)"
        />
```

- [ ] **Step 5: Run focused Angular tests**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts
```

Expected:

```text
TOTAL: 5 SUCCESS
```

- [ ] **Step 6: Commit**

Run:

```bash
cd clipper_angular
git add src/features/template-builder/components src/features/template-builder/pages
git commit -m "feat: wire template builder publish actions"
```

### Task 8: Full Verification And Documentation

**Files:**

- Modify: `.codex/implementation/TASKS.md`
- Modify: `.codex/implementation/WORKLOG.md`
- Modify: `.codex/session-logs/2026-05-07.log`

- [ ] **Step 1: Run backend full template-builder verification**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js
```

Expected:

```text
# fail 0
```

- [ ] **Step 2: Run frontend focused verification**

Run:

```bash
cd clipper_angular
./node_modules/.bin/ng test --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
npm run build:electron -- --progress=false
```

Expected:

```text
TOTAL: 7 SUCCESS
Application bundle generation complete
```

- [ ] **Step 3: Run diff checks**

Run:

```bash
git -C clipper_nestjs diff --check
git -C clipper_angular diff --check
```

Expected: no output and exit code 0 for both commands.

- [ ] **Step 4: Update `.codex/implementation/TASKS.md`**

Add under a new heading `## Template Builder Implementation (2026-05-07)`:

```markdown
- [x] Template Builder approved v4 spec recorded.
- [x] NestJS Template Builder DTO/repository/service/controller/module first slice.
- [x] Angular top-level `/templates` route and nav entry.
- [x] Angular v4 editor shell with fixed ratio slots, narrower canvas, wider property panel, color palette, box/outline/shadow controls.
- [x] Sample render and publish action plumbing.
- [ ] Follow-up: bridge published custom templates into `TemplatePresetCatalogService` consumers after custom render fixtures exist.
- [ ] Follow-up: replace dry-run sample render status with real 3-5 second render recipe execution.
- [ ] Follow-up: add custom layout/font asset upload.
```

- [ ] **Step 5: Update `.codex/implementation/WORKLOG.md`**

Append:

```markdown
## 2026-05-07 Template Builder first implementation slice

- Implemented NestJS Template Builder catalog boundary with local JSON repository.
- Added system/custom family and fixed ratio variant model.
- Added validation, sample render state, and publish gate plumbing.
- Added Angular top-level `/templates` route and `템플릿` nav item.
- Added approved v4 editor shell: left family/ratio/layer panel, narrowed canvas, wide properties panel, color palette, and box/outline/shadow controls.
- Verification:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js`
  - `clipper_angular ./node_modules/.bin/ng test --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts`
  - `clipper_angular npm run build:electron -- --progress=false`
  - `git -C clipper_nestjs diff --check`
  - `git -C clipper_angular diff --check`
- Remaining risk:
  - Sample render service is first-slice plumbing and must be replaced by a real 3-5 second video render job before production publish semantics are complete.
  - Published custom templates are not yet consumed by Clipper1/Variation template pickers.
```

- [ ] **Step 6: Update session log**

Append to `.codex/session-logs/2026-05-07.log`:

```markdown
[2026-05-07 HH:MM:SS KST] Template Builder implementation slice verification

Implemented:
- NestJS Template Builder DTO/repository/service/controller/module.
- Angular Template Builder API client, route/nav/page/editor shell.
- Approved v4 layout with fixed ratio slots, narrow canvas, wide properties panel, color palette, box/outline/shadow sections.

Verification:
- `clipper_nestjs npm run build`: passed.
- `clipper_nestjs node --test test/template-builder-validation.test.js test/template-builder-repository.test.js test/template-builder-api.test.js`: passed.
- `clipper_angular focused ng tests`: passed.
- `clipper_angular npm run build:electron -- --progress=false`: passed.
- `git diff --check` for NestJS and Angular: passed.
```

- [ ] **Step 7: Commit docs if a git repository exists**

Run:

```bash
git rev-parse --show-toplevel
```

Expected in current workspace:

```text
fatal: not a git repository
```

If the root remains not a git repository, do not commit `.codex`. Report that `.codex` docs were updated outside subrepo git history.

## Plan Self-Review

Spec coverage:

- Top-level `템플릿` menu: Task 5.
- Shared Template Catalog backend boundary: Tasks 1-3.
- Local repository with future adapter replacement: Task 2.
- System/custom model: Tasks 1 and 3.
- Fixed ratio slots only: Tasks 1, 3, 6.
- Narrower canvas and wider properties panel: Task 6.
- Color palette: Task 6.
- Box/outline/shadow controls: Task 6.
- Draft/published lifecycle and sample-render publish gate: Tasks 3 and 7.
- Angular zoneless rules: Tasks 4-7 tests use `provideExperimentalZonelessChangeDetection()`.

Placeholder scan:

- The implementation plan intentionally contains no empty deferred step markers and no "similar to previous task" shortcuts.

Type consistency:

- Backend and frontend use matching names: `TemplateBuilderFamily`, `TemplateBuilderVariant`, `TemplateBuilderRatio`, `TemplateBuilderLayers`.
- `TemplateBuilderService` method names match Angular API methods and NestJS service methods.

Known planned follow-ups:

- Bridge published custom templates into `TemplatePresetCatalogService` consumers.
- Add asset upload for layout images and fonts.

## Post-plan Update: Real Sample Render First Slice

2026-05-07 13:55 KST:

- Completed the planned follow-up that replaces dry-run/fake sample render success with real 3-second MP4 execution.
- `TemplateBuilderSampleRenderService` now stages bundled sample media under `CLIPPER_DATA_DIR/template-samples/...`, builds a `RenderRecipe`, resolves `video.render.local_ffmpeg.basic`, and calls the provider with `dryRun: false`.
- The publish gate now depends on a sample render snapshot that was produced from a real `render.video` artifact URI.
- Verification:
  - `clipper_nestjs npm run build`
  - `clipper_nestjs node --test test/template-builder-api.test.js`
  - direct smoke with actual `LocalFfmpegBasicRenderProvider`, producing a 3-second MP4 of `93181` bytes.
- Remaining renderer parity risk:
  - The current MP4 validates the real render path, but does not yet compose all legacy Clipper1 template layers, logo, subtitle/TTS, and BGM. That work belongs to the template-aware renderer parity follow-up.
