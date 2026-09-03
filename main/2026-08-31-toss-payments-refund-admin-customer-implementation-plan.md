# 환불 관리자·고객 화면 구현 계획

- 작성일: 2026-08-31
- 상태: 구현 전 상세 계획
- 선행 조건: 환불 Web API와 OpenAPI 계약 완료
- 대상: Admin web, Customer web, Web API 계약 보정

> 실제 실행 전 사용자의 구현 승인이 필요하다. 승인 후 `superpowers:executing-plans`와 테스트 우선 방식으로 수행한다. 고객용 환불 신청 기능이나 환불금액 자동 계산 기능은 만들지 않는다.

## Goal

- 담당자가 회원·결제·크레딧 근거를 한 화면에서 확인한다.
- 최고 관리자가 결제별 환불금액과 사유를 입력하고 두 번 확인한 뒤 실행한다.
- 처리 중·일부 완료·확인 필요·내부 재처리 필요 상태를 한 환불 건으로 추적한다.
- 회원 상세와 전체 환불 탭이 같은 Web API와 같은 상세 컴포넌트를 사용한다.
- 고객은 결제내역·구독·크레딧에서 결과만 이해할 수 있게 확인한다.

## 화면 구조

```text
회원 목록
  -> 회원 상세
       ├─ 계정 기본정보
       ├─ 정기구독
       ├─ 크레딧 지급 건
       ├─ 결제
       └─ 환불 내역 / 환불 처리 진입

결제 운영
  ├─ 결제 주문
  ├─ 웹훅
  ├─ 재확인 필요
  └─ 환불
       -> 환불 건 상세/재처리
```

환불 처리 form은 `refund-workbench`로 한 번만 구현한다. 회원 상세에서는 해당 회원을 고정해 열고, 전체 환불 탭에서는 검색 결과에서 연다.

## Task 1 — Admin API 타입과 client를 OpenAPI에 맞춰 고정

**Files**

- Modify: `clipper_web_admin/src/app/core/api/models.ts`
- Create: `clipper_web_admin/src/app/core/api/payment-refunds-api.service.ts`
- Create: `clipper_web_admin/src/app/core/api/payment-refunds-api.service.spec.ts`
- Modify: `clipper_web_admin/src/app/core/api/members-api.service.ts`
- Modify: `clipper_web_admin/src/app/core/api/members-api.service.spec.ts`

- [ ] HTTP service 실패 테스트를 먼저 작성한다.
- [ ] Admin 모델을 backend OpenAPI에서 사용한 stable code와 동일하게 정의한다.

필수 모델:

```ts
interface AdminRefundOption;
interface AdminRefundPreview;
interface CreateRefundRequest;
interface AdminRefundCaseSummary;
interface AdminRefundCaseDetail;
interface AdminRefundItem;
interface AdminRefundAttempt;
interface AdminRefundInternalEvent;
interface AdminMemberSubscription;
interface AdminMemberPayment;
interface AdminMemberCreditGrant;
```

- [ ] API service에 다음 호출을 구현한다.

- 회원별 환불 대상 조회
- 환불 미리보기
- 환불 생성·실행 요청
- 목록·상세
- 재시도·재조회
- 토스 관리자 사이트 수동 취소 검증
- 내부 처리 재시도
- 토스 취소가 하나도 성공하지 않은 건 종료
- 연결되지 않은 외부 취소 연결

