# Windows ONNX 시험과 세 하이라이트 GPU 통합 검토

2026-11-03 KST. 읽기 중심 조사. 제품 런타임·모델·브랜치·앱 프로세스는 변경하지 않았다. **결론:** 팀원 시험의 YOLO pose, YuNet, CLIP 시각 추론은 해당 PC의 24개 입력에서 빠르고 일부 수치 동등성이 보고되었다. AuraFace는 DirectML과 Windows ML 시험 모두 실패했다. 키트 소스와 전체 결과가 없으므로 제품 속도·정확도·타 기기 호환성을 확정할 수 없다. 기존 안무·인물·대사 파이프라인을 폐기할 근거는 없고, 모델별 추론 경계에서 검증해 통합하는 것이 맞다.

## 근거의 시점과 검색 범위

| 대상 | 확인한 상태 |
|---|---|
| Python 제품 | `desktop/clipper_python` 작업 브랜치 `fix/dance-gpu-performance-20261102`; HEAD와 fetch 후 `origin/dev` 모두 `4b54bced17e13aadbeb97be75259b7f7213a9b24`. 수정/미추적 약 91항목. GPU 어댑터 `face_runtime.py`, `opencv_acceleration.py` 및 현재 역할·구간 수정은 **미커밋 작업 트리**에 있다. 원격 dev에 실렸다고 쓰면 틀리다. `origin/main`은 `cf7744894eac0f33c5886ce586cb0ec7485b7ee3`이다. |
| 문서 | `clipper_docs` main `b2a18b0`, `origin/main`보다 12커밋 뒤. fetch 수행. 일반 역사 문서에는 과거 InsightFace/CPU 설명이 남아 있어 현재 코드의 근거로 쓰지 않았다. `.codex`의 GPU 감사와 앱 실행 기록은 현재 미커밋 로컬 자료다. |
| Windows 키트 | 사용자가 본 경로 `C:\Users\Metabuzz\Desktop\clipper-gpu-kit`, `run_kit.py`, 배치 파일, `results/directml20261103-053501`. 이 Mac의 `/Users/jina/project/adlight`, Desktop/Downloads 및 `/Users/jina` 파일명 탐색, Python/Docs fetch 후 모든 로컬·원격 ref/태그의 Git object 경로, 모든 ref tip 문자열, `run_kit.py`의 전체 커밋 pickaxe를 조사했지만 파일·문서·커밋 일치가 없었다. 다른 저장소 Git object 경로에도 일치하지 않았다. **해당 Windows PC 파일에 접근한 적이 없고 키트 SHA/작성자/export 코드도 확인할 수 없다.** 아래 시험 수치는 사용자 제공 부분 로그다. |

검색 명령의 무출력은 이 사본의 검색 결과이지 Windows PC나 비공개 저장소에 파일이 없다는 증명이 아니다. 키트 소스가 없어서 정확한 export `opset`, shape, batch, half, preprocessing/postprocessing/NMS, 오류 래핑 구현은 리뷰할 수 없다.

## 제품의 실제 모델·선택 경로

