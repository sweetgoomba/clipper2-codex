# Template Builder Redesign Spec

작성일: 2026-05-10
상태: 브라우저 목업 승인 전 설계안

## 배경

현재 Template Builder는 기능은 충분하지만 화면 구조가 너무 압축되어 있다. 특히 다음 문제가 겹쳐 있다.

- 왼쪽 템플릿 목록이 단순 세로 리스트라서 탐색성이 낮다.
- 오른쪽 속성 영역이 너무 넓고, 선택 레이어 제목/비율/탭이 중복된다.
- `샘플 렌더 시작`과 `게시`가 레이어 선택 맥락에 묶여 있어서 찾기 어렵다.
- 템플릿 빌더 editor 컴포넌트가 너무 커서 역할 경계가 흐려진다.

이 스펙의 목표는 레이아웃을 다시 잡고, 화면을 섹션 단위로 분리하면서도 기존 데이터 모델과 preview/final contract는 유지하는 것이다.

## 목표

- 템플릿 목록을 카드 그리드로 바꾼다.
- 각 카드에 썸네일, 이름, 상태 배지를 보여준다.
- 오른쪽 속성 패널은 더 좁게 만들고, 불필요한 헤더와 탭 행을 제거한다.
- `샘플 렌더 시작` / `게시`는 선택 레이어와 분리된 고정 액션으로 노출한다.
- editor를 소규모 컴포넌트로 분해한다.
- 실제 UI 반영 전에 브라우저용 목업으로 새 구조를 먼저 확인할 수 있게 한다.

## 비목표

- preview/final 렌더 contract 자체를 바꾸지 않는다.
- 레이어 편집 기능을 줄이지 않는다.
- template family / variant 데이터 모델을 완전히 다시 설계하지 않는다.
- template export/import를 추가하지 않는다.

## 화면 구조

새 화면은 3열 워크스페이스로 정리한다.

### 1. 왼쪽: 템플릿 갤러리

- 기존 세로 목록 대신 카드 그리드로 표시한다.
- 기본 2열, 넓은 화면에서는 3열까지 허용한다.
- 카드에는 다음 정보를 넣는다.
  - 썸네일
  - 템플릿 이름
  - 배지

배지 규칙:

- `기본 제공`: `ownerType === 'system'`
- `사용자 템플릿`: `ownerType === 'user'`이면서 복제 계보가 없는 경우
- `복제본`: `ownerType === 'user'`이면서 복제 계보가 있는 경우

썸네일 규칙:

- system template는 legacy catalog의 `thumbnail_url`을 우선 사용한다.
- custom template는 성공한 sample render thumbnail을 우선 사용한다.
- 썸네일이 없으면 중립적인 placeholder를 보여준다.

### 2. 가운데: canvas / preview

- 현재와 같은 실제 편집 캔버스를 유지한다.
- layout image, content area, text/logo layers의 preview z-order는 그대로 유지한다.
- layout selection 상태에서는 layout image만 이동/확대축소 가능하게 유지한다.
- preview guide와 selection chrome은 편집 대상과 분리한다.

### 3. 오른쪽: inspector

- 현재보다 좁게 만든다.
- 선택 레이어의 이름을 다시 보여주지 않는다.
- ratio 표시도 제거한다.
- `위치 / 텍스트 / 색상 / 박스 / 효과` 탭 행도 제거한다.
- 대신 개별 섹션을 바로 세로로 노출한다.
- `샘플 렌더 시작` / `게시`는 inspector 상단 고정 액션으로 둔다.

## 컴포넌트 분해

기존 단일 editor 컴포넌트를 다음 단위로 쪼갠다.

- `TemplateBuilderPageComponent`
  - family 목록 로드
  - 선택 family 관리
  - modal / undo / redo / sample render 요청 라우팅
- `TemplateFamilyGalleryComponent`
  - 왼쪽 카드 그리드 렌더
  - family 선택 이벤트 emit
- `TemplateFamilyCardComponent`
  - 썸네일, 이름, 배지 표시
