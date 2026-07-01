# Desktop Secretless Provider Routing And Dialog Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the installed desktop app run provider-backed Dance and Dialog Highlight workflows without bundling OpenAI/Naver/Kakao secrets and without direct desktop provider fallback paths.

**Architecture:** Desktop workflow execution goes through Angular -> local `desktop/clipper_nestjs` -> `web/clipper_web_api` -> external providers. Python plugins become media workers only: they produce/read local stage artifacts and never call `web_api`, OpenAI, Naver, or Kakao. Dialog Highlight is converted from a monolithic Python/OpenAI pipeline into local NestJS orchestration plus Python media stages.

**Tech Stack:** NestJS 11 (`web/clipper_web_api`), NestJS 11 + node:test (`desktop/clipper_nestjs`), Electron main process TypeScript (`desktop/clipper_electron`), Python 3.11 uv workspace (`desktop/clipper_python`), Angular 19 (`desktop/clipper_angular`) for user-facing error/UX follow-up.

---

## Source Spec

Read first:

- `.codex/design/DESKTOP_SECRETLESS_PROVIDER_ROUTING_AND_DIALOG_PIPELINE_2026-07-01.md`
- `.codex/design/DESKTOP_WEB_API_ENTITLEMENT_AND_PROXY_WORKING_NOTES_2026-06-26.md`
- `.codex/design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md`
- `.codex/AGENTS.md`

Non-negotiable constraints:

- No release/version-management work in this plan.
- No desktop-bundled provider secrets.
- No direct Python calls to `web_api`, OpenAI, Naver, or Kakao.
- No direct Naver/Kakao provider path in desktop workflow code.
- Kakao is removed from the active image-search path.
- Auth/token/entitlement work is intentionally excluded and belongs to the separate app-wide auth/permission track.

## Repo Work Map

### `web/clipper_web_api`

Owns external provider credentials and provider calls.

Create:

- `src/modules/dialog-highlight/dialog-highlight.module.ts`
- `src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts`
- `src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts`
- `src/modules/dialog-highlight/presentation/dialog-highlight-llm.controller.ts`
- `src/modules/dialog-highlight/presentation/dto/dialog-highlight-llm.dto.ts`

Modify:

- `src/app.module.ts`

### `desktop/clipper_nestjs`

Owns local workflow orchestration, web_api calls, stage artifact IO, and user-facing job errors.

Create:

- `src/core/web-api/web-api-client.service.ts`
- `src/core/web-api/web-api-client.service.spec.ts`
- `src/modules/dance/infrastructure/services/web-api-member-image-source.ts`
- `src/modules/dialog-highlight/dialog-highlight.module.ts`
- `src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts`
- `src/modules/dialog-highlight/application/dialog-highlight-web-api.client.ts`
- `src/modules/dialog-highlight/application/dialog-highlight-artifacts.ts`
- `test/dance-web-api-member-image-source.test.js`
- `test/dialog-highlight-web-api-client.test.js`
- `test/dialog-highlight-workflow-executor.test.js`

Modify:

- `src/app.module.ts`
- `src/modules/dance/dance.module.ts`
- `src/modules/dance/infrastructure/services/member-image-source-selector.ts`
- `src/modules/dance/infrastructure/services/image-search.service.ts`
- `src/modules/workflows/application/workflow-executor-registry.service.ts`
- `src/modules/plugins/plugins.module.ts`

Delete after replacement tests pass:

- `src/modules/dance/infrastructure/services/naver-direct-image-source.ts`
- `src/modules/dance/infrastructure/services/fallback-image-source.ts`
- `test/dance-naver-direct-image-source.test.js`
- `test/dance-fallback-image-source.test.js`

### `desktop/clipper_python`

Owns media stages and local artifacts.

Create:

- `plugins/dialog_highlight/dialog_highlight/services/stage_contracts.py`
- `plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
- `tests/test_dialog_stage_contracts.py`
- `tests/test_dialog_no_external_provider_calls.py`

Modify:

- `plugins/dialog_highlight/dialog_highlight/app.py`
- `plugins/dialog_highlight/dialog_highlight/services/pipeline.py`

Delete after all Dialog stage tests pass:

- `plugins/dialog_highlight/dialog_highlight/services/llm_client.py`

### `desktop/clipper_electron`

Owns packaged resource guardrails.

Create:

- `scripts/assert-no-packaged-secrets.mjs`
- `test/packaged-secret-scan.test.js`

Modify:

- `scripts/build-app.mjs`

### `desktop/clipper_angular`

Owns user-facing error display after backend error codes exist.

Modify later in this plan:

- `src/core/errors/error-catalog.ts`
- `src/shared/ui/app-error-banner/app-error-banner.component.*` if current catalog mapping is insufficient
- Dialog/Dance setup specs that assert displayed error messages

## Error Codes

Use these exact machine codes across local NestJS and Angular:

- `web_api_not_configured`
- `web_api_unreachable`
- `web_api_unauthorized`
- `provider_not_configured`
- `provider_failed`
- `pipeline_stage_failed`
- `artifact_contract_failed`

For the no-auth phase, `web_api_unauthorized` can be mapped as a server error. Keep the code stable for the separate auth/permission track.

---

## Task 1: Add web_api Dialog Highlight LLM Endpoint

**Files:**

- Create: `web/clipper_web_api/src/modules/dialog-highlight/dialog-highlight.module.ts`
- Create: `web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts`
- Create: `web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts`
- Create: `web/clipper_web_api/src/modules/dialog-highlight/presentation/dialog-highlight-llm.controller.ts`
- Create: `web/clipper_web_api/src/modules/dialog-highlight/presentation/dto/dialog-highlight-llm.dto.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`

- [ ] **Step 1: Write the DTO and service failing tests**

Create `src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts`.

Use this test shape:

```ts
import { ServiceUnavailableException, BadGatewayException } from '@nestjs/common';
import { DialogHighlightLlmService } from './dialog-highlight-llm.service.js';

