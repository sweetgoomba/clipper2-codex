# Template Builder Official Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Template Builder from implicit local/system editing toward explicit edit sessions, stable card thumbnails, and a DB/S3-backed official template registry.

**Architecture:** Keep Angular and existing `/v1/template-builder` DTOs insulated from DB/S3 details. Introduce official-template repository and asset-storage abstractions behind `TemplateBuilderService`, while preserving local JSON for personal templates. Implement in phases so publish removal, edit-session state, thumbnail separation, and DB/S3 registration are independently testable.

**Tech Stack:** Angular standalone components/signals, NestJS services/controllers, Node test runner, local JSON repositories, Postgres via `pg`, S3 via `@aws-sdk/client-s3`, existing Template Builder DTOs.

---

## Scope And Order

This is intentionally split into five phases. Do not start DB/S3 writes until Phase 1 and Phase 2 are green, because the current UI still conflates sample render, publish status, card thumbnail, and immediate persistence.

1. Phase 1: Remove publish semantics and split card thumbnails from sample render thumbnails.
2. Phase 2: Add explicit edit mode and session-scoped undo/redo in Angular, using existing save APIs.
3. Phase 3: Add backend repository/storage interfaces and env names without changing runtime behavior.
4. Phase 4: Add Postgres official template repository, S3 asset storage, and admin-only `register-official`.
5. Phase 5: Add import/register script for the corrected 21 legacy templates.

## File Map

### Angular

- Modify `clipper_angular/src/features/template-builder/models/template-builder.ts`
  - Add `cardThumbnailUri?: string | null`.
  - Add `capabilities.canRegisterOfficial?: boolean`.
  - Keep `ownerType: 'system' | 'user'` for DTO compatibility.
- Modify `clipper_angular/src/features/template-builder/components/template-family-gallery.component.ts`
  - Use `family.cardThumbnailUri` before sample render thumbnails.
  - Show `편집 중` badge when selected family has active local edit session.
- Modify `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
  - Remove `게시` button.
  - Keep sample render action as preview-only.
  - Add `템플릿 등록` action when `canRegisterOfficial` is true and edit mode is active.
- Modify `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
  - Remove `publishRequest`.
  - Add `registerOfficialRequest`.
  - Add `editMode` input and use it to gate preview interaction/inspector controls.
- Modify `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
  - Add explicit edit-session state.
  - Scope undo/redo to current edit session.
  - Block accidental template switch when draft is dirty.
  - Flush/save via existing `updateVariant` batching in Phase 2.
- Modify matching Angular specs:
  - `components/template-family-gallery.component.spec.ts`
  - `components/template-builder-editor.component.spec.ts`
  - `pages/template-builder-page.component.spec.ts`
  - `services/template-builder.service.spec.ts`

### NestJS

- Modify `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
  - Add `cardThumbnailUri?: string | null`.
  - Add `canRegisterOfficial?: boolean`.
  - Keep `TemplateBuilderVariantStatus` temporarily to minimize blast radius, but stop using `published` as UI gate.
- Modify `clipper_nestjs/src/template-builder/template-builder-seed.ts`
  - Seed `cardThumbnailUri` from legacy preset thumb.
  - Stop treating `sampleRender.thumbnailUri` as card thumbnail source.
- Modify `clipper_nestjs/src/template-builder/template-builder.service.ts`
  - Remove `publishVariant` from main flow.
  - Add `registerOfficialTemplate`.
  - Add official repository merge behind `listFamilies`.
- Modify `clipper_nestjs/src/template-builder/template-builder.controller.ts`
  - Remove or deprecate `publish` endpoint.
  - Add `POST /template-builder/families/:familyId/register-official`.
- Modify `clipper_nestjs/src/template-builder/template-builder.repository.ts`
  - Keep JSON personal repository.
  - Add `TemplateBuilderOfficialRepository` abstraction.