| 기능 | 현재 모델/포맷·실제 호출 | Mac/Windows GPU 범위와 CPU 비용 |
|---|---|---|
| 안무 pose | `yolov8s-pose.pt`를 Ultralytics PyTorch로 로드, `imgsz=640`, `conf=.25`, `iou=.7`, `half`와 `device`를 매 호출 전달. [config.py:16](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/config.py:16), [pose_engine.py:16](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pose_engine.py:16). | Mac MPS, 기타 torch CUDA가 실제 사용 가능하면 장치0, 아니면 CPU. 제품 Windows 기본 wheel에서 CUDA 전체 설치가 확인된 것은 아니다. `.cpu().numpy()`로 박스/관절을 되가져오고 후속 선택·추적은 CPU. |
| 안무 YuNet | **이미 ONNX** `face_detection_yunet_2023mar.onnx`. OpenCV `FaceDetectorYN`을 유지하고, 미커밋 `AcceleratedYuNet`이 전체 원본 프레임만 고정 shape ORT로 실행한다. 32배수 zero pad, shape metadata 재추론, OpenCV 방식 decode/NMS를 Python에서 수행. 다른 크기 ROI는 OpenCV CPU. [face_cluster.py:69](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_cluster.py:69), [opencv_acceleration.py:21](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:21), [같은 파일:128](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:128). | Mac CoreML `MLProgram/CPUAndGPU`, Windows 제공 CUDA 우선·DML 차선·CPU fallback. ORT DML은 sequential/memory pattern off, 호출 lock. 세션 준비 실패/잘못된 출력/호출 실패 시 기존 OpenCV CPU로 복귀. `gpu_seconds`에는 pad/blob/ORT/decode가 포함돼 순수 GPU kernel 시간이 아니다. ROI CPU 검출·원본 decode·복사/해시도 별개. |
| 안무 얼굴 특징 | **이미 ONNX** AuraFace `glintr100.onnx` 512차원. 공통 5점 정렬·BGR→RGB·127.5 정규화 후 ORT. 안무만 `DanceFaceSession` factory를 주입해 CoreML/Windows CUDA/DML→CPU, 0입력 warmup, 유한 출력 검사, 실패 시 CPU 재시도와 정확 입력 hash 캐시를 쓴다. [auraface.py:18](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/auraface.py:18), [face_runtime.py:89](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_runtime.py:89). | 정렬/warp/blob/ROI 선택/512 벡터 이름 비교는 CPU. DML이 BatchNormalization에서 실패한 팀원 PC에서는 이 경로가 실제로 CPU fallback될 수 있다. CUDA EP가 노출되었다가 실패하면 현재는 DML을 다시 시도하지 않고 CPU로 내려간다. |
| 안무 보조 SFace | **이미 ONNX** `face_recognition_sface_2021dec.onnx`. OpenCV 정렬 유지, `AcceleratedSFace`가 같은 112×112 RGB float32 입력으로 ORT, 실패하면 OpenCV CPU. [opencv_acceleration.py:193](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:193). | 안무 전용 세션을 검증 단계 사이 재사용. 정렬/참조 이름 판정은 CPU. |
| 인물 | 동일 pose `.pt`, YuNet `.onnx`, AuraFace `.onnx`. `YoloBodyDetector.detect`와 `OpenCvFaceBackend.detect`를 프레임별 실행. 공유 AuraFace 기본 provider는 **CPU**이며 안무 factory를 주입하지 않는다. [body_detector.py:44](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/body_detector.py:44), [opencv_backend.py:20](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/opencv_backend.py:20), [auraface.py:21](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/auraface.py:21). | torch CUDA→MPS→CPU 탐지. MPS/CUDA와 가용 RAM≥2GiB일 때 한 프레임의 CPU 얼굴과 GPU body를 겹친다. 이후 사람 군집·음성 대응·클립 구성은 별도 인물 정책. [frame_inference.py:8](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/frame_inference.py:8), [app.py:178](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/app.py:178). |
| 대사 시각 | OpenCLIP `ViT-B-32/laion2b_s34b_b79k`, 현재 PyTorch/safetensors 경로. 키프레임을 BGR→PIL→preprocess→tensor batch→`.to(device)`→`encode_image`→L2/shot 평균. **제품에서는 ONNX가 아니다.** [common.py:101](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/common.py:101), [embedding_pipeline.py:55](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/embedding_pipeline.py:55), [staged_artifacts.py:119](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:119). | torch CUDA→MPS→CPU. 키프레임 decode, 색 변환, PIL/preprocess, tensor upload, shot mean, 비교·구간화는 모델 추론과 별도. |
| 음성/기타 | 인물·대사는 공유 faster-whisper/CTranslate2 `small`; CUDA float16 실패 시 CPU int8, MPS 요청은 CPU. 대사 EasyOCR는 기본 off이고 CUDA 외 실행하지 않는다. [speech model.py:34](/Users/jina/project/adlight/desktop/clipper_python/clipper_speech_core/clipper_speech_core/model.py:34), [staged_artifacts.py:100](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:100). | 팀원 `clip_visual` 성공은 STT·scene detect·audio feature·export 가속 증거가 아니다. 안무 SAM/mask/joint heavy 검증은 현재 `disabled_runtime_cost_v1` OFF이며 CPU로 남은 가벼운 body 비교와 구분한다. |

