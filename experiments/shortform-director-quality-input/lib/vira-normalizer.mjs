const CASE_IDS = ['BEAUTY-01', 'PRODUCT-01', 'IDOL-01', 'EXPERT-01'];
const CASE_ID_SET = new Set(CASE_IDS);
const MARKET_KEYS = new Set([
  'caseId',
  'rowId',
  'platformVideoId',
  'title',
  'channel',
  'keyword',
  'category',
  'tags',
  'snapshotDate',
  'views',
  'viewsSource',
  'likes',
  'comments',
  'positive',
  'negative',
  'neutral',
  'classified',
]);
const GROWTH_KEYS = new Set([
  'caseId',
  'rowId',
  'platformVideoId',
  'keyword',
  'category',
  'snapshotFrom',
  'snapshotTo',
  'snapshotCount',
  'dailyViewDelta',
  'ageDays',
  'ageBucket',
  'percentile',
  'peerSampleSize',
  'risingThreshold',
  'isRising',
  'isNewRising',
]);
const AGE_BUCKETS = new Set(['0-7', '8-30', '31-90', '91-365', '365+']);

function invariant(condition) {
  if (!condition) throw new Error('invalid');
}

function exactKeys(value, allowedKeys) {
  invariant(
    value
      && typeof value === 'object'
      && !Array.isArray(value)
      && Object.keys(value).every((key) => allowedKeys.has(key)),
  );
}

function nonEmptyString(value) {
  return typeof value === 'string' && value.length > 0;
}

function optionalString(value) {
  return value === null || value === undefined || nonEmptyString(value);
}

function nonNegativeCount(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function optionalCount(value) {
  return value === null || value === undefined || nonNegativeCount(value);
}

function isoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
}

function validateIdentity(row) {
  invariant(
    CASE_ID_SET.has(row.caseId)
      && Number.isSafeInteger(row.rowId)
      && row.rowId > 0
      && nonEmptyString(row.platformVideoId),
  );
}

function validateMarketRow(row) {
  exactKeys(row, MARKET_KEYS);
  validateIdentity(row);
  invariant(
    optionalString(row.title)
      && optionalString(row.channel)
      && optionalString(row.keyword)
      && optionalString(row.category)
      && Array.isArray(row.tags)
      && row.tags.every(nonEmptyString)
      && (row.snapshotDate === null || isoDate(row.snapshotDate))
      && Object.hasOwn(row, 'views')
      && optionalCount(row.views)
      && ['snapshot', 'discovery'].includes(row.viewsSource)
      && optionalCount(row.likes)
      && optionalCount(row.comments)
      && nonNegativeCount(row.positive)
      && nonNegativeCount(row.negative)
      && nonNegativeCount(row.neutral)
      && nonNegativeCount(row.classified)
      && row.positive + row.negative + row.neutral === row.classified,
  );
  if (row.viewsSource === 'snapshot') invariant(isoDate(row.snapshotDate));
}

function expectedAgeBucket(ageDays) {
  if (ageDays <= 7) return '0-7';
  if (ageDays <= 30) return '8-30';
  if (ageDays <= 90) return '31-90';
  if (ageDays <= 365) return '91-365';
  return '365+';
}

function validateGrowthRow(row) {
  exactKeys(row, GROWTH_KEYS);
  validateIdentity(row);
  invariant(
    optionalString(row.keyword)
      && optionalString(row.category)
      && isoDate(row.snapshotFrom)
      && isoDate(row.snapshotTo)
      && row.snapshotFrom <= row.snapshotTo
      && row.snapshotCount === 3
      && Number.isFinite(row.dailyViewDelta)
      && nonNegativeCount(row.ageDays)
      && AGE_BUCKETS.has(row.ageBucket)
      && row.ageBucket === expectedAgeBucket(row.ageDays)
      && Number.isSafeInteger(row.percentile)
      && row.percentile >= 0
      && row.percentile <= 100
      && Number.isSafeInteger(row.peerSampleSize)
      && row.peerSampleSize > 0
      && row.risingThreshold === 90
      && typeof row.isRising === 'boolean'
      && typeof row.isNewRising === 'boolean'
      && row.isRising === (row.percentile >= 90)
      && row.isNewRising === (row.percentile >= 90 && row.ageDays <= 7),
  );
}

function validateRows(rows, validateRow) {
  invariant(Array.isArray(rows));
  const rowIdsByCase = new Map();
  const videoIdsByCase = new Map();
  for (const row of rows) {
    validateRow(row);
    const rowIds = rowIdsByCase.get(row.caseId) ?? new Set();
    const videoIds = videoIdsByCase.get(row.caseId) ?? new Set();
    invariant(!rowIds.has(row.rowId) && !videoIds.has(row.platformVideoId));
    rowIds.add(row.rowId);
    videoIds.add(row.platformVideoId);
    rowIdsByCase.set(row.caseId, rowIds);
    videoIdsByCase.set(row.caseId, videoIds);
  }
}

function validateRawExport(raw) {
  try {
    exactKeys(raw, new Set(['market', 'growth']));
    invariant(Object.keys(raw).length === 2);
    validateRows(raw.market, validateMarketRow);
    validateRows(raw.growth, validateGrowthRow);
    return raw;
  } catch {
    throw new Error('Vira export is invalid');
  }
}

