# Clipper 하이라이트 자동 가속 독립 감사

2026-11-03 KST · 읽기 전용 독립 검토 · 대상: 1차 구현 checkpoint 및 전체 목표와의 차이

**판정: 작업을 보존할 부분 checkpoint로는 수용할 수 있지만, 계획의 ‘기준·공통 기반(T01–08) 완료’로 인수하거나 제품 자동 가속을 활성화할 수는 없다.** 기존 보고가 전체 자동 가속·실제 플러그인 복구·실장비 인증을 미완료라고 명시한 것은 정확하다. 그러나 이미 구현한 공통 경계에도 인증서 재사용, 실행 pack 불일치, 결과 세대 혼합 등 수정할 문제가 있다. 현재 catalogue가 비어 있어 신규 GPU 경로의 제품 노출은 제한되지만, 이 상태를 근거로 공통 기반의 안전성이 입증됐다고 볼 수 없다.

P0 확정 결함은 발견하지 않았다. 아래 **현재 확정 결함 10개(F01–F10)**와 **구현 공백(G01–G04)**, **조건부 위험(R01–R04)**을 분리했다. P1/P2는 수정·출시 우선순위이며 지금 모든 사용자에게 해당 문제가 발생한다는 뜻은 아니다. ‘확정’은 명시한 조건에서 현재 코드를 재현했다는 뜻이다. 감사에서 문제가 발견되지 않은 범위도 전수 무결성 보장은 아니다.

## 1. 범위·변경 구분·보존

| 표기 | 실제 위치 |
|---|---|
| P | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` |
| N | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` |
| E | `/Users/jina/project/adlight/desktop/clipper_electron` — 패키징 연결만 읽음 |
| D | `/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11` |
| T | `/private/tmp/clipper-acceleration-independent-audit-20261103` — 이번 감사의 격리된 재현·로그 |

Python base `4b54bced17e13aadbeb97be75259b7f7213a9b24`, Nest base `e4e1fcf5d37bdbbd2c0c00a9f558b052c2d55f7f`를 기준으로 확인했다. Python은 HEAD 전체 diff 대신 **시작 전 dirty overlay와 현재 코드 사이의 37개 파일**을 검토했다. 보존된 원본으로 unified diff를 재생성하니 `implementation.patch`와 byte 단위로 일치했다(SHA256 `31960a35280e2a8dd6ce1ac7ee974e6b840e1cd334e86d94eeb096242e97aae5`). Nest는 시작 clean 기준의 diff 및 새 resolver/test를 읽었다.

원본 baseline inventory의 Python **615개**, Nest **1,472개** 파일을 현재 원본 checkout과 다시 해시 비교했고 변경은 없었다. 이는 그 inventory 범위의 보존 확인이며 모든 ignored/external 모델·환경까지 새로 조사했다는 뜻은 아니다. 두 작업트리의 `git diff --check`도 통과했다. 제품 source·기존 test·golden은 수정하지 않았고 commit/push/merge, 설치/uv sync, 앱 재시작, GPU 활성화, 외부 LLM 호출을 하지 않았다. TypeScript emit은 T 하위에만 만들었다.

증거: [변경 범위 대조](/private/tmp/clipper-acceleration-independent-audit-20261103/main/scope-check.json), [원본 보존 검사](/private/tmp/clipper-acceleration-independent-audit-20261103/main/original-preservation-check.json). 세부 분담 검토도 최종 판단 전 소스와 재현 산출물을 교차 확인했다: [worker](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/audit-report.md), [선택·품질](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/report.md), [모델·제품 연결](/private/tmp/clipper-acceleration-independent-audit-20261103/models/report-ko.md).

## 2. 현재 확정 결함

| ID | 우선순위 | 문제 | 발생 조건·현재 노출 |
|---|---|---|---|
| F01 | P1 | 인증서가 backend 실행 정체성을 고정하지 않음 | enabled 인증 자료를 넣는 새 registry 경로에서 재현; 현재 배포 catalogue는 비어 있음 |
| F02 | P2 | 실제 worker pack과 요청 pack이 달라도 실행 | 현재 CPU worker로 재현; 실제 pool/installer 연결 전 수정 필요 |
| F03 | P1 | 여러 파일 읽기가 서로 다른 committed revision을 혼합 | 읽는 도중 같은 root에 새 generation commit; 실제 candidate/detail 소비자에서 재현 |
| F04 | P2 | committed 본문 손상 검증 누락 및 `{}`로 은폐 | 커밋 후 파일 변경/손상 시 재현; legacy의 느슨한 읽기를 새 committed 결과에도 적용 |
| F05 | P2 | accelerator만 변경한 재빌드가 venv 갱신을 건너뜀 | 같은 app/plugin 버전·경로·lock에서 공통 package만 변경 |
| F06 | P2 | calibration 후반 workload가 영구 미측정 | 한 회차 총 budget보다 workload 집합이 큼 |
| F07 | P2 | 마지막 comparator에서 예산 초과해도 complete 발급 | 최종 compare 동안 deadline/취소·선점 경계 도달 |
| F08 | P2 | 입력 오류와 OOM의 잘못된 backend 오류 분류 | 로컬 tensor 직렬화 실패 또는 load/infer MemoryError |
| F09 | P2 | bootstrap 인증 정지 후 thread/socket 누수 | 먼저 연결한 local peer가 challenge에 응답하지 않음 |
| F10 | P3 | 잘못된 corpus 구조가 BLOCKED report 없이 종료 | 유효 JSON이지만 최상위가 list 등 잘못된 schema |

### F01 — 인증된 DML을 다른 backend로 바꾸어도 후보·선택 통과

**위치:** [registry.py:47](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/registry.py:47)–61, [contracts.py:101](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/contracts.py:101)–114.

`QualityCertificate`에 model_id/backend/purpose의 정확한 결합이 없고, GPU `_qualified`는 artifact/pack/consumer/preprocess/shape/batch/precision·장치 scope를 검사한 후 backend 이름을 인증과 대조하지 않는다. DML 후보의 이름만 `unimplemented`로 바꾼 경우 후보 목록에 포함되고 **정상 Measurement를 전달한 selector가 실제로 그 후보를 선택**했다. `ort_cuda`로 바꿔도 같은 DML 인증이 허용됐다. 동일 artifact를 공유하는 다른 ModelSpec과 다른 purpose도 허용됐다.

