# W13 안무 후속 조사와 비교 평가 설계

2026-09-30 KST. **조사·설계 초안 / 사용자 대상·범위 선택 대기.** 제품 코드, 영상 추론·렌더, 모델 다운로드, 외부 유료 호출, Build5, fetch, commit/push/merge/deploy는 수행하지 않았다. 이 기록은 9/29 W12 조사와 9/30 로컬 read-only 대조를 합친다. 실행 결과가 아니다.

## 1. 기준과 증거 구분

| 구분 | 확인 내용과 한계 |
|---|---|
| 코드 사실 | Python `47782953228861f4bdbdc135265d067c2a826b0e`(9/29 기준과 현재 일치). Nest 현재 `c8b8b074d083c6e0632e795b1da94b0d32f64118`, Angular 현재 `5570f8ca0452de1d778acfac74d343f632d0ccc1`는 9/29의 `824a7a9`, `797782e` 이후다. 원격 최신 여부는 fetch하지 않아 모른다. |
| 사용자 보고 | “예전보다 정확도가 떨어졌다”, 가로 영상을 1:1/4:3에 넣으면 이동한 메인 인물이 화면 밖으로 나간다. 재현 입력·정답 라벨이 아직 없다. |
| 가설 | 얼굴 backend/표본/매핑 변화, 현재 main 휴리스틱, IoU track 교체, 탈락 처리, montage 제거로 달라진 결과 체감이 기여했을 수 있다. 각각의 효과·회귀 인과는 미측정이다. |
| 미검증 | 동일 원본 old/new 정확도, Mac/Windows parity, 최신 origin/dev, 실제 설치 모델 hash/device, crop 전신 보존, UX 소요 시간, 서버 실행·배포 상태. |

루트 `/Users/jina/project/adlight` 자체는 Git 저장소가 아니다. `.codex`와 `desktop/clipper_*` 등은 독립 저장소다. `.codex`에는 여러 세션의 미커밋·미추적 문서가 있고 Angular에는 다른 설계 문서의 미커밋 변경이 있다. 이 파일과 W13 카드·WORKBOARD·날짜 기록만 갱신한다. 코드 수정 범위가 결정되면 필요한 저장소만 `origin/dev`를 확인하고 Desktop/Web 형제 상대경로가 유지되는 새 브랜치·격리 worktree를 준비한다.

## 2. 코드·이력 대조

현행 연결: `yolov8s-pose.pt` → 매 4원본 프레임의 후보 중 main 선정 → 선택된 bbox 하나에 IoU/TTL track → raw/smooth/group 유사 구간 처리 → OpenCV YuNet/SFace ROI 얼굴 표본 → track 평균 embedding → cosine/average cluster 및 작은 cluster 병합 → 참조 이미지별 평균 embedding과 거리 기반 멤버 매핑 → main/group 개별 clip export와 main thumb export → `dance_meta_v1`. [코드·Git 상세](29-dance-code-history.md).

`segment.py`의 main score는 중심 .45 + bbox 면적 .35 + `pose_energy/300` .20이다. `pose_energy`는 **같은 프레임의 어깨·팔·골반 관절 거리 합(픽셀 거리)**이고 프레임 사이 속도·움직임이 아니다. keypoint confidence/visibility를 점수 계산에 쓰지 않는다. `MainSelector(fps=원본 fps)`의 streak은 실제로 `analyze_skip=4`마다 한 번 증가한다. 30fps에서 분석 간격은 약 133ms다. BASE 7회는 첫 후보 sample부터 판정 sample까지 6간격=0.8초, 첫 후보가 나타나기 전 위상까지 포함한 지속 요구는 최대 약 0.933초다. FAST 3회는 0.267~0.4초, group enter 10회는 1.2~1.333초, exit 7회는 0.8~0.933초다. 의도한 원본 fps 기준 0.25/0.10/0.35/0.25초와 다르다. 즉시 hard switch·후보 상태·검출 누락 때문에 실제 전환 지연이 이 범위에 항상 든다는 뜻은 아니다. 현행 구조의 발생 시점은 4/17 이식이므로 최근 회귀의 증거는 아니다.

