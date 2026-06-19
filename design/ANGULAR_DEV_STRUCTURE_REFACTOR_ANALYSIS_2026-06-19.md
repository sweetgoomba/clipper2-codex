# Angular dev 구조 리팩토링 분석

작성일: 2026-06-19

이 문서는 `clipper_angular`의 초기 구조와 `origin/dev`에 들어간 구조 리팩토링을 비교해, 다음 작업자가 merge 기준을 이해하고 이후 다른 프로젝트에서 더 나은 초기 설계를 할 수 있도록 정리한 문서다.

분석 기준:

- 초기/사용자 설계 기준: `feature/initial-scaffold` `70d6e58`
- 현재 Angular merge의 실제 공통 조상: `9b68b17 Rebuild Clipper1 workflows and remove Variation`
- dev 구조 리팩토링 기준: `origin/refactor/structure-unification` `3debc35`
- 현재 dev 기준: `origin/dev` `425de06`
- 현재 사용자 작업 브랜치: `audit/old-render-path-cleanup-ui` `dba0a36`

## 결론 요약

초기 구조는 잘못된 구조라기보다, 빠르게 기능을 세우고 제품 경계를 실험하기에 적합한 구조였다. Angular 19 standalone, zoneless, signal 중심, Electron/NestJS/Python 직접 빌드 의존 제거라는 핵심 설계 판단은 dev 리팩토링 이후에도 유지됐다.

dev의 리팩토링은 그 핵심 설계를 뒤집지 않았다. 주된 변화는 코드의 책임 위치를 더 명확히 하고, import와 컴포넌트 생성 규약을 장기 유지보수에 맞게 정리한 것이다.

가장 중요한 판단:

- `standalone true` / zoneless 방향은 초기 설계와 dev 모두 동일하다.
- dev 리팩토링은 기능 구조를 바꾼 것이 아니라, 파일 배치와 import boundary를 정리한 리팩토링이다.
- merge 시에는 dev의 구조 규칙을 target으로 삼고, 사용자 브랜치의 제품/기능 변경을 그 구조 위에 얹는 방식이 맞다.
- 단, dev 최신 작업도 완벽히 일관되지는 않다. TTS/logs/settings 추가 이후 일부 상대 deep import와 root `core` 파일이 다시 생겼다. 따라서 dev 구조 원칙은 유지하되, 최신 dev의 모든 세부 배치를 무비판적으로 따를 필요는 없다.

## 초기 구조의 설계 의도

초기 `clipper_angular`는 기존 `adlight_angular`와 달리 순수 Angular SPA로 새로 만든 앱이었다. 목표는 Angular가 Electron, NestJS, Python 구현체에 직접 빌드 의존하지 않고, 런타임 locator/bridge를 통해 필요한 주소와 native 기능만 얻는 구조였다.

초기 설계의 중요한 원칙:

- Angular 19 standalone component 사용
- `bootstrapApplication(AppComponent, appConfig)` 사용
- `provideExperimentalZonelessChangeDetection()` 사용
- `angular.json`의 `polyfills`는 빈 배열
- UI 상태는 `signal`, `computed`, local component state 중심
- Electron native 기능은 preload bridge를 통해 접근
- NestJS API는 `BackendLocator`를 통해 접근
- Python plugin job은 Plugin/Backend locator 계약을 통해 접근
- 기능 영역은 `features/<domain>` 아래에 모음

즉 초기 구조의 핵심은 "웹앱 같은 Angular SPA"가 아니라 "Electron 기반 로컬 plugin host의 renderer UI"였다.

초기 구조는 대략 다음과 같았다.

```text
src/
  app/
    app.component.*
    app.config.ts
    app.routes.ts

  core/
    backend-locator.ts
    clipper-bridge.ts
    realtime-event.service.ts
    pipeline-feature-registry.ts
    plugin-status.service.ts
    plugin-job.ts
    job-history.service.ts
    project-history.service.ts
    resource-status.service.ts
    ffmpeg-download.service.ts
    model-download.service.ts
    source.ts
    source-inspect.service.ts
    file-picker.service.ts
    youtube-auth.service.ts
    ffmpeg-consent/
    model-consent/
    floating-install-bar/
    index.ts

  environments/

  features/
    clipper-studio/
    shortform/
    template-builder/
    dance-highlight/
    dialog-highlight/
    variation/

  shell/
    nav/
    page-header/
    dashboard/
    projects/
    store/

  styles.scss
```