- Create `clipper_nestjs/src/template-builder/template-builder-official-postgres.repository.ts`
  - Postgres-backed official family/variant/asset read/write.
- Create `clipper_nestjs/src/template-builder/template-builder-asset-storage.ts`
  - Common local/S3 asset storage interfaces.
- Create `clipper_nestjs/src/template-builder/template-builder-s3-asset-storage.ts`
  - Upload official assets to `clipperstudio/templates/...`.
- Create `clipper_nestjs/scripts/register-official-template-seed.js`
  - Register corrected 21 legacy families from current Template Builder DTOs.
- Modify `clipper_nestjs/.env.example`
  - Add DB/S3 variable names only, no secrets.
- Modify matching NestJS tests:
  - `test/template-builder-api.test.js`
  - `test/template-builder-preset-source.test.js`
  - Add `test/template-builder-official-repository.test.js`
  - Add `test/template-builder-register-official.test.js`

---

## Phase 1: Remove Publish Semantics And Split Card Thumbnail

### Task 1.1: Add `cardThumbnailUri` To DTOs And Seed

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Test: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.spec.ts`

- [ ] **Step 1: Write failing NestJS seed test**

Add this assertion to the existing system preset test in `clipper_nestjs/test/template-builder-api.test.js`:

```js
assert.equal(
  template1.cardThumbnailUri,
  'template-presets/legacy-clipper1/assets/1_ratio_16_9_thumb.png',
);
assert.equal(template1Variant.sampleRender.thumbnailUri, null);
```

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Expected: FAIL because `cardThumbnailUri` does not exist and seed still stores thumbnail under `sampleRender.thumbnailUri`.

- [ ] **Step 2: Implement NestJS DTO and seed**

In `TemplateBuilderFamily`, add:

```ts
cardThumbnailUri?: string | null;
```

In `variantFromPreset`, change `sampleRender` to:

```ts
variant.sampleRender = {
  status: 'missing',
  message: '샘플 렌더 없음',
};
```

In `systemFamiliesFromPresets`, set family-level thumbnail when creating/updating family:

```ts
const thumbnailUri = preset.preview?.remoteImageUrl ?? preset.preview?.remoteLargeImageUrl ?? null;
const family = families.get(designId) ?? { ... };
if (!family.cardThumbnailUri && thumbnailUri) {
  family.cardThumbnailUri = thumbnailUri;
}
```

- [ ] **Step 3: Update Angular model and gallery test**

In Angular model `TemplateBuilderFamily`, add:

```ts
cardThumbnailUri?: string | null;
```

In gallery spec, add a case:

```ts
it('uses cardThumbnailUri before sample render thumbnails', () => {
  const family = familyFixture({
    cardThumbnailUri: 'template-presets/legacy-clipper1/assets/1_ratio_16_9_thumb.png',
    variants: {
      full: variantFixture({
        sampleRender: {
          status: 'succeeded',
          thumbnailUri: 'sample-render-thumb.jpg',
        },
      }),
    },
  });

  fixture.componentRef.setInput('families', [family]);
  fixture.detectChanges();

  const image = fixture.nativeElement.querySelector('img') as HTMLImageElement;
  expect(image.src).toContain('template-presets/legacy-clipper1/assets/1_ratio_16_9_thumb.png');
});
```

- [ ] **Step 4: Implement gallery priority**

Use this priority in `template-family-gallery.component.ts`:

```ts
if (family.cardThumbnailUri) return this.resolveAssetUrl(family.cardThumbnailUri);
if (variant.sampleRender.status === 'succeeded' && variant.sampleRender.thumbnailUri) {
  return this.service.sampleRenderThumbnailFileUrl(this.backendBaseUrl(), family.id, ratio);
}
```

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-api.test.js

cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-family-gallery.component.spec.ts
npm run build
```

- [ ] **Step 6: Commit**

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git add src/template-builder/dto/template-builder.dto.ts src/template-builder/template-builder-seed.ts test/template-builder-api.test.js
git commit -m "Separate template card thumbnails from samples"

