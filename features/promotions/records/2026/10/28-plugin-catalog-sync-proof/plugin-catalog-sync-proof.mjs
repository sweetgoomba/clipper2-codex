// Throwaway feasibility proof. This is NOT a product API or a deployment hook.
// Reads actual app registration source, sends an artifact over HTTP, persists in
// an isolated PostgreSQL cluster, and checks discovery/publication boundaries.
import assert from 'node:assert/strict';
import { createHash, randomBytes } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';

const arg = (key, fallback) => {
  const index = process.argv.indexOf(key);
  return index < 0 ? fallback : process.argv[index + 1];
};
const sourceRoot = arg('--source-root', '/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028');
const dependencies = arg('--dependency-root', '/Users/jina/project/adlight/web/clipper_web_api');
const output = arg('--output', '/private/tmp/plugin-catalog-sync-proof-evidence');
const require = createRequire(path.join(dependencies, 'package.json'));
const ts = require('typescript');
const { Pool } = require('pg');
const express = require('express');
const pgBin = '/opt/homebrew/opt/postgresql@15/bin';
const sha = (text) => createHash('sha256').update(text).digest('hex');

function parse(text, filename) {
  const file = ts.createSourceFile(filename, text, ts.ScriptTarget.Latest, true);
  assert.equal(file.parseDiagnostics.length, 0, `Invalid TypeScript: ${filename}`);
  return file;
}
function unwrap(node) {
  while (ts.isAsExpression(node) || ts.isSatisfiesExpression(node) || ts.isParenthesizedExpression(node)) node = node.expression;
  return node;
}
const named = (node, name) => ts.isIdentifier(node) && node.text === name;
function stringProperty(object, key, optional = false) {
  const property = object.properties.find((node) => ts.isPropertyAssignment(node) && node.name.getText() === key);
  if (!property && optional) return undefined;
  assert.ok(property && ts.isStringLiteral(property.initializer), `Expected literal metadata: ${key}`);
  return property.initializer.text;
}

export function extract(configText, metadataText, revision) {
  const registrations = [];
  const walkConfig = (node) => {
    if (ts.isCallExpression(node) && named(node.expression, 'providePipelineFeature')) {
      const declaration = node.arguments[0];
      assert.ok(ts.isObjectLiteralExpression(declaration), 'Unsupported feature registration');
      const navigation = declaration.properties.find((property) => ts.isSpreadAssignment(property)
        && ts.isCallExpression(property.expression) && named(property.expression.expression, 'pipelineFeatureNavigation'));
      const key = navigation?.expression.arguments[0];
      assert.ok(key && ts.isStringLiteral(key), 'A feature must declare a stable literal key');
      registrations.push(key.text);
    }
    ts.forEachChild(node, walkConfig);
  };
  walkConfig(parse(configText, 'app.config.ts'));
  assert.ok(registrations.length > 0, 'No registered features found');
  assert.equal(new Set(registrations).size, registrations.length, 'Duplicate registered feature');

  let metadata;
  const walkMetadata = (node) => {
    if (ts.isVariableDeclaration(node) && named(node.name, 'APP_NAVIGATION_METADATA')) metadata = unwrap(node.initializer);
    ts.forEachChild(node, walkMetadata);
  };
  walkMetadata(parse(metadataText, 'app-navigation-metadata.ts'));
  assert.ok(metadata && ts.isObjectLiteralExpression(metadata), 'Navigation metadata object missing');
  const plugins = registrations.sort().map((pluginKey) => {
    const property = metadata.properties.find((node) => ts.isPropertyAssignment(node) && node.name.getText() === pluginKey);
    assert.ok(property, `Missing metadata for ${pluginKey}`);
    const call = property.initializer;
    assert.ok(ts.isCallExpression(call) && named(call.expression, 'pluginMetadata'), `Not a public plugin: ${pluginKey}`);
    const definition = call.arguments[0];
    assert.ok(ts.isObjectLiteralExpression(definition));
    assert.equal(stringProperty(definition, 'name'), pluginKey);
    return {
      pluginKey,
      defaultName: stringProperty(definition, 'storeDisplayName', true) ?? stringProperty(definition, 'label'),
      route: stringProperty(definition, 'route'),
      icon: stringProperty(definition, 'icon'),
    };
  });
  return seal({ schemaVersion: 1, source: { revision, configSha256: sha(configText), metadataSha256: sha(metadataText) }, plugins });
}
function seal(body) { return { ...body, digest: sha(JSON.stringify(body)) }; }
function validate(artifact) {
  const { digest, ...body } = artifact;
  assert.equal(digest, sha(JSON.stringify(body)), 'Artifact digest mismatch');
  assert.equal(body.schemaVersion, 1);
  assert.ok(Array.isArray(body.plugins) && body.plugins.length > 0 && body.plugins.length <= 100);
  const keys = new Set();
  for (const plugin of body.plugins) {
    assert.deepEqual(Object.keys(plugin).sort(), ['defaultName', 'icon', 'pluginKey', 'route']);
    assert.match(plugin.pluginKey, /^[a-z][a-z0-9_]{0,99}$/);
    assert.ok(!keys.has(plugin.pluginKey), 'Duplicate plugin key');
    keys.add(plugin.pluginKey);
    for (const field of ['defaultName', 'icon', 'route']) assert.ok(typeof plugin[field] === 'string' && plugin[field].length > 0);
  }
}

