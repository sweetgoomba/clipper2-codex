# Clipper2 Session Handoff: Shortform Phase 3 Status

작성일: 2026-06-10

Status: implementation committed and pushed

이 문서는 설치형 Clipper2 앱의 기존 Clipper1 재구현 작업 중 2026-06-10 현재까지 진행한 Phase 3 상태를 기록한다.

대상 repo:

- `clipper_angular`
- `clipper_nestjs`
- `clipper_infra`

참조 repo:

- `adlight_angular`
- `adlight_python`

## 이번 세션에서 확정한 결정

- user-facing 명칭에서 `Clipper1`을 계속 쓰지 않고 `숏폼 제작`을 기준으로 정리한다.
- 현재 Phase 3에서는 URL 입력과 붙여넣기 입력을 구현하지 않는다.
- URL/붙여넣기 workflow는 plugin 목록에서도 열리지 않게 막고, 직접 route 진입도 준비중 화면으로 막는다.
- 프롬프트 입력 generation만 활성화한다.
- 왼쪽 입력 영역의 기존 요구 기능은 유지한다.
  - 카테고리 추천
  - `프롬프트 생성`
  - prompt textarea
  - 언어 선택
  - `클립 생성하기`
- 가운데 클립 편집 영역은 레거시 동작이 복잡하므로 별도 컴포넌트로 쪼개고 이후 세부 UX를 더 정리한다.
- 오른쪽 스타일 영역은 다음 항목을 우선 유지한다.
  - BGM 선택/재생
  - TTS 목소리 선택/재생
  - 재생 속도
  - 메인 타이틀
- 비율 선택은 제거한다.
- 템플릿 요소는 다음 phase에서 다시 다룰 예정이므로 이번에는 실제 preview를 구현하지 않고 영역만 남긴다.
- 향후 preview/editor는 가짜 preview가 아니라 ffmpeg final render 전에 실제로 어떤 영상이 만들어질지 재생하며 보는 편집기로 설계한다.
- TTS는 provider abstraction을 둔다.
  - 현재 실제 사용: Naver Clova
  - 추후 구현 예정: Supertone bundled provider
- TypeORM 기반 DB 저장소를 준비하고, `clipper_infra` dev database 설정을 통해 테이블이 자동 생성되도록 한다.
- 컴포넌트와 SCSS는 큰 단일 파일로 몰지 않고 역할별로 분리한다.
- 클립별 에셋 선택/수정 UX에는 검색 결과뿐 아니라 유저 로컬 업로드를 포함한다.
- Tenor/GIF 검색 provider는 사용하지 않는다.
- `RemoteProxyClipperStudioImageSearchProvider`는 과거 asset store proxy 성격이므로 현재 media search provider chain에서 제외한다.

## 현재 브랜치 상태

작성 시점 기준:

```text
clipper_angular: work/clipper1-input-workflow-split
clipper_nestjs:  work/clipper1-input-workflow-split
clipper_infra:   feature/infra-initial-setup
```

작성 시점 기준 `clipper_angular`, `clipper_nestjs`, `clipper_infra` 모두 remote branch와 동기화되어 있다.

현재 commit 기준:

```text
clipper_angular
  8740cc4 feat(shortform): add prompt-only workspace UI
  e9acb31 feat(shortform): connect clip media editor
  0f227d4 feat(shortform): show sample playback state
  b32132b feat(shortform): support local media uploads
  90bcb00 fix(shortform): show local video media placeholder

clipper_nestjs
  8995166 feat(shortform): add prompt workspace APIs
  26220c6 chore(shortform): remove Clipper1 from display labels
  fb3d1ca chore(shortform): exclude remote media proxy search

clipper_infra
  f398031 chore(shortform): add dev database envs
  b8c8297 docs(db): clarify dev database host access
```

## 구현 완료 범위

### clipper_angular

- 기존 `src/features/clipper1/` 구조를 제거했다.
- 새 `src/features/shortform/` 구조를 만들었다.
- 주요 분리 구조:

```text
features/shortform/
  components/
    input/
      shortform-prompt-input.component.*
    editor/
      shortform-clip-editor.component.*
      shortform-clip-list.component.*
      shortform-caption-list.component.*
    style/
      shortform-style-panel.component.*
    preview/
      shortform-preview-placeholder.component.*
    render/
      shortform-render-panel.component.*
  models/
    shortform-workspace.ts
  pages/
    shortform-workflow-page.component.*
    shortform-unavailable-page.component.*
  services/
    shortform-workspace.service.ts
    shortform-template-preset-catalog.service.ts
```

