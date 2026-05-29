# Architecture Notes

이 문서는 Clipper2의 현재 구조를 빠르게 파악하기 위한 입구다. 팀원에게 설명할 긴 버전은 [design/TEAM_ARCHITECTURE_OVERVIEW.md](design/TEAM_ARCHITECTURE_OVERVIEW.md)를 보고, plugin/workflow runtime의 기술 분석은 [design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)와 [design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)를 본다. 자세한 과거 설계는 `design/`과 feature별 `records/`에 남긴다.

## Repo Roles

- `clipper_angular`
  - 사용자 UI.
  - NestJS API만 호출한다.
  - plugin process URL/port를 직접 알지 않는다.
- `clipper_nestjs`
  - 앱 control plane.
  - project, template, source, workflow orchestration, job history, WorkflowExecutor dispatch를 담당한다.
  - local/devapp에서는 Python plugin process를 `PluginHost`로 직접 실행할 수 있고, NestJS-native executor도 직접 실행할 수 있다.
- `clipper_electron`
  - desktop host/native adapter.
  - packaged NestJS spawn, packaged Python plugin process host, ffmpeg/model download IPC, file dialog, packaging을 담당한다.
- `clipper_python`
  - Python worker/plugin 구현.
  - `dialog_highlight`, `dance_highlight`, `clipper1_video_render` 같은 compute runtime을 담는다.

## Current Boundary

- Angular -> NestJS -> WorkflowExecutor -> runtime provider 흐름을 기준으로 한다.
- `WorkflowExecutor`는 Python runtime plugin, NestJS-native executor, virtual workflow를 같은 plugin/job 모델로 묶는 NestJS 계층이다.
- `PluginHost`는 Python process lifecycle control에 집중한다. `/jobs` 실행 dispatch의 기준은 `WorkflowExecutorRegistry`다.
- Electron은 desktop integration과 packaged process host 역할에 집중한다.
- plugin별 고정 포트나 Angular의 plugin URL 직접 접근은 금지한다.

## Primary References

- [context/PROJECT_HISTORY_AND_STATUS.md](context/PROJECT_HISTORY_AND_STATUS.md)
- [design/TEAM_ARCHITECTURE_OVERVIEW.md](design/TEAM_ARCHITECTURE_OVERVIEW.md)
- [design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
- [design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
- [design/BACKEND_ROLE_SPLIT_CURRENT.md](design/BACKEND_ROLE_SPLIT_CURRENT.md)
- [design/NESTJS_CONTROL_PLANE_REDESIGN.md](design/NESTJS_CONTROL_PLANE_REDESIGN.md)
- [design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md](design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md)
- [design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md](design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md)
- [design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md](design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md)
