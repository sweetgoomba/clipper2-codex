# Desktop Entitlement and Credit Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 데스크톱에서 새 이용 자격·출처별 크레딧 정보를 표시하고, 하위 등급에 포함되지 않은 플러그인을 라우트·스토어·실행·모델 설치 경계에서 일관되게 차단한다.

**Architecture:** `clipper_nestjs`는 렌더러 JWT를 사용해 web API의 `/access/current`·`/credits/*`를 프록시하고 플러그인 HTTP start/install 전에 권한을 검증한다. Angular은 서버 결과로 잠금·안내를 표시하며, Electron은 렌더러가 로컬 IPC를 직접 호출하는 우회 경로에서도 web API 권한을 다시 확인한다. 실제 크레딧 차감은 계속 web API가 최종 강제한다.

**Tech Stack:** NestJS/TypeScript local gateway, Angular 22.1, Electron 43.3, Node.js 24, `node:test`, Karma/Jasmine

## Global Constraints

- 작업 브랜치는 세 저장소 모두 `feat/access-credit-system-replacement`이다.
- 경로는 `/Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit`, `/Users/jina/project/adlight/.worktrees/clipper_angular-access-credit`, `/Users/jina/project/adlight/.worktrees/clipper_electron-access-credit`이다.
- 세 저장소 모두 Node 24를 사용한다.
- Angular 22.1과 Electron 43.3 업그레이드 상태를 유지하고 빌드 캐시를 SQLite로 우회하지 않는다.
- 안무·대사·숏폼·베리에이션 등 기존 작업 실행 흐름을 재구성하지 않고 인가·계약 경계만 교체한다.
- 서버가 알려준 `allowedPluginKeys`를 UI가 임의로 확장하지 않는다.
- 사용자 노출 플러그인 키는 `shortform_url`, `shortform_paste`, `shortform_prompt`, `dance_highlight`, `dialog_highlight`, `comment_overlay`, `variation`이다.
- `clipper_video_render`, `tts_supertonic` 등 내부 런타임 dependency는 사용자 플러그인 등급 키로 취급하지 않고 상위 workflow가 인가된 뒤 내부적으로 사용한다.
- 이용 자격 없음, 플러그인 미포함, 크레딧 부족을 서로 다른 사용자 메시지로 표시한다.
- 오프라인 권한 유예 정책이 없으므로 이 단계에서는 권한 확인 불가 시 신규 실행·설치를 fail closed하고 네트워크 오류로 안내한다.
- 로컬 개발에서도 권한 우회 플래그를 만들지 않고, 테스트 계정에 관리자가 표준 최상위 등급을 지급한다.

---

### Task 1: Replace the Local Nest License Proxy with Access/Credit Proxies

**Files (`clipper_nestjs`):**
- Delete: `src/modules/licenses/application/licenses.service.ts`
- Delete: `src/modules/licenses/presentation/licenses.controller.ts`
- Delete: `src/modules/licenses/licenses.module.ts`
- Create: `src/modules/access/application/access.service.ts`
- Create: `src/modules/access/presentation/access.controller.ts`
- Create: `src/modules/access/access.module.ts`
- Create: `src/modules/credits/application/credits.service.ts`
- Create: `src/modules/credits/presentation/credits.controller.ts`
- Create: `src/modules/credits/credits.module.ts`
- Modify: `src/app.module.ts`
- Modify: `src/core/web-api/web-api-operation-run.service.ts`
- Create: `test/access-credit-proxy.test.js`
- Modify: existing operation proxy tests that reference `/operations/ledger`

**Interfaces:**
- Consumes: authenticated web API endpoints `/access/current`, `/credits/summary`, `/credits/grants`, `/credits/ledger`
- Produces: same local `/v1/access/current` and `/v1/credits/*` raw proxy endpoints for Angular

- [ ] **Step 1: Write a failing built-output proxy test**

