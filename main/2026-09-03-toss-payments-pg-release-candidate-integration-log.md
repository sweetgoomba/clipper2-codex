# TossPayments PG release candidate 통합 로그

- 시작일: 2026-09-03 (Asia/Seoul)
- 상태: 7개 저장소 integration 후보 통합·선별 이식·로컬 자동 검증 완료, 기존 데이터 보존 전략이
  정해질 때까지 DB migration은 배포 차단
- 통합 브랜치: `integration/toss-payments-pg-20260903`
- 작업 위치: 각 원본 저장소의 위 integration 브랜치 checkout
- 임시 복제본: 초기 작업 위치를 잘못 해석해 만든
  `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/`은 백업으로만 보존하며
  작업 정본이 아니다. 사용자 승인 없이 삭제하거나 사용하지 않는다.
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
| Angular | `da0a2029d19fe3781b2a4d9e467f9c4001d00682` |
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
| Angular | 704 / 6 | 6 | 필요한 PG 동작만 선별 이식 |
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
  존재한다. 폐기 가능한 빈 PostgreSQL 16 DB에서 TypeORM runner를 실행한 결과 두 migration이
  datasource 등록 순서대로 모두 적용됐다.
- 빈 DB 전체 적용 결과: User 9개, Admin 54개, Release 2개가 성공했고, 같은 DB에 두 번째로
  실행했을 때 세 연결 모두 `No pending migrations`였다.
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

### 6-1. 폐기 가능한 DB 검증 checkpoint

- 사용 환경:
  - 로컬 `postgres:16-alpine` 임시 container
  - host에는 `127.0.0.1:55439`로만 노출
  - 현재 개발 DB port인 5433/5434/5435는 사용하지 않음
  - 빈 검증 DB 3개와 구형 데이터 fixture DB 1개만 사용
  - 검증 종료 후 `--rm` container를 중지해 위 폐기용 DB 4개를 모두 제거함
- 빈 DB 검증:
  - User migration 9개 전체 적용 성공
  - Admin migration 54개 전체 적용 성공
  - Release migration 2개 전체 적용 성공
  - 세 DB 모두 재실행 시 pending migration 0개
  - Admin의 동일 timestamp `1785100000000` 두 migration은
    `EnforceSingleYoutubeCredential` 다음 `SeedShortformDirectorStrategyOperationPolicy` 순으로 둘 다 기록
  - migration 직후 필수 유료 operation policy는 `variation.render` 1개만 존재했다. 실제 앱 시작 때
    실행되는 `OperationPolicySeeder`를 같은 DB에 적용하자 숏폼 3종, 하이라이트 2종, 베리에이션 1종
    총 6개가 모두 생성됐다. 따라서 향후 준비 검증은 migration뿐 아니라 앱 시작 seed 결과도 확인해야 함
- 구형 데이터 fixture 검증:
  - 구형 무통장 주문 1건과 event 1건을 넣은 뒤 `1786560000000`을 적용하자 둘 다 0건이 됨
  - 구형 `shortform.create` 실행 1건과 차감 장부 1건을 넣은 뒤 `1786650000000`을 적용하자 둘 다
    0건이 되고 새 입력 방식별 policy 3개가 생성됨
  - 구형 purchase request, license, token usage, credit ledger를 넣은 뒤 `1786800000000`까지 적용하자
    `plans`, `purchase_requests`, `licenses`, `token_usage`, `credit_ledger` 표 자체가 모두 없어짐
  - `1786800000000`의 `down`을 실행하자 위 표는 다시 생겼지만 모든 행 수가 0이어서 데이터 복원은
    되지 않음
- 판정:
  - 새 빈 DB 설치 순서, 반복 실행, 앱 시작 operation seed는 검증됨
  - 기존 데이터가 있는 DB로 바로 올리는 것은 안전하지 않음
  - 기존 무통장 주문, 이용권, 토큰 사용량, 크레딧 장부를 새 구조로 옮기거나 보관하는 migration과
    검증 기준이 별도로 승인되기 전에는 stage/prod 배포 후보로 승격할 수 없음

### 7. 인수인계 문서와 현재 상태의 차이

