# AI 숏폼 디렉터 — 대표 AssetPack acceptance와 production readiness 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`

## 목적

현재 `AssetPack.status`는 모든 visual requirement가 해결됐는지만 `ready|incomplete`로 알려준다. 그러나 incomplete 상태 안에는 서로 다른 다음 단계가 섞여 있다.

- 이미 로컬 project artifact로 해결된 layer
- provider 요청이 아직 필요한 layer
- provider가 처리 중이거나 재시도 가능한 layer
- strategy, 권리, binding 또는 non-retryable 실패 때문에 사람이 먼저 고쳐야 하는 layer

대표 45초 기준편에 실제 계약 모양의 project-scoped AssetRef와 binding을 채우고, 이 차이를 결정적으로 판정하는 `asset-production-readiness.v1` report를 추가한다.

```text
대표 45초 VideoPlan
  + synthetic project-artifact AssetRefs
  + planned-origin bindings
  + manual-replacement binding
  + provider-neutral acquisitions
                    ↓
              AssetPack resolver
                    ↓
       asset-production-readiness.v1
        ├─ ready
        ├─ waiting
        └─ blocked
```

fixture는 실제 파일 경로나 URL을 저장하지 않는다. production 계약과 같은 `(projectId, artifactId)` locator, provenance, rights, availability만 사용한다.

## 대표 acceptance 상태

visual requirement 10개를 다음처럼 구성한다.

- programmatic: 1개
- planned local source/owned binding: 7개
- generated-image를 owned image로 manual replacement: 1개
- search provider가 아직 필요한 layer: 1개

따라서 첫 acceptance snapshot은 다음 상태다.

```text
전체 10
  ├─ 해결 9
  │   ├─ programmatic 1
  │   └─ local project artifact 8
  └─ provider 필요 1

production readiness = waiting
renderable = false
```

search layer까지 로컬 영상으로 manual replacement한 변형은 10/10 `ready`가 된다. 같은 search acquisition을 non-retryable failure로 바꾼 변형은 `blocked`가 된다.

## report 계약

```ts
interface AssetProductionReadinessV1 {
  schemaVersion: 'asset-production-readiness.v1';
  status: 'empty' | 'ready' | 'waiting' | 'blocked';
  renderable: boolean;
  items: Array<{
    layerId: string;
    state:
      | 'resolved'
      | 'provider_required'
      | 'provider_pending'
      | 'retryable_failure'
      | 'blocking_failure';
    reason:
      | 'programmatic_ready'
      | 'planned_local_asset_ready'
      | 'manual_replacement_ready'
      | 'provider_asset_ready'
      | 'provider_not_requested'
      | 'provider_cancelled'
      | 'provider_in_progress'
      | 'provider_retryable_failure'
      | 'provider_non_retryable_failure'
      | 'provider_result_unmaterialized'
      | 'local_asset_required'
      | 'invalid_asset_binding'
      | 'strategy_required'
      | 'acquisition_state_missing';
    acquisitionStatus?: AssetAcquisitionV1['status'];
  }>;
  summary: {
    total: number;
    resolved: number;
    localResolved: number;
    providerResolved: number;
    providerRequired: number;
    providerPending: number;
    retryableFailures: number;
    blockingFailures: number;
  };
}
```

`renderable`은 모든 visual requirement가 해소된 `ready`에서만 true다. 이는 renderer가 구현됐다는 뜻이 아니라, 향후 compiler/renderer에 넘길 에셋 gate를 통과했다는 뜻이다.

## 판정 규칙

### resolved

- `programmatic_ready`: programmatic resolution
- `asset_ref_ready` + AssetRef origin `owned|source`: planned local resolution
- `manual_replacement_ready`: local manual replacement
- `asset_ref_ready` + AssetRef origin `search|generated-*`: provider materialized resolution

`localResolved`는 planned local과 manual replacement만 센다. programmatic은 전체 `resolved`에는 포함하지만 localResolved에는 포함하지 않는다.

### waiting