## 초기 폴더별 책임

### `src/app`

앱 부트스트랩과 전역 라우팅을 담당했다.

- `app.config.ts`: zoneless, router, HTTP, animation provider, backend locator, feature registry provider 연결
- `app.routes.ts`: store/dashboard/projects/templates/clipper/dance/dialog 등 route 선언
- `app.component.*`: nav, router outlet, install bar 같은 최상위 shell 조립

이 위치는 초기와 dev 모두 큰 방향이 같다.

### `src/core`

초기에는 앱 전체에서 공유되는 platform/service 성격의 코드가 모두 `core/` 루트에 있었다.

담당 책임:

- Electron preload bridge type과 wrapper
- Backend URL locator
- realtime event/SSE helper
- plugin feature registry
- plugin status/service
- plugin job 실행 helper
- job/project history client
- source asset model/helper
- source inspect/file picker/youtube auth
- model/ffmpeg 설치 상태와 consent UI

초기 의도는 명확했다. "feature에 속하지 않는 앱 공통 기반"을 한곳에 모으는 것이다. 작은 앱에서는 이 방식이 빠르고 이해하기 쉽다.

문제는 `core` 안에 서로 다른 종류의 책임이 같이 누적됐다는 점이다. 예를 들어 `backend-locator`, `plugin-status`, `project-history`, `ffmpeg-download`, `source-inspect`, `youtube-auth`는 모두 공통 코드이긴 하지만, 같은 수준의 같은 종류 책임은 아니다.

### `src/features`

제품 기능 단위의 화면과 도메인 코드를 담았다.

초기 주요 feature:

- `clipper-studio`: Clipper1/shortform 제작 흐름
- `template-builder`: Template Builder 화면, canvas/editor/inspector/service
- `dance-highlight`: 안무 하이라이트 setup flow
- `dialog-highlight`: 대사 하이라이트 setup flow
- `shortform`: shared shortform picker/catalog 등 일부 공통 shortform 조각
- `variation`: 변형/variation 실험 기능

이 구조는 feature 단위로 코드를 찾기 쉽다는 장점이 있었다. 특히 Template Builder처럼 큰 기능은 `features/template-builder` 아래에서 page/components/services/models로 자연스럽게 확장됐다.

다만 시간이 지나면서 `clipper-studio` 안에 실제로는 `Clipper1`, `shortform`, editor, preview, input workflow가 섞이기 시작했다. 이 이름은 제품 역사에는 맞지만, 코드 책임을 설명하는 이름으로는 점점 애매해졌다.

### `src/shell`

앱 전체 shell과 주요 상위 화면을 담았다.

초기 담당 책임:

- `nav`: 왼쪽 사이드바
- `page-header`: 여러 페이지에서 쓰는 header
- `dashboard`: 대시보드
- `projects`: 작업 보관함/큐/상세 패널/overlay
- `store`: 플러그인 스토어와 plugin card/detail

초기에는 shell에 nav/page-header를 두는 것이 자연스러웠다. 둘 다 앱 shell의 일부였기 때문이다.

하지만 시간이 지나면서 `page-header`는 feature page에서도 재사용되고, `nav` 역시 root layout component에 가까워졌다. 이 둘은 "shell 아래 특정 화면"이라기보다 "공유 layout primitive"에 가까워졌다.

## 초기 구조에서 생긴 문제

초기 구조의 문제는 한 번에 터진 것이 아니라, 기능이 커지면서 점진적으로 드러났다.

### 1. `core/`가 flat해서 책임 경계가 흐려짐

초기 `core/`는 모든 앱 공통 코드를 한 레벨에 뒀다.

```text
core/
  backend-locator.ts
  plugin-status.service.ts
  project-history.service.ts
  ffmpeg-download.service.ts
  source-inspect.service.ts
  youtube-auth.service.ts
```

파일이 10개 미만일 때는 문제가 작다. 하지만 20개에 가까워지면 `core`가 "공통 기반"이 아니라 "어디 둘지 애매한 것들의 모음"처럼 보이기 쉽다.

또한 새 파일을 추가할 때 다음 판단이 어려워진다.

