# AI 숏폼 디렉터 — RenderRecipe compiler foundation 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NARRATION_AUDIO_MATERIALIZATION_AND_REGENERATION_DESIGN_2026-07-16.md`

## 목적

현재 Director는 창작 정본과 렌더 입력에 필요한 세 계약을 모두 갖고 있다.

```text
VideoPlan
  Scene → Beat → Shot → Layer + tts_aligned timing

AssetPack
  visual requirement → AssetRef/binding + production readiness

narrationAudio
  cue → materialized Supertonic WAV metadata
```

이번 단계는 세 계약을 기존 실행 IR인 `render-recipe.v1`로 결정적으로 컴파일한다.

```text
VideoPlan + AssetPack + narrationAudio
                  ↓ strict compile gate
          existing render-recipe.v1
            ├─ visual timeline
            ├─ TTS audio tracks
            ├─ narration subtitles
            ├─ text/programmatic overlays
            └─ Director composition metadata
```

renderer, image/video provider, preview engine은 선택하지 않는다. 실제 파일 staging, 렌더 job, encode도 실행하지 않는다.

## 기존 RenderRecipe를 재사용하는 이유

현재 `project-manifest/domain/render-recipe.model.ts`는 이미 다음을 표현한다.

- absolute timeline item
- video/audio/subtitle/overlay track
- artifact id
- output size/fps/codec
- provider-neutral `templateParams`

따라서 Director 전용 두 번째 실행 IR을 만들지 않는다. 부족한 Layer hierarchy와 project-scoped locator는 `templateParams.shortformDirectorComposition`에 보존한다.

기존 simplified/legacy renderer가 새 레시피를 자동 선택하지 않도록 다음 identity를 사용한다.

```text
templatePresetId = shortform.director.hybrid.v1
templateParams.shortformDirectorComposition.schemaVersion
  = shortform-director-composition.v1
```

기존 provider가 인식하는 `shortformTemplateModel`은 넣지 않는다.

## compile gate

컴파일은 다음을 모두 만족할 때만 성공한다.

### VideoPlan

- `status: draft`
- `timingBasis: tts_aligned`
- `timingAlignment`과 compact estimated baseline 존재
- plan duration, scene/beat/shot/layer/cue timing이 정수 ms
- 모든 Layer가 소속 Shot 안에 있음

### AssetPack

- `videoPlanId`가 현재 plan id와 일치
- 현재 plan과 refs/bindings/acquisitions로 다시 계산한 pack이 `ready`
- `productionReadiness.renderable: true`
- external visual layer마다 정확히 한 binding과 compatible AssetRef가 있음
- programmatic visual에는 외부 artifact를 가장하지 않음

compile foundation은 snapshot 계약을 검증한다. 실제 source project 파일이 이후 삭제됐는지는 다음 materialization/staging adapter가 render 직전에 다시 검증한다.

### narrationAudio

- `status: ready`
- `videoPlanId`가 현재 plan id와 일치
- cue exact set과 순서가 일치
- cue text fingerprint, duration, artifact checksum/provider/speaker가 alignment measurement와 일치
- cue timing과 audio track timing이 동일

하나라도 맞지 않으면 부분 recipe를 반환하지 않는다.

## 결정적 출력

### identity/output

```text
id               recipe.<director project>.output.shortform-director.main
projectId        Director project id
outputId         output.shortform-director.main
templatePresetId shortform.director.hybrid.v1
canvas           1080 × 1920, 9:16, 30fps
format           mp4 / h264 / aac
```

`provenance.createdAt`은 compile 시각이 아니라 project `updatedAt`을 사용한다. 같은 project snapshot은 같은 recipe JSON을 만든다.

### external visual

외부 에셋이 연결된 visual Layer는 `RenderTimelineItem`이 된다.

- `sourceArtifactId`: recipe-local stable id인 `AssetRef.id`
- 실제 `(projectId, artifactId)` locator는 composition metadata에 둠
- `background|b_roll`: `cover`
- `product|evidence|diagram`: `contain`
- Layer start/duration을 ms에서 sec로 그대로 변환
- 별도 motion effect를 임의로 선택하지 않음

