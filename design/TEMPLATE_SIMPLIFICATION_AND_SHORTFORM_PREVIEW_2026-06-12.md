# Template Simplification And Shortform Preview

Date: 2026-06-12
Status: approved product direction, implementation in progress

## Summary

Template Builder and shortform template usage are moving from the existing full
legacy-compatible template model to a simplified template model.

2026-06-15 sequence refinement:

- Do not build the full shortform preview engine before the simplified Template
  Builder model is available.
- First lock the template runtime contract that both Template Builder and the
  preview/render paths will consume.
- Then simplify Template Builder so it creates real shortform templates,
  captures real 9:16 card thumbnails, and stores the runtime contract.
- Then replace the current static shortform preview box with the browser
  timeline preview engine.

2026-06-16 implementation update:

- The first browser timeline preview engine is implemented in Angular.
- The preview engine does not create FFmpeg preview files. It composes clips,
  media, TTS, BGM, main title lines, and captions in the browser.
- The shortform runtime canvas is now 1080x1920. The original Builder canvas is
  preserved as `templateCanvas`, and its placement inside the portrait canvas is
  preserved as `templateFrame`.
- The shortform production page now loads the user's Builder shortform template
  list directly from `template_builder.custom`. It no longer falls back to
  built-in simplified templates when the Builder list is empty.

2026-06-17 render payload update:

- The final Python worker path still consumes the legacy Clipper1 payload shape,
  so Builder shortform presets must expose the Template Builder render contract
  as well as the browser `ShortformTemplateRuntimeSpec`.
- `clipper_nestjs` `af8e838` adds `templateBuilderRenderContract`, layers,
  content area, and output size to shortform preset default params, and maps
  `main_title1`/`main_title2` overlay roles back to legacy title payload fields.
- This keeps the final render aligned with the same content area, layout layer,
  main title, and caption geometry that the browser preview reads.

The new template model keeps only:

- `main_title1`
- `main_title2`
- `caption`

The following legacy template roles are removed from new templates and from the
shortform production page:

- `sub_title`
- `bottom_title`
- `logo`

Main title remains a two-line title. It is not collapsed into one field.

Each template has exactly one ratio. A template is either `1:1` or `4:3`.
Templates no longer contain four ratio variants under one family.

Existing official legacy templates are not used by the new shortform production
template list.

## Scope Split

This change has two related but separate workstreams.

### Shortform Production Page

The immediate shortform production page must stop exposing controls that no
longer exist in the simplified template model.

Required UI changes:

- Rename the `레이아웃` section to `템플릿`.
- Remove ratio selection.
- Remove title visibility checkboxes.
- Show a template list and let the user select one template.
- The selected template determines the output ratio.
- The selected template is reflected in preview and in the final render payload.

Required data changes:

- `renderSettings.ratio` must no longer be a user-selected control.
- The selected template must carry its own ratio, either `1:1` or `4:3`.
- The generated video must use the selected template ratio.
- `sub_title`, `bottom_title`, and `logo` must not be populated from fallback UI text.
- `main_title1` and `main_title2` must come from generated title data or user edits.

Current known gap:

- Clipper2 already asks the script generator for `main_title1`,
  `main_title2`, `sub_title`, and `bottom_title`, and the normalizer returns
  `mainTitle1`, `mainTitle2`, `subTitle`, and `bottomTitle`.
- `ShortformProjectService.generateClips()` currently drops those generated
  title fields when it maps the draft to `ShortformProject`.
- Angular `ShortformProject` has no generated title fields, so the shortform
  page falls back to `project.title`. For prompt projects, `project.title` is
  currently derived from the prompt text.
- Before final render payload parity, generated `mainTitle1` and `mainTitle2`
  must be stored in the shortform project and initialized into the page title
  state.

### Template Builder Simplification

Before changing Template Builder code, preserve the current full Template
Builder implementation on archive branches.

Recommended archive branch name:

```text
archive/template-builder-full-2026-06-12
```

Current local heads at the time this design was written:

```text
clipper_angular: 9c23235 Polish shortform style controls
clipper_nestjs:  4504b55 Update shortform audio presets
clipper_python:  535131c Render sample images as cover
.codex:          dc504ef docs: record Clipper2 modal inventory
```