cd /Users/jina/project/adlight/clipper_angular
git add src/features/template-builder/models/template-builder.ts src/features/template-builder/components/template-family-gallery.component.ts src/features/template-builder/components/template-family-gallery.component.spec.ts
git commit -m "Prefer template card thumbnails in gallery"
```

### Task 1.2: Remove Publish UI/API Gate

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify tests containing `publishVariant`.

- [ ] **Step 1: Write failing Angular tests**

In `template-builder-editor.component.spec.ts`, replace publish expectations:

```ts
it('keeps sample render available without showing publish action', () => {
  fixture.componentRef.setInput('family', familyFixture());
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector('[data-testid="sample-render-button"]')).not.toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="publish-button"]')).toBeNull();
});
```

In page spec, remove publish service delegation and assert no `publishVariant` call is made by the UI.

- [ ] **Step 2: Write failing NestJS test**

In `template-builder-api.test.js`, replace publish test with:

```js
assert.equal(typeof service.publishVariant, 'undefined');
```

If direct method deletion is too disruptive for TypeScript compile, keep method private/inaccessible and remove controller route. Controller test should verify route is gone by not importing a route helper; service tests should no longer call publish.

- [ ] **Step 3: Remove Angular publish outputs**

Remove:

```ts
readonly publishRequest = output<{ familyId: string; ratio: TemplateBuilderRatio }>();
publishSelectedVariant(): void { ... }
```

Remove `(publishRequest)="handlePublish($event)"` from the page template and `handlePublish` from page component.

- [ ] **Step 4: Remove NestJS publish route**

Remove from controller:

```ts
@Post('families/:familyId/variants/:ratio/publish')
publishVariant(...)
```

Keep `TemplateBuilderVariantStatus` for now but stop requiring sample success for any UI action.

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build

cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js
```

Expected: existing preset-source tests will need updates because they currently refer to “published” variants. Change terminology to “registered official” in later phase or mark those tests to use official repository once Phase 4 lands.

- [ ] **Step 6: Commit**

```bash
git add ...
git commit -m "Remove template builder publish action"
```

---

## Phase 2: Explicit Edit Mode And Scoped Undo

### Task 2.1: Add Angular Edit Session State

**Files:**
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Write failing edit-mode test**

Add:

```ts
it('does not persist layer edits until edit mode is started', async () => {
  await renderPageWithFamilies([familyWithFullVariant('family.view-only')]);

  await emitVariantPatch({ layers: { subtitleText: { x: 123 } } });

  expect(service.updateVariantCalls).toEqual([]);
  expect(fixture.componentInstance.undoStack()).toEqual([]);
});
```

Add:

```ts
it('starts an edit session and saves changes without leaving edit mode', async () => {
  await renderPageWithFamilies([familyWithFullVariant('family.edit')]);

  clickByTestId('edit-template-button');
  await emitVariantPatch({ layers: { subtitleText: { x: 123 } } });
  clickByTestId('save-template-button');

  expect(service.updateVariantCalls.at(-1)).toEqual({
    familyId: 'family.edit',
    ratio: 'full',
    request: { layers: { subtitleText: { x: 123 } } },
  });
  expect(fixture.componentInstance.editSession()?.familyId).toBe('family.edit');
});
```

- [ ] **Step 2: Add state shape**

In page component:

```ts
interface TemplateBuilderEditSession {
  id: string;
  familyId: string;
  startedAt: string;
  baseFamily: TemplateBuilderFamily;
  draftFamily: TemplateBuilderFamily;
  dirty: boolean;
}

readonly editSession = signal<TemplateBuilderEditSession | null>(null);
readonly isEditingSelectedFamily = computed(() =>
  this.editSession()?.familyId === this.selectedFamily()?.id,
);
```

- [ ] **Step 3: Gate edits**

