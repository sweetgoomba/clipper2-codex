# Clipper Studio Workflow Redesign

작성일: 2026-05-04
Status: previous implementation reference

2026-05-06 기준 사용자-facing 제품 방향은 `SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`가 우선한다. 이 문서는 기존 Clipper Studio 1차 편입 설계와 구현 히스토리 참고용으로 유지한다.

이 문서는 Clipper1을 Clipper2에 편입하는 목표를 다시 고정한다.
핵심 정정은 다음이다.

> `clipper1_video_render`는 사용자가 여는 세 번째 플러그인이 아니다.
> Clipper Studio workflow가 마지막 단계에서 호출하는 내부 `video.render` provider다.

## 1. 지금까지 완료된 것과 완료되지 않은 것

2026-05-04 현재 커밋된 변경:

| repo | commit | 의미 |
|---|---|---|
| `clipper_angular` | `eea2e9e feat: add project render job UI` | 프로젝트 상세에서 render job API를 볼 수 있는 UI 경계 추가, headless worker를 Store/Dashboard에서 숨김 |
| `clipper_angular` | `5186325 feat: add clipper studio workflow shell` | Store/nav에서 실제 `/clipper-studio` 제작 화면을 열고 project shell을 만들 수 있게 함 |
| `clipper_angular` | `083083c feat: generate clipper studio drafts` | Clipper Studio project 생성 후 deterministic draft를 만들고 `/projects` presenter에 표시 |
| `clipper_angular` | `9c8c290 feat: run clipper studio drafts as jobs` | draft 생성을 progress/cancel 가능한 job UI로 전환 |
| `clipper_angular` | `1045c46 feat: show clipper studio final renders` | render 완료 후 manifest artifact URL을 해석하고 Clipper Studio detail에서 최종 MP4/thumbnail preview 표시 |
| `clipper_angular` | `81fec28 fix: refresh clipper studio render manifest` | render job polling 완료 시 manifest를 다시 읽어 final preview가 같은 상세 화면에서 갱신되게 보정 |
| `clipper_angular` | `6d7332a feat: add clipper studio edit state client` | Angular API client에 Clipper Studio edit-state PATCH method 추가 |
| `clipper_angular` | `3f135a7 feat: edit clipper studio render settings` | Clipper Studio detail에 title visibility/logo text/TTS speed 편집 UI와 save wiring 추가 |
| `clipper_angular` | `5836899 feat: select clipper studio templates` | Clipper1 template catalog를 Clipper Studio detail select에 연결하고 선택값을 edit-state로 저장 |
| `clipper_angular` | `47f3151 feat: select clipper studio audio and logo assets` | Clipper Studio detail에 project artifact 기반 BGM/logo image select와 stale 재렌더 문구 추가 |
| `clipper_angular` | `db4fc42 feat: edit clipper studio clip media` | Clipper Studio clip list에서 clip별 media artifact 선택 UI 추가 |
| `clipper_angular` | `609a9b9 feat: select clipper studio tts presets` | Clipper Studio detail에 TTS preset select 추가 |
| `clipper_angular` | `8217791 feat: show clipper studio render versions` | render control에 완료 render job 이력을 version label로 표시 |
| `clipper_angular` | `edb2de6 feat: link clipper studio render versions` | final render preview에서 보존된 version MP4 링크 표시 |
| `clipper_angular` | `b9dec90 feat: show clipper studio render empty state` | final render MP4가 없을 때 9:16 empty preview 표시 |
| `clipper_angular` | `1341a3d polish clipper studio render empty state` | Chrome CDP visual QA 후 final render empty preview의 중복 상태 문구 정리 |
| `clipper_angular` | `c1f9d22 fix projects detail panel scrolling` | Clipper Studio detail의 `편집 상태` 이하가 실제 UI에서 스크롤 접근 가능하도록 detail panel overflow 보정 |
| `clipper_angular` | `842066e feat: edit clipper studio script clips` | Clipper Studio detail에서 title/keywords/clip subtitle/search query/duration 편집 UI 추가 |
| `clipper_nestjs` | `4f31579 feat: add project manifest render jobs` | `ProjectManifest`, `RenderRecipe`, `VideoRenderJob`, render provider registry/API 추가 |
| `clipper_nestjs` | `167eae7 feat: add clipper studio project shell` | Clipper Studio virtual workflow와 project shell/create API 추가 |
| `clipper_nestjs` | `5f5330a feat: add clipper studio draft generation` | prompt/text deterministic draft generation API와 manifest 업데이트 추가 |
| `clipper_nestjs` | `559652e feat: add clipper studio draft jobs` | draft generation을 persisted job/progress/cancel model로 전환 |
| `clipper_nestjs` | `329fc84 feat: split clipper studio script generator` | deterministic script generation을 `llm.script` provider facade 뒤로 분리 |
| `clipper_nestjs` | `673c965 feat: prepare clipper studio render assets` | placeholder media/TTS/BGM/logo/layout artifact preparation과 renderable output 추가 |
| `clipper_nestjs` | `3ea487b feat: promote clipper studio render results` | render job 완료 결과를 Clipper Studio manifest final output state로 승격 |
| `clipper_nestjs` | `f699a30 feat: update clipper studio edit state` | template/BGM/TTS/logo/title visibility edit state 저장 API와 render recipe 반영 경계 추가 |
| `clipper_nestjs` | `4d75b9e feat: load clipper1 template catalog from json` | Clipper1 template preset source를 fixture가 아니라 JSON catalog 파일 기반으로 전환 |
| `clipper_nestjs` | `fbb0340 feat: support clipper studio clip media selection` | clip media edit-state override와 render recipe source artifact 반영 추가 |
| `clipper_nestjs` | `58af2fd feat: add clipper studio tts preset catalog` | Clipper Studio TTS preset catalog endpoint 추가 |
| `clipper_nestjs` | `d518b12 feat: preserve clipper studio render versions` | render 완료 시 job별 version artifact를 보존하고 metadata에 누적 |
| `clipper_nestjs` | `41792be feat: use clipper studio seed assets` | Clipper1 bundled seed media/TTS/layout/logo asset을 draft project-file artifact로 복사하고 silent BGM 기본 생성을 제거 |
| `clipper_nestjs` | `da1e96d feat: import clipper studio local media` | local file을 project `draft/assets/user_media/`로 복사하고 `media.local_user.file` artifact/edit-state/render recipe에 연결 |
| `clipper_nestjs` | `bb07a87 feat: synthesize clipper studio local tts` | macOS `say` 기반 `tts.local_os.say` provider로 subtitle text별 m4a TTS artifact 생성, seed TTS fallback 유지 |
| `clipper_angular` | `4f679de feat: add clipper studio media import UI` | Clipper Studio clip별 `미디어 추가` UI와 local media import API 호출 추가 |
| `clipper_nestjs` | `8262299 feat: add clipper studio media search import` | Naver/Kakao image search 후보 반환, HTTP(S) media download, project-file artifact 등록, clip edit-state/render recipe 교체 API 추가 |
| `clipper_angular` | `b8bd59a feat: apply clipper studio media search results` | Clipper Studio clip row에서 검색어 기반 `검색 적용`으로 첫 media search 결과를 다운로드/적용하는 UI 추가 |
| `clipper_nestjs` | `1f2605e feat: add clipper studio bgm and logo imports` | legacy BGM MP3 bundled catalog, BGM/logo local upload role, edit-state/render recipe 연결 추가 |
| `clipper_nestjs` | `687d914 feat: add clipper studio remote script provider` | `llm.script` remote proxy/OpenAI-compatible provider boundary와 legacy response 정규화 추가 |
| `clipper_nestjs` | `43d9165 feat: auto apply clipper studio search media` | script-generated search query로 clip media를 draft 생성 중 자동 검색/다운로드/적용 |
| `clipper_nestjs` | `6797b5a refactor: split clipper studio script providers` | `llm.script` provider registry, provider adapters, response normalizer 분리 |
| `clipper_nestjs` | `0da9415 feat: add clipper studio ollama script provider` | Ollama/Gemma 같은 local LLM server를 붙일 수 있는 `llm.script.ollama` adapter 추가 |
| `clipper_nestjs` | `36211b5 refactor: split clipper studio media search providers` | `media.search` provider registry, Naver/Kakao adapters, remote media downloader 분리 |
| `clipper_nestjs` | `8aac74d feat: add clipper studio remote media search provider` | `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 기반 company/custom/local media search proxy adapter 추가 |
| `clipper_nestjs` | `db92d6a refactor: split clipper studio tts providers` | `tts.synthesis` provider registry와 macOS `say` adapter 분리 |
| `clipper_nestjs` | `b170178 feat: add clipper studio http tts provider` | Clova/Oute/local TTS server 같은 실제 구현을 붙일 수 있는 HTTP/local-server TTS adapter 추가 |
| `clipper_nestjs` | `a95c35a feat: add clipper studio image generation provider` | `image.generate` provider registry와 HTTP/local-server-compatible adapter 추가 |
| `clipper_angular` | `02e2c04 feat: add clipper studio image generation UI` | clip row의 검색 prompt에서 generated image를 만들고 clip source로 적용 |
| `clipper_nestjs` | `4d40aa8 feat: expose clipper studio capability status` | image/media provider availability를 capability endpoint로 노출 |
| `clipper_angular` | `083dbdc feat: show clipper studio generation availability` | image generation endpoint 미설정 시 `생성 적용` 버튼 비활성화 |
| `clipper_nestjs` | `47495ec feat: expose clipper studio provider fallback status` | `llm.script`/`media.search`/`image.generate`/`tts.synthesis` provider 상태와 fallback 여부를 capability endpoint로 노출 |
| `clipper_angular` | `b077fba feat: show clipper studio provider status` | Clipper Studio detail 상단에 provider 상태 카드 표시 |
| `clipper_nestjs` | `76bbac8 feat: include clipper studio provider config hints` | capability status에 provider 설정용 env key 힌트 추가 |
| `clipper_nestjs` | `7c6cb49 feat: edit clipper studio script clips` | `edit-state` API가 script/clip patch를 받고 subtitle 변경 시 새 TTS artifact 생성 |
| `clipper_angular` | `9ad8455 feat: show clipper studio provider config hints` | provider 상태 카드에 설정 키 힌트 표시 |
| `clipper_angular` | `bb543e9 feat: add clipper studio bgm and logo import UI` | Clipper Studio detail에서 BGM/로고 `추가` 버튼으로 local artifact를 import/선택 |
| `clipper_angular` | `8e20564 feat: use clipper studio script search queries` | script provider가 만든 clip search query를 `검색 적용` 입력 기본값으로 사용 |
| `clipper_electron` | `4f3e9ac feat: add media file dialog bridge` | Electron preload/main에 이미지/영상 파일 선택 dialog bridge 추가 |
| `clipper_electron` | `43fbd9b feat: add audio file dialog bridge` | Electron preload/main에 오디오 파일 선택 dialog bridge 추가 |
| `clipper_python` | `c53ea33 feat: add clipper1 video render worker` | `clipper1_video_render` Python worker와 로컬 ffmpeg render adapter 추가 |

현재 완료된 것은 Clipper1 전체 편입이 아니라 다음 vertical slice다.

```text
ProjectManifest -> RenderRecipe -> video.render provider -> MP4 artifact
workflow.clipper_studio shell -> deterministic draft job -> bundled seed asset artifacts
  -> user-selected local media artifact override
  -> local OS TTS synthesis artifact
  -> Naver/Kakao media search/download artifact override
  -> HTTP remote media search proxy provider override
  -> bundled legacy BGM catalog and local BGM/logo upload artifact override
  -> remote proxy/OpenAI-compatible llm.script provider boundary
  -> script searchQuery based auto media search/download override
  -> script/title/clip subtitle editor with edited TTS artifact regeneration
  -> video.render.legacy_clipper1.python_worker -> final MP4/thumbnail manifest output
  -> Clipper Studio detail preview/edit-state controls
