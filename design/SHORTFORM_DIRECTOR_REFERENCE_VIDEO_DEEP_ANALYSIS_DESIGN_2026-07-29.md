# AI 숏폼 디렉터 — YouTube 레퍼런스 영상 정밀 분석 설계

- 작성일: 2026-07-29 KST
- 상태: 사용자 승인
- 대상 레포:
  - `desktop/clipper_angular`
  - `desktop/clipper_nestjs`
  - `web/clipper_web_api`
- 관련 정본:
  - `.codex/design/2026-07-27-shortform-director-quality-input-lineage-and-production-design.md`
  - `.codex/design/SHORTFORM_DIRECTOR_PRODUCTION_MODEL_AND_SCENE_REVISION_DESIGN_2026-07-28.md`
- 성격: 기존 품질 입력 설계의 YouTube 수집·분석 구간을 구체화하고 일부 수량 결정을
  대체하는 증분 설계

## 1. 결정 요약

조사 단계의 YouTube 처리는 다음 두 단계로 분리한다.

```text
가벼운 후보 탐색
  → 최종 후보 최대 6개
  → 추천 3개 자동 선택
  → 사용자 확인·교체
  → 예상 호출·비용 승인
  → 선택한 실제 영상 3개를 각각 정밀 분석
```

핵심 결정은 다음과 같다.

1. 처음부터 YouTube 영상 수십 개를 정밀 분석하지 않는다.
2. YouTube 검색 결과는 실행 전체에서 최종 최대 6개만 후보로 노출한다.
3. AI가 관련성·최신성·성과·다양성을 기준으로 3개를 추천한다.
4. 사용자는 정밀 분석 전에 나머지 후보로 교체할 수 있다.
5. 실제 유료 호출 전에 선택 영상, 모델, 호출 수와 예상 최대 비용을 보여주고 승인받는다.
6. 정밀 분석은 영상마다 독립된 Gemini 호출 한 번으로 실행한다.
7. Gemini에는 실제 공개 YouTube 영상을 video input으로 전달한다.
8. 자막·FFmpeg 전체 프레임 분석·주요 프레임을 함께 사용해 빠른 컷과 화면 문구를
   보완한다.
9. 세 영상 중 하나라도 분석되지 않았으면 세 영상 공통 패턴을 종합하지 않는다.
10. 분석 결과의 모든 시간·근거 ID는 로컬에서 검증한 뒤에만 게시한다.
11. 영상에서 말한 주장과 외부 자료로 확인된 사실을 분리한다.
12. 원본 영상은 조사·형식 분석용이며 제작 영상의 미디어 소재로 자동 재사용하지 않는다.
13. 이 조사·분석 실행은 Clipper 크레딧 operation을 만들거나 크레딧을 차감하지 않는다.

이 문서는 기존
`2026-07-27-shortform-director-quality-input-lineage-and-production-design.md`의
`형식 분석 대상은 통과 결과 중 20~30개` 결정을 대체한다. 초기 제품 검증 범위는
**후보 최대 6개, 정밀 분석 정확히 3개**다.

## 2. 문제와 현재 상태

현재 구현된 `youtube-reference-analysis`는 실제 영상을 입력하지 않는다. YouTube Data
API로 얻은 제목·설명·통계·댓글을 텍스트로 정규화한 뒤 Gemini에 전달한다.

따라서 현재 구현은 다음 항목을 실제로 판단할 수 없다.

- 첫 화면과 첫 동작
- 빠른 점프컷
- 화면에 잠깐 나타나는 자막·그래픽
- 인물의 자세·표정·카메라 구도
- 음성과 화면 변화의 동기
- 실제 영상의 장면 구조와 편집 리듬

또한 현재 Gemini 호출은 여러 영상을 담을 수 있는 큰 공용 스키마를 사용하다
`400 INVALID_ARGUMENT`로 실패했다. 새 경로는 이 호출을 재사용하지 않는다.

- 입력은 한 번에 영상 한 개다.
- 목적은 `reference-video-deep-analysis`로 좁힌다.
- 응답 스키마는 영상 한 개의 분석 결과만 표현한다.
- 실제 영상이 처리되지 않으면 메타데이터만으로 성공한 것처럼 대체하지 않는다.

## 3. Revid 벤치마크

### 3.1 가져올 것

Revid의 검색·정밀 분석 UX에서 다음을 벤치마킹한다.

