# Template Builder Official Template Registry Design

작성일: 2026-05-13

## 목표

Template Builder의 템플릿 저장 모델을 로컬 파일 기반 임시 구조에서 공식 템플릿/개인 템플릿이 분리된 구조로 전환한다. 최종 제품에서는 공식 템플릿이 모든 유저에게 공유되어야 하므로 중앙 Template API가 맞다. 다만 현재 개발 단계에서는 Clipper2 local NestJS가 Postgres DB와 S3에 직접 접근하는 방식으로 먼저 구현한다.

구현은 사용자가 기존 21개 템플릿 보정을 완료하고 “설계 들어가라”고 지시한 뒤 시작한다. 이 문서는 그 전까지의 합의된 설계 기준이다.

## 현재 문제

- Template Builder 템플릿 데이터는 현재 local JSON/filesystem에 저장된다.
- 기존 21개 템플릿은 앱에 번들된 legacy preset seed에서 생성된다.
- 복제본, 새 템플릿, system override는 각 PC 로컬에만 저장되므로 다른 유저에게 공유되지 않는다.
- system template card thumbnail은 디자인팀 제공 bundled thumb를 사용하지만, 복제/수정 시 `sampleRender`가 초기화되면서 card thumbnail이 layout image fallback으로 바뀐다.
- `sampleRender.thumbnailUri`가 “카드 대표 썸네일”과 “샘플 렌더 결과 썸네일” 역할을 동시에 맡고 있어 의미가 섞여 있다.
- 편집 모드가 명시적이지 않아 변경사항이 즉시 저장되고, undo stack도 페이지 전체 전역이라 다른 템플릿 변경 이력까지 되돌릴 수 있다.
- `게시`는 샘플 렌더 성공과 엮여 있는데, 제품 관점에서는 샘플 렌더와 공식 템플릿 등록은 별개의 기능이어야 한다.

## 제품 정책

- `게시` 버튼과 게시 개념은 제거한다.
- `샘플 렌더 시작`은 계속 유지하되, 단순히 현재 템플릿 설정으로 샘플 영상을 생성해보는 기능이다.
- 샘플 렌더 성공 여부는 공식 등록 가능 여부와 연결하지 않는다.
- 공식 템플릿은 모든 유저가 템플릿 선택 리스트에서 볼 수 있는 공유 템플릿이다.
- 기존 21개 기본 템플릿도 공식 템플릿이다.
- 개인 템플릿은 관리자 권한이 없는 유저가 만들거나 복제한 템플릿이며, 해당 PC의 로컬 앱에서만 보이고 사용된다.
- 로그인/권한 시스템이 붙기 전까지는 현재 `임시 관리자 모드`가 관리자 권한을 대신한다.
- 관리자 모드에서만 `템플릿 등록` 버튼을 보여준다.
- `템플릿 등록`은 현재 편집 중인 템플릿을 공식 템플릿으로 DB/S3에 저장한다.
- 최종적으로 Clipper2에서 생성되는 모든 shorts output은 템플릿 적용 기능을 가져야 하며, 그때 표시되는 템플릿 목록은 공식 템플릿과 해당 PC의 개인 템플릿을 합친 catalog여야 한다.

## 아키텍처 방향

최종 구조는 중앙 Template API가 맞다.

```text
Clipper2 desktop app
  -> central Template API
    -> Postgres
    -> S3
```

개발 단계에서는 아래처럼 구현한다.

```text
Angular Template Builder
  -> local Clipper2 NestJS /v1/template-builder
    -> TemplateBuilderRepository abstraction
      -> JsonTemplateBuilderRepository: 개인/로컬 템플릿
      -> PostgresOfficialTemplateRepository: 공식 템플릿
    -> TemplateBuilderAssetStorage abstraction
      -> LocalTemplateAssetStorage: 개인/로컬 asset
      -> S3TemplateAssetStorage: 공식 등록 asset
```

중요한 제약:

- DB/S3 credential은 개발 단계 local `.env`에만 둔다.
- credential을 git에 커밋하거나 packaged app에 포함하지 않는다.
- 나중에 중앙 Template API로 바꿀 수 있도록 Angular와 Template Builder service contract는 DB/S3 구현을 몰라야 한다.
- local NestJS는 repository/storage interface만 의존한다.

