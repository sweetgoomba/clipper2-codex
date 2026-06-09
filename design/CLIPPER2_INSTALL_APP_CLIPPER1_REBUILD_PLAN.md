# Clipper2 Install App Clipper1 Rebuild Plan

작성일: 2026-06-09

Status: current implementation plan draft

이 문서는 최근 web/infra 작업 범위가 아니라 설치형 Clipper2 앱 범위의 Clipper1 재구현 계획을 정리한다.

대상 repo:

- `clipper_angular`
- `clipper_nestjs`
- `clipper_python`
- `clipper_electron`

참조 repo:

- `adlight_angular`
- `adlight_python`

핵심 방향:

> 기존 Clipper2의 단일 `clipper1`/`clipper-studio` workflow를 그대로 키우지 않는다. Clipper1 입력 방식을 각각 별도 user-facing plugin/workflow entry로 분리하고, 입력 이후 편집/템플릿/TTS/클립/render 영역은 shared Clipper1/Shortform editor로 재사용한다.

---

## 1. 사용자가 원하는 제품 변화

### 1.1 사이드 메뉴에서 Clipper1 직접 진입 제거

현재 `clipper_angular/src/shell/nav/nav.component.html`에는 `/clipper-studio`로 이동하는 "제작" nav item이 있다.

목표:

- 사이드 메뉴에서 단일 Clipper1/Clipper Studio 제작 메뉴를 제거한다.
- 사용자는 Store/Plugin 목록에서 원하는 입력 방식 plugin을 선택해 시작한다.
- `Clipper1 숏폼 제작`이라는 단일 plugin card도 제거한다.
- Clipper1 진입은 입력 방식별 plugin card로만 노출한다.

### 1.2 Clipper1 입력 방식별 plugin 분리

기존 Clipper1은 한 page 안에서 입력 방식을 tab으로 선택했다.

목표:

- 입력 방식별로 Store plugin card를 따로 만든다.
- 예:
  - `URL에서 숏폼 생성`
  - `복사 붙여넣기로 숏폼 생성`
  - `프롬프트로 숏폼 생성`
- 각 card의 `열기` 버튼은 해당 입력 방식 전용 화면으로 이동한다.
- 같은 page 안에서 URL/paste/prompt tab을 다시 보여주지 않는다.
- `수동 시작`은 Clipper1 plugin entry와 route에서 제외한다.

권장 plugin id:

```text
clipper1_url_shortform
clipper1_paste_shortform
clipper1_prompt_shortform
```

권장 route:

```text
/clipper1/url
/clipper1/paste
/clipper1/prompt
```

각 plugin은 user-facing workflow entry다. 실제 final render worker가 아니다.

### 1.3 입력 영역만 다르고 나머지는 공통 재사용

각 Clipper1 input plugin에서 달라지는 부분:

- URL 입력 form
- 복사 붙여넣기 form
- 프롬프트 form
- 해당 입력에서 draft/clip을 생성하는 시작 action

공통 재사용해야 하는 부분:

- clip list/editor
- media pool / media slot / media replace
- TTS 선택
- BGM 선택
- template 선택
- title/subtitle 편집
- preview
- render start
- render result 상태
- project/workspace save

권장 Angular 구조:

```text
features/clipper1/
  pages/
    clipper1-workflow-page.component.ts
      route data/inputMode를 받아 해당 input component 렌더링

  input/
    clipper1-url-input.component.ts
    clipper1-paste-input.component.ts
    clipper1-prompt-input.component.ts

  editor/
    clipper1-shared-editor.component.ts
      clip list / media / TTS / template / render controls

  preview/
    clipper1-preview.component.ts

  services/
    clipper1-workspace.service.ts
```

현재 `clipper_angular/src/features/clipper-studio/components/clipper1-input-panel.component.*`는 tab 기반이다. 이 component는 새 구조에서 폐기하거나 입력 방식별 component로 분해한다.

현재 `clipper_angular/src/features/clipper-studio/pages/clipper-studio-page.component.*`는 단일 Clipper1 page 역할을 한다. 새 구조에서는 route-level shell로 다시 만들거나 `features/clipper1` 아래로 재배치한다.

---

## 2. 레거시 Clipper1 참조 방식

### 2.1 참조 대상

