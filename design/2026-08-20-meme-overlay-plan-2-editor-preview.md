# 밈 오버레이 구현 계획 2/3 — 편집기·타임라인·실시간 프리뷰

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** 사용자가 배경 쇼츠를 불러오고 원격 밈 카드를 선택해 9:16 스테이지와 동적 1~2레인 타임라인에서 위치·크기·구간·소리·앞뒤 순서를 편집하며, 배경 1개+밈 최대 2개를 실시간으로 미리 본다.

**Architecture:** 기존 SourceInputComponent, SourceInspectService, 파일 선택, YouTube 로그인, 페이지/오류 UI를 직접 사용한다. 반복된 소스 인제스트·정규화 좌표·transport만 작은 공용 코드로 추출하고 기존 댓글/랭킹도 새 공용 코드로 이관한다. 밈 카탈로그, interval 모델, 2-slot 동영상 동기화는 밈 기능 전용으로 작성한다. 댓글 컴포넌트를 복사하거나 feature 간 import하지 않는다.

**Tech Stack:** Angular 22 standalone components, signals, NgRx Signal Store, HTMLVideoElement, requestAnimationFrame, Jasmine/Karma

**Spec:** [밈 오버레이 플러그인 교차 레포 설계](./2026-08-20-meme-overlay-plugin-design.md) §3.3, §6–§9, §14.2, §15

**Depends on:** [Plan 1 — 카탈로그·디스크 캐시](./2026-08-20-meme-overlay-plan-1-catalog-cache.md)

## Global Constraints

- 메인 프리뷰 DOM의 video decoder 상한은 배경 1 + 밈 2다. 인스턴스 개수만큼 video를 만들지 않는다.
- 동시 활성 밈은 반열림 구간 [start, end) 기준 최대 2개다.
- 레인 번호는 저장하지 않고 매번 interval partition으로 파생한다.
- WebGL, 브라우저 chromakey, FFmpeg 임시 프리뷰, 자동 성능 감지는 구현하지 않는다.
- overlay.webm 다운로드는 사용자가 카드를 선택/추가할 때만 한다. 카드 목록을 열었다고 overlay variant를 받지 않는다.
- 메인 재생 중 카드 video는 pause한다.
- 카탈로그의 `cardStatus`는 `ready | failed` 판별자다. ready 항목만 `cardStreamPath`를 가지며 failed 항목은 `cardErrorCode`로 개별 재시도를 표시한다.
- 좌표 정본은 xPct/yPct/wPct/hPct이고 스테이지 전체 안으로 clamp한다.
- 기존 댓글/랭킹 코드를 복사하지 않는다. 공용 추출 뒤 기존 소비자도 같은 implementation을 import한다.
- UniversalOverlayEditor 같은 거대 공통 editor는 만들지 않는다.
- `overlayStreamUrl`은 runtime-only map에 `assetId@version` 키로 보관한다. canonical `MemeOverlayInstance`와 project manifest에는 localhost URL이나 절대 경로를 넣지 않는다.
- 아래 checkpoint는 커밋 경계 제안일 뿐이다. 사용자 요청 전 commit/push하지 않는다.

## 변경 파일 구조

~~~text
desktop/clipper_angular/src/
  core/source/
    video-source-ingest.service.ts
  shared/media-stage/
    normalized-rect.ts
  shared/media-transport/
    media-transport.component.{ts,html,scss}
  features/meme-overlay/
    meme-overlay.providers.ts
    models/
      meme-overlay.ts
      meme-overlay-timing.ts
      meme-overlay-manifest.ts
    flow/
      meme-overlay.state.ts
      meme-overlay.store.ts
    services/
      meme-overlay-api.ts
    components/
      meme-library/
      meme-overlay-preview/
      meme-overlay-settings/
      meme-overlay-timeline/
    pages/
      meme-overlay-setup/
~~~

---

## Task 1: 공용 영상 소스 인제스트 facade 추출

**Files**

- Create: desktop/clipper_angular/src/core/source/video-source-ingest.service.ts
- Create: desktop/clipper_angular/src/core/source/video-source-ingest.service.spec.ts
- Modify: desktop/clipper_angular/src/core/index.ts
- Modify: desktop/clipper_angular/src/features/comment-overlay/flow/comment-overlay.store.ts
- Modify: desktop/clipper_angular/src/features/comment-overlay/flow/comment-overlay.store.spec.ts
- Modify: desktop/clipper_angular/src/features/ranking/flow/ranking.store.ts
- Modify: desktop/clipper_angular/src/features/ranking/flow/ranking.store.spec.ts