When `handleVariantPatch` receives changes:

```ts
if (!this.isEditingSelectedFamily()) return;
```

Update editor input:

```html
[editMode]="isEditingSelectedFamily()"
```

In editor, make `isReadonly()` include edit mode:

```ts
isReadonly(): boolean {
  return this.readonly() || !this.editMode();
}
```

- [ ] **Step 4: Add buttons**

In page header or editor toolbar:

```html
<button data-testid="edit-template-button" (click)="startEditSession()">편집 시작</button>
<button data-testid="save-template-button" (click)="saveEditSession()" [disabled]="!editSession()?.dirty">저장</button>
<button data-testid="cancel-edit-button" (click)="cancelEditSession()">취소</button>
```

- [ ] **Step 5: Verify and commit**

Run Angular page specs and build, then commit.

### Task 2.2: Scope Undo/Redo To Edit Session

**Files:**
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Write failing regression**

```ts
it('does not undo into a previously edited template after switching sessions', async () => {
  await renderPageWithFamilies([
    familyWithFullVariant('family.first'),
    familyWithFullVariant('family.second'),
  ]);

  clickByTestId('edit-template-button');
  await emitVariantPatch({ layers: { subtitleText: { x: 111 } } });
  clickByTestId('save-template-button');
  clickByTestId('cancel-edit-button');

  selectFamily('family.second');
  clickByTestId('edit-template-button');
  await emitVariantPatch({ layers: { subtitleText: { x: 222 } } });
  await undo();
  await undo();

  expect(fixture.componentInstance.selectedFamily()?.id).toBe('family.second');
  expect(fixture.componentInstance.canUndo()).toBeFalse();
});
```

- [ ] **Step 2: Key stacks by edit session**

Replace global stack semantics with:

```ts
interface TemplateBuilderHistoryState {
  sessionId: string;
  undo: TemplateBuilderHistoryEntry[];
  redo: TemplateBuilderHistoryEntry[];
}
```

On `startEditSession`, set empty stacks. On `cancelEditSession`, clear stacks. On template selection outside current session, do not reuse old entries.

- [ ] **Step 3: Verify and commit**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build
```

Commit:

```bash
git add src/features/template-builder/pages/template-builder-page.component.ts src/features/template-builder/pages/template-builder-page.component.spec.ts
git commit -m "Scope template builder undo to edit sessions"
```

---

## Phase 3: Repository And Storage Abstractions

### Task 3.1: Add Official Repository Interface

**Files:**
- Modify: `clipper_nestjs/src/template-builder/template-builder.repository.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.module.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`

- [ ] **Step 1: Write failing merge test**

```js
test('template builder service lists official repository families before local personal templates', async () => {
  const official = {
    list: async () => [officialFamilyFixture('official.template.1')],
    get: async (id) => id === 'official.template.1' ? officialFamilyFixture(id) : null,
    upsert: async (family) => family,
  };
  const service = serviceFixture({ officialRepository: official });

  const families = await service.listFamilies();

  assert.equal(families[0].id, 'official.template.1');
  assert.equal(families[0].ownerType, 'system');
  assert.equal(families[0].capabilities.canRegisterOfficial, false);
});
```

- [ ] **Step 2: Add interface**

```ts
export abstract class TemplateBuilderOfficialRepository {
  abstract list(): Promise<TemplateBuilderFamily[]>;
  abstract get(familyId: string): Promise<TemplateBuilderFamily | null>;
  abstract upsert(family: TemplateBuilderFamily): Promise<TemplateBuilderFamily>;
}
```

Inject it as optional in `TemplateBuilderService`.

- [ ] **Step 3: Merge official families**

In `listFamilies`, merge in order:

```ts
const official = this.officialRepository ? await this.officialRepository.list() : [];
const systemSeed = await this.systemFamilies();
const custom = await this.repository.list();
return [...official, ...systemSeed, ...custom]
  .map((family) => this.withCapabilities(family))
  .sort(...);
