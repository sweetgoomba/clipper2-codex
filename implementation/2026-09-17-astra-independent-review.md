# Astra 독립 재감사 — 정식 PG 통합판

이 문서는 **수정 전 재감사 증거**다. 이후 사용자 승인으로 R01–R13 및 추가 A14 수정·회귀검증을 진행했다. 현재 상태와 남은 검증은 [최신 수정 결과](2026-09-17-astra-fix-result.md)를 우선한다.

기준: 2026-09-17 KST. 범위: 현재 통합 HEAD와 최신 사용자 결정의 읽기 전용 대조. 소스 수정·추가 병합·커밋·push·배포·서버 접속 없음.

## 판정

**병합과 후속 구현 커밋은 존재하지만, 안전성 보완이 모두 끝났다는 기존 판정은 철회한다.** 우선 수정할 P1 7건과 P2 6건을 확인했다. 기존 테스트 통과만으로 장애 경계가 검증된 것은 아니었다. 개발 DB 복제본 리허설을 바로 다음 실행 단계로 삼지 말고, 아래 수정 범위 확인 → 회귀 테스트를 포함한 수정 → 독립 재검증을 먼저 한다.

이번 검토는 모든 기능이 무결함이라는 보증이 아니다. 실제 ML·Build 5 전체 QA는 HOLD다. 실제 Google 로그인은 사용자가 로컬에서, Windows installer/실기 종료는 사용자가 Windows 장비에서 확인한다. 실제 개발 DB 복제본, 실제 PG 결제, 개발서버 전환은 수행하지 않았다.

## 확인한 Git 범위

정본 작업공간: `/Users/jina/project/adlight/.worktrees/dev-pg-local-validation-20260917/`, 공통 branch `integration/dev-pg-local-validation-20260917`.

| 저장소 | 감사 HEAD |
|---|---|
| desktop/clipper_angular | ac8793299b75834868e89afe6889764cb0939844 |
| desktop/clipper_electron | 827fcda8b12a34232c2574983afff6284b69d949 |
| desktop/clipper_nestjs | f452b6f892dfa77d22e971c746daa94285c04a3c |
| desktop/clipper_python | 60417ce865499df519971650a43a7ca1a82d9867 |
| web/clipper_infra | f975f34924bcf6c483dc16ba7acb08917b127fd4 |
| web/clipper_web_admin | 3d47536b9f8c3e8bf0dfd71dd78805a98f775475 |
| web/clipper_web_api | 73921471d9126c85bb669fbfd477f8673531c719 |
| web/clipper_web_client | a4bc54b5852e82d0699f63e6198d409746dd0ee0 |

8repo 원격 `dev`/`integration/main-unification-20260911`은 `git ls-remote`로 재확인했고 로컬 origin 참조와 일치했다. 각 통합 HEAD에서 두 참조의 미포함 커밋은 0이다. 원본 checkout은 전진시키지 않았다. Electron 앱 이름 커밋도 통합 이력에 포함돼 있다. 따라서 이번 발견은 주로 **병합 누락보다 후속 코드의 연결·장애 처리 결함**이다.

기존 결과/앱 이름 문서의 Electron 전체 SHA `827fcdadc32a4a59917cc126e99ca4ec84789b65`는 실제 Git 값과 달랐다. 위 실제 SHA로 정정했다. short SHA가 같다는 이유로 전체 값도 맞다고 취급하면 안 된다.

아래 경로는 위 작업공간 기준이다. 줄 번호는 감사 HEAD 기준이다.

## P1 — 먼저 수정할 결함

### R01. operation 시작 transaction이 연결 풀을 고갈시킬 수 있음

- 위치: `web/clipper_web_api/src/modules/operations/application/operations.service.ts:149,165`, `infrastructure/typeorm-operations.repository.ts:46`.
- transaction에서 연결 하나를 점유한 뒤 `requirePolicy()`가 transaction manager가 아닌 DataSource repository로 정책을 읽어 추가 연결을 요구한다.
- 풀을 채울 만큼 동시에 새 작업을 시작하면 각 요청이 연결 하나를 쥔 채 두 번째 연결을 기다려 진행하지 못할 수 있다. 사용자에게 작업 시작 요청이 멈춘 것처럼 보인다.
- 현재 실제 service/repository를 불러오는 유한 fake-pool 재현: transaction 10개가 연결 10개를 점유, policy query 10개 대기, 완료 0개. 실제 PostgreSQL 부하 테스트는 아니다.
- 수정: 정책 조회도 같은 transaction manager를 사용하거나 일관성을 검토해 transaction 밖으로 이동한다. 실제 작은 pool 동시성 회귀 테스트를 추가한다.

