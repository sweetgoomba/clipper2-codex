# 운영·dev 통합 및 main 반영

## 최신 Git 후속 상태

원본 checkout 전환 완료: 사용자 “응” 승인 후 원본8repo를 `integration/dev-pg-local-validation-20260917`로 전환했다. 기존 통합 worktree8개는 같은 HEAD에서 detach해 보존했다. 원본은 clean 및 origin 통합 참조와 일치, dev 참조는 origin/dev와 계속 일치한다. `checkout --no-overwrite-ignore` 사용, 기존 ignored 환경파일11개(앱 산출물 내부2개 포함) 전후 SHA256 비교 불변. 비밀값 출력/복사/수정 없음. 원본 환경의 Nest `.env.local` DB 호스트가 비-loopback이며 실제 사용 여부는 미확인이다. 앱 실행 전 환경 로딩·연결 목적지·로컬 포트·의존성/산출물을 점검한다. 기존 통합 Nest cwd Node4개는 종료하지 않았다. 앱/DB/ML 실행·코드커밋·코드push·병합 없음. 앞으로 검증은 원본 폴더에서 하며 아래 옛 작업위치 설명보다 이 절이 우선한다.

옛 fix 정리 완료: Nest `000414f`, Web API `3c33268` 및 앱 이름 feature `7aed9f6` push·원격 SHA 확인 완료. 두 fix worktree만 제거했으며 로컬/원격 브랜치·커밋과 앱 이름 worktree는 유지했다. [상세](../../implementation/2026-09-17-old-pg-worktree-disposition.md). 아래 “미커밋/승인 전/보류”는 조사 당시 기록이다.

후속 [옛 fix worktree 대조](../../implementation/2026-09-17-old-pg-worktree-disposition.md): Nest7파일/Web API1파일의 초기 수정 목적은 현 통합 구현에 반영·대체됐다. 고유 미통합 커밋은 없으나 미커밋 파일을 그대로 병합했던 것은 아니다. 현재 통합 관련148 tests PASS. 보존용 커밋·push·worktree 제거는 승인 전이며 아직 실행하지 않았다.

2026-09-17 원본 Angular/Nest dev fast-forward 뒤 사용자에게 나머지5repo의 정확한 목적지 승인을 받았고 통합8repo push를 모두 완료했다. 대상은 각 기존 `https://github.com/OhMyMetabuzz/<repo>.git`의 `integration/dev-pg-local-validation-20260917` 브랜치다. 원격 SHA와 로컬 HEAD 일치를 8repo 모두 확인했다: Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Python `60417ce`, Infra `f975f34`, Web Admin `3d47536`, Web API `8b074a5`, Web Client `a4bc54b`. 통합8repo clean이며 제품 코드·HEAD는 추가 변경하지 않았다. 원격 main/dev push·추가 병합·배포·DB 변경·서버 접속 없음. 이번 검증은 Git SHA/clean/원격 일치이며 빌드·테스트를 재실행한 것은 아니다. 다음은 수정본 설치형 로컬 실기이며 ML/Build5 HOLD를 유지한다.

출시 후 API compatibility TODO는 `clipper_docs`가 아니라 [`.codex/todos`](../../todos/2026-09-16-post-launch-desktop-api-compatibility.md)에 보존한다. 아래 커밋 단계의 push 없음·원본 미변경 표현보다 이 절이 우선한다.

최종 확인: 2026-09-17 KST. 상태: **8repo 통합 유지 / R01–R13+A14 및 추가 환급 누락·Dialog 수정 검증 / 4repo 로컬 커밋 완료, 설치형 로컬 실기 필요**.

실기 전 Git 정리 완료: [커밋 결과](../../implementation/2026-09-17-integration-commit-proposal.md)에 승인된 코드4repo의 SHA와 fresh 검증을 기록했다. Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Web API `8b074a5`로 로컬 커밋했고 통합8repo clean, 원본8repo dev/HEAD는 unchanged clean이다. 사용자 명시 요청으로 `.codex`만 별도 커밋·푸시한다. 코드 push·원본 dev fast-forward·추가 병합은 수행하지 않았다. 아래 미커밋/이전 HEAD 표현은 커밋 전 역사 기록이다.

최신 추가 확인: 두 잔여 항목 진단 뒤 사용자 “응 진행해줘” 승인으로 수정했다. [최신 수정 결과](../../implementation/2026-09-17-archive-refund-fix-result.md)가 아래 미재현·승인 대기 기록보다 우선한다. 취소 직전 상태를 영속 저장하고 실행 전 취소의 fail outbox를 삭제 전에 보존한다. stale job/project attempt ID fallback을 제거했다. Dialog 제품 로직은 유지하고 테스트만 분리했다. 최종 Nest 전체 2,678/2,678, 대상 70, Dialog 20회×11건, 격리 부팅 PASS. 다음은 수정본 설치형 로컬 실기이며 커밋·push·DB 리허설·배포는 자동 진행하지 않는다. 실제 Google/Windows는 사용자 실행, ML/Build5 HOLD 유지.

[전체 작업 현황](../WORKBOARD.md)

## 현재 상태

### 2026-09-17 Astra 수정·재검증 — 커밋 전 기록

사용자 “진행해줘” 승인 후 R01–R13을 수정했다. 최신 [수정·검증 결과](../../implementation/2026-09-17-astra-fix-result.md)가 아래 모든 과거 checkpoint보다 우선한다. Angular/Electron/Nest/Web API 4repo의 미커밋 수정이며 8repo branch/HEAD·원본 checkout은 그대로다. 새 병합·커밋·push·배포·실제 DB 변경은 없다.

추가 A14는 사용자 승인 후 수정했다. Variation **최초 실행**도 preparing job을 먼저 저장하고 job별 차감 연결 후 제출한다. 취소·삭제된 예약을 뒤늦게 차감하지 않도록 기존 job lock으로 보호했다. 실제 JSON 재시작 회귀와 독립 재리뷰를 완료했다. 코드 검토상 기존 post-charge 삭제→환급 outbox 저장 전 종료 위험은 별도 재현하지 않았으므로 후속 확인한다. 기존 Dialog 5ms DELETE 테스트의 간헐적 실패도 기록했다. 상세 최종 테스트 결과는 위 최신 결과 문서를 따른다. 개발 DB 복제본 리허설로 자동 진행하지 않는다.

