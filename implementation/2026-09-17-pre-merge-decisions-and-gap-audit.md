# 정식 PG 통합 전 결정·수정·누락 감사

> 병합 전 조사·결정의 역사 기록이다. 이후 사용자 결정·실제 수정 결과가 우선하며 현재 정본은 [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)다. 아래 “현재 정본”, “승인 전”은 작성 당시를 뜻한다.

기준일: **2026-09-17 KST**

상태: **조사·설계 감사 완료 / 병합·구현 승인 전**

이 문서는 이번 대화의 최신 사용자 결정, 지정 인계 문서, `clipper_docs` 요청 범위, 8개 저장소의 실제 원격·worktree·코드를 다시 대조한 현재 정본이다. 과거 문서와 충돌하면 이 문서의 최신 결정과 실제 Git 상태를 우선하되, 아래 미결정 항목은 사용자 승인 없이 임의 확정하지 않는다.

## 1. 승인·작업 경계

- 현재 요청은 조사·설계·병합안 준비 승인이지 병합 승인이 아니다.
- fast-forward, merge, rebase, cherry-pick, 파일 복사도 저장소별 설명과 사용자 명시 승인 전 실행하지 않는다.
- 원본 `main/dev`를 직접 변경하거나 원격 push하지 않는다.
- 통합은 승인 뒤 별도 worktree/branch에서만 한다.
- 서버에 직접 접속하지 않는다. 서버·개발 DB·배포 명령은 장비·목적·영향을 설명한 뒤 사용자가 실행한다.
- 첫 목표는 통합과 별도 로컬 DB 검증이다. 개발서버 전환은 로컬 검증·복제 DB 리허설·전환계획 승인을 거친 별도 단계다.
- 실제 ML 플러그인 실행과 Build 5 전체 QA HOLD를 유지한다.

## 2. 8개 저장소와 관련 worktree 실제 상태

2026-09-17 `git fetch --prune origin` 뒤 확인했다. 원본 8개는 모두 `dev`, 미커밋 변경 없음이다.

| 저장소 | 원본 HEAD | `origin/dev` | 원본 뒤처짐 | integration HEAD | `dev only / integration only` |
|---|---|---|---:|---|---:|
| Angular | `019687d9` | `98d44958` | 44 | `f7bcadde` | 44 / 10 |
| Electron | `0b43737c` | 동일 | 0 | `b698014a` | 0 / 10 |
| NestJS | `e99b3962` | `4c32e03c` | 17 | `da3b7f2f` | 17 / 9 |
| Python | `88b1da27` | 동일 | 0 | `ae0a6fd5` | 0 / 1 |
| Infra | `6cc7a379` | 동일 | 0 | `948e8a12` | 0 / 16 |
| Web Admin | `beda584f` | 동일 | 0 | `dade0ee6` | 0 / 42 |
| Web API | `fdd0cb6b` | 동일 | 0 | `31e014b6` | 0 / 167 |
| Web Client | `4b361efc` | 동일 | 0 | `4d95a963` | 0 / 57 |

- 앱 이름 worktree는 `feature/app-window-name-20260915`, HEAD `7aed9f6`, clean, integration보다 2커밋 앞이다. `99444d8`, `7aed9f6` 모두 로컬 보존이며 push·병합되지 않았다.
- Desktop Nest 격리 수정은 integration HEAD 기준 7파일, `+559/-35` 미커밋이다. access/credit runtime projector와 Variation terminal 환급 보완 후보이며 확정 통합 커밋이 아니다.
- Web API 격리 수정은 OpenAPI 1파일 미커밋이다. active-access 설명 정정 후보이며 확정 통합 커밋이 아니다.
- 밈·대사 하이라이트 worktree는 clean하고 이번 작업에서 변경하지 않았다.
- 앱 이름 별도 Codex 작업은 현재 실행 중이 아니며, 실제 보존 상태는 위 Git 결과로 확인했다.
- 출시 후 API compatibility/versioning TODO는 사용자 요청으로 `clipper_docs/todos/2026-09-16-post-launch-desktop-api-compatibility.md`에 기록돼 있으며 아직 untracked다. 이번 전환의 옛 개발판 호환 구현 범위에는 넣지 않는다.

