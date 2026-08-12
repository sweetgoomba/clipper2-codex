# Billing Product Catalog Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an additive, production-shaped product catalog that separates plan tiers, billing products, and plugin entitlements without changing the current Toss review checkout or legacy `/plans` flow.

**Architecture:** Create a new `catalog` module in `clipper_web_api` backed by three new admin-DB tables. The public API returns only active tiers and products, while operator-protected APIs manage inactive and active catalog records. This phase deliberately coexists with the legacy `billing` module so dev review checkout remains runnable throughout the work.

**Tech Stack:** Node.js version from `web/clipper_web_api/.nvmrc`, NestJS 11, TypeScript 5.7, TypeORM/PostgreSQL, Jest 30, class-validator, OpenAPI YAML.

## Global Constraints

- The approved design is `.codex/design/2026-08-12-billing-subscription-credit-policy-design.md`.
- All planning and handoff documents stay under `.codex`; code changes belong in their owning repository.
- Execute this plan on a new `feat/billing-product-catalog-foundation` branch in `web/clipper_web_api`.
- Do not edit an already-applied migration. Add a new forward migration to the admin datasource.
- Keep `GET /plans`, `POST /payments/review/checkout`, `PlansService`, `plans`, `purchase_requests`, and `licenses` unchanged in this phase.
- Do not seed real product names, prices, plugin mappings, or credit quantities; those product values are not approved yet.
- New catalog records are inactive by default and therefore cannot accidentally appear in the public catalog.
- Public success responses remain raw objects or arrays; do not introduce a response envelope.
- Admin endpoints use the existing `OperatorJwtGuard`.
- Admin DB columns are explicit snake_case and `synchronize` remains `false`.
- Backend imports use relative paths with `.js` extensions.
- Do not add a plugin registry, subscription table, credit grant, Toss fulfillment, scheduler, frontend screen, or legacy cleanup in this phase.
- Use TDD for every behavior change: failing focused test, minimal implementation, passing focused test, then commit.

---

## Roadmap and Plan Boundary

The approved design spans multiple independently testable subsystems. Implement them as separate plans in this order:

1. **Product catalog foundation — this plan:** plan tiers, sellable billing products, plugin entitlement keys, public/admin catalog APIs.
2. **Access and credit foundation:** one base access source, credit grants, source-aware ledger, earliest-expiry consumption, operation refund migration.
3. **Administrator grants:** standard plan assignment, arbitrary start/end dates, monthly full-credit grants, manual credit grants and audit history.
4. **Authenticated Toss subscription checkout:** logged-in user orders, billing-key ownership, server-confirmed initial payment, idempotent subscription fulfillment.
5. **Recurring lifecycle:** monthly benefit grants, renewal charging, `past_due` grace and retry, reconciliation and stop behavior.
6. **Plan changes and cancellation:** immediate prorated upgrade, next-renewal downgrade/interval change, next-payment cancellation.
7. **Client and legacy cutover:** web pricing/account/admin/desktop contracts, source-visible credit UI, remove bank-transfer purchase request and legacy license code.
8. **Refund and production readiness:** legally reviewed refund formula, Toss production keys, review-mode shutdown, retention/operations runbook.

Do not draft executable detail for phases 2–8 until the preceding phase is implemented and reviewed. Their exact file paths and interfaces depend on the code that actually lands.

## Phase 1 File Map

### Create in `web/clipper_web_api`

- `src/modules/catalog/domain/product-catalog.model.ts` — stable domain shapes and create/update inputs.
- `src/modules/catalog/domain/product-catalog.repository.ts` — persistence port used by the service.
- `src/modules/catalog/application/product-catalog.service.ts` — filtering, validation, active product lookup, and orchestration.
- `src/modules/catalog/application/product-catalog.service.spec.ts` — catalog policy tests with an in-memory repository.
- `src/modules/catalog/infrastructure/plan-tier.entity.ts` — `plan_tiers` TypeORM mapping.
- `src/modules/catalog/infrastructure/billing-product.entity.ts` — `billing_products` TypeORM mapping.
- `src/modules/catalog/infrastructure/plan-plugin-entitlement.entity.ts` — tier-to-plugin mapping.
- `src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts` — admin-DB repository implementation.
- `src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts` — mapping, replacement, and DB conflict tests.
- `src/modules/catalog/presentation/catalog.controller.ts` — unauthenticated active catalog endpoint.
- `src/modules/catalog/presentation/admin-catalog.controller.ts` — operator catalog endpoints.
- `src/modules/catalog/presentation/catalog.controller.spec.ts` — public response contract test.
- `src/modules/catalog/presentation/admin-catalog.controller.spec.ts` — admin DTO-to-service mapping tests.
- `src/modules/catalog/presentation/dto/create-plan-tier.dto.ts` — tier creation validation.
- `src/modules/catalog/presentation/dto/update-plan-tier.dto.ts` — tier patch validation.
- `src/modules/catalog/presentation/dto/replace-tier-plugins.dto.ts` — plugin-key list validation.
- `src/modules/catalog/presentation/dto/create-billing-product.dto.ts` — product creation validation.
- `src/modules/catalog/presentation/dto/update-billing-product.dto.ts` — product patch validation.
- `src/modules/catalog/catalog.module.ts` — TypeORM registration and dependency binding.
- `src/core/database/migrations/admin/1786500000000-CreateProductCatalog.ts` — additive catalog tables.
- `src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts` — migration SQL regression test.

