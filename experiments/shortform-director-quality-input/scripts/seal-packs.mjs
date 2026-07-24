import { randomUUID } from 'node:crypto';
import { readFile, rename, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { sha256Json } from '../lib/canonical-json.mjs';
import {
  DIGESTED_CASE_FILES,
  loadCaseBundle,
  validateCaseBundle,
} from '../lib/contracts.mjs';

const experimentDirectory = fileURLToPath(new URL('../', import.meta.url));
const defaultCaseDirectories = [
  'beauty-01',
  'product-01',
  'idol-01',
  'expert-01',
].map((directoryName) => join(experimentDirectory, 'cases', directoryName));

const bundleKeyByFileName = {
  'profile.json': 'profile',
  'episodes.json': 'episodes',
  'source-cards.json': 'sources',
  'audience-cards.json': 'audience',
  'reference-cards.json': 'references',
  'vira-evidence.json': 'vira',
  'feedback-cards.json': 'feedback',
};
const defaultFileSystem = {
  readFile,
  writeFile,
  rename,
  rm,
};

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

function serializedJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function atomicWriteBytes(filePath, bytes, fileSystem) {
  const temporaryPath = join(
    dirname(filePath),
    `.${basename(filePath)}.${process.pid}.${randomUUID()}.tmp`,
  );
  try {
    await fileSystem.writeFile(temporaryPath, bytes, {
      flag: 'wx',
    });
    await fileSystem.rename(temporaryPath, filePath);
  } finally {
    await fileSystem.rm(temporaryPath, { force: true });
  }
}

export async function sealCaseDirectory(
  caseDirectory,
  {
    fileSystem = defaultFileSystem,
    validateBundle = validateCaseBundle,
  } = {},
) {
  const bundle = await loadCaseBundle(caseDirectory);
  validateBundle(bundle, { sealed: false });

  bundle.sources.cards = bundle.sources.cards.map((card) => ({
    ...card,
    contentDigest: sha256Json(contentDigestInput(card)),
  }));

  bundle.manifest = {
    ...bundle.manifest,
    state: 'sealed',
    fileDigests: Object.fromEntries(
      DIGESTED_CASE_FILES.map((fileName) => [
        fileName,
        sha256Json(bundle[bundleKeyByFileName[fileName]]),
      ]),
    ),
  };
  validateBundle(bundle, { sealed: true });

  const sourceCardsPath = join(caseDirectory, 'source-cards.json');
  const manifestPath = join(caseDirectory, 'manifest.json');
  const [originalSourceBytes, originalManifestBytes] = await Promise.all([
    fileSystem.readFile(sourceCardsPath),
    fileSystem.readFile(manifestPath),
  ]);
  let sourceCommitted = false;
  let manifestCommitted = false;

  try {
    await atomicWriteBytes(sourceCardsPath, serializedJson(bundle.sources), fileSystem);
    sourceCommitted = true;
    await atomicWriteBytes(manifestPath, serializedJson(bundle.manifest), fileSystem);
    manifestCommitted = true;

    const persistedBundle = await loadCaseBundle(caseDirectory);
    validateBundle(persistedBundle, { sealed: true });
    return persistedBundle;
  } catch (error) {
    const rollbackErrors = [];
    if (manifestCommitted) {
      try {
        await atomicWriteBytes(manifestPath, originalManifestBytes, fileSystem);
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError);
      }
    }
    if (sourceCommitted) {
      try {
        await atomicWriteBytes(sourceCardsPath, originalSourceBytes, fileSystem);
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError);
      }
    }

    if (rollbackErrors.length > 0) {
      throw new AggregateError(
        [error, ...rollbackErrors],
        'case sealing failed and rollback was incomplete',
      );
    }
    throw error;
  }
}

async function main() {
  const caseDirectories = process.argv.slice(2);
  const targets = caseDirectories.length > 0 ? caseDirectories : defaultCaseDirectories;
  for (const caseDirectory of targets) {
    const bundle = await sealCaseDirectory(caseDirectory);
    process.stdout.write(`${bundle.manifest.caseId} sealed\n`);
  }
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  await main();
}
