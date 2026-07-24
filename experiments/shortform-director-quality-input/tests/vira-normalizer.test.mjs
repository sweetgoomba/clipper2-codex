import assert from 'node:assert/strict';
import {
  copyFile,
  cp,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rename,
  rm,
  writeFile,
} from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { loadCaseBundle, validateCaseBundle } from '../lib/contracts.mjs';
import { normalizeViraExport } from '../lib/vira-normalizer.mjs';
import { normalizeViraExportFile } from '../scripts/normalize-vira-export.mjs';

const sufficientFixture = JSON.parse(await readFile(
  new URL('./fixtures/vira-export-sufficient.json', import.meta.url),
  'utf8',
));
const emptyFixture = JSON.parse(await readFile(
  new URL('./fixtures/vira-export-empty.json', import.meta.url),
  'utf8',
));
const context = {
  materializedAt: '2026-07-24T12:00:00.000Z',
  codeRevision: '2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4',
};
const experimentDirectory = fileURLToPath(new URL('../', import.meta.url));
const caseDirectories = ['beauty-01', 'product-01', 'idol-01', 'expert-01'];
const guardedFileSystem = {
  copyFile,
  mkdir,
  readFile,
  rename,
  rm,
  writeFile,
};

function cloneFixture() {
  return structuredClone(sufficientFixture);
}

function assertFixedValidationError(raw) {
  assert.throws(
    () => normalizeViraExport(raw, context),
    /^Error: Vira export is invalid$/,
  );
}

function assertNoUndefined(value) {
  if (Array.isArray(value)) {
    value.forEach(assertNoUndefined);
    return;
  }
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      assert.notEqual(child, undefined, `${key} must be omitted instead of undefined`);
      assertNoUndefined(child);
    }
  }
}

async function rollbackFixture(t) {
  const temporaryExperiment = await mkdtemp(
    join(experimentDirectory, 'private', '.normalize-rollback-test-'),
  );
  t.after(() => rm(temporaryExperiment, { recursive: true, force: true }));
  await mkdir(join(temporaryExperiment, 'cases'));
  for (const directoryName of caseDirectories) {
    await cp(
      join(experimentDirectory, 'cases', directoryName),
      join(temporaryExperiment, 'cases', directoryName),
      { recursive: true },
    );
  }
  const rawExportPath = join(temporaryExperiment, 'fixture-export.json');
  await writeFile(rawExportPath, JSON.stringify(sufficientFixture));
  const originalBytes = new Map();
  for (const directoryName of caseDirectories) {
    for (const fileName of ['vira-evidence.json', 'manifest.json']) {
      const filePath = join(temporaryExperiment, 'cases', directoryName, fileName);
      originalBytes.set(filePath, await readFile(filePath));
    }
  }
  return { temporaryExperiment, rawExportPath, originalBytes };
}

async function assertRollbackCompleted(fixture) {
  for (const [filePath, originalBytes] of fixture.originalBytes) {
    assert.deepEqual(await readFile(filePath), originalBytes);
  }
  const names = await readdir(fixture.temporaryExperiment, { recursive: true });
  assert.equal(names.some((name) => name.endsWith('.tmp')), false);
  for (const directoryName of caseDirectories) {
    const bundle = await loadCaseBundle(
      join(fixture.temporaryExperiment, 'cases', directoryName),
    );
    validateCaseBundle(bundle, { sealed: true });
  }
}

test('keeps at most three market and two growth records per case', () => {
  const result = normalizeViraExport(sufficientFixture, context);
  const beautyPack = result.get('BEAUTY-01');

  assert.equal(beautyPack.evidence.length, 5);
  assert.deepEqual(
    beautyPack.evidence.map(({ kind }) => kind),
    [
      'market.video-observation',
      'market.video-observation',
      'market.video-observation',
      'market.peer-growth',
      'market.peer-growth',
    ],
  );
  assert.equal(beautyPack.state, 'sufficient');
});

test('does not invent evidence when a topic has no rows', () => {
  const result = normalizeViraExport(emptyFixture, context);

  assert.deepEqual(result.get('EXPERT-01'), {
    schemaVersion: 'quality-input-vira-pack.v1',
    caseId: 'EXPERT-01',
    state: 'insufficient',
    evidence: [],
  });
});

test('never carries comment author or text fields', () => {
  const raw = cloneFixture();
  raw.market[0].author = 'identity-must-be-rejected';
  raw.market[0].commentText = 'body-must-be-rejected';

  assertFixedValidationError(raw);
});

