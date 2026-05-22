# Operations Notes

빌드, 패키징, 설치 asset, smoke 확인을 위한 기준 문서다.

## Windows Packaging Rules

- Windows build 중 PowerToys `Command Palette`를 끈다.
- `Keyboard Manager`는 사용해도 된다.
- PowerToys `Command Palette`가 `Clipper2.exe`를 잡아 electron-builder Step 5에서 `EBUSY`가 날 수 있다.
- 이 문제를 해결하려고 `win.asar: false`, electron-builder retry, lock cleanup/fail-fast를 다시 넣지 않는다.

## Install Asset Rules

- ffmpeg/ffprobe는 Electron download IPC가 준비 상태를 관리한다.
- Template Builder는 sample render와 text preview worker warm-up 때문에 진입 전에 ffmpeg/ffprobe readiness를 확인한다.
- plugin model install state는 marker 파일보다 실제 model file presence가 source of truth다.

## Current References

- [operations/windows-packaging/README.md](operations/windows-packaging/README.md)
- [operations/env-runtime/README.md](operations/env-runtime/README.md)
- [operations/windows-packaging/records/2026/05/21-powertoys-ebusy-diagnosis.md](operations/windows-packaging/records/2026/05/21-powertoys-ebusy-diagnosis.md)
- [implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md](implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md)
