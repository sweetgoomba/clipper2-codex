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
- `clipper_angular`에서 다음 작업을 완료하고 push했다.
  - Dance setup vertical scroll.
  - Dance member image selector centering.
  - Template Builder thumbnail skeleton component extraction.
  - Template Builder ffmpeg/ffprobe readiness gate.

## Next Work

1. `.codex` 구조 리팩토링을 계속 진행한다.
2. Windows packaged smoke에서 아래를 확인한다.
   - PowerToys `Command Palette` off 상태의 Windows build.
   - app boot, NestJS health, Template Builder families.
   - Dance member image candidates가 0개가 아닌지.
   - Template Builder ffmpeg/ffprobe consent/gate.
   - ffmpeg/ffprobe 설치 후 text preview artifact와 sample render.
   - Dance member image selection scroll/centering.
   - Template Builder thumbnail skeleton UX.

## Notes

- `.codex`는 이제 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
