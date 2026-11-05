# Independent final whole-branch review

**Verdict: With fixes — I1, I2, and I3 should be resolved before launch.** No Critical finding. Minor M1 is also actionable.

## Scope and evidence

Reviewed the approved scope, implementation plan, SDD ledger and frozen review packages for the Web API, customer web, admin web, desktop Nest and desktop Angular repositories, with surrounding source where needed. Applicable repository CLAUDE.md instructions were read. All 186 manifest file entries matched their SHA-256 values at review time. Electron has no changes.

This was a read-only source/contract review; no reported suite was rerun, no application/database state was changed, and no checkout, index or branch was mutated. The test counts and real PostgreSQL/browser results in the briefing are controller-provided evidence, not executions performed by this reviewer. Responsive QA and the final API/Nest reruns were still controller-owned at dispatch; this report does not declare those pending checks complete.

## Strengths

- Signup creation and the benefit intent are committed in the user database together. Signup and promotion grants plus their ledgers commit in one admin transaction, and normal login waits for completed provisioning. Existing grant keys preserve exactly-once monetary issuance across the usual acknowledgment-loss retry.
- The new credit benefit is explicitly discriminated from the retained access benefit. Registration limits remain per code, campaign/member history remains enforceable, and the original grant/redemption/ledger relationships are preserved.
- Persistent Free is projected independently of gift balance and expiry. The migration renames the original tier in place, and Free cannot be sold as a recurring product or issued as a synthetic primary admin pass.
- Tier mode and keys are written transactionally, paid hierarchy writes serialize across tiers, and tier reads use a single SQL statement. New operation admission resolves access under the account lock before debit; an existing operation attempt can still recover and refund after downgrade.
- Both pricing surfaces use one catalog component with API-derived prices, signup benefits and plugin rows. Promotion reporting/export routes and services are removed, while the ordinary initial-payment, retry, renewal and cancellation machinery remains. Accepted future initial payments remain visible and cancelable in the dashboard.

## Issues

### Critical

None identified.

### Important

#### I1 — A changed code can be reported successful while the original code's benefit remains applied

**References:**
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/auth/infrastructure/typeorm-signup-completion.repository.ts:40`
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.ts:51`
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/promotions/application/signup-promotion-credit-provisioner.service.ts:38`

**Trigger:** Code A's admin transaction commits, but `markCompleted` fails and the user job becomes retryable. The consent form still permits edits. The member submits a different valid code B, potentially offering a different amount. The user database replaces the durable code with B; the provisioner then finds `signup-promotion:<user>` and returns A's existing grant without checking which redemption it represents. The job is marked completed and login succeeds. Removing the code similarly changes the intent without reconciling the committed promotion.

**Impact:** The final accepted form/durable intent says B, while participation, code count, referrer and credits all belong to A. A member can receive less than B promises without any explanation. Avoiding duplicate grants is correct, but silently treating a different benefit as fulfillment of the changed request violates the signup and attribution contract.

**Fix:** Reconcile committed admin-side fulfillment before accepting a changed intent. Once a promotion is committed, preserve its actual code and return an explicit already-applied/recovery state (or reject edits with a useful explanation); do not claim that a different code was applied. Do not issue a second grant to solve this. Cover both changed-code and removed-code retries after acknowledgment loss, including different A/B credit amounts. The existing provisioner test at `signup-promotion-credit-provisioner.service.spec.ts:42` explicitly permits another raw code and therefore does not catch the end-to-end mismatch.

#### I2 — Resetting the attempt count lets an expired worker complete a different signup intent

**References:**
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.ts:53`
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.ts:166`
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/access/application/free-trial-onboarding.service.ts:72`

**Trigger:** Worker W1 is processing attempt 1 of an intent with no promotion and is delayed beyond the five-minute lease, for example after its admin commit while waiting to acknowledge in the user DB. The member changes the pending intent to code B. `updateSignupIntent` resets `attempt_count` to 0, and W2 claims the edited job as attempt 1. W1 then executes `markCompleted(job.id, 1, ...)`, which matches W2's `processing` row because the only fencing values are the job ID and the reused count. The same collision applies to failure/manual-review writes.

**Impact:** A stale worker can complete the new intent before B's grant is ready, permitting the OAuth login gate to treat the user as ready with only the signup gift. If B fails, its failure update no longer matches because W1 already completed the job, and B can be permanently omitted. More generally, an expired worker may also race to commit the old benefit after an edit. This directly affects the explicitly required durable, concurrent recovery path.

**Fix:** Separate retry-budget accounting from a monotonic claim/intent generation or unique claim token, and require that token for every completion/failure transition. Serialize or fence benefit provisioning against intent changes so an expired worker cannot apply a superseded choice. Add a deterministic interleaving test: pause W1, expire lease, edit/claim W2, resume W1, then fail W2; the edited intent must not become completed or allow login without its accepted benefit.

