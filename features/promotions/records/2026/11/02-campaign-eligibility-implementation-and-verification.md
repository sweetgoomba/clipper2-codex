# 캠페인 참여 가능 조건 · 실제 구현과 검증

2026-11-02 KST. 사용자 승인: 참여 대상3개와 추가 조건2개부터 구현. 앞선 실제 구현 보류 지시는 해제되었다. 후속 참고 후보 전체는 [별도 문서](02-campaign-eligibility-followup-candidates.md)에 보존했다.

## 실제 동작

- 관리자 기존 공통 drawer/Material 재사용. 상단 탭이나 별도 참여 시점 입력은 없다.
- 혜택 종류: 크레딧 지급 / 이용권 지급. 크레딧형은 지급량/유효일수를 한 줄 반반. 이용권형은 등급/개월, 별도 유효일수 입력 없음.
- 참여 대상: 회원가입하는 신규 회원만 / 기존 회원만 / 신규·기존 회원. audience=new/existing/all 단일 값.
- 추가 조건: 현재 활성 이용권 없음 / 과거 유료 이용권 결제·사용 이력 없음. eligibilityConditions=no_active_access/no_paid_history. 선택 조건 모두 충족(AND).
- 신규 전용이면 추가 조건을 해제·비활성화하고 계속 표시한다. 기존/전체로 바꾸면 빈 선택으로 활성화한다. 요약이 즉시 바뀐다.
- Free는 활성 이용권 검사 대상이 아니다. 활성 관리자 지급/프로모션/유료 이용권은 포함한다. 과거 관리자 지급 이력 자체/무료체험 이력/다른 캠페인 이력은 옵션에 없다.
- 일반 크레딧형은 별도 조건에 걸리지 않으면 활성 유료 이용권을 유지한 채 지급된다. 이용권형은 현재·예정 이용권/진행 중 첫 구독과의 구조적 중복을 계속 막는다.
- 서버가 실제 가입 흐름에서만 신규로 판정한다. 일반 회원 HTTP 요청에서 신규 여부를 지정할 수 없다. DB user행이 존재한다는 이유로 가입 처리 중 회원을 기존 회원으로 오판하지 않는다.
- 이용권형 최초·매월 크레딧은 일반 유료와 동일한 월별 기념일에 만료되며 최종 지급 기간은 이용권 종료를 넘지 않는다. 프로모션만 별도 유효일수를 더하던 분기를 제거했다.
- 가입/가입 후 공통 지급 helper와 공통 크레딧 grant/원장 writer를 재사용한다. signup-promotion:user 멱등 증명 키와 user-job/admin 트랜잭션 복구는 유지했다.
- 캠페인1회/코드별 상한/삭제·수정 잠금/회수/참여 조회는 보존한다. 레퍼럴 결제 성과·유료 예약·XLSX는 재도입하지 않았다.
- 회원 웹 확인 모달에서 크레딧형이라는 이유만으로 가입 전용으로 차단하던 처리를 제거했다. 서버 거절 사유에 따라 안내하며 크레딧형 참여 내역은 ‘1회 지급’으로 표시한다.

## 마이그레이션·기존 기록

1793577800000 CampaignParticipationConditions를 추가했다. 기존 signup_credits는 credits+new로, 기존 paid 제외는 no_paid_history로 변환한다. 관리자 과거 이력 제외 옵션은 제거한다. 이용권형 campaign creditValidityDays는 null, 크레딧형은 양수다. 신규 전용+추가 조건의 중복 설정은 서버와 DB에서 거부한다.

**재량 결정:** 이미 지급한 크레딧/사용/결제/원장과 약속된 만료일은 소급 수정하지 않는다. 새 최초 지급과 향후 월별 지급은 새 만료 규칙이다. 이 결정은 과거 지급분의 이용 기한을 사후 변경하지 않기 위한 것이며, 따라서 이미 지급된 구형 크레딧은 원래 만료일이 남는다.

개발단계 호환 예외를 실행 코드에 추가하지 않았다. 과거 저장값 변환은 버전 관리된 migration으로만 처리한다. 표현할 수 없는 신규 참여 조건이 있는 상태에서 rollback하면 조건을 유실하지 않도록 거부한다.

## 독립 검토 및 수정

fresh Astra xhigh read-only review: Critical0 / Important2 / Minor0. 두 Important는 재현 후 한 수정 단계에서 해결했다.