function config(values: Record<string, string | undefined>) {
  return { get: (key: string) => values[key] } as any;
}

describe('DialogHighlightLlmService', () => {
  const originalFetch = global.fetch;
  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('fails when OPENAI_API_KEY is not configured', async () => {
    const svc = new DialogHighlightLlmService(config({ OPENAI_API_KEY: undefined }));
    await expect(svc.run({
      operation: 'sentence_split',
      locale: 'ko-KR',
      input: { shotTexts: [{ shotId: 1, start: 0, end: 3, text: '안녕하세요 반갑습니다' }] },
    })).rejects.toBeInstanceOf(ServiceUnavailableException);
  });

  it('calls OpenAI responses API and parses JSON output', async () => {
    global.fetch = jest.fn(async () => ({
      ok: true,
      json: async () => ({ output_text: JSON.stringify({ shots: [{ shot_id: 1, sentences: [{ text: '안녕하세요.' }] }] }) }),
    })) as any;

    const svc = new DialogHighlightLlmService(config({
      OPENAI_API_KEY: 'test-key',
      DIALOG_HIGHLIGHT_OPENAI_MODEL: 'gpt-4.1-mini',
      DIALOG_HIGHLIGHT_OPENAI_BASE_URL: 'https://api.openai.com/v1/responses',
    }));

    await expect(svc.run({
      operation: 'sentence_split',
      locale: 'ko-KR',
      input: { shotTexts: [{ shotId: 1, start: 0, end: 3, text: '안녕하세요 반갑습니다' }] },
    })).resolves.toEqual({ shots: [{ shot_id: 1, sentences: [{ text: '안녕하세요.' }] }] });
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('maps OpenAI HTTP failure to BadGatewayException', async () => {
    global.fetch = jest.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })) as any;
    const svc = new DialogHighlightLlmService(config({ OPENAI_API_KEY: 'test-key' }));

    await expect(svc.run({
      operation: 'select_highlights',
      locale: 'ko-KR',
      input: { candidates: [] },
    })).rejects.toBeInstanceOf(BadGatewayException);
  });
});
```

- [ ] **Step 2: Run the focused failing test**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- dialog-highlight-llm.service.spec.ts --runInBand
```

Expected: FAIL because `dialog-highlight-llm.service.ts` does not exist.

- [ ] **Step 3: Add DTO**

Create `src/modules/dialog-highlight/presentation/dto/dialog-highlight-llm.dto.ts`.

```ts
import { IsIn, IsObject, IsOptional, IsString } from 'class-validator';

export const DIALOG_HIGHLIGHT_LLM_OPERATIONS = [
  'sentence_split',
  'story_backbone',
  'canonical_info',
  'events_from_blocks',
  'define_highlight_topics',
  'select_highlights',
  'highlight_metadata',
] as const;

export type DialogHighlightLlmOperation = typeof DIALOG_HIGHLIGHT_LLM_OPERATIONS[number];

export class DialogHighlightLlmRequestDto {
  @IsIn(DIALOG_HIGHLIGHT_LLM_OPERATIONS)
  operation!: DialogHighlightLlmOperation;

  @IsOptional()
  @IsString()
  locale?: string;

  @IsObject()
  input!: Record<string, unknown>;
}
```

- [ ] **Step 4: Add service**

Create `src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts`.

The service must:

- read `OPENAI_API_KEY` from `ConfigService`.
- use `DIALOG_HIGHLIGHT_OPENAI_MODEL` with default `gpt-4.1-mini`.
- use `DIALOG_HIGHLIGHT_OPENAI_HIGH_MODEL` with default `gpt-4.1`.
- use `DIALOG_HIGHLIGHT_OPENAI_BASE_URL` with default `https://api.openai.com/v1/responses`.
- use `DIALOG_HIGHLIGHT_TIMEOUT_MS` with default `90000`.
- build operation-specific prompts copied from the current Python functions in `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline.py`.
- call OpenAI Responses API, not Chat Completions.
- return raw parsed JSON object.
- throw `ServiceUnavailableException('provider_not_configured: OPENAI_API_KEY is not configured')` when missing.
- throw `BadGatewayException('provider_failed: ...')` on OpenAI request/parse failures.

Use helper methods with these names:

```ts
private modelFor(operation: DialogHighlightLlmOperation): string
private promptFor(operation: DialogHighlightLlmOperation, input: Record<string, unknown>): string
private extractJsonText(payload: unknown): string | null
private parseJsonText(text: string): Record<string, unknown>
private message(e: unknown): string
```

Prompt source mapping:

- `sentence_split`: copy intent/schema from Python `llm_split_sentences_all_shots`.
- `story_backbone`: copy intent/schema from Python `build_story_backbone_gpt`.
- `canonical_info`: copy intent/schema from Python `build_canonical_info_gpt`.
- `events_from_blocks`: copy intent/schema from Python `build_events_from_blocks_gpt`.
- `define_highlight_topics`: copy intent/schema from Python `gpt_define_highlight_topics`.
- `select_highlights`: copy intent/schema from Python `call_gpt_select_highlights`.
- `highlight_metadata`: copy intent/schema from Python `build_highlights_meta_gpt`.

- [ ] **Step 5: Add controller and module**

Create `src/modules/dialog-highlight/presentation/dialog-highlight-llm.controller.ts`.

```ts
import { Body, Controller, Post, UsePipes, ValidationPipe } from '@nestjs/common';
import { DialogHighlightLlmService } from '../application/dialog-highlight-llm.service.js';
import { DialogHighlightLlmRequestDto } from './dto/dialog-highlight-llm.dto.js';

@Controller('dialog-highlight')
export class DialogHighlightLlmController {
  constructor(private readonly llm: DialogHighlightLlmService) {}

  @Post('llm')
  @UsePipes(new ValidationPipe({ whitelist: true, transform: true }))
  run(@Body() dto: DialogHighlightLlmRequestDto): Promise<Record<string, unknown>> {
    return this.llm.run({
      operation: dto.operation,
      locale: dto.locale ?? 'ko-KR',
      input: dto.input,
    });
  }
}
```