실제 ML/Build5 HOLD 유지. 실제 Google OAuth와 Windows installer는 사용자 실행이며 새 수정본의 설치형 UI offline/online 실기도 남아 있다. 아래 과거 병합·설계 기록의 “다음 행동”, “미구현”, “clean” 표현을 현재 상태로 해석하지 않는다.

### 2026-09-17 Astra 독립 재감사 — 수정 전 역사 기록

[재감사 결과](../../implementation/2026-09-17-astra-independent-review.md)는 수정 전 R01–R13 결함을 확인한 기록이다. 시작 응답 유실·DB pool·Variation 연결 저장·terminal 저장 순서·반복 재시작·프로세스 identity/종료·outbox online replay·차감 시점·preflight/재시도/출력 격리·잔액 갱신 문제로 당시 “후속 안전성 구현까지 모두 완료” 판정을 철회했다. 이후 수정 상태는 위 최신 절을 따른다.

이번 리뷰에서 제품 코드는 수정하지 않았고 commit/merge/push/deploy/서버/DB 변경도 없다. 다음 행동은 수정 범위 확인 후 회귀 테스트를 포함한 보완과 재검증이다. 개발 DB 복제본 리허설로 곧바로 넘어가지 않는다. Electron 전체 SHA는 `827fcda8b12a34232c2574983afff6284b69d949`가 맞으며 이전 문서의 전체 값 오기를 정정했다.

### 2026-09-17 이전 로컬 검증 checkpoint — 완료 판정은 위 재감사로 정정

아래는 이전 실행 증거와 당시 판정을 보존한 기록이다. 현재 판정은 위 Astra 재감사를 우선한다. 과거의 “완료”, “승인 대기”, “미구현”, 옛 HEAD는 현재 상태로 자동 해석하지 않는다.

- `.worktrees/dev-pg-local-validation-20260917/`의 8개 `integration/dev-pg-local-validation-20260917` branch에 승인된 병합과 후속 안전성 구현을 완료했다. 8개 worktree는 clean이다.
- 현재 HEAD: Angular `ac879329`, Electron `827fcda`, NestJS `f452b6f`, Python `60417ce`, Infra `f975f34`, Web Admin `3d47536`, Web API `7392147`, Web Client `a4bc54b`.
- Electron `1930ad4`가 운영 identity를 개발 identity로 잘못 통일한 문제는 사용자 지적 뒤 `827fcda`에서 정정했다. 운영은 기존 `ai.clipperstudio.app`/`clipperstudio://`/`Clipper`, 개발은 기존 `ai.clipperstudio.desktop`/`clipper://`/`Clipper Studio`를 각각 유지하고 표시·패키지 이름만 새 요구대로 구분한다.
- Web API 기준선 3건과 Web Admin telemetry 순서 가정 1건은 runtime 동작을 바꾸지 않는 테스트 보정으로 완료했고 전체 suite를 통과했다.
- operation start 멱등성, 로컬 billing attempt metadata, 30일 보존, durable outbox, 공통 finalizer, 명시적 job 상태 enum, 새 유료 재시도, Shortform preflight, 옛 license adapter 제거, 시작 시 reconciliation, Electron child-process 종료·identity 보존을 구현했다.
- 별도 로컬 PostgreSQL의 User/Admin/Release DB에서 migration 1회 및 재실행 no-op을 검증했다. 로컬 API에서 무료체험과 “구독 종료 후 추가구매 크레딧만 잔존” 정책, 차감·중복방지·환급·evidence·ledger를 검증했다.
- `DropLegacyBilling` 직전의 실제 과거 schema fixture도 재현했다. 옛 table/review order/operation history는 제거되고 이미 존재하던 새 PG grant/ledger는 보존됨을 확인했으므로, 개발 금융 상태 전체 초기화에는 별도 reset SQL이 필요하다. replacement table 누락 시 drop 전 안전 중단과 dump→migration→DB 재생성→restore의 핵심 row-count checksum 복원도 통과했다.
- Web Client 실제 브라우저와 macOS arm64 `Clipper Studio (dev).app`을 실행해 검증용 일회성 token/code session, access/credit 표시, Variation/설정 진입, 정상 종료와 잔존 프로세스 0을 확인했다. 격리 API에는 Google OAuth client ID/secret을 넣지 않았으므로 실제 Google OAuth 브라우저 로그인과 표시명 변경 뒤의 실사용자 재로그인은 검증하지 않았다. 격리 계정에 기존 프로젝트가 없어 특정 기존 프로젝트 표시 자체도 아직 미검증이다.
- Windows NSIS 실제 installer는 사용자가 Windows 서버에서 검증한다. 실제 ML, Build 5 전체 QA, 실제 Toss 결제, 서버·개발 DB 변경은 수행하지 않았다.
- push·배포·main/dev 직접 변경·서버 접속·개발 DB 변경은 모두 0건이다.

당시 다음 행동으로 제시했던 **개발 DB 복제본 리허설은 재감사 결함 수정·검증 뒤로 순연**한다. 리허설에 돌아오면 에이전트가 서버에 접속하지 않고 사용자가 read-only dump를 만든다. 장비·접속 방식·DB 이름을 확인한 뒤 명령을 안내하고 복제본 inventory/reset/migration/dump 복원 결과를 다시 승인받는다. 실제 개발 DB migration·배포로 자동 진행하지 않는다.

### 과거 병합·설계 기록

2026-09-17 사용자의 명시적 승인 뒤 `.worktrees/dev-pg-local-validation-20260917/`에 8개 저장소별 `integration/dev-pg-local-validation-20260917` branch를 만들고 최신 `origin/dev`와 formal-PG integration을 `--no-ff` 병합했다. Electron은 앱 이름 2커밋을 두 번째 merge로 추가했다. 충돌 0건, 원본 checkout 변경 0건, push·배포·서버·DB 변경 0건이다. 정확한 merge HEAD, 빌드·테스트, 앱 패키징, 새 Web API 기준선 문제는 [2026-09-17 병합·기준선 결과](../../implementation/2026-09-17-local-integration-baseline-result.md)가 정본이다.

