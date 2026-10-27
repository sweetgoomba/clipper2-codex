# plugin-runtime-isolation -> dev 병합 기록 (2026-07-03)

> **2026-10-26 문서 이관 안내:** 이 문서는 2026-07-03의 **1차 통합 병합 기록**이다. 이후 사용자 검토를 거친 `integration/plugin-runtime-isolation-review2-20260703` 진행과 당시 최종 상태는 [같은 날짜의 세션 기록](../../../../../records/sessions/2026/07/03.md)을 따른다. 아래 재검토 제안과 SHA는 1차 병합 당시 이력으로 보존한다.

이 문서는 `feature/plugin-runtime-isolation`을 최신 `dev`에서 복제한 통합 브랜치에 병합한 과정을 설명한다.

중요:

- secret-bearing 파일 내용, env 값, 토큰 값은 기록하지 않는다.
- 이 병합은 사용자가 재검토할 수 있도록 상세 기록을 남긴 1차 통합이다.
- 특히 Python dialog highlight `stage_runner` 관련 해결은 구조 판단이 들어간 부분이라, 2차 병합/리뷰 때 반드시 다시 확인해야 한다.

## 병합 범위

대상 app repo:

- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `desktop/clipper_python`
- `desktop/clipper_electron`
- `web/clipper_web_api`

제외:

- `.codex` repo는 app repo 병합 대상이 아니어서 제외했다.

통합 브랜치:

- `integration/plugin-runtime-isolation-20260703`

병합 방식:

1. 각 repo에서 `dev`로 이동.
2. `origin/dev`를 `git pull --ff-only`로 최신화.
3. 최신 `dev`에서 `integration/plugin-runtime-isolation-20260703` 브랜치 생성.
4. `origin/feature/plugin-runtime-isolation`을 `--no-ff`로 병합.

## 최종 commit 상태

`desktop/clipper_angular`

- merge commit: `de04dd4 Merge feature/plugin-runtime-isolation into integration branch`
- parent 1: `12d7335` 최신 dev
- parent 2: `d7ef5e6` feature/plugin-runtime-isolation

`desktop/clipper_nestjs`

- merge commit: `365ecd8 Merge feature/plugin-runtime-isolation into integration branch`
- parent 1: `42f194d` 최신 dev
- parent 2: `8e55d76` feature/plugin-runtime-isolation

`desktop/clipper_python`

- merge commit: `2d0daa4 Merge feature/plugin-runtime-isolation into integration branch`
- parent 1: `276b8f1` 최신 dev
- parent 2: `4405cad` feature/plugin-runtime-isolation

`desktop/clipper_electron`

- merge commit: `91233c9 Merge feature/plugin-runtime-isolation into integration branch`
- parent 1: `fd16b8d` 최신 dev
- parent 2: `1837328` feature/plugin-runtime-isolation
- 수동 충돌 없음.

`web/clipper_web_api`

- merge commit: `e1caeee Merge feature/plugin-runtime-isolation into integration branch`
- follow-up fix commit: `0200a50 Fix shortform script guard import`
- parent 1: `2b1e5bd` 최신 dev
- parent 2: `2817381` feature/plugin-runtime-isolation
- Git conflict는 없었지만 merge 후 build에서 import 누락이 발견되어 별도 커밋으로 수정했다.

## 충돌 요약

`desktop/clipper_angular`

- `src/shell/store/plugin-detail/plugin-detail.component.spec.ts`
- `src/shell/store/store/store.component.spec.ts`

`desktop/clipper_nestjs`

- `.env.packaged`
- `package-lock.json`
- `src/modules/plugins/plugins.module.ts`
- `src/modules/shortform/application/shortform-project.service.ts`
- `src/modules/shortform/shortform.module.ts`
- `src/modules/tts-synthesis/tts-synthesis.provider.ts`
- `src/modules/workflows/application/workflow-executor-registry.service.ts`
- `test/shortform-tts-provider.test.js`
- `test/workflow-executor-registry.test.js`

추가로 merge 후 테스트/빌드 보정을 한 파일:

- `package.json`
- `src/modules/tts-synthesis/tts-synthesis.module.ts`
- `test/shortform-project-generation-assets.test.js`

`desktop/clipper_python`

- `plugins/dialog_highlight/dialog_highlight/services/pipeline.py`

실제 최종 해결에서 수정된 파일:

- `plugins/dialog_highlight/dialog_highlight/services/pipeline/__init__.py`
- `plugins/dialog_highlight/dialog_highlight/services/pipeline/llm_strategies.py`
- `plugins/dialog_highlight/dialog_highlight/services/pipeline.py`는 삭제 상태 유지

`desktop/clipper_electron`

- 수동 충돌 없음.

`web/clipper_web_api`

- Git conflict 없음.
- merge 후 build error:
  - `UseGuards` import 누락
  - `ScriptServiceTokenGuard` import 누락

## Angular 충돌 상세

### `plugin-detail.component.spec.ts`

충돌 이유:

- dev 쪽은 Plugin Store에서 `installGated` 플러그인의 제거 버튼 동작을 테스트하고 있었다.
- feature 쪽은 설치 진행 중 UI 상태를 테스트하고 있었다.
- 두 브랜치 모두 같은 spec helper와 버튼 상태 검증 영역을 수정했다.

