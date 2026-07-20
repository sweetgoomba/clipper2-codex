# AI 숏폼 디렉터 — native VideoPlan planner 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_GROUNDED_CONTENT_STRATEGY_DESIGN_2026-07-16.md`

## 이번 수직 기능의 결과

`shortform_director`의 `ContentStrategy.contentMatrix`에서 사용자가 한 항목을 고르면, 이를 provider-neutral한 native `VideoPlan` 초안으로 바꾼다.

```text
ContentStrategy
  └─ 사용자가 고른 matrix entry
       └─ 연결된 grounded hypothesis
            ↓ shortform_director.video_plan
         VideoPlan (creative planning IR)
           ├─ Scene
           │   └─ Beat + grounding
           │       └─ Shot
           │           └─ Layer + abstract asset strategy
           └─ AudioTimeline.narrationCues

여기까지 생성
────────────────────────────────────────
아직 생성하지 않음
AssetRef / RenderRecipe / renderer job / 최종 영상
```

기존 `shortform_prompt`, clips, `/llm/script`, RenderRecipe와 Python renderer는 변경하지 않는다. 이번 단계에서는 image/video provider와 renderer도 선정하지 않는다.

## 선택 입력

desktop Nest가 project의 저장된 전략에서 다음을 서버 측으로 선택한다.

- `contentStrategyId`
- 사용자가 고른 `matrixEntryId`
- matrix entry가 가리키는 hypothesis
- 해당 hypothesis가 실제로 참조한 candidate evidence와 SourcePack claim
- admission을 통과한 context-only evidence
- BrandProfile과 CampaignBrief

클라이언트는 hypothesis나 evidence 본문을 다시 보내지 않는다. project에 저장된 정본을 사용해 변조와 stale 조합을 막는다.

excluded evidence는 web API 요청에 포함하지 않는다. candidate evidence도 선택 hypothesis가 참조한 것만 보낸다.

## 저장되는 VideoPlan

빈 foundation plan과 생성된 plan을 같은 `video-plan.v1` 안에서 상태로 구분한다.

```ts
type VideoPlan = EmptyVideoPlan | DraftVideoPlan;

interface DraftVideoPlan {
  schemaVersion: 'video-plan.v1';
  id: string; // desktop Nest 부여
  status: 'draft';
  timingBasis: 'estimated';
  derivation: {
    kind: 'native';
    planningContextId: string;
    contentStrategyId: string;
    matrixEntryId: string;
    hypothesisId: string;
  };
  durationMs: number;
  scenes: Scene[];
  audioTimeline: { narrationCues: NarrationCue[] };
}
```

LLM은 `video-plan-draft.v1`만 반환한다. project id, plan id, derivation은 신뢰하지 않고 desktop Nest가 저장된 project에서 조립한다. narration cue도 Beat의 narration과 timing에서 결정적으로 만든다.

## 시간 계약

모든 시간은 프로젝트 시작 기준 millisecond 절대값이다.

1. plan 길이는 CampaignBrief의 `targetDurationSec * 1000`과 정확히 같아야 한다.
2. scene은 0부터 시작하고 순서대로 붙어 plan 전체를 덮는다.
3. 각 scene의 beat도 scene 전체를 순서대로 덮는다.
4. 각 beat의 shot도 beat 전체를 순서대로 덮는다.
5. layer는 자신이 속한 shot 안에 있어야 한다.
6. 각 shot에는 shot 전체를 덮는 layer가 최소 하나 있어야 한다.
7. `order`는 각 부모 안에서 0부터 끊김 없이 증가한다.

생성 직후 timing은 TTS 실측값이 아니므로 반드시 `estimated`다. 현재 Supertonic은 word/sentence timestamp를 반환하지 않으므로 다음 단계는 cue별 WAV 전체 duration으로 `tts_aligned` 재배치를 수행한다. 더 세밀한 단어 동기화는 provider 계약에 실제 timestamp가 추가된 뒤 확장한다.

## 계층별 의미

### Scene

- `purpose`: `hook | context | value | proof | cta`
- `intent`: 이 구간이 시청자에게 해야 할 일
- 첫 scene은 `hook`, 마지막 scene은 `cta`

