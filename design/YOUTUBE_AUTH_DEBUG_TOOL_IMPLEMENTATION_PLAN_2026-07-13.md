# YouTube Auth Debug Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 개발자 모드의 `YouTube 디버그` 페이지에서 Electron 쿠키 파일/세션을 조회·초기화하고, 동일 URL을 네 가지 인증 전략으로 yt-dlp 메타데이터 및 실제 다운로드 진단할 수 있게 한다.

**Architecture:** Electron은 `persist:youtube-auth` 세션과 Netscape 쿠키 파일을 단독 관리하고 IPC로 상태/제어만 노출한다. NestJS `sources` feature는 실제 SourceService의 yt-dlp 설정과 실행 인자를 재사용하는 진단 API를 제공하며, Angular는 기존 SourceInput과 Material 패턴으로 두 계약을 한 페이지에서 조합한다.

**Tech Stack:** Angular 19 standalone/zoneless/Material, Electron 35 IPC (embedded Node.js 22), NestJS 11, TypeScript, node:test, Karma, yt-dlp CLI with EJS dependencies

---

사용자 지시에 따라 이 계획의 커밋 단계는 생략한다. 각 저장소는 현재 `dev` 브랜치에서 수정하며, `.codex` 문서만 `main`에 둔다. push·배포·DB·runner 작업은 하지 않는다.

## Execution Status (2026-07-13)

- Task 1~7 구현 완료
- NestJS, Electron, Angular 빌드와 관련/전체 자동 테스트 통과
- yt-dlp EJS 경고 대응: Electron 35.7.0의 Node.js 22 런타임을 사용하고, 관리 venv에 `yt-dlp[default]`를 설치하도록 변경
- 기존 관리 venv는 EJS 런타임 marker가 없으면 다음 패키지 앱 기동 시 자동 보강
- 로컬 Angular/NestJS devapp 및 Electron 기동 확인 후 사용자 지시에 따라 모두 종료
- macOS packaged local-api에서 `전체 초기화` 후 기본 공개 URL의 `none + metadata` 성공
- 같은 조건의 실제 다운로드 성공: 종료 코드 0, 약 3.9초, 약 97.6 MB, 임시 파일 정리 경로 사용
- 회원 전용 영상의 `none + metadata`는 종료 코드 1과 `Join this channel` 오류로 실패해 접근 제한 재현 성공
- 아동용(`Made for Kids`) 공개 영상은 metadata/download 모두 성공했으며 기대 동작으로 확인
- 회원 전용 오류를 현재 `authRequired`가 분류하지 못하는 누락 확인; `availability`/`age_limit` 구조화 표시와 함께 후속 보완 필요
- 로그인 후 관리 쿠키/브라우저 쿠키, 연령 제한, anti-bot, Windows packaged 경로의 수동 검증은 보류
- 최초 실행/업데이트의 관리 venv 설치가 오프라인에서 실패할 때 안내·앱 진입 차단·재시도·부분 설치 복구가 되는지는 별도 감사 필요
- 사용자 지시에 따라 commit, push, 배포는 수행하지 않음

## File Map

### `desktop/clipper_nestjs`

- Create `src/modules/sources/domain/youtube-diagnostics.model.ts`: 진단 종류·인증 전략·결과 raw 계약과 허용 브라우저 목록
- Create `src/modules/sources/presentation/dto/run-youtube-diagnostic.dto.ts`: HTTP 입력 allowlist 검증
- Create `src/modules/sources/presentation/youtube-diagnostics.controller.ts`: config/run 진단 라우트
- Modify `src/modules/sources/application/source.service.ts`: 현재 yt-dlp 옵션을 재사용하는 config snapshot과 metadata/download 진단 실행
- Modify `src/modules/sources/sources.module.ts`: 새 controller 등록
- Create `test/youtube-diagnostics.test.js`: 인증 인자, 결과 판정, 임시 파일 정리, controller 위임 검증

### `desktop/clipper_electron`

- Create `src/main/youtube-cookie-file.ts`: 쿠키 경로 상태 조회·Netscape 줄 집계·삭제 순수 파일 함수
- Modify `src/shared/ipc-contract.ts`: YouTube debug IPC 채널과 payload 타입
- Modify `src/main/youtube-auth-ipc.ts`: 상태, 파일 위치, 삭제, 세션 초기화, 전체 초기화, 외부 브라우저 IPC
- Modify `src/preload/preload.ts`: 허용된 메서드만 renderer bridge에 노출
- Create `test/youtube-cookie-file.test.js`: 실제 임시 파일 기반 상태/삭제 테스트

### `desktop/clipper_angular`