- 이 파일은 bridge인가?
- plugin runtime 관련인가?
- resource 설치 관련인가?
- history/project API 관련인가?
- source asset 관련인가?
- 아니면 feature service인가?

폴더가 책임을 안내하지 못하면, 작업자마다 다른 기준으로 파일을 추가하게 된다.

### 2. 상대 deep import가 구조 변경 비용을 키움

초기 사용자 브랜치에는 다음 같은 import가 많이 있었다.

```ts
import { BackendLocator } from '../../../core/backend-locator';
import { ProjectHistoryService } from '../../core/project-history.service';
import { PageHeaderComponent } from '../page-header/page-header.component';
```

이 방식은 처음에는 단순하다. 하지만 파일을 한 단계 옮기면 import가 모두 깨진다. 특히 merge 상황에서는 같은 기능 변경과 경로 변경이 동시에 충돌한다.

상대 deep import의 문제:

- 파일 위치 변경이 기능 코드 diff처럼 보인다.
- 실제 behavior 변경과 import 경로 변경을 분리하기 어렵다.
- merge conflict가 많아진다.
- 특정 service의 물리적 위치가 외부 파일에 노출된다.

### 3. `shell/`과 `shared/`의 경계가 없음

초기에는 `shared/`가 없고, `nav`와 `page-header`가 `shell/` 아래에 있었다.

```text
shell/
  nav/
  page-header/
  projects/
  store/
```

이 구조는 "앱 shell에 속한 UI"라는 관점에서는 맞다. 하지만 재사용 관점에서는 `page-header`가 projects/store/dashboard와 같은 종류가 아니다.

- `projects`와 `store`는 route page 또는 route page의 하위 UI다.
- `nav`와 `page-header`는 layout primitive다.

이 둘을 같은 레벨에 두면, 나중에 feature page에서 `page-header`를 쓸 때 `shell/page-header`를 import해야 한다. 의미상 "feature가 shell의 내부 구현을 참조"하는 느낌이 생긴다.

### 4. 컴포넌트 파일이 flat하게 쌓임

초기 `shell/projects`와 `shell/store`에는 여러 컴포넌트가 같은 폴더에 flat하게 있었다.

```text
shell/projects/
  projects.component.ts
  projects-queue.component.ts
  projects-history-list.component.ts
  projects-detail-panel.component.ts
  projects-clip-overlay.component.ts
  dance-result-detail.component.ts
  dialog-result-detail.component.ts
```

장점은 한 화면의 관련 파일을 한눈에 볼 수 있다는 점이다. 하지만 각 컴포넌트가 `.ts/.html/.scss/.spec.ts` 네 파일을 가지기 시작하면, 폴더가 금방 길어진다.

문제:

- 한 컴포넌트의 4파일이 한눈에 묶이지 않는다.
- 새 spec을 추가할 때 위치가 애매하다.
- `ng generate component` 기본 동작과 repo 규약이 달라질 수 있다.
- 큰 page component를 분해할 때 어떤 파일이 어떤 컴포넌트 소유인지 추적하기 어렵다.

### 5. 생성 규약이 자동화되어 있지 않음

초기 `angular.json`은 component schematic에 `style: scss`만 있었다.

```json
"@schematics/angular:component": {
  "style": "scss"
}
```

따라서 새 컴포넌트 생성 시 작업자 환경이나 CLI 옵션에 따라 spec이 빠지거나 flat하게 생성될 수 있다. 설계 규칙은 문서에만 있고 도구가 강제하지 않는 상태였다.

### 6. 제품 용어 변화와 코드 이름이 어긋남

초기에는 `clipper-studio`가 자연스러운 feature 이름이었다. 하지만 이후 제품 용어는 `shortform`, `project`, `plugin`, `queue` 중심으로 바뀌었다.

그 결과 `clipper-studio` 안에 shortform 제작/편집/preview/render 관련 코드가 남아 있으면 새 작업자는 다음을 헷갈릴 수 있다.

- 이 기능은 아직 Clipper Studio인가?
- shortform과 clipper1은 같은 것인가?
- 보관함 project와 clipper-studio project는 다른 것인가?

이 문제는 단순 폴더 구조 문제가 아니라 제품 개념의 변화가 코드 이름에 반영되지 않은 문제다.

