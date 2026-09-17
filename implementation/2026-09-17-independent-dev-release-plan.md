# Independent Development Release Channel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, or superpowers:subagent-driven-development only after user choice. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 새 개발판을 `dev` 채널에서만 빌드·게시·조회하고, 운영/옛 개발판 채널에 잘못 공급하지 않는다.

**Architecture:** Web API가 build job에 앱 profile을 넣고 runner가 이를 실제 산출물과 대조한다. Artifact에 검증한 profile을 저장하며 서버가 게시/rollback/feed에서 검사한다. Admin은 선택한 대상만 요청하고 서버 검사를 대체하지 않는다.

**Tech Stack:** NestJS/TypeORM/Jest, Node ESM runner/node:test, Angular/Material/Jasmine.

**Spec:** [독립 개발판 설계](2026-09-17-independent-dev-identity-design.md). 앱 runtime 계약은 [앱·로그인 계획](2026-09-17-independent-dev-app-plan.md) Task 1–2.

## 2026-09-17 실행 체크포인트

- [x] Task 1–3 코드·자동 테스트·독립 리뷰 완료. [실행 증거와 미완료 게이트](2026-09-17-independent-dev-release-validation.md).
- [x] Web API build/2,882 PASS·21 SKIP, Infra 51 PASS·1 SKIP, Admin build/50 PASS. 코드와 문서는 미커밋.
- [x] 새 격리 DB 사용 승인 및 실제 migration/transaction 검증. [로컬 실DB 9 PASS](2026-09-17-independent-dev-real-db-validation.md), 기존 DB/실 env 미변경.
- [ ] 새 설치형 앱/Google 로그인/템플릿 이관/동시 실행/Windows 실기. 아래 review/commit checkpoint 중 commit은 사용자 별도 요청 전 실행하지 않는다.

## Global Constraints

- 기준 루트 `/Users/jina/project/adlight`, 원본 checkout `integration/dev-pg-local-validation-20260917`. Git 병합/checkout/push/배포 없음.
- 채널 union `stable | rc | alpha | dev`. 새 development profile은 dev에만 게시. production profile은 stable/rc/alpha 대상, runtime 기본 업데이트 채널은 stable 유지. 빌드 후보 채널과 앱 runtime 채널을 혼동하지 않는다.
- 서버 환경 `DESKTOP_RELEASE_TARGET=development|production` 필수. development 서버에서 새 stable/rc/alpha 빌드·게시·rollback 금지. production 서버에서 dev 대상 금지. NODE_ENV로 구분하지 않는다(개발 배포 컨테이너도 production 모드일 수 있음).
- 위 설정 미지정 시 읽기 전용 이력은 유지하되 신규 빌드/게시/rollback을 구성 오류로 차단한다. 기존 DB 레코드/설치파일 삭제 없음.
- 신규 작성 문서는 `.codex`에만. OpenAPI는 코드 계약 정본으로 API 저장소에서 변경.
- remote runner 실행/실제 업로드/다운로드/게시 금지. 테스트는 fake shell/HTTP/storage와 임시 디렉터리 사용.
- 커밋은 사용자 요청 시 단계별. Windows 실제 빌드/설치는 사용자 실행. ML/Build5 HOLD.

## 보류 항목 M1: Mac 자동 업데이트 파일 형식 — 이번 작업의 승인 게이트 아님

2026-09-17 사용자 지적 후 정정: [2026-09-09 기존 결정](2026-09-09-production-setup-log.md)의 Mac 공개·자동빌드·업데이트 구현 HOLD를 놓쳤다. ZIP 생성/게시를 이번 필수 확장으로 제시한 것은 잘못이다. 기존 보류 유지, 이번 구현 범위에서 ZIP 지원 제외. Mac 업데이트 URL은 경로 설계 참고값이지 활성화 또는 구현 재개 승인이 아니다.

현재 원본 dist-app의 Mac 개발 앱 및 build/generated의 packaged-runtime-config.json은 `autoUpdateDisabled: true`, API `http://127.0.0.1:3000` 확인. 현재 소스는 macOS 전체를 무조건 제외하지 않고 disabled 환경값으로 판정하므로 모든 배포 Mac 앱까지 꺼져 있다고 단정하지 않는다. 실제 배포 설정/서버 DB 상태는 미조회. 후속 Mac 빌드에서도 비활성 유지 여부를 검증하며 업데이트를 임의 활성화하지 않는다.