- Modify `src/core/bridge/clipper-bridge.ts`: Electron debug bridge 타입
- Modify `src/core/source/youtube-auth.service.ts`: debug IPC facade
- Create `src/core/source/youtube-diagnostics.service.ts`: NestJS config/run API 클라이언트와 타입
- Create `src/core/source/youtube-diagnostics.service.spec.ts`: raw request/response 계약 테스트
- Modify `src/core/index.ts`: 새 service export
- Modify `src/core/navigation/app-navigation-metadata.ts`: `youtube_debug` dev-only 항목과 순서
- Modify `src/app/app.routes.ts`: `/youtube-debug` lazy route
- Modify `src/shared/layout/nav/nav.component.spec.ts`: developer mode 노출 순서 테스트
- Modify `src/shared/highlight-setup/source-input/source-input.component.ts`: 기존 동작을 유지하는 `youtubeOnly` 입력
- Modify `src/shared/highlight-setup/source-input/source-input.component.html`: YouTube 전용일 때 모드 탭/로컬 입력 숨김
- Modify `src/shared/highlight-setup/source-input/source-input.component.spec.ts`: 기본 모드 회귀와 YouTube 전용 렌더 테스트
- Create `src/shell/settings/youtube-debug/youtube-debug.component.ts`: 화면 상태와 명령 orchestration
- Create `src/shell/settings/youtube-debug/youtube-debug.component.html`: 쿠키 상태·제어·인증·진단 UI
- Create `src/shell/settings/youtube-debug/youtube-debug.component.scss`: 토큰 기반 responsive 레이아웃
- Create `src/shell/settings/youtube-debug/youtube-debug.component.spec.ts`: 기본 URL, IPC, 진단, 확인 다이얼로그 테스트

## Task 1: Define The NestJS Diagnostic Contract

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/sources/domain/youtube-diagnostics.model.ts`
- Create: `desktop/clipper_nestjs/src/modules/sources/presentation/dto/run-youtube-diagnostic.dto.ts`
- Test: `desktop/clipper_nestjs/test/youtube-diagnostics.test.js`

- [ ] **Step 1: Write failing contract tests**

Create `test/youtube-diagnostics.test.js` with tests that import the built model and assert the allowlists and auth argument builder:

```js
const assert = require('node:assert/strict');
const { describe, it } = require('node:test');
const {
  YOUTUBE_DIAGNOSTIC_BROWSERS,
  youtubeDiagnosticAuthArgs,
} = require('../dist/modules/sources/domain/youtube-diagnostics.model');

describe('youtube diagnostics contract', () => {
  it('keeps browser cookie sources on a fixed allowlist', () => {
    assert.deepEqual(YOUTUBE_DIAGNOSTIC_BROWSERS, ['chrome', 'edge', 'firefox', 'brave', 'safari']);
  });

  it('builds no auth args for none strategy', () => {
    assert.deepEqual(youtubeDiagnosticAuthArgs({ strategy: 'none' }, {}), []);
  });

  it('uses the effective source configuration', () => {
    assert.deepEqual(youtubeDiagnosticAuthArgs(
      { strategy: 'effective' },
      { cookiesPath: '/tmp/cookies.txt', cookiesPathExists: true },
    ), ['--cookies', '/tmp/cookies.txt']);
  });

  it('uses an explicitly validated managed cookie file', () => {
    assert.deepEqual(youtubeDiagnosticAuthArgs(
      { strategy: 'managed_file', managedCookiesPath: '/tmp/www.youtube.com_cookies.txt' },
      {},
    ), ['--cookies', '/tmp/www.youtube.com_cookies.txt']);
  });

  it('uses only allowlisted browser names', () => {
    assert.deepEqual(youtubeDiagnosticAuthArgs(
      { strategy: 'browser', browser: 'firefox' },
      {},
    ), ['--cookies-from-browser', 'firefox']);
    assert.throws(() => youtubeDiagnosticAuthArgs(
      { strategy: 'browser', browser: 'custom --flag' },
      {},
    ));
  });
});
```

- [ ] **Step 2: Run the test and confirm the missing-module failure**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/youtube-diagnostics.test.js
```

Expected: FAIL because `youtube-diagnostics.model` does not exist.

- [ ] **Step 3: Add the domain contract and pure auth argument builder**

Create `youtube-diagnostics.model.ts` with these public types and strict validation:

```ts
export const YOUTUBE_DIAGNOSTIC_BROWSERS = [
  'chrome', 'edge', 'firefox', 'brave', 'safari',
] as const;

export type YoutubeDiagnosticBrowser = typeof YOUTUBE_DIAGNOSTIC_BROWSERS[number];
export type YoutubeDiagnosticKind = 'metadata' | 'download';
export type YoutubeDiagnosticStrategy = 'effective' | 'none' | 'managed_file' | 'browser';

export interface YoutubeDiagnosticAuth {
  strategy: YoutubeDiagnosticStrategy;
  managedCookiesPath?: string;
  browser?: YoutubeDiagnosticBrowser;
}

export interface YoutubeDiagnosticConfigSnapshot {
  ytdlpBin: string;
  cookiesPath?: string;
  cookiesPathExists: boolean;
  cookiesFromBrowser?: string;
  autoBrowserCookies: boolean;
  browserFallbacks: string[];
}

export interface YoutubeDiagnosticResult {
  ok: boolean;
  kind: YoutubeDiagnosticKind;
  strategy: YoutubeDiagnosticStrategy;
  browser?: YoutubeDiagnosticBrowser;
  startedAt: string;
  finishedAt: string;
  elapsedMs: number;
  exitCode: number | null;
  authRequired: boolean;
  browserCookieError: boolean;
  videoId?: string;
  title?: string;
  downloadedBytes?: number;
  message?: string;
  stdout?: string;
  stderr?: string;
}

export interface EffectiveYoutubeAuthConfig {
  cookiesPath?: string;
  cookiesPathExists?: boolean;
  cookiesFromBrowser?: string;
}

export function youtubeDiagnosticAuthArgs(
  auth: YoutubeDiagnosticAuth,
  effective: EffectiveYoutubeAuthConfig,
): string[] {
  if (auth.strategy === 'none') return [];
  if (auth.strategy === 'effective') {
    if (effective.cookiesPath && effective.cookiesPathExists) {
      return ['--cookies', effective.cookiesPath];
    }
    return effective.cookiesFromBrowser
      ? ['--cookies-from-browser', effective.cookiesFromBrowser]
      : [];
  }
  if (auth.strategy === 'managed_file') {
    if (!auth.managedCookiesPath) throw new Error('managedCookiesPath is required');
    return ['--cookies', auth.managedCookiesPath];
  }
  if (!auth.browser || !YOUTUBE_DIAGNOSTIC_BROWSERS.includes(auth.browser)) {
    throw new Error('Unsupported diagnostic browser');
  }
  return ['--cookies-from-browser', auth.browser];
}
```

