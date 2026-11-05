# Final fix wave — frozen

Status: **Implemented and verified; ready for the one scoped re-review.** Findings addressed: **I1, I2, I3, M1**. Source frozen at 2026-11-02T04:55:50.553225+00:00.

This is the sole final implementation fix wave. No subagents, commits, staging, push, merge, original-checkout edits, original database access, live provider calls, or documentation edits outside the permitted scope. Only the two assigned isolated worktrees were edited. The disposable integration database on port 15437 received the additive migration and test fixtures; root owns restoration of UI fixture tier lists and browser QA.

## Changes by finding

### I1 — committed promotion and durable intent agree

Completion locks the existing user-job row before inspecting or editing the signup intent. While holding that row lock, an attempted change/removal checks the committed admin-side `signup-promotion:<user>` grant under the admin per-user advisory lock. Its redemption and code identify the actual applied benefit. A conflicting request gets HTTP409 `SIGNUP_PROMOTION_ALREADY_APPLIED`, with `appliedPromotionCode`, and leaves the original durable intent untouched. No second grant is issued. The provisioner itself also rejects an existing grant belonging to a different requested code rather than silently treating it as fulfillment.

The client restores the actual code, saves that draft, makes the input read-only, explains why the committed benefit cannot be changed/removed, and offers **적용된 혜택으로 가입 완료**. The normal capped/failed-without-commit path remains editable and removable. Real tests cover original200 versus replacement900 credits and both changed and removed choices; totals, redemption counts, and ledgers remain exactly once.

### I2 — claim fencing and serialized effects

An additive `claim_generation` integer is separate from `attempt_count`. Every claim and accepted intent edit increments generation. Completion, retryable failure, and manual-review writes match generation and processing status. Retry count can reset for a new code without reusing claim identity.

Workers enter `withClaim`, which locks and revalidates the user-job row before running any effects. The row lock remains held through the separately committed admin transaction and user acknowledgement. A superseded worker does no provisioning or status writes. Intent edits acquire the same row lock; background/immediate claims use `SKIP LOCKED`, so an expired lease does not defeat an actively held lock. The lock order is user/job then admin user lock; worker user lookup is a plain read performed **before** reserving the job-lock connection. The known user snapshot passes into gift provisioning, eliminating nested user-pool borrowing. The read failure is still classified and persisted through the fenced failure path.

Explicit signup repair may retry a signup job in manual review, so commit-response loss at the sixth attempt does not become permanent. Background scanning still excludes manual review and keeps the bounded retry behavior. No cross-database FK, JOIN, atomic shared transaction, or 2PC was added: admin grants commit independently while the user lock serializes intent changes, and acknowledgement loss recovers idempotently.

Real PostgreSQL checks cover both no-code and code-A stale workers, all three stale status writes, W2 failure/login denial after an edit, an actual blocked edit while W1 is paused after admin commit, background/immediate skip-locked claims, unknown admin commit at the retry budget, and three concurrent requests with the user pool capped at one connection and a one-second acquisition timeout.

### I3 — completed same-ticket recovery

Before new-member rejection, the service distinguishes a completed signup whose stored ticket matches the verified signed ticket and account. Both service and transactional repository return HTTP409 `SIGNUP_ALREADY_COMPLETED` (including the applied code when present). No session is blindly reissued and no benefits/consents are appended on this recovery response. Genuine existing-member attempts using a different ticket still receive `SIGNUP_PROMOTION_NEW_MEMBERS_ONLY`; existing duplicate-ticket rejection for unrelated tickets remains intact.

The UI clears the consumed ticket/draft, replaces the editable consent form with a completed-signup explanation and a **다시 로그인** action, and can display the actual applied code. API-plus-UI regressions preserve the original code across session/response failure and retry the same ticket. Fresh Google-login recovery remains covered by the pre-existing real test.

### M1 — accurate revocation copy

The shared dashboard notice now says the code's **프로모션 혜택** was revoked. This neutral wording is accurate for both credit-only and retained access benefits and does not claim that Free or a nonexistent access pass was revoked. The shared notice regression asserts the inaccurate 이용권과 wording is absent while code/reason/benefit notice remains.

## Verification

All commands used `PATH=/Users/jina/.nvm/versions/node/v24.19.0/bin:$PATH`. Commands ran from the respective assigned repository. Log paths below are relative to `/private/tmp/promotion-launch-final-review`.

| Stage | Exact command after PATH prefix | Result | Log |
|---|---|---|---|
| API RED | `SIGNUP_INTEGRATION_DB_PORT=15437 npm test -- --runInBand signup-benefits.integration.spec.ts` | 4 expected failures, 8 pass | `fix-red-api.log` |
| Client RED | `npm test -- --watch=false --karma-config=/tmp/task2-frontend-karma.cjs --include='**/signup-consent.component.spec.ts' --include='**/dashboard.component.spec.ts'` | 3 expected failures,106 pass | `fix-red-client.log` |
| Pool RED | `npm test -- --runInBand free-trial-onboarding.service.spec.ts` | 1 expected failure,12 pass | `fix-red-user-pool.log` |
| API focused GREEN | `npm test -- --runInBand free-trial-onboarding.service.spec.ts free-trial-provisioner.service.spec.ts signup.service.spec.ts typeorm-signup-completion.repository.spec.ts typeorm-user-onboarding-jobs.repository.spec.ts signup-promotion-credit-provisioner.service.spec.ts` | 6 suites,56 pass | `fix-green-api-focused.log` |
| Real PostgreSQL GREEN | `SIGNUP_INTEGRATION_DB_PORT=15437 npm test -- --runInBand signup-benefits.integration.spec.ts` | 16/16 pass | `fix-green-api-integration.log` |
| Client focused GREEN | same command as Client RED | 109/109 pass | `fix-green-client-focused.log` |
| Final API full | `npm test -- --runInBand` | 468 suites pass,11 skipped;5082 tests pass,86 skipped;5 snapshots pass | `fix-api-full.log` |
| Final client full | `npm test -- --watch=false --karma-config=/tmp/task2-frontend-karma.cjs` | 587/587 pass | `fix-client-full.log` |
| API production build | `npm run build` | exit0 | `fix-api-build.log` |
| Client production build | `npm run build` | exit0; existing initial bundle budget warning505.20kB versus500kB | `fix-client-build.log` |
| Whitespace | `git diff --check` in both repositories | exit0 | checked directly |

