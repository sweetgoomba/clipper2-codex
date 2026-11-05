# 유휴 교정·자동 선택 독립 재검증 추가 수정

2026-11-03. 대상: Apple Silicon Mac / Windows x64. 원본 보고서 `03-highlight-auto-acceleration-independent-reverification.md`와 그 재현 자료를 보존하고, 아래 A01/A02/N01–N04를 실제 코드와 같은 조건에서 수정했습니다. 이 문서가 시험용 전달물의 최신 수정 상태입니다.

## 수정 결과

| 항목 | 재현한 원인 | 수정·회귀 근거 |
|---|---|---|
| A01 / F03 | 기본 YOLO FP16 경로에서 원래 raw incumbent 측정은 1개뿐이고, 유휴 native replay가 FP32뿐이라 같은 정밀도 baseline을 얻을 수 없음 | FP16과 FP32 native GPU replay를 별개 후보/측정/키로 분리. CPU는 원래 FP32 유지. 같은 raw 입력·같은 FP16 연산의 worker 실행 시간으로 원래 경로 baseline을 구성. 수집한 실제 프로필→run_once 순환→다음 ModelGate CPU 선택까지 검증. 원래 foreground 결과 객체와 전체 prediction 진단은 보존하고 전체 시간을 raw 시간으로 쓰지 않음 |
| A02 / F05 | 느린 CPU 비교가 조기 return하면 모델/전역 소비 시간이 0으로 남고 CPU/기존 경로가 후보 deadline 밖에서 실행됨 | CPU·기존 경로·후보를 공통 accounting finally로 감쌈. 첫 비교부터 같은 남은 예산을 적용하고 예산이 소진되면 추가 비교를 시작하지 않음. 이미 필요한 정상 분석 수행 시간은 추가 비교와 분리. CPU 35초 fake clock의 이전 0/0→현재35/35 재현. 실제 별도 프로세스의 CPU/GPU 역할 hang을 남은 watchdog으로 중단·종료 확인 |
| N01 | 다른 native GPU 측정이 selector에서 continue되어 실제 factory에 도달하지 않음 | 승인된 대체 native 후보를 YOLO/CLIP 실제 factory→NativeInference→소유 NativeCalibrationSession/worker에 연결. 실제 adapter/index·정밀도·source/weights·runtime·인증 scope 재검사, 살아 있는 host lease와 종료 확인 유지. 승인 없음/정밀도·장치·런타임 변경은 거부 |
| N02 | 최신 전달물과 지정 mac-artifacts/source-current-check JSON의 SHA·크기·파일 수 불일치 | 최종 Mac/소스 산출물 생성 후 designated metadata를 같은 build_id로 함께 재생성하고 실제 파일을 다시 읽어 확인. 이전 기록은 별도 보존. 파일명만 같다는 이유로 과거 PASS를 재사용하지 않음 |
| N03 | CPU 저장 후 idle 종료 실패409인데 UI가 이전 자동 설정을 유지 | 저장 오류 뒤 실제 저장 설정을 다시 조회하고 runtime/idle도 갱신. 조회도 실패하면 stale 설정을 지우고 제어를 비활성화. CPU 저장과 종료 미확인 차단은 계속 유지. 실제 bridge/HTTP/component 조건 회귀 |
| N04 | Python worktree의 `.git` 파일과 pytest/ruff 캐시가 앱에 포함됨 | electron-builder에서 `.git` 파일과 루트/하위 `.pytest_cache`·`.ruff_cache`를 명시 제외. 실제 FileMatcher+copyDir 동작으로 회귀 검증하고 최종 앱 ZIP/소스 ZIP도 직접 검사 |

## 품질·정밀도·승인 조건

기존 가중치, 모델 크기, 이미지 전후처리, 샘플링, NMS, 인물/안무 판정 임계값, Whisper small/beam5/VAD off/word timestamps/chunking을 바꾸지 않았습니다. SAM/OCR 비활성 상태도 유지합니다. FP16 baseline을 FP32 값으로 대신하거나 허용 오차를 늘리지 않았습니다. 원래 uint8 정규화에서 half 정밀도 연산과 FP32 후 half 변환의 일치는 256개 입력값으로 검증했습니다.

FP16 출력이 엄격한 원래 품질 비교를 통과하지 못하면 그 replay는 선택 baseline으로 승인하지 않습니다. 이런 경우 기존 경로를 유지하며 실제 장비의 수치·최종 품질은 사용자 시험 범위입니다. 정밀도 이름만 붙인 가짜 측정이나 실제 GPU 성능 수치는 사용하지 않았습니다.

대체 native GPU를 일반 자동 분석에 적용하려면 기존 release 인증과 현재 유효 측정이 모두 필요합니다. 로컬 유휴 비교가 인증서를 만들지는 않습니다. 준비된 장치가 없거나 승인·완결 비교 근거가 없으면 기존 경로를 유지합니다. 새 native 작업자는 원래 모델·실제 장치·정밀도를 확인하고, GPU lease를 보유한 소유 프로세스로 실행합니다. 종료를 확인하기 전에 lease를 해제하거나 CPU 재분석을 시작하지 않습니다.

