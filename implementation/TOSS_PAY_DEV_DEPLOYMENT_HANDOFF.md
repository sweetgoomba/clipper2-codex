# Toss Pay Dev Deployment Handoff

This runbook starts after the Toss Pay feature branches have been merged into
and pushed to each repository's `dev` branch. Run it on `m2-stage`; do not run
it from a developer laptop.

## Deployment scope

| Host | Action |
| --- | --- |
| `m2-stage` (`192.168.0.23`) | Pull infra/API/client `dev`, build API and client images, migrate admin DB, recreate API and web client |
| `m2-db` (`192.168.0.7`) | No container restart; the migration reaches `clipper_admin_dev` over port `55213` |
| `m2-proxy` (`192.168.0.2`) | No change; existing `dev.clipperstudio.ai` and `dev-api.clipperstudio.ai` routes are reused |

Do not recreate `clipper-web-admin-dev`, restart any PostgreSQL container, or
change Nginx Proxy Manager for this deployment.

## Follow-up: recurring review retry fix

Use this shorter procedure after `fix/toss-recurring-review-retry` has been
merged into `clipper_web_api/dev`. The initial Toss deployment and payment
migration must already be present.

This follow-up changes only the API. It adds a per-order Toss `displayId` and
reconciles recurring billing-key `CREATE`, `ACTIVE`, `CANCEL`, `FAIL`, and
`REMOVE` states. It has no migration, client, infra, credit, or license change.

On `m2-stage`:

```sh
cd /Users/metabuzz/Desktop/project/clipper2

git -C clipper_web_api status --short --branch
git -C clipper_web_api switch dev
git -C clipper_web_api pull --ff-only origin dev

docker build -t clipper-web-api:dev clipper_web_api

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  up -d --force-recreate api
```

Stop before pulling if the API repository has server-local changes. Do not run
any migration and do not deploy the web client for this follow-up.

Verify the recreated API:

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  ps api

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  logs --tail=200 api

curl -sS https://dev-api.clipperstudio.ai/health
curl -sS https://dev-api.clipperstudio.ai/payments/review/config
```

Expected review config remains `{"mode":"checkout"}`.

In a logged-out or incognito browser, open the pricing page and repeat a
recurring checkout with a card that was already used in the shared test store.
The new registration must no longer be rejected as the same merchant billing
registration because each order supplies its own `displayId`. Successful rows
must finish with these events:

```text
billing_key_created / CREATE
billing_activated   / ACTIVE
billing_paid        / PAY_COMPLETE
```

If the tester cancels or Toss rejects registration, opening the result/cancel
page must reconcile the local order to `canceled` or `failed` instead of leaving
it indefinitely at `checkout_ready`.

## 1. Read-only preflight on m2-stage

```sh
cd /Users/metabuzz/Desktop/project/clipper2

git -C clipper_infra status --short --branch
git -C clipper_web_api status --short --branch
git -C clipper_web_client status --short --branch

docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
curl -sS https://dev-api.clipperstudio.ai/health
```

Stop if a repository has uncommitted server-local changes. Preserve all dohit
containers, files, and ports.

## 2. Update the three deployed repositories

```sh
git -C clipper_infra switch dev
git -C clipper_infra pull --ff-only origin dev

git -C clipper_web_api switch dev
git -C clipper_web_api pull --ff-only origin dev

git -C clipper_web_client switch dev
git -C clipper_web_client pull --ff-only origin dev
```

## 3. Set the ignored dev environment

Edit this existing server-only file without replacing its DB credentials or
other secrets:

```text
/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/stack.dev.env
```

Required values:

```dotenv
TOSS_PAY_API_KEY=<official shared test key>
TOSS_PAY_REVIEW_MODE=true
TOSS_PAY_CALLBACK_BASE_URL=https://dev-api.clipperstudio.ai
WEB_BASE_URL=https://dev.clipperstudio.ai
API_KEY_ENC_SECRET=<existing valid value>
```

Check only presence, without printing values:

```sh
cd /Users/metabuzz/Desktop/project/clipper2

for key in TOSS_PAY_API_KEY TOSS_PAY_REVIEW_MODE TOSS_PAY_CALLBACK_BASE_URL WEB_BASE_URL API_KEY_ENC_SECRET; do
  if grep -Eq "^${key}=.+" clipper_infra/env/stack.dev.env; then
    printf '%s=present\n' "$key"
  else
    printf '%s=MISSING\n' "$key"
  fi
done
```

Do not print or commit `stack.dev.env`.

## 4. Validate Compose and build the API image

```sh
cd /Users/metabuzz/Desktop/project/clipper2

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  config --quiet

docker build -t clipper-web-api:dev clipper_web_api
```

## 5. Confirm the migration target

Use a one-off API container so the check receives exactly the same DB
environment as the deployed API. It does not publish a port or replace the
running API container.

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/admin.datasource.js'); const dataSource = module.default?.default ?? module.default; await dataSource.initialize(); const [row] = await dataSource.query('SELECT current_database() AS database_name'); console.log(row.database_name); await dataSource.destroy();"
```

The only acceptable output database name is:

```text
clipper_admin_dev
```

Stop if any other database name is printed.

## 6. Apply the admin migration

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/admin.datasource.js'); const dataSource = module.default?.default ?? module.default; await dataSource.initialize(); const migrations = await dataSource.runMigrations({ transaction: 'each' }); console.log(migrations.length ? migrations.map(({ name }) => name).join('\\n') : 'No pending migrations.'); await dataSource.destroy();"
```

Expected new migration:

```text
CreatePaymentOrders1786300000000
```

This creates `payment_orders` and `payment_events` in `clipper_admin_dev`.
It does not create or restart a DB container.

## 7. Recreate API and web client

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  up -d --force-recreate api

cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh web
```

## 8. Runtime verification

```sh
cd /Users/metabuzz/Desktop/project/clipper2

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  ps api web-client

curl -sS https://dev-api.clipperstudio.ai/health
curl -sS https://dev-api.clipperstudio.ai/payments/review/config
curl -sS -I https://dev.clipperstudio.ai/pricing
```

Expected:

- API and web client containers are running.
- Health reports user, release, and admin DB as `ok`.
- Review config returns `{"mode":"checkout"}`.
- Pricing returns HTTP 200.

## 9. Browser smoke test

Use a logged-out or incognito browser:

1. Open `https://dev.clipperstudio.ai/pricing`.
2. Confirm 1- and 3-month cards have recurring and one-time buttons.
3. Confirm the 12-month card has only a one-time button.
4. Open one-time and recurring Toss test checkout windows without logging in.
5. Complete a test payment and confirm the result page reaches the completed state.
6. Confirm no license, credit, or purchase-request row is automatically granted; that behavior is intentionally out of scope.