- 영상 성과 지표가 있는 검색 결과 표
- 영상별 형식·분위기·촬영 방식 태그
- `왜 효과가 있었나` 설명
- spoken hook과 visual hook의 분리
- 재사용 가능한 hook formula
- scroll-stopper
- story structure
- common belief / contrarian reality
- replicate this
- 제작에 전달할 수 있는 구조화된 패턴

### 3.2 그대로 가져오지 않을 것

Revid 출력은 제작자에게 빠르게 영감을 주는 데 최적화되어 있지만 다음 한계가 있다.

- 영상 길이보다 뒤의 structure timestamp가 생성될 수 있다.
- 조회 성과와 편집 방식의 인과관계를 단정할 수 있다.
- `Exceptional` 같은 평가의 비교 기준이 공개되지 않는다.
- 영상 속 제작자의 말을 검증된 사실처럼 취급할 수 있다.
- 원본 문장이나 연출을 지나치게 가깝게 재사용할 위험이 있다.

AI Director는 결과의 매력적인 설명보다 검증 가능한 계보를 우선한다.

### 3.3 AI Director의 차별점

Revid형 영상 분석은 `Reference` 입력이다. AI Director의 전체 조사는 다음 세 종류를
계속 함께 사용한다.

- Google Trends RSS·네이버 DataLab: 검색 관심과 변화
- 네이버 뉴스·공식 자료: 현재 사건과 사실 확인
- YouTube: 주제 반응, 시청자 반응, 실제 영상 형식

YouTube 레퍼런스 분석 결과만으로 최신 주제나 사실을 확정하지 않는다.

## 4. 수량과 검색 정책

### 4.1 원시 검색 범위

초기 구현은 YouTube Data API 검색을 다음 두 lane으로 제한한다.

| lane | 정렬 | 목적 | 요청 결과 상한 |
|---|---|---|---:|
| current-popular | `viewCount` | 최근 기간의 성과가 큰 영상 | 6 |
| current-relevant | `relevance` | 운영 프로필·검색어와 밀접한 영상 | 6 |

QueryPlanner는 이 두 호출에 사용할 YouTube query를 각각 하나만 만든다. 하나의 lane을
여러 확장 검색어로 반복 호출하지 않는다.

두 lane에서 최대 12개의 원시 결과를 확인하고 다음 기준으로 중복·부적합 항목을 제거한
뒤 최종 후보 최대 6개를 만든다.

- video ID 중복
- 제목·채널·내용이 사실상 같은 재업로드
- 공개 접근 불가
- 3분 초과
- 조사 시점 기준 최신성 범위 밖
- 운영 프로필 및 조사 query와 관련성 부족
- 한 채널이 후보를 과도하게 점유

수십 개의 `videos.list` 결과나 댓글을 먼저 쌓아두지 않는다. `videos.list`는 최대 12개의
원시 video ID를 한 batch로 확장하고, 댓글은 최종 후보 또는 선택된 3개에만 호출한다.

### 4.2 후보가 부족한 경우

- 적격 후보가 6개 미만이어도 가짜 후보를 채우지 않는다.
- 3~5개면 실제 개수를 그대로 표시하고 그중 3개를 추천한다.
- 적격 후보가 3개 미만이면 Gemini 호출 전에 `insufficient`로 중단한다.
- 검색 기간을 자동으로 오래된 범위까지 늘려 최신성 기준을 훼손하지 않는다.

### 4.3 추천 3개

추천은 다음 값을 구성 요소별로 보존한다.

- query 관련성
- 게시 후 시간당 조회수
- `(좋아요 + 댓글) / 조회수`
- 게시 시각과 최신성
- 검색 결과 집합 안의 상대 성과
- 채널 다양성
- 영상 길이와 숏폼 적합성

단일 `viralScore`만 저장하지 않고 각 구성 요소와 추천 이유를 함께 저장한다.

YouTube Data API가 제공하지 않는 공유 수는 `0`으로 만들지 않고 UI에 `—`로 표시한다.

## 5. 사용자 흐름

### 5.1 1단계: 시장·영상 후보 탐색

기존 조사 승인 뒤 Google Trends RSS·네이버·YouTube의 가벼운 수집을 실행한다.
YouTube 구간은 실제 영상 정밀 분석 전에 멈춘다.

완료 상태:

```text
ResearchRun.status = awaiting_reference_selection
```

화면에는 최대 6개의 후보가 표시된다.

- 썸네일
- 제목·채널
- 게시 시각
- 길이
- 조회수·좋아요·댓글
- 참여율
- 시간당 조회수
- 해시태그
- 얕은 요약
- 추천 여부와 추천 이유

