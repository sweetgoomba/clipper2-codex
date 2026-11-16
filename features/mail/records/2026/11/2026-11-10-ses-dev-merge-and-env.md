# SES internal-mail migration — dev merge and env handoff

User explicitly requested local dev integration and remote push, and will deploy manually on the development server. No server connection/deployment was performed by the agent.

## Git result

- API: `fadabc0c044fa066b84f449cead9b42e3af8bffa`, `feat(mail): move internal mail delivery from Resend to SES`. Parent `130c81e8e2fd3e7759072be6ba22fb269c5f128b`. 19 reviewed files.
- Infra: `724185f36e8d680da702e7768e56c45503e7df36`, `feat(mail): configure SES for internal inquiry and operator mail`. Parent `50b2038c97afea62bf75603feb33efbbf876c5d8`. 6 reviewed files.
- Both source dev checkouts pulled with --ff-only, then fast-forwarded to the feature commit. Both dev refs pushed to origin and verified with ls-remote. No force push; no conflict. Tested tree IDs match dev exactly.
- API/infra source and managed feature worktrees are clean. Host-managed worktrees and local feature branches are preserved; no unrelated branches or files removed. Admin/client untouched.

## Fresh integration checks

API `CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent`: 6,283 passed, 524 conditional skipped, 540 suites passed, 5 snapshots passed. `npm run build` passed. Infra deployment/mail-env/AWS-deployment/Toss-env tests: 135 passed. Source file hashes still match the independently reviewed final snapshot. Logs `/private/tmp/clipper-ses-merge-*`; integration backup/evidence in `/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/resend-to-ses-261110/`.

## Development env

In server `clipper_infra/env/stack.dev.env`, remove `RESEND_API_KEY` and `INQUIRY_FROM_EMAIL` when replacing the stopped old API with the new version. Keep `INQUIRY_TO_EMAIL`: it is the corporate inbox, not a Resend credential. Set explicitly:

```dotenv
INQUIRY_TO_EMAIL=clipper@metabuzz.co.kr
MAIL_FROM_EMAIL="Clipper <clipper@metabuzz.co.kr>"
```

Existing MAIL_SES_REGION, MAIL_SES_ACCESS_KEY_ID/MAIL_SES_SECRET_ACCESS_KEY (or execution-role chain), MAIL_SES_CONFIGURATION_SET, MAIL_PUBLIC_API_URL, MAIL_UNSUBSCRIBE_SECRET, MAIL_SNS_TOPIC_ARNS, MAIL_WORKER_ENABLED and MAIL_SEND_INTERVAL_MS remain unchanged. Existing S3 AWS_* variables must not be removed as part of this cleanup. No actual env file/secret was edited by the agent.

Do not remove Resend settings from an environment still running the old API. Do not revoke the provider key itself until all environments using it are migrated. This includes production if it has not received this version.

## Manual development deployment

Only API needs rebuilding. Infra is updated by git pull. Existing deploy helper pulls the API current branch before building; select dev first. Stop API before env cleanup and migration. No old API worker should run during provider/schema transition. Run the following on the user's existing remote development-server session, not the agent machine:

```sh
(
  set -e
  cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
  git switch dev
  git pull --ff-only origin dev
  git -C ../clipper_web_api switch dev
  ./scripts/deploy-dev.sh api --build-only
  docker compose --project-name clipper-dev --env-file env/stack.dev.env -f apps/compose.yml -f apps/compose.dev.yml stop api
  vi env/stack.dev.env
  ./scripts/migrate-db.sh dev
  ./scripts/deploy-dev.sh api --start-only
)
```

Edit/save the env in vi (`i` to edit, then Esc and `:wq` to save/exit); confirm the migration prompt with `migrate dev`. Failed migration stops the block before starting API. Newly required admin migration is `InquiryDeliveryOutcomes1794270000000`; existing helper checks user→admin→release pending migrations. Existing attempted-but-unconfirmed Resend inquiries are quarantined (count-only warning), not blindly resent through SES; reconcile provider/company inbox records as documented in Infra runbook. The guard blocks schema rollback while ambiguous pending forwarding exists; do not start an old API binary on such records even without reverting schema. Existing 24-hour payload expiry is maintained.

Deployment completion, actual environment values, live mail and health remain unverified until the user performs deployment.

## Development deployment confirmed by user-provided output

On 2026-11-10 the user supplied the actual remote development-server check outputs. These are user-observed results, not an agent SSH/deployment or independent HTTP probe.

- API running, CLIPPER_ENV dev, container revision matches API commit `fadabc0c044fa066b84f449cead9b42e3af8bffa`.
- All checked MAIL_* / INQUIRY_TO_EMAIL settings are nonempty and match resolved env-file Compose configuration versus the running container. Exact recipient/sender, Seoul region, dev configuration set/API URL/SNS topic, unsubscribe-secret length and customer worker enabled checks all OK. Secret values were not supplied or recorded.
- Old RESEND_API_KEY and INQUIRY_FROM_EMAIL rows absent in development env.
- Admin migration `InquiryDeliveryOutcomes1794270000000` applied; both new columns exist.
- Legacy inquiry quarantine awaiting confirmation: 0 rows at check time.
- User ran `curl -fsS https://dev-api.clipperstudio.ai/health` and received `{"status":"ok","service":"clipper_web_api","db":{"user":"ok","release":"ok","admin":"ok"}}`.

Development image/config/schema/DB health are confirmed to this scope. Real SES delivery of migrated company inquiry and operator invitation/re-invitation/password-reset messages has not yet been reported. Production deployment remains unconfirmed; do not infer it from the development outputs.