```

아직 완료되지 않은 것:

- production provider endpoint/key/billing 정책과 실제 endpoint 운영
- script/story full editor와 multi-subtitle timeline editor
- Clipper1 legacy workflow adapter
- Clipper1 template catalog DB/remote source
- 최종 MP4/thumbnail open UX visual QA와 세부 polish
- Super Clone / variation batch workflow

따라서 현재 상태를 "Clipper1이 포함됨"이라고 부르면 안 된다.
정확한 표현은 "Clipper Studio의 prompt-to-render 1차 vertical slice, local media override, local TTS, media search/download, remote media search proxy, BGM/logo catalog/upload, remote LLM provider boundary, script query 기반 자동 media 적용 1차, script/clip subtitle editor 1차가 준비됨"이다.

## 2. 제품 목표

사용자가 기대하는 Clipper1 편입은 다음 경험이다.

1. Store 또는 navigation에서 `Clipper Studio`를 연다.
2. prompt, text, URL, local source 중 하나로 숏폼 제작을 시작한다.
3. 앱이 script/clip plan/media/TTS/template draft를 만든다.
4. 사용자는 title, subtitle, media, TTS, BGM, logo, template를 확인하고 수정한다.
5. `렌더 시작`을 누르면 최종 MP4와 thumbnail이 생성된다.
6. 결과는 `/projects` 작업 보관함에 동일한 project artifact model로 남는다.
7. 재열기, 재렌더, 변형 생성이 같은 project에서 가능하다.

이 경험이 없으면 Store에 `Clipper1 숏폼 제작` 카드가 보이더라도 제품적으로는 편입이 아니다.

## 3. Workflow / Capability / Provider 구분

앞으로 새 단위를 추가할 때는 먼저 아래 세 분류 중 하나로 결정한다.

| 분류 | 사용자에게 보이는가 | 예 |
|---|---:|---|
| Workflow | 예 | `workflow.dance_highlight`, `workflow.dialog_highlight`, `workflow.clipper_studio` |
| Capability | 보통 아니오 | `source.ingest`, `llm.script`, `media.search`, `tts.synthesis`, `template.apply`, `video.render` |
| Provider/runtime | 아니오 | `video.render.legacy_clipper1.python_worker`, `video.render.local_ffmpeg.basic`, local TTS worker |

Store/Dashboard 정책:

- Store는 사용자가 실행할 수 있는 workflow만 기본 노출한다.
- Dashboard는 workflow readiness와 runtime process/resource를 분리해서 보여준다.
- provider/runtime은 dependency detail로 볼 수는 있어도 "열기" 대상이 아니다.
- `clipper1_video_render` 같은 headless worker는 Store 카드가 아니다.

### 3.1 Provider 교체 원칙

Clipper Studio는 특정 AI vendor나 특정 local model에 묶이면 안 된다.
OpenAI, Ollama/Gemma, Gemini, remote company proxy, Naver Image, Kakao Image, local image generation server, Naver Clova, Oute TTS, macOS `say`는 모두 capability 뒤의 provider 구현체일 뿐이다.

따라서 workflow/editor/render code는 다음 세부를 몰라야 한다.

- 어떤 LLM provider가 script를 만들었는지
- 이미지가 Naver/Kakao 검색 결과인지, local diffusion 생성 결과인지, user upload인지
- TTS가 Clova인지, Oute TTS local server인지, macOS `say`인지
- provider credential, billing, quota, retry/fallback 정책이 무엇인지

Provider adapter가 해야 하는 일:

- vendor/local runtime별 request/response를 capability contract로 정규화
- 결과를 `ProjectManifest` artifact 또는 typed draft DTO로 승격
- provider id, model/speaker/source metadata, 오류/fallback 정보를 metadata에 기록
- network 없는 fake provider로 smoke/test 가능하게 유지

Provider adapter가 하면 안 되는 일:

- workflow project state를 직접 소유
- Angular UI 상태를 직접 결정
- render recipe에 vendor-specific response shape을 흘려보내기
- API key나 billing policy를 renderer/editor 코드에 노출

예상 capability/provider 형태:

```text
llm.script
  -> llm.script.remote_proxy
  -> llm.script.openai_responses
  -> llm.script.ollama.local
  -> llm.script.deterministic