### 5.2 2단계: 정밀 분석 대상 확인

AI가 추천한 3개가 기본 선택되어 있다.

- 사용자는 선택을 해제하고 다른 후보를 선택할 수 있다.
- 선택 수는 정확히 3개여야 한다.
- 후보가 3개뿐이면 세 개가 자동 선택된다.
- 이미 정밀 분석한 후보는 결과를 재사용한다.

### 5.3 3단계: 비용 승인

`정밀 분석 시작` 전에 다음을 표시한다.

- 선택한 영상 3개
- 각 영상 길이
- provider와 model
- Gemini 영상 분석 3회
- 자막 부재 시 기존 로컬 `faster-whisper-small` STT 최대 3건
- 세 영상 종합 1회
- 예상 입력·출력 토큰과 비용 범위
- 가격 기준일

사용자가 승인하기 전에는 실제 Gemini 영상 분석과 음성 인식을 호출하지 않는다.

### 5.4 4단계: 분석과 후속 종합

승인 뒤 영상마다 독립 작업을 실행한다.

```text
video A: acquire → analyze → validate → persist
video B: acquire → analyze → validate → persist
video C: acquire → analyze → validate → persist
```

세 영상 모두 성공하면 공통 패턴을 종합하고 Topic 생성으로 진행한다.

사용자는 완료 후에도 나머지 후보의 `정밀 분석`을 실행할 수 있다. 이 경우 해당 영상
한 개의 예상 비용을 다시 보여주고 승인받으며 기존 결과를 덮어쓰지 않는다.

## 6. 영상별 정밀 분석 데이터 흐름

```text
YouTube candidate
  ├─ yt-dlp metadata
  ├─ yt-dlp video download/cache
  ├─ creator/auto caption fetch
  ├─ ffprobe media facts
  ├─ FFmpeg scene boundary analysis
  ├─ FFmpeg keyframe extraction
  └─ caption 부재 시 대사 하이라이트의 기존 로컬 STT 재사용
              ↓
ReferenceAnalysisInput
  ├─ public YouTube video URI
  ├─ timestamped transcript
  ├─ deterministic cut timeline
  ├─ selected keyframes
  ├─ metadata/metrics/comments
  └─ operating-profile context
              ↓
Gemini 3.6 Flash Interactions API
              ↓
parsed ReferenceVideoAnalysis
              ↓
local validators
              ↓
published reference pattern
```

### 6.1 실제 영상 입력

Web API가 보관 중인 Gemini credential을 사용해 공개 YouTube URL을 Gemini Interactions
API의 `video` input으로 전달한다. API key는 desktop으로 반환하지 않는다.

- 영상마다 요청 한 번
- 한 요청에 영상 한 개
- `gemini-3.6-flash`
- default media resolution
- compact per-video output schema
- Google Search grounding 미사용

공개 URL 입력이 실패하면 desktop의 다운로드 파일을 자동으로 Web API에 올리는
fallback은 초기 범위에 넣지 않는다. 실패 이유를 남기고 남은 후보로 교체한다.

### 6.2 자막과 음성

1. 제작자 자막
2. YouTube 자동 자막
3. 자막 부재 시 대사 하이라이트 플러그인의 기존 로컬
   `faster-whisper-small` STT

순서로 사용한다.

제작자·자동 VTT 자막은 cue별 `startMs`, `endMs`, `text`를 가진다. 로컬 STT는 이미
`stt_worker.py`에서 `word_timestamps=True`로 실행되며 실제 segment와 word의
시작·종료 시간을 저장한다. AI Director가 별도 STT 구현이나 Web API 전사 endpoint를
추가하지 않고 이 결과를 같은 transcript 계약으로 정규화한다. Gemini가 영상의 음성을
직접 처리하더라도 별도 transcript를 직접 문구 검증 근거로 제공한다.

AI Director는 대사 하이라이트의 과금 workflow executor를 호출하지 않는다. 기존
Python 플러그인의 provider-free STT stage를 공통 로컬 플러그인 실행 경계로 호출하므로
크레딧 차감과 외부 API 비용이 없다. 기존 `analyze_media` 전체를 그대로 호출하면
이 단계에 불필요한 OpenCLIP·audio embedding까지 실행되므로, 같은 `run_stt`를 호출하는
좁은 `transcribe_media` stage로 노출한다.

### 6.3 장면 전환

FFmpeg는 다운로드한 전체 영상을 처음부터 끝까지 디코딩해 인접 프레임의 변화량을
계산한다. 다음은 LLM이 아니라 로컬 계산값이다.

