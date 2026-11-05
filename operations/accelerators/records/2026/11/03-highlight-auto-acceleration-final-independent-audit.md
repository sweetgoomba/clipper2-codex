# Clipper 하이라이트 자동 가속 — 최종 독립 감사

감사일: 2026-11-03 KST. 대상: 지정된 4개 분리 작업 트리의 현재 미커밋 소스와 최종 전달물. 구현 코드는 수정하지 않았다.

## 판정

**현재 전달물은 소스 전달·제한된 개발자 실험에는 사용할 수 있지만, 설정 화면을 사용하는 일반 사용자의 기기 인수 시험 준비는 미완료다.** 가장 먼저 고쳐야 할 문제는 실제 세 하이라이트 작업 경로가 새 설정 서비스를 우회한다는 점이다. CPU 설정·다시 최적화 예약·완료 진단은 화면/API/개별 runner 테스트에 존재하지만 일반 workflow에 연결되지 않는다(F01). 살아 있는 GPU 소유자의 lease를 heartbeat 만료만으로 회수하는 결함(F02), 더 빠른 CPU를 자동 선택하지 못하는 실제 선택 경로(F03), 부분 실행·성능 회귀를 기기 시험 PASS로 표시하는 판정(F04)도 확인했다.

새 ONNX 후보를 인증 없이 일반 자동 실행에 넣지 않는 것은 **의도한 품질 보호**다. 이를 풀어 해결하면 안 된다. 다만 현재 release catalog와 출하 corpus/기기 매트릭스가 없으므로 “여섯 모델의 환경별 자동 최적화 완료”로 인수할 수 없다(R01/R02). Mac Whisper CPU 유지도 품질 계약 보존으로 타당하며, Mac 음성 GPU 가속 구현 완료를 뜻하지 않는다.

확정 코드 결함/동작 불일치 F01–F12와 요구 미충족 R01–R02를 아래에 구분했다. P0는 확인하지 못했다. 실기기 성능·Windows 동작은 이번 감사에서 합격 처리하지 않았다.

## 1. 범위, 안전 제한, 변경 출처

경로 약어는 다음 절의 파일/줄 표기에 적용한다. 모두 절대 경로의 실제 작업 트리다.

| 약어 | 작업 트리 | 기준 HEAD |
|---|---|---|
| P | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` | `4b54bced17e13aadbeb97be75259b7f7213a9b24` |
| N | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` | `e4e1fcf5d37bdbbd2c0c00a9f558b052c2d55f7f` |
| E | `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103` | `775ffd5e7df8bede6a9096316a7a367da8dba0da` |
| A | `/Users/jina/project/adlight/.worktrees/clipper-angular-accelerators-20261103` | `7a186b00907859aa9376b79211e593a2abd52afb` |

`.codex/AGENTS.md`、`.codex/README.DOCS.md`와 네 저장소의 `CLAUDE.md`를 확인했다. 감사에는 pragmatic-coding-guardrails, dispatching-parallel-agents, verification-before-completion을 적용했다. 원래 design/implementation-plan을 기준으로 코드를 추적한 뒤 completion 설명과 대조했다. 구현·테스트·배포를 새로 수행한 것으로 과장하지 않았다.

새 앱 실행/공유 프로필 사용/실행 중 프로세스 종료/venv 동기화/모델 설치·변경/GPU 시험/전체 pytest/CPU 성능 측정은 하지 않았다. 원본 venv는 설치된 라이브러리 읽기와 다섯 개의 mock 회귀 함수 실행에만 사용했다. 모든 별도 출력은 `/private/tmp/clipper-final-audit-20261103-root`에 두었다. 소켓 없는 가짜 요청, fake host, mock clock을 이용했다. 이 증거는 실기기 속도를 측정하지 않는다.

**HEAD diff 전체를 이번 구현으로 보지 않았다.** `final-changes.json`의 113개 기록 중 14개는 동시 사용자 변경 보존 표시가 있다. `current-work-merge/manifest.json`의 9개 병합 결과와 `new-user-files-sha.json`의 새 사용자 파일 5개를 현재 소스 해시와 대조해 일치했다. 안무 pipeline의 clean three-way merge, 나머지 copy_new_user_change 기록을 구분했다. 원본 비교의 9개 mismatch는 동시 사용자 변경 기록으로 설명되며, 원본 손상의 근거로 사용하지 않았다. Angular 기존 overlay 작업도 이번 가속 구현으로 평가하지 않았다.

## 2. 확정 발견

### F01 · P1 · 기능 연결 결함 — 실제 workflow가 CPU 설정·시험 예약·완료 보고를 우회한다

