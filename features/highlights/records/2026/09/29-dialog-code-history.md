# W12 대사 하이라이트 현행·팀원 변경·평가 설계 조사

조사일: 2026-09-29 KST. 조사 방식: 로컬 파일·Git log/show/diff 읽기. 실제 ML, 유료 API, 모델 다운로드, 서버, build/test, fetch, commit, 제품 코드 변경은 수행하지 않았다. 아래 성능·비용 개선은 실측 결과가 아니라 검증할 가설이다. [종합 인계](29-pipeline-design-handoff.md)와 [개별 세션 프롬프트](../../../../../handoff/prompts/2026-09-29-highlight-sessions.md)의 입력·실행 상한을 우선한다.

## 1. 결론과 범위

1. 9/4 감사 이후 Python STT·shot·embedding·candidate·score·OCR 알고리즘과 모델 기본값은 그대로다. 주요 변화는 9/18의 원본 비율 raw clip 출력, 제목을 manifest 데이터로 분리, Nest/Angular의 원본 클립 준비·backfill·숏폼 생성 연결, Web API의 제목 프롬프트와 조건부 보정 호출이다. “민준 변경 때문에 추출 정확도가 낮아졌다”는 동일 입력 비교 전 가설이다.
2. Git author로 확인되는 곽민준 <gwak0214@naver.com>의 변경을 아래에 분리했다. Git 이름은 분해형 Unicode(곽민준)다. minjun/gyumin/Jason 같은 별칭은 author metadata만으로 동일인이라고 단정하지 않는다. integration/jason-dev 브랜치명도 사람 신원의 증거가 아니다. Claude coauthor trailer와 실제 author/committer를 구분한다.
3. OCR False는 최근 비활성화가 아니다. 4/17 최초 업무 코드 반입부터 False이고 실행 경로도 CUDA 전용이다. 끈 이유를 설명하는 근거는 현재 소스·관련 commit에서 찾지 못했다. 속도·메모리·중복 자막·비용 이유는 합리적인 평가 가설이며 작성자 의도로 확정할 수 없다.
4. 9/4의 주요 잔여 항목(실제 모델 warmup과 UI 준비의 차이, O(duration) 메모리, root PID RSS, LLM 순차·resume 없음, score scale, sentence 이후 shot snap)은 여전히 남는다. durable billing/refund와 결과·숏폼 UX는 개선됐다. 취소 상태/환불의 내구성과 Python 작업의 실제 중단은 별개다.
5. 9/4 문서의 trim 설명은 정정해야 한다. 당시와 현재 모두 추출된 원본 클립 내부의 clip-relative timeline이다. 전체 source 영상에서 원래 후보 밖으로 경계를 늘릴 수 있는 편집 기능이 아니다.

필독 자료: .codex/AGENTS.md, .codex/handoff/tasks/dialog-highlight.md, highlight-overview.md, .codex/main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md 및 5개 저장소 CLAUDE.md. workspace 루트는 Git 저장소가 아니며 루트 CLAUDE.md는 없다.

아래 경로 접두어는 모두 /Users/jina/project/adlight 기준이다.

| 접두어 | 저장소 절대 경로 |
|---|---|
| PY | /Users/jina/project/adlight/desktop/clipper_python |
| NE | /Users/jina/project/adlight/desktop/clipper_nestjs |
| NG | /Users/jina/project/adlight/desktop/clipper_angular |
| EL | /Users/jina/project/adlight/desktop/clipper_electron |
| WA | /Users/jina/project/adlight/web/clipper_web_api |
| PP | PY/plugins/dialog_highlight/dialog_highlight/services/pipeline |

파일 뒤 :숫자는 현행 one-based 행이고 함수명을 함께 기록했다. 역사 SHA를 명시한 경우 그 revision의 코드다.

## 2. 비교 기준선과 현재 스냅샷

모두 local dev이며 조사 시작 시 working tree가 clean이었다. fetch하지 않았으므로 실제 remote 최신 상태라는 뜻은 아니다. 날짜는 AuthorDate, KST(+09:00)다.

| 저장소 | 9/4 감사 기준 SHA | 현재 HEAD | 현재 HEAD 날짜·author |
|---|---|---|---|
| PY | 7d9a470c6c1ab25111badd04407fa56133a42712 | 47782953228861f4bdbdc135265d067c2a826b0e | 9/21 07:31:38, 곽민준 <gwak0214@naver.com> |
| NE | cffa4ee2ee4137a91e139c6934a9ddce24d4d54f | 824a7a9f71dde8aa44c8692eadacb6ba6e4961b8 | 9/21 13:00:29, 곽민준 <gwak0214@naver.com> |
| NG | 566b1d398e54930b3edc59faa41b7927a69ee9fe | 797782e8f8e1c8488d024d23e6291e91c2b1e30e | 9/21 13:02:05, 곽민준 <gwak0214@naver.com> |
| EL | 768b8767ba4d6ab3d6dc11242a9e80e91382ddc2 | 0cd7ed7b9444bb00c6372bdcff47a356f5520c35 | 9/18 22:27:05, metabuzz-jinahan <jinahan@metabuzz.co.kr> |
| WA | 557da3fd22c47009d222d18a231a2b4848d9e5e9 | 31f448260148b11e61e9f53cad0ee9ac372345fe | 9/21 12:58:50, 곽민준 <gwak0214@naver.com> |

PY dialog 경로의 all-history author는 곽민준, metabuzz-jinahan, yoonseo <choiys613@gmail.com>로 확인된다. merge commit의 이름만 보고 그 아래 모든 코드 변경을 같은 사람에게 귀속시키지 않았다. git diff 기준 PY dialog 제품 소스는 6개 파일 80 insert/91 delete이며 주로 font 계약과 raw export 변경이다. STT worker, chunked mel, segmentation, embedding, OCR 기본값의 감사 이후 변경은 없다.

## 3. 실제 전체 실행 경로

### Angular 입력 → Nest job/source

NG/src/features/dialog-highlight/flow/dialog-flow.state.ts:25 initialDialogFlowState는 YouTube 기본, 내부 outputRoot 초기값 /tmp/clipper_dialog_out을 갖지만 startJob params에는 이 값을 보내지 않는다. dialog-flow.store.ts:95–145 startPipeline은 YouTube metadata preview/로컬 ingest preview 후 source, source_assets, title, 로컬 video_path를 넘긴다. YouTube requestedQuality는 1080p(:106). 단일 파일 picker 또는 첫 dropped file만 사용한다(NG/src/features/dialog-highlight/pages/dialog-setup/dialog-setup.component.ts:283). source-input.component.html:23의 “모든 영상형식 지원”은 실제 decoder 검증 범위보다 넓은 문구다.

