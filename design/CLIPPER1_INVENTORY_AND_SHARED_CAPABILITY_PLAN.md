# Clipper1 Inventory and Shared Capability Plan

작성일: 2026-05-04

Status: current draft
Last verified: 2026-05-04
Applies to:

- `adlight_angular` `feature/d2x-electron`
- `adlight_python` `feature/d2x-electron`
- Clipper2 `clipper_angular`, `clipper_nestjs`, `clipper_python`, `clipper_electron`

이 문서는 Clipper1/D2X 기능을 Clipper2에 편입하기 전 기능 inventory와 분해 설계를 정리한다. 결론은 명확하다.

> Clipper1을 `clipper_studio`라는 거대한 workflow plugin 하나로 복사하지 않는다. 사용자 실행 workflow는 얇게 두고, script/media/TTS/template/render/project output은 shared capability layer로 분해한다.

## 0. 2026-05-04 상태 정정

현재 구현된 것은 Clipper1 전체 workflow가 아니라 Clipper Studio 1차 vertical slice다.

- `clipper_python` `c53ea33 feat: add clipper1 video render worker`
  - `clipper1_video_render`는 headless Python worker/provider다.
  - 사용자가 Store에서 여는 workflow plugin이 아니다.
- `clipper_nestjs` `4f31579 feat: add project manifest render jobs`
  - `ProjectManifest`, `RenderRecipe`, `VideoRenderJob`, render provider registry/API 경계가 추가됐다.
- `clipper_angular` `eea2e9e feat: add project render job UI`
  - render job UI 경계가 생겼다.
  - headless worker는 Store/Dashboard에서 숨긴다.
- `clipper_angular` `1045c46 feat: show clipper studio final renders`
  - Clipper Studio completed render output의 MP4/thumbnail을 project detail에서 preview한다.
- `clipper_angular` `81fec28`, `6d7332a`, `3f135a7`, `5836899`, `47f3151`, `db4fc42`, `609a9b9`, `8217791`, `edb2de6`, `b9dec90`
  - render 완료 후 manifest를 refresh해 preview를 같은 화면에서 갱신하고, edit-state API client를 추가했다.
  - Clipper Studio detail에 title visibility/logo text/TTS speed 편집 UI를 추가했다.
  - Clipper Studio detail에 Clipper1 template catalog select를 추가했다.
  - Clipper Studio detail에 project artifact 기반 BGM/logo image select를 추가하고 stale 재렌더 문구를 보정했다.
  - Clipper Studio detail에 clip별 media artifact select를 추가했다.
  - Clipper Studio detail에 TTS preset select를 추가했다.
  - render control에 완료 render job 이력을 version label로 표시하고, final render 영역에서 version MP4 링크를 표시한다.
  - final render MP4 URL이 아직 없을 때 9:16 empty preview를 표시한다.
- `clipper_nestjs` `167eae7`, `5f5330a`, `559652e`, `329fc84`, `673c965`, `3ea487b`
  - Clipper Studio project shell, deterministic draft job, script generator facade, placeholder asset preparation, render provider 연결, render result manifest promotion이 추가됐다.
- `clipper_nestjs` `f699a30`
  - Clipper Studio edit-state 저장 API와 render recipe 반영 경계를 추가했다.
- `clipper_nestjs` `4d75b9e`
  - Clipper1 template preset source를 JSON catalog file 기반으로 전환했다.
- `clipper_nestjs` `fbb0340`
  - edit-state `clipMediaArtifactIds`와 render recipe source artifact override를 추가했다.
- `clipper_nestjs` `58af2fd`
  - Clipper Studio TTS preset catalog endpoint를 추가했다.
- `clipper_nestjs` `d518b12`
  - render 완료 시 `renders/versions/<jobId>/` version artifact를 보존하고 manifest metadata에 누적한다.
- `clipper_nestjs` `41792be`
  - Clipper Studio draft asset preparation이 단색 BMP/silent WAV 대신 bundled Clipper1 seed media/TTS/layout/logo project-file artifact를 생성한다.
  - silent BGM artifact는 기본 생성하지 않고 실제 BGM catalog/upload provider 전까지 `사용 안 함` 상태로 둔다.
- `clipper_nestjs` `da1e96d`, `clipper_angular` `4f679de`, `clipper_electron` `4f3e9ac`
  - Electron image/video file dialog -> NestJS local media import API -> project-file artifact -> clip edit-state override -> render recipe source artifact 경계를 추가했다.
- `clipper_nestjs` `bb07a87`
  - macOS `say` 기반 `tts.local_os.say` provider로 subtitle text별 m4a TTS artifact를 생성한다.
  - 사용할 수 없는 환경은 기존 `tts.legacy_seed.bundle` seed MP3로 fallback한다.
- `clipper_nestjs` `8262299`, `clipper_angular` `b8bd59a`
  - Naver/Kakao image search 후보를 반환하고 HTTP(S) media를 project `draft/assets/search_media/`로 다운로드하는 1차 provider/API를 추가했다.
  - Clipper Studio clip row의 `검색 적용`으로 첫 검색 후보를 project-file media artifact로 저장하고 clip edit-state/render recipe source artifact를 교체한다.
- `clipper_nestjs` `1f2605e`, `clipper_angular` `bb543e9`, `clipper_electron` `43fbd9b`
  - legacy Clipper1 BGM MP3 10개를 bundled catalog로 옮겨 `audio.bgm.legacy_bundle` project-file artifact로 등록한다.
  - user-selected BGM/logo file을 `audio.bgm.local_user.file` / `logo.local_user.file` artifact로 등록하고 edit-state/render recipe에 즉시 반영한다.
  - Electron audio file dialog bridge와 Angular BGM/logo `추가` UI를 연결했다.
- `clipper_nestjs` `687d914`, `clipper_angular` `8e20564`
  - `CLIPPER1_LLM_SCRIPT_ENDPOINT` 기반 remote proxy provider와 explicit `openai_responses` provider boundary를 추가했다.
  - legacy Clipper1 GPT response shape(`clips[].subtitles`, `keywords`, `combined_keyword`, `total_keywords`, `main_title*`)을 Clipper Studio draft로 정규화한다.
  - clip별 `combined_keyword`/`searchQuery`는 Angular `검색 적용` 입력 기본값으로 사용한다.
- `clipper_nestjs` `43d9165`
  - media search credential이 있으면 draft 생성 중 clip별 `searchQuery`/keyword로 첫 검색 결과를 자동 다운로드한다.
  - 자동 검색 결과는 project `draft/assets/auto_search_media/` artifact로 등록되고 edit-state/render recipe source artifact로 연결된다.
  - user-selected media는 덮지 않고, 이전 자동 검색 artifact만 새 draft에서 교체한다.

정확한 현재 상태:

```text
Clipper Studio workflow: prompt-to-render plus local media override, local TTS synthesis, media search/download, remote media search proxy, BGM/logo catalog/upload, remote LLM provider boundary, script-query auto media apply, and script/clip editor 1차 implemented
Clipper1 render provider boundary: implemented as internal video.render provider
```

따라서 다음 구현은 `clipper1_video_render`를 사용자 플러그인으로 키우는 것이 아니라,
production provider endpoint/key/billing 정책을 확정하고 Clipper Studio edit/re-render UX를 완성하는 방향이어야 한다.
상세 재설계 문서: `.codex/design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`

---

## 1. 세션 시작 기준 repo 상태

작업 시작 전 확인한 4개 Clipper2 repo 상태:

| repo | branch / status | latest commit |
|---|---|---|
| `clipper_angular` | `feature/initial-scaffold...origin/feature/initial-scaffold`, clean | `7da0fdc refactor: split projects page components` |
| `clipper_nestjs` | `feature/initial-scaffold...origin/feature/initial-scaffold`, clean | `35337dc feat: add source ingestion and provenance` |
| `clipper_python` | `feature/plugin-architecture...origin/feature/plugin-architecture`, clean | `780e00d feat: support source-prepared highlight jobs` |
| `clipper_electron` | `feature/initial-scaffold...origin/feature/initial-scaffold`, clean | `2064e19 feat: add YouTube auth host support` |

