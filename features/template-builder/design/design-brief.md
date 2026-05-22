# Template Builder Design Brief

작성일: 2026-05-06
상태: brainstorming 확정 사항 및 다음 세션 인계용 brief

## 배경

Clipper2의 새 Clipper1 workflow는 기존 Clipper1을 그대로 붙이는 것이 아니라 Shared Shortform Core 위에서 다시 구현 중이다. 하지만 최종 숏츠 영상의 템플릿 적용 결과는 기존 Clipper1과 동일해야 한다.

기존 Clipper1의 템플릿은 `adlight_angular`/`adlight_python` `feature/d2x-electron` 기준으로 분석했고, 자세한 reference는 다음 문서가 기준이다.

- `.codex/features/template-builder/design/legacy-clipper1-template-system.md`

이 문서는 그 legacy 분석 이후 사용자가 새로 요구한 Clipper2 템플릿 생성기 방향을 정리한다.

## 핵심 원칙

- Clipper2의 Clipper1 출력물은 기존 Clipper1 템플릿이 적용된 숏츠 결과물과 시각적으로 호환되어야 한다.
- Python legacy 코드를 그대로 복사할 필요는 없지만, 1080x1920 좌표계, ratio별 content area, layout/title/logo/subtitle overlay semantics는 보존해야 한다.
- 템플릿 생성기는 플러그인이 아니다. `보관함`, `플러그인 대시보드`, `플러그인 스토어`와 같은 top-level 메뉴에 둔다.
- 생성된 템플릿은 Clipper1 plugin만이 아니라 Variation plugin과 향후 결과물이 숏츠 영상인 모든 workflow plugin에서 공통으로 사용한다.
- 현재 Clipper2는 DB 없이 파일시스템 중심으로 저장하지만, 이후 로그인/크레딧/서버 DB/사용자별 custom template이 들어올 수 있다. 따라서 저장소는 반드시 repository/adapter 경계로 추상화한다.
- 기본 제공 템플릿과 사용자 생성 custom template은 데이터 모델에서 분리한다.
- template export/import 기능은 범위에서 제외한다.

## Shared Template Catalog

Template Builder가 직접 편집하는 대상은 Shared Template Catalog다.

권장 추상화:

```text
Shorts workflow plugins
  -> TemplateCatalogService
    -> TemplateRepository interface
      -> LocalFileTemplateRepository today
      -> DbTemplateRepository later
      -> RemoteApiTemplateRepository later
```

데이터 소유권:

- `system` 또는 `built-in` template
  - 기본 제공 템플릿
  - 모든 유저가 조회 가능
  - 삭제 불가
  - 직접 수정 불가, 복제 후 custom draft로 편집
- `custom` template
  - 유저가 생성한 템플릿
  - 저장 위치는 아직 미정
  - local-only 또는 DB 저장으로 갈아끼울 수 있어야 함

## Template Family And Ratio Variants

템플릿은 family와 ratio variant로 나눈다.

```text
TemplateFamily
  id
  name
  ownerType: system | user
  variants:
    16:9?
    4:3?
    1:1?
    full?
```

확정 사항:

- 지원 ratio는 기존 Clipper1의 네 가지로 고정한다: `16:9`, `4:3`, `1:1`, `full`.
- 임의 ratio, 무제한 variant, 자유로운 custom ratio는 1차 범위가 아니다.
- 새 템플릿 생성 시 `full`만 먼저 만들도록 강제하지 않는다. 사용자가 최초 ratio를 선택한다.
- 같은 family 안에서 나중에 비어 있는 ratio를 추가할 수는 있다.
- UI에 `variant 추가` 버튼을 두지 않는다.
- UI에 `없는 비율 만들기` 같은 문구도 쓰지 않는다.
- 대신 네 개 ratio 슬롯을 고정으로 보여주고 각 슬롯의 상태를 표현한다.
  - 예: `게시됨`, `초안`, `편집 중`, `+ 생성`

## Editor Scope V1

1차 템플릿 생성기는 자유 레이어 편집기가 아니라 기존 Clipper1 renderer와 호환되는 고정 레이어 편집기다.

지원 레이어:

- layout image
- content area
- sub title
- main title line 1
- main title line 2
- bottom title
- logo image
- logo text
- dialogue subtitle
- subtitle box/bar

1차 범위에서 제외:

- 임의 텍스트 레이어 추가
- 임의 이미지 레이어 추가
- 자유 도형 레이어 추가
- timeline 기반 animation authoring
- arbitrary ratio authoring

## Coordinate And Preview Rules

- 저장 모델과 속성 패널은 실제 output 좌표계인 1080x1920 px 값을 사용한다.
- 캔버스에서는 drag/resize로 자연스럽게 조작할 수 있어야 한다.
- 좌표 입력과 캔버스 조작은 항상 같은 모델을 수정한다.
- preview scale은 uniform scale을 사용한다.
- legacy Angular preview의 `261x455` non-uniform scale은 계승하지 않는다.

## Required Layer Properties

각 텍스트 계층은 legacy settings에서 사용하던 스타일 값을 편집할 수 있어야 한다.

공통 텍스트 속성:

- font
- font size
- color
- tracking
- one-line/two-line y offsets
- left/right align margin

Box style:

- box color
- alpha
- padding left/right
- box height
- border color
- border width

Outline style:

- outline width
- outline color

Shadow style:

- shadow color
- shadow outline width
- shadow outline color
- shadow x offset
- shadow y offset

주의:

- 기존 legacy renderer에서는 shadow x/y offset이 schema에는 있었지만 일부 경로에서 실제 적용되지 않았다.
- Clipper2에서는 legacy output parity를 우선하되, 사용자가 편집기로 설정하는 값이 renderer에 반영되는지 명확히 검증해야 한다.

## Creation And Lifecycle

시작 방식:

- 빈 템플릿에서 시작
- 기존 기본 제공 템플릿 또는 사용자 템플릿을 복제해서 시작

상태:

- `draft`: 편집 중, 저장 가능, workflow plugin에 노출되지 않음
- `published`: Clipper1/Variation/future shorts plugin에서 선택 가능

게시 조건:

- schema validation 통과
- 필수 asset 존재
- numeric bounds 통과
- sample render job 성공

게시 전 테스트 렌더:

- 3-5초 짧은 sample mp4
- sample media/title/logo/2줄 subtitle/TTS/BGM 포함
- 정적 대표 프레임만으로 publish 검증하지 않음

## UI Direction

확정된 큰 구조:

- top-level `템플릿` 메뉴
- 템플릿 목록/검색/필터 화면
- system/custom 분리 표시
- 템플릿 family 상세
- ratio 슬롯 네 개 고정 표시
- editor 화면
- publish/test render 상태 표시

Editor 화면의 목표:

- 한국어 UI
- 캔버스에서 실제 9:16 숏츠 프레임을 보며 편집
- 우측 또는 별도 속성 패널에서 정확한 px 값과 스타일 값을 조정
- 레이어 선택 시 해당 레이어의 위치/폰트/색상/박스/윤곽선/그림자 설정이 모두 보여야 함
- 디자인팀/내부 운영자가 Zeplin과 spreadsheet로 픽셀을 재던 작업을 대체할 수 있어야 함

## Latest User Feedback To Carry Forward

마지막 사용자 피드백:

> 캔버스 영역이 너무 넓으니까 좀 줄이고 속성 영역을 더 넓게 해서 컬러 팔렛트도 추가한다거나 아무튼 정말 제대로 된 템플릿 생성기처럼 만들어달라고.

반영해야 할 다음 mockup 방향:

- editor v4에서는 캔버스 영역 비중을 줄인다.
- 속성 패널을 더 넓게 만든다.
- 속성 패널에서 텍스트 스타일, 박스, 윤곽선, 그림자, 위치 값을 한 화면에서 더 명확하게 다룬다.
- 컬러 팔레트를 추가한다.
  - 최소: 현재 선택 색상, 최근 사용 색상, 기본 swatch, 직접 hex 입력
  - 가능하면 템플릿 내 공통 색상 palette를 보여주고 재사용 가능하게 한다.
