# Template Builder API Test Follow-up

작성일: 2026-05-19
상태: 현재 작업 범위 밖, 후속 정비 필요

## 배경

Windows packaging 작업 중 다음 정책 정리를 했다.

- 공식 Template Builder templates는 DB/S3가 source of truth다.
- 공식 template font는 DB payload의 S3 URL을 사용한다.
- 앱 설치 파일에 legacy font 파일을 번들링하지 않는다.
- 새 custom template baseline도 filename font 대신 official S3 font URL을 기본값으로 사용한다.

관련 최신 커밋:

- `clipper_electron` `e264865 Remove external font packaging dependency`
- `clipper_python` `5a61a62 Revert "Bundle legacy template fonts"`
- `clipper_nestjs` `2b6bab8 Use S3 fonts for new template defaults`

## 현재 실패 명령

`clipper_nestjs`에서:

```bash
npm run build
node --test test/template-builder-api.test.js
```

`npm run build`는 성공한다.

`node --test test/template-builder-api.test.js`는 실패한다.

## 실패 유형 1: sample subtitle expectation mismatch

첫 번째 실패:

```text
template builder service creates, clones, validates, and sample-renders a custom full variant without publish
```

현재 actual:

```js
[
  '자막이 표시되는 영역입니다',
  '자막이 표시되는 영역입니다'
]
```

현재 expected:

```js
[
  '자막이 표시되는 영역이며,',
  '최대 두 줄까지 가능합니다'
]
```

관련 위치:

- `clipper_nestjs/test/template-builder-api.test.js`
  - sample render recipe subtitle item assertion 근처
- `clipper_nestjs/src/template-builder/fixtures/new-template-baseline.json`
  - 새 템플릿 baseline의 sample/default text 쪽 확인 필요
- `clipper_nestjs/src/template-builder/template-builder-sample-render.service.ts`
  - sample render text를 어디서 구성하는지 확인 필요

후속 작업 방향:

1. 현재 product behavior가 어느 쪽인지 먼저 결정한다.
   - 새 템플릿 sample subtitle이 같은 문장을 두 번 쓰는 것이 맞는지.
   - 아니면 테스트 expected처럼 두 줄 안내 문구가 맞는지.
2. product behavior가 맞다면 테스트 expected를 갱신한다.
3. 테스트 expected가 맞다면 sample render fixture/build logic을 고친다.

이 실패는 이번 S3 font default 변경 자체의 핵심 실패는 아니다. 다만 같은 테스트 파일을 전체 실행할 때 가장 먼저 보이는 failure다.

## 실패 유형 2: official DB repository missing

나머지 다수 실패는 다음 예외다.

```text
Template Builder official DB is not configured.
```

대표 failing tests:

- `template builder service updates role-scoped common styles across every ratio`
- `template builder service stages a layout image asset without mutating the family`
- `template builder service stores uploaded layout images with configured asset storage`
- `template builder service stores uploaded card thumbnails under the card-thumbnail S3 prefix`
- `template builder service uploads a logo image asset for a custom variant`
- read-only preset/system edit/clone/delete 관련 tests 다수

원인:

- `TemplateBuilderService`는 현재 `listFamilies()`/`getFamily()`에서 official repository를 필수로 사용한다.
- DB 필수 정책 도입 이후, service unit tests 중 상당수가 `TemplateBuilderService` 생성자에 `officialRepository` mock을 넘기지 않는다.
- 그래서 custom family test라도 내부에서 `getFamily()`를 타면 먼저 official repository 접근이 발생하고, mock이 없어서 `ServiceUnavailableException`이 난다.

관련 위치:

- `clipper_nestjs/src/template-builder/template-builder.service.ts`
  - `listFamilies()`
  - `getFamily()`
  - `officialTemplates()`
- `clipper_nestjs/test/template-builder-api.test.js`
  - `new TemplateBuilderService(...)` 호출 대부분
  - 파일 내 `inMemoryOfficialRepository(initial = [])` helper는 이미 있음

후속 작업 방향:

1. `test/template-builder-api.test.js`의 service factory/helper를 만든다.
   - 예: `createTemplateBuilderTestService({ root, officialFamilies, assetStorage, presetCatalog, overrides })`
   - 기본적으로 `officialRepository: inMemoryOfficialRepository([])`를 주입한다.
2. custom/local repository behavior를 보는 tests도 official mock을 빈 repository로 주입한다.
3. read-only/system preset tests는 현재 seed fallback이 사라진 정책과 맞춰야 한다.
   - 예전에는 `presetCatalogFixture()`로 system seed가 보였지만, 현재는 DB official이 필수다.
   - 따라서 해당 tests는 `systemFamiliesFromPresets(...)` 결과를 `inMemoryOfficialRepository([...])`에 넣거나, 테스트 목적에 맞는 official family fixture를 명시적으로 넣어야 한다.
4. `Template Builder official DB is not configured.` 자체를 검증하는 test는 유지한다.
   - 이 test만 official repository를 일부러 생략해야 한다.

## 이번 세션에서 확인된 S3 font default 검증

별도 smoke script로 새 custom family 생성 결과를 확인했다.

결과:

```text
mainTitle    -> https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/fonts/JalnanGothic.otf
subtitleText -> https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/fonts/Pretendard-SemiBold.otf
logoText     -> https://clipperstudio.s3.ap-northeast-2.amazonaws.com/templates/legacy-clipper1/fonts/Pretendard-Bold.otf
```

즉 이번 변경의 직접 목표인 “새 템플릿 기본 font가 filename이 아니라 S3 URL로 생성된다”는 확인했다.

## 후속 정비 기준

이 테스트 정비는 Windows installer build 자체의 blocker로 보지 않는다.

Windows packaging을 계속할 때는 우선 다음을 유지한다.

- `clipper_nestjs npm run build`: passed
- 새 custom family 생성 smoke: S3 font URL 확인됨
- `clipper_electron npm run build:app:mac:arm64`: passed after removing `adlight_python/fonts`

하지만 Template Builder API test suite를 다시 신뢰하려면, Windows work 이후 별도 세션에서 이 문서 기준으로 `test/template-builder-api.test.js`를 정비해야 한다.
