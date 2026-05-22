# Template Builder Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Template Builder around a card-based template gallery, a narrower inspector, and split editor components, while first exposing the new layout in a browser-only mockup route for visual approval.

**Architecture:** Keep template data flow anchored in the existing NestJS family/variant API, add a minimal lineage field so the gallery can distinguish clones from ordinary user templates, and let Angular render the redesign through a temporary mockup route before the real page is swapped over. The real page will then be decomposed into gallery, workspace, canvas, inspector, and property-section components so layout, selection logic, and property editing stop living in one monolith.

**Tech Stack:** Angular 19 standalone components, NestJS DTO/service tests, signal-based state, zoneless TestBed, existing Template Builder preview/render contracts.

---

### Task 1: Add Clone Lineage Metadata For Gallery Badges

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/services/template-builder.service.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Write the failing NestJS test**

Add a Node test that proves cloned families carry an explicit lineage field.

```js
it('marks cloned families with originFamilyId for gallery badges', async () => {
  const cloned = await service.cloneFamily('system.legacy.clipper1.template.1', {
    name: '뉴스 강조형 복제본',
    ratio: '16:9',
    cloneFromRatio: '16:9',
  });
  assert.equal(cloned.originFamilyId, 'system.legacy.clipper1.template.1');
});
```

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js --test-name-pattern "marks cloned families with originFamilyId"
```

Expected: FAIL before `cloneFamily()` stamps the lineage field.

- [ ] **Step 2: Write the minimal implementation**

Add `originFamilyId?: string | null` to the family DTO and set it in `cloneFamily()` when a new custom family is created from an existing family.

```ts
// clipper_nestjs/src/template-builder/dto/template-builder.dto.ts
export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: TemplateBuilderOwnerType;
  source: TemplateBuilderSource;
  originFamilyId?: string | null;
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}
```

```ts
// clipper_nestjs/src/template-builder/template-builder.service.ts
const family: TemplateBuilderFamily = {
  id: familyId,
  name: request.name.trim() || `${source.name} 복제본`,
  ownerType: 'user',
  source: 'custom',
  originFamilyId: source.id,
  readonly: false,
  createdAt: now,
  updatedAt: now,
  variants,
};
```

Mirror the new optional field in Angular types so the gallery can read it without extra mapping.

```ts
// clipper_angular/src/features/template-builder/models/template-builder.ts
export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: 'system' | 'user';
  source: 'built_in' | 'custom';
  originFamilyId?: string | null;
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}
```

- [ ] **Step 3: Run the focused tests**

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js
cd ../clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts
```

Expected: PASS once the clone lineage is returned by API and accepted by the client model.

- [ ] **Step 4: Commit**

```bash
git add src/template-builder/dto/template-builder.dto.ts src/template-builder/template-builder.service.ts test/template-builder-api.test.js
git commit -m "feat: add template builder clone lineage"
```

### Task 2: Add A Browser-Only Redesign Mockup Route

**Files:**
- Modify: `clipper_angular/src/app/app.routes.ts`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.ts`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.html`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.scss`
- Create: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts`

- [ ] **Step 1: Write the failing route/component test**

Add a spec that loads the redesign preview page and expects a gallery grid, a narrower inspector, and fixed actions near the inspector header.

```ts
it('renders the redesign mockup shell', () => {
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelector('[data-testid="template-gallery-grid"]')).not.toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="template-inspector-actions"]')).not.toBeNull();
  expect(fixture.nativeElement.textContent).toContain('기본 제공');
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts
```

Expected: FAIL until the route and standalone component exist.

- [ ] **Step 2: Write the minimal implementation**

Add a lazy route for a separate preview page, for example `templates-preview`, and render a read-only mockup shell that reuses live family data but disables mutation buttons.

```ts
// clipper_angular/src/app/app.routes.ts
{
  path: 'templates-preview',
  loadComponent: () =>
    import('../features/template-builder/pages/template-builder-redesign-preview.component').then(
      (m) => m.TemplateBuilderRedesignPreviewComponent,
    ),
},
```

The mockup page should:

- reuse `TemplateBuilderService.listFamilies()`
- render a gallery grid with thumbnails and badges
- render a dummy workspace/canvas column
- render a narrower inspector column with `샘플 렌더 시작` and `게시` disabled