Clipper1 reference 상태:

| repo | branch / status | latest commit |
|---|---|---|
| `adlight_angular` | current checkout `feature/longform-highlight...origin/feature/longform-highlight [ahead 1]` | `c9d92a9 chore: ignore local agent docs` |
| `adlight_angular` reference branch | `feature/d2x-electron` exists locally/remotely | inspected with `git show`/`git grep`, checkout unchanged |
| `adlight_python` | current checkout `feature/longform-highlight...origin/feature/longform-highlight`, clean | `8b21428 chore: add NEXT_SESSION_PROMPT.md to .gitignore` |
| `adlight_python` reference branch | `feature/d2x-electron` exists locally/remotely | inspected with `git show`/`git grep`, checkout unchanged |

Reference docs read:

- `.codex/implementation/NEXT_SESSION_PROMPT.md`
- `.codex/design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
- `.codex/design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
- `adlight_angular/docs/clipper/*`
- `adlight_python/docs/clipper/*`
- `feature/d2x-electron` code in `adlight_angular` and `adlight_python`

---

## 2. Clipper1 기능 inventory

### 2.1 Product workflows

Clipper1/D2X의 핵심 사용자 workflow는 다음이다.

| workflow | 설명 | 현재 구현 위치 |
|---|---|---|
| Shortform create | prompt/URL/editor 입력을 받아 LLM으로 clip structure, 제목, 키워드를 만들고 media/TTS를 붙여 draft project 생성 | `ShortsProjectRouter`, `ShortsProjectService`, `GPTService`, Angular `ShortformComponent`, `ContentInput` class |
| Shortform edit/save | 생성된 프로젝트의 template/BGM/TTS/title/logo/clip media/subtitle를 편집하고 TEMP 저장 | `PATCH /v1/shorts/projects/{id}/save`, `ShortsProjectService._save_or_overwrite_project` |
| Shortform render | 편집 project를 media server 또는 local renderer로 보내 최종 mp4/thumbnail 생성 | `PATCH /v1/shorts/projects/{id}/create-video*`, `MediaService`, `VideoService` |
| Project library | user별 project list, completed/processing/temp 상태 표시, polling/SSE 동기화 | Angular `LibraryComponent`, `ProjectItemComponent`, `GET /v1/shorts/projects/user/{user_id}` |
| Clone project | 기존 project/clip/contents_input 복제 | `POST /v1/shorts/projects/{id}/clone`, `ShortsProjectService.clone_project` |
| Super Clone | client별 variation(template/BGM/TTS)을 적용해 다수 project shell 생성 후 TTS 재생성/render를 백그라운드 실행 | `SuperCloneService`, admin/user super-clone routers, Angular admin page/dialog |
| Media replace/search | clip media를 Naver/Kakao/Pixabay/Tenor/origin media에서 검색/교체 | `/v1/common/search/*`, Angular media dialogs |
| TTS regenerate | subtitle row/title change 시 TTS 재생성 및 subtitle duration 갱신 | `POST /v1/shorts/text-to-speech`, Angular subtitle/title components |
| Admin management | user/credit/error log/super clone client variation 관리 | `d2x-admin` module, admin routers |

비핵심 또는 별도 제품군 후보:

- TikTok upload/statistics routers: Clipper1 core shortform generation과 분리된 publishing capability 후보.
- `adlight/DownloadRouter` YouTube channel download: 현재 `fastapi_server.py`에서 `adlight_app.include_router`가 주석 처리되어 있지만, media/source provider 후보로 inventory에 포함한다.
- WRTN video path: `create_wrtn_video` 관련 코드는 일부 호출 흔적과 helper가 있으나 현재 `MediaService.create_video_request_for_local_wrtn`은 주석 처리 상태다. template/render capability 검토 자료로만 본다.

### 2.2 Angular surface

주요 화면/컴포넌트:

| UI area | route/component | 역할 |
|---|---|---|
| User app layout | `D2xLayoutComponent` | library/mypage shell |
| Create/edit | `/shortform`, `/shortform/:projectId`, `ShortformComponent` | input, template/BGM/TTS/media/title/subtitle editing |
| Library | `/library`, `LibraryComponent` | project list, SSE/polling, clone/super clone action |
| Project card | `ProjectItemComponent` | open, clone, super clone, delete, status display |
| Content input | `prompt-input`, `url-input`, `load-input`, `contents-input` | prompt/URL/editor source input |
| Media editing | `my-asset-dialog`, `template-select-dialog`, `clip-and-subtitle`, `subtitle-row`, `title-check` | clip media, template, subtitle/TTS controls |
| Admin | `/admin/d2x/super-clone`, `SuperCloneManageComponent` | client variation CRUD |

Angular API wrappers:

- `src/modules/d2x-client/apis/shorts.api.ts`
- `src/modules/d2x-client/apis/contents-input.api.ts`
- `src/modules/d2x-client/apis/common.api.ts`
- `src/modules/d2x-client/apis/templates.api.ts`
- `src/modules/d2x-admin/services/d2x-admin-super-clone.api.ts`

### 2.3 Backend storage entities

| entity/table | 핵심 필드 | Clipper2로의 의미 |
|---|---|---|
| `projects` / `ShortsProject` | `status`, `bgm_id`, `template_id`, `tts_id`, `tts_speed`, `thumbnail`, `video_url`, `video_duration`, title/logo flags/text | `ProjectManifest.outputs`, `TemplatePreset`, `RenderRecipe.projectOverlays`로 분해 |
| `clips` / `Clip` | `media_url`, `thumbnail_url`, `subtitles JSONB`, `order_num` | `ClipArtifact`, `RenderRecipe.timeline.items` |
| `contents_input` | `input_type`, `input_content`, `parsed_content`, `image_url`, `status` | `SourceInput`, `SourceAsset`, `workflow.clipper_studio.detail.source` |
| `templates` / `templates_jp` | `template`, `contents_ratio`, `origin_url`, `thumbnail_url`, `settings JSONB`, `name`, `category` | `TemplatePreset` catalog |
| `bgms` | `name`, `url` | `AudioAsset` / `audio.bgm` provider |
| legacy `tts` | `name`, `speaker`, `url` | old speaker catalog, superseded by richer TTS model/speaker catalog |
| `clipper_tts_*` via `app.models.adlight.TtsModel` | model/speaker/speed/language metadata | `tts.catalog` provider metadata |
| `super_clone_clients` | name/description | batch preset group |
| `super_clone_variations` | `template_id`, `bgm_id`, `tts_id`, `order_num` | `VariationPreset` or batch `RenderRecipe` overrides |

### 2.4 Project status model

Clipper1 statuses:

```text
CREATED -> TEMP -> QUEUED -> PROCESSING -> COMPLETED
                                      -> ERROR
```

Observed usage:

- `CREATED`: project draft returned after LLM/media/TTS initial generation.
- `TEMP`: user saved edited project.
- `QUEUED`: `VideoQueueService.enqueue` accepted render job.
- `PROCESSING`: render or super-clone shell in progress.
- `COMPLETED`: `video_url`/`thumbnail`/duration written.
- `ERROR`: render failure.

Clipper2 already has richer job/project snapshots. The Clipper1 status should map into `ProjectManifest.status` and job snapshots, not be imported as the only lifecycle model.

---

## 3. Endpoint inventory

### 3.1 Shortform project endpoints

Prefix: `/v1/shorts`

