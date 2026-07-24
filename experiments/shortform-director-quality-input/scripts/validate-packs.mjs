import { CASE_IDS, loadCaseBundle, validateCaseBundle } from '../lib/contracts.mjs';

const usage = 'usage: validate-packs.mjs [--sealed] cases/beauty-01 cases/product-01 cases/idol-01 cases/expert-01\n';

function printUsage() {
  process.stdout.write(usage);
}

const DISPLAY_STATES = new Set(['draft', 'sealed']);

function displayCaseId(value) {
  return CASE_IDS.includes(value) ? value : 'unknown';
}

function displayState(value) {
  return DISPLAY_STATES.has(value) ? value : 'unknown';
}

async function validateDirectory(caseDirectory, sealed) {
  let bundle;
  try {
    bundle = await loadCaseBundle(caseDirectory);
    validateCaseBundle(bundle, { sealed });
    process.stdout.write(`${displayCaseId(bundle.manifest?.caseId)} ${displayState(bundle.manifest?.state)} pass\n`);
    return true;
  } catch {
    process.stdout.write(`${displayCaseId(bundle?.manifest?.caseId)} ${displayState(bundle?.manifest?.state)} fail\n`);
    return false;
  }
}

const argumentsList = process.argv.slice(2);
if (argumentsList.length === 1 && argumentsList[0] === '--help') {
  printUsage();
} else {
  const sealed = argumentsList[0] === '--sealed';
  const caseDirectories = sealed ? argumentsList.slice(1) : argumentsList;
  if (caseDirectories.length !== 4) {
    printUsage();
    process.exitCode = 1;
  } else {
    const results = await Promise.all(caseDirectories.map((directory) => validateDirectory(directory, sealed)));
    if (results.includes(false)) process.exitCode = 1;
  }
}
