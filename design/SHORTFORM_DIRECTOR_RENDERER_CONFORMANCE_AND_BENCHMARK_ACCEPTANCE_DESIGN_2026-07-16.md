# AI 숏폼 디렉터 — Renderer conformance와 benchmark acceptance 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_DESIGN_2026-07-16.md`

## 목적

renderer를 선택하기 전에 모든 후보가 같은 입력과 같은 기준으로 비교되도록 acceptance 계약을 고정한다.

```text
representative RenderRecipe
  + immutable stage metadata
  + programmatic motion reference frames
                 ↓
renderer conformance profile
  ├─ recipe/stage/input fingerprint
  ├─ required capability ids
  ├─ output/timeline expectation
  ├─ exact motion state checkpoints
  └─ manual 7-axis rubric
                 ↓
future candidate adapter report
  ├─ observed output probe
  ├─ consumed staged input ids
  ├─ observed timeline counts
  ├─ motion state checksums
  └─ benchmark metadata
                 ↓
automated_failed
manual_review_required
manual_rejected
accepted
```

이번 단계는 renderer process를 실행하거나 후보를 선정하지 않는다.

## Profile identity와 입력 fingerprint

profile은 private execution bundle에서 결정적으로 생성한다.

- `recipeId`, `recipeChecksum`, `stageId`
- stage input의 `sourceId`, `stagedInputId`, kind, media kind/type, size, checksum
- 위 input metadata의 canonical SHA-256 `inputFingerprint`
- recipe checksum과 input fingerprint에 묶인 deterministic profile id

profile과 candidate report에는 path, URL, original ProjectManifest, provider raw payload를 넣지 않는다.

candidate report의 profile id와 input fingerprint가 다르면 같은 benchmark case가 아니므로 자동 실패다.

## Required capabilities

대표 recipe의 실제 구조에서 필요한 capability만 도출한다.

- staged image input
- staged video input
- staged WAV narration input
- timeline/layered composition
- timed subtitle
- programmatic text overlay
- `diagram.sequence-card.v1` motion
- MP4/H.264/AAC output
- progress reporting
- cancellation

특정 renderer 이름, framework, process 방식, provider/model을 capability id에 넣지 않는다.

adapter descriptor는 profile의 모든 required capability를 선언해야 한다. 추가 capability는 허용한다.

## Automated acceptance

자동 gate는 다음만 검사한다.

### 1. Profile identity

- profile id
- input fingerprint
- adapter id
- candidate revision

### 2. Staged input consumption

candidate가 소비했다고 보고한 staged input id가 profile exact set과 같아야 한다.

- missing 불가
- extra 불가
- duplicate 불가
- original source path 사용 여부를 report로 우회할 수 없음

### 3. Output probe

- width, height, aspect ratio, format
- fps
- video/audio codec
- audio stream 존재
- duration drift

duration 허용 오차는 고정된 임의 초 값이 아니라 `1 / fps`, 즉 한 frame이다.

### 4. Timeline projection

- visual timeline item 수
- TTS audio track 수
- subtitle item 수
- overlay 수
- composition layer 수

이는 pixel quality를 판정하지 않고 recipe 일부를 누락한 renderer를 빠르게 차단한다.

### 5. Programmatic motion checkpoints

`diagram.sequence-card.v1`의 start/reveal/hold/exit/end reference frame 각각을 canonical state checksum으로 고정한다.

- overlay id
- primitive/sampler
- reference frame id/progress
- container/connector/step state checksum

candidate renderer 또는 conformance harness가 동일 normalized progress에서 만든 semantic motion state가 일치해야 한다. pixel screenshot 동일성은 이 단계의 자동 gate가 아니다.

### 6. Benchmark metadata validity

- opaque environment id
- candidate revision
- elapsed milliseconds
- output bytes
- optional peak RSS bytes

elapsed/output size/peak RSS는 양수인지와 metadata 완전성만 확인한다. 아직 다음을 하지 않는다.

- latency 합격선
- memory 합격선
- 비용 환산
- 서로 다른 environment 간 순위
- 특정 renderer 우대 가중치

성능 비교는 같은 environment id 안에서만 의미가 있다.

## Manual 7-axis review

기존 `VideoPlanQualityEvaluator`의 축을 그대로 사용한다.

1. `source_faithfulness`
2. `hook_strength`
3. `script_coherence`
4. `narration_visual_fit`
5. `visual_brand_consistency`
6. `motion_continuity`
7. `mobile_readability`

각 축은 `pass | fail`이며 notes는 선택이다.

- 평균이나 100점 환산을 만들지 않는다.
- 모든 축이 정확히 한 번 제출되고 모두 pass여야 한다.
- 누락/중복/unknown 축은 review 미완료다.
- 한 축이라도 fail이면 `manual_rejected`다.

source artifact 오류, 깨진 글자/로고/얼굴 같은 세부 관찰은 해당 축 notes에 남기고 향후 별도 taxonomy가 필요할 때 확장한다.

## Evaluation status

```text
automated check fail
  → automated_failed

automated pass + manual missing/incomplete
  → manual_review_required

automated pass + complete manual with any fail
  → manual_rejected

automated pass + exact 7 axes all pass
  → accepted
```

자동 gate와 수동 review를 섞어 단일 숫자 점수를 만들지 않는다.

## 대표 acceptance case

현재 synthetic 대표 case:

- aligned duration: 41.2초
- canvas: 1080×1920, 30fps, 9:16
- output: MP4/H.264/AAC
- staged input: unique visual 6 + narration 7 = 13
- visual timeline item: 9
- TTS audio track: 7
- subtitle item: 7
- overlay: 11
- composition layer: 20
- sequence-card overlay: 1
- sequence-card reference frame: 5

fixture는 비밀, 실제 브랜드/사용자 데이터, path/URL을 포함하지 않는다.

## API와 runtime

이번 foundation에는 다음을 추가하지 않는다.

- render start/list/retry/cancel API
- Angular benchmark UI
- production adapter
- renderer process/harness
- ffprobe/영상 decode
- screenshot/pixel diff
- output artifact materialization
- operation charge

profile builder와 evaluator는 pure domain code와 test fixture로만 둔다.

## Acceptance

- 같은 execution bundle은 같은 profile id/input fingerprint/checkpoint를 만든다.
- representative profile이 expected counts/capabilities/manual axes와 일치한다.
- profile/report JSON에 path/URL/provider/model/credential이 없다.
- missing capability/input, wrong output, duration drift 초과, timeline 누락, motion mismatch가 자동 실패한다.
- benchmark metric 값은 기록되지만 성능 합격/순위에 쓰이지 않는다.
- 자동 pass만으로 accepted가 되지 않고 manual 7축이 필요하다.
- manual exact 7축 all-pass만 accepted다.
- production adapter는 계속 0개다.
- 기존 `shortform_prompt`와 generic renderer는 변경하지 않는다.
- renderer/provider/server/Electron/DB/migration/runner를 실행하지 않는다.

## 비범위

- Remotion/Motion Canvas/Manim/FFmpeg 조합 선정
- 실제 후보 benchmark 실행
- hardware normalization
- pixel/perceptual diff threshold
- audio waveform/sentence sync 자동 측정
- performance/cost threshold와 가중 점수
- public benchmark API/UI
- JobsService executor
- output artifact와 retention/GC
- commit/push/deploy