media.search / image.generate
  -> media.search.remote_proxy.image
  -> media.search.naver.image
  -> media.search.kakao.image
  -> image.generate.local_server
  -> media.local_user.file

tts.synthesis
  -> tts.local_os.say
  -> tts.clova.remote
  -> tts.oute.local_server
  -> tts.legacy_seed.bundle
```

다음 provider 작업은 "OpenAI 하나 붙이기", "Naver 하나 붙이기"처럼 끝내지 않는다.
먼저 capability contract와 provider registry/adapter boundary를 세우고, 실제 provider는 그 뒤의 교체 가능한 구현체로 둔다.

## 4. Target Architecture

```text
Angular
  Clipper Studio feature
    - create/edit/review/render screens
    - NestJS API client only
    - no direct Python plugin calls

NestJS
  Workflow orchestration/control plane
    - Clipper Studio project state
    - job/queue/history/events
    - capability registry
    - ProjectManifest/ArtifactStorage
    - provider selection and policy

Python workers
  Compute/provider adapters
    - legacy render worker
    - optional local TTS/media helpers
    - no product-level project ownership

Electron
  Desktop host/native adapter
    - packaged process lifecycle
    - venv/ffmpeg/tool path
    - file dialog and local filesystem affordances
```

핵심 경계:

- Angular는 workflow 화면과 사용자 상호작용만 소유한다.
- NestJS가 project/job/workflow state를 소유한다.
- Python worker는 계산과 변환을 수행한다.
- Electron은 packaged host 기능만 제공한다.

## 5. Clipper Studio MVP Workflow

MVP는 legacy Clipper1 전체를 한 번에 복사하지 않는다.
하지만 사용자가 "Clipper1 숏폼 제작이 들어왔다"고 느낄 수 있는 얇은 vertical slice는 반드시 완성해야 한다.

### 5.1 사용자 흐름

```text
New Clipper Studio Project
  -> Source/Prompt input
  -> Generate draft
  -> Review script + clip list
  -> Select template/BGM/TTS/logo options
  -> Render
  -> Open final MP4 in project detail
