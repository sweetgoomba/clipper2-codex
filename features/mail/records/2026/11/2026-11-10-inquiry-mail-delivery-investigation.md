# Company inquiry delivery investigation — 2026-11-10

User reports customer acknowledgement received but company mailbox clipper@metabuzz.co.kr does not show the forwarded inquiry. User confirms that mailbox/alias exists and receives ordinary mail.

## User-provided read-only DB evidence

Inquiry b1b184c4-4d8b-4691-9036-cff52f7c2dc5: received 2026-11-10 13:02:37 KST, SES acceptance recorded 13:02:38, status settled, no last_error_code.

Company-recipient mail_feedback within the same time window has one delivered event at 13:02:42 KST, SES message ID 010c01a1c39f4765-6848ed82-e9e2-4094-9d7f-f84d29821122-000000. Customer acknowledgement for the same inquiry ID has delivered status with a different SES message ID (010c01a1c39f4ba7-6650618c-43c7-4344-a0c4-109556407af6-000000).

Company staging does not persist the provider message ID, so exact correlation is by recipient/time and the single matching event rather than a stored inquiry-to-provider foreign key. The matching company event establishes recipient mail-server acceptance, not Inbox placement or reading. Do not classify the root cause as definitively spam before receiver-side evidence is available.

## Investigation so far

Reviewed actual SES adapter, coordinator, feedback parser/repository. Company request must return SES MessageId before customer acknowledgement registration. Feedback records can persist for direct internal messages even without campaigns/deliveries; this does not add administrator mail activity.

Public DNS MX lookup returned 10 mx01.mailplug.com and 20 mx02.mailplug.com. Company receiving is therefore routed to these Mailplug hosts. No live server access, real send, resend, DB write, deployment or product-code change was performed during this investigation. Temporary diagnostic command was syntax/fixture checked without network access.

Next evidence: Mailplug administrator spam-management blocked-mail entry for recipient clipper@metabuzz.co.kr around 13:02:42 KST, subject prefix [Clipper 문의]; inspect block reason and final mailbox/folder. Also check user spam/trash/automatic classification. If no record is visible, recipient provider can trace the specific SES message ID and delivery time. Sender/recipient both being the same address is not by itself proven as the cause. Existing SES/domain/DNS settings should not be changed speculatively.

Sources: AWS https://docs.aws.amazon.com/ses/latest/dg/event-publishing-retrieving-sns-contents.html ; https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-deliverability.html ; Mailplug official manual https://mailplug-help.atlassian.net/wiki/spaces/MM/pages/451379214 ; user settings https://mailplug-help.atlassian.net/wiki/spaces/MM/pages/413040655/ . Official manual search content was available, though direct fetch of the admin page failed.

Current state: transport acceptance and matching company delivered notification observed from user output; actual company Inbox receipt remains unconfirmed; receiver-side filtering/storage investigation pending.

## Primary inbox receipt confirmed; downstream forwarding investigation

User logged in to the actual Mailplug account clipper@metabuzz.co.kr and confirmed the SES inquiry is in its Inbox. Thus the migrated Clipper→SES→primary company Inbox path is now confirmed by user observation, not only the SNS notification. User describes a separately configured company distribution/forwarding rule: a Mailplug message from an employee to clipper propagates to the designated company users, but the SES inquiry does not.

Remaining fault domain is downstream Mailplug forwarding/distribution or the final recipients' filtering. Do not call the original recipient spam-blocked now that Inbox placement is confirmed. A small forwarding delay is possible but no service latency evidence is available. Different From identities and sending infrastructure are confounded in the two tests: employee@metabuzz via Mailplug versus clipper@metabuzz via SES, both to clipper@metabuzz. Sender=recipient loop/self-message exclusion is a hypothesis, not a verified Mailplug policy. No official documentation confirming that exception was found.

Official current Mailplug forwarding guide https://www.mailplug-help.com/50cc6138-8bbc-4b90-9fae-446858071422 documents Mail→bottom gear→User→Forwarding and categories all mail/sender/subject. First inspect the actual feature/rule and its category/destination addresses. If category is all mail, ask the company administrator/provider to check whether forwarding was attempted, exclusions and each target's result, using the 13:02 KST message. Optional controlled user-run tests: personal external email to clipper and normal Mailplug compose from clipper to clipper (not the special Write-to-self action); compare distribution. Do not change sender/DNS, add duplicate CC/BCC routing or disable security before identifying the rule/receiver behavior. No product/server/AWS changes or messages to company staff were performed by the agent.


