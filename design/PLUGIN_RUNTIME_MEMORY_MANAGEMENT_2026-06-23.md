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
  11979f3 fix(plugin-runtime): retry idle stop after active jobs finish
  a5a6003 feat(plugin-runtime): expose lifecycle diagnostics and pressure cleanup
  a2efd95 fix(plugin-runtime): stop managed runtime on cancelled jobs

clipper_angular:
  652bc44 chore(template-builder): remove legacy template builder UI paths
  1460727 feat(plugin-runtime): show lifecycle diagnostics on dashboard
  3d4c231 test(template-builder): align specs with current ratios

clipper_python:
  84a1d44 chore(clipper1): remove legacy template assets

clipper_electron:
  e839aca feat(nest-manager): update data directory path for korean_artists.json to match bundle layout
  b18f424 fix(plugin-runtime): gracefully stop Electron-hosted Python runtime
  abafc4c test(electron): run node tests with file globs
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

정상 영상 full pipeline output smoke:

```text
input:
  dance_highlight: YouTube CHp0Kaidr14 -> /tmp/clipper-youtube-real-input/CHp0Kaidr14.mp4
  dialog_highlight: YouTube ulQr-_f3DG8 -> /tmp/clipper-youtube-real-input/ulQr-_f3DG8.mp4

command:
  CLIPPER_E2E_OUTPUT_ROOT=/tmp/clipper-youtube-real-output-with-llm
  uv run --extra test pytest tests/e2e/test_real_pipeline.py -v -s

result:
  2 passed in 242.54s
```

- `dialog_highlight` output: `/tmp/clipper-youtube-real-output-with-llm/dialog/json/manifest.json`.
- `dance_highlight` output: `/tmp/clipper-youtube-real-output-with-llm/dance/json/dance_meta.json` and montage mp4 files.

packaged normal-video memory lifecycle probe:

```text
app:
  dist-app/mac-arm64/Clipper2.app/Contents/MacOS/Clipper2

sequence:
  cycle 1: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate
  cycle 2: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate

result:
  completed=6
  failures=0
  max plugin process count=1
  final plugin process count=0
  max sampled relevant RSS=3386 MB
```

- `dance_highlight` PIDs `82940`, `86976`; max sampled RSS `2996 MB`; `/health.active_jobs` observed `1 -> 0`.
- `dialog_highlight` PIDs `84373`, `88382`; max sampled RSS `1553 MB`; `/health.active_jobs` observed `1 -> 0`.
- `tts_supertonic` PIDs `86854`, `90612`; max sampled RSS `562 MB`.
- All observed peer evictions exited with `lastExitCode=0`.
- Summary JSON: `/tmp/clipper-packaged-memory-probe-2026-06-24T04-02-46-162Z/memory-probe-summary.json`.

## 2026-06-24 Final Verification Addendum

`a2efd95` 이후 cancel path에서 NestJS job cancel이 Python worker를 즉시 정리하도록 보강했다.
host-owned packaged/local/devapp runtime이고 manifest가 `safeToEvictWhenIdle=true`일 때만 stop하며,
external/static runtime host는 stop하지 않는다.

최신 packaged cancel/error/idle probe:

```text
app API:
  http://127.0.0.1:51660/v1
summary:
  /tmp/clipper-packaged-cancel-error-idle-2026-06-24T05-44-04-496Z/cancel-error-idle-summary.json
result:
  completed=3
  failures=0
  TTS reused PID 4968 inside the 30s idle window and then stopped after the idle window
  dance cancel observed active_jobs=1 before cancel
  after DELETE, dance_highlight was already stopped
  observedActiveAfterCancel=null
  stoppedWithin100s=true
```

최신 packaged normal-video memory lifecycle probe:

```text
app API:
  http://127.0.0.1:51660/v1
summary:
  /tmp/clipper-packaged-memory-probe-2026-06-24T05-46-03-415Z/memory-probe-summary.json
sequence:
  cycle 1: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate
  cycle 2: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate
result:
  completed=6
  failures=0
  sampleCount=81
  max plugin process count=1
  final running plugins=none
  final plugin process count=0
  max sampled relevant RSS=2833 MB
  max sampled plugin RSS:
    dance_highlight=2462 MB
    dialog_highlight=1543 MB
    tts_supertonic=563 MB
  active job values stayed within expected 0/1 samples
```

Angular TemplateBuilder follow-up:

```text
commit:
  3d4c231 test(template-builder): align specs with current ratios
reason:
  full Karma failures were stale expectations from the current ratio policy
  TEMPLATE_BUILDER_RATIOS = 16:9, 4:3, 1:1
  SHORTFORM_TEMPLATE_BUILDER_RATIOS = 1:1, 4:3
verification:
  Node v22.22.2
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless
  TOTAL: 638 SUCCESS
```

After packaged app shutdown, no `Clipper2`, `dance_highlight`, `dialog_highlight`,
`tts_supertonic`, or `clipper1_video_render` process remained.

## Remaining Follow-up

현재 요청된 lifecycle/cancel/TemplateBuilder verification 범위에서 별도 남은 follow-up은 없다.
다만 제품 hardening 관점에서 아래 항목은 추후 필요할 때 다시 판단한다.

1. idle stop timer가 실제 사용자 워크플로에서 너무 빠르거나 느린지 장시간 사용성 관점에서 조정한다.
2. OS memory pressure/RSS 기반 eviction threshold를 더 공격적으로 둘지 별도 제품 기준으로 판단한다.
3. Dashboard UI에 현재 diagnostics보다 더 많은 memory trend/history를 보여줄지 사용자 요구가 생기면 재검토한다.

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