```

### 5.2 최소 입력

MVP 입력은 하나로 시작한다.

- text prompt 또는 pasted script

YouTube/URL ingest는 이미 Clipper2 source capability가 있으므로 두 번째 slice로 붙인다.

### 5.3 최소 draft 산출물

Draft project는 다음을 가져야 한다.

- project id
- workflow id: `workflow.clipper_studio`
- script/title/keywords
- clip list
- clip별 media reference
- subtitle rows
- TTS audio artifact reference 또는 pending marker
- selected `TemplatePreset`
- selected BGM/logo option
- renderable `RenderRecipe`

### 5.4 최소 render 산출물

Render가 끝나면 manifest에 다음 artifact가 생겨야 한다.

- final video MP4
- thumbnail image
- render recipe snapshot
- source/draft metadata
- render job history reference

UI는 이 artifact를 실제로 열 수 있어야 한다.

## 6. Data Model Direction

Clipper Studio는 legacy DB row를 그대로 복제하지 않는다.
NestJS project model 위에 workflow-specific detail을 얇게 둔다.

```ts
type ClipperStudioProjectDetail = {
  kind: 'clipper_studio';
  source: SourceInput;
  draft: {
    title: string;
    script: string;
    keywords: string[];
    clips: ClipperStudioClip[];
  };
  editState: {
    templatePresetId: string;
    bgmArtifactId?: string;
    logoArtifactId?: string;
    titleVisibility?: 'main' | 'sub' | 'bottom' | 'hidden';
  };
  render: {
    recipeId?: string;
    latestRenderJobId?: string;
    outputArtifactId?: string;
    thumbnailArtifactId?: string;
  };
};
```

`ProjectManifest`는 공통 필드와 artifact/output contract를 유지한다.
workflow-specific detail은 presenter와 editor 상태에 필요한 최소 정보만 담는다.

## 7. API Shape

정확한 route 이름은 구현 시 기존 NestJS convention에 맞추되, 책임은 다음처럼 나눈다.

| API | 책임 |
|---|---|
| `POST /v1/projects/clipper-studio` | Clipper Studio project shell 생성 |
| `POST /v1/projects/:id/clipper-studio/draft-jobs` | prompt/source에서 draft 생성 job 시작 |
| `PATCH /v1/projects/:id/clipper-studio/edit-state` | template/BGM/TTS/logo/subtitle/title 편집 상태 저장 |
| `GET /v1/projects/:id/manifest` | 공통 manifest 조회 |
| `GET /v1/projects/:id/outputs/:outputId/render-recipe` | 현재 edit state로 render recipe 조회 |
| `POST /v1/projects/:id/outputs/:outputId/render-jobs` | `video.render` provider 실행 |

Angular는 이 API만 호출한다.
Python plugin URL, provider id, ffmpeg path, remote key policy를 직접 알면 안 된다.

## 8. Capability Plan

MVP와 이후 확장을 위해 capability는 다음 순서로 닫는다.

| 순서 | capability | MVP 처리 |
|---:|---|---|
| 1 | `template.catalog` | 기존 `TemplatePresetCatalogService` 확장 |
| 2 | `template.apply` | selected preset + edit state -> `RenderRecipe` |
| 3 | `video.render` | 현재 `clipper1_video_render` worker 사용 |
| 4 | `llm.script` | mock 또는 legacy adapter behind NestJS facade |
| 5 | `media.search/download` | initially one provider, artifact로 저장 |
| 6 | `tts.catalog/synthesis` | initially one provider, artifact로 저장 |
| 7 | `source.ingest` | prompt 먼저, YouTube/local URL은 후속 |

중요한 제한:

- LLM/TTS 유료 provider key는 packaged app/plugin 코드에 직접 넣지 않는다.
- media/TTS/template/render 결과는 파일만 남기지 않고 manifest artifact로 등록한다.
- provider 실패/retry/cancel은 NestJS job model로 표준화한다.

## 9. Implementation Phases

### Phase 0. Status correction and cleanup

상태: 완료.

- `clipper1_video_render`를 headless worker로 분류.
- Store/Dashboard 사용자 목록에서 숨김.
- dialog/dance completed detail에 잘못 붙은 render UX 제거 또는 Clipper Studio manifest로 제한.
- 기존 변경 커밋:
  - `clipper_angular` `eea2e9e`
  - `clipper_nestjs` `4f31579`
  - `clipper_python` `c53ea33`

완료 기준:

- 사용자는 headless worker를 "열기" 대상으로 보지 않는다.
- 현재 render bridge가 Clipper1 workflow 완료로 표현되지 않는다.

### Phase 1. Clipper Studio workflow shell

목표:

- `workflow.clipper_studio`를 user-facing workflow로 등록한다.
- Angular에 실제로 열리는 `Clipper Studio` screen을 만든다.

작업:

- workflow descriptor 추가.
- Store/Dashboard filtering을 workflow descriptor 기반으로 바꾼다.
- Angular route 예: `/clipper-studio`.
- 화면은 landing page가 아니라 project creation/editor shell이어야 한다.
- 비어 있는 "열기" 버튼은 금지한다.

완료 기준:

- Store에서 `Clipper Studio`를 누르면 실제 제작 화면이 열린다.
- 아직 provider가 없어도 사용자는 project shell을 만들 수 있다.
- headless provider는 dependency로만 표시된다.

Implementation note from 2026-05-04:

- NestJS `clipper_studio` virtual workflow descriptor를 추가했다.
- `clipper1_video_render`는 계속 headless provider/runtime으로 남겨두고, Angular user-visible list에서는 `clipper_studio`만 workflow로 노출한다.
- Angular `/clipper-studio` route와 prompt 기반 project shell creation 화면을 추가했다.
- Store와 nav에서 `Clipper Studio`를 열면 실제 제작 화면으로 이동한다.
- Dashboard에서는 `clipper_studio`를 runtime start/stop 대상이 아니라 workflow screen으로 취급한다.

### Phase 2. Clipper Studio project shell + manifest

목표:

- 사용자가 만든 Clipper Studio draft가 `/projects`에 project로 남는다.

작업:

- NestJS에 `workflow.clipper_studio` project create/update path 추가.
- `ClipperStudioProjectDetail` DTO 추가.
- prompt/source/edit state를 저장한다.
- `/v1/projects/:id/manifest`가 `detail.kind = 'clipper_studio'`를 반환한다.
- `/projects` detail panel이 Clipper Studio presenter를 선택한다.

완료 기준:

- 앱 재시작 후에도 draft project가 남는다.
- project detail에서 source, script, clips, selected template를 볼 수 있다.

Implementation note from 2026-05-04:

- `POST /v1/projects/clipper-studio`가 prompt/title을 받아 `clipper_studio` project shell을 만든다.
- project result에 embedded `project-manifest.v1`을 저장한다.
- manifest detail은 `kind = 'clipper_studio'`, input prompt, editState, empty clip list, draft output을 포함한다.
- Angular `/projects?project=...`가 job history에 없는 project shell도 synthetic completed job으로 표시할 수 있게 했다.
- `/projects` detail에 Clipper Studio presenter를 추가했다.

### Phase 3. Draft generation adapter

목표:

- prompt/source에서 실제 clip draft를 만든다.

작업:

- `llm.script` facade를 NestJS에 둔다.
- MVP는 mock 또는 legacy adapter로 시작하되 provider boundary를 코드상 고정한다.
- clip plan, title, keywords, subtitles를 project detail에 저장한다.
- media/TTS가 준비되지 않은 항목은 pending state를 명시한다.

완료 기준:

- prompt 입력 후 project에 script와 clip list가 생긴다.
- job history/progress/cancel이 NestJS event model로 보인다.

Implementation note from 2026-05-04:

- `POST /v1/projects/:projectId/clipper-studio/draft`를 추가했다.
- 첫 구현은 real LLM이 아니라 deterministic draft adapter다.
- prompt/title에서 script title, keywords, 3개 clip plan/subtitle row를 만든다.
- draft 결과는 embedded `project-manifest.v1`의 script artifact, draft output, `detail.script`, `detail.clips`에 저장된다.
- `POST /v1/projects/:projectId/clipper-studio/draft-jobs`를 추가해 초안 생성을 `queued/running/succeeded/failed/cancelled` job snapshot으로 저장한다.
- `GET /v1/projects/:projectId/clipper-studio/draft-jobs/:jobId`와 `DELETE /v1/projects/:projectId/clipper-studio/draft-jobs/:jobId`로 progress polling과 cancel을 지원한다.
- Angular `/clipper-studio`는 project shell 생성 후 draft job을 시작하고 진행률/취소 UI를 보여준 뒤 `/projects?project=...`로 이동한다.
- `ClipperStudioScriptGenerator` facade를 추가하고 deterministic adapter를 `llm.script.deterministic` provider로 분리했다.
- 남은 gap: deterministic fallback을 실제 운영에서 대체할 production proxy/key/billing 정책과 endpoint wiring은 아직 없다.

### Phase 4. Asset preparation

목표:

- render 가능한 media/TTS/BGM/logo artifact를 만든다.

작업:

- media provider 하나를 붙인다.
- TTS provider 하나를 붙인다.
- BGM/template catalog를 선택 가능하게 한다.
- 모든 결과를 `ArtifactStorage`와 manifest artifact로 등록한다.

완료 기준:

- Clipper Studio project가 local artifact만으로 render recipe를 만들 수 있다.
- remote URL은 provider 내부 임시값이 아니라 artifact reference로 정규화된다.

Initial implementation note from 2026-05-04:

- `ClipperStudioAssetPreparer`를 추가했다.
- 첫 provider는 real media/TTS가 아니라 deterministic placeholder였다.
- 초기 draft job 완료 시 다음 local project-file artifact를 만들었다.
  - clip별 `media.image` BMP
  - clip별 silent `audio.tts` WAV
  - silent `audio.bgm` WAV
  - placeholder `media.image` logo BMP
  - placeholder layout BMP
- `output.clipper-studio.render.main` render output과 `renderRecipeId`를 manifest에 추가한다.
- legacy fixture template의 원격 `layout_image`는 local layout artifact로 override해 packaged render가 외부 `example.invalid`에 의존하지 않게 했다.

Provider replacement notes from 2026-05-04:

- `41792be`: 단색 BMP/silent WAV 기본값을 bundled legacy seed media/TTS/layout/logo artifact로 교체하고 silent BGM 기본 생성을 제거했다.
- `da1e96d`/`4f679de`/`4f3e9ac`: Electron image/video file dialog -> NestJS local media import -> `media.local_user.file` artifact -> clip edit-state/render recipe override를 연결했다.
- `bb07a87`: macOS `say` 기반 `tts.local_os.say` artifact를 subtitle text별로 생성하고 seed TTS fallback을 유지했다.
- `8262299`/`b8bd59a`: Naver/Kakao media search와 HTTP(S) image/video download를 project artifact로 등록하고 clip source artifact를 교체한다.
- `1f2605e`/`bb543e9`/`43fbd9b`: legacy BGM MP3 10개를 bundled `audio.bgm.legacy_bundle` catalog artifact로 등록하고, user BGM/logo import를 `audio.bgm.local_user.file`/`logo.local_user.file` artifact와 edit-state/render recipe에 연결했다.
- `687d914`/`8e20564`: `CLIPPER1_LLM_SCRIPT_ENDPOINT` 기반 remote proxy provider와 explicit `openai_responses` provider boundary를 추가하고, legacy Clipper1 GPT response shape을 Clipper Studio draft로 정규화한다. clip별 `combined_keyword`/`searchQuery`는 media search 입력 기본값으로 사용한다.
- `43d9165`: media search credential이 있으면 draft 생성 중 clip별 `searchQuery`/keyword로 첫 검색 후보를 자동 다운로드하고 edit-state `clipMediaArtifactIds`에 연결한다. user-selected media는 덮지 않는다.
- `6797b5a`: `llm.script` 구현을 provider registry/adapter 구조로 분리했다. workflow-facing facade는 `ClipperStudioScriptGenerator`이고, provider 구현체는 deterministic/remote proxy/OpenAI Responses adapter로 분리된다. response 정규화는 별도 normalizer가 담당한다.
- `0da9415`: `llm.script`에 Ollama-compatible adapter를 추가했다. `CLIPPER1_LLM_SCRIPT_PROVIDER=ollama`와 `CLIPPER1_LLM_SCRIPT_OLLAMA_MODEL` 설정으로 local Ollama/Gemma 계열 모델을 호출하고, Ollama `/api/generate`의 `response` JSON 문자열을 기존 script draft normalizer로 정규화한다.
- `36211b5`: `media.search` 구현을 provider registry/adapter 구조로 분리했다. workflow-facing facade는 `ClipperStudioMediaSearchProvider`이고, provider 구현체는 Naver/Kakao image search adapter로 분리된다. HTTP(S) artifact materialization은 `ClipperStudioRemoteMediaDownloader`가 담당한다.
- `8aac74d`: `RemoteProxyClipperStudioImageSearchProvider`를 추가했다. `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 또는 `CLIPPER_STUDIO_MEDIA_SEARCH_ENDPOINT` 설정 시 company/custom/local media search proxy를 호출하고, `items`/`results`/`candidates`/`images` 계열 응답을 `media.image` candidate로 정규화한다.
- `db92d6a`: `tts.synthesis` 구현을 provider registry/adapter 구조로 분리했다. workflow-facing facade는 `ClipperStudioTtsSynthesisProvider`이고, macOS `say`는 `MacOsSayClipperStudioTtsProvider` adapter로 분리된다. seed TTS fallback은 asset preparation 단계의 artifact fallback으로 유지된다.
- `b170178`: `tts.synthesis`에 HTTP/local-server-compatible adapter를 추가했다. `CLIPPER1_TTS_SYNTHESIS_ENDPOINT` 또는 `CLIPPER_STUDIO_TTS_SYNTHESIS_ENDPOINT`가 있으면 JSON base64/audio URL/direct audio response를 받아 `audio.tts` artifact로 정규화한다. Clova/Oute/local model server는 workflow가 아니라 이 provider adapter 뒤에 붙인다.
- `a95c35a`: `image.generate` 구현을 provider registry/adapter 구조로 추가했다. workflow-facing facade는 `ClipperStudioImageGenerationProvider`이고, HTTP/local-server-compatible image generation은 `HttpClipperStudioImageGenerationProvider` adapter로 분리된다. generated image는 project-file artifact로 정규화되고 clip source edit-state에 연결된다.
- `02e2c04`: `/projects` Clipper Studio clip row에 `생성 적용` 버튼을 추가했다. 기존 search query 입력을 prompt로 사용하고, Angular client가 `media/generate` API를 호출해 generated artifact를 clip source로 적용한다.
- `4d40aa8`/`083dbdc`: `GET /projects/clipper-studio/capabilities`로 provider availability를 노출하고, image generation endpoint가 설정되지 않은 상태에서는 `/projects`의 `생성 적용` 버튼을 비활성화한다.
- `47495ec`/`b077fba`: capability endpoint와 Clipper Studio detail UI가 provider availability뿐 아니라 fallback 상태까지 표시한다. `llm.script`는 deterministic fallback, `tts.synthesis`는 local provider + seed fallback, `media.search`/`image.generate`는 endpoint/key 미설정 상태를 명시한다.
- `76bbac8`/`9ad8455`: capability endpoint가 각 provider를 설정할 때 필요한 env key를 `configurationKeys`로 내려주고, Clipper Studio detail provider 카드가 대표 설정 키를 표시한다.
- `7c6cb49`/`842066e`: Clipper Studio detail에서 main/sub/bottom title, keywords, clip subtitle, clip search query, clip duration을 편집한다. subtitle 변경 시 현재 `tts.synthesis` provider로 새 `audio.tts` artifact를 만들고 다음 render recipe가 새 subtitle/TTS artifact를 사용한다.

