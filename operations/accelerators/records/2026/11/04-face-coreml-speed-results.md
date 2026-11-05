# AuraFace CPU 병목 개선과 Made My Night 실제 결과

2026년 11월 4일 KST. 실행 시간 단축을 우선한다는 사용자 지시에 따라 Mac 얼굴 처리 병목을 측정하고, 기존 AuraFace 모델에서 파생한 CoreML 경로를 연결했다. Windows 조합 비교와 실행 앱 빌드는 별도 채팅에 위임했다. 개발 서버 배포는 하지 않았다.

## 결과

같은 Mac, Made My Night 원본 SHA `3400a0f3d21399609c54b38884d0208bf28e2541e10d450c5135306deba2e363`, 기존 참조 사진 31장, 같은 분석 옵션을 사용했다. 기존 프로젝트를 덮지 않고 별도 결과 폴더에서 앱과 같은 `run_visual_unit`·소유된 자식 프로세스·실제 Electron 메모리 lease를 사용했다.

| 항목 | 기존 MPS + CPU 얼굴 | MPS + CoreML 얼굴 |
|---|---:|---:|
| 전체 소요 시간 | 721.975초 | 327.616초 |
| 얼굴 모델 추론 누적 | 336.420초 | 23.671초 |
| 얼굴 추출 단계 | 166.360초 | 약 36.2초 |
| 메인 인물 선택 단계 | 289.864초 | 약 116.2초 |
| 얼굴 요청 / 실제 추론 / 캐시 적중 | 4603 / 4557 / 46 | 4603 / 4557 / 46 |
| 최종 메인 / 단체 / 전체 클립 | 49 / 14 / 63 | 49 / 14 / 63 |
| 이름 미확정 메인 구간 | 4.872초 | 4.872초 |

얼굴 모델 누적 시간은 여러 분석 단계에 포함되므로 단계별 시간과 합산하지 않는다.

이번 단일 비교에서 전체 약 **54.62% 감소**, 얼굴 모델 추론 누적 약 **14.2배 가속**을 관측했다. 최종 `lists` 전체와 `config`는 기존 결과와 정확히 같았다. 이 한 영상에서 확인한 결과이며 다른 PC·영상의 동일한 개선율을 보장하지 않는다. 기존 측정과 이번 측정은 다른 시점의 단일 실행이며, 변경하지 않은 YuNet CPU 누적도 146.446→105.027초로 달라졌다. 전체 감소분을 순수한 모델 단독 가속 비율로 해석하지 않는다.

CPU 재분석 없이 attempt 0에서 완료했다. AuraFace 실제 프로파일에서 CoreML 노드 6개, CPU 노드 12개를 확인했다. 이는 첫 세 검사 실행의 이벤트 수이며, 전체 4603회가 모두 물리 GPU에서만 실행됐다는 뜻은 아니다. CoreML `ALL`은 OS가 CPU/GPU/Neural Engine을 배치할 수 있으며 진단은 `graph_execution=mixed`, `release_qualified=false`로 기록한다.

## 왜 얼굴 처리가 계속 CPU였는가

기존 공유 AuraFace 생성기는 CPU 세션을 만들고, 준비된 선택적 실행기와 인증·프로필 조건이 있는 경우에만 별도 라우터를 사용했다. 실제 자동 모드의 기본 얼굴 경로에는 CoreML 실행 연결이 없었다. YOLO의 MPS 가속만으로는 전체 시간의 큰 비중을 차지하던 이 CPU 추론이 줄지 않았다.

CPU 스레드 1/2/4 제한과 배치 2/4/8도 먼저 시험했으나 기본 CPU보다 느려 채택하지 않았다. 얼굴 고정 입력 30개의 원본 FP32 CPU 중앙값은 약 50.1ms, 정적 배치 1의 FP16 내부 CoreML은 약 3.52ms, 원본과 코사인 최소 0.9999637이었다. 실제 연결의 전체 영상 로컬 검사에서는 CPU 59.42ms, CoreML 6.32ms, 코사인 최소 0.9999695, 준비 828.7ms를 관측했다.

## 반영한 코드와 보호 장치

Python 원격 dev 커밋: `a73593a2c6445bc87401eb4de30e9954ef2467ba` (기준 `5d565dfa96c1fa3bd6a4b94e9dc96110088f0dab`). 일반 fast-forward와 push 후 서버 SHA를 확인했다. 다른 저장소의 소스·안무 품질 정책·참조 사진·SAM OFF는 수정하지 않았다.

