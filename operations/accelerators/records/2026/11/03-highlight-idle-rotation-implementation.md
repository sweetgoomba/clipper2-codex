> 최초 유휴 교정 전달 단계의 기록입니다. 독립 재검증 추가 수정과 최신 산출물은 [최신 수정 보고서](03-highlight-idle-rotation-reaudit-remediation.md) 및 [검증 JSON](03-highlight-idle-rotation-validation.json)을 참고하세요.

# 하이라이트 유휴 교정·GPU/실행기 순환 비교 구현 및 검증

작성: 2026-11-03. 대상: Apple Silicon Mac, Windows x64. 이 문서가 유휴 교정 단계의 최신 상태입니다. 이전 IMPLEMENTATION-REPORT/AUDIT-REMEDIATION의 미구현 항목을 이 구현으로 갱신합니다.

## 구현 결과

안무·인물·대사의 실제 모델 실행 경로에 유휴 교정과 다음 분석의 선택을 연결했습니다. Electron이 검사 프로세스와 사용자 작업의 배타 실행을 관리하고, Python이 실제 입력 재실행·CPU 대비 품질 확인·반복 측정·후보 순환을 수행합니다. NestJS의 분석·취소·얼굴 사전검사와 Angular 설정 카드도 연결했습니다. 단순 벤치마크용 함수나 시험용 가짜 실행기를 제품 동작으로 세지 않았습니다.

기존 YOLO Pose, YuNet, AuraFace, SFace, CLIP ViT-B32, Whisper small의 가중치·전후처리·NMS·샘플링·인물/안무 기준·하이라이트 임계값을 유지합니다. Whisper는 small/beam 5/VAD off/word timestamps/기존 chunking을 유지하며 Mac에서는 기존 CPU를 사용합니다. SAM/OCR은 기존 비활성 상태입니다. 출력의 공개·revision 및 GPU 실패 시 새 CPU 분석으로 재시도하는 기존 전체 작업 복구 계약도 유지합니다.

## 실제 동작

1. 명시적인 **이 기기 시험**에서 원래 CPU 입력과 출력을 무결성 해시로 봉인합니다. 작업 전체의 품질 검사와 결과 commit이 성공한 뒤에만 유휴 검사 자료로 공개합니다. 평소 자동 분석에서는 원시 입력을 수집하지 않습니다.
2. 시각 모델은 서로 다른 입력 24개와 CPU 기준 출력을 재실행합니다. 3회 warmup 후 최소 30회 측정하며 CPU와 후보 순서를 번갈아 실행합니다. 음성은 서로 다른 30초 이하의 완전한 PCM 입력 3종과 CPU 전사를 각 3 round 재실행합니다. 긴 입력을 잘라 표본을 만들거나 정밀도를 줄이지 않습니다.
3. 준비된 호환 실행기 × 실제로 대응되는 GPU를 안정적인 ID로 열거합니다. Mac ONNX Core ML, Windows ONNX DirectML 및 명시적으로 준비한 NVIDIA ONNX CUDA와, 설치된 기존 PyTorch CPU/MPS/CUDA·CTranslate2 CPU/CUDA 환경을 사용합니다. TensorRT/OpenVINO/MLX를 모두 설치하는 기능은 포함하지 않습니다.
4. 회차당 최대 120초·후보 2개를 검사하고 cursor를 저장해 이어갑니다. 시각 후보 30초·음성 후보 60초 예산을 로드·실행·취소까지 전달합니다. CPU 모드에서는 해당 플러그인의 검사를 보류합니다.
5. 성공한 완결 측정만 원자 저장합니다. 품질 불일치·잘못된 출력·비호환 후보는 격리하고, 점유·timeout·메모리 부족은 15–300초 재시도 간격을 둡니다. 새 수동 요청 ID나 실행 환경 변경은 재검사 계기가 됩니다. 나중에 취소·실패해도 이전 완결 자료를 불완전 값으로 덮지 않습니다.
6. 다음 자동 분석의 첫 모델 입력에서 선택을 고정합니다. 현재 경로의 실제 실행 비용, 후보의 로드·컴파일 비용, 예상 작업량과 median/p90을 비교합니다. 기존 경로보다 실익이 확인되지 않거나 비교 근거가 부족하면 현재 경로를 유지합니다. YOLO 전체 predict 시간을 원시 tensor 시간으로 둔갑시키거나 worker IPC 시간을 기존 인프로세스 비용으로 쓰지 않습니다. 분석 중에 임베딩 실행기를 바꾸지 않습니다.
7. 전원 모드·드라이버·모델·전처리·shape·빌드·실행기·실제 GPU ID가 바뀌면 이전 측정은 현재 선택에서 제외합니다. 입력 자료 자체는 무결성 검사를 거쳐 재사용하고 새 환경에서 CPU/후보를 다시 측정합니다. Mac 전원 탐색에는 배터리 잔량 변동을 불필요한 변경으로 포함하지 않습니다. Windows 전원 탐색은 별도 제한 시간의 stdlib helper를 사용합니다.

