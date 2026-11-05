const assert = require('node:assert/strict');
const test = require('node:test');
const { BadGatewayException, UnauthorizedException } = require('@nestjs/common');
const { AccessService } = require('../dist/modules/access/application/access.service');
const { AccessController } = require('../dist/modules/access/presentation/access.controller');
const { CreditsService } = require('../dist/modules/credits/application/credits.service');
const { CreditsController } = require('../dist/modules/credits/presentation/credits.controller');

test('access proxy forwards the caller bearer token', async () => {
  const calls = [];
  const service = new AccessService({
    getJson: async (path, options) => {
      calls.push([path, options]);
      return {
        access: {
          source: 'subscription',
          tierId: 'tier-1',
          tierCode: 'pro',
          tierName: 'Pro',
          entitlementMode: 'all',
          allowedPluginKeys: [],
          spendableCreditSources: ['subscription', 'topup'],
          serverOnlyField: 'must-not-leak',
        },
        envelopeExtra: true,
      };
    },
  });

  const result = await service.current({ accessToken: 'user-jwt' });

  assert.equal(result.access.tierCode, 'pro');
  assert.equal('serverOnlyField' in result.access, false);
  assert.equal('envelopeExtra' in result, false);
  assert.deepEqual(calls, [['/access/current', { bearerToken: 'user-jwt' }]]);
  await assert.rejects(() => service.current({}), UnauthorizedException);
});

test('access proxy accepts a promotion plan from the Web API', async () => {
  const service = new AccessService({
    getJson: async () => ({ access: {
      source: 'promotion', tierId: 'tier-pro', tierCode: 'pro', tierName: 'Pro',
      entitlementMode: 'all', allowedPluginKeys: [],
      spendableCreditSources: ['promotion', 'topup'],
    } }),
  });
  const result = await service.current({ accessToken: 'user-jwt' });
  assert.equal(result.access.source, 'promotion');
  assert.deepEqual(result.access.spendableCreditSources, ['promotion', 'topup']);
});

test('access proxy rejects malformed provider responses', async () => {
  for (const response of [
    {},
    { access: { tierCode: 'pro' } },
    {
      access: {
        source: 'unknown',
        tierId: 'tier-1',
        tierCode: 'pro',
        tierName: 'Pro',
        entitlementMode: 'all',
        allowedPluginKeys: [],
        spendableCreditSources: [],
      },
    },
  ]) {
    const service = new AccessService({ getJson: async () => response });
    await assert.rejects(
      () => service.current({ accessToken: 'user-jwt' }),
      (error) => error instanceof BadGatewayException,
    );
  }
});

test('credit proxies forward summary, grants, and ledger with paging', async () => {
  const calls = [];
  const service = new CreditsService({
    getJson: async (path, options) => {
      calls.push([path, options]);
      if (path === '/credits/summary') {
        return {
          heldBalance: 120,
          spendableBalance: 120,
          bySource: [{ source: 'topup', credits: 120, extra: true }],
          currentBenefit: {
            kind: 'plan_period',
            source: 'subscription',
            initialCredits: 500,
            remainingCredits: 120,
            periodStart: '2026-09-01T00:00:00.000Z',
            periodEnd: '2026-10-01T00:00:00.000Z',
            extra: true,
          },
          extra: true,
        };
      }
      if (path.startsWith('/credits/grants')) {
        return {
          items: [{
            id: 'grant-1',
            source: 'topup',
            initialCredits: 120,
            remainingCredits: 120,
            grantedAt: '2026-09-17T00:00:00.000Z',
            expiresAt: null,
            benefitPeriodStart: null,
            benefitPeriodEnd: null,
            status: 'active',
            statusLabel: null,
            extra: true,
          }],
          nextCursor: null,
          extra: true,
        };
      }
      return {
        items: [{
          id: 'ledger-1',
          creditGrantId: 'grant-1',
          userId: 'user-1',
          type: 'operation_charge',
          deltaCredits: -20,
          balanceAfter: 100,
          operationRunId: 'run-1',
          paymentOrderId: null,
          referenceKey: 'operation:variation.render',
          reason: 'operation:variation.render',
          createdAt: '2026-09-17T00:00:00.000Z',
          extra: true,
        }],
        nextCursor: null,
        extra: true,
      };
    },
  });

  assert.deepEqual(await service.summary({ accessToken: 'user-jwt' }), {
    heldBalance: 120,
    spendableBalance: 120,
    bySource: [{ source: 'topup', credits: 120 }],
    currentBenefit: {
      kind: 'plan_period',
      source: 'subscription',
      initialCredits: 500,
      remainingCredits: 120,
      periodStart: '2026-09-01T00:00:00.000Z',
      periodEnd: '2026-10-01T00:00:00.000Z',
    },
  });
  const grants = await service.grants({ accessToken: 'user-jwt' }, { limit: 10, cursor: 'grant_cursor' });
  const ledger = await service.ledger({ accessToken: 'user-jwt' }, { limit: 20, cursor: 'ledger_cursor' });
  assert.equal('extra' in grants, false);
  assert.equal('extra' in grants.items[0], false);
  assert.equal('extra' in ledger.items[0], false);

  assert.deepEqual(calls, [
    ['/credits/summary', { bearerToken: 'user-jwt' }],
    ['/credits/grants?limit=10&cursor=grant_cursor', { bearerToken: 'user-jwt' }],
    ['/credits/ledger?limit=20&cursor=ledger_cursor', { bearerToken: 'user-jwt' }],
  ]);
  await assert.rejects(() => service.summary({}), UnauthorizedException);
});