사용자 영향은 검증되지 않은 실행 구현이 인증된 것처럼 선택되는 것이다. 모르는 backend가 worker load에서 나중에 실패하는 것은 품질 gate의 대체가 아니다. 다만 현재 빈 catalogue를 통해 이미 제품 GPU 인증이 우회됐다는 증거는 없다.

**수정:** 인증서를 model/backend/consumer profile과 불변 pack 구현에 결합하고 registry에서 정확히 비교한다. 알려진 backend 문자열 목록만 추가하면 DML→CUDA 재사용은 남는다. **회귀:** backend 불명·다른 backend·다른 model·미인증 purpose에 모두 후보 없음; 이름을 바꿔 만든 유효 timing도 이를 우회하지 못함. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/registry-results.json), [재현 코드](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/registry_repro.py).

### F02 — 시작한 pack A에서 pack B의 인증·측정 identity로 실행 가능

**위치:** [worker_client.py:80](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker_client.py:80)–91, [worker.py:31](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker.py:31)–63.

bootstrap에 실제 pack identity가 없고 load는 artifact hash만 확인한다. `actual-pack/111…`로 시작한 **실제 CPU ONNX worker**에 `different-certified-pack/222…` context를 주어도 load/infer가 `ok`, 출력 `[1,2]`였다. 다른 runtime에서 얻은 결과와 성능이 요청된 pack의 인증·캐시에 귀속될 수 있다.

**수정:** 시작 시 pack id/hash를 worker와 client에 고정하고 모든 load의 BackendKey와 대조한다. T04 설치 manifest 검증도 별도로 필요하다. **회귀:** pack ID만/sha만/둘 다 다른 요청을 session 생성 전에 거부. [재현](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/pack-identity-results.json).

추가 경계 확인: [worker.py:62](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker.py:62), 72–85는 job/epoch/backend만 binding하고 실제 tensor는 ONNX static shape만 검사한다. dynamic Identity 모델에서 선언 shape `(1,2)`, batch=1인데 실제 `(2,2)` 입력도 성공했고, load 후 preprocessing_id 변경도 허용됐다. 이는 **workload 검증 책임이 worker/adapter 사이에 아직 고정되지 않았다는 증거**다. 실제 인증된 제품 adapter 우회로 확대 해석하지 않는다. adapter에서 실제 shape/batch와 인증 workload를 검증하고 worker session도 그 계약에 binding하는 회귀가 필요하다. [결과](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/error-workload-results.json).

### F03 — 원자 pointer 교체만으로 multi-file 소비의 일관성이 보장되지 않음

**위치:** [artifacts.py:174](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/artifacts.py:174)–184, [staged_artifacts.py:342](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:342)–349 및 529–533, [TS resolver:69](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/projects/infrastructure/committed-artifact-resolver.ts:69)–99, [LocalArtifactStorage:9](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/projects/infrastructure/local-artifact-storage.ts:9), [ProjectDetailBuilder:57](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/projects/application/project-detail-builder.ts:57)–64.

resolver는 매 호출 latest pointer를 읽는다. revision 인자가 있어도 실제 소비자는 snapshot을 전달하지 않으며 ArtifactStorage 인터페이스에도 읽기 session/revision이 없다. 한 요청이 첫 파일을 읽은 직후 다른 성공 commit이 발생하도록 제어했다.

- **실제 Python 후보 생성:** `duration=60`인 이전 analysis와 `generation=new`인 새 story를 합친 후보를 저장했다.
- **실제 Nest 프로젝트 상세:** 이전 영상 `clips/v1.mp4`, 길이60과 새 제목 `v2`, 새 자막 `stt-v2`를 같은 응답에 반환했다.

CAS는 stale writer의 commit을 막지만 이 reader race는 막지 못한다. 영상·인물·자막의 조합이 잘못될 수 있다. 새 generation과 동시 읽기가 있어야 드러나므로 현재 pointer 없는 일반 legacy 프로젝트에서 발생했다고 주장하지 않는다.

**수정:** stage/상세 요청 시작 때 성공 revision 또는 immutable artifact map을 한 번 pin하고 그 소비 전체에 전달한다. 다음 stage는 그 stage가 의존하는 성공 commit을 명시적으로 받게 한다. 최신 revision을 각 파일마다 다시 읽지 않는다. **회귀:** 두 파일 사이에 writer commit을 배치해도 결과 전체가 이전 또는 새 revision 중 하나이며, job A의 후속 단계가 job B 자료를 소비하지 않음. [Python 실제 소비자 재현](/private/tmp/clipper-acceleration-independent-audit-20261103/main/python-artifact-repros.log), [Nest 실제 소비자 재현](/private/tmp/clipper-acceleration-independent-audit-20261103/main/node-artifact-repros.log).

### F04 — committed 파일의 hash는 저장되지만 읽을 때 검사하지 않고 손상 JSON은 빈 값으로 숨김

**위치:** [artifacts.py:140](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/artifacts.py:140)–144, 179–184; [TS resolver:92](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/projects/infrastructure/committed-artifact-resolver.ts:92)–99; [LocalArtifactStorage:13](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/projects/infrastructure/local-artifact-storage.ts:13)–18.

커밋한 analysis 본문을 `duration=60`→999로 바꾸어도 Python resolver가 그대로 반환했다. committed manifest를 `{broken`으로 바꾸면 Nest `readJson`은 오류 대신 `{}`를 반환했다. hash는 형식만 검사하고 본문 무결성 확인에 쓰지 않는다. 파일 변경/손상이 전제이며 정상 commit이 스스로 데이터를 망가뜨린다는 증거는 아니다.

**수정:** legacy missing-file 정책과 committed 무결성 오류를 구분한다. committed JSON parse/read 실패를 typed artifact 오류로 보존하고, hash 검증 시점과 immutable generation 보장을 정한다. 큰 영상마다 전량 hash를 반복하는 대신 JSON/manifest 및 최초 검증 캐시 등 비용이 명확한 방식이 적절하다. **회귀:** hash 불일치, invalid JSON, missing generation은 빈 프로젝트나 stale 성공으로 보이지 않음; legacy의 의도된 optional missing 동작은 보존. [재현 로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/node-artifact-repros.log), [Python 로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/python-artifact-repros.log).

