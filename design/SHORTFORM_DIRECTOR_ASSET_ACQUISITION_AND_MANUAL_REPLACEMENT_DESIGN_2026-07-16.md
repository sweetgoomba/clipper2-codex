# AI 숏폼 디렉터 — search/generated acquisition과 수동 대체 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`

## 목적

현재 `search`, `generated-image`, `generated-video` visual layer는 AssetRef가 없다는 사실만 `missing`으로 보인다. provider를 아직 정하지 않은 상태에서도 다음 두 가지는 먼저 고정할 수 있다.

1. 향후 어떤 provider adapter가 붙어도 공통으로 사용할 요청·진행·성공·실패·취소·재시도 상태
2. provider 결과를 기다리지 않고 사용자가 기존 로컬 프로젝트 에셋으로 대체하는 fallback

```text
VideoPlan search/generated layer
              ↓
     AssetAcquisition request
       not_requested
            ↓ queue
          queued
            ↓ start
          running
       ┌────┼────────┐
    succeeded       failed
                      ↓ retry
                    queued

어느 시점이든 현재 범위에서는
owned/source project artifact를
명시적 manual replacement로 연결 가능
```

이번 slice는 상태 계약과 수동 대체만 구현한다. 실제 검색·이미지 생성·영상 생성, provider/model 선택, 비용 차감, 원격 결과 다운로드와 artifact materialization은 실행하지 않는다.

## 핵심 분리

`AssetAcquisition`과 `AssetBinding`은 같은 것이 아니다.

- `AssetAcquisition`: 원래 계획 route인 search/generated 요청의 실행 상태
- `AssetBinding`: 현재 layer가 실제로 사용할 AssetRef
- `manual-replacement`: 원래 route와 다른 owned/source AssetRef를 사용자가 명시적으로 선택한 binding mode

수동 대체가 연결되어도 원래 acquisition 이력을 삭제하지 않는다. binding에 `mode: manual-replacement`를 기록하고 acquisition에는 현재 대체 AssetRef ID만 파생해 표시한다. 연결을 해제하면 기존 acquisition 상태가 다시 보인다.

## 계약

```ts
type AssetAcquisitionStrategy =
  | 'search'
  | 'generated-image'
  | 'generated-video';

interface AssetAcquisitionV1 {
  schemaVersion: 'asset-acquisition.v1';
  id: string;
  layerId: string;
  strategy: AssetAcquisitionStrategy;
  request: {
    brief: string;
    acceptedMediaKinds: Array<'image' | 'video'>;
  };
  status:
    | 'not_requested'
    | 'queued'
    | 'running'
    | 'succeeded'
    | 'failed'
    | 'cancelled';
  attempt: number;
  updatedAt?: string;
  result?: {
    assetRefId: string;
  };
  failure?: {
    code:
      | 'provider_unavailable'
      | 'timeout'
      | 'rate_limited'
      | 'content_policy'
      | 'no_results'
      | 'invalid_result'
      | 'unknown';
    retryable: boolean;
    message?: string;
  };
  manualReplacementAssetRefId?: string;
}

interface AssetBindingV1 {
  layerId: string;
  assetRefId: string;
  mode: 'planned-origin' | 'manual-replacement';
}
```

`request.brief`는 provider prompt가 아니라 VideoPlan layer의 provider-neutral visual intent다. provider-specific prompt, model, seed, raw request/response, URL, credential과 진단 로그는 이 계약에 넣지 않는다.

## 초기 acquisition 생성

`buildAssetPack()`은 draft VideoPlan의 visual layer 중 다음 route에만 deterministic acquisition을 만든다.

| strategy | accepted media |
|---|---|
| `search` | image, video |
| `generated-image` | image |
| `generated-video` | video |

초기 상태는 `not_requested`, `attempt: 0`이다. ID는 `asset_acquisition_${layerId}`로 결정적이다. plan 재생성 시 새 layer 기준으로 다시 만들고 stale acquisition은 승계하지 않는다.

## 상태 전이

허용 전이:

```text
not_requested ─queue→ queued
queued ─start→ running
queued ─cancel→ cancelled
running ─succeed→ succeeded
running ─fail→ failed
running ─cancel→ cancelled
failed(retryable) ─queue→ queued
cancelled ─queue→ queued
```

- queue할 때 attempt를 1 증가시키고 이전 result/failure를 지운다.
- retryable이 false인 failed request는 queue할 수 없다.
- succeeded request는 자동 재실행하지 않는다.
- 성공 result는 materialized AssetRef ID만 가진다.
- 실패 message는 사용자에게 보여도 되는 정제된 문장만 허용한다. raw provider payload/stack은 프로젝트에 저장하지 않는다.

현재 production endpoint에서는 이 전이를 실행하지 않는다. 순수 domain state machine과 저장 계약을 먼저 고정해 이후 provider adapter가 같은 규칙을 사용하게 한다.

## 수동 대체 규칙

