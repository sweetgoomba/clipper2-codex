# Independent Development App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, or superpowers:subagent-driven-development only when the user chooses delegation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 새 개발판을 옛 개발판/운영판과 독립적으로 설치·실행하고, 해당 앱에서 시작한 로그인만 완료한다.

**Architecture:** Electron의 빌드 identity를 설치 설정·데이터 경로·로그인 대상·업데이트 채널의 기준으로 사용한다. Web API는 명시적인 desktop target 및 로그인 시도 결속을 검증한다. 기존 사용자 계정·프로젝트 파일을 이동하거나 초기화하지 않는다.

**Tech Stack:** Electron/TypeScript/node:test, NestJS/Jest/TypeORM/PostgreSQL. 추가 인증 라이브러리 없이 기존 JwtService와 Node crypto 사용.

**Spec:** [승인된 독립 개발판 변경안](2026-09-17-independent-dev-identity-design.md). 2026-09-17 사용자 “응”으로 변경 범위 확인.

## 실행 체크포인트 (2026-09-17)

- [x] Task 1–2 Electron 코드 기반 구현, TypeScript build 및 전체 회귀 **963/963 PASS**. [상세 증거와 한계](2026-09-17-independent-dev-app-validation.md).
- [x] builder 생성은 dev/prod 모두 다루도록 `prepareDesktopBuilderConfig`로 통일. `scripts/build-app.mjs` 호출/secret allowlist의 공개 updateChannel/로그 격리도 함께 반영했다. Windows update YAML은 빌더 생성기 fixture로 확인했다.
- [ ] 실제 Windows 설치본 내부 YAML/캐시/NSIS와 Mac 동시 실행 검증. 이번에는 앱 패키징·기동 없음.
- [x] Task 3–4 로그인 계약/서명 state/S256/code 원자 소비/앱 pending 결속 코드 연결. Web API build 및 2,845 PASS/21 SKIP, Electron build 및 975 PASS. 실제 DB·Google·설치본 실기와 독립 리뷰 게이트는 별도 미완료.
- [ ] release 계획 API/runner/Admin 변경 및 Task 5 템플릿 실기.
- [ ] 커밋/푸시 승인 및 실행. 현재 Electron·Web API·문서 변경 미커밋, 새 병합/배포 없음.

아래는 원래 세부 실행 명세이다. 위 체크포인트가 실제 실행 상태를 나타내며, 명세에 있는 실기/commit 단계를 모두 완료한 것으로 해석하지 않는다.

## Global Constraints

- 저장소 기준 경로: `/Users/jina/project/adlight`. 아래 경로는 이 루트 기준. 원본 checkout의 `integration/dev-pg-local-validation-20260917`에서 실행한다. branch 이동/새 병합은 이 계획에 포함하지 않는다.
- 새 개발판: `Clipper Studio (dev)` / `ai.clipperstudio.dev` / `clipperstudio-dev` / `Clipper Studio Dev` / update `dev`.
- 운영판: `Clipper Studio` / `ai.clipperstudio.app` / `clipperstudio` / `Clipper` / update 기본 `stable`.
- 구 개발판의 `ai.clipperstudio.desktop`, `clipper`, `Clipper Studio`를 새 코드의 호환 fallback으로 남기지 않는다. 과거 테스트 자료·역사 문서는 삭제 대상이 아니다.
- 템플릿 이관 필수. 전체 폴더 복사/옛 queue 이행/옛 로그인 세션 이행은 구현하지 않는다.
- 서버 접속·실제 개발 DB 변경·배포·push 금지. migration 실행은 별도 승인된 로컬 검증 DB에만 한다. 이 계획의 migration 코드 작성과 migration 실행 승인은 다르다.
- 커밋은 사용자 요청 범위가 확인된 경우에만 단계별 수행. 각 단계에서 diff/test 결과를 남기고 승인 없는 일괄 add/commit을 하지 않는다.
- 실제 ML 실행·Build 5 전체 QA HOLD. Windows 실기는 사용자가 수행.
- Mac 공개·자동빌드·자동 업데이트 구현 HOLD 유지. 현재 로컬 Mac 빌드는 autoUpdateDisabled=true. ZIP 지원은 이번 범위 아님. Mac feed 주소/캐시 격리 설계를 자동 업데이트 활성화로 해석하지 않는다.

