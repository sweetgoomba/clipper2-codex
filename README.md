# Codex Workspace

이 저장소는 Clipper2 작업 중 Codex가 읽고 갱신하는 설계, 구현 기록, 다음 세션 인계 문서다.

앱 소스 코드는 각 repo에 있고, 이 저장소는 판단과 작업 이력을 추적한다.

## Current Repo Layout

2026-06-23 기준 `/Users/jina/project/adlight` 루트 자체는 git repo가 아니다.
앱 소스는 하위 repo로 나뉘고, 모든 active app repo의 기본 작업 브랜치는 `dev`다.

```text
desktop/
  clipper_angular/
  clipper_nestjs/
  clipper_python/
  clipper_electron/

web/
  clipper_infra/
  clipper_web_client/
  clipper_web_api/
  clipper_web_admin/

legacy/
  adlight_python/
  adlight_angular/
  adlight_nestjs/
```

작업은 각 repo에서 새 브랜치를 만들고 검증 후 `dev`에 merge한다. `.codex`는
별도 문서 repo이며 앱 코드 repo와 commit을 섞지 않는다.

과거 session record와 archive 문서에는 경로 이동 전의
`/Users/jina/project/adlight/clipper_*` 또는 `adlight_*` 절대 경로가 남아 있을 수 있다.
새 작업과 현재 runbook에서는 위 새 경로를 기준으로 한다.

## Current Focus

2026-06-23 기준 현재 첫 작업은 `desktop/*` 4개 repo의 plugin/runtime process
memory pressure와 lifecycle cleanup이다. 여러 plugin/runtime을 연달아 실행할 때
메모리 부족으로 Clipper2 앱 또는 다른 앱까지 freeze되는 문제를 줄이는 방향이다.

1차 구현은 `desktop/clipper_nestjs` `feature/plugin-runtime-memory-management`
브랜치의 `a978ea7 feat(plugin-runtime): add Python runtime lifecycle policy`에 있다.
이 구현은 완료 판정 전 단계다. 다음 세션에서는 실제 local/devapp/packaged runtime에서
idle peer process 종료, `/health active_jobs`, Electron-hosted child process stop 동작을
먼저 검증한다.

먼저 [handoff/NEXT.md](handoff/NEXT.md),
[design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md),
[records/sessions/2026/06/19.md](records/sessions/2026/06/19.md),
[design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md](design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md)를 본다.

Project-first / Plugin / Queue 대정리는 아직 별도 작업으로 둔다.

## Current Design Notes

- [design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md)
  - plugin/runtime memory pressure 완화를 위한 2026-06-23 초기 구현 상태 문서다.
  - `PythonRuntimeLifecyclePolicy`의 현재 범위, env 옵션, 검증 결과, 아직 실제 앱에서
    확인해야 할 runtime gap을 정리했다.
  - 완료 문서가 아니라 다음 세션의 이어받기 기준이다.
- [design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md](design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md)
  - `web/clipper_web_admin` 앱 버전 관리 mock 화면(`/versions`, `/versions2`) 비교 문서다.
  - 최종 방식은 아직 확정하지 않는다. 공통 제품 버전과 OS별 artifact 배포 현실을 분리해서 본다.
  - Windows 코드서명 준비 완료, macOS 공증/서명 미완료 및 `xattr` 수동 안내 상황 때문에 `/versions2`가 더 정직하게 느껴지는 이유도 기록했다.
  - 다음 설계에서는 release보다 artifact provenance를 1차 진실로 두는 방안을 우선 검토한다.

## 먼저 읽을 문서

1. [handoff/NEXT.md](handoff/NEXT.md)
2. [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
3. [README.RUNTIME.md](README.RUNTIME.md)
4. [README.OPERATIONS.md](README.OPERATIONS.md)
5. [README.DOCS.md](README.DOCS.md)

## Top-Level Guides

- [standards/GIT_COMMIT_MESSAGE_POLICY.md](standards/GIT_COMMIT_MESSAGE_POLICY.md)
  - 모든 app repo와 `.codex` repo 커밋 메시지는 Conventional Commit 형식을 따른다.
  - type 없는 `Add ...`, `Remove ...`, `Update ...` 메시지는 금지한다.
- [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
  - repo 역할, backend/frontend/process boundary, plugin/project 구조.
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

## Current Product Terms

- [design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
  - 2026-06-11 확정 기준. 유저에게 노출되는 핵심 개념은 `플러그인`과 `프로젝트`다.
  - `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 사용자 플러그인이다.
  - 큐/보관함의 사용자 단위는 `Project`이며, 기존 `workflow`/`job`은 현재 코드와 내부 실행 설명에서만 사용한다.
- [design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)
  - 위 제품 용어 기준을 코드에 반영하기 위한 Phase 1 구현 계획이다.

## Current UI References

- [design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
  - 2026-06-12 확정된 Template Builder 단순화와 숏폼 제작 템플릿/미리보기 방향.
  - 새 템플릿은 `main_title1`, `main_title2`, `caption`만 사용하고, ratio는 `1:1` 또는 `4:3` 단일 ratio다.
- [design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)
  - Clipper2 앱 전체의 모달/오버레이 사용처와 shared confirmation modal 교체 후보를 정리한 인벤토리다.

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