- 인수인계 이후 최신 `origin/dev`를 다시 fetch해 위 HEAD로 재확인했다. 세션 도중 Angular는
  `09ce2a36`에서 `fc9ae5e8`로 전진한 뒤 다시 `da0a2029`로 전진했다. NestJS는 `2c7612b`에서
  `b817034`로, Electron은 `301ca340`에서 `53cdb7d`로 더 전진했다. Angular의 마지막 변경은
  Variation 상세 패널의 긴 파일명 칩 표시 수정이다. 이 변경들은 제외 대상으로 정한 meme/AI video
  merge가 아니다.
- 원본 저장소 중 API/Angular/NestJS/Electron은 처음 확인 당시 `dev`가 아닌 meme 통합용
  브랜치가 checkout돼 있었다. Admin 원본은 `origin/dev`보다 2 commit 뒤였다.
- 사용자 결정에 따라 새 worktree와 별도 복제본을 작업 장소로 쓰지 않고, 원본 저장소의
  `dev`를 최신화한 뒤 같은 원본 저장소에 integration 브랜치를 만들어 작업한다.
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

## 원본 최신화와 작업 위치 수정 checkpoint

- 원본 7개 저장소를 모두 `dev`로 전환했다.
- 각 로컬 `dev`에는 `origin/dev`에 없는 고유 commit이 0개임을 확인한 뒤 `--ff-only`로만
  최신화했다.
- 최신화 직후 7개 원본은 모두 `HEAD == origin/dev`, working tree clean이었다.
- 기존 PG worktree 7개는 branch와 HEAD가 처음 확인한 값 그대로다.
- API worktree의 `docs/api/openapi.yaml.orig`와 Customer worktree의 `build/`도 그대로 남아 있다.
- 처음에는 지시를 잘못 해석해 별도 임시 복제본 7개에서 통합과 검증을 수행했다.
- 잘못을 확인한 뒤 각 임시 복제본의 최종 integration commit SHA를 검사하고, 로컬 fetch로 그
  동일 commit을 각 원본 저장소에 가져왔다. 각 원본 저장소에서
  `integration/toss-payments-pg-20260903` 브랜치를 그 commit에 만들고 checkout했다.
- 현재 작업 정본은 원본 저장소 7개다. 각 원본의 integration HEAD는 아래 저장소별 최종 HEAD와
  같고 working tree가 깨끗하다.
- 원본 저장소의 로컬 `dev` ref는 checkout 상태와 별개로 계속 `origin/dev`와 정확히 같다.
- 임시 복제본은 삭제하지 않고 백업으로만 남겼으며, 이후 작업에는 사용하지 않는다.
- 작업 위치 수정 후 다시 fetch하자 Angular `origin/dev`가 `fc9ae5e8`에서 `da0a2029`로 전진한 것이
  확인됐다. 결제·meme·AI video와 무관한 Variation 파일명 칩 표시 수정이었고 PG 이식 파일과
  겹치지 않았다. 이를 원본 Angular integration 브랜치에 충돌 없이 merge하고 로컬 `dev` ref도
  `da0a2029`로 fast-forward했다.
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
  - 현재 DB와 5433/5434/5435에는 migration을 실행하지 않았고 앞으로도 데이터 보존 절차 승인 전에는
    실행하면 안 된다.
  - 동일 timestamp 두 migration은 빈 DB에서 정상 적용됐지만, 장기적으로 migration 이름·적용 순서를
    운영 점검표에서 함께 확인해야 한다.
  - `1786560000000`, `1786650000000`, `1786800000000`의 데이터 삭제는 fixture에서 실제로 재현됐다.
    기존 무통장 주문·이용권·토큰 사용·구형 크레딧 기록을 새 구조로 옮기는 별도 설계와 테스트가
    release blocker다.
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

- 상태: 필요한 PG 동작 선별 이식 및 로컬 자동 검증 완료
- integration commits:
  - `f7c7897f feat: forward-port desktop credit integration`
  - `7b56e2a3 fix: label account-level credit history accurately`
  - `9504e098 merge: refresh Angular integration from latest dev`
