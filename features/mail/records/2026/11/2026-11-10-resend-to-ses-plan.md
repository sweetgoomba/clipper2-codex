# Resend to SES implementation plan

**Goal:** Replace active Resend inquiry forwarding and operator invitation/password-reset sending with existing SES transport, without adding these messages to administrator mail activity.

**Spec / approved scope:** User instructions in this chat on 2026-11-10. Company recipient is configured as `INQUIRY_TO_EMAIL=clipper@metabuzz.co.kr`; addresses must come from environment, never executable defaults. Keep customer inquiry acknowledgement separate and unchanged. Preserve links, recipient/reply-to, validation and operator failure semantics. Reuse inquiry temporary storage, distinguish successful completion from forwarding/acknowledgement registration expiry, protect against ambiguous SES send replay. No commits/push/merge/deployment unless separately instructed. Open a new independent-review chat after implementation.

**Architecture:** Existing MailModule/SesMailSender supplies shared credentials, sender and configuration set. A small shared inquiry delivery module supplies the same InquiryMailer to request handling and recovery. AuthModule uses SesOperatorMailer directly; operator tokens never enter customer mail records. Inquiry recovery gains send-start/error metadata and distinct expiry outcomes; known rejections can retry, uncertain sends cannot be blindly repeated. Historic settled rows are not reclassified.

**Tech stack:** NestJS/TypeORM/PostgreSQL, AWS SESv2 SDK, Jest, Docker Compose environment examples.

## Tasks

- [x] 1. Update isolated API/infra branches from fetched latest origin/dev (API 130c81e, infra 50b2038). Preserve all other worktrees. Add regression tests for env-only From, shared SES wiring/recovery, operator boolean semantics and no campaigns for internal messages. Watch failures, implement minimal wiring, run targeted tests.
- [x] 2. Add a versioned admin DB migration for `send_started_at`, `last_error_code`, and `forward_expired`/`receipt_expired` statuses. Keep original migration immutable. Test real PostgreSQL migration up/down, successful replay, safe known-failure recovery, ambiguous/crashed sends without duplicates, expiry distinctions and payload cleanup, and receipt-only recovery after forwarding. Watch failures, implement, rerun.
- [x] 3. Remove active Resend config from Compose/examples, keep INQUIRY_TO_EMAIL and MAIL_FROM_EMAIL explicit, update existing API contract/config docs. Run full API tests/build and infra checks, review diff/secrets/unrelated changes, document results. Open an independent review chat; wait for its result and resolve actionable findings. Leave changes uncommitted on feat branches.

## Review focus

- Missing/blank sender or inbox must not send to a fallback address; no network in tests.
- Request and scheduled recovery must use the same SES configuration and preserve Reply-To.
- An accepted send followed by timeout, process death or DB write failure must not be blindly replayed.
- Expiry clears raw inquiry data while preserving a distinct outcome; company accepted but receipt registration failure is distinct from company failure.
- Concurrent/replayed submissions register one customer acknowledgement, and no internal-forward or credential-link campaign.

## Progress

Latest origin/dev pulled for API/admin/client/infra. API and infra branches `feat/resend-to-ses-261110` created from origin/dev. Actual server env inaccessible locally; examples previously use INQUIRY_TO_EMAIL (prod example already clipper@metabuzz.co.kr), no claim about deployed value.

Local final verification after P2 correction: API 6,281 passed / 524 skipped, snapshots 5, build passed; infra remains 135 passed. Follow-up independent review requested in chat `01a1c34e-2af7-7cd2-ba38-78e551567ef7`. No product edits until reviewer finishes.

Independent review complete. P2 race reproduced, corrected without extending raw-data retention, and independently rechecked (42 tests + build + 6 probes). Final changes are uncommitted; user deployment remains pending.

Second user-requested independent whole-change review: new conditional provider/schema cutover P2 reproduced, migration quarantine + rollback guard + runbook prerequisites added. Two new regressions RED→GREEN; QueryRunner fixture cleanup corrected. Full API 6,283/build passed; independent post-fix 44 tests/build/transition and timing probes passed. Final round2 report: no new actionable findings under documented cutover prerequisites. No commit/push/merge/deployment.
