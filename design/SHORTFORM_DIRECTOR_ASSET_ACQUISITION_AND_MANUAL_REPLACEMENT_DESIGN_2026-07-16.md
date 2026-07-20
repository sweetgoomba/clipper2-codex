# AI 숏폼 디렉터 — search/generated acquisition과 수동 대체 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`

## 목적

현재 `search`, `generated-image`, `generated-video` visual layer는 AssetRef가 없다는 사실만 `missing`으로 보인다. provider를 아직 정하지 않은 상태에서도 다음 두 가지는 먼저 고정할 수 있다.

1. 향후 어떤 provider adapter가 붙어도 공통으로 사용할 요청·진행·성공·실패·취소·재시도 상태
2. provider 결과를 기다리지 않고 사용자가 기존 로컬 프로젝트 에셋으로 대체하는 fallback

```text
VideoPlan search/generated layer
              ↓
     AssetAcquisition request
       not_requested
            ↓ queue
          queued
            ↓ start
          running
       ┌────┼────────┐
    succeeded       failed
                      ↓ retry
                    queued

어느 시점이든 현재 범위에서는
owned/source project artifact를
명시적 manual replacement로 연결 가능
```

이번 slice는 상태 계약과 수동 대체만 구현한다. 실제 검색·이미지 생성·영상 생성, provider/model 선택, 비용 차감, 원격 결과 다운로드와 artifact materialization은 실행하지 않는다.

## 핵심 분리

`AssetAcquisition`과 `AssetBinding`은 같은 것이 아니다.

- `AssetAcquisition`: 원래 계획 route인 search/generated 요청의 실행 상태
- `AssetBinding`: 현재 layer가 실제로 사용할 AssetRef
- `manual-replacement`: 원래 route와 다른 owned/source AssetRef를 사용자가 명시적으로 선택한 binding mode

수동 대체가 연결되어도 원래 acquisition 이력을 삭제하지 않는다. binding에 `mode: manual-replacement`를 기록하고 acquisition에는 현재 대체 AssetRef ID만 파생해 표시한다. 연결을 해제하면 기존 acquisition 상태가 다시 보인다.

## 계약

```ts
type AssetAcquisitionStrategy =
  | 'search'
  | 'generated-image'
  | 'generated-video';

interface AssetAcquisitionV1 {
  schemaVersion: 'asset-acquisition.v1';
  id: string;
  layerId: string;
  strategy: AssetAcquisitionStrategy;
  request: {
    brief: string;
    acceptedMediaKinds: Array<'image' | 'video'>;
  };
  status:
    | 'not_requested'
    | 'queued'
    | 'running'
    | 'succeeded'
    | 'failed'
    | 'cancelled';
  attempt: number;
  updatedAt?: string;
  result?: {
    assetRefId: string;
  };
  failure?: {
    code:
      | 'provider_unavailable'
      | 'timeout'
      | 'rate_limited'
      | 'content_policy'
      | 'no_results'
      | 'invalid_result'
      | 'unknown';
    retryable: boolean;
    message?: string;
  };
  manualReplacementAssetRefId?: string;
}

interface AssetBindingV1 {
  layerId: string;
  assetRefId: string;
  mode: 'planned-origin' | 'manual-replacement';
}
```

`request.brief`는 provider prompt가 아니라 VideoPlan layer의 provider-neutral visual intent다. provider-specific prompt, model, seed, raw request/response, URL, credential과 진단 로그는 이 계약에 넣지 않는다.

## 초기 acquisition 생성

`buildAssetPack()`은 draft VideoPlan의 visual layer 중 다음 route에만 deterministic acquisition을 만든다.

| strategy | accepted media |
|---|---|
| `search` | image, video |
| `generated-image` | image |
| `generated-video` | video |

초기 상태는 `not_requested`, `attempt: 0`이다. ID는 `asset_acquisition_${layerId}`로 결정적이다. plan 재생성 시 새 layer 기준으로 다시 만들고 stale acquisition은 승계하지 않는다.