## Original message comparison and approved sender separation

User confirmed forwarding targets are correct and the category is all mail. Ordinary Mailplug messages, including normal compose from clipper to itself, forward successfully. A personal Gmail message to clipper also forwards successfully. Thus neither sender=recipient alone nor all external-origin messages explain the failure.

The user supplied both original .eml files. The SES message has X-Spam-Flag YES, X-Spam-Status Yes with score 14.7 and required threshold 7.0. Its decoded original Subject has a [SPAM] prefix. The Gmail control has X-Spam-Status No, score -1.0. Mailplug recorded SPF pass and DKIM_VALID_AU/DKIM_VALID for the SES message; authentication failure is not established.

Explicit SES scoring rules include MSP_FrToNeEnvFrom (+7.0; From equals To while From differs from envelope Return-Path), FREEMAIL_FORGED_REPLYTO (+2.5; Gmail Reply-To with non-Gmail From), and proprietary MSP_2025122403 (+5.0; exact rule not disclosed). The original is spam-labelled even though the user saw it in the Inbox. Spam-based forwarding exclusion is a strong hypothesis, not directly proven by a forwarding execution log. No external support message was sent.

User asked for a code/AWS-side change rather than waiting for Mailplug support, proposed noreply@metabuzz.co.kr, and approved proceeding. Local API change reads optional INQUIRY_FROM_EMAIL for the internal inquiry sender only. If absent or whitespace, it retains the existing environment-based MAIL_FROM_EMAIL; it never hardcodes an executable email default. The destination remains INQUIRY_TO_EMAIL and the visitor email remains Reply-To. General/customer/operator mail retains MAIL_FROM_EMAIL. Shared SES region, credentials and configuration set are reused. Recovery and submission resolve the same InquiryMailer provider.

Infra compose forwards INQUIRY_FROM_EMAIL; dev/stage/prod and API env examples document Clipper <noreply@metabuzz.co.kr>. The IAM sample adds noreply alongside clipper in ses:FromAddress without broadening other resources. The deployed IAM policy must be edited by the user: IAM → Policies → ClipperSesSendEmail → Edit → JSON, change only ses:FromAddress from the single string to the array ["clipper@metabuzz.co.kr", "noreply@metabuzz.co.kr"], retaining existing action/resource/other conditions. On the development server, after delivering the code change, set INQUIRY_FROM_EMAIL="Clipper <noreply@metabuzz.co.kr>" in env/stack.dev.env and redeploy API; retain MAIL_FROM_EMAIL and INQUIRY_TO_EMAIL unchanged. No DB migration is required for this change.

Important limit: subtracting 7 points alone from the old score leaves 7.7, still above 7.0. Other rules may also change, but cannot be predicted from their private names. A new user-submitted inquiry and its receiver-side headers/forwarding must confirm actual improvement. Do not claim forwarding is fixed from local tests. The Gmail Reply-To is intentionally preserved for the staff reply workflow.

Custom SES MAIL FROM can replace the default amazonses.com domain with a verified-domain subdomain such as bounce.metabuzz.co.kr, with DNS MX/TXT requirements. It does not make the SMTP envelope address identical to clipper@metabuzz.co.kr; no custom MAIL FROM/DNS change was applied. Reference: https://docs.aws.amazon.com/ses/latest/dg/mail-from.html . IAM From restriction: https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html .

At the implementation checkpoint the remediation changes were local and uncommitted. No AWS mutation, real send, live database access or remote deployment was performed by the agent. Git integration and push were subsequently authorized and completed as recorded below. Local focused tests: 23 API tests and 4 infra environment tests pass; API build passes. Full local API suite: 540 suites pass, 31 conditional suites skipped; 6,251 tests pass, 561 conditional tests skipped; 5 snapshots pass (exit 0). Final git diff --check passes in both API and infra.


## Remediation dev integration and remote push

User confirmed the IAM sender allowlist and the new development-server env row were set, then explicitly requested remote push and development deployment commands. Server deployment remains user-owned.

