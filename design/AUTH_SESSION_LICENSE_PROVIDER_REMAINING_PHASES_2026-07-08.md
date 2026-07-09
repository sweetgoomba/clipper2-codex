# Auth/Session/License/Credit/Provider Remaining Phases

작성일: 2026-07-08
목적: `AUTH_SESSION_LICENSE_PROVIDER_TARGET_DESIGN_2026-07-07.md` 구현 후속 단계와 사용자가 추가로 지적한 누락 항목을 다음 세션에서 바로 이어갈 수 있게 정리한다.

이 문서는 구현 완료 기록과 남은 작업을 분리한다. secret-bearing 값, env 값, provider key 원문, refresh token 원문, 로컬 사용자 경로 원문은 적지 않는다.

## 1. 현재 완료된 범위

### 1.1 Auth/session

- desktop OAuth deep link는 JWT URL 전달이 아니라 one-time code exchange로 변경됨.
- Electron main은 access/refresh token bundle을 `safeStorage`로 저장하고 refresh rotation을 수행함.
- local NestJS는 user access JWT를 public key로 1차 검증하고, 보호된 local API 호출에서 web_api로 user token을 relay함.
- web Google login도 server-side `user_sessions` row를 생성함.
- web access JWT에 `sid`가 들어감.
- web refresh token은 URL/localStorage에 노출하지 않고 HttpOnly cookie로만 내려감.
- `/auth/refresh`는 desktop body refresh token과 web HttpOnly cookie refresh token을 모두 지원함.
- `/auth/sessions`는 본인 session만 반환하며 `isCurrent`, client kind, browser/OS, masked IP만 노출함.
- `DELETE /auth/sessions/:id`는 같은 user의 다른 session만 revoke함.
- web client `/app/account`는 실제 로그인 기기 목록과 원격 로그아웃을 제공함.
- web_api admin member session endpoint는 회원의 활성 세션을 관리자용 sanitized summary로 반환함.
- web_admin `/members` 세션/기기 탭은 raw session id, refresh token hash, IP hash 없이 기기 label, client kind, OS/platform, app version, masked IP, 최근 사용일만 표시함.

### 1.2 License/current summary

- desktop Settings의 이용권/잔여 크레딧 dummy 표시를 live summary로 교체함.
- active license와 queued license summary를 표시함.
- `/app/history` 구매 내역 연결 버튼을 추가함.
- web client 구매 내역에서 `queued` 상태를 `시작 대기`로 표시함.
- web client `/app/credits`는 현재 잔여/총 제공/사용 크레딧과 활성/대기 이용권 요약을 먼저 표시하고, 아래에 장기 사용 내역을 표시함.
- web client `/app/purchase` 플랜 카드에는 제공 크레딧(`tokenAllowance`)을 표시함.
- active license가 있어도 새 승인 license는 queued로 발급되고, 여러 queued license를 전제로 표시함.

### 1.3 Operation/credit foundation

- `operation_policies`, `operation_runs`, `credit_ledger`, `provider_usage` 기반이 생성됨.
- `shortform.create`, `dialog_highlight.extract`, `dance_highlight.extract` 기본 operation definition이 있음.
- `/operations/start`, succeed/fail, quote 기본 API가 있음.
- 시작 시 debit, 실패 시 refund ledger를 남기는 `charge_then_refund` 모델이 구현됨.
- admin `/api-usage`는 기존 `provider_usage`에 기록된 OpenAI/Naver 호출 로그를 조회함.
- `provider_usage`는 이제 `operationRunId` 없이도 authenticated setup/manual provider search를 `usageContext`로 기록할 수 있음.
- current charge points:
  - Plugin Store 카드 `열기`: 차감 없음.
  - 사이드바 메뉴 이동: 차감 없음.
  - Shortform `클립 생성하기`: 차감 없음.
  - Shortform render queue / `숏폼 생성하기`: `shortform.create`, 현재 50 credits.
  - Dialog Highlight pipeline 시작: `dialog_highlight.extract`, 영상 길이 시작 분 단위 `ceil(sourceDurationSec / 60) * 50` credits.
  - Dance Highlight pipeline 시작: `dance_highlight.extract`, 영상 길이 시작 분 단위 `ceil(sourceDurationSec / 60) * 50` credits.
  - Dance reference/member image search, clip media search 등 provider search: 사용자 크레딧 차감 대상 아님.
  - Variation 영상 생성: 2026-07-09 첫 구현 완료. 정책은 `영상 생성` 또는 `변형하고 영상까지` 실행 시 생성 영상 1개당 20 credits.
  - Variation render queue 등록 이후 개별 render job 실패: 실패한 영상 개수만큼 `variation.render` 단가를 부분 환불한다. 현재 단가 기준 실패 job 1개당 20 credits.

### 1.4 Provider credential/runtime

