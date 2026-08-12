# Access and Credit API Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `clipper_web_api`에 상품 등급과 플러그인 권한, 한 개의 기본 이용 자격, 출처별 크레딧 지급·차감·반환, 관리자 운영 API를 구현한다.

**Architecture:** 상품 정책은 `catalog`, 현재 이용 권한은 `access`, 사용량 자산과 불변 원장은 `credits`가 소유한다. 크레딧 차감과 반환은 짧은 TypeORM 트랜잭션 안에서 지급 묶음 단위로 수행하고, `operations`는 외부 AI 실행 전후로 각각 시작·성공·실패 트랜잭션만 연다.

**Tech Stack:** NestJS 11, TypeORM, PostgreSQL, Jest 30, class-validator, OpenAPI YAML, Node.js 22

## Global Constraints

- 작업 경로는 `/Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit`, 브랜치는 `feat/access-credit-system-replacement`이다.
- 브랜치는 `feat/billing-product-catalog-foundation` 커밋을 포함한다.
- Node 22를 사용한다.
- API 계약은 `docs/api/openapi.yaml`에 먼저 반영하고 raw JSON 응답을 유지한다.
- admin DB와 user DB 사이에 FK나 JOIN을 만들지 않고 `user_id` 문자열로만 연결한다.
- 데이터베이스 컬럼은 snake_case로 명시하고 `synchronize` 없이 새 admin 마이그레이션만 추가한다.
- 모든 크레딧 사용은 유효한 기본 이용 자격이 필요하다.
- 크레딧은 만료일 오름차순, 같은 만료일은 지급일·ID 오름차순, 만료 없음은 마지막 순으로 차감한다.
- AI 실행 동안 DB 트랜잭션을 열어 두지 않는다.
- 정확한 상품값과 만료기간은 관리자가 저장하는 카탈로그 데이터로 두고 신규 코드 상수를 만들지 않는다.

---

### Task 1: Extend the Catalog Contract with Credit Products and Credit Validity

**Files:**
- Modify: `docs/api/openapi.yaml`
- Modify: `src/modules/catalog/domain/product-catalog.model.ts`
- Modify: `src/modules/catalog/domain/product-catalog.repository.ts`
- Modify: `src/modules/catalog/application/product-catalog.service.ts`
- Modify: `src/modules/catalog/infrastructure/plan-tier.entity.ts`
- Create: `src/modules/catalog/infrastructure/credit-product.entity.ts`
- Modify: `src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts`
- Create: `src/modules/catalog/presentation/dto/create-credit-product.dto.ts`
- Create: `src/modules/catalog/presentation/dto/update-credit-product.dto.ts`
- Modify: `src/modules/catalog/presentation/catalog.controller.ts`
- Modify: `src/modules/catalog/presentation/admin-catalog.controller.ts`
- Modify: `src/modules/catalog/catalog.module.ts`
- Test: `src/modules/catalog/application/product-catalog.service.spec.ts`
- Test: `src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts`
- Test: `src/modules/catalog/presentation/catalog.controller.spec.ts`
- Test: `src/modules/catalog/presentation/admin-catalog.controller.spec.ts`

**Interfaces:**
- Consumes: `ProductCatalogService.activeProductById(id: string): Promise<BillingProduct>`
- Produces: `ProductCatalogService.activeCreditProductById(id: string): Promise<CreditProduct>` and `GET /catalog/credit-products`

- [ ] **Step 1: Define the OpenAPI schemas and routes**

Add these exact fields and paths:

```yaml
CreditProduct:
  type: object
  required: [id, code, name, credits, priceKrw, validityDays, isActive, sortOrder, createdAt, updatedAt]
  properties:
    id: { type: string, format: uuid }
    code: { type: string }
    name: { type: string }
    credits: { type: integer, minimum: 1 }
    priceKrw: { type: integer, minimum: 1 }
    validityDays: { type: [integer, 'null'], minimum: 1 }
    isActive: { type: boolean }
    sortOrder: { type: integer, minimum: 0 }
    createdAt: { type: string, format: date-time }
    updatedAt: { type: string, format: date-time }
```

