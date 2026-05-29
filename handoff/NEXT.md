# Next Handoff

최신 갱신: 2026-05-29

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
10. [../design/TEAM_DEVELOPMENT_GUIDE.md](../design/TEAM_DEVELOPMENT_GUIDE.md)
11. [../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
12. [../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
13. [../records/sessions/2026/05/29.md](../records/sessions/2026/05/29.md)
14. [../records/sessions/2026/05/27.md](../records/sessions/2026/05/27.md)

## Current Repo Heads

2026-05-29 세션에서 직접 확인하고 main 브랜치로 모은 로컬 기준:

```text
clipper_angular:  main @ 70d6e58 Improve template sample render flow
clipper_nestjs:   main @ 73c2519 Stage template sample media
clipper_python:   main @ 535131c Render sample images as cover
clipper_electron: main @ f701677 Revert "Update electron builder"
clipper2-codex:   main @ this handoff/session documentation commit; check `git log -1 --oneline`
```

세션 시작 시 반드시 각 repo에서 `git status -sb`와 `git log -1 --oneline`을 다시 확인한다. `.codex`는 별도 git repo다.

### Main Branch Consolidation Notes

- `clipper_nestjs`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 3커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_electron`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 1커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_angular`
  - 로컬 `main`을 `feature/initial-scaffold`에서 생성했다.
  - 현재 `main`과 `feature/initial-scaffold`는 같은 commit이다.
- `clipper_python`
  - 기존 `main`은 `origin/main`의 `1e94974 Initial commit`에 머물러 있었다.
  - 로컬 `main`을 `feature/windows-packaging`까지 fast-forward했다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이고, `feature/plugin-architecture` 변경도 포함한다.
  - 그래서 `git status -sb`는 `main...origin/main [ahead 103]`로 보인다.
  - 이 `ahead 103`은 미커밋 변경이나 파일 103개가 아니라, `origin/main..main` 범위의 103개 commit이다.
  - Sync/push하면 그동안 feature 브랜치에 쌓인 Python plugin architecture, render worker, Template Builder fixture/render, env/windows packaging 관련 이력이 `origin/main`으로 올라간다.

## Active Decisions

- 실행 모드는 `local`, `devapp`, `packaged`.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>` 파일에 optional blank placeholder를 넣지 않는다.
- plugin별 고정 포트는 사용하지 않는다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- Windows packaged build 중 PowerToys `Command Palette`를 끈다.
- `win.asar: false`, electron-builder retry, build script lock handling을 EBUSY 우회로 다시 넣지 않는다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.
- Template Builder sample render는 Angular 버튼/UI, NestJS recipe/assets, Python ffmpeg renderer가 함께 동작한다.
- 샘플 렌더의 콘텐츠 이미지는 콘텐츠 영역을 `cover` 방식으로 꽉 채운다. 빈 여백을 만들지 않고 넘친 부분을 중앙 crop한다.
- root `README.*.md`는 정해진 top-level guide만 둔다.
  - 현재 root README guide: `README.ARCHITECTURE.md`, `README.RUNTIME.md`, `README.FRONTEND.md`, `README.OPERATIONS.md`, `README.DOCS.md`.
  - 팀 설명용/심화 분석 문서는 `design/` 또는 domain folder 아래에 둔다.

## Last Completed Work

- 팀원 온보딩/Notion import용 개발 가이드를 추가했다.
  - `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
  - 구조, repo별 책임, `local`/`devapp`/`packaged` 실행 방법, branch 운영, env 첨부 섹션을 한 문서에 정리했다.
  - 명령어는 팀원이 각자 `PROJECT_ROOT`를 지정해 실행할 수 있게 작성했다.
- NestJS-native workflow도 Plugin Store/job history/start-stop 모델에 통합하기 위한 설계를 추가했다.
  - `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
  - 현재 Python runtime plugin 중심 구조의 한계를 정리했다.
  - `WorkflowExecutor`, executor registry, Python adapter, NestJS-native ffmpeg executor 방향을 정의했다.
  - 작업 브랜치:
    - `.codex`: `workflow-executor-design`
    - `clipper_nestjs`: `design/workflow-executor`
- `clipper_nestjs` `design/workflow-executor`에서 WorkflowExecutor 초기 구현을 진행했다.
  - commit: `ceaa6ab Add workflow executor runtime dispatch`
  - `src/workflows/`에 executor interface, registry, Python adapter, virtual workflow executor, `simple_ffmpeg_transform` NestJS-native executor를 추가했다.
  - `JobsService`는 `PluginHost` 직접 호출 대신 `WorkflowExecutorRegistry`로 dispatch한다.
  - `PluginsService`는 Python, NestJS-native, virtual workflow를 registry 기반 list/status/start/stop으로 통합한다.
  - `PluginManifestView.runtimeKind`를 추가하고 기존 catalog/local manifests에 runtime kind를 명시했다.
  - 검증:
    - `clipper_nestjs npm run build`: passed.
    - `clipper_nestjs npm run bundle`: passed.
    - `clipper_nestjs node --test test/workflow-executor-registry.test.js`: passed (`2 passed`).
    - `simple_ffmpeg_transform` direct executor start smoke: passed locally with `runtimeState=running`.
    - `clipper_nestjs git diff --check`: passed.
- WorkflowExecutor 기준을 기존 아키텍처 문서들에도 반영했다.
  - `README.ARCHITECTURE.md`, `README.RUNTIME.md`
  - `design/TEAM_ARCHITECTURE_OVERVIEW.md`
  - `design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
  - `design/TEAM_DEVELOPMENT_GUIDE.md`
  - `design/BACKEND_ROLE_SPLIT_CURRENT.md`
  - `design/NESTJS_CONTROL_PLANE_REDESIGN.md`
  - `design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
  - `design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
  - `design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
  - `design/CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`
  - `design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
  - `operations/env-runtime/README.md`
- 로컬 앱 repo의 최종 작업 상태를 `main` 브랜치로 모았다.
  - 코드 내용은 새로 수정하지 않았다.
  - `clipper_nestjs`, `clipper_electron`, `clipper_angular`는 없던 로컬 `main`을 생성했다.
  - `clipper_python`은 기존 로컬 `main`을 `feature/windows-packaging`로 fast-forward했다.
  - branch 포함 관계 확인:
    - `clipper_nestjs`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_electron`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_python`: `feature/windows-packaging`가 `feature/plugin-architecture`와 기존 `main`을 포함.
  - 원격에는 아직 push하지 않았다.
- Template Builder sample render UX와 렌더 동작을 수정했다.
  - `clipper_angular` `70d6e58 Improve template sample render flow`
    - 상단 `샘플 렌더` 버튼은 결과 화면을 여는 역할만 한다.
    - 실제 최초 렌더/재렌더는 화면 안의 `렌더 시작` 버튼이 담당한다.
    - 샘플 렌더 화면에는 "이 화면을 닫아도 진행 중인 샘플 렌더는 계속 진행됩니다." 안내를 둔다.
    - 샘플 렌더는 가능한 네 비율을 모두 순차 렌더한다.
    - 플레이어는 shorts 비율로 표시한다.
    - 샘플 렌더 UI를 inspector에서 page header/overlay로 이동했다.
    - 편집 저장 시 사용자 템플릿 카드 썸네일은 저장 당시 선택 ratio를 사용한다.
    - 공식 템플릿 등록 직전에는 4:3 기준 카드 썸네일을 다시 생성한다.
  - `clipper_nestjs` `73c2519 Stage template sample media`
    - 샘플 렌더용 기본 콘텐츠 이미지를 `src/projects/assets/template-builder/sample-media.jpg`로 stage한다.
    - 해당 파일이 없으면 기존 generated PNG fallback을 쓴다.
    - 단색 `layoutImage`도 render layout layer로 전달해 content 영역 밖 흰 배경 문제를 보정했다.
  - `clipper_python` `535131c Render sample images as cover`
    - `effects: [{ type: "none" }]`을 실제로 존중해 자동 팬/줌을 끈다.
    - 샘플/정지 이미지 기본 렌더를 `contain + pad`가 아니라 `cover + crop`으로 변경했다.
    - 콘텐츠 영역을 꽉 채우고 넘친 부분은 중앙 crop한다.
- 검증:
  - `clipper_angular`: targeted tests `220 SUCCESS`, page-only `60 SUCCESS`, `npm run build` passed, `git diff --check` passed.
  - `clipper_nestjs`: `npm run build` passed, render payload targeted tests passed, sample render targeted tests passed, `git diff --check` passed.
  - `clipper_python`: `uv run pytest tests/test_clipper1_video_render_media_looping.py -q` passed (`27 passed`), `git diff --check` passed.
- main branch consolidation 직후 앱 코드 repo는 위 커밋들까지 clean 상태였다. 이후 `clipper_nestjs` `design/workflow-executor`의 WorkflowExecutor 구현은 `ceaa6ab`로 커밋 완료했다.

## Next Work

1. 세션 시작 시 `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python`의 `git status -sb`, `git log -1 --oneline`을 확인한다.
2. 현재 작업 branch 상태를 먼저 정리한다.
   - `.codex`: `workflow-executor-design`, 이번 문서 커밋 이후 clean이어야 한다.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인:
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
   - 필요한 경우 Angular Plugin Store/job start UI에서 `runtimeKind` 표시/버튼 정책 연결.
4. 앱 repo의 로컬 `main`을 remote에 push할지 사용자에게 확인하거나, 사용자가 요청하면 repo별로 push한다.
   - 특히 `clipper_python`은 `origin/main`이 오래된 초기 commit이라 `main...origin/main [ahead 103]`로 보인다.
   - 이는 feature 개발 이력 103개 commit을 `origin/main`에 올릴 준비가 된 상태다.
5. Template Builder sample render smoke를 다시 할 경우 아래를 확인한다.
   - 새 템플릿 생성 후 단색/이미지 layout 변경 저장.
   - 샘플 렌더 화면 열기와 `렌더 시작`.
   - 네 비율 모두 생성.
   - 콘텐츠 이미지가 각 ratio의 content area를 빈 여백 없이 꽉 채우는지.
   - content area 밖 layout image 또는 단색 background가 흰색으로 빠지지 않는지.
   - 화면을 닫아도 렌더 진행이 계속되는지.
   - 공식 템플릿 등록 후 카드 썸네일이 4:3 기준인지.
6. Windows packaged smoke가 필요하면 기존 운영 문서 기준을 따른다.
   - PowerToys `Command Palette` off.
   - `.env.local` packaged read/copy 금지.
   - plugin별 env port 나열 금지.

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
11. `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
12. `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
13. `.codex/design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
14. `.codex/records/sessions/2026/05/29.md`
15. `.codex/records/sessions/2026/05/27.md`

현재 repo HEAD는 세션 시작 시 직접 `git status -sb`와 `git log -1 --oneline`으로 재확인한다.

현재 기준:
- `clipper_angular`: `main @ 70d6e58 Improve template sample render flow`
- `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`
- `clipper_python`: `main @ 535131c Render sample images as cover`
- `clipper_electron`: `main @ f701677 Revert "Update electron builder"`
- `.codex`: `workflow-executor-design`, this documentation commit

다음에 할 일:
1. `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python` 상태를 확인한다.
2. WorkflowExecutor 작업 branch들을 먼저 확인한다.
   - `.codex`: `workflow-executor-design`, clean after this documentation commit.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인을 진행한다.
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
4. 사용자가 요청하면 로컬 main들을 repo별로 push한다.
   - `clipper_python`의 `main...origin/main [ahead 103]`은 origin/main이 초기 commit에 머물러 있었기 때문에 보이는 commit count다.
   - 미커밋 변경이나 파일 103개가 아니다.
5. Template Builder sample render 관련 후속 버그가 입력되면 아래 전제를 유지한다.
   - 샘플 렌더 UI는 Angular, recipe/assets는 NestJS, 실제 MP4 합성은 Python renderer가 담당한다.
   - 샘플 이미지는 콘텐츠 영역을 `cover + center crop`으로 꽉 채워야 한다.
   - layout image/단색 background는 content area 밖에서 흰색으로 빠지면 안 된다.
   - 공식 등록 전 카드 썸네일은 4:3 기준이어야 한다.
6. 새 분석 문서는 `.codex/design/` 아래에 둔다.

주의:
- `.codex`는 별도 git repo다.
- 앱 코드 repo 변경과 `.codex` 문서 변경을 같은 커밋에 섞지 않는다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- Windows build 중 PowerToys `Command Palette`를 끈다.
```

## Notes

- `.codex`는 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
- root `README.*.md`를 새로 늘리지 않는다. cross-cutting design 문서는 `design/`, feature 문서는 `features/<feature>/`, operations 문서는 `operations/<domain>/` 아래에 둔다.
