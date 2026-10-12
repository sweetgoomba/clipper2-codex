# W12 안무 하이라이트 읽기 전용 조사

조사일: 2026-09-29 KST. 조사자: W12 dance 하위 에이전트. 실제 ML/서버 실행, 모델 다운로드, 빌드/테스트, fetch, commit, 제품코드 수정은 하지 않았다. 이 문서는 현행 소스와 로컬 Git 객체를 읽은 조사 결과이며, 정확도·시간·자원 성능 측정 결과가 아니다. “예전보다 정확도가 떨어졌다”는 회귀 가설로 유지한다.

읽은 지침: `.codex/handoff/tasks/dance-highlight.md`, `highlight-overview.md`, `.codex/AGENTS.md`, Desktop Python/Nest/Angular/Electron 각 `CLAUDE.md`, `.codex/features/dance-highlight/README.md`, `.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md`. 루트 `CLAUDE.md`는 현재 없다. 이 상세 조사는 로컬 코드·이력에 집중했고, 공식 라이선스·최신 모델 근거는 [모델 조사](29-official-model-candidates.md), MVP·공통 계약·실행 상한은 [종합 인계](29-pipeline-design-handoff.md)에 분리했다.

## 1. 조사 기준과 핵심 판단

각 repo의 `dev`, `HEAD == origin/dev`(로컬 remote-tracking ref; fetch 없이 확인), `git status --short`는 모두 비어 있었다.

| Repo | 현재 HEAD | HEAD 날짜/author |
|---|---|---|
| `/Users/jina/project/adlight/desktop/clipper_python` | `47782953228861f4bdbdc135265d067c2a826b0e` | 2026-09-21 07:31:38 +09, 곽민준 `<gwak0214@naver.com>` |
| `/Users/jina/project/adlight/desktop/clipper_nestjs` | `824a7a9f71dde8aa44c8692eadacb6ba6e4961b8` | 2026-09-21 13:00:29 +09, 곽민준 |
| `/Users/jina/project/adlight/desktop/clipper_angular` | `797782e8f8e1c8488d024d23e6291e91c2b1e30e` | 2026-09-21 13:02:05 +09, 곽민준 |

핵심은 다음과 같다.

1. 메인 댄서 선정은 YOLO pose 결과에 중앙/면적/관절 거리 점수를 주고 bbox IoU로 이어가는 휴리스틱이다. 얼굴 identity는 이후 선택된 bbox ROI에 YuNet/SFace를 적용하고 track 평균 → cluster → reference 평균 embedding 거리로 매핑한다. 두 정확도는 분리해서 평가해야 한다.
2. 2026-07-01 `fe223e3`가 InsightFace `buffalo_l` → YuNet/SFace, 후보 프레임 품질 선별, cluster/member 배정까지 함께 바꿨다. 회귀 조사에서 가장 직접적인 비교점이다. 8/13은 중복 배정 제한, 9/18은 montage 제거와 결과 UX 개편이다. 메인 score/selector/track는 최근 변경되지 않았다.
3. **단일 clip 이동·숨김과 실행취소가 이미 구현돼 있다.** 복수선택 체크는 숏폼 생성용이며 일괄 이동/숨김 기능은 없다. Drag/drop도 없다. 안무 trim은 현재 지원되지 않는다.
4. 분석에는 `(원본 t, bbox, trackId)`가 있으나 최종 `dance_meta_v1`에 저장되지 않는다. 결과·숏폼 요청·렌더 payload에는 인물 tracking crop 계약이 없다. preview와 renderer는 기본적으로 중앙 cover crop이다.
5. 얼굴 embedding을 못 만든 main 구간은 clip 생성 전에 drop한다. 현재 “미분류” UI는 이 drop 전체를 복구하는 화면이 아니다. 타임라인 검토/지연 export의 핵심 선행 작업은 후보 구간·bbox·판정/제외 이유를 안정된 ID로 저장하는 것이다.

문서 스택 설명도 현행과 다르다: Angular `package.json:25`는 `@angular/core ^22.1.1`, Nest `package.json:19`는 `@nestjs/core ^11.0.1`이다. 각 CLAUDE의 Angular19/Nest10 설명을 현재 버전으로 인용하면 안 된다.

## 2. 현행 end-to-end 구조

아래 약칭은 각각 이 절대경로를 뜻한다: `PY=/Users/jina/project/adlight/desktop/clipper_python`, `NE=/Users/jina/project/adlight/desktop/clipper_nestjs`, `FE=/Users/jina/project/adlight/desktop/clipper_angular`. 모든 파일·라인은 위 HEAD 기준이다.

### 입력, job, source

