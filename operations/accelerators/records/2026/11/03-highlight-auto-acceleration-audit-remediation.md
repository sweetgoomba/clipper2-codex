# 하이라이트 자동 가속 감사 수정 기록

2026년 11월 3일. [독립 감사 보고서](/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/03-highlight-auto-acceleration-independent-audit.md)의 인증 경계, 결과 버전 일관성, 실제 CPU 복구 연결을 우선 수정했다. 신규 GPU 후보의 인증·활성화는 계속 차단한다. **실제 분석 단위 복구 연결은 대사 플러그인의 분석·STT까지이며, 안무·인물 전체 분석 복구와 실기기 출하 검증까지 완료한 상태는 아니다.**

## 수정 범위와 보존

| 저장소 | 수정 작업트리 | 이번 수정 소스·시험 파일 |
|---|---|---:|
| Python | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` | 29 |
| Nest | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` | 22 |
| Electron | `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103` | 2 |

Python/Nest의 기존 가속 작업트리를 이어 사용했고, Electron은 원본이 clean임을 확인한 뒤 별도 작업트리를 만들었다. 원본 Python/Nest 소스 inventory **2,087개 해시 일치**, 별도로 보존한 기존 변경·모델 파일 **120개 해시 일치**를 확인했다. Electron 원본 Git 상태도 clean이다. 기존 골든, 판단 임계값, 모델 가중치, 전후처리 알고리즘을 새 결과에 맞춰 변경하지 않았다. 이번 전체 시험에서 새로 생성된 CoreML 캐시 19개는 소스 변경 목록에서 제외하고 증거 폴더에 별도 보존했다.

- [원본 소스 보존 확인](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/original-preservation.json)
- [기존 변경·모델 보존 확인](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/original-models-and-dirty-preservation.json)
- [이번 변경 파일과 전후 해시](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/changed-files.json)

커밋·병합·배포·설치된 앱 재시작은 하지 않았다. 코드와 재현 시험은 위 작업트리에 있다.

## 감사 항목별 조치와 증거

| 항목 | 조치 | 재현·회귀 증거 |
|---|---|---|
| F01 인증서 바꿔 쓰기 | 인증서를 모델 ID, backend, pack ID, purpose까지 정확히 결합. 미구현 backend 거부. 기존 필드가 없는 인증서는 차단 | `f01-red.log` 5 실패 → `f01-green.log` 47 통과 |
| G01 품질 판정 | 모델·consumer별 필수 semantic schema 검증. 기록 비교 결과와 출시 판정을 분리. 같은 입력을 반복하거나 semantic 라벨을 꾸며도 **release BLOCKED**. 이 도구는 인증서를 발급하지 않음 | `g01-f10-red.log`, `g01-f10-green.log`, `gates-and-calibration-green.log`, `test_accelerator_recorded_release_safety.py` |
| F10 잘못된 manifest | list/null/잘못된 case·outputs·nested baseline을 이유가 담긴 BLOCKED 결과로 처리. CLI exit 2 | `test_accelerator_release_gate.py`, nested `expected_outputs=[]` 독립 재현과 회귀 |
| F03 결과 버전 혼합 | 요청·stage마다 immutable snapshot 고정. Nest가 Python 성공 revision을 다음 stage에 전달. 이전 job revision이면 실행·CAS 공개 거부 | Python `f03-f04-python-red.log` 2 실패 → `f03-f04-python-green.log` 20 통과. Nest `f03-f04-red.log` → 최종 전체 시험 |
| F04 무결성 | committed JSON은 같은 바이트의 SHA와 JSON을 검증. 손상·누락은 오류로 전달. 영상은 streaming SHA + 제한된 stat-signature 캐시. 논리 경로와 실제 generation 경로 모두 검증. 미공개 `.acceleration` 경로 접근 거부 | `physical-path-red.log`, 양쪽 `test_artifacts`/`committed-artifact-resolver` 회귀 |
| G02 실제 CPU 복구 | 아래 대사 분석·STT 실제 연결 참조. 기존 함수 callback 시험에만 머물지 않도록 앱 dispatch 및 후속 소비자를 연결 | `g02-red.log` → `g02-green.log`, `g02-integration.log`, `owned-process-green.log`, 최종 `final-targeted.log` |
| F02 pack·workload 경계 | 시작한 pack ID/hash와 요청 BackendKey 대조. load 시 workload도 세션에 결합. dynamic ONNX라도 선언 shape/batch와 다른 tensor 거부 | `worker-red.log` → `worker-green.log` 25 통과. 설치된 pack 자체의 attest/manifest 검증은 G03의 남은 작업 |
| F08 잘못된 입력·OOM | 송신 전에 요청을 직렬화·검증해 입력 오류가 worker 종료·CPU 재시도를 유발하지 않음. MemoryError와 알려진 runtime OOM을 `oom`으로 구분 | `test_worker_audit_boundaries.py`, `worker-final.log` |
| F09 인증 대기 | accept와 인증 대기를 제한. 인증되지 않은 accepted socket을 shutdown하고 인증 thread를 정리. 인증 완료 직후의 thread 종료 경합도 보완 | 무응답 peer의 EOF 확인 회귀, `worker-final.log` |
| R03 잘못된 오류 응답 | null/list/알 수 없는 kind 등은 `invalid_output`으로 분류하고 worker 정리 | `test_worker_audit_boundaries.py`의 4개 잘못된 error payload |
| F05 설치 갱신 | 세 하이라이트 plugin의 source fingerprint와 `--reinstall-package`에 accelerators 추가. 코드·catalog만 바뀌어도 재설치, 그대로면 재사용 | Electron `f05-red.log` → 최종 `plugin-venv.test.js`; 세 plugin 각각 실제 ensurePluginVenv 호출 수 검증, uv 실행은 mock |
| F06 작업 순환 | idle 측정의 workload cursor를 유지해 앞쪽 profile의 예산 소진이 뒤쪽을 계속 굶기지 않음 | `f06-f07-r01-red.log` → `gates-and-calibration-green.log` |
| F07 완료 직전 취소 | 마지막 comparator 후에도 취소·foreground·deadline 검사. cleanup 뒤 이미 중단된 측정은 publish하지 않음 | cancel/deadline/foreground 3개 fake-clock 회귀 |
| R01 첫 실행 비용 | 첫 inference의 지연 비용을 측정해 steady median을 뺀 cold overhead에 포함. session의 compile 비용도 보존 | 500ms deferred first-run 주입 회귀 |

