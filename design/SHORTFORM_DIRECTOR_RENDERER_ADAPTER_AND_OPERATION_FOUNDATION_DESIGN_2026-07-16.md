# AI 숏폼 디렉터 — Renderer adapter와 operation foundation 설계

작성일: 2026-07-16 KST

> 2026-07-20 후속: 이 문서의 “실제 renderer/API/UI는 아직 연결하지 않는다”는 원래 foundation 범위는 이력으로 보존한다. 사용자가 수동 품질 검토보다 실제 영상 생성 구현을 먼저 완료하라고 순서를 명시적으로 바꿨고, 아래 `2026-07-20 실행 확장`이 application 경계의 정본이다. 무료 상용 renderer 선택은 `SHORTFORM_DIRECTOR_FREE_COMMERCIAL_RENDERER_AND_OS_DECISION_2026-07-20.md`가 supersede한다.

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`

## 목적

renderer/provider를 고르기 전에 실행 경계를 고정한다.

```text
immutable render-input stage
  ├─ private exact RenderRecipe
  ├─ public-safe stage metadata
  └─ staged files
          ↓
private execution bundle
  ├─ recipe
  ├─ sourceId → staged input metadata
  └─ resolveInput(sourceId) → private staged path
          ↓
Director renderer adapter registry
          ↓
future JobsService workflow executor
          ↓
future output materialization
```

이번 단계는 실제 renderer를 등록하거나 실행하지 않는다.

## 감사 결과와 재사용 결정

현재 공용 `VideoRenderProviderRegistry`는 `RenderRecipe + ProjectArtifact[]`를 provider에 전달한다. 기존 local FFmpeg/Python provider는 ProjectArtifact path를 직접 해석한다.

Director는 다음 이유로 이 인터페이스를 그대로 사용하지 않는다.

- 원본 ProjectManifest artifact가 아니라 immutable staged bytes만 소비해야 한다.
- public stage contract에는 path가 없고 private resolver만 path를 해소해야 한다.
- 기존 renderer가 `shortform.director.hybrid.v1` recipe를 자동 claim하면 안 된다.
- Director adapter의 input provenance는 stage checksum으로 닫혀 있어야 한다.

queue/persistence/retry/cancel은 새로 만들지 않는다. 기존 `JobsService`가 이미 다음을 소유한다.

- persisted job snapshot
- owner scope
- in-memory scheduling과 global concurrency
- cancellation/AbortSignal
- failed/cancelled retry 시 새 job id와 `retryOf`
- restart 시 active job failure 처리

따라서 future Director render executor만 JobsService에 연결한다.

## Stage가 exact recipe를 비공개로 보관해야 하는 이유

현재 stage는 recipe id/checksum만 보관한다. project가 수정된 뒤 retry하면 current project 재컴파일은 원래 실행 snapshot을 재현하지 못한다.

stage private manifest에 exact `render-recipe.v1`을 함께 저장한다.

- public stage 응답은 바뀌지 않는다.
- private manifest의 recipe canonical checksum은 public `recipeChecksum`과 일치해야 한다.
- 같은 stage를 retry해도 project current state와 무관하게 exact recipe를 다시 사용한다.
- recipe나 staged file이 변조되면 bundle hydration이 실패한다.

## Private execution bundle

```ts
interface ShortformDirectorRenderExecutionBundle {
  schemaVersion: 'shortform-director-render-execution-bundle.v1';
  stage: ShortformDirectorRenderInputStageV1;
  recipe: RenderRecipe;
  inputs: Array<{
    sourceId: string;
    stagedInputId: string;
    kind: 'visual' | 'narration';
    mediaKind: 'image' | 'video' | 'audio';
    mediaType: string;
    sizeBytes: number;
    checksum: string;
  }>;
  resolveInput(sourceId: string): Promise<{
    stagedInputId: string;
    absolutePath: string;
    mediaType: string;
    sizeBytes: number;
    checksum: string;
  }>;
}
```

bundle 자체는 application 내부 객체이며 API JSON으로 반환하지 않는다. `absolutePath`는 `resolveInput` 호출 결과에만 존재한다.

exact mapping:

- recipe `sourceAssetIds`의 모든 visual source id가 stage visual input에 정확히 한 번 존재
- recipe TTS audio track artifact id가 stage narration input에 정확히 한 번 존재
- extra/missing/duplicate input은 bundle 생성 실패
- stage project/recipe id/checksum과 private recipe가 일치해야 함

## Renderer adapter 계약

```ts
interface ShortformDirectorRendererAdapterDescriptor {
  adapterId: string;
  label: string;
  executionMode: 'local' | 'worker' | 'remote';
  status: 'available' | 'unavailable';
  capabilityIds: string[];
  notes?: string[];
}

