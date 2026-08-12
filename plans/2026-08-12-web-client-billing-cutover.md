# Web Client Billing Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 고객 웹을 legacy 무통장 구매 요청·단일 이용권 표시에서 상품 등급·플러그인 권한·구독·출처별 크레딧·추가 충전 UI로 전환한다.

**Architecture:** 공개 요금 페이지는 catalog를 등급 기준으로 렌더링한다. 로그인 사용자는 실제 구독 checkout으로, 심사 기간의 비로그인 사용자는 익명 review checkout으로 분기한다. 포털은 현재 이용 자격과 보유/사용 가능 잔액, 출처별 크레딧, 만료, 결제 상태를 새 raw API에서 조합한다.

**Tech Stack:** Angular 19 standalone components, signals, Angular Material, Karma/Jasmine, Node.js 22

## Global Constraints

- 작업 경로는 `/Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit`, 브랜치는 `feat/access-credit-system-replacement`이다.
- Node 22를 사용한다.
- API 타입은 `clipper_web_api/docs/api/openapi.yaml`과 일치하고 raw 응답을 그대로 소비한다.
- 요금제 개수·판매 주기·가격·할인율을 컴포넌트에 하드코딩하지 않는다.
- 등급별 플러그인 차등을 표시하고, 결제 기간에 따라 플러그인 목록을 별도로 발명하지 않는다.
- 로컬에서도 Toss 버튼을 숨기지 않고, 클릭하면 로컬 환경에서 결제를 사용할 수 없다는 안내를 표시한다.
- 추가 크레딧 결제는 활성 이용 자격이 있는 로그인 사용자에게만 표시한다.
- 유효한 이용 자격이 없어도 보유 잔액과 출처·만료일은 표시하고 사용 가능 잔액이 0인 이유를 안내한다.
- 인라인 템플릿·스타일을 추가하지 않고 기존 4파일 Angular 컴포넌트 구조를 유지한다.

---

### Task 1: Replace Legacy Billing Models, API Services, and Mocks

**Files:**
- Modify: `src/app/core/api/models.ts`
- Create: `src/app/core/api/catalog-api.service.ts`
- Create: `src/app/core/api/catalog-api.service.spec.ts`
- Create: `src/app/core/api/access-api.service.ts`
- Create: `src/app/core/api/access-api.service.spec.ts`
- Create: `src/app/core/api/credits-api.service.ts`
- Create: `src/app/core/api/credits-api.service.spec.ts`
- Modify: `src/app/core/api/payments-api.service.ts`
- Modify: `src/app/core/api/payments-api.service.spec.ts`
- Delete: `src/app/core/api/plans-api.service.ts`
- Delete: `src/app/core/api/licenses-api.service.ts`
- Delete: `src/app/core/api/license-requests-api.service.ts`
- Delete: `src/app/core/api/credit-ledger-api.service.ts`
- Modify: `src/app/core/api/mock/mock-data.ts`
- Modify: `src/app/core/api/mock/mock-api.interceptor.ts`
- Modify: `src/app/core/api/mock/mock-api.interceptor.spec.ts`

**Interfaces:**
- Consumes: catalog/access/credits/subscriptions/payment contracts from the API plans
- Produces: typed Observables used by pricing, dashboard, credits, and payment result components

- [ ] **Step 1: Add exact client types**

```ts
export interface CatalogTier {
  id: string; code: string; name: string; description: string | null;
  sortOrder: number; monthlyCredits: number; monthlyCreditValidityDays: number | null;
  pluginKeys: string[]; products: BillingProduct[];
}
export interface CurrentAccessResponse { access: AccessView | null; }
export interface CreditSummary {
  heldBalance: number;
  spendableBalance: number;
  blockedReason: 'NO_ACTIVE_ACCESS' | null;
  bySource: Array<{ source: CreditSource; heldBalance: number; spendableBalance: number }>;
}
export interface CreditGrantView {
  id: string; source: CreditSource; initialCredits: number; remainingCredits: number;
  grantedAt: string; expiresAt: string | null; status: CreditGrantStatus; reason: string;
}
```

Ledger rows use `type: 'grant'|'operation_charge'|'operation_refund'|'admin_revoke'|'payment_adjustment'|'expire'`, include `source`, nullable operation metadata, and `balanceAfter` for the affected grant rather than pretending it is the user's total balance.

- [ ] **Step 2: Write failing URL contract tests**

```ts
service.currentAccess().subscribe();
http.expectOne(`${apiBase}/access/current`).flush({ access: null });
service.summary().subscribe();
http.expectOne(`${apiBase}/credits/summary`).flush(summary);
payments.startTopupCheckout({ creditProductId: 'cp-1' }).subscribe();
http.expectOne(`${apiBase}/payments/topups/checkout`).flush(checkout);
```

- [ ] **Step 3: Run service tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/api/**/*.spec.ts'`

Expected: FAIL because the new services do not exist and old endpoints are still expected.

- [ ] **Step 4: Implement services and deterministic mocks**