- [ ] URL segment는 `encodeURIComponent`, 금액은 number 안전 정수, secret/paymentKey 원문은 모델에 두지 않는다.
- [ ] 일반 운영자 read와 최고 관리자 mutation이 다른 HTTP method임을 테스트에서 명확히 한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration
npm test -- --watch=false --include='src/app/core/api/payment-refunds-api.service.spec.ts' --include='src/app/core/api/members-api.service.spec.ts'
```

Review checkpoint: OpenAPI field와 Angular 모델을 1:1 대조한다.

## Task 2 — 회원 목록을 정기구독·결제 운영 관점으로 변경

**Files**

- Modify: `clipper_web_admin/src/app/features/portal/members/members.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/members/members.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/members/members.component.scss`
- Modify: `clipper_web_admin/src/app/features/portal/members/members.component.spec.ts`

- [ ] 다음 column과 상태를 먼저 테스트로 작성한다.

| 열 | 표시 내용 |
|---|---|
| 이메일 | 계정 이메일 |
| 이름 | Google 계정 프로필 이름 |
| 요금제 | 현재 정기구독 요금제 또는 없음 |
| 구독 상태 | 활성, 다음 결제 취소, 갱신 실패, 종료 등 |
| 현재 구독 월 종료 | 연간 전체 종료일이 아니라 현재 혜택 월 경계 |
| 다음 결제 | 예정일 또는 중단됨 |
| 크레딧 | 현재 사용 가능한 전체 크레딧 |
| 문제 | 결제 확인·환불 처리·내부 재처리 필요 |

- [ ] 기존 “만료일” label과 expiry sort를 “현재 구독 월 종료” 의미로 바꾼다. 구독이 없는 회원은 `—`로 표시한다.
- [ ] 기존 이용권 상태 filter를 `전체`, `현재 구독 중`, `다음 결제 취소`, `결제 실패·중단`, `종료·구독 없음`, `결제·환불 확인 필요`로 교체하고 server query parameter와 맞춘다.
- [ ] 이름 열은 유지한다.
- [ ] 행 클릭으로 기존 회원 상세 route를 사용한다.
- [ ] 상태 color만으로 의미를 전달하지 않고 text/aria label을 함께 둔다.

```bash
npm test -- --watch=false --include='src/app/features/portal/members/members.component.spec.ts'
```

Review checkpoint: 월간, 연간, 다음 결제 취소, 구독 없음 fixture를 한 표에서 확인한다.

## Task 3 — 회원 상세를 5개 section으로 재구성

**Files**

- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.scss`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Modify: `clipper_web_admin/src/app/core/api/members-api.service.ts`

- [ ] 실패 테스트로 다음 section을 고정한다.

1. 계정: 이메일, 이름, 가입일
2. 정기구독: 요금제, 월간/연간, 상태, 현재 구독 월, 다음 결제, 예약 변경, 환불 상태
3. 크레딧 지급 건: 출처, 최초량, 사용량, 잔량, 충전·만료, 상태, 연결 결제
4. 결제: 최초·갱신·상향·추가 구매, 원금, 누적 환불, 잔액, 토스 상태, 일시, 영수증
5. 환불: 환불 건 상태와 상세 진입

- [ ] 기존 `기간 수동 연장`, `크레딧 조정`, `정지(미구현)` 영역은 환불과 합치지 않는다.
- [ ] 현재 user model에 실제 계정 상태가 없으므로 “정상” 같은 고정값을 만들어 표시하지 않는다. 계정 정지 기능은 별도 설계·구현 범위로 남긴다.
- [ ] 동작하지 않는 `정지(미구현)` 버튼은 환불 버튼으로 재활용하지 않는다. 숨길지 유지할지는 기존 범위대로 두고 환불 진입은 별도 명확한 버튼으로 추가한다.
- [ ] 관리자 수동 크레딧 조정과 환불 크레딧 회수의 이력을 다른 용어로 표시한다.
- [ ] 환불 잠금 지급 건은 “환불 처리 중”, 회수 완료는 “환불 회수”, 만료는 “만료”로 구분한다.
- [ ] 영수증 URL은 기존 안전한 host 검사 원칙을 유지한다.

```bash
npm test -- --watch=false --include='src/app/features/portal/members/detail/member-detail.component.spec.ts'
```

Review checkpoint: 같은 회원의 무료 체험·정기구독·추가 구매 지급 건이 섞이지 않고 보이는지 확인한다.

## Task 4 — 재사용 가능한 환불 처리 workbench 구현

**Files**

- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/refund-workbench.component.ts`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/refund-workbench.component.html`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/refund-workbench.component.scss`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/refund-workbench.component.spec.ts`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.ts`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.html`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.scss`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.spec.ts`

- [ ] component 실패 테스트를 먼저 작성한다.
- [ ] workbench를 다음 단계로 구성한다.

1. 환불 대상 종류 선택: 월간 구독, 연간 구독, 추가 구매 크레딧
2. 서버 미리보기 조회
3. 자격 근거·차단 이유, 관련 결제, 연결 크레딧 사용량 표시
4. 결제별 환불금액과 토스 취소 사유 입력
5. 선택적 내부 메모
6. 최종 확인 dialog
7. 환불 생성 후 상세 상태로 이동

- [ ] 월간 구독과 추가 구매 크레딧은 전액만 가능하므로 금액 input을 자유 편집할 수 없게 한다.
- [ ] 연간 구독은 결제별 금액 input을 허용하되 다음 client validation만 한다: 정수, 1원 이상, 서버가 준 취소 가능 잔액 이하. 실제 허용 여부는 제출 때 서버가 다시 검증한다.
- [ ] 기본 결제와 상향 차액 결제를 하나의 환불 건 안에서 그룹으로 보여준다. “차액만 환불” 일반 동작은 제공하지 않는다.
- [ ] 미리보기 뒤 사용량이나 토스 상태가 바뀐 409 응답은 금액을 자동 보정하지 않고 최신 미리보기 재조회 안내를 한다.
- [ ] 최종 확인창에 사용자, 상품, 결제별 원금·환불금액, 합계, 종료 시각, 잠금/회수 크레딧, 유지 크레딧, 다음 결제 중단, 되돌릴 수 없음 안내를 표시한다.
- [ ] 최고 관리자가 아닌 경우 상세은 볼 수 있어도 실행 form과 재처리 버튼은 표시하지 않는다. 서버 권한 검사가 최종 방어다.

