# AI 부스 가입 프로모션과 Free Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Track steps with checkbox (`- [x]`) syntax. 사용자가 요청하지 않은 commit/push는 하지 않는다.

**Goal:** 신규 회원이 Google 인증 뒤 가입 화면에서 선택 코드를 등록하고, 가입 혜택과 이벤트 크레딧을 받은 상태로 서비스를 시작하며 Free·요금제별 기능과 제안 F 요금제 표시가 실제 관리자 설정과 일치하게 한다.

**Architecture:** 기존 코드·캠페인·등록 기록과 크레딧 원장을 재사용하고 가입 전용 크레딧 지급을 이용권 지급과 분리한다. 사용자 DB의 가입/지급 의도와 관리자 DB의 지급은 기존 내구 작업·멱등 처리를 확장해 연결한다. Free는 활성 주 이용권이 없을 때의 지속 정책으로 조회하며 가입 크레딧 잔액으로 수명을 정하지 않는다.

**Tech Stack:** 기존 NestJS·TypeORM·PostgreSQL, Angular/Material, Jest 및 Desktop node:test. 새 라이브러리/프레임워크나 플러그인 목록 자동 동기화를 선행 도입하지 않는다.

**Spec:** [확정 범위·제안 F·브랜치 증거](02-ai-booth-signup-credits-and-free-scope.md).

## Global Constraints

- 신규 코드는 **Google 왕복 뒤 /signup/consent**에서 입력한다. Google OAuth state/구글 요청에 코드를 넣는 별도 경로를 만들지 않는다.
- 최초 가입 혜택과 프로모션 지급분의 출처·유효기간·원장은 별개이며 첫 로그인 잔액에는 두 유효 지급분이 반영된다. 기존 회원/재동의에는 가입 전용 보너스를 주지 않는다.
- Free는 지속 상태, 가입 크레딧은 최초 1회다. 카드 문구는 **가입 시 1회 N크레딧**, 유효기간은 **가입 크레딧 유효기간: 가입일부터 D일**. N/D는 설정값이다.
- 프로모션 유료 예약·레퍼럴 성과·XLSX는 Git 보존 후 실행 코드에서 제거한다. 일반 정기결제·환불·원장과 회원 참여 조회는 보존한다. 운영 데이터 삭제를 포함하지 않는다.
- Basic ⊆ Pro ⊆ Business. Free 허용 목록은 별도다. 설치·탐색·편집 준비를 허용하고 제한 대상 실행에서 현재 등급/잔액을 검사한다.
- 프런트에 요금제별 플러그인 목록/가격/지급량을 하드코딩하지 않는다. 목업 예시 숫자와 허용 조합은 정책이 아니다.
- 공개 API는 raw 응답 계약을 유지하고 OpenAPI·DTO·FE 모델/호출을 함께 변경한다. DB 간 FK/JOIN/공유 트랜잭션을 만들지 않는다.
- 새 Markdown은 .codex에만 둔다. 기존 설치/즐겨찾기 순서, 연간 월별 지급, 만료·FIFO·변경 과금·환불·재시도 정책을 임의 변경하지 않는다.

## Review Focus

1. Google 인증은 끝났으나 가입 동의는 미완료: 세션·혜택을 먼저 발급하지 않는다. Task 4의 신규/기존/재동의 시험으로 고정한다.
2. 두 DB 사이 장애·응답 유실 후 재시도: 회원/참여/지급/원장 중복과 누락을 막는다. Task 4의 장애 지점별 시험으로 고정한다.
3. 코드 확인 뒤 중지/만료/마지막 자리 경쟁: 실제 지급 때 재검사하고 허위 잔액을 표시하지 않는다. Task 3·4의 동시성 시험으로 고정한다.
4. 새로고침·새 대기표·다른 Google 계정: 임시 입력이 잘못된 계정에 자동 적용되지 않는다. Task 5의 입력 보존/정리 시험으로 고정한다.
5. 잔액 소진·이용권 종료·대기 작업 중 등급 변경: Free가 사라지거나 가입 크레딧이 다시 지급되지 않고, 거절한 새 실행에 차감하지 않는다. Task 6·7의 상태 전환 시험으로 고정한다.