### Modify in `web/clipper_web_api`

- `docs/api/openapi.yaml` — additive public and admin catalog contract.
- `src/app.module.ts` — import `CatalogModule`.
- `src/core/database/admin.datasource.ts` — register three entities and the new migration.

### Explicitly unchanged

- `src/modules/billing/**`
- `src/modules/payments/**`
- `web/clipper_web_client/**`
- `web/clipper_web_admin/**`
- `desktop/**`
- `web/clipper_infra/**`

---

### Task 1: Define the additive OpenAPI contract

**Files:**

- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**

- Produces: `PlanTier`, `BillingProduct`, `CatalogTier`, `AdminCatalog`, and five request schemas.
- Produces: `GET /catalog`, `GET /admin/catalog`, `POST /admin/catalog/tiers`, `PATCH /admin/catalog/tiers/{id}`, `PUT /admin/catalog/tiers/{id}/plugins`, `POST /admin/catalog/products`, and `PATCH /admin/catalog/products/{id}`.
- Preserves: existing `/plans` and `/admin/plans` schemas and paths unchanged.

- [ ] **Step 1: Add the component schemas**

Add these exact field names to `components.schemas`. Reuse the repository's existing `ErrorResponse` schema for errors.

```yaml
    PlanTier:
      type: object
      required: [id, code, name, description, sortOrder, monthlyCredits, pluginKeys, isActive, createdAt, updatedAt]
      properties:
        id: { type: string, format: uuid }
        code: { type: string, pattern: '^[a-z][a-z0-9_-]{0,49}$' }
        name: { type: string, minLength: 1, maxLength: 80 }
        description:
          oneOf:
            - { type: string, maxLength: 500 }
            - { type: 'null' }
        sortOrder: { type: integer, minimum: 0 }
        monthlyCredits: { type: integer, minimum: 0 }
        pluginKeys:
          type: array
          uniqueItems: true
          maxItems: 100
          items: { type: string, pattern: '^[a-z][a-z0-9._-]{0,99}$' }
        isActive: { type: boolean }
        createdAt: { type: string, format: date-time }
        updatedAt: { type: string, format: date-time }

    BillingProduct:
      type: object
      additionalProperties: false
      required: [id, code, tierId, name, billingIntervalMonths, priceKrw, autoRenews, isActive, createdAt, updatedAt]
      properties:
        id: { type: string, format: uuid }
        code: { type: string, pattern: '^[a-z][a-z0-9_-]{0,49}$' }
        tierId: { type: string, format: uuid }
        name: { type: string, minLength: 1, maxLength: 100 }
        billingIntervalMonths: { type: integer, minimum: 1 }
        priceKrw: { type: integer, minimum: 1 }
        autoRenews: { type: boolean }
        isActive: { type: boolean }
        createdAt: { type: string, format: date-time }
        updatedAt: { type: string, format: date-time }

    CatalogTier:
      allOf:
        - $ref: '#/components/schemas/PlanTier'
        - type: object
          required: [products]
          properties:
            products:
              type: array
              items: { $ref: '#/components/schemas/BillingProduct' }

    AdminCatalog:
      type: object
      additionalProperties: false
      required: [tiers, products]
      properties:
        tiers:
          type: array
          items: { $ref: '#/components/schemas/PlanTier' }
        products:
          type: array
          items: { $ref: '#/components/schemas/BillingProduct' }
```

Add request schemas with these required and mutable fields:

```yaml
    CreatePlanTierRequest:
      type: object
      additionalProperties: false
      required: [code, name, sortOrder, monthlyCredits]
      properties:
        code: { type: string, pattern: '^[a-z][a-z0-9_-]{0,49}$' }
        name: { type: string, minLength: 1, maxLength: 80 }
        description: { type: string, maxLength: 500 }
        sortOrder: { type: integer, minimum: 0 }
        monthlyCredits: { type: integer, minimum: 0 }

    UpdatePlanTierRequest:
      type: object
      additionalProperties: false
      minProperties: 1
      properties:
        name: { type: string, minLength: 1, maxLength: 80 }
        description:
          oneOf:
            - { type: string, maxLength: 500 }
            - { type: 'null' }
        sortOrder: { type: integer, minimum: 0 }
        monthlyCredits: { type: integer, minimum: 0 }
        isActive: { type: boolean }

    ReplaceTierPluginsRequest:
      type: object
      additionalProperties: false
      required: [pluginKeys]
      properties:
        pluginKeys:
          type: array
          uniqueItems: true
          maxItems: 100
          items: { type: string, pattern: '^[a-z][a-z0-9._-]{0,99}$' }

    CreateBillingProductRequest:
      type: object
      additionalProperties: false
      required: [code, tierId, name, billingIntervalMonths, priceKrw, autoRenews]
      properties:
        code: { type: string, pattern: '^[a-z][a-z0-9_-]{0,49}$' }
        tierId: { type: string, format: uuid }
        name: { type: string, minLength: 1, maxLength: 100 }
        billingIntervalMonths: { type: integer, minimum: 1 }
        priceKrw: { type: integer, minimum: 1 }
        autoRenews: { type: boolean }

    UpdateBillingProductRequest:
      type: object
      additionalProperties: false
      minProperties: 1
      properties:
        name: { type: string, minLength: 1, maxLength: 100 }
        billingIntervalMonths: { type: integer, minimum: 1 }
        priceKrw: { type: integer, minimum: 1 }
        autoRenews: { type: boolean }
        isActive: { type: boolean }
```

- [ ] **Step 2: Add public and operator paths**

Use these response shapes and security rules:

```yaml
  /catalog:
    get:
      operationId: getProductCatalog
      summary: List active plan tiers and sellable billing products
      tags: [catalog]
      security: []
      responses:
        '200':
          description: Active tiers with active products, sorted for display.
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/CatalogTier' }

  /admin/catalog:
    get:
      operationId: adminGetProductCatalog
      tags: [admin, catalog]
      security: [{ bearerAuth: [] }]
      responses:
        '200':
          description: All active and inactive catalog records.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/AdminCatalog' }
```

Add the five mutation operations listed in the Interfaces block. Apply the matching request schema, UUID path parameters, `OperatorJwtGuard`-compatible bearer security, and these success responses:

```text
POST  /admin/catalog/tiers                 -> 201 PlanTier
PATCH /admin/catalog/tiers/{id}            -> 200 PlanTier
PUT   /admin/catalog/tiers/{id}/plugins    -> 200 PlanTier
POST  /admin/catalog/products              -> 201 BillingProduct
PATCH /admin/catalog/products/{id}         -> 200 BillingProduct
```

Document `400`, `401`, `403`, `404`, and `409` with the existing `ErrorResponse`. Do not add DELETE endpoints; deactivation is the supported removal mechanism.

- [ ] **Step 3: Validate the YAML and confirm legacy paths remain**

Run:

```bash
cd web/clipper_web_api
ruby -e "require 'yaml'; YAML.load_file('docs/api/openapi.yaml', aliases: true); puts 'openapi yaml ok'"
rg -n '^  /catalog:|^  /admin/catalog|^  /plans:|^  /admin/plans' docs/api/openapi.yaml
```

Expected:

```text
openapi yaml ok
```

The search output contains all new catalog paths and both legacy plan paths.

- [ ] **Step 4: Commit the contract**

```bash
git add docs/api/openapi.yaml
git commit -m "docs(catalog): define product catalog API"
```

---

### Task 2: Add the product catalog migration and entity mappings

**Files:**

- Create: `web/clipper_web_api/src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/admin/1786500000000-CreateProductCatalog.ts`
- Create: `web/clipper_web_api/src/modules/catalog/infrastructure/plan-tier.entity.ts`
- Create: `web/clipper_web_api/src/modules/catalog/infrastructure/billing-product.entity.ts`
- Create: `web/clipper_web_api/src/modules/catalog/infrastructure/plan-plugin-entitlement.entity.ts`

**Interfaces:**

- Produces tables: `plan_tiers`, `billing_products`, `plan_plugin_entitlements`.
- Produces entities: `PlanTierEntity`, `BillingProductEntity`, `PlanPluginEntitlementEntity`.
- Does not modify or reference the legacy `plans` table.

- [ ] **Step 1: Write the failing migration regression test**

