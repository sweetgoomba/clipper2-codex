# W12 후속 조사 — 2026-07-01 안무 얼굴 모델 교체

조사일: 2026-09-29. 이번 작업은 로컬 Git 객체와 문서만 읽었다. 제품 코드는 수정하지 않았고 ML, API, 다운로드, fetch, build, test를 실행하지 않았다. 역사 코드의 읽기용 사본을 이 기록의 evidence 폴더에 보존했다. `.py.txt` 등은 당시 Git 객체 내용의 증거 사본이며 제품 코드나 새 구현이 아니다. 아래 검증 결과는 **당시 문서에 남은 기록**이며 이번에 다시 실행한 결과가 아니다.

7월 1일 변경의 Git author와 committer는 모두 **`metabuzz-jinahan <jinahan@metabuzz.co.kr>`**다. 이 이름을 다른 사람의 실명·별칭으로 해석할 근거는 이번 조사에서 확인하지 않았다. 8월 13일의 작성자 `곽민준 <gwak0214@naver.com>`과는 다른 Git 기록이다.

변경의 주된 이유는 일반 Windows PC에서 InsightFace 소스 빌드 때문에 앱 창이 열리지 않는 문제와, InsightFace 제공 사전학습 모델의 상업 이용·배포 조건이었다. 동시에 얼굴 표본 선택과 참조 멤버 배정도 바꿨다. **실제 Mac 영상 1건의 실행 성공 기록은 있다. 다만 같은 입력으로 이전 모델과 정확도를 비교하거나 threshold를 보정한 완료 기록은 확인되지 않았다.** 따라서 “검증을 전혀 하지 않았다”와 “정확도가 검증됐다”는 모두 기록보다 강한 표현이다.

## 1. 정확한 커밋과 비교 기준

| 항목 | 로컬 Git 기록 |
|---|---|
| 변경 SHA | `fe223e3b9339a14994bcef1e55d0f4665396e352` |
| 제목 | `feat: make dance face matching Windows-safe` |
| author | `metabuzz-jinahan <jinahan@metabuzz.co.kr>` |
| AuthorDate | `2026-07-01 17:13:11 +0900` |
| committer | `metabuzz-jinahan <jinahan@metabuzz.co.kr>` |
| CommitDate | `2026-07-01 17:13:11 +0900` |
| 직접 parent | `e34cdbcc62518a8079a988dd8add015b569dd7e1` |
| 변경량 | 13개 파일, 591줄 추가·294줄 삭제 |

근거: [Git 원문 사본](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/git-metadata.txt:1), [parent 대비 전체 diff](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/july-01.diff:1). 7월 1일 커밋 메시지에는 coauthor trailer가 없다. 이 사실로 도구 사용 여부나 실제 작업 참여자를 추정하지 않는다.

역사 코드 링크의 `before/`는 위 parent, `after/`는 위 변경 SHA에서 `git show SHA:path`로 읽은 파일 그대로다. 현행 파일의 줄 번호를 과거 코드에 붙이지 않기 위해 사본을 만들었다. 이 사본은 실행하지 않았다.

## 2. 왜 바꿨나 — 당시 기록과 설계 의도

Windows 설치 앱 `clipperstudio Setup 0.0.3.exe`가 약 25초 동안 창 없이 살아 있다가 종료됐고, 첫 실행의 `uv sync`가 `insightface==0.7.3` 소스 빌드에서 Microsoft Visual C++ Build Tools를 요구해 실패했다고 설계 문서에 기록돼 있다. 앱의 `openMainWindow()`가 전체 플러그인 의존성 설치 완료를 기다리는 구조였기 때문에 선택 플러그인 하나의 실패가 앱 기동을 막았다. [장애 기록과 호출 흐름](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:10)

이에 따라 해결을 두 갈래로 나눴다. Electron은 작은 기본 Python 환경과 플러그인별 환경으로 분리하고, 안무 플러그인은 Windows 사용자가 MSVC Build Tools를 설치하지 않아도 되는 얼굴 backend로 교체한다. 환경 분리 자체는 Electron의 별도 변경이며, Python `fe223e3` 하나가 그 전체 작업을 구현한 것은 아니다. [목표](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:32), [환경 분리 후 별도 얼굴 교체 계획](/Users/jina/project/adlight/.codex/records/worklog/2026/07/plugin-runtime-isolation-implementation-plan-2026-07-01.md:245)

