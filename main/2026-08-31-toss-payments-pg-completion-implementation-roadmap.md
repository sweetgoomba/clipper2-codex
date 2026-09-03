# TossPayments PG 완성 구현 로드맵

- 작성일: 2026-08-31
- 상태: 구현 전 실행 계획
- 기준 설계: `2026-08-31-toss-payments-pg-completion-refund-credit-design.md`
- 기준 코드: 7개 `toss-payments-pg-integration` feature worktree

> 이 문서는 구현 순서와 검증 경계를 정의한다. 문서 작성만으로 코드 수정, migration 생성·실행, 토스페이먼츠 호출, 운영 반영이 승인되는 것은 아니다. 실제 구현을 시작할 때는 `superpowers:executing-plans`를 사용하고 사용자의 별도 구현 승인을 먼저 받는다.

## 1. 목표

현재 구현된 정기구독·추가 크레딧 결제를 다음 상태까지 완성한다.

- 회원가입 시 무료 체험 400크레딧을 신뢰성 있게 지급한다.
- 무료 기능은 정기구독과 관계없이 사용하고, 유료 기능은 사용 가능한 크레딧만 검사한다.
- 무료 체험·정기구독·추가 구매 크레딧의 만료와 차감 순서를 승인 정책에 맞춘다.
- 요금제 상향 결제에 환불 판단에 필요한 불변 스냅샷과 결제 연결을 남긴다.
- 관리자가 한 환불 건에서 여러 토스 결제를 전액 또는 부분 취소할 수 있다.
- 토스 취소 성공 뒤 정기구독·크레딧 처리를 멱등하게 완료한다.
- 일부 성공, 응답 유실, 수동 취소, 내부 처리 실패를 추적하고 복구한다.
- 관리자와 고객 화면이 같은 환불 상태를 표시한다.
- 신규 DB와 일회용 복제 DB에서 migration과 전체 회귀 검증을 통과한다.

## 2. 기준점과 보호 대상

| 저장소 | 기준 HEAD | 역할 |
|---|---|---|
| Web API | `a85e2fa665a8497ff66c4939e417fb10fc48df8d` | 상품·구독·결제·크레딧·환불의 최종 판단과 DB 변경 |
| Customer web | `2fbd5e9c6c43b1efefd334cf57dc6bc80254cb43` | 결제·환불·구독·크레딧 고객 표시 |
| Admin web | `cbf7c52a20555ff736e0be7711dd3645fdfe59c4` | 회원별 환불 실행과 전체 환불 운영 화면 |
| Infra | `e6ae78f58b559cf3715f6acaecf6ac067a4e7930` | 환경 검증·migration 및 배포 runbook |
| Desktop Angular | `f0da4e4a4aca26bbf08ccbc16856b085c06b0404` | 플러그인 잠금 제거와 크레딧 부족 안내 |
| Desktop Electron | `abdc5753741301f4bf22278a22ca8e20dc78ac24` | 직접 변경 예상 없음, 회귀 확인 |
| Desktop NestJS | `8e131e3f601f981259c7bf00bb1a3001631c0fe5` | 플러그인 이용권 차단 제거와 Web API 프록시 계약 정리 |

보호 규칙:

- 최신 `dev`는 PG가 연결되지 않은 다른 설계이므로 이 구현의 merge base나 기능 판단 기준으로 사용하지 않는다.
- Customer web의 기존 untracked `build/`는 삭제·수정·stage하지 않는다.
- `meme-overlay-timeline-seek`와 `operator-jwt-expiry-test` worktree는 수정하지 않는다.
- 기존 migration 파일과 migration history를 수정하지 않는다.
- 5433·5434·5435 DB에는 어떤 write나 migration도 실행하지 않는다.
- 토스 테스트키 검증 전에는 mock 기반 검증만 수행하고, 운영키·실결제·실환불은 사용하지 않는다.
- 저장소별 commit·push는 사용자가 별도로 요청할 때만 한다.

## 3. 구현 단위와 의존성