test('credit proxies reject malformed summary and page responses', async () => {
  const cases = [
    ['/credits/summary', { heldBalance: 10.5, spendableBalance: 10, bySource: [] }, 'summary'],
    ['/credits/summary', { heldBalance: 10, spendableBalance: -1, bySource: [] }, 'summary'],
    ['/credits/summary', { heldBalance: 10, spendableBalance: 10, bySource: [{ source: 'mystery', credits: 10 }] }, 'summary'],
    ['/credits/grants', { items: 'invalid', nextCursor: null }, 'grants'],
    ['/credits/ledger', { items: [], nextCursor: 42 }, 'ledger'],
  ];
  for (const [path, response, method] of cases) {
    const service = new CreditsService({
      getJson: async (requestedPath) => {
        assert.equal(requestedPath, path);
        return response;
      },
    });
    await assert.rejects(
      () => service[method]({ accessToken: 'user-jwt' }),
      (error) => error instanceof BadGatewayException,
    );
  }
});

test('credit summary remains compatible when an older Web API omits currentBenefit', async () => {
  const summaries = [
    { heldBalance: 0, spendableBalance: 0, bySource: [] },
    { heldBalance: 0, spendableBalance: 0, bySource: [], currentBenefit: null },
  ];

  for (const response of summaries) {
    const service = new CreditsService({ getJson: async () => response });
    assert.deepEqual(await service.summary({ accessToken: 'user-jwt' }), {
      heldBalance: 0,
      spendableBalance: 0,
      bySource: [],
      currentBenefit: null,
    });
  }
});

test('credit summary accepts every valid Web API currentBenefit variant', async () => {
  const benefits = [
    {
      kind: 'free_trial',
      source: 'free_trial',
      initialCredits: 400,
      remainingCredits: 300,
      periodStart: '2026-09-01T00:00:00.000Z',
      periodEnd: null,
    },
    ...['subscription', 'admin_plan', 'promotion'].map((source) => ({
      kind: 'plan_period',
      source,
      initialCredits: 400,
      remainingCredits: 300,
      periodStart: '2026-09-01T00:00:00.000Z',
      periodEnd: '2026-10-01T00:00:00.000Z',
    })),
  ];

  for (const currentBenefit of benefits) {
    const service = new CreditsService({
      getJson: async () => ({
        heldBalance: 300,
        spendableBalance: 300,
        bySource: [{ source: currentBenefit.source, credits: 300 }],
        currentBenefit,
      }),
    });
    assert.deepEqual(
      (await service.summary({ accessToken: 'user-jwt' })).currentBenefit,
      currentBenefit,
    );
  }
});

test('credit summary rejects currentBenefit variants outside the Web API contract', async () => {
  const benefit = {
    kind: 'plan_period',
    source: 'subscription',
    initialCredits: 400,
    remainingCredits: 300,
    periodStart: '2026-09-01T00:00:00.000Z',
    periodEnd: '2026-10-01T00:00:00.000Z',
  };
  const invalidBenefits = [
    { ...benefit, kind: 'free_trial', source: 'subscription' },
    { ...benefit, kind: 'plan_period', source: 'free_trial' },
    { ...benefit, periodEnd: null },
  ];

  for (const currentBenefit of invalidBenefits) {
    const service = new CreditsService({
      getJson: async () => ({
        heldBalance: 300,
        spendableBalance: 300,
        bySource: [{ source: currentBenefit.source, credits: 300 }],
        currentBenefit,
      }),
    });
    await assert.rejects(
      () => service.summary({ accessToken: 'user-jwt' }),
      (error) => error instanceof BadGatewayException,
    );
  }
});

test('access and credit controllers obtain auth context from request headers', async () => {
  const headers = { authorization: 'Bearer user-jwt' };
  const auth = {
    fromHttpHeaders: async (received) => {
      assert.equal(received, headers);
      return { accessToken: 'user-jwt' };
    },
  };
  const accessController = new AccessController({ current: async (context) => context }, auth);
  const creditsController = new CreditsController({
    summary: async (context) => context,
    grants: async (_context, query) => query,
    ledger: async (_context, query) => query,
  }, auth);

  assert.deepEqual(await accessController.current(headers), { accessToken: 'user-jwt' });
  assert.deepEqual(await creditsController.summary(headers), { accessToken: 'user-jwt' });
  assert.deepEqual(await creditsController.grants(headers, { limit: 5 }), { limit: 5 });
  assert.deepEqual(await creditsController.ledger(headers, { limit: 5 }), { limit: 5 });
});

test('access proxy accepts the current free plan source without changing entitlements', async () => {
  const access = { source: 'free', tierId: 'tier-free', tierCode: 'free', tierName: 'Free',
    entitlementMode: 'allowlist', allowedPluginKeys: ['dance_highlight'],
    spendableCreditSources: ['topup', 'free_trial'] };
  const service = new AccessService({ getJson: async () => ({ access }) });
  assert.deepEqual((await service.current({ accessToken: 'user-jwt' })).access, access);
});