- route 기준:
  - `/shortform/prompt`는 실제 숏폼 제작 화면으로 연결한다.
  - `/shortform/url`은 준비중 화면으로 막는다.
  - `/shortform/paste`는 준비중 화면으로 막는다.
  - `/clipper1/:mode`는 호환 redirect 없이 준비중 화면으로 막는다.
- Store/plugin 목록에서 URL/붙여넣기 workflow는 열리지 않도록 막고 안내 문구를 표시한다.
- plugin 상태 service는 현재 활성 workflow를 `shortform_prompt` 중심으로 정리했다.
- render worker의 user-facing display는 `숏폼 렌더 워커`로 정리했다.
- 기술 호환 ID인 `clipper1_video_render`는 아직 유지한다.
- 가운데 클립 편집 영역에 `shortform-media-panel`을 추가했다.
  - media search
  - remote candidate import
  - selected asset replace
  - local file import
  - selected asset local file replace
  - asset delete
  - asset order up/down
- 생성된 caption TTS audio URL이 있으면 자막 row에서 바로 재생할 수 있게 했다.
- 오른쪽 스타일 패널의 BGM/TTS 샘플 재생 버튼은 sample URL이 없으면 비활성화하고, 재생 중에는 `정지` 상태로 전환한다.

### clipper_nestjs

- 기존 `src/projects/clipper1-workspace*` 구현을 제거하고 `src/shortform/` 모듈로 분리했다.
- `ShortformModule`을 `AppModule`에 추가했다.
- 주요 파일:

```text
src/shortform/
  dto/shortform-workspace.dto.ts
  shortform.module.ts
  shortform.controller.ts
  shortform-prompt.service.ts
  shortform-bgm-catalog.ts
  shortform-workspace.controller.ts
  shortform-workspace.service.ts
  shortform-workspace.repository.ts
  tts/shortform-tts.provider.ts
  tts/shortform-tts.service.ts
```

- 현재 product API 방향:
  - prompt recommendation
  - BGM catalog
  - TTS preset/sample
  - prompt-mode workspace create/list/get/update
  - workspace clip generation
  - clip media import/search/reorder/remove
  - caption TTS generation
  - render job request
  - workspace TTS artifact file serving
- URL/paste/manual workspace 생성은 `400`으로 차단한다.
- media search provider chain에서 remote proxy image search를 제외했다.
  - 현재 검색 provider chain: Naver image, Kakao image
  - `RemoteProxyClipperStudioImageSearchProvider` class 자체는 호환/후속 판단을 위해 남아 있으나 registry에서 사용하지 않는다.
- `ProjectsModule`은 `ProjectRepository`를 export하도록 조정했고, shortform render promotion이 기존 project history와 이어질 수 있게 했다.
- `shortform-core` DTO는 새 workflow id를 `shortform`으로 쓰되, 기존 render 호환을 위해 일부 legacy workflow 값은 허용한다.
- plugin catalog:
  - user-facing workflow plugin은 `shortform_url`, `shortform_paste`, `shortform_prompt`로 정리했다.
  - URL/paste는 준비중 설명을 둔다.
  - Python render runtime의 기술 ID `clipper1_video_render`는 유지한다.
- user-facing으로 보일 수 있는 legacy render/template/TTS label 문구는 `Clipper1` 대신 `숏폼` 또는 `shortform` 표현으로 정리했다.
- class/file 이름, legacy asset path, render capability id, env alias처럼 호환 계약에 가까운 `clipper1` 값은 유지한다.

### TTS abstraction

- `ShortformTtsProvider` interface를 만들었다.
- provider registry를 통해 provider를 교체할 수 있게 했다.
- 현재 provider:
  - `NaverClovaShortformTtsProvider`
  - `SupertoneShortformTtsProvider` stub
- 실제 합성은 현재 Naver Clova를 사용한다.
- Clova env 이름:

```text
NAVER_CLOVA_CLIENT_ID
NAVER_CLOVA_CLIENT_SECRET
```

- Clova key 값은 문서화하지 않는다.
- UI의 playback speed는 Clova speech speed 범위로 매핑한다.
- caption line 단위로 TTS artifact id, audio url, duration을 workspace에 저장할 수 있게 했다.

### TypeORM / DB

- `clipper_nestjs`에 `typeorm` dependency를 추가했다.
- `ShortformWorkspaceRepository`는 JSON fallback과 TypeORM 구현을 모두 둔다.
- TypeORM 사용 조건:

```text
SHORTFORM_WORKSPACE_REPOSITORY=typeorm
SHORTFORM_DATABASE_URL
CLIPPER_USER_DATABASE_URL
USER_DATABASE_URL
SHORTFORM_DATABASE_ENABLED=true
```