후속 구현은 아직 시작하지 않았다. Web API 전체 unit의 3건 실패를 조사한 결과 production 결함이 아니라 (1) 실제 현재 시각에 의존하는 고정 날짜 테스트 2건과 (2) formal-PG/dev entity 결합 뒤에도 배열 끝 순서를 가정한 datasource 테스트 1건이다. 사용자 신규 문제 승인 규칙에 따라 테스트 전용 수정안 승인을 기다린다.

8repo `integration/main-unification-20260911` 원격보존. 7개 merge commit, Client는 추가dev변경0. [정확한 SHA·조합 결과](../../implementation/2026-09-15-main-integration-result.md), [병합 기준](../../implementation/2026-09-15-main-integration-plan-update.md).

중복 integration worktree는 제거했다. 사용자 PC의 원본8repo는 후속 요청으로 다시 최신dev로 전환됐다. 통합 결과는 branch에 남아 있으며 현재 원본 소스와 동일하지 않다. main에는 반영하지 않았다.

2026-09-17 `git fetch --prune origin` 재확인 결과도 동일하다. 위 마지막 문장의 "최신dev"는 더 이상 8repo 모두에 적용되지 않는다. Angular `origin/dev=98d449584055b324f223678f058e255c7d464c80`는 integration 공통기준 `019687d9` 뒤로 44커밋 전진했다. NestJS `origin/dev=4c32e03c327003e85ec5da248e362d4e85b49fb7`는 공통기준 `e99b3962` 뒤로 17커밋 전진했다. 원본 checkout은 각각 이전 dev HEAD에 그대로 두었고 clean이며, 승인 없이 fast-forward하지 않았다. 나머지6repo `origin/dev`와 8repo integration HEAD는 기존 기록과 같다.

작업 파일을 바꾸지 않는 `git merge-tree` 시뮬레이션은 8repo 모두 텍스트 충돌0이었다. 의미상 동시수정은 Angular5파일(variation API/store/spec와 projects component/spec), NestJS1파일(`test/variation-v2-render-service.test.js`)이다. 자동 결과에서 최신dev의 베리에이션 효과음 슬롯·영상/프로젝트 삭제와 integration의 PG 과금·크레딧 안내가 함께 남는 것을 확인했다. 실제 병합은 사용자 승인 전 실행하지 않는다.

Electron 앱 표시 이름 작업은 integration HEAD `b698014a` 위 로컬 커밋 `99444d8dd40ab198c8664aecf7959a637cc8b3ec`, `7aed9f666d26b55c22307c7a77df82751cb0e8b5`로 보존됐다. push되지 않았다.

사용자 질문을 계기로 PG 계약을 다시 대조해 아래 세 격리 작업을 만들었다. 어느 변경도 dev/main/integration에 병합하거나 push하지 않았다.

- Web API: `.worktrees/pg-contract-render-refund-20260916/web/clipper_web_api`, `fix/credit-operation-contract-20260916`, integration HEAD `31e014b` 기준. operation 문서의 잘못된 active-access 요구를 실제 정책에 맞게 수정했다.
- Desktop Nest: `.worktrees/pg-contract-render-refund-20260916/desktop/clipper_nestjs`, `fix/pg-contract-and-render-refund-20260916`, integration HEAD `da3b7f2` 기준. access/credit 응답 런타임 projector와 Variation terminal 과금·환급을 구현했다.
- Electron: 기존 앱 이름 worktree에서 운영/개발의 macOS·Windows 패키지 이름까지 각각 `Clipper Studio`/`Clipper Studio (dev)`로 후속 수정하고 두 번째 로컬 커밋으로 보존했다. 상세는 앱 이름 카드에 기록했다.

## 과거 병합 전 다음 행동·설계 기록

제안 작업공간은 `.worktrees/main-unification-local-verify-20260917/{desktop,web}/...`, 공통 branch는 `integration/main-unification-local-verify-20260917`이다. 다만 전체 과금 수명주기 재감사에서 병합 전 정할 문제가 확인되어, 현재는 저장소별 최종 병합안을 제시하는 단계로 넘어가지 않는다. macOS `safeStorage`는 사용자가 새 앱에서 1회 재로그인을 허용해 기존 Keychain migration을 현재 범위에서 제외했다. branch/worktree 생성과 모든 병합·cherry-pick은 승인 대기다.

승인 후 Angular 크레딧확인+최신 베리에이션 효과음/삭제, Electron identity+표시명+키검사/종료, API/Admin 계약·migration, Nest 과금+최신 베리에이션 계약·디스크정리+리소스소유권의 조합을 검증한다. dev로 실행한 로컬 앱 정상보고나 카드사 심사판 검증은 통합판 검증이 아니다.

2026-09-16 정책·계약 재검토에서 아래를 통합 전 명시적 정리 대상으로 확인했다.

- 모든 현재 tier는 `entitlement_mode=all`이라 플러그인 차등을 사용하지 않는다. 장래에 차등을 다시 쓸지는 미정이므로 allowlist 스키마를 즉시 삭제하지 않고, 현재 정책이 `all`임을 계약 테스트로 고정한다.
- `access/current`의 활성 access는 로그인 여부가 아니라 유효기간 안의 구독·관리자 플랜·무료체험 이용 자격이다. 정책은 이미 "구독 종료 후 보유 중인 유효 추가구매 크레딧 사용 허용, 신규 추가구매 차단"으로 결정돼 있었다(`main/2026-08-31-toss-payments-pg-completion-refund-credit-design.md` 656-657행). Web API 코드와 credit tests도 이를 구현하지만 OpenAPI `/operations/start` 설명만 active access가 필요하다고 잘못 적혀 있었다. 격리 Web API 수정안은 문서를 코드·정책에 맞췄다.
- 최신 `origin/dev` Nest의 Variation에는 PG operation 과금 자체가 없다. formal-PG integration은 영상마다 먼저 차감한 뒤 큐 제출 즉시 operation을 성공 처리해, 나중의 실제 렌더 실패가 환급되지 않는 결함이 있었다. 사용자 정책은 실제 렌더 실패·취소 시 복구다. 격리 Nest 수정안은 제출 때 operation을 열린 상태로 두고 실제 job `completed`에서 성공, `failed/cancelled`에서 fail→정확한 차감분 환급, 실패 재시도에서는 새 operation으로 재과금한다.
- Web API에서 독립 `/operations/:runId/refund` 엔드포인트는 제거됐지만 Desktop Nest의 사용되지 않는 `refund()` 메서드와 단위 테스트가 남아 있다. 통합 시 참조0을 다시 확인하고 제거하는 안을 제시한다. 실제 환급은 operation `fail` 전이의 정확한 차감분 환급을 사용한다.
- Angular의 `CurrentLicenseSummary/currentLicense/_license`는 PG integration 자체에 access+credit 응답을 옛 UI 모양으로 합성하는 adapter로 들어 있으므로, 단순 병합으로 저절로 사라지지 않는다. `/licenses/current` 원격 호출은 이미 없어졌지만 옛 이름, queued 상태·필드·표시 테스트는 명시적으로 `AccountBillingSummary` 계열로 바꾸고 도달 불가능한 옛 이용권 대기 필드를 제거해야 한다. 사용자의 명시적 요구에 따라 통합안의 정식 정리 범위로 포함한다.
- access/credit Desktop Nest 프록시는 TypeScript 타입 표명만 하고 런타임 JSON을 믿던 상태였다. 격리 Nest 수정안은 `unknown` 응답을 projector로 검사·정규화하고, 필수 필드/enum/정수/페이지 envelope가 잘못되면 502로 실패하며, 모르는 추가 필드는 버리는 forward-compatible 계약 테스트를 추가했다.