얼굴 분석은 main segment만 수행한다. `face_cluster.py`의 track 평균에는 유효 embedding이 최소 2개 필요하다. `pipeline.py:478`은 `face_detected`가 거짓이거나 `track_embeddings`가 비면 main segment 자체를 건너뛴다. 이는 `unknown` 카드 보존 이전의 **coverage 손실**이다. 남은 구간도 cluster vote가 없으면 `unknown`, 참조 매칭이 없으면 `person_N`일 수 있다. 최소 2표본과 drop 규칙은 7/1 전 코드에도 있었으므로 새 회귀 원인으로 단정하지 않는다. 평가에는 raw/smoothed/kept/drop 모두 별도 보존해야 한다.

| 변경 | 코드로 확인한 내용 | 평가 해석 |
|---|---|---|
| 7/1 `fe223e3` | InsightFace `buffalo_l` CPU에서 OpenCV YuNet/SFace로 교체. 후보 5→12 중 품질 상위 5, greedy primary mapping도 함께 변경. cluster .42·member .60은 유지. [상세](29-face-change-detail.md) | 하나의 모델 교체 효과로 귀속 불가. 당시 Mac 실행은 산출물 생성 확인이며 라벨 정확도 비교가 아니다. |
| 8/13 `86fc71a` | 이미 배정된 단일 참조 멤버에 추가 cluster를 붙일 때 `min(.45, primary distance+.08)` 제한. 뒤이어 설정 노출. | 과잉 매핑 감소 가능성과 같은 사람 split 증가 가능성을 함께 측정. |
| 9/18 `49e7827` | montage 생성 제거. 개별 clip·person 출력 유지. | 결과 화면 구성 변화를 검출 정확도 변화와 분리. |

현행 단일 clip 이동·숨김·되돌리기, 인물 묶음 배정, 하이라이트→숏폼 생성은 Nest/Angular에 있다. `dance_clip_assignments`와 `dance_hidden_clips`는 원본 `dance_meta`와 별도 overlay다. 단일 이동 API는 원래 배정으로 옮길 때 override를 지운다. 안무 trim은 `ClipTrimService`의 경로에서 거절되며 UI·저장·미디어 작업까지 포함한 새 계약 없이는 가능하다고 표시할 수 없다. 재검증 항목은 단일 이동/undo, 숨김 복원, 인물 배정과 clip override의 우선순위, 숏폼 manifest/렌더 경로 유지다.

## 3. 정확도 평가 설계

**10/1 사용자 정정:** 메인은 한 명으로 제한하지 않는다. 공동 메인은 여러 명으로 기록하고, 불확실한 장면은 `확인 필요`로 보존한다. 그룹과 사람별 메인도 함께 존재할 수 있다. 의상 색이나 기존 앱의 예측 이름을 정답 멤버명으로 요구/사용하지 않는다. [다중 메인·보류 계약과 지표](../10/01-w13-multi-main-retention-design.md)가 이 단락의 단일 `main ID` 가정보다 우선한다.

첫 제안은 D1 중앙/리드 교체, D2 큰 좌우 이동, D3 가림·뒤돌기·작은 얼굴에서 각각 120초 이하, 합계 6분 이하였으나 첫 영상 `yFTAYXDTjqI`는 사용자가 **원본 전체 133.654초**를 선택했다. 비교 interval의 원본 시간축 GT에는 `main track ID 집합`과 사람별 bbox, group, `확인 필요`, face-visible, 독립적으로 확인된 member 또는 unknown, shot cut을 분리해 라벨한다. 참조 이미지는 조건 간 동일하게 고정한다. **메인 선정과 identity를 분리**하려고 identity는 (a) 현행 main ROI와 (b) GT 사람별 ROI의 조건부 결과를 별도 계산한다. (b)는 판정 전파 오차를 분리하는 분석용이며 제품 결과로 세지 않는다.