## dev 리팩토링의 변경 내용

dev 구조 리팩토링은 `origin/refactor/structure-unification`에서 주로 진행됐다. 문서화된 의도는 "동작 불변 디렉토리 정리"였다.

핵심 변경:

1. path alias 추가
2. `core/`를 책임별 하위 폴더로 재그룹화
3. `shared/layout` 신설
4. shell/store, shell/projects, clipper1/input의 component-per-folder 정리
5. Angular schematic 규칙 강화
6. 누락 spec 일부 백필

dev 리팩토링 후 구조:

```text
src/
  app/

  core/
    bridge/
      clipper-bridge.ts
      backend-locator.ts
      realtime-event.service.ts

    plugins/
      plugin-status.service.ts
      pipeline-feature-registry.ts
      plugin-job.ts

    resources/
      ffmpeg-download.service.ts
      model-download.service.ts
      resource-status.service.ts
      ffmpeg-consent/
      model-consent/
      floating-install-bar/

    history/
      job-history.service.ts
      project-history.service.ts

    source/
      source.ts
      source-inspect.service.ts
      file-picker.service.ts
      youtube-auth.service.ts

    index.ts

  shared/
    layout/
      nav/
      page-header/

  features/
    clipper1/
    dance-highlight/
    dialog-highlight/
    shortform/
    template-builder/
    tts/

  shell/
    dashboard/
    projects/
      projects-queue/
      projects-history-list/
      projects-detail-panel/
      projects-clip-overlay/
      dance-result-detail/
      dialog-result-detail/
    settings/
    store/
      plugin-card/
      plugin-detail/
```

## dev 구조의 폴더별 책임

### `src/core/bridge`

Electron/NestJS/runtime URL과 관련된 "renderer가 외부 host/runtime과 연결되는 통로"다.

담당:

- Electron preload bridge type
- backend URL lookup
- realtime event service

이 폴더는 Angular UI 자체가 아니라 외부 runtime boundary를 표현한다.

### `src/core/plugins`

앱의 plugin 기능 노출과 job 실행 계약을 담당한다.

담당:

- plugin status 조회
- pipeline feature registry
- plugin job client/helper

이 폴더는 "어떤 기능이 사용 가능한가"와 "plugin job을 어떻게 다루는가"에 집중한다.

### `src/core/resources`

앱 실행에 필요한 로컬 resource 설치/상태 UI를 담당한다.

담당:

- ffmpeg download/status
- model download/status
- resource status
- model/ffmpeg consent component
- floating install bar

이 폴더는 product feature가 아니라 runtime readiness UX다.

### `src/core/history`

작업 큐와 프로젝트 보관함의 저장/조회 client 계층이다.

담당:

- job history
- project history
- project detail/result type

이 폴더는 shell/projects와 feature render flow가 공유하는 data access boundary다.

### `src/core/source`

입력 source asset과 local/native source 선택을 담당한다.

담당:

- source asset model
- source inspect
- file picker
- youtube auth

이 폴더는 dance/dialog/shortform 등 여러 기능이 공유하는 입력 자산 boundary다.

### `src/shared/layout`

여러 화면에서 재사용되는 layout component다.

담당:

- nav
- page-header

이 위치로 옮긴 의미는 "shell 내부 구현"이 아니라 "앱 layout primitive"라는 점을 명확히 하는 것이다.

### `src/shell`

앱의 route-level shell page를 담당한다.

담당:

- dashboard
- projects
- store
- settings

`shell`은 이제 재사용 layout component보다 "앱 상위 화면과 화면 조립"에 가까운 영역이다.

### `src/features`

제품 기능 단위의 화면과 도메인 로직이다.

dev 현재 기준:

- `clipper1`: 기존 Clipper1 input workflow
- `template-builder`: Template Builder
- `dance-highlight`: 안무 하이라이트
- `dialog-highlight`: 대사 하이라이트
- `shortform`: shortform 관련 shared pieces
- `tts`: TTS 페이지와 store/api/components

사용자 브랜치 merge 이후에는 `clipper1` 중심보다 `shortform` 중심 구조가 더 중요해진다. 이때도 dev의 구조 원칙은 유지하되, 제품 도메인 이름은 사용자 브랜치의 최신 개념을 살리는 것이 맞다.

