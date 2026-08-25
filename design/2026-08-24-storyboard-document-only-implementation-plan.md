# Storyboard Document-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Storyboard plugin into a read-only, copyable storyboard-document workflow and remove every plugin-owned capability that turns that document into generated media.

**Architecture:** Keep the existing two internal inference purpose IDs, but change their contracts to an editorial plan followed by shot-production direction. Desktop Nest validates both stages, persists stage checkpoints and the final immutable storyboard as lineage artifacts, exposes a storyboard view that can also adapt earlier successful results, and never creates new media-production project state. Angular renders that view and builds all copy output deterministically; Web API, Electron, Web Admin, and Desktop Nest remove media-generation/runtime surfaces while Python receives a boundary verification only unless a directly dedicated symbol is found.

**Tech Stack:** TypeScript, NestJS, TypeORM, Angular, RxJS, Electron, Node test runner, Jest, Karma/Jasmine, Python/pytest.

**Spec:** `.codex/design/2026-08-24-storyboard-document-only-design.md`

## Global Constraints

- The retained user flow ends at storyboard review and clipboard copy.
- Normal generation performs exactly two GPT-5.6 Luna inference calls; one failed-stage recovery is allowed, for an absolute maximum of three provider calls.
- A successful first pass is persisted before the second pass starts and is never repeated merely because the app or page restarted.
- No user-facing model or production-mode selector remains.
- No image/video generation, media search/download/storage, TTS, render, completed-video, or media-export action remains in the plugin.
- Research-time reference video analysis remains unchanged.
- New results use `storyboard-document.v1`; earlier successful results remain readable but missing prompt/search fields are not fabricated.
- Search queries are planning guidance only. The product does not search, download, verify rights, or claim that an image is reusable.
- Clipboard output excludes run IDs, artifact IDs, provider diagnostics, credential data, and storage paths.
- New HTTP contracts remain raw Nest responses; removed endpoints return the standard Nest 404 response.
- Preserve the existing Angular changes in `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html` and its `.spec.ts`; do not edit or stage them in this work.
- Preserve already-applied database migration files. Remove active media-job entities through a new forward migration.
- Automated tests must not make a paid external inference or media-generation call.

---

## File and Contract Map

The implementation is one coordinated contract migration across six repositories:

- `web/clipper_web_api`: owns strict JSON schemas, prompts, inference transport, active entity registration, and removal of media-generation routes.
- `desktop/clipper_nestjs`: owns candidate lineage, two-stage orchestration, validation, artifact checkpoints, recovery, earlier-result adaptation, and public storyboard endpoints.
- `desktop/clipper_angular`: owns typed reads, progress/history state, read-only presentation, and deterministic clipboard documents.
- `desktop/clipper_electron`: owns packaged runtime/resource wiring and must stop bundling the Storyboard rendering runtime.
- `web/clipper_web_admin`: owns provider credential administration and must stop presenting the removed fal.ai generation credential.
- `desktop/clipper_python`: has no currently detected Storyboard-specific symbol; it is verification-only so shared renderer behavior stays intact.

The retained internal purpose IDs deliberately remain `video-plan` and `scene-media-decision` to avoid historical artifact and usage-accounting migrations. Their new payloads are:

```ts
export interface StoryboardEditorialPlanV1 {
  schemaVersion: 'storyboard-editorial-plan.v1';
  title: string;
  targetDurationMs: number;
  overview: {
    coreMessage: string;
    audience: string;
    format: string;
    tone: string;
    pacing: string;
    storyArc: string;
    narrationDirection: string;
    visualStyle: string;
    colorLighting: string;
    musicDirection: string;
    ambienceDirection: string;
    soundEffectDirection: string;
    cta: string;
    continuityRules: string[];
    requiredFacts: string[];
    factualConstraints: string[];
    prohibitedExpressions: string[];
    negativeConstraints: string[];
  };
  scenes: Array<{
    sceneIndex: number;
    purpose: 'hook' | 'context' | 'evidence' | 'development' | 'payoff' | 'cta';
    intent: string;
    durationMs: number;
    narration: string;
    onScreenText: string[];
    claim: string;
    evidenceIds: string[];
  }>;
}

export interface StoryboardShotDirectionV1 {
  schemaVersion: 'storyboard-shot-direction.v1';
  shots: Array<{
    sceneIndex: number;
    shotIndex: number;
    startOffsetMs: number;
    durationMs: number;
    visualDirectionKo: string;
    subject: string;
    setting: string;
    action: string;
    composition: string;
    camera: string;
    lighting: string;
    colorTexture: string;
    onScreenTextTreatment: string;
    audioDirection: string;
    transition: string;
    continuity: string[];
    aiVideoPromptEn: string;
    negativeConstraints: string[];
    imageSearchPlan: {
      recommendedSourceType:
        | 'official-image'
        | 'editorial-photo'
        | 'licensed-stock'
        | 'user-provided'
        | 'programmatic-graphic';
      queries: Array<{ language: 'ko' | 'en'; query: string }>;
      selectionCriteria: string[];
      avoid: string[];
      usage: {
        crop: string;
        motion: string;
        durationMs: number;
        overlay: string;
        transition: string;
      };
    };
  }>;
}
```

The assembled scene, shot, and search-plan types are exact rather than open-ended:

```ts
export type StoryboardSourceType =
  | 'official-image'
  | 'editorial-photo'
  | 'licensed-stock'
  | 'user-provided'
  | 'programmatic-graphic';

export interface StoryboardImageSearchPlanV1 {
  recommendedSourceType: StoryboardSourceType;
  queries: Array<{ language: 'ko' | 'en'; query: string }>;
  selectionCriteria: string[];
  avoid: string[];
  usage: {
    crop: string;
    motion: string;
    durationMs: number;
    overlay: string;
    transition: string;
  };
}

export interface StoryboardShotV1 {
  shotIndex: number;
  startMs: number;
  durationMs: number;
  visualDirectionKo: string;
  subject: string;
  setting: string;
  action: string;
  composition: string;
  camera: string;
  lighting: string;
  colorTexture: string;
  onScreenTextTreatment: string;
  audioDirection: string;
  transition: string;
  continuity: string[];
  aiVideoPromptEn: string;
  negativeConstraints: string[];
  imageSearchPlan: StoryboardImageSearchPlanV1;
}

export interface StoryboardSceneV1 {
  sceneIndex: number;
  startMs: number;
  durationMs: number;
  purpose: 'hook' | 'context' | 'evidence' | 'development' | 'payoff' | 'cta';
  intent: string;
  narration: string;
  onScreenText: string[];
  claim: string;
  evidenceIds: string[];
  shots: StoryboardShotV1[];
}
```

Desktop Nest assembles those payloads into this persisted output and projects both current and earlier formats into one public view:

```ts
export interface StoryboardDocumentV1 {
  schemaVersion: 'storyboard-document.v1';
  id: string;
  runId: string;
  profileId: string;
  researchRunId: string;
  topicId: string;
  candidateRunId: string;
  candidateId: string;
  title: string;
  targetDurationMs: number;
  aspectRatio: '9:16';
  overview: StoryboardEditorialPlanV1['overview'];
  scenes: StoryboardSceneV1[];
  createdAt: string;
}

export interface CurrentStoryboardViewV1 {
  schemaVersion: 'shortform-director-storyboard-view.v1';
  format: 'current';
  id: string;
  title: string;
  targetDurationMs: number;
  aspectRatio: '9:16';
  overview: StoryboardDocumentV1['overview'];
  scenes: StoryboardSceneV1[];
}

export interface EarlierStoryboardViewV1 {
  schemaVersion: 'shortform-director-storyboard-view.v1';
  format: 'earlier';
  id: string;
  title: string;
  targetDurationMs: number;
  aspectRatio: '9:16';
  overview: null;
  scenes: StoryboardSceneViewV1[];
}

export type StoryboardViewV1 =
  | CurrentStoryboardViewV1
  | EarlierStoryboardViewV1;

export interface StoryboardShotViewV1 {
  shotIndex: number;
  startMs: number;
  durationMs: number;
  visualDirectionKo: string;
  subject: string | null;
  setting: string | null;
  action: string | null;
  composition: string | null;
  camera: string | null;
  lighting: string | null;
  colorTexture: string | null;
  onScreenTextTreatment: string | null;
  audioDirection: string | null;
  transition: string | null;
  continuity: string[] | null;
  aiVideoPromptEn: string | null;
  negativeConstraints: string[] | null;
  imageSearchPlan: StoryboardImageSearchPlanV1 | null;
}

export interface StoryboardSceneViewV1 {
  sceneIndex: number;
  startMs: number;
  durationMs: number;
  purpose: StoryboardSceneV1['purpose'];
  intent: string;
  narration: string;
  onScreenText: string[];
  claim: string | null;
  evidenceIds: string[];
  shots: StoryboardShotViewV1[];
}
```

Use this canonical valid pair in contract, validator, assembler, gateway, and clipboard fixtures. Framework-specific specs may translate `as const` into plain JavaScript, but field names and timing stay identical:

```ts
const validEditorialPlan: StoryboardEditorialPlanV1 = {
  schemaVersion: 'storyboard-editorial-plan.v1',
  title: '신인 걸그룹 데뷔곡에 국내 창작자가 참여하는 이유',
  targetDurationMs: 30000,
  overview: {
    coreMessage: '국내 창작자 참여가 신인 그룹의 음악적 정체성을 선명하게 만든다.',
    audience: 'K-POP 신인 걸그룹 흐름을 빠르게 알고 싶은 10~30대',
    format: '근거 중심 30초 설명형 쇼츠',
    tone: '빠르고 명확한 분석',
    pacing: '첫 8초 훅, 12초 근거, 10초 결론',
    storyArc: '질문 제기에서 사례 확인을 거쳐 시청 포인트로 마무리한다.',
    narrationDirection: '한 문장에 한 주장만 담고 고유명사를 또렷하게 읽는다.',
    visualStyle: '공식 자료와 간결한 비교 그래픽을 교차한다.',
    colorLighting: '짙은 남색 배경에 밝은 포인트 컬러와 선명한 인물 조명',
    musicDirection: '도입은 짧은 비트, 근거 구간은 낮은 볼륨, 결론에서 상승',
    ambienceDirection: '공식 현장 컷에는 약한 관객 현장감을 유지한다.',
    soundEffectDirection: '핵심 문구 등장과 장면 전환에만 짧은 효과음을 사용한다.',
    cta: '다음 데뷔곡에서는 크레딧의 국내 창작자 이름도 확인해 보세요.',
    continuityRules: [
      '세로 9:16 구도를 유지한다.',
      '동일 인물의 얼굴과 의상을 장면 사이에서 바꾸지 않는다.',
    ],
    requiredFacts: [
      '공식 발표와 크레딧으로 확인된 참여 정보만 말한다.',
    ],
    factualConstraints: [
      '근거에 없는 차트 순위나 성과 수치를 추가하지 않는다.',
    ],
    prohibitedExpressions: [
      '무조건 성공한다',
      '업계를 완전히 바꿨다',
    ],
    negativeConstraints: [
      '워터마크와 임의 로고를 만들지 않는다.',
      '가로 화면이나 읽을 수 없는 자막을 만들지 않는다.',
    ],
  },
  scenes: [
    {
      sceneIndex: 0,
      purpose: 'hook',
      intent: '데뷔곡 크레딧을 봐야 하는 이유를 질문한다.',
      durationMs: 8000,
      narration: '신인 걸그룹의 색깔, 이제 데뷔곡 크레딧에서 먼저 보입니다.',
      onScreenText: ['데뷔곡 크레딧을 보세요'],
      claim: '데뷔곡 참여진은 그룹의 초기 음악 방향을 보여준다.',
      evidenceIds: ['evidence.1'],
    },
    {
      sceneIndex: 1,
      purpose: 'evidence',
      intent: '공식 크레딧과 발표 자료에서 국내 창작자 참여를 확인한다.',
      durationMs: 12000,
      narration: '공식 크레딧에 국내 싱어송라이터와 작곡가 참여가 확인되며, 팀의 첫인상도 더 구체적으로 설계됩니다.',
      onScreenText: ['공식 크레딧', '국내 창작자 참여'],
      claim: '공식 자료에서 국내 창작자 참여가 확인된다.',
      evidenceIds: ['evidence.1', 'evidence.2'],
    },
    {
      sceneIndex: 2,
      purpose: 'cta',
      intent: '다음 신인 그룹을 볼 때 확인할 구체적인 기준을 제안한다.',
      durationMs: 10000,
      narration: '다음 데뷔곡을 들을 때는 무대뿐 아니라 크레딧의 이름도 함께 확인해 보세요.',
      onScreenText: ['다음에는 크레딧까지'],
      claim: '크레딧은 시청자가 직접 확인할 수 있는 공식 정보다.',
      evidenceIds: ['evidence.2'],
    },
  ],
};

const validShotDirection: StoryboardShotDirectionV1 = {
  schemaVersion: 'storyboard-shot-direction.v1',
  shots: [
    {
      sceneIndex: 0,
      shotIndex: 0,
      startOffsetMs: 0,
      durationMs: 4000,
      visualDirectionKo: '공식 데뷔 무대의 세로 크롭 위로 질문 문구를 크게 연다.',
      subject: '신인 걸그룹 공식 데뷔 무대',
      setting: '밝은 쇼케이스 무대',
      action: '멤버들이 첫 포즈를 잡는다.',
      composition: '중앙 인물 중심의 미디엄 와이드 세로 구도',
      camera: '느린 디지털 푸시인',
      lighting: '공식 무대의 전면 조명',
      colorTexture: '짙은 남색과 밝은 포인트 컬러, 선명한 질감',
      onScreenTextTreatment: '상단 안전영역에 데뷔곡 크레딧을 보세요를 두 줄로 표시',
      audioDirection: '도입 비트와 짧은 전환 효과음',
      transition: '크레딧 화면으로 빠른 매치 컷',
      continuity: ['다음 컷과 동일한 포인트 컬러를 유지한다.'],
      aiVideoPromptEn: 'Vertical 9:16 official debut showcase, rookie girl group holding the opening pose, centered medium-wide composition, slow push-in, clean front stage lighting, dark navy with bright accent colors, no added logos or text.',
      negativeConstraints: ['얼굴 변경 금지', '임의 로고 금지', '가로 프레임 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'official-image',
        queries: [
          { language: 'ko', query: '신인 걸그룹 공식 데뷔 쇼케이스 사진' },
          { language: 'en', query: 'rookie girl group official debut showcase photo' },
        ],
        selectionCriteria: ['공식 채널 출처', '멤버가 선명한 세로 크롭 가능 구도'],
        avoid: ['팬 합성 이미지', '워터마크가 화면 중앙을 가리는 이미지'],
        usage: {
          crop: '인물을 중앙에 둔 9:16 크롭',
          motion: '4초 동안 104%까지 느리게 확대',
          durationMs: 4000,
          overlay: '상단 질문 문구와 하단 얇은 그라데이션',
          transition: '다음 컷으로 4프레임 매치 컷',
        },
      },
    },
    {
      sceneIndex: 0,
      shotIndex: 1,
      startOffsetMs: 4000,
      durationMs: 4000,
      visualDirectionKo: '공식 음원 크레딧의 참여진 영역을 확대해 핵심 이름을 강조한다.',
      subject: '공식 음원 크레딧',
      setting: '짙은 배경의 세로 정보 카드',
      action: '참여진 행에 강조선이 순서대로 나타난다.',
      composition: '크레딧 일부를 크게 잡은 정면 클로즈업',
      camera: '고정 화면에서 강조선만 움직인다.',
      lighting: '정보 카드 자체의 균일한 밝기',
      colorTexture: '남색 배경과 흰 글자, 노란 강조선',
      onScreenTextTreatment: '하단에 그룹의 첫인상을 만드는 이름을 표시',
      audioDirection: '비트를 낮추고 강조선마다 가벼운 클릭음',
      transition: '강조선이 화면을 가로지르며 다음 장면으로 전환',
      continuity: ['첫 컷의 남색과 노란 포인트를 유지한다.'],
      aiVideoPromptEn: 'Vertical 9:16 clean editorial credit card, close-up of official music credits with sequential highlight lines, dark navy background, white type, yellow accents, fixed camera, crisp readable layout, no invented names or logos.',
      negativeConstraints: ['근거에 없는 이름 추가 금지', '읽을 수 없는 글자 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'programmatic-graphic',
        queries: [],
        selectionCriteria: ['공식 크레딧의 확인된 문구를 정확히 재현'],
        avoid: ['실제 크레딧처럼 보이는 임의 이름 생성'],
        usage: {
          crop: '9:16 정보 카드 전체 화면',
          motion: '강조선만 위에서 아래로 순차 등장',
          durationMs: 4000,
          overlay: '확인된 참여진 행만 표시',
          transition: '가로 와이프',
        },
      },
    },
    {
      sceneIndex: 1,
      shotIndex: 0,
      startOffsetMs: 0,
      durationMs: 6000,
      visualDirectionKo: '공식 발표 자료와 크레딧을 좌우 비교 카드로 배치한다.',
      subject: '공식 발표 자료와 음원 크레딧',
      setting: '두 자료를 비교하는 세로 분할 화면',
      action: '발표 문구와 크레딧의 일치 부분에 체크가 표시된다.',
      composition: '상하 2단 비교 카드',
      camera: '고정 정면',
      lighting: '자료의 가독성을 우선한 균일한 밝기',
      colorTexture: '흰 카드와 남색 테두리, 녹색 확인 표시',
      onScreenTextTreatment: '중앙에 공식 자료로 확인을 짧게 표시',
      audioDirection: '낮은 배경음과 확인 표시 효과음',
      transition: '확인 표시를 확대해 다음 컷으로 연결',
      continuity: ['공식 자료의 원문 의미를 바꾸지 않는다.'],
      aiVideoPromptEn: 'Vertical 9:16 editorial split comparison of an official announcement and verified music credits, matching entries receive a green check, white cards with navy borders, fixed front view, highly readable, no fabricated data.',
      negativeConstraints: ['임의 수치 금지', '자료 내용 왜곡 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'official-image',
        queries: [
          { language: 'ko', query: '신인 걸그룹 데뷔곡 공식 크레딧 발표' },
          { language: 'en', query: 'rookie girl group debut song official credits announcement' },
        ],
        selectionCriteria: ['공식 소속사 또는 음원 서비스 자료', '발표 문구가 선명한 이미지'],
        avoid: ['출처가 불명확한 재편집 카드', '팬 계정 캡처'],
        usage: {
          crop: '두 자료의 핵심 행이 보이는 9:16 상하 배치',
          motion: '각 자료를 3초씩 순차 강조',
          durationMs: 6000,
          overlay: '일치 항목에만 확인 표시',
          transition: '확인 표시 확대',
        },
      },
    },
    {
      sceneIndex: 1,
      shotIndex: 1,
      startOffsetMs: 6000,
      durationMs: 6000,
      visualDirectionKo: '음악 색깔, 멜로디, 가사 세 축을 간결한 연결 그래픽으로 보여준다.',
      subject: '음악적 정체성을 설명하는 세 개의 키워드 카드',
      setting: '세로 인포그래픽 화면',
      action: '세 카드가 순서대로 연결되고 중앙의 팀 색깔로 모인다.',
      composition: '위에서 아래로 흐르는 3단 구조',
      camera: '고정 화면',
      lighting: '평면 그래픽의 균일한 밝기',
      colorTexture: '남색, 흰색, 노란색의 단순한 벡터 질감',
      onScreenTextTreatment: '음악 색깔, 멜로디, 가사를 정확히 표시',
      audioDirection: '카드 등장마다 짧은 팝 효과음',
      transition: '중앙 카드가 확대되며 결론 장면으로 전환',
      continuity: ['앞선 비교 카드와 같은 글꼴과 포인트 색을 사용한다.'],
      aiVideoPromptEn: 'Vertical 9:16 clean motion infographic, three labeled concept cards for musical identity, melody, and lyrics connect into one central group identity card, navy white and yellow palette, fixed camera, crisp vector animation, no extra claims.',
      negativeConstraints: ['추가 수치 금지', '실제 인물 합성 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'programmatic-graphic',
        queries: [],
        selectionCriteria: ['세 개의 개념이 한눈에 구분되는 구조'],
        avoid: ['근거 없는 성과 그래프', '복잡한 배경 사진'],
        usage: {
          crop: '전체 9:16 그래픽',
          motion: '카드를 1.5초 간격으로 연결',
          durationMs: 6000,
          overlay: '검증된 세 키워드만 사용',
          transition: '중앙 카드 확대',
        },
      },
    },
    {
      sceneIndex: 2,
      shotIndex: 0,
      startOffsetMs: 0,
      durationMs: 5000,
      visualDirectionKo: '공식 무대 사진 옆에 확인할 크레딧 항목을 체크리스트로 보여준다.',
      subject: '공식 무대 사진과 크레딧 체크리스트',
      setting: '사진과 정보 카드가 결합된 세로 화면',
      action: '작사, 작곡, 편곡 항목이 순서대로 체크된다.',
      composition: '상단 사진, 하단 체크리스트',
      camera: '사진에 약한 패닝, 카드는 고정',
      lighting: '무대 사진은 원본 조명, 카드는 밝고 균일하게',
      colorTexture: '무대 색상과 남색 정보 카드의 대비',
      onScreenTextTreatment: '작사, 작곡, 편곡을 짧고 크게 표시',
      audioDirection: '결론 비트 상승과 세 번의 체크 효과음',
      transition: '체크리스트가 위로 밀리며 마지막 CTA 노출',
      continuity: ['동일한 공식 무대와 멤버 구성을 유지한다.'],
      aiVideoPromptEn: 'Vertical 9:16 editorial layout with an official stage photo above a clean credits checklist for lyrics, composition, and arrangement, subtle pan on the photo, fixed readable card, navy accents, no fabricated names.',
      negativeConstraints: ['임의 참여진 이름 금지', '얼굴 변경 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'official-image',
        queries: [
          { language: 'ko', query: '신인 걸그룹 공식 데뷔 무대 보도 사진' },
          { language: 'en', query: 'rookie girl group official debut stage press photo' },
        ],
        selectionCriteria: ['공식 또는 보도 출처', '상단 배치에 맞는 넓은 여백'],
        avoid: ['얼굴이 흐린 원거리 사진', '과도한 워터마크'],
        usage: {
          crop: '상단 60%에 무대 사진을 둔 9:16 크롭',
          motion: '사진을 5초 동안 좌우로 천천히 이동',
          durationMs: 5000,
          overlay: '하단 체크리스트 카드',
          transition: '체크리스트 위쪽 슬라이드',
        },
      },
    },
    {
      sceneIndex: 2,
      shotIndex: 1,
      startOffsetMs: 5000,
      durationMs: 5000,
      visualDirectionKo: '마지막 크레딧 확인 CTA를 단순한 타이포그래피 카드로 마무리한다.',
      subject: '크레딧 확인 CTA 문구',
      setting: '짙은 남색 세로 엔드 카드',
      action: 'CTA 문구와 작은 확인 아이콘이 차례로 나타난다.',
      composition: '중앙 정렬의 큰 문구와 하단 여백',
      camera: '고정',
      lighting: '평면 카드의 균일한 밝기',
      colorTexture: '남색 배경, 흰 글자, 노란 확인 아이콘',
      onScreenTextTreatment: '다음에는 크레딧까지를 중앙에 정확히 표시',
      audioDirection: '짧은 상승음 뒤 자연스럽게 종료',
      transition: '검은 화면으로 6프레임 페이드아웃',
      continuity: ['전체 영상과 같은 글꼴, 남색, 노란 포인트를 유지한다.'],
      aiVideoPromptEn: 'Vertical 9:16 minimal end card, centered call to check the credits next time, dark navy background, clean white typography, small yellow check icon, fixed camera, six-frame fade to black, no logos or watermarks.',
      negativeConstraints: ['임의 로고 금지', '추가 문구 금지'],
      imageSearchPlan: {
        recommendedSourceType: 'programmatic-graphic',
        queries: [],
        selectionCriteria: ['CTA가 한눈에 읽히는 단순한 레이아웃'],
        avoid: ['배경 사진', '작은 글자', '추가 로고'],
        usage: {
          crop: '전체 9:16 엔드 카드',
          motion: '문구와 확인 아이콘을 0.3초 간격으로 등장',
          durationMs: 5000,
          overlay: 'CTA 한 문장만 표시',
          transition: '검은 화면으로 6프레임 페이드아웃',
        },
      },
    },
  ],
};

function withShot(
  patch: Partial<StoryboardShotDirectionV1['shots'][number]>,
): StoryboardShotDirectionV1 {
  return {
    ...validShotDirection,
    shots: [
      { ...validShotDirection.shots[0], ...patch },
      ...validShotDirection.shots.slice(1),
    ],
  };
}
```