## 기존 접속 정보 위치

실제 secret 값은 문서에 기록하지 않는다.

기존 DB 연결 패턴:

- `adlight_nestjs/src/configs/database.config.ts`
  - TypeORM Postgres 설정이 있다.
  - ClipperStudio DB 후보 env:
    - `CLIPPERSTUDIO_HOST`
    - `CLIPPERSTUDIO_PORT`
    - `CLIPPERSTUDIO_USERNAME`
    - `CLIPPERSTUDIO_PASSWORD`
    - `CLIPPERSTUDIO_NAME`
  - AWS DB 후보 env:
    - `AWS_DATABASE_HOST`
    - `AWS_DATABASE_PORT`
    - `AWS_DATABASE_USERNAME`
    - `AWS_DATABASE_PASSWORD`
    - `AWS_DATABASE_NAME`
- `adlight_python/app/configs/Environment.py`
  - SQLAlchemy/Postgres 설정이 있다.
  - AWS DB 후보 env:
    - `AWS_HOST`
    - `AWS_PORT`
    - `AWS_DB`
    - `AWS_USER`
    - `AWS_PASSWORD`

기존 S3 연결 패턴:

- `adlight_python/app/configs/Environment.py`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION`
  - `AWS_BUCKET_NAME`
- `adlight_python/app/services/S3FileUploaderService.py`
  - boto3 resource를 사용해 `AWS_BUCKET_NAME`에 upload하고 public URL을 만든다.
- `adlight_angular/sign-and-publish.js`, `electron-builder.yml`
  - `clipperstudio` bucket 사용 흔적이 있다.

Clipper2 쪽 현재 상태:

- `clipper_nestjs/.env.example`에는 DB/S3 env가 아직 없다.
- 구현 단계에서 `.env.example`에는 변수 이름만 추가하고, 실제 값은 local `.env`에만 둔다.

## DB 스키마

기존 `templates` 테이블과 이름이 겹치지 않게 새 테이블을 사용한다. 템플릿 속성은 JSONB 중심으로 저장한다. 이유는 layer/ratio/style 구조가 자주 바뀌고, 모든 속성을 컬럼으로 쪼개면 migration 비용과 코드 결합이 커지기 때문이다.

권장 테이블:

```sql
clipper2_template_families
clipper2_template_variants
clipper2_template_assets
```

### `clipper2_template_families`

- `id uuid primary key`
- `template_key text unique not null`
- `name text not null`
- `owner_type text not null`
  - `official`
  - `local_user_imported`는 DB에는 저장하지 않고 local JSON에서만 사용한다.
- `source text not null`
  - `legacy_clipper1`
  - `template_builder`
  - `imported`
- `origin_family_id text null`
- `card_thumbnail_asset_id uuid null`
- `schema_version text not null`
- `family_json jsonb not null`
- `metadata jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`
- `deleted_at timestamptz null`

### `clipper2_template_variants`

- `id uuid primary key`
- `family_id uuid not null references clipper2_template_families(id)`
- `ratio text not null`
  - `16:9`
  - `4:3`
  - `1:1`
  - `full`
- `variant_json jsonb not null`
- `sample_render_asset_id uuid null`
- `sample_thumbnail_asset_id uuid null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`
- unique `(family_id, ratio)`

### `clipper2_template_assets`

- `id uuid primary key`
- `family_id uuid null references clipper2_template_families(id)`
- `variant_id uuid null references clipper2_template_variants(id)`
- `kind text not null`
  - `card_thumbnail`
  - `layout_image`
  - `layout_layer_image`
  - `logo_image`
  - `font`
  - `sample_render`
  - `sample_thumbnail`
- `s3_bucket text not null`
- `s3_key text not null`
- `public_url text null`
- `content_type text null`
- `width int null`
- `height int null`
- `byte_size bigint null`
- `metadata jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null default now()`
- unique `(s3_bucket, s3_key)`

이 설계에서 `card_thumbnail`과 `sample_thumbnail`은 다른 asset kind다. 카드 대표 이미지와 샘플 렌더 결과를 더 이상 같은 필드에 섞지 않는다.

## S3 저장 정책

공식 템플릿 등록 시 모든 공식 asset은 `clipperstudio` bucket 아래 `templates/` prefix로 정규화한다.

권장 key 구조:

```text
templates/
  families/{familyId}/card-thumbnail.png
  families/{familyId}/variants/{ratio}/layout/{layerId}.png
  families/{familyId}/variants/{ratio}/logo/logo.png
  families/{familyId}/variants/{ratio}/fonts/{fontFileName}
  families/{familyId}/variants/{ratio}/sample/thumbnail.jpg
  families/{familyId}/variants/{ratio}/sample/video.mp4
