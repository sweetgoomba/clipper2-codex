# Current Credit Benefit Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep total spendable credits truthful while restoring a progress bar backed by the current free-trial or monthly-plan benefit.

**Architecture:** Web API adds a backward-compatible `currentBenefit` projection to `GET /credits/summary`, derived from existing credit grants and the effective paid access. Desktop Angular keeps `spendableBalance` as the headline and renders a progress meter only when the new projection is present and valid.

**Tech Stack:** NestJS 11, TypeORM/PostgreSQL, Jest, OpenAPI YAML, Angular 22 signals/templates/SCSS, Jasmine/Karma.

**Spec:** `/Users/jina/project/adlight/.codex/implementation/2026-09-18-current-credit-benefit-progress-design.md`

## Global Constraints

- All documentation remains under `/Users/jina/project/adlight/.codex`.
- No DB migration or existing grant/ledger rewrite.
- `spendableBalance` remains the account-total source of truth.
- `heldBalance` remains response-compatible but receives no new UI usage.
- Top-up, promotion, and admin-adjustment credits never enter the current-benefit denominator.
- `refund_locked`, revoked, and expired grants never enter the current-benefit projection.
- No commit or push is performed without the user's explicit instruction.

---

### Task 1: Web API current-benefit projection

**Files:**
- Modify: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Test: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`
- Modify: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Test: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`
- Modify: `/Users/jina/project/adlight/web/clipper_web_api/docs/api/openapi.yaml`
- Test: `/Users/jina/project/adlight/web/clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

**Interfaces:**
- Produces repository method `listCurrentBenefitGrants(userId, source, at): Promise<CreditGrant[]>` for `subscription` and `admin_plan` sources.
- Produces repository method `findCurrentFreeTrialGrant(userId, at): Promise<CreditGrant | undefined>`.
- Produces response field `currentBenefit: CurrentCreditBenefit | null` where `CurrentCreditBenefit` contains `kind`, `source`, `initialCredits`, `remainingCredits`, `periodStart`, and `periodEnd`.

- [x] **Step 1: Write failing service tests**

Add focused cases to `credit-grants.service.spec.ts` for:

```ts
expect(summary.currentBenefit).toEqual({
  kind: 'free_trial',
  source: 'free_trial',
  initialCredits: 400,
  remainingCredits: 300,
  periodStart: trialGrantedAt,
  periodEnd: trialExpiresAt,
});
```

and for current-period subscription grants:

```ts
expect(summary.currentBenefit).toEqual({
  kind: 'plan_period',
  source: 'subscription',
  initialCredits: 1_000,
  remainingCredits: 650,
  periodStart,
  periodEnd,
});
```

The subscription test must include two same-period grants to prove upgrade delta aggregation, a top-up to prove denominator isolation, and a free-trial grant to prove paid-benefit precedence. Add null, depleted trial, admin-plan aggregation, and excluded-status cases.

- [x] **Step 2: Run service tests and confirm RED**

Run:

```bash
npm test -- --runInBand src/modules/credits/application/credit-grants.service.spec.ts
```

Expected: compilation or assertion failure because `currentBenefit` and the repository methods do not exist.

- [x] **Step 3: Write failing repository tests**

Add SQL contract tests proving:

```text
plan query: user/source match, benefit period contains at, status IN (active, depleted)
trial query: source=free_trial, grant time contains at, status IN (active, depleted), newest first, LIMIT 1
```

- [x] **Step 4: Implement repository queries and service projection**

Add the two repository methods. In `summaryWithManager()`:

```ts
const paidAccess = await this.access.bind(manager).findEffectiveForUser(userId, at);
const currentBenefit = paidAccess
  ? await this.planBenefit(credits, userId, paidAccess.source, at)
  : await this.freeTrialBenefit(credits, userId, at);
```

`planBenefit()` selects the newest current benefit-period pair and sums only grants with the same start/end pair. `freeTrialBenefit()` maps the single current trial grant. Both retain depleted grants so `0 / initial` remains visible until period expiry.

- [x] **Step 5: Run repository and service tests and confirm GREEN**

Run:

```bash
npm test -- --runInBand src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts src/modules/credits/application/credit-grants.service.spec.ts
```

Expected: all selected tests pass.

- [x] **Step 6: Add OpenAPI schema and failing/passing contract assertions**

Add `CurrentCreditBenefit` with closed properties and extend `CreditSummary`:

```yaml
required: [heldBalance, spendableBalance, bySource, currentBenefit]
currentBenefit:
  allOf:
    - $ref: '#/components/schemas/CurrentCreditBenefit'
  nullable: true
