# 원본 로컬 API 관리자 500 — 미적용 DB 마이그레이션 진단

2026-11-04 04:00 KST. 사용자가 원본 Admin4202에서 API3000의 `/admin/catalog`, `/admin/customer-refund-requests`, `/admin/release-console`, `/admin/payments/reconciliation` QueryFailedError/500을 보고했다. 원본 소스와 DB를 변경하지 않고 실제 서버 로그 및 DB 스키마·마이그레이션 이력을 읽기 전용으로 확인했다.

## 확인된 원인

최신 dev 소스와 별개로 원본 로컬 DB 스키마가 이전 상태다. API PID81330은 원본 `web/clipper_web_api`에서 실행 중이며 로그는 `/private/tmp/clipper-web-api-local-20261029.log`에 있다. 로그에서 개인정보·SQL 파라미터는 출력하지 않고 누락 테이블·컬럼 오류명만 추출했다.

- `catalog_plugin_settings` 없음 → 관리자 catalog 조회 오류와 일치.
- `customer_refund_requests`, `payment_refund_request_rate_limits` 없음 → 환불 요청 기능 오류와 일치.
- `release_runner_jobs.run_url` 없음 → release-console 오류와 일치.
- `payment_orders.last_cancellation_scanned_at`, `external_cancellation_effects` 없음 → 신규 결제 대사·취소 관련 처리 오류.
- `user_onboarding_jobs.claim_generation` 없음 → 가입 작업 처리 오류도 누적.

`/health`의 DbHealthService는 각 DB에 `SELECT 1`만 실행하므로 연결 성공은 확인하지만 최신 스키마나 기능 정상까지 검사하지 않는다. 앞서 연결·health 정상으로 보고한 결과를 기능 전체 정상으로 해석하면 안 된다.

## 실제 DB 이력

API는 기본 `.env`를 사용하며 로컬 localhost5433(admin),5434(release),5435(user) 대상이다. 이들을 guard한 뒤 PostgreSQL default_transaction_read_only=on으로 조회했다. 별도 worktree DB15438 및 `.env.local`의56433/56434/56435와 혼동하지 않았다. 인증값은 출력·기록하지 않았다.

| DB | 실행 완료 | 현재 코드에 등록 | 미적용 |
|---|---:|---:|---:|
| user5435 | 11 | 13 | 2 |
| admin5433 | 88 | 115 | 27 |
| release5434 | 3 | 5 | 2 |
| 합계 | 102 | 133 | 31 |

JSON에 정확한31개 pending migration 이름을 기록했다. 등록된 마이그레이션의 실제 객체와 DB migrations 이력을 대조했으며, 문제가 된 테이블·컬럼이 현재 information_schema/to_regclass 조회에서도 없는 것을 확인했다.

## 기존 데이터에 미치는 영향

pending migration은 단순 테이블 추가만이 아니다. 요금제·플러그인 권한·운영 정책·프로모션 구조 변경, 구형 가상계좌 지원 제거도 포함한다. 특히 RemoveVirtualAccountPayments는 가상계좌 관련 주문·이벤트·웹훅 데이터 삭제와 컬럼 제거를 포함하고 down에서 되돌릴 수 없다고 선언한다. UpdatePlanCatalogPrices도 가격·월 크레딧을 변경한다.

읽기 전용 영향 집계 시점에는 payment_orders0건, 가상계좌 삭제 후보0건, 입금 callback0건, 프로모션0건, 환불case0건, 기본미디어0건이었다. 기존 요금제4개가 있고, 가격 업데이트 대상 상품6개 모두 현재값이 새 가격과 다르다. 현재 금융 삭제 후보가0건이어도 스키마 및 설정값이 변경되는 작업임은 동일하다. 데이터 행이나 인증정보 자체는 기록하지 않았다.

## 필요한 후속 조치

원본 로컬3DB를 먼저 백업하고 대상DB를 재확인한 후 각 DataSource의 pending migration을 정식 순서로 적용해야 한다. 프로모션15438·564xx 등 다른DB나 개발·운영 서버는 대상이 아니다. DB 초기화/reset, synchronize, 임의 수동 CREATE로 우회하지 않는다. 적용 후 pending0·누락 스키마 해소·로그인한 관리자4개 조회 API와 API health를 다시 검증해야 한다.

이번 요청은 마이그레이션 필요 여부 진단이므로 마이그레이션·데이터 갱신·백업 생성·서버 재시작은 수행하지 않았다. source/shared .gitignore 및 원본4201/4202/3000은 그대로 유지했다. 이미 종료한4241/4242/4340도 다시 시작하지 않았다.