### Beat

- 하나의 narration 문장/의미 단위
- 연결된 hypothesis의 `evidenceIds`와 `sourceClaimIds` 중 실제 사용한 값을 grounding으로 기록
- plan 전체 Beat grounding의 합집합은 선택 hypothesis의 모든 참조를 최소 한 번 포함

### Shot

- 한 시각 구도 또는 전환 전까지의 연속 구간
- `intent`는 어떤 시각 의미를 전달해야 하는지 기록

### Layer

레이어는 실제 파일·URL·provider id를 담지 않는다.

```ts
type PlannedAssetStrategy =
  | 'owned'
  | 'source'
  | 'search'
  | 'generated-image'
  | 'generated-video'
  | 'programmatic'
  | 'unresolved';
```

- visual role: `background | b_roll | product | evidence | diagram`
- text role: `caption | kinetic_text | label | cta | disclosure`
- text는 항상 `programmatic`
- 실제 제품·증거를 뜻하는 `product`, `evidence`에는 생성 이미지·영상을 배정하지 않는다.
- `diagram`은 재현 가능한 `programmatic`으로 제한한다.

이는 asset router에 주는 창작 의도일 뿐이다. 실제 artifact, 권리, 비용, provider 선택은 다음 단계에서 해결한다.

## 품질·grounding validator

provider JSON Schema 성공 뒤 web API와 desktop Nest가 각각 다시 검증한다.

- 모든 id의 형식과 동일 범위 내 유일성
- scene/beat/shot/layer 개수 상한과 전체 layer 상한
- 절대 시간, 포함 관계, 연속성, 전체 길이
- matrix entry와 hypothesis 연결 정합성
- Beat grounding이 선택 hypothesis의 참조만 사용하는지
- 선택 hypothesis의 evidence/claim 참조가 plan에서 누락되지 않았는지
- 첫 scene에 선택 hook이 narration 또는 text로 실제 포함되는지
- 마지막 scene의 `cta` text layer에 선택 CTA가 실제 포함되는지
- BrandProfile의 금지 표현이 narration, intent, layer content에 없는지
- provider/model 이름이나 실행용 artifact 참조를 위한 별도 필드가 없는지

금지 표현이 이미 선택 matrix entry에 들어 있으면 operation을 시작하기 전에 400으로 거부해 차감하지 않는다.

## 호출·인증·과금 경계

```text
Angular
  matrix entry 선택
  → shortform_director.video_plan quote/confirm
desktop Nest
  project/strategy/selection preflight
  → operation start
  → POST web API /shortform-director/video-plan
web API
  JWT + running operation + openai scope
  + 정확한 operation key 확인
  → Responses strict JSON Schema, store:false, tools 없음
desktop Nest
  독립 runtime validation
  → server provenance 조립 + 전용 project store 저장
  → succeed
실패
  → 기존 plan 유지 + fail/refund
```

신규 operation 초기 policy는 `shortform_director.video_plan`, 10 credit/회, `charge_then_refund`, `openai` scope로 둔다. 운영 검토 전 임시 기본값이며 migration은 이번 작업에서 실행하지 않는다.

## UI 범위

- 생성된 ContentStrategy의 matrix 항목을 실제 내용과 함께 보여준다.
- 각 항목의 `이 구성으로 VideoPlan 생성` 액션에서 차감을 확인한다.
- 완료 시 길이, scene/beat/shot/layer 개수와 선택한 hook을 요약한다.
- 렌더, 미리보기, 에셋 생성 버튼은 추가하지 않는다.

## 수용 기준

1. 선택되지 않은 matrix entry나 stale client payload로 plan을 만들 수 없다.
2. excluded/context-only evidence를 direct grounding으로 인용할 수 없다.
3. 시간축과 hierarchy가 runtime validator를 통과한 plan만 저장된다.
4. 훅, CTA, grounding coverage, 금지 표현 규칙을 위반한 plan은 저장하지 않는다.
5. 실패 시 기존 empty/previous plan이 유지되고 operation이 fail/refund된다.
6. UI에서 matrix 선택부터 plan 요약까지 확인할 수 있지만 render control은 없다.
7. 기존 shortform 세 코드 경로는 `origin/dev` 대비 diff 0이다.
8. 관련 테스트와 세 저장소 build가 통과한다.

