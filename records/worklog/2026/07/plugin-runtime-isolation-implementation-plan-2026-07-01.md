# Plugin Runtime Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make packaged app startup independent from optional plugin Python dependencies by using a minimal base venv and plugin-specific venvs.

**Architecture:** `first-run.ts` owns only the base packaged runtime. A new plugin venv installer owns per-plugin Python dependency installation and freshness markers. `LocalPluginManager` ensures a plugin venv before spawning packaged plugin processes, and `PluginProcess` launches the plugin with that venv's Python.

**Tech Stack:** Electron main process TypeScript, Node test runner, uv, packaged Python venvs, Clipper Python plugin pyprojects.

---

## File Map

- Modify `desktop/clipper_electron/src/main/setup/first-run.ts`
  - Export base venv helpers and startup uv argument builder.
  - Remove plugin package reinstall from startup sync.
- Create `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`
  - Resolve plugin venv paths.
  - Read/write dependency install marker JSON.
  - Generate plugin-only uv install args.
  - Ensure a plugin venv in packaged mode.
- Modify `desktop/clipper_electron/src/main/plugin/plugin-manager.ts`
  - Accept optional plugin venv installer.
  - Run plugin dependency preflight before packaged plugin spawn.
  - Pass plugin-specific venv path into `PluginProcess`.
- Modify `desktop/clipper_electron/src/main/plugin/plugin-process.ts`
  - Continue accepting a concrete venv path.
  - Treat that path as plugin-specific in packaged mode.
- Modify `desktop/clipper_electron/src/main/main.ts`
  - Instantiate the plugin venv installer in packaged mode.
  - Keep app startup on base runtime only.
- Add `desktop/clipper_electron/test/first-run-base-venv.test.js`
  - Verify startup args do not include plugin packages.
- Add `desktop/clipper_electron/test/plugin-venv.test.js`
  - Verify path resolution, marker freshness, and plugin install args.
- Later phase modifies `desktop/clipper_python/plugins/dance_highlight/*`
  - Replace InsightFace with YuNet/SFace after runtime isolation lands.

## Task 1: Lock Startup Sync Behavior

**Files:**
- Test: `desktop/clipper_electron/test/first-run-base-venv.test.js`
- Modify: `desktop/clipper_electron/src/main/setup/first-run.ts`

- [ ] **Step 1: Write the failing test**

Create `test/first-run-base-venv.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');

const { buildBaseVenvSyncArgs } = require('../dist-electron/main/setup/first-run');

test('base venv sync does not reinstall plugin packages during app startup', () => {
  const args = buildBaseVenvSyncArgs('C:\\resources\\clipper_python', []);

  assert.equal(args.includes('clipper-plugin-dialog-highlight'), false);
  assert.equal(args.includes('clipper-plugin-dance-highlight'), false);
  assert.equal(args.includes('clipper-plugin-clipper1-video-render'), false);
  assert.equal(args.includes('--directory'), true);
  assert.equal(args.includes('C:\\resources\\clipper_python'), true);
});
```

- [ ] **Step 2: Run the test to verify RED**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/first-run-base-venv.test.js
```

Expected: FAIL because `buildBaseVenvSyncArgs` is not exported.

- [ ] **Step 3: Implement minimal production code**

Add `buildBaseVenvSyncArgs(pythonRoot, extraArgs)` to `first-run.ts` and use it
inside `runUvSync`. The base args must include `sync --directory <pythonRoot>`
and must not include plugin `--reinstall-package` values.

- [ ] **Step 4: Run GREEN check**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/first-run-base-venv.test.js
```

Expected: PASS.

## Task 2: Add Plugin Venv Planning Helpers

**Files:**
- Create: `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`
- Test: `desktop/clipper_electron/test/plugin-venv.test.js`

- [ ] **Step 1: Write failing tests**

Create tests covering:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { join } = require('node:path');

const {
  getPluginVenvPath,
  getPluginDependencyMarkerPath,
  buildPluginVenvSyncArgs,
  isPluginDependencyMarkerFresh,
} = require('../dist-electron/main/plugin/plugin-venv');

test('plugin venv path is isolated per plugin', () => {
  assert.equal(
    getPluginVenvPath('C:\\Users\\u\\AppData\\Roaming\\Clipper2', 'dance_highlight'),
    join('C:\\Users\\u\\AppData\\Roaming\\Clipper2', 'venvs', 'plugins', 'dance_highlight'),
  );
});

test('plugin sync args install only the selected workspace package', () => {
  const args = buildPluginVenvSyncArgs({
    pythonRoot: 'C:\\resources\\clipper_python',
    pluginPackageName: 'clipper-plugin-dance-highlight',
  });

  assert.deepEqual(args.slice(0, 4), ['sync', '--directory', 'C:\\resources\\clipper_python']);
  assert.equal(args.includes('clipper-plugin-dance-highlight'), true);
  assert.equal(args.includes('clipper-plugin-dialog-highlight'), false);
});

