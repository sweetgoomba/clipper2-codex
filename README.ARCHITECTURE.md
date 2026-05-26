# Architecture Notes

이 문서는 Clipper2의 현재 구조를 빠르게 파악하기 위한 입구다. 팀원에게 설명할 긴 버전은 [design/TEAM_ARCHITECTURE_OVERVIEW.md](design/TEAM_ARCHITECTURE_OVERVIEW.md)를 보고, plugin system의 기술 분석은 [design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)를 본다. 자세한 과거 설계는 `design/`과 feature별 `records/`에 남긴다.

## Repo Roles

- `clipper_angular`
  - 사용자 UI.
  - NestJS API만 호출한다.
  - plugin process URL/port를 직접 알지 않는다.
- `clipper_nestjs`
  - 앱 control plane.
  - project, template, source, workflow orchestration, local/devapp plugin host를 담당한다.
- `clipper_electron`
  - desktop host/native adapter.
  - packaged NestJS spawn, Python plugin process, ffmpeg/model download IPC, file dialog, packaging을 담당한다.
- `clipper_python`
  - Python worker/plugin 구현.
  - `dialog_highlight`, `dance_highlight`, `clipper1_video_render` 같은 compute runtime을 담는다.

## Current Boundary

- Angular -> NestJS -> plugin/runtime provider 흐름을 기준으로 한다.
- Electron은 desktop integration과 packaged process host 역할에 집중한다.
- plugin별 고정 포트나 Angular의 plugin URL 직접 접근은 금지한다.

## Primary References

- [context/PROJECT_HISTORY_AND_STATUS.md](context/PROJECT_HISTORY_AND_STATUS.md)
- [design/TEAM_ARCHITECTURE_OVERVIEW.md](design/TEAM_ARCHITECTURE_OVERVIEW.md)
- [design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
- [design/BACKEND_ROLE_SPLIT_CURRENT.md](design/BACKEND_ROLE_SPLIT_CURRENT.md)
- [design/NESTJS_CONTROL_PLANE_REDESIGN.md](design/NESTJS_CONTROL_PLANE_REDESIGN.md)
- [design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md](design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md)
- [design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md](design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md)
- [design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md](design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md)