Create `src/modules/dialog-highlight/dialog-highlight.module.ts`.

```ts
import { Module } from '@nestjs/common';
import { DialogHighlightLlmService } from './application/dialog-highlight-llm.service.js';
import { DialogHighlightLlmController } from './presentation/dialog-highlight-llm.controller.js';

@Module({
  controllers: [DialogHighlightLlmController],
  providers: [DialogHighlightLlmService],
})
export class DialogHighlightModule {}
```

Modify `src/app.module.ts` to import and include `DialogHighlightModule`.

- [ ] **Step 6: Verify web_api endpoint**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- dialog-highlight-llm.service.spec.ts --runInBand
npm run build
```

Expected: both exit 0.

- [ ] **Step 7: Commit web_api LLM endpoint**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
git add src/modules/dialog-highlight src/app.module.ts
git commit -m "feat: add dialog highlight llm endpoint"
```

---

## Task 2: Add Local NestJS web_api Client And Error Mapping

**Files:**

- Create: `desktop/clipper_nestjs/src/core/web-api/web-api-client.service.ts`
- Create: `desktop/clipper_nestjs/test/web-api-client.test.js`
- Modify later consumers to use this client.

- [ ] **Step 1: Write failing client tests**

Create `test/web-api-client.test.js`.

Test cases:

```js
const assert = require('node:assert/strict');
const test = require('node:test');
const { WebApiClient, WebApiNotConfiguredError, WebApiUnreachableError, WebApiProviderError } = require('../dist/core/web-api/web-api-client.service.js');

function cfg(values) {
  return { get: (key) => values[key] };
}

test('web api client fails when base url is missing', async () => {
  const client = new WebApiClient(cfg({}));
  await assert.rejects(
    () => client.postJson('/media/search', { keyword: 'IVE Wonyoung', limit: 5 }),
    WebApiNotConfiguredError,
  );
});

test('web api client posts JSON to configured base url', async () => {
  const seen = [];
  global.fetch = async (url, init) => {
    seen.push({ url, init });
    return { ok: true, json: async () => ({ ok: true }) };
  };
  const client = new WebApiClient(cfg({ CLIPPER_WEB_API_BASE_URL: 'http://127.0.0.1:39000' }));
  const result = await client.postJson('/media/search', { keyword: 'IVE Wonyoung', limit: 5 });
  assert.deepEqual(result, { ok: true });
  assert.equal(seen[0].url, 'http://127.0.0.1:39000/media/search');
});

test('web api client maps non-2xx to provider error', async () => {
  global.fetch = async () => ({ ok: false, status: 503, text: async () => 'provider_not_configured' });
  const client = new WebApiClient(cfg({ CLIPPER_WEB_API_BASE_URL: 'http://127.0.0.1:39000' }));
  await assert.rejects(
    () => client.postJson('/dialog-highlight/llm', { operation: 'sentence_split', input: {} }),
    WebApiProviderError,
  );
});

test('web api client maps fetch throw to unreachable', async () => {
  global.fetch = async () => { throw new Error('ECONNREFUSED'); };
  const client = new WebApiClient(cfg({ CLIPPER_WEB_API_BASE_URL: 'http://127.0.0.1:39000' }));
  await assert.rejects(
    () => client.postJson('/media/search', { keyword: 'IVE Wonyoung', limit: 5 }),
    WebApiUnreachableError,
  );
});
```

- [ ] **Step 2: Run failing test**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/web-api-client.test.js
```

Expected: FAIL because `dist/core/web-api/web-api-client.service.js` is missing.

- [ ] **Step 3: Implement client**

Create `src/core/web-api/web-api-client.service.ts`.

Required exports:

```ts
export class WebApiNotConfiguredError extends Error {
  readonly code = 'web_api_not_configured';
}
export class WebApiUnreachableError extends Error {
  readonly code = 'web_api_unreachable';
}
export class WebApiProviderError extends Error {
  readonly code = 'provider_failed';
  constructor(message: string, readonly status?: number) { super(message); }
}
export class WebApiClient {
  constructor(private readonly config: ConfigService) {}
  async postJson<T>(path: string, body: Record<string, unknown>): Promise<T> { ... }
}
```

Implementation rules:

- Base URL env key: `CLIPPER_WEB_API_BASE_URL`.
- Trim trailing slash from base URL.
- Request timeout env key: `CLIPPER_WEB_API_TIMEOUT_MS`, default `30000`.
- Always send `Accept: application/json` and `Content-Type: application/json`.
- Do not send auth headers in this pass.
- Do not print request bodies if they may contain user content.

- [ ] **Step 4: Verify client**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/web-api-client.test.js
```

Expected: exit 0.

- [ ] **Step 5: Commit client**

```bash
git add src/core/web-api/web-api-client.service.ts test/web-api-client.test.js
git commit -m "feat: add desktop web api client"
```

---

## Task 3: Route Dance Image Search Only Through web_api

**Files:**

- Create: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/web-api-member-image-source.ts`
- Create: `desktop/clipper_nestjs/test/dance-web-api-member-image-source.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/dance/dance.module.ts`
- Modify: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/member-image-source-selector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/image-search.service.ts`
- Delete: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/naver-direct-image-source.ts`
- Delete: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/fallback-image-source.ts`
- Delete or replace tests: `desktop/clipper_nestjs/test/dance-naver-direct-image-source.test.js`, `desktop/clipper_nestjs/test/dance-fallback-image-source.test.js`

- [ ] **Step 1: Write failing source test**

Create `test/dance-web-api-member-image-source.test.js`.

Expected behavior:

- calls `WebApiClient.postJson('/media/search', { keyword, limit, page })`.
- maps returned `candidates[].contentUrl` to `RawImageHit.imageUrl`.
- sets `provider` to `web_api`.
- does not accept direct Naver/Kakao env.

- [ ] **Step 2: Run failing dance tests**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/dance-web-api-member-image-source.test.js
```

Expected: FAIL because `web-api-member-image-source` does not exist.

- [ ] **Step 3: Implement web_api source**

Create `src/modules/dance/infrastructure/services/web-api-member-image-source.ts`.

The class must implement `MemberImageSearchSource` and use `WebApiClient`.

Mapping:

```ts
contentUrl | content_url | imageUrl | image_url | url | link -> imageUrl
thumbnailUrl is ignored by the current dance DTO unless the DTO is expanded in this same task
width, height pass through when numeric
source = 'naver'
provider = 'web_api'
```

- [ ] **Step 4: Remove selector fallback**

Modify `src/modules/dance/infrastructure/services/member-image-source-selector.ts`.

Target behavior:

```ts
@Injectable()
export class MemberImageSourceSelector {
  constructor(private readonly webApi: WebApiMemberImageSource) {}

  pick(): MemberImageSearchSource {
    return this.webApi;
  }
}
```

- [ ] **Step 5: Update module providers**

Modify `src/modules/dance/dance.module.ts`.

Remove providers:

- `NaverDirectImageSource`
- `RemoteProxyImageSource`
- `FallbackImageSource`

Add providers:

- `WebApiClient`
- `WebApiMemberImageSource`

Keep:

- `MemberImageSourceSelector`
- `ImageSearchService`

- [ ] **Step 6: Delete direct provider files and tests**

Delete:

```bash
git rm src/modules/dance/infrastructure/services/naver-direct-image-source.ts
git rm src/modules/dance/infrastructure/services/fallback-image-source.ts
git rm test/dance-naver-direct-image-source.test.js
git rm test/dance-fallback-image-source.test.js
```

Keep `remote-proxy-image-source.ts` only if shortform still imports it. If no import remains after `rg "RemoteProxyImageSource|remote-proxy-image-source"`, delete it in the same commit.

- [ ] **Step 7: Verify dance image routing**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/web-api-client.test.js test/dance-web-api-member-image-source.test.js test/dance-image-search-service.test.js test/dance-controller-member-images.test.js
rg "NAVER_CLIENT_ID|NAVER_CLIENT_SECRET|KAKAO_REST_API_KEY|NaverDirectImageSource|FallbackImageSource" src/modules/dance test
```

Expected:

- build exits 0.
- node tests exit 0.
- `rg` returns no active direct provider source references except historical docs or removed-test references. If `rg` finds active code, remove it before commit.

- [ ] **Step 8: Commit dance routing**

```bash
git add src/modules/dance test
git commit -m "refactor: route dance image search through web api"
```

---

## Task 4: Add Electron Packaged Secret Scan

**Files:**

- Create: `desktop/clipper_electron/scripts/assert-no-packaged-secrets.mjs`
- Create: `desktop/clipper_electron/test/packaged-secret-scan.test.js`
- Modify: `desktop/clipper_electron/scripts/build-app.mjs`

- [ ] **Step 1: Write failing scan test**

Create `test/packaged-secret-scan.test.js`.

Test these cases:

- file containing `OPENAI_API_KEY=` fails.
- file containing `NAVER_CLIENT_SECRET=` fails.
- file containing `KAKAO_REST_API_KEY=` fails.
- file containing `CLIPPER_WEB_API_BASE_URL=` passes.
- error output must include key names but not values.

- [ ] **Step 2: Run failing test**

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
npm test -- test/packaged-secret-scan.test.js
```

Expected: FAIL because script does not exist.

- [ ] **Step 3: Implement scanner**

Create `scripts/assert-no-packaged-secrets.mjs`.

Forbidden keys:

```js
const FORBIDDEN_KEYS = [
  'OPENAI_API_KEY',
  'CLIPPER1_LLM_SCRIPT_OPENAI_API_KEY',
  'NAVER_CLIENT_SECRET',
  'NAVER_CLIENT_ID',
  'KAKAO_REST_API_KEY',
  'NAVER_CLOVA_CLIENT_SECRET',
  'CLIPPER_STUDIO_MEDIA_SEARCH_API_KEY',
  'CLIPPER1_MEDIA_SEARCH_API_KEY',
];
```

The scanner must inspect:

- `../clipper_python/.env.packaged`
- `../clipper_nestjs/.env.packaged`

It must print only file path and forbidden key name.

- [ ] **Step 4: Wire scanner into build**

Modify `scripts/build-app.mjs` after packaged env existence checks and before asset copying/building:

```js
await import('./assert-no-packaged-secrets.mjs');
```

If direct import side effects are too opaque, export `assertNoPackagedSecrets()` and call it explicitly.

- [ ] **Step 5: Verify Electron scanner**

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
npm test -- test/packaged-secret-scan.test.js
npm run build
```

Expected: both exit 0 when packaged env files do not contain forbidden key names. If local `.env.packaged` currently contains forbidden keys, do not print values; remove/move those keys before rerunning.

- [ ] **Step 6: Commit scanner**

```bash
git add scripts/assert-no-packaged-secrets.mjs scripts/build-app.mjs test/packaged-secret-scan.test.js
git commit -m "build: reject packaged provider secrets"
```

---

## Task 5: Add Python Dialog Stage Contracts And External-Call Guard

**Files:**

