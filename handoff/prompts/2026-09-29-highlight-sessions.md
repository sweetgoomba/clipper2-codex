# 2026-09-29 — 안무·인물·대사 개별 새 세션 시작 프롬프트

아래 세 블록을 각각 별도의 새 작업 세션에 붙여 넣는다. 이번 조사에서는 새 세션을 자동 생성하지 않았다.

[조사·설계 종합](../../features/highlights/records/2026/09/29-pipeline-design-handoff.md) · [후속 사용자 결정·설명](../../features/highlights/records/2026/09/29-user-feedback-clarifications.md) · [WORKBOARD](../WORKBOARD.md)

## 1. 안무 — 정확도 분해·기존 편집 검증·인물 crop·원본 타임라인

```text
Using Superpowers.

프로젝트 루트는 /Users/jina/project/adlight.
이 세션은 W13 안무 하이라이트 후속 조사·설계와 사용자 선택 범위의 개선을 맡는다.

먼저 다음 문서를 읽어줘.
- .codex/handoff/WORKBOARD.md
- .codex/handoff/tasks/highlight-overview.md
- .codex/handoff/tasks/dance-highlight.md
- .codex/features/highlights/records/2026/09/29-pipeline-design-handoff.md
- .codex/features/highlights/records/2026/09/29-dance-code-history.md
- .codex/features/highlights/records/2026/09/29-official-model-candidates.md
- .codex/features/highlights/records/2026/09/29-face-change-detail.md
- .codex/features/highlights/records/2026/09/29-user-feedback-clarifications.md
연결된 요구와 현재 코드·Git 이력을 대조하고 사실/사용자 보고/가설/미검증을 구분해줘.

9/29 조사 Python HEAD는 47782953228861f4bdbdc135265d067c2a826b0e,
Nest는 824a7a9f71dde8aa44c8692eadacb6ba6e4961b8,
Angular는 797782e8f8e1c8488d024d23e6291e91c2b1e30e다.
이는 fetch하지 않은 로컬 dev 기준이다. 먼저 read-only로 현재 상태를 확인하고,
실제 코드 수정 대상이 정해지면 필요한 repo만 최신 origin/dev를 확인한 뒤
새 브랜치·격리 worktree를 준비해줘. Desktop/Web 형제 상대경로를 유지하고
다른 세션의 작업 공간과 기존 미커밋 변경을 보존해줘.

현행은 YOLOv8s Pose → main 선정 → IoU track → OpenCV YuNet/SFace
→ cluster → 참조 이미지 평균 embedding 매칭 → 개별 clip export다.
메인 댄서 선정과 identity를 별도로 평가해줘. 7/1 fe223e3 얼굴 backend·표본·매핑,
8/13 86fc71a 단일 참조 멤버 과잉 매핑 방지, 9/18 montage 제거를 조사 기준선으로 삼되
‘예전보다 정확도가 떨어졌다’는 동일 입력 평가 전 가설로 유지해줘.
main score의 pose_energy가 관절 거리 합인 점, skip4와 원본 fps streak의 실효 시간,
얼굴 미검출 또는 track 평균에 필요한 유효 표본이 부족한 main segment가
unknown 카드로 남지 않고 drop되는 점도 확인해줘.

이미 구현된 개별 clip 이동·숨김·되돌리기·인물 묶음 배정·숏폼 생성은 재구현하지 말고
현행 계약과 필요한 검증을 확인해줘. 안무 trim은 현재 거절되는 경로다.
복수 선택 → 목적 인물 선택 → 일괄 적용/되돌리기와 드래그 보조를 비교하고,
batch 원자성·edit revision·자동 판정 보존·재분석 시 override 처리 범위를 설계해줘.

가로 원본을 1:1/4:3 템플릿에 넣을 때 메인 인물이 이동해 화면 밖으로 나가는 문제를 다뤄줘.
현재 bbox/track는 최종 dance_meta에 남지 않고 preview/render는 center crop다.
source-relative track keyframe sidecar → clip/trim/render 시간 변환 → 같은 preview/render
crop 경로를 먼저 설계해줘. 전신 보존·smoothing·shot cut·짧은/긴 누락·인물 교체·contain fallback,
멤버 재배정이 실제 다른 사람의 crop track 확보를 뜻하는지도 검증 항목에 넣어줘.

원본 타임라인에서 자동 장면 경계·main 인물·탈락 사유를 보여주고 경계/제외/재배정을 검토한 후
실제 clip을 생성하는 흐름을 현행 전량 export 및 선택 재export 중간안과 비교해줘.
분석 완료/review-ready/export 완료, draft/project/job, 원본 보존, cache/revision,
취소·재개·ffmpeg 경계 정확도·대기시간을 구체화하고 생성 지연을 확정 요구로 취급하지 말아줘.

얼굴 공통 모듈은 향후 다른 플러그인도 재사용할 공개 API와 관측 계약을 갖춰야 한다.
안무·인물은 초기 소비자이며 이용 대상을 두 이름으로 제한하지 말아줘.
W14가 공통 경로 초기 작업 소유, 이 세션은 main·멤버 mapping·crop 소비자라는 제안을 재확인해줘.
계약 합의 전 같은 공통 Python 파일을 두 세션이 동시에 수정하지 말아줘.

우선 코드·이력·실험 manifest·선택 scope의 설계 산출물을 작성해줘.
실제 ML 전에 정확한 원본 경로/hash, 구간, 참조 이미지, 라벨, 모델 hash, OS/device,
실행 SHA/횟수·시간·자원 상한·출력 위치를 사용자와 확정해줘.
첫 제안은 중앙/교체·좌우 이동·가림 사례 3개×120초 이하, 합계6분,
현행3pass+대조 조건 하나3pass 최대6pass의 metadata 평가다.
현행 run()은 export까지 수행하므로 export 없는 평가 adapter 준비를 선행 조건으로 두고,
그 전에는 기존 artifact 정적 비교만 진행해줘.
메인 정확도/전환 지연과 조건부 identity precision·unknown 오배정률·전체 coverage를 분리해줘.
crop은 4개×10초×2ratio×center/follow=16개 결과부터 제안해줘.
역사 모델 weights의 상업 이용조건·보유/다운로드 승인 조건이 맞지 않으면
이전 artifact/로그로만 비교해줘. 실제 실행 완료라고 표현하지 말아줘.

최신 모델 후보는 공식 문서·논문·모델 카드의 날짜/weight license/OS·hardware를 재확인하고
upstream 벤치마크를 우리 정확도로 환산하지 말아줘. 한 번에 모델·tracker·UX를 모두 바꾸지 말아줘.
ML/모델 다운로드/외부 과금/Build5는 지정된 입력과 실행 범위 안에서만 진행해줘.
서버 실행 방식과 commit/push/merge/deploy는 기존 사용자 지시를 따르고,
종료 시 W13 카드·WORKBOARD·날짜별 기록에 근거/검증/남은 결정을 갱신해줘.
```