- **파일/줄:** N `src/modules/workflows/infrastructure/python-plugin-workflow-executor.ts:75`(특히 82), factory `:235–242`; N `src/modules/dialog-highlight/application/dialog-highlight-python-stage.runner.ts:27–28`; N `src/modules/plugins/application/local-plugin-job.runner.ts:51,67,73`.
- **조건/실제 동작:** 안무·인물의 factory가 생성한 executor는 `context.params`를 그대로 POST한다. `AccelerationSettingsService.snapshot/record`가 없다. 대사는 `new LocalPluginJobRunner(host,lifecycle)`로 세 번째 acceleration 의존성을 생략한다. 해당 runner의 snapshot/record는 optional 의존성이 있을 때만 호출된다. 전체 src 검색에서 이를 보완하는 별도 호출을 찾지 못했다.
- **영향:** UI에서 CPU 저장 성공 후에도 일반 작업은 기본 auto/기존 GPU를 사용할 수 있다. 다시 최적화 예약은 다음 작업에서 소비되지 않는다. 완료 report API도 업데이트되지 않는다. 사용자가 제시한 가장 직접적인 제어 계약이 충족되지 않는다.
- **증거:** `workflow/reproduction.json` 및 `reproduce.cjs`. 실제 compiled executor에 fake host/submit/watch를 주입한 결과 dance/person 제출 params는 `{video_path:"audit.mp4"}` 그대로였고 대사 내부 runner의 acceleration은 undefined였다. 원문 TS와도 대조했다. 실제 앱은 실행하지 않았다.
- **최소 수정 방향:** 실제 factory/runner의 DI를 연결해 모든 하이라이트의 제출 직전에 서버 소유 설정을 고정하고 완료 보고를 보존한다. 회귀는 설정 API만 시험하지 말고 실제 workflow factory → 제출 params → 1회 예약 소비 → 완료 report를 이어 검증해야 한다. 기존 executor 파일이 HEAD 대비 미변경인 것은 보존 위반이 아니라 통합 누락이다.

### F02 · P1 · 자원 소유권 결함 — heartbeat 만료만으로 살아 있는 owner의 lease를 삭제한다

- **파일/줄:** E `src/main/accelerators/leases.ts:20,32,43–47`; P `clipper_accelerators/clipper_accelerators/lease_client.py:41–53`.
- **조건:** 절전/복귀, heartbeat thread 지연, 브리지 일시 정지 등으로 15초 TTL이 지난다.
- **영향:** `expire()`는 `expires < now || !alive(owner)`로 삭제한다. 기존 GPU 호출·메모리가 남아 있어도 다음 작업이 같은 adapter를 획득할 수 있다. 원래 설계의 “heartbeat 부재만으로 메모리 회수로 간주하지 않음”을 위반한다.
- **증거:** 살아 있는 현 PID를 owner로 한 소켓 없는 handler 재현: 최초 acquire 200 → 만료 전 재획득 409 → expires만 과거로 주입 → 새 acquire 200 → 이전 validate 410. `workflow/reproduction.json`에 기록했다. 실제 sleep/GPU 장애는 주입하지 않았다.
- **최소 수정 방향:** 만료는 stale 상태로 처리하고 owner 및 등록 worker 종료가 확인될 때까지 exclusive reservation을 유지한다. 강제 회수가 필요하면 소유 프로세스 정리·종료 확인을 먼저 한다. TTL 연장만으로는 해결되지 않는다.

### F03 · P1 · 선택 결함 — 실제 ModelGate는 더 빠른 CPU를 선택할 수 없다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/runtime.py:164,185–194`; 실제 연결 P `.../yolo_adapter.py:165`, `.../clip_adapter.py:52`.
- **조건:** CPU·기존 MPS/CUDA·새 후보를 모두 측정했지만 CPU가 가장 빠르다.
- **영향:** 추천은 후보가 incumbent보다 빠르면 후보, 아니면 incumbent뿐이다. CPU 측정값은 있지만 CPU를 승자로 고르는 분기가 없다. “CPU가 무조건 GPU보다 느리다고 가정하지 말라”는 요구를 충족하지 못한다. 공통 `selection.select_backend()`에는 더 넓은 비교가 있지만 실제 제품 caller가 없다(F05).
- **증거:** mock clock과 서로 다른 34 입력으로 CPU 1ms / 기존 MPS 10ms / 후보 20ms를 제공해 실제 ModelGate를 호출했다. 결과는 `no_material_gain`, selected/recommended `torch_mps`였다. `model/cpu-faster-than-incumbent.json`. 속도 수치는 재현을 위한 주입값이며 기기 성능 측정이 아니다.
- **최소 수정 방향:** CPU·기존 경로·새 후보를 동일 품질·load/compile/IPC/p90·작업량 비용으로 비교하고 분석 단위 시작 시 승자를 고정한다. 기존 GPU도 비교에서 제거하지 않는다.

### F04 · P1 · 시험 판정 결함 — 성능 회귀와 미실행 모델을 포함해 기기 시험 PASS가 가능하다

