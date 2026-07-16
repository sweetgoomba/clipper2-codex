# 프롬프트 숏폼 품질 고도화와 하이브리드 생성 파이프라인 방향

작성일: 2026-07-15 KST
갱신일: 2026-07-16 KST

## 문서 상태

- 이 문서는 2026-07-15 제품·기술 논의를 정리하고, 2026-07-16 코드 감사와 독립 `shortform_director` 플러그인 결정을 반영한 working design이다.
- 전체 하이브리드 파이프라인의 확정 설계나 renderer/provider 선정 결과가 아니다.
- 현재 Clipper 코드 경계와 기존 계약은 2026-07-16에 감사했으며, 첫 구현은 기존 렌더 결과를 바꾸지 않는 계획 IR 호환 계층으로 한정한다.
- NotebookLM의 공개 사실과 출력물을 보고 추정한 재현 아이디어를 구분한다.
- `clipper_docs`에는 아직 반영하지 않고 `.codex` 작업 문서로 유지한다.

## 한 줄 결론

Clipper Studio를 `프롬프트 1개 → 정적 이미지 중심 영상 1개` 도구에서, Vira의 시장 인텔리전스와 브랜드 근거를 바탕으로 실제 에셋·생성 에셋·프로그램 모션을 장면별로 혼합해 수십·수백 개의 마케팅 숏폼을 기획·제작하는 시스템으로 발전시킨다.

## 문제 정의

현재 프롬프트 숏폼 생성은 대략 다음 흐름이다.

```text
사용자 프롬프트
  → 백엔드에서 보강한 LLM 요청
  → 클립별 대본과 검색 키워드
  → 키워드 기반 이미지 검색
  → 클립 하나에 에셋 하나를 매칭
  → TTS·자막·클립 렌더
  → FFmpeg 최종 합성
```

이 구조의 품질 한계는 정적 이미지 하나만의 문제가 아니다.

- 입력이 단발성 프롬프트에 가까워 사실·시장·브랜드 맥락이 약하다.
- LLM 출력이 기존 `clip + keyword` 스키마에 묶여 영상 연출 결정을 충분히 표현하지 못한다.
- 검색 키워드와 에셋의 의미적 연관성만 보고 장면의 목적·진정성·감정·연출을 판단하지 않는다.
- 대본, 단어 타이밍, 시각 레이어, 전환, 효과음이 하나의 시간축에서 계획되지 않는다.
- 한 번 생성한 결과를 품질 기준으로 평가·교정하거나 실제 성과로 학습하는 폐루프가 없다.

따라서 네이버 이미지 검색을 생성형 영상 API로 단순 교체하는 것은 근본 해결이 아니다.

## NotebookLM 벤치마크의 사실 경계

### 공개적으로 확인된 내용

- NotebookLM은 PDF, 웹사이트, YouTube, 오디오, Google Docs/Slides 등 사용자가 선택한 source를 바탕으로 답변과 artifact를 생성한다.
- Video Overview는 형식, 언어, 시각 스타일과 steering prompt를 제공한다.
- 공식 도움말 기준 Short Video Overview는 약 60초이며 현재 영어만 지원한다.
- Google은 일반 Video Overview가 Nano Banana로 source 문맥에 맞는 일러스트를 생성한다고 공개했다.
- 별도 Cinematic Video Overview는 Gemini 3, Nano Banana Pro, Veo 3를 조합하고, Gemini가 narrative·visual style·format·consistency를 결정하는 creative director 역할을 한다고 공개했다.
- Google은 source grounding에도 생성 음성·시각물에 부정확함이나 audio glitch가 있을 수 있다고 명시한다.

공식 자료:

- https://support.google.com/notebooklm/answer/16164461?hl=en
- https://support.google.com/notebooklm/answer/16454555?hl=en-GB
- https://blog.google/innovation-and-ai/models-and-research/google-labs/video-overviews-nano-banana/
- https://blog.google/innovation-and-ai/products/notebooklm/generate-your-own-cinematic-video-overviews-in-notebooklm/

### 공개적으로 확인되지 않은 내용

다음 도구가 NotebookLM 내부에서 실제 사용된다는 공개 근거는 확인하지 못했다.

- Stable Video Diffusion, SDXL
- Manim, Remotion
- ChatTTS, ElevenLabs
- Suno, Udio
- FFmpeg memory pipe, Drawtext, WebVTT를 사용한 구체적인 합성 방식

이 목록은 NotebookLM의 확정 스택이 아니라 유사 결과를 재현할 때 검토할 수 있는 후보 기술로 취급한다. Short와 Cinematic이 같은 내부 생성 파이프라인을 쓴다고도 단정하지 않는다.

## NotebookLM에서 실제로 벤치마킹할 것

NotebookLM 제품 자체를 복제하지 않는다. 다음 세 가지 설계 원리를 가져온다.

1. source-grounded planning
   - 선택한 근거와 사용자 지시를 바탕으로 대본과 구조를 만든다.
   - 주장별 source provenance를 보존한다.
2. AI creative director
   - 영상 전체의 narrative, pacing, style, visual grammar와 일관성을 결정한다.
   - 에셋 API 하나를 고르는 수준이 아니라 장면별로 많은 연출 결정을 내린다.
3. timeline orchestration
   - 음성, 단어·문장 타임스탬프, 시각 레이어, 도식, 자막, BGM, SFX를 같은 시간축에서 조정한다.

## Clipper의 제품 차별점