- Create: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_contracts.py`
- Create: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
- Create: `desktop/clipper_python/tests/test_dialog_stage_contracts.py`
- Create: `desktop/clipper_python/tests/test_dialog_no_external_provider_calls.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/app.py`

- [ ] **Step 1: Write stage contract tests**

Create `tests/test_dialog_stage_contracts.py`.

Assert:

- valid stage names are exactly `prepare_media`, `analyze_media`, `build_candidates`, `render_highlights`.
- each stage request has `stage`, `video_path`, `output_root`.
- `stage_contracts.stage_paths(output_root)` returns paths under `output_root/json`.
- stage result JSON is serializable.

- [ ] **Step 2: Write no external provider guard test**

Create `tests/test_dialog_no_external_provider_calls.py`.

Test rules:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "plugins" / "dialog_highlight" / "dialog_highlight"

def test_dialog_python_does_not_import_openai_or_read_provider_env():
    forbidden = [
        "from openai import",
        "OpenAI(",
        "OPENAI_API_KEY",
        "CLIPPER_LLM_PROXY_URL",
        "CLIPPER_SUBSCRIPTION_TOKEN",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "KAKAO_REST_API_KEY",
    ]
    offenders = []
    for path in DIALOG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{path.relative_to(ROOT)}:{needle}")
    assert offenders == []
```

This test must fail before removing `llm_client.py` and OpenAI references from `pipeline.py`.

- [ ] **Step 3: Run failing Python tests**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_stage_contracts.py tests/test_dialog_no_external_provider_calls.py -q
```

Expected: FAIL because stage contracts do not exist and OpenAI references still exist.

- [ ] **Step 4: Implement stage contracts**

Create `stage_contracts.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DialogStageName = Literal["prepare_media", "analyze_media", "build_candidates", "render_highlights"]
VALID_DIALOG_STAGES: tuple[str, ...] = ("prepare_media", "analyze_media", "build_candidates", "render_highlights")

@dataclass(frozen=True)
class DialogStageRequest:
    stage: DialogStageName
    video_path: Path
    output_root: Path
    device: str = "cpu"

def stage_paths(output_root: Path) -> dict[str, Path]:
    json_dir = output_root / "json"
    return {
        "analysis": json_dir / "analysis.json",
        "llm_sentences": json_dir / "llm_sentences.json",
        "story_backbone": json_dir / "story_backbone.json",
        "canonical_info": json_dir / "canonical_info.json",
        "highlight_topics": json_dir / "highlight_topics.json",
        "highlight_selection": json_dir / "gpt_highlight_selection.json",
        "highlight_metadata": json_dir / "highlights_meta.json",
        "manifest": json_dir / "manifest.json",
    }
```

- [ ] **Step 5: Implement stage runner shell**

Create `stage_runner.py` with:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .stage_contracts import DialogStageRequest

ProgressCb = Callable[[int, str], None] | None

def run_dialog_stage(request: DialogStageRequest, progress_cb: ProgressCb = None) -> dict[str, Any]:
    if request.stage == "prepare_media":
        return run_prepare_media(request, progress_cb)
    if request.stage == "analyze_media":
        return run_analyze_media(request, progress_cb)
    if request.stage == "build_candidates":
        return run_build_candidates(request, progress_cb)
    if request.stage == "render_highlights":
        return run_render_highlights(request, progress_cb)
    raise ValueError(f"unknown dialog stage: {request.stage}")

def run_prepare_media(request: DialogStageRequest, progress_cb: ProgressCb = None) -> dict[str, Any]:
    request.output_root.mkdir(parents=True, exist_ok=True)
    (request.output_root / "json").mkdir(parents=True, exist_ok=True)
    if progress_cb:
      progress_cb(10, "영상 준비 완료")
    return {"stage": "prepare_media", "output_root": str(request.output_root)}

def run_analyze_media(request: DialogStageRequest, progress_cb: ProgressCb = None) -> dict[str, Any]:
    raise NotImplementedError("analyze_media stage extraction is implemented in Task 6")

def run_build_candidates(request: DialogStageRequest, progress_cb: ProgressCb = None) -> dict[str, Any]:
    raise NotImplementedError("build_candidates stage extraction is implemented in Task 7")

def run_render_highlights(request: DialogStageRequest, progress_cb: ProgressCb = None) -> dict[str, Any]:
    raise NotImplementedError("render_highlights stage extraction is implemented in Task 8")
```

- [ ] **Step 6: Add stage dispatch in `app.py`**

Modify `DialogHighlightPlugin.run_job` to accept `params.stage`.

Rules:

- If `params.stage` is present, call `run_dialog_stage`.
- If `params.stage` is absent, keep legacy `run_pipeline_for_video` temporarily until Task 9 switches executor. This temporary legacy path is removed in Task 10.

- [ ] **Step 7: Verify stage shell**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_stage_contracts.py -q
```

Expected: exit 0.

`test_dialog_no_external_provider_calls.py` is expected to keep failing until Task 10 removes OpenAI references.

- [ ] **Step 8: Commit stage shell**

```bash
git add plugins/dialog_highlight/dialog_highlight/services/stage_contracts.py plugins/dialog_highlight/dialog_highlight/services/stage_runner.py plugins/dialog_highlight/dialog_highlight/app.py tests/test_dialog_stage_contracts.py tests/test_dialog_no_external_provider_calls.py
git commit -m "feat: add dialog highlight stage contracts"
```

---

## Task 6: Extract Dialog `prepare_media` And `analyze_media` Python Stages

**Files:**

- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
- Create: `desktop/clipper_python/tests/test_dialog_analyze_stage.py`

- [ ] **Step 1: Write analyze stage artifact test**

Create `tests/test_dialog_analyze_stage.py`.

Use a tiny synthetic/local fixture if available in existing tests. If no video fixture exists, test the artifact contract with monkeypatched pipeline helpers so the test does not download models.

Assert that `run_analyze_media` writes:

- `json/analysis.json`
- keys: `shots`, `stt_segments`, `stt_words`, `ocr_items`, `duration_sec`

- [ ] **Step 2: Run failing test**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_analyze_stage.py -q
```

Expected: FAIL because `run_analyze_media` still raises `NotImplementedError`.

- [ ] **Step 3: Extract media analysis code**

In `pipeline.py`, introduce:

```python
def analyze_video_to_artifacts(
    input_video: Path,
    output_root: Path,
    device: str = "cpu",
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict[str, Any]:
    ...
```

Move the existing non-LLM work from the beginning of `run_pipeline_for_video` through STT/OCR/shot/audio feature generation into this function. It must not call `create_openai_client`, `llm_split_sentences_*`, or any `call_gpt_*` function.

Write `json/analysis.json` containing the data local NestJS needs for LLM steps.

- [ ] **Step 4: Connect stage runner**

Modify `run_analyze_media` in `stage_runner.py` to call `analyze_video_to_artifacts`.

- [ ] **Step 5: Verify analyze stage**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_analyze_stage.py -q
```

Expected: exit 0.

- [ ] **Step 6: Commit analyze stage**

```bash
git add plugins/dialog_highlight/dialog_highlight/services/pipeline.py plugins/dialog_highlight/dialog_highlight/services/stage_runner.py tests/test_dialog_analyze_stage.py
git commit -m "refactor: extract dialog media analysis stage"
```

---

## Task 7: Add Local NestJS Dialog LLM Client And Artifact Helpers

**Files:**

- Create: `desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-web-api.client.ts`
- Create: `desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-artifacts.ts`
- Create: `desktop/clipper_nestjs/test/dialog-highlight-web-api-client.test.js`

- [ ] **Step 1: Write client tests**

Create `test/dialog-highlight-web-api-client.test.js`.

Assert:

- `splitSentences(input)` posts to `/dialog-highlight/llm` with `operation: "sentence_split"`.
- `selectHighlights(input)` posts with `operation: "select_highlights"`.
- errors from `WebApiClient` propagate with code fields intact.

- [ ] **Step 2: Implement `DialogHighlightWebApiClient`**

Create `dialog-highlight-web-api.client.ts`.

Required methods:

```ts
splitSentences(input: Record<string, unknown>): Promise<Record<string, unknown>>
storyBackbone(input: Record<string, unknown>): Promise<Record<string, unknown>>
canonicalInfo(input: Record<string, unknown>): Promise<Record<string, unknown>>
eventsFromBlocks(input: Record<string, unknown>): Promise<Record<string, unknown>>
defineHighlightTopics(input: Record<string, unknown>): Promise<Record<string, unknown>>
selectHighlights(input: Record<string, unknown>): Promise<Record<string, unknown>>
highlightMetadata(input: Record<string, unknown>): Promise<Record<string, unknown>>
```

All methods call `WebApiClient.postJson('/dialog-highlight/llm', { operation, locale: 'ko-KR', input })`.

- [ ] **Step 3: Implement artifact helpers**

Create `dialog-highlight-artifacts.ts`.

Export:

```ts
export interface DialogArtifactPaths {
  analysis: string;
  llmSentences: string;
  storyBackbone: string;
  canonicalInfo: string;
  highlightTopics: string;
  highlightSelection: string;
  highlightMetadata: string;
  manifest: string;
}

export function dialogArtifactPaths(outputRoot: string): DialogArtifactPaths;
export function readJsonFile<T>(path: string): T;
export function writeJsonFile(path: string, value: unknown): void;
```

All paths live under `${outputRoot}/json`.

- [ ] **Step 4: Verify local Dialog client**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/dialog-highlight-web-api-client.test.js
```

Expected: exit 0.

- [ ] **Step 5: Commit Dialog client**

```bash
git add src/modules/dialog-highlight/application/dialog-highlight-web-api.client.ts src/modules/dialog-highlight/application/dialog-highlight-artifacts.ts test/dialog-highlight-web-api-client.test.js
git commit -m "feat: add dialog highlight web api client"
```

---

## Task 8: Add Local NestJS Dialog Workflow Executor

**Files:**

- Create: `desktop/clipper_nestjs/src/modules/dialog-highlight/dialog-highlight.module.ts`
- Create: `desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-workflow.executor.ts`
- Create: `desktop/clipper_nestjs/test/dialog-highlight-workflow-executor.test.js`
- Modify: `desktop/clipper_nestjs/src/app.module.ts`
- Modify: `desktop/clipper_nestjs/src/modules/workflows/application/workflow-executor-registry.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/plugins/plugins.module.ts`

- [ ] **Step 1: Write executor tests**

Create `test/dialog-highlight-workflow-executor.test.js`.

Use fake dependencies:

- fake Python stage runner that records called stages.
- fake Dialog web_api client that returns known JSON.
- fake run context with `publishProgress`, `complete`, and `fail`.
- fake `PluginHost` that still exposes the legacy Python `dialog_highlight` manifest.

Assert order:

```text
prepare_media
analyze_media
web_api sentence_split
web_api story_backbone
web_api canonical_info
web_api define_highlight_topics
web_api select_highlights
web_api highlight_metadata
build_candidates
render_highlights
complete
```

Add a registry assertion:

```text
WorkflowExecutorRegistry.list() returns exactly one dialog_highlight executor
WorkflowExecutorRegistry.get('dialog_highlight') returns runtimeKind nestjs_executor
```

- [ ] **Step 2: Implement executor**

Create `dialog-highlight-workflow.executor.ts` implementing `WorkflowExecutor`.

Rules:

- `pluginName = 'dialog_highlight'`.
- `runtimeKind = 'nestjs_executor'`.
- `getManifest()` reads the legacy manifest from `PluginHost.getManifest('dialog_highlight')`, overlays `runtimeKind: 'nestjs_executor'`, and throws `WorkflowExecutorNotFoundError('dialog_highlight')` if the manifest is missing.
- `run(context)` orchestrates stages and web_api calls.
- Stage calls submit jobs to the Python plugin with `params.stage` set.
- For each web_api output, write the corresponding artifact JSON file before the next Python stage.
- If an artifact is missing or invalid, call `context.fail('artifact_contract_failed: ...')`.

- [ ] **Step 3: Register Dialog executor as the only Dialog execution path**

