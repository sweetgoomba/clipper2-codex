# Template Builder Approved Spec

작성일: 2026-05-07
상태: v4 mockup 사용자 승인 후 구현 전 spec

## 기준 문서

- `.codex/design/LEGACY_CLIPPER1_TEMPLATE_SYSTEM_2026-05-06.md`
- `.codex/design/TEMPLATE_BUILDER_DESIGN_BRIEF_2026-05-06.md`
- visual mockup: `.superpowers/brainstorm/75878-1778126293/content/template-builder-editor-ko-v4.html`

## 승인된 방향

사용자는 2026-05-07에 v4 mockup 방향을 승인했다.

핵심 승인 내용:

- 템플릿 생성기는 top-level `템플릿` 메뉴다.
- UI는 한국어로 제공한다.
- 캔버스 중심 화면이 아니라 속성 편집 중심 화면으로 간다.
- 화면은 `왼쪽 설정/레이어`, `가운데 축소 캔버스`, `오른쪽 대형 속성 패널`의 3열 구조를 기준으로 한다.
- 가운데 캔버스는 실제 1080x1920 output을 uniform scale로 축소한 preview와 selection handle을 제공한다.
- 오른쪽 속성 패널은 위치, 텍스트, 색상, 박스, 윤곽선, 그림자, 표시 조건, sample render/publish gate를 다룬다.
- 컬러 팔레트는 필수다.
- ratio는 `16:9`, `4:3`, `1:1`, `full` 네 개 fixed slot으로만 표현한다.
- `variant 추가`, `없는 비율 만들기` 문구는 사용하지 않는다.

## 제품 범위

Template Builder는 workflow plugin이 아니다. Clipper2 shell의 top-level feature이며, Shared Template Catalog를 관리한다.

생성된 template은 다음 consumer가 공통으로 사용한다.

- Clipper1 workflow
- Variation workflow
- 향후 shorts video를 출력하는 workflow plugins

1차 목표는 디자인팀/내부 운영자가 기존 Zeplin 측정과 spreadsheet 입력 작업을 줄이고, legacy Clipper1과 호환되는 template을 직접 만들 수 있게 하는 것이다.

## Legacy Compatibility

Renderer output semantics는 기존 Clipper1과 호환되어야 한다.

고정 기준:

- output coordinate system: 1080x1920
- supported ratios: `16:9`, `4:3`, `1:1`, `full`
- content area heights:
  - `16:9`: 608
  - `4:3`: 810
  - `1:1`: 1080
  - `full`: 1920
- template settings는 legacy `settings` JSONB의 값을 보존할 수 있어야 한다.
- Clipper2 preview는 legacy Angular의 261x455 non-uniform preview를 계승하지 않고 uniform scale을 사용한다.

## Architecture

권장 구조:

```text
Angular Template Builder UI
  -> NestJS TemplateCatalogController
    -> TemplateCatalogService
      -> TemplateRepository interface
        -> LocalFileTemplateRepository
        -> DbTemplateRepository later
        -> RemoteApiTemplateRepository later
      -> TemplateAssetRepository interface
      -> TemplateValidationService
      -> TemplateSampleRenderService
        -> video.render capability
```

경계 원칙:

- Angular는 UI state와 사용자 interaction만 담당한다.
- Angular는 template 저장 위치가 local file인지 DB인지 몰라야 한다.
- NestJS가 catalog orchestration, draft/publish lifecycle, validation, sample render job을 담당한다.
- Electron은 필요 시 native file dialog와 packaged runtime path만 제공한다.
- renderer는 `TemplatePreset` 또는 `RenderRecipe` 계약으로 template을 소비한다.

## Data Model

### TemplateFamily

```text
TemplateFamily
  id
  name
  ownerType: system | user
  source: built_in | custom
  statusSummary
  createdAt
  updatedAt
  variants
```

### TemplateVariant

