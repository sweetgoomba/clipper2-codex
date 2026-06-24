# Plugin Runtime Memory Management Status

작성일: 2026-06-23

## Problem

여러 Python plugin/runtime을 연달아 실행하면 이전 runtime process가 계속 남아 메모리를
잡고 있을 수 있다. 사용자가 관찰한 증상은 Clipper2 앱 종료 또는 Chrome 같은 다른 앱 freeze다.

메모리 pressure 자체를 OS 수준에서 정확히 감지하는 구현은 아직 없다. 이번 세션의 1차 대응은
heavy Python plugin들을 exclusive group으로 묶고, 그 중 하나가 실행될 때 이미 떠 있는 같은
그룹의 idle plugin runtime을 종료하는 정책이다.

## Branch And Commits

현재 작업 브랜치:

```text
desktop/clipper_nestjs:   feature/plugin-runtime-memory-management
desktop/clipper_angular:  feature/plugin-runtime-memory-management
desktop/clipper_python:   feature/plugin-runtime-memory-management
desktop/clipper_electron: feature/plugin-runtime-memory-management
```

이번 세션 관련 커밋:

```text
clipper_nestjs:
  dded94b chore(template-builder): remove legacy template families and S3 storage
  a978ea7 feat(plugin-runtime): add Python runtime lifecycle policy
  fbf7b41 fix(plugin-runtime): gracefully stop local Python runtime
  ef1b23a fix(plugin-runtime): include TTS runtime in lifecycle policy

clipper_angular:
  652bc44 chore(template-builder): remove legacy template builder UI paths

clipper_python:
  84a1d44 chore(clipper1): remove legacy template assets

clipper_electron:
  e839aca feat(nest-manager): update data directory path for korean_artists.json to match bundle layout
  b18f424 fix(plugin-runtime): gracefully stop Electron-hosted Python runtime
```

`cleanup/remove-legacy-templates` worktree는 제거했다. cleanup branch는 원격에 남아 있고,
Angular/Python의 `feature/plugin-runtime-memory-management` 원격 브랜치는 cleanup 커밋까지
갱신되어 있다. NestJS의 `feature/plugin-runtime-memory-management` 원격 브랜치는
`a978ea7`까지 push되어 있다.

## Implemented In NestJS

파일:

```text
desktop/clipper_nestjs/.env.example
desktop/clipper_nestjs/src/modules/plugins/plugins.module.ts
desktop/clipper_nestjs/src/modules/workflows/index.ts
desktop/clipper_nestjs/src/modules/workflows/application/python-runtime-lifecycle-policy.service.ts
desktop/clipper_nestjs/src/modules/workflows/infrastructure/python-plugin-workflow-executor.ts
desktop/clipper_nestjs/test/python-runtime-lifecycle-policy.test.js
```

새 정책:

- `PythonRuntimeLifecyclePolicy`를 추가했다.
- Python workflow executor가 `start()`/`run()` 전에 pending idle stop을 취소하고
  `prepareForRun(pluginName)`을 호출한다.
- `run()` 완료/실패/취소 이후 `finally`에서 idle stop을 예약한다.
- exclusive group 안의 다른 plugin이 running 상태이고 `/health`가 `active_jobs: 0` 또는
  `activeJobs: 0`을 반환하면 `PluginHost.stop(pluginName)`으로 종료한다.
- manifest의 `resourceProfile.idlePolicy.safeToEvictWhenIdle === true`인 plugin만 종료 후보로 본다.
- health check 실패, non-200, active job 존재, safe-to-evict false이면 종료하지 않는다.
- NestJS DI는 `PYTHON_RUNTIME_LIFECYCLE_OPTIONS` token으로 env 기반 옵션을 주입한다.

환경 변수:

```text
CLIPPER_PLUGIN_RUNTIME_EXCLUSIVE_GROUP=dance_highlight,dialog_highlight,clipper1_video_render,tts_supertonic
CLIPPER_PLUGIN_RUNTIME_IDLE_SHUTDOWN_MS=60000
CLIPPER_PLUGIN_RUNTIME_HEALTH_TIMEOUT_MS=800
```

