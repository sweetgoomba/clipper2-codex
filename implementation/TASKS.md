# Codex Implementation Tasks

작성일: 2026-04-29

이 문서는 Codex가 실제 구현에 들어갈 때 기준으로 삼는 작업 목록이다. 설계 문서는 `../design/`에 두고, 실제 구현 상태는 이 문서에서 추적한다.

## 현재 목표

Clipper2를 NestJS control plane 중심 구조로 재설계한다.

핵심 방향:

- Angular의 기본 API 대상은 NestJS로 수렴한다.
- NestJS가 plugin/job/project/queue orchestration의 중심이 된다.
- FastAPI plugin은 Python compute worker로 유지한다.
- Electron은 packaged desktop host/native adapter로 제한한다.
- Electron에 이미 구현된 PluginManager는 폐기하지 않고 Electron plugin process host adapter로 재배치한다.

## 현재 우선순위 정정 (2026-05-06)

Clipper1 편입의 다음 구현 목표는 `clipper1_video_render` 보강이 아니라 `workflow.clipper_studio` 사용자 흐름이다.

2026-05-06 16:02 KST 추가 정정:

- 현재 prompt-only `workflow.clipper_studio` 화면과 prompt submit 후 completed project shell을 만드는 흐름은 제품 방향과 맞지 않는다.
- 사용자-facing workflow는 `Clipper1` plugin과 `Variation` plugin으로 분리한다.
- 두 plugin은 `ShortformWorkspace`, `ShortformClip`, `NarrationLine`, `MediaPool`, `MediaSlot`, `PreviewTimeline`, `RenderRecipe` 등 공통 Shortform Core를 공유해야 한다.
- Clipper1 plugin은 왼쪽 tabbed input(URL/프롬프트/붙여넣기/수동 시작), 중앙 clip editor, 오른쪽 9:16 full preview/settings 구조로 재설계한다.
- 입력 영역 primary action label은 `클립 생성`이다.
- `클립 생성`은 workspace 안에 clip draft를 만드는 단계이며 보관함 completed project를 만들면 안 된다.
- `숏폼 생성`을 눌렀을 때만 render queue/job/project output으로 승격한다.
- clip당 media 1개 제한은 제거하고, clip마다 여러 media asset/pool/slot을 지원한다.
- Variation plugin은 별도 entry로 두되, asset folder/pool, variation locks, seeded media slot selection, batch render 개념을 shared core와 render path에 반영한다.
- 기준 설계 문서: `../design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
- Phase 1 구현 계획: `SHORTFORM_PLUGIN_SPLIT_PHASE1_PLAN.md`

## Template Builder Implementation (2026-05-07)

기준 문서:

- `../features/template-builder/design/approved-spec.md`
- `TEMPLATE_BUILDER_IMPLEMENTATION_PLAN_2026-05-07.md`

현재 상태:

- [x] Template Builder v4 mockup 사용자 승인
- [x] 승인된 방향을 구현 전 spec으로 문서화
- [x] 구현 계획 작성
- [x] NestJS Template Builder DTO/repository/service/controller/module first slice
- [x] Angular top-level `/templates` route and `템플릿` nav entry
- [x] Angular approved v4 editor shell
- [x] Sample render and publish action plumbing
- [x] Backend/frontend focused tests and build verification
- [x] Follow-up: dry-run sample render status를 실제 3-5초 mp4 render recipe 실행으로 교체
- [x] Follow-up: published custom template을 Clipper1/Variation template picker에 연결
- [x] Follow-up: layout image upload 추가
- [x] Follow-up: font asset upload 추가
- [x] Follow-up: uploaded font file stem과 실제 렌더 font family mismatch를 수동 `fontName` override로 보정
- [x] Follow-up: Template Builder 속성 패널을 실제 layer patch 저장 UI로 전환하고 canvas를 variant layer 기반 preview로 교체
- [x] Follow-up: Template Builder canvas text layer drag/resize first slice
- [x] Follow-up: uploaded layout image를 backend file endpoint로 canvas preview에 표시
- [x] Follow-up: Template Builder layer patch optimistic state merge
- [x] Follow-up: fixed 4 ratio slot 중 missing ratio를 같은 family 안에 생성하는 흐름 추가
- [x] Follow-up: canvas drag/resize output bounds clamp와 keyboard nudge
- [x] Follow-up: selected text layer 8방향 resize handle
- [x] Follow-up: canvas snap toggle와 snap size control
- [x] Follow-up: Template Builder page-level undo/redo history
- [x] Follow-up: snap enabled canvas grid guide
- [x] Follow-up: canvas center align assist
- [x] Follow-up: visible text layer 기준 edge/center align assist first slice
- [x] Follow-up: align assist 후보 최단거리 우선 선택
- [x] Follow-up: Template Builder layer update microtask batching
- [x] Follow-up: Template Builder layer update timer debounce/history coalescing
- [x] Follow-up: missing ratio variant 생성 시 text layer geometry 비례 복제
- [x] Follow-up: family clone 시 target ratio content/layer geometry 보정
- [x] Follow-up: ratio clone 시 layout/logo media와 logo text output-relative geometry 보존
- [x] Follow-up: canvas drag/resize pointermove 단위 continuous patch emission
- [x] Follow-up: Template Builder layer visibility를 속성 UI와 legacy render payload에 반영
- [x] Follow-up: Template Builder canvas에서 layout image 직접 이동/리사이즈 first slice
- [x] Follow-up: Template Builder 속성 패널에서 layout image 좌표/크기 numeric controls 추가
- [x] Follow-up: Template Builder logo image upload/file endpoint/canvas preview/properties controls 추가
- [x] Follow-up: Template Builder logo image asset을 published preset requiredAssets와 legacy render payload에 연결
- [x] Follow-up: Template Builder layout/logo media image 표시/숨김 UI와 render payload 반영
- [x] Follow-up: Template Builder `새 템플릿` 생성 시 이름과 시작 비율 선택 form 추가
- [x] Follow-up: Template Builder custom family 이름 변경 API/UI 추가
- [x] Follow-up: Template Builder 선택 family 복제 UI 추가
- [x] Follow-up: Template Builder custom family 삭제 API/UI 추가
- [x] Follow-up: Clipper1 제작 화면에서 legacy/custom template preset 선택 UI 연결
- [x] Follow-up: Clipper1 제작 화면 template picker를 thumbnail/card UI로 보강
- [x] Follow-up: published custom template sample render preview를 Clipper1 template picker에 표시
- [x] Follow-up: Clipper1 전용 template picker를 shared shortform component로 분리
- [x] Follow-up: template preset catalog loading을 shared shortform service로 분리
- [x] Follow-up: Variation 제작/배치 route shell에 shared template preset 선택 UI 연결
- [x] Follow-up: Variation workspace/domain DTO와 저장 API first slice
- [x] Follow-up: Python renderer가 explicit zoom/pan motion effect를 video/GIF에도 적용
- [x] Follow-up: Python renderer video/GIF 기본 표시를 legacy loop + blur-fill 방식으로 보정
- [x] Follow-up: Python renderer가 업로드된 TTF/OTF 내부 font family name을 자동 추출
- [x] Follow-up: Python renderer가 subtitle box border color/width를 ASS box style에 반영
- [x] Follow-up: Template Builder text layer center alignment를 render payload/Python renderer에 보존
- [x] Follow-up: Template Builder text layer 정렬 속성을 Angular 속성 패널에서 수정
- [x] Follow-up: Variation scenario clips와 asset pool refs를 workspace에 저장
- [x] Follow-up: Variation lock/randomize policy DTO 추가
- [x] Follow-up: Variation local folder picker/folder scan 연결
- [x] Follow-up: Variation folder asset list materialization
- [x] Follow-up: Variation cards 생성 first slice
- [ ] Follow-up: Variation card별 media reroll/selection

주의:

- 2026-05-07 13:55 KST 기준 sample render는 더 이상 가짜 성공 marker가 아니다. NestJS `TemplateBuilderSampleRenderService`가 `video.render.local_ffmpeg.basic` provider를 `dryRun: false`로 호출해 3초 MP4 artifact를 생성하고, 성공 artifact URI가 있어야 publish gate를 통과한다.
- 현재 sample render MP4는 render capability 경로 검증용 first real render다. legacy Clipper1 템플릿의 title/logo/subtitle/TTS/BGM overlay를 모두 합성하는 full template renderer parity는 아직 남은 작업이다.
- 2026-05-07 14:01 KST 기준 published custom template은 `/template-presets` catalog에 `source=template_builder`로 노출되고, Clipper Studio template picker는 더 이상 `source=clipper1`로만 필터링하지 않는다.
- 2026-05-07 14:07 KST 기준 published custom template preset의 `defaultParams.templateBuilderLayers`는 legacy Python renderer payload의 `template_settings`로 1차 변환된다.
- 2026-05-07 14:11 KST 기준 Template Builder에서 custom variant layout image를 multipart로 업로드할 수 있고, 업로드 후 `layers.layoutImage.assetUri`가 로컬 asset path로 갱신된다.
- 2026-05-07 14:19 KST 기준 Template Builder에서 text layer별 OTF/TTF font upload가 가능하고, Python renderer는 업로드된 font path의 directory를 ASS subtitles filter `fontsdir`로 넘긴다.
- 2026-05-07 19:15 KST 기준 Template Builder text layer에는 선택적 `text.fontName`이 있고 Angular `렌더 폰트명` 입력 -> NestJS `${prefix}_font_name` payload -> Python ASS style/shadow style font name override로 이어진다.
- 2026-05-07 14:31 KST 기준 `clipper_python`에 Template Builder custom template visual contract smoke를 추가했다. 실제 MP4를 만들고 layout image, content area, uploaded font `fontsdir`, ASS event count, frame pixel sample을 검증한다.
- 2026-05-07 14:35 KST 기준 Template Builder sample render service는 `video.render.legacy_clipper1.python_worker`를 요청하고 custom variant layer snapshot, sample TTS/BGM/logo를 포함한 legacy-compatible recipe를 만든다.
- 2026-05-07 14:42 KST 기준 실제 `clipper1_video_render` worker E2E로 Template Builder sample render가 `template-sample/main.mp4`를 생성하는 것까지 확인했다. 같은 과정에서 draft sample recipe가 built-in base preset을 통해 legacy payload로 매핑되도록 mapper를 보정했다.
- 2026-05-07 14:47 KST 기준 성공한 Template Builder sample render MP4를 NestJS endpoint로 안전하게 serve하고 Angular editor publish gate에서 재생한다.
- 2026-05-07 14:50 KST 기준 Python renderer의 Template Builder text style parity fixture를 추가했고 box/outline/shadow color/offset의 ASS style 매핑을 보강했다.
- 2026-05-07 19:08 KST 기준 Python renderer는 `shadow_outline_*`가 있는 `Subtitle`, `MainTitle`, `MainTitle2`에 별도 `*Shadow` ASS style/event를 본문 event 앞에 추가한다.
- 2026-05-07 14:52 KST 기준 Angular Template Builder `새 템플릿` 버튼은 실제 custom full 템플릿을 만들고 생성된 family를 바로 선택한다.
- 2026-05-07 15:04 KST 기준 Angular Template Builder 속성 패널에서 selected text layer의 위치/크기, 텍스트 스타일, box/outline/shadow 값을 수정하면 `PATCH /template-builder/families/:familyId/variants/:ratio` 경로로 저장된다. main canvas도 hard-coded mock이 아니라 selected variant layer 좌표/스타일을 축소 렌더링한다.
- 2026-05-07 15:10 KST 기준 Angular Template Builder canvas에서 text layer를 pointer drag로 이동하고 selected layer 우하단 handle로 크기 조절할 수 있다. pointerup 때 `updateVariant()` patch를 저장한다.
- 2026-05-07 15:10 KST 기준 uploaded layout image는 `GET /template-builder/families/:familyId/variants/:ratio/assets/layout-image/file`로 serve되고 Angular canvas에 실제 이미지로 표시된다.
- 2026-05-07 15:13 KST 기준 Angular Template Builder page는 layer patch를 서버에 저장하기 전에 selected family state에 먼저 deep merge한다. 저장 실패 시 이전 family snapshot으로 되돌린다.
- 2026-05-07 15:19 KST 기준 없는 ratio 슬롯은 full fallback을 보여주지 않고 `미설정`/`이 비율로 시작` 상태를 보여준다. 클릭 시 `POST /template-builder/families/:familyId/variants/:ratio`로 같은 family 안에 draft variant를 만든다.
- 2026-05-07 15:24 KST 기준 canvas text layer 이동/리사이즈는 output bounds 안으로 clamp된다. 선택된 text layer는 방향키로 1px, Shift+방향키로 10px 이동 patch를 emit한다.
- 2026-05-07 15:28 KST 기준 selected text layer는 8개 resize handle(`nw/n/ne/e/se/s/sw/w`)을 제공한다. 각 handle은 방향에 따라 필요한 `x/y/width/height` patch만 emit한다.
- 2026-05-07 15:33 KST 기준 stage toolbar에서 스냅을 켜고 간격(px)을 지정할 수 있다. 스냅이 켜져 있으면 canvas move/resize 결과가 지정 간격에 맞춰 저장된다.
- 2026-05-07 15:38 KST 기준 Template Builder page header에 `되돌리기`/`다시 실행`이 있다. 성공한 layer update는 before/after family snapshot을 page-local history에 쌓고 undo/redo 시 snapshot layers를 다시 저장한다.
- 2026-05-07 15:42 KST 기준 스냅이 켜져 있으면 canvas에 같은 간격의 grid guide가 표시된다. guide size는 `snapSize * canvasScale()`로 계산된다.
- 2026-05-07 15:44 KST 기준 canvas layer 이동 중 layer center가 canvas 중앙선 8px 이내에 들어오면 중앙에 자동 정렬되고 vertical/horizontal guide line이 표시된다.
- 2026-05-07 15:49 KST 기준 canvas layer 이동 중 다른 visible text layer의 left/center/right, top/center/bottom guide와 8px 이내로 가까워지면 해당 기준선에 붙고 guide line이 표시된다.
- 2026-05-07 15:51 KST 기준 여러 align guide 후보가 동시에 threshold 안에 있으면 가장 가까운 vertical/horizontal guide 후보를 선택한다.
- 2026-05-07 15:55 KST 기준 같은 family/ratio에 대한 연속 layer patch는 microtask 단위로 병합되어 `updateVariant()` 1회로 저장된다. undo history도 batch 단위로 1개만 쌓인다.
- 2026-05-07 16:12 KST 기준 layer patch 저장은 40ms debounce window로 확장됐다. microtask gap이 있어도 같은 family/ratio patch는 merged payload 1회 저장과 undo history 1개로 coalescing된다.
- 2026-05-07 16:05 KST 기준 fixed ratio slot 생성 시 source ratio의 text layer x/width/style은 보존하고 y/height/lineY는 source content area 상대 위치에서 target content area 좌표로 변환한다.
- 2026-05-07 16:09 KST 기준 family clone도 source variant deep copy가 아니라 target ratio 기본 variant 위에 같은 geometry/style clone 경로를 적용한다.
- 2026-05-07 16:18 KST 기준 `layoutImage`, `logoImage`, `logoText`는 output canvas 기준 layer로 보고 ratio clone 시 x/y/width/height와 style/assetUri를 output-size 비율로 보존한다. 모든 ratio output이 1080x1920이라 현재는 source 좌표가 그대로 유지된다.
- 2026-05-07 19:00 KST 기준 canvas text layer drag/resize는 pointermove마다 layer patch를 emit한다. pointerup은 중복 emit 없이 interaction state만 종료한다. backend 저장과 undo history는 page의 40ms debounce로 계속 coalescing된다.
- 2026-05-07 19:20 KST 기준 selected text layer는 `표시` checkbox로 `visible` patch를 저장할 수 있다. Template Builder layer visibility는 legacy render payload의 `sub_title_check/main_title_check/bottom_title_check/logo_check`와 clip subtitles에도 반영된다. Python renderer는 `main_title1` 없이 `main_title2`만 있는 payload도 `MainTitle2` event로 렌더한다.
- 2026-05-07 19:33 KST 기준 uploaded/remote layout image는 canvas에서 pointer drag로 이동하고 selection box의 8방향 handle로 resize할 수 있다. patch는 `layers.layoutImage.{x,y,width,height}`로 emit되며 기존 optimistic/debounce/undo 흐름을 탄다.
- 2026-05-07 19:35 KST 기준 `레이아웃 이미지` 속성 섹션에서도 `X/Y/너비/높이`를 숫자로 수정할 수 있다.
- 2026-05-07 19:45 KST 기준 custom variant `logoImage`도 multipart upload와 backend file endpoint preview를 지원한다. Angular editor에는 `로고 이미지` asset section과 `X/Y/너비/높이` numeric controls가 있다.
- 2026-05-07 19:45 KST 기준 published custom template preset은 `layers.logoImage.assetUri`를 `requiredAssets`의 `logo.image`/`logo_image`로 노출한다. Legacy Clipper1 render payload는 project logo artifact가 있으면 그것을 우선하고, 없으면 template logo image asset을 `project.logo_image`로 전달한다.
- 2026-05-07 20:22 KST 기준 Clipper1 제작 화면은 `/template-presets?workflow=workflow.clipper1&locale=ko-KR`에서 기존 Clipper1 템플릿과 게시된 Template Builder custom template을 불러와 `renderSettings.templateId`로 저장한다. `숏폼 생성` 전 저장된 `templateId`는 Clipper1 render recipe의 `templatePresetId`와 `templateParams.templateBuilder*`로 이어진다.
- 2026-05-07 20:22 KST 기준 legacy Clipper1 template preset compatibility에는 `workflow.clipper1`도 포함된다. 기존 `workflow.clipper_studio` project detail picker 호환성은 유지한다.
- 2026-05-07 20:28 KST 기준 Clipper1 제작 화면 template picker는 별도 `Clipper1TemplatePickerComponent`로 분리되었고, select + thumbnail/card 빠른 선택 UI를 제공한다. Component style budget warning 없이 `build:electron`을 통과했다.
- 2026-05-07 20:28 KST 기준 Variation은 virtual workflow catalog entry만 있고 아직 user-facing 제작/배치 화면이 없다. shared template picker 연결은 Variation surface 구현 뒤 진행한다.
- 2026-05-07 20:40 KST 기준 published Template Builder custom template preset은 성공한 sample render를 `preview.remoteVideoUrl`로 노출한다. Angular `ProjectHistoryService`는 backend-relative preview URL을 절대 URL로 보정하고, Clipper1 picker는 이미지 preview가 없으면 video preview를 렌더한다.
- 2026-05-07 20:47 KST 기준 Template Builder sample render `thumbnailArtifact`는 `thumbnailUri`로 저장되고 `sample-render/thumbnail/file` endpoint와 published preset `preview.remoteImageUrl`로 노출된다.
- 2026-05-07 20:51 KST 기준 Clipper1 template picker는 `ShortformTemplatePickerComponent`로 `src/features/shortform/components`에 이동했고, Clipper1 editor는 shared selector `app-shortform-template-picker`를 사용한다.
- 2026-05-07 20:55 KST 기준 template preset catalog loading은 `ShortformTemplatePresetCatalogService`로 분리되었다. 이 facade는 `workflow.clipper1`, `workflow.clipper_studio`, `workflow.variation`을 받고 `category: shorts`를 고정한다.
- 2026-05-07 20:59 KST 기준 `/variation` route와 `VariationPageComponent` first shell이 생겼다. Store/Dashboard plugin route mapping도 `variation -> /variation`으로 연결됐고, page는 `workflow.variation` template presets를 shared picker로 보여준다.
- 2026-05-07 21:05 KST 기준 Variation workspace는 `POST/PATCH/GET /projects/variation/workspaces`로 JSON 저장된다. `variationSet.count/variants`와 `renderSettings.templateId`가 저장되고, Angular page는 진입 시 workspace를 생성하고 template 선택 시 PATCH 한다.
- 2026-05-07 21:38 KST 기준 Variation workspace request는 `clips[]`를 받을 수 있고, `ShortformClip.mediaPool.folders[]`로 clip별 local asset folder ref를 저장한다. Angular Variation page에는 클립 제목/대사/미디어 폴더 경로 입력과 `클립 추가` 저장 흐름이 있다.
- 2026-05-07 21:44 KST 기준 Variation workspace `variationSet.randomizePolicy`가 생겼다. `lockedFields`, `randomizeFields`, `minMediaSlotMs`를 저장하며, Angular Variation page에는 `고정 설정` checkbox UI가 있다. 서버는 `lockedFields` 기준으로 `randomizeFields`를 정규화한다.
- 2026-05-07 21:48 KST 기준 Variation page의 미디어 폴더 경로는 기존 `FilePickerService.pickDirectory()`를 통해 Electron native directory picker를 사용할 수 있다. NestJS는 absolute local folder path를 저장할 때 1-depth media file count를 `mediaPool.folders[].assetCount`에 채운다.
- 2026-05-07 21:52 KST 기준 NestJS는 local folder scan 결과를 `mediaPool.assets[]`에도 materialize한다. 생성되는 asset ref는 deterministic `artifactId`, label, kind, mediaType, sourceHost=`local.folder`, sourcePath를 가진다. Angular Variation page는 folder asset count를 `N개 미디어`로 표시한다.
- 2026-05-07 21:55 KST 기준 `variationSet.variants[]`는 scenario clips projection을 가진다. 각 variant clip에는 `clipId`, `title`, `script`, `pickedAssetIds`가 있고, media randomize 정책이 켜져 있으면 variant index/clip order 기준으로 materialized media asset을 분산 선택한다. Angular batch panel은 고정 V1-V4가 아니라 실제 workspace variants를 렌더한다.
- 2026-05-07 21:13 KST 기준 `clipper_python` renderer는 render recipe에 명시된 `zoom`/`pan` effect를 image뿐 아니라 video/mp4와 gif media에도 적용한다. 단, media type 기반 자동 motion 판정은 아직 image-only다.
- 2026-05-07 21:16 KST 기준 `clipper_python` renderer는 video/GIF media 입력에 `-stream_loop -1`을 붙여 clip duration을 채우고, motion effect가 없는 video/GIF 기본 표시를 legacy Clipper1처럼 blur-fill background + centered foreground로 만든다.
- 2026-05-07 21:19 KST 기준 `clipper_python` renderer는 explicit `*_font_name`이 없을 때 업로드된 실제 TTF/OTF의 name table에서 typographic/family name을 읽어 ASS `Fontname`으로 사용한다. 읽을 수 없는 경우 기존 stem fallback을 유지한다.
- 2026-05-07 21:22 KST 기준 `clipper_python` renderer는 box style에서 `*_box_border_color/width`가 있으면 ASS `OutlineColour`/`Outline`에 우선 매핑한다. 특히 legacy `subtitle_box_border_*`가 최종 자막바에 반영된다.
- 2026-05-07 21:26 KST 기준 Template Builder custom text layer의 `align=center`은 NestJS payload에서 `*_center_x=x+width/2`로 전달되고, Python renderer는 `*_center_x`를 left/right margin보다 우선해 ASS alignment 8로 렌더한다. left/right align은 legacy margin key를 계속 사용한다.
- 2026-05-07 21:31 KST 기준 Angular Template Builder 속성 패널에서 selected text layer의 `정렬` segmented control로 `left/center/right`를 저장할 수 있다. 이 값은 기존 optimistic/debounce 저장 흐름을 타고 custom preset publish/render payload까지 이어진다.
- 2026-05-07 22:10 KST 기준 `clipper_python` renderer는 박스형 project text(`sub_title`, `main_title`, `main_title2`, `bottom_title`, `logo_text`)와 clip subtitle을 ASS box가 아니라 legacy Clipper1 방식에 가까운 PIL PNG text image로 만들고 ffmpeg timed overlay로 합성한다. `*_box_padding_left_right`, `*_box_height`, `*_box_alpha`, `*_box_border_*`를 이미지 생성에 반영하고 render summary에 `legacy_text_overlay_count`를 기록한다.
- 2026-05-07 22:19 KST 기준 `clipper_python` renderer는 legacy Clipper1처럼 박스형 main title에 shadow가 있으면 shadow PNG를 body box PNG 앞에 overlay하고, subtitle shadow가 있으면 box background보다 outline/shadow PNG 경로를 우선한다. 이로써 shadow + box 조합의 legacy PIL overlay 순서가 보강됐다.
- 2026-05-07 22:22 KST 기준 legacy font bundle audit에서 `JalnanGothic.otf` 등 상대 font filename의 실제 internal family name과 파일 stem이 다를 수 있음을 확인했다. Python renderer는 이제 상대 font filename도 legacy fonts dir에서 resolve한 뒤 TTF/OTF name table을 읽어 ASS `Fontname`에 사용한다.
- 2026-05-07 22:27 KST 기준 `clipper_python`에 reusable RGB frame comparison harness가 생겼다. `CLIPPER1_GOLDEN_FRAME_FIXTURE_DIR` 또는 `tests/fixtures/clipper1_golden_frames/manifest.json`에 old Clipper1 golden frame/payload/recipe를 넣으면 현재 renderer output frame과 channel tolerance/sample step/mismatch ratio 기준으로 비교한다.
- 2026-05-08 10:15 KST 기준 `adlight_python/scripts/export_clipper1_reference_frames.py`가 기존 Clipper1 `VideoService.create_video()`로 실제 영상을 만들고 첫 프레임 정답 이미지를 저장한다. 단일 `template-1-16:9`와 대표 25개 case export가 `/tmp`에서 성공했다.
- 2026-05-08 10:25 KST 기준 기존 Clipper1 정답 이미지 25개를 `clipper_python/tests/fixtures/clipper1_golden_frames`에 생성했다. raw strict 기준은 첫 case mismatch ratio `0.154080`으로 실패하지만, 영상 압축/글자 edge 차이를 반영해 `channelTolerance=32`, `maxMismatchRatio=0.04`를 1차 비교 기준으로 채택했다. 이 기준에서는 `uv run pytest tests/test_clipper1_video_render_golden_frames.py -q`가 통과한다.
- 2026-05-08 10:45 KST 기준 `clipper_python/scripts/diagnose_clipper1_golden_frame_drift.py`가 25개 정답 이미지 fixture를 실제 렌더/비교하고 case별 top/content/bottom mismatch report와 diff PNG를 만든다. 최신 진단 worst case는 `template-12-16_9`이고, 전체 mismatch `0.037809`, top region mismatch `0.102660`, content region mismatch `0.000646`이다. 다음 parity 수정 대상은 media 배치가 아니라 top 영역 project text/box 렌더링이다.
- 2026-05-08 13:15 KST 기준 `clipper_python` renderer는 legacy tracking 음수값을 보존하고, 박스형 text PNG canvas width를 Clipper1처럼 문장 전체 bbox 폭 + tracking으로 계산한다. `template-12-16_9` main title PNG는 `Legacy Clipper1 -> (753, 135)`, `Template 12 -> (597, 135)`로 맞춰졌고, golden drift는 전체 `0.037809 -> 0.011443`, top `0.102660 -> 0.024770`으로 감소했다. 새 worst case는 `template-1-full` 전체 `0.027674`다. 다음 parity 수정 대상은 full ratio/content 영역 합성 차이다.
- 2026-05-08 13:26 KST 기준 full 비율 render 순서를 Clipper1처럼 `concat된 비디오 -> layout -> 제목/자막/로고`로 맞췄다. 이전 Clipper2는 segment 안에 제목/자막/로고를 먼저 넣고 마지막에 alpha layout을 덮어서 텍스트가 회색으로 눌렸다. `template-1-full` mismatch는 `0.027674 -> 0.011059`, `template-17-full`은 `0.024510 -> 0.014497`로 감소했고, 새 worst case는 `template-3-16_9` 전체 `0.015185`다.
- 2026-05-08 13:54 KST 기준 Clipper2의 text height reference character set을 기존 Clipper1 `generate_reference_texts()` 기준으로 맞췄다. `template-3-16_9`에서 text PNG 안 glyph가 약 3px 낮게 그려지던 문제가 줄었고, mismatch는 `0.015185 -> 0.007126`으로 감소했다. 새 worst case는 `template-17-full` 전체 `0.012880`이다.
- 2026-05-08 13:59 KST 기준 recipe에서 legacy auto pan 방향/offset을 pinning할 수 있게 했다. `template-17-full` 참고 영상은 Clipper1 random pan이 `right_to_left`로 생성됐으므로 recipe에 `fit=height`, `direction=right_to_left`, `travelPx=8`, `offsetPx=416`을 명시했다. mismatch는 `0.012880 -> 0.005683`으로 감소했고, 새 worst case는 `template-6-1_1` 전체 `0.011948`이다.
- 2026-05-08 14:12 KST 기준 사용자가 직접 봤을 때 `template-6-1_1` 차이가 거의 없다는 점과 diff가 edge/resize noise에 몰려 있다는 점을 반영해 golden fixture 기준을 `maxMismatchRatio=0.04`에서 `0.015`로 강화했다. 이 기준에서도 25개 Clipper1 answer frame comparison은 통과한다.
- 2026-05-08 14:28 KST 기준 FFmpeg zoom branch scale에 `flags=bilinear`를 추가해 Clipper1 MoviePy/OpenCV linear resize에 더 가깝게 맞췄다. `template-6-1_1` mismatch는 `0.011948 -> 0.010862`로 감소했다. 다음 후보는 `template-16-16_9`, `template-11-16_9` top text edge 차이다.
- 2026-05-08 14:45 KST 기준 Clipper2 renderer의 layout/logo/text PNG overlay에서 `format=auto`를 제거해 기존 Clipper1 FFmpeg overlay 기본 동작과 맞췄다. `template-11-16_9` mismatch는 `0.009001 -> 0.003457`, `template-16-16_9`는 `0.009687 -> 0.006590`, `template-1-full`은 `0.011059 -> 0.000573`까지 줄었다. 새 worst는 `template-6-1_1` `0.011861`이며, golden fixture 기준도 `maxMismatchRatio=0.012`로 강화했다.
- 2026-05-08 15:07 KST 기준 automatic zoom branch를 기존 Clipper1처럼 content fit/crop 후 time-based scale/crop하는 2단계 FFmpeg filter로 바꿨다. `template-6-1_1` mismatch는 `0.011861 -> 0.006979`로 감소했고, golden fixture 기준도 `maxMismatchRatio=0.008`로 강화했다.
- 2026-05-08 15:31 KST 기준 x264 encoding preset을 기존 Clipper1 MoviePy 경로처럼 `ultrafast`로 맞췄다. top edge 상위 케이스는 소폭 줄었고, 현재 worst는 `template-6-1_1` `0.007012`이며 기준 `maxMismatchRatio=0.008` 안이다.
- 2026-05-08 16:05 KST 기준 automatic zoom source preprocessing을 기존 Clipper1처럼 content-area fit/crop 중간 JPEG/PNG source를 만드는 방식으로 맞췄다. `template-6-1_1` mismatch는 `0.007012 -> 0.006559`로 감소했고, golden fixture 기준도 `maxMismatchRatio=0.007`로 강화했다.
- 2026-05-08 16:23 KST 기준 text height 평균에서 zero-height glyph도 포함하도록 기존 Clipper1과 맞췄다. `template-16-4_3` mismatch는 `0.006553 -> 0.003434`로 감소했고, golden fixture 기준도 `maxMismatchRatio=0.0067`로 강화했다.
- 2026-05-08 17:09 KST 기준 automatic zoom scale flag를 `fast_bilinear`로 바꿔 Clipper1 MoviePy/OpenCV resize edge에 더 가깝게 맞췄다. `template-6-1_1` mismatch는 `0.006559 -> 0.006354`로 감소했고, golden fixture 기준도 `maxMismatchRatio=0.0065`로 강화했다.
- 2026-05-08 17:32 KST 기준 단일 클립도 기존 Clipper1처럼 최종 concat/filter/x264 encode 단계를 거치도록 맞췄다. `template-6-1_1` mismatch는 `0.006354 -> 0.006318`, `template-6-16_9`는 `0.004701 -> 0.003358`로 감소했고, golden fixture 기준도 `maxMismatchRatio=0.0064`로 강화했다.
- 2026-05-08 17:52 KST 기준 automatic image zoom을 기존 Clipper1 MoviePy/OpenCV처럼 30fps frame sequence로 먼저 만든 뒤 segment encode하도록 맞췄다. `template-6-1_1` mismatch는 `0.006318 -> 0.000114`로 감소했고, 새 worst는 `template-17-16_9` `0.003854`다. Golden fixture 기준도 `maxMismatchRatio=0.0039`로 강화했다.
- 2026-05-07 19:51 KST 기준 layout/logo media image에는 `표시` checkbox가 있고, 숨긴 media image는 canvas preview와 legacy render payload에서 제외된다.
- 2026-05-07 19:55 KST 기준 `새 템플릿`은 즉시 `full`로 생성되지 않고, inline form에서 이름과 시작 비율(`16:9`, `4:3`, `1:1`, `full`)을 선택한 뒤 생성한다.
- 2026-05-07 20:01 KST 기준 custom family는 `이름 변경` inline form과 `PATCH /template-builder/families/:familyId`로 이름을 바꿀 수 있다. 기본 제공/system family는 UI에서 rename button을 노출하지 않고 backend에서도 readonly로 거부한다.
- 2026-05-07 20:05 KST 기준 selected family는 `복제` inline form으로 새 custom family로 복제할 수 있다. system family도 복제는 가능하며, form의 ratio 선택지는 source family에 실제 존재하는 fixed ratio variant로 제한된다.
- 2026-05-07 20:10 KST 기준 custom family는 `삭제` inline confirmation과 `DELETE /template-builder/families/:familyId`로 삭제할 수 있다. 기본 제공/system family는 UI에서 delete button을 노출하지 않고 backend에서도 readonly로 거부한다. 삭제 후에는 남은 첫 family를 자동 선택하고, backend는 `template-assets/<familyId>`와 `template-samples/<safeFamilyId>` local directory를 함께 정리한다.
- Legacy Clipper1 render parity는 2026-05-09 기준 `maxMismatchRatio=0.0006` compatibility guard로 동결한다. 남은 top edge mismatch를 더 줄이는 작업은 중단하고, 새 우선순위는 Template Builder preview/final parity다.
- 아직 남은 render 작업: Template Builder canvas preview와 sample/final render가 같은 variant snapshot, 좌표, visibility, style, asset reference를 공유하도록 테스트 경계를 만든다. 템플릿별 수동 QA는 legacy 출력 안정성 확인과 modern preview/final 일치성 확인으로 분리한다.
- 아직 남은 editor UX: logo image 전용 drag/resize 회귀 테스트 일반화, text layer별 ratio conversion parity 세분화.
- Angular 구현 시 `zone.js` 재도입 금지, standalone + zoneless 테스트 규칙을 유지한다.

Phase 1 구현 목표:

- [x] Shortform Core DTO와 media slot scheduler 추가
- [x] legacy Clipper1 render recipe가 clip별 multiple media slots를 timeline item으로 확장하도록 수정
- [x] completed project history와 분리된 Clipper1 workspace API 추가
- [x] Clipper1/Variation virtual workflow plugin 분리
- [x] Angular Clipper1 3-panel workspace shell 추가
- [x] clip editor와 Angular-native 9:16 preview 1차 추가
- [x] `숏폼 생성`에서만 project/render job으로 승격되는 흐름 연결
- [x] Phase 1 검증과 `.codex` worklog/session log 갱신
- [x] Clipper1 editor 변경사항을 렌더 시작 전에 NestJS workspace `PATCH`로 저장
  - 2026-05-06 확인: NestJS에는 `PATCH /projects/clipper1/workspaces/:workspaceId`가 있지만 Angular `Clipper1WorkspaceService`는 아직 `updateWorkspace()`를 노출하지 않는다.
  - 현재 editor의 `workspaceChange`는 client signal만 갱신하므로, 사용자가 자막/클립/media slot을 수정한 뒤 바로 `숏폼 생성`을 누르면 서버 repository 기준의 이전 workspace로 렌더될 수 있다.
  - 다음 작업에서는 autosave 또는 render 직전 save를 추가하고, 저장 실패 시 렌더를 시작하지 않아야 한다.
  - 2026-05-06 완료: Angular workspace API client에 `updateWorkspace()`를 추가하고, `숏폼 생성` 클릭 시 최신 workspace를 먼저 저장한 뒤 저장된 workspace id로 render job을 시작하도록 수정했다.
- [x] Clipper1 workspace render 승격 시 실제 render worker 입력 파일 준비
  - 2026-05-06 확인: workspace render promotion이 `outputRoot: null`과 `clipper1://workspace/...` placeholder artifact를 만들 수 있어 Python worker execute mode에서 실패할 수 있었다.
  - 완료: `ClipperStudioAssetPreparer`를 재사용해 Clipper1 workspace render에도 seed media/TTS/layout/logo와 render output artifact를 project-file로 준비하고, `VideoRenderJobsService`에 실제 `outputRoot`를 전달하도록 수정했다.
  - workspace에 materialized artifact가 없는 임시 media slot이 있으면 prepared seed media slots로 대체해 render recipe가 항상 project-file media를 참조하게 했다.