```

Update the contract test to validate free-trial, plan-period, and null values, then run:

```bash
npm test -- --runInBand src/modules/payments/presentation/payments-openapi-contract.spec.ts src/modules/credits/presentation/credits.controller.spec.ts
```

Expected: all selected tests pass.

- [x] **Step 7: Verify Web API build and focused regression**

Run:

```bash
npm run build
npm test -- --runInBand src/modules/credits src/modules/access/application/effective-access.service.spec.ts
```

Expected: build succeeds and all selected credit/access tests pass.

---

### Task 2: Desktop progress meter backed by currentBenefit

**Files:**
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings-account.service.ts`
- Test: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings-account.service.spec.ts`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/account/account-summary.store.ts`
- Test: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/account/account-summary.store.spec.ts`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings.component.ts`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings.component.html`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings.component.scss`
- Test: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/settings/settings.component.spec.ts`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/home-side-panel/home-side-panel.component.ts`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/home-side-panel/home-side-panel.component.html`
- Modify: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/home-side-panel/home-side-panel.component.scss`
- Test: `/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/home-side-panel/home-side-panel.component.spec.ts`

**Interfaces:**
- Consumes optional `CreditSummary.currentBenefit` so old API responses remain safe.
- Produces store signals `currentBenefit`, `creditBenefitProgress`, and `creditBenefitLabel` shared by both screens.

- [x] **Step 1: Write failing service/store tests**

Add the optional DTO shape and fixtures only in tests first. Assert:

```ts
expect(store.creditLabel()).toBe('사용 가능 1,300');
expect(store.creditBenefitLabel()).toBe('이번 이용기간 남음 300 / 400');
expect(store.creditBenefitProgress()).toBe(75);
```

Also assert free-trial copy, null/absent fallback, invalid zero initial value fallback, and that a top-up changes the total but not the benefit meter.

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```bash
CI=1 ./node_modules/.bin/ng test --watch=false --progress=false \
  --include=src/shell/settings/settings/settings-account.service.spec.ts \
  --include=src/shell/account/account-summary.store.spec.ts
```

Expected: compilation or assertion failure because the DTO/signals do not exist.

- [x] **Step 3: Implement optional client contract and store derivations**

Add:

```ts
export interface CurrentCreditBenefit {
  kind: 'free_trial' | 'plan_period';
  source: 'free_trial' | 'subscription' | 'admin_plan';
  initialCredits: number;
  remainingCredits: number;
  periodStart: string;
  periodEnd: string | null;
}
```

Make `currentBenefit?: CurrentCreditBenefit | null` optional for old-server compatibility. Clamp remaining to `0..initial`, hide invalid projections, and keep `creditLabel()` based only on `spendableBalance`.

- [x] **Step 4: Run focused service/store tests and confirm GREEN**

Run the Step 2 command. Expected: all selected tests pass.

- [x] **Step 5: Write failing component tests**

For both settings and home side panel, assert:

```text
사용 가능 1,300
이번 이용기간 남음 300 / 400
progressbar now=300 max=400
no 보류
```

Add the free-trial label and null-benefit no-meter cases.

- [x] **Step 6: Implement the meter in both views**

Render the meter only when the validated store benefit is non-null. Reuse the same compact meter class names and color treatment in both components; do not restore the removed used/held segment or legend.

- [x] **Step 7: Run focused UI tests and confirm GREEN**

Run:

```bash
CI=1 ./node_modules/.bin/ng test --watch=false --progress=false \
  --include=src/shell/settings/settings/settings.component.spec.ts \
  --include=src/shell/projects/home-side-panel/home-side-panel.component.spec.ts
```

Expected: all selected tests pass.

- [x] **Step 8: Verify full Desktop regression and build**

Run:

```bash
CI=1 ./node_modules/.bin/ng test --watch=false --progress=false
npm run build -- --progress=false
git diff --check
```

Expected: full suite and build pass; no whitespace errors.

---

### Task 3: Closeout documentation and cross-repo verification

**Files:**
- Modify: `/Users/jina/project/adlight/.codex/implementation/2026-09-18-current-credit-benefit-progress-design.md`
- Modify: `/Users/jina/project/adlight/.codex/implementation/2026-09-18-desktop-credit-balance-presentation-followup.md`
- Modify: `/Users/jina/project/adlight/.codex/implementation/2026-09-18-current-credit-benefit-progress-implementation-plan.md`

**Interfaces:**
- Consumes verified test/build outputs from Tasks 1 and 2.
- Produces an auditable record of implemented semantics, exact test counts, and remaining `heldBalance` deprecation work.

- [x] **Step 1: Record implementation status and evidence**

Change design status to implemented only after both builds and the relevant suites pass. Record exact commands and observed test counts without claiming deployment.

- [x] **Step 2: Self-review against the design**

Confirm every design rule has a corresponding server or Desktop test, scan all three repositories with `git diff --check`, and verify no product source displays `보류`.

- [x] **Step 3: Present commit boundaries for approval**

Present separate proposed commits for Web API, Desktop Angular, and `.codex`. Do not commit or push until the user explicitly approves those exact repository scopes.
