# TossPayments PG release candidate 통합 로그

- 시작일: 2026-09-03 (Asia/Seoul)
- 상태: Web API·Web Admin·Web Customer 통합 checkpoint 완료, Desktop 선별 이식 분석 중
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
| Angular | `fc9ae5e86b8b48af60ef91c4251adfc6b8964756` |
| NestJS | `b817034513d19adf1dfecba4a0b480518d9271f4` |
| Electron | `53cdb7d21996a758b260fb266f7a5e10d1f9bc69` |
| Infra | `4d3202263d84de9d046a1abc6eb51826a47009ae` |

### 3. 최신 dev와 PG branch 차이

숫자는 `dev에만 있는 commit / PG에만 있는 commit`이다.

| 저장소 | 차이 | 단순 merge 예상 충돌 파일 수 | 통합 방식 |
|---|---:|---:|---|
| Web API | 57 / 139 | 9 | 전체 이력을 합치고 의미별로 해결 |
| Web Customer | 0 / 31 | 0 | 전체 merge |
| Web Admin | 10 / 21 | 3 | 전체 merge 후 양쪽 화면 보존 |
| Angular | 702 / 6 | 6 | 필요한 PG 동작만 선별 이식 |
| NestJS | 370 / 7 | 3 | 필요한 PG 동작만 선별 이식 |
| Electron | 51 / 3 | 0 | 필요한 PG 동작만 선별 이식 |
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

- 인수인계 이후 최신 `origin/dev`를 다시 fetch해 위 HEAD로 재확인했다. 세션 도중 Angular는
  `09ce2a36`에서 `fc9ae5e8`로, NestJS는 `2c7612b`에서 `b817034`로, Electron은
  `301ca340`에서 `53cdb7d`로 더 전진했다. 새 commit은 렌더 재시도, 플러그인 수명주기,
  미디어 가져오기 안정화 관련이며 제외 대상으로 정한 meme/AI video merge는 아니다.
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

## 원본 최신화와 독립 복제본 checkpoint

- 원본 7개 저장소를 모두 `dev`로 전환했다.
- 각 로컬 `dev`에는 `origin/dev`에 없는 고유 commit이 0개임을 확인한 뒤 `--ff-only`로만
  최신화했다.
- 최신화 후 7개 원본은 모두 `HEAD == origin/dev`, working tree clean이다.
- 기존 PG worktree 7개는 branch와 HEAD가 처음 확인한 값 그대로다.
- API worktree의 `docs/api/openapi.yaml.orig`와 Customer worktree의 `build/`도 그대로 남아 있다.
- 복제본 7개를
  `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/` 아래에
  `--no-hardlinks`로 만들었다.
- 각 복제본에는 로컬 원본을 가리키는 `source`와 Git 서버를 가리키는 `origin` 두 remote가 있다.
- 각 복제본에서 실제 Git 서버의 `origin/dev`를 다시 fetch한 후
  `integration/toss-payments-pg-20260903` 브랜치를 만들었다.
- 7개 복제본 모두 integration HEAD와 `origin/dev`가 같고 working tree가 깨끗하다.
- 7개 복제본 모두 `source/feature/toss-payments-pg-integration`이 위 PG HEAD와 정확히 같다.
- 서버 접속, DB 접속, migration, 배포는 실행하지 않았다.

## 저장소별 진행 기록

아래 항목은 작업할 때마다 갱신한다.

### Web API

- 상태: 통합 및 로컬 자동 검증 완료
- integration commit: `f1517f35f83da69ead02c10dac9ff079ac2aaa00`
- merge 부모:
  - 최신 `origin/dev`: `727876c701c7d85302a46d48ea88e3734dd25471`
  - PG 전체 이력: `4ef22684115947df3aee124da18d94a0f896c97f`
- 충돌 원인:
  - OpenAPI: 최신 `dev`는 스토리보드·AI 디렉터·YouTube credential API를, PG는 상품·접근권한·
    크레딧·결제·환불 API를 추가했다.
  - AppModule: 최신 `dev`는 AI 디렉터 모듈을, PG는 스케줄러와 상품·접근권한·크레딧·결제·
    회원·대시보드 모듈을 등록했다.
  - datasource: 최신 `dev`는 AI 디렉터 migration과 참조분석 replay 표를, PG는 새 결제·구독·
    크레딧·환불 표와 migration을 등록했다.
  - 이미지 검색: 최신 `dev`는 승인 당시의 정확한 Naver credential ID/revision을 고정했고,
    PG는 유료 operation의 공급자 요청 시작·성공·실패 근거를 기록했다.
  - operation: 최신 `dev`는 폐기된 AI 디렉터 과금 정책을 숨겼고, PG는 구형 장부를 새
    CreditGrantsService 기반 차감·환급·근거 기록으로 바꿨다.
  - controller test 2개는 실제 사용하지 않는 삭제된 `BillingModule`을 “참조하지 않음” 검사만
    위해 import하고 있어 전체 테스트 시작을 막았다.
