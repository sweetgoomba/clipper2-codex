# Environment And Runtime

## 프로모션 브랜치 전용 로컬 환경 (2026-11-02)

[실행 주소·빈 DB·독립 앱·관리자 계정·시작/종료](records/2026/11/02-promotion-branch-isolated-local-runtime.md). API4340·Client4241·Admin4242·DB15438과 전용 local-api 앱이 실행 중이다. 다른 작업의3000/4202/기존 개발 앱/DB는 유지했다. 테스트 중인 환경을 임의 종료/초기화하지 않는다.


Execution mode, env file ownership, and runtime process boundaries are tracked here.

## Current Rules

- Modes are `local`, `devapp`, `packaged`.
- Each repo owns its own env files.
- packaged mode reads only packaged env resources.
- plugin port assignment is dynamic within mode-specific ranges.
- Electron is native adapter / packaged process host; NestJS is control plane.
- NestJS `WorkflowExecutor` dispatches workflow jobs. Python plugin process hosting still follows `PluginHost`; NestJS-native executors do not need plugin ports.

## Active References

- [records/2026/07/10-auth-runtime-env.md](records/2026/07/10-auth-runtime-env.md)
- [records/2026/07/10-dev-deploy-notes.md](records/2026/07/10-dev-deploy-notes.md)
- [records/2026/05/21-execution-env-mode-design.md](records/2026/05/21-execution-env-mode-design.md)
- [runbooks/execution-mode-runbook.md](runbooks/execution-mode-runbook.md)
- [records/2026/05/21-windows-dance-image-env-management-context.md](records/2026/05/21-windows-dance-image-env-management-context.md)
- [../../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](../../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)

## 병합 이력

- [2026-07-03 런타임 격리 1차 병합: 충돌·해결 판단·검증](records/2026/07/plugin-runtime-isolation-dev-merge-20260703.md)
- [같은 날의 사용자 검토·2차 병합 기록](../../records/sessions/2026/07/03.md)

1차 기록의 SHA와 재검토 제안은 당시 이력이다. 최신 실행 경계는 위 Current Rules와 후속 세션 기록을 따른다.