- OpenAI/Naver provider credential은 DB encrypted credential 중심으로 이동함.
- admin API key page는 Runtime 상태를 보여주되 internal credential id를 UI에 표시하지 않음.
- provider credential delete는 hard delete가 아니라 `deleted_at` soft delete로 처리함. `disabled`는 재활성화 가능한 제외 상태이고, delete는 운영 목록/runtime candidate/rotation에서 제외되는 soft-deleted 상태다.
- `provider_usage`는 사용된 provider credential을 internal FK로 저장하고, admin `/api-usage`에는 raw UUID/key id 없이 credential label/status/deleted 여부만 표시함.
- OpenAI env fallback은 2026-07-09 follow-up에서 제거됨. OpenAI runtime은 DB credential만 사용하며 DB credential이 없으면 `not_configured`로 실패한다.
- Naver legacy key runtime은 정리됨.

### 1.5 Plugin smoke

- Shortform end-to-end smoke 성공: clip generation, TTS preview, render queue, archive thumbnail/video playback.
- Dance Highlight end-to-end smoke 성공: pipeline, queue, completed project, archive/detail thumbnails/videos.
- Dialog Highlight install/readiness bugs 수정 후 end-to-end smoke 성공.

### 1.6 Logging/privacy hardening

- Electron main/child JSONL log 저장 전에 token, refresh token, provider key 형태, local absolute path를 redaction함.
- local NestJS JSON logger도 token, refresh token, provider key 형태, local absolute path를 redaction함.
- Electron auth token bundle 저장 로그에서 local auth bundle path를 제거함.
- 개인정보 처리방침 반영 초안과 후속 retention/deletion TODO는 target design에 추가됨.

## 2. 핵심 정책 정리

### 2.1 Provider 호출은 과금 단위가 아님

사용자-facing credit 차감 단위는 product operation이다. 외부 provider 호출 자체는 사용자에게 별도 크레딧을 차감하지 않는다.

따라서 다음 구현에서 provider 관련 용어는 아래처럼 구분한다.

- `operation_run`: 사용자-facing 제품 실행. credit debit/refund 기준.
- `credit_ledger`: 어떤 operation 때문에 몇 credits가 차감/환불되었는지 기록.
- `external API usage log` 또는 `provider_usage`: OpenAI/Naver 등 외부 API 호출 감사/운영 진단 로그. 크레딧 차감 단위가 아님.

피해야 할 표현:

- `free provider usage`
- provider call을 billable operation처럼 보이게 하는 UI/DB 용어

### 2.2 Quote와 start는 같은 pricing input을 써야 함

`quote`는 사용자에게 예상 차감량과 실행 가능 여부를 보여주는 preflight다. `start`는 실제 DB transaction 안에서 credit을 차감하는 authoritative step이다.

두 API는 같은 billing input과 같은 서버 pricing function을 사용해야 한다.

예:

```json
{
  "operationKey": "dance_highlight.extract",
  "billingInput": {
    "sourceDurationSec": 166.3
  }
}
```

흐름:

1. UI가 `quote` 요청.
2. 서버가 billing input으로 cost/canStart/projectedBalance 반환.
3. UI가 사용자 확인 모달 표시.
4. 사용자가 동의하면 같은 billing input으로 `start` 요청.
5. 서버가 active license row를 lock하고 다시 가격/잔액을 계산한 뒤 debit.

`quote` 결과는 안내용이다. 다른 기기에서 먼저 credit을 쓸 수 있으므로, 실제 차감 판단은 반드시 `start`에서 다시 한다.

## 3. Remaining Phases

### Phase 8A. Billing quote/confirm UX

목표: 사용자가 credit 차감 지점을 명확히 알고 동의한 뒤 제품 operation을 시작하게 한다.

필수 작업:

- web_api quote/start DTO에 `billingInput` 추가.
- pricing function을 operation별로 분리한다.
- quote 응답에 `creditCost`, `currentBalance`, `projectedBalance`, `canStart`, `reason` 포함.
- desktop local NestJS에 quote/start proxy를 추가한다.
- desktop Angular에서 charge point 직전에 확인 모달을 띄운다.
- debit 성공 후 snackbar로 “N credits 차감, 잔여 M credits”를 보여준다.
- 실패/refund 후 사용자 메시지를 정리한다.

초기 적용 대상:

- Shortform render queue / `숏폼 생성하기`
- Dialog Highlight pipeline 시작
- Dance Highlight pipeline 시작

명시적 비대상:

- Plugin Store 카드 `열기`
- 사이드바 navigation
- provider image/media search

검증:

- quote와 start가 같은 input에서 같은 cost를 계산한다.
- 잔액 부족이면 local job이 시작되지 않는다.
- 사용자가 취소하면 debit이 없다.
- debit 후 Settings credit summary가 갱신된다.

현재 구현 상태:

- Shortform은 `클립 생성하기`가 아니라 `숏폼 생성하기`/render start 직전에 quote/confirm을 수행한다.
- Dialog/Dance Highlight는 pipeline start 직전에 source duration을 포함해 quote/confirm을 수행한다.
- Highlight quote modal은 영상 길이와 계산된 cost를 표시한다.
- debit/refund 후 최근 ledger history는 Phase 8D 첫 슬라이스에서 desktop Settings와 web_admin member detail에 표시한다.