```bash
npm test -- --watch=false --include='src/app/features/portal/refunds/refund-workbench/refund-workbench.component.spec.ts' --include='src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.spec.ts'
```

Review checkpoint: 월간 전액, 연간 부분, 추가 구매 전액 fixture의 입력 가능 범위를 확인한다.

## Task 5 — 회원 상세에 환불 진입과 상태 추적 연결

**Files**

- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.scss`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Reuse: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/**`

- [ ] 회원 ID를 고정한 workbench가 해당 회원의 결제만 표시하는 테스트를 작성한다.
- [ ] 환불 처리 버튼은 환불 후보가 없을 때 disabled가 아니라 이유가 보이게 한다.
- [ ] 환불 생성 뒤 회원 상세 데이터를 다시 불러와 지급 건 잠금, 다음 결제 중단, 환불 상태를 즉시 표시한다.
- [ ] 브라우저를 닫았다 다시 들어와도 server case를 조회해 processing 상태를 이어서 보여준다.
- [ ] 같은 회원의 처리 중 환불이 있으면 중복 생성 대신 기존 상세로 유도한다.

```bash
npm test -- --watch=false --include='src/app/features/portal/members/detail/member-detail.component.spec.ts'
```

Review checkpoint: 환불 시작 전후 회원 상세 diff를 확인한다.

## Task 6 — 결제 운영 화면에 전체 환불 탭과 상세 추가

**Files**

- Modify: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.scss`
- Modify: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.spec.ts`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.ts`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.html`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.scss`
- Create: `clipper_web_admin/src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.spec.ts`

- [ ] `OperationsTab`에 `refunds`를 추가하는 실패 테스트를 작성한다.
- [ ] 상세 route는 `payment-operations/refunds/:refundCaseId`로 추가하고 `adminGuard`로 일반 운영자까지 read 접근을 허용한다. mutation은 component route가 아니라 Web API의 최고 관리자 guard로 최종 차단한다.
- [ ] 목록에 사용자, 종류, 계획/실제 금액, 돈 상태, 내부 상태, 생성일, 마지막 변경, 조치 필요 여부를 표시한다.
- [ ] filter는 처리 중, 일부 완료, 확인 필요, 내부 재처리 필요, 완료를 제공한다. 검색·filter의 최종 구현은 서버 query를 사용하고 전체 데이터를 client에서 모두 받지 않는다.
- [ ] 상세에 결제별 항목과 시도 timeline, 내부 처리 timeline을 분리해 표시한다.
- [ ] 최고 관리자 동작:

- 재조회
- 같은 키 재시도
- 토스 관리자 사이트 수동 취소 검증
- 내부 처리 재시도
- 토스 성공 0건인 환불 건 종료
- 연결되지 않은 외부 취소 연결

- [ ] 버튼마다 대상 결제·금액·현재 상태를 확인 dialog에 표시한다.
- [ ] “수동 취소 완료” checkbox 하나로 완료시키지 않고 실제 재조회 결과를 기다린다.
- [ ] 일부 완료 상태에서 성공 항목과 남은 항목을 한눈에 구분한다.
- [ ] 회원 상세 이동 link를 제공한다.

```bash
npm test -- --watch=false --include='src/app/features/portal/payment-operations/payment-operations.component.spec.ts' --include='src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.spec.ts' --include='src/app/features/portal/portal.routes.spec.ts'
```

Review checkpoint: 일부 성공·수동 검증 불일치·내부 재처리 fixture를 화면에서 확인한다.

## Task 7 — Admin 전체 회귀와 접근성 검증

**Files**

- Verify: `clipper_web_admin/src/app/core/api/payment-refunds-api.service.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/members/members.component.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/refunds/refund-workbench/refund-workbench.component.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/refunds/refund-confirm-dialog/refund-confirm-dialog.component.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/refunds/refund-case-detail/refund-case-detail.component.spec.ts`
- Verify: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.spec.ts`