| method/path | purpose | main service/capability |
|---|---|---|
| `GET /upload-image-assets/{user_id}` | local uploaded image/video list | legacy local upload listing |
| `POST /upload-image/{user_id}` | upload user image/video to S3 `images/` | `asset.store` |
| `POST /projects` | create shortform project from input | `source.inspect/parse`, `llm.script`, `media.search`, `tts.synthesis`, `project.draft` |
| `POST /projects-auto` | unauthenticated/auto variant of create | same as above |
| `POST /projects-sse` | old streaming create endpoint, marked unused | superseded by event bus |
| `POST /projects/{id}/regenerate` | regenerate clips/title/media from new input | `llm.script`, `media.search`, `tts.synthesis` |
| `POST /projects/{id}/clone` | duplicate project, clips, contents_input | `project.clone` |
| `GET /projects/{id}` | project summary | `project.read` |
| `GET /projects/tmp/{id}` | TEMP project full detail | `project.read` |
| `GET /projects/data_all/{id}` | project + clips + contents_input for editor | `project.read.detail` |
| `GET /projects/user/{user_id}` | paged project library | `project.list` |
| `GET /projects/user/{user_id}/temp` | temp project list | `project.list` |
| `PATCH /projects/{id}/save` | save/edit project and clips | `project.update`, `asset.store` |
| `PATCH /projects/{id}/create-video` | render via local media service synchronously | `video.render` |
| `PATCH /projects/{id}/create-video-auto` | async/local render path | `video.render`, `queue.job` |
| `PATCH /projects/{id}/create-video-sse` | queued render with SSE status | `queue.job`, `video.render`, `events` |
| `POST /wrtn/create-video` | WRTN one-off render path | historical/render experiment |
| `POST /video/callback` | remote media server callback | `project.output.finalize` |
| `DELETE /projects/{id}` | soft delete | `project.delete` |
| `POST /projects/{id}/upload-logo-image` | upload logo image to S3 | `asset.store` |
| `POST /projects/{id}/upload-clip-image` | upload clip image to S3 | `asset.store` |
| `POST /text-to-speech` | synthesize one subtitle audio | `tts.synthesis` |
| `GET /projects/{id}/contents-input-images` | source/origin images for project | `source.asset.list` |
| `GET /super-clone/clients` | user-facing super-clone client list | `batch.preset.list` |
| `POST /projects/{id}/super-clone` | execute super clone batch | `project.clone`, `tts.synthesis`, `video.render`, `events` |

### 3.2 Content input endpoints

Prefix: `/v1/contents-input`

| method/path | purpose | capability |
|---|---|---|
| `POST /generate-informative-article` | user text -> article + clip structure | `llm.script` |
| `POST /generate-article-for-video` | user text -> video prompt + keyword | `llm.script` |
| `POST /generate-prompt-by-user-input` | user text -> prompt + keyword | `llm.script` |
| `GET /search-news` | Naver news search | `source.search.news` |
| `GET /get-news-headline-body` | Naver news scrape | `source.parse.url` |
| `POST /improve-prompt-using-news` | news + prompt -> improved prompt | `llm.script` |

### 3.3 Media/search endpoints

Prefix: `/v1/common`

| method/path | provider | output |
|---|---|---|
| `GET /search-gif-giphy` | Giphy | first GIF URL |
| `GET /search-gif-tenor` | Tenor | first GIF URL |
| `GET /search-jpg-pixabay` | Pixabay | first JPG URL |
| `GET /search/media` | Pixabay photo/video | paged `MediaSchema[]` |
| `GET /search/naver` | Naver Image | paged image results |
| `GET /search/kakao` | Kakao Image | paged image results |
| `GET /search/origin` | project `contents_input.image_url` | paged origin images |
| `GET /search/gif` | Tenor | paged GIF results |
| `GET /get-image` | CommonService download | temporary local image URL |
| `GET /get-shorts-default-data` | BGM + old TTS | initial editor data |
| `GET /get-shorts-default-data-v2` | BGM + rich TTS catalog | initial editor data |

Related routers/services:

- `MediaBookmarkRouter` and `MediaBookmarkService` store user-selected media bookmarks.
- `DownloadRouter`/`DownloadService` define YouTube channel download with `yt-dlp`, cookies, proxy, playlist range. It is not included in `fastapi_server.py` for `feature/d2x-electron`, but it is a strong source/media provider candidate.

### 3.4 Template/BGM/TTS endpoints

| prefix | method/path | purpose |
|---|---|---|
| `/v1/templates` | `GET /list` | default template catalog |
| `/v1/templates` | `GET /{template_id}` | template detail |
| `/v1/templates` | `POST /upload-csv*` | CSV/Google Sheet template import |
| `/v1/templates-japan` | `GET /list` | Japanese template catalog |
| `/v1/templates-japan` | `POST /upload-csv-from-google-sheet` | Japanese catalog import |
| `/v1/bgms` | `GET /bgm-list` | BGM list |
| `/v1/bgms` | `GET /tts-list` | old TTS voice list |
| `/v1/bgms` | `GET /tts/{id}` | old TTS voice detail |
| `/v1/tts` | `GET /models` | active TTS models |
| `/v1/tts` | `GET /models/{model_id}` | TTS model detail |
| `/v1/tts` | `GET /speakers` | active speakers |
| `/v1/tts` | `GET /speakers/{speaker_id}` | speaker detail |
| `/v1/tts` | `GET /models/{model_id}/speakers` | model speakers, optional language |
| `/v1/tts` | `GET /models/{model_id}/details` | model + speaker + speed data |
| `/v1/tts` | `GET /initial-data` | page initial TTS catalog |

### 3.5 Events, queue, admin

| prefix | method/path | purpose |
|---|---|---|
| `/v1/SSE` | `GET /notify/events/clip/{project_id}` | project generation progress events |
| `/v1/SSE` | `GET /notify/events/video/{project_id}` | video progress events |
| `/v1/SSE` | `GET /notify/events/manage?session_id=...` | library/manage events targeted by session |
| `/v1/SSE` | `GET /connections/count` | active SSE count |
| `/v1/admin/super-clone` | `GET/POST/PUT/DELETE /clients*` | client group CRUD |
| `/v1/admin/super-clone` | `GET/POST /clients/{id}/variations` | variation list/create |
| `/v1/admin/super-clone` | `PUT/DELETE /variations/{id}` | variation update/delete |

Important event lesson:

- The 2026-04-03 fix changed event targeting from "last subscribed session" to request `session_id`.
- Clipper2 already moved to WebSocket `/v1/events` with owner scoping. The Clipper1 event semantics should map to the Clipper2 event broker, not reintroduce the old global fallback.

---

## 4. Service inventory

### 4.1 Core project services

| service | responsibilities | capability boundary |
|---|---|---|
| `ShortsProjectService` | project create/regenerate/clone/save/list/render payload/finalize/delete/TTS wrapper | currently too broad; split into project orchestration, project repository, source/script/media/TTS/render adapters |
| `GPTService` | input parsing, URL/blog parsing, GPT call, JSON repair | `source.parse.url`, `llm.script` |
| `ContentsInputService` | contents_input CRUD, origin media paging, Gemini prompt/article generation | split into `source.input.repository`, `llm.script` |
| `MediaService` | prepare payload, remote media server call, local `VideoService` call, project finalize/error logging | `video.render` orchestrator/provider adapter |
| `VideoQueueService` | single-slot queue, QUEUED/PROCESSING status, manage SSE events | Clipper2 `JobQueue` already supersedes this |
| `SuperCloneService` | client/variation CRUD, clone shells, apply variation, TTS regeneration, render background tasks | `batch.render_variations` workflow over shared capabilities |

### 4.2 Script/content services

| service | responsibilities |
|---|---|
| `GPTService.process_and_call_gpt` | converts input type/content/tone/as-is/language to `GPTResponseSchema` clip structure |
| `GPTService._parse_url_content` | Naver blog, Tistory, Brunch, general URL parsing |
| `GeminiService` | Gemini API calls for prompt/article generation |
| `NewsCrawlService`, `ScrapeService`, `NaverNewsService` | news search/scrape and article body extraction |

### 4.3 Media providers