- **파일/줄:** P `scripts/accelerators/benchmark_app.py:13–15,61–77`, `:21,75`; P `clipper_accelerators/clipper_accelerators/verification.py:6–35`.
- **조건/실제 동작:** required_models는 보고서에 이름이 존재하는지만 확인한다. calls=0, CPU 유지, quality_failed, 표본 부족도 coverage에 포함된다. require_gpu는 각 비교 row에서 모델 하나의 실행만 요구한다. 5% 회귀 조건은 계산하지만 device_test_status/exit code에 반영하지 않는다. `--baseline`은 읽거나 해시 검증하지 않고 경로만 보관한다.
- **영향:** 하이브리드 시험 출력과 전체 CPU의 결과가 같다는 제한된 확인이, 필수 모델 경로·성능까지 기기 시험 PASS인 것처럼 소비될 수 있다. 고정된 원래 baseline과 새 CPU 사이의 회귀도 이 명령으로는 확인하지 못한다.
- **증거:** 실제 `main()`에 가짜 analysis process/snapshot을 주입했다. CPU 1초 / 후보 100초, required YOLO calls=0/CPU + YuNet GPU 1회, 존재하지 않는 baseline을 제공해도 `coverage_complete=true`, `device_test_status=PASS`, exit 0이었다. `timings.within_five_percent=false`와 `release_status=BLOCKED`는 그대로 남았다. `probe_benchmark.py`, `benchmark-probe-result.json`.
- **실제 보관 증거의 해석:** `completion/person-coreml-result.json`도 최종 비교 PASS이지만 YOLO는 raw quality_failed/CPU, YuNet은 12 distinct inputs/deferred_budget, Whisper는 CPU다. completion 본문은 이 한계를 적었으므로 이를 허위 GPU 전모델 합격으로 단정하지 않는다. 다만 benchmark의 합격 조건은 고쳐야 한다.
- **최소 수정 방향:** 결과 동등성·모델/프로필별 실제 실행·표본 충족·성능·기기 지원 판정을 분리한다. 필수 model/consumer/backend/shape/각 round의 실행과 품질·측정 충족을 검사하고 성능 회귀는 실패/보류로 반영한다. baseline은 실제 frozen 소스/출력과 결합해 실행·검증해야 한다. release BLOCKED 보호는 유지한다.

### F05 · P2 · 정책 통합 누락 — idle calibration/후보 회전/엄격한 시간 예산은 제품 경로에 적용되지 않는다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/calibration.py:65–174`, `selection.py:27–51`; 실제 P `runtime.py:166–202`, `onnx_adapter.py:48–52`; A `src/shell/settings/acceleration-settings-card/acceleration-settings-card.component.html:9`.
- **조건/영향:** calibrate/select_backend의 production caller가 없다. 현재는 foreground 분석 중 CPU → incumbent → 후보를 실행하는 ModelGate다. idle 선점·후보 최대 2개/나머지 회전·교차 3 round를 검사한 공통 함수 테스트는 앱에서 그 정책을 사용한다는 증거가 아니다. UI는 다음 영상에서 비교한다고 적어 현 동작 변경을 어느 정도 설명하지만, 원래 계획의 idle 정책과는 다르다.
- **시간 경계:** 30/120초 검사는 CPU/incumbent 호출 뒤, 후보 호출 전에만 한다. 이후 load 60초 + infer 30초에 남은 전역 예산이 전달되지 않는다. 앞단 처리가 이미 120초를 쓰면 미시험이고, 잔여 1초에서도 후보 load/infer가 크게 초과할 수 있다. export 준비도 이 제한된 trial 밖이다.
- **증거/미검증:** caller 검색과 시간 경계 코드 확인. 실시간 timeout/부하 측정은 하지 않았다.
- **최소 수정 방향:** 공통 정책을 실제 실행 경로에 연결하거나 제품 정책을 명시적으로 재정의하고 인수받는다. 부모 deadline을 load/export/infer에 전파하고 deferred/회전 상태를 영속화한다. 분석 중 전체 하이라이트 계산에 필요한 시간과 후보 비교 예산을 구분한다.

### F06 · P2 · 복구 동작 불일치 — 재검사 성공 뒤에도 품질 quarantine가 남는다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/verification.py:62–67`; `cache.py:111–130,149–154`.
- **조건:** 동일 key에 quality_failed(또는 invalid_output) 격리가 있고 명시 재검사에서 다양성/표본 조건과 최종 의미 비교를 통과한다.
- **영향:** 새 measurement는 저장되지만 write가 quarantine를 보존하고 finish_measurements는 세 가지 runtime 오류만 해제한다. 이후 cache.read는 None이다. 사용자는 “다시 최적화 성공”과 실제 지속 차단이 다른 상태를 만날 수 있다.
- **증거:** `model/quarantine-after-explicit-success.json`: measurement_stored=true, quarantine_after_explicit_success=quality_failed, eligible_measurement=false. 새 build/key에서는 별개이며, 미인증 local 성공이 release 권한을 만드는 문제와 혼동하면 안 된다.
- **최소 수정 방향:** 승인 범위를 유지한 정식 재평가 상태·복구 절차를 만들고 계속 격리 중임을 명시한다. 단순 local PASS만으로 release gate를 해제하지 않는다. 충분한 재검증을 요구하는 정책이면 버튼 결과에도 이를 반영한다.

### F07 · P2 · 메모리 admission 누락 — 기존 GPU 모델은 예약량 0으로 들어간다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/native_sessions.py:19–26`; E `src/main/accelerators/leases.ts:21–24,41,48–51`.
- **조건/영향:** 기본 auto가 보존하는 기존 Torch/ORT 모델의 첫 입장은 `HostLease.acquire(adapter,0)`이다. 같은 adapter의 후속 native 모델도 추가 reserve하지 않는다. 새 remote의 예약 합산 테스트와 달리, 기존 모델들의 실제 동시 생존 메모리는 반영되지 않는다. 낮은 RAM/VRAM에서 입장 후 OOM·CPU 전체 재실행 비용을 겪을 수 있다.
- **증거/미검증:** literal 0과 reserve 부재를 코드에서 확인했다. 실제 메모리 압박 시험은 하지 않았다. 다른 plugin 수준 입장 제한이 이 모델별 0 예약을 보완한다는 증거는 확보하지 못했다.
- **최소 수정 방향:** 모델별/동시 생존 peak를 예약하고, unknown은 설계의 보수적인 단일 worker/제한된 probe 정책으로 처리한다. 파일 크기 배수만으로 실제 peak 검증을 대체하지 않는다.

