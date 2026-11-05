# 가격·월 크레딧·무료체험 유효기간 변경 통합 결과

> 후속 갱신(2026-11-04): 사용자 요청으로 유효기간 상한을365일로 수정·dev반영했다. 아래1~3650일은변경전시점기록이다. [365일수정결과](04-trial-validity-365-limit.md)를따른다.

2026-11-04 KST. 사용자 요청으로 최신 원격 dev 중복 여부를 확인한 뒤 기존 미커밋 구현을 검증·커밋·원격 dev 반영했다. 운영 배포/공유 DB 변경은 수행하지 않았다.

## 변경 내용

| 요금제 | 월 결제액 | 연 결제액 | 매월 지급 크레딧 | 연간 할인 표시 |
| --- | ---: | ---: | ---: | ---: |
| Basic | 8,900원 | 90,000원 | 1,500 | 16% |
| Pro | 26,900원 | 264,000원 | 5,000 | 18% |
| Business | 99,000원 | 948,000원 | 20,000 | 20% |

API의 현재 상품 카탈로그를 갱신하는 마이그레이션과 Admin/Client 목 데이터·기대값을 일치시켰다. 기존 결제·구독 계약·지급 크레딧을 소급 변경하지 않는다. 클라이언트 가입 혜택 목 데이터 200→400은 이미 실제 기본 정책인 400과 맞추는 변경이며 새 운영 지급량 인상이 아니다.

관리자 상품 화면의 가입 크레딧 유효일수를 1~3650일 정수로 편집할 수 있다. API 검증·저장·감사, 관리자 입력 오류·포커스·확인·저장·되돌리기, 목 API 검증을 포함한다. 기본 30일을 바꾸는 마이그레이션은 없고 정책을 편집한 뒤 새로 지급하는 분부터 반영한다. 기존 지급분 만료일과 기존 가입 이력은 유지한다.

## 중복 여부와 통합

- 시작 시 최신 원격 API91afe80/Adminb68e415에는 가격 변경 마이그레이션과 validityDays PATCH/입력 편집이 없었다. Clientdacc90d도 이전 카탈로그 목 값이었다. 동일 구현의 선행 병합은 없었다.
- Client에 먼저 최신 dev4커밋을 fast-forward했다. 다른 세션의 결제수단 인증창 정리·미결제 구독 초안 숨김을 보존했다. 원래 로컬 목/환경 파일 해시도 유지했다.
- API13/Admin8/Client2개 파일만 선별했다. API datasource의 무관한 Dance import 포맷 변경, 실제 Toss 자동갱신 harness3개, 관리자 계획문서4개, local환경2개, .env·빌드 산출물은 제외했다.
- 모든 기존 미커밋 파일의 내용이 보존됐다. 실제 index는 commit 후 read-tree만 했고 작업 파일을 덮어쓰지 않았다.

| 저장소 | 원격 dev 커밋 | 검증된 tree |
| --- | --- | --- |
| api | `fa169401ae80c27f399ce12cfc9fe38ed80279df` | `7902bd062e3052cb34c3ab088c434089f0ea12b9` |
| admin | `442d66fb4a385728c67b44c4c3f8dc6d3237e24b` | `53c1ad80f40f6ba840e671102135b4da3c53f15f` |
| client | `aabcf3d4aa33a7da0795e7b141aee31da3ac2b71` | `6ae6e9bb8ef6f3dfa07af911cbff3fd78bbec265` |

정상 fast-forward push 뒤 원격 `git ls-remote --heads origin dev`로 위 SHA를 확인했다. 다른 세션의 로컬 dev 브랜치/작업트리는 변경하지 않았다.

## 검증

