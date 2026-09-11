# Windows 소유 프로세스 트리 보완 보관본 — 2026-09-10

**미커밋·미푸시·미배포. 실제 ML 플러그인 실행 및 Build5 전체 QA HOLD.**

이 보관본은 앞선 `2026-09-10-resource-safety`를 기반으로 R5를 추가한 **4개 저장소 / 50개 파일 전체 패치**다. 기존 CPU 개선과 R1~R4·watchdog·UI 변경을 포함한다. 이전 보관본 37개 파일은 작업본과 byte 단위로 동일함을 재확인했다. 이번 R5 추가 변경은 Electron6/Nest5/Python2 = 13개 파일이다. Angular는 이번에 변경하지 않았다.

## 복구

1. `manifest.json`의 저장소별 `baseCommit`을 기준으로 **별도 clean checkout**을 만든다. 원본 공유 checkout이나 기존 CPU/안전성 패치를 적용한 checkout에 중복 적용하지 않는다.
2. 각 checkout에서 해당 `<repository>.patch`의 SHA-256을 manifest와 대조한다.
3. `git apply --check --whitespace=error <patch>` 후 `git apply <patch>`를 실행한다.
4. CPU → 안전성 → R5 패치를 차례로 적용하는 형태가 아니다. 이 폴더의 패치 하나가 해당 저장소의 누적 전체 변경이다.

보관 당시 네 저장소 모두 기준 파일 복원 → 패치 적용 → 작업본 전체 50파일 byte 대조를 통과했다. 이전 CPU·안전성 보관본은 변경하지 않았다.

작업본: `/private/tmp/clipper-resource-dashboard-review/`.

## R5 구현

- Python SDK `windows_supervisor`가 실행별 비상속 Job Object 핸들을 보유한다. `KILL_ON_JOB_CLOSE`, breakaway 미허용. `CreateProcessW + PROC_THREAD_ATTRIBUTE_JOB_LIST`로 실제 플러그인을 생성 시점부터 해당 Job에 넣는다. 생성 후 PID를 찾아 넣는 방식은 사용하지 않는다.
- 플러그인에 상속하는 핸들은 NUL stdin·복제한 stdout·stderr만이다. supervisor의 호스트 제어 stdin과 Job 핸들은 플러그인에 상속하지 않는다.
- 호스트 제어 stdin EOF 또는 실제 플러그인 종료 시 해당 Job만 종료하고 `ActiveProcesses == 0`을 재조회한 뒤 JSONL 확인 이벤트를 보낸다. 기동 전 EOF는 플러그인을 실행하지 않는다. 생성/정리 실패는 확인 이벤트 없이 오류가 된다.
- Electron dev/packaged와 Nest local의 Windows 실행만 supervisor를 거친다. 호스트는 `exit`만으로 완료 처리하지 않고 stdout 확인 이벤트와 `close`를 함께 기다린다. 제어 요청은 stdin 종료이며 임의 PID나 프로세스 이름으로 강제 종료하지 않는다.
- 확인되지 않은 close/정리 실패는 관리자까지 오류로 전달하고 process·port를 보존한다. 재시작을 거부한다. 이전 실행의 늦은 callback은 다른 실행의 소유 상태를 해제하지 못한다. POSIX의 기존 graceful→SIGTERM→SIGKILL 경로는 유지한다.

Windows10+/Server2016+ API를 사용한다. 근거: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [원자적 Job 할당 설명](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812), [프로세스 생성 속성](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).

## 검증 범위

- Electron 관련 테스트19 통과. Nest 관련 회귀·R1~R4·watchdog 테스트66 통과. Python supervisor 테스트10 통과.
- Electron/Nest TypeScript 빌드 통과. Python 구문 컴파일 통과.
- 모의 ChildProcess/health/WinAPI와 로컬 포트 할당만 사용. WinAPI 테스트는 x64 구조체 크기/offset·생성 속성/핸들 목록·정리 재조회/시간 초과를 검증하며 실제 Windows 호출은 아니다.
- 신규 테스트 실패를 먼저 확인한 뒤 구현. 독립 리뷰에서 발견한 proof 없는 close의 관리자 해제 문제를 보완하고 통합 테스트 추가. 재검토에서 잔여 blocker 없음.
- 원본8repo branch/HEAD/status/tracked diff hash 및 원격8repo dev·배포 branch HEAD가 직전 기록과 동일. `fetch`/merge/reset/stash/commit/push 없음.
- Angular는 직전48테스트·packaged 빌드 통과 기록을 유지하며 이번에 반복하지 않았다. 이전 안전성 전체 검증은 상위 후속 문서 참조. 로그는 `evidence/`.

## 아직 남은 검증·작업

**R5는 구현과 격리 검증까지다. 실제 Windows의 Job Object·uv stdin 전달·자손 Python/ffmpeg 정리·설치본 종료를 검증하지 않았으므로 실환경 검증 완료로 취급하지 않는다.** 확인 실패 시 소유 상태를 보수적으로 유지하며 자동으로 다시 시작하지 않는다.

다음 Windows 검증 전에는 새 Python SDK와 Electron/Nest를 함께 반영한 source snapshot 및 새 appVersion/venv 갱신을 확인해야 한다. 기존 packaged venv는 `--no-editable`로 복사되므로 이전 SDK가 남아 있으면 새 supervisor가 없다. 이번에는 의존성 설치·venv 갱신·Windows 빌드·설치·실행을 하지 않았다.

CPU CIM/Build7 source-artifact 대조, 작업별 RAM/VRAM 예산·GPU telemetry 신선도, 무응답 작업 강제 종료 정책, 넓은 UI 실기 검증 등은 기존 보류 상태다. 운영 배포 및 Build5 전체 QA를 진행하지 않는다.