The public workflow endpoints become:

```text
GET  /projects/shortform-director/candidate-production/candidate-runs/:candidateRunId/candidates/:candidateId/preflight
POST /projects/shortform-director/candidate-production/runs
POST /projects/shortform-director/candidate-production/runs/:runId/resume
GET  /projects/shortform-director/candidate-production/runs/:runId/storyboard
GET  /projects/shortform-director/candidate-production/runs/:runId
GET  /projects/shortform-director/candidate-production/runs
GET  /projects/shortform-director/candidate-production/candidate-runs/:candidateRunId/candidates/:candidateId/storyboards
```

`GET .../runs/:runId/project` and `GET .../runs/:runId/result` are removed. The read adapter accesses stored result artifacts and the existing project repository internally; neither artifact IDs nor an old media-shaped project crosses the new public endpoint. New successful runs have no `projectId`.

---

### Task 1: Establish a Clean Cross-Repository Baseline

**Files:**
- Inspect: all six repository worktrees and their package manifests
- Protect: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html`
- Protect: `desktop/clipper_angular/src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts`

**Interfaces:**
- Consumes: the approved design and current `feat/storyboard` branches.
- Produces: a recorded baseline that every later task can compare against.

- [ ] **Step 1: Record branch and dirty-file state without changing it**

```bash
for repo in \
  web/clipper_web_api \
  desktop/clipper_nestjs \
  desktop/clipper_angular \
  desktop/clipper_electron \
  web/clipper_web_admin \
  desktop/clipper_python
do
  git -C "$repo" status --short --branch
done
```

Expected: every repository is on `feat/storyboard`; only the two protected Angular files may already be dirty.

- [ ] **Step 2: Capture the protected Angular diff for comparison**

```bash
git -C desktop/clipper_angular diff -- \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts
```

Expected: save the output in the executor transcript; the same diff must remain after Tasks 4, 5, and 12.

- [ ] **Step 3: Run narrow existing tests before changing contracts**

```bash
npm -C web/clipper_web_api test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
node --test desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
```

Expected: PASS, or record a pre-existing failure before proceeding. Do not alter product code to mask a baseline failure.

---

### Task 2: Replace Web API Inference Contracts and Prompts

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts`

**Interfaces:**
- Consumes: purpose IDs `video-plan` and `scene-media-decision`, the existing bounded inference transport, and grounded candidate input.
- Produces: `StoryboardEditorialPlanV1` and `StoryboardShotDirectionV1` with prompt versions `shortform-director.video-plan.v6` and `shortform-director.scene-media-decision.v9`.

- [ ] **Step 1: Replace contract fixtures with failing editorial-plan tests**

Add a valid fixture with `targetDurationMs: 30000`, three scenes of `8000`, `12000`, and `10000` milliseconds, exact narration, exact on-screen text, and well-formed evidence IDs. Assert the strict schema rejects seconds-based duration, extra properties, and a missing CTA scene. Evidence membership is request-dependent and is tested in Desktop Nest Task 3.

```ts
expect(INFERENCE_PURPOSE_SPECS['video-plan'].validateOutput(validEditorialPlan))
  .toEqual({ ok: true });
expect(INFERENCE_PURPOSE_SPECS['video-plan'].validateOutput({
  ...validEditorialPlan,
  targetDurationSeconds: 30,
})).toEqual(expect.objectContaining({ ok: false }));
expect(INFERENCE_PURPOSE_SPECS['video-plan'].validateOutput({
  ...validEditorialPlan,
  scenes: validEditorialPlan.scenes.filter(scene => scene.purpose !== 'cta'),
})).toEqual(expect.objectContaining({ ok: false }));
```

- [ ] **Step 2: Add failing shot-direction contract tests**

Use two shots in scene 0 and assert the parser rejects non-contiguous indexes, non-positive durations, non-English `aiVideoPromptEn`, more than three queries, a vague one-word query, and URLs. Assert a `programmatic-graphic` shot may use zero queries; when it does provide queries, the same 2–3 phrase rule applies.

```ts
expect(INFERENCE_PURPOSE_SPECS['scene-media-decision']
  .validateOutput(validShotDirection)).toEqual({ ok: true });
expect(INFERENCE_PURPOSE_SPECS['scene-media-decision'].validateOutput(
  withShot({
    imageSearchPlan: {
      ...validImageSearchPlan,
      queries: [{ language: 'ko', query: '걸그룹' }],
    },
  }),
)).toEqual(expect.objectContaining({ ok: false }));
```

- [ ] **Step 3: Run the contract tests and confirm the old schemas fail**

```bash
npm -C web/clipper_web_api test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts
```

Expected: FAIL because the current parser still expects `VIDEO_PLAN_SCHEMA` and `SCENE_MEDIA_DECISION_SCHEMA` media-decision fields.

- [ ] **Step 4: Implement strict editorial and shot-direction schemas**

Replace the two schema constants and their manual validation branches. Keep `additionalProperties: false` at every object level. The shot parser must enforce:

```ts
const ALLOWED_SOURCE_TYPES = new Set([
  'official-image',
  'editorial-photo',
  'licensed-stock',
  'user-provided',
  'programmatic-graphic',
]);

function assertImageSearchPlan(plan: StoryboardImageSearchPlanV1): void {
  if (!ALLOWED_SOURCE_TYPES.has(plan.recommendedSourceType)) {
    throw new InferenceContractError('Invalid recommended source type');
  }
  if (plan.queries.length > 3) {
    throw new InferenceContractError('Image search queries must not exceed 3');
  }
  if (plan.queries.length === 1) {
    throw new InferenceContractError('Image search requires 2-3 phrases');
  }
  if (
    plan.recommendedSourceType !== 'programmatic-graphic'
    && plan.queries.length === 0
  ) {
    throw new InferenceContractError('Image search requires 2-3 phrases');
  }
  if (plan.queries.some(({ query }) =>
    query.trim().split(/\s+/u).length < 2 || /^https?:\/\//iu.test(query))) {
    throw new InferenceContractError('Each query must be a usable search phrase');
  }
}
```

The Web API validator checks response shape and local field rules only. Cross-stage timing, evidence membership, narration density, and continuity are enforced in Desktop Nest Task 3.

- [ ] **Step 5: Write failing prompt tests for the new product boundary**

Assert exact prompt clauses for: Korean narration and visual direction, English model-neutral prompts, exact on-screen copy, evidence-only facts, 2–3 search phrases, rights disclaimer semantics, and no provider/model/media-job directives. Also assert the version strings.

```ts
expect(prompt.promptTemplateVersion)
  .toBe('shortform-director.scene-media-decision.v9');
expect(prompt.systemPrompt).toContain('Do not add facts not present in evidence');
expect(prompt.systemPrompt).toContain('2 to 3 concrete image search phrases');
expect(prompt.systemPrompt).not.toMatch(/Seedance|Veo|Nano Banana|render job/i);
expect(editorialPrompt.systemPrompt).toContain('hook exactly once');
expect(editorialPrompt.systemPrompt).toContain(
  'Narration contains only words the viewer should hear',
);
```

- [ ] **Step 6: Implement the two prompts**

The first prompt returns editorial structure only. The second receives the validated first response and uses this non-negotiable boundary:

```ts
const EDITORIAL_PLAN_RULES = `
Use the selected candidate hook exactly once, as the opening narration.
Keep the candidate promise, core message, and CTA grounded in supplied evidence.
Narration contains only words the viewer should hear; never put camera,
editing, sound, or visual instructions in narration.
Return exact Korean on-screen copy and evidence IDs for every scene.
Do not add a person, organization, event, date, number, or factual claim that
is absent from the supplied grounded context.
`;

const SHOT_DIRECTION_RULES = `
Return shot-production directions, not media jobs or provider settings.
Write visualDirectionKo and all production directions in Korean.
Write aiVideoPromptEn as a self-contained, model-neutral English prompt.
Do not translate by adding or removing factual claims.
Copy narration and on-screen wording exactly from the editorial plan.
For each non-programmatic shot provide 2 to 3 concrete Korean or English
image-search phrases plus selection criteria, avoid rules, crop, motion,
duration, overlay, and transition instructions.
Search phrases are discovery guidance and must never claim usage rights.
Do not return URLs, asset IDs, storage paths, provider names, model names,
generation parameters, or job instructions.
`;
```

- [ ] **Step 7: Run Web API inference tests**

```bash
npm -C web/clipper_web_api test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts
```

Expected: PASS; model catalog tests still prove both retained purposes resolve to GPT-5.6 Luna.

- [ ] **Step 8: Commit the inference contract**