### Phase 8B. Dynamic video-length pricing

목표: 하이라이트 추출 플러그인의 fixed credit cost를 영상 길이 기반 pricing으로 바꿀 수 있게 한다.

필수 작업:

- `dialog_highlight.extract`, `dance_highlight.extract` pricing에 `sourceDurationSec` 입력을 사용한다.
- local NestJS source 준비 단계에서 source duration을 안정적으로 확보한다.
- YouTube source는 기존 `SourceAsset.durationSec`를 활용한다.
- local file source는 ffprobe 기반 duration 측정이 필요하다.
- quote 모달에 영상 길이와 계산된 cost를 표시한다.
- start에서 duration 변조/누락을 서버가 거부하거나 안전한 fallback을 적용한다.

현재 결정/구현:

- 단가: `dialog_highlight.extract`, `dance_highlight.extract` 모두 50 credits / 시작 분.
- rounding: `ceil(sourceDurationSec / 60)`.
- 최소 charge: 1 started minute, 즉 최소 50 credits.
- 최대 charge cap: 현재 없음.
- duration missing/invalid 입력은 web_api가 거부한다.
- desktop Angular는 source duration을 확인하지 못하면 quote/start를 진행하지 않는다.
- 기존 기본값이 남은 DB row는 admin migration에서 `dialog_highlight.extract` 70 -> 50, `dance_highlight.extract` 80 -> 50으로 보정한다. 단, 이미 운영자가 바꾼 값은 덮어쓰지 않는다.

남은 정책/운영 결정:

- 긴 영상 maximum charge cap을 둘지.
- 실패/refund 조건을 모든 하이라이트 실패에 계속 전액 환불로 둘지, 일부 소모 비용을 둘지.
- duration을 클라이언트 제출값만으로 둘지, 서버/로컬 NestJS에서 재검증 가능한 증거를 추가할지.

검증:

- 1분/5분/30분 영상에서 expected cost가 계산된다.
- quote와 start cost가 일치한다.
- duration missing/invalid 입력은 안전하게 실패한다.

### Phase 8C. Operation policy admin

목표: 운영자가 product operation별 credit cost/policy를 조회하고 제한적으로 수정할 수 있게 한다.

현재 구현 상태:

- `web_api`에 `GET /admin/operation-policies`와 `PATCH /admin/operation-policies/:operationKey` 추가.
- `web_admin`에 `/operation-policies` 페이지와 `크레딧 정책` 상단 메뉴 추가.
- MVP 수정 가능 항목은 `creditCost`만 허용한다.
- admin 응답/화면에 단가 단위를 표시한다. `shortform.create`는 `실행 1회당`, 하이라이트 추출은 `영상 1분당`이다.
- `shortform.create` 표시명은 `클리퍼 숏폼 생성`이다.
- `Provider` 열은 admin 단가 화면에서 제거했다. `providerScopes`는 실제 provider 사용 전체가 아니라 operation run provider authorization scope라, 이 화면에서 운영 비용/사용 provider처럼 보여주면 오해를 만든다.
- Create/Delete는 열지 않았다.
- provider credential/key/secret 값은 이 화면과 API 응답에 포함하지 않는다.
- `enabled`, `updatedBy`, 변경 이력/audit은 아직 별도 phase로 남긴다.

필수 작업:

- code registry가 만든 `operation_key` row는 Create/Delete 없이 Read + 제한 Update만 허용한다.
- seed/upsert는 기존 DB 운영값을 덮어쓰지 않는다.
- 변경 이력/audit이 필요하면 별도 admin audit phase로 분리한다.

표시 항목:

- operation key
- 한국어 표시명
- 현재 pricing strategy
- fixed cost 또는 dynamic pricing parameter
- provider scopes
- updated at / updated by, 가능하면

검증:

- admin이 cost를 수정하면 quote/start에 반영된다.
- 일반 user는 operation policy admin API에 접근할 수 없다.
- provider key/credential 값은 표시하지 않는다.

### Phase 8D. Credit ledger user/admin history

목표: 사용자와 관리자가 credit 차감/환불 내역을 추적할 수 있게 한다.

필수 작업:

- user-facing credit ledger API.
- admin member credit ledger API.
- web client 또는 desktop Settings에서 “크레딧 사용 내역” 진입점 제공.
- web_admin member detail에서 user별 ledger 조회.
- `credit_ledger -> operation_runs -> user_sessions` join으로 session/device attribution 표시.

사용자 화면 표시:

- 일시
- 제품 기능명
- 차감/환불 credits
- 잔액 또는 해당 시점 잔액이 가능하면 표시
- 실행 기기 요약: 예: `Clipper Studio macOS`, `Chrome on macOS`

admin 화면 표시:

- user/email
- operation key/display name
- amount/type/reason
- run status
- session/device summary
- trace/run id

표시 금지:

- refresh token hash
- IP hash 원문
- raw IP
- provider key/secret
- local absolute path

검증:

- Shortform/Dialog/Dance 성공/실패/refund가 ledger에 보인다.
- admin은 user별 필터가 가능하다.
- user는 타 user ledger를 볼 수 없다.

현재 구현 상태:

- `web_api`:
  - user `GET /operations/ledger` 추가.
  - admin `GET /admin/members/:userId/credit-ledger` 추가.
  - 두 API 모두 `{ items, nextCursor }` page response를 반환한다.
  - cursor는 `createdAt + ledgerId` 기준이며 `limit + 1` 조회로 다음 page 여부를 판단한다.
  - admin DB에 `(user_id, created_at DESC, id DESC)` cursor index migration을 추가했다.
  - admin DB `credit_ledger`/`operation_runs`/`operation_policies`와 user DB `user_sessions`를 애플리케이션 레이어에서 합쳐 반환한다.
  - admin DB `credit_ledger.balance_after` snapshot column을 추가했다. 새 charge/refund ledger row에는 작업 처리 후 최종 잔여 credit을 저장한다.
  - 기존 과거 ledger row는 정확한 재구성이 어려우므로 `balance_after=null`로 둔다.
  - user/admin ledger API는 `from`, `to`, `type=charge|refund` query filter를 지원한다.
  - `from`/`to` date-only query는 KST 날짜 경계로 해석하며, `to`는 해당 날짜까지 포함하기 위해 다음 날 00:00 KST 미만 조건으로 조회한다.
  - 응답에는 `operationRunId`와 표시용 session summary만 포함한다. raw IP, IP hash, refresh token hash, provider secret, session/device id 원문은 포함하지 않는다.
- `desktop/clipper_nestjs`:
  - `GET /v1/operations/ledger` proxy 추가. caller bearer token과 cursor/limit query를 web_api로 relay한다.
- `desktop/clipper_angular`:
  - Settings에 최근 크레딧 사용 내역을 표시한다.
  - 표시 항목은 작업명, 일시, signed credits, session label이다.
  - Settings에서는 최근 5개만 보여주고 `전체 내역 보기`로 web client `/app/credits`를 외부 브라우저에서 연다.
- `web/clipper_web_client`:
  - `/app/credits` 장기 credit ledger 페이지를 추가했다.
  - `/app/credits` 상단에 현재 credit balance, allowance, used credits, active license, queued license summary를 표시한다.
  - 처음 20개를 표시하고 `더 보기` 버튼으로 cursor 기반 이전 내역을 하단에 append한다.
  - `/app/credits`에 시작일/종료일/유형 필터와 `처리 후 잔여` column을 추가했다.
- `web/clipper_web_admin`:
  - `/members` 상세 영역을 목록 하단 카드에서 상시 우측 drawer/detail panel로 변경했다.
  - drawer는 기본 선택 탭을 이용권으로 두고, 세션/기기, 크레딧 사용 내역 탭을 제공한다.
  - 세션/기기 탭은 `GET /admin/members/:userId/sessions`에서 받은 sanitized 활성 세션을 표시한다.
  - 크레딧 사용 내역 탭은 처음 20개를 표시하고 `더 보기` 버튼으로 cursor 기반 이전 내역을 append한다.
  - 크레딧 사용 내역 탭에 시작일/종료일/유형 필터와 `처리 후 잔여` column을 추가했다.
  - admin UI에는 raw run id를 직접 표시하지 않는다. API response에는 내부 추적용 `operationRunId`가 남아 있다.
  - admin 공통 page width를 1320px로 늘려 member drawer와 ledger table을 안정적으로 수용한다.

남은 작업:

- operation key/session filter는 아직 없다. 필요 시 별도 UX로 추가한다.
- 더 긴 admin ledger 운영을 위한 가상 스크롤은 아직 없다. 현재는 날짜/유형 필터 + cursor 더보기로 운영한다.
- 실패/refund reason을 더 사용자 친화적으로 표시할 mapping.

### Phase 8H. Desktop navigation/plugin metadata SoT cleanup

목표: desktop Angular의 nav label, page title/subtitle, plugin store display name이 중복 하드코딩되지 않고 한 메타데이터에서 파생되게 한다.

현재 구현:

- `desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts`를 desktop UI SoT로 사용한다.
- plugin feature와 shell navigation item을 같은 파일에서 관리한다.
- 사이드바 일반 메뉴, plugin feature route/display label, plugin store display name normalization, 주요 shell page title/subtitle가 이 파일에서 파생된다.
- 기존 `src/core/plugins/plugin-feature-metadata.ts`는 제거했다.

주의:

- `projects` 페이지는 section별 동적 title/subtitle가 있어 page component 내부 computed 값을 유지한다.
- `shortform-unavailable` 같은 nav item이 아닌 예외 페이지는 이 SoT 대상이 아니다.

검증:

- desktop Angular 관련 spec과 build를 통과해야 한다.
- 새 nav/page/plugin label 추가 시 같은 문자열을 component template에 다시 하드코딩하지 않는다.