- 처음 출발한 `origin/dev`: `fc9ae5e86b8b48af60ef91c4251adfc6b8964756`
- 현재 포함한 최신 `origin/dev`: `da0a2029d19fe3781b2a4d9e467f9c4001d00682`
- 충돌 원인:
  - 오래된 PG branch 뒤로 최신 `dev`가 694 commit 전진해 화면, 플러그인, 렌더링, 메모리 관리
    구조가 크게 달라졌다. 따라서 branch 전체를 merge하면 최신 데스크톱 기능을 과거 구조로 되돌릴
    위험이 있다.
  - 최신 Angular는 폐기된 로컬 `/licenses/current`, `/operations/ledger` 응답 모양을 화면에 쓰고
    있었지만, 현재 Web API는 `/access/current`, `/credits/summary`, `/credits/ledger`로 나뉘어 있다.
  - 과거 PG 구현은 플랜별 플러그인 사용 제한을 전제로 했지만 최종 정책은 모든 플랜의 플러그인
    구성이 같고, 크레딧이 들지 않는 기능은 결제 상태와 무관하게 사용할 수 있어야 한다.
  - 과거에는 숏폼 생성 전체가 `shortform.create` 하나였지만 현재 API는 URL·본문 붙여넣기·프롬프트
    생성을 서로 다른 과금 작업으로 구분한다.
- 보존 기능:
  - 최신 `dev`의 UI foundation, settings/home 화면 구조, 메모리 최적화, 플러그인 수명주기와
    설치 상태 확인 구조
  - 무료 기능과 플러그인이 구독 여부 때문에 막히지 않는 최종 정책
  - 현재 Web API가 반환하는 이용 권한, 사용 가능/보류/출처별 크레딧, 크레딧 변동 내역
  - Customer의 현재 요금제, 결제 내역, 크레딧 화면으로 가는 링크
  - URL·붙여넣기·프롬프트별 정확한 숏폼 과금 키
- 해결 방식:
  - 오래된 PG branch는 merge/cherry-pick하지 않고 현재 파일에 필요한 동작만 TDD로 옮겼다.
  - 화면이 사용하는 `CurrentLicenseSummary` 이름은 대규모 UI 재작성과 회귀를 피하기 위한 내부
    adapter로 유지하되, 실제 호출은 `/access/current`와 `/credits/summary`를 동시에 읽도록 바꿨다.
  - 화면에는 사용 가능 크레딧, 보류 크레딧, 전체 보유량과 원천별 잔액을 정확한 이름으로 표시한다.
  - 최근 내역은 현재 `/credits/ledger` 응답을 기존 최신 UI의 표시 model로 변환한다.
  - 새 장부 응답에는 기기 세션이 없으므로 모든 행을 `알 수 없는 기기`로 오해하게 표시하지 않고
    `계정 크레딧`으로 표시한다. 기존 세션 정보가 실제로 있는 행은 원래 기기 이름을 유지한다.
  - 요금제 버튼은 `/pricing`, 결제 내역은 `/app/payment-history`, 전체 크레딧 내역은
    `/app/credits`로 연결했다.
  - 숏폼 project의 저장된 입력 방식에 따라 `shortform_url.create`, `shortform_paste.create`,
    `shortform_prompt.create` 중 하나를 선택한다.
  - 플러그인 entitlement guard는 추가하지 않았고 기존 route의 설치 여부 guard만 유지했다.
- 실행한 테스트:
  - 최신 `dev` 기준선: 전체 Karma 4,254/4,254 통과
  - 최신 `dev` 기준선: style 6/6 통과, `npm run build` 성공
  - TDD RED: 현재 API 응답·원천별 잔액·새 포털 경로·대문자 `INSUFFICIENT_CREDITS`·숏폼별
    operation key를 기대하도록 바꾸자 구현 전 TypeScript/expectation 실패 확인
  - 첫 GREEN: 구현 후 관련 테스트 328개 통과, 새 버튼 이름을 반영하지 않은 기존 expectation 2개 실패
  - expectation 수정 후 집중 검사: 357/357 통과
  - 직접 코드 리뷰 RED: 세션 없는 새 장부 행과 홈 빈 상태의 잘못된 문구 2건 실패 확인
  - 표시 수정 집중 검사: 16/16 통과
  - 수정 후 최종 전체: 4,256/4,256 통과
  - 최종 style: 6/6 통과
  - 최종 build: `npm run build` 성공, 초기 bundle 253.14 kB
  - 최신 `origin/dev` 갱신 후 Variation 상세 패널 집중 검사: 20/20 통과
  - 최신 `origin/dev` 갱신 후 전체: 4,262/4,262 통과
  - 최신 `origin/dev` 갱신 후 style: 6/6 통과
  - 최신 `origin/dev` 갱신 후 build: 성공, 초기 bundle 253.14 kB
  - 샌드박스 안에서 esbuild deadlock으로 두 차례 종료됐지만 같은 Node 22 명령을 샌드박스 밖에서
    실행하자 집중/전체 테스트와 build가 모두 통과했다.
  - Git 검사: unmerged 0, 충돌 표식 0, `git diff --check` 통과, commit 후 working tree clean
