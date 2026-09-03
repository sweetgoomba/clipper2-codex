# TossPayments PG release candidate 통합 로그

- 시작일: 2026-09-03 (Asia/Seoul)
- 상태: 준비 중
- 통합 브랜치: `integration/toss-payments-pg-20260903`
- 복제본 루트: `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/`
- 계획: `2026-09-03-toss-payments-pg-release-candidate-integration-plan.md`

## 범위 결정

- `meme-overlay-timeline-seek`: 제외
- `origin/feat/ai-video-generation-merge`: 제외
- 기존 PG worktree: 보존, 읽기 전용
- 서버 작업: Codex가 직접 접속하거나 실행하지 않음
- DB 작업: 현재 개발 DB와 5433/5434/5435에는 migration/write 금지
- 문서 위치: 새 계획·로그·체크리스트는 `.codex` 아래에만 작성

## Current State checkpoint

### 1. 기존 7개 PG worktree

| 저장소 | PG branch | HEAD | tracked/staged 상태 | 보존할 untracked |
|---|---|---|---|---|
| Web API | `feature/toss-payments-pg-integration` | `4ef22684115947df3aee124da18d94a0f896c97f` | clean | `docs/api/openapi.yaml.orig` |
| Web Customer | `feature/toss-payments-pg-integration` | `7f4d04a886c7529d5f430a3608cdcc78423d27dd` | clean | `build/` |
| Web Admin | `feature/toss-payments-pg-integration` | `dab857c45fdb76600a128f8008862b2b35b9afae` | clean | 없음 |
| Angular | `feature/toss-payments-pg-integration` | `f02bf2219bc88abfc14214d17acaf4160bbe8185` | clean | 없음 |
| NestJS | `feature/toss-payments-pg-integration` | `60a4f072e4ed53607664ae447c353f4f29271d61` | clean | 없음 |
| Electron | `feature/toss-payments-pg-integration` | `abdc5753741301f4bf22278a22ca8e20dc78ac24` | clean | 없음 |
| Infra | `feature/toss-payments-pg-integration` | `e6ae78f58b559cf3715f6acaecf6ac067a4e7930` | clean | 없음 |

### 2. 최신 `origin/dev`

| 저장소 | `origin/dev` HEAD |
|---|---|
| Web API | `727876c701c7d85302a46d48ea88e3734dd25471` |
| Web Customer | `4b361efc742db797e85848c5aea90eb1736194c5` |
| Web Admin | `eae522f4908c65a55680be09353dd95df2a71190` |
| Angular | `09ce2a3620e92e30e59f0091e9d0c4d3364cec8a` |
| NestJS | `2c7612b845ea31370ba792246f3e21b63db51640` |
| Electron | `301ca3403340a73010b24acab34e06418e8bb5a3` |
| Infra | `4d3202263d84de9d046a1abc6eb51826a47009ae` |

### 3. 최신 dev와 PG branch 차이

숫자는 `dev에만 있는 commit / PG에만 있는 commit`이다.

| 저장소 | 차이 | 단순 merge 예상 충돌 파일 수 | 통합 방식 |
|---|---:|---:|---|
| Web API | 57 / 139 | 9 | 전체 이력을 합치고 의미별로 해결 |
| Web Customer | 0 / 31 | 0 | 전체 merge |
| Web Admin | 10 / 21 | 3 | 전체 merge 후 양쪽 화면 보존 |
| Angular | 694 / 6 | 6 | 필요한 PG 동작만 선별 이식 |
| NestJS | 357 / 7 | 3 | 필요한 PG 동작만 선별 이식 |
| Electron | 50 / 3 | 0 | 필요한 PG 동작만 선별 이식 |
| Infra | 0 / 6 | 0 | 로컬 후보 설정으로 merge |

### 4. API에서 확인된 충돌

| 쉬운 분류 | 파일 | 원인과 보존 목표 |
|---|---|---|
| API 메뉴판 | `docs/api/openapi.yaml` | 스토리보드 API와 결제 API를 모두 보존 |
| 서버 시작 목록 | `src/app.module.ts` | 최신 AI 디렉터/스토리보드와 PG 모듈을 모두 등록 |
| DB 등록 목록 | `admin.datasource.ts`, `user.datasource.ts`, spec | 스토리보드 표/migration과 PG 표/migration을 모두 등록 |
| 이미지 검색 | `media-search.controller.ts` | 정확한 credential 고정과 과금 근거 기록을 함께 수행 |
| 작업·크레딧 | `operations.service.ts`, `operation-definitions` 및 spec | 무료 디렉터 동작과 새 유료 렌더링 장부를 함께 보존 |

### 5. 런칭에 포함할 다른 작업

- 포함됨을 확인: Angular UI foundation
- 포함됨을 확인: Angular/NestJS/Electron/Python 메모리 최적화
- 포함됨을 확인: API operator JWT 보강
- 명시적으로 제외: meme overlay timeline seek
- 명시적으로 제외: AI video generation merge

### 6. migration 확인

- 직접적인 새 파일명/timestamp 충돌은 없음.
- 최신 API `origin/dev`에는 Admin DB timestamp `1785100000000`을 공유하는 migration 두 개가 이미
  존재한다. 실제 runner 동작을 폐기 가능한 DB에서 확인해야 한다.