## 상태 전이

허용 전이:

```text
not_requested ─queue→ queued
queued ─start→ running
queued ─cancel→ cancelled
running ─succeed→ succeeded
running ─fail→ failed
running ─cancel→ cancelled
failed(retryable) ─queue→ queued
cancelled ─queue→ queued
```

- queue할 때 attempt를 1 증가시키고 이전 result/failure를 지운다.
- retryable이 false인 failed request는 queue할 수 없다.
- succeeded request는 자동 재실행하지 않는다.
- 성공 result는 materialized AssetRef ID만 가진다.
- 실패 message는 사용자에게 보여도 되는 정제된 문장만 허용한다. raw provider payload/stack은 프로젝트에 저장하지 않는다.

현재 production endpoint에서는 이 전이를 실행하지 않는다. 순수 domain state machine과 저장 계약을 먼저 고정해 이후 provider adapter가 같은 규칙을 사용하게 한다.

## 수동 대체 규칙

기존 project artifact candidate API를 재사용한다.

- 대체 후보는 기존과 동일하게 로컬 검증된 `owned|source` image/video만 사용한다.
- `search` layer는 image 또는 video로 대체할 수 있다.
- `generated-image` layer는 image만 가능하다.
- `generated-video` layer는 video만 가능하다.
- `owned|source` 원래 route는 기존처럼 같은 origin의 `planned-origin` binding을 사용한다.
- `search|generated-*`에 owned/source를 연결하면 서버가 `manual-replacement` mode를 자동 결정한다.
- 클라이언트가 binding mode나 origin을 지정하지 않는다.
- 권리 확인은 계속 필수다.

resolver 결과:

- 계획 origin과 맞는 ref: `asset_ref_ready`
- 허용된 수동 대체 ref: `manual_replacement_ready`
- media 불일치 또는 허용되지 않은 origin: `asset_ref_incompatible`

## AssetPack lifecycle과 hydration

`AssetPackV1`에 `acquisitions`를 추가한다.

```ts
interface AssetPackV1 {
  // 기존 필드
  acquisitions: AssetAcquisitionV1[];
}
```

- 새 project/empty plan: acquisitions `[]`
- 새 draft VideoPlan: search/generated layer별 `not_requested`
- binding 변경: 기존 acquisition 상태를 보존하고 manual replacement locator만 재계산
- 수동 대체 해제: manual replacement field가 사라지고 기존 request 상태가 다시 노출
- 구형 director JSON에 acquisitions 또는 binding mode가 없음: read 시 메모리에서 보강하되 read만으로 rewrite하지 않음

## UX

search/generated pending requirement에는 provider 실행 버튼 대신 현재 acquisition 상태를 표시한다.

```text
[배경 · 생성 이미지]
추상적인 자외선 신호 배경

Provider 미선정 · 요청 전
[프로젝트 에셋으로 대체]
```

상태 문구:

- `not_requested`: Provider 미선정 · 요청 전
- `queued`: 요청 대기
- `running`: 처리 중
- `succeeded`: 결과 준비
- `failed`: 실패 · 재시도 가능 또는 수동 확인 필요
- `cancelled`: 요청 취소

수동 대체 picker는 기존 owned/source candidate를 사용하고 media compatibility에 따라 필터링한다. 연결된 카드에는 `수동 대체`를 명확히 표시하며 연결 해제를 제공한다.

실제 “검색”, “이미지 생성”, “영상 생성”, “재시도” 버튼은 만들지 않는다. 버튼이 생기면 provider/operation policy가 존재한다고 오해할 수 있기 때문이다.

## 수용 기준

