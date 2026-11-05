# 세 하이라이트 자동 가속 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 실제 실행 방식은 구현 요청 때 정한다. 이번 산출물은 설계·계획이며 제품 구현을 시작하지 않는다.

**Goal:** 안무·인물·대사의 모든 활성 모델에 품질 인증, 환경별 자동 가속 선택, 실제 성능 검증, CPU 복구를 적용한다.

**Architecture:** Electron은 환경·설치·프로세스 소유·GPU 임대를 담당한다. 경량 `clipper_accelerators` Python package는 모델 등록·선택·worker·복구를 제공하고, 기존 face/speech core와 플러그인 알고리즘은 실행 객체를 주입받는다. Nest/Angular는 기존 계약 위에 설정과 실제 사용 진단을 추가한다.

**Tech Stack:** Python 3.11/uv, PyTorch·Ultralytics·OpenCV·ONNX Runtime·CTranslate2, 후보별 CoreML/DirectML/CUDA/MLX, Electron/TypeScript, NestJS, Angular Material. 각 repo의 현재 lock을 출발점으로 하며 optional pack의 정확한 버전·해시는 T04/T15 인증 산출물이다.

**Spec:** [세 하이라이트 자동 가속 설계](/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/03-highlight-auto-acceleration-design.md)

2026-11-03 KST · 구현 전 계획 v1. 모든 체크박스는 미실행이다.

## Global Constraints

- Apple Silicon native arm64 Mac + Intel/AMD CPU의 Windows x64. Intel Mac, Windows ARM와 x64 에뮬레이션은 이번 범위 밖이다.
- 활성 고유 모델 6개: `pose.yolov8s`, `face.yunet`, `face.auraface`, `face.sface`, `visual.clip_b32`, `speech.whisper_small`. 현재 꺼진 SAM2와 EasyOCR는 실행·설치·측정하지 않는다.
- 모델 weight, 전처리, frame sampling, 임계값, 이름/인물/메인/단체 정책, CLIP shot 평균, STT small/VAD=False/word timestamps를 보존한다. 가속 때문에 품질을 낮추지 않는다.
- CPU 기준부터 현재 승인된 최종 결과 gate를 통과한다. 수치 허용치와 최종 의미 gate는 설계 §7의 값 그대로 사용한다. 더 빠르다는 이유로 golden을 갱신하지 않는다.
- CPU 기준은 기존 plugin 환경에 준비한다. CPU/DML/GPU ORT wheel을 한 venv에 혼합하지 않는다. pack별 lock·hash·실측 인증 없이 latest를 설치하지 않는다.
- GPU worker는 plugin 소유. loopback 인증, `send_bytes/recv_bytes`, header 64KiB, tensor 총 64MiB, no pickle. 취소 유예 5초; 시각 infer 30초, STT 기존 3600초 상한.
- 자동 측정은 idle 120초/회, 시각 후보 30초·STT 후보 60초, CPU+GPU 최대2후보/프로필/회차. 다른 인증 후보/adapter는 다음 idle 회차의 순환 대기열로 평가한다. 시각24입력·warmup3·10회×3round, STT 예산 내3회. 완성되지 않은 row는 deferred.
- 새 후보는 인증 범위 안의 장치이며 로컬 품질 검사를 통과해야 한다. 예상 stage cost 10% 이상 감소, p90≤기준×1.05일 때 전환한다. 최종 앱 median>기준×1.05면 기본 활성화 금지.
- 오류 후 분석 단위 전체를 CPU로 한 번 재실행한다. 취소/잘못된 입력은 재시도하지 않는다. GPU/CPU epoch의 gallery·tracking·결과를 혼합하지 않는다.
- 현재 미커밋 안무 작업과 다른 세션의 변경을 보존한다. 구현 시작 때 상태를 다시 읽고, 격리가 필요하면 관리 worktree를 사용한다. 사용자 요청 전 commit/push/restart/실기기 장시간 실행을 이 계획 작성의 일부로 하지 않는다.
- Markdown 산출물은 `.codex`에 둔다. 실행 코드/fixture schema는 해당 코드 repo에 둔다. 내부 API는 raw, TS/Python 계약 fixture 공유, Angular Material/semantic tokens/분리된4파일 규칙을 따른다.

## Review Focus

1. **새 드라이버·미시험 GPU·같은 이름의 두 GPU:** 인증 범위를 자동 확대하거나 잘못된 adapter에 session을 만들지 않는다. T02/T03/T07의 `test_unknown_driver_is_not_auto_qualified`, `test_ambiguous_adapter_mapping_blocks_candidate`가 고정한다.
2. **다운로드 취소·오프라인·worker를 쓰는 중 pack 교체:** 기존 CPU/pack이 남고 첫 분석이 끝없이 대기하지 않는다. T04의 `activation preserves previous pack and live references`가 고정한다.
3. **한국어 경로·Windows 파일 잠금·취소와 완료의 동시 발생:** 이전 결과가 남고 하나의 완료 상태만 공개한다. T08의 `test_cancel_commit_race_has_one_terminal_state`와 Nest resolver 테스트가 고정한다.
4. **GPU는 빠르지만 관절/identity/자막 경계가 달라짐:** 수치 gate가 통과해도 최종 결과가 다르면 후보를 제외한다. T01/T09–T12의 의미 gate 테스트가 고정한다.
5. **긴 영상의 늦은 crash·동시 plugin·sleep 후 끊긴 heartbeat:** 부분 결과/CPU·GPU 혼합/타인 프로세스 종료 없이 한 번만 복구한다. T05/T06/T08/T15가 고정한다.

## 파일 지도와 실행 규칙

이 문서의 파일 표기 prefix는 아래 절대 경로를 의미한다. `NEW`는 계획상 신규 파일이며 아직 존재하지 않는다. 나머지는 조사한 기존 파일이다. 줄 번호는 변경 중인 작업 트리에서 흔들리므로 정확한 파일과 함수명을 지정한다.

| Prefix | 절대 경로 |
|---|---|
| P | `/Users/jina/project/adlight/desktop/clipper_python` |
| E | `/Users/jina/project/adlight/desktop/clipper_electron` |
| N | `/Users/jina/project/adlight/desktop/clipper_nestjs` |
| A | `/Users/jina/project/adlight/desktop/clipper_angular` |
| D | `/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11` |
| C | `P/clipper_accelerators/clipper_accelerators` (NEW package source) |
| CT | `P/clipper_accelerators/tests` (NEW tests) |

