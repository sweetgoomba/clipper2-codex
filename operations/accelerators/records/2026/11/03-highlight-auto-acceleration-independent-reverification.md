# 하이라이트 자동 가속 — 수정 후 독립 재검증

2026-11-03 KST. 대상 구현 세션: **하이라이트 GPU·ONNX 전환 및 Windows 시험 도구 감사** (`01a19e03-43e4-7880-83f1-92e0b923fb88`). 해당 세션의 최종 turn이 19:35:25 KST에 completed/idle인 것을 도구로 확인한 뒤 검증했다.

기준: [이전 최종 독립 감사](03-highlight-auto-acceleration-final-independent-audit.md). 기존 보고서는 수정하지 않았다. 구현자의 완료 주장과 테스트 수를 합격 근거로 전제하지 않고, 현재 소스와 원래 실패 조건을 대조했다.

## 결론

**기존 코드 지적 F01–F12 중 10개는 원래 실패 조건 기준으로 해결됐고, F03·F05는 부분 해결이다.** 실제 workflow의 설정 연결, 살아 있는 lease의 TTL 회수, 부족한 증거를 PASS로 만드는 benchmark 문제는 독립 재현에서 해소됐다. idle 작업과 복수 runtime/adapter 순환도 이제 실제 제품 경로에 존재한다.

남은 주요 문제는 다음과 같다.

- 기본 안무 YOLO의 FP16 incumbent에 대한 같은 추론 경계의 측정이 쌓이지 않아, 더 빠른 CPU를 선택할 비교 기준이 없는 경로가 남았다(F03 잔존, P2).
- 명시 시험에서 느린 CPU 비교가 시간 한도를 넘은 뒤 조기 반환하면 소비 예산이 0으로 기록된다(F05 잔존, P2).
- 순환 측정한 다른 native GPU는 다음 작업의 승자 후보로 전달되지 않는다(N01, P2).
- 지정된 전달 검증 JSON 일부가 최신 앱·소스 묶음 대신 이전 해시/파일 수를 담고 있다(N02, P2).
- CPU 설정 저장 후 idle 정리 실패 때 UI와 저장값 불일치(N03, P3), 개발 캐시·worktree `.git` 파일의 앱 포함(N04, P3)도 확인했다.

**사용자 기기에서 제한된 기능 시험을 진행할 소스·앱은 준비됐지만, 모든 감사 지적 해결 또는 복수 GPU 자동 최적화 완료로 인수할 상태는 아니다.** 위 잔존 코드는 사용자의 실기기 측정만으로 해결되지 않는다. R01의 출하 catalog는 여전히 없고 R02의 실제 기기 품질·속도·고장 매트릭스는 미검증이다. 이는 최신 지시대로 사용자가 수행할 인수 영역과 구분한다. 인증 gate를 풀거나 기존 정밀도·품질 기준을 바꾸는 해결을 권하지 않는다.

## 1. 범위와 검증 방식

| 약어 | 현재 소스 작업 트리 |
|---|---|
| P | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` |
| N | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` |
| E | `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103` |
| A | `/Users/jina/project/adlight/.worktrees/clipper-angular-accelerators-20261103` |

기준 HEAD는 이전 감사와 같다. 현재 미커밋 소스와 최신 전달물을 포함했다. `.codex/AGENTS.md`와 기존 검증·변경 최소화 규칙을 적용했다. 구현 코드, 원본 desktop, 대상 작업 트리, 공유 venv·모델 캐시·앱 프로필은 수정하지 않았다. 앱 실행·DMG 마운트·GPU 시험·전체 suite·새 설치·타 프로세스 종료도 하지 않았다.

실제 factory/runner/bridge/ModelGate/benchmark/원본 보관 함수와 현재 compiled JS를 읽고, 비싼 외부 추론·WebSocket·host·clock만 독립 fake로 바꿔 원래 조건을 재현했다. 이 방법은 연결·정책·판정을 검증하며 실제 GPU 품질·성능·Windows Job 실행을 증명하지 않는다. 가짜 timing을 제품 속도로 보고하지 않는다.

증거는 이 보고서와 같은 폴더의 `03-highlight-auto-acceleration-independent-reverification-evidence/`에 보존한다. 아래 증거 경로는 그 폴더 기준이다. 원 실행 출력은 `/private/tmp/clipper-reaudit-20261103/`에도 있다.

