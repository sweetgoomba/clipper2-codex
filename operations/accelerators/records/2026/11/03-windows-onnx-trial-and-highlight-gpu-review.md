# Windows ONNX 시험과 세 하이라이트 GPU 통합 검토 — 첨부 원본 확인판

2026-11-03 KST. 제품 런타임을 수정하지 않고, 사용자 제공 키트 코드·ONNX 4개·NPZ·세 실행 JSON/TXT와 9개 저장소 최신 원격 refs를 검토했다.

**앞선 부분 로그 해석을 정정한다. AuraFace 전체 GPU 실패로 볼 수 없다.** 세 실행의 명시 DML/auto 총 6개 traceback은 모두 단일 장 시험과 비교가 끝난 뒤 추가한 **batch 8의 첫 호출**에서 발생했다. 키트가 batch 8 오류로 앞서 저장한 batch 1 결과를 덮어썼다. batch 1의 시간·cosine 수치는 소실되어 지금 파일로 복구할 수 없다.

이 PC는 **Windows 10 build 19045, NVIDIA GTX 1660 Ti, Ryzen 7 3700X(8코어/16스레드)**다. 제조사 실행기 시험은 bootstrap/catalog 등록에 실패했고, 세 실행 모두 등록된 GPU EP는 DirectML 하나다. 세 번째 표를 NVIDIA 전용 실행기 성능으로 읽으면 안 된다. DML을 선택한 세션에서 YOLO·YuNet·CLIP의 실행 시간 단축은 확인되지만, 비교 기준은 **같은 ONNX의 ORT CPU 실행**이다. 현재 앱 PyTorch/OpenCV 및 전체 앱 시간 대비 배율은 아직 측정하지 않았다.

기존 안무의 구간·정체성·역할 조립, 인물의 등장/음성 결합, 대사의 장면/STT/클립 파이프라인은 유지하면서 모델 추론 경계에서 통합할 수 있다. 사용자 지시로 보류된 `단체 조건 탈락→개인 메인` 판정은 이 검토에서 변경하지 않았다.

## 1. 저장소 조사 범위와 키트 출처

추가 요청에 따라 Electron/Angular/Nest, web client/admin/API/infra를 포함한 아래 **9개 저장소 모두 `git fetch --all --prune --tags`가 exit 0**이었다. 전부 `+refs/heads/*:refs/remotes/origin/*` refspec임을 확인했다. checkout/stash/reset/merge는 수행하지 않았다.

| 저장소 | 조사 당시 로컬 HEAD | fetch 후 origin/dev | fetch 후 origin/main | refs / 중복 제거 tip |
|---|---|---|---|---:|
| `desktop/clipper_electron` | `775ffd5e7df8bede6a9096316a7a367da8dba0da` | `8e70e99bc44e164d84dba16dd253b3b939928859` | `df36a6e66c5153f75a4af4f34f55716ed0ba5d72` | 99 / 60 |
| `desktop/clipper_angular` | `7217bda17e0330971aa4aa6a5f57f1950324e0c0` | `7a186b00907859aa9376b79211e593a2abd52afb` | `d2f2475feb964f5cd840409d47f3bcc43842fc8b` | 161 / 109 |
| `desktop/clipper_nestjs` | `e4e1fcf5d37bdbbd2c0c00a9f558b052c2d55f7f` | `f2cc17a9c6a73fa7096c602e8fc68df4403aeacc` | `ad719cab11bf657b28ca57ab5a06cdaad54e4e69` | 158 / 104 |
| `web/clipper_web_client` | `17e3e07ace8c67352217fc55a11a772f3fe24241` | `50779ad01b1abb7009205a8490979b7bf032dceb` | `74fc845e00b7837993b3c4bca514e6501e10b04c` | 51 / 28 |
| `web/clipper_web_admin` | `694a5227241f31b2f34c62efdb10dc40ebb01937` | `e84d531a086075245f991ec74d30b90265d1006c` | `2a4316211a842cdb3a320ce2156c7a6541c43571` | 69 / 44 |
| `web/clipper_web_api` | `ee9d41871ac63b85d92088a1727752ad329fa171` | `6e1d001c0f5bef357a1352bf667a8427e3ae0043` | `dc04f1eb61e1a391772d80ad5a5a27f22a31ab4e` | 135 / 94 |
| `web/clipper_infra` | `9732aee47540ccf78dbbc09979dad0553f209b89` | `f304750c4d1d6277483ba71ce73f88baaf33fe80` | `51fbc6992e48947dd0df947755d43088fd49dd7f` | 44 / 25 |
| `desktop/clipper_python` | `4b54bced17e13aadbeb97be75259b7f7213a9b24` | `4b54bced17e13aadbeb97be75259b7f7213a9b24` | `cf7744894eac0f33c5886ce586cb0ec7485b7ee3` | 97 / 55 |
| `clipper_docs` | `b2a18b021ecd27b4d0663f1e180cb8aa763bdd11` | `—` | `5b3b57a14879f26702fbc628f9a3c229bf216780` | 5 / 3 |