dev 쪽 변경:

- `installGated` 플러그인만 제거 버튼을 보여야 한다는 테스트 추가.
- 설치된 install-gated 플러그인은 `제거` 버튼이 보이고, 미설치 install-gated 플러그인은 보이지 않는지 확인.
- `제거` 버튼 클릭 시 `uninstall` output이 emit되는지 확인.
- `installGatedItem()` helper 추가.

feature 쪽 변경:

- 설치 중인 플러그인의 primary action이 `설치 중...` 상태로 disabled 되는지 테스트.
- 다른 플러그인 설치 중일 때 미설치 플러그인의 install action이 `다른 플러그인 설치 중`으로 disabled 되는지 테스트.
- `pluginItem()` helper가 boolean `installed` 대신 `installState` 값을 직접 받도록 변경.

해결:

- dev의 제거 버튼 테스트를 유지했다.
- feature의 설치 진행/다른 설치 중 disabled 테스트도 유지했다.
- `pluginItem()`은 `installState: PluginStoreItem['status']['installState'] = 'installed'` 형태로 맞췄다.
- `installGatedItem()`은 별도 helper로 유지했다.

재검토 포인트:

- UI 버튼 문구가 실제 product text와 맞는지 확인 필요.
- `설치 중...` 문구는 코드상 ellipsis가 어떤 문자로 렌더되는지 Angular template과 같이 다시 확인하면 좋다.

### `store.component.spec.ts`

충돌 이유:

- dev 쪽은 `variation` 같은 virtual workflow 설치/제거 flow를 테스트하고 있었다.
- feature 쪽은 모델/ffmpeg 설치 flow 중복 실행 방지 테스트를 추가했다.
- 둘 다 fake service와 `onInstall()` 테스트 구조를 바꿔서 충돌했다.

dev 쪽 변경:

- `variation` virtual workflow item helper 추가.
- `PluginStatusService.install()` 호출 조건 테스트.
- 이미 설치된 virtual workflow는 install을 호출하지 않는지 테스트.
- uninstall confirm dialog flow 테스트.
- uninstall 후 `refreshOne()` 호출 테스트.
- `ConfirmDialogService` fake 추가.

feature 쪽 변경:

- `FakeModelDownloadService`가 `state`, `pluginName`, `reset`, `check`를 실제 signal 변화처럼 동작하게 변경.
- `FakeFfmpegDownloadService`도 `state`, `reset`, `check`를 실제 흐름처럼 동작하게 변경.
- 다른 플러그인을 설치 중이면 현재 active install flow를 reset/check하지 않고 notice만 띄우는 테스트 추가.

해결:

- fake service는 feature 쪽처럼 실제 signal 상태를 바꾸도록 유지했다.
- dev의 virtual workflow install/uninstall 테스트를 유지했다.
- feature의 active install 중복 방지 테스트를 유지했다.
- `FfmpegDownloadService` fake는 기본 상태를 `ready`로 둬서 variation처럼 모델이 필요 없는 경로가 바로 install로 진행될 수 있게 했다.

재검토 포인트:

- `onInstall()`의 실제 UX 의도가 “설치 중인 플러그인이 있으면 다른 설치 요청은 무조건 차단”인지 다시 확인 필요.
- confirm dialog 문구와 Plugin Store 최종 UX가 맞는지 수동 확인 필요.

## NestJS 충돌 상세

### `.env.packaged`

충돌 유형:

- modify/delete.

dev 쪽 상태:

- `.env.packaged`가 Git에 추적되어 있었다.
- 파일 안에는 provider/env 설정이 있었다.

feature 쪽 상태:

- `.env.packaged`를 추적 대상에서 제거한 상태였다.
- packaged env는 로컬 ignored 파일로만 존재해야 한다는 방향이었다.

해결:

- `.env.packaged`는 Git에서 삭제 상태를 유지했다.
- secret-bearing 값은 문서화하지 않았다.

판단 이유:

- 사용자가 이전에 `desktop/clipper_nestjs/.env.packaged`를 `git rm --cached`로 추적 해제하라고 요청했다.
- packaged env는 각 로컬/패키징 환경에서 별도 주입하는 파일이어야 하고, Git merge 결과에 포함되면 안 된다.

재검토 포인트:

- 다음 2차 merge에서도 `.env.packaged`가 다시 Git에 들어오면 삭제 또는 untrack 유지가 맞다.
- 단, 실제 패키징 테스트에는 ignored `.env.packaged` 파일이 로컬에 별도로 있어야 할 수 있다.

### `package.json` / `package-lock.json`

충돌 이유:

- dev 쪽은 variation batch/export 쪽에서 `archiver` 의존성을 추가했다.
- feature 쪽은 desktop NestJS에서 DB/TypeORM 경로를 제거하면서 `pg`, `typeorm`을 제거했다.
- 두 변경이 dependency tree와 lockfile의 같은 영역을 건드렸다.

dev 쪽 변경:

- `archiver`
- `@types/archiver`

feature 쪽 변경:

- `pg` 제거.
- `typeorm` 제거.
- shortform project repository를 DB가 아니라 JSON 파일 repository로 고정.