dialog-setup.component.ts:133 activeRequirements는 로컬 파일에서 yt-dlp를 제외한다. confirm(:151)은 ensureReady → blocking progress → OperationChargeGuard quote/confirmation → start/navigate 순서다. NG/src/core/readiness/readiness.service.ts:163–180에서 model 파일 준비 다음 warmup은 plugins.start 호출이다. Whisper/OpenCLIP 메모리 로드 완료와 동일하지 않다.

NE/src/modules/jobs/application/jobs.service.ts:380 enqueueJob: fresh params에서 기존 billing_attempt_id/operation_run_id 제거 → managed project params 생성 → durable preparing job 생성 → billing start(:420) → run binding/queued 저장(:422) → queue enqueue(:438). 따라서 과금은 queue 진입 전이다. runJob(:750)에서 disabled plugin 검증 → runtime lease(:766) → source ingest(:771) → running(:780) → executor(:791) 순서다. Angular preview는 선행하지만 Nest 실제 재-ingest는 과금 뒤다.

NE/src/modules/sources/application/source.service.ts:247 prepareJobParams는 source 또는 legacy video_path를 다시 ingest한다. 로컬 localFileAsset(:771)은 stat/isFile와 ffprobe metadata(:790)를 읽고 thumbnail을 만들 수 있다. YouTube metadata preview와 실제 다운로드, 로컬 preview와 job ingest의 중복 probe 비용은 따로 측정할 항목이다. NE/src/modules/projects/application/projects.service.ts:616 prepareJobParams는 managedProjectsRoot/subjectId/projectId 기반 output_root와 project_id/title을 만든다. 원본 source_assets.localPath와 source provenance가 결과/backfill의 근거다.

### Nest orchestration → Python → Web API

NE/src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts:45 단계 목록은 prepare_media, analyze_media, build_candidates, render_highlights 4개다. transcribe_media는 Python이 지원하지만 제품 executor에서 호출하지 않는다. 각 단계는 별도 Python POST job와 WS 이벤트 연결이며 job ID는 부모ID:stage다(dialog-highlight-python-stage.runner.ts:1–88).

executor.run(:120): prepare → analyze → analysis.json 읽기(:134) → split_sentences(:143) → story_backbone(:153) → canonical_info(:166) → define_highlight_topics(:179) → build_candidates(:194) → select_highlights(:203) → highlight_metadata(:217) → render(:240) → manifest 읽기/complete(:247–255). LLM 단계를 병렬화하지 않는다. declare된 events_from_blocks는 현재 executor 경로에 없다.

dialog-highlight-llm-evidence.ts:11 buildDialogLlmEvidence는 STT/OCR 모든 text를 정규화해 fullSttText/fullOcrText와 evidence로 만든다. char/token 상한이 없는 full transcript를 story/canonical에 각각, STT를 topics에도 보낸다. shot text는 segment overlap을 기준으로 같은 STT segment가 여러 shot에 반복될 수 있다(:62). 문장 분리는 40 shot/2,500 text chars와 ±2 shot context로 나누고 target shot 결과만 merge한다(dialog-highlight-sentence-split.ts:1,37). batch 호출은 순차(:343–364 executor).

### Python 분석·후보·최종 출력

PY/plugins/dialog_highlight/dialog_highlight/app.py:28 plugin 0.1.0; load_models(:36)는 device 감지와 Whisper/OpenCLIP 파일 확보만 한다. run_job(:65)은 video_path/output_root 필수 및 입력 존재를 확인하고 staged 경로만 지원한다. stage runner의 prepare(:24)는 output_root/json 생성 정도다(PY/.../services/stage_runner.py).

PP/staged_artifacts.py:48 analyze_video_to_artifacts:

| 순서 | 함수·행 | 현행 동작/산출물 |
|---|---|---|
| duration/목표 개수 | :66–67 | ffprobe duration; clamp(round(duration/120), 6,16). 짧은 영상도 목표가 최소 6이므로 목표 달성·중복을 따로 측정 |
| 무음 | :70 / media_utils.py:129 | ffmpeg silencedetect .35초/-35dB, silence.json |
| STT | :77 / services/stt_worker.py:198 | small, device 전달, STT JSON ok/list 검증(:85); stt.json |
| shot | :95 / media_utils.py:157 | ContentDetector(), frame_skip=2; .5초 미만 shot merge; shots.json |
| OCR | :100–117 | 기본 off; on이라도 CUDA만; raw→dedup; ocr.json(실행 때만) |
| visual | :124 / embedding_pipeline.py:55 | shot당 midpoint frame 1개 순차 generator→OpenCLIP→cosine diff |
| audio | :133 / embedding_pipeline.py:141 | librosa full audio 16k mono 재로드→shot별 MFCC 20차원 mean/std/p25/p50/p75 합친 100차원 L2 정규화→L2 diff |
| analysis | :140–150 | duration,count,shots,silence,stt_segments,stt_words,ocr_items,visual/audio diffs |

PP/stt_pipeline.py:224 build_sentence_spans_hybrid는 LLM 문장을 word exact match(:375), segment coverage≥.6(:293), 남은 overlap segment fallback(:405)으로 시간에 매핑한다. PP/staged_artifacts.py:332 build_candidates_from_artifacts는 analysis/llm_sentences/story/canonical 필수, topics optional(:346). raw(:372)→semantic(:382) 산출; sentence_spans.json, raw_segments.json, semantic_segments.json, highlight_candidates.json을 저장한다.

PP/segmentation_pipeline.py:28 build_raw_segments는 0/duration, shot, silence, sentence 끝점을 모아 .12초 이내 중복을 합치고 .35초 미만 제외, 4.5초 초과 분할하되 sentence 내부를 보호한다. build_semantic_segments(:173,274) target25/max45/min3초; strong scene break(v>.35/a>.45, embedding_pipeline.py:198)는 sentence 내부여도 즉시 flush 가능하다. 보통 target25 이상에서 silence<1초 또는 shot<.8초일 때 flush한다.

segment_signal_score(:115): score_hint=.42*(regex word count/sec)+.30*visual_peak+.18*audio_peak+.10*boundary_clarity. clarity는 양 끝 ±2초 silence 유무로 0/.5/1이다. 신호 간 공통 scale 정규화는 없다. candidate.score_norm(:752)은 정규화가 아니라 raw score_hint 반올림이다. 후보 payload(:731) STT 3,000자/OCR 1,500자, 범위·ID; staged_artifacts._candidate_payload(:288)는 cand_id/cand_index/sentence_ids와 글로벌 story/canonical/topics context를 추가한다. 명시적인 앞뒤 neighboring candidate transcript는 없다. topics가 Python interval construction을 직접 바꾸지는 않고 LLM 선택 문맥으로 들어간다.

Nest selectedCandidatesForMetadata(dialog-highlight-selection-metadata.ts:1)은 selected ID가 없거나 모두 미매칭이면 전체 candidates로 fallback한다. metadataTargetCount(:24)는 전달 candidates 수가 있으면 그 수를 그대로 쓰므로 잘못된 selection은 metadata token/개수를 늘릴 수 있다.