- [x] Clipper1 workspace clip별 media search first-candidate 적용
  - 2026-05-06 완료: workspace API에 `POST /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/search-import`를 추가했다.
  - Clipper Studio media search provider를 재사용해 첫 검색 후보를 clip `mediaPool.assets`에 remote media asset으로 저장하고 media slots를 재스케줄한다.
  - render promotion은 workspace remote media asset을 `remote-url` artifact로 manifest에 반영해 Python worker가 remote staging할 수 있게 했다.
  - Angular editor에 clip별 검색어 입력과 `검색 적용` 버튼을 추가하고, 적용된 remote image를 9:16 preview에 표시한다.
- [x] Clipper1 workspace media search 후보 리스트 선택 UI
  - 2026-05-06 완료: workspace API를 `media/search` 후보 조회와 `media/remote` 선택 후보 적용으로 분리했다.
  - 기존 `media/search-import`는 첫 후보 자동 적용 호환 endpoint로 유지한다.
  - Angular editor는 clip별 검색 결과 후보 썸네일/라벨을 표시하고, 사용자가 선택한 후보만 clip `mediaPool.assets`와 preview에 반영한다.
- [x] Clipper1 workspace local media upload + drag/drop
  - 2026-05-06 완료: `POST /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/local` multipart upload API를 추가했다.
  - 업로드 파일은 `CLIPPER_DATA_DIR/sources/clipper1-workspace/...`에 저장하고, workspace asset에는 preview용 `contentUrl`과 render용 `sourcePath`를 함께 저장한다.
  - render promotion은 local upload asset을 `source-file` artifact로 manifest에 반영해 Python worker가 로컬 파일을 직접 읽게 한다.
  - Angular editor는 파일 선택과 드래그앤드랍을 모두 지원하며, 둘 다 같은 upload handler/API를 사용한다.