현재 builder는 DMG만 생성, runner는 단일 `.dmg`을 보고, 서버 latest-mac.yml은 그 URL을 내보낸다. 설치된 electron-updater 6.8.9의 MacUpdater는 `findFile(files, 'zip', ['pkg','dmg'])` 결과가 없으면 `ERR_UPDATER_ZIP_FILE_NOT_FOUND`를 발생시킨다.

2026-09-17 읽기 전용 Node 검증: DMG-only 입력→undefined, DMG+ZIP 입력→ZIP 선택. 네트워크/설치/업데이트 실행 없음. 이 상태에서 아래 채널 변경만 해서는 Mac 자동 업데이트 완료가 아니다.

**향후 사용자가 Mac 자동 업데이트를 재개할 때 검토할 범위:** 수동 설치용 DMG 유지 + 자동 업데이트용 ZIP 생성·동반 업로드·별도 URL/해시/크기 저장 + latest-mac.yml의 ZIP 참조. 지금은 구현하지 않으며 이 결정을 위해 다른 승인된 앱 분리 작업을 막지 않는다. Windows EXE 계약은 보존. 아래 task의 Mac 테스트는 경로/비활성 경계만 검사하며 Mac 자동빌드·업데이트 설치를 실행하지 않는다.

## Task 1: Server channel/profile contract and publication guard

**Modify — Web API paths:**

- `src/modules/releases/domain/release.model.ts`
- `src/modules/releases/application/releases.service.ts`
- `src/modules/releases/presentation/dto/start-build.dto.ts`, `publish-artifact.dto.ts`, `release-update-feed-params.dto.ts`, `report-runner-job.dto.ts`
- `src/modules/releases/infrastructure/typeorm-releases.repository.ts`, `typeorm-release-runner.repository.ts`, `release-artifact.entity.ts`
- `src/modules/releases/application/release-update-feed.service.ts`
- `src/core/database/release.datasource.ts`
- `docs/api/openapi.yaml`

**Create — Web API:**

- `src/modules/releases/domain/desktop-release-policy.ts` and `.spec.ts`
- `src/modules/releases/infrastructure/typeorm-releases.repository.spec.ts` if absent
- `src/modules/releases/infrastructure/typeorm-release-runner.repository.spec.ts` if absent
- `src/core/database/migrations/release/1789600000000-AddArtifactDesktopProfile.ts` and `.spec.ts`

**Contract:**

```ts
export type DesktopReleaseIdentity = 'development' | 'production';
export interface DesktopBuildProfile {
  identity: DesktopReleaseIdentity;
  appId: string;
  protocol: string;
  updateChannel: 'dev' | 'stable';
  webApiBaseUrl: string;
}
export function profileForChannel(channel: 'dev'|'stable'|'rc'|'alpha'): DesktopBuildProfile {
  return channel === 'dev'
    ? { identity:'development', appId:'ai.clipperstudio.dev', protocol:'clipperstudio-dev', updateChannel:'dev', webApiBaseUrl:'https://dev-api.clipperstudio.ai' }
    : { identity:'production', appId:'ai.clipperstudio.app', protocol:'clipperstudio', updateChannel:'stable', webApiBaseUrl:'https://api.clipperstudio.ai' };
}
// ReleaseRunnerJobPayload adds desktopProfile: DesktopBuildProfile.
// ReleaseArtifactRecord/report adds desktopProfile: DesktopBuildProfile | null (history); new reports require non-null.
// canPublishDesktopProfile(profile: DesktopBuildProfile|null,
//   channel: ReleaseChannelName, serverIdentity: DesktopReleaseIdentity): boolean
```

- [x] Add OpenAPI enum `dev`, job payload/report profile schema and strict DTO validation first. No raw response envelope change.
- [x] Add policy RED tests:

```ts
const dev = profileForChannel('dev');
const prod = profileForChannel('rc');
expect(canPublishDesktopProfile(dev, 'dev', 'development')).toBe(true);
expect(canPublishDesktopProfile(dev, 'stable', 'development')).toBe(false);
expect(canPublishDesktopProfile(prod, 'dev', 'production')).toBe(false);
expect(canPublishDesktopProfile(prod, 'stable', 'production')).toBe(true);
expect(canPublishDesktopProfile(null, 'dev', 'development')).toBe(false);
expect(canPublishDesktopProfile({ ...dev, appId:prod.appId }, 'dev', 'development')).toBe(false);
```