Clipper Studio의 핵심 타깃은 학습 영상을 소비하는 사용자가 아니라 숏폼을 지속해서 제작해야 하는 마케터·광고주·브랜드 운영자다.

따라서 다음을 NotebookLM보다 더 중요하게 다뤄야 한다.

- 한국 숏폼 시장에서 현재 작동하는 포맷·훅·키워드
- 브랜드, 실제 제품, 연예인·인플루언서 등 실재 대상의 진정성 있는 에셋
- 캠페인 목적, CTA, 퍼널 단계, 타깃과 금지 표현
- 한 영상이 아니라 콘텐츠 시리즈와 대량 변형
- 생성 후 실제 공유·저장·조회·전환 성과의 피드백
- 저작권·초상권·상표·광고 고지와 사실 주장에 대한 provenance

## Vira 현재 코드에서 확인한 연결점

현재 정본:

- 실제 저장소: `/Users/jina/project/vira`
- 감사 기준: `main`의 `2f1d1fd`, `origin/main` 동기화, clean
- 상세 감사·handoff 설계: `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`

기존 PDF는 제품 방향과 작성 당시 상태를 설명하는 참고 자료로 낮춘다.

- `/Users/jina/project/adlight/vira/vira-deck.pdf`
- `/Users/jina/project/adlight/vira/vira-IR_20260616 (3).pdf`

현재 코드 기준 Vira의 기본 시장 표면은 2026-07-10에 바뀌었다.

- `/intel/market`은 `shorts_videos`, 최신 `shorts_snapshots`, `shorts_comments`, `comment_sentiments`를 읽는 YouTube Shorts 분류·탐색 화면이다.
- 활성 데이터는 열린 Naver category 문자열, 수집 keyword, hashtag, 조회·좋아요·댓글, 댓글 감성 중심이다.
- `/intel/Tmarket`은 최근 3개 snapshot의 endpoint 조회 증가량을 영상 나이 버킷 안에서 백분위로 환산한다. `s >= 90`을 `뜨는 중`으로 표시하지만 아직 기본 navigation에 없는 lab surface다.
- 단일 영상 8차원 분석 engine과 `analyzeVideo` handler는 남아 있다. 다만 분석을 시작하던 기존 UI는 `_archived` 아래에 있어 완료 run이 있을 때만 on-demand evidence로 다룬다.
- 기존 16개 포맷/5개 그룹, hook strength/3초 통과율, keyword Viral Score/rolling cohort 코드는 보존돼 있지만 관련 Market/Viral Inngest 함수가 등록 해제됐다. 이는 current active contract가 아니라 `legacy_unregistered` 자산이다.
- Vira 코드에는 현재 Clipper handoff endpoint, export button, webhook 또는 다른 자동 연동 구현이 없다. 전략 문서의 자동 연동 표현을 현재 기능으로 기술하지 않는다.

따라서 Vira 입력은 하나의 평평한 MarketContext가 아니라 다음 lifecycle을 가진 evidence로 구분한다.

- `active`: 현재 Shorts raw observation
- `lab`: 또래 성장 백분위 같은 request-time derived signal
- `on_demand`: 성공한 8차원 analysis module 결과
- `legacy_unregistered`: 과거 format/hook/viral report

아래 제품 루프는 현재 구현 상태가 아니라 목표 상태다.

```text
Vira
  무엇이 왜 통하는지 진단
    ↓
Clipper
  진단과 브랜드 근거를 제작 명세로 바꾸고 대량 생성
    ↓
ViewX
  실제 성과를 측정
    ↓
Vira / Clipper
  다음 전략·생성·변형 우선순위에 환류
```

## 입력 계층의 목표 모델

Vira DB 전체를 LLM prompt에 그대로 넣지 않는다. 조회 시점·계산법·lifecycle·출처가 있는 구조화된 context package를 만든다.

### BrandProfile

- 기업·브랜드·제품 정보
- 주요 타깃과 고객 문제
- 브랜드 톤·비주얼 가이드
- 반드시 포함할 사실·표현과 금지 표현
- 실제 제품 사진·영상·로고·인물 등 owned assets

### CampaignBrief

- 인지도, 참여, 전환 등 목적
- 퍼널 단계, CTA, 플랫폼과 영상 길이
- 예산, 생성 수량, 게시 일정
- 캠페인별 법무·광고 고지 제약

### SourcePack

- 사용자가 제공한 문서, URL, 동영상, 오디오, 메모
- 브랜드가 승인한 사실과 주장 근거
- source snapshot/version과 claim provenance

### MarketContext

- 현재 활성 Shorts의 category·keyword·tag·최신 지표·댓글 감성 관측
- 최근 3개 snapshot과 나이 버킷을 근거로 한 파생 성장 백분위
- 완료된 단일 영상 8차원 분석과 근거 module이 표시된 재현 가설
- 명시적으로 선택한 경우에만 사용하는 legacy format/hook/viral report
- 데이터 관측 기간·표본 수·계산법 version·sufficient/partial/insufficient 상태
- AI module confidence와 통계적 표본 충분성을 분리한 품질 metadata

### ContentStrategy

- 만들 콘텐츠 시리즈와 우선순위
- 포맷 × 훅 × 타깃 × 소구점 × CTA의 콘텐츠 매트릭스
- 각 영상이 검증하려는 가설과 변형 축

## 단일 clip 구조를 넘어서는 시간 기반 IR

기존 clip은 편집 단위로 남길 수 있지만 전체 렌더 모델은 시간 기반이어야 한다.