**Produces**

~~~ts
export type VideoSourceSelection =
  | { type: 'local_file'; path: string }
  | { type: 'youtube_url'; url: string };

export interface IngestedVideoSource {
  sourcePath: string;
  sourceLabel: string;
  durationMs: number;
  width: number;
  height: number;
  streamUrl: string;
  thumbnailUrl?: string;
}

@Injectable({ providedIn: 'root' })
export class VideoSourceIngestService {
  ingest(selection: VideoSourceSelection): Promise<IngestedVideoSource>;
  restoreLocalPath(path: string, label?: string): Promise<IngestedVideoSource>;
}
~~~

- [ ] **Step 1: facade 실패 테스트를 작성한다.**

Assertions:

- local_file은 SourceInspectService.ingest에 mediaType video로 전달
- youtube_url은 URL input으로 전달
- localPath 누락은 사용자용 오류
- BackendLocator base URL 조회와 /sources/stream?path= URL 조립은 facade 한 곳에서 수행
- 저장된 label이 있으면 restore에서 ingest cache filename보다 우선

- [ ] **Step 2: 실패를 확인한다.**

Run:

~~~sh
./node_modules/.bin/ng test --watch=false --include='src/core/source/video-source-ingest.service.spec.ts'
~~~

Expected: FAIL — service missing.

- [ ] **Step 3: facade를 구현한다.**
- [ ] **Step 4: 댓글 store의 local/YouTube 분기와 stream URL 조립을 facade 호출로 교체한다.**
- [ ] **Step 5: 랭킹 store의 ingestClip/restore URL 조립을 facade 호출로 교체한다.**
- [ ] **Step 6: 세 대상 spec를 통과시킨다.**

이 단계가 끝나면 소스 인제스트 규칙은 한 파일에 있고 댓글·랭킹·밈은 모두 그것을 직접 호출해야 한다.

- [ ] **Checkpoint:** source reuse seam review.

## Task 2: 공용 정규화 좌표 순수 함수

**Files**

- Create: desktop/clipper_angular/src/shared/media-stage/normalized-rect.ts
- Create: desktop/clipper_angular/src/shared/media-stage/normalized-rect.spec.ts
- Modify: desktop/clipper_angular/src/features/comment-overlay/components/comment-overlay-preview/comment-overlay-preview.component.ts
- Modify: desktop/clipper_angular/src/features/comment-overlay/components/comment-overlay-preview/comment-overlay-preview.component.spec.ts

**Produces**

~~~ts
export interface NormalizedRect {
  xPct: number;
  yPct: number;
  wPct: number;
  hPct: number;
}

export function clampNormalizedRect(rect: NormalizedRect): NormalizedRect;
export function clampMeasuredPositionPct(
  positionPct: number,
  contentPx: number,
  stagePx: number,
): number;
export function moveNormalizedRect(
  origin: NormalizedRect,
  deltaPx: { x: number; y: number },
  stagePx: { width: number; height: number },
): NormalizedRect;
export function resizeNormalizedRectFromCorner(
  origin: NormalizedRect,
  deltaPx: { x: number; y: number },
  stagePx: { width: number; height: number },
  sourceAspectRatio: number,
  minimumWidthPct?: number,
): NormalizedRect;
export function resizeNormalizedRectFreeFromCorner(
  origin: NormalizedRect,
  deltaPx: { x: number; y: number },
  stagePx: { width: number; height: number },
  minimumSizePct?: { width: number; height: number },
): NormalizedRect;
export function normalizedRectToPixels(
  rect: NormalizedRect,
  canvas: { width: number; height: number },
): { x: number; y: number; width: number; height: number };
~~~

- [ ] **Step 1: 경계/등비 resize 실패 테스트를 작성한다.**

Cases: 음수 이동, 우하단 overflow, zero-size stage no-op, 16:9/1:1/portrait aspect 유지, minimum size, measured DOM 카드 clamp, 댓글의 독립 w/h resize 보존, 1080x1920 px 변환.

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: 순수 함수를 구현한다.**
- [ ] **Step 4: 댓글 preview의 clamp/delta 수식을 공용 함수 호출로 바꾼다.**