Mocks cover one active Pro access, subscription/admin/top-up grant sources, an expired grant, and `heldBalance > 0` with `spendableBalance = 0` when access is absent. Mock checkout returns a same-origin test result URL; it never grants credit before the result mock reports fulfillment success.

- [ ] **Step 5: Run API service tests**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/api/**/*.spec.ts'`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/core/api
git commit -m "refactor: replace web billing api contracts"
```

### Task 2: Render Tier-Based Pricing and Correct Checkout Paths

**Files:**
- Modify: `src/app/features/public/pricing/pricing.component.ts`
- Modify: `src/app/features/public/pricing/pricing.component.html`
- Modify: `src/app/features/public/pricing/pricing.component.scss`
- Modify: `src/app/features/public/pricing/pricing.component.spec.ts`
- Create: `src/app/features/public/pricing/plugin-label.ts`
- Create: `src/app/features/public/pricing/plugin-label.spec.ts`

**Interfaces:**
- Consumes: `CatalogApiService.listTiers`, `AuthService.user`, `PaymentsApiService.checkoutConfig/startSubscriptionCheckout/startReviewCheckout`
- Produces: one pricing card per tier with product-cycle choices and correct authenticated/anonymous checkout

- [ ] **Step 1: Write failing pricing behavior tests**

```ts
it('shows plugins by tier and never derives them from billing interval', () => {
  catalog.next([tier({ pluginKeys: ['shortform_prompt', 'variation'], products: [monthly, annual] })]);
  expect(text()).toContain('프롬프트로 숏폼 제작');
  expect(text()).toContain('베리에이션');
  expect(fixture.debugElement.queryAll(By.css('[data-plugin-key="variation"]')).length).toBe(1);
});

it('uses authenticated subscription checkout after login', () => {
  auth.user.set(user);
  clickProduct(monthly.id);
  expect(payments.startSubscriptionCheckout).toHaveBeenCalledWith({ billingProductId: monthly.id });
  expect(payments.startReviewCheckout).not.toHaveBeenCalled();
});

it('keeps review recurring and one-time buttons for anonymous card-company review', () => {
  auth.user.set(null);
  expect(button('review-recurring')).toBeTruthy();
  expect(button('review-one-time')).toBeTruthy();
});
```

- [ ] **Step 2: Run the pricing test and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/public/pricing/*.spec.ts'`

Expected: FAIL because pricing still consumes legacy plans and month-based feature text.

- [ ] **Step 3: Implement tier cards and product selectors**

Sort tiers/products according to API order. Display tier name, tier description, monthly credits, plugin labels, product total price, interval, and monthly-equivalent price. Calculate savings only from products in the same tier and only when a one-month product exists. Unknown plugin keys render their key instead of disappearing.

- [ ] **Step 4: Implement environment and login behavior**

`GET /payments/config` returns `checkout` or `local_notice`. In `local_notice`, both authenticated and review buttons stay visible but clicks set the existing local-unavailable message and make no API call. In `checkout`, logged-in users call real subscription checkout; anonymous users call review checkout. Review one-time is allowed for 1/3/12 months and review recurring for 1/3 months.

- [ ] **Step 5: Run pricing tests and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/public/pricing/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/public/pricing
git commit -m "feat: render tier pricing and toss checkout paths"
```

### Task 3: Replace Dashboard and Credits with Access/Source Views

**Files:**
- Modify: `src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `src/app/features/portal/dashboard/dashboard.component.scss`
- Modify: `src/app/features/portal/dashboard/dashboard.component.spec.ts`
- Modify: `src/app/features/portal/credits/credits.component.ts`
- Modify: `src/app/features/portal/credits/credits.component.html`
- Modify: `src/app/features/portal/credits/credits.component.scss`
- Modify: `src/app/features/portal/credits/credits.component.spec.ts`

**Interfaces:**
- Consumes: access, credit summary, grant page, ledger page, and current subscription APIs
- Produces: customer-visible entitlement and source-aware credit state

- [ ] **Step 1: Write failing dashboard tests**

```ts
it('shows held credits separately when access is inactive', () => {
  access.next({ access: null });
  credits.next({ heldBalance: 5000, spendableBalance: 0, blockedReason: 'NO_ACTIVE_ACCESS', bySource: [] });
  expect(text()).toContain('보유 크레딧 5,000');
  expect(text()).toContain('이용권을 다시 활성하면');
});

it('does not render queued license or manual purchase copy', () => {
  expect(text()).not.toContain('대기 이용권');
  expect(text()).not.toContain('구매 요청');
});
```

- [ ] **Step 2: Write failing source-ledger tests**

Test source chips for subscription/admin/top-up, per-grant expiry, held/spendable totals, and ledger labels for grant/charge/refund/revoke/expire.

