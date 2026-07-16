# Vira 현재 코드 감사와 Clipper evidence handoff 설계

작성일: 2026-07-16 KST

## 문서 상태

- 이 문서는 PDF가 아니라 `/Users/jina/project/vira`의 현재 코드를 기준으로 작성한 working design이다.
- 감사 기준은 `main`의 `2f1d1fd`이며, 감사 시점에 `origin/main`과 동기화된 clean 상태였다.
- Vira 저장소는 읽기만 했고 변경하지 않았다.
- Clipper/Vira 간 API, 인증 방식, 데이터 SoT는 아직 확정하지 않았다.
- 문서는 사용자 지시에 따라 `.codex`에만 둔다.

## 결론

현재 Vira의 기본 제품 표면은 PDF에서 강조한 `16개 포맷 + 5개 그룹 + 3초 통과율 + Viral Score`가 아니다. 2026-07-10부터 `shorts_*` 테이블을 읽는 YouTube Shorts 탐색 화면이 `/intel/market`의 기본 경로가 됐고, 기존 `intel_market_*`와 Viral Intelligence 실행 함수는 등록 해제됐다.

따라서 Clipper는 Vira 입력을 다음 네 종류로 분리해야 한다.

1. 현재 활성화된 원시 관측: Shorts 메타데이터, 최신 지표, 댓글 감성
2. 현재 코드가 계산하는 파생 관측: 또래 연령 버킷 내 성장 속도 백분위
3. 실행 가능한 별도 추론 자산: 단일 영상 8차원 AI 분석의 완료 결과
4. 보존됐지만 비활성인 legacy 자산: 포맷/훅 분류와 keyword Viral Score

PDF와 제품 로드맵은 방향 자료로 남기되, 현재 런타임 계약으로 사용하지 않는다.

## 저장소·런타임 경계

- 애플리케이션: Next.js 16, React 19, TypeScript
- DB access: Drizzle ORM + PostgreSQL
- 비동기 실행: Inngest
- media/object storage: Cloudflare R2 abstraction
- production 전제: AWS EC2의 Docker + Caddy, AWS RDS PostgreSQL 18, Inngest Cloud

향후 연동 설계에서 Vercel/Neon을 현재 전제로 두지 않는다. Clipper가 Vira DB나 R2에 직접 연결하는 대신, Vira가 소유한 versioned export boundary를 두는 방향이 현재 배포 구조에도 맞는다.

## 실제 제품·파이프라인 상태

| 영역 | 현재 코드 | lifecycle | Clipper에서의 취급 |
|---|---|---|---|
| Market Explorer | `/intel/market`, `tshow-dashboard.ts`, `shorts_*` | `active` | 현재 관측 근거로 사용 가능 |
| Growth Lab | `/intel/Tmarket`, `tmarket-dashboard.ts`, `shorts_*` | `lab` | 계산법을 함께 보존할 때 파생 근거로 사용 |
| 8차원 영상 분석 | `src/lib/ai/modules`, `analyzeVideo` 등록 유지 | `on_demand` | 완료된 run과 성공 module만 선택적으로 사용 |
| 구 Market/포맷·훅 | `_legacy-market-monitor`, `intel_market_*` | `legacy_unregistered` | 기본 전략 입력에서 제외 |
| Viral Intelligence | UI·DB·계산 코드는 남아 있으나 Inngest handler/rolling cron 미등록 | `legacy_unregistered` | 현재 생성 가능한 신호로 가정 금지 |
| Vira → Clipper 연동 | 전략 문서의 목표만 존재 | `not_implemented` | API나 수동 연동이 존재한다고 표현 금지 |

`/intel/viral` 링크와 report 생성 action은 남아 있지만, `intelViralReport` 이벤트 핸들러가 현재 Inngest route에 등록돼 있지 않다. 화면의 존재를 활성 파이프라인의 증거로 간주하면 안 된다.

## 현재 활성 Market 데이터

### 수집·관측 모델

`shorts_videos`는 YouTube Shorts의 발견 시점 메타데이터를 보존한다.