| 소유 | 새 파일 묶음 / 역할 |
|---|---|
| T01 | `P/scripts/accelerators/freeze_baseline.py`, `quality.py`, `qualify.py`; `P/tests/fixtures/accelerators/{corpus.schema.json,calibration.schema.json,contracts.json}` — baseline과 검증 CLI |
| T02 | `C/{__init__,contracts,registry}.py`, `C/catalog/{models,packs}.json` — 데이터 계약과 인증 등록; `P/clipper_accelerators/pyproject.toml` |
| T03 | `C/{environment,windows_dxgi}.py`, `E/src/main/resources/accelerator-environment.ts` — OS/실제 장치 대응 |
| T04 | `P/scripts/accelerators/build_runtime_pack.py`, `E/src/main/plugin/accelerator-packs.ts` — lock 생성·설치·활성화 |
| T05 | `C/{protocol,worker,worker_client}.py` — binary IPC와 프로세스 경계 |
| T06 | `C/lease_client.py`, `E/src/main/resources/accelerator-leases.ts` — adapter별 소유권/메모리 임대 |
| T07 | `C/{selection,calibration,cache}.py` — 제한 실측·선택·무효화 |
| T08 | `C/{recovery,artifacts}.py`, `N/src/modules/projects/infrastructure/committed-artifact-resolver.ts` — CPU 재시도·결과 공개 |
| T09–12 | `C/backends/{__init__,pose,face,clip,speech}.py`, `P/scripts/accelerators/export_models.py` — lazy backend factory와 재현 export |
| T14 | `C/diagnostics.py`, `N/src/modules/plugins/presentation/dto/acceleration-settings.dto.ts` — 실제 사용 상태·설정 입력 |
| T15 | `P/scripts/accelerators/benchmark_app.py` — 실제 앱 계측·출하 증거 |

기능별 변경은 아래 태스크가 명시한 기존 파일에만 추가한다. 공통 package는 plugin을 import하지 않는다. 테스트가 요구하기 전 범용 backend plugin SDK나 별도 daemon은 만들지 않는다.

**검증 명령 규칙:** Python 명령의 cwd는 P다. 기존 소비자 package name은 `clipper-plugin-dance-highlight`, `clipper-plugin-person-highlight`, `clipper-plugin-dialog-highlight`다. 테스트 의존성을 갖춘 해당 plugin interpreter를 사용한다. T02에서 새 package와 테스트 의존성을 lock에 포함한 뒤에는 **`uv run --frozen --package clipper-accelerators --extra test python -m pytest ... -q`**를 공통 경량 시험 명령으로 확정한다. 모델 소비자 테스트는 각각의 기존 plugin 환경에서 같은 `python -m pytest`를 실행한다. 새 `test` extra는 pytest/NumPy 등 테스트에 실제 필요한 것만 pin하며 torch/ORT는 공통 extra에 넣지 않는다. 외부 다운로드 없는 검증에서는 이미 준비된 interpreter를 직접 사용한다. 아래 `$PY`는 해당 테스트 의존성이 설치된 interpreter 절대 경로를 뜻한다(환경변수 `$HOME` 등을 재정의하지 않음).

Electron: E에서 `npm run build`, 이어서 `node --test test/<파일>.test.js`. Nest: N에서 같은 build+node:test 방식. Angular: A에서 `npx ng test --watch=false --browsers=ChromeHeadless --include=<spec>` 및 `npm run test:styles`. 계획 문서 작성 중에는 이 빌드/추론을 실행하지 않는다.

## 실행 순서

`T01 → T02 → T03/T04 → T05 → T06 → T07 → T08 → T09/T10/T11/T12 → T14 → T15`.

T13의 추가 vendor 후보는 기본 경로 인증 이후 진행한다. T15는 각 후보가 추가될 때 해당 matrix만 반복한다. 병렬 가능 표기는 의존 관계 설명이며 자동으로 다른 채팅/에이전트를 생성하라는 지시가 아니다. 공통 파일을 공유하는 T09–12는 동일 파일 동시 편집을 피한다.

각 태스크는 아래 test를 먼저 작성해 의도한 assertion으로 실패하는지 확인하고, 최소 변경 후 동일 test와 명시된 기존 회귀 시험을 통과시킨다. 파일 미존재·의존성 미설치에 의한 실패를 품질 시험의 RED로 대신하지 않는다. 태스크 종료 때 diff/검증 결과를 남기며 commit은 별도 사용자 지시에 따른다.

### T01 — 품질 기준·내부 corpus·배포 fixture 확정

**의존:** 없음. **산출물:** 현재 품질을 재현할 manifest와 검증기; GPU 구현 전 독립적으로 유용하다.

**Files:** NEW `P/scripts/accelerators/{freeze_baseline,quality,qualify}.py`, `P/tests/test_accelerator_quality.py`, 위 corpus/calibration schema. 산출 증거는 `D/03-highlight-acceleration-baseline/`(구현 때 생성; 개인정보·대형 원본은 기존 허용 위치에 두고 hash/path만 기록).

**Interfaces:**
- `freeze_baseline(repo_roots: Sequence[Path], corpus_path: Path, output_dir: Path) -> Path`: HEAD+dirty diff·untracked hash+모델/설정/환경과 예상 출력 manifest를 반환한다.
- `compare_outputs(model_id: str, consumer: str, expected: Mapping, actual: Mapping) -> QualityResult(passed, numeric_failures, semantic_failures)`.
- `qualify.py --corpus <manifest> --candidate <candidate-json> --out <dir>`: PASS=exit0, FAIL=1, BLOCKED=2. 없는 영상·장비·예상 결과는 skip/PASS가 아니다.