해결:

- `archiver`와 `@types/archiver`는 유지했다.
- `pg`와 `typeorm`은 제거했다.
- `npm install`로 lockfile을 최종 `package.json`에 맞게 재생성/정리했다.

판단 이유:

- 최신 dev의 variation 기능은 `archiver`가 필요하다.
- feature의 명확한 방향은 “desktop shortform project persistence는 DB 없이 JSON repository만 사용”이었다.

재검토 포인트:

- `npm audit`에서 high severity 경고가 있었지만, 이번 merge 범위에서는 별도 보안 업데이트를 하지 않았다.
- lockfile churn이 크므로 2차 merge 때 `npm ci` 기준으로 재확인 필요.

### `plugins.module.ts`

충돌 이유:

- dev 쪽은 plugin runtime host 구조를 `PluginHostModule`로 분리하기 전의 provider wiring과 virtual workflow install-state repository를 갖고 있었다.
- feature 쪽은 `DialogHighlightModule`과 `PluginHostModule`을 사용하도록 바꿨지만, dev의 virtual workflow install-state repository wiring이 없었다.

dev 쪽 상태:

- `StaticPluginHost`, `ElectronPluginHost`, `LocalPluginHost`, `PluginHost` factory가 `PluginsModule` 안에 직접 있었다.
- `PYTHON_RUNTIME_LIFECYCLE_OPTIONS`, `PythonRuntimeLifecyclePolicy`도 직접 wiring.
- `InstalledVirtualWorkflowsRepository -> JsonInstalledVirtualWorkflowsRepository` provider가 있었다.
- `WorkflowExecutorRegistry`가 virtual workflow install-state repository를 받을 수 있는 구조였다.

feature 쪽 상태:

- `PluginHostModule`을 import/export해서 plugin host wiring을 별도 module로 옮겼다.
- `DialogHighlightModule`을 import해서 NestJS-native dialog highlight executor를 쓸 수 있게 했다.
- `InstalledVirtualWorkflowsRepository` provider/export는 빠져 있었다.

해결:

- `PluginHostModule` 구조는 유지했다.
- `DialogHighlightModule` import를 유지했다.
- dev의 `InstalledVirtualWorkflowsRepository -> JsonInstalledVirtualWorkflowsRepository` provider/export를 다시 추가했다.
- 직접 host factory wiring은 `PluginHostModule`에 맡기고 `PluginsModule`에서는 반복하지 않았다.

판단 이유:

- feature의 plugin runtime isolation 구조상 `PluginHostModule` 분리가 맞다.
- dev의 virtual workflow install-state persistence도 최신 dev 기능이라 유지해야 한다.

재검토 포인트:

- `PluginHostModule`이 `PythonRuntimeLifecyclePolicy`와 host provider를 모두 export하는지 2차 merge 때 다시 확인 필요.
- virtual workflow install-state가 실제 app restart 후 유지되는지는 패키지 앱에서 별도 smoke 필요.

### `workflow-executor-registry.service.ts`

충돌 이유:

- dev 쪽은 virtual workflow install-state repository를 `VirtualWorkflowExecutor`에 넘기는 구조였다.
- feature 쪽은 dialog highlight를 Python plugin manifest가 아니라 NestJS-native executor로 우선 사용하도록 바꿨다.
- 양쪽 모두 constructor와 executor list/get 로직을 바꿨다.

dev 쪽 상태:

- NestJS-native executor는 `ffmpegTransform`만 있었다.
- virtual workflow executor 생성 시 `InstalledVirtualWorkflowsRepository`를 전달했다.
- Python plugin manifest를 그대로 모두 executor로 만들었다.

feature 쪽 상태:

- NestJS-native executor에 `dialogHighlight`가 추가됐다.
- `list()`에서 NestJS-native plugin name과 같은 Python manifest는 제외했다.
- `get()`에서 NestJS-native executor는 `getManifest()`로 availability를 검증했다.
- virtual workflow executor 생성 시 install-state repository 전달이 빠져 있었다.

해결:

- NestJS-native executor 목록을 `[ffmpegTransform, dialogHighlight]`로 유지했다.
- `InstalledVirtualWorkflowsRepository` constructor dependency를 유지했다.
- virtual workflow executor 생성 시 repository를 전달했다.
- Python manifest 목록에서 NestJS-native plugin name은 제외했다.
- NestJS-native manifest가 없으면 list에서는 제외하고, get에서는 typed error를 유지했다.

판단 이유:

- dialog highlight는 feature에서 Python plugin 직접 provider 호출을 제거하고 NestJS/web_api orchestrated path로 바꾼 핵심 변경이다.
- dev의 virtual workflow install-state persistence도 최신 기능이므로 같이 유지해야 한다.

재검토 포인트:

- NestJS-native dialog executor가 실패할 때 Python dialog plugin으로 fallback하지 않는 것이 의도인지 확인 필요.
- 현재 테스트는 fallback하지 않는 것을 기대한다.

### `shortform.module.ts`

충돌 이유:

- dev 쪽은 `ConfiguredShortformProjectRepository`와 TypeORM repository를 포함하고 있었다.
- feature 쪽은 shortform project repository를 JSON 파일로 고정하고, script generation을 local provider가 아니라 web_api로 위임했다.
- dev 쪽은 `VideoRenderModule`, `TtsSynthesisModule` 등 최신 render path가 있었다.
- feature 쪽은 Supertonic TTS provider를 shortform 내부 path에 두고 `PluginsModule`을 직접 import했다.

dev 쪽 상태:

- `ConfiguredShortformProjectRepository`
- `TypeOrmShortformProjectRepository`
- `ConfiguredClipperStudioScriptGenerator`
- local script providers: deterministic, remote_proxy, OpenAI responses, Ollama
- `VideoRenderModule`, `TtsSynthesisModule`

feature 쪽 상태:

- `JsonShortformProjectRepository`만 사용.
- `WebApiClipperStudioScriptGenerator` 사용.
- `WebApiClient` 추가.
- Supertonic TTS provider와 plugin TTS client wiring이 shortform module 안에 있었다.

해결:

- `VideoRenderModule`, `TtsSynthesisModule`은 dev 쪽 최신 render path로 유지했다.
- shortform project repository는 `JsonShortformProjectRepository`로 고정했다.
- `ConfiguredShortformProjectRepository`, `TypeOrmShortformProjectRepository`는 넣지 않았다.
- `ClipperStudioScriptGenerator`는 `WebApiClipperStudioScriptGenerator`로 binding했다.
- Supertonic provider wiring은 `TtsSynthesisModule`로 이동된 구조를 사용했다.

판단 이유:

- 사용자가 “숏폼 편집용 원본 프로젝트도 파일 json에만 저장되어야 하지 않나? db를 안써야하는데”라고 했고, 이후 “아예 db 관련된거 다 빼버려”라고 했다.
- feature 방향은 web_api에 provider 호출을 몰아 desktop secret 보유를 줄이는 것이다.
- 최신 dev의 render pipeline은 `VideoRenderService`를 쓰는 쪽이므로 유지해야 한다.

재검토 포인트:

- `WebApiClipperStudioScriptGenerator`가 local-api/remote-api 환경에서 올바른 base URL을 쓰는지 패키지 앱 smoke 필요.
- JSON repository의 저장 경로가 packaged app과 devapp 모두 의도한 위치인지 확인 필요.

### `shortform-project.service.ts`

충돌 이유:

- dev 쪽은 최신 shortform render path를 `VideoRenderService.reserve()` / `submitReserved()` 중심으로 바꿨다.
- feature 쪽은 template snapshot fallback, default Template Builder preset, Supertonic TTS default, remote media materialization, web_api script path 등 여러 기능을 넣었다.
- 두 브랜치가 생성자 dependency, render 준비 path, template snapshot path, TTS default, media search query path를 동시에 수정했다.

dev 쪽 상태:

- constructor에 `RenderRecipeProvider`, `LegacyClipper1RenderPayloadMapper`가 남아 있었다.
- 실제 render submit 쪽은 `VideoRenderService` 기반으로 바뀌는 중이었다.
- TypeORM/Configured repository 경로와 맞물린 테스트가 있었다.

feature 쪽 상태:

- default TTS provider를 Supertonic으로 바꿨다.
- default speed를 `1.2`로 바꿨다.
- Template Builder 기본 템플릿 snapshot을 project 생성/수정/render에 보존하려 했다.
- media search 실패 시 query 후보를 여러 개 시도하도록 바꿨다.
- legacy render payload helper 쪽 fallback을 추가했지만, dev의 최신 render path와 충돌했다.

해결:

- constructor는 최신 dev render path에 맞춰 `VideoRenderService`를 사용하도록 정리했다.
- `RenderRecipeProvider`, `LegacyClipper1RenderPayloadMapper` dependency와 `legacyRenderPayloadFor()` private helper는 제거했다.
- render 준비는 `videoRender.reserve()`와 `videoRender.submitReserved()`를 쓰도록 했다.
- feature의 Supertonic default는 유지했다:
  - provider: `tts.supertone`
  - speaker: `F2`
  - speed: `1.2`
- feature의 Template Builder default/snapshot logic은 유지했다:
  - `defaultShortformTemplatePreset()`
  - `templateVersionSnapshotFor()`
  - `templatePresetSnapshotForRender()`
  - `withRenderableTemplateForLegacyRender()`
- render manifest 생성 전에 renderable Template Builder preset을 보장하도록 유지했다.
- media search query는 hint/narration/title 후보를 순차 시도하는 feature 쪽 로직을 유지했다.

판단 이유:

- dev의 render path가 더 최신 구조라, service가 직접 legacy payload를 만드는 helper를 계속 보유하면 중복/충돌 가능성이 컸다.
- feature의 핵심 사용자 요구는 “기본 템플릿 존재, 기본 템플릿 snapshot 유지, Supertonic default, JSON persistence”였으므로 유지해야 했다.

재검토 포인트:

- `withRenderableTemplateForLegacyRender()`는 이름에 legacy가 남아 있는데, 실제로는 render manifest가 Template Builder preset을 갖게 보정하는 역할이다. 2차 merge 때 이름/위치 재검토 가능.
- 삭제한 `legacyRenderPayloadFor()`가 실제 product path에서 더 이상 필요 없는지 `VideoRenderService.submitReserved()` 내부까지 다시 따라가 볼 필요가 있다.
- 테스트 harness에서 제거한 `legacyRenderPayloadFor` 직접 호출 테스트는 “private helper가 없어졌다”는 이유로 삭제했다. 이 판단은 2차 merge 때 다시 확인해야 한다.