## 3. 확정된 제품·계약 결정

### 이용 자격·크레딧

- 현행 모든 tier는 플러그인 차등 없이 `entitlement_mode=all`이다.
- 장래 플러그인 차등을 절대 쓰지 않을지는 미정이므로 allowlist 스키마는 당장 삭제하지 않는다. 현재 정책이 `all`임을 계약 테스트로 고정한다.
- `active access`는 로그인 여부가 아니라 유효한 구독·관리자 플랜·무료체험 이용 자격이다.
- 구독이 끝났어도 유효한 추가구매 크레딧이 남은 사용자는 작업할 수 있다.
- active access가 없는 사용자는 남은 추가구매 크레딧을 쓸 수 있지만 새 추가구매는 할 수 없다.
- 실제 렌더가 실패하거나 취소되면 해당 attempt 차감분은 복구되어야 한다. queue에 job ID를 받았다는 사실만으로 성공 확정하지 않는다.
- 실패·취소로 환급된 뒤 사용자가 실패 카드의 `다시 시도`/`다시 만들기`를 누르면 원시도를 재사용하지 않는다. 현재 설정으로 새 견적과 과금 확인을 보여주고, 승인 뒤 새 attempt·새 operation·새 idempotency key로 다시 차감한다.
- 최초 실행과 사용자 재시도 모두 모든 preflight를 통과하고 사용자가 금액을 확인한 직후 차감한다. `preparing | queued | starting | running` 어느 단계에서든 실패·취소되면 공통 finalizer가 전액 환급한다.

### 출시 전 데스크톱 호환

- 이번 개발서버 PG 전환에서는 옛 개발판 API 계약을 지원하지 않는다.
- 새 통합 앱·Web API를 같은 계약으로 검증하고 사용자는 새 빌드 설치와 필요 시 1회 재로그인을 전제로 한다.
- 출시 후 `1.2.1 -> 1.2.2` 같은 하위 호환·API versioning은 별도 TODO다. 옛 Angular license 이름을 호환 계층으로 남기지 않는다.

### 앱 이름·identity

- 운영 표시명·macOS 앱·DMG·Windows 설치파일: `Clipper Studio`.
- 개발 표시명·macOS 앱·DMG·Windows 설치파일: `Clipper Studio (dev)`.
- 기존 appId, protocol scheme, 명시적 userData/sessionData, 캐시·포트, 업데이트 구조는 보존한다.
- 운영 데이터 경로는 기존 `Clipper`, 개발 데이터 경로는 기존 `Clipper Studio`를 유지한다.
- macOS 앱 이름 변경으로 기존 `safeStorage` 로그인 복호화가 안 돼도 1회 재로그인을 허용한다. Keychain migration은 현재 범위에서 하지 않는다.
- 복호화 실패는 크래시·반복 프롬프트·무한 루프 없이 로그아웃 상태가 되어야 하고, 재로그인 뒤 다음 실행에서 로그인 유지되어야 한다.
- 옛·새 개발 앱을 번갈아 실행하는 사용 방식은 지원하지 않는다.

## 4. 확정된 구현·정리 방향

### 공통 유료 attempt 수명주기