## 전체 유료 작업 수명주기 재감사

정식 PG의 유료 operation은 `shortform_url.create`, `shortform_paste.create`, `shortform_prompt.create`, `dialog_highlight.extract`, `dance_highlight.extract`, `variation.render` 여섯 개다. 모두 `charge_then_refund` 정책이지만 Desktop의 실제 시작·재시도·취소 연결은 동일하지 않다.

- Dance Highlight는 큐가 실제 실행을 가져간 뒤 차감한다. 대기 취소는 미차감이고, 실행 결과가 `failed/cancelled`면 환급된다. 재시도는 새 job·새 operation이지만 Angular 공용 재시도 UI가 새 과금 확인창을 다시 띄우지 않는다.
- Dialog Highlight도 실제 executor 진입 때 차감하며, 성공하지 못한 종료는 `finally`에서 환급한다. 재시도는 새 operation이지만 새 과금 확인창이 없다.
- Shortform 세 경로는 큐 job 예약 전 차감하고 별도 in-memory watcher가 terminal 상태를 보고 성공/환급한다. 따라서 대기 job도 이미 차감된 상태다. 공용 job 재시도는 이 orchestrator를 우회하므로 현재는 새 operation 없이 무료 재실행되며 watcher도 붙지 않는 결함이 있다.
- Variation은 영상별로 큐 예약 전 차감한다. integration은 제출 직후 성공 처리해 terminal 실패·대기 취소를 환급하지 않았고, 재시도는 환급된 옛 operation ID를 복사했다. 격리 수정안은 이 세 항목만 보완했지만 새 과금 확인창은 아직 없다.

### 최신 `origin/dev`의 사용자 재시도 실측

보관함/프로젝트의 `다시 시도`와 Variation 결과의 `다시 만들기`는 모두 Angular에서 별도 견적·확인 없이 공통 `POST /jobs/:jobId/retry`를 호출한다. Nest는 실패·취소 잡의 params로 새 job을 만들지만 과금 결과는 플러그인별로 갈린다.

- Dance는 새 job이 queue claim된 뒤 `dance_highlight.extract` operation을 새로 시작하므로 **확인창 없이 다시 차감**한다.
- Dialog도 새 executor 실행 때 `dialog_highlight.extract` operation을 새로 시작하므로 **확인창 없이 다시 차감**한다.
- Shortform의 렌더 job은 공통 `clipper_video_render` job이다. 재시도가 `ShortformRenderOrchestrator`를 다시 통과하지 않아 새 operation·terminal watcher가 없으므로, 준비가 끝난 잡의 재시도는 **무료 재실행**이 된다. 준비 중 실패한 Shortform 잡은 등록된 `RenderJobPreparer`가 없어 공통 재시도 자체가 실패할 수 있다.
- 최신 dev의 Variation v2에는 PG operation 과금 코드가 없으므로 최초 실행과 재시도 모두 무과금이다. Variation 과금은 formal-PG integration이 dev의 v2 렌더 서비스에 별도로 결합한 변경이다.

따라서 "Shortform/Variation은 예약 때 차감, Dance/Dialog는 실행 때 차감"은 최신 dev 전체의 설명이 아니라 formal-PG integration의 설명이다. 최신 dev는 **Shortform=예약 전 차감, Dance/Dialog=실행 시 차감, Variation=차감 없음**이다.

### 갈라진 원인과 필요한 공통 경계

Git 이력상 공통 job retry는 2026-06-20 구조 개편 때 이미 존재했다(`99894567`). Dance/Dialog/Shortform operation billing은 2026-07-08 각 기능의 서로 다른 실행 소유자에 후삽입됐고, Variation v2는 9월에 새로 만들어진 뒤 PG 통합 과정에서 과금이 별도 결합됐다. Angular 견적 확인, Desktop operation client, Web API 원장은 공용이지만 **한 번의 유료 job attempt를 생성·영속화·종결·재시도하는 공통 수명주기**는 없다. 최초 실행은 기능별 orchestrator를 타고 재시도는 더 아래의 공통 job queue로 바로 들어가므로 과금 경계를 우회하거나 중복한다.

상속 계층을 늘리는 것보다 구성(composition) 기반 `BillableJobAttempt` 경계를 검토할 가치가 있다. 기능은 operation key·견적 입력·차감 시점 정책·실제 준비/실행만 제공하고, 공통 계층이 attempt key, operation start, terminal 성공/환급, 사용자 재시도를 조정하는 방향이다. 사용자는 (1) job/attempt-operation 최소 연결정보를 원격 프로젝트 DB가 아니라 **사용자 PC의 기존 로컬 데이터 영역**에 영속 보존하는 원칙과 (2) Shortform watcher·Dance JobsService·Dialog executor `finally`·Variation 자체 서비스에 흩어진 terminal 종결을 **공통 finalizer로 통합해야 한다**는 방향을 확정했다. 실제 저장 스키마·보존기간·호출 경계와 병합 범위는 구현 전에 별도 제시해 승인받는다. 로컬 프로젝트·미디어·작업 입력을 서버 DB로 옮긴다는 뜻이 아니다.