## 2. 이전 지적별 판정

| 항목 | 판정 | 현재 코드 및 독립 증거 |
|---|---|---|
| F01 실제 workflow 설정 우회 | **해결** | N `python-plugin-workflow-executor.ts:83–103,169–170,251–258`; `dialog-highlight-python-stage.runner.ts:28–29`와 module DI. 실제 factory/대사 runner＋실제 E settings store에 fake HTTP/WS를 연결했다. 안무·인물 제출 모드는 CPU→verify→auto, grant 존재, 예약 idle로 소비, report 모델 1개. DI metadata에도 설정 서비스가 있다. `workflow/routing.json`, `di.json` |
| F02 살아 있는 lease TTL 회수 | **해결** | E `accelerators/leases.ts:20–25`. 살아 있는 owner의 expires만 과거로 바꿔도 새 acquire 409, 기존 validate 200. native release 뒤에도 owner 생존 중 예약 유지. `workflow/leases-idle.json` |
| F03 더 빠른 CPU 미선택 | **부분 해결** | P `runtime.py:177–190`, `idle.py:352–412`에 다음 단위 CPU 선택이 추가됨. FP32 비교가 있는 control에서는 CPU 승자가 정상 반환된다. 기본 안무 FP16 경로의 측정 부재는 §3 A01에 남음 |
| F04 부분 실행·회귀도 benchmark PASS | **해결** | P `scripts/accelerators/benchmark_app.py:62–90,166–252`, `benchmark_evidence.py:56–95,156–224`. 실제 CLI 판정을 여섯 조건으로 실행. 없는 baseline은 분석 시작 전 BLOCKED/exit2; 100배 느림 FAIL/exit2; calls0·입력다양성1은 BLOCKED; 인물 ID 차이는 FAIL. 정상 control만 PASS이고 release는 항상 BLOCKED. `root/benchmark-results.json` |
| F05 idle/회전/시간 정책 미연결 | **부분 해결** | E `accelerators/idle.ts:47–59,88–127` → P `idle.py:188–349` → `calibration.measure_profile:76–149` 실제 연결. CPU/GPU 교대 round, 완료 row·회전 cursor 저장, 후보 제한과 다음 작업 선택을 확인했다. 명시 foreground trial의 CPU 예산 누락은 §3 A02에 남음 |
| F06 재검사 성공 뒤 quarantine 잔류 | **해결** | P `verification.py:64–69`. 충분한 표본＋최종 PASS인 명시 verify만 quality/invalid_output 해제. 독립 cache probe는 성공 재검사 후 사용 가능, 불충분 재검사는 계속 격리, release_qualified=false 유지. `model/policy-result.json` |
| F07 native 메모리 예약 0 | **해결, 실제 peak 미검증** | P `native_sessions.py:25–34,43–56`. 실제 소스의 admission 함수에 fake host로 acquire100, 추가 모델 reserve200, 증가분 reserve50을 확인. 동일 모델 재사용은 중복 예약하지 않음. 값은 주입값이며 실제 peak가 아님. `workflow/native.json` |
| F08 대사 후속 단계 report 덮어쓰기 | **해결** | N `acceleration-settings.service.ts:140–156`; P `transactional_stages.py:94–96`. 실제 analyze→build/render 경로와 record를 실행해 models1·validation·CPU 복구 이력이 유지됨. commit 전 디스크 진단 재기록도 확인. `workflow/routing.json` |
| F09 GPU/mixed 실행 증거 혼동 | **해결** | P `runtime.py:292–308,341–344`. mixed CPU7/CoreML3 node counts 보존, profile_verified=true, CoreML physical_gpu_verified=false, legacy=provider_only를 독립 probe 확인. `model/policy-result.json` |
| F10 부팅 시 optional 자동 설치 | **해결** | E `main.ts:385–389`는 inspect/환경 관측. 실제 inspect를 빈 임시 home에서 실행: not_prepared, install 호출0, 생성 파일0. `workflow/startup-inspect.json` |
| F11 generation별 원본 복제 | **해결** | P `immutable_source.py:40–88`; `visual_unit.py:48–59,73–74,111–115`; person `app.py:277–284`. 같은 원본의 보관을 3번 실행해 asset1/동일 reference, 별도 inode, 외부 입력 변경 후 보관 bytes 불변을 확인. `root/source-result.json` |
| F12 load/최초 smoke watchdog 부재 | **코드상 해결, 실제 hang 미검증** | P dance `opencv_acceleration.py:74–83`, `face_runtime.py:115–130`. 현재 loader source AST와 실제 model_call을 fake ORT/Timer로 실행해 두 load/smoke 모두 시작 전에 60초 Timer가 활성이고 종료 시 취소됨. `workflow/native.json` |
| R01 catalog·다중 후보·자동 적용 | **부분 진전, 출하 미완료** | 여러 설치 runtime/adapter와 native 후보의 열거·idle 회전이 추가됐다. 다만 다른 native GPU의 승자 적용은 N01 미구현이며 `catalog/packs.json`은 빈 packs/certificates, models.json artifacts도 비어 있다. 새 ONNX 일반 auto의 인증 gate는 유지됨 |
| R02 전체 corpus·기기 매트릭스 | **실기기 미검증 유지** | private profile·소형 CPU worker·fake GPU 회전은 다양한 최종 하이라이트 corpus/Windows/실제 GPU 성능·고장 검증을 대체하지 못함. 이번 감사에서 실행하지 않았으며 사용자 인수 영역으로 남김 |

