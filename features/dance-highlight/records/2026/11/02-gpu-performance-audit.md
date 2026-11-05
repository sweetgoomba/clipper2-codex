# 안무 하이라이트 GPU 적용 상태와 성능 검증 — 2026-11-02

## 결론과 작업 범위

GPU는 포즈 검출(YOLO)에 이미 적용돼 있다. 그러나 주요 후속 단계인 얼굴 이름 인식(AuraFace)과 몸 연속성 검증(SAM2)은 CPU로 고정돼 있다. 따라서 앱이 `device=mps`라고 보고해도 전체 파이프라인 GPU 실행을 뜻하지 않는다.

이번에는 현재 코드·설치된 런타임·기존 앱 실행 로그를 감사하고, 실제 영상 입력을 사용한 독립 프로세스에서 CPU/GPU 비교 실험을 했다. 제품 코드, 앱 설정, 저장된 프로젝트, 기존 결과는 수정하지 않았다. 전체 영상 3편을 새로 실행한 결과가 아니다. 원본 Python 저장소는 `dev`, HEAD `4b54bced17e13aadbeb97be75259b7f7213a9b24`이며 작업 전후 clean이다.

AuraFace는 CoreML을 통해 실제 Apple GPU를 사용할 수 있었고, **프로파일링을 끈 재측정에서 추론 약 1.63배 향상**을 확인했다. SAM2는 MPS 실행은 가능하지만 출력 차이가 있어 그대로 전환하지 않았다. GPU 적용과 반복 검증량 축소를 함께 추진해야 한다.

## 현재 모델별 설정

| 단계 | 실제 설정 | 근거와 해석 |
|---|---|---|
| YOLO 포즈 검출 | MPS, half=True | 앱 로그 `[YOLO] device=mps half=True`; `services/config.py`, `services/pose_engine.py` |
| AuraFace 얼굴 특징 추출 | CPUExecutionProvider 고정 | `clipper_face_core/clipper_face_core/auraface.py:25`; 세 프로젝트의 `runtime.recognizer_providers`도 CPU |
| YuNet 얼굴 검출 | OpenCV DNN 기본 CPU | `clipper_face_core/clipper_face_core/opencv_backend.py`; CoreML 지원 여부와 별개로 현 검출 경로는 GPU 미설정 |
| SFace 보조 얼굴 인식 | OpenCV DNN 기본 CPU | `services/secondary_faces.py`; 별도 전환 검증 필요 |
| SAM2 몸 마스크 추적 | device='cpu' 고정 | `services/mask_tracker.py:128` |
| 영상 클립 생성 | 스트림 복사/VideoToolbox 지원 | 현재 주요 지연은 이 단계가 아님 |

위 `services/` 경로의 기준은 `/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/`이다. `/runtime/accelerators`의 `primary_device`는 YOLO 장치 기준이며 모델별 장치를 설명하지 못한다.

하드웨어/런타임: Apple M4, 메모리 24 GiB, macOS 27.0, Python 3.11, PyTorch 2.11.0, ONNX Runtime 1.31.0, Ultralytics 8.4.38. MPS available=true, CUDA=false. ONNX Runtime은 CoreMLExecutionProvider를 제공한다.

## 기존 실제 앱 실행의 시간 구성

2026-10-29 완료 로그와 저장된 진단 정보를 대조했다. 아래 전체 시간은 Python 파이프라인의 `TOTAL`이며 새 실행이나 다운로드부터 끝까지의 사용자 체감 시간 측정은 아니다.

| 영상 | 파이프라인 TOTAL | YOLO | cluster_map | SAM 검증 시도 수 | SAM 시도 누적 시간 |
|---|---:|---:|---:|---:|---:|
| Made My Night | 17분 38.4초 | 1분 28.4초 | 4분 21.4초 | 40 | 1분 25.5초 |
| ANTIFRAGILE | 24분 58.3초 | 1분 35.4초 | 8분 23.3초 | 86 | 4분 39.3초 |
| NEON | 44분 16.6초 | 1분 52.9초 | 25분 42.1초 | 146 | 21분 38.8초 |

`cluster_map`에는 단순 군집 처리 외에도 이름 타임라인, 보조 얼굴, 몸 연결, 마스크 추적, 재검증 등이 포함된다. SAM 누적 시간은 각 프로젝트 `diagnostics/face_evidence.json`의 `mask_continuity_refinement.candidates[].attempts[].elapsed_seconds` 합계이며 cluster_map에 포함되는 값이다. 두 시간을 더하면 안 된다.