## 리팩토링으로 개선된 점

### 1. 폴더가 책임을 설명한다

초기에는 `core/backend-locator.ts`와 `core/project-history.service.ts`가 같은 레벨이었다. dev에서는 다음처럼 책임이 폴더명에 드러난다.

```text
core/bridge/backend-locator.ts
core/history/project-history.service.ts
```

파일을 열기 전에 역할을 예상할 수 있다. 이것은 새 작업자에게 특히 중요하다.

### 2. import가 물리적 위치보다 public boundary를 따르게 된다

dev는 `@core`, `@shared`, `@features`, `@env` alias를 추가했다.

```ts
import { JobHistoryService } from '@core';
import { PageHeaderComponent } from '@shared/layout/page-header/page-header.component';
import { provideDanceApi } from '@features/dance-highlight';
import { environment } from '@env';
```

이 방식의 장점:

- `core` 내부 파일 이동이 외부 feature import를 덜 깨뜨린다.
- merge diff에서 경로 변경 노이즈가 줄어든다.
- public API를 `core/index.ts` 배럴로 통제할 수 있다.
- feature가 `../../../core/history/...` 같은 물리 구조를 알 필요가 줄어든다.

주의할 점도 있다. `@core` 배럴이 너무 넓어지면 core 내부 세부 구현까지 모두 public API가 될 수 있다. 따라서 `@core`는 앱 전체에서 써도 되는 public platform API만 export해야 한다.

### 3. shared layout과 shell page의 의미가 분리된다

초기:

```text
shell/nav
shell/page-header
shell/projects
shell/store
```

dev:

```text
shared/layout/nav
shared/layout/page-header
shell/projects
shell/store
shell/settings
```

이 변화는 작지만 의미가 크다.

- `nav`, `page-header`는 route page가 아니라 layout primitive다.
- feature page가 page header를 쓰는 것이 더 자연스럽다.
- `shell`은 앱의 상위 화면 조립에 집중한다.

### 4. component-per-folder 규칙이 파일 소유권을 명확히 한다

dev는 shell/projects와 shell/store의 서브 컴포넌트를 폴더별로 분리했다.

```text
shell/projects/
  projects.component.ts
  projects-queue/
    projects-queue.component.ts
    projects-queue.component.html
    projects-queue.component.scss
    projects-queue.component.spec.ts
  projects-history-list/
    ...
```

장점:

- 한 컴포넌트의 ts/html/scss/spec가 묶인다.
- 컴포넌트 단위 이동/삭제가 쉽다.
- spec 누락이 눈에 잘 띈다.
- `ng generate component` 결과와 repo 구조가 맞아진다.

단점:

- 작은 컴포넌트가 많으면 폴더가 깊어진다.
- 단일 화면에서 관련 컴포넌트를 한눈에 보는 밀도는 줄어든다.

하지만 `projects`나 `store`처럼 컴포넌트가 여럿이고 각자 template/style/spec를 갖는 영역에서는 폴더화가 더 낫다.

### 5. 생성 규약이 도구로 강제된다

dev는 `angular.json`을 다음처럼 바꿨다.

```json
"@schematics/angular:component": {
  "style": "scss",
  "skipTests": false,
  "flat": false
}
```

이 변화는 장기적으로 중요하다.

- 새 컴포넌트가 자동으로 폴더를 가진다.
- spec이 기본 생성된다.
- "이번만 spec 없이" 같은 편차가 줄어든다.
- 팀원마다 다른 CLI 습관으로 구조가 흔들리는 것을 줄인다.

### 6. 리팩토링과 spec 백필이 함께 진행됐다

구조 리팩토링은 이동만 해도 위험하다. dev는 여러 should-create spec과 행동 spec을 추가해 최소한의 안전망을 넓혔다.

이것은 좋은 방향이다. 폴더 이동 리팩토링은 behavior를 바꾸지 않는다고 주장하기 쉽지만, 실제로 import/provider/template 경로가 깨질 수 있다. spec 백필은 이런 실수를 빨리 드러낸다.

## dev 구조의 한계와 주의점

dev 리팩토링 방향은 타당하지만, 현재 `origin/dev`가 완전히 일관된 최종 상태라는 뜻은 아니다.

확인된 drift:

- TTS 관련 일부 파일이 다시 상대 deep import를 사용한다.
  - 예: `../../../core/bridge/backend-locator`
- settings/logs 추가 후 `src/core/logs.service.ts`, `src/core/renderer-logger.ts`가 root `core`에 생겼다.
- 사용자 브랜치는 구조통일 이전 계열에서 발전했기 때문에 `@core` alias를 거의 쓰지 않는다.

따라서 merge 원칙은 다음이 맞다.

```text
dev의 구조 원칙은 따른다.
dev 최신의 모든 세부 배치를 무조건 정답으로 보지는 않는다.
새로 합치는 사용자 기능은 가능하면 dev 구조 원칙에 맞춰 배치한다.
```

예를 들어 logging 관련 root `core` 파일은 나중에 `core/logging` 또는 `core/bridge`/`core/plugins` 중 성격에 맞는 위치를 검토할 수 있다. 다만 이번 merge 범위에서는 불필요한 추가 리팩토링을 하지 않는 것이 좋다.

## 현재 Angular merge에 주는 의미

현재 사용자 브랜치와 dev의 공통 조상은 `9b68b17 Rebuild Clipper1 workflows and remove Variation`이다.

즉 실제 merge 충돌은 다음 두 흐름 사이에서 생긴다.

```text
9b68b17
  ├─ dev:
  │   structure-unification
  │   TTS
  │   settings/logs
  │
  └─ audit/old-render-path-cleanup-ui:
      shortform workflow
      Template Builder simplification
      project archive redesign
      Clipper Studio project path cleanup
```

merge 시 유지 기준:

dev에서 유지할 것:

- `@core`, `@shared`, `@features`, `@env` alias
- `core/bridge`, `core/plugins`, `core/resources`, `core/history`, `core/source`
- `shared/layout/nav`, `shared/layout/page-header`
- component-per-folder 규칙
- TTS page/route/sidebar entry
- settings page
- logs/debug page
- RendererErrorHandler/logging hook

사용자 브랜치에서 유지할 것:

- 플러그인 스토어 카드 문구/표현
- Template Builder 최신 기능 상태
- shortform workflow/page/store/preview/render flow
- `shortform/prompt`, `shortform/url`, `shortform/paste` route
- project archive UI
- `projects/history/:sectionKey`
- `projects/:projectId` detail route
- project card/detail/archive behavior
- Clipper Studio project client/path 제거
- `shared/ui/confirmation-modal`

## merge 전략 권장안

바로 `origin/dev` 복제 브랜치에 `audit/old-render-path-cleanup-ui`를 merge하면 구조 충돌과 기능 충돌이 섞인다. 권장 순서는 다음이다.

### 1. 사용자 브랜치 복제 후 dev 구조로만 정렬

원본 `audit/old-render-path-cleanup-ui`는 보존하고, 새 port 브랜치를 만든다.

```text
audit/old-render-path-cleanup-ui
  -> port/angular-audit-dev-structure-20260619
```

이 port 브랜치에서 먼저 기능 의미를 바꾸지 않고 구조만 맞춘다.

구조 정렬 대상:

- flat `core` import를 dev 위치/alias에 맞춤
- `shell/nav`와 `shell/page-header`를 `shared/layout` 기준으로 맞춤
- shell/projects와 shell/store 컴포넌트 배치를 dev 규칙에 맞춤
- relative core/env/features import를 alias로 바꿈
- `angular.json`의 schematic 규칙과 style budget 변경을 조합

이 단계의 커밋 메시지는 예를 들어 다음이 적합하다.

```text
refactor(angular): align audit branch with dev structure
```

이 커밋은 behavior 변경이 아니라 merge 준비용 구조 정렬이어야 한다.

### 2. 구조 정렬 브랜치에서 build 확인

구조 정렬 후 `npm run build`가 통과해야 한다. 가능하면 관련 Angular spec도 도메인별로 확인한다.

이 단계가 통과하면 이후 충돌은 경로 문제가 아니라 실제 기능 선택 문제가 된다.

### 3. dev 복제 브랜치에 도메인별로 반영

대상 브랜치:

```text
merge/dev-selected-20260619
```

도메인별 권장 순서:

1. app route/config/nav 조합
2. core/shared import와 shared/ui confirmation modal
3. Template Builder
4. shortform feature
5. shell/projects archive/detail/queue UI
6. store card copy
7. styles/angular config

