# 두 세션 감사 및 외부 취소 자동 후처리 결과

> 후속 갱신(2026-11-04): 아래 감사 시점에 미커밋으로 남아 있던 가격·크레딧·무료체험 유효기간 변경도 이후 dev에 반영했다. 최신 결과는 [가격·유효기간 통합 기록](04-catalog-price-trial-validity-integration.md)을 따른다. 아래의 미커밋 표기는 이전 시점 기록이다.

2026-11-04 KST. 구현·전체 테스트·독립 검토·원격 dev 반영을 완료했다. 운영 배포 및 실제 Toss 외부 취소 후처리 E2E를 완료했다는 뜻은 아니다.

## 전체 작업 상태

| 항목 | 현재 상태 |
| --- | --- |
| 고객 신청·철회, 관리자 조건 확인·승인·반려, 실패 후속조치 | 기존 두 세션 작업이 이미 dev에 포함됨. 고객 신청은 여전히 관리자 승인 후에만 토스 취소를 요청함. |
| 환불 관리 3탭, 결제 운영·상품 정책 메뉴 통합, 공통 검색·페이지네이션·건수·모달·팝오버 | 기존 작업이 이미 dev에 포함됨. |
| 앱 미완료 작업의 원 지급분 반환·재시도·강제 종료·오프라인 복구 | 기존 API/앱 커밋이 최신 dev에 포함됨. 결제 취소 후 혜택 회수와 별개의 기능임. |
| 외부 취소 관찰·웹훅·스캔·거래 매칭·기존 내부 환불 연결 | 기존 dev에 포함됨. |
| 내부 환불 건 없는 외부 전액 취소의 혜택 정리 | 이번에 구현·검증하고 API/Admin dev에 반영함. |
| 새 가격·월 지급 크레딧 및 무료체험 유효일수 편집 | 원래 PG 세션의 미커밋 변경으로 보존됨. 최신 dev에 동등 구현 없음. 이번 기능과 섞지 않음. |
| 실제 TEST 자동갱신 harness·로컬 계획 문서 | 기존 미커밋 상태 유지. .env·전용 포트·빌드 산출물 제외. |
| 최종 환불 정책/법적 예외·연락 경로 문구, 공유 환경 배포·데이터 초기화·종합 PG 검증 | 이번 완료 범위가 아님. |

## 새 기능

- 토스를 다시 조회·검증한 뒤 해당 결제의 남은 크레딧만 회수한다. 무료체험·프로모션·수동 지급·다른 결제의 크레딧은 보존한다.
- 귀속이 명확한 현재 구독 이용권과 다음 자동결제·연간 월별 지급을 중단한다. 과거 결제 취소로 이후 유효한 기간을 종료하지 않는다.
- 이미 사용한 분량은 음수나 다른 지급분 차감으로 정산하지 않고 운영자 확인 대상으로 남긴다. 남은 해당 크레딧은 회수한다. 부분 취소·업그레이드/복수 결제 등 모호한 귀속도 사유를 표시한다.
- 영속 작업·lease·멱등 원장으로 중복 이벤트, DB 실패, 재시작·재시도를 처리한다. 외부 후처리에서 토스 결제취소 API를 다시 보내지 않는다. 기존 내부 환불이 있으면 그 엔진이 효과를 소유한다.
- 모든 대상 결제의 외부 정리가 완료된 대기 신청은 시스템 상태 `resolved_externally`로 종료한다. 고객은 완료로, 관리자는 ‘외부 취소 완료’로 보며 가짜 승인·반려를 기록하지 않는다.
- 관리자 ‘결제 운영 → 결제 상태 점검 → 외부 취소 조사’에 ‘내부 처리’ 상태·상세 툴팁, 재확인 후 내부 재시도를 추가했다. ‘환불 관리 → 고객 환불 신청’에는 ‘외부 취소 완료’ 탭/건수가 있다.

## 커밋·보존·검증

