# Clipper Studio Checkpoint

작성일: 2026-05-05 18:37 KST

이 문서는 2026-05-05 세션 종료 시점의 Clipper Studio 인계용 checkpoint다.
2026-05-04 checkpoint를 대체해서 다음 세션에서 먼저 읽는다.

## 세션 로그 규칙

사용자가 다시 언급하지 않아도 다음 Codex 세션에서는 매 턴 session log를 작성한다.

- 경로: `.codex/session-logs/YYYY-MM-DD.log`
- rotation: 날짜별 파일을 기본으로 한다.
- 기록 범위: 사용자 입력, assistant가 사용자에게 출력한 설명, 실행한 명령어, 주요 실행 결과, 수정한 파일과 수정 목적, 구현/검증 결정 요약.
- 주의: hidden reasoning은 원문 그대로 기록하지 않고, 사용자가 검토 가능한 결정/근거 요약으로 기록한다.
- 루트에 `codex-session.log` 같은 단일 파일을 만들지 않는다.

## 한 줄 상태

Clipper Studio의 packaged Electron render path는 사용자가 직접 확인한 기준으로 정상이다. 새 DMG에서 `영상 만들기 / 최종 영상 / 준비됨` 상태가 표시됐고, `영상 만들기` 실행 후 MP4 생성, final preview, thumbnail/poster, render history/version, edit -> stale/rerender -> regenerated output 흐름이 모두 정상 동작했다.

## 최신 빌드

- 최신 DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- 생성 시각: `2026-05-05 15:32 KST`
- 크기: `150M`
- Node: `v22.22.2`
- npm: `10.9.7`
- 빌드 명령: `npm run build:app:mac:arm64`
- 빌드 경고:
  - `package.json` author 누락.
  - 기본 Electron icon 사용.
  - macOS signing certificate가 없어 code signing skipped.

## 이번 세션에서 확인된 핵심

1. 문서 기준 최신 상태를 재확인했다.
   - `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-04.md`
   - `.codex/implementation/NEXT_SESSION_PROMPT.md`
   - `.codex/implementation/TASKS.md`
   - `.codex/implementation/WORKLOG.md`
2. 다른 Mac mini에서 이어받은 상태를 고려해 Node/npm/dependency/build baseline을 확인했다.
3. dev/static NestJS smoke에서 render provider availability 오표시를 발견했다.
4. packaged Electron render E2E는 사용자가 직접 확인했고 정상이다.

## 수정한 문제

dev/static host에서는 `StaticPluginHost`가 Python plugin process를 spawn할 수 없는데도 `video.render.legacy_clipper1.python_worker`가 `available`로 표시됐다.
그 결과 UI는 render 가능 상태처럼 보이고, render start 후 job이 실패했다.

수정:

- `PluginHost.canStartProcesses()` 기본값을 `false`로 추가.
- `ElectronPluginHost.canStartProcesses()`는 `true`로 override.
- `LegacyClipper1PythonWorkerRenderProvider.describe()`를 async/host-aware로 변경.
  - Electron/process-owning host에서는 available 유지.
  - Static host에서는 `clipper1_video_render`가 이미 running일 때만 available.
  - Static host에서 worker가 stopped/unreachable이면 unavailable과 수동 시작 안내 note 반환.
- `VideoRenderProviderRegistry`가 async descriptor를 지원하도록 변경.
- unavailable provider는 자동 resolve/start 대상에서 제외.
- explicit unavailable provider start 요청은 job 생성 전에 거부.
- Angular render control은 실행 가능한 render provider가 없을 때 provider note를 표시.

## 검증

Dependency/build:

- `clipper_nestjs`: `npm install`, `npm run build` 성공.
- `clipper_angular`: `npm install`, `npm run build:electron -- --progress=false` 성공.
- `clipper_electron`: `npm install`, `npx tsc -p tsconfig.json`, `npm run build:app:mac:arm64` 성공.

dev/static API smoke:

- Clipper Studio project create 성공.
- draft job 성공.
- 수정 후 provider 상태:
  - `video.render.legacy_clipper1.dry_run`: `available`, `canRender=true`, `dryRun=true`.
  - `video.render.local_ffmpeg.basic`: `available`, `canRender=false`, `dryRun=false`.
  - `video.render.legacy_clipper1.python_worker`: `unavailable`, `canRender=true`, `dryRun=false`.
- 실행 가능한 non-dry-run provider는 없음.
- render start는 job을 만들지 않고 `No available video render provider can render recipe...`로 거부됨.
- `render-job-count = 0`.

Packaged Electron user QA:

- `영상 만들기 / 최종 영상 / 준비됨` 표시 확인.
- `영상 만들기` 버튼으로 MP4 생성 확인.
- final preview 표시 확인.
- thumbnail/poster 정상 확인.
- render history/version 정상 확인.
- edit 후 stale/rerender 흐름 정상 확인.
- 다시 만들기 후 regenerated output 정상 확인.

Packaged bundle string check:

- renderer bundle에 `renderUnavailableReason` 포함.
- packaged NestJS bundle에 `Static plugin host cannot spawn render worker processes.` 포함.
- packaged NestJS bundle에 `No available video render provider can render recipe` 포함.

## 현재 repo 상태

루트 `/Users/jina/project/adlight` 자체는 git repo가 아니다.

2026-05-05 18:37 KST 기준:

| repo | branch/status |
|---|---|
| `clipper_nestjs` | `feature/initial-scaffold...origin/feature/initial-scaffold`, modified files 있음 |
| `clipper_angular` | `feature/initial-scaffold...origin/feature/initial-scaffold`, modified files 있음 |
| `clipper_electron` | `feature/initial-scaffold...origin/feature/initial-scaffold`, `package-lock.json` modified |
| `clipper_python` | `feature/plugin-architecture...origin/feature/plugin-architecture`, clean |

Modified files:

`clipper_nestjs`:

- `package-lock.json`
- `src/plugins/electron-plugin-host.service.ts`
- `src/plugins/plugin-host.ts`
- `src/project-manifest/legacy-clipper1-python-worker-render-provider.ts`
- `src/project-manifest/video-render-jobs.service.ts`
- `src/project-manifest/video-render-provider-registry.ts`
- `src/project-manifest/video-render-provider.ts`
- `src/projects/projects.service.ts`

`clipper_angular`:

- `angular.json`
- `package-lock.json`
- `src/shell/projects/projects-detail-panel.component.html`
- `src/shell/projects/projects-detail-panel.component.ts`

`clipper_electron`:

- `package-lock.json`

`.codex`:

- `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-05.md`
- `.codex/implementation/NEXT_SESSION_PROMPT.md`
- `.codex/implementation/TASKS.md`
- `.codex/implementation/WORKLOG.md`
- `.codex/session-logs/2026-05-05.log`

Notes:

- `clipper_angular/angular.json`의 `analytics: false` 변경은 이번 구현 전부터 있던 local change다.
- 세 repo의 `package-lock.json` 변경은 `npm install` 재실행으로 생긴 npm metadata 변화다.
- 이번 세션에서는 commit하지 않았다.

## 현재 제품 상태

이제 Clipper Studio의 1차 vertical slice는 packaged app 기준으로 다음이 작동한다.

```text
prompt -> draft job -> asset preparation -> edit 일부 -> render job -> MP4/thumbnail -> final preview -> edit stale -> rerender version
```

여전히 "Clipper1 전체 편입 완료"는 아니다.
정확한 표현은 Clipper Studio workflow의 1차 vertical slice와 provider 교체 경계가 구현됐고, packaged render E2E smoke가 통과한 상태다.

## 남은 주요 문제

제품 품질을 위해 다음은 여전히 남아 있다.

1. 생성 영상 품질 QA
   - 자막 위치, 제목 overlay, image motion, BGM/TTS volume, thumbnail, 템플릿별 visual parity.
2. Production provider 연결
   - LLM/media search/image generation/TTS 실제 endpoint/env 설정.
   - timeout, quota, billing, fallback 정책 정리.
3. Clipper1 parity
   - legacy template/table/DB parity.
   - legacy `VideoService` video/GIF motion parity.
   - legacy workflow import/adapter.
4. 편집 UX 확장
   - 현재는 clip당 첫 subtitle 중심.
   - multi-subtitle timeline editor는 아직 없다.
   - story/script structure editor도 1차 수준이다.
5. Source ingest와 Clipper Studio create flow 결합
   - prompt-only 시작 흐름을 넘어 기존 source ingest와 더 자연스럽게 묶어야 한다.

## 다음 세션 추천 시작점

1. 이 문서를 먼저 읽는다.
2. `.codex/session-logs/YYYY-MM-DD.log`에 매 턴 session log를 남긴다.
3. `git status --short --branch`를 네 repo에서 다시 확인한다.
4. 사용자가 생성된 MP4를 보며 품질 피드백을 줬다면 그 피드백을 최우선으로 처리한다.
5. 피드백이 없으면 생성 영상 품질 QA를 시작한다.
   - 자막 위치.
   - 제목 overlay.
   - TTS/BGM 볼륨.
   - 이미지 motion.
   - Clipper1 template visual parity.
6. provider 추가/연결 작업은 반드시 capability provider adapter 뒤에 붙인다.