```ts
import { CreateProductCatalog1786500000000 } from './1786500000000-CreateProductCatalog.js';

describe('CreateProductCatalog1786500000000', () => {
  it('creates independent tier, product, and plugin entitlement tables', async () => {
    const sql: string[] = [];
    const queryRunner = { query: async (statement: string) => { sql.push(statement); } } as any;

    await new CreateProductCatalog1786500000000().up(queryRunner);

    const joined = sql.join('\n');
    expect(joined).toContain('CREATE TABLE plan_tiers');
    expect(joined).toContain('CREATE TABLE billing_products');
    expect(joined).toContain('CREATE TABLE plan_plugin_entitlements');
    expect(joined).toContain('billing_interval_months');
    expect(joined).toContain('monthly_credits');
    expect(joined).not.toContain('INSERT INTO plan_tiers');
    expect(joined).not.toContain('DROP TABLE plans');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts
```

Expected: FAIL because `1786500000000-CreateProductCatalog.ts` does not exist.

- [ ] **Step 3: Implement the additive migration**

Create the migration with these constraints:

```sql
CREATE TABLE plan_tiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(50) NOT NULL UNIQUE,
  name varchar(80) NOT NULL,
  description varchar(500),
  sort_order int NOT NULL CHECK (sort_order >= 0),
  monthly_credits int NOT NULL CHECK (monthly_credits >= 0),
  is_active boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
)
```

```sql
CREATE TABLE billing_products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(50) NOT NULL UNIQUE,
  plan_tier_id uuid NOT NULL REFERENCES plan_tiers(id) ON DELETE RESTRICT,
  name varchar(100) NOT NULL,
  billing_interval_months int NOT NULL CHECK (billing_interval_months > 0),
  price_krw int NOT NULL CHECK (price_krw > 0),
  auto_renews boolean NOT NULL,
  is_active boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
)
```

```sql
CREATE TABLE plan_plugin_entitlements (
  plan_tier_id uuid NOT NULL REFERENCES plan_tiers(id) ON DELETE CASCADE,
  plugin_key varchar(100) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (plan_tier_id, plugin_key)
)
```

Add indexes on `plan_tiers (is_active, sort_order)`, `billing_products (plan_tier_id, is_active)`, and `plan_plugin_entitlements (plugin_key)`. The `down()` method drops the three new tables in reverse dependency order. Do not seed product data.

- [ ] **Step 4: Add explicit TypeORM entity mappings**

Use these properties and column names:

```ts
// PlanTierEntity
id: string;
code: string;
name: string;
description: string | null;
sortOrder: number;              // sort_order
monthlyCredits: number;         // monthly_credits
isActive: boolean;              // is_active, default false
createdAt: Date;                // created_at
updatedAt: Date;                // updated_at
```

```ts
// BillingProductEntity
id: string;
code: string;
planTierId: string;             // plan_tier_id
name: string;
billingIntervalMonths: number;  // billing_interval_months
priceKrw: number;               // price_krw
autoRenews: boolean;            // auto_renews
isActive: boolean;              // is_active, default false
createdAt: Date;
updatedAt: Date;
```

```ts
// PlanPluginEntitlementEntity
planTierId: string;             // plan_tier_id, primary column
pluginKey: string;              // plugin_key, primary column
createdAt: Date;
```

Use `@Column({ name: ... })` for every snake_case mapping, `@CreateDateColumn`/`@UpdateDateColumn` for timestamps, and the same indexes as the migration.

- [ ] **Step 5: Run the focused test and compile check**

```bash
npm test -- --runInBand src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts
npm run build
```

Expected: migration spec PASS and Nest build exit 0.

- [ ] **Step 6: Commit the schema foundation**

```bash
git add src/core/database/migrations/admin/1786500000000-CreateProductCatalog.ts \
  src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts \
  src/modules/catalog/infrastructure/plan-tier.entity.ts \
  src/modules/catalog/infrastructure/billing-product.entity.ts \
  src/modules/catalog/infrastructure/plan-plugin-entitlement.entity.ts
git commit -m "feat(catalog): add product catalog schema"
```

---

### Task 3: Define the catalog domain and application policy

**Files:**

- Create: `web/clipper_web_api/src/modules/catalog/domain/product-catalog.model.ts`
- Create: `web/clipper_web_api/src/modules/catalog/domain/product-catalog.repository.ts`
- Create: `web/clipper_web_api/src/modules/catalog/application/product-catalog.service.spec.ts`
- Create: `web/clipper_web_api/src/modules/catalog/application/product-catalog.service.ts`

**Interfaces:**

