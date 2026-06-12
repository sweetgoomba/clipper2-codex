# Template Builder

Template Builder는 top-level `템플릿` 메뉴에서 system/custom template family와 ratio variant를 편집하는 기능이다.

## Current Notes

- 2026-06-12에 Template Builder 제품 방향이 simplified model로 변경됐다.
  - 새 템플릿은 `main_title1`, `main_title2`, `caption`만 사용한다.
  - `sub_title`, `bottom_title`, `logo`는 새 템플릿/숏폼 제작 flow에서 제거한다.
  - 템플릿 하나는 `1:1` 또는 `4:3` 중 하나의 ratio만 가진다.
  - 기존 full Template Builder 구현은 단순화 작업 전 archive branch로 보존한다.
  - 기준 문서: [../../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
- Template Builder 목록 API 자체는 ffmpeg/ffprobe를 직접 쓰지 않는다.
- 페이지 진입 시 text preview renderer worker를 warm-up하고, sample render 기능도 `clipper1_video_render` worker를 사용하므로 본 UI는 ffmpeg/ffprobe ready 이후에 시작한다.
- card thumbnail loading은 `TemplateFamilyThumbnailComponent`가 skeleton/load/error 상태를 관리한다.
- official template registry, S3 asset, local custom JSON persistence가 함께 존재한다.

## Active References

- [records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)
- [design/approved-spec.md](design/approved-spec.md)
- [design/design-brief.md](design/design-brief.md)
- [runbooks/manual-app-checklist.md](runbooks/manual-app-checklist.md)