| provider/service | responsibilities |
|---|---|
| `NaverImageService` | Naver image search, URL validation |
| `KakaoImageService` | Kakao image search fallback, URL validation |
| `PixabayService` | photo/video search, paged result mapping |
| `TenorService` / `GiphyService` | GIF search |
| `S3FileUploaderService` | upload local file or URL to S3 paths |
| `LocalFileUploaderService` | local filesystem upload path and URL mapping |
| `DownloadService` | yt-dlp channel download with cookies/proxy/range, not active in current server include |

### 4.4 TTS services

| service | responsibilities |
|---|---|
| `TtsService` | active model/speaker/speed catalog, speaker lookup |
| `ClovaVoiceService` | external Clova synthesis, speed conversion, audio upload |
| `TtsOuteServiceWrapper` | local Oute TTS model loading and synthesis |
| `ShortsProjectService._process_tts_for_clips` | batch synthesis for generated clip subtitles |
| `ShortsProjectService.convert_text_to_speech` | one-off subtitle row synthesis |
| `SuperCloneService._regenerate_tts_for_project` | rebuild all subtitle `tts_url`/duration after TTS variation change |

### 4.5 Template/render services

| service | responsibilities |
|---|---|
| `TemplatesService` | default template DB read/import from CSV/Google Sheet |
| `TemplatesJapanService` | Japanese template catalog read/import |
| `VideoService` | local render engine using MoviePy, PIL, ffmpeg, S3 upload |
| `WrtnVideoService` | one-off WRTN overlay/render experiment using `VideoService` helpers |

---

## 5. Template inventory

Clipper1 template model:

- Table: `templates`, `templates_jp`
- `template_id` identifies both visual design and content ratio row.
- `template` is the design number.
- `contents_ratio` is one of `16:9`, `4:3`, `1:1`, `full`.
- `origin_url` and `thumbnail_url` are catalog assets.
- `settings` is a large JSONB object.

Important `settings` groups observed in `ShortsTemplateSettingsSchema` and `VideoService`:

| group | examples |
|---|---|
| canvas/content | `contents_area_y_offset`, `layout_image`, ratio-specific content area height |
| title fonts | `sub_title_font`, `main_title_font`, `bottom_title_font`, `logo_text_font`, `subtitle_font` |
| font sizes/colors | `*_font_size`, `*_color`, `main_title2_color`, `subtitle_font_color` |
| placement | `*_y_offset_*`, `*_left_align_margin`, `*_right_align_margin` |
| spacing | `*_tracking` |
| boxes | `*_box_color`, `*_box_alpha`, `*_box_padding_left_right`, `*_box_height`, subtitle border settings |
| outline/shadow | `*_outline_width`, `*_outline_color`, `*_shadow_*` |
| logo | `logo_image_y_offset`, `logo_image_area_height`, `logo_image_area_width`, `logo_text_y_offset` |
| audio | `bgm_volume` is read by `VideoService` even if not declared in the schema excerpt |

Ratio mapping in `VideoService.calculate_contents_area_height`:

| ratio | content area height |
|---|---:|
| `16:9` | 608 |
| `4:3` | 810 |
| `1:1` | 1080 |
| `full` | 1920 |

Migration implication:

- A Clipper1 template row should become a `TemplatePreset`.
- Raw legacy `settings` should be preserved in `TemplatePreset.params.legacySettings` during initial import.
- A normalization layer can later project legacy fields into stable render slots and style params.
- `templates_jp` should be a locale/catalog variant, not a separate renderer.

---

## 6. Media download/cache inventory

Current media behavior:

1. Input URL/editor parsing extracts original images.
2. `S3FileUploaderService.upload_from_url` copies original images to `project/{projectId}/image/origin/*`.
3. For each clip, `_find_media_for_clips` selects media:
   - original images first when available,
   - Pixabay video/photo,
   - Naver image,
   - Kakao image,
   - Tenor/GIF path depending on UI/provider.
4. On save/render, `s3_upload_clip_media_urls` uploads non-S3 `clip.media_url` to S3 and mirrors it into `thumbnail_url`.
5. `VideoService` downloads remote media/TTS/layout/BGM into a local temp directory for rendering.
6. Final mp4 and thumbnail are uploaded to S3.

Storage paths from uploaders:

| artifact | S3/local path pattern |
|---|---|
| origin images | `project/{projectId}/image/origin/{file}` |
| clip media | `project/{projectId}/image/clip/{file}` or `project/{projectId}/video/{file}` |
| logo | `project/{projectId}/image/logo/{file}` |
| thumbnail | `project/{projectId}/image/thumbnail/{file}` |
| TTS | `tts/{file}` |
| general images | `images/{file}` |

Clipper2 implication:

- Search and download must be separate capabilities:
  - `media.search`: returns provider result references.
  - `media.download`: materializes a remote URL as an `AssetArtifact`.
  - `asset.store`: owns local/S3/object-store destination.
- `source.ingest` for YouTube/local files already exists in Clipper2 and should not be duplicated by Clipper1 media download code.

---

## 7. TTS inventory

Clipper1 has two overlapping TTS models:

1. Old `tts` table used by `/v1/bgms/tts-list`.
2. Rich `app.models.adlight.TtsModel` model/speaker catalog used by `/v1/tts/*` and `ShortsProjectService.convert_text_to_speech`.

Synthesis flow:

```text
subtitle text[] + tts_model_id + tts_speaker_id + speed
  -> TtsService speaker lookup
  -> model_id dispatch
      1: ClovaVoiceService
      2: TtsOuteServiceWrapper
  -> mp3/wav generation
  -> upload URL
  -> SubtitleSchema { subtitle, tts_url, duration }
```

Super Clone dependency:

- TTS variation changes are not metadata-only.
- Because render consumes `clip.subtitles[].tts_url`, changing `tts_id` requires regenerating audio files and updating subtitle JSONB.

Clipper2 implication:

- `tts.catalog` and `tts.synthesis` are shared capabilities.
- `clipper_studio` should never call Clova/Oute directly.
- Render recipes should reference `AudioTrack` artifacts, not mutable `tts_url` strings embedded only in clip subtitles.

---

## 8. Render inventory

Current render modes:

| mode | flow |
|---|---|
| remote media server | `MediaService.create_video_request` -> `POST {MEDIA_SERVER_URL}/v1/video/create` -> callback `/v1/shorts/video/callback` |
| local render | `MediaService.create_video_request_for_local` -> `VideoService.create_video` -> project finalize |
| queued local render | `VideoQueueService` -> `MediaService.create_async_video_request` -> `VideoService.create_video` |
| super clone render | `SuperCloneService._background_generate_videos` -> `MediaService.create_video_request_for_local` |

`VideoService.create_video` responsibilities:

- create OS-safe temp directory;
- calculate content area from ratio;
- download layout image, media clips, TTS audio, BGM, logo;
- turn image/GIF/video media into per-clip video segments;
- generate title/subtitle/logo text images with PIL fonts, boxes, outlines, shadows, tracking;
- build ffmpeg filter graph for layout/title/subtitle/logo/BGM/TTS mixing;
- render final mp4;
- extract first-frame thumbnail;
- upload final mp4 and thumbnail to S3;
- return `VideoCreateCallbackSchema(success, project_id, data.video_url, data.thumbnail_url, duration)`;
- cleanup local temp directory.

Important boundary issue:

- `VideoService` currently combines template application, subtitle composition, media normalization, final render, and artifact upload.
- In Clipper2, these are separate capabilities:
  - `template.apply`: TemplatePreset + workflow output -> RenderRecipe
  - `subtitle.compose`: subtitle text/timing/style -> subtitle overlay tracks
  - `video.render`: RenderRecipe -> video artifact
  - `asset.store`: store outputs and return artifact references

---

## 9. Project output inventory

Clipper1 project output is DB/S3-oriented:

```text
projects row
  status, template_id, bgm_id, tts_id, tts_speed,
  title/logo flags/text,
  video_url, thumbnail, video_duration

clips rows
  media_url, thumbnail_url,
  subtitles: [{ subtitle: string[], tts_url, duration }],
  order_num

contents_input row
  input_type, input_content, parsed_content, image_url[]

S3
  project/{id}/image/origin/*
  project/{id}/image/clip/*
  project/{id}/image/logo/*
  project/{id}/image/thumbnail/*
  project/{id}/video/*
  tts/*
```

