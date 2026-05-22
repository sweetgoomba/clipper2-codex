# Clipper2 Official Template -> Clipper1 Template Export Design

작성일: 2026-05-19
상태: 구현 전 조사/설계

## 목적

Clipper2 Template Builder에서 사용자가 만든 local custom/clone template을 관리자 모드에서 "공식 템플릿"으로 등록하면, 현재 Clipper2의 official template 목록뿐 아니라 기존 내부 Clipper1의 숏폼 생성 템플릿 목록에도 보이게 한다.

이번 문서는 구현 전 파악 결과와 설계 방향을 기록한다. 현재까지 구현한 것은 Clipper2 official 등록과 asset promotion까지이며, Clipper1 `templates` 테이블로 export하는 코드는 아직 없다.

## 현재 커밋/작업 상태

관련 최신 커밋:

- `clipper_nestjs` `01940c1 fix: require db for official templates`
  - Template Builder official source는 DB를 필수로 사용.
  - runtime에서 legacy seed/system override JSON fallback 제거.
  - local custom/clone은 여전히 local `template-builder.json`에 저장.
- `clipper_nestjs` `87f95e1 feat: promote official template assets`
  - official 등록 시 local App Support assets를 S3 official asset으로 승격.
  - `cardThumbnailUri`, `layoutImage`, `contentArea`, `logoImage`, `layoutLayers[].assetUri`, local font file path를 promotion 대상에 포함.
  - packaged app env fallback 보강.
- `clipper_angular` `2315a27 feat: add template builder overlays`
  - create/rename/clone/delete/admin password overlay 추가.
  - 임시 관리자 모드 password `050505` gate 추가.
  - official registration button, top-center snackbar 추가.

현재 저장소 상태:

- `clipper_nestjs`: clean
- `clipper_angular`: clean
- `.codex/session-logs/2026-05-19.log`: 이번 조사 내용 포함

## 핵심 결론

가능하다. 다만 Clipper2 official 등록은 현재 `clipper2_template_families`, `clipper2_template_variants`, `clipper2_template_assets`에만 저장한다. Clipper1은 이 테이블들을 전혀 보지 않고 기존 `templates` 테이블만 본다.

따라서 "Clipper2 공식 템플릿으로 등록" 단계에서 다음 두 저장을 모두 해야 한다.

1. Clipper2 official DB upsert
   - `clipper2_template_families`
   - `clipper2_template_variants`
   - `clipper2_template_assets`
2. Clipper1 legacy export
   - `templates` 테이블에 ratio별 4 rows insert/update
   - export mapping table에 Clipper2 family id와 Clipper1 design/template number 연결 저장

## Clipper1 템플릿 조회 흐름

### Angular frontend

관련 파일:

- `adlight_angular/src/modules/d2x-client/apis/templates.api.ts`
- `adlight_angular/src/modules/d2x-client/services/d2x-data.service.ts`
- `adlight_angular/src/modules/d2x-client/datas/template.data.ts`
- `adlight_angular/src/modules/d2x-client/components/dialogs/template-select-dialog/template-select-dialog.component.ts`
- `adlight_angular/src/modules/d2x-client/components/dialogs/template-select-dialog/template-select-dialog.component.html`
- `adlight_angular/src/modules/d2x-client/components/shorform-buttons/shorform-buttons.component.ts`
- `adlight_angular/src/modules/d2x-client/interfaces/templates-api.interface.ts`

흐름:

1. `TemplatesApi.getList()`가 `GET /v1/templates/list` 호출.
2. `D2XDataService.fetchDefaultData()`에서 templates 전체를 받아 `templateData.templates`에 저장.
3. ratio별로 `templateData.templateMap[ratio] = templates.filter(t => t.contents_ratio === ratio)` 구성.
4. `TemplateSelectDialogComponent`는 현재 ratio의 rows만 보여준다.
5. UI는 template name을 보여주지 않고 `thumbnail_url` 이미지를 사용한다.
6. 템플릿 선택 시 numeric `id`를 기준으로 `currentTemplate`을 찾는다.
7. 저장/생성 요청에는 `template_id: currentTemplate.id`를 보낸다.