#### I3 — Retrying after session issuance/response loss gets stuck on an incorrect new-member-only error

**References:**
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api/src/modules/auth/application/signup.service.ts:93`
- `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_client/src/app/features/public/signup-consent/signup-consent.component.ts:204`

**Trigger:** A new member submits a valid code, both benefits are granted and the user job is completed, but session issuance or the completion response fails. The UI retains the original code and invites retry. On that retry the user now exists and has no pending job, so line 93 returns `SIGNUP_PROMOTION_NEW_MEMBERS_ONLY` before the repository can produce `signup_ticket_used`. The UI treats this as an editable code error and keeps the same form/ticket/code. Every unchanged retry returns the same error.

**Impact:** The new member is told that their own signup code is only for new members, with no actionable recovery guidance, even though their grant succeeded. Fresh Google login can recover, as the integration test demonstrates, but the actual retry flow does not guide them there. This is specifically the session/response-loss case required by the launch acceptance criteria.

**Fix:** Distinguish an already-completed signup for this same signed ticket/account from an existing member attempting a new redemption. Either resume session issuance safely without regranting, or return a dedicated completed/used-ticket response that takes the UI to a clear login-recovery action. Add an API-plus-UI regression using the same ticket and preserved code after session issuance failure; keep the existing-member rejection intact.

### Minor

#### M1 — Credit-only revocation still tells the member that an access pass was revoked

**Reference:** `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html:16`

**Trigger:** An administrator revokes a signup-credit redemption. The generic latest-revocation notice is shown on the member dashboard.

**Impact:** The text says the code's access pass and remaining promotion credits were revoked, although this variant never issued a pass and Free remains active. The actual revocation transaction correctly preserves unrelated access and credits; the message misrepresents that result.

**Fix:** Carry the benefit kind/access-grant presence into the notice and select the appropriate copy, or use accurate neutral benefit wording. Verify a credit-only revocation alongside the retained access-benefit notice.

## Deferred-ledger triage

- The previous header-suite issue is resolved in the reviewed package by test URL/history teardown; no production header change or new finding is warranted.
- Baseline bundle-budget warnings are not newly introduced functional defects and do not invalidate the reported successful builds.
- The admin audit null labels and purchased-credit expiry label are corrected in the reviewed sources; no remaining finding on those items.
- The global AuthService/HTTP Set-Cookie race limitations were examined. They predate this change: component destruction guards now avoid local draft/token/navigation side effects, but cannot cancel a browser cookie response or an already-running global session load. No new regression was established in the changed signup code; the broader global-auth serialization concern is set aside explicitly below.

## Declined to judge

1. General cross-tab/account AuthService serialization and cancellation of previously issued HTTP Set-Cookie responses: pre-existing application-wide behavior, not a newly established regression from these changes. This does not exempt the new signup recovery errors I1–I3.
2. Full plugin registration discovery, app/admin store synchronization, categories/order and global publication/off controls: expressly deferred to W18. The manual shared labels and current registered execution keys were reviewed.
3. Real Google-provider and Toss-provider traffic, production configuration/secrets, deployment sequencing and rollout compatibility with already-installed older desktop binaries: not exercised or fully evidenced in this isolated implementation review. The brief explicitly reports mocked Google and no live Toss traffic.
4. Final responsive/browser appearance and the controller's still-running full-suite/environment work: owned by the controller, not repeated here. Source structure and supplied evidence were considered; this report makes no claim of independently completed browser QA.
5. Unrelated historical payment-engine algorithms beyond the changed call sites and preserved commitment paths: no general payment-system audit was requested, and no unrelated defect was established by this pass.
6. Existing bundle-budget warnings and unrelated local font/packaged-environment test-fixture availability: baseline/environment concerns, not source defects demonstrated in this branch. Their final verification status still belongs in the handoff.
7. Production data cleanup, disabling already-accepted future financial commitments, and destructive rollback of used signup-benefit schema: expressly outside the authorized scope; preserving records and rejecting destructive rollback is appropriate.

No other observed behavior was silently excluded on the basis that the spec did not enumerate its trigger.

## Recommendations and assessment

Keep the existing transactional grant/idempotency structure. Address mutable-intent recovery and worker fencing as a focused fix wave, then verify the new interleavings and same-ticket login recovery in addition to the existing real-database suite. Correct the notice copy without changing revocation policy. No broad refactor or additional feature work is necessary for the findings.

**Ready to merge/launch: With fixes.** The core Free, pricing, catalog, execution and payment-retirement implementation is coherent. The remaining important findings are reachable fault-recovery cases in the launch's central signup path and should be resolved before calling that path durable and complete.