NEON에서는 이미 GPU를 쓰는 YOLO가 전체의 약 4.3%, SAM 시도 누적은 약 48.9%였다. 따라서 YOLO만 더 빠르게 해도 전체 단축 폭은 작다. SAM을 무한히 빠르게 한다는 가정으로도 다른 약 22분 38초는 남는다.

현재 `refine_main_roles()`는 기존 최종 타이밍 항목 밖에서 실행되므로 항목 합계가 TOTAL에 못 미친다. 로그 간격과 segment_build 시간을 이용하면 이 구간은 세 영상에서 대략 6분 40초~9분 4초다. 이는 독립 타이머 측정이 아닌 간격으로 추정한 값이다. 메인 판정의 전체 해상도 얼굴 검출·프레임 읽기·중복 관측도 세분화해 측정해야 한다.

## AuraFace: GPU 적용 가능성과 속도

동일한 기존 `glintr100.onnx`, 동일한 얼굴 정렬/전처리, 실제 영상에서 검출한 얼굴 36개를 사용했다. 입력을 준비한 뒤 모델 추론만 3회 반복했다. 검출·영상 디코딩·전체 이름 판정 시간은 제외됐다. GPU 경로는 CoreML `MLProgram`, `CPUAndGPU`와 CPU fallback이다.

| 조건 | CPU 중앙값 | CoreML 중앙값 | CPU/CoreML |
|---|---:|---:|---:|
| 초기 실행: ONNX Runtime profiling 활성 | 1.975초 | 0.458초 | 4.32배 |
| 재확인: profiling 비활성 | 1.782초 | 1.094초 | **1.63배** |

초기 4.32배가 다음 측정에서 유지되지 않았으므로 대표 개선 배율로 사용하지 않는다. 프로파일링, 실행 순서, 캐시 및 장치 상태 등 조건 차이의 기여도를 분리하지 않았으므로 차이의 원인도 확정할 수 없다. 안정적인 앱 성능 주장은 전체 파이프라인을 동일 조건에서 반복 측정한 뒤에만 가능하다.

GPU 사용 증거는 provider 설정뿐 아니라 CoreML compute plan의 **253개 연산이 `MLGPUComputeDevice Apple M4`에 배정된 기록**과 실행 프로파일이다. 작은 CPU fallback 연산은 남아 있다.

두 비교에서 CPU/GPU 특징 벡터 코사인 유사도 최솟값은 `0.9999998808`, 평균은 약 `1.0`이었다. 이는 샘플 특징값의 일치 증거이며 전체 멤버 이름 정확도·임계값 경계 사례의 동등성 검증은 아니다.

초기 GPU 세션 준비 1.299초, 첫 추론 1.049초로 초기 비용도 존재했다. 캐시 재사용 재측정에서는 세션 준비 0.562초, 첫 추론 0.074초였다. 세션과 모델 캐시를 재사용해야 한다.

## SAM2: 실행은 되지만 즉시 전환할 수 없음

동일 설치 런타임의 MaskTracker를 독립 프로세스에서 CPU/MPS만 바꾸어 비교했다. 3개 영상의 약 1.5초 구간, 각 23프레임, fp32, 이미지 크기 512, torch/OpenCV threads=1이다. 첫 번째 실행 후 이미지 특징 캐시를 재사용한 두 번째 실행을 warm으로 기록했다.

| 영상 | CPU warm | MPS warm | 배율 | CPU/MPS 마스크 평균 IoU | 얼굴 소유 판정 차이 |
|---|---:|---:|---:|---:|---:|
| ANTIFRAGILE | 2.003초 | 1.426초 | 1.40배 | 0.538 | 2/23프레임 |
| NEON | 1.942초 | 1.394초 | 1.39배 | 0.794 | 4/23프레임 |
| Made My Night | 1.973초 | 1.445초 | 1.36배 | 0.940 | 0/23프레임 |

첫 MPS 사례는 초기 준비 영향으로 12.04초가 걸렸다. 이후 비캐시 첫 실행은 약 2.90~2.95초, CPU는 약 4.13~4.45초였다.

**검증 범위 제한:** 이번 SAM 실험은 bbox prompt의 정방향 `_masks()` 비교다. 제품의 얼굴 양성/음성 prompt, 역방향 검증, 컷 확인, 최종 승인 판정을 모두 실행한 결과가 아니다. 얼굴 소유 판정 차이는 누락·추가도 포함할 수 있으므로 이를 곧바로 다른 사람 오인으로 단정하면 안 된다. 다만 품질 동등성 확보 없이 전면 전환할 수 없다는 증거다.