1. 가입 대기 중 운영자가 이용권을 지급하면 signup 지급의 하드코딩된 false 검사로 조건을 통과하던 문제: 실제 user lock과 transaction-bound repo로 현재/예정 이용권 및 pending subscription을 재검사한다. 멱등 지급 확인은 먼저 유지한다. 단위 RED→GREEN과 실제 DB pending-signup/admin-pass 테스트 통과.
2. 신규 전용 이용권 캠페인을 구형 schema로 rollback할 때 audience가 없어지는 문제: 반대 변환 불가 조합을 거부한다. 실제 PostgreSQL에서 특정 fixture만 확인하는 RED→GREEN 테스트 통과.

추가 자체 검증: 자동 월별 만료의 null을 운영 기록에서 ‘제한 없음’으로 설명하면 의미가 잘못되므로 ‘월별 이용 기간’으로 표시하도록 재현 테스트와 함께 수정했다. 최종 관리자 전체2,705개 및 build 통과.

검토에서 제외한 이전 W19 레퍼럴/예약 제거 및 무관한 catalog/plugin 변경은 앞선 구현 범위이며 이번 후속 검토에 재편입하지 않았다.

## 검증 증거

- API 전체:470 suites 통과,11 skip /5,100 tests 통과,91 skip. skip에는 별도 opt-in 실제 DB 시험21개가 포함되며 아래에서 따로 실행했다. build 통과.
- 회원 웹 전체591개 통과, build 통과.
- 관리자 전체2,705개 통과, build 및 색상 직접값0 확인.
- 일회용 PostgreSQL16/15439: signup-benefits.integration21개 통과. 신규 가입 원자성/멱등·복구·응답 유실·pool1 동시성·코드별 마지막자리 경합, 일반 크레딧/기존 유료 이용권 보존/회수, 기존 전용 signup 거절, 가입 이용권과 월별 만료, 조건 유실 rollback 거절, pending signup/admin grant 경합을 포함한다.
- 월말/윤년/최종 짧은 기간 expiry3개 단위 시험 통과.
- 세 저장소 git diff --check 통과, OpenAPI YAML parse/audience schema 확인.
- 브라우저 실제4242: drawer/라디오3개/조건2개, 체크 후 신규 전용으로 전환 시 visible/disabled=true·checked=false, 기존 전용 복귀 후 재선택/요약, credits 두 input 같은y/너비198.78·198.80px, access의 유효일수 input0개 확인. 화면 에러 로그 없음. 실제 사용자 DB에 테스트 캠페인을 저장하지 않았다.
- 실제4241 홈의 새 bundle/API catalog 렌더 확인. 실제 Google 신규 계정 생성이나 Toss 청구는 이 후속에서 수행하지 않았다.

전체/RED/GREEN 로그는 /tmp/promotion-api-full.log, promotion-api-target.log, promotion-integration.log, promotion-review-fix-red.log, promotion-review-fix-green.log, promotion-rollback-red.log, promotion-admin-full.log, promotion-client-full.log에 있다. 기존 번들 크기 경고(Admin 약880kB/Client508.94kB)와 기존 transaction 내 병렬 쿼리의 pg9 deprecation 경고가 있다. 테스트 실패로 숨기지 않으며 이번 범위와 무관한 전역 성능 변경은 하지 않았다.

## 로컬 반영

작업 브랜치 feat/signup-credit-promotion-free-20261102의 API/Admin/Client 후속 수정. 기존 다른 작업과 미커밋 W19 변경을 유지했다. stage/commit/push/merge/공유 dev 배포 없음.

사용자 테스트 DB15438의 clipper_promo_admin을 private runtime/backups/admin-before-participation-conditions.dump로 백업한 뒤 새 migration1개만 적용했다. DB 초기화 없음. API4340만 재시작(PID55613), 웹4241/4242의 Python60587은 중단 없이 번들만 갱신. API health 세 DB 모두ok. 기존API3000/관리자4202/독립 로컬 앱66870·67050 실행 유지. 검증 전용 QA15439 컨테이너는 검증 후 제거했고 사용자 DB15438은 유지했다.

[실제 관리자 화면](http://localhost:4242/promotions) · [크레딧형 구현 화면](02-campaign-eligibility-implemented.jpg) · [이용권형 구현 화면](02-campaign-access-benefit-implemented.jpg).

## 후속 스타일 보정

[목업 정합·라디오 포커스·가입 코드 label 보정](02-campaign-eligibility-style-corrections.md)에서 실제 화면 검증과 후속 수정 내용을 확인할 수 있다.
