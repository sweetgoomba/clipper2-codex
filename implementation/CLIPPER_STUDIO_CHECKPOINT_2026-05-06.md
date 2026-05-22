# Clipper Studio Checkpoint

작성일: 2026-05-06 11:12 KST
최신 갱신: 2026-05-06 13:16 KST

이 문서는 2026-05-06 세션 종료 시점의 Clipper Studio 인계용 checkpoint다.
다음 세션에서는 이 문서를 먼저 읽고, 그 다음 `.codex/implementation/NEXT_SESSION_PROMPT.md`, `TASKS.md`, `WORKLOG.md`를 확인한다.

## 세션 로그 규칙

사용자가 다시 언급하지 않아도 다음 Codex 세션에서는 매 턴 session log를 작성한다.

- 경로: `.codex/session-logs/YYYY-MM-DD.log`
- 날짜별 파일로 누적한다.
- 기록 범위: 사용자 입력, assistant 출력 요약, 실행 명령어와 주요 결과, 수정한 파일과 수정 목적, 구현/검증 결정 요약.
- hidden reasoning은 원문이 아니라 검토 가능한 결정/근거 요약으로 기록한다.
- 루트에 `codex-session.log` 같은 단일 파일은 만들지 않는다.

## 한 줄 상태

Clipper Studio의 packaged Electron render path는 2026-05-05 사용자 QA 기준 정상이다. 2026-05-06 13:16 KST에는 생성 영상 품질 QA 중 BGM-only 볼륨 적용 문제를 `clipper_python`에서 수정했고, 해당 변경은 아직 커밋하지 않았다.

## 2026-05-06 13:16 추가 진행

- 생성 영상 품질 QA를 시작했다.
- `clipper1_video_render`의 BGM-only audio path에서 `bgm_volume`이 실제 ffmpeg 필터에 적용되지 않는 문제를 수정했다.
  - 기존 TTS+BGM 경로는 BGM 볼륨을 낮췄다.
  - TTS가 없는 BGM-only 프로젝트는 요약에만 `bgm_volume`이 표시되고 실제 BGM track은 원본 볼륨으로 들어갔다.
  - BGM track 생성 단계에서 `volume=<bgm_volume>,aresample=48000`을 적용하도록 변경했다.
  - TTS+BGM mix 경로는 이미 볼륨이 적용된 BGM track을 다시 낮추지 않도록 조정했다.
- 테스트:
  - `clipper_python`: `uv run pytest tests/test_clipper1_video_render_remote_assets.py` 성공, 6 passed.
- 미커밋 변경:
  - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - `clipper_python/tests/test_clipper1_video_render_remote_assets.py`

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

## 이번 세션에서 정리한 것

1. Superpowers 플러그인 사용 방식을 확인했다.
   - `SKILL.md`는 프로젝트 파일이 아니라 Codex 플러그인 캐시의 절차 문서다.
   - 프로젝트 상태 기록은 `.codex/session-logs/YYYY-MM-DD.log`에 남긴다.
2. 2026-05-05 checkpoint/NEXT_SESSION_PROMPT/TASKS/WORKLOG를 다시 읽고 상태를 확인했다.
3. 이전 세션의 변경사항을 커밋했다.
4. 남아 있던 `clipper_angular/angular.json`의 Angular analytics 비활성화 변경도 사용자 요청으로 커밋했다.

## 커밋된 변경

`clipper_nestjs`:

- `ee3c7cb fix: gate unavailable render providers`
  - Static host에서 Python worker를 spawn할 수 없는데 `video.render.legacy_clipper1.python_worker`가 available로 표시되던 문제 수정.
  - unavailable provider를 자동 resolve/start 대상에서 제외.
  - explicit unavailable provider start 요청은 job 생성 전에 거부.
- `531725b chore: refresh npm lock metadata`
  - 이전 `npm install` 실행으로 생긴 `package-lock.json` metadata 변경 반영.

`clipper_angular`:

- `d6f7560 fix: show render provider unavailable reason`
  - 실행 가능한 render provider가 없을 때 provider note/unavailable reason을 UI에 표시.
- `75351c5 chore: refresh npm lock metadata`
  - 이전 `npm install` 실행으로 생긴 `package-lock.json` metadata 변경 반영.
- `1ba755c chore: disable angular analytics`
  - `angular.json`에 `"analytics": false` 설정.

`clipper_electron`:

- `e44c8b7 chore: refresh npm lock metadata`
  - 이전 `npm install` 실행으로 생긴 `package-lock.json` metadata 변경 반영.

`clipper_python`:

- 새 커밋 없음.

## 검증

커밋 전 fresh 검증:

- `clipper_nestjs`: `npm run build` 성공.
- `clipper_angular`: `npm run build:electron -- --progress=false` 성공.
- `clipper_electron`: `npx tsc -p tsconfig.json` 성공.

`angular.json` 커밋 전 추가 검증:

- `clipper_angular`: `npm run build:electron -- --progress=false` 성공.

2026-05-05 packaged Electron 사용자 QA:

- `영상 만들기 / 최종 영상 / 준비됨` 표시 확인.
- `영상 만들기` 버튼으로 MP4 생성 확인.
- final preview 표시 확인.
- thumbnail/poster 정상 확인.
- render history/version 정상 확인.
- edit 후 stale/rerender 흐름 정상 확인.
- 다시 만들기 후 regenerated output 정상 확인.

## 현재 repo 상태

루트 `/Users/jina/project/adlight` 자체는 git repo가 아니다.

2026-05-06 13:16 KST 기준:

| repo | branch/status |
|---|---|
| `clipper_nestjs` | clean |
| `clipper_angular` | clean |
| `clipper_electron` | clean |
| `clipper_python` | modified: BGM-only volume fix and test |

## 현재 제품 상태

Clipper Studio의 1차 vertical slice는 packaged app 기준으로 다음이 작동한다.

```text
prompt -> draft job -> asset preparation -> edit 일부 -> render job -> MP4/thumbnail -> final preview -> edit stale -> rerender version
```

여전히 "Clipper1 전체 편입 완료"는 아니다.
정확한 표현은 Clipper Studio workflow의 1차 vertical slice와 provider 교체 경계가 구현됐고, packaged render E2E smoke가 통과한 상태다.

## 남은 주요 문제

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
