# Web Admin Access and Credit Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 관리자 웹에서 상품 등급·결제 상품·추가 크레딧 상품을 관리하고, 회원에게 표준 등급 이용 자격과 출처별 크레딧을 원장·감사 이력과 함께 운영한다.

**Architecture:** 기존 `/plans`는 `/admin/catalog`의 세 영역으로 교체하고, 무통장 승인 큐는 완전히 제거한다. 회원 상세는 이용 자격 생성·같은 등급 기간 수정·즉시 등급 변경·회수와 수동 크레딧 지급·회수를 서로 다른 명시적 작업으로 제공한다.

**Tech Stack:** Angular 19 standalone components, signals, Angular Material, Karma/Jasmine, Node.js 22

## Global Constraints

- 작업 경로는 `/Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit`, 브랜치는 `feat/access-credit-system-replacement`이다.
- Node 22를 사용한다.
- 기존 인증·operator role guard를 유지하고 API는 raw JSON으로 소비한다.
- 관리자는 내부 프리패스가 아니라 실제 `plan_tier`를 지급한다.
- 이용 자격 시작·종료일은 임의 시각과 만료 없음을 지원하고, 마지막 불완전한 월에도 한 달분 크레딧을 전액 지급한다.
- 같은 등급 기간 수정으로 크레딧을 재지급하지 않는다.
- 등급 변경은 하나의 관리자 액션으로 보이되 상향은 당월 차이만 지급하고 하향은 기존 크레딧을 회수하지 않는다.
- 수동 크레딧은 수량·만료일·사유를 입력하고, 사용자 총잔액을 숫자 하나로 덮어쓰지 않는다.
- 크레딧 회수는 선택한 관리자 지급 묶음의 현재 잔액 이하만 허용한다.
- 인라인 Angular 템플릿·스타일을 추가하지 않는다.

---

### Task 1: Replace Admin Billing Contracts and Mocks

**Files:**
- Modify: `src/app/core/api/models.ts`
- Create: `src/app/core/api/catalog-api.service.ts`
- Create: `src/app/core/api/catalog-api.service.spec.ts`
- Modify: `src/app/core/api/members-api.service.ts`
- Modify: `src/app/core/api/members-api.service.spec.ts`
- Delete: `src/app/core/api/plans-api.service.ts`
- Delete: `src/app/core/api/license-requests-api.service.ts`
- Modify: `src/app/core/api/mock/mock-data.ts`
- Modify: `src/app/core/api/mock/mock-api.interceptor.ts`
- Modify: `src/app/core/api/mock/mock-api.interceptor.spec.ts`

**Interfaces:**
- Consumes: `/admin/catalog` and `/admin/members/{id}/access-credit` OpenAPI contracts
- Produces: typed admin catalog, access action, credit action, and audit methods

- [ ] **Step 1: Define exact member operations**

```ts
export interface MemberAccessCreditView {
  member: { id: string; email: string; name: string };
  access: AccessView | null;
  creditSummary: CreditSummary;
  creditGrants: CreditGrantView[];
  accessEvents: AccessEventView[];
}

export interface GrantAdminAccessBody {
  tierId: string; startsAt: string; endsAt: string | null; reason: string; requestKey: string;
}
export interface GrantAdminCreditsBody {
  credits: number; expiresAt: string | null; reason: string; requestKey: string;
}
```

Service methods use the exact routes from the API core plan for grant, same-tier patch, change-tier, revoke, manual credit grant, and per-grant revoke.

- [ ] **Step 2: Write failing service URL tests**

```ts
api.grantAccess('u1', body).subscribe();
http.expectOne(`${base}/admin/members/u1/access-grants`).flush(view);
api.changeTier('u1', 'ag1', change).subscribe();
http.expectOne(`${base}/admin/members/u1/access-grants/ag1/change-tier`).flush(view);
api.revokeCredits('u1', 'cg1', revoke).subscribe();
http.expectOne(`${base}/admin/members/u1/credit-grants/cg1/revoke`).flush(view);
```

- [ ] **Step 3: Run API tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/api/**/*.spec.ts'`

Expected: FAIL because legacy plan/request services are still used.

- [ ] **Step 4: Implement services and stateful mocks**

