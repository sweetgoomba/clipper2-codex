# 캠페인 참여 가능 조건과 혜택 지급 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. 아래 checkbox로 진행을 추적한다.

**Goal:** 승인된 참여 대상3개/추가 조건2개를 실제 관리자·API·가입/회원 지급에 연결하고 이용권형 크레딧의 월별 만료를 통일한다.
**Architecture:** 혜택 종류 credits/access와 audience(new/existing/all), eligibilityConditions(no_active_access/no_paid_history)를 별도로 저장한다. 신규 여부는 신뢰된 가입 작업에서만 제공한다. 단일 정책 함수와 공통 지급 함수를 가입/회원 경로에서 재사용한다.
**Tech Stack:** NestJS/TypeORM/PostgreSQL16, Angular22/Material.
**Spec:** 02-campaign-create-eligibility-mockup.md 최신 목업 및 사용자 승인(참여 대상에 기존 회원만 추가), 02-campaign-eligibility-followup-candidates.md 이번 확정.

## Global Constraints

- 기존 feat/signup-credit-promotion-free-20261102 격리 checkout 재사용. 기존 미커밋 변경 보존, 커밋/푸시/병합/배포 없음.
- 문서는 .codex에만. 목업 상단 탭 없음, 별도 참여 시점 입력 없음. 기존 app-modal drawer/Material 재사용.
- 지급량/독립 유효일수는 크레딧형에서 한 줄 반반. 이용권형은 등급/기간만, 월별 만료.
- 신규 전용은 조건을 비우고 비활성화하되 숨기지 않는다. 추가 조건은 AND. 회원당 캠페인1회와 코드별 상한 유지.
- Free는 활성 이용권 미보유 조건을 통과. 크레딧형은 설정하지 않은 이용권 중복 제한 없음. 이용권형 구조적 중복 방지 유지.
- 최초 가입 보너스·코드 지급의 내구성/멱등성/실패 복구를 유지. 성과/예약/XLSX 재도입 없음.
- API4340, 웹4241/4242, DB15438, 별도 앱/기존 다른 작업 보존. DB 초기화 없음.

## Review Focus

- 신규 가입 과정에서 user행이 이미 생성된 상태여도 신규 전용 통과; 일반 회원 요청은 신규로 위장 불가.
- 가입 후 크레딧형 지급은 기존 유료 이용권을 건드리지 않고 정확한 지급분/원장만 생성.
- 코드 상한/중복/재시도/실패 시 전체 혜택의 원자성과 기존 signup-promotion 증명 키 유지.
- 두 조건 동시 AND, Free/프로모션/관리자 활성/과거 유료 만료 판정과 가입 전용 조건 정규화.
- 최초/매월 지급 만료가 월말·최종 짧은 기간에도 접근 종료를 넘지 않음.

### Task 1: 계약·참여 정책·마이그레이션

**Files:** API promotions domain/presentation/repository, OpenAPI, admin datasource/new migration.
**Interfaces:** audience new/existing/all, eligibilityConditions no_active_access/no_paid_history, benefitKind credits/access. Access creditValidityDays=null, credits positive days.
- [x] 기존 테스트에9개 유효 조합/신규·기존 경계/현재 활성 vs 예정 이용권/paid 이력 RED 추가·실행.
- [x] 계약·DTO·도메인·DB 매핑과 신규 마이그레이션 구현. 기존 signup_credits는 credits+new로 변환, paid는 no_paid_history, admin 과거 옵션 제거.
- [x] 대상 tests GREEN. 신규 전용+추가 조건 동시 저장은 검증으로 거부.

### Task 2: 가입·회원 공통 지급과 만료

**Files:** promotions/application 공통 지급 helper, signup provisioner, promotions service, monthly credit service/domain anniversary helper.
**Interfaces:** bound ports/transaction 내부 공통 issuePromotionBenefit; signup-promotion:user 키 유지. 기존 member redeem 응답 accessGrantId nullable.
- [x] RED: 일반 크레딧형+활성 Pro, 기존 전용 signup 거절, 신규 전용 member 거절, access signup, 지급 롤백/멱등, 최초/월별 만료.
- [x] 공통 지급과 trusted signup 정책 연결. 기존 가입내구 잠금 순서 유지. 유료 동일 월별 만료, 마지막 period access end cap.
- [x] 정책/지급/signup durability와 만료 대상 tests GREEN.

### Task 3: 실제 관리자 및 회원 계약 소비

**Files:** Admin promotions API types/mock/component/template/scss/tests/audit labels; Client promotion/auth types/dialog/copy/tests.
**Interfaces:** Task1 계약 그대로; 실제 Material radio3개, 추가 checkbox2개, 요약.
- [x] RED: 신규 전용 disabled/clear, 기존 전용 payload, credits 두 칸, access days 미표시/null, 변경 없는 수정 저장 disabled.
- [x] 관리자 drawer 구현, 목록/상세 조건 설명과 감사 표시 갱신. 가입·회원 UI는 credits/access 계약과 오류를 소비.
- [x] 단일 Karma 순차 실행, 각 build 및 색상 검사 GREEN.

### Task 4: 통합 검증·로컬 반영·최종 검토

**Files:** 기존 로컬 runtime 관리 및 .codex 기록/인계.
- [x] API 전체 tests/build, Admin/Client 전체 tests/build. 전용 PostgreSQL 마이그레이션/가입·회원·회수·상한 실제 통합 검증.
- [x] 자신의4340 API만 안전 재시작, 웹 복사 bundle만 갱신(4241/4242 서버 유지), 브라우저 실제 drawer/저장/수정 및 조건 동작 확인.
- [x] fresh final review, 중요 발견 RED→GREEN 수정, 증거/선택/한계를 기록. WORKBOARD/NEXT 보류 해제·진행/완료 상태 갱신.

## 실행 재량

사용자의 명시적 구현 진행 지시로 별도 재승인 질문 없이 inline 실행한다. commit 지시 없음이 스킬의 task commit 단계보다 우선한다. DB 기록은 삭제하지 않고 새 마이그레이션으로 변환한다. 새 발급분 만료는 새 규칙을 따르며 기존 지급분/금융 이력은 소급 변경하지 않는다(월별 배치 경로의 기존 별도 일수 예외는 제거).
