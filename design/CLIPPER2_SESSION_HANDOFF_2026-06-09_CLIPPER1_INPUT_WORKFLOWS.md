# Clipper2 Session Handoff: Clipper1 Input Workflows

작성일: 2026-06-09

## 이번 세션에서 확정한 결정

- Clipper1은 단일 `Clipper1 숏폼 제작` plugin/card로 노출하지 않는다.
- Clipper1 user-facing entry는 입력 방식별 plugin/workflow entry로 분리한다.
- 현재 남기는 입력 방식은 3개다.
  - `URL에서 숏폼 생성`
  - `복사 붙여넣기로 숏폼 생성`
  - `프롬프트로 숏폼 생성`
- `수동 시작`은 plugin entry, route, UI 입력 방식에서 제외한다.
- `/clipper-studio`, `/clipper1` 같은 기존 호환 redirect는 남기지 않는다.
- 영상 생성/ffmpeg final render는 Python/FastAPI worker boundary에 둔다.
- NestJS는 Clipper1 product API, project/workspace/clip/media/template control plane을 담당하고, Python은 final render execution을 담당한다.

## 이번 세션에서 작성한 문서

- `design/CLIPPER2_VIDEO_RENDER_OWNERSHIP.md`
  - Clipper2 전체에서 영상 생성 로직을 어디에 두는 것이 맞는지 정리.
  - NestJS와 FastAPI/Python runtime 차이, Node.js event loop, ffmpeg child process, Python worker boundary 근거 포함.
- `design/CLIPPER2_INSTALL_APP_CLIPPER1_REBUILD_PLAN.md`
  - 설치형 앱 범위의 Clipper1 재구현 계획 정리.
  - 입력 방식별 plugin 분리, NestJS/FastAPI 책임 재분배, 템플릿 단순화, 작업 보관함 통합 방향 포함.
  - 이번 세션 후 기준으로 `수동 시작`과 기존 호환 route를 제외하도록 업데이트.

## 이번 세션에서 구현한 내용

### clipper_angular

- Store-visible Clipper1 workflow entry를 3개로 분리.
  - `clipper1_url_shortform` -> `/clipper1/url`
  - `clipper1_paste_shortform` -> `/clipper1/paste`
  - `clipper1_prompt_shortform` -> `/clipper1/prompt`
- `clipper1_manual_shortform` 제거.
- 기존 단일 `clipper1` route mapping 제거.
- `/clipper-studio`, `/clipper1`, `/clipper1/manual` route 제거.
- sidebar의 직접 제작 nav item 제거.
- 기존 `clipper-studio` page shell은 아직 임시 재사용하되, route data의 `clipper1InputMode`로 입력 모드를 고정한다.
  - 예: `/clipper1/prompt`에서는 tab 없이 prompt 입력만 표시.
- `ShortformSourceMode`에서 `manual` 제거.
- 관련 Angular specs를 새 기준에 맞게 수정.

### clipper_nestjs

- `PLUGIN_CATALOG`에서 user-facing 단일 workflow 제거.
  - `clipper1`
  - `clipper_studio`
- `clipper1_manual_shortform` 제거.
- `VIRTUAL_WORKFLOW_PLUGINS`에는 다음 3개 Clipper1 entry와 `variation`만 남김.
  - `clipper1_url_shortform`
  - `clipper1_paste_shortform`
  - `clipper1_prompt_shortform`
- `clipper1_video_render` Python plugin은 유지.
  - 이 항목은 Store의 입력 workflow가 아니라 final render worker/runtime이다.
- workflow registry test를 새 catalog 기준으로 수정.

## 용어 정리

`virtual_workflow`는 실제 Python process를 start/stop하는 runtime plugin이 아니다. Store에 보이는 작업 진입점이며, 클릭 시 Angular workflow route로 이동한다.

예를 들어 `URL에서 숏폼 생성`은 `virtual_workflow`이고, 실제 ffmpeg 렌더링 runtime은 `clipper1_video_render` Python worker가 담당한다.

## 검증 결과

### clipper_angular

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include='src/core/plugin-status.service.spec.ts' --include='src/app/app.routes.spec.ts' --include='src/features/clipper-studio/pages/clipper-studio-page.component.spec.ts' --include='src/features/variation/services/variation-workspace.service.spec.ts' --include='src/features/variation/pages/variation-page.component.spec.ts'
```

결과: 38 SUCCESS

```bash
npm run build
```

결과: 성공

### clipper_nestjs

```bash
npm run build
```

결과: 성공

```bash
node --test test/workflow-executor-registry.test.js
```

결과: 2 pass

## 다음 세션에서 이어갈 작업

다음 작업은 Phase 2가 적절하다.

- `clipper_angular/src/features/clipper1/` 새 구조 생성.
- 현재 임시 재사용 중인 `features/clipper-studio` page shell을 새 Clipper1 구조로 옮기거나 재구현.
- 입력 컴포넌트 분리.
  - URL input component
  - paste input component
  - prompt input component
- 입력 이후 공통 영역을 shared editor component로 분리.
  - clip list/editor
  - media pool/slot
  - TTS
  - BGM
  - template picker
  - preview
  - render controls
- 레거시 `adlight_angular`, `adlight_python`의 Clipper1 UI/UX와 behavior를 참조하되 코드 복사 붙여넣기는 하지 않는다.
- Python/FastAPI에는 final ffmpeg render boundary만 남긴다는 원칙을 유지한다.

## 다음 세션 시작 프롬프트

다음 세션에서 아래처럼 입력하면 바로 이어서 진행할 수 있다.

```text
Clipper2 설치형 앱 Clipper1 재구현을 이어서 진행하자. 이번에는 Phase 2로, clipper_angular에서 기존 features/clipper-studio 임시 재사용 구조를 features/clipper1 구조로 분리하고, URL/붙여넣기/프롬프트 입력 컴포넌트와 공통 editor/preview/render 영역을 나눠줘. 수동 시작은 만들지 말고, /clipper-studio와 /clipper1 호환 redirect도 되살리지 마. 먼저 .codex/design/CLIPPER2_SESSION_HANDOFF_2026-06-09_CLIPPER1_INPUT_WORKFLOWS.md와 CLIPPER2_INSTALL_APP_CLIPPER1_REBUILD_PLAN.md를 읽고 현재 브랜치/변경사항을 확인한 뒤 진행해줘.
```
