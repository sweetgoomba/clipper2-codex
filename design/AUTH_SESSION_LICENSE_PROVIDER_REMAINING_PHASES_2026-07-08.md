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
- current charge points:
  - Plugin Store 카드 `열기`: 차감 없음.
  - 사이드바 메뉴 이동: 차감 없음.
  - Shortform `클립 생성하기`: 차감 없음.
  - Shortform render queue / `숏폼 생성하기`: `shortform.create`, 현재 50 credits.
  - Dialog Highlight pipeline 시작: `dialog_highlight.extract`, 영상 길이 시작 분 단위 `ceil(sourceDurationSec / 60) * 50` credits.
  - Dance Highlight pipeline 시작: `dance_highlight.extract`, 영상 길이 시작 분 단위 `ceil(sourceDurationSec / 60) * 50` credits.
  - Dance reference/member image search, clip media search 등 provider search: 사용자 크레딧 차감 대상 아님.
  - `/llm/variation`: 제품 operation policy 미결정으로 deferred.

### 1.4 Provider credential/runtime

- OpenAI/Naver provider credential은 DB encrypted credential 중심으로 이동함.
- admin API key page는 Runtime 상태를 보여주되 internal credential id를 UI에 표시하지 않음.
- OpenAI env fallback은 migration window용 opt-in으로 축소됨. 완전 제거는 아직 남음.
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

필수 작업:

- web_api admin operation policies list/update API.
- web_admin operation policy page.
- code registry가 만든 `operation_key` row는 Create/Delete 없이 Read + 제한 Update만 허용.
- seed/upsert는 기존 DB 운영값을 덮어쓰지 않는다.
- 변경 이력/audit이 필요하면 별도 admin audit phase로 분리.

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

### Phase 8E. Desktop navigation/plugin metadata SoT cleanup

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

### Phase 8F. Cross-repo Python plugin manifest/catalog SoT

목표: Python plugin 표시 metadata가 repo 간 수동 복붙으로 drift되지 않게 한다.

현재 관찰:

- `desktop/clipper_python/plugins/*/manifest.json`은 Python plugin 자체 배포 단위의 manifest다.
- `desktop/clipper_nestjs/src/modules/plugins/domain/plugin-catalog.ts`에도 Python plugin `displayName`/`description`/capability/resource/model 정보가 일부 중복되어 있다.
- `LocalPluginHost`는 `CLIPPER_PYTHON_ROOT/plugins/*/manifest.json`을 읽어 `PluginManifestView`를 만든다.
- packaged/Electron mode에서도 Electron plugin host가 Python plugin manifest를 읽어 NestJS에 전달한다.
- `StaticPluginHost`와 virtual workflow fallback은 `PLUGIN_CATALOG`를 사용한다.
- Angular plugin detail은 API 응답의 `manifest.description`을 표시한다.

문제:

- 같은 description이 `clipper_python` manifest와 `clipper_nestjs` catalog에 동시에 존재한다.
- local/devapp/Electron에서는 Python manifest 값이 직접 쓰이고, static/fallback 경로에서는 NestJS catalog 값이 쓰일 수 있다.
- 서로 다른 repo 파일이므로 단순히 한 파일만 남기는 방식의 SoT는 현재 구조에서 어렵다.

현재 결정:

- 지금은 구현 변경하지 않고 문서화만 한다.
- 다음 설계 때 Python plugin metadata SoT를 다시 결정한다.

추천 방향:

1. Python plugin의 원본 SoT는 `desktop/clipper_python/plugins/*/manifest.json`으로 둔다.
2. NestJS catalog는 virtual workflow와 보강 metadata 중심으로 축소한다.
3. NestJS가 Python plugin 표시 metadata가 필요하면 가능하면 Python manifest를 읽거나, monorepo root 기준 sync/validate script로 drift를 검출한다.
4. cross-repo 특성상 당장 하나의 파일로 강제하기보다 CI/test 또는 sync script로 “두 값이 다르면 실패”시키는 방식이 현실적이다.

검토해야 할 선택지:

- Runtime read: NestJS가 `CLIPPER_PYTHON_ROOT`의 manifest를 읽는다.
- Validate script: `clipper_python` manifest와 `clipper_nestjs` catalog의 중복 필드를 비교해 drift를 실패 처리한다.
- Shared package/json: 별도 shared manifest package를 만들고 두 repo가 소비한다. 구조 변경 폭이 가장 크다.

현재 구현 상태:

- `web_api`:
  - user `GET /operations/ledger` 추가.
  - admin `GET /admin/members/:userId/credit-ledger` 추가.
  - 두 API 모두 `{ items, nextCursor }` page response를 반환한다.
  - cursor는 `createdAt + ledgerId` 기준이며 `limit + 1` 조회로 다음 page 여부를 판단한다.
  - admin DB에 `(user_id, created_at DESC, id DESC)` cursor index migration을 추가했다.
  - admin DB `credit_ledger`/`operation_runs`/`operation_policies`와 user DB `user_sessions`를 애플리케이션 레이어에서 합쳐 반환한다.
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
- `web/clipper_web_admin`:
  - `/members` 상세 영역을 목록 하단 카드에서 상시 우측 drawer/detail panel로 변경했다.
  - drawer는 기본 선택 탭을 이용권으로 두고, 세션/기기, 크레딧 사용 내역 탭을 제공한다.
  - 세션/기기 탭은 `GET /admin/members/:userId/sessions`에서 받은 sanitized 활성 세션을 표시한다.
  - 크레딧 사용 내역 탭은 처음 20개를 표시하고 `더 보기` 버튼으로 cursor 기반 이전 내역을 append한다.
  - admin UI에는 raw run id를 직접 표시하지 않는다. API response에는 내부 추적용 `operationRunId`가 남아 있다.
  - admin 공통 page width를 1320px로 늘려 member drawer와 ledger table을 안정적으로 수용한다.