### `tts-synthesis.provider.ts` / `tts-synthesis.module.ts`

충돌 이유:

- dev 쪽은 `src/modules/tts-synthesis/tts-synthesis.provider.ts`에 Naver Clova provider와 기본 Supertonic placeholder가 있었다.
- feature 쪽은 Supertonic plugin 기반 TTS provider를 별도 shortform infrastructure path에 추가한 상태였다.
- 두 브랜치의 TTS provider 위치와 provider registry 구조가 달랐다.

dev 쪽 상태:

- Naver Clova provider가 실제 HTTP 호출과 secret/env를 직접 사용했다.
- output은 MP3 중심이었다.
- default speed는 Clova 기준이었다.

feature 쪽 상태:

- Supertonic plugin client를 통해 WAV를 생성한다.
- provider secret을 desktop NestJS에서 직접 쓰지 않는 방향.
- default speed는 `1.2`.
- WAV/MP3 duration parsing helper가 있었다.

해결:

- dev의 `src/modules/tts-synthesis` module 위치를 유지했다.
- provider 구현은 feature의 Supertonic plugin 기반으로 바꿨다.
- Naver Clova provider는 제거했다.
- `ShortformTtsProviderRegistry`는 Supertonic aliases만 허용한다.
- `TtsSynthesisModule`은 `PluginsModule`, `TtsPluginClient`, `TtsVoiceCatalog`, `SupertonicShortformTtsProvider`를 wiring한다.

판단 이유:

- feature의 provider-runtime-isolation 방향은 desktop app에서 provider secret 직접 호출을 줄이는 것이다.
- 사용자가 Supertonic TTS 기본값과 speed/pitch 관련 검증을 이미 완료했다고 정리했다.

재검토 포인트:

- UI preset 목록이 `TtsVoiceCatalog`와 정확히 연결되는지 앱에서 확인 필요.
- WAV duration parsing이 실제 Supertonic output에서 안정적인지 최종 render timing smoke 필요.

### `test/shortform-tts-provider.test.js`

충돌 이유:

- dev 테스트는 Naver Clova provider와 기존 registry를 검증했다.
- feature 테스트는 Supertonic plugin TTS, WAV output, speed clamp/default를 검증했다.

해결:

- Supertonic-only provider 테스트로 정리했다.
- `tts.naver_clova`는 unknown provider로 거절되는 기대를 유지했다.
- default speed `1.2` 테스트 유지.

재검토 포인트:

- product에서 Naver Clova TTS를 완전히 제거하는 것이 맞는지 확인 필요.

### `test/workflow-executor-registry.test.js`

충돌 이유:

- dev 테스트는 virtual workflow executor에 install-state repository가 들어가는 구조를 검증했다.
- feature 테스트는 dialog highlight NestJS-native executor 우선순위와 Python fallback 제거를 검증했다.

해결:

- `createInstalledRepo()` helper를 추가/사용했다.
- `WorkflowExecutorRegistry` 생성자는 `installedWorkflows`와 `dialogHighlight`를 모두 받도록 테스트를 정렬했다.
- dialog highlight가 NestJS-native executor로 우선 노출되고, Python manifest fallback을 하지 않는 테스트를 유지했다.

재검토 포인트:

- 사용자가 원하면 “NestJS-native dialog executor 실패 시 Python fallback 허용” 정책으로 바꿀 수 있지만, 현재 feature 의도는 fallback 금지다.

### `test/shortform-project-generation-assets.test.js`

이 파일은 Git conflict 목록에는 없었지만, merge 후 Nest 테스트 실패를 고치면서 수정했다.

문제:

- `ShortformProjectService` constructor argument 순서가 dev/feature 병합 후 바뀌었다.
- 오래된 직접-instantiation 테스트들이 제거된 `RenderRecipeProvider` / `LegacyClipper1RenderPayloadMapper` 자리에 빈 객체를 넘기고 있었다.
- 그 결과 `ConfigService` 자리에 엉뚱한 객체가 들어가 `this.config.get is not a function`으로 다수 테스트가 실패했다.

해결:

- test-only wrapper를 추가했다:
  - `RealShortformProjectService`를 import한다.
  - `ShortformProjectService(...args)` wrapper가 legacy 빈 placeholder를 제거해 현재 constructor 순서에 맞춘다.
- remote media/materialization 테스트 중 fake provider/jobs가 한 칸 밀린 케이스는 인자 위치를 직접 조정했다.
- 제거된 `legacyRenderPayloadFor()` private helper 직접 호출 테스트는 삭제했다.
- 바로 다음 테스트인 “shortform render normalizes legacy-incompatible shortform template before building legacy payload”는 실제 manifest + recipe + mapper 조합을 검증하므로 유지했다.

재검토 포인트:

- 이 wrapper는 테스트 compatibility용 임시 완충에 가깝다.
- 2차 merge 때는 테스트마다 `createShortformProjectService()` factory를 명시적으로 만드는 것이 더 좋다.
- 삭제한 private helper 직접 호출 테스트가 product behavior coverage를 잃지 않았는지 확인 필요.

## Python 충돌 상세

### 핵심 질문: stage runner가 뭐냐?

`stage_runner.py`는 dialog highlight Python plugin의 기존 “한 번에 전체 파이프라인 실행” 방식을 여러 단계로 나누어 실행하게 하는 dispatcher다.

현재 stage 목록:

- `prepare_media`
- `analyze_media`
- `build_candidates`
- `render_highlights`

동작 방식:

- Electron/NestJS plugin host가 Python plugin job을 호출할 때 `params.stage`를 넣는다.
- `dialog_highlight/app.py`의 `run_job()`이 이 `stage` 값을 읽는다.
- `run_job()`은 `DialogStageRequest`를 만들고 `run_dialog_stage()`에 넘긴다.
- `run_dialog_stage()`는 stage 이름에 따라 다음 함수로 분기한다:
  - `run_prepare_media()`
  - `run_analyze_media()`
  - `run_build_candidates()`
  - `run_render_highlights()`

왜 필요한가:

- dialog highlight는 영상 분석, STT, shot detection, visual/audio embedding 같은 무거운 로컬 미디어 작업과, sentence split/story/highlight selection/title generation 같은 LLM/provider 작업이 섞여 있었다.
- feature의 방향은 provider 호출을 Python plugin에서 직접 하지 않고 local NestJS/web_api가 담당하게 하는 것이다.
- 그러려면 Python이 한 번에 OpenAI까지 호출하는 monolithic pipeline이면 안 된다.
- Python은 media artifact를 만들고, NestJS/web_api가 LLM artifact JSON을 만든 뒤, 다시 Python이 그 artifact를 받아 후보/렌더를 진행해야 한다.

stage별 artifact 흐름:

1. `prepare_media`
   - output directory와 `json/` directory를 만든다.
   - 아직 무거운 분석은 하지 않는다.

2. `analyze_media`
   - Python이 로컬 media analysis를 수행한다.
   - 생성/저장:
     - `analysis.json`
     - `silence.json`
     - `stt.json`
     - `shots.json`
   - 반환:
     - `analysis_path`
     - `duration_sec`
     - `num_highlights`

3. NestJS/web_api LLM 단계
   - 이 부분은 Python stage runner 안에 없다.
   - NestJS dialog highlight workflow executor가 web_api를 호출해서 다음 JSON들을 만든다.
   - 예:
     - `llm_sentences.json`
     - `story_backbone.json`
     - `canonical_info.json`
     - `topics.json`
     - `gpt_highlight_selection.json`
     - `highlights_meta.json`

4. `build_candidates`
   - Python이 `analysis.json`과 LLM artifact 일부를 읽는다.
   - sentence span, raw segment, semantic segment, highlight candidates를 만든다.
   - 생성/저장:
     - `sentence_spans.json`
     - `raw_segments.json`
     - `semantic_segments.json`
     - `highlight_candidates.json`

5. `render_highlights`
   - Python이 selection/meta artifact를 읽는다.
   - 최종 clip 구간을 정리하고 실제 clip export/manifest 생성.
   - 생성/저장:
     - `semantic_clips.json`
     - `clip_stt.json`
     - `manifest.json`
     - clip files

따라서 `stage_runner`는 provider 호출 자체가 아니라 “Python stage를 job param으로 나눠 실행하는 얇은 라우터”다.

### `plugins/dialog_highlight/dialog_highlight/services/pipeline.py`

충돌 유형:

- modify/delete.

dev 쪽 상태:

- 기존 단일 `pipeline.py`가 없어지고 `services/pipeline/` package로 분해되어 있었다.
- package 구성:
  - `common.py`
  - `media_utils.py`
  - `ocr_pipeline.py`
  - `embedding_pipeline.py`
  - `stt_pipeline.py`
  - `segmentation_pipeline.py`
  - `llm_strategies.py`
  - `orchestrator.py`
  - `__init__.py`
- `orchestrator.py`에는 여전히 monolithic `run_pipeline_for_video()`가 있고, 이 경로는 provider/LLM helper를 호출하는 구조였다.

feature 쪽 상태:

- 단일 `pipeline.py` 파일이 남아 있었다.
- 그 파일 안에 stage 실행에 필요한 함수들이 추가되어 있었다:
  - `analyze_video_to_artifacts()`
  - `build_candidates_from_artifacts()`
  - `render_highlights_from_artifacts()`
- provider 직접 호출을 제거하고 “LLM artifact creation is handled by local NestJS/web_api”라는 방향이었다.
- `llm_client.py` 삭제.
- `stage_contracts.py`, `stage_runner.py` 추가.

충돌 원인:

- dev는 파일을 package로 이동/분해했다.
- feature는 삭제된 옛 파일에 stage 함수들을 계속 추가했다.
- Git 입장에서는 “dev에서 파일 삭제, feature에서 같은 파일 수정”이다.

해결:

- 옛 단일 `pipeline.py`는 삭제 상태를 유지했다.
- dev의 `services/pipeline/` package 구조를 유지했다.
- feature의 stage 함수 세 개와 helper들을 `services/pipeline/__init__.py`에 이식했다:
  - `analyze_video_to_artifacts()`
  - `build_candidates_from_artifacts()`
  - `render_highlights_from_artifacts()`
  - stage 함수들이 필요한 artifact conversion helper들
- `stage_runner.py`는 그대로 유지했고, 이 함수들이 `from .pipeline import ...`으로 import될 수 있게 했다.

판단 이유:

- dev의 package decomposition은 구조적으로 큰 refactor라 되돌리면 최신 dev 변경을 잃는다.
- feature의 staged execution은 provider-runtime-isolation의 핵심이라 버리면 안 된다.
- 그래서 “dev package 유지 + feature stage function 이식”으로 해결했다.

재검토 포인트:

- stage 함수들을 `__init__.py`에 많이 넣은 것은 빠른 conflict resolution이다.
- 2차 merge 때는 `services/pipeline/staged.py` 같은 새 파일로 분리하는 편이 더 명확할 수 있다.
- `__init__.py`가 re-export shim 역할과 stage implementation 역할을 동시에 하게 된 점은 구조적으로 깨끗하지 않다.

### `services/pipeline/llm_strategies.py`

충돌/보정 이유:

- dev의 `llm_strategies.py`는 OpenAI chat completions를 직접 호출하는 함수들을 갖고 있었다.
- feature의 provider guard 테스트는 dialog Python code가 OpenAI import/provider env/direct client call을 갖지 않아야 한다.
- staged architecture에서는 LLM 작업이 Python이 아니라 NestJS/web_api로 이동해야 한다.

해결:

- `llm_strategies.py`를 provider-free stub으로 교체했다.
- 기존 symbol 이름은 남겨 두었다:
  - `call_gpt_json_with_retry`
  - `llm_split_sentences_from_text`
  - `llm_split_sentences_all_shots`
  - `build_story_backbone_gpt`
  - `build_canonical_info_gpt`
  - `gpt_define_highlight_topics`
  - `build_events_from_blocks_gpt`
  - `call_gpt_select_highlights`
  - `build_highlights_meta_gpt`
- 호출되면 `RuntimeError("dialog_highlight LLM stages run through local NestJS/web_api")`를 던진다.
- `dedup_llm_sentences_in_same_window()`은 identity function으로 남겼다.

판단 이유:

- old imports나 tests가 symbol 존재를 기대할 수 있다.
- 하지만 Python에서 provider call이 실제로 실행되면 안 된다.
- 그래서 symbol은 유지하고 실행은 막았다.

재검토 포인트:

- `orchestrator.py`는 여전히 `run_pipeline_for_video()` 안에서 provider flow를 기대하는 구조다.
- 현재 `app.py`는 `stage` 없이 호출되면 `dialog_highlight requires staged execution through local NestJS` 에러를 반환하므로 monolithic path는 막혀 있다.
- 하지만 누군가 `pipeline.run_pipeline_for_video()`를 직접 호출하면 stub/삭제된 `llm_client.py` 때문에 실패한다.
- 이것이 의도된 실패인지, 아니면 `run_pipeline_for_video()` 자체도 제거/명시적 error로 바꿀지 2차 merge 때 확인해야 한다.

### `app.py`와 no-stage behavior

dev 쪽 상태:

- 기존 plugin job은 monolithic pipeline을 호출할 수 있었다.

feature 쪽 상태:

- `stage` param이 있을 때만 stage runner를 호출한다.
- `stage` param이 없으면 `dialog_highlight requires staged execution through local NestJS`를 반환한다.

해결:

- feature의 no-stage 차단 behavior를 유지했다.

판단 이유:

- provider-runtime-isolation의 핵심은 Python plugin이 직접 LLM provider까지 실행하지 않게 하는 것이다.
- NestJS가 stage 순서를 orchestrate해야 한다.

재검토 포인트:

- 앱에서 dialog_highlight를 실행하는 모든 경로가 NestJS staged executor를 타는지 확인 필요.
- Python plugin 단독 실행/개발용 명령이 필요하면 별도 dev-only path를 명확히 만들어야 한다.

## Electron 병합 상세

수동 충돌 없음.

병합 결과:

- 최신 dev의 media-dir/download 관련 변경과 feature의 Windows reset/local API build 관련 변경이 자동 병합됐다.

재검토 포인트:

- Windows local-api build README 내용을 제거하고 `.codex`에만 두기로 했던 흐름이 있었지만, 이 통합에서는 `.codex`를 건드리지 않았다.
- Windows reset script fix는 merge commit 안에 포함되어 있다.

## Web API 병합 상세

수동 Git conflict 없음.

merge 후 문제:

- `src/modules/shortform-script/presentation/script.controller.ts`에서 `@UseGuards(ScriptServiceTokenGuard)`가 남아 있었지만 import가 없었다.
- `npm run build`가 실패했다.

해결:

- `@nestjs/common` import에 `UseGuards` 추가.
- `ScriptServiceTokenGuard` import 추가.
- 별도 commit: `0200a50 Fix shortform script guard import`

판단 이유:

- dev 쪽 variation endpoint가 token guard를 추가했고, feature 쪽 script hardening 변경이 같은 controller에 들어오면서 import만 빠진 상태였다.