### Phase 8I. Cross-repo plugin manifest/catalog/navigation metadata SoT

목표: plugin 표시 metadata가 repo 간 수동 복붙으로 drift되지 않게 한다.

현재 관찰:

- `desktop/clipper_python/plugins/*/manifest.json`은 Python plugin 자체 배포 단위의 manifest다.
- `desktop/clipper_nestjs/src/modules/plugins/domain/plugin-catalog.ts`에도 Python plugin `displayName`/`description`/capability/resource/model 정보가 일부 중복되어 있다.
- `desktop/clipper_nestjs/src/modules/plugins/domain/plugin-catalog.ts`에는 `shortform_url`, `shortform_paste`, `shortform_prompt`, `variation` 같은 virtual workflow plugin metadata도 들어 있다.
- `desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts`에는 같은 virtual workflow의 nav label, page title, plugin store display name, route, icon이 들어 있다.
- `LocalPluginHost`는 `CLIPPER_PYTHON_ROOT/plugins/*/manifest.json`을 읽어 `PluginManifestView`를 만든다.
- packaged/Electron mode에서도 Electron plugin host가 Python plugin manifest를 읽어 NestJS에 전달한다.
- `StaticPluginHost`와 virtual workflow fallback은 `PLUGIN_CATALOG`를 사용한다.
- Angular plugin detail은 API 응답의 `manifest.description`을 표시한다.
- Angular plugin store/list/navigation은 desktop UI 표시명에 대해 `app-navigation-metadata.ts`를 우선 사용한다.

문제:

- 같은 description이 `clipper_python` manifest와 `clipper_nestjs` catalog에 동시에 존재한다.
- `붙여넣기로 숏폼 제작` 같은 shortform virtual workflow 표시명이 `clipper_nestjs` catalog와 `clipper_angular` navigation metadata에 동시에 존재한다.
- local/devapp/Electron에서는 Python manifest 값이 직접 쓰이고, static/fallback 경로에서는 NestJS catalog 값이 쓰일 수 있다.
- virtual workflow는 Python manifest가 없으므로 현재는 NestJS catalog와 Angular UI metadata가 각각 필요하지만, 표시명/설명/route 의도는 drift될 수 있다.
- 서로 다른 repo 파일이므로 단순히 한 파일만 남기는 방식의 SoT는 현재 구조에서 어렵다.

현재 결정:

- 지금은 구현 변경하지 않고 문서화만 한다.
- 다음 설계 때 cross-repo plugin metadata SoT를 다시 결정한다.
- 지금 당장 `desktop_angular`가 `desktop_nestjs` TS 파일을 import하거나, 반대로 NestJS가 Angular TS 파일을 import하는 방식은 채택하지 않는다. 두 repo의 TypeScript project/rootDir/build boundary가 다르고, frontend/backend ownership도 섞인다.

추천 방향:

1. Python plugin의 원본 SoT는 `desktop/clipper_python/plugins/*/manifest.json`으로 둔다.
2. Virtual workflow의 원본 SoT는 별도 shared JSON/catalog 후보를 검토한다. 예: `desktop/shared/plugin-catalog/*.json` 또는 monorepo root shared manifest.
3. Angular는 shared JSON에서 page/nav/store metadata를 생성하거나 adapter로 읽는다.
4. NestJS는 shared JSON에서 `PluginManifestView` 기본 표시 metadata를 생성하고, capability/resource/model 같은 server-only 보강 metadata만 자기 catalog에서 유지한다.
5. 구조 변경 폭을 줄이는 1차 대안은 sync/validate script로 drift를 검출하는 것이다. 즉 당장 하나의 파일로 강제하기보다 CI/test에서 “중복 필드가 다르면 실패”시키는 방식이 현실적이다.

검토해야 할 선택지:

- Runtime read: NestJS가 `CLIPPER_PYTHON_ROOT`의 manifest를 읽는다.
- Validate script: `clipper_python` manifest와 `clipper_nestjs` catalog의 중복 필드를 비교해 drift를 실패 처리한다.
- Shared package/json: 별도 shared manifest package를 만들고 `clipper_angular`/`clipper_nestjs`/필요 시 `clipper_python`이 소비한다. 구조 변경 폭이 가장 크지만 장기 SoT로 가장 명확하다.

명시적 후속 작업:

- `shortform_url`, `shortform_paste`, `shortform_prompt`, `variation`의 `displayName`/설명/route/icon ownership을 정한다.
- Python plugin `dance_highlight`, `dialog_highlight`, `tts_supertonic`, `clipper_video_render`의 표시 metadata ownership을 정한다.
- shared JSON을 도입할 경우 Angular/NestJS build에서 repo 바깥 파일을 어떻게 포함할지 결정한다.
- shared JSON을 도입하지 않을 경우 drift validate script와 테스트를 추가한다.
- 관리자/사용자에게 노출되는 label과 내부 operation/plugin key를 분리해, label 변경이 billing operation key나 route key를 바꾸지 않게 한다.