- API 전체: 491suite/5400test 통과, 9suite/86test skip, snapshot5통과. 빌드 성공.
- Admin 전체: 2868test 통과, 빌드 성공, 직접 색0개.
- Client 전체: 635test 통과, 빌드 성공.
- 독립 Sol 검토: Spec PASS / Quality PASS, P0/P1/P2 및 선택적 지적 없음. 선택한23파일이 검증 tree와 일치함을 독립 비교했다. Astra 미사용.
- 실제 격리 PostgreSQL: 기존 전체 마이그레이션을52까지 적용하되 가격42만 제외한 DB에 기존 일부 사용 무료체험 grant를 추가했다. 이후42를 도입해 TypeORM이 해당 migration만 실행함을 확인했다. 3tier/6상품 가격·할인 일치, 이전 grant행 JSON 불변, 실제 repository의 validityDays14 저장 후에도 기존 grant불변, 재실행migration0개를 확인했다. 생성한 시험 DB는 삭제했으며 공유·운영 DB는 건드리지 않았다.
- Angular CLI의 `--port`는 지원하지 않아 첫 명령은 실행 전 인자 오류였다. 결과를 별도 보존하고 지원 옵션으로 Admin→Client 순차 실행했다. 위 수치는 완료된 정상 전체 실행 결과다.
- 기존 Admin/Client 초기 번들 크기 경고가 있으나 오류 임계 미만이며 빌드는 성공했다. 운영 배포 및 실제 토스 결제는 이 작업에 포함하지 않았다.

증거: `/private/tmp/catalog-trial-integration-20261104/` 아래 각 저장소 full-tests.log/build.log/selected.json/commit-proof.json, pg-upgrade-smoke.log, independent-review.md.

## 독립 검토 원문

# Independent catalog / trial integration review

## Scope and provenance

Read-only review of the exact selected integration trees against the supplied latest-dev bases:

| Repository | Base | Reviewed tree | Selected files |
| --- | --- | --- | --- |
| API | `91afe80e19350516e79a4562b197f870536da0e5` | `7902bd062e3052cb34c3ab088c434089f0ea12b9` | 13 |
| Admin | `b68e415bcfeb677417b3d65c8ef9985c2ae2669c` | `53c1ad80f40f6ba840e671102135b4da3c53f15f` | 8 |
| Client | `dacc90dcd5b3e2cb486408baf0b1d0fdbab85ffd` | `6ae6e9bb8ef6f3dfa07af911cbff3fd78bbec265` | 2 |

Independently compared every selected `verified-source` file byte-for-byte with its Git tree blob: all 23 matched. Read the entire selected diff plus the surrounding API authorization, policy/provisioning, catalog projection, checkout, persisted subscription/renewal, Admin save-bar, and Client production pricing/mock checkout code. No checkout, index, HEAD, branch, dependency, or application source mutations; no subagents or test-suite reruns. This report is the only file created by the reviewer.

## Strengths and spec alignment

- The migration updates exactly the three current paid-tier credit allocations and six current billing-product prices. Targets are Basic 8,900 / 90,000 / 1,500, Pro 26,900 / 264,000 / 5,000, Business 99,000 / 948,000 / 20,000 (monthly KRW / annual KRW / monthly credits); configured annual percentages are 16 / 18 / 20. It does not write historical grants, orders, subscriptions, access snapshots, or the trial policy. Its explicit unsafe-down refusal avoids replacing later operator catalog edits with guessed old values.
- API validity is an optional integer in 1..3650; `ValidateIf(value !== undefined)` preserves partial patches while rejecting explicit null, and the closed validation pipe rejects unknown/immutable fields. The controller continues requiring operator authentication and merged `catalog.read` / `catalog.write` permissions. Policy update uses the existing transaction/row lock, includes validity in the audit diff, and persists it on the singleton policy.
- Existing trial participation returns before any grant creation. New participation calculates expiry from the policy at issuance and the existing signup-date convention. The added provisioner regression explicitly checks that previously issued expiry is unchanged when validity changes. Public catalog already projects the persisted policy, so production signup-benefit display follows the policy without a separate hardcoded TTL.
- Admin validity uses the existing single save-bar flow with draft/pending detection, integer bounds, inline error state, invalid-field focus, revert, confirmation facts, future-issuance explanation, success synchronization, and failure draft retention. Both its disabled state and setter/save guards honor `catalog.write` and busy state. Tier remains disabled. Mock policy validation rejects null, noninteger, out-of-range, and unknown fields before mutating state.
- Admin and Client current-catalog fixtures match the migration values. Client signup benefit 400 matches the existing production default (30-day default remains unchanged). Production price cards read catalog fields. The current mock checkout and plan-change targets derive values from the updated catalog; historical subscription, payment, receipt, retry, and access examples intentionally retain their old contract snapshots.
- Current real checkout snapshots current product/tier fields (`subscription-payments.service.ts:176-216`), while initial orders and renewals read the persisted subscription contract (`subscription-payments.service.ts:1168-1172`, `subscription-renewal.service.ts:194-235`). A current-catalog update therefore does not reprice existing contracts or rewrite the credit amount agreed in them.
- The installed TypeORM executor matches pending migrations by name and has its lower-than-last-timestamp rejection commented out (`node_modules/typeorm/migration/MigrationExecutor.js:152-162`). The consumed disposable-PostgreSQL upgrade smoke confirms that a database already through migration 52 executes exactly missing migration 42 and nothing on a second run.