## 작업 폴더와 파일 표기

기존 격리 작업 루트는 `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028`다. 아래 API/Client/Admin/Nest/App은 각각 이 루트의 `web/clipper_web_api`, `web/clipper_web_client`, `web/clipper_web_admin`, `desktop/clipper_nestjs`, `desktop/clipper_angular`를 뜻한다. Electron은 계약/IPC 확인 결과 실제 수정이 필요할 때만 바꾼다.

모든 제품 수정은 `feat/signup-credit-promotion-free-20261102`에서 한다. `archive/promotion-access-referral-20261102`와 원본 checkout은 보존한다. 6개 checkout을 새 작업 브랜치로 전환했고 아래 검증을 수행했다. 상세 증거·최종 수정·한계는 [구현/검증 기록](02-ai-booth-signup-free-implementation-and-verification.md)을 따른다.

## 공통 작업 방식

각 Task는 해당 회귀 테스트를 먼저 추가해 실패를 확인하고, 필요한 최소 구현 후 그 테스트와 빌드를 통과시킨다. 기존 테스트 삭제로 새 정책 검증을 대신하지 않는다. 완료 표시는 실제 명령 결과가 있는 경우에만 체크한다. 커밋은 사용자 요청 시에만 한다.

### Task 1: 새 작업 브랜치와 기준 상태

**Files:** 제품 파일 변경 전 준비. Spec의 `02-launch-scope-evidence/branch-preparation.json` 및 API 6파일 패치 참조.

- [x] 기존 격리 작업 폴더·브랜치·미커밋 상태를 다시 확인한다. 이후 생성된 타 작업 변경은 보존한다.
- [x] 새 브랜치의 기준 SHA와 보존 브랜치 SHA를 대조한 뒤 새 브랜치를 checkout한다. 기존 API topup 보완은 패치와 비교해 필요한 변경만 보존/이식한다.
- [x] 현재 의존성과 저장소별 빌드/관련 테스트를 실행해 기준 실패를 변경 유발 실패와 구분한다. 원본 checkout·DB·기존 서버를 초기화하지 않는다.

### Task 2: 프로모션 예약·성과·내보내기 제거

**Files:** API `src/modules/promotions/{application/promotion-report.service.ts,domain/promotion-report.model.ts,domain/promotions.repository.ts,infrastructure/typeorm-promotions.repository.ts,presentation/admin-promotions.controller.ts,presentation/promotion.dto.ts,promotions.module.ts}` 및 관련 spec. API `src/modules/payments/application/subscription-payments.service.ts`와 `presentation/dto/create-subscription-checkout.dto.ts`의 프로모션 전용 연결. Client/Admin `src/app/core/api/promotions-api.service.ts` 및 `features/portal/promotions/promotions.component.*`, Client의 프로모션 예약 전용 호출/모달/대시보드 표시. OpenAPI 해당 경로.

**Interfaces:** 제거: 프로모션 `report`/`report.xlsx`와 프로모션 종료 후 첫 결제 예약 진입. 유지: 캠페인/코드 CRUD, 코드/회원별 참여 내역, 일반 구독 checkout·갱신·해지·환불.

- [x] 삭제 대상 경로를 호출하면 제공되지 않고 관리자/회원 화면에도 버튼·탭이 없음을 시험한다. 참여 회원 목록과 일반 결제 회귀는 유지한다.
- [x] 전용 서비스·집계 쿼리·DTO·DI·API/FE 호출을 제거한다. 공유 결제/Excel 의존성은 다른 사용처가 있으면 유지한다. 대량 주석으로 남기지 않는다.
- [x] 등록 건수/상한·참여 회원 조회·크레딧 원장은 계속 동작하는지 검증한다.

### Task 3: 가입 전용 크레딧 혜택과 관리자 설정

