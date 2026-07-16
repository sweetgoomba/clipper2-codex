# AI 숏폼 디렉터 — Diagram step copy 소유권 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`

## 목적

`diagram.sequence-card.v1`의 `context → evidence → action` 단계 문구를 renderer가 임의로 만들지 않고 creative planning IR인 VideoPlan이 명시적으로 소유하게 한다.

```text
web API structured VideoPlan draft
  Layer.content                 = diagram headline
  Layer.programmaticPayload     = exact context/evidence/action copy
                 ↓
desktop VideoPlan contract validation
  primitive/schema/step identity/copy policy 검증
                 ↓
RenderRecipe compiler
  programmaticMotion.content에 그대로 전달
                 ↓
Angular deterministic preview / future renderer adapter
  같은 semantic copy 소비
```

renderer, browser preview, motion sampler는 표현과 시간 변화만 소유한다. 캠페인 의미나 광고 문구를 새로 작성하지 않는다.

## 소유권 결정

VideoPlan Layer가 다음을 소유한다.

- `content`: sequence-card 전체의 headline
- `programmaticPayload.steps[].label`: 화면에 표시할 세 단계의 exact copy

motion contract가 소유하는 것은 다음으로 제한한다.

- step의 고정 identity와 order
- layout
- enter/hold/exit timing
- frame sampling

renderer adapter는 VideoPlan/RenderRecipe에 없는 문구를 생성하거나 보완하지 않는다.

## Layer 계약

```ts
interface DiagramSequenceCardContentV1 {
  schemaVersion: 'diagram-sequence-card-content.v1';
  primitive: 'diagram.sequence-card.v1';
  steps: [
    { id: 'context'; label: string },
    { id: 'evidence'; label: string },
    { id: 'action'; label: string },
  ];
}

interface VideoPlanLayer {
  // existing fields
  content: string;
  programmaticPayload?: DiagramSequenceCardContentV1;
}
```

규칙:

- `role: diagram`은 `assetStrategy: programmatic`과 위 payload가 필수다.
- step은 정확히 3개이며 순서는 `context`, `evidence`, `action`이다.
- label은 공백이 아닌 짧은 문구이며 최대 120자다.
- 세 label은 정규화 뒤 서로 달라야 한다.
- prohibited expression을 포함할 수 없다.
- diagram이 아닌 Layer에는 payload를 둘 수 없다.
- label은 입력 brief, selected strategy, beat grounding, SourcePack claim 범위를 벗어난 새 사실을 만들 수 없다.

`order`는 payload에 중복 저장하지 않는다. 배열 위치와 고정 id가 semantic order를 결정하고, motion compiler가 이를 `0, 1, 2`로 변환한다.

## web API strict response 모양

OpenAI strict structured output에서는 모든 object property가 required여야 하므로 draft 단계의 모든 Layer가 `programmaticPayload` 필드를 반환한다.

```text
diagram Layer      → DiagramSequenceCardContentV1 object
non-diagram Layer  → null
```

web API parser는 이 조건을 fail-closed로 검증한다. desktop validator는 정상화할 때 non-diagram의 `null`을 저장 모델에서 생략하고, diagram object만 보존한다.

## 생성 품질 규칙

세 단계는 generic UI label이 아니라 해당 diagram의 의미를 압축한다.

```text
context  현재 상황·문제·선택 맥락
evidence 확인해야 할 관측 근거·승인 자료·비교 기준
action   시청자가 취할 다음 행동·선택 원칙
```

예:

```text
headline: 사용 환경에 맞는 선택 기준
context:  실내와 야외의 노출 환경 구분
evidence: 승인 자료와 사용 조건 함께 확인
action:   내 사용 환경에 맞춰 제품 선택
```

이는 표현 예시일 뿐 고정 카피가 아니다. 모델은 제공된 사실과 선택된 hypothesis grounding 안에서 매 plan에 맞는 문구를 작성한다.

## 기존 저장 프로젝트 호환

기존 `video-plan.v1` diagram Layer에는 payload가 없다. schemaVersion을 즉시 올리거나 저장 JSON을 일괄 rewrite하지 않는다.

컴파일러 경계에서만 다음 명시적 legacy fallback을 둔다.

```text
payload 있음  → exact authored step copy 사용
payload 없음  → 상황 / 확인 / 행동 legacy fallback
payload malformed → compile error
```

fallback은 과거 저장 데이터 호환용이다. 새 web draft와 desktop draft validation은 payload 없는 diagram을 거부하므로 새 프로젝트가 fallback에 의존하지 않는다.

## RenderRecipe와 preview

`programmaticMotion.content.steps`는 payload label을 순서대로 복사하고 motion `order`만 추가한다.

- headline은 계속 Layer `content`와 일치한다.
- Angular preview는 이미 RenderRecipe motion 값을 소비하므로 별도 카피 생성 로직이 없다.
- future renderer adapter도 동일 motion contract를 소비해야 한다.
- path, URL, provider/model, artifact payload, credential은 추가하지 않는다.

## acceptance

- web strict schema가 모든 Layer에 `programmaticPayload`를 요구한다.
- diagram object와 non-diagram null을 구분한다.
- missing/malformed/wrong-order/duplicate/prohibited diagram step copy를 거부한다.
- desktop validator가 유효 payload를 VideoPlan에 보존한다.
- 대표 45초 fixture가 generic fallback이 아닌 authored copy를 가진다.
- RenderRecipe motion과 Angular preview에 세 authored label이 그대로 나타난다.
- payload 없는 legacy representative clone은 기존 `상황/확인/행동`으로 컴파일된다.
- malformed stored payload는 compile error다.
- 기존 `shortform_prompt`, renderer/provider, operation/queue, server/Electron에는 변화가 없다.

## 비범위

- primitive를 2개 이상으로 확장
- 자유 형식 diagram DSL
- renderer/provider 선택과 실행
- image/video acquisition 실행
- 실제 영상 생성
- 저장 프로젝트 migration/rewrite
- 별도 preview API
- typography/color/style token 계약
- commit/push/deploy/DB/runner/server/Electron 조작