```text
Campaign
└─ VideoPlan
   ├─ Scene
   │  ├─ NarrationBeat
   │  ├─ Shot
   │  │  ├─ background / b-roll layer
   │  │  ├─ product / person layer
   │  │  ├─ diagram / SVG layer
   │  │  ├─ kinetic text / caption layer
   │  │  └─ transition / SFX cue
   │  └─ timing / motion instructions
   └─ AudioTimeline
      ├─ Supertonic narration
      ├─ BGM
      └─ SFX
```

필요한 핵심 관계:

- Scene 하나는 여러 Shot을 가진다.
- Shot 하나는 여러 시각 Layer와 audio cue를 가진다.
- Asset 하나는 여러 Shot에서 재사용될 수 있다.
- Narration word/sentence timestamp가 시각 이벤트의 기준 시간이 된다.
- 생성, 검색, 원본, 브랜드 보유 에셋을 같은 `AssetRef` 계약으로 다룬다.
- 각 에셋은 provider, source, license, prompt, model/version, cost, 생성 상태를 추적한다.

## 하이브리드 에셋 라우팅

영상 전체에 한 가지 에셋 방식을 강제하지 않고 Shot 또는 Beat 단위로 선택한다.

### 실제·검색·원본 에셋 우선

- 연예인, 인플루언서, 실제 사람
- 실제 제품·패키지·매장·장소
- 후기, 성과, 사실의 증거로 쓰는 장면
- 브랜드 일관성이나 초상 동일성이 중요한 장면

### 생성 이미지·영상 우선

- 추상 개념과 분위기
- 존재하지 않는 가상의 상황
- 실제 촬영이 어렵거나 비용이 큰 짧은 B-roll
- source에서 직접 표현할 실제 에셋을 찾을 수 없는 장면

### 프로그램 모션 우선

- 비교, 순서, 관계, 데이터 흐름
- 차트, 숫자, 제품 장점의 구조화된 설명
- 강한 훅, 핵심 문장, CTA
- 반복 가능한 브랜드 템플릿과 전환

라우터는 최소한 `authenticity`, `identity sensitivity`, `visual intent`, `asset availability`, `rights`, `budget`, `latency`, `quality`를 고려해야 한다.

## 기술 후보의 현재 판단

이 절은 shortlist이며 provider 선정 결과가 아니다.

- LLM creative director와 planner: 기존 OpenAI/Gemini API를 provider abstraction 뒤에서 비교한다.
- TTS: 현재 로컬 Supertonic을 유지한다.
- 범용 타임라인·타이포그래피·레이어 합성: Remotion 또는 Motion Canvas를 우선 비교한다.
- 정밀한 수학·기술 도식: Manim을 특화 renderer/plugin으로 검토한다.
- 범용 도식·차트: SVG 기반 renderer와 Graphviz/Mermaid 계열 출력을 검토한다.
- 반복 가능한 아이콘·캐릭터 모션: Lottie 또는 Rive를 검토한다.
- 최종 encode, mux, audio mix, 포맷 변환: 기존 FFmpeg 역할을 유지한다.
- 생성 이미지·영상: 오픈 모델과 상용 API를 품질·비용·시간·라이선스 기준으로 평가한다. 최신 provider/model matrix는 다음 조사에서 별도로 만든다.

Manim 하나를 전체 마케팅 영상 renderer로 삼기보다는 범용 타임라인 renderer에 특화 도식 renderer를 붙이는 구성이 더 적합할 가능성이 높다.

또한 동적인 결과를 위해 모든 장면을 video generation으로 만들 필요는 없다. 고품질 정적 일러스트에 레이어 분리, mask, parallax, camera pan/zoom, text motion과 transition을 적용하면 더 낮은 비용과 높은 재현성으로 충분한 motion quality를 얻을 수 있다.

## 품질 정의와 평가

`NotebookLM처럼 좋아 보인다`를 단일 주관 평가로 두지 않는다. 최소한 다음 축을 분리한다.

- source faithfulness와 claim provenance
- 첫 3초 hook strength
- script coherence와 정보 밀도
- narration과 visual의 의미 적합도
- visual style·character·brand consistency
- motion continuity와 transition 품질
- word/sentence 단위 audio-video sync
- caption 가독성과 mobile safe zone
- 생성 artifact, 깨진 글자·손·얼굴·로고 오류율
- 실제 에셋 권리와 생성물 provenance
- 영상당 latency와 변동 비용
- 사용자 수정량과 생성 성공률
- ViewX에서 관측한 retention·engagement·conversion

초기에는 동일 brief로 기존 Clipper, NotebookLM Short/Cinematic, 경쟁 도구, 새 PoC를 생성해 blind review와 shot-by-shot annotation을 수행한다. 이후 Vira·ViewX 지표를 연결한다.

2026-07-16에는 이 사람 평가를 대체하지 않는 첫 회귀 기반을 추가했다. 비밀 없는 45초 합성 기준편을 기존 Vira admission, ContentStrategy, VideoPlan validator로 통과시킨 뒤 `structural_proxy` report를 만든다. grounding, 첫 3초 hook, CTA, 서사, visual coverage, asset authenticity, 금지 표현, disclosure는 blocking으로 보고, narration density, shot pacing, text readability, unresolved asset은 warning으로만 본다. source faithfulness와 실제 연출 품질 7개 축은 rendered sample 전까지 자동 점수화하지 않는다.

## 2026-07-16 설계 구체화

### 현재 코드 감사

