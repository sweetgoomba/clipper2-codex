# Codex Workspace Notes

이 폴더는 Codex와 진행하는 Clipper2 설계/구현 기록의 기준점이다. `.claude/` 문서를 대체하지 않고, Codex가 읽고 보완한 판단과 구현 이력을 별도로 누적한다.

## 구조

```text
.codex/
  context/          # 프로젝트 히스토리, 현재 상태, 레거시 이해
  design/           # 아키텍처/기능 설계, 대안 비교, 결정 전 초안
  implementation/   # 실제 구현 작업 추적, 작업 로그, 다음 세션 인계
  session-logs/     # 날짜별 Codex session log
  standards/        # SOLID, 경계 분리, 문서화 규칙 등 작업 원칙
```

## 주요 문서

### Context

- `context/PROJECT_HISTORY_AND_STATUS.md`
  - `adlight_*` 레거시에서 현재 `clipper_*` 구조까지의 변천사
  - 현재 기준 아키텍처, 폐기된 결정, 남은 작업의 배경

### Design

- `design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
  - 현재 Clipper1/Variation 재설계의 우선 기준 문서
  - Clipper1 plugin과 Variation plugin을 분리하고, 내부는 Shared Shortform Core로 통합하는 방향
  - `CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`의 이전 prompt-only Clipper Studio 화면 방향을 대체

- `design/LEGACY_CLIPPER1_TEMPLATE_SYSTEM_2026-05-06.md`
  - `adlight_angular`/`adlight_python` `feature/d2x-electron` 기준 원래 Clipper1 템플릿 구조 분석
  - template row/settings JSONB, Angular preview/edit UI, Python FFmpeg renderer 적용 순서, legacy 불일치와 Clipper2 migration 기준

- `design/TEMPLATE_BUILDER_DESIGN_BRIEF_2026-05-06.md`
  - Clipper2 top-level 템플릿 생성기 설계 brief
  - legacy Clipper1 출력 호환성, Shared Template Catalog, system/custom 분리, ratio variant, draft/published lifecycle, editor v4 요구사항

- `design/TEMPLATE_BUILDER_APPROVED_SPEC_2026-05-07.md`
  - 사용자 승인된 Template Builder v4 방향의 구현 전 spec
  - UI 구조, data model, repository boundary, lifecycle, validation/sample render publish gate, 테스트 전략

- `design/PLUGIN_STORE_DASHBOARD_REVIEW.md`
  - 기존 `.claude/PLUGIN_STORE_DASHBOARD_DESIGN.md`에 대한 설계 피드백
  - 실제 코드와 맞지 않는 부분, 구현 위험 지점

- `design/PLUGIN_STORE_DASHBOARD_SPEC.md`
  - 플러그인 스토어/대시보드 보완 설계
  - IPC 계약, 상태 모델, Electron/Angular 구현 기준

- `design/CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`
  - 현재 Clipper2 구조와 Pipeline Queue / Project Orchestration 초안
  - 주의: Electron 중심 queue 초안이며, NestJS 중심 재설계로 개정 필요 표시됨

- `design/NESTJS_CONTROL_PLANE_REDESIGN.md`
  - NestJS를 메인 앱 백엔드/control plane으로 복원하는 수정 설계
  - Angular -> NestJS -> FastAPI plugin 흐름
  - Electron을 desktop host/native adapter로 제한하는 실행 모드별 구조

- `design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
  - Workflow Plugin / Shared Capability / Provider / Resource 계층 구분
  - 플러그인 리소스 모니터링, manifest resource metadata, Clipper1 capability 분해 원칙

- `design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
  - 사용자 실행 Workflow Plugin과 공통 Shared Capability를 분리하는 현재 기준 설계
  - YouTube 입력, 템플릿 공통화, Clipper1 편입을 위한 단계별 변경 계획

- `design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
  - Clipper1/D2X endpoint/service/template/media/TTS/render/project output inventory
  - Clipper1을 giant plugin이 아니라 shared capability layer로 분해하는 설계
  - `ProjectManifest`, workflow별 artifact detail, `TemplatePreset`, `RenderRecipe` 초안

- `design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`
  - 이전 `workflow.clipper_studio` 1차 설계
  - 주의: 현재 사용자-facing Clipper1/Variation 제품 방향은 `SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`를 우선한다.

- `design/WINDOWS_CUDA_RUNTIME_STRATEGY.md`
  - Windows CUDA/VRAM telemetry와 CUDA runtime 배포 전략
  - CPU fallback, CUDA profile, provider probe, hard admission 승격 기준

