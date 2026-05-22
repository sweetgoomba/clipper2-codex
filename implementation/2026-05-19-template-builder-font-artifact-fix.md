# 2026-05-19 Template Builder Font Artifact Fix

## Context

Mac packaged build에서 Template Builder preview text가 처음에는 정상 텍스트로 보이다가, 잠시 뒤 final-render text artifact PNG로 교체된 후 한글이 작고 깨진 문자처럼 보였다.

처음에는 Angular live preview가 S3 font URL을 CSS `font-family`로 직접 쓰는 문제로 보였고, 실제로 그 문제도 있었다. 하지만 사용자가 재빌드 후에도 "처음에는 보이다가 변환 이후 깨진다"고 확인하면서, 최종 원인은 text artifact 생성 경로까지 포함해야 했다.

## Root Cause

Template Builder preview에는 두 경로가 있다.

- Angular DOM preview
  - 템플릿 선택 직후 바로 보이는 텍스트.
  - 브라우저에서 CSS font-family/FontFace 기준으로 렌더된다.
- Final-render text artifact preview
  - 잠시 뒤 NestJS가 Python worker에 요청해 생성하는 PNG 텍스트 이미지.
  - 실제 렌더 결과에 가까운 preview로 DOM 텍스트를 대체한다.

font 파일 번들링을 제거하고 S3 font 정책으로 바꾸는 과정에서 다음 문제가 겹쳤다.

1. 새 템플릿 기본 `fontFamily`가 S3 URL로 바뀌었지만 Angular live preview가 해당 URL을 `FontFace`로 등록하지 않았다.
2. 기존 local custom template JSON에는 `JalnanGothic.otf`, `Pretendard-SemiBold.otf`, `Pretendard-Bold.otf` 같은 예전 bare filename이 남아 있었다.
3. 공식/레거시 계열에는 `NanumMyeongjoExtraBold.otf`, `NanumSquareEB.otf` 같은 다른 bare legacy font filename도 있을 수 있다.
4. packaged app에는 font 파일을 번들링하지 않으므로 Python artifact renderer가 bare filename을 실제 font file로 찾지 못하면 PIL 기본 bitmap font로 fallback한다.
5. 이 fallback 때문에 artifact PNG의 한글이 작은 네모/깨진 문자처럼 보였다.

## Fixes

### Angular

- `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
  - remote `fontFamily` URL을 `FontFace`로 등록.
  - canvas preview CSS에는 URL 문자열이 아니라 generated font family name을 사용.

Commit:

- `clipper_angular` `4501146 Fix remote template font preview`

### NestJS

- `clipper_nestjs/src/template-builder/fixtures/new-template-baseline.json`
  - 새 템플릿 기본 font를 official S3 URL로 유지.
  - 각 text style에 `fontName` 추가.

- `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
  - fallback default text layer에도 S3 URL + `fontName` 적용.

Commit:

- `clipper_nestjs` `6679b91 Add font names to S3 template defaults`

### Existing Custom/Legacy Font Normalization

- `clipper_nestjs/src/template-builder/template-builder-font-references.ts`
  - Template Builder font reference normalization helper 추가.
  - API family 응답과 text artifact request 직전에 font reference를 normalize.
  - absolute/local upload path는 그대로 둔다.
  - bare `.otf`/`.ttf` filename은 `templates/legacy-clipper1/fonts/<filename>` official S3 URL로 변환한다.
  - known family name mapping:
    - `JalnanGothic.otf` -> `fontName: JalnanGothic`
    - `Pretendard-SemiBold.otf` -> `fontName: Pretendard`
    - `Pretendard-Bold.otf` -> `fontName: Pretendard`
  - 그 외 bare filename은 확장자 제거값을 `fontName`으로 사용한다.

- `clipper_nestjs/src/template-builder/template-builder.service.ts`
  - family를 API로 반환하기 전 normalize.

- `clipper_nestjs/src/template-builder/template-builder-text-artifact.service.ts`
  - Angular draft variant가 request body로 직접 넘어오는 경우도 Python worker 요청 전 normalize.

- `clipper_nestjs/test/template-builder-font-references.test.js`
  - 기본 3개 font filename normalize test.
  - `NanumMyeongjoExtraBold.otf` 같은 bare legacy filename normalize test.
  - uploaded absolute font path를 건드리지 않는 test.

Commits:

- `clipper_nestjs` `eed4bf2 Fix legacy custom template font artifacts`
- `clipper_nestjs` `c33fbd8 Normalize bare legacy template font filenames`

## Verification

- 실제 app data 확인:
  - `/Users/jina/Library/Application Support/Clipper2/templates/template-builder.json`
  - 일부 custom family에 `JalnanGothic.otf`, `Pretendard-*.otf` bare filename이 남아 있음을 확인.
  - uploaded custom font는 absolute path로 존재하고 실제 파일도 있음.

- Smoke:
  - 기존 custom family normalize 후 `JalnanGothic.otf`가 official S3 URL + `JalnanGothic`으로 변환됨.
  - Python text artifact export smoke에서 정상 한글 PNG 확인.
  - `NanumMyeongjoExtraBold.otf` smoke에서 official S3 URL + `NanumMyeongjoExtraBold`로 변환되고 정상 한글 PNG 확인.
  - uploaded absolute font path smoke에서 정상 한글 PNG 확인.

- Commands:
  - `clipper_nestjs npm run build`: passed.
  - `clipper_nestjs node --test test/template-builder-font-references.test.js`: 2 passed.
  - `clipper_nestjs git diff --check`: passed.
  - `clipper_electron npm run build:app:mac:arm64`: passed.

## User Confirmation

사용자가 재빌드 후 Template Builder preview 변환 이후에도 텍스트가 정상 표시됨을 확인했다.

## Current Repo State

- `clipper_nestjs`
  - branch: `feature/windows-packaging`
  - latest relevant commit: `c33fbd8 Normalize bare legacy template font filenames`
  - worktree clean at last check.

- `clipper_angular`
  - branch: `feature/initial-scaffold`
  - ahead of origin by 2 at last check.
  - relevant commit: `4501146 Fix remote template font preview`
  - worktree clean at last check.

- `clipper_electron`
  - branch: `feature/windows-packaging`
  - worktree clean at last check.

## Notes

- 이 fix는 bare legacy filename을 official S3 font URL로 해석하는 compatibility layer다.
- uploaded custom font absolute path는 local user template 저장 정책상 그대로 유지한다.
- font 파일을 app resource로 번들링하는 방향은 사용자가 명시적으로 제외했고, 현재 정책은 DB/S3 official font URL + local upload path다.