- [x] Run from Web API `npm test -- --runInBand --testPathPatterns='desktop-release-policy|releases|release-update-feed'`; confirm intended failure.
- [x] Implement equality of all five profile fields to `profileForChannel(channel)` plus server identity match. Do not infer profile from filename or populate historical rows based on channel alone: old dev used stable.
- [x] Add nullable JSONB column `desktop_profile` to release_artifacts; migration adds only that column, no history deletion/backfill. Map entity/repository/console DTO. Channel storage itself remains varchar.

```sql
ALTER TABLE release_artifacts ADD COLUMN desktop_profile jsonb NULL;
```

- [x] Add job.desktopProfile from server policy when build job is created. Before success report transaction changes job/build status or writes artifact, validate report profile equals job profile. A mismatched report writes no success state.
- [x] New publish and rollback transactions use the same profile guard; compare rollback artifact instead of trusting target channel. Concurrent mutation must hold row locks for selected target/build data and rollback pointer swap. Wrong profile leaves currentArtifactId/rollbackArtifactId untouched.
- [x] Feed guard: dev requires validated dev profile; profile mismatch returns no update. Historical null-profile records are never newly published or used for rollback. Do not automatically classify/modify existing published null-profile stable targets; keep their current read behavior outside dev channel until deployment review explicitly decides their disposition. This is preservation of existing targets, not an old desktop API compatibility layer.
- [x] Mock repository tests assert no mutation on rejected report/publish/rollback, positive production rc→stable and development dev→dev, distinct platform/arch targets, dev feed never falls back to stable. Record historical stable treatment as deployment check, not verified production state.
- [x] Run fresh Web API build + full Jest. Migration SQL tests only here; no implicit DB connection/migration. Review complete; commit not executed.

## Task 2: Runner profile propagation and built-bundle verification

**Modify — Infra:** `runner/release-runner.mjs`, `runner/release-runner.test.mjs`, `runner/release-runner-server.test.mjs`, `runner/job-sources.test.mjs`, `runner/local-artifact.test.mjs`, `runner/env/release-runner.dev.env.example`, `runner/env/release-runner.prod.env.example`.

**Create — Infra:** `runner/desktop-build-profile.mjs`, `runner/desktop-build-profile.test.mjs`.

**Interfaces:** `assertDesktopBuildProfile(expected, actual): void` compares all five profile fields; throws before upload on mismatch. `releaseBuildEnv(job)` consumes job.payload.desktopProfile; new success report adds the profile read/verified from built output, not copied blindly from job.

- [x] Add RED to release-runner.test.mjs using a full existing job fixture with added profile:

```js
const env = releaseBuildEnv({ payload: {
  buildNumber:1, artifactVersion:'1.0.0.1', sourceRevisions:[],
  desktopProfile:{ identity:'development', appId:'ai.clipperstudio.dev', protocol:'clipperstudio-dev', updateChannel:'dev', webApiBaseUrl:'https://dev-api.clipperstudio.ai' },
} }, {});
assert.equal(env.CLIPPER_DESKTOP_ENVIRONMENT, 'dev');
assert.equal(env.CLIPPER_DESKTOP_API_BASE_URL, 'https://dev-api.clipperstudio.ai');
assert.equal(env.CLIPPER_UPDATE_CHANNEL, 'dev');
```

- [x] Run from Infra `node --test runner/release-runner.test.mjs runner/release-runner-server.test.mjs runner/job-sources.test.mjs runner/local-artifact.test.mjs runner/desktop-build-profile.test.mjs`. No real remote source checkout, npm installation or AWS upload. Existing snapshot tests use temporary local Git clone fixtures; this is not a deployment runner execution.
- [x] Add profile-derived env to whitelist while preserving telemetry/build-number/sourceCommit fields. Missing/invalid profile fails before expensive build. Production env=prod; dev env=dev. Runner ambient env must not override job profile.

```js
CLIPPER_DESKTOP_ENVIRONMENT: job.payload.desktopProfile.identity === 'production' ? 'prod' : 'dev',
CLIPPER_DESKTOP_API_BASE_URL: job.payload.desktopProfile.webApiBaseUrl,
CLIPPER_UPDATE_CHANNEL: job.payload.desktopProfile.updateChannel,
```

- [x] After build, read output resources/packaged-runtime-config.json (not build/generated input). On Mac compare final `.app/Contents/Info.plist` bundle ID and URLTypes; on Windows compare effective builder appId/protocol settings and packaged runtime. Static fixture checks implemented; actual installed registry remains in the user-run smoke gate below.
- [x] Verify final installer belongs to this isolated job output and matches collected file hash/size; profile verification evidence accompanies success report. Stop upload on mismatched runtime, absent config or stale output. Unit tests inject file fixtures/fake shell and assert AWS command is not called on mismatch.
- [x] Keep telemetry/public-key/source snapshot handling unchanged. Test source app config restoration on failure. M1 governs adding Mac ZIP; do not silently extend installerKind to zip in this task.
- [x] Run targeted test command and record result. Review complete; commit not executed.