- [ ] **Step 3: Run component tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/dashboard/*.spec.ts' --include='src/app/features/portal/credits/*.spec.ts'`

Expected: FAIL because both pages use `licenses/current` and operation-only ledger rows.

- [ ] **Step 4: Implement access and credit presentation**

Dashboard shows tier, access source, starts/ends, next monthly grant, allowed plugin count, held/spendable balances, and subscription next bill/cancel state. Credits shows source totals, grant rows with expiry/status, and the immutable ledger. Filters use new ledger types rather than old charge/refund-only values.

When the subscription is `past_due`, dashboard shows the failed charge state and a `결제 다시 시도` action backed by `POST /subscriptions/current/retry`. It explains that access remains until the current paid period ends and does not promise a grace period beyond that date.

- [ ] **Step 5: Run portal component tests**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/dashboard/*.spec.ts' --include='src/app/features/portal/credits/*.spec.ts'`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/portal/dashboard src/app/features/portal/credits
git commit -m "feat: show access and source credit balances"
```

### Task 4: Add Prepaid Top-up Purchase and Unified Payment Result

**Files:**
- Create: `src/app/features/portal/topup/topup.component.ts`
- Create: `src/app/features/portal/topup/topup.component.html`
- Create: `src/app/features/portal/topup/topup.component.scss`
- Create: `src/app/features/portal/topup/topup.component.spec.ts`
- Modify: `src/app/features/portal/portal.routes.ts`
- Modify: `src/app/features/public/payment-result/payment-result.component.ts`
- Modify: `src/app/features/public/payment-result/payment-result.component.html`
- Modify: `src/app/features/public/payment-result/payment-result.component.spec.ts`
- Modify: `src/app/features/public/pricing/pricing.component.ts`

**Interfaces:**
- Consumes: credit-product catalog, current access, authenticated checkout, secret-token payment result/reconcile
- Produces: `/app/topup` and result states that distinguish paid/fulfillment completion

- [ ] **Step 1: Write failing top-up admission tests**

```ts
it('lists the same catalog products without plan-tier pricing', () => {
  expect(cards().map(cardPrice)).toEqual(['10,000원', '30,000원']);
});

it('does not call checkout when current access is absent', () => {
  access.next({ access: null });
  clickTopup('cp-small');
  expect(payments.startTopupCheckout).not.toHaveBeenCalled();
  expect(text()).toContain('추가 크레딧은 활성 이용권이 필요합니다');
});
```

- [ ] **Step 2: Write failing result-state tests**

Test `paid + pending`, `paid + failed`, `paid + succeeded`, canceled, and failed. Only `succeeded` says credits/access were supplied. `paid + failed` says payment succeeded and supply is being retried, not that the payment failed.

- [ ] **Step 3: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/topup/*.spec.ts' --include='src/app/features/public/payment-result/*.spec.ts'`

Expected: FAIL because top-up page and fulfillment-aware result states do not exist.

- [ ] **Step 4: Implement top-up and result polling**

Use `GET /payments/orders/{receiptToken}` and `POST /payments/orders/{receiptToken}/reconcile` for authenticated orders; keep review endpoints for anonymous review tokens. Poll only while payment or fulfillment is nonterminal, with the existing bounded short-poll behavior and no client-side fulfillment action.

- [ ] **Step 5: Run tests and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/topup/*.spec.ts' --include='src/app/features/public/payment-result/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/portal/topup src/app/features/portal/portal.routes.ts src/app/features/public/payment-result
git commit -m "feat: add prepaid credit topup flow"
```

### Task 5: Remove Manual Purchase and History User Paths

**Files:**
- Delete: `src/app/features/portal/purchase/purchase.component.ts`
- Delete: `src/app/features/portal/purchase/purchase.component.html`
- Delete: `src/app/features/portal/purchase/purchase.component.scss`
- Delete: `src/app/features/portal/purchase/purchase.component.spec.ts`
- Delete: `src/app/features/portal/history/history.component.ts`
- Delete: `src/app/features/portal/history/history.component.html`
- Delete: `src/app/features/portal/history/history.component.scss`
- Delete: `src/app/features/portal/history/history.component.spec.ts`
- Modify: `src/app/features/portal/portal.routes.ts`
- Modify: `src/app/shared/layout/app-header/app-header.component.html`
- Modify: `src/app/shared/layout/app-header/app-header.component.spec.ts`

**Interfaces:**
- Consumes: replacement pricing, dashboard, credits, and top-up routes
- Produces: no reachable `/app/purchase` or `/app/history` legacy workflow

- [ ] **Step 1: Replace route/navigation tests**

Assert that portal routes include `credits`, `topup`, and `account`, exclude `purchase` and `history`, and that no visible link contains `구매 요청` or `무통장`.

- [ ] **Step 2: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/**/*.spec.ts' --include='src/app/shared/layout/app-header/*.spec.ts'`

Expected: FAIL while legacy routes and copy remain.

- [ ] **Step 3: Delete the legacy pages and point purchase CTAs to `/pricing` or `/app/topup`**

No redirect from `/app/purchase` may submit a request. The wildcard route can return users to the portal dashboard.

- [ ] **Step 4: Run full test and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A src/app
git commit -m "refactor: remove manual purchase web workflow"
```