- 개별 DB 설정 env도 지원한다.

```text
SHORTFORM_DATABASE_HOST
SHORTFORM_DATABASE_PORT
SHORTFORM_DATABASE_NAME
SHORTFORM_DATABASE_USER
SHORTFORM_DATABASE_PASSWORD
```

- 생성 대상 테이블:

```text
shortform_workspaces
shortform_clips
```

- `SHORTFORM_DATABASE_SYNCHRONIZE=true`이면 TypeORM synchronize로 dev DB에 테이블을 자동 생성한다.

### clipper_infra

- `env/stack.dev.env.example`에 shortform DB 설정을 추가했다.
- `apps/compose.yml`에 shortform DB 관련 env pass-through를 추가했다.
- 현재 추가한 주요 env:

```text
SHORTFORM_WORKSPACE_REPOSITORY=typeorm
SHORTFORM_DATABASE_SYNCHRONIZE=true
SHORTFORM_DATABASE_ENABLED
SHORTFORM_DATABASE_URL
SHORTFORM_DATABASE_HOST
SHORTFORM_DATABASE_PORT
SHORTFORM_DATABASE_NAME
SHORTFORM_DATABASE_USER
SHORTFORM_DATABASE_PASSWORD
```

## 검증 결과

### clipper_nestjs

```bash
npm run build
```

결과: 성공

```bash
node --test test/workflow-executor-registry.test.js
```

결과: 성공

```bash
node --test test/shortform-workspace-api.test.js
```

결과: 5 pass

참고:

- 처음 API 테스트는 테스트 child process가 `PORT`만 설정하고 기존 환경의 `NEST_PORT=9019`를 덮지 못해 실패했다.
- 테스트 헬퍼에서 `NEST_PORT`와 `PORT`를 함께 설정하도록 수정했다.
- 테스트 서버는 실행 후 종료되며, 테스트 뒤 `19131`, Karma 임시 포트, `9019` 리스닝이 남지 않음을 확인했다.

```bash
SHORTFORM_WORKSPACE_REPOSITORY=typeorm SHORTFORM_DATABASE_SYNCHRONIZE=true node dist/main.js
```

결과: dev DB TypeORM smoke test 성공

- `clipper_nestjs/.env.local`에 local smoke test용 dev DB env를 추가했다.
- 현재 로컬 개발 머신에서는 `CLIPPER_DATABASE_HOST=metabuzz.iptime.org`를 사용한다.
- Nest를 임시 포트 `19143`으로 띄워 prompt workspace 생성과 clip generation을 실행했다.
- TypeORM synchronize로 `shortform_workspaces`, `shortform_clips` 테이블 존재를 확인했다.
- smoke workspace row 1개와 clip row 3개 저장을 확인했다.
- smoke test row는 확인 후 삭제했다.
- 테스트 뒤 `19143`, `9019` 리스닝이 남지 않음을 확인했다.

### clipper_angular

```bash
npm run build
```

결과: 성공

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/app/app.routes.spec.ts' \
  --include='src/core/plugin-status.service.spec.ts' \
  --include='src/shell/dashboard/dashboard.component.spec.ts' \
  --include='src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts'
```

결과: 16 SUCCESS

후속 media editor 연결 후 재검증:

```bash
npm run build
```

결과: 성공

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/app/app.routes.spec.ts' \
  --include='src/core/plugin-status.service.spec.ts' \
  --include='src/shell/dashboard/dashboard.component.spec.ts' \
  --include='src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts'
```

결과: 16 SUCCESS

후속 local upload/remote proxy 제외 후 재검증:

```bash
npm run build
```

결과: 성공

```bash
node --input-type=module <temporary smoke script>
```

결과: 성공

- Nest를 임시 포트 `19145`로 띄웠다.
- dev DB TypeORM repository를 사용했다.
- prompt workspace 생성과 clip generation을 실행했다.
- `POST /v1/projects/shortform/workspaces/:workspaceId/clips/:clipId/media/local`로 로컬 PNG import를 확인했다.
- `PUT /v1/projects/shortform/workspaces/:workspaceId/clips/:clipId/media/:assetId/local`로 선택 asset 교체를 확인했다.
- 생성된 테스트 workspace row는 `shortform_clips`, `shortform_workspaces`에서 삭제했다.
- `19145` 리스닝과 Karma 임시 포트 리스닝이 남지 않음을 확인했다.
- `dist/main.js`, Karma, ChromeHeadless 프로세스가 남지 않음을 확인했다.

local video asset placeholder 보정 후 재검증:

```bash
npm run build
```

결과: 성공