Mocks must mutate one member's access and grants, reject a second open access, preserve credits on downgrade/revoke, and reject credit revocation above the selected grant's remaining balance.

- [ ] **Step 5: Run API tests**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/api/**/*.spec.ts'`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/core/api
git commit -m "refactor: replace admin billing api contracts"
```

### Task 2: Replace Plans with Product Catalog Administration

**Files:**
- Modify: `src/app/features/portal/plans/plans.component.ts`
- Modify: `src/app/features/portal/plans/plans.component.html`
- Modify: `src/app/features/portal/plans/plans.component.scss`
- Modify: `src/app/features/portal/plans/plans.component.spec.ts`
- Create: `src/app/features/portal/plans/catalog-form.types.ts`

**Interfaces:**
- Consumes: admin tier/product/credit-product CRUD and replace-tier-plugins endpoints
- Produces: a catalog page that edits all sellable product data without fixed tier count

- [ ] **Step 1: Write failing catalog-page tests**

```ts
it('separates tier entitlements from billing products', () => {
  expect(sectionTitles()).toEqual(['요금제 등급', '구독 결제 상품', '추가 크레딧 상품']);
});

it('edits plugins once per tier, not once per billing interval', () => {
  selectTierPlugins('pro', ['variation']);
  expect(api.replaceTierPlugins).toHaveBeenCalledOnceWith(proId, { pluginKeys: ['variation'] });
});
```

- [ ] **Step 2: Run the component test and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/plans/*.spec.ts'`

Expected: FAIL because the page only edits legacy period plans.

- [ ] **Step 3: Implement three explicit editors**

Tier editor controls code/name/description/order/monthly credits/validity/active and plugin keys. Billing product editor controls tier, code/name/interval/price/auto-renew/active. Credit product editor controls code/name/credits/price/validity/order/active and has no tier selector.

- [ ] **Step 4: Keep activation explicit**

New products are shown as inactive until the operator activates them. Validation prevents positive-price/credit/interval fields from being zero and displays raw API validation messages without inventing fallback values.

- [ ] **Step 5: Run component tests and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/plans/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/portal/plans
git commit -m "feat: replace plans page with product catalog"
```

### Task 3: Implement Member Access Grant, Edit, Change, and Revoke

**Files:**
- Modify: `src/app/features/portal/members/detail/member-detail.component.ts`
- Modify: `src/app/features/portal/members/detail/member-detail.component.html`
- Modify: `src/app/features/portal/members/detail/member-detail.component.scss`
- Modify: `src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Create: `src/app/features/portal/members/detail/access-action-dialog/access-action-dialog.component.ts`
- Create: `src/app/features/portal/members/detail/access-action-dialog/access-action-dialog.component.html`
- Create: `src/app/features/portal/members/detail/access-action-dialog/access-action-dialog.component.scss`
- Create: `src/app/features/portal/members/detail/access-action-dialog/access-action-dialog.component.spec.ts`

**Interfaces:**
- Consumes: member access-credit view, catalog tiers, access mutation methods
- Produces: explicit UI for four access actions with reason and request key

- [ ] **Step 1: Write failing dialog tests**

Test that no active access shows `이용 자격 지급`; same tier shows `기간·사유 수정`; different tier uses `등급 변경`; revoke requires confirmation and reason. `endsAt` accepts a date-time or `회수 전까지` (`null`).

- [ ] **Step 2: Run member-detail tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/members/detail/**/*.spec.ts'`

Expected: FAIL because current buttons are no-op and the member model is license based.

- [ ] **Step 3: Implement action-specific submissions**

Generate `requestKey` once when a dialog opens with `crypto.randomUUID()` and reuse it across retried HTTP submissions. Same-tier editing never calls the grant endpoint. Tier change warns that plugin access changes immediately, upgrade grants only the monthly difference, and downgrade does not reclaim credits.

- [ ] **Step 4: Refresh authoritative state after mutations**

On success, close the dialog and reload `/access-credit`; do not locally guess the calculated next grant date or difference credit.