현재 프롬프트 숏폼의 실제 호출·데이터·렌더 경계는 다음과 같다.

```text
clipper_angular
  ShortformProject(clips + previewTimeline) 편집
    ↓ POST /projects/shortform/projects/:id/clips
clipper_nestjs
  WebApiClipperStudioScriptGenerator
    ↓ POST /llm/script
clipper_web_api
  OpenAI Responses + web_search
  고정된 8 clips × 2 subtitles 중심 JSON 생성
    ↓
clipper_nestjs
  TTS + source URL 이미지 또는 이미지 검색
  clips/mediaSlots/previewTimeline 저장
    ↓ 렌더 시작
  ProjectManifest → RenderRecipe → legacy clipper_payload
    ↓
clipper_python / clipper_video_render
  legacy payload 중심 FFmpeg 합성·자막·BGM·최종 mux
```

감사에서 확인한 핵심 경계:

- 실제 NestJS DI는 `ClipperStudioScriptGenerator → WebApiClipperStudioScriptGenerator`로 연결된다. 같은 파일에 남은 configured/direct generator는 현재 숏폼 모듈의 런타임 경로가 아니다.
- `ShortformProject`의 정본 편집 단위는 아직 `clips`이며, Angular preview도 `clips/mediaSlots`를 평면 시간축으로 조합한다.
- 기존 `RenderRecipe`에는 이미 video/audio/subtitle/overlay track과 실행용 timeline이 있다. 따라서 새 `VideoPlan`은 이를 대체하는 두 번째 실행 레시피가 아니라 **창작 의도와 근거를 담는 상위 planning IR**이어야 한다.
- 현재 Python renderer는 `clipper_payload`를 주로 소비하고 `RenderRecipe`에서 fps·timing·motion·output 일부를 사용한다. 첫 단계에서 이 경로를 바꾸면 IR 도입과 renderer 교체가 결합되므로 피한다.
- `/llm/script`의 실제 DTO는 `operationRunId`를 선택값으로 허용하지만 OpenAPI는 필수로 기술한다. NestJS의 clip 생성은 operation run을 시작하지 않고 렌더 시작 시 `shortform.create`를 과금한다. 과금 시점 결정 없이 이 drift를 이번 작업에서 수정하지 않는다.

소유권은 다음처럼 분리한다.

| 계층 | 책임 | 현재/향후 계약 |
|---|---|---|
| Grounded input | 브랜드·캠페인·source·Vira 관측 근거 | `PlanningContext` |
| Creative planning | 서사·장면·비트·샷·레이어·에셋 전략 | `VideoPlan` |
| Execution planning | artifact가 해소된 렌더 track과 timing | 기존 `RenderRecipe` |
| Compatibility | 현재 편집 UI와 Python renderer 연결 | 기존 `clips`, `clipper_payload` |
| Encoding | 합성, codec, mux, thumbnail | 기존 FFmpeg 경로 |

### Vira → Clipper 최소 structured handoff

Vira 원본 DB나 전체 8차원 분석 JSON을 prompt에 그대로 넣지 않는다. 현재 Vira의 서로 다른 세대와 계산 방식을 평평한 객체로 합치지 않고, Clipper가 받은 시점의 작은 불변 evidence snapshot을 `MarketContext`에 보존한다.

```ts
type ViraEvidenceKind =
  | 'market.video-observation'
  | 'market.peer-growth'
  | 'analysis.video-8d'
  | 'legacy.market-format-hook'
  | 'legacy.keyword-viral-report';

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
    lifecycle: 'active' | 'lab' | 'on_demand' | 'legacy_unregistered';
    recordRefs?: Array<{ kind: string; id: string }>;
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
    state: 'sufficient' | 'partial' | 'insufficient' | 'unavailable';
  };
  method: {
    id: string;
    version: string;
    parameters?: Record<string, string | number | boolean>;
  };
  payload: TPayload;
}
```

규칙:

- current Market raw observation, Tmarket derived percentile, 8차원 AI inference, legacy report를 `kind`와 lifecycle로 분리한다.
- stable subject identity는 `platform + platformVideoId`다. Vira의 `shorts_videos.id`와 `videos.id`는 source trace ref로만 사용한다.
- request-time 계산인 Tmarket 신호는 handoff 때 사용한 snapshot endpoint 날짜, 나이 버킷, 표본 수, 계산법 version과 함께 materialize한다.
- 공통 `confidence`를 두지 않는다. AI confidence는 module payload 안에, 데이터 충분성은 observation state/window/sample size에 둔다.
- `insufficient`를 낮은 점수로 바꾸지 않고 별도 상태로 보존한다.
- Market observation과 재현 레시피는 생성 지시나 성공 보장이 아니라 근거가 있는 전략 후보로 전달한다.
- `active`는 기본 후보, `lab`은 실험 opt-in, `on_demand`는 완료된 성공 module만, `legacy_unregistered`는 사용자 명시 선택 때만 사용한다.
- 댓글 감성은 audience language/반응 가설에만 쓰고 브랜드·제품 사실 근거로 쓰지 않는다.
- brand/source 사실 주장은 `SourcePack.claims`의 provenance를 인용한다.
- Vira deck의 투자자용 성과 주장이나 아직 검증하지 않은 수치는 제작 사실 근거로 사용하지 않는다.
- 현재 Vira에는 Clipper export/API가 없다. desktop의 Vira DB 직접 접근이나 기존 내부 analysis API 재사용을 피하고, versioned exporter/API와 identity/auth는 별도 계약으로 남긴다.
- Phase 1a에는 네트워크 연동을 추가하지 않는다.