Clipper2 project output is file/manifest-oriented:

- `CLIPPER_DATA_DIR/projects/files/<projectId>`
- project snapshot/detail in NestJS
- `sourceAssets` and provenance
- dialog/dance-specific detail builders

Target direction:

- Keep DB rows only if/when remote service mode needs them.
- Local desktop Clipper2 should produce `ProjectManifest` plus artifacts.
- `clipper_studio` output detail should be a presenter over the common manifest, not a legacy DB schema clone.

---

## 10. Shared capability decomposition

### 10.1 Workflow vs capability

User-visible workflow plugins:

| workflow id | purpose |
|---|---|
| `workflow.dialog_highlight` | longform dialog highlight extraction |
| `workflow.dance_highlight` | longform dance/person highlight extraction |
| `workflow.clipper_studio` | Clipper1-style AI shortform generation and editing |
| `workflow.super_clone` or batch action | variation batch generation over an existing project |

Shared capabilities:

| capability | providers | initial home |
|---|---|---|
| `source.inspect` | local file, YouTube, URL/news parser, text prompt | NestJS |
| `source.ingest` | local file, yt-dlp, URL text parser | NestJS + host tools |
| `llm.script` | OpenAI, Gemini, remote Adlight LLM proxy | NestJS facade, remote provider |
| `media.search` | Naver, Kakao, Pixabay, Tenor, Giphy, origin project assets | NestJS facade |
| `media.download` | HTTP downloader, yt-dlp, provider-specific downloader | NestJS + Electron/host tool when needed |
| `asset.store` | local filesystem, S3/object storage | NestJS abstraction |
| `tts.catalog` | Clipper legacy DB import, remote catalog | NestJS |
| `tts.synthesis` | Clova, Oute/local, future remote TTS | NestJS provider + Python/local worker if needed |
| `subtitle.compose` | basic text timing, TTS-derived timing, style tracks | NestJS or Python helper |
| `template.catalog` | legacy templates, built-in presets, remote catalog | NestJS |
| `template.apply` | legacy template adapter, native Clipper2 template engine | NestJS service |
| `video.render` | local ffmpeg, legacy VideoService adapter, future remote render farm | Python worker or NestJS-managed host tool |
| `project.manifest` | manifest builder/normalizer | NestJS |
| `queue.events` | Clipper2 JobQueue + WebSocket events | NestJS |

### 10.2 Why not one giant plugin

If Clipper1 is imported as one `clipper_studio` Python plugin that owns LLM, media search, TTS, templates, renderer, output schema:

- dialog/dance cannot reuse templates or TTS without calling a product workflow plugin;
- provider credentials and remote LLM policy leak into a local compute worker;
- resource dashboard cannot distinguish a heavy renderer from a lightweight template catalog;
- output manifests remain workflow-specific and `/projects` must learn every legacy shape;
- super clone remains an internal special case instead of a batch orchestration pattern.

Correct decomposition:

```text
workflow.clipper_studio
  declares inputs, screens, pipeline graph, presenter
  calls shared capabilities:
    source.ingest
    llm.script
    media.search
    media.download
    tts.synthesis
    template.apply
    video.render
    project.manifest
```

### 10.3 Provider placement

| provider type | should live in | reason |
|---|---|---|
| LLM providers | NestJS facade + remote server | key policy, billing, auth, audit |
| search providers | NestJS | API routing/cache/rate policy |
| TTS remote providers | NestJS facade | key policy, provider routing |
| TTS local model | Python worker or host-managed local runtime | model lifecycle/resource use |
| legacy `VideoService` | initially Python worker/provider adapter | ffmpeg/MoviePy/PIL-heavy compute |
| ffmpeg binary | Electron host install/telemetry, invoked through provider | packaged OS path concern |
| asset storage | NestJS `ArtifactStorage` | local/object storage substitution |

---

## 11. Minimum ProjectManifest schema draft

This is a schema direction, not an implementation commitment.

```ts
export interface ProjectManifest {
  schemaVersion: 'project-manifest.v1';
  projectId: string;
  ownerSubjectId?: string;
  workflow: {
    id: string;
    version?: string;
    displayName?: string;
  };
  title: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'interrupted';
  createdAt: string;
  updatedAt: string;
  sourceAssets: SourceAsset[];
  outputs: ProjectOutput[];
  artifacts: ProjectArtifact[];
  summary: ProjectSummary;
  detail: DialogProjectDetail | DanceProjectDetail | ClipperStudioProjectDetail | Record<string, unknown>;
  provenance: {
    appVersion?: string;
    jobId?: string;
    parentProjectId?: string;
    retryOfJobId?: string;
    importedFrom?: {
      system: 'clipper1' | 'clipper2' | string;
      legacyProjectId?: string | number;
      branch?: string;
    };
  };
}

export interface ProjectOutput {
  id: string;
  kind: 'render' | 'clip' | 'analysis' | 'draft' | 'batch';
  label: string;
  artifactIds: string[];
  primaryArtifactId?: string;
  thumbnailArtifactId?: string;
  renderRecipeId?: string;
  templatePresetId?: string;
  durationSec?: number;
  width?: number;
  height?: number;
  createdAt: string;
  metadata?: Record<string, unknown>;
}

export interface ProjectArtifact {
  id: string;
  kind:
    | 'source.video'
    | 'source.image'
    | 'source.audio'
    | 'source.text'
    | 'source.unknown'
    | 'analysis.transcript'
    | 'analysis.entity'
    | 'media.image'
    | 'media.video'
    | 'audio.tts'
    | 'audio.bgm'
    | 'subtitle.track'
    | 'template.preset'
    | 'render.recipe'
    | 'render.video'
    | 'render.thumbnail'
    | 'debug.log';
  uri: string;
  storage: 'local' | 's3' | 'object' | 'remote';
  access?: {
    kind: 'project-file' | 'source-file' | 'remote-url';
    path?: string;
    url?: string;
  };
  mediaType?: string;
  sizeBytes?: number;
  checksum?: string;
  sourceAssetId?: string;
  provider?: string;
  createdAt: string;
  metadata?: Record<string, unknown>;
}

export interface ProjectSummary {
  sourceLabel?: string;
  thumbnailArtifactId?: string;
  primaryOutputId?: string;
  counts?: {
    clips?: number;
    renders?: number;
    entities?: number;
  };
  badges?: string[];
}
```

Required common fields:

- `workflow.id`
- `status`
- `sourceAssets`
- at least one `ProjectOutput` for successful render workflows
- artifacts with stable ids instead of raw paths scattered through detail DTOs
- workflow-specific `detail` allowed, but every file/media reference should also be represented as an artifact

Implementation note from Phase C smoke:

- `uri` is the provider/storage URI, while `access` tells the UI which serving route can open it.
  - `project-file`: project output relative path, served by `GET /v1/projects/:projectId/file?path=...`
  - `source-file`: source cache/local input path, served by `GET /v1/sources/file?path=...`
  - `remote-url`: direct remote URL
- Generated ids must be ASCII and collision-resistant. Non-ASCII label/path parts are encoded as Unicode code points, e.g. `모카` -> `_ubaa8_uce74`.

---

## 12. Output artifact model by workflow

### 12.1 Dialog highlight

Current shape:

- source video asset;
- generated highlight clips;
- clip thumbnails;
- transcripts/subtitle text;
- rendered shorts clips.

Draft detail:

```ts
export interface DialogProjectDetail {
  kind: 'dialog_highlight';
  clips: Array<{
    id: string;
    outputId: string;
    renderArtifactId: string;
    thumbnailArtifactId?: string;
    title?: string;
    startSec?: number;
    endSec?: number;
    dialogText?: string;
    score?: number;
    reason?: string;
  }>;
  transcriptArtifactId?: string;
}
```