- 상속 계층을 늘리지 않고 구성 기반의 공통 attempt coordinator/finalizer 경계를 만든다.
- 여섯 유료 operation의 start, job/attempt 연결, terminal 성공·실패·환급, 취소, 사용자 재시도가 같은 경계를 통과해야 한다.
- 기능별로 흩어진 Shortform watcher, Dance JobsService, Dialog executor `finally`, Variation 자체 종결을 공통 finalizer로 통합한다.
- operation ID는 영상 job ID가 아니라 한 번의 견적·차감·성공/실패·환급을 잇는 금융 원장 실행 ID다.
- 동일 logical attempt의 start 재전송이 중복 차감되지 않도록 stable idempotency key와 서버 DB 유일 제약이 필요하다. 사용자가 명시적으로 새 재시도를 시작하면 새 attempt/key를 쓴다.
- job/attempt-operation의 최소 metadata는 사용자 PC의 기존 로컬 데이터 영역에 영속 저장할 수 있다. 프로젝트·미디어·입력 전체를 원격 DB에 올리지 않는다.
- 삭제 가능한 project/job 콘텐츠와 billing metadata/tombstone을 분리해 사용자 삭제를 실패·재환급으로 오인하지 않는다.
- Admin 수동 recovery는 자동으로 판정할 수 없는 마지막 안전망이다. 시간 경과만으로 성공·환급하지 않는다.
- 네트워크 실패한 terminal 보고를 잃지 않는 durable local outbox를 이번 통합 범위에 포함한다. terminal 명령을 먼저 로컬에 원자적으로 기록한 뒤 전송하고, 앱 재시작·네트워크 복구 때 같은 `runId`로 재전송한다. 서버의 `succeed/fail`은 이미 run 상태 잠금으로 같은 terminal 전이를 멱등 처리하지만, operation `start`에는 별도의 stable idempotency key와 DB 유일 제약을 추가해야 한다.
- outbox/attempt 중 미종결·전송대기·판정모호 항목은 기간만으로 삭제하지 않는다. 서버 종결 확인 완료 항목과 그 tombstone은 확인 시점부터 30일 보존한 뒤 자동 정리한다.

### Job 상태와 재시작

- `waiting + phase`가 아니라 status enum을 `preparing | queued | starting | running | completed | failed | cancelled`로 직접 확장한다.
- `render_prepare_pending`, payload 유무, `queue.contains()`를 domain 상태의 정본으로 쓰지 않는다.
- `preparing -> queued -> starting -> running -> terminal` 전이를 중앙에서 강제한다.
- 옛 개발 빌드 active queue를 새 빌드에서 이어받지 않는다.
- 기존 terminal `completed | failed | cancelled` 이력은 보존한다.
- 업데이트 시 남은 옛 `waiting | starting | running`은 새 failed 이력으로 만들지 않고 v2 store에서 제거한다.
- 배포 전 기존 빌드 active job 0건을 rollout precondition으로 확인한다.
- 신규 앱 재시작 시 active job을 자동 재개하지 않는다. interruption 실패로 종결하고, 안전하게 결과가 실패로 확정된 operation은 fail/refund한 뒤 사용자가 명시적으로 재시도한다.
- `starting/running` 외부 실행 결과가 모호하면 성공 결과와 환급이 동시에 생기지 않도록 evidence 확인 또는 Admin recovery로 보낸다.

### 프로세스 종료 정적 감사

- Electron이 직접 소유한 최상위 Python plugin은 `/shutdown` 요청 뒤 제한시간 내 종료하지 않으면 `SIGTERM`, 다시 실패하면 `SIGKILL`로 내린다. integration은 Windows에서 wrapper뿐 아니라 owned process tree 종료까지 추적한다.
- Electron의 Nest utility process 종료는 현재 `proc.kill()`과 최대 5초 대기뿐이다. Nest bootstrap은 `enableShutdownHooks()`를 호출하지 않으므로 signal 종료 때 `OnModuleDestroy`가 항상 실행된다고 볼 수 없다.
- Nest 내부 local ffmpeg render provider들은 job cancel용 `AbortSignal`은 받지만 앱 종료 전체를 위한 공통 child registry/shutdown hook이 없다. 일부 workflow executor만 자체 `activeProcesses`를 추적한다.
- Python renderer도 ffmpeg를 `subprocess.run/Popen`으로 띄우지만 process group 단위 소유권·종료 보장은 확인되지 않았다. 상위 Python/Nest가 죽을 때 하위 ffmpeg가 반드시 함께 종료되는지는 플랫폼별 실증이 필요하다.
- 따라서 유료 기능별 `starting/running` 종료 결과를 추측하지 않는다. Shortform·Variation·Dance·Dialog에 대해 정상 종료, 강제 종료, Nest crash, Python crash, 네트워크 단절을 각각 재현하고 PID tree·산출물·job·operation·outbox 상태를 대조한다. 실제 ML 실행 HOLD는 유지하므로 먼저 fake child/짧은 ffmpeg fixture와 packaged process lifecycle test로 검증하고, 실제 ML 실기는 HOLD 해제 뒤 별도 게이트로 둔다.

