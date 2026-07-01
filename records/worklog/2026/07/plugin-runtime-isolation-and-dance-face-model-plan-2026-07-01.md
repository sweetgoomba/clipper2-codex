# Plugin Runtime Isolation And Dance Face Model Plan

Date: 2026-07-01

## Status

Release/version-management work is paused. The active blocker is packaged app
startup and plugin runtime isolation.

Root cause from Windows PC:

```text
0.0.3 packaged app first launch
  -> ensureVenv()
  -> uv sync includes clipper-plugin-dance-highlight
  -> insightface source build requires MSVC Build Tools
  -> uv sync fails
  -> main window never opens
```

## Implementation Phases

### Phase 1: Baseline Tests And Current Failure Lock

- Add unit tests around `first-run.ts` argument construction so startup sync
  cannot include plugin packages.
- Add tests for plugin venv path resolution and marker invalidation.
- Verify existing `desktop/clipper_electron` test suite before edits where
  practical.

Expected local checks:

```text
cd desktop/clipper_electron
node --test test/*.js test/*.mjs
npx tsc -p tsconfig.json
```

### Phase 2: Base Runtime Minimalization

- Change packaged startup so `ensureVenv()` prepares only the base runtime.
- Remove `clipper-plugin-dialog-highlight`,
  `clipper-plugin-dance-highlight`, and
  `clipper-plugin-clipper1-video-render` from startup reinstall/sync.
- Ensure failure in optional plugin dependency install cannot prevent
  `openMainWindow()`.

Verification:

- Unit test proves startup args do not include plugin package names.
- Packaged launch on Windows with fresh userData opens the main window.

### Phase 3: Plugin-Specific Venv Manager

- Add a main-process helper responsible for:
  - plugin venv path resolution.
  - install marker read/write.
  - stale marker detection by plugin version, lock hash, platform, Python
    version, and install args.
  - `uv sync` or equivalent plugin-only dependency installation.
- Keep install markers secret-free.
- Expose enough status for plugin start and model install UI to show dependency
  install progress/failure later.

Verification:

- Unit tests for marker freshness/staleness.
- Unit tests for generated uv args per plugin.

### Phase 4: Spawn Plugins From Their Own Venv

- Change `LocalPluginManager` / `PluginProcess` packaged mode so each plugin is
  spawned with its own venv Python.
- Keep dev mode behavior compatible with `uv run --directory`.
- Ensure `ensureFfmpeg()` and plugin env handling still work.

Verification:

- Unit tests for plugin process config/path selection.
- Mac packaged or local smoke where possible.
- Windows smoke with one lightweight plugin.

### Phase 5: YuNet + SFace Spike

- Add a focused Python spike for `dance_highlight` face detection/embedding
  using OpenCV YuNet + SFace.
- Use fixed sample frames/videos and reference images.
- Measure:
  - detection count/rate.
  - embedding similarity distribution.
  - clustering stability.
  - final highlight differences where possible.

Mac is the primary quality tuning environment.

Verification:

- Scripted sample run on Mac with saved summary metrics.
- Windows parity smoke with a small representative set.

### Phase 6: Replace InsightFace In Dance Highlight

- Remove `insightface` dependency from `dance_highlight`.
- Replace `FaceClusterService` implementation with YuNet/SFace adapter.
- Add model download/cache behavior for YuNet/SFace model files.
- Update thresholds and tests from spike results.

Verification:

- Python tests for face adapter on fixture images if available.
- Dance sample job on Mac.
- Dance sample job on Windows.
- Confirm no `insightface` install attempt in Windows logs.

### Phase 7: Packaged Installer Verification

Windows PC:

- Build/sign/upload can remain on runner PC when needed.
- On a normal Windows PC without MSVC Build Tools:
  - install app.
  - launch with fresh userData.
  - confirm main window opens.
  - start dance plugin.
  - confirm plugin venv installs without source build toolchain.
  - run sample dance job.

Mac:

- Run quality sample checks.
- Run packaged smoke when macOS release path becomes active.

## Release Work Resume Criteria

Return to `0.0.4` stable publish/update detection only after:

- Windows fresh install opens a window reliably.
- Plugin dependency failures no longer block startup.
- `dance_highlight` no longer depends on InsightFace model zoo assets.
- Windows dance plugin install/run has a passing smoke test.

## Open Follow-Ups

- UI copy may need to distinguish plugin dependency install from model/assets
  install.
- Face recognition usage needs product/privacy/legal review beyond open-source
  model license checks.
- Disk cleanup policy for plugin venvs is not part of the first implementation
  unless needed by tests.