Python 로그의 기준 폴더는 [audit-fixes](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes), Nest/Electron 로그는 각각 작업트리의 `.implementation-evidence`다. [항목별 원장](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/ledger.jsonl)에도 상태와 로그명을 남겼다.

## 대사 분석과 STT의 실제 연결

앱의 `run_dialog_stage`에서 `analyze_media`와 `transcribe_media`를 새 owned process로 실행한다. child는 기존 OpenCLIP/CT2 모델 서비스와 기존 분석 알고리즘을 호출한다. 새 ONNX 변환이나 provider를 선택하는 경로가 아니다.

1. 분석을 비공개 generation 안에서 수행한다. 모델 캐시는 child마다 새로 만들어진다.
2. 명시적으로 분류된 backend 오류, 프로세스 충돌·timeout이면 GPU를 요청한 분석에 한해 새 CPU process로 전체 단위를 한 번 재실행한다.
3. 첫 실패 generation을 제거하고 process 종료를 확인한 뒤 CPU를 시작한다. 입력·파일·일반 로직 오류와 취소는 엔진을 바꾸지 않는다. CPU도 실패하면 이전 성공 결과를 유지한다.
4. 성공 응답 파일을 썼더라도 child가 nonzero로 종료하면 성공 공개하지 않는다. 뒤늦은 native 종료 실패 회귀도 추가했다.
5. STT 전용 stage의 MPS 요청은 원래 CT2 동작대로 CPU이다. 이 CPU 실패를 GPU 실패로 오인해 같은 CPU 분석을 다시 하지 않는다. 반환의 `requested_device`는 실제 모든 모델의 GPU 배치를 증명하는 필드가 아니다.
6. LLM 호출은 Nest에 남겨 분석 재시도에서 반복되지 않는다. LLM 응답은 run별 메모리에 보관해 다음 Python stage로 넘기며, 기존 프로젝트의 공개 제목 JSON을 미리 덮어쓰지 않는다.
7. 후보 생성·렌더는 명시적 입력 revision의 JSON만 private generation으로 복사한다. 완료 시 CAS commit하고 다음 소비자는 반환된 revision을 읽는다. 렌더는 CPU 복구 재시도 범위에 포함하지 않는다.
8. 프로젝트 상세, trim 원본 선택, raw clip backfill, dance review 읽기에 snapshot을 연결했다. STT를 재사용하는 Shortform Director 소비자도 반환 revision으로 읽는다.

**검증의 범위:** 실제 파이프라인 함수·generation·Nest 소비자를 통과하는 시험에서는 비싼 native 추론/미디어 작업을 stub했다. 동일한 기존 CPU 파이프라인의 로컬 기대 결과와 분석 JSON을 비교했다. 별도로 실제 자식 process의 정상 종료, cache 초기화, crash, timeout, cancel, 늦은 exit를 확인했다. 이 둘을 실제 GPU/실영상 최종 하이라이트 품질 인증으로 확대하지 않는다.

주요 코드:

- [transactional_stages.py](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/transactional_stages.py)
- [owned_stage.py](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/owned_stage.py)
- [Nest workflow](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts)
- [실제 분석 경로 회귀](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/tests/test_dialog_transactional_analysis.py)

## 검증 결과