### Phase 8E. External API usage log

목표: provider 호출을 과금이 아닌 운영 감사/진단 로그로 기록하고 admin에서 볼 수 있게 한다.

현재 구현 상태:

- `web_api`:
  - admin `GET /admin/provider-usage` 추가.
  - `provider_usage` row를 최신순 cursor page로 조회한다.
  - `operation_run_id`가 있는 row는 `provider_usage -> operation_runs -> operation_policies`를 LEFT JOIN해 product operation key/name과 run status를 반환한다.
  - `operation_run_id`가 없는 row는 `usageContext`를 표시명/식별자로 사용한다.
  - 응답 metadata에서 secret/token/password/api key/client secret/key id/credential id 계열 key는 제외한다.
  - `provider_usage.operation_run_id`를 nullable로 전환하고 `session_id`, `usage_context`를 추가하는 admin migration을 추가했다.
  - `provider_usage.provider_credential_id`를 추가해 사용 credential을 internal FK로 저장한다.
  - `provider_credentials.deleted_at`을 추가해 API key delete를 soft delete로 바꿨고, runtime/list/detail 조회는 deleted row를 제외한다.
- `desktop/clipper_nestjs`:
  - Dance reference image search는 `/media/search`에 `usageContext='dance.reference_search'`를 전달한다.
  - Shortform manual clip media search는 caller bearer token과 `usageContext='media.manual_search'`를 전달한다.
  - Remote media search proxy는 `operationRunId`가 없는 authenticated search에 `usageContext='media.manual_search'`를 전달한다.
- `web_admin`:
  - `/api-usage` route와 상단 nav `API 사용` 추가.
  - 외부 API 사용 로그 페이지에서 일시, provider, credential label/status, 제품 기능, operation key, run status, unit count, context metadata를 표시한다.
  - operation run 없는 row는 operation key 위치에 `usageContext`를 표시하고, 상태는 `-`로 표시한다.
  - cursor 기반 `더 보기`로 이전 로그를 append한다.
  - 화면에서도 secret/token/password/api key/client secret/key id/credential id 계열 metadata key를 한 번 더 제외한다.

현재 gap:

- 일부 provider 호출만 `provider_usage`에 기록된다. 현재 확인된 setup/manual Naver image search gap과 credential attribution gap은 닫혔다.
- OpenAI `/llm/variation`은 제품 기능/과금 정책이 2026-07-09에 확정됐지만, 실제 operation policy/start/provider usage 전환 구현은 아직 남아 있다.

필수 작업:

- provider usage 기록 모델은 “operation run 선택적 연결 + usageContext”로 1차 정리했다.
- 추가 provider 호출이 생기면 setup/manual search에는 `usageContext`를 남긴다. 예: `dance.reference_search`, `media.manual_search`.
- userId/sessionId는 가능한 범위에서 기록한다.
- providerCredentialId는 internal FK로만 저장하고, admin UI/API에는 원문 UUID/key id를 표시하지 않는다.
- 과거 로그 표시는 provider credential row를 soft delete로 보존하고, admin UI에는 label/status/deleted 여부만 표시한다.

중요 정책:

- provider image/media search는 사용자 credit 차감 대상이 아니다.
- provider 사용 로그는 운영/비용 분석/rotation/debug용이다.
- `disabled` credential은 나중에 다시 standby/active로 바꿀 수 있는 제외 상태다. delete는 `deleted_at`을 찍는 soft delete이며 운영 목록/rotation 후보에서 제외된다.

검증:

- Dance reference image search도 provider usage/audit에 남는다.
- manual media search도 credit ledger 없이 provider usage/audit에 남는다.
- provider secret은 response/log/UI 어디에도 나오지 않는다.
- provider credential raw UUID/key id는 admin `/api-usage` response/UI에 나오지 않는다.

### Phase 8J. Variation render billing and provider routing

목표: Variation 영상 생성 버튼을 product operation으로 묶고, 생성 영상 개수만큼 credit을 차감한다.

정책 결정:

- 차감 지점: `영상 생성` 버튼 또는 `변형하고 영상까지` 버튼.
- 차감 단위: 생성 영상 1개당.
- 단가: 20 credits / generated video.
- 예: 원본 1개 + 변형 19개로 총 20개 영상이 생성되면 `20 * 20 = 400 credits`.
- Plugin Store 카드 열기, variation 페이지 진입, preview/설정 조작은 과금하지 않는다.

필수 작업:

- 완료: `variation.render` stable operation key를 추가했다.
- 완료: pricing unit에 `per_generated_video`를 추가했다.
- 완료: quote/start billing input에 `generatedVideoCount`를 포함한다.
- 완료: desktop Angular Variation UI에서 실제 생성 영상 수를 계산해 quote/confirm을 띄운다.
- 완료: local NestJS Variation render queue 시작 전에 web_api `/operations/start`를 호출하고, queue submission 성공/실패를 succeed/fail로 보고한다.
- 완료: queue submission 이후 개별 render job이 비동기로 실패하면 실패한 job 개수만큼 부분 환불한다.
  - `credit_ledger.reference_key`는 `variation.render:<batchId>:<jobId>` 형태로 저장해 같은 failed job 중복 환불을 막는다.
  - `operation_runs.status`는 queue submission 성공 기준 `succeeded`를 유지하고 `refundedCredits`만 누적 증가시킨다.
  - retry로 새 jobId가 생성되면 그 retry job 실패는 별도 failed job으로 본다.
- 남음: `/llm/variation`이 실제 영상 생성 operation에 필요한 provider 호출인지, preview/free AI copy provider usage인지 정책을 확정한 뒤 operationRunId 또는 usageContext를 연결한다.

검증:

- generatedVideoCount가 1/20일 때 quote와 start cost가 각각 20/400 credits로 일치한다.
- 잔액 부족이면 render queue가 시작되지 않는다.
- queue submission 실패 시 refund ledger가 남는다.
- queue submission 이후 개별 render job 실패는 failed job 단위로 partial refund ledger가 남는다.
- provider 호출은 credit ledger가 아니라 provider usage log에만 남는다.

### Phase 8F. Session/device retention and privacy operations

목표: 수집한 session/device 정보의 보관/삭제 정책을 제품 운영 정책으로 확정한다.

이번에 하지 않은 결정:

- active session + 만료 후 N일 보관.
- 보안 로그 별도 N개월 보관.
- 회원 탈퇴/삭제 시 session/device/security log 처리.
- admin이 session/device/ledger를 조회한 기록을 남길지.
- IP hash secret rotation 정책.

구현 후보:

- expired/revoked session cleanup job.
- account deletion 시 session revoke + refresh token invalidation.
- 개인정보 삭제 요청 시 raw가 없는 파생값도 삭제/익명화할지 정책 반영.
- admin 조회 audit log.

검증:

- 탈퇴 user는 refresh/session이 모두 무효화된다.
- retention job이 active session을 삭제하지 않는다.
- admin UI/API는 raw IP/device id/token/hash를 표시하지 않는다.

### Phase 8G. Operator/admin auth hardening

목표: user JWT와 operator/admin JWT를 완전히 분리하고 legacy `JWT_SECRET` fallback을 제거한다.

현재 상태:

- 2026-07-09 follow-up에서 user JWT는 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY` 전용 RS256 구조로 고정했고 `JWT_SECRET` fallback을 제거했다.
- 2026-07-09 follow-up에서 operator/admin JWT는 user JWT와 분리된 `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY` 또는 `OPERATOR_JWT_SECRET`만 사용하도록 변경했다.
- local/dev에서는 secret 값을 shell command에 매번 직접 넣지 않고, `web/clipper_web_api/.secrets/` 같은 gitignore된 repo-local 파일에 보관한 뒤 `.env`의 `USER_JWT_PRIVATE_KEY_PATH`, `USER_JWT_PUBLIC_KEY_PATH`, `OPERATOR_JWT_SECRET_PATH`로 참조한다. runtime은 direct env value와 `*_PATH`를 모두 지원한다.
- 2026-07-09 follow-up에서 admin DB에 `operator_sessions` table을 추가했고, operator refresh token hash 저장/rotation/logout/session list/revoke API를 추가했다.
- `web_admin`은 admin login 응답의 access/refresh token bundle을 저장하고, 일반 admin API 401에서 refresh를 1회 시도한 뒤 원 요청을 재시도한다.
- `web_admin /operators`는 모든 operator에게 `내 로그인 세션` 섹션을 보여주고, 현재 세션이 아닌 operator session을 로그아웃시킬 수 있다.
- user session과 operator session은 공통 테이블 하나로 합치지 않고 `operator_sessions`처럼 분리된 테이블/도메인으로 둔다.
- user와 operator는 권한 모델, 감사 기준, 사고 영향 범위가 다르므로 session storage를 분리해 blast radius를 줄이는 것이 중요하다.
- user web session은 desktop/web handoff UX 때문에 metadata 기반 same-device 중복 정리를 적용하지만, operator/admin web session에는 이를 적용하지 않는다. admin은 같은 계정이 여러 브라우저/프로필에서 로그인한 세션을 모두 활성 세션으로 보여주고, 운영자가 명시적으로 로그아웃/revoke하도록 한다.
- 중복을 줄여야 할 부분은 refresh token hashing, device metadata sanitizer, revoke helper 같은 낮은 수준의 유틸로 제한한다.

완료된 작업:

- operator/admin token signing key/secret을 user token과 분리한다.
- `operator_sessions` table, operator refresh token rotation, operator session revoke/list를 추가한다.
- `JwtModule`의 module-level `JWT_SECRET` 의존을 제거한다.
- user token에서 `JWT_SECRET` fallback 제거.

남은 작업:

- operator role/status를 DB schema에 실제 반영하고, payload role만 믿지 않도록 guard를 정리한다.
- permission guard를 추가해 API key write/release write/operator management 같은 민감 admin endpoint를 role/permission별로 제한한다.
- operator/admin login smoke 재검증.

검증:

- `JWT_SECRET` 없이 user desktop login/web login/admin login이 통과한다. 단, smoke 실행 시 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY` 또는 각 `*_PATH`, 그리고 `OPERATOR_JWT_SECRET`/`OPERATOR_JWT_SECRET_PATH` 또는 `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY` 계열 설정이 필요하다.
- user token으로 admin API 접근 불가.
- operator token으로 user API 접근 불가.