## Task 3: Admin build/publish UI and deployment examples

**Modify — Admin:**

- `src/app/features/portal/versions/models/version-console.models.ts`, `.helpers.ts`, `.selectors.ts`, `.mappers.ts`
- `src/app/features/portal/versions/services/version-console.store.ts`, `version-console-api.models.ts`, `version-console-api.service.ts`
- `src/app/features/portal/versions/versions.component.ts`, `.html`, `.spec.ts`
- `src/app/features/portal/versions/components/version-installation-files-section/version-installation-files-section.component.ts`, `.html`, `.spec.ts`
- `src/app/features/portal/versions/data/version-console.mock.ts`
- Existing models `.helpers.spec.ts`, `.selectors.spec.ts`; create `services/version-console.store.spec.ts` if absent.

**Modify — Infra/API:** `web/clipper_infra/apps/compose.yml`, `web/clipper_infra/env/stack.dev.env.example`, `stack.prod.env.example`, `stack.stage.env.example`, API `.env.example` (never real .env).

**Interfaces:** remove `publishArtifactToStable`; use `publishArtifact(artifactId: string, channel: ReleaseChannelName): void`. `startWindowsBuildForSelectedRelease(channel: ReleaseChannelName)` receives actual selection, no hidden rc default. Publish event emits `{artifactId, channel}`; selectors expose deployed channel rather than stable-only boolean. API client keeps raw endpoints.

- [x] Extend model union and mock before changing templates. Add RED helpers test:

```ts
expect(targetLabel('dev')).toBe('개발 배포');
expect(targetLabel('stable')).toBe('정식 배포');
```

- [x] Store test with HttpClient mock: dev publish sends `{channel:'dev'}`, production promotion sends `{channel:'stable'}`. Dev selection cannot call stable behind the scenes; rejected server response stays visible and does not show success.
- [x] Run from Admin `npm test -- --watch=false --browsers=ChromeHeadless --include='src/app/features/portal/versions/**/*.spec.ts'`; note environment/browser failure separately from assertion failures.
- [x] Replace fixed confirmation copy with actual target name/platform/arch/version. For verified dev artifact only dev is enabled; production artifact allows valid production destinations. Null-profile history can be viewed but not newly published. No new generic form framework/style system.

```html
<!-- Confirmation data comes from selected artifact + explicit selected channel. -->
<p>{{ publishTargetLabel }} 대상으로 게시할까요?</p>
```

- [x] Pass `DESKTOP_AUTH_TARGET`, `DESKTOP_RELEASE_TARGET` through compose. dev example=development, prod=production. stage example documents explicit target configuration but leaves it unset (desktop login/publication disabled) until its deployment purpose is selected; do not infer stage identity/API. Remove obsolete DESKTOP_REDIRECT fallback only after all active code consumers are replaced. Explain any remaining unrelated consumers rather than deleting blindly.
- [x] Retest Admin/build and Web API DTO/OpenAPI/report contract. Review complete; commit not executed.
- [ ] Local browser smoke with an actual isolated API/DB (ChromeHeadless component tests used mocked HTTP). Never publish remotely.

## Verification and deployment gates

- [x] Profile/channel routing unit tests pass for Mac ARM64 + Windows x64. Mac updater 비활성 유지 검증; 실제 Mac 업데이트 및 ZIP 구현은 HOLD, 이번 통과 조건 아님.
- [x] One fresh isolated PostgreSQL fixture checks new nullable profile schema, valid dev publish, invalid stable promotion, rollback rejection and separate production fixture. User approved local-only containers 58433–58435; 9 real-DB tests pass. Existing dev/production DB unchanged. See the real-DB validation record for first-run versus repeat evidence.
- [ ] Mac 수동 설치/동시 실행과 Windows 설치/업데이트 증거를 구분한다. Mac 자동 업데이트 실기는 HOLD. 이 계획은 signing keys/remote runners 접근 권한을 주지 않는다.
- [ ] Legacy dev stable target inventory is read by user-run server commands at deployment planning. No automatic clearing/deletion/backfill. Explicitly decide whether to freeze/disable old feed at that gate.
- [x] Update WORKBOARD/task handoff with M1 decision and per-platform actual evidence. Plan execution is separate from merge/push/deploy approvals.