- [ ] keyboard만으로 회원 상세 이동, 환불 입력, dialog 취소가 가능하다.
- [ ] focus가 dialog 열기 전 요소로 돌아간다.
- [ ] pending 중 중복 click을 막는다.
- [ ] API error에 토스 원문 오류나 paymentKey가 표시되지 않는다.
- [ ] 좁은 화면에서 결제별 금액과 상태가 겹치지 않는다.
- [ ] 전체 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

Review checkpoint: 일반 운영자와 최고 관리자 계정 fixture로 route와 버튼을 각각 확인한다.

## Task 8 — Customer API 모델과 결제내역 환불 표시

**Files**

- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.html`
- Modify: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.spec.ts`

- [ ] 다음 표시 실패 테스트를 먼저 작성한다.

- 환불 없음: 원결제금액과 결제 완료
- 부분 환불: 원결제금액, 환불금액, 남은 금액, 처리 완료일
- 전액 환불: 원결제와 전액 환불 사실 모두 표시
- 처리 중: 확정되지 않은 금액을 완료처럼 표시하지 않음
- 관리자 확인 필요: 고객에게 내부 오류 대신 “환불 확인 중” 표시
- 영수증 link 안전성 유지

- [ ] 기존 `PaymentStatus.canceled`만으로 환불을 표현하지 않고 별도 refund field를 사용한다.
- [ ] 기본 결제와 상향 차액은 각각 결제내역 행으로 유지하되 같은 환불 처리와 연결된 상태를 일관되게 표시한다.
- [ ] 고객용 환불 신청 버튼을 추가하지 않는다.
- [ ] 외부 환불 문의 연락처는 최종 운영 문구가 전달되는 위치에만 추가하고 임의 이메일·전화번호를 만들지 않는다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration
npm test -- --watch=false --include='src/app/core/api/payments-api.service.spec.ts' --include='src/app/features/portal/payment-history/payment-history.component.spec.ts'
```

Review checkpoint: 결제 완료와 환불 완료가 서로 덮어쓰이지 않는지 확인한다.

## Task 9 — Customer 구독·크레딧 환불 상태 표시

**Files**

- Modify: `clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.html`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.spec.ts`

- [ ] 다음 상태 fixture를 테스트한다.

- 월간 환불 처리 중: 다음 결제 중단, 대상 크레딧 잠금
- 월간 환불 완료: 구독 즉시 종료
- 연간 현재 월 미사용: 즉시 종료
- 연간 현재 월 사용: 현재 구독 월 종료일까지 사용, 종료 예정일 표시
- 추가 구매 환불: 해당 지급 건만 처리 중/회수, 구독은 유지
- 환불 후 남은 무료 체험·추가 구매 크레딧은 사용 가능 잔액에 유지
- 무료 기능은 모든 상태에서 잠금 안내 대상이 아님

- [ ] “이용권 만료”와 “현재 구독 월 종료”, “다음 결제일”, “환불 적용 종료일”을 다른 label로 표시한다.
- [ ] 잠긴 크레딧은 전체 지급 이력에는 보이지만 사용 가능 합계에서 제외한다.
- [ ] 내부 재시도 횟수·토스 오류 코드·관리자 메모는 표시하지 않는다.

```bash
npm test -- --watch=false --include='src/app/core/api/payments-api.service.spec.ts' --include='src/app/features/portal/dashboard/dashboard.component.spec.ts' --include='src/app/features/portal/credits/credits.component.spec.ts'
```

Review checkpoint: 연간 현재 월 사용/미사용 두 종료 시나리오의 문구를 비교한다.

## Task 10 — Customer 전체 회귀와 보호 파일 확인

**Files**

- Verify: `clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Verify: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.spec.ts`
- Verify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`
- Verify: `clipper_web_client/src/app/features/portal/credits/credits.component.spec.ts`

- [ ] 전체 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

- [ ] 기존 untracked `build/`가 삭제·수정·stage되지 않았는지 확인한다.
- [ ] `git status --short`, tracked diff, staged diff를 기록한다.
- [ ] 사용자 검토 전 stage·commit·push하지 않는다.

## 완료 기준

- 회원 상세와 전체 환불 탭이 같은 backend 환불 건을 표시한다.
- 관리자가 결제별 환불금액을 입력하지만 월간·추가 구매 전액 금액은 변경할 수 없다.
- 두 단계 확인 뒤 최고 관리자만 실행할 수 있다.
- 일부 성공·수동 검증·내부 재처리 상태가 숨겨지지 않는다.
- 고객은 결제·환불·구독 종료·크레딧 잠금을 이해할 수 있지만 내부 오류는 보지 않는다.
- 고객용 환불 신청과 자동 환불금액 계산은 추가되지 않는다.
- Admin/Customer 전체 테스트와 build가 통과한다.