GPU를 이전에 전혀 생각하지 않았던 것은 아니다. 10월 27일 실제 제품 검증 경로의 MPS 실험에서 CPU가 통과한 경로를 GPU가 `unconfirmed_main_ownership`으로 거절해 CPU를 유지했다. 기록은 다음에 남아 있다.

- 기존 회고: `/Users/jina/project/adlight/desktop/clipper_python/docs/superpowers/status/2026-10-28-dance-retrospective-and-next-steps.md`
- 기존 실험: `/Users/jina/project/adlight/.worktrees/dance-member-coverage-20261023/evaluation-output/structural-main-20261026/anti-mps-product-path-probe/product-path.json`

그렇더라도 큰 CPU 병목을 해결하지 못한 채 반복 검증 비용이 커진 상태는 남아 있다. AuraFace를 CPU로 둔 과거의 개별 결정 이유는 이번 감사만으로 확정하지 않는다.

## 다음 구현·검증 우선순위

1. 모델별 실제 장치/provider, 호출 수, 디코딩·검출·추론·검증 시간을 기록한다. 현재 YOLO만 나타내는 MPS 표시와 합계에서 빠지는 메인 판정 시간을 바로잡는다.
2. AuraFace의 CoreML 경로를 안무 플러그인에서 선택하도록 적용한다. 공유 클래스 기본값을 일괄 변경해 인물 하이라이트 동작까지 바꾸지 않는다. 세션/캐시 재사용, CPU fallback, 임계값 근처 이름 정확도 검증을 포함한다.
3. 동일 프레임의 얼굴 검출·특징·영상 읽기 재사용과 반복 SAM 시도의 중복 제거를 우선한다. 미확인 0초를 목표로 추적을 계속 늘리지 않는다. 검증량 제한은 실제 메인 교대/이름 판정이 후퇴하지 않는 범위에서 결정한다.
4. SAM2는 MPS 출력 차이의 원인과 제품 전체 검증 경로의 품질을 해결한 후 전환한다. 현재 결과로 무조건 GPU를 켜지 않는다.
5. 동일한 3개 YouTube URL로 새 앱을 실제 실행해 전체 시간, 단계 시간, 이름·메인 교대·구간 경계 품질을 비교한다. GPU 모델의 배율을 전체 앱 배율로 주장하지 않는다.

## 재현 자료

[측정 자료 디렉터리](02-gpu-performance-evidence/)에 스크립트, 결과 JSON, 시간 로그 발췌, compute plan을 저장했다. 모델·영상·얼굴 이미지·대형 캐시는 복사하지 않았다.

- `probe.py`: SAM CPU/MPS, AuraFace CPU/CoreML 초기 비교. `sam face` 인자를 함께 사용.
- `probe_no_profile.py`: AuraFace profiling을 끈 재측정. `face` 인자 사용.
- `coreml_plan.py`: 실제 CoreML 장치 배정 확인.
- `results.json`: 초기 측정 결과와 감사에서 추가한 하드웨어/배율/compute-plan 집계.
- `no-profile-results.json`: profiling 비활성 측정 원본.
- `historical-runtime-summary.json`, `historical-timing.jsonl`: 기존 앱 기록의 제한된 발췌·집계.

설치 앱의 `/Users/jina/Library/Application Support/Clipper Studio Dev/venvs/plugins/dance_highlight/bin/python`으로 실행했다. 스크립트에는 입력 프로젝트 경로와 출력 `/private/tmp/dance-gpu-audit-20261102`가 고정돼 있다. 재실행 전 해당 출력과 `no-profile` 하위 폴더를 만들고, 기존 결과를 보존하려면 다른 출력 경로로 바꾼다. 한 번의 실행은 결과 파일을 덮어쓴다.

모델 SHA256:

- AuraFace `glintr100.onnx`: `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60`
- SAM2 `sam2.1_t.pt`: `3c1e81ca9b037dd39d70a014ddb9a813d6c4c4e12555420db7eaff31689bd4e3`

공식 참고: [ONNX Runtime CoreML provider 옵션](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html), [PyTorch MPS](https://docs.pytorch.org/docs/main/notes/mps.html). 공식 지원 설명과 이 장비의 실측값을 구분한다.