레거시 Clipper1 기준 repo:

- `adlight_angular`
- `adlight_python`

참조해야 하는 내용:

- UI/UX 흐름.
- URL, prompt, paste/text editor 입력 방식.
- clip 생성 UX.
- clip/media editor UX.
- TTS/template/BGM 선택 UX.
- render request payload shape.
- `VideoService.py` 기반 ffmpeg render behavior.

### 2.2 복사 붙여넣기 금지

목표는 "기존 코드를 그대로 복사"가 아니다.

- UI/UX는 레거시와 동일하게 동작하게 다시 만든다.
- 레거시 Angular component/service를 그대로 가져오지 않는다.
- 레거시 Python API 구조를 그대로 가져오지 않는다.
- 레거시 behavior를 fixture/test/reference로 삼는다.

레거시 코드는 다음 용도로만 사용한다.

- 기능 inventory.
- request/response behavior reference.
- render payload reference.
- visual/reference behavior.
- 예외 처리 문구와 UX 흐름 참고.

---

## 3. Backend 책임 재분배

### 3.1 원칙

기존 `adlight_python`에서는 영상 생성뿐 아니라 project, contents input, media, TTS, template, queue 등 대부분의 API가 FastAPI에 있었다.

Clipper2에서는 다음처럼 나눈다.

```text
NestJS
  Clipper1 product API
  input parsing/orchestration
  script/clip generation provider calls
  media search/download/import
  TTS provider calls
  template catalog/apply
  workspace/project/queue/history
  RenderRecipe / VideoRenderJob

Python/FastAPI
  final video render execution
  ffmpeg-heavy logic
  VideoService.py-compatible render boundary
  progress/cancel/result

Electron
  packaged host
  ffmpeg/ffprobe install/readiness
  file dialogs and native path bridge

Angular
  input forms
  shared editor/preview
  Store/plugin entry
  job/project state display
```

### 3.2 NestJS로 옮길 레거시 FastAPI API 영역

NestJS로 이관할 것:

- URL input parsing endpoint.
- prompt/paste input draft generation.
- GPT/LLM script generation provider boundary.
- media search provider boundary.
- media download/import/cache.
- project/workspace create/update/delete/list.
- clip CRUD/edit.
- TTS synthesis provider boundary.
- BGM catalog/import.
- template catalog and template selection.
- render job creation and result promotion.
- Super Clone / Variation orchestration.
- job queue and project history.

Python/FastAPI에 남길 것:

- `VideoService.py` 계열 final render.
- ffmpeg filter graph / composition / muxing.
- final MP4 and thumbnail artifact generation.
- render progress/cancel/result.

이 기준은 `.codex/design/CLIPPER2_VIDEO_RENDER_OWNERSHIP.md`의 결론을 따른다.

### 3.3 VideoService.py 사용 방식

`adlight_python`의 `VideoService.py`는 render behavior reference로 유지한다.

가능한 방향:

- Clipper2 Python render worker에 `VideoService.py` behavior를 adapter로 포팅한다.
- NestJS는 legacy-compatible payload를 직접 만들기보다 provider-neutral `RenderRecipe`를 만들고, Python worker 또는 mapper가 render payload로 변환한다.
- 단기 이행에서는 mapper가 legacy-compatible payload를 만들 수 있다.

중요:

- bottom title, sub title, logo 같은 제거 대상 요소는 UI/API에서 더 이상 노출하지 않는다.
- render payload를 만들 때도 제거 대상 요소는 기본적으로 disabled/null로 보낸다.
- `VideoService.py` 내부에 해당 overlay if문이 남아 있어도, 입력 값이 disabled/null이면 overlay되지 않는 경로를 사용한다.
- 장기적으로는 Python render worker에서도 제거 대상 요소를 active feature로 취급하지 않는다.

---

## 4. Template 기능 축소

### 4.1 현재 구조

현재 Template Builder는 한 family에 여러 ratio variant가 붙는 구조다.

현재 ratio:

```text
16:9
4:3
1:1
full
```

현재 layer/role에는 다음 요소들이 있다.

- `subTitle`
- `mainTitleLine1`
- `mainTitleLine2`
- `bottomTitle`
- `subtitleText`
- `subtitleBox`
- `logoImage`
- `logoText`
- layout/content layer 등