interface ShortformDirectorRendererAdapter {
  adapterId: string;
  describe(): Descriptor | Promise<Descriptor>;
  canRender(bundle: ShortformDirectorRenderExecutionBundle): boolean;
  render(
    bundle: ShortformDirectorRenderExecutionBundle,
    context: {
      operationId: string;
      ownerSubjectId: string;
      signal: AbortSignal;
      onProgress(progress: number, message: string): void | Promise<void>;
    },
  ): Promise<{
    status: 'succeeded' | 'failed' | 'cancelled';
    outputArtifactIds?: string[];
    failure?: {
      code: string;
      retryable: boolean;
      message?: string;
    };
  }>;
}
```

adapter는 Director project repository, original ProjectManifest, original source path를 받지 않는다. 필요한 input만 `bundle.resolveInput(sourceId)`로 해소한다.

registry 규칙:

- explicit adapter id가 있으면 존재, claim, availability를 모두 검증한다.
- id가 없으면 등록 순서 중 claim 가능하고 available인 첫 adapter를 고른다.
- production adapter는 이번 단계에 0개 등록한다.
- 기존 generic VideoRenderProvider는 자동 포함하지 않는다.

## Durable job reference

future JobsService params에는 recipe 전체나 path를 넣지 않고 다음 opaque reference만 저장한다.

```ts
interface ShortformDirectorRenderJobReferenceV1 {
  schemaVersion: 'shortform-director-render-job-reference.v1';
  projectId: string;
  stageId: string;
  recipeId: string;
  recipeChecksum: string;
  adapterId: string;
}
```

executor는 job 시작 시 reference로 private bundle을 hydrate하고 adapter를 다시 resolve한다. retry는 JobsService가 새 job을 만들되 같은 exact reference를 복사한다.

## Queue, retry, cancel

future mapping:

| Director 의미 | 기존 JobsService |
|---|---|
| queued | `waiting` |
| adapter 준비 | `starting` |
| render | `running` |
| succeeded | `completed` |
| failed | `failed` |
| cancelled | `cancelled` |
| retry | failed/cancelled snapshot params로 새 job, `retryOf` 보존 |

cancel은 queue 제거 또는 running AbortSignal과 adapter cancellation으로 전달한다. adapter는 terminal result만 반환하고 job 상태 persistence를 직접 수정하지 않는다.

## Stage retention

stage 삭제 worker는 아직 만들지 않는다. 대신 cleanup 판단에 필요한 retention class를 고정한다.

```text
waiting | starting | running → active-job
failed | cancelled           → retry-source
completed                    → completed-source
```

- `active-job`: 절대 삭제 금지
- `retry-source`: retry window가 끝나기 전 삭제 금지
- `completed-source`: output artifact materialization과 보존 정책 확인 전 삭제 금지

현재 Jobs repository에는 GC/retention query와 policy duration이 없다. 임의의 기간을 하드코딩하거나 stage를 삭제하지 않는다. future cleanup은 persisted job reference를 조회해 zero-reference와 policy expiry를 모두 만족할 때만 수행한다.

## API와 Angular

이번 foundation에는 render start/list/retry/cancel API를 추가하지 않는다.

- production adapter가 0개이므로 실행 가능한 render action을 노출하지 않는다.
- Angular의 기존 `렌더 입력 고정`까지만 유지한다.
- provider selector, render button, queue UI를 추가하지 않는다.
- public stage response에 recipe/path를 추가하지 않는다.

## Acceptance

- stage private manifest가 exact recipe를 보관하고 checksum mismatch를 거부한다.
- source file 변경 뒤에도 bundle은 staged copy만 resolve한다.
- source id로만 input을 해소하며 unknown source id를 거부한다.
- bundle은 recipe visual/TTS exact set과 stage input set을 검증한다.
- registry는 claim/availability/explicit id를 검증하고 generic provider를 자동 등록하지 않는다.
- durable job reference는 opaque id/checksum만 포함한다.
- retry는 같은 reference를 재사용할 수 있다.
- retention class가 JobsService status에 결정적으로 매핑된다.
- public API response, project JSON, Jobs store에는 path/URL/provider raw payload가 추가되지 않는다.
- renderer/provider/queue worker/server/Electron을 실제 실행하지 않는다.
- 기존 `shortform_prompt`는 변경하지 않는다.

## 비범위

- production renderer adapter
- FFmpeg/Remotion/Motion Canvas/Manim 선택
- renderer process 실행
- render start/list/retry/cancel endpoint
- operation credit policy
- output MP4/thumbnail artifact materialization
- stage GC worker와 retention 기간
- acquisition provider
- DB/migration/server/Electron/commit/push/deploy

## 2026-07-20 실행 확장

### 순서 변경

기존 문서는 manual 7축, packaging, license gate를 통과한 뒤 executor/API/UI를 구현하는 순서를 제안했다. 사용자는 “실제 영상을 먼저 만들어야 품질을 검토할 수 있다”고 명시했다. 따라서 구현 gate와 release gate를 분리했다.

- 구현 gate: ready project가 immutable stage에서 실제 MP4까지 도달해야 한다.
- release gate: 실제 에셋 manual 7축, Electron packaging/offline, 지원 OS, Remotion license/cost는 계속 남는다.
- 이 순서 변경은 기존 `shortform_prompt`, provider/acquisition, 배포 범위를 넓히지 않는다.

### 최종 실행 흐름

```text
ready Director project
  → exact immutable render-input stage
  → shortform-director-render-job-reference.v1
  → existing JobsService waiting/starting/running
  → job-only ShortformDirector workflow executor
  → exact execution bundle hydration
  → director.adapter.remotion-local.v1
  → isolated Node worker over private stdin
  → loopback staged asset server
  → source-revision composition bundle cache
  → Remotion H.264/AAC render
  → ffprobe + conditional FFmpeg duration finalization
  → owner/project-scoped atomic output materialization
  → path-free operation/result API
  → Angular progress/cancel/retry/MP4 저장
