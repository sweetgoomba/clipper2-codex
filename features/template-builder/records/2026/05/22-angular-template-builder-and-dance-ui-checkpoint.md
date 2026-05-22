# 2026-05-22 Angular Template Builder / Dance UI Checkpoint

작성일: 2026-05-22

## Scope

이번 작업은 Windows packaged env/runtime 정리 이후 `clipper_angular`에서 발견된 UI/UX 문제와 Template Builder ffmpeg/ffprobe readiness 문제를 정리한 것이다.

Root `.codex` 문서는 git repo가 아니므로 커밋 대상이 아니다.

## Repo State

작업 완료 후 repo 상태:

```text
clipper_nestjs:   feature/windows-packaging @ 9cd43f1 Trim optional env placeholders
clipper_electron: feature/windows-packaging @ f701677 Revert "Update electron builder"
clipper_angular:  feature/initial-scaffold  @ cad4b6c Gate template builder startup on ffmpeg readiness
clipper_python:   feature/windows-packaging @ 88d22c6 Trim optional env placeholders
```

네 repo 모두 origin과 동기화된 clean 상태다.

## Completed Angular Commits

```text
4785375 Fix dance setup vertical scrolling
584570c Center dance member image selector
bf4374e Extract template family thumbnail loading
e9c348b Guard template builder renders on ffmpeg readiness
cad4b6c Gate template builder startup on ffmpeg readiness
```

## Dance Setup Scroll / Centering

문제:

- 안무 플러그인 멤버별 이미지 선택 페이지에서 세로 스크롤이 되지 않았다.
- 멤버별 이미지 선택 내부 컨테이너가 왼쪽으로 치우쳐 중앙 정렬이 깨져 보였다.

수정:

- `dance-setup.component.scss`
  - 페이지 shell이 viewport 안에서 고정되고 내부 단계 영역이 스크롤을 소유하도록 정리.
- `member-image-select.component.scss`
  - host width를 `min(1080px, 100%)`로 제한하고 block width를 명시.
  - 내부 `.wrap`이 host 전체 폭을 사용하도록 정리.
- `dance-setup.component.spec.ts`
  - 스크롤 ownership과 멤버 이미지 선택 단계 중앙 정렬 회귀 테스트 추가.

검증:

```text
clipper_angular npm test -- --watch=false --include src/features/dance-highlight/pages/dance-setup/dance-setup.component.spec.ts
clipper_angular npm run build -- --progress=false
```

## Template Builder Card Thumbnail Loading

문제:

- Template Builder 목록에서 thumbnail 이미지가 로딩되기 전 카드가 검정 배경으로 보였다.
- 여러 이미지가 decode/load된 뒤 한꺼번에 thumbnail이 세팅되는 것처럼 보이는 UX였다.

원인:

- `TemplateFamilyCardComponent`가 thumbnail `<img>`와 fallback 상태를 직접 관리했다.
- thumbnail 로딩 전 `.thumb` 배경이 어두운 fallback으로 먼저 보였다.

수정:

- `TemplateFamilyThumbnailComponent`를 새로 분리.
- thumbnail loading 전에는 skeleton placeholder를 보여준다.
- 이미지 load 완료 후에만 실제 thumbnail 상태로 전환한다.
- gallery/card 컴포넌트는 thumbnail loading 세부 상태를 직접 알지 않도록 역할을 분리했다.

주요 파일:

```text
clipper_angular/src/features/template-builder/components/template-family-thumbnail.component.ts
clipper_angular/src/features/template-builder/components/template-family-thumbnail.component.html
clipper_angular/src/features/template-builder/components/template-family-thumbnail.component.scss
clipper_angular/src/features/template-builder/components/template-family-thumbnail.component.spec.ts
clipper_angular/src/features/template-builder/components/template-family-card.component.*
clipper_angular/src/features/template-builder/components/template-family-gallery.component.spec.ts
```

검증:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-family-thumbnail.component.spec.ts
clipper_angular npm test -- --watch=false --include src/features/template-builder/components/template-family-gallery.component.spec.ts
clipper_angular npm run build -- --progress=false
```

## Template Builder ffmpeg/ffprobe Readiness

정정된 결론:

- Template Builder 목록 API 자체는 ffmpeg/ffprobe를 직접 쓰지 않는다.
- 하지만 Template Builder 기능 안에는 ffmpeg/ffprobe가 필요한 기능 흐름이 있다.
- 따라서 사용자 관점에서는 Template Builder 진입 전에 ffmpeg/ffprobe 설치 여부를 확인하는 것이 맞다.

ffmpeg/ffprobe가 필요한 기능 흐름:

1. 샘플 렌더
   - Angular `TemplateBuilderService.startSampleRender()`
   - NestJS `TemplateBuilderSampleRenderService.start()`
   - `video.render.legacy_clipper1.python_worker`
   - `clipper1_video_render` Python worker
   - worker가 mp4/thumbnail 생성을 수행하므로 ffmpeg/ffprobe 준비가 필요하다.

2. 텍스트 프리뷰 아티팩트
   - Angular `TemplateBuilderService.ensureTextPreviewRendererSession()`
   - NestJS `TemplateBuilderTextArtifactWorkerClient.ensureWarm()`
   - `clipper1_video_render` Python worker를 warm-up한다.
   - 페이지 진입 시 이 warm-up을 수행하므로 ffmpeg/ffprobe 준비 전에는 Template Builder 본 UI를 시작하지 않게 했다.

수정:

- `TemplateBuilderPageComponent` 생성 시 `FfmpegDownloadService.check()`를 호출한다.
- `state === ready | done`이 되기 전에는 Template Builder 본 UI를 렌더링하지 않는다.
- ready 이후에만 아래를 시작한다.
  - backend base URL 로드
  - template families 로드
  - text preview renderer worker warm-up
- 샘플 렌더 요청도 ffmpeg/ffprobe ready 여부를 다시 확인한다.

주의:

- `needsFfmpeg()`는 Electron main에서 `ffmpeg` 또는 `ffprobe` 중 하나라도 없으면 true를 반환한다.
- 이 흐름은 `.env.local`을 packaged에서 읽는 방식과 무관하다.
- plugin별 고정 포트를 다시 도입하지 않는다.

주요 파일:

```text
clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts
clipper_angular/src/features/template-builder/pages/template-builder-page.component.html
clipper_angular/src/features/template-builder/pages/template-builder-page.component.scss
clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts
```

검증:

```text
clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
# 57 SUCCESS

clipper_angular npm run build -- --progress=false
# passed

git -C clipper_angular diff --check
# passed
```

## Open Notes

- Windows packaged smoke에서 Template Builder 진입 시 ffmpeg/ffprobe consent overlay와 blocked gate가 기대대로 보이는지 확인한다.
- ffmpeg/ffprobe 설치 완료 후 Template Builder families load, text preview artifact, sample render가 정상 동작하는지 확인한다.
- PowerToys `Command Palette` / electron-builder `EBUSY` 원인과 우회 금지 정책은 그대로 유지한다.