```js
test('access proxy forwards the caller bearer token', async () => {
  await service.current({ accessToken: 'user-jwt' });
  assert.deepEqual(webApi.calls[0], ['/access/current', { bearerToken: 'user-jwt' }]);
});
```

Also assert ledger now targets `/credits/ledger` and quote reason accepts `NO_ACTIVE_ACCESS`, `PLUGIN_NOT_ENTITLED`, and `INSUFFICIENT_CREDITS`.

- [ ] **Step 2: Run build and test to confirm failure**

Run: `nvm use 24 && npm run build && node --test test/access-credit-proxy.test.js`

Expected: FAIL because the access/credits modules do not exist.

- [ ] **Step 3: Implement thin authenticated proxies**

Every controller obtains `AuthContextService.fromHttpHeaders(headers)`, requires a bearer token, and passes it to `WebApiClient`. Do not calculate balances or plugin permissions locally.

- [ ] **Step 4: Run focused tests and build**

Run: `nvm use 24 && npm run build && node --test test/access-credit-proxy.test.js`

Expected: PASS.

- [ ] **Step 5: Commit in `clipper_nestjs`**

```bash
git add -A src/modules src/core/web-api test/access-credit-proxy.test.js
git commit -m "refactor: proxy access and source credit contracts"
```

### Task 2: Enforce Plugin Entitlement in the Local Nest Control Plane

**Files (`clipper_nestjs`):**
- Create: `src/modules/plugins/application/plugin-access.service.ts`
- Modify: `src/modules/plugins/application/plugins.service.ts`
- Modify: `src/modules/plugins/presentation/plugins.controller.ts`
- Modify: `src/modules/plugins/domain/plugin.model.ts`
- Modify: `src/modules/plugins/plugins.module.ts`
- Create: `test/plugin-access-controller.test.js`

**Interfaces:**
- Consumes: authenticated access response and canonical user-visible plugin names
- Produces: `entitled`/`entitlementReason` on list/status plus enforced start/install admission

- [ ] **Step 1: Write failing access-decision tests**