- 남은 위험:
  - Web API integration 후보 및 NestJS integration 후보를 실제로 함께 띄운 데스크톱 E2E는 아직
    실행하지 않았다.
  - 원천별 잔액이 화면 폭이 좁은 실제 패키지 창에서 어떻게 줄바꿈되는지는 수동 확인이 필요하다.
  - `npm ci` audit 결과 17건(보통 8, 높음 9)이 보고됐다. 자동 fix는 실행하지 않았다.

### NestJS

- 상태: 필요한 PG 동작 선별 이식 및 로컬 자동 검증 완료
- integration commits:
  - `9f5b411 feat: forward-port desktop access and credit proxies`
  - `78270ec test: retire legacy desktop license proxy contract`
  - `f306519 feat: forward-port durable desktop operation billing`
  - `5b50588 fix: retire stale desktop operation ledger proxy`
- 출발점인 최신 `origin/dev`: `b817034513d19adf1dfecba4a0b480518d9271f4`
- 충돌 원인:
  - 오래된 PG branch 전체를 합치면 최신 플러그인 수명주기, 렌더 재시도, 미디어 가져오기와 메모리
    최적화를 과거 구현으로 덮을 위험이 있다.
  - 데스크톱 로컬 서버에는 폐기된 license proxy가 남아 있었고 현재 Web API의 access/credit API와
    주소 및 응답 형식이 달랐다.
  - 과거 PG 플러그인 접근 차단은 모든 플랜에서 같은 플러그인을 제공한다는 최종 정책과 맞지 않는다.
  - 실제 크레딧 차감 뒤 성공·실패를 판단할 근거가 일부 렌더 경로에 영구 저장되지 않았고,
    숏폼의 작업 키도 입력 방식별 현재 API 계약과 달랐다.
- 보존 기능:
  - 최신 `dev`의 plugin/render/job 구조, 렌더 재시도와 메모리 최적화
  - 사용자의 bearer token을 저장하지 않고 요청마다 Web API로 전달하는 인증 경계
  - 현재 Web API의 access, credit summary/grants/ledger 계약
  - 대사 하이라이트, 댄스 하이라이트, 숏폼 렌더, 베리에이션 렌더의 차감·성공·실패 기록
  - 무료 기능을 결제 상태로 차단하지 않는 최종 정책
- 해결 방식:
  - 오래된 PG branch를 merge하지 않고 현재 구조에 새 `AccessModule`, `CreditsModule`과 proxy를
    추가하고 폐기된 `LicensesModule`을 제거했다.
  - operation 시작 요청에는 실제 공급자/렌더 작업을 확인할 수 있는 evidence를 필수로 보내고,
    완료·실패 때 같은 run을 갱신하도록 각 workflow에 연결했다.
  - 숏폼은 저장된 source mode에 따라 URL·붙여넣기·프롬프트별 operation key를 선택한다.
  - quote 거절 사유와 ledger 주소를 현재 API의 `INSUFFICIENT_CREDITS`, `/credits/ledger`로 맞췄다.
  - 새 `/credits/ledger` proxy와 동시에 남아 있던 구형 `/operations/ledger` route 및 구형 반환 타입은
    제거해 장부 계약을 한 경로로 통일했다.
  - 과거 플러그인 entitlement/라이선스 차단 코드는 의도적으로 이식하지 않았다.