## 작업 시작 점검

- [ ] 각 대상 저장소에서 `git status --short --branch`, `git rev-parse HEAD` 기록. unrelated dirty 파일은 보존한다.
- [ ] Node/의존성 버전을 확인하고 아래 각 task의 기존 테스트를 먼저 실행한다. 자동 dependency upgrade 없음.
- [ ] `.env` 내용·토큰·OAuth secret은 출력/계획/fixture에 넣지 않는다. 모형 키는 테스트에서 생성한다.

## Task 1: 설치 identity와 runtime config 계약

**Files — modify:**

- `desktop/clipper_electron/electron-builder.yml`
- `desktop/clipper_electron/package.json`, `package-lock.json` (root package name only; dependencies unchanged)
- `desktop/clipper_electron/scripts/build-runtime-config.mjs`
- `desktop/clipper_electron/src/main/config/production-identity.ts`
- `desktop/clipper_electron/src/main/config/packaged-runtime-config.ts`
- `desktop/clipper_electron/src/main/main.ts`
- `desktop/clipper_electron/src/main/auth/deeplink.ts` (이번 task에서는 protocol type/default만 변경)
- `desktop/clipper_electron/test/production-identity.test.js`
- `desktop/clipper_electron/test/build-runtime-config.test.mjs`
- `desktop/clipper_electron/test/packaged-runtime-config.test.js`
- `desktop/clipper_electron/test/packaging-artifact-name.test.js`

**Interfaces:** PackagedRuntimeConfig.identity becomes `'development' | 'production'`. `updateChannel` becomes `'dev' | 'stable'`. Existing `applyDesktopIdentity(app, config, ensureDirectory)` retained. `protocolForIdentity(config)` returns `'clipperstudio-dev' | 'clipperstudio'`. Packaged config must explicitly name identity; unpackaged entry builds an explicit development config. Missing/invalid packaged identity is a packaging error, not a silent production/dev guess.

- [ ] Add the following assertion to production-identity.test.js (existing Node test imports retained), then build/run and confirm RED:

```js
test('new development identity has independent paths and Windows app ID', () => {
  const calls = [];
  const app = {
    getPath: () => '/app-data', setName: v => calls.push(['name', v]),
    setPath: (k, v) => calls.push([k, v]),
    setAppUserModelId: v => calls.push(['appId', v]),
  };
  applyDesktopIdentity(app, { identity: 'development' }, () => {});
  assert.ok(calls.some(([k,v]) => k === 'userData' && v === join('/app-data', 'Clipper Studio Dev')));
  assert.ok(calls.some(([k,v]) => k === 'appId' && v === 'ai.clipperstudio.dev'));
  assert.equal(protocolForIdentity({ identity:'development' }), 'clipperstudio-dev');
  assert.equal(acceptsProtocol('clipper://auth/callback', 'clipperstudio-dev'), false);
});
```

- [ ] Run from Electron: `npm run build && node --test test/production-identity.test.js test/build-runtime-config.test.mjs test/packaged-runtime-config.test.js test/packaging-artifact-name.test.js`. RED must reflect expected old identity, not unrelated build failures.
- [ ] Implement explicit profile constants in production-identity.ts; retain functions instead of introducing a class hierarchy:

```ts
export const DESKTOP_IDENTITIES = {
  development: { appId:'ai.clipperstudio.dev', name:'Clipper Studio (dev)', directory:'Clipper Studio Dev', protocol:'clipperstudio-dev', updateChannel:'dev' },
  production: { appId:'ai.clipperstudio.app', name:'Clipper Studio', directory:'Clipper', protocol:'clipperstudio', updateChannel:'stable' },
} as const;
```

