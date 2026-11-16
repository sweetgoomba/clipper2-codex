# Resend to SES — implementation and independent review handoff

## Approved scope

User requested all currently active Resend paths (company inquiry forwarding, operator invitations/re-invitations, operator password reset) move to SES, with none of these internal messages appearing in administrator mail activity. Customer inquiry acknowledgement remains its separate existing SES automatic event. Company destination must be environment-driven, configured as `INQUIRY_TO_EMAIL=clipper@metabuzz.co.kr`. All sender addresses must be environment-driven, with no executable fallback address. Improve inquiry expiry outcomes. User explicitly requested a NEW chat for independent verification after implementation.

## Sources and branches

All four source repositories were pulled with `git pull --ff-only origin dev` and were already up to date. Original admin checkout has unrelated untracked compose mockups; preserved.

- API source dev/base: `130c81e8e2fd3e7759072be6ba22fb269c5f128b`.
- API changes: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api`, branch `feat/resend-to-ses-261110`.
- Infra source dev/base: `50b2038c97afea62bf75603feb33efbbf876c5d8`.
- Infra changes: `/Users/jina/.codex/worktrees/mail-integration-infra-261109/clipper_infra`, branch `feat/resend-to-ses-261110`.
- Admin source dev `e89a8d197b1c6f7a77beebfab1759df1fa988f2e`; client source dev `93fb968c038b6d75e57b6028c2e56a1b62498b8e`; no edits.
- Changes are UNCOMMITTED. No new commits, push, merge, server deployment, AWS changes or real mail sends. Source dev checkouts were only pulled, not modified by implementation.

## Implementation

- `InquiryDeliveryModule` provides the environment-configured `SesInquiryMailer` to submission and scheduled recovery. AuthModule binds `SesOperatorMailer` using the same core SES sender. Existing target/Reply-To, operator links and boolean failure behavior are preserved; internal messages bypass campaigns/deliveries.
- `MAIL_FROM_EMAIL` is explicit; removed hardcoded sender fallback from MailModule and Compose. `INQUIRY_TO_EMAIL` remains explicit. Removed active `RESEND_API_KEY` and `INQUIRY_FROM_EMAIL` wiring from Compose and examples; no actual server env files were changed or found locally. All examples document the requested inbox. Prod example configuration set aligned with user-created `clipper-mail-prod`.
- Old inactive Resend adapter classes/tests remain untouched except their former active bindings are removed; there is no automatic runtime fallback to them. Existing inactive withdrawal adapter was not reactivated.
- New admin migration `1794270000000-InquiryDeliveryOutcomes.ts` adds send_started_at and last_error_code; statuses now also allow forward_expired and receipt_expired. Original migration is unchanged. Historic settled records cannot reliably be reclassified and remain untouched. Down migration maps new terminal states back to settled before restoring original schema.
- Send-start metadata is persisted and ownership checked before network call. Definitive rejections release the send-start fence for retry; ambiguous timeout/process death pauses automatic forwarding to avoid duplicates. Pending ambiguous payload is cleared at retention expiry. This is not a claim of exactly-once delivery; no SNS reconciliation for these internal records was introduced.
- Accepted forwarding is preserved if the first completion DB write fails; subsequent recovery only registers the customer acknowledgement. Registration is guarded by ownership in a transaction.
- Expiry clears raw payload, preserves distinct failure status/error and emits an ID-only warning. Existing 24-hour recovery retention and separate customer acknowledgement content/history remain.
- Updated existing API description/config examples and infra runbook. No UI change.

## Verification evidence

Logs in `/private/tmp/clipper-ses-*.log`.

- Baseline scoped API: 71 tests passed.
- RED: From fallback + missing SES binding tests failed as expected; uncertain error classification failed as expected; PostgreSQL expiry distinction and ambiguous replay tests failed as expected; lost-lease-before-send test failed as expected; infra env tests failed before edits.
- GREEN scoped API + isolated PostgreSQL: 108 tests passed.
- Full API `CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent`: 540 suites / 6,279 tests passed, 30 suites / 524 tests skipped; 5 snapshots passed. Expected negative-path logger output is present; zero failing tests. Includes 33 real PostgreSQL mail integration tests.
- `npm run build`: passed.
- Infra `node --test scripts/deployment.test.mjs scripts/mail-env.test.mjs scripts/deploy-aws-prod.test.mjs scripts/validate-toss-payments-env.test.mjs`: 135 tests passed.
- Compose base/dev/prod YAML parse passed. `git diff --check` passed in both repos.
- Existing opt-in PG test had an outdated assertion expecting no `[Clipper]` subject prefix, inconsistent with already-implemented behavior. Updated only that expected string; no customer template behavior changed.

## Disposable PostgreSQL for independent tests

Parent created a brand-new local cluster ONLY for tests:
`/private/tmp/clipper-resend-ses-261110-pg/data`, host `127.0.0.1`, port `55439`, role `clipper_mail_test`, DB names `clipper_mail_user_test` and `clipper_mail_admin_test`. No application DB env is consumed by this test suite. It deliberately rebuilds these disposable schemas. Tests mock all SES requests; do not send real mail.

Reviewer may run `CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent` and `npm run build` in the API worktree and the infra commands above. Do not stop the disposable cluster until reviewer is done. Parent will shut it down after review.

## Review request

Inspect actual uncommitted diffs and untracked new source files independently, not only this summary. Check env-only routing, request/recovery provider parity, shared Nest dependency wiring, operator credential privacy/no campaigns, duplicate protection under concurrent requests/process death/DB failure, expiry distinction and privacy, migration order/up/down, and deployment/config compatibility. Report actionable findings with severity, absolute file path and line; separate limitations/inferences from proven bugs. Do not edit product code, switch branches, commit, merge, push, deploy or access live DB/AWS/mail. Save report beside this document as `2026-11-10-resend-to-ses-independent-review.md` and report completion. Record exact verification commands/results. Parent will resolve findings.

## Independent-review P2 correction

First review found an actual race: expiry cleanup removed the active attempt token, so late known SES acceptance could not be recorded and was misclassified as forwarding expiry. Parent reproduced RED in `/private/tmp/clipper-ses-red-expiry-metadata.log`.

Correction preserves the opaque send-attempt token on expiry while deleting payload on the original deadline. A late definitive acceptance updates forwarded_at and changes forward_expired to receipt_expired, without registering a customer acknowledgement after retention expiry or retaining raw data longer. The accepted-result recovery write handles this conversion too. Added PostgreSQL cases for both ordinary late success and failure of the first completion write. Retention policy and automatic-replay fence are unchanged. First report remains a historical snapshot; a follow-up review is requested after final verification.

## Final local state

Independent follow-up review concluded the P2 is resolved and no new actionable defect was found in the correction. Reviewer independently passed 42 related tests, a build and 6 real-time/race/failure PostgreSQL probes. See `2026-11-10-resend-to-ses-independent-review.md`, final follow-up section. Parent final API suite passed 6,281 tests (524 conditional tests skipped), 5 snapshots, build; isolated mail PostgreSQL suite has 35 passing tests. Infra 135 tests and YAML/diff checks passed. No live sends or live environment checks were made.

API and Infra remain uncommitted on `feat/resend-to-ses-261110`; original dev checkouts retain their original heads and zero tracked changes. Original Admin's 15 unrelated untracked review files remain. No new commits/push/merge/deploy were performed.

Deployment prerequisites (user performs deployment): apply the new admin migration before starting this API; update both API and Compose; explicitly set `INQUIRY_TO_EMAIL=clipper@metabuzz.co.kr` and `MAIL_FROM_EMAIL="Clipper <clipper@metabuzz.co.kr>"`; reuse the existing MAIL_SES_* credentials/role/configuration set. Actual server's current Resend recipient remains unverified: old code reads INQUIRY_TO_EMAIL, and the existing prod example already uses the requested inbox. Do not describe example values as inspected server values.

Intentional limitation: ambiguous SES acceptance pauses automatic replay to prevent duplicate forwarding; it requires internal investigation rather than guaranteeing loss-free exactly-once delivery. Historic settled records cannot distinguish previous expiry from success and are not rewritten. Separate customer acknowledgement history retains its existing content/retention behavior.

Disposable local PostgreSQL is stopped after independent review; its data and evidence are preserved under `/private/tmp/clipper-resend-ses-261110-pg` for optional reproduction. No application/server DB was touched.

## Second independent-review correction — provider/schema cutover

User requested a second whole-change independent review. New report `2026-11-10-resend-to-ses-independent-review-round2.md` reproduced another conditional P2: a Resend-accepted request without forwarded_at could be replayed through SES after upgrade, and down/up could erase an existing uncertainty fence.

Correction in the unreleased new migration conservatively quarantines old pending, attempted, unforwarded rows with `LEGACY_FORWARD_UNCERTAIN` and a send-start fence. Never-attempted and already-forwarded rows retain normal recovery. This migration timestamp means quarantine time, not historical network start. A count-only warning asks the deployer to reconcile provider acceptance. Raw retention is unchanged. Down migration refuses to erase pending uncertain-send metadata with `INQUIRY_UNCERTAIN_FORWARDING_BLOCKS_ROLLBACK` before any DDL. Runbook requires all old API instances stopped for cutover and prohibits rolling back the binary while ambiguous pending sends exist; an old binary cannot honor the fence.

RED proof: `/private/tmp/clipper-ses-red-cutover.log` (both new PostgreSQL tests failed as expected). GREEN: `/private/tmp/clipper-ses-green-cutover-clean.log`, 37 actual PostgreSQL tests passed. Repeated migration setup exposed test-only QueryRunner leaks; fixture now releases each runner in finally rather than increasing pool limits. Two waiting parent test processes were terminated and final verification rerun sequentially; interrupted logs are not passing evidence. No product runtime change outside the new migration, tests and deployment documentation was needed. Follow-up independent verification pending.

## Second review final result

The provider/schema cutover P2 is fixed and independently reverified; round2 report's final section is authoritative. Independent checks passed 44 relevant tests/build, the same real child-process Resend-acceptance/crash fixture (no SES replay after quarantine), rollback refusal before DDL, safe down/up after expiry, normal legacy recovery, metadata/privacy assertions and 6 prior timing probes. No new actionable finding remained within documented transition prerequisites. Final parent full API: 6,283 passed / 524 conditional skipped / snapshots 5, build passed. Infra 135 passed in the fresh round2 whole-change review; only deployment documentation changed after that run. Changes remain uncommitted on the same two feat branches. No real server/DB/AWS/mail was used. Owned temporary cluster stopped after review. Rollback is not advertised safe for arbitrarily starting an old binary: follow the runbook stop/reconcile prerequisites.

## Git integration follow-up

User authorized dev merge and remote push. API `fadabc0c044fa066b84f449cead9b42e3af8bffa` and Infra `724185f36e8d680da702e7768e56c45503e7df36` are committed, fast-forwarded into dev and pushed/verified. Previous uncommitted descriptions are historical. User deployment/env changes remain pending. See `2026-11-10-ses-dev-merge-and-env.md` for full evidence and commands.
