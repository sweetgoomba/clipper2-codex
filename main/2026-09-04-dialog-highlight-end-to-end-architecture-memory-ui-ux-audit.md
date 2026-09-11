# 대사 하이라이트 플러그인 End-to-End 구조·메모리·UI/UX 감사

- 작성일: 2026-09-04
- 범위: Desktop Angular, Electron, NestJS, Python 플러그인, Web API
- 목적: 대사 하이라이트의 현재 구현과 최근 메모리 최적화 전후를 보존하고, 내부 구조 및 UI/UX 개선 작업의 기준점으로 사용
- 코드 기준: 각 저장소의 2026-09-04 최신 `origin/dev`; Python 메모리 최적화 도입 이력은 관련 커밋과 회귀 테스트까지 별도 비교

## 1. 핵심 결론

대사 하이라이트는 하나의 AI 모델이 영상을 입력받아 결과를 직접 만드는 단일 파이프라인이 아니다. 로컬에서 영상·음성 신호를 추출하고, Web API가 OpenAI에 문장 구조화·스토리 해석·후보 선택·메타데이터 생성을 요청한 뒤, 로컬 Python 플러그인이 최종 클립을 렌더링하는 하이브리드 파이프라인이다.

최근 메모리 최적화는 크게 두 부분이다.

1. 전체 키프레임을 메모리에 보관하던 리스트 방식을 generator 기반 스트리밍으로 변경했다.
2. Whisper의 전체 오디오 STFT/mel 계산을 약 5분 단위 청크 계산으로 변경했다.

긴 영상에서 메모리 증가 기울기는 product-path 측정 기준 약 `50.8 MB/분`에서 `11.2 MB/분`으로 낮아졌다. 다만 전체 waveform, 최종 mel, 모든 STT segment/word, librosa의 오디오 재로딩은 남아 있으므로 완전한 constant-memory 구조는 아니다.

2026-09-04 조사 당시 원래 `desktop/clipper_python` checkout의 HEAD는 `f8274ac`이고 최신 `origin/dev`의 최적화가 포함되지 않은 상태였다. 후속 개선 작업용 새 worktree는 최신 `origin/dev` `7d9a470`에서 만들었으며 메모리 최적화 merge `3c31ec0`을 포함한다.

## 2. 관련 저장소와 책임

| 저장소 | 책임 |
| --- | --- |
| `desktop/clipper_angular` | 입력, 소스 확인, 크레딧 확인, 작업 시작, 프로젝트 결과·편집 UI |
| `desktop/clipper_electron` | NestJS utility process 및 Python 플러그인 프로세스 시작·중지, 로컬 브리지, 리소스 관측 |
| `desktop/clipper_nestjs` | 작업 큐, 소스 ingest, 파이프라인 오케스트레이션, Python/Web API 호출, 취소·진행률·결과 관리 |
| `desktop/clipper_python` | STT, 무음·장면·시각·오디오 특징 분석, 후보 구간 생성, 최종 렌더링 |
| `web/clipper_web_api` | 크레딧 견적·차감·환불, OpenAI 호출, provider 요청 이력과 operation 상태 관리 |

Web Customer, Web Admin, Infra는 현재 대사 하이라이트의 직접 실행·편집 경로에 참여하지 않는다.

## 3. 런타임 및 프로세스 구조

```text
Angular renderer
  -> local NestJS API
       -> Electron plugin-host bridge
            -> Python FastAPI/Uvicorn plugin
                 -> Whisper / OpenCLIP / OpenCV / librosa
                 -> ffprobe / ffmpeg subprocess
       -> Clipper Web API
            -> OpenAI Responses API
```

패키지 앱에서는 Electron main, Chromium renderer, 로컬 NestJS utility process가 상시 존재하고, Python 플러그인은 준비 또는 작업 시 시작된다. YouTube 처리와 미디어 분석·렌더링 과정에서 `yt-dlp`, `ffprobe`, `ffmpeg`가 일시적인 child process로 생성된다. OpenCV, PySceneDetect, Whisper, OpenCLIP, librosa 계산은 Python 프로세스 내부 작업 스레드에서 수행된다.