```

### JobsService 재사용과 public plugin 경계

새 queue를 만들지 않았다. `WorkflowExecutorRegistry`에 job-only executor map을 추가했다.

- public `list()`와 `get('shortform_director')`는 기존 install-gated virtual workflow를 그대로 반환한다.
- JobsService의 실행/cancel 해석만 `getJobExecutor()`를 사용한다.
- Director executor는 module lifecycle에서 job-only로 register/unregister한다.
- retry는 기존 JobsService가 같은 opaque reference를 복사해 새 job id와 `retryOf`를 만든다.
- local render는 provider/LLM operation이 아니므로 새 credit charge를 추가하지 않았다.

generic ProjectsService에는 schema로 제한된 두 예외만 뒀다.

- Director render reference에는 generic `project_id`, `title`, absolute `output_root`를 주입하지 않는다.
- Director render 완료 job은 기존 generic project history로 다시 materialize하지 않는다.

### Local Remotion worker

application adapter는 isolated PoC package의 pinned Remotion runtime을 child worker로 실행한다.

- worker request의 recipe/staged absolute path/output path/cache path는 pipe로만 전달하고 Jobs/API/project JSON에 저장하지 않는다.
- runtime은 기존 설치된 Chrome, FFmpeg, FFprobe와 nested Remotion package가 모두 있을 때만 `available`이다.
- browser/native binary 자동 다운로드는 없다.
- composition metadata는 input projection의 width/height/fps/duration으로 동적으로 계산한다.
- progress는 JobsService의 0..1 snapshot으로 전달한다.
- AbortSignal은 worker SIGTERM과 Remotion cancel signal로 연결하며, 종료 지연 시 제한된 SIGKILL fallback을 사용한다.
- worker 오류 원문과 private path는 public operation result에 넣지 않는다.

### Output materialization

`shortform-director-render-output.v1`은 다음 public metadata만 가진다.

- opaque output id
- project/stage/recipe/adapter identity
- safe MP4 filename과 `video/mp4`
- bytes/SHA-256/duration/dimensions/fps/H.264/AAC
- createdAt

실제 파일은 `CLIPPER_DATA_DIR` 아래 Director 전용 owner/project hash namespace의 temporary workspace에 생성한다. ffprobe 계약과 filesystem size를 통과한 뒤 SHA-256을 계산하고 metadata와 MP4 directory를 원자적으로 rename한다. 다운로드 시 owner/project/operation output reference를 다시 확인하며 absolute path를 응답 JSON에 노출하지 않는다.

### Render operation API와 Angular

Director 전용 endpoint만 추가했다.

- `POST .../:projectId/render-jobs`
- `GET .../:projectId/render-jobs`
- `GET .../:projectId/render-jobs/:operationId`
- `DELETE .../:projectId/render-jobs/:operationId`
- `POST .../:projectId/render-jobs/:operationId/retry`
- `GET .../:projectId/render-outputs/:outputId/file`

operation DTO는 job params/history/auth/path를 반환하지 않는다. Angular는 immutable stage가 준비된 뒤에만 MP4 생성 버튼을 보이고 waiting/starting/running progress, cancel, failed/cancelled retry, completed MP4 저장을 제공한다. React/Remotion Player나 기존 shortform UI는 추가·변경하지 않았다.

### 구현 acceptance와 실제 결과

- application adapter/output/executor/operation 계약 테스트 5개와 Jobs/registry 경계 테스트가 통과했다.
- 로컬 실제 통합 테스트에서 유효한 staged PNG 1개와 WAV 1개로 1초, 30fps, 540×960 MP4를 생성했다.
- 최종 파일은 MP4 `ftyp`, H.264 video, AAC audio, width/height, size와 progress `→ 1`을 재검증했다.
- 실제 local render final rerun은 약 5.0초였다.
- Nest Director + Jobs/registry 회귀는 101 pass, opt-in actual render 1 pass였다.
- Angular Director는 33/33, web API Director는 18/18 pass했다.
- Nest/Angular/web API build가 모두 통과했다.

### 남은 release gate

- actual representative asset/audio manual 7축
- Electron extraResources와 packaged/offline runtime
- Windows x64와 지원 macOS 범위
- Remotion Company License/Automator 비용
- composition/output/stage retention과 GC 기간
- thumbnail/inline preview가 제품에 필요한지 결정
- provider acquisition과 complex diagram materialization

현재 source checkout에서는 실제 영상 생성까지 동작하지만 packaged release 준비 완료를 뜻하지 않는다.

## 2026-07-20 Motion Canvas 기본 adapter 정정

application executor/API/output/Angular 경계는 바꾸지 않고 adapter registry만 다음 순서로 확장했다.

```text
ShortformDirectorRendererAdapterRegistry
  ├─ director.adapter.motion-canvas-local.v1  # default
  └─ director.adapter.remotion-local.v1       # preserved explicit fallback