관련 파일:

- `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- `clipper_angular/src/features/template-builder/models/template-builder.ts`
- `clipper_angular/src/features/template-builder/components/*`
- `clipper_nestjs/src/template-builder/template-builder-render-contract.ts`
- `clipper_python/plugins/clipper1_video_render/*`

### 4.2 목표 ratio 모델

한 template은 하나의 ratio만 가진다.

허용 ratio:

```text
1:1
4:3
```

목표:

- template 생성 시 ratio를 선택한다.
- 한 family 아래에 4개 ratio variant를 강제 생성하지 않는다.
- `16:9`와 `full`은 새 template 생성 UI에서 제거한다.
- 기존 데이터 migration은 별도 phase에서 처리한다.

권장 모델:

```text
Template
  id
  name
  ratio: '1:1' | '4:3'
  outputSize
  contentArea
  layers
  status
```

기존 `family -> variants[ratio]` 구조는 유지하더라도, 새 UX/API에서는 family당 variant 1개만 허용하는 compatibility 단계로 시작할 수 있다.

### 4.3 목표 layer 모델

남길 요소:

- main title 1
- main title 2
- subtitle 1
- subtitle 2

제거할 요소:

- sub title
- bottom title
- logo

여기서 "subtitle 1/2"는 레거시/현재 코드의 naming 혼동을 정리해야 한다.

권장 새 naming:

```text
mainTitleLine1
mainTitleLine2
captionLine1
captionLine2
```

compatibility mapping:

```text
mainTitleLine1 -> legacy main_title1
mainTitleLine2 -> legacy main_title2
captionLine1   -> legacy subtitle line 1
captionLine2   -> legacy subtitle line 2

removed sub title    -> disabled/null
removed bottom title -> disabled/null
removed logo         -> disabled/null
```

### 4.4 Template Builder UI 수정

해야 할 것:

- template create dialog에 ratio 선택 추가.
- ratio option은 `1:1`, `4:3`만 표시.
- family detail에서 4개 ratio tabs/variants를 제거하거나 단일 ratio editor로 축소.
- inspector에서 sub title, bottom title, logo 관련 panel 제거.
- canvas에서 sub title, bottom title, logo layer 제거.
- common style role에서 `subTitle`, `bottomTitle`, `logoText` 제거.
- sample render fixture도 제거된 layer를 disabled/null로 보낸다.

### 4.5 RenderRecipe/render worker 수정

해야 할 것:

- `RenderRecipe`와 template params에서 removed layer를 active layer로 만들지 않는다.
- Python render worker에 전달되는 payload에서 sub title, bottom title, logo를 사용하지 않는다.
- `VideoService.py` compatibility path를 쓰더라도 removed fields는 false/null/empty로 고정한다.
- existing templates/rendered outputs를 열어볼 때는 legacy compatibility를 유지할 수 있지만, 새 template 생성과 새 render path에서는 제거한다.

---

## 5. 작업 보관함 / output 통합

### 5.1 목표

작업 큐/작업 보관함 페이지는 모든 workflow output이 모이는 단일 장소여야 한다.

대상 output:

- dance highlight output.
- dialog highlight output.
- Clipper1 URL shortform output.
- Clipper1 paste shortform output.
- Clipper1 prompt shortform output.
- Clipper1 manual shortform output.
- Variation output.
- future workflow output.

### 5.2 모든 output에 template 적용 가능

모든 output은 template 적용 가능해야 한다.

구조:

```text
ProjectManifest output
  -> template selection
  -> RenderRecipe
  -> video.render job
  -> video.rendered artifact
```

현재 `ProjectsComponent`는 이미 job queue/history, project detail, `renderableOutputs`, `startVideoRender`, render provider list를 가진다. 이 구조를 강화해서 Clipper1/Variation뿐 아니라 highlight output도 같은 `template.apply -> video.render` 흐름에 태워야 한다.

필요한 정리:

- `ProjectManifest.outputs[]`가 모든 workflow에서 template-apply 가능해야 한다.
- output별 `templatePresetId`를 수정할 수 있어야 한다.
- output별 `renderRecipeId`를 안정적으로 만들 수 있어야 한다.
- detail panel이 workflow별 custom UI를 갖더라도 render controls는 공통화한다.
- render result artifact는 workflow와 무관하게 `video.rendered`로 정규화한다.

---

## 6. 현재 코드와 목표 구조 차이

### 6.1 Angular

현재:

- `PLUGIN_ROUTES`에서 `clipper1 -> /clipper-studio`.
- `WORKFLOW_ONLY_PLUGINS = ['clipper1', 'variation']`.
- nav에 `/clipper-studio` 제작 메뉴가 있음.
- `Clipper1InputPanelComponent`가 URL/prompt/paste 입력 UI를 가짐.
- `ClipperStudioPageComponent`가 단일 Clipper1 page 역할.

목표:

- `clipper1` 단일 Store entry 제거.
- 입력 방식별 plugin route 추가: `/clipper1/url`, `/clipper1/paste`, `/clipper1/prompt`.
- `/clipper-studio`, `/clipper1`, `/clipper1/manual` 호환 redirect를 남기지 않음.
- nav의 단일 제작 메뉴 제거.
- tab input panel 제거.
- input component와 shared editor component 분리.

### 6.2 NestJS

현재:

- `PLUGIN_CATALOG`에 `clipper1` virtual workflow가 있음.
- `VIRTUAL_WORKFLOW_PLUGINS`에 `clipper1`, `variation`.
- `Clipper1WorkspaceController`가 `/projects/clipper1/workspaces` 아래에 workspace API 제공.
- `Clipper1WorkspaceService`가 mode 기반 `create()`를 지원.
- `RenderRecipeProvider`, `VideoRenderJobsService`, provider registry가 이미 존재.

목표:

- `clipper1` virtual workflow를 입력 방식별 virtual workflow로 분해.
- 단일 `clipper1`/`clipper_studio` user-facing workflow manifest와 `clipper1_manual_shortform` manifest를 제거.
- workspace API는 공통 Clipper1 workspace API로 유지 가능하되, `source.mode`와 `workflowId`를 명확히 기록.
- legacy FastAPI product APIs를 NestJS service/provider로 이관.
- Python worker는 final render provider로만 사용.

### 6.3 Python

현재:

- `clipper1_video_render` Python plugin이 `video.render` provider/runtime 역할.
- 기존 render parity를 위해 legacy mapper/adapter가 존재.

목표:

- final render execution만 유지.
- removed template layer를 active feature로 취급하지 않음.
- Clipper1 new template payload를 지원.
- legacy `VideoService.py` behavior는 render reference/adapter로 활용.

### 6.4 Electron

현재:

- packaged process host, ffmpeg/model download, native file dialogs 역할.

목표:

- 큰 변경 없음.
- ffmpeg/ffprobe readiness와 packaged worker host 유지.
- Clipper1 입력 방식 분해는 Electron 책임이 아님.

---

## 7. 권장 phase plan

### Phase 0. Inventory and fixtures

목표:

- 레거시 `adlight_angular`, `adlight_python` Clipper1 기능 inventory 작성.
- 입력 방식별 request/response, UI flow, render payload 정리.
- 현재 Clipper2 `clipper-studio` 구현에서 폐기/재사용할 부분 분류.

검증:

- 문서상 API/use-case inventory 완료.
- 레거시 URL/prompt/paste flow별 fixture 후보 확보.

### Phase 1. Plugin entry split

목표:

- Store plugin list에 입력 방식별 Clipper1 entries 추가.
- 기존 `clipper1`/`clipper_studio` 단일 entry 제거.
- `수동 시작` entry는 만들지 않는다.
- nav에서 `/clipper-studio` 직접 메뉴 제거.
- routes: `/clipper1/url`, `/clipper1/paste`, `/clipper1/prompt`.
- `/clipper-studio`, `/clipper1`, `/clipper1/manual` redirect를 남기지 않는다.
- 각 route는 아직 기존 shared page shell을 쓰되 input mode를 고정한다.

검증:

- Store에서 각 plugin card `열기`가 올바른 route로 이동.
- page 안에 input tab이 보이지 않음.
- 기존 dance/dialog/variation route 영향 없음.

### Phase 2. Angular Clipper1 page rebuild

목표:

- `features/clipper1` 새 구조 생성.
- input components 분리.
- shared editor component 구성.
- 레거시 UI/UX를 기준으로 재구현하되 코드 복붙 금지.
- 현재 `clipper-studio` route/page 진입점은 제거하고, 필요한 내부 코드는 `features/clipper1` 구조로 옮기거나 재구현한다.

검증:

- 각 입력 방식에서 workspace 생성 가능.
- 입력 이후 공통 clip/editor/template/TTS 영역 재사용.
- Angular component tests.

### Phase 3. NestJS Clipper1 product API migration

목표:

- URL/prompt/paste input handling을 NestJS provider/service로 정리.
- legacy FastAPI product API 중 non-render 영역을 NestJS로 이관.
- workspace/project/clip/media/TTS/template operations를 NestJS source of truth로 확정.

검증:

- URL 입력으로 draft/clip 생성.
- paste 입력으로 draft/clip 생성.
- prompt 입력으로 draft/clip 생성.
- render 전까지 Python API 직접 호출 없음.

### Phase 4. Template simplification

목표:

- ratio `1:1`, `4:3`만 허용.
- template당 하나의 ratio만 허용.
- sub title, bottom title, logo 제거.
- main title 1/2, caption/subtitle 1/2만 유지.
- Angular/NestJS/Python contract 동시 정리.

검증:

- 새 template 생성 시 ratio 선택은 `1:1`, `4:3`만 가능.
- builder UI에 removed layer controls 없음.
- sample render에 removed layer overlay 없음.
- render payload에 removed layer disabled/null.

### Phase 5. Unified output templating

목표:

- 작업 보관함에서 모든 workflow output이 template 적용 가능.
- dance/dialog/clipper1/variation output을 `ProjectManifest.outputs[] -> RenderRecipe -> video.render` 흐름으로 통일.
- render controls 공통화.

검증:

- highlight output에도 template picker/render action 표시.
- Clipper1/Variation output도 같은 render job list에 표시.
- render result artifact가 workflow와 무관하게 preview 가능.

### Phase 6. Render worker cleanup

목표:

- Python `clipper1_video_render` worker가 새 simplified template contract를 1차 지원.
- legacy-only layer dependency 제거 또는 compatibility path로 격리.
- `VideoService.py` behavior를 필요한 범위에서 adapter로 유지.

검증:

- 1:1 template render 성공.
- 4:3 template render 성공.
- removed layer가 나타나지 않음.
- progress/cancel/result 유지.

---

## 8. 우선순위

첫 구현 단위는 Phase 1이 좋다.

이유:

- 제품 정보 구조를 먼저 바꾼다.
- 기존 Clipper1 단일 page를 더 키우지 않게 막는다.
- backend/render/template 대공사를 시작하기 전에 사용자-facing entry contract를 고정한다.
- 위험이 낮고 회귀 범위가 명확하다.

Phase 1에서 건드릴 가능성이 높은 파일:

```text
clipper_angular/src/core/plugin-status.service.ts
clipper_angular/src/core/plugin-status.service.spec.ts
clipper_angular/src/app/app.routes.ts
clipper_angular/src/app/app.routes.spec.ts
clipper_angular/src/shell/nav/nav.component.html
clipper_nestjs/src/plugins/plugin-catalog.ts
clipper_nestjs/src/workflows/workflow-executor-registry.service.ts
```

---

## 9. Open questions

구현 전에 확정하면 좋은 내용:

- route naming을 `/clipper1/url`로 할지 `/shortform/url`로 할지.
- `Clipper Studio`라는 이름을 계속 UI에 남길지, 모두 `Clipper1`/`숏폼 생성` naming으로 바꿀지.
- 기존 custom template data migration 정책.
- 기존 `16:9`/`full` template를 숨길지 read-only legacy로 유지할지.
- 제거 대상 layer가 있는 기존 project/render 결과를 열 때 어떻게 표시할지.

---

## 10. Non-goals

이번 Clipper1 rebuild의 non-goals:

- web/infra repo 변경.
- hosted web client/admin/API UX 변경.
- Python에 product-level Clipper1 API를 다시 만드는 것.
- Electron에 workflow/queue/project policy를 넣는 것.
- 기존 Clipper2 `clipper-studio` 구현을 그대로 확장하는 것.