- [x] Clipper1 local media 선택을 기존 Electron file picker 경계와 통합
  - 2026-05-06 완료: 기존 `FilePickerService`에 media picker wrapper를 추가하고, Clipper1 파일 선택 버튼이 Electron `openMediaFile()`를 우선 사용하게 했다.
  - Electron native picker/drop처럼 절대 로컬 경로가 있는 경우 `media/source-path` API로 workspace asset을 만든다.
  - 브라우저 fallback 또는 path 없는 drop은 기존 multipart `media/local` upload 경로를 유지한다.
- [x] Clipper1 clip media asset 삭제와 slot 재계산
  - 2026-05-06 완료: `DELETE /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId`를 추가했다.
  - 삭제된 asset은 clip `mediaPool.assets`와 `mediaSlots`에서 빠지고, 남은 asset이 있으면 slot을 재계산한다.
  - Angular editor는 각 media asset chip에 삭제 버튼을 표시하고, 삭제 후 workspace/preview를 갱신한다.
- [x] Clipper1 clip media asset 교체
  - 2026-05-06 완료: `PUT /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId/(remote|local|source-path)`를 추가했다.
  - 교체는 기존 `assetId`를 보존해 clip `mediaSlots`와 `previewTimeline` 참조를 깨지 않고 media source만 바꾼다.
  - Angular editor는 media chip에서 파일 교체, 검색 결과 교체, 삭제를 제공한다.
  - Electron/native picker는 source-path replace를 사용하고, 브라우저 fallback은 multipart local replace를 사용한다.
