# Clipper 하이라이트 자동 가속 — 직접 빌드·시험 안내

지원 범위는 Apple Silicon Mac과 Windows x64입니다. Intel Mac과 Windows ARM은 이번 범위에 포함하지 않습니다. 기존 모델 가중치·사람 판정·얼굴 정렬·샘플링·하이라이트 임계값·Whisper small/beam 5를 유지합니다.

## 이 Mac에서 바로 시험

새로 만든 미서명 테스트 앱:

`/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103/dist-app/Clipper Studio (dev)-0.0.1-arm64.dmg`

기존 설치본·실행 중 앱을 자동으로 교체하거나 종료하지 않았습니다. 생성한 앱은 개발 빌드이며 기존 계정·서비스 연결 설정을 사용합니다. 이번 가속 변경은 원본 desktop 폴더가 아닌 아래 네 작업 트리에 있습니다.

| 구성 | 경로 |
|---|---|
| Electron | `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103` |
| Angular | `/Users/jina/project/adlight/.worktrees/clipper-angular-accelerators-20261103` |
| NestJS | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` |
| Python | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` |

Mac 재빌드:

```sh
cd /Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103
CI=1 PATH=/Users/jina/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH npm run build:app:mac:arm64
```

기본 셸의 Node 24.3은 현재 Angular 요구사항보다 낮습니다. 위에 설치된 Node 24.19를 사용해 실제 빌드했습니다. 다른 컴퓨터에서도 Node 24.19 이상인 24 LTS를 사용하세요.

## Windows로 소스 옮겨 빌드

`clipper-acceleration-source.zip`을 새 폴더에 풉니다. 기존 Windows 작업 폴더에 덮어쓰지 마세요. 압축에는 네 프로젝트의 현재 소스와 lock 파일, 공개 인증키, 공개 배포 설정을 담습니다. 모델 캐시·가상환경·node_modules·로그·개인 .env·Git 저장소는 제외합니다. `source-manifest.json`으로 파일별 SHA-256을 확인할 수 있습니다.

압축을 푼 폴더에서 PowerShell:

```powershell
node --version
cd desktop/clipper_angular
npm ci
cd ../clipper_nestjs
npm ci
cd ../clipper_electron
npm ci
npm run fetch-uv
npm run build:app:win:x64
```

Node 24.19 이상인 24 LTS, 인터넷 연결, Windows x64 환경이 필요합니다. 출력은 `desktop/clipper_electron/dist-app`입니다. 배포 설정과 공개키가 필요한 기존 빌드 절차는 유지합니다. 실제 Windows 빌드는 해당 Windows에서 확인해야 합니다.

## 앱에서 시험 순서

1. **설정 → 분석 가속**에서 안무·인물·대사 각각 `자동`을 선택합니다. `CPU 사용`을 선택한 플러그인은 CPU로 분석하고 유휴 검사를 보류합니다. 설정은 다음 분석부터 적용됩니다.
2. **추가 실행기 준비**를 누릅니다. Apple Silicon은 Core ML, Windows x64는 DirectML을 별도 환경에 준비합니다. Windows에서 실제 사용 가능한 NVIDIA CUDA 장치를 감지하면 **Windows NVIDIA CUDA 실행기 준비**도 표시됩니다. 이 버튼은 대용량 NVIDIA 패키지를 별도로 내려받으며, 준비한 DirectML도 계속 비교 대상에 남습니다. 화면을 열자마자 기기 탐색이 끝나지 않았다면 잠시 뒤 새로고침하세요.
3. 각 플러그인의 **이 기기 시험**을 누른 뒤 평소와 같은 영상으로 새 분석을 실행합니다. 그 분석 한 번에만 실제 후보와 원래 CPU 전체 분석을 비교합니다. 평소보다 오래 걸립니다. 작업 전체의 품질 비교와 결과 저장이 성공한 자료만 유휴 검사에 전달됩니다. 취소·실패한 분석은 합격 자료가 되지 않습니다.
4. 분석이 끝나면 앱을 켜둔 채 분석 작업을 쉬게 둡니다. 약 15초 간격으로 유휴 여부를 확인하고, 수집한 입력으로 준비된 실행기와 실제 GPU별 후보를 순서대로 비교합니다. 회차당 최대 120초, 후보 최대 2개를 검사하고 남은 순서를 저장합니다. 표본이 많거나 실행기가 여러 개면 여러 회차가 필요합니다. 사용자가 새 분석을 시작하면 검사를 중단하고 하위 프로세스 종료를 확인한 뒤 분석합니다.
5. **실행 기록 새로고침**으로 유휴 검사의 예약·진행·보류·완료와 남은 후보 수, 실제 분석의 모델별 경로·측정시간·CPU 재분석 여부를 확인합니다. **유휴 검사 다시 예약**은 이미 모은 자료로 다시 비교합니다. 새로운 영상 시험을 예약하는 버튼과 용도가 다릅니다. 표본 부족·실행기 미준비·저장 한도·품질 불일치·종료 확인 실패는 완료로 표시하지 않습니다.
6. 동일 영상·옵션으로 `CPU 사용` 분석도 실행해 인물 ID, 등장 구간, 안무 컷, 자막 내용·타이밍과 대사 클립 선택을 비교합니다. 해상도·길이·인원수·얼굴 크기·언어가 다른 실제 영상도 시험하세요. LLM 결과에는 별도의 변동 요인이 있습니다. 첫 실행의 모델 로드·컴파일 시간과 반복 실행 시간은 나눠 기록합니다.