- FE `src/features/dance-highlight/flow/dance-flow.store.ts:546–625` `startPipeline`: local file 또는 YouTube(1080p 요청)를 구성하고, 포함 멤버별 `memberKey/memberName/selectedImages`, 제외 멤버, `usedCache`를 `dance_setup`으로 제출한다. `:635–649`에서 progress/completed 이벤트를 화면에 반영한다.
- FE `src/core/plugins/plugin-job.ts:58–66`은 Nest `POST /jobs`로 제출한다. DanceController의 “Angular talks directly to Python /jobs” 주석(`NE/src/modules/dance/presentation/dance.controller.ts:34–36`)은 현재 코드와 불일치한다.
- NE `src/modules/jobs/application/jobs.service.ts:380–441` `enqueueJob`은 프로젝트 파라미터 생성→참고 이미지 선택 캐시→durable job 예약→과금 operation→큐 실행이다. `:744–791`에서 source 준비 이후 executor를 실행한다. `:1046–1098` `prepareSourceForJob`은 `SourcesService.prepareJobParams`에 위임한다.
- NE `src/modules/projects/application/projects.service.ts:616–638` `prepareJobParams`는 기본 output root를 `CLIPPER_DATA_DIR/projects/files/<subject>/<projectId>`로 만들고 `project_id`, title, `output_root`를 넣는다. `:448–484` `recordCompletedJob`은 Python 결과와 source path/assets를 project snapshot으로 저장한다.
- 입력 전 artist 감지/멤버 조회/이미지 후보 검색은 Nest dance module이다. `dance.controller.ts:51–95`는 제목 사전매칭, Wikidata 멤버 조회와 cache 적용이다. `infrastructure/services/dance-reference-cache.service.ts:15–32,47–76,80–132`는 subject/artist 단위 **이미지 URL 선택 목록**을 `dance/reference-cache.json`에 저장하며 embedding cache가 아니다.
- PY `plugins/dance_highlight/dance_highlight/app.py:33–50` `load_models`가 모델과 pipeline을 조립하고 `:60–105` `run_job`이 `video_path/output_root/project_id/dance_setup`을 받아 pipeline 완료 meta를 반환한다. 외부 웹 API의 실제 호출이나 과금은 이번 조사에서 실행하지 않았다.

### Python 분석과 선정

소스: [pipeline.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py:65), [segment.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/segment.py:31), [track.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/track.py:24).

1. `DancePipeline.analyze_video_to_records`, `pipeline.py:65–118`: OpenCV decode, 원본 fps/duration 파악, `MainSelector(fps=원본fps)` 생성(`:78`), `analyze_skip`마다 YOLO 수행(`:94–106`). main bbox 하나만 `TrackAssigner.assign`에 전달한다. 전체 인물 MOT, 얼굴 tracker 또는 ByteTrack 사용 경로가 아니다.
2. `PoseEngine.run_pose_on_frame`, `pose_engine.py:20–47`: Ultralytics YOLO bbox와 keypoint XY만 추출한다. keypoint confidence를 선정 점수에 전달하지 않는다.
3. `segment.py:10–36`: main 점수 = `0.45*centrality + 0.35*(bbox area/frame area) + 0.20*(pose_energy/300)`. `pose_energy_score(:23–28)`는 팔/어깨/골반 관절 간 **거리 합**이다. 시간상 움직임/속도/안무 에너지를 계산하지 않는다. 프레임 크기/포즈/가려진 keypoint에 민감한 후보이다.
4. `MainSelector.select`, `segment.py:94–168`: 이전 main bbox와 IoU가 가장 높은 person 추종, 면적 축소/점수 저하/IoU 저하 때 빠른 switch, 후보 streak, hard score jump로 main 선택. group은 상위 2점수 차≤0.10, 전체 person 면적 max/min≤1.9(`:60–74`)와 hysteresis로 분류한다. 명시적인 shot/cut detector는 없다.
5. `TrackAssigner.assign`, `track.py:31–55`: TTL 1초 안의 기존 bbox와 IoU≥0.35면 같은 trackId. 얼굴 identity/외형/motion prediction 없이 선택된 main bbox 위치만 비교한다. 서로 다른 사람이 같은 위치에 교대하면 같은 track으로 이어질 가능성은 측정할 가설이다.
6. `build_raw_main_segments`, `segment.py:188–259`: 선택 trackId 변화로 구간 분리, `(t,bbox,trackId)` 누적. `smooth_main_segments(:300–392)`는 1.2초 미만 segment를 인접 segment에 흡수/bridge하며 bbox도 합친다. 하나의 smoothed segment가 여러 trackId를 포함할 수 있다.
7. `pipeline.py:417–437`: main/group 후처리 뒤 group overlap≥0.6 main을 drop하되 시작<12초·길이≤3.2초는 예외로 유지(`_filter_group_like_main_segments:305–344`).

### 얼굴 embedding, cluster, member identity

소스: [face_cluster.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_cluster.py:30), [pipeline.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py:167).

- `pipeline.py:120–165` `_download_reference_images`: `memberName` 우선으로 디렉터리를 만들고 선택 URL을 `refs/dance/<safe_name>/ref_XX`로 받는다. 다운로드 실패는 조용히 건너뛰고 기존 같은 파일명은 다시 받지 않는다. 동일 output root 재사용 시 URL 변경과 파일 stale 여부를 확인해야 한다.
- `_build_reference_embeddings`, `pipeline.py:167–188`: 유효 reference 얼굴 embedding을 멤버별 평균 후 L2 정규화. `face_cluster.py:66–97`은 이미지/ROI에서 detector score가 가장 높은 얼굴 하나를 선택하므로 여러 얼굴 reference가 올바른 인물을 가리키는지는 검증하지 않는다.
- `FaceClusterService.batch_segment_embeddings`, `face_cluster.py:150–276`: main bbox ROI를 좌우 15%, 위35%, 아래10% 확장(`:115–136`). segment당 균등 12개 bbox 후보(`:138–148,167–189`), 전체 영상 sequential decode/grab, 후보별 YuNet→aligned SFace embedding. 동일 `(segment,trackId)`에서 품질 상위5개, **최소2개**가 있어야 평균 embedding을 생성한다(`:256–268`). 품질 점수는 detection65% + face/ROI 면적25% + ROI blur10%(`:99–113`); 얼굴 자체 blur나 identity 확신은 아니다.
- `pipeline.py:477–486`: 얼굴 track 평균이 없으면 `dropped_main_no_face` 증가 후 **구간 자체 제거**. 뒤의 output clip이 없으며 개별 drop 사유/경계/bbox는 최종 JSON에 없다.
- `face_cluster.py:290–330`: 기본 Agglomerative average-linkage/cosine distance0.42. 선택형 DBSCAN cosine eps0.6/min_samples2, noise→None. embedding 개수1을 별도 처리하는 branch는 없어 singleton 경계 fixture가 필요하다(실행 확인은 하지 않음).
- `pipeline.py:495–539`: 크기<3 cluster의 centroid가 다른 centroid와 거리<0.45면 label post-merge. `:541–558`은 segment의 **track별 표 1개**씩 majority vote이다. track 지속시간·face confidence·sample 수로 가중하지 않는다.
- `_map_cluster_to_member_name`, `pipeline.py:212–297`: cosine distance=1−dot. 전체 거리순 greedy one-to-one primary 배정(≤0.60), 미배정 cluster는 최선 reference로 fallback하되 같은 멤버에 추가할 때 `min(0.45, primary거리+0.08)` 제한. 가장 닮은 reference가 primary로 이미 차지됐으면 다른 멤버가 threshold 안에 있는 경우 그 멤버에 primary로 배정될 수 있어 margin/unknown calibration 후보이다.
- `pipeline.py:560–590`: cluster centroid→실제 멤버 이름, 성공한 memberName을 파일안전 이름으로 변환해 `person_id`; 미매칭 cluster는 `person_N`; vote 없음은 `unknown`. **pose trackId, clusterId, memberKey, 최종 personId는 다른 개념**이다. 최종 personId는 안정된 외부 memberKey가 아니라 이름/현재 cluster 번호에서 파생된다.

