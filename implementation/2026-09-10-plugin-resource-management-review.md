# 플러그인 대시보드·리소스 관리 검토

> **후속 우선:** 이 문서의 리소스 ‘구현 전’ 상태는 [R1~R4·watchdog·UI 후속](./2026-09-10-plugin-resource-safety-followup.md)과 [R5 후속](./2026-09-10-windows-owned-process-tree-followup.md)에서 갱신되었다. 최신 완료·보류 구분과 Build7 증거·SDK/venv 조건은 [문서 정리](./2026-09-10-documentation-source-reconciliation.md) 및 [TASKS](./TASKS.md)를 따른다. 아래 본문은 당시 감사 이력으로 보존한다.

기준 2026-09-10. 사용자 요청: CPU 표시 개선, 대시보드 UI/UX 전반과 메모리 부족 감시·안전한 플러그인 종료 점검. 현재 진행/배포 정본은 [전체 상태 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md).

**판정: 현재 기능은 리소스 현황 조회와 작업 시작/종료 시점의 조건부 정리다. 지속적 메모리 부족 감시와 모든 진행 작업의 보호까지 보장하는 관리자로 볼 수 없다.** 아래 중요 경로 4개를 실제 소스 기반 모의 실행으로 재현했다. 실제 ML 플러그인 실행이나 사용자의 프로세스 종료는 하지 않았다. 자동 종료/동시 작업 정책 변경은 이번 CPU 표시 수정에 섞지 않았으며 후속 구현 대상이다.

## 조사한 소스

- Electron a34a39d510bca51bf8b3e527d433ff9112c686fc: `src/main/resources/host-resource-monitor.ts`, `src/main/backend/plugin-host-bridge.ts`, `src/main/plugin/{plugin-process,child-process-stop}.ts`.
- Angular c8b186770ae6f77294a2a1689226834f05a8944a: `src/shell/dashboard/dashboard.component.{ts,html,scss,spec.ts}`, `src/core/resources/resource-status.service.ts`, `src/core/plugins/plugin-status.service.ts`.
- Nest780128a069c38a9df6438cc64d79f7a2e42bc1ea: resources/정책·PluginService·PythonRuntimeLifecyclePolicy·Python/Dialog executor·TTS/직접 STT 클라이언트·local/host stop.
- Python260751d2fa5be8a5a9cd8e346c60ba22d1512ed9: SDK health/job 집계, tts_supertonic의 /tts, clipper_video_render 자식 ffmpeg 경로.
- 새 CPU 수정은 별도 `/private/tmp/clipper-resource-dashboard-review`에 있다. 이하 리소스 관리 결함은 그 이전 배포 소스의 감사 결과이며 새 CPU 수정으로 해결했다고 표시하지 않는다.

## 현재 기능이 실제로 하는 일

| 구간 | 현재 동작 | 보장하지 않는 부분 |
|---|---|---|
| 화면 조회 | 대시보드가 보일 때 약3초마다 플러그인/호스트/앱 작업 조회, 화면 파괴 시 interval 정리 | 화면 조회가 메모리 감시·자동 정리 실행이라는 뜻은 아님 |
| CPU | Windows는 논리 CPU 시간차 사용률, macOS는1분 평균 load | 서로 단위 다름. CPU 사용률 기준 자동 종료 없음 |
| 메모리 | 호스트 사용/가용 RAM, 추적 프로세스의 RSS | Electron renderer·모든 자손까지 포함한 앱 전체 합계 아님 |
| GPU | NVIDIA는 사용률/VRAM 수집, macOS/기타 Windows는 가능한 범위의 정보 | GPU 수집값은60초 cache, 현재 snapshot 시각과 실제 GPU 갱신 시각이 다를 수 있음 |
| 수동 시작 | 예상 RAM/VRAM > 가용량이면 차단, 가용량의70% 초과이면 경고 | 정리보다 먼저 판정하므로 정리 가능한 idle이 있어도 먼저 차단될 수 있음 |
| 작업 준비 | prepareForRun에서 exclusive peer 정리 후 필요시 RAM pressure 정리 | 정리 후 실제 가용량 재측정/최종 차단 보장 없음, 실제 job은 수동 시작 admission을 우회 |
| 기본 exclusive 그룹 | dance_highlight/dialog_highlight/clipper_video_render/tts_supertonic | 그룹명과 달리 모든 동시 실행을 상호 배제하는 lock이 아님 |
| 정리 대상 | manifest safeToEvictWhenIdle=true, running/baseUrl, health active_jobs 정확히0 | 모든 처리 중 요청이 health에 포함되는 것은 아님 |
| 정상 종료 후 | 참여하는 작업 종료 시 기본60초 뒤 idle 확인, busy/health불가면 재시도 | 수동 시작만 한 경우에는 idle timer가 생기지 않을 수 있음 |
| RAM pressure | 요청 프로세스 미실행 + 예상 RAM > 가용량70%면 RSS 큰 idle 후보부터 정리 | 종료 후 RSS를 더한 예상값 사용. 지속 압력 감시/VRAM 압력 정리 없음 |
| 종료 | /shutdown 요청800ms → graceful2초 → SIGTERM5초 → SIGKILL1초 | Windows 전체 자손 종료 보장은 없음 |