댓글 모델의 x/y/w/h 이름은 바꾸지 않는다. adapter 함수로 NormalizedRect에 매핑하여 기존 저장 계약을 유지한다. 댓글 HTML 카드의 기존 resize는 가로·세로 독립 조절이므로 이를 영상 밈의 등비 resize로 바꾸지 않는다. 대신 같은 파일의 free-resize 순수 함수로 기존 계산을 옮기고, `resizeNormalizedRectFromCorner`의 등비 계산은 밈 영상 레이어가 사용한다.

- [ ] **Step 5: 공용/댓글 spec를 통과시킨다.**
- [ ] **Checkpoint:** geometry reuse seam review.

## Task 3: 공용 transport presentational component

**Files**

- Create: desktop/clipper_angular/src/shared/media-transport/media-transport.component.ts
- Create: desktop/clipper_angular/src/shared/media-transport/media-transport.component.html
- Create: desktop/clipper_angular/src/shared/media-transport/media-transport.component.scss
- Create: desktop/clipper_angular/src/shared/media-transport/media-transport.component.spec.ts
- Modify: desktop/clipper_angular/src/features/comment-overlay/components/comment-overlay-preview/comment-overlay-preview.component.{ts,html,scss,spec.ts}
- Modify: desktop/clipper_angular/src/features/ranking/components/ranking-preview/ranking-preview.component.{ts,html,scss,spec.ts}

**Component contract**

~~~ts
currentSec = input.required<number>();
durationSec = input.required<number>();
playing = input.required<boolean>();
disabled = input(false);
togglePlay = output<void>();
seekFraction = output<number>();
~~~

- [ ] **Step 1: presentational component 실패 spec를 쓴다.**

Assertions:

- current/duration을 m:ss로 표시
- play/pause icon
- progress width clamp 0..100
- bar pointer down/move가 0..1 fraction 방출
- pointer up 후 global listener 제거
- disabled이면 이벤트 없음

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: component를 구현한다. video element를 직접 소유하지 않고 이벤트만 방출하게 한다.**
- [ ] **Step 4: 댓글 preview markup/함수를 component로 교체한다.**
- [ ] **Step 5: 랭킹 preview markup/함수를 component로 교체하되 랭킹의 segment switching은 feature에 남긴다.**
- [ ] **Step 6: 공용/댓글/랭킹 spec를 통과시킨다.**

공용 코드는 transport UI까지만 책임진다. 밈의 2-slot 동기화나 랭킹의 다중 clip source switching을 넣지 않는다.

- [ ] **Checkpoint:** transport reuse seam review.

## Task 4: 밈 프로젝트 모델·interval 알고리즘

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay.spec.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay-timing.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay-timing.spec.ts

**Canonical model**

~~~ts
export interface MemeOverlayInstance {
  id: string;
  assetId: string;
  assetVersion: string;
  assetName: string;
  assetDurationMs: number;
  assetWidth: number;
  assetHeight: number;
  sourceStartMs: number;
  sourceEndMs: number;
  timelineStartMs: number;
  transform: NormalizedRect;
  audio: { muted: boolean; volume: number };
  zIndex: number;
}

export interface PositionedMemeOverlay extends MemeOverlayInstance {
  timelineEndMs: number;
  lane: 0 | 1;
}
~~~

**Pure functions**

~~~ts
export interface AddMemeOverlayInput {
  id: string;
  assetId: string;
  assetVersion: string;
  assetName: string;
  assetDurationMs: number;
  assetWidth: number;
  assetHeight: number;
  playheadMs: number;
  backgroundDurationMs: number;
  transform: NormalizedRect;
  audio?: { muted: boolean; volume: number };
}

export type MemeOverlayEditErrorCode =
  | 'invalid_input'
  | 'instance_not_found'
  | 'minimum_duration'
  | 'outside_background'
  | 'outside_asset'
  | 'max_concurrent_overlays';

export type MemeOverlayEditResult =
  | { ok: true; instances: MemeOverlayInstance[]; candidate: MemeOverlayInstance }
  | { ok: false; instances: readonly MemeOverlayInstance[]; candidate: MemeOverlayInstance | null; error: { code: MemeOverlayEditErrorCode; message: string } };