RED failures were behavioral: completed signup returned the incorrect new-member-only error; changed/removal requests resolved while the original grant remained; the stale worker issued the old benefit; the client offered no recovery/actual-code action; and the dashboard claimed an access pass. The pool-specific RED invoked the real free-gift provisioner with a user lookup that refused nested borrowing under the lock and proved completion failed. After correction the same test and the real max-one-connection integration pass.

Environment notes: the first sandboxed integration attempt could not connect (EPERM), and the first sandboxed client launch could not start normally. They were rerun with the authorized local-network/Chrome runner before accepting RED evidence. The first full API sandbox run could not bind local HTTP fixtures and exited with EPERM; preserved at `fix-api-full-sandbox.log`. The final elevated run passes. `fix-api-full-before-pool.log` retains the earlier green full run before the pool correction; the final result above is after that correction. No outstanding test failure is omitted.

## Migration and operational implications

New migration: `1793664000000-AddOnboardingClaimGeneration.ts`, registered in user datasource. Adds non-null integer `claim_generation` default0; existing jobs/history and admin data are preserved. It was exercised through `user.runMigrations()` only against the opt-in disposable connection. Down refuses rollback once any generation has been used (`ONBOARDING_CLAIM_ROLLBACK_HAS_DATA`). Apply the additive migration before running the new binary and drain old generation-unaware workers during rollout; mixed old/new worker behavior is not promised.

An active grant transaction can make a same-user edit wait until the row lock is released. This is intentional serialization, not waiting for lease expiry. Actual browser QA/server restart, production rollout, Google/Toss traffic, and wider app auth-cookie races remain root/previous-review scope. Tests fault-inject response/acknowledgement loss, not abrupt termination of a database backend while an independent transaction is executing. No assertion of crash fault coverage beyond the recorded interleavings is made.

## Review package and exact scope

Before snapshot: `/private/tmp/promotion-launch-final-review/fix-before/` captures all1354 API and337 client tracked/nonignored untracked files before this wave. Before manifest SHA-256: `a6baa82e31bcdb30a76c79339b356934308d5f82ca751d884ff7939e79c81cde`.

Fix-only archive: `/private/tmp/promotion-launch-final-review/fix-package.tar.gz` SHA-256 `9fe31b9a70063219dfaf2feb077b5329bb8441a8e638c289c1412b825972a86d`. It contains only changed-file before/after copies, both fix-only diffs, and the per-file SHA-256 manifest. Manifest: `/private/tmp/promotion-launch-final-review/fix-manifest.json`. The broad whole-branch review packages were not regenerated.

- `clipper_web_api`: branch `feat/signup-credit-promotion-free-20261102`; unchanged HEAD `64919db3d8b12640cab115cf7103c419b60ab2c3`; fix diff SHA-256 `b6befd13194d0b708e2336b4652a22b8453f90fd99a9d2d5834e04b34cfdb3ea`.
- `clipper_web_client`: branch `feat/signup-credit-promotion-free-20261102`; unchanged HEAD `c0719ac8a1f288fc151121fc543c8b4ba8f8cb6c`; fix diff SHA-256 `d859f48657a649ff5ea128fa09ce653d360fb89fbb26d7197d87930e047a83e1`.

Exactly22 files changed in this wave (17 API,5 client):

### clipper_web_api

- `src/core/database/migrations/user/1793664000000-AddOnboardingClaimGeneration.ts`
- `src/core/database/user.datasource.ts`
- `src/modules/access/application/free-trial-onboarding.service.spec.ts`
- `src/modules/access/application/free-trial-onboarding.service.ts`
- `src/modules/access/application/free-trial-provisioner.service.ts`
- `src/modules/auth/application/signup.service.spec.ts`
- `src/modules/auth/application/signup.service.ts`
- `src/modules/auth/infrastructure/typeorm-signup-completion.repository.spec.ts`
- `src/modules/auth/infrastructure/typeorm-signup-completion.repository.ts`
- `src/modules/promotions/application/signup-benefits.integration.spec.ts`
- `src/modules/promotions/application/signup-promotion-credit-provisioner.service.spec.ts`
- `src/modules/promotions/application/signup-promotion-credit-provisioner.service.ts`
- `src/modules/users/domain/user-onboarding-job.model.ts`
- `src/modules/users/domain/user-onboarding-jobs.repository.ts`
- `src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.spec.ts`
- `src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.ts`
- `src/modules/users/infrastructure/user-onboarding-job.entity.ts`
### clipper_web_client

- `src/app/features/portal/dashboard/dashboard.component.html`
- `src/app/features/portal/dashboard/dashboard.component.spec.ts`
- `src/app/features/public/signup-consent/signup-consent.component.html`
- `src/app/features/public/signup-consent/signup-consent.component.spec.ts`
- `src/app/features/public/signup-consent/signup-consent.component.ts`