await mkdir(output, { recursive: true });
const angular = path.join(sourceRoot, 'desktop/clipper_angular');
const configPath = path.join(angular, 'src/app/app.config.ts');
const metadataPath = path.join(angular, 'src/core/navigation/app-navigation-metadata.ts');
const configText = await readFile(configPath, 'utf8');
const metadataText = await readFile(metadataPath, 'utf8');
const revision = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: angular, encoding: 'utf8' }).trim();
const actual = extract(configText, metadataText, revision);
await writeFile(path.join(output, 'actual-app-plugin-catalog.json'), JSON.stringify(actual, null, 2));
if (process.argv.includes('--extract-only')) {
  console.log(JSON.stringify({ extracted: actual.plugins.length, keys: actual.plugins.map((p) => p.pluginKey), revision }));
  process.exit(0);
}

const results = [];
async function check(name, work) {
  await work();
  results.push({ name, passed: true });
  console.log(`PASS ${name}`);
}
const cluster = await mkdtemp('/private/tmp/clipper-plugin-catalog-proof-');
const data = path.join(cluster, 'data');
const socket = path.join(cluster, 'socket');
await mkdir(socket);
let running = false;
let pool;
let server;
const syncToken = randomBytes(32).toString('hex');
const adminToken = randomBytes(32).toString('hex');
const evidence = { kind: 'throwaway-local-proof', revision, extractedCount: actual.plugins.length, results };

