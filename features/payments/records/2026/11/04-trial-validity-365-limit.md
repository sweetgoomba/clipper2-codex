# 가입 크레딧 유효기간 상한 365일 수정

2026-11-04 KST. 사용자 명시 요청으로 최대 허용값을3650→365일로 수정하고 API/Admin 원격 dev에 반영했다.

- API DTO최대값과OpenAPI, 관리자 input max/정수 검증/안내 문구/목 API를1~365로 통일했다.
- 실제 ValidationPipe에서365허용·366거절, 관리자 DOM입력365저장·366저장차단·포커스/오류, 목 API동일경계를 검증했다.
- 기존 기본30일, 저장된 정책, 기존 크레딧 만료일·가입이력은 변경하지 않았다. DB마이그레이션·운영배포는 없다.
- TDD RED: API2실패/10성공, Admin6실패/122성공으로 기존366허용 및문서/화면불일치를 재현했다.
- 최종 전체 GREEN: API491suite/5400tests성공,9suite/86tests스킵, snapshot5성공. Admin2868성공. 양쪽빌드 및관리자직접색0검사 성공. 기존초기번들경고만있다.
- 독립Sol검토 SpecPASS/QualityPASS, P0/P1/P2지적없음. 검토시진행중인전체테스트는이후실행자가exit0완료확인했다.
- 선별tree그대로커밋했고정상fast-forward push후gitlsremote로확인했다. 원래API포맷·harness,Admin전용환경·계획문서는보존·제외했다. 로컬서버재시작이나실제데이터변경은이번작업에서하지않았다.

- api dev `197af457fc00517de11e0f89fbb7c78863ca897c` (검증tree `f3c1933617c27da82555dab9633236eb87e28c2c`)
- admin dev `13b0568df99c3e3c6f99374f329d8f9bccc7b6a7` (검증tree `0bf15057062529ac816ac78d3350ce41045fde41`)

증거: `/private/tmp/trial-validity-365-20261104/` 아래 red.log/full-tests.log/build.log,selected.json,commit-proof.json,independent-review.md.

## 독립 검토 원문

# Independent review: trial validity maximum 365 days

Spec: PASS
Quality: PASS
Actionable P0/P1/P2 findings: none.

Reviewed the exact eight-file review package against the supplied requirement and immutable selected sources. API base `fa169401ae80c27f399ce12cfc9fe38ed80279df`, selected tree `f3c1933617c27da82555dab9633236eb87e28c2c`; Admin base `442d66fb4a385728c67b44c4c3f8dc6d3237e24b`, selected tree `0bf15057062529ac816ac78d3350ce41045fde41`.

## Strengths and evidence

- API `src/modules/access/presentation/dto/update-free-trial-policy.dto.ts:9-13` retains explicit undefined-only optionality, integer validation and minimum 1, and changes the maximum to 365. Null, fractions, zero and 366 fail these validators; integers 1 through 365 pass. The controller actually installs the matching ValidationPipe.
- API `docs/api/openapi.yaml:1844` declares maximum 365 for PATCH. Its response schema remains able to describe historical stored values, consistent with the requirement to leave stored policy unchanged.
- API `src/modules/access/presentation/admin-free-trial-policy.controller.spec.ts:68` checks 366 rejection, `:107` checks 365 acceptance, and `:138` checks the documented maximum. These use the actual DTO and parsed OpenAPI document.
- Admin `src/app/features/portal/plans/plans.component.html:28` sets input maximum 365; `plans.component.ts:129` gives the matching Korean rule and `:217` enforces integer 1..365. The existing save path checks that predicate before confirmation or API submission, preserves invalid input and focuses the field.
- Admin `src/app/features/portal/plans/plans.component.spec.ts:1603` drives a DOM edit to 365 through confirmation, actual API service and stateful mock, asserting saved state and display. `:1622` exercises invalid 0, fractional, 366 and empty input, checking message, focus and no submission.
- Admin `src/app/core/api/mock/mock-api.interceptor.ts:710-712` agrees with the API integer/range contract. Its spec checks 365 persistence and rejection of null, zero, fractional and 366 values without mutating stored policy.
- No residual literal 3650/3651 occurs in either selected source tree or selected API OpenAPI document. The diff only changes cap-related production literals and associated behavioral expectations; the 30-day mock default, provisioning expiry computation, existing grant behavior, prices and credits remain unchanged.

## Declined to judge

- Migration/clamping of already stored policies above 365 or existing grant expiry conversion: explicitly excluded by the requirement; no migration is introduced.
- Unrelated local formatting, environment, harness and notes: excluded from the supplied immutable selection and review package.
- Deployed database contents and live end-to-end browser/server behavior: no live environment or database evidence was supplied; this review evaluates the selected code and existing run logs.
- Full-suite completion and build process exit status: parent-owned processes were still running or exit status was not yet available at review handoff; the parent must establish successful exits before merge.

## Verification status at handoff

No tests were rerun and no checkout, index, HEAD or branch state was mutated. Existing RED logs confirm API 2 failed / 10 passed and Admin 6 failed / 122 passed against old production code. Existing full-test logs were inspected and were still progressing, so this report does not assert a full green run. Admin build log records successful application bundle generation with an initial bundle budget warning (896.96 kB against 500 kB); API build log contains `nest build`, with no error shown but no exit status. The parent is already collecting definitive process results.

## Assessment

Ready to merge once the parent-owned verification runs complete successfully. The selected implementation matches the requested 365-day boundary with consistent API, documentation, UI and mock behavior; no corrective source changes are required by this review.
