import { randomUUID } from 'node:crypto';
import {
  constants,
  copyFile,
  mkdir,
  readFile,
  rename,
  rm,
  writeFile,
} from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { loadCaseBundle, validateCaseBundle } from '../lib/contracts.mjs';
import { normalizeViraExport } from '../lib/vira-normalizer.mjs';
import { sealCaseDirectory } from './seal-packs.mjs';

const CODE_REVISION = '2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4';
const EXPERIMENT_DIRECTORY = fileURLToPath(new URL('../', import.meta.url));
const CASES = [
  ['BEAUTY-01', 'beauty-01'],
  ['PRODUCT-01', 'product-01'],
  ['IDOL-01', 'idol-01'],
  ['EXPERT-01', 'expert-01'],
];
const defaultFileSystem = {
  copyFile,
  mkdir,
  readFile,
  rename,
  rm,
  writeFile,
};

async function atomicWriteBytes(filePath, bytes, fileSystem) {
  const temporaryPath = join(
    dirname(filePath),
    `.${basename(filePath)}.${process.pid}.${randomUUID()}.tmp`,
  );
  let ownsTemporary = true;
  try {
    try {
      await fileSystem.writeFile(temporaryPath, bytes, {
        flag: 'wx',
      });
    } catch (error) {
      if (error?.code === 'EEXIST') ownsTemporary = false;
      throw error;
    }
    await fileSystem.rename(temporaryPath, filePath);
  } finally {
    if (ownsTemporary) await fileSystem.rm(temporaryPath, { force: true });
  }
}

async function backUpPreviousFiles(caseDirectory, backupCaseDirectory, fileSystem) {
  await fileSystem.mkdir(backupCaseDirectory, { recursive: true });
  await Promise.all(
    ['vira-evidence.json', 'manifest.json'].map((fileName) => fileSystem.copyFile(
      join(caseDirectory, fileName),
      join(backupCaseDirectory, fileName),
      constants.COPYFILE_EXCL,
    )),
  );
}

export async function normalizeViraExportFile(
  rawExportPath,
  {
    materializedAt = new Date().toISOString(),
    codeRevision = CODE_REVISION,
    experimentDirectory = EXPERIMENT_DIRECTORY,
    fileSystem = defaultFileSystem,
  } = {},
) {
  const raw = JSON.parse(await fileSystem.readFile(rawExportPath, 'utf8'));
  const normalized = normalizeViraExport(raw, { materializedAt, codeRevision });
  const backupDirectory = join(
    experimentDirectory,
    'private',
    'pre-vira-normalization',
  );
  const originalBytes = new Map();

  for (const [, directoryName] of CASES) {
    const caseDirectory = join(experimentDirectory, 'cases', directoryName);
    for (const fileName of ['vira-evidence.json', 'manifest.json']) {
      const filePath = join(caseDirectory, fileName);
      originalBytes.set(filePath, await fileSystem.readFile(filePath));
    }
  }

  for (const [, directoryName] of CASES) {
    const caseDirectory = join(experimentDirectory, 'cases', directoryName);
    await backUpPreviousFiles(
      caseDirectory,
      join(backupDirectory, directoryName),
      fileSystem,
    );
  }

  try {
    for (const [caseId, directoryName] of CASES) {
      const caseDirectory = join(experimentDirectory, 'cases', directoryName);
      await atomicWriteBytes(
        join(caseDirectory, 'vira-evidence.json'),
        `${JSON.stringify(normalized.get(caseId), null, 2)}\n`,
        fileSystem,
      );
    }

    for (const [, directoryName] of CASES) {
      await sealCaseDirectory(
        join(experimentDirectory, 'cases', directoryName),
        { fileSystem },
      );
    }
  } catch (error) {
    const rollbackErrors = [];
    for (const [filePath, bytes] of originalBytes) {
      try {
        await atomicWriteBytes(filePath, bytes, fileSystem);
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError);
      }
    }
    if (rollbackErrors.length === 0) {
      for (const [, directoryName] of CASES) {
        try {
          const bundle = await loadCaseBundle(
            join(experimentDirectory, 'cases', directoryName),
          );
          validateCaseBundle(bundle, { sealed: true });
        } catch (rollbackError) {
          rollbackErrors.push(rollbackError);
        }
      }
    }
    if (rollbackErrors.length > 0) {
      throw new AggregateError(
        [error, ...rollbackErrors],
        'Vira normalization failed and rollback was incomplete',
      );
    }
    throw error;
  }

  return normalized;
}

async function main() {
  if (process.argv.length !== 3) {
    throw new Error('usage: normalize-vira-export.mjs <raw-export.json>');
  }
  await normalizeViraExportFile(resolve(process.argv[2]));
}

if (process.argv[1]
  && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await main();
}