### F05 — 공통 package 변경만으로 설치본 venv가 갱신되지 않음

**위치:** 새 의존 [dialog pyproject:7](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/pyproject.toml:7), dance/person 동명 파일; 기존 Electron [plugin-venv.ts:113](/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-venv.ts:113)–143, 163–167 및 84–91.

fingerprint는 SDK·plugin·face/speech core를 포함하지만 새 accelerators source/pyproject/catalog는 포함하지 않는다. 같은 버전·경로에서 accelerator `.py`와 catalog만 바꾼 뒤 `ensurePluginVenv`를 호출하자 **세 plugin 모두 fingerprint 불변, 두 호출 합계 sync 1회**였다. 즉 기존 설치를 그대로 쓴다. 대사는 새 resolver를 이미 import하므로 향후 resolver 수정도 설치본에 누락될 수 있다.

최초 도입 때는 uv.lock/plugin pyproject 변경이 fingerprint를 바꾸므로 최초 설치 불가라는 주장은 아니다. 재현은 현재 Electron TS를 메모리 transpile하고 설치 호출만 mock했다. 실제 uv 재설치는 실행하지 않았다.

**수정:** 세 plugin의 source fingerprint·명시 재설치 목록에 `clipper-accelerators`를 추가. **회귀:** 공통 코드 또는 catalog만 변경해도 sync 호출; 변경 없으면 재사용; 기존 face/speech 기준 보존. `--reinstall-package` 누락만으로 모든 uv 상황에서 stale wheel이 된다는 동적 증거는 없으며, 확정한 것은 marker에 의한 sync 생략이다. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/models/package-result.json), [코드](/private/tmp/clipper-acceleration-independent-audit-20261103/models/repro-package.cjs).

### F06 — 120초 뒤쪽 profile이 다음 idle에도 실행되지 않음

**위치:** [calibration.py:145](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/calibration.py:145)–165.

매 회 workload 목록 처음부터 시작하며 rotation은 profile 내부 GPU offset만 보존한다. 가짜 clock에서 5 profile, CPU/GPU 각각 300ms/infer, 후보당 57회(24품질+3warmup+30측정)를 주었다. 각 후보는 30초 안에 끝나지만 120초 회차를 3번 반복해도 앞의 7개 row만 반복 완료되고 **마지막 profile은 한 번도 open되지 않았다**. 실제 360초를 소모한 장비 시험은 아니다.

**수정:** workload 간 cursor/완료·미완료 대기열을 지속하고 완료 row 재측정 정책을 분리. 또는 호출자가 이 대기열을 공급해야 함을 API 계약으로 강제한다. **회귀:** 두 번째/세 번째 idle에서 마지막 profile도 실행; foreground 중단 후 미완료 지점 재개. GPU offset만 유지하는 현재 시험으로 이를 증명할 수 없다. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/repro-results.json).

### F07 — 최종 품질 비교 이후 취소·기한 확인이 없음

**위치:** [calibration.py:121](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/calibration.py:121)–136.

infer 전후는 확인하지만 마지막 `compare` 후에는 확인하지 않는다. 마지막 비교에서 fake clock을 130초 이동시키니 총 budget120초/후보30초를 넘은 **130.057초 시점에 complete row 1개**가 발급됐다. 사용자 선점이나 취소가 최종 comparator 동안 일어나는 경우도 같은 경계다.

**수정:** 비교 완료 후와 row 확정 직전에 deadline/cancel/foreground를 다시 확인. fixture hash/read 및 close 비용의 예산 책임도 명시한다. **회귀:** 마지막 compare가 deadline 초과/cancel/foreground 변경을 만들면 row 없음, session close 확인. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/repro-results.json).

### F08 — 손상 입력은 backend 장애로, OOM은 영구 장애 후보로 분류됨

**위치:** [worker_client.py:138](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker_client.py:138)–156, [worker.py:58](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker.py:58)–59 및 86–87/138, [recovery.py:81](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/recovery.py:81)–90, [cache.py:17](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/cache.py:17), 132–147.

`TensorPacket(float32,(1,2),b'short')`는 송신 전 길이 검증 실패인데 정상 worker가 종료되고 `BackendFailure('invalid_output')`로 변환됐다. GPU 계획이면 이 타입은 전체 CPU 재실행 대상이다. 반대로 session load/run에 `MemoryError`를 주입하면 `oom`이 아닌 `backend_unavailable`이 됐다. 실제 RAM/VRAM 고갈은 유발하지 않았다.

이는 잘못된 입력을 재시도하지 않는 계약 및 transient OOM을 해당 job에만 격리하는 계약과 맞지 않는다. 현재 cache caller가 미연결이므로 영구 quarantine가 실제 사용자에게 발생했다는 주장은 아니다.

**수정:** 로컬 encode/input validation, transport/response 오류, runtime OOM을 분리한다. runtime별 OOM code/예외를 typed `oom`으로 보존하고 모든 RuntimeError를 OOM으로 간주하지 않는다. **회귀:** bad input은 attempt1/worker 유지, native failure는 정리 후 CPU 1회, OOM은 job-only quarantine, 다음 job 재사용. [입력 재현](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/bad-input-results.json), [OOM 주입 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/error-workload-results.json).

### F09 — 인증 handshake는 부모의 bootstrap timeout으로 정리되지 않음

**위치:** [worker_client.py:92](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker_client.py:92)–108.

authkey를 모르는 local peer가 정상 worker보다 먼저 TCP로 연결해 challenge에 응답하지 않으면 `Listener.accept()` thread가 인증 내부에서 정지한다. `.15초` timeout을 3회 반복한 결과 실제 worker는 모두 종료됐지만 **accept thread 3개가 반환 후 남았고 peer를 닫아야 없어졌다**. listener.close가 이미 accept된 socket을 닫지 못한다. 원격 노출이나 authkey 탈취를 주장하지 않는다.

**수정:** accept와 authentication 모두를 동일 deadline과 명시적 socket 소유·종료 범위에 넣는다. 실패 peer 뒤에도 남은 예산에 정상 worker를 수용할 수 있게 한다. **회귀:** peer를 열린 채 유지해도 timeout 후 thread/FD 수가 baseline 복귀; 정상 worker가 영향을 받은 뒤 안전하게 다음 시도 가능. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/repro-results.json).

