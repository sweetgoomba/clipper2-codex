# Template Builder Role-Scoped Common Styles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add family-level, role-scoped common text styles to Template Builder so editing one role's style or effect applies across all ratios while ratio-specific geometry stays variant-local.

**Architecture:** Store canonical role styles on `TemplateBuilderFamily`, but mirror each common-style edit into the matching layer fields of every ratio variant so the existing canvas and render pipeline keep working unchanged. The right inspector becomes the place where users see `비율 공통 스타일` for a selected role, while the left panel remains focused on `공통 레이어` for layout only and `기본 레이어` for role-based text/media layers.

**Tech Stack:** NestJS DTO/service/controller tests, Angular 19 standalone components, existing Template Builder preview/render flow, JSON-backed repository, Karma/TestBed.

---

### Task 1: Add Family-Level Role Common Styles To The NestJS API

**Files:**
- Create: `clipper_nestjs/src/template-builder/template-builder-role-common-styles.ts`
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Modify: `clipper_nestjs/test/template-builder-api.test.js`

- [ ] **Step 1: Write the failing API test for role-scoped common styles**

Add a NestJS API test that proves:

- `GET /template-builder/families/:familyId` returns `commonStyles`
- `PATCH /template-builder/families/:familyId/common-styles/mainTitle` updates the canonical family style
- the same patch is mirrored into the matching variant layers
- `POST /template-builder/families/:familyId/clone` copies the role common styles into the clone

Use a concrete request payload so the failure is obvious before the new endpoint exists.

```js
it('updates role-scoped common styles and mirrors them into every ratio', async () => {
  const created = await service.createFamily({ name: '공통 스타일 테스트', ratio: '16:9' });

  const updated = await request(app.getHttpServer())
    .patch(`/template-builder/families/${created.id}/common-styles/mainTitle`)
    .send({
      text: {
        fontFamily: 'Pretendard',
        fontName: 'Pretendard',
        fontSize: 72,
        color: '#ff00ff',
        tracking: 0,
        lineHeight: 1.1,
      },
      box: {
        enabled: true,
        color: '#111111',
        alpha: 0.4,
        paddingX: 16,
        height: 72,
        borderColor: '#111111',
        borderWidth: 2,
      },
    })
    .expect(200);

  assert.equal(updated.body.commonStyles.mainTitle.text.fontFamily, 'Pretendard');
  assert.equal(updated.body.variants['16:9'].layers.mainTitleLine1.text.fontFamily, 'Pretendard');
  assert.equal(updated.body.variants['16:9'].layers.mainTitleLine2.text.fontFamily, 'Pretendard');
});
```

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js --test-name-pattern "role-scoped common styles"
```

Expected: FAIL before the new DTO field, controller route, and service method exist.

- [ ] **Step 2: Add the new common-style model and the service/controller plumbing**

Add a new backend helper for the role map and default style seeding.

```ts
export const TEMPLATE_BUILDER_COMMON_STYLE_ROLES = [
  'mainTitle',
  'subTitle',
  'bottomTitle',
  'subtitleText',
  'logoText',
] as const;

export type TemplateBuilderCommonStyleRole = typeof TEMPLATE_BUILDER_COMMON_STYLE_ROLES[number];

export interface TemplateBuilderRoleCommonStyle {
  text: TemplateBuilderTextStyle;
  box: TemplateBuilderBoxStyle;
  outline: TemplateBuilderOutlineStyle;
  shadow: TemplateBuilderShadowStyle;
}

export interface TemplateBuilderRoleCommonStyles {
  mainTitle: TemplateBuilderRoleCommonStyle;
  subTitle: TemplateBuilderRoleCommonStyle;
  bottomTitle: TemplateBuilderRoleCommonStyle;
  subtitleText: TemplateBuilderRoleCommonStyle;
  logoText: TemplateBuilderRoleCommonStyle;
}

