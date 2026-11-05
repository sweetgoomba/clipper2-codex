> 최종 독립 감사 반영 전 기록입니다. 현재 상태는 [최종 감사 후 수정 결과](03-highlight-auto-acceleration-final-audit-remediation.md)와 [시험 안내](03-highlight-auto-acceleration-device-build-guide.md)를 확인하세요.

# 하이라이트 자동 가속 구현·검증 기록 — 2026-11-03

얼굴·CLIP·Whisper의 실제 실행 경로, 공통 자동 선택/검증, 앱 설정, 실패 시 CPU 재분석을 연결했다. Apple Silicon Mac과 Windows x64용 소스와 직접 빌드 절차를 준비했다. 기존 샘플링·사람/안무 판정·모델 가중치·얼굴 정렬·하이라이트 기준·Whisper small/beam 5는 유지했다.

## 변경 범위

- `clipper_accelerators`: 모델/아티팩트/실행기/OS/GPU/드라이버/shape/배치/정밀도/소비 플러그인의 동일성을 검증한다. 인증된 후보와 기존 실행 경로를 로드 비용·중앙값·p90·다양한 실제 입력으로 비교한다. 분석 단위 중 임베딩을 임의로 섞지 않는다.
- YOLO는 원래 Ultralytics 전후처리, YuNet은 OpenCV 디코더/NMS, AuraFace는 원래 정렬/입력, SFace는 alignCrop/RGB/스케일 1, CLIP은 원래 전처리/정규화/샷 집계를 유지한다. 새 후보가 사용되지 않을 때 기존 MPS/CUDA 경로를 보존한다.
- Whisper는 실제 CTranslate2 장치·정밀도·모델 파일·디코딩·chunking을 캐시 키에 묶는다. Windows CUDA와 CPU의 비교·품질 검사·측정 이력을 연결했다. Mac MLX는 beam search 미지원 때문에 기존 beam 5와 동등하게 대체하지 않는다. Mac의 Whisper CPU 실행은 의도한 품질 보존 정책이다.
- Electron은 해시가 고정된 별도 실행기 환경을 만들고 프로세스/메모리 소유권을 관리한다. 실행기 준비 실패가 기존 MPS/CUDA를 숨기지 않도록 기본 Python의 가벼운 환경 탐색과 분리했다. GPU가 사용 중이면 영구 고장 기록으로 바꾸지 않는다.
- NestJS는 신뢰할 수 있는 Electron 설정을 작업 시작 시 고정하고, 앱에서 예약한 명시적 기기 시험에만 해당 플러그인·job·소유 프로세스에 묶인 일회용 권한을 전달한다. 사용자 분석 params로 새 GPU 시험 권한을 만들 수 없다.
- Angular **설정 → 분석 가속**에 세 플러그인의 자동/CPU, 실행기 준비, 다음 분석의 재최적화 예약, 실제 모델 실행 경로/시간/CPU 재분석 결과를 표시한다.
- GPU 실행 실패는 소유 프로세스를 정리한 후 CPU 새 프로세스로 해당 분석 전체를 한 번 다시 수행한다. 취소·잘못된 입력·CPU 자체 실패는 GPU 고장으로 처리하지 않는다. 완성된 generation만 원자적으로 revision을 공개하고 결과를 읽는 소비자는 같은 revision을 사용한다.

## 독립 최종 검토와 재현·회귀

별도 Astra xhigh 검토자가 전체 변경을 읽고 지적한 6개 항목을 수정했다. 검토자는 수정 후 재검토를 수행한 것으로 표시하지 않는다.

