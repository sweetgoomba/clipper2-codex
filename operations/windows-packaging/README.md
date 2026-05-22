# Windows Packaging

Windows installer build, packaged smoke, and OS-specific build hazards are tracked here.

## Current Rules

- PowerToys `Command Palette` must be off during Windows build.
- `Keyboard Manager` can stay on.
- Do not reintroduce `win.asar: false`, electron-builder retry, or build script lock cleanup as the EBUSY fix.
- Prefer ASCII workspace path on Windows, for example `C:\project\adlight`.

## Active References

- [../../implementation/2026-05-21-windows-electron-builder-powertoys-ebusy-diagnosis.md](../../implementation/2026-05-21-windows-electron-builder-powertoys-ebusy-diagnosis.md)
- [../../implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_2026-05-20.md](../../implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_2026-05-20.md)
- [../../implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_CONFIGURABLE_ROOT_2026-05-20.md](../../implementation/CLIPPER2_WINDOWS_BUILD_GUIDE_CONFIGURABLE_ROOT_2026-05-20.md)
