# Codex Workspace

이 저장소는 Clipper2 작업 중 Codex가 읽고 갱신하는 설계, 구현 기록, 다음 세션 인계 문서다.

앱 소스 코드는 각 repo에 있고, 이 저장소는 판단과 작업 이력을 추적한다.

## Current Focus

2026-06-15 기준 현재 우선 작업은 shortform 제작 페이지의 템플릿/레이아웃/미리보기 라인이다. Template Builder 단순화와 Builder-created shortform template catalog 연결은 진행됐고, browser timeline preview engine 전에 Builder `template-builder.v1` shortform preset이 backend render recipe/provider path를 통과하도록 남은 blocker를 먼저 고친다.

먼저 [handoff/NEXT.md](handoff/NEXT.md), [design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md), [design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md](design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md), [records/sessions/2026/06/15.md](records/sessions/2026/06/15.md)를 본다.

Project-first / Plugin / Queue 정리는 아직 시작하지 않는다.

## 먼저 읽을 문서

1. [handoff/NEXT.md](handoff/NEXT.md)
2. [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
3. [README.RUNTIME.md](README.RUNTIME.md)
4. [README.OPERATIONS.md](README.OPERATIONS.md)
5. [README.DOCS.md](README.DOCS.md)

## Top-Level Guides

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
