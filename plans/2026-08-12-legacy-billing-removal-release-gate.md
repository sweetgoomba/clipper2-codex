# Legacy Billing Removal and Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 무통장 구매 요청, legacy `plans`/`licenses`/단일 잔액 코드와 테이블을 제거하고, 여섯 저장소의 새 계약을 한 번에 검증한 뒤에만 병합·배포한다.

**Architecture:** 파괴적 전환 마이그레이션은 새 상품·이용 자격·크레딧·결제 스키마가 먼저 존재하는 것을 검증한 후 prelaunch legacy 테이블을 삭제한다. API의 legacy `billing` 모듈에 섞여 있던 회원 조회는 새 `members` 모듈로 이전하고, 운영 대시보드는 활성 자격·구독·결제 공급 실패를 보여준다. 데이터 백업과 마이그레이션 스모크 후 코드 커밋 세트를 고정한다.

**Tech Stack:** NestJS 11, TypeORM/PostgreSQL, Angular 19/22.1, Electron 43.3, Node.js 22/24, Docker Compose deployment

## Global Constraints

- 모든 선행 계획의 커밋이 여섯 기능 브랜치에 존재해야 시작한다.
- 새 스키마와 모든 클라이언트가 완성되기 전에 `dev`에 일부만 병합하거나 배포하지 않는다.
- 출시 전 데이터는 보존하지 않으며 legacy 구매 요청·이용권·잔액·원장을 삭제한다.
- 과거에 적용된 마이그레이션 파일은 수정하지 않고 새 admin 마이그레이션을 추가한다.
- 상용 DB 마이그레이션 전에는 반드시 복구 가능한 백업을 생성한다. 마이그레이션 `down` 스키마는 삭제된 사용자 데이터를 복구하지 못한다.
- 익명 Toss 심사 checkout과 비밀 조회 토큰은 유지하고 fulfillment만 금지한다.
- 로컬 Toss 결제 버튼은 표시하되 클릭 시 사용 불가 안내를 표시한다.
- 장시간 `running` 작업은 시간 경과만으로 자동 환불하지 않고 공급자 증거 확인 후 운영자가 성공 또는 실패·반환으로 확정한다.
- 완료 주장 전 `superpowers:verification-before-completion`을 사용해 실제 명령 출력을 다시 확인한다.

---

### Task 1: Move Member Queries and Admin Stats off Legacy Billing

**Files (`clipper_web_api`):**
- Create: `src/modules/members/domain/member.model.ts`
- Create: `src/modules/members/application/members.service.ts`
- Create: `src/modules/members/application/members.service.spec.ts`
- Create: `src/modules/members/presentation/members.controller.ts`
- Create: `src/modules/members/presentation/members.controller.spec.ts`
- Create: `src/modules/members/members.module.ts`
- Create: `src/modules/admin-dashboard/application/admin-stats.service.ts`
- Create: `src/modules/admin-dashboard/application/admin-stats.service.spec.ts`
- Create: `src/modules/admin-dashboard/presentation/admin-stats.controller.ts`
- Create: `src/modules/admin-dashboard/admin-dashboard.module.ts`
- Modify: `src/app.module.ts`
- Modify: `docs/api/openapi.yaml`

**Files (`clipper_web_admin`):**
- Modify: `src/app/core/api/models.ts`
- Modify: `src/app/core/api/stats-api.service.ts`
- Modify: `src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `src/app/features/portal/dashboard/dashboard.component.scss`
- Modify: `src/app/features/portal/dashboard/dashboard.component.spec.ts`

**Interfaces:**
- Consumes: user repository, access/credit/subscription/payment repositories
- Produces: member list/detail and stats without purchase request or license types

- [ ] **Step 1: Define the replacement stats contract**

```ts
export interface AdminStats {
  activeAccessGrants: number;
  activeSubscriptions: number;
  pastDueSubscriptions: number;
  failedPaymentFulfillments: number;
}
```

Member list rows contain `accessStatus: 'active'|'scheduled'|'none'`, nullable tier/source/end, `heldCredits`, and `spendableCredits`; they contain no `license`, `queued`, or `tokenBalance` compatibility fields.

- [ ] **Step 2: Write failing API and admin dashboard tests**

Test cross-DB composition by ID with separate repository mocks, and test that the admin dashboard contains no approval actions or deposit counters.

- [ ] **Step 3: Run focused tests and confirm failure**

Run API: `nvm use 22 && npm test -- --runInBand src/modules/members src/modules/admin-dashboard`

Run admin: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/dashboard/*.spec.ts'`