Python 플러그인은 개발 모드에서 대략 `uv run --project ... python -m dialog_highlight <port> --idle-timeout 0` 형태로 실행된다. SDK 자체 idle watchdog은 Electron 실행 인자 때문에 비활성화되고, NestJS runtime lifecycle이 유휴 종료를 책임진다.

Python SDK는 HTTP stage job마다 `asyncio.create_task`를 만들고 동기 plugin 코드를 `asyncio.to_thread`로 실행한다. 주요 endpoint는 다음과 같다.

- `POST /jobs`
- `DELETE /jobs/:id`
- `GET /health`
- `GET /runtime/accelerators`
- `WS /jobs/:id/events`
- `POST /shutdown`

종료는 graceful shutdown 요청 후 SIGTERM, 마지막으로 SIGKILL 순서다. CUDA OOM은 runtime OOM과 model-load OOM을 구분해 처리한다.

NestJS의 전역 동시 실행 작업 수는 현재 1이다. 여러 영상은 병렬 분석되지 않고 큐에서 하나씩 실행된다. 소스 준비는 작업 진행률의 첫 10%를 사용하고, 실제 operation은 큐 대기와 소스 준비가 끝난 뒤 시작된다.

## 4. 전체 파이프라인

| 순서 | 단계 | 위치 | 역할 |
| ---: | --- | --- | --- |
| 1 | `prepare_media` | Python | 입력 미디어 검증 및 stage 작업 디렉터리 준비 |
| 2 | `analyze_media` | Python | 길이, 무음, STT, 장면, 시각·오디오 특징 분석 |
| 3 | `sentence_split` | Web API/OpenAI | shot별 끊어진 STT를 문장 단위로 정리 |
| 4 | `story_backbone` | Web API/OpenAI | 5~7개 핵심 사건, 인물, 근거와 전체 이야기 흐름 생성 |
| 5 | `canonical_info` | Web API/OpenAI | STT/OCR 근거만으로 이름·용어 교정 맵 생성 |
| 6 | `define_highlight_topics` | Web API/OpenAI | 서로 다른 시간대의 하이라이트 주제 생성 |
| 7 | `build_candidates` | Python | 문장을 타임라인에 매핑하고 의미 구간 후보 생성 |
| 8 | `select_highlights` | Web API/OpenAI | 후보 ID 중 최종 하이라이트 선정 |
| 9 | `highlight_metadata` | Web API/OpenAI | 제목, 요약, 선정 이유, 교정 정보 생성 |
| 10 | `render_highlights` | Python | 최종 클립 및 썸네일 렌더링 |

Python stage 진행률 구간은 각각 `prepare 0.02~0.08`, `analyze 0.08~0.42`, `build 0.70~0.78`, `render 0.88~0.98`이다. 중간 OpenAI 단계가 두 Python 단계 사이를 채운다.

각 Python stage는 별도 로컬 HTTP job ID를 사용하지만 같은 Python runtime을 재사용한다. 대형 Python 객체를 stage 간 직접 전달하지 않고 다음 파일을 중간 계약으로 사용한다.

- `analysis.json`
- `llm_sentences.json`
- `story_backbone.json`
- `canonical_info.json`
- `topics.json`
- `highlight_candidates.json`
- `gpt_highlight_selection.json`
- `highlights_meta.json`
- `manifest.json`
- `silence`, `stt`, `shots`, `sentence_spans`, `raw_segments`, `semantic_segments`, `semantic_clips`, `clip_stt` 계열 artifact

stage contract에는 재사용 가능한 `transcribe_media`가 선언돼 있지만 현재 제품 NestJS workflow는 호출하지 않는다. `analyze_media`가 이미 STT를 실행한다. stage 없이 예전 단일 Python pipeline을 실행하는 경로는 현재 오류 처리된다.

작업 취소 시 네 개 Python stage ID 모두에 취소 요청을 시도하며, 다른 active job이 없으면 관리 중인 runtime도 정지할 수 있다.

## 5. 소스 준비

### YouTube

공식 YouTube Data API 대신 `yt-dlp`를 사용한다.

입력 화면의 URL 확인은 `yt-dlp --dump-json --skip-download --no-playlist` 형태의 metadata inspect다. 작업이 큐에서 시작되면 source ingest가 metadata를 다시 조회하고, media cache가 없으면 최대 1080p AVC1 MP4 + M4A를 우선해 다운로드하며 필요하면 ffmpeg로 merge한다.

