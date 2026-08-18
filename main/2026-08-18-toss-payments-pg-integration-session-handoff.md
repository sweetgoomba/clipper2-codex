# 토스페이먼츠 PG 전체 연동 다음 세션 인계

- 기록일: 2026-08-18 (Asia/Seoul)
- 구현 상태: 아직 시작하지 않음
- 설계 상태: `2026-08-18-toss-payments-pg-integration-design.md` 작성, 사용자 최종 검토 대기
- 다음 코드 브랜치: `feature/toss-payments-pg-integration`

## 1. 다음 세션 첫 작업

1. 이 인계 문서와 `2026-08-18-toss-payments-pg-integration-design.md`를 전부 읽는다.
2. 사용자가 설계 문서를 승인했는지 확인한다.
3. 승인되지 않았다면 구현이나 worktree 생성을 시작하지 않고 변경 요청부터 반영한다.
4. 승인되면 Superpowers `writing-plans`를 읽고 `.codex/main`에 상세 구현 계획을 작성한다.
5. 구현 계획은 저장소별 task, 정확한 파일, 실패 테스트, 구현, 검증, 커밋 순서까지 포함한다.
6. 계획 검토 후 `using-git-worktrees`, `test-driven-development`, 적절한 실행 skill 순으로 진행한다.

## 2. 절대 건드리지 않을 것

- 각 저장소의 기존 `feat/access-credit-system-replacement` branch와 worktree
- 각 저장소의 `dev` branch와 현재 dev PG review 배포
- `dev.clipperstudio.ai`의 review mode 동작
- 사용자의 기존 미관련 변경

reset, rebase, branch 강제 이동, worktree 삭제를 하지 않는다.

## 3. 2026-08-18 확인한 보존 대상 HEAD

| 저장소 | access-credit HEAD | 원격 상태 |
| --- | --- | --- |
| `clipper_web_api` | `10cf10f` | 원격보다 18커밋 앞섬 |
| `clipper_web_client` | `25091ec` | 원격보다 5커밋 앞섬 |
| `clipper_web_admin` | `e17c5b4` | 원격보다 1커밋 앞섬 |
| `clipper_infra` | `dac0ed2` | 원격보다 1커밋 앞섬 |
| `clipper_angular` | `7938350` | 원격과 일치 |
| `clipper_electron` | `7f5d4d3` | 원격과 일치 |
| `clipper_nestjs` | `2abc490` | 원격과 일치 |

새 feature branch를 만들기 전에 위 로컬 access-credit HEAD를 해당 원격 branch에 push해 정확히 보존한다.

## 4. 2026-08-18 확인한 최신 origin/dev

| 저장소 | origin/dev |
| --- | --- |
| `clipper_web_api` | `4dcbfe4` |
| `clipper_web_client` | `4b361ef` |
| `clipper_web_admin` | `91116c7` |
| `clipper_infra` | `4d32022` |
| `clipper_angular` | `2847c38` |
| `clipper_electron` | `d3c88ba` |
| `clipper_nestjs` | `925d219` |

다음 세션에서는 먼저 `git fetch`하고 최신 값을 다시 확인한다. 이 표의 커밋을 무조건 최신이라고 가정하지 않는다.

## 5. branch와 worktree 생성 원칙

각 저장소에서:

```text
정확한 access-credit HEAD 보존·push
  -> 그 HEAD에서 feature/toss-payments-pg-integration 생성
  -> 전용 격리 worktree 생성
  -> 새 worktree 안에서 최신 origin/dev merge
  -> 충돌 해결
```

branch는 `feat/`가 아니라 정확히 `feature/toss-payments-pg-integration`을 사용한다.

## 6. merge 시 중요한 코드 경계

access-credit 쪽에서 보존한다.

- catalog, access, credits, operations 도메인
- subscription·renewal·payment method change 흐름
- 관리자 catalog·access·credit·renewal policy UI
- 고객 dashboard·credits·topup·pricing UI
- 데스크톱 entitlement와 credit 계약

dev PG review 쪽에서 선별 재사용한다.

- `TossPaymentsProvider` V2 HTTP adapter 형태
- `@tosspayments/tosspayments-sdk`와 `TossPaymentsSdkService`
- `paymentKey`, `lastTransactionKey`, confirm·billing issue·billing charge 멱등키
- success/fail redirect와 uncertain result 조회 복구
- Node 22에서 통과한 PG review 테스트 fixture

제거한다.

- 익명 review API·rate limiter·capability
- `TOSS_PAYMENTS_REVIEW_MODE`
- 1·3·12개월 심사용 노출 규칙
- review 주문의 미지급 전용 UI
- 토스페이 직접 `payToken`, `displayId`, `resultCallback` provider

## 7. migration 순서 주의

현재 dev에는 `1786560000000-MigrateReviewPaymentsToTossPaymentsPg`가 있고 access-credit에는 그 앞뒤로 다음 migration이 있다.

- `1786500000000-CreateProductCatalog`
- `1786600000000-CreateAccessCreditSystem`
- `1786700000000-GeneralizePaymentsAndCreateSubscriptions`
- 이후 renewal/payment method change migration