| 검증 | 결과 | 해석 |
|---|---|---|
| Python 전체 | **3,090 passed / 6 failed / 7 skipped** | 아래 기존 6개 실패와 assertion 상세 25줄까지 이전 로그와 동일. 마지막 두 경계 수정 전 전체 실행 |
| 마지막 경계 수정 후 Python 대상 전체 | **147 passed** | owned process, 대사 분석·STT·stage 계약, accelerator 전체. 마지막 변경 포함 |
| Nest 전체 | **5,250 passed / 0 failed / 9 skipped** | TypeScript build 통과. 후속 STT revision 소비 회귀 포함 |
| Electron 공식 전체 `npm test` | **1,860 passed / 1 failed** | 기존 fake-updater timer 시험의 `26 !== 1`. 원본 저장소에서 같은 시험·같은 assertion 실패 재현 |
| Electron 설치·패키징 대상 | **28 passed** | 로컬 기존 build fixture를 사용한 staging 시험. 신규 uv 설치나 Windows installer 실행 시험은 아님 |
| Nest bundle | 컴파일 성공 | standalone checkout의 bundled template font 경고가 남음. 앱 출하 패키징 완료 판정은 하지 않음 |
| 세 저장소 diff check | 통과 | Git에 반영되지 않은 새 파일은 별도 변경 목록/해시로 추적 |

Python 기존 실패는 annotation counter/chip/arrow/arrow-above/no-area byte hash와 fadeblack transition이다. [기존 로그와 상세 대조](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/baseline-comparison.json). 이 실패를 숨기기 위해 golden을 갱신하지 않았다.

- [Python 전체 로그](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/full-python.log)
- [최종 대상 147개 로그](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/final-targeted.log)
- [Nest 전체 로그](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/.implementation-evidence/audit-fixes-final-full-node.log)
- [Electron 전체 로그](/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103/.implementation-evidence/audit-fixes-final-full-electron.log)
- [Electron 기존 실패 원본 재현](/private/tmp/clipper-acceleration-electron-original-fake-updater.log)

격리 작업트리의 형제 저장소가 없는 탓에 발생한 초기 Electron fixture 실패는 실제 로컬 Angular 산출물 연결, Nest 작업트리 bundle, 기존 generated config/auth의 로컬 복사 후 해당 시험이 통과했다. 외부 전송은 하지 않았다.

## 독립 재검토

별도 reviewer가 이번 변경을 읽기 전용으로 검토했다. 그 과정에서 기존 제목의 조기 덮어쓰기, 영상의 physical path hash 우회, 반복 입력으로 release PASS, nested baseline 예외, STT 재사용 소비자의 legacy 경로, STT 오류 분류 누락을 추가 발견했고 위 수정에 반영했다. 재검증한 범위에서 남은 P1/P2를 확인하지 못했다는 결과이며, 아래 미구현·미검증 항목이 해소됐다는 뜻은 아니다. [독립 재현 스크립트](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/independent-review). 마지막 device 표기·MPS STT·늦은 종료·인증 socket 변경도 별도 재검토했으며, [최종 독립 회귀 4개가 통과했다](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/independent-review/final-narrow-reverification.log).

## 남은 인수 조건

- **G02 일부:** 안무·인물 전체 분석의 tracker/gallery/reference state 재생성 및 원래 YOLO/OpenCV/AuraFace/SFace CPU factory 연결, 인물 speech 작업 경계까지 같은 복구·공개 계약으로 확대해야 한다. 이번에 그 모델을 새 ONNX 경로로 전환하지 않았다.
- **G01 출시 기준:** 실제 원본 영상·참조 얼굴·승인 baseline·3회 반복·최종 인물/클립/순서/자막 golden과 배포 fixture 권리·용량·coverage가 필요하다. 기록 JSON의 schema와 해시만으로 이를 인증하지 않는다.
- **G03/G04:** native Apple/DXGI 환경 탐지, 정확한 pack 설치·검증, host GPU lease·CPU admission, 사용자 진단/UI 연결은 남아 있다.
- **R02:** POSIX process group을 벗어나 새 session을 만든 후손까지 host가 소유·회수한다는 보장은 없다. Windows Job Object, 부모 native hang/정지, sleep/wake 등 실기기 검증이 필요하다.
- **R04:** 현재 calibration의 CPU/GPU 측정은 순차 trial이다. 교차 round와 전후처리·IPC·shot aggregation을 포함한 실제 성능 인수, 전체 앱 5% 회귀 gate는 남아 있다.
- Windows x64 GPU/CPU-only와 Apple Silicon 실제 모델·실영상, 설치본 업데이트·offline·rollback 시험이 통과하기 전 **신규 GPU 인증/활성화와 출하는 BLOCKED**다. Windows ARM과 Intel Mac은 이번 지원 범위에 추가하지 않았다.

## 변경 전달 자료

아래 patch는 원본 checkout에 보존된 사용자 변경을 기준으로 이번 가속 작업 전체를 비교한 자료다. 현재 dirty HEAD 전체 diff를 이번 수정이라고 간주하지 않는다.

- [Python 누적 patch](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/clipper-python-cumulative.patch)
- [Nest 누적 patch](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/clipper-nestjs-cumulative.patch)
- [Electron patch](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/audit-fixes/clipper-electron-cumulative.patch)