```bash
git -C web/clipper_web_api add \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts \
  src/modules/shortform-director-inference/application/shortform-director-inference.service.spec.ts
git -C web/clipper_web_api commit -m "feat: generate storyboard document contracts"
```

---

### Task 3: Add Desktop Nest Storyboard Domain, Validation, and Assembly

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/domain/storyboard-document.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard.validator.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard.assembler.ts`
- Create: `desktop/clipper_nestjs/test/shortform-director-storyboard-validator.test.js`
- Create: `desktop/clipper_nestjs/test/shortform-director-storyboard-assembler.test.js`

**Interfaces:**
- Consumes: the exact `StoryboardEditorialPlanV1` and `StoryboardShotDirectionV1` shapes from Task 2.
- Produces: `parseStoryboardEditorialPlan`, `parseStoryboardShotDirection`, `validateStoryboardStages`, and `ShortformDirectorStoryboardAssembler.assemble(input): StoryboardDocumentV1`.

- [ ] **Step 1: Write domain parser tests before creating the domain file**

Cover exact keys, non-empty strings, unique evidence IDs, contiguous scene/shot indexes, the fixed scene-purpose union, integer millisecond timing, source-type membership, nullable-free current documents, and rejection of internal IDs or URLs inside human-facing prompt/search fields.

```js
assert.throws(
  () => parseStoryboardShotDirection({
    ...validShots,
    shots: [{ ...validShots.shots[0], shotIndex: 2 }],
  }),
  /contiguous/i,
);
assert.throws(
  () => parseStoryboardShotDirection(withPrompt('asset.director.secret')),
  /internal identifier/i,
);
```

- [ ] **Step 2: Run parser tests and verify the module is missing**

```bash
node --test desktop/clipper_nestjs/test/shortform-director-storyboard-validator.test.js
```

Expected: FAIL with module-not-found for `storyboard-document` or `shortform-director-storyboard.validator`.

- [ ] **Step 3: Implement focused domain types and strict parsers**

Define `StoryboardOverviewV1`, `StoryboardSceneV1`, `StoryboardShotV1`, `StoryboardImageSearchPlanV1`, `StoryboardDocumentV1`, and `StoryboardViewV1` in `storyboard-document.ts`. Export parsers with these signatures:

```ts
export function parseStoryboardEditorialPlan(
  value: unknown,
): StoryboardEditorialPlanV1;

export function parseStoryboardShotDirection(
  value: unknown,
): StoryboardShotDirectionV1;

export function parseStoryboardDocument(
  value: unknown,
): StoryboardDocumentV1;
```

Use the repository's existing `expectRecord`/strict-own-data style rather than accepting TypeScript casts.

- [ ] **Step 4: Write failing cross-stage validator tests**

Tests must reject: scene totals not equal to target, shot totals not equal to their scene, gaps/overlaps, missing opening hook, missing CTA, evidence outside the allowed set, spoken Korean text outside a plausible `2.5–6.5` syllables-per-second range, repeated adjacent visual direction, contradictory continuity/negative rules, and search `usage.durationMs` different from its shot duration.

```js
assert.deepEqual(validateStoryboardStages({
  editorialPlan: validEditorialPlan,
  shotDirection: validShotDirection,
  candidateHook: validEditorialPlan.scenes[0].narration,
  allowedEvidenceIds: new Set(['evidence.1', 'evidence.2']),
  groundingTextByEvidenceId: new Map([
    ['evidence.1', '아워벌스데이 데뷔 쇼케이스와 공식 발표'],
    ['evidence.2', '2026년 신인 걸그룹 제작 참여 정보'],
  ]),
}), { valid: true, issues: [] });

assert.match(
  validateStoryboardStages({
    editorialPlan: validEditorialPlan,
    shotDirection: withUnknownEvidence('evidence.99'),
    candidateHook: validEditorialPlan.scenes[0].narration,
    allowedEvidenceIds: new Set(['evidence.1']),
    groundingTextByEvidenceId: new Map([
      ['evidence.1', '아워벌스데이 데뷔 쇼케이스와 공식 발표'],
    ]),
  }).issues[0].code,
  /UNKNOWN_EVIDENCE/,
);
```

- [ ] **Step 5: Implement deterministic validation without creative repair**

Return all issues so retry prompts can state exactly what failed:

```ts
export interface StoryboardValidationIssueV1 {
  code:
    | 'TARGET_DURATION_MISMATCH'
    | 'SCENE_DURATION_MISMATCH'
    | 'TIMELINE_NOT_CONTIGUOUS'
    | 'OPENING_HOOK_MISSING'
    | 'CTA_MISSING'
    | 'NARRATION_DENSITY_OUT_OF_RANGE'
    | 'UNKNOWN_EVIDENCE'
    | 'SHOT_NOT_SPECIFIC'
    | 'ADJACENT_SHOT_DUPLICATE'
    | 'CONSTRAINT_CONFLICT'
    | 'SEARCH_PLAN_INVALID';
  path: string;
  message: string;
}

export function validateStoryboardStages(input: {
  editorialPlan: StoryboardEditorialPlanV1;
  shotDirection: StoryboardShotDirectionV1;
  candidateHook: string;
  allowedEvidenceIds: ReadonlySet<string>;
  groundingTextByEvidenceId: ReadonlyMap<string, string>;
}): { valid: boolean; issues: StoryboardValidationIssueV1[] };
```

Normalize dates, numbers, quoted names, and uppercase Latin proper nouns from scene claims and on-screen text; require them in the text mapped by that scene's evidence IDs. Apply the same factual-token check to shot directions and English prompts against the validated editorial plan plus its evidence corpus, excluding a fixed camera/lighting/composition vocabulary. Also require normalized `candidateHook` exactly once in the first scene's narration and nowhere else. This guard complements the prompt and evidence-ID checks without attempting to rewrite model output.

- [ ] **Step 6: Write failing assembler tests**

Assert stable absolute offsets, shot nesting by `sceneIndex`, `aspectRatio: '9:16'`, immutable snapshots, and no document produced when validation has issues.

```js
assert.equal(document.scenes[1].startMs, 8000);
assert.equal(document.scenes[1].shots[0].startMs, 8000);
assert.equal(document.scenes[1].shots[1].startMs, 14000);
assert.equal(document.aspectRatio, '9:16');
```

- [ ] **Step 7: Implement the assembler**

```ts
assemble(input: {
  documentId: string;
  runId: string;
  profileId: string;
  researchRunId: string;
  topicId: string;
  candidateRunId: string;
  candidateId: string;
  editorialPlan: StoryboardEditorialPlanV1;
  shotDirection: StoryboardShotDirectionV1;
  candidateHook: string;
  allowedEvidenceIds: ReadonlySet<string>;
  groundingTextByEvidenceId: ReadonlyMap<string, string>;
  createdAt: string;
}): StoryboardDocumentV1
```

Compute `scene.startMs` from preceding scene durations and `shot.startMs` from the scene start plus `startOffsetMs`. Deep-copy arrays; never mutate inference output.

- [ ] **Step 8: Run domain tests and commit**

```bash
node --test \
  desktop/clipper_nestjs/test/shortform-director-storyboard-validator.test.js \
  desktop/clipper_nestjs/test/shortform-director-storyboard-assembler.test.js
git -C desktop/clipper_nestjs add \
  src/modules/shortform-director/domain/storyboard-document.ts \
  src/modules/shortform-director/application/shortform-director-storyboard.validator.ts \
  src/modules/shortform-director/application/shortform-director-storyboard.assembler.ts \
  test/shortform-director-storyboard-validator.test.js \
  test/shortform-director-storyboard-assembler.test.js
git -C desktop/clipper_nestjs commit -m "feat: validate and assemble storyboard documents"
```

---

### Task 4: Rebuild Desktop Nest Generation Around Artifacts and Resume Checkpoints

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard-read.adapter.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-run-recovery.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/run-record.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-candidate-production.dto.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-candidate-production.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
- Create: `desktop/clipper_nestjs/test/shortform-director-candidate-production-controller.test.js`
- Create: `desktop/clipper_nestjs/test/shortform-director-run-recovery.test.js`
- Create: `desktop/clipper_nestjs/test/shortform-director-storyboard-read-adapter.test.js`

**Interfaces:**
- Consumes: validator/assembler from Task 3, candidate prepared context, inference client, artifact registry, run repository, and earlier project repository for reads only.
- Produces: two-stage artifact workflow, `resume(runId, auth)`, `storyboard(runId, auth): StoryboardViewV1`, history without model/mode, and a maximum call count of three.

- [ ] **Step 1: Write failing preflight and DTO tests**

Assert `maxCalls: 3`, model remains internal, the approval snapshot contains no production config or video model, the start DTO accepts only candidate IDs plus approval confirmation, and query `model`, `mode`, or `kind` no longer changes preflight.

```ts
expect(preflight).toMatchObject({
  approvalVersion: 'storyboard-document-cost-2026-08-24.v1',
  model: 'gpt-5.6-luna',
  normalCalls: 2,
  maxCalls: 3,
  estimatedCostUsd: {
    currency: 'USD',
    minimum: 0.02,
    maximum: 0.45,
  },
});
expect(preflight).not.toHaveProperty('productionConfig');
expect(preflight).not.toHaveProperty('videoModel');
```

- [ ] **Step 2: Implement the preflight contract**

Change the approval version to `storyboard-document-cost-2026-08-24.v1`, remove generated-media imports and arguments, and hash this exact snapshot:

```ts
const approvalSnapshot = {
  schemaVersion: 'shortform-director-storyboard-approval-snapshot.v1',
  approvalVersion: SHORTFORM_DIRECTOR_CANDIDATE_PRODUCTION_APPROVAL_VERSION,
  candidateRunId,
  candidateId,
  researchRunId: researchRun.id,
  profileId: researchRun.profileId,
  topicId: topic.id,
  provider: 'openai',
  credentialId,
  credentialRevision,
  model: 'gpt-5.6-luna',
  normalCalls: 2,
  maxCalls: 3,
  estimatedCostUsd: { currency: 'USD', minimum: 0.02, maximum: 0.45 },
} as const;
```

- [ ] **Step 3: Write failing orchestration tests for normal and recovered runs**

Verify the normal call order is `video-plan`, then `scene-media-decision`; pass 1 is attached before pass 2 begins; the completed document and result are attached only after both pass validation; a pass-2 contract failure retries only pass 2; and total calls never exceed three.

```js
assert.deepEqual(inferencePurposes, ['video-plan', 'scene-media-decision']);
assert.equal(savedRun.projectId, undefined);
assert.equal(result.schemaVersion, 'shortform-director-storyboard-result.v1');
assert.equal(storyboardArtifact.value.schemaVersion, 'storyboard-document.v1');
assert.equal((await service.storyboard(savedRun.id, ownerAuth)).format, 'current');

assert.deepEqual(recoveredPurposes, [
  'video-plan',
  'scene-media-decision',
  'scene-media-decision',
]);
assert.equal(recoveredPurposes.filter(value => value === 'video-plan').length, 1);
```

- [ ] **Step 4: Define and persist the checkpoint and result contracts**

Publish the input artifact before inference, then publish a new immutable checkpoint after each paid call. The loader selects the newest valid checkpoint attached to the run:

```ts
interface StoryboardGenerationCheckpointV1 {
  schemaVersion: 'storyboard-generation-checkpoint.v1';
  runId: string;
  completedStage: 'input' | 'editorial-plan' | 'shot-direction';
  providerCallCount: 0 | 1 | 2 | 3;
  editorialPlanArtifactId: string | null;
  shotDirectionArtifactId: string | null;
  lastUpdatedAt: string;
}