- [ ] `runtimeConfigForBuild` always emits explicit identity/channel/API. `--local-api` emits development/dev, localhost API, autoUpdateDisabled=true. Ordinary dev build emits dev-api; production requires existing production API check. Accept explicit `CLIPPER_DESKTOP_ENVIRONMENT=dev|prod`, unset means dev at build entry only; other values fail. Update production builder regex to new base ID/scheme and assert generated production config has no dev protocol registration.
- [ ] Set development package name to `clipper-studio-dev` in package.json and lock root metadata. Set the production generated package name to `clipper-studio`; the installed builder derives updater cache from package name, so appId change alone would leave old/new dev sharing `clipper-electron-updater`. Assert new dev cache `clipper-studio-dev-updater`, production `clipper-studio-updater`, neither equal old dev cache. No dependency upgrade. The production package/cache rename was approved on 2026-09-18 because the prior internal `clipper` name had not been publicly distributed.
- [ ] Both profiles set app name, userData, sessionData and AppUserModelId before single-instance lock/bootstrap. Do not rename the existing production data directory. Change deep-link activeProtocol/initDeepLink type/default to the new development scheme here so this task builds independently; callback proof logic stays in Task 4.
- [ ] Rerun the four tests; inspect YAML and generated-config fixture diff. Record unexecuted real packaging separately. Review/commit checkpoint under user authority.

## Task 2: App-local mutable state and update selection

**Files — modify:** Electron `src/main/config/packaged-runtime-config.ts`, `src/main/main.ts`, `src/main/update/update-feed.ts`, `src/main/update/auto-update-core.ts`; tests `packaged-runtime-config.test.js`, `update-feed.test.js`, `main-boot-order-boundary.test.js`, `installer-process-isolation.test.mjs`, `auth-token-store.test.js`.

**Interfaces:** Rename `productionIsolationEnv` to `desktopIsolationEnv(config, userDataPath)` and update its callers (no compatibility alias). `resolveUpdateFeed` consumes env after `applyRuntimeConfigToEnv` has pinned channel/base to the packaged profile. Missing channel no longer falls back to stable.

- [ ] Add a RED test to packaged-runtime-config.test.js:

```js
const env = applyRuntimeConfigToEnv(
  { CLIPPER_UPDATE_CHANNEL:'stable', HF_HOME:'/old-cache' },
  { identity:'development', updateChannel:'dev', webApiBaseUrl:'https://dev-api.clipperstudio.ai' },
  '/new-user-data',
);
assert.equal(env.CLIPPER_UPDATE_CHANNEL, 'dev');
assert.equal(env.HF_HOME, require('node:path').join('/new-user-data', 'cache', 'huggingface'));
```

- [ ] Run Electron build and `node --test test/packaged-runtime-config.test.js test/update-feed.test.js test/main-boot-order-boundary.test.js test/installer-process-isolation.test.mjs test/auth-token-store.test.js`.
- [ ] Set cache variables for both identities under their userData; retain production port range 55000–55199. Development uses existing dynamic PortAllocator; remove inherited range overrides in the final dev env instead of reusing the production range. Apply these values to process.env and child env consistently.
- [ ] Preserve userData-based auth.bin/Nest data/plugin runtime ownership. Audit logs, telemetry outbox and updater cache paths for writes outside profile root; fix only shared mutable destinations reached by these flows. Do not copy old .env overrides into new userData.
- [ ] Set feed base from pinned API and channel from profile. local-api disabled update flag takes precedence. Runtime mismatched identity/channel fails validation; no stable fallback.
- [ ] 자동 업데이트를 사용하는 Windows packaging의 app-update.yml/updaterCacheDirName을 검사한다. Generate builder generic publish configuration using the profile's feed base, retaining explicit `--publish never` for local packaging so this config cannot authorize upload. Read final bundled YAML in packaging tests; setAsDefaultProtocolClient/setFeedURL alone does not establish updater cache isolation. Production/new dev cache names must match installer store paths, and old dev cache remains untouched. Mac은 비활성 유지 여부를 검사하며 이 설정을 넣기 위해 자동 업데이트를 켜지 않는다.