- [x] Clipper1 clip media asset 순서 변경과 sequential slot 재계산
  - 2026-05-06 완료: `PATCH /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/order`를 추가했다.
  - 요청 body의 `assetIds`는 clip의 기존 media asset 전체 집합과 정확히 일치해야 하며, 누락/중복/unknown id는 거부한다.
  - 순서 변경 후 clip `mediaPool.assets`, `mediaSlots`, `previewTimeline`을 같은 순서로 갱신하고 selection policy를 `sequential`로 전환한다.
  - Angular editor는 각 media chip에 위/아래 이동 버튼을 제공하고, 서버 응답으로 preview를 갱신한다.
- [x] Clipper1 clip media slot duration/구간 편집
  - 2026-05-06 완료: `PATCH /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/slots`를 추가했다.
  - slot update는 기존 media asset을 참조해야 하고, 0부터 clip duration까지 빈틈 없이 이어지는 구간만 허용한다.
  - 저장된 slot 구간은 workspace preview timeline과 render manifest detail clips의 `mediaSlots`에 그대로 반영된다.
  - Angular editor는 slot별 초 단위 duration input을 제공하고, 한 slot을 조정하면 인접 slot을 반대로 조정해 clip 전체 길이를 유지한다.
- [x] Clipper1 workspace media library 1차 reuse
  - 2026-05-06 완료: `POST /projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/reuse`를 추가했다.
  - 별도 workspace-level 저장소를 새로 만들지 않고, workspace 안 다른 clip들의 `mediaPool.assets`를 library처럼 파생한다.
  - 같은 workspace의 다른 clip asset만 재사용 가능하며, 대상 clip에 이미 붙은 asset은 중복 추가하지 않는다.
  - Angular editor는 다른 clip에서 쓰인 media asset을 대상 clip 아래에 `사용` 버튼으로 노출한다.
  - 다음 단계: 후보 검색 pagination/재검색 UX, slot drag handle/타임라인형 편집 UX, library filter/thumbnail UX.