interface StoryboardRunContext {
  run: LocalRunManifestV1;
  ownerSubjectId: string;
  bearerToken: string;
  prepared: PreparedShortformDirectorCandidateProduction;
  inputArtifactId: string;
  approvalArtifactId: string;
}

interface StoredShortformDirectorStoryboardResultV1 {
  schemaVersion: 'shortform-director-storyboard-result.v1';
  runId: string;
  storyboardId: string;
  candidateRunId: string;
  candidateId: string;
  researchRunId: string;
  topicId: string;
  inferenceArtifactIds: string[];
  storyboardArtifactId: string;
}
```

Artifact kinds are `candidate-storyboard-input`, `storyboard-editorial-plan`, `storyboard-shot-direction`, `storyboard-generation-checkpoint`, `candidate-storyboard-document`, and `candidate-storyboard-result`.

- [ ] **Step 5: Implement one shared call-budget executor**

Replace the project mapper/compiler path with stage methods. The only retryable failures are transient provider errors and explicit contract/validator errors; authentication, authorization, lineage, approval, and missing-evidence errors fail immediately.

```ts
private async runMissingStages(context: StoryboardRunContext): Promise<void> {
  let checkpoint = await this.loadCheckpoint(context.run.id);
  if (checkpoint.editorialPlanArtifactId === null) {
    checkpoint = await this.runStageWithSingleRecovery(
      context,
      checkpoint,
      'video-plan',
    );
  }
  if (checkpoint.shotDirectionArtifactId === null) {
    checkpoint = await this.runStageWithSingleRecovery(
      context,
      checkpoint,
      'scene-media-decision',
    );
  }
  await this.assembleAndCommit(context, checkpoint);
}

private async runStageWithSingleRecovery(
  context: StoryboardRunContext,
  checkpoint: StoryboardGenerationCheckpointV1,
  purpose: 'video-plan' | 'scene-media-decision',
): Promise<StoryboardGenerationCheckpointV1>;
```

`runStageWithSingleRecovery` checks `providerCallCount < 3` before every call and permits only one retry across the entire run. Retry input contains validation issue codes and paths, never raw provider diagnostics.

- [ ] **Step 6: Write failing restart-recovery tests**

Cover a process interruption with no successful pass, with pass 1 saved, and with both passes saved but no final document. Expected statuses are failure for an unusable checkpoint and `awaiting_storyboard_resume` for a usable one.

```js
assert.equal(afterRecovery.status, 'awaiting_storyboard_resume');
await service.resume(afterRecovery.id, ownerAuth);
assert.deepEqual(inferencePurposes, ['scene-media-decision']);
```

- [ ] **Step 7: Implement resumable run state**

Add `'awaiting_storyboard_resume'` to `LocalRunActiveStatus`. Change `requiresProject()` so `video-plan` no longer requires `projectId`; existing records that contain it still parse. On startup, the recovery service validates owned checkpoint refs before choosing resumable state. `POST runs/:runId/resume` takes no new approval or generation options: it reuses the persisted, already-confirmed approval snapshot and input artifact, authorizes the owner, and runs only missing stages.

- [ ] **Step 8: Write and implement the earlier-result read adapter**

Current artifacts return `format: 'current'`. Earlier projects return `format: 'earlier'`, `overview: null`, and `null` for fields never generated:

```ts
return {
  schemaVersion: 'shortform-director-storyboard-view.v1',
  format: 'earlier',
  id: project.id,
  title: project.title,
  targetDurationMs: project.videoPlan.durationMs,
  aspectRatio: '9:16',
  overview: null,
  scenes: project.videoPlan.scenes.map(scene => ({
    sceneIndex: scene.order,
    startMs: scene.startMs,
    durationMs: scene.durationMs,
    purpose: mapEarlierPurpose(scene.purpose),
    intent: scene.intent,
    narration: narrationForScene(project.videoPlan, scene),
    onScreenText: textLayersForScene(scene).map(layer => layer.content),
    claim: null,
    evidenceIds: uniqueEvidenceIds(scene.beats),
    shots: scene.beats.flatMap(beat => beat.shots).map((shot, shotIndex) => ({
      shotIndex,
      startMs: shot.startMs,
      durationMs: shot.durationMs,
      visualDirectionKo: shot.intent,
      subject: null,
      setting: null,
      action: null,
      composition: null,
      camera: null,
      lighting: null,
      colorTexture: null,
      onScreenTextTreatment: null,
      audioDirection: null,
      transition: null,
      continuity: null,
      aiVideoPromptEn: null,
      negativeConstraints: null,
      imageSearchPlan: null,
    })),
  })),
};
```

`mapEarlierPurpose` maps `value` to `development` and `proof` to `evidence`; existing `hook`, `context`, and `cta` values remain unchanged. `narrationForScene` follows beat `narrationCueId` references into `audioTimeline.narrationCues`, and `textLayersForScene` reads only text-kind layers. The adapter does not write the project or turn removed controls back on.

- [ ] **Step 9: Update controller and history responses**

Remove production-config query parsing and request-body mapping, and remove `GET runs/:runId/project` plus `GET runs/:runId/result`. Add `POST runs/:runId/resume` and `GET runs/:runId/storyboard`. History items contain `format`, `resumable`, `title`, duration and counts, but not `model` or `mode`.

```ts
export interface ShortformDirectorStoryboardHistoryItemV1 {
  runId: string;
  status: 'running' | 'awaiting_storyboard_resume' | 'partial'
    | 'succeeded' | 'failed' | 'cancelled';
  format: 'current' | 'earlier';
  resumable: boolean;
  startedAt: string;
  finishedAt?: string;
  title: string | null;
  durationMs: number | null;
  sceneCount: number | null;
  shotCount: number | null;
  canOpen: boolean;
  failureCode?: string;
  failureStage?: string;
}
```

- [ ] **Step 10: Run Nest workflow tests**

```bash
node --test \
  desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js \
  desktop/clipper_nestjs/test/shortform-director-candidate-production-controller.test.js \
  desktop/clipper_nestjs/test/shortform-director-run-recovery.test.js \
  desktop/clipper_nestjs/test/shortform-director-storyboard-read-adapter.test.js
```

Expected: PASS, with explicit assertions for 2-call normal flow, 3-call ceiling, pass-2-only resume, atomic result visibility, owner authorization, and earlier-format null fields.

- [ ] **Step 11: Commit the artifact workflow**

```bash
git -C desktop/clipper_nestjs add \
  src/modules/shortform-director/application/shortform-director-candidate-production-preflight.service.ts \
  src/modules/shortform-director/application/shortform-director-candidate-production.service.ts \
  src/modules/shortform-director/application/shortform-director-storyboard-read.adapter.ts \
  src/modules/shortform-director/application/shortform-director-run-recovery.service.ts \
  src/modules/shortform-director/domain/run-record.ts \
  src/modules/shortform-director/presentation/dto/start-shortform-director-candidate-production.dto.ts \
  src/modules/shortform-director/presentation/shortform-director-candidate-production.controller.ts \
  src/modules/shortform-director/shortform-director.module.ts \
  test/shortform-director-candidate-production.test.js \
  test/shortform-director-candidate-production-controller.test.js \
  test/shortform-director-run-recovery.test.js \
  test/shortform-director-storyboard-read-adapter.test.js
git -C desktop/clipper_nestjs commit -m "feat: persist resumable storyboard documents"
```

---

### Task 5: Add Angular Storyboard Contracts and Clipboard Documents

**Files:**
- Create: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-storyboard.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-storyboard.spec.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/services/storyboard-clipboard.service.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/services/storyboard-clipboard.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`

**Interfaces:**
- Consumes: public preflight, run, history, and `StoryboardViewV1` contracts from Task 4.
- Produces: Angular `StoryboardViewV1` types, current/earlier fixtures, and deterministic formatter/copy methods. This task is additive so the existing page still builds until Task 6 switches the gateway and state atomically.

- [ ] **Step 1: Write failing model contract tests**

Assert the preflight has `normalCalls: 2` and `maxCalls: 3`; history has `format` and `resumable` but no model/mode; current views require complete shot fields; earlier views require `overview: null` and permit unavailable detailed fields.

```ts
expect(storyboardPreflight).toEqual(expect.objectContaining({
  normalCalls: 2,
  maxCalls: 3,
}));
expect(currentStoryboard.format).toBe('current');
expect(earlierStoryboard).toEqual(expect.objectContaining({
  format: 'earlier',
  overview: null,
}));
expect(storyboardHistory.items[0]).not.toHaveProperty('model');
expect(storyboardHistory.items[0]).not.toHaveProperty('mode');
```

- [ ] **Step 2: Implement the Angular types and canonical fixtures**

Mirror the discriminated `CurrentStoryboardViewV1 | EarlierStoryboardViewV1` contract from the file map. Add `storyboardPreflight`, `currentStoryboard`, `earlierStoryboard`, and `storyboardHistory` to the fixture file without deleting old exports yet; Task 6 removes the old consumers and exports in one buildable change.

- [ ] **Step 3: Write failing clipboard formatter tests**

Assert Korean whole-document section order, English master-prompt shot order, exact per-shot content, newline-separated query output, a rights reminder, and exclusion of values matching `run.director.`, `artifact.`, `credential`, `/Users/`, and provider diagnostic keys. Assert earlier-format unavailable text returns `null` and `copy(null)` returns `{ copied: false, reason: 'unavailable' }`.

```ts
expect(service.wholeStoryboard(currentStoryboard)).toContain('# 스토리보드');
expect(service.externalAiPrompt(currentStoryboard))
  .toContain('Vertical 9:16 short-form video');
expect(service.externalAiPrompt(currentStoryboard))
  .not.toContain(currentStoryboard.id);
expect(service.searchQueries(currentStoryboard.scenes[0].shots[0])).toBe(
  '신인 걸그룹 공식 데뷔 쇼케이스 사진\n'
  + 'rookie girl group official debut showcase photo',
);
expect(service.aiPrompt(earlierStoryboard.scenes[0].shots[0])).toBeNull();
await expectAsync(service.copy(null)).toBeResolvedTo({
  copied: false,
  reason: 'unavailable',
});
```

- [ ] **Step 4: Implement deterministic clipboard documents**

The service first formats pure strings, then writes through `navigator.clipboard.writeText`. Whole-document Markdown uses these fixed sections: title/metadata, production overview, global continuity and constraints, ordered scenes, ordered shots, image-search guidance, and the rights reminder. The English master prompt contains global direction followed by numbered shot prompts and negative constraints; it does not translate Korean facts itself.

```ts
export type ClipboardResult =
  | { copied: true }
  | { copied: false; reason: 'unavailable' | 'clipboard-failed' };

export class StoryboardClipboardService {
  wholeStoryboard(view: StoryboardViewV1): string;
  externalAiPrompt(view: StoryboardViewV1): string | null;
  shotContent(scene: StoryboardSceneViewV1, shot: StoryboardShotViewV1): string;
  aiPrompt(shot: StoryboardShotViewV1): string | null;
  searchQueries(shot: StoryboardShotViewV1): string | null;
  copy(text: string | null): Promise<ClipboardResult>;
}
```