상세 payload, 현재 코드 경로, legacy 경계와 구현 순서는 `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`를 따른다.

### 폐기된 초기 Phase 1a — legacy clip 기반 VideoPlan foundation

> 이 절의 legacy adapter는 의사결정 이력을 보존하기 위한 것이다. 2026-07-16 후속 결정으로 기존 `shortform_prompt`를 변경하지 않기로 했고, 관련 uncommitted 코드와 테스트를 제거했다. 현재 구현 정본은 새 `shortform_director` 플러그인의 native plan foundation이다.

초기에는 provider·renderer와 무관한 `video-plan.v1` 도메인 모델과 결정적 호환 어댑터를 검토·구현했다.

```text
현재 ShortformProject.clips
  ↓ LegacyClipVideoPlanAdapter (순수·결정적)
VideoPlan
  ├─ Scene        = legacy clip 1개
  ├─ NarrationBeat = narration line 1개
  ├─ Shot         = media slot 1개
  ├─ Layer        = visual + caption
  └─ AudioTimeline = narration cue + 선택 BGM cue

기존 렌더 경로
ShortformProject.clips → ProjectManifest → RenderRecipe → clipper_payload → FFmpeg
                       (Phase 1a에서 불변)
```

`video-plan.v1`의 시간은 모두 프로젝트 시작 기준 millisecond 절대값으로 정규화한다. visual layer는 실제 provider 이름 대신 다음 전략만 표현한다.

- `owned`, `source`, `search`, `generated-image`, `generated-video`, `programmatic`, `existing`, `unresolved`

Phase 1a의 어댑터는 현재 에셋을 `owned/source/search/existing`으로 분류하고, 미디어가 없는 clip에는 `unresolved` visual layer를 만든다. 생성형·프로그램 모션 전략은 schema에 표현할 수 있지만 아직 선택하거나 실행하지 않는다. 로컬 파일 경로와 원본 URL은 `VideoPlan`에 복제하지 않고 안정적인 artifact/provider 참조만 둔다.

호환 규칙:

- `ShortformProject.clips`는 현재 편집·렌더 호환 정본으로 유지한다.
- `videoPlan`은 optional이다. 기존 JSON 프로젝트에 필드가 없어도 읽기 실패나 즉시 디스크 migration이 발생하지 않는다.
- 서비스 read/write 경계에서 현재 clip 상태로 legacy-derived plan을 만든다. 미디어 교체·재정렬·slot 수정·TTS 길이 변경 후 stale plan이 저장되지 않아야 한다.
- 향후 native planner를 도입할 때는 `VideoPlan → legacy clips projection`과 `VideoPlan → RenderRecipe compiler`를 별도 단계로 추가한다. Phase 1a의 역방향 어댑터를 창작 정본으로 승격하지 않는다.

Phase 1a 수용 기준:

1. clip 순서와 길이가 절대 scene timeline으로 정확히 변환된다.
2. narration line은 scene 안에서 gap 없이 beat timing을 갖고 마지막 beat가 scene 끝과 일치한다.
3. media slot은 shot과 visual/caption layer로 변환되고 asset route가 provenance에 따라 결정된다.
4. 미디어가 없는 clip도 `unresolved` shot으로 표현된다.
5. 구형 project read는 디스크를 쓰지 않으면서 plan을 제공하고, 모든 후속 저장은 최신 clip에서 plan을 갱신한다.
6. 기존 ProjectManifest/RenderRecipe/clipper_payload/Python renderer 계약과 결과는 바뀌지 않는다.

Phase 1a 비범위:

- `PlanningContext`/`vira-evidence.v1` runtime validation, Vira exporter/API, UI 입력 화면, LLM prompt/schema 변경
- `VideoPlan → RenderRecipe` compiler와 새 renderer
- image/video provider 선정, fallback, 비용·quota 정책
- programmatic motion 구현과 품질 benchmark 실행
- `/llm/script` operation run/OpenAPI drift 수정

Phase 1a 과거 검증 이력과 제거 상태(2026-07-16):

- `clipper_nestjs`의 `feat/shortform-video-plan-foundation` 브랜치에서 한 차례 구현·검증했다.
- 당시 새 테스트 5개와 격리 숏폼 API 테스트 10개, TypeScript build가 통과했다.
- 이후 사용자 결정에 따라 해당 uncommitted adapter/model/service 변경과 테스트를 모두 제거했다.
- 현재 기존 Nest `shortform`/`shortform-core`와 Angular `features/shortform` 경로는 `origin/dev` 대비 diff가 0이다.

### 현재 결정 — 독립 `shortform_director` native plan foundation

새 품질 파이프라인은 기존 `프롬프트로 숏폼 제작(shortform_prompt)` 안에 점진적으로 끼워 넣지 않는다.

```text
기존 shortform_prompt                          새 shortform_director
clips 기반 생성·편집·렌더                     campaign brief
현재 동작 그대로 유지                         + vira-evidence.v1
                                                ↓
                                            PlanningContext
                                                ↓
                                            ContentStrategy
                                                ↓
                                            native VideoPlan
                                                ↓ (향후)
                                            compiler / renderer
```

첫 vertical slice는 독립 plugin identity, 설치 guard, Angular route, 전용 Nest API와 JSON repository, Vira envelope runtime validator, `PlanningContext + empty native VideoPlan` draft 생성까지다. 실제 Vira exporter/API, LLM planner, asset router, compiler와 renderer는 연결하지 않는다.

