# 실제 앱으로 UI 목업 만들기

Clipper에서 “목업”, “화면 목업”, “UI 시안”을 요청받았을 때 적용하는 기본 방식이다. 검토 화면에 보이는 UI를 앱이 쓰는 프레임워크와 컴포넌트로 구현하고, 브라우저에서 실제로 렌더링한다. 메일 검토 캔버스 v12가 기준 사례다.

## 1. 화면은 앱 코드에서 만든다

- 작업 전 실제 화면과 소스를 확인한다. 기존 화면을 수정하거나 화면에서 모달을 여는 안이면 실제 페이지, 내비게이션, 사이드바, 헤더를 포함한다. 모달·드로어는 실제 화면 위에 앱의 공통 컴포넌트로 연 상태를 보여준다. 확인하지 않은 내비게이션이나 배경을 그려 넣지 않는다.
- 새 UI도 리뷰 전용 Angular 컴포넌트의 HTML/SCSS/TS로 구현한다. 기존 공통 페이지·카드·모달, Angular Material 폼·셀렉트·버튼, 전역 테마·디자인 토큰·폰트·아이콘을 실제로 가져다 쓴다. 폼 높이, 테두리, 버튼 정렬 등은 컴포넌트 기본값과 앱 스타일에서 결정되게 한다. 새 패턴에 필요한 CSS만 작성한다.
- 화면을 PNG/JPEG로 붙이거나 캡처한 DOM을 별도 HTML/SVG로 다시 그리지 않는다. 로고·본문 이미지 같은 콘텐츠 에셋은 화면 안에서 원본을 쓴다. 예를 들어 본문에 이미지와 글이 섞이면 실제 편집기에 배치한다.
- 화면 상태는 검토 전용 엔트리나 로컬 가드가 있는 라우트에서 fixture로 재현한다. 필요한 응답만 모의하고 나머지 API 요청은 차단한다. 실제 계정, 발송, 결제, 운영 데이터와 연결하지 않는다. 제품 반영이나 정책 결정은 별도다.

## 2. 캔버스는 렌더링된 화면만 움직인다

- 검토용 링크 하나의 전체 화면을 캔버스로 쓰고, 각 아트보드에 같은 출처의 라이브 프리뷰를 iframe으로 담는다. iframe에 원래 레이아웃에 맞는 고정 뷰포트를 주고, `transform: scale(...)`과 `transform-origin: top left`로 아트보드에 맞춘다. 모달을 포함한 화면도 같은 방법으로 넣는다.
- 캔버스 이동과 확대·축소는 보드 한 요소의 `transform: translate(...) scale(...)`으로 처리한다. 휠·드래그 중에는 프레임을 다시 로드하거나 개별 아트보드의 크기, iframe 뷰포트, 글자 크기를 바꾸지 않는다. `requestAnimationFrame`은 빠르게 들어오는 입력에서 가장 최근 위치·배율을 한 번 반영하는 용도다. 레이아웃 재계산을 요청하는 용도가 아니다.
- 상한은 캔버스 표시 기준 **600%**, 하한은 현재 뷰포트에서 **모든 아트보드가 보이는 배율**이다. `전체 보기`는 같은 배율에서 보드를 맞춘다. 브라우저 자체 확대에는 별도 제한을 두지 않는다.
- `CSS zoom`으로 iframe이나 앱 루트를 축소하지 않는다. v11에서 `zoom: 488 / 1487`을 적용하자 브라우저에서 입력창의 원래 `1px` 테두리가 `3.04713px`로 계산됐다. v12에서 같은 배율을 바깥 `transform: scale(...)`으로 바꾸고, iframe의 레이아웃 폭과 앱 CSS는 유지했다. 입력창과 본문 편집기의 기본 테두리가 모두 `1px`로 돌아왔다.

## 3. 현재 구현 위치 — 메일 목업 v12

