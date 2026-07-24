import assert from 'node:assert/strict';
import { execFile as execFileCallback } from 'node:child_process';
import { mkdtemp, readFile, rm, symlink } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import test from 'node:test';
import { loadCaseBundle, validateCaseBundle } from '../lib/contracts.mjs';
import { canonicalJson, sha256Json } from '../lib/canonical-json.mjs';

const fixtureUrl = new URL('./fixtures/minimal-case-bundle.json', import.meta.url);
const loadableCaseDirectory = fileURLToPath(new URL('./fixtures/loadable-case/', import.meta.url));
const maliciousCaseDirectory = fileURLToPath(new URL('./fixtures/malicious-label-case/', import.meta.url));
const validatePacksUrl = new URL('../scripts/validate-packs.mjs', import.meta.url);
const execFile = promisify(execFileCallback);
const fileNames = {
  'manifest.json': 'manifest',
  'profile.json': 'profile',
  'episodes.json': 'episodes',
  'source-cards.json': 'sources',
  'audience-cards.json': 'audience',
  'reference-cards.json': 'references',
  'vira-evidence.json': 'vira',
  'feedback-cards.json': 'feedback',
};

async function fixtureBundle() {
  return JSON.parse(await readFile(fixtureUrl, 'utf8'));
}

test('validates the fixed case bundle shape', async () => {
  const bundle = await fixtureBundle();
  assert.equal(validateCaseBundle(bundle, { sealed: false }).manifest.caseId, 'BEAUTY-01');
});

test('rejects an audience set that is not exactly ten questions', async () => {
  const bundle = await fixtureBundle();
  bundle.audience.questions.pop();
  assert.throws(
    () => validateCaseBundle(bundle, { sealed: false }),
    /audience\.questions must contain exactly 10 items/,
  );
});

test('rejects a sealed source without content digest or locator', async () => {
  const bundle = await fixtureBundle();
  bundle.manifest.state = 'sealed';
  bundle.sources.cards[0].contentDigest = null;
  assert.throws(
    () => validateCaseBundle(bundle, { sealed: true }),
    /sealed source card requires contentDigest and located claims/,
  );
});

test('canonical JSON hashes object keys deterministically', () => {
  assert.equal(canonicalJson({ b: [2, { z: 1, a: 0 }], a: true }), '{"a":true,"b":[2,{"a":0,"z":1}]}');
  assert.equal(sha256Json({ a: 1, b: 2 }), sha256Json({ b: 2, a: 1 }));
});

test('loads exactly the fixed case files from an experiment-local directory', async () => {
  const bundle = await loadCaseBundle(loadableCaseDirectory);
  assert.deepEqual(Object.keys(bundle).sort(), Object.values(fileNames).sort());
  assert.equal(bundle.manifest.caseId, 'BEAUTY-01');
});

test('rejects a directory outside the experiment workspace', async (t) => {
  const outsideDirectory = await mkdtemp('/private/tmp/quality-input-outside-');
  t.after(() => rm(outsideDirectory, { recursive: true, force: true }));
  await assert.rejects(loadCaseBundle(outsideDirectory), /inside the experiment workspace/);
});

test('rejects an outside workspace symlink before loading its target', async (t) => {
  const outsideDirectory = await mkdtemp('/private/tmp/quality-input-outside-');
  const symlinkPath = join(outsideDirectory, 'case-link');
  t.after(() => rm(outsideDirectory, { recursive: true, force: true }));
  await symlink(loadableCaseDirectory, symlinkPath);
  await assert.rejects(loadCaseBundle(symlinkPath), /must not be a symbolic link/);
});

test('prints the fixed validator usage without loading packs', async () => {
  const { stdout, stderr } = await execFile(process.execPath, [validatePacksUrl.pathname, '--help']);
  assert.equal(stderr, '');
  assert.equal(
    stdout,
    'usage: validate-packs.mjs [--sealed] cases/beauty-01 cases/product-01 cases/idol-01 cases/expert-01\n',
  );
});

test('replaces malicious manifest labels with safe placeholders on validation failure', async () => {
  let failure;
  try {
    await execFile(process.execPath, [
      validatePacksUrl.pathname,
      maliciousCaseDirectory,
      maliciousCaseDirectory,
      maliciousCaseDirectory,
      maliciousCaseDirectory,
    ]);
  } catch (error) {
    failure = error;
  }
  assert.equal(failure?.code, 1);
  assert.equal(failure?.stdout, 'unknown unknown fail\n'.repeat(4));
  assert.doesNotMatch(failure.stdout, /INJECTED|BEAUTY-01/);
});