기존 project artifact candidate API를 재사용한다.

- 대체 후보는 기존과 동일하게 로컬 검증된 `owned|source` image/video만 사용한다.
- `search` layer는 image 또는 video로 대체할 수 있다.
- `generated-image` layer는 image만 가능하다.
- `generated-video` layer는 video만 가능하다.
- `owned|source` 원래 route는 기존처럼 같은 origin의 `planned-origin` binding을 사용한다.
- `search|generated-*`에 owned/source를 연결하면 서버가 `manual-replacement` mode를 자동 결정한다.
- 클라이언트가 binding mode나 origin을 지정하지 않는다.
- 권리 확인은 계속 필수다.

resolver 결과:

- 계획 origin과 맞는 ref: `asset_ref_ready`
- 허용된 수동 대체 ref: `manual_replacement_ready`
- media 불일치 또는 허용되지 않은 origin: `asset_ref_incompatible`

## AssetPack lifecycle과 hydration

`AssetPackV1`에 `acquisitions`를 추가한다.

```ts
interface AssetPackV1 {
  // 기존 필드
  acquisitions: AssetAcquisitionV1[];
}
```

- 새 project/empty plan: acquisitions `[]`
- 새 draft VideoPlan: search/generated layer별 `not_requested`
- binding 변경: 기존 acquisition 상태를 보존하고 manual replacement locator만 재계산
- 수동 대체 해제: manual replacement field가 사라지고 기존 request 상태가 다시 노출
- 구형 director JSON에 acquisitions 또는 binding mode가 없음: read 시 메모리에서 보강하되 read만으로 rewrite하지 않음

## UX

search/generated pending requirement에는 provider 실행 버튼 대신 현재 acquisition 상태를 표시한다.

```text
[배경 · 생성 이미지]
추상적인 자외선 신호 배경

Provider 미선정 · 요청 전
[프로젝트 에셋으로 대체]
```

상태 문구:

- `not_requested`: Provider 미선정 · 요청 전
- `queued`: 요청 대기
- `running`: 처리 중
- `succeeded`: 결과 준비
- `failed`: 실패 · 재시도 가능 또는 수동 확인 필요
- `cancelled`: 요청 취소

수동 대체 picker는 기존 owned/source candidate를 사용하고 media compatibility에 따라 필터링한다. 연결된 카드에는 `수동 대체`를 명확히 표시하며 연결 해제를 제공한다.

실제 “검색”, “이미지 생성”, “영상 생성”, “재시도” 버튼은 만들지 않는다. 버튼이 생기면 provider/operation policy가 존재한다고 오해할 수 있기 때문이다.

## 수용 기준

1. search/generated visual layer마다 deterministic acquisition이 생성된다.
2. 허용 상태 전이와 retryable 규칙을 순수 domain 테스트가 고정한다.
3. provider/model/URL/raw payload/secret이 acquisition에 들어가지 않는다.
4. 구형 AssetPack은 acquisition과 binding mode를 read-only hydration한다.
5. search는 image/video, generated-image는 image, generated-video는 video로만 수동 대체된다.
6. 수동 대체 binding은 `manual-replacement`와 `manual_replacement_ready`로 식별된다.
7. 수동 대체 해제 후 원 acquisition 상태가 보존된다.
8. Angular는 acquisition 상태와 수동 대체를 보여주되 provider 실행·재시도 control을 노출하지 않는다.
9. 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- provider/model 선정과 benchmark
- 실제 search/image/video generation endpoint
- operation quote, credit charge/refund
- remote result download/cache/materialization
- provider request/response와 진단 저장
- queue worker, polling, websocket progress
- 새 upload/URL paste
- renderer/compiler/preview
- DB migration, server/Electron 실행, commit/push/deploy

## 구현 결과

2026-07-16에 이 계약을 새 `shortform_director` 전용 코드에 구현했다.

- Nest domain에 deterministic acquisition 생성과 순수 상태 머신을 추가했다.
- AssetPack rebuild가 기존 acquisition 상태를 보존하고 stale layer를 제거한다.
- 구형 저장 JSON은 read 시 acquisitions와 binding mode를 메모리에서 보강하지만 rewrite하지 않는다.
- 기존 project artifact binding API가 planned origin과 manual replacement를 서버에서 구분한다.
- 수동 대체 연결·해제 뒤에도 원 acquisition 실패·진행 상태가 보존된다.
- Angular는 acquisition 상태, media-compatible 대체 picker, `수동 대체` binding 표시를 제공한다.
- provider 시작·재시도·render 버튼과 비용 차감은 추가하지 않았다.

검증:

- desktop Nest build 및 director 테스트 39/39
- Angular production build 및 director 테스트 19/19
- 기존 `shortform_prompt` 관련 Angular/Nest/web 경로 `origin/dev` 대비 diff 0
- raw color, trailing whitespace, 고신뢰 secret-like pattern 검사 통과