- [ ] **Step 4: Add DTO validation**

Create `run-youtube-diagnostic.dto.ts`:

```ts
import { IsIn, IsOptional, IsString, IsUrl } from 'class-validator';
import {
  YOUTUBE_DIAGNOSTIC_BROWSERS,
  type YoutubeDiagnosticBrowser,
  type YoutubeDiagnosticKind,
  type YoutubeDiagnosticStrategy,
} from '../../domain/youtube-diagnostics.model';

export class RunYoutubeDiagnosticDto {
  @IsUrl({ require_protocol: true })
  url!: string;

  @IsIn(['metadata', 'download'])
  kind!: YoutubeDiagnosticKind;

  @IsIn(['effective', 'none', 'managed_file', 'browser'])
  strategy!: YoutubeDiagnosticStrategy;

  @IsOptional()
  @IsString()
  managedCookiesPath?: string;

  @IsOptional()
  @IsIn(YOUTUBE_DIAGNOSTIC_BROWSERS)
  browser?: YoutubeDiagnosticBrowser;
}
```

- [ ] **Step 5: Build and run the contract tests**

Run `npm run build` and `node --test test/youtube-diagnostics.test.js`.

Expected: PASS for all contract tests.

## Task 2: Execute Metadata And Fresh Downloads Through SourceService

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/sources/application/source.service.ts`
- Create: `desktop/clipper_nestjs/src/modules/sources/presentation/youtube-diagnostics.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/sources/sources.module.ts`
- Modify: `desktop/clipper_nestjs/test/youtube-diagnostics.test.js`

- [ ] **Step 1: Add failing SourceService config and controller tests**

Append tests that construct `SourceService` with a minimal fake ConfigService and verify `youtubeDiagnosticConfig()`. Instantiate `YoutubeDiagnosticsController` with a fake service and verify `config()` and `run()` delegate raw results unchanged.

```js
const { SourceService } = require('../dist/modules/sources/application/source.service');
const { YoutubeDiagnosticsController } = require('../dist/modules/sources/presentation/youtube-diagnostics.controller');

it('reports the effective yt-dlp auth configuration without cookie values', () => {
  const values = new Map([
    ['CLIPPER_YTDLP_BIN', 'yt-dlp-test'],
    ['CLIPPER_YTDLP_COOKIES', '/missing/www.youtube.com_cookies.txt'],
    ['CLIPPER_YTDLP_COOKIES_FROM_BROWSER', 'firefox'],
    ['CLIPPER_YTDLP_AUTO_BROWSER_COOKIES', '1'],
  ]);
  const service = new SourceService({ get: (key) => values.get(key) });
  const snapshot = service.youtubeDiagnosticConfig();
  assert.equal(snapshot.ytdlpBin, 'yt-dlp-test');
  assert.equal(snapshot.cookiesPath, '/missing/www.youtube.com_cookies.txt');
  assert.equal(snapshot.cookiesPathExists, false);
  assert.equal(snapshot.cookiesFromBrowser, 'firefox');
  assert.equal('cookieContents' in snapshot, false);
});

it('delegates diagnostic runs through a raw controller response', async () => {
  const expected = { ok: true, kind: 'metadata', strategy: 'none', authRequired: false };
  const service = {
    youtubeDiagnosticConfig: () => ({ ytdlpBin: 'yt-dlp', cookiesPathExists: false }),
    runYoutubeDiagnostic: async (request) => ({ ...expected, request }),
  };
  const controller = new YoutubeDiagnosticsController(service);
  assert.equal(controller.config().ytdlpBin, 'yt-dlp');
  assert.deepEqual(
    await controller.run({ url: 'https://youtu.be/test', kind: 'metadata', strategy: 'none' }),
    { ...expected, request: { url: 'https://youtu.be/test', kind: 'metadata', strategy: 'none' } },
  );
});
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run `npm run build` followed by `node --test test/youtube-diagnostics.test.js`.

Expected: FAIL because the SourceService methods and controller are missing.

- [ ] **Step 3: Add SourceService config snapshot**

Import the diagnostic model, `mkdtemp`, `rm`, and `tmpdir`. Add a public method that returns only configuration metadata:

```ts
youtubeDiagnosticConfig(): YoutubeDiagnosticConfigSnapshot {
  return {
    ytdlpBin: this.ytdlpBin,
    cookiesPath: this.ytdlpCookiesPath,
    cookiesPathExists: !!this.ytdlpCookiesPath && existsSync(this.ytdlpCookiesPath),
    cookiesFromBrowser: this.ytdlpCookiesFromBrowser,
    autoBrowserCookies: this.ytdlpAutoBrowserCookies,
    browserFallbacks: [...this.ytdlpBrowserFallbacks],
  };
}
```

- [ ] **Step 4: Add diagnostic execution without changing production methods**

Add `runYoutubeDiagnostic()` beside the public `inspect/ingest` methods. It must:

1. Validate the URL with `validYoutubeUrl()`.
2. Validate `managed_file` as an absolute existing file named `www.youtube.com_cookies.txt`.
3. Build auth args with `youtubeDiagnosticAuthArgs()`.
4. Reuse `ytdlpJsRuntimeArgs()`, `ytdlpRemoteComponentArgs()`, and `ytdlpFfmpegArgs()`.
5. Run metadata with the same `--dump-json --skip-download --no-playlist` arguments.
6. Run downloads with the same 1080p format expression into `mkdtemp(join(tmpdir(), 'clipper-ytdlp-debug-'))`.
7. Find the completed video, record `stat().size`, and remove the temp directory in `finally`.
8. Catch `YtdlpCommandError` and return a raw diagnostic result rather than converting it to the production friendly error.
9. Limit stdout/stderr to the last 8,000 characters.

The public signature is:

```ts
async runYoutubeDiagnostic(request: {
  url: string;
  kind: YoutubeDiagnosticKind;
  strategy: YoutubeDiagnosticStrategy;
  managedCookiesPath?: string;
  browser?: YoutubeDiagnosticBrowser;
}): Promise<YoutubeDiagnosticResult>
```

Use a small internal result builder so both success and failure always include `startedAt`, `finishedAt`, `elapsedMs`, `kind`, `strategy`, `exitCode`, `authRequired`, and `browserCookieError`. Detect browser-cookie access errors with:

```ts
/could not copy chrome cookie database|failed to decrypt|keyring|cookies database|browser.*profile/i
```

Do not add `--verbose` and do not place auth args or cookie contents in any log message.

- [ ] **Step 5: Add the diagnostic controller and module registration**

Create `youtube-diagnostics.controller.ts`:

```ts
import { Body, Controller, Get, Post } from '@nestjs/common';
import { SourceService } from '../application/source.service';
import {
  YoutubeDiagnosticConfigSnapshot,
  YoutubeDiagnosticResult,
} from '../domain/youtube-diagnostics.model';
import { RunYoutubeDiagnosticDto } from './dto/run-youtube-diagnostic.dto';

@Controller('sources/diagnostics/youtube')
export class YoutubeDiagnosticsController {
  constructor(private readonly sources: SourceService) {}

  @Get('config')
  config(): YoutubeDiagnosticConfigSnapshot {
    return this.sources.youtubeDiagnosticConfig();
  }

  @Post('run')
  run(@Body() body: RunYoutubeDiagnosticDto): Promise<YoutubeDiagnosticResult> {
    return this.sources.runYoutubeDiagnostic(body);
  }
}
```

Register `YoutubeDiagnosticsController` next to `SourcesController` in `sources.module.ts`.

- [ ] **Step 6: Run NestJS verification**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/youtube-diagnostics.test.js
node --test test/error-code.test.js
```

Expected: all tests PASS and TypeScript build succeeds.

## Task 3: Add Electron Cookie File Primitives

**Files:**
- Create: `desktop/clipper_electron/src/main/youtube-cookie-file.ts`
- Create: `desktop/clipper_electron/test/youtube-cookie-file.test.js`

- [ ] **Step 1: Write failing file-state tests**

Create tests using `mkdtemp`, `writeFile`, and `rm` under `tmpdir()`:

```js
const assert = require('node:assert/strict');
const { afterEach, describe, it } = require('node:test');
const { mkdtemp, rm, writeFile } = require('node:fs/promises');
const { join } = require('node:path');
const { tmpdir } = require('node:os');
const {
  deleteYoutubeCookieFile,
  readYoutubeCookieFileState,
} = require('../dist-electron/main/youtube-cookie-file');