### R02. 과금 시작 응답 유실 후 저장한 key로 결과를 복구하지 않음

- 위치: `desktop/clipper_nestjs/src/modules/operations/application/billable-job-attempt.coordinator.ts:45,63`, `billing-restart-reconciliation.service.ts:44`.
- 서버는 같은 key에 대한 중복 차감을 막지만 coordinator는 호출마다 새 attempt/key를 생성한다. 첫 요청이 서버에서 차감된 뒤 응답만 유실되면 로컬에는 run ID 없는 attempt가 남는다. 이를 저장한 key로 재전송/조회하는 흐름이 없다.
- 사용자가 오류 뒤 다시 시작하면 첫 차감이 미종결인 채 두 번째 차감이 생길 수 있다. 실제 coordinator + 멱등 fake server로 두 개의 차감 run과 첫 연결 유실을 재현했다.
- 수정: **결과 불명인 동일 요청의 복구**는 저장된 key를 재사용한다. **확실히 실패·환급된 뒤 사용자가 승인한 새 시도**는 기존 결정대로 새 key를 사용한다. 이 두 동작을 혼동하지 않는다.

### R03. Variation 재시도의 새 과금 연결을 준비 완료 전까지 디스크에 남기지 않음

- 위치: `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:320`, `variation-v2/application/variation-v2-render.service.ts:259`.
- retry reserve는 옛 params를 복사한다. 새 operation/attempt 연결은 준비 중 메모리의 `reserved.baseParams`에만 있고 submit 시 저장된다.
- 새로 차감한 뒤 준비 도중 앱이 종료되면 디스크 job은 옛 attempt를 가리킨다. 재시작 시 명백한 준비 중단임에도 새 차감분과 job을 연결하지 못해 자동 환급 대신 모호한 항목으로 남는다.
- 실제 Variation 준비 경로와 로컬 저장소 재현에서 옛 ID 유지, 새 attempt ambiguous, 환급 outbox 0건을 확인했다.
- 수정: 비동기 준비 전에 새 job-attempt 연결을 영속 저장한다. 연결 쓰기 직전/직후 강제 종료와 batch 대기 경계를 테스트한다.

### R04. terminal 의도를 저장하기 전에 evidence 네트워크 요청을 기다림

- 위치: `desktop/clipper_nestjs/src/modules/operations/application/billing-terminal-finalizer.ts:59–73`.
- 현재 순서는 원격 evidence 호출 → 로컬 terminal outbox 저장이다. evidence 응답이 지연되는 동안 프로세스가 종료되면 이미 결정한 성공/환급 의도가 outbox에 없다.
- 로컬 job이 남으면 이후 대조로 회복할 여지가 있으나, 그 사이 terminal 카드/프로젝트가 삭제되거나 연결이 부족하면 판단 근거를 잃을 수 있다. 따라서 모든 경우 즉시 환급 유실이라는 뜻은 아니지만 durable outbox의 핵심 보장이 깨진다.
- evidence 요청을 대기시키는 재현에서 durable terminal 저장 0건을 확인했다. `markUserDeleted`도 실제 삭제 호출부에 연결돼 있지 않다.
- 수정: 네트워크 전에 결정과 필요한 최소 evidence를 내구성 있게 기록한다. 삭제 경로와 재전송을 함께 검증한다. 사용자의 데이터 삭제를 실패·환급 근거로 오해해서는 안 된다.

### R05. 재시작을 두 번 거치면 모호한 running 중단을 확정 실패로 바꿈

- 위치: `desktop/clipper_nestjs/src/modules/jobs/infrastructure/json-job-repository.ts:82`, `operations/application/billing-restart-reconciliation.service.ts:61–70`.
- 부팅 시 running을 failed로 저장하지만 원래 running이었다는 정보는 반환값/메모리에만 남는다. 그 뒤 다시 종료되면 다음 부팅은 이전 상태를 모른 채 failed를 확정 실패로 판단한다.
- 실제 JSON 저장소와 두 번의 시작 재현에서 처음에는 모호한 실행 결과로 남아야 할 항목이 다음 시작에서 fail/refund outbox로 들어갔다. 별도 프로세스가 결과를 완성했을 가능성을 확인하지 않은 환급이다.
- 수정: 중단 전 상태/판단 근거를 종결 확인까지 영속 보존한다. 결과 불명은 반복 재시작만으로 확정 실패가 되면 안 된다. preparing/queued 자동 재개 금지라는 사용자 결정은 유지한다.