- [x] Clipper1 media slot boundary slider 1차
  - 2026-05-06 완료: 기존 `PATCH .../media/slots` API를 그대로 사용하고 Angular editor에 슬롯 사이 경계를 조정하는 range slider를 추가했다.
  - 각 경계 slider는 양쪽 인접 slot의 최소 길이를 보장하는 min/max를 계산한다.
  - 경계를 이동하면 두 인접 slot의 `endMs`/`startMs`만 바꾸고 전체 clip duration과 contiguous slot 조건을 유지한다.
  - 다음 단계: 실제 waveform/timeline track 형태의 drag handle, thumbnail이 붙은 slot bar, slot fit/crop 세부 편집.
- [x] Clipper1 media slot fit 선택과 preview 반영
  - 2026-05-06 완료: slot별 `cover`/`contain`/`fill` 값을 Angular editor에서 선택할 수 있게 했다.
  - NestJS workspace `previewTimeline.items`에 slot `fit`을 포함해 렌더 전 preview가 final render recipe와 같은 표시 방식을 사용할 수 있게 했다.
  - Angular preview player는 현재 timeline item의 `fit`으로 media `object-fit`을 바꾼다.
  - 다음 단계: slot별 crop/position, motion preset 선택, thumbnail timeline bar.
- [x] Clipper1 media slot thumbnail timeline bar 1차
  - 2026-05-06 완료: clip editor에 media slot 구간을 비율 기반 가로 bar로 보여주는 1차 thumbnail timeline을 추가했다.
  - 각 segment는 slot duration 비율, media label, 구간 라벨, thumbnail/content URL을 사용한다.
  - 다음 단계: timeline segment 직접 선택, handle drag, slot crop/position.
- [x] Clipper1 media slot motion preset 저장/선택 1차
  - 2026-05-06 완료: slot별 `motionPreset` 값을 workspace update API, preview timeline, render manifest detail slots에서 보존하도록 했다.
  - Angular editor는 slot별 `고정`/`줌인`/`좌이동`/`우이동` select를 제공한다.
  - 다음 단계: Angular preview에서 motion preset을 실제 애니메이션으로 재생하고 Python renderer에 대응 효과를 연결.
- [x] Clipper1 media slot motion preset preview/render recipe 연결
  - 2026-05-06 완료: Angular preview player가 현재 playback position 기준으로 `zoom-in`, `pan-left`, `pan-right` transform을 계산해 media에 적용한다.
  - Legacy Clipper1 render recipe provider는 slot `motionPreset`을 Python render adapter가 이해하는 `effects` params로 변환한다.
  - `zoom-in`은 `zoom` effect, `pan-left`/`pan-right`는 방향성 `pan` effect로 전달한다.
  - 다음 단계: Python renderer 결과물에서 motion parity를 확인하고 필요하면 params/속도 값을 조정.

2026-05-06 11:12 KST checkpoint:

- 최신 상태 요약은 `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_2026-05-06.md`를 먼저 본다.
- packaged Electron render E2E와 final preview/rerender flow는 사용자가 직접 확인했고 정상이다.
- 이전 세션 변경사항은 repo별로 커밋됐고, 네 repo 모두 clean 상태다.
- 다음 구현 우선순위는 생성된 MP4 품질 피드백 또는 production provider 연결 우선순위에 따라 잡는다.
- 2026-05-06 13:16 KST 추가 진행:
  - `clipper_python`에서 BGM-only render가 `bgm_volume`을 실제 오디오에 적용하지 않는 문제를 수정했다.
  - `uv run pytest tests/test_clipper1_video_render_remote_assets.py` 성공, 6 passed.
  - 변경은 아직 커밋하지 않았다.