PP/staged_artifacts.py:509 render_highlights_from_artifacts는 semantic fallback을 항상 계산(:546), metadata에 boundary snap(:559)을 적용한다. PP/segmentation_pipeline.py:803 snap은 sentence→shot 순서이며 shot이 방금 sentence snap을 덮을 수 있다; ±2초, final25–55초 길이로 강제 조절한다. 메타 final이 유효하면 그 범위를 쓰고(:568), 아니면 semantic fallback. fallback(:462)은 selected ID 또는 시간순 첫 target semantic(:478), continuity bridge/maxgap max(60,duration*.03)/min separation8, final min25/target35/max55/gap3, backfill이다. score 순 top K fallback이 아니다.

final은 시간순 정렬 후 end=min(end+.25,duration)(:575), clip_stt.json과 semantic_clips.json 저장, clip별 ffmpeg export와 thumbnail 후 manifest 저장(:626). build_raw_clip_cmd(media_utils.py:333)는 title PNG/1080×1920 pad 없이 구간 원본 비율로 재인코딩한다. scale=trunc(iw/2)*2:trunc(ih/2)*2, H264 CRF20/veryfast/yuv420p/AAC/faststart, 첫 video와 optional audio. clip당 export+thumbnail 두 ffmpeg 실행이다. 원본 compressed stream-copy는 아니다.

PP/common.py:407 build_manifest_v65_compat는 기존 clips string[]/final_segments 계약을 보존하고 clip_format='raw', clip_titles[{line1,line2}]를 추가한다. 메타 fallback 때 clip_titles는 빈 문자열이다. title_font_path는 Nest가 여전히 보내지만 Python은 :518 del로 무시한다. 제목과 raw 클립의 분리는 현행 의도다.

## 4. 모델·기본값·런타임 계약

| 항목 | 현행 근거 | 사실과 제한 |
|---|---|---|
| STT 모델 | services/stt_worker.py:85–134,198–264; PP/orchestrator.py:18 | faster-whisper small/Systran/faster-whisper-small. CUDA float16 시도, 실패/비CUDA는 CPU int8; MPS를 CTranslate2 inference로 쓰지 않음. transcribe(vad_filter=False,word_timestamps=True); language/beam은 명시하지 않아 library default. 요청 device와 실제 fallback engine를 구분해야 함 |
| Visual 모델 | PP/common.py:103; embedding_pipeline.py:55–87 | OpenCLIP ViT-B-32/laion2b_s34b_b79k; HF laion/CLIP-ViT-B-32-laion2B-s34B-b79K. device별 cache, model.to(device), dummy encode 후 실제 shot embeddings |
| 모델 revision | PP/orchestrator.py:45 이하 | cache-first snapshot/hf_hub_download, 명시 revision pin 없음. 모델명만 같아도 cached snapshot hash를 평가에 기록해야 함 |
| OCR | PP/ocr_pipeline.py:78 | EasyOCR ko/en, model 이름/version/revision pin 및 install manifest 없음. pyproject에 easyocr 없음 |
| LLM | WA/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:24–53,238 | default normal/high gpt-5-mini; env DIALOG_HIGHLIGHT_OPENAI_MODEL/HIGH_MODEL로 override. story/topics/metadata medium16k/300초, 나머지 minimal8k/180초. select도 minimal. 주석의 27.5원 원가/19.9원 수익은 역사 주석이며 현재 측정값으로 사용 불가 |
| Package/version | PY/plugins/dialog_highlight/manifest.json:3,55; pyproject.toml:3–15 | plugin0.1.0/sdk1/Python3.11 only; faster>=1.2,<2, openclip>=2.24, scene>=.6, librosa>=.10. manifest faster>=1.0은 stale |
| lock 값 | PY/uv.lock:348,462,601,700,909,1112,1560,1779 | CTranslate2 4.7.1, faster-whisper1.2.1, huggingface-hub1.11.0, librosa.11.0, numpy2.4.4, open-clip-torch3.3.0, scenedetect.6.7.1, torch2.11.0. lock상 값이고 설치된 실제 binary/env를 조회한 결과는 아님 |
| 자원 선언 | manifest.json:42–57 | RAM6144MB/VRAM4096MB, GPU optional, preferred cuda/mps/cpu, cold high,max concurrency1,idle manual,safe idle eviction |

PP/common.py의 RUN_STT=True(:27), STT_VAD_FILTER=True(:51), CONTENT_THRESHOLD=27(:38), EVENT_MIN=10(:78), LLM_MAX_RETRY=3(:92), LLM_TEMPERATURE=.35(:93)는 현재 제품 실행 동작을 그대로 표현하지 못한다. 분석은 STT를 무조건 호출하고 VAD false; ContentDetector에 threshold를 넘기지 않아 library default; final min25; 원격 retry는 Nest 2 attempts이고 Python direct LLM 경로는 사용하지 않는다. 선언만 읽고 기능 config라고 보고하면 안 된다. 실제 OCR on/off도 job/UI/env 옵션이 없고 코드 상수다.

EL/src/main/plugin/plugin-process.ts:95–119 dev는 sibling PY project로 uv run, packaged(:145–172)는 plugin venv Python module; 양쪽 --idle-timeout 0으로 SDK 자체 idle exit를 끈다. plugin-venv.ts:72–104는 frozen/no-dev/no-editable sync와 Python3.11 managed runtime, ready marker에 plugin/root/platform/arch/python/app/source fingerprint를 사용한다. :107 source fingerprint가 uv.lock/plugin/SDK를 포함해 0.1.0만으로 변경 여부를 판단하지 않는다.

EL/src/main/plugin/plugin-install-state.ts:62–73 cache precedence HF_HOME/hub→HUGGINGFACE_HUB_CACHE→XDG→default; :103 required weight filenames; :148 HF repo mapping; :156–241 ready는 weight 파일과 validated ready marker가 모두 있어야 한다. health alone은 설치 완료 증거가 아니다. OCR 설치/weight 확인은 계약에 없다. EL/src/main/config/packaged-runtime-config.ts:120 desktopIsolationEnv는 userData/cache 아래 HF/Torch/uv를 격리하고 production ports55000–55199를 사용한다. config된 endpoint/secret/DB 실값은 읽거나 호출하지 않았다.

## 5. LLM·제목·retry·checkpoint·호출/과금

WA LLM 서비스는 Responses JSON object를 요청하고(:64–78) OpenAI call 한 번(:98), HTTP/JSON/truncated/no-text/bad-JSON failure를 provider_failed 502로 처리한다. strict highlight schema 검증은 아니다. gpt 모델명에 supportsReasoning이 false면 reasoning뿐 아니라 max_output_tokens도 붙이지 않는다(:75).