### F08 · P2 · 완료 진단 손실 — 연결 수정 후 대사 후속 단계가 분석 보고서를 덮어쓴다

- **파일/줄:** N `src/modules/resources/application/acceleration-settings.service.ts:39–42`; P `plugins/dialog_highlight/dialog_highlight/services/transactional_stages.py:132,144–145`; A `src/shell/settings/acceleration-settings-card/acceleration-settings-card.component.html:20–28`.
- **조건:** F01을 고친 후 정상 대사 workflow가 analyze → build_candidates → render_highlights로 진행한다.
- **영향:** 후속 stage도 빈 models 보고서를 반환하고 record가 무조건 latest를 교체한다. 최종 UI에서 모델 실행·CPU 복구·품질 비교가 사라진다. 현재는 F01에 가려진 잠재 결함이다.
- **증거:** isolated service.record 재현에서 models 1 / cpu_reanalysis true / validation PASS가 빈 후속 보고서 저장 뒤 0 / false / null로 바뀌었다. `workflow/reproduction.json`.
- **최소 수정 방향:** job/stage/revision별 진단을 보존하고 workflow 완료 시 분석 보고서와 복구 이력을 합친다. 빈 비모델 stage 보고서로 분석 기록을 대체하지 않는다. 대사 retry에서 value에 추가한 복구 필드는 디스크 `acceleration.json`에도 commit 전에 반영해야 한다(`transactional_stages.py:92–93`).

### F09 · P2 · 진단 불완전 — mixed graph와 legacy GPU 증거 범위를 구분하지 않는다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/onnx_adapter.py:54–58`; `worker.py:127–139`; `runtime.py:213–221`; P `plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:77–80,184–186,238–240`.
- **확인된 보호:** 새 RemoteInference는 실제 원하는 EP의 graph node가 0이면 거부한다. provider가 설치됐다는 이유만으로 새 후보를 성공 처리하는 문제는 이 경로에서 막았다.
- **남은 조건/영향:** CPU와 GPU 양쪽 node가 있는 profile도 최종 ModelGate 진단에는 단순 ort_* backend로 전달된다. mixed/partition 수가 공개되지 않는다. 기존 dance 경로의 gpu_calls는 provider 목록/성공한 Run 기준으로 집계하므로 실제 GPU node 배정과 동일한 증거가 아니다.
- **증거/미검증:** 정적 추적 및 보관 ORT profile 구조 확인. 모든 기존 경로의 실제 CPU-only partition 실행은 새로 시험하지 않았다.
- **최소 수정 방향:** requested/actual/graph mixed와 profile 확인 여부를 분리해 결과·UI로 전달한다. legacy provider 이름만 확인한 실행은 검증된 GPU 사용으로 집계하지 않는다.

### F10 · P2 · 설치 정책 불일치 — 명시 준비와 무관하게 앱 부팅 때 optional 실행기를 설치한다

- **파일/줄:** E `src/main/main.ts:381–382`; E `src/main/accelerators/runtime-packs.ts:43–48,76–82`.
- **조건:** 지원 플랫폼 앱 시작, 실행기 캐시 없음 또는 build identity 변경.
- **영향:** `prepare()`가 CPU 설정/준비 버튼/설치 동의 확인 없이 관리 venv와 ORT lock pip sync를 시작한다. CPU-only 새 PC도 네트워크·디스크 사용/실패를 겪는다. 원래 계획의 기존 동의·진행 UI 재사용과 다르다. 비동기 실패를 흡수하므로 이것만으로 CPU 분석이 막히는 결함이라고 판단하지는 않는다.
- **증거/미검증:** 정적 호출 경로 확인. 실제 다운로드/설치를 하지 않았다.
- **최소 수정 방향:** 부팅에는 기존 상태/호환성만 확인하고, 다운로드는 저장된 동의 정책 또는 실행기 준비 요청에서 수행한다. 진행·실패·재시도를 연결한다. Windows packaged Python bootstrap은 main.ts:340–353의 기존 준비 후 :373에서 전달되므로, bootstrap 부재를 별도 확정 결함으로 올리지 않았다.

### F11 · P2 · 저장·성능 부작용 — 인물 재분석마다 원본 영상이 generation에 복제·잔류한다

- **파일/줄:** P `clipper_accelerators/clipper_accelerators/visual_unit.py:46–55,65–72,106–107`; P `plugins/person_highlight/person_highlight/app.py:277–287`; P `clipper_accelerators/clipper_accelerators/artifacts.py:150–165`.
- **조건/영향:** 기존 copy2 루틴의 output_root가 새 generation으로 바뀌어 매 성공 분석마다 원본 전체를 다시 복사한다. verify는 후보와 CPU reference 양쪽에서 복사한다. 성공 generation은 이전 revision을 포함해 남으므로 대용량 영상의 반복 분석에서 원본 중복과 디스크 비용이 누적된다. 기존 copy 코드 자체를 이번 구현으로 잘못 분류한 것이 아니라 generation 도입과의 상호작용이다. 원래 설계 §8의 “원본을 generation마다 복제하지 않음”과 다르다.
- **증거/미검증:** 정적 경로 확인. 보관 person-coreml-result의 source_video_path도 generation 내부다. 대용량 복사 실험은 하지 않았다.
- **최소 수정 방향:** 원본은 project의 immutable 저장소에 한 번 보관하고 generation은 검증된 hash/reference를 pin한다. 실패·이전 결과 보존과 source 변경 감지는 유지한다.