```ts
const expected = config.identity === 'production' ? 'stable' : 'dev';
if (config.updateChannel !== expected) throw new Error('desktop_update_identity_mismatch');
// applyRuntimeConfigToEnv result, after spreading inherited env:
// CLIPPER_UPDATE_CHANNEL: expected
// CLIPPER_UPDATE_FEED_BASE_URL: `${config.webApiBaseUrl}/releases/updates`
```

- [ ] Add assertions for Mac ARM64 and Windows x64 exact feed URLs in the spec; local-api causes no update request; missing channel returns null. Production defaults remain stable. Verify NSIS installation/kill scope by existing path-boundary tests; do not edit node_modules.
- [ ] Rerun targeted tests and all Electron tests; record output. Real simultaneous-app update/Keychain validation remains Task 5. Review/commit checkpoint.

## Task 3: Login request binding contract and server implementation

**Files — modify (Web API):**

- `docs/api/openapi.yaml`
- `src/modules/auth/dto/auth-state.ts`
- `src/modules/auth/application/auth.service.ts` and `.spec.ts`
- `src/modules/auth/application/auth-session.service.ts` and `.spec.ts`
- `src/modules/auth/presentation/auth.controller.ts` and its existing specs
- `src/modules/auth/presentation/desktop-redirect.ts` and `.spec.ts`
- `src/modules/auth/presentation/dto/desktop-exchange.dto.ts`
- `src/modules/auth/domain/desktop-auth-code.model.ts`, `desktop-auth-codes.repository.ts`
- `src/modules/auth/infrastructure/desktop-auth-code.entity.ts`, `typeorm-desktop-auth-codes.repository.ts`
- `src/core/database/user.datasource.ts`

**Files — create (Web API):**

- `src/modules/auth/domain/desktop-login-policy.ts` and `.spec.ts`
- `src/modules/auth/infrastructure/typeorm-desktop-auth-codes.repository.spec.ts` if not already present
- `src/core/database/migrations/user/1789600000000-AddDesktopLoginBinding.ts` and `.spec.ts`

**Interfaces:**

```ts
export type DesktopTarget = 'development' | 'production';
export interface DesktopLoginBinding {
  desktopTarget: DesktopTarget;
  requestId: string; // random UUID; not authentication proof
  codeChallenge: string; // S256 base64url, 43 chars
}
export function desktopCallback(target: DesktopTarget): string {
  return target === 'development'
    ? 'clipperstudio-dev://auth/callback' : 'clipperstudio://auth/callback';
}
// issueDesktopAuthCode(user: User, binding: DesktopLoginBinding,
//   metadata?: AuthSessionClientMetadata): Promise<DesktopCodeIssue>
// exchange input adds desktopTarget, requestId, codeVerifier (43..128 chars).
// Repo adds consumePending(id: string, at: Date): Promise<boolean>.
```

- [ ] Define OpenAPI first: desktop `/auth/google` requires desktopTarget, requestId, codeChallenge, codeChallengeMethod=S256. `client=web` contract unchanged. Desktop exchange requires binding fields; raw token bundle response unchanged.
- [ ] Unit RED tests for `desktopCallback`, malformed target/requestId/challenge, target disallowed by server `DESKTOP_AUTH_TARGET=development|production`. Missing server target disables desktop login with configuration error; web login still works. Missing target in an old desktop request returns update-required error and never redirects to new app. Rejected custom returnUrl never falls back to clipper.

```ts
expect(desktopCallback('development')).toBe('clipperstudio-dev://auth/callback');
expect(desktopCallback('production')).toBe('clipperstudio://auth/callback');
```

- [ ] Run `npm test -- --runInBand --testPathPatterns='auth|desktop-login-policy'` from Web API and record RED.
- [ ] Sign desktop OAuth state with existing USER_JWT private key (RS256), `audience='clipper-desktop-oauth-state'`, `issuer='clipper-web-api'`, `typ='desktop-oauth-state'`, TTL 5m. Verify with public key, fixed algorithm/audience/type and strict decoded schema. Keep web flow encoding separate; reject invalid desktop state instead of falling through to web session issuance. JWT access-token verification must not accept this state token (different audience/type). Do not create/store an extra secret or use Google client secret as this signing key.
- [ ] Server selects only its configured target. Valid unpackaged returnUrl retains existing loopback host/port/path allowlist, packaged returnUrl omitted. Include requestId in completion URL and carry signed binding into code issuance.
- [ ] Add nullable `desktop_target`, `request_id`, `code_challenge` columns to desktop_auth_codes; keep existing users/sessions/financial data untouched. web_handoff rows use null. Legacy desktop rows without binding are rejected; no backfill that falsely makes them trusted. Register migration in user datasource only.