현재 구현 정본:

- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_IMPLEMENTATION_PLAN_2026-07-16.md`

두 번째 vertical slice는 Vira exporter가 없는 현재 상태를 숨기지 않고 manual JSON handoff를 제공한다. active/lab/on-demand/legacy evidence를 current payload와 lifecycle로 검증하고 `candidate/context_only/excluded`로 분류하며, LLM derivation 전 `contentStrategy`는 `null`로 유지한다.

세 번째 vertical slice는 `planning-context.v2`의 BrandProfile/CampaignBrief/SourcePack과 grounded ContentStrategy structured output을 구현했다. 네 번째 vertical slice는 사용자가 고른 content matrix entry를 `Scene → Beat → Shot → Layer` native VideoPlan으로 바꾸고, absolute timeline, grounding coverage, hook/CTA, 금지 표현, provider-neutral asset strategy를 web API와 desktop에서 이중 검증한다.

현재 추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_GROUNDED_CONTENT_STRATEGY_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`

다섯 번째 vertical slice는 45초 합성 선크림 case와 `video-plan-quality-report.v1`을 추가했다. 5 scene, 7 beat, 10 shot, 20 layer의 expected plan을 기준으로 deterministic structural 회귀를 수행한다. 이 evaluator는 production generation/billing/UI에 연결하지 않았고 총점이나 배포 gate가 아니다. 상세 기준과 구현 결과는 위 대표 eval 정본을 따른다.

여섯 번째 vertical slice는 `asset-pack.v1`과 `asset-ref.v1` foundation을 추가했다. VideoPlan visual layer를 requirement로 바꾸고 programmatic은 resolved, route가 정해졌지만 ref가 없으면 missing, route 자체가 미정이면 unresolved로 분리한다. 합성 ref/binding으로 origin, image/video, availability, rights 호환성을 검증하지만 실제 ingestion endpoint, picker, provider 호출은 아직 없다. Angular는 이 준비 상태와 pending layer를 표시한다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`

일곱 번째 vertical slice는 기존 사용자 프로젝트의 로컬 `owned/source` artifact를 director layer에 연결한다. ProjectManifest artifact id가 project-scoped라는 감사 결과에 따라 `(sourceProjectId, artifactId)` locator를 저장한다. 후보 API는 path/URL/uri를 제거하고, 서버가 소유권·artifact 종류·로컬 파일 존재를 다시 검증한다. Angular는 owned/source에만 lazy picker와 권리 확인, 연결/해제를 제공하며 search/generated/provider/render는 여전히 비범위다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_IMPLEMENTATION_PLAN_2026-07-16.md`

여덟 번째 vertical slice는 search/generated route마다 provider-neutral `asset-acquisition.v1`을 만든다. provider-specific prompt나 model을 저장하지 않고 요청 전·대기·처리·성공·실패·취소와 retryability만 고정했다. 기존 로컬 owned/source project artifact는 search에 image/video, generated-image에 image, generated-video에 video 범위로 명시적 manual replacement가 가능하다. binding mode와 resolver reason으로 planned origin과 수동 대체를 구분하고, 대체를 해제해도 원 acquisition 상태를 보존한다. Angular는 상태와 대체 picker만 보여주며 실제 provider 실행·재시도·render control은 없다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_IMPLEMENTATION_PLAN_2026-07-16.md`

아홉 번째 vertical slice는 대표 45초 AssetPack을 production 계약 모양의 synthetic project-artifact refs로 채우고 `asset-production-readiness.v1` gate를 추가했다. planned local 7개, generated-image manual replacement 1개, programmatic 1개가 해결되고 search 1개만 provider-required로 남아 waiting이 된다. 마지막 search까지 수동 대체하면 ready, non-retryable failure나 succeeded-without-binding은 blocked다. Angular는 해결·로컬·Provider·차단 summary를 보여주지만 render control은 여전히 없다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_IMPLEMENTATION_PLAN_2026-07-16.md`