라이선스에 관해서는 **당시 문서가** “InsightFace 코드는 MIT지만 제공 사전학습 모델·`buffalo_l` 모델 zoo는 별도 상업 라이선스 없는 공개 조건에서 비상업 연구용”이라고 판단했다. 대체 후보 YuNet·SFace는 당시 확인한 모델 저장소 기준 각각 MIT·Apache-2.0로 기록했다. 이번 조사는 현재 법적 이용조건을 다시 판정한 작업이 아니다. [당시 판단](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:115), [모델 출처·hash·라이선스 기록](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:21)

품질에 대해서는 기존 군집 로직을 유지하더라도 **샘플 영상으로 embedding 정규화·threshold를 다시 조정**해야 한다고 설계했다. 대표 안무 영상과 참조 이미지를 고정해 검출률, 군집, 최종 결과를 측정하고 Mac에서 조정한 뒤 Windows에서도 같은 표본을 비교하는 의도였다. 작은 얼굴·움직임 흐림·옆얼굴·문턱 근처 embedding에서 기존 모델과 품질이 달라질 위험도 명시했다. [재조정 의도](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:131), [측정·플랫폼 검증 계획](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:136), [품질 위험](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:158)

## 3. 실제 old/new 코드 — 얼굴 backend

| 기능 | parent: InsightFace | 7월 1일: OpenCV |
|---|---|---|
| 초기화 | `FaceAnalysis(name='buffalo_l', allowed_modules=['detection','recognition'])`, `prepare(ctx_id, det_size)` | `ensure_face_models()` 후 `FaceDetectorYN.create`와 `FaceRecognizerSF.create` |
| 실행 장치 | `detect_face_ctx_id()` 실제 반환은 모든 OS에서 `-1`, CPU 고정 | 위 OpenCV 생성자에 GPU/backend/target 인자를 따로 지정하지 않음 |
| 얼굴 선택 | ROI에서 검출 confidence가 가장 높은 얼굴 1개 | 동일하게 confidence가 가장 높은 얼굴 1개 |
| embedding | `faces[0].embedding` → L2 정규화 | `alignCrop(img, face)` → `feature(aligned)` → flatten → L2 정규화 |
| 검출 문턱 | `.28` | `.28` 유지; detector 생성 인자에도 전달 |
| 영상 ROI 입력 | 기존 backend 내부 처리 | ROI마다 `setInputSize((실제 ROI 폭, 높이))`; `(320,320)`은 생성 시 설정 |
| 실패 처리 | 얼굴 없음·confidence 미달이면 `None` | 빈 이미지·얼굴 없음·confidence 미달·OpenCV 검출/정렬 예외이면 `None` |
| 새 보조 정보 | 없음 | `FaceEmbeddingCandidate(embedding, quality)` |

근거: [이전 초기화·embedding](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/face_cluster.py.txt:23), [이전 CPU 설정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/config.py.txt:40), [새 초기화·embedding](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:30).

메인 댄서의 몸 bbox를 확장하는 ROI 비율은 가로 `.15`, 위 `.35`, 아래 `.10`으로 유지됐다. ROI 안에 다른 사람 얼굴이 있으면 여전히 “이 몸의 얼굴”을 연결하는 별도 판정 없이 confidence가 가장 높은 하나를 선택한다. 전체 화면의 모든 얼굴을 검출하는 기능이 이 커밋에 추가된 것은 아니다. [이전 ROI·설정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/config.py.txt:118), [새 ROI·설정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/config.py.txt:101)