Shortform의 용어도 분리한다. 첫 `클립 생성하기`는 LLM 대본·검색 미디어·줄별 TTS를 실제 생성하는 **클립 생성 단계**다. 마지막 `숏폼 생성하기` 뒤 `render_prepare_pending=true` 구간은 기존 줄별 TTS 파일의 경로·길이를 확인하고, 선택 미디어를 로컬화하고, asset/manifest/`clipper_payload`를 조립해 예약 job을 실제 실행 큐에 활성화하는 **렌더 입력 준비 단계**다. 다만 최신 dev의 공용 `ClipperStudioAssetPreparer.prepare()`가 이 구간에서 클립 전체 대사를 합친 별도 fallback TTS artifact를 다시 합성(실패 시 seed/silent fallback)한다. manifest의 자막은 기존 줄별 `ttsArtifactId`를 우선 사용하고 fallback ID를 뒤에 추가한다. 따라서 "TTS를 전혀 생성하지 않는다"도 사실이 아니며, 중복/legacy fallback 경로의 필요성을 통합 설계에서 재검토한다.

추가 코드·Git 추적으로 이 fallback의 기원과 실제 소비 경계를 확정했다. `ClipperStudioAssetPreparer`는 현재 Shortform보다 앞선 2026-05-04 `673c9650`에서 옛 Clipper Studio/Clipper1 호환 프로젝트가 실제 자산 없이도 렌더되도록 seed media·무음 TTS·layout·logo·출력 선언을 한 번에 만드는 구성요소로 시작했다. 같은 날 `41792be0`이 번들 seed를, `bb07a87b`가 macOS 로컬 TTS 합성과 seed/silent fallback을 넣었다. 2026-06-11 `06e31233`에서 현대 Shortform의 `클립 생성하기`가 줄별 실제 TTS를 생성하게 됐지만, 최종 렌더가 이미 호출하던 옛 preparer와 per-clip fallback append는 제거되지 않았다. 2026-06-18 `0370d891`은 옛 Clipper Studio project API를 제거했으나 preparer는 Shortform 의존성으로 남았고, 7월 builder/orchestrator 추출은 동작 보존 리팩터링이라 이를 그대로 옮겼다.

정상 줄별 TTS와 fallback TTS가 모두 manifest/recipe의 TTS 목록에 들어가지만, 현재 Python payload mapper는 그 목록을 TTS 파일 lookup map으로 사용한다. 각 subtitle은 `line.ttsArtifactId ?? fallbackId`로 하나만 선택하므로 정상 줄 ID가 있으면 fallback이 별도 음성으로 무조건 겹쳐 재생되는 것은 아니다. fallback은 줄 ID가 없는 경우에만 그 subtitle의 음성으로 연결된다. 문제는 정상 프로젝트에서도 불필요한 per-clip 합성·파일 생성·artifact 혼입을 수행하고, 합성 실패 시 실제 사용자 목소리와 무관한 sample 음성 또는 무음을 조용히 대체할 수 있다는 점이다. 기존 개발 사용자 데이터 보존을 고려해 옛 저장 프로젝트의 누락 TTS 처리 정책(명시적 재생성 또는 렌더 차단)을 정한 뒤, 현대 Shortform 정상 경로에서는 암묵 fallback TTS를 제거하고 asset preparer의 media/layout/logo/output 준비와 TTS 책임을 분리하는 안을 우선 검토한다.

`legacy*` 이름 자체는 정리 대상이 아니다. 새 렌더의 per-clip fallback TTS, `CLIPPER_STUDIO_SEED_TTS`, 참조 0인 `prepareClipTts()`는 명시적 TTS 완전성 검사를 먼저 넣은 뒤 제거할 대상이다. seed media placeholder도 현재 자산 누락을 숨기므로 클립 media 완전성 검사와 함께 제거하는 방향이다. 반면 `clipper-studio-bgm/*.mp3`와 `legacy-bgm.*` identity는 현재 정상 BGM 카탈로그가 실제 사용하므로 파일·ID·provider 이름을 그대로 유지하며, 이름에서 `legacy`를 빼기 위한 migration은 만들지 않는다. layout/logo seed도 `legacy`라는 이름만으로 template migration·rename 대상으로 잡지 않는다. 현재 Shortform 렌더에서 실제로 필요한지 확인해 필요하면 유지하고, 불필요하다고 입증된 경우에만 producer·consumer를 함께 제거하고 회귀 테스트한다.

현재 최종 `숏폼 생성하기`에는 모든 줄의 TTS ID·파일과 모든 클립의 media 완전성을 확인하는 동기 preflight가 없다. 최초 `클립 생성하기` 중 TTS 합성이 throw하면 생성은 완료되지 않지만, 이후 대사 편집은 기존 TTS ID를 먼저 지우고 재합성을 호출하므로 재합성 실패 시 ID 없는 줄이 남을 수 있다. `projectTtsArtifactPathsFor()`도 ID 없는 줄을 필터로 건너뛰어 fallback이 대신 사용된다. ID는 있으나 파일이 사라진 경우는 HTTP 응답·보관함 이동 뒤 비동기 준비에서 실패하고, 읽을 수 있으나 손상된 오디오는 duration probe가 오류를 삼켜 실행 단계까지 갈 수 있다. 따라서 fallback 제거와 함께 과금 전 동기 preflight 또는 과금/이동 전 명확한 완전성 검사가 필요하다.

`waiting` 중복 의미는 2026-06-17 `6e98b153`에서 오래 걸리는 Shortform asset/manifest 준비를 HTTP 요청 밖 비동기로 보내 job을 즉시 보관함에 노출하기 위해 도입됐다. 당시 기존 job enum/UI/API를 넓히지 않고 예약과 실제 queue 대기를 같은 상태로 재사용한 것으로 코드 이력상 보인다. 현재는 `render_prepare_pending`, `queue.contains()` 같은 보조 판정으로 retry/reorder를 구분하므로 상태 중복만으로 확인된 즉시 오류는 없지만, 보조 필드 누락·stale 값이면 재시도가 잘못된 경로를 타고, 과금 취소 시점·복구 timeout·queue 위치·운영 지표가 status만으로 판정되지 않는 실질적 위험이 있다. 통합 설계에서는 `preparing/queued`를 별도 phase로 영속화하는 안을 검토한다.