1. **정적 artifact 비교 우선:** `legacy/adlight_python/output/highlight_projects/*/json/dance_meta.json`의 JSON 49개를 읽기 전용으로 확인했다. 모두 `dance_meta_v1`이고 집계 `dropped_main_no_face`는 25다. 저장된 `input_video` 문자열이 동일한 artifact 쌍은 0개였으며 원본 파일 hash·라벨·실행 SHA까지 맞춘 old/new 쌍은 확인되지 않았다. 이는 49개가 모두 다른 원본이라는 증명이 아니다. 현재 정적 자료만으로 전후 정확도 표를 만들지 않는다. 추가 JSON·clip·로그가 실제 남아 있으면 SHA/모델/입력·참조/구간 차이를 적어 나란히 읽고, 조건이 다르면 인과 주장 금지. 과거 InsightFace weights의 상업 이용권과 보유/다운로드 승인이 맞지 않으면 역사 비교는 여기로 제한한다.
2. **평가 adapter 선행:** 현행 `run()`은 참조 이미지 다운로드와 main/group export까지 수행한다. 제품 판정 함수를 재사용하면서 영상 생성·제품 project 쓰기를 하지 않는 metadata 전용 adapter를 별도 승인 범위에서 준비한다. adapter가 없으면 새 3pass를 돌리지 않는다. raw/smoothed/kept/drop, bbox/track, 검출 수·유효 embedding 수, cluster/매핑 거리·거절 이유를 기록하되 원본 얼굴/embedding 자체는 manifest·로그에 복사하지 않는다. 동일 decode·sample·model/device 조건과 오류/취소 기록을 고정한다.
3. **최초 대조:** 현행 3pass + **선택한 변경 하나** 3pass, 최대 6pass(원본 재생 시간 누계 12분). 추천 첫 변경은 모델 다운로드가 필요 없는 skip/streak 시간 기준 보정이며, 어떤 가설을 먼저 고를지는 사용자 범위 선택으로 확정한다. 모델·tracker·UX를 한 번에 바꾸지 않는다. cold/warm과 추가 조건은 첫 결과 후 새 범위로 결정한다.

| 지표 | 분모·기록 |
|---|---|
| Main 정확도 | GT 메인 **사람 집합** 대비 시간 가중 사람별 recall/precision·집합 일치와 각 사람의 추가/제거 전환 지연(ms). 공동 메인 중 한 명만 맞히면 부분 적중과 나머지 누락을 함께 기록. group/비안무/보류를 별도로 기록. |
| 조건부 identity | **메인 사람이 맞고 그 사람의 이름이 독립적으로 확인되며 얼굴이 보이는** GT 구간에서 known 멤버 예측의 precision/recall을 계산한다. GT unknown 또는 참조 밖 인물을 known 멤버로 붙인 비율은 해당 GT 구간을 분모로 별도 기록한다. GT 사람별 ROI 분석을 별도 열로 둔다. |
| 전체 coverage | GT 안무 장면 시간과 메인 사람별 시간을 분리해 raw 검출, smooth, `확인 필요` 보존, 얼굴 표본 충족, kept/export 가능, 참조 매핑 가능 비율을 단계별로 기록. no-face/drop·group 겹침 공백·보류를 구분하고 보류를 identity 적중으로 세지 않는다. |
| Cluster/속도 | split/merge·한 참조 멤버 과잉 mapping, 단계별 wall time, peak process-tree RSS/VRAM, 오류/재시도. 평균만으로 심각한 오배정을 가리지 않도록 사례·분포를 같이 기록. |

## 4. 편집 UX 계약 후보

**추천:** 복수 clip 체크 → 목적 인물 카드/검색 선택 → 변경 전후 요약 → 한 번에 적용/한 번에 되돌리기. 드래그는 단일 clip의 보조 입력으로 두고 다중 drag는 선택 상태가 명확할 때만 허용한다. 순차 단일 API 호출은 초기 구현이 쉽지만 중간 실패와 다른 편집의 덮어쓰기·부분 undo가 생긴다. batch API는 선택 ID 전체 존재/권한/대상/expected `editRevision`을 먼저 검증하고 한 번의 원자적 저장으로 commit한다. 현재 `JsonProjectRepository.upsert()`는 메모리 map 갱신 후 `projects.json`에 직접 `writeFile`하며 CAS·프로젝트 잠금·임시 파일 rename이 없다. 따라서 **현재 저장소가 batch 원자성을 제공한다고 주장할 수 없다**. 채택 시 직렬화+revision CAS와 temp/rename 또는 등가의 crash-safe 저장을 함께 설계하고 실패·동시 요청 시험을 통과해야 한다. 충돌 시 409와 최신 revision을 반환한다. undo는 transaction ID와 각 clip의 이전 override(없음 포함)를 기록해 **그 batch만** 되돌리며 이후 다른 편집을 덮지 않도록 revision·대상별 충돌을 검사한다.

자동 판정 `dance_meta`는 불변 분석 결과로 남기고 member-level/clip-level override·hide·trim을 별도 edit layer에 둔다. UI는 자동 인물/현재 인물/사용자 수정 근거를 구별한다. 재분석 시 `sourceHash + analysisRevision + stable segment correspondence`가 확인된 override만 제안 매핑하고, 경계·ID가 달라진 항목은 검토 대기로 둔다. cluster 순번이나 `main_0001` 파일명만으로 새 분석에 override를 묵시 이전하지 않는다. trim은 원본 구간 편집 계약이 정해진 뒤에만 포함한다.