- [ ] 기존 승인 출력/안무 미커밋 snapshot과 비교할 CPU·현재 MPS/CoreML 기준을 확보한다. 내부 corpus는 설계 §11의 안무/인물 각 영상≥96프레임+경계 전부, 인물≥3영상, 대사≥4사례, CLIP≥64shot, STT≥12구간을 manifest에 고정한다. 소유자 승인/출처를 기존 기록에서 확인할 수 없으면 그 fixture의 release 상태를 BLOCKED로 남긴다.
- [ ] 배포 fixture를 별도로 만든다: 프로필당24시각 입력+짧은 한국어/영어/무음, 재배포 권리·expected CPU output·모든 hash, 압축≤25MiB. 개인 영상/참조 얼굴 복사를 금지하고 offline 검사에 필요한 자료를 모두 넣는다.
- [ ] `test_numeric_pass_does_not_override_semantic_failure` 작성: cosine=0.999999지만 identity 또는 start_frame이 달라지면 `passed is False`; YOLO box=.5px/관절=.5px/score=.001 경계, Whisper50ms 경계를 각각 넘는 입력은 실패한다. `test_missing_fixture_is_blocked`는 exit2를 검증한다.
- [ ] `$PY -m pytest tests/test_accelerator_quality.py -q`의 의도한 실패를 확인하고 비교기를 구현한다. 임시 시각·경로만 제외하고 자막 저장 정밀도·최종 clip 순서를 그대로 비교한다.
- [ ] 같은 명령 PASS 후 baseline을 같은 설정3회 실행해 변동을 기록한다. 미확정 corpus/CPU 품질 차이는 후속 enabled gate를 막되 계약/격리 작업은 진행할 수 있다.

### T02 — 모델·인증·선택 데이터 계약과 경량 package

**의존:** T01 schema. **Files:** NEW `P/clipper_accelerators/pyproject.toml`, `C/{__init__,contracts,registry}.py`, `C/catalog/{models,packs}.json`, `CT/test_registry.py`, `CT/test_import_boundary.py`; MODIFY `P/pyproject.toml`, `P/uv.lock` 및 세 plugin pyproject의 workspace 의존.

**Interfaces:** 설계의 `Workload`, `BackendKey`, `ExecutionContext`를 그대로 정의한다. 다음 dataclass도 여기서 정의하며 runtime 호출은 하지 않는다.

- `AnalysisContext(job_id: str, unit_id: str, attempt: int, epoch: str, mode: str, selections: Mapping[str, BackendKey])`: immutable 분석 단위 계획. 각 workload ID의 선택에서 모델별 ExecutionContext를 생성하며 CPU 복구는 매핑 전체를 새 epoch로 교체한다.

- `SupportScope(os_build_ranges, native_arch, cpu_isa, gpu_device_ids, apple_chip_families, driver_ranges, exclusions)`; 범위는 certificate 증거에 명시된 값만.
- `QualityCertificate(id, artifact_sha256, pack_sha256, consumer, preprocessing_id, shapes, batches, precisions, support_scope, corpus_sha256, calibration_sha256, report_sha256, status)`.
- `ModelSpec(model_id, active, consumers, artifacts, io_contract, cpu_backend, recovery_unit, candidates)`와 `RuntimePackSpec(pack_id, manifest_sha256, platform, python_abi, locks, native_libraries, compatibility, download_bytes)`.
- `EnvironmentSnapshot(host_arch, process_arch, os_build, cpu_isa, available_ram_bytes, adapters, installed_packs, fingerprint)`; `Adapter(id, vendor, device_id, driver, backend_indices, free_bytes, total_bytes, memory_kind, usable)`.
- `Measurement(key, status, local_quality_passed, load_ms, compile_ms, median_ms, p90_ms, peak_bytes, samples, environment_fingerprint)`.
- `Selection(backend: BackendKey, reason: str, measured: bool)`; `Policy(version, mode, calibration_budget_s=120, minimum_gain=.10, p90_limit=1.05)`.
- `Registry.candidates(workload: Workload, environment: EnvironmentSnapshot) -> tuple[BackendKey, ...]`.

- [ ] `test_unknown_driver_is_not_auto_qualified`: 미등록 driver/device, certificate hash 불일치, disabled SAM/OCR는 후보가 없어야 한다. CPU 후보도 미인증이면 새 가속 기능의 기준으로 활성화하지 않는다.
- [ ] `test_import_boundary`는 공통 package import 뒤 torch/onnxruntime/cv2/faster_whisper가 `sys.modules`에 없음을 검사한다. shared core→공통 계약 단방향을 지킨다.
- [ ] `$PY -m pytest clipper_accelerators/tests/test_registry.py clipper_accelerators/tests/test_import_boundary.py -q`로 RED→GREEN. 6개 활성 모델/2개 disabled entry와 소비자별 profile만 등록하고 허위 certificate/버전 값을 채우지 않는다.
- [ ] `P/tests/fixtures/accelerators/contracts.json`에 schema2 진단, 설정, 오류, lease, artifact pointer의 valid/invalid 예시를 넣고 이후 Python/TS 시험이 같은 파일을 읽게 한다.

### T03 — 실제 OS·아키텍처·GPU adapter 감지

**의존:** T02. **Files:** NEW `C/{environment,windows_dxgi}.py`, `CT/test_environment.py`, `E/src/main/resources/accelerator-environment.ts`, `E/test/accelerator-environment.test.js`; MODIFY `E/src/main/resources/host-resource-monitor.ts`.

**Interfaces:** `probe_environment(host_snapshot: Mapping, packs: Sequence[RuntimePackSpec]) -> EnvironmentSnapshot`; `resolve_adapter(adapter: Adapter, backend: str, probe_rows: Sequence[Mapping]) -> int | None`. Electron `collectAcceleratorEnvironment(): Promise<AcceleratorEnvironment>`의 JSON은 T02 계약을 따른다.

- [ ] `test_ambiguous_adapter_mapping_blocks_candidate`: OS GPU 순서 [Intel,NVIDIA], CUDA 순서 [NVIDIA]일 때 정확한 장치가 맞고, 동일명/매핑 불확실이면 None. Windows ARM+x64 process, Intel Mac, Apple Silicon+Rosetta를 native 지원으로 표시하지 않는다.
- [ ] Windows는 격리 worker의 `ctypes` DXGI EnumAdapters1 결과와 LUID/PCI instance/vendor/device 정보를 OS 목록에 대응한다. 재부팅으로 바뀔 수 있는 LUID만을 영구 key로 쓰지 않는다. CUDA index/DXGI index를 동일시하지 않는다. 미매핑 장치는 자동 후보에서 제외한다.
- [ ] Apple은 실제 host chip/arm64와 shared memory를 기록한다. GPU 조회 실패는 `unknown`, GPU 없음은 `none`; free memory 미상은0으로 위조하지 않는다.
- [ ] Python `CT/test_environment.py`와 E `accelerator-environment.test.js` RED→GREEN; 실제 adapter 출력 fixture에 한국어 장치명/복수GPU/드라이버 미조회/재부팅 LUID 변경을 포함한다.