## Issues

P0: none found.

P1: none found.

P2: none found.

Optional nits: none requested. No speculative refactor or unrelated historical fixture rewrite is recommended.

## Verification evidence and limits

- Consumed existing API full-suite log: **491 suites passed, 9 skipped; 5,400 tests passed, 86 skipped; 5 snapshots passed**. No failures reported in that run.
- Consumed completed Admin full-suite output: **TOTAL: 2,868 SUCCESS**, and executor reports exit 0.
- Executor confirms all three selected-source builds exited 0. Consumed Admin and Client bundle output; both have initial-bundle budget warnings (Admin 896.97 kB; Client 512.07 kB).
- Consumed `pg-upgrade-smoke.log`: **PASS**, upgrade from `1793665200000` applied exactly `UpdatePlanCatalogPrices1793664200000`, checked three tiers/six prices, old grant unchanged, validity-only patch persisted as 14, second migration run empty. Executor reports all existing migrations were applied without 42 first, the partly spent grant was compared as byte JSON after migration and actual repository policy patch, and the disposable database was dropped. No shared database was modified.
- Client full-suite execution is the only remaining gate at report time (558 / 635 successful at last observation). No test or smoke was duplicated by this reviewer.

## Declined to judge

- Production/shared-database or Toss execution: excluded by the authorized scope; this review performs no live writes or provider calls.
- Exact deployed operator catalog customizations or missing/deleted standard catalog records: no live database inspection was authorized; the requested migration targets the established standard codes already seeded by existing migrations.
- Changing production signup-credit amount or default TTL: not requested; the Client 200-to-400 fixture correction reflects the existing production 400 / 30 policy, and no production default policy changes are introduced.
- Repricing historical mock records and existing contracts: explicitly excluded; preservation is a requirement, not a consistency defect.
- Broader payment/refund functionality, excluded harness/formatting/environment changes, and unrelated pre-existing behavior: outside these selected trees and this integration's requirements.
- Independent certification of all test/build/runtime gates: execution belongs to the parent; this review uses available logs and does not treat in-progress or unobserved checks as passed.

## Verdict

**Spec: PASS.** The selected implementation matches the supplied existing intent and preserves historical contracts and trial grant expiries.

**Quality: PASS.** No actionable P0/P1/P2 defect found in the reviewed change. Ready to merge from code review, subject to the executor confirming the remaining Client full-suite result.

## 실행자 최종 확인

독립 검토 기록 시점에 진행 중이던 Client 전체 테스트는 이후 TOTAL635SUCCESS 및 exit0으로 완료했다. 세 검토 tree 그대로 커밋·원격 dev에 반영했으며 위 remote SHA를 확인했다.
