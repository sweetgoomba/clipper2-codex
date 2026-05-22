# Template Builder Layout Inspector Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move layout layer management from the left default layer list into the right inspector, with Photoshop-order drag-and-drop stack editing and mixed image/color layout layers.

**Architecture:** Keep `variant.layers.layoutLayers[]` as the persisted/render source of truth in bottom-to-top order. The Angular inspector displays the reverse top-to-bottom order and reverses again before emitting patches. NestJS and Python continue consuming bottom-to-top order, with added solid-color layer support.

**Tech Stack:** Angular standalone components/signals, Angular CDK drag-drop, Karma/Jasmine, NestJS Node tests, Python pytest, Clipper1 local render adapter.

---

## Task 1: Angular Left Layer Row And Inspector View Model

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`

- [ ] **Step 1: Write failing Angular specs for single layout row and Photoshop-order inspector data**

Add these specs near the existing layout stack specs in `template-builder-editor.component.spec.ts`:

```ts
it('shows one layout row and exposes stack rows in Photoshop order in the inspector', () => {
  const family = familyFixture();
  const bottomLayer = {
    id: 'layout.bottom',
    label: 'Black Background',
    visible: true,
    sourceType: 'color' as const,
    backgroundColor: '#000000',
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
    assetUri: null,
  };
  const topLayer = {
    id: 'layout.top',
    label: 'Top Overlay',
    visible: true,
    sourceType: 'image' as const,
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
    assetUri: 'https://example.com/layout/top.png',
  };
  family.variants.full!.layers.layoutLayers = [bottomLayer, topLayer];
  fixture.componentRef.setInput('family', family);
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector('[data-testid="layer-row-layoutImage"]')).not.toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="layer-row-layoutLayers:layout.bottom"]')).toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="layer-row-layoutLayers:layout.top"]')).toBeNull();

  fixture.componentInstance.selectMediaLayer('layoutImage');
  fixture.detectChanges();

  const rows = Array.from(
    fixture.nativeElement.querySelectorAll('[data-testid^="layout-manager-row-"]'),
  ) as HTMLElement[];
  expect(rows.map((row) => row.getAttribute('data-testid'))).toEqual([
    'layout-manager-row-layout.top',
    'layout-manager-row-layout.bottom',
  ]);
  expect(rows[0].classList).toContain('layout-manager-row--selected');
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: FAIL because the left list currently renders one row per stack layer and the inspector has no layout manager rows.

- [ ] **Step 3: Extend the Angular inspector contract**

In `template-builder-editor.contract.ts`, add:

```ts
import type { CdkDragDrop } from '@angular/cdk/drag-drop';
```

Add the layout manager row interface:

```ts
export interface TemplateBuilderLayoutManagerRow {
  layer: TemplateBuilderLayoutLayer;
  selectionId: TemplateBuilderLayoutLayerMediaId;
  sourceType: 'image' | 'color';
  thumbnailUrl: string | null;
  color: string | null;
  summary: string;
}
```

Extend `TemplateBuilderInspectorVm`:

```ts
layoutManagerVisible: boolean;
layoutManagerRows: TemplateBuilderLayoutManagerRow[];
selectedLayoutStackLayer: TemplateBuilderLayoutLayer | null;
selectedLayoutStackSelectionId: TemplateBuilderLayoutLayerMediaId | null;
selectLayoutStackLayer: (selectionId: TemplateBuilderLayoutLayerMediaId) => void;
addImageLayoutLayer: () => void;
addColorLayoutLayer: () => void;
deleteLayoutStackLayer: (selectionId: TemplateBuilderLayoutLayerMediaId) => void;
reorderLayoutStackLayers: (event: CdkDragDrop<TemplateBuilderLayoutManagerRow[]>) => void;
updateLayoutLayerName: (event: Event) => void;
```

Keep the existing `selectedLayoutMediaLayer` and geometry methods for the selected stack layer properties.

- [ ] **Step 4: Change the left default layer rows to a single layout row**

In `TemplateBuilderEditorComponent.defaultLayerRows`, replace stack-row expansion:

```ts
const layoutRows = variant.layers.layoutLayers?.length
  ? variant.layers.layoutLayers.map((layer, index) =>
    layerMediaRow(layer, layer.label || `레이아웃 ${index + 1}`, layoutLayerSelectionId(layer.id)),
  )
  : [layerMediaRow(variant.layers.layoutImage, '레이아웃')];
```

with:

```ts
const layoutRows = [layerMediaRow(variant.layers.layoutImage, '레이아웃')];
```

In `template-builder-workspace.component.html`, update the selected-state expression for media rows so `layoutImage` stays selected when an inspector/preview stack layer is selected:

```html
(row.kind === 'media' && (
  data.canvas.selectedMediaLayerId === row.rowId ||
  (row.rowId === 'layoutImage' && data.canvas.selectedMediaLayerId?.startsWith('layoutLayers:'))
))
```

- [ ] **Step 5: Add computed inspector layout manager rows**

In `TemplateBuilderEditorComponent`, add:

