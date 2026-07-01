# Dance Highlight

Dance Highlight는 artist/member detection, member image selection, reference image selection, pipeline execution을 포함한다.

## Current Notes

- member image search는 Python plugin이 아니라 NestJS image search API가 담당한다.
- Naver/Kakao image search key는 NestJS env에 있어야 한다.
- Python env에는 Naver/Kakao key를 두지 않는다.
- member image selection 페이지는 내부 단계 컨테이너가 스크롤을 소유한다.

## Active References

- [../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md](../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md)
- [../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md](../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md)
- [../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)