시각 교정에는 프로필마다 서로 다른 원래 입력 24개가 필요합니다. 같은 프레임 반복으로 채우지 않습니다. 음성 교정에는 서로 다른 **30초 이하의 완전한 음성 입력 3종과 원래 CPU 전사**가 필요하므로 대사 시험을 서로 다른 짧은 영상으로 반복하세요. 긴 음성을 잘라 조건을 맞추거나 beam 값을 낮추지 않습니다. 필요한 자료가 없으면 기존 Whisper 경로로 분석하고 유휴 비교는 보류합니다.

기기 시험에서 선택한 입력·원래 CPU 출력은 이 PC의 앱 데이터에만 보관합니다. 한 프로필 128 MiB, 플러그인당 512 MiB, 프로필 최대 8개로 제한하며 업로드·소스 ZIP·앱 배포물에 넣지 않습니다. 공간이 부족하면 표본 수나 정밀도를 낮추지 않고 보류합니다. 사용 중인 자료를 지우지 않으며 폐기된 빌드 자료와 소유 프로세스 종료가 확인된 미완성 자료만 정리합니다. 배포용 허가된 검사 자료의 한도는 별도로 25 MiB입니다.

`CPU 재분석`은 파일을 되살린다는 뜻이 아닙니다. GPU 실행에 실패한 분석 작업을 새 프로세스에서 CPU로 처음부터 한 번 다시 수행하고, 완성된 결과만 새 revision으로 공개한다는 뜻입니다. 기존에 완료된 결과는 실패한 중간 결과로 덮지 않습니다. 취소·입력 오류·CPU 자체 실패는 GPU 고장으로 바꾸지 않습니다.

## 모델별 현재 실행 방식

| 모델 | 기존 경로 및 후보 | 품질 보존 |
|---|---|---|
| YOLO Pose | 기존 PyTorch CPU/MPS/CUDA + ONNX CPU/DirectML/Core ML/CUDA 후보 | 원래 Ultralytics 전처리·NMS·키포인트 처리; 기존 GPU 경로가 선택되면 원래 결과 객체를 그대로 사용 |
| YuNet | OpenCV CPU 및 기존 GPU + ONNX 후보 | 기존 패딩·디코더·NMS; 작은 얼굴 crop은 기존 경로 유지 |
| AuraFace | 기존 ONNX CPU/GPU + 별도 ONNX 후보 | 원래 얼굴 정렬·입력·임베딩; BatchNorm 상수화는 기존 가중치 보존 |
| SFace | OpenCV CPU + ONNX 후보 | 원래 alignCrop·RGB·스케일 1·112 입력 보존 |
| CLIP ViT-B32 | 기존 OpenCLIP CPU/MPS/CUDA + FP32 ONNX 후보 | 현재 가중치 SHA·원래 이미지 변환·정규화·배치 순서·샷 집계 보존 |
| Whisper small | 기존 faster-whisper/CTranslate2 CPU int8 또는 NVIDIA CUDA FP16 | beam 5·VAD off·word timestamps·기존 chunking 유지 |

Mac Whisper는 현재 CPU를 사용합니다. MLX Whisper의 beam search가 지원되지 않아 기존 beam 5와 같은 조건으로 대체할 수 없기 때문입니다. 이 빌드는 속도를 위해 greedy decoding이나 작은 모델로 바꾸지 않습니다. 이 빌드에서는 품질 계약을 유지하는 CPU 경로를 사용합니다.

Core ML은 CPU와 GPU를 함께 허용하는 실행기입니다. 실행 기록의 Core ML partition은 해당 실행기에서 연산한 증거이며 모든 연산이 물리 GPU에서 수행됐다는 증거는 아닙니다. Windows DirectML의 기기 인덱스는 DXGI의 실제 어댑터 ID와 대응시키며, CUDA가 없거나 실행에 필요한 라이브러리를 쓸 수 없으면 CPU 경로를 사용합니다.