재검토 포인트:

- `/llm/variation` endpoint가 token guard 대상인 것이 맞는지 확인 필요.
- `/llm/script` endpoint도 같은 guard가 필요한지 정책적으로 확인 가능하다.

## 내가 임의 판단한 부분 / 반드시 재검토할 부분

아래는 “테스트 통과”와 별개로 사용자가 의도와 맞는지 확인해야 하는 지점이다.

1. Python stage 함수 위치

- 현재는 `services/pipeline/__init__.py`에 stage implementation이 들어갔다.
- 동작은 하지만 구조적으로 좋은 위치는 아닐 수 있다.
- 2차 merge 때 `services/pipeline/staged.py` 같은 파일로 분리하는 것이 더 낫다.

2. Python `llm_strategies.py` stub 처리

- provider direct call 제거를 위해 stub으로 바꿨다.
- monolithic `run_pipeline_for_video()`가 살아 있지만 사실상 호출 불가/실패 경로가 됐다.
- 이것을 명시적으로 제거할지, error-only function으로 바꿀지 다시 결정해야 한다.

3. Nest `legacyRenderPayloadFor()` 제거

- dev의 최신 render path가 `VideoRenderService.submitReserved()`로 payload build를 담당하므로 service private helper는 제거했다.
- 하지만 기존 테스트 중 private helper 직접 호출 테스트도 삭제했다.
- product behavior가 충분히 다른 테스트로 커버되는지 확인 필요.

4. `test/shortform-project-generation-assets.test.js` wrapper

- constructor 호환을 위해 test-only wrapper가 legacy placeholder를 제거한다.
- 빠른 병합 보정으로는 유효하지만 장기적으로는 명시적인 service factory가 더 낫다.

5. Naver Clova TTS 제거

- 최종 provider registry는 Supertonic만 허용한다.
- 이것이 제품 의도와 완전히 맞는지 확인 필요.

6. dialog highlight fallback 금지

- NestJS-native dialog executor가 있으면 Python manifest fallback을 하지 않는다.
- 현재 테스트도 fallback 금지를 검증한다.
- 실제 운영에서 NestJS-native executor manifest가 깨졌을 때 어떤 UX가 맞는지 확인 필요.

7. `.env.packaged` 삭제 유지

- Git에서는 삭제가 맞다.
- 하지만 패키지 앱 build/test에는 ignored local `.env.packaged`가 여전히 필요할 수 있다.

## 2차 merge를 다시 한다면 추천 절차

사용자 의도 확인을 위해 새 브랜치에서 병합을 다시 하는 것이 좋다.

권장 브랜치명 예:

- `integration/plugin-runtime-isolation-20260703-review2`

권장 절차:

1. 모든 app repo에서 `dev` 최신화.
2. `dev`에서 새 통합 브랜치 생성.
3. `origin/feature/plugin-runtime-isolation` merge.
4. 충돌은 이 문서의 파일별 판단과 대조하면서 해결.
5. 특히 Python은 아래 질문에 답하고 진행:
   - stage 함수는 `__init__.py`에 둘 것인가, 별도 `staged.py`로 뺄 것인가?
   - `orchestrator.py/run_pipeline_for_video()`는 남길 것인가, 명시적 error로 바꿀 것인가?
   - `llm_strategies.py`는 stub 유지가 맞는가?
6. Nest는 아래 질문에 답하고 진행:
   - `legacyRenderPayloadFor()` 제거가 맞는가?
   - Supertonic-only가 맞는가?
   - shortform project test wrapper를 둘 것인가, explicit factory로 정리할 것인가?
7. Angular는 UI text와 버튼 상태를 실제 화면에서 확인.
8. Web API는 script/variation guard 정책 확인.

## 이번 1차 병합 검증 결과

통과한 검증:

- `desktop/clipper_angular`: `npm run build -- --progress=false`
- `desktop/clipper_electron`: `npm run build`
- `web/clipper_web_api`: `npm run build`
- `desktop/clipper_nestjs`: `npm run build`
- `desktop/clipper_nestjs`: 관련 `node --test ...` 42개 통과
- `desktop/clipper_python`: 관련 pytest 31개 통과
- staged diff check 통과

검증하지 않은 것:

- 패키지 앱 end-to-end smoke.
- Windows packaged/unpacked 앱 smoke.
- Dialog/Dance plugin install 후 restart persistence.
- ffmpeg/ffprobe consent/install state flow.
- Prompt/Dialog/Dance 최종 영상 생성과 timing 검증.

## 다음에 내가 다시 병합한다면 바꿀 수 있는 점

1. Python stage implementation을 처음부터 별도 파일로 분리한다.
2. Nest shortform test는 wrapper 대신 `createService()` factory로 정리한다.
3. `legacyRenderPayloadFor()` 삭제 판단은 먼저 `VideoRenderService.submitReserved()`와 mapper coverage를 추적한 뒤 결정한다.
4. `orchestrator.py`의 monolithic path는 남겨둘지 제거할지 사용자 확인을 먼저 받는다.
5. Web API guard 정책은 `/llm/script`와 `/llm/variation` 모두 명시적으로 확인한다.