```

Prevent duplicate IDs by later source replacing earlier source only if explicitly desired. Initial rule: official wins over system seed for same `id`.

- [ ] **Step 4: Verify and commit**

Run NestJS API tests and build, then commit.

### Task 3.2: Add Asset Storage Interfaces And Env Names

**Files:**
- Create: `clipper_nestjs/src/template-builder/template-builder-asset-storage.ts`
- Create: `clipper_nestjs/src/template-builder/template-builder-s3-asset-storage.ts`
- Modify: `clipper_nestjs/.env.example`
- Test: `clipper_nestjs/test/template-builder-register-official.test.js`

- [ ] **Step 1: Add `.env.example` names**

```dotenv
CLIPPER2_TEMPLATE_DB_HOST=
CLIPPER2_TEMPLATE_DB_PORT=5432
CLIPPER2_TEMPLATE_DB_USER=
CLIPPER2_TEMPLATE_DB_PASSWORD=
CLIPPER2_TEMPLATE_DB_NAME=
CLIPPER2_TEMPLATE_S3_BUCKET=clipperstudio
CLIPPER2_TEMPLATE_S3_REGION=ap-northeast-2
CLIPPER2_TEMPLATE_S3_ACCESS_KEY_ID=
CLIPPER2_TEMPLATE_S3_SECRET_ACCESS_KEY=
```

- [ ] **Step 2: Define storage interface**

```ts
export interface StoredTemplateBuilderAsset {
  bucket: string;
  key: string;
  publicUrl: string | null;
  contentType: string | null;
  byteSize: number | null;
  width?: number | null;
  height?: number | null;
}

export abstract class TemplateBuilderAssetStorage {
  abstract putObject(args: {
    key: string;
    body: Buffer;
    contentType?: string | null;
  }): Promise<StoredTemplateBuilderAsset>;
}
```

- [ ] **Step 3: Implement S3 storage**

Use `@aws-sdk/client-s3` with `PutObjectCommand`. Add dependency only when implementing this task:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm install @aws-sdk/client-s3 pg
```

Expected package updates: `package.json`, `package-lock.json`.

- [ ] **Step 4: Verify and commit**

Run build and targeted tests. Commit env/interface separately from DB behavior.

---

## Phase 4: Register Official Templates

### Task 4.1: Add Postgres Official Repository

**Files:**
- Create: `clipper_nestjs/src/template-builder/template-builder-official-postgres.repository.ts`
- Test: `clipper_nestjs/test/template-builder-official-repository.test.js`

- [ ] **Step 1: Write test with fake pg client**

Do not require a live DB in unit tests. Inject a minimal client:

```js
const queries = [];
const client = {
  query: async (sql, params) => {
    queries.push({ sql, params });
    if (sql.includes('select')) return { rows: [] };
    return { rows: [{ id: params[0] }] };
  },
};
```

Assert upsert writes family, variants, and assets with JSONB payloads.

- [ ] **Step 2: Implement repository**

Use the schema from the design doc:

```sql
clipper2_template_families
clipper2_template_variants
clipper2_template_assets
```

Repository methods must map DB official rows back to `TemplateBuilderFamily` DTO with:

```ts
ownerType: 'system',
source: 'built_in',
readonly: true,
```

- [ ] **Step 3: Verify and commit**

Run repository tests and NestJS build. Commit.

### Task 4.2: Add Admin-Only Register Official Endpoint

**Files:**
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Test: `clipper_nestjs/test/template-builder-register-official.test.js`
- Modify Angular service/page/editor for button.

- [ ] **Step 1: Write NestJS failing tests**

```js
test('register official rejects when admin mode is disabled', async () => {
  const service = serviceFixture({ officialRepository, assetStorage });
  await assert.rejects(
    () => service.registerOfficialTemplate('custom.template.1'),
    /관리자 권한이 필요합니다/,
  );
});
```