### Phase 5. Render integration using existing provider

목표:

- 현재 만든 `clipper1_video_render`를 최종 렌더 단계에서 사용한다.

작업:

- edit state + artifacts + template preset -> `RenderRecipe`.
- `video.render.legacy_clipper1.python_worker` provider 선택.
- render job progress/cancel/result를 project detail에 연결.
- final MP4/thumbnail artifact를 manifest에 반영한다.

완료 기준:

- 사용자가 Clipper Studio project에서 `렌더 시작`을 누르면 실제 MP4가 생성된다.
- 완료 후 같은 화면에서 최종 영상을 열 수 있다.
- `/projects` history에도 최종 artifact가 보인다.

Implementation note from 2026-05-04:

- render output은 existing `video.render.legacy_clipper1.python_worker` provider와 호환된다.
- packaged app smoke에서 Clipper Studio draft -> asset preparation -> `RenderRecipe` -> Python worker render job이 `succeeded` 됐다.
- 생성 파일:
  - `renders/main.mp4`
  - `renders/main_thumbnail.jpg`
- render job 조회 시 job result가 project manifest final artifact state로 승격된다.
- manifest summary는 final render output을 primary output으로 바꾸고 `renders=1`, `render-completed` badge, thumbnail artifact를 기록한다.
- Angular manifest client가 project-file/source-file/remote-url artifact를 열 수 있는 URL로 해석한다.
- `/projects` Clipper Studio detail은 completed render output의 MP4를 `<video controls>`로 보여주고 thumbnail을 poster로 사용한다.
- render job polling이 terminal 상태로 끝나면 detail과 manifest를 함께 다시 읽어 같은 화면에서 final preview가 갱신된다.
- `PATCH /v1/projects/:id/clipper-studio/edit-state`가 template/BGM/TTS/logo/title visibility edit state를 manifest에 저장하고 다음 render recipe에 반영한다.
- `/projects` Clipper Studio detail에서 서브/메인/하단 제목, 로고 표시, 로고 텍스트, TTS 속도를 저장할 수 있다.
- `/projects` Clipper Studio detail에서 `GET /v1/template-presets?workflow=workflow.clipper_studio&source=clipper1&locale=ko-KR` 기반 template select를 표시하고 선택값을 저장할 수 있다.
- Clipper1 template preset source는 `src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`를 읽는다.
- 남은 gap: visual QA, empty/error state, 재렌더/버전 선택 UX polish.