describe('youtube cookie file', () => {
  const dirs = [];
  afterEach(async () => Promise.all(dirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true }))));

  it('reports a missing file without throwing', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'clipper-cookie-test-'));
    dirs.push(dir);
    const state = await readYoutubeCookieFileState(join(dir, 'www.youtube.com_cookies.txt'));
    assert.equal(state.exists, false);
    assert.equal(state.content, '');
    assert.equal(state.cookieCount, 0);
  });

  it('returns raw content and counts only Netscape cookie rows', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'clipper-cookie-test-'));
    dirs.push(dir);
    const path = join(dir, 'www.youtube.com_cookies.txt');
    const content = '# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tfixture-value\n# comment\n';
    await writeFile(path, content, 'utf8');
    const state = await readYoutubeCookieFileState(path);
    assert.equal(state.exists, true);
    assert.equal(state.content, content);
    assert.equal(state.cookieCount, 1);
    assert.ok(state.sizeBytes > 0);
  });

  it('deletes idempotently', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'clipper-cookie-test-'));
    dirs.push(dir);
    const path = join(dir, 'www.youtube.com_cookies.txt');
    await deleteYoutubeCookieFile(path);
    await writeFile(path, 'cookie', 'utf8');
    await deleteYoutubeCookieFile(path);
    assert.equal((await readYoutubeCookieFileState(path)).exists, false);
  });
});
```

The literal `fixture-value` is synthetic test data only; never copy a real cookie value into the test.

- [ ] **Step 2: Run the Electron build/test and confirm failure**

Run `npm run build` and `node --test test/youtube-cookie-file.test.js` in `desktop/clipper_electron`.

Expected: FAIL because the helper module is missing.

- [ ] **Step 3: Implement file state and deletion**

Create `youtube-cookie-file.ts`:

```ts
import { readFile, stat, unlink } from 'node:fs/promises';

export interface YoutubeCookieFileState {
  exists: boolean;
  content: string;
  cookieCount: number;
  sizeBytes: number;
  modifiedAt: string | null;
}

export async function readYoutubeCookieFileState(path: string): Promise<YoutubeCookieFileState> {
  try {
    const [content, info] = await Promise.all([readFile(path, 'utf8'), stat(path)]);
    return {
      exists: true,
      content,
      cookieCount: content.split(/\r?\n/).filter((line) => line && !line.startsWith('#') && line.split('\t').length >= 7).length,
      sizeBytes: info.size,
      modifiedAt: info.mtime.toISOString(),
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return { exists: false, content: '', cookieCount: 0, sizeBytes: 0, modifiedAt: null };
    }
    throw error;
  }
}

export async function deleteYoutubeCookieFile(path: string): Promise<void> {
  try {
    await unlink(path);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
  }
}
```

- [ ] **Step 4: Run the tests**

Run `npm run build` and `node --test test/youtube-cookie-file.test.js`.

Expected: PASS.

## Task 4: Extend The Electron YouTube Auth IPC

**Files:**
- Modify: `desktop/clipper_electron/src/shared/ipc-contract.ts`
- Modify: `desktop/clipper_electron/src/main/youtube-auth-ipc.ts`
- Modify: `desktop/clipper_electron/src/preload/preload.ts`
- Modify: `desktop/clipper_electron/test/youtube-cookie-file.test.js`

- [ ] **Step 1: Add contract assertions to the existing test**

Import `IPC` from `dist-electron/shared/ipc-contract` and assert six new unique channels:

```js
it('exposes distinct youtube debug IPC channels', () => {
  const { IPC } = require('../dist-electron/shared/ipc-contract');
  const channels = [
    IPC.youtubeAuth.getDebugState,
    IPC.youtubeAuth.openCookiesLocation,
    IPC.youtubeAuth.deleteCookieFile,
    IPC.youtubeAuth.clearEmbeddedSession,
    IPC.youtubeAuth.resetDebugState,
    IPC.youtubeAuth.openExternalLogin,
  ];
  assert.equal(new Set(channels).size, channels.length);
});
```

- [ ] **Step 2: Run the test and confirm missing channels**

Run `npm run build` and `node --test test/youtube-cookie-file.test.js`.

Expected: FAIL because the channels do not exist.

- [ ] **Step 3: Define IPC channels and payloads**

Add these channel names under `IPC.youtubeAuth`:

```ts
getDebugState: 'clipper:youtubeAuth:getDebugState',
openCookiesLocation: 'clipper:youtubeAuth:openCookiesLocation',
deleteCookieFile: 'clipper:youtubeAuth:deleteCookieFile',
clearEmbeddedSession: 'clipper:youtubeAuth:clearEmbeddedSession',
resetDebugState: 'clipper:youtubeAuth:resetDebugState',
openExternalLogin: 'clipper:youtubeAuth:openExternalLogin',
```

Add the shared response:

```ts
export interface YoutubeAuthDebugState {
  cookiesPath: string;
  fileExists: boolean;
  fileContent: string;
  fileCookieCount: number;
  fileSizeBytes: number;
  fileModifiedAt: string | null;
  embeddedSessionCookieCount: number;
}
```

- [ ] **Step 4: Implement IPC handlers in the existing YouTube domain**

Refactor `youtube-auth-ipc.ts` around two private helpers:

```ts
const YOUTUBE_AUTH_PARTITION = 'persist:youtube-auth';
const YOUTUBE_LOGIN_URL = 'https://www.youtube.com/';

function youtubeCookiesPath(): string {
  return join(app.getPath('userData'), 'www.youtube.com_cookies.txt');
}