과거 migration을 편집하지 말고 merge 후 새 forward migration으로 최종 PG 스키마를 맞춘다. 빈 PostgreSQL 16에서 전체 migration 순서와 rollback 가능 범위를 테스트한다.

## 8. 구현 기본값

### 요금제

- Basic 월간 19,900원, 매월 400크레딧
- Basic 연간 190,900원, 매월 400크레딧
- Pro 월간 39,900원, 매월 1,000크레딧
- Pro 연간 382,900원, 매월 1,000크레딧

### 기능 권한

- Basic: 모든 현재 작업 플러그인 중 `variation` 제외
- Pro: Basic 전체 + `variation`
- DB와 관리자 UI에서 변경 가능, 기존 사용자에게 즉시 적용

### 추가 크레딧

- 100 / 5,900원 / 365일
- 500 / 27,900원 / 365일
- 1,000 / 49,900원 / 365일

### 결제수단

- 구독: 카드 자동결제만
- topup: 카드, 카카오페이, 네이버페이, 토스페이, 계좌이체, 가상계좌
- 가상계좌 입금기한: 24시간

### 구독

- 월간과 연간 모두 자동 갱신
- 연간 크레딧도 월별 지급
- 구독 크레딧은 다음 월별 지급일 만료, 이월 없음
- 다음 결제 취소와 기간 내 취소 철회
- 상향 즉시 차액 결제, 하향·주기 변경은 다음 갱신
- D+3 유예, D+1·D+2 자동 재시도

## 9. 환불 범위

돈 환불은 모두 제외한다.

- 환불 요청·고객센터
- 관리자 환불 목록·승인
- 환불 산식
- 토스 취소 API
- 전액·부분 환불
- 돈 환불에 따른 크레딧·권한 조정

웹훅에서 외부 `CANCELED`·`PARTIAL_CANCELED`를 감지해 재조회·기록·경고하는 것은 포함한다. 자동 권한·크레딧 변경은 하지 않는다.

작업 실패 시 서비스 내부 크레딧을 돌려주는 것은 `크레딧 반환/복구`이며 계속 포함한다.

## 10. 공식 MCP에서 재확인한 핵심

- 빌링키는 발급 후 조회할 수 없다.
- 빌링키 발급 전에 암호화 authKey와 고정 멱등키를 저장해야 한다.
- POST 멱등키는 15일 유효하며 같은 응답 복구에 사용할 수 있다.
- 같은 요청 처리 중 `409 IDEMPOTENT_REQUEST_PROCESSING`이 올 수 있다.
- 가상계좌는 승인 시 `WAITING_FOR_DEPOSIT`, 입금 `DONE` 후 지급한다.
- 일반 결제 웹훅은 body를 신뢰하지 않고 Payment API로 재조회한다.
- `PAYMENT_STATUS_CHANGED`와 `DEPOSIT_CALLBACK`은 가상계좌에서 중복될 수 있다.
- `BILLING_DELETED`를 현재·과거·후보 키 fingerprint로 구분해야 한다.

## 11. 다음 구현 계획에 반드시 포함할 작업

1. access-credit HEAD 원격 보존
2. feature branch·worktree 생성과 최신 dev merge
3. migration 충돌 해결과 새 PG forward migration
4. OpenAPI 우선 계약
5. 상품 seed와 exact monthly credit expiry
6. provider adapter 교체
7. billing auth attempt와 빌링키 응답 유실 복구
8. 로그인 구독 checkout과 최초 결제
9. 월·연 갱신과 취소·철회
10. 카드 변경과 `past_due` 재결제
11. topup 주문서형 카드·간편·계좌이체
12. 가상계좌 입금 대기·웹훅·지급
13. PAYMENT_STATUS_CHANGED·DEPOSIT_CALLBACK·BILLING_DELETED inbox
14. 결제내역·영수증·가상계좌 고객 UI
15. 관리자 운영 조회·경고·재처리
16. 상향·하향·주기 변경
17. review mode와 legacy 무통장 제거
18. 고객·관리자·데스크톱 계약 정리
19. infra 로컬 환경변수·CSP·compose 검증
20. 전체 자동 테스트·빌드·테스트키 수동 검증

## 12. 테스트 실행 기준

- API와 고객 웹: Node 22
- 고객 웹과 API는 테스트 우선
- API: 전체 Jest, build, OpenAPI parse, 빈 DB migration
- 고객 웹: 전체 Angular test와 build
- 관리자 웹: 프로젝트 지정 Node 버전의 전체 test와 build
- Angular·Electron·NestJS: 각 저장소 현재 지정 버전과 테스트 명령
- Infra: compose config, env validation, script 정적 검증

operator JWT의 과거 고정 날짜 실패는 최신 dev의 `e3feaa5`에서 이미 해결되었으므로 별도 선행 수정으로 취급하지 않는다.

## 13. 다음 세션 종료 조건

다음 세션은 설계 승인 뒤 바로 구현을 시작하지 말고 먼저 상세 구현 계획을 `.codex/main`에 작성·자체 검토한다. 그 계획이 저장소별 실제 파일·테스트 순서와 일치하는지 확인한 후 worktree와 TDD 구현으로 전환한다.