제목 프롬프트(dialog-highlight-llm.prompts.ts:210–310): 훅→핵심 2줄, 줄당18자, 나열·번호·해시태그·이모지 금지, evidence/canonical grounded 내용. 최근 제목 repair는 모든 품질 오류를 검수하지 않는다. overlay-title-quality.ts:23 looksLikeKeywordList는 구분기호/원번호/번호형식/emoji 또는 3개 이상 짧은 comma tokens를 감지한다. plain 장문·빈 제목·근거 없는 내용은 이 조건만으로 repair되지 않는다.

repairKeywordListTitles(service:165–236)는 bad title 전부를 묶어 추가 호출 최대1회; 같은 model/minimal/max1500; min(45초, main start+main timeout+15초까지의 잔여시간), 잔여5초 미만이면 skip. 실패/invalid replacement면 원문 유지. 채택은 두 줄 nonempty/각18 Unicode chars 이내/나열 아님이다. repair prompt는 old title+content_summary를 주로 받아 원문 transcript 근거 재검증이 아니다. 타이틀 관련 의미 정확도 개선은 아직 측정하지 않았다.

NE dialog-highlight-web-api.client.ts:21–35 timeout330초 env override, 최대2 attempts. :147–171 provider_failed/web_api_timeout이면서 메시지 /timed out/i이고 cancel 안 된 경우에만 1회 즉시 retry. rate limit/인증/JSON 계약 오류는 retry하지 않는다. Web API 자체 main call retry는 없다. abort가 HTTP 대기를 끊어도 이미 시작된 Web API provider timeout signal이 client disconnect에 연결되어 있지는 않다(WA service:106–117); 이미 수행된 provider 비용의 환불 여부와 사용자 크레딧 환불은 다르다.

executor.callWebApiAndWrite(:303)은 파일 존재를 보고 건너뛰지 않고 매번 call/write한다. 모든 artifact는 단계 결과의 로컬 파일이며 resumable checkpoint 계약이 아니다. split batch 결과는 메모리에 모아 모두 끝난 뒤 merge/write하므로 앞 batch 성공을 개별 resume하지 않는다. NE jobs.service.ts:287 retry는 새 job/project/paid attempt로 전체 재실행하며 기존 operation ID를 재사용하지 않는다(:392).

호출 계산: B=실제 split batch 수(빈/한 batch 경로도 1 call), L=B+5(총6 종류의 현행 logical LLM op), R=timeout retry 추가 횟수(0≤R≤L), P=각 metadata attempt에서 실행한 title repair 수(0≤P≤metadata attempts≤2).

- Desktop→Web API LLM POST 수 = L+R. OpenAI provider 요청 수 = L+R+P. title repair는 Desktop HTTP를 한 번 더 만들지 않는다.
- WA controller:23,33–55는 Desktop LLM HTTP마다 하나의 requestId/provider_request evidence를 기록하므로 repair를 포함해 provider 호출을 합치면 실제 provider requests를 적게 센다. request/usage logs에서 main/repair·retry·실패를 따로 집계해야 한다.
- 정상 paid flow에서는 quote/start/terminal evidence/succeed 등 부수 HTTP가 더 있다. durable finalizer/recovery/outbox retry로 wire count가 달라질 수 있으므로 B+9 같은 고정값을 비용 계수로 쓰지 않는다.
- 고정 evidence 대조의 budget은 전체 pipeline job 수가 아니라 main·repair·retry 모두 포함한 실제 provider 요청으로 제한한다. 24회/$2 같은 상한은 제안이며 사용자 승인/실제 실행·정산 결과가 아니다. 지금은 0회/$0 실행.

NE jobs.service.ts:936은 source_assets의 양수 duration을 billing input으로 선택한다. WA operation-definitions.ts:30 기본 policy는 dialog_highlight.extract 50 credits, charge_then_refund, openai scope; operations.service.ts:327 DB policy를 읽고 :351 creditCost*max(1,ceil(sourceDurationSec/60))로 계산한다. 실제 배포 DB policy를 확인하지 않았으므로 50을 live price로 단정하지 않는다. OCR on/off로 duration이 같으면 사용자 산식은 같지만 provider token/repair/운영 원가가 늘 수 있다.

NE/src/modules/operations/application/billable-job-attempt.coordinator.ts:43 start는 durable attempt와 idempotent client key; :125 unresolved start는 같은 key 복구 후 abandoned fail 처리. jobs.service.ts:960 terminal status에 따라 succeed/evidence 또는 fail/refund를 finalizer/outbox로 보낸다. 9/17 변경으로 재시작/취소/네트워크 실패에서 operation binding과 환불 intent가 저장된다. 이것을 실제 결제 API 검증 완료라고 표현하지 않는다.

highlight shortform은 NE/src/modules/highlight-shortform/application/highlight-shortform-render.service.ts:66에서 origin/clip/template/BGM을 검증하고 :124 reserve→submit한다. VideoRenderService:26,48은 clipper_video_render로 JobsService.reserve/activateReserved를 쓰고 이 dialog LLM workflow charge map에 포함되지 않는다. 현재 경로에 추가 LLM call/별도 dialog 추출 과금은 없다. 이것을 서비스 모든 이용료가 영구 무료라는 의미로 확대하지 않는다.

## 6. 결과·trim·shortform·legacy assets

NG/src/shell/projects/dialog-result-detail/dialog-result-detail.component.html:1–193는 clip list/정보/숏폼 설정/preview 4개 열 카드와 미리보기 하단 생성 버튼이다. 제목·script·선정 이유는 읽기 영역; overlay 제목은 shortform draft에서 clip별 편집한다. component.ts:54 선택한 한 클립을 preview하고 :274 generate는 한 clip을 보낸다. headline/reason을 원문/후보와 함께 재선정하는 UI는 없다.

NG/src/features/highlight-shortform/services/highlight-shortform-draft.ts:142 clip별 기본 overlay title seed; :158 저장된 숏폼 settings 복원; :175 clip ID Map에 user title 보존하고 template/BGM/source credit 같은 공통 settings 관리; :224 render POST/inflight guard, queue snackbar. title/BGM/template 변경만으로 다시 STT/LLM 분석하지 않는다. highlight-shortform.ts:178 pending/unavailable은 생성 차단한다.

NE ProjectDetailBuilder(project-detail-builder.ts:49,80)는 manifest/highlights_meta/clip_stt/raw-clips/clip-edits sidecar를 조합한다. final_segments로 source 범위(:152), originalDuration=end-start, originalVideoPath=추출 clip videoPath(:164). raw format/clip_titles(:98), legacy rawStatus/readystate(:175), 수정 clip path(:189), trim range에 맞춰 STT(:217). 9/4 기준 cffa4ee의 같은 파일도 originalDuration=end-start/originalVideoPath=videoPath이며 trim은 clip-relative라고 명시했다. 9/4 감사의 source-relative full timeline 문장을 그대로 승계하면 안 된다.

