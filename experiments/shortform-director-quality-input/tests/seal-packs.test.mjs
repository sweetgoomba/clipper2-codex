import assert from 'node:assert/strict';
import {
  cp,
  mkdtemp,
  readFile,
  readdir,
  rename,
  rm,
  writeFile,
} from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import {
  DIGESTED_CASE_FILES,
  loadCaseBundle,
  validateCaseBundle,
} from '../lib/contracts.mjs';
import { sha256Json } from '../lib/canonical-json.mjs';

const experimentDirectory = fileURLToPath(new URL('../', import.meta.url));
const cases = [
  {
    caseId: 'BEAUTY-01',
    directoryName: 'beauty-01',
    sourceIds: ['B-S01', 'B-S02', 'B-S03'],
    referenceIds: ['B-R01', 'B-R02'],
  },
  {
    caseId: 'PRODUCT-01',
    directoryName: 'product-01',
    sourceIds: ['P-S01', 'P-S02', 'P-S03', 'P-S04', 'P-S05'],
    referenceIds: ['P-R01'],
  },
  {
    caseId: 'IDOL-01',
    directoryName: 'idol-01',
    sourceIds: ['I-S01', 'I-S02', 'I-S03', 'I-E01'],
    referenceIds: ['I-R01'],
  },
  {
    caseId: 'EXPERT-01',
    directoryName: 'expert-01',
    sourceIds: ['E-S01', 'E-S02', 'E-S03'],
    referenceIds: ['E-R01'],
  },
];

function caseDirectory(directoryName) {
  return join(experimentDirectory, 'cases', directoryName);
}

function contentDigestInput(card) {
  return {
    id: card.id,
    title: card.title,
    publisher: card.publisher,
    originalUrl: card.originalUrl,
    publishedAt: card.publishedAt,
    retrievedAt: card.retrievedAt,
    claims: card.claims,
    rightsNote: card.rightsNote,
  };
}

async function unsealedCaseCopy(t) {
  const sourceDirectory = caseDirectory('beauty-01');
  const temporaryDirectory = await mkdtemp(join(experimentDirectory, 'cases', '.seal-test-'));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  await cp(sourceDirectory, temporaryDirectory, { recursive: true });

  const sourceCardsPath = join(temporaryDirectory, 'source-cards.json');
  const sourceCards = JSON.parse(await readFile(sourceCardsPath, 'utf8'));
  sourceCards.cards[0].contentDigest = null;
  await writeFile(sourceCardsPath, `${JSON.stringify(sourceCards, null, 2)}\n`);

  const manifestPath = join(temporaryDirectory, 'manifest.json');
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  manifest.state = 'materializing';
  manifest.fileDigests = Object.fromEntries(DIGESTED_CASE_FILES.map((fileName) => [fileName, null]));
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

  return {
    temporaryDirectory,
    sourceCardsPath,
    manifestPath,
    originalSourceBytes: await readFile(sourceCardsPath),
    originalManifestBytes: await readFile(manifestPath),
  };
}

async function assertOriginalPairAndNoTemps(fixture) {
  assert.deepEqual(await readFile(fixture.sourceCardsPath), fixture.originalSourceBytes);
  assert.deepEqual(await readFile(fixture.manifestPath), fixture.originalManifestBytes);
  const siblingNames = await readdir(fixture.temporaryDirectory);
  assert.equal(siblingNames.some((name) => name.endsWith('.tmp')), false);
}

test('four sealed case packs preserve fixed identities and exact inventories', async () => {
  for (const expected of cases) {
    const bundle = await loadCaseBundle(caseDirectory(expected.directoryName));
    validateCaseBundle(bundle, { sealed: true });

    assert.equal(bundle.manifest.caseId, expected.caseId);
    assert.equal(bundle.profile.caseId, expected.caseId);
    assert.equal(bundle.episodes.caseId, expected.caseId);
    assert.equal(bundle.episodes.episodeA.id, `${expected.caseId}-A`);
    assert.equal(bundle.episodes.episodeB.id, `${expected.caseId}-B`);
    assert.deepEqual(bundle.sources.cards.map(({ id }) => id), expected.sourceIds);
    assert.equal(bundle.audience.questions.length, 10);
    assert.deepEqual(bundle.references.cards.map(({ id }) => id), expected.referenceIds);
    assert.equal(bundle.vira.state, 'provider_not_called');
    assert.deepEqual(bundle.vira.evidence, []);
    assert.equal(bundle.feedback.state, 'not_collected');
    assert.deepEqual(bundle.feedback.cards, []);

    for (const card of bundle.sources.cards) {
      assert.equal(card.contentDigest, sha256Json(contentDigestInput(card)));
    }
    for (const fileName of DIGESTED_CASE_FILES) {
      const bundleKey = {
        'profile.json': 'profile',
        'episodes.json': 'episodes',
        'source-cards.json': 'sources',
        'audience-cards.json': 'audience',
        'reference-cards.json': 'references',
        'vira-evidence.json': 'vira',
        'feedback-cards.json': 'feedback',
      }[fileName];
      assert.equal(bundle.manifest.fileDigests[fileName], sha256Json(bundle[bundleKey]));
    }
  }
});