모든 external visual item은 하나의 main video track에 시간 순서로 들어간다. 겹침과 z-order의 정본은 composition metadata다.

### narration

- cue마다 `role: tts` audio track 1개
- narration cue 전체를 subtitle track 1개로 변환
- subtitle item의 `ttsArtifactId`는 같은 cue audio artifact를 가리킴
- BGM/SFX는 이번 compiler에서 생성하지 않음

### text/programmatic Layer

text Layer와 programmatic visual Layer는 `role: template` overlay로 변환한다.

- text: 원문, start/end, role 기반 styleRef
- programmatic diagram: artifact 없이 semantic primitive metadata
- 현재 primitive는 `diagram.sequence-card.v1` 하나만 둠
- animation curve, transition, color, font, layout pixel은 아직 고정하지 않음

### Director composition metadata

`templateParams.shortformDirectorComposition`은 모든 Layer를 원래 hierarchy와 순서대로 보존한다.

```ts
interface ShortformDirectorCompositionV1 {
  schemaVersion: 'shortform-director-composition.v1';
  timingBasis: 'tts_aligned';
  layerOrder: 'ascending-back-to-front';
  canvas: { width: 1080; height: 1920; fps: 30 };
  layers: Array<{
    layerId: string;
    sceneId: string;
    beatId: string;
    shotId: string;
    order: number;
    kind: 'visual' | 'text';
    role: VideoPlanLayerRole;
    startSec: number;
    durationSec: number;
    content: string;
    source:
      | {
          kind: 'project-artifact';
          assetRefId: string;
          projectId: string;
          artifactId: string;
          mediaKind: 'image' | 'video';
        }
      | {
          kind: 'programmatic';
          primitive: 'diagram.sequence-card.v1' | 'text.role.v1';
        };
  }>;
}
```

경로, URL, provider raw payload, credential은 포함하지 않는다.

## API와 Angular

read-only endpoint:

```text
GET /v1/projects/shortform-director/projects/:projectId/render-recipe
```

- owner를 확인한다.
- project snapshot을 컴파일해 raw `RenderRecipe`를 반환한다.
- project나 파일을 수정하지 않는다.
- operation charge가 없다.
- renderer registry나 render service를 호출하지 않는다.

Angular는 production readiness와 narrationAudio가 모두 ready일 때만 `실행 레시피 확인`을 활성화한다.

성공 후 다음 요약만 표시한다.

```text
RenderRecipe 준비
41.2초 · visual 9 · programmatic/text 11 · TTS 7 · caption 7
renderer 미선정 · 렌더는 실행하지 않음
```

full recipe editor, JSON 노출, render 버튼은 추가하지 않는다.

## 대표 45초 acceptance

ready AssetPack 변형과 F2 1.2x narration fixture를 사용한다.

- plan duration: 41.2초
- scene 5 / beat 7 / shot 10 / total Layer 20
- external visual timeline item 9
- programmatic/text overlay 11
- unique visual AssetRef 6
- TTS audio track 7
- subtitle item 7
- programmatic diagram 1
- 모든 artifact source는 opaque id/locator이며 path/URL 없음

같은 입력을 두 번 compile하면 deep equal이어야 한다.

## 실패 acceptance

다음은 compiler error다.

- estimated 또는 empty VideoPlan
- waiting/blocked/stale AssetPack
- current plan id와 다른 pack
- narrationAudio empty/stale
- cue/artifact/checksum/duration mismatch
- alignment measurement와 narration pack 불일치
- visual Layer binding/ref 누락
- Layer가 Shot 밖으로 나감

## 비범위

- recipe project 저장 또는 `render.recipe` artifact materialization
- source project 실제 파일 staging/revalidation
- renderer/provider 선택
- preview canvas
- FFmpeg/Python/Remotion/Motion Canvas 실행
- BGM/SFX/mix
- transition/motion 품질 결정
- render operation charge, queue, retry
- server/Electron 실행, commit/push/deploy