timelineEndMs(instance: MemeOverlayInstance): number;
activeInstancesAt(instances: readonly MemeOverlayInstance[], timeMs: number): MemeOverlayInstance[];
assignOverlayLanes(instances: readonly MemeOverlayInstance[]): PositionedMemeOverlay[];
maxConcurrentOverlays(instances: readonly MemeOverlayInstance[]): number;
tryAddInstance(instances: readonly MemeOverlayInstance[], input: AddMemeOverlayInput): MemeOverlayEditResult;
tryMoveInstance(instances: readonly MemeOverlayInstance[], id: string, timelineStartMs: number, backgroundDurationMs: number): MemeOverlayEditResult;
tryTrimLeft(instances: readonly MemeOverlayInstance[], id: string, timelineStartMs: number, backgroundDurationMs: number): MemeOverlayEditResult;
tryTrimRight(instances: readonly MemeOverlayInstance[], id: string, sourceEndMs: number, backgroundDurationMs: number): MemeOverlayEditResult;
bringToFront(instances: readonly MemeOverlayInstance[], id: string): readonly MemeOverlayInstance[];
~~~

`MemeOverlayEditResult.instances`는 성공 시 새 canonical 배열이고 실패 시 입력 canonical 배열과 동일한 readonly 참조다. 실패해도 `candidate`에는 invalid ghost로 표시할 제안값을 돌려주되, 존재하지 않는 ID처럼 후보를 만들 수 없는 오류만 `null`이다. 후보의 중첩 `audio`/`transform`은 입력·원본과 참조를 공유하지 않는다. 추가는 `sourceStartMs=0`, `timelineStartMs=playheadMs`, `sourceEndMs=min(assetDurationMs, backgroundDurationMs-playheadMs)`, `zIndex=max+1`을 기본으로 하되 JavaScript 수 정밀도 때문에 더 큰 유한 값을 만들 수 없으면 기존 z 순서를 `0..n-1`로 정규화하고 새 후보를 `n`에 둔다. 편집 검증 순서는 유한 입력/소스 경계와 최소 길이/배경 경계/최대 동시 2개이며 기존 배열과 인스턴스를 mutate하지 않는다.

- [ ] **Step 1: 실패 테스트를 작성한다.**

Cases:

- [0,1000)과 [1000,2000)은 같은 lane
- 실제 overlap만 lane 2 생성
- stable sort는 timelineStartMs 다음 id
- 세 번째 overlap은 invalid
- 추가 기본점은 playhead, 배경 끝에 맞춰 sourceEnd trim
- 남은 구간 500ms 미만이면 추가 거부
- body drag는 timelineStartMs만 변경
- left trim은 sourceStartMs와 timelineStartMs를 함께 바꾸고 오른쪽 timeline end 유지
- right trim은 sourceEndMs만 변경
- 최소 duration 500ms
- 배경 밖/asset source 밖 거부
- invalid ghost 후보는 반환하지만 canonical instances는 원본 유지
- zIndex 정규화와 active 두 개의 앞뒤 순서

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: 순수 함수를 구현한다. lane 필드를 canonical model에 추가하지 않는다.**
- [ ] **Step 4: 대상 spec를 통과시킨다.**
- [ ] **Checkpoint:** timeline domain review.

## Task 5: 로컬 API client와 feature store

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/services/meme-overlay-api.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/services/meme-overlay-api.spec.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.state.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.store.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.store.spec.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/meme-overlay.providers.ts

**API client**

~~~ts
abstract class MemeOverlayApi {
  abstract catalog(query: { page: number; limit: 12; q?: string }): Promise<LocalMemeAssetPage>;
  abstract prepareOverlay(assetId: string, version: string): Promise<PreparedMemeOverlay & { overlayStreamUrl: string }>;
  abstract render(request: MemeOverlayRenderRequest): Promise<{ jobId: string }>;
  abstract loadProject(projectId: string): Promise<unknown>;
}
~~~

Angular의 public `ReadyLocalMemeAsset`은 Nest 응답의 `cardStreamPath`를 보존하면서 runtime-only `cardStreamUrl`을 추가한다. failed 항목에는 둘 다 생성하지 않는다. `prepareOverlay`도 wire의 `overlayStreamPath`를 보존하고 `overlayStreamUrl`을 추가해 반환한다. 두 절대 URL은 `BackendLocator`가 가리키는 localhost origin과 같은 origin이어야 하며 canonical instance/manifest에는 들어가지 않는다.