- [ ] **Step 5: Run the additive model/clipboard tests and commit**

```bash
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/models/shortform-director-storyboard.spec.ts' \
  --include='src/features/shortform-director/services/storyboard-clipboard.service.spec.ts'
npm -C desktop/clipper_angular run build:electron
git -C desktop/clipper_angular add \
  src/features/shortform-director/models/shortform-director-storyboard.ts \
  src/features/shortform-director/models/shortform-director-storyboard.spec.ts \
  src/features/shortform-director/services/storyboard-clipboard.service.ts \
  src/features/shortform-director/services/storyboard-clipboard.service.spec.ts \
  src/features/shortform-director/testing/shortform-director-production.fixtures.ts
git -C desktop/clipper_angular commit -m "feat: define copyable storyboard documents"
```

---

### Task 6: Build the Korean-First Read-Only Storyboard Page

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-preflight-card/production-preflight-card.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-preflight-card/production-preflight-card.component.html`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/production-preflight-card/production-preflight-card.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/routing/shortform-director-context.guards.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/routing/shortform-director-context.guards.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/shortform-director-routing.integration.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`
- Delete: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Delete: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.spec.ts`
- Delete: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-project.ts`
- Delete: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/`
- Delete: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/`
- Delete: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-shot-status-list/`
- Delete: `desktop/clipper_angular/src/features/shortform-director/components/sequence-card-preview/`

**Interfaces:**
- Consumes: Task 5 models and clipboard service plus Task 4 HTTP contracts.
- Produces: one generation action, overview/timeline/shot presentation, five copy actions, earlier-format disclosure, history, and retry UX.

- [ ] **Step 1: Write failing gateway and store tests**

Assert start body has no `productionConfig`; preflight URL has no model/mode query; storyboard reads `/runs/:runId/storyboard`; resume posts `{}`. Verify polling a succeeded run loads `getStoryboard`, `awaiting_storyboard_resume` posts resume only once, and a failed new run keeps the previously opened storyboard.

```ts
expect(req.request.url).not.toContain('model=');
expect(req.request.url).not.toContain('mode=');
expect(req.request.body).toEqual({
  candidateRunId,
  candidateId,
  approvalVersion,
  approvalId,
  confirmed: true,
});
expect(store.storyboard()).toEqual(previousStoryboard);
expect(store.error()).toEqual({
  message: '스토리보드를 완성하지 못했습니다. 다시 시도해 주세요.',
  retryable: true,
});
```

- [ ] **Step 2: Implement the narrow gateway and reduced store**

```ts
export interface ShortformDirectorProductionGateway {
  listRuns(profileId: string): Promise<ShortformDirectorProductionRunV1[]>;
  getStoryboardHistory(
    candidateRunId: string,
    candidateId: string,
  ): Promise<ShortformDirectorStoryboardHistoryV1>;
  getPreflight(
    candidateRunId: string,
    candidateId: string,
  ): Promise<ShortformDirectorProductionPreflightV1>;
  startProduction(
    candidateRunId: string,
    candidateId: string,
    approvalVersion: string,
    approvalId: string,
  ): Promise<ShortformDirectorProductionRunV1>;
  resume(runId: string): Promise<ShortformDirectorProductionRunV1>;
  getRun(runId: string): Promise<ShortformDirectorProductionRunV1>;
  getStoryboard(runId: string): Promise<StoryboardViewV1>;
}
```

Delete project, narration, generated-video, render, and download methods. Keep candidate context, preflight, active run, history, storyboard, progress, and retryable error. Make resume idempotent per run ID so polling cannot post it concurrently. Do not add a client-side inference or creative repair path.

- [ ] **Step 3: Run gateway/store tests and verify they pass**

```bash
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/services/shortform-director-production.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: PASS with no media-production request or state field.

- [ ] **Step 4: Write failing page and component tests**

Assert visible copy and controls:

```ts
expect(text()).toContain('스토리보드 만들기');
expect(text()).toContain('일반적으로 AI 호출 2회');
expect(text()).toContain('복구 시 최대 3회');
expect(text()).toContain('전체 스토리보드 복사');
expect(text()).toContain('외부 AI용 프롬프트 복사');
expect(text()).toContain('출처와 사용 권한을 직접 확인해 주세요');
expect(text()).not.toMatch(/영상 모델|제작 모드|음성 합성|영상 생성|최종 렌더|완성 영상/);
```

For an earlier-format fixture, assert the page says `이전 형식의 스토리보드` and omits English prompt/search copy buttons. For clipboard rejection, assert `복사하지 못했습니다. 다시 시도해 주세요.` without clearing the storyboard.

- [ ] **Step 5: Remove setup and media components from the page**

Delete their imports, template elements, event handlers, scrolling targets, store selectors, and old fixture exports before deleting the four component directories and three old model files. Update the routing integration fake gateway to the Task 5 interface. Keep the existing route path `/shortform/director/storyboard`; an internal folder rename is intentionally omitted from this scope.

- [ ] **Step 6: Implement the production overview and shot cards**

The result hierarchy is:

```html
@if (storyboard.overview; as overview) {
  <section class="storyboard-overview">
    <h2>제작 개요</h2>
    <dl>
      <dt>핵심 메시지</dt><dd>{{ overview.coreMessage }}</dd>
      <dt>시청자</dt><dd>{{ overview.audience }}</dd>
      <dt>형식</dt><dd>{{ overview.format }}</dd>
      <dt>톤</dt><dd>{{ overview.tone }}</dd>
      <dt>호흡</dt><dd>{{ overview.pacing }}</dd>
      <dt>전개</dt><dd>{{ overview.storyArc }}</dd>
    </dl>
  </section>
}
<app-storyboard-scene-list
  [storyboard]="storyboard"
  (copyShot)="copyShot($event)"
  (copyAiPrompt)="copyAiPrompt($event)"
  (copySearchQueries)="copySearchQueries($event)" />
```

Each scene shows absolute time, purpose, intent, exact narration, exact on-screen text, claim, and evidence count. Each shot shows Korean direction, subject/setting/action, composition/camera/light/color, audio, transition, continuity, negative constraints, English prompt, and image-source/query/selection/avoid/usage guidance.

- [ ] **Step 7: Wire copy success/failure feedback accessibly**

Use one `aria-live="polite"` status region. Successful labels are `전체 스토리보드를 복사했습니다.`, `외부 AI용 프롬프트를 복사했습니다.`, `컷 내용을 복사했습니다.`, `AI 프롬프트를 복사했습니다.`, and `검색어를 복사했습니다.`. Failure is retryable and never navigates or clears state.

- [ ] **Step 8: Simplify history and route context**

History rows show title, created time, duration, scene/shot count, status, and earlier/current badge. Remove model and mode. Remove `projectId`, `storyboardRevisionId`, and `finalRenderId` query-context validation; keep profile, research, topic, candidate-run, candidate, and run context.

- [ ] **Step 9: Run component tests**

```bash
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/components/production-preflight-card/production-preflight-card.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.spec.ts' \
  --include='src/features/shortform-director/routing/shortform-director-context.guards.spec.ts' \
  --include='src/features/shortform-director/shortform-director-routing.integration.spec.ts'
npm -C desktop/clipper_angular run build:electron
```

Expected: tests and build pass with no media-production element or method in the component fixtures.

- [ ] **Step 10: Verify protected diffs and commit the complete UI migration**

```bash
git -C desktop/clipper_angular diff -- \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts
git -C desktop/clipper_angular add \
  src/features/shortform-director/services/shortform-director-production.gateway.ts \
  src/features/shortform-director/services/shortform-director-production.service.ts \
  src/features/shortform-director/services/shortform-director-production.service.spec.ts \
  src/features/shortform-director/state/shortform-director-production.store.ts \
  src/features/shortform-director/state/shortform-director-production.store.spec.ts \
  src/features/shortform-director/pages/production-page \
  src/features/shortform-director/components/production-preflight-card \
  src/features/shortform-director/components/storyboard-scene-list \
  src/features/shortform-director/components/storyboard-history-menu \
  src/features/shortform-director/components/production-setup-card \
  src/features/shortform-director/components/ai-video-production-card \
  src/features/shortform-director/components/ai-video-shot-status-list \
  src/features/shortform-director/components/sequence-card-preview \
  src/features/shortform-director/models/shortform-director-production.ts \
  src/features/shortform-director/models/shortform-director-production.spec.ts \
  src/features/shortform-director/models/shortform-director-project.ts \
  src/features/shortform-director/shortform-director-routing.integration.spec.ts \
  src/features/shortform-director/testing/shortform-director-production.fixtures.ts \
  src/features/shortform-director/routing/shortform-director-context.guards.ts \
  src/features/shortform-director/routing/shortform-director-context.guards.spec.ts
git -C desktop/clipper_angular commit -m "feat: present read-only storyboard documents"
```

Expected: the protected diff is byte-for-byte the baseline and neither protected file appears in `git diff --cached --name-only`.

---

### Task 7: Remove Web API Media Generation and Active Job Tables

**Files:**
- Delete: `web/clipper_web_api/src/modules/shortform-director-image-generation/`
- Delete: `web/clipper_web_api/src/modules/shortform-director-video-generation/`
- Delete: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
- Delete: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_api/src/app.module.spec.ts`
- Modify: `web/clipper_web_api/src/core/database/user.datasource.ts`
- Modify: `web/clipper_web_api/src/core/database/user.datasource.spec.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/user/1787800000000-DropShortformDirectorGeneratedMediaJobs.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/user/1787800000000-DropShortformDirectorGeneratedMediaJobs.spec.ts`
- Modify: `web/clipper_web_api/src/modules/provider-credentials/provider-credentials.module.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/application/api-keys.service.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/application/api-keys.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.controller.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.controller.spec.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/presentation/api-keys.openapi.spec.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/presentation/dto/create-api-key.dto.ts`
- Modify: `web/clipper_web_api/src/modules/api-keys/presentation/dto/create-api-key.dto.spec.ts`
- Modify: `web/clipper_web_api/src/modules/provider-credentials/domain/provider-credential.model.ts`
- Delete: `web/clipper_web_api/src/modules/provider-credentials/application/fal-credential.service.ts`
- Delete: `web/clipper_web_api/src/modules/provider-credentials/application/fal-credential.service.spec.ts`

**Interfaces:**
- Consumes: Task 2 inference module, which no longer imports generated-media capabilities.
- Produces: no active image/video generation routes or entities; an idempotent forward migration; retained Naver/OpenAI/Gemini/YouTube credential paths.

- [ ] **Step 1: Write failing application-boundary tests**

Update `app.module.spec.ts` to assert `ShortformDirectorImageGenerationModule` and `ShortformDirectorVideoGenerationModule` are absent. Add HTTP/OpenAPI assertions that generation paths are absent while `/v1/projects/shortform-director/inference/run` remains.

```ts
expect(source).not.toContain('ShortformDirectorImageGenerationModule');
expect(source).not.toContain('ShortformDirectorVideoGenerationModule');
expect(openApi.paths).not.toHaveProperty(
  '/v1/projects/shortform-director/video-generation/jobs',
);
```

- [ ] **Step 2: Write failing migration tests**

Use a mocked `QueryRunner` and assert `up` checks/drops image first and video second. Assert `down` invokes the two original create migrations in dependency-safe order.

```ts
expect(queryRunner.dropTable.mock.calls).toEqual([
  ['shortform_director_ai_image_jobs', true],
  ['shortform_director_ai_video_jobs', true],
]);
```

- [ ] **Step 3: Implement the forward migration without rewriting history**

```ts
import type { MigrationInterface, QueryRunner } from 'typeorm';
import {
  CreateShortformDirectorAiVideoJobs1786000000000,
} from './1786000000000-CreateShortformDirectorAiVideoJobs.js';
import {
  CreateShortformDirectorAiImageJobs1786100000000,
} from './1786100000000-CreateShortformDirectorAiImageJobs.js';

