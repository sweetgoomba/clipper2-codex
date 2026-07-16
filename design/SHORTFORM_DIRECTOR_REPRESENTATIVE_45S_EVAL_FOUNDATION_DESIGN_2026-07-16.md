# AI 숏폼 디렉터 — 대표 45초 품질 eval foundation 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`

## 목적

현재 validator는 VideoPlan이 계약상 유효한지는 판별하지만, 그 plan이 대표 숏폼 기준에서 충분한 hook·서사·시각 변화·가독성을 갖는지는 알려주지 않는다.

이번 단계는 비밀 없는 합성 45초 기준편과 결정적 eval report를 추가한다.

```text
Vira-shaped synthetic evidence
  + BrandProfile / CampaignBrief / SourcePack
  + expected ContentStrategy draft
  + expected VideoPlan draft
                ↓
       기존 contract validator
                ↓
 structural-proxy quality evaluator
   ├─ 자동 pass/fail
   ├─ 자동 warning + 측정값
   └─ manual_review_required 축
```

실제 LLM 호출이나 subjective 총점 없이도 schema/prompt/compiler 변경이 대표 기준편을 악화시키는지 회귀 테스트로 잡는 것이 목표다.

## 대표 case

기존 합성 선크림 Vira fixture를 그대로 재사용한다.

- active Market observation: candidate
- completed on-demand 8D hook/structure analysis: candidate
- lab peer growth: opt-in하지 않아 excluded
- 실제 브랜드나 제품이 아닌 `합성 브랜드/합성 선크림`
- 승인 claim 2개와 provenance label만 사용
- 45초 consideration/conversion brief
- hook → context → value → proof → CTA의 5 scene
- 검색/보유/source/programmatic/generated-image를 섞은 provider-neutral layer 계획

fixture에는 cookie, URL credential, JWT, provider key, 실제 내부 식별자를 넣지 않는다.

## report 계약

```ts
interface VideoPlanQualityReportV1 {
  schemaVersion: 'video-plan-quality-report.v1';
  evaluationMode: 'structural_proxy';
  passed: boolean;
  checks: Array<{
    id: string;
    severity: 'blocking' | 'warning';
    status: 'pass' | 'fail' | 'warning';
    message: string;
  }>;
  metrics: {
    durationMs: number;
    sceneCount: number;
    beatCount: number;
    shotCount: number;
    layerCount: number;
    narrationCharacterCount: number;
    narrationCharactersPerSecond: number;
    averageShotDurationMs: number;
    maxShotDurationMs: number;
    unresolvedVisualLayerCount: number;
  };
  manualReviewRequired: ManualQualityAxis[];
}
```

`passed`는 blocking check가 모두 pass라는 뜻일 뿐, 영상 품질이 사람 기준으로 좋다는 뜻이 아니다. calibration 전 임의의 100점 총점이나 production threshold를 만들지 않는다.

## 자동 blocking check

| id | 규칙 |
|---|---|
| `grounding_integrity` | Beat 참조가 선택 hypothesis 안에 있고 선택 evidence/claim이 모두 최소 한 번 쓰임 |
| `hook_in_first_3s` | 선택 hook이 narration 또는 text로 3초 안에 시작 |
| `cta_coverage` | 마지막 CTA scene의 programmatic CTA layer가 선택 CTA를 포함 |
| `narrative_arc` | 첫 scene hook, 마지막 scene CTA, 중간에 value 또는 proof가 존재 |
| `visual_coverage` | 모든 Beat에 visual layer가 최소 하나 존재 |
| `asset_authenticity` | product/evidence는 생성형 금지, diagram/text는 programmatic |
| `prohibited_copy` | intent, narration, layer copy에 금지 표현 없음 |
| `disclosure_coverage` | disclosure requirement가 있으면 disclosure text layer에서 확인 가능 |

## 자동 warning check

초기 heuristic은 대표 fixture의 회귀 탐지용이며 품질 진실값이 아니다.

- `narration_density`: 공백을 제외한 narration 문자 수가 초당 3~9 범위를 벗어남
- `shot_pacing`: 평균 shot 길이가 2~6초 범위를 벗어나거나 단일 shot이 10초를 초과
- `text_readability`: text layer가 36자를 초과하거나 표시 시간이 문자당 60ms보다 짧음
- `unresolved_assets`: unresolved visual layer가 하나 이상 남음

warning은 `passed`를 false로 바꾸지 않는다. 임계값은 실제 TTS/render benchmark 뒤 조정한다.

## 사람 평가 축

자동 evaluator가 단정하지 않고 report에 항상 남긴다.

- `source_faithfulness`
- `hook_strength`
- `script_coherence`
- `narration_visual_fit`
- `visual_brand_consistency`
- `motion_continuity`
- `mobile_readability`

이 축은 후속 rendered sample review에서 1~5 rubric과 reviewer note를 붙인다. 이번 단계에서는 자동 점수를 생성하지 않는다.

## 배치 경계

- canonical VideoPlan을 소유하는 desktop Nest `shortform-director/domain`에 순수 evaluator를 둔다.
- fixture와 회귀 테스트는 `test/fixtures/shortform-director`와 `test/`에 둔다.
- production generation service, operation billing, web API, Angular UI에는 연결하지 않는다.
- 기존 `shortform_prompt`는 계속 변경하지 않는다.

## 수용 기준

1. 대표 case가 기존 Vira/ContentStrategy/VideoPlan validator를 모두 통과한다.
2. 대표 plan report의 blocking check가 모두 pass한다.
3. warning과 metrics가 고정 expected snapshot으로 검증된다.
4. hook 시작 지연, grounding 누락, 생성형 product route, 과밀 narration 같은 변형이 예상한 fail/warning을 낸다.
5. report는 structural proxy임을 명시하고 manual 축을 자동 채점하지 않는다.
6. 기존 shortform 경로는 `origin/dev` 대비 diff 0이다.

## 2026-07-16 구현 결과

대표 fixture와 evaluator는 다음 경계에 추가했다.

- `desktop/clipper_nestjs/test/fixtures/shortform-director/representative-45s-eval-case.json`
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-quality-evaluator.ts`
- `desktop/clipper_nestjs/test/shortform-director-quality-eval.test.js`

기준편의 결정적 측정값은 다음과 같다.

- 45,000ms, 5 scene, 7 beat, 10 shot, 20 layer
- 공백 제외 narration 225자, 초당 5자
- 평균 shot 4,500ms, 최대 shot 7,500ms
- unresolved visual 0개

평가기 부재 RED를 먼저 확인한 뒤 기준편, hook 3초 지연, grounding 누락, 생성형 product route, narration 과밀, unresolved background 변형을 GREEN으로 만들었다. evaluator는 production service나 operation에 등록하지 않은 순수 도메인 객체이며 입력을 변경하지 않는다.

검증 결과:

- desktop Nest `shortform-director-*.test.js`: 24/24 통과
- desktop Nest TypeScript build 통과
- 기존 Angular/Nest/web API shortform 경로: `origin/dev` 대비 diff 0
- 실제 provider 호출, migration, server/Electron, commit/push/deploy 없음

## 비범위

- 실제 OpenAI/Vira API 호출
- 자동 semantic judge 또는 LLM-as-a-judge
- production 생성 차단 threshold
- 실제 TTS, AssetRef resolution, render 결과 분석
- renderer/provider 선정
- UI, DB, migration, commit/push/deploy