- ratio는 네 개 고정 슬롯으로 보여주고 `variant 추가`, `없는 비율 만들기` 문구는 사용하지 않는다.
- 레이어 속성이 부족해 보이면 안 된다. 특히 텍스트마다 서로 다른 그림자/윤곽선/박스 스타일을 가질 수 있음을 UI에 명확히 보여줘야 한다.
- mockup은 영어가 아니라 한국어로 작성한다.

## Editor Mockup V4 Direction

작성일: 2026-05-07
승인: 2026-05-07 사용자 승인

Visual companion mockup:

- `.superpowers/brainstorm/75878-1778126293/content/template-builder-editor-ko-v4.html`

v4에서 반영한 방향:

- 화면을 `왼쪽 설정/레이어`, `가운데 축소 캔버스`, `오른쪽 대형 속성 패널`의 3열로 구성한다.
- 가운데 캔버스는 이전 mockup보다 좁게 두고, 실제 1080x1920 output의 축소 preview와 drag/resize selection box만 담당하게 한다.
- 오른쪽 속성 패널은 가장 넓게 두고, 선택 레이어의 실측 px 속성과 스타일 속성을 한 화면에서 충분히 볼 수 있게 한다.
- `속성` 패널에는 `위치`, `텍스트`, `색상`, `박스`, `효과` 탭을 둔다.
- 색상 편집은 별도 `컬러 팔레트` 섹션으로 보강한다.
  - 현재 색상 preview
  - hex 값
  - opacity
  - 기본 swatch
  - 최근 사용 swatch
  - 향후 template common palette 재사용 가능성
- 텍스트 layer별로 서로 다른 스타일을 가질 수 있음을 명확히 노출한다.
  - 박스: color, alpha, padding, height, border color/width
  - 윤곽선: width, color, renderer 적용 확인 상태
  - 그림자: color, width, x/y offset, shadow outline color/width
- `비율 슬롯`은 네 개 fixed slot으로 표시한다.
  - `16:9`, `4:3`, `1:1`, `full`
  - 상태: `게시됨`, `초안`, `편집 중`, `+ 생성`
  - `variant 추가`, `없는 비율 만들기` 문구는 사용하지 않는다.
- 상단 메뉴에는 `템플릿`이 top-level 메뉴로 표시된다.
- 게시 전 상태는 `샘플 렌더 필요`로 표시하고, `샘플 렌더 시작` button이 publish gate와 연결된다는 점을 보여준다.

v4는 아직 구현 spec이 아니라 사용자 컨펌을 받기 위한 UI 방향 mockup이다. 컨펌 전에는 Angular/NestJS implementation으로 넘어가지 않는다.

사용자가 v4 방향을 승인했으므로, 구현 전 기준 spec은 다음 문서로 고정한다.

- `.codex/features/template-builder/design/approved-spec.md`

## Unresolved Topics

다음 세션에서 이어서 확정해야 할 항목:

- editor v4의 정확한 레이아웃
  - canvas width
  - properties panel width
  - layer list 위치
  - ratio 슬롯 위치
- 컬러 팔레트 범위
  - 최근 색상만 둘지
  - 템플릿 palette를 따로 둘지
  - 브랜드 palette나 system palette를 둘지
- font asset 관리
  - built-in font catalog
  - custom font upload 여부
  - renderer packaging 방식
- layout image/background asset 관리
  - system layout
  - custom layout upload
  - content area mask/guide 표시
- sample render job UX
  - 렌더 중 상태
  - 실패 원인 표시
  - publish gate 재시도
- local filesystem template repository schema
- 향후 DB/API repository로 전환할 때 migration boundary
- 로그인 도입 후 system/custom template 권한 모델

## Next Recommended Step

다음 세션의 첫 작업은 구현이 아니라 editor mockup v4 재설계다.

순서:

1. 이 문서와 legacy template 분석 문서를 읽는다.
2. 마지막 피드백을 반영해 한국어 editor mockup v4를 만든다.
3. 캔버스 영역은 줄이고 속성 영역은 넓힌다.
4. 컬러 팔레트와 텍스트별 박스/윤곽선/그림자 설정을 명확히 노출한다.
5. 사용자 컨펌을 받은 뒤에만 implementation plan으로 넘어간다.