현재 완료:

- [x] `clipper_angular` `eea2e9e feat: add project render job UI`
- [x] `clipper_angular` `1045c46 feat: show clipper studio final renders`
- [x] `clipper_angular` `81fec28 fix: refresh clipper studio render manifest`
- [x] `clipper_angular` `6d7332a feat: add clipper studio edit state client`
- [x] `clipper_angular` `3f135a7 feat: edit clipper studio render settings`
- [x] `clipper_angular` `5836899 feat: select clipper studio templates`
- [x] `clipper_nestjs` `4f31579 feat: add project manifest render jobs`
- [x] `clipper_nestjs` `f699a30 feat: update clipper studio edit state`
- [x] `clipper_nestjs` `4d75b9e feat: load clipper1 template catalog from json`
- [x] `clipper_python` `c53ea33 feat: add clipper1 video render worker`
- [x] `clipper1_video_render`를 headless `video.render` provider/runtime으로 정리

다음 구현:

필수 구현 원칙:

- OpenAI/Ollama/Gemma/remote proxy, Naver/Kakao/local image generation, Clova/Oute/local TTS는 모두 provider 구현체다.
- Workflow/editor/render code는 특정 vendor API shape, credential, billing, quota, retry/fallback 정책을 몰라야 한다.
- 새 provider를 붙일 때 core workflow 수정이 필요하면 abstraction이 부족한 것이다. 먼저 capability contract, provider registry, adapter boundary를 만든다.

- [x] `workflow.clipper_studio` descriptor 추가
- [x] Angular `/clipper-studio` 제작 화면 추가
- [x] NestJS Clipper Studio project shell/create API 추가
- [x] `/projects` Clipper Studio presenter 추가
- [x] prompt/text draft generation job 추가
- [x] prompt/text draft generation을 NestJS job/progress/cancel model로 전환
- [x] `llm.script` facade를 deterministic adapter 뒤로 분리
- [x] media/TTS/BGM/logo artifact preparation 추가
- [x] existing `video.render.legacy_clipper1.python_worker` final render 연결
- [x] render 완료 결과를 Clipper Studio project manifest/open UX에 반영
- [x] Clipper Studio detail에 final MP4/thumbnail preview 1차 연결
- [x] render job 완료 polling 후 manifest refresh로 final preview 즉시 갱신
- [x] Clipper Studio edit-state 저장 API/client 추가
- [x] Clipper Studio detail에 title visibility/logo text/TTS speed 편집 UI 추가
- [x] Clipper Studio detail에 Clipper1 template catalog select 추가
- [x] Clipper1 template catalog를 JSON file source로 전환
- [x] Clipper Studio detail에 BGM/logo artifact 선택 UI 추가
- [x] edit 후 stale render output의 주요 버튼 문구를 재렌더 흐름으로 보정
- [x] Clipper Studio clip별 media artifact 선택 UI와 render recipe override 연결
- [x] Clipper Studio TTS preset catalog endpoint와 선택 UI 연결
- [x] Clipper Studio 렌더 이력 표시와 version artifact 보존 연결
- [x] Clipper Studio final render empty state 표시
- [x] Clipper Studio script/title/clip subtitle editor 1차 연결
  - `clipper_nestjs` `7c6cb49 feat: edit clipper studio script clips`
  - `clipper_angular` `842066e feat: edit clipper studio script clips`
  - project detail에서 main/sub/bottom title, keywords, clip subtitle, clip search query, clip duration을 저장 가능
  - subtitle 변경 시 현재 `tts.synthesis` provider를 통해 새 `audio.tts` artifact를 만들고 render recipe가 새 subtitle/TTS artifact를 사용
- [ ] placeholder/demo provider 제거
  - [x] Clipper1 bundled seed asset provider로 단색 BMP/silent WAV 제거
    - `clipper_nestjs` `41792be feat: use clipper studio seed assets`
  - [x] local/user media provider 1차 연결
    - `clipper_nestjs` `da1e96d feat: import clipper studio local media`
    - `clipper_angular` `4f679de feat: add clipper studio media import UI`
    - `clipper_electron` `4f3e9ac feat: add media file dialog bridge`
  - [x] 실제 TTS synthesis provider 1차 연결
    - `clipper_nestjs` `bb07a87 feat: synthesize clipper studio local tts`
  - [x] media search/download provider 1차 연결
    - `clipper_nestjs` `8262299 feat: add clipper studio media search import`
    - `clipper_angular` `b8bd59a feat: apply clipper studio media search results`
  - [x] BGM/logo catalog/upload provider 1차 연결
    - `clipper_nestjs` `1f2605e feat: add clipper studio bgm and logo imports`
    - `clipper_angular` `bb543e9 feat: add clipper studio bgm and logo import UI`
    - `clipper_electron` `43fbd9b feat: add audio file dialog bridge`
  - [x] real/remote LLM script provider boundary 1차 연결
    - `clipper_nestjs` `687d914 feat: add clipper studio remote script provider`
    - `clipper_angular` `8e20564 feat: use clipper studio script search queries`
    - `CLIPPER1_LLM_SCRIPT_ENDPOINT` 또는 explicit `CLIPPER1_LLM_SCRIPT_PROVIDER=openai_responses` 설정이 있을 때 remote provider 사용
    - production proxy/key/billing 정책과 실제 endpoint 운영은 후속
  - [x] script searchQuery 기반 clip media 자동 검색/적용 1차 연결
    - `clipper_nestjs` `43d9165 feat: auto apply clipper studio search media`
    - media search key가 있으면 draft 생성 중 clip별 `searchQuery`/keyword로 첫 검색 결과를 자동 다운로드
    - user-selected media는 덮지 않고 자동 검색 artifact만 다음 draft에서 교체
- [x] provider registry/adapter boundary 1차 정리
  - `llm.script`, `media.search`, `image.generate`, `tts.synthesis`를 vendor/local runtime 구현과 분리
  - OpenAI/Ollama/Gemma, Naver/Kakao/local image generation, Clova/Oute/local TTS가 provider 구현체로 교체 가능해야 함
  - [x] `llm.script` provider registry/adapter 1차 분리
    - `clipper_nestjs` `6797b5a refactor: split clipper studio script providers`
    - `DeterministicClipperStudioScriptProvider`, `RemoteProxyClipperStudioScriptProvider`, `OpenAiResponsesClipperStudioScriptProvider`
    - `ClipperStudioScriptProviderRegistry`, `ClipperStudioScriptResponseNormalizer`
  - [x] `llm.script` Ollama/local model provider 추가
    - `clipper_nestjs` `0da9415 feat: add clipper studio ollama script provider`
    - `OllamaClipperStudioScriptProvider`
    - `CLIPPER1_LLM_SCRIPT_PROVIDER=ollama`
    - `CLIPPER1_LLM_SCRIPT_OLLAMA_ENDPOINT` 또는 `CLIPPER1_LLM_SCRIPT_OLLAMA_BASE_URL`, `CLIPPER1_LLM_SCRIPT_OLLAMA_MODEL`
    - Ollama `/api/generate` response JSON 문자열을 기존 script draft normalizer로 정규화
  - [x] `media.search` provider registry/adapter 1차 분리
    - `clipper_nestjs` `36211b5 refactor: split clipper studio media search providers`
    - `NaverClipperStudioImageSearchProvider`, `KakaoClipperStudioImageSearchProvider`
    - `ClipperStudioMediaSearchProviderRegistry`, `ConfiguredClipperStudioMediaSearchProvider`, `ClipperStudioRemoteMediaDownloader`
  - [x] `media.search` HTTP/remote proxy provider 추가
    - `clipper_nestjs` `8aac74d feat: add clipper studio remote media search provider`
    - `RemoteProxyClipperStudioImageSearchProvider`
    - `CLIPPER1_MEDIA_SEARCH_ENDPOINT` 또는 `CLIPPER_STUDIO_MEDIA_SEARCH_ENDPOINT` 설정 시 Naver/Kakao 대신 company/custom/local media search proxy를 호출
    - `CLIPPER1_MEDIA_SEARCH_PROVIDER_ID`로 provider id를 capability status와 artifact metadata에 맞춰 표시
    - response는 `items`/`results`/`candidates`/`images` 계열 배열과 `contentUrl`/`imageUrl`/`url` 계열 필드를 `media.image` candidate로 정규화
  - [x] `image.generate` provider registry/adapter 1차 분리
    - `clipper_nestjs` `a95c35a feat: add clipper studio image generation provider`
    - `clipper_angular` `02e2c04 feat: add clipper studio image generation UI`
    - `clipper_nestjs` `4d40aa8 feat: expose clipper studio capability status`
    - `clipper_angular` `083dbdc feat: show clipper studio generation availability`
    - `HttpClipperStudioImageGenerationProvider`
    - `ClipperStudioImageGenerationProviderRegistry`, `ConfiguredClipperStudioImageGenerationProvider`
    - `POST /v1/projects/:projectId/clipper-studio/media/generate`가 generated media artifact를 만들고 clip source로 연결
    - `/projects` Clipper Studio clip row의 `생성 적용` 버튼이 같은 입력 prompt로 generated media를 적용
    - `GET /v1/projects/clipper-studio/capabilities`로 image generation provider availability를 내려주고 endpoint 미설정 시 버튼 비활성화
  - [x] `tts.synthesis` provider registry/adapter 1차 분리
    - `clipper_nestjs` `db92d6a refactor: split clipper studio tts providers`
    - `MacOsSayClipperStudioTtsProvider`
    - `ClipperStudioTtsSynthesisProviderRegistry`, `ConfiguredClipperStudioTtsSynthesisProvider`
  - [x] `tts.synthesis` HTTP/local-server provider 추가
    - `clipper_nestjs` `b170178 feat: add clipper studio http tts provider`
    - `HttpClipperStudioTtsProvider`
    - `CLIPPER1_TTS_SYNTHESIS_ENDPOINT` 또는 `CLIPPER_STUDIO_TTS_SYNTHESIS_ENDPOINT` 설정 시 remote/local TTS server를 호출
    - JSON base64/audio URL/direct audio response를 `audio.tts` project-file artifact로 정규화
    - configured provider id/speaker id가 capability status와 TTS preset catalog에 표시됨
  - [x] Clipper Studio provider status/fallback surface 추가
    - `clipper_nestjs` `47495ec feat: expose clipper studio provider fallback status`
    - `clipper_angular` `b077fba feat: show clipper studio provider status`
    - `clipper_nestjs` `76bbac8 feat: include clipper studio provider config hints`
    - `clipper_angular` `9ad8455 feat: show clipper studio provider config hints`
    - `GET /v1/projects/clipper-studio/capabilities`가 `llm.script`, `media.search`, `image.generate`, `tts.synthesis`의 `available`/`fallback`/`unavailable` 상태와 provider id를 반환
    - capability별 setup env key를 `configurationKeys`로 반환. `media.search`에는 remote proxy endpoint/provider id와 Naver/Kakao key가 함께 표시됨
    - `/projects` Clipper Studio detail 상단에 provider 상태 카드와 설정 키 힌트 표시