### R06. Electron이 spawn 전에 Nest PID를 읽어 종료 식별값이 null로 고정될 수 있음

- 위치: `desktop/clipper_electron/src/main/backend/nest-process.ts:205`.
- `utilityProcess.fork()` 직후 PID를 읽는다. 설치된 Electron 계약상 PID는 spawn 전 undefined일 수 있다. 이때 null로 저장한 identity를 spawn 이후 갱신하지 않는다.
- cleanup/force-kill은 유효한 identity를 요구하므로 비정상 종료 fallback이 실행되지 않을 수 있다. 기존 fake process는 생성 때부터 PID를 넣어 이 타이밍을 숨긴다.
- 실제 NestProcess 코드에 비동기 spawn fake를 연결해 identity 조회가 호출되지 않고 cleanup에 null이 전달됨을 재현했다. 실제 Electron crash 실기는 별도다.
- 수정: spawn 시 PID와 birth identity를 확보하고 exit 후에도 안전하게 보관한다. spawn 전 취소·spawn 실패·정상 종료·crash를 테스트한다.

### R07. Nest가 기록한 자식 identity와 Electron의 검증 알고리즘 불일치

- 위치: `desktop/clipper_nestjs/src/core/process/owned-child-process-registry.ts:204`, `desktop/clipper_electron/src/main/backend/owned-child-cleanup.ts:46,72`.
- POSIX에서 Nest는 owner marker/환경이 포함된 `ps eww` 결과를 hash한다. Electron은 환경이 없는 일반 `ps` 결과를 hash해 비교한다.
- 실제 Nest registry가 기록한 현재 살아 있는 테스트 자식을 Electron cleanup에 전달했지만 다른 identity로 판단해 종료 대상에서 제외했다. 실제 앱/ML 프로세스는 사용하지 않았다.
- 수정: 두 저장소가 정확히 같은 ownership/identity 계약을 공유하도록 맞춘다. PID만 비교하거나 identity 검사를 제거해서 해결하면 안 된다. Nest writer → Electron reader를 연결하는 회귀 테스트가 필요하다. Windows는 별도 실기 검증한다.

## P2 — 기능·정책·복구 연결 보완

### R08. 네트워크 복구만으로 pending 환급이 재전송되지 않음

- 위치: `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:566`, `operations/application/billable-job-attempt.coordinator.ts:44`, realtime 연결 경로.
- replay는 GET jobs와 새 유료 작업 시작에 연결돼 있다. realtime 재연결/보관함 유지 자체는 이 경로를 호출하지 않는다.
- 인터넷이 돌아와도 보관함에 머무르면 환급이 pending으로 남을 수 있다. 앱 시작 대조가 있다는 것과 네트워크 복구 자동 전송이 있다는 것은 다르다.
- 수정: 인증 복구/온라인 복구와 owner-scoped backoff retry를 연결한다. 로그아웃·다른 사용자 전환·중복 replay도 검증한다. 정적 호출 경로로 확인했으며 실제 브라우저 offline 실기는 아직 하지 않았다.

### R09. Dance/Dialog 차감 시점은 여전히 큐 실행 이후

- 위치: `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:694`, `dialog-highlight/application/dialog-highlight-workflow.executor.ts:143`.
- Shortform/Variation과 달리 Dance는 starting, Dialog는 executor 안에서 차감한다. 공통 coordinator 사용만으로 호출 시점이 공통화된 것은 아니다.
- 결정 감사 §3은 최초/재시도 모두 preflight와 금액 확인 직후 차감하는 것으로 기록돼 있다. 현재 코드에서는 대기 중 잔액이 확보되지 않고 실행 시 잔액 부족 실패가 날 수 있다.
- 이는 기존 실행 구조가 남은 요구사항 대조 항목이다. 수정 설계에서 최초/재시도 양쪽의 정확한 경계를 맞추고, 기다리는 동안 다른 작업이 잔액을 사용하는 시나리오를 테스트한다. 문서만 고쳐 완료로 만들지 않는다.