총 **819 refs, 저장소별 중복 제거 522개 tip commit**에서 `git ls-tree` 파일명과 `git grep` 텍스트를 검색했다. 또한 `git rev-list --objects --all`, `git log --all --name-only`, `git log --all -G<키트 패턴>`으로 도달 가능한 이력의 경로·문자열 변경을 확인했다. 검색어에는 `clipper-gpu-kit`, `run_kit.py`, 결과 timestamp, 배치 안내문, `same_people_dance/person`, `matched_box_iou_min`, `MLOperatorAuthorImpl`, `Init provider bridge failed`가 포함된다. 추가로 모든 tip에 `onnxruntime-directml`, `onnxruntime-windowsml`, `Windows ML`, `DmlExecutionProvider`, `PREFER_GPU`, `clip_visual`을 대조했다. **일치 0건**이다. 안무 미커밋 GPU 코드가 이 결과에 없는 것은 Git tip 검색과 작업 트리 검색이 다르기 때문이다.

명령을 shell pipe로 연결해 오류를 감추지 않았다. 기본 검색의 비-grep 명령 585개는 exit 0, 무일치 `git grep` 522개는 exit 1/빈 stderr이며, 추가 broad grep 9개도 exit 1/빈 stderr다. 해석할 수 없는 ref와 Git 오류는 0건이다. 전체 ref명·SHA와 명령별 exitcode/출력 크기는 [audit.json](03-windows-onnx-ref-search-evidence/audit.json), fetch 원 출력은 [fetch.json](03-windows-onnx-ref-search-evidence/fetch.json), 추가 검색은 [broad-audit.json](03-windows-onnx-ref-search-evidence/broad-audit.json)에 보존했다. 이는 fetch된 refs의 tracked text/경로 조사이며 다른 비공개 저장소, 미푸시 Windows 파일, 압축파일 내부·외부 LFS payload까지 부재를 증명하지 않는다.

`clipper_docs` 최신 `origin/main` **5b3b57a14879f26702fbc628f9a3c229bf216780**을 직접 검색했다. 로컬은 12커밋 뒤이며 최신 변경은 11개 문서(설명 숏폼·폰 리모컨·배너·해외 더빙·큐레이션)다. `gpu|directml|windows[ _-]?ml|onnx`는 33파일/162행에 일치했고 ref명·행번호를 제외한 내용은 로컬 HEAD 검색과 전부 같다. DirectML/Windows ML 일치는 0개다. 기존 GPU telemetry·과거 Windows CUDA 패키징·Supertonic/RapidOCR 문서는 있지만 이 시험 키트 설계/실험 결과 문서는 없었다. [원격 검색 전체](03-windows-onnx-ref-search-evidence/docs-gpu-current.txt), [12커밋](03-windows-onnx-ref-search-evidence/docs-remote-commits.txt), [직접 비교](03-windows-onnx-ref-search-evidence/docs-comparison.json).

키트는 이후 사용자가 `/Users/jina/Downloads`에 제공한 파일로 확보했다. Git 브랜치/SHA로 연결된 출처는 확인되지 않았다. `run_kit.py` 원본 SHA256은 `66930908463be4c7fab115e328cd11cf2ba7849213d71b0b7950754cf93fa34c`이다. 원본 코드/배치/manifest/JSON/TXT는 [첨부 증거 폴더](03-windows-onnx-kit-evidence/)에 보관했고 대용량 모델/NPZ는 원본 경로와 SHA만 기록했다. 이전 첨부 전 보고서도 그 폴더에 별도로 보존했다.

Python 작업 트리의 안무 GPU 개선은 여전히 미커밋이다. HEAD=`origin/dev`=`4b54bced17e13aadbeb97be75259b7f7213a9b24`인 것과 작업 트리의 새 GPU 어댑터를 구분해야 한다. 아래 제품 경로는 첫 조사 때 읽은 원본 작업 트리이며 다른 세션의 이후 런타임 변경을 덮어쓰지 않았다.

## 2. 제품의 실제 모델·선택 경로