### Phase 6. Legacy parity hardening

목표:

- 기존 Clipper1 사용자 결과물과 시각/음성 parity를 높인다.

작업:

- template-specific subtitle style 추출.
- legacy video/GIF motion parity 보강.
- logo/title/layout edge cases 보강.
- remote asset persistent cache 정책 결정.
- long external object storage render E2E.

완료 기준:

- 대표 legacy template 샘플이 Clipper2 render와 비교 가능한 수준으로 맞는다.
- 긴 render와 cancel/cleanup이 안정적이다.

### Phase 7. Super Clone / batch variation

목표:

- 단일 project workflow가 안정된 뒤 variation batch를 붙인다.

작업:

- Super Clone을 별도 workflow로 둘지 project batch action으로 둘지 최종 결정.
- variation set을 project manifest와 job queue 위에 표현한다.
- render provider를 재사용한다.

완료 기준:

- batch 결과도 project history/artifact model을 벗어나지 않는다.

## 10. Immediate Next Implementation Target

2026-05-04 21:13 KST 기준으로 즉시 이어서 구현하기보다 product/UX checkpoint를 먼저 확인한다.
현재 결과물이 기존 Clipper1과 다르게 보이는 핵심 원인은 render worker 하나가 아니라 production provider endpoint, draft/script/editor parity, template parity, render QA가 아직 부족하기 때문이다.
render worker는 MP4를 만들 수 있고 media/TTS/BGM/logo/layout의 1차 artifact provider, remote `llm.script` provider boundary, remote `media.search` proxy, script query 기반 자동 media 적용, script/clip subtitle editor 1차는 붙었다. 이제 남은 큰 demo 의존은 production provider endpoint 운영과 세부 editor/parity다.