## 사용자 작업 우선과 CPU 복구

약 15초 간격으로 유휴 상태를 확인하지만 분석 시작 요청이 우선입니다. 실제 작업 시작 전, 진행 중 검사의 모든 소유 하위 프로세스 종료를 확인합니다. 프로세스 ID 재사용·프로세스 소유자 종료·불명확한 health 응답을 종료 증거로 삼지 않습니다. Mac은 birth/PGID/nonce를 확인하고 Windows는 nonce가 있는 고유 named Job을 사용합니다. 앱 재시작 및 같은 프로세스에서 supervisor가 죽은 경우도 소유권 증거로 회수합니다.

Nest 프로세스가 죽어도 Electron 소유 Python은 계속 실행될 수 있으므로, Nest PID만으로 예약을 해제하지 않습니다. 안무 기준 얼굴 확인 요청도 분석과 같은 foreground 수명주기에 포함합니다. 응답 유실·취소·실패 시에는 예약 정리와 실제 Python 종료를 확인하고 나서 유휴 검사를 허용합니다.

자식 종료가 확인되지 않은 `CleanupIncomplete`는 SDK health의 `cleanup_pending`과 busy 상태에 남깁니다. 오류가 취소/OOM 등으로 감싸져도 원인을 추적합니다. 이 상태에서는 새 분석·유휴 검사·정상 종료가 성공한 것처럼 진행하지 않습니다. 정상 GPU 실패의 CPU 전체 재분석은 종료가 확인된 뒤 수행합니다. 취소·입력 오류·CPU 자체 실패를 GPU 실패로 분류하지 않습니다.

## 저장·런타임·설정

개인 검사 자료는 한 프로필 128 MiB, 플러그인당 합계 512 MiB, 최대 8개로 제한합니다. 현재 사용 중인 자료/소유권 미확인 staging은 보존하고, 폐기된 빌드 또는 종료가 입증된 staging만 회수합니다. 공간 부족은 `insufficient_storage`로 남기며 입력 수/모델/정밀도를 낮추지 않습니다. 실제 첨부 YOLO 시험 자료는 원래 CPU 입력·출력의 압축 합계가 49,641,539바이트라 배포 검사 자료용 25 MiB 한도를 개인 자료에 그대로 쓸 수 없음을 확인했습니다. 라이선스가 확인된 배포 검사 자료의 별도 25 MiB 제한은 유지합니다. 개인 입력·음성·출력은 업로드하지 않고 앱/소스 배포물에서 제외합니다.

런타임은 기존 플러그인 환경과 분리해 해시 고정 lock으로 준비합니다. 부팅 시에는 설치 상태를 읽고 기기를 탐색하며, 추가 패키지 설치는 준비 버튼으로 수행합니다. Windows CUDA는 실제 사용 가능한 CUDA 장치를 확인한 경우 별도 대용량 준비를 허용합니다. 준비된 DirectML을 CUDA로 덮지 않으며 호환 immutable pack 목록을 유지합니다. Core ML 추가 패키지의 ONNX Runtime 1.31은 macOS 14 이상이 필요하고 미지원 환경에서는 기존 경로를 유지합니다.

설정 카드에는 자동/CPU, 추가 실행기 준비, NVIDIA CUDA 별도 준비, 이 기기 시험, 유휴 검사 다시 예약, 진행·보류·완료·잔여 후보 및 실제 실행 기록이 있습니다. 상세 측정은 `userData/accelerators/idle/PLUGIN/measurements`, 실패/보류는 `attempts`, 순서는 `rotation.json`에 저장합니다. 사용법은 BUILD-AND-TEST.ko.md를 참고하세요.

## 품질 승인과 실기기 시험의 구분

로컬 교정은 실제 기기의 속도·출력 비교이며 제품 전체의 승인 인증서를 생성하지 않습니다. 기존 CPU/MPS/CUDA 실행은 유지하고, 새 ONNX 경로나 다른 GPU를 일반 자동 분석에 채택하려면 기존의 모델·입력·환경별 release 승인과 현재 유효한 로컬 측정을 모두 충족해야 합니다. 이 빌드에는 공급받지 않은 승인 corpus/catalog를 만들어 넣지 않았습니다. 따라서 명시적인 기기 시험과 유휴 순환으로 새 후보를 실제 시험할 수 있지만, 미승인 후보를 일반 자동 모드에 무조건 적용하지 않습니다.

F05에서 남았던 유휴 교정 제품 연결과 준비 실행기/다중 GPU 순환은 구현했습니다. 승인 corpus/catalog 작성·여러 실제 GPU에서 품질·속도·고장 복구 확인은 사용자 실기기 검증 범위입니다. Windows x64에서 빌드/실행했다고 주장하지 않으며, Apple GPU 추론을 이 개발 환경에서 승인했다고 주장하지 않습니다. Windows ARM/Intel Mac은 이번 지원 범위 밖입니다. 특정 GPU에서 가장 빠르거나 모든 PC에 같은 실행기가 최선이라고 결론 내리지 않습니다.

## 독립 검토와 재현·회귀

