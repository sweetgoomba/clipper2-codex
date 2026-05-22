# Template Builder Editor Checkpoint - 2026-05-10

## Scope

- Template Builder gallery/card layout, inspector/property UI, reusable color field, layout background controls.
- Common/default layer interaction rules and layout selection lock behavior.
- Canvas preview toolbar cleanup, horizontal-center action, measurement distance guides.
- Box effect width mode contract: text-fit vs fixed width.
- Preview/final text artifact drift fixes for text-fit box move/center behavior.

## Commits

- `clipper_angular` `c4c52e3 feat: refine template builder preview editor`
- `clipper_nestjs` `5923995 feat: extend template builder box sizing contract`
- `clipper_python` `89e940b feat: render template builder fixed text boxes`

## Key Decisions

- `레이아웃`은 `공통 레이어`에만 둔다. `레이아웃`은 항상 사용되므로 사용 토글과 사용/사용 안 함 상태 텍스트를 표시하지 않는다.
- `기본 레이어`가 선택된 상태에서는 layout image preview interaction을 막는다.
- layout image background mode가 `image`이면 배경색 UI를 숨기고 background color는 `#000000`으로 유지한다. `color`이면 image upload UI를 숨긴다.
- text style/effect는 role-scoped common style이다. UI에서는 기본 레이어 요소를 선택했을 때 비율 공통 스타일/효과임을 속성 영역에서 다룬다.
- box effect `sizing: 'text'`는 text width + `paddingX`로 계산하고 horizontal resize를 막는다.
- box effect `sizing: 'fixed'`는 `box.width`를 사용하고 horizontal resize가 common style `box.width`를 patch한다.
- measurement guide neighbor에는 visible `contentArea`도 포함한다. 단 `contentArea`는 편집 대상이 아니라 preview guide다.
- text-fit box artifact는 visible frame과 persisted layer anchor x가 다를 수 있다. selection/measurement/center 계산은 visible frame을 쓰되, patch emit 시 persisted layer x로 되돌려 저장한다.

## Verification

- `clipper_angular npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`: passed (`78 SUCCESS`)
- `clipper_angular npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder.service.spec.ts --include=src/features/template-builder/components/template-builder-editor.component.spec.ts --include=src/features/template-builder/pages/template-builder-page.component.spec.ts --include=src/features/template-builder/components/template-family-gallery.component.spec.ts`: passed (`123 SUCCESS`)
- `clipper_angular npm run build`: passed
- `clipper_angular git diff --check`: passed
- `clipper_nestjs npm run build`: passed
- `clipper_nestjs git diff --check`: passed
- `clipper_python uv run --extra test pytest tests/test_template_builder_text_renderer.py`: passed (`5 passed`)
- `clipper_python git diff --check`: passed

## Next Work

- User should rebuild/run packaged Electron and manually verify Template Builder editor behavior:
  - Template gallery card sizing and thumbnail crop.
  - Inspector controls, color picker/hex sync, layout background mode switching.
  - `가로 중앙` with text-fit box effects after moving the element.
  - Fixed box width resizing in preview and sample/final render parity.
  - Measurement guides against frame edges, nearby layers, and content area.
- If visual drift remains, debug through `TemplateBuilder layer -> text preview artifact metadata -> canvas frame -> sample/final render payload`.