```ts
it('allows an entitled visible plugin and internal runtimes', async () => {
  access.current.mockResolvedValue({ access: { allowedPluginKeys: ['variation'] } });
  await expect(service.assertAllowed(token, 'variation')).resolves.toBeUndefined();
  await expect(service.assertAllowed(token, 'clipper_video_render')).resolves.toBeUndefined();
});

it('denies a visible plugin missing from the tier', async () => {
  access.current.mockResolvedValue({ access: { allowedPluginKeys: [] } });
  await expect(service.assertAllowed(token, 'variation')).rejects.toMatchObject({ code: 'PLUGIN_NOT_ENTITLED' });
});
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `nvm use 24 && npm run build && node --test test/plugin-access-controller.test.js`

Expected: FAIL because plugin routes do not authenticate or authorize.

- [ ] **Step 3: Thread auth through plugin routes**

`list`, `getManifest`, `getStatus`, `start`, `install`, and `uninstall` receive headers and authenticate. List keeps locked plugins visible with `{ entitled: false, entitlementReason }`. Start/install/uninstall call `assertAllowed` before any resource assessment, model download, file mutation, or Electron plugin-host call. Stop remains allowed for an already-running process to avoid trapping resources.

- [ ] **Step 4: Map server failures without hiding their code**

Return 403 with Nest's raw error body containing `PLUGIN_NOT_ENTITLED` or `NO_ACTIVE_ACCESS`; upstream network failure returns 503. Do not turn these into a resource-policy 409.

- [ ] **Step 5: Run focused and full tests**

Run: `nvm use 24 && npm run build && node --test test/plugin-access-controller.test.js && node --test test/*.test.js`

Expected: PASS.

- [ ] **Step 6: Commit in `clipper_nestjs`**

```bash
git add src/modules/plugins test/plugin-access-controller.test.js
git commit -m "feat: enforce plugin entitlements in desktop gateway"
```

### Task 3: Split Shortform Billing by Server-Derived Source Mode

**Files (`clipper_nestjs`):**
- Modify: `src/modules/shortform/application/shortform-render-orchestrator.ts`
- Modify: shortform render tests that assert `shortform.create`
- Modify: `src/core/web-api/web-api-operation-run.service.ts`
- Create: `test/shortform-operation-entitlement.test.js`

**Interfaces:**
- Consumes: web API operation keys from the API core plan
- Produces: server-derived shortform operation keys that cannot be selected arbitrarily by the client

- [ ] **Step 1: Write the source-mode mapping test**

```js
assert.equal(shortformOperationKeyForSourceMode('url'), 'shortform_url.create');
assert.equal(shortformOperationKeyForSourceMode('paste'), 'shortform_paste.create');
assert.equal(shortformOperationKeyForSourceMode('prompt'), 'shortform_prompt.create');
assert.equal(shortformOperationKeyForSourceMode('manual'), 'shortform_prompt.create');
```

- [ ] **Step 2: Run build and test to confirm failure**

Run: `nvm use 24 && npm run build && node --test test/shortform-operation-entitlement.test.js`

Expected: FAIL because the orchestrator uses the single legacy key.

- [ ] **Step 3: Derive the operation key from persisted project source**

Both quote and actual `operationRuns.start` use the persisted `current.source.mode`; no HTTP `pluginKey` or arbitrary operation key from the renderer is forwarded into the billed start.

- [ ] **Step 4: Run shortform tests**

Run: `nvm use 24 && npm run build && node --test test/shortform-operation-entitlement.test.js test/shortform*.test.js`

Expected: PASS.

- [ ] **Step 5: Commit in `clipper_nestjs`**

```bash
git add src/modules/shortform src/core/web-api test/shortform-operation-entitlement.test.js
git commit -m "refactor: derive shortform billing key from source mode"
```

### Task 4: Add Angular Access State, Locked Routes, and Store Messaging

**Files (`clipper_angular`):**
- Create: `src/core/access/access-entitlement.service.ts`
- Create: `src/core/access/access-entitlement.service.spec.ts`
- Modify: `src/core/plugins/plugin-route.guards.ts`
- Modify: `src/core/plugins/plugin-route.guards.spec.ts`
- Modify: `src/core/plugins/plugin-status.service.ts`
- Modify: `src/core/plugins/plugin-status.service.spec.ts`
- Modify: `src/shell/store/plugin-card/plugin-card.component.ts`
- Modify: `src/shell/store/plugin-card/plugin-card.component.html`
- Modify: `src/shell/store/plugin-card/plugin-card.component.scss`
- Modify: `src/shell/store/plugin-card/plugin-card.component.spec.ts`
- Modify: `src/shell/store/plugin-detail/plugin-detail.component.ts`
- Modify: `src/shell/store/plugin-detail/plugin-detail.component.html`
- Modify: `src/shell/store/plugin-detail/plugin-detail.component.spec.ts`
- Modify: `src/app/app.routes.ts`

**Interfaces:**
- Consumes: local Nest `/access/current` and plugin list entitlement fields
- Produces: `pluginEntitledGuard` and locked-but-visible store/navigation behavior

- [ ] **Step 1: Write failing route and card tests**

```ts
it('redirects an installed but unentitled plugin to its store detail', async () => {
  access.isPluginAllowed.and.resolveTo(false);
  expect(await pluginEntitledGuard(route('variation'))).toEqual(
    router.createUrlTree(['/store'], { queryParams: { select: 'variation', reason: 'not-entitled' } }),
  );
});

it('shows the required plan-upgrade message while keeping the card visible', () => {
  setItem({ name: 'variation', entitled: false });
  expect(text()).toContain('상위 요금제에서 사용할 수 있습니다');
});
```

- [ ] **Step 2: Run focused Angular tests and confirm failure**

Run: `nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/core/access/*.spec.ts' --include='src/core/plugins/*.spec.ts' --include='src/shell/store/**/*.spec.ts'`

