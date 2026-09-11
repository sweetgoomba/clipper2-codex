# 결제 전 안내 보완 구현 계획

승인: 대화의 최초구독/즉시변경/예약변경/카드변경/갱신재개/추가충전 및 재진입 경로 설명안.

목표: 지금 청구액과 이후 자동결제 조건을 버튼 직전에 표시하고, 구독 관련 조건에는 명시적 동의를 받는다. 차액 계산 정책·청구 로직은 변경하지 않는다.

- [x] API CheckoutSession에 선택적 subscriptionTerms {billingIntervalMonths, priceKrw, autoRenews:true} 추가. billing_auth 재진입은 주문 snapshot만 사용하며 누락/잘못된 값은 세션 발급 실패. OpenAPI 및 서비스 테스트 함께 수정. normal_payment에는 생략.
- [x] Customer 모델 동일 확장. 최초구독은 reviewTerms 또는 subscriptionTerms 기반 금액/주기/자동갱신 동의문 제공. billing 조건 부재는 결제 진행 차단. 추가충전은 1회결제/자동갱신 없음 안내.
- [x] ConfirmDialog에 선택적 consentText/동의 gate, notices, 펼침 계산 내역 추가. 다른 확인창은 기존 동작 유지. 체크 전후 버튼 상태 및 상세 펼침 테스트.
- [x] Dashboard 차액 화면: 새상품가격-기존구독공제=즉시청구, 두 잔존가치 산식·선택이유, 새기간/크레딧교체 안내. 즉시/예약 변경 모두 다음 결제조건 동의. 카드변경 및 갱신재개도 금액/주기/시점 안내와 동의.
- [x] 대상 테스트 실패 확인 후 구현, 전체 Customer/API 테스트 및 양쪽 빌드, 로컬 시각 확인, 최종 diff 검토.
- [x] WORKLOG/TASKS 갱신. 커밋·푸시·운영배포는 이번 구현 요청에서 실행하지 않는다. 개발서버/개발DB/운영DB 초기화/라이브키 전환 없음.

실행: API와 Customer는 파일 소유를 분리해 병렬 진행하고 API 인터페이스는 위 형태로 고정한다. 서버/DB 실행은 사용자가 직접 수행한다. UI 동의는 표시와 클릭 gate이며 새로운 동의 이력 저장 API를 임의로 추가하지 않는다.