1. search/generated visual layer마다 deterministic acquisition이 생성된다.
2. 허용 상태 전이와 retryable 규칙을 순수 domain 테스트가 고정한다.
3. provider/model/URL/raw payload/secret이 acquisition에 들어가지 않는다.
4. 구형 AssetPack은 acquisition과 binding mode를 read-only hydration한다.
5. search는 image/video, generated-image는 image, generated-video는 video로만 수동 대체된다.
6. 수동 대체 binding은 `manual-replacement`와 `manual_replacement_ready`로 식별된다.
7. 수동 대체 해제 후 원 acquisition 상태가 보존된다.
8. Angular는 acquisition 상태와 수동 대체를 보여주되 provider 실행·재시도 control을 노출하지 않는다.
9. 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- provider/model 선정과 benchmark
- 실제 search/image/video generation endpoint
- operation quote, credit charge/refund
- remote result download/cache/materialization
- provider request/response와 진단 저장
- queue worker, polling, websocket progress
- 새 upload/URL paste
- renderer/compiler/preview
- DB migration, server/Electron 실행, commit/push/deploy

## 구현 결과

2026-07-16에 이 계약을 새 `shortform_director` 전용 코드에 구현했다.

- Nest domain에 deterministic acquisition 생성과 순수 상태 머신을 추가했다.
- AssetPack rebuild가 기존 acquisition 상태를 보존하고 stale layer를 제거한다.
- 구형 저장 JSON은 read 시 acquisitions와 binding mode를 메모리에서 보강하지만 rewrite하지 않는다.
- 기존 project artifact binding API가 planned origin과 manual replacement를 서버에서 구분한다.
- 수동 대체 연결·해제 뒤에도 원 acquisition 실패·진행 상태가 보존된다.
- Angular는 acquisition 상태, media-compatible 대체 picker, `수동 대체` binding 표시를 제공한다.
- provider 시작·재시도·render 버튼과 비용 차감은 추가하지 않았다.

검증:

- desktop Nest build 및 director 테스트 39/39
- Angular production build 및 director 테스트 19/19
- 기존 `shortform_prompt` 관련 Angular/Nest/web 경로 `origin/dev` 대비 diff 0
- raw color, trailing whitespace, 고신뢰 secret-like pattern 검사 통과

## 2026-07-20 확장 — 자동 에셋 준비

위의 “provider 실행 버튼을 만들지 않는다”는 2026-07-16 foundation slice의 당시 범위다. 사용자가 최종 사용자에게 에셋을 한 장씩 준비시키는 흐름을 명시적으로 거부했으므로, 실제 제품 기본 흐름은 다음으로 변경한다.

```text
VideoPlan visual layer
  ├─ programmatic
  │   └─ 외부 에셋 없이 Motion Canvas가 도식·타이포·모션을 직접 생성
  ├─ owned
  │   └─ 같은 사용자의 기존 로컬 프로젝트 artifact를 자동 매칭
  ├─ source
  │   ├─ 기존 로컬 source artifact 자동 매칭
  │   └─ 없으면 기존 media.search 경계로 공식·실물 이미지 검색/다운로드
  ├─ search
  │   └─ 기존 media.search 경계로 이미지 검색/다운로드
  ├─ generated-image
  │   └─ Google AI Nano Banana 이미지 생성
  └─ generated-video
      └─ Google AI Veo 영상 생성
```

수동 picker는 기본 조달 수단이 아니다. 자동 결과가 부정확하거나 권리 확인이 어려운 일부 항목만 사용자가 `직접 교체`하는 fallback이다.

### 사용자 흐름

1. VideoPlan과 TTS 정렬 뒤 AssetPack이 incomplete이면 `에셋을 한 번에 자동 준비합니다` 블록을 표시한다.
2. 사용자는 캠페인 단위로 검색·생성 에셋 이용 권리와 공급자 조건을 한 번 확인한다.
3. `에셋 자동 준비` 한 번으로 현재 미해결 visual layer를 순차 처리한다.
4. 결과는 곧바로 AssetRef와 binding으로 저장되고 readiness가 다시 계산된다.
5. 실패하거나 마음에 들지 않는 항목만 기존 로컬 프로젝트 에셋으로 직접 교체한다.
6. 모든 항목이 준비되면 기존 RenderRecipe compile → immutable staging → Motion Canvas render 흐름을 그대로 사용한다.

