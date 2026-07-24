import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  mkdtemp,
  readFile,
  readdir,
  rename,
  rm,
  stat,
  writeFile,
} from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import * as exportModule from '../scripts/export-vira-readonly.mjs';

const { buildPsqlInvocation } = exportModule;

test('keeps the database URL and password out of psql arguments', () => {
  const result = buildPsqlInvocation({
    databaseUrl: 'postgresql://reader:secret-value@db.example:5432/vira?sslmode=require',
    sqlFile: '/absolute/export-readonly.sql',
    baseEnv: {
      DATABASE_URL: 'must-be-removed',
      PGSERVICE: 'must-be-removed',
      PGSERVICEFILE: 'must-be-removed',
      PGSSLMODE: 'prefer',
      PATH: '/usr/bin:/bin',
    },
  });

  assert.doesNotMatch(JSON.stringify(result.args), /secret-value|postgresql:/);
  assert.deepEqual(result.args, [
    '--no-psqlrc',
    '--set=ON_ERROR_STOP=1',
    '--quiet',
    '--tuples-only',
    '--no-align',
    '--file=/absolute/export-readonly.sql',
  ]);
  assert.equal(result.env.DATABASE_URL, undefined);
  assert.equal(result.env.PGSERVICE, undefined);
  assert.equal(result.env.PGSERVICEFILE, undefined);
  assert.equal(result.env.PGHOST, 'db.example');
  assert.equal(result.env.PGPORT, '5432');
  assert.equal(result.env.PGDATABASE, 'vira');
  assert.equal(result.env.PGUSER, 'reader');
  assert.equal(result.env.PGPASSWORD, 'secret-value');
  assert.equal(result.env.PGSSLMODE, 'require');
  assert.equal(result.env.PATH, '/usr/bin:/bin');
});

test('requires a database URL without spawning psql', () => {
  assert.throws(
    () => buildPsqlInvocation({
      databaseUrl: '',
      sqlFile: '/absolute/export-readonly.sql',
    }),
    /^Error: DATABASE_URL is required$/,
  );
});

test('removes every inherited libpq variable while preserving non-libpq environment', () => {
  const result = buildPsqlInvocation({
    databaseUrl: 'postgresql://reader:password@db.example/vira',
    sqlFile: '/absolute/export-readonly.sql',
    baseEnv: {
      DATABASE_URL: 'removed',
      PGHOSTADDR: 'removed',
      PGOPTIONS: 'removed',
      PGPASSFILE: 'removed',
      PGSSLKEY: 'removed',
      PGSSLCERT: 'removed',
      PGSSLROOTCERT: 'removed',
      PGSSLMODE: 'removed',
      PATH: '/usr/bin:/bin',
      APP_MODE: 'fixture',
    },
  });

  assert.deepEqual(
    Object.keys(result.env).filter((key) => key.startsWith('PG')).sort(),
    ['PGDATABASE', 'PGHOST', 'PGPASSWORD', 'PGPORT', 'PGUSER'],
  );
  assert.equal(result.env.DATABASE_URL, undefined);
  assert.equal(result.env.PATH, '/usr/bin:/bin');
  assert.equal(result.env.APP_MODE, 'fixture');
});

test('normalizes IPv6 host brackets and accepts only a libpq sslmode', () => {
  const result = buildPsqlInvocation({
    databaseUrl: 'postgresql://reader:password@[2001:db8::1]:5433/vira?sslmode=verify-full',
    sqlFile: '/absolute/export-readonly.sql',
    baseEnv: {},
  });

  assert.equal(result.env.PGHOST, '2001:db8::1');
  assert.equal(result.env.PGPORT, '5433');
  assert.equal(result.env.PGSSLMODE, 'verify-full');
});

test('redacts invalid URL protocol identity encoding database and sslmode errors', () => {
  const invalidUrls = [
    'https://reader:password@db.example/vira',
    'postgresql://:password@db.example/vira',
    'postgresql://reader:password@db.example/',
    'postgresql://reader%ZZ:password@db.example/vira',
    'postgresql://reader:password@db.example/vira%ZZ',
    'postgresql://reader:password@db.example/vira?sslmode=unsafe-mode',
  ];

  for (const databaseUrl of invalidUrls) {
    assert.throws(
      () => buildPsqlInvocation({
        databaseUrl,
        sqlFile: '/absolute/export-readonly.sql',
        baseEnv: {},
      }),
      /^Error: DATABASE_URL is invalid$/,
    );
  }
});

test('redacts malformed psql JSON without including raw output fragments', () => {
  const rawFragment = 'raw-row-fragment';
  let failure;

  try {
    exportModule.parseViraExport(`{"market":[${rawFragment}`);
  } catch (error) {
    failure = error;
  }

  assert.equal(failure?.message, 'Vira export returned invalid JSON');
  assert.doesNotMatch(failure?.message ?? '', new RegExp(rawFragment));
});

test('atomically writes exact validated JSON bytes with mode 0600 and digest', async (t) => {
  const temporaryDirectory = await mkdtemp('/private/tmp/vira-export-file-test-');
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const outputFile = join(temporaryDirectory, 'vira-export.raw.json');
  const jsonText = '{"market":[],"growth":[]}';

  const digest = await exportModule.writeViraExportFile(jsonText, outputFile);

  assert.deepEqual(await readFile(outputFile), Buffer.from(`${jsonText}\n`));
  assert.equal(
    digest,
    `sha256:${createHash('sha256').update(jsonText).digest('hex')}`,
  );
  assert.equal((await stat(outputFile)).mode & 0o777, 0o600);
  assert.deepEqual(await readdir(temporaryDirectory), ['vira-export.raw.json']);
  assert.equal(
    exportModule.formatExportSuccess(digest),
    `Vira read-only export saved ${digest}\n`,
  );
});

test('does not overwrite an exclusive temporary-file collision', async (t) => {
  const temporaryDirectory = await mkdtemp('/private/tmp/vira-export-file-test-');
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const outputFile = join(temporaryDirectory, 'vira-export.raw.json');
  const temporaryFile = join(temporaryDirectory, '.known-export.tmp');
  await writeFile(temporaryFile, 'existing');

  await assert.rejects(
    exportModule.writeViraExportFile(
      '{"market":[],"growth":[]}',
      outputFile,
      { temporaryFile },
    ),
    (error) => error?.code === 'EEXIST',
  );
  assert.equal(await readFile(temporaryFile, 'utf8'), 'existing');
  await assert.rejects(stat(outputFile), (error) => error?.code === 'ENOENT');
});

test('cleans an owned temporary file when exclusive write creates then throws', async (t) => {
  const temporaryDirectory = await mkdtemp('/private/tmp/vira-export-file-test-');
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const outputFile = join(temporaryDirectory, 'vira-export.raw.json');
  const temporaryFile = join(temporaryDirectory, '.post-create-failure.tmp');

  await assert.rejects(
    exportModule.writeViraExportFile(
      '{"market":[],"growth":[]}',
      outputFile,
      {
        temporaryFile,
        fileSystem: {
          writeFile: async (...args) => {
            await writeFile(...args);
            throw new Error('injected post-create write failure');
          },
          rename,
          rm,
        },
      },
    ),
    /injected post-create write failure/,
  );
  await assert.rejects(stat(temporaryFile), (error) => error?.code === 'ENOENT');
  await assert.rejects(stat(outputFile), (error) => error?.code === 'ENOENT');
});