```text
1. 크레딧·이용 정책 기반
   ├─ 한국 날짜 계산
   ├─ 회원가입 무료 체험 지급
   ├─ 충전 시점 우선 차감
   └─ 이용권/플러그인 차단 제거
            ↓
2. 결제 스냅샷과 연결 보강
   ├─ 구독 월·결제기간 스냅샷
   ├─ 기본 결제 ↔ 상향 차액 결제 연결
   └─ 환불 판단 가능한 결제별 잔액
            ↓
3. 환불 백엔드
   ├─ 환불 건/항목/시도/내부 이력
   ├─ 환불 전 크레딧·정기구독 잠금
   ├─ 토스 취소/재조회/멱등 재시도
   └─ 정기구독·크레딧 후처리
            ↓
4. 관리자·고객 화면
   ├─ 회원 상세 환불 진입
   ├─ 전체 환불 운영 탭
   └─ 고객 결제·구독·크레딧 상태
            ↓
5. 기존 PG TODO의 별도 마무리
   ├─ BILLING_DELETED 두 정확 상태 통합 테스트
   ├─ user-MID 결제 웹훅
   └─ 가상계좌 발급·입금·만료 검증
            ↓
6. 전체 검증과 출시 준비
```

한 단계가 다음 단계에 제공하는 계약을 먼저 고정한다. 화면에서 환불 판단을 복제하지 않고 모든 자격·상태 계산은 Web API 응답을 사용한다.

## 4. 단계별 산출물

### Phase 0 — 구현 시작 전 재확인

- [ ] 7개 feature worktree의 HEAD와 status를 다시 기록한다.
- [ ] `operator-jwt-expiry-test`의 관리자 인증 변경 여부만 읽어 환불 권한 계획과 충돌하는지 확인한다.
- [ ] `meme-overlay-timeline-seek`가 Desktop Angular의 동일 파일을 수정하는지 확인한다.
- [ ] Web API의 마지막 admin/user migration 번호를 다시 확인한다.
- [ ] 3000·4201 listener가 feature 검증 서버가 아님을 확인하고 별도 포트를 정한다.
- [ ] 기존 5433·5434·5435가 아닌 신규 DB와 일회용 복제 DB 이름·포트를 정한다.

중단 조건: 기준 HEAD가 바뀌었거나 같은 migration/schema 파일에 다른 작업이 생겼다면 계획을 먼저 갱신한다.

### Phase 1 — 무료 체험·크레딧·기능 사용 정책

상세 계획: `2026-08-31-toss-payments-credit-access-policy-implementation-plan.md`

완료 조건:

- [ ] 무료 체험 400크레딧이 가입일 기준으로 한 번만 지급된다.
- [ ] 가입일·구매일을 1일차로 계산한 한국 날짜 30일 만료가 적용된다.
- [ ] 정기구독 크레딧이 한국 날짜 기준 구독 월 경계에서 소멸한다.
- [ ] 모든 출처의 크레딧이 충전 시점, 지급 건 ID 순서로 차감된다.
- [ ] 추가 구매 크레딧은 구독 종료 뒤에도 만료 전까지 사용할 수 있다.
- [ ] 무료 동작과 플러그인 실행이 정기구독·요금제별 허용 목록으로 막히지 않는다.
- [ ] 유료 동작은 크레딧 부족만 안정적인 차단 사유로 사용한다.

### Phase 2 — 결제 스냅샷과 환불 데이터 기반

상세 계획: `2026-08-31-toss-payments-refund-backend-implementation-plan.md`의 Task 1~4

완료 조건:

- [ ] 신규 최초·갱신·상향 결제가 구독기간과 혜택 월 스냅샷을 명시적 컬럼으로 저장한다.
- [ ] 상향 차액 결제가 같은 기간의 기본 결제와 연결된다.
- [ ] 환불 건, 결제별 항목, 토스 시도·검증, 내부 처리 이력을 저장한다.
- [ ] 원결제 상태와 환불 상태가 분리된다.
- [ ] 한 결제의 누적 환불액과 현재 취소 가능 잔액을 검증할 수 있다.
- [ ] 기존 데이터에 스냅샷이 부족하면 임의 추론하지 않고 관리자 확인 필요로 분류한다.

### Phase 3 — 토스 결제 취소와 환불 처리 조정

상세 계획: `2026-08-31-toss-payments-refund-backend-implementation-plan.md`의 Task 5~12

완료 조건:

- [ ] 토스 결제 조회가 `balanceAmount`, 부분 취소 가능 여부, 취소 거래 목록을 안전하게 파싱한다.
- [ ] 전액 취소는 `cancelAmount` 없이, 부분 취소는 원 단위 정수 금액과 함께 호출한다.
- [ ] 결제별 고정 중복 방지 키를 사용한다.
- [ ] 여러 결제는 전체 사전 확인 뒤 순차 처리한다.
- [ ] 일부 성공·timeout·5xx·응답 유실·중복 요청을 재조회로 복구한다.
- [ ] 토스 관리자 사이트 수동 취소는 API 재조회로 실제 거래를 검증한 뒤에만 완료된다.
- [ ] 환불 잠금 이후 같은 크레딧이 새 작업에 사용되지 않는다.
- [ ] 토스 취소 성공 후 내부 DB 실패는 토스 재호출 없이 내부 처리만 재시도한다.

### Phase 4 — 관리자·고객 화면

상세 계획: `2026-08-31-toss-payments-refund-admin-customer-implementation-plan.md`

완료 조건:

- [ ] 회원 목록이 정기구독 상태, 현재 구독 월 종료일, 다음 결제일, 크레딧, 문제 상태를 표시한다.
- [ ] 회원 상세가 계정·구독·크레딧·결제·환불을 분리해 표시한다.
- [ ] 최고 관리자만 두 단계 확인 후 환불을 실행할 수 있다.
- [ ] 일반 운영자는 같은 정보를 읽을 수 있지만 실행·재처리할 수 없다.
- [ ] 전체 환불 탭에서 일부 완료, 확인 필요, 내부 재처리 필요 건을 처리할 수 있다.
- [ ] 고객 결제내역과 구독 화면이 환불금액·상태·종료 예정일을 표시한다.
- [ ] 고객에게 토스 상세 오류, 내부 시도 이력, 비밀값이 노출되지 않는다.

### Phase 5 — 기존 PG TODO를 별도 흐름으로 마무리

환불 기반 구현과 자동 검증이 안정된 뒤에 수행한다. 환불의 첫 구현 작업과 섞지 않는다.

- [x] `BILLING_DELETED` issued-candidate 정확 일치 상태의 repository-backed 통합 테스트 (2026-09-02, 일회용 PostgreSQL + controllable fake provider)
- [x] `BILLING_DELETED` extant-previous 정확 일치 상태의 repository-backed 통합 테스트 (2026-09-02, 일회용 PostgreSQL + controllable fake provider)
- [ ] user-MID widget key로 `PAYMENT_STATUS_CHANGED` 웹훅과 중복 전달 검증
- [ ] user-MID widget key로 `DEPOSIT_CALLBACK` 웹훅과 중복 전달 검증
- [ ] 가상계좌 발급 후 입금 전 `waiting_for_deposit`와 지급 0건 검증
- [ ] 가상계좌 입금 후 `paid`·지급 정확히 1건 검증
- [ ] 미입금 가상계좌 만료 후 지급 0건 검증

각 항목은 실행 직전에 별도의 좁은 테스트 계획을 작성한다. 실제 user-MID key 값과 가상계좌 정보는 문서에 남기지 않는다.

### Phase 6 — 전체 회귀·migration·출시 준비

상세 계획: `2026-08-31-toss-payments-pg-final-verification-rollout-plan.md`

완료 조건:

- [ ] 신규 DB에서 전체 migration이 처음부터 적용된다.
- [ ] 일회용 복제 DB에서 현재 상태부터 후속 migration이 적용되고 데이터 수량·연결 무결성이 유지된다.
- [ ] 7개 저장소의 관련 단위·계약·통합 테스트와 build가 통과한다.
- [ ] 토스 테스트키로 승인된 테스트 시나리오만 수행하고 결과를 민감정보 없이 기록한다.
- [ ] 운영 migration, 운영 토스 호출, merge·push·deploy는 별도 승인 체크포인트에 남는다.

## 5. API 소유권