사용자는 보조 `phase`를 추가하는 과도기안 대신 status enum 자체를 `preparing | queued | starting | running | completed | failed | cancelled`로 바로 확장하기로 결정했다. 신규 코드는 `render_prepare_pending`·payload 유무·queue membership을 phase의 정본으로 사용하지 않고, job store v2 migration이 옛 `waiting`만 한 번 판정한 뒤 해당 compatibility field를 제거한다. 상세 transition/invariant/preflight 수용 기준은 `../implementation/2026-09-16-job-status-and-shortform-render-preflight-design.md`에 기록했다. 이는 구현·병합 승인이 아니다.

위의 "옛 `waiting` 판정"은 2026-09-17 사용자 결정으로 철회했다. 옛 개발 빌드의 active queue를 새 빌드에서 이어받을 필요가 없으므로 `render_prepare_pending`이나 payload로 과거 preparing/queued를 구분하지 않는다. 기존 terminal 작업 이력만 보존하고, 업데이트 시 남은 `waiting | starting | running`은 새 `failed` 이력으로 만들지 않고 v2 store에서 제거한다. 업데이트 전 active job 0건 확인을 rollout precondition으로 두며, v2 rewrite에서 옛 params 키를 제거한다.

재시작 자동 재개 설명에서 "로그인 토큰을 추가 저장해야 한다"고 단정한 표현은 정정했다. 자동 재개도 기존 암호화 로그인 세션이 복원된 뒤 현재 토큰을 전달받아 수행할 수 있으며 job 파일에 토큰을 넣을 필요는 없다. 핵심 정책은 디스크의 `queued`와 사라진 in-memory queue를 방치하지 않는 것이다. 아래 사용자 결정에 따라 현 통합에서는 자동 재구성하지 않고 interruption 실패·정리 뒤 명시적 재시도로 끝낸다.

2026-09-17 사용자는 현 통합의 재시작 정책을 권장안대로 확정했다. 앱 재시작 시 진행 중이던 신규 `preparing | queued | starting | running` job은 자동 재개하지 않고 `failed` interruption으로 종결하며, 연결된 operation을 fail/refund 정리한 뒤 사용자가 새 견적·확인을 거쳐 재시도한다. job 파일에 로그인 토큰을 추가 저장하지 않는다.

2026-09-17 전체 reserve 경로를 다시 검색한 결과 `render_prepare_pending` 준비 미완 재시도 문제는 Shortform과 Variation만의 범위가 아니었다. 댓글 오버레이와 영상 랭킹도 `reserve -> submitReserved`를 사용하고 준비 중 flag를 저장하지만 `RenderJobPreparerRegistry`에는 Variation만 등록돼 있다. 두 무료 기능도 준비 중 실패 후 공통 retry에서 `RenderPrepareIncompleteError`가 날 수 있으므로, status enum·preparation callback·취소·재시도 개편은 Shortform/Variation/댓글 오버레이/영상 랭킹 네 렌더 경로를 포함한다. billing coordinator는 유료 여섯 operation에만 적용한다.

재시작 정책에는 안전조건이 필요하다. `starting/running`에서 앱이 종료됐을 때 별도 프로세스나 외부 실행이 늦게 성공할 가능성이 있는 기능은 먼저 실행 중단 또는 결과 evidence를 확인한다. 결과가 모호하면 성공 결과와 환급이 함께 남지 않도록 즉시 자동 환급하지 않고 Admin recovery로 보낸다.

Shortform URL/paste/prompt는 이미 같은 Angular component/store와 Nest workflow/orchestrator를 공유하고 source mode만 분기한다. 현 규모에서 세 Strategy 클래스를 추가하는 것은 사용자 동작을 바꾸지 않고 간접계층만 늘릴 가능성이 크므로 통합 필수 리팩터링으로 삼지 않는다. mode별 plugin/operation identity는 중앙 descriptor/map 또는 현재의 작은 resolver로 유지하고, 실제 공통화 우선순위는 `BillableJobAttempt`·terminal finalizer·retry 수명주기다.

사용자는 이 판단을 명시적으로 문서화하도록 요청했다. URL/paste/prompt를 세 상속/Strategy 구현으로 분리하지 않는 결정, 세 plugin/operation identity는 유지하는 결정, 실제 우선순위가 billing attempt/finalizer/retry라는 내용을 위 설계 문서에도 고정했다.

### `clipper_docs` 대조와 Admin recovery 이력

`/Users/jina/project/adlight/clipper_docs`의 최신 `main=c0afb2d70e20ca6fde69df4d3ec3b62997b08baf`를 확인했다. 과금 관련 정리는 대부분 2026-07-13 기준 QA 문서다. 당시 문서는 Shortform/Dance/Dialog의 공용 확인창, Variation의 확인창 없는 옛 `renderBillable` 및 독립 부분 `refund()` 모델을 설명한다. 현재 Variation v2와 formal-PG의 `fail -> 정확한 원차감 환급` 계약보다 오래됐고, 재시도 재견적·재과금이나 예약/실행 차감 시점의 제품 결정은 기록하지 않는다. 현재 Admin operation recovery의 설계·의사결정 기록도 `clipper_docs`에는 없다.

실제 코드 이력에서는 Web API `36464a5`와 Admin `bef01e3`(2026-08-12)이 장기 `running` operation 수동 recovery를 추가했다. 조회만으로 상태·크레딧을 바꾸지 않고, 운영자가 공급자 콘솔·저장 결과 등 증거를 확인해 성공 또는 실패·정확환급을 확정하며 사유·request key를 감사 기록으로 남긴다. 다음날 `a45416d`/`0f2746d`가 영속 evidence가 없으면 확정을 막고 결제지급 복구와 operation 복구를 분리했으며, `704cef2`가 동시 replay/refund 직렬화를 강화했다. Shortform watcher·operation billing은 그 전에 이미 코드에 있었지만, 이 이력만으로 recovery 구현자가 그 watcher의 프로세스 종료 문제를 특정해 알고 있었다고 단정할 수 없다. 확인되는 결정은 **시간만으로 자동 성공·환급하지 않고, 불확실한 결과는 증거를 본 사람이 확정한다**는 것이다. 자동복구가 기술적으로 불가능하거나 공수 때문에 포기했다는 기록은 발견하지 못했다.

