# Environment And Runtime

Execution mode, env file ownership, and runtime process boundaries are tracked here.

## Current Rules

- Modes are `local`, `devapp`, `packaged`.
- Each repo owns its own env files.
- packaged mode reads only packaged env resources.
- plugin port assignment is dynamic within mode-specific ranges.
- Electron is native adapter / packaged process host; NestJS is control plane.
- NestJS `WorkflowExecutor` dispatches workflow jobs. Python plugin process hosting still follows `PluginHost`; NestJS-native executors do not need plugin ports.

## Active References

- [records/2026/05/21-execution-env-mode-design.md](records/2026/05/21-execution-env-mode-design.md)
- [runbooks/execution-mode-runbook.md](runbooks/execution-mode-runbook.md)
- [records/2026/05/21-windows-dance-image-env-management-context.md](records/2026/05/21-windows-dance-image-env-management-context.md)
- [../../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](../../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