**Store state**

~~~ts
type MemeOverlayView = 'BOOTSTRAP' | 'INTAKE' | 'EDITOR';

interface MemeOverlayState {
  view: MemeOverlayView;
  catalog: LocalMemeAssetPage | null;
  catalogLoading: boolean;
  sourceLoading: boolean;
  preparingAssetIds: string[];
  preparedOverlays: Record<string, PreparedMemeOverlay & { overlayStreamUrl: string }>;
  source: IngestedVideoSource | null;
  instances: MemeOverlayInstance[];
  selectedInstanceId: string | null;
  currentMs: number;
  durationMs: number;
  playing: boolean;
  error: AppError | null;
}
~~~

Store는 `bootstrap`, `loadCatalog`, `retryCatalog`, `loadSource`, `addFromCatalog`, `selectInstance`, `setCurrentMs`, `setPlaying`, `clearError`를 이 단계에서 제공한다. 새 배경 소스는 instances/selection/playhead를 초기화하되 이미 준비된 runtime 에셋 map은 재사용할 수 있게 유지한다. `addFromCatalog`는 ready 카드와 source가 있을 때만 동작하고, `assetId@version` 준비 결과를 재사용하며, 인스턴스에는 URL/path를 복사하지 않는다.

- [ ] **Step 1: API spec를 쓴다.**

Assertions: BackendLocator 사용, catalog query encoding, prepare body/version, returned relative stream path를 absolute localhost URL로 resolve, render body shape.

- [ ] **Step 2: store 실패 spec를 쓴다.**

Assertions:

- bootstrap은 page=1, limit=12를 준비하는 동안 BOOTSTRAP/spinner
- 성공 후 INTAKE
- 실패 시 인터넷 필요 메시지와 retry
- loadSource는 VideoSourceIngestService 직접 호출
- addFromCatalog는 prepareOverlay 완료 전 instance를 추가하지 않음
- prepare 완료 결과는 `assetId@version` runtime map에 저장하고 같은 asset의 여러 instance가 같은 stream URL을 재사용
- 같은 asset을 여러 instance로 추가 가능
- domain invalid result를 error toast로 매핑
- page/search 변경 시 card page만 load하고 기존 editor instances 유지
- selected inactive block 선택 시 currentMs를 block start로 이동

- [ ] **Step 3: 실패를 확인한다.**
- [ ] **Step 4: API/store/providers를 구현한다.**
- [ ] **Step 5: 대상 spec를 통과시킨다.**
- [ ] **Checkpoint:** store/API review.

## Task 6: 플러그인 route·navigation 등록

**Files**

- Modify: desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts
- Modify: desktop/clipper_angular/src/core/navigation/app-navigation-metadata.spec.ts
- Modify: desktop/clipper_angular/src/app/app.routes.ts
- Modify: desktop/clipper_angular/src/app/app.routes.spec.ts
- Modify: desktop/clipper_angular/src/app/app.config.ts
- Modify: desktop/clipper_angular/src/core/plugins/pipeline-feature-registry.spec.ts

- [ ] **Step 1: 실패 spec를 추가한다.**

Expected metadata:

~~~ts
{
  name: 'meme_overlay',
  label: '밈 오버레이',
  subtitle: '쇼츠 위에 짧은 밈 영상을 원하는 시점과 위치에 얹습니다.',
  icon: 'animated_images',
  route: 'meme-overlay'
}
~~~

- [ ] **Step 2: PluginFeatureName/order/metadata, guarded route, provider, PipelineFeature 등록을 구현한다.**
- [ ] **Step 3: navigation/route/registry spec를 통과시킨다.**

이 단계는 Plan 1의 기존 virtual workflow 설치 상태를 읽을 뿐 별도 설치 UI나 저장소를 만들지 않는다.

## Task 7: bootstrap·intake·카탈로그 화면

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/pages/meme-overlay-setup/meme-overlay-setup.component.{ts,html,scss,spec.ts}
- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-library/meme-library.component.{ts,html,scss,spec.ts}

