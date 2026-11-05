# 종료일 미정 캠페인 · 구현과 검증

**후속 정정:** 이 기록 당시의 ‘등록 이력 후 종료일 단축 금지’는 [최신 정책](02-campaign-deadline-and-summary-colors.md)으로 대체됐다. 현재는 시작일 이후 범위에서 단축/연장/미정 전환을 허용하며 지급 혜택은 유지한다.

2026-11-02 KST. 사용자가 종료일 미정 캠페인을 요청했다. 격리 작업 브랜치 `feat/signup-credit-promotion-free-20261102`에서 API·관리자와 회원 웹의 미리보기 계약 타입을 수정했다. 기존 W19 변경은 보존했다. 커밋·푸시·병합 없음.

## 동작과 계약

- 관리자 추가·수정의 종료일은 선택값이다. 빈 칸은 API `endsAt: null`, DB `ends_at: null`로 저장하며 목록·상세·운영 기록에는 ‘종료일 미정’으로 표시한다. 수정 시 빈 값으로 불러온다.
- 종료일이 없으면 날짜에 따른 자동 종료가 없다. 시작일 이후 캠페인/코드 활성 상태, 참여 대상·추가 조건, 코드별 상한, 캠페인당 회원1회 등 기존 검사를 통과하면 등록할 수 있다. 운영자 비활성화로 신규 등록을 차단하며 재활성화도 가능하다.
- 날짜가 있는 캠페인의 종료 판정과 종료 후 재활성화 금지는 유지한다. 등록 이력이 생긴 후 시작일/혜택 잠금, 정해진 종료일의 단축 금지도 유지한다. 날짜→미정은 허용하고 미정→새 날짜는 처음 기한을 설정하는 것으로 처리한다.
- API 입력은 날짜 문자열 또는 명시적 null이다. 필드 누락/유효하지 않은 날짜는 계속 거절한다. 캠페인/코드 미리보기 `endsAt`만 nullable이며 회원의 실제 혜택 만료일은 계속 날짜다.
- 크레딧 지급량/유효기간과 이용권 기간은 별개다. 크레딧형은 지급 당시 설정한 자체 유효기간, 이용권형은 기존 월별 이용 기간 만료를 그대로 사용한다. 이미 지급한 혜택/기록/크레딧 만료를 바꾸지 않는다.
- 종료일 미정인 활성 이용권형 캠페인도 지급 등급 비활성화 방지 검사에 포함한다.

## 구현 지점

API: OpenAPI, DTO/controller의 null 변환, 도메인/저장소 계약, 정책 판정과 변경/활성화 guard, TypeORM 변환·활성화 SQL, 이용권 등급 비활성화 guard를 함께 수정했다. `new Date(null)`이 1970년으로 변환되는 문제를 피하도록 명시적으로 null을 보존한다.

신규 `AllowOpenEndedPromotionCampaigns1793577900000`은 `promotion_campaigns.ends_at` NOT NULL만 해제한다. 기존 날짜·조건·혜택 데이터는 보존한다. rollback은 null 데이터가 있으면 DB 제약으로 중단하며 임의 날짜로 덮어쓰지 않는다.

관리자는 기존 공통 Material 입력·drawer를 유지하고 ‘종료일 (선택)’, ‘비우면 종료일 없이 운영합니다.’를 표시한다. 무기한 날짜를 가짜 미래 날짜로 대체하지 않는다. 회원 웹은 nullable 미리보기 계약만 맞추었다.

## 검증

실패 테스트로 기존 null의 만료 오판/1970년 변환/DTO 거절/관리자 저장 실패를 먼저 확인한 뒤 통과시켰다.

| 검증 | 결과 |
| --- | --- |
| API 관련 단위4 suites | 69 통과 |
| 관리자 프로모션 화면 | 51 통과 |
| 일회용 실제 PostgreSQL16 통합 | 23 통과 |
| API 전체 `npm test -- --runInBand` | 470 suites/5,106 통과, 11 suites/93 tests skip |
| 관리자 전체 | 2,707 통과 |
| 회원 웹 전체 | 591 통과 |
| API/Admin/Client build | 모두 통과 |
| 관리자 `check:colors` | 직접 색상0 |
| 세 repo `git diff --check` | 통과 |
| OpenAPI YAML parse | nullable3개 캠페인 schema 확인 |

실제 DB 시험은 `SIGNUP_INTEGRATION_DB_PORT=15439`로 별도 opt-in 실행했다. 무기한 캠페인의 저장/2099년 만료 sweep 제외/가입 혜택200과 자체30일 만료/기존 가입400 합산600/운영자 중지 후 지급 차단/기존 지급 보존/재활성화 등록을 확인했다. 활성 무기한 캠페인에서 지급 등급 비활성화 거절도 확인했다.

최초 전체 API 실행에서 SQL 기대문구1개와 무관한 환불 HTTP 테스트의 일시적401이 있었다. 기대문구는 새 SQL에 맞게 수정했고 환불 코드 변경 없이 관련30개와 최종 전체5,106개 재실행이 통과했다. 초기 실패를 최종 통과와 구분한다. 기존 Admin 약880kB/Client508.94kB 번들 예산 경고와 기존 pg9 병렬쿼리 deprecation은 남아 있다.

로그: `/tmp/open-ended-api-red.log`, `open-ended-controller-red.log`, `open-ended-admin-red.log`, `open-ended-api-green.log`, `open-ended-admin-green.log`, `open-ended-integration.log`, `open-ended-api-full-final.log`, `open-ended-admin-full.log`, `open-ended-client-full.log`, 각 `open-ended-*-build.log`.

## 로컬 반영과 데이터 보존

사용자 테스트 DB15438의 `clipper_promo_admin`을 runtime의 `backups/admin-before-open-ended-campaign.dump`(권한600)로 백업한 뒤 신규 migration1개만 적용했다. `ends_at` nullable=YES 및 migration 이력을 확인했다. 초기화하지 않았다. 적용 후 캠페인/코드/등록/크레딧은 각각0건으로 기존 상태를 보존했다.

API4340만 새 빌드로 재시작(PID64548), `/health` 세 DB 모두ok. 웹4241/4242 PID60587은 중단 없이 번들만 갱신했고 로컬 사본에서만 API4340 주소로 치환했다. 다른 작업 서버/API3000/Admin4202/DB/앱은 변경하지 않았다. 사용자 테스트 런타임과 DB15438은 계속 유지한다. 이번 검증 전용 `clipper-open-ended-qa-20261102`(15439)만 정리했다.

실제 관리자4242의 캠페인 추가 drawer에서 종료일 입력 value=''/required=false와 크레딧 유효기간30일 독립 입력을 확인했다. 사용자 DB에 확인용 캠페인을 추가하지 않았다. 저장·재활성화·크레딧 보존은 위 실제 DB 통합으로 검증했다.

[확인 화면](02-open-ended-campaign-admin.png) · [계획](02-open-ended-campaign-plan.md).

## 양방향 수정 추가 확인

[종료일 미정↔날짜 지정 회귀 검증](02-open-ended-campaign-edit-regression-check.md): 참여 이력 유무·혜택 종류별 실제 DB8조합과 비활성/종료 후2상황, 관리자4조합을 추가했다. 실제DB33·화면55 통과. 제품 수정 없이 테스트만 보강했고 기존 지급/만료와 실행 환경을 보존했다.