### F12 · P2 · 고장 격리 지연 — 기존 GPU load/최초 smoke가 짧은 watchdog 밖에 있다

- **파일/줄:** P `plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:77`; `face_runtime.py:119–123`; P `clipper_accelerators/clipper_accelerators/model_boundary.py:13–16`; `owned_stage.py:34,44`.
- **조건/영향:** 기존 ORT 세션 생성/컴파일 또는 AuraFace 최초 smoke가 native hang이면 model_call의 30초 watchdog이 시작되지 않는다. 이 경계에서는 기본 owned stage 21,600초 상한까지 지연될 수 있다. 사용자가 취소하기 전 자동 CPU 복구가 짧은 시간 안에 이루어진다고 보장할 수 없다.
- **증거/미검증:** 코드 경계로 확인했다. 실제 드라이버 hang은 주입하지 않았다.
- **최소 수정 방향:** owned child의 load/smoke에도 부모 watchdog과 typed failure를 둔다. CPU 재시도 전 소유 process tree 종료 확인을 유지한다.

## 3. 요구 미충족과 의도한 보호

### R01 · P1 · 기본 자동 가속 출하 자료/경로 미완료

P `clipper_accelerators/clipper_accelerators/catalog/packs.json:1`은 빈 packs/certificates이며 models.json의 여섯 활성 모델 artifacts도 비어 있다. E main.ts:377–378은 `clipper_accelerators/release-catalog.json`이 있을 때만 환경변수로 전달하지만 현재 소스/전달물에 그 release catalog는 없다. P `runtime_catalog.py:12–13,36–42`, `runtime.py:258–267`에 따라 일반 auto는 이 승인 자료가 없으면 새 후보 routing을 하지 않는다.

**명시 시험이 성공해도 그 성공이 후속 일반 auto의 새 ONNX 선택으로 곧장 반영되지 않는다.** 로컬 시험은 release 권한을 만들지 않고, ModelGate key에도 qualified 상태가 들어간다(runtime.py:122–125). 승인 자료를 나중에 공급해도 기존 unqualified 시험 row가 그대로 인증된 선택 row라는 뜻은 아니다. 별도의 인증·로컬 재검사 흐름이 필요하다.

E runtime-packs.ts:56–57은 CoreML 또는 DML 하나, P assets.py:26–27은 첫 호환 adapter 하나를 고른다. 여러 GPU/여러 runtime의 비교·순환은 실제 제품 경로에 없다. 기존 MPS/CUDA는 일부 ModelGate incumbent로 보존·비교하므로 “모든 GPU 비교를 전혀 하지 않는다”는 평가는 부정확하지만, 전체 환경별 후보 비교 요구가 완료된 것도 아니다.

- **의도한 보호:** 미인증 후보 차단, 기존 CPU/MPS/CUDA 유지, Mac Whisper CPU 유지, SAM/OCR 비활성 유지.
- **요구 미충족:** 새 자동 후보의 출하 승인·fixture·다중 후보 탐색, Mac 음성의 별도 가속 후보 구현·인증은 미완료다. 품질에 맞지 않는 MLX 등을 억지로 넣을 필요는 없지만 지원 범위와 남은 일을 완료 상태에서 구분해야 한다.
- **최소 방향:** 지원하려는 정확한 model/consumer/shape/backend/device 범위를 정하고 immutable export·pack·CPU baseline·최종 품질/성능 자료로 catalog를 생산·등록한다. 권한 gate를 우회하지 않는다. 그 전 UI는 “이 기기 시험”과 “다음 자동 분석에 적용 가능”을 명확히 구분해야 한다.

### R02 · P1 · 출하 corpus와 전체 실기기 매트릭스는 미검증이다

보관된 인물 6초/합성 정지 화면, 대사 18초/6 CLIP 호출 등은 실제 모델 smoke 증거지만 원래 요구의 다양한 인물 3영상·대사 4사례·96프레임/64 shot/12 audio·중요 경계·baseline 반복 3회·재배포 fixture를 대체하지 않는다. `release_gate.py:39`는 기록 비교만으로 출하를 승인하지 못하게 계속 BLOCKED 사유를 추가한다. 이 안전한 BLOCKED를 정상 출하 PASS로 바꾸면 안 된다.

Windows CPU-only/Intel iGPU/AMD/GTX1660Ti/RTX/hybrid, 낮은 메모리 Apple Silicon 및 최소 OS, 한국어 Windows 경로, cold/warm 전체 시간 3회, OOM·native crash·hang·sleep/wake·오프라인/업데이트 중단을 이번 감사에서 확인하지 않았다. 완료 문서도 Windows native_tested=false를 명시해 이 부분을 실기기 완료로 허위 표기하지는 않았다.