test('E-S01-C01 preserves the audited primary-source locator', async () => {
  const bundle = await loadCaseBundle(caseDirectory('expert-01'));
  const source = bundle.sources.cards.find(({ id }) => id === 'E-S01');
  const claim = source.claims.find(({ id }) => id === 'E-S01-C01');

  assert.equal(
    claim.evidenceLocator,
    "자막 ‘채권수익률 산출’ p.10 및 ‘채권수익률 결정요인 및 채권투자 리스크’ p.11",
  );
});

test('sealer repairs digests atomically and leaves no temporary sibling', async (t) => {
  const fixture = await unsealedCaseCopy(t);

  const { sealCaseDirectory } = await import('../scripts/seal-packs.mjs');
  const sealedBundle = await sealCaseDirectory(fixture.temporaryDirectory);
  validateCaseBundle(sealedBundle, { sealed: true });

  const siblingNames = await readdir(dirname(fixture.manifestPath));
  assert.equal(siblingNames.some((name) => name.endsWith('.tmp')), false);
});

test('manifest commit failure rolls back source and manifest bytes without temp siblings', async (t) => {
  const fixture = await unsealedCaseCopy(t);
  const { sealCaseDirectory } = await import('../scripts/seal-packs.mjs');
  let manifestCommitFailed = false;

  await assert.rejects(
    sealCaseDirectory(fixture.temporaryDirectory, {
      fileSystem: {
        readFile,
        writeFile,
        rename: async (fromPath, toPath) => {
          if (!manifestCommitFailed && toPath === fixture.manifestPath) {
            manifestCommitFailed = true;
            throw new Error('injected manifest commit failure');
          }
          await rename(fromPath, toPath);
        },
        rm,
      },
    }),
    /injected manifest commit failure/,
  );
  await assertOriginalPairAndNoTemps(fixture);
});

test('persisted sealed validation failure rolls back both files without temp siblings', async (t) => {
  const fixture = await unsealedCaseCopy(t);
  const { sealCaseDirectory } = await import('../scripts/seal-packs.mjs');
  let sealedValidations = 0;

  await assert.rejects(
    sealCaseDirectory(fixture.temporaryDirectory, {
      validateBundle: (bundle, options) => {
        const result = validateCaseBundle(bundle, options);
        if (options.sealed && ++sealedValidations === 2) {
          throw new Error('injected persisted sealed validation failure');
        }
        return result;
      },
    }),
    /injected persisted sealed validation failure/,
  );
  await assertOriginalPairAndNoTemps(fixture);
});

test('rollback failure reports both commit and rollback errors', async (t) => {
  const fixture = await unsealedCaseCopy(t);
  const { sealCaseDirectory } = await import('../scripts/seal-packs.mjs');
  let manifestCommitFailed = false;
  let sourceRenames = 0;
  let failure;

  try {
    await sealCaseDirectory(fixture.temporaryDirectory, {
      fileSystem: {
        readFile,
        writeFile,
        rename: async (fromPath, toPath) => {
          if (toPath === fixture.sourceCardsPath && ++sourceRenames === 2) {
            throw new Error('injected source rollback failure');
          }
          if (!manifestCommitFailed && toPath === fixture.manifestPath) {
            manifestCommitFailed = true;
            throw new Error('injected manifest commit failure');
          }
          await rename(fromPath, toPath);
        },
        rm,
      },
    });
  } catch (error) {
    failure = error;
  }

  assert.equal(failure instanceof AggregateError, true);
  assert.deepEqual(
    failure.errors.map(({ message }) => message),
    ['injected manifest commit failure', 'injected source rollback failure'],
  );
  const siblingNames = await readdir(fixture.temporaryDirectory);
  assert.equal(siblingNames.some((name) => name.endsWith('.tmp')), false);
});