| 재현된 문제 | 수정 및 증거 |
|---|---|
| AuraFace 후보가 없으면 기존 GPU 세션을 버림 | 기존 incumbent 세션을 계속 사용. `review-red.log` → `review-python-green.log`, `test_missing_face_candidate_preserves_incumbent` |
| YuNet wrapper의 입력 크기가 기존 GPU detector로 전달되지 않음 | setInputSize 전달. `test_yunet_incumbent_receives_input_size` |
| 별도 실행기 설치 실패가 native GPU 탐색까지 막음 | stdlib 기반 native 환경 탐색 독립. Electron `accelerator-native-environment.test.js` red/green 기록 |
| 실제 CPU Whisper 오류가 바깥 CUDA 호출 때문에 GPU 오류로 바뀜 | 실제 선택한 장치에서 분류하고 gpu=false를 owned 단계/worker 사이에 보존. `test_actual_cpu_whisper_error_is_not_relabeled_gpu` |
| worker 시작 실패 뒤 GPU lease 누수 | client가 없더라도 lease 해제, close 멱등성. `test_worker_start_failure_still_releases_lease` |
| 대사에서 CPU 결과를 공개하면 실제 GPU 실행 증거도 사라짐 | 공개 결과 경로와 실행한 후보 증거를 별도 기록. `test_dialog_executed_gpu_evidence_survives_cpu_publication` |

추가로 시험 권한의 plugin/job/PID 범위, 합산 GPU 메모리 예약, 일시적 GPU 사용 중 상태, 기존 YOLO 결과 객체 보존, 정상 idle worker 재생성을 회귀 검사했다. `final-boundaries-red.log`와 Electron `completion-leases-red.log`에 실패 재현, `final-focused-green.log` 및 `completion-final-accelerator-tests.log`에 수정 후 증거를 남겼다. 새 테스트의 환경변수 누수는 테스트 fixture에서 복구했으며 전체 검사를 다시 실행했다.

## 실제 실행 증거

- 인물 CPU 분석: 실제 6초 영상, 1개 인물 그룹/1개 클립, revision 1. `person-cpu-result.json`.
- 인물 Core ML 명시적 시험: 실제 음성 포함 영상에서 YuNet Core ML 실행, Whisper CPU 실행, CPU 전체 재분석과 인물/클립/자막 의미 결과 일치(PASS). `person-coreml-result.json`, `person-coreml.log`.
- 해당 시험의 YOLO Core ML 후보는 raw 수치 비교 실패로 CPU를 사용했다. 이를 성공으로 바꾸거나 허용 오차를 늘리지 않았다. YuNet은 서로 다른 입력 수가 12여서 최소 24개 다양성 조건을 채우지 못했다. 승인/속도 판정용 corpus로 사용하지 않는다.
- 대사 CPU 분석: 장면 전환 6개와 오디오가 있는 18초 fixture에서 Whisper 실제 실행, CLIP 실제 6회 임베딩, 분석 JSON/revision 1 생성. `dialog-cuts-audio-cpu-result.json`. LLM 과금/생성 단계는 호출하지 않았다.
- 첫 무음 장면 전환 fixture는 원래 MFCC 경로의 오디오 디코더에서 실패했다. 이를 GPU 실패로 바꾸거나 CPU 재시도로 숨기지 않았다. 이후 오디오 트랙이 있는 fixture로 실제 전체 analyze_media 단계 성공을 확인했다.
- 이전 단계의 실제 안무 CPU/ONNX CPU 비교와 주입된 GPU 실패 후 인물 CPU 재실행 증거는 `.implementation-evidence/next-integration`에 유지한다. 이번 Windows 실기기 검증으로 표시하지 않는다.

이 시험들은 정지 화면을 포함한 구현 smoke test이며 실제 다양한 하이라이트 영상 corpus를 대체하지 않는다. 동시 부하가 있어 이 결과의 ms 값을 제품 속도 개선 주장에 사용하지 않는다.

## 최종 검사

