# AI 숏폼 디렉터 — Renderer adapter와 operation foundation 설계

작성일: 2026-07-16 KST

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