| 기능 | 현재 모델/포맷·실제 호출 | Mac/Windows GPU 범위와 CPU 비용 |
|---|---|---|
| 안무 pose | `yolov8s-pose.pt`를 Ultralytics PyTorch로 로드, `imgsz=640`, `conf=.25`, `iou=.7`, `half`와 `device`를 매 호출 전달. [config.py:16](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/config.py:16), [pose_engine.py:16](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pose_engine.py:16). | Mac MPS, 기타 torch CUDA가 실제 사용 가능하면 장치0, 아니면 CPU. 제품 Windows 기본 wheel에서 CUDA 전체 설치가 확인된 것은 아니다. `.cpu().numpy()`로 박스/관절을 되가져오고 후속 선택·추적은 CPU. |
| 안무 YuNet | **이미 ONNX** `face_detection_yunet_2023mar.onnx`. OpenCV `FaceDetectorYN`을 유지하고, 미커밋 `AcceleratedYuNet`이 전체 원본 프레임만 고정 shape ORT로 실행한다. 32배수 zero pad, shape metadata 재추론, OpenCV 방식 decode/NMS를 Python에서 수행. 다른 크기 ROI는 OpenCV CPU. [face_cluster.py:69](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_cluster.py:69), [opencv_acceleration.py:21](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:21), [같은 파일:128](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:128). | Mac CoreML `MLProgram/CPUAndGPU`, Windows 제공 CUDA 우선·DML 차선·CPU fallback. ORT DML은 sequential/memory pattern off, 호출 lock. 세션 준비 실패/잘못된 출력/호출 실패 시 기존 OpenCV CPU로 복귀. `gpu_seconds`에는 pad/blob/ORT/decode가 포함돼 순수 GPU kernel 시간이 아니다. ROI CPU 검출·원본 decode·복사/해시도 별개. |
| 안무 얼굴 특징 | **이미 ONNX** AuraFace `glintr100.onnx` 512차원. 공통 5점 정렬·BGR→RGB·127.5 정규화 후 ORT. 안무만 `DanceFaceSession` factory를 주입해 CoreML/Windows CUDA/DML→CPU, 0입력 warmup, 유한 출력 검사, 실패 시 CPU 재시도와 정확 입력 hash 캐시를 쓴다. [auraface.py:18](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/auraface.py:18), [face_runtime.py:89](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_runtime.py:89). | 정렬/warp/blob/ROI 선택/512 벡터 이름 비교는 CPU. 제품은 batch 1 경로다. 이번 키트의 batch 8 실패만으로 제품 AuraFace가 CPU fallback된다고 단정할 수 없다. CUDA EP가 노출되었다가 실패하면 현재는 DML을 다시 시도하지 않고 CPU로 내려간다. |
| 안무 보조 SFace | **이미 ONNX** `face_recognition_sface_2021dec.onnx`. OpenCV 정렬 유지, `AcceleratedSFace`가 같은 112×112 RGB float32 입력으로 ORT, 실패하면 OpenCV CPU. [opencv_acceleration.py:193](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:193). | 안무 전용 세션을 검증 단계 사이 재사용. 정렬/참조 이름 판정은 CPU. |
| 인물 | 동일 pose `.pt`, YuNet `.onnx`, AuraFace `.onnx`. `YoloBodyDetector.detect`와 `OpenCvFaceBackend.detect`를 프레임별 실행. 공유 AuraFace 기본 provider는 **CPU**이며 안무 factory를 주입하지 않는다. [body_detector.py:44](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/body_detector.py:44), [opencv_backend.py:20](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/opencv_backend.py:20), [auraface.py:21](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/auraface.py:21). | torch CUDA→MPS→CPU 탐지. MPS/CUDA와 가용 RAM≥2GiB일 때 한 프레임의 CPU 얼굴과 GPU body를 겹친다. 이후 사람 군집·음성 대응·클립 구성은 별도 인물 정책. [frame_inference.py:8](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/frame_inference.py:8), [app.py:178](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/app.py:178). |
| 대사 시각 | OpenCLIP `ViT-B-32/laion2b_s34b_b79k`, 현재 PyTorch/safetensors 경로. 키프레임을 BGR→PIL→preprocess→tensor batch→`.to(device)`→`encode_image`→L2/shot 평균. **제품에서는 ONNX가 아니다.** [common.py:101](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/common.py:101), [embedding_pipeline.py:55](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/embedding_pipeline.py:55), [staged_artifacts.py:119](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:119). | torch CUDA→MPS→CPU. 키프레임 decode, 색 변환, PIL/preprocess, tensor upload, shot mean, 비교·구간화는 모델 추론과 별도. |
| 음성/기타 | 인물·대사는 공유 faster-whisper/CTranslate2 `small`; CUDA float16 실패 시 CPU int8, MPS 요청은 CPU. 대사 EasyOCR는 기본 off이고 CUDA 외 실행하지 않는다. [speech model.py:34](/Users/jina/project/adlight/desktop/clipper_python/clipper_speech_core/clipper_speech_core/model.py:34), [staged_artifacts.py:100](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:100). | 키트의 `clip_visual` 성공은 STT·scene detect·audio feature·export 가속 증거가 아니다. 안무 SAM/mask/joint heavy 검증은 현재 `disabled_runtime_cost_v1` OFF이며 CPU로 남은 가벼운 body 비교와 구분한다. |