권리 확인 checkbox는 실제 저작권을 새로 부여하지 않는다. 캠페인 담당자가 이미 가진 사용 권한과 공급자 이용 조건을 확인했다는 attestation이다. 실제 인물, 공식 공연, 브랜드 제품처럼 동일성이 중요한 source layer는 생성형으로 fallback하지 않는다.

### 검색 선택 정책

- 기존 `ClipperStudioMediaSearchProvider`를 재사용한다. remote proxy가 설정된 packaged/local-api 구성에서는 기존 web API `media.search`와 Naver 설정을 그대로 사용한다.
- 검색어는 BrandProfile의 브랜드명·제품명, layer 설명, role을 결합한다. `source`와 `evidence`에는 `공식`을 추가한다.
- SourcePack provenance URL의 공식 host와 같은 검색 결과를 우선한다.
- 제목/host token 일치, 해상도, 세로 비율을 함께 점수화하고 이미 사용한 URL은 제외한다.
- 최대 12개 후보를 받고 최대 6회 다운로드를 시도한다. 원본 hotlink가 막히면 검색 provider가 준 thumbnail URL도 시도한다.
- 현재 Naver 경계는 이미지 검색이므로 공식 영상 컷 요구도 우선은 정지 이미지로 materialize된다. 실제 동영상 검색과 구간 추출은 별도 품질 확장이다.

현재 검색 선택은 제목·host·크기 metadata 기반이다. 이미지 픽셀을 vision model로 의미 재정렬하는 단계는 아직 포함하지 않는다. 따라서 자동 조달 기본 흐름은 완성됐지만, 사람/제품/장면의 시각적 동일성 검증은 다음 품질 경계다.

### 생성 provider

- `generated-image`: 기본 `gemini-3.1-flash-image`, 9:16, JPEG, 2K
- `generated-video`: 기본 `veo-3.1-fast-generate-preview`, 9:16, 720p, layer 길이에 따라 4/6/8초
- key는 web API의 암호화된 provider credential DB에서 활성 Gemini credential 하나만 읽는다. project, response, log, 문서에는 저장하지 않는다.
- 이미지/영상 모델은 env로 override할 수 있다.
- 실제 연예인 얼굴, 특정 브랜드 제품, 로고, 자막, UI, watermark를 생성하지 않도록 Director prompt guardrail을 넣는다.
- 생성 API는 JWT 보호된 Director 전용 web API endpoint다. 현재 slice에서는 별도 queue/job executor를 만들지 않고 local request가 long-running provider operation을 기다린다.

Google AI 사용량 비용은 renderer 라이선스 비용과 별개다. Motion Canvas 렌더는 무료 상용 기본 경로지만 Nano Banana/Veo 호출에는 공급자 사용량 비용이 생길 수 있다.

### materialization과 staging

- 검색 다운로드와 생성 결과는 `CLIPPER_DATA_DIR/shortform-director/assets/<owner hash>/<project hash>/materialized` 아래에 저장한다.
- public/project locator는 `shortform-director-asset`의 project id, opaque artifact id, 상대 경로만 가진다.
- AssetRef는 media kind/type, size, SHA-256 snapshot, provenance, rights status를 갖고 binding mode는 `automatic-acquisition`이다.
- RenderRecipe는 새 locator를 source로 허용하되 path를 public contract에 넣지 않는다.
- immutable staging 직전에 파일을 다시 열어 size/checksum/media kind를 검증하고 staged copy로 고정한다.
- provider raw payload, bearer token, API key, absolute path는 project/stage public JSON에 넣지 않는다.

### 2026-07-20 검증