### 이번 감사에서 새로 발견한 누락

- `reserve -> submitReserved`와 `render_prepare_pending`을 쓰는 기능은 Shortform·Variation뿐 아니라 댓글 오버레이와 영상 랭킹도 있다.
- 현재 준비 재시도 registry에는 Variation만 등록돼 있다. Shortform·댓글 오버레이·영상 랭킹의 준비 미완 job은 공통 retry에서 `RenderPrepareIncompleteError`가 날 수 있다.
- 따라서 job enum·preparation callback·취소·재시도 개편은 네 렌더 기능 전체를 포함해야 한다. 댓글 오버레이·영상 랭킹은 현재 무료이므로 billing coordinator가 아니라 공통 job preparation 상태 기계만 적용한다.

### Shortform 최종 렌더

- `클립 생성하기`의 LLM·검색 미디어·줄별 TTS 생성과 마지막 `숏폼 생성하기` 뒤 렌더 입력 준비를 구분한다.
- 최종 흐름은 `편집 저장 -> 서버 preflight -> 성공 시 견적/확인 -> startRender 내부 authoritative preflight -> operation/job -> 보관함`이다.
- preflight 실패 시 편집 화면에 머물고 quote, operation start, job reserve, 보관함 이동을 모두 하지 않는다.
- 다음을 모두 검사한다: TTS ID 누락, 파일 누락, 손상, 대사 수정 뒤 재합성 실패, 새/빈 줄, media/slot 누락, 원격 media materialization 가능성, preflight 뒤 I/O race.
- sample 음성·무음·seed media로 누락을 숨기지 않는다.
- 제거 대상: per-clip fallback TTS, `CLIPPER_STUDIO_SEED_TTS`, sample TTS, silent WAV fallback, 참조 0 `prepareClipTts()`, 완전성 검사 후 seed media placeholder.
- 현재 정상 BGM 카탈로그가 사용하는 MP3와 `legacy-bgm.*` identity는 이름까지 그대로 유지한다. `legacy`라는 문자열을 없애기 위한 rename 또는 one-time migration은 하지 않는다.
- seed layout/logo도 이름만 보고 migration·rename 대상으로 분류하지 않는다. 현재 렌더에서 실제로 필요한지 먼저 검증하고, 필요하면 그대로 유지하며, 불필요하다고 입증된 경우에만 producer·consumer를 함께 제거하고 회귀 테스트한다.
- URL/paste/prompt는 이미 한 workflow를 공유하므로 세 Strategy/자식 클래스를 만들지 않는다. 세 plugin/operation identity와 작은 mode resolver만 유지한다.

### Angular·Desktop API 정리

- Angular의 `CurrentLicenseSummary/currentLicense/_license`와 도달 불가능한 queued/expired 이용권 필드를 완전히 제거하고 access·credit 원형 모델로 정리한다. PG 병합만으로 자동 제거되지 않는다.
- Desktop access/credit proxy는 TypeScript generic만 믿지 않고 실제 JSON을 runtime validation/projector로 검사한다. 필수 필드·enum·정수·page envelope 오류는 502로 실패하고 모르는 추가 필드는 버린다.
- Web API에서 없어진 독립 refund endpoint에 대응하는 Desktop Nest의 미사용 `refund()` 메서드와 테스트는 참조 0을 재확인한 뒤 제거한다. 환급은 operation `fail` 전이로 정확한 원차감분을 복구한다.
- 차감·환급 직후 Angular 잔액과 원장이 즉시 갱신되는지 별도 검증한다.

