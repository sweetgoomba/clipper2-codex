# Windows Packaging

Windows installer build, packaged smoke, and OS-specific build hazards are tracked here.

## Current Rules

- PowerToys `Command Palette` must be off during Windows build.
- `Keyboard Manager` can stay on.
- Do not reintroduce `win.asar: false`, electron-builder retry, or build script lock cleanup as the EBUSY fix.
- Prefer ASCII workspace path on Windows, for example `C:\project\adlight`.

## Active References

- [records/2026/05/21-powertoys-ebusy-diagnosis.md](records/2026/05/21-powertoys-ebusy-diagnosis.md)
- [runbooks/windows-build-guide.md](runbooks/windows-build-guide.md)
- [runbooks/windows-build-guide-configurable-root.md](runbooks/windows-build-guide-configurable-root.md)
