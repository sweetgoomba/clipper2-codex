# AI 숏폼 디렉터 — Render input 재검증과 immutable staging 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`

## 목적

준비 완료로 보이는 AssetPack과 narration metadata만 믿고 renderer에 넘기지 않는다. 실제 렌더 직전에 현재 파일을 다시 열어 identity, media kind, size와 checksum을 확인하고, exact RenderRecipe가 소비할 입력을 immutable local stage로 고정한다.

```text
Director project snapshot
  ├─ tts_aligned VideoPlan
  ├─ ready/renderable AssetPack
  └─ ready narrationAudio
                 ↓
existing RenderRecipe compiler strict gate
                 ↓
render input revalidation
  ├─ source ProjectManifest ownership + artifact identity
  ├─ local access kind + readable file
  ├─ image/video kind compatibility
  ├─ bound snapshot / manifest metadata checksum
  └─ narration pack size + checksum
                 ↓
atomic immutable local stage
  ├─ unique visual files
  ├─ narration WAV files
  ├─ recipe checksum binding
  └─ opaque staged input ids
                 ↓
future renderer adapter
```

이번 단계는 renderer를 선택하거나 실행하지 않는다.

## 왜 compile과 staging을 분리하는가

RenderRecipe compile은 순수하고 read-only다. 파일을 읽거나 복사하지 않아 같은 project snapshot에서 결정적 결과를 만든다.

staging은 로컬 파일 시스템의 현재 상태를 검사하고 파일을 복사하는 side effect다. 두 경계를 분리하면 다음이 명확해진다.

- creative/execution IR 오류: compile 실패
- 파일이 삭제·교체·손상됨: staging 실패
- renderer 실행·encode 실패: 향후 render operation 실패

compile endpoint는 그대로 유지하고 별도 명시적 POST action으로 staging한다.

## API

```text
POST /v1/projects/shortform-director/projects/:projectId/render-input-stage
```

- owner-scoped
- body 없음
- operation charge 없음
- project JSON을 변경하지 않음
- renderer/queue/provider를 호출하지 않음
- 경로, URL, provider payload를 응답하지 않음

## AssetRef bind snapshot

새로 연결하는 로컬 project artifact에는 binding 시점의 content snapshot을 함께 저장한다.

```ts
interface ProjectArtifactSnapshotV1 {
  schemaVersion: 'project-artifact-snapshot.v1';
  artifactKind: 'source.image' | 'source.video' | 'media.image' | 'media.video';
  mediaType: string;
  sizeBytes: number;
  checksum: `sha256:${string}`;
}

interface AssetRefV1 {
  // existing fields
  sourceSnapshot?: ProjectArtifactSnapshotV1;
}
```

staging 시 locator가 가리키는 현재 파일과 snapshot을 비교한다. 같은 artifact id 아래 파일 내용이 바뀌면 실패한다.

기존 저장 AssetRef에는 snapshot이 없다. 이를 일괄 rewrite하지 않는다.

- snapshot 있음: exact bound snapshot 검증
- snapshot 없음 + manifest size/checksum 있음: manifest metadata 검증
- 둘 다 없음: 현재 파일을 읽어 checksum을 만들고 stage에 고정

legacy 입력도 stage 이후에는 immutable하지만, bind 시점 이후 변경 여부까지 증명하지는 못한다. stage item의 verification mode로 이 차이를 보존한다.

## 지원 로컬 입력

visual:

- `access.kind: project-file`
- `access.kind: source-file`이면서 absolute local file
- image kind: `source.image | media.image`
- video kind: `source.video | media.video`

지원하지 않음:

- `remote-url`
- directory
- image/video kind가 AssetRef mediaKind와 다른 artifact
- owner가 다른 project
- 읽을 수 없거나 0 byte인 파일

narration:

- 현재 Director project의 ready narration pack에 속한 artifact
- storage 실파일 size/checksum이 pack과 timing measurement에 모두 일치

## stage 계약

```ts
interface ShortformDirectorRenderInputStageV1 {
  schemaVersion: 'shortform-director-render-input-stage.v1';
  id: string;
  projectId: string;
  projectUpdatedAt: string;
  recipeId: string;
  recipeChecksum: string;
  status: 'ready';
  createdAt: string;
  inputs: Array<{
    id: string;
    kind: 'visual' | 'narration';
    sourceId: string;
    mediaKind: 'image' | 'video' | 'audio';
    mediaType: string;
    sizeBytes: number;
    checksum: string;
    verification:
      | 'bound-snapshot'
      | 'manifest-metadata'
      | 'current-content'
      | 'narration-pack';
  }>;
  summary: {
    total: number;
    visual: number;
    narration: number;
    totalBytes: number;
  };
}
```

`sourceId`는 visual의 경우 RenderRecipe `sourceAssetIds`에 있는 AssetRef id, narration은 audio track artifact id다. future renderer는 recipe source id를 staged input id로 결정적으로 매핑할 수 있다.

## identity와 원자성

stage id는 다음 exact snapshot에서 계산한다.

- project id와 `updatedAt`
- recipe id와 canonical JSON checksum
- 정렬된 input source id, kind, size, checksum

같은 project/file snapshot을 다시 staging하면 같은 id의 기존 stage를 재사용한다.

새 stage는 임시 directory에 모든 파일을 복사하고, 복사된 파일의 size/checksum을 다시 확인한 뒤 manifest와 함께 final directory로 rename한다. 하나라도 실패하면 임시 directory를 제거하고 ready stage를 남기지 않는다.

stage root:

```text
CLIPPER_DATA_DIR/shortform-director/render-input-stages/
  <owner hash>/<project hash>/<stage id>/
```

public contract에는 filesystem path나 내부 filename을 넣지 않는다.

현재 renderer가 없으므로 old stage cleanup policy는 이번 범위에 넣지 않는다. 향후 render operation이 stage reference lifecycle과 retention을 소유한다.

## Angular

RenderRecipe를 먼저 확인한 project에만 `렌더 입력 고정` action을 보여준다.

- POST staging 호출
- visual/narration/total byte summary 표시
- path/URL/raw manifest 표시 없음
- operation charge confirmation 없음
- render button, provider selector, queue 상태 없음
- project mutation 뒤 recipe와 stage preview를 함께 무효화

## acceptance

- 대표 ready project의 unique visual 6개와 narration 7개, 총 13개가 stage된다.
- 같은 snapshot을 두 번 stage하면 같은 stage id와 contract를 반환한다.
- staged file은 source와 checksum이 같고 source 변경 뒤에도 immutable하다.
- deleted/inaccessible/remote/wrong-kind visual은 staging을 막는다.
- bound snapshot과 다른 content는 staging을 막는다.
- narration size/checksum mismatch는 staging을 막는다.
- partial copy 실패는 ready stage를 남기지 않는다.
- response에는 path/URL/provider/model/credential이 없다.
- project repository upsert, operation charge, renderer/provider 호출이 없다.
- 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- renderer adapter와 registry claim
- render operation/queue/retry/cancel
- encode/mux/output artifact
- stage retention/garbage collection
- remote download
- image/video provider 실행
- project JSON에 stage 저장
- DB/migration/server/Electron 실행
- commit/push/deploy