Create archive branches before any simplification implementation in repos that
will be touched. At minimum this means `clipper_angular` and `clipper_nestjs`.
Include `clipper_python` if renderer/template behavior changes there. Include
`.codex` if preserving the old Template Builder documentation line is useful.

After archive branches exist, the current working branches should directly
replace the existing Template Builder with the simplified model. Do not keep a
parallel full Template Builder route in the active product.

## Simplified Template Domain

### Template

```text
SimplifiedTemplate
  id
  name
  status: draft | published
  ratio: 1:1 | 4:3
  outputSize
  contentArea
  layers
  assets
  sampleRender
  createdAt
  updatedAt
```

There is no `TemplateFamily` with multiple ratio variants in the new product
model. A template id points to one ratio and one set of layers.

### Layers

Allowed layers:

```text
mainTitleLine1
mainTitleLine2
caption
contentArea
layout/background assets as required by rendering
```

Removed user-facing layers:

```text
subTitle
bottomTitle
logoImage
logoText
```

`contentArea` and layout/background data may remain internal renderer/template
geometry. They are not user-facing title/logo roles.

## Simplified Template Runtime Contract

The simplified template must not be represented only by a thumbnail and ratio.
The runtime template contract is the shared source for:

- Template Builder canvas editing.
- Shortform production template picker.
- Browser timeline preview.
- Final render recipe/provider.

The contract should be stored with each template and returned by the shortform
template catalog API.

Target shape:

```text
ShortformTemplateRuntimeSpec
  schemaVersion: shortform-template-runtime.v1
  templateId
  ratio: 1:1 | 4:3
  canvas:
    width: 1080
    height: 1920
    fps
    backgroundColor
  templateCanvas:
    width
    height
  templateFrame:
    x, y, width, height, scale
  thumbnail:
    url
    captureRatio: 9:16
  regions:
    clip_media:
      x, y, width, height
      fit: cover | contain | fill
      motionPreset
    main_title1:
      x, y, width, height
      anchor, zIndex
      textStyle
    main_title2:
      x, y, width, height
      anchor, zIndex
      textStyle
    caption:
      x, y, width, height
      anchor, zIndex
      textStyle
  audio:
    ttsVolume
    bgmVolume
```

Text style must include enough information for both browser preview and final
render:

```text
fontFamily
fontSize
fontWeight
lineHeight
letterSpacing
color
textAlign
backgroundColor
padding
borderColor
borderWidth
borderRadius
boxSizing
outline
shadow
maxLines
```

Only these public text slots are allowed in the new shortform runtime contract:

```text
main_title1
main_title2
caption
```

The following slots must not appear in new shortform runtime templates:

```text
sub_title
bottom_title
logo
```

### Ratios

Allowed ratios:

```text
1:1
4:3
```

Template creation requires choosing one ratio. Changing ratio after template
creation should be treated as creating a different template, not as adding a
variant to the same template.

## Existing Official Legacy Templates

Existing official legacy templates must not be shown in the new shortform
template picker.

They may remain in code/data for historical reference, golden-frame tests, or
archive branches, but they are not product-visible templates for the simplified
shortform flow.

The new shortform template picker must use a new simplified catalog. New built-in
templates should be authored directly in the simplified model.

## Shortform Preview Direction

The current Clipper2 shortform production page preview is still an approximate
static preview: it shows one selected media asset and one caption text inside a
ratio box. That is not the target behavior. The new preview should be a
timeline preview.

Required behavior:

- Provide a real play/pause preview control.
- Play through generated clips as a video-like timeline without pre-rendering an
  FFmpeg preview file.
- Clicking a caption-level play button seeks to that caption start time.
- TTS audio plays during preview from each narration line's `ttsAudioUrl`.
- BGM plays during preview from the selected BGM preset/artifact URL.
- The preview renders the selected clip media asset.
- The preview overlays `main_title1`, `main_title2`, and the active caption.
- The preview uses the selected template ratio and runtime layout/style
  contract.
- The preview updates when the selected template changes.
- The preview updates when caption text is edited and the regenerated TTS result
  updates `ttsAudioUrl` or `durationMs`.