### T04 — runtime pack 생성·설치·활성화

**의존:** T02/T03. **Files:** NEW `P/scripts/accelerators/build_runtime_pack.py`, `E/src/main/plugin/accelerator-packs.ts`, `E/test/accelerator-packs.test.js`; MODIFY `E/src/main/plugin/{plugin-venv,model-install,plugin-model-files}.ts`, `E/scripts/build-app.mjs`, `E/package.json`; model/export manifest는 T09–12와 연결한다.

**Interfaces:** `build_runtime_pack.py --spec <json> --target <darwin-arm64|win32-x64> --out <dir>`; TS `ensureAcceleratorPack(spec, consent, signal): Promise<InstalledPack>` 및 `activateAcceleratorPack(pack): Promise<void>`; `InstalledPack`은 immutable root/interpreter/manifest hash/완료 marker를 가진다.

- [ ] `activation preserves previous pack and live references`, `offline without optional pack keeps CPU available`, `two requests share one install` 시험을 작성한다. 손상 wheel/native DLL/취소/디스크 부족은 active pointer를 바꾸지 않는다.
- [ ] `win-dml`, `win-cuda`, `mac-apple`, `mac-mlx`를 별도 Python3.11 환경으로 고정한다. 모든 transitive/native library·license·CPU ISA·OS/driver floor와 압축/설치 크기를 manifest에 넣는다. 최초 DML 후보1.24.4; CUDA는 GPU 세대와 driver에 맞는 실제 호환 lock을 만든다. CTranslate2/torch/ORT가 요구하는 CUDA/cuDNN을 같은 pack에서 충족 못 하면 pack을 더 분리한다.
- [ ] 기본 CPU 런타임·원본 모델·배포 fixture가 준비된 뒤 GPU pack을 활성화한다. optional 다운로드는 기존 설치 동의·진행 UI를 재사용한다. 모델 export는 출시 환경에서 만들며 고객 PC에 compiler/exporter를 요구하지 않는다.
- [ ] `node --test test/accelerator-packs.test.js test/plugin-venv.test.js test/plugin-process-packaged-paths.test.js` PASS. arm64 Mac/win32-x64 설치 경로만 새 가속 pack 지원표에 포함하고 Intel Mac build script로 새 지원을 주장하지 않게 release target 검사를 추가한다.
- [ ] 산출 exact lock과 hash는 아직 experimental. 설치 smoke는 가짜 worker로 먼저 검사하고 T05 이후 실제 CPU/GPU worker smoke를 붙인다. T15 전에는 qualified/enabled marker를 만들지 않는다.

### T05 — worker IPC·수명·취소 경계

**의존:** T02/T04. **Files:** NEW `C/{protocol,worker,worker_client}.py`, `CT/test_protocol.py`, `CT/test_worker_lifecycle.py`; MODIFY `E/src/main/plugin/{plugin-process,windows-owned-tree,child-process-stop}.ts`에서 기존 owned-tree 경로 확장; `P/clipper_plugin_sdk/clipper_plugin_sdk/windows_supervisor.py`는 소유 전파에 필요한 경우만 변경.

**Interfaces:** `WorkerClient.start(pack: RuntimePackSpec, owner: Mapping) -> WorkerClient`; `client.request(operation: str, context: ExecutionContext, inputs: Sequence[TensorPacket], cancel, deadline: float) -> WorkerReply`; `client.close(grace_s: float = 5) -> ExitEvidence`. `TensorPacket(dtype, shape, data: bytes)`와 `WorkerReply(request_id, epoch, outputs, diagnostics, error)`는 T02 계약에 추가한다. operation은 probe/load/infer/unload/close뿐.

- [ ] `test_rejects_oversized_mismatched_or_stale_payload`: header>64KiB, tensor>64MiB, dtype/shape product 불일치, 예전 epoch 응답을 거부한다. float NaN은 수치 출력 검사에서 typed `invalid_output`으로 분류한다.
- [ ] 인증된 loopback listener를 부모가 생성하고 `send_bytes/recv_bytes`만 사용한다. 요청별 correlation·읽기 상한·부분 frame 종료를 구현한다. audio path는 allow-root 상대경로+hash이며 `..`/symlink 외부 이탈을 거부한다.
- [ ] `test_worker_crash_does_not_kill_plugin`, `test_cancel_kills_only_owned_tree_after_five_seconds`에 가짜 crash/hang subprocess를 사용한다. 실제 crash 재현을 host pytest 프로세스 안에서 하지 않는다.
- [ ] `$PY -m pytest clipper_accelerators/tests/test_protocol.py clipper_accelerators/tests/test_worker_lifecycle.py clipper_plugin_sdk/tests/test_runtime_cancel.py -q` PASS. 마지막 호출 latency에 IPC copy를 포함하고 idle60초 unload, parent exit cleanup을 확인한다.

### T06 — GPU 임대와 CPU admission의 공통 조정

**의존:** T03/T05. **Files:** NEW `E/src/main/resources/accelerator-leases.ts`, `E/test/accelerator-leases.test.js`, `C/lease_client.py`, `CT/test_lease_client.py`; MODIFY `E/src/main/backend/plugin-host-bridge.ts`, `E/src/main/plugin/plugin-manager.ts`, `N/src/modules/resources/application/plugin-resource-policy.service.ts`, `N/src/modules/resources/infrastructure/electron-resource-host.service.ts`.

**Interfaces:** `acquireLease(request: LeaseRequest): LeaseResult`; `heartbeatLease(id, owner): void`; `releaseLease(id, exitEvidence): void`. Request=`{plugin_pid,unit_id,worker_pids,start_nonce,adapter_id,epoch,peak_bytes,kind:'foreground'|'calibration'}`; result=`{state:'granted',lease_id}|{state:'busy'|'insufficient'|'unavailable',reason}`. Python `LeaseClient.acquire/heartbeat/release`도 동일 JSON. 추가 worker 등록은 동일 owner/unit/epoch의 lease 갱신으로만 허용하고 전체 peak를 재심사한다.

