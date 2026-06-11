# Clipper Studio

Clipper Studio는 Clipper1 template catalog, source asset, script/TTS/render flow를 project manifest 구조 위에서 다루는 제작 화면이다.

## Current Notes

- 2026-06-11 현재 우선순위는 strict legacy parity port다. Clipper2 shortform production editor는 `adlight_angular` 레거시 Clipper 숏폼 제작 화면과 UI, 스타일, 영상 생성 전 동작이 완전히 동일해야 한다.
- 첫 구현 패스는 진행됐다. `clipper_angular`는 legacy shortform editor UI/style을 Clipper2 shell 안으로 가져왔고, `clipper_nestjs`는 shortform clip generation을 LLM, Naver Clova TTS, Naver image search, WebSocket progress event 기반으로 연결했다.
- 아직 Phase 1 완료가 아니다. 남은 핵심은 legacy 화면과의 세부 visual/behavior parity 검증 및 수정, URL/prompt/paste 전체 수동 플로우 검증, packaged runtime 검증이다.
- Project-first / Plugin / Queue 모델 정리는 아직 시작하지 않았다. 현재 순서는 shortform legacy parity를 먼저 끝내고, 그 다음에 큐/프로젝트/잡 모델 정리를 시작하는 것이다.
- 이 Phase 1에서는 `숏폼 생성하기` 버튼이 backend video generation, queue, render job, `/projects` navigation을 호출하면 안 된다. legacy `adlight_python` video-create schema payload를 `console.log`로 확인하는 것까지만 한다.
- 사용자-facing Clipper1/Variation 방향은 `SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`를 우선한다.
- `clipper1_video_render` worker와 shared render recipe/provider 구조를 사용한다.

## Active References

- [records/2026/06/11-shortform-legacy-parity-port.md](records/2026/06/11-shortform-legacy-parity-port.md)
- [records/2026/06/11-shortform-legacy-parity-port-plan.md](records/2026/06/11-shortform-legacy-parity-port-plan.md)
- [../../design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md](../../design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md)
- [../../design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md](../../design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md)
- [../../implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-06.md](../../implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-06.md)
