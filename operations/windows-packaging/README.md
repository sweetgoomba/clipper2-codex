# Windows Packaging

Windows installer build, packaged smoke, and OS-specific build hazards are tracked here.

## Current Release Runner Status

- 2026-07-10: app identity was reset around `Clipper Studio`, dev release DB was reset, and Windows 0.0.1 remote build/sign/upload/stable target flow was verified.
- 2026-07-10: packaged Windows JWT auth now requires the packaged user JWT public key resource and packaged NestJS `jwt` mode env to be prepared by the runner env script.
- 2026-07-10: runner token/start-token mismatch caused source snapshot 401; runner env preparation now passes both explicitly. Do not document token values.
- 2026-06-29: Windows 10 Pro runner candidate verified for Windows containers.
- 2026-06-30: direct Windows runner flow was merged to `dev` across
  `web/clipper_infra`, `web/clipper_web_api`, and `web/clipper_web_admin`.
- 2026-06-30: m2-stage and Windows runner PC were updated to `dev`; m2-db
  `clipper_infra` checkout was also switched to `dev`.
- 2026-06-30: Windows runner container build/sign/report passed in dry-run
  upload mode. Artifact status is `local_verified`, signature status is
  `signed`, and upload timestamp is empty until real S3 upload is enabled.
- Docker Desktop must be installed in all-users mode with Windows containers enabled.
- Windows 10 Pro 19045 uses `mcr.microsoft.com/windows/servercore:ltsc2019`; `ltsc2022` did not match this host.
- CodeSignTool must be mounted read-only from host, copied to a writable container path, then executed.
- Docker container actual SSL.com signing was verified and Authenticode status was `Valid`.
- Current runner output workaround keeps electron-builder output inside the
  container at `C:\runner-output\dist-app`. Official
  `desktop/clipper_electron/scripts/build-app.mjs --output-dir` support is a
  next-session item.
- Real S3 upload is not enabled yet. Keep secret values in mounted env files,
  not in docs or committed files.

Detailed runbook:

- [release-runner-docker-codesign-2026-06-29.md](release-runner-docker-codesign-2026-06-29.md)

Latest session record:

- [../../records/sessions/2026/07/10.md](../../records/sessions/2026/07/10.md)
- [../../records/sessions/2026/06/30.md](../../records/sessions/2026/06/30.md)

## Current Rules

- PowerToys `Command Palette` must be off during Windows build.
- `Keyboard Manager` can stay on.
- Do not reintroduce `win.asar: false`, electron-builder retry, or build script lock cleanup as the EBUSY fix.
- Prefer ASCII workspace path on Windows, for example `C:\project\adlight` or `C:\Users\Metabuzz00\Desktop\project\clipper`.
- Build with Node 22.x. Node 24 is not the runner baseline.
- If electron-builder fails extracting `winCodeSign` with symlink errors, run elevated/admin or enable Developer Mode, then clear the corrupted cache.

## Active References

- [records/2026/07/10-windows-runner-dev-release.md](records/2026/07/10-windows-runner-dev-release.md)
- [records/2026/05/21-powertoys-ebusy-diagnosis.md](records/2026/05/21-powertoys-ebusy-diagnosis.md)
- [runbooks/windows-build-guide.md](runbooks/windows-build-guide.md)
- [runbooks/windows-build-guide-configurable-root.md](runbooks/windows-build-guide-configurable-root.md)