남은 작업:

- `/app/credits`와 admin drawer에 기간/operation/session 필터 추가 여부 결정.
- 더 긴 admin ledger 운영을 위한 가상 스크롤 또는 날짜 range query 도입 여부 결정.
- ledger row의 당시 잔액 snapshot 저장 여부 결정. 현재는 amount 중심 조회이며 historical balance는 없다.
- 실패/refund reason을 더 사용자 친화적으로 표시할 mapping.

### Phase 8E. External API usage log

목표: provider 호출을 과금이 아닌 운영 감사/진단 로그로 기록하고 admin에서 볼 수 있게 한다.

현재 gap:

- 일부 provider 호출은 `operationRunId`와 묶여 기록된다.
- Dance setup-time reference image search처럼 product operation run이 생기기 전 provider 호출은 기록 gap이 있다.
- `provider_usage`는 provider credential id/key id를 저장하지 않는다.
- admin 조회 화면이 없다.

필수 작업:

- provider usage 기록 모델을 “operation run 선택적 연결”로 정리한다.
- `operationRunId`는 nullable 또는 별도 `provider_call_logs` 도입을 검토한다.
- setup/manual search에는 `usageContext`를 남긴다. 예: `dance.reference_search`, `media.manual_search`.
- userId/sessionId는 가능한 범위에서 기록한다.
- providerCredentialId는 internal UUID로만 저장하고, admin UI에는 원문 전체를 표시하지 않는다. 필요하면 label 또는 짧은 prefix만 표시한다.
- admin external API usage page/API 추가.

중요 정책:

- provider image/media search는 사용자 credit 차감 대상이 아니다.
- provider 사용 로그는 운영/비용 분석/rotation/debug용이다.

검증:

- Dance reference image search도 provider usage/audit에 남는다.
- manual media search도 credit ledger 없이 provider usage/audit에 남는다.
- provider secret은 response/log/UI 어디에도 나오지 않는다.

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

- user JWT는 RS256 target 구조로 이동 중이다.
- `JWT_SECRET`은 legacy user/operator/admin fallback 때문에 아직 남아 있다.

필수 작업:

- operator/admin token signing key/secret을 user token과 분리한다.
- `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY` 또는 최소 별도 `OPERATOR_JWT_SECRET` 정책을 결정한다.
- `JwtModule`의 module-level `JWT_SECRET` 의존을 줄인다.
- user token에서 `JWT_SECRET` fallback 제거.
- operator/admin login smoke 재검증.

검증:

- `JWT_SECRET` 없이 user desktop login/web login/admin login이 통과한다.
- user token으로 admin API 접근 불가.
- operator token으로 user API 접근 불가.

### Phase 9. Provider credential operation/staging hardening

목표: DB credential 기반 provider routing을 운영/스테이징에서 안전하게 확정한다.

필수 작업:

- OpenAI env fallback 완전 제거 여부 결정 및 실행.
- provider credential rotation 운영 절차 문서화.
- staging/prod에서 OpenAI/Naver runtime status 확인.
- provider credential decrypt failure/empty secret 상태에서 user-facing 오류와 admin runtime 상태 정리.
- provider usage log와 credential label/rotation 분석 연결.

검증:

- env fallback off 상태에서 DB credential로 Shortform/Dialog 성공.
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

현재 제품 operation key가 없다. 사용자가 variation 기능과 과금 포인트를 아직 정확히 파악하지 못한 상태이므로 billable operation으로 묶지 않는다.

다음 결정 전까지:

- 새 credit charge point를 만들지 않는다.
- `variation.generate` 같은 operation key를 임의 추가하지 않는다.
- preview/free 성격으로 분리할지, generation 단계에서 과금할지 기획 확정 후 진행한다.

### Plugin Store open/navigation billing

Plugin Store 카드 `열기`와 사이드바 navigation은 과금하지 않는다. 제품 실행 버튼 또는 pipeline start 지점에서만 quote/confirm/debit를 고려한다.

### Provider search billing

인물별 이미지 검색, 클립별 미디어 검색, 수동 provider-backed search는 사용자 credit 차감 대상이 아니다. 운영 비용 추적을 위한 external API usage log로만 다룬다.

## 5. 다음 세션 추천 시작점

추천 순서:

1. Phase 8A/8B local migration + manual smoke: 하이라이트 61초/121초 이상 영상 quote와 실제 차감 확인.
2. Phase 8D follow-up: ledger filter/date range, historical balance snapshot 정책.
3. Phase 8C: operation policy admin.
4. Phase 8E: external API usage log admin.
5. Phase 8F/G: privacy retention과 operator auth hardening.
6. Phase 9: provider credential operation/staging hardening.

Phase 8A와 8B는 같은 pricing input 모델을 공유하므로 같은 설계 안에서 다루되, 구현 커밋은 API DTO/pricing, local proxy, Angular UX로 나누는 것이 좋다.
