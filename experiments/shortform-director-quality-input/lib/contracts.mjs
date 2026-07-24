import { constants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import { join, isAbsolute, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

export const CASE_IDS = ['BEAUTY-01', 'PRODUCT-01', 'IDOL-01', 'EXPERT-01'];
export const SOURCE_CLASSES = [
  'official_fact',
  'authority_explanation',
  'audience_observation',
  'market_observation',
  'creative_pattern',
  'editorial_interpretation',
  'ai_hypothesis',
];
export const AVAILABILITY = [
  'verified',
  'partial',
  'insufficient',
  'unavailable',
  'provider_not_called',
];
export const VIRA_STATES = [
  'provider_not_called',
  'sufficient',
  'partial',
  'insufficient',
  'unavailable',
];
export const DIGESTED_CASE_FILES = [
  'profile.json',
  'episodes.json',
  'source-cards.json',
  'audience-cards.json',
  'reference-cards.json',
  'vira-evidence.json',
  'feedback-cards.json',
];

const CASE_FILES = {
  'manifest.json': 'manifest',
  'profile.json': 'profile',
  'episodes.json': 'episodes',
  'source-cards.json': 'sources',
  'audience-cards.json': 'audience',
  'reference-cards.json': 'references',
  'vira-evidence.json': 'vira',
  'feedback-cards.json': 'feedback',
};
const EXPERIMENT_DIRECTORY = fileURLToPath(new URL('../', import.meta.url));

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function sha256Digest(value) {
  return typeof value === 'string' && /^sha256:[0-9a-f]{64}$/.test(value);
}

function isoTimestamp(value) {
  return nonEmpty(value) && !Number.isNaN(Date.parse(value));
}

function isInside(parentDirectory, targetPath) {
  const pathFromParent = relative(parentDirectory, targetPath);
  return pathFromParent === '' || (!pathFromParent.startsWith('..') && !isAbsolute(pathFromParent));
}

function sameIdentity(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

async function inspectCaseDirectory(caseDirectory, experimentDirectory, expectedIdentity) {
  const directoryStats = await lstat(caseDirectory);
  if (directoryStats.isSymbolicLink()) {
    throw new Error('case directory must not be a symbolic link');
  }
  if (!directoryStats.isDirectory()) throw new Error('case directory must be a directory');
  if (expectedIdentity && !sameIdentity(directoryStats, expectedIdentity)) {
    throw new Error('case directory changed while loading');
  }

  const resolvedDirectory = await realpath(caseDirectory);
  if (!isInside(experimentDirectory, resolvedDirectory)) {
    throw new Error('case directory must be inside the experiment workspace');
  }
  if (expectedIdentity && resolvedDirectory !== expectedIdentity.realpath) {
    throw new Error('case directory changed while loading');
  }
  return { ...directoryStats, realpath: resolvedDirectory };
}

async function readCaseJson(caseDirectory, directoryIdentity, fileName) {
  await inspectCaseDirectory(caseDirectory, directoryIdentity.experimentRoot, directoryIdentity);
  const filePath = join(caseDirectory, fileName);
  const fileStats = await lstat(filePath);
  if (fileStats.isSymbolicLink()) {
    throw new Error(`case file ${fileName} must not be a symbolic link`);
  }
  if (!fileStats.isFile()) throw new Error(`case file ${fileName} must be a regular file`);
  const resolvedFile = await realpath(filePath);
  if (!isInside(directoryIdentity.realpath, resolvedFile)) {
    throw new Error(`case file ${fileName} must stay inside the case directory`);
  }

  let handle;
  try {
    handle = await open(filePath, constants.O_RDONLY | constants.O_NOFOLLOW);
    const openedStats = await handle.stat();
    if (!openedStats.isFile()) throw new Error(`case file ${fileName} must be a regular file`);
    if (!sameIdentity(fileStats, openedStats)) {
      throw new Error(`case file ${fileName} changed while loading`);
    }
    const value = JSON.parse(await handle.readFile({ encoding: 'utf8' }));
    await inspectCaseDirectory(caseDirectory, directoryIdentity.experimentRoot, directoryIdentity);
    return value;
  } catch (error) {
    if (error?.code === 'ELOOP') throw new Error(`case file ${fileName} must not be a symbolic link`);
    throw error;
  } finally {
    await handle?.close();
  }
}

export async function loadCaseBundle(caseDirectory) {
  const experimentDirectory = await realpath(EXPERIMENT_DIRECTORY);
  const directoryIdentity = await inspectCaseDirectory(caseDirectory, experimentDirectory);
  directoryIdentity.experimentRoot = experimentDirectory;

  const bundle = {};
  for (const [fileName, bundleKey] of Object.entries(CASE_FILES)) {
    bundle[bundleKey] = await readCaseJson(caseDirectory, directoryIdentity, fileName);
  }
  await inspectCaseDirectory(caseDirectory, experimentDirectory, directoryIdentity);
  return bundle;
}

export function validateCaseBundle(bundle, { sealed }) {
  invariant(bundle && typeof bundle === 'object', 'case bundle must be an object');
  invariant(CASE_IDS.includes(bundle.manifest?.caseId), 'manifest.caseId is invalid');
  invariant(
    bundle.manifest.schemaVersion === 'quality-input-pack-manifest.v1'
      && isoTimestamp(bundle.manifest.cutoffAt),
    'manifest schemaVersion and cutoffAt are required',
  );
  invariant(
    bundle.profile?.profileSchemaVersion === 'quality-input-profile.v1'
      && bundle.profile.caseId === bundle.manifest.caseId
      && nonEmpty(bundle.profile.operatorRole)
      && nonEmpty(bundle.profile.audience)
      && nonEmpty(bundle.profile.desiredAfterState)
      && Array.isArray(bundle.profile.toneRules)
      && bundle.profile.toneRules.length > 0
      && bundle.profile.toneRules.every(nonEmpty)
      && Array.isArray(bundle.profile.prohibitedClaims)
      && bundle.profile.prohibitedClaims.length > 0
      && bundle.profile.prohibitedClaims.every(nonEmpty),
    'profile contract is invalid',
  );
  invariant(
    bundle.episodes?.episodeSchemaVersion === 'quality-input-episodes.v1'
      && bundle.episodes.caseId === bundle.manifest.caseId
      && nonEmpty(bundle.episodes.episodeA?.id)
      && nonEmpty(bundle.episodes.episodeA?.question)
      && nonEmpty(bundle.episodes.episodeB?.id)
      && nonEmpty(bundle.episodes.episodeB?.question)
      && bundle.episodes.episodeA.id === `${bundle.manifest.caseId}-A`
      && bundle.episodes.episodeB.id === `${bundle.manifest.caseId}-B`,
    'episodes A and B require fixed IDs and questions',
  );
  invariant(
    Array.isArray(bundle.sources?.cards)
      && bundle.sources.cards.length >= 3
      && bundle.sources.cards.length <= 5,
    'source cards must contain 3 to 5 items',
  );
  invariant(
    Array.isArray(bundle.audience?.questions)
      && bundle.audience.questions.length === 10,
    'audience.questions must contain exactly 10 items',
  );
  invariant(
    Array.isArray(bundle.references?.cards)
      && bundle.references.cards.length >= 1
      && bundle.references.cards.length <= 2,
    'reference cards must contain 1 to 2 items',
  );
  invariant(VIRA_STATES.includes(bundle.vira?.state), 'vira.state is invalid');
  invariant(
    Array.isArray(bundle.vira?.evidence) && bundle.vira.evidence.length <= 5,
    'vira.evidence must contain at most 5 items',
  );
  for (const question of bundle.audience.questions) {
    invariant(
      nonEmpty(question.id)
        && nonEmpty(question.question)
        && ['general_reader_question', 'audience_observation'].includes(question.originClass),
      'audience question is invalid',
    );
    invariant(
      !('author' in question) && !('handle' in question) && !('profileUrl' in question),
      'audience question must not contain identity fields',
    );
    if (question.originClass === 'audience_observation') {
      invariant(
        nonEmpty(question.sourceId) && nonEmpty(question.evidenceLocator),
        'audience observation requires sourceId and evidenceLocator',
      );
    }
  }
  for (const reference of bundle.references.cards) {
    invariant(
      nonEmpty(reference.id)
        && nonEmpty(reference.pattern)
        && nonEmpty(reference.allowedInfluence)
        && nonEmpty(reference.forbiddenUse)
        && nonEmpty(reference.rightsNote),
      'reference card is invalid',
    );
  }
  for (const evidence of bundle.vira.evidence) {
    invariant(
      evidence.schemaVersion === 'vira-evidence.v1'
        && ['market.video-observation', 'market.peer-growth'].includes(evidence.kind)
        && evidence.source?.system === 'vira'
        && ['sufficient', 'partial', 'insufficient', 'unavailable']
          .includes(evidence.observation?.state),
      'Vira evidence is invalid for this experiment',
    );
  }
  invariant(
    ['not_collected', 'ready'].includes(bundle.feedback?.state)
      && Array.isArray(bundle.feedback?.cards)
      && bundle.feedback.cards.length <= 3,
    'feedback must be not_collected or ready with at most 3 cards',
  );
  if (bundle.feedback.state === 'not_collected') {
    invariant(bundle.feedback.cards.length === 0, 'not_collected feedback must be empty');
  }
  if (bundle.feedback.state === 'ready') {
    invariant(
      bundle.feedback.cards.length >= 1
        && bundle.feedback.cards.every((card) => (
          nonEmpty(card.id)
          && nonEmpty(card.sourceOutputArtifactId)
          && ['approve', 'revise', 'reject'].includes(card.decision)
          && ['hook', 'thesis', 'claim', 'evidence', 'visual', 'feasibility', 'tone']
            .includes(card.appliesTo)
          && nonEmpty(card.observedProblem)
          && nonEmpty(card.preferredRule)
          && nonEmpty(card.evidenceOrExample)
          && ['route', 'topic_family', 'global'].includes(card.scope)
        )),
      'ready feedback requires 1 to 3 complete cards',
    );
  }
  for (const card of bundle.sources.cards) {
    invariant(nonEmpty(card.id), 'source card requires id');
    invariant(SOURCE_CLASSES.includes(card.sourceClass), 'sourceClass is invalid');
    invariant(
      nonEmpty(card.title)
        && nonEmpty(card.publisher)
        && nonEmpty(card.originalUrl)
        && (card.publishedAt === null || isoTimestamp(card.publishedAt))
        && isoTimestamp(card.retrievedAt)
        && isoTimestamp(card.cutoffAt)
        && Array.isArray(card.permittedUse)
        && card.permittedUse.length > 0
        && card.permittedUse.every((item) => (
          ['fact', 'audience', 'market', 'creative', 'editorial'].includes(item)
        ))
        && nonEmpty(card.rightsNote)
        && typeof card.notes === 'string',
      'source card metadata is invalid',
    );
    invariant(AVAILABILITY.includes(card.availability), 'availability is invalid');
    invariant(Array.isArray(card.claims), 'source card claims must be an array');
    if (['unavailable', 'insufficient'].includes(card.availability)) {
      invariant(card.claims.length === 0, 'unavailable source card claims must be empty');
    }
    if (sealed && !['unavailable', 'insufficient'].includes(card.availability)) {
      invariant(
        sha256Digest(card.contentDigest)
          && card.claims.length > 0
          && card.claims.every((claim) => (
            nonEmpty(claim.id)
            && nonEmpty(claim.statement)
            && nonEmpty(claim.evidenceLocator)
            && ['paraphrase', 'short_quote'].includes(claim.excerptMode)
            && nonEmpty(claim.evidenceExcerpt)
          )),
        'sealed source card requires contentDigest and located claims',
      );
    }
  }
  if (sealed) {
    invariant(bundle.manifest.state === 'sealed', 'sealed bundle requires sealed manifest');
    const digestKeys = Object.keys(bundle.manifest.fileDigests ?? {}).sort();
    invariant(
      JSON.stringify(digestKeys) === JSON.stringify([...DIGESTED_CASE_FILES].sort())
        && digestKeys.every((key) => sha256Digest(bundle.manifest.fileDigests[key])),
      'sealed manifest requires every file digest',
    );
  }
  return bundle;
}