- [ ] bridge에 `POST /accelerators/leases`, `POST /accelerators/leases/:id/heartbeat`, `DELETE /accelerators/leases/:id`를 추가한다. plugin별 scoped token과 등록한 process tree를 검증한다. Nest의 전체 Bearer token을 Python worker에 복사하지 않는다.
- [ ] `stale heartbeat does not free live memory`: heartbeat5초를 놓쳐도 소유 프로세스 종료 증거 전 임대 강탈 금지. worker는 CPU-only bootstrap→owner 등록→lease→GPU load 순서다.
- [ ] 장치당 foreground heavy unit1개, calibration은 foreground0개일 때만. dedicated 여유에서 max(512MiB,10%) reserve; shared memory는 available RAM에서 max(1GiB,15%) reserve. unknown이면 인증된 최소 batch/단일 worker probe부터; CPU도 기존 RAM/thread admission 통과가 필요하다.
- [ ] E `accelerator-leases.test.js`, N `plugin-resource-policy.test.js`, Python `CT/test_lease_client.py` RED→GREEN. 다른 plugin PID/epoch, simultaneous start, sleep/wake, bridge unavailable, 강제 CPU의 전체 thread budget을 검사한다.

### T07 — 품질 확인 후 제한 실측·순수 선택·캐시

**의존:** T01–06. **Files:** NEW `C/{selection,calibration,cache}.py`, `CT/test_selection.py`, `CT/test_calibration.py`, `CT/test_selection_cache.py`; MODIFY `C/catalog`의 상태 기록.

**Interfaces:** `select_backend(workload: Workload, environment: EnvironmentSnapshot, registry: Registry, measurements: Sequence[Measurement], policy: Policy) -> Selection`; `calibrate(workloads, registry, environment, cancel, deadline) -> tuple[Measurement, ...]`; `SelectionCache.read(key)/write(measurement)/invalidate(changed_fields)`.

- [ ] `test_fast_but_wrong_is_rejected`: CPU100ms/candidate50ms라도 local_quality=False면 CPU. `test_gain_p90_and_cold_cost`: 100→91ms는 유지, 100→89ms이고 p90≤기준×1.05이면 전환 가능, 긴load+짧은작업이면 유지. 입력 개수 unknown일 때 warm 값만으로 cold 전환하지 않는다.
- [ ] fixture hash→현 PC CPU 대 expected→candidate 대 CPU 순서로 검사한다. 인증 범위 밖/자료손상/CPU baseline mismatch면 후보를 활성화하지 않는다. 실제 EP node 배정 증거는 release profile과 연결하고 mixed를 숨기지 않는다.
- [ ] deadline120초와 후보30/60초, 최대2GPU, 시각24/3warm/10×3round를 fake clock으로 시험한다. 다음 idle 회차에 남은 후보와 다른 adapter를 순환 평가하며, 사용자 job 선점 때 완성된 row만 저장; batch1 PASS를 batch8 FAIL이 덮어쓰지 않는다. 고분산/timeout은 inconclusive/deferred.
- [ ] model/pack/precision/preproc/shape/batch/certificate/OSarch/adapter/driver/policy 전체 key, power mode 재측정, deterministic quarantine와 OOM job-only 차단을 구현한다.
- [ ] `$PY -m pytest clipper_accelerators/tests/test_selection.py clipper_accelerators/tests/test_calibration.py clipper_accelerators/tests/test_selection_cache.py -q` PASS. registry/측정/cache로 shadow 선택만 기록하며 이 단계에서 실사용 GPU 기본값을 바꾸지 않는다.

### T08 — 분석 단위 CPU 복구와 결과 commit

**의존:** T05–07. **Files:** NEW `C/{recovery,artifacts}.py`, `CT/test_recovery.py`, `CT/test_artifacts.py`, `N/src/modules/projects/infrastructure/committed-artifact-resolver.ts`, `N/test/committed-artifact-resolver.test.js`; MODIFY 세 plugin `app.py`, dance `services/pipeline.py`, person `result_storage.py`, dialog `services/{stage_contracts,stage_runner}.py`와 `services/pipeline/staged_artifacts.py`; N `src/modules/projects/infrastructure/local-artifact-storage.ts`, `application/{project-artifact-paths,projects.service}.ts`, dialog `application/{dialog-highlight-artifacts,dialog-highlight-workflow.executor}.ts`.

**Interfaces:** `run_with_cpu_recovery(operation: Callable[[AnalysisContext, Path], T], context: AnalysisContext, transaction: ArtifactTransaction, cancel) -> T`; `ArtifactTransaction.begin(unit_id, epoch) -> Path`, `commit(artifacts: Mapping[str, Path], expected_revision: int) -> CommittedArtifacts`, `abort() -> None`. `resolve_committed_artifact(root: Path, logical_path: str, revision: int | None = None) -> Path`; TS `resolveCommittedArtifact(root: string, logicalPath: string, revision?: number): Promise<string>`.

Pointer JSON=`{schema:1,revision,units:{unit_id:{epoch,commit_revision,artifacts:{logical_path:{relative_path,sha256}}}}}`. Generation 경로는 `.acceleration/runs/<unit_id>/<epoch>/`, pointer는 `.acceleration/committed.json`이다. revision과 commit_revision은 단조 증가 정수이고 epoch는 UUID다. unit_id는 경로용으로 검증한 job+stage다. 같은 logical artifact는 가장 높은 성공 commit_revision을 가진 unit의 경로로 해석한다.