### export와 결과 metadata

- `pipeline.py:599–647`: identity 완료 뒤 main/group 구간을 ffmpeg로 실제 파일 생성. main은 원본 시작시각 JPG thumbnail도 추출. 현재는 분석 job 한 번으로 모든 clip 생성까지 완료해야 결과를 받을 수 있다.
- `render.py:69–101` `extract_clip`: 기본 `use_stream_copy=True`, input 이전 `-ss/-to`, `-c copy`. crop/rescale 없음. 사용자 편집 경계와 실제 keyframe/decode 시작·길이가 얼마나 어긋나는지는 ffprobe/프레임 비교로 측정해야 한다. 여기서 frame-exact trim이라고 주장할 근거는 없다.
- `pipeline.py:656–707`: person별 clip 목록, aggregate stats, `json/dance_meta.json`. [dance_meta.py:13–75](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/dance_meta.py:13) `DanceClipItem`은 `seg_id/seg_type/start/end/clip_path/person_id`뿐이다. `Segment.bboxes`, selector score, face 후보/품질, track→cluster 관계, 거리/margin, drop 구간, 모델 hash, 전체 effective config, 단계 timing은 저장하지 않는다. meta config에는 member_match/duplicate threshold도 없다(`:43–57`).
- stats는 fps/duration/raw/smoothed/kept/drop count/person count(`pipeline.py:680–690`); `_timings`는 로그로만 출력한다. 9/18 이후 montage 생성/metadata가 제거됐고 Nest dance renders는 빈 배열이다.

## 3. 모델·설정과 Git 기준선

