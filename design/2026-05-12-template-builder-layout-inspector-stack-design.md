# Template Builder Layout Inspector Stack Design

작성일: 2026-05-12

## 목표

Template Builder의 레이아웃 편집을 왼쪽 기본 레이어 목록이 아니라 오른쪽 inspector에서 관리한다. 왼쪽 `기본 레이어`에는 `레이아웃` row 하나만 표시하고, 이 row를 선택하면 inspector에 Photoshop식 layout layer stack을 보여준다.

## 사용자 기준

- 레이아웃 레이어 목록은 Photoshop처럼 동작한다.
  - inspector 목록 맨 위 row가 preview/render에서도 가장 위에 덮이는 레이어다.
  - 순서 변경은 `위/아래` 버튼이 아니라 drag-and-drop으로 한다.
- layout layer는 이미지와 단색 배경을 모두 지원한다.
  - 이미지 layout과 단색 layout을 같은 stack 안에서 함께 사용할 수 있다.
  - 예: 검은 단색 full-frame layer 위에 고양이 PNG image layer를 올릴 수 있다.
- 단색 layer도 image layer와 같은 레이어다.
  - `x/y/width/height`를 가진다.
  - 새로 추가할 때 기본값만 output frame 전체 크기다.
  - 이후 preview drag/resize와 inspector 숫자 입력으로 위치와 크기를 바꿀 수 있다.

## UI 구조

### 왼쪽 기본 레이어

왼쪽 `기본 레이어`에는 layout stack의 개별 layer를 나열하지 않는다.

표시 순서:

1. `레이아웃`
2. `서브 타이틀`
3. `타이틀`
4. `하단 타이틀`
5. `자막`
6. `로고`

`레이아웃` row를 클릭하면 inspector가 layout manager 모드로 열린다. preview canvas에서 특정 layout stack layer를 직접 클릭하면 inspector는 같은 layout manager를 유지하되 해당 layer row를 선택한다.

### Inspector Layout Manager

Inspector의 `레이아웃` section은 다음 구조를 가진다.

- Header:
  - title: `레이아웃`
  - action buttons: `+ 이미지`, `+ 단색`
- Layer stack list:
  - Photoshop order: top row is topmost visual layer.
  - row content:
    - drag handle
    - thumbnail
      - image layer: image thumbnail when available, placeholder otherwise
      - color layer: color swatch
    - layer name
    - type summary: `이미지`, `단색`, dimensions or color
    - delete button
  - selected row shows active styling.
  - drag-and-drop reorder updates preview order immediately.
- Selected layer properties:
  - 이름
  - 방식: `레이아웃 이미지` / `단색 배경`
  - for image:
    - asset URI summary
    - image upload
    - `맞춤` / `채우기`
  - for color:
    - color picker
  - common geometry:
    - X
    - Y
    - 너비
    - 높이

## Data Order

Existing `variant.layers.layoutLayers[]` remains the render source of truth and stores layers in render order: bottom to top.

The inspector displays the reverse order:

- persisted array: `[bottom, middle, top]`
- inspector list: `[top, middle, bottom]`

When the user drags rows in the inspector:

1. Reorder the displayed top-to-bottom list.
2. Reverse it before emitting `layers.layoutLayers` patch.
3. Preview/render continue consuming `layoutLayers[]` in bottom-to-top order.

This avoids changing the existing NestJS/Python render contract that already composites stack layers in array order.

## Layer Types

### Image Layout Layer

Fields:

- `sourceType: 'image'`
- `assetUri`
- `assetWidth` / `assetHeight` when known
- `x`, `y`, `width`, `height`

Preview:

- Rendered as image.
- Uses the same file URL path currently used by layout stack layers.
- Can be selected, moved, resized, fit, and cover-fit.

Render:

- NestJS emits `asset_uri`, geometry, and type metadata.
- Python renderer loads the image and composites it in stack order.

### Solid Color Layout Layer

Fields:

- `sourceType: 'color'`
- `backgroundColor`
- `x`, `y`, `width`, `height`
- `assetUri: null`

Preview:

- Rendered as an absolutely-positioned color block.
- Can be selected, moved, resized, and edited like an image layer.

Render:

- NestJS emits `source_type: 'color'`, `background_color`, and geometry.
- Python renderer creates a color source of the layer geometry and composites it in stack order.

## Add, Delete, Empty Stack

### Add Image

Adds a new image layout layer at the top of the visual stack.

Persisted patch appends the layer to `layoutLayers[]`, because persisted order is bottom-to-top.

Default geometry:

- `x = 0`
- `y = 0`
- `width = outputSize.width`
- `height = outputSize.height`
- `assetUri = null`

### Add Solid Color

Adds a new color layout layer at the top of the visual stack.

Default geometry:

- `x = 0`
- `y = 0`
- `width = outputSize.width`
- `height = outputSize.height`
- `sourceType = 'color'`
- `backgroundColor = '#000000'`
- `assetUri = null`

### Delete

Deletes the selected layout layer. Deleting the final layer is allowed.

When the stack becomes empty:

- persist `layoutLayers: []`
- do not fall back to legacy `layoutImage`
- show an inspector empty state with `+ 이미지` and `+ 단색`
- preview shows no layout stack, only content/background/text layers

## Legacy Bridge

Existing data may have only `layers.layoutImage` and no `layers.layoutLayers`.

When opening the layout inspector or adding a new layer:

- If `layoutLayers` is `undefined`, create an editing stack from legacy `layoutImage`.
- The bridge preserves:
  - `sourceType`
  - `backgroundColor`
  - `assetUri`
  - geometry
  - `assetWidth` / `assetHeight`
- After the first stack edit, emit `layoutLayers[]` and use it as source of truth.

The left row still says `레이아웃`; it does not expose the bridge layer as a separate left-panel row.

## Preview Semantics

Full ratio:

- Layout stack is rendered above content media and below logo/text.
- This preserves full-ratio `gradient.png` behavior.

Non-full ratios:

- Layout stack is rendered below the content area/media.
- The content area placeholder remains visible in preview.
- This matches legacy single `layout_image` behavior.

Color and image layers share the same z-order model.

## Backend And Renderer Impact

NestJS:

- DTO already has `TemplateBuilderLayoutLayer` through `TemplateBuilderMediaLayer`.
- Render payload mapper should include layer type metadata:
  - `source_type`
  - `background_color`
  - `asset_uri`
  - geometry
- Upload routes remain image-layer only.

Python renderer:

- Continue consuming `template_builder_layout_layers` in bottom-to-top order.
- Support image layers as today.
- Add color layer support by generating color overlays from `source_type: 'color'`.
- Preserve full vs non-full stack placement:
  - full: stack above content in final overlay
  - non-full: stack below content media

## Testing Plan

Angular focused regressions:

- Left default layer list shows only one `레이아웃` row even when `layoutLayers[]` has multiple items.
- Selecting `레이아웃` opens inspector layout manager.
- Inspector displays stack rows in Photoshop order, reverse of persisted order.
- Drag-drop reorder emits persisted bottom-to-top `layoutLayers[]`.
- `+ 이미지` appends a new image layer at visual top.
- `+ 단색` appends a movable full-frame color layer at visual top.
- Color layer renders in preview, can be selected, moved, resized, and edited through inspector.
- Deleting the last layer persists `layoutLayers: []` and does not resurrect legacy `layoutImage`.

NestJS focused regressions:

- Render payload includes `source_type` and `background_color` for color layout layers.
- Existing image stack payload remains compatible.

Python focused regressions:

- Color layout layers composite in stack order.
- Mixed color/image stacks composite in order.
- Legacy image-only stack tests continue passing.

## Out Of Scope

- Opacity and blend mode UI.
- Lock/visibility toggles beyond existing `visible` handling.
- Arbitrary layer grouping.
- Moving all text/logo layers into the same Photoshop-style layer manager.