### F10 — 잘못된 JSON 구조가 품질 FAIL로 보이고 보고서도 없음

**위치:** [qualify.py:14](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/scripts/accelerators/qualify.py:14)–18, 47–52.

corpus 내용 `[]`를 주면 `.get`의 AttributeError로 exit1, `qualification.json` 없음이었다. 계획의 BLOCKED=2(검증 자료/구조 불충분)와 FAIL=1(품질 불일치)을 구분하지 못한다.

**수정:** top-level/cases/case/outputs 구조를 검사하고 예상 가능한 schema 오류를 BLOCKED report로 변환. **회귀:** `[]`, `null`, `cases:[null]`, outputs list → exit2+reason; 진짜 출력 차이 → exit1. [재현 결과](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/repro-results.json).

## 3. 구현 공백 — 단순 TODO와 실제 전환 실패를 구분

### G01 · P1 · T01의 필수 품질 schema·coverage·CPU baseline이 아직 release gate가 아님

**위치:** [quality.py:129](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/scripts/accelerators/quality.py:129)–153, [qualify.py:13](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/scripts/accelerators/qualify.py:13)–38, [현재 corpus inventory](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/corpus-inventory.json).

`semantic`은 비어 있지 않은 dict 두 개가 같으면 된다. 수치가 같은 embedding에 `semantic={'unchecked':true}`만 넣어도 PASS였다. `schema=999`, `status=BLOCKED`, 없는 baseline, case 1개인 합성 corpus도 파일 해시만 맞으면 **CLI exit0/PASS**였다. `certificate_enabled=false`라 이 CLI가 GPU를 직접 활성화한 것은 아니다. 실제 보관 corpus는 `cases=[]/BLOCKED`이며 이를 통과했다고 주장한 증거도 없다.

이 항목은 구현 보고가 인정한 **manifest/semantic schema 미구현 공백**이 실제 false-PASS를 만드는 경우다. 이전 empty/NaN/True≠1 수정의 회귀와 구분한다. 최종 `(person/type, source, start_frame, end_frame, order, subtitle)`와 소비자별 필수 의미, 승인 expected 출처·baseline 연결, 필수 모델/consumer/장면/언어 coverage를 검사해야 한다. case-level 수치 PASS와 전체 release PASS를 나눈다. 누락·중복 case·placeholder 의미·baseline mismatch·권리 불명 fixture는 release BLOCKED로 남겨야 한다.

현재 baseline 자동 도구/기록은 Python/Nest 두 repo 중심이며 설계의 네 repo·설치 라이브러리·모든 ignored/external 모델·승인 영상 출력·CPU/기존 가속 3회 변동을 함께 재현하는 baseline은 아니다. 일부 모델·corpus 해시는 다른 증거에 있으므로 ‘아무것도 동결하지 않았다’고 평가하지 않는다. [false-PASS 재현](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/repro-results.json).

### G02 · P1 · 실제 plugin 전체 CPU 재실행·generation 생산자 전환 미완료

**위치:** [recovery.py:22](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/recovery.py:22)–93, 실제 대사 producer [staged_artifacts.py:50](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:50)–159/335–421, [stage_runner.py](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/stage_runner.py).

실제 모델 호출에서 신규 선택·adapter·복구 연결은 **6개 중 0개**다. 기존 모델/기존 개별 가속 경로는 그대로 존재한다. 공통 wrapper 시험의 ‘all models CPU’는 context의 BackendKey를 바꿔 더미 callback을 다시 호출한 결과이며, gallery/tracking/STT/CLIP가 새 CPU 객체로 재계산됐다는 증거가 아니다.

연결 누락은 이미 공개된 TODO지만 구체적 전환 실패도 재현했다. 이전 analysis를 committed generation에 둔 뒤 **현재 `analyze_video_to_artifacts`**를 실행하면 새 논리 `json/analysis.json`과 반환값은 duration120인데 `_load_required_json`은 이전 duration60을 읽는다. 생성자는 기존 경로에 쓰고 새 reader는 pointer를 우선하기 때문이다. 모델·ffmpeg만 fake API로 교체했고 쓰기/읽기 함수는 현재 코드 그대로 사용했다. pointer 없는 legacy만 시험하면 드러나지 않는다. [재현 로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/python-artifact-repros.log).

**필요 조치/회귀:** producer·reader·rollback을 한 계약으로 전환하고 job/stage가 자신의 commit revision을 전달하게 한다. 기존 프로젝트→첫 generation→다음 CPU 실행→feature rollback까지 새 결과가 보이는지 시험한다. JSON 속 절대 경로의 owned-root 재작성, 논리 output_root 유지, 사용자 편집/렌더의 위치 분리도 실제 producer에서 검증해야 한다. 지금 `ArtifactTransaction.commit`은 파일 목록과 hash를 만들 뿐 JSON 내부 경로나 returned value를 재작성하지 않는다.

모델 상태의 필수 경계는 다음과 같다. 아래 기존 코드의 상태·fallback 자체를 이번 신규 회귀로 집계하지 않는다.