### Phase 9. Provider credential operation/staging hardening

목표: DB credential 기반 provider routing을 운영/스테이징에서 안전하게 확정한다.

필수 작업:

- provider credential rotation 운영 절차와 로직을 정리한다.
- Naver는 active/standby/exhausted/disabled 기반 daily limit rotation이 일부 구현되어 있으나, 운영 화면/수동 전환/실패 시 fallback 정책을 더 명확히 한다.
- OpenAI는 DB credential resolver는 있으나 standby/failover rotation 로직이 아직 충분하지 않다.
- credential status 전환 정책을 명확히 한다. `disabled`는 재활성화 가능한 제외, `deleted_at`은 soft delete로 runtime/rotation 후보에서 제외한다.
- staging/prod에서 OpenAI/Naver runtime status 확인.
- provider credential decrypt failure/empty secret 상태에서 user-facing 오류와 admin runtime 상태 정리.
- provider usage log와 credential label/rotation 분석 연결.
- OpenAI env fallback 완전 제거는 2026-07-09 follow-up에서 완료됐다. `OPENAI_API_KEY`/`OPENAI_API_KEY_ENV_FALLBACK_ENABLED`는 더 이상 OpenAI runtime credential 결정에 사용하지 않는다.

검증:

- DB credential로 Shortform/Dialog/Variation provider call 성공.
- Naver DB credential로 Dance reference image search 성공.
- disabled/exhausted/excluded credential은 runtime resolver에서 제외된다.
- UI/log/API에 provider secret 원문이 노출되지 않는다.

### Phase 10. End-to-end billing QA

목표: auth/session/license/credit/provider routing을 실제 사용자 흐름에서 회귀 없이 확인한다.

필수 smoke:

- 신규 web login -> session list에 web browser 표시.
- desktop login -> session list에 Clipper Studio 표시.
- web account page에서 다른 session revoke -> 해당 session의 다음 API/refresh 실패.
- active license 없음 -> billable operation start 실패.
- active license 있음 -> quote/confirm -> debit -> ledger 표시.
- insufficient credits -> local job 미시작.
- local job 실패 -> refund ledger 표시.
- queued license 있음 -> Settings/history 표시.
- multi-device concurrent start -> DB transaction lock으로 초과 차감 방지.

남은 manual QA:

- packaged app이 아닌 devapp 기준으로 먼저 검증.
- 이후 staging/prod credential과 실제 Google OAuth redirect에서 재검증.

## 4. Deferred / intentionally skipped

### `/llm/variation`

2026-07-09에 과금 정책은 확정됐고, render billing과 개별 render job 실패 부분 환불 구현이 완료됐다. Variation 영상 생성은 generated video 1개당 20 credits로 과금한다.

남은 구현 전까지:

- `/llm/variation` provider routing은 `variation.render` credit ledger와 섞지 않는다.
- preview/free 성격의 카드 생성과 실제 영상 render generation을 UI/API 레벨에서 명확히 분리한다.

### Plugin Store open/navigation billing

Plugin Store 카드 `열기`와 사이드바 navigation은 과금하지 않는다. 제품 실행 버튼 또는 pipeline start 지점에서만 quote/confirm/debit를 고려한다.

### Provider search billing

인물별 이미지 검색, 클립별 미디어 검색, 수동 provider-backed search는 사용자 credit 차감 대상이 아니다. 운영 비용 추적을 위한 external API usage log로만 다룬다.

## 5. 다음 세션 추천 시작점

추천 순서:

1. Phase 9: provider credential rotation 운영 로직과 staging 검증. OpenAI env fallback 제거는 완료됐으므로 DB credential-only 상태를 검증한다.
2. Phase 8G: operator/admin session hardening. `operator_sessions` 분리 구조로 refresh rotation/session revoke/list를 추가.
3. Phase 8J follow-up: `/llm/variation` provider usage 전환 여부 결정.
4. Phase 8A/8B local migration + manual smoke: 하이라이트 61초/121초 이상 영상 quote와 실제 차감 재검증.
5. Phase 8H/8I: desktop UI metadata SoT는 유지하고, cross-repo plugin metadata drift 방지 방식을 결정.
6. Phase 10: end-to-end billing QA.

Phase 8A와 8B는 같은 pricing input 모델을 공유하므로 같은 설계 안에서 다루되, 구현 커밋은 API DTO/pricing, local proxy, Angular UX로 나누는 것이 좋다.