search/generated requirement가 아직 unresolved일 때 acquisition 상태에 따라 분류한다.

- `not_requested`: `provider_required`
- `cancelled`: `provider_required`
- `queued|running`: `provider_pending`
- retryable `failed`: `retryable_failure`

이 항목만 존재하면 report status는 `waiting`이다.

### blocked

다음은 자동 진행으로 해결할 수 없다고 본다.

- route 자체가 `unresolved`
- owned/source 실제 AssetRef가 없음
- binding ref가 missing/unavailable/incompatible/rights unknown
- search/generated acquisition이 없음
- non-retryable acquisition failure
- acquisition은 `succeeded`인데 requirement가 여전히 missing

하나라도 있으면 report status는 `blocked`다.

## AssetPack lifecycle

`AssetPackV1`에 `productionReadiness`를 추가하고 `buildAssetPack()`이 requirement와 acquisition 계산 직후 항상 다시 만든다.

- empty plan: `status: empty`, `renderable: false`
- binding/acquisition 변경: report 재계산
- 구형 저장 JSON: read 시 메모리에서 report 보강, read만으로 rewrite하지 않음
- report를 클라이언트가 보내거나 수정하지 않음

## Angular UX

기존 에셋 준비 카드에 다음 요약만 추가한다.

```text
제작 준비 대기
해결 9 · 로컬 해결 8 · Provider 필요 1 · 차단 0
```

상태 문구:

- `empty`: 계획 필요
- `ready`: 제작 준비 완료
- `waiting`: 제작 준비 대기
- `blocked`: 제작 차단

상세 원인은 기존 requirement, acquisition 상태, binding 카드에서 계속 확인한다. render 버튼은 추가하지 않는다.

## 수용 기준

1. 대표 45초 fixture가 실제 계약 모양의 AssetRef와 binding으로 9/10 해결된다.
2. generated-image manual replacement가 local resolution으로 집계된다.
3. 남은 search acquisition이 `provider_required`로 분류되어 report가 waiting이다.
4. search를 manual replacement하면 10/10 ready와 renderable true가 된다.
5. running은 provider pending, retryable failure는 waiting, non-retryable failure는 blocked다.
6. succeeded지만 materialized binding이 없으면 blocked다.
7. owned/source ref 누락과 unresolved strategy는 blocked다.
8. Angular가 readiness summary를 표시하되 render/provider control을 추가하지 않는다.
9. 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- 실제 provider queue/start/retry endpoint
- remote asset download와 project artifact materialization
- compiler, renderer, preview, render 실행
- operation charge/refund
- 실제 파일 생성·복사·검증
- Supertonic timing
- Vira exporter/API
- migration, server/Electron, commit/push/deploy

## 구현 결과

2026-07-16에 대표 fixture와 production readiness gate를 새 `shortform_director` 전용 코드에 구현했다.

- `representative-45s-asset-acceptance.json`에 project-scoped synthetic AssetRef 6개와 binding 8개를 추가했다.
- planned source/owned binding 7개와 generated-image manual replacement 1개로 visual 10개 중 9개를 해결했다.
- 남은 search layer는 `provider_not_requested`로 분류되어 report가 waiting이다.
- search layer까지 owned video로 수동 대체하면 ready와 `renderable: true`가 된다.
- running, retryable failure, non-retryable failure, succeeded-without-binding 변형을 회귀로 고정했다.
- `buildAssetPack()`은 empty/build/hydration/binding 변경마다 report를 다시 계산한다.
- Angular는 제작 준비 완료·대기·차단과 해결/로컬/Provider/차단 집계를 표시한다.
- `renderable`은 향후 compiler 입력 gate일 뿐 render 버튼이나 renderer 구현을 의미하지 않는다.

검증:

- desktop Nest build 및 director 테스트 43/43
- Angular production build 및 director 테스트 19/19
- 기존 `shortform_prompt` Angular/Nest/web 경로 `origin/dev` 대비 diff 0
- raw color, trailing whitespace, 고신뢰 secret-like pattern 검사 통과