```text
GET   /catalog/credit-products
POST  /admin/catalog/credit-products
PATCH /admin/catalog/credit-products/{id}
```

Also add nullable `monthlyCreditValidityDays` to `PlanTier` and the tier create/update schemas.

- [ ] **Step 2: Write failing catalog tests**

```ts
it('returns only active credit products in configured order', async () => {
  repo.listCreditProducts.mockResolvedValue([
    creditProduct({ code: 'large', sortOrder: 2, isActive: true }),
    creditProduct({ code: 'hidden', sortOrder: 0, isActive: false }),
    creditProduct({ code: 'small', sortOrder: 1, isActive: true }),
  ]);
  await expect(service.publicCreditProducts()).resolves.toEqual([
    expect.objectContaining({ code: 'small' }),
    expect.objectContaining({ code: 'large' }),
  ]);
});

it('does not attach a plan tier to a credit product', async () => {
  const created = await service.createCreditProduct({
    code: 'topup-small', name: '추가 크레딧', credits: 1000,
    priceKrw: 10000, validityDays: null, sortOrder: 0,
  });
  expect(created).not.toHaveProperty('tierId');
});
```

- [ ] **Step 3: Run the focused tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/catalog/application/product-catalog.service.spec.ts src/modules/catalog/presentation/catalog.controller.spec.ts src/modules/catalog/presentation/admin-catalog.controller.spec.ts`

Expected: FAIL because credit-product types and methods do not exist.

- [ ] **Step 4: Implement the exact domain types and repository methods**

```ts
export interface CreditProduct {
  id: string;
  code: string;
  name: string;
  credits: number;
  priceKrw: number;
  validityDays: number | null;
  isActive: boolean;
  sortOrder: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PlanTier {
  // existing fields stay unchanged
  monthlyCreditValidityDays: number | null;
}
```

Add repository methods `listCreditProducts`, `findCreditProductById`, `createCreditProduct`, and `updateCreditProduct`. New products always start with `isActive: false`; public listing filters inactive rows and sorts by `sortOrder`, then `code`.

- [ ] **Step 5: Add controller methods and validation**

`CreateCreditProductDto` validates positive integer `credits`/`priceKrw`, nullable positive integer `validityDays`, and non-negative `sortOrder`. `UpdateCreditProductDto` makes the same fields optional and adds optional `isActive`.

- [ ] **Step 6: Run catalog tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/catalog && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/api/openapi.yaml src/modules/catalog
git commit -m "feat: extend billing catalog with credit products"
```

### Task 2: Create Access and Source-Aware Credit Schema

**Files:**
- Create: `src/core/database/migrations/admin/1786600000000-CreateAccessCreditSystem.ts`
- Create: `src/core/database/migrations/admin/1786600000000-CreateAccessCreditSystem.spec.ts`
- Create: `src/modules/access/domain/access.model.ts`
- Create: `src/modules/access/infrastructure/user-access-grant.entity.ts`
- Create: `src/modules/access/infrastructure/access-grant-event.entity.ts`
- Create: `src/modules/credits/domain/credit.model.ts`
- Create: `src/modules/credits/infrastructure/credit-grant.entity.ts`
- Create: `src/modules/credits/infrastructure/credit-ledger-entry.entity.ts`
- Create: `src/core/database/admin-transaction.runner.ts`
- Modify: `src/core/database/admin.datasource.ts`

**Interfaces:**
- Consumes: `plan_tiers.id`
- Produces: TypeORM entities for `user_access_grants`, `access_grant_events`, `credit_grants`, and `credit_ledger_entries`

- [ ] **Step 1: Write the migration contract test**

```ts
it('creates one open access per user and nonnegative credit balances', () => {
  expect(upSql).toContain('CREATE UNIQUE INDEX UQ_user_access_grants_open_user');
  expect(upSql).toContain("WHERE status IN ('scheduled', 'active')");
  expect(upSql).toContain('CHECK (remaining_credits >= 0)');
  expect(upSql).toContain('UNIQUE (idempotency_key)');
  expect(upSql).toContain('CREATE TABLE credit_ledger_entries');
});
```

- [ ] **Step 2: Run the migration test and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/core/database/migrations/admin/1786600000000-CreateAccessCreditSystem.spec.ts`

Expected: FAIL because the migration does not exist.

- [ ] **Step 3: Create the target tables and indexes**

Use these stored values:

```ts
export type AccessGrantSource = 'subscription' | 'admin_plan';
export type AccessGrantStatus = 'scheduled' | 'active' | 'ended' | 'revoked' | 'replaced';
export type CreditSource = 'subscription' | 'admin_plan' | 'topup' | 'admin_adjustment' | 'promotion';
export type CreditGrantStatus = 'active' | 'depleted' | 'expired' | 'revoked';
export type CreditLedgerType = 'grant' | 'operation_charge' | 'operation_refund' | 'admin_revoke' | 'payment_adjustment' | 'expire';
```

`user_access_grants` stores `user_id`, `plan_tier_id`, source, status, `starts_at`, nullable `ends_at`, `credit_anchor_at`, nullable `next_credit_grant_at`, nullable `subscription_id`, nullable `admin_reason`, nullable `operator_id`, and lifecycle timestamps/reasons. The partial unique index covers one `scheduled` or `active` row per `user_id`.

`credit_grants` stores source, `initial_credits`, `remaining_credits`, `granted_at`, nullable `expires_at`, status, nullable references (`access_grant_id`, `subscription_id`, `payment_order_id`, `operator_id`), reason, and unique `idempotency_key`.

`credit_ledger_entries` stores `delta_credits`, `balance_after`, nullable `operation_run_id`/`payment_order_id`, `reference_key`, reason, and a unique composite `(credit_grant_id, type, reference_key)`.

Add a single short-transaction runner used by later cross-module use cases:

```ts
@Injectable()
export class AdminTransactionRunner {
  constructor(@InjectDataSource('admin') private readonly dataSource: DataSource) {}
  run<T>(work: (manager: EntityManager) => Promise<T>): Promise<T> {
    return this.dataSource.transaction(work);
  }
}
```

Repository methods that participate in a cross-module atomic action accept the provided `EntityManager`; they never open a nested transaction.

- [ ] **Step 4: Register entities without cross-database foreign keys**

Add all four entities to the admin DataSource and `TypeOrmModule.forFeature(..., 'admin')` only. `user_id` is `varchar(36)` with no FK because users live in the user DataSource.

- [ ] **Step 5: Run migration test and API build**

Run: `nvm use 22 && npm test -- --runInBand src/core/database/migrations/admin/1786600000000-CreateAccessCreditSystem.spec.ts && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/core/database/admin.datasource.ts src/core/database/migrations/admin/1786600000000-* src/modules/access src/modules/credits
git commit -m "feat: add access and credit grant schema"
```

### Task 3: Implement Atomic Access Grant Administration

**Files:**
- Modify: `docs/api/openapi.yaml`
- Create: `src/modules/access/domain/access.repository.ts`
- Create: `src/modules/access/application/access-grants.service.ts`
- Create: `src/modules/access/application/access-grants.service.spec.ts`
- Create: `src/modules/access/infrastructure/typeorm-access.repository.ts`
- Create: `src/modules/access/infrastructure/typeorm-access.repository.spec.ts`
- Create: `src/modules/access/presentation/dto/grant-admin-access.dto.ts`
- Create: `src/modules/access/presentation/dto/update-admin-access.dto.ts`
- Create: `src/modules/access/presentation/dto/change-admin-access-tier.dto.ts`
- Create: `src/modules/access/presentation/dto/revoke-admin-access.dto.ts`
- Create: `src/modules/access/presentation/admin-member-access.controller.ts`
- Create: `src/modules/access/presentation/admin-member-access.controller.spec.ts`
- Create: `src/modules/access/access.module.ts`
- Modify: `src/app.module.ts`

**Interfaces:**
- Consumes: `CreditGrantsService.grant(input: GrantCreditsInput): Promise<CreditGrant>` from Task 4
- Produces: `AccessGrantsService.current(userId)`, `grantAdmin`, `updateSameTier`, `changeAdminTier`, `revoke`, `activateSubscription`, and `extendSubscriptionAccess`

- [ ] **Step 1: Add the admin API contract**

```text
GET   /admin/members/{userId}/access-credit
POST  /admin/members/{userId}/access-grants
PATCH /admin/members/{userId}/access-grants/{grantId}
POST  /admin/members/{userId}/access-grants/{grantId}/change-tier
POST  /admin/members/{userId}/access-grants/{grantId}/revoke
```

`GrantAdminAccessRequest` is `{ tierId, startsAt, endsAt: string|null, reason, requestKey }`. `UpdateAdminAccessRequest` is `{ endsAt: string|null, reason, requestKey }`. `ChangeAdminAccessTierRequest` is `{ tierId, reason, requestKey }`. `RevokeAdminAccessRequest` is `{ reason, requestKey }`.

- [ ] **Step 2: Write failing service tests for the business rules**

```ts
it('rejects a second open access grant', async () => {
  repo.withUserLock.mockImplementation((_id, work) => work(repo));
  repo.findOpenForUser.mockResolvedValue(activeGrant());
  await expect(service.grantAdmin(input)).rejects.toThrow('ACTIVE_ACCESS_CONFLICT');
});

it('changes 10000-credit tier to 30000-credit tier with one 20000 difference grant', async () => {
  await service.changeAdminTier({ userId, grantId, tierId: proId, reason: '업그레이드', requestKey });
  expect(credits.grant).toHaveBeenCalledWith(expect.objectContaining({
    credits: 20000,
    source: 'admin_plan',
    idempotencyKey: `access-tier-change:${requestKey}`,
  }));
});

it('does not regrant credits when only the same-tier end date changes', async () => {
  await service.updateSameTier(input);
  expect(credits.grant).not.toHaveBeenCalled();
});
```

- [ ] **Step 3: Run focused tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/access/application/access-grants.service.spec.ts`

Expected: FAIL because the service and repository contracts do not exist.

- [ ] **Step 4: Implement one short transaction per admin action**

```ts
abstract withUserLock<T>(userId: string, work: (repo: AccessRepository) => Promise<T>): Promise<T>;
abstract findEffectiveForUser(userId: string, at: Date): Promise<UserAccessGrant | undefined>;
abstract findOpenForUser(userId: string): Promise<UserAccessGrant | undefined>;
abstract createGrant(input: NewAccessGrant): Promise<UserAccessGrant>;
abstract endAsReplaced(id: string, at: Date, reason: string): Promise<void>;
abstract updatePeriod(id: string, endsAt: Date | null, reason: string): Promise<UserAccessGrant>;
abstract revoke(id: string, at: Date, reason: string): Promise<void>;
abstract appendEvent(input: NewAccessGrantEvent): Promise<void>;
```

Within `changeAdminTier`, lock by user, end the old grant, create the new grant with the old `creditAnchorAt` and `nextCreditGrantAt`, write both audit events, and grant `Math.max(newTier.monthlyCredits - oldTier.monthlyCredits, 0)` once. Downgrades grant zero and never revoke existing credits.

`activateSubscription(input)` creates a source-`subscription` access grant and its first monthly credit grant in one `AdminTransactionRunner.run` call. `extendSubscriptionAccess(input)` locks the same grant and extends only its period/next billing metadata; monthly credit issuance remains owned by the monthly worker.

- [ ] **Step 5: Test the transaction rollback path**

Add a repository integration test proving that a duplicate open grant or failed difference-credit insert rolls back both the old-grant end and the new-grant insert.

- [ ] **Step 6: Run access tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/access && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/api/openapi.yaml src/app.module.ts src/modules/access
git commit -m "feat: add atomic access grant administration"
```

### Task 4: Implement Source-Aware Grant, Consume, Refund, and Revoke

**Files:**
- Create: `src/modules/credits/domain/credits.repository.ts`
- Create: `src/modules/credits/application/credit-grants.service.ts`
- Create: `src/modules/credits/application/credit-grants.service.spec.ts`
- Create: `src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Create: `src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`
- Create: `src/modules/credits/credits.module.ts`
- Modify: `src/modules/access/access.module.ts`

**Interfaces:**
- Consumes: effective access lookup from `AccessRepository.findEffectiveForUser(userId, at)`
- Produces: `grant`, `consume`, `refundOperation`, `revokeAdminCredits`, `summary`, and paged grant/ledger reads

- [ ] **Step 1: Define the application inputs and outputs in a failing test**

```ts
export interface GrantCreditsInput {
  userId: string;
  source: CreditSource;
  credits: number;
  grantedAt: Date;
  expiresAt: Date | null;
  accessGrantId: string | null;
  subscriptionId: string | null;
  paymentOrderId: string | null;
  operatorId: string | null;
  reason: string;
  idempotencyKey: string;
}

export interface CreditDebit {
  creditGrantId: string;
  credits: number;
  balanceAfter: number;
}
```

The exact service signatures are `grant(input, manager?: EntityManager)`, `consume(input, manager?: EntityManager)`, and `refundOperation(input, manager?: EntityManager)`. When `manager` is present, repositories bind to it and do not open a nested transaction; otherwise the service opens one short transaction with `AdminTransactionRunner`.

Test a 70-credit charge across a 50-credit expiring grant and a 100-credit non-expiring grant; expect debits `[{credits: 50}, {credits: 20}]` in that order.

- [ ] **Step 2: Run the focused test and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/credits/application/credit-grants.service.spec.ts`

Expected: FAIL because the credit service does not exist.

- [ ] **Step 3: Implement lock ordering and idempotency**

The repository method `lockSpendableGrants(userId, at)` must use:

```sql
ORDER BY expires_at ASC NULLS LAST, granted_at ASC, id ASC
FOR UPDATE
```

`consume` first verifies effective access, then locks grants and rejects with `INSUFFICIENT_CREDITS` before changing rows if the sum is too small. Each debit updates one grant and inserts one `operation_charge` ledger entry using reference key `${operationRunId}:${creditGrantId}`.

- [ ] **Step 4: Implement exact-grant refund**

`refundOperation(operationRunId, reason)` locks the run's charge entries, skips entries that already have matching `operation_refund`, restores each original `credit_grant_id`, and records one refund row per grant. An expired grant's stored balance is restored, but summary queries exclude it from spendable balance.

- [ ] **Step 5: Implement admin grant revocation bounds**

`revokeAdminCredits` accepts only grants with source `admin_adjustment` or `admin_plan`, requires `0 < credits <= remainingCredits`, and writes `admin_revoke`. It never overwrites a user's total balance.

- [ ] **Step 6: Add concurrency and idempotency repository tests**

Test that two concurrent consumes cannot make `remaining_credits` negative, duplicate `idempotency_key` returns the original grant, and duplicate refund produces no second ledger row.

- [ ] **Step 7: Run credit tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/credits && npm run build`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/modules/credits src/modules/access/access.module.ts
git commit -m "feat: implement source aware credit accounting"
```

### Task 5: Add Monthly Credit Recovery and User/Admin Read APIs

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Modify: `docs/api/openapi.yaml`
- Create: `src/modules/access/application/monthly-credit-grant.service.ts`
- Create: `src/modules/access/application/monthly-credit-grant.service.spec.ts`
- Create: `src/modules/access/application/monthly-credit-grant.scheduler.ts`
- Create: `src/modules/access/domain/month-anniversary.ts`
- Create: `src/modules/access/domain/month-anniversary.spec.ts`
- Create: `src/modules/access/presentation/current-access.controller.ts`
- Create: `src/modules/access/presentation/current-access.controller.spec.ts`
- Create: `src/modules/credits/presentation/credits.controller.ts`
- Create: `src/modules/credits/presentation/credits.controller.spec.ts`
- Create: `src/modules/credits/presentation/dto/list-credit-history-query.dto.ts`
- Create: `src/modules/credits/presentation/admin-member-credits.controller.ts`
- Create: `src/modules/credits/presentation/admin-member-credits.controller.spec.ts`
- Modify: `src/modules/access/access.module.ts`
- Modify: `src/modules/credits/credits.module.ts`
- Modify: `src/app.module.ts`

**Interfaces:**
- Consumes: `CreditGrantsService.grant` and catalog tier validity settings
- Produces: `GET /access/current`, `GET /credits/summary`, `GET /credits/grants`, `GET /credits/ledger`, and admin manual credit APIs

- [ ] **Step 1: Add the user and admin read/write contracts**

```text
GET  /access/current
GET  /credits/summary
GET  /credits/grants?limit={n}&cursor={cursor}
GET  /credits/ledger?limit={n}&cursor={cursor}
POST /admin/members/{userId}/credit-grants
POST /admin/members/{userId}/credit-grants/{creditGrantId}/revoke
GET  /admin/members/{userId}/credits/ledger?limit={n}&cursor={cursor}
```

`GET /access/current` returns `{ access: AccessView|null }`; `AccessView` includes grant/tier/source/start/end/next grant and sorted `allowedPluginKeys`. `GET /credits/summary` returns `{ heldBalance, spendableBalance, blockedReason, bySource }`, where `blockedReason` is `NO_ACTIVE_ACCESS` only when held balance exists but access is absent.

- [ ] **Step 2: Write failing anniversary and recovery tests**

```ts
expect(nextMonthAnniversary(new Date('2026-01-31T00:00:00Z'), new Date('2026-01-31T00:00:00Z')))
  .toEqual(new Date('2026-02-28T00:00:00Z'));

it('catches up each missed monthly grant exactly once', async () => {
  repo.findById.mockResolvedValue(access({ nextCreditGrantAt: new Date('2026-06-12T00:00:00Z') }));
  await service.processDueGrant('access-1', new Date('2026-08-12T01:00:00Z'));
  expect(credits.grant).toHaveBeenCalledTimes(3);
  expect(repo.advanceNextCreditGrantAt).toHaveBeenLastCalledWith(expect.anything(), new Date('2026-09-12T00:00:00Z'));
});
```

- [ ] **Step 3: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/access/domain/month-anniversary.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts`

Expected: FAIL because anniversary and recovery services do not exist.

- [ ] **Step 4: Install and wire the scheduler**

Run: `nvm use 22 && npm install @nestjs/schedule`

Add `ScheduleModule.forRoot()` once. `MonthlyCreditGrantScheduler` runs once per minute, selects due grant IDs without one global transaction, and calls `processDueGrant(id, now)` separately. The idempotency key is `monthly:${accessGrantId}:${creditPeriodStart.toISOString()}`.

- [ ] **Step 5: Implement full-credit final partial periods**

When `nextCreditGrantAt < endsAt`, grant the tier's full `monthlyCredits` even if the remaining interval is shorter than a month. Never create a grant at or after `endsAt`. `expiresAt` is `grantedAt + monthlyCreditValidityDays` when configured, otherwise `null`.

- [ ] **Step 6: Add authenticated controllers and admin request DTOs**

Use the existing user JWT guard and operator JWT guard. Manual admin credit input is `{ credits, expiresAt: string|null, reason, requestKey }`; exact expiry is intentionally chosen per adjustment and recorded in the grant.

- [ ] **Step 7: Run access/credit tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/access src/modules/credits && npm run build`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add package.json package-lock.json docs/api/openapi.yaml src/app.module.ts src/modules/access src/modules/credits
git commit -m "feat: expose access credit APIs and monthly grants"
```

### Task 6: Cut Operations Over to Entitlement-Aware Grant Accounting

**Files:**
- Modify: `docs/api/openapi.yaml`
- Create: `src/core/database/migrations/admin/1786650000000-AddOperationPluginEntitlements.ts`
- Create: `src/core/database/migrations/admin/1786650000000-AddOperationPluginEntitlements.spec.ts`
- Modify: `src/modules/operations/domain/operation-definitions.ts`
- Modify: `src/modules/operations/domain/operation-definitions.spec.ts`
- Modify: `src/modules/operations/domain/operations.repository.ts`
- Modify: `src/modules/operations/application/operations.service.ts`
- Modify: `src/modules/operations/application/operations.service.spec.ts`
- Modify: `src/modules/operations/infrastructure/operation-policy.entity.ts`
- Modify: `src/modules/operations/infrastructure/typeorm-operations.repository.ts`
- Delete: `src/modules/operations/infrastructure/credit-ledger.entity.ts`
- Modify: `src/modules/operations/operations.module.ts`
- Modify: `src/modules/operations/presentation/operations.controller.ts`
- Modify: `src/modules/operations/presentation/operations.controller.spec.ts`

**Interfaces:**
- Consumes: `AccessGrantsService.current(userId)` and `CreditGrantsService.consume/refundOperation`
- Produces: entitlement-aware operation quote/start/fail with error reasons `NO_ACTIVE_ACCESS`, `PLUGIN_NOT_ENTITLED`, `INSUFFICIENT_CREDITS`

- [ ] **Step 1: Replace the OpenAPI quote reason and operation keys**

The exact operation-to-plugin mapping is:

```ts
const OPERATION_PLUGIN_KEYS = {
  'shortform_url.create': 'shortform_url',
  'shortform_paste.create': 'shortform_paste',
  'shortform_prompt.create': 'shortform_prompt',
  'dialog_highlight.extract': 'dialog_highlight',
  'dance_highlight.extract': 'dance_highlight',
  'variation.render': 'variation',
} as const;
```

Split legacy `shortform.create` into three policies with the same initial cost. This lets the server derive the entitlement from `operationKey` instead of trusting a client-supplied `pluginKey`.

- [ ] **Step 2: Write failing permission-order and refund tests**

```ts
it.each([
  [null, 'NO_ACTIVE_ACCESS'],
  [access({ pluginKeys: [] }), 'PLUGIN_NOT_ENTITLED'],
])('denies before inspecting balance', async (currentAccess, reason) => {
  accessService.current.mockResolvedValue(currentAccess);
  await expect(service.quote(userId, 'variation.render', {})).resolves.toMatchObject({ canStart: false, reason });
  expect(credits.summary).not.toHaveBeenCalled();
});

it('commits debits and running operation before external work begins', async () => {
  const run = await service.start(userId, 'variation.render', {});
  expect(run.status).toBe('running');
  expect(credits.consume).toHaveBeenCalledWith(expect.objectContaining({ operationRunId: run.id }));
});
```

- [ ] **Step 3: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/operations/application/operations.service.spec.ts src/modules/operations/domain/operation-definitions.spec.ts`

Expected: FAIL on old license and single-balance behavior.

- [ ] **Step 4: Add `plugin_key` to policies and seed split shortform operations**

The migration adds non-null `plugin_key`, deletes the prelaunch `shortform.create` policy, and inserts the three new policies. Existing highlight and variation rows receive the exact mapping above.

- [ ] **Step 5: Replace operation charge/refund calls**

`quote` checks access, plugin membership, then spendable total. `start` opens `AdminTransactionRunner.run`, creates the run with the provided `EntityManager`, and calls `credits.consume(input, manager)` before committing. `succeed` only marks the run in another short transaction. `fail` opens a separate `AdminTransactionRunner.run`, calls `credits.refundOperation(input, manager)`, and marks failed before committing. Repeated failure/refund is idempotent.

- [ ] **Step 6: Remove old operation-only ledger endpoints and entity**

Replace `GET /operations/ledger` with the new `GET /credits/ledger` contract. Keep operation-run session metadata as nullable presentation enrichment when listing credit ledger entries; the ledger itself remains source/grant based.

- [ ] **Step 7: Run operations tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/operations src/modules/credits src/modules/access && npm run build`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add docs/api/openapi.yaml src/core/database/migrations/admin/1786650000000-* src/modules/operations src/modules/credits src/modules/access
git commit -m "feat: enforce plugin access in credit charged operations"
```