설정 연결과 완료 report는 API만 직접 호출해 합격시킨 것이 아니다. 이전에 빠져 있던 실제 workflow factory와 대사 단계 runner를 사용했다. 다만 실제 Angular 설치본을 켜서 전체 UI를 조작한 검증은 하지 않았다.

## 3. 남은 결함과 신규 발견

### A01 · F03 잔존 · P2 — 기본 안무 FP16 incumbent의 비교 근거가 축적되지 않는다

- **위치:** P `plugins/dance_highlight/dance_highlight/services/config.py:77,139–141`; P `clipper_accelerators/clipper_accelerators/yolo_adapter.py:165,178–188`; `runtime.py:310–328`; `native_calibration.py:103–111`; `native_worker.py:59–63`; `idle.py:401–403`.
- **조건:** 기본 안무의 yolo_half=True가 적용되는 MPS 또는 device0 경로. 현재 idle native replay는 half=False/FP32만 생성하며, 선택기는 incumbent_precision과 같은 row만 baseline으로 쓴다. 정밀도가 다른 측정을 같은 근거로 사용하지 않는 보호는 올바르다.
- **실제 결함:** 같은 shape의 후속 프레임은 PreserveNativeResults가 raw gate를 우회한다. observe_native_prediction은 전체 prediction 진단만 기록하므로 원래 raw boundary 관측이 33개 쌓이지 않는다.
- **독립 재현:** 실제 `_routed_pose`＋fake Torch/모델을 40개의 서로 다른 frame으로 호출. raw incumbent 표본1, distinct1, full prediction 진단33, 게시 가능한 observed_incumbent=null, precision fp16. `model/native-observation-result.json`, `probe-native-observation.py`.
- **영향:** 더 빠른 CPU가 있어도 이 기본 경로는 baseline 부족으로 기존 GPU를 유지한다. F03의 일반 CPU 선택 분기는 생겼지만 현재 기본 안무 경로까지 해결됐다고 볼 수 없다.
- **최소 방향:** 같은 정밀도·동일 추론 경계의 owned native replay 또는 raw 관측을 확보한다. 원래 FP16을 FP32로 바꾸거나 full prediction 시간을 raw inference 시간으로 위장하면 안 된다. 실제 기기에서 속도가 느리다고 측정한 결과가 아니라, 비교 자료를 만들 수 없는 연결 결함이다.

### A02 · F05 잔존 · P2 — 느린 CPU 비교가 한도를 넘고도 소비 예산은 0으로 남는다

