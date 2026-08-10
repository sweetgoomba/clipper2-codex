# Toss Pay Review Checkout Worklog

## Changed repositories

- `.codex`: 설계, 구현 계획, 작업 추적 문서
- `web/clipper_web_api`: 결제 도메인·영속성·Toss adapter·공개 API·callback·migration·설정
- `web/clipper_web_client`: 요금 페이지 결제 CTA·공개 결과/취소 화면·API client
- `web/clipper_infra`: dev/stage/prod Compose 환경변수 전달

## Meaningful changes

- 토스페이 심사용 checkout 설계와 구현 계획을 확정했다.
- `.codex`, `clipper_web_api`, `clipper_web_client`, `clipper_infra`를 `feat/toss-pay-review-checkout` 브랜치로 분리했다.
- 심사 설정이 유효한 dev에서만 비로그인 단건·정기결제 버튼을 표시하고, 비활성 환경은 기존 무통장 구매 요청 동선을 유지한다.
- 1·3개월은 단건/정기, 12개월은 단건만 서버와 UI 양쪽에서 허용한다.
- 단건결제 callback과 빌링키 활성화/최초 결제를 Toss Pay 상태 조회로 재검증하고, `TEST` 결과만 저장한다.
- 주문·결제 이벤트를 admin DB에 저장하는 migration과 repository를 추가하고, 조회 토큰은 hash, 빌링키는 암호문으로만 저장한다.
- 공개 완료 페이지는 2초 간격 최대 10회만 조회한다. 취소 페이지는 provider reconcile을 먼저 수행하고 브라우저 도착만으로 취소 처리하지 않는다.
- 최초 빌링 청구를 transaction-scoped advisory lock과 조건부 상태 전이로 직렬화하고, 불확실한 응답은 동일 주문번호 상태 조회로 복구한다.
- Nginx reverse proxy 한 홉 신뢰와 IP별 checkout/result rate limit를 적용했다.
- capability를 `checkout | local_notice | legacy_purchase`로 확장했다. 로컬 요금 페이지는 dev와 동일한 Toss 버튼을 표시하지만 클릭 시 API를 호출하지 않고 dev 테스트 안내를 표시한다.

## Verification

- Client baseline: `npm test -- --watch=false --browsers=ChromeHeadless` — 66/66 PASS.
- API baseline: `npm test -- --runInBand` — 500/501 PASS, 기존 날짜 고정 session fixture 1건 FAIL.
- API 결제 집중 테스트: `npm test -- --runInBand src/modules/payments src/core/config/trust-proxy.spec.ts` — 75/75 PASS.
- API 전체 테스트: `npm test -- --runInBand` — 578/579 PASS. 유일한 실패는 기준선과 동일한 날짜 고정 session fixture다.
- Client 전체 테스트: `npm test -- --watch=false --browsers=ChromeHeadless` — 82/82 PASS.
- API build: `npm run build` — PASS.
- Client production build: `npm run build` — PASS.
- OpenAPI YAML parse: `OPENAPI_OK`.
- dev/stage/prod Compose config: 모두 PASS. review mode는 각각 `true/false/false`이고 실제 키 대신 placeholder만 렌더링됐다.
- 공용 테스트 키 실제 문자열 전체 저장소 검색: 0건. Client의 `TOSS_PAY_API_KEY`, `sk_test_`, `sk_live_` 검색: 0건.
- 네 저장소 `git diff --check`: PASS. 모두 `feat/toss-pay-review-checkout` 브랜치다.
- 독립 코드 리뷰: Critical 0, Important 0, merge 준비 가능 판정.
- 실행 중인 로컬 API `GET /payments/review/config`: HTTP 200, `{ "mode": "local_notice" }` 확인.
- 실행 중인 로컬 `/pricing`: HTTP 200 및 headless 렌더링에서 1·3개월 정기/단건, 12개월 단건 버튼과 로컬 안내 문구 확인.

## Remaining risks

- 실제 토스페이 공용 테스트 키 checkout·callback은 dev 배포 후 수동 스모크 테스트가 필요하다.
- 기준선 API 실패는 토스페이 범위 밖의 기존 테스트 픽스처 문제다.
- 이번 범위에서는 결제 완료 후 이용권·크레딧 지급, 회원 연결, 반복 청구, 해지, 환불을 의도적으로 연결하지 않았다.
- API가 Toss callback 재시도 기간 내내 중단되면 자동 scheduler가 없으므로 해당 주문은 수동 상태 재검증이 필요할 수 있다.

## Deployment handoff

- `implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md`에 m2-stage 수동 배포 순서를 작성했다.
- 이 배포는 m2-stage의 API와 web client만 recreate하고, m2-proxy는 변경하지 않으며, m2-db의 DB container를 재시작하지 않는다.
- admin migration은 Compose one-off API container로 `clipper_admin_dev`를 먼저 확인한 뒤 적용하도록 정리했다.
- 현재 로컬 작업 환경에서 사설망 m2-stage/m2-proxy/m2-db SSH는 timeout이었다. 공개 dev web/API/admin URL은 모두 HTTP 200이고 API health의 user/release/admin DB는 모두 `ok`였다.

## Recurring review retry follow-up

- 최초 정기결제는 `billing_key_created → billing_activated → billing_paid`와 `paid`까지 성공했다.
- 후속 세 건은 Toss 직접 상태 조회에서 `FAIL`, `CANCEL`, `CANCEL`이었지만 실패 callback이 없어 로컬 `checkout_ready`로 남는 현상을 확인했다.
- 공용 테스트 상점에서 동일 결제수단을 반복 등록할 수 있도록 각 주문의 `orderNo`를 Toss `displayId`로 생성·상태 조회·callback 검증에 전달한다.
- receipt-token 재검증에서 빌링키 `CREATE`, `ACTIVE`, `CANCEL`, `FAIL`, `REMOVE`를 조회하고, 주문·빌링키 일치 검증 후 로컬 주문과 deduplicated event에 반영한다.
- `ACTIVE` 재검증은 기존 advisory lock 기반 최초 청구 경로를 재사용한다. 크레딧·이용권 지급은 추가하지 않았다.
- API 결제 모듈 테스트: 86/86 PASS.
- API build: PASS.
- API 전체 테스트: 590/591 PASS. 유일한 실패는 별도 브랜치로 분리한 기존 운영자 JWT 고정 날짜 fixture다.
- 후속 배포는 API 이미지 빌드와 API container recreate만 필요하다. migration, web client, web admin, infra, proxy, DB restart는 필요하지 않다.