- **안무:** [app.py:43](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/app.py:43), 59–65/147의 pipeline 재사용, [face_runtime.py:57](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/face_runtime.py:57)–81/154–176의 input-only cache, [opencv_acceleration.py:238](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:238)–246의 SFace 객체까지 새 CPU attempt에 재사용하면 안 된다. source 참조 이미지에서 AuraFace/SFace gallery를 각각 다시 만들고 첫 프레임부터 selector/tracker/anchor를 재실행해야 한다.
- **동기 참조 검사:** [app.py:90](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/app.py:90)–114의 `/dance/reference/validate`도 같은 `pipeline.face.get_face_embedding`을 호출한다. 영상 job wrapper만 연결하면 이 YuNet/AuraFace 소비자는 빠진다. 독립된 작은 분석 단위·CPU 복구·취소/오류 응답 계약을 마련하고 실행 중 job의 모델 상태를 다른 route가 바꾸지 않게 해야 한다. 이 route도 현재 신규 복구와 미연결이다.
- **인물:** [analysis.py:469](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/person_highlight/person_highlight/analysis.py:469)–490의 tracker·sampler·frame inference를 시작부터 다시 만들고, 대표 얼굴/thumbnail/JSON의 쓰기를 attempt에 넣어야 한다. 독립 speech job과 인물 분석 job의 재시도 범위는 별도다.
- **대사:** analyze_media는 STT와 CLIP를 함께 CPU로 재실행해야 한다. [embedding_pipeline.py:37](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/pipeline/embedding_pipeline.py:37)–56의 `(model,pretrained,device)` cache, [speech model.py:11](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_speech_core/clipper_speech_core/model.py:11)/37–46의 model cache, [speech cache.py:18](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_speech_core/clipper_speech_core/cache.py:18)–55의 schema1을 새 engine/precision/pack/epoch와 혼용하지 않는다. 기존 `cuda:1→cuda` 정규화도 explicit adapter를 보존하지 못하므로 새 경로에 그대로 쓰지 않는다.
- **LLM/부작용:** [workflow:134](/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103/src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts:134)–243의 서버 LLM은 local analysis wrapper 밖에 둔다. 전체 Nest workflow 재시작은 기존 LLM/파일 쓰기를 반복할 수 있다. 기존 mock 시험은 분석을 실제로 실패·CPU 복구시키지 않고 committed 파일을 배치하므로 ‘실제 복구 중 LLM 중복 없음’은 아직 미검증이다.
- **난수·오류·취소:** epoch 변경만으로 native RNG/전역 상태를 초기화했다고 보지 않는다. 실제 CPU golden 반복과 fault injection이 필요하다. 기존 broad model fallback/음성 실패를 빈 결과로 취급하는 경로도 새 typed failure를 가리지 않게 검토한다. CPU도 실패하면 두 원인, 취소/timeout/OOM, 늦은 frame 실패, cleanup 실패를 실제 서비스로 시험해야 한다.

### G03 · P1 · 환경·설치·자원·소유권은 아직 관측/계약 수준

**위치:** [environment.py:16](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/environment.py:16)–40, [contracts.py:153](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/contracts.py:153)–158, [worker.py:37](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker.py:37)–40, [packs.json](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/catalog/packs.json).

전달된 OS/arch/adapter를 정규화하고 미지원 native arch/unknown scope를 제외하는 로직은 있다. 그러나 native DXGI/Apple probe, stable device↔실제 runtime index 증명, pack lock/설치 완료 marker/호환 DLL·드라이버·ISA·rollback, 실제 host credential/lease/heartbeat/CPU admission은 없다. `lease_id`가 truthy라는 조건은 자원 승인 증거가 아니다. available RAM/VRAM 숫자가 타입에 있다는 것과 실제 admission이 연결됐다는 것은 다르다.

Windows x64/Apple Silicon native, 복수 GPU/hybrid, CPU-only/드라이버 미지원, offline·손상 pack·업데이트 중단·저메모리·sleep/wake는 **미검증**이다. Intel Mac/Windows ARM 제외 필터의 synthetic 통과를 실제 설치본의 native 판별 PASS로 확대하면 안 된다. CPU fallback도 준비된 CPU runtime·RAM·ISA·thread admission이 있어야 가능하다.

### G04 · P1/P2 · 실제 진단·UI·출하 매트릭스 없음

모델별 실제 backend/adapter/precision/certificate/혼합 graph·cold/steady·fallback 이력의 SDK/TS 공유 계약과 사용자 설정 UI는 미완료(P2). ORT `get_providers()`에 GPU가 있다는 것은 노드 배정 증거가 아니며 worker도 `requires_profile`을 반환한다. GPU default를 켜기 전 target hardware의 최종 품질·전체 앱 시간·pack 설치본·복구 fault matrix가 필요하다(P1). 현재 빈 certificate와 BLOCKED를 유지하는 것이 맞다.

## 4. 조건부 위험과 개선 제안

| ID·우선순위·분류 | 근거·재현 | 수정 및 필요한 회귀 |
|---|---|---|
| R01 · P2 · 조건부 성능 위험 | [calibration.py:102](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/calibration.py:102)–135는 open 시간과 session.compile_ms만 저장하고 품질/초기 infer 비용을 제외. fake session CPU100ms, GPU 첫 infer5001ms/이후1ms에서 1건 작업에 GPU 선택. 실제 adapter가 없어 native 발생 미검증. | load/compile/first-infer/steady의 중복 없는 정의와 cold overhead 측정. compile이 load 안/첫 infer 안에 있는 두 경우 및 warmed/cold 짧은·긴 작업 회귀. |
| R02 · P1 활성화 전 gate · 조건부 소유권 위험 | [worker_client.py:59](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker_client.py:59)–71는 PGID만 확인. child가 setsid하면 close=True여도 child 생존 재현. 현재 OnnxRunner가 이런 child를 만든다는 증거 없음. [worker.py:99](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker.py:99)–108의 내부 watchdog은 GIL 점유/SIGSTOP에서 못 돌 수 있음(기존 보고가 인정한 한계). | group 소유권만 보장할지 외부 host가 descendant tree를 감독할지 명시. leader crash·새 session 자식·native hang·부모 사망·Windows nested Job Object/실제 종료 수 회귀. 기존 일반 PGID child 종료 수정은 유효하나 전체 tree 증명은 아님. |
| R03 · P2 · 조건부 response schema 위험 | [worker_client.py:160](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/worker_client.py:160)–163에서 인증된 fake peer의 `error=[]`가 AttributeError로 전파되고 worker 생존. 정상 worker.main은 이 응답을 만들지 않음. | status/error dict/kind/message schema 검증 후 invalid_output+정리. null/list/unknown kind/missing status 회귀. |
| R04 · P2 · 측정·모델 계약 개선 제안 | [calibration.py:116](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/calibration.py:116)–126/155–164는 CPU 모든 round 후 GPU 모든 round. 설계의 교차 순서 미구현. [quality.py:92](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/scripts/accelerators/quality.py:92)–99는 다시 정규화한 cosine만 비교. CLIP frame scale/shot mean, 전처리 pixels 검사는 없음. | CPU/GPU round 교차 및 부하·발열 추세 검증. CLIP 원래 per-frame L2→shot mean→L2 결과와 최종 경계 비교. AuraFace raw norm 차이를 일률 결함으로 취급하지 말고 모델별 계약을 명시. |