NE ClipTrimService(clip-trim.service.ts:120) dialog 전용이고 manifest/raw clip 원본을 resolve(:144), 그 clip duration을 ffprobe(:145), 0..duration·최소3초(:18,247)로 검증, temp→rename 후 clip-edits.json 저장(:168–190). ±1초 상한 slack이 있으나 actual clip length로 clamp한다. 같은 clip lock(:95), revert는 sidecar 제거 후 derived 파일 삭제(:64). 추출 clip 밖의 source duration까지 확장하지 못한다.

legacy raw backfill(dialog-raw-clip-backfill.service.ts:21–27,71–197): getDetail에서 pending을 보면 asynchronous trigger; project singleflight, 5분 cooldown, persisted 실패3회면 unavailable. 원본 source 파일이 있으면 final 범위를 다시 cut(:243–258); 없으면 기존9:16 pad/title clip에서 알려진 landscape content 영역 crop(:228–265). source가 없고 portrait/square 등 제거 안전조건이 없으면 unavailable. crop만으로 옛 scale 손실을 복원하지는 못한다. old clip-edits도 raw clip 기준으로 recut(:288). 새 raw manifest는 backfill 불필요.

NG projects-detail-page.component.ts:48–57,194–237 pending일 때3초 poll→2분 후15초→10분 후 stop/snackbar; 연속오류5회도 stop(:563). quiet refresh는 선택 clip/draft 보존(:520), media path+range key로 token URL 갱신 때문에 되감기지 않게 한다. source 없는 unavailable 복구와 source 밖 경계 재추출은 아직 사용자 액션이 필요하다.

NE highlight-shortform-render.service.ts:74 duplicate ID 거부, :154 dialog one-clip, raw readiness 확인(:167). manifest builder(:7,61–95)는1080×1920, 기본 clipFit cover, origin clip absolute source-file와 BGM/template/title/source credit을 recipe로 연결한다. raw clip extraction과 final 숏폼 crop/fit의 품질은 별도로 평가해야 한다.

자원 가설: legacy backfill은 GET detail로 시작하는 ffmpeg이며 project singleflight만 있다. global JobsService queue/admission lease 경로를 직접 거치지 않으므로 여러 프로젝트 조회와 분석/숏폼 렌더가 동시에 자원을 쓸 수 있는지 평가한다. 현재 실행으로 concurrency를 재현한 것은 아니다.

## 7. 메모리·warmup·취소와 자원 정책

Whisper cache(stt_worker.py:85)는 model size/requested device key로 process 생명까지 남는다. OpenCLIP cache(embedding_pipeline.py:55)도 model/pretrained/device key로 남는다. analyze의 Whisper→OCR→OpenCLIP→MFCC는 순서지만 이전 cached 모델이 unload되는 순서는 아니다. PP/orchestrator.py:29 warm_pipeline_models는 실제 instantiate 함수이나 app.load_models에서 호출하지 않는다. model 파일 download 완료/ready marker/start/health와 실제 memory warm은 서로 다른 사건이다.

키프레임 streaming(media_utils.py:241–327)은 모든 RGB frame list를 잡지 않고 generator와 sequential capture/finally release를 사용한다. chunked_feature_extractor.py:26–63는 약5분 mel chunk STFT로 큰 complex STFT 중간체를 줄인다. 그러나 full decoded float32 waveform, reflect padding copy, mel chunk list/concatenate/log array, 전체 STT segment/words, MFCC의 librosa full decode는 여전히 O(duration)이다. CUDA Whisper와 OpenCLIP 혼합 allocator/cache, FFmpeg child, WAV decode/후속model load peak를 함께 측정해야 한다.

9/2 관련 역사 evidence: 81분 기존 문서 peak5.406→2.351GB, slope50.8→11.2MB/min, runtime+4–8% 등은 당시 문서/커밋에 기록된 결과다. 이번 조사가 그 수치를 재현하지 않았다. 현재 host6GB 선언에 대한 근거 검토에는 쓸 수 있지만 현행 total process tree peak 보장으로 쓰지 않는다.

NE python-runtime-lifecycle-policy.service.ts:27 dialog/dance/video/tts exclusive group; :34 idle60초(override 가능); :91 beginRun owner를 먼저 등록하고 serialized admission, missing snapshot/critical block, manual warning acknowledgement와 auto flow를 구분. :275 estimated RAM>available*.7이면 safe idle plugin을 RSS 큰 순으로 evict; :353 health active_jobs==0을 확인하고 health 없으면 idle로 간주하지 않는다. manifest manual idle policy와 Nest 실제 idle timer는 책임이 다르다. 이미 ready/running인 runtime의 추가 duration별 peak를 완전히 예측하는 정책은 아니다.

EL/src/main/resources/host-resource-monitor.ts:282 Electron own memory.rss, :305 ps -o rss -pcpu -p PID, :316 Windows Get-Process ID는 단일 root PID다. 9/17의 owned process registry/재시작 정리는 process ownership이며 child RSS 합산 구현과 동일하지 않다. 따라서 ffmpeg/ytdlp child와 process-tree peak 누락은 남는다.

취소: NE jobs.service.ts:476 cancelled 저장→abort(:484)→stage DELETE(:487)→active slot release(:492). LocalPluginJobRunner:162 abort는 DELETE(1초timeout) 후 WS를 닫고 resolve(null), Python terminal을 기다리지 않는다. PY SDK base.py:316–330은 CancelFlag set 후 cancelling 반환; :264는 thread worker, routes.py:46은 동일 job ID 중복만 방지. dialog app.py:85–100은 progress callback에서만 flag를 확인하고 run_dialog_stage에 flag를 넘기지 않는다. STT/OCR/ffmpeg loop는 cancel로 즉시 종료되지 않는다. SDK active_jobs와 idle eviction 보호는 남아 있지만 다음 Nest job을 같은 runtime에 제출할 때 미종료 worker와 겹칠 가능성은 별도로 검증해야 한다. durable refund 완료를 compute stop 완료라고 판단하지 않는다.

## 8. 실제 팀원 변경 SHA/date/diff

다음 표의 민준 author는 모두 곽민준 <gwak0214@naver.com> (Git 분해형 표기)로 확인했다. 같은 subject만 읽은 것이 아니라 관련 git show/diff와 현행 호출 경로를 확인했다. tests 추가는 커밋 내용이며 이번 조사에서 실행한 증거가 아니다.