| 검사 | 결과 |
|---|---|
| Python 전체 최종 | 3,169 passed, 6 failed, 5 skipped. 실패 6개는 기존 annotation golden 5개와 fadeblack 1개와 동일. `python-baseline-comparison.json`으로 실패 집합 비교 |
| 가속·얼굴·CPU 재분석 집중 검사 | 195 passed, `final-focused-green.log` |
| 최신 안무 변경 보존 후 관련 검사 | 210 passed, `current-work-python-green.log` |
| Python 정적 검사 | `final-ruff.log`: All checks passed |
| NestJS 전체 | 5,261 passed, 0 failed. 최신 접근권한 변경 보존 후 해당 10개도 통과 |
| Angular | 실제 Chrome 설정 테스트 31개, 스타일 검사 21개 통과. packaged 빌드 성공 |
| Electron 전체 | 1,865 passed, 2 failed. 기존 fake-updater 시간 모의 실패(26!=1)와 POSIX 소유 프로세스 검사 간헐 실패. 후자는 수정 없이 분리 재실행 6/6 통과, 원본도 6/6 통과. 소스/compiled 해시가 원본과 동일함을 확인 |
| Electron 가속·설정·경로·성능 집중 | 122 passed, 0 failed |
| Apple Silicon 앱 | 실제 arm64 Mach-O, DMG/ZIP 생성. 미서명 개발 빌드. 패키지 공통 runtime 소스 30개 일치, 테스트 자료 제외 확인. 심볼릭 링크 의존성 누락을 발견해 작업 트리에서 npm ci로 별도 설치 후 다시 패키징했고, 실제 Electron asar 해석기로 9개 런타임 의존성을 재확인 |
| Windows 실기기 | 이 Mac에서 확인하지 않음. Windows x64 소스/lock/빌드 절차 제공 |

기존 실패를 통과로 표시하거나 관련 없는 golden·시간 예산을 바꾸지 않았다. 전체 테스트가 모두 통과했다고 주장하지 않는다.

## 진행 중 변경 보존

원본 desktop 폴더는 구현 대상으로 쓰지 않았다. 시작 시 해시와 최종 원본을 비교하면서 다른 작업이 추가한 Python 7개/NestJS 2개 변경을 발견했다. 원본을 수정하지 않고 가속 작업 트리에 보존했다. 겹친 pipeline.py는 보관한 기준 파일을 사용해 세 방향으로 병합했고 충돌이 없었다. 새 안무 모듈과 fixture 5개도 함께 보존했다. 원본의 새 변경을 되돌리지 않았다.

`current-work-merge/manifest.json`과 `new-user-files-sha.json`에 원본/병합 전/병합 후 해시를 기록했다. `packaged-user-preservation.json`은 최신 안무 코드가 실제 앱에 들어갔으며 원본이 캡처 이후 바뀌지 않았음을 확인한다. 기존 Angular source-scene-overlay 작업 4개도 원본/작업 트리에서 유지했다. 원본 비교 결과의 mismatch를 무조건 덮어쓰지 않았다.

## 직접 시험 범위와 남은 승인

직접 빌드·시험 방법은 `BUILD-AND-TEST.ko.md`, Windows 전달용 소스는 `handoff/clipper-acceleration-source.zip`이다. 4,896개 소스 파일과 lock/공개 설정/공개키의 해시를 저장하고 압축 내부 및 현재 소스와 대조했다. 원본 Git/개인 .env/모델/가상환경/node_modules/시험 로그는 묶지 않았다.

실기기 승인이 없는 새 ONNX 후보는 앱의 **다시 최적화**에서 실제 실행·CPU 비교할 수 있다. 일반 자동 모드는 release catalog에 승인된 범위만 새 경로로 선택하고, 나머지는 기존 CPU/MPS/CUDA 경로를 유지한다. 현재 광범위 Windows GPU 승인 catalog는 비어 있다. 이를 가짜 보고서로 채우거나 로컬 smoke test를 전체 GPU 승인으로 바꾸지 않았다.

이 빌드는 모든 GPU 어댑터/모든 실행기 조합의 전수 벤치마크를 구현한 것은 아니다. 기본 ONNX 준비는 확인한 호환 어댑터 하나를 사용한다. TensorRT/MLX 등 품질 동등성이 확인되지 않은 후보를 기본 활성화하지 않는다. 실기기 corpus의 최종 품질·속도 확인과 지원 범위 승인은 사용자의 Mac/Windows 테스트 결과가 필요하다.
