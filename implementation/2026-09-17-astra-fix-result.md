# Astra 재감사 R01–R13 및 A14 수정·재검증 결과

기준: 2026-09-17 KST. 승인된 수정 범위는 [독립 재감사](2026-09-17-astra-independent-review.md)의 R01–R13이며, 이후 사용자 “진행해줘”로 수정·회귀검증을 진행했다. 새 병합·커밋·push·배포 승인은 아니다.

## 현재 판정

후속 갱신: [잔여 두 항목 진단](2026-09-17-remaining-boundaries-diagnosis.md) 뒤 사용자 승인으로 환급 누락과 Dialog 테스트를 수정했다. 최신 [수정 결과](2026-09-17-archive-refund-fix-result.md): Nest 전체 2,678/2,678 PASS, 설치형 실기 필요. 아래 “미재현”·승인 대기는 A14 수정 직후 당시 기록이며 현재 상태가 아니다.

R01–R13 수정 뒤 별도로 재현한 Variation 최초 실행의 차감→작업 예약 사이 중단 문제(A14)도 사용자의 “응” 승인 후 수정했다. A14의 실제 변경과 최신 검증은 아래 별도 절을 따른다. **설치형 UI 실기는 아직 남아 있으며 개발 DB 복제본 리허설로 자동 진행하지 않는다.** 테스트 통과를 전체 로컬 검증 완료나 출시 가능 판정으로 확대하지 않는다.

제품 변경은 기존 `.worktrees/dev-pg-local-validation-20260917/`의 Angular/Electron/Nest/Web API 4repo에 미커밋 상태다. 8repo의 branch/HEAD는 재감사 기준과 동일하며 원본 checkout은 모두 clean이다. 새로운 merge/rebase/cherry-pick/commit/push/deploy는 없다. 실제 서버·개발 DB·운영 DB에 접근하지 않았다.

## 수정 내용

| 항목 | 실제 변경과 검증 경계 |
|---|---|
| R01 | 정책 조회에 기존 transaction manager 전달. pool 1/2/10 회귀 테스트, 별도 PostgreSQL pool 1/2 실험에서 기존 timeout→수정 후 완료, 같은 key 한 번 차감·잔액 부족/증거 저장 실패 rollback 확인 |
| R02 | 시작 전에 가격 계산용 수치와 동일 요청 key 저장. 응답 유실 시 같은 key로만 복구하고 실행하지 않은 시도를 환급. 미확정 이전 요청이 있으면 새 차감 차단. 확정 4xx 거절은 자동 재실행하지 않음. 사용자별 격리·진행 중 요청 오환급 방지·복구 중 재종료 검사 |
| R03 | Variation 재시도 attempt에 새 job ID를 차감 전 영속 저장. 준비 도중/이전 batch 대기 중 중단을 실제 JSON 재로딩으로 검증. 옛 params가 남아 있어도 새 차감만 환급하고 옛 종결은 유지 |
| R04 | 성공/환급 의도와 최소 evidence를 네트워크 요청 전에 outbox 저장. 보관함 삭제 전에 소유자별 tombstone 저장. 삭제 자체로 환급 판단하지 않음. 삭제와 통신이 겹치면 tombstone 보존 후 다음 replay로 확인 처리 |
| R05 | 중단 직전 job 상태를 디스크에 남김. 두 번 부팅해도 원래 running이었던 불명 결과를 확정 실패로 바꾸지 않음 |
| R06 | Electron spawn 이후 Nest PID/identity 확보, spawn 전 종료 요청·exit 이후 identity 유지 검증 |
| R07 | Nest가 기록한 소유 marker/child identity를 Electron도 같은 방식으로 검증. 실제 일회용 자식 프로세스 writer→reader 테스트, 불일치 시 타 프로세스 종료 금지 |
| R08 | 인증/온라인/실시간 연결 복구 시 본인 요청만 replay. 5→10→20→40→60초 backoff, idle 60초 재확인, 로그아웃/계정 전환/중복 요청 검사 |
| R09 | Dance/Dialog도 확인 후 큐 진입 전에 차감. 먼저 preparing 작업을 영속 저장하고 차감 연결·queued 저장 후 큐 진입. 최초/재시도/잔액 부족/큐 취소/실행 직전 취소/예약 중 강제 중단/알림 실패와 queue claim 경쟁 검증. 취소 신호는 환급 네트워크 응답보다 먼저 전달 |
| R10 | Shortform 빈 media slot, TTS ID·파일 누락, 잘못된 codec·truncated 음성, 잘못된 이미지 등을 거절. 음성 전체·미디어 첫 프레임의 ffmpeg 디코드 검사 |
| R11 | 보관함 Shortform 재시도도 금액 견적·확인·예약·이동 전 같은 preflight 실행. 실제 retry endpoint에서도 예약 전 재검사 |
| R12 | Comment Overlay/Ranking 재시도에 복사된 옛 output_root를 제거하고 새 프로젝트 경로 계산. 기존/신규 결과 디렉터리 격리 검증 |
| R13 | 작업 상태 변경과 실제 금융 확정 이벤트에서 계정 잔액·원장 갱신. 확정 이벤트를 놓치거나 다른 경로에서 outbox를 소비해도 예약된 재확인에서 조회. 느린 이전 계정 응답이 새 사용자 잔액을 덮지 않도록 generation 검사 |