```sql
ALTER TABLE desktop_auth_codes
  ADD COLUMN desktop_target varchar NULL,
  ADD COLUMN request_id varchar NULL,
  ADD COLUMN code_challenge varchar NULL;
```

- [ ] At exchange validate target/requestId and SHA256(verifier) before consuming. Wrong proof must not mark code used or issue session. Constant-time compare normalized fixed-length challenge. Repo consume must be conditional/atomic:

```sql
UPDATE desktop_auth_codes SET used_at = $2
WHERE id = $1 AND used_at IS NULL AND expires_at > $2
RETURNING id;
```

- [ ] Two concurrent exchanges of the same code yield one success only. Consumed code/session-issuance failure means user restarts login, not automatic replay. Existing web_handoff behavior remains covered; do not broaden this task into a full session subsystem rewrite.
- [ ] Tests: modified/expired state, wrong audience, wrong target, malformed verifier, missing old binding, expired 60-second code, parallel exchanges, no session creation on any failure, web flow/handoff regression. Add migration SQL and entity mapping tests; build and full Jest. No live DB execution in this task. Review/commit checkpoint.

## Task 4: Electron initiator and callback proof

**Files — modify:** Electron `src/main/auth/google-login.ts`, `deeplink.ts`, `desktop-exchange.ts`, `loopback-callback-server.ts`, `log-redaction.ts`, `src/main/main.ts`; existing `test/auth-google-login.test.js`, `auth-deeplink.test.js`, `auth-desktop-exchange.test.js`, `auth-loopback-callback-server.test.js`, `auth-log-redaction.test.js`.

**Files — create:** `src/main/auth/pending-desktop-login.ts`, `test/pending-desktop-login.test.js`.

**Interfaces:**

```ts
type Target = 'development' | 'production';
type Attempt = { requestId:string; desktopTarget:Target; codeVerifier:string; codeChallenge:string; expiresAt:number };
// PendingDesktopLogin holds at most one attempt for this app process.
// begin(target: Target, now: number): Attempt
// take(requestId: string, target: Target, now: number): Attempt | null
// clear(): void
// LoopbackCallbackServer.waitForCode now returns {code:string, requestId:string}.
// exchangeDesktopAuthCode receives {code, requestId, desktopTarget, codeVerifier} + existing deps.
```