| 항목 | 현행 설정/근거 |
|---|---|
| YOLO pose | `yolov8s-pose.pt`, confidence0.25, NMS IoU0.7, skip4, CUDA0/MPS/CPU 자동, CUDA/MPS half=True (`config.py:16–37,74–83,136–139`) |
| Face detector | OpenCV YuNet `face_detection_yunet_2023mar.onnx`, score≥0.28, NMS0.30, top_k5000 (`config.py:95–109`; `face_cluster.py:43–50`) |
| Face recognizer | OpenCV SFace `face_recognition_sface_2021dec.onnx`, aligned crop feature+L2 (`face_cluster.py:52–56,87–96`) |
| 고정 face assets | YuNet SHA256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`, 232589 bytes; SFace `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`, 38696353 bytes (`face_models.py:28–49`). override `CLIPPER_DANCE_FACE_MODEL_DIR`, 기본 cwd/plugin_models/dance_highlight (`:52–56`). |
| Cluster/member | agglomerative cosine/average0.42; optional dbscan0.6/min2; primary0.60/duplicate0.45/margin0.08 (`config.py:111–123`) |
| export | stream copy, 인코딩 선택 시 medium/CRF18 + 플랫폼 HW encoder (`config.py:125–134`; `render.py:29–101`) |
| package/lock | Python3.11, plugin0.1.0; 선언은 ultralytics≥8/OpenCV≥4.10/sklearn≥1.3 (`pyproject.toml:1–14`). 현재 lock: NumPy2.4.4(`uv.lock:909`), OpenCV4.13.0.92(:1131), sklearn1.8.0(:1580), torch2.11.0(:1779), ultralytics8.4.38(:1899). 설치/packaged 실제 버전은 실행 확인하지 않았다. |

face OpenCV create에는 CUDA backend/target override가 없다. Manifest accelerator 목록(CUDA/MPS/CPU)은 YOLO/전체 plugin 가능성을 의미하며 face가 이 장치에서 가속됨을 보증하지 않는다. Manifest RAM4096/VRAM2048 MB는 estimate(`manifest.json:49–59`), 측정값이 아니다.

### 의미 있는 변경

| Repo/SHA | 날짜 + author | 확인한 diff와 비교 의미 |
|---|---|---|
| PY `61c1b1c0` | 2026-04-17 14:34:08 +09, metabuzz-jinahan `<jinahan@metabuzz.co.kr>` | 안무 로직 이식. git log/blame상 `segment.py/track.py`, skip4·기본 smoothing/IoU/TTL이 여기서 온다. 최근 main 선정 회귀로 단정할 수 없다. |
| PY `fe223e3b9339a14994bcef1e55d0f4665396e352` | 2026-07-01 17:13:11 +09, metabuzz-jinahan | buffalo_l/InsightFace CPU→YuNet/SFace; 후보5→12 중 품질상위5; member mapping independent nearest→greedy primary+duplicate fallback; model download hash 고정. score/track/pose 파일 diff 없음. cluster0.42/member0.60 값은 그대로였다. 모델만 바뀐 실험이 아니므로 하나씩 ablation 필요. |
| PY `86fc71a02dd278c0fb5fd9dbcb59b75b67cad00c` | 2026-08-13 13:50:53 +09, 곽민준 | single-reference cluster 흡수 제한: duplicate ceiling0.45, primary+0.08. 오배정 precision과 같은 인물 split-cluster recall을 같이 비교해야 한다. |
| PY `65bbd33de0f0af0e1a64cdfe25cb0347bf559b4a` | 2026-08-13 13:52:14 +09, 곽민준 | 위 threshold를 DanceConfig에 노출. 기본 수치 변경 아님. |
| PY `98d2b7cef81609fcd907ccd14ce4060de660dd17` | 2026-08-25 14:50:29 +09, 곽민준 | Windows Unicode 모델 경로: path→model bytes로 로드. 인식 알고리즘/모델 변경 아님. |
| PY `49e7827922087a2bd66f5b182a5d90e8d15d7e73` | 2026-09-18 20:20:27 +09, 곽민준 | 인물 montage, normalize/concat/duration-selection 단계 제거. persons/clip 생성 유지. 더 짧아진/다른 출력 체감과 detector 정확도를 구분해야 한다. |
| PY `bdbe125` | 2026-09-18 20:25:05 +09, 곽민준 | montage 제거 뒤 남은 ffprobe 준비 제거. |
| NE `79969a19d445530c7b627a2f213b59278b99326e` | 2026-09-18 20:30:57 +09, 곽민준 | dance detail을 person 중심+overlay로 조립; montage 표시 제거. |
| NE `324877c615d7ee0d4829de768f9deca830e82dd2` | 2026-09-18 20:43:51 +09, 곽민준 | clip 숨김·이동 API+영속 overlay. |
| NE `887297e6d8f5d8bd4bdb77857b4fd4d60ef07fde` | 2026-09-18 21:25:26 +09, 곽민준 | highlight→shortform manifest/render job 추가, template fit opt-in. |
| FE `111444e7`, `5bba3492`, `2a4b75d0` | 2026-09-18 20:56:33 /20:59:53 /22:13:34 +09, 곽민준 | clip 이동/숨김 서버 저장, 직전 배정으로 undo, 멤버/미확인/미분류 3구획. |
| FE `6c70b2ea` | 2026-09-19 23:45:45 +09, 곽민준 | 결과 화면 열 카드 개편. ML 변경 아님. |

직접 비교 기준점:

- 모델 교체 전 `fe223e3^ = e34cdbcc62518a8079a988dd8add015b569dd7e1` (2026-06-26 09:52:59 +09, metabuzz-jinahan). `fe223e3` 직후와 두 모델/샘플링/mapping 요인을 분해한다. 이 parent와 현행 lock의 위 5개 core package 버전은 동일했다.
- 중복배정 제한 전 `86fc71a^ = 2c1ea93de10dc5ef60e3beea5af85864520b58e4` (2026-08-13 13:49:19 +09, 곽민준) ↔ `86fc71a`.
- montage 제거 전 `49e7827^ = 31f8917727d142c9368b49ed8531f9e60dd0c1cb` (2026-09-18 19:46:47 +09, 곽민준) ↔ 현행: 인식결과 동일성과 출력/총소요시간 비교.
- 옛 reference embedding을 새 recognizer에 재사용하면 안 된다. 엔진/모델별 embedding 공간이 다르므로 baseline별 동일 reference 이미지 bytes에서 다시 추출해야 한다. 과거 buffalo_l 비교는 적법한 기존 모델/입력 확보와 실행 허용 범위를 먼저 확인한다(이번엔 실행 안 함).

7/1 설계 기록 `...FACE_MODEL...md:131–144`는 임계값 재조정·고정 input 평가를 명시하고 `:160–161`에서 작은 얼굴/blur/profile 위험을 예고했다. 이번 소스/tests/Git만으로 실제 대표영상 threshold calibration 완료를 입증할 수 없다. 이 문서의 계획을 “실영상 정확도 검증 완료”로 전환하면 안 된다.

## 4. 정확도 가설과 동일 조건 측정 계획

### 우선 가설 (확인된 코드와 미측정 영향 분리)

| 가설 | 코드 사실 | 분리할 검증 |
|---|---|---|
| H1 얼굴 engine 교체/threshold 미보정 | 7/1 SFace로 교체되었으나 cluster0.42/member0.60 유지 | GT main bbox ROI를 고정해 face detection coverage, same/different 거리 분포, member confusion/unknown/false accept 비교. sampling/mapping 별도 ablation. |
| H2 main 휴리스틱은 센터·크기·정적 관절 거리에 치우침 | `segment.py:31–36`; keypoint conf 미사용 | 화면 옆 주인공, 작은 주인공, 여러 댄서 동등 크기, 카메라 zoom, profile/occlusion 시 main selection 정확도. identity evaluator에 oracle bbox를 넣어 전파 오차 분리. |
| H3 skip와 selector hold 시간 불일치 | `pipeline.py:78,94–100`; `segment.py:49–58,79,87,152`의 threshold는 원본fps이고 streak는 샘플 처리 1회마다 증가 | 30fps/skip4에서 BASE7회≈0.933초, FAST3회≈0.4초, group enter10회≈1.333초, exit7회≈0.933초의 cadence(첫/마지막 sample 위치 때문에 실제 지연은 경계에 따라 다름). intended .25/.10/.35/.25초와 비교. 이 구조는 4/17부터라 최근 회귀 증거는 아님. FPS/skip를 바꾸는 미래 최적화가 selection을 바꿀 수 있다. |
| H4 IoU track switch/segment smoothing이 인물을 혼합 | selected bbox만 IoU tracker; 짧은 segment bbox를 다른 label segment에 합침 | annotation track fragmentation/ID-switch, segment 안 실제 인물 혼합 비율, 시간가중 vote vs 현재 track vote, smoothing 전후 오류. |
| H5 ROI 최고 detector confidence 얼굴이 다른 사람 | 확장 bbox 안 얼굴 중 top confidence 1개; 얼굴 위치-머리 pose 연계 없음 | 두 얼굴 포함 ROI에서 선택 얼굴이 main 몸체에 속하는지, ref 이미지도 같은 검토. 후보 수/face area/blur를 저장해 failure grouping. |
| H6 no-face drop이 recall과 UX를 가림 | 최소2 embed/track, 이후 no-face scene 제거 | detected sample수/유효 track수/auto-drop count뿐 아니라 drop 시간과 GT identity 복구가능성을 평가. |
| H7 small-cluster postmerge/greedy naming/duplicate 제한 | 작은 cluster 거리<0.45 merge, greedy primary, duplicate ceiling | pairwise/B-cubed cluster precision/recall, member assignment precision/recall, split person recall, 다른 멤버 없는 참조 상황, 0/1 embedding 경계. |
| H8 export/결과 개편을 ML 회귀로 느낄 수 있음 | stream-copy 구간, 9/18 montage 제거, UI grouping overlay | 분석 구간 JSON 자체와 실제 생성 clip frame/time, 원본 자동판정 vs 수동overlay vs 숏폼 출력 비교. |

측정 입력 계약: 동일 원본 로컬 영상 bytes/hash, decode 해상도/FPS/rotation, 동일 reference image bytes/hash·포함/제외 멤버, code SHA, config 전체, 모델 hash, Python/package lock 및 실제 설치 버전, OS/device/precision, FFmpeg/OpenCV 버전, cold/warm/cache 상태를 함께 고정한다. 라이브 URL 재검색/재다운로드는 같은 입력 조건이 아니다. 실패 다운로드를 조용히 skip하는 현행을 고려해 reference 성공 수를 기록한다.

추천 지표:

- main: sampled-frame 정확도(정답 main/group/none), bbox IoU/subject coverage, switch delay, ID switch/fragmentation, 구간 boundary 오차/segment F1. 그룹 장면 정답을 별도 둔다.
- face isolated: **GT 몸체 bbox**에서 검출 recall, main 얼굴 선택 precision, ≥2 유효 face/track coverage, same/different pair 분포, threshold별 FAR/FRR 또는 precision/recall.
- clustering: person pair precision/recall, B-cubed 또는 purity+completeness, 한 인물 split 수/다른 인물 merge 수.
- member: 올바른 reference label 비율, false assignment/unknown rate, 멤버별 confusion. 참조 없는 영상 인물을 특정 멤버에 붙이는 false accept를 반드시 포함한다.
- end-to-end: GT 장면이 최종 올바른 인물 clip에 남은 시간 비율, wrong-person 포함 시간, missed/drop 시간, 경계/clip actual duration 오차.
- 시간/자원: decode/pose/ref-face/video-face/cluster/export 각 wall time, 처리 frame/face-call 수, CPU/RAM RSS/GPU VRAM peak, cold 모델 시작과 warm 분석을 분리. 선언된 RAM/VRAM estimate를 측정치로 사용하지 않는다.

샘플 strata: 1인·2인·다인, 중앙/측면 이동, 조명/각도/모션 blur, 작은 얼굴, 댄서 교대, hard cut, zoom, occlusion, 포함 reference가 1명뿐인 영상, 해당 인물 reference 누락/잘못된 이미지, 영상 마지막/짧은 구간. 동일 annotation과 hold-out으로 threshold tuning/평가를 나눈다. 지금 fixture 영상이나 정답 annotation을 새로 만들거나 실행하지 않았다.

기존 테스트는 fake detector/recognizer로 normalization/12→top5/bytes loader와 synthetic vector mapping 등을 확인한다(`PY/tests/test_dance_face_cluster_opencv.py:110–174,232–254`, `test_dance_cluster_member_mapping.py:15–108`). `test_dance_pipeline_helpers.py:1–4`도 E2E는 integration fixture 영역이라고 명시한다. 이 테스트 존재는 실제 춤영상 정확도 증거가 아니다. 이번엔 테스트 실행 안 함.

## 5. 현재 결과 편집 UX와 저장 계약

### 이미 있는 기능

- FE [dance-result-detail.component.ts](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/dance-result-detail/dance-result-detail.component.ts:51): 멤버/미확인 인물/미분류 구획(`:75–104`), 인물별 clip 선택, 모달로 **clip 1개** 목적 인물 선택(`:233–279`), 숨김 확인(`:285–295`), 미매칭 인물 행 전체를 확정 멤버로 병합(`:185–226`).
- 체크 전체/부분선택(`:107–155`, HTML `:87–108`)은 preview와 `onGenerate(:157–164)`의 숏폼 clipIds에 쓰인다. 여러 clip을 체크한 뒤 일괄 이동하는 event/API가 아니다. 모달 방식은 현재 동작을 그대로 확장하는 가장 작은 후보이다.
- FE `projects-detail-page.component.ts:310–376`: API 저장→detail 재조회→6초 snack undo. 연속 A→B→C 이동의 undo는 최초 A가 아니라 직전 B로 다시 배정한다(`:333–361`). 영구 히스토리/숨긴 clip 관리 목록은 확인하지 못했고, 현재 노출은 직후 snack undo이다.
- NE `projects.controller.ts:111–177`: `PATCH /projects/:id/dance/member-assignments`, clip별 `PUT/DELETE .../dance/hidden-clips/:clipId`, `PUT/DELETE .../dance/clip-assignments/:clipId`.
- NE `projects.service.ts:117–197,205–347`: `project.result.dance_member_assignments`, `dance_hidden_clips`, `dance_clip_assignments` overlay만 저장한다. 원본 Python `dance_meta.json`/mp4는 재작성하지 않는다. 저장 위치는 `JsonProjectRepository`, `.../infrastructure/json-project-repository.ts:19–22,40–44,67–73`의 `CLIPPER_DATA_DIR/projects/projects.json`.
- NE [dance-project-detail-builder.ts](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/projects/application/dance-project-detail-builder.ts:101): 숨김→clip 제외, **clip 이동 > 인물 병합 > 원본 person_id** 적용(`:108–140`), 최종 clips에서 person.clipIds 재계산(`:202–205` 이후). `clipId`는 `main_0000`처럼 clip 파일 basename(`:65–74`). 재분석 때 segment 순서가 바뀌면 같은 index ID를 이전 판정과 연결하면 안 된다.
- ZIP은 수정된 detail을 소비한다(`project-zip-entries.ts:16–32`, `projects.service.ts:670–685`): 숨김은 다운로드에서 제외, 이동은 목적 인물 폴더/ZIP에 반영. 새로운 숏폼도 수정된 detail을 소비하고 선택 personId 불일치·숨김 clip을 거절(`highlight-shortform-render.service.ts:150–170`). 기존 숏폼 output은 생성 시점의 별도 manifest snapshot이므로 원본 결과를 옮기거나 숨긴다고 자동 갱신되는 흐름은 없다.

### 아직 없는 범위

- 안무 trim: `ClipTrimService.runTrim`, `NE/.../clip-trim.service.ts:130–134`가 `dialog_highlight` 외 유형을 거절한다. FE `projects-detail-page.component.html:86–109`는 대사에만 trim 이벤트를 연결하며, dance는 native clip modal 재생만 한다(`:132–134`; `projects-clip-overlay.component.html:40–48`). 대사의 3초 최소 trim 계약을 안무의 1.2초 분석 구간에 그대로 복사하면 충돌한다.
- 원본 영상 전체의 검토 타임라인: dance 결과는 인물별 clip list+숏폼 합성 playback scrub이다. 원본의 분석 경계/main dancer/bbox를 수정하는 timeline은 없다. 현재 `ProjectClipItem.sourceStartSec/sourceEndSec`는 시간 표시에 쓸 수 있지만 bbox와 자동 제외 후보는 없다.
- 복수 이동/숨김: 현재 단일 API만 여러 번 호출하면 last snapshot/concurrency/partial success가 발생할 수 있으므로 실제 일괄 기능을 선택한다면 한 번의 저장으로 여러 clipIds를 적용하는 국소 계약을 검토한다. 목적 인물 모달 + 선택 후 toolbar가 기존 UX와 가장 가까운 후보. Drag/drop은 discoverability/키보드 접근성과 scrolling, 여러 선택의 이동 semantics를 별도 검토할 선택지이다.
- 동일 projectId로 새 완료 결과를 쓰면 `recordCompletedJob(:459–475)`가 기존.result overlay를 merge하지 않고 job.result에서 새 결과를 만든다(`completedProjectResultFor:585–594`). 이 경로에 재처리를 붙일 경우 수동 수정 유지/무효화 정책을 명시해야 한다. 현재 일반 새 job은 새 project ID지만 same-project rerun 안전성을 보증하면 안 된다.

## 6. 인물 tracking crop 후보와 preview/render 계약

### 현행 crop 경로

1. Python dance export는 원본 비율 clip이며 bbox가 JSON에서 사라진다.
2. FE [highlight-shortform-preview HTML:18–20](/Users/jina/project/adlight/desktop/clipper_angular/src/features/highlight-shortform/components/highlight-shortform-preview/highlight-shortform-preview.component.html:18)는 `video`의 `object-fit`만 바인딩하고 `object-position/track/crop`이 없다. TS `:297–301`은 template clip_media region/fit을 쓴다. 기본 브라우저 object-position은 중앙이다. preview는 selected clip들을 이어서 읽는다(`models/highlight-shortform.ts:104–123`, component.ts `:129–153`).
3. NE `highlight-shortform-manifest.builder.ts:25–33,124–142`의 resolved clip은 path/sourceStartMs/durationMs, slot은 sourceStartMs/duration/fit뿐이다. `editState.honorTemplateClipFit=true(:199–200)` → `render-recipe-provider.ts:135–162` → `clipper-render-payload-mapper.ts:855–866`에서 `source_start_sec`와 fit을 전달한다. crop trajectory를 전달하지 않는다.
4. `RenderTimelineItem.crop`라는 **static rectangle 타입**은 `domain/render-recipe.model.ts:27–31,49`에 있지만 dance→shortform slot mapper나 payload mapper가 populate/serialize하지 않으므로 기존 타입 하나로 tracking crop이 구현된 상태가 아니다. mediaSlots 타입도 crop 없음(`project-manifest.model.ts:225–239`).
5. PY `local_render_adapter.py:195–259`가 payload clip의 fit/source_start만 받고, `:437–460`이 filter graph를 만든다. [filter_graph.py:70–75](/Users/jina/project/adlight/desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/filter_graph.py:70)는 increase scale 후 중앙 crop이다. 자동 motion은 이미지에만 적용(`motion_effect.py:24–27`); 기존 explicit pan은 일정 방향/속도 경로로 댄서 bbox를 읽지 않는다.

현재 fit parity의 제한: preview는 cover/contain/fill 모두 CSS로 해석하지만 `clipper-render-payload-mapper.ts:407–420`은 cover만 전달하고 다른 값은 경고 후 생략한다. worker `local_render_adapter.py:447–455`의 non-cover 기본은 blur background+contain이다. 따라서 fill의 browser/render 결과를 같다고 주장하면 안 된다. crop 기능 도입 시 cover와 원하는 ratio fixture에서 먼저 검증하고 fit별 계약을 함께 명시한다.

### 구현 후보

| 후보 | 범위/효과 | 한계/비용 |
|---|---|---|
| A clip당 bbox 중앙값으로 static focus | 현행 segment.bboxes를 저장해 단일 중심. renderer/preview static offset 추가 | 가볍고 안정적이나 옆으로 이동하는 인물을 끝까지 따라가지 못함. baseline으로 유용. |
| B 선택된 main bbox keyframe를 smoothing해 dynamic crop | 기존 bbox/t/trackId를 활용, normalized trajectory 저장, preview와 ffmpeg가 같은 trajectory 소비 | 최소 모델 변경으로 움직임 요구를 직접 다룸. track switch/실종/혼합 segment의 오선정을 같이 따라갈 위험. |
| C 전체 인물 tracking + scene identity에 맞는 subject path | all detections/keypoint-confidence·track association/face identity를 보존하고 선택 subject path 분리 | main 교체/수동 actor 선택까지 가능하나 현행 selected bbox 하나 tracker를 바꾸는 큰 단계. 동일조건 main/identity eval 후 별도 범위로 선택. |

추천 순서는 A를 정량 baseline으로 두고 B를 한정 구현/비교, C는 B 실패 사례와 인물 플러그인 계약이 확인된 후 결정하는 것이다. 모델 교체와 crop/UX 전면 구현을 같은 실험으로 묶지 않는다.

### 필요한 최소 계약 (제안이며 현행 아님)

- immutable 분석 artifact: schemaVersion, analysisId/revision, source fingerprint/dimensions/FPS/rotation, engine/model/config fingerprint, segment stable ID, sourceStart/end, selectedMainTrackId, `(sourceTime,bbox normalized,trackId,quality/status)` keyframes, auto identity 후보/cluster/reference 거리·drop reason. 큰 embedding arrays를 UI meta에 통째로 넣기보다 내부 artifact를 분리한다.
- 사용자 edit overlay: analysisRevision + segmentId를 기준으로 edited sourceStart/end, excluded, assignedPersonId, 선택한 cropMode/subject override. **identity label만 옮기는 것**과 **다른 화면 인물을 crop subject로 선택하는 것**을 분리한다. 현재 clip 이동은 label 수정이고 몸체 bbox를 다시 고르지 않는다.
- resolved shortform clip/slot/recipe/payload에 같은 cropTrack 또는 versioned trajectory artifact reference를 전달. 순서는 metadata→Nest detail→FE preview model→manifest→두 recipe mapper→payload→Python filter graph이다. `render-recipe-provider.ts:129–134`와 `infrastructure/clipper-render-recipe-provider.ts:103–107`은 mediaSlots mapping이 중복이므로 하나만 변경하면 다른 워크플로에서 누락될 수 있다.
- 시간축은 원본 sourceTime, clip-local time, concatenated timeline time을 명시한다. 원본 t를 무조건 file.currentTime에 적용하면 export/trim/seek 후 어긋난다. edited source start와 sourceStartMs를 기준으로 clip-local keyframe로 해석하고 `mediaKey`에도 trajectory revision을 넣어 preview가 예전 crop을 유지하지 않게 한다.
- canonical 중심 경로에서 interpolating/clamp/ease/누락 처리 규칙을 저장하거나 공통 계약으로 고정한다. shot cut/실제 subject change에서는 reset; 짧은 누락은 마지막 유효 중심 hold/짧은 보간, 긴 누락은 center/contain 중 선택한 fallback; abrupt jump는 max velocity/deadband/smoothing으로 비교. 불확실한 identity를 임의로 다른 사람 path에 붙이지 않는다.
- 템플릿 ratio는 전체 9:16 canvas가 아니라 **clip_media region**의 실제 W/H를 기준으로 계산한다. cover에서 scale=`max(viewW/sourceW,viewH/sourceH)`, source crop 크기=`viewW/scale,viewH/scale`; left=`clamp(subjectX*sourceW-cropW/2,0,sourceW-cropW)` 등. CSS object-position은 subjectX%를 그대로 쓰는 값과 다르며, 넘치는 폭이 있으면 `left/(sourceW-cropW)*100%`로 맞춘다. renderer도 같은 left/top/cropW/cropH를 써야 한다. frame ratio/rotation/odd-pixel 반올림 정책을 동일하게 둔다.
- browser crop은 frame-synchronized update(예: video frame callback/canvas)로 부드럽게 보여주고 preview/render는 동일 interpolation·좌표식을 쓴다. 현재 timeupdate만으로 trajectory animation 성능을 입증할 수 없다. 최소 parity fixture: 왼쪽→오른쪽 이동, bounding clamp, template1:1/9:16/16:9 영역, shot switch, tracking gap, edited start/end, clip concatenate 경계. 같은 timestamp rendered frame과 preview visible crop/subject coverage를 비교한다.
- 원본 clip은 그대로 보관하고 crop을 숏폼 render 시 적용하면 template ratio별 재렌더가 가능하다. 개별 다운로드도 crop된 clip을 원하는지 원본 비율을 원하는지는 별도 output 선택이다. 한번 crop해서 원본을 대체하면 template 변경/수정 복구 비용이 커진다.

## 7. 원본 타임라인 검토 뒤 export 분리 가능성

기술적으로 분리 지점은 명확하다: `DancePipeline.run`에서 `person_ids`가 계산된 `pipeline.py:578–598` 이후, `:601` ffmpeg clip 생성 전에 분석 artifact를 확정할 수 있다. 현재 `run()` 한 함수와 `run_job` 한 동작에 묶여 있으므로 단순 UI 버튼 추가만으로 분리되는 구조는 아니다.

가능한 흐름(아직 확정 요구 아님):

1. source 준비→pose/face/identity 분석 → 자동 후보·제외 이유·bbox artifact 저장.
2. 분석 완료 결과에서 원본 source video를 재생하고 source timeline에 구간/main dancer/자동 identity/불확실성/auto excluded 구간 표시. start/end/exclude/assignment/crop focus를 overlay로 저장.
3. 사용자가 검토한 revision으로 export job을 실행하여 포함된 구간만 ffmpeg 생성. export 결과는 분석revision/editrevision/outputrevision을 참조한다.
4. 단순 이름 재배정은 이미 있는 metadata overlay로 즉시 반영. 경계 변경은 해당 clip export만 다시 생성. template/crop/제목/BGM 변경은 숏폼 render revision만 만든다.

장점: 잘못 잘라낸 clip 재생성·불필요 export를 줄이고 drop 후보도 사용자가 복구할 수 있다. 단점: 원본 파일이 계속 접근 가능해야 함, analysis metadata/preview source ticket, draft persistence/restart resume, revision conflict, export pending/error/retry 상태와 input integrity 계약이 필요하다. 기본 stream-copy export는 빠를 수 있으므로 첫 분석 대기시간이 얼마나 줄어드는지는 stage timing으로 측정해야 한다. ML 시간이 지배하면 총 대기 절감은 작을 수 있다.

현재 project status는 `completed`만(`NE/src/modules/projects/domain/project.model.ts:3`), clip videoPath 없이 preview/render/export가 되는 계약은 없다. 전역 job 상태에 임의 review 상태를 섞기보다 완료된 analysis job의 artifact+project 편집 단계와 별도 export job을 국소적으로 설계할 후보이다. 가격 operation은 기존 `dance_highlight.extract` 예약 흐름과 충돌하지 않도록 분석/export 중 어디를 charge/retry하는지 확인해야 한다. 이번 조사에서 과금 변경을 제안된 확정 행동으로 두지 않는다.

export 범위의 결정점: (a) 현행 즉시 export를 유지하면서 타임라인 수정 후 선택 clip 재export, (b) 분석 완료 후 사용자 검토 export, (c) preview용 저비용 proxy/thumbnail만 먼저 만들기. 사용 편의·첫 결과 대기·재편집 비용을 실제 입력으로 비교한 뒤 한 가지를 선택한다. 사용자가 요청한 “검토 후 export”의 장단점을 조사하는 단계이며 모든 기존 결과를 자동으로 지연 생성으로 전환하라고 확정하지 않는다.

## 8. 공통화와 W13 인계

재사용 후보는 `face_models.py`의 model asset 검증/Unicode bytes loader, 얼굴 detection/alignment/embedding/quality, normalization/clustering의 순수 부분이다. `FaceClusterService.batch_segment_embeddings`는 dance Segment/main bbox/최소2샘플에 종속돼 있어 그대로 “일반 인물 plugin” 공통 서비스라고 단정할 수 없다. `MainSelector`/group smoothing/member reference mapping은 안무 정책으로 유지한다.

인물 W14와 먼저 맞출 계약은 optional reference matching, face/body track ID와 person identity 분리, face observation 좌표/시간축, embedding engine ID/dimension/hash, cluster evidence/대표 이미지, background person 취급, stable segment/person IDs, 수정 overlay/revision이다. 향후 다른 플러그인도 사용할 독립 공통 모듈/공개 API 계약을 정한 후 필요한 기본 기능을 추출한다. 안무와 인물은 초기 소비자이며 소비자 이름을 두 플러그인으로 제한하지 않는다. 전체 dance pipeline의 정책은 안무에 남긴다.

W13 권장 실행 순서: 현재 HEAD와 위 역사 기준선 고정 → 같은 영상/참고이미지 annotation/지표 확정 → main vs face isolated 평가 → 한 원인씩 최소 변경/ablation → bbox/불확실성 metadata 보존 → 기존 단일 이동 UX의 복수선택 확장 여부 결정 → crop trajectory/preview-render parity → timeline/export 방식을 선택. 실제 실행 허용 범위·input assets·HW·old model 확보는 사용자의 새 지시와 기존 HOLD를 대조해야 한다.

읽기 전용 확인만 완료했고, 실제 모델 성능·runtime 성공·테스트 통과·render parity 개선을 주장하지 않는다. 제품코드/다른 문서는 수정하지 않았다.

## 9/29 후속 조사

[7/1 얼굴 교체의 작성자·원본 설계·변경 전후](29-face-change-detail.md) · [사용자 결정과 픽셀 좌표/crop 설명](29-user-feedback-clarifications.md). 인물은 배경 포함 전부 표시하며 자동 필터는 후속으로 미룬다. 공통 얼굴 도구의 이용 대상은 향후 여러 플러그인이다.