- 안정 식별자: `platform_video_id`
- 발견 문맥: keyword, Naver category
- 콘텐츠 메타: title, description, duration, language, channel, upload date, tags, YouTube categories, thumbnail, subtitles
- 발견 시 조회수: `discovery_views`

`shorts_snapshots`는 영상별·KST 날짜별 view/like/comment count를 저장한다. 등록된 `shortsSnapshotCron`은 매일 09:00 KST에 실행되며, 업로드 1년 미만 또는 날짜를 알 수 없는 영상을 추적한다.

`shorts_comments`는 snapshot별 상위 댓글을 저장하고, `comment_sentiments`는 댓글별 긍정/부정/중립 추론 결과와 batch 상태를 별도로 관리한다.

### `/intel/market`

현재 기본 시장 화면은 request 시점에 다음을 읽는다.

- 최신 snapshot의 조회수·좋아요·댓글수
- snapshot이 없을 때의 발견 조회수 fallback
- Naver category와 수집 keyword
- 제목·설명에서 추출한 hashtag
- 긍정·부정 댓글 수와 댓글 상세
- 조회수, 좋아요, 댓글, `(좋아요 + 댓글) / 조회수` 정렬

이 화면에는 현재 포맷 code, 포맷 group, hook strength, 3초 통과율이 없다.

### `/intel/Tmarket`

Growth Lab은 snapshot이 3개 이상인 영상만 대상으로 다음을 request 시점에 계산한다.

```text
vd = (최근 조회수 - 세 번째 최근 조회수) / 두 endpoint 날짜 간격
s  = 같은 영상 나이 버킷 안에서 vd의 percent_rank × 100
```

영상 나이 버킷:

- 0~7일
- 8~30일
- 31~90일
- 91~365일
- 365일 이상

현재 UI의 `뜨는 중`은 `s >= 90`, `새로 뜨기 시작`은 이 조건을 만족하면서 업로드 후 7일 이내인 영상이다. 이는 같은 버킷 안의 상대 성장 속도이지, 바이럴 성공 확률이나 인과적 품질 점수가 아니다.

현재 계산 결과는 별도 immutable report로 저장되지 않는다. Clipper로 넘기려면 export 시점에 사용한 endpoint 날짜, 표본 수, 버킷, 계산법 버전을 함께 materialize해야 한다.

## 8차원 분석의 실제 계약

현재 module group은 다음과 같다.

- core: 광고 분류, 훅 분석, 콘텐츠 구조, 비주얼 스타일, 타깃·톤
- extras: 오디오 스타일, 자막·화면 텍스트
- meta: 바이럴 요인

실행 순서:

```text
shared input 준비
  → core 5개를 한 번의 multimodal structured output으로 실행
  → extras 2개를 독립 실행
  → 완료된 core 결과를 근거로 virality_factors 실행
  → run을 succeeded / partial / failed로 종료
```

Clipper와 직접 연결하기 좋은 실제 필드는 다음과 같다.

- 훅: hook type, opening phrase, opening frame 설명, pacing, attention devices
- 구조: narrative pattern, 시간 구간별 beat와 role, setup/payoff, replay trigger, loop
- 비주얼: 제작 수준, 촬영 환경, 색감, 편집 방식, 컷 리듬, 카메라, framing, aesthetic tag
- 타깃·톤: 연령·성별 편향, 관심사, 문화 맥락, persona, 말투, 감정 arc
- 오디오: BGM/voiceover 추정, pace/energy, SFX pattern, audio-visual sync, silence ratio
- 자막: style, position, animation, readability, frame별 overlay와 role, text dependency
- 광고: 광고 가능성·유형, 브랜드·제품, 고지, CTA
- 바이럴 요인: 근거 module이 명시된 가설, share/replay trigger, pain point, 재현 one-liner와 key ingredients

주의할 점:

- 오디오 module은 실제 음원을 직접 듣는 분석이 아니라 transcript와 메타데이터 기반 추론이다.
- 각 module의 `confidence`는 해당 AI 추론의 확신도다. 시장 표본의 통계적 신뢰도와 같은 필드로 합치면 안 된다.
- `reproduction_recipe`와 virality hypothesis는 관측된 인과 법칙이 아니라 선행 module 결과에 근거한 생성 가설이다.
- 현재 분석 실행 handler는 등록돼 있지만, 이를 시작하는 기존 사용자 UI는 `_archived` 아래에 있다.
- 기존 `/api/videos/:id/analysis`와 `/api/analyses/:id/status`는 내부 DB shape 조회용이다. versioned export, subject identity, evidence lifecycle을 제공하지 않으므로 Clipper 통합 API로 사용하지 않는다.

## Legacy Market·Viral 자산

기존 코드는 다음 자산을 보존하고 있다.

- 16개 format code와 5개 format group
- `hookStrength`, `threeSecPass`, hook phrase
- 60일 keyword search, keyword당 top 100
- 최소 cohort 15
- velocity 35%, recency 25%, engagement 20%, view scale 20%의 Viral Score
- 14일 recent concentration
- p90 velocity/engagement/view scale 기반 component
- rolling cohort와 score history

그러나 2026-07-10부터 관련 discovery, Tier 1, report, rolling snapshot 함수가 Inngest route에서 등록 해제됐다. 다음 원칙을 적용한다.

- 새 Clipper generation의 기본 입력으로 사용하지 않는다.
- 과거 완료 report를 사용한다면 `legacy_unregistered` lifecycle과 계산 버전을 명시한다.
- PDF에 있다는 이유만으로 새 format/hook/viral 값이 계속 생산된다고 가정하지 않는다.
- 재활성화되거나 `shorts_*` 세대로 이식되기 전까지 current Vira contract라고 부르지 않는다.

## PDF 가정과 현재 코드의 차이

| PDF/기존 설계 가정 | 현재 코드 기준 정정 |
|---|---|
| Vira 입력은 16-format/5-group 중심 | 현재 기본 Market은 category/keyword/tag/metrics/comment sentiment 중심 |
| 3초 통과율과 hook strength가 현재 시장 신호 | 해당 필드는 legacy `intel_market` 세대에 남아 있음 |
| Viral Score와 phase가 현재 생성 가능 | report handler와 rolling cron이 등록 해제됨 |
| Vira → Clipper가 현재 수동 연동 | 코드에는 Clipper handoff/API/버튼 구현이 없음. 전략 목표만 존재 |
| 모든 Vira 신호에 공통 confidence가 있음 | raw observation, derived percentile, AI inference의 품질 의미가 서로 다름 |
| category가 foods/beauty/living으로 고정 | 현재 `shorts_videos.naver_category`는 열린 문자열이며 실제 화면은 동적 분류 |

## `vira-evidence.v1` handoff

### 설계 원칙

1. Vira DB 전체나 내부 row를 Clipper prompt에 직접 넣지 않는다.
2. live query 결과는 handoff 시점에 immutable evidence로 materialize한다.
3. 원시 관측, 결정적 파생값, AI 추론, legacy 값을 구분한다.
4. `insufficient`를 낮은 score로 변환하지 않는다.
5. stable subject key는 `platform + platformVideoId`를 사용한다. `shorts_videos.id`와 `videos.id`는 trace ref일 뿐 교차 시스템 identity로 쓰지 않는다.
6. evidence는 생성 지시가 아니다. Clipper의 `ContentStrategy`가 evidence를 인용해 가설을 만든다.
7. 로컬 파일 경로, provider secret, 인증 정보는 전달하지 않는다.

### Envelope