캐시 관련 이전 동시 쓰기/격리 소실 수정은 key별 OS lock 안의 load→update→atomic save로 반영됐고 multiprocessing 시험에서 재발하지 않았다. Windows `msvcrt` 분기는 실기기 미검증이다. measurement key는 model/consumer/preprocess/purpose/shape/batch, BackendKey 전체, OS/arch/device/driver/power 포함 environment fingerprint, policy version을 사용한다. estimated_items 제외는 측정을 작업 길이별로 재사용하려는 설계에 맞는다. 그러나 quarantine를 실제 candidate/idle 실행에 적용하고 전원 변경 시 재측정을 예약하는 연결은 아직 없다.

## 5. 활성 6모델·모든 현재 소비자 대조

아래는 현재 코드를 읽어 확인한 계약이다. 모든 행에서 **새 adapter·신규 자동 선택·실제품 전체 CPU 복구는 미연결**이다. 실제 기존 모델별 결과를 이 감사에서 전수 실행하지 않았으므로 표는 품질 PASS가 아니다.

| 모델·소비자 | 보존해야 할 입력/후처리·shape/batch/precision | 근거 및 빠진 검증 |
|---|---|---|
| YOLO pose · 안무/인물 | 기존 yolov8s-pose.pt/Ultralytics. 안무 기본 imgsz640/conf.25/iou.7/half 정책, **native scene imgsz1920**. 인물 conf.1/classes0, 정수 bbox·HSV appearance·추가 중복 제거; half/imgsz/iou 명시 없음. 관절17/head confidence·letterbox/좌표 복원 보존. | [안무 pose:20](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/pose_engine.py:20), [native scene:275](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/native_scene.py:275), [인물:43](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/person_highlight/person_highlight/body_detector.py:43). 고정640 ONNX transport가 .pt/rect/native1920/소비자별 NMS 품질을 증명하지 않음. |
| YuNet · 안무/인물 | 2023mar, BGR source native W/H·가변 ROI. 안무 score.28, 인물 앱 .75(shared 기본 .6), NMS.30/topK5000. 기존 안무 가속 full-frame의 32배수 padding·FP32 blob·decode/NMS 및 ROI CPU 유지. | [shared:23](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_face_core/clipper_face_core/opencv_backend.py:23)–49, [인물 app:76](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/person_highlight/person_highlight/app.py:76), [안무:128](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:128)–190. 640 raw 12tensor 동등성과 실제 box/landmark/threshold 동등성은 다름. |
| AuraFace · 안무/인물 | YuNet5점→LMEDS affine→112×112 BGR→RGB/127.5 FP32 NCHW batch1→512→L2. 인물 min embedding score.85/size48 필터. reference/video의 같은 정렬·gallery 공간 필요. | [auraface:21](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_face_core/clipper_face_core/auraface.py:21)–53, [인물 app:184](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/person_highlight/person_highlight/app.py:184). 준비 tensor 30개 transport만 존재; 정렬/identity/unknown·경쟁 인물 최종 gate 없음. batch8을 자동 확대하면 안 됨. |
| SFace · 안무 보조 | OpenCV alignment, RGB FP32 scale1 112×112→128. AuraFace와 별도 gallery, cosine distance.637/roster margin.08·반복 시점 증거. secondary recognizer cache 재생성 필요. | [secondary_faces:137](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/secondary_faces.py:137), [가속:193](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py:193)–246. 새 worker 실모델·이중 인식기 최종 판정 증거 없음. |
| CLIP visual · 대사 | ViT-B-32/laion2b_s34b_b79k image encoder. BGR→RGB→PIL→원래 preprocess→stack, eval/no_grad, per-image L2→shot 평균→L2→cosine 차이. 현재 기본 1 keyframe/shot; 3개 경로도 존재. 명시 half/autocast 없음. | [embedding:55](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/pipeline/embedding_pipeline.py:55)–106. ONNX(1,3,224,224) transport가 OpenCLIP weight/export/preprocess/batch/shot·최종 선택 인증을 대체하지 않음. |
| Whisper small · 인물/대사 | faster-whisper/CTranslate2 CPU int8, CUDA float16, MPS 요청 CPU. chunked mel, 실제 호출 VAD=False/word_timestamps=True, segment/word text/time·무음/no-audio 유지. | [model:34](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_speech_core/clipper_speech_core/model.py:34)–53, [transcript:84](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_speech_core/clipper_speech_core/transcript.py:84)–121, [인물 speech:28](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/person_highlight/person_highlight/speech_stage.py:28). 새 worker는 CT2/MLX 미구현. 오래된 VAD=True 상수를 실제 계약으로 삼지 말 것. |
| SAM2·EasyOCR · 비활성 유지 | SAM2 runtime 비활성/주석 경로와 RUN_OCR=False 유지. 자동 설치/측정/실행 대상으로 추가하지 않음. | [catalog](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/catalog/models.json), [대사 common:28](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dialog_highlight/dialog_highlight/services/pipeline/common.py:28), [안무 app:82](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/plugins/dance_highlight/dance_highlight/app.py:82). active false와 실제 상태 일치. |

**shape/IPC의 숨은 선행조건:** [protocol.py:8](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators/clipper_accelerators/protocol.py:8)–29의 64MiB 한도에서 3840×2160 FP32 NCHW YuNet 입력은 99,532,800 bytes라 초과한다. 기존 native/ROI 계약을 640 resize로 일괄 바꾸면 품질 변경이다. 인증 profile과 transport 가능한 크기를 함께 정의하고 나머지는 원래 CPU 경로에 남겨야 한다. 이는 신규 adapter의 구현 요구이며 지금 원래 YuNet이 4K를 못 처리한다는 주장은 아니다.

**CPU 기준의 실제 의미:** registry의 기본 CPU는 YOLO/CLIP=torch, YuNet/SFace=OpenCV, Whisper=CT2, AuraFace=ORT다. 현재 worker는 ORT만 구현한다. CPU ONNX 결과가 bit-equivalent라고 해서 기존 torch/OpenCV/CT2 기준까지 같은 것으로 치환하면 안 된다.

## 6. 설계 요구사항별 구현·검증·미검증 매핑