native 실행 기록은 `runtime_device`와 실제 device/precision/adapter/runtime/source/weights 근거를 사용하며 ONNX graph profile로 위장하지 않습니다. benchmark 판정도 이 범위와 원래 33회/24종·CPU 시간·후보 시간·품질 비교를 요구합니다. 평소 자동 실행의 samples=0은 비교 완료로 승격하지 않습니다.

현재 기본 benchmark CLI의 `--verify`는 기본 명시 후보를 대상으로 하므로 새 native 다음 단위 자동 경로를 자동으로 전체 인수 시험했다고 표시하지 않습니다. 대응하는 실제 native 비교 증거가 없는 matrix 항목은 BLOCKED입니다. native 유휴 측정, 승인된 native 자동 실행 연결, 출하용 전체 하이라이트 인수는 서로 다른 근거입니다. 이 수정에서 새 출하 corpus/catalog를 만들어 채우지 않았습니다.

## 검증

- 수정 전 소스 ZIP 4,934개 파일과 이번 지적의 원래 재현을 기준으로 확인했습니다. 기존 작업 트리/원본 desktop/가중치/사용자 변경을 덮어쓰지 않았습니다.
- A02 원인 재현 RED 이후 예산/정책/선택/복구 집중 검사 34개 통과. 실제 CPU/GPU 역할 별도 프로세스의 짧은 watchdog 종료를 포함합니다.
- A01/N01 신규 native/benchmark 69개와 실제 CPU worker·idle·adapter 83개 검사 통과. 실제 tiny CPU checkpoint의 원래 출력 일치 및 작업자 종료를 포함합니다. 주입한 GPU 시간은 정책 검사용이며 제품 성능 수치가 아닙니다.
- Electron 전체 1,904개, Angular 설정/API/페이지 53개 및 스타일 21개 통과. NestJS는 이번 수정에서 소스 변경이 없고 직전 최종 소스의 전체 5,292개 통과 근거를 유지합니다.
- Python 최종 전체: 3,379개 통과, 기존 실패 6개, skip 5개. 기존 annotation golden 5개/fadeblack 렌더 1개와 실패 집합을 대조합니다.
- 새 native 테스트의 환경 모형이 import된 함수 binding에 남는 순서 의존성도 전체 검사로 재현했습니다. 제품 코드는 그대로 두고 테스트 fixture의 두 binding을 같은 환경으로 격리해 기본 가속 모듈 287개와 최종 전체 검사를 통과시켰으며, 테스트 수정도 독립 검토했습니다.
- 별도 검토자가 A02 이전/이후를 독립 재현하고 실제 native selector/factory·정밀도·host lease·작업자 종료와 설정·패키징 조건을 검토했습니다. 최종 상태는 검증 JSON의 독립 검토 항목으로 확인할 수 있습니다.
- native MPS 실행을 CUDA로 잘못 표시하던 설정 화면의 추가 연결 문제도 실제 RED1건→통합 GREEN53개로 교정하고 독립 재검토했습니다.
- 최종 앱의 Python/Nest/Angular/Electron 실행 파일 SHA, 런타임 lock, 필수 Node 의존성, 앱 ZIP의 `.git`/캐시/개인 자료 제외, 소스 ZIP의 현재 소스 SHA 및 지정 전달 metadata를 다시 확인합니다.

기존 전체 검사 실패를 새 기능의 성공으로 숨기지 않습니다. Windows 실제 빌드·GPU·Windows Job·전원 전환·한국어 경로와 여러 영상의 최종 하이라이트 품질·cold/warm 속도 검증은 사용자가 수행합니다. Mac 앱은 미서명 개발 시험 빌드입니다. 설치본/실행 중 앱/공유 가상환경을 교체하지 않았고 커밋·푸시는 하지 않았습니다.

## 산출물과 증거

빌드·시험 순서는 BUILD-AND-TEST.ko.md를 따릅니다. 새 시험용 Mac DMG/ZIP과 Windows 직접 빌드용 source ZIP은 같은 경로의 파일을 갱신합니다.

- 최신 구현 문서: `.codex/operations/accelerators/records/2026/11/03-highlight-idle-rotation-reaudit-remediation.md`.
- 최신 검증/SHA: `03-highlight-idle-rotation-validation.json` 및 Python `.implementation-evidence/reaudit-corrections/validation.json`.
- 지정 전달 metadata: Python `.implementation-evidence/completion/mac-artifacts.json`, `completion/handoff/source-current-check.json`, `completion/handoff/sha256.json`.
- 재현·회귀: Python `reaudit-corrections/`, `reaudit-native/`; Angular/Electron `reaudit-ui-packaging/`. 독립 재검토는 `reaudit-corrections/review/`에 보존합니다.
