# Next Handoff

최신 갱신: 2026-05-26

이 문서는 다음 세션이 가장 먼저 읽는 압축 인계문이다. 긴 과거 인계는 [archive/2026/05/next-session-prompt-legacy.md](archive/2026/05/next-session-prompt-legacy.md)에 보관한다.

## 먼저 읽기

1. [../README.md](../README.md)
2. [../README.ARCHITECTURE.md](../README.ARCHITECTURE.md)
3. [../README.RUNTIME.md](../README.RUNTIME.md)
4. [../README.OPERATIONS.md](../README.OPERATIONS.md)
5. [../operations/env-runtime/README.md](../operations/env-runtime/README.md)
6. [../operations/windows-packaging/README.md](../operations/windows-packaging/README.md)
7. [../features/template-builder/README.md](../features/template-builder/README.md)
8. [../features/dance-highlight/README.md](../features/dance-highlight/README.md)
9. [../design/TEAM_ARCHITECTURE_OVERVIEW.md](../design/TEAM_ARCHITECTURE_OVERVIEW.md)
10. [../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
11. [../records/sessions/2026/05/26.md](../records/sessions/2026/05/26.md)

## Current Repo Heads

2026-05-26 세션 시작 시 직접 확인한 기준:

```text
clipper_nestjs:   feature/windows-packaging @ 9cd43f1 Trim optional env placeholders
clipper_electron: feature/windows-packaging @ f701677 Revert "Update electron builder"
clipper_angular:  feature/initial-scaffold  @ cad4b6c Gate template builder startup on ffmpeg readiness
clipper_python:   feature/windows-packaging @ 88d22c6 Trim optional env placeholders
clipper2-codex:   main @ 5aa515c Add technical analysis and architecture overview documents for Clipper2
```

세션 시작 시 반드시 각 repo에서 `git status -sb`와 `git log -1 --oneline`을 다시 확인한다.

2026-05-26 세션 종료 시 앱 코드 repo는 수정하지 않았다. `.codex` repo에는 handoff/session/worklog 문서 변경이 미커밋 상태로 남아 있다.

## Active Decisions

- 실행 모드는 `local`, `devapp`, `packaged`.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>` 파일에 optional blank placeholder를 넣지 않는다.
- plugin별 고정 포트는 사용하지 않는다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- Windows packaged build 중 PowerToys `Command Palette`를 끈다.
- `win.asar: false`, electron-builder retry, build script lock handling을 EBUSY 우회로 다시 넣지 않는다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.
- root `README.*.md`는 정해진 top-level guide만 둔다.
  - 현재 root README guide: `README.ARCHITECTURE.md`, `README.RUNTIME.md`, `README.FRONTEND.md`, `README.OPERATIONS.md`, `README.DOCS.md`.
  - 팀 설명용/심화 분석 문서는 `design/` 또는 domain folder 아래에 둔다.

## Last Completed Work

- `.codex`를 독립 git repo로 초기화하고 `sweetgoomba/clipper2-codex`에 연결했다.
- `.codex/imports/`는 legacy asset / DB backup 성격이라 git ignore 상태로 둔다.
- `.codex` 문서 구조 리팩토링을 완료했다.
  - root `README.*.md`를 architecture/runtime/frontend/operations/docs로 분리.
  - 활성 인계문을 `handoff/NEXT.md`로 축소.
  - 기존 긴 인계문은 `handoff/archive/2026/05/next-session-prompt-legacy.md`에 보관.
  - session logs는 `records/sessions/2026/05/`로 이동.
  - worklog는 `records/worklog/2026/05.md`로 이동.
  - Windows/env-runtime 문서는 `operations/` 하위로 이동.
  - Template Builder 문서는 `features/template-builder/` 하위로 이동.
- `clipper_angular`에서 다음 작업을 완료하고 push했다.
  - Dance setup vertical scroll.
  - Dance member image selector centering.
  - Template Builder thumbnail skeleton component extraction.
  - Template Builder ffmpeg/ffprobe readiness gate.
- 2026-05-26 문서화:
  - [../design/TEAM_ARCHITECTURE_OVERVIEW.md](../design/TEAM_ARCHITECTURE_OVERVIEW.md)를 추가했다.
    - Clipper2 전체 구조, repo별 책임, 실행 모드, feature 예시, 팀 설명 스크립트.
  - [../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)를 추가했다.
    - PluginHost, Electron bridge, Python PluginRuntime, job protocol, model install, resource assessment, port/concurrency, extension checklist.
  - 처음에는 root `README.*.md`로 만들었다가 규칙 위반이라 `design/` 아래로 이동했다.
  - [../README.ARCHITECTURE.md](../README.ARCHITECTURE.md)에 두 design 문서를 primary reference로 연결했다.
  - [../records/sessions/2026/05/26.md](../records/sessions/2026/05/26.md)와 [../records/worklog/2026/05.md](../records/worklog/2026/05.md)를 갱신했다.

## Next Work

1. 세션 시작 시 `.codex`와 네 앱 repo의 `git status -sb`, `git log -1 --oneline`을 확인한다.
2. `.codex` 문서 변경 diff를 확인한다.
   - root `README.*.md` 목록이 정해진 guide만 유지되는지 확인.
   - 새 문서가 `design/TEAM_ARCHITECTURE_OVERVIEW.md`, `design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`에 있는지 확인.
   - 필요하면 `.codex` 문서 변경을 commit/push한다.
3. Windows packaged smoke에서 아래를 확인한다.
   - PowerToys `Command Palette` off 상태의 Windows build.
   - app boot, NestJS health, Template Builder families.
   - Dance member image candidates가 0개가 아닌지.
   - Template Builder ffmpeg/ffprobe consent/gate.
   - ffmpeg/ffprobe 설치 후 text preview artifact와 sample render.
   - Dance member image selection scroll/centering.
   - Template Builder thumbnail skeleton UX.
4. smoke 결과를 `operations/windows-packaging/records/2026/05/` 또는 새 월 폴더에 기록한다.

## Next Session Prompt

```text
Using Superpowers.

먼저 `/Users/jina/project/adlight/.codex`가 별도 git repo라는 점을 기준으로 아래 문서를 순서대로 읽고 현재 상태를 파악해줘.

1. `.codex/README.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/README.ARCHITECTURE.md`
4. `.codex/README.RUNTIME.md`
5. `.codex/README.OPERATIONS.md`
6. `.codex/operations/env-runtime/README.md`
7. `.codex/operations/windows-packaging/README.md`
8. `.codex/features/template-builder/README.md`
9. `.codex/features/dance-highlight/README.md`
10. `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`
11. `.codex/design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
12. `.codex/records/sessions/2026/05/26.md`

현재 목표:
- 2026-05-21에 정리한 `local` / `devapp` / `packaged` env/runtime 구조를 기준으로 이어서 작업한다.
- Windows packaged build는 PowerToys `Command Palette` 때문에 `EBUSY`가 났던 것이며, Clipper2 코드 문제로 보지 않는다.
- `win.asar: false`, electron-builder retry, build script lock handling 같은 우회는 다시 넣지 않는다.
- Windows build 중에는 PowerToys `Command Palette`를 끈다. `Keyboard Manager`는 사용해도 된다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.
- root `README.*.md`에는 정해진 top-level guide만 둔다. 팀 설명용/심화 분석 문서는 `design/` 또는 domain folder 아래에 둔다.

현재 repo HEAD는 세션 시작 시 직접 `git status -sb`와 `git log -1 --oneline`으로 재확인한다.

다음에 할 일:
1. `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python` 상태를 확인한다.
2. `.codex` 문서 변경 diff를 확인한다.
   - 새 문서는 `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`, `.codex/design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`에 있어야 한다.
   - root `README.*.md`에는 `README.ARCHITECTURE.md`, `README.RUNTIME.md`, `README.FRONTEND.md`, `README.OPERATIONS.md`, `README.DOCS.md`만 있어야 한다.
   - 필요하면 `.codex` 문서 변경을 commit/push한다.
3. Windows PC에서 최신 commit pull, secret `.env.*` 파일 존재 확인, PowerToys `Command Palette` off 상태로 Windows packaged build를 실행한다.
4. installer 생성 후 packaged app smoke를 진행한다.
5. 특히 아래를 확인한다.
   - app boot / NestJS health / Template Builder families load
   - Dance member image 후보가 0개가 아니라 실제로 반환되는지
   - Template Builder ffmpeg/ffprobe consent/gate가 먼저 동작하는지
   - ffmpeg/ffprobe 설치 완료 후 text preview artifact와 sample render가 정상 동작하는지
   - Dance member image selection 스크롤/중앙 정렬
   - Template Builder thumbnail skeleton UX
6. smoke 결과를 `.codex/operations/windows-packaging/records/`에 문서화하고 `.codex` repo에 commit/push한다.

주의:
- `.codex`는 별도 git repo이므로 문서 변경은 `.codex`에서 따로 commit/push한다.
- `.codex/imports/`는 ignored 상태로 유지한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경을 같은 커밋에 섞지 않는다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- 실제 `.env.<mode>` 파일에 optional blank placeholder를 다시 넣지 않는다.
```

## Notes

- `.codex`는 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
- root `README.*.md`를 새로 늘리지 않는다. cross-cutting design 문서는 `design/`, feature 문서는 `features/<feature>/`, operations 문서는 `operations/<domain>/` 아래에 둔다.
