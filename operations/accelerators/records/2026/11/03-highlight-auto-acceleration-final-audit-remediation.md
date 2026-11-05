# 하이라이트 자동 가속 최종 독립 감사 후 수정 결과

2026-11-03. Apple Silicon Mac과 Windows x64가 대상이다. 최종 독립 감사의 실제 설정 연결·GPU 소유권·CPU 선택·시험 판정 결함을 수정하고, 기존 작업과 모델 품질 계약을 보존한 상태로 재현·회귀 검사와 Mac 재패키징을 수행했다. **F01–F04, F06–F12의 코드 결함을 수정했다. F05는 시간 예산 전파를 수정했으며 idle 교정·다중 어댑터 순환은 남아 있다. R01/R02의 출하 승인 자료·실기기 품질 검증도 남아 있다.**

이전 완료 기록은 최종 독립 감사 이전의 상태다. 현재 상태는 이 기록과 아래 검증 JSON을 기준으로 읽는다. 원래 독립 감사 보고서는 수정하지 않았다.

## 수정과 재현 증거

경로 약어:

- P: `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103`
- N: `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103`
- E: `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103`
- A: `/Users/jina/project/adlight/.worktrees/clipper-angular-accelerators-20261103`
- Q: P의 `.implementation-evidence/final-audit-fixes`