- API dev/origin-dev: 6da3ebf0bd74092ad5e36d412ec9fe56800fabe3 (`fix(mail): separate the internal inquiry sender`), parent fadabc0c044fa066b84f449cead9b42e3af8bffa; tree e3a0426d81f459c62016a8a9d6ec1eab05a22f2b.
- Infra dev/origin-dev: 88b37607463a552929465641d868e42e2f2591d7 (`fix(mail): configure a dedicated inquiry sender`), parent 724185f36e8d680da702e7768e56c45503e7df36; tree b0b95cec4a5bcd69c3ceb8bb8d65d29c80893281.
- Both original dev checkouts were clean, updated with pull --ff-only and fast-forwarded from the feature branch. Merged tree IDs exactly match tested feature trees. Both pushes succeeded without force. git ls-remote confirmed both exact SHAs; original dev checkouts clean afterward. Existing host-managed feature branches/worktrees retained.
- Fresh premerge checks: full API 6,251 passed, 561 conditional skipped; 540 suites passed, 31 conditional suites skipped; 5 snapshots passed. API build and diff checks pass. Infra deployment/mail-env/AWS-deployment/Toss-env suite 57 passed.
- Independent read-only subagent review /root/review_inquiry_from approved with no actionable bugs or regressions. No live services accessed.

After previously completed IAM/env edits, user can deploy API only with no migration:

```sh
(
  set -e
  cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
  git switch dev
  git pull --ff-only origin dev
  git -C ../clipper_web_api switch dev
  git -C ../clipper_web_api pull --ff-only origin dev
  ./scripts/deploy-dev.sh api
)
```

The deployment helper pulls sources, builds the new API image before replacing the container, and applies current Compose env with force-recreate. No standalone docker restart is sufficient to apply changed container env. If env needs editing use vi, never nano. Do not repeat the previous schema migration solely for this sender change. Expected API image revision is 6da3ebf0bd74092ad5e36d412ec9fe56800fabe3. Check only INQUIRY_FROM_EMAIL, INQUIRY_TO_EMAIL and MAIL_FROM_EMAIL when displaying runtime env, never secrets. User must submit a new inquiry and inspect Mailplug forwarding and original headers; actual forwarding is not yet confirmed after remediation.


## Remediation deployment and forwarding confirmed by user

The user supplied development runtime verification: API image revision 6da3ebf0bd74092ad5e36d412ec9fe56800fabe3; INQUIRY_FROM_EMAIL is Clipper <noreply@metabuzz.co.kr>, INQUIRY_TO_EMAIL is clipper@metabuzz.co.kr, MAIL_FROM_EMAIL remains Clipper <clipper@metabuzz.co.kr>. Public health response status ok with user/release/admin DBs ok. These are user-run results, not agent server access.

The user then submitted a new inquiry and explicitly confirmed receiving the automatic forward. The supplied original [Clipper 문의] 기타 — 테스트입니다.eml was parsed locally, headers only; no mail body was needed. SES Message-ID is 010c01a1c3f1ae32-6c74409a-9e3d-407d-9c30-e1aa2cef72b7-000000, Date 2026-11-10 14:32:38 KST, primary Mailplug receipt 14:32:43 KST. From is Clipper <noreply@metabuzz.co.kr>; To and Delivered-To remain clipper@metabuzz.co.kr. Return-Path is still the default generated ap-northeast-2.amazonses.com address; Reply-To remains the visitor Gmail address (not duplicated here).

The new original records X-Spam-Status No, score=2.7 required=7.0, no X-Spam-Flag YES and no [SPAM] subject prefix. SPF pass and DKIM_VALID/DKIM_VALID_AU remain present. FREEMAIL_FORGED_REPLYTO remains in the test list, so the intended visitor reply workflow is preserved. MSP_FrToNeEnvFrom and MSP_2025122403 are both absent from the new test list; the prior original had their respective +7 and +5 entries, with total score14.7. Total new score is12 points lower. Proprietary rule internals remain undisclosed; no claim is made that every scoring difference has been independently isolated. The new SES outbound IP differs from the old one, so this is a successful before/after operational test rather than a controlled proof of every individual filter decision.

Result: dev sender separation deployed, primary recipient arrival and downstream forwarding confirmed by user, normal spam classification supported by the original headers. The incident is resolved for this verified development flow. No custom MAIL FROM, DNS changes, Reply-To removal, blanket spam allowlisting, or production deployment was performed as part of this remediation. No further change is required for the reported test case. Existing production rollout remains user-owned and separate.