### R10. Shortform preflight가 일부 손상/빈 선택을 통과시킴

- 위치: `desktop/clipper_nestjs/src/modules/shortform/application/shortform-render-preflight.service.ts:51,65,74`.
- TTS는 header 기반 duration, 로컬 미디어는 파일 존재와 크기만 검사한다. 선택 슬롯의 빈 asset ID는 `uniqueStrings`가 제거해 검사 자체가 생략된다.
- 현재 dist 직접 probe에서 잘못된 codec 값의 WAV header + 이미지 확장자의 텍스트 파일, 빈 asset ID 슬롯이 각각 `{ ready: true }`를 반환했다. 실제 ffmpeg decode 결과까지 확인한 것은 아니다.
- 수정: 유효한 슬롯과 참조를 명시적으로 검사하고 최소한의 실제 디코딩/재생 가능성 검증을 추가한다. 모든 렌더 오류를 사전에 막는다는 보장은 하지 않되, 사용자가 지정한 ID 없음/파일 없음/손상/편집 후 TTS 미생성 경계는 fixture로 각각 검증한다.

### R11. Shortform 재시도는 사전검증보다 과금 확인·새 job 예약이 먼저

- 위치: `desktop/clipper_angular/src/shell/projects/projects/projects.component.ts:1051`, Nest `jobs/application/jobs.service.ts:320`.
- 최초 편집 화면은 preflight를 호출하지만 보관함 재시도는 quote/confirm → retry → 새 job/화면 이동 → background prepare 검사 순서다.
- 실패 job의 TTS 파일이 없으면 미리 알려줄 수 있는데도 다시 확인창을 띄우고 새 실패 카드를 만든다. 이 특정 검사 실패는 새 차감 전이라 추가 과금된다고 주장하는 것은 아니다.
- 수정: 재시도도 quote/charge/reserve/navigation 전에 같은 preflight를 거치게 한다. 최초 화면과 재시도 화면의 순서 테스트가 필요하다.

### R12. 무료 렌더 두 기능의 재시도가 옛 output_root를 재사용

- 위치: Nest `src/modules/comment-overlay-render/application/comment-overlay-render.service.ts:47`, `src/modules/ranking-render/application/ranking-render.service.ts:44`, `src/modules/projects/application/projects.service.ts:420`.
- 새 project/job ID를 만들면서 옛 params의 output_root는 복사한다. ProjectsService도 이미 제공된 output_root를 유지한다.
- 두 실제 preparer 직접 probe에서 새 project ID와 `/safe-fixture/projects/old-project`가 함께 반환됐다. 결과 덮어쓰기나 한 프로젝트 삭제로 다른 카드의 결과가 사라지는 위험이 있다. 실제 사용자 파일 삭제/덮어쓰기는 수행하지 않았다.
- 수정: 새 project에 맞게 출력 디렉터리를 다시 계산한다. 기존 테스트와 달리 원 job에 output_root가 실제로 들어 있는 fixture를 사용한다.

### R13. 차감·환급 후 계정 요약 cache를 갱신하지 않음

- 위치: Angular `src/shell/account/account-summary.store.ts:70`, `src/shell/projects/projects/projects.component.ts:592,1669`.
- ensureLoaded는 이미 로드됐으면 다시 읽지 않는다. job event는 프로젝트를 갱신하지만 account summary를 갱신하지 않는다. 명시적인 refresh 호출은 설정 진입에 있다.
- 사용자가 보관함에 계속 머물면 차감/환급 이후 잔액 표시가 오래된 값일 수 있다. 정적 호출 대조 결과이며 이번 감사에서 UI 전체를 다시 실행하지 않았다.
- 수정: 금융 종결/서버 확인 이벤트에서 summary와 원장을 갱신한다. 단순 job 실패 이벤트만으로는 outbox 지연 환급의 실제 완료 시점을 알 수 없으므로 뒤늦은 환급도 테스트한다.

## 이번에 실제 다시 실행한 검증

