# 취소·삭제 환급 누락 수정 및 Dialog 테스트 안정화

2026-09-17 KST. 사용자가 [진단 결과](2026-09-17-remaining-boundaries-diagnosis.md)의 두 수정안을 “응 진행해줘”로 승인한 뒤 구현했다. 승인 범위는 이 수정·회귀검증이며 새 병합·커밋·push·배포·실제 DB 변경은 아니다.

## 결과

준비 대기 중 차감된 작업을 취소·삭제한 뒤 앱이 종료돼도 환급 의도가 삭제 전에 로컬 outbox에 남는다. 디스크에 다시 읽은 job/attempt/outbox와 가짜 금융 원장으로 재시작·로그인 복구 후 정확한 환급을 확인했다. Dialog의 5ms HTTP 도착 가정은 제품 코드 변경 없이 테스트를 분리해 제거했다.

다음 단계는 수정본 설치형 앱의 로컬 실기다. 테스트 통과를 전체 제품 검증 완료로 확대하지 않으며, 개발 DB 복제본 리허설·실제 전환으로 자동 진행하지 않는다.

## 실제 변경

범위: 기존 `.worktrees/dev-pg-local-validation-20260917/desktop/clipper_nestjs`, `integration/dev-pg-local-validation-20260917`, HEAD `f452b6f892dfa77d22e971c746daa94285c04a3c` 그대로.

### 취소·삭제 경계

- `job.model.ts`: `cancelledFromStatus`를 로컬 job 최소 메타데이터로 추가.
- `json-job-repository.ts`: cancelled 전환과 같은 저장에 **실제 직전 상태**를 기록한다. 같은 cancelled 상태를 재저장해도 원래 근거를 지우지 않는다. 구버전 queue migration/임의 복원은 추가하지 않았다.
- `jobs.service.ts`: 취소 직전 preparing/queued이며 startedAt·중단 출처·commitPhase가 없는 경우만 실행 전 취소로 인정한다. 삭제 전에 공통 billing 경계로 이를 전달한다.
- `billable-job-attempt.coordinator.ts`: owner + 영속 `desktop_job` ID가 정확히 일치하는 running/known-run attempt에 대해 fail intent·최소 evidence를 outbox에 먼저 저장하고, 이후 삭제 표시를 저장한다. 저장 실패는 호출자에게 전달해 프로젝트/job 삭제를 막는다.
- 기존 pending/confirmed intent는 덮어쓰지 않는다. 성공 완료·실행 결과 불명·취소 출처 없음은 삭제만으로 환급하지 않는다. unresolved start는 기존 동일 key 복구를 유지한다.
- 삭제 요청은 원격 금융 통신을 실행하거나 성공 응답을 기다리지 않는다. 로컬 환급 요청을 내구성 있게 남기며 기존 인증/온라인 복구 경로가 전송하고 서버 확인 후 잔액을 갱신한다. “삭제 즉시 서버 환급 완료”라는 계약이 아니다.

독립 리뷰에서 재시도 params에 남은 옛 `desktop_project` attempt ID가 다른 작업의 환급 근거로 오인될 수 있음을 발견했다. 별도 RED 회귀로 확인한 뒤 **삭제 경계의 attemptId/프로젝트 fallback을 제거**했다. 현재 최초/재시도의 정확한 job 연결만 사용한다. 옛 ID를 새 이름으로 바꾸거나 BGM/template ID를 마이그레이션하는 변경은 없다.

### Dialog

`test/dialog-highlight-python-stage-runner.test.js`만 수정했다.

1. 실제 loopback HTTP 서버에서 DELETE의 인코딩된 경로와 정상 응답 처리를 확인한다.
2. 제어된 transport와 abort signal로, 응답 없는 DELETE가 abort 후 정상 반환하는지 확인한다. 실제 TCP 도착이 5ms보다 빨라야 한다는 가정은 없다.

제품의 기본 1초 제한과 취소 로직은 변경하지 않았다. 테스트 process의 안전 timeout은 유지한다.

## 검증

- 최초 RED: 대상 25건 중 6건 실패. 취소 출처 누락, 환급 outbox 미생성, 디스크 오류여도 삭제 진행, stale 다른 job attempt 선택을 실제 저장소로 확인했다.
- 리뷰 추가 RED: 상속된 옛 project-scoped attempt ID 회귀 1건 실패를 확인하고 보완했다.
- 최종 build PASS. `/private/tmp/astra-delete-refund-final-build.log`.
- 최종 대상 회귀 **70/70 PASS**. `/private/tmp/astra-delete-refund-final-targeted.log`.
- 최종 Nest 전체 **2,678/2,678 PASS**, 0 fail/cancel/skip, exit 0. `/private/tmp/astra-delete-refund-final-full.log`.
- Dialog 파일 **새 프로세스 20회 × 11건 모두 PASS**. `/private/tmp/astra-dialog-stability-20.log`.
- 원래 진단 시나리오를 수정 후 기대값으로 갱신해 **6/6 PASS**. 삭제한 경우에도 환급이 복구됨. `/private/tmp/astra-delete-refund-diagnostic-fixed.log`. 진단 스크립트는 `.codex/implementation/2026-09-17-remaining-boundaries.diagnostic.cjs`에 보존.
- 최종 실제 Nest 격리 부팅: health 200, 미인증 recovery 401, 정상 종료 PASS. `/private/tmp/astra-fix-nest-smoke-OtBu53/boot.log`. 실제 사용자 데이터 대신 일회용 CLIPPER_DATA_DIR·loopback-only 원격 URL 사용.
- 독립 재리뷰: 수정 범위의 남은 actionable finding 없음. 전체 제품/설치형 실기 승인이라는 의미는 아님.
- 원본8repo clean, 통합8repo HEAD 불변, 8repo `git diff --check` PASS.

새 영속 회귀 `test/billing-archive-cancellation.test.js`와 기존 Variation integration 테스트에 다음을 보존했다: preparing/queued 취소, Variation/Shortform/Dance/Dialog 이름을 사용하는 공통 삭제 경계, owner 격리, 디스크 쓰기 실패 전후, retry 조상 삭제, pending/confirmed 성공·환급 보존, 실행 불명 오환급 방지, stale job/project attempt 오선택 금지. 실제 플러그인 실행을 테스트한 것은 아니다. OS 강제 kill 대신 promise 경계와 새 JSON reader로 재시작을 모사했다.

## 보존·미실행·다음 행동

기존 Angular/Electron/Nest/Web API 4repo의 미커밋 수정은 보존했다. 이번 새 제품/테스트 수정은 Nest에만 있다. 다른 원본·worktree를 이동하거나 수정하지 않았다. 문서·진단도 갱신했으며 커밋·push·서버 접속·배포·실제 개발/운영 DB 변경은 없다.

남은 일:

1. 최신 수정본을 설치형 로컬 앱에 포함해 offline/online, 재시작, 로그아웃·계정전환, 취소·환급·잔액 표시 실기. 실제 ML/Build5 HOLD 유지.
2. Google 로그인은 사용자 직접 확인. Windows build/installer/종료 실기는 사용자 Windows 장비에서 실행.
3. 검증 결과 확인 후 승인받아 커밋 보존. push는 별도.
4. 그 뒤 사용자 실행 dump → 개발 DB 복제본의 inventory/전환/복원 리허설. 실제 DB 변경과 서버 적용은 별도 승인·사용자 실행.