**Files:** API `src/modules/promotions/{domain/promotion.model.ts,domain/promotion-policy.ts,domain/promotions.repository.ts,application/promotions.service.ts,infrastructure/typeorm-promotions.repository.ts,presentation/promotion.dto.ts}` 및 관련 spec. API의 admin DataSource별 신규 마이그레이션/등록. Admin `features/portal/promotions/promotions.component.*`, API 모델/호출.

**Interfaces:** 캠페인 혜택은 이용권형과 가입 전용 크레딧형을 구분하며, 후자는 지급 수량·크레딧 유효일수를 사용한다. 가입 전용 등록은 일반 회원의 등록 경로에서 허용하지 않는다. 참여 기록은 이용권 ID가 없어도 조회/회수할 수 있어야 한다.

- [x] 설정 수량 200/유효일수 테스트 값을 사용한 가입형이 이용권·월별 지급 일정 없이 1회 지급되는 시험을 추가한다. 운영 기본값 200을 하드코딩하지 않는다.
- [x] 코드별 상한 2의 두 코드가 각각 2명까지 등록 가능하며 동일 캠페인의 중복 참여·동시 마지막 자리 초과를 막는 시험을 추가한다.
- [x] 혜택 종류별 필수값 검증과 지급 스냅샷을 추가하고 공통 코드/등록 처리를 재사용한다. 관리자 입력·수정·회원 이메일/코드별 내역을 연결한다.
- [x] 미사용 프로모션 지급분만 회수하고 별도 구매/가입 지급분과 사용 기록은 보존하는지 검증한다.

### Task 4: Google 인증 뒤 가입 완료와 내구 지급

**Files:** API `auth/presentation/dto/signup.dto.ts`, `auth/presentation/auth.controller.ts`, `auth/application/signup.service.ts`, `auth/domain/signup-completion.repository.ts`, `auth/infrastructure/typeorm-signup-completion.repository.ts`, `users/domain/user-onboarding-job.model.ts`, `users/infrastructure/user-onboarding-job.entity.ts`, `users/infrastructure/typeorm-user-onboarding-jobs.repository.ts`, `access/application/free-trial-onboarding.service.ts`, `access/application/free-trial-provisioner.service.ts` 및 관련 spec. 경로는 모두 `src/modules/` 아래다. user DataSource의 지급 의도 저장 마이그레이션과 OpenAPI.

**Interfaces:** `SignupCompleteDto`/`SignupCompleteInput`에 `promotionCode?: string`을 추가한다. 가입 대기표로 확인한 계정과 실제 신규 생성 결과를 사용해 지급 의도를 보존한다. 기존 신규/기존 구분 `created`를 버리지 않는다. 일반 OAuth state에는 코드 필드를 추가하지 않는다.

- [x] 현재 `signup-flow.spec.ts`의 웹/앱 신규 동의 게이트를 유지하고, 코드 미입력/유효 코드/기존 계정/재동의의 지급 결과를 시험한다.
- [x] 최초 가입 크레딧 400 + 프로모션 200인 테스트 설정에서 지급·원장이 각각 1건이며 완료 직후 잔액은 600임을 시험한다.
- [x] user DB 가입·의도 저장 후 admin DB 실패, admin 지급 커밋 후 user 작업 완료 기록 실패, 세션 발급/응답 유실을 각각 재현한다. 재처리 후 지급·참여·원장이 각 1회임을 시험한다.
- [x] 기존 작업 lease/멱등 처리를 확장한다. 지급 전에 로그인 완료/600 표시를 내보내지 않는다. 이미 생성된 회원의 미완료 가입 의도는 복구하되 기존 회원에게 새 가입 혜택을 주는 통로가 되지 않게 한다.
- [x] 잘못된 코드·지급 시 상한 소진은 명확한 입력 오류/처리 상태로 반환한다. 코드 입력을 보존하고 수정·제거할 수 있게 하며 보너스 미지급을 숨기지 않는다. 대기표 사용 완료와 로그인 발급의 실패 복구를 함께 검증한다.

### Task 5: 가입 코드 UI와 참여 회원 조회 연결

**Files:** Client `features/public/signup-consent/signup-consent.component.{ts,html,scss,spec.ts}`, `signup-ticket.ts`/spec, `core/api/auth-api.service.ts`, `core/api/models.ts`. Admin `features/portal/promotions/promotions.component.*` 및 회원 상세 연결.