Clipper1 frontend가 기대하는 template row shape:

```ts
interface IVideoTemplateServer {
  id: number;
  template: number;
  contents_ratio: '16:9' | '4:3' | '1:1' | 'full';
  origin_url: string;
  thumbnail_url: string;
  settings: Settings;
  name: null | string;
  category: null | string;
}
```

### FastAPI backend

관련 파일:

- `adlight_python/app/routers/v1/TemplatesRouter.py`
- `adlight_python/app/services/TemplatesService.py`
- `adlight_python/app/repositories/TemplatesRepository.py`
- `adlight_python/app/models/TemplateModel.py`
- `adlight_python/app/schemas/TemplateSchema.py`
- `adlight_python/app/schemas/ShortsProjectSchema.py`
- `adlight_python/app/services/ShortsProjectService.py`

조회 API:

- `GET /v1/templates/list`
  - `TemplatesService.get_all()`
  - `TemplatesRepository.get_all()`
  - `db.query(Template).order_by(Template.id.asc()).all()`

단건 API:

- `GET /v1/templates/{template_id}`
  - 현재 decorator path param 이름은 `template_id`인데 function argument는 `id: int`다.
  - 실제 사용 전 FastAPI validation 동작 확인이 필요하다.
  - 현재 Clipper1 frontend의 template list/생성 flow에서는 단건 API를 직접 쓰지 않는다.

생성 flow:

1. Angular가 `template_id`로 `templates.id`를 보낸다.
2. `ShortsProjectService.prepare_media_server_payload()`가 project row를 업데이트한다.
3. 업데이트된 `project.template_id`로 `TemplatesService.get_by_id()`를 호출한다.
4. 조회된 `template_data.contents_ratio`, `template_data.settings`를 media server payload에 넣는다.
5. media server/Python renderer는 `template_settings` JSON을 직접 사용한다.

## Clipper1 `templates` DB schema

코드 모델:

```py
class Template(EntityMeta):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    template = Column(Integer, nullable=False)
    contents_ratio = Column(Enum(TemplateRatio, name="template_ratio", create_type=False), nullable=False)
    origin_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=False)
    settings = Column(JSONB, nullable=False)
    name = Column(String(100), nullable=True)
    category = Column(String(50), nullable=True)
```

실제 DB read-only 확인 결과:

- columns:
  - `id integer not null default nextval('templates_id_seq')`
  - `name varchar nullable`
  - `category varchar nullable`
  - `thumbnail_url text not null`
  - `settings jsonb not null`
  - `template integer not null`
  - `origin_url text not null`
  - `contents_ratio template_ratio not null default '16:9'`
- constraints:
  - primary key: `templates_pkey (id)`
  - 별도 unique constraint는 확인되지 않음
- 현재 rows:
  - total rows: 84
  - design/template count: 21
  - id range: 1..84
  - ratio counts:
    - `16:9`: 21
    - `4:3`: 21
    - `1:1`: 21
    - `full`: 21
  - 각 `template` design마다 4 ratio rows가 존재
  - `name`: 현재 모두 null
  - `category`: 현재 모두 null

현재 row pattern:

```text
id 1  template 1  ratio 16:9
id 2  template 1  ratio 4:3
id 3  template 1  ratio 1:1
id 4  template 1  ratio full
id 5  template 2  ratio 16:9
...
id 84 template 21 ratio full
```

즉 신규 official family 하나를 Clipper1에도 공개하려면 일반적으로 다음이 필요하다.

```text
template = 22
rows:
  template 22, contents_ratio 16:9
  template 22, contents_ratio 4:3
  template 22, contents_ratio 1:1
  template 22, contents_ratio full
```

`id`는 sequence가 할당하는 numeric PK를 사용한다.

## Clipper1 renderer가 settings에서 요구하는 값

관련 파일:

- `adlight_python/app/schemas/ShortsProjectSchema.py`
- `adlight_python/app/services/VideoService.py`
- `adlight_angular/src/modules/d2x-client/components/video-preview/video-preview.component.html`
- `adlight_angular/src/modules/d2x-client/components/video-preview/video-preview.component.ts`