- Produces domain types: `PlanTier`, `BillingProduct`, `CatalogTier`, `AdminCatalog`.
- Produces repository port: `ProductCatalogRepository`.
- Produces service methods used by controllers and future checkout: `publicCatalog()`, `adminCatalog()`, `activeProductById()`, `createTier()`, `updateTier()`, `replaceTierPlugins()`, `createProduct()`, `updateProduct()`.

- [ ] **Step 1: Write the model and repository contracts**

Use these exact domain fields:

```ts
export interface PlanTier {
  id: string;
  code: string;
  name: string;
  description: string | null;
  sortOrder: number;
  monthlyCredits: number;
  pluginKeys: string[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface BillingProduct {
  id: string;
  code: string;
  tierId: string;
  name: string;
  billingIntervalMonths: number;
  priceKrw: number;
  autoRenews: boolean;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface CatalogTier extends PlanTier {
  products: BillingProduct[];
}

export interface AdminCatalog {
  tiers: PlanTier[];
  products: BillingProduct[];
}
```

Define controller-facing inputs, repository-facing inputs, and patches exactly as follows. `code` and product `tierId` are immutable after creation.

```ts
export interface CreatePlanTierInput {
  code: string;
  name: string;
  description?: string;
  sortOrder: number;
  monthlyCredits: number;
}

export interface NewPlanTier {
  code: string;
  name: string;
  description: string | null;
  sortOrder: number;
  monthlyCredits: number;
  isActive: boolean;
}

export interface PlanTierPatch {
  name?: string;
  description?: string | null;
  sortOrder?: number;
  monthlyCredits?: number;
  isActive?: boolean;
}

export interface CreateBillingProductInput {
  code: string;
  tierId: string;
  name: string;
  billingIntervalMonths: number;
  priceKrw: number;
  autoRenews: boolean;
}

export interface NewBillingProduct extends CreateBillingProductInput {
  isActive: boolean;
}

export interface BillingProductPatch {
  name?: string;
  billingIntervalMonths?: number;
  priceKrw?: number;
  autoRenews?: boolean;
  isActive?: boolean;
}
```

Use this repository port:

```ts
export abstract class ProductCatalogRepository {
  abstract listTiers(): Promise<PlanTier[]>;
  abstract findTierById(id: string): Promise<PlanTier | undefined>;
  abstract createTier(input: NewPlanTier): Promise<PlanTier>;
  abstract updateTier(id: string, patch: PlanTierPatch): Promise<PlanTier>;
  abstract replaceTierPlugins(id: string, pluginKeys: string[]): Promise<PlanTier>;
  abstract listProducts(): Promise<BillingProduct[]>;
  abstract findProductById(id: string): Promise<BillingProduct | undefined>;
  abstract createProduct(input: NewBillingProduct): Promise<BillingProduct>;
  abstract updateProduct(id: string, patch: BillingProductPatch): Promise<BillingProduct>;
}
```

- [ ] **Step 2: Write failing service tests**

Create an in-memory implementation of `ProductCatalogRepository` inside the spec and cover these exact cases:

```ts
it('publicCatalog returns only active tiers and active products in display order');
it('publicCatalog omits active products whose tier is inactive');
it('adminCatalog returns active and inactive records');
it('activeProductById rejects a missing, inactive, or inactive-tier product');
it('createTier always creates an inactive tier');
it('createProduct rejects an unknown tier and always creates an inactive product');
it('replaceTierPlugins rejects an unknown tier and returns sorted unique keys');
it('updateTier and updateProduct reject unknown ids');
```

The primary assertion should demonstrate the separation explicitly:

```ts
expect(await service.publicCatalog()).toEqual([
  expect.objectContaining({
    code: 'pro',
    monthlyCredits: 1000,
    pluginKeys: ['dialog-highlight', 'shortform-studio'],
    products: [
      expect.objectContaining({ code: 'pro-monthly', billingIntervalMonths: 1 }),
      expect.objectContaining({ code: 'pro-yearly', billingIntervalMonths: 12 }),
    ],
  }),
]);
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
npm test -- --runInBand src/modules/catalog/application/product-catalog.service.spec.ts
```

Expected: FAIL because `ProductCatalogService` does not exist.

- [ ] **Step 4: Implement the minimal application service**

Use this public filtering behavior:

```ts
async publicCatalog(): Promise<CatalogTier[]> {
  const [tiers, products] = await Promise.all([
    this.repo.listTiers(),
    this.repo.listProducts(),
  ]);
  return tiers
    .filter((tier) => tier.isActive)
    .sort((a, b) => a.sortOrder - b.sortOrder || a.code.localeCompare(b.code))
    .map((tier) => ({
      ...tier,
      pluginKeys: [...tier.pluginKeys].sort(),
      products: products
        .filter((product) => product.isActive && product.tierId === tier.id)
        .sort((a, b) => a.billingIntervalMonths - b.billingIntervalMonths || a.code.localeCompare(b.code)),
    }));
}
```