**Interfaces:** 동의 화면의 `completeSignup` 호출은 기존 대기표·필수동의와 선택 코드를 함께 보낸다. 신규 여부는 서버가 판단한다. 현재 가입 대기표의 fragment→같은 탭 저장 동작을 유지한다.

- [x] Google 복귀 후 신규에게 코드 입력란이 보이고, 소문자 정규화·빈 값 생략·실패 후 입력 유지·중복 제출 방지를 시험한다.
- [x] 입력 임시 보관을 넣으면 대기표/계정 단위로 구분하고 새 대기표·완료·취소·만료 시 정리한다. 오래된 다른 계정의 코드를 자동 제출하지 않는 시험을 추가한다.
- [x] 가입 완료 상태와 실제 서버 지급 결과를 기준으로 잔액을 새로 조회한다. 화면에서 임의로 200을 더하지 않는다.
- [x] 관리자 코드→회원, 회원→입력 코드 조회가 일치하며 빈 목록에도 안내가 보이는지 검증한다.

### Task 6: 지속 Free와 가입 크레딧 유효기간 분리

**Files:** API `access/application/effective-access.service.ts`, `access/application/free-trial-provisioner.service.ts`, `catalog/application/product-catalog.service.ts` 및 spec/DTO, Client/Admin 접근 상태 소비자와 공통 API 모델, Nest `src/core/auth/`, App의 접근 상태 소비자. 현재 trial/free_trial 참조를 검색해 외부 계약 소비자 전체를 갱신한다.

**Interfaces:** 활성 주 이용권이 없으면 Free 정책을 조회 결과로 반환한다. 지속 primary access 행이나 0원 결제 계약을 만들지 않는다. 공개 catalog는 Free의 최초 가입 크레딧 수량·유효기간과 허용 목록을 표시할 수 있어야 한다.

- [x] 가입 지급분이 0·만료·없음이어도 Free 상태가 유지되고, 유료 종료/재가입을 거쳐도 최초 가입 크레딧이 다시 지급되지 않는 시험을 추가한다.
- [x] 기존 가입 크레딧 만료 기준(가입일 기준 설정 일수)을 유지한다. 유효 topup/프로모션 잔액이 있어도 현재 허용 목록은 Free 정책을 따르는지 시험한다.
- [x] 과거 지급/사용 기록을 보존하며 UI의 이용 상태와 가입 혜택 만료일을 분리한다. 사용자 표시명만 바꾸고 서버가 여전히 잔액 0을 이용권 없음으로 반환하는 상태를 남기지 않는다.

### Task 7: 관리자 허용 목록과 실제 실행 검사

**Files:** API `catalog/application/product-catalog.service.ts`, `catalog/infrastructure/typeorm-product-catalog.repository.ts`, `catalog/presentation/admin-catalog.controller.ts`, `operations/application/operations.service.ts` 및 관련 spec. Admin `features/portal/plans/plans.component.*`, Nest `src/core/auth/license-policy.service.ts`와 `src/modules/jobs/application/jobs.service.ts`, App `src/shell/store/plugin-detail/plugin-detail.component.*` 등 실제 허용 상태 소비자.

**Interfaces:** 기존 플러그인 ID와 관리자 저장 허용값을 재사용한다. mode+keys는 하나의 저장 결과로 적용하고 관련 유료 등급 포함 관계를 같은 잠금 순서에서 검증한다. 현재 유효 등급 허용과 기존 유효 크레딧 잔액을 별도로 검사한다.

- [x] Basic⊆Pro⊆Business 위반·동시 등급 수정·저장 중 실패에서 부분 저장이 남지 않는 시험을 추가한다. 새 dev의 기존 검증을 먼저 확인하고 중복 구현하지 않는다.
- [x] 미허용 플러그인의 설치·열기·준비는 가능하고 제한 대상 생성 요청은 차감 전에 거절되는 시험을 추가한다.
- [x] 큐 대기/재시작 중 등급 변경과 이미 차감한 작업의 반환·완료 멱등 처리를 시험한다. 완료/복구 경로를 새 실행 검사로 막지 않는다.
- [x] 목록 자동 동기화·카테고리/설치 순서 변경을 끼워 넣지 않고 실제 앱 실행 경계에 연결한다.