| 저장소 | 원격 dev 커밋 | 전체 테스트한 tree |
| --- | --- | --- |
| API | `91afe80e19350516e79a4562b197f870536da0e5` | `7fa77c97986503d7f8375d7cb328b62a43776ed7` |
| Admin | `b68e415bcfeb677417b3d65c8ef9985c2ae2669c` | `b84fda9315bf980284d017dd19798d0b8de29008` |

정상 fast-forward push 후 `git ls-remote`로 확인했다. 커밋과 테스트 tree가 같으며 API 1,414개/Admin 752개 작업 파일의 커밋 전후 해시가 같다. 임시 선별 인덱스를 사용했고 원래 미커밋 정책·환경 파일은 그대로 남았다. 다른 작업트리 checkout/reset은 하지 않았다.

기존 세션 커밋도 최신 dev의 조상임을 재확인했다: Client `e996b95`(원격 `dacc90d`), Electron `febb167`(원격 `6831d8d`), 앱 Angular `7b559706`, Nest `a5f8db6f`. 이 저장소 소스는 이번 작업에서 바꾸지 않았다.

- API: 490개 suite / **5,392개 test 통과**, 9개 suite/86개 test skip, snapshot 5개 통과. 빌드 통과.
- 새 외부 효과 테스트: **실제 격리 PostgreSQL 35개 사례**, fake Toss. 구독/충전/연간/과거, 사용·부분·귀속, 중복·rollback·lease, 일반 환불 공존, 지급/갱신 경합, 지연 반환, 요청 종료/복구/동시 결정 포함.
- Admin: **2,862개 test**, 빌드, 색상 검사 통과. 기존 initial bundle 경고는 있으나 오류 기준 미만.
- 독립 Sol 검토에서 API 3건과 Admin 경쟁 상황 안내 1건을 보완하고 재검토 통과. 최종 49파일 전체 통합 검토 Spec PASS / Quality PASS / merge 가능. Astra 미사용.
- 전용 admin DB에 `ExternalCancellationEffects1793665200000`만 새로 적용. API3311 health에서 user/admin/release DB 정상. 외부 취소/효과 작업 0건이므로 실제 결제 권리를 바꾼 로컬 사례는 없음. Admin4204/Client4203과 기존 설정 보존.
- **미실행:** 실제 Toss TEST 신규 외부 취소 후처리 E2E, 기존 내부 환불 연결 장애 복구 E2E, 운영/shared DB 적용·backfill·rollback, 실제 기기별 수동 시각·접근성 검증. 단위/DB 검증을 이것들의 완료로 표현하지 않는다.

증거는 `/private/tmp/external-cancellation-implementation-20261104/`의 API/Admin `verified-v2-full-tests.log`, `verified-v2-build.log`, `commit-proof.json`, `whole-review-package.diff`. 이전 세션 감사는 `/private/tmp/pg-session-audit-20261104.md` 및 JSON.

## Rulings I made

실행 ledger의 명시적 판단 5건을 발생 순서대로 모두 보존한다. 자동 정리 정책 자체는 사용자가 승인했다.

1. 원래 정책·가격 hunk를 정확히 보존하고 새 기능만 검증·커밋했다. 잘못된 판단이면 함께 배포해야 할 정책이 누락될 수 있어 미커밋 잔여를 명시했다.
2. 설계 검토에 따라 지급 경합 차단, 연간 주문 없는 grant의 좁은 귀속, 명시적 금융/관찰/내부 환불 lock 순서, 진행 중 갱신 차단, 고객 외부 상태 요약을 포함했다. 잘못되면 권리 오회수·교착·복구 지연·잘못된 완료 표시가 생길 수 있어 PostgreSQL 경합·귀속 회귀와 전체 검토를 거쳤다.
3. 완료한 효과는 미해결 경고에서 제외하되 취소 사실·무관한 다른 점검 사유는 보존했다. 잘못되면 필요한 경고가 누락될 수 있어 상태별 조회를 검증했다.
4. 모든 원래 신청 결제의 외부 효과가 완료된 경우만 시스템 상태로 종료하고 금융 lock 밖의 요청 행 transaction/주기 복구를 사용했다. 잘못되면 신청 오종료·복구 지연이 가능해 multiorder·소유권·중단·동시 승인 회귀를 포함했다.
5. API 소스/계약 동결 후 전체 검증 중 Admin 개발을 병행하되 모든 gate 통과 전 push를 금지했다. 잘못된 계약이 뒤늦게 나오면 UI 재작업 비용이 생기지만 배포는 차단되는 순서였다. 최종 양쪽 검증/통합 검토 후 push했다.