Expected: FAIL because members/stats still depend on purchase requests and licenses.

- [ ] **Step 4: Implement member composition without cross-DB joins**

Page users from the user repository, query access/credit summaries by returned user IDs in the admin repository, then combine in application memory. Detail reads user and access-credit view separately. Do not introduce a DB link or cross-database FK.

- [ ] **Step 5: Implement new dashboard cards**

Show active access, active subscriptions, past-due subscriptions, and failed fulfillments. Failed fulfillment count links to an operational list or member/payment detail, not a payment re-execution button.

- [ ] **Step 6: Run tests and builds**

Run API: `nvm use 22 && npm test -- --runInBand src/modules/members src/modules/admin-dashboard && npm run build`

Run admin: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/dashboard/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit in both repositories**

```bash
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit add docs/api/openapi.yaml src/app.module.ts src/modules/members src/modules/admin-dashboard
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit commit -m "refactor: move members and stats off legacy billing"
git -C /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit add src/app/core/api src/app/features/portal/dashboard
git -C /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit commit -m "refactor: show access payment admin stats"
```

### Task 2: Add Safe Stale-Operation Recovery Operations

**Files (`clipper_web_api`):**
- Modify: `docs/api/openapi.yaml`
- Modify: `src/modules/operations/domain/operations.repository.ts`
- Create: `src/modules/operations/application/operation-recovery.service.ts`
- Create: `src/modules/operations/application/operation-recovery.service.spec.ts`
- Create: `src/modules/operations/presentation/admin-operation-recovery.controller.ts`
- Create: `src/modules/operations/presentation/admin-operation-recovery.controller.spec.ts`
- Create: `src/modules/operations/presentation/dto/list-stale-operations-query.dto.ts`
- Create: `src/modules/operations/presentation/dto/resolve-stale-operation.dto.ts`
- Modify: `src/modules/operations/infrastructure/typeorm-operations.repository.ts`
- Modify: `src/modules/operations/operations.module.ts`

**Files (`clipper_web_admin`):**
- Create: `src/app/core/api/operation-recovery-api.service.ts`
- Create: `src/app/core/api/operation-recovery-api.service.spec.ts`
- Create: `src/app/features/portal/operation-recovery/operation-recovery.component.ts`
- Create: `src/app/features/portal/operation-recovery/operation-recovery.component.html`
- Create: `src/app/features/portal/operation-recovery/operation-recovery.component.scss`
- Create: `src/app/features/portal/operation-recovery/operation-recovery.component.spec.ts`
- Modify: `src/app/features/portal/portal.routes.ts`

**Interfaces:**
- Consumes: running operation rows and exact-grant refund service
- Produces: read-only stale list plus explicit evidence-backed resolution

- [ ] **Step 1: Define exact recovery routes**

```text
GET  /admin/operations/recovery?olderThan={ISO-8601}&limit={1..100}
POST /admin/operations/{runId}/resolve
body { outcome: 'succeeded'|'failed_refund', reason: string, requestKey: string }
```

List rows include operation/user/start/provider reference/current charged grants and session metadata. They contain no automatic resolution recommendation.

- [ ] **Step 2: Write failing no-timeout-refund tests**

```ts
it('listing a stale run never changes credits or run status', async () => {
  await service.list({ olderThan, limit: 20 });
  expect(credits.refundOperation).not.toHaveBeenCalled();
  expect(repo.markFailed).not.toHaveBeenCalled();
});

it('refunds only after an operator submits failed_refund with a reason', async () => {
  await service.resolve(operatorId, runId, { outcome: 'failed_refund', reason: '공급자 실패 확인', requestKey });
  expect(credits.refundOperation).toHaveBeenCalledOnceWith(expect.objectContaining({ operationRunId: runId }));
});
```

- [ ] **Step 3: Run tests and confirm failure**

Run API: `nvm use 22 && npm test -- --runInBand src/modules/operations/application/operation-recovery.service.spec.ts`