```

기존 legacy layout 이미지는 현재 S3 URL을 쓰는 경우가 있으나, 원본 파일이 `/Users/jina/project/adlight/adlight_python/layout`에 있으므로 최종 공식 등록/import 단계에서 이 로컬 원본을 S3 `templates/` prefix로 업로드하고 template JSON의 asset reference를 새 S3 asset으로 치환한다.

DB에는 가능하면 `s3_bucket`/`s3_key`를 source of truth로 저장하고, API 응답에서 `public_url` 또는 signed URL을 만들어준다. 개발 단계에서는 기존 URL 렌더링을 깨지 않기 위해 `public_url`도 같이 저장할 수 있다.

## Template Builder 저장 모델

템플릿 목록은 두 source를 합쳐 만든다.

1. 공식 템플릿: Postgres `clipper2_template_*`
2. 개인 템플릿: local JSON/filesystem

Angular가 받는 `TemplateBuilderFamily` contract는 가능한 유지한다. backend가 source별 repository를 합쳐 같은 DTO로 반환한다.

권장 family flags:

- `ownerType`
  - `system`은 기존 호환 용어로 당분간 유지 가능
  - 새 내부 모델에서는 `official` 의미로 매핑
  - `user`는 local personal template 의미로 유지
- `capabilities`
  - `canEdit`
  - `canClone`
  - `canRegisterOfficial`
  - `canDelete`
  - `canRename`
- `cardThumbnailUri`
  - 카드 대표 이미지
  - `sampleRender.thumbnailUri`와 분리

카드 썸네일 우선순위:

1. 편집 중이면 카드에 `편집 중` 상태를 표시한다. 이미지는 마지막 저장된 card thumbnail을 계속 사용한다.
2. `cardThumbnailUri`가 있으면 사용한다.
3. 샘플 렌더 결과를 카드에 임시로 보여주는 정책은 기본값으로 사용하지 않는다.
4. `layoutImage.assetUri` fallback은 마지막 fallback으로만 사용한다.
5. 이미지가 없으면 ratio fallback을 보여준다.

샘플 렌더 썸네일을 카드 대표 이미지로 쓰고 싶을 때는 명시적 액션으로 `현재 샘플을 카드 썸네일로 사용` 같은 별도 기능을 둔다. 초기 구현 범위에는 포함하지 않는다.

## 편집 모드

명시적 편집 모드를 도입한다.

상태:

- view mode
  - 템플릿 선택/비교/샘플 확인 가능
  - 수정 control 비활성 또는 숨김
- edit mode
  - `편집 시작`으로 진입
  - 변경사항은 edit session draft에 쌓임
  - 카드에는 `편집 중` badge 표시
  - `저장`은 현재 draft를 저장하지만 edit mode를 종료하지 않음
  - `취소`는 edit session 시작 상태로 복귀하고 edit mode 종료

개인 템플릿 저장:

- 관리자 권한이 없는 유저가 새 템플릿/복제본을 만들면 local JSON/filesystem에 저장한다.
- `저장`은 local personal template만 갱신한다.

공식 템플릿 등록:

- 관리자 모드에서만 `템플릿 등록` 버튼 표시.
- 등록은 현재 edit session draft를 official template으로 저장한다.
- 등록 중 필요한 asset은 S3에 업로드한다.
- 등록 완료 후 template list를 reload하고 official template badge를 보여준다.

기존 system 템플릿 보정:

- 사용자가 기존 21개 템플릿 수정을 완료하기 전까지 DB/S3 등록 구현은 시작하지 않는다.
- 보정 완료 후 복제본을 삭제한 상태에서 import/register script로 공식 템플릿 DB/S3 seed를 만든다.

## Undo/Redo

현재 전역 undo stack은 제거하거나 edit session scope로 제한한다.

규칙:

- undo/redo stack key는 `editSessionId` 또는 `familyId + ratio + editStartedAt`.
- 현재 열려 있고 편집 중인 템플릿의 변경사항만 undo/redo 가능하다.
- 다른 템플릿으로 이동하면 이전 템플릿의 undo stack으로 되돌아가지 않는다.
- 현재 edit session에서 더 되돌릴 변경이 없으면 `되돌리기` 버튼은 비활성화된다.
- `저장`은 undo stack을 유지할 수 있다.
- `취소`는 edit session을 폐기하고 undo/redo stack을 비운다.
- 템플릿 전환 시 unsaved draft가 있으면 저장/취소/계속 편집 중 하나를 요구한다.

## API 변경 방향

기존 API는 유지하되 의미를 바꾼다.

제거 또는 비활성화:

- `publish` endpoint와 Angular `게시` 버튼은 제거한다.
- sample render success가 publish/register gate가 되는 흐름을 제거한다.

추가 예정:

- `POST /template-builder/families/:familyId/edit-sessions`
- `PATCH /template-builder/edit-sessions/:sessionId`
- `POST /template-builder/edit-sessions/:sessionId/save`
- `POST /template-builder/edit-sessions/:sessionId/cancel`
- `POST /template-builder/edit-sessions/:sessionId/register-official`
- `GET /template-builder/families`
  - official + local personal merged catalog 반환

개발 단계에서는 edit session을 Angular state + backend save call로 단순화할 수 있다. 다만 API 이름과 service boundary는 나중에 중앙 Template API로 옮기기 쉬운 형태로 둔다.

## 구현 단계 초안

사용자가 기존 템플릿 보정을 완료한 뒤 다음 순서로 구현한다.

1. `게시` UI/API 제거
2. `cardThumbnailUri`와 sample render thumbnail 의미 분리
3. 명시적 edit mode 도입
4. edit-session scoped undo/redo 도입
5. Template repository/storage abstraction 정리
6. Clipper2 `.env.example`에 DB/S3 env 이름 추가
7. Postgres official template repository 추가
8. S3 template asset storage 추가
9. 관리자 전용 `템플릿 등록` flow 추가
10. 기존 21개 템플릿 import/register script 작성
11. packaged app에서 DB/S3 credential이 포함되지 않는지 확인

## 검증 기준

- 기존 21개 공식 템플릿의 카드 썸네일이 디자인팀 제공 thumbnail로 유지된다.
- 공식 템플릿을 수정해도 카드 썸네일이 layout image fallback으로 바뀌지 않는다.
- 복제본은 원본 card thumbnail을 유지하거나 개인 템플릿 전용 thumbnail을 가진다.
- 샘플 렌더를 여러 번 실행해도 공식 등록 상태와 무관하다.
- 관리자 모드에서만 `템플릿 등록`이 보인다.
- 비관리자 유저의 새 템플릿/복제본은 local personal template로만 보인다.
- 공식 템플릿은 DB에서 조회되어 모든 클라이언트 catalog에 나타난다.
- edit mode 밖에서는 실수로 저장되지 않는다.
- undo는 현재 edit session 안에서만 동작한다.
- 다른 템플릿의 과거 변경으로 되돌아가지 않는다.
- S3 업로드 asset의 DB row와 template JSON reference가 일치한다.

## 보류된 결정

- 개발 단계 direct DB 접근은 허용하지만, 제품 배포 전에는 중앙 Template API로 전환한다.
- 공식 템플릿 등록 시 생성할 card thumbnail 방식은 구현 직전 확정한다. 기본 후보는 Template Builder preview를 headless/browser screenshot으로 캡처해 S3에 올리는 방식이다.
- 기존 `system`/`user` 용어를 API DTO에서 즉시 바꿀지, 내부 DB 모델에서만 `official`/`personal`로 쓰고 DTO 호환을 유지할지는 구현 계획 단계에서 결정한다.
- 개인 템플릿을 미래에 계정 단위 cloud sync 대상으로 올릴지는 로그인/계정 시스템 설계 때 결정한다.
