# Release Coordinator correctness design

Date: 2026-09-18 KST

> **후속 완료 상태:** 아래 설계 뒤 runner module 누락과 effective config 위치 가정도 수정했고 Windows Build54 `0.0.35.54`가 성공했다. 개발 정식 배포 대상과 공개 다운로드/update feed는 0.0.35를 반환한다. 최신 결과와 남은 설치 실기는 [PG 통합 종료 감사](2026-09-18-pg-integration-closeout-and-remaining-work.md)를 우선한다. 아래 Build53 기대 문구는 설계 당시 기록이다.

## Problem

The first real development Windows build after the independent desktop identity cutover exposed three coupled defects.

1. Admin asks an operator to choose among `dev`, `stable`, `rc`, and `alpha` even though the API server already has an explicit `DESKTOP_RELEASE_TARGET`. The development server accepts only `dev`; the production server accepts only production channels.
2. `startWindowsBuildForSelectedRelease()` silently falls back from the selected release to another snapshotted candidate. In addition, the displayed coordinator state is stored separately from `selectedReleaseId`, so the visible target and the release ID sent to the API can diverge. Build 52 was consequently recorded as `0.0.33.52` with `snapshot-20260914T234620Z` while the operator saw 0.0.34.
3. The development Windows runner runs `npm ci` in the shared host checkout. A previous process held `clipper_angular/node_modules/@esbuild/win32-x64/esbuild.exe`, causing `EPERM unlink` and blocking Build 52.

## Decisions

### Server-derived build channel

The build-start request no longer accepts a channel from Admin.

- `DESKTOP_RELEASE_TARGET=development` derives build channel `dev`.
- `DESKTOP_RELEASE_TARGET=production` derives build channel `rc`.
- `stable`, `rc`, and `alpha` remain explicit publication targets after a production artifact has been built and verified.
- The runtime updater channel remains a separate concept: a development binary reads the `dev` feed and a production binary reads the `stable` feed. `rc` and `alpha` are publication lanes, not different installed-app identities.

The console response exposes the derived channel as read-only coordinator data so the button can say what will be built without asking the operator to choose an invalid value.

### Exact selected release only

- Coordinator presentation is computed from current `releases`, server coordinator data, and `selectedReleaseId`; it is not an independently stale copy.
- Creating or freezing a release selects that exact release.
- Build start uses only the selected release. If it is missing or has no frozen source snapshot, no HTTP mutation occurs and Admin shows an error.
- The candidate fallback is removed.
- The button is disabled unless the exact selected release is buildable.

Failed Build 52 stays as immutable audit history. The next valid 0.0.34 build consumes the next sequence number and is expected to be `0.0.34.53`, not a rewritten Build 52.

### Per-job development runner workspace

Every Windows runner environment, including `dev`, receives a work root and archive root. The runner clones the five frozen source revisions into a new job directory and runs dependency installation there. No job runs `npm ci` against the shared host checkout or shared `node_modules`.

The Windows container must be recreated from the updated infra code; restarting an existing container is insufficient because runner code and environment are captured at container creation.

After the API, Admin, and Infra commits are merged into `dev` and the development API/Admin are deployed, recreate the Windows development runner from its existing workspace:

```powershell
cd C:\workspace\clipper\web\clipper_infra
runner\windows\start-windows-runner-container.cmd
curl http://localhost:19029/health
```

If that machine's checkout root is not `C:\workspace\clipper`, run the same wrapper from its actual `web\clipper_infra` directory. The wrapper pulls Infra `dev`, prepares the environment, removes and recreates the non-production container, and starts the updated image. The next operator action is to select release 0.0.34 and start Windows build. Expected evidence is Build 53 attached to release 0.0.34, channel `dev`, display version `0.0.34-dev.53`, artifact version `0.0.34.53`, the intended frozen snapshot ID, and job-local paths under `C:\runner-work`.

## Verification

- Admin tests prove there is no build-channel selector, the request body contains no hidden channel, the displayed release follows selection, and an unsnapshotted selection never falls back.
- API tests prove development derives `dev`, production derives `rc`, and client-supplied channels are not part of the build-start contract.
- Infra tests prove dev and prod runner invocations both set isolated work/archive roots and that source preparation uses job-local paths.
- Existing Admin, API releases, and runner suites remain green.
- A user-run Windows smoke build after container recreation must show job-local paths rather than `C:\workspace\clipper\...\node_modules` and must produce the selected release version/snapshot.

## Snapshot audit

Release 0.0.34 froze `snapshot-20260918T010011Z` with the five supplied commits. They were valid `dev` commits and remain ancestors of current `origin/dev`. A fresh fetch on 2026-09-18 later found Angular, Electron, and NestJS had advanced; Python and Web API still matched. The frozen snapshot is internally valid and represents the remote state captured at that time, but it is intentionally immutable and is no longer identical to the later current `dev` heads.

| Repository | Frozen revision | Current `origin/dev` at audit | Result |
| --- | --- | --- | --- |
| `clipper_angular` | `9dc31ec15da498fcd231132395491b0ffff9f500` | `428ed1f95483a3b7dd7a534360ed7e8259043fb2` | frozen revision is an ancestor; 37 graph commits behind |
| `clipper_electron` | `d95c05058439a8be5c08d34ee3cb9890b2005b35` | `3fca00b6a9e91ecb304333b45ca1f3443d4df7d1` | frozen revision is an ancestor; 3 graph commits behind |
| `clipper_nestjs` | `884fa8bc7abf5d802a142c918568d8e606041900` | `1adb62fc50119a96f22d3bc9ee62600588477dab` | frozen revision is an ancestor; 17 graph commits behind |
| `clipper_python` | `60417ce865499df519971650a43a7ca1a82d9867` | same | exact match |
| `clipper_web_api` | `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f` | same | exact match |

The snapshot ID time is 2026-09-18 10:00:11 KST. The later Angular, Electron, and NestJS merge heads are timestamped 10:14, 10:51, and 10:48 KST respectively, which is consistent with those repositories advancing after the snapshot was frozen.