## 최종 독립 검토 원문

# Whole implementation independent review

Reviewed 2026-11-04 against the binding external-cancellation design and implementation plan. Reviewer: senior reviewer, Sol. Review was performed personally in several passes, without helpers/subagents or duplicate test runs. Source, index, HEAD, branches, processes and financial records were not changed; this report is the sole review write.

## Exact scope

| Repository | Base | Reviewed commit | Reviewed/tested tree |
| --- | --- | --- | --- |
| API | `755010493ff27e04c1c3a152dadc4f9a0d344667` | `91afe80e19350516e79a4562b197f870536da0e5` | `7fa77c97986503d7f8375d7cb328b62a43776ed7` |
| Admin | `e079df729e15383ae29ff4e80503f3440522da9b` | `b68e415bcfeb677417b3d65c8ef9985c2ae2669c` | `b84fda9315bf980284d017dd19798d0b8de29008` |

Read the complete 35-file API and 14-file Admin diffs in `/private/tmp/external-cancellation-implementation-20261104/whole-review-package.diff`, the entire new worker/repository/resolution/migration/PG-test sources, and the surrounding fulfillment, renewal, ordinary effects, credit-return, monthly-grant, eligibility/history and customer/Admin presentation paths relevant to integration. Used immutable `api/verified-source-v2` and `admin/verified-source-v2`, not dirty working-file overlays. Independently compared every changed file in both commits with those selected-source directories: 35/35 API and 14/14 Admin files are byte-identical. Exact-range `git diff --check` returned exit 0 for both repositories.

Read the ledger and both original/scoped task reviews. Their findings informed regression inspection but did not replace whole-range review. No parked or deferred findings are carried forward.

## Strengths and requirement assessment

- Provider evidence and benefit effects remain separate. Correlation and cancellation identities/totals are revalidated before rights writes; observation persists money evidence and the order-scoped job atomically. The worker only queries Toss and hands off existing ordinary internal effects; no second provider cancellation is introduced.
- The lease token, expired-lease recovery, transaction rollback and deterministic per-grant ledger reference provide durable, idempotent recovery. Observation uses order → evidence/job locking without financial advisory locks. Financial effects and fulfillment hold subscription → user → order ordering through rights changes. Ordinary-case handoff/FK attribution occurs before financial advisory locks.
- Credit selection is limited to the same user, correct source and affected payment. Null-order subscription grants additionally require bounded benefit periods, one base-payment owner and no overlapping upgrade. Explicitly different payment IDs, unrelated paid/free/promotion/manual grants and later periods are preserved. Used credits remain a review reason without debt; delayed operation refunds retain revoked status and cannot become spendable.
- Current monthly/annual access and renewal end only through the unambiguous contract path. Old periods preserve current entitlement/renewal. Partial, upgrade, ambiguous and mixed-payment cases retain readable review states. Existing in-flight money remains reconcilable; paid/unfulfilled adjacent renewal/upgrade orders cannot disappear from the review outcome. Renewal preparation, recovery/failure and late fulfillment respect the external fence, and annual monthly issuance consults it under the shared user lock.
- An ordinary refund retains ownership of its effects and is not replaced by a synthetic administrator/customer refund. External investigation completion waits for its money/internal completion and exact provider-event linkage.
- Customer requests close in a separate request-row transaction only for a nonempty, same-user snapshot whose every payment is fully canceled with completed, externally owned effects. System evidence and the `resolved_externally` raw state are persisted, with public `completed` plus `resolutionSource`. Repair, SKIP LOCKED and decision/withdrawal checks cover crash and concurrent action paths. Ordinary customer refund requests still require operator approval.
- Money/history and unresolved warnings remain distinct from cleanup. Pending/retry/review states cannot project completed history; resolved cleanup leaves warning lists/counts while factual cancellation markers and unrelated reconciliation warnings remain. Existing customer copy handles full/partial/processing/attention projections. Full-refund eligibility is checked before the legacy external-cancellation support reason, so completed cleanup does not require that obsolete support message.
- Admin matches the nullable effects contract, preserves unknown/legacy fallbacks, and uses one compact column with readable tooltip details. Recheck keeps its permission, duplicate-action guard and refresh lifecycle. Raw external-resolution filtering/counts, completed labels, absent decision controls, mocks and both approve/reject response races agree with API behavior.