```text
TemplateVariant
  id
  familyId
  ratio: 16:9 | 4:3 | 1:1 | full
  status: draft | published
  outputSize: 1080x1920
  contentArea
  settings
  assets
  validation
  sampleRender
```

### Ownership

System template:

- 모든 유저가 조회 가능
- 삭제 불가
- 직접 수정 불가
- 복제해서 user custom draft로 시작 가능

User custom template:

- 수정 가능
- 삭제 가능
- 저장 위치는 repository adapter로 숨긴다
- local-only 또는 DB/API 저장으로 갈아끼울 수 있어야 한다

## Editor UI

### Left Panel

역할:

- template family metadata
- 시작 방식 표시
- 네 개 fixed ratio slot
- legacy-compatible fixed layer list

Ratio slot 상태:

- `게시됨`
- `초안`
- `편집 중`
- `+ 생성`

Layer list:

- layout image
- content area
- sub title
- main title line 1
- main title line 2
- bottom title
- dialogue subtitle
- subtitle box/bar
- logo image
- logo text

### Center Canvas

역할:

- 1080x1920 output의 uniform-scale preview
- selected layer bounding box
- drag/resize handles
- content area guide
- zoom indicator

캔버스는 편집의 시각적 확인과 직접 조작을 담당하지만, 화면의 주 작업 영역은 오른쪽 속성 패널이다.

### Right Properties Panel

역할:

- 선택 layer의 실제 px 속성 편집
- legacy settings에 필요한 style fields 노출
- sample render/publish 상태 표시

탭:

- 위치
- 텍스트
- 색상
- 박스
- 효과

위치:

- x/y
- width/height
- one-line y offset
- two-line first/second y offset
- left/right align margin
- alignment

텍스트:

- font
- font size
- tracking
- line height
- preview text

색상:

- current color
- hex input
- opacity
- default swatches
- recent swatches
- future template common palette

박스:

- box color
- alpha
- padding left/right
- height
- border color
- border width

윤곽선:

- outline width
- outline color
- renderer applicability status

그림자:

- shadow color
- shadow outline width
- shadow outline color
- shadow x offset
- shadow y offset

## Lifecycle

Creation:

- blank template
- clone system template
- clone custom template

Save:

- draft save persists editor state
- draft is not exposed to shorts workflow plugins

Publish:

- schema validation passes
- required assets exist
- numeric bounds pass
- sample render job succeeds
- only published variants are selectable in Clipper1/Variation/future shorts plugins

2026-05-07 implementation note:

- Published custom variants are now bridged into the existing `/template-presets` catalog as `source=template_builder`.
- The Clipper Studio template picker no longer requests only `source=clipper1`, so published custom presets can appear through the same catalog endpoint as legacy templates.
- The preset bridge carries `defaultParams.templateBuilderLayers` and related metadata.
- `LegacyClipper1RenderPayloadMapper` now converts that fixed layer snapshot into the legacy Python renderer's `template_settings` shape for first-pass final render compatibility.
- Layout image upload is now available for custom variants as a local-path first slice.
- Font upload is now available per text layer as a local-path first slice, and the Python renderer passes the uploaded font directory to ffmpeg/libass through `fontsdir`.
- The Python final renderer now has a headless custom-template visual contract smoke. It creates a real MP4 and verifies layout image, content area, uploaded font `fontsdir`, ASS event count, and sampled frame pixels.
- Template Builder sample render now requests `video.render.legacy_clipper1.python_worker` instead of the basic letterbox renderer. The sample recipe carries legacy Clipper1 provenance, custom variant layer snapshot, sample media, sample TTS, sample BGM, and sample logo.
- Draft sample recipes are accepted by the legacy payload mapper when they carry `templateParams.templateBuilderVariantId`, even if the base `templatePresetId` is a built-in preset rather than a published custom preset.
- Successful sample render artifacts are served through a dedicated Template Builder file endpoint and shown as a playable video in the Angular editor publish gate.
- Python renderer now maps Template Builder box color/alpha, outline color/width, and shadow color/offset into ASS style fields for text overlays.
- Full renderer parity still depends on Python renderer support for every Template Builder style field, especially `shadow_outline_*`, and on explicit font family name override if uploaded file stem/internal family name mismatch becomes a real issue.