```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/app/app.routes.spec.ts' \
  --include='src/core/plugin-status.service.spec.ts' \
  --include='src/shell/dashboard/dashboard.component.spec.ts' \
  --include='src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts'
```

결과: 16 SUCCESS

- Karma 임시 포트 `52321` 리스닝이 남지 않음을 확인했다.
- Karma, ChromeHeadless 프로세스가 남지 않음을 확인했다.

## 2026-06-10 용어 정정: workspace -> project

레거시 Clipper(`adlight_angular`, `adlight_python`) 기준을 다시 확인했다.

- Angular `/library`는 `IProject[]`를 렌더링하고, 각 숏폼 결과물은 `project_id`를 가진다.
- Python/FastAPI 쪽도 `ShortsProject`, `projects` 테이블, `/v1/shorts/projects/...` API를 사용한다.
- clip row와 contents input도 `project_id`를 기준으로 연결된다.

따라서 Clipper2 shortform 생성물도 `workspace`가 아니라 `project`로 부른다. 이 문서의 이 섹션 이전에 남아 있는 `workspace` 표현은 rename 이전 기록이며, 이후 구현 기준에서는 `ShortformProject`로 읽는다.

반영된 변경:

- `clipper_nestjs`
  - `ShortformWorkspace*` -> `ShortformProject*`
  - API root: `/projects/shortform/workspaces` -> `/projects/shortform/projects`
  - TypeORM table: `shortform_workspaces` -> `shortform_projects`
  - clip FK column: `workspace_id` -> `project_id`
  - JSON fallback store: `shortform/projects.json`
  - env: `SHORTFORM_PROJECT_REPOSITORY` 사용. 기존 로컬 env 호환을 위해 `SHORTFORM_WORKSPACE_REPOSITORY` fallback은 읽기만 유지한다.
  - render response는 편집 중 shortform entity를 `shortformProject`, 보관함/렌더 결과 project snapshot을 `project`로 분리한다.
- `clipper_angular`
  - model/service 파일: `shortform-project.ts`, `shortform-project.service.ts`
  - service class/type: `ShortformProjectService`, `ShortformProject`, `CreateShortformProjectRequest`, `UpdateShortformProjectRequest`
  - component input/output: `project`, `projectId`, `projectChange`
  - API 호출 경로: `/projects/shortform/projects/...`
- `clipper_infra`
  - compose/example env: `SHORTFORM_PROJECT_REPOSITORY`

커밋:

- `clipper_nestjs` `8ac76d5 refactor(shortform): rename workspace state to project`
- `clipper_angular` `993efb2 refactor(shortform): use project terminology`
- `clipper_infra` `20f6795 chore(shortform): rename project repository env`

검증:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-project-api.test.js
```

결과: Nest build 성공, shortform project API test 5개 성공.

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run build
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless \
  --include='src/app/app.routes.spec.ts' \
  --include='src/core/plugin-status.service.spec.ts' \
  --include='src/shell/dashboard/dashboard.component.spec.ts' \
  --include='src/features/shortform/services/shortform-template-preset-catalog.service.spec.ts'
```

결과: Angular build 성공, Karma 16 SUCCESS.

- API 테스트 포트 `19131` 리스닝이 남지 않음을 확인했다.
- Karma 임시 포트 `52764` 리스닝이 남지 않음을 확인했다.
- 로컬 dev server는 띄우지 않았다.

## 아직 검증하지 않은 것

- 전체 Angular Karma suite.
- 전체 NestJS test suite.
- 실제 packaged Electron app 안에서 shortform API와 Angular route가 함께 동작하는지.
- 레거시 UI와의 visual parity.
- Naver Clova 실 API key를 통한 실제 TTS 파일 생성.
- Supertone provider 실제 구현.

## 남은 작업

### 바로 다음에 할 작업

1. caption line 편집과 caption TTS 생성 UI를 더 다듬는다.
2. 가운데 클립 편집 UX를 레거시 기준으로 더 구체화한다.
3. 클립별 미디어 패널의 실제 UI 클릭 흐름을 Playwright/브라우저 기준으로 확인한다.

### 이후 Phase

- 가운데 클립 편집 UX를 레거시 기준으로 더 정교하게 맞춘다.
- 클립별 media search/import/replace/order/local upload UX를 더 다듬는다.
- caption line 편집과 TTS 생성 UX를 더 다듬는다.
- BGM/TTS sample playback을 실제 UI에서 확인한다.
- template 영역은 main title/subtitle 중심으로 다시 설계한다.
- fake template preview가 아니라 실제 편집기형 preview/player 설계를 시작한다.
- Supertone bundled TTS provider를 실제 구현한다.
- 최종 render worker boundary는 Python/ffmpeg runtime과 계속 호환시킨다.