- **최소 방향:** 필수 행을 PASS/FAIL/BLOCKED/INELIGIBLE로 따로 채운다. 없는 장비/자료는 BLOCKED다. CPU/no-GPU 설치본 첫 분석과 고장 후 golden 결과/LLM 호출 수/process leak을 별도 인수 조건으로 둔다.

## 4. 실제 호출 경로와 품질 계약 확인

| 모델/소비자 | 실제 연결 | 확인/한계 |
|---|---|---|
| YOLOv8s pose / 안무·인물 | pose_engine/body_detector → yolo_adapter.create_pose_model → 원래 Ultralytics 또는 ModelGate/RemoteInference | 원래 전후처리를 재사용. MPS/CUDA incumbent 비교가 있으나 F03. 보관 CoreML 후보 raw 수치 불일치를 CPU로 거절한 것은 올바른 보호 |
| YuNet / 안무·인물 | 공통 OpenCvFaceBackend 및 dance opencv_acceleration → route_detector → ModelGate | OpenCV 디코드/NMS 유지. full-frame과 크기가 다른 ROI는 기존 native 경로로 돌아가므로 한 모델의 GPU 성공이 전체 workload coverage는 아님 |
| AuraFace / 안무·인물 | AuraFaceRecognizer/session_factory → RoutedSession 또는 기존 AcceleratedSession | 정렬/원래 입력 유지. 후보 없음 시 기존 세션 보존 수정 확인. load watchdog·partition 증거는 F09/F12 |
| SFace / 안무 보조 | route_recognizer + 기존 alignCrop/feature | RGB/scale 1 및 native alignCrop 유지. 실제 해당 보조 경로 미사용 영상에서는 모델 등록만으로 실행·품질 합격이 아님 |
| CLIP ViT-B32 / 대사 | embedding_pipeline.build_openclip_encoder → visual_inference → ModelGate | 기존 pretrained/transform, L2/shot aggregation 유지. 원래 MPS/CUDA와 비교하나 F03. verify는 analyze_media 단계로 최종 LLM 선택/렌더까지 검증하지 않음 |
| Whisper small / 인물·대사 | speech_stage/stt_worker → default_executor → CT2 CPU/CUDA/VerificationSpeechExecutor | small·VAD off·word timestamps 유지. 설치된 faster-whisper 기본 beam_size=5도 읽어서 확인. CPU int8/CUDA float16을 구분하고 cache identity에 실제 backend/decode/chunking을 넣음. Mac MLX adapter 없음 |

P verification.py는 인물 groups/clips, 안무 lists/persons, 대사 analysis 또는 stt, 존재하는 speech/구간 JSON을 비교한다. 이는 raw 수치 비교보다 넓지만 전체 앱 최종 결과 corpus gate와 같지 않다. 대사 원격 LLM을 고정해 최종 clip/자막까지 비교하는 출하 검증은 없다. 일부 모델이 거절되어 CPU를 사용한 동일 결과도 PASS이므로 비교 범위를 명시해야 한다(F04).

SAM/OCR는 catalog에서 active=false로 유지되며 새 선택·측정 대상으로 활성화한 변경을 확인하지 못했다. 현재 감사 범위에서 가중치·샘플 수·임계값·정렬·전후처리·small/beam5/VAD off/word timestamps를 속도를 위해 낮춘 확정 증거는 찾지 못했다. 다만 이는 미검증 기기/입력의 품질 동등성 보장이 아니다.

## 5. CPU 재분석·결과 공개·동시 작업

다음 보호는 코드에 실제 연결돼 있다. 단순 standalone recovery 함수만 있는 상태는 아니다.

- 안무/인물 run_visual_unit, 대사 run_transactional_stage가 owned child를 시작한다. 실패 시 새 process/새 epoch로 전체 분석 단위를 CPU 한 번 재실행한다. visual은 분석 run, dialog analyze_media는 STT+CLIP을 함께 다시 수행한다. 취소/CPU typed failure의 gpu=false는 CPU 재시도를 막는다.
- 대사 LLM은 Python analyze 성공 뒤 Nest workflow에서 실행하므로 이 CPU retry 루프 자체가 LLM을 중복 호출하는 구조는 아니다. 실제 전체 workflow의 fault injection 호출 수는 이번에 재검증하지 않았다.
- ArtifactTransaction은 stage에 쓰고 파일 SHA·project lock·revision CAS·취소 확인 후 pointer를 원자 교체한다. abort는 실패 generation을 제거하며 기존 성공 pointer를 보존한다. ArtifactSnapshot/TS resolver는 같은 revision의 맵과 hash를 검사한다. 이전 감사의 per-file latest/hash 미검사 문제에 대한 구조적 보완을 확인했다.
- 입력은 stat/hash를 고정하고 재시도 전/commit 전 재확인한다. 뒤늦은 동시 commit은 CAS 충돌로 막는다. 실패 partial generation의 직접 control 경로 해석도 거절한다. 실제 한국어 Windows 파일 잠금/동시 UI 편집은 미검증이다.
- owned process 종료 확인 실패는 정상 성공/안전한 복구로 숨기지 않는다. Windows Job의 원자 할당·kill-on-close·active process 확인 구조를 재사용하지만 Windows에서 실제 확인하지 않았다. 정상 idle remote worker 재생성도 코드/기존 회귀에 있다.

