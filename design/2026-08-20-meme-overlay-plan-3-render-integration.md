# 밈 오버레이 구현 계획 3/3 — 매니페스트·최종 렌더·재편집

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** 편집 상태를 프로젝트 매니페스트에 보존하고, 기존 clipper_video_render 경로가 투명 WebM 영상과 효과음을 배경 쇼츠에 합성해 1080×1920 MP4를 만들며, 보관함에서 같은 상태로 다시 편집하게 한다.

**Architecture:** 새 Nest workflow는 공용 ProjectManifest, RenderRecipeProvider, ClipperRenderPayloadMapper, VideoRenderService를 확장한다. reserve→submit→rollback은 VideoRenderService의 원자 helper 하나로 통합해 댓글·랭킹·배리에이션도 같은 경로로 이관한다. Python은 별도 렌더러를 만들지 않고 기존 LocalRenderAdapter의 segment concat 이후 영상 단계와 AudioMixer에 optional meme_overlays 단계를 추가한다. payload에 meme_overlays가 없으면 기존 명령 경로가 완전히 같아야 한다.

**Tech Stack:** NestJS 11, class-validator, project-manifest.v1, render-recipe.v1, Python 3.11, FFmpeg, VP9 alpha, Opus/AAC, pytest, node:test

**Spec:** [밈 오버레이 플러그인 교차 레포 설계](./2026-08-20-meme-overlay-plugin-design.md) §9, §12–§16

**Depends on:**

- [Plan 1 — 카탈로그·디스크 캐시](./2026-08-20-meme-overlay-plan-1-catalog-cache.md)
- [Plan 2 — 편집기·타임라인·실시간 프리뷰](./2026-08-20-meme-overlay-plan-2-editor-preview.md)

## Global Constraints

- 최종 렌더는 선택 시 캐시된 동일 overlay.webm을 사용한다. 세 번째 render-source 파일을 만들지 않는다.
- 요청은 asset ID+version만 신뢰하지 않고 catalog metadata와 캐시 checksum을 다시 검증한다.
- project manifest에는 cache 절대 경로나 localhost URL을 저장하지 않는다. assetId+assetVersion+표시 snapshot만 저장한다.
- timelineStart/End는 출력 전체 기준, sourceStart/End는 밈 파일 기준으로 이름과 타입에서 분리한다.
- 동시 활성 최대 2개를 Nest에서도 다시 검증한다.
- Python은 meme_overlays가 없을 때 새 input, filter, audio command를 만들지 않는다.
- 기존 댓글 PNG/랭킹 overlay 파이프라인을 복제하거나 우회하지 않는다.
- 배경 영상은 contain+black letterbox이고 Angular preview와 같은 기하를 사용한다.
- 아래 checkpoint는 커밋 경계 제안일 뿐이다. 사용자 요청 전 commit/push하지 않는다.

---

## Task 1: 공용 렌더 예약 원자 연산

**Files**

- Modify: desktop/clipper_nestjs/src/modules/video-render/video-render.service.ts
- Modify: desktop/clipper_nestjs/test/video-render-service.test.js
- Modify: desktop/clipper_nestjs/src/modules/comment-overlay-render/application/comment-overlay-render.service.ts
- Modify: desktop/clipper_nestjs/test/comment-overlay-render-service.test.js
- Modify: desktop/clipper_nestjs/src/modules/ranking-render/application/ranking-render.service.ts
- Modify: desktop/clipper_nestjs/test/ranking-render-service.test.js
- Modify: desktop/clipper_nestjs/src/modules/variation/application/variation.service.ts
- Modify: relevant variation service tests that assert reserve/submit

**Produces**

~~~ts
interface ReserveAndSubmitRenderInput {
  jobId: string;
  baseParams: Record<string, unknown>;
  auth: AuthContext;
  message: string;
  manifest: ProjectManifest;
  outputId: string;
}

async reserveAndSubmit(input: ReserveAndSubmitRenderInput): Promise<JobQueuedResult>;
~~~

- [ ] **Step 1: VideoRenderService 실패 테스트를 추가한다.**