export class DropShortformDirectorGeneratedMediaJobs1787800000000
implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    if (await queryRunner.hasTable('shortform_director_ai_image_jobs')) {
      await queryRunner.dropTable('shortform_director_ai_image_jobs', true);
    }
    if (await queryRunner.hasTable('shortform_director_ai_video_jobs')) {
      await queryRunner.dropTable('shortform_director_ai_video_jobs', true);
    }
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await new CreateShortformDirectorAiVideoJobs1786000000000()
      .up(queryRunner);
    await new CreateShortformDirectorAiImageJobs1786100000000()
      .up(queryRunner);
  }
}
```

Do not edit the two existing create-migration files.

- [ ] **Step 4: Remove module registration, entities, and generation source trees**

Remove both modules from `AppModule`, remove `AiVideoJobEntity` and `AiImageJobEntity` from `user.datasource.ts`, add `DropShortformDirectorGeneratedMediaJobs1787800000000` after both create migrations in the datasource migration list, remove capability-catalog imports from retained inference code, then delete the three listed generation/capability paths. Update `user.datasource.spec.ts` to assert both job entities are absent and all three create/create/drop migration classes remain registered in chronological order.

- [ ] **Step 5: Remove fal.ai runtime administration but preserve stored rows as inert rollback data**

Delete the fal credential service/provider/controller branches and reject `fal` in `CreateApiKeyDto`. Keep the storage-level `ProviderCredentialProvider` discriminator able to read an already persisted `fal` row, but make `ApiKeysService` filter it from `list()` and reject update, delete, activate, lookup-for-test, or creation when the resolved provider is `fal`. This avoids destructive deletion of encrypted user data while making it unreachable from the product.

```ts
export const ACTIVE_PROVIDER_CREDENTIALS = [
  'naver',
  'openai',
  'gemini',
  'youtube',
] as const;

export type ActiveProviderCredentialProvider =
  typeof ACTIVE_PROVIDER_CREDENTIALS[number];

// `fal` remains readable only for already persisted encrypted rows.
export type StoredProviderCredentialProvider =
  | ActiveProviderCredentialProvider
  | 'fal';

export type ProviderCredentialProvider = StoredProviderCredentialProvider;

export function isActiveProviderCredential(
  provider: StoredProviderCredentialProvider,
): provider is ActiveProviderCredentialProvider {
  return (ACTIVE_PROVIDER_CREDENTIALS as readonly string[]).includes(provider);
}
```

- [ ] **Step 6: Run Web API boundary, credential, migration, and build checks**

```bash
npm -C web/clipper_web_api test -- --runInBand \
  src/app.module.spec.ts \
  src/core/database/migrations/user/1787800000000-DropShortformDirectorGeneratedMediaJobs.spec.ts \
  src/modules/api-keys/application/api-keys.service.spec.ts \
  src/modules/api-keys/presentation/api-keys.controller.spec.ts \
  src/modules/api-keys/presentation/dto/create-api-key.dto.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.openapi.spec.ts
npm -C web/clipper_web_api run build
```

Expected: PASS; no migration is run against the user's local database during this test task.

- [ ] **Step 7: Commit Web API removal**

```bash
git -C web/clipper_web_api add src
git -C web/clipper_web_api commit -m "refactor: remove storyboard media generation api"
```

---

### Task 8: Remove Desktop Nest Media, Render, and Completed-Video Paths

**Files:**
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video-web-api.client.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video.service.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-project.mapper.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration.service.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-image-production.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/domain/programmatic-motion.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-quality-evaluator.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-timing-alignment.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/generated-image-file.inspector.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-generated-image.storage.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-generated-video.storage.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-ai-video.dto.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/synthesize-shortform-director-narration.dto.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-ai-video.controller.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-final-render.controller.ts`
- Delete: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-narration.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/project-detail-builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/domain/project.model.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-storyboard-only-boundary.test.js`
- Modify: `desktop/clipper_nestjs/test/project-detail-builder-shortform-director.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-project-archive.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-ai-image-job.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-ai-video-client.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-ai-video-controller.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-ai-video-service.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-clipper-render-adapter.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-final-render-service.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-generated-image-storage.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-generated-media-production.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-narration-controller.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-narration-service.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-quality-eval.test.js`
- Delete: `desktop/clipper_nestjs/test/shortform-director-tts-timing-alignment.test.js`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024-progressive.jpg`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024-vp8.webp`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024-vp8l.webp`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024-vp8x.webp`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024.jpg`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024.png`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-512.webp`
- Delete: `desktop/clipper_nestjs/test/fixtures/shortform-director/representative-45s-tts-timing.json`

**Interfaces:**
- Consumes: Task 4 artifact-based workflow and earlier-result read adapter.
- Produces: no plugin-owned media/TTS/render route, provider, storage, or completed-video archive integration; generic project/render modules remain intact. Historical project-schema parsers remain solely so the read adapter can open existing saved results.

- [ ] **Step 1: Strengthen the boundary test before deletion**

Update `desktop/clipper_nestjs/test/shortform-director-storyboard-only-boundary.test.js` to boot the module and assert 404 for the removed paths:

```js
for (const path of [
  '/projects/shortform-director/projects/example/narration/presets',
  '/projects/shortform-director/projects/example/ai-video/jobs',
  '/projects/shortform-director/projects/example/final-renders',
]) {
  const response = await request(app.getHttpServer()).get(path);
  assert.equal(response.status, 404);
}
```

Also scan the Nest module metadata for removed controllers/providers.

- [ ] **Step 2: Remove module registrations and exact source files**

Remove imports/providers/controllers/exports first so TypeScript identifies remaining consumers, then delete every file listed above. Retain `shortform-director-project.repository.ts`, its JSON implementation, `shortform-director.model.ts`, and the domain types imported by that parser only for earlier-result reading and still-active pre-storyboard routes. Those retained parsers must not be registered as media executors and must not expose a media action.

- [ ] **Step 3: Remove completed-video publishing from generic projects**

Delete `recordCompletedShortformDirectorRender`, render-origin parsing, Storyboard render revision fields, special completed-video file resolution, and the `shortform_director` render list category from `projects.service.ts`, `project-detail-builder.ts`, and `project.model.ts`. Preserve generic project details and plugin navigation metadata.

- [ ] **Step 4: Delete tests whose subject no longer exists and update shared tests**

Delete the exact active-execution and replaced-quality tests listed above. Keep asset-pack, production-state, and project-repository parser tests that protect existing saved-project readability. Update project service/detail tests to assert no completed-video Storyboard block while unrelated project categories still render.

- [ ] **Step 5: Prove removed symbols and routes are gone**

```bash
rg -n -i \
  'ShortformDirectorAiVideoService|ShortformDirectorNarrationService|ShortformDirectorFinalRenderService|LocalShortformDirectorGenerated|startAiVideo|synthesizeNarration|recordCompletedShortformDirectorRender' \
  desktop/clipper_nestjs/src/modules/shortform-director/application \
  desktop/clipper_nestjs/src/modules/shortform-director/presentation \
  desktop/clipper_nestjs/src/modules/shortform-director/infrastructure \
  desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts \
  desktop/clipper_nestjs/src/modules/projects
node --test \
  desktop/clipper_nestjs/test/shortform-director-storyboard-only-boundary.test.js \
  desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js \
  desktop/clipper_nestjs/test/project-detail-builder-shortform-director.test.js \
  desktop/clipper_nestjs/test/shortform-director-project-archive.test.js
npm -C desktop/clipper_nestjs run build
```

Expected: `rg` has no hit for active runtime symbols; tests and build pass. Historical parser-only domain names are outside this active-runtime scan.

- [ ] **Step 6: Commit Nest removal**

```bash
git -C desktop/clipper_nestjs add src test
git -C desktop/clipper_nestjs commit -m "refactor: remove storyboard media production runtime"
```

---

### Task 9: Remove Electron Storyboard Runtime Packaging

**Files:**
- Delete: `desktop/clipper_electron/scripts/prepare-shortform-director-motion-canvas.mjs`
- Delete: `desktop/clipper_electron/src/main/backend/shortform-director-runtime.ts`
- Delete: `desktop/clipper_electron/test/shortform-director-packaged-runtime.test.js`
- Delete: `desktop/clipper_electron/test/shortform-director-packaging-script.test.mjs`
- Create: `desktop/clipper_electron/test/storyboard-document-only-packaging.test.mjs`
- Modify: `desktop/clipper_electron/scripts/build-app.mjs`
- Modify: `desktop/clipper_electron/electron-builder.yml`
- Modify: `desktop/clipper_electron/package.json`
- Modify: `desktop/clipper_electron/src/main/backend/nest-process.ts`
- Modify: `desktop/clipper_electron/src/main/backend/nest-manager.ts`
- Modify: `desktop/clipper_electron/src/main/main.ts`

**Interfaces:**
- Consumes: the Desktop Nest boundary from Task 8.
- Produces: a normal packaged Nest process with no Storyboard Motion Canvas resource, discovery object, build step, or environment variable.

- [ ] **Step 1: Write failing packaging-boundary assertions**

Create `storyboard-document-only-packaging.test.mjs` to read `electron-builder.yml`, `package.json`, `scripts/build-app.mjs`, `src/main/backend/nest-process.ts`, `src/main/backend/nest-manager.ts`, and `src/main/main.ts`. Assert the packaged resource list and spawned environment omit `shortform-director-motion-canvas`, `SHORTFORM_DIRECTOR_MOTION_CANVAS_DIR`, and all Storyboard renderer variables, while the bundled Nest entry point and data directory remain.

```js
assert.equal(spawnOptions.env.SHORTFORM_DIRECTOR_MOTION_CANVAS_DIR, undefined);
assert.doesNotMatch(builderYaml, /shortform-director-motion-canvas/i);
assert.doesNotMatch(packageJson.scripts ?? {}, /prepare:shortform-director/i);
```

- [ ] **Step 2: Remove runtime discovery and build wiring**

Delete constructor fields/imports/calls for `ShortformDirectorRuntime`, remove environment injection from `nest-process.ts`, remove the preparation call from `build-app.mjs`, remove the `prepare:shortform-director` package script, and remove the resource entry from `electron-builder.yml`. Then delete the runtime/preparation source and their dedicated tests.

- [ ] **Step 3: Run Electron tests and build**

```bash
npm -C desktop/clipper_electron test
npm -C desktop/clipper_electron run build
```