| 계획/요구사항 | 현재 구현 | 이번 감사·기존 증거의 유효 범위 | 아직 필요한 인수 증거 |
|---|---|---|---|
| T01 baseline/품질/corpus | 비교기·snapshot·recorded qualification CLI, BLOCKED inventory | 수치·의미 일부 경계 시험, 원본 hash 보존; G01/F10 확인 | 필수 schema/승인 CPU·기존 가속 최종 golden, 6모델3plugin coverage, 배포24시각/3음성 fixture·권리·25MiB, 반복3회 |
| T02 계약/registry/package | 경량 dataclass/catalog, workspace deps | active6/disabled2, heavy import 없음, 19시험; F01/F05 | backend/IO/CPU factory/source·정밀도/shape·pack support 완전 계약, TS/Python 공통 fixture, wheel/설치 갱신 |
| T03 native 환경 | 전달 snapshot 정규화·adapter unique mapping 함수 | synthetic OS/arch/unknown·중복 매핑 시험 | 실제 DXGI/Apple native 판별·driver/복수 GPU↔runtime 장치 대응 |
| T04 pack | 미구현, catalogue 비어 있음 | 빈 값이 enabled를 만들지 않음 | 정확 lock/hash/ABI/ISA·설치 smoke/취소/offline/손상·업데이트/rollback |
| T05 worker | ORT CPU/DML/CUDA/CoreML, 인증 loopback/binary IPC·기한·소유 그룹/WindowsJob 재사용 | protocol/수명 시험23개, tiny CPU 실실행; F02/F08/F09. 기존 첨부4모델102입력/366tensor transport | native GPU/Windows, 실제 EP partition/adapter 증명, 실제 partial-frame/blocked-send/stale fault 확대, host 소유·lease |
| T06 자원 조정 | 미구현 | 계약/placeholder만 확인 | GPU lease·heartbeat/credential, CPU admission·thread/RAM 총량, 동시3plugin·sleep/wake |
| T07 선택/measurement/cache | pure 선택, 제한 trial, key/atomic cache·quarantine | 10%/p90 gate와 cache 동시성 대상 시험; F06/F07/R01 | workload 대기열·실제 idle/foreground·cache quarantine 연결, cold 정의·교차 측정·실제 성능 |
| T08 분석 복구/atomic 공개 | wrapper·attempt cleanup·CAS pointer·일부 reader | dummy operation CPU1회·2차 실패·취소·stale writer·이전 결과 보존. F03/F04/G02 | 3plugin 실제 state/gallery/cache 재계산, 전체 producer·consumer·revision·절대경로, 실제 fault와 CPU golden/LLM 횟수 |
| T09 YOLO/T10 face/T11 CLIP/T12 speech | 새 adapter 미구현 | 기존 consumer 코드 대조; CPU transport는 4모델 일부 profile | 위 표의 모든 consumer/shape/batch/전후처리·최종 품질, 각각 원래 CPU 기준부터 연결 |
| T13 optional vendor | 미구현 | 인증을 켜지 않음 | 기본 경로 통과 뒤 optional lock/device/품질·속도 인증 |
| T14 진단/UI | 미구현 | 신규 상태가 실제 runtime/UI까지 전해진다는 증거 없음 | auto/cpu/idle 재측정, selected≠available, mixed/recovering/fallback/quality_blocked 공유 계약 |
| T15 출시/롤백 | 미구현 | release BLOCKED 보고는 정직함 | native Mac/Windows matrix, 설치본·CPU-only/offline/실GPU·E2E 품질, app regression≤5%, fault CPU1회/LLM불변/leak0 |

‘기준·공통 기반’ 인수 표는 T01–08+기존 회귀를 요구한다. 현재는 T04/T06 미구현, T01/T02/T03/T05/T07/T08 부분 완료이므로 **그 단계의 완료 판정은 충족하지 않는다**. 문서의 ‘1차 부분 구현’ 표현은 유지 가능하지만 ‘CPU 복구 검증 완료’는 공통 callback/transaction 시험 범위로 한정해야 한다.

## 7. 실제 실행한 검증·기존 결과의 해석

| 검증 | 이번 실행 결과 | 한계/증거 |
|---|---|---|
| Python artifacts/recovery/dialog candidate/completed event | **29 passed** | [로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/python-regression.log). tmp·cache off·원래 interpreter+작업트리 PYTHONPATH |
| Python registry | **19 passed** | [로그](/private/tmp/clipper-acceleration-independent-audit-20261103/models/registry-tests.txt) |
| Python quality/selection/calibration/cache + missing fixture | **50+1 passed** | [선택 보고서 명령](/private/tmp/clipper-acceleration-independent-audit-20261103/selection/report.md). baseline snapshot test는 임시 git commit을 만들므로 실행하지 않음 |
| Python protocol/worker/environment | **23 passed** | [worker 보고서](/private/tmp/clipper-acceleration-independent-audit-20261103/worker/audit-report.md). 최초 sandbox의 8 loopback 실패 후 허용된 로컬 실행으로 통과 |
| Python 대상 합계 | **122 passed** | 전체 suite 재실행 수치가 아님 |
| Nest resolver/storage/path/workflow | **34 passed** | [로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/node-regression-authorized.log). 최초 1건 localhost EPERM 후 같은 대상 허용 실행 |
| TypeScript | **noEmit 및 T 안 격리 emit 성공** | [빌드 로그](/private/tmp/clipper-acceleration-independent-audit-20261103/main/typescript-isolated-build.log). 검사한 source4개와 테스트가 읽은 기존 dist JS가 동일함 [대조](/private/tmp/clipper-acceleration-independent-audit-20261103/main/compiled-output-check.json); copy-assets/설치본 build 재실행 아님 |
| 새 결함 재현 | Python **3개 기대조건 실패**, Node **2개 기대조건 실패** | [Python](/private/tmp/clipper-acceleration-independent-audit-20261103/main/test_artifact_audit.py), [Node](/private/tmp/clipper-acceleration-independent-audit-20261103/main/artifact_audit.test.cjs). 수정 전 오동작을 보존한 감사 시험이며 제품 테스트에 추가하지 않음 |
| 나머지 재현 | registry/CLI/calibration fake clock, Electron freshness mock, 실제 tiny CPU ONNX/worker 및 fault injection | T의 각 결과 JSON. GPU 실측·실제 OOM이 아님 |
| 원본·diff | 원본 inventory 2,087파일 hash 일치, Python37파일 patch 일치, 양쪽 diff check 성공 | 전체 ignored/external 자산·현재 실행 앱 상태까지 보증하지 않음 |