- 보존 기능:
  - 최신 스토리보드/AI 디렉터 전략·리서치·추론·참조분석 모듈과 API 계약
  - 사용자가 승인한 정확한 provider credential 고정
  - YouTube credential runtime-status 관리자 API
  - PG 상품·무료 체험·접근권한·크레딧·결제·구독·환불·관리자 대시보드
  - 입력 방식별 숏폼 3종과 하이라이트/베리에이션 유료 operation
  - AI 디렉터 준비 동작은 유료 operation에서 제외하고, 폐기된 DB 정책도 조회·수정·실행에서 제외
  - 삭제된 구형 Billing module·controller·entity는 되살리지 않음
- 해결 방식:
  - OpenAPI의 양쪽 최신 경로와 schema를 합쳤다. PG에서 삭제한 구형 관리자 plan API 설명은
    실제 controller/schema가 없어 제거하고, 최신 YouTube runtime-status API는 보존했다.
  - AppModule에 PG 모듈과 최신 AI 디렉터 모듈을 함께 등록하고 `BillingModule`은 제외했다.
  - Admin datasource는 양쪽 migration을 timestamp 순으로 등록했다. User datasource에는
    ReferenceAnalysisReplay와 UserOnboardingJob을 함께 등록했다.
  - 이미지 검색은 한 `executeSearch` 경로에서 credential 고정을 적용하고, operation run이 있으면
    같은 검색의 시작·성공·실패 근거를 기록하도록 합쳤다.
  - OperationsService는 PG의 새 credit 장부·transaction·evidence 흐름을 사용하면서 최신
    `ACTIVE_OPERATION_KEYS` 필터를 유지했다.
  - 구형 장부 구현이 삭제됐으므로 구형 장부 전용 테스트는 되살리지 않았다. 대신 새 장부 테스트와
    폐기된 AI 디렉터 과금 정책 차단 테스트를 함께 유지했다.
  - 삭제된 BillingModule을 부정 검사만 위해 import하던 controller 테스트는 module metadata의
    실제 import 이름을 검사하도록 바꿨다.
- 실행한 테스트:
  - 최신 `dev` 기준선: `npm test -- --runInBand --silent` → 134 suites, 1,180 tests 통과
  - 최신 `dev` 기준선: `npm run build` → 성공
  - 이미지 검색 TDD RED: exact credential + evidence 결합 테스트에서 2 failed, 5 passed
  - 이미지 검색 TDD GREEN: 같은 spec에서 7/7 통과
  - AppModule TDD RED: PG 모듈만 선택한 상태에서 최신 inference module 누락을 확인
  - AppModule GREEN: module metadata 테스트 2/2 통과
  - datasource TDD RED: 최신 Director migration과 ReferenceAnalysisReplay 누락을 확인
  - datasource GREEN: 2 suites, 5/5 통과
  - operation 정책·서비스: 2 suites, 28/28 통과
  - OpenAPI 첫 검사: 끊긴 구형 plan schema 참조 4건을 검출
  - OpenAPI 수정 후: 10 suites, 103/103 통과
  - 삭제된 BillingModule test import 수정 후: 2 suites, 27/27 통과
  - 최종 전체: `npm test -- --runInBand --silent` → 226 suites, 2,384 tests 통과
  - 최종 build: `npm run build` → 성공
  - Git 검사: unmerged 0, unstaged 0, `git diff --cached --check` 통과, commit 후 working tree clean
  - staged credential 형태 검사: 발견 0
- 남은 위험:
  - 현재 DB와 5433/5434/5435에는 migration을 실행하지 않았다.
  - `1785100000000` timestamp가 두 Admin migration에 이미 중복되어 있다. 폐기 가능한 DB에서 실제
    TypeORM 실행 결과를 확인해야 한다.
  - `1786560000000`, `1786650000000`, `1786800000000`의 기존 데이터 삭제와 변환 전략은 아직
    폐기 가능한 DB fixture로 검증하지 않았다.
  - Toss test key와 실제 webhook/결제/취소/환불은 이번 세션 범위상 실행하지 않았다.
  - `npm ci` audit 결과 10건(낮음 1, 보통 2, 높음 7)이 보고됐다. 통합 범위를 벗어나는 자동
    `npm audit fix`는 실행하지 않았다.

### Web Admin

- 상태: 통합 및 로컬 자동 검증 완료
- integration commit: `ed1b5a4a7ffc2c541d37116ecf4cf21bc61255ef`
- merge 부모:
  - 최신 `origin/dev`: `eae522f4908c65a55680be09353dd95df2a71190`
  - PG 전체 이력: `dab857c45fdb76600a128f8008862b2b35b9afae`
- 충돌 원인:
  - API mock interceptor: 최신 `dev` 쪽 충돌 구간은 비어 있었고, PG는 상품·접근권한·크레딧·
    결제·환불·복구용 mock API를 추가했다.
  - 공용 model: PG는 중단된 operation 복구 model을 추가했고, 최신 `dev`는 Gemini API key
    provider를 지원했다.
  - 공용 header test: 최신 `dev`는 API key·버전·운영자 메뉴를 검사했고, PG는 상품·결제·환불·
    복구 운영 메뉴를 검사했다.