- [ ] **Step 1: page/component 실패 spec를 작성한다.**

Assertions:

- 첫 진입은 전체 bootstrap spinner와 재시도
- catalog 준비 뒤 기존 SourceInputComponent가 표시됨
- 파일 pick/drop과 YouTube 로그인 재시도는 기존 서비스 사용
- 카드 video는 muted, loop, playsinline
- visible card만 src 연결; page 이탈 시 src 제거
- main playing=true이면 모든 card pause
- +와 doubleclick은 동일 add action
- 개별 prepare 실패는 해당 카드 retry, 전체 catalog 유지
- `cardStatus=failed`는 video src를 만들지 않고 해당 카드 retry 상태를 표시하며 전체 catalog를 유지
- page/search controls가 store 호출

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: page와 library를 구현한다.**

`cardStatus=ready`인 카드 video URL만 `cardStreamPath`에 local base URL을 붙여 사용한다. failed 항목에는 `cardStreamPath`가 없다. card file bytes/File 객체를 Angular state에 저장하지 않는다.

- [ ] **Step 4: 대상 spec를 통과시킨다.**

## Task 8: 동적 1~2레인 timeline

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-overlay-timeline/meme-overlay-timeline.component.{ts,html,scss,spec.ts}

- [ ] **Step 1: 실패 spec를 작성한다.**

Assertions:

- background 고정 row는 항상 1개
- overlap 없으면 overlay row 1개, overlap 있을 때만 2개
- instance가 없어도 add 안내용 overlay row 1개
- block x/width는 전체 background duration 비율
- body drag, left/right handle이 순수 timing 함수 호출
- invalid third overlap은 red ghost, pointerup rollback
- block click selection+playhead 이동
- 모든 row를 관통하는 shared playhead
- pointer listener cleanup
- keyboard delete와 접근성 label

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: component를 구현한다.**
- [ ] **Step 4: 대상 spec를 통과시킨다.**

## Task 9: 9:16 스테이지와 2-slot 동기 재생

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-overlay-preview/meme-overlay-preview.component.{ts,html,scss,spec.ts}
- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-overlay-preview/meme-preview-coordinator.ts
- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-overlay-preview/meme-preview-coordinator.spec.ts

**Coordinator contract**

~~~ts
interface MemeVideoSlot {
  element: HTMLVideoElement;
  instanceId: string | null;
}

class MemePreviewCoordinator {
  syncPaused(timeMs: number, instances: MemeOverlayInstance[]): void;
  start(instances: MemeOverlayInstance[]): void;
  tick(backgroundTimeMs: number, instances: MemeOverlayInstance[]): void;
  pause(): void;
  destroy(): void;
}
~~~

Coordinator/preview는 canonical instance와 별도로 store의 `assetId@version → overlayStreamUrl` runtime map을 받는다. slot의 `src`는 이 map에서만 정하고, URL을 instance에 복사하지 않는다.

- [ ] **Step 1: fake video를 사용한 coordinator 실패 spec를 쓴다.**

Assertions:

- 활성 instance가 0/1/2일 때 slot mapping
- 세 번째 slot은 절대 생성/요청하지 않음
- sourceTime = sourceStart + current - timelineStart
- 새 instance mount 때 seek 후 play
- drift가 100ms 이하이면 currentTime을 덮어쓰지 않음
- 100ms 초과일 때만 correction
- pause/scrub은 background와 slots pause+seek
- ended boundary에서 slot 해제
- next instance metadata preload는 비어 있는 slot에서만
- slot source는 runtime map의 정확한 assetId@version URL을 사용하고 instance/manifest에는 URL을 쓰지 않음
- RAF cancel/destroy cleanup

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: coordinator를 구현한다.**
- [ ] **Step 4: preview component 실패 spec를 쓴다.**

Assertions:

- DOM에 background video 1 + overlay video 2만 존재
- background object-fit contain, stage background black
- active instance transform/zIndex 반영
- selected layer move와 aspect-preserving resize가 공용 geometry 호출
- layer click selects
- common MediaTransportComponent events control background/coordinator
- slot metadata 대기만 작은 layer spinner 표시

- [ ] **Step 5: preview component를 구현한다.**
- [ ] **Step 6: coordinator/component spec를 통과시킨다.**

## Task 10A: 정본 편집 명령과 store 연결