정상적인 cache miss 기준 고수준 `yt-dlp` 실행은 보통 다음 3회다.

1. 입력 화면 metadata inspect
2. 작업 준비 metadata ingest
3. media download

cache hit이면 1·2만 실행한다. 각 `yt-dlp` 프로세스가 실제 YouTube에 보내는 wire-level HTTP 요청 수는 extractor, manifest, 인증과 재시도에 따라 달라져 고정할 수 없다.

일반 metadata 실패는 인증 전략별 최대 2회, media access forbidden 다운로드는 인증 전략별 최대 3회까지 재시도한다. 인증 전략은 무인증 이후 관리 쿠키 또는 브라우저 쿠키 fallback으로 확장될 수 있다.

### 로컬 파일

입력 UI 미리보기와 작업 큐 source prepare가 각각 ingest를 실행한다. 각 ingest는 file stat과 `ffprobe`를 수행하므로 일반적으로 ffprobe가 두 번 실행된다. 첫 ingest에서 thumbnail이 없으면 ffmpeg로 생성하고, 두 번째는 cache hit이면 thumbnail 렌더를 건너뛴다.

Angular store에는 legacy `outputRoot` setter/default가 남아 있지만 작업 제출에는 사용하지 않고, NestJS가 관리되는 data root 아래의 `output_root`를 주입한다.

## 6. 로컬 영상 분석 기술

### STT

- 모델: `Systran/faster-whisper-small`
- 출력: segment와 word-level timestamp
- CUDA: float16
- CPU: int8
- MPS 선택 시 현재 Whisper 경로는 CPU fallback
- 실제 `transcribe` 호출: `vad_filter=False`, `word_timestamps=True`

공통 설정의 `STT_VAD_FILTER=True`는 실제 호출과 일치하지 않는 stale 설정이다.

### 장면 및 무음

- 장면: PySceneDetect `ContentDetector`
- 프레임 샘플링: `frame_skip=2`
- 0.5초 미만 장면 병합
- 무음: ffmpeg `silencedetect`, 약 `-35 dB`, 최소 0.35초

코드에 `CONTENT_THRESHOLD=27` 상수가 있으나 `ContentDetector()`에 전달되지 않아 라이브러리 기본 threshold가 사용된다.

### 시각 특징

- OpenCLIP ViT-B-32, LAION weight
- 현재 shot별 midpoint frame 한 장을 사용
- 프레임 디코딩은 OpenCV로 영상 처음부터 순차 진행
- 인접 shot embedding cosine distance를 visual change로 사용

sampling 함수는 15/50/85%의 세 프레임도 지원하지만 현재 제품 호출은 한 장이다.

### 오디오 특징

- librosa로 전체 오디오를 16 kHz mono로 로드
- shot마다 MFCC 20차원
- 각 차원에서 mean, std, p25, p50, p75를 계산해 100차원 벡터 구성
- 벡터 normalize 후 인접 shot 간 L2 distance를 audio change로 사용

Whisper와 OpenCLIP 모델은 model/device 키로 전역 캐시되어 같은 Python 프로세스가 살아 있는 동안 유지된다.

## 7. 하이라이트 후보 생성 및 선택

### 목표 개수

```text
target_count = clamp(round(duration_seconds / 120), 6, 16)
```

약 2분당 한 개이며, 짧은 영상도 최소 6개를 요구한다.

### 문장 정리

shot별 STT를 LLM sentence split 입력으로 만든다. batch는 target shot 최대 40개, target text 약 2,500자 조건을 동시에 적용하고 각 batch에 앞뒤 2개 shot을 context로 포함한다. batch는 순차 호출되며 target에 해당하는 결과만 병합한다.

### 스토리와 canonical 정보

story backbone은 5~7개 핵심 문장과 event/entity/evidence를 만든다. canonical info는 STT와 현재 비활성인 OCR 근거만 사용하며 외부 검색은 하지 않는다. 확실하지 않은 이름은 `dont_use_names`로 분리한다.

### 주제 생성