`ShortsTemplateSettingsSchema`와 `VideoService`가 legacy settings keys를 직접 참조한다. 주요 key:

### 공통 layout/media

- `contents_area_y_offset`
- `layout_image`
- `contents_area_height`는 schema에는 없지만 Clipper2 mapper가 생성할 수 있고, Clipper2 renderer 쪽에서 의미가 있다.
- `bgm_volume`은 optional이며 없으면 renderer에서 기본값 `0.15` 사용.

`layout_image`는 URL이어도 된다. `VideoService._download_layout_image_once()`가 다운로드한다.

### 상단 sub title

- `sub_title_font`
- `sub_title_font_size`
- `sub_title_color`
- `sub_title_tracking`
- `sub_title_y_offset_main_title_line_1`
- `sub_title_y_offset_main_title_line_2`
- `sub_title_left_align_margin`
- `sub_title_right_align_margin`
- `sub_title_box_color`
- `sub_title_box_alpha`
- `sub_title_box_padding_left_right`
- `sub_title_box_height`

### main title

- `main_title_font`
- `main_title_font_size`
- `main_title_color`
- `main_title2_color`
- `main_title_tracking`
- `main_1st_title_y_offset_main_title_line_1`
- `main_1st_title_y_offset_main_title_line_2`
- `main_2nd_title_y_offset_main_title_line_2`
- `main_title_left_align_margin`
- `main_title_right_align_margin`
- `main_title_box_color`
- `main_title_box_alpha`
- `main_title_box_padding_left_right`
- `main_title_box_height`
- `main_title_outline_width`
- `main_title_outline_color`
- `main_title_shadow_color`
- `main_title_shadow_outline_width`
- `main_title_shadow_outline_color`
- `main_title_shadow_x_offset`
- `main_title_shadow_y_offset`

### bottom title

- `bottom_title_font`
- `bottom_title_font_size`
- `bottom_title_color`
- `bottom_title_tracking`
- `bottom_title_y_offset`
- `bottom_title_left_align_margin`
- `bottom_title_right_align_margin`

### logo

- `logo_text_font`
- `logo_text_font_size`
- `logo_text_color`
- `logo_text_tracking`
- `logo_text_y_offset`
- `logo_image_y_offset`
- `logo_image_area_width`
- `logo_image_area_height`

### subtitle/caption

- `subtitle_font`
- `subtitle_font_size`
- `subtitle_font_color`
- `subtitle_tracking`
- `subtitle_1st_y_offset_subtitle_line_1`
- `subtitle_1st_y_offset_subtitle_line_2`
- `subtitle_2nd_y_offset_subtitle_line_2`
- `subtitle_left_align_margin`
- `subtitle_right_align_margin`
- `subtitle_box_color`
- `subtitle_box_alpha`
- `subtitle_box_padding_left_right`
- `subtitle_box_height`
- `subtitle_box_border_color`
- `subtitle_box_border_width`
- `subtitle_outline_width`
- `subtitle_outline_color`
- `subtitle_shadow_color`
- `subtitle_shadow_outline_width`
- `subtitle_shadow_outline_color`
- `subtitle_shadow_x_offset`
- `subtitle_shadow_y_offset`

## 중요한 font 호환성 이슈

기존 Clipper1 DB settings의 font 값은 `JalnanGothic.otf`, `Pretendard-SemiBold.otf` 같은 파일명이다.

`adlight_python/app/services/VideoService.py`는 다음처럼 로컬 path를 조립한다.

```py
fonts_dir = os.path.join(self.PROJECT_ROOT, 'fonts')
main_title_font_path = os.path.join(fonts_dir, self.template_settings["main_title_font"])
```

즉 Clipper1 renderer는 font URL을 다운로드하는 구조가 아니다. Clipper2 official registration은 local font를 S3 URL로 승격할 수 있지만, 그 URL을 그대로 Clipper1 `templates.settings.*_font`에 넣으면 기존 Clipper1 renderer가 `app/fonts/https://...` 같은 잘못된 path를 만들 가능성이 높다.

