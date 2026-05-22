# Template Builder System Template Admin Edit

작성일: 2026-05-12
상태: 구현 및 검증 완료

## 배경

Template Builder의 기존 21개 Legacy Clipper1 템플릿은 NestJS에서 preset catalog를 읽어 `system` / `built_in` / `readonly: true` family로 생성한다. 현재 Angular와 NestJS 모두 `readonly`를 수정 불가의 직접 조건으로 사용한다.

사용자는 기존 21개 템플릿의 좌표, 크기, 폰트, 박스, 자막 위치 등 기본값을 UI에서 직접 보정하고 싶다. 또한 향후 로그인 시스템이 붙으면 관리자 권한 사용자가 기존 템플릿을 수정할 수 있어야 한다. 이번 작업은 로그인 시스템을 만들지 않는다.

## 목표

- 개발용 관리자 모드에서 system template을 Template Builder UI로 수정할 수 있게 한다.
- 일반 모드에서는 system template이 계속 readonly처럼 동작한다.
- 수정 결과는 일반 사용자 템플릿 저장소와 섞지 않고 system template override로 저장한다.
- 나중에 로그인 기반 관리자 권한으로 교체할 수 있게 `readonly` 대신 capability/policy 경계를 만든다.

## 비목표

- 로그인, 사용자 계정, 세션, 권한 DB를 구현하지 않는다.
- system template 삭제/이름 변경을 허용하지 않는다.
- system template asset 업로드를 1차 범위에 넣지 않는다.
- 기존 21개 기본값을 즉시 seed/preset 코드에 반영하지 않는다. UI로 보정한 뒤, 필요한 값은 별도 후속 작업에서 seed 기본값으로 승격한다.

## 설계 결정

### 권한 모델

`readonly`는 family의 출처/성격을 나타내는 값으로 유지한다. 실제 편집 가능 여부는 backend가 계산한 capability로 전달한다.

```text
TemplateBuilderFamily.capabilities.canEdit
TemplateBuilderFamily.capabilities.canRename
TemplateBuilderFamily.capabilities.canDelete
TemplateBuilderFamily.capabilities.canClone
```

현재 actor는 로그인 사용자가 아니라 env flag에서 온다.

```text
TEMPLATE_BUILDER_SYSTEM_TEMPLATE_EDIT=1
```

이 값이 켜져 있고 family가 system template이면 `canEdit=true`가 된다. 나중에 로그인 시스템이 생기면 env flag 판단 부분만 `actor.roles.includes('admin')` 같은 실제 권한 판단으로 교체한다.

### System Template Override 저장

system template은 preset에서 매번 생성되므로 기존 `JsonTemplateBuilderRepository`에 같은 id로 저장하면 안 된다. `getFamily()`가 system seed를 먼저 반환하기 때문에 일반 repo 저장값이 무시될 수 있고, user template과 system template의 생명주기도 섞인다.

별도 JSON 파일을 둔다.

```text
CLIPPER_DATA_DIR/templates/template-builder-system-overrides.json
```

1차 구현은 family 전체 snapshot을 저장한다. 저장 파일은 다음 형태다.

```json
{
  "version": 1,
  "families": []
}
```

목록/조회 시에는 `preset system family` 위에 override family를 덮어쓴다. override는 표시와 렌더에 항상 적용하지만, 수정 API는 capability가 있을 때만 허용한다.

### 수정 범위

관리자 모드에서 허용하는 system template 수정:

- variant layer patch
- role common style patch

허용하지 않는 system template 수정:

- rename
- delete
- variant create
- publish
- sample render
- layout/logo/font asset upload

이 제한은 현재 21개 기본값 보정 목적에 맞춘다. 향후 운영 관리자 기능에서 필요하면 별도 권한으로 확장한다.

### Angular 변경

Angular는 `family.readonly`를 편집 가능 여부로 직접 보지 않고 helper를 둔다.

```text
isFamilyEditable(family) = family.capabilities?.canEdit ?? !family.readonly
```

editor에 전달되는 `family.readonly` 자체는 유지한다. 대신 editor의 `isReadonly()`가 capability를 우선한다. 그래서 system template은 "기본 제공"으로 표시되면서도 개발용 관리자 모드에서는 캔버스/인스펙터 편집이 가능해진다.

rename/delete 버튼은 capability의 `canRename`, `canDelete`만 따른다. system template은 관리자 모드에서도 rename/delete가 보이지 않는다.

## 데이터 흐름

```text
Angular listFamilies()
  -> NestJS TemplateBuilderService.listFamilies()
    -> systemFamiliesFromPresets()
    -> SystemOverrideRepository.list()
    -> merge override onto matching system families
    -> attach capabilities
```

```text
Angular updateVariant(system family)
  -> NestJS updateVariant()
    -> require canEdit
    -> patch system family snapshot
    -> SystemOverrideRepository.upsert()
    -> return family with capabilities
```

## 검증 기준

- env flag off:
  - system template `capabilities.canEdit=false`
  - system template updateVariant/updateRoleCommonStyle는 기존처럼 실패
  - Angular editor는 기존처럼 readonly
- env flag on:
  - system template `capabilities.canEdit=true`
  - system template updateVariant/updateRoleCommonStyle가 override JSON에 저장됨
  - list/get이 override 값을 반영함
  - rename/delete는 여전히 불가
- user template:
  - 기존 create/update/delete 흐름이 유지됨

## 후속 작업

UI로 보정한 결과를 "앱 기본값"으로 고정하려면 override JSON과 seed/preset 생성 결과를 비교해 필요한 값을 `template-builder-seed.ts` 또는 원본 preset data로 승격하는 별도 작업을 진행한다.

## 구현 결과

- NestJS가 `TEMPLATE_BUILDER_SYSTEM_TEMPLATE_EDIT=1`일 때 system template의 `capabilities.canEdit=true`를 내려준다.
- System template variant/common style 수정은 `CLIPPER_DATA_DIR/templates/template-builder-system-overrides.json`에 저장된다.
- Rename/delete/variant create/sample render/publish/asset upload은 system template에서 계속 차단된다.
- Angular는 editor 편집 가능 여부와 출력/자산/비율 생성 액션 가능 여부를 분리해 처리한다.