- `design/BACKEND_ROLE_SPLIT_CURRENT.md`
  - 현재 NestJS/FastAPI/Electron/Angular 역할 분리 기준
  - Clipper1 Phase 1 구현에서 각 계층이 맡은 책임

- `design/2026-05-21-execution-env-mode-design.md`
  - `local`/`devapp`/`packaged` 실행 모드와 repo별 env 파일 소유권 기준
  - packaged에서 `.env.local` copy/read 금지, `.env.packaged`만 resources 포함
  - plugin별 고정 포트 금지, runtime port pool 기반 동적 할당
  - NestJS control plane / Electron desktop host-native adapter 역할 정리
  - Template Builder official DB 필수 정책과 env schema 정리 결과

### Implementation

- `implementation/TASKS.md`
  - 현재 구현 목표, 단계별 작업, 완료/보류/위험 항목

- `implementation/WORKLOG.md`
  - 시간순 구현 기록
  - 어떤 repo에서 어떤 변경을 했고 어떤 검증을 했는지 누적

- `implementation/NEXT_SESSION_PROMPT.md`
  - 다음 Codex 세션 또는 다른 도구가 이어받을 때 필요한 압축 인계문

- `implementation/TEMPLATE_BUILDER_NEXT_SESSION_PROMPT_2026-05-06.md`
  - 템플릿 생성기 설계를 다음 세션에서 그대로 이어받기 위한 전용 prompt

- `implementation/TEMPLATE_BUILDER_IMPLEMENTATION_PLAN_2026-05-07.md`
  - 사용자 승인된 Template Builder spec을 실제 구현으로 옮기기 위한 phase별 계획
  - NestJS catalog API, local repository, Angular top-level route/editor, validation/sample render publish gate 작업 순서

- `implementation/2026-05-21-windows-dance-image-env-management-context.md`
  - Windows packaged dance member image 0건 문제의 root cause와 구조 개선 경과
  - NestJS image search key 주입, 실행 모드/env 파일 재정의, packaged env copy/read 정리
  - LocalPluginHost, Electron packaged plugin port range, Template Builder DB 필수 정책 보강
  - env 파일 정리, optional blank placeholder 제거, Python Naver/Kakao key 제거, 이번 세션 commit/검증 목록

- `implementation/2026-05-21-execution-mode-runbook.md`
  - `local`/`devapp`/`packaged` 환경별 실행 명령어 정리
  - NestJS/Angular/Electron을 몇 개의 터미널에서 어떻게 띄우는지 설명
  - 모드별 env 파일, OS-independent secret env 복사 기준, packaged build/run, smoke 확인 명령 정리

- `implementation/2026-05-21-windows-electron-builder-powertoys-ebusy-diagnosis.md`
  - Windows electron-builder Step 5 `Clipper2.exe` EBUSY 원인 분석
  - 실패한 우회 시도와 되돌린 코드 변경 기록
  - PowerToys `Command Palette` / `Microsoft.CmdPal.UI.exe`가 원인이었음을 ProcMon으로 확인한 흐름

- `implementation/2026-05-22-angular-template-builder-and-dance-ui-checkpoint.md`
  - Dance setup/member image selection scroll 및 중앙 정렬 수정 기록
  - Template Builder thumbnail skeleton 컴포넌트 분리 기록
  - Template Builder ffmpeg/ffprobe readiness gate 기준과 샘플 렌더/text preview worker 의존 관계 정리

### Session Logs

- `session-logs/YYYY-MM-DD.log`
  - 날짜별 session log
  - 짧게 쓴다. 토큰을 많이 쓰는 장황한 기록을 남기지 않는다.
  - 남길 것: 사용자 요구의 핵심, root cause/결정, 주요 변경 파일, 검증 명령과 pass/fail, 다음 작업
  - 남기지 않을 것: 긴 명령 출력, 반복 조사 과정, diff 전문, 이미 다른 문서에 있는 상세 설명
  - hidden reasoning은 원문이 아니라 검토 가능한 결정/근거 요약으로 기록

### Standards

- `standards/SOLID_AND_BOUNDARIES.md`
  - Clipper2 구현 시 반드시 지킬 SOLID/추상화/경계 분리 원칙

- `standards/DOCUMENTATION_POLICY.md`
  - 작업 전/중/후 문서화 규칙
  - 설계 문서와 구현 문서의 분리 기준

- `standards/ANGULAR_FRONTEND_RULES.md`
  - Angular 19 standalone/zoneless, signal state, TestBed provider 규칙
  - zone.js 재도입 금지와 legacy UI 이식 기준
