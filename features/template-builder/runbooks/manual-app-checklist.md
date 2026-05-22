# Template Builder 수동 앱 확인 체크리스트 (2026-05-10)

목적: Template Builder preview/final local guard에 visibility fixture와 style-heavy fixture coverage를 추가한 뒤, 패키징된 Electron 앱을 사람이 직접 실행해서 확인한다.

이 체크리스트는 사람이 앱을 직접 보면서 확인하는 절차다.

아래 자동 local guard는 개발자가 Template Builder preview/final 렌더링 관련 코드를 바꾼 뒤 실행하는 별도 검증 도구다. 일반 앱 사용 중에 실행되는 기능이 아니고, 이번 수동 확인을 위해 사용자가 반드시 직접 실행해야 하는 명령도 아니다.

```bash
cd clipper_python
uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard
```

## 현재 빌드

- 앱: `/Users/jina/project/adlight/clipper_electron/dist-app/mac-arm64/Clipper2.app`
- DMG: `/Users/jina/project/adlight/clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`
- 사용한 빌드 명령: `source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`
- 이 local build는 code signing이 되어 있지 않다. 그래서 macOS에서 미서명 앱 경고가 나올 수 있다.

이 빌드에 포함된 최신 Template Builder fixture commit:

- `clipper_nestjs` `f4eca90 feat: add style heavy template fixture`
- `clipper_angular` `a7f047f feat: add style heavy preview fixture`
- `clipper_python` `a3a6c3b feat: add style heavy guard fixture`
- `clipper_angular` `5ed7cbe fix: constrain template builder panel scrolling`
- `clipper_angular` `ebcaedd fix: gate template builder readonly actions`
- `clipper_nestjs` `5cf529b fix: reject readonly template builder mutations`
- `clipper_angular` `6c0b1df fix: clone current template builder ratio`
- `clipper_nestjs` `48091dd fix: preserve template builder clone visuals`
- `clipper_angular` `3f2a216 fix: show selected clone ratio`
- `clipper_angular` `80ddba7 fix: default template builder selection to 16x9`
- `clipper_nestjs` `8a75081 fix: seed legacy template builder styles`
- `clipper_angular` `6a9e889 fix: improve template builder editing controls`
- `clipper_nestjs` `56e6d38 fix: clone template builder families`
- `clipper_angular` `2aefebe fix: refine template builder subtitle layers`
- `clipper_nestjs` `32ebdd2 fix: honor template builder unused layers`
- `clipper_python` `553d490 fix: render template builder subtitle boxes`

최신 subtitle/background/usage 수정 이후 rebuild:

- `clipper_angular npm run build`: passed.
- `clipper_angular npx ng test --watch=false --browsers=ChromeHeadless '--include=src/features/template-builder/**/*.spec.ts'`: 93 specs passed.
- `clipper_nestjs npm run build`: passed.
- `clipper_nestjs node --test` for Template Builder validation/api/render-payload/render-contract/sample-render/text-artifact: 34 tests passed.
- `clipper_python uv run pytest` for subtitle artifacts/media looping/text preview/export/template styles/guard runner: 52 tests passed.
- `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.
- Latest app: `/Users/jina/project/adlight/clipper_electron/dist-app/mac-arm64/Clipper2.app`
- Latest DMG: `/Users/jina/project/adlight/clipper_electron/dist-app/Clipper2-0.0.1-arm64.dmg`

최신 Template Builder editor usability 수정 이후 rebuild 대상:

- 기본 제공 템플릿 복제는 더 이상 선택한 ratio 하나만 복제하지 않는다. 원본 family의 모든 ratio variant를 새 사용자 템플릿 family로 복제한다.
- clone form에서 `복제할 비율` select를 제거했다.
- clone 후 editor는 복제된 family의 기본 ratio인 `16:9`로 열린다. `16:9`가 없는 custom full-only family는 기존 fallback으로 사용 가능한 ratio를 연다.
- title/subtitle/logo text box는 glyph가 잘리지 않도록 legacy seed 높이를 font size/line-height/effect padding 기준으로 보강한다.
- subtitle line 위치는 기존 Clipper1 구조 그대로 `oneLineY`, `twoLineFirstY`, `twoLineSecondY`를 사용한다.
  - canvas preview에서 각 subtitle line을 직접 드래그할 수 있다.
  - 속성 패널에서도 `한 줄 Y`, `두 줄 첫째 Y`, `두 줄 둘째 Y`를 직접 수정할 수 있다.
- `렌더 폰트명`은 편집 UI에서 숨겼다. 내부 render contract compatibility 필드로는 남아 있을 수 있다.
- preview zoom은 기본 30%이며, 이는 1080px output width의 30%인 324px canvas width를 의미한다.
  - stage toolbar의 `줌` 입력이나 canvas 영역 wheel로 10-80% 범위에서 조절한다.
- `간격` 라벨은 `스냅 간격`으로 바꿨다. 의미는 snap grid의 final-render px 간격이다.
- text effect UI는 `없음 / 박스 / 윤곽선 / 그림자` 중 하나만 선택하게 바꿨다.
  - 윤곽선 mode를 처음 선택할 때 width가 0이면 기본 8로 켠다.
- `자막 박스`는 편집 UI에서 보이지 않는다. 고정 레이어에는 `자막 첫번째줄`, `자막 두번째줄`이 보인다.
- 자막 두 줄은 위치를 따로 조정하지만 폰트/크기/색상/자간/행간/효과는 `subtitleText` 스타일을 공유한다.
- `표시` 용어는 `사용`으로 바꿨다. 기본 제공 템플릿에서는 사용 체크가 직접 토글되지 않아야 한다.
- 레이아웃 배경은 이미지 또는 단색 배경 중 하나를 선택할 수 있다.

최신 clone family / subtitle line / effect mode 수정 이후 rebuild smoke:

- `clipper_angular npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`: 47 specs passed.
- `clipper_angular npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts`: 25 specs passed.
- `clipper_angular npm run build`: passed.
- `clipper_nestjs npm run build`: passed.
- `clipper_nestjs node --test test/template-builder-api.test.js`: 14 tests passed.
- `clipper_angular git diff --check`: passed.
- `clipper_nestjs git diff --check`: passed.
- `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.
- Packaged smoke:
  - `GET /v1/health`: HTTP 200.
  - template 17 clone request: HTTP 201.
  - source ratios와 clone ratios가 모두 `16:9`, `1:1`, `4:3`, `full`이었다.
  - clone `16:9` sanity values: `mainTitleLine1.y=321`, `subtitleText.twoLineFirstY=1255`, `mainTitleLine1.outline.width=8`.
  - smoke 이후 별도 packaged app/NestJS 인스턴스를 종료했다.

수동 앱 확인 전에 통과한 최신 자동 guard:

- 명령: `clipper_python uv run python scripts/run_template_builder_preview_final_guard.py --output-root /tmp/template-builder-preview-final-guard-style-heavy-full-20260510`
- 결과: passed `true`
- fixture set:
  - `default-image-logo`
  - `long-korean-text`
  - `hidden-logo`
  - `subtitle-hidden`
  - `logo-text-only`
  - `style-heavy`

최신 rebuild 이후 packaged bridge smoke:

- `GET /v1/health`: HTTP 200.
- `GET /v1/template-builder/families`: HTTP 200.
- warmup 전 `GET /v1/plugins/clipper1_video_render/status`: HTTP 200, `runtimeState=stopped`.
- `POST /v1/template-builder/preview/renderer-session`: HTTP 201, `status=ready`, renderer `baseUrl=http://127.0.0.1:50304`, `time_total=0.259108`.
- smoke 이후 packaged app, NestJS, Python renderer worker가 정상 종료됐다.

최신 panel scrolling 수정 이후 rebuild smoke:

- `GET /v1/health`: HTTP 200, `time_total=0.001022`.
- `GET /v1/template-builder/families`: HTTP 200, `time_total=0.005769`.
- smoke 이후 packaged app과 NestJS가 정상 종료됐다.

최신 read-only action guard 수정 이후 rebuild smoke:

- `GET /v1/health`: HTTP 200, `time_total=0.005476`.
- `GET /v1/template-builder/families`: HTTP 200, `time_total=0.005544`; 기본 제공 system family는 `readonly=true`.
- 기본 제공 템플릿에 대한 직접 샘플 렌더 요청: HTTP 400, `기본 제공 템플릿은 복제 후 샘플 렌더할 수 있습니다.`
- 기본 제공 템플릿에 대한 직접 게시 요청: HTTP 400, `기본 제공 템플릿은 복제 후 게시할 수 있습니다.`
- 기본 제공 템플릿에 대한 직접 레이아웃 이미지 업로드 요청: HTTP 400, `기본 제공 템플릿은 복제 후 수정할 수 있습니다.`
- smoke 이후 packaged app과 NestJS가 정상 종료됐다.

최신 clone visual preservation 수정 이후 rebuild smoke:

- `GET /v1/health`: HTTP 200.
- 기본 제공 template 17의 16:9 clone 요청: HTTP 201.
- source와 clone의 주요 visual 값이 일치했다:
  - `contentArea.y=595`
  - `layers.contentArea.y=595`
  - `layoutImage.assetUri=https://d2x-s3.s3.ap-northeast-2.amazonaws.com/layout/17.png`
  - `mainTitleLine1.y=364`
  - `subtitleText.oneLineY=1291`
- smoke 이후 별도 packaged app/NestJS 인스턴스를 종료했다.

최신 clone ratio select 표시 수정 이후 rebuild:

- 1:1 ratio를 보고 clone form을 열 때 DOM select 표시값과 실제 clone state가 모두 1:1로 일치하도록 수정했다.
- `clipper_angular npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts`: 25 specs passed.
- `clipper_angular npm run build`: passed.
- `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.

최신 default ratio / legacy style seed 수정 이후 rebuild:

- 템플릿 family 선택 시 `16:9` variant가 있으면 editor 기본 ratio가 `16:9`로 열린다.
- 새 템플릿/복제 폼의 기본 ratio도 `16:9` 중심으로 맞췄다. 단, 선택 가능한 ratio가 `full`뿐이면 `full`을 사용한다.
- 기본 제공 legacy template의 title/subtitle/logo text style을 legacy catalog `rawSettings`에서 seed한다.
- `sub_title_box_color=null`, `main_title_box_color=null` 같은 legacy null box는 disabled/transparent box로 seed한다.
- 어두운 subtitle text가 있는 template 3 16:9는 subtitle box가 `#ffffff`로 seed되는 것을 자동 테스트로 고정했다.
- `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/components/template-builder-editor.component.spec.ts`: 42 specs passed.
- `clipper_angular npm run test -- --watch=false --browsers=ChromeHeadless --include src/features/template-builder/pages/template-builder-page.component.spec.ts`: 25 specs passed.
- `clipper_angular npm run build`: passed.
- `clipper_nestjs npm run build`: passed.
- `clipper_nestjs node --test test/template-builder-api.test.js --test-name-pattern "legacy Clipper1 text styles"`: passed; Node runner executed all 13 tests in the file.
- `clipper_electron source ~/.zshrc && nvm use 22 && npm run build:app:mac:arm64`: passed.

## 수동 확인 항목

1. `dist-app/mac-arm64/Clipper2.app`을 실행한다.
2. Template Builder를 연다.
3. `Shared Template Catalog` 페이지 전체가 세로로 스크롤되지 않는지 확인한다.
4. 1번 영역인 template family 목록이 자기 영역 안에서만 세로 스크롤되는지 확인한다.
5. 2번 영역인 비율 슬롯/고정 레이어 목록이 자기 영역 안에서만 세로 스크롤되는지 확인한다.
6. 3번 영역인 canvas preview 영역에는 세로 스크롤이 생기지 않는지 확인한다.
7. 4번 영역인 속성 패널이 자기 영역 안에서만 세로 스크롤되는지 확인한다.
8. template family와 variant 목록이 정상 로드되는지 확인한다.
9. 기본 제공 템플릿을 선택한다.
   - `16:9`가 있는 템플릿은 기본으로 `16:9`가 선택되어야 한다.
   - title/subtitle/logo text의 font, size, color, tracking이 legacy template별로 다르게 보이는지 확인한다. 모든 텍스트가 같은 Pretendard/40px/검정처럼 보이면 안 된다.
   - legacy 설정에서 box color가 `null`인 title/subtitle box는 화면에서 투명하게 보여야 한다.
   - 고정 레이어 행을 눌러도 선택 표시가 생기지 않아야 하고, preview에 파란 선택 박스가 보이면 안 된다.
   - ratio 슬롯에는 `게시됨` 또는 `편집 중` 상태 문구가 보이지 않아야 한다.
   - `테스트 렌더`, `게시`, `레이아웃 이미지`, `로고 이미지`, `폰트 선택` 같은 수정성 컨트롤이 직접 실행되지 않아야 한다.
   - 속성 패널 수치 입력, 텍스트 효과 선택, 폰트/이미지 선택은 수정할 수 없어야 한다.
   - 수정이 필요하면 사용자 템플릿으로 복제한 뒤 진행한다.
10. 기본 제공 템플릿을 복제한다.
   - clone form에는 `복제할 비율` select가 없어야 한다.
   - 복제는 16:9, 1:1, 4:3, full 전체 ratio를 한 family로 복제해야 한다.
   - 복제 직후 기본으로 16:9가 선택되어야 한다.
   - 복제된 family에서 ratio를 바꿔가며 배경 이미지, 콘텐츠 영역 위치, 타이틀/자막 위치가 원본과 같은 구조로 보이는지 확인한다.
   - 타이틀/자막이 콘텐츠 영역 안으로 한꺼번에 모여 있거나 검은 배경만 보이면 안 된다.
