# Plugin Runtime Isolation And Dance Face Model Design

Date: 2026-07-01

## Context

Release/version-management work is paused until the packaged Windows app can
launch reliably on a normal user PC.

The `clipperstudio Setup 0.0.3.exe` installer was downloaded from the dev S3
artifact and installed on a clean Windows PC. `Clipper2.exe` stayed alive for
about 25 seconds with no window handle, then exited. Electron logs showed that
packaged first-run `uv sync` failed while installing
`clipper-plugin-dance-highlight` because `insightface==0.7.3` fell back to a
source build and required Microsoft Visual C++ Build Tools.

Current packaged startup is too tightly coupled to plugin dependencies:

```text
Clipper2.exe
  -> main.ts bootstrap
  -> await ensureVenv()
  -> uv sync --directory clipper_python
  -> plugin dependencies, including dance_highlight
  -> failure before openMainWindow()
```

Model files were already intended to download at plugin use time, but Python
package dependencies were still installed during app startup. That is the wrong
boundary for a plugin-based app.

## Goals

- The app window must not be blocked by optional plugin dependency installation.
- Packaged apps must use a small base runtime and a separate venv per plugin.
- A plugin install failure must affect only that plugin, not app startup or
  unrelated plugins.
- Windows users must not be asked to install MSVC Build Tools.
- `dance_highlight` must remain a Windows-supported plugin.
- `dance_highlight` must stop relying on InsightFace-provided pretrained models
  unless a commercial license is explicitly obtained.

## Non-Goals

- Do not continue `0.0.4` publish/update detection until app startup is fixed.
- Do not implement macOS release runner work as part of this change.
- Do not add release console UX work as part of this change.
- Do not ship InsightFace `buffalo_l` or auto-downloaded InsightFace model zoo
  models under the current public non-commercial pretrained model terms.

## Runtime Architecture

Packaged runtime state should be split by responsibility:

```text
userData/
  venvs/
    base/
    plugins/
      dialog_highlight/
      dance_highlight/
      clipper1_video_render/
  plugin-install/
    dialog_highlight.json
    dance_highlight.json
    clipper1_video_render.json
  models/
    ...
```

The base venv is only for app-level Python requirements needed before any
plugin runs. It must include Python and minimal shared tools such as `yt-dlp`
only if they are truly needed by app-level services.

Each plugin venv owns that plugin's Python dependencies. `PluginManager` should
ensure the plugin venv before spawning the plugin process. `PluginProcess`
should run with the Python executable from the plugin's venv, not the base venv.

Plugin model/assets installation remains separate from Python dependency
installation. A plugin can have:

- dependency install state: Python packages are ready.
- asset/model install state: model files are present or need download.
- runtime state: stopped, starting, running, error.

## Plugin Install Flow

On app startup:

```text
initElectronLog()
load packaged config
ensure base runtime only
create main window
start Nest/backend bridge as applicable
```

On plugin start:

```text
discover plugin manifest
resolve plugin venv path
if venv missing or stale:
  run uv sync/install for that plugin only
  write install marker with plugin version, lock hash, platform, python version
verify required plugin packages import
spawn plugin using plugin venv python
stream model download/loading progress as today
```

The install marker must not contain secrets.

## Dance Face Model Direction

`insightface` has two separate issues:

- Packaging: PyPI `insightface 0.7.3` has no Windows wheel, so a normal Windows
  PC falls back to source build and fails without MSVC Build Tools.
- Licensing: InsightFace code is MIT, but the provided pretrained models,
  including auto-downloaded model zoo assets such as `buffalo_l`, are publicly
  documented for non-commercial research use unless a separate commercial
  license is obtained.

The preferred replacement path is OpenCV YuNet + SFace:

- YuNet: face detection and landmarks.
- SFace: face embedding/recognition.
- Model licenses are permissive in the checked public model cards/repo:
  YuNet MIT, SFace Apache-2.0.

Implementation should replace `FaceClusterService`'s InsightFace backend with
an adapter that uses YuNet for detection and SFace for embeddings. Existing
clustering logic can remain if embedding shape/normalization thresholds are
retuned with sample videos.

## Quality And Platform Verification

Primary quality tuning can happen on Mac:

- use representative dance videos and reference images.
- measure face detection rate per sampled frame.
- compare clustering and final highlight output against current expected
  behavior.
- tune thresholds on Mac using fixed model files and fixed input assets.

Windows still needs parity and packaged runtime verification:

- install dependencies without MSVC Build Tools.
- run the same representative samples and compare detection counts/clustering
  shape against Mac output.
- verify packaged installer fresh launch, plugin venv creation, model load, and
  plugin job execution.

Mac quality success does not remove the need for Windows parity checks because
OpenCV/ONNXRuntime wheels, video decoding, path handling, and packaged resource
paths can differ.

## Risks

- YuNet/SFace quality may differ from InsightFace `buffalo_l`, especially on
  small faces, motion blur, side profiles, and threshold-near embeddings.
- Plugin-specific venvs increase disk usage and install flow complexity.
- Existing UI install-state language currently mixes model/assets state with
  plugin readiness; it may need a follow-up copy/state cleanup.
- Commercial use of face recognition also has biometric/privacy implications
  outside package/model license terms.

## Decision

Proceed with plugin-specific venvs from the start rather than a shared venv
intermediate step. Use OpenCV YuNet + SFace as the first commercial-friendly
replacement path for dance face detection/recognition. Keep release-platform
publish/update work paused until packaged app startup and Windows dance plugin
runtime are verified.
