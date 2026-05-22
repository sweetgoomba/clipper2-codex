# Clipper Studio Checkpoint

작성일: 2026-05-04 21:13 KST

이 문서는 사용자가 직접 빌드된 앱을 확인하고 다음 방향을 다시 정리하기 위한 checkpoint다.
현재 상태를 "Clipper1 편입 완료"로 표현하지 않는다. 정확한 상태는 Clipper Studio workflow의 1차 vertical slice와 provider 교체 경계가 구현된 상태다.

## 한 줄 상태

Clipper Studio는 이제 prompt -> draft -> asset 준비 -> 편집 일부 -> render job -> MP4 artifact까지 이어진다. 하지만 production provider endpoint, Clipper1 parity, 편집 UX, render 품질 검증이 아직 부족해서 제품적으로는 재설계/검토가 필요한 단계다.

## 최신 빌드

- 최신 DMG: `clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- 생성 시각: `2026-05-04 20:55 KST`
- 크기: `150M`
- Node: `v22.22.2`
- 빌드 명령: `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`

## repo 상태

2026-05-04 21:13 KST 기준:

| repo | branch/status |
|---|---|
| `clipper_nestjs` | `feature/initial-scaffold...origin/feature/initial-scaffold [ahead 30]`, clean |
| `clipper_angular` | `feature/initial-scaffold...origin/feature/initial-scaffold [ahead 26]`, clean |
| `clipper_electron` | `feature/initial-scaffold...origin/feature/initial-scaffold [ahead 2]`, clean |
| `clipper_python` | `feature/plugin-architecture...origin/feature/plugin-architecture [ahead 1]`, clean |

루트 `/Users/jina/project/adlight` 자체는 git repo가 아니다. `.codex` 문서는 루트 문서로만 관리된다.

## 이번 checkpoint 직전 완료된 핵심 커밋

| repo | commit | 내용 |
|---|---|---|
| `clipper_nestjs` | `8aac74d feat: add clipper studio remote media search provider` | `media.search` HTTP/remote proxy provider 추가 |
| `clipper_nestjs` | `7c6cb49 feat: edit clipper studio script clips` | script/clip edit API 확장, subtitle 변경 시 새 TTS artifact 생성 |
| `clipper_angular` | `842066e feat: edit clipper studio script clips` | title/keywords/clip subtitle/search query/duration 편집 UI 추가 |

이미 앞서 완료된 provider 경계:

- `llm.script`: deterministic, remote proxy, OpenAI Responses-compatible, Ollama/local model.
- `media.search`: remote proxy, Naver, Kakao.
- `image.generate`: HTTP/local-server-compatible provider.
- `tts.synthesis`: HTTP/local-server provider, macOS `say`, seed fallback.
- `video.render`: `video.render.legacy_clipper1.python_worker` headless provider.

## 현재 실제 사용자 흐름

1. Store/nav에서 Clipper Studio를 연다.
2. prompt로 Clipper Studio project shell을 만든다.
3. draft job을 실행한다.
4. NestJS가 script draft, clip plan, seed/local/provider asset artifact를 manifest에 저장한다.
5. `/projects` detail에서 provider 상태 카드, final render area, edit-state controls, clip list를 본다.
6. 사용자는 template, title visibility, logo text, TTS speed, TTS preset, BGM/logo artifact, clip media artifact를 바꿀 수 있다.
7. 사용자는 main title/sub title/bottom title/keywords, clip subtitle/search query/duration을 바꿀 수 있다.
8. clip subtitle이 바뀌면 NestJS가 현재 `tts.synthesis` provider로 새 `audio.tts` artifact를 만들고 clip의 TTS reference를 교체한다.
9. media는 local file import, media search/import, image generation endpoint가 있으면 generated image 적용으로 바꿀 수 있다.
10. render start를 누르면 manifest render output의 `RenderRecipe`가 Python Clipper1 render worker로 전달되고 MP4/thumbnail artifact가 manifest에 반영된다.

## Provider 추상화 원칙

다음 원칙은 앞으로도 계속 유지해야 한다.

- OpenAI, Ollama/Gemma, Gemini, company proxy는 `llm.script` provider 구현체다.
- Naver/Kakao/custom proxy/local generation/user upload는 `media.search`/`image.generate`/`media.import` provider 구현체다.
- Clova/Oute/local TTS/macOS `say`는 `tts.synthesis` provider 구현체다.
- Workflow/editor/render code는 vendor API shape, credential, billing, quota, retry/fallback 정책을 몰라야 한다.
- 새 provider를 붙일 때 core workflow를 수정해야 한다면 abstraction이 부족한 것이다.
- Provider output은 typed draft DTO 또는 `ProjectManifest` artifact로 정규화한다.
- Fake provider 또는 local HTTP server로 network 없이 smoke test가 가능해야 한다.

## 현재 provider env 요약

| capability | 주요 env |
|---|---|
| `llm.script.remote_proxy` | `CLIPPER1_LLM_SCRIPT_ENDPOINT`, `CLIPPER1_LLM_SCRIPT_PROVIDER_ID`, `CLIPPER1_LLM_SCRIPT_ALLOW_FALLBACK` |
| `llm.script.openai_responses` | `CLIPPER1_LLM_SCRIPT_PROVIDER=openai_responses`, `CLIPPER1_LLM_SCRIPT_OPENAI_API_KEY`, `CLIPPER1_LLM_SCRIPT_OPENAI_MODEL` |
| `llm.script.ollama` | `CLIPPER1_LLM_SCRIPT_PROVIDER=ollama`, `CLIPPER1_LLM_SCRIPT_OLLAMA_MODEL`, `CLIPPER1_LLM_SCRIPT_OLLAMA_ENDPOINT` 또는 `CLIPPER1_LLM_SCRIPT_OLLAMA_BASE_URL` |
| `media.search.remote_proxy` | `CLIPPER1_MEDIA_SEARCH_ENDPOINT`, `CLIPPER_STUDIO_MEDIA_SEARCH_ENDPOINT`, `CLIPPER1_MEDIA_SEARCH_PROVIDER_ID`, token/api key variants |
| `media.search.naver/kakao` | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `KAKAO_REST_API_KEY` |
| `image.generate` | `CLIPPER1_IMAGE_GENERATE_ENDPOINT`, `CLIPPER_STUDIO_IMAGE_GENERATE_ENDPOINT`, `CLIPPER1_IMAGE_GENERATE_PROVIDER_ID` |
| `tts.synthesis.http` | `CLIPPER1_TTS_SYNTHESIS_ENDPOINT`, `CLIPPER_STUDIO_TTS_SYNTHESIS_ENDPOINT`, `CLIPPER1_TTS_SYNTHESIS_PROVIDER_ID`, `CLIPPER1_TTS_SYNTHESIS_SPEAKER_ID` |
| local TTS | `CLIPPER1_LOCAL_TTS_ENABLED`, `CLIPPER1_LOCAL_TTS_VOICE`, `CLIPPER1_LOCAL_TTS_RATE` |
| auto media search | `CLIPPER1_AUTO_MEDIA_SEARCH`, `CLIPPER_STUDIO_AUTO_MEDIA_SEARCH`, `CLIPPER1_AUTO_MEDIA_SEARCH_MAX_CLIPS` |

## 검증 완료

- `clipper_nestjs npm run build`
- `clipper_angular ./node_modules/.bin/ngc -p tsconfig.app.json`
- `clipper_angular npm run build:electron -- --progress=false`
- `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`
- Fake HTTP media search proxy smoke:
  - `media.search.test_proxy.image` provider 선택 확인.
  - WebP candidate 정규화, width/height/sourceHost 반영 확인.
- Script/clip edit API smoke:
  - project create -> draft -> `edit-state` PATCH.
  - title/keywords/subtitle/searchQuery/duration 반영 확인.
  - subtitle 변경 후 edited TTS artifact 생성 확인.
- Packaged bundle string check:
  - `RemoteProxyClipperStudioImageSearchProvider`, `CLIPPER1_MEDIA_SEARCH_ENDPOINT`, `media.search.remote_proxy.image`.
  - `prepareClipTts`, `edited_tts`, `script must be an object`.
  - Angular renderer `메인 제목 1`, `키워드`, `script-editor`, `clip-text-control`.

## 아직 제품적으로 부족한 점

현재 사용자가 직접 확인하면 "기존 Clipper1과 다르다", "아직 장난감 같다"고 느낄 수 있는 지점들이다.

1. Production provider endpoint가 실제 운영 수준으로 연결되지 않았다.
2. Deterministic fallback과 seed asset이 아직 남아 있어, provider 미설정 상태에서는 결과 품질이 낮다.
3. Multi-subtitle timeline editor가 없다. 현재 clip당 첫 subtitle 중심 편집이다.
4. Story/script structure editor가 부족하다. 제목/키워드/clip text만 1차 편집 가능하다.
5. Clipper1 legacy template/table/DB parity가 부족하다.
6. Clipper1 legacy workflow import/adapter가 없다.
7. Source ingest 흐름이 Clipper Studio 시작 화면과 충분히 결합되지 않았다.
8. Render 결과 품질을 실제 provider output 기준으로 수동 QA하지 않았다.
9. Final MP4/thumbnail open UX와 error/retry state polish가 부족하다.
10. Provider status card는 표시되지만, 사용자가 다음에 무엇을 설정해야 하는지까지 안내하는 UX는 약하다.
11. Image generation/search/TTS/LLM endpoint별 quota, timeout, fallback, billing 정책은 아직 운영 정책으로 확정되지 않았다.
12. Super Clone, variations, batch generation workflow는 아직 없다.

## 생각 정리 후 결정해야 할 것

다음 구현 전 사용자가 정하면 좋은 질문이다.

1. Clipper Studio의 MVP 품질 기준은 무엇인가?
   - "기존 Clipper1과 거의 동일한 결과"인지
   - "Clipper2 구조 위에서 새 UX로 재구성"인지
   - "일단 production provider만 붙인 1차 사용 가능 버전"인지
2. 실제 provider 우선순위는 무엇인가?
   - LLM: OpenAI / Ollama-local / company proxy
   - media search: Naver/Kakao / custom search proxy / local asset library
   - image generation: remote generation endpoint / local diffusion
   - TTS: Clova / Oute local server / other local model / macOS say fallback
3. 사용자-facing editor 범위는 어디까지인가?
   - 단순 title/clip text editor
   - multi-subtitle timeline editor
   - Clipper1 legacy editor parity
4. 기존 Clipper1 template/DB는 어떻게 들여올 것인가?
   - JSON catalog 유지
   - DB import
   - remote template catalog
5. 다음 작업은 구현보다 product review/UX 재설계가 먼저인가?

## 다음 작업 후보

사용자가 앱을 확인한 뒤 우선순위를 다시 정해야 한다. 그래도 기술적으로 자연스러운 다음 후보는 다음이다.

1. 직접 확인 피드백 기반 UX 문제 수정.
2. Render/error state polish.
3. Final MP4/thumbnail visual QA.
4. Production provider endpoint 실제 연결.
5. Multi-subtitle timeline editor 설계.
6. Clipper1 template/catalog parity 설계.
7. Source ingest와 Clipper Studio create flow 결합.

## 다음 세션 시작 지침

1. 이 문서를 먼저 읽는다.
2. `.codex/implementation/TASKS.md`, `.codex/implementation/WORKLOG.md`, `.codex/implementation/NEXT_SESSION_PROMPT.md`를 이어서 확인한다.
3. 네 repo의 `git status --short --branch`를 먼저 확인한다.
4. 사용자가 직접 앱을 확인한 피드백이 있으면 그 피드백을 최우선으로 반영한다.
5. provider 추가 작업은 반드시 registry/adapter boundary 뒤에 붙인다.