- `clipper_accelerators/native_face.py`: Apple Silicon Mac의 소유된 자동 분석에서만 동작한다. Windows/Intel Mac/CPU 강제/실행기 없음/호스트 없음에서는 기본 CPU를 유지한다. 계획 작업량이 128 미만이거나 없으면 변환과 시험 자체를 건너뛴다.
- 원본 AuraFace SHA `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60`와 파생 SHA `a97695fbb8785013af24264fe235cb8bcffca8de77d56a47b3cc0e787608757c`를 고정했다. ONNX 1.20.1 / ORT 1.31.0의 검증한 변환만 허용한다. 원본 파일은 수정하지 않는다. 정적 배치 1, 내부 FP16, FP32 입출력의 파일을 별도 accelerator cache에 원자적으로 저장하고 매번 해시를 확인한다.
- 최초 실제 얼굴과 두 방향 반전 입력을 CPU·CoreML에서 비교한다. 유효 출력, 코사인 최소 0.9995, 임베딩 norm 차이 2% 이내, 실제 CoreML 노드, CPU 대비 중앙값 20% 이상 감소를 모두 확인한 뒤 해당 분석의 경로를 고정한다. 이 짧은 로컬 수치 검사는 전영상·전기기 품질 인증을 발급하지 않는다. 다른 선택적 모델 팩의 인증 gate도 바꾸지 않았다.
- 호스트의 소유권과 메모리 admission을 유지한다. 파생 모델 크기 × 4 + 64MiB를 예약하며 실제 YOLO 예약과 합친 조건에서도 실행을 확인했다. 전용 native 호출은 기존 30초 watchdog을 통과한다.
- ONNX Runtime의 세션 전체 CPU 내부 재시도는 비활성화한다. 그래프의 CPU 할당 노드는 유지하되, 선택 이후 GPU 실행 오류나 잘못된 출력은 `BackendFailure(gpu=true)`로 전달해 전체 분석을 새 CPU 프로세스로 한 번 다시 수행한다. 최초 로컬 시험 실패는 CPU 임베딩만 반환한다. 이미 전달한 가속 임베딩 뒤에 개별 얼굴만 CPU로 바꾸지 않는다.
- 공유 AuraFace 기본 생성기와 준비된 라우터의 incumbent를 연결했다. 준비된 라우터는 선택이 끝난 뒤 backend/precision을 gate에 고정해 CoreML 시간을 CPU 시간으로 기록하지 않는다. 동시 첫 호출도 lock으로 보호한다. 준비된 다른 후보를 최종 선택하면 사용하지 않은 builtin 세션의 예약이 분석 종료까지 유지될 수 있는 보수적 자원 비용은 남아 있다.

## 재현·회귀와 독립 검토

최종 **1772개 통과**, Ruff와 `git diff --check` 통과. 새 테스트 26개가 원본/비대상 경로, 출력·속도 거절, 메모리 거절 사유, 실제 ORT 예외, 내부 CPU 재시도 차단, 모델 watchdog, 짧은 작업 사전 제외, 동시 첫 호출, 준비된 후보의 backend/precision 기록, 늦은 EPFail의 전체 CPU 재분석과 같은 artifact revision 게시를 확인한다.

독립 검토에서 발견한 ORT 예외의 상속 차이, host 오류 정보 손실, watchdog 누락, 내부 CPU 재시도, 초기 준비 손해, 준비된 후보 기록 오류와 동시성 경합을 각각 재현한 뒤 수정했다. 마지막 읽기 전용 재검토에서 차단 사항 없음으로 확인했다. 실제 전체 영상 측정 이후 추가한 마지막 변경은 동시성 보호와 준비된 후보의 기록 보완이며, 그 부분은 회귀 검사로 확인했다.

재현 로그와 입력 해시·측정·비교 JSON은 `04-face-coreml-speed-evidence/`, 구조화 요약은 `04-face-coreml-speed-results.json`이다. 원본 프로젝트 데이터는 보존했고 시험 출력은 `/private/tmp/clipper-face-speed-20261104/mmn`이다.

## Windows 병행 작업과 현재 모델 상태

새 채팅 **Windows x64 하이라이트 가속 조합 비교와 실행 앱 빌드** (`01a1a294-76cc-7d73-af4d-be827b33bde9`)에 사용자 요청을 전달했다. 모델별 기존/현재 경로, 실제 지원 조합, 하나의 앱과 격리된 실행기 팩, 자동 순환 시험, 실제 장치·시간·오류·CPU 복구의 분리 기록, Windows 실행 산출물 제공을 맡겼다. 부모 측정 중 무거운 빌드를 보류했고 측정 후 재개하도록 전달했다.

전부 PyTorch에서 ONNX로 교체한 상태가 아니다. YOLO·CLIP은 원래 PyTorch와 선택적 ONNX 후보가 함께 있고, 얼굴 모델들은 원래 ONNX이다. Whisper는 현재 CTranslate2 경로이다. Windows에서 DirectML/CUDA/TensorRT/OpenVINO/Windows ML 등은 하드웨어·운영체제·모델별 지원 범위가 다르며 실제로 지원하는 후보를 비교해야 한다. 이 Mac 수정이 Windows AuraFace의 BatchNormalization 오류를 해결했다는 의미는 아니다. 해당 원인과 가능한 다른 실행기는 새 채팅의 별도 시험 대상이다.

## Mac 앱 빌드

원본 저장소에서 사용자가 요청한 `npm run build:app:mac:arm64:local-api`가 exit 0으로 완료됐다.

앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`

- 패키지에 포함된 새 helper·공유 라우터·AuraFace 생성기의 SHA가 원본 소스와 모두 일치한다.
- `webApiBaseUrl=http://127.0.0.1:3000`, `autoUpdateDisabled=true`를 패키지에서 확인했다. API health와 user/release/admin DB가 정상이며, 앱 Nest health도 정상이다.
- 실제 앱을 실행해 기존 로그인·안무 하이라이트 입력 화면을 확인했다. 프로젝트와 참조 사진·기존 결과를 삭제하지 않았다.
- 설치된 안무 venv는 새 소스 fingerprint와 달라 갱신이 필요한 상태였다. 앱의 실제 `ensurePluginVenv` 함수를 패키지 소스로 실행해 네 로컬 패키지를 갱신했다. 이 함수는 원래 플러그인 시작 때도 같은 fingerprint 비교와 갱신을 수행한다. 이후 설치된 `native_face.py` SHA가 패키지·원본과 일치함을 확인했다.
- 원본 8개 저장소는 모두 dev이며 추적 소스 변경은 없다. 이전에 설명한 CoreML 변환 캐시 38개와 과거 Mac 시험 앱 산출물은 보존했다. 개발 서버 배포는 수행하지 않았다. 이전 Windows 기준 실행 폴더는 `desktop/clipper_electron/.tmp/latest-dev-build-20261104/windows-baseline/win-unpacked`, 이전 Mac 앱은 같은 `.tmp/latest-dev-build-20261104/previous-mac/`에 보존했다.
