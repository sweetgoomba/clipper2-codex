# Environment And Runtime

Execution mode, env file ownership, and runtime process boundaries are tracked here.

## Current Rules

- Modes are `local`, `devapp`, `packaged`.
- Each repo owns its own env files.
- packaged mode reads only packaged env resources.
- plugin port assignment is dynamic within mode-specific ranges.
- Electron is native adapter / packaged process host; NestJS is control plane.

## Active References

- [../../design/2026-05-21-execution-env-mode-design.md](../../design/2026-05-21-execution-env-mode-design.md)
- [../../implementation/2026-05-21-execution-mode-runbook.md](../../implementation/2026-05-21-execution-mode-runbook.md)
- [../../implementation/2026-05-21-windows-dance-image-env-management-context.md](../../implementation/2026-05-21-windows-dance-image-env-management-context.md)