test('maps only audited Vira evidence envelopes and keeps row ids as record references', () => {
  const result = normalizeViraExport(sufficientFixture, context);
  const [marketEvidence] = result.get('BEAUTY-01').evidence;
  const [growthEvidence] = result.get('IDOL-01').evidence;

  assert.equal(marketEvidence.schemaVersion, 'vira-evidence.v1');
  assert.equal(marketEvidence.kind, 'market.video-observation');
  assert.equal(marketEvidence.source.codeRevision, context.codeRevision);
  assert.deepEqual(marketEvidence.source.recordRefs, [
    { kind: 'shorts-video', id: 101 },
  ]);
  assert.equal(marketEvidence.subject.keyword, '젤광');
  assert.equal(marketEvidence.subject.category, '뷰티');
  assert.equal(marketEvidence.rowId, undefined);
  assert.equal(marketEvidence.observation.sampleSize, 3);
  assert.equal(marketEvidence.payload.metrics.engagementRate, 0.1);
  assert.equal(marketEvidence.payload.tags.length, 5);
  assert.deepEqual(marketEvidence.payload.commentSentiment, {
    positive: 7,
    negative: 1,
    neutral: 2,
    classified: 10,
  });

  assert.equal(growthEvidence.kind, 'market.peer-growth');
  assert.equal(growthEvidence.observation.state, 'partial');
  assert.equal(growthEvidence.observation.sampleSize, 30);
  assert.equal(growthEvidence.payload.percentile, 92);

  const serialized = JSON.stringify(result);
  assert.doesNotMatch(serialized, /analysis\.video-8d|legacy/);
});

test('assigns partial state to non-empty case data below both sufficiency thresholds', () => {
  const result = normalizeViraExport(sufficientFixture, context);

  assert.equal(result.get('PRODUCT-01').state, 'partial');
  assert.equal(result.get('PRODUCT-01').evidence[0].observation.state, 'partial');
  assert.equal(result.get('IDOL-01').state, 'partial');
  assert.equal(result.get('EXPERT-01').state, 'insufficient');
});

test('rejects malformed top-level Vira export shapes before counting rows', () => {
  assertFixedValidationError(null);
  assertFixedValidationError([]);
  assertFixedValidationError({ market: [] });
  assertFixedValidationError({ market: [], growth: [], unexpected: [] });
});

test('rejects missing row identity and duplicate identity within a case and kind', () => {
  const missingRowId = cloneFixture();
  delete missingRowId.market[0].rowId;
  assertFixedValidationError(missingRowId);

  const missingVideoId = cloneFixture();
  delete missingVideoId.growth[0].platformVideoId;
  assertFixedValidationError(missingVideoId);

  const duplicateRowId = cloneFixture();
  duplicateRowId.market[1].rowId = duplicateRowId.market[0].rowId;
  assertFixedValidationError(duplicateRowId);

  const duplicateVideoId = cloneFixture();
  duplicateVideoId.growth[1].platformVideoId = duplicateVideoId.growth[0].platformVideoId;
  assertFixedValidationError(duplicateVideoId);
});

test('rejects non-finite or negative counts and invalid dates ranges and booleans', () => {
  const invalidRows = [
    (raw) => { delete raw.market[0].views; },
    (raw) => { raw.market[0].views = Number.POSITIVE_INFINITY; },
    (raw) => { raw.market[0].likes = -1; },
    (raw) => { raw.market[0].classified = -1; },
    (raw) => { raw.market[0].snapshotDate = '2026-02-30'; },
    (raw) => { raw.growth[0].snapshotFrom = 'invalid-date'; },
    (raw) => { raw.growth[0].snapshotFrom = '2026-07-25'; },
    (raw) => { raw.growth[0].percentile = 101; },
    (raw) => { raw.growth[0].peerSampleSize = -1; },
    (raw) => { raw.growth[0].isRising = 'true'; },
  ];

  for (const mutate of invalidRows) {
    const raw = cloneFixture();
    mutate(raw);
    assertFixedValidationError(raw);
  }
});

test('omits optional nullable market fields instead of storing undefined', () => {
  const raw = {
    market: [{
      caseId: 'EXPERT-01',
      rowId: 901,
      platformVideoId: 'expert-video-nullable',
      title: null,
      channel: null,
      keyword: null,
      category: null,
      tags: [],
      snapshotDate: null,
      views: 0,
      viewsSource: 'discovery',
      likes: null,
      comments: null,
      positive: 0,
      negative: 0,
      neutral: 0,
      classified: 0
    }],
    growth: [],
  };

  const [evidence] = normalizeViraExport(raw, context).get('EXPERT-01').evidence;
  assertNoUndefined(evidence);
  assert.equal(Object.hasOwn(evidence.subject, 'keyword'), false);
  assert.equal(Object.hasOwn(evidence.subject, 'category'), false);
  assert.equal(Object.hasOwn(evidence.observation, 'window'), false);
  assert.equal(Object.hasOwn(evidence.payload.metrics, 'likes'), false);
  assert.equal(Object.hasOwn(evidence.payload.metrics, 'comments'), false);
});