| repo/SHA | 날짜 KST | 실제 diff와 현행 의미 |
|---|---|---|
| PY 480b765b2464d0b88f789da63edd09ab6953417c | 9/2 09:09:13 | list keyframes→iter generator/sequential decode/finally release. 2e066eb46867f4944f72e92e079478b3389811cd(09:30:56) decode-count/identity 검증·dead guard 보완. 이미9/4 기준에 포함 |
| PY 1b5b8cc037634cc826391c241b1722b75de47b5c | 9/2 17:44:36 | CUDA/CPU Whisper에 chunked feature extractor, faster<2. 3467b5088999779b286e2caa8a538bd41b2172d5(17:56:46) feat_kwargs 반영. 이미9/4 포함 |
| PY 9a91a0e14cfd6e696a14e948cbea6cb96d4f8ff3 | 9/4 20:08:09 | title font를 Nest request로. a3333ff(21:14:42) fallback font size 보완. 후속 raw export로 burn-in path 자체가 없어짐 |
| PY 49838e071a2ea57a266dd91fd4a29e69f24d33d3 | 9/18 20:30:58 | 6files236+/128-; title PNG/scale-pad-overlay/title dir 제거, raw cut 명령과 clip_format/clip_titles 추가. STT/candidate/model 변경 아님 |
| PY 8bc950190d64659bb72100a69f70a30539a7499d | 9/18 20:39:45 | 3files104+/6-; odd dimension even scale, semantic fallback title 비움. commit은 자연 invalid-range가 minlen snap으로 먼저 치유되어 fallback branch 테스트를 monkeypatch했다고 명시 |
| PY 278f0ffb2d1948b8b383d8910d21130f12a8e28c | 9/18 21:49:55 | unused TOP_PAD 제거 |
| NE bf9bf674137cb47f4e098462cf1e1ac13b4d8b76 | 9/4 20:08:20 | Hangul 지원 bundled font path 전송. 현재 Python은 받아서 무시 |
| NE 288a44b67c431bafb805bca5c77d93db9fe09f01 | 9/18 21:03:35 | 5files359+/8-; raw/original path, clip별 title, ready status, trim 원본 resolve |
| NE 3e0481ee60bdd502d8088fb3effee75b2dd423f2 | 9/18 21:09:55 | 기존 edit path와 원본 raw path 정합성 보완 |
| NE 2155134f9b9d9e02bbf967895fdf14829f8af117 | 9/18 21:17:46 | legacy raw clip backfill 추가 |
| NE d7660ff3cb249d4b35b4c4050cb5f1a6aaf01069 | 9/18 21:22:47 | mismatch selfheal/점진적 record 저장/square crop guard |
| NE 887297e6d8f5d8bd4bdb77857b4fd4d60ef07fde | 9/18 21:25:26 | 12files1109+/1-; highlight-shortform builder/service/controller/DTO와 shared render recipe 연결 |
| NE d4b93a0f554bad943108ece4fc9d03da2ae6640d | 9/18 21:28:54 | dialog는1 clip 생성 rule |
| NE 72dd83bb29ed5d9c96d44ed085a49e6fc8be03be | 9/18 21:52:08 | persisted failure3회 unavailable; duplicate clip400 |
| NG 345a224e797bd9959a00255504d3f9d927547aa6 | 9/18 15:59:55 | 대사 결과4pane layout |
| NG e81202ec44ea345f26f53a406365ba7c62360caf | 9/18 21:09:13 | 22files699+/49-; render API/draft, per-clip title, ready state, 결과 생성 연결 |
| NG 5770c469752c420c57f539cd112ccab9a32abcb9 | 9/18 21:13:48 | quiet poll errors, pending 동안 trim 차단 |
| NG 7146cb5d27d061017811aba343a7d1d728e232bd | 9/18 21:34:13 | 숏폼 edit에서 settings 복원 |
| NG 360caa67fe162d6ba4e01857372f2f9071ed7cac | 9/18 21:58:46 | 7files227+/17-; preview path+range 키, poll backoff/giveup, partial restore 안내 |
| NG e97f60c9695420f95e7dbc3c14be5377d843d7bf | 9/19 23:38:04 | 공용 column header/소제목 |
| NG 6c70b2ea483626aee4972807ba04eae35e1432c9 | 9/19 23:45:45 | 21files368+/371-; 네 개 열 카드, 중복 메타/source 줄 제거, 생성 버튼 preview 아래 |
| WA af664d760a935c2f9660533ed408d343c77f0b0b | 9/18 22:23:04 | 6files498+/34-; caption/명사구→hook+핵심 제목 prompt, shared18자 rule, list detection/조건부1회 repair |

다른 author의 대사 연관 변경도 혼동하지 않는다. 아래는 metabuzz-jinahan <jinahan@metabuzz.co.kr>다.

| repo/SHA | 날짜 KST | 의미 |
|---|---|---|
| NE f3edd21e4dff58eb2ec5a2f1db33a8ca71299fc4 | 9/17 02:49:52 | paid workflow lifecycle을 Jobs/coordinator/finalizer로 모으고 dialog executor의 중복 책임 제거 |
| NE f452b6f892dfa77d22e971c746daa94285c04a3c | 9/17 04:14:22 | restart billing recovery와 owned process cleanup |
| NE fda1eda586fe2b80a444691303fb1e52fef57a34 | 9/17 08:21:05 | 취소/refund durability, dialog cancel에서 runtime 전체 stop 제거; owner 격리 |
| EL dd4e9d67d85f3da18b6a3a107c06987c67da46d0 | 9/10 04:39:50 | production cache/port 격리 |
| EL 0d9cc11e70ece2c9f0dd40a5344dfd9d8b5d33e5 | 9/18 22:17:36 | Python source fingerprint로 venv refresh, plugin 버전만 같아 stale되는 문제 대응 |

## 9. 9/4 감사 대비 해결·잔여

| 9/4 항목 | 현재 판정 | 검증/다음 측정 |
|---|---|---|
| 한국어 title font | 이전 burn-in 문제의 적용 범위 소멸 | 새 raw는 제목 없음. 최종 shortform renderer font/title wrap은 따로 화면 QA |
| fallback 제목 오매칭 | semantic fallback manifest titles 비움은 해결 | partial malformed metadata와 Nest display summary/title positional association은 fixture 검증 잔여 |
| runtime warmup 표시 | 잔여 | files ready/start와 first model load latency 별도 기록 |
| 모델 장시간 메모리 | 이전 개선 유지, O(duration) 잔여 | full waveform/MFCC/캐시 포함 tree RSS 재측정 |
| child RSS | 잔여 | root+recursive descendants 동시 계측; owned registry와 혼동 금지 |
| timeout retry/resume | 1회 timeout retry 유지, resume 없음 | checkpoint 성공파일 reuse가 없으므로 고정 evidence 평가로 범위 축소 |
| score scale/strongbreak/snap | 잔여 | 동일 분석 evidence에서 ablation, sentence cut/clip quality |
| 최소6/시간순 fallback | 잔여 | 짧은 입력 duplicate/target shortage 및 top-score 대비 검증 |
| OCR 채택 결정 | 잔여 | 기본False·CUDA gating·미선언 dependency와 실패 visibility 우선 확인 |
| stale defaults/deps | 잔여 | VAD/threshold/LLM retry 등 선언과 actual, manifest>=1.0 vs pyproject>=1.2 |
| durable billing/취소/재시작 | 코드 구조 개선 | payment endpoint 실행 안 함. compute cancellation은 별도 잔여 |
| 결과편집/숏폼 UX | 크게 변화 | raw 준비·제목 편집·single clip render·poll 안정성. 후보 경계 밖 재추출/이유 편집은 없음 |
| trim full-source timeline | 감사 설명 오류 정정 | 당시/현재 모두 clip-relative; source 전체에서 extension하려면 신규 설계 |
| 모든 영상 형식/단일 파일 | 잔여 | decoder capability 표기와 실패 사례; batch intake 없음 |