```ts
type ViraEvidenceKind =
  | 'market.video-observation'
  | 'market.peer-growth'
  | 'analysis.video-8d'
  | 'legacy.market-format-hook'
  | 'legacy.keyword-viral-report';

type ViraEvidenceLifecycle =
  | 'active'
  | 'lab'
  | 'on_demand'
  | 'legacy_unregistered';

type ViraEvidenceState =
  | 'sufficient'
  | 'partial'
  | 'insufficient'
  | 'unavailable';

interface ViraEvidenceEnvelopeV1<TPayload> {
  schemaVersion: 'vira-evidence.v1';
  id: string;
  kind: ViraEvidenceKind;
  evidenceClass: 'observed' | 'derived' | 'inferred';
  source: {
    system: 'vira';
    surface:
      | 'shorts-market'
      | 'shorts-growth-lab'
      | 'video-analysis-8d'
      | 'legacy-intel-market'
      | 'legacy-intel-viral';
    lifecycle: ViraEvidenceLifecycle;
    codeRevision?: string;
    recordRefs?: Array<{
      kind: 'shorts-video' | 'analysis-run' | 'viral-report';
      id: string;
    }>;
  };
  subject: {
    platform: 'youtube_shorts';
    platformVideoId?: string;
    keyword?: string;
    category?: string;
  };
  observation: {
    materializedAt: string;
    window?: { from: string; to: string };
    sampleSize?: number;
    state: ViraEvidenceState;
  };
  method: {
    id: string;
    version: string;
    parameters?: Record<string, string | number | boolean>;
  };
  payload: TPayload;
}
```

공통 `confidence`는 두지 않는다. AI module의 confidence는 해당 module payload 안에 두고, 시장 데이터의 충분성은 `observation.state`, `sampleSize`, window로 표현한다.

### 활성 Market observation payload

```ts
interface ViraMarketVideoObservationV1 {
  title?: string;
  channel?: string;
  keyword: string;
  naverCategory?: string;
  tags: string[];
  metrics: {
    snapshotDate?: string;
    views?: number;
    viewsSource: 'snapshot' | 'discovery';
    likes?: number;
    comments?: number;
    engagementRate?: number;
  };
  commentSentiment?: {
    positive: number;
    negative: number;
    neutral?: number;
    classified: number;
  };
}
```

댓글 문구 자체를 전달할 경우에는 별도 sample 정책, 개인정보 최소화, 개수 제한을 먼저 정한다. Phase 1 handoff에는 aggregate count만 둔다.

### peer growth payload

```ts
interface ViraPeerGrowthSignalV1 {
  snapshotFrom: string;
  snapshotTo: string;
  snapshotCount: 3;
  dailyViewDelta: number;
  ageDays: number;
  ageBucket: '0-7' | '8-30' | '31-90' | '91-365' | '365+';
  percentile: number;
  risingThreshold: 90;
  isRising: boolean;
  isNewRising: boolean;
}
```

`method.id`는 예를 들어 `last3-endpoint-daily-delta-age-bucket-percentile`, `version`은 `1`로 고정한다. 현재 loader가 endpoint 날짜를 응답하지 않으므로 exporter 구현 시 이를 보강해야 한다.

### 8차원 분석 payload

전체 module JSON을 복사하지 않고 planner에 필요한 필드만 정규화한다.

```ts
interface ViraVideoAnalysis8dV1 {
  analysisRunId: string;
  runStatus: 'succeeded' | 'partial';
  completedAt?: string;
  modules: {
    ad?: {
      probability: number;
      primaryType: string;
      brands: string[];
      products: string[];
      disclosurePresent: boolean;
      cta?: { phrase?: string; channel?: string; timestampSec?: number };
      confidence: number;
    };
    hook?: {
      type: string;
      secondaryType?: string;
      windowSec: number;
      phrases: string[];
      attentionDevices: string[];
      openingFrame: string;
      pacing: number;
      confidence: number;
    };
    structure?: {
      narrativePattern: string;
      beats: Array<{
        role: string;
        startSec: number;
        endSec: number;
        summary: string;
      }>;
      replayTriggers: string[];
      loopClosure: boolean;
      confidence: number;
    };
    visual?: Record<string, unknown>;
    audienceAndTone?: Record<string, unknown>;
    audio?: Record<string, unknown>;
    captionAndText?: Record<string, unknown>;
    virality?: {
      hypotheses: Array<{
        factor: string;
        evidenceModules: string[];
        strength: 'weak' | 'moderate' | 'strong';
        rationale: string;
      }>;
      shareTriggers: string[];
      replayTriggers: string[];
      painPoints: string[];
      reproductionRecipe: {
        oneLiner: string;
        keyIngredients: string[];
      };
      confidence: number;
    };
  };
}
```

