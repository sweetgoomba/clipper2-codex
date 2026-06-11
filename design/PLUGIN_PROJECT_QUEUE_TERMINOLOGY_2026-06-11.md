# Plugin / Project / Queue 용어 정리

작성 기준: 2026-06-11

이 문서는 2026-06-10 `workspace -> project` 정정 이후, 2026-06-11에 확정한 Clipper2 제품 용어와 개발자 내부 용어 기준을 정리한다.

이 문서의 범위는 플러그인, 프로젝트, 큐, 내부 실행 기록, 진행 메시지다. 기존 코드에 남아 있는 `workflow`, `job`, `workspace` 용어는 현재 구현 상태를 설명할 때만 언급한다.

## 2026-06-11 구현 상태

이 문서는 제품/개발자 용어 기준과 목표 구조를 정리한 문서다. 이 기준에
맞춘 Project-first / Plugin / Queue 모델 변경은 아직 시작하지 않았다.

현재 합의한 작업 순서:

1. 먼저 숏폼 제작 레거시 UI/pre-render parity를 끝낸다.
   - 기준 브랜치: `work/clipper1-input-workflow-split`
   - 유지할 것: `shortform_url`, `shortform_paste`, `shortform_prompt` 3분리,
     기존 `workspace -> project` 정정, 현재 NestJS shortform API
   - 목표: `adlight_angular` 레거시 숏폼 제작 화면과 UI/스타일/영상 생성 전
     동작을 맞춘다.
   - 하지 않을 것: 큐/프로젝트/잡 모델 대수술
2. 그 다음 Project-first / Plugin / Queue / terminology 정리를 시작한다.
   - 큐에 들어가는 단위를 프로젝트로 정리한다.
   - `/projects`, `/jobs`, `VideoRenderJob`, plugin catalog, ProjectRun,
     ProjectProgress를 본격 정리한다.

따라서 이 문서 아래의 목표 구조와 구현 원칙은 다음 단계의 기준이며, 현재
코드에 이미 모두 구현됐다는 의미가 아니다.

## 핵심 결론

유저가 알아야 하는 제품 개념은 두 개다.

```text
플러그인
프로젝트
```

유저는 플러그인 스토어에서 플러그인을 보고, 설치하고, 연다. 플러그인을 열어 무언가 만들기 시작하면 그것이 프로젝트다. 실행 큐에 들어가는 단위도 프로젝트이고, 완료 후 보관함/프로젝트 페이지에 남는 단위도 프로젝트다.

`workflow`, `job`, `runtime`, `worker`는 유저에게 노출하지 않는다.

## 사용자 용어

### 플러그인

플러그인은 스토어에 보이는 설치/실행 단위다.

예:

- `shortform_prompt`: 프롬프트로 숏폼 영상 제작
- `shortform_url`: URL로 숏폼 영상 제작
- `shortform_paste`: 붙여넣기로 숏폼 영상 제작
- `dance_highlight`: 안무 영상 하이라이트 추출
- `dialog_highlight`: 대사 중심 영상 하이라이트 추출
- `variation`: 베리에이션 제작

중요한 결정:

- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 독립된 사용자 플러그인이다.
- 이 셋은 하나의 `shortform` 플러그인 안에 있는 입력 모드가 아니다.
- 다만 내부 구현은 같은 숏폼 프로젝트 엔진, 렌더 provider, 렌더 worker를 공유할 수 있다.

### 프로젝트

프로젝트는 유저가 플러그인에서 만들기 시작한 작업물이다.

예:

- 대사 하이라이트 프로젝트
- 안무 하이라이트 프로젝트
- 프롬프트 숏폼 프로젝트
- URL 숏폼 프로젝트
- 붙여넣기 숏폼 프로젝트
- 베리에이션 프로젝트

프로젝트는 큐/보관함의 기본 표시 단위다.

```text
프로젝트 생성
  -> 편집 중
  -> 큐에 추가
  -> 대기 중
  -> 처리 중
  -> 완료
```

