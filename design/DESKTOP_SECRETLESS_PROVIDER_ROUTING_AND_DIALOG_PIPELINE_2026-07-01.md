# Desktop Secretless Provider Routing And Dialog Pipeline

Date: 2026-07-01
Status: design draft for implementation planning

## Goal

Make the installed desktop app work without bundling external provider secrets.
All OpenAI and Naver provider credentials must live in `web/clipper_web_api`.
The desktop app may call `web_api` only through local `desktop/clipper_nestjs`
for workflow execution paths.

This work is about installed app correctness, not release/version management.

## Non-Goals

- Do not implement login, entitlement, subscription token, or permission checks in
  this pass. Those belong to the separate app-wide auth/permission track.
- Do not add direct Angular-to-web_api workflow execution calls.
- Do not keep direct provider fallback paths in desktop code.
- Do not support Kakao image search. Naver image search is the only media search
  provider in this design.
- Do not place `OPENAI_API_KEY`, Naver client secrets, or Kakao keys in
  `desktop/clipper_python/.env.packaged`, `desktop/clipper_nestjs/.env.packaged`,
  or the Electron packaged resources.

## Current Problems

### Packaged env still carries secret risk

`desktop/clipper_electron/electron-builder.yml` currently copies:

- `desktop/clipper_python/.env.packaged`
- `desktop/clipper_nestjs/.env.packaged`

`BundledEnvProvider` reads both files from app resources and userData override
paths, then injects the merged env into local NestJS and Python plugin
processes. This is acceptable only for non-secret runtime configuration.

### Dance image search still has fallback paths

`desktop/clipper_nestjs` already has a remote proxy path:

```text
Angular
  -> local clipper_nestjs /dance/members/images
  -> web_api /media/search
  -> Naver image search
```

However, local NestJS still has direct Naver/Kakao fallback code. The Python
dance plugin also still contains an older direct image search service. Those
paths are incompatible with secretless installed apps.

### Dialog Highlight still calls OpenAI from Python

`desktop/clipper_python/plugins/dialog_highlight/.../pipeline.py` creates an LLM
client and calls `client.chat.completions.create(...)` inside the pipeline.
That makes Python depend on OpenAI-compatible credentials or a proxy env.

The desired boundary is stricter:

```text
Angular
  -> local clipper_nestjs
  -> web/clipper_web_api
  -> external provider
```

Python should execute media processing stages only. Python should not call
`web_api`, OpenAI, Naver, or Kakao directly.

## Decisions

1. Local `desktop/clipper_nestjs` is the only desktop component that calls
   `web/clipper_web_api` for workflow provider operations.
2. `desktop/clipper_python` plugins do not call external provider APIs.
3. `dialog_highlight` becomes a staged pipeline. Python produces and consumes
   local structured artifacts; local NestJS performs LLM stages by calling
   `web_api`.
4. Dance member image search always uses `web_api /media/search`. There is no
   direct Naver/Kakao fallback in desktop code.
5. Kakao image search is removed from the active desktop/provider path.
6. Failure is explicit. If `web_api` is missing, misconfigured, unreachable, or
   returns a provider error, the job fails with a clear cause instead of falling
   back silently.

## Target Architecture

### Provider ownership

```text
web/clipper_web_api
  owns:
    - OPENAI_API_KEY
    - Naver image search keys
    - provider prompts/model selection for server-owned LLM stages
    - provider error normalization

desktop/clipper_nestjs
  owns:
    - local workflow orchestration
    - local project/job state
    - local file paths and artifacts
    - web_api client calls for provider-backed stages
    - user-facing error mapping for local UI

desktop/clipper_python
  owns:
    - media processing worker code
    - STT/OCR/scene/segment feature extraction
    - clip rendering
    - no provider secrets
    - no web_api calls
```

### Request path

```text
Angular UI
  -> local NestJS job/control endpoint
  -> Python media stage command
  -> local NestJS reads stage output artifact
  -> local NestJS calls web_api for LLM/Naver stage
  -> local NestJS writes next input artifact
  -> Python next media/render stage command
  -> local NestJS records project/result
  -> Angular shows progress/result
```

## Dialog Highlight Stage Split

The current Python pipeline has these LLM-dependent areas:

- sentence splitting from STT/shot text
- story backbone generation
- canonical/correction info generation
- event generation from timeline blocks
- highlight topic definition
- highlight selection from semantic candidates
- final highlight metadata/title generation

These become local NestJS orchestration steps.

### Python media stages

Python should expose deterministic stage commands through the plugin job API or
through a small internal stage runner. The implementation can choose the exact
transport, but the boundary is fixed:

```text
Stage A: prepare_media
  input:
    - source video path
    - output root
  output artifacts:
    - normalized input video metadata
    - downloaded/local source path when applicable

Stage B: analyze_media
  input:
    - prepared video path
  output artifacts:
    - shots
    - STT segments/words
    - OCR items
    - audio/visual feature summaries
    - semantic candidate inputs that do not require LLM

Stage C: build_candidates
  input:
    - LLM sentence split/canonical/story artifacts from local NestJS
    - media analysis artifacts
  output artifacts:
    - semantic segments
    - highlight candidates
    - render candidate metadata

Stage D: render_highlights
  input:
    - selected highlights and title/meta artifacts from local NestJS
    - media analysis artifacts
  output artifacts:
    - clips
    - thumbnails
    - final manifest
```

Python may include pure helper logic for aligning LLM results to timestamps, but
it must not build an OpenAI client or call remote provider endpoints.

### Local NestJS Dialog orchestrator

`desktop/clipper_nestjs` should own a `dialog-highlight` application service
that runs the full workflow:

```text
1. start Python Stage A/B
2. read `analysis/*.json`
3. call web_api LLM endpoint for sentence split
4. write `llm/sentences.json`
5. call Python Stage C
6. read candidate artifacts
7. call web_api LLM endpoint for story/canonical/topic/selection/title steps
8. write `llm/*.json`
9. call Python Stage D
10. record job/project result
```

The exact file names should be stable, versioned, and under the plugin job
output root. Artifacts must not contain provider keys.

### web_api LLM endpoints

`web/clipper_web_api` should expose domain-specific Dialog Highlight LLM
operations rather than a generic OpenAI proxy.

Recommended endpoint:

```text
POST /dialog-highlight/llm
```

Request shape:

```json
{
  "operation": "sentence_split",
  "locale": "ko-KR",
  "input": {}
}
```

Allowed operations for the first implementation:

- `sentence_split`
- `story_backbone`
- `canonical_info`
- `events_from_blocks`
- `define_highlight_topics`
- `select_highlights`
- `highlight_metadata`

`web_api` owns the prompt templates, model names, retry policy, and OpenAI API
key. Local NestJS sends structured inputs and receives structured JSON outputs.
This avoids installing a generic OpenAI proxy surface in desktop code and lets
prompt/model changes happen server-side.

## Dance Image Search

Target flow:

```text
Angular member image step
  -> local clipper_nestjs POST /dance/members/images
  -> local clipper_nestjs POST {WEB_API_MEDIA_SEARCH_URL}
  -> web_api Naver image search
```

Rules:

- No direct Naver search from `desktop/clipper_nestjs`.
- No direct Kakao search from `desktop/clipper_nestjs`.
- No direct image search from `desktop/clipper_python`.
- If web_api URL is missing, fail immediately with configuration error.
- If web_api is unreachable, fail with server connectivity error.
- If web_api has no active Naver key, fail with provider configuration error.
- If Naver returns an error through web_api, surface a provider error.

The existing direct providers should be removed or made unreachable in packaged
and local development modes. Local development must run local/remote `web_api`
instead of relying on direct desktop keys.

## Error Contract

No fallback means errors must be precise.

Desktop UI should distinguish at least:

- `web_api_not_configured`: local NestJS does not know the web_api base URL.
- `web_api_unreachable`: network/connectivity failure or timeout.
- `web_api_unauthorized`: auth/token failure reserved for the separate
  auth/permission track.
- `provider_not_configured`: web_api is up but missing OpenAI/Naver config.
- `provider_failed`: OpenAI/Naver returned a failed response.
- `pipeline_stage_failed`: Python media stage failed independently of provider.
- `artifact_contract_failed`: expected stage artifact was missing or invalid.

For the current no-auth phase, `web_api_unauthorized` can be treated as an
unexpected server error, but the name is reserved so the separate
auth/permission track does not change the UI vocabulary.

## Packaged App Secret Policy

`desktop/clipper_python/.env.packaged` and
`desktop/clipper_nestjs/.env.packaged` may contain non-secret config such as:

- web_api base URL
- provider proxy endpoint URLs
- local feature flags
- timeout values

They must not contain:

- `OPENAI_API_KEY`
- `NAVER_CLIENT_SECRET`
- `NAVER_CLIENT_ID` if paired with a secret for direct desktop use
- `KAKAO_REST_API_KEY`
- any bearer token intended to protect provider secrets

Build tooling must fail if forbidden key names are present in packaged env
files or copied resources.

## First-Run And Reset Verification

Installed app tests must support a true fresh-start reset.

### Windows reset

Run only after the app is fully closed:

```powershell
Stop-Process -Name Clipper2 -Force -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Clipper2" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface" -ErrorAction SilentlyContinue
```

This clears:

- local NestJS project/job data
- shortform project data
- dance reference/profile data
- Electron auth/cache files
- base Python venv
- plugin venvs
- plugin install markers
- downloaded ffmpeg/ffprobe
- dance model files under userData
- Hugging Face model cache used by dialog models

### macOS reset

Run only after the app is fully closed:

```bash
pkill -f Clipper2 || true
rm -rf "$HOME/Library/Application Support/Clipper2"
rm -rf "$HOME/.cache/huggingface"
```

### ffmpeg/ffprobe packaging fact

ffmpeg and ffprobe are not bundled as app resources today. In packaged mode they
are downloaded on demand into:

```text
userData/bin/ffmpeg(.exe)
userData/bin/ffprobe(.exe)
```

This remains acceptable if the UI asks for consent, shows progress, and fails
with a clear download/connectivity error.

## Implementation Order

1. Keep the already committed Angular app-completeness fixes.
2. Add web_api Dialog Highlight LLM operation endpoint and tests.
3. Add local NestJS web_api clients for media search and Dialog LLM operations.
4. Remove desktop direct Naver/Kakao fallback paths.
5. Split Python Dialog pipeline into media stages and remove direct OpenAI
   client creation/calls.
6. Move Dialog orchestration into local NestJS job flow.
7. Add forbidden packaged-env secret scans to Electron build tooling.
8. Normalize user-facing errors in Angular.
9. Run fresh-install reset verification on Windows and macOS.

## Open Implementation Questions

These are not product decisions; they are implementation details for the plan.

- Whether Python stages should be exposed as separate plugin job endpoints or a
  single stage runner command.
- Whether local NestJS should store intermediate artifacts under the existing
  project output root or a new `stages/` subdirectory.
- Whether `POST /dialog-highlight/llm` should stay one operation endpoint or be
  split into multiple routes after the first pass.

The non-negotiable boundary remains: Python does not call OpenAI, Naver, Kakao,
or web_api directly.