**남은 고장 분류 미검증:** owned_stage.py:51은 응답 없는 비정상 process 종료에 backend를 모르는 gpu=None을 부여하고 상위는 요청 device가 GPU면 재시도한다. GPU 가능 분석의 CPU native 모듈이 crash한 경우도 GPU 실패처럼 표시할 수 있다. 실기기 fault matrix에서 GPU/CPU crash 지점을 각각 주입해 구분해야 한다. 이 감사에서는 실제 crash 원인을 입증하지 않았으므로 별도의 확정 재현 결함으로 세지 않았다.

## 6. 기존 최종 검토의 여섯 지적 재확인

완료 문서의 여섯 항목을 코드에서 대조했다. 다섯 Python 함수는 임시 복사에서 pytest MonkeyPatch와 tempdir로 직접 실행했고, Electron 한 개는 기존 compiled JS를 읽는 node:test로 실행했다. 실제 추론·GPU·설치를 하지 않았다.

| 기존 지적 | 현재 확인 결과 | 이번 신선 검증 |
|---|---|---|
| AuraFace 후보가 없으면 기존 GPU 세션을 버림 | face_adapter.RoutedSession.run:87에서 incumbent 유지 | `test_missing_face_candidate_preserves_incumbent` PASS |
| YuNet setInputSize 전달 누락 | face_adapter.py:136–138에서 incumbent 전달 | `test_yunet_incumbent_receives_input_size` PASS |
| optional pack 실패가 native 탐색 차단 | runtime-packs.environment가 별도 bootstrap/probe 사용 | `accelerator-native-environment.test.js` 1/1 PASS |
| 실제 CPU Whisper 오류를 GPU로 재분류 | speech_adapter._actual_call + model_boundary의 gpu=false 보존 | `test_actual_cpu_whisper_error_is_not_relabeled_gpu` PASS |
| worker 시작 실패 뒤 lease 누수 | onnx_adapter.close:62–65에서 client 없는 경우도 release | `test_worker_start_failure_still_releases_lease` PASS |
| 대사 CPU 공개 시 후보 GPU 증거 소실 | executed_candidate_backend/candidate_executions 보존 | `test_dialog_executed_gpu_evidence_survives_cpu_publication` PASS |

이 여섯 국소 수정은 확인됐으나, F01의 실제 앱 연결 누락이나 F02의 TTL 소유권 결함을 이 테스트가 검증하지 않는다. 마지막 항목도 GPU 실행 증거 보존을 입증할 뿐, F04의 전체 모델 coverage나 F08의 최종 latest report 보존을 입증하지 않는다.

표준 pytest collector 실행은 `/private/tmp/codex-daemon-501`의 접근 제한으로 수집 단계에서 실패했다(테스트 실패가 아님). 재설치/권한 변경 없이 같은 다섯 함수를 직접 실행해 확인했다. `review-regression-results.json`에 결과가 있다. 따라서 “이번 감사 pytest 전체 green”이라고 주장하지 않는다.

## 7. 전달물과 현재 소스 일치

전달물은 앱 실행/마운트 없이 ZIP/ASAR 원문과 SHA로 읽었다.

| 검증 | 신선 결과 |
|---|---|
| handoff source-manifest ↔ 현재 네 작업 트리 | 4,896개 SHA 일치, mismatch 0 |
| source ZIP ↔ manifest | 4,896개 일치, mismatch 0, symlink entry 0 |
| 앱 ZIP Python 원문 ↔ P | 362개 일치 |
| 앱 ZIP Nest payload ↔ 현재 dist/bundled | 89개 일치 |
| 앱 ZIP Angular renderer ↔ 현재 dist | 142개 일치 |
| ASAR Electron payload ↔ 현재 dist-electron | 316개 일치, symlink entry 0 |
| ASAR 핵심 runtime 의존성 | 9개 package.json 존재 |

확인한 의존성은 electron-log, electron-updater, builder-util-runtime, graceful-fs, js-yaml, lazy-val, lodash.escaperegexp, lodash.isequal, semver다. 실제 native require 성공까지 새로 확인한 것은 아니다. Nest/Angular의 node_modules는 원본을 향한 개발용 symlink지만 Electron은 별도 실제 디렉터리다. 최종 ASAR에는 symlink가 없다. 이전 패키징 의존성 누락이 현재도 그대로 남았다는 증거는 찾지 못했다.

실제 파일 SHA-256은 handoff sha256.json / completion mac-artifacts.json의 기록과 일치했다.

| 파일 | SHA-256 |
|---|---|
| `P/.implementation-evidence/completion/handoff/clipper-acceleration-source.zip` | `c800658afed383f1d59b7b4e34150733135c8b34aad94c553e35fbaebbfc7d58` |
| `E/dist-app/Clipper Studio (dev)-0.0.1-arm64.zip` | `b4285f220ec24348bb486356910a60e62484ec1af6e18f56c0c4be561df576c5` |
| `E/dist-app/Clipper Studio (dev)-0.0.1-arm64.dmg` | `492b0a275fa9f18f9785e9cc214200f188d876c2d2a52ea2b36eeb85864df840` |

