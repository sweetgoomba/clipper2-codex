# TossPayments BILLING_DELETED 정확 상태 통합 검증

검증일: 2026-09-02

## 범위

- `billing_key_issued` 상태의 후보 빌링키와 정확히 일치하는 `BILLING_DELETED`
- 새 빌링키 설치 후 삭제에 실패해 남아 있는 이전 빌링키와 정확히 일치하는 `BILLING_DELETED`

실제 PostgreSQL repository와 application service를 사용하고, 빌링키 발급·삭제 결과만 제어 가능한 fake Toss provider로 대체했다. 일회용 DB 55433·55434·55435만 사용했으며 ngrok, Toss 키, 실제 provider 호출, 기존 DB write는 사용하지 않았다.

## 확인 결과

- 후보 키 삭제: 변경 시도는 `failed`와 `WEBHOOK_CANDIDATE_BILLING_KEY_DELETED`로 종료되고 후보 키 암호문·fingerprint가 제거됨
- 후보 키 삭제: 기존 구독에 설치된 빌링키와 활성 상태는 유지됨
- 이전 키 삭제: 남아 있던 이전 키 암호문·fingerprint가 제거되고 cleanup이 `succeeded`로 변경됨
- 이전 키 삭제: 교체된 현재 빌링키와 구독 활성 상태는 유지됨
- 두 웹훅 모두 durable inbox에서 `processed`, 오류 없음, 원문 빌링키 비저장 상태로 종료됨

## 자동 검증

- 새 통합 테스트 반복 실행: 2/2 통과
- 전체 E2E: 5 suites, 39 tests 통과
- 전체 단위 테스트: 185 suites, 1,790 tests 통과
- API production build: 통과
- 새 테스트 파일 ESLint·Prettier: 통과

## 변경 범위

- 운영 코드·DB schema·migration 변경 없음
- 통합 테스트와 검증 체크리스트만 변경

## 남은 Phase 5 항목

- user-MID `PAYMENT_STATUS_CHANGED` 웹훅 및 중복 전달 검증
- user-MID `DEPOSIT_CALLBACK` 웹훅 및 중복 전달 검증
- 가상계좌 발급 후 입금 전 상태 검증
- 가상계좌 입금 후 지급 검증
- 미입금 가상계좌 만료 검증

위 항목은 이번 작업 범위에 포함하지 않았다.