실패 또는 취소도 프로젝트 상태로 보여준다.

```text
실패
취소됨
```

## 제품 화면 기준

### 플러그인 스토어

스토어는 사용자 플러그인만 보여준다.

보여야 하는 것:

- `shortform_prompt`
- `shortform_url`
- `shortform_paste`
- `dance_highlight`
- `dialog_highlight`
- `variation`

보이면 안 되는 것:

- `clipper1_video_render`
- Python runtime process
- ffmpeg executor
- 내부 render worker
- 내부 테스트 executor

`clipper1_video_render` 같은 항목은 숏폼 플러그인이 의존하는 숨김 실행 자원이다. 유저가 직접 설치해서 여는 플러그인으로 보이면 안 된다.

### 큐 / 보관함 / 프로젝트 페이지

큐와 보관함은 프로젝트 목록을 보여준다.

현재 코드에는 job history와 project history가 섞여 있지만, 목표 제품 모델에서는 유저가 보는 카드는 전부 프로젝트 카드다.

```text
현재 화면에 보이는 카드 = 프로젝트
현재 큐에 들어간 항목 = 프로젝트
완료 후 보관함에 남는 항목 = 프로젝트
```

카드 문구도 `job`, `workflow`, `pipeline`이 아니라 프로젝트 상태로 표현한다.

예:

```text
대기 중
처리 중
영상 생성 중
완료
실패
취소됨
```

## 개발자 내부 용어

유저 용어와 내부 구현 용어를 분리한다.

| 용어 | 의미 | 유저 노출 |
| --- | --- | --- |
| `Plugin` | 스토어에 보이는 사용자 기능 단위 | 예 |
| `Project` | 플러그인에서 생성된 사용자 작업물 | 예 |
| `ProjectRun` | 프로젝트를 한 번 처리/분석/렌더링하는 내부 실행 기록 | 아니오 |
| `RuntimeProgress` | worker/provider가 보내는 원본 진행 이벤트 | 아니오 |
| `ProjectProgress` | 유저에게 보여줄 정제된 프로젝트 진행 상태 | 예 |
| `ProgressStep` | 유저에게 보여도 되는 분석 단계 메시지 | 예, 필요할 때만 |
| `RuntimeWorker` | Python process, render worker, ffmpeg executor 같은 숨김 실행 자원 | 아니오 |
| `Artifact` / `Output` | 프로젝트가 만든 결과 파일 | 일부 노출 |

`task`라는 단어는 혼동을 만들기 쉬우므로 새 제품/문서 용어로 쓰지 않는다. 프로젝트 처리 단계를 설명해야 할 때는 `ProjectRun`, `ProgressStep`, `RuntimeProgress` 중 하나로 구체적으로 쓴다.

## Plugin catalog라는 말의 의미

개발자 문서에서 `Plugin catalog`라고 하면, 코드가 플러그인 목록을 만들기 위해 읽는 원본 데이터 또는 registry를 뜻한다.

유저에게는 그냥 플러그인 스토어의 플러그인 목록이다.

현재 문제는 사용자 플러그인과 숨김 실행 자원이 catalog에 섞일 수 있다는 점이다.

정리 목표:

```text
User Plugin Registry
  - 스토어에 보여줄 플러그인
  - 유저가 설치/열기 가능한 단위

Runtime Worker Registry
  - Python process, render worker, ffmpeg executor
  - 유저에게 직접 보이지 않는 실행 자원
```

내부 구현에서 같은 파일이나 service를 당장 공유하더라도, 개념과 API 응답에서는 두 목록을 구분해야 한다.

## 현재 구현 상태

현재 구현은 아직 목표 제품 모델과 다르다.

### `/jobs` PipelineJob

대사/댄스 하이라이트는 현재 `/jobs` 큐를 중심으로 실행된다.

현재 흐름:

```text
Job 생성
  -> 큐 대기
  -> 실행
  -> 완료
  -> ProjectSnapshot으로 승격
```

목표 흐름:

```text
Project 생성
  -> ProjectRun 생성
  -> 큐 대기
  -> 실행
  -> 같은 Project 상태/결과 갱신
```

즉 완료 후 프로젝트를 만드는 구조가 아니라, 처음부터 프로젝트가 있고 실행 결과가 그 프로젝트에 반영되어야 한다.

### VideoRenderJob

숏폼 렌더는 현재 `/jobs`와 별도의 `VideoRenderJob` 시스템을 쓴다.

현재 흐름:

```text
ShortformProject
  -> 렌더 시작
  -> ProjectSnapshot으로 promote
  -> VideoRenderJob 생성
  -> render provider 실행
  -> 필요 시 clipper1_video_render Python worker 호출
```

목표 모델에서는 유저에게 이 구조가 보이면 안 된다. 유저에게는 하나의 숏폼 프로젝트가 `영상 생성 중` 상태로 보이면 된다.

### Python runtime job

Python plugin SDK에도 `/jobs` protocol이 있다.

이건 NestJS가 Python worker에 일을 전달하기 위한 worker-local 실행 protocol이다. 유저 용어의 작업이나 프로젝트가 아니다.

### Angular synthetic job card

현재 Angular Projects 화면에는 실제 `/jobs` 기록이 없는 프로젝트를 job card처럼 보이게 하려고 만든 synthetic job card가 있다.

이 구조는 목표 모델에서 제거해야 한다. 큐/보관함 화면이 처음부터 프로젝트 카드를 보여주면 가짜 job card가 필요 없다.

## 진행 메시지 정책

진행 메시지는 두 층으로 나눈다.

```text
RuntimeProgress
  - worker/provider가 보내는 원본 메시지
  - 내부 저장/디버깅용

ProjectProgress
  - 유저에게 보여줄 정제된 상태
  - 프로젝트 종류와 실행 종류에 따라 매핑
```

raw worker message를 UI에 그대로 노출하지 않는다.

### 하이라이트 분석

하이라이트 분석은 시간이 길고 현재 어떤 분석을 하는지 유저에게 의미가 있으므로 세부 단계 메시지를 보여준다.

대사 하이라이트 예:

```text
영상 정보를 확인하고 있습니다
영상의 음성을 분석하고 있습니다
영상의 장면을 구분하고 있습니다
영상 내용을 문장 단위로 정리하고 있습니다
문장 위치를 영상과 맞추고 있습니다
화면 속 텍스트를 인식하고 있습니다
영상에서 의미 있는 구간을 분석하고 있습니다
영상 스토리를 파악하고 있습니다
하이라이트 주제를 분석하고 있습니다
하이라이트 타이틀을 생성하고 있습니다
하이라이트 영상을 생성하고 있습니다
마무리 작업을 진행하고 있습니다
```

안무 하이라이트 예:

```text
영상 프레임을 분석하고 있습니다
구간을 정리하고 있습니다
얼굴 특징을 추출하고 있습니다
클립을 생성하고 있습니다
그룹 클립을 생성하고 있습니다
인물별 하이라이트를 만들고 있습니다
결과를 정리하고 있습니다
```

이런 문구는 `ProgressStep`으로 취급해 유저에게 보여도 된다.

### 숏폼 렌더 / ffmpeg 영상 생성

렌더 worker의 세부 메시지는 기술 로그에 가깝다.

내부 메시지 예:

```text
Staging render assets
Rendering clip 1/5
Concatenating rendered clips
Applying full-ratio layout
Mixing render audio
Extracting render thumbnail
```

이 메시지를 유저에게 그대로 보여주지 않는다.

유저에게는 단순화한다.

```text
영상 생성 중
영상 생성 완료
영상 생성 실패
영상 생성 취소됨
```

### 설치 / 모델 다운로드