### Task 8: 제안 F의 공통 4카드와 API 데이터

**Files:** Client `features/public/pricing/plan-card/plan-card.component.*`, `pricing.component.*`, `billing-interval-toggle/billing-interval-toggle.component.*`, `features/public/landing/sections/pricing-section/pricing-section.component.*`, `core/api/models.ts`와 기존 catalog 서비스. API catalog의 공통 플러그인 고객용 이름/허용 표시정보.

**Interfaces:** `/#price`·`/pricing`은 같은 카드 컴포넌트를 사용한다. Free에는 ‘가입 시 1회 N크레딧’과 ‘가입 크레딧 유효기간: 가입일부터 D일’을 표시하고 월/연 선택으로 1회 혜택이 변하지 않는다. 카드의 같은 플러그인 행은 각 관리자 허용값으로 체크/X를 표시한다.

- [x] 테스트 설정의 N/D·가격·허용 목록을 변경하면 두 URL에서 함께 반영되고 월/연 토글에도 Free의 수량/유효기간이 유지되는 시험을 추가한다.
- [x] 목업의 150/14일/유료 가격·할인·허용 조합을 복사하지 않고 API 값을 연결한다. Free CTA는 유료 checkout에 보내지 않는다.
- [x] 제안 F의 4카드·강조 띠·같은 기능 행·구분선 아래 추가 구매·하단 충전 안내를 기존 Angular 구조/토큰에 적용한다.
- [x] 360/768/1280px, 긴 이름/목록·빈 목록·로딩/오류·랜딩 앵커와 카드 정렬을 브라우저에서 확인한다. 실제 화면 스크린샷으로 결과를 남긴다.

### Task 9: 통합 확인과 인계

- [x] API 관련 Jest 후 `npm test -- --runInBand`와 `npm run build`를 실행한다. Client/Admin은 `npx ng test --watch=false --browsers=ChromeHeadless`와 `npm run build`; Desktop은 변경된 node:test/Angular 및 빌드를 실행한다. 실행하지 못한 검증은 별도 기록한다.
- [x] 테스트용 격리 DB에서 코드 없음/유효 코드/무효/중지/상한/기존 회원/동시 가입/응답 유실을 검증하고 관리자 조회·원장·첫 잔액을 대조한다. 기존 DB 초기화는 하지 않는다.
- [x] 로컬 웹에서 Google 복귀 이후 동의→선택 코드→가입 완료→합산 잔액을 검증한다. 모의 Google 응답 시험과 실제 Google 로그인 검증을 구분해 기록한다.
- [x] Free 소진/만료 후 유지, 추가 구매 신규 자격, 현재 등급의 플러그인 실행, 기존 결제/환불 회귀와 제안 F 화면을 확인한다.
- [x] WORKBOARD·작업카드에 실제 완료/미검증을 기록한다. 요청 없는 commit/push/dev 병합·배포는 수행하지 않는다.

## 지금 확인된 내용

- 보존/작업 브랜치 준비와 기존 API 6파일 패치 보존은 Spec의 기록을 따른다.
- Google 신규 계정은 세션 없이 동의 화면으로 가며 앱 로그인도 같은 화면을 거친다. 프로모션 입력은 그 뒤에 추가하므로 Google 왕복 전 코드 보존 기능이 필요하지 않다.
- 구현과 로컬 모의 Google 이후 실제 API/DB/웹 검증을 완료했다. 실제 Google 제공자와 Toss망 검증·운영 배포는 수행하지 않았다.
- 기존 Google 콜백·가입 대기표·가입 완료·가입 저장의 관련 API 테스트는 4 suites / 34 tests 통과했다. 이는 구현 전 기준선 기록이며, 최종 신규 경로의 검증 수치는 위 구현/검증 기록을 따른다.
