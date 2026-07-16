# AI 숏폼 디렉터 — AssetPack/AssetRef resolution foundation 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`

## 목적

native VideoPlan의 `assetStrategy`는 어떤 방식으로 장면을 준비할지 말할 뿐 실제로 사용할 에셋이 준비됐다는 뜻이 아니다. 이번 단계는 visual layer의 요구사항과 실제 참조를 분리하고, 렌더 전 준비 상태를 거짓 없이 보여주는 `AssetPack` foundation을 추가한다.

```text
VideoPlan visual layers
  ├─ programmatic
  ├─ owned / source / search
  ├─ generated-image / generated-video
  └─ unresolved
             ↓
      AssetPackResolver
        ├─ resolved
        ├─ missing
        └─ unresolved
             ↓
  Angular 에셋 준비 현황
```

기존 `shortform_prompt`, renderer, RenderRecipe, 실제 파일 저장소와 provider 호출은 변경하지 않는다.

## 용어 경계

- `assetStrategy`: VideoPlan이 원하는 조달 방식이다. 실제 에셋이나 provider 선택 결과가 아니다.
- `AssetRequirement`: visual layer 한 개가 렌더 전에 충족해야 할 요구사항이다.
- `AssetRef`: 실제 artifact를 가리킬 수 있는 provider-neutral 메타데이터다. URL이나 로컬 경로를 직접 저장하지 않는다.
- `AssetBinding`: VideoPlan layer와 AssetRef의 명시적 연결이다.
- `AssetPack`: 한 VideoPlan에 대한 requirement, ref, binding과 준비도 snapshot이다.

text layer는 compiler가 직접 만드는 계획 요소이므로 AssetRequirement를 만들지 않는다. visual `programmatic` layer는 외부 파일 없이 계획만으로 다음 compiler 단계에 넘길 수 있어 이번 해소 수준에서는 resolved로 본다.

## 상태 의미

세 상태를 섞지 않는다.

| 상태 | 의미 |
|---|---|
| `resolved` | programmatic visual이거나, 호환되고 available이며 권리 확인된 AssetRef가 연결됨 |
| `missing` | owned/source/search/generated처럼 조달 방식은 정해졌지만 사용할 AssetRef가 없음 또는 사용할 수 없음 |
| `unresolved` | VideoPlan의 조달 방식 자체가 `unresolved`라서 먼저 routing 결정이 필요함 |

`missing`과 `unresolved`가 하나라도 있으면 AssetPack은 `incomplete`다. 모든 visual requirement가 resolved일 때만 `ready`다. 이는 영상 품질 점수가 아니라 렌더 입력 준비도다.

## 계약

```ts
interface AssetPackV1 {
  schemaVersion: 'asset-pack.v1';
  videoPlanId: string | null;
  status: 'empty' | 'incomplete' | 'ready';
  assetRefs: AssetRefV1[];
  bindings: AssetBindingV1[];
  requirements: AssetRequirementV1[];
  summary: {
    total: number;
    resolved: number;
    missing: number;
    unresolved: number;
  };
}

interface AssetRefV1 {
  schemaVersion: 'asset-ref.v1';
  id: string;
  mediaKind: 'image' | 'video';
  origin: 'owned' | 'source' | 'search' | 'generated-image' | 'generated-video';
  locator: {
    kind: 'project-artifact';
    projectId: string;
    artifactId: string;
  };
  label: string;
  sourceProjectTitle?: string;
  provenance: {
    kind: 'user_provided' | 'source_evidence' | 'search_result' | 'generated';
    sourceRef?: string;
  };
  rights: { status: 'cleared' | 'unknown' };
  availability: 'available' | 'missing';
}

interface AssetBindingV1 {
  layerId: string;
  assetRefId: string;
}
```

기존 `ProjectManifest` 감사 결과 artifact id는 project 범위이므로 이후 연결 slice에서 `(projectId, artifactId)` locator로 구체화했다. `sourceRef`는 선택적 provenance 식별자다. foundation 단계에는 이를 생성하거나 받는 HTTP endpoint를 추가하지 않았으며 실제 URL, 파일 경로, provider key, prompt 원문, 비용은 프로젝트에 넣지 않는다.

## 호환 규칙

- `owned|source|search` layer는 같은 origin의 image 또는 video ref를 받을 수 있다.
- `generated-image`는 image + generated-image ref만 받을 수 있다.
- `generated-video`는 video + generated-video ref만 받을 수 있다.
- `availability: available`이고 `rights.status: cleared`여야 resolved다.
- 정상 ref는 `asset_ref_ready`, 없는 ref, unavailable ref, origin/media 불일치, 권리 미확인은 missing 상태와 구체적인 reason으로 남긴다.
- `product|evidence` 생성 금지는 기존 VideoPlan validator가 계속 정본으로 강제한다.

이번 slice의 production project에는 외부 AssetRef 입력 경로가 없으므로 실제 visual은 programmatic만 자동 resolved되고 나머지는 missing/unresolved로 정직하게 표시된다. 순수 resolver는 합성 ref/binding을 받아 호환성 규칙을 검증할 수 있게 만들어 다음 ingestion 단계의 계약을 선행 고정한다.