## 10. OCR 비활성의 정확한 이력과 활성 전 결함

기본False와 CUDA-only gate는 PY d5f1740c7a0936d6f5868026e24df9b80b68ae9b (2026-04-17 14:33:52, metabuzz-jinahan <jinahan@metabuzz.co.kr>) 최초 business logic 반입 diff에 이미 있었다. common 추출 bf291d0eb4bf723ce0ac6f33b9b0bc8f9726e5f3(6/29 13:48:45, 곽민준)과 OCR 추출 d08c8f624c968f54eeedab42cfe52ac422f6591d(6/29 14:39:27, 곽민준)는 move-only였다. staged analyze 추출은 665c173(7/1, jinahan). 9/4 이후 OCR 변경을 찾지 못했다. “민준님이 OCR을 최근 껐다”라고 쓰면 근거가 없다.

제품 실행조건: PP/common.py:28 False → analyze(:101) True인가 확인 → device exactly cuda(:102)인가 확인. MPS/CPU는 on을 설정해도 skip한다. OCR function 단독 use_gpu=False를 직접 호출할 수는 있으나 현재 제품 CPU 지원을 뜻하지 않는다. 사용자 UI/job params/environment toggle도 없다.

활성 경로: run_ocr_easyocr_full_sweep(PP/ocr_pipeline.py:60)에서 EasyOCR/cv2 lazy import → Reader ko/en(:78) → every1초 np.arange(:80) → 각 frame random seek(:95) → readtext detail=0,paragraph=False(:102) → len≥2(:105), raw와 merged 저장. 제품은 merged 대신 raw(:115 analyze)를 다시 dedup(max gap1.5, ocr_pipeline.py:153)한다. text의 confidence/bounding box는 출력에 남지 않는다.

정적 결함/측정 왜곡 요인:

- easyocr는 package/model install 계약에 없음. Reader가 모델을 다운로드하려 할 수 있으며 즉시 enable은 preprovisioned offline 재현과 같지 않다.
- import/Reader/outer 오류는 ok=False/raw=[]를 반환하고 analyze는 ok를 검사하지 않아 빈 OCR을 정상처럼 소비한다. failure/off/skipped/no-text를 analysis.json만으로 구분하기 어렵다.
- per-frame 오류를 skip한다. 성공 payload여도 frame coverage를 별도로 확인해야 한다.
- elapsed_sec(:119)는 Reader initialization/probe 전이 아니라 후(:83)에 시작하므로 model load/download/probe를 제외한다. 외부 OCR stage wall timer(:107 analyze)는 이를 포함한다. 비용과 cold latency 비교에 내부 elapsed만 쓰면 안 된다.
- dedup(:179–199)은 시간 간격이 멀어진 동일 norm을 suffix key에 넣지만 base merged[norm] 포인터를 새 구간으로 바꾸지 않는다. 같은 문구가0,1,100,101,102초이면 첫 구간 다음100/101/102가 따로 남는 정적 로직이다. 활성 상태에서 duplicate OCR/evidence tokens를 늘리는지 synthetic fixture로 확인한다. 현재 off라 기본 실행 결과에 직접 영향은 없다.
- merge_ocr_stream 기본 gap .8초는1초 sampling과 같지 않아 동일 텍스트를 이어 붙이지 못하지만 제품은 별도1.5초 dedup을 쓰므로 이 값만 보고 제품 dedup이 없는 것으로 판단하지 않는다. 두 ocr_blob_in_range 정의는 move-only 주석대로 뒤 정의가 유효하다.

## 11. W12 후 대사 평가: 고정 evidence 소규모 대조부터

이번 session의 다음 단계 제안은 전체 pipeline 반복 실행이 아니라 검토/승인된 로컬 artifact를 고정한 소규모 대조다. 별도 실행 범위가 확정될 때까지 ML/provider 호출은 하지 않는다. 24 provider requests와 $2는 예시 상한이며 main/retry/repair/실패 요청 모두 포함한다. 비용 상한을 현재 pricing 확인 없이 보장하지 않는다.

### 11.1 동일 입력 품질 기준과 분리

사용자가 지정한 source(파일 hash,duration,fps,해상도,audio tracks), 9/4 baseline SHA와 current SHA, OS/hardware, actual model/device/precision/weight snapshot hash, installed versions, prompt/env overrides를 기록한다. 기준은 소스 진실값과 사용자 기대이며 이전 결과 자체를 정답으로 삼지 않는다.

첫 입력은 종합 인계의 T1~T3 원본 3개×180초 이하, 합계9분 이하로 한정한다. STT segments/words/shots/diffs와 source-relative truth interval, 대표 누락/오타·title issue를 묶는다. raw/full source를 반복 decoding하는 대신 artifact validation→candidate deterministic comparison→선택/metadata prompt 소량 비교→UI/clip 확인을 단계 분리한다.

- STT: 동일 excerpt의 사람이 교정한 transcript로 CER/WER, entity·숫자·고유명사 오류, timestamp deviation, hallucination/silence insertion. STT artifact가 동일하면 이후 raw export/title 변화로 STT 품질이 변했다고 쓰지 않는다.
- candidate: 고정 analysis/LLM sentence fixture로 interval 수/길이, human gold recall atK(temporal IoU≥.5), overlap duplicate, beginning8초 제외/짧은영상 min6의 영향, text-density/visual/audio score 기여 분포. score normalization·strongbreak·fallback은 각 하나만 ablate한다.
- title: 동일 selected candidate/STT/canonical input에 9/4 vs current prompt 출력(소수 seed/repeats)을 blinded pair review. 두 줄18자 준수/keyword-list/가독성/훅/clip 의미 정합/이름·숫자 hallucination, bad-title detect false positive/negative, repair 개선/악화와 비용·시간. current repair on/off를 분리해 prompt 효과와 extra call 효과를 혼합하지 않는다.
- final boundary/render: sentence cut/음절 잘림/완결성, actual end/video bound, title⇔clip⇔summary/reason identity, raw aspect/odd-resolution/audio/subtitle와 final cover/contain crop를 별도 체크한다. boundary 밖 extension은 current trim으로 해결되지 않는다.

### 11.2 OCR A/B: 단계적·동일 입력·장치 적합

A=current False, B=isolated evaluation harness에서 True/현행1fps·ko/en·minlen2. 현재 제품에 OCR env toggle이 있다고 가정하지 않는다. 제품 default 파일을 수정하지 않고 이후 허가된 임시 evaluation branch/harness와 artifact derivative만 쓴다. CUDA 환경과 사전 설치/weight preprovision이 확인된 B만 유효하다. MPS/CPU는 skip-contract 확인용이며 A/B 품질쌍으로 계산하지 않는다. 실제 라이브러리·weight license/상업 이용·revision은 실행 전에 공식 근거로 별도 확인한다.

