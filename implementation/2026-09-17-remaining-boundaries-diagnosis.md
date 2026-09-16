# A14 이후 잔여 두 항목 재현·원인 확인

후속: 두 수정안은 사용자 승인 후 구현·검증됐다. 현재 상태는 [수정 결과](2026-09-17-archive-refund-fix-result.md)가 정본이며 아래는 **수정 전 진단 기록**이다. 동봉 진단 스크립트는 원래 재현 경계를 유지하되 수정 후 정상 환급을 기대하도록 갱신했다.

2026-09-17 KST. 사용자 “1번 진행해줘”는 재현·원인 확인 승인이다. 추가 제품/기존 테스트 수정, 병합, 커밋, push, 배포, 실제 DB 작업은 하지 않았다. 기존 R01–R13+A14 미커밋 변경을 보존했다.

대상: `.worktrees/dev-pg-local-validation-20260917/desktop/clipper_nestjs`, branch `integration/dev-pg-local-validation-20260917`, HEAD `f452b6f892dfa77d22e971c746daa94285c04a3c`.

## 1. 차감 후 취소·삭제·앱 종료: 결함 재현

실제 Variation render/JobsService, JSON job/attempt/outbox 저장소, coordinator/finalizer/reconciliation을 사용했다. 원격 operation은 가짜 원장으로 대체했고, 앞 batch를 기다리는 준비 대기 상태를 promise로 유지했다. 새 저장소 인스턴스로 디스크를 읽어 재시작을 모사했다. 실제 OS 강제 종료나 ML·실결제는 아니다.

유저 흐름: Variation 생성·과금 동의 → 앞 작업의 준비가 끝나기를 대기 → 보관함에서 취소 → 취소 카드 삭제 → 해당 batch가 취소를 처리하기 전 앱 종료 → 다시 로그인.

| 비교 조건 | 재시작·로그인 복구 후 해당 차감 | 결과 |
|---|---|---|
| 취소 후 job 기록 유지 | server_confirmed / 환급됨 | 정상 대조군 |
| 취소 후 환급 outbox 생성 전에 job 삭제 | ambiguous / 환급 안 됨 | 결함 재현 |
| 취소 후 outbox 저장, 통신 실패 상태에서 job 삭제 | server_confirmed / 환급됨 | 정상 대조군 |

각 실험에서 2개 영상 차감 후 첫 작업만 비교 조작했다. 결함 조건에서 다른 남은 job은 환급되고 삭제한 job만 환급되지 않았다(총 환급 1/2). 정상 조건은 2/2 환급이다. 재로그인 복구를 두 번 호출해도 ambiguous는 자동 종결되지 않았다. 새 차감이나 실제 렌더 실행은 없었다.

원인 연결:

1. `jobs.service.ts:445` cancel은 preparing job을 cancelled로 저장하지만 환급 outbox를 생성하지 않는다. queued 전용 종결 경로와 달리 준비 중 Variation은 자체 배치가 처리하기를 기다린다.
2. `variation-v2-render.service.ts:551` 부근에서 이전 batch를 기다린 뒤 준비 루프가 취소·삭제를 감지하고 fail을 호출한다. 그 전까지 틈이 존재한다.
3. `jobs.service.ts:523` 삭제는 `markJobDeleted()`로 userDeleted만 남기고 job을 지운다. coordinator의 markJobDeleted는 취소 상태/취소 전 실행 단계/terminal intent를 저장하지 않는다.
4. `billing-restart-reconciliation.service.ts:53`은 job이 없고 outbox도 없는 running attempt를 ambiguous로 처리한다. 삭제 자체를 실패·환급의 증거로 취급하지 않는 원칙은 옳지만, 삭제 전에 필요한 종결 근거를 보존하지 못한다.

**권장 수정 범위(승인 대기):** 공통 과금 종결/삭제 경계에서 실행되지 않았음이 확인된 취소에 대한 최소 근거와 fail outbox를 job 삭제 전에 내구성 있게 저장한다. 디스크 저장에 실패하면 삭제를 완료하지 않는다. job ID·owner·정확한 attempt 연결을 사용하고 플러그인별 중복 로직을 추가하지 않는다. 취소 전 실행 단계도 필요하면 보존한다. 실행 중 결과 불명·성공 완료·이미 환급된 작업을 단순 삭제 이유로 환급하지 않는다. 기존 30일 정책·토큰 미저장·프로젝트 로컬 저장 원칙은 유지한다.