- 보존 기능:
  - 최신 API key 화면과 Naver/OpenAI/Gemini/YouTube provider 계약
  - 최신 버전·운영자 메뉴
  - PG 상품·회원 접근권한·크레딧·결제 이행·결제 운영·환불·operation 복구·구독 갱신 정책 화면
  - PG가 새 catalog/access 흐름으로 교체한 구형 승인·license request 화면은 되살리지 않음
- 해결 방식:
  - PG mock endpoint 전체를 유지했다.
  - `ApiKeyProvider`에 최신 `gemini`를 포함하고 PG의 operation 복구 model도 유지했다.
  - header 테스트는 어느 한쪽을 버리지 않고 최신 메뉴 검사와 PG 운영 메뉴 검사를 합쳤다.
  - 나머지 비충돌 파일은 PG 전체 merge 결과를 유지하고 route·화면 테스트로 연결 여부를 검증했다.
- 실행한 테스트:
  - 최신 `dev` 기준선: 전체 Karma 227/227 통과
  - 최신 `dev` 기준선: `npm run build` 성공
  - 충돌 관련 집중 검사: mock interceptor, header, portal routes, API key view-model 54/54 통과
  - 최종 전체: `npm test -- --watch=false` → 366/366 통과
  - 최종 build: `npm run build` → 성공
  - Git 검사: unmerged 0, unstaged 0, 충돌 표식 0, `git diff --cached --check` 통과,
    commit 후 working tree clean
  - 저장소 내 Toss key 형태 검사: 발견 0
- 남은 위험:
  - build 초기 bundle이 557.06 kB로 500 kB 예산을 57.06 kB 초과한다. build는 성공했지만
    런칭 성능 검토 항목으로 남긴다.
  - 실제 API와 연결한 관리자 브라우저 시나리오 및 권한별 수동 검증은 아직 하지 않았다.
  - `npm ci` audit 결과 48건(낮음 3, 보통 10, 높음 34, 치명적 1)이 보고됐다. 통합 범위를
    벗어나는 자동 `npm audit fix`는 실행하지 않았다.

### Web Customer

- 상태: 통합 및 로컬 자동 검증 완료
- integration commit: `bedafa38e02b4c800fc50efb086827eff4579e90`
- merge 부모:
  - 최신 `origin/dev`: `4b361efc742db797e85848c5aea90eb1736194c5`
  - PG 전체 이력: `7f4d04a886c7529d5f430a3608cdcc78423d27dd`
- 충돌 원인:
  - PG branch가 최신 `dev`의 직계 후손이라 Git 수준 충돌은 없었다.
  - 기능 수준에서는 공개 결제 화면을 인증된 portal 안으로 옮기고, 구형 수동 구매·license·plan API를
    새 catalog/access/credits/payments API로 교체하는 큰 변경이다.
- 보존 기능:
  - 최신 `dev`의 로그인·다운로드·법률 고지·계정 등 고객 화면
  - 상품 catalog와 월/연간 가격 선택
  - 인증 후 Toss 결제창, 성공·취소 결과 복구, 결제 수단 변경 결과
  - 구독 upgrade 견적, 갱신·복구 상태, 결제 이력
  - 유료 구독자용 선불 크레딧 충전과 source별 크레딧 잔액
- 해결 방식:
  - PG 31개 commit 전체 이력을 no-ff merge했다.
  - 구형 수동 purchase, license request, plan API와 중복 공개 checkout/result 화면은 PG 최종 정책대로
    제거된 상태를 유지했다.
  - 실제 API 호출 대신 서비스·route·가격·checkout 계약 테스트를 먼저 집중 검증한 뒤 전체 회귀를
    실행했다.
- 실행한 테스트:
  - 최신 `dev` 기준선: 전체 Karma 93/93 통과
  - 최신 `dev` 기준선: `npm run build` 성공
  - PG API·route·가격·checkout 집중 검사: 64/64 통과
  - 최종 전체: `npm test -- --watch=false` → 226/226 통과
  - 최종 build: `npm run build` → 성공, 초기 bundle 493.00 kB
  - Git 검사: unmerged 0, unstaged 0, 충돌 표식 0, `git diff --cached --check` 통과,
    commit 후 working tree clean
  - Toss key 형태 7건은 모두 spec/mock에 있는 최대 15자의 짧은 placeholder이며 실제 key 형태로
    의심되는 긴 값은 0건
  - 기존 PG worktree의 untracked `build/`가 그대로 남아 있고 branch/HEAD도 변하지 않았음을 재확인
- 남은 위험:
  - Web API integration 후보를 실제로 연결한 브라우저 E2E는 아직 하지 않았다.
  - Toss SDK는 mock/test 계약만 검증했으며 라이브 결제·환불은 실행하지 않았다.
  - `npm ci` audit 결과 49건(낮음 3, 보통 10, 높음 34, 치명적 2)이 보고됐다. 통합 범위를
    벗어나는 자동 `npm audit fix`는 실행하지 않았다.

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