1. ML 없는 fixture 검토: dependency/weight/readiness/ok status, dedup recurring text, absent/invalid metadata, out-of-range boundaries, selected-ID mismatch. 이는 현재 코드 수정 허가가 아니다.
2. OCR-only 작은 pilot: 이미 추출 가능한 동일 source의 고정 frame/time samples(예: 각 evidence8프레임)를 대상으로 OCR 정확도/추가 facts/중복과 CPU decode·Reader cold load/VRAM을 측정한다. product1fps full sweep의 시간 추정과 sparse sampling의 결과를 구분한다.
3. artifact-grounded downstream pair: 같은 STT/shot/visual/audio artifacts에서 OCR evidence 유무만 바꾼다. story/canonical/selection/metadata 영향은 각각 비교한다. 비용 상한 안에서 complete pipeline 대신 selected fixed candidates의 metadata를 우선하며 raw provider request budget으로 stop한다. 결과만 보고 candidate recall 개선이라고 주장하지 않는다.
4. pilot이 유용하면 새로운 입력·회수·시간/비용 상한을 정해 product end-to-end A/B를 별도로 계획한다. cold fresh-process와 warm-process를 분리하고 장편 평가는 소규모 대조 통과 후 확대 여부를 결정한다. 전체 pipeline 반복·장편 실행은 현재 제안 상한에 포함하지 않는다.

각 A/B의 OCR off/skipped/failed/success와 frame coverage를 필수 기록한다. STT/scene boundaries와 title repair는 다른 평가 축이다. failed OCR을 정상B의 빈 결과로 섞지 않는다.

### 11.3 측정 항목과 채택 기준 초안

| 축 | 기록/계산 |
|---|---|
| OCR 품질 | annotated screen text precision/recall/CER, unique useful facts/names recovery, duplicate rate·sample coverage·confidence 없는 출력의 error propagation |
| output 품질 | canonical factual error, candidate recall/duplicate, blinded title grounding·hook/readability, sentence completeness/cut 오류. 영상 단위 paired difference와 bootstrap CI; frame 수를 독립 표본수로 부풀리지 않음 |
| 시간 | ready/fileprefetch/Reader init/STT/OCR/shot/CLIP/MFCC/local build/mainLLM/repair/export/thumbnail 단계wall, end-to-end P50/P95/real-time factor, cold/warm 구분. OCR elapsed_sec 단독 금지 |
| RAM | root와 recursive children RSS를 동일 시각에 합산한 tree peak/time curve, baseline/cached model delta, peak stage, duration별 slope. root peak와 child peak 각자 max를 단순 합산하지 않음 |
| GPU | system VRAM/NVML 및 allocator allocated/reserved, model warm state/fallback. torch와 CTranslate2 수치가 같은 범위를 나타낸다고 가정하지 않음 |
| 비용 | provider actual requests B+5+R+P; operation/model/input+cached/output/reasoning usage, failed attempt/repair도 포함. 검증일 rate 적용 provider currency와 credits/ceil-min 정책을 별도 산정 |
| 상태/UX | cancel 요청→Python 실제 종료 시간/잔여child/job overlap, pending→ready/unavailable, poll stop/reopen, trim edit source, shortform raw crop/fit/title consistency |

채택 gate 예시(사용자가 평가 시작 때 확정): 화면글이 유용한 그룹에서 useful fact/gold highlight recall ≥5pp 개선 또는 동일 품질을 더 낮은 비용에 달성; factual/title hallucination·cut 오류는 유의한 악화 없음; negative control(화면글 없는 대화)은 품질 악화≤2pp; 허용한 latency/RAM/VRAM/provider 비용 상한 안에서 완료. p95 추가 지연≤15% 같은 수치는 제품 요구와 pilot을 보고 조정하는 제안이지 사전 입증된 한계가 아니다. 품질효과가 특정 유형에서만 나오면 전체 OCR on 대신 선택적 사용/미채택을 논의한다. 오래된 모델명 또는 OCR 텍스트량 증가만으로 채택하지 않는다.

## 12. 현재 잔여 문제·가설·작은 검증 순서

| 우선/문제 | 근거 | 가설/다음 검증 |
|---|---|---|
| P1 cancellation/compute overlap | app.py85, SDKbase316, LocalRunner162, jobs492 | cancel 후 refund/UI는 끝났어도 worker가 남아 다음 분석과 동시 실행 가능. 작은 instrumented stub부터 확인하고 실제MLcancel은 별도 허가 |
| P1 malformed metadata | segmentation821, staged426/590 | JSON object만 보장하며 invalid entry/start/end/title type은 snap/sort에서 fallback 전에 예외 가능. 합성fixture로 failure vs fallback 확인 |
| P1 range/title identity | staged575/590; NE detail90/123 | metadata row 일부 제외/순서중복/최종clamp 시 위치 title/summary association이 틀어질 수 있음. stable cand/clip ID fixture 검토; 현재 실영상오류를 단정하지 않음 |
| P1 OCR enable reliability | dependency없음, analyze115 | silent failure/분리없는status로 실제A/B가 잘못될 수 있음. 모델 readiness/ok/coverage·dedup 검증 후 실행 |
| P1 resource observability | EL monitor305; caches/STFT/MFCC | FFmpeg child·long duration peak누락, readywarm착시. tree/time/actualdevice 측정 |
| P2 LLM 비용·tail latency | fullSttText 반복, 2attempts, repair | prompt token growth/truncated reply/앞단재실행이 비용주요축. fixedevidence token cap/retry/repair 별도 집계 |
| P2 candidate 품질 | score160, snap830, min6, firstfallback478 | density/scene break가 말 흐름보다 강할 수 있음. deterministic ablation·blinded interval review |
| P2 source/backfill/render concurrency | sources247, backfill81 | 준비재probe/GETbackfill이 실제 실행 peak와 UXwait를 늘릴 수 있음. source별stage timing/owner concurrency |
| P3 선언/설정 정리 | common·manifest | 값만 읽은 문서가 실제 동작을 오해. 코드교정은 향후 선택개선 session으로 분리 |

이번 조사에서는 위 ML/fixture/API 검증을 실행하지 않았다. W12 종합 문서와 카드·보드에는 확인된 동작, 역사 evidence, 새 실측 가설, 다음 실행 제안을 구분해 인계한다. 제품 코드는 변경하지 않았다.

## 9/29 제목 후속 조사

[9/18 제목 prompt·나열형 detector·repair 이전/이후 상세](29-title-change-detail.md). 작성자·date·parent diff·관련 문서와 실제 보정 한계를 추가 확인했다. 모델/API 실행·제목 품질 A/B는 하지 않았다.