정확한 ONNX 모델 원본과 hash는 [Dance face_models.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_models.py), [공통 face_models.py](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/face_models.py), [Person model_assets.py:15](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/model_assets.py:15)에 고정돼 있다. 현재 안무만 [pyproject.toml:11](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/pyproject.toml:11)에서 Windows `onnxruntime-directml==1.24.4`, 기타 OS `onnxruntime==1.31.0`을 배타 marker로 설치한다. Person은 CPU ORT 1.31.0, Dialog에는 OpenCLIP·speech core가 있다. Windows ML 1.30.0 시험 wheel을 제품이 설치한다는 근거는 없다.

## 3. 설치·장치 선택·설정의 경계

Electron은 OS GPU/driver/VRAM을 관측하지만 그 결과로 모델 EP나 wheel을 고르지 않는다. 패키징 앱은 플러그인별 venv에 `uv sync --frozen --no-dev --no-editable`을 실행하고 Python으로 플러그인을 시작한다. [plugin-venv.ts:53](/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-venv.ts:53), [plugin-process.ts:165](/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-process.ts:165). CUDA/DirectX 드라이버 자동 설치, DML GPU index와 OS 목록 연계, 사용자별 EP 우선순위/강제 CPU 설정은 없다. DirectML 기본 어댑터가 최적 GPU라는 보장도 없다. 개발 `uv run`의 공용 환경과 패키징의 플러그인별 exact sync는 구분해야 한다. CPU ORT와 DML wheel을 같은 venv에 덧설치하면 충돌 위험이 있어 현행 배타 marker가 중요하다. 상세 횡단 감사: [2026-11-02 앱 GPU 아키텍처](/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/02-app-gpu-architecture-audit.md).

SDK `/runtime/accelerators`는 torch·ORT·CTranslate2 probe와 플러그인별 `selected`를 Nest/Angular에 전달한다. ORT `get_available_providers`나 session `get_providers`는 등록 가능성이지 모든 노드의 GPU 배정 증거가 아니다. Angular 대시보드는 DML label이 없고 모델별 `selected.models`를 아직 표시하지 않는다. [SDK base.py:398](/Users/jina/project/adlight/desktop/clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py:398), [dashboard.component.ts:645](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/dashboard/dashboard.component.ts:645). 안무의 미커밋 `app.py`는 YOLO/얼굴 모델별 provider와 fallback 통계를 응답한다. [dance app.py:69](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/app.py:69).

## 4. 첨부 모델과 입력의 실제 구조

모델 4개의 파일 크기와 SHA256은 모두 첨부 manifest와 일치했다. YuNet과 AuraFace는 제품에 고정된 원본 SHA와도 같다. 모델을 실행하지 않고 ONNX graph와 metadata만 읽었다. [전체 모델·표본·파일 해시](03-windows-onnx-kit-evidence/model-samples-audit.json).

| 모델 | ONNX 입력 → 출력 | export/정밀도 | NPZ 표본 |
|---|---|---|---|
| YOLOv8s-pose | `[1,3,640,640]` → `[1,56,8400]` | opset 17/IR8, PyTorch2.11.0, Ultralytics8.4.38. metadata `batch=1, half=False, dynamic=False, simplify=True, nms=False`; float32 | 24개, float32, 값0–1 |
| YuNet 2023mar | `[1,3,640,640]` → cls/obj/bbox/kps 12출력 | opset11/IR6, float32. 원본 SHA `8f2383…2fa4` | 24개, float32, 값0–255 |
| AuraFace v1 | `[None,3,112,112]` → **`[1,512]`** | opset11/IR6, float32. 원본 SHA `a7933e…5c60`. input batch만 가변, output batch 고정 | 30개, float32, 값−1–1 |
| CLIP visual | `[batch,3,224,224]` → `[batch,512]` | opset17/IR8, PyTorch2.11.0, float32, 가변 batch | 24개, float32, 약−1.792–2.146 |

YOLO와 CLIP의 실제 ONNX export 결과는 확보했지만 **export 스크립트와 표본 생성 코드/원본 영상·프레임 목록은 없다.** manifest의 YOLO torch 대비 최대 상대오차 `3.84664e-6`, CLIP 최소 cosine `0.99999994`는 제작자가 기록한 값이다. 이번에 그 원래 비교를 재현한 것은 아니다. NPZ 범위가 예상 정규화와 일치하는 것만으로 RGB/BGR·resize/crop/letterbox·face alignment가 제품과 같다고 증명하지 않는다.

특히 제품 Ultralytics는 이미지 형상과 `rect` 설정에 따라 최소 사각 padding을 사용한다([설치된 predictor.py:185](/Users/jina/project/adlight/desktop/clipper_python/.venv/lib/python3.11/site-packages/ultralytics/engine/predictor.py:185)). 이 키트의 고정640×640과 제품 `.pt`의 실제 입력 shape/역좌표 변환을 맞춰야 한다. 키트 YuNet640×640 시간도 제품의 원본 해상도 전체 프레임/가변 ROI 검출 시간과 직접 비교할 수 없다.