| 감사 항목 | 최종 변경 | 재현과 수정 후 검사 |
|---|---|---|
| F01 실제 workflow가 설정 우회 | 실제 안무·인물 executor factory와 대사 stage runner에 설정 서비스를 주입했다. runtime 준비·취소 확인 후 제출 직전에 서버 소유 설정/일회용 시험을 고정하고, 완료 이벤트에서 보고서를 저장한다. 시작 실패는 예약을 소비하지 않는다. | N `final-audit-workflow-red.log`: 실제 factory에서 CPU 설정 무시 재현. `final-audit-workflow-green.log`: factory/실제 stage runner → HTTP 제출 → WebSocket 완료 → 보고서 연결 검사 17개 통과. 이후 통합 집중 검사 31개 통과. |
| F02 heartbeat 만료 시 살아 있는 GPU 소유자 예약 회수 | heartbeat 만료는 stale 상태다. owner/등록 worker 종료를 확인하기 전 다른 작업을 들이지 않는다. native 메모리는 owner가 죽기 전까지 명시 release 후에도 유지한다. EPERM은 종료 증거로 보지 않는다. Python remote worker의 실제 PID를 등록하고 host는 owner의 자손인지 검사한다. | E `final-audit-leases-red.log`: 살아 있는 owner의 만료 후 새 acquire 200 재현. `final-audit-native-release-red.log`, `final-audit-owner-proof-red.log`. 최종 `final-audit-owner-proof-green.log`: 소유권/준비 회귀 11개 통과. 실제 절전/Windows 드라이버 시험을 대신하지 않는다. |
| F03 CPU를 승자로 선택하지 못함 | CPU·기존 GPU·신규 후보가 동일한 품질·중앙값·p90·로드/작업량 비용 정책으로 경쟁한다. CPU가 이기면 다음 분석 단위 시작에 CPU를 고정하고 원래 CPU 결과를 반환한다. 분석 중 임베딩 경로를 섞지 않는다. | Q `model-policy-red.log` → `model-policy-green.log`; `test_cpu_wins_and_is_pinned_only_at_the_next_unit_start`. 주입 clock으로 CPU 1ms/기존 GPU 10ms/후보 20ms 재현. 이 수치는 실제 기기 속도가 아니다. |
| F04 부족한 근거·성능 회귀도 PASS | benchmark는 원래 소스/영상/옵션/원래 결과·3회 시간의 schema2 동결 baseline을 실제로 해시 확인한다. 현재 CPU/후보/원래 결과를 독립 비교한다. 필수 consumer/backend/shape/전처리/각 round 실제 실행, 다양한 표본, 전체 시간 5% 회귀 한도가 결과와 exit code에 반영된다. 대사 CPU 공개 시 별도 후보 JSON 증거를 검증한다. | Q `benchmark/verification.json`: RED 로그 7종, 집중 검사 81개 통과. 원래 감사의 “없는 baseline + 모델 미실행 + 100배 느림” probe는 이제 BLOCKED/exit 2다. 출하 승인을 만드는 명령은 아니다. |
| F05 후보 시간 예산이 load/export/infer에 미전달 | 후보 준비/export에 별도 상한을 두고, 실제 비교에 쓴 시간과 기존 분석 시간을 분리했다. 남은 비교 예산을 worker 시작/load/infer에 전달한다. 예산 소진은 일시적 보류다. | Q `model-policy-red.log`, `load-diagnostics-red.log` → GREEN. 남은 3초에서 deadline 103으로 제한하는 clock 회귀 포함. **현재 제품 정책은 bounded_foreground_trial이다. idle corpus 교정과 다중 어댑터/실행기 순환은 미구현이다.** |
| F06 품질 재검사 성공 뒤 격리 잔류 | 충분한 다양성/표본과 최종 결과 검사를 갖춘 명시 재평가만 로컬 quality/invalid-output 격리를 해제한다. 음성은 실패 전 측정치를 버리고 서로 다른 PCM·전사 결과의 새 비교가 필요하다. release 인증은 별도 유지한다. | Q `model-policy-red.log` → GREEN. 시각 입력 33회/24종 및 음성 PCM 3종·전사 3종·각 3회 비교 조건 검사. |
| F07 기존 GPU 모델 메모리 예약 0 | 기존 모델도 첫 입장부터 모델별 보수적 예약을 한다. 같은 adapter의 추가 생존 모델은 reserve를 누적하며 동일 모델 재호출은 중복 합산하지 않는다. Whisper도 최소 예약을 둔다. | Q `load-diagnostics-red.log` → `load-diagnostics-green.log`. 첫 모델 acquire 100, 재사용 추가 없음, 다음 모델 reserve 200 검증. 예약량은 추정치이며 실제 peak 측정 결과로 표시하지 않는다. |
| F08 후속 대사 단계가 분석 진단 덮어씀 | job/stage/revision별 보고서를 보존하고 모델 없는 build/render가 최신 분석 진단을 지우지 못하게 했다. CPU 재분석 표시는 commit 전에 디스크에도 기록한다. 대사 후보 분석 JSON은 정규화·SHA와 함께 해당 revision의 `validation/candidate`에 보관한다. | N 실제 후속 stage 연결 회귀, Q `disk-diagnostic-red.log`의 디스크 필드 누락 재현 → 최종 전체 통과. `test_dialog_transactional_analysis.py`의 committed 후보 증거/해시 검사 포함. |
| F09 실제 실행과 요청 경로 혼동 | ONNX 요청 EP, 실제 profile node 수, mixed graph를 구분한다. 기존 provider 확인만 있는 경로는 provider_only다. Whisper CUDA는 실제 CTranslate2 runtime device를 확인한다. Core ML partition을 물리 GPU 증명으로 표시하지 않는다. UI도 선택 경로와 시험 실행 근거를 나눠 보여 준다. | Q `load-diagnostics-*`, benchmark 실행 증거 회귀; A `final-audit-speech-evidence-ui.log`: 실제 Chrome 38개 통과. |
| F10 부팅 시 optional 실행기 자동 설치 | 부팅은 호환성/이미 준비된 immutable pack 검사만 한다. **추가 실행기 준비** 요청이 설치를 시작한다. 기존 CPU/MPS/CUDA 탐색은 optional pack 설치와 분리돼 있다. | E `accelerator-runtime-preparation.test.js`, agent 준비 정책 RED/GREEN. 설치/child/network 없는 inspect 경로 및 준비된 pack의 정확한 identity 검사. |
| F11 revision마다 원본 영상 중복 | 원본은 `.acceleration/sources/<SHA>/original...`에 한 번 저장하고 revision은 정확한 hash/reference를 pin한다. mutable 입력과 hardlink하지 않는다. retry/CPU 기준 분석도 같은 원본을 사용한다. Python/서버 resolver 모두 hash와 경로를 확인하며 과거 per-generation 결과도 읽는다. | Q `source-storage/results.json`: Python 48개/서버 14개 통과. 실제 동일 인물 영상 2회 분석에서 revision 2, 원본 1개, 기존 인물 그룹·클립 동일(`native-source-smoke.json`). |
| F12 기존 GPU 로드/최초 smoke가 watchdog 밖 | 기존 얼굴 ORT 생성과 AuraFace 최초 smoke, CLIP 장치 이동에도 소유 프로세스 내 load watchdog을 건다. 작업별 메모리 identity와 실패 정보를 CPU 재분석 경계까지 전달한다. | Q `load-diagnostics-red.log` → GREEN. 생성/최초 smoke 시점에 Timer가 이미 활성인지 검사한다. 실제 native hang·Windows Job 종료는 실기기 검증 항목이다. |