기본값:

- exclusive group: `dance_highlight,dialog_highlight,clipper1_video_render,tts_supertonic`
- idle shutdown delay: `60000ms`
- health timeout: `800ms`

2026-06-24 추가:

- actual sequential smoke에서 `tts_supertonic`이 default group 밖이면 heavy peer와 함께 남는 것을 확인했다.
- `tts_supertonic`은 manifest상 `safe_to_evict_when_idle=true`이고 Supertonic ONNX runtime을 로드하므로
  default exclusive group에 포함했다.
- `TtsPluginClient`는 workflow executor를 거치지 않으므로 synthesis 전 `prepareForRun()`,
  완료 후 `scheduleIdleStop()`을 직접 호출하도록 변경했다.

## Verification Performed

NestJS에서 fresh 검증:

```text
npm run build
node --test test/python-runtime-lifecycle-policy.test.js
node --test test/*.test.js
git diff --check
```

결과:

- `npm run build`: pass
- `test/python-runtime-lifecycle-policy.test.js`: 3/3 pass
- `test/*.test.js`: 148/148 pass
- `git diff --check`: pass

## 2026-06-24 Verification Addendum

완료한 actual smoke:

```text
local:    dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
devapp:   dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
packaged: dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
```

결과:

- `dance_highlight`, `dialog_highlight`, `tts_supertonic` model/runtime start 확인.
- `dance_highlight`, `dialog_highlight` job 중 `/health.active_jobs > 0` 관찰, 완료 후 `0` 확인.
- 각 다음 plugin start에서 이전 idle peer가 Python `/shutdown`으로 종료되고 `lastExitCode=0`.
- rebuilt packaged Electron mode에서도 bridge 경유 child process 종료 확인.

## Remaining Follow-up

남은 확인/구현 후보:

1. 실제 정상 영상 asset으로 full pipeline output까지 확인한다. 이번 smoke는 invalid mp4로 model load,
   active_jobs, peer eviction, process shutdown을 검증했다.
2. idle stop timer가 job 완료 후 너무 빨리/느리게 동작하지 않는지 사용성 관점에서 확인한다.
3. plugin 실행 중 cancel/error path에서도 idle cleanup이 안전한지 확인한다.
4. OS memory pressure 감지 또는 process RSS 기준 eviction이 필요한지 판단한다.
5. Angular UI에는 아직 runtime cleanup 상태나 memory pressure 표시가 없다. 필요 여부를 별도 판단한다.

## Next Session Start Prompt

다음 세션에서 그대로 사용할 시작문:

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 먼저 아래 repo들의 git status와 최신 커밋을 확인해줘.
- desktop/clipper_nestjs
- desktop/clipper_angular
- desktop/clipper_python
- desktop/clipper_electron
- .codex

그리고 아래 문서를 먼저 읽어줘.
- .codex/README.md
- .codex/handoff/NEXT.md
- .codex/design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md
- .codex/records/sessions/2026/06/23.md
- .codex/standards/GIT_COMMIT_MESSAGE_POLICY.md

현재 plugin/runtime memory management 작업은 완료가 아니라 초기 구현 상태야.
clipper_nestjs의 feature/plugin-runtime-memory-management 브랜치에
a978ea7 feat(plugin-runtime): add Python runtime lifecycle policy 가 올라가 있고,
Angular/Python에는 legacy template cleanup 커밋만 들어가 있어.
Electron에는 아직 이번 memory management 구현 커밋이 없어.

먼저 실제 local/devapp/packaged runtime에서 여러 plugin을 연달아 실행했을 때
idle peer process가 종료되는지, /health active_jobs가 정확한지, Electron packaged mode에서
PluginHost.stop()이 child process를 실제 종료하는지 확인해줘.
그 다음 부족한 Electron/Python/NestJS lifecycle 개선을 제안하고 구현해줘.

커밋 메시지는 반드시 Conventional Commit 형식(<type>(<scope>): <summary>)을 지켜줘.
```