## 5. 세 실행의 확인된 결과

모든 JSON에서 OS는 `Windows-10-10.0.19045-SP0`, Python3.11.14, GPU는 GTX1660Ti, driver `32.0.15.8157`, DML `DxgiAdapterNumber=0`, PCI device `0x2182`, `DxgiVideoMemory=5966MB`로 같다. WMI `AdapterRAM=4293918720`은 별도 값이므로 이를 근거로 VRAM4GB라고 단정하지 않는다. CPU는 Ryzen73700X,8코어/16스레드다.

아래는 **같은 준비된 ONNX 입력의 session.run 중앙값 ms/장**이다. GPU 칸은 명시 DML0 / auto 순서다.

| 모델 | DirectML ORT1.24.4 CPU → GPU | Windows ML ORT1.30.0 CPU → GPU | vendor 시험 ORT1.25.2 CPU → GPU |
|---|---:|---:|---:|
| YOLO pose | 89.93 → 12.95 /10.81 | 67.53 → 13.04 /10.77 | 66.73 → 13.07 /10.96 |
| YuNet | 4.71 → 2.46 /2.50 | 4.77 → 2.52 /2.53 | 4.88 → 2.47 /2.54 |
| AuraFace batch1 | CPU56.49; GPU수치 소실 | CPU42.14; GPU수치 소실 | CPU77.69; GPU수치 소실 |
| CLIP visual batch1 | 31.94 → 14.51 /13.03 | 27.26 → 14.54 /13.31 | 29.68 → 15.11 /13.35 |
| CLIP visual batch8, 장당 | 25.26 → 8.23 /8.31 | 23.49 → 8.37 /8.54 | 24.31 → 8.43 /8.41 |

세 실행에서 YOLO GPU warm 시간은 거의 같지만 CPU는89.93→67.53→66.73ms로 달라져 보고된 배율도6.94/8.32→5.18/6.27→5.11/6.09로 변한다. ORT 버전, 실행 순서, 잔존 세션/thread pool, 시스템 상태를 통제한 실험이 아니므로 한 배포판이 다른 배포판보다 빠르다는 결론을 내릴 수 없다. CLIP batch8의 처리량은 좋지만 batch8 출력 동등성 검사가 없는 점은 아래와 같다.

`run.bat`은 세 시험을 서로 다른 `uv run --with` 환경으로 실행한다. 1.24.4, `onnxruntime-windowsml==1.30.0.202609102321`, wasdk2.3.0 의존성으로 선택된 ORT1.25.2다. **제조사 시험에서는 bootstrap 오류와 “프로세스에 패키지 ID가 없습니다” catalog 오류가 기록됐다.** `registered`가 비었으며 `winml:<vendor>` 행이 없다. 성공 행의 `providers_used`는 모두 `[DmlExecutionProvider, CPUExecutionProvider]`다. auto가 새로운 CUDA/TensorRT EP를 선택한 시험이 아니다.

현재 Microsoft의 catalog EP 요건은 Windows11 24H2 이상이고 NVIDIA NvTensorRtRtx는 RTX30 이상이다. 이 Windows10/GTX1660Ti 장비는 그 요건을 충족하지 않는다. DirectML 지원과 제조사 EP 적격성은 구별해야 한다. [Microsoft EP 요건](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/supported-execution-providers), [ORT DirectML 요구사항](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html). 세 번째의 약15분 간격을 모델 추론 시간으로 세지 않는다. 설치/부트스트랩/UI 대기 등의 개별 타이머가 없어 정확한 배분은 알 수 없다.

## 6. AuraFace 오류의 실제 경로와 유력 원인

첨부 [run_kit.py:234](/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/03-windows-onnx-kit-evidence/run_kit.py:234)는 session 생성 → batch1 `run_all` → CPU/GPU `compare` 및 row 저장 → 선택적 batch8 순서다. **여섯 traceback 모두 :240(batch8) → :136(first session.run) → ORT native binding**이다. 따라서 batch1 실행·비교 절차가 예외 없이 끝났다는 코드상 근거가 있다. 하지만 :241–242의 넓은 except가 row 전체를 error로 교체해 단일 장 timing/providers/cosine을 삭제했다. 수치가 남아 있지 않아 AuraFace 배율·정확도 합격을 주장할 수 없다. fake 추론으로 동일 덮어쓰기를 재현했다([contract-probes.json](03-windows-onnx-kit-evidence/contract-probes.json)). 제품은 현재112×112 batch1을 호출하므로 batch8 실패를 그대로 제품 가속 불가로 확대하면 안 된다.