- [ ] production provider endpoint/key/billing 정책 확정 및 실제 endpoint 운영
- [x] Clipper Studio desktop visual QA smoke와 final render empty state polish
- [ ] Clipper Studio render/error state polish
  - [x] 2026-05-05 dev/static host에서 `clipper1_video_render`를 spawn할 수 없는데 Python render worker provider가 available로 표시되던 문제 수정
- [x] 최종 MP4/thumbnail preview visual QA 1차
  - 2026-05-05 packaged Electron 사용자 확인: final preview, thumbnail/poster, render history/version, edit -> stale/rerender -> regenerated output 정상
- [ ] 생성 영상 품질 QA
  - 자막 위치, 제목 overlay, image motion, BGM/TTS volume, thumbnail, Clipper1 template visual parity 확인
  - [x] BGM-only render path에서 `bgm_volume`이 실제 오디오에 적용되도록 수정
    - `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
    - `clipper_python/tests/test_clipper1_video_render_remote_assets.py`
    - `uv run pytest tests/test_clipper1_video_render_remote_assets.py` 성공, 6 passed

기준 문서: `../design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`

이전 참고 문서: `../design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`

## Phase 0: 문서/상태 정리

- [x] `.codex` 문서 구조화
- [x] 기존 설계/히스토리 문서 보존 및 폴더 이동
- [x] NestJS control plane 재설계 문서 작성
- [x] SOLID/경계 분리 기준 문서 작성
- [x] 현재 4개 repo 상태 재확인
- [x] 당시 작업트리 상태를 확인하고 충돌 없는 구현 범위 확정

## Phase 1: 현재 코드 경계 분석

- [x] `clipper_angular`의 pipeline job 실행 경로에서 FastAPI plugin 직접 호출 제거
- [x] `clipper_angular`에서 남은 FastAPI/plugin direct call 지점 목록화
- [x] `clipper_angular`에서 Electron IPC를 직접 호출하는 지점 분류
- [x] `clipper_nestjs`의 현재 module/service 구조 확인
- [x] `clipper_electron`의 PluginManager/IPC 책임 분리 지점 확인
- [x] `clipper_python` SDK endpoint 계약 확인

## Phase 2: NestJS PluginHost 설계/구현

- [x] NestJS에 `PluginHost` 추상화 추가
- [x] `StaticPluginHost` 구현: local/dev에서 env/static plugin URL 사용
- [x] `PluginService` 구현: list/status/start/stop/url 획득 API facade
- [x] Electron packaged mode용 host bridge 설계
- [x] Angular가 직접 plugin URL을 몰라도 되는 DTO 설계

## Phase 3: NestJS Job/Queue Orchestration

- [x] `Job` DTO 설계
- [x] `Project` DTO 설계
- [x] `JobQueueService` 인터페이스 설계
- [x] 초기 저장소 결정: JSON snapshot 우선
- [x] NestJS가 FastAPI plugin `/jobs` 호출
- [x] NestJS가 FastAPI plugin WS/SSE progress 수신
- [x] Angular에 job progress 전달 방식 결정
- [x] 실제 순차 queue 구현
- [x] persisted job snapshot/history 구현
- [x] completed job을 project/output history로 승격
- [x] retry 정책 1차 구현
- [x] reorder 정책 1차 구현
- [x] managed project output root 1차 구현

## Phase 4: Angular API 전환

- [x] `PluginJobService`의 FastAPI 직접 호출 제거 또는 deprecated 처리
- [x] NestJS `JobApi` service 추가
- [x] Dance/Dialog flow가 NestJS job API로 enqueue하도록 전환
- [x] Dashboard에 Project history 1차 조회 UI 연결
- [x] `/projects` 작업/프로젝트 history 화면 1차 구현
- [x] Queue job 상세 UI 1차 구현
- [x] Project/작업 보관함 UI 1차 재구성
- [x] 작업 보관함 실행 큐/완료 목록 레이아웃 1차 개선
- [x] 작업 보관함 실행 큐를 접힘/overlay drawer 구조로 개선
- [x] 작업 보관함 compact queue bar / overlay drawer 실제 Angular 코드 반영
- [x] 작업 보관함 상세 결과를 dialog/dance별 2단 UI로 재구성
- [x] 작업 보관함 상세 metadata 단순화 및 9:16 숏츠형 플레이어 적용
- [x] 안무 상세 인물/영상 모음/클립 리스트 후속 레이아웃 조정
- [x] 작업 보관함 안무 상세 responsive overlap packaged app 수동 확인
- [x] `projects.component.scss` component style budget warning 정리
- [x] 공통 페이지 헤더 컴포넌트 적용
- [x] Store/Dashboard plugin status/start/stop 경로를 NestJS `/v1/plugins` API로 전환

## Phase 5: Electron 책임 재배치

- [ ] 현재 `LocalPluginManager`를 host-level manager로 명명/분리할지 결정
- [x] Electron plugin IPC를 Angular-facing API가 아니라 NestJS host bridge로 재설계
- [x] packaged mode에서 NestJS가 Electron host bridge를 통해 plugin start/stop 가능하게 구현
- [x] local/dev mode에서 Electron 없이 동작 가능한 경로 유지
- [x] `build:app` Node 22 LTS guard 추가
- [x] Node 22 LTS 환경에서 `npm run build:app:mac:arm64` 재검증
- [x] 설치된 app에서 packaged bridge -> NestJS -> Python plugin E2E 검증
- [x] 5분 idle plugin shutdown 회귀 검증

## Phase 6: Clipper1 편입 준비

- [ ] 레거시 Clipper1 workflow endpoint/서비스 목록화
- [ ] `clipper_studio` Python plugin 범위 정의
- [ ] NestJS `clipper-studio` module 책임 정의
- [ ] Angular `features/clipper-studio` 화면 흐름 정의
- [ ] LLM proxy/remote server 전환 시점 결정

## Phase 7: Resource-Aware Plugin Management

- [x] Workflow/Capability/Resource 설계 문서 작성
- [x] Electron host telemetry collector 추가
- [x] packaged bridge `GET /resources` 추가
- [x] NestJS `ResourceHost` 추상화 및 `/v1/resources` facade 추가
- [x] Angular Dashboard resource summary 1차 연결
- [x] packaged app에서 `/v1/resources` runtime 검증
- [x] macOS memory availability 계산 보정
- [x] Electron/NestJS 프로세스 RSS/CPU 추적
- [x] running plugin process RSS/CPU 표시 E2E 검증
- [x] plugin manifest resource metadata 추가
- [x] NestJS/Angular DTO에 resource metadata 연결
- [x] Store/Dashboard에 resource profile 1차 표시
- [x] Dashboard에 가용 RAM 기반 resource pressure warning 1차 표시
- [x] NestJS advisory resource assessment API 설계/1차 구현
- [x] Dashboard resource/process operations console 1차 고도화
- [x] resource admission confirm 정책 1차 구현
- [x] GPU/VRAM telemetry best-effort adapter 1차 구현
- [x] Windows CUDA 배포 전략 초안 작성
- [x] plugin runtime accelerator probe endpoint 1차 구현
- [x] hard admission blocking 정책 1차 구현
- [x] idle plugin 수동 eviction UX 1차 구현
- [ ] host GPU telemetry + plugin runtime probe 결합 assessment 설계
- [x] Dashboard running plugin runtime accelerator 표시 1차 구현
- [x] Dashboard runtime resource/process 표시 용어와 섹션 레이아웃 1차 개선
- [ ] idle plugin policy-based eviction 설계
- [ ] plugin dashboard를 operations console 형태로 고도화

## Phase 8: Multi-Mode Architecture Boundaries

- [x] SSE 기반 job event stream을 WebSocket `/v1/events`로 전환
- [x] `ownerSubjectId` 기반 job/project/event scope 추가
- [x] 로그인 서버 도입 대비 `AuthProvider` 경계 추가
- [x] 이용권/권한 정책 도입 대비 `LicensePolicyService` 경계 추가
- [x] 사용자/tenant별 실행 정책 도입 대비 `ExecutionScopeService` 경계 추가
- [x] in-memory job queue를 `JobQueue` 추상화 뒤로 이동
- [x] 산출물 저장소 변경 대비 `ArtifactStorage` 경계 추가
- [x] project detail 변환 로직을 `ProjectDetailBuilder`로 분리
- [x] 실행 중 job 취소 시 queue slot을 즉시 해제하고 다음 waiting job 실행
- [ ] 원격 auth/license 서버 실제 연동
- [ ] Redis/DB-backed queue 구현
- [ ] object storage/S3 artifact backend 구현
- [ ] multi-instance WS event broker 설계

## Phase 9: Workflow / Shared Capability Foundation

기준 문서: `../design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
후속 inventory/schema 초안: `../design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`