정확한 ONNX 모델 원본과 hash는 [Dance face_models.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_models.py), [공통 face_models.py](/Users/jina/project/adlight/desktop/clipper_python/clipper_face_core/clipper_face_core/face_models.py), [Person model_assets.py:15](/Users/jina/project/adlight/desktop/clipper_python/plugins/person_highlight/person_highlight/model_assets.py:15)에 고정돼 있다. 현재 안무만 [pyproject.toml:11](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/pyproject.toml:11)에서 Windows `onnxruntime-directml==1.24.4`, 기타 OS `onnxruntime==1.31.0`을 배타 marker로 설치한다. Person은 CPU ORT 1.31.0, Dialog에는 OpenCLIP·speech core가 있다. Windows ML 1.30.0 시험 wheel을 제품이 설치한다는 근거는 없다.

## 설치·장치 선택·설정의 경계

Electron은 OS GPU/driver/VRAM을 관측하지만 그 결과로 모델 EP나 wheel을 고르지 않는다. 패키징 앱은 플러그인별 venv에 `uv sync --frozen --no-dev --no-editable`을 실행하고 Python으로 플러그인을 시작한다. [plugin-venv.ts:53](/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-venv.ts:53), [plugin-process.ts:165](/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-process.ts:165). CUDA/DirectX 드라이버 자동 설치, DML GPU index와 OS 목록 연계, 사용자별 EP 우선순위/강제 CPU 설정은 없다. DirectML 기본 어댑터가 최적 GPU라는 보장도 없다. 개발 `uv run`의 공용 환경과 패키징의 플러그인별 exact sync는 구분해야 한다. CPU ORT와 DML wheel을 같은 venv에 덧설치하면 충돌 위험이 있어 현행 배타 marker가 중요하다. 상세 횡단 감사: [2026-11-02 앱 GPU 아키텍처](/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/02-app-gpu-architecture-audit.md).

SDK `/runtime/accelerators`는 torch·ORT·CTranslate2 probe와 플러그인별 `selected`를 Nest/Angular에 전달한다. ORT `get_available_providers`나 session `get_providers`는 등록 가능성이지 모든 노드의 GPU 배정 증거가 아니다. Angular 대시보드는 DML label이 없고 모델별 `selected.models`를 아직 표시하지 않는다. [SDK base.py:398](/Users/jina/project/adlight/desktop/clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py:398), [dashboard.component.ts:645](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/dashboard/dashboard.component.ts:645). 안무의 미커밋 `app.py`는 YOLO/얼굴 모델별 provider와 fallback 통계를 응답한다. [dance app.py:69](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/app.py:69).

## 팀원 Windows 부분 로그의 해석

첫 배치 안내는 “Clipper GPU 시험을 시작합니다. 15~30분 걸릴 수 있어요. 창을 닫지 마세요.”였고, 첫 결과 폴더는 `results/directml20261103-053501`로 보인다. 하드웨어/드라이버/입력 해상도/반복 횟수/전체 JSON은 전달되지 않았다.

| [1/3] ORT 1.24.4 | CPU | 명시 DML:0 | `auto:PREFER_GPU` | 확인 범위 |
|---|---:|---:|---:|---|
| yolo_pose (안무·인물) | 89.9 ms/장, 첫 97 | 12.9 ms, 첫 137, 6.94배 | 10.8 ms, 첫 19, 8.32배 | `same_people_dance/person=24/24`, `matched_box_iou_min=1.0` 보고. 24개 프레임의 box/인원 근거이며 키포인트·confidence·NMS 경계/클립 최종 동등성은 아직 모름. |
| YuNet | 4.7 ms, 첫 7 | 2.5 ms, 첫 9, 1.91배 | 2.5 ms, 첫 8, 1.88배 | 얼굴 수 24/24, score 최대차 .0003. 랜드마크·identity 문턱의 최종 판정 대조 필요. |
| AuraFace | 56.5 ms, 첫 59 | 실패 | 실패 | `/features/BatchNormalization`의 DML `MLOperatorAuthorImpl.cpp(2853)`, HRESULT `80070057`. CPU 성공이므로 모델 포맷 전체 불가라고 할 수 없음. |
| clip_visual (대사) | 31.9 ms, 첫 37 | 14.5 ms, 첫 383, 2.2배 | 13 ms, 첫 73, 2.45배 | `cosine_min=1.0` 보고. 개별 임베딩 비교로 보이며 shot 평균·장면 경계·최종 컷 동등성은 아님. |