- Nest 자동 준비: search, generated image/video, programmatic route를 한 번에 ready로 만들고 권리 확인 전 provider 호출 0임을 검증
- managed asset → RenderRecipe → immutable staging의 size/checksum/byte copy 검증
- Nest Shortform Director 전체 110개: 108 pass, 2 opt-in integration skip, fail 0
- Angular Shortform Director 39/39, 전체 1,544/1,544, production/packaged build pass
- web API Director 23/23, Nano Banana/Veo mock 2/2, Google credential resolver/test mock 통과, 전체 448/448, build pass
- 기존 remote media.search routing/paging 6/6
- Nest TypeScript build와 `ncc` bundle pass
- 실제 Naver/Google/OpenAI 호출, dev server/Electron GUI, deploy, migration, commit/push는 실행하지 않음

## 2026-07-20 확장 — 관리자 Gemini 다중 키 관리

초기 env-only key resolver는 운영자가 키를 안전하게 등록·교체·검증할 수 없다는 한계가 있어 기존 관리자 API 키 관리 경계로 대체했다.

### 저장과 런타임 선택

- 기존 `provider_credentials`와 `SecretCipher`를 재사용하며 provider 값에 `gemini`를 추가한다.
- DB의 provider 컬럼은 varchar이고 provider별 active 1개 partial unique index가 이미 있으므로 새 schema/migration은 필요하지 않다.
- 첫 Gemini 키는 `active`, 이후 키는 `standby`로 저장한다.
- standby 키를 운영에 쓰려면 관리자가 직접 `활성`을 실행한다. 기존 active만 standby로 바뀐다.
- active 키를 standby/disabled로 바꾸거나 삭제해도 다른 Gemini 키를 자동 활성화하지 않는다.
- Nano Banana/Veo runtime은 active Gemini DB credential만 읽으며 env fallback이나 standby 자동 승계를 하지 않는다.

### 관리자 UI와 키 테스트

- 기존 `/api-keys`에 Gemini 전용 section을 추가한다.
- 여러 키의 라벨, 마지막 네 자리만 남긴 마스킹 값, active/standby/disabled 상태를 표시한다.
- 각 행에서 추가·수정·삭제·대기·수동 활성화와 개별 테스트를 제공한다.
- 개별 테스트는 선택한 credential id만 복호화하여 Google `GET /v1beta/models?pageSize=1`을 호출한다.
- API key는 공식 `x-goog-api-key` header로만 전달하며 응답에는 `provider`, `ok`, HTTP status와 비밀이 아닌 error code만 반환한다.
- 테스트는 active 여부를 바꾸지 않고 다른 키를 호출하거나 순환하지 않는다.

### 보안과 비범위

- raw key는 create/update request와 암호화 직전 메모리 경계 밖으로 반환하지 않는다.
- 목록/runtime/test 응답, Angular state, project, log, 문서에는 raw key를 넣지 않는다.
- 자동 로테이션, 실패 시 fallback, 사용량·비용 분산, quota 기반 전환은 구현하지 않는다.
- 실제 Google 호출, DB migration 실행, server restart, deploy, commit/push는 수행하지 않는다.

### 검증

- web API Gemini/API-key targeted 35/35, 전체 82 suites·448/448, build pass
- web admin API-key focused 55/55, 기존 깨진 header spec 1개를 제외한 전체 184/184, production build pass
- 표준 web admin 전체 test command는 기존 committed `app-header.component.spec.ts` 42행 문법 파손 때문에 compilation 단계에서 막힌다. 해당 파일은 이번 범위 밖이라 수정하지 않았다.

## 2026-07-20 수정 — Nano Banana Interactions API 400

실제 `에셋 자동 준비`에서 Gemini key 연결 테스트는 200이었지만 Nano Banana 생성이 HTTP 400으로 실패했다. 기존 adapter가 provider 오류 body를 버려 그 호출의 세부 사유는 사후 복원할 수 없었지만, 코드 대조에서 Interactions API `response_format.mime_type`에 지원되지 않는 `image/png`를 지정한 확정적인 400 유발 요인을 찾았다.