### 12.2 Dance highlight

Current shape:

- source video asset;
- reference images;
- mapped members/persons;
- person render videos;
- person clip lists;
- mapped/unmapped person metadata.

Draft detail:

```ts
export interface DanceProjectDetail {
  kind: 'dance_highlight';
  entities: Array<{
    id: string;
    label: string;
    entityType: 'person' | 'member';
    mappedMember: boolean;
    referenceArtifactIds?: string[];
    thumbnailArtifactId?: string;
  }>;
  renders: Array<{
    id: string;
    entityId: string;
    outputId: string;
    renderArtifactId: string;
    thumbnailArtifactId?: string;
    clipIds: string[];
  }>;
  clips: Array<{
    id: string;
    entityId?: string;
    renderArtifactId?: string;
    startSec?: number;
    endSec?: number;
    thumbnailArtifactId?: string;
  }>;
}
```

### 12.3 Clipper Studio / Clipper1

Current shape:

- `contents_input` source;
- `projects` row with template/BGM/TTS/title/logo settings;
- `clips` rows with media/subtitles/TTS URLs;
- final `video_url` and `thumbnail`;
- optional super-clone batch shells and variation outputs.

Draft detail:

```ts
export interface ClipperStudioProjectDetail {
  kind: 'clipper_studio';
  input: {
    mode: 'prompt' | 'url' | 'editor' | 'imported';
    text?: string;
    parsedTextArtifactId?: string;
    originImageArtifactIds?: string[];
  };
  script?: {
    artifactId?: string;
    mainTitle1?: string;
    mainTitle2?: string;
    subTitle?: string;
    bottomTitle?: string;
    totalKeywords?: string[];
  };
  editState: {
    templatePresetId?: string;
    bgmArtifactId?: string;
    ttsProviderId?: string;
    ttsSpeakerId?: string;
    ttsSpeed?: number;
    logoArtifactId?: string;
    logoText?: string;
    titleVisibility?: {
      subTitle: boolean;
      mainTitle: boolean;
      bottomTitle: boolean;
      logo: boolean;
    };
  };
  clips: Array<{
    id: string;
    order: number;
    mediaArtifactId: string;
    thumbnailArtifactId?: string;
    subtitleTrackArtifactId?: string;
    ttsArtifactIds?: string[];
    subtitles: Array<{
      text: string[];
      startSec?: number;
      endSec?: number;
      ttsArtifactId?: string;
      durationSec?: number;
    }>;
  }>;
  variations?: Array<{
    id: string;
    label: string;
    templatePresetId?: string;
    bgmArtifactId?: string;
    ttsSpeakerId?: string;
    outputId?: string;
    status: ProjectManifest['status'];
  }>;
}
```

---

## 13. TemplatePreset draft

```ts
export interface TemplatePreset {
  schemaVersion: 'template-preset.v1';
  id: string; // e.g. legacy.clipper1.template.7.ratio.9x16 or shorts.basic_letterbox
  displayName: string;
  category: 'shorts' | 'news' | 'education' | 'commerce' | 'highlight' | string;
  locale?: string;
  aspectRatio: '9:16' | '16:9' | '4:3' | '1:1' | 'full' | string;
  canvas: {
    width: number;
    height: number;
    fps?: number;
    backgroundColor?: string;
  };
  preview?: {
    imageArtifactId?: string;
    videoArtifactId?: string;
    remoteImageUrl?: string;
    remoteVideoUrl?: string;
  };
  slots: TemplateSlot[];
  defaultParams: Record<string, unknown>;
  requiredAssets?: Array<{
    id: string;
    kind: 'font' | 'layout_image' | 'overlay_image';
    uri: string;
  }>;
  capabilities: {
    requires: string[]; // e.g. subtitle.compose, video.render.ffmpeg
  };
  compatibility?: {
    workflows?: string[];
    sourceMediaTypes?: string[];
    minDurationSec?: number;
    maxDurationSec?: number;
  };
  legacy?: {
    source: 'clipper1';
    table: 'templates' | 'templates_jp';
    templateRowId: number;
    templateDesignId?: number;
    contentsRatio?: string;
    rawSettings: Record<string, unknown>;
  };
}

export interface TemplateSlot {
  id: string;
  type: 'video' | 'image' | 'text' | 'subtitle' | 'audio' | 'logo';
  required: boolean;
  accepts?: string[];
  defaultBinding?: string;
  params?: Record<string, unknown>;
}
```

Initial presets:

| preset id | meaning |
|---|---|
| `shorts.basic_letterbox` | current dialog/dance hardcoded 9:16 black-padding shorts render |
| `legacy.clipper1.template.{template}.ratio.{ratio}` | imported Clipper1 template row |
| `legacy.clipper1.jp.template.{template}.ratio.{ratio}` | imported Japanese template row |

---

## 14. RenderRecipe draft

```ts
export interface RenderRecipe {
  schemaVersion: 'render-recipe.v1';
  id: string;
  projectId: string;
  outputId?: string;
  templatePresetId: string;
  sourceAssetIds: string[];
  timeline: {
    durationSec?: number;
    fps?: number;
    items: RenderTimelineItem[];
  };
  tracks: {
    video: VideoTrack[];
    audio: AudioTrack[];
    subtitles?: SubtitleTrack[];
    overlays?: OverlayTrack[];
  };
  templateParams: Record<string, unknown>;
  output: {
    label: string;
    width: number;
    height: number;
    aspectRatio: string;
    format: 'mp4' | 'mov';
    videoCodec?: 'h264' | 'hevc' | string;
    audioCodec?: 'aac' | string;
    destination?: {
      storage: 'local' | 's3' | 'object';
      relativePath?: string;
    };
  };
  provenance: {
    createdByCapability: 'template.apply' | 'workflow' | string;
    createdAt: string;
    legacy?: {
      source: 'clipper1';
      templateId?: number;
      projectId?: number | string;
    };
  };
}

export interface RenderTimelineItem {
  id: string;
  clipId?: string;
  sourceArtifactId: string;
  mediaType: 'video' | 'image' | 'gif';
  startSec: number;
  durationSec: number;
  sourceRange?: {
    startSec?: number;
    endSec?: number;
  };
  fit?: 'cover' | 'contain' | 'fill';
  crop?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  effects?: Array<{
    id: string;
    type: 'zoom' | 'pan' | 'fade' | 'none' | string;
    params?: Record<string, unknown>;
  }>;
}

export interface VideoTrack {
  id: string;
  role: 'main' | 'layout' | 'overlay' | 'logo';
  items: RenderTimelineItem[];
}

export interface AudioTrack {
  id: string;
  role: 'tts' | 'bgm' | 'source' | 'effect';
  artifactId: string;
  startSec: number;
  durationSec?: number;
  volume?: number;
  loop?: boolean;
}

export interface SubtitleTrack {
  id: string;
  artifactId?: string;
  items: Array<{
    text: string[];
    startSec: number;
    durationSec: number;
    styleRef?: string;
    ttsArtifactId?: string;
  }>;
}

export interface OverlayTrack {
  id: string;
  role: 'main_title' | 'sub_title' | 'bottom_title' | 'logo' | 'template';
  artifactId?: string;
  text?: string;
  startSec?: number;
  endSec?: number;
  styleRef?: string;
  params?: Record<string, unknown>;
}
```

Mapping from Clipper1:

- `projects.template_id` -> `templatePresetId`
- `projects.bgm_id` / BGM URL -> `AudioTrack(role='bgm')`
- `clips[].media_url` -> `RenderTimelineItem.sourceArtifactId`
- `clips[].subtitles[].tts_url` -> `AudioTrack(role='tts')` and subtitle item `ttsArtifactId`
- `projects.main_title*`, `sub_title`, `bottom_title`, logo fields -> `OverlayTrack`
- template `settings` -> `templateParams.legacySettings`

---

## 15. Migration plan

Implementation should proceed in small vertical slices. This section is the plan; no implementation has been done in this document step.

### Phase A: Contracts only