export interface UpdateTemplateBuilderRoleCommonStyleRequest {
  text?: Partial<TemplateBuilderTextStyle>;
  box?: Partial<TemplateBuilderBoxStyle>;
  outline?: Partial<TemplateBuilderOutlineStyle>;
  shadow?: Partial<TemplateBuilderShadowStyle>;
}
```

Extend `TemplateBuilderFamily` with the new family-level store:

```ts
export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: TemplateBuilderOwnerType;
  source: TemplateBuilderSource;
  originFamilyId?: string | null;
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  commonStyles: TemplateBuilderRoleCommonStyles;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}
```

Add a helper that seeds `commonStyles` from a representative variant and another helper that mirrors a role patch into every affected variant layer. Use the existing variant layers as the materialized render source so the preview and sample render paths do not need a separate resolver.

```ts
export function createDefaultRoleCommonStylesFromVariant(
  variant: TemplateBuilderVariant,
): TemplateBuilderRoleCommonStyles {
  return {
    mainTitle: copyTextLayerStyle(variant.layers.mainTitleLine1),
    subTitle: copyTextLayerStyle(variant.layers.subTitle),
    bottomTitle: copyTextLayerStyle(variant.layers.bottomTitle),
    subtitleText: copyTextLayerStyle(variant.layers.subtitleText),
    logoText: copyTextLayerStyle(variant.layers.logoText),
  };
}
```

Add the new controller route:

```ts
@Patch('families/:familyId/common-styles/:role')
updateRoleCommonStyle(
  @Param('familyId') familyId: string,
  @Param('role') role: TemplateBuilderCommonStyleRole,
  @Body() request: UpdateTemplateBuilderRoleCommonStyleRequest,
) {
  return this.service.updateRoleCommonStyle(familyId, role, request);
}
```

Update `createFamily()`, `cloneFamily()`, and `systemFamiliesFromPresets()` so every returned family has populated `commonStyles`.

- [ ] **Step 3: Run the focused NestJS tests**

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js
```

Expected: PASS once the new endpoint, mirrored variant updates, and family-level style fields exist.

- [ ] **Step 4: Commit the backend model/API work**

```bash
git add src/template-builder/template-builder-role-common-styles.ts src/template-builder/dto/template-builder.dto.ts src/template-builder/template-builder.service.ts src/template-builder/template-builder.controller.ts src/template-builder/template-builder-seed.ts test/template-builder-api.test.js
git commit -m "feat: add role-scoped template builder common styles"
```

### Task 2: Mirror The New Common-Style Model In Angular