Sample render:

- 3-5 second mp4
- includes sample media, title, logo, two-line subtitle, TTS, BGM
- failure must show actionable reason

2026-05-07 implementation note:

- First real sample render slice now executes `video.render.local_ffmpeg.basic` with `dryRun: false` and produces a 3-second MP4 artifact instead of a fake success marker.
- This first slice validates the render capability path and publish gate artifact contract.
- 2026-05-07 follow-up: sample render now requests the legacy Python worker provider with title/logo/subtitle/TTS/BGM recipe inputs, so the service boundary is template-aware.
- 2026-05-07 E2E follow-up: an actual `clipper1_video_render` worker run produced `template-sample/main.mp4` for a default draft full-ratio sample.
- 2026-05-07 UI follow-up: successful sample render MP4s are playable from the Template Builder editor publish gate.
- Full legacy-compatible visual/audio sample parity still needs renderer field-by-field parity checks.

## Error Handling

Validation errors:

- Missing required asset
- Invalid ratio
- Out-of-bounds coordinate
- Invalid color/alpha
- Missing font
- Renderer-incompatible setting

UI behavior:

- Show field-level error when possible
- Block publish while errors exist
- Allow draft save even when publish validation fails
- Preserve user edits when sample render fails

Sample render failure:

- Keep template in draft
- Show failed step and message
- Allow retry after field or asset correction

## Testing Strategy

Angular:

- standalone zoneless components
- `provideExperimentalZonelessChangeDetection()`
- signal/computed state for local UI
- no `zone.js`, no `fakeAsync`, no `tick`
- tests for:
  - ratio slot rendering
  - layer selection
  - properties panel field binding
  - color palette selection
  - canvas coordinate conversion
  - publish button disabled until validation/sample render success

NestJS:

- repository adapter contract tests
- local filesystem repository tests
- DTO validation tests
- draft save/load tests
- publish gate tests
- sample render job orchestration tests with fake `video.render` provider

Renderer parity:

- legacy template fixture -> Clipper2 render recipe mapping
- fixed sample render comparison by layout/coordinate contract
- custom Template Builder payload -> Python renderer smoke with real MP4, layout/content/font/event/pixel assertions
- shadow x/y behavior is currently mapped to ASS `Shadow` using the larger absolute offset

## Implementation Boundaries

Do not implement arbitrary layer editing in v1.

Do not add export/import.

Do not add arbitrary ratios.

Do not store template state directly in Angular local component code as the source of truth.

Do not couple workflow plugins to local filesystem template storage.

Do not reintroduce Zone.js in Angular.

## Open Decisions Before Implementation Plan

These can be resolved in the implementation plan or early Phase 0, but must not be hidden:

- Exact local filesystem schema for custom template drafts.
- Built-in template seed source path and migration format.
- Whether custom fonts are allowed in v1 or only built-in font catalog.
- How layout image upload is exposed in v1.
- Whether shadow x/y offset follows legacy effective behavior or schema intent.
- Sample render provider: direct existing render provider vs dedicated template sample recipe builder.

## Spec Self-Review

Placeholder scan:

- No `TBD` or empty section remains.

Consistency check:

- The spec keeps Template Builder as top-level feature, not workflow plugin.
- The UI layout matches approved v4 mockup.
- Ratio behavior matches the fixed four-slot decision.
- Storage remains repository/adapter based for future DB/API replacement.
- Angular rules match the zoneless project standard.

Scope check:

- The spec is large but still a single first implementation theme: top-level Template Builder with legacy-compatible fixed layer editor.
- Implementation should be split into phases before coding.

Ambiguity check:

- Open decisions are explicitly listed instead of being treated as settled.