1. Add TypeScript DTO drafts in `clipper_nestjs` for `ProjectManifest`, `ProjectArtifact`, `ProjectOutput`, `TemplatePreset`, `RenderRecipe`.
2. Keep them internal first; do not expose new public APIs until the current dialog/dance detail builder can map to them.
3. Add manifest fixture examples for:
   - dialog highlight output,
   - dance highlight output,
   - Clipper1 imported output.

### Phase B: Manifest adapter for current Clipper2

1. Extend current dialog/dance project detail builder to emit common artifact/output ids alongside existing detail DTOs.
2. Name the existing shorts render as `shorts.basic_letterbox`.
3. Keep Angular UI compatible with existing `ProjectRenderItem`/detail shapes while adding common fields.

Implementation note from 2026-05-04:

- `ProjectManifestBuilder` now exposes dialog/dance outputs through `GET /v1/projects/:projectId/manifest`.
- Existing dialog/dance detail APIs remain unchanged.
- `TemplatePresetCatalogService` exposes `GET /v1/template-presets`.
- `RenderRecipeProvider` exposes `GET /v1/projects/:projectId/outputs/:outputId/render-recipe`.
- The current dialog/dance shorts outputs use `templatePresetId = shorts.basic_letterbox`.
- The first recipe provider describes current completed outputs as pass-through render recipes over their primary output artifact. It is a compatibility bridge, not the final editable timeline model.

### Phase C: Capability registry skeleton

1. Add read-only `CapabilityRegistry` and `ProviderRegistry` in NestJS.
2. Register existing providers:
   - `source.ingest.local_file`
   - `source.ingest.yt_dlp`
   - `video.analyze.dialog_worker`
   - `video.analyze.dance_worker`
   - `asset.store.local`
3. Add placeholder providers for Clipper1:
   - `llm.script.legacy_openai`
   - `media.search.naver`
   - `media.search.kakao`
   - `media.search.pixabay`
   - `tts.synthesis.clova`
   - `tts.synthesis.oute`
   - `template.catalog.legacy_clipper1`
   - `video.render.legacy_ffmpeg`

### Phase D: Clipper1 catalog import, not workflow import

1. Import Clipper1 template rows into a `TemplatePreset` catalog file or local DB table.
2. Preserve raw legacy `settings`; add normalized minimal fields only where needed.
3. Import BGM/TTS speaker catalogs as provider metadata.
4. Do not copy `ShortsProjectService` as-is. Extract only provider adapters behind capability interfaces.

Implementation note from 2026-05-04:

- `TemplatePresetCatalogService` composes `TemplatePresetSource` providers instead of directly seeding fixtures.
- Current sources:
  - `BuiltInTemplatePresetSource`
  - `LegacyClipper1TemplatePresetSource`
- Clipper1 templates enter through `LegacyClipper1TemplateRow` and `legacyClipper1TemplateRowToPreset`.
- The supported row shape mirrors `templates` / `templates_jp`:
  - `id`
  - `template`
  - `contents_ratio`
  - `origin_url`
  - `thumbnail_url`
  - `settings`
  - `name`
  - `category`
  - `table`
  - `locale`
- Raw `settings` are preserved as `TemplatePreset.defaultParams.legacySettings` and `legacy.rawSettings`.
- The source abstraction is ready for a local JSON catalog first, then DB/remote catalog sources later.

### Phase E: `workflow.clipper_studio` vertical slice

1. Start with prompt/text input only.
2. Use shared `llm.script` mock/adapter to produce clip structure.
3. Use one media provider and one TTS provider.
4. Use one imported `TemplatePreset`.
5. Produce a `RenderRecipe`, then render through a `video.render` provider.
6. Store output as `ProjectManifest` artifacts.
7. Add Super Clone only after single render manifests are stable.

Implementation note from 2026-05-04:

- `LegacyClipper1RenderRecipeProvider` converts `ClipperStudioProjectDetail` into `RenderRecipe`.
- Current mapping:
  - `clips[].mediaArtifactId` -> `RenderTimelineItem.sourceArtifactId`
  - `clips[].subtitles[]` -> `SubtitleTrack.items`
  - `subtitles[].ttsArtifactId` -> `AudioTrack(role='tts')`
  - `editState.bgmArtifactId` -> `AudioTrack(role='bgm')`
  - `script` + `editState.titleVisibility` -> `OverlayTrack`
  - legacy template preset `defaultParams.legacySettings` -> `RenderRecipe.templateParams`
- This is still a recipe generation step only. It does not yet execute legacy `VideoService` or a Clipper2 `video.render` provider.

Implementation note from the Clipper Studio shell/draft slices:

- `workflow.clipper_studio` now exists as a user-facing virtual workflow descriptor.
- Angular `/clipper-studio` is a real project creation screen, not a headless worker card.
- `POST /v1/projects/clipper-studio` creates a Clipper Studio project shell with embedded `project-manifest.v1`.
- `POST /v1/projects/:projectId/clipper-studio/draft-jobs` runs deterministic prompt/text draft generation as a persisted NestJS job.
- Draft jobs support `queued/running/succeeded/failed/cancelled` status, progress polling, and cancel.
- `ClipperStudioScriptGenerator` now owns the `llm.script` facade, with `DeterministicClipperStudioScriptGenerator` as the current provider.
- `/projects` can reopen the Clipper Studio project and show script/clip plan through a dedicated presenter.
- `ClipperStudioAssetPreparer` now creates bundled seed media/layout/logo artifacts, local OS TTS artifacts, and fallback seed artifacts where needed.
- `output.clipper-studio.render.main` can build a legacy Clipper1 `RenderRecipe` and execute through `video.render.legacy_clipper1.python_worker`.
- Packaged smoke produced `renders/main.mp4` and `renders/main_thumbnail.jpg` from a Clipper Studio project.
- Render job result is promoted back into the project manifest final artifact state after job polling.
- Angular Clipper Studio detail now previews the completed render MP4 and uses the thumbnail artifact as the video poster.
- Angular render job polling reloads the manifest after terminal render status so the preview updates without reopening the project.
- Clipper Studio edit-state can be patched through NestJS and is reflected in the next render recipe.
- Angular Clipper Studio detail can patch title visibility, logo text, and TTS speed through that edit-state boundary.
- Angular Clipper Studio detail can select a Clipper1 template preset from the template catalog.
- Clipper1 template catalog currently comes from `src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`; DB/remote catalog is still a future source.
- Remaining gap: production provider endpoint/key/billing policy and actual endpoint operations must be added, and final MP4/thumbnail preview needs visual QA plus re-render/version-state polish.

Implementation note from the follow-up slice:

- `VideoRenderProvider` is now the render execution contract.
- `LegacyClipper1RenderPayloadMapper` maps `RenderRecipe` into the legacy media server / `VideoService.create_video` payload:
  - `recipe.provenance.legacy.projectId` -> `project_id`
  - legacy template preset id/settings -> `template_id`, `contents_ratio`, `template_settings`
  - timeline items -> `clips[].media_url`
  - subtitle + TTS tracks -> `clips[].subtitles`
  - BGM track -> `bgm_url`
  - overlays -> legacy project title/logo fields
- `LegacyClipper1VideoRenderProvider` exists as a dry-run provider only.
- Actual render execution still needs an adapter that decides whether legacy `VideoService` runs in Python, a local host worker, or a future remote render service.

Implementation note from the render job skeleton slice:

- `VideoRenderProviderRegistry` now lists and resolves render providers by recipe compatibility.
- Provider descriptors expose:
  - provider id
  - execution mode (`dry_run`, `local`, `python-worker`, `remote`)
  - availability status
  - dry-run flag
  - capability ids
- `VideoRenderJob` snapshots are persisted separately from pipeline jobs.
  - store: `CLIPPER_DATA_DIR/render-jobs/render-jobs.json`
  - status: `queued`, `running`, `succeeded`, `failed`, `cancelled`
  - result: `VideoRenderResult`
  - history: lifecycle events