## 2. 인물 — 참조 없는 grouping MVP·인물 전부 표시·대표 이미지·선택 export

```text
Using Superpowers.

프로젝트 루트는 /Users/jina/project/adlight.
이 세션은 W14 신규 인물 하이라이트의 구상·MVP·계약·검증 설계를 맡는다.

먼저 .codex/handoff/WORKBOARD.md, .codex/handoff/tasks/highlight-overview.md,
.codex/handoff/tasks/person-highlight.md, .codex/handoff/tasks/dance-highlight.md,
.codex/features/highlights/records/2026/09/29-pipeline-design-handoff.md,
29-dance-code-history.md, 29-official-model-candidates.md,
29-user-feedback-clarifications.md와 29-face-change-detail.md를 같은 조사 폴더에서 읽어줘.
출력/MVP는 승인된 구현 스펙이 아니라 제안 상태다. 먼저 사용 목적과 성공 기준을 확인하고
2~3개 접근의 trade-off와 첫 버전 범위를 구체화해줘.

원하는 기능은 참조 이미지를 미리 고르지 않고 영상 안의 같은 사람 등장 구간을 묶는 것이다.
첫 가정은 인터뷰·토크의 소수 반복 인물이며, 드라마·예능 및 행사·거리·브이로그와 비교해줘.
익명 Person 1/2 grouping, 선택적 참조 이미지 검색, face+body/화자 fusion의 차이를 설명하되
실명 식별이나 얼굴=화자 판정을 기본 기능으로 넣지 말아줘.

대표 얼굴 카드 → 해당 인물의 source 구간·장면 목록·원본 seek preview →
오분류 장면 재배정/그룹 병합/이름·대표 이미지 수정/제외·복원 →
선택 경계 검토 → 단일/복수 MP4·ZIP export를 MVP 후보로 다듬어줘.
선택 구간을 하나의 MP4/쇼츠로 합치기는 포함 여부를 별도 선택하고
순서·동일 편집 source 구간의 중복 제거·원본 소리·총 길이·과금/취소/재개를 설계해줘.
같은 scene ID라도 편집 경계가 다른 구간은 보존하고 겹치는 다른 구간의 합침은 별도 선택으로 둬줘.
템플릿/BGM/자동 타이틀/crop/ReID를 모두 첫 버전에 넣지 말아줘.

사용자 결정: 배경·잠깐 지나간 사람 포함, 검출된 모든 인물 그룹을 기본 목록에 표시해줘.
결과가 복잡해져도 자동 배경 숨김/제외·soft filter·시간/반복/크기 표시 제한은 후속으로 미뤄줘.
그룹 판정이 불확실한 관측도 확인 필요 결과로 보존하고 모델 미검출과 결과 숨김을 구분해줘.
대표 이미지는 선명도·가림·얼굴 크기·centroid 대표성을 이용하고 사용자 교체를 보존해줘.
얼굴 없는 구간, shot cut·재등장, 동시 출연, unknown, false split/merge의 보장 범위를 정해줘.

안무 현행은 main 한 명만 IoU tracking하고 main segment에서만 얼굴 embedding을 뽑는다.
현재 ROI 최고 점수 얼굴 하나 반환과 단일 main용 TrackAssigner를 일반 다중 인물 추적으로
그대로 쓰지 말아줘. 모든 유효 얼굴 관측 → shot-local 다중 track → embedding →
영상 단위 cluster → 등장 interval을 설계해줘. 동시 출연 두 얼굴의 잘못된 합침을 제약/지표로 다뤄줘.
한 Scene에 여러 PersonGroup이 속하는 다대다 관계가 필요하며
현행 clip.personId 하나, category와 shortform origin의 dance/dialog 전용 계약은 확장 검토 대상이다.
선택 export도 현행 전체/한 인물 ZIP과 차이가 있으니 계약을 먼저 정해줘.

얼굴 공통 모듈은 향후 여러 플러그인이 재사용할 독립 패키지/공개 API로 설계해줘.
안무·인물은 초기 소비자이며 공개 입출력을 dance Segment/PersonGroup/UI/job에 종속시키지 말아줘.
검출·정렬·embedding/거리·품질·대표 이미지 후보와 source/model/config hash, time base,
pixel/normalized bbox, observation/track ID/version·실패 상태·backend 교체 규칙을 정의해줘.
플러그인별 선택 의존성/venv·모델 준비를 유지하고 기본 SDK 시작 경로에 ML을 강제하지 말아줘.
W14가 공통 경로 초기 작업 소유, W13이 기존 adapter·main/mapping/crop 소비자라는 제안을
서로 확인하고 파일 소유권·merge 순서·compatibility test를 인계에 남겨줘.
서로 다른 모델 embedding 공간/cache/threshold를 혼용하지 말아줘.

우선 read-only 코드 조사와 MVP·artifact·UI·평가 설계만 진행하고
선택 scope의 Superpowers 설계/계획 절차를 거친 뒤 구현 범위를 정해줘.
실제 수정은 필요한 Python/Nest/Angular repo와 plugin 등록용 Electron,
신규 과금/권한 계약이 필요할 때만 Web API의 최신 origin/dev에서
새 브랜치·격리 worktree를 준비하고 형제 경로와 다른 세션 변경을 보존해줘.
9/29 조사 baseline SHA는 종합 인계 문서 §2에 있으며 원격 fetch로 보증된 상태는 아니다.

실제 ML 전에 정확한 입력 경로/hash·구간·GT 익명 인물/등장/배경/동시 출연 라벨,
모델 hash·OS/device·SHA·횟수/시간·자원 상한·출력 위치를 확정해줘.
첫 제안은 인터뷰·재등장/동시 출연·배경 사례 3개×120초 이하 합계6분,
다중 얼굴 평가 adapter 준비 후 face-only 관측 추론 최대3회,
같은 관측/embedding에서 grouping 기준 하나를 대조해 최대6개 조건 결과를 제안해줘.
soft-filter 대조는 하지 말고 모든 인물 결과의 누락·잘못된 합침·쪼개짐을 평가해줘.
pairwise/B-cubed 지표와 배경·단역 포함 인물 interval recall·false merge/split,
대표 이미지 품질·수정 횟수/탐색 시간·중복 export·수정 보존을 분리해줘.
이 제안은 실행 승인이나 성능 결과가 아니다. 새 모델 다운로드/외부 유료 API/Build5는 별도 범위를 정해줘.

공식 모델·논문·모델 카드로 최신성·weight/code license·Mac/Windows·CPU/CUDA 지원을 재확인해줘.
종료 시 W14 카드·WORKBOARD·날짜별 기록·W13 공통 계약 인계에
결정·근거·실제 검증·미검증·남은 입력을 기록해줘. 새 작업 세션은 자동 생성하지 말아줘.
```