Assertions:

- reserve 후 submitReserved 호출
- submit 성공 시 queued result 반환
- submit 실패 시 failReserved 정확히 1회 후 원래 오류 rethrow
- reserve 자체 실패 시 failReserved 호출하지 않음
- manifest는 caller가 reserve 전에 완성하므로 builder/probe 실패는 helper에 들어오지 않음

- [ ] **Step 2: 실패를 확인한다.**

Run: npm run build && node --test test/video-render-service.test.js

Expected: FAIL — reserveAndSubmit missing.

- [ ] **Step 3: 기존 reserve/submit/fail 메서드 위에 helper를 구현한다.**
- [ ] **Step 4: 댓글·랭킹·배리에이션의 같은 try/catch 블록을 helper 호출로 교체한다. 기존 사본을 남기지 않는다.**
- [ ] **Step 5: 대상 회귀를 통과시킨다.**

Run:

~~~sh
npm run build
node --test test/video-render-service.test.js test/comment-overlay-render-service.test.js test/ranking-render-service.test.js test/variation-*.test.js
~~~

- [ ] **Checkpoint:** render submission reuse seam review.

## Task 2: Nest 렌더 요청 DTO와 독립 validation

**Files**

- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/presentation/dto/meme-overlay-render.dto.ts
- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/domain/meme-overlay-render.model.ts
- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/domain/meme-overlay-validation.ts
- Create: desktop/clipper_nestjs/test/meme-overlay-render-dto.test.js
- Create: desktop/clipper_nestjs/test/meme-overlay-validation.test.js

**Canonical server input**

~~~ts
export interface MemeOverlayRenderInput {
  sourcePath: string;
  sourceLabel?: string;
  instances: Array<{
    id: string;
    assetId: string;
    assetVersion: string;
    assetName: string;
    sourceStartMs: number;
    sourceEndMs: number;
    timelineStartMs: number;
    transform: {
      xPct: number;
      yPct: number;
      wPct: number;
      hPct: number;
    };
    audio: { muted: boolean; volume: number };
    zIndex: number;
  }>;
}
~~~

- [ ] **Step 1: class-validator DTO 실패 테스트를 쓴다.**

Assertions:

- sourcePath non-empty
- instances ArrayNotEmpty
- ID/version regex
- all ms finite integer and non-negative
- x/y 0..100, w/h >0..100, volume 0..1
- nested whitelist rejects unknown fields

- [ ] **Step 2: pure domain validation 실패 테스트를 쓴다.**

Input collaborators: backgroundDurationMs and Map<assetId@version, metadata>.

Cases:

- sourceStart < sourceEnd <= asset duration
- timelineEnd <= background duration
- x+w <=100, y+h <=100
- [start,end) 기준 max concurrency 2
- asset ID/version missing
- duplicate instance id
- minimum duration 500ms
- zIndex finite integer; duplicate zIndex는 stable id tie-break 허용

- [ ] **Step 3: 실패를 확인한다.**
- [ ] **Step 4: DTO와 pure validator를 구현한다.**
- [ ] **Step 5: 대상 테스트를 통과시킨다.**

Frontend timing 함수를 import하지 않는다. 서로 다른 런타임의 같은 계약을 독립 검증하는 것이 보안 경계다.

## Task 3: 밈 프로젝트 매니페스트 builder

**Files**

- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/application/meme-overlay-manifest.builder.ts
- Create: desktop/clipper_nestjs/test/meme-overlay-manifest-builder.test.js

**Artifacts**

~~~text
media.source
media.meme.<instanceId>
render.video.main -> renders/meme_overlay.mp4
~~~

**editState**

~~~ts
{
  templatePresetId: 'meme-overlay.passthrough.v1',
  templatePresetSnapshot: MemeOverlayPassthroughPreset,
  sourceLabel?: string,
  sourceAudioVolume: 1,
  memeOverlay: {
    schemaVersion: 'meme-overlay-project.v1',
    source: {
      sourcePath,
      sourceLabel,
      durationMs,
      width,
      height
    },
    instances: request.instances
  }
}
~~~