- cut timestamp
- change score
- shot duration
- 첫 3초의 cut 수
- 평균·중앙 shot 길이
- 가장 긴 정지 구간

### 6.4 주요 프레임

영상당 최대 24장을 추출한다.

- 0초, 0.5초, 1초, 2초, 3초
- 장면 전환 직전·직후
- 변화 점수가 큰 장면
- 중간 핵심 구간
- 마지막 CTA 구간

첫 3초와 마지막 구간은 반드시 포함한다. 24장을 넘으면 변화 점수와 시간 분포를 함께
사용해 선택한다.

24장은 로컬 근거 열람용 상한이다. Gemini 요청에는 이 중 첫 3초, 가장 큰 장면 변화,
화면 문구와 마지막 CTA를 대표하는 최대 12장만 전달한다. 각 이미지는 Web API의 전용
DTO 크기 제한을 통과한 JPEG로 축소하고 원본 frame ID와 timestamp를 함께 전달한다.

### 6.5 Gemini의 책임

Gemini는 다음 해석을 담당한다.

- spoken hook
- visual hook
- hook formula
- scroll-stopper
- 내용 형식과 전개 방식
- common belief / contrarian reality
- 장면별 의미와 역할
- pattern interrupt와 visual reset
- 화면 문구의 기능
- 재사용 가능한 제작 패턴
- 관찰 한계와 confidence

정확한 컷 수, 영상 길이, transcript timing은 Gemini 출력보다 로컬 측정값을 우선한다.

## 7. 분석 결과 계약

```ts
interface ReferenceVideoAnalysisV1 {
  schemaVersion: 'shortform-director-reference-video-analysis.v1';
  id: string;
  researchRunId: string;
  videoId: string;
  sourceEvidenceId: string;
  durationMs: number;
  generatedByCallId: string;

  hook: {
    category: string;
    qualityLabel: 'exceptional' | 'strong' | 'ordinary' | 'weak';
    spokenText?: string;
    visualDescription: string;
    screenText?: string;
    formula: string;
    promise: string;
    curiosityGap?: string;
    evidenceRefs: string[];
  };

  scrollStopper: {
    description: string;
    evidenceRefs: string[];
  };

  mechanics: Array<{
    type:
      | 'listicle'
      | 'pattern-interrupt'
      | 'curiosity-stacking'
      | 'rapid-pacing'
      | 'visual-reset'
      | 'proof'
      | 'transformation'
      | 'contrarian-framing'
      | 'other';
    reasoning: string;
    evidenceRefs: string[];
  }>;

  beliefContrast?: {
    commonBelief: string;
    contrarianReality: string;
    evidenceRefs: string[];
  };

  structure: Array<{
    role: 'hook' | 'build' | 'proof' | 'payoff' | 'cta' | 'other';
    startMs: number;
    endMs: number;
    summary: string;
    evidenceRefs: string[];
  }>;

  pacing: {
    cutCount: number;
    cutsInFirst3Seconds: number;
    medianShotLengthMs: number;
    longestStaticSectionMs: number;
    interpretation: string;
  };

  onScreenTexts: Array<{
    text: string;
    startMs: number;
    endMs: number;
    role: string;
    evidenceRefs: string[];
  }>;

  videoClaims: Array<{
    text: string;
    transcriptRefs: string[];
    verificationStatus: 'verified' | 'unverified' | 'contradicted';
    verifiedEvidenceRefs: string[];
  }>;

  reusablePattern: {
    format: string;
    hookFormula: string;
    structureRoles: string[];
    productionNotes: string[];
    prohibitedCopyElements: string[];
  };

  confidence: 'high' | 'medium' | 'low';
  limitations: string[];
  validation: {
    passed: boolean;
    issues: string[];
  };
}
```

`qualityLabel`은 조회수만으로 정하지 않는다. 같은 검색 결과 집합의 성과, 게시 후 경과
시간과 채널 편향을 함께 사용하며 UI에서 기준을 확인할 수 있어야 한다.

## 8. 로컬 검증

Gemini 출력은 다음 검증을 통과해야 한다.

