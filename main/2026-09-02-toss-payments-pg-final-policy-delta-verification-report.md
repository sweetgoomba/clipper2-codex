# TossPayments PG 최종 정책 변경 구현 검증 보고서

- 작성일: 2026-09-02
- 정책 기준: `2026-09-02-toss-payments-pg-final-policy-delta.md`
- 구현 계획: `2026-09-02-toss-payments-pg-final-policy-delta-implementation-plan.md`
- 상태: 구현·검증 및 저장소별 로컬 커밋 완료

## 1. 구현 결과

### 요금제 변경

- 월간·연간 결제기간과 동일·상위·하위 요금제의 변경 조합을 하나의 도메인 정책으로 분류했다.
- 같은 결제기간의 상향, 같은 요금제의 월간→연간, 월간→상위 연간은 즉시 변경으로 처리한다.
- 같은 결제기간의 하향과 월간→하위 연간은 다음 결제일부터 적용하고, 연간→월간은 허용하지 않는다.
- 즉시 변경 금액은 기간 기준 차액과 해당 정기구독 크레딧 기준 차액을 각각 계산한 뒤 더 큰 금액을 선택한다.
- 연간 크레딧 계산은 월 지급량이 아니라 계약 전체 지급 예정량을 기준으로 한다.
- 계산 입력·두 잔존가치·두 차액·최종 선택 기준과 금액을 결제 주문에 불변 스냅샷으로 저장한다.
- 즉시 변경 결제가 성공하면 승인 시각부터 새 이용기간과 결제주기를 시작하고, 기존 정기구독 크레딧을 종료한 뒤 새 요금제의 첫 월 크레딧을 지급한다.
- 결제가 실패하거나 결과가 확정되지 않으면 기존 이용권과 결제주기를 유지한다.

### 크레딧과 만료

- 정기구독 크레딧의 실제 소비량을 지급·만료·환불 회수와 구분해 조회한다.
- 무료 체험 400크레딧은 회원가입 시각에 지급하고 그 시각부터 정확히 30×24시간 동안 유효하게 했다.
- 별도 구매 크레딧도 실제 지급 시각부터 정확히 30×24시간 동안 유효하게 했다.
- 정기구독 크레딧의 기존 월별 지급 경계와 이월 불가 정책은 유지했다.
- 무료 체험 및 별도 구매 크레딧은 즉시 요금제 변경 때 유지하고, 기존 정기구독 크레딧만 교체한다.

### 환불

- 월간·연간 정기구독은 환불 대상 정기구독 크레딧의 실제 사용 이력이 없을 때만 결제금액 전액 환불을 허용한다.
- 연간 부분 환불과 현재 구독 월 종료 방식은 일반 환불 흐름에서 제거했다.
- 사용하지 않고 만료된 정기구독 크레딧은 사용 이력으로 간주하지 않는다.
- 별도 구매 크레딧은 유효기간 안에 해당 지급분이 전부 남아 있을 때만 전액 환불한다.
- 즉시 상향의 차액 결제는 상향 후 지급된 정기구독 크레딧이 미사용이면 그 차액 결제 한 건만 전액 환불한다.
- 상향 차액 환불 완료 시 현재 이용권을 종료하고 상향 후 지급된 정기구독 크레딧을 회수한다. 상향 이전 이용권·결제·잔존가치는 복원하지 않는다.
- 기존의 토스 취소 시도 이력, 응답 유실 복구, 내부 처리 재시도, 중복 방지, 수동 취소 확인, 권한 분리는 유지했다.

### 관리자·고객 화면과 API 계약

- 관리자 일반 환불 흐름에서 임의 부분 환불액 입력을 제거하고, 취소 가능한 전액을 확인한 뒤 실행하도록 변경했다.
- 관리자 화면에서 기간 차액·크레딧 차액·최종 차액과 선택 기준을 확인할 수 있게 했다.
- 고객 화면에서 연간 부분 환불과 현재 구독 월 종료 표현을 제거하고 전액 환불·즉시 종료 정책에 맞췄다.
- OpenAPI와 양쪽 웹 모델·mock·계약 테스트를 동일한 응답 구조로 맞췄다.

## 2. 최종 자체 리뷰에서 보완한 경계 사례

1. 같은 요금제의 월간→연간 즉시 변경에서 결제 응답이 유실된 경우에도 기존 결제를 재조회해 완료할 수 있도록 복구 조건을 변경 유형 정책과 통일했다.
2. 한 결제기간 안에서 두 번 이상 연속 상향할 때 직전 상향 결제를 현재 이용기간의 기준 결제로 찾아 다음 차액을 계산하도록 보완했다.
3. 환불 처리 중인 구독은 외부 상태가 아직 `active`여도 새 요금제 변경을 시작할 수 없도록 환불 건 연결 상태와 갱신 일시정지 상태를 함께 검사했다.

세 항목 모두 재현 테스트를 먼저 추가해 실패를 확인한 뒤 수정했으며, 최종 전체 테스트에 포함됐다.

## 3. 자동 검증 결과