얼굴 미검출 또는 유효 표본 부족으로 탈락한 main 구간은 새 review 화면에서 `확인 필요` 후보와 정확한 사유를 표시하는 방향을 검토한다. 현재 `dance_meta_v1`에는 개별 탈락 구간/사유가 없어서 분석 artifact 추가가 선행된다. 자동 생성 목록에 포함할지와 사용자가 선택 export할 수 있게 할지는 실제 누락률·오탐 사례를 보고 결정한다.

## 5. 대상 추적 crop 설계

현재 `Segment.bboxes`는 `(sourceTime,bbox,trackId)` 픽셀 좌표이며 최종 `dance_meta_v1`에 없다. preview/render의 기본 `cover`는 중심 crop이다. clip을 다른 인물에게 재배정하는 것은 label 변경이며 **새 인물의 위치 경로 확보가 아니다**. 따라서 첫 구현 후보는 현재 main track의 source-relative keyframe sidecar(`sourceHash`, width/height/rotation, source timestamp, bbox, track ID, confidence/validity, shot ID, analysis version)와 sidecar hash를 결과 clip이 참조하는 방식이다. 새 인물 crop은 해당 인물의 검증된 track이 없으면 follow를 제공하지 않고 center/contain 선택을 요청한다. 이후 모든 인물 track 보존은 별도 평가·범위다.

`shot ID`와 rotation 정규화는 현행 Segment 산출물이 아니다. 원본 metadata/shot 경계 검출 또는 사람이 검토한 cut을 새 sidecar에 공급해야 하며, cut을 모를 때는 긴 누락·급점프를 안전하게 처리하는 fallback이 필요하다. sidecar의 track ID는 영상 내부 임시 ID이고 실명/영속 인물 ID가 아니다.

시간 변환은 원본 `sourceMs` → 편집 구간 `[editedStartMs,editedEndMs)` → clip-local `sourceMs-editedStartMs` → render-local `(sourceMs-editedStartMs)/playbackRate`(합성 slot 시작시각 가산)로 명시한다. 현재 export clip의 file-local 시각과 원본 시각이 같지 않으므로 각 media file의 `sourceOriginMs`, 실제 첫 frame PTS, 추가 in-file seek/trim을 기록해 이중 offset을 피한다. preview와 Python renderer는 **같은 versioned normalized trajectory와 보간·clamp·fallback 명세**를 각각 구현하고 동일 timestamp fixture로 parity를 검증한다. clip_media 영역의 실제 비율에서 `scale=max(viewW/sourceW,viewH/sourceH)`, `cropW=viewW/scale`, `cropH=viewH/scale`; 중심 bbox를 여백 포함한 뒤 `left/top`을 프레임 안으로 clamp한다. CSS `object-position`은 중심 좌표를 그대로 백분율에 넣지 않고 넘치는 source 폭·높이에 대한 crop offset으로 환산한다. 해상도/rotation 적용 순서와 frame PTS/timebase, 홀수 pixel 반올림을 고정한다. 전신 bbox에 안전 여백을 두고 화면 크기 안에서 crop window가 들어맞을 때만 follow한다. 화면보다 큰 인물·전신 불가 시 `contain` 또는 사용자 선택 fallback을 명시한다. 경로는 smoothing과 속도/가속도 상한을 적용하되 shot cut에서 reset한다. 짧은 누락은 같은 shot/track에서 제한된 보간, 긴 누락·track 교체·타인 교차는 hold 후 center/contain으로 전환하고 사유를 표시한다. 인물 재배정 후 실제 대상 track 가용성을 별도로 검사한다. 기존 preview는 `object-fit`만 적용하며 `object-position`/추적 path가 없고, 기존 renderer의 non-cover fit과 브라우저 `fill`은 완전 parity가 확인되지 않았다. 최초 비교는 cover에 한정한다.

**비교:** 4개의 고정 10초 구간 × 1:1/4:3 × center/follow = 16개 결과(총 160초 출력)를 최초 범위로 제안한다. GT 대상 bbox/전신·얼굴 in-frame, target coverage, pan jitter/속도, shot cut/누락·인물 교체 실패, preview/render 동일 시각 위치와 A/V 경계, 처리 시간·자원을 수작업 검토한다. 이는 미실행 제안이다.