[배포된 검토 캔버스](https://clipper-mail-design-review.cloudytetra33.chatgpt.site/?v=12#compose). 아래 앱 경로는 `adlight` 기준이다. 캔버스 체크아웃은 앱 저장소와 별개다.

| 역할 | 현재 파일 |
| --- | --- |
| 관리자 메일 작성·설정 등 검토 UI | `web/clipper_web_admin/src/app/features/samples/mail-review/mail-review.component.{ts,html,scss}`. 작성 화면은 `mat-form-field`, `matInput`, `matSelect`, `matButton`, 공통 모달을 쓰고, 본문은 이미지와 텍스트가 들어가는 하나의 편집 영역이다. |
| 관리자 기존 화면과 나머지 상태 | 같은 폴더의 `mail-review-overview.component.{ts,html}`. 앱 소식과 회원 상세 등 기존 컴포넌트를 재사용한다. 관리자 `src/app/app.routes.ts`의 `__mockups/mail`은 로컬·mock 구성에서만 열린다. |
| 관리자 실제 테마·레이아웃 | `web/clipper_web_admin/src/styles.scss`, `src/styles/_theme.scss`, `src/styles/_tokens.scss`, `src/app/shared/layout/{app-shell,sidebar,nav-items.ts}`, `src/app/shared/ui/{page,card}`, `src/app/components/modal`. 편집기 자체 테두리는 리뷰 SCSS의 `1px solid var(--outline-input)`이다. |
| 고객 검토 UI와 실제 레이아웃 | `web/clipper_web_client/src/app/features/samples/mail-review/mail-review.component.{ts,html,scss}`. 기존 계정·가입 동의 화면을 활용한다. 앱의 `src/styles.scss`, `src/app/app.component.*`, `src/app/shared/layout/{app-header,app-footer}`, `src/app/features/portal/portal-layout`을 따른다. |
| 프리뷰 엔트리와 데이터 격리 | 양쪽 Angular 저장소의 `src/mail-review-main.ts`, `src/mail-review-index.html`, `tsconfig.mail-review.json`. 실제 앱 레이아웃과 별도 해시 라우트 및 mock 공급자를 연결한다. |
| 캔버스 15장 배치와 연결 | 캔버스 저장소 `dist/index.html`. `/mockups/live-admin/index.html#/mail?screen=compose` 같은 리뷰 URL을 고정 크기의 iframe에 연결한다. |
| 캔버스 CSS와 조작 | `dist/review.css`는 캔버스 UI와 iframe 배율, `dist/canvas.js`는 이동·배율·전체 보기만 담당한다. v12의 iframe은 1487×1058, 카드의 내부 너비는 488px이므로 `scale(calc(488 / 1487))`을 쓴다. 이 수치는 메일 캔버스의 사례다. |
| 컴파일 결과와 호스팅 | `dist/mockups/live-admin/`, `dist/mockups/live-client/`의 JS/CSS/HTML은 빌드 결과다. `dist/mockups/{admin-icons.css,client-fonts.css,fonts/}`와 `dist/assets/brand/`는 프리뷰에 쓰이는 에셋이다. `.openai/hosting.json`이 `dist`를 Sites에 연결한다. |

캔버스 체크아웃: `/Users/jina/.codex/visualizations/2026/11/06/01a1ae65-bc06-74e2-9be2-367679e4f818/clipper-mail-review`. 배포 v12의 Sites 소스 커밋은 `c84c86bf6bef8ddaba88e7aec169bce77209115a`다. 이 경로는 해당 작업의 체크아웃이며 후속 작업의 필수 경로는 아니다. 앱 소스 수정은 위 Angular 파일에서 하고, 빌드 산출물의 CSS/JS를 직접 편집하지 않는다.

## 4. 이 사례 다시 빌드하기

각 앱 저장소에서 `.nvmrc`에 맞는 Node와 설치된 프로젝트 의존성을 사용한다.

```bash
# web/clipper_web_admin
node ./node_modules/@angular/cli/bin/ng.js build --configuration mock \
  --ts-config tsconfig.mail-review.json --browser src/mail-review-main.ts \
  --index src/mail-review-index.html --base-href /mockups/live-admin/ \
  --output-path /private/tmp/clipper-live-mail --source-map=false --optimization=true

# web/clipper_web_client
node ./node_modules/@angular/cli/bin/ng.js build --configuration local \
  --ts-config tsconfig.mail-review.json --browser src/mail-review-main.ts \
  --index src/mail-review-index.html --base-href /mockups/live-client/ \
  --output-path /private/tmp/clipper-live-client --source-map=false --optimization=true
```

각 빌드의 `browser/` 정적 파일을 캔버스의 해당 `dist/mockups/live-*/`에 넣고, 생성된 `mail-review-index.html`을 그 디렉터리의 `index.html`로 둔다. 에셋의 상대 경로와 iframe URL을 맞춘 뒤 `dist/`를 로컬 HTTP로 띄워 확인한다. 게시가 요청된 작업이면 검토한 `dist/`를 같은 Sites 프로젝트에 반영한다.

## 5. 전달 전 브라우저 확인

- 실제 앱과 목업을 같은 뷰포트 및 UI 상태로 비교한다. 폰트, 버튼 정렬, 입력창 높이와 테두리, 드롭다운, 모달 배경을 본다. 페이지 URL을 단독으로 열었을 때와 캔버스 iframe 안에서의 `getComputedStyle`도 비교한다. 예를 들어 Material 폼은 평상시 outline 부분, 본문 편집기는 실제 컨테이너의 `borderWidth`를 읽는다.
- 모든 아트보드가 비어 있지 않은지, 폰트·아이콘·이미지가 로드되는지 확인한다. 확대 상태에서 텍스트와 입력 UI를 보고, 전체 보기 하한과 600% 상한, 휠과 드래그를 확인한다. 지연이 있으면 실제 입력 중 프레임 시간과 레이아웃 작업을 측정한다.
- 게시한 경우에는 로컬 결과와 함께 사용자에게 줄 링크에서도 확인한다. 문제가 있으면 앱 스타일인지 캔버스의 변환인지 분리해 진단한다.