커밋 author는 `metabuzz-jinahan <jinahan@metabuzz.co.kr>`로 기록돼 있지만 에이전트 작업도 저장소 Git identity를 상속할 수 있으므로 실제 작업한 팀원을 식별하는 근거로 쓰지 않는다. `clipper_docs` 문서 작성자와 recovery 구현자를 연결해 추정하지 않는다.

### 자동 reconciliation과 operation start 멱등성

과금 operation 자동 reconciliation은 현재 없다. Nest 부팅 때 로컬 active job을 interrupted로 바꾸는 코드는 있지만 연결된 Web API operation을 성공/실패·환급으로 종결하지 않는다. Shortform의 detached in-memory watcher가 앱 종료 때 사라지는 것이 가장 직접적인 사례지만, Dance/Dialog도 프로세스가 try/finally 중간에 죽으면 종결 호출이 실행되지 않고, 모든 기능은 `succeed/fail` 네트워크 호출 실패 시 `running`이 남을 수 있다. Variation 격리 수정도 terminal 연결을 보완했을 뿐 재시작 대조는 아직 구현하지 않았다.

formal-PG와 최신 dev 모두 operation start 요청 DTO/DB에는 한 logical attempt를 식별하는 client idempotency key와 유일 제약이 없다. formal-PG `start()`는 요청마다 새 run을 만들고 차감한다. evidence의 `(operation_run_id, kind, reference)` 유일성은 한 run 내부 중복만 막으므로 같은 job reference로 여러 run이 생기는 것을 막지 못한다. Desktop HTTP client는 timeout/network 실패를 자동 재전송하지 않고 401 token refresh 때만 1회 재요청하므로 현재 상시 중복차감이 관측됐다는 뜻은 아니다. 하지만 첫 요청이 commit된 뒤 응답만 유실되고 같은 logical start가 다시 전송되면 서버가 이를 구분할 수 없어 중복차감이 가능한 구조다.

안전성 방향은 (1) job/attempt 기반 안정적 key와 Web API DB 유일성, (2) 기존 사용자 PC의 로컬 job 저장소와 분리한 billing attempt 저장소에 operation ID·최종화 대기 상태 같은 최소 참조만 보존, (3) 기능별로 흩어진 terminal 종결을 공통 finalizer로 모으기, (4) 앱 시작 때 자동 판정 가능한 로컬 terminal 결과만 `running` operation과 대조하고 모호한 interrupted 결과는 현재 Admin 수동 recovery로 넘기기다. 사용자는 이 원칙과 실패한 terminal 보고를 로컬에 원자적으로 남겨 네트워크 복구 후 재전송하는 durable outbox를 **이번 통합 범위에 포함**하기로 결정했다. 이것은 병합 승인은 아니다. 서버에는 프로젝트·미디어·전체 job 내용을 저장하지 않고 금융 원장에 필요한 operation·멱등키·불투명한 job/attempt 참조만 둔다. Shortform Director에는 로컬 manifest/checkpoint를 읽어 부팅 때 작업을 복구하는 별도 구현 예가 있으나 operation billing에는 연결돼 있지 않다.

자동 reconciliation은 사용자 삭제를 실패로 해석해서는 안 된다. 최신 dev의 보관함 다중 삭제는 terminal job만 허용하고, Variation 프로젝트 다중 삭제는 active render를 제외하지만, 삭제 시 job/project 레코드와 파일이 실제로 제거될 수 있다. 따라서 과금 연결 metadata는 삭제 가능한 콘텐츠와 분리하거나 `deletedByUserAt`·기존 terminal 상태·`billingFinalized` 같은 최소 tombstone을 보존해야 한다. 이미 terminal·과금종결된 항목 삭제는 재환급하지 않고, active 항목은 기존 취소→terminal 확정이 먼저여야 한다.

공통 위험도 확인했다. Desktop 프로세스가 차감 뒤 종료되거나 Web API의 `succeed/fail` 호출이 실패하면 operation이 `running`으로 남을 수 있다. 현재 Web API/Admin에는 evidence를 보고 운영자가 성공 또는 실패·환급으로 정리하는 수동 recovery만 있고 자동 reconciliation은 없다. operation `start`에도 클라이언트 idempotency key가 없어, 응답 유실 뒤 시작 요청을 재전송하면 중복 operation·중복 차감 가능성을 배제할 수 없다.

2026-09-17 사용자는 병합안 전 남아 있던 두 제품 정책을 다음과 같이 확정했다:

1. 보관함/프로젝트의 `실패`·`취소됨` 카드에서 `다시 시도`를 누르거나 Variation 결과 카드에서 `다시 만들기`를 누르면, 환급된 원시도와 분리된 새 작업으로 현재 설정을 다시 견적하고 확인창 승인 뒤 새 attempt·operation·차감을 만든다.
2. Shortform/Variation도 모든 preflight 통과와 사용자 금액 확인 직후 차감한다. 준비·queue 대기·실행 중 어느 단계에서든 실패·취소되면 공통 finalizer로 전액 환급한다.

전체 확정·미결정 목록과 migration 실제 영향은 [2026-09-17 통합 전 결정·누락 감사](../../implementation/2026-09-17-pre-merge-decisions-and-gap-audit.md)를 정본으로 사용한다.

저장소별 최신 dev/integration SHA, 정확한 범위, semantic overlap, Electron 앱 이름 2단계 병합, 권장 worktree/branch는 [2026-09-17 저장소별 병합 제안](../../implementation/2026-09-17-repository-integration-merge-proposal.md)에 정리했다. Desktop/Web API 후속 안전성 구현은 [Desktop PG 안전성 구현 계획](../../implementation/2026-09-17-desktop-pg-safety-implementation-plan.md), DB 검증·전환 rehearsal은 [로컬 PG migration 검증 계획](../../implementation/2026-09-17-local-pg-migration-validation-plan.md)을 따른다. 세 문서 모두 계획이며 현재 병합 승인을 뜻하지 않는다.