## 주의할 점

- 사용자가 요청하지 않은 한 로컬 dev server를 계속 띄워두지 않는다.
- API 테스트와 Karma browser 테스트처럼 실행 후 종료되는 테스트는 돌려도 된다.
- 테스트나 smoke test로 서버를 잠깐 띄운 경우 반드시 종료 여부를 확인한다.
- URL/paste workflow를 이번 phase에서 실수로 열지 않는다.
- `/clipper-studio`, `/clipper1` 호환 redirect를 되살리지 않는다.
- 컴포넌트를 다시 큰 단일 파일로 합치지 않는다.
- 레거시 코드는 기능과 behavior 참조용이며 그대로 복사하지 않는다.

## 다음 세션 시작 프롬프트

```text
Clipper2 설치형 앱 숏폼 제작 Phase 3를 이어서 진행하자. 먼저 .codex/design/CLIPPER2_SESSION_HANDOFF_2026-06-10_SHORTFORM_PHASE3_STATUS.md를 읽고 현재 브랜치/변경사항을 확인해줘. 레거시 `/library` 기준과 맞춰 shortform 생성물 명칭은 workspace가 아니라 project로 사용해. URL/붙여넣기 입력은 계속 준비중으로 막고, 프롬프트 입력 generation만 유지해. 다음 작업은 가운데 클립 편집 UX, media search/import/replace/order 연결, caption line 편집과 TTS 생성 UI 연결이야. 로컬 dev server는 계속 켜두지 말고, API/Karma 테스트처럼 실행 후 종료되는 검증은 필요하면 실행해.
```

## 2026-06-10 세션 종료 상태

이번 세션에서 완료한 것:

- 레거시 Clipper의 `/library` 단위가 `project/project_id`인지 확인했다.
- Clipper2 shortform 생성물 명칭을 `workspace`에서 `project`로 정정했다.
- `clipper_nestjs`, `clipper_angular`, `clipper_infra`에 각각 커밋하고 원격 브랜치로 push했다.
- handoff 문서에 rename 결정, commit hash, 검증 결과, 주의사항을 남겼다.

최종 원격 반영 상태:

- `clipper_nestjs` branch `work/clipper1-input-workflow-split`
  - `8ac76d5 refactor(shortform): rename workspace state to project`
- `clipper_angular` branch `work/clipper1-input-workflow-split`
  - `993efb2 refactor(shortform): use project terminology`
- `clipper_infra` branch `feature/infra-initial-setup`
  - `20f6795 chore(shortform): rename project repository env`

검증 완료:

- `clipper_nestjs`: `npm run build`
- `clipper_nestjs`: `node --test test/shortform-project-api.test.js`
- `clipper_angular`: `npm run build`
- `clipper_angular`: targeted Karma 16 SUCCESS
- API/Karma 임시 포트 리스닝이 남지 않음을 확인했다.
- 로컬 dev server는 띄우지 않았다.

다음 세션에서 먼저 해야 할 것:

1. 세 repo의 branch/status를 다시 확인한다.
2. `workspace` 잔여 용어를 새로 만든 코드에 다시 도입하지 않도록 주의한다.
3. 가운데 클립 편집 UX를 레거시 UI/동작 기준으로 재정리한다.
4. 클립별 media search/import/replace/order/local upload UI 흐름을 실제 클릭 기준으로 검증한다.
5. caption line 편집과 TTS 생성 UI를 다듬는다.

다음 세션에 그대로 입력할 프롬프트:

```text
Clipper2 설치형 앱 숏폼 제작 Phase 3를 이어서 진행하자. 먼저 /Users/jina/project/adlight/.codex/design/CLIPPER2_SESSION_HANDOFF_2026-06-10_SHORTFORM_PHASE3_STATUS.md를 읽고, clipper_nestjs / clipper_angular / clipper_infra의 현재 브랜치와 git status를 확인해줘. 레거시 `/library` 기준과 맞춰 shortform 생성물 명칭은 workspace가 아니라 project로 유지해. URL/붙여넣기 입력은 계속 준비중으로 막고, 프롬프트 입력 generation만 유지해. 다음 작업은 가운데 클립 편집 UX를 레거시 UI/동작 기준으로 다듬고, 클립별 media search/import/replace/order/local upload 흐름과 caption line 편집/TTS 생성 UI를 이어서 구현하는 거야. 컴포넌트는 작게 나누고, 로컬 dev server는 계속 켜두지 마. API/Karma/browser 테스트처럼 실행 후 종료되는 검증은 필요하면 실행해.
```