- 기존 데이터 삭제 위험:
  - `1786560000000-MigrateReviewPaymentsToTossPaymentsPg`: 기존 `payment_events`,
    `payment_orders`를 조건 없이 삭제한다.
  - `1786650000000-AddOperationPluginEntitlements`: 과거 `shortform.create` 실행과 연결된 구형
    장부 일부를 삭제한다.
  - `1786800000000-DropLegacyBilling`: 검증 후 legacy review 주문/이벤트를 삭제하고
    `credit_ledger`, `token_usage`, `licenses`, `purchase_requests`, `plans`를 drop한다.
  - 마지막 migration의 `down`은 표만 빈 상태로 다시 만들며 기존 행을 복원하지 못한다.
- 결론: 운영 또는 현재 개발 DB에서 실행 금지. 별도 데이터 보존·변환 절차가 확인되기 전까지
  release 위험으로 유지한다.

### 7. 인수인계 문서와 현재 상태의 차이

- 인수인계 이후 최신 `origin/dev`를 다시 fetch해 위 HEAD로 재확인했다.
- 원본 저장소 중 API/Angular/NestJS/Electron은 처음 확인 당시 `dev`가 아닌 meme 통합용
  브랜치가 checkout돼 있었다. Admin 원본은 `origin/dev`보다 2 commit 뒤였다.
- 사용자 결정에 따라 기존의 “새 worktree 생성” 방식은 폐기하고 “원본 `dev` 최신화 후 독립
  복제본 생성” 방식으로 변경했다.
- meme overlay와 AI video merge는 더 이상 후보가 아니라 명시적 제외 항목이다.
- 인수인계에서 강조한 `1786800000000` 외에도 `1786560000000`, `1786650000000`에서 기존 데이터
  삭제가 확인되어 위험 목록을 넓혔다.
- Infra의 실제 서버 확인·설정은 Codex가 수행하지 않는다. 사용자가 각 PC에서 직접 실행할 때
  명령과 판정 기준만 제공한다.

## `.codex` 기존 변경 checkpoint

- commit: `64731b8 docs: record Toss Payments PG implementation handoff`
- 포함: 이 세션 시작 전 존재한 PG 관련 문서 19개 변경
- 검증: `git diff --cached --check` 통과, credential 형태 정규식 검사에서 발견 없음
- 상태: commit 직후 `.codex` working tree clean, `origin/main`보다 1 commit 앞섬

## 저장소별 진행 기록

아래 항목은 작업할 때마다 갱신한다.

### Web API

- 상태: 시작 전
- 충돌 원인: Current State의 API 충돌 표 참고
- 보존 기능: 최신 스토리보드/AI 디렉터/credential 고정 + PG 계약/크레딧/결제/환불
- 해결 방식: 미정
- 실행한 테스트: 미실행
- 남은 위험: destructive migration, 중복 timestamp, 실제 Toss test-key 검증 미실행

### Web Admin

- 상태: 시작 전
- 충돌 원인: 최신 credential/화면 변경과 PG 운영 메뉴가 같은 mock/model/header를 수정
- 보존 기능: 최신 운영 화면 + PG 상품/결제/크레딧/환불 화면
- 해결 방식: 미정
- 실행한 테스트: 미실행
- 남은 위험: 미정

### Web Customer

- 상태: 시작 전
- 충돌 원인: Git 수준 충돌은 현재 없음
- 보존 기능: 최신 고객 화면 + PG 구매/구독/크레딧/환불 흐름
- 해결 방식: 미정
- 실행한 테스트: 미실행
- 남은 위험: API 계약과 브라우저 수동 검증

### Angular

- 상태: 시작 전
- 충돌 원인: PG branch 이후 최신 `dev` 구조가 크게 변경됨
- 보존 기능: 최신 UI/메모리/settings/plugin 구조 + 필요한 PG 연결
- 해결 방식: 오래된 branch 전체 merge 금지, 동작 단위 선별 이식
- 실행한 테스트: 미실행
- 남은 위험: 선별할 정확한 변경 범위

### NestJS

- 상태: 시작 전
- 충돌 원인: PG branch 이후 module/plugin/render 구조가 크게 변경됨
- 보존 기능: 최신 구조/메모리 최적화 + 최종 정책과 맞는 PG 연결
- 해결 방식: 동작 단위 선별 이식, 구독 기반 무료 기능 차단 제외
- 실행한 테스트: 미실행
- 남은 위험: API와 desktop 계약 차이

### Electron

- 상태: 시작 전
- 충돌 원인: Git 수준 충돌은 없지만 PG access gate가 최종 정책과 충돌 가능
- 보존 기능: 최신 Electron 구조 + 필요한 일반 결제 포털 연결
- 해결 방식: 정책에 맞는 변경만 선별 이식
- 실행한 테스트: 미실행
- 남은 위험: 과거 access gate를 제외했을 때 남는 유효 변경 확인

### Infra

- 상태: 시작 전
- 충돌 원인: Git 수준 충돌은 없지만 과거 3대 서버 가정과 현재 장비 구성이 다름
- 보존 기능: PG 배포에 필요한 로컬 설정 후보
- 해결 방식: 로컬 branch에만 merge, 서버에는 미적용
- 실행한 테스트: 미실행
- 남은 위험: `m2-db`, `m2-proxy`, `m2-stage`, `m4-prod`, `storage`별 실제 상태 미확인