다음은 제품 과금 정책과 별도로 필요한 안전성 목표다. attempt 저장·outbox 자체는 이번 통합 포함이 확정됐다. 미종결·전송대기·모호 항목은 해결될 때까지 보존하고 서버 종결 확인 항목·tombstone은 확인 시점부터 30일 뒤 정리한다. 구체적인 저장 위치·구조는 병합안의 설계 검토 후 승인받는다:

- 동일한 한 번의 job attempt에서 operation start HTTP 응답이 유실돼 재전송되더라도 한 번만 차감되도록 안정적인 idempotency key와 DB 유일성을 둔다. 사용자가 누르는 `다시 시도`는 별도의 새 attempt라 새 key를 쓴다.
- job/attempt와 operation을 안전하게 재연결할 방법을 설계한다. 우선안은 사용자 PC의 기존 로컬 job 저장소에 operation ID와 미전송 종결 상태 같은 최소 metadata만 두고, 서버에는 금융 원장·멱등키·불투명한 참조만 두는 것이다. 앱 시작·네트워크 복구 때 완료 산출물이나 명시적 실패처럼 자동 판정 가능한 건만 종결하고, 단순 `interrupted`처럼 결과가 모호하면 관리자 수동 recovery를 마지막 안전망으로 쓴다.
- 모든 사용자 재시도 경로에 새 견적·과금 확인창을 붙이고, 차감·환급 직후 잔액과 원장을 갱신한다.
- terminal 명령은 전송 전에 durable outbox에 기록하고, 앱 재시작·네트워크 복구 후 같은 run에 재전송한다. 미종결·전송대기·모호 항목은 시간만으로 지우지 않는다.
- Electron/Nest/Python/ffmpeg의 실제 parent-child tree와 종료 신호를 플랫폼별로 검증한다. 현재 정적 감사상 최상위 Python plugin과 Windows owned tree는 종료 관리가 있으나, Nest utility process와 Nest/Python 내부 ffmpeg는 모든 경로에서 공통 shutdown 소유권이 증명되지 않았다.
- Angular의 옛 license adapter는 사용자의 기존 결정대로 명시적으로 제거한다. `CurrentLicenseSummary/currentLicense/_license`와 도달 불가능한 queued/expired 이용권 필드를 남기지 않고 access·credit 원형 모델로 정리한다. 이 정리는 PG 병합만으로 자동 발생하지 않는다.

이번 개발서버 정식 PG 전환은 출시 전 통합이므로 과거 개발판 데스크톱의 API 계약까지 지원하지 않는다. 새 통합 데스크톱·웹을 같은 계약으로 검증하고, 옛 개발판 사용자는 새 빌드 설치와 1회 재로그인을 전제로 한다. 출시 후 `1.2.1 → 1.2.2` 같은 호환 정책·API versioning은 별도 후속 설계다. 후속 정본은 [출시 후 호환 정책 TODO](../../todos/2026-09-16-post-launch-desktop-api-compatibility.md)다. 사용자 지시에 따라 `.codex`로 이동했으며 `clipper_docs`에는 남기지 않는다. 사용자·로그인 보존 및 로컬 프로젝트 보존은 별개의 요구이며, 서버의 개발 금융·작업 이력 정리 범위는 최신 전환 승인 정책을 따른다.

## 격리 수정 검증

- Nest `npm run build`: PASS. access/credit·Variation·job terminal·operation client·render retry 대상 113 PASS, 0 FAIL.
- Nest 전체 suite는 샌드박스 밖에서 실행했으나 격리 worktree에 sibling Python 번들 폰트와 `.env.packaged`가 없어 폰트/패키징 관련 실패가 있었고, 별도의 기존 shortform 후보 테스트 1건도 실패했다. 수정 대상 suite는 별도로 전부 통과했다.
- Web API `npm run build`: PASS. OpenAPI contract 60 PASS, 0 FAIL.
- Electron 상세 검증은 앱 이름 카드 참조. 전체 943개 중 942 PASS, sibling Angular renderer fixture 부재 1 FAIL.

## 로컬 PG 검증 체크리스트

다음 항목은 구현·병합 승인 뒤 별도 로컬 DB에서 모두 검증하며, 일부만 통과한 상태를 전체 검증 완료로 기록하지 않는다.

- access 없음/활성/만료와 크레딧 0/충분/추가구매만 잔존 조합별 조회·작업 시작 허용 결과
- 모든 현행 tier에서 동일 플러그인 접근, `entitlement_mode=all`, 빈 allowlist가 기능을 막지 않는지
- 견적 표시 → 사용자 확인 → 실제 차감액 일치, 여러 영상 작업의 부분 시작 방지와 실패 시 원복
- 준비 단계 실패·대기/실행 중 사용자 취소·큐 제출 실패의 정확한 환급과 중복 fail idempotency
- 큐 제출 성공 뒤 비동기 렌더 성공 시 차감 확정, 실패 시 환급, 실패 재시도 시 새 operation 재과금
- Variation 작업 직후, 프로젝트/보관함 이동 직후, 설정 화면 재진입·명시적 refresh 뒤 잔액과 원장 즉시 갱신
- 혼합 batch의 일부 실패, 중복 토스트·중복 원장·중복 환급이 없는지
- 차감/환급 원장의 작업명·사유·금액·operation evidence와 리소스 소유권 검증
- 새 통합판 계약 기준 잘못된 access/credit 원격 JSON과 누락·추가 필드의 실패 방식. 출시 전 옛 데스크톱용 호환 변환은 만들지 않음
- 기존 개발 사용자·로그인·프로젝트·작업 이력을 보존한 별도 DB migration 및 dump 복원 rollback 리허설

그다음 main반영/배포 여부 결정. 서버 배포는 사용자 실행. 실제ML/Build5 HOLD 유지. 테스트·빌드·배포 재개 범위는 그때 사용자 지시를 확인한다.

## 제외한 과거 작업

사용자 결정대로 오래된 main 고유코드, 별도 feature/toss-payments-pg-integration, 밈·대사하이라이트 branch를 추가병합하지 않았다. 이를 자동 복원하거나 새 통합 범위로 넣지 않는다.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