```ts
readonly layoutManagerVisible = computed(() => {
  const layerId = this.selectedMediaLayerId();
  return layerId === 'layoutImage' || isLayoutLayerMediaId(layerId ?? '');
});

readonly layoutManagerRows = computed(() => {
  const variant = this.selectedVariant();
  if (!variant) return [];
  return this.layoutLayersForEditing(variant)
    .map((layer) => ({
      layer,
      selectionId: layoutLayerSelectionId(layer.id),
      sourceType: (layer.sourceType ?? 'image') as 'image' | 'color',
      thumbnailUrl: (layer.sourceType ?? 'image') === 'image' ? this.layoutLayerPreviewUrl(layer) : null,
      color: (layer.sourceType ?? 'image') === 'color' ? layer.backgroundColor || '#000000' : null,
      summary: this.layoutLayerSummary(layer),
    }))
    .reverse();
});

readonly selectedLayoutStackLayer = computed(() => {
  const rows = this.layoutManagerRows();
  if (!rows.length) return null;
  const selectedMediaLayerId = this.selectedMediaLayerId();
  const selected = isLayoutLayerMediaId(selectedMediaLayerId ?? '')
    ? rows.find((row) => row.selectionId === selectedMediaLayerId)
    : null;
  return (selected ?? rows[0]).layer;
});

readonly selectedLayoutStackSelectionId = computed(() => {
  const layer = this.selectedLayoutStackLayer();
  return layer ? layoutLayerSelectionId(layer.id) : null;
});
```

Add the helper:

```ts
private layoutLayerSummary(layer: TemplateBuilderLayoutLayer): string {
  if ((layer.sourceType ?? 'image') === 'color') {
    return `단색 | ${layer.backgroundColor || '#000000'}`;
  }
  return `이미지 | ${Math.round(layer.width)} x ${Math.round(layer.height)}`;
}
```

- [ ] **Step 6: Route selected layout media layer to the selected stack layer**

Update `selectedLayoutMediaLayer`:

```ts
readonly selectedLayoutMediaLayer = computed<TemplateBuilderMediaLayer | null>(() => {
  const layerId = this.selectedMediaLayerId();
  if (layerId === 'layoutImage' || isLayoutLayerMediaId(layerId ?? '')) {
    return this.selectedLayoutStackLayer() ?? this.selectedMediaLayer();
  }
  return null;
});
```

Update `createInspectorVm()` with the new fields:

```ts
layoutManagerVisible: this.layoutManagerVisible(),
layoutManagerRows: this.layoutManagerRows(),
selectedLayoutStackLayer: this.selectedLayoutStackLayer(),
selectedLayoutStackSelectionId: this.selectedLayoutStackSelectionId(),
selectLayoutStackLayer: (selectionId) => this.selectMediaLayer(selectionId),
addImageLayoutLayer: () => this.addLayoutLayer('image'),
addColorLayoutLayer: () => this.addLayoutLayer('color'),
deleteLayoutStackLayer: (selectionId) => this.deleteLayoutLayer(selectionId),
reorderLayoutStackLayers: (event) => this.reorderLayoutStackLayers(event),
updateLayoutLayerName: (event) => this.updateLayoutLayerName(event),
```

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: the new inspector data tests pass. Existing command-button tests may still fail until Task 2 removes old buttons.

- [ ] **Step 8: Commit Angular view-model groundwork**

```bash
cd clipper_angular
git add src/features/template-builder/components/template-builder-editor.contract.ts \
  src/features/template-builder/components/template-builder-editor.component.ts \
  src/features/template-builder/components/template-builder-editor.component.spec.ts \
  src/features/template-builder/components/template-builder-workspace.component.html
git commit -m "Move layout stack selection into inspector model"
```