function youtubeAuthSession(): Session {
  return session.fromPartition(YOUTUBE_AUTH_PARTITION);
}
```

Register handlers with these exact behaviors:

- `getDebugState`: combine `readYoutubeCookieFileState()` with the filtered Electron session cookie count.
- `openCookiesLocation`: call `shell.showItemInFolder(path)` when the file exists; otherwise `mkdir(dirname(path), {recursive:true})` then `shell.openPath(dirname(path))`.
- `deleteCookieFile`: delete only the Netscape file.
- `clearEmbeddedSession`: call `youtubeAuthSession().clearStorageData()` without touching the file.
- `resetDebugState`: delete the file and clear the session with `Promise.all`.
- `openExternalLogin`: call `shell.openExternal(YOUTUBE_LOGIN_URL)`.

Change cookie export to write with owner-only mode and enforce it after overwriting:

```ts
await writeFile(cookiesPath, `${lines.join('\n')}\n`, { encoding: 'utf8', mode: 0o600 });
if (process.platform !== 'win32') await chmod(cookiesPath, 0o600);
```

Keep cookie contents out of logs and do not return them from `openLogin`; raw content is returned only by `getDebugState`.

- [ ] **Step 5: Expose preload methods**

Extend `youtubeAuth` in preload:

```ts
getDebugState: (): Promise<YoutubeAuthDebugState> => ipcRenderer.invoke(IPC.youtubeAuth.getDebugState),
openCookiesLocation: (): Promise<void> => ipcRenderer.invoke(IPC.youtubeAuth.openCookiesLocation),
deleteCookieFile: (): Promise<void> => ipcRenderer.invoke(IPC.youtubeAuth.deleteCookieFile),
clearEmbeddedSession: (): Promise<void> => ipcRenderer.invoke(IPC.youtubeAuth.clearEmbeddedSession),
resetDebugState: (): Promise<void> => ipcRenderer.invoke(IPC.youtubeAuth.resetDebugState),
openExternalLogin: (): Promise<void> => ipcRenderer.invoke(IPC.youtubeAuth.openExternalLogin),
```

- [ ] **Step 6: Verify Electron**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
npm run build
npm test
```

Expected: build and all Electron node tests PASS.

## Task 5: Add Angular Contracts And API Services

**Files:**
- Modify: `desktop/clipper_angular/src/core/bridge/clipper-bridge.ts`
- Modify: `desktop/clipper_angular/src/core/source/youtube-auth.service.ts`
- Create: `desktop/clipper_angular/src/core/source/youtube-diagnostics.service.ts`
- Create: `desktop/clipper_angular/src/core/source/youtube-diagnostics.service.spec.ts`
- Modify: `desktop/clipper_angular/src/core/index.ts`

- [ ] **Step 1: Write the failing diagnostics service test**

Use `HttpTestingController` and a fake `BackendLocator`:

```ts
it('loads the effective youtube diagnostic config', async () => {
  const promise = service.config();
  const req = http.expectOne('http://127.0.0.1:9019/v1/sources/diagnostics/youtube/config');
  expect(req.request.method).toBe('GET');
  req.flush({ ytdlpBin: 'yt-dlp', cookiesPathExists: false, autoBrowserCookies: false, browserFallbacks: [] });
  await expectAsync(promise).toBeResolvedTo(jasmine.objectContaining({ ytdlpBin: 'yt-dlp' }));
});

it('posts a raw metadata diagnostic request', async () => {
  const body = { url: 'https://youtu.be/test', kind: 'metadata', strategy: 'none' } as const;
  const promise = service.run(body);
  const req = http.expectOne('http://127.0.0.1:9019/v1/sources/diagnostics/youtube/run');
  expect(req.request.method).toBe('POST');
  expect(req.request.body).toEqual(body);
  req.flush({ ok: false, ...body, startedAt: '', finishedAt: '', elapsedMs: 1, exitCode: 1, authRequired: true, browserCookieError: false });
  expect((await promise).authRequired).toBeTrue();
});
```

- [ ] **Step 2: Run the focused Angular test and confirm failure**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include src/core/source/youtube-diagnostics.service.spec.ts
```

Expected: FAIL because the service is missing.

- [ ] **Step 3: Mirror the Electron debug state contract and facade**

Add `YoutubeAuthDebugState` to `clipper-bridge.ts` with the same fields as Electron. Extend `ClipperBridge.youtubeAuth` with all six Promise methods.

Extend `YoutubeAuthService` with:

```ts
isAvailable(): boolean
getDebugState(): Promise<YoutubeAuthDebugState>
openCookiesLocation(): Promise<void>
deleteCookieFile(): Promise<void>
clearEmbeddedSession(): Promise<void>
resetDebugState(): Promise<void>
openExternalLogin(): Promise<void>
```

Every method except `isAvailable` must call a private `bridge()` helper that throws the existing Electron-only error when the bridge is absent.

- [ ] **Step 4: Implement the NestJS diagnostic API service**

Create `youtube-diagnostics.service.ts` with mirrored raw contracts and only two methods:

```ts
@Injectable({ providedIn: 'root' })
export class YoutubeDiagnosticsService {
  private readonly http = inject(HttpClient);
  private readonly backend = inject(BackendLocator);

