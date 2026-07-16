# AI 숏폼 디렉터 — grounded ContentStrategy 수직 기능 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_DESIGN_2026-07-16.md`

## 이번 수직 기능의 결과

새 `shortform_director` 안에서 사용자가 입력한 브랜드·캠페인·승인 claim과 Vira evidence를 한 번의 구조화된 `ContentStrategy`로 바꾼다.

```text
BrandProfile ───────┐
CampaignBrief ──────┼─→ PlanningContext
SourcePack.claims ──┤      │
Vira evidence ──────┘      ├─ candidate: 직접 인용 가능
                            ├─ context_only: 배경 참고만 가능
                            └─ excluded: LLM에 전달하지 않음
                                   ↓
                         ContentStrategy structured output
                           ├─ seriesConcept
                           ├─ audiencePromise
                           ├─ grounded hypotheses
                           └─ content matrix
```

기존 `shortform_prompt`, `/llm/script`, clips/render store는 변경하지 않는다. 이 단계는 `VideoPlan` scene이나 asset을 만들지 않고 renderer/image/video provider도 선택하지 않는다.

## PlanningContext 입력 계약

### BrandProfileV1

```ts
interface BrandProfileV1 {
  schemaVersion: 'brand-profile.v1';
  brandName: string;
  productName: string;
  toneKeywords: string[];
  requiredFacts: string[];
  prohibitedExpressions: string[];
}
```

모든 항목은 사용자가 제공한 제작 제약이다. 빈 값은 허용하지만 LLM이 비어 있는 브랜드 사실을 추측해서 채우지는 않는다.

### CampaignBriefV1

```ts
interface CampaignBriefV1 {
  schemaVersion: 'campaign-brief.v1';
  prompt: string;
  objective: 'awareness' | 'engagement' | 'conversion';
  funnelStage: 'awareness' | 'consideration' | 'conversion' | 'retention';
  targetAudience: string;
  keyMessage: string;
  cta: string;
  platform: 'youtube_shorts';
  targetDurationSec: number; // 15..60
  disclosureRequirements: string[];
}
```

기존 prompt는 원문 그대로 보존한다. 구조 필드는 prompt를 덮어쓰는 자동 추론 결과가 아니라 사용자가 명시한 제약이며, 생략 시 보수적인 기본값을 저장한다.

### SourcePackV1

```ts
interface SourcePackV1 {
  schemaVersion: 'source-pack.v1';
  claims: Array<{
    id: string;
    statement: string;
    provenance: {
      kind: 'user_provided' | 'source_reference';
      label: string;
      sourceRef?: string;
    };
  }>;
}
```

- `claim`은 브랜드·제품 사실의 유일한 명시적 인용 경계다.
- Vira의 조회·성장·댓글 감성은 제품 효능이나 브랜드 사실의 provenance로 사용하지 않는다.
- `sourceRef`는 사용자가 준 문서명·URL·내부 참조 문자열일 수 있지만 실제 cookie, auth header, secret을 받거나 기록하지 않는다.
- 같은 SourcePack 안의 claim id는 유일해야 한다.

## ContentStrategyV1 출력 계약

```ts
interface ContentStrategyV1 {
  schemaVersion: 'content-strategy.v1';
  id: string; // desktop Nest가 부여
  status: 'draft';
  seriesConcept: string;
  audiencePromise: string;
  hypotheses: Array<{
    id: string;
    statement: string;
    rationale: string;
    basis: 'brief' | 'market_evidence' | 'source_claim' | 'mixed';
    evidenceIds: string[];
    sourceClaimIds: string[];
    intendedVariationAxis: string;
  }>;
  contentMatrix: Array<{
    id: string;
    hypothesisId: string;
    format: string;
    hook: string;
    targetAudience: string;
    appeal: string;
    cta: string;
  }>;
}
```

runtime 규칙:

1. hypothesis와 matrix id는 각각 유일해야 한다.
2. matrix의 `hypothesisId`는 같은 응답 안의 hypothesis를 가리켜야 한다.
3. `evidenceIds`는 admission의 `candidateEvidenceIds`만 가리킬 수 있다.
4. `context_only`는 prompt의 배경 문맥으로 전달할 수 있지만 직접 근거 id로 인용할 수 없다.
5. `sourceClaimIds`는 SourcePack에 실제로 존재하는 claim만 가리킬 수 있다.
6. `brief` basis는 두 참조 배열이 모두 비어 있어야 한다.
7. `market_evidence`, `source_claim`, `mixed` basis는 이름에 맞는 참조를 최소 하나 가져야 한다.
8. excluded evidence는 LLM 입력 자체에서 제거한다.

## 호출·인증·과금 경계

```text
Angular
  quote + 사용자 차감 확인
    operationKey = shortform_director.strategy
          ↓
desktop Nest
  POST /projects/shortform-director/projects/:id/content-strategy
  operation start
          ↓ bearer token + operationRunId
web API
  JWT 확인
  operation이 running + openai scope인지 확인
  operationKey가 정확히 shortform_director.strategy인지 확인
  OpenAI Responses structured output 호출
          ↓
desktop Nest
  grounding 재검증 → project에 저장 → operation succeed
  실패 시 operation fail/refund
```