## 우선 수정해야 할 정확성 문제

### R1 — P1: 진행 중 TTS를 idle로 오인

- Nest `src/modules/tts/infrastructure/tts-plugin.client.ts:21`은 idle timer 취소 → prepare → /tts 호출 동안 별도 작업 소유권을 보유하지 않는다.
- Python `plugins/tts_supertonic/tts_supertonic/app.py:63`의 /tts는 SDK job registry 밖에서 처리한다. `clipper_plugin_sdk/clipper_plugin_sdk/base.py:311`의 health는 그 registry의 active jobs만 센다.
- 재현: /tts 응답을 보류한 상태에서 다른 heavy plugin의 prepare를 실행하고 health0을 반환하면 TTS host.stop 호출을 확인. **Nest 제어 경로를 재현한 것이며 실제 음성 생성 중단 실기 아님.**
- 필요한 수정: 준비 전부터 응답 종료까지 TTS의 실행 소유권을 등록하고 정리가 이를 존중해야 한다. Python health도 동기 API 작업을 포함해야 한다.

### R2 — P1: 이미 실행된 idle timer와 새 작업 경합

- lifecycle `python-runtime-lifecycle-policy.service.ts:141`은 타이머 발화 시 pendingStops에서 먼저 제거한 후 비동기 health 조회. `stopIfIdle:161`은 health 확인과 stop을 따로 실행한다.
- 재현: timer 발화 → health0 응답 지연 → 새 작업이 cancelScheduledStop 호출 → 이전 health 응답 완료 → 새 작업 시작 중 stop. clearTimeout은 이미 실행 중인 콜백을 취소하지 못한다.
- 필요한 수정: 플러그인별 실행 소유권/세대와 정리 사이의 공통 배타 구간. await 후 재검증은 필요하지만 단순 health 두 번 조회만으로 마지막 조회/stop 사이 경합을 닫지 못한다.

### R3 — P1: 하나의 작업 취소가 같은 런타임의 다른 작업까지 중지

- Python executor `stopCancelledRuntimeIfManaged:100`, Dialog executor `:499`는 safeToEvictWhenIdle를 확인하고 **idle 여부 검사 없이** host.stop을 호출한다.
- 앱의 일반 작업 큐가 한 개씩 실행돼도 직접 reference STT/TTS 경로는 큐 밖이다. 직접 STT 클라이언트 `shortform-director-reference-local-stt.client.ts:60`은 같은 runtime을 사용할 수 있다.
- 모의 재현: 한 job 취소 후 남은 작업 health를 묻지 않고 전체 runtime.stop이 호출됨.
- 필요한 수정: 취소한 작업의 소유권만 해제. 다른 소유자가 없을 때만 전체 종료 가능. 응답하지 않는 취소 작업의 강제 종료 정책은 별도로 명시.

### R4 — P1: 실제 job 실행은 메모리 부족 차단을 우회

- PluginsService.start:199의 수동 시작은 resource assessment를 적용한다. 반면 Python executor.run:72는 prepareForRun 다음 ensureStarted를 직접 실행한다.
- 재현: 예상4GiB/가용1GiB, 정리 후보 없음 → 수동 시작 차단 / queued job ensureStarted 호출 성공 경로 확인.
- 필요한 수정: 수동/자동/직접 호출이 같은 admission 경로를 사용하고, idle 정리 → 가용량 재수집 → 최종 판정 순서를 공유. 동시 시작의 예산 예약은 추가 보호 요건.

### R5 — P2: Windows 프로세스 트리 정리 증거 부족

- Electron 및 Nest의 `child-process-stop.ts:29`는 전달받은 immediate child에 signal을 보내고 그 exit만 기다린다. Python 렌더는 ffmpeg 자손을 만든다.
- owned tree / Windows Job Object / 자손 추적 정리가 없음. **정적 결함 후보이며 실제 Windows orphan을 만들거나 검증하지 않았다.** 기존 stop2테스트도 단일 가짜 프로세스만 모델링한다.
- 필요한 수정: 앱이 소유한 프로세스 트리 단위 종료와 종료 확인. 이름 기반 전체 taskkill은 개발판/다른 앱에 영향을 줄 수 있어 해법으로 사용하지 않음.

## UI/UX 점검 결과