- `TemplateBuilderWorkspaceComponent`
  - 가운데 canvas와 오른쪽 inspector 배치
- `TemplateBuilderCanvasComponent`
  - preview, selection, drag, resize, layout lock 유지
- `TemplateBuilderInspectorComponent`
  - 속성 섹션과 고정 액션 렌더
- `TemplateBuilderPropertySectionComponent`
  - 텍스트/이미지/박스/효과 같은 반복 구조를 공통화

분리 원칙:

- gallery는 편집 로직을 모른다.
- canvas는 family selection과 property form layout을 모른다.
- inspector는 canvas pointer logic을 모른다.
- page는 각 하위 컴포넌트의 state coordination만 담당한다.

## 데이터 모델

카드 배지를 정확하게 표시하려면 family lineage가 필요하다.

현재 모델은 다음을 이미 가진다.

- `ownerType`
- `source`
- `sampleRender.thumbnailUri`

추가가 필요한 메타데이터:

- `originFamilyId?: string | null`
- 또는 `cloneSourceFamilyId?: string | null`

이 필드는 `복제본` 배지를 판단하는 용도로만 쓴다.

## 목업 전략

실제 UI를 바로 교체하기 전에, 브라우저에서 확인 가능한 목업을 먼저 만든다.

권장 방식:

- 실제 편집 페이지와 분리된 mockup shell을 만든다.
- mockup shell은 실제 데이터와 썸네일을 읽되, 저장/수정 버튼은 비활성화한다.
- 화면 구성과 공간 비중만 먼저 확인한다.

이 목업을 통해 다음을 먼저 검증한다.

- 카드 그리드가 2열/3열로 자연스럽게 보이는지
- inspector 폭이 충분히 줄었는지
- 고정 액션 위치가 자연스러운지
- 속성 섹션이 너무 길거나 답답하지 않은지

## 실행 순서

### Phase 0. 브라우저 목업

- 실제 데이터로 갤러리/워크스페이스/인스펙터의 비중만 먼저 보여준다.
- 기능은 최소화하고, 배치와 정보 구조만 확인한다.

### Phase 1. 컴포넌트 분리

- page / gallery / canvas / inspector / property section으로 분리한다.
- 현재 기능 동작은 유지한다.

### Phase 2. 갤러리 카드화

- left list를 card grid로 교체한다.
- thumbnail + name + badge를 붙인다.

### Phase 3. 인스펙터 정리

- 선택 레이어 제목, ratio 표시, tab row를 제거한다.
- 액션을 상단으로 올린다.
- 섹션을 직접 노출한다.

### Phase 4. 마무리 검증

- preview/final contract 회귀를 확인한다.
- read-only UX와 layout lock이 유지되는지 확인한다.
- legacy render와 sample render smoke를 다시 확인한다.

## 검증 기준

- 템플릿 목록은 스크롤 가능한 카드 그리드로 보여야 한다.
- system template는 `기본 제공` 배지를 가진다.
- clone lineage가 있는 custom template는 `복제본` 배지를 가진다.
- inspector 상단에 `샘플 렌더 시작` / `게시`가 보인다.
- `속성 · {layer}` 형태의 헤더는 보이지 않는다.
- `위치 / 텍스트 / 색상 / 박스 / 효과` 탭 행은 보이지 않는다.
- layout selection 상태는 preview에서 layout image만 조작 가능해야 한다.
- contentArea는 layout image와 text 사이에서 보이는 guide여야 한다.

## 참조 경로

- Angular page: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Angular editor: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Template Builder data model: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- NestJS template family data: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Legacy template thumbnails: `clipper_nestjs/src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`

## 남은 결정

- 브라우저 목업을 실제 Angular 임시 라우트로 만들지, 아니면 별도 static shell로 만들지
- `복제본` 배지를 위한 lineage 필드를 정확히 어느 층에서 저장할지
- inspector 상단 액션의 정확한 크기와 우선순위
