# Clipper2 Modal Usage Inventory

Date: 2026-06-12

## Purpose

This document records where Clipper2 currently uses app-level modals,
modal-like overlays, and native confirmation prompts. The user decided not to
migrate the existing usages immediately, but this inventory should be used when
deciding whether to replace future cases with the shared confirmation modal.

Current shared confirmation component:

- `clipper_angular/src/shared/ui/confirmation-modal/confirmation-modal.component.*`

The component is intentionally simple: title, optional description, and
configurable action buttons. It is a good fit for destructive or blocking
confirmation prompts, but not for media viewers, progress dialogs, install
flows, or input forms unless it is extended.

## Current Usage

| Route / Area | Feature | Current implementation | Migration fit |
| --- | --- | --- | --- |
| `/shortform/url`, `/shortform/prompt`, `/shortform/paste` | Regenerate clips confirmation when existing clips would be replaced | `app-confirmation-modal` in `shortform-workflow-page.component.html` | Already uses the shared confirmation modal. |
| `/shortform/url`, `/shortform/prompt`, `/shortform/paste` | Clip generation progress dialog | `clip-generating-overlay` in `shortform-workflow-page.component.html` | Do not migrate to the simple confirmation modal. It is a progress/status dialog with images and staged text. |
| `/store` | ffmpeg/model download consent and retry during plugin install | `app-ffmpeg-consent`, `app-model-consent` in `store.component.html` | Keep separate for now. These are consent/error states tied to download services and the floating progress bar. |
| `/dance` | ffmpeg/model download consent and retry before Dance Highlight setup | `app-ffmpeg-consent`, `app-model-consent` in `dance-setup.component.html` | Same as Store. Keep as consent components unless a richer shared consent modal is designed. |
| `/dialog` | ffmpeg/model download consent and retry before Dialog Highlight setup | `app-ffmpeg-consent`, `app-model-consent` in `dialog-setup.component.html` | Same as Store. Keep as consent components unless a richer shared consent modal is designed. |
| `/templates` | ffmpeg download consent and retry before Template Builder render features | `app-ffmpeg-consent` in `template-builder-page.component.html` | Same as Store. Keep as consent component. |
| `/templates` | Sample render panel with render controls and video grid | `template-overlay` + `sample-render-panel` in `template-builder-page.component.html` | Do not migrate. It is a complex render/media panel, not a confirmation prompt. |
| `/templates` | Create template form | `template-overlay` + `template-create-panel` | Do not migrate to the simple confirmation modal. It is an input form. |
| `/templates` | Rename template form | `template-overlay` + `template-create-panel` | Do not migrate to the simple confirmation modal. It is an input form. |
| `/templates` | Clone template form | `template-overlay` + `template-create-panel` | Do not migrate to the simple confirmation modal. It is an input form. |
| `/templates` | Delete template confirmation | `template-overlay` + `template-create-panel--danger` | Good future migration candidate. It is close to a destructive confirmation prompt. |
| `/templates` | Temporary admin mode password form | `template-overlay` + password form | Do not migrate to the simple confirmation modal. It is an input form with inline validation. |
| `/templates` | Dirty edit-session cancel prompt | Native `window.confirm('저장하지 않은 변경사항이 사라집니다. 편집을 취소할까요?')` in `template-builder-page.component.ts` | Strong future migration candidate. Replace the native browser confirm with the shared confirmation modal. |
| `/dashboard` | Plugin runtime admission warning/block dialog before starting a runtime under resource pressure | `modal-backdrop` + `admission-modal` in `dashboard.component.html` | Conditional candidate. It has badge and detail rows, so migrate only after the shared modal supports custom body/detail content or a slot-like variant. |
| `/projects` | Completed project clip video preview, close, previous, next | `ProjectsClipOverlayComponent` | Do not migrate. It is a media viewer. |
| `/dance` member image selection | Candidate image preview | Local `preview-overlay` + `preview-modal` in `member-image-select.component.html` | Do not migrate. It is an image viewer. |

## Non-Modal Alerts

These are visible notifications, not modal dialogs:

- Template Builder error/success snackbar-like UI in
  `template-builder-page.component.html`.
- Dance/Dialog setup inline `role="alert"` error bars.
- Store `notice()` message.
- Floating install bar for ffmpeg/model download progress.

Do not treat these as confirmation-modal migration targets. If shared snackbar
work starts later, inventory them separately.

## Recommended Future Order

1. Replace Template Builder native `window.confirm` for dirty edit-session
   cancellation.
2. Consider replacing Template Builder delete confirmation with the shared
   confirmation modal.
3. Revisit Dashboard admission only if the shared modal gains custom body/detail
   content.

Avoid broad conversion of install consent, progress, media preview, and form
overlays. They have different interaction models and should either remain
specialized or be migrated to richer shared primitives later.