새 모델은 `face_detection_yunet_2023mar.onnx`(232,589 bytes, SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`)와 `face_recognition_sface_2021dec.onnx`(38,696,353 bytes, SHA-256 `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`)다. URL은 OpenCV Zoo `main` 경로지만 정확한 size·hash를 검사한다. 임시 파일로 받은 뒤 검증에 통과하면 교체하고, `CLIPPER_DANCE_FACE_MODEL_DIR` 또는 `cwd/plugin_models/dance_highlight`를 사용한다. [고정 모델 명세](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_models.py.txt:26), [저장 경로·검증](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_models.py.txt:50), [다운로드 후 교체](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_models.py.txt:88)

## 4. sampling·clustering·reference mapping도 함께 바뀜

기존에는 세그먼트 bbox에서 최대 5개를 균등 추출하고, 얻어진 얼굴 embedding을 track별로 평균했다. 새 코드는 세그먼트 bbox에서 최대 12개 후보를 균등 추출한 뒤, 각 `(segment, track)` 안에서 품질 상위 최대 5개를 골라 평균한다. 후보 12개는 track마다 12개가 아니라 **세그먼트 전체에서 뽑는 수**다. 순차 영상 읽기 방식은 유지됐다. [이전 sampling](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/face_cluster.py.txt:94), [새 sampling](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:146), [track별 상위 표본·평균](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:252)

품질 점수는 `검출 confidence×.65 + 얼굴 면적/ROI 면적×.25 + blur 점수×.10`이다. blur는 얼굴 crop만이 아니라 **입력 ROI 전체**의 Laplacian 분산을 150으로 나눈 뒤 0~1로 제한한다. track 평균을 만들려면 유효 embedding이 최소 2개 필요하다는 규칙은 이전부터 있었다. 평균 track embedding이 없으면 segment의 `face_detected=False`가 되는 것도 새 교체 때 처음 도입한 규칙이 아니다. [새 품질 점수](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:95), [이전 최소 2개](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/face_cluster.py.txt:188), [새 최소 2개](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:255)

| 설정·판정 | 이전 → 7월 1일 |
|---|---|
| `face_det_size` | `(320,320)` → 유지 |
| `face_min_det_score` | `.28` → 유지 |
| `face_sample_frames` | `5` → 최종 선택 개수 `5` 유지 |
| `face_candidate_sample_frames` | 없음 → `12` |
| `face_nms_threshold`, `face_top_k` | 없음 → `.30`, `5000` |
| 군집 방식 | agglomerative, cosine, average linkage → 유지 |
| `cluster_distance_threshold` | `.42` → 유지 |
| DBSCAN 선택 설정 | eps `.6`, min_samples `2` → 유지 |
| 참조 멤버 배정 거리 | cosine distance `1-dot`, threshold `.60` → 유지 |

근거: [이전 설정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/config.py.txt:112), [새 설정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/config.py.txt:95), [기존 군집](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/face_cluster.py.txt:207), [새 군집](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:286).

참조 이미지 읽기·멤버별 평균 함수 `_build_reference_embeddings()` 자체는 바뀌지 않았다. 다만 같은 `get_face_embedding_from_image_path()` 호출이 이제 SFace embedding을 반환하므로 참조와 영상 양쪽의 특징 공간이 함께 교체됐다. 참조 이미지 각각의 유효 embedding을 평균하고 다시 L2 정규화하는 구조는 유지됐다. 새 후보 12개/품질 상위 5개 규칙은 영상 sampling용이며 참조 이미지 평균에 그대로 적용한 것이 아니다. [참조 평균 코드](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/pipeline.py.txt:168), [이미지 읽기·평균](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/face_cluster.py.txt:328)

이전 `_map_cluster_to_member_name()`은 각 cluster를 독립적으로 가장 가까운 멤버에 `.60` 이내이면 배정했다. 새 코드는 모든 cluster–멤버 후보를 거리 순서로 정렬해, 먼저 cluster와 멤버가 각각 한 번씩만 배정되는 **greedy 1차 배정**을 수행한다. 이는 최적 matching 알고리즘이 아니다. 이어서 1차 배정되지 않은 cluster는 자기 최인접 멤버에 `.60` 이내이면 다시 붙인다. 따라서 **최종 결과까지 1:1인 규칙은 아니다.** [이전 독립 배정](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/pipeline.py.txt:213), [새 1차 배정과 중복 허용 fallback](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/pipeline.py.txt:243)

7월 2일 session은 이 sampling/mapping 개선의 의도를 익명 cluster나 “멤버 0개 clip” 결과를 줄이는 것으로 설명한다. 실제 개선 정도를 측정한 숫자는 이 문구에 없다. [당시 의도 기록](/Users/jina/project/adlight/.codex/records/sessions/2026/07/02.md:33)

`pose_engine.py`, `segment.py`, `track.py`, `render.py`는 이 parent→커밋 diff에서 변경 파일이 아니다. YOLO/메인 선정·track/clip export를 얼굴 모델 교체와 같은 변경으로 설명하면 안 된다. `app.py`의 로딩 이름·runtime pipeline label, `dance_meta.py`의 후보 개수 설정 기록, manifest 모델 목록도 새 backend에 맞춰 바뀌었다. [전체 변경 파일별 diff](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/july-01.diff:1)

## 5. dependencies의 실제 변경

Dance `pyproject.toml`에서 `insightface>=0.7`, `onnxruntime>=1.19` 직접 의존성을 제거했다. `opencv-python>=4.10`은 pyproject에 **이미 있었으며 새로 추가한 패키지가 아니다.** manifest에는 기존 InsightFace/ONNXRuntime 항목을 빼고 OpenCV 항목을 추가했다. [이전 pyproject](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/dance_pyproject.toml.txt:5), [새 pyproject](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/dance_pyproject.toml.txt:5), [이전 manifest](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/before/manifest.json.txt:14), [새 manifest](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/manifest.json.txt:14)

`uv.lock`에서는 `insightface==0.7.3`과 관련된 12개 package 항목이 함께 사라졌다: albucore, albumentations, cython, easydict, imageio, ml-dtypes, onnx, prettytable, scikit-image, simsimd, stringzilla, tifffile. 새 package 항목이나 기존 package 버전 변경은 없었다. NumPy `2.4.4`, OpenCV `4.13.0.92`, scikit-learn `1.8.0`, Torch `2.11.0`, Ultralytics `8.4.38`은 동일했다. 이것은 **lock 비교**이며 당시 실제 설치 환경이 정확히 이 버전이었다는 별도 확인은 아니다. [전체 삭제 목록·유지 버전](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/lock-summary.txt:3)

`onnxruntime==1.24.4` 자체는 workspace lock에 남았다. Dance의 직접 의존성을 제거한 것이고, faster-whisper·supertonic 등 다른 경로에서 여전히 필요했다. “Python 전체에서 ONNXRuntime을 없앴다”라고 쓰면 틀린 설명이다. [유지 여부](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/lock-summary.txt:28)

## 6. 실제 검증 기록 — 있는 것과 없는 것

| 당시 확인 | 남은 기록 | 기록이 증명하는 범위 |
|---|---|---|
| OpenCV 실제 모델 API 확인 | `FaceDetectorYN`, `FaceRecognizerSF` 생성 성공 | 두 API·모델 초기화 가능 |
| Python adapter/model 단위 테스트 | 두 test 파일 `8 passed` | fake detector/recognizer, 모델 size/hash·경로·fake downloader 등의 계약 |
| Electron 검증 | TypeScript compile, `47 passed` | 설치 상태·런타임 주변 계약 |
| Dance health smoke | `1 passed, 2 deselected` | 플러그인 identity/health 응답 |
| 영상 경로 없음 smoke | `1 passed, 1 deselected` | 잘못된 입력의 실패 처리 |
| 사용자 실행 Mac 실제 영상 | `1 passed in 111.13s` | 해당 영상에서 pipeline 실행·산출물 생성 |

근거: [모델 API 확인](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:36), [단위·smoke 결과](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:184), [실제 영상 실행 기록](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:205).

Mac 영상은 당시 `sample_videos/KiiiKiii - 404 (New Era) #엠카운트다운 EP.915 | Mnet 260205 방송.mp4`로 기록돼 있다. summary는 duration `190.7239s`, raw main `200`, smoothed main `62`, kept main `61`, dropped no-face `1`, inferred persons `8`, montages `8`, main clips `61`, group clips `0`이다. 이 숫자들은 통과율·정확도나 GT 인원 수가 아니다. [출력 summary](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:217)

해당 SHA의 실제 E2E 테스트는 job 완료를 기다린 후 output 폴더에 **어떤 산출물이든 있는지** 검사한다. payload에는 `dance_setup`·참조 이미지·정답 멤버가 없다. 따라서 이 pass는 참조 멤버 식별 정확도 검증이 아니다. mapping용 새 단위 테스트도 합성 벡터 2개로 A/B 분리 배정 규칙을 검증한다. [실제 E2E assertion·payload](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/test_real_pipeline.py.txt:118), [합성 mapping 테스트](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/test_dance_cluster_member_mapping.py.txt:15)

기록의 정합성에도 작은 한계가 있다. 커밋 시점의 model test 함수는 5개, OpenCV adapter test 함수는 4개라 두 파일에는 총 9개의 test 함수가 있다. 문서의 `8 passed` 기록만으로 sampling 테스트까지 최종 커밋 전체가 다시 검증됐다고 확정할 수 없다. 실행 시점·버전 차이인지 기록 갱신 누락인지는 확인되지 않았다. “최종 커밋의 두 파일 9개 모두 통과”라고 바꾸어 쓰지 않는다. [model test 함수](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/test_dance_face_models.py.txt:15), [adapter test 함수](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/test_dance_face_cluster_opencv.py.txt:108), [새 sampling test](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/after/test_dance_face_cluster_opencv.py.txt:142)

7월 1일 worklog는 이 Mac pass가 최종 얼굴 군집 품질을 증명하지 않는다고 직접 적었다. 예상 인원보다 8이 많다면 montage를 눈으로 검토하고 군집 threshold나 sampling을 조정하라고 했으며, 대표 영상 시각 품질 검토·튜닝과 일반 PC의 Windows installer/plugin 실행 검증은 미완료로 남겼다. [품질 해석과 미완료 목록](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:231)

이후 7월 2일 session·누적 handoff에는 사용자가 Mac/Windows를 수동 테스트했고 Windows feature branch 앱 기동·Dance 설치/결과 생성이 대체로 동작했다는 추가 기록이 있다. 동시에 0-clip 멤버와 익명 cluster 품질 문제가 남았고, 알려진 영상들 및 옆각도·저해상도에서 품질을 검증하는 일은 후속 항목으로 남겼다. 이는 7월 1일 worklog의 “미완료” 이후 일부 수동 확인이 있었음을 뜻하며, 동일조건 모델 비교나 전체 Windows 검증 gate 완료를 뜻하지 않는다. [나중 수동 확인](/Users/jina/project/adlight/.codex/records/sessions/2026/07/02.md:1017), [당시 품질 문제·Windows 앱 동작](/Users/jina/project/adlight/.codex/handoff/archive/2026/07/next-handoff-through-2026-07-20.md:1778), [후속 품질 검증 항목](/Users/jina/project/adlight/.codex/records/sessions/2026/07/02.md:1101)

이번 관련 기록 검색에서 **고정 영상·참조 이미지·GT를 둔 old/new 검출률·identity precision/recall 비교표, threshold 후보별 수치, 선택된 threshold의 근거, Mac/Windows 동일 표본 정량 parity 결과**는 찾지 못했다. 실제 `.42` 군집 문턱과 `.60` 배정 문턱도 커밋에서 유지됐으므로 설계의 재조정 계획이 완료됐다고 단정할 근거는 없다. 이 검색 결과로 다른 PC·미보관 대화에서 실험을 전혀 하지 않았다고까지 단정하지 않는다.

## 7. 8월 13일 후속과 구분

`86fc71a02dd278c0fb5fd9dbcb59b75b67cad00c`의 author·committer는 `곽민준 <gwak0214@naver.com>`, 날짜는 모두 `2026-08-13 13:50:53 +0900`다. 직접 parent는 `2c1ea93de10dc5ef60e3beea5af85864520b58e4`다. Git name 원문은 분해형 한글로 저장돼 있고 여기서는 읽기 쉽게 표기했다. [원문 metadata](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/git-metadata.txt:11)

이 커밋은 얼굴 backend를 다시 바꾼 것이 아니다. 7월 1일 fallback은 참조 멤버가 1명이면 `.60` 안에 든 여러 cluster를 그 한 멤버로 배정할 수 있었다. 8월 13일에는 이미 1차 배정된 멤버에 추가 cluster를 붙일 때 `min(.45, 그 멤버의 1차 배정 거리 + .08)`를 통과해야 한다는 제한을 추가했다. 같은 사람이 각도·조명 탓에 여러 cluster로 나뉜 경우를 허용하면서 다른 사람의 흡수를 막으려는 변경이다. [8월 13일 실제 fallback diff](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/august-13.diff:5), [추가 합성 테스트 3개](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/august-13.diff:79)

곧이어 `65bbd33de0f0af0e1a64cdfe25cb0347bf559b4a`, `2026-08-13 13:52:14 +0900`, 같은 author·committer가 `.60/.45/.08`을 `DanceConfig`로 노출했다. 7월 1일 교체에 `.45/.08` 중복 제한이 있었다고 설명하면 시점이 틀린다. 두 8월 커밋 메시지에는 AI coauthor trailer가 있으나, 그것을 다른 인간 작업자의 신원 근거로 쓰지 않는다. [후속 설정 노출 metadata](/Users/jina/project/adlight/.codex/features/highlights/records/2026/09/evidence/face-change-2026-07-01/git-metadata.txt:25)

## 8. 찾아 읽은 관련 문서와 기록의 위치

`rg -l/-n`으로 `.codex`의 SHA, InsightFace/buffalo_l, YuNet/SFace, MSVC와 관련 파일명을 검색하고, Python/Electron `docs` 및 `clipper_docs`의 spec/plan/review도 확인했다. 이번 변경에 직접 해당하는 추가 repo-local spec/review는 검색에서 발견하지 못했다. 8월의 ranking review나 다른 주제의 모델 언급을 7월 1일 검증 기록으로 계산하지 않았다.

| 문서 | 역할 |
|---|---|
| [7월 1일 design](/Users/jina/project/adlight/.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md:1) | 장애 원인, 라이선스 판단, 교체·품질·Windows 검증 의도 |
| [통합 계획](/Users/jina/project/adlight/.codex/records/worklog/2026/07/plugin-runtime-isolation-and-dance-face-model-plan-2026-07-01.md:1) | 환경 분리 → quality spike → 모델 교체 → 패키지 검증 순서 |
| [환경 분리 구현 계획](/Users/jina/project/adlight/.codex/records/worklog/2026/07/plugin-runtime-isolation-implementation-plan-2026-07-01.md:245) | backend 교체와 Electron 환경 분리를 별도 검증 batch로 나누려는 의도·runtime 검증 |
| [YuNet/SFace replacement plan+progress](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-yunet-sface-replacement-plan-2026-07-01.md:173) | 실제 구현, unit/smoke/Mac 실제 영상 실행 숫자, 품질 미완료 |
| [멤버 profile·수동 mapping 계획](/Users/jina/project/adlight/.codex/records/worklog/2026/07/dance-member-profile-and-manual-mapping-plan-2026-07-01.md:5) | 익명 cluster를 사용자가 보정하는 별도 UX·서버 overlay; 모델 정확도 평가와 구분 |
| [7월 2일 session](/Users/jina/project/adlight/.codex/records/sessions/2026/07/02.md:33) | 커밋 목록·sampling/mapping 의도·나중 수동 확인·잔여 품질 항목 |
| [7월 누적 handoff](/Users/jina/project/adlight/.codex/handoff/archive/2026/07/next-handoff-through-2026-07-20.md:1766) | Windows 진단→교체→수동 동작→0-clip/익명 품질 문제의 흐름 |

사용자에게 설명할 때는 “7월 1일 Git 작성자는 metabuzz-jinahan이다. Windows 설치 장애와 모델 이용조건 때문에 InsightFace에서 YuNet/SFace로 교체했고 표본·배정도 함께 개선하려 했다. 실행 검증은 남아 있지만 정량 정확도 비교와 threshold 보정 완료 근거는 없다. 8월 13일 곽민준의 변경은 별도의 중복 멤버 배정 제한이다”라고 구분하면 로컬 근거에 맞는다.
