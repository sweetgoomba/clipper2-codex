# Desktop Stdout and Control Event Contract

Date: 2026-07-02

## Decision

Desktop child-process stdout remains a log stream by default. The normal log record is the
desktop `v:1` JSON Lines schema documented in `.codex/AGENTS.md`.

There is one current exception: Python plugin startup may emit a small set of model-install
control events on stdout before the plugin HTTP runtime is fully useful. Electron main parses
those events and forwards them to Angular through the existing model-download IPC.

## Allowed stdout control events

Only these stdout control events are currently allowed from Python plugins:

```json
{"type":"model_loading","name":"Model display name","current":0,"total":2}
```

```json
{"type":"download_progress","model_name":"Model display name","pct":0.42}
```

Constraints:

- `current` is the zero-based model index currently loading.
- `total` is the number of model-loading steps.
- `pct` is a `0..1` byte-level download ratio for the current model.
- `model_name` may be omitted by parsers that can carry forward the latest `model_loading`
  model name, but new emitters should include it.

Parser and consumer locations:

- Python emitters:
  - `desktop/clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py`
  - plugin-specific bootstrap code such as Dance/Dialog model setup
- Electron parser:
  - `desktop/clipper_electron/src/main/plugin/plugin-process.ts`
- Electron IPC payloads:
  - `desktop/clipper_electron/src/shared/ipc-contract.ts`
  - `clipper:modelDownload:modelProgress`
  - `clipper:modelDownload:downloadProgress`
- Angular consumer:
  - `desktop/clipper_angular/src/core/resources/model-download.service.ts`

## What is not stdout

Normal job progress is not a stdout control event.

Python plugin `report_progress(job_id, progress, message)` sends WebSocket progress messages
through the plugin HTTP runtime. Queue status, render status, cancellation, and completed job
results should continue to use the job API, SSE/WebSocket, or the local NestJS orchestration
contracts rather than ad hoc stdout lines.

## Logging behavior

Actual log lines should use the desktop `v:1` JSON Lines schema. Electron main still wraps
non-`v:1` child stdout/stderr lines into valid log records before writing log files, so the
local diagnostic log files remain valid JSON Lines even when a permitted control event appears.

Do not add new stdout event shapes without documenting:

- the event schema;
- the parser location;
- the IPC or API consumer;
- the tests that cover the parser and UI expectation.

## Future direction

The preferred long-term shape is to separate plugin runtime events from logs completely. Until
that channel exists, keep stdout control events limited to startup/model-install bootstrap
events that must be observed before the plugin's normal HTTP progress channel is available.