## 5. 개발 DB 데이터 정책과 실제 migration 영향

### 이전 승인 정책에서 유지되는 것

- 보존: 기존 사용자 계정과 로그인 관련 데이터.
- 초기화: 옛 요금제, 구매 신청, 이용권, 잔여 크레딧, 유효기간, 옛 차감·환급 장부.
- 초기화: 과거 금융 `operation_runs` 전체와 연결된 `operation_resolution_events`.
- 유지 정책: 현재 여섯 operation policy만 유지하고 폐기된 정책 제거.
- 기존 사용자에게 무료체험·이용권·크레딧을 소급 지급하지 않는다. 새 권한은 정상 PG 흐름으로 취득한다.
- 로컬 데스크톱 project와 terminal job 이력은 별개이며 보존한다. 여기서 삭제하는 operation history는 서버 금융 원장 기록이다.

### integration migration이 실제로 하는 일

- `1786560000000`: 기존 `payment_events`, `payment_orders`를 전부 삭제한 뒤 새 PG 열 구조로 바꾼다.
- `1786650000000`: 옛 `shortform.create`의 `credit_ledger`, operation run, policy를 삭제하고 세 Shortform operation policy를 만든다.
- `1786800000000`: replacement billing table 존재를 확인한 뒤 구형 `plans`, `purchase_requests`, `licenses`, `token_usage`, `credit_ledger`를 drop한다. down은 빈 표만 만들고 행을 복원하지 못한다.
- `1786850000000`: `operation_resolution_events`를 먼저, `operation_runs`를 다음으로 전부 삭제하고 여섯 정책 외 operation policy를 삭제한다. down 복구는 없다.

### 반드시 보완할 전환 확인

- 운영 DB 전체 삭제·재생성 절차를 개발 DB에 적용하지 않는다.
- 실제 개발 DB 적용 전에 별도 로컬 DB, 그다음 개발 DB dump 복제본에서 migration·앱 seed·보존/삭제 건수를 검증한다.
- rollback은 역migration이 아니라 전환 직전 dump를 검증된 절차로 복원하는 방식이다.
- `1786800000000`은 새 `user_access_grants`, `credit_grants`, `credit_ledger_entries`, `subscriptions`의 기존 행을 자동 초기화하지 않는다. 개발 DB가 부분 migration됐거나 새 PG 데이터를 이미 가진 경우 이전 승인 정책과 결과가 어긋날 수 있으므로, clone에서 이 표들의 사전 건수·출처·연결 관계를 조사하고 승인 정책에 맞춘 전체 금융 초기화의 대상 건수와 삭제 순서를 사용자에게 보여준 뒤 적용해야 한다.
- 위 조사는 새 PG 테스트 데이터를 보존할지 임의 선택하기 위한 것이 아니다. 현재 승인 정책의 목표 상태는 사용자·로그인은 보존하되 기존 금융 상태는 구·신 스키마를 막론하고 초기화하고, 기존 사용자에게 access·credit을 소급 지급하지 않는 것이다. `user_access_grants/credit_grants/subscriptions`가 이미 존재하면 테스트키 결제·관리자 수동 지급을 포함한 개발 금융 데이터로 보고 clone에서 연결 관계와 삭제 순서를 검증한다. 다만 실제 live provider 거래로 의심되는 행이 발견되면 자동 삭제하지 않고 중단해 별도 확인한다.
- `테스트 구독`은 DB의 정식 source/status 이름이 아니라 이전 설명에서 사용한 부정확한 표현이었다. 실제 `user_access_grants`는 `subscription | admin_plan` source의 이용 자격, `subscriptions`는 정기결제 계약, `credit_grants`는 무료체험·구독·추가구매·관리자 지급 등으로 생긴 크레딧 묶음이다. 이전 예시의 5,000은 실제 확인값이 아니라 임의 숫자였다.
- 세 DB dump는 같은 시점 스냅샷이 아닐 수 있으므로 실제 전환에서는 쓰기 중지/일관성 확보 절차가 필요하다.

