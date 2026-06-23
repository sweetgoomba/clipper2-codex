# Runtime And Environment

이 문서는 실행 모드, env 파일, port/runtime 기준의 현재 정책을 요약한다.

## Execution Modes

- `local`
  - browser 개발 실행.
  - `desktop/clipper_nestjs`, `desktop/clipper_python`의 `.env.local` 사용.
  - NestJS `WorkflowExecutor`가 Python plugin을 `LocalPluginHost`로 실행하거나 NestJS-native executor를 직접 실행한다.
- `devapp`
  - unpackaged Electron 개발 앱.
  - `desktop/clipper_nestjs`, `desktop/clipper_python`, `desktop/clipper_electron`의 `.env.devapp` 사용.
  - Electron 창은 띄우지만 Python plugin process는 기본적으로 NestJS `LocalPluginHost` 경로를 따른다.
- `packaged`
  - 설치형 앱.
  - packaged resource의 `.env.packaged`만 사용.
  - Python plugin process는 Electron bridge가 host하고, NestJS-native executor는 packaged NestJS process 안에서 실행된다.

## Hard Rules

- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>`에는 실제로 값이 있는 key만 둔다.
- optional blank placeholder를 real env 파일에 다시 넣지 않는다.
- OS별 env 파일을 만들지 않는다.
- plugin별 고정 포트는 사용하지 않는다. mode별 port range에서 runtime이 동적으로 할당한다.
- Python env에는 Naver/Kakao key를 두지 않는다. Dance member image search owner는 NestJS다.
- `.env.local`을 packaged에서 읽게 만들거나 복사하는 방식으로 WorkflowExecutor/PluginHost 문제를 해결하지 않는다.

## Plugin Runtime Lifecycle

2026-06-23 초기 구현 기준으로 `desktop/clipper_nestjs`는 heavy Python plugin을 exclusive group으로
묶어, 새 plugin 실행 전 같은 group의 idle peer runtime을 종료할 수 있다. 이 기능은 아직 실제 앱
runtime에서 최종 검증되지 않았다.

NestJS env keys:

```text
CLIPPER_PLUGIN_RUNTIME_EXCLUSIVE_GROUP=dance_highlight,dialog_highlight,clipper1_video_render
CLIPPER_PLUGIN_RUNTIME_IDLE_SHUTDOWN_MS=60000
CLIPPER_PLUGIN_RUNTIME_HEALTH_TIMEOUT_MS=800
```

정책 문서:

- [design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md)

## Current References

- [operations/env-runtime/records/2026/05/21-execution-env-mode-design.md](operations/env-runtime/records/2026/05/21-execution-env-mode-design.md)
- [operations/env-runtime/runbooks/execution-mode-runbook.md](operations/env-runtime/runbooks/execution-mode-runbook.md)
- [operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md](operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md)
- [operations/env-runtime/README.md](operations/env-runtime/README.md)
- [design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