11. 기본 제공 템플릿의 title/subtitle/logo text 선택 박스를 확인한다.
   - 텍스트 일부가 선택 박스 높이 때문에 잘려 보이면 안 된다.
   - 특히 큰 title font와 outline/shadow가 있는 경우를 확인한다.
12. subtitle text를 선택한다.
   - 고정 레이어 목록에 `자막 첫번째줄`, `자막 두번째줄`이 보이고 `자막 박스`는 보이지 않아야 한다.
   - preview 안에서 subtitle 첫째 줄과 둘째 줄이 각각 따로 선택되고, 각각 드래그할 수 있어야 한다.
   - 속성 패널의 `한 줄 Y`, `두 줄 첫째 Y`, `두 줄 둘째 Y` 값을 수정하면 해당 subtitle y-offset만 바뀌어야 한다.
13. title text의 한 줄/두 줄 위치를 확인한다.
   - `타이틀 첫번째줄`에는 `한 줄 Y`, `두 줄 첫째 Y`가 보여야 한다.
   - `타이틀 두번째줄`에는 `두 줄 둘째 Y`가 보여야 한다.
   - 타이틀 두 번째 줄을 사용하지 않는 경우 첫 번째 줄은 `한 줄 Y` 위치를 사용해야 한다.
   - 타이틀 두 줄을 모두 사용하는 경우 첫 번째 줄과 두 번째 줄은 각각 `두 줄 첫째 Y`, `두 줄 둘째 Y` 위치를 사용해야 한다.
14. 텍스트 속성 패널을 확인한다.
   - `렌더 폰트명` 입력은 보이지 않아야 한다.
   - `스냅 간격` 라벨이 보여야 한다.
   - `줌` 값을 바꾸거나 canvas 영역에서 wheel을 사용하면 preview 크기가 변해야 한다.
   - `텍스트 효과`는 `없음 / 박스 / 윤곽선 / 그림자` 중 하나만 선택되어야 하고, 선택한 mode의 세부 속성만 보여야 한다.
   - 윤곽선을 처음 켰을 때 두께 기본값은 8이어야 한다.
15. 16:9 Template Builder variant를 열거나 새로 만든다.
16. main title 텍스트를 한 글자 수정한다.
   - preview는 browser/CSS fallback으로 즉시 바뀌어야 한다.
   - renderer가 만든 text image가 잠시 뒤 교체되어도 이전 텍스트가 stale 상태로 다시 나타나면 안 된다.
17. main title, subtitle, logo layer를 움직여 본다.
   - preview가 즉시 반응해야 한다.
   - selection handle이나 editor-only overlay가 sample/final output에 들어가면 안 된다.
18. image logo를 끄고 text logo를 켠다.
   - preview에는 text logo만 보여야 한다.
   - sample/final render에는 이전 image logo가 남아 있으면 안 된다.
19. subtitle 사용을 끈다.
   - preview에서 subtitle line과 subtitle box 효과가 사라져야 한다.
   - sample/final render에도 subtitle overlay가 없어야 한다.
20. 배경 방식을 바꾼다.
   - `레이아웃 이미지` 모드에서는 선택한 이미지가 배경으로 보여야 한다.
   - `단색 배경` 모드에서는 선택한 색상이 preview와 final render 배경으로 쓰여야 한다.
21. 강한 text style을 적용한다.
   - text color, box fill, border, outline, shadow, letter spacing을 확인한다.
   - main title, subtitle title, bottom title, text logo를 같이 확인한다.
22. 같은 edited variant로 sample/final render를 생성한다.
23. editor preview와 생성된 video frame을 눈으로 비교한다.
   - layout, visibility, text content, logo mode, 주요 style 선택이 맞아야 한다.
   - 작은 MP4 encoding/scale edge 차이는 허용한다.
24. 앱을 종료한 뒤 다시 연다.
   - 다시 열었을 때 edited Template Builder 상태가 이상 없이 유지되는지 확인한다.

## 참고

- Python worker가 cold 상태라면 첫 renderer warmup은 몇 초 걸릴 수 있다.
- warmup 이후 text/subtitle artifact refresh는 편집 흐름을 방해하지 않을 정도로 짧아야 한다.
- 이 수동 확인은 product UX와 눈에 띄는 visual correctness를 보기 위한 것이다. 픽셀 수준 preview/final regression coverage는 local guard runner가 담당한다.