## 6. 통합 후 로컬 검증 게이트

- access 없음/활성/만료와 크레딧 0/충분/추가구매만 잔존 조합.
- 모든 tier 동일 플러그인 접근과 `entitlement_mode=all`.
- 견적·확인·실제 차감액 일치, batch 일부 시작/실패 원복.
- 준비 실패, queue 제출 실패, 대기/실행 중 취소, 실제 렌더 실패의 정확한 환급과 중복 fail 멱등성.
- 성공 시 차감 유지, 실패·취소 시 환급, 사용자 재시도 정책에 맞는 새/기존 operation 처리.
- 사용자 재시도 때 반환 안내 -> 새 견적/확인 -> 새 attempt/차감이 순서대로 보이고, 확인 없이 무료 재실행하거나 환급된 operation을 재사용하지 않는지.
- terminal 전송 전 앱 종료·네트워크 단절·응답 유실 뒤 outbox가 남고 재시작/복구 후 같은 terminal 전이를 중복 환급 없이 완료하는지.
- Shortform·Variation·Dance·Dialog의 플랫폼별 process tree 종료, orphan child 0건, 모호한 늦은 산출물의 Admin recovery 분기.
- 차감·환급 직후 보관함 이동과 설정 재진입에서 잔액·원장 refresh.
- operation evidence, 작업명·사유·금액, resource ownership.
- access/credit malformed JSON runtime 거절과 추가 필드 정규화.
- Shortform 7개 preflight 범주, 정상 manifest의 fallback TTS/media 0개.
- 네 reserve 기능의 상태 전이, preparation callback, cancel/retry/restart/reorder invariant.
- 앱 이름, 데이터 경로, protocol, update identity, macOS 1회 재로그인, Windows 업그레이드/바로가기/제거 동작.
- 빈 로컬 DB migration과 개발 DB clone 리허설, dump restore rollback.

## 7. 병합안 전에 아직 닫지 못한 결정·설계

1. **attempt metadata/outbox schema**: 로컬 저장과 outbox의 이번 통합 포함, 미종결·전송대기·모호 항목의 해결 시까지 보존, 서버 종결 확인 항목·tombstone의 30일 보존은 승인됐다. 남은 설계는 필드, 파일 위치, 원자적 저장 방식, retry/backoff다.
2. **running interruption 판정과 process ownership**: 앱 종료 때 하위 프로세스를 확실히 중단할 수 있는 기능과 늦은 성공 가능성이 있는 기능을 플랫폼별로 검증해야 한다. 모호한 상태를 자동 환급할 조건은 정하지 않았다.
3. **seed layout/logo 기능 감사**: 이름의 `legacy` 여부와 무관하게 현재 Shortform manifest·recipe·renderer에서 실제 기능을 담당하는지 확인해야 한다. 단순 rename이나 저장 template migration은 범위에 넣지 않는다.
4. **부분 PG 데이터 정리**: clone에서 replacement table에 기존 행이 있으면 현 승인 정책대로 금융 상태를 초기화할 삭제 순서·건수를 검증한다. live provider 거래 의심 행만 자동 삭제하지 않고 별도 확인한다.

재시도 과금과 차감 시점의 제품 정책은 2026-09-17 사용자 승인으로 닫혔다. 위 1~4는 그 정책을 반영한 구체 설계·정적/동적 검증 결과를 저장소별 병합안에 포함해 승인받아야 한다.

## 8. 이번 감사의 변경·비변경

- 변경: 원격 ref fetch, 읽기 전용 코드/Git 대조, `.codex` 설계·handoff 문서 갱신.
- 비변경: 8개 원본 소스, 관련 기능 worktree, branch checkout, DB, 서버, 배포.
- commit·merge·rebase·cherry-pick·push·fast-forward·deploy 없음.
