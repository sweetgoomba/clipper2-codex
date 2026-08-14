# 토스페이먼츠 PG 심사용 익명 결제 전환 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 이 작업은 기존 `feat/access-credit-system-replacement` checkout을 사용하지 않고 아래 격리 worktree에서만 실행한다.

**Goal:** 비로그인 심사자가 공개 요금 페이지에서 토스페이먼츠 PG V2 주문서형 단건결제와 자동결제 카드 등록 후 최초 테스트 결제 1회를 완료하고, 결과를 Clipper DB와 공개 결과 페이지에서 확인하게 한다.

**Architecture:** 고객 웹은 익명 주문을 만든 뒤 Clipper 공개 checkout으로 이동하고, 서버가 준 세션만으로 토스페이먼츠 SDK를 초기화한다. API는 브라우저 성공 리다이렉트의 식별자를 DB 스냅샷과 대조한 뒤 토스페이먼츠 코어 API를 Basic 인증과 고정 멱등키로 호출하며, 결과가 불확실하면 주문번호 조회 또는 같은 멱등키 재시도로 복구한다. 단건과 빌링은 서로 다른 토스페이먼츠 키 세트를 사용하고 Secret Key·평문 `authKey`·평문 `billingKey`는 브라우저, 로그, 이벤트 payload에 노출하지 않는다.

**Tech Stack:** Node.js 22.22.x, NestJS 11, TypeORM/PostgreSQL 16, Jest 30, Angular 19, Jasmine/Karma, `@tosspayments/tosspayments-sdk` V2, Docker Compose.

**Execution status (2026-08-14):** Tasks 1–9 were implemented test-first in the three isolated feature worktrees, reviewed, merged, and pushed to each repository's `dev`. Final merge commits are API `880c053`, customer web `4b361ef`, and infra `4d32022`. The API passes 93 suites/590 tests and builds, the customer web passes 93 tests and builds without test-key strings in `dist`, PostgreSQL 16 migration up/no-op/down/up passed, and the infra preflight 8/8 plus dev/stage/prod Compose overlays validate. Deployment is still pending because this workstation cannot reach the dev Mac mini and the real billing Secret Key must be entered directly in its ignored `env/stack.dev.env`.

## Global Constraints

