# Dance Highlight

Dance Highlight는 artist/member detection, member image selection, reference image selection, pipeline execution을 포함한다.

## Current Notes

- 2026-10-23 Person 기능 브랜치가 데스크톱 4개 원격 dev에 병합됐다. 안무와 인물은 공통 AuraFace/ONNX Runtime 1.31.0을 사용하며, 후속 그룹화·구간 구성은 각 플러그인 정책이다.
- [최신 병합·검증·인계](../highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md)와 [W13 작업 카드](../../handoff/tasks/dance-highlight.md)를 먼저 읽는다. 결과 UI 이식과 원본 구간 저장 전환은 [무대 사용성 완료 기록](../highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md)과 같이 원격 dev에 반영됐다(Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`). 품질 개선은 별도 무대 파이프라인 세션에서 이어간다. 실제 영상·Windows 검증은 별도다.

- member image search는 Python plugin이 아니라 NestJS image search API가 담당한다.
- Naver/Kakao image search key는 NestJS env에 있어야 한다.
- Python env에는 Naver/Kakao key를 두지 않는다.
- member image selection 페이지는 내부 단계 컨테이너가 스크롤을 소유한다.

## Active References

- [../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md](../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md)
- [../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md](../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md)
- [../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)