또한 AuraFace의 input batch는 symbolic `None`인데 마지막 `/features/BatchNormalization` 출력 `1333`의 batch는1로 고정돼 있다. 원본을 바꾸지 않고 메모리에서 batch를 지정해 ONNX strict shape inference를 실행했다.

| shape 검사 | 원래 출력 `[1,512]` | 출력 batch만 가변으로 표기한 메모리 사본 |
|---|---|---|
| 입력 batch1 | 통과 `[1,512]` | 통과 `[1,512]` |
| 입력 batch8 | **동일 `/features/BatchNormalization`에서 `(8) vs (1)` 불일치** | 통과 `[8,512]` |

[shape 검사 원 결과](03-windows-onnx-kit-evidence/auraface-shape-inference.json), [재현 코드](03-windows-onnx-kit-evidence/review_auraface_shapes.py)(ONNX 1.20.1, 모델 추론 없음). 마지막 BN의 scale/bias/mean/variance는 모두512 float32, epsilon≈1e−5다. **출력 metadata 불일치는 정적으로 확인된 결함이며 DML batch8 실패의 가장 직접적인 후보**다. 이를 고치면 해당 Windows 드라이버/ORT에서 실행도 성공하는지는 아직 확인하지 않았다. 모델 재학습이나 BN 노드 삭제가 필요한 상황으로 단정하지 않는다. 먼저 batch1 결과를 보존하고, 별도 이름/해시의 출력-shape 보정 사본을 batch8에서 비교하는 검증이 최소 단계다. 원본 모델 파일은 보존한다. [ONNX BN shape 계약](https://onnx.ai/onnx/operators/onnx__BatchNormalization.html).

`UnicodeDecodeError` 원본 bytes의 `\xb8\xc5...`를 CP949로 읽으면 **“매개 변수가 틀립니다.”**라는 Windows 오류 문구가 나온다. traceback은 subprocess.stdout/키트 텍스트 파일 쓰기가 아니라 **ORT `_sess.run` 경계**에서 UTF-8 디코딩 실패를 보여준다. 따라서 `chcp65001`, `PYTHONIOENCODING=utf-8`을 다시 설정하는 것만으로 계산 오류나 이 native 예외 변환을 해결할 근거는 없다. 1차 실패는 DML invalid argument(`0x80070057`), 2차 실패는 CP949 메시지를 UTF-8로 처리한 오류다. 원 오류 bytes와 trace는 JSON에 이미 보존되어 있다.

`Init provider bridge failed` 후에도 builtin DML 실행은 진행됐으므로 이를 전체 GPU 초기화 실패와 같게 보면 안 된다. 어떤 bridge library가 왜 실패했는지는 로그에 부족하다. 중복 `ep.dmlexecutionprovider.device_id=0` 경고도 키트의 explicit tuple은 한 번만 설정한다(:123–125). native 내부 설정/자동 등록 경로까지 추적하지 않고 키트가 옵션을 두 번 넣었다고 확정하지 않는다. 같은0으로 덮어쓴 경고이며, batch8 BN shape 오류와의 인과 근거는 없다.

## 7. 키트 코드 리뷰: 채택 전 고칠 것

| 우선순위 | 확인한 문제 | 제품/후속 시험에 필요한 조치 |
|---|---|---|
| 높음 | 선택적 batch8 실패가 batch1 성공/측정값을 삭제(:234–244). 실제6행에서 발생 | batch1과 각 batch 시험을 독립 결과로 보존. 모델/provider/batch별 즉시 저장하고, 추가 시험 실패를 별도 `batch8.error`로 기록 |
| 높음 | YuNet `same_face_count`는 **NMS 이전 anchor score>.6 개수**만 비교(:167–180). bbox/kps/decode/NMS를 확인하지 않음. 안무 threshold .28도 검사하지 않음 | 제품 OpenCV/adapter와 같은 decode·threshold·정수 박스 NMS 후 얼굴 개수/박스/5점 landmark를 일대일 비교하고 최종 이름 판정 대조 |
| 높음 | YOLO는 박스와 인원수만 확인.17개 관절/관절 confidence 미검사, box 매칭도 단방향 maxIoU라 일대일 보장 없음(:156–165) | pose/score/소인물·가림·NMS 문턱·최종 main/group/person 결과까지 비교. 제품 전처리/좌표 복원과 NMS cap 등도 일치 확인 |
| 중간 | `cosine_min=1.0`은 소수5자리 반올림이고 finite/허용오차 합격 기준이 없음(:151–155). batch8은 outputs=[]여서 정확도 비교0회(:145) | 반올림 전 오차·NaN/Inf·norm·shape·문턱별 판정/배치별 출력 비교를 보존. 1.0을 bit-identical이라고 설명하지 않음 |
| 중간 | manifest SHA/bytes가 있지만 실행 코드는 검증하지 않고 결과에도 source/model/sample hash·명령·runs를 기록하지 않음(:208–225) | 실행 전 hash 검사, export provenance·표본 원본 목록/전처리 버전·전체 명령/환경을 결과에 포함 |
| 중간 | 명시 DML은 memory pattern off/sequential이나 auto 분기와 adapter probe는 이를 직접 설정하지 않음(:55,109–125). `get_providers`만 보고 가속 성공 표시 | runtime 적용 SessionOptions·provider options·adapter·노드 배정 확인. DML 경로마다 동일 제한을 검증. `enable_fallback=0`은 graph CPU partition 금지를 뜻하지 않음 |
| 중간 | 존재하지 않는 adapter나 모델/driver 오류가 모두 `break`로 처리돼 뒤 adapter를 생략(:53–60). Windows catalog 실패 후에도 vendor label 그대로 | 장치별 실패 원인과 실제 등록/선택 EP를 분리. 지원 OS/GPU에서만 제조사 catalog 시험 수행 |

비교 함수의 허점을 모델 없이 재현했다. YuNet bbox/landmark를1000씩 바꿔도 `same_face_count=1/1, score_diff=0`; YOLO의 모든 keypoint를1000으로 바꿔도 `same_people=1/1, IoU=1.0`이다. [재현 코드](03-windows-onnx-kit-evidence/review_contract_probes.py), [결과](03-windows-onnx-kit-evidence/contract-probes.json). 이는 실제 GPU 결과가 틀렸다는 증거가 아니라 **현재 지표로는 그 오류를 잡을 수 없다는 증거**다.

측정은 미리 준비된 NPZ tensor에서 첫 호출1회, warmup3회, 기본20회 중앙값/p90, 이후 표본 전체 출력 비교 순서다. 따라서24장 중 timing은 앞20장, Aura30장도 timing은 앞20장이다. batch8은 기본5회이며 Aura의 뒤6개는 잘라낸다. 모델 load는 JSON의 `load_s`로 따로 기록되나 원본 decode·resize·정렬·NMS·클립 조립은 타이밍에 없다. 반대로 `session.run`은 NumPy 입력/출력과 runtime overhead/전송이 포함될 수 있으므로 순수 GPU kernel 시간도 아니다. CPU→DML→auto 고정 순서이고 세션을 명시 해제하지 않아 이전 세션/thread pool이 겹쳐 남을 수 있다. 동일 조건 반복·순서 교차·빈/따뜻한 캐시·GPU 동시 부하를 통제해야 한다.

README의 “모든 파일이 폴더 안, 지우면 흔적 없음”도 제조사 catalog의 `ensure_ready_async`/Windows App SDK 설치까지 보장하는 설명은 아니다. 이번 PC는 등록 실패였으며 별도 시스템 설치가 성공했다는 주장은 하지 않는다. 원본 키트/uv.exe는 실행하지 않았다.

## 8. ONNX 포맷과 런타임 교체, 최소 통합 경계

ONNX export는 모델 연산·가중치를 graph로 직렬화하는 작업이다. 첨부 YOLO·CLIP은 그 산출물이고, YuNet·AuraFace·SFace는 제품에서 이미 ONNX다. ORT/DirectML/Windows ML 선택은 그 graph를 어떤 실행기로 돌릴지 정하는 별도 작업이다. Windows ML을 설치했다고 모델·전후처리·구간 판단이 함께 바뀌지 않는다. [PyTorch ONNX](https://docs.pytorch.org/docs/stable/onnx), [Windows ML 배포](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/distributing-your-app).

안무/인물은 `frame BGR → body/pose observations`, 대사는 `keyframes → 정규화된 visual embeddings` 경계에서 backend를 선택한다. 얼굴은 공유 정렬·모델 hash·512차원 계약과 안무의 session factory/CPU fallback을 보존한다. 역할/정체성/구간/클립 조립을 ONNX export 안에 넣거나 버릴 이유가 없다. 기존 안무의 CPU 병렬·정확 입력 캐시·prefetch·원본 읽기 재사용도 함께 사용할 수 있다. 공유 Person 기본값을 바꾸는 것은 각 기능의 동등성 검증 후 별도 적용한다.

이 PC에서 우선 검증할 경로는 **기존 DML batch1**이다. AuraFace batch1 수치를 먼저 다시 보존하고, batch8 output shape 보정은 독립 실험으로 둔다. NVIDIA 제조사 EP를 위해 이 GTX1660Ti PC의 환경만 반복 변경하는 것은 지원 요건상 적절한 검증이 아니다. Mac의 MPS/CoreML 경로는 별도 측정하고 Windows 수치를 전용하지 않는다.

모델별 adapter 선택은 `auto/CPU/검증된 EP` 정도의 명시적 사용자·진단 계약을 갖추되, 지원하지 않는 조합은 CPU로 복귀하고 실제 선택 EP·adapter index·fallback 원인·모델 hash를 기록해야 한다. AuraFace batch8 실패로 현재 제품의 batch1 fallback을 예측하지 않는다. batch1 실제 결과와 GPU 배정을 별도로 보존해야 한다. OpenCLIP ONNX 결과를 제품에 넣을 때는 model graph만이 아니라 RGB resize/crop/mean/std, L2, shot 평균과 최종 구간까지 비교한다.

단일 추론의 `6.94–8.32배`는 전체 앱 배율이 아니다. 다른 비용이 고정일 때 Amdahl 상한 `전체배율=1/(1-p+p/s)`에서 YOLO가 전체 실행 시간의 `p`를 차지하고 그 단계만 `s=8.32`배가 되면:

| 가정한 YOLO 시간 비중 | 전체 이론상한 | 전체 시간 감소 |
|---:|---:|---:|
| 10% | 1.096배 | 8.8% |
| 25% | 1.282배 | 22.0% |
| 50% | 1.785배 | 44.0% |

이는 모델 load/export cache, 첫 실행, frame decode, resize/upload/download, CPU NMS·ROI·얼굴·이름·장면·clip, GPU 간 경합이 **추가되지 않는 이상적인 상한**이다. 실제 stage 비중은 기기/영상/모델에 따라 다르다. 이미 Mac에서 안무 YuNet/SFace GPU화를 앱 세 영상에 적용했을 때 모델 추론은 빨라졌지만 전체는 1673.480→1597.736초, **4.5% 단축**에 그쳤다. 이어 CPU 병렬·정확 재사용·prefetch·원본 읽기 개선은 별도 앱 비교 1597.736→1219초 안팎으로 단축했으나 조건별 한 번 측정이며 품질 수정도 일부 포함됐다. [YuNet/SFace GPU 실측](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-yunet-sface-gpu-results.md), [내부 병목/앱 비교](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-deep-profile-results.md). 최신 연속성 빌드 세 영상은 `MMN 1793649506337`, `ANT 1793649573540`, `NEON 1793649654322`, 합계 **1326.930초**로 직전1207.958초보다 느렸다. [최신 앱 기록](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/03-role-continuity-app-results.md). 서로 다른 시점·코드/조건의 숫자를 하나의 누적 속도 개선으로 합산하지 않는다.

현재 Dance 성능 조치의 범위: `face_runtime.py`의 OpenCV CPU 병렬 설정, 정확 bytes hash 검출/embedding 캐시; `opencv_acceleration.py`의 안무 전용 CoreML/DML; 전체 프레임 source 재사용과 ROI prefetch; 동일 갤러리 fingerprint/포즈 대응/장면 확인의 재계산 축소. [main-face 계획](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-main-face-performance-plan.md), [deep profile](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-deep-profile-results.md). CPU ROI 검출, 원본 decode, 96MiB frame cache, `cv2` copy/warp/해시, Python NMS는 여전히 비용이다. `gpu_seconds`와 stage wall time을 별도로 보고해야 한다. heavy SAM/mask/joint는 `disabled_runtime_cost_v1` OFF이며, 꺼서 바뀐 미확인/클립 품질도 기록됐다. [mask 비용 결과](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-mask-cost-reduction-results.md).

## 9. 남은 검증과 이번 작업의 범위

1. 키트의 결과 덮어쓰기를 고친 사본에서 동일 PC의 AuraFace **batch1만** 먼저 재실행해 timing/cosine/EP/노드 배정을 보존한다. 기존 원본 모델은 유지한다.
2. batch8 출력 shape metadata만 보정한 별도 사본으로 같은 DML/CPU 비교. 정적 검사 통과를 Windows 실행 성공으로 대신하지 않는다.
3. 기존 제품 PyTorch/OpenCV CPU·Mac MPS/CoreML·Windows DML을 같은 원본 영상/전처리/샘플링으로 대조한다. YOLO 관절, YuNet NMS/랜드마크, identity 문턱, CLIP shot 특징과 최종 클립을 확인한다.
4. 원본 decode/ROI copy/preprocess/upload/inference/download/postprocess와 앱 started→completed를 분리 측정한다. cold/warm·median/p90·CPU/GPU RAM·fallback·모듈 SHA를 함께 보존한다.

수행: 원격 fetch/읽기,9개 repo819refs 검사, 첨부 파일 hash/ONNX metadata/NPZ 검사, 메모리상 strict shape inference4조건, fake inference 및 순수 비교 함수3개 재현, 공식 문서 대조. 수행하지 않은 검증: Windows 기기 재실행, 실제 모델 추론·앱 빌드/재시작·성능 재측정. 제품 소스·첨부 원본 모델/키트는 수정하지 않았다. 보관한 문서와 증거만 추가/갱신했다.