Task 8 timeline과 Task 9 preview는 의도적으로 presentational output만 내보낸다. 페이지에서 정본 배열을 직접 고치거나 검증 공식을 복제하지 않도록, 기존 timing domain에 transform/audio edit를 추가하고 store가 timing/transform/audio/front/delete/cancel 명령을 한 경로로 적용한다.

**Files**

- Modify: desktop/clipper_angular/src/features/meme-overlay/models/meme-overlay-timing.{ts,spec.ts}
- Modify: desktop/clipper_angular/src/features/meme-overlay/flow/meme-overlay.store.{ts,spec.ts}

- [ ] **Step 1: transform/audio domain edit와 store command 실패 spec를 쓴다.**
- [ ] **Step 2: domain spec의 행동 실패를 확인한다.**
- [ ] **Step 3: 기존 validateCollection/result 경로를 통해 최소 구현한다.**
- [ ] **Step 4: store spec의 행동 실패를 확인하고 같은 result application 경로로 연결한다.**
- [ ] **Step 5: focused spec와 production build를 통과시킨다.**

상세 계약은 실행 workspace의 `task-10a-brief.md`를 따른다.

## Task 10B: 선택 인스턴스 설정과 화면 조립

**Files**

- Create: desktop/clipper_angular/src/features/meme-overlay/components/meme-overlay-settings/meme-overlay-settings.component.{ts,html,scss,spec.ts}
- Modify: desktop/clipper_angular/src/features/meme-overlay/pages/meme-overlay-setup/meme-overlay-setup.component.{ts,html,scss,spec.ts}

- [ ] **Step 1: settings 실패 spec를 쓴다.**

Controls:

- timeline start/end 표시·입력
- x/y/w/h percent와 1080x1920 px 표시
- effect audio mute/volume 0..1
- 맨 앞으로
- 삭제

Assertions: inactive selection도 setting 가능, invalid 숫자는 canonical state를 손상하지 않음, delete 후 다음 selection 규칙.

- [ ] **Step 2: settings를 구현한다.**
- [ ] **Step 3: page를 preview/library/settings/timeline 레이아웃으로 조립한다.**
- [ ] **Step 4: 좁은 창에서 세로 스택과 각 pane scroll owner를 확인한다.**
- [ ] **Step 5: Angular 전체 회귀를 실행한다.**

Run:

~~~sh
./node_modules/.bin/ng test --watch=false
npm run test:styles
npm run build
~~~

Expected: all PASS, production build exit 0.

## Task 11: 수동 프리뷰 검증

- [ ] 제공 Angry cat overlay.webm을 local catalog fixture로 연결한다.
- [ ] 30초 세로/가로 배경 각각에서 contain+black letterbox가 맞는지 확인한다.
- [ ] 같은 밈을 세 번 서로 안 겹치게 배치하면 timeline이 background+overlay 2줄인지 확인한다.
- [ ] 두 밈을 겹치면 세 번째 줄이 아니라 overlay 두 번째 lane만 생기는지 확인한다.
- [ ] 세 번째 동시 overlap을 drag하면 invalid ghost 후 rollback하는지 확인한다.
- [ ] 재생·pause·scrub·경계 통과에서 audio/영상 slot이 맞는지 확인한다.
- [ ] main 재생 중 카드가 멈추는지 확인한다.
- [ ] Chromium task manager에서 메인 video decoder 수가 최대 3인지 확인한다.
- [ ] 4GB 저사양 장비에서 체감 테스트를 하되 자동 성능 감지 코드는 추가하지 않는다. 실제 문제가 재현되면 별도 측정 이슈로 기록한다.

## Plan 2 완료 기준

- 기존 댓글/랭킹과 밈이 같은 source facade, geometry, transport를 직접 사용한다.
- 겹침 없는 여러 밈은 한 overlay lane, 겹칠 때만 두 lane으로 보인다.
- 어느 시점에도 세 번째 밈을 만들거나 preview하지 못한다.
- 프리뷰는 배경 1+밈 2 video만 유지하고 FFmpeg 없이 즉시 편집 결과를 보여준다.
- card는 page variant만, 선택한 밈은 overlay variant만 내려받는다.
- Plan 3은 store의 source+instances를 그대로 render request와 manifest editState로 저장하면 된다.