신규 operation의 seed 기본값은 1회 10 credit, `charge_then_refund`, provider scope `openai`다. 이는 현재 수직 기능을 실행 가능하게 하는 초기 운영값이며 관리자 policy로 조정할 수 있다. 이번 작업에서는 migration을 실행하지 않는다.

local/trusted-header처럼 user JWT가 없는 실행 모드에서는 외부 전략 생성을 가장하지 않고 명시적으로 거부한다. draft 생성과 조회는 계속 가능하다.

## web API structured output

- 새 endpoint: `POST /shortform-director/content-strategy`
- 기존 `/llm/script`와 module/service/prompt를 공유하지 않는다.
- Responses API의 `text.format.type = json_schema`, `strict = true`를 사용한다.
- API key는 기존 DB credential resolver에서만 읽고 request/log/project에 넣지 않는다.
- `store: false`를 명시한다.
- request 원문과 evidence payload를 log에 남기지 않는다.
- JSON Schema 성공 뒤에도 서버 runtime validator와 reference validator를 통과해야 한다.
- web search는 사용하지 않는다. 이번 전략은 제공된 SourcePack/Vira snapshot에만 grounded된다.

## UI 범위

- 기존 한 줄 prompt를 유지하면서 목적, 퍼널, 타깃, 핵심 메시지, CTA, 목표 길이를 입력할 수 있게 한다.
- 브랜드명, 제품명, 톤, 필수 사실, 금지 표현을 입력할 수 있게 한다.
- SourcePack claims는 줄 단위 claim 입력과 provenance label 입력으로 작은 범위에서 제공한다.
- 저장된 draft 카드에서 `전략 생성`을 명시적으로 실행한다.
- 생성 중·실패·완료 상태를 정확히 표시하고 완료 시 series concept과 hypothesis/matrix 개수를 보여준다.
- VideoPlan/렌더/에셋 생성 버튼은 추가하지 않는다.

## 비침범 경계

- Angular `src/features/shortform/**` 변경 금지
- desktop Nest `src/modules/shortform/**`, `src/modules/shortform-core/**` 변경 금지
- web API `src/modules/shortform-script/**` 변경 금지
- Vira 저장소 read-only
- 기존 project/store migration 금지
- renderer/compiler/image/video provider 작업 금지

## 수용 기준

1. expanded PlanningContext가 validation 후 전용 director store에 저장된다.
2. SourcePack duplicate/unknown claim reference와 Vira non-candidate reference가 거부된다.
3. 새 web API endpoint는 JWT와 정확한 operation key를 요구한다.
4. OpenAI request가 strict JSON Schema와 `store: false`를 사용한다.
5. 성공한 전략만 project에 저장되고 실패한 provider/contract 검증은 operation fail로 환불된다.
6. Angular에서 입력·차감 확인·전략 생성·결과 요약 흐름이 동작한다.
7. 기존 shortform 세 경로는 `origin/dev` 대비 diff 0이다.
8. 관련 테스트와 세 저장소 build가 통과한다.

## 비범위

- Vira exporter/API/auth 자동 연결
- URL/document 실제 수집·snapshotting
- ContentStrategy 편집/version history
- ContentStrategy → native VideoPlan 생성
- asset router/provider, renderer/compiler, preview/render
- 실제 migration 실행, commit, push, deploy

## 구현 상태 — 2026-07-16

세 번째 vertical slice로 위 계약과 흐름을 Angular, desktop Nest, web API에 구현했다.

```text
사용자 입력 + manual Vira evidence
  → planning-context.v2 저장
  → 10 credit quote/confirm
  → shortform_director.strategy operation start
  → candidate/context-only만 별도 배열로 web API 전달
  → OpenAI Responses strict JSON Schema
  → web API reference validation
  → desktop Nest reference 재검증
  → contentStrategy 저장 + operation succeed
  ↘ 어느 단계든 실패: strategy 미저장 + operation fail/refund
```

OpenAI 공식 Structured Outputs 문서 기준으로 Responses API의 `text.format`에 `json_schema`, `name`, `schema`, `strict`를 두는 현재 문법을 확인했다. 모든 object에 `additionalProperties: false`를 적용했고, 문자열 길이처럼 provider schema 지원 변화에 민감한 제한은 runtime validator가 최종 강제한다.

provider request에는 `store: false`를 명시하고 web search/tool을 붙이지 않았다. request 원문, evidence payload, provider/contract diagnostic은 controller log에 복제하지 않는다.

기본 LLM model은 현재 web API가 이미 사용하는 OpenAI credential 경계 안의 `gpt-4.1`이며 `SHORTFORM_DIRECTOR_OPENAI_MODEL`로 교체 가능하다. 이는 ContentStrategy planner의 초기 실행 경계일 뿐 renderer와 image/video provider 선정이 아니다.

후속 native VideoPlan 작업에서 두 deterministic 품질 규칙을 보강했다.

- NFKC/소문자/공백 정규화 결과가 같은 matrix hook은 중복으로 거부한다.
- prohibited expression이 strategy copy에 포함되면 web API와 desktop Nest 모두 거부한다.

또한 전략 재생성 성공 시 이전 ContentStrategy에서 파생된 VideoPlan은 empty native plan으로 초기화한다. 후속 정본은 다음 문서다.

- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_IMPLEMENTATION_PLAN_2026-07-16.md`