수정 시 필수 회귀: preparing/queued 취소→삭제→재시작, 디스크 쓰기 실패, outbox 저장 전후 중단, 기존 성공/환급 중복 요청, 실행 결과 불명, owner 격리, retry 조상 삭제. 이번에 다른 모든 플러그인의 동일 경계를 검증했다고 확대하지 않는다.

## 2. Dialog 취소 테스트: 5ms 도착 가정의 간헐 실패 확인

기존 `test/dialog-highlight-python-stage-runner.test.js:465`는 timeout을 5ms로 넘기고, 호출 반환 후 서버가 DELETE를 반드시 받았다고 검사한다. 실제 기본값은 `dialog-highlight-python-stage.runner.ts`의 1,000ms다. 공통 LocalPluginJobRunner.cancel은 AbortSignal.timeout을 fetch에 전달하며 제한시간 초과를 잡고 반환한다. 요청 도착/원격 취소 확정까지 보장하는 API는 아니다.

실제 loopback HTTP 서버에서 응답을 하지 않는 조건으로 확인:

- 5ms 제한 20회: 모두 정상 반환. 19회는 DELETE 도착, 최초 1회는 도착하지 않음(8ms 뒤 반환). 기존 assertion이 실패하는 바로 그 조건이다.
- 기본 1초 제한 3회: 3회 모두 DELETE 도착, 약 1,002ms 뒤 정상 반환.
- 5ms 제한 + 의도적 event-loop 지연 30ms: DELETE 미도착, 33ms 뒤 정상 반환.
- 제어된 fetch 경계: DELETE 호출과 timeout abort, Promise 정상 반환을 확인. 서버 도착 여부 없이도 timeout 처리 계약을 검증할 수 있다.

**판정:** 이번 간헐 실패는 제품 취소가 멈춘 증거가 아니라, timeout보다 먼저 요청이 반드시 도착한다는 테스트의 잘못된 가정 때문이다. 어떤 환경에서도 원격 작업이 반드시 중지된다고 검증한 것은 아니다. 원격 DELETE는 best-effort이며 기존 실제 프로세스 종료/설치형 실기 검증과 구분한다.

**권장 수정 범위(승인 대기):** 제품 코드·기본 제한은 유지. 기존 테스트만 (a) HTTP DELETE 경로/요청 전달, (b) 응답 없는 transport의 timeout/반환으로 나눈다. (b)는 제어 가능한 transport/타이머를 사용해 5ms 안에 실제 네트워크가 연결돼야 한다는 가정을 제거한다. timeout 값을 크게 늘리는 것만으로 결함을 숨기지 않는다.

## 실행 증거와 변경 범위

- `npm run build`: PASS. `/private/tmp/astra-remaining-diagnostic-build.log`.
- `node --test .codex/implementation/2026-09-17-remaining-boundaries.diagnostic.cjs`: 진단 6/6, exit 0. **관찰된 결함을 확인하는 assertion이므로 제품 결함 해결/회귀 전체 통과를 의미하지 않는다.**
- 재현 스크립트는 이 문서와 같은 디렉터리에 보존했다. 기존 integration test의 fixture 부분을 재사용하므로 해당 파일 구조가 바뀌면 경계 확인 실패로 멈춘다.
- 로그: `/private/tmp/astra-remaining-boundaries.log`. 임시 로그 대신 위 주요 결과와 진단 코드를 장기 인계로 보존한다.
- 제품 소스·기존 test는 이번 턴에 수정하지 않았다. 새 파일은 `.codex` 진단 코드와 결과 문서이며 인계 문서만 갱신했다. 전체 2,652건 재실행은 이번에 하지 않았고 이전 기록과 구분한다.
- 서버/실제 DB/ML/Build5/Windows 설치 실기 없음. 개발 DB 복제본 리허설은 계속 보류.

다음 행동: 위 두 수정 범위를 사용자에게 확인받고 회귀 테스트와 함께 수정. 그 뒤 설치형 로컬 실기를 진행하며, 실제 개발 DB·서버 적용으로 자동 진행하지 않는다.