LLM은 목표 개수와 같은 수의 주제를 만들고, 서로 다른 시간대·독립적인 내용·원문 STT 표현·25~55초 길이를 요구받는다.

### 문장-시간 매핑

1. shot window 안에서 STT word의 정확한 연속 일치
2. STT segment 문자열 시퀀스의 60% 이상 coverage
3. 아직 사용되지 않은 겹치는 STT segment fallback
4. 무음뿐인 문장 제외

겹치는 cluster는 긴 구간, STT word coverage, text 길이 순으로 선택한다.

### raw segment

cut point는 shot 경계, silence 끝, sentence 경계, 0과 전체 duration의 합집합이다.

- 0.12초 이내 경계 dedup
- 0.35초 미만 segment 제거
- 4.5초 초과 segment는 보호되는 sentence를 훼손하지 않는 범위에서 분할

### semantic merge

- 목표 25초
- 최대 45초
- 최소 3초
- visual difference `> 0.35` 또는 audio difference `> 0.45`이면 즉시 분리
- 25초 이상에서 1초 이내 silence 또는 0.8초 이내 shot end가 있으면 flush

후보 score hint:

```text
0.42 * text words/sec
+ 0.30 * visual peak
+ 0.18 * audio peak
+ 0.10 * boundary clarity
```

boundary clarity는 끝점 부근 2초 안의 silence 여부에 따라 0, 0.5, 1이다. 각 신호를 하나의 공통 scale로 정규화하지 않기 때문에 text density가 상대적으로 크게 작용할 수 있다. 이 점수는 최종 규칙이 아니라 LLM 힌트다.

### LLM 최종 선택

각 candidate는 range, ID, score, 문장 ID, 주변 문맥, 최대 3,000자 STT, 최대 1,500자 OCR을 포함한다. LLM은 완결성, 비중복성, 흥미도, 정보성, 감정성을 기준으로 candidate ID를 선택한다.

metadata 단계는 선택된 candidate에 대해 2줄 overlay, summary, reason, corrections를 생성한다.

### 경계 보정과 fallback

렌더 직전 metadata 범위를 첫 sentence 경계로 snap하고 다시 shot 경계 ±2초로 snap한다. 두 번째 shot snap이 첫 sentence snap을 일부 되돌릴 수 있다. 이후 25~55초 범위를 강제하고 끝에 0.25초 tail을 더한다.

metadata가 비었거나 유효하지 않으면 선택 candidate ID를 사용하고, 그것도 없으면 시간순 첫 semantic segment를 사용한다. fallback은 최고 score 순서가 아니다. story continuity fallback은 영상 시작 8초 이내 후보를 제거하고 큰 간격을 메우며, target 35초·최소 25초·최대 55초·최대 gap 3초 clip을 조립한다. 최종 NMS IoU 기준은 0.35다.

공통 상수 `EVENT_MIN=10`은 legacy이며 실제 후보와 렌더링은 최소 25초를 명시한다.

## 8. 렌더링

- 출력: 1080×1920, 9:16
- 원본 비율: crop하지 않고 contain + padding
- 제목: 상단 2줄, 녹색 `#12ff31`, 대략 y=240, size 82
- 비디오: H.264, preset veryfast, CRF 20, yuv420p
- 오디오: AAC
- faststart 사용
- 클립별 1초 지점 thumbnail 별도 생성

최종 자막 텍스트는 선택 구간과 겹치는 word/segment에서 다시 구성한다.

최종 클립 수를 N이라 하면 렌더링 ffmpeg 1회와 thumbnail ffmpeg 1회씩, 총 `2N` subprocess가 실행된다. 목표 개수 6~16 기준 12~32회다.

## 9. 외부 호출과 호출 횟수

### OpenAI

OpenAI 호출은 Python이나 데스크톱이 직접 하지 않고 Web API가 수행한다. credential은 Web API DB에서 암호화 관리되며 데스크톱에 전달하지 않는다.

- endpoint: OpenAI Responses API
- 기본 모델: `gpt-5-mini`
- story/topics/metadata: medium reasoning, 최대 16k
- 나머지: minimal reasoning, 최대 8k
- Desktop Web API timeout 기본 330초
- Web API timeout은 일반 단계 180초, high 단계 300초
- JSON object 출력

