# Runtime And Environment

이 문서는 실행 모드, env 파일, port/runtime 기준의 현재 정책을 요약한다.

## Execution Modes

- `local`
  - browser 개발 실행.
  - 각 repo의 `.env.local` 사용.
- `devapp`
  - unpackaged Electron 개발 앱.
  - 각 repo의 `.env.devapp` 사용.
- `packaged`
  - 설치형 앱.
  - packaged resource의 `.env.packaged`만 사용.

## Hard Rules

- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>`에는 실제로 값이 있는 key만 둔다.
- optional blank placeholder를 real env 파일에 다시 넣지 않는다.
- OS별 env 파일을 만들지 않는다.
- plugin별 고정 포트는 사용하지 않는다. mode별 port range에서 runtime이 동적으로 할당한다.
- Python env에는 Naver/Kakao key를 두지 않는다. Dance member image search owner는 NestJS다.

## Current References

- [operations/env-runtime/records/2026/05/21-execution-env-mode-design.md](operations/env-runtime/records/2026/05/21-execution-env-mode-design.md)
- [operations/env-runtime/runbooks/execution-mode-runbook.md](operations/env-runtime/runbooks/execution-mode-runbook.md)
- [operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md](operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md)
- [operations/env-runtime/README.md](operations/env-runtime/README.md)