- 실행한 테스트:
  - 최신 `dev` 기준선 build: 성공
  - 최신 `dev` 원본 전체 test에서 `template-builder-no-s3-storage.test.js`는 untracked
    `.env.packaged` 부재로 실패하고, `web-api-client.test.js`는 다섯 번째 테스트의 Promise가
    끝나지 않아 뒤 10개가 취소되는 기존 문제를 확인
  - access/credit proxy TDD: 3/3 통과
  - operation/evidence/shortform 집중 검사: 최종 52/52 통과
  - 구형 operation ledger 제거 TDD RED: route/service 2건 실패 확인, 구현 제거 후 관련 6/6 통과
  - 위 두 기준선 문제 파일만 제외한 수정 후 최종 전체: 2,239/2,239 통과
  - 최종 build: `npm run build` 성공
  - 샌드박스 안 전체 실행은 local loopback listen 권한(`EPERM`)으로 실패했으나, 같은 명령을
    샌드박스 밖에서 실행해 2,239개 전부 통과했다.
  - source 검사: 폐기된 `no_active_license`, `shortform.create` 상수, `/operations/ledger`,
    `/licenses/current` 참조 없음
  - Git 검사: 세 checkpoint commit 후 working tree clean
- 남은 위험:
  - 기준선의 `.env.packaged` 의존 테스트와 pending Promise 테스트는 이번 PG 범위에서 임의로 고치지
    않았다. 따라서 두 파일을 포함한 원문 그대로의 전체 test 명령은 아직 green이 아니다.
  - Web API integration 후보를 실제로 연결한 HTTP E2E와 실패 후 실제 크레딧 반환 확인은 하지 않았다.
  - `npm ci` audit 결과 5건(보통 1, 높음 4)이 보고됐다. 자동 fix는 실행하지 않았다.

### Electron

- 상태: 유효한 PG test 계약 선별 이식 및 로컬 자동 검증 완료
- integration commit: `578a12a test: use current portal handoff path`
- 출발점인 최신 `origin/dev`: `53cdb7d21996a758b260fb266f7a5e10d1f9bc69`
- 충돌 원인:
  - PG branch의 주 구현은 Electron IPC에서 플러그인 실행과 모델 다운로드 전에 Web API access를
    검사하고 차단한다. 이는 모든 플랜의 플러그인 구성이 같고 무료 기능은 결제 상태와 무관하게
    쓸 수 있어야 한다는 최종 정책과 충돌한다.
  - PG branch의 나머지 변경은 포털 URL 테스트가 삭제된 `/app/purchase`를 예시로 쓰지 않고 현재
    `/app/credits`를 사용하도록 고친 test-only commit이다.
- 보존 기능:
  - 최신 `dev`의 Electron 보안, 프로세스/플러그인 수명주기, 메모리·로그 최적화
  - renderer가 요청한 상대 경로만 허용하고 일회용 handoff code로 Customer 포털을 여는 기존 bridge
  - 결제 상태와 무관한 플러그인 실행 및 명시적 모델 설치 동작
  - 현재 Customer `/app/credits` 경로를 사용하는 포털 handoff 계약
- 해결 방식:
  - `50610d9 feat: enforce plugin access in electron ipc`와 그 access authorizer/tests는 이식하지 않았다.
  - `7f5d4d3 test: use current portal handoff path`만 cherry-pick했다. bridge 구현은 원래 임의의 안전한
    상대 경로를 지원하므로 source 변경은 필요하지 않았다.
  - 최종 검사에서 `src/main/access/web-access-authorizer.ts`와 access authorizer 참조가 없음을 확인했다.
- 실행한 테스트:
  - 최신 `dev` 기준 build: `npm run build` 성공
  - 최초 test/build 병렬 실행은 테스트가 `dist-electron` 생성 전에 시작해 module-not-found로 실패;
    이 저장소는 build 뒤 test 순서가 필요함을 확인
  - Electron binary 최초 lazy install 때 병렬 test worker가 같은 압축 해제 경로를 사용해 6건 실패;
    단일 설치가 끝난 뒤 재실행해 해소
  - 포털 bridge 단독: 변경 전 5/5, 변경 후 포함한 핵심 검사 22/22 통과
  - 최종 build: `npm run build` 성공
  - 패키징 fixture 파일 하나를 제외한 전체: 341/341 통과
  - 원문 `npm test`: 347/348 통과, 아래 환경 의존 패키징 fixture 1건 실패
  - Git 검사: 최종 정책과 충돌하는 access authorizer 없음, commit 후 working tree clean
- 남은 위험:
  - `storyboard-document-only-packaging.test.mjs`의 fresh staged resources 검사는 검증 당시 임시
    복제본 옆의 Nest `dist/bundled`와 커밋하지 않는 `.env.packaged`를 요구해 실행 환경에서 1건
    실패했다. secret 파일을 임의 생성하거나 출력하지 않았다.
  - 실제 Angular → Electron → Customer desktop handoff 브라우저 E2E는 아직 실행하지 않았다.
  - 앱 패키징, 서명, notarization, 실행은 이번 세션 범위에서 하지 않았다.