## Issues

**P0: none. P1: none. P2: none found.** No actionable trigger/file/line finding remains in the reviewed commits.

**Optional nits: none.**

## Verification consumed

No full or focused suites were rerun by this reviewer. Existing results were read and tied to the exact committed sources by the independent byte comparisons above.

- API `verified-v2-full-tests.log`: 490 suites passed, 9 skipped; **5,392 tests passed, 86 skipped; 5 snapshots passed**. API selected-source build succeeded per integration execution evidence and its build log.
- API `task1-review1-final-focused.log`: **7 suites / 400 tests passed**. The fully read external-effects spec supplies 35 fake-Toss/disposable-real-PostgreSQL cases, including duplicate workers, partial → full, used credits/delayed returns, rollback/expired leases, current/annual/historical contracts, narrow attribution, ordinary ownership, both fulfillment orderings, delayed paid/failed/uncertain/network renewal results, paid-before-fulfillment gaps and customer-request recovery/races. The isolated database helper applies real migrations with synchronization disabled.
- Admin `verified-v2-full-tests.log`: **2,862 tests succeeded**. Selected-source build completed successfully; `check-colors.log` reports **zero direct colors**. The existing initial-bundle budget warning remains a warning, not a build failure.
- Scoped regression logs/reviews confirm the earlier three API findings and one integrated Admin action-response finding were fixed. Current sources and the added assertions were independently inspected here.
- Fresh review checks: exact-range diff checks passed; all 49 changed committed files matched tested immutable snapshots. No unverified source overlay was used to infer a passing result.

## Declined to judge

- **Real Toss end-to-end external benefit cleanup:** fake Toss plus isolated real PostgreSQL is the authorized implementation evidence; no actual provider/financial action was performed in this read-only review. A real Toss cleanup E2E is not claimed.
- **Production/shared-database deployment, production backfill execution and operational rollback execution:** outside this review's implementation gate; the disclosed dedicated local migration/health evidence does not prove production rollout. No production deployment is claimed.
- **Excluded parent price, signup-validity, environment, packaged-artifact and unrelated worktree changes:** outside both exact commit ranges and explicitly excluded by the plan; their correctness was not graded.
- **Manual physical-viewport, touch and screen-reader verification:** no browser/device session was run. Angular rendering, actual Material tooltip-overlay, accessible-detail and row-stability evidence was reviewed; manual cross-device visual verification is not claimed.

## Assessment

**Spec: PASS. Quality: PASS. Ready to merge: Yes.**

The reviewed commits satisfy the approved automatic-full-cancellation policy and its conservative exception paths, including recovery and concurrent lifecycle boundaries. No further code changes are requested by this review. This is a merge-readiness verdict for these two exact commits; it is not a real Toss E2E or production-deployment claim.