설치와 모델 다운로드는 용량과 대기 이유가 유저에게 중요하므로 진행률과 파일/모델 단위 메시지를 보여줄 수 있다.

단, 내부 path, port, process id 같은 runtime 세부정보는 일반 스토어 화면에 노출하지 않는다. 필요한 경우 개발자용 dashboard에만 둔다.

## 목표 API 방향

신규 중심 API는 `/projects`가 되어야 한다.

예상 방향:

```text
POST /projects
GET /projects
GET /projects/:projectId
PATCH /projects/:projectId
POST /projects/:projectId/queue
POST /projects/:projectId/cancel
POST /projects/:projectId/retry
GET /projects/:projectId/runs
```

기존 `/jobs`는 당장 삭제하지 않는다. 초기에는 compatibility/internal layer로 남겨 기존 Python plugin 실행 경로를 재사용할 수 있다.

최종 목표는 다음이다.

```text
/jobs public 중심 구조를 줄인다.
큐/보관함의 source of truth를 Project 중심으로 옮긴다.
Job/VideoRenderJob/Python runtime job은 ProjectRun 또는 RuntimeWorker 내부 구현으로 숨긴다.
```

## 플러그인별 목표 모델

| 플러그인 | 유저에게 보임 | 프로젝트 종류 | 실행 내부 |
| --- | --- | --- | --- |
| `shortform_prompt` | 예 | 프롬프트 숏폼 프로젝트 | 숏폼 엔진 + render provider + hidden worker |
| `shortform_url` | 예 | URL 숏폼 프로젝트 | 숏폼 엔진 + render provider + hidden worker |
| `shortform_paste` | 예 | 붙여넣기 숏폼 프로젝트 | 숏폼 엔진 + render provider + hidden worker |
| `dance_highlight` | 예 | 안무 하이라이트 프로젝트 | Python runtime worker |
| `dialog_highlight` | 예 | 대사 하이라이트 프로젝트 | Python runtime worker |
| `variation` | 예 | 베리에이션 프로젝트 | variation processor + render provider |
| `clipper1_video_render` | 아니오 | 없음 | hidden render worker |
| `simple_ffmpeg_transform` | 아니오 또는 개발자용 | 없음 | internal executor |

## 마이그레이션 방향

### 1. 문서와 화면 용어 정리

- 사용자 문구에서 `workflow`, `job`, `pipeline`을 제거한다.
- `플러그인`, `프로젝트`, `큐`, `보관함` 중심으로 바꾼다.
- 개발자 문서에서는 기존 코드명을 설명할 때만 `WorkflowExecutor`, `PipelineJob`, `VideoRenderJob`을 쓴다.

### 2. Plugin list와 Runtime worker 분리

- 스토어에 보이는 사용자 플러그인 목록과 내부 worker 목록을 분리한다.
- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 사용자 플러그인으로 유지한다.
- `clipper1_video_render`는 숨김 worker로 분류한다.

### 3. Project-first backend 추가

- 프로젝트를 먼저 만들고, 프로젝트 실행 요청이 내부 run을 만들게 한다.
- 기존 `/jobs` 실행기는 초기에는 ProjectRun processor 뒤에서 재사용할 수 있다.
- 완료 후 새 프로젝트를 만드는 흐름을 줄이고, 기존 프로젝트 상태/결과를 갱신한다.

### 4. Angular 큐/보관함 변경

- 큐/보관함 화면을 `ProjectHistoryService` 중심으로 바꾼다.
- `JobHistoryService` 중심 card와 synthetic job card를 제거 방향으로 정리한다.
- 진행 문구는 raw runtime message가 아니라 ProjectProgress mapping 결과를 표시한다.

### 5. 숏폼 정리

- `ShortformProject`는 유저 관점에서 프로젝트다.
- 내부 저장 구조가 당장 분리되어도 API와 화면에서는 프로젝트로 보이게 한다.
- `pluginId`는 `shortform_prompt`, `shortform_url`, `shortform_paste` 중 실제 진입 플러그인을 유지한다.
- 렌더 세부 message는 `영상 생성 중`으로 단순화한다.