Implement `activeProductById(id)` so it returns a product only when both product and parent tier are active; otherwise throw `NotFoundException('billing product not found')`.

`createTier(input: CreatePlanTierInput)` normalizes a missing description to `null` and passes `isActive: false` to the repository. `createProduct(input: CreateBillingProductInput)` verifies its tier exists and passes `isActive: false`. Update methods first verify the row exists and throw `NotFoundException` on a missing ID. `replaceTierPlugins()` normalizes keys with `new Set(pluginKeys.map((key) => key.trim()))` and sorts them before persistence.

- [ ] **Step 5: Run the service tests**

```bash
npm test -- --runInBand src/modules/catalog/application/product-catalog.service.spec.ts
```

Expected: all eight cases PASS.

- [ ] **Step 6: Commit the domain and service**

```bash
git add src/modules/catalog/domain src/modules/catalog/application
git commit -m "feat(catalog): add product catalog policy"
```

---

### Task 4: Implement TypeORM persistence

**Files:**

- Create: `web/clipper_web_api/src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts`
- Create: `web/clipper_web_api/src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts`

**Interfaces:**

- Consumes: all methods and inputs from `ProductCatalogRepository`.
- Produces: `TypeOrmProductCatalogRepository` for `CatalogModule` dependency injection.
- Guarantees: plugin replacement is atomic and duplicate `code` values become HTTP 409 conflicts.

- [ ] **Step 1: Write failing repository tests**

Use mocked TypeORM repositories and a mocked transaction manager. Cover:

```ts
it('maps tier entity fields and sorted plugin keys to PlanTier');
it('maps planTierId to BillingProduct.tierId');
it('replaceTierPlugins deletes and inserts within one transaction');
it('maps Postgres 23505 on tier or product code to ConflictException');
it('rethrows non-unique database errors');
```

For the transaction assertion, use this shape:

```ts
expect(dataSource.transaction).toHaveBeenCalledTimes(1);
expect(pluginRepository.delete).toHaveBeenCalledWith({ planTierId: 'tier-1' });
expect(pluginRepository.save).toHaveBeenCalledWith([
  expect.objectContaining({ planTierId: 'tier-1', pluginKey: 'a.plugin' }),
  expect.objectContaining({ planTierId: 'tier-1', pluginKey: 'b.plugin' }),
]);
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
npm test -- --runInBand src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts
```

Expected: FAIL because the TypeORM repository does not exist.

- [ ] **Step 3: Implement entity-to-domain mapping**

Inject the named admin datasource:

```ts
constructor(@InjectDataSource('admin') private readonly dataSource: DataSource) {
  super();
}
```

Load tier rows and entitlement rows, group plugin keys by `planTierId`, and return each tier with sorted keys. Use explicit repository calls rather than cross-database joins; all three catalog tables are in the admin DB.

Map products exactly as follows:

```ts
private toProduct(row: BillingProductEntity): BillingProduct {
  return {
    id: row.id,
    code: row.code,
    tierId: row.planTierId,
    name: row.name,
    billingIntervalMonths: row.billingIntervalMonths,
    priceKrw: row.priceKrw,
    autoRenews: row.autoRenews,
    isActive: row.isActive,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
  };
}
```

- [ ] **Step 4: Implement atomic plugin replacement and conflict mapping**

`replaceTierPlugins()` must:

1. Start `dataSource.transaction()`.
2. Load and reject a missing tier with `NotFoundException('plan tier not found')`.
3. Delete all existing mappings for the tier.
4. Insert the normalized list supplied by the service.
5. Return the tier with exactly the new plugin keys.

Wrap `createTier()` and `createProduct()` persistence errors. If `QueryFailedError.driverError.code === '23505'`, throw `ConflictException('catalog code already exists')`; rethrow every other error unchanged.

- [ ] **Step 5: Run repository and service tests**

```bash
npm test -- --runInBand \
  src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts \
  src/modules/catalog/application/product-catalog.service.spec.ts
```

Expected: all catalog repository and service tests PASS.

- [ ] **Step 6: Commit persistence**

```bash
git add src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts \
  src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts
git commit -m "feat(catalog): persist product catalog records"
```

---

### Task 5: Expose public and operator controllers

**Files:**