| 검증 | 결과 | 한계 |
|---|---|---|
| Electron build | PASS | 패키지 실기 전체 검증 아님 |
| Nest build | PASS | 실제 ML 실행 없음 |
| Electron identity/runtime/auth/종료 관련 5파일 | 66/66 PASS | 비동기 spawn·서로 다른 identity writer/reader를 기존 fixture가 놓침 |
| Nest 과금/복구/preflight/retry 관련 15파일 | 194/194 PASS | 아래 별도 장애 재현은 기존 suite에 없음 |
| Web API operation/attempt/trial/user 관련 8 suite | 62/62 PASS | 실제 DB pool 동시성 검증은 없음 |
| 실제 코드 + fake/local 저장소 장애 재현 | R01–R07 문제 확인 | fake 네트워크/유한 pool, 테스트용 프로세스 사용 |
| reviewer preflight/output_root 직접 probe | R10/R12 문제 확인 | 실제 렌더·사용자 파일 변경 없음 |

재실행 가능한 이번 세션 임시 진단 파일:

- `/private/tmp/adlight-billing-review.cjs`: R05, R03, R04, R02 순서로 4개 재현. `node /private/tmp/adlight-billing-review.cjs`.
- `/private/tmp/adlight-operation-pool-review.cjs`: R01. `node /private/tmp/adlight-operation-pool-review.cjs`.
- `/private/tmp/clipper-astra-audit-20260917.YKEgor/process-boundaries.cjs`: R06/R07. 첫 sandbox 실행의 OS 프로세스 조회 제한을 구분하고 허용된 재실행에서 재현. 자체 테스트 자식만 생성/종료했다.
- R10/R12는 reviewer의 stdin probe로 실행돼 별도 스크립트는 남아 있지 않다. 영구 회귀 테스트는 수정 단계에서 저장소에 추가해야 한다.

임시 파일은 장기 증거 정본이 아니다. 각 항목의 위 조건을 저장소 회귀 테스트로 옮기고 수정 전 실패/수정 후 통과를 남긴다. 과거 전체 suite 수치나 과거 DB/browser smoke를 이번 새 실행으로 계산하지 않았다.

## 유지가 확인된 부분

- 운영 `ai.clipperstudio.app` / `clipperstudio://` / `Application Support/Clipper`, 개발 `ai.clipperstudio.desktop` / `clipper://` / `Application Support/Clipper Studio`로 현재 identity는 분리돼 있다. 표시명은 각각 Clipper Studio / Clipper Studio (dev). 이전 identity 통일 결함은 현재 HEAD에서 정정돼 있다.
- 서버의 같은 사용자+attempt key 동시성 잠금/유일성, 반대 terminal 전이 409, 로컬 terminal 응답의 run/status 확인이 존재한다. R01/R02는 이 계약의 바깥 연결 문제다.
- 로컬 attempt/outbox에 소유자 구분이 있고 bearer token은 저장하지 않는다. 미종결/모호한 항목을 보존하고 서버 확인된 종결 항목은 30일 보존하는 기본 정책도 구현돼 있다.
- 옛 Angular license adapter 제거, 네 렌더 preparer 등록, 대사 편집 후 TTS ID 무효화, BGM ID 유지가 확인됐다. 따라서 해당 구현 전체가 없다는 뜻은 아니다.
- 기존 사용자 소급 무료체험을 일반 조회/기존 로그인에 지급하는 경로는 발견하지 않았다. 새 PG table의 기존 행 전체 정리는 migration만으로 되지 않아 개발 DB clone 전환 검증은 여전히 필요하다.

## 다음 수정·재검증 순서 제안

1. 금융 내구성: R01–R05, R08. 서버 transaction 연결, 시작 응답 유실, 즉시 연결 저장, durable terminal/evidence, 반복 재시작, online/auth replay를 하나의 장애 시나리오로 검증.
2. 프로세스 소유권/종료: R06–R07. 실제 Nest writer와 Electron reader, 실제 spawn 순서로 검증. Windows는 사용자 실기 절차로 전달.
3. 사용자 흐름/파일 안전: R09–R13. 여섯 유료 operation 최초/재시도/취소/복구, 무료 두 renderer의 출력 격리, 보관함 잔액 갱신을 확인.
4. 위 수정 및 별도 로컬 검증 결과를 확인한 뒤 개발 DB 복제본 dump/rehearsal 안내로 돌아간다. 실제 개발 DB 변경/배포는 여전히 별도 승인이다.

이 문서는 수정 승인을 대신하지 않는다. 이번 작업은 리뷰와 증거 수집/문서 정정이며 제품 코드 수정·커밋·push·배포를 하지 않았다.