```

Motion Canvas worker는 execution bundle 외 project/source state를 읽지 않는다. exact staged bytes를 다시 검사한 뒤 source fingerprint static bundle, strict loopback resolver, Puppeteer frame bridge와 external FFmpeg/FFprobe를 사용한다. official Motion Canvas FFmpeg exporter와 Remotion package를 import하지 않는다.

adapter의 required capability는 staged image/video/WAV, layered composition, timed subtitle, text role, sequence-card, MP4/H.264/AAC와 progress다. AbortSignal이 발생하거나 worker가 cancellation을 보고하면 temporary output workspace를 폐기하고 `{status: 'cancelled'}`를 반환한다.

검증:

- Motion Canvas adapter success/cancel/registry/isolation 4/4
- 최소 actual render 1/1
- Shortform Director 전체 103개에서 fail 0
- 기존 Remotion tests pass, 관련 코드 삭제 없음

release gate는 Remotion 비용 판정이 아니라 Motion Canvas packaged browser/encoder ownership으로 바뀐다. 현재 GPL/libx264 FFmpeg binary를 그대로 묶지 말고 GPL 준수 배포 또는 LGPL/platform encoder를 선택해야 한다. macOS arm64 source checkout만 실제 확인됐고 macOS x64/Windows x64 packaged smoke는 남아 있다.
