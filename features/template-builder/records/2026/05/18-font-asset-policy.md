# Template Builder Font Asset Policy

Date: 2026-05-18

## Current Boundary

- NestJS owns the Template Builder catalog, official registry, registration API, and official DB/S3 integration.
- FastAPI/Python owns rendering only. It receives render payloads and should materialize any remote assets needed by the renderer.
- Official legacy template card thumbnails and layout images are already uploaded to S3 and stored in the official Postgres payload as public URLs.
- Fonts are still mixed:
  - legacy official templates store font filenames such as `Pretendard-SemiBold.otf`;
  - custom template font uploads are written under local `template-assets/.../fonts`;
  - Python resolves absolute font paths or filenames from `CLIPPER_LEGACY_FONTS_DIR` / legacy `adlight_python/fonts`.
- Custom/system edit persistence is still local JSON through `TemplateBuilderService` repository. Official registration snapshots the edited system family into Postgres only when `템플릿 등록` is invoked.

## Policy

For official Template Builder templates, every binary asset reference in the DB payload should be a remote object URL owned by the official asset store:

- card thumbnails: `templates/legacy-clipper1/card-thumbnails/...`
- layout/content/logo images: `templates/legacy-clipper1/layouts/...` or `templates/legacy-clipper1/logos/...`
- fonts: `templates/legacy-clipper1/fonts/...`

The official Postgres JSON payload remains the source of truth. `clipper2_template_assets` is an index/audit table derived from that payload, not a separate runtime lookup requirement.

Renderers must not depend on bundled official template files for official templates. Python may keep local filename fallback only for legacy payload compatibility and existing custom/local templates.

## Minimal Implementation Step

1. Extend `register-official-template-seed.js --asset-mode=upload` to collect text layer font files, upload them from `adlight_python/fonts`, and rewrite `layer.text.fontFamily` to the S3 public URL.
2. Extend the Python renderer font loading path to stage `http(s)` font URLs through the existing per-render `RemoteAssetStager` before Pillow/fontTools access.
3. Keep custom template font uploads local for now. Moving custom/personal templates to DB/S3 is a separate repository policy decision and should not be coupled to official template migration.

## Non-Goals

- Do not add a new central Template API in this step.
- Do not move local custom/system edit JSON persistence in this step.
- Do not remove legacy local font fallback yet; tests and older payloads still rely on it.
