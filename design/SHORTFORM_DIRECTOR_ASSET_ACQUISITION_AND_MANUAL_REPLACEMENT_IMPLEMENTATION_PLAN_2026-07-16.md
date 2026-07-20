# AI 숏폼 디렉터 — asset acquisition과 수동 대체 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`

## Task 1 — RED domain contract

- [x] search/generated layer별 acquisition 초기 snapshot 테스트를 추가한다.
- [x] queue/start/succeed/fail/cancel/retry 상태 전이 테스트를 추가한다.
- [x] non-retryable 실패와 잘못된 전이 거부 테스트를 추가한다.
- [x] manual replacement media/origin 호환성과 reason 테스트를 추가한다.
- [x] 구형 AssetPack read-only hydration 테스트를 추가한다.

## Task 2 — NestJS foundation

- [x] `asset-acquisition.v1`과 binding mode 계약을 추가한다.
- [x] 순수 acquisition state machine을 구현한다.
- [x] `buildAssetPack()`이 acquisition을 생성·보존·prune하도록 확장한다.
- [x] JSON repository가 acquisitions와 기존 binding mode를 read-only 보강하도록 한다.
- [x] owned/source binding과 search/generated manual replacement를 서버가 구분한다.
- [x] 수동 대체 해제 후 기존 acquisition 상태를 보존한다.

## Task 3 — Angular UX

- [x] acquisition과 binding mode model을 반영한다.
- [x] search/generated pending requirement에 acquisition 상태를 표시한다.
- [x] search/generated에 기존 project artifact 수동 대체 picker를 제공한다.
- [x] media compatibility로 후보를 필터링한다.
- [x] 연결된 카드에 수동 대체를 표시한다.
- [x] provider 실행·재시도·render control 부재를 회귀 검증한다.

## Task 4 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] raw color, secret-like token, trailing whitespace를 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.

## 구현 결과

- desktop Nest build와 `test/shortform-director-*.test.js` 39/39 통과
- Angular production build와 `features/shortform-director/**/*.spec.ts` 19/19 통과
- 기존 Angular/Nest/web shortform 경로는 `origin/dev` 대비 diff 0
- Angular 새 SCSS raw color 0, 변경 diff whitespace·고신뢰 secret pattern 검사 통과
- 실제 acquisition endpoint, provider 호출, operation charge, renderer control은 추가하지 않음

## 2026-07-20 자동 준비 확장

### Task 5 — 자동 라우팅과 로컬 materialization

- [x] owned/source도 provider-neutral acquisition 상태를 갖게 한다.
- [x] owned/source는 기존 프로젝트 artifact를 먼저 자동 매칭한다.
- [x] source/search는 기존 remote media.search/Naver 경계를 재사용한다.
- [x] 공식 SourcePack host, 검색 title, 해상도와 세로 비율로 후보를 정렬한다.
- [x] 중복 URL을 제외하고 원본 실패 시 thumbnail까지 최대 6회 다운로드한다.
- [x] 검색·생성 결과를 owner/project-scoped Director local storage에 저장한다.
- [x] 자동 AssetRef/binding과 acquisition 성공·실패 상태를 원자적으로 다시 계산한다.

### Task 6 — Nano Banana와 Veo

- [x] JWT 보호 Director generated-media web API를 추가한다.
- [x] 1차로 `GEMINI_API_KEY` env-only resolver를 추가했다. 2026-07-20 Task 9에서 관리자 DB credential 방식으로 대체했다.
- [x] 9:16 Nano Banana 이미지 응답을 검증·materialize한다.
- [x] Veo long-running operation을 poll하고 9:16 MP4를 검증·materialize한다.
- [x] provider/model/secret/raw payload가 Director project에 들어가지 않게 한다.
- [x] 실제 인물·브랜드 제품을 reference 없이 생성하지 않는 prompt guardrail을 추가한다.

### Task 7 — 한 번에 준비하는 UX

- [x] 캠페인 단위 권리/공급자 조건 확인 checkbox를 추가한다.
- [x] incomplete AssetPack에 `에셋 자동 준비` 단일 action을 추가한다.
- [x] 검색/생성/프로그램 모션 라우팅을 쉬운 문구로 설명한다.
- [x] 자동 결과와 실패 사유를 표시한다.
- [x] 기존 picker는 `직접 교체` fallback으로 유지한다.
- [x] 자동 준비 중 중복 mutation을 막는다.

### Task 8 — staging과 회귀