Modify `WorkflowExecutorRegistry` constructor to accept `DialogHighlightWorkflowExecutor` and make `pluginName === 'dialog_highlight'` resolve only to this NestJS executor. The generic Python plugin executor can still serve other Python-only plugins, but Dialog Highlight must not fall through to the generic Python execution path.

Update `list()` to skip Python manifests whose `name` already exists in `nestjsExecutors`:

```ts
async list(): Promise<WorkflowExecutor[]> {
  const nestjsNames = new Set(this.nestjsExecutors.map((executor) => executor.pluginName));
  const pythonExecutors = (await this.pluginHost.listManifests())
    .filter((manifest) => !nestjsNames.has(manifest.name))
    .map((manifest) => this.pythonFactory.create(this.withRuntimeKind(manifest, 'python_plugin')));
  return [
    ...this.nestjsExecutors,
    ...pythonExecutors,
    ...this.virtualExecutors(),
  ];
}
```

Example target:

```ts
constructor(
  private readonly pluginHost: PluginHost,
  private readonly pythonFactory: PythonPluginWorkflowExecutorFactory,
  ffmpegTransform: NestjsFfmpegTransformExecutor,
  dialogHighlight: DialogHighlightWorkflowExecutor,
) {
  this.nestjsExecutors = [ffmpegTransform, dialogHighlight];
}
```

- [ ] **Step 4: Wire module/providers**

Create `DialogHighlightModule`, export `DialogHighlightWorkflowExecutor`, and import `DialogHighlightModule` from the module that owns `WorkflowExecutorRegistry`. Keep provider ownership clear: Dialog executor code lives under `modules/dialog-highlight`; registry wiring only receives the exported executor.

- [ ] **Step 5: Verify executor registration**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/dialog-highlight-web-api-client.test.js test/dialog-highlight-workflow-executor.test.js test/workflow-executor-registry.test.js
```

Expected: exit 0.

- [ ] **Step 6: Commit executor**

```bash
git add src/modules/dialog-highlight src/modules/workflows/application/workflow-executor-registry.service.ts src/modules/plugins/plugins.module.ts src/app.module.ts test/dialog-highlight-workflow-executor.test.js
git commit -m "feat: orchestrate dialog highlight in nestjs"
```

---

## Task 9: Extract Python Candidate And Render Stages

**Files:**

- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/stage_runner.py`
- Create: `desktop/clipper_python/tests/test_dialog_candidate_stage.py`
- Create: `desktop/clipper_python/tests/test_dialog_render_stage.py`

- [ ] **Step 1: Write candidate stage test**

Assert `run_build_candidates` reads:

- `json/analysis.json`
- `json/llm_sentences.json`
- `json/story_backbone.json`
- `json/canonical_info.json`

and writes:

- `json/semantic_segments.json`
- `json/highlight_candidates.json`

- [ ] **Step 2: Write render stage test**

Assert `run_render_highlights` reads:

- `json/highlight_selection.json`
- `json/highlights_meta.json`

and writes:

- clips under `clips/`
- final `json/manifest.json`

Use monkeypatched ffmpeg helpers for unit tests so this test does not render a real video.

