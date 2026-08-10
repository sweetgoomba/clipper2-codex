# Toss Pay Review Checkout Tasks

설계: `../design/2026-08-10-toss-pay-review-checkout-design.md`
계획: `../design/2026-08-10-toss-pay-review-checkout-implementation-plan.md`
브랜치: `feat/toss-pay-review-checkout`

- [x] Contract and active-plan boundary
- [x] Payment persistence
- [x] Toss Pay provider adapter
- [x] Checkout application flow
- [x] Callback and first billing charge
- [x] HTTP/module wiring
- [x] Pricing checkout UI
- [x] Public payment result UI
- [x] Infra env wiring
- [x] Full local verification
- [x] Local Toss button notice mode
- [ ] Dev deployment and smoke test

비범위: 이용권·크레딧 지급, 반복 청구, 해지, 환불, 운영 키 전환.

## 기준선 예외

- 2026-08-10 구현 전 API 전체 테스트: 500/501 통과.
- 기존 `operator-jwt.strategy.spec.ts` 픽스처의 `expiresAt=2026-08-09` 이 현재 날짜보다 과거라 1건 실패.
- 사용자 승인에 따라 해당 비관련 실패는 별도 기록하고 토스페이 범위를 계속한다.