- Create: `web/clipper_web_api/src/modules/catalog/presentation/dto/create-plan-tier.dto.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/dto/update-plan-tier.dto.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/dto/replace-tier-plugins.dto.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/dto/create-billing-product.dto.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/dto/update-billing-product.dto.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/catalog.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/catalog.controller.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/admin-catalog.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/catalog/presentation/admin-catalog.controller.ts`

**Interfaces:**

- Consumes: `ProductCatalogService` methods from Task 3.
- Produces: HTTP behavior matching Task 1 exactly.

- [ ] **Step 1: Add DTO validation rules**

Use these regex constants in the DTO layer:

```ts
export const CATALOG_CODE_PATTERN = /^[a-z][a-z0-9_-]{0,49}$/;
export const PLUGIN_KEY_PATTERN = /^[a-z][a-z0-9._-]{0,99}$/;
```

Apply these class-validator rules:

```text
code: string, non-empty, max 50, CATALOG_CODE_PATTERN
name: string, non-empty, max 80 for tiers and 100 for products
description: optional string, max 500; update accepts null by declaring string | null and ValidateIf
sortOrder: integer >= 0
monthlyCredits: integer >= 0
tierId: UUID
billingIntervalMonths: integer >= 1
priceKrw: integer >= 1
autoRenews/isActive: boolean
pluginKeys: array, max 100, unique, each string matching PLUGIN_KEY_PATTERN
```

Create DTOs do not expose `isActive`. Update DTOs do not expose immutable `code` or `tierId`.

- [ ] **Step 2: Write failing controller tests**

Public test:

```ts
it('GET /catalog returns ProductCatalogService.publicCatalog raw');
```

Admin tests:

```ts
it('GET returns adminCatalog raw');
it('POST tier forwards only create-tier fields');
it('PATCH tier forwards mutable fields including isActive');
it('PUT plugins forwards the pluginKeys array');
it('POST product forwards product creation fields');
it('PATCH product forwards mutable product fields');
```

Use a fake service and assert exact calls, for example:

```ts
expect(service.createProduct).toHaveBeenCalledWith({
  code: 'pro-monthly',
  tierId: '00000000-0000-4000-8000-000000000001',
  name: 'Pro 월간',
  billingIntervalMonths: 1,
  priceKrw: 19900,
  autoRenews: true,
});
```

- [ ] **Step 3: Run controller tests to verify they fail**

```bash
npm test -- --runInBand \
  src/modules/catalog/presentation/catalog.controller.spec.ts \
  src/modules/catalog/presentation/admin-catalog.controller.spec.ts
```

Expected: FAIL because the controllers do not exist.

- [ ] **Step 4: Implement the public controller**

```ts
@Controller('catalog')
export class CatalogController {
  constructor(private readonly catalog: ProductCatalogService) {}

  @Get()
  list() {
    return this.catalog.publicCatalog();
  }
}
```

Do not add an auth guard to the public controller.

- [ ] **Step 5: Implement the operator controller**

Use:

```ts
@Controller('admin/catalog')
@UseGuards(OperatorJwtGuard)
@UsePipes(new ValidationPipe({ whitelist: true, transform: true }))
```

Map methods exactly:

```text
GET    /admin/catalog                       -> adminCatalog()
POST   /admin/catalog/tiers                 -> createTier(dto)
PATCH  /admin/catalog/tiers/:id             -> updateTier(id, dto)
PUT    /admin/catalog/tiers/:id/plugins     -> replaceTierPlugins(id, dto.pluginKeys)
POST   /admin/catalog/products              -> createProduct(dto)
PATCH  /admin/catalog/products/:id          -> updateProduct(id, dto)
```

Use `ParseUUIDPipe` for all ID parameters. Return service values raw.

- [ ] **Step 6: Run DTO and controller tests**

```bash
npm test -- --runInBand src/modules/catalog/presentation
```

Expected: all catalog presentation tests PASS.

- [ ] **Step 7: Commit the HTTP layer**

```bash
git add src/modules/catalog/presentation
git commit -m "feat(catalog): expose product catalog APIs"
```

---

### Task 6: Wire the module and migration into the application

**Files:**

- Create: `web/clipper_web_api/src/modules/catalog/catalog.module.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_api/src/core/database/admin.datasource.ts`

**Interfaces:**

- Consumes: entities, repository, service, and controllers from Tasks 2–5.
- Produces: bootable Nest module and runnable admin migration.
- Exports: `ProductCatalogService` for the future authenticated payment module.

- [ ] **Step 1: Write the catalog module**

