# AI 숏폼 디렉터 — Vira evidence policy와 strategy input 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`

## 목표

새 `shortform_director` 플러그인 안에서 Vira evidence를 단순 JSON 보관물이 아니라, 다음 planner가 안전하게 소비할 수 있는 strategy input으로 만든다.

```text
versioned Vira evidence JSON
  → envelope + current payload validation
  → lifecycle / observation policy
  → candidate | context_only | excluded
  → PlanningContext.evidenceAdmission
  → 향후 ContentStrategy.hypotheses[]
```

Vira exporter/API와 LLM planner가 아직 없으므로 이번 단계는 수동 JSON handoff와 결정적 admission까지만 구현한다.

## 실제 Vira 코드 기준

감사 정본은 `/Users/jina/project/vira`, `main@2f1d1fd`다.

- active Market: `shorts_videos`, 최신 `shorts_snapshots`, aggregate comment sentiment
- lab growth: 최근 3 snapshot endpoint의 일평균 조회 증가량을 나이 버킷 안에서 백분위화, rising threshold 90
- on-demand analysis: `video_analyses`의 `succeeded|partial` run과 성공한 module 결과
- legacy Market/Viral: 파일은 남아 있으나 관련 Inngest 함수는 등록 해제

fixture는 위 필드 모양을 따르되 실제 DB row, 사용자, URL, 댓글 원문, secret을 복사하지 않는 합성 데이터로 만든다.

## 입력 계약

기존 생성 요청에 다음 선택 입력을 추가한다.

```ts
interface ViraEvidencePolicyV1 {
  allowLab: boolean;     // default false
  allowLegacy: boolean;  // default false
}

interface CreateShortformDirectorProjectInput {
  prompt: string;
  marketEvidence?: ViraEvidenceEnvelope[];
  evidencePolicy?: Partial<ViraEvidencePolicyV1>;
}
```

`on_demand`는 사용자가 evidence를 명시적으로 제공한 행위 자체가 선택이므로 별도 opt-in flag를 두지 않는다. 다만 성공/부분 성공 run과 비어 있지 않은 module 결과만 유효하다.

## current payload validation

envelope 검증 뒤 현재 활성 종류에 최소 payload 검증을 적용한다.

| kind | 최소 검증 |
|---|---|
| `market.video-observation` | keyword, tags, metrics, `snapshot|discovery`, 비음수 지표와 sentiment aggregate |
| `market.peer-growth` | snapshot from/to, `snapshotCount=3`, daily delta, age, age bucket, percentile 0..100, `risingThreshold=90`, boolean flags |
| `analysis.video-8d` | analysisRunId, `succeeded|partial`, 비어 있지 않은 modules object |
| legacy kinds | envelope/lifecycle만 검증하고 payload는 동결하지 않음 |

같은 요청 안의 evidence id는 중복될 수 없다.

## admission policy

정책 우선순위:

1. `insufficient|unavailable`은 lifecycle과 관계없이 `excluded`.
2. `lab`은 `allowLab=true`일 때만 다음 단계로 이동.
3. `legacy_unregistered`는 `allowLegacy=true`일 때만 다음 단계로 이동.
4. `partial` observation은 전략 가설의 직접 근거가 아닌 `context_only`.
5. 나머지 유효 evidence는 `candidate`.

```text
EvidenceAdmission
  policy
    allowLab
    allowLegacy
  decisions[]
    evidenceId
    status: candidate | context_only | excluded
    reason
  candidateEvidenceIds[]
  contextEvidenceIds[]
  excludedEvidenceIds[]
```

admission은 evidence의 성공 보장을 뜻하지 않는다. 향후 LLM strategy가 candidate를 인용할 수 있다는 의미뿐이다.

## ContentStrategy 경계

이번 단계에서는 LLM이나 규칙으로 가설을 만들어내지 않는다. 대신 다음 output 계약을 타입으로 고정하고 project에는 아직 생성되지 않았음을 정확히 저장한다.

```ts
interface ContentStrategyV1 {
  schemaVersion: 'content-strategy.v1';
  id: string;
  status: 'draft';
  hypotheses: Array<{
    id: string;
    statement: string;
    evidenceIds: string[];
    intendedVariationAxis: string;
  }>;
}

ShortformDirectorProject.contentStrategy: ContentStrategyV1 | null;
```

새 project 생성 직후 값은 `null`이다. 빈 가설을 생성 완료로 표현하지 않는다.

## UI

- campaign prompt 아래에 선택형 `Vira 근거 JSON` 입력을 둔다.
- JSON array만 허용하고 client parse 오류를 API 호출 전에 표시한다.
- lab/legacy opt-in을 각각 명시적인 checkbox로 제공한다.
- project card에는 candidate/context/excluded 개수와 `전략 미생성` 상태를 표시한다.
- 자동 Vira 연동, 전략 생성, 렌더 버튼은 추가하지 않는다.

## 비침범 경계

- 기존 Angular `features/shortform/**` 변경 금지
- 기존 Nest `modules/shortform/**`, `modules/shortform-core/**` 변경 금지
- Vira 저장소 read-only
- 기존 shortform API/store와 데이터 교차 금지
- renderer/provider/web_api 호출 추가 금지

## 수용 기준

1. 실제 Vira 현재 필드에서 파생한 합성 fixture 3종이 validator를 통과한다.
2. 잘못된 payload, duplicate id, lifecycle spoofing은 400으로 거부된다.
3. 기본 정책은 active/on-demand만 candidate로 허용하고 lab/legacy는 opt-in 전 제외한다.
4. partial은 context-only, insufficient/unavailable은 excluded다.
5. project가 evidence, policy, admission과 `contentStrategy: null`을 전용 store에 저장한다.
6. Angular에서 수동 JSON handoff와 opt-in이 전용 director API로 전달된다.
7. 기존 shortform 경로는 `origin/dev` 대비 diff 0이다.
8. 관련 테스트와 Angular/Nest build가 통과한다.

## 비범위

- Vira exporter/API/auth/webhook
- Vira DB 직접 접근
- BrandProfile/SourcePack claim 편집 UI
- LLM ContentStrategy derivation
- native VideoPlan scene 생성
- renderer/compiler/provider/queue/billing