function assignOptional(target, key, value) {
  if (value !== null && value !== undefined) target[key] = value;
}

function marketEnvelope(row, {
  materializedAt,
  codeRevision,
  state,
  sampleSize,
}) {
  const views = row.views ?? undefined;
  const likes = row.likes ?? undefined;
  const comments = row.comments ?? undefined;
  const observation = { materializedAt, state, sampleSize };
  if (row.snapshotDate) {
    observation.window = {
      from: String(row.snapshotDate),
      to: String(row.snapshotDate),
    };
  }
  const metrics = { viewsSource: row.viewsSource };
  assignOptional(metrics, 'views', views);
  assignOptional(metrics, 'snapshotDate', row.snapshotDate);
  assignOptional(metrics, 'likes', likes);
  assignOptional(metrics, 'comments', comments);
  if (views > 0 && likes !== undefined && comments !== undefined) {
    metrics.engagementRate = Math.min(1, (likes + comments) / views);
  }
  const payload = {
    tags: Array.isArray(row.tags) ? row.tags.slice(0, 5) : [],
    metrics,
  };
  assignOptional(payload, 'title', row.title);
  assignOptional(payload, 'channel', row.channel);
  assignOptional(payload, 'keyword', row.keyword);
  assignOptional(payload, 'naverCategory', row.category);
  if (Number(row.classified) > 0) {
    payload.commentSentiment = {
      positive: Number(row.positive ?? 0),
      negative: Number(row.negative ?? 0),
      neutral: Number(row.neutral ?? 0),
      classified: Number(row.classified),
    };
  }
  const envelope = {
    schemaVersion: 'vira-evidence.v1',
    id: `evidence.market.${row.caseId.toLowerCase()}.${row.platformVideoId}`,
    kind: 'market.video-observation',
    evidenceClass: 'observed',
    source: {
      system: 'vira',
      surface: 'shorts-market',
      lifecycle: 'active',
      codeRevision,
      recordRefs: [{ kind: 'shorts-video', id: row.rowId }],
    },
    subject: {
      platform: 'youtube_shorts',
      platformVideoId: row.platformVideoId,
    },
    observation,
    method: {
      id: 'shorts-market-cutoff-observation',
      version: '1',
      parameters: { cutoffDate: '2026-07-24' },
    },
    payload,
  };
  assignOptional(envelope.subject, 'keyword', row.keyword);
  assignOptional(envelope.subject, 'category', row.category);
  return envelope;
}

function growthEnvelope(row, { materializedAt, codeRevision, state }) {
  const envelope = {
    schemaVersion: 'vira-evidence.v1',
    id: `evidence.growth.${row.caseId.toLowerCase()}.${row.platformVideoId}`,
    kind: 'market.peer-growth',
    evidenceClass: 'derived',
    source: {
      system: 'vira',
      surface: 'shorts-growth-lab',
      lifecycle: 'lab',
      codeRevision,
      recordRefs: [{ kind: 'shorts-video', id: row.rowId }],
    },
    subject: {
      platform: 'youtube_shorts',
      platformVideoId: row.platformVideoId,
    },
    observation: {
      materializedAt,
      state,
      sampleSize: Number(row.peerSampleSize),
      window: {
        from: String(row.snapshotFrom),
        to: String(row.snapshotTo),
      },
    },
    method: {
      id: 'last3-endpoint-daily-delta-age-bucket-percentile',
      version: '1',
      parameters: {
        snapshotCount: 3,
        risingThreshold: 90,
        cutoffDate: '2026-07-24',
      },
    },
    payload: {
      snapshotFrom: String(row.snapshotFrom),
      snapshotTo: String(row.snapshotTo),
      snapshotCount: 3,
      dailyViewDelta: Number(row.dailyViewDelta),
      ageDays: Number(row.ageDays),
      ageBucket: row.ageBucket,
      percentile: Number(row.percentile),
      risingThreshold: 90,
      isRising: row.isRising === true,
      isNewRising: row.isNewRising === true,
    },
  };
  assignOptional(envelope.subject, 'keyword', row.keyword);
  assignOptional(envelope.subject, 'category', row.category);
  return envelope;
}

export function normalizeViraExport(raw, context) {
  const validated = validateRawExport(raw);
  const result = new Map();
  for (const caseId of CASE_IDS) {
    const marketRows = validated.market.filter((row) => row.caseId === caseId).slice(0, 3);
    const growthRows = validated.growth.filter((row) => row.caseId === caseId).slice(0, 2);
    const marketState = marketRows.length >= 3
      ? 'sufficient'
      : marketRows.length > 0 ? 'partial' : 'insufficient';
    const growthState = growthRows.length >= 2
      ? 'sufficient'
      : growthRows.length > 0 ? 'partial' : 'insufficient';
    const evidence = [
      ...marketRows.map((row) => marketEnvelope(row, {
        ...context,
        state: marketState,
        sampleSize: marketRows.length,
      })),
      ...growthRows.map((row) => growthEnvelope(row, {
        ...context,
        state: growthState,
      })),
    ];
    result.set(caseId, {
      schemaVersion: 'quality-input-vira-pack.v1',
      caseId,
      state: evidence.length === 0
        ? 'insufficient'
        : marketState === 'sufficient' || growthState === 'sufficient'
          ? 'sufficient'
          : 'partial',
      evidence,
    });
  }
  return result;
}