R02의 “복구”는 새 영상 자동 실행이 아니다. 불명인 과금 요청의 동일 key를 재전송해 결과를 확인하고, 실행에 진입하지 않은 기존 요청을 종결한다. 확정 실패·환급 뒤 사용자가 승인한 새 시도는 별도 key를 사용한다. 로컬 metadata는 프로젝트 폴더 밖에 저장하며 토큰·미디어·대본은 저장하지 않는다. 기존 30일 종결 보존 정책은 유지한다.

R09 검증에서 거절된 과금은 작업 예약을 failed로 남기지만 큐에는 넣지 않고 차감/환급을 임의로 만들지 않는다. preparing 기록은 차감 후 앱 종료 시 아무 일도 실행하지 않았음을 복구가 판단하는 근거다.

## 로컬 계약 추가

- `POST /v1/operations/recover`: body `{}`, 실제 인증 헤더에서 소유자·토큰을 확인. 결과 `{confirmed: string[], pending: string[]}`. 로그인 없는 local session은 401. 다른 사용자의 요청을 replay하지 않음.
- `POST /v1/jobs/:jobId/retry/preflight`: owner/retry 가능 상태/access 검사 후 등록된 준비기의 preflight 실행, 성공 `{ready:true}`. Shortform UI에서 과금 확인 전에 호출하고 실제 retry에서도 반복.
- realtime `operations.confirmed`: 원격 금융 성공 응답과 로컬 `server_confirmed` 저장 뒤 해당 사용자에게만 전달. 필드 ownerSubjectId/attemptId/runId/intent. UI 알림 오류가 금융 결과를 바꾸지 않음. 이벤트 유실은 예약된 조회로 보완.

## R01–R13 실행 검증 (A14 직전 기록)

- Electron: `npm run build` PASS, 전체 `npm test` **955/955 PASS**.
- Web API: `npm run build` PASS, 전체 `npm test -- --runInBand` **259 suites / 2,802 tests PASS**, 기존 5 suites / 21 tests SKIP.
- Angular: 변경된 과금 복구·보관함·계정·인증·app 연결 관련 **226/226 PASS**, `devapp` build PASS. 전체 Angular suite나 설치형 UI E2E로 표현하지 않는다.
- Nest: 최종 build PASS. 전체 `node --test 'test/*.test.js'` **2,640/2,640 PASS**.
- 최종 Nest 실제 앱 부팅 smoke: 별도 임시 `CLIPPER_DATA_DIR`, 없는 env 파일, loopback-only API 설정. health 200, 미인증 recovery 401, 정상 종료 PASS. 실제 OAuth/ML/금융 서버 호출 없음.
- 8repo `git diff --check` PASS, 원본8repo clean 및 HEAD 불변 확인.