## 비범위

- Vira exporter/API와 자동 동기화
- ContentStrategy/VideoPlan 편집 및 version history
- AssetPack/AssetRef 해소와 실제 검색·생성
- renderer/image/video provider 선정
- `VideoPlan → RenderRecipe` compiler
- TTS 실행과 실측 timestamp 정렬
- preview/render/queue/deploy
- migration 실행, commit, push

## 구현 상태 — 2026-07-16

네 번째 vertical slice로 위 흐름을 Angular, desktop Nest, web API에 구현했다.

```text
ContentStrategy matrix entry 클릭
  → shortform_director.video_plan 10 credit quote/confirm
  → desktop에서 저장된 matrix↔hypothesis 선택 검증
  → 선택 hypothesis의 candidate evidence/claim만 요청에 포함
  → web API strict video-plan-draft.v1 생성
  → web API timeline/grounding/route/copy 검증
  → desktop Nest 동일 계약 독립 재검증
  → server-owned derivation + narration cue 조립
  → 전용 director project의 videoPlan 교체
```

추가로 ContentStrategy 단계에서 정규화했을 때 같은 hook과 금지 표현을 거부한다. 전략을 다시 생성하면 이전 strategy에서 파생된 VideoPlan은 새 empty plan으로 교체해 stale derivation을 남기지 않는다.

실제 provider 호출은 수행하지 않았다. renderer, image/video provider, AssetRef와 RenderRecipe compiler는 계속 미정·비범위다.

## 실사용 provider draft canonicalization — 2026-07-20

macOS arm64 packaged app에서 LANEIGE 예시로 VideoPlan 생성을 세 번 실행한 결과, provider는 strict JSON Schema 모양은 지켰지만 Schema로 표현할 수 없는 교차 필드 조건을 매번 다르게 위반했다.

1. 첫 scene에 선택 hook 전체가 없음
2. 마지막 scene에 선택 CTA 전체가 없음
3. 두 번째 scene의 Beat 합계가 scene 전체 시간을 덮지 않음

이 조건을 같은 provider 재호출의 우연에 맡기지 않는다. web API는 provider JSON을 strict parser에 넣기 전에 다음 결정적 값만 canonicalize한다.

- root duration을 CampaignBrief 목표 길이로 고정
- Scene/Beat/Shot의 최소 길이를 지키면서 provider duration 비율을 사용해 부모 전체 시간을 정확히 분배
- 각 계층의 `order`와 absolute `startMs`를 0-based contiguous 값으로 재계산
- Layer를 재배치된 Shot 안으로 옮기고 각 Shot에 full-shot Layer가 하나 이상 있도록 보정
- 선택 hook이 누락된 경우 첫 Beat narration 앞에 정확한 hook을 넣음
- 선택 CTA가 누락된 경우 마지막 Shot의 적절한 text Layer를 CTA로 확정하거나 최대 Layer 수 안에서 CTA Layer를 추가

이미 유효한 draft는 byte-equivalent payload로 유지한다. 다음 항목은 의미를 바꾸거나 가짜 근거를 만들 수 있으므로 보정하지 않고 기존 strict validator가 계속 거부한다.

- unknown/context-only/missing grounding reference
- 금지 표현
- 잘못된 product/evidence 생성형 asset route
- malformed diagram payload와 authored copy
- 잘못된 id, 필수 구조 또는 문자열 계약

desktop Nest는 web API의 `WebApiProviderError`를 raw Error로 다시 던지지 않고 HTTP 502, code `provider_failed`인 `BadGatewayException`으로 변환한다. operation fail/refund와 이전 VideoPlan 보존은 그대로 유지한다.

packaged app의 기본 runtime은 배포된 web API를 호출한다. 따라서 canonicalizer 코드와 새 앱 package가 로컬에 존재하는 것만으로 현재 설치본의 provider 실패가 해결되지는 않는다. web API 배포는 별도 명시 승인 뒤 수행해야 하며, 그 전에는 실제 provider 재시도를 완료 검증으로 기록하지 않는다.