- [ ] **Step 3: Run the route/component tests**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts
```

Expected: PASS once the mockup page exists and renders the intended shell.

- [ ] **Step 4: Commit**

```bash
git add src/app/app.routes.ts src/features/template-builder/pages/template-builder-redesign-preview.component.ts src/features/template-builder/pages/template-builder-redesign-preview.component.html src/features/template-builder/pages/template-builder-redesign-preview.component.scss src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts
git commit -m "feat: add template builder redesign mockup route"
```

### Task 3: Convert The Left Template List Into A Thumbnail Grid

**Files:**
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-family-card.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-family-card.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-family-card.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.spec.ts`

- [ ] **Step 1: Write the failing gallery test**

Add a spec that renders a family card grid and asserts the card contents and badge labels.

```ts
it('renders template cards with thumbnail, name, and badge', () => {
  fixture.detectChanges();
  const cards = fixture.nativeElement.querySelectorAll('[data-testid="template-family-card"]');
  expect(cards.length).toBeGreaterThan(0);
  expect(cards[0].textContent).toContain('기본 제공');
  expect(cards[0].querySelector('img')).not.toBeNull();
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-family-gallery.component.spec.ts
```

Expected: FAIL until the gallery/card components are created.

- [ ] **Step 2: Write the minimal implementation**

Move the current left-side family list out of the page template and replace it with a gallery component that renders a CSS grid.

```html
<!-- clipper_angular/src/features/template-builder/pages/template-builder-page.component.html -->
<app-template-family-gallery
  [families]="families()"
  [selectedFamilyId]="selectedFamilyId()"
  (familySelected)="selectFamily($event)"
></app-template-family-gallery>
```

Use card badges like this:

```ts
const badge = family.ownerType === 'system'
  ? '기본 제공'
  : family.originFamilyId
    ? '복제본'
    : '사용자 템플릿';
```

Thumbnail selection rules:

- system family: `thumbnail_url` from the catalog if present
- user family: `sampleRender.thumbnailUri` if succeeded
- fallback: neutral thumbnail fallback

- [ ] **Step 3: Run the gallery tests and page tests**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-family-gallery.component.spec.ts
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts
```

Expected: PASS after the page uses the gallery components and the new badge model.

- [ ] **Step 4: Commit**

```bash
git add src/features/template-builder/pages/template-builder-page.component.ts src/features/template-builder/pages/template-builder-page.component.html src/features/template-builder/pages/template-builder-page.component.scss src/features/template-builder/components/template-family-gallery.component.ts src/features/template-builder/components/template-family-gallery.component.html src/features/template-builder/components/template-family-gallery.component.scss src/features/template-builder/components/template-family-card.component.ts src/features/template-builder/components/template-family-card.component.html src/features/template-builder/components/template-family-card.component.scss
git commit -m "feat: render template builder gallery cards"
```

### Task 4: Split The Editor Into Workspace, Canvas, And Inspector Pieces

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-property-section.component.ts`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-property-section.component.html`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-property-section.component.scss`

- [ ] **Step 1: Write the failing editor test**

Add a spec that confirms the old `속성 · {layer}` header and the `위치 / 텍스트 / 색상 / 박스 / 효과` tab row are gone, and that the sample render/publish actions are pinned to the inspector.

```ts
it('moves sample render and publish into the inspector header and removes tab rows', () => {
  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).not.toContain('속성 ·');
  expect(fixture.nativeElement.querySelector('[data-testid="template-editor-tabs"]')).toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="template-inspector-actions"]')).not.toBeNull();
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: FAIL before the inspector layout is refactored.

- [ ] **Step 2: Write the minimal implementation**

Move the layout into a workspace shell and make the inspector own the action buttons, section list, and section-specific property rendering.

```html
<!-- clipper_angular/src/features/template-builder/components/template-builder-editor.component.html -->
<section class="template-editor">
<app-template-builder-workspace
  [family]="family()"
  [selectedRatio]="selectedRatio()"
  [selectedFamily]="selectedFamily()"
  [galleryFamilies]="families()"
  (sampleRenderRequest)="requestSampleRender()"
  (publishRequest)="requestPublish()"