```js
test('register official stores current family as official without requiring sample render', async () => {
  service.enableSystemTemplateEditMode();
  const family = await service.createFamily({ name: '공식 후보', ratio: 'full' });
  const registered = await service.registerOfficialTemplate(family.id);

  assert.equal(registered.ownerType, 'system');
  assert.equal(registered.readonly, true);
  assert.equal(officialRepository.upserts.length, 1);
});
```

- [ ] **Step 2: Implement service method**

```ts
async registerOfficialTemplate(familyId: string): Promise<TemplateBuilderFamily> {
  if (!this.systemTemplateEditEnabled()) {
    throw new BadRequestException('관리자 권한이 필요합니다.');
  }
  if (!this.officialRepository) {
    throw new BadRequestException('공식 템플릿 저장소를 사용할 수 없습니다.');
  }
  const source = await this.getFamily(familyId);
  const official = this.prepareOfficialFamily(source);
  return this.withCapabilities(await this.officialRepository.upsert(official));
}
```

- [ ] **Step 3: Add controller route**

```ts
@Post('families/:familyId/register-official')
registerOfficialTemplate(@Param('familyId') familyId: string) {
  return this.service.registerOfficialTemplate(familyId);
}
```

- [ ] **Step 4: Add Angular button**

Show only when:

```ts
family.capabilities?.canRegisterOfficial && isEditingSelectedFamily()
```

The button text is `템플릿 등록`.

- [ ] **Step 5: Verify and commit**

Run Angular editor/page specs, NestJS register/API tests, and builds. Commit.

---

## Phase 5: Register The Corrected 21 Legacy Templates

### Task 5.1: Add Import/Register Script

**Files:**
- Create: `clipper_nestjs/scripts/register-official-template-seed.js`
- Test: `clipper_nestjs/test/template-builder-register-official-seed-script.test.js`

- [ ] **Step 1: Script behavior**

The script must:

1. Load system families through `TemplateBuilderService`, including current system overrides.
2. Filter only 21 official legacy families.
3. Refuse to run if custom clone families are present unless `--allow-custom` is passed.
4. Upload or preserve asset references based on current implementation mode.
5. Upsert official families into Postgres repository.

- [ ] **Step 2: Add dry-run mode**

Required command:

```bash
node scripts/register-official-template-seed.js --dry-run
```

Expected output includes:

```text
21 legacy official families ready
0 custom clone families included
```

- [ ] **Step 3: Add live mode**

Required command:

```bash
node scripts/register-official-template-seed.js --apply
```

Live mode must require all DB/S3 env vars and fail clearly if missing.

- [ ] **Step 4: Verify and commit**

Run script tests, NestJS build, and dry-run against local current data. Commit.

---

## Final Verification Checklist

- [ ] `clipper_nestjs npm run build`
- [ ] `clipper_nestjs node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-register-official.test.js test/template-builder-official-repository.test.js`
- [ ] `clipper_angular npm run build`
- [ ] `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-family-gallery.component.spec.ts`
- [ ] `clipper_python uv run pytest tests/test_template_builder_text_renderer.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_clipper1_video_render_text_artifact_job.py -q`
- [ ] Packaged Electron smoke test verifies:
  - Existing 21 templates keep card thumbnails.
  - Sample render does not change card thumbnail.
  - Edit mode is required before changes.
  - Undo cannot cross template sessions.
  - Admin mode shows `템플릿 등록`.
  - Non-admin mode keeps new/clone templates local only.

## Self-Review Notes

- The plan keeps DTO `ownerType: system/user` for now to avoid broad Angular churn, while DB internal language can use official/personal.
- The plan does not require live DB/S3 for unit tests; live registration is isolated to script dry-run/apply and later manual verification.
- The plan preserves current local JSON custom templates through Phase 4.
- The plan removes publish semantics before adding official registration so sample render and registration do not stay coupled.