- The preview updates when clips are added, deleted, reordered, or when clip
  media selection changes.

The browser preview engine should compose:

```text
ShortformProject clips
  + narration line text, durationMs, ttsAudioUrl
  + clip mediaSlots and selected assets
  + selected BGM
  + selected ShortformTemplateRuntimeSpec
  -> interactive DOM/CSS/media/audio timeline preview
```

The preview engine should not call final render or create a temporary rendered
video file for normal editing playback.

Removed preview behavior:

- No `sub_title` overlay.
- No `bottom_title` overlay.
- No `logo` overlay.
- No ratio picker independent of the selected template.

## Preview And Final Render Parity

Browser HTML/CSS preview cannot guarantee pixel-identical output with the final
FFmpeg/Python render. The main differences are font shaping, line breaks, image
crop/scale, overlay composition, timing, and audio mixing.

Use a hybrid preview strategy:

1. Fast interactive browser preview for editing:
   - Uses the same template data model and timing data as final render.
   - Good enough for editing and timing inspection.
   - Not presented as pixel-identical proof.

2. Render-engine preview for final confirmation:
   - Uses the same render recipe/provider path as final output.
   - Produces a short clip, frame, or low-cost preview artifact.
   - Used when pixel/renderer parity matters.

The implementation should avoid duplicating template semantics separately in
Angular and renderer code. Angular preview may render with HTML/CSS, but it
should consume the same normalized template contract that the renderer consumes.

## Data Flow Target

```text
Script generation
  -> ShortformProject generated titles:
       mainTitle1
       mainTitle2
  -> Shortform clips:
       narration lines
       media assets
       TTS artifact URLs
  -> Simplified template selection:
       templateId
       ratio
       layer geometry/styles
  -> Browser timeline preview:
       media + TTS + BGM + main titles + caption
  -> Final render payload/recipe:
       same templateId/ratio/layers/titles/captions/audio
```

## Implementation Order

1. Preserve existing full Template Builder on archive branches.
2. Add or define the simplified template runtime contract in documentation and
   tests.
3. Fix shortform generated title persistence for `mainTitle1` and `mainTitle2`.
4. Replace shortform `레이아웃` controls with the simplified `템플릿` picker.
5. Remove shortform title visibility controls and sub/bottom/logo preview
   overlays.
6. Ensure selected template ratio drives shortform preview and render payload at
   the static-preview level.
7. Simplify Template Builder from full family/variant editing to single-ratio
   shortform template creation/editing.
8. Make Template Builder save `ShortformTemplateRuntimeSpec` and capture real
   9:16 shortform thumbnails from the template canvas.
9. Replace the temporary simplified built-in template catalog with templates
   produced by the simplified Template Builder path.
10. Build the browser timeline preview engine that consumes
    `ShortformTemplateRuntimeSpec` plus `ShortformProject` clips/TTS/media/BGM.
11. Add render-engine preview only after the browser preview contract and
    simplified Template Builder contract are stable.

## Non-Goals

- Do not start Project-first / Plugin / Queue restructuring as part of this
  change.
- Do not keep old official legacy templates visible in the new shortform
  template picker.
- Do not maintain a product-visible full Template Builder route after the
  archive branch is created.
- Do not promise browser preview pixel identity with FFmpeg output.

## Verification Targets

Shortform:

- Selecting a template updates the preview ratio.
- The final log/render payload uses the selected template id and ratio.
- No `sub_title`, `bottom_title`, or `logo` fallback display text leaks into
  payload.
- Generated `mainTitle1` and `mainTitle2` appear in preview and payload.
- Caption-level play seeks to the caption start and plays TTS.
- BGM and TTS both play in preview without blocking editing.

Template Builder:

- Creating a template requires choosing `1:1` or `4:3`.
- Created templates have exactly one ratio.
- Editor exposes only main title line 1, main title line 2, caption, and
  renderer-required layout/content controls.
- No sub-title, bottom-title, or logo controls remain in the simplified editor.
- Sample render uses the simplified template contract.

Renderer:

- Simplified template render payload contains only main title lines and caption
  overlays.
- Output dimensions match selected template ratio.
- Render-engine preview and final render consume the same normalized template
  contract.