| 판단 또는 동작 | 최종 소유자 | 화면/데스크톱 책임 |
|---|---|---|
| 크레딧 사용 가능 여부와 차감 순서 | Web API | 응답을 표시하고 서버 오류 코드를 사용자 문구로 변환 |
| 무료 체험 발급·만료 | Web API | 잔액·만료일만 표시 |
| 추가 크레딧 구매 자격 | Web API | 구매 버튼 노출은 편의 기능이며 서버 검사를 대체하지 않음 |
| 환불 가능 여부 | Web API | 관리자 화면은 근거와 차단 이유를 표시 |
| 연간 환불금액 | 관리자 입력 + Web API 범위 검증 | 계산 자동화 없음 |
| 토스 결제 취소 | Web API의 토스 연동 계층 | 브라우저에서 토스를 직접 호출하지 않음 |
| 정기구독·크레딧 환불 후처리 | Web API | 상태를 조회·표시 |
| 환불 실행 권한 | Web API guard | Admin route guard는 추가 방어선 |

## 6. migration 순서

구현 시작 시 마지막 번호를 재확인하되 현재 기준 파일명은 다음과 같이 예약한다.

1. Admin DB `1788200000000-ApplyLaunchCreditAccessPolicies.ts`
2. User DB `1788200000000-CreateUserOnboardingJobs.ts`
3. Admin DB `1788300000000-PersistPaymentRefundSnapshots.ts`
4. Admin DB `1788400000000-CreatePaymentRefundWorkflow.ts`
5. Admin DB `1788500000000-AddRefundHoldsAndBalances.ts`

Admin DB와 User DB는 migration history가 별도이므로 같은 timestamp를 사용할 수 있다. 구현 시작 시 같은 DB 계열에서 번호가 충돌하면 새 번호로 계획 문서와 파일명을 함께 갱신한다. 기존 `1788100000000-CreateFreeTrialPolicy.ts`는 수정하지 않는다.

## 7. 구현 세션 분할

한 세션에서 전체를 동시에 변경하지 않는다.

1. Session A: Phase 1만 구현·검증
2. Session B: Phase 2와 환불 domain/repository까지만 구현·검증
3. Session C: 토스 provider와 환불 실행·복구 구현·검증
4. Session D: Admin API·화면 구현·검증
5. Session E: Customer·Desktop 정리와 교차 저장소 계약 검증
6. Session F: 기존 PG TODO의 별도 통합 검증
7. Session G: 신규/복제 DB, 토스 테스트키, 전체 회귀와 출시 준비

각 세션은 다음 단계로 넘어가기 전에 관련 테스트 결과와 남은 위험을 사용자에게 보고한다. 자동 commit·push는 하지 않는다.

## 8. 명시적으로 범위에서 분리할 기존 TODO

다음은 유지하지만 환불 기반 구현의 선행 조건으로 끌어오지 않는다. 다만 전체 PG 완료 판정 전에는 Phase 5에서 별도로 끝낸다.

- `BILLING_DELETED` exact candidate/extant-previous integration test
- user-MID webhook
- 가상계좌 발급
- 가상계좌 입금
- 가상계좌 만료 검증

단, 결제 취소 provider 모델은 나중에 가상계좌 환불 계좌 정보가 필요할 수 있도록 확장 가능한 입력 구조로 만든다. 위 가상계좌 TODO를 이 계획에서 구현하지는 않는다.

## 9. 계획 변경이 필요한 조건

다음 중 하나가 확인되면 구현을 멈추고 설계 또는 계획을 다시 승인받는다.

- 전략팀 약관 결과가 이미 승인된 환불 대상·종료 시점·크레딧 회수 규칙을 바꾼다.
- 토스 최신 API가 현재 가정한 전액·부분 취소 또는 중복 방지 방식과 다르다.
- 실제 상향 결제 데이터만으로 기본 결제와 상향 결제를 안전하게 연결할 수 없다.
- `operator-jwt-expiry-test` 결과가 최고 관리자 권한 모델을 변경한다.
- 가상계좌 결제가 런칭 필수로 변경되어 환불 계좌 입력이 환불 첫 범위에 들어온다.
- 기존 DB의 실제 데이터가 추가형 migration만으로 보존되지 않는다.

## 10. 최종 승인 경계

이 로드맵과 하위 계획이 완성돼도 구현은 시작하지 않는다. 사용자가 구현 범위와 시작 세션을 명시적으로 승인한 뒤 해당 계획의 첫 실패 테스트부터 시작한다.
