// Diagnostic retained after the fix: all cancellation cases must now refund.
// No product edits, real financial endpoints, ML, or existing user data.
// Usage: node --test <this file> (current integration worktree must be built).
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const http = require('node:http');
const { once } = require('node:events');
const { performance } = require('node:perf_hooks');

const repo = path.resolve(__dirname, '../../.worktrees/dev-pg-local-validation-20260917/desktop/clipper_nestjs');
// Reuse the existing real JSON/coordinator/JobsService fixture without running
// its other tests. The injected pending prepareTail models an earlier batch.
const fixtureFile = path.join(repo, 'test/variation-v2-initial-billing-restart.integration.test.js');
const fixtureText = fs.readFileSync(fixtureFile, 'utf8');
const boundary = fixtureText.indexOf('// Regression target:');
assert.ok(boundary > 0, 'Diagnostic fixture boundary must still exist');
const helperModule = new Module(fixtureFile, module);
helperModule.filename = fixtureFile;
helperModule.paths = Module._nodeModulePaths(path.dirname(fixtureFile));
helperModule._compile(fixtureText.slice(0, boundary) + '\nmodule.exports = { fixture, open, AUTH };', fixtureFile);
const { fixture, open, AUTH } = helperModule.exports;
const { DialogHighlightPythonStageRunner } = require(path.join(repo,
  'dist/modules/dialog-highlight/application/dialog-highlight-python-stage.runner'));

for (const mode of ['keep-job', 'delete-before-outbox', 'outbox-before-delete']) {
  test(`post-charge cancellation restart diagnostic: ${mode}`, async t => {
    const f = await fixture(t);
    f.service.prepareTail = f.crashGate;
    const result = await f.service.render(f.project.id, AUTH);
    const jobId = result.jobIds[0];
    const charged = (await f.store.attempts.list()).find(a => a.featureReference.reference === jobId);
    assert.equal(f.runs.size, 2);
    assert.equal(f.mapperCalls(), 0, 'No renderer or media preparation started');
    await f.jobService.cancel(jobId, AUTH);
    assert.equal((await f.store.jobs.get(jobId)).status, 'cancelled');
    assert.equal((await f.store.outbox.list()).length, 0, 'Cancellation has not staged its refund');

    if (mode === 'outbox-before-delete') {
      // Control: use real finalizer, simulate financial network unavailability.
      const realFail = f.operations.fail;
      f.operations.fail = async () => { throw Error('diagnostic offline'); };
      const delivered = await f.store.billing.fail({ attemptId: charged.id,
        ownerSubjectId: AUTH.subjectId, runId: charged.webApiRunId, operationKey: charged.operationKey },
      AUTH.accessToken, 'cancelled before rendering', [{ kind: 'desktop_job', reference: jobId, status: 'failed' }]);
      assert.equal(delivered, false);
      assert.equal((await f.store.outbox.list()).length, 1);
      f.operations.fail = realFail;
    }
    if (mode !== 'keep-job') {
      await f.jobService.deleteArchiveEntry(jobId, AUTH);
      assert.equal(await f.store.jobs.get(jobId), null);
      const deleted = (await f.store.attempts.list()).find(a => a.id === charged.id);
      assert.equal(deleted.userDeleted, true);
    }

    // Model app exit without resuming preparation; load all records anew.
    const boot = open(f.config, f.operations);
    const interrupted = await boot.jobs.markInterruptedActiveJobs();
    await boot.reconcile.reconcile(await boot.jobs.list(), interrupted);
    await boot.billing.recoverPending(AUTH.subjectId, 'fresh-login');
    await boot.billing.recoverPending(AUTH.subjectId, 'fresh-login');
    const after = (await boot.attempts.list()).find(a => a.id === charged.id);
    const refundReceived = f.refunds.includes(charged.webApiRunId);
    assert.equal(after.state, 'server_confirmed');
    assert.equal(refundReceived, true);
    assert.equal(f.runs.size, 2, 'No fresh charge during recovery');
    assert.equal(f.mapperCalls(), 0);
    t.diagnostic(JSON.stringify({ mode, jobRetained: !!await boot.jobs.get(jobId),
      attemptState: after.state, refundReceived, totalRefunds: f.refunds.length,
      outboxRemaining: (await boot.outbox.list()).length }));
  });
}

async function hangingDelete(timeoutMs, stallMs = 0) {
  let received = false;
  const server = http.createServer((req, res) => {
    if (req.method === 'DELETE') { received = true; req.resume(); return; }
    res.writeHead(404); res.end();
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const runner = new DialogHighlightPythonStageRunner({});
  const started = performance.now();
  try {
    const done = runner.cancelStageJob(`http://127.0.0.1:${server.address().port}`, 'diagnostic:prepare_media', timeoutMs);
    if (stallMs) {
      const deadline = performance.now() + stallMs;
      while (performance.now() < deadline) { /* controlled scheduler delay */ }
    }
    await done;
    return { received, resolved: true, elapsedMs: Math.round(performance.now() - started) };
  } finally {
    server.closeAllConnections();
    await new Promise((resolve, reject) => server.close(err => err ? reject(err) : resolve()));
  }
}

test('Dialog original 5ms deadline vs production default: actual loopback HTTP', { timeout: 15000 }, async t => {
  const short = [];
  for (let i = 0; i < 20; i++) short.push(await hangingDelete(5));
  const normal = [];
  for (let i = 0; i < 3; i++) normal.push(await hangingDelete(undefined));
  assert.ok([...short, ...normal].every(r => r.resolved));
  assert.ok(normal.every(r => r.received), 'Default timeout permits these local requests to arrive');
  t.diagnostic(JSON.stringify({ shortDeadlineMs: 5, short,
    productionDefaultDeadlineMs: 1000, normal }));
});

test('Dialog 5ms arrival assertion is not guaranteed under scheduler delay', { timeout: 3000 }, async t => {
  const result = await hangingDelete(5, 30);
  assert.equal(result.resolved, true);
  t.diagnostic(JSON.stringify({ forcedSchedulerDelayMs: 30, ...result }));
});

test('Dialog cancellation timeout does not require server arrival: deterministic transport boundary', async t => {
  const originalFetch = global.fetch;
  let method, signalWasAborted = false;
  global.fetch = async (_url, options) => {
    method = options.method;
    return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => {
      signalWasAborted = true;
      reject(options.signal.reason);
    }, { once: true }));
  };
  // AbortSignal.timeout is unref'd; keep this diagnostic process alive.
  const keepAlive = setTimeout(() => {}, 1000);
  try {
    await new DialogHighlightPythonStageRunner({}).cancelStageJob('http://127.0.0.1:1', 'job:stage', 5);
    assert.equal(method, 'DELETE');
    assert.equal(signalWasAborted, true);
    t.diagnostic('DELETE invoked; hung transport aborted; cancel promise fulfilled without server acknowledgement');
  } finally { clearTimeout(keepAlive); global.fetch = originalFetch; }
});