### Infra

- 상태: 로컬 integration branch merge 및 정적 검증 완료, 실제 적용은 보류
- integration commit: `fa92eda merge: integrate Toss Payments PG infrastructure candidate`
- merge 부모:
  - 최신 `origin/dev`: `4d3202263d84de9d046a1abc6eb51826a47009ae`
  - PG 전체 이력: `e6ae78f` (`feature/toss-payments-pg-integration`)
- 충돌 원인:
  - Git 파일 충돌은 없었다. PG branch가 최신 `dev`의 직계 후손이기 때문이다.
  - 운영 의미의 충돌은 남아 있다. PG runbook 일부는 과거 개발 배포 배치를 전제로 하지만 현재 실제
    장비는 `m2-db`, `m2-proxy`, `m2-stage`, `m4-prod`, `storage` 다섯 역할로 나뉜다.
  - 어느 장비에서 어떤 compose project, 경로, secret mount, DB, NPM proxy host를 관리하는지 아직
    사용자 장비에서 확인하지 않았다.
- 보존 기능:
  - 최신 release runner와 Windows runner 구성
  - API 컨테이너에만 전달되는 Toss widget/billing credential 두 쌍과 독립 HMAC secret 후보
  - 삭제된 review-mode/direct 변수 거부, placeholder·중복 credential·위험한 URL 거부
  - 검증 실패 시 실제 배포 전에 멈추고 값 자체는 출력하지 않는 preflight
- 해결 방식:
  - PG branch 전체를 no-ff merge해 로컬 후보 설정과 이력을 보존했다.
  - `TOSS_PAYMENTS_REVIEW_MODE` 기반 옛 validator를 최종 7개 runtime 변수 validator로 교체했다.
  - 이 commit은 어떤 현재 PC에도 적용하지 않았고, deploy script도 실행하지 않았다.
  - 5대 장비에 대한 자동 매핑은 하지 않았다. 사용자가 각 PC에서 직접 명령을 실행하면 Codex가
    결과를 받아 다음 한 단계만 안내하는 방식으로 고정했다.
  - 장비별 첫 read-only 확인표는
    `2026-09-03-toss-payments-pg-infra-five-pc-readonly-checklist.md`에 별도로 기록했다.
- 실행한 테스트:
  - 최신 `dev` 기준 root: 41 passed, Windows 전용 1 skipped
  - 최신 `dev` 기준 monitor: 6/6 통과
  - merge 후 root: 104 passed, Windows 전용 1 skipped
  - merge 후 monitor: 6/6 통과
  - `sh -n scripts/validate-toss-payments-env.sh`, `sh -n scripts/deploy-dev.sh` 통과
  - Infra runbook이 참조하는 API test-key checklist 파일 존재 확인
  - `git diff --cached --check` 통과, unmerged 0, commit 후 working tree clean
  - monitor `npm ci`: 21 packages audit, vulnerability 0
- 남은 위험:
  - 다섯 장비의 OS, 실제 역할, 저장소/compose 경로, container 이름, network, volume, secret mount,
    방화벽과 reverse proxy 설정을 아직 확인하지 않았다.
  - 예시의 DB host/IP와 runbook 명령을 실제 구성으로 검증하기 전에는 실행하면 안 된다.
  - Nginx Proxy Manager의 query-string access log 차단 여부와 정확한 webhook event 설정을 확인하지
    않았다.
  - 서버 env의 7개 변수는 값이 있는지조차 확인하지 않았다. 값 자체를 채팅이나 로그에 출력해서는
    안 된다.
  - 어떤 서버 접속, 설정 변경, 컨테이너 재생성, migration, 배포도 실행하지 않았다.

## 직접 코드 리뷰 checkpoint

Superpowers 코드 리뷰 기준을 직접 적용했다. 현재 실행 환경에서는 하위 리뷰 agent를 사용할 수
없으므로, integration diff와 API 계약을 저장소별로 다시 읽고 교차 검사했다.

### 리뷰에서 찾아 고친 항목