## 6. 원본 타임라인 검토와 export

| 경로 | 장점 | 추가 계약·비용 |
|---|---|---|
| 현행 전량 export 후 overlay | 기존 job/project/개별 MP4·숏폼 호환 | 탈락 사유와 원본 경계가 안 보이고 불필요 clip 생성. 안무 trim 없음. |
| 원본 타임라인 검토 → 선택 export | 장면 경계·main·탈락 사유 확인 후 제외/재배정/경계 수정 가능 | `analysis complete/review_ready/export complete`를 분리하고 원본 보존·draft/project/job·queue·취소/재개·cache/revision·과금/대기시간 계약 필요. |
| 전량 export + 원본 검토/선택 재export | 기존 출력 계약을 유지하며 편집을 점진 도입 | 최초 전체 비용은 유지. 원본/수정 clip 중복과 stale output 처리 필요. |

추천 검토 순서는 현행에 원본 타임라인·탈락 이유를 읽기 전용으로 보여주는 중간안 → 실제 사용/대기시간 측정 → 지연 export 채택 여부 결정이다. 생성 지연은 확정 요구가 아니다. 타임라인 단위는 stable scene/segment ID와 source `[startMs,endMs)` 및 auto person/confidence/reason, 사용자 edit revision을 가진 draft다. draft를 저장해도 export job을 시작하지 않는 상태를 지원하고 project `completed`의 기존 의미를 바꾸지 않는다. source bytes/hash를 output 수명 동안 보존하고 cache key는 source/model/config/analysis/edit/output setting revision으로 분리한다. 취소 시 partial 파일과 재시작 지점, retry idempotency, job 진행률을 정한다. ffmpeg stream copy의 keyframe 경계 오차와 정확한 재인코딩의 시간·품질을 같은 구간에서 비교하고, 경계 정확도 요구가 정해지기 전 한쪽을 기본으로 확정하지 않는다. export 전 preview는 원본 seek/thumbnail이지 완성 MP4가 아님을 UI에 표시한다.

지연 export를 선택할 경우 **AnalysisJob**은 `analyzing → analysis_complete/failed/cancelled`, **ReviewDraft**는 분석 revision을 참조하는 `review_ready`와 단조 증가 edit revision, **ExportJob**은 `queued → exporting → completed/failed/cancelled`로 분리한다. 기존 `ProjectSnapshot.status='completed'`는 export가 끝나 미디어가 준비된 결과에만 사용하며, draft를 완료 project로 가장하지 않는다. 원본은 draft/재개/export가 참조하는 동안 hash와 함께 유지하고, 삭제/보존 기간은 별도 사용자 정책으로 정한다. 분석 cache key는 `sourceHash+modelHashes+configHash+analysisSchemaVersion`, 출력 cache key는 `analysisRevision+editRevision+outputSettingsHash`다. 취소/실패 후 같은 revision의 재개는 완료된 clip만 재사용하고 `.part`를 정리하거나 검증하며, revision이 바뀌면 stale 출력을 재사용하지 않는다. 대기시간은 `time-to-review-ready`, 사용자 검토 시간, `time-to-first-MP4`, 전체 export 시간으로 나눠 실제로 측정한다. 경계 비교는 요청한 source PTS와 첫/마지막 출력 frame PTS의 차이, A/V 동기와 재인코딩 시간을 함께 기록한다.

## 7. 공통 얼굴 모듈 경계와 최신 후보

W14가 초기 공통 Python 관측 모듈 소유, W13은 main·멤버 mapping·crop 소비자라는 **충돌 회피 제안**을 유지한다. 합의 전 공통 Python 파일 동시 수정 금지. 공통 공개 API는 플러그인 이름을 타입/허용 목록에 박지 않고 `detect_all(frame,time,coordinateSpace,modelRef)`, `align/embed(observation)`, `distance/quality`, `failure`를 제공하는 방향이다. 입력 영상 좌표/rotation/timebase, output bbox/landmark/품질/validity·실패 사유, model id+weight hash·embedding dimension/normalization/backend version, optional dependency/venv·cache 호환성·관측 로그를 명시한다. 안무의 main/참조 mapping, 인물의 grouping/display는 각 소비자 정책으로 남긴다. API·패키지 경로·호환/병합 순서에 대한 W14 합의가 선행이다.

