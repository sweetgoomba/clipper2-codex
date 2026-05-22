# Legacy Clipper1 Template System

작성일: 2026-05-06
상태: reference 분석 완료, Clipper2 재설계 전 기준 문서

## 범위

이 문서는 현재 Clipper2에 이미 붙어 있는 템플릿 구현을 기준으로 삼지 않는다. 사용자가 명시한 대로, 원래 Clipper1/D2X의 템플릿 시스템을 다음 reference에서 다시 조사한 결과만 정리한다.

- `adlight_angular` branch `feature/d2x-electron`
- `adlight_python` branch `feature/d2x-electron`

주요 확인 파일:

- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/apis/templates.api.ts`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/interfaces/templates-api.interface.ts`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/datas/template.data.ts`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/components/title-check/*`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/components/dialogs/template-select-dialog/*`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/components/video-preview/*`
- `adlight_angular@feature/d2x-electron:src/modules/d2x-client/components/shorform-buttons/*`
- `adlight_python@feature/d2x-electron:app/models/TemplateModel.py`
- `adlight_python@feature/d2x-electron:app/models/TemplateJapanModel.py`
- `adlight_python@feature/d2x-electron:app/schemas/TemplateSchema.py`
- `adlight_python@feature/d2x-electron:app/schemas/ShortsProjectSchema.py`
- `adlight_python@feature/d2x-electron:app/services/TemplatesService.py`
- `adlight_python@feature/d2x-electron:app/services/ShortsProjectService.py`
- `adlight_python@feature/d2x-electron:app/services/api/MediaService.py`
- `adlight_python@feature/d2x-electron:app/services/VideoService.py`

## 한 줄 결론

기존 Clipper1의 템플릿은 "선택 가능한 UI 스킨" 정도가 아니라, DB row와 `settings` JSONB, 레이아웃 이미지, 폰트 파일, 제목/로고 표시 상태, 콘텐츠 비율, FFmpeg overlay 좌표가 모두 연결된 렌더 recipe에 가깝다.

따라서 Clipper2에서는 현재 붙어 있는 단순 preset 형태를 버리고, legacy `TemplatePreset`을 다음 단위로 복원해야 한다.

- catalog metadata: `id`, `template`, `contents_ratio`, `origin_url`, `thumbnail_url`, `name`, `category`
- render settings: legacy `settings` JSONB 전체
- project overlay state: title/logo check, title/logo text/image, logo type
- renderer contract: 1080 x 1920 좌표계, content area, overlay order
- preview contract: Angular-native preview가 renderer와 같은 recipe에서 파생되어야 함

## 데이터 구조

### Template row

Python의 `Template` 모델은 `templates` 테이블이다.

```text
templates
  id              int primary key
  template        int
  contents_ratio  enum TemplateRatio
  origin_url      text
  thumbnail_url   text
  settings        JSONB
  name            string nullable
  category        string nullable
```

일본어용은 같은 구조의 `templates_jp` 테이블이다. `ShortsProjectService.prepare_media_server_payload()`에서 `project.language == 'japanese'`이면 `templates_jp`, 아니면 `templates`를 조회한다.

### Ratio

Python enum:

```text
16:9
4:3
1:1
full
```

Angular UI에서는 `full`을 사용자에게 `9:16` 라벨로 보여준다.

Python renderer의 실제 content area 높이:

```text
16:9 -> 608
4:3  -> 810
1:1  -> 1080
full -> 1920
```

공통 기준은 항상 output size `1080 x 1920`이다.

### Template assets

`adlight_python@feature/d2x-electron:template/`에는 legacy template image asset이 들어 있다.

파일 패턴:

```text
template/{templateNumber}_ratio_{ratio}_origin.png
template/{templateNumber}_ratio_{ratio}_thumb.png
template/black_bg.jpg
template/white_bg.jpg
```

관찰한 asset 수는 177개다. 주된 template number는 `1`부터 `21`까지이며, 각 template number가 4개 ratio의 origin/thumb 이미지를 가진다. 일부 구형 파일(`1.png`, `2.png`, ...), 배경 파일, 한글 파일명 asset도 함께 존재한다.

DB row의 `thumbnail_url`은 Angular template 선택 dialog에서 사용된다. `origin_url`은 모델/schema/upload에는 있지만, 확인한 Angular preview/render 경로에서는 직접 사용하지 않았다. 실제 렌더에 쓰는 레이아웃 이미지는 `settings.layout_image`다.

Clipper2에서는 기존 Clipper1 UI asset을 다음처럼 분리해서 가져간다.

- `thumbnail_url`에 대응하는 작은 grid/list 이미지는 bundled `thumb` asset으로 serve한다.
- `origin_url`에 대응하는 큰 preview 이미지는 bundled `origin` asset으로 serve한다.
- 영상 render 배경은 계속 `settings.layout_image`가 기준이며, Clipper2 local source는 Python worker package 내부 `clipper1_video_render/legacy_assets/layout`이다. 원본 import source는 `adlight_python/layout`이다.
- 즉 UI용 `thumb/origin`과 render용 `layout_image`는 서로 다른 asset 역할이다.

현재 Clipper2 local bundle 위치:

```text
clipper_nestjs/src/projects/assets/legacy-clipper1-template-ui/thumbs-and-origins/
```

Serve endpoint:

```text
GET /v1/template-presets/legacy-clipper1/assets/{template}_ratio_{ratio}_{thumb|origin}.png
```

재수입 command:

```bash
cd clipper_nestjs
npm run import:legacy-template-ui-assets -- --dry-run
```

Render layout bundle 위치:

```text
clipper_python/plugins/clipper1_video_render/clipper1_video_render/legacy_assets/layout/
```

Renderer resolution order:

1. `CLIPPER_LEGACY_ASSETS_DIR`
2. Python package 내부 `legacy_assets`
3. dev fallback `cwd`
4. dev fallback `cwd.parent/adlight_python`

재수입 command:

```bash
cd clipper_python
uv run python scripts/import_legacy_clipper1_layout_assets.py --dry-run
```

Catalog coverage validation:

```bash
cd clipper_python
uv run python scripts/validate_legacy_clipper1_layout_catalog.py
```

현재 legacy Korean catalog 기준 검증 결과는 84 rows, 32 unique layout files, missing 0이다.

Render smoke command:

```bash
cd clipper_python
uv run python scripts/render_legacy_clipper1_template_smoke.py --duration 0.2 --fps 4
```

21개 design별 smoke:

```bash
cd clipper_python
uv run python scripts/render_legacy_clipper1_template_smoke.py --all-designs --duration 0.12 --fps 3
```

이 smoke는 pixel-level golden parity가 아니라, legacy template row + bundled layout + legacy text overlay + ffmpeg renderer가 실제 MP4/thumbnail artifact를 생성하는지 확인하는 단계다.

2026-05-08 기준 fixture 결정:

- 실제 legacy Clipper1 final render reference frame은 아직 workspace에 없다.
- `template/*_origin.png`와 `*_thumb.png`는 UI preview asset이므로 final render pixel golden으로 쓰지 않는다.
- true legacy parity fixture는 계속 `clipper_python/tests/fixtures/clipper1_golden_frames`에 둔다.
- 현재 Clipper2 smoke output은 별도 `clipper_python/tests/fixtures/clipper2_template_baseline_frames`로 승격했다.
- 이 baseline은 21개 template design의 `16:9` case와 ratio edge 4 case(`template-1-full`, `template-6-1_1`, `template-16-4_3`, `template-17-full`)를 포함한다.
- `clipper2_template_baseline_frames`는 current renderer regression baseline이며, legacy Clipper1 parity 증명은 아니다.
- baseline 재생성 command:

```bash
cd clipper_python
uv run python scripts/promote_legacy_template_smoke_baseline.py \
  --all-designs \
  --case 1:full \
  --case 6:1:1 \
  --case 16:4:3 \
  --case 17:full
```

## API 흐름

### Template catalog API

Angular:

```text
GET /v1/templates/list
```

구현:

- `TemplatesApi.getList()`
- `TemplatesRouter.templates_list()`
- `TemplatesService.get_all()`
- `TemplatesRepository.get_all()`

정렬은 `Template.id.asc()`다. ratio별 endpoint는 TODO로만 남아 있고 실제 UI는 전체 list를 받아 프론트에서 필터링한다.

일본어 catalog API도 있다.

```text
GET /v1/templates-japan/list
```

하지만 확인한 Angular 코드에서는 `templates-japan` API를 직접 호출하지 않는다. 생성 요청 단계에서 Python backend가 language에 따라 일본어 template table을 선택한다.

### CSV upload

템플릿 row는 CSV 또는 Google Sheet CSV export로 생성 가능하다.

- `POST /v1/templates/upload-csv`
- `POST /v1/templates/upload-csv-select-rows`
- `POST /v1/templates/upload-csv-from-google-sheet`
- `POST /v1/templates/upload-csv-from-google-sheet-select-rows`
- `POST /v1/templates-japan/upload-csv-from-google-sheet`

CSV row에서 `template`, `contents_ratio`, `name`, `category`, `thumbnail_url`, `origin_url`를 제외한 모든 컬럼을 `settings` 후보로 모은 뒤 `ShortsTemplateSettingsSchema`로 검증하고 JSONB에 저장한다.

## Angular 편집 흐름

### 초기 로딩

`D2XDataService.fetchDefaultData()`가 다음 두 요청을 병렬로 호출한다.

```text
templates.getList()
common.getDefaultDataV2()
```

로딩 후:

- `templateData.templates = templates`
- `templateData.currentTemplate = templates[0]`
- `templateData.templateMap[ratio] = templates.filter(...)`
- BGM catalog와 TTS model/speaker/speed도 같이 초기화한다.

### TemplateData

`TemplateData`는 legacy Angular 템플릿 상태의 중심이다.

주요 상태:

```text
previewWidth = 261
previewHeight = 455
imageWidth = previewWidth
imageHeight = ratio별 계산값
ratioOptions = 16:9, 4:3, 1:1, full(라벨 9:16)
currentRatio
currentTemplate
templates
templateMap
titlesForGeneration
titlesForInit
```

Preview 좌표 변환:

```text
adjustHeight(size) = previewHeight * size / 1920
adjustWidth(size)  = previewWidth  * size / 1080
```

주의: `previewWidth=261`, `previewHeight=455`는 정확한 9:16 축소값이 아니다. x/y 스케일이 서로 다른 비율로 줄어든다. 따라서 legacy preview는 최종 렌더와 완전히 동일한 픽셀 preview가 아니라 근사치다.

### Ratio 변경

ratio 변경 시 현재 선택된 template의 "ratio별 index"를 유지하려고 한다.

동작:

1. 현재 ratio의 template list에서 현재 template index를 찾는다.
2. 새 ratio의 template list에서 같은 index를 선택한다.
3. 없으면 새 ratio의 첫 template을 선택한다.

즉, 같은 `template` number나 같은 visual family id로 연결하는 구조가 아니라 list index 기반이다.

### Template 선택 dialog

`TemplateSelectDialogComponent`는 현재 ratio에 맞는 template만 보여준다.

좌측:

- thumbnail grid
- 각 item은 `thumbnail_url`

우측:

- 선택 template 큰 preview
- 적용 버튼

적용하면 `templateData.currentTemplate = result`가 된다.

### 오른쪽 스타일/레이아웃 패널

`TitleCheckComponent`가 오른쪽 패널 전체를 담당한다.

포함 UI:

- BGM select + 미리듣기
- TTS 재생 속도 select
- AI 목소리 select + 미리듣기
- ratio 선택
- template 변경 버튼
- title visibility checkbox
  - 서브
  - 메인
  - 하단
  - 로고
- preview
- 하단 shortform buttons

TTS voice나 speed를 변경하면 모든 clip subtitle에 대해 `POST /v1/shorts/text-to-speech`를 다시 호출하고 duration을 재계산한다.

### Title/logo 상태

Angular는 title 상태를 두 벌로 들고 있다.

`titlesForGeneration`:

- 최종 API 요청에 쓰는 값
- contenteditable keyup이 이 객체를 갱신
- check 상태도 여기에 있음

`titlesForInit`:

- 화면 초기 렌더링용 값
- legacy comment상 이벤트 중첩 문제 때문에 분리

필드:

```text
sub.text
sub.isChecked
main.text1
main.text2
main.isChecked
bottom.text
bottom.isChecked
logo.text
logo.isChecked
logo.logoIamge
logo.logoType = IMAGE | TEXT
```

### Preview

`VideoPreviewComponent`는 실제 mp4를 만드는 preview가 아니다. selected clip의 media, 현재 subtitle, template layer, title/logo overlay를 DOM/CSS로 근사 렌더한다.

구성:

1. root black stage: `261 x 455`
2. `settings.layout_image`를 배경으로 배치
3. `contents_ratio == 'full'`이면 같은 layout image를 media 위에 한 번 더 overlay
4. 현재 played clip media를 content area에 배치
5. title rows overlay
6. subtitle rows overlay
7. bottom title overlay
8. logo image 또는 logo text overlay

`app-title-row`는 `contenteditable` div를 absolute position으로 올린다. font, color, size, y/x offset, box color/alpha/padding/height, letter spacing, outline 유사 text-shadow를 template settings에서 받는다.

Preview에서 `subtitle`은 전체 timeline 재생이 아니라 사용자가 subtitle row를 클릭/재생했을 때 `clipData.playedClip`에 들어간 한 subtitle을 보여준다. 긴 문장은 Angular에서 `subtitlePerRowLength = 28` 기준으로 최대 두 줄로 쪼갠다.

### Preview y-offset 계산

Sub title:

- main title이 한 줄이면 `sub_title_y_offset_main_title_line_1`
- main title이 두 줄이면 `sub_title_y_offset_main_title_line_2`

Main title:

- 한 줄: `main_1st_title_y_offset_main_title_line_1`
- 두 줄:
  - line1: `main_1st_title_y_offset_main_title_line_2`
  - line2: `main_2nd_title_y_offset_main_title_line_2`

Subtitle:

- 일반 template:
  - 한 줄: `subtitle_1st_y_offset_subtitle_line_1`
  - 두 줄 line1: `subtitle_1st_y_offset_subtitle_line_2`
  - 두 줄 line2: `subtitle_2nd_y_offset_subtitle_line_2`
- template DB row id `36`만 예외 처리:
  - main title 한 줄 + subtitle 두 줄이면 line2를 `subtitle_1st_y_offset_subtitle_line_1 + 72`로 계산
  - Python renderer에도 같은 예외가 있다.

### Logo upload

Preview에서 logo image upload는 `uploadLogoImage(projectId, file)`를 호출한다. 확인한 branch에는 project id가 `297`로 하드코딩되어 있다.

이것은 legacy bug 또는 개발 중 임시 코드로 보인다. Clipper2에 가져오면 반드시 project/workspace id 기반으로 고쳐야 한다.

## 최종 생성 요청

`ShorformButtonsComponent.createShortformSSE()`가 `PATCH /v1/shorts/projects/{projectId}/create-video-sse`를 호출한다.

보내는 project payload:

```text
bgm_id
template_id
tts_model_id
tts_speaker_id
tts_speed
sub_title_check
main_title_check
bottom_title_check
logo_check
logo_type
sub_title
main_title1
main_title2
bottom_title
logo_image
logo_text
language
```

보내는 clips:

- 각 clip의 `media_url`
- `thumbnail_url`
- `order_num`
- `subtitles`
- 각 subtitle은 최종 요청에서 `subtitle: [subtitle.subtitle[0]]` 형태로 줄여 보내는 코드가 있다.

주의: schema상 subtitle은 `List[str]`라 여러 줄을 표현할 수 있지만, Angular 최종 요청은 각 subtitle의 첫 줄만 보내도록 되어 있다. 기존 preview의 줄바꿈과 backend subtitle wrapping이 완전히 같은 모델은 아니다.

## Python 생성 흐름

### Queue 진입

`PATCH /v1/shorts/projects/{id}/create-video-sse`

흐름:

1. session/credit 검증
2. `video_queue_service.enqueue(id, project_data, media_service, user_id, x_session_id)`
3. queue worker가 `MediaService.create_async_video_request()` 실행
4. `ShortsProjectService.prepare_media_server_payload()` 호출
5. `VideoService.create_video()` 호출

### prepare_media_server_payload

`ShortsProjectService.prepare_media_server_payload()`는 다음을 수행한다.

1. request project fields를 DB project에 반영
2. `project.tts_id = project_data.project.tts_speaker_id`
3. language가 `japanese`이면 `templates_jp`, 아니면 `templates`에서 `template_id` 조회
4. BGM URL 조회
5. title/logo 관련 project subset 생성
6. clip media URL을 S3 업로드/정규화
7. clip DB 업데이트
8. `ShortsCreateRequestToMediaServerSchema` 생성

Media server payload:

```text
project_id
project
contents_ratio
template_id
template_settings
bgm_url
clips
```

여기서 `template_settings`는 template row의 JSONB `settings` 그대로다.

## Python renderer 적용 방식

### 전체 크기와 content area

`VideoService.create_video()`는 다음 상수를 잡는다.

```text
video_height = 1920
contents_area_width = 1080
contents_area_height = ratio별 계산값
```

`contents_area_y_offset`은 template settings에서 읽는다.

즉 media content box는 다음으로 정의된다.

```text
x = 0
y = settings.contents_area_y_offset
width = 1080
height = ratio별 height
```

### 렌더 순서

큰 흐름:

1. layout image를 한 번 다운로드하고 검증한다.
2. 각 clip media를 개별 mp4 clip으로 변환한다.
3. title/subtitle/logo 텍스트를 PNG 이미지로 미리 만든다.
4. clip mp4들을 concat한다.
5. 필요하면 layout image를 최종 영상 위에 overlay한다.
6. title/subtitle/logo PNG를 순서대로 overlay한다.
7. TTS audio를 concat한다.
8. BGM이 있으면 TTS와 mix한다.
9. 최종 mp4와 thumbnail을 S3에 업로드한다.
10. local temp directory를 정리한다.

### Basic ratio와 full ratio의 차이

`contents_area_height < video_height`인 경우, 즉 `16:9`, `4:3`, `1:1`:

- clip media를 만들 때 layout image를 background로 깐다.
- media는 content area 안에 올라간다.
- 최종 concat 후에는 layout image를 다시 overlay하지 않는다.

`contents_area_height == video_height`인 경우, 즉 `full`:

- clip media를 만들 때 흰색 background를 사용한다.
- media는 사실상 1080 x 1920 full content area에 맞춰진다.
- 최종 concat 후 layout image를 `overlay=0:0`으로 한 번 더 올린다.

Angular preview도 같은 의도로 `full`일 때 layout image를 media 위에 한 번 더 그린다.

### Image media 처리

이미지 clip:

1. media URL 다운로드
2. image ratio와 content area ratio 차이를 계산
3. 차이가 `0.3` 이하이면 zoom 효과
4. 더 크면 pan 효과 후보
5. pan 이동 속도가 너무 느리면 zoom으로 fallback
6. MoviePy/PIL로 content area에 맞춰 crop/resize
7. layout or white background 위에 composite
8. mp4 clip으로 저장

### GIF/video media 처리

GIF:

- GIF duration이 clip duration보다 짧으면 loop
- content area에 맞춰 원본 GIF를 scale
- 같은 GIF를 blur background로도 깔고, 원본을 중앙 overlay
- clip duration만큼 mp4 생성

Video:

- source duration이 clip duration보다 짧으면 loop
- 길면 앞부분을 subclip
- content area에 맞춰 원본 video를 scale
- 같은 video를 blur background로 깔고, 원본을 중앙 overlay
- clip duration만큼 mp4 생성

### Title/subtitle/logo overlay 순서

최종 `filter_complex` overlay 순서:

1. clip videos concat -> `[v0]`
2. `full` ratio이면 layout image overlay -> `[v1]`
3. sub title
4. main title line1 shadow
5. main title line1 body
6. main title line2 shadow
7. main title line2 body
8. bottom title
9. timed subtitles
10. logo
11. format yuv420p

Logo가 subtitle보다 뒤에 올라오므로, 겹치면 logo가 더 위에 있다.

### Subtitle timing

Backend subtitle overlay는 전체 video timeline 기준으로 계산한다.

각 subtitle:

```text
start = current cumulative time
end = start + subtitle.duration
```

`subtitle.subtitle` 안에 여러 string이 있으면 각 string을 line으로 취급한다. 하지만 이후 `_generate_subtitle_images()`가 다시 `wrap_text_to_lines()`를 수행하므로, 실제 render line 수는 source array 길이와 달라질 수 있다.

FFmpeg overlay에는 다음 enable 조건이 들어간다.

```text
enable='between(t,start,end)'
```

### Text image 생성

텍스트는 FFmpeg drawtext가 아니라 PIL로 투명 PNG를 먼저 만든 뒤 FFmpeg overlay한다.

함수:

- `create_text_image()`
- `create_outline_text_image()`
- `adjust_font_size_to_fit()`
- `wrap_text_to_lines()`

지원하는 효과:

- font file
- font size
- text color
- letter spacing
- optional background box
- box opacity
- box left/right padding
- box height
- optional border
- optional outline
- optional shadow image
- max width 기준 font size 축소 또는 줄바꿈

폰트는 `adlight_python@feature/d2x-electron:fonts/` 아래의 파일명을 settings에서 직접 참조한다.

### Audio

최종 영상 audio:

1. clip subtitle별 TTS audio path를 입력으로 넣는다.
2. TTS audio를 concat한다.
3. BGM URL이 있으면 다운로드해 `volume={bgm_volume}` 적용 후 `amix`.
4. BGM이 없으면 TTS audio만 사용한다.

Renderer는 `template_settings.get("bgm_volume", 0.15)`를 읽는다. 그러나 `ShortsTemplateSettingsSchema`에는 `bgm_volume` 필드가 없다. CSV import 경로에서는 이 값이 정식 schema로 보존되지 않을 가능성이 있다.

## Template settings 전체 목록

아래 목록은 `ShortsTemplateSettingsSchema` 기준이다. Angular `Settings` interface도 대부분 같은 필드를 갖지만 nullable 여부와 일부 타입이 완전히 일치하지 않는다.

### Core layout

| field | 의미 |
|---|---|
| `contents_area_y_offset` | media content area가 영상 상단에서 떨어진 y 좌표 |
| `layout_image` | template layout/background image URL |

### Fonts

| field | 의미 |
|---|---|
| `sub_title_font` | 서브 타이틀 폰트 파일명 |
| `main_title_font` | 메인 타이틀 폰트 파일명 |
| `bottom_title_font` | 하단 타이틀 폰트 파일명 |
| `logo_text_font` | 로고 텍스트 폰트 파일명 |
| `subtitle_font` | 대사 자막 폰트 파일명 |

### Font sizes

| field | 의미 |
|---|---|
| `sub_title_font_size` | 서브 타이틀 크기 |
| `main_title_font_size` | 메인 타이틀 크기 |
| `bottom_title_font_size` | 하단 타이틀 크기 |
| `logo_text_font_size` | 로고 텍스트 크기 |
| `subtitle_font_size` | 대사 자막 크기 |

### Text colors

| field | 의미 |
|---|---|
| `sub_title_color` | 서브 타이틀 글자색 |
| `main_title_color` | 메인 타이틀 1줄/기본 글자색 |
| `main_title2_color` | 메인 타이틀 2번째 줄 글자색 |
| `bottom_title_color` | 하단 타이틀 글자색 |
| `logo_text_color` | 로고 텍스트 글자색 |
| `subtitle_font_color` | 대사 자막 글자색 |

### Y offsets

| field | 의미 |
|---|---|
| `sub_title_y_offset_main_title_line_1` | main title이 한 줄일 때 sub title y |
| `sub_title_y_offset_main_title_line_2` | main title이 두 줄일 때 sub title y |
| `main_1st_title_y_offset_main_title_line_1` | main title 한 줄 상태의 line1 y |
| `main_1st_title_y_offset_main_title_line_2` | main title 두 줄 상태의 line1 y |
| `main_2nd_title_y_offset_main_title_line_2` | main title 두 줄 상태의 line2 y |
| `bottom_title_y_offset` | bottom title y, null이면 template상 bottom title 없음 |
| `logo_text_y_offset` | text logo y |
| `logo_image_y_offset` | image logo y |
| `subtitle_1st_y_offset_subtitle_line_1` | subtitle 한 줄 상태 line1 y |
| `subtitle_1st_y_offset_subtitle_line_2` | subtitle 두 줄 상태 line1 y |
| `subtitle_2nd_y_offset_subtitle_line_2` | subtitle 두 줄 상태 line2 y |

### X alignment margins

왼쪽 margin이 있으면 `x = margin_left`, 오른쪽 margin이 있으면 `x = main_w-overlay_w-margin_right`, 둘 다 없으면 center다.

| field | 의미 |
|---|---|
| `sub_title_left_align_margin` | sub title 왼쪽 정렬 margin |
| `sub_title_right_align_margin` | sub title 오른쪽 정렬 margin |
| `main_title_left_align_margin` | main title 왼쪽 정렬 margin |
| `main_title_right_align_margin` | main title 오른쪽 정렬 margin |
| `bottom_title_left_align_margin` | bottom title 왼쪽 정렬 margin |
| `bottom_title_right_align_margin` | bottom title 오른쪽 정렬 margin |
| `subtitle_left_align_margin` | subtitle 왼쪽 정렬 margin |
| `subtitle_right_align_margin` | subtitle 오른쪽 정렬 margin |

### Logo image area

| field | 의미 |
|---|---|
| `logo_image_area_height` | image logo 영역 높이 |
| `logo_image_area_width` | image logo 영역 너비 |

Renderer는 image logo를 height 기준으로 scale한 뒤, `logo_image_area_width x logo_image_area_height` 영역으로 중앙 crop하고, 최종 x는 center다.

### Letter spacing

| field | 의미 |
|---|---|
| `sub_title_tracking` | sub title 자간 |
| `main_title_tracking` | main title 자간 |
| `bottom_title_tracking` | bottom title 자간 |
| `logo_text_tracking` | logo text 자간 |
| `subtitle_tracking` | subtitle 자간 |

### Main title outline/shadow

| field | 의미 |
|---|---|
| `main_title_outline_width` | main title outline 두께 |
| `main_title_outline_color` | main title outline 색 |
| `main_title_shadow_color` | main title shadow 텍스트 색 |
| `main_title_shadow_outline_width` | main title shadow outline 두께 |
| `main_title_shadow_outline_color` | main title shadow outline 색 |
| `main_title_shadow_x_offset` | schema상 shadow x offset |
| `main_title_shadow_y_offset` | schema상 shadow y offset |

주의: 확인한 `VideoService._create_final_video()` 경로에서는 `main_title_shadow_x_offset`, `main_title_shadow_y_offset`를 실제 overlay 좌표에 반영하지 않는다. shadow image를 본문과 같은 x/y에 먼저 overlay한다.

### Sub title box

| field | 의미 |
|---|---|
| `sub_title_box_color` | sub title background box 색 |
| `sub_title_box_alpha` | sub title background box 투명도 |
| `sub_title_box_padding_left_right` | sub title box 좌우 padding |
| `sub_title_box_height` | sub title box 높이 |

### Main title box

| field | 의미 |
|---|---|
| `main_title_box_color` | main title background box 색 |
| `main_title_box_alpha` | main title background box 투명도 |
| `main_title_box_padding_left_right` | main title box 좌우 padding |
| `main_title_box_height` | main title box 높이 |

### Subtitle box/border/outline/shadow

| field | 의미 |
|---|---|
| `subtitle_box_color` | subtitle background box 색 |
| `subtitle_box_alpha` | subtitle box 투명도 |
| `subtitle_box_padding_left_right` | subtitle box 좌우 padding |
| `subtitle_box_height` | subtitle box 높이 |
| `subtitle_box_border_color` | subtitle box border 색 |
| `subtitle_box_border_width` | subtitle box border 두께 |
| `subtitle_outline_width` | subtitle outline 두께 |
| `subtitle_outline_color` | subtitle outline 색 |
| `subtitle_shadow_color` | subtitle shadow 텍스트 색 |
| `subtitle_shadow_outline_width` | subtitle shadow outline 두께 |
| `subtitle_shadow_outline_color` | subtitle shadow outline 색 |
| `subtitle_shadow_x_offset` | schema상 subtitle shadow x offset |
| `subtitle_shadow_y_offset` | schema상 subtitle shadow y offset |

주의: 확인한 renderer 경로에서는 subtitle shadow x/y offset도 실제 overlay 위치에 반영되지 않는다.

## Legacy 불일치와 주의점

1. Preview와 final render는 같은 결과가 아니다.
   - Preview는 DOM/CSS 근사치다.
   - 실제 mp4를 재생하는 것이 아니다.
   - x/y scale도 서로 다르다.

2. `origin_url`은 template row에 있지만 runtime에서 거의 쓰이지 않는다.
   - 선택 dialog는 `thumbnail_url`.
   - preview/render는 `settings.layout_image`.

3. `full` ratio는 특별하다.
   - basic ratio는 clip 생성 시 layout을 background로 사용한다.
   - full ratio는 최종 concat 후 layout을 overlay한다.

4. template DB row id `36` 예외가 hardcode되어 있다.
   - subtitle y offset 계산이 일반 규칙과 다르다.
   - Angular preview와 Python renderer 양쪽에 예외가 있다.

5. shadow offset 필드는 schema/interface에는 있지만 실제 renderer에서 적용되지 않는다.

6. `bgm_volume`은 renderer에서 optional로 읽지만 schema에는 없다.

7. logo upload project id hardcode가 있다.
   - `VideoPreviewComponent`에서 `uploadLogoImage(297, file)` 호출.

8. title state가 `titlesForGeneration`과 `titlesForInit`으로 나뉘어 있다.
   - Clipper2에서는 단일 source of truth와 derived view model로 바꾸는 편이 맞다.

9. Angular 최종 생성 요청에서 subtitle array의 첫 번째 원소만 보내는 코드가 있다.
   - backend schema는 여러 줄 subtitle을 받을 수 있다.
   - 실제 줄바꿈은 backend `wrap_text_to_lines()`가 다시 수행한다.

10. template ratio 변경이 template family id가 아니라 list index 기반이다.
    - 같은 디자인의 다른 ratio variant를 안정적으로 매핑하려면 Clipper2에서는 `templateFamilyId` 같은 개념이 필요하다.

## Clipper1 정답 이미지 추출 기준

2026-05-08 기준 legacy render parity의 정답 이미지는 기존 Clipper1 `adlight_python`에서 직접 생성한다.

- 실행 경로:
  - `adlight_python/scripts/export_clipper1_reference_frames.py`
  - 내부적으로 기존 `app.services.VideoService.VideoService.create_video()`를 호출한다.
  - template id와 `contents_ratio`를 바꿔가며 실제 MP4를 만들고 첫 프레임 PNG를 저장한다.
- 입력:
  - `.codex/imports/legacy-clipper1-templates/templates.json`
  - `settings.layout_image`는 local HTTP server를 통해 `adlight_python/layout/{file}`로 제공한다.
  - synthetic media image와 silent TTS mp3도 local HTTP server로 제공해 기존 Clipper1 download 경로를 그대로 탄다.
- 출력:
  - 기존 Clipper1 입력 JSON
  - Clipper2 비교용 payload/recipe JSON
  - 첫 프레임 PNG
  - legacy MP4/thumbnail
  - manifest
- 확인 결과:
  - 단일 `template-1-16:9` export 성공.
  - 같은 입력으로 Clipper1을 두 번 렌더하면 첫 프레임 PNG hash가 동일했다.
  - 21개 design `16:9` + ratio edge 4개, 총 25개 export 성공.
  - raw strict 기준으로 현재 Clipper2와 첫 정답 이미지를 비교하면 `template-1-16_9`에서 mismatch ratio `0.154080`으로 실패한다.
  - 25개 전체를 `channelTolerance=32`로 비교하면 mismatch ratio는 `2.0%~3.8%` 범위다.
  - 같은 이미지를 2px 아래로 민 synthetic drift는 `channelTolerance=32`에서도 mismatch ratio `0.096489`이므로, `maxMismatchRatio=0.04`는 위치 어긋남을 잡는 1차 기준으로 채택했다.

`clipper_python/tests/fixtures/clipper1_golden_frames`에는 25개 정답 이미지 fixture가 생성되어 있다. 현재 기준은 완전 동일 픽셀이 아니라 영상 압축/고주파 배경/글자 edge 차이를 허용하는 1차 pixel 비교다. 다음 단계는 이 fixture를 유지하면서 template별 mismatch를 줄여 기준을 더 엄격하게 만드는 것이다.

## Clipper2로 가져갈 기준

### 유지해야 할 legacy semantics

- output coordinate system은 1080 x 1920을 기준으로 한다.
- template은 `contents_ratio`별 content area height를 가진다.
- `settings.layout_image`는 render에 직접 쓰이는 layout asset이다.
- title/logo visibility와 텍스트 값은 template catalog가 아니라 project/workspace state다.
- title/subtitle/logo는 final render에서 media 위에 overlay되는 별도 layer다.
- full ratio는 layout overlay timing이 basic ratio와 다르다.
- subtitle timing은 TTS duration 누적값으로 계산한다.

### 그대로 가져오면 안 되는 것

- 현재 legacy preview의 261 x 455 non-uniform scale
- `titlesForGeneration`/`titlesForInit` 이중 상태
- project id hardcode logo upload
- shadow offset 미적용 상태를 새 기능처럼 유지하는 것
- ratio variant 매핑을 list index에 의존하는 것
- template settings를 타입 없는 JSON blob으로만 방치하는 것

### Clipper2 권장 모델

```text
TemplatePreset
  id
  legacyTemplateId
  templateFamilyId
  ratio
  thumbnailArtifactId
  layoutArtifactId
  settings
  capabilities

TemplateSettings
  legacy-compatible fields
  validated schema version
  renderer defaults

ShortformRenderSettings
  templatePresetId
  ratio
  titleVisibility
  titleText
  logo
  bgm
  tts

RenderRecipe
  outputSize = 1080 x 1920
  contentArea
  mediaSlots
  overlayLayers
  audioMix
```

### Preview renderer 기준

Clipper2 preview는 legacy DOM preview를 그대로 복사하지 않는다.

필요한 방향:

- Angular-native renderer 유지
- 9:16 viewport는 정확한 uniform scale 사용
- preview와 final render가 같은 `RenderRecipe`에서 파생
- template image, media slots, subtitles, title/logo overlay order를 renderer와 동일하게 유지
- full ratio overlay 규칙을 명시적으로 모델링
- title/subtitle layout 계산을 공통 pure function으로 분리

### Migration 우선순위

1. legacy settings schema를 Clipper2 `TemplatePreset` schema로 보존한다.
2. template catalog source를 JSON/SQLite/seed artifact 중 하나로 정한다.
3. legacy layout/thumb assets를 project runtime에서 안정적으로 참조하게 만든다.
4. Angular template picker를 새 workspace 오른쪽 설정 패널에 붙인다.
5. preview renderer가 `TemplatePreset + RenderSettings + PreviewTimeline`을 받아 렌더하게 한다.
6. Python final renderer 또는 future renderer provider도 같은 recipe를 받게 한다.

## 현재 다음 작업에 대한 판단

템플릿을 시작하기 전, 먼저 catalog와 settings를 "대충 select box"로 처리하면 안 된다. 기존 Clipper1의 템플릿은 최종 렌더 좌표와 title/logo/subtitle layer 계약까지 포함한다.

따라서 Clipper2 다음 단계는 다음 순서가 맞다.

1. `TemplatePreset` catalog 계약 확정
2. legacy `settings` field 전체를 수용하는 schema 추가
3. Angular workspace 오른쪽 패널에 ratio/template/title/logo 설정 복원
4. preview renderer가 legacy field를 읽어 실제 위치에 표시
5. render recipe에 template overlay layer를 반영