초기 Electron/Web API 전체 테스트의 sandbox 실행은 로컬 포트/프로세스 조회 EPERM으로 실패했다. 로컬 테스트 권한으로 재실행한 위 결과와 구분한다. 테스트를 통과시키려고 제품 코드의 보안 검사를 완화하지 않았다.

실제 PostgreSQL 검증은 기존 DB와 분리한 Unix-socket-only 일회용 cluster였다. 비교 대상 기존 코드는 pool 1/2 모두 연결 획득 timeout, 수정본은 완료했다. 같은 사용자+key 동시 replay는 단일 run/차감이며, 잔액 부족과 evidence insert 실패는 잔액·원장·run을 rollback했다. 테스트 cluster는 종료했고 사용자 DB는 건드리지 않았다. 전체 migration/HTTP stack 재리허설과는 다르다.

주요 로그: `/private/tmp/astra-fix-electron-full.log`, `/private/tmp/astra-fix-web-api-full.log`, `/private/tmp/astra-fix-nest-full.log`, `/private/tmp/astra-ui-final-tests.log`, `/private/tmp/astra-ui-build.log`. 최종 격리 부팅 로그: `/private/tmp/astra-fix-nest-smoke-8dgOw8/boot.log`. 임시 로그는 장기 정본이 아니며 주요 회귀는 각 repo의 test/spec 파일에 보존했다.

## A14 — 사용자 승인 후 수정·회귀검증

위치는 Nest `src/modules/variation-v2/application/variation-v2-render.service.ts`의 최초 `render()` 경로다. 재시도 `prepare()`와 다르다.

수정 전 순서: 선택 영상 전체의 operation 차감 → 프로젝트 잠금 저장 → 영상별 job 예약 → 준비·큐 제출. 두 영상 차감 후 잠금 저장에서 프로세스가 종료된 상태를 실제 coordinator/JSON 저장소로 재현했다. 차감 run 2개, job 0개가 남고, 재시작 시 두 건 모두 ambiguous가 되어 환급 outbox가 생기지 않았다.

적용한 순서: 프로젝트 잠금 → 선택 영상의 preparing job 전부 로컬 저장 → 각 job ID에 연결한 operation 차감 → 기존 준비·큐 제출. coordinator가 네트워크 요청 전에 저장하는 attempt의 `featureReference={kind:'desktop_job',reference:jobId}`가 중단 복구의 영속 연결이다. job params의 run/attempt ID는 기존 submit 시점에 반영되며, 그보다 앞선 중단도 attempt→job 연결로 복구한다. 중간 실패 시 알려진 차감만 환급하고 미차감 예약은 실패 정리한다. 응답 불명은 기존 동일 key 복구를 사용하며 앱 재시작 시 영상 자동 실행은 하지 않는다.

독립 리뷰에서 예약이 먼저 노출되면서 생기는 취소·삭제 경쟁도 발견했다. 앞 영상 차감 응답을 기다리는 동안 뒤 영상을 취소·삭제하면 없는 job을 뒤늦게 차감할 수 있었다. `JobsService.withPreparingJob()`이 기존 cancel과 동일한 job 수명주기 lock 안에서 소유자·preparing 상태를 확인하고 차감 시작/연결까지 보호한다. 먼저 취소·삭제된 job은 차감하지 않으며, 앞 job이 건너뛰어져도 뒤 job의 run 연결이 밀리지 않는다. 새로운 병합·API·DB schema·금융 정책은 추가하지 않았다.

신규 `test/variation-v2-initial-billing-restart.integration.test.js`는 0/1/2개 차감 시점 중단, 잠금·예약 실패, 두 번째 차감 거절/응답 유실, 이전 batch 대기, 취소·삭제 경쟁, 다른 소유자 거절을 검증한다. 기존 Variation 서비스/재시도·billing restart 회귀도 함께 실행해 107/107 PASS. 최초 7건과 취소 경쟁 2건은 수정 전 RED를 확인했다. 실제 JSON 재로딩과 fake 원격 원장을 사용하며 실제 OS kill·ML·실결제 검증은 아니다. 독립 재리뷰에서 A14 범위의 추가 결함은 보고되지 않았다.