- **위치:** P `clipper_accelerators/clipper_accelerators/runtime.py:206–223,263–266`.
- **조건:** 명시 verify의 CPU/기존 경로 비교가 per-model 30초 예산을 소진한다.
- **독립 재현:** fake clock에서 CPU 비교가 35초 걸리도록 주입했다. 결과는 deferred_budget, 후보 호출0이지만 전역 소비 시간과 gate.trial_seconds 모두 0이다. CPU/기존 호출이 accounting finally 밖이며 remaining<=0의 조기 return이 이를 건너뛴다. `model/policy-result.json`, `probe-policy-regressions.py`.
- **영향:** 다음 모델들도 같은 예산을 새로 남아 있는 것처럼 사용할 수 있고, 시각 비교 30초/전체 비교 120초 상한이 명시 시험에서 보장되지 않는다. 새 idle CLI의 부모 120초 watchdog과 `measure_profile` deadline은 별도로 연결됐으므로, idle 전체가 다시 미구현이라는 뜻은 아니다.
- **최소 방향:** CPU·기존 경로·후보 비교 전체를 하나의 accounting finally에 넣고 비교 시작 전부터 남은 deadline을 전파한다. 원래 정상 분석에 필요한 추론과 추가 비교 비용을 구분한다. 실제 CPU 성능 시험 없이 제어 흐름을 재현한 결과다.

### N01 · P2 · 요구 미구현 — 더 빠른 다른 native GPU를 측정해도 다음 분석에서 선택할 수 없다

- **위치:** P `clipper_accelerators/clipper_accelerators/idle.py:396–404,405–412`.
- **조건:** 현재 GPU보다 다른 native Torch adapter가 빠르며 해당 측정이 유효하다.
- **실제 동작:** native row는 CPU/current incumbent timing으로만 사용하고 continue한다. 다른 adapter는 entries에 들어가지 않고 qualified_backend 검사에도 도달하지 않는다. 선택 결과로 native 실행 계획을 넘기는 연결이 없다.
- **독립 재현:** 실제 choose_for_gate에 현재 CUDA0 10ms / CPU20ms / native CUDA1 1ms의 유효 row와 인증 가능 stub을 제공. 선택 없음, native 인증 검사 호출0. CPU를1ms로 바꾸면 CPU 선택은 정상이다. `model/native-choice-result.json`, `probe-native-candidate-selection.py`.
- **영향:** 여러 GPU를 실제로 순환 측정하는 부분과 “빠른 실행 경로를 다음 분석에 적용”하는 부분 사이에 공백이 남는다. 단순히 현재 빈 catalog 때문에 보수적으로 거절된 것이 아니다. catalog가 있어도 이 분기를 통과할 수 없다. 장치가 실제로 10배 빠르다는 성능 주장은 아니며 주입값이다.
- **최소 방향:** 실제 adapter·정밀도·모델·승인 범위를 갖는 native execution plan/factory를 연결한다. 인증이 없으면 안전하게 보류하되, 승인된 대체 native GPU를 선택할 코드 경로는 있어야 한다. 현재 benchmark_evidence.py:184–198의 visual acceptance도 CPU/ORT만 처리하므로 native 경로의 인수 도구 범위를 함께 정의할 필요가 있다.

### N02 · P2 · 전달 증거 불일치 — 지정된 검증 JSON이 구 산출물 정보를 유지한다

- **위치:** P `.implementation-evidence/completion/mac-artifacts.json:4–5,9–10`; P `.implementation-evidence/completion/handoff/source-current-check.json:2`.
- **조건/영향:** 최신 앱은 새로 생성됐지만 mac-artifacts는 16:35 무렵의 구 DMG/ZIP SHA·크기다. source-current-check는 checked4896인데 최신 manifest는4934다. 사용자가 명시한 검증 파일들만 보면 현재 전달물을 검증했다는 잘못된 결론을 얻는다.
- **증거:** 두 실제 앱 파일을 다시 해시해 모두 구 JSON과 불일치. 최신 idle-rotation validation/handoff verification과 실제 내용은 일치한다. `delivery/delivery-check.json`.
- **구분:** 산출물 실행 코드 손상이나 소스 ZIP 불일치를 발견한 것은 아니다. 최신 source4934개와 실행 코드 payload는 아래 §5처럼 일치한다.
- **최소 방향:** 최종 전달물 생성 시 지정된 모든 검증 JSON을 같은 build identifier로 함께 재생성한다. 구 검증 기록을 남길 필요가 있으면 명시적인 과거 버전 이름으로 보관한다.

### N03 · P3 · 설정 표시 불일치 — CPU는 저장됐지만 실패 응답 뒤 UI에는 자동이 남는다