따라서 첫 구현에서는 Clipper1 export 대상 font를 다음 중 하나로 제한해야 한다.

1. Clipper1 `adlight_python/fonts`에 이미 있는 legacy filename만 허용한다.
2. upload font가 쓰인 Template Builder family는 Clipper1 export를 차단하고 에러를 보여준다.

업로드 font까지 Clipper1에서 쓰려면 별도 선행 작업이 필요하다.

- Clipper1 `VideoService`가 font URL을 다운로드/cache해서 `ImageFont.truetype()`에 local path를 넘기도록 수정.
- 또는 official registration 시 Clipper1 runtime이 접근하는 `app/fonts` 위치에 font를 동기화하는 배포/운영 경로 마련.

현재는 1번 또는 2번이 안전하다.

## Clipper2 현재 official registration 구조

관련 파일:

- `clipper_nestjs/src/template-builder/template-builder.service.ts`
- `clipper_nestjs/src/template-builder/template-builder-official-postgres.repository.ts`
- `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`

현재 flow:

1. `TemplateBuilderService.registerOfficialTemplate(familyId)`
2. admin mode 확인
3. `getFamily(familyId)`
4. `prepareOfficialFamily(source)`
5. `promoteOfficialFamilyAssets(official)`
6. `officialTemplates().upsert(official)`

현재 official registration이 쓰는 DB tables:

- `clipper2_template_families`
- `clipper2_template_variants`
- `clipper2_template_assets`

현재 official registration은 Clipper1 `templates`를 쓰지 않는다.

## 기존 변환 로직 재사용 가능성

관련 파일:

- `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
- `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`
- `clipper_nestjs/src/template-builder/template-builder-render-contract.ts`

`LegacyClipper1RenderPayloadMapper.templateBuilderSettingsFor()`는 Template Builder layers를 legacy Clipper1 settings key로 변환하는 로직을 이미 갖고 있다.

현재는 private method이고 render payload mapper 내부에 묶여 있다. Clipper1 DB export에서도 같은 변환이 필요하므로 다음 중 하나가 필요하다.

- 권장: `TemplateBuilderLegacySettingsMapper` 같은 service/helper로 추출.
- 대안: official export service 안에 변환 로직을 복제.

복제는 나중에 preview/render/export 간 값 불일치를 만들 가능성이 높으므로 추출이 낫다.

## 필요한 신규 설계

### 1. Clipper1 export repository

NestJS에 Clipper1 `templates`를 다루는 repository를 추가한다.

예상 interface:

```ts
export interface TemplateBuilderLegacyClipper1ExportRepository {
  ensureSchema(): Promise<void>;
  getExportByFamilyId(familyId: string): Promise<LegacyClipper1ExportMapping | null>;
  allocateTemplateDesign(): Promise<number>;
  upsertExport(input: LegacyClipper1ExportInput): Promise<LegacyClipper1ExportResult>;
}
```

주의:

- Clipper2 official DB와 Clipper1 `templates`는 현재 같은 Postgres DB에 있다.
- 그래도 code boundary는 분리하는 편이 낫다.
- 같은 transaction으로 묶으려면 현재 `TemplateBuilderOfficialPostgresRepository.upsert()`가 내부적으로 client query를 직접 실행하는 구조라 transaction client 주입/공유 설계가 필요하다.

### 2. Export mapping table

재등록 때 매번 새 Clipper1 design을 만들면 템플릿 목록이 중복된다. Clipper2 family와 Clipper1 `template` design number를 연결하는 mapping table이 필요하다.

제안:

```sql
create table if not exists clipper2_template_legacy_exports (
  family_id text primary key,
  legacy_template integer not null unique,
  legacy_row_ids jsonb not null,
  created_at timestamptz not null,
  updated_at timestamptz not null
);
```

`legacy_row_ids` 예:

```json
{
  "16:9": 85,
  "4:3": 86,
  "1:1": 87,
  "full": 88
}
```

선택적으로 다음 컬럼도 고려할 수 있다.

- `legacy_table text not null default 'templates'`
- `family_name text`
- `last_export_payload_hash text`
- `last_error text`

초기 구현에는 필요 최소한만 두는 게 낫다.

### 3. 신규 등록 vs 재등록

신규 등록:

1. mapping 없음.
2. `legacy_template = max(templates.template) + 1` 할당.
3. 4 ratio rows insert.
4. 생성된 numeric `id`를 mapping table에 저장.

재등록:

1. mapping 있음.
2. 기존 `legacy_template` 유지.
3. 기존 4 rows update.
4. 누락 row가 있으면 insert 후 mapping 보정.

업데이트 기준:

- 가장 안전: mapping의 `legacy_row_ids[ratio]`로 update.
- 보조 안전장치: row id가 사라졌으면 `(template = legacy_template and contents_ratio = ratio)`로 찾고 복구.

### 4. Clipper1 row payload 생성

Template Builder family one -> Clipper1 templates four rows:

```ts
type LegacyClipper1TemplateRowDraft = {
  template: number;
  contents_ratio: '16:9' | '4:3' | '1:1' | 'full';
  origin_url: string;
  thumbnail_url: string;
  settings: Record<string, unknown>;
  name: string | null;
  category: string | null;
};
```

값 정책:

- `template`: mapping 또는 신규 allocation
- `contents_ratio`: variant ratio
- `name`: 현재 Clipper1 UI는 안 쓰지만 family name을 넣어도 DB schema상 가능
- `category`: 기존 rows는 null이다. 불필요하면 null 유지.
- `settings`: TemplateBuilder variant -> legacy settings 변환 결과
- `thumbnail_url`: ratio별 thumbnail URL
- `origin_url`: ratio별 origin/preview URL

`name/category` 결정:

- 현재 Clipper1 rows 모두 `name/category` null이고 UI도 사용하지 않는다.
- 사용자가 이름 표시를 원하지 않는 이상 초기 export는 기존과 맞춰 `name = null`, `category = null`이 가장 보수적이다.
- 나중에 Clipper1 UI에서 이름을 보여줄 계획이면 `name = family.name`, `category = 'shorts'`로 바꿀 수 있다.

### 5. Ratio별 thumbnail/origin asset

Clipper1 목록 UI는 `thumbnail_url`만 직접 사용한다.

하지만 table schema상 `origin_url`도 NOT NULL이고 기존 data도 ratio별 origin URL을 갖고 있다. 따라서 신규 export에도 ratio별로 둘 다 채워야 한다.

현재 Clipper2 Template Builder에는 family 대표 `cardThumbnailUri`가 있다. 이것은 Clipper1 ratio별 row thumbnail과 의미가 다르다.

필요한 방식:

1. official registration 시 각 ratio variant에 sample render 결과가 있는지 확인.
2. 없으면 registration 전에 sample render를 강제하거나, "모든 비율 샘플 렌더가 필요합니다"로 차단.
3. sample render thumbnail/video 또는 rendered still을 S3 official path로 승격.
4. Clipper1 `thumbnail_url`, `origin_url`에 ratio별 URL 저장.

권장 S3 key 예:

```text
templates/official/<familyId>/clipper1/<ratio>/thumbnail.png
templates/official/<familyId>/clipper1/<ratio>/origin.png
```

또는 legacy naming과 맞추려면:

```text
template/<legacy_template>_ratio_<ratio>_thumb.png
template/<legacy_template>_ratio_<ratio>_origin.png
```

두 번째는 기존 Clipper1 naming과 맞지만 기존 bucket/prefix와 충돌 관리가 더 중요하다. Clipper2 공식 등록 산출물임을 명확히 하려면 첫 번째가 더 안전하다.

### 6. Validation policy

Clipper1 export 전에 다음을 검증해야 한다.

- family가 official 등록 가능 상태인지.
- 4개 ratio variant가 모두 존재하는지.
- 각 variant validation이 valid인지.
- 각 ratio thumbnail/origin URL을 만들 수 있는지.
- `settings.layout_image`가 remote URL이거나 Clipper1 renderer가 접근 가능한 URL인지.
- font가 Clipper1 compatible인지.
  - 초기 구현: fontFamily가 filename이고 Clipper1 fonts dir에 존재해야 함.
  - S3/http font URL이면 export 차단.
- legacy settings 변환 결과가 `ShortsTemplateSettingsSchema`를 만족하는지.

### 7. UI/UX

현재 Template Builder의 "템플릿 등록" 버튼은 관리자 모드 + 편집 모드 아님 + local custom/clone일 때 보인다.

등록 전에 Clipper1 export까지 포함한다면 snackbar/error 문구도 바뀌어야 한다.

성공:

- `템플릿을 공식 등록했습니다. Clipper1에도 반영되었습니다.`

검증 실패 예:

- `Clipper1 등록에는 4개 비율의 샘플 렌더가 모두 필요합니다.`
- `Clipper1에서 사용할 수 없는 업로드 폰트가 포함되어 있습니다.`
- `Clipper1 등록용 썸네일을 만들 수 없습니다.`

초기 구현에서는 Clipper1 export dry-run API를 먼저 만들면 UI에서 "등록 전 검사"를 붙일 수 있다.

## 권장 구현 순서

### Phase 1. Dry-run/export preview

목표:

- DB에 쓰지 않고 selected family가 Clipper1 `templates` 4 rows로 변환 가능한지 확인.

작업:

- `TemplateBuilderLegacySettingsMapper` 추출.
- `TemplateBuilderLegacyClipper1ExportService.preview(familyId)` 추가.
- 각 ratio row draft 생성.
- validation errors/warnings 반환.

검증:

- legacy 21개 official family 중 하나를 변환했을 때 기존 catalog settings와 큰 차이가 없는지 snapshot 비교.
- custom family with missing ratio/font URL/sample render에 대해 차단 사유가 정확히 나오는지 test.

### Phase 2. Mapping table + upsert

목표:

- family id별로 Clipper1 design number를 안정적으로 유지.

작업:

- `clipper2_template_legacy_exports` schema 생성.
- 신규 등록: `max(template)+1` 할당 후 4 rows insert.
- 재등록: mapping 기반 4 rows update.
- concurrency 방지: allocation 시 DB lock 필요.

주의:

- `max(template)+1`는 동시 등록에서 race가 날 수 있다.
- Postgres advisory lock 또는 transaction 안에서 lock table/sequence를 사용해야 한다.
- Clipper1 `templates.template` 자체 sequence가 없으므로 allocation 정책을 명시해야 한다.

### Phase 3. Official registration에 연결

목표:

- Template Builder의 기존 official registration button 하나로 Clipper2 official + Clipper1 export가 함께 끝난다.

작업:

- `registerOfficialTemplate()`에서 official family asset promotion 후 legacy export 실행.
- 실패 시 부분 성공 정책 결정.

권장 정책:

- 초기에는 "둘 중 하나라도 실패하면 실패로 보고 사용자에게 명확히 표시"가 낫다.
- DB transaction을 완전히 묶기 어렵다면 단계별 결과를 반환하고, 재시도 가능하게 idempotent upsert를 보장한다.

### Phase 4. Ratio별 thumbnail/origin 자동 생성

목표:

- Clipper1 list/preview가 요구하는 ratio별 이미지가 자동으로 준비된다.

작업:

- 등록 전 4 ratio sample render 존재 확인.
- 없으면 자동 sample render job 실행 또는 차단.
- sample render thumbnail/origin을 S3에 업로드.
- Clipper1 row `thumbnail_url`, `origin_url`에 저장.

초기 보수안:

- 자동 render까지 넣지 않고, "4개 비율 샘플 렌더를 먼저 성공시켜야 등록 가능"으로 시작.
- 이후 자동 render로 확장.

## Transaction/rollback 고려

현재 official registration은 `TemplateBuilderOfficialPostgresRepository.upsert()`가 독립적으로 DB write를 수행한다.

Clipper1 export까지 atomic하게 만들려면:

- 같은 pg client transaction을 공유하도록 repository 구조 변경.
- 또는 service layer에서 transaction client를 생성하고 official/legacy repository 모두에 넘김.

하지만 초기 구현에서는 다음 pragmatic path가 가능하다.

1. asset promotion은 idempotent remote write로 본다.
2. Clipper2 official upsert 실행.
3. Clipper1 export upsert 실행.
4. Clipper1 export가 실패하면 registration endpoint는 실패 응답.
5. 재시도 시 같은 family id mapping을 사용해 보정.

이 경우 Clipper2 official만 성공하고 Clipper1 export가 실패하는 잠깐의 불일치가 가능하다. 사용자가 "공식 등록 = 둘 다 반영"으로 이해한다면 최종적으로 transaction 공유 구조를 갖추는 것이 낫다.

## 현재 가장 큰 리스크

1. Font 호환성
   - Clipper1은 local `app/fonts/<filename>` 방식.
   - Clipper2 official은 font를 S3 URL로 승격할 수 있음.
   - 그대로 export하면 Clipper1 render가 깨질 수 있음.

2. Thumbnail/origin 준비
   - Clipper1은 ratio별 row thumbnail을 요구.
   - Clipper2 family 대표 card thumbnail 하나로는 부족.

3. Design number allocation
   - `templates.template`에 unique constraint가 없다.
   - 동시 등록 시 `max(template)+1` race 가능.

4. Partial publish
   - Clipper2 official DB와 Clipper1 legacy table이 모두 update되어야 사용자가 기대하는 결과.
   - transaction boundary를 설계해야 함.

5. Existing Clipper1 API bug 가능성
   - `GET /v1/templates/{template_id}` 라우트 argument mismatch.
   - list flow에는 영향 없지만, export 후 단건 조회나 관리 기능에서 문제 될 수 있음.

## 다음 세션에서 먼저 확인할 것

1. 사용자에게 정책 확인:
   - Clipper1 export 초기 버전에서 upload font 사용 template은 차단해도 되는가?
   - 등록 전 4개 ratio sample render 필수로 시작해도 되는가?
   - Clipper1 `name/category`는 기존처럼 null로 둘지, family name/category를 넣을지?

2. 구현 시작 전 백업:
   - `templates`
   - `clipper2_template_families`
   - `clipper2_template_variants`
   - `clipper2_template_assets`
   - 신규 mapping table이 생긴 뒤에는 `clipper2_template_legacy_exports`

3. 첫 구현 범위:
   - dry-run API + mapper extraction + tests까지만 먼저.
   - 실제 DB write는 dry-run 결과를 확인한 뒤 별도 단계.

## 참고한 주요 파일

Clipper1:

- `adlight_angular/src/modules/d2x-client/apis/templates.api.ts`
- `adlight_angular/src/modules/d2x-client/services/d2x-data.service.ts`
- `adlight_angular/src/modules/d2x-client/datas/template.data.ts`
- `adlight_angular/src/modules/d2x-client/components/dialogs/template-select-dialog/template-select-dialog.component.ts`
- `adlight_angular/src/modules/d2x-client/components/dialogs/template-select-dialog/template-select-dialog.component.html`
- `adlight_angular/src/modules/d2x-client/components/shorform-buttons/shorform-buttons.component.ts`
- `adlight_angular/src/modules/d2x-client/interfaces/templates-api.interface.ts`
- `adlight_python/app/routers/v1/TemplatesRouter.py`
- `adlight_python/app/services/TemplatesService.py`
- `adlight_python/app/repositories/TemplatesRepository.py`
- `adlight_python/app/models/TemplateModel.py`
- `adlight_python/app/schemas/TemplateSchema.py`
- `adlight_python/app/schemas/ShortsProjectSchema.py`
- `adlight_python/app/services/ShortsProjectService.py`
- `adlight_python/app/services/VideoService.py`

Clipper2:

- `clipper_nestjs/src/template-builder/template-builder.service.ts`
- `clipper_nestjs/src/template-builder/template-builder-official-postgres.repository.ts`
- `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
- `clipper_nestjs/src/project-manifest/template-builder-published-preset-source.ts`
- `clipper_nestjs/src/template-builder/template-builder-render-contract.ts`
- `clipper_nestjs/src/project-manifest/catalogs/legacy-clipper1-templates.ko.json`
