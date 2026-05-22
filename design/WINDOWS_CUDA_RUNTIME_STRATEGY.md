# Windows CUDA Runtime Strategy

작성일: 2026-04-29

## 결론

Windows CUDA 지원은 "앱이 CUDA 전체를 조용히 번들한다"가 아니라 다음 3단계로 나눈다.

1. CPU fallback을 항상 유지한다.
2. NVIDIA GPU와 driver/runtime 가용성을 telemetry로 감지한다.
3. CUDA 가속은 provider별 준비 상태가 확인된 경우에만 opt-in 또는 자동 선택한다.

초기 제품 안정성 기준에서는 CUDA 부재를 plugin start 실패로 보지 않는다. GPU-required workflow가 생길 때만 hard admission 대상으로 승격한다.

## 현재 Python 의존성 관찰

`clipper_python` workspace:

- `pyproject.toml`의 `tool.uv.environments`는 현재 `darwin`, `linux`만 명시되어 있다.
- Windows packaging을 정식 지원하려면 uv environment/lock 전략을 별도로 다뤄야 한다.

`dance_highlight`:

- `ultralytics`
- `onnxruntime>=1.19`
- `insightface`
- `opencv-python`
- runtime device:
  - Apple Silicon: YOLO는 `mps` 사용 가능
  - NVIDIA: torch CUDA 가능 시 CUDA 사용 가능
  - InsightFace/onnxruntime provider는 CUDA provider가 없으면 CPU provider로 fallback

`dialog_highlight`:

- `faster-whisper`
- `open-clip-torch`
- `scenedetect[opencv]`
- runtime device:
  - torch CUDA 가능 시 `cuda`
  - Apple Silicon `mps` 가능 시 CLIP은 mps, faster-whisper STT는 cpu fallback
  - OCR path 일부는 CUDA일 때만 활성화됨

## Windows CUDA 리스크

### torch CUDA

`ultralytics`와 `open-clip-torch`는 torch에 의존한다. Windows에서 CUDA를 쓰려면 torch wheel 자체가 CUDA runtime과 맞아야 한다.

위험:

- CPU torch wheel이 설치되면 `torch.cuda.is_available()`은 false다.
- CUDA torch wheel은 용량이 크고 Python/CUDA build matrix를 탄다.
- Electron packaged app의 venv 생성 시간이 길어질 수 있다.

초기 전략:

- 기본 bundled/runtime venv는 CPU-compatible dependency set으로 둔다.
- Windows CUDA 가속은 별도 install profile로 분리한다.
- profile 전환은 Electron native/download 책임 또는 NestJS facade에서 명시적으로 관리한다.

### onnxruntime vs onnxruntime-gpu

`dance_highlight`는 `onnxruntime`을 사용한다. NVIDIA CUDA provider를 쓰려면 일반적으로 `onnxruntime-gpu` 계열이 필요하다.

위험:

- `onnxruntime`과 `onnxruntime-gpu`를 동시에/무분별하게 설치하면 provider 충돌과 DLL path 문제가 생길 수 있다.
- 현재 macOS smoke test에서도 CUDA provider warning은 출력되지만 CPU provider fallback으로 동작한다.

초기 전략:

- CPU fallback을 기본으로 유지한다.
- Windows CUDA profile에서만 `onnxruntime-gpu`를 선택한다.
- provider list를 plugin startup telemetry로 노출하는 것을 다음 단계 후보로 둔다.

### faster-whisper

`dialog_highlight` STT는 `faster-whisper`를 사용한다.

위험:

- CUDA 사용 가능 여부는 ctranslate2/faster-whisper wheel과 driver/runtime에 좌우된다.
- CUDA 실패 시 현재 코드는 CPU int8 fallback 경로가 있다.

초기 전략:

- CUDA 실패를 start admission hard failure로 보지 않는다.
- job/runtime telemetry에 실제 사용 device를 기록하는 방향이 더 안전하다.

## Telemetry 기준

이미 구현된 1차 telemetry:

- `HostResourceSnapshot.accelerators.gpus`
- NVIDIA: `nvidia-smi` 기반 VRAM total/used/free/utilization
- macOS: `system_profiler` 기반 GPU identity/Metal 지원
- Windows fallback: PowerShell `Win32_VideoController` 기반 GPU identity/adapter RAM

Windows CUDA admission에 추가로 필요한 정보:

- `nvidia-smi` 실행 가능 여부
- driver version
- CUDA runtime/profile installed 여부
- torch CUDA availability
- onnxruntime provider list
- faster-whisper/cTranslate2 CUDA probe 결과

`nvidia-smi`는 host-level telemetry이고, torch/onnx/faster-whisper probe는 plugin Python environment-level telemetry다.

2026-04-29 현재 plugin Python environment-level telemetry의 1차 endpoint는 구현되어 있다.

- plugin direct: `GET /runtime/accelerators`
- NestJS facade: `GET /v1/plugins/:name/runtime-accelerators`
- 반환 정보:
  - selected runtime device/pipeline
  - torch installed/version/CUDA/MPS availability
  - onnxruntime available providers/CUDA/CoreML availability
  - cTranslate2 installed/version/CUDA device count
- 현재 계약은 running plugin에 대해서만 조회 가능하며, stopped 상태의 NestJS facade는 `409 Conflict`를 반환한다.

## 권장 구현 순서

1. Windows packaging target을 CPU fallback 기준으로 먼저 통과시킨다.
2. `GET /v1/resources`에 NVIDIA driver/VRAM telemetry가 들어오는지 Windows NVIDIA PC에서 확인한다.
3. Python plugin에 lightweight accelerator probe endpoint를 추가한다. 완료
   - 예: `GET /runtime/accelerators`
   - torch CUDA availability
   - onnxruntime available providers
   - faster-whisper/cTranslate2 CUDA probe 가능 여부
4. NestJS resource assessment가 host telemetry와 plugin probe를 결합한다.
5. CUDA install profile을 분리한다.
   - CPU/default profile
   - CUDA profile
6. CUDA-required workflow가 생길 때만 hard admission을 활성화한다.

## Admission Policy

현재 plugin들은 `requiresGpu: false`다. 따라서 다음 기준을 유지한다.

- RAM 부족: confirmation
- VRAM 부족: confirmation
- VRAM telemetry 없음: `requiresGpu: false`면 confirmation 강제하지 않음
- GPU required + GPU telemetry 없음: confirmation
- GPU required + CUDA profile/probe 실패: hard block 후보

hard block은 아직 켜지지 않았다. GPU/VRAM 추정치는 advisory에서 시작하고, Windows NVIDIA 실측이 쌓인 뒤 승격한다.

## 남은 결정

- Windows packaged app에서 Python venv를 CPU/CUDA profile로 어떻게 분리할지
- CUDA profile 설치를 Electron native/download flow로 둘지, NestJS facade로 감쌀지
- job/runtime telemetry에 actual device/provider를 어떤 표준 필드로 기록할지
- `requiresGpu: true` workflow가 등장했을 때 hard block을 어떤 HTTP contract로 표현할지