| 우선순위 | 현재 표시/행동 | 권장 변경 |
|---|---|---|
| 이번 수정 | CPU 사용률과 논리 수를 슬래시로 연결, OS/arch를 별도 줄 | 주값은 사용률만. 보조는 실제 물리 코어·논리 스레드. 조회불가/측정중을0으로 위장하지 않음 |
| 높음 | `canEvict`가 runtime activeJobs 미확인을0처럼 허용하고 batch stop은 일반 강제 중지 경로 사용 | 알 수 없으면 정리 대상 제외. UI 선택만 신뢰하지 않는 서버의 조건부 idle-stop 필요. 일괄중지 중복 방지·일부 실패/보호된 작업 결과 표시 |
| 높음 | 개별 stop 확인은 앱 작업 목록만 확인 | 런타임 작업/직접 요청도 고려. 실행 작업 수/보호 사유를 화면에 표시하되 서버 소유권이 정본이어야 함 |
| 높음 | 3초 조회 중첩 가능, 상태가 오래됐어도 정리 후보 표시 가능 | polling 직렬화/최신 응답만 적용, 상태 갱신 실패/오래됨·새로고침 표시. 조회와 자동보호 동작 구분 |
| 중간 | Memory 사용/총량만 주로 표시 | `사용 12GB / 전체32GB`와 `사용 가능20GB` 표시. admission이 실제 사용하는 가용량을 보이게 함 |
| 중간 | Processes/tracked host processes와 PID 중심 | `추적 중인 프로세스`로 한글화, 앱 전체가 아님을 명확히. 기본은 플러그인 이름/작업/메모리, PID·포트는 상세 정보 |
| 중간 | GPU 카드가 GPU 수와 첫 GPU만 표시 | 장치별 사용률/VRAM·통합 GPU 공유메모리 구분. 수집 불가와 GPU 없음 구분,60초 cache의 수집 시각 표시 |
| 중간 | idle 문구는 있으나 종료 이유는 lastExitCode 중심 | 수동/유휴/메모리 부족/오류 종료 이유와 시각, 다음 정리 확인 시각을 구분 |
| 중간 | runtime 목록이 비면 빈 영역, 플러그인 조회 오류는 toast 중심 | 미설치/실행없음/조회실패를 구분한 안내와 스토어 이동. CPU/메모리 조회 성공과 플러그인 조회 성공을 별도 표시 |
| 낮음 | telemetry/heavy plugin/RAM 등 용어 혼재 | `측정 정보`, `리소스를 많이 쓰는 플러그인`, 가용 RAM 등 일관된 문구. 기존 토큰/공통 state panel 재사용 |

상기 권장 변경 전체를 이번에 구현했다는 뜻이 아니다. 사용자 명시 CPU 카드 변경 외에는 발견 사항과 후속 설계를 기록했다. 화면만 먼저 `안전하게 정리`라고 바꾸면 실제 보호 결함을 가리므로 R1~R4를 먼저 해결해야 한다.

## 검증 및 후속 구현 순서

- 기존 순수 lifecycle8 + child-stop2 테스트 통과. 4개 새 모의 재현도 예상 결함을 확인. 도구 출력 `REPRO PASS`는 **결함 재현 성공**이며 기능 정상 통과가 아님.
- 재현 스크립트 `/private/tmp/clipper-resource-lifecycle-audit-repro.cjs`, 로그 `/private/tmp/clipper-resource-lifecycle-audit-repro.log`. TS 소스를 메모리에서 transpile하고 fetch/host/timer를 가짜로 제공. 실제 OS 프로세스 시작·종료·운영 API·모델 실행·파일 빌드 없음.
- 첫 구현 묶음: R1~R3 실행 소유권·조건부 정리·취소 격리 및 대시보드 batch 경로. 검증은 진행TTS, health 응답 지연, 직접STT와 큐 작업, 동시시작/취소에서 다른 작업 미중단.
- 둘째: R4 공통 admission·가용량 재측정, 경고/차단 UI 일치. 부족한 경우 ensureStarted/과금·작업 제출이 호출되지 않음을 검증.
- 셋째: 사용자 기대인 **지속 pressure watchdog** 추가. 화면을 닫아도 동작하는 백엔드 담당, 임계값/관찰횟수/회복구간/쿨다운/정리 우선순위와 실패 정책을 정한 후 구현. 실행 소유권을 먼저 갖춘 다음 시작해야 함. CPU 높다는 이유만으로 활성 작업을 종료하지 않음.
- 넷째: Windows owned process tree 정리, mock 검증 후 별도 Windows 실기. 기존 Build5/실제 플러그인 HOLD는 사용자 재개 전 유지.
- 이번 검토가 공개/실결제/전체 플러그인 QA 승인 또는 자동 종료 정책 변경 승인을 뜻하지 않는다.

## CPU 표시 변경 완료·적용 대기

CPU 수집·표시 변경은 Electron2/Angular4/Nest모델1파일에 구현했고 테스트8+42 및 세 빌드·로컬 dark/light/unknown·실제 Mac 조회까지 완료. **미커밋·미푸시·새 앱 배포 전**이다. Windows 설치0.0.3.7에서 사용자에게 보이던 기존 CPU 표시와 새 코드 적용 단계를 구분한다. 자동 종료와 watch 문제는 위 검토 단계에 머물러 있다. 자세한 파일 위치와 로그는 [현재 감사5절](./2026-09-10-current-state-and-resource-dashboard-audit.md)을 따른다.