- [ ] **Step 3: Run failing tests**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_candidate_stage.py tests/test_dialog_render_stage.py -q
```

Expected: FAIL because stages still raise `NotImplementedError`.

- [ ] **Step 4: Extract candidate builder**

In `pipeline.py`, create:

```python
def build_candidates_from_artifacts(
    output_root: Path,
    device: str = "cpu",
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict[str, Any]:
    ...
```

Move non-provider logic that transforms STT/OCR/LLM artifacts into semantic segments and candidate payloads. This function must not call `client.chat.completions.create`.

- [ ] **Step 5: Extract renderer**

In `pipeline.py`, create:

```python
def render_highlights_from_artifacts(
    input_video: Path,
    output_root: Path,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict[str, Any]:
    ...
```

Move clip cutting, thumbnail generation, title/manifest writing, and output collection here.

- [ ] **Step 6: Connect stage runner**

Modify:

- `run_build_candidates` -> `build_candidates_from_artifacts`
- `run_render_highlights` -> `render_highlights_from_artifacts`

- [ ] **Step 7: Verify Python stages**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_stage_contracts.py tests/test_dialog_analyze_stage.py tests/test_dialog_candidate_stage.py tests/test_dialog_render_stage.py -q
```

Expected: exit 0.

- [ ] **Step 8: Commit Python stage extraction**

```bash
git add plugins/dialog_highlight/dialog_highlight/services/pipeline.py plugins/dialog_highlight/dialog_highlight/services/stage_runner.py tests/test_dialog_candidate_stage.py tests/test_dialog_render_stage.py
git commit -m "refactor: split dialog highlight media stages"
```

---

## Task 10: Remove Direct OpenAI From Python Dialog Plugin

**Files:**

- Delete: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/llm_client.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/app.py`
- Modify: `desktop/clipper_python/plugins/dialog_highlight/manifest.json` if it lists LLM env permissions.
- Test: `desktop/clipper_python/tests/test_dialog_no_external_provider_calls.py`

- [ ] **Step 1: Remove `llm_client.py`**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
git rm plugins/dialog_highlight/dialog_highlight/services/llm_client.py
```

- [ ] **Step 2: Remove direct LLM calls**

In `pipeline.py`, remove all active direct `client.chat.completions.create` usage from stage execution. Move prompt text that is still needed into `web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts`, then delete the Python prompt helper that owned that prompt.

`rg` must not find these strings under `plugins/dialog_highlight/dialog_highlight`:

- `from openai import`
- `OpenAI(`
- `OPENAI_API_KEY`
- `CLIPPER_LLM_PROXY_URL`
- `CLIPPER_SUBSCRIPTION_TOKEN`
- `client.chat.completions.create`

- [ ] **Step 3: Remove legacy monolithic run path**

In `app.py`, require `params.stage`.

If `stage` is missing, return:

```python
{"error": "dialog_highlight requires staged execution through local NestJS"}
```

Do not run `run_pipeline_for_video` directly.

- [ ] **Step 4: Verify no external provider calls**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_no_external_provider_calls.py tests/test_dialog_stage_contracts.py -q
rg "from openai import|OpenAI\\(|OPENAI_API_KEY|CLIPPER_LLM_PROXY_URL|CLIPPER_SUBSCRIPTION_TOKEN|client\\.chat\\.completions\\.create" plugins/dialog_highlight/dialog_highlight
```

Expected:

- pytest exits 0.
- `rg` exits 1 with no matches.

- [ ] **Step 5: Commit Python provider removal**

```bash
git add plugins/dialog_highlight tests/test_dialog_no_external_provider_calls.py
git commit -m "refactor: remove direct dialog llm provider calls"
```

---

## Task 11: Normalize Angular Provider Error Messages

**Files:**

- Modify: `desktop/clipper_angular/src/core/errors/error-catalog.ts`
- Modify tests under `desktop/clipper_angular/src/core/errors/*.spec.ts` or add one if absent.
- Modify Dialog/Dance setup component specs only if they assert exact displayed messages.

- [ ] **Step 1: Write error catalog tests**

Add tests for these input messages/codes:

- `web_api_not_configured`
- `web_api_unreachable`
- `provider_not_configured`
- `provider_failed`
- `artifact_contract_failed`

Expected Korean copy:

- web API not configured: "API 서버 주소가 설정되지 않았습니다."
- web API unreachable: "API 서버에 연결할 수 없습니다."
- provider not configured: "API 서버의 외부 제공자 설정이 완료되지 않았습니다."
- provider failed: "외부 제공자 호출에 실패했습니다."
- artifact contract failed: "파이프라인 단계 산출물을 읽을 수 없습니다."

- [ ] **Step 2: Run failing Angular test**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include src/core/errors/error-catalog.spec.ts
```

Expected: FAIL until mappings are added.

- [ ] **Step 3: Add mappings**

Modify `error-catalog.ts` so string messages containing the exact machine code map to the Korean copy above.

- [ ] **Step 4: Verify Angular error mapping**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include src/core/errors/error-catalog.spec.ts
npm run build
```

Expected: exit 0.

- [ ] **Step 5: Commit Angular errors**

```bash
git add src/core/errors/error-catalog.ts src/core/errors/error-catalog.spec.ts
git commit -m "feat: map provider routing errors"
```

---

## Task 12: End-To-End Local Verification

**Files:** no code changes expected.

- [ ] **Step 1: Run web_api tests/build**

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- dialog-highlight-llm.service.spec.ts --runInBand
npm test -- search.service.spec.ts --runInBand
npm run build
```

Expected: exit 0.

- [ ] **Step 2: Run desktop NestJS tests/build**

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/web-api-client.test.js test/dance-web-api-member-image-source.test.js test/dialog-highlight-web-api-client.test.js test/dialog-highlight-workflow-executor.test.js test/workflow-executor-registry.test.js
```

Expected: exit 0.

- [ ] **Step 3: Run Python tests**

```bash
cd /Users/jina/project/adlight/desktop/clipper_python
uv run --package clipper-plugin-dialog-highlight python -m pytest tests/test_dialog_stage_contracts.py tests/test_dialog_analyze_stage.py tests/test_dialog_candidate_stage.py tests/test_dialog_render_stage.py tests/test_dialog_no_external_provider_calls.py -q
```

Expected: exit 0.

- [ ] **Step 4: Run Electron tests/build**

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
npm test -- test/packaged-secret-scan.test.js
npm run build
```

Expected: exit 0.

- [ ] **Step 5: Run Angular tests/build**

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include src/core/errors/error-catalog.spec.ts
npm run build
```

Expected: exit 0.

---

## Task 13: Fresh Installed App Verification Checklist

Use this after the code-level checks pass and before considering the installed app complete.

### Windows reset

Run after closing the app:

```powershell
Stop-Process -Name Clipper2 -Force -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Clipper2" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface" -ErrorAction SilentlyContinue
```

### macOS reset

Run after closing the app:

```bash
pkill -f Clipper2 || true
rm -rf "$HOME/Library/Application Support/Clipper2"
rm -rf "$HOME/.cache/huggingface"
```

### Manual checks

- [ ] First launch opens a window before optional plugin installs.
- [ ] ffmpeg/ffprobe are absent before consent and appear under `userData/bin` after consent.
- [ ] Dance member image search fails clearly if `CLIPPER_WEB_API_BASE_URL` is missing.
- [ ] Dance member image search succeeds only when `web_api /media/search` is reachable and configured.
- [ ] Dialog Highlight fails clearly if `web_api /dialog-highlight/llm` is unreachable.
- [ ] Dialog Highlight succeeds with no OpenAI key in desktop packaged env.
- [ ] `desktop/clipper_python/.env.packaged` and `desktop/clipper_nestjs/.env.packaged` contain no forbidden key names.
- [ ] Packaged app resources contain no copied `.env` value with forbidden provider key names.

## Self-Review Checklist For Implementers

- [ ] `rg "OPENAI_API_KEY|NAVER_CLIENT_SECRET|KAKAO_REST_API_KEY" desktop/clipper_python desktop/clipper_nestjs desktop/clipper_electron/electron-builder.yml` has no active packaged/provider path.
- [ ] `rg "OpenAI\\(|client\\.chat\\.completions\\.create" desktop/clipper_python/plugins/dialog_highlight` returns no matches.
- [ ] `rg "NaverDirectImageSource|FallbackImageSource|KAKAO_REST_API_KEY" desktop/clipper_nestjs/src/modules/dance desktop/clipper_nestjs/test` returns no active references.
- [ ] Every repo touched has its focused tests and build command recorded in the commit message body or session worklog.
- [ ] No secret values are printed in logs, test output, or commit content.