### 6. 하이라이트/베리에이션 정리

- 실행 요청 전에 Project를 만든다.
- 큐에는 Project가 들어간 것으로 보이게 한다.
- 하이라이트 분석 단계 메시지는 유저에게 보여준다.
- 완료 시 새 Project를 만드는 대신 기존 Project를 completed로 갱신한다.

### 7. 내부 rename은 나중에 점진 진행

현재 코드에 `WorkflowExecutor`, `PipelineJob`, `VideoRenderJob` 같은 이름이 남아 있어도 즉시 대량 rename하지 않는다.

우선순위:

1. 사용자 화면/API 모델을 Project 중심으로 맞춘다.
2. 숨김 worker와 사용자 plugin을 분리한다.
3. 이후 안정화되면 내부 이름을 점진적으로 바꾼다.

대량 rename은 diff가 커지고 회귀 위험이 커서 기능 전환 후 별도 작업으로 진행한다.

## 신규 구현 원칙

1. 유저에게는 `플러그인`과 `프로젝트`만 중심 개념으로 노출한다.
2. `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 사용자 플러그인이다.
3. 큐에 들어가는 유저 단위는 항상 프로젝트다.
4. 보관함에 남는 유저 단위도 항상 프로젝트다.
5. 내부 실행 기록은 `ProjectRun`으로 생각한다.
6. worker/provider 원본 메시지는 `RuntimeProgress`로 생각한다.
7. 유저 표시용 메시지는 `ProjectProgress`로 정제한다.
8. 하이라이트 분석 단계는 자세히 보여줄 수 있다.
9. 숏폼/ffmpeg 렌더 단계는 `영상 생성 중`으로 단순화한다.
10. `workspace`는 신규 제품 도메인 용어로 쓰지 않는다.
11. `job`과 `workflow`는 기존 코드 설명 또는 내부 compatibility 맥락에서만 쓴다.

## 관련 현재 코드

현재 구현을 읽을 때 참고할 파일:

- `clipper_nestjs/src/plugins/plugin-catalog.ts`
- `clipper_nestjs/src/workflows/workflow-executor.ts`
- `clipper_nestjs/src/workflows/workflow-executor-registry.service.ts`
- `clipper_nestjs/src/jobs/jobs.service.ts`
- `clipper_nestjs/src/jobs/dto/job.dto.ts`
- `clipper_nestjs/src/projects/projects.service.ts`
- `clipper_nestjs/src/projects/dto/project.dto.ts`
- `clipper_nestjs/src/project-manifest/video-render-jobs.service.ts`
- `clipper_nestjs/src/shortform/shortform-project.service.ts`
- `clipper_nestjs/src/shortform/shortform-project.repository.ts`
- `clipper_angular/src/core/plugin-status.service.ts`
- `clipper_angular/src/core/job-history.service.ts`
- `clipper_angular/src/core/project-history.service.ts`
- `clipper_angular/src/shell/projects/projects.component.ts`
- `clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/routes.py`
- `clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py`
- `clipper_electron/src/main/backend/plugin-host-bridge.ts`
- `clipper_electron/src/main/plugin/plugin-manager.ts`

## 관련 문서

- `.codex/design/WORKFLOW_PLUGIN_JOB_EASY_EXPLANATION.md`
  - 과거 `WorkflowExecutor` 도입 당시의 기술 설명이다.
  - 제품 용어 기준은 이 문서가 우선한다.
- `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
  - 현재 코드의 기술 경계를 이해하기 위한 참고 문서다.
- `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`
- `.codex/design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
- `.codex/design/CLIPPER2_SESSION_HANDOFF_2026-06-10_SHORTFORM_PHASE3_STATUS.md`
- `.codex/standards/SOLID_AND_BOUNDARIES.md`