## Task 2: Angular Inspector Layout Manager UI And Drag-Drop

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.spec.ts`

- [ ] **Step 1: Write failing specs for no left-side stack controls and drag-drop reorder**

In `template-builder-editor.component.spec.ts`, replace the old add/reorder/delete button expectations with:

```ts
it('reorders layout manager rows with drag and drop using Photoshop order', () => {
  const family = familyFixture();
  const bottomLayer = {
    id: 'layout.bottom',
    label: 'Bottom',
    visible: true,
    sourceType: 'color' as const,
    backgroundColor: '#000000',
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
    assetUri: null,
  };
  const topLayer = {
    id: 'layout.top',
    label: 'Top',
    visible: true,
    sourceType: 'image' as const,
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
    assetUri: 'https://example.com/top.png',
  };
  family.variants.full!.layers.layoutLayers = [bottomLayer, topLayer];
  fixture.componentRef.setInput('family', family);
  fixture.componentInstance.selectMediaLayer('layoutImage');
  fixture.detectChanges();
  const updates: Array<{ familyId: string; ratio: string; layers: DeepPartial<TemplateBuilderLayers> }> = [];
  fixture.componentInstance.variantUpdateRequest.subscribe((event) => updates.push(event));

  expect(fixture.nativeElement.querySelector('[data-testid="add-layout-layer-button"]')).toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="move-layout-layer-up-button"]')).toBeNull();
  expect(fixture.nativeElement.querySelector('[data-testid="move-layout-layer-down-button"]')).toBeNull();

  fixture.componentInstance.reorderLayoutStackLayers({
    previousIndex: 0,
    currentIndex: 1,
  } as never);

  expect(updates.at(-1)?.layers.layoutLayers).toEqual([topLayer, bottomLayer]);
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: FAIL because old workspace controls still exist and `reorderLayoutStackLayers()` does not exist.

- [ ] **Step 3: Import Angular CDK drag-drop into the inspector**

In `template-builder-inspector.component.ts`:

```ts
import { DragDropModule } from '@angular/cdk/drag-drop';
```

Update `imports`:

```ts
imports: [DragDropModule, TemplateBuilderColorFieldComponent, TemplateBuilderPropertySectionComponent],
```

- [ ] **Step 4: Remove old left-panel layout layer command buttons**

In `template-builder-workspace.component.html`, delete the `@if (data.layoutLayerControlsVisible) { ... }` block containing:

- `add-layout-layer-button`
- `move-layout-layer-up-button`
- `move-layout-layer-down-button`
- `delete-layout-layer-button`

In `template-builder-editor.contract.ts`, remove these fields from `TemplateBuilderWorkspaceVm`:

```ts
layoutLayerControlsVisible: boolean;
canMoveSelectedLayoutLayerUp: boolean;
canMoveSelectedLayoutLayerDown: boolean;
canDeleteSelectedLayoutLayer: boolean;
addLayoutLayer: () => void;
moveSelectedLayoutLayerUp: () => void;
moveSelectedLayoutLayerDown: () => void;
deleteSelectedLayoutLayer: () => void;
```

In `createWorkspaceVm()`, remove the matching assignments.

Update `template-builder-workspace.component.spec.ts` fixture objects to remove those fields.

- [ ] **Step 5: Implement inspector layout manager markup**

In `template-builder-inspector.component.html`, replace the current `@if (data.selectedLayoutMediaLayer; as layoutImage)` body with a manager-first layout:

```html
@if (data.layoutManagerVisible) {
  <fieldset class="inspector-fields" data-testid="inspector-fields" [disabled]="data.readonly">
    <app-template-builder-property-section title="레이아웃">
      <div class="layout-manager-header">
        <button data-testid="add-image-layout-layer-button" type="button" [disabled]="data.readonly" (click)="data.addImageLayoutLayer()">+ 이미지</button>
        <button data-testid="add-color-layout-layer-button" type="button" [disabled]="data.readonly" (click)="data.addColorLayoutLayer()">+ 단색</button>
      </div>

      @if (data.layoutManagerRows.length > 0) {
        <div
          class="layout-manager-list"
          cdkDropList
          [cdkDropListData]="data.layoutManagerRows"
          (cdkDropListDropped)="data.reorderLayoutStackLayers($event)"
        >
          @for (row of data.layoutManagerRows; track row.layer.id) {
            <button
              type="button"
              cdkDrag
              class="layout-manager-row"
              [class.layout-manager-row--selected]="row.selectionId === data.selectedLayoutStackSelectionId"
              [attr.data-testid]="'layout-manager-row-' + row.layer.id"
              (click)="data.selectLayoutStackLayer(row.selectionId)"
            >
              <span class="layout-manager-row__handle" cdkDragHandle aria-hidden="true">⋮⋮</span>
              @if (row.sourceType === 'color') {
                <span class="layout-manager-row__thumbnail" [style.background]="row.color || '#000000'"></span>
              } @else if (row.thumbnailUrl) {
                <img class="layout-manager-row__thumbnail" [src]="row.thumbnailUrl" alt="" />
              } @else {
                <span class="layout-manager-row__thumbnail layout-manager-row__thumbnail--empty"></span>
              }
              <span class="layout-manager-row__body">
                <strong>{{ row.layer.label }}</strong>
                <small>{{ row.summary }}</small>
              </span>
              <span
                role="button"
                tabindex="0"
                class="layout-manager-row__delete"
                [attr.data-testid]="'delete-layout-manager-row-' + row.layer.id"
                (click)="$event.stopPropagation(); data.deleteLayoutStackLayer(row.selectionId)"
                (keydown.enter)="$event.stopPropagation(); data.deleteLayoutStackLayer(row.selectionId)"
              >삭제</span>
            </button>
          }
        </div>
      } @else {
        <p class="empty-state">등록된 레이아웃 레이어가 없습니다.</p>
      }
    </app-template-builder-property-section>

    @if (data.selectedLayoutMediaLayer; as layoutImage) {
      <!-- keep the selected layer property sections here; Task 3 refines them -->
    }
  </fieldset>
}
```

- [ ] **Step 6: Add minimal inspector CSS**

In `template-builder-inspector.component.scss`, add:

```scss
.layout-manager-header {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.layout-manager-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.layout-manager-row {
  display: grid;
  grid-template-columns: 18px 36px 1fr auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 1px solid #d8dee8;
  border-radius: 6px;
  background: #fff;
  padding: 8px;
  text-align: left;
}

.layout-manager-row--selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.layout-manager-row__handle {
  color: #64748b;
  cursor: grab;
}

.layout-manager-row__thumbnail {
  width: 36px;
  height: 36px;
  border: 1px solid #d8dee8;
  border-radius: 4px;
  object-fit: cover;
}

.layout-manager-row__thumbnail--empty {
  background: repeating-linear-gradient(45deg, #f8fafc, #f8fafc 6px, #e2e8f0 6px, #e2e8f0 12px);
}

.layout-manager-row__body {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.layout-manager-row__body strong,
.layout-manager-row__body small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layout-manager-row__body small {
  color: #64748b;
}
```

- [ ] **Step 7: Implement drag-drop reorder method**

In `TemplateBuilderEditorComponent`, import:

```ts
import type { CdkDragDrop } from '@angular/cdk/drag-drop';
import { moveItemInArray } from '@angular/cdk/drag-drop';
```

Add:

```ts
reorderLayoutStackLayers(event: CdkDragDrop<unknown[]>): void {
  if (this.isReadonly()) return;
  const variant = this.selectedVariant();
  if (!variant) return;
  const topDown = this.layoutManagerRows().map((row) => row.layer);
  if (!topDown.length) return;
  moveItemInArray(topDown, event.previousIndex, event.currentIndex);
  this.emitLayoutLayersPatch([...topDown].reverse());
}
```

- [ ] **Step 8: Verify GREEN**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts
```

Expected: layout manager and workspace fixture specs pass.

- [ ] **Step 9: Commit inspector layout manager UI**

```bash
cd clipper_angular
git add src/features/template-builder/components/template-builder-inspector.component.ts \
  src/features/template-builder/components/template-builder-inspector.component.html \
  src/features/template-builder/components/template-builder-inspector.component.scss \
  src/features/template-builder/components/template-builder-workspace.component.html \
  src/features/template-builder/components/template-builder-workspace.component.spec.ts \
  src/features/template-builder/components/template-builder-editor.component.ts \
  src/features/template-builder/components/template-builder-editor.component.spec.ts \
  src/features/template-builder/components/template-builder-editor.contract.ts
git commit -m "Manage layout layers from inspector"
```

## Task 3: Angular Add/Delete/Type Editing For Image And Color Layout Layers

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write failing specs for add image, add color, delete final layer, and type change**

Add:

```ts
it('adds image and color layout layers at the visual top', () => {
  const family = familyFixture();
  family.variants.full!.layers.layoutLayers = [];
  fixture.componentRef.setInput('family', family);
  fixture.componentInstance.selectMediaLayer('layoutImage');
  fixture.detectChanges();
  const updates: Array<{ familyId: string; ratio: string; layers: DeepPartial<TemplateBuilderLayers> }> = [];
  fixture.componentInstance.variantUpdateRequest.subscribe((event) => updates.push(event));

  (fixture.nativeElement.querySelector('[data-testid="add-color-layout-layer-button"]') as HTMLButtonElement).click();
  expect((updates.at(-1)?.layers.layoutLayers as unknown as Array<Record<string, unknown>>).at(-1)).toEqual(jasmine.objectContaining({
    sourceType: 'color',
    backgroundColor: '#000000',
    assetUri: null,
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
  }));

  fixture.componentRef.setInput('family', {
    ...family,
    variants: {
      ...family.variants,
      full: {
        ...family.variants.full!,
        layers: {
          ...family.variants.full!.layers,
          layoutLayers: updates.at(-1)?.layers.layoutLayers as never,
        },
      },
    },
  });
  fixture.detectChanges();

  (fixture.nativeElement.querySelector('[data-testid="add-image-layout-layer-button"]') as HTMLButtonElement).click();
  expect((updates.at(-1)?.layers.layoutLayers as unknown as Array<Record<string, unknown>>).at(-1)).toEqual(jasmine.objectContaining({
    sourceType: 'image',
    assetUri: null,
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
  }));
});

it('deletes the last layout layer without falling back to legacy layoutImage', () => {
  const family = familyFixture();
  const onlyLayer = {
    id: 'layout.only',
    label: 'Only',
    visible: true,
    sourceType: 'color' as const,
    backgroundColor: '#000000',
    x: 0,
    y: 0,
    width: 1080,
    height: 1920,
    assetUri: null,
  };
  family.variants.full!.layers.layoutLayers = [onlyLayer];
  family.variants.full!.layers.layoutImage.assetUri = 'https://example.com/legacy.png';
  fixture.componentRef.setInput('family', family);
  fixture.componentInstance.selectMediaLayer('layoutLayers:layout.only');
  fixture.detectChanges();
  const updates: Array<{ familyId: string; ratio: string; layers: DeepPartial<TemplateBuilderLayers> }> = [];
  fixture.componentInstance.variantUpdateRequest.subscribe((event) => updates.push(event));

  (fixture.nativeElement.querySelector('[data-testid="delete-layout-manager-row-layout.only"]') as HTMLElement).click();

  expect(updates.at(-1)?.layers.layoutLayers).toEqual([]);
  expect(fixture.componentInstance.selectedMediaLayerId()).toBe('layoutImage');
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: FAIL because add color and final delete are not implemented.

- [ ] **Step 3: Replace `addLayoutLayer()` with typed add methods**

Change the method signature:

```ts
addLayoutLayer(sourceType: 'image' | 'color'): void {
  if (this.isReadonly()) return;
  const variant = this.selectedVariant();
  if (!variant) return;
  const currentLayers = this.layoutLayersForEditing(variant);
  const id = this.nextLayoutLayerId(currentLayers);
  const layer: TemplateBuilderLayoutLayer = {
    id,
    label: sourceType === 'color' ? `단색 ${currentLayers.length + 1}` : `이미지 ${currentLayers.length + 1}`,
    visible: true,
    sourceType,
    backgroundColor: sourceType === 'color' ? '#000000' : null,
    x: 0,
    y: 0,
    width: variant.outputSize.width,
    height: variant.outputSize.height,
    assetUri: null,
  };
  this.selectedCanvasId.set('line-mode-double');
  this.selectedMediaLayerId.set(layoutLayerSelectionId(id));
  this.selectedLayerId.set(null);
  this.emitLayoutLayersPatch([...currentLayers, layer]);
}
```

- [ ] **Step 4: Allow deleting the final layer**

Replace `deleteSelectedLayoutLayer()` with a selection-id based method:

```ts
deleteLayoutLayer(selectionId?: TemplateBuilderLayoutLayerMediaId): void {
  if (this.isReadonly()) return;
  const variant = this.selectedVariant();
  const layoutLayers = variant?.layers.layoutLayers;
  if (!layoutLayers) return;
  const targetSelectionId = selectionId ?? this.selectedLayoutStackSelectionId();
  if (!targetSelectionId) return;
  const targetLayerId = layoutLayerIdFromSelectionId(targetSelectionId);
  const nextLayers = layoutLayers.filter((layer) => layer.id !== targetLayerId);
  this.selectedMediaLayerId.set('layoutImage');
  this.selectedLayerId.set(null);
  this.emitLayoutLayersPatch(nextLayers);
}
```

Keep a compatibility wrapper only if existing tests still call it:

```ts
deleteSelectedLayoutLayer(): void {
  this.deleteLayoutLayer();
}
```

- [ ] **Step 5: Add layer name and type editing**

Add:

```ts
updateLayoutLayerName(event: Event): void {
  const value = stringValueFromEvent(event).trim();
  const selectionId = this.selectedLayoutStackSelectionId();
  if (!selectionId || !value) return;
  this.emitLayoutLayerPatch(selectionId, { label: value });
}

updateLayoutBackgroundSource(event: Event): void {
  const sourceType = selectValueFromEvent(event) === 'color' ? 'color' : 'image';
  const selectionId = this.selectedLayoutStackSelectionId();
  if (selectionId) {
    this.emitLayoutLayerPatch(selectionId, {
      sourceType,
      backgroundColor: sourceType === 'color' ? this.selectedLayoutStackLayer()?.backgroundColor || '#000000' : null,
      assetUri: sourceType === 'color' ? null : this.selectedLayoutStackLayer()?.assetUri ?? null,
    });
    return;
  }
  this.patchMediaLayer('layoutImage', {
    sourceType,
    backgroundColor: sourceType === 'color' ? this.selectedVariant()?.layers.layoutImage.backgroundColor || '#000000' : null,
  });
}
```

If `stringValueFromEvent()` does not exist, add:

```ts
function stringValueFromEvent(event: Event): string {
  const target = event.target as HTMLInputElement | null;
  return target?.value ?? '';
}
```

- [ ] **Step 6: Show selected layer properties in inspector**

In `template-builder-inspector.component.html`, under the manager list, add:

```html
@if (data.selectedLayoutMediaLayer; as layoutImage) {
  <app-template-builder-property-section title="선택 레이어">
    <label class="form-field">
      <span>이름</span>
      <input data-testid="layout-layer-name-input" type="text" [value]="layoutImage.label" (change)="data.updateLayoutLayerName($event)" />
    </label>
    <label class="form-field">
      <span>방식</span>
      <select data-testid="layout-background-source-select" [value]="layoutImage.sourceType ?? 'image'" (change)="data.updateLayoutBackgroundSource($event)">
        <option value="image">레이아웃 이미지</option>
        <option value="color">단색 배경</option>
      </select>
    </label>
    @if ((layoutImage.sourceType ?? 'image') === 'color') {
      <app-template-builder-color-field
        class="layout-background-color-field"
        label="배경 색상"
        testId="layout-background-color"
        [value]="layoutImage.backgroundColor || '#000000'"
        (valueChange)="data.updateLayoutBackgroundColor($event)"
      />
    } @else {
      <p class="asset-uri">{{ layoutImage.assetUri || '등록된 이미지 없음' }}</p>
      @if (!data.assetActionsReadonly) {
        <label class="asset-upload">
          <input data-testid="layout-image-input" type="file" accept="image/png,image/jpeg,image/webp" (change)="data.handleLayoutImageInput($event)" />
          <span>이미지 선택</span>
        </label>
      }
    }
  </app-template-builder-property-section>
  <app-template-builder-property-section title="위치와 크기">
    <!-- keep existing X/Y/width/height inputs -->
  </app-template-builder-property-section>
}
```

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: add/delete/type/name tests pass.

- [ ] **Step 8: Commit Angular layout manager commands**

```bash
cd clipper_angular
git add src/features/template-builder/components/template-builder-editor.component.ts \
  src/features/template-builder/components/template-builder-inspector.component.html \
  src/features/template-builder/components/template-builder-editor.component.spec.ts
git commit -m "Edit image and color layout layers in inspector"
```

## Task 4: Angular Preview Support For Color Layout Layers

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write failing preview spec for mixed color and image stack**

Add:

```ts
it('renders mixed color and image layout stack layers in preview order', () => {
  const family = familyFixture();
  family.variants.full!.layers.layoutLayers = [
    {
      id: 'layout.black',
      label: 'Black',
      visible: true,
      sourceType: 'color',
      backgroundColor: '#000000',
      x: 0,
      y: 0,
      width: 1080,
      height: 1920,
      assetUri: null,
    },
    {
      id: 'layout.cat',
      label: 'Cat',
      visible: true,
      sourceType: 'image',
      x: 100,
      y: 200,
      width: 300,
      height: 240,
      assetUri: 'https://example.com/cat.png',
    },
  ];
  fixture.componentRef.setInput('family', family);
  fixture.detectChanges();

  const colorLayer = fixture.nativeElement.querySelector('[data-testid="layout-stack-layer-layout.black"]') as HTMLElement;
  const imageLayer = fixture.nativeElement.querySelector('[data-testid="layout-stack-layer-layout.cat"]') as HTMLImageElement;

  expect(colorLayer).not.toBeNull();
  expect(colorLayer.style.background).toContain('rgb(0, 0, 0)');
  expect(imageLayer.src).toBe('https://example.com/cat.png');
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: FAIL because color layers are filtered out or rendered only as images.

- [ ] **Step 3: Extend preview item contract**

In `TemplateBuilderLayoutLayerPreviewItem`, change:

```ts
url: string;
```

to:

```ts
sourceType: 'image' | 'color';
url: string | null;
color: string | null;
```

- [ ] **Step 4: Include visible color layers in `layoutLayerPreviewItems`**

Replace the computed filter/map with:

```ts
readonly layoutLayerPreviewItems = computed(() => {
  const variant = this.selectedVariant();
  if (!variant?.layers.layoutLayers?.length) return [];
  return variant.layers.layoutLayers
    .filter((layer) => layer.visible !== false)
    .map((layer) => {
      const sourceType = (layer.sourceType ?? 'image') as 'image' | 'color';
      const url = sourceType === 'image' ? this.layoutLayerPreviewUrl(layer) : null;
      if (sourceType === 'image' && !url) return null;
      return {
        layer,
        selectionId: layoutLayerSelectionId(layer.id),
        sourceType,
        url,
        color: sourceType === 'color' ? layer.backgroundColor || '#000000' : null,
      };
    })
    .filter((item): item is TemplateBuilderLayoutLayerPreviewItem => !!item);
});
```

Update `layoutLayerStackVisible()`:

```ts
private layoutLayerStackVisible(): boolean {
  const layoutLayers = this.selectedVariant()?.layers.layoutLayers;
  return !!layoutLayers?.some((layer) =>
    layer.visible !== false && (
      (layer.sourceType ?? 'image') === 'color' ||
      !!layer.assetUri
    ),
  );
}
```

- [ ] **Step 5: Render color blocks in canvas**

In `template-builder-canvas.component.html`, replace the stack `<img>` loop body with:

```html
@for (item of data.layoutLayerPreviewItems; track item.layer.id) {
  @if (item.sourceType === 'color') {
    <div
      class="layout-stack-layer layout-stack-layer--color"
      [class.canvas-layer--interactive]="data.canInteractWithPreviewLayer(item.selectionId)"
      [class.layout-stack-layer--below-content]="variant.contentArea.height < variant.outputSize.height"
      [attr.data-testid]="'layout-stack-layer-' + item.layer.id"
      [style.background]="item.color || '#000000'"
      [style.left.px]="data.frameFor(item.layer).x * data.canvasScale"
      [style.top.px]="data.frameFor(item.layer).y * data.canvasScale"
      [style.width.px]="data.frameFor(item.layer).width * data.canvasScale"
      [style.height.px]="data.frameFor(item.layer).height * data.canvasScale"
      (pointerdown)="data.beginCanvasLayerMove(item.layer, $event)"
    ></div>
  } @else if (item.url) {
    <img
      class="layout-stack-layer"
      [class.canvas-layer--interactive]="data.canInteractWithPreviewLayer(item.selectionId)"
      [class.layout-stack-layer--below-content]="variant.contentArea.height < variant.outputSize.height"
      [attr.data-testid]="'layout-stack-layer-' + item.layer.id"
      [src]="item.url"
      alt=""
      [style.left.px]="data.frameFor(item.layer).x * data.canvasScale"
      [style.top.px]="data.frameFor(item.layer).y * data.canvasScale"
      [style.width.px]="data.frameFor(item.layer).width * data.canvasScale"
      [style.height.px]="data.frameFor(item.layer).height * data.canvasScale"
      (load)="data.handleLayoutImageLoad(item.layer, $event)"
      (pointerdown)="data.beginCanvasLayerMove(item.layer, $event)"
    />
  }
}
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
npm run build
```

Expected: preview color layer spec and build pass.

- [ ] **Step 7: Commit Angular color preview**

```bash
cd clipper_angular
git add src/features/template-builder/components/template-builder-editor.contract.ts \
  src/features/template-builder/components/template-builder-editor.component.ts \
  src/features/template-builder/components/template-builder-canvas.component.html \
  src/features/template-builder/components/template-builder-canvas.component.scss \
  src/features/template-builder/components/template-builder-editor.component.spec.ts
git commit -m "Render color layout layers in template preview"
```

## Task 5: NestJS Render Payload Color Layer Contract

**Files:**
- Modify: `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
- Modify: `clipper_nestjs/test/template-builder-render-payload.test.js`

- [ ] **Step 1: Write failing payload test for mixed image/color layout stack**

Add a Node test near the existing layout stack payload test:

```js
test('template settings include color layout layers in stack order', () => {
  const variant = structuredClone(baseTemplateBuilderVariant);
  variant.layers.layoutLayers = [
    {
      id: 'layout.black',
      label: 'Black',
      visible: true,
      sourceType: 'color',
      backgroundColor: '#000000',
      x: 0,
      y: 0,
      width: 1080,
      height: 1920,
      assetUri: null,
    },
    {
      id: 'layout.cat',
      label: 'Cat',
      visible: true,
      sourceType: 'image',
      x: 180,
      y: 520,
      width: 320,
      height: 240,
      assetUri: 'layouts/cat.png',
    },
  ];
  const payload = payloadForTemplateBuilderVariant(variant);

  assert.deepEqual(payload.template_settings.template_builder_layout_layers, [
    {
      id: 'layout.black',
      label: 'Black',
      source_type: 'color',
      background_color: '#000000',
      asset_uri: null,
      x: 0,
      y: 0,
      width: 1080,
      height: 1920,
    },
    {
      id: 'layout.cat',
      label: 'Cat',
      source_type: 'image',
      background_color: undefined,
      asset_uri: 'layouts/cat.png',
      x: 180,
      y: 520,
      width: 320,
      height: 240,
    },
  ]);
});
```

If the file has no `payloadForTemplateBuilderVariant()` helper, follow the existing layout stack test setup and only add the assertion shown above.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-render-payload.test.js
```

Expected: FAIL because color layers are filtered out by `!!layer.assetUri`.

- [ ] **Step 3: Include color layout layers in mapper filter**

Replace `layoutLayers()` with:

```ts
private layoutLayers(layers: Partial<Record<keyof TemplateBuilderLayers, unknown>>): TemplateBuilderMediaLayer[] {
  const rawLayers = this.asRecord(layers).layoutLayers;
  if (!Array.isArray(rawLayers)) return [];
  return rawLayers
    .map((layer) => this.mediaLayer(layer))
    .filter((layer): layer is TemplateBuilderMediaLayer => {
      if (!layer || !this.layerVisible(layer)) return false;
      const sourceType = layer.sourceType ?? 'image';
      if (sourceType === 'color') return typeof layer.backgroundColor === 'string' && layer.backgroundColor.trim().length > 0;
      return !!layer.assetUri;
    });
}
```

- [ ] **Step 4: Emit source metadata**

Replace `layoutLayerSettingsFor()` with:

```ts
private layoutLayerSettingsFor(layer: TemplateBuilderMediaLayer): Record<string, unknown> {
  const sourceType = layer.sourceType ?? 'image';
  return {
    id: layer.id,
    label: layer.label,
    source_type: sourceType,
    background_color: sourceType === 'color' ? layer.backgroundColor : undefined,
    asset_uri: sourceType === 'color' ? null : layer.assetUri,
    x: layer.x,
    y: layer.y,
    width: layer.width,
    height: layer.height,
  };
}
```

Update the existing image-only expected payload to include `source_type: 'image'` and `background_color: undefined`, or omit `background_color` from both implementation and expectation for image layers.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-render-payload.test.js
node --test test/template-builder-validation.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js
```

Expected: build passes and all listed Node tests pass.

- [ ] **Step 6: Commit NestJS payload contract**

```bash
cd clipper_nestjs
git add src/project-manifest/legacy-clipper1-render-payload-mapper.ts \
  test/template-builder-render-payload.test.js
git commit -m "Include color layout layers in render payload"
```

## Task 6: Python Renderer Solid Color Layout Layer Support

**Files:**
- Modify: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
- Modify: `clipper_python/tests/test_clipper1_video_render_media_looping.py`
- Modify: `clipper_python/tests/test_clipper1_video_render_remote_assets.py`

- [ ] **Step 1: Write failing Python tests for resolving and compositing color layers**

In `test_clipper1_video_render_remote_assets.py`, add:

```py
def test_render_adapter_resolves_color_layout_layers_without_asset_uri(tmp_path: Path) -> None:
    visual_assets = LocalRenderAdapter()._visual_assets(
        {
            "template_settings": {
                "template_builder_layout_layers": [
                    {
                        "id": "layout.black",
                        "label": "Black",
                        "source_type": "color",
                        "background_color": "#000000",
                        "asset_uri": None,
                        "x": 0,
                        "y": 0,
                        "width": 1080,
                        "height": 1920,
                    },
                ],
            },
        },
        tmp_path,
        RemoteAssetStager(tmp_path / "remote-assets"),
    )

    assert visual_assets["layout_layers"] == [
        {
            "id": "layout.black",
            "label": "Black",
            "source_type": "color",
            "background_color": "#000000",
            "path": None,
            "x": 0,
            "y": 0,
            "width": 1080,
            "height": 1920,
        }
    ]
```

In `test_clipper1_video_render_media_looping.py`, add:

```py
def test_render_segment_composites_color_layout_layer_below_content_media(tmp_path: Path) -> None:
    adapter = RecordingRenderAdapter()
    media_path = tmp_path / "still.png"
    media_path.write_bytes(b"fake-image")

    adapter._render_segment(
        media_path=media_path,
        segment_path=tmp_path / "segment.mp4",
        overlay_path=None,
        duration=3.0,
        width=1080,
        height=1920,
        fps=30,
        content_area={"x": 0, "y": 596, "width": 1080, "height": 608},
        visual_assets={
            "layout_image": None,
            "layout_layers": [
                {
                    "id": "layout.black",
                    "source_type": "color",
                    "background_color": "#000000",
                    "path": None,
                    "x": 0,
                    "y": 0,
                    "width": 1080,
                    "height": 1920,
                },
            ],
            "logo_image": None,
        },
        settings={},
        motion_effect=None,
    )

    filter_complex = _filter_complex(adapter.commands[0])

    assert "color=c=0x000000:s=1080x1920[layoutlayer0]" in filter_complex
    assert "[layoutstackbase][layoutlayer0]overlay=0:0[v0]" in filter_complex
    assert "[v0][media]overlay=0:596[base]" in filter_complex
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_remote_assets.py::test_render_adapter_resolves_color_layout_layers_without_asset_uri \
  tests/test_clipper1_video_render_media_looping.py::test_render_segment_composites_color_layout_layer_below_content_media -q
```

Expected: FAIL because color layers without `asset_uri` are skipped.

- [ ] **Step 3: Resolve color layout layers**

In `_template_builder_layout_layers()`, determine source type before resolving asset:

```py
source_type = self._non_empty_string(layer.get("source_type")) or self._non_empty_string(layer.get("sourceType")) or "image"
background_color = self._non_empty_string(layer.get("background_color")) or self._non_empty_string(layer.get("backgroundColor"))
if source_type == "color":
    if not background_color:
        continue
    resolved_layers.append({
        "id": layer_id,
        "label": self._non_empty_string(layer.get("label")) or layer_id,
        "source_type": "color",
        "background_color": background_color,
        "path": None,
        "x": layer.get("x"),
        "y": layer.get("y"),
        "width": layer.get("width"),
        "height": layer.get("height"),
    })
    continue
```

Keep the existing image path resolution for image layers and include:

```py
"source_type": "image",
"background_color": None,
```

- [ ] **Step 4: Normalize color layers**

Update `_normalized_layout_layers()` so `path` is only required for image layers:

```py
source_type = self._non_empty_string(layer.get("source_type")) or "image"
path = layer.get("path")
if source_type == "image" and not isinstance(path, Path):
    continue
if source_type == "color":
    background_color = self._non_empty_string(layer.get("background_color"))
    if not background_color:
        continue
else:
    background_color = None
```

Append:

```py
normalized.append({
    **layer,
    "id": layer_id,
    "label": self._non_empty_string(layer.get("label")) or layer_id,
    "source_type": source_type,
    "background_color": background_color,
    "path": path if isinstance(path, Path) else None,
    **geometry,
})
```

- [ ] **Step 5: Composite color layers**

In `_append_layout_layer_stack_steps()`, before image input-index handling, add:

```py
if layer.get("source_type") == "color":
    color = self._ffmpeg_color_value(layer.get("background_color") or "#000000")
    layer_label = f"layoutlayer{layer_index}"
    steps.append(f"color=c={color}:s={layer['width']}x{layer['height']}[{layer_label}]")
    steps.append(f"[{previous}][{layer_label}]overlay={layer['x']}:{layer['y']}[v{overlay_index}]")
    previous = f"v{overlay_index}"
    overlay_index += 1
    continue
```

If `_ffmpeg_color_value()` does not exist, add:

```py
def _ffmpeg_color_value(self, value: Any) -> str:
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        return "0x" + text[1:]
    return "black"
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py -q
uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py
```

Expected: pytest and compileall pass.

- [ ] **Step 7: Commit Python color layout renderer support**

```bash
cd clipper_python
git add plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py \
  tests/test_clipper1_video_render_media_looping.py \
  tests/test_clipper1_video_render_remote_assets.py
git commit -m "Render color template layout layers"
```

## Task 7: Final Verification And Docs

**Files:**
- Modify: `.codex/implementation/NEXT_SESSION_PROMPT.md`
- Modify: `.codex/session-logs/2026-05-12.log`

- [ ] **Step 1: Run Angular focused tests and build**

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/services/template-builder.service.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts
npm run build
git diff --check
```

Expected:

- Karma reports all included specs `SUCCESS`.
- Angular build exits 0.
- `git diff --check` exits 0.

- [ ] **Step 2: Run NestJS focused tests and build**

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-validation.test.js test/template-builder-api.test.js test/template-builder-render-payload.test.js
git diff --check
```

Expected:

- Build exits 0.
- Node tests pass.
- `git diff --check` exits 0.

- [ ] **Step 3: Run Python focused tests**

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_media_looping.py -q
uv run python -m compileall plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py
git diff --check
```

Expected:

- Pytest reports all selected tests passed.
- Compileall exits 0.
- `git diff --check` exits 0.

- [ ] **Step 4: Update docs and session logs**

Update `.codex/implementation/NEXT_SESSION_PROMPT.md` with:

- Angular commits and current behavior.
- NestJS commit and payload contract.
- Python commit and renderer behavior.
- Verification command results.
- Manual follow-up: packaged Electron Template Builder layout inspector DnD, mixed color/image stacks, full and non-full preview/render parity.

Update `.codex/session-logs/2026-05-12.log` with the same implementation summary.

- [ ] **Step 5: Final clean status check**

```bash
cd clipper_angular && git status --short
cd ../clipper_nestjs && git status --short
cd ../clipper_python && git status --short
```

Expected:

- Each repo is clean after commits.
- `.codex` docs remain outside git and may be modified.