## 3. 대사 — 민준님 변경·STT·후보·타이틀·OCR·비용 분리

```text
Using Superpowers.

프로젝트 루트는 /Users/jina/project/adlight.
이 세션은 W01 대사 하이라이트의 현행 조사·평가 설계와 사용자 선택 범위 개선을 맡는다.

먼저 .codex/handoff/WORKBOARD.md, .codex/handoff/tasks/highlight-overview.md,
.codex/handoff/tasks/dialog-highlight.md,
.codex/features/highlights/records/2026/09/29-pipeline-design-handoff.md,
29-dialog-code-history.md, 29-official-model-candidates.md,
29-title-change-detail.md와 29-user-feedback-clarifications.md를 같은 조사 폴더에서 읽어줘.
.codex/main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md는
과거 기준선으로 읽고 현행 대조표의 수정사항을 우선해줘.

9/29 Python/Nest/Angular/Web API baseline SHA는 종합 문서 §2에 있다.
read-only로 현재 dev/clean/commit 포함 여부부터 확인하고, 실제 수정 대상이 정해지면
필요한 repo만 최신 origin/dev에서 새 브랜치·격리 worktree를 준비해줘.
Desktop/Web 형제 상대경로와 기존 미커밋 작업을 보존하고 옛 dialog worktree를 최신 공간으로 쓰지 말아줘.

Python faster-whisper small·OpenCLIP·shot/feature·후보 로직 → Nest 단계 orchestration과 LLM 사이 artifact 저장
→ Web API OpenAI Responses 문장/줄거리/용어/주제/선택/타이틀 → Python 원본 비율 clip export
→ Angular clip-local trim·숏폼 생성/재편집이라는 현행 구조부터 재확인해줘.
저장 artifact의 resume는 없다. 현행 STT는 word timestamps ON·VAD OFF이며 Mac은 CPU int8이다.
기본 LLM은 gpt-5-mini이며 실제 환경 override/서버 배포 모델은 별도 확인 대상이다.
Python 직접 LLM stub이나 다른 기능의 Gemini를 대사 현행으로 설명하지 말아줘.

민준님 변경은 author/commit/date/diff로 설명해줘.
9/18 Python 49838e0/8bc9501의 제목 번인 제거·원본 비율+타이틀 분리,
Web API af664d7의 overlay_title/나열형 제목 repair,
Nest/Angular legacy raw clip 백필·ready/pending/unavailable·숏폼 생성/복원을 검증해줘.
9/4 감사의 ‘원본 전체 타임라인 trim’은 당시 코드에도 맞지 않은 문서 오기다.
현행 trim은 추출 clip 내부이며 의미 경계를 원본 구간 밖으로 확장하는 기능과 구분해줘.
Angular preview/quote → durable job·operation start → 큐 → runtime lease → Nest 실제 source ingest
순서를 확인하고, 과금 뒤 실제 ingest가 진행되는 현행과 과거 설명을 대조해줘.

STT, topic/후보·score·경계·중복, select_highlights, title 생성/repair를 각각 평가해줘.
STT·선택 구간을 고정해 타이틀 품질 원인과 OCR evidence 효과를 분리하고
이름·숫자 오류, 완결성·후킹·독립성·근거 없는 주장·키워드 나열·두 줄 길이를 점검해줘.
warmup 파일 준비 vs 실제 모델 load, chunked mel 이후 waveform/final mel/word·librosa 메모리,
retry/artifact 저장과 resume 부재, 실제 provider 호출수·token·credit 차감의 차이도 확인해줘.
기존 CPU·리소스 안전성 구현을 중복 개발하지 말아줘.

OCR은 EasyOCR ko/en full sweep이지만 RUN_OCR=False, CUDA gate, 의존성 부재가 겹친다.
Mac에서 상수만 켜서 ON 결과가 생긴다고 가정하지 말아줘.
package/model 준비와 device gate, sample/ROI/shot 전략, bbox/confidence 보존,
evidence downstream 연결을 먼저 설계하고 OFF/ON 비교로 품질·시간·자원을 측정해줘.
꺼둔 이유는 실제 기록/commit으로 확인된 것만 말하고 CPU 성능 탓으로 추정 확정하지 말아줘.

최신 STT/타이틀/OCR 후보는 공식 자료를 다시 확인해줘.
9/29 조사 모델 문서의 GPT-6 Luna 등 후보는 자동 교체 결정이 아니다.
supportsReasoning prefix·reasoning effort·max_output_tokens·Responses schema·가격·timeout,
STT word timestamp/한국어·CT2/MPS/CPU/CUDA·packaged asset 계약과 상업 weights를 확인해줘.
‘최신 모델이므로 더 정확하다’고 결론내리지 말아줘.

먼저 조사 delta·실험 manifest·설계와 첫 개선 하나를 선택할 수 있는 근거를 작성해줘.
실제 ML 전에 입력 원본 경로/hash·구간·GT transcript/word 표본/OCR/타이틀 근거,
모델 hash·OS/device·실행 SHA·회수/시간/자원·출력 위치·외부 전송·비용 상한을 확정해줘.
첫 제안은 깨끗한 인터뷰·BGM/겹말·화면 글자 보완 사례 3개×180초 이하 합계9분,
small3pass+후보 하나3pass 최대6pass; OCR ON은 고정 STT artifact에서 최대540프레임(1fps)이다.
title/candidate는 고정된12개씩의 evidence를 batch로 비교하고
provider repair/retry 포함 최대24calls와 총$2 중 먼저 도달하는 상한을 제안해줘.
이 상한은 현재 승인된 예산이 아니며 전체 pipeline 실행과도 다른 평가다.
현행 전체 workflow는 문장 분할 batch B+5 logical calls, retry R·내부 repair P를 더한
B+5+R+P provider calls다. 주제 개수는 token량에 영향이 있고 요청 수와 구분해줘.

한국어 CER/WER·고유명사/숫자·경계 오류·후보/제목 blind 평가·OCR positive/negative 효과,
phase elapsed·cold/warm·process-tree RSS/VRAM·provider token/비용·실패/취소를 따로 기록해줘.
모델 다운로드/유료 호출/실제 ML/Build5는 지정한 입력과 실행 범위 안에서만 진행하고
서버 실행 방식·commit/push/merge/deploy는 기존 사용자 지시를 따라줘.
종료 시 W01 카드·WORKBOARD·날짜별 기록에 결정·근거·실행한 검증과 남은 입력을 갱신해줘.
```