Run admin: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/operation-recovery/*.spec.ts'`

Expected: FAIL because recovery capability does not exist.

- [ ] **Step 4: Implement locked, idempotent manual resolution**

Lock the run, reject non-running runs unless the same request key already resolved it, write an audit event, then either mark succeeded without credit change or refund exact grants and mark failed in one short transaction. The admin UI requires the operator to inspect provider reference/evidence and enter a reason.

- [ ] **Step 5: Run tests and builds**

Run API: `nvm use 22 && npm test -- --runInBand src/modules/operations && npm run build`

Run admin: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/operation-recovery/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit in both repositories**

```bash
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit add docs/api/openapi.yaml src/modules/operations
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit commit -m "feat: add evidence based operation recovery"
git -C /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit add src/app/core/api src/app/features/portal
git -C /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit commit -m "feat: add stale operation recovery console"
```

### Task 3: Drop Legacy Tables and Delete the API Billing Module

**Files (`clipper_web_api`):**
- Create: `src/core/database/migrations/admin/1786800000000-DropLegacyBilling.ts`
- Create: `src/core/database/migrations/admin/1786800000000-DropLegacyBilling.spec.ts`
- Delete: `src/modules/billing/**`
- Modify: `src/core/database/admin.datasource.ts`
- Modify: `src/app.module.ts`
- Modify: `docs/api/openapi.yaml`
- Modify: tests/imports elsewhere that still reference billing types

**Interfaces:**
- Consumes: complete new catalog/access/credits/members/payments modules
- Produces: no runtime dependency on `plans`, `purchase_requests`, `licenses`, `token_usage`, or old `credit_ledger`

- [ ] **Step 1: Write the destructive migration test**

```ts
it.each(['purchase_requests', 'token_usage', 'licenses', 'plans', 'credit_ledger'])(
  'drops legacy table %s only after target tables exist', (table) => {
    expect(upSql.indexOf('user_access_grants')).toBeLessThan(upSql.indexOf(`DROP TABLE IF EXISTS ${table}`));
  },
);
```

The migration first asserts target tables through `to_regclass`, clears prelaunch review/order rows that reference removed legacy snapshots when necessary, removes dependent constraints, then drops tables in FK-safe order. `down` recreates the exact empty legacy schemas for technical rollback but explicitly cannot restore deleted rows.

- [ ] **Step 2: Run migration test and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/core/database/migrations/admin/1786800000000-DropLegacyBilling.spec.ts`

Expected: FAIL because the migration does not exist.

- [ ] **Step 3: Delete module code and old OpenAPI paths**

Remove `/plans`, `/license-requests`, `/licenses/current`, `/licenses/consume`, `/admin/requests`, legacy `/admin/plans`, and their schemas. Keep `/catalog`, `/access`, `/credits`, `/subscriptions`, `/payments`, `/admin/members`, and new admin routes.

- [ ] **Step 4: Scan for forbidden runtime references**

Run:

```bash
rg -n "PlansService|LicensesService|PurchaseRequestsService|LicenseEntity|PlanEntity|PurchaseRequestEntity|TokenUsageEntity|licenses/current|license-requests|purchase_requests|token_usage" src docs/api/openapi.yaml
```

Expected: no matches outside the destructive migration's quoted table names and historical docs excluded from the command.

- [ ] **Step 5: Run all API tests and build**

Run: `nvm use 22 && npm test -- --runInBand && npm run build`

Expected: PASS, including the separately merged/fixed operator JWT expiry test.

- [ ] **Step 6: Commit**

```bash
git add -A docs/api/openapi.yaml src
git commit -m "refactor: remove legacy manual billing system"
```

### Task 4: Remove Residual Legacy Client Symbols

**Files:**
- Modify/Delete: residual files found in `clipper_web_client/src`, `clipper_web_admin/src`, `clipper_angular/src`, and `clipper_nestjs/src`
- Test: full client and desktop suites

**Interfaces:**
- Consumes: complete replacement UI/proxy plans
- Produces: no client call or copy referring to manual purchase, queued license, or single token balance

- [ ] **Step 1: Run exact residual scans**

```bash
rg -n "license-requests|licenses/current|operations/ledger|/plans|purchase_requests|queuedLicense|queuedLicenses|tokenBalance|\uBB34\uD1B5\uC7A5|\uC785\uAE08\uC790|\uAD6C\uB9E4 \uC694\uCCAD|\uC2B9\uC778 \uB300\uAE30" web/clipper_web_client/src web/clipper_web_admin/src desktop/clipper_angular/src desktop/clipper_nestjs/src
```

Expected before cleanup: only explicitly identified residuals; after cleanup: no matches except unrelated natural-language documentation excluded from `src`.

- [ ] **Step 2: Remove only the matched legacy runtime symbols and update their tests**

Do not rename current access or subscription concepts merely to satisfy the scan; remove compatibility fields and dead services created solely for the old contract.

- [ ] **Step 3: Run repository suites**

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd /Users/jina/project/adlight/.worktrees/clipper_angular-access-credit && nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build:devapp
cd /Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit && nvm use 24 && npm run build && node --test test/*.test.js
```

Expected: PASS.

- [ ] **Step 4: Commit cleanup in each repository that changed**

Use commit message `refactor: remove legacy billing compatibility` in each affected repository.

### Task 5: Apply the Migration to a Disposable Local Database

**Files:**
- Modify: none
- Test: compiled admin DataSource against a disposable/local admin database

**Interfaces:**
- Consumes: all new admin migrations
- Produces: database evidence for clean install and upgrade-from-current-schema paths

- [ ] **Step 1: Back up or clone the local admin database before the destructive test**

Use the existing local Postgres credentials and create a disposable database name dedicated to this verification. Do not point this test at dev or production.

- [ ] **Step 2: Test upgrade from the current prelaunch schema**

Run: `nvm use 22 && npm run db:migrate:admin`

Expected: all new migrations apply once; a second run reports no pending migrations.

- [ ] **Step 3: Verify target and removed tables**

```sql
SELECT to_regclass('public.plan_tiers'),
       to_regclass('public.billing_products'),
       to_regclass('public.credit_products'),
       to_regclass('public.user_access_grants'),
       to_regclass('public.credit_grants'),
       to_regclass('public.credit_ledger_entries'),
       to_regclass('public.subscriptions'),
       to_regclass('public.payment_orders');

SELECT to_regclass('public.plans'),
       to_regclass('public.purchase_requests'),
       to_regclass('public.licenses'),
       to_regclass('public.token_usage'),
       to_regclass('public.credit_ledger');
```

Expected: every target relation is non-null; every legacy relation is null.

- [ ] **Step 4: Run API boot smoke**

Run: `nvm use 22 && npm run start:dev`

Expected: Nest dependency injection completes, `/health` returns success, catalog/access/credits/payment/admin routes register, and removed routes return 404. Stop the process after the smoke result is recorded.

### Task 6: Execute the Six-Repository Verification Matrix

**Files:**
- Modify: `.codex/records/sessions/2026-08-12-access-credit-release-verification.md`

**Interfaces:**
- Consumes: exact feature-branch heads and disposable DB result
- Produces: merge approval evidence

- [ ] **Step 1: Run fresh automated checks**

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit && nvm use 22 && npm test -- --runInBand && npm run build
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd /Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit && nvm use 24 && npm run build && node --test test/*.test.js
cd /Users/jina/project/adlight/.worktrees/clipper_angular-access-credit && nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build:local && npm run build:devapp && npm run build:packaged
cd /Users/jina/project/adlight/.worktrees/clipper_electron-access-credit && nvm use 24 && npm test && npm run build
```

Expected: every command exits 0.

- [ ] **Step 2: Run the local application smoke matrix**

Verify: admin grant/change/revoke; monthly idempotent grant; source balances; access-required spending; entitled and locked plugins; operation charge/success/failure exact refund; top-up checkout unavailable notice on localhost; and no manual-purchase screen/API.

- [ ] **Step 3: Run the dev Toss smoke matrix after coordinated deployment**

Verify: authenticated subscription registration and first charge; top-up payment and one fulfillment; duplicate callback without duplicate credit; paid-plus-failed fulfillment recovery; renewal test using a controlled due subscription; cancel-at-period-end; anonymous review one-time/recurring with no access or credits.

- [ ] **Step 4: Fill the verification record with command output, commit hashes, order numbers, and DB evidence**

Do not record API keys, billing keys, access tokens, receipt tokens, or full callback payloads.

### Task 7: Merge and Deploy as One Coordinated Release

**Files:**
- Modify: none unless deployment configuration is proven missing during the verification gate

**Interfaces:**
- Consumes: approved verification record
- Produces: aligned `dev` branches and one dev-server deployment

- [ ] **Step 1: Push the six feature branches after verification**

Run `git push -u origin feat/access-credit-system-replacement` in each repository.

- [ ] **Step 2: Merge only the verified commit heads into each `dev`**

Record the resulting six merge commits. Do not merge a newly advanced feature branch without rerunning the matrix.

- [ ] **Step 3: Back up the dev admin database**

Use the existing `m2-db` backup procedure and verify that the backup artifact is readable before applying the destructive migration.

- [ ] **Step 4: Build images, run the admin migration, and restart the coordinated dev stack**

Use the documented `clipper_infra` compose files on `m2-stage`. The migration runs once from the new API image before exposing the new client/admin images.

- [ ] **Step 5: Execute the dev smoke matrix and make the release decision**

If migration, API boot, authenticated checkout, fulfillment, or entitlement enforcement fails, stop rollout and restore the DB backup plus previous images; do not attempt to recreate deleted legacy data manually.
