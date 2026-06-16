# Shortform Browser Preview Debugging, 2026-06-16

## Scope

이번 작업은 shortform 제작 페이지의 browser timeline preview 1차 구현을 실제
packaged app 흐름에서 검증하면서 발견된 문제를 작은 단위로 고친 것이다.

확인한 주요 흐름:

- Template Builder에서 만든 custom shortform template이 제작 페이지 템플릿 목록에
  노출된다.
- 클립 생성 후 browser preview가 9:16 화면에서 재생, seek, style 반영, TTS,
  BGM을 처리한다.
- preview에서 사용하는 template font, template asset, BGM file은 packaged app의
  local Nest API를 통해 로드된다.

Project-first, Plugin, Queue 정리는 이 작업에서 시작하지 않았다.

## Symptoms

사용자 테스트 중 다음 문제가 반복해서 확인됐다.

- 템플릿 카드 thumbnail이 깨진 이미지로 보였다.
- preview에서 TTS가 끝까지 재생되지 않거나 clip 전환 시 이전 TTS의 앞부분이 잠깐
  들렸다.
- template background color, font, font size, caption box style, caption line
  gap이 Template Builder와 다르게 보였다.
- caption이 한 줄만 보이고 두 번째 줄은 잘렸다.
- clip 전환 시 다음 clip asset 대신 마지막 clip asset 또는 빈 dotted placeholder가
  잠깐 보였다.
- seek bar의 총 시간이 재생 중 증가하고 playhead가 뒤로 튀었다.
- style section의 BGM/voice sample과 preview audio가 동시에 재생될 수 있었다.
- BGM file URL과 font file URL이 browser console에서 500으로 실패했다.
- subtitle text 수정 시 마지막 한글 글자가 잠깐 중복되어 보였다.
- TTS 재생성 후 clip duration label이 갱신되지 않거나, clip drag order가 원래
  생성 순서로 돌아갔다.

## Root Causes

### 1. Font asset URI shape mismatch

초기 preview runtime data에는 local absolute path가 그대로 들어올 수 있었다.

예:

```text
/Users/jina/Library/Application Support/Clipper2/template-assets/.../fonts/...
```

browser preview가 이 값을 그대로 `/v1/template-builder/assets/file?uri=...`에
넘기면 packaged app의 local API에서 경로 해석과 보안 allowlist 처리가 안정적으로
맞지 않았다.

수정 후 preview font URL은 app data root를 제거한 relative URI만 사용한다.

예:

```text
http://127.0.0.1:{port}/v1/template-builder/assets/file?uri=template-assets%2Fcustom.template...%2F1_1%2Ffonts%2FmainTitleLine1_..._Shilla_Culture_B.ttf
```

font retry가 필요한 경우 cache busting query만 추가된다.

```text
&previewFontRetry=1
```

### 2. Generic template asset endpoint was image-oriented

`/v1/template-builder/assets/file`은 thumbnail/image 계열 asset 중심으로 동작하고
있었다. Browser preview는 같은 endpoint로 `.ttf` font도 가져와야 했고, BGM과
template file도 packaged app의 bundled/local 경로에서 안정적으로 찾아야 했다.

수정 내용:

- template asset resolver가 `template-assets/...` relative URI를 local app data
  root 기준으로 해석한다.
- persisted custom template의 absolute asset path도 호환 경로로 계속 허용한다.
- font extension에 맞는 content type을 내려준다.
- allowlist 내부 파일이 없을 때 raw 500 대신 404를 반환한다.

### 3. Electron renderer Origin was rejected by CORS

가장 오래 남았던 font 500의 직접 원인은 CORS였다.

검증 결과:

- 같은 packaged app endpoint를 `curl`로 Origin 없이 호출하면 font file이 200으로
  내려왔다.
- 같은 URL에 `Origin: file://` header를 붙이면 500이 발생했다.
- Electron packaged renderer의 `FontFace.load()` 요청은 `Origin: file://`를 보내고
  있었다.

기존 CORS origin checker는 다음 정도만 허용했다.

- Origin 없음
- `null`
- localhost
- `127.0.0.1`

`file://`가 빠져 있어서 Electron renderer font request만 실패했다. 이 때문에 URL을
relative URI로 고친 뒤에도 browser console에는 계속 500이 남았다.

수정 내용:

- `clipper_nestjs/src/config/local-api-cors-origin.ts`를 추가했다.
- local API CORS allowlist에 `file://`를 명시적으로 허용했다.
- `clipper_nestjs/src/main.ts`는 이 helper를 사용해 CORS origin 판정을 수행한다.

검증 결과, 새 bundle에서 `Origin: file://` 요청은 다음처럼 성공했다.

```text
HTTP/1.1 200 OK
Access-Control-Allow-Origin: file://
Content-Type: font/ttf
Content-Length: 8849936
```

### 4. Preview timeline depended on mutable playback state