`visual`, `audienceAndTone`, `audio`, `captionAndText`의 최종 compact shape는 첫 native planner use case와 token budget을 정한 뒤 좁힌다. 현재 Vira module schema를 그대로 외부 계약으로 동결하지 않는다.

## Clipper 내부 연결

```text
ViraEvidenceEnvelope[]
  ↓ validate + lifecycle policy + compact digest
PlanningContext.marketEvidence
  ↓ StrategyDeriver
ContentStrategy.hypotheses[]
  - statement
  - evidenceIds[]
  - intendedVariationAxis
  ↓ Native VideoPlan planner
Scene / Beat / Shot / Layer
  - strategyHypothesisIds[]
```

정책:

- `active`: 충분한 관측이면 기본 후보
- `lab`: 사용자/실험 설정이 명시적으로 허용할 때만 후보
- `on_demand`: 완료된 run의 성공 module만 후보
- `legacy_unregistered`: 기본 제외, 사용자가 과거 report 사용을 명시할 때만 후보
- brand/source 사실 주장은 Market evidence가 아니라 `SourcePack.claims`를 인용
- 댓글 감성은 audience language/반응 가설에만 사용하고 제품 사실 근거로 사용하지 않음
- 성장 percentile과 재현 레시피는 variation 가설의 우선순위 근거이지 성공 보장이 아님

## 연동 경계

현재 Vira에는 Clipper용 export endpoint나 handoff button이 없다. 다음 경계를 지킨다.

- Clipper desktop이 Vira DB에 직접 연결하지 않는다.
- 기존 내부 analysis 조회 API를 외부 계약으로 재사용하지 않는다.
- 첫 구현은 versioned fixture/manual import로 `PlanningContext` 소비 경계를 검증할 수 있다.
- 자동 연동 단계에서는 Vira가 immutable evidence를 export하고 Clipper가 schema validation 후 저장한다.
- 인증, tenant/owner mapping, retention, delete propagation, API 위치는 별도 결정한다.
- Vira의 live query와 Clipper project에는 동일 snapshot ID/hash를 남겨 재현 가능하게 한다.

## 기존 Phase 1a 구현에 미치는 영향

현재 `LegacyClipVideoPlanAdapter`와 `video-plan.v1`은 Vira의 format/viral schema를 전혀 가정하지 않는다. 따라서 이번 감사로 Phase 1a 코드를 수정할 필요는 없다.

- `VideoPlan`은 creative planning IR 역할을 유지한다.
- Vira evidence는 `VideoPlan` 자체가 아니라 상위 `PlanningContext`에 둔다.
- legacy clip에서 파생된 plan에는 Vira evidence를 거꾸로 추정해 넣지 않는다.
- native planner가 도입될 때만 strategy/evidence reference를 plan에 추가한다.

## 다음 구현 순서

1. Clipper에 `PlanningContext`와 `vira-evidence.v1` runtime validator를 추가한다.
2. 실제 Vira 데이터와 같은 구조의 비밀 없는 fixture로 import·저장·legacy project 호환을 TDD한다.
3. `StrategyDeriver`가 evidence lifecycle과 state를 지키고 evidence ID를 인용하는지 검증한다.
4. 첫 use case에 필요한 8차원 compact projection만 확정한다.
5. 그 뒤 Vira exporter/API와 identity/auth 계약을 별도 설계한다.
6. native `VideoPlan` planner와 `VideoPlan → RenderRecipe` compiler를 순차적으로 연결한다.

## 미결정

- `/intel/Tmarket`을 정식 active surface로 승격할지
- legacy format/hook/viral pipeline을 폐기할지 `shorts_*` 위에 재구현할지
- 8차원 분석을 어떤 현재 Vira 화면에서 다시 trigger할지
- Vira exporter의 소유 서비스와 API 인증 방식
- 댓글 원문을 handoff에 포함할지와 개인정보/retention 정책
- `visual` 등 8차원 module의 compact projection 최종 shape
- evidence snapshot의 저장 위치와 retention/deletion 전파