- [x] Workflow Plugin과 Shared Capability 분리 설계 문서화
- [x] YouTube 입력, 템플릿 공통화, Clipper1 편입을 같은 구조에서 설명하는 단계별 계획 문서화
- [x] Clipper1 legacy endpoint/service/template/media/TTS/render inventory 작성
- [x] `SourceInput` / `SourceAsset` DTO 1차 설계 및 compatibility adapter 구현
- [x] NestJS `source.inspect` / `source.ingest` service 1차 구현
- [x] local file 입력을 `SourceInput` 흐름으로 전환하되 기존 dialog/dance job 호환 유지
- [x] YouTube URL provider 1차 구현 위치 결정 및 vertical slice 구현
- [x] project snapshot/detail에 `sourceAssets`와 provenance 저장
- [x] Clipper1 shared capability 분해안 문서화
- [x] `ProjectManifest` / workflow별 output artifact 모델 / `TemplatePreset` / `RenderRecipe` 초안 문서화
- [x] `clipper_nestjs`에 contract-only `ProjectManifest` / `TemplatePreset` / `RenderRecipe` DTO와 fixture 추가
- [x] dialog/dance output을 공통 `ProjectManifest` clip/entity artifact 모델로 매핑하는 builder/API 1차 구현
- [x] 실제 packaged userData의 dialog/dance 완료 프로젝트로 manifest endpoint smoke 및 artifact access 보정
- [x] `TemplatePreset` / `RenderRecipe` catalog/provider 초안 구현
- [x] 현재 shorts 렌더 결과를 기본 템플릿(`shorts.basic_letterbox`)으로 명명
- [x] Clipper1 template row -> `TemplatePreset` adapter 및 catalog source 분리
- [x] Clipper1 legacy template apply -> `RenderRecipe` 매핑 규칙 1차 구현
- [x] `VideoRenderProvider` contract 및 Clipper1 dry-run render payload mapper 1차 구현
- [x] `video.render` provider registry 및 render job skeleton 1차 구현
- [x] `clipper1_video_render` Python worker plugin contract 및 NestJS python-worker provider 연결
- [x] `clipper1_video_render` first-pass execute adapter로 로컬 mp4/thumbnail artifact 생성
- [x] `clipper1_video_render` SRT 기반 기본 subtitle compositing 추가
- [x] `clipper1_video_render` TTS/BGM audio mixing 및 final MP4 mux 추가
- [x] `clipper1_video_render` content area 배치 및 ASS 기반 legacy text overlay 1차 구현
- [x] `clipper1_video_render` local layout image background 및 logo image overlay 1차 구현
- [x] `clipper1_video_render` recipe-declared image zoom/pan motion effects 1차 구현
- [x] `clipper1_video_render` legacy image automatic zoom/pan motion parity 1차 구현
- [x] `clipper1_video_render` render job 단위 remote media/layout/logo/TTS/BGM URL staging 구현
- [x] `clipper1_video_render` legacy local layout/template asset resolution 구현
- [x] `clipper1_video_render` legacy render layout assets를 Python worker package 내부에 bundle
- [x] `clipper1_video_render` legacy render layout asset import script 추가
- [x] 기존 Clipper1 84-row catalog layout_image와 Python worker bundle coverage validator 추가
- [x] 기존 Clipper1 대표 template render smoke runner 추가
- [x] 현재 Clipper2 legacy-template smoke output을 별도 regression baseline frame fixture로 승격
- [x] 실제 legacy Clipper1 reference frame export를 받아 `clipper1_golden_frames` pixel-level parity fixture 채우기
- [x] `clipper1_video_render` project/subtitle text를 legacy PNG overlay 기본 경로로 전환
- [x] `clipper1_video_render` legacy main title font-size fit 구현
- [x] `clipper1_video_render` legacy subtitle long-line wrapping 구현
- [x] `clipper1_video_render` legacy logo image scale/crop parity 구현
- [x] `clipper1_video_render` legacy full-height layout final overlay stage parity 구현
- [x] Store/Dashboard에서 Workflow readiness와 Runtime provider status를 분리하는 UI 계획 정정
- [x] `clipper1_video_render` headless worker를 Store/Dashboard user-visible list에서 숨김
- [x] Clipper Studio workflow 재설계 문서 작성
- [ ] `ProjectManifest` 최소 공통 schema 확정
- [x] `workflow.clipper_studio` descriptor 추가
- [x] Angular `/clipper-studio` 제작 화면 추가
- [x] NestJS Clipper Studio project shell/create/update API 추가
- [x] `/projects` Clipper Studio presenter 추가
- [x] prompt/text deterministic draft generation API 추가
- [x] prompt/text draft generation을 NestJS job/progress/cancel model로 전환
- [x] `llm.script` facade를 deterministic adapter 뒤로 분리
- [x] Clipper Studio seed media/TTS/logo/layout artifact preparation 추가; silent BGM 기본 생성 제거
- [x] Clipper Studio render output을 `video.render.legacy_clipper1.python_worker`에 연결
- [x] render 완료 결과를 Clipper Studio manifest final output으로 승격
- [x] Clipper Studio detail에 final MP4/thumbnail preview 1차 연결
- [x] Clipper Studio render 완료 후 manifest refresh 보정
- [x] Clipper Studio edit-state 저장 API/client 추가
- [x] Clipper Studio title visibility/logo text/TTS speed 편집 UI 추가
- [x] Clipper Studio Clipper1 template catalog 선택 UI 추가
- [x] Clipper1 template catalog JSON file source 연결
- [x] Clipper1 template 1 fixed ratio catalog asset placeholder 제거 및 `16:9` row 추가
- [x] 기존 Clipper1 운영 `templates` export 기반 84-row legacy catalog 이관
- [x] 기존 Clipper1 template UI thumbnail/origin asset local bundle 및 preset preview URL 연결
- [x] 기존 Clipper1 template UI thumbnail/origin asset import script 추가
- [x] Clipper1 제작 화면에서 published Template Builder custom preset preview video 연결
- [x] Template Builder sample render thumbnail artifact를 published preset `preview.remoteImageUrl`로 연결
- [ ] Clipper1 template catalog DB/remote source 연결
- [x] Clipper1 legacy `VideoService` video/GIF motion parity 구현

## Phase 10: Projects UI Component Split

- [x] `ProjectsComponent`에서 실행 큐를 `ProjectsQueueComponent`로 분리
- [x] 완료 작업 리스트를 `ProjectsHistoryListComponent`로 분리
- [x] 상세 영역 shell을 `ProjectsDetailPanelComponent`로 분리
- [x] 대사 결과 상세와 안무 결과 상세를 각각 전용 컴포넌트로 분리
- [x] clip/player overlay를 `ProjectsClipOverlayComponent`로 분리
- [x] 분리 후 `projects.component.scss`는 page layout shell만 남기고, feature별 SCSS를 각 컴포넌트로 이동
- [x] Angular `anyComponentStyle` budget은 조정하지 않고 component split으로 warning 없이 통과

## 현재 보류/주의

- root `/Users/jina/project/adlight` 자체는 git repo가 아니다. `.codex` 문서는 현재 로컬 문서다.
- Legacy Clipper1 25개 golden fixture는 현재 `maxMismatchRatio=0.0006` 기준으로 통과한다. 최신 worst는 `template-17-16_9` `0.0005690586419753086`다.
- full app packaging은 Node 22 LTS와 sandbox 밖 실행에서 성공했다. Codex sandbox 안에서는 nvm Node 기반 Angular build가 멈출 수 있다.
- NestJS control plane 전환은 큰 구조 변경이므로, 계속 작은 vertical slice 단위로 빌드/런타임 검증한다.
- 각 세션 시작 시 repo별 `git status --short --branch`를 다시 확인한다. 특정 PC의 임시 로컬 변경 상태를 장기 인계 조건으로 고정하지 않는다.