현재 완료된 vertical slice:

1. `workflow.clipper_studio` descriptor.
2. Store/nav가 실제 Angular `/clipper-studio` route를 연다.
3. `/clipper-studio` 화면에서 prompt/project shell 생성.
4. NestJS project create path가 `detail.kind = 'clipper_studio'` manifest를 만든다.
5. prompt/text deterministic draft가 job/progress/cancel model로 실행된다.
6. `/projects`에서 script와 clip plan을 다시 열 수 있다.
7. bundled seed media/TTS/logo/layout artifact가 local project-file로 준비된다. 기본 BGM은 실제 catalog가 붙기 전까지 만들지 않는다.
8. render recipe가 existing Clipper1 Python worker provider를 통해 실제 MP4/thumbnail을 생성한다.
9. render 완료 결과가 manifest final output으로 승격되고 `/projects` Clipper Studio detail에서 preview된다.
10. Clipper Studio edit state 저장 API가 title visibility/logo text/TTS speed 등을 manifest와 render recipe에 반영한다.
11. Clipper Studio detail UI에서 title visibility/logo text/TTS speed를 직접 저장할 수 있다.
12. Clipper Studio detail UI에서 Clipper1 template catalog 기반 템플릿을 선택할 수 있다.
13. Clipper1 template catalog가 fixture에서 JSON file source로 분리됐다.
14. Clipper Studio detail UI에서 project artifact 기반 BGM/logo image를 선택할 수 있다.
15. Clipper Studio detail UI에서 clip별 media artifact를 선택할 수 있고, render recipe가 선택값을 반영한다.
16. Clipper Studio detail UI에서 TTS preset을 선택할 수 있고, render recipe가 선택값을 반영한다.
17. stale render output의 주요 render action 문구가 재렌더 흐름으로 표시된다.
18. 완료 render job 이력이 version label로 표시된다.
19. 완료 render artifact가 `renders/versions/<jobId>/`에 보존되고 final render 영역에서 version 링크로 열린다.
20. final render MP4가 아직 없으면 9:16 empty preview가 표시된다.
21. Clipper Studio detail UI에서 clip별 media search를 실행하고 첫 검색 결과를 project artifact로 다운로드/적용할 수 있다.
22. render recipe가 media search/download artifact를 clip source로 반영한다.
23. Clipper Studio draft가 bundled legacy BGM catalog 10개를 `audio.bgm.legacy_bundle` artifact로 갖는다.
24. Clipper Studio detail UI에서 local BGM/logo file을 import하고 즉시 edit-state/render recipe에 반영할 수 있다.
25. `CLIPPER1_LLM_SCRIPT_ENDPOINT` 기반 remote proxy 또는 explicit OpenAI Responses-compatible provider를 통해 script draft를 생성할 수 있다.
26. legacy Clipper1 GPT response의 `combined_keyword`가 clip media search 기본값으로 연결된다.
27. media search credential이 있으면 draft 생성 중 clip별 첫 검색 결과가 자동으로 project artifact가 되고 render recipe source artifact로 쓰인다.
28. `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 기반 HTTP/remote media search proxy provider가 있다.
29. Clipper Studio detail에서 title/keywords/clip subtitle/search query/duration을 1차 편집하고, subtitle 변경 시 새 TTS artifact를 만든다.

placeholder/demo provider 제거는 아래 순서로 닫는다. 2026-05-04 현재 1~6, remote media search proxy, script query 기반 자동 media 적용, script/clip editor 1차 구현은 끝났다. 다음 실제 구현 대상은 사용자의 앱 확인 피드백을 기준으로 다시 정한다.

1. **Bundled legacy seed asset provider**
   - 외부 API 없이 기존 Clipper1 repo에 있는 템플릿 배경, 로고, 샘플 미디어, 샘플 TTS 음성을 Clipper2 번들 asset으로 옮긴다.
   - `ClipperStudioAssetPreparer`가 단색 BMP와 silent WAV를 만들지 않고, 이 seed asset을 project-file artifact로 복사하게 한다.
   - 이 단계는 "실제 provider 최종형"은 아니지만, 현재처럼 무음/단색 placeholder 영상이 나오는 문제를 먼저 제거한다.
   - 2026-05-04 구현: `clipper_nestjs` `41792be feat: use clipper studio seed assets`.
   - `media.legacy_seed.bundle`, `tts.legacy_seed.bundle`, `layout.legacy_seed.bundle`, `logo.legacy_seed.bundle` provider id로 project-file artifact를 만든다. 기본 BGM은 silent artifact를 생성하지 않고 `사용 안 함` 상태로 둔다.
2. **Local/user media provider**
   - 사용자가 업로드한 이미지/영상 또는 source ingest 결과를 clip media artifact로 등록한다.
   - Clipper Studio clip별 media select가 실제 사용자/로컬 media를 선택하게 한다.
   - 2026-05-04 구현: `clipper_nestjs` `da1e96d`, `clipper_angular` `4f679de`, `clipper_electron` `4f3e9ac`.
   - Electron media file dialog -> NestJS local media import API -> project-file artifact -> clip edit-state override -> render recipe source artifact까지 연결했다.
3. **TTS synthesis provider**
   - 기존 Clipper1 TTS catalog/model/speaker 구조를 NestJS provider boundary 뒤로 옮긴다.
   - subtitle text별 실제 음성 파일을 생성하고 `audio.tts` artifact로 저장한다.
   - provider key/billing이 필요한 remote TTS는 packaged app에 key를 직접 넣지 않는다.
   - 2026-05-04 1차 구현: `clipper_nestjs` `bb07a87`.
   - macOS `say` + `Yuna` voice로 subtitle text별 `.m4a`를 생성하고 `tts.local_os.say` artifact로 등록한다. 사용할 수 없으면 기존 `tts.legacy_seed.bundle` seed MP3로 fallback한다.
4. **Media search/download provider**
   - Naver/Kakao/Pixabay/Tenor/origin media search를 capability provider로 분리한다.
   - 검색 결과는 URL만 UI에 노출하지 않고 download/cache 후 manifest artifact로 등록한다.
   - 2026-05-04 1차 구현: `clipper_nestjs` `8262299`, `clipper_angular` `b8bd59a`.
   - 현재 provider는 HTTP remote proxy, Naver/Kakao image search와 HTTP(S) image/video download를 지원한다.
   - UI는 clip row에서 검색어를 입력하고 `검색 적용`을 누르면 첫 검색 후보를 다운로드해 해당 clip media artifact로 교체한다.
5. **BGM/logo catalog/upload provider**
   - 기존 BGM catalog와 logo upload/catalog를 project artifact model에 붙인다.
   - 기본값은 "사용 안 함" 또는 실제 선택지여야 하며 silent BGM artifact를 기본 BGM처럼 취급하지 않는다.
   - 2026-05-04 1차 구현: `clipper_nestjs` `1f2605e`, `clipper_angular` `bb543e9`, `clipper_electron` `43fbd9b`.
   - bundled legacy BGM 10개, user BGM import, user logo import, audio file dialog bridge가 연결됐다.
6. **Legacy/remote LLM script provider**
   - deterministic script generator는 개발 fallback으로 유지한다.
   - 기존 Clipper1 prompt/script logic 또는 remote LLM proxy는 key/billing/proxy 정책 확정 뒤 `llm.script` provider로 교체한다.
   - 2026-05-04 1차 구현: `clipper_nestjs` `687d914`, `clipper_angular` `8e20564`.
   - remote proxy/OpenAI-compatible provider boundary와 legacy response 정규화는 구현됐다.
   - production proxy/key/billing 정책과 실제 endpoint 운영은 후속이다.
7. **Render/re-render/error polish**
   - 위 provider들이 실제 artifact를 만들기 시작한 뒤 final MP4/thumbnail visual QA와 재렌더/오류 상태를 다듬는다.

이 순서 전에는 "Clipper1 제작 품질 편입 완료"로 표현하지 않는다.

## 11. Anti-goals

- `clipper1_video_render`를 Store 카드로 다시 노출하지 않는다.
- dialog/dance 완료 결과에 Clipper1 render 버튼을 붙이지 않는다.
- legacy Clipper1 folder를 Python plugin 하나로 통째로 복사하지 않는다.
- Angular가 multi-step generation/render orchestration을 직접 관리하지 않는다.
- output manifest 없이 파일 경로만 보고 UI가 결과를 추론하지 않는다.
- provider/runtime 상태를 workflow readiness처럼 표시하지 않는다.