처음 구현된 browser preview는 audio element가 실제로 로드되면서 알게 되는 duration에
많이 의존했다. 그래서 테스트 fixture를 불러온 뒤 재생 중 총 시간이 0:22에서 0:31처럼
늘어나거나, playhead가 뒤로 튀는 현상이 생겼다.

수정 내용:

- preview timeline을 만들기 전에 TTS duration을 먼저 측정해 total duration을
  고정한다.
- clip/project/TTS가 업데이트되는 동안 preview playback을 멈추고 playhead를 0으로
  reset한다.
- TTS 재생성 완료 후 preview state를 한 번에 갱신한다.
- seek bar 표시를 percentage가 아니라 `현재 시간 / 총 시간` 형태로 바꿨다.
- style sample audio와 preview playback은 서로 시작 시점에 상대 audio를 멈춘다.

### 5. Style projection needed browser-specific mapping

Template Builder의 runtime spec은 9:16 canvas 좌표와 style 정보를 담고 있지만,
browser preview에는 CSS로 다시 투영하는 단계가 필요했다. 이 단계가 부족해서 text
size, caption wrapping, caption box, background, line gap이 Builder와 다르게 보였다.

수정 내용:

- runtime spec에 caption `linePositions`를 포함했다.
- preview caption은 줄 전체를 하나의 큰 박스로 감싸지 않고, 실제 표시되는 각 line
  box를 따로 그린다.
- 한 줄 caption이면 한 줄 box만 표시한다.
- 두 줄 caption이면 template의 line position/gap을 사용한다.
- text size는 preview canvas 기준으로 안정적으로 환산한다.
- template background color를 preview layout background에 반영한다.
- media는 저해상도 thumbnail보다 `contentUrl`을 우선 사용한다.

### 6. TTS regeneration did not preserve local editing state

재생속도 또는 voice 변경 시 전체 TTS를 다시 생성하는 과정에서 backend 기준의 원래 clip
순서가 다시 적용될 수 있었다. 또한 line text 수정 후 TTS duration이 바뀌어도 clip의
표시 duration이 갱신되지 않았다.

수정 내용:

- full TTS regeneration은 현재 UI의 clip order를 보존한다.
- per-line TTS regeneration과 full TTS regeneration 모두 변경된 line duration과
  clip duration을 응답으로 반영한다.
- 개별 subtitle 수정 중에는 TTS regeneration spinner/status를 표시한다.
- 한글 조합 입력 후 Enter 처리에서 마지막 글자가 잠깐 중복되어 보이는 상태 갱신
  경합을 제거했다.

## Files Changed

### Angular

- `clipper_angular/src/features/shortform/components/preview/shortform-browser-preview-timeline.ts`
- `clipper_angular/src/features/shortform/components/preview/shortform-browser-timeline-preview.component.ts`
- `clipper_angular/src/features/shortform/components/preview/shortform-browser-timeline-preview.component.html`
- `clipper_angular/src/features/shortform/components/preview/shortform-browser-timeline-preview.component.scss`
- `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.ts`
- `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.html`
- `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.scss`
- `clipper_angular/src/features/shortform/services/shortform-project.service.ts`
- related Angular shortform specs

### NestJS

- `clipper_nestjs/src/config/local-api-cors-origin.ts`
- `clipper_nestjs/src/main.ts`
- `clipper_nestjs/src/template-builder/template-builder.service.ts`
- `clipper_nestjs/src/template-builder/shortform-template-runtime-spec.ts`
- `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`
- `clipper_nestjs/src/shortform/shortform-bgm-catalog.ts`
- `clipper_nestjs/src/shortform/shortform-project.controller.ts`
- `clipper_nestjs/src/shortform/shortform-project.service.ts`
- related NestJS tests

## Verification

Latest verification for this change set:

```text
clipper_angular:
- npm test -- --watch=false --include='src/features/shortform/**/*.spec.ts'
- npm run build
- git diff --check

clipper_nestjs:
- npm run build
- node --test test/template-builder-asset-file.test.js test/template-builder-shortform-preset-source.test.js test/template-builder-shortform-mode.test.js test/shortform-project-preview-fixture.test.js test/shortform-bgm-catalog.test.js test/local-api-cors-origin.test.js
- git diff --check

clipper_electron:
- npm run build:app:mac:arm64
```

Observed result:

- Angular shortform specs passed.
- Angular production build passed.
- NestJS build passed.
- Focused NestJS node tests passed.
- Electron mac arm64 packaged app build passed.
- `git diff --check` passed in both changed repositories.

## Operational Notes

- After changing CORS or bundled NestJS code, the packaged Electron app must be
  rebuilt and restarted. An already-running app process keeps the old CORS policy.
- If font loading fails again, compare the same font URL with and without
  `Origin: file://`. A 200 without Origin and failure with `file://` indicates a
  CORS regression.
- The browser preview aims for practical authoring parity with final FFmpeg
  render, not exact pixel identity. Caption wrapping can still diverge slightly
  from FFmpeg text layout and should be treated as a future parity improvement
  unless it blocks editing.
- BGM now has an explicit no-music option. When selected, preview and final render
  should both omit BGM.