문장 분할 batch 수를 B라 하면:

```text
OpenAI 호출 수 = B + 5
```

고정 5회는 story backbone, canonical info, topics, selection, metadata다. B=1인 일반적인 경우 총 6회다. 호출은 순차다.

Web API 자체는 OpenAI 호출을 재시도하지 않지만 Desktop NestJS client가 OpenAI timeout으로 명확히 판별된 `provider_failed` 또는 desktop의 `web_api_timeout`에 한해 한 번 더 시도한다. 인증 오류, 출력 누락, 계약 위반, 일반 provider failure, 사용자 취소는 재시도하지 않는다. 따라서 timeout 재시도 수를 R이라 하면 실제 OpenAI 및 Web API LLM 요청 수는 `B + 5 + R`이며, 이론상 모든 논리 호출이 한 번씩 timeout되면 최대 `2 * (B + 5)`가 된다. 두 번째 시도도 실패하면 전체 job 실패와 operation 환불로 이어진다.

`events_from_blocks` client/prompt는 존재하지만 현재 executor에서 호출하지 않아 0회다.

### Desktop -> Web API

사전 quote까지 포함하면:

```text
정상 요청 수 = B + 9
timeout 재시도 포함 요청 수 = B + 9 + R
```

- quote 1
- operation start 1
- LLM B+5
- desktop job evidence 1
- succeed 또는 fail 1

B=1이면 10회다. 각 LLM controller는 DB에 provider_request started와 succeeded/failed를 기록하지만 추가 desktop HTTP는 아니다.

### Local NestJS -> Python

- Python stage `POST /jobs`: 4회
- 각 stage WebSocket event stream: 4개
- 취소 시 `DELETE /jobs/:id`: 최대 4회

### Hugging Face

필수 모델은 faster-whisper small과 LAION OpenCLIP ViT-B-32다. cache hit이면 외부 요청이 없고, cache miss이면 큰 파일의 `hf_hub_download`와 나머지 `snapshot_download`가 수행된다. 실제 HTTP 요청 수는 파일 수와 retry에 따라 달라진다. HF XET는 비활성화한다.

manifest에는 faster-whisper `>=1.0` 및 auto-download 설명이 남아 있지만 실제 `pyproject`는 `>=1.2,<2`이고 명시적인 모델 prefetch를 사용한다.

## 10. 메모리 최적화 상세

Git author metadata 기준 작업자는 곽민준이며 2026-09-02~03에 반영됐다.

### 키프레임 스트리밍

관련 커밋: `480b765`, review `2e066eb`, merge `1f4d280`.

최적화 전 `sample_keyframes`는 shot별 full-resolution frame을 모두 리스트에 보관했다. 1080p BGR frame은 약 6.2 MB이고, shot이 많을수록 메모리가 선형 증가했다.

controlled benchmark:

- 66 shots: 1.50 GB
- 327 shots: 2.71 GB

최적화 후 `iter_keyframes` generator는 하나의 OpenCV capture로 target frame까지 순차 진행하고, 완료한 shot reference를 pending 구조에서 제거한 뒤 즉시 yield한다. 소비자가 embedding을 계산하고 나면 frame 전체를 보존하지 않는다.

변경 후 66 shots와 327 shots가 모두 약 1.50 GB였다. embedding은 `np.array_equal`, 최대 절대 오차 0, MD5 동일로 검증됐다.

### STT chunked mel

관련 커밋: 문서 `b8adb31`, 구현 `1b5b8cc`, fix `3467b50`, merge `3c31ec0`.

최적화 전에는 전체 오디오 STFT를 한 번에 계산했다. 81.3분 입력의 중간 배열 추정은 다음과 같다.

- complex128 STFT: 1,495 MB
- complex64 변환: 748 MB
- magnitude: 374 MB
- squared magnitude: 374 MB
- 최종 mel: 149 MB
- 중간 배열 합계: 약 3,139 MB
- 실제 mel 단계 증가: 약 3,650 MB

최적화 후 faster-whisper feature extractor를 `ChunkedFeatureExtractor`로 교체했다.

- 약 30,000 frame, 약 5분 단위
- float32 waveform
- reflect padding
- chunk별 `center=False` STFT와 overlap
- complex64/mel 계산 후 중간 배열 제거
- mel chunk를 모아 concat
- 마지막에 global log normalization