관측 계약은 요청/trace ID와 stage, 입력 frame/ROI·검출/유효 embedding 수, 실패 코드(`no_face`, `low_quality`, `align_error`, `model_unavailable` 등), model/config fingerprint, stage elapsed와 device를 구조화해서 기록한다. 좌표/시간 기준을 명시하고 원본 얼굴 이미지·embedding 벡터·참조 파일 경로의 민감한 값을 일반 로그에 남기지 않는다. 초기 소비자 두 개의 이름으로 등록을 제한하지 않고, 서로 다른 embedding model/hash의 distance·centroid/cache 혼용을 거절한다.

2026-09-30 공식 자료 재확인: [YOLO26 모델 문서](https://docs.ultralytics.com/models/yolo26/)는 2026년 1월 출시라고 명시하고 [pose 문서](https://docs.ultralytics.com/tasks/pose/)는 COCO val2017·ONNX CPU/T4 속도 표와 첫 사용 시 weight 자동 다운로드를 명시한다. [tracker 문서](https://docs.ultralytics.com/modes/track)는 ByteTrack/BoT-SORT를 포함하고 8.4.63부터 추가 tracker를 알리므로 현행 lock 8.4.38의 기능으로 확대하면 안 된다. [Ultralytics 라이선스](https://www.ultralytics.com/license)는 AGPL/Enterprise 선택을 안내한다. 이 수치는 우리 안무 정확도·Mac/Windows 제품 처리 시간으로 환산하지 않는다. [ByteTrack 원 제작자](https://github.com/FoundationVision/ByteTrack)와 [BoT-SORT 원 제작자](https://github.com/NirAharon/BoT-SORT)는 MIT 코드·연구 환경의 근거이지 데스크톱 통합·detector weight 권리의 증거가 아니다. [YuNet](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md)은 해당 모델 디렉터리 MIT이며 2026may 파일은 OpenCV 5용 dynamic shape 재export다. [SFace](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)는 해당 디렉터리 Apache-2.0이다. [InsightFace 모델 규정](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md)은 제공 pretrained weights를 비상업 연구용으로 제한한다. 코드 라이선스와 weight 권리는 별개다. 새 후보의 실제 선택 때 weight revision/hash, 상업 조건, Mac arm64/Windows x64·CPU/MPS/CUDA와 패키징을 다시 고정한다. 9/29 후보별 상세는 [공식 후보 기록](29-official-model-candidates.md)을 따른다.

OS·hardware 범위도 공식 문서 수준으로 한정한다. [Ultralytics predict 인자](https://docs.ultralytics.com/modes/predict/)는 CPU/CUDA 등의 device 선택을 설명하고 [CoreML export](https://docs.ultralytics.com/integrations/coreml)는 Apple 전용 배포 경로를 설명하지만, 이 자료가 현재 Python lock+Mac MPS·Windows 앱 패키지에서 YOLO26 pose가 성공한다는 증거는 아니다. 현행 코드는 Mac MPS→CPU, 다른 OS CUDA→CPU 선택을 갖는다. [InsightFace runtime](https://github.com/deepinsight/insightface/blob/master/python-package/docs/runtime.md)은 ONNX Runtime의 실제 provider 목록에 따라 CoreML/CUDA/CPU를 고른다고 설명한다. CoreML은 MPS와 다르고 현행 OpenCV 얼굴 경로에도 적용되지 않는다. [BoT-SORT 원 repo](https://github.com/NirAharon/BoT-SORT)는 Ubuntu 20.04, Python 3.7, Torch 1.11/CUDA 11.3 시험 환경을 적었으므로 Mac/Windows와 현재 Python 3.11 지원 근거로 옮길 수 없다.

## 8. 실행 전 manifest와 사용자 선택

[실험 manifest 초안](30-w13-experiment-manifest.yaml)에 필요한 칸과 제한을 정리했다. **입력 경로/hash·구간·참조 이미지·라벨·모델 hash·OS/device·실행 SHA·반복/시간/자원 상한·출력 위치가 모두 정해지기 전에는 실제 ML을 시작하지 않는다.** 원본·참조의 처리 권한, 역사 weight의 상업 사용/보유/다운로드 승인도 확인한다. 우선 선택할 범위는 (A) 기존 artifact 정적 비교만, (B) metadata adapter 설계/구현까지, (C) 확정 manifest에 따른 최대 6pass 분석 평가, (D) 별도 crop 16개 렌더 비교 중 어디까지인지다. C/D는 입력과 한도가 정해진 뒤 별도 실행한다.