test('dependency marker is stale when platform changes', () => {
  const expected = {
    pluginName: 'dance_highlight',
    pluginVersion: '0.1.0',
    pluginPackageName: 'clipper-plugin-dance-highlight',
    platform: 'win32',
    arch: 'x64',
    pythonMajorMinor: '3.11',
  };
  const actual = { ...expected, platform: 'darwin' };

  assert.equal(isPluginDependencyMarkerFresh(actual, expected), false);
});
```

- [ ] **Step 2: Run tests to verify RED**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/plugin-venv.test.js
```

Expected: FAIL because `plugin-venv` does not exist.

- [ ] **Step 3: Implement helper module**

Implement path helpers, marker comparison, and uv args. Keep this module free of
Electron imports except where needed by a later `ensurePluginVenv` function.

- [ ] **Step 4: Run GREEN check**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/plugin-venv.test.js
```

Expected: PASS.

## Task 3: Ensure Plugin Venv Before Packaged Plugin Spawn

**Files:**
- Modify: `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`
- Modify: `desktop/clipper_electron/src/main/plugin/plugin-manager.ts`
- Modify: `desktop/clipper_electron/src/main/main.ts`
- Test: `desktop/clipper_electron/test/plugin-venv.test.js`

- [ ] **Step 1: Add failing test for installer contract**

Extend `plugin-venv.test.js` with a fake runner that records uv args and writes
a marker. Expected behavior: `ensurePluginVenv()` returns the plugin venv path
and does not reinstall when the marker is fresh.

- [ ] **Step 2: Run test to verify RED**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/plugin-venv.test.js
```

Expected: FAIL because `ensurePluginVenv` is not implemented.

- [ ] **Step 3: Implement installer and manager integration**

Implement `ensurePluginVenv()` with injectable process runner for tests. In
`LocalPluginManager`, run the installer in packaged mode before creating
`PluginProcess`, then pass the returned venv path. In `main.ts`, instantiate the
installer with `process.resourcesPath`, `app.getPath('userData')`, platform,
arch, and the bundled uv binary path.

- [ ] **Step 4: Run GREEN check**

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/plugin-venv.test.js test/plugin-manager-exit-listener.test.js
```

Expected: PASS.

## Task 4: Full Electron Test Pass

**Files:**
- All changed Electron files.

- [ ] **Step 1: Run full Electron tests**

```text
cd desktop/clipper_electron
node --test test/*.js test/*.mjs
npx tsc -p tsconfig.json
```

Expected: PASS.

- [ ] **Step 2: Inspect git diff**

```text
git -C desktop/clipper_electron diff --stat
git -C desktop/clipper_electron diff -- src/main/setup/first-run.ts src/main/plugin/plugin-venv.ts src/main/plugin/plugin-manager.ts src/main/main.ts
```

Expected: only runtime isolation changes.

## Task 5: Dance Face Model Replacement Plan Gate

**Files:**
- Modify or create a follow-up `.codex` worklog if runtime isolation uncovers
  additional constraints.

- [ ] **Step 1: Do not replace InsightFace in the same unverified batch**

Stop after runtime isolation is tested. Then plan the YuNet/SFace spike as a
separate implementation batch using fixed samples and quality metrics.

## Verification Summary Required Before Completion

Report:

- Electron tests run and results.
- TypeScript compile result.
- Whether Windows packaged verification still needs to be run.
- Files changed.
- Remaining work for YuNet/SFace replacement.

## Progress 2026-07-01

Completed on `desktop/clipper_electron` branch
`feature/plugin-runtime-isolation`:

- Packaged startup base venv no longer uses `uv sync` against the
  `clipper_python` workspace.
- Base runtime now uses `uv venv --no-project --allow-existing <baseVenv>` and
  installs only `yt-dlp>=2025.12.8` with `uv pip install --only-binary :all:`.
- Added plugin-specific venv helper and marker logic.
- `LocalPluginManager` now calls a packaged plugin venv installer before
  spawning a plugin and passes the returned plugin venv path to `PluginProcess`.
- `main.ts` wires packaged plugin venv installation through
  `ensurePluginVenv()`.

Local verification:

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/*.js test/*.mjs
-> 44 pass
```

Follow-up verification after nested plugin venv cwd/PATH fix and YuNet/SFace
metadata updates:

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/*.js test/*.mjs
-> 47 pass
```

Extra local runtime check:

```text
uv venv --no-project --allow-existing /private/tmp/clipper-base-venv-check2
uv pip install --python /private/tmp/clipper-base-venv-check2/bin/python --only-binary :all: 'yt-dlp>=2025.12.8'
/private/tmp/clipper-base-venv-check2/bin/python -c "import importlib.util; print('yt_dlp', importlib.util.find_spec('yt_dlp') is not None); print('insightface', importlib.util.find_spec('insightface') is not None)"
-> yt_dlp True
-> insightface False
```

Not completed:

- Windows packaged installer verification.
- Mac representative dance quality run with real sample video/reference setup.
- Windows dance plugin venv install/run smoke.