- [x] managed Director locator를 RenderRecipe source 계약에 추가한다.
- [x] managed 파일 snapshot을 immutable staging 직전에 재검증한다.
- [x] 자동 materialized byte가 staged copy까지 보존되는 테스트를 추가한다.
- [x] Angular Director 39/39, 전체 1,544/1,544와 packaged build를 통과한다.
- [x] Nest Director 110개 중 108 pass/2 opt-in skip/fail 0과 `ncc` bundle을 통과한다.
- [x] web API Director 23/23, Google adapter/resolver 4/4, 전체 438/438과 build를 통과한다.
- [x] 기존 remote media.search routing/paging 6/6을 통과한다.
- [x] 기존 `shortform_prompt` source를 수정하지 않는다.
- [x] 실제 provider 호출, server/GUI 조작, migration, deploy, commit/push를 실행하지 않는다.

### 다음 품질 경계

- [ ] 검색 후보의 실제 픽셀을 읽는 vision semantic reranking과 인물/제품 동일성 검증
- [ ] 이미지 위주의 공식 검색을 동영상 검색·구간 추출까지 확장
- [ ] 실제 Naver 결과와 Nano Banana/Veo 결과의 품질·비용·latency benchmark
- [ ] 사용자 local-api E2E에서 자동 준비 → stage → Motion Canvas MP4 확인

### Task 9 — 관리자 Gemini 다중 키 관리

- [x] 기존 provider credential provider에 `gemini`를 추가한다.
- [x] 첫 Gemini 키는 active, 이후 키는 standby로 암호화 저장한다.
- [x] active 1개를 관리자가 수동 전환하며 자동 로테이션·자동 승계를 하지 않는다.
- [x] active Gemini DB credential만 Nano Banana/Veo runtime에 공급하고 env fallback을 제거한다.
- [x] 관리자 API 키 화면에 다중 목록, 추가·수정·삭제·대기·활성 action을 추가한다.
- [x] 각 키 ID별 Google models 연결 테스트를 추가하고 raw key를 응답/log에 노출하지 않는다.
- [x] 기존 varchar provider/active unique index를 재사용해 schema migration을 추가하지 않는다.
- [x] web API targeted 35/35, 전체 448/448와 build를 통과한다.
- [x] web admin API-key focused 55/55, 기존 깨진 header spec을 제외한 전체 184/184와 build를 통과한다.
- [x] 실제 provider 호출, migration, server restart, deploy, commit/push를 실행하지 않는다.

### Task 10 — Nano Banana Interactions API MIME 계약 수정

- [x] 실제 HTTP 400을 공식 Interactions API의 이미지 출력 MIME 계약과 대조한다.
- [x] `response_format.mime_type`과 응답 기본 media type을 `image/jpeg`로 교정한다.
- [x] provider JSON 오류에서 안전하게 정제한 status/message를 보존한다.
- [x] 수정 전 실패하는 계약 테스트를 확인하고 web API 전체 450/450 및 build를 검증한다.
- [x] 사용자 local web API 재실행이 Nano 400을 넘고 Veo 호출까지 진행됨을 확인한다.

### Task 11 — Veo 모델별 unsupported parameter 제거

- [x] 실제 `INVALID_ARGUMENT`의 `numberOfVideos isn't supported` 사유를 공식 Veo text-to-video REST 계약과 대조한다.
- [x] 출력 1개가 모델 고정값이므로 `parameters.numberOfVideos`를 제거한다.
- [x] `aspectRatio`, `durationSeconds`, `resolution` 계약은 유지한다.
- [x] 수정 전 실패하는 negative contract test를 확인한다.
- [x] focused generated-media 3/3, web API 전체 450/450 및 build를 검증한다.
- [x] local web API 재실행이 요청 계약 400을 넘고 provider quota 판정 429까지 진행됨을 확인한다.
- [ ] 활성 Gemini key가 속한 Google AI Studio project를 Paid 상태와 양수 credit/quota로 준비한 뒤 다시 실행한다.

### Task 12 — owned inventory dead-end 제거와 직접 파일 업로드

- [x] verified owned inventory가 없는 VideoPlan 입력에서 provider `owned` visual을 `search`로 canonicalize한다.
- [x] 저장된 owned requirement에 compatible local candidate가 없으면 Layer route와 AssetPack acquisition을 search로 다시 만든다.
- [x] local owned candidate가 있으면 기존 automatic binding을 유지하고 search/provider를 호출하지 않는다.
- [x] Director 전용 multipart image/video upload와 owner/project-scoped materialization을 추가한다.
- [x] 권리 확인, media type/size, generated route media-kind compatibility를 서버에서 검증한다.
- [x] Angular empty picker에서도 `내 파일 선택`과 권리 확인을 제공한다.
- [x] Nest Director 113개 중 111 pass/2 opt-in skip/fail 0, Angular 37/37, web API 관련 15/15와 세 build를 통과한다.
- [x] 기존 `shortform_prompt`를 수정하지 않는다.
- [x] 코드 저장소별 커밋과 origin push를 완료한다.