- [ ] `test_late_gpu_error_restarts_all_models_once`: frame23에서 GPU 실패→attempt1의 모든 모델은 CPU, gallery도 새 epoch, 성공 결과는 CPU golden과 같아야 한다. CPU도 실패하면 terminal failure이며 attempt2는 없다. bad input/cancel/FFmpeg error는 GPU 재시도 대상으로 분류하지 않는다.
- [ ] 안무의 model 분석 구간과 후속 썸네일/렌더/저장을 구분해 recovery callback으로 감싼다. 알고리즘은 그대로 옮기며 다운로드된 참조 원본은 재사용한다. 인물 분석과 독립 speech 단위를 구분한다. 대사 `analyze_media`는 현재 STT+CLIP 둘 다 포함하므로 이 unit의 CPU 복구에서 둘 다 재계산한다. 독립 `transcribe_media`는 audio 전체만 재계산한다.
- [ ] intermediate는 attempt root에 기록, 성공 generation은 이동하지 않고 hash 검증 후 pointer 파일만 원자 교체한다. begin 시 revision을 pin하고 동일 project commit을 직렬화한다. Windows file-lock 실패 시 기존 pointer를 보존한다. 경로는 허용 root 안에서만 해석한다.
- [ ] `test_cancel_commit_race_has_one_terminal_state`, `test_old_result_survives_failed_attempt`, `test_recovery_rejects_other_epoch_cache`를 구현한다. pointer 변경 후에만 완료 이벤트, 기존 성공 결과·타인 job 삭제 금지.
- [ ] Nest resolver의 pointer 없는 legacy 경로, 한국어/공백, symlink/상위 경로, 실패 generation 미노출, 새 project 조회/파일 serving/기존 clip 편집 경로를 검사한다. 대사 workflow는 stage 성공 뒤 paths를 다시 해석하고 Python의 후속 stage에 committed 입력을 명시한다. logical output_root는 유지한다.
- [ ] Python `CT/test_recovery.py CT/test_artifacts.py`, 기존 `clipper_plugin_sdk/tests/test_completed_event_payload.py` 및 N `committed-artifact-resolver.test.js`, `local-artifact-storage-enoent.test.js`, `project-artifact-paths.test.js`, `dialog-highlight-workflow-executor.test.js` PASS. 서버 LLM mock 호출 수가 복구 때문에 늘지 않아야 한다.

### T09 — YOLO pose: 기존 .pt 대비 ONNX·GPU 후보 연결

**의존:** T01/T07/T08. **Files:** NEW `C/backends/pose.py`, `P/scripts/accelerators/export_models.py`, `CT/test_pose_backend.py`; MODIFY `P/plugins/dance_highlight/dance_highlight/services/pose_engine.py`, `P/plugins/person_highlight/person_highlight/body_detector.py`; 기존 `P/plugins/person_highlight/tests/test_body_detector.py` 확장.

**Interfaces:** `make_pose_executor(context: ExecutionContext) -> PoseExecutor`; `PoseExecutor.infer(preprocessed: TensorPacket) -> PoseOutput(boxes, scores, keypoints)`; consumer별 전처리/NMS/좌표복원은 버전 고정 adapter로 두고 현재 공개 반환값을 유지한다. `export_models.py --model pose.yolov8s --source <pt> --out <dir> --spec <json>`.

- [ ] 현재 안무·인물의 전처리 tensor와 공개 결과를 capture하는 test 작성. 안무 conf=.25/iou=.7, 인물 conf=.1/classes와 추가 dedup, 정사각/세로/가로/ROI, visibility 임계값 양옆을 포함한다. `test_rect_padding_and_keypoint_parity`는 bbox만 같고 keypoint가 달라지면 실패한다.
- [ ] 원본 `.pt` hash에서 batch1/dynamic H/W를 export하고 opset/exporter/weight/preproc hash를 기록한다. 키트 fixed640 ONNX를 제품용으로 인증 없이 대체하지 않는다. MPS/PT-CUDA도 동일 adapter 진단으로 감싼다.
- [ ] ORT CPU를 먼저 기존 PyTorch CPU와 비교하고 DML/CoreML/CUDA를 각각 비교한다. DML sequential/memory-pattern-off/session lock을 명시·auto·probe 경로 공통 적용한다. ONNX GPU만 빨라진 수치를 .pt 대비 배율로 보고하지 않는다.
- [ ] `CT/test_pose_backend.py`, `plugins/person_highlight/tests/test_body_detector.py` PASS와 T01 corpus의 관절/추적/최종clip gate PASS를 후보별로 기록한다. consumer별 인증을 공유 이름만으로 합치지 않는다.

### T10 — YuNet·AuraFace·SFace 실행 객체 주입

**의존:** T01/T07/T08. **Files:** NEW `C/backends/face.py`, `CT/test_face_backend.py`; MODIFY `P/clipper_face_core/clipper_face_core/{opencv_backend,auraface}.py`, dance `services/{opencv_acceleration,face_runtime,secondary_faces}.py`; 기존 `clipper_face_core/tests/test_{opencv_backend,auraface_recognizer,consumer_contract}.py`, `P/tests/test_dance_{face_runtime,opencv_acceleration}.py` 확장.

**Interfaces:** `make_face_executor(context) -> FaceExecutor`; `detect(image: TensorPacket) -> FaceDetections(boxes,scores,landmarks)`와 `embed(aligned_faces: TensorPacket) -> TensorPacket`. 기존 `OpenCvFaceBackend`/AuraFace에 optional executor를 주입하고 기본 factory 동작과 소비자 정책은 보존한다.

- [ ] `test_yunet_compares_decoded_nms_faces_not_raw_anchors`: 실제 얼굴 개수/순서/5점·정수NMS·소비자 .28/.6 임계값 검사. full frame/ROI profile을 구분한다.
- [ ] `test_auraface_batch1_success_survives_batch8_failure`: batch1 인증과 batch8 상태를 별도 기록. 현재 output-shape 오류의 변환 수정은 별도 artifact hash이며 Windows 실제 추론 전 통과 처리하지 않는다.
- [ ] `test_embedding_boundary_keeps_identity`: Aura/SFace cosine≥.99999여도 accept/reject 또는 경쟁 인물 순서가 바뀌면 실패. RGB/정렬/L2/gallery를 고정한다.
- [ ] CPU/OpenCV·ORT CoreML/DML/CUDA 계산 adapter만 공통화한다. 현재 안무 세션 lock/cache/미커밋 품질 로직을 보존하고 인물 정책을 안무 정책으로 통합하지 않는다.
- [ ] 위 CT와 기존 shared face/dance test를 소비자 환경에서 PASS. 등록 얼굴 gallery도 선택 backend/precision/certificate/epoch에 맞춰 생성되며 CPU 복구 때 재계산됨을 확인한다.

### T11 — CLIP image encoder 후보 연결

**의존:** T01/T07/T08. **Files:** NEW `C/backends/clip.py`, `CT/test_clip_backend.py`; MODIFY `P/scripts/accelerators/export_models.py`, `P/plugins/dialog_highlight/dialog_highlight/services/pipeline/{embedding_pipeline,staged_artifacts}.py`; 기존 `P/tests/test_dialog_keyframe_streaming.py` 확장.

**Interfaces:** `make_clip_executor(context) -> ClipExecutor`; `ClipExecutor.encode(batch: TensorPacket) -> TensorPacket`를 기존 `build_openclip_encoder`의 encode callable에 연결한다. export CLI model=`visual.clip_b32`.