1. NestJS에 새 `/credits/ledger` proxy와 함께 구형 `/operations/ledger` route 및 구형 반환 타입이
   남아 있었다. 실제로는 새 JSON을 구형 타입이라고 잘못 주장하는 계약이었다.
   - RED: 구형 controller/service method가 없어야 한다는 테스트 2건 실패
   - 해결: 구형 route, service method, 반환 타입 제거; 새 CreditsModule route만 유지
   - commit: `5b50588 fix: retire stale desktop operation ledger proxy`
2. Angular는 새 계정 단위 크레딧 내역에 세션 정보가 없는데도 `알 수 없는 기기`로 표시했다.
   - RED: 세션 없는 행과 홈 빈 상태 문구 테스트 2건 실패
   - 해결: `계정 크레딧`으로 표시하고 홈도 `변동 내역` 용어로 통일; 실제 세션이 있으면 기존 라벨 유지
   - commit: `7b56e2a3 fix: label account-level credit history accurately`
3. 빈 Admin DB는 migration 직후 필수 operation policy 6개 중 1개만 있었다.
   - 조사 결과 나머지는 migration이 아니라 실제 앱 시작의 `OperationPolicySeeder`가 생성하는 구조였다.
   - 같은 폐기용 DB에서 seeder를 실행해 6개 모두 생성되는 것을 확인했다.
   - 후속 서버 준비 점검에는 migration 완료와 앱 시작 seed 결과를 둘 다 포함해야 한다.

### 최종 Git 교차 검사

| 저장소 | 최종 integration HEAD | PG 이력 방식 | working tree / unmerged / diff check |
|---|---|---|---|
| Web API | `f1517f35f83da69ead02c10dac9ff079ac2aaa00` | 전체 merge | clean / 0 / 통과 |
| Web Admin | `ed1b5a4a7ffc2c541d37116ecf4cf21bc61255ef` | 전체 merge | clean / 0 / 통과 |
| Web Customer | `bedafa38e02b4c800fc50efb086827eff4579e90` | 전체 merge | clean / 0 / 통과 |
| Angular | `9504e09806f23a1d8aad1aa3c2dfddf84aa1c564` | 필요한 동작 선별 이식 + 최신 dev 갱신 | clean / 0 / 통과 |
| NestJS | `5b50588442adf995e9c76958af7919886ecebda8` | 필요한 동작 선별 이식 | clean / 0 / 통과 |
| Electron | `578a12a8883c8268f28db7edae269752869159c4` | 유효한 test 계약만 선별 이식 | clean / 0 / 통과 |
| Infra | `fa92eda300f87be37187df703802c6bf2e447d0c` | 전체 merge, 실제 적용 보류 | clean / 0 / 통과 |

- API/Admin/Customer/Infra는 PG branch HEAD가 integration HEAD의 ancestor임을 확인했다.
- Angular/NestJS/Electron은 의도대로 PG branch 전체가 ancestor가 아니며 선별 commit만 존재한다.
- Customer source의 삭제된 `/app/purchase`, `/app/history`는 부정 회귀 테스트에서만 발견됐다.
- Angular/NestJS/Electron source에는 구형 license/ledger 경로, 구형 소문자 잔액 부족 코드,
  `shortform.create`, 구독 기반 plugin 차단 구현이 남지 않았다.
- 원본 7개 저장소는 모두 integration 브랜치를 checkout하고 있으며 working tree가 깨끗하다.
  각 저장소의 로컬 `dev` ref도 `origin/dev`와 정확히 같다.
- 기존 PG worktree 7개의 branch/HEAD는 불변이며 API `docs/api/openapi.yaml.orig`와 Customer
  `build/d2x_logo.icns`, `build/d2x_logo.ico`도 untracked 상태로 보존돼 있다.

### 리뷰 판정

- 로컬 코드 release candidate: 준비됨. 원본 7개 저장소가 각각의 integration 브랜치를 checkout하고
  있고 자동 검증과 재검증 가능한 commit이 남아 있다.
- 실제 stage/prod 배포: 준비되지 않음. 기존 DB 데이터 보존 전략, 실제 5대 PC 구성, test-key 수동
  결제 흐름 및 브라우저/데스크톱 E2E가 남아 있다.
- 가장 큰 차단 항목: destructive migration 3개의 기존 데이터 삭제. 이 항목을 해결하거나
  “기존 개발 데이터는 이관하지 않고 새 운영 DB를 사용한다”는 명시적 결정을 내리기 전에는 배포 금지.