controlled 및 product-path 결과:

| 측정 | 최적화 전 | 최적화 후 | 감소 |
| --- | ---: | ---: | ---: |
| controlled 단기 | 2,932 MB | 1,847 MB | 약 37% |
| controlled 장기 | 5,406 MB | 2,742 MB | 약 49% |
| product path 단기 | 약 2,932 MB | 1,805 MB | 약 38% |
| product path 장기 | 약 5,406 MB | 2,351 MB | 약 57% |

메모리 증가 기울기는 controlled 기준 약 18.4 MB/분, product path 기준 약 11.2 MB/분이 되었고 기존 약 50.8 MB/분 대비 product path는 약 4.5배 완만하다. runtime은 약 4~8% 늘었다.

예측 peak:

| 길이 | 최적화 전 | 최적화 후 |
| --- | ---: | ---: |
| 60분 | 4.22 GB | 2.06 GB |
| 120분 | 7.20 GB | 2.72 GB |
| 180분 | 10.18 GB | 3.38 GB |

segment, character, word, mel 결과 동일성이 검증됐다. `3467b50`은 `model.feat_kwargs`를 새 extractor에 넘기도록 수정했다. small 모델 기본값은 우연히 맞았지만 large-v3의 128 mel bin 같은 모델에서는 전달하지 않으면 조용히 잘못된 feature가 생성될 수 있었다.

### 남은 메모리 비용

- 전체 waveform 보존
- mel chunk 리스트 및 concat된 최종 mel 보존
- 모든 STT segment/word 보존
- librosa가 MFCC 계산을 위해 전체 오디오를 다시 로드
- 모델 cache를 runtime 종료까지 보존

81분 기준 각 full audio load는 약 298 MB 수준이다. 이번 최적화는 거대한 temporary array를 제거했지만 모든 `O(duration)` 데이터를 제거한 것은 아니다.

## 11. 런타임 메모리 정책

dialog highlight는 dance, video render, TTS 등과 exclusive group을 공유한다. Python runtime은 기본 60초 idle stop 대상이다.

새 runtime 예상 RAM이 가용 메모리의 70%를 넘으면 safe-to-evict 상태인 idle plugin을 RSS 내림차순으로 종료해 headroom을 확보한다. active job이 있으면 종료하지 않는다. 일반 exclusivity 처리에서는 최근 idle-stop pending인 peer를 보호하지만, 명시적인 memory-pressure eviction에서는 recency보다 메모리 확보를 우선한다.

manifest 예상 리소스:

- RAM 6,144 MB
- VRAM 4,096 MB
- required GPU: false
- accelerator: CUDA, MPS, CPU
- max concurrency: 1
- cold start: high
- idle 시 safe-to-evict

현재 host resource monitor는 root PID의 RSS를 읽고 child process 전체 합을 집계하지 않는다. 따라서 ffmpeg가 동작하는 순간 실제 process-tree 메모리를 낮게 볼 가능성이 있다.

## 12. 현재 UI/UX

화면 상태는 `INIT`, `SOURCE_CONFIRM`, `PIPELINE_RUNNING`, `PIPELINE_DONE`, `PIPELINE_FAILED`다. 좌측 내비게이션의 “대사 하이라이트”에서 `/dialog`로 진입하며 plugin-installed guard를 사용한다.

### 입력

- 기본 YouTube 탭
- 로컬 파일 탭
- URL Enter 제출
- 클릭 파일 선택
- drag-and-drop
- thumbnail 또는 placeholder
- 제목, 채널/업로더, 길이, URL/path 표시
- “다시 선택”
- “이 영상으로 하이라이트 추출”

UI 문구는 “MP4, MOV, AVI 등 모든 영상 형식 지원”이라고 표시한다. Electron picker는 mp4, mov, avi, mkv, webm, m4v, ts와 all files를 허용하지만 source streaming allowlist에는 ts가 없다. 카피가 실제 보장 범위보다 넓다.

folder 및 multi-select 기반 infrastructure는 Electron/FilePicker에 있지만 dialog setup은 `pickVideoFile()`과 drop된 첫 번째 파일만 사용한다. 현재 사용자는 폴더 또는 다중 영상을 선택할 수 없다.