- 작업 브랜치는 API·고객 웹·인프라 모두 `feat/toss-payments-pg-review-checkout`이고 기준은 각 저장소의 최신 `origin/dev`다.
- 작업 경로는 `/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-review-checkout`, `/Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-review-checkout`, `/Users/jina/project/adlight/.worktrees/clipper_infra-toss-payments-pg-review-checkout`다.
- `/Users/jina/project/adlight/.worktrees/*-access-credit`와 `feat/access-credit-system-replacement`는 읽기·수정·rebase·reset·삭제·병합하지 않는다.
- API와 고객 웹의 모든 npm 명령은 `source ~/.zshrc && nvm use 22` 이후 실행한다.
- 새 동작은 테스트가 기대한 이유로 실패하는 RED를 먼저 확인한 뒤 최소 구현으로 GREEN을 만든다.
- 최초 구현 세션에서는 commit, push, merge, 배포를 보류했고, 2026-08-14 사용자의 명시적 진행 요청 후 검증된 기능 브랜치를 `dev`에 병합·push했다.
- 1·3개월은 단건·정기결제를 허용하고 12개월은 단건만 허용한다.
- 회원 연결, 이용권·플러그인 권한·크레딧 지급, 반복 갱신, 환불·해지·알림을 구현하지 않는다.
- 토스페이먼츠 공식 MCP 확인 결과 주문서형은 결제 연동 키 세트 `test_gck_`/`test_gsk_`, 자동결제는 API 개별 연동 키 세트 `test_ck_`/`test_sk_`를 사용한다. Client Key와 Secret Key는 반드시 같은 세트를 사용한다.
- 토스페이먼츠 POST API는 UUID v4 `Idempotency-Key`를 사용하고 첫 요청부터 15일 동안 같은 키를 재사용한다. GET에는 멱등키를 보내지 않는다.
- 공식 계약 근거는 [API 키](https://docs.tosspayments.com/reference/using-api/api-keys), [SDK V2 환경 설정](https://docs.tosspayments.com/sdk/v2/js/environment), [주문서형 결제](https://docs.tosspayments.com/guides/v2/payment-widget/integration), [자동결제 카드 등록](https://docs.tosspayments.com/guides/v2/billing/integration), [코어 API](https://docs.tosspayments.com/reference), [멱등키](https://docs.tosspayments.com/reference/using-api/idempotency-key)다.
- API `dev` baseline의 `operator-jwt.strategy.spec.ts` 날짜 의존 fixture는 별도 수정 브랜치로 검증한 뒤 merge commit `5c1f832`로 먼저 반영했다. PG 기능 브랜치는 이 최신 `dev`를 포함하고 최종 전체 suite가 통과했다.

---

### Task 1: 토스페이먼츠 PG 주문 스키마와 repository 계약

**Files:**
- Create: `web/clipper_web_api/src/core/database/migrations/admin/1786560000000-MigrateReviewPaymentsToTossPaymentsPg.ts`
- Modify: `web/clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `web/clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `web/clipper_web_api/src/modules/payments/domain/payment.model.ts`
- Modify: `web/clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `web/clipper_web_api/src/modules/payments/infrastructure/payment-order.entity.ts`
- Modify: `web/clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `web/clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`

**Interfaces:**
- `PaymentOrder.customerKey: string`
- `PaymentOrder.paymentKey: string | null`
- `PaymentOrder.billingAuthKeyEnc: string | null`
- `PaymentOrder.billingKeyEnc: string | null`
- `PaymentOrder.confirmationIdempotencyKey: string`
- `PaymentOrder.billingIssueIdempotencyKey: string`
- `PaymentOrder.billingChargeIdempotencyKey: string`
- `PaymentOrder.lastTransactionKey: string | null`
- `PaymentOrdersRepository.markCheckoutReady(id): Promise<PaymentOrder>`
- `PaymentOrdersRepository.markNormalPaymentPending(id, paymentKey): Promise<PaymentOrder>`
- `PaymentOrdersRepository.saveBillingAuthKey(id, encryptedAuthKey): Promise<PaymentOrder>`
- `PaymentOrdersRepository.markBillingActive(id, encryptedBillingKey, payMethod): Promise<PaymentOrder>` clears `billingAuthKeyEnc`.
- `PaymentOrdersRepository.markPaid(id, { paymentKey, payMethod, paidAmountKrw, lastTransactionKey, mode }): Promise<PaymentOrder>`

- [ ] **Step 1: Write failing entity/repository/migration tests**

  Add literal expectations proving new orders persist a non-null random `customerKey`, three UUID v4 idempotency keys, null PG secrets, and the renamed `paymentKey`/`lastTransactionKey`. Add repository transition tests for normal confirmation claim, encrypted `authKey` storage, billing activation clearing `billingAuthKeyEnc`, and `paid` protection. Extend `admin.datasource.spec.ts` to require the new migration.

- [ ] **Step 2: Run RED**

  Run from the API worktree:

  ```bash
  npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/core/database/admin.datasource.spec.ts
  ```

  Expected: FAIL because the PG fields, repository methods, and migration are absent.

- [ ] **Step 3: Add the PG migration and minimal model/repository implementation**

  The migration must delete `payment_events` before `payment_orders`, then perform these schema changes without editing `1786300000000-CreatePaymentOrders.ts`:

  ```sql
  ALTER TABLE payment_orders RENAME COLUMN review_user_id TO customer_key;
  ALTER TABLE payment_orders RENAME COLUMN pay_token TO payment_key;
  ALTER TABLE payment_orders RENAME COLUMN transaction_id TO last_transaction_key;
  ALTER TABLE payment_orders ALTER COLUMN customer_key SET NOT NULL;
  ALTER TABLE payment_orders ALTER COLUMN order_no TYPE varchar(64);
  ALTER TABLE payment_orders ALTER COLUMN payment_key TYPE varchar(200);
  ALTER TABLE payment_orders ALTER COLUMN last_transaction_key TYPE varchar(200);
  ALTER TABLE payment_orders ADD COLUMN billing_auth_key_enc text;
  ALTER TABLE payment_orders ADD COLUMN confirmation_idempotency_key uuid NOT NULL;
  ALTER TABLE payment_orders ADD COLUMN billing_issue_idempotency_key uuid NOT NULL;
  ALTER TABLE payment_orders ADD COLUMN billing_charge_idempotency_key uuid NOT NULL;
  ```

  The down migration must clear the two review tables, drop the new columns, restore nullable `review_user_id`, and rename the three legacy columns back so rollback is deterministic for this temporary feature.

- [ ] **Step 4: Run GREEN**

  Run the Task 1 Jest command and `npm run build`. Expected: repository and datasource tests pass; TypeScript build exits 0.

### Task 2: 토스페이먼츠 V2 서버 provider

**Files:**
- Delete: `web/clipper_web_api/src/modules/payments/domain/toss-pay.provider.ts`
- Delete: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Delete: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`
- Create: `web/clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`
- Modify: `web/clipper_web_api/src/modules/payments/payments.module.ts`

**Interfaces:**

```ts
type TossPaymentsKeySet = 'widget' | 'billing';

interface TossPaymentsPayment {
  paymentKey: string;
  orderId: string;
  status: string;
  type: string;
  method: string;
  currency: string;
  totalAmount: number;
  lastTransactionKey: string;
}

abstract class TossPaymentsProvider {
  confirmPayment(input: { paymentKey: string; orderId: string; amount: number; idempotencyKey: string }): Promise<TossPaymentsPayment>;
  getPaymentByOrderId(input: { orderId: string; keySet: TossPaymentsKeySet }): Promise<TossPaymentsPayment>;
  issueBillingKey(input: { authKey: string; customerKey: string; idempotencyKey: string }): Promise<{ billingKey: string; customerKey: string; method: string }>;
  chargeBillingKey(input: { billingKey: string; customerKey: string; orderId: string; orderName: string; amount: number; idempotencyKey: string }): Promise<TossPaymentsPayment>;
  deleteBillingKey(input: { billingKey: string }): Promise<void>;
}
```

- [ ] **Step 1: Write provider RED tests**

  Cover exact URLs and bodies for `POST /v1/payments/confirm`, `GET /v1/payments/orders/{orderId}`, `POST /v1/billing/authorizations/issue`, `POST /v1/billing/{billingKey}`, and `DELETE /v1/billing/{billingKey}`. Assert Basic auth is `base64(secret + ':')`, widget operations use `TOSS_PAYMENTS_WIDGET_SECRET_KEY`, billing operations use `TOSS_PAYMENTS_BILLING_SECRET_KEY`, every POST carries the supplied `Idempotency-Key`, GET does not, and no secret is included in thrown messages.

  Add response tests for `DONE`/`NORMAL`, `DONE`/`BILLING`, `NOT_FOUND_PAYMENT`, deterministic 4xx errors, and transport/5xx/invalid-success-body uncertain errors.

- [ ] **Step 2: Run RED**

  ```bash
  npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts
  ```

  Expected: FAIL because the PG provider does not exist.

- [ ] **Step 3: Implement the minimal provider**

  Fix the base URL in code as `https://api.tosspayments.com`, use `AbortSignal.timeout(10_000)`, accept only object JSON, sanitize provider error codes to `[A-Za-z0-9_:-]{1,120}`, and normalize only fields consumed by the application. Treat transport errors, HTTP 5xx, and malformed successful responses from POST approvals as uncertain; treat a missing order lookup as `TossPaymentsPaymentNotFoundError`.

- [ ] **Step 4: Run GREEN**

  Run the Task 2 Jest command. Expected: all provider contract and secrecy tests pass.

### Task 3: 익명 checkout session과 PG 리다이렉트 application flow

**Files:**
- Replace: `web/clipper_web_api/src/modules/payments/application/review-payments.service.spec.ts`
- Replace: `web/clipper_web_api/src/modules/payments/application/review-payments.service.ts`
- Modify: `web/clipper_web_api/src/modules/payments/presentation/review-payments.controller.spec.ts`
- Modify: `web/clipper_web_api/src/modules/payments/presentation/review-payments.controller.ts`
- Delete: `web/clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`
- Delete: `web/clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Delete: `web/clipper_web_api/src/modules/payments/presentation/dto/normal-result-callback.dto.ts`
- Delete: `web/clipper_web_api/src/modules/payments/presentation/dto/billing-result-callback.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/toss-payments-review-redirect.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/toss-payments-review-redirect.controller.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/normal-payment-success-query.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/billing-auth-success-query.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/payment-fail-query.dto.ts`
- Modify: `web/clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `web/clipper_web_api/.env.example`

**Interfaces:**

```ts
interface ReviewCheckoutSession {
  paymentType: 'one_time' | 'recurring';
  planName: string;
  months: number;
  amount: { value: number; currency: 'KRW' };
  orderId: string;
  customerKey: string;
  clientKey: string;
  successUrl: string;
  failUrl: string;
}
```

- `POST /payments/review/checkout` returns only `https://<web>/payment/checkout?receiptToken=...` and makes no provider request.
- `GET /payments/review/orders/:receiptToken/checkout` returns `ReviewCheckoutSession`; `clientKey` is the widget key for `one_time` and billing client key for `recurring`.
- Redirect controllers accept `GET /payments/tosspayments/review/normal/success`, `/billing/success`, and `/fail`, then issue `303 See Other` to the public result URL.

- [ ] **Step 1: Write checkout/session RED tests**

  Prove review capability requires `TOSS_PAYMENTS_REVIEW_MODE=true`, both test key pairs, and either dev HTTPS origins or local loopback origins. Prove order creation generates one random `customerKey`, receipt token hash, three UUID v4 idempotency keys, accepts only the 1/3/12-month matrix, never calls the provider, and returns a Clipper checkout URL. Prove session responses contain no Secret Key, `authKey`, or `billingKey`.

- [ ] **Step 2: Run checkout/session RED**

  ```bash
  npm test -- --runInBand src/modules/payments/application/review-payments.service.spec.ts src/modules/payments/presentation/review-payments.controller.spec.ts
  ```

  Expected: FAIL on the new Clipper checkout and session contract.

- [ ] **Step 3: Implement checkout/session GREEN**

  Generate `orderId` and `customerKey` with `clipper-review-` plus 20 base64url characters, receipt tokens with 32 random bytes, and idempotency keys with `randomUUID()`. Mark the order `checkout_ready` before returning. Add session lookup rate limiting in the existing result bucket and retain raw NestJS responses.

- [ ] **Step 4: Write normal success RED tests**

  Prove `orderId`, integer `amount`, and `paymentKey` are compared to the locked order before provider access; `paymentKey` is conditionally stored; confirmation uses the DB amount and stored idempotency key; only `status=DONE`, `type=NORMAL`, `currency=KRW`, matching `orderId`, `paymentKey`, and exact `totalAmount` become `paid`. Prove duplicate redirects do not reconfirm, and uncertain confirmation queries by `orderId` with the widget key set without guessing failure.

- [ ] **Step 5: Implement normal success GREEN**

  Keep `payment_pending` for unresolved transport/5xx/query-not-found cases, mark deterministic provider rejection as `failed`, store sanitized events without provider message text, and never grant entitlements.

- [ ] **Step 6: Write billing success RED tests**

  Prove a mismatched `customerKey` prevents provider calls. Prove `authKey` is encrypted before issue, the billing issue UUID is reused, a successful key is encrypted and clears the encrypted auth key, and the first charge uses the order UUID and billing charge idempotency key exactly once. Accept `paid` only for `DONE`, `BILLING`, `KRW`, exact `orderId`, exact amount, and a non-empty `lastTransactionKey`. Prove the auth key remains recoverable after an uncertain issue, the billing key remains after a failed charge, and `paid` orders never call provider APIs again.

- [ ] **Step 7: Implement billing success GREEN**

  Retry an uncertain billing issue with the same encrypted auth key and issue idempotency key. For a pending first charge, query the order with the billing key set; if no payment exists, repeat the POST only with the stored billing charge idempotency key. Do not schedule any subsequent charge.

- [ ] **Step 8: Write and implement failure/reconcile/303 tests**

  `PAY_PROCESS_CANCELED` becomes `canceled`; other sanitized codes become `failed`; neither path overwrites `paid`. Reconcile may query or repeat only the current order's already-created provider operation and must not create a new order or new idempotency key. The redirect controller must send `303` with a Clipper result URL containing only the receipt token.

- [ ] **Step 9: Run application/controller GREEN**

  ```bash
  npm test -- --runInBand src/modules/payments
  npm run build
  ```

  Expected: all payment suites pass and the API builds.

### Task 4: OpenAPI 계약 교체

**Files:**
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

- [ ] **Step 1: Replace Toss Pay callback schemas and paths**

  Add `ReviewCheckoutSession`, document the session endpoint, three GET redirect endpoints and their query fields, and `303` responses. Remove `TossNormalResultCallback`, `TossBillingResultCallback`, and `/payments/toss/**/result-callback`. Update wording from Toss Pay direct to Toss Payments PG without changing unrelated API paths.

- [ ] **Step 2: Validate the contract**

  Run the existing OpenAPI parse test discovered by `rg -n "openapi" src test` and `npm run build`. Expected: YAML parses and generated Nest code still builds.

### Task 5: 고객 웹 SDK adapter

**Files:**
- Modify: `web/clipper_web_client/package.json`
- Modify: `web/clipper_web_client/package-lock.json`
- Create: `web/clipper_web_client/src/app/core/payments/toss-payments-sdk.service.ts`
- Create: `web/clipper_web_client/src/app/core/payments/toss-payments-sdk.service.spec.ts`

**Interfaces:**

```ts
interface MountedOneTimeCheckout {
  requestPayment(): Promise<void>;
  destroy(): Promise<void>;
}

class TossPaymentsSdkService {
  mountOneTime(session: ReviewCheckoutSession): Promise<MountedOneTimeCheckout>;
  requestBillingAuth(session: ReviewCheckoutSession): Promise<void>;
}
```

- [ ] **Step 1: Write adapter RED tests**

  Inject a controlled `loadTossPayments` boundary. Assert the observable SDK sequence is `widgets({customerKey})` → `setAmount({currency:'KRW', value})` → `renderPaymentMethods({selector:'#payment-method'})` → `renderAgreement({selector:'#agreement'})`, followed later by `requestPayment({orderId, orderName, successUrl, failUrl})`. Assert billing uses `payment({customerKey}).requestBillingAuth({method:'CARD', successUrl, failUrl})` and never uses the widgets request path.

- [ ] **Step 2: Run RED**

  ```bash
  npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/payments/toss-payments-sdk.service.spec.ts'
  ```

  Expected: FAIL because the adapter and SDK dependency do not exist.

- [ ] **Step 3: Install and implement**

  Run `npm install @tosspayments/tosspayments-sdk --save`, add an Angular injection token whose default factory is `loadTossPayments`, and implement only the two flows above. Keep SDK types inside the adapter; UI components depend only on `MountedOneTimeCheckout` and `TossPaymentsSdkService`.

- [ ] **Step 4: Run GREEN**

  Run the Task 5 Karma command. Expected: adapter sequence and payload tests pass.

### Task 6: 공개 checkout 화면과 API client

**Files:**
- Modify: `web/clipper_web_client/src/app/core/api/models.ts`
- Modify: `web/clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `web/clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Create: `web/clipper_web_client/src/app/features/public/payment-checkout/payment-checkout.component.ts`
- Create: `web/clipper_web_client/src/app/features/public/payment-checkout/payment-checkout.component.html`
- Create: `web/clipper_web_client/src/app/features/public/payment-checkout/payment-checkout.component.scss`
- Create: `web/clipper_web_client/src/app/features/public/payment-checkout/payment-checkout.component.spec.ts`
- Modify: `web/clipper_web_client/src/app/features/public/public.routes.ts`

- [ ] **Step 1: Write API/session and route RED tests**

  Add `ReviewCheckoutSession` with only the public fields from Task 3. Prove `getReviewCheckoutSession(receiptToken)` sends an unauthenticated GET to `/payments/review/orders/{encodedToken}/checkout`. Add `/payment/checkout` to public routes.

- [ ] **Step 2: Run RED**

  Run the API service spec. Expected: FAIL because the session method/model are absent.

- [ ] **Step 3: Implement API/session GREEN**

  Add the model, API method, and route without any static key in Angular environments.

- [ ] **Step 4: Write checkout component RED tests**

  Cover invalid receipt tokens, safe API/SDK failure copy, server price display, and the two exclusive flows. For one-time, require mounted payment-method and agreement areas and call `requestPayment()` only after mount. For recurring, render product, amount, billing period, immediate first test charge notice, no-real-withdrawal notice, and a required checkbox; assert no billing auth before explicit consent and exact billing session after consent. Assert no entitlement or renewal claim is displayed.

- [ ] **Step 5: Implement checkout component GREEN**

  Use four separate Angular files, semantic CSS variables, and a fakeable SDK service. Disable the primary button while loading/requesting. Destroy mounted widgets on component teardown. Convert all SDK/provider exceptions to fixed Korean user guidance.

- [ ] **Step 6: Run checkout GREEN**

  ```bash
  npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/core/api/payments-api.service.spec.ts' --include='src/app/features/public/payment-checkout/payment-checkout.component.spec.ts'
  ```

  Expected: API and checkout component specs pass.

### Task 7: 요금·결과 화면의 PG 문구와 복구 동작

**Files:**
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.spec.ts`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.ts`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.html`
- Modify: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.spec.ts`
- Modify: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.ts`
- Modify: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.html`
- Remove route: `/payment/cancel` from `web/clipper_web_client/src/app/features/public/public.routes.ts`

- [ ] **Step 1: Write pricing/result RED tests**

  Preserve the 1·3-month recurring/one-time and 12-month one-time-only matrix. Change fixtures so checkout navigation points to the Clipper `/payment/checkout` URL. Require user copy to say `토스페이먼츠 PG 테스트 결제`. On a pending result, the first read uses GET and later polling/refresh uses the existing reconcile endpoint; paid/canceled/failed stop polling. No screen may claim access, credit, renewal, or real withdrawal.

- [ ] **Step 2: Run RED**

  Run the pricing and result component specs. Expected: FAIL on PG wording, Clipper checkout URL, and pending reconcile behavior.

- [ ] **Step 3: Implement minimal UI changes and run GREEN**

  Keep the existing layout and result states. Change only checkout navigation fixtures, provider naming, and pending reconciliation. Run the Task 7 specs, then the entire client suite and `npm run build` under Node 22.

### Task 8: 인프라 환경계약 교체

**Files:**
- Modify: `web/clipper_infra/apps/compose.yml`
- Modify: `web/clipper_infra/env/stack.dev.env.example`
- Modify: `web/clipper_infra/env/stack.stage.env.example`
- Modify: `web/clipper_infra/env/stack.prod.env.example`

- [ ] **Step 1: Replace legacy variables**

  Remove `TOSS_PAY_API_KEY`, `TOSS_PAY_REVIEW_MODE`, and `TOSS_PAY_CALLBACK_BASE_URL`. Add server-only values:

  ```text
  TOSS_PAYMENTS_WIDGET_CLIENT_KEY
  TOSS_PAYMENTS_WIDGET_SECRET_KEY
  TOSS_PAYMENTS_BILLING_CLIENT_KEY
  TOSS_PAYMENTS_BILLING_SECRET_KEY
  TOSS_PAYMENTS_REVIEW_MODE
  TOSS_PAYMENTS_RETURN_BASE_URL
  WEB_BASE_URL
  ```

  Dev examples use `CHANGE_ME_TEST_GCK`, `CHANGE_ME_TEST_GSK`, `CHANGE_ME_TEST_CK`, and `CHANGE_ME_TEST_SK`; stage/prod keep review mode false. Do not add any real key.

- [ ] **Step 2: Validate compose and deployment scripts**

  Run `docker compose --env-file env/stack.dev.env.example -f apps/compose.yml -f apps/compose.dev.yml config`, repeat for stage/prod overlays with their example files, run `bash -n scripts/deploy-dev.sh`, and search the changed infra worktree for legacy variable names. Expected: compose parses, shell syntax passes, and no active config retains a legacy Toss Pay variable.

### Task 9: 전체 검증과 범위 감사

- [ ] **Step 1: API verification under Node 22**

  Run payment/database focused tests, full Jest, `npm run build`, OpenAPI parse validation, and a Nest boot/health smoke if local DB-independent startup is available. Record the known unrelated operator JWT baseline failure separately; no new failures are allowed.

- [ ] **Step 2: Client verification under Node 22**

  Run all ChromeHeadless tests and `npm run build`. Inspect the output/source map strings to ensure no `test_gsk_`, `test_sk_`, `billingKey`, or `authKey` value is embedded by configuration.

- [ ] **Step 3: Migration verification**

  Against an empty PostgreSQL 16 admin DB, apply all admin migrations, run them a second time with no pending migrations, revert the PG migration, and re-apply it. Query `information_schema.columns` to confirm `payment_key`, `customer_key`, encrypted secret fields, three idempotency columns, and `last_transaction_key` exist while `pay_token` and `review_user_id` do not.

- [ ] **Step 4: Diff and isolation audit**

  For each feature worktree, inspect `git status --short`, `git diff --check`, `git diff --stat`, and the full diff. Confirm every changed line traces to this plan, no entitlement/credit/renewal implementation exists, and the three `*-access-credit` worktrees retain their original HEAD and clean/dirty status.

- [ ] **Step 5: Read-only code review**

  Use the `superpowers:requesting-code-review` template for a read-only review of the three worktree diffs against this plan. Fix all Critical and Important findings with a failing regression test first, then rerun the affected focused and full verification commands.

### Deployment handoff (2026-08-14)

- 코드는 API `880c053`, 고객 웹 `4b361ef`, 인프라 `4d32022`로 각 원격 `dev`에 반영되었다.
- 배포 전 dev Mac mini의 ignored `clipper_infra/env/stack.dev.env`에 두 테스트 키 세트와 HTTPS URL, review mode를 직접 설정한다. Secret Key는 채팅·커밋·로그에 남기지 않는다.
- 첫 PG 배포는 새 API 이미지를 빌드하고 API만 일시 중지한 뒤 admin migration을 적용하고 API·고객 웹을 재생성한다. 정확한 명령은 `clipper_infra/runbooks/deploy-dev.md`에 있다.
- Nginx Proxy Manager의 `dev-api.clipperstudio.ai` access log가 billing `authKey`와 `receiptToken` query를 저장하지 않도록 임시 dev host의 `access_log off;`를 확인한 뒤 카드 등록 스모크를 실행한다.
- 이 작업 환경에서 dev Mac mini의 LAN/DDNS SSH가 모두 timeout이어서 서버 migration·container 재생성·브라우저 스모크는 미수행 상태다.