></app-template-builder-workspace>
</section>
```

The inspector should render property sections directly, without a horizontal tab strip.

```html
<header class="template-inspector__header">
  <div>
    <strong>속성</strong>
    <small>{{ selectedLabel }}</small>
  </div>
  <div data-testid="template-inspector-actions">
    <button type="button" (click)="sampleRender()">샘플 렌더 시작</button>
    <button type="button" (click)="publish()">게시</button>
  </div>
</header>
```

- [ ] **Step 3: Run the editor and page tests**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build
```

Expected: PASS once the editor shell is split and the inspector owns the fixed actions.

- [ ] **Step 4: Commit**

```bash
git add src/features/template-builder/components/template-builder-editor.component.ts src/features/template-builder/components/template-builder-editor.component.html src/features/template-builder/components/template-builder-editor.component.scss src/features/template-builder/components/template-builder-editor.component.spec.ts src/features/template-builder/components/template-builder-workspace.component.ts src/features/template-builder/components/template-builder-workspace.component.html src/features/template-builder/components/template-builder-workspace.component.scss src/features/template-builder/components/template-builder-canvas.component.ts src/features/template-builder/components/template-builder-canvas.component.html src/features/template-builder/components/template-builder-canvas.component.scss src/features/template-builder/components/template-builder-inspector.component.ts src/features/template-builder/components/template-builder-inspector.component.html src/features/template-builder/components/template-builder-inspector.component.scss src/features/template-builder/components/template-builder-property-section.component.ts src/features/template-builder/components/template-builder-property-section.component.html src/features/template-builder/components/template-builder-property-section.component.scss
git commit -m "feat: split template builder editor shell"
```

### Task 5: Rebalance Layout Widths And Verify The Full Flow

**Files:**
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-family-gallery.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.scss`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.scss`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write the failing layout test**

Add a spec that asserts the gallery grid exists, the inspector is visibly narrower than the old shell, and the layout no longer shows the removed header/tab strip text.

```ts
it('keeps the gallery grid and inspector proportions in the redesign shell', () => {
  fixture.detectChanges();
  const inspector = fixture.nativeElement.querySelector('[data-testid="template-inspector"]') as HTMLElement;
  const gallery = fixture.nativeElement.querySelector('[data-testid="template-gallery"]') as HTMLElement;
  expect(inspector).not.toBeNull();
  expect(gallery).not.toBeNull();
  expect(inspector.getBoundingClientRect().width).toBeLessThan(gallery.getBoundingClientRect().width);
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts
```

Expected: FAIL until the final width tuning lands.

- [ ] **Step 2: Write the minimal implementation**

Tune the grid so the gallery takes roughly 280-360px on the left, the canvas stays centered, and the inspector takes about 2/3 of the right-side space rather than the current oversized panel.

```scss
.template-page__body {
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
}

.template-editor {
  grid-template-columns: minmax(0, 1.1fr) minmax(340px, 0.85fr);
}
```

- [ ] **Step 3: Run the full verification set**

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js
cd ../clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/**/*.spec.ts
npm run build
git diff --check
```

Expected: PASS across the Template Builder spec set and build.

- [ ] **Step 4: Commit**

```bash
git add src/features/template-builder/pages/template-builder-page.component.scss src/features/template-builder/components/template-builder-editor.component.scss src/features/template-builder/components/template-family-gallery.component.scss src/features/template-builder/components/template-builder-inspector.component.scss src/features/template-builder/pages/template-builder-redesign-preview.component.scss src/features/template-builder/pages/template-builder-redesign-preview.component.spec.ts src/features/template-builder/components/template-builder-editor.component.spec.ts
git commit -m "fix: rebalance template builder redesign layout"
```

## Self-Review Checklist

- Gallery cards have a thumbnail, a name, and a badge with a real data source.
- Clone lineage has a concrete field in the API and Angular model.
- The redesign is visible in a separate browser route before the real page changes.
- The real page is decomposed into focused components rather than one monolith.
- The old label/tab clutter is removed from the inspector.
- Sample render and publish actions are fixed into the inspector header.
- Each task has a concrete test command and a commit step.

## Open Questions To Resolve During Execution

- Should the mockup route stay permanently as a QA aid, or be removed after the redesign is merged?
- Should `originFamilyId` be the final lineage field name, or should we prefer `cloneSourceFamilyId` everywhere?
- Do we want to keep the inspector action bar horizontal, or stack the buttons vertically on narrow widths?