Expected: FAIL because routes only check installation state.

- [ ] **Step 3: Implement access state and guard order**

Plugin routes use `[pluginInstalledGuard, pluginEntitledGuard]`. The entitlement service caches only the in-memory latest response and exposes `refresh`, `current`, and `isPluginAllowed`; it clears on logout/session change. It never grants on request failure.

- [ ] **Step 4: Implement locked store actions**

Locked cards/details disable install/open/start controls and link to the web pricing page through the existing external URL mechanism. Internal runtime plugins remain absent from user entitlement UI.

- [ ] **Step 5: Run focused tests and build**

Run: `nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/core/access/*.spec.ts' --include='src/core/plugins/*.spec.ts' --include='src/shell/store/**/*.spec.ts' && npm run build:devapp`

Expected: PASS.

- [ ] **Step 6: Commit in `clipper_angular`**

```bash
git add src/core/access src/core/plugins src/shell/store src/app/app.routes.ts
git commit -m "feat: show and guard desktop plugin entitlements"
```

### Task 5: Replace Angular License/Credit Summaries and Operation Errors

**Files (`clipper_angular`):**
- Modify: `src/shell/settings/settings/settings-account.service.ts`
- Modify: `src/shell/settings/settings/settings-account.service.spec.ts`
- Modify: `src/shell/settings/settings/settings.component.ts`
- Modify: `src/shell/settings/settings/settings.component.html`
- Modify: `src/shell/settings/settings/settings.component.scss`
- Modify: `src/shell/settings/settings/settings.component.spec.ts`
- Modify: `src/core/operations/operation-billing.service.ts`
- Modify: `src/core/operations/operation-billing.service.spec.ts`
- Modify: `src/shared/operations/operation-charge-guard.service.ts`
- Modify: `src/shared/operations/operation-charge-guard.service.spec.ts`
- Modify: `src/features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component.ts`
- Modify: shortform specs that assert `shortform.create`

**Interfaces:**
- Consumes: local `/access/current`, `/credits/summary`, `/credits/grants`, `/credits/ledger`, and new quote reasons
- Produces: source-aware settings UI and reason-specific work admission dialogs

- [ ] **Step 1: Write failing settings and error-message tests**

Test held/spendable balances, source rows, expiry, no-access blocked copy, and distinct dialogs:

```text
NO_ACTIVE_ACCESS -> 사용 가능한 이용권이 없습니다.
PLUGIN_NOT_ENTITLED -> 현재 요금제에서 이 플러그인을 사용할 수 없습니다.
INSUFFICIENT_CREDITS -> 사용 가능한 크레딧이 부족합니다.
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run: `nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/shell/settings/settings/*.spec.ts' --include='src/core/operations/*.spec.ts' --include='src/shared/operations/*.spec.ts'`

Expected: FAIL because settings use `licenses/current` and quote uses legacy reasons.

- [ ] **Step 3: Implement new service methods and views**

Settings displays plan tier/source/period/next grant/allowed plugins, held and spendable totals, source balances, and recent ledger. Remove queued-license fields and `tokenBalance` compatibility fallbacks.

- [ ] **Step 4: Use mode-specific shortform quote keys**

Angular quote uses the route/input mode mapping `url -> shortform_url.create`, `paste -> shortform_paste.create`, `prompt -> shortform_prompt.create`; actual Nest execution still derives independently from the saved project.

- [ ] **Step 5: Run tests and build**

Run: `nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless --include='src/shell/settings/settings/*.spec.ts' --include='src/core/operations/*.spec.ts' --include='src/shared/operations/*.spec.ts' --include='src/features/shortform/pages/shortform-workflow-page/*.spec.ts' && npm run build:devapp`

Expected: PASS.

- [ ] **Step 6: Commit in `clipper_angular`**

```bash
git add src/shell/settings src/core/operations src/shared/operations src/features/shortform
git commit -m "refactor: show access and source credits on desktop"
```

### Task 6: Enforce Direct Electron IPC Start and Model-Install Paths

**Files (`clipper_electron`):**
- Create: `src/main/access/web-access-authorizer.ts`
- Modify: `src/main/plugin/plugin-ipc.ts`
- Modify: `src/main/model-download-ipc.ts`
- Modify: `src/main/main.ts`
- Create: `test/web-access-authorizer.test.js`
- Create: `test/plugin-ipc-access.test.js`
- Create: `test/model-download-access.test.js`

**Interfaces:**
- Consumes: `getApiBase()`, `getToken()`, and web API `/access/current`
- Produces: `PluginAccessAuthorizer.assertAllowed(pluginName): Promise<void>` injected into direct IPC registrations

- [ ] **Step 1: Write failing authorizer tests**

```js
await assert.rejects(
  authorizer({ token: null }).assertAllowed('variation'),
  /NO_ACTIVE_ACCESS/,
);
await assert.rejects(
  authorizer({ allowedPluginKeys: [] }).assertAllowed('variation'),
  /PLUGIN_NOT_ENTITLED/,
);
await assert.doesNotReject(
  authorizer({ allowedPluginKeys: ['variation'] }).assertAllowed('variation'),
);
```

- [ ] **Step 2: Run build and tests to confirm failure**

Run: `nvm use 24 && npm run build && node --test test/web-access-authorizer.test.js test/plugin-ipc-access.test.js test/model-download-access.test.js`

Expected: FAIL because direct IPC bypasses subscription entitlement.

- [ ] **Step 3: Implement the online authorizer**

Fetch `${getApiBase()}/access/current` with `Authorization: Bearer ${getToken()}`. Gate only the seven user-visible plugin keys; allow internal runtime dependencies. Missing token yields `NO_ACTIVE_ACCESS`, 403 preserves its server reason, and network failure yields `ACCESS_CHECK_UNAVAILABLE`. Do not persist entitlement to disk or add an offline grace value.

- [ ] **Step 4: Inject at every direct mutation/start boundary**

Call `assertAllowed` before `plugin.getUrl`, `plugin.start`, and `modelDownload.startPlugin`, and before any direct install/model download side effect. Status/list/stop and opening the data directory do not create new paid access and remain available.

- [ ] **Step 5: Run Electron tests and build**

Run: `nvm use 24 && npm test && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit in `clipper_electron`**

```bash
git add src/main/access src/main/plugin/plugin-ipc.ts src/main/model-download-ipc.ts src/main/main.ts test
git commit -m "feat: enforce plugin access in electron ipc"
```

### Task 7: Verify the Three-Repository Desktop Contract Together

**Files:**
- Modify: none
- Test: all desktop access/credit/plugin paths

**Interfaces:**
- Consumes: committed heads from Tasks 1-6
- Produces: a green desktop integration baseline for the final release gate

- [ ] **Step 1: Run all automated checks with Node 24**

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit && nvm use 24 && npm run build && node --test test/*.test.js
cd /Users/jina/project/adlight/.worktrees/clipper_angular-access-credit && nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build:local && npm run build:devapp && npm run build:packaged
cd /Users/jina/project/adlight/.worktrees/clipper_electron-access-credit && nvm use 24 && npm test && npm run build
```

Expected: PASS.

- [ ] **Step 2: Run the local authenticated smoke test**

Start web API, local Nest, Angular devapp, and Electron. With an admin-granted lower tier, confirm locked plugins remain visible but cannot route/start/install; with the highest standard tier, confirm they work. With held top-up credits and no active access, confirm settings shows held balance but operations and starts remain blocked.

- [ ] **Step 3: Record exact commit hashes in the roadmap verification record**

Run:

```bash
git -C /Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_angular-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_electron-access-credit rev-parse HEAD
```

Expected: three hashes recorded without merging any repository to `dev`.
