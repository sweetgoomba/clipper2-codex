# Codex Workspace

이 저장소는 Clipper2 작업 중 Codex가 읽고 갱신하는 설계, 구현 기록, 다음 세션 인계 문서다.

앱 소스 코드는 각 repo에 있고, 이 저장소는 판단과 작업 이력을 추적한다.

## 먼저 읽을 문서

1. [handoff/NEXT.md](handoff/NEXT.md)
2. [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
3. [README.RUNTIME.md](README.RUNTIME.md)
4. [README.OPERATIONS.md](README.OPERATIONS.md)
5. [README.DOCS.md](README.DOCS.md)

## Top-Level Guides

- [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
  - repo 역할, backend/frontend/process boundary, workflow capability 구조.
- [README.RUNTIME.md](README.RUNTIME.md)
  - `local` / `devapp` / `packaged`, env 파일 소유권, port/runtime 정책.
- [README.FRONTEND.md](README.FRONTEND.md)
  - Angular standalone/signal/component/style/event 기준.
- [README.OPERATIONS.md](README.OPERATIONS.md)
  - Windows packaging, PowerToys EBUSY, smoke, ffmpeg/model 설치 운영 기준.
- [README.DOCS.md](README.DOCS.md)
  - 이 저장소 문서 구조와 날짜별 기록 규칙.

## Domain Indexes

- [features/template-builder/README.md](features/template-builder/README.md)
- [features/dance-highlight/README.md](features/dance-highlight/README.md)
- [features/clipper-studio/README.md](features/clipper-studio/README.md)
- [operations/windows-packaging/README.md](operations/windows-packaging/README.md)
- [operations/env-runtime/README.md](operations/env-runtime/README.md)
- [records/README.md](records/README.md)

## Current Legacy Areas

아직 이관 중인 기존 폴더다. 새 문서는 가능하면 domain index 아래에 추가한다.

- `context/`: 프로젝트 히스토리와 현재 상태 배경.
- `design/`: 오래된 설계 초안과 아직 이관하지 않은 설계 문서.
- `implementation/`: 오래된 구현 계획, 체크포인트, runbook.
- `diagnostics/`: 긴 원인 분석 기록.
- `standards/`: 반복 적용할 개발/문서화 규칙.

`imports/`는 legacy asset / DB backup 성격이므로 git 추적에서 제외한다.

## Repo Notes

- 이 저장소는 `/Users/jina/project/adlight/.codex` 자체가 git root다.
- 원격은 `git@github.com-personal:sweetgoomba/clipper2-codex.git`.
- 기존 앱 repo와 별도로 commit/push한다.