| 대상 | 결과 |
|---|---|
| API unit | 185 suites, 1,790 tests 통과 |
| API E2E | 격리 DB 55433·55434·55435 + fake Toss provider, 4 suites, 37 tests 통과 |
| API build | 통과 |
| API 변경 production TypeScript ESLint | 통과 |
| API 변경 TypeScript Prettier | 통과 |
| Admin | 328 tests 통과 |
| Admin build | 통과 |
| Customer | 226 tests 통과 |
| Customer build | 통과 |
| Desktop Angular | 2,143 tests 및 별도 6 tests 통과 |
| Desktop NestJS | build 통과, 명시 실행 792 tests 및 별도 6 tests 통과 |
| Desktop Electron | 219 tests 통과 |
| Infra | 71 tests 통과 |
| diff 무결성 | 7개 worktree 모두 `git diff --check HEAD` 통과, staged diff 없음 |
| 민감값 패턴 점검 | API·Admin·Customer 추가 diff에서 발견 0건 |

관리자 build에는 기존 initial bundle budget 초과 경고 56.17 kB가 남아 있으나 build는 성공했다.

## 4. Migration 검증

- 기존 migration 파일과 적용 이력은 수정하지 않고 신규 Admin migration `1788700000000-AddSubscriptionUpgradePricingSnapshot`만 추가했다.
- 격리된 검증 DB의 현재 적용 결과는 Admin 51개, Release 2개, User 5개 migration이다.
- 각 DB의 최신 migration timestamp는 Admin `1788700000000`, Release `1782790000000`, User `1788200000000`으로 확인했다.
- Admin `payment_orders.upgrade_pricing_snapshot`은 nullable `jsonb`로 생성됐고, 값이 있을 때 JSON object만 허용하는 check constraint가 적용됐다.
- 기존 개발 DB 5433·5434·5435에는 migration이나 write를 실행하지 않았다.

## 5. 알려진 비관련 검증 제약

- Desktop NestJS의 `shortform-clip-generation-events.test.ts`는 feature와 기준 worktree에서 동일하게 `this.projectStore.get is not a function`으로 실패한다. 이번 PG 변경과 무관한 기존 테스트 문제다.
- Desktop NestJS의 대화 강조 테스트 한 건은 5ms timeout에 의존해 feature와 기준 worktree 모두 간헐 실패한다. 같은 파일의 나머지 6개 테스트는 별도로 통과했다.
- `template-builder-no-s3-storage.test.js`는 git에 포함되지 않는 `.env.packaged`가 필요한 테스트라 실행 대상에서 제외했다. 비밀 환경 파일을 복사하거나 출력하지 않았다.
- API 전체 테스트의 최초 샌드박스 실행에서 로컬 HTTP 포트가 차단됐고, 권한이 있는 동일 환경에서 재실행해 1,790개 전부 통과했다.
- Admin·Customer build의 최초 샌드박스 실행은 Angular worker가 종료 코드 134로 중단됐고, 권한이 있는 동일 Node 22 환경에서 순차 재실행해 모두 통과했다.

## 6. 보호 상태와 worktree 상태

| Worktree | Branch | 현재 HEAD | 현재 상태 |
|---|---|---|---|
| API | `feature/toss-payments-pg-integration` | `2d93338` | 최종 정책 변경 커밋 완료 |
| Admin | `feature/toss-payments-pg-integration` | `dab857c` | 최종 정책 변경 커밋 완료 |
| Customer | `feature/toss-payments-pg-integration` | `7f4d04a` | 최종 정책 변경 커밋 완료 |
| Desktop Angular | `feature/toss-payments-pg-integration` | `f02bf221` | clean |
| Desktop NestJS | `feature/toss-payments-pg-integration` | `60a4f07` | clean |
| Desktop Electron | `feature/toss-payments-pg-integration` | `abdc575` | clean |
| Infra | `feature/toss-payments-pg-integration` | `e6ae78f` | clean |

- Customer의 기존 untracked `build/`는 삭제·수정·stage하지 않았다.
- API의 기존 untracked `docs/api/openapi.yaml.orig`는 삭제·수정·stage하지 않았다.
- `operator-jwt-expiry-test`와 `meme-overlay-timeline-seek` worktree는 수정하지 않았다.
- 실제 Toss 결제·취소 API, live payment, live refund를 호출하지 않았다.
- API `2d93338`, Admin `dab857c`, Customer `7f4d04a` 로컬 커밋을 생성했다.
- push, merge, PR, deploy는 수행하지 않았다.

## 7. 후속 범위

- 이번 최종 정책 변경분은 API·Admin·Customer 저장소별 로컬 커밋으로 보존됐다.
- `BILLING_DELETED` exact candidate/extant-previous integration test, user-MID webhook, 가상계좌 발급·입금·만료 검증 TODO는 그대로 유지한다.
- 그 다음 단계는 남은 Phase 5 TODO 처리 또는 Phase 6 출시 준비다. 기존 DB나 실제 Toss 환경을 사용하는 작업은 별도 명시적 승인 전에는 진행하지 않는다.
