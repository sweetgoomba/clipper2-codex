# Template Builder Multiple Layout Layers Design

작성일: 2026-05-12

## 배경

현재 Template Builder의 layout media model은 `variant.layers.layoutImage` 한 개만 가진다. 이 구조는 `16:9`, `4:3`, `1:1`처럼 비율별로 서로 다른 layout image를 편집하는 데는 충분하지만, full ratio의 실제 legacy 구조를 표현하기에는 부족하다.

full ratio legacy template은 일반적으로 다음 순서로 렌더링된다.

1. 사용자 콘텐츠 이미지/영상
2. `gradient.png` full-frame overlay
3. title/subtitle/logo 등 텍스트 및 로고

일부 template은 예외적으로 `gradient.png` 아래에 `6_full.png`, `10_full.png`, `14_full.png`, `17_full.png` 같은 full 전용 layout image도 둔다. 즉 full ratio는 "layout image 없음"이 아니라, 최소 하나의 gradient overlay와 선택적인 lower layout image를 갖는다.

## 현재 임시 처리

2026-05-12 패치에서는 데이터 모델을 크게 바꾸지 않기 위해 다음 임시 기준을 적용했다.

- `layoutImage`는 ratio별 layer로 분리한다. 한 ratio의 layout image 편집은 다른 ratio에 전파되지 않는다.
- full ratio에서 legacy `layout_image`가 `gradient.png`이면 `layoutImage.assetUri`를 비우고 `contentArea.assetUri`에 `gradient.png`를 둔다.
- full ratio에서 legacy `layout_image`가 `_full.png`이면 `layoutImage.assetUri`는 `_full.png`로 유지하고, `contentArea.assetUri`에 `gradient.png`를 둔다.
- 기존 Clipper1 render payload는 `layout_image`가 하나뿐이므로, `layoutImage.assetUri`가 없을 때만 `contentArea.assetUri`를 fallback으로 내려보낸다.

이 방식은 Template Builder preview에서 "lower layout image + gradient overlay + text/logo" 순서를 보여주기 위한 호환 레이어다. 하지만 `contentArea`는 본래 layout layer가 아니므로 장기 모델은 아니다.

## 목표 모델

`TemplateBuilderVariant.layers`에 단일 `layoutImage` 대신 ratio별 layout stack을 둔다.

```ts
interface TemplateBuilderLayoutLayer {
  id: string;
  label: string;
  visible: boolean;
  assetUri: string | null;
  sourceType?: 'image' | 'color';
  backgroundColor?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  assetWidth?: number;
  assetHeight?: number;
  opacity?: number;
  blendMode?: 'normal';
  locked?: boolean;
}

interface TemplateBuilderLayers {
  layoutImage: TemplateBuilderMediaLayer; // migration bridge only
  layoutLayers?: TemplateBuilderLayoutLayer[];
  contentArea: TemplateBuilderMediaLayer;
  logoImage: TemplateBuilderMediaLayer;
  // text layers...
}
```

장기적으로는 `layoutImage`를 read/write bridge로만 남기고, UI/render는 `layoutLayers[]`를 source of truth로 사용한다.

## Layer Order

Preview와 renderer는 아래 순서로 그린다.

1. background color
2. content media placeholder or actual content
3. `layoutLayers[]` in ascending order
4. logo image
5. text layers and text boxes
6. selection/guide chrome

각 layout layer row에는 z-order controls가 필요하다.

- 위로 이동
- 아래로 이동
- 잠금
- 표시/숨김
- 삭제
- 이름 변경

## Migration

기존 single-layer variant migration:

- `layoutImage.assetUri`가 있으면 `layoutLayers = [{ id: 'layout.base', label: '레이아웃', ...layoutImage }]`
- full ratio이고 `contentArea.assetUri`가 `gradient.png`이면 `layoutLayers` 마지막에 `{ id: 'layout.fullGradient', label: 'Full Gradient', assetUri: gradient.png, x: 0, y: 0, width: 1080, height: 1920, locked: true }`를 추가한다.
- migration 후 `contentArea.assetUri`는 다시 콘텐츠 영역 표시 용도에서 제외한다.

Legacy system seed:

- normal full: `layoutLayers = [gradient]`
- full exception: `layoutLayers = [_full, gradient]`
- non-full: `layoutLayers = [legacy layout_image]`

## Render Contract Impact

현재 legacy Clipper1 payload는 `layout_image` 하나만 받는다. 다중 layer를 sample/final render까지 정확히 반영하려면 renderer contract가 바뀌어야 한다.

권장 contract:

```json
{
  "template_builder_layout_layers": [
    {
      "asset_uri": "https://.../6_full.png",
      "x": 0,
      "y": 0,
      "width": 1080,
      "height": 1920,
      "opacity": 1
    },
    {
      "asset_uri": "https://.../gradient.png",
      "x": 0,
      "y": 0,
      "width": 1080,
      "height": 1920,
      "opacity": 1
    }
  ]
}
```

Backward compatibility:

- If `template_builder_layout_layers` exists, renderer uses it.
- Otherwise renderer falls back to legacy `layout_image` fields.
- During transition, NestJS can still emit legacy `layout_image` as the first visible layout layer for older renderers.

## UI Impact

The current "레이아웃" row should become a compact layer stack inside the selected ratio.

Recommended first UI:

- Keep it in the existing left layer list under `기본 레이어`.
- Show one row per layout layer.
- Reuse current layout inspector for the selected layout layer.
- Add small icon buttons for reorder/visibility/lock/delete.
- Keep upload/fit/cover controls scoped to the selected layout layer.

Do not reintroduce a `공통 레이어` layout section. Layouts are ratio-specific.

## Not In Current Patch

This design is intentionally not implemented in the 2026-05-12 ratio split patch because it touches:

- DTO contract
- repository migration/backfill
- Angular layer row model
- inspector selection model
- preview render order
- NestJS render payload mapper
- Python/renderer support

The current patch only removes incorrect cross-ratio propagation and restores full ratio preview semantics without changing the saved layout stack contract.