최종 교차 검토에서 추가로 발견한 두 회귀도 수정했다. 시험 종료 뒤 남은 deadline이 장기 정상 추론을 끊는 문제는 선택된 후보에서 trial deadline을 해제했다(`selected-deadline-red.log` → GREEN). 과거 cache의 빠른 load가 현재 느린 cold load를 가리는 문제는 현재 load 비용을 반영했다(`cold-load-red.log` → GREEN). 두 항목을 포함한 최종 정책/라우터 검사 17개가 통과했다. 검토자가 수정 후 다시 재검토한 것으로 표시하지 않는다.

## 품질과 기존 변경 보존

모델 가중치, 입력 정렬·색·스케일, Ultralytics 전후처리, 샘플링, 사람/안무 판정 임계값, CLIP 정규화/샷 집계, Whisper small/beam 5/VAD off/word timestamps/chunking을 속도를 위해 바꾸지 않았다. Mac Whisper는 CPU를 유지한다. SAM/OCR는 계속 비활성이다. 품질 비교 실패를 성공으로 바꾸거나 허용 오차를 넓히지 않았다.

Q `before.json`은 수정 전 네 작업 트리와 원본 네 저장소의 파일 SHA/HEAD다. 수정 전 소스 ZIP도 `before-source.zip`으로 보존했다. 최종 `preservation.json`에서 원본 네 저장소의 기존 파일·HEAD가 모두 같고, 앞서 병합/보존한 사용자 변경도 일치한다. 원본 모델 가중치 파일 10개가 초기 SHA와 같다. 기존 설치본/실행 중 앱/공유 venv를 교체·동기화하지 않았다. 커밋·push는 하지 않았다.

실제 인물 CPU 분석을 같은 영상에서 두 번 실행해 이전 단계의 그룹/클립 결과와 비교했다. 이는 공유 원본 보관과 CPU 경로의 smoke 증거다. 다양한 인물·안무·대사 영상의 출하 품질 합격을 의미하지 않는다.

## 최종 검사 결과