`[2/3]` Windows ML ORT 1.30.0에서도 실행기 이름은 `DmlExecutionProvider:0`/`auto:PREFER_GPU`였고 AuraFace의 같은 BatchNormalization 지점이 `MLOperatorAuthorImpl.cpp(2936)`, HRESULT `80070057`로 실패했다. `Init provider bridge failed`와 `ep.dmlexecutionprovider.device_id=0` 중복 설정 경고가 있었으며 clip_visual까지 진행 중인 부분만 관측됐다. `[2/3]` 최종 수치와 `[3/3]` 결과는 없다. Windows ML과 standalone DML의 ORT 버전·provider 구성 차이를 통제한 비교가 아니다. 특히 `auto`가 실제 어느 EP/장치를 골랐는지, 모델 중 CPU partition이 있는지 로그 문자열만으로 확정할 수 없다.

### 오류 원인: 확인과 추론

1. 확정: 해당 모델/입력/PC의 DML 노드 실행이 `BatchNormalization`에서 `80070057`로 실패했고 두 시험에서 재현됐다. `0x80070057`은 invalid argument 계열이다. CPU 성공, 다른 모델 DML 성공과 양립한다. **가능성**은 해당 op/shape/attribute/정밀도와 DML kernel·driver의 호환, 그래프 변환·버전/장치 문제다. 키트/ONNX graph/driver/원본 ORT stack 없이 한 원인으로 좁힐 수 없다.
2. 표면 `UnicodeDecodeError('utf-8', b'[ONNXRuntimeError] :6:RUNTIME_EXCEPTION...')`는 DML 계산 실패 자체가 아니라 예외 메시지 bytes를 UTF-8로 해석하는 별도 경로의 2차 오류로 보인다. 정확한 위치와 Windows locale/codepage/서브프로세스 처리 여부는 `run_kit.py` traceback 없이는 확정 불가. raw stderr bytes/hex를 보존하고 `errors='replace'`로 표시하되 본래 ORT 예외·stack을 가리지 않아야 한다.
3. `Init provider bridge failed`는 provider bridge 초기화 경고다. 같은 모델의 DML 오류가 직접 이 경고 때문에 생겼는지는 증거가 없다. 선택된 EP 목록과 각 노드 배정·별도 provider load 오류를 확인해야 한다. `ep.dmlexecutionprovider.device_id=0` 중복 경고는 동일 옵션을 두 번 전달한 구성 문제 가능성이 있으나 키트 코드가 없어 발생 위치를 특정할 수 없다. 경고를 무시하고 `auto`가 다른 GPU를 골랐다고 해석하면 안 된다.

공식 [ORT DirectML 요구사항/제약](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)은 DX12 GPU·지원 드라이버, memory pattern off, sequential mode, 동일 session 동시 `Run` 금지를 명시한다. [Windows ML EP 선택 문서](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/select-execution-providers)는 명시 장치 선택과 정책 선택을 구분하고, [Windows ML 버전표](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/onnx-versions)는 1.30.0을 RC/experimental 경로에도 연결한다. 이 문서들은 이번 PC 오류의 원인 확정 근거는 아니다.

## ONNX 변환과 실행기 전환은 다른 작업