### 준비 상태

YouTube는 yt-dlp, ffmpeg, model file, warmup이 필요하고 로컬 파일은 yt-dlp 없이 사용할 수 있다. ffmpeg가 없으면 동의·다운로드 overlay를 보여준다.

현재 Angular의 warmup은 사실상 plugin `start()`다. Python `load_models()`는 device와 모델 파일을 확인하지만 Whisper와 OpenCLIP 객체를 실제 instantiate하지 않는다. 모델은 `analyze_media`에서 lazy load된다. 따라서 UI의 “준비 완료”가 inference warmup 완료를 의미하지 않으며 첫 실행 지연이 남는다.

### 크레딧

작업 전 모달은 영상 길이, 차감량, 현재 잔액, 예상 잔액, `N 크레딧 사용` 버튼을 보여준다. 부족하면 별도 부족 모달을 표시한다.

기본 정책은 시작된 1분당 50 credits다.

```text
credits = ceil(duration / 60) * 50
```

최소 1분이고 `charge_then_refund` 방식이다. 실제 quote는 DB 정책에서 오므로 단가를 UI에 하드코딩하지 않는다. 큐 대기는 과금하지 않고 작업이 실제 시작된 뒤 차감하며 실패·취소 시 환불한다.

job이 queued로 반환되면 setup 화면은 즉시 `/projects?plugin=dialog_highlight&job=<id>`로 이동한다. setup의 pipeline-running 상태는 일반적으로 짧게만 보이며 프로젝트 화면이 진행률을 소유한다.

오류는 2026-08-25 이후 inline banner가 아니라 snackbar/toast 중심이다. 화면이 직접 생성한 오래된 sticky error toast만 성공적인 사용자 동작 뒤 정리한다.

### 결과 및 편집

- 헤더: 제목, 상태, plugin, clip 수, 생성일, 입력 소스
- 좌측 세로 clip 목록: thumbnail, 제목, 시간, STT, 편집 여부
- 선택된 9:16 플레이어
- 제목, 범위, script, 선택 이유
- 개별 다운로드
- 전체 ZIP 다운로드
- project 삭제 확인

trim UI는 원본 영상의 source-relative 전체 timeline을 사용하고, 선택한 구간만 preview한 뒤 저장 시 새 편집 결과를 렌더링한다. 원래 구간으로 reset한 뒤 저장할 수도 있다. 프로젝트 삭제는 복구 불가능한 동작임을 묻는다.

## 13. 문제 및 개선 후보

### 높은 우선순위

1. 원래 Python checkout이 최신 memory optimization 전 상태였음. 새 개선 worktree는 반드시 최신 dev 기준을 유지해야 한다.
2. warmup 표시와 실제 lazy model load의 차이를 해소해야 한다.
3. 긴 영상의 waveform, final mel, STT word, librosa audio memory를 추가로 줄일 수 있는지 측정해야 한다.
4. resource monitor가 child process RSS를 포함하도록 할지 검토해야 한다.
5. timeout 한정 1회 retry는 존재하지만 LLM 단계는 여전히 순차이며 성공한 앞 단계를 원격 checkpoint로 resume하지 않는다. retry 범위, 단계별 resume와 비용 중복 방지 정책을 추가 검토해야 한다.

### 후보 품질

1. score 신호들의 scale을 명시적으로 정규화할지 검토한다.
2. 짧은 영상에도 최소 6개를 강제하는 정책을 content-aware하게 바꿀지 검토한다.
3. metadata fallback을 시간순이 아닌 score·coverage·diversity 기반으로 바꿀지 검토한다.
4. sentence snap 뒤 shot snap이 의미 경계를 되돌리는 문제를 조정한다.
5. OCR을 실제로 사용할지 제거할지 결정한다.

### 유지보수

1. 사용되지 않는 `events_from_blocks`와 `transcribe_media` 경로 정리 여부 결정
2. `CONTENT_THRESHOLD`, `STT_VAD_FILTER`, `EVENT_MIN`의 선언과 실제 동작 일치
3. manifest와 `pyproject`의 dependency/version/download 설명 일치
4. YouTube metadata와 로컬 ffprobe 중복 호출 제거 가능성 검토
5. local license policy가 always-allow stub이고 Web API가 실권한을 갖는 구조를 명확히 문서화