| 검사 | 최종 결과 | 증거 |
|---|---|---|
| Python 전체 | 3,251 passed, 6 failed, 5 skipped | Q `full-python-frozen.log`; `python-baseline-comparison.json`에서 기존 6개 실패 ID 집합과 일치 |
| Python 가속/복구/품질 집중 | 265 passed; 이후 추가 정책/라우터 17 passed | Q `final-focused-green.log`, `cold-load-green.log`; 추가 두 테스트는 최종 전체에도 포함 |
| Python 정적 검사 | All checks passed | Q `ruff.log` |
| NestJS 전체 | 5,271 passed, 0 failed | N `.implementation-evidence/final-audit-full-node.log` |
| Electron 전체 | 1,874 passed, 1 failed | E `.implementation-evidence/final-audit-full-electron.log`; 기존 fake-updater 시간 mock 26!=1 실패. 무관한 테스트/허용값을 수정하지 않음 |
| Angular 설정/실행 증거 | 실제 Chrome 38 passed | A `.implementation-evidence/final-audit-speech-evidence-ui.log`; 스타일 검사와 packaged 빌드도 통과 |
| Mac arm64 패키지 | DMG/ZIP 생성 성공, 미서명 개발 앱 | E `.implementation-evidence/final-audit-mac-package-final.log` |
| 패키지 코드 대조 | Python/NestJS/renderer 470개 + Electron 316개 일치, 필수 의존성 9개 해석 성공 | Q `packaged-source-check.json`, E `final-audit-packaged-electron.json`, `final-audit-packaged-dependencies.json` |
| Windows 실기기/다양한 GPU 속도 | 미검증 | Windows x64 소스/lock/빌드 안내 제공. 사용자 기기 시험 필요 |

Python의 기존 실패는 annotation renderer golden 5개와 fadeblack transition 1개다. Electron의 이전 POSIX 소유 프로세스 간헐 실패는 이번 전체 실행에서는 통과했다. 전체 검사가 모두 성공했다고 표시하지 않는다. 실패한 시험을 wrapper의 프로세스 exit 0만으로 합격 처리하지 않았다.

## 직접 시험할 산출물과 남은 일

Mac DMG: E의 `dist-app/Clipper Studio (dev)-0.0.1-arm64.dmg`. Windows 전달용 최종 소스: P의 `.implementation-evidence/completion/handoff/clipper-acceleration-source.zip`. 사용 방법은 같은 기록 폴더의 `03-highlight-auto-acceleration-device-build-guide.md`다. 소스 ZIP에는 현재 코드/lock/공개 배포 설정과 SHA manifest를 넣으며 모델·개인 환경설정·가상환경은 제외한다.

현재 **설정 → 분석 가속 → 이 기기 시험**은 다음 분석에서 실제 후보와 CPU를 비교하는 개발용 기기 시험이다. CPU 설정은 실제 workflow에도 적용된다. 실행기 준비 전 CPU 분석을 위해 optional 실행기를 자동 내려받지 않는다. 후보가 실패하면 소유 프로세스를 정리한 뒤 새 CPU 프로세스에서 분석 단위를 한 번 다시 수행하고, 완성된 결과만 새 revision으로 공개한다. 파일을 원래대로 되돌린다는 의미의 복구가 아니다.

남은 F05/R01/R02는 다음과 같다.

- idle corpus 교정과 여러 GPU/실행기 후보를 순환해 비교하는 제품 경로는 아직 없다. 현재 명시 시험은 제한된 foreground 비교다.
- 새 ONNX 경로의 일반 자동 적용에는 정확한 모델/프로필/기기 범위의 release catalog와 로컬 품질·속도 근거가 필요하다. 현재 출하용 catalog는 비어 있다. 로컬 시험 PASS가 그 권한을 만들지 않는다. 기존 CPU/MPS/CUDA는 유지한다.
- 사용자의 실제 Mac/Windows 영상에서 cold/warm 3회, 필수 모델·프로필별 실행/품질/전체 시간과 고장 후 CPU 결과를 채워야 한다. 다양한 Windows GPU, 낮은 메모리, 한국어 경로, 오프라인, OOM/crash/hang, 절전/복귀는 이번 Mac 회귀 검사로 합격 처리하지 않았다.
- 대사 benchmark는 분석 JSON/STT/CLIP 단계까지 비교한다. 원격 LLM의 최종 컷 선택과 렌더는 같은 입력/설정으로 별도 인수해야 한다. 실제 peak 메모리도 기기 측정이 필요하다.

이 제한을 숨기거나 인증 gate를 풀어서 “모든 환경의 가장 빠른 자동 가속 완료”로 만들지 않았다. 이번 산출물은 확인된 결함을 수정한 Mac 시험 앱과 Windows 소스이며, 출하 승인 완료본과 구분한다.