**Files:**
- Create: `clipper_angular/src/features/template-builder/services/template-builder-role-common-styles.ts`
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/services/template-builder.service.spec.ts`

- [ ] **Step 1: Write the failing Angular service test**

Add a spec that proves the client knows how to send the new patch to the backend and accepts the new `commonStyles` field on family payloads.

```ts
it('patches role-scoped common styles through the new endpoint', async () => {
  const updated = await firstValueFrom(
    service.updateRoleCommonStyle('family-1', 'mainTitle', {
      text: {
        fontFamily: 'Pretendard',
        fontName: 'Pretendard',
        fontSize: 72,
        color: '#ff00ff',
        tracking: 0,
        lineHeight: 1.1,
      },
    }),
  );

  expect(httpMock.expectOne(
    '/api/template-builder/families/family-1/common-styles/mainTitle',
  ).request.method).toBe('PATCH');
  expect(updated.commonStyles.mainTitle.text.fontFamily).toBe('Pretendard');
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts
```

Expected: FAIL before the new client method and model field exist.

- [ ] **Step 2: Add the frontend role mapping and API client method**

Define the same role key map on the Angular side so the editor can resolve a selected layer into a common-style role without hard-coding the mapping in the template.

```ts
export const TEMPLATE_BUILDER_COMMON_STYLE_ROLES = [
  'mainTitle',
  'subTitle',
  'bottomTitle',
  'subtitleText',
  'logoText',
] as const;

export type TemplateBuilderCommonStyleRole = typeof TEMPLATE_BUILDER_COMMON_STYLE_ROLES[number];

export function roleForTextLayerId(layerId: TemplateBuilderTextLayerKey): TemplateBuilderCommonStyleRole | null {
  switch (layerId) {
    case 'mainTitleLine1':
    case 'mainTitleLine2':
      return 'mainTitle';
    case 'subTitle':
      return 'subTitle';
    case 'bottomTitle':
      return 'bottomTitle';
    case 'subtitleText':
      return 'subtitleText';
    case 'logoText':
      return 'logoText';
    default:
      return null;
  }
}
```

Add the new family-level common-style shape to the Angular model and expose a typed HTTP client method:

```ts
export interface TemplateBuilderRoleCommonStyle {
  text: TemplateBuilderTextStyle;
  box: TemplateBuilderBoxStyle;
  outline: TemplateBuilderOutlineStyle;
  shadow: TemplateBuilderShadowStyle;
}

export interface TemplateBuilderRoleCommonStyles {
  mainTitle: TemplateBuilderRoleCommonStyle;
  subTitle: TemplateBuilderRoleCommonStyle;
  bottomTitle: TemplateBuilderRoleCommonStyle;
  subtitleText: TemplateBuilderRoleCommonStyle;
  logoText: TemplateBuilderRoleCommonStyle;
}

export interface TemplateBuilderFamily {
  id: string;
  name: string;
  ownerType: 'system' | 'user';
  source: 'built_in' | 'custom';
  originFamilyId?: string | null;
  readonly: boolean;
  createdAt: string;
  updatedAt: string;
  commonStyles: TemplateBuilderRoleCommonStyles;
  variants: Partial<Record<TemplateBuilderRatio, TemplateBuilderVariant>>;
}
```

```ts
updateRoleCommonStyle(
  familyId: string,
  role: TemplateBuilderCommonStyleRole,
  request: UpdateTemplateBuilderRoleCommonStyleRequest,
) {
  return this.http.patch<TemplateBuilderFamily>(
    `${this.baseUrl}/families/${familyId}/common-styles/${role}`,
    request,
  );
}
```

Add the role/common-style labels to the editor contract so the inspector can show exactly which role it is editing.

```ts
export interface TemplateBuilderInspectorVm {
  selectedMediaLayerId: TemplateBuilderMediaLayerKey | null;
  selectedTextLayer: TemplateBuilderTextLayer | null;
  selectedCommonStyleRole: TemplateBuilderCommonStyleRole | null;
  selectedCommonStyleLabel: string | null;
  selectedVariant: TemplateBuilderVariant | null;
  selectedLogoMode: 'text' | 'image';
  paletteColors: readonly string[];
  readonly: boolean;
  textEffectModeFor: (layer: TemplateBuilderTextLayer) => TemplateBuilderTextEffectMode;
  sampleRenderTitle: string;
  sampleRenderDescription: string;
  sampleRenderFileUrl: string | null;
  requestSampleRender: () => void;
  requestPublish: () => void;
  updateLayoutBackgroundSource: (event: Event) => void;
  updateLayoutBackgroundColor: (event: Event) => void;
  handleLayoutImageInput: (event: Event) => void;
  updateMediaLayerVisible: (layerId: TemplateBuilderMediaLayerKey, event: Event) => void;
  updateLayoutImageNumber: (field: NumberMediaLayerField, event: Event) => void;
  handleLogoImageInput: (event: Event) => void;
  updateLogoImageNumber: (field: NumberMediaLayerField, event: Event) => void;
  updateLogoMode: (eventOrMode: Event | 'text' | 'image') => void;
  updateLayerVisible: (event: Event) => void;
  updateLayerNumber: (field: NumberLayerField, event: Event) => void;
  updateMainTitleLineMode: (event: Event) => void;
  updateSubtitleLineMode: (event: Event) => void;
  updateTitleY: (field: SubtitleYField, event: Event) => void;
  updateSubtitleY: (field: SubtitleYField, event: Event) => void;
  updateLayerAlign: (align: TextAlignValue) => void;
  updateTextNumber: (field: NumberTextField, event: Event) => void;
  updateTextColor: (eventOrColor: Event | string) => void;
  updateTextEffectMode: (event: Event) => void;
  updateBoxEnabled: (event: Event) => void;
  updateBoxNumber: (field: NumberBoxField, event: Event) => void;
  updateBoxColor: (field: 'color' | 'borderColor', event: Event) => void;
  updateOutlineEnabled: (event: Event) => void;
  updateOutlineNumber: (field: NumberOutlineField, event: Event) => void;
  updateOutlineColor: (event: Event) => void;
  updateShadowEnabled: (event: Event) => void;
  updateShadowNumber: (field: NumberShadowField, event: Event) => void;
  updateShadowColor: (field: 'color' | 'outlineColor', event: Event) => void;
  handleFontInput: (event: Event) => void;
}
```

- [ ] **Step 3: Run the focused Angular service test**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts
```

Expected: PASS once the new client method and family model field exist.

- [ ] **Step 4: Commit the Angular model/client work**

```bash
git add src/features/template-builder/services/template-builder-role-common-styles.ts src/features/template-builder/models/template-builder.ts src/features/template-builder/services/template-builder.service.ts src/features/template-builder/components/template-builder-editor.contract.ts src/features/template-builder/services/template-builder.service.spec.ts
git commit -m "feat: mirror template builder common styles in angular"
```

### Task 3: Update The Inspector To Edit Role-Scoped Common Styles

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.scss`
- Create: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write the failing inspector spec**

Add a spec that proves the inspector:

- shows `비율 공통 스타일` for `mainTitleLine1`, `mainTitleLine2`, `subTitle`, `bottomTitle`, `subtitleText`, and `logoText`
- hides that section for `layoutImage` and `logoImage`
- keeps the existing `위치와 크기` section for geometry edits

Use a stable test id for the new section so the assertion is unambiguous.

Define a full `baseVm` fixture in the spec setup so the test does not depend on undeclared helpers.

```ts
it('shows the ratio-common style section only for role-scoped text layers', () => {
  const vm = Object.assign({}, baseVm, {
    selectedTextLayer: {
      id: 'mainTitleLine1',
      label: '메인 타이틀 1',
      visible: true,
      x: 86,
      y: 280,
      width: 908,
      height: 64,
      lineMode: 'single',
      oneLineY: 280,
      twoLineFirstY: 280,
      twoLineSecondY: 340,
      leftMargin: 86,
      rightMargin: 86,
      align: 'center',
      text: {
        fontFamily: 'Pretendard',
        fontName: 'Pretendard',
        fontSize: 72,
        color: '#ff00ff',
        tracking: 0,
        lineHeight: 1.1,
      },
      box: {
        enabled: false,
        color: '#000000',
        alpha: 0,
        paddingX: 0,
        height: 0,
        borderColor: '#000000',
        borderWidth: 0,
      },
      outline: { enabled: false, width: 0, color: '#000000' },
      shadow: {
        enabled: false,
        color: '#000000',
        outlineWidth: 0,
        outlineColor: '#000000',
        offsetX: 0,
        offsetY: 0,
      },
    },
    selectedCommonStyleRole: 'mainTitle',
    selectedCommonStyleLabel: '메인 타이틀',
  });
  fixture.componentRef.setInput('vm', vm);
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector('[data-testid="common-style-section"]')).not.toBeNull();
  expect(fixture.nativeElement.textContent).toContain('비율 공통 스타일');
  expect(fixture.nativeElement.textContent).toContain('선택한 역할의 모든 비율에 적용됩니다.');
});
```

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-inspector.component.spec.ts
```

Expected: FAIL before the inspector template knows about the new section.

- [ ] **Step 2: Move the inspector UI onto the new role-scoped common-style contract**

Keep the existing geometry section as-is, but change the text-style and text-effect controls so they sit under a single `비율 공통 스타일` block when the selected layer maps to a common-style role.

```html
@if (vm(); as data) {
  <aside class="template-inspector">
    <section class="publish-gate publish-gate--top">
      <strong>{{ data.sampleRenderTitle }}</strong>
      <span>{{ data.sampleRenderDescription }}</span>
      <div class="publish-gate__actions">
        <button type="button" [disabled]="data.readonly" (click)="data.requestSampleRender()">샘플 렌더 시작</button>
        <button type="button" [disabled]="data.readonly || data.selectedVariant?.sampleRender?.status !== 'succeeded'" (click)="data.requestPublish()">게시</button>
      </div>
    </section>

    @if (data.selectedCommonStyleRole) {
      <app-template-builder-property-section class="common-style-section" title="비율 공통 스타일" tone="emphasis">
        <p class="common-style-help">선택한 역할의 모든 비율에 적용됩니다.</p>
        <app-template-builder-property-section title="텍스트 스타일"></app-template-builder-property-section>
        <app-template-builder-property-section title="텍스트 효과"></app-template-builder-property-section>
      </app-template-builder-property-section>
    }
  </aside>
}
```

Update `TemplateBuilderEditorComponent` so it resolves `selectedCommonStyleRole` and `selectedCommonStyleLabel` from the selected text layer using the new role-mapping helper.

Route the existing `updateText*`, `updateBox*`, `updateOutline*`, and `updateShadow*` handlers through `updateRoleCommonStyle()` when a role-scoped text layer is selected. Keep geometry handlers (`updateLayerNumber`, `updateTitleY`, `updateSubtitleY`, `updateLayerAlign`) editing the selected variant only.

- [ ] **Step 3: Run the focused inspector/editor tests**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-inspector.component.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: PASS once the inspector renders the new section and the editor routes common-style edits through the new family-level API.

- [ ] **Step 4: Commit the inspector UI work**

```bash
git add src/features/template-builder/components/template-builder-editor.component.ts src/features/template-builder/components/template-builder-editor.component.html src/features/template-builder/components/template-builder-inspector.component.ts src/features/template-builder/components/template-builder-inspector.component.html src/features/template-builder/components/template-builder-inspector.component.scss src/features/template-builder/components/template-builder-inspector.component.spec.ts src/features/template-builder/components/template-builder-editor.component.spec.ts
git commit -m "feat: add ratio-common style inspector for template builder"
```

### Task 4: Backfill Legacy Families And Verify End-To-End Behavior

**Files:**
- Create: `clipper_nestjs/test/fixtures/template-builder-store.v1.json`
- Modify: `clipper_nestjs/src/template-builder/template-builder.repository.ts`
- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Write the failing repository migration test**

Add a fixture that mimics the old store shape with no `commonStyles`, then assert the repository normalizes it on load.

```json
{
  "version": 1,
  "families": [
    {
      "id": "custom.template.legacy",
      "name": "Legacy Custom",
      "ownerType": "user",
      "source": "custom",
      "readonly": false,
      "createdAt": "2026-05-10T00:00:00.000Z",
      "updatedAt": "2026-05-10T00:00:00.000Z",
      "variants": {
        "16:9": {
          "id": "custom.template.legacy.16x9",
          "familyId": "custom.template.legacy",
          "ratio": "16:9",
          "status": "draft",
          "outputSize": { "width": 1080, "height": 1920 },
          "contentArea": { "x": 0, "y": 656, "width": 1080, "height": 608 },
          "layers": {
            "layoutImage": { "id": "layoutImage", "label": "레이아웃", "visible": true, "x": 0, "y": 0, "width": 1080, "height": 608, "assetUri": null },
            "contentArea": { "id": "contentArea", "label": "콘텐츠", "visible": true, "x": 0, "y": 656, "width": 1080, "height": 608, "assetUri": null },
            "subTitle": {
              "id": "subTitle",
              "label": "서브 타이틀",
              "visible": true,
              "x": 86,
              "y": 1120,
              "width": 908,
              "height": 64,
              "align": "center",
              "text": { "fontFamily": "Pretendard", "fontSize": 64, "color": "#ffffff", "tracking": 0, "lineHeight": 1.2 },
              "box": { "enabled": false, "color": "#000000", "alpha": 0, "paddingX": 0, "height": 0, "borderColor": "#000000", "borderWidth": 0 },
              "outline": { "enabled": false, "width": 0, "color": "#000000" },
              "shadow": { "enabled": false, "color": "#000000", "outlineWidth": 0, "outlineColor": "#000000", "offsetX": 0, "offsetY": 0 }
            }
          },
          "validation": { "valid": true, "issues": [] },
          "sampleRender": { "status": "missing" },
          "updatedAt": "2026-05-10T00:00:00.000Z"
        }
      }
    }
  ]
}
```

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js --test-name-pattern "normalize legacy template-builder store"
```

Expected: FAIL before the repository backfill exists.

- [ ] **Step 2: Add repository normalization and version bump**

Teach `JsonTemplateBuilderRepository` to upgrade version 1 files to version 2 by filling any missing `commonStyles` from the first available variant and then flushing version 2 back to disk on the next write.

```ts
interface TemplateBuilderStoreFileV2 {
  version: 2;
  families: TemplateBuilderFamily[];
}
```

The normalization should:

- keep the current family/variant data intact
- seed `commonStyles` from the first available variant when it is missing
- preserve `originFamilyId`
- keep system families and custom families on the same normalized shape after load

Use the same helper that seeds `commonStyles` for the system preset path so the legacy-store backfill and the runtime family creation path stay in sync.

- [ ] **Step 3: Run the full verification sweep**

Run:

```bash
cd clipper_nestjs
node --test test/template-builder-api.test.js
cd ../clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-inspector.component.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts --include=src/features/template-builder/services/template-builder.service.spec.ts --include=src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build
git diff --check
```

Expected: PASS after the repository backfill lands and the Angular inspector/client wiring is in place.

- [ ] **Step 4: Commit the migration and verification work**

```bash
git add test/fixtures/template-builder-store.v1.json src/template-builder/template-builder.repository.ts test/template-builder-api.test.js src/features/template-builder/pages/template-builder-page.component.spec.ts
git commit -m "feat: backfill template builder common styles"
```

### Self-Review

1. **Spec coverage**
- [x] Family-level common styles are added to the NestJS data model.
- [x] Editing a role-scoped style is exposed through a dedicated API route.
- [x] The new family-level styles are mirrored into variant layers so preview/render behavior stays stable.
- [x] Angular receives the new model and API client method.
- [x] The inspector shows a dedicated `비율 공통 스타일` block for role-scoped text layers only.
- [x] Legacy store files are normalized so old families do not break when the new field appears.

2. **Placeholder scan**
- [x] No `TBD`, `TODO`, `implement later`, or similar placeholders are used.
- [x] Every step has a concrete file list, test command, and expected result.
- [x] Every code step includes the actual interface, route, or template shape needed to implement it.

3. **Type consistency**
- [x] `TemplateBuilderCommonStyleRole` is the same concept in NestJS and Angular.
- [x] `mainTitleLine1` and `mainTitleLine2` both map to `mainTitle`.
- [x] `subtitleBox` stays a helper layer, not a user-facing role key.
- [x] The new `commonStyles` field is present on `TemplateBuilderFamily` in both repos.