- [ ] **Step 5: Run member-detail tests**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/members/detail/**/*.spec.ts'`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/portal/members/detail
git commit -m "feat: administer member access grants"
```

### Task 4: Implement Manual Credit Grant, Revoke, and Audit Views

**Files:**
- Modify: `src/app/features/portal/members/detail/member-detail.component.ts`
- Modify: `src/app/features/portal/members/detail/member-detail.component.html`
- Modify: `src/app/features/portal/members/detail/member-detail.component.scss`
- Modify: `src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Create: `src/app/features/portal/members/detail/credit-action-dialog/credit-action-dialog.component.ts`
- Create: `src/app/features/portal/members/detail/credit-action-dialog/credit-action-dialog.component.html`
- Create: `src/app/features/portal/members/detail/credit-action-dialog/credit-action-dialog.component.scss`
- Create: `src/app/features/portal/members/detail/credit-action-dialog/credit-action-dialog.component.spec.ts`

**Interfaces:**
- Consumes: credit summary, credit grants, credit ledger, access audit events, manual grant/revoke endpoints
- Produces: source-aware operations with immutable history

- [ ] **Step 1: Write failing credit-action tests**

```ts
it('grants arbitrary positive credits with operator-selected expiry and reason', () => {
  submitGrant({ credits: 7500, expiresAt: null, reason: '고객 보상' });
  expect(api.grantCredits).toHaveBeenCalledWith(userId, expect.objectContaining({ credits: 7500, expiresAt: null }));
});

it('caps revoke input at the selected admin grant remaining balance', () => {
  openRevoke(grant({ source: 'admin_adjustment', remainingCredits: 1200 }));
  expect(maxInput()).toBe('1200');
});
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/members/detail/**/*.spec.ts'`

Expected: FAIL because only operation charge/refund history exists.

- [ ] **Step 3: Implement source-aware summaries and actions**

Show held/spendable totals, blocked reason, source totals, each grant's remaining/initial amount, expiry, status, reason, and linked payment/access identifiers when present. Revoke is available only for server-marked revocable admin grants.

- [ ] **Step 4: Implement two audit timelines**

Access events show grant/update/change/revoke with operator and before/after values. Credit ledger shows grant/charge/refund/revoke/adjustment/expire with affected grant balance. Never label `balanceAfter` as the user's total balance.

- [ ] **Step 5: Run tests and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/members/detail/**/*.spec.ts' && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/app/features/portal/members/detail
git commit -m "feat: administer source aware member credits"
```

### Task 5: Remove Manual-Payment Approval Navigation and Screens

**Files:**
- Delete: `src/app/features/portal/approvals/approvals-flash.ts`
- Delete: `src/app/features/portal/approvals/approvals.component.ts`
- Delete: `src/app/features/portal/approvals/approvals.component.html`
- Delete: `src/app/features/portal/approvals/approvals.component.scss`
- Delete: `src/app/features/portal/approvals/approvals.component.spec.ts`
- Delete: `src/app/features/portal/approvals/detail/approval-detail.component.ts`
- Delete: `src/app/features/portal/approvals/detail/approval-detail.component.html`
- Delete: `src/app/features/portal/approvals/detail/approval-detail.component.scss`
- Delete: `src/app/features/portal/approvals/detail/approval-detail.component.spec.ts`
- Delete: `src/app/features/portal/approvals/detail/revoke-dialog.component.ts`
- Modify: `src/app/features/portal/portal.routes.ts`
- Modify: `src/app/features/portal/portal.routes.spec.ts`
- Modify: `src/app/shared/layout/app-header/app-header.component.ts`
- Modify: `src/app/shared/layout/app-header/app-header.component.html`
- Modify: `src/app/shared/layout/app-header/app-header.component.spec.ts`

**Interfaces:**
- Consumes: catalog and member administration replacement screens
- Produces: no approval queue, deposit confirmation, or request revocation path

- [ ] **Step 1: Change route/navigation tests to exclude approvals**

Assert that `approvals` and `approvals/:id` are absent, catalog remains at `plans`, and members remain reachable.

- [ ] **Step 2: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/portal.routes.spec.ts' --include='src/app/shared/layout/app-header/*.spec.ts'`

Expected: FAIL while approval links/routes exist.

- [ ] **Step 3: Delete approval screens and legacy copy**

Remove all `입금 확인`, `승인`, `반려`, `구매 요청` navigation and mocks. Do not redirect old approval URLs to an action-capable screen.

- [ ] **Step 4: Run full test and build**

Run: `nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A src/app
git commit -m "refactor: remove manual payment approvals"
```