각 단계에서 파일별로 다음 세 가지 중 하나를 명확히 선택한다.

- dev 유지
- 사용자 브랜치 유지
- 조합

## 앞으로 다른 프로젝트에서 적용할 교훈

초기부터 과도한 구조를 만들 필요는 없다. 하지만 다음 정도는 초기에 잡아두는 것이 좋다.

### 1. `core`는 처음부터 책임별 하위 폴더를 둔다

추천:

```text
core/
  bridge/
  api/
  auth/
  resources/
  history/
  source/
  logging/
  index.ts
```

프로젝트마다 이름은 달라져도, "공통 코드"를 한 폴더에 flat하게 두는 것은 빨리 한계가 온다.

### 2. path alias는 초기에 도입한다

추천:

```json
"paths": {
  "@core": ["src/core"],
  "@core/*": ["src/core/*"],
  "@shared/*": ["src/shared/*"],
  "@features/*": ["src/features/*"],
  "@env": ["src/environments/environment"]
}
```

처음부터 alias를 쓰면 나중에 폴더 이동 비용이 줄어든다.

### 3. `shared`는 신중하게 만들되, layout primitive는 분리한다

추천:

```text
shared/
  layout/
  ui/
```

주의:

- 제품 도메인 로직은 shared로 올리지 않는다.
- 두 곳 이상에서 재사용되거나 앱 전체 layout primitive인 경우만 shared로 둔다.
- "어디 둘지 모르겠다"는 이유로 shared에 넣으면 shared가 두 번째 core가 된다.

### 4. route page와 reusable component를 구분한다

추천:

```text
features/my-feature/
  pages/
  components/
  services/
  models/
```

route page는 orchestration과 persistence 중심으로 두고, 반복 UI나 독립 상태가 있는 부분은 components로 내린다.

### 5. component-per-folder를 기본값으로 둔다

추천:

```text
my-card/
  my-card.component.ts
  my-card.component.html
  my-card.component.scss
  my-card.component.spec.ts
```

특히 Angular에서는 template/style/spec가 함께 움직이므로 폴더화가 유지보수에 유리하다.

### 6. schematic 규칙을 도구로 강제한다

문서보다 `angular.json`이 강하다.

```json
"@schematics/angular:component": {
  "style": "scss",
  "skipTests": false,
  "flat": false
}
```

팀 프로젝트에서는 "좋은 습관"보다 "도구가 기본으로 그렇게 만들게 하는 것"이 더 안정적이다.

### 7. 제품 용어가 바뀌면 폴더 이름도 따라가야 한다

`clipper-studio`처럼 역사적으로 맞았던 이름도, 제품 개념이 `shortform`/`project` 중심으로 바뀌면 코드 탐색을 방해할 수 있다.

폴더 이름은 과거 구현 이름보다 현재 제품 개념과 책임을 설명해야 한다.

### 8. 리팩토링은 기능 변경과 분리한다

이번 Angular merge에서 중요한 교훈이다.

좋은 순서:

```text
1. 구조 정렬만 하는 commit
2. build/test
3. 기능 변경 commit
4. build/test
```

나쁜 순서:

```text
구조 이동 + 기능 변경 + 삭제 + 신규 기능을 한 commit에 섞기
```

이렇게 섞이면 merge conflict에서 어떤 쪽을 선택해야 하는지 판단하기 어렵다.

## 최종 판단

초기 설계는 당시 상황에 맞는 합리적인 설계였다. 특히 standalone/zoneless, feature boundary, Electron/NestJS/Python 직접 빌드 의존 제거는 지금도 유지해야 할 좋은 판단이다.

dev 리팩토링은 그 설계를 부정한 것이 아니라, 기능이 커진 뒤 생긴 유지보수 압력을 반영해 구조를 더 명시적으로 만든 작업이다.

따라서 앞으로의 기준은 다음이 좋다.

```text
초기 설계의 runtime/Angular 원칙은 유지한다.
dev 리팩토링의 폴더/import/component 규칙을 따른다.
사용자 브랜치의 최신 제품/기능 상태를 dev 구조 위에 얹는다.
```

이번 merge에서도 이 원칙을 적용하는 것이 가장 안전하다.
