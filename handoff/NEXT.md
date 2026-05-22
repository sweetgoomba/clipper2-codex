# Next Handoff

최신 갱신: 2026-05-22

이 문서는 다음 세션이 가장 먼저 읽는 압축 인계문이다. 긴 과거 인계는 [archive/2026/05/next-session-prompt-legacy.md](archive/2026/05/next-session-prompt-legacy.md)에 보관한다.

## 먼저 읽기

1. [../README.md](../README.md)
2. [../README.RUNTIME.md](../README.RUNTIME.md)
3. [../README.OPERATIONS.md](../README.OPERATIONS.md)
4. [../operations/env-runtime/README.md](../operations/env-runtime/README.md)
5. [../operations/windows-packaging/README.md](../operations/windows-packaging/README.md)
6. [../features/template-builder/README.md](../features/template-builder/README.md)
7. [../features/dance-highlight/README.md](../features/dance-highlight/README.md)
8. [../features/template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](../features/template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)

## Current Repo Heads

마지막 확인 기준:

```text
clipper_nestjs:   feature/windows-packaging @ 9cd43f1 Trim optional env placeholders
clipper_electron: feature/windows-packaging @ f701677 Revert "Update electron builder"
clipper_angular:  feature/initial-scaffold  @ cad4b6c Gate template builder startup on ffmpeg readiness
clipper_python:   feature/windows-packaging @ 88d22c6 Trim optional env placeholders
clipper2-codex:   main @ current
```

세션 시작 시 반드시 각 repo에서 `git status -sb`를 다시 확인한다.

## Active Decisions

- 실행 모드는 `local`, `devapp`, `packaged`.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>` 파일에 optional blank placeholder를 넣지 않는다.
- plugin별 고정 포트는 사용하지 않는다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- Windows packaged build 중 PowerToys `Command Palette`를 끈다.
- `win.asar: false`, electron-builder retry, build script lock handling을 EBUSY 우회로 다시 넣지 않는다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.

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

## Next Work

1. 세션 시작 시 `.codex`와 네 앱 repo의 `git status -sb`를 확인한다.
2. Windows packaged smoke에서 아래를 확인한다.
   - PowerToys `Command Palette` off 상태의 Windows build.
   - app boot, NestJS health, Template Builder families.
   - Dance member image candidates가 0개가 아닌지.
   - Template Builder ffmpeg/ffprobe consent/gate.
   - ffmpeg/ffprobe 설치 후 text preview artifact와 sample render.
   - Dance member image selection scroll/centering.
   - Template Builder thumbnail skeleton UX.
3. smoke 결과를 `operations/windows-packaging/records/2026/05/` 또는 새 월 폴더에 기록한다.

## Next Session Prompt

```text
Using Superpowers.

먼저 `/Users/jina/project/adlight/.codex`가 별도 git repo라는 점을 기준으로 아래 문서를 순서대로 읽고 현재 상태를 파악해줘.

1. `.codex/README.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/README.RUNTIME.md`
4. `.codex/README.OPERATIONS.md`
5. `.codex/operations/env-runtime/README.md`
6. `.codex/operations/windows-packaging/README.md`
7. `.codex/features/template-builder/README.md`
8. `.codex/features/dance-highlight/README.md`

현재 목표:
- 2026-05-21에 정리한 `local` / `devapp` / `packaged` env/runtime 구조를 기준으로 이어서 작업한다.
- Windows packaged build는 PowerToys `Command Palette` 때문에 `EBUSY`가 났던 것이며, Clipper2 코드 문제로 보지 않는다.
- `win.asar: false`, electron-builder retry, build script lock handling 같은 우회는 다시 넣지 않는다.
- Windows build 중에는 PowerToys `Command Palette`를 끈다. `Keyboard Manager`는 사용해도 된다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.

현재 repo HEAD는 세션 시작 시 직접 `git status -sb`와 `git log -1 --oneline`으로 재확인한다.

다음에 할 일:
1. `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python` 상태를 확인한다.
2. Windows PC에서 최신 commit pull, secret `.env.*` 파일 존재 확인, PowerToys `Command Palette` off 상태로 Windows packaged build를 실행한다.
3. installer 생성 후 packaged app smoke를 진행한다.
4. 특히 아래를 확인한다.
   - app boot / NestJS health / Template Builder families load
   - Dance member image 후보가 0개가 아니라 실제로 반환되는지
   - Template Builder ffmpeg/ffprobe consent/gate가 먼저 동작하는지
   - ffmpeg/ffprobe 설치 완료 후 text preview artifact와 sample render가 정상 동작하는지
   - Dance member image selection 스크롤/중앙 정렬
   - Template Builder thumbnail skeleton UX
5. smoke 결과를 `.codex/operations/windows-packaging/records/`에 문서화하고 `.codex` repo에 commit/push한다.

주의:
- `.codex`는 이제 별도 git repo이므로 문서 변경은 `.codex`에서 따로 commit/push한다.
- `.codex/imports/`는 ignored 상태로 유지한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경을 같은 커밋에 섞지 않는다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- 실제 `.env.<mode>` 파일에 optional blank placeholder를 다시 넣지 않는다.
```

## Notes

- `.codex`는 이제 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