  async config(): Promise<YoutubeDiagnosticConfigSnapshot> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.get<YoutubeDiagnosticConfigSnapshot>(`${base}/sources/diagnostics/youtube/config`));
  }

  async run(request: RunYoutubeDiagnosticRequest): Promise<YoutubeDiagnosticResult> {
    const base = await this.backend.getBaseUrl();
    return firstValueFrom(this.http.post<YoutubeDiagnosticResult>(`${base}/sources/diagnostics/youtube/run`, request));
  }
}
```

Export the service and types through `src/core/index.ts`.

- [ ] **Step 5: Run the focused test and build**

Run the focused Karma test, then `npm run build`.

Expected: PASS and production Angular build succeeds.

## Task 6: Add Dev Navigation And YouTube-Only Source Input

**Files:**
- Modify: `desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts`
- Modify: `desktop/clipper_angular/src/app/app.routes.ts`
- Modify: `desktop/clipper_angular/src/shared/layout/nav/nav.component.spec.ts`
- Modify: `desktop/clipper_angular/src/shared/highlight-setup/source-input/source-input.component.ts`
- Modify: `desktop/clipper_angular/src/shared/highlight-setup/source-input/source-input.component.html`
- Modify: `desktop/clipper_angular/src/shared/highlight-setup/source-input/source-input.component.spec.ts`

- [ ] **Step 1: Add failing navigation and source-input tests**

Extend the nav developer-mode test to assert both presence and DOM order:

```ts
const debugLink = fixture.nativeElement.querySelector('a[href="/youtube-debug"]');
const logsLink = fixture.nativeElement.querySelector('a[href="/logs"]');
expect(debugLink).not.toBeNull();
expect(logsLink).not.toBeNull();
expect(debugLink.compareDocumentPosition(logsLink) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
```

Before enabling developer mode, assert both links are null.

Add a SourceInput test:

```ts
it('renders only the youtube URL input when youtubeOnly is true', () => {
  fixture.componentInstance.youtubeOnly = true;
  fixture.componentInstance.sourceMode = 'youtube';
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelector('.source-tabs')).toBeNull();
  expect(fixture.nativeElement.querySelector('input[type="url"]')).not.toBeNull();
  expect(fixture.nativeElement.querySelector('.drop-zone')).toBeNull();
});
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```bash
npm test -- --watch=false --include src/shared/layout/nav/nav.component.spec.ts --include src/shared/highlight-setup/source-input/source-input.component.spec.ts
```

Expected: FAIL because the nav item and input option are missing.

- [ ] **Step 3: Add navigation metadata and route**

Add `'youtube_debug'` to `ShellNavigationName`, place it immediately before `'logs'` in `UTILITY_SHELL_NAVIGATION_ORDER`, and define:

```ts
youtube_debug: shellMetadata({
  name: 'youtube_debug',
  kind: 'shell',
  label: 'YouTube 디버그',
  pageTitle: 'YouTube 인증 디버그',
  subtitle: '쿠키와 yt-dlp 인증 경로를 비교합니다.',
  icon: 'cookie',
  route: 'youtube-debug',
  devOnly: true,
}),
```

Add a lazy `/youtube-debug` route immediately before `/logs`.

- [ ] **Step 4: Add YouTube-only rendering without changing existing callers**

Add `@Input() youtubeOnly = false` to `SourceInputComponent`. Wrap only the mode tabs with `@if (!youtubeOnly)`, and render the local drop zone only when `!youtubeOnly && sourceMode === 'file'`. Existing dance/dialog callers see no behavior change because the default remains false.

- [ ] **Step 5: Run focused tests and Angular build**

Expected: nav/source tests PASS and build resolves the lazy route after the page is created in Task 7. If the route build fails before Task 7, run tests only and defer the build to Task 7.

## Task 7: Build The YouTube Debug Page

**Files:**
- Create: `desktop/clipper_angular/src/shell/settings/youtube-debug/youtube-debug.component.ts`
- Create: `desktop/clipper_angular/src/shell/settings/youtube-debug/youtube-debug.component.html`
- Create: `desktop/clipper_angular/src/shell/settings/youtube-debug/youtube-debug.component.scss`
- Create: `desktop/clipper_angular/src/shell/settings/youtube-debug/youtube-debug.component.spec.ts`

- [ ] **Step 1: Write failing component tests**

Configure the standalone component with mocked `YoutubeAuthService`, `YoutubeDiagnosticsService`, and `ConfirmDialogService`. Cover these exact assertions:

```ts
expect(component.youtubeUrl()).toBe('https://youtu.be/9cS2wv6AfHk?si=alPbLCGjV_2OMD9E');
expect(fixture.nativeElement.querySelector('app-source-input')).not.toBeNull();
```

Then verify:

- initial load calls both Electron state and Nest config once;
- raw cookie content is absent until `showCookieContents` is true;
- folder icon calls `openCookiesLocation`;
- manual refresh reloads state/config;
- embedded login reloads cookie state after the window closes;
- external login only opens the browser and does not claim cookie success;
- each destructive action asks for confirmation and reloads state only when confirmed;
- metadata calls `run()` with `kind: 'metadata'`;
- download asks for confirmation and calls `run()` with `kind: 'download'`;
- `managed_file` sends the current Electron `cookiesPath`;
- `browser` sends the selected browser;
- running state disables both diagnostic commands;
- metadata and download results remain independently visible.

- [ ] **Step 2: Run the component test and confirm missing component failure**

Run:

```bash
npm test -- --watch=false --include src/shell/settings/youtube-debug/youtube-debug.component.spec.ts
```

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement component state and commands**

The component must use signals with these initial values:

```ts
readonly youtubeUrl = signal('https://youtu.be/9cS2wv6AfHk?si=alPbLCGjV_2OMD9E');
readonly strategy = signal<YoutubeDiagnosticStrategy>('effective');
readonly browser = signal<YoutubeDiagnosticBrowser>('chrome');
readonly cookieState = signal<YoutubeAuthDebugState | null>(null);
readonly nestConfig = signal<YoutubeDiagnosticConfigSnapshot | null>(null);
readonly showCookieContents = signal(false);
readonly loadingState = signal(false);
readonly runningKind = signal<YoutubeDiagnosticKind | null>(null);
readonly metadataResult = signal<YoutubeDiagnosticResult | null>(null);
readonly downloadResult = signal<YoutubeDiagnosticResult | null>(null);
readonly pageError = signal<string | null>(null);
```

Implement `refreshState`, `openCookieLocation`, `openEmbeddedLogin`, `openExternalLogin`, `deleteCookieFile`, `clearEmbeddedSession`, `resetAll`, `runMetadata`, and `runDownload`. `runDiagnostic(kind)` must build the request from the selected strategy and store the result in the matching result signal without clearing the other result.

Use `appErrorFrom()` or a local message extractor for HTTP/IPC failures, but never append cookie content to the error string.

- [ ] **Step 4: Implement the four-section template**

Use `<app-page>` and unframed sections separated by `mat-divider`:

1. `쿠키 상태`: status definition list, `folder_open` and `refresh` icon buttons beside this section heading, reveal toggle, raw `<pre>` only when enabled.
2. `쿠키·세션 제어`: file delete, session clear, reset-all buttons.
3. `로그인 방식`: Electron login and external browser buttons.
4. `yt-dlp 진단`: Material button-toggle strategy, browser select for browser strategy, YouTube-only `<app-source-input>`, separate actual download button, metadata/download result panels.

Every icon-only button must have `aria-label` and `matTooltip`. Use Material icons rather than inline SVG. Do not put the sections inside cards.

- [ ] **Step 5: Implement token-only responsive SCSS**

Use only existing semantic variables such as `--outline-variant`, `--surface-container`, `--on-surface`, `--on-surface-variant`, `--danger`, `--primary`, and spacing/radius tokens. Required stable layout rules:

```scss
:host { display: block; }
.debug-section { display: grid; gap: var(--space-md); padding-block: var(--space-lg); }
.section-heading { display: flex; align-items: center; gap: var(--space-sm); }
.section-actions { display: flex; align-items: center; gap: var(--space-xs); margin-left: auto; }
.status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-sm); }
.cookie-content, .diagnostic-output { max-height: 320px; overflow: auto; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, monospace; }
.command-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-sm); }
.result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--space-md); }
```

No raw hex, rgba, negative letter spacing, nested cards, or viewport-scaled fonts.

- [ ] **Step 6: Run Angular tests and build**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include src/shell/settings/youtube-debug/youtube-debug.component.spec.ts --include src/core/source/youtube-diagnostics.service.spec.ts --include src/shared/layout/nav/nav.component.spec.ts --include src/shared/highlight-setup/source-input/source-input.component.spec.ts
npm run build
```

Expected: all focused tests PASS and Angular production build succeeds with raw-hex invariant unchanged.

## Task 8: Cross-Repository Verification And Runtime Smoke

**Files:**
- Verify only; do not add docs outside `.codex`.

- [ ] **Step 1: Run all relevant builds and tests**

Run in order:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/youtube-diagnostics.test.js test/error-code.test.js

cd /Users/jina/project/adlight/desktop/clipper_electron
npm run build
npm test

cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false
npm run build
```

Expected: all commands exit 0.

- [ ] **Step 2: Inspect repository diffs and secret safety**

Run `git diff --check` and `git status --short` in each changed repository. Search changed files for cookie fixture values and confirm only the explicit fake value in the Electron unit test exists. Confirm no `.env`, real cookies, generated downloads, or user-specific runtime paths are staged or untracked.

- [ ] **Step 3: Start local runtime services**

Use the existing devapp execution order without changing env files:

1. Start NestJS with `npm run start:devapp` on `127.0.0.1:9019`.
2. Start Angular with `npm run start:devapp`.
3. Start Electron with `npm run start:devapp`.

If a port is occupied, inspect the existing process and use the already-running matching service instead of killing it.

- [ ] **Step 4: Perform UI and IPC smoke checks**

Verify:

1. Build number five-click activation reveals `YouTube 디버그` immediately above `디버그 로그`.
2. Cookie status section buttons are inside the section rather than in the page header.
3. Folder open selects the file or opens its parent directory.
4. File delete does not clear the embedded session; full reset clears both.
5. No-cookie metadata result displays auth requirement when yt-dlp returns it.
6. Embedded login refreshes the managed cookie file state.
7. External browser opens without falsely reporting completion.
8. Selected browser strategy reaches `--cookies-from-browser` and displays read/decrypt errors separately.
9. Actual download reports downloaded bytes and leaves no diagnostic temp directory.
10. Cookie contents never appear in debug logs.

- [ ] **Step 5: Final status report**

Report changed repositories/files, test/build results, runtime URL/process state, and any environment-specific diagnostic limitation. Do not commit, push, package, deploy, or restart runners without a separate user request.