주요 재현 명령은 각 세부 보고서와 T의 스크립트에 있다. main Python 검증은 P에서 다음 형식으로 실행했다.

```text
UV_NO_SYNC=1 UV_PROJECT_ENVIRONMENT=/Users/jina/project/adlight/desktop/clipper_python/.venv python3 .implementation-evidence/run_tests.py -q -p no:cacheprovider --basetemp=<T 안 임시폴더> <대상 테스트>
```

Nest 대상은 `node --test test/committed-artifact-resolver.test.js test/local-artifact-storage-enoent.test.js test/project-artifact-paths.test.js test/dialog-highlight-workflow-executor.test.js`였다. 외부 LLM은 mock이며 local HTTP/child process만 사용했다.

**기존 전체 로그를 직접 비교한 결과:** [baseline 대조 JSON](/private/tmp/clipper-acceleration-independent-audit-20261103/main/baseline-log-comparison.json).

- Python 최종 기록의 3,049 passed/6 failed/7 skipped는 로그와 일치한다. 6개는 annotation counter/chip/arrow/arrow-above/no-area byte hash 및 fadeblack transition이다. baseline에도 모두 있고 **6개 AssertionError 내용·픽셀 차이·hash·fadeblack 수치까지 동일**했다. 따라서 이 6개를 이번 가속 변경이 새로 만든 실패라고 볼 근거는 없다.
- 다만 baseline 전체 기록은 2,910 passed/**10 failed+17 errors**/5 skipped였다. 나머지 4실패+17error에는 loopback `PermissionError` 21개가 기록돼 있다. 같은 권한의 clean baseline 전체 성공표가 아니므로 단순 통과 개수 증가를 새 기능 검증량이나 전수 회귀 증명으로 해석하지 않는다. 기존 golden 실패는 여전히 제품 품질 gate에서 별도 설명/해결이 필요하며 golden을 새 출력으로 바꾸어 감추면 안 된다.
- Nest 기존 최종 로그의 5,246 passed/0 failed/9 skipped 및 기존 build 기록을 확인했다. 이번 감사가 그 전체 시험을 새로 5,246회 돌렸다는 뜻은 아니다.
- 네 ONNX의 102입력/366출력/절대차0 기록과 실행 스크립트를 읽었다. 같은 ORT1.31.0 CPU 직접 실행 대 worker로 **이미 전처리된 tensor**를 비교한 것이 맞다. 이 감사에서는 그 대형 4모델 추론을 재실행하지 않았다. .pt→ONNX/OpenCV→ORT 변환, SFace/Whisper, 실제 영상/최종 하이라이트, GPU 품질·속도 인증으로 사용할 수 없다.

**확인하지 못한 범위:** native Windows(경로 잠금/Job Object/msvcrt/설치 DLL), 실제 CoreML/DML/CUDA/MLX 및 복수 GPU, 모든 실영상·참조 얼굴의 최종 결과, 장시간 native hang/OOM/sleep, 설치본 업데이트/rollback, 실시간 app/UI. 이 범위는 ‘문제 없음’이 아니라 **미검증**이다. POSIX 일반 자식 종료·Windows 문자열 정규화의 시험 통과를 해당 전체 플랫폼 PASS로 확대하지 않았다.

## 8. 다음 순서와 인수 권고

1. **P1: 인증·품질 gate부터 고정.** F01과 G01을 먼저 닫고 모델/consumer별 required semantic·원래 CPU baseline을 확보한다. record 비교 도구는 부분 PASS와 release BLOCKED를 분리한다. 빈 catalogue/신규 GPU off는 유지한다.
2. **P1: 하나의 실제 CPU 실행 경로를 먼저 완성.** 한 plugin의 실제 모델 서비스→새 CPU 계획→새 상태/gallery→generation commit→Nest/후속 Python 읽기까지 연결한다. backend fault는 주입해 전체 단위가 한 번만 CPU로 돌아가는지 실제 golden과 비교한다. F03/G02의 revision·producer/reader·rollback을 이 단계에서 닫는다. 모든 generic 기반·vendor pack을 끝낸 뒤 처음 제품 경로를 연결하는 순서는 통합 결함을 너무 늦게 드러낸다.
3. **P2: 기반 경계 보수.** F02/F04/F05/F08/F09와 response schema를 수정하고 해당 최소 재현을 회귀에 넣는다. worker pack provenance·오류 분류·완료/취소·무결성이 깨진 상태에서 GPU 후보 수를 늘리지 않는다.
4. **P1: 6모델·모든 소비자로 CPU 복구 확장.** 원래 torch/OpenCV/CT2 CPU factory를 먼저 유지한다. 전체 모델 객체를 새로 만드는 명확한 reset이 가능한 곳은 복잡한 cache epoch 교정 체계보다 이를 우선한다. 기존 STT cache는 새 namespace와 명시 identity를 마련한다. LLM·사용자 편집·렌더를 재시도 밖에 두고 source/ref만 재사용한다.
5. **P1/P2: native 환경·pack·host lease와 측정 연결.** 설치된 exact pack·host 소유권·CPU admission 뒤에만 GPU load. F06/F07/R01을 해결하고 workload 순환·교차 round·cold/steady·IPC/전후처리 총비용을 실제 adapter로 검증한다. 전체 app gate(5%)와 모델 선택 gate(10%)를 혼동하지 않는다.
6. **P1: 실기기 출하 gate.** 낮은 메모리 Apple Silicon/현재 Mac, Windows CPU-only·Intel/AMD GPU·지원 NVIDIA·hybrid 등 계획 matrix에 PASS/FAIL/BLOCKED를 남긴다. 설치본에서 후반 crash/timeout/OOM/취소/두 번째 실패/한국어 경로/locked file/offline/update 중단을 검사한다. CPU attempt=1, CPU golden 동일, LLM 호출수 불변, 소유 process leak=0를 확인한 후보만 shadow→모델별 활성화한다.

공통 계약·worker 격리·작은 pure selector를 나눈 방향 자체를 폐기할 근거는 없다. 현재 가장 큰 위험은 **계약을 실제 소비자·설치본·품질 증거에 연결하지 않은 채 완료로 확대하는 것**이다. 기반 API의 확정 결함을 먼저 수정하고 실제 CPU 경로 하나를 끝까지 통과시킨 뒤 확장하는 편이 다음 단계의 판단 근거를 더 빨리 만든다.