- [ ] `test_same_weights_preprocess_and_shot_order`: ViT-B-32/laion2b_s34b_b79k hash, resize/crop/mean/std 픽셀, L2, keyframe order/shot averaging을 비교한다. embedding cosine PASS라도 shot 경계/후속 후보가 다르면 실패한다.
- [ ] original PyTorch CPU/MPS/CUDA와 ONNX CPU→DML/CoreML/CUDA를 비교한다. batch를 늘리는 후보는 별도 certificate이며 스트리밍 소비를 전체 프레임 적재로 바꾸지 않는다.
- [ ] `CT/test_clip_backend.py`, `tests/test_dialog_keyframe_streaming.py`, `tests/test_dialog_analyze_stage.py` PASS. T01의 고정 LLM fixture를 사용해 최종 선택 동일성을 기록하고 remote 호출 변동을 GPU 오차로 섞지 않는다.

### T12 — Whisper 공통 실행·CPU/CUDA·Apple MLX 인증

**의존:** T01/T07/T08. **Files:** NEW `C/backends/speech.py`, `CT/test_speech_backend.py`; MODIFY `P/clipper_speech_core/clipper_speech_core/{model,transcript,cache,worker}.py`, dialog `services/stt_worker.py`, person `speech_stage.py`; 기존 `clipper_speech_core/tests/test_{cache,transcript,worker}.py`, person `tests/test_speech_stage.py` 확장.

**Interfaces:** `make_speech_executor(context) -> SpeechExecutor`; `SpeechExecutor.transcribe(audio_path: Path, *, model_id: str, decode_options: Mapping) -> TimedTranscript`. 기존 `transcribe`/`transcribe_to_file`에 optional executor keyword만 추가해 기본 사용자를 보존한다. `cache_key_v2(source_sha256, backend: BackendKey, decode_hash: str, chunking_hash: str) -> str`.

- [ ] `test_cache_uses_actual_backend_and_decode_contract`: requested cuda였어도 실제CPU면 CPUkey, precision/model revision/단어타이밍/VAD/chunk 변경 시 miss. schema1 결과를 새 engine에서 그대로 쓰지 않는다.
- [ ] CTranslate2 CPU int8/CUDA float16을 기준대로 유지하고 실제 device index를 보존한다. CPU fallback이 내장된 기존 builder의 broad catch가 새 orchestrator의 실패를 숨기지 않게, explicit executor 모드에서는 typed error를 전달한다. 기존 default 호출자 동작은 유지한다.
- [ ] MLX는 동일 small 계열 weights/decode/chunk/timestamp로 변환한 별도 Mac pack 후보로 만든다. `test_mlx_text_timestamp_parity`는 NFC·공백만 정규화, 문장부호 유지, word≤50ms+최종 자막/clip gate를 검사한다. 실패하면 Mac speech는 CPU가 enabled 선택이다.
- [ ] CPU/CUDA/MLX 공통으로 무음/음성 없음/한국어/영어혼합/긴audio/취소를 검사한다. word timestamps=False나 VAD 추가로 속도를 올리지 않는다. 작은 CT core에 MLX를 mandatory dependency로 넣지 않는다.
- [ ] CT와 기존 shared speech/person speech/dialog transcribe test PASS. transcript 전체를 worker가 메모리에 중복 적재하지 않게 현재 chunked feature extraction을 유지하며 길이별 peak와 전체time을 T15에서 기록한다.

### T13 — 추가 vendor 후보의 제한된 확장

**의존:** 기본 모델별 인증(T09–12), T04/T15 harness. **Files:** MODIFY `C/catalog/{models,packs}.json`, 해당 `C/backends/{pose,face,clip,speech}.py`, export/pack script; NEW `CT/test_optional_vendor_candidates.py` 및 실제 인증된 pack lock/manifest만.

**Interfaces:** 기존 factory/BackendKey/Certificate를 그대로 사용하며 별도 선택기나 vendor별 사용자 설정은 만들지 않는다.

- [ ] 순서: NVIDIA ORT TensorRT(필요 CUDA fallback 포함) → Intel OpenVINO → Windows ML vendor catalog/AMD 지원 후보. 플랫폼/OS/driver/모델 조건이 안 맞으면 INELIGIBLE, 장비가 없으면 BLOCKED로 기록한다. Windows ARM은 추가하지 않는다.
- [ ] `test_optional_candidate_cannot_bypass_certificate`로 라이브러리 설치만으로 enabled가 되지 않음을 고정한다. TensorRT engine cache는 GPU/driver/runtime/model/shape/precision을 모두 key로 하며 FP16/INT8은 별도 품질 인증을 요구한다.
- [ ] ROCm/MIGraphX/음성 대안은 Windows x64 해당 배포판의 실제 지원·설치 가능성을 공식 문서와 실기기로 확인한다. CTranslate2의 `cuda` 이름만으로 NVIDIA/ROCm를 구분하지 않는다. 고객PC source build가 필요하면 기본 배포 후보에서 제외하고 CPU/DML을 유지한다.
- [ ] `CT/test_optional_vendor_candidates.py` PASS 후 후보별 T01/T15 gate. 더 느리거나 품질이 다르면 REJECTED 보고서가 정상 완료이며 억지로 지원을 선언하지 않는다. 기본6모델 전체 coverage는 이 optional 후보 채택 여부에 의존하지 않는다.

### T14 — 설정·진단·설치 UI와 전체 연결

**의존:** T02–12. **Files:** NEW `C/diagnostics.py`, `CT/test_diagnostics.py`, `N/src/modules/plugins/presentation/dto/acceleration-settings.dto.ts`, `N/test/plugin-acceleration-contract.test.js`; MODIFY SDK `P/clipper_plugin_sdk/clipper_plugin_sdk/{base,models}.py`, 세 plugin `app.py`, E `src/main/backend/plugin-host-bridge.ts`, N `src/modules/plugins/{domain/plugin.model.ts,application/plugins.service.ts,presentation/plugins.controller.ts}`, A `src/core/plugins/plugin-status.service.{ts,spec.ts}`, `src/shell/dashboard/dashboard.component.{ts,html,scss,spec.ts}`와 필요한 기존 model-download/consent 연결부.

