# 구독 중간 업그레이드 차액의 빌링 MID 청구 — 공식 근거 확인

확인일: 2026-11-02 KST. 사용자는 정기결제일 외 업그레이드 차액을 자동결제용 MID/기존 빌링키로 청구하는 현재 방식의 정책상 타당성과 타 서비스 사례를 요청했다. 제품 코드·환경·결제 데이터는 변경하지 않았다.

## 결론과 범위

토스의 공개 서비스 설명은 빌링으로 원하는 시점에 등록 결제수단을 청구하고 반복 결제 또는 한 번의 결제를 수행할 수 있다고 명시한다. 개발 가이드는 구독의 청구 금액·주기와 스케줄링을 가맹점 서버가 관리하도록 안내한다. 이를 기존 구독에 연결된 업그레이드 추가 청구와 대조하면, 해당 구독의 빌링키와 자동결제용 MID를 사용하는 현재 설계는 공개 설명에 부합한다고 판단한다.

‘요금제 업그레이드 차액’이라는 특정 사례를 그대로 적은 토스의 공개 문구나, 클리퍼 해당 MID의 개별 서면 허가를 확보한 것은 아니다. 공개 일반 설명으로부터의 설계 판단과 개별 계약의 확정은 구분한다. 확인한 작업 문서에서 해당 MID별 추가 특약·토스 승인 회신 원본은 찾지 못했다. 토스 개발 가이드에 있는 정기 구독형 서비스·리스크 검토·추가 계약 조건은 그대로 전제한다. 일반결제용 MID로 바꿔야 한다는 공개 규정은 확인하지 못했다.

## 토스 공식 근거

1. [PG 서비스 소개](https://www.tosspayments.com/services)의 ‘빌링(자동결제)’: 원하는 때 등록 수단으로 자동결제하며, ‘주기에 따라 반복해서 결제할 수도, 한 번만 결제할 수도 있습니다.’라고 명시한다. 정기결제일에만 호출 가능한 API라는 해석의 근거는 없다.
2. [자동결제 이해하기](https://docs.tosspayments.com/guides/v2/billing): 구독 금액 변경은 amount 변경, 주기 변경은 API 호출 주기 변경으로 처리한다. 스케줄링은 상점이 구현한다. 동시에 정기 구독형 서비스가 아니라면 정책적으로 제한되며 리스크 검토·추가 계약이 필요하다고 안내한다.
3. [자동결제 API](https://docs.tosspayments.com/reference#자동결제-승인): 발급된 빌링키로 POST /v1/billing/{billingKey}를 호출하고 amount에 청구 금액을 전달한다. API 호출 가능성만으로 개별 계약 허가를 주장하지 않는다.

## 다른 서비스·결제 플랫폼의 공식 사례

- [Notion](https://www.notion.com/help/billing): 결제기간 중 업그레이드하면 남은 기존 기간분을 공제하고 즉시 청구하며 새 기간을 시작한다.
- [GitHub](https://docs.github.com/en/billing/concepts/impact-of-plan-changes): 업그레이드와 유료 좌석 추가는 일할 정산하여 즉시 청구하고 즉시 적용한다.
- [Stripe](https://docs.stripe.com/api/subscriptions/update): always_invoice로 업그레이드 정산 금액을 즉시 청구하고 수납을 시도할 수 있다.
- [Paddle 정산](https://developer.paddle.com/concepts/subscriptions/proration/): prorated_immediately로 구독 중간 정산분을 즉시 청구한다. [저장 결제수단 안내](https://developer.paddle.com/build/checkout/saved-payment-methods/)는 구독에 저장한 결제수단이 갱신·업그레이드·다운그레이드 및 구독 관련 청구에 쓰인다고 명시한다.

이들은 ‘기존 구독의 등록 결제수단으로 중간 변경 금액을 청구’하는 방식의 사례다. 해외 서비스가 토스 bill_ MID를 사용한다는 증거로 해석하지 않는다. 국내 개발사 JenaLab의 토스 빌링키 사례도 조사했지만, 본문은 일할 차액 대신 새 요금제 전액을 청구한다고 설명하므로 정확히 동일한 차액 계산 사례로 인용하지 않았다. 검색 요약의 ‘차액’ 문구만으로 같은 구현이라고 단정하지 않는다.

## 현재 클리퍼 구현 대조

작업 폴더: .worktrees/signup-promotion-plugin-access-20261028, 브랜치 feat/signup-credit-promotion-free-20261102.

- SubscriptionPlanChangesService.settle: 해당 구독의 빌링키를 읽어 chargeBillingKey에 계산된 order.amountKrw를 전달한다.
- HttpTossPaymentsProvider.chargeBillingKey: keySet=billing, TOSS_PAYMENTS_BILLING_SECRET_KEY, POST /v1/billing/{billingKey}를 사용한다. MID 문자열 접두어만으로 경로를 고르지 않는다.
- 일반 추가 크레딧 결제는 별도의 ONE_TIME 키와 /v1/payments/confirm 경로다.
- 회원 확인창에서 즉시 청구액·새 이용기간·이후 정기결제 조건을 보여주고 필수 동의 체크 후 ‘결제하고 변경’을 누른다. client dashboard.component.ts:583–612와 shared confirm-dialog.component.html:33–46에서 확인했다.
- 청구 성공을 확인한 뒤 이용권·크레딧 변경을 처리한다. 이번 조사로 MID 선택을 변경할 이유는 발견하지 못했다.

이번 작업은 공개 정책·계약 범위와 코드 경로 조사다. 토스에 문의 메시지를 보내거나 추가 결제를 실행하지 않았다. 직전 구현 대조에서 provider/plan-change/topup 243개 테스트는 통과했으나, 이는 결제사의 개별 계약 승인 증거와는 별개다.