제품 변경: `variation-v2-render.service.ts`, `jobs.service.ts`. 테스트 변경: 위 신규 integration 파일과 `variation-v2-render-service.test.js`, `variation-v2-retry-billing-restart.integration.test.js`. 기존 R01–R13 미커밋 변경을 보존했다. 최종 build 및 격리 Nest 부팅(health 200, 미인증 recovery 401, 정상 종료) PASS. 부팅 로그: `/private/tmp/astra-fix-nest-smoke-JLmW4K/boot.log`.

전체 재실행 중 기존 `dialog-highlight-python-stage-runner.test.js:465`의 5ms DELETE 도착 가정이 한 번 실패했다(2,651 PASS / 1 FAIL). 단독 10/10은 통과했으며 이 파일과 제품 코드는 변경하지 않았다. 이 간헐적 테스트 안정성은 별도 후속 항목으로 남긴다. A14 회귀 실패와 구분하며 전체 최종 재실행 결과는 아래에 기록한다.

최종 전체 재실행: **2,652/2,652 PASS**, 0 fail/cancel/skip, exit 0. `/private/tmp/astra-a14-nest-final-rerun.log`. A14 targeted 107/107 로그: `/private/tmp/astra-a14-targeted.log`. 간헐적 실패 기록은 `/private/tmp/astra-a14-nest-final.log`, Dialog 단독 통과는 `/private/tmp/astra-a14-dialog-rerun.log`에 남겼다. 최종 8repo `git diff --check` PASS, 원본8repo clean, 통합8repo HEAD 불변을 재확인했다.

별도 잔여 위험(코드 검토상 가능성, 미재현): 차감·run 연결 완료 → 준비 대기 중 취소 및 보관함 삭제 → 환급 outbox 저장 전 앱 종료. attempt의 `userDeleted`는 삭제 기록이지 환급 증거가 아니므로, 대응 job까지 없어지면 restart reconciliation이 ambiguous로 남길 수 있다. 이번에 재현·수정한 **삭제 이후 새 차감**과는 다른 기존 post-charge 경로다. 재현 테스트로 확인하고, 확인된 경우 삭제 전에 종결 의도를 영속화하는 수정 범위를 제시한다. 이를 해결 완료로 간주하거나 삭제 사실만으로 환급하도록 바꾸지 않는다.

## 남은 게이트

1. 위 post-charge 삭제/종료 위험을 별도 재현·검증하고 수정이 필요하면 범위를 확인받는다. Dialog 5ms 취소 테스트의 비결정적 도착 가정도 별도 수정 범위 확인 후 안정화. R01–R13+A14 통과만으로 모든 장애 경계가 닫혔다고 판정하지 않는다.
2. 실제 설치형 앱의 offline/online·로그아웃/계정전환·사용자 Google OAuth 재로그인 실기. Windows installer/종료 실기는 사용자 Windows 장비에서 실행.
3. 그 결과를 확인한 뒤에만 사용자 실행 dump로 개발 DB 복제본 inventory/reset/migration/복원 리허설. 실제 개발 사용자·로그인 보존, 운영 초기화 절차 그대로 적용 금지.
4. 개발서버 적용은 전환 계획·실제 DB 변경·배포 각각 승인 후 사용자 실행. 실제 ML/Build5 전체 QA는 계속 HOLD.

### R01–R13 당시 전체 Nest 확인 (A14 이전)

전체 **2,640/2,640 PASS**, 0 fail/cancel/skip, exit 0. 첫 전체 실행은 내구성 있는 preparing 예약 도입 후에도 잔액 부족 시 job이 없다고 가정한 기존 테스트 1건이 실패했다(2,639 pass). 해당 기대값을 failed 예약 존재·큐 없음·실행/환급 없음으로 명시해 수정한 뒤 전체를 재실행했다. 단순히 assertion을 제거하거나 제품 동작을 옛 상태로 되돌리지 않았다. 최종 제품 소스는 이 기대값 보정 전후 동일하다.