**Interfaces:** SDK `selected`에 schema2 추가(legacy primary 호환 유지). Local Nest `GET/PUT /v1/plugins/:name/acceleration-settings`↔`{mode:'auto'|'cpu'}`; `POST /v1/plugins/:name/acceleration-calibration`↔`{state:'scheduled'|'already_scheduled'}`. plugin name3개만 허용. E bridge에 같은 `/plugins/:name/acceleration-settings` GET/PUT, `/plugins/:name/acceleration-calibration` POST를 추가하고 저장 책임은 Electron userData. Python에는 unit 시작마다 읽을 scoped GET 제공.

- [ ] `plugin-acceleration-contract`에서 T02 JSONfixture를 읽고 Python/TS/Angular가 unloaded/disabled/unmeasured/mixed/recovering/cpu_fallback/quality_blocked를 보존하는지 검사한다. probe GPU 존재를 실제 사용으로 표시하지 않는다.
- [ ] auto/cpu 모드는 다음 unit부터, 다시 최적화는 idle 예약. 실행 중 interrupt/설정변경 없음. calibration 요청 중복은 already_scheduled. bridge unavailable이면 이전 설정 snapshot과 CPU admission을 적용하고 진단에 이유를 남긴다.
- [ ] 실제 model/backend/adapter/precision/certificate, local median과 비교 CPU값, cold/steady, fallback횟수·이유를 표시한다. 측정 전에는 배율을 만들지 않는다. 기본 화면에는 ‘자동’, ‘CPU 사용’, ‘다시 최적화’만 노출하고 내부 engine은 상세 진단에 둔다.
- [ ] CPU attempt 시작 전 GPU모델/worker가 정리되었는지, 모델 로딩/진행/취소 이벤트가 기존 job별 순서로 전달되는지 검사한다. heartbeat/authkey/영상/얼굴vector는 UI로그에 넣지 않는다.
- [ ] SDK runtime accelerator/cancel/completed tests와 CTdiagnostics PASS. N build+`node --test test/plugin-acceleration-contract.test.js`; A `npx ng test --watch=false --browsers=ChromeHeadless --include=src/core/plugins/plugin-status.service.spec.ts --include=src/shell/dashboard/dashboard.component.spec.ts`, `npm run test:styles`, `npm run build:packaged` PASS.

### T15 — 실기기 품질·전체 성능·CPU 복구 출하 판정

**의존:** T01–12/T14; T13은 후보별 추가. **Files:** NEW `P/scripts/accelerators/benchmark_app.py`, `P/tests/e2e/test_acceleration_recovery_subprocess.py`; MODIFY `P/tests/e2e/test_runtime_oom_subprocess.py`, candidate registry 상태; 증거 `D/03-highlight-acceleration-qualification/`.

**Interfaces:** `benchmark_app.py --matrix <json> --corpus <manifest> --baseline <snapshot> --candidate <release> --out <dir>`는 model timing과 실제 stage/app timing·quality·recovery·pack 환경을 한 report에 기록한다. exit0은 요청 matrix의 필수 조합 전부 PASS, exit1 FAIL, exit2 BLOCKED. 시험행 누락을 통과로 바꾸지 않는다.

- [ ] matrix 확정: 저메모리 Apple Silicon(예 M1)+현재 M4, Windows CPU/가속미설치, Intel iGPU, AMD GPU, GTX1660Ti/Win10 build19045, 호환 RTX/Win11, hybrid. 실제 앱 최저OS/ISA·driver floor를 기존 배포와 시험에서 확정하고 해당 범위 밖은 support certificate에 넣지 않는다.
- [ ] 세 플러그인×각 후보에서 T01 최종 품질과 cold/warm 전체 시간을 기준/변경 교차순서로 최소3회 측정한다. 설치·다운로드·컴파일과 분석시간을 분리하고 decoding/FFmpeg/후처리/IPC 시간을 포함한다. 10%model 선택 gate와 5%app 회귀 gate를 별도 판정한다.
- [ ] fault matrix: session load 실패, frame23/긴영상 후반 worker crash, infer timeout, OOM, sleep/wake, GPU0 busy+GPU1, 사용자취소, 한국어경로, 잠긴결과파일, offline 설치완료후, update중단, CPU자체실패. `CPU attempt count == 1`, `committed result == CPU golden`, `LLM call count unchanged`, `owned process leak == 0`를 증거로 남긴다.
- [ ] 패키징 설치본에서 runtime DLL·라이브러리 충돌 없이 CPU/noGPU가 완료되는지 확인한다. 개발환경 pytest PASS를 Windows 설치본 PASS로 대신하지 않는다. 사용할 실제PC가 없으면 해당행 BLOCKED다.
- [ ] shadow(선택기만관측)→모델/소비자별 basic candidate→CUDA/MLX→optional 순서로 enable한다. feature flag off로 이전 certified pack/CPU로 돌아가는 rollback을 설치본에서 시험한다. 신규 namespace/원본/기존 project는 보존한다.
- [ ] 완료 보고에 활성6모델 coverage, disabled2개 유지, 인증범위와 제외범위, 모델별·전체 앱 실측, fallback실패이력, 정확한 pack/model/corpushash, PASS/FAIL/BLOCKED/INELIGIBLE를 모두 첨부한다. 자료 없는 GPU까지 지원 완료라고 표현하지 않는다.

## 단계별 인수 기준

| 인수 단계 | 필수 완료 | 사용자가 얻게 되는 상태 |
|---|---|---|
| 기준·공통 기반 | T01–08 + 기존 회귀시험 | 현재 결과를 고정하고 CPU 복구/격리/선택을 검증할 수 있음; GPU 기본값은 아직 변경 안 함 |
| 기본 자동 가속 | T09–12/T14 + T15 basic matrix | 6모델 모두 자동 관리. 모델별 인증된 Mac/Windows 후보 또는 CPU를 선택 |
| 추가 GPU 최적화 | T13 + 해당 T15 matrix | CUDA/MLX/고급vendor에서 실제 품질·성능을 통과한 범위만 확대 |

설계 §1–3→T01/T02/T09–13, §4→T02, §5→T04/T05, §6→T03/T07, §7→T01/T09–12, §8→T08/T12, §9→T06, §10→T14, §11–12→T15로 추적한다. 현재 계획에는 특정 GPU의 속도나 CPU와 GPU 결과 동등성이 이미 검증됐다는 주장이 없다.
