import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import {
  mkdir,
  rename,
  rm,
  writeFile,
} from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const PSQL = '/opt/homebrew/opt/postgresql@15/bin/psql';
const ROOT = resolve('.codex/experiments/shortform-director-quality-input');
const SSL_MODES = new Set([
  'disable',
  'allow',
  'prefer',
  'require',
  'verify-ca',
  'verify-full',
]);
const defaultFileSystem = {
  rename,
  rm,
  writeFile,
};

export function buildPsqlInvocation({ databaseUrl, sqlFile, baseEnv = process.env }) {
  if (!databaseUrl) throw new Error('DATABASE_URL is required');

  let connection;
  try {
    const parsed = new URL(databaseUrl);
    if (!['postgres:', 'postgresql:'].includes(parsed.protocol)) {
      throw new Error('unsupported protocol');
    }
    const host = parsed.hostname.replace(/^\[(.*)\]$/, '$1');
    const database = decodeURIComponent(parsed.pathname.slice(1));
    const user = decodeURIComponent(parsed.username);
    const password = decodeURIComponent(parsed.password);
    const sslMode = parsed.searchParams.get('sslmode');
    if (!host || !database || !user || (sslMode && !SSL_MODES.has(sslMode))) {
      throw new Error('invalid connection fields');
    }
    connection = {
      host,
      port: parsed.port || '5432',
      database,
      user,
      password,
      sslMode,
    };
  } catch {
    throw new Error('DATABASE_URL is invalid');
  }

  const childEnv = { ...baseEnv };
  for (const key of Object.keys(childEnv)) {
    if (key === 'DATABASE_URL' || key.startsWith('PG')) delete childEnv[key];
  }
  childEnv.PGHOST = connection.host;
  childEnv.PGPORT = connection.port;
  childEnv.PGDATABASE = connection.database;
  childEnv.PGUSER = connection.user;
  childEnv.PGPASSWORD = connection.password;
  if (connection.sslMode) childEnv.PGSSLMODE = connection.sslMode;

  return {
    command: PSQL,
    args: [
      '--no-psqlrc',
      '--set=ON_ERROR_STOP=1',
      '--quiet',
      '--tuples-only',
      '--no-align',
      `--file=${sqlFile}`,
    ],
    env: childEnv,
  };
}

export function parseViraExport(stdout) {
  const jsonText = stdout.trim();
  try {
    JSON.parse(jsonText);
  } catch {
    throw new Error('Vira export returned invalid JSON');
  }
  return jsonText;
}

export async function writeViraExportFile(
  jsonText,
  outputFile,
  {
    temporaryFile,
    fileSystem = defaultFileSystem,
  } = {},
) {
  const validatedJsonText = parseViraExport(jsonText);
  await mkdir(dirname(outputFile), { recursive: true });
  const temporary = temporaryFile ?? join(
    dirname(outputFile),
    `.${basename(outputFile)}.${process.pid}.${randomUUID()}.tmp`,
  );
  let ownsTemporary = true;
  try {
    try {
      await fileSystem.writeFile(temporary, `${validatedJsonText}\n`, {
        flag: 'wx',
        mode: 0o600,
      });
    } catch (error) {
      if (error?.code === 'EEXIST') ownsTemporary = false;
      throw error;
    }
    await fileSystem.rename(temporary, outputFile);
  } finally {
    if (ownsTemporary) await fileSystem.rm(temporary, { force: true });
  }
  return `sha256:${createHash('sha256').update(validatedJsonText).digest('hex')}`;
}

export function formatExportSuccess(digest) {
  return `Vira read-only export saved ${digest}\n`;
}

export async function exportViraReadonly({ databaseUrl, sqlFile, outputFile }) {
  const invocation = buildPsqlInvocation({ databaseUrl, sqlFile });
  const stdout = await new Promise((resolvePromise, reject) => {
    const child = spawn(invocation.command, invocation.args, {
      env: invocation.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    child.stdout.setEncoding('utf8');
    child.stderr.resume();
    child.stdout.on('data', (chunk) => {
      out += chunk;
    });
    child.on('error', () => {
      reject(new Error('read-only psql could not be started'));
    });
    child.on('close', (code) => {
      if (code === 0) resolvePromise(out);
      else reject(new Error(`read-only psql failed with exit ${code}`));
    });
  });

  return writeViraExportFile(parseViraExport(stdout), outputFile);
}

if (process.argv[1]
  && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const digest = await exportViraReadonly({
    databaseUrl: process.env.DATABASE_URL,
    sqlFile: resolve(ROOT, 'vira/export-readonly.sql'),
    outputFile: resolve(ROOT, 'private/vira-export.raw.json'),
  });
  process.stdout.write(formatExportSuccess(digest));
}