1. 모든 timestamp가 `0 <= timestamp <= durationMs` 범위다.
2. structure의 `startMs < endMs`다.
3. structure 구간은 겹치지 않고 시간순이다.
4. hook과 scroll-stopper에는 transcript·frame·scene 근거가 있다.
5. 모든 evidence reference가 실제 저장 artifact를 가리킨다.
6. Gemini가 생성한 cut 수가 아니라 FFmpeg 측정값을 사용한다.
7. 영상에서 들리지 않은 문장을 spoken hook의 직접 문구로 기록하지 않는다.
8. 영상 속 주장은 외부 검증 전까지 `unverified`다.
9. 세 영상 종합은 검증 통과한 분석 세 개만 입력으로 받는다.
10. provider 실패를 빈 분석 결과나 fixture로 대체하지 않는다.

검증 실패 결과는 삭제하지 않고 `rejected-analysis.json`과 failure artifact에 보존한다.

## 9. 세 영상 종합

세 분석이 모두 통과한 뒤 텍스트 전용 종합 호출을 한 번 실행한다.

입력:

- 세 `ReferenceVideoAnalysisV1`
- 세 영상의 성과 구성 요소
- 운영 프로필
- 같은 research run의 Market·Audience signal

출력:

- 반복되는 hook formula
- 서로 다른 format과 angle
- 반복되는 visual reset과 pacing 패턴
- 현재 주제에서 과포화된 표현
- AI Director가 재사용할 수 있는 구조
- 원본을 복제하지 않기 위한 금지 요소
- 어떤 패턴이 어떤 evidence에 근거하는지

이 결과는 `reference-patterns.json`에 저장되고 Topic과 영상 후보 생성의 Reference 입력이
된다. 영상 후보는 여전히 선택 Topic마다 최소 10개를 생성한다. `레퍼런스 영상 3개`와
`제작할 영상 후보 10개 이상`은 서로 다른 개념이다.

## 10. 비용과 호출 상한

Gemini 3.6 Flash의 2026-07-29 기준 Standard 가격:

- input: USD 1.50 / 1M tokens
- output 및 thinking: USD 7.50 / 1M tokens

Google의 기본 영상 토큰 계산은 약 300 tokens/second다.

40초 영상 하나의 계획 상한:

| 항목 | 예상 |
|---|---:|
| video input | 약 12,000 tokens |
| prompt·transcript·보조 입력 | 약 2,000~8,000 tokens |
| output·thinking | 약 1,500~4,000 tokens |
| 예상 비용 | 약 USD 0.03~0.06 |

세 영상:

- Gemini deep analysis: 3회
- 로컬 STT: 자막 부재 영상에만 최대 3건, 외부 API 호출·USD 비용 없음
- cross-video synthesis: 1회
- 예상 Gemini deep analysis 합계: 약 USD 0.09~0.18

가격은 catalog의 기준일과 함께 표시하고 실제 완료 뒤 provider usage로 실비를 기록한다.
가격표가 없거나 모델이 바뀌면 비용 승인을 진행하지 않는다.

## 11. 컴포넌트 경계

### 11.1 `clipper_nestjs`

- `ReferenceCandidateCollector`
  - source fetch 결과에서 최대 6개 후보 구성
- `ReferenceCandidateRanker`
  - 추천 3개와 구성 점수 생성
- `ReferenceSelectionService`
  - 사용자 선택·교체와 snapshot 저장
- `ReferenceMediaPreprocessor`
  - 기존 `SourceService`, yt-dlp, FFmpeg, ffprobe 재사용
- `ReferenceAnalysisOrchestrator`
  - 영상별 독립 실행, 교체, 세 영상 종합 조율
- `ReferenceAnalysisValidator`
  - timestamp·evidence·duration 검증
- JSON repositories
  - selection, media evidence, call audit, parsed analysis 저장

각 책임은 하나의 거대 research service에 합치지 않는다.

### 11.2 `clipper_web_api`

- 기존 관리자 credential 저장·조회 경계 재사용
- 전용 Gemini video analysis transport
- Gemini Interactions API의 video URI·image·text input
- per-video compact structured output
- 모델 allowlist와 credential revision 검증
- input/output usage와 안전한 provider call metadata 반환
- API key·Authorization·provider raw body 비노출

기존 공용 텍스트 inference DTO에 video input을 억지로 추가하지 않는다.

### 11.3 `clipper_angular`

- 최대 6개 후보 결과 표·카드
- 추천 3개 기본 선택과 교체
- 호출·비용 승인
- 영상별 진행 상태
- 영상별 `왜 효과가 있었나`
- 근거 프레임·자막·장면·provider call 열람
- 완료 후 추가 정밀 분석

## 12. JSON 저장 구조

기존 research run 아래에 다음을 추가한다.

