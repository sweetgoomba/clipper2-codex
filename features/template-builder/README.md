# Template Builder

Template Builder는 top-level `템플릿` 메뉴에서 system/custom template family와 ratio variant를 편집하는 기능이다.

## Current Notes

- Template Builder 목록 API 자체는 ffmpeg/ffprobe를 직접 쓰지 않는다.
- 페이지 진입 시 text preview renderer worker를 warm-up하고, sample render 기능도 `clipper1_video_render` worker를 사용하므로 본 UI는 ffmpeg/ffprobe ready 이후에 시작한다.
- card thumbnail loading은 `TemplateFamilyThumbnailComponent`가 skeleton/load/error 상태를 관리한다.
- official template registry, S3 asset, local custom JSON persistence가 함께 존재한다.

## Active References

- [../../implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md](../../implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md)
- [../../design/TEMPLATE_BUILDER_APPROVED_SPEC_2026-05-07.md](../../design/TEMPLATE_BUILDER_APPROVED_SPEC_2026-05-07.md)
- [../../design/TEMPLATE_BUILDER_DESIGN_BRIEF_2026-05-06.md](../../design/TEMPLATE_BUILDER_DESIGN_BRIEF_2026-05-06.md)
- [../../implementation/TEMPLATE_BUILDER_MANUAL_APP_CHECKLIST_2026-05-10.md](../../implementation/TEMPLATE_BUILDER_MANUAL_APP_CHECKLIST_2026-05-10.md)