function makeApp() {
  const app = express();
  app.use(express.json({ limit: '64kb' }));
  const authorize = (token) => (req, res, next) => req.headers.authorization === `Bearer ${token}` ? next() : res.sendStatus(401);
  app.post('/internal/plugin-catalog/sync', authorize(syncToken), async (req, res) => {
    try { validate(req.body); } catch (error) { return res.status(400).json({ error: error.message }); }
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('SELECT pg_advisory_xact_lock(2026102801)');
      let created = 0;
      for (const plugin of req.body.plugins) {
        const saved = await client.query(`
          INSERT INTO catalog_plugins(plugin_key, discovered_name, source_revision, source_digest)
          VALUES ($1, $2, $3, $4)
          ON CONFLICT(plugin_key) DO UPDATE SET
            discovered_name = EXCLUDED.discovered_name,
            source_revision = EXCLUDED.source_revision,
            source_digest = EXCLUDED.source_digest
          RETURNING (xmax = 0) AS inserted`,
          [plugin.pluginKey, plugin.defaultName, req.body.source.revision, req.body.digest]);
        if (saved.rows[0].inserted) created++;
      }
      await client.query('COMMIT');
      res.json({ created, total: Number((await pool.query('SELECT count(*) AS total FROM catalog_plugins')).rows[0].total) });
    } catch (error) {
      await client.query('ROLLBACK');
      res.status(500).json({ error: error.message });
    } finally { client.release(); }
  });
  app.get('/admin/plugins', authorize(adminToken), async (_req, res) => {
    res.json((await pool.query('SELECT * FROM catalog_plugins ORDER BY plugin_key')).rows);
  });
  app.post('/admin/plugins/:key/configure', authorize(adminToken), async (req, res) => {
    const { categoryId, displayName, allowedTargets } = req.body;
    if (!categoryId || !displayName || !Array.isArray(allowedTargets) || allowedTargets.length === 0) return res.sendStatus(400);
    const saved = await pool.query(`UPDATE catalog_plugins SET category_id=$2, display_name=$3, allowed_targets=$4
      WHERE plugin_key=$1 RETURNING plugin_key`, [req.params.key, categoryId, displayName, allowedTargets]);
    res.sendStatus(saved.rowCount === 1 ? 200 : 404);
  });
  app.post('/admin/plugins/:key/publish', authorize(adminToken), async (req, res) => {
    const saved = await pool.query(`UPDATE catalog_plugins SET status='published'
      WHERE plugin_key=$1 AND category_id IS NOT NULL AND display_name IS NOT NULL
      AND cardinality(allowed_targets)>0 RETURNING plugin_key`, [req.params.key]);
    res.sendStatus(saved.rowCount === 1 ? 200 : 409);
  });
  app.get('/store/plugins', async (_req, res) => {
    res.json((await pool.query("SELECT plugin_key, display_name, category_id FROM catalog_plugins WHERE status='published' ORDER BY plugin_key")).rows);
  });
  return app;
}
async function listen() {
  const app = makeApp();
  server = await new Promise((resolve, reject) => {
    const listener = app.listen(0, '127.0.0.1', () => resolve(listener));
    listener.on('error', reject);
  });
  return `http://127.0.0.1:${server.address().port}`;
}
async function closeServer() { if (server) await new Promise((resolve, reject) => server.close((e) => e ? reject(e) : resolve())); server = undefined; }
let base;
async function request(url, body, token) {
  const response = await fetch(base + url, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { ...(body === undefined ? {} : { 'content-type': 'application/json' }), ...(token ? { authorization: `Bearer ${token}` } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const text = await response.text();
  return { status: response.status, body: text.startsWith('{') || text.startsWith('[') ? JSON.parse(text) : text };
}

try {
  execFileSync(path.join(pgBin, 'initdb'), ['-D', data, '-U', 'catalog_proof', '--auth=trust', '--no-locale', '--encoding=UTF8'], { stdio: 'ignore' });
  execFileSync(path.join(pgBin, 'pg_ctl'), ['-D', data, '-l', path.join(cluster, 'postgres.log'), '-o', `-c listen_addresses='' -c unix_socket_directories=${socket} -p 55494`, '-w', 'start'], { stdio: 'ignore' });
  running = true;
  pool = new Pool({ host: socket, port: 55494, user: 'catalog_proof', database: 'postgres', password: () => '', ssl: false });
  await pool.query(`CREATE TABLE catalog_plugins (
    plugin_key text PRIMARY KEY, discovered_name text NOT NULL,
    source_revision text NOT NULL, source_digest text NOT NULL,
    status text NOT NULL DEFAULT 'settings_pending' CHECK(status IN ('settings_pending', 'published')),
    category_id text, display_name text, allowed_targets text[] NOT NULL DEFAULT '{}',
    CHECK(status <> 'published' OR (category_id IS NOT NULL AND display_name IS NOT NULL AND cardinality(allowed_targets)>0))
  )`);
  base = await listen();
  await check('actual app source exports 14 public plugin registrations', async () => {
    assert.equal(actual.plugins.length, 14);
    assert.ok(actual.plugins.some((p) => p.pluginKey === 'person_highlight'));
    assert.ok(!actual.plugins.some((p) => p.pluginKey === 'tts_supertonic'));
  });
  await check('unauthorized upload is rejected without inserting rows', async () => {
    assert.equal((await request('/internal/plugin-catalog/sync', actual)).status, 401);
    assert.equal((await pool.query('SELECT count(*) FROM catalog_plugins')).rows[0].count, '0');
  });
  await check('real HTTP upload creates 14 pending rows and zero store entries', async () => {
    assert.deepEqual((await request('/internal/plugin-catalog/sync', actual, syncToken)).body, { created: 14, total: 14 });
    const listed = await request('/admin/plugins', undefined, adminToken);
    assert.equal(listed.body.length, 14);
    assert.ok(listed.body.every((p) => p.status === 'settings_pending' && p.allowed_targets.length === 0));
    assert.deepEqual((await request('/store/plugins')).body, []);
  });
  await check('parallel repeated uploads do not duplicate plugin IDs', async () => {
    const replies = await Promise.all([request('/internal/plugin-catalog/sync', actual, syncToken), request('/internal/plugin-catalog/sync', actual, syncToken)]);
    assert.ok(replies.every((reply) => reply.status === 200 && reply.body.created === 0 && reply.body.total === 14));
  });
  await check('invalid digest and duplicate IDs are rejected before DB writes', async () => {
    const tampered = structuredClone(actual); tampered.plugins[0].defaultName = 'tampered';
    assert.equal((await request('/internal/plugin-catalog/sync', tampered, syncToken)).status, 400);
    const { digest, ...body } = actual;
    const duplicate = seal({ ...body, plugins: [...body.plugins, body.plugins[0]] });
    assert.equal((await request('/internal/plugin-catalog/sync', duplicate, syncToken)).status, 400);
    assert.equal((await pool.query('SELECT count(*) FROM catalog_plugins')).rows[0].count, '14');
  });
  await check('sync credentials cannot publish and missing configuration blocks publication', async () => {
    assert.equal((await request('/admin/plugins/person_highlight/publish', {}, syncToken)).status, 401);
    assert.equal((await request('/admin/plugins/person_highlight/publish', {}, adminToken)).status, 409);
  });
  await check('admin configuration and publication expose only the configured plugin', async () => {
    assert.equal((await request('/admin/plugins/person_highlight/configure', { categoryId: 'highlight', displayName: '운영자가 지정한 이름', allowedTargets: ['free_trial', 'basic'] }, adminToken)).status, 200);
    assert.equal((await request('/admin/plugins/person_highlight/publish', {}, adminToken)).status, 200);
    assert.deepEqual((await request('/store/plugins')).body, [{ plugin_key: 'person_highlight', display_name: '운영자가 지정한 이름', category_id: 'highlight' }]);
  });
  await check('resync preserves operator publication, name, category and allowed targets', async () => {
    assert.equal((await request('/internal/plugin-catalog/sync', actual, syncToken)).status, 200);
    const row = (await pool.query("SELECT * FROM catalog_plugins WHERE plugin_key='person_highlight'")).rows[0];
    assert.equal(row.status, 'published'); assert.equal(row.category_id, 'highlight');
    assert.equal(row.display_name, '운영자가 지정한 이름');
    assert.deepEqual(row.allowed_targets, ['free_trial', 'basic']);
  });
  await check('adding a registration in source fixtures discovers exactly one new pending plugin', async () => {
    // Synthetic source registration, reusing an existing component solely to
    // exercise discovery. It is NOT a developed or compiled new product feature.
    const marker = '    provideAppInitializer(() => {';
    assert.ok(configText.includes(marker));
    const fixtureConfig = configText.replace(marker, `    providePipelineFeature({ ...pipelineFeatureNavigation('proof_new_plugin'), loadComponent: () => import('../features/person-highlight/pages/person-setup/person-setup.component').then(m => m.PersonSetupComponent) }),\n${marker}`);
    const fixtureMetadata = metadataText.replace('export const APP_NAVIGATION_METADATA = {', `export const APP_NAVIGATION_METADATA = {\n  proof_new_plugin: pluginMetadata({ name: 'proof_new_plugin', kind: 'plugin', label: '실험용 새 등록', icon: 'science', route: 'proof/new' }),`)
      .replace('export type PluginFeatureName =', "export type PluginFeatureName =\n  | 'proof_new_plugin'");
    await mkdir(path.join(output, 'source-fixtures'), { recursive: true });
    await writeFile(path.join(output, 'source-fixtures/app.config.ts'), fixtureConfig);
    await writeFile(path.join(output, 'source-fixtures/app-navigation-metadata.ts'), fixtureMetadata);
    const next = extract(fixtureConfig, fixtureMetadata, 'synthetic-source-registration-fixture');
    assert.equal(next.plugins.length, 15);
    await writeFile(path.join(output, 'fixture-app-plugin-catalog.json'), JSON.stringify(next, null, 2));
    assert.deepEqual((await request('/internal/plugin-catalog/sync', next, syncToken)).body, { created: 1, total: 15 });
    const added = (await pool.query("SELECT * FROM catalog_plugins WHERE plugin_key='proof_new_plugin'")).rows[0];
    assert.equal(added.status, 'settings_pending'); assert.deepEqual(added.allowed_targets, []);
    assert.equal((await request('/store/plugins')).body.length, 1);
  });
  await check('missing source metadata fails extraction instead of silently exporting an incomplete list', async () => {
    assert.throws(() => extract(configText, metadataText.replace('  person_highlight: pluginMetadata({', '  missing_person_metadata: pluginMetadata({'), revision), /Missing metadata/);
  });
  await check('server and DB client restart retain discovery and operator settings', async () => {
    await closeServer(); await pool.end();
    pool = new Pool({ host: socket, port: 55494, user: 'catalog_proof', database: 'postgres', password: () => '', ssl: false });
    base = await listen();
    assert.equal((await request('/admin/plugins', undefined, adminToken)).body.length, 15);
    assert.equal((await request('/store/plugins')).body.length, 1);
  });
  evidence.databaseRows = (await pool.query('SELECT plugin_key, status, category_id, display_name, allowed_targets FROM catalog_plugins ORDER BY plugin_key')).rows;
  evidence.passed = results.length;
  evidence.scope = 'Actual source extraction + real loopback HTTP + actual PostgreSQL. Temporary server; no product endpoint, operator JWT integration, app packaging or deployment pipeline was implemented.';
} catch (error) {
  evidence.error = error.stack;
  console.error(error);
  process.exitCode = 1;
} finally {
  await closeServer();
  if (pool) await pool.end();
  if (running) execFileSync(path.join(pgBin, 'pg_ctl'), ['-D', data, '-m', 'fast', '-w', 'stop'], { stdio: 'ignore' });
  evidence.temporaryPostgresStopped = running;
  evidence.productSourcesUnchanged = (await readFile(configPath, 'utf8')) === configText && (await readFile(metadataPath, 'utf8')) === metadataText;
  await writeFile(path.join(output, 'result.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ passed: results.length, temporaryPostgresStopped: evidence.temporaryPostgresStopped, productSourcesUnchanged: evidence.productSourcesUnchanged, evidence: path.join(output, 'result.json') }));
}