## project lifecycle

```text
새 planning draft
  → empty VideoPlan + empty AssetPack

ContentStrategy 생성/재생성
  → stale VideoPlan 제거 + empty AssetPack

VideoPlan 생성/재생성
  → 새 plan id 기준으로 AssetPack 재계산
  → 이전 layer binding은 자동 승계하지 않음

구형 저장 JSON에 assetPack 없음
  → read 시 메모리에서 plan 기준 보강
  → read만으로 디스크 rewrite하지 않음
```

새 plan의 layer id와 의미가 달라질 수 있으므로 이전 binding을 자동으로 재사용하지 않는다. 향후 재사용 UX는 AssetRef inventory와 새 layer에 대한 사용자 확인을 분리해서 설계한다.

## UX

VideoPlan 요약 아래에 다음을 표시한다.

- `준비 n / 전체 n`
- `실제 에셋 필요 n`
- `조달 방식 미정 n`
- pending visual layer별 scene/shot 위치, role, strategy, content 설명
- missing은 `에셋 참조 필요`, unresolved는 `조달 방식 결정 필요`로 서로 다르게 안내

실제 asset picker, upload, search, generation, render 버튼은 추가하지 않는다. 버튼 없이도 무엇이 부족한지 이해하고 다음 연결 단계의 입력 계약을 검증하는 것이 이번 UX의 목표다.

## 수용 기준

1. 대표 45초 plan의 visual layer가 결정적으로 requirement로 변환된다.
2. programmatic visual, 외부 ref 누락, unresolved route를 각각 resolved/missing/unresolved로 구분한다.
3. 합성 AssetRef/Binding의 origin, media, availability, rights 호환성을 순수 resolver가 검사한다.
4. 새 project와 strategy reset에는 empty AssetPack, 새 VideoPlan에는 해당 plan id의 AssetPack이 저장된다.
5. assetPack 없는 구형 director JSON은 읽기만으로 안전하게 보강되며 디스크 migration을 요구하지 않는다.
6. Angular는 준비도와 pending 요구사항을 보여주되 render 또는 provider 제어를 노출하지 않는다.
7. 기존 `shortform_prompt` 세 코드 경로는 `origin/dev` 대비 diff 0이다.

## 2026-07-16 구현 결과

다음 코드 경계에 foundation을 구현했다.

- `desktop/clipper_nestjs/src/modules/shortform-director/domain/asset-pack.ts`
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
- `desktop/clipper_nestjs/test/shortform-director-asset-pack.test.js`
- `desktop/clipper_angular/src/features/shortform-director/**`

대표 45초 기준편의 결과:

- visual requirement 10개
- programmatic diagram 1개 resolved
- owned/source/search/generated route 9개 missing
- route 자체가 unresolved인 항목 0개
- AssetPack 상태 `incomplete`

순수 resolver는 합성 ref와 binding을 입력받아 다음을 확인한다.

- 같은 origin의 owned/source/search image 또는 video
- generated-image는 image, generated-video는 video
- artifact availability
- rights clearance
- binding이 가리키는 ref 존재 여부

project lifecycle도 함께 연결했다.

- 새 project는 empty AssetPack으로 시작
- 전략 재생성은 stale VideoPlan과 AssetPack을 함께 초기화
- 새 VideoPlan 저장은 동일 plan id의 AssetPack을 함께 저장
- assetPack 없는 기존 JSON은 read 시 메모리에서 보강하며 파일을 다시 쓰지 않음

Angular는 VideoPlan 아래에 준비 완료/실제 에셋 필요/조달 방식 미정 개수와 pending layer의 장면·비트·샷, role, route, 설명을 표시한다. 실제 picker/provider/render control은 추가하지 않았다.

검증 결과:

- desktop Nest director: 28/28 통과, build 통과
- Angular director: 12/12 통과, production build 통과
- 기존 Angular/Nest/web API shortform 경로: `origin/dev` 대비 diff 0
- provider, server/Electron, migration, commit/push/deploy 없음

## 2026-07-16 후속 연결 slice

foundation 다음 단계에서 로컬로 검증 가능한 project artifact에 한해 실제 AssetRef 입력 경로를 추가했다.

- stable identity: `(sourceProjectId, artifactId)`
- `source.image|source.video` → `source`
- `media.image|media.video` + local-user provider → `owned`
- 원격 URL, 검색·생성·render 결과는 제외
- 후보 응답과 director JSON에는 path/URL/uri를 넣지 않음
- 권리 확인 후 layer binding을 저장하고 AssetPack을 재계산
- Angular lazy picker와 연결 해제 제공

정본은 `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`다.

## 비범위

- 실제 파일 업로드, URL import, 검색, 이미지·영상 생성
- foundation 자체의 AssetRef 등록·binding endpoint와 picker
- provider/model/version/cost/latency 기록
- license 자동 판별 또는 원격 artifact 존재 확인
- TTS timing, compiler, RenderRecipe, preview/render
- web API, operation billing, migration, server/Electron 실행
- renderer/provider 선정, commit/push/deploy