- Google 공식 Interactions API의 `ImageResponseFormat.mime_type` 허용값에 맞춰 `image/jpeg`로 교정한다.
- 응답의 media type 기본값도 `image/jpeg`로 일치시킨다.
- non-2xx 응답은 HTTP status만 버리지 않고 Google JSON의 `error.status`와 `error.message`를 추출한다.
- 오류 상세는 key/query credential/Bearer 형태를 마스킹하고 공백 정규화 및 300자 제한 뒤 기존 `provider_failed` 경계로 전달한다.
- raw provider body, request prompt, API key는 log·응답·문서에 저장하지 않는다.

mock 계약 테스트에서 수정 전 JPEG 요청 기대와 오류 상세 기대가 실패함을 확인한 뒤 수정했고, web API 전체 82 suites·450/450 및 build가 통과했다. 실제 provider 재호출과 server restart는 수행하지 않았다.

## 2026-07-20 수정 — Veo `numberOfVideos` 400

Nano Banana 수정 반영 뒤 실제 자동 준비가 Veo 호출까지 진행했으나, `veo-3.1-fast-generate-preview`가 `parameters.numberOfVideos`를 지원하지 않는다는 `INVALID_ARGUMENT` 400을 반환했다.

- 현재 Veo 3.1/Fast의 출력은 요청당 1개로 고정되므로 개수를 별도 지정하지 않는다.
- text-to-video 요청에는 현재 필요한 `aspectRatio: 9:16`, `durationSeconds: 4|6|8`, `resolution: 720p`만 유지한다.
- 모델별 unsupported parameter를 자동 재시도하며 제거하지 않는다. provider가 명시한 현재 계약에 맞춰 정적으로 요청을 교정한다.

mock 계약 테스트에서 `numberOfVideos`가 없어야 한다는 기대가 기존 코드에서 실패함을 확인한 뒤 필드 하나만 제거했다. focused generated-media 3/3, web API 전체 82 suites·450/450 및 build가 통과했다. 실제 provider 재호출과 server restart는 수행하지 않았다.

## 2026-07-20 수정 — owned inventory 부재 시 dead-end 제거

초기 자동 준비는 `owned`를 “이미 다른 project에 등록된 로컬 보유 artifact”로만 해석했다. 그러나 VideoPlan 입력에는 실제 owned inventory가 없었으므로 provider가 `owned`를 선택해도 존재를 보장할 수 없었다. 수동 picker 역시 같은 candidate 목록만 사용해 candidate가 0개면 사용자가 새 파일을 넣을 수 없었다.

최종 계약은 다음과 같다.

```text
new VideoPlan draft, verified owned inventory 없음
  → provider owned visual을 search로 canonicalize

stored owned requirement
  ├─ compatible local artifact 있음 → automatic owned binding
  └─ 없음 → Layer strategy를 search로 변경
           → AssetPack/acquisition rebuild
           → 기존 media.search 자동 준비 계속

직접 교체
  ├─ 연결된 project artifact 선택
  └─ 현재 기기의 image/video 파일 업로드
       → Director local materialization
       → checksum snapshot + rights-cleared AssetRef
```

search 결과를 `owned`라고 위장하지 않는다. local candidate가 없는 순간 VideoPlan의 실제 acquisition route를 `search`로 바꾼 뒤 search-origin AssetRef를 연결한다. 이미 실패한 retryable owned acquisition도 다음 자동 준비에서 같은 전환을 거친다.

직접 업로드는 Director 전용 경계다.

- 지원: JPG, PNG, WebP, GIF, MP4, MOV, WebM
- image 최대 64MB, video 최대 256MB
- 캠페인 권리 확인 필수
- absolute path는 project/public response에 넣지 않음
- owner/project hash namespace, opaque artifact id, SHA-256 snapshot 사용
- generated-image/video replacement는 media kind를 강제
- 기존 `shortform_prompt` upload/API에는 의존하거나 변경하지 않음

검증은 Nest Director 113개 중 111 pass/2 opt-in skip/fail 0, Angular page/service 37/37, web API 관련 15/15와 세 build pass다.