최초 작업 스냅샷 `idle-rotation/before.json`과 이전 소스 ZIP을 기준으로 독립 검토했습니다. 7개 지적을 수정했고 검토자의 독립 집중 검사 73개가 통과했습니다.

| 지적 | 수정과 검증 |
|---|---|
| R1: Nest 종료 시 살아 있는 Python과 검사 중첩 | 실제 Python stopped/idle 증거를 요구, 불명확한 상태는 예약 유지 |
| R2: Windows supervisor 강제 종료 후 같은 Electron 내 회수 실패 | 고유 named Job 소유권·empty proof 회수와 살아 있는 supervisor 보류 |
| R3: CUDA 없는 Windows에도 CUDA 준비 제공 | 실제 사용 가능한 CUDA 장치 대응표로 노출/설치 진입 검증 |
| R4: 안무 기준 얼굴 사전 확인이 배타 실행 우회 | 실제 서비스에 공통 수명주기 연결; AppModule DI·실제 request 검사 |
| R5: 종료 불명확한 자식이 health 0으로 보고됨 | SDK cleanup_pending 지속, 오류 cause 추적, N/E health 확인 강화; RED→GREEN 9개 |
| R6: 전원/드라이버 변경 후 음성의 새 측정을 선택에 쓰지 못함 | immutable 입력 재사용과 새 CPU/후보 환경 검증 분리, 저장 경로 문자열 처리 수정 |
| R7: 다른 플러그인 staging/과거 8개 자료가 새 수집 차단 | 플러그인별 한도와 안전한 obsolete/abandoned 회수; 현재 자료 보존 |

독립 검토 뒤 전체 검사 중 CLI의 신호 처리기/환경 복원 누락을 추가로 재현해 수정했습니다(RED 2개 → 관련 idle 검사 39개 GREEN). 이는 별도 독립 재검토를 받았다고 표현하지 않습니다. 추가 전체 검사에서는 새 테스트의 Ultralytics import가 PIL을 전역 패치하고 교정 테스트 환경값이 남는 순서 의존성을 재현했습니다. 모델 기준 출력 생성은 별도 CPU 프로세스로 격리하고 monkeypatch 수명을 바로잡아 동일 순서 검사 68개를 통과했습니다. 렌더 코드/품질 기준을 수정하지 않았습니다.

최종 검증 수치는 `03-highlight-idle-rotation-validation.json` 및 아래 로컬 증거에 기록합니다. 증거 루트는 Python 작업 트리의 `.implementation-evidence/idle-rotation`, 각 Node 프로젝트의 같은 하위 폴더입니다.

- Python 전체: 3,360개 통과, 6개 실패, 5개 skip. 기존 기준선의 annotation golden 5개와 fadeblack 렌더 1개는 별도 기록하며 신규 실패로 감추지 않습니다.
- NestJS 전체 5,292개 통과, Electron 전체 1,903개 통과. Electron 기본 동시 실행에서 Node 테스트 runner의 파일 메시지 역직렬화 오류가 한 번 발생했고, 파일 단독 검사 및 `--test-concurrency=4` 전체 재검사에서 실제 동일 코드가 모두 통과했습니다. 실패 로그도 보존했습니다.
- Angular Chrome 집중 검사 50개, 스타일 검사 21개 통과. Ruff F 검사 통과.
- 실제 prepared pack의 별도 CPU 작업자에서 24종 입력/72회 실행 및 종료 확인. 실제 owned idle CLI의 foreground 선점·종료·재실행 확인. 이는 모델 GPU 품질/성능 승인이 아닌 소프트웨어 실행 경로 검사입니다.
- 실제 인물 CPU 분석 smoke: 이전 단계와 groups/clips 동일, source 1개, revision 1. 여러 영상의 품질 검증을 대신하지 않습니다.
- Mac arm64 DMG/ZIP 실제 생성, 패키지 Python/Nest/Angular 477개 파일과 Electron 324개 파일의 SHA 일치, 필수 Node 의존성 9개 해석 성공.
- 원본 desktop 네 저장소의 기존 파일·HEAD, 이전에 보존한 사용자 변경 18개, 원본 모델 파일 10개의 SHA 보존을 확인했습니다. 현재 변경은 네 분리 작업 트리에 있습니다. 커밋/푸시는 하지 않았고 기존 실행 앱·공유 가상환경을 교체하지 않았습니다.

## 시험용 산출물

- Mac: Electron 작업 트리 `dist-app/Clipper Studio (dev)-0.0.1-arm64.dmg` 및 `.zip` (미서명 개발 빌드).
- Windows 직접 빌드용: Python 작업 트리 `.implementation-evidence/completion/handoff/clipper-acceleration-source.zip`. 네 프로젝트의 현재 소스·lock·공개 설정/공개키 및 파일별 SHA manifest 포함. 모델/가상환경/로그/개인 시험 자료 제외.
- 사용법: `BUILD-AND-TEST.ko.md`. 검증 결과와 산출물 SHA: `03-highlight-idle-rotation-validation.json`.