- **위치:** E `src/main/backend/plugin-host-bridge.ts:190–192`; A `src/shell/settings/acceleration-settings-card/acceleration-settings-card.component.ts:31–41`.
- **조건:** 자동→CPU 저장 중 idle process 종료 확인이 실패한다.
- **독립 재현:** 실제 bridge handler를 소켓 없이 호출하고 cleanup 실패만 주입했다. 응답409 idle_cleanup_not_confirmed, 파일은 mode=cpu/revision1이다. Angular save catch는 toast만 보여 이전 auto row를 유지한다. 5초 polling도 runtime/idle만 읽으므로 수동 새로고침 전까지 설정 값이 다르다. `workflow/save-error.json`, `verify-save-error.cjs`.
- **영향/방향:** 실제 CPU 보호와 cleanup 차단은 유지된다. 위험한 GPU 실행 허용으로 평가하지 않는다. 저장 결과와 cleanup_pending을 분리한 응답 또는 실패 시 settings 재조회로 화면을 동기화한다.

### N04 · P3 · 패키징 정리 누락 — 개발 캐시와 worktree `.git` 파일을 앱에 넣는다

- **위치:** E `electron-builder.yml:39–61`; 앱 ZIP의 `Contents/Resources/clipper_python/.git`, `.pytest_cache/**`, `.ruff_cache/**`.
- **증거/영향:** .pytest_cache 5개, .ruff_cache 34개 및 worktree .git 파일이 실제 앱에 있다. `.git/**` 제외는 worktree의 .git 파일에 적용되지 않는다. 불필요한 개발 경로/정보가 포함되고 ruff cache1개는 현 worktree와 바이트가 다르다. 실행 코드 mismatch 또는 원시 영상·venv 유출 증거는 아니다.
- **최소 방향:** `.git` 파일과 두 cache 디렉터리를 명시 제외한 뒤 재패키지·해시 검증한다. `delivery/delivery-check.json`과 ZIP entry 검토에 근거한다.

## 4. 새 idle 경로에서 확인한 보호와 한계

- Electron coordinator는 begin 첫 await 전에 admitting을 올리고 idle 종료 확인 뒤 foreground를 허용한다. 가짜 stop Promise를 지연한 재현에서 이벤트는 idle_running → cleanup_requested → cleanup_confirmed → foreground_admitted였다. 선점된 요청은 pending으로 남았다(`workflow/leases-idle.json`).
- 소유권 복구는 PID birth 불일치와 소유하지 않은 process가 섞인 group을 signal 없이 거절했다. Windows Job 관측이 unverified면 ownership 기록을 유지했다(`workflow/owner-recovery.json`). 실제 process를 종료하거나 Windows Job을 실행한 시험은 아니다.
- P idle.run_once는 실제 profile 검증, immutable 입력/CPU expected hash 확인, 설치된 runtime/adapter 열거, 회전 cursor 영속화, 최대2 GPU 후보, CPU 교대 round, 미완료 row의 보류/격리를 수행한다. measure_profile은 warmup3/10×3round와 p90/cleanup을 검사한다. 완료 구현이 테스트 함수에만 머물러 있던 F05의 큰 공백은 해소됐다.
- six focused low-load regressions는 새로 실행해 6 passed/0.61초였다(`model/focused-pure-tests.log`). 제품 성능 숫자가 아니다. 전체 Python/Nest/Electron/Angular suite 및 새 설치본 UI를 이번 감사에서 다시 실행하지 않았다.
- Whisper small/beam5/VAD off/word timestamps/chunking, Mac CT2 CPU 유지, SAM/OCR 비활성, 인증 gate는 보존됐다. 음성 후보는 native interpreter와 CT2/faster-whisper 버전으로 구성되므로 “다른 isolated speech runtime을 측정하고 원 plugin runtime을 쓴다”는 의심은 현 코드에서 확정하지 않았다.
- 실제 GPU crash/hang/OOM/sleep·wake/Windows Job/한국어 Windows 경로/메모리 peak 및 최종 인물 ID·구간·clip·자막의 다양한 입력 품질은 실기기 미검증이다. 다른 안무 세션의 3영상 측정은 가속 트리 통합 증거가 아니므로 사용하지 않았다.

## 5. 최신 전달물·원본 보존 재검증

실제 파일을 읽고 다시 해시했으며 이전 감사나 source-current-check의 결과를 재사용하지 않았다.