test('accepts a null market view count and omits views from metrics', () => {
  const raw = {
    market: [{
      caseId: 'EXPERT-01',
      rowId: 902,
      platformVideoId: 'expert-video-without-views',
      title: '조회수 없는 발견 행',
      channel: 'Fixture Channel',
      keyword: '채권',
      category: '금융',
      tags: [],
      snapshotDate: null,
      views: null,
      viewsSource: 'discovery',
      likes: null,
      comments: null,
      positive: 0,
      negative: 0,
      neutral: 0,
      classified: 0
    }],
    growth: [],
  };

  const pack = normalizeViraExport(raw, context).get('EXPERT-01');
  assert.equal(pack.state, 'partial');
  assert.equal(pack.evidence.length, 1);
  assert.equal(Object.hasOwn(pack.evidence[0].payload.metrics, 'views'), false);
  assert.equal(
    Object.hasOwn(pack.evidence[0].payload.metrics, 'engagementRate'),
    false,
  );
  assertNoUndefined(pack.evidence[0]);
});

test('restores all four case pairs after the second Vira write fails', async (t) => {
  const fixture = await rollbackFixture(t);
  const failedPath = join(
    fixture.temporaryExperiment,
    'cases',
    'product-01',
    'vira-evidence.json',
  );
  let injected = false;

  await assert.rejects(
    normalizeViraExportFile(fixture.rawExportPath, {
      experimentDirectory: fixture.temporaryExperiment,
      materializedAt: context.materializedAt,
      fileSystem: {
        ...guardedFileSystem,
        rename: async (fromPath, toPath) => {
          if (!injected && toPath === failedPath) {
            injected = true;
            throw new Error('injected second Vira write failure');
          }
          await rename(fromPath, toPath);
        },
      },
    }),
    /injected second Vira write failure/,
  );
  await assertRollbackCompleted(fixture);
});

test('restores all four case pairs after an intermediate seal fails', async (t) => {
  const fixture = await rollbackFixture(t);
  const failedPath = join(
    fixture.temporaryExperiment,
    'cases',
    'product-01',
    'manifest.json',
  );
  let injected = false;

  await assert.rejects(
    normalizeViraExportFile(fixture.rawExportPath, {
      experimentDirectory: fixture.temporaryExperiment,
      materializedAt: context.materializedAt,
      fileSystem: {
        ...guardedFileSystem,
        rename: async (fromPath, toPath) => {
          if (!injected && toPath === failedPath) {
            injected = true;
            throw new Error('injected intermediate seal failure');
          }
          await rename(fromPath, toPath);
        },
      },
    }),
    /injected intermediate seal failure/,
  );
  await assertRollbackCompleted(fixture);
});

test('reports the cause and rollback errors when atomic restoration is incomplete', async (t) => {
  const fixture = await rollbackFixture(t);
  const writeFailurePath = join(
    fixture.temporaryExperiment,
    'cases',
    'product-01',
    'vira-evidence.json',
  );
  const rollbackFailurePath = join(
    fixture.temporaryExperiment,
    'cases',
    'beauty-01',
    'vira-evidence.json',
  );
  let writeFailed = false;
  let rollbackFailed = false;
  let failure;

  try {
    await normalizeViraExportFile(fixture.rawExportPath, {
      experimentDirectory: fixture.temporaryExperiment,
      materializedAt: context.materializedAt,
      fileSystem: {
        ...guardedFileSystem,
        rename: async (fromPath, toPath) => {
          if (!writeFailed && toPath === writeFailurePath) {
            writeFailed = true;
            throw new Error('injected write cause');
          }
          if (writeFailed && !rollbackFailed && toPath === rollbackFailurePath) {
            rollbackFailed = true;
            throw new Error('injected rollback failure');
          }
          await rename(fromPath, toPath);
        },
      },
    });
  } catch (error) {
    failure = error;
  }

  assert.equal(failure instanceof AggregateError, true);
  assert.deepEqual(
    failure.errors.map(({ message }) => message),
    ['injected write cause', 'injected rollback failure'],
  );
  const names = await readdir(fixture.temporaryExperiment, { recursive: true });
  assert.equal(names.some((name) => name.endsWith('.tmp')), false);
});

test('cleans an owned normalization temp when exclusive write creates then throws', async (t) => {
  const fixture = await rollbackFixture(t);
  let injected = false;

  await assert.rejects(
    normalizeViraExportFile(fixture.rawExportPath, {
      experimentDirectory: fixture.temporaryExperiment,
      materializedAt: context.materializedAt,
      fileSystem: {
        ...guardedFileSystem,
        writeFile: async (filePath, ...args) => {
          await writeFile(filePath, ...args);
          if (!injected && filePath.includes('.vira-evidence.json.')) {
            injected = true;
            throw new Error('injected normalization post-create failure');
          }
        },
      },
    }),
    /injected normalization post-create failure/,
  );
  await assertRollbackCompleted(fixture);
});