- [ ] **Step 1: 실패 builder 테스트를 쓴다.**

Assertions:

- output 1080x1920, duration=background duration
- background clip slot 전체 길이, fit contain
- source audio volume 1
- each meme artifact uri/access는 검증된 local cache path
- editState에는 local meme cache path/localhost URL이 없음
- assetName/version/source trim/transform/audio/zIndex snapshot 보존
- workflow/display/badges/title/output destination

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: builder를 구현한다.**

댓글 builder를 복사하지 않는다. ProjectManifest literal은 새 workflow의 고유 editState/artifact를 명시한다. 추출할 완전히 같은 5줄 이상의 primitive가 실제로 확인될 때만 project-manifest 아래 좁은 helper로 옮기고 댓글도 함께 호출하게 한다.

- [ ] **Step 4: 대상 테스트를 통과시킨다.**

## Task 4: RenderRecipe와 clipper payload 확장

**Files**

- Modify: desktop/clipper_nestjs/src/modules/project-manifest/domain/render-recipe.model.ts
- Modify: desktop/clipper_nestjs/src/modules/project-manifest/application/render-recipe-provider.ts
- Modify: desktop/clipper_nestjs/src/modules/project-manifest/infrastructure/clipper-render-payload-mapper.ts
- Create: desktop/clipper_nestjs/test/meme-overlay-render-recipe.test.js
- Create: desktop/clipper_nestjs/test/meme-overlay-render-payload.test.js
- Modify: desktop/clipper_nestjs/test/comment-overlay-*.test.js
- Modify: desktop/clipper_nestjs/test/ranking-render-pipeline.test.js

**Recipe extension**

~~~ts
export type RenderOverlayRole =
  | existing roles
  | 'meme';

interface MemeOverlayTrackParams {
  sourceStartSec: number;
  sourceEndSec: number;
  xPct: number;
  yPct: number;
  wPct: number;
  hPct: number;
  muted: boolean;
  volume: number;
  zIndex: number;
}
~~~

Each OverlayTrack uses:

- artifactId = media.meme.instanceId
- startSec/endSec = global output timeline
- role = meme
- params = source range, transform, audio, z-order

**Payload extension**

~~~ts
meme_overlays?: Array<{
  mediaUrl: string;
  timelineStartSec: number;
  timelineEndSec: number;
  sourceStartSec: number;
  sourceEndSec: number;
  xPct: number;
  yPct: number;
  wPct: number;
  hPct: number;
  muted: boolean;
  volume: number;
  zIndex: number;
}>;
~~~

- [ ] **Step 1: recipe 실패 테스트를 쓴다.**

Assertions: artifact resolution, global times, params mapping, zIndex sort stable by overlay id, no meme tracks for old editState.

- [ ] **Step 2: payload 실패 테스트를 쓴다.**

Assertions: exact camel→snake mapping above, media URL from artifact, global timeline naming, no meme_overlays key when absent.

- [ ] **Step 3: 실패를 확인한다.**
- [ ] **Step 4: provider의 기존 overlay 배열에 memeOverlaysFor를 합친다. 별도 recipe pipeline을 만들지 않는다.**
- [ ] **Step 5: mapper의 기존 optional payload 조립에 memeOverlaysFor를 합친다.**
- [ ] **Step 6: 대상+댓글+랭킹 회귀를 통과시킨다.**
- [ ] **Checkpoint:** manifest→recipe→payload contract review.

## Task 5: Nest workflow service/controller/module

**Files**

- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/application/meme-overlay-render.service.ts
- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/presentation/meme-overlay-render.controller.ts
- Create: desktop/clipper_nestjs/src/modules/meme-overlay-render/meme-overlay-render.module.ts
- Create: desktop/clipper_nestjs/test/meme-overlay-render-service.test.js
- Create: desktop/clipper_nestjs/test/meme-overlay-render-controller.test.js
- Modify: desktop/clipper_nestjs/src/app.module.ts

- [ ] **Step 1: service 실패 테스트를 쓴다.**