| 확인 | 결과 |
|---|---|
| source-manifest ↔ 현재 네 작업 트리 | 4,934개 일치, mismatch0 |
| source-manifest ↔ source ZIP | 4,934개 일치, mismatch0, symlink0 |
| source ZIP 안내/예제6개 ↔ 현재 completion | 모두 일치 |
| 앱 Python payload | 403개 중 실행 코드 mismatch0. 개발 ruff cache1개만 다름(N04) |
| 앱 Nest payload ↔ 현재 bundle | 89개 일치 |
| 앱 Angular renderer ↔ 현재 dist | 142개 일치 |
| ASAR Electron ↔ 현재 dist-electron | 324개 일치, symlink0 |
| 필수 Node dependency package.json | 9개 모두 존재. 새 native require 실행은 안 함 |
| 이전 사용자 변경 merge/new-user SHA | 9개/5개 모두 일치 |
| idle 시작 snapshot의 보존 사용자 파일 | 18개 모두 일치 |

최신 실제 SHA-256:

| 전달물 | SHA-256 |
|---|---|
| P `.implementation-evidence/completion/handoff/clipper-acceleration-source.zip` | `18701193394c9bfed7d665e39babe32bdb7009bfd035b4bea95648dda3ad9fe9` |
| E `dist-app/Clipper Studio (dev)-0.0.1-arm64.zip` | `f0e25ac8806cf330dc0b48a77857e8faee76752101b47e2f7c949489d314c93c` |
| E `dist-app/Clipper Studio (dev)-0.0.1-arm64.dmg` | `288b0d165abd46505f350d3e97c97f700682ac0357ff33b855040fe0000a5f12` |

source ZIP의 sha256.json은 최신과 일치한다. mac-artifacts/source-current-check의 구 기록 문제는 N02처럼 별도다. DMG는 hash/크기만 검증했고 마운트하지 않았다. 현재 generated JS/renderer와 앱 일치는 fresh TS build나 실제 설치 실행 합격을 뜻하지 않는다.

원본 desktop 네 repo를 idle 시작 snapshot과 직접 대조했다. Python599/Nest1473/Electron461/Angular2271 파일에서 mismatch0, HEAD도 같다. Python의 10MiB 초과 fixture JSON·폰트 두 파일은 이번 보존 대조에서 다시 해시하지 않았다. 이전에 병합한 사용자 변경을 이번 구현으로 잘못 분류하지 않았다. `delivery/preservation-check.json`에 범위를 기록했다.

구현자의 최신 전체 검사 기록은 Python3360 pass/6 fail/5 skip, Nest5292 pass, Electron1903 pass, Angular 관련50 pass다. 해당 로그·validation을 참고했지만 이번 독립 감사에서 전체를 재실행한 결과로 쓰지 않는다. Python의 기존 렌더링 실패6개가 없어졌다고 표시하지 않는다.

## 6. 준비 판정과 필수 후속

- **기본 제어·복구 소프트웨어:** 이전 P1 설정 연결·TTL·benchmark 결함은 수정됐다. 제한된 기기 기능 시험을 진행할 근거가 개선됐다.
- **자동 최적화 완성:** A01/A02/N01 때문에 전체 해결 판정은 보류한다. 먼저 같은 정밀도 incumbent 비교·대체 native GPU 실행 계획·명시 비교 예산 처리를 보완해야 한다. 품질 gate 완화는 해결이 아니다.
- **전달물 인수:** 최신 앱/소스 내용 일치는 확인했다. N02의 지정 검증 기록은 갱신해야 한다. N03/N04는 낮은 우선순위의 사용성·패키징 정리다.
- **출하·성능 승인:** R01/R02는 계속 미완료/미검증이다. 사용자가 수행할 실제 Mac/Windows의 cold/warm3회·여러 입력·최종 품질·고장 매트릭스가 필요하다. 소형 CPU worker와 mock GPU 후보의 성공을 출하 corpus 또는 물리 GPU 성능 합격으로 승격하지 않는다.

수정 후에는 이 보고서의 원래 조건을 다시 재현하고 새로운 앱·source ZIP·manifest/해시를 함께 봉인해야 한다. 이번 재검증은 코드 직접 수정 없이 끝냈으며, 완료 감지용 일회성 예약은 재검증 보고 후 종료한다.