- ONNX **export**는 PyTorch `.pt`/OpenCLIP 가중치+연산을 `.onnx` graph로 직렬화하는 일이다. YOLO pose와 대사 OpenCLIP은 제품에서 아직 이 작업이 필요하다. `opset`, 입력 shape/동적 축, batch, FP32/FP16, 전처리, 좌표/키포인트 decode, confidence/NMS, feature L2 정규화의 계약을 함께 고정해야 한다. [Ultralytics export 옵션](https://docs.ultralytics.com/modes/export), [PyTorch ONNX 문서](https://docs.pytorch.org/docs/stable/onnx).
- YuNet·AuraFace·SFace는 **이미 ONNX**다. 이 셋의 GPU화는 주로 ORT/OpenCV DNN 실행기, EP, shape metadata와 입력·출력 adapter를 바꾸는 일이다. 같은 ONNX 파일도 EP가 일부 노드를 CPU에 배정하거나 아예 실패할 수 있다. 안무 YuNet/SFace는 파생 graph metadata를 정리해 사용하며 원본 가중치·연산 노드는 보존한다. 그럼에도 정밀도·NMS·문턱 부근 결과는 검증해야 한다.
- Windows ML은 ONNX라는 별도 모델 포맷이 아니라 Windows 제공 ORT/EP 배포·선택 계층이다. 신규 Python Windows ML 의존성/OS 조건/패키지 배포를 검증해야 하며 기존 앱이 자동으로 Windows ML을 쓰는 것은 아니다. [Microsoft 배포 가이드](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/distributing-your-app), [EP 구성](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/supported-execution-providers). `Windows ML Runtime API` 자체는 현재 Microsoft 문서상 experimental이므로 이 API와 Windows ML에 포함된 안정 ORT 사용을 혼동하지 않는다. [Runtime API 개요](https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/runtime/overview).

키트 코드를 받으면 먼저 `run_kit.py`와 배치의 package install, 모델 SHA, export 명령, opset/shape/batch/precision, preprocess/postprocess/NMS, EP options, CPU fallback, raw exception handling, 측정 warmup/동기화/반복, 결과 JSON을 리뷰해야 한다. 지금은 특정 구현 버그를 지적할 근거가 없다.

## 도입 권고와 예상 속도의 상한

**최소 통합 경계:** 안무/인물 body detector는 동일 `frame BGR → body/pose observations` 계약에서 PyTorch/ONNX backend를 선택하게 하고, 대사는 `preprocessed keyframes → 정규화된 visual embeddings` encoder만 교체한다. 이미 ONNX인 얼굴은 기존 `clipper_face_core`의 정렬·전처리·모델 hash/출력 계약과 안무 `session_factory`/OpenCV CPU fallback을 유지한다. 기존 인물의 얼굴·화자 결합, 안무의 정체성/역할/구간 조립, 대사의 shot/STT/audio/clip 구성은 후속 단계로 병행 가능하다. shared/person 기본값을 바꿔 일괄 배포하지 않는다. 사용자 지시대로 `단체 조건 탈락→개인 메인` 판정 변경은 보류한다.

모델별 adapter 선택은 `auto/CPU/검증된 EP` 정도의 명시적 사용자·진단 계약을 갖추되, 지원하지 않는 조합은 CPU로 복귀하고 실제 선택 EP·adapter index·fallback 원인·모델 hash를 기록해야 한다. Windows DML AuraFace 실패는 제품에서 이미 CPU fallback할 가능성이 높지만, 해당 PC에서 기존 앱 결과와 동등한지 실제 설치본으로 확인해야 한다. OpenCLIP ONNX 결과를 제품에 넣을 때는 model graph만이 아니라 RGB resize/crop/mean/std, L2, shot 평균과 최종 구간까지 비교한다.

단일 추론의 `6.94–8.32배`는 전체 앱 배율이 아니다. 다른 비용이 고정일 때 Amdahl 상한 `전체배율=1/(1-p+p/s)`에서 YOLO가 전체 실행 시간의 `p`를 차지하고 그 단계만 `s=8.32`배가 되면:

| 가정한 YOLO 시간 비중 | 전체 이론상한 | 전체 시간 감소 |
|---:|---:|---:|
| 10% | 1.095배 | 8.8% |
| 25% | 1.282배 | 22.0% |
| 50% | 1.785배 | 44.0% |

이는 모델 load/export cache, 첫 실행, frame decode, resize/upload/download, CPU NMS·ROI·얼굴·이름·장면·clip, GPU 간 경합이 **추가되지 않는 이상적인 상한**이다. 실제 stage 비중은 기기/영상/모델에 따라 다르다. 이미 Mac에서 안무 YuNet/SFace GPU화를 앱 세 영상에 적용했을 때 모델 추론은 빨라졌지만 전체는 1673.480→1597.736초, **4.5% 단축**에 그쳤다. 이어 CPU 병렬·정확 재사용·prefetch·원본 읽기 개선은 별도 앱 비교 1597.736→1219초 안팎으로 단축했으나 조건별 한 번 측정이며 품질 수정도 일부 포함됐다. [YuNet/SFace GPU 실측](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-yunet-sface-gpu-results.md), [내부 병목/앱 비교](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-deep-profile-results.md). 최신 연속성 빌드 세 영상은 `MMN 1793649506337`, `ANT 1793649573540`, `NEON 1793649654322`, 합계 **1326.930초**로 직전1207.958초보다 느렸다. [최신 앱 기록](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/03-role-continuity-app-results.md). 서로 다른 시점·코드/조건의 숫자를 하나의 누적 속도 개선으로 합산하지 않는다.

현재 Dance 성능 조치의 범위: `face_runtime.py`의 OpenCV CPU 병렬 설정, 정확 bytes hash 검출/embedding 캐시; `opencv_acceleration.py`의 안무 전용 CoreML/DML; 전체 프레임 source 재사용과 ROI prefetch; 동일 갤러리 fingerprint/포즈 대응/장면 확인의 재계산 축소. [main-face 계획](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-main-face-performance-plan.md), [deep profile](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-deep-profile-results.md). CPU ROI 검출, 원본 decode, 96MiB frame cache, `cv2` copy/warp/해시, Python NMS는 여전히 비용이다. `gpu_seconds`와 stage wall time을 별도로 보고해야 한다. heavy SAM/mask/joint는 `disabled_runtime_cost_v1` OFF이며, 꺼서 바뀐 미확인/클립 품질도 기록됐다. [mask 비용 결과](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-mask-cost-reduction-results.md).

## 남은 검증 순서

1. 키트 배치/`run_kit.py`/모델 export 산출물·SHA/전체 `results` JSON·raw traceback, PC CPU/GPU/driver/Windows build/DX feature level, ORT/Windows ML distribution과 각 session의 실제 EP/노드 배정을 확보한다. 원격 브랜치나 사용자 Mac에 있다고 추정하지 않는다.
2. AuraFace graph의 실패 node 입력 shape·dtype/epsilon/attribute, DML adapter/driver, CPU 및 다른 EP를 같은 입력에서 분리 재현한다. ORT profiling/verbose log로 노드 배정 확인. Windows ML provider bridge 및 중복 device_id 설정은 각각 원 로그/코드로 추적한다.
3. YOLO export의 원본 `.pt` 대비 24개보다 넓은 실제 영상: 빈 장면·다중 인물·작은/가려진 몸·키포인트·NMS/신뢰도 문턱, 인물/안무 최종 clip까지 비교한다. YuNet 랜드마크/AuraFace·SFace cosine 및 이름 문턱, CLIP shot 변화·최종 대사 구간도 포함한다.
4. 빈 캐시 첫 설치·첫 호출과 warm 반복을 분리하고 stage별 decode/preprocess/upload/inference/download/postprocess 및 앱 started→completed 시간을 동일 입력에서 반복 측정한다. 여러 GPU/driver, Windows CPU-only와 Mac MPS/CoreML을 별도 표로 보고한다. 실제 앱 venv 업그레이드, fallback/동시 호출, 한글 사용자 경로도 확인한다.

이번 조사는 코드/문서/사용자 부분 로그만으로 완료했다. Windows 물리 기기·키트·대규모 모델은 실행하지 않았다.