## 자동 선택과 시험 결과의 의미

기존 MPS/CUDA 가속은 유지합니다. 새 ONNX 후보는 모델·가중치·전처리·입력 shape·배치·정밀도·플러그인·OS·GPU·드라이버·실행기 버전이 맞는 품질 승인 범위와 로컬 검사를 모두 통과해야 자동 선택됩니다. 워밍업/모델 로드 비용과 p90을 포함해 기존 실행 방식보다 실질적으로 빨라야 합니다. 분석 도중 임베딩 경로를 임의로 섞지 않습니다.

2026-11-03 최종 독립 감사 수정에 이어 유휴 교정·다중 실행기 순환·다중 GPU 비교를 연결하고, 추가 독립 검토의 종료 확인·얼굴 사전검사·자료 재사용·보관 한도 결함을 수정한 빌드입니다. 부팅 때는 준비된 추가 실행기 상태만 확인하며, 추가 패키지는 준비 버튼으로 설치합니다.

이 테스트 빌드에는 여러 Windows GPU와 실제 하이라이트 영상으로 승인된 release catalog를 아직 넣지 않았습니다. 따라서 **이 기기 시험에서는 실제 새 GPU 후보를 실행할 수 있고, 일반 자동 모드에서는 승인되지 않은 후보 대신 기존 실행 방식을 사용합니다.** 로컬 시험 하나를 모든 PC의 품질 승인으로 바꾸지 않습니다. 시험 로그·결과를 모아 승인 범위를 채울 수 있는 상태입니다. 모든 GPU에서 가장 빠르다는 보장은 현재 시험만으로 할 수 없습니다.

Windows 다중 GPU 환경에서는 실제로 선택된 `adapter_id / adapter_index`를 결과에서 확인하세요. 준비된 호환 실행기마다 실제 장치 대응표에 있는 GPU를 순환합니다. 기존 PyTorch CPU/MPS/CUDA와 CTranslate2 CPU/CUDA도 설치된 플러그인 환경을 사용해 비교하며, NVIDIA ONNX CUDA는 별도로 준비한 경우 포함합니다. TensorRT·OpenVINO·MLX 등 모든 실행기를 자동 설치하는 기능은 아닙니다.

일반 자동 분석은 시작 전에 벤치마크를 돌리지 않습니다. 유휴 시간에 완결한 측정과 실제 분석의 기존 경로 비용을 읽고, 모델 로드·컴파일 비용과 p90을 포함해 이득이 확인된 선택을 다음 분석 단위에 고정합니다. 근거가 부족하면 기존 경로를 유지합니다. 드라이버·전원 모드·모델·전처리·빌드·실행기 버전이 바뀌면 이전 측정은 선택에 사용하지 않습니다. 저장된 입력 자체는 무결성 검사를 거쳐 재사용하고 현재 환경에서 다시 측정합니다.

유휴 비교의 상세 자료는 앱 `userData/accelerators/idle/플러그인명/` 아래 `status.json`, `rotation.json`, `measurements/*.json`, `attempts/*.json`에 있습니다. macOS 기본 경로는 `~/Library/Application Support/앱이름/accelerators`, Windows는 `%APPDATA%/앱이름/accelerators`이며 개발/제품 앱 이름에 따라 폴더가 다릅니다. 화면에는 상태·후보 수, 파일에는 후보별 측정과 실패/보류 이유를 남깁니다. 과거 완결 측정은 후속 취소·실패로 덮지 않습니다. 측정 파일을 손으로 수정해 승인 상태를 만들지 마세요.

현재 선택 실행기 Core ML용 ONNX Runtime 1.31 추가 패키지는 macOS 14 이상이 필요합니다. 패키지를 준비할 수 없는 OS에서는 기존 CPU/MPS 경로를 유지합니다. 이는 추가 패키지의 조건이며 앱 전체의 기존 OS 지원 범위를 바꾸지 않습니다.

## CLI로 증거 남기기

Python 작업공간에서 `uv sync --locked`로 해당 컴퓨터의 환경을 준비한 뒤:

```sh
uv run --locked python -m scripts.accelerators.run_analysis_test --plugin person_highlight --video VIDEO.mp4 --output OUT_CPU --cpu --result cpu-result.json
uv run --locked python -m scripts.accelerators.run_analysis_test --plugin person_highlight --video VIDEO.mp4 --output OUT_TEST --verify --accelerator-home ACCELERATOR_HOME --result gpu-result.json
```

플러그인 이름은 `dance_highlight`, `person_highlight`, `dialog_highlight`입니다. 대사 CLI는 과금/LLM 생성 이전의 analyze_media 단계를 실행합니다. 앱 전체 클립·렌더 결과는 앱에서 확인합니다. CLI의 개발용 명시적 시험과 앱의 일회용 시험 권한은 구분됩니다.