```text
research-runs/<researchRunId>/
├─ reference-candidates/
│  ├─ candidates.json
│  ├─ recommendation.json
│  └─ selection-revisions/
│     └─ <selectionRevisionId>.json
├─ reference-media/
│  └─ <videoId>/
│     ├─ acquisition.json
│     ├─ media-probe.json
│     ├─ transcript.json
│     ├─ scene-boundaries.json
│     ├─ keyframes.json
│     └─ frames/*.jpg
├─ reference-analyses/
│  └─ <videoId>/
│     ├─ manifest.json
│     ├─ input.json
│     ├─ provider-call.json
│     ├─ analysis.json
│     ├─ validation.json
│     └─ rejected-analysis.json
└─ normalized/
   └─ reference-patterns.json
```

실제 MP4·WAV·JPG는 미디어 파일로 저장하고 JSON에는 경로·checksum·크기·생성 시각을
기록한다. provider 원문 response는 저장하지 않고 파싱·검증한 결과와 사용량·모델·요청
식별 정보만 저장한다. `provider-call.json`에는 prompt template version, 실제 전송한
텍스트 입력, 미디어 reference ID, provider/model, credential revision, usage와 실제
비용을 남기되 base64 media bytes와 credential 값은 남기지 않는다.

## 13. 실패 처리

- 후보 3개 미만: `insufficient`, Gemini 호출 없음
- 비공개·삭제·지역 제한: 남은 후보로 교체 제안
- yt-dlp 다운로드 실패: 해당 후보 실패, 다른 후보 선택
- 자막 없음: 기존 로컬 `faster-whisper-small` STT fallback
- STT 실패: Gemini audio 이해 결과만으로 transcript를 꾸미지 않고 해당 근거를
  `unavailable`로 표시
- Gemini 4xx: safe provider code 저장, 자동 재시도 없음
- Gemini 429·5xx: 사용자가 승인한 상한 안에서만 bounded retry
- structured output parse 실패: 한 번의 좁은 repair retry만 허용
- timestamp 검증 실패: 분석 게시 금지
- 세 영상 중 한 개 실패: 공통 패턴 종합 중지, 교체 후보 선택 요청

첫 실패를 숨긴 성공 기록이나 가짜 fixture는 만들지 않는다.

## 14. 검증 계획

### 14.1 단위 검증

- 최대 6개 후보와 최대 12개 원시 ID
- 중복·채널 편향·오래된 영상 제거
- 추천 점수 구성 요소
- 정확히 3개 선택
- 비용 승인 없는 provider 차단
- transcript 우선순위와 STT fallback
- FFmpeg timestamp projection
- Gemini output validator
- 영상 길이를 넘는 timestamp 거부
- 존재하지 않는 evidence ID 거부
- shares 미제공 시 `null` 유지

### 14.2 통합 검증

- 실제 `SourceService` yt-dlp 캐시 재사용
- 실제 FFmpeg/ffprobe 실행
- desktop → authenticated Web API → Gemini credential 경계
- parsed analysis의 로컬 JSON 저장과 reload
- 세 영상 성공 뒤에만 reference pattern 생성
- Angular 근거·과정에서 저장 artifact 열람

### 14.3 첫 live acceptance

사용자 승인을 받은 최신 주제 한 번으로 실행한다.

성공 조건:

1. 후보가 실제 최신 YouTube 데이터에서 나온다.
2. 추천 3개와 추천 이유가 표시된다.
3. 사용자가 분석 전 영상을 교체할 수 있다.
4. 비용 승인 뒤 영상 세 개가 각각 실제 video input으로 분석된다.
5. 각 분석에서 실제 hook·scroll-stopper·structure·pacing을 확인할 수 있다.
6. 모든 timestamp가 실제 영상 길이 안에 있다.
7. hook과 structure에서 근거 프레임·자막을 열 수 있다.
8. 영상 속 주장과 검증된 사실이 분리된다.
9. 세 분석의 공통 패턴이 Topic·영상 후보 생성에 연결된다.
10. 어떤 단계에서도 runtime fixture·가짜 provider response를 사용하지 않는다.

## 15. 참고 자료

- Gemini video understanding:
  https://ai.google.dev/gemini-api/docs/video-understanding
- Gemini API pricing:
  https://ai.google.dev/gemini-api/docs/pricing
- Revid viral video search:
  https://www.revid.ai/search
- Revid TikTok video finder:
  https://www.revid.ai/tiktok-video-finder
- Revid pattern workflow:
  https://www.revid.ai/blog/how-to-create-viral-content