열 번째 vertical slice는 현재 Supertonic 계약을 다시 감사하고 cue-level measured TTS alignment를 추가했다. Python plugin은 WAV 경로만 반환하고 Nest가 전체 duration/checksum을 계산하므로 word timestamp인 것처럼 다루지 않는다. 모든 narration cue의 artifact id/checksum/text fingerprint/duration이 정확히 맞을 때만 Scene/Beat/Shot/Layer를 재배치한다. 대표 45초 plan은 41.2초 `tts_aligned`가 되며, 실패하면 estimated plan을 부분 변경 없이 유지한다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_IMPLEMENTATION_PLAN_2026-07-16.md`

열한 번째 vertical slice는 Director 전용 Supertonic narration artifact materialization과 voice/speed 재생성을 연결했다. cue별 WAV를 순차 생성하고 opaque artifact metadata만 project에 저장하며, 모든 cue 성공 뒤에만 plan과 pack을 원자적으로 교체한다. 재생성은 직전 aligned timing이 아니라 저장된 estimated baseline에서 다시 시작한다.

열두 번째 vertical slice는 `tts_aligned VideoPlan + renderable AssetPack + ready narrationAudio`를 기존 `render-recipe.v1`로 결정적으로 컴파일한다. 새 renderer가 없으므로 compile endpoint는 read-only preview이고 기존 renderer가 recipe를 자동 claim하지 않는다.

열세 번째 vertical slice는 `diagram.sequence-card.v1`의 normalized motion, deterministic sampler와 5개 reference frame을 만들고 Angular 9:16 inspector가 같은 RenderRecipe 값을 소비하게 했다.

열네 번째 vertical slice는 diagram semantic copy 소유권을 VideoPlan Layer로 확정했다. `content`는 headline, `programmaticPayload`는 `context/evidence/action` exact copy를 소유한다. 새 web draft는 이를 필수로 검증하고 renderer/compiler는 새 문구를 만들지 않는다. `상황/확인/행동`은 payload가 없는 기존 저장 plan에만 적용되는 compatibility fallback이다.

열다섯 번째 vertical slice는 렌더 직전 파일 경계를 추가했다. 현재 project를 strict compile한 뒤 RenderRecipe가 실제 소비하는 visual과 narration 파일을 다시 열어 owner/artifact/media kind/size/checksum을 검증하고, 임시 directory 복사와 재검증 뒤 immutable local stage로 rename한다. 새 binding은 bind 시점 snapshot을 저장하고 기존 snapshot 없는 AssetRef는 manifest metadata 또는 현재 content checksum으로 호환한다. Angular는 recipe를 먼저 확인한 경우에만 `렌더 입력 고정`을 제공하며 summary만 표시하고 renderer/provider/queue/operation은 실행하지 않는다.

열여섯 번째 vertical slice는 renderer 선택 전에 private 실행 경계를 고정했다. immutable stage private manifest가 checksum으로 봉인된 exact RenderRecipe를 함께 보관하고, renderer adapter에는 public path나 원본 ProjectManifest 대신 `sourceId → staged input`만 해소하는 execution bundle을 전달한다. Director 전용 registry는 claim/availability/explicit id를 검증하지만 production adapter는 0개이며 기존 generic VideoRenderProvider를 자동 포함하지 않는다. future JobsService에는 recipe/path 원문 대신 stage/recipe checksum과 adapter id만 가진 opaque job reference를 저장하고, waiting/starting/running은 `active-job`, failed/cancelled는 `retry-source`, completed는 `completed-source`로 retention class를 고정했다. 실제 queue executor, render API/UI, cleanup worker와 renderer/provider 실행은 아직 추가하지 않았다.

열일곱 번째 vertical slice는 renderer 후보가 생기기 전에 동일 비교 기준을 코드로 고정했다. private execution bundle에서 path 없이 deterministic conformance profile과 staged-input fingerprint를 만들고, 대표 41.2초 recipe의 input/output/timeline/capability와 sequence-card 5개 semantic motion checkpoint를 acceptance로 만든다. candidate report는 adapter revision과 동일 environment의 elapsed/output bytes/optional peak RSS를 기록하지만 성능 threshold나 순위에는 쓰지 않는다. 자동 gate를 통과해도 기존 수동 7축이 정확히 한 번씩 모두 pass해야 최종 accepted이며 평균·가중치·100점 총점은 만들지 않았다. production adapter, renderer harness, API/UI와 실제 영상 실행은 여전히 없다.

열여덟 번째 vertical slice는 current Angular/Nest/Electron/Python packaging과 공식 문서를 기준으로 renderer 역할을 나눴다. Remotion을 layered media/text/caption과 Node progress/cancel 적합성이 가장 높은 첫 비프로덕션 범용 합성 PoC로 두고, Motion Canvas는 vector diagram 강점이 필요하거나 Remotion packaging/license/quality gate가 실패할 때 두 번째 후보로 둔다. 기존 app-managed FFmpeg/ffprobe는 main quality compositor가 아니라 final probe, thumbnail과 필요한 mux/normalize 역할을 유지한다. Manim은 final render 중 즉석 호출하지 않고 complex technical diagram을 checksummed artifact로 먼저 materialize해 AssetPack과 immutable stage에 포함시키는 전문 renderer 후보로 고정했다. 첫 PoC에서는 Angular에 React Player를 넣지 않고 같은 RenderRecipe와 motion contract를 Angular preview와 Remotion final/still render가 각각 소비한다. dependency 설치, harness 구현과 실제 renderer 실행은 아직 하지 않았다.

열아홉 번째 vertical slice는 Nest root와 분리된 nested Remotion `4.0.489`/React `19.2.7` package와 representative benchmark harness를 구현했다. 실제 synthetic PNG 4, H.264 MP4 2, WAV 7을 size/checksum으로 다시 staging하고 loopback-only resolver를 통해 41.2초, 30fps, 1080×1920 full MP4와 sequence-card checkpoint still 5개를 만들었다. raw Remotion video는 41.2초였지만 AAC/container가 41.258667초로 한 frame tolerance를 넘었고, 이를 video duration으로 숨기지 않고 조건부 FFmpeg finalizer가 video copy + audio trim/re-encode + remux하도록 했다. 최종 video/audio/container는 모두 41.2초이며 staged input/output/timeline/motion/benchmark 자동 check 7개가 모두 pass했다. progress는 `0 → 1`, AbortSignal cancel은 2%에서 partial output 없이 종료됐다. Korean clipping/mobile safe-zone/motion state spot check는 이상이 없었지만 synthetic media이므로 manual 7축은 `pending`이며 production adapter는 계속 0개다.

추가 정본:

- `.codex/design/SHORTFORM_DIRECTOR_NARRATION_AUDIO_MATERIALIZATION_AND_REGENERATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_CONFORMANCE_AND_BENCHMARK_ACCEPTANCE_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_DECISION_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_IMPLEMENTATION_PLAN_2026-07-16.md`

## 단계적 구현 제안

### Phase 0 — Benchmark와 현재 코드 감사

- 대표 use case와 동일 source pack으로 비교 샘플을 만든다.
- NotebookLM 출력의 shot, motion, typography, diagram, audio cue를 프레임 단위로 분해한다.
- 현재 Angular/NestJS/Python/FFmpeg의 생성·편집·렌더 계약과 소유권을 코드 기준으로 그린다.

### Phase 1 — Grounded brief와 timeline IR

- 독립 `shortform_director` 안에서 BrandProfile, CampaignBrief, SourcePack, MarketContext 계약을 정의한다.
- `PlanningContext → ContentStrategy → VideoPlan → Scene → Beat → Shot → Layer` 계약을 확장한다.
- 기존 `shortform_prompt` clips는 migration하지 않고 별도 제품 경계로 유지한다.

### Phase 2 — 프로그램 모션 중심 PoC

- 현재는 Supertonic cue별 measured WAV duration으로 큰 구간을 정렬하고, 실제 word/sentence timestamp 계약이 생기면 자막·kinetic text·도식·SFX의 세부 동기화를 확장한다.
- 실제/검색 에셋에 camera motion과 layered composition을 적용한다.
- 생성형 영상 없이도 현재 대비 품질 상승 폭을 먼저 측정한다.

### Phase 3 — 생성 이미지·영상 라우터

- 동일 shot spec으로 open model과 commercial API를 평가한다.
- 품질이 기준 미달이면 상용 API로 fallback한다.
- cost cap, timeout, retry, cache, provenance와 manual replacement를 포함한다.

### Phase 4 — Vira 기반 캠페인 대량 생성

- 활성 Shorts 관측·또래 성장 신호·완료된 8차원 분석을 lifecycle policy에 따라 ContentStrategy로 변환한다.
- legacy 포맷·훅·Viral Score는 재활성화/이식 전까지 기본 입력에서 제외한다.
- 한 brief에서 수십·수백 개의 content matrix와 variation을 생성한다.
- 중복, 브랜드 위반, 사실 불일치, 낮은 품질 결과를 사전 제거한다.

### Phase 5 — ViewX 성과 폐루프

- 생성 가설과 실제 성과를 연결한다.
- Vira 분석과 다음 Clipper 생성 우선순위에 결과를 환류한다.
- 단순 조회수 최적화가 아니라 캠페인 목적별 지표를 사용한다.

## 다음 세션에서 먼저 확정할 것

1. 구현된 grounded ContentStrategy/native VideoPlan/대표 eval/AssetPack/project-artifact binding diff와 두 10 credit 초기 policy를 리뷰한다.
2. 구현된 Director 전용 Supertonic materialization과 `VideoPlan + AssetPack + narrationAudio → RenderRecipe` compiler diff를 리뷰한다.
3. 구현된 `diagram.sequence-card.v1` normalized motion contract와 5개 deterministic reference-frame preview를 리뷰한다.
4. 구현된 VideoPlan-owned diagram `programmaticPayload`와 legacy-only fallback을 리뷰한다.
5. 구현된 immutable stage/private execution bundle/adapter registry/conformance profile diff를 리뷰한다.
6. 구현된 isolated Remotion representative harness와 조건부 FFmpeg finalization diff를 리뷰한다.
7. source revision fingerprint 기반 composition bundle cache/reuse와 child-process peak RSS 측정을 추가한다.
8. 실제 representative asset/audio로 full MP4와 5개 checkpoint still의 manual 7축을 검토한다.
9. Electron `extraResources` packaged smoke, offline startup, Windows x64와 supported macOS 범위를 검증한다.
10. Remotion license/Automator 비용과 packaging/quality gate를 통과한 뒤에만 production private adapter 후보로 승격하고, 실패 시 Motion Canvas PoC를 진행한다.
11. 선택 뒤 기존 JobsService executor/API/UI 연결을 별도 vertical slice로 구현한다.
12. 실제 acquisition adapter의 operation/materialization 경계와 provider benchmark를 별도 범위로 설계한다.
13. complex technical diagram 요구가 생기면 Manim 선행 materialization 계약과 PoC를 별도 범위로 설계한다.
14. 실제형 비밀 없는 Vira exporter/API snapshot identity/auth 계약을 별도 범위로 설계한다.

## 아직 결정하지 않은 항목

- Remotion을 production 범용 renderer로 채택할지와 Company License 적용 여부
- Remotion packaged browser/compositor 공급 방식, 앱 크기와 minimum supported macOS 범위
- renderer process를 Electron이 소유할지 Nest child worker로 둘지
- Remotion gate 실패 또는 실제 비교 필요 시 Motion Canvas PoC를 수행할지
- Manim materializer를 별도 Python plugin으로 둘지와 transparent video/image sequence 출력 형식
- 생성 이미지·영상 provider와 fallback 순서
- BGM/SFX source와 라이선스 정책
- native VideoPlan 도입 뒤 clip을 편집 projection으로 유지할 기간과 migration 방식
- cloud generation과 local packaged runtime의 책임 경계
- 대량 생성 작업의 queue, quota, 과금과 재시도 정책
- Vira·Clipper·ViewX 간 자동 연동 API와 데이터 SoT
- Vira의 legacy Market/Viral 자산을 폐기할지 `shorts_*` 위에 재구현할지
- `/intel/Tmarket`을 정식 active signal로 승격할지
- 8차원 분석 compact projection과 현재 제품에서의 trigger 경로