Expected: PASS; the build output contains no Storyboard-specific runtime reference.

- [ ] **Step 4: Commit Electron removal**

```bash
git -C desktop/clipper_electron add \
  package.json electron-builder.yml scripts src test
git -C desktop/clipper_electron commit -m "refactor: stop packaging storyboard render runtime"
```

---

### Task 10: Remove fal.ai Controls from Web Admin

**Files:**
- Modify: `web/clipper_web_admin/src/app/core/api/api-keys-api.service.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/api-keys-api.service.spec.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/mock/mock-api.interceptor.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/mock/mock-data.ts`
- Modify: `web/clipper_web_admin/src/app/core/api/models.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.html`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.component.spec.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/api-keys.view-model.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/components/api-key-test-modal/api-key-test-modal.component.spec.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/components/provider-credential-section/provider-credential-section.component.spec.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/services/manual-provider-credential.facade.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/api-keys/services/manual-provider-credential.facade.spec.ts`

**Interfaces:**
- Consumes: active provider list `openai`, `gemini`, and `youtube` from Task 7.
- Produces: no fal.ai form, status card, API method, facade branch, copy, or model union; Naver, OpenAI, Gemini, and YouTube controls continue to work.

- [ ] **Step 1: Enumerate exact active files and write failing UI/API tests**

Update the listed specs first. Full provider-list tests assert Naver, OpenAI, Gemini, and YouTube remain; the manual-provider facade asserts only Gemini and YouTube; API tests assert no fal endpoint request can be constructed; visible text contains no fal.ai or Seedance label.

```ts
expect(fixture.nativeElement.textContent).not.toMatch(/fal\.ai|seedance/i);
expect(manualProviderIds).toEqual(['gemini', 'youtube']);
expect(allProviderIds).toEqual(['naver', 'openai', 'gemini', 'youtube']);
```

- [ ] **Step 2: Remove the exact returned branches**

Delete fal-specific API methods, runtime types, facade signals/actions, form controls, status cards, mocks, and HTML blocks. Do not alter Naver, Gemini, OpenAI, or YouTube behavior.

- [ ] **Step 3: Run Web Admin tests, scan, and build**

```bash
npm -C web/clipper_web_admin test -- --watch=false --browsers=ChromeHeadless
rg -n -i 'fal\.ai|\bfal\b|seedance' web/clipper_web_admin/src
npm -C web/clipper_web_admin run build
```

Expected: tests/build pass and `rg` returns no application-source hit.

- [ ] **Step 4: Commit Web Admin removal**

```bash
git -C web/clipper_web_admin add src
git -C web/clipper_web_admin commit -m "refactor: remove fal generation controls"
```

---

### Task 11: Verify Desktop Python Has No Storyboard-Owned Runtime

**Files:**
- Inspect: `desktop/clipper_python/plugins/`
- Inspect: `desktop/clipper_python/tests/`
- No planned source change

**Interfaces:**
- Consumes: the removal boundary from Tasks 8 and 9.
- Produces: evidence that shared Python rendering remains decoupled and no Storyboard-owned code is left.

- [ ] **Step 1: Scan for direct ownership markers**

```bash
rg -n -i \
  'shortform-director|shortform_director|storyboard' \
  desktop/clipper_python/plugins \
  desktop/clipper_python/tests
```

Expected: no hits. If a direct marker appears, stop this task and add only that exact file to the deletion set after proving it has no non-Storyboard caller with a second `rg` call.

- [ ] **Step 2: Prove currently shared renderer concepts have active non-Storyboard callers**

```bash
rg -n \
  'composition_mode|tts_offset|Jalnan|template_gradient' \
  desktop/clipper_python/plugins \
  desktop/clipper_python/tests \
  desktop/clipper_nestjs/src
```

Expected: the symbols are used by generic manifest/template/render paths, so they remain.

- [ ] **Step 3: Run the targeted generic renderer tests**

```bash
uv run --directory desktop/clipper_python pytest \
  tests/test_clipper_video_render_contract.py \
  tests/test_auto_motion_renderer.py \
  tests/test_local_render_adapter_golden_frames.py -q
```

Expected: PASS; these exercise the generic render contract, motion renderer, and local-render output without creating a Storyboard-specific replacement test.

- [ ] **Step 4: Record no-op repository status**

```bash
git -C desktop/clipper_python status --short
```

Expected: this task creates no diff and therefore no commit.

---

### Task 12: Remove Angular Completed-Video Archive Integration

**Files:**
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.html`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/core/history/project-history.service.ts`
- Modify: `desktop/clipper_angular/src/core/history/project-history.service.spec.ts`

**Interfaces:**
- Consumes: the read-only Storyboard page from Task 6 and generic project API boundary from Task 8.
- Produces: plugin navigation remains available, but generic project details no longer present Storyboard render revisions or completed-video actions.

- [ ] **Step 1: Locate the exact special-case files and write failing tests**

Update both listed specs to assert a project-detail response containing an old `shortform_director` category does not render a video player/download/open-render action, while the plugin-store navigation card still routes to the Storyboard plugin.

- [ ] **Step 2: Remove archive/render-specific branches**

Delete Storyboard render models, mapper cases, query parameters, templates, event handlers, and completed-video copy. Retain generic project history and plugin navigation.

- [ ] **Step 3: Run Angular project and Storyboard integration tests**

```bash
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless \
  --include='src/shell/projects/projects-detail-page/projects-detail-page.component.spec.ts' \
  --include='src/features/shortform-director/shortform-director-routing.integration.spec.ts' \
  --include='src/features/shortform-director/shortform-director-registration.spec.ts'
```

Expected: PASS; plugin route/registration remains and completed-video integration is absent.

- [ ] **Step 4: Verify protected files and commit the archive removal**

```bash
git -C desktop/clipper_angular diff -- \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts
git -C desktop/clipper_angular add \
  src/shell/projects/projects-detail-page \
  src/core/history/project-history.service.ts \
  src/core/history/project-history.service.spec.ts
git -C desktop/clipper_angular commit -m "refactor: remove storyboard completed video archive"
```

Expected: protected diff still matches Task 1.

---

### Task 13: Cross-Repository Verification and Packaged Smoke Test

**Files:**
- Modify only if a verification failure reveals a defect in files already owned by Tasks 2–12
- Inspect: all six repository statuses and diffs

**Interfaces:**
- Consumes: every task deliverable.
- Produces: evidence for all acceptance criteria without paid external calls.

- [ ] **Step 1: Run all affected repository unit suites**

```bash
npm -C web/clipper_web_api test -- --runInBand
node --test desktop/clipper_nestjs/test/*.test.js
npm -C desktop/clipper_angular test -- --watch=false --browsers=ChromeHeadless
npm -C desktop/clipper_electron test
npm -C web/clipper_web_admin test -- --watch=false --browsers=ChromeHeadless
```

Expected: PASS. Test doubles must intercept inference; there must be no live provider credential use.

- [ ] **Step 2: Run all affected builds**

```bash
npm -C web/clipper_web_api run build
npm -C desktop/clipper_nestjs run build
npm -C desktop/clipper_angular run build:electron
npm -C desktop/clipper_electron run build
npm -C web/clipper_web_admin run build
```

Expected: PASS.

- [ ] **Step 3: Run static boundary scans**

```bash
rg -n -i \
  'Seedance|Nano Banana|generated-video|generated-image|ai-video/jobs|final-renders|narration/presets' \
  desktop/clipper_angular/src/features/shortform-director
rg -n \
  'ShortformDirector(Image|Video)GenerationModule|Ai(Image|Video)JobEntity' \
  web/clipper_web_api/src/app.module.ts \
  web/clipper_web_api/src/core/database/user.datasource.ts
rg -n \
  'SHORTFORM_DIRECTOR_MOTION_CANVAS_DIR|shortform-director-motion-canvas' \
  desktop/clipper_electron/src \
  desktop/clipper_electron/scripts \
  desktop/clipper_electron/electron-builder.yml
```

Expected: all three scans return no hit. Historical media-shaped types may remain only inside the Desktop Nest earlier-result read adapter and persisted project parser.

- [ ] **Step 4: Verify migration registration and active entity metadata**

Run the migration spec plus a datasource metadata test that asserts neither job table/entity is active. Do not run the migration command against a developer database.

```bash
npm -C web/clipper_web_api test -- --runInBand \
  src/core/database/migrations/user/1787800000000-DropShortformDirectorGeneratedMediaJobs.spec.ts \
  src/core/database/user.datasource.spec.ts
```

Expected: PASS.

- [ ] **Step 5: Build the packaged desktop app and inspect its resources**

```bash
npm -C desktop/clipper_electron run build:app:mac:arm64:local-api
find desktop/clipper_electron/dist-app -iname '*shortform*' -o -iname '*motion-canvas*'
```

Expected: the app build succeeds; no Storyboard-specific Motion Canvas/runtime resource is listed. The normal Angular and Nest bundles can still contain internal `shortform-director` module names.

- [ ] **Step 6: Perform a local mocked workflow smoke test**

Start the local app against fixture inference responses and verify in order:

```text
candidate -> preflight (2 normal / 3 maximum) -> generate
-> persisted editorial checkpoint -> persisted shot checkpoint
-> storyboard view -> Korean whole-document copy
-> English master-prompt copy -> per-shot prompt/query copy
```

Then terminate after pass 1, restart, and verify the resume request calls only `scene-media-decision`. Open an earlier successful result and verify it is readable with unavailable prompt/search actions omitted. Request each removed route and verify 404.

- [ ] **Step 7: Check diffs, protected changes, and whitespace**

```bash
for repo in \
  web/clipper_web_api \
  desktop/clipper_nestjs \
  desktop/clipper_angular \
  desktop/clipper_electron \
  web/clipper_web_admin \
  desktop/clipper_python
do
  git -C "$repo" status --short --branch
  git -C "$repo" diff --check
done
git -C desktop/clipper_angular diff -- \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.html \
  src/features/shortform-director/components/research-artifact-summary/research-artifact-summary.component.spec.ts
```

Expected: no whitespace errors; protected Angular diff equals Task 1; Python remains unchanged; every implementation commit is present on `feat/storyboard`.

- [ ] **Step 8: Close verification without an umbrella commit**

If Steps 1–7 reveal a defect, return to the task that owns the failing test, correct only that task's listed files, rerun its narrow test and commit command, then restart Task 13. If no correction is required, do not create an empty commit.

---

## Acceptance Traceability

- Two-call generation and three-call ceiling: Tasks 2–5, 13.
- Stage persistence, atomic result, and restart resume: Task 4, 13.
- Timing, evidence, narration, specificity, continuity, and search validation: Tasks 2–4.
- Korean document and English prompt/search clipboard actions: Tasks 5–6.
- Earlier successful storyboard reading: Tasks 4–6, 13.
- No media/TTS/render/completed-video UI or API: Tasks 6–10, 12–13.
- No packaged Storyboard rendering runtime: Tasks 9 and 13.
- Forward removal of active media-job tables: Tasks 7 and 13.
- No automatic image search/download/rights claim: Tasks 2, 5–6, 13.
- Shared Python rendering preserved: Task 11.
- Protected pre-existing Angular work preserved: Tasks 1, 5–6, 12–13.