source-current-check.json의 결론을 그대로 믿은 것이 아니라 manifest와 현 소스/ZIP을 다시 대조했다. DMG는 hash/크기까지만 확인했고 내부 앱을 마운트해 ZIP과 비교하지 않았다. TS→JS fresh compile도 하지 않았으므로 “현재 generated payload가 패키지와 일치”를 “현재 TS로 새 빌드 성공”으로 확대하지 않는다.

plugin-venv.ts:72–96의 frozen/no-editable 설치·workspace 재설치, :115–149의 uv.lock/SDK/공통 코드 fingerprint, runtime-packs.ts:59–95의 소스/lock/pyproject identity와 worker/package hash 확인은 존재한다. Windows 첫 PC의 native wheel import/한국어 경로/Job 정리 성공은 코드와 lock만으로 합격시키지 않았다.

보관 전체 회귀 기록은 Python 3,169 pass/6 fail/5 skip이며 baseline/final 실패 집합이 같다. Electron 1,865 pass/2 fail도 전체 green이 아니다. 이번 감사에서는 그 전체 suite를 다시 실행하지 않았다. 기존 실패를 해결한 것으로 쓰거나 가속 완료를 증명하는 근거로 삼지 않는다.

## 8. 완료 표현과 재인수 순서

completion 문서는 Windows 미검증, 빈 release catalog, 작은 smoke corpus, YOLO 품질 거절, 모든 GPU 전수 비교 미구현을 비교적 명확하게 적었다. 그 한계 표기는 유지해야 한다. 반면 “Nest는 설정을 작업 시작 시 고정”, “앱에서 다음 분석 재최적화와 실제 완료 진단 제공”은 F01 때문에 현재 일반 작업 경로를 설명하지 못한다. 첫 문단의 구현 완료는 “모델 어댑터·국소 검증·전달물 준비” 수준으로 좁혀야 한다.

필수 수정/검증 순서는 다음과 같다.

1. **앱 제어 연결:** F01을 고치고 F08까지 함께 고친다. UI 저장 → 실제 workflow 제출 → mode/revision pin → 예약 정확히 한 번 소비 → 최종 보고서까지 통합 검증한다. 실행 시작 실패/취소 때 예약을 언제 소비하는지도 명시한다.
2. **실행 안전:** F02를 고쳐 살아 있는 소유자의 메모리가 TTL로 풀리지 않게 하고 F07/F12의 admission/load watchdog을 보완한다. 공유 환경이 비는 별도 기기에서 sleep/wake·timeout·late crash·CPU 자체 실패·취소를 시험한다.
3. **선택과 시험 판정:** F03/F04를 고쳐 CPU 포함 실제 비용과 필수 profile별 결과를 검증한다. F05/F06/F09의 예산·회전·재평가·진단 상태를 실제 경로에 연결한다.
4. **설치/저장:** F10/F11을 원래 동의·원본 보존 계약에 맞춘다. 새 CPU-only PC에서 optional 설치 실패/오프라인이어도 CPU 전체 분석을 완료하는지 확인한다.
5. **출하 승인:** R01/R02의 범위를 채우고 새 소스·빌드·ZIP/DMG 해시를 다시 봉인한다. gate를 풀거나 smoke를 전체 인수로 승격하지 않는다.

별도 실기기 재현은 현재 성능 측정 세션이 끝난 후, 공유하지 않는 앱 프로필/모델 캐시/venv를 써야 한다. Windows 새 계정의 한국어/공백 경로에서 CPU-only 첫 실행, 강제 CPU, 실행기 준비 실패, GPU 후반 오류 후 전체 CPU 한 번, CPU도 실패, 취소, 결과 파일 잠금, LLM 호출 수 불변과 owned process leak=0을 확인한다. 최종 인물 ID/구간/clip/자막은 frozen baseline 및 고정 LLM fixture와 비교한다. 성능은 cold/warm을 분리해 기준/후보 교차 최소 3회로 측정하고 5% 전체 회귀 기준을 실제 판정에 반영한다.

## 9. 이번 감사의 재현 증거

모두 `/private/tmp/clipper-final-audit-20261103-root/` 아래다. 임시 디렉터리이므로 장기 보존이 필요하면 보고서와 함께 별도 보관해야 한다.

- `workflow/reproduce.cjs`, `workflow/reproduction.json`: F01/F02/F08 저부하 재현.
- `model/cpu-faster-than-incumbent.json`, `model/quarantine-after-explicit-success.json`: F03/F06 mock clock/cache 재현 결과.
- `probe_benchmark.py`, `benchmark-probe-result.json`: F04 판정 재현. 모델/앱을 실행하지 않는 의존성 주입 시험이다.
- `test_review_regressions.py`, `run_review_regressions.py`, `review-regression-results.json`: 기존 여섯 지적 중 다섯 Python 회귀 함수 확인. Electron 한 개 node:test도 1/1 PASS를 직접 확인했다.
- `delivery/delivery-check-summary.json`: 현 소스/ZIP/ASAR/SHA·보존 검사의 방법·결과·한계.

**최종 준비 판정:** 전달물 무결성은 확인됐다. 실제 UI를 통한 일반 사용자 시험과 자동 가속 기능 인수는 F01–F04를 포함한 필수 수정 및 위 기기 검증 전까지 보류한다. 제한된 개발자용 CPU/명시 후보 실험은 가능하지만, 이 보고서는 현재 공유 앱·프로필에서 새 실행을 승인하거나 실기기 합격을 선언하지 않는다.