- [ ] Add RED unit test in new pending-desktop-login.test.js:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { PendingDesktopLogin } = require('../dist-electron/main/auth/pending-desktop-login');
test('different request cannot consume the active login', () => {
  const pending = new PendingDesktopLogin();
  const attempt = pending.begin('development', 1000);
  assert.equal(pending.take('other', 'development', 1001), null);
  assert.equal(pending.take(attempt.requestId, 'production', 1001), null);
  assert.equal(pending.take(attempt.requestId, 'development', 1001).codeVerifier, attempt.codeVerifier);
  assert.equal(pending.take(attempt.requestId, 'development', 1002), null);
});
```

- [ ] Build and run `node --test test/pending-desktop-login.test.js test/auth-google-login.test.js test/auth-deeplink.test.js test/auth-desktop-exchange.test.js test/auth-loopback-callback-server.test.js test/auth-log-redaction.test.js`; verify intended RED.
- [ ] Implement one process-local pending attempt, 5m timeout. `randomBytes(32).toString('base64url')` verifier and SHA256→base64url challenge; UUID requestId. New login replaces pending old login. Proof stays in main process memory, never renderer/log/URL/disk. URL carries only target/requestId/challenge/method.

```ts
const codeVerifier = randomBytes(32).toString('base64url');
const codeChallenge = createHash('sha256').update(codeVerifier, 'ascii').digest('base64url');
```

- [ ] Deep links require active profile scheme plus hostname `auth`, pathname `/callback`, no credentials/port/hash, one code and one requestId. Accept no query `token` fallback. Reject foreign schemes without changing tokens. For callback without pending attempt (app closed/restarted), show login-failed/retry state and do not exchange/store tokens.
- [ ] Loopback receiver returns code+requestId to same pending-attempt check. Packaged flow remains custom scheme; do not change packaged login to a loopback webserver. A failed/replayed/expired request must not overwrite existing account session.
- [ ] Exchange includes verifier/target/requestId, uses existing token-bundle validator and saves only successful response. On expiry/cancel/openExternal failure clear pending attempt; on unrequested callback leave other pending attempt intact. App logout clears pending attempt as well.
- [ ] Extend log redaction for verifier/challenge/state; compare redaction parity if Nest/renderer copy contracts require it, without logging secret fixtures. Rerun targeted tests, Electron full build/test, API auth tests. Review/commit checkpoint.

## Task 5: Template and co-install verification (not a new migration feature)

**Files — tests:** Nest `test/template-bundle-roundtrip.test.js`, `template-bundle-import-service.test.js`, `template-builder-import-fonts.test.js`, `template-builder-export-fonts.test.js`, `template-builder-store-flatten.test.js`.

**Evidence file — create at execution:** `.codex/implementation/2026-09-17-independent-dev-app-validation.md` (record date of actual execution if different).

- [ ] Run existing Nest template tests with fresh dist:

```sh
npm run build
node --test test/template-bundle-roundtrip.test.js test/template-bundle-import-service.test.js test/template-builder-import-fonts.test.js test/template-builder-export-fonts.test.js test/template-builder-store-flatten.test.js
```

- [ ] Add a disjoint-root assertion to existing roundtrip fixture, after `const a`/`const b` extraction. Confirm it would fail if importer leaves old absolute paths:

```js
assert.ok(a.startsWith(dataRoot + sep));
assert.ok(b.startsWith(dataRoot + sep));
assert.equal(a.startsWith(root + sep), false);
assert.equal(b.startsWith(root + sep), false);
```

- [ ] User exports representative templates from actually distributed old build: custom layout/background, embedded image, custom font, each used aspect ratio. If old build lacks export, stop migration sign-off and report missing capability; do not invent a whole-folder copy workaround.
- [ ] Import into new blank app root. Compare counts, layers, dimensions, asset bytes and permitted fonts; edit/save/restart. Skip/warnings/fallback fonts mean qualified result, not lossless success. If multivariant export loses variants, present exact affected sample and scoped fix before changing importer.
- [ ] macOS: new development + production concurrent start, separate PIDs/Nest ports/data/auth/modelcache/telemetry/outbox, one app logout/quit must not affect the other. Keep old dev installed at another path for protocol test. Query NSWorkspace for all three schemes, then exercise real browser login for new dev and production in both launch orders. Do not manually re-register away the old app to make the test pass.
- [ ] Windows user-run: NSIS installation directories/AppUserModelId/protocol registry/uninstaller isolated; install/upgrade/uninstall one app must not remove files or terminate processes of another. User reviews execution commands before running on Windows server; agent does not connect.
- [ ] Old-template export files and old userData remain intact. No oldqueue/job migration. Mark optional materials/projects transfer explicitly NOT IMPLEMENTED; not a release blocker if required templates pass.

## Review and handoff

- [ ] Compare all product diffs against task paths, build/test results, and spec exact strings. Record actual tests vs manual not-run separately.
- [ ] Update `.codex/handoff/tasks/app-window-name.md`, WORKBOARD, NEXT. No claim of production/development deployment.
- [ ] Continue to [release channel plan](2026-09-17-independent-dev-release-plan.md) within approved scope. Mac ZIP/update는 보류 기록으로 남기며 identity 작업의 차단 게이트로 삼지 않는다.