`benchmark_app.py`는 corpus/matrix와 **schema 2 동결 원본 baseline**을 받아 CPU/시험 순서를 번갈아 최소 3회 실행합니다. 파일 이름만 baseline으로 주면 합격하지 않습니다. 원래 소스의 파일 집합과 SHA, corpus/영상 SHA, 옵션, 보관한 원래 분석 JSON과 SHA, 원래 전체 분석 3회 시간을 실제로 확인합니다. 기존 schema 1 소스 출처 기록은 이 합격 근거를 대신하지 못합니다.

```sh
uv run --locked python -m scripts.accelerators.benchmark_app --help
uv run --locked python -m scripts.accelerators.benchmark_app --matrix matrix.json --corpus corpus.json --baseline frozen-original.json --candidate ACCELERATOR_HOME --out BENCHMARK_OUT
```

matrix의 `required_profiles`에는 필수 model_id/consumer/backend/전처리/purpose/실제 입력 shape를 지정합니다. 각 영상이 실제 사용해야 하는 모델만 case별로 지정하되 필수 모델을 누락하면 범위 충족으로 인정하지 않습니다. 시각 모델은 프로필/round마다 최소 33회 측정과 서로 다른 입력 24개가 필요합니다. Whisper는 시각 입력 규칙 대신 beam 5/VAD off/word timestamps/chunking 식별자, 서로 다른 PCM 3종과 저장 전사 3종, 각 3 round의 실제 CPU/CUDA 비교를 확인합니다. Mac Whisper CPU 유지를 GPU 합격으로 표시할 수 없습니다.

기본 `require_gpu=true`는 물리 GPU 실행 근거를 요구합니다. Core ML EP 자체를 시험할 때는 `require_gpu=false`, `require_accelerator=true`로 설정합니다. Core ML partition은 물리 GPU 전용 실행의 증거가 아니기 때문입니다. 현재 코드가 기록한 `profile/preprocessing/purpose/consumer`와 맞춰야 하며 예시의 shape를 모든 영상에 그대로 적용하면 안 됩니다.

전체 시간 5% 초과 회귀, 미실행 모델, 불충분한 표본, 후보 결과 불일치, 동결 자료 누락/변조는 PASS가 되지 않습니다. 없는 장비/영상/원래 출력은 BLOCKED로 남습니다. 이 명령은 `release_status=BLOCKED`를 유지하며 출하 인증서를 만들지 않습니다. 대사 비교 범위는 분석 JSON/STT/CLIP까지이며 이후 LLM/렌더는 앱에서 별도 확인합니다.

유휴 교정과 준비된 호환 GPU·실행기의 순환 비교는 이번 빌드에 구현했습니다. 최신 독립 재검증 수정·회귀 증거와 실기기 검증 범위는 `REAUDIT-REMEDIATION.ko.md`를 확인하세요. `IDLE-ROTATION-IMPLEMENTATION.ko.md`는 최초 유휴 교정 단계의 기록입니다. `IMPLEMENTATION-REPORT.ko.md`와 `AUDIT-REMEDIATION.ko.md`는 그 이전 단계의 기록입니다.

## 독립 재검증 추가 수정 사항

YOLO native GPU는 FP16·FP32를 별도로 교정합니다. CPU FP32로 원래 FP16 GPU의 속도를 대신 판단하지 않습니다. 같은 정밀도의 유효한 비교가 없거나 품질이 맞지 않으면 기존 경로를 유지합니다. 승인된 다른 native GPU가 이기는 경우 다음 분석의 실제 YOLO/CLIP 작업자가 그 장치에서 실행됩니다. 설정 저장 중 종료 확인 오류가 생겨도 실제 저장된 CPU 설정을 다시 표시하며, 종료 확인 차단은 유지합니다.

기본 benchmark CLI의 --verify가 새 native 자동 경로까지 전체 인수했다고 해석하지 마세요. native 프로필은 실제 장치·정밀도·source/weights·runtime scope와 충분한 비교 표본이 있는 기록만 검사할 수 있고, 맞는 실제 비교 증거가 없으면 BLOCKED입니다. 평소 자동 분석의 실행 횟수만으로 비교 완료를 만들지 않습니다. native 유휴 측정과 전체 영상의 하이라이트 품질 비교를 함께 확인하세요.

전달 파일을 확인할 때는 최신 `mac-artifacts.json`, `handoff/source-current-check.json`, `handoff/sha256.json`의 같은 build_id와 실제 SHA를 사용하세요. 이전 버전의 파일 수·SHA는 새 시험 앱의 확인 근거가 아닙니다.