```ts
@Module({
  imports: [
    TypeOrmModule.forFeature(
      [PlanTierEntity, BillingProductEntity, PlanPluginEntitlementEntity],
      'admin',
    ),
    AuthModule,
  ],
  controllers: [CatalogController, AdminCatalogController],
  providers: [
    ProductCatalogService,
    { provide: ProductCatalogRepository, useClass: TypeOrmProductCatalogRepository },
  ],
  exports: [ProductCatalogService],
})
export class CatalogModule {}
```

- [ ] **Step 2: Register the module in AppModule**

Import `CatalogModule` using a relative `.js` path and add it to `imports`. Do not remove `BillingModule` or `PaymentsModule`.

- [ ] **Step 3: Register datasource entities and migration**

In `admin.datasource.ts`:

1. Import the three catalog entities.
2. Add all three to `entities`.
3. Import `CreateProductCatalog1786500000000`.
4. Append it after `CreatePaymentOrders1786300000000` in `migrations`.

- [ ] **Step 4: Run the full catalog test set**

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/catalog src/core/database/migrations/admin/1786500000000-CreateProductCatalog.spec.ts
```

Expected: every catalog and migration test PASS.

- [ ] **Step 5: Run the API build and regression tests**

```bash
npm run build
npm test -- --runInBand \
  src/modules/billing/application/plans.service.spec.ts \
  src/modules/payments/application/review-payments.service.spec.ts \
  src/modules/payments/presentation/review-payments.controller.spec.ts
```

Expected:

- Nest build exits 0.
- Legacy plans and Toss review tests remain PASS.

- [ ] **Step 6: Commit module wiring**

```bash
git add src/modules/catalog/catalog.module.ts src/app.module.ts src/core/database/admin.datasource.ts
git commit -m "feat(catalog): register product catalog module"
```

---

### Task 7: Apply the additive migration locally and smoke-test the API

**Files:**

- No source files unless verification exposes a defect.

**Interfaces:**

- Verifies: local admin DB receives only the three additive tables.
- Verifies: public catalog is reachable and legacy review capability is unchanged.

- [ ] **Step 1: Confirm the target database before migration**

Use the existing local environment only. Print `current_database()` through the built admin datasource and verify it is the developer's local admin DB, not `clipper_admin_dev` or any production database.

Run:

```bash
cd web/clipper_web_api
node --input-type=module -e "const module = await import('./dist/core/database/admin.datasource.js'); const ds = module.default?.default ?? module.default; await ds.initialize(); console.log((await ds.query('SELECT current_database() AS name'))[0].name); await ds.destroy();"
```

Expected: the configured local database name. Stop if it points to a shared dev or production DB.

- [ ] **Step 2: Apply the local admin migration**

```bash
npm run db:migrate:admin
```

Expected: `CreateProductCatalog1786500000000` is applied once.

- [ ] **Step 3: Start the API and smoke-test public routes**

In one terminal:

```bash
npm run start:dev
```

In another terminal, using the configured local port:

```bash
curl -sS http://localhost:3000/catalog
curl -sS http://localhost:3000/plans
curl -sS http://localhost:3000/payments/review/config
```

Expected:

- `/catalog` returns `[]` because this phase intentionally seeds nothing.
- `/plans` continues returning the legacy review plans.
- `/payments/review/config` retains the environment-appropriate existing mode.

If the API uses a non-default `PORT`, substitute that exact local port; do not change application code solely for the smoke command.

- [ ] **Step 4: Run final repository verification**

```bash
npm test -- --runInBand
npm run build
git diff --check
git status --short --branch
```

Expected:

- Full Jest suite reports zero failures.
- Build exits 0.
- `git diff --check` reports no whitespace errors.
- Status contains no unintended files.

- [ ] **Step 5: Handle any verification defect through its owning task**

If verification exposes a defect, return to the task that owns the affected file, add a focused failing regression test, make the minimal fix, rerun that task's commands and the full verification commands, then use that task's existing commit scope. If no source changed, do not create an empty commit.

---

## Phase 1 Completion Gate

Phase 1 is complete only when all of the following are true:

- The additive OpenAPI contract parses and retains legacy plan paths.
- Catalog migration and entity mappings match exactly.
- New records default inactive.
- Public catalog exposes only active tiers and active products.
- Tier plugin keys and monthly credits are independent of billing product interval and price.
- Admin catalog endpoints are operator-protected.
- `activeProductById()` rejects inactive product/tier combinations.
- No approved product values are invented or seeded.
- Existing `/plans` and Toss review tests remain green.
- Local migration and route smoke tests pass.
- No legacy billing or payment code is removed.

After review of this phase, write the separate Access and Credit Foundation plan using the concrete catalog interfaces that landed.