### UI/UX

1. “모든 형식 지원” 문구와 실제 allowlist 통일
2. folder/multi-select를 제품에 노출할지 infrastructure를 제거할지 결정
3. 준비 화면을 runtime 준비, 모델 파일 준비, 모델 memory load로 세분화
4. queue/source/analysis/LLM/select/render 단계를 사용자에게 의미 있게 표시
5. 실패 단계·환불 상태·재시도 가능 여부를 결과 화면에서 구체화
6. 후보 선정 이유와 원본 transcript 근거를 사용자가 이해하고 수정할 수 있는 편집 UX 검토

## 14. 작업용 최신 dev worktree 기준점

모든 저장소에 동일한 브랜치 `feature/dialog-highlight-overhaul-20260904`를 만들었다.

| 저장소 | 기준 `origin/dev` | worktree |
| --- | --- | --- |
| Desktop Angular | `566b1d398e54930b3edc59faa41b7927a69ee9fe` | `.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_angular` |
| Desktop Electron | `768b8767ba4d6ab3d6dc11242a9e80e91382ddc2` | `.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_electron` |
| Desktop NestJS | `cffa4ee2ee4137a91e139c6934a9ddce24d4d54f` | `.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_nestjs` |
| Desktop Python | `7d9a470c6c1ab25111badd04407fa56133a42712` | `.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_python` |
| Web API | `557da3fd22c47009d222d18a231a2b4848d9e5e9` | `.worktrees/dialog-highlight-overhaul-20260904/web/clipper_web_api` |

Electron의 cross-repository build script가 `../clipper_angular`, `../clipper_nestjs`, `../clipper_python` 형제 경로를 전제로 하므로 개별 flat worktree가 아니라 원래 `desktop/...`, `web/...` 레이아웃을 보존한 하나의 작업 루트로 구성했다.

## 15. 조사 검증

최신 dev worktree에서 수행한 기준선 검증:

- Python dialog 및 chunked mel 집중 테스트: 74/74 통과
- Angular dialog flow/setup/result/charge guard: 55/55 통과
- Electron plugin/Nest process 집중 테스트: 41/41 통과
- NestJS workflow/stage runner/Web client/runtime lifecycle/operation controller: 60/60 통과
- Web API dialog LLM/controller/operation: 63/63 통과
- Angular, Electron, NestJS, Web API build 통과

Angular 22.1.3 기본 build는 worktree에서도 원본 저장소의 `.angular/cache`를 공유한다. 이 환경의 `lmdb@3.5.6` native addon은 해당 cache를 열면서 잘못된 포인터 해제로 SIGABRT를 냈다. SQLite cache는 첫 build는 통과했지만 다른 프로세스가 재사용하면 `contents must be a string or Uint8Array` 오류가 발생해 안정적인 대안이 아니었다. build와 unit test 모두 `CI=1`로 persistent cache를 완전히 끄면 반복 실행이 통과했다. 이는 application source failure가 아니라 worktree 사이 shared Angular persistent cache 문제지만, 후속 개발 명령과 CI 기준에서 재발 방지 방식을 정해야 한다.

샌드박스 안의 전체 Electron, NestJS, Web API 테스트 중 localhost에 임시 server를 여는 항목은 `listen EPERM`으로 실패했다. 관련 집중 테스트는 localhost 권한을 부여해 재실행했고 모두 통과했다. Electron 전체 packaging fixture는 추적되지 않는 `.env.packaged`와 사전 생성된 sibling bundle을 요구하므로 이번 clean worktree 기준선에는 포함하지 않았다.

모든 코드 worktree는 의존성 설치와 검증 후 tracked/untracked 변경 없이 clean 상태로 정리했다. `node_modules`, `.venv`, `dist`는 각 저장소 ignore 규칙에 따라 로컬 준비물로만 유지한다.

30~81분 실제 media benchmark를 이번 감사에서 새로 재실행하지는 않았다. 메모리 수치는 저장소에 커밋된 benchmark·regression evidence와 구현을 교차 확인한 결과다.