Sequence assertions:

1. SourceService.inspect로 background duration/size/label 확인
2. MemeCatalogService로 각 unique ID+version metadata resolve
3. MemeAssetCacheService로 각 unique overlay file checksum 확인/prepare
4. pure domain validation
5. poster는 existing ensureLocalMediaThumbnail/coverSourceAsset 사용
6. manifest build
7. VideoRenderService.reserveAndSubmit 1회

예약 전 단계가 실패하면 reserve가 호출되지 않아야 한다.

baseParams:

~~~ts
{
  mode: 'execute',
  feature: 'meme_overlay',
  project_id: projectId,
  title: sourceLabel ?? '밈 오버레이',
  source_assets: optionalCover
}
~~~

- [ ] **Step 2: controller 실패 테스트를 쓴다.**

Assertions: POST /meme-overlay/render, AuthContextService.fromHttpHeaders, DTO validation, response jobId.

- [ ] **Step 3: 실패를 확인한다.**
- [ ] **Step 4: service/controller/module을 구현하고 AppModule에 등록한다.**
- [ ] **Step 5: 대상 테스트와 Nest 전체 회귀를 실행한다.**

Run:

~~~sh
npm run build
node --test test/meme-overlay-*.test.js
node --test test/*.test.js
~~~

Expected: all PASS.

## Task 6: Python payload normalization

**Files**

- Create: desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/meme_overlays.py
- Create: desktop/clipper_python/tests/test_clipper_video_render_meme_overlay_model.py

**Produces**

~~~py
@dataclass(frozen=True)
class MemeOverlay:
    media_url: str
    timeline_start: float
    timeline_end: float
    source_start: float
    source_end: float
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float
    muted: bool
    volume: float
    z_index: int

def normalized_meme_overlays(payload: dict[str, Any]) -> list[MemeOverlay]:
    ...
~~~

- [ ] **Step 1: 실패 tests를 쓴다.**

Assertions: optional absent→[], invalid entry skip or ValueError policy consistent with existing coerce boundary, stable zIndex sort, source/timeline durations match, normalized numeric clamps are validation defense not contract widening.

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: pure parser를 구현한다.**
- [ ] **Step 4: 대상 test를 통과시킨다.**

## Task 7: FFmpeg 투명 영상 layer 합성

**Files**

- Modify: desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/filter_graph.py
- Modify: desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/video_renderer.py
- Modify: desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/local_render_adapter.py
- Create: desktop/clipper_python/tests/test_clipper_video_render_meme_overlays.py
- Modify: desktop/clipper_python/tests/test_clipper_video_render_contract.py

**New optional stage**

~~~text
render segments
→ concat
→ existing final layout if needed
→ timed meme video layers if meme_overlays exists
→ existing audio mux
~~~

- [ ] **Step 1: pure filter graph 실패 테스트를 쓴다.**

For each sorted overlay:

- input decoder option libvpx-vp9
- seek=sourceStartSec, duration=timelineEnd-timelineStart
- trim/setpts resets PTS then adds timelineStart/TB
- scale to even pixel size derived from 1080x1920 percentages
- format=yuva420p
- overlay x/y derived from percentages
- enable uses start inclusive/end exclusive expression
- eof_action=pass and shortest=0
- final format yuv420p

- [ ] **Step 2: recording runner 실패 테스트를 쓴다.**

Assertions:

- payload absent: overlay_meme_layers is not called and existing concat→mux path unchanged
- payload present: visual intermediate path advances once
- output H.264 command maps final video label, no audio
- same local cached media path accepted by RemoteAssetStager/asset resolver boundary

- [ ] **Step 3: 실패를 확인한다.**
- [ ] **Step 4: filter_graph helper와 VideoRenderer.overlay_meme_layers를 구현한다.**
- [ ] **Step 5: LocalRenderAdapter에서 optional post-concat stage를 호출한다.**
- [ ] **Step 6: command tests를 통과시킨다.**
- [ ] **Step 7: real FFmpeg alpha test를 추가한다.**

Fixture는 테스트 중 lavfi color background와 작은 VP9 alpha overlay를 생성한다. 중앙/바깥 픽셀을 추출해 투명 영역은 배경색, 불투명 영역은 overlay색인지 확인한다. 제공 Angry cat 파일의 절대 경로를 automated test fixture로 사용하지 않는다.

- [ ] **Step 8: real test를 통과시킨다.**
- [ ] **Checkpoint:** video alpha composition review.

## Task 8: 밈 효과음 track을 기존 AudioMixer에 추가

**Files**

- Modify: desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/audio_mixer.py
- Create: desktop/clipper_python/tests/test_clipper_video_render_meme_audio.py
- Modify: desktop/clipper_python/tests/test_local_render_audio_mixer.py
- Modify: desktop/clipper_python/tests/test_clipper_video_render_source_audio.py

**Optional audio order**

~~~text
existing TTS/BGM/SFX base
→ existing source audio
→ optional meme effect track
→ limiter only when meme track is present
~~~

- [ ] **Step 1: command-capture 실패 테스트를 쓴다.**

Assertions:

- muted/volume=0/no audio stream은 input 제외
- audio source uses same sourceStart and duration as video
- volume filter
- adelay=timelineStart in ms for both channels
- atrim to total output duration
- multiple instances amix normalize=0
- background/current mix + meme track amix normalize=0
- final alimiter
- absent meme_overlays means current command list/summary keys unchanged

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: AudioMixer._build_meme_audio_track을 구현하고 build_mix 마지막 optional branch에 연결한다.**
- [ ] **Step 4: command tests와 existing source/sfx tests를 통과시킨다.**
- [ ] **Step 5: real FFmpeg test를 추가한다.**

Generate background sine and short overlay sine, render, then ffprobe duration/audio stream and silence/non-silence windows to confirm delay+trim.

- [ ] **Step 6: real test를 통과시킨다.**

## Task 9: Python 전체 회귀

- [ ] **Step 1: targeted tests**

Run:

~~~sh
uv run pytest \
  tests/test_clipper_video_render_meme_overlay_model.py \
  tests/test_clipper_video_render_meme_overlays.py \
  tests/test_clipper_video_render_meme_audio.py -q
~~~

- [ ] **Step 2: existing render regressions**

Run:

~~~sh
uv run pytest \
  tests/test_clipper_video_render_contract.py \
  tests/test_clipper_video_render_comment_overlays.py \
  tests/test_clipper_video_render_ranking_overlays.py \
  tests/test_clipper_video_render_source_audio.py \
  tests/test_clipper_video_render_sfx_mix.py \
  tests/test_local_render_audio_mixer.py -q
~~~

- [ ] **Step 3: full suite/lint/type**

Run:

~~~sh
uv run pytest -q
uv run ruff check .
uv run mypy plugins/clipper_video_render/clipper_video_render
~~~

Expected: all PASS.

## Task 10: Angular render 제출과 manifest 재편집 복원

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay-manifest.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay-manifest.spec.ts
- Modify: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.store.ts
- Modify: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.store.spec.ts
- Modify: desktop/clipper_angular/src/features/meme-overlay/pages/meme-overlay-setup/meme-overlay-setup.component.{ts,html,spec.ts}
- Modify: desktop/clipper_angular/src/shell/projects/models/projects-view.ts
- Modify: desktop/clipper_angular/src/shell/projects/models/project-card.builder.ts
- Modify: desktop/clipper_angular/src/shell/projects/projects/projects.component.ts
- Modify: desktop/clipper_angular/src/shell/projects/projects/projects.component.spec.ts

- [ ] **Step 1: manifest parser 실패 tests를 쓴다.**

Assertions:

- schemaVersion 검증
- background path/label/duration/dimensions 복원
- all instance snapshots 복원
- cache path/stream URL이 저장본에 없어도 정상
- malformed/third-overlap manifest는 사용자용 복원 오류

- [ ] **Step 2: store loadProject 실패 tests를 쓴다.**

Sequence:

1. generic project manifest fetch
2. background restore through shared VideoSourceIngestService
3. unique assetId+version overlay prepare
4. all prepared then EDITOR
5. cache missing+offline이면 인터넷 필요 오류와 retry

- [ ] **Step 3: render submit 실패 tests를 쓴다.**

Assertions:

- source+instances exact request
- zero instances disabled
- saving double-submit guard
- success routes /projects?plugin=clipper_video_render&job=...
- failure remains editor with toast

- [ ] **Step 4: projects classification/route 실패 tests를 쓴다.**

Expected:

- params.feature=meme_overlay → moduleName meme_overlay
- tall card, label/chip/icon
- edit route /meme-overlay?project=<projectId>
- comment/ranking/shortform routing unchanged

- [ ] **Step 5: parser/store/page/projects를 구현한다.**
- [ ] **Step 6: targeted and full Angular tests를 통과시킨다.**

Run:

~~~sh
./node_modules/.bin/ng test --watch=false
npm run test:styles
npm run build
~~~

Expected: all PASS.

## Task 11: 교차 레포 end-to-end 검증

- [ ] 로컬 Web API test catalog에 권리 승인 대신 dev-only Angry cat fixture metadata를 연결한다.
- [ ] 플러그인 설치 → 첫 진입 12-card page 준비 spinner → source ingest를 확인한다.
- [ ] Angry cat을 한 번 추가한 직후에만 overlay.webm이 다운로드되는지 확인한다.
- [ ] 두 instance를 일부 겹치고 서로 다른 위치/크기/volume/zIndex로 설정한다.
- [ ] Angular preview의 기준 프레임을 같은 timestamp에서 캡처한다.
- [ ] 영상 생성을 실행하고 queue→completed→project card를 확인한다.
- [ ] 결과 MP4의 같은 timestamp를 추출해 위치/크기/alpha/z-order가 preview와 허용 오차 내인지 비교한다.
- [ ] background audio와 meme audio가 모두 있고 muted instance는 없는지 확인한다.
- [ ] card의 편집을 눌러 source/instances/timing/transform/audio가 복원되는지 확인한다.
- [ ] cache를 비우고 offline에서 재편집 시 명확한 인터넷 필요 오류가 나는지 확인한다.
- [ ] online retry 후 정확한 asset version이 다시 받아지는지 확인한다.

## Task 12: 패키지 smoke와 문서 동기화

**Files**

- Modify if needed: desktop/clipper_electron packaging tests/config only; no meme asset inclusion
- Modify: .codex/design/2026-08-20-meme-overlay-plugin-design.md
- Create: .codex/features/clipper-studio/records/2026/08/2026-08-20-meme-overlay-implementation-record.md

- [ ] Angular production build
- [ ] Nest build+bundle
- [ ] Python plugin packaged worker smoke
- [ ] Electron packaged app 실행
- [ ] package archive에 card-preview.webm/overlay.webm 없음
- [ ] localhost Range 재생과 render worker가 packaged path에서도 동작
- [ ] 실제 구현에서 바뀐 수치/계약만 .codex 설계 문서에 반영하고 결정 자체를 소급 변경하지 않음
- [ ] MEME_ASSET_CDN_HOSTS 등 운영 설정과 최종 검증 결과를 .codex 구현 기록에 남김
- [ ] 각 repo git diff --check와 status를 보고 unrelated user changes가 없는지 확인

## Plan 3 완료 기준

- render 요청부터 manifest→recipe→payload→Python까지 하나의 명시적 meme_overlays 계약이 이어진다.
- 배경+투명 밈 영상+효과음이 최종 1080×1920 H.264/AAC MP4에 합성된다.
- meme_overlays 없는 기존 워크플로의 Python command path가 변하지 않는다.
- reserve→submit→rollback 사본이 제거되고 공용 VideoRenderService helper로 통일된다.
- 프로젝트에는 ID/version 기반 편집 상태만 남고 cache 위치가 남지 않는다.
- 보관함에서 재편집과 재렌더가 가능하다.
- Electron 배포 파일에 밈 에셋이 포함되지 않는다.