- Project APIs now expose the render execution boundary:
  - `GET /v1/projects/:projectId/outputs/:outputId/render-providers`
  - `POST /v1/projects/:projectId/outputs/:outputId/render-jobs`
  - `GET /v1/projects/:projectId/render-jobs`
  - `GET /v1/projects/:projectId/render-jobs/:renderJobId`
- Registered Clipper1 render providers now include the dry-run payload mapper and the Python-worker-backed execute provider.
- Dialog/dance recipes currently surface provider compatibility as `canRender: false`; they are not silently rendered by the Clipper1 adapter.
- Next execution steps are no longer only render-parity-focused. The user-facing `workflow.clipper_studio` vertical slice must come before more renderer polish.

Implementation note from the Python-worker boundary slice:

- `clipper_python/plugins/clipper1_video_render` now exists as a dedicated worker plugin.
  - It uses the standard PluginRuntime `/jobs` + WebSocket event contract.
  - It advertises `video.render.legacy_clipper1`.
  - It validates and records the legacy render payload in `dry_run` mode.
  - It now has a first-pass `execute` adapter that writes local MP4 and thumbnail files.
- `LegacyClipper1PythonWorkerRenderProvider` now exists in NestJS.
  - provider id: `video.render.legacy_clipper1.python_worker`
  - execution mode: `python-worker`
  - dry-run-only flag: `false`
  - submits the mapped legacy payload to plugin `clipper1_video_render`
  - waits for plugin WebSocket completion and maps it back to `VideoRenderResult`
- This confirms the intended control-plane split:
  - NestJS chooses provider, creates jobs, maps recipe/payload, and records results.
  - Python worker owns the render execution boundary.
  - Actual legacy template effect and template-specific subtitle parity still need to be extracted from Clipper1 `VideoService` without copying it into NestJS.

Implementation note from the first executable adapter slice:

- `LocalRenderAdapter` inside `clipper1_video_render` is the first executable adapter.
  - It resolves local media relative to `output_root`.
  - It converts each image/video clip to a normalized vertical MP4 segment.
  - It now places media inside the legacy content area derived from `contents_ratio` and `contents_area_y_offset`.
  - It can use a local `template_settings.layout_image` as the render background.
  - It can overlay a local `project.logo_image` when `logo_type = IMAGE`.
  - It applies recipe-declared image `zoom` and `pan` effects from `RenderRecipe.timeline.items[].effects`.
  - If an image clip has no recipe-declared motion effect, it now selects a deterministic legacy-style automatic image motion:
    - ratio difference `<= 0.3`: zoom
    - wide image: horizontal pan
    - tall image: vertical pan
    - pan travel uses legacy min/max speed bounds and deterministic direction selection instead of runtime randomness.
  - It concatenates segments into `recipe.output.destination.relativePath`.
  - It writes a thumbnail beside the output video.
- A basic ASS text overlay layer now exists.
  - `clips[].subtitles[].subtitle` / `duration` are converted to per-segment ASS events.
  - subtitle font size/color/outline and y positions are read from legacy `template_settings`.
  - main/sub/bottom title text overlays are also emitted as ASS events using legacy y offsets and style settings.
  - optional legacy font directories are passed to ffmpeg through `fontsdir`.
- A basic audio mixing layer now exists.
  - local `clips[].subtitles[].tts_url` files are normalized to subtitle durations and concatenated in clip order.
  - missing TTS audio or clip tail gaps are padded with silence so the audio timeline stays aligned.
  - local `payload.bgm_url` is looped/trimmed to render duration and mixed with TTS through ffmpeg `amix`.
  - the final mixed audio is muxed into the output MP4 as AAC.
- Current limitations are explicit:
  - video/GIF input motion parity is not complete yet
  - remote media/layout/logo/TTS/BGM URL staging exists per render job, but persistent cache/asset registration policy is not implemented yet
- This adapter is intentionally smaller than legacy `VideoService`; it proves the artifact/output boundary first.

---

## 16. Open decisions

1. Should `workflow.super_clone` be a separate workflow plugin or a batch action available to any project with compatible `RenderRecipe` overrides?
   - Current recommendation: batch action/capability first, workflow only if it needs its own product screen.
2. Should legacy `VideoService` initially run inside `clipper_python` as a worker or inside `clipper_nestjs` as a host binary adapter?
   - Current recommendation: Python worker/provider adapter because MoviePy/PIL/ffmpeg-heavy logic is Python-centered.
3. Should Clipper1 remote providers call production APIs directly from local NestJS?
   - Current recommendation: no for LLM/TTS paid providers in production. Use remote provider/proxy for keys, billing, entitlement.
4. How much of legacy `settings` should be normalized before import?
   - Current recommendation: import raw first, normalize incrementally as `template.apply` needs stable cross-workflow fields.
5. Should local desktop continue using S3 URLs for generated media?
   - Current recommendation: no as the default. Use `ArtifactStorage` local paths first; support S3/object storage through the existing abstraction for server mode.

---

## 17. Immediate next steps

The immediate next step is now replacing placeholder Clipper Studio providers and adding edit/re-render workflow, not another headless render worker card.

Completed in the first user-visible `workflow.clipper_studio` vertical slice:

1. `workflow.clipper_studio` descriptor and Store/Dashboard workflow/runtime split.
2. Angular `/clipper-studio` project creation screen.
3. NestJS Clipper Studio project shell with `detail.kind = 'clipper_studio'`.
4. `/projects` Clipper Studio presenter.
5. prompt/text deterministic draft generation as a persisted job with progress/cancel.
6. bundled seed media/TTS/logo/layout project-file artifacts. Silent BGM default generation has been removed.
7. render through `video.render.legacy_clipper1.python_worker`.
8. manifest promotion of the completed MP4/thumbnail.
9. final render preview in the Clipper Studio detail.
10. manifest refresh after render job completion so the preview appears in-place.
11. edit-state PATCH for title visibility/logo text/TTS speed and recipe reflection.
12. Angular controls for title visibility/logo text/TTS speed.
13. Angular Clipper1 template catalog select.
14. JSON file source for the local Clipper1 template catalog.
15. Angular project-artifact BGM/logo image selects.
16. Stale render action wording for re-render flow.
17. Angular clip media selects backed by project media artifacts.
18. Render recipe clip source override through `editState.clipMediaArtifactIds`.
19. Clipper Studio TTS preset catalog endpoint and Angular select.
20. Render version artifacts preserved under `renders/versions/<jobId>/`.
21. Angular render version labels and version MP4 links.
22. Angular final render empty preview.
23. Local image/video media import as `media.local_user.file` artifact and clip media override.
24. Local macOS TTS synthesis as `tts.local_os.say` artifact with seed TTS fallback.
25. Naver/Kakao media search result import as `media.search.*.image` artifact and clip media override.
26. HTTP(S) image/video media download as project `draft/assets/search_media/` artifact.
27. Bundled legacy BGM catalog as `audio.bgm.legacy_bundle` artifacts.
28. User BGM/logo imports as `audio.bgm.local_user.file` / `logo.local_user.file` artifacts and render recipe overrides.
29. Remote proxy/OpenAI-compatible `llm.script` provider boundary with legacy GPT response normalization.
30. Script-generated clip search queries used as media search defaults.
31. Script-generated clip search queries auto-download first media search result into `draft/assets/auto_search_media/` when media search credentials are available.
32. Remote media search proxy can be configured with `CLIPPER1_MEDIA_SEARCH_ENDPOINT`.
33. Script/title/clip subtitle/search query/duration can be edited in the Clipper Studio detail screen; edited subtitles generate new TTS artifacts.

Next:

1. Decide production provider endpoint/key/billing policy and connect real endpoints behind provider adapters.
2. Run visual QA and polish error/re-render states.
3. Run visual QA on final render preview.
4. Continue render parity work after the above path exists.
   - template-specific subtitle styling
   - video/GIF motion parity
   - persistent remote asset cache
   - object storage/CDN long render E2E
