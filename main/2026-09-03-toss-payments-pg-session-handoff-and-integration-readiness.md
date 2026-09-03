# TossPayments PG 세션 인수인계 및 통합 준비 현황

- 작성일: 2026-09-03
- 목적: 지금까지 개발한 PG 기능의 실제 상태를 보존하고, 다음 세션의 최신 `dev` 통합과 이후 운영 배포를 안전하게 이어가기 위한 기준 문서
- 현재 단계: 기능 브랜치 구현과 로컬 자동 검증은 대부분 완료. 최신 `dev` 통합, 실제 기존 데이터 호환 검증, 운영 인프라 구축, 상점 테스트·라이브 검증은 미완료

## 1. 결론

다음 세션에는 PG 브랜치를 현재 `dev`에 바로 병합하거나 개발서버에 배포하지 않는다.

각 repository의 최신 `origin/dev`에서 별도 통합 브랜치와 worktree를 만든 뒤, 최신 런칭 UI·UX 및 메모리 최적화 구조를 기준으로 PG 기능을 통합한다. 단순히 충돌 파일에서 한쪽 내용을 선택하는 작업이 아니라 양쪽 기능을 함께 보존하는 의미 단위 통합이 필요하다.

통합 결과는 먼저 로컬 환경과 폐기 가능한 DB 복제본에서 검증한다. 내부 사용자가 있는 현재 개발서버와 개발 DB에는 이 단계의 결과를 배포하거나 migration하지 않는다.

운영 환경은 현재 개발서버와 분리하는 방향이 적절하다.

- `m2-stage`: 기존 개발서버 유지
- `m4-prod`: 운영용 client, API, admin 실행
- `m2-db`: 운영용 user, admin, release DB를 개발 DB와 별도 컨테이너·볼륨으로 구성
- `m2-proxy`: TLS와 reverse proxy, 운영 모니터링 경로 관리
- `storage`: 설치형 프로그램 빌드 runner 역할 유지

다만 `m4-prod`에 바로 공개 배포하는 것이 통합 검증을 대신하지는 않는다. 통합 완료 → 폐기 가능한 DB 검증 → 비공개 운영 후보 환경 검증 → 카드사 심사에 필요한 경우 test key를 사용하는 별도 심사용 route 공개 → 라이브키 설정 및 실제 결제 검증 → 운영 route 공개 전환 순서를 권장한다.

## 2. 현재까지 완료된 범위

### PG 제품 기능

- 월간·연간 정기구독 최초 결제와 자동 갱신
- 카드 등록·변경, 재결제와 실패 복구 흐름
- 추가 구매 크레딧 결제
- 요금제 변경과 상향 차액 결제
- 가입 시 무료 체험 크레딧 지급
- 정기구독·무료 체험·추가 구매 크레딧의 분리된 지급·사용·만료 처리
- 관리자 상품·가격·크레딧 정책 관리
- 관리자 환불 대상 조회, 미리보기, 실행, 재조회, 재시도, 수동 확인 및 감사 이력
- 토스 결제 취소와 이용권 종료·크레딧 회수를 분리하되 연결된 환불 처리
- 고객 결제·구독·크레딧·환불 상태 화면
- 설치형 앱의 현재 이용권·크레딧 조회 및 크레딧 차감 연동
- 최종 환불·요금제 변경 정책 변경분 반영

### 확정 정책 반영

- 모든 요금제에서 사용 가능한 플러그인은 동일하며, 차이는 지급 크레딧 수량
- 크레딧이 필요 없는 기능은 정기구독과 관계없이 사용 가능
- 추가 크레딧은 유료 정기구독 중에만 구매 가능하지만, 구매 후에는 구독 종료와 관계없이 유효기간 동안 사용 가능
- 무료 체험과 추가 구매 크레딧은 지급 시각 기준 30일 유효
- 크레딧은 먼저 지급된 순서로 차감
- 정기구독 크레딧은 다음 지급 주기로 이월하지 않음
- 월간 구독은 해당 결제로 지급된 크레딧을 사용하지 않은 경우 전액 환불
- 연간 구독은 연간 구독으로 지급된 크레딧을 한 번도 사용하지 않은 경우 전액 환불
- 추가 구매 크레딧은 전량이 보전된 경우에만 전액 환불하고 부분 환불하지 않음
- 상향 후 환불은 상향으로 새로 지급된 정기구독 크레딧을 사용하지 않은 경우 실제 차액 결제 금액만 환불하며, 이용권은 종료하고 이전 이용권은 복원하지 않음
- 연간에서 월간으로의 변경은 동일·상향·하향 모두 불가
- 같은 결제기간 내 상향, 같은 요금제의 월간→연간, 월간→상위 연간은 즉시 적용
- 같은 결제기간 내 하향과 월간→하위 연간은 다음 결제일부터 적용
- 즉시 변경 성공 시 이용기간과 결제주기를 변경 시각부터 새로 시작
- 즉시 상향 차액은 기간 기준과 해당 정기구독 크레딧 기준으로 각각 계산하고 더 큰 차액 적용
- 즉시 변경 결제가 실패하면 기존 이용권 유지

### 마지막 검증 결과

최종 정책 변경을 반영한 전체 검증 기록:

- API 단위 테스트: 185 suites, 1,790 tests
- API E2E: 당시 4 suites, 37 tests
- 이후 `BILLING_DELETED` 정확 상태 2건을 repository-backed E2E로 추가하여 API E2E는 5 suites, 39 tests
- Admin: 328 tests 및 build
- Customer: 226 tests 및 build
- Desktop Angular: 2,143 tests와 추가 집중 테스트 6건
- Desktop NestJS: 792 tests와 추가 집중 테스트 6건 및 build
- Electron: 219 tests
- Infra: 71 tests

위 결과는 각 PG 기능 worktree 기준이다. 최신 `dev`와 통합된 결과에 대한 검증은 아니다.

## 3. 현재 보존해야 할 PG worktree

| Repository | 브랜치 | HEAD | 상태 |
| --- | --- | --- | --- |
| Web API | `feature/toss-payments-pg-integration` | `4ef2268` | tracked/staged 변경 없음, `docs/api/openapi.yaml.orig`만 untracked |
| Web Customer | `feature/toss-payments-pg-integration` | `7f4d04a` | tracked/staged 변경 없음, 기존 `build/`만 untracked |
| Web Admin | `feature/toss-payments-pg-integration` | `dab857c` | clean |
| Desktop Angular | `feature/toss-payments-pg-integration` | `f02bf221` | clean |
| Desktop NestJS | `feature/toss-payments-pg-integration` | `60a4f07` | clean |
| Desktop Electron | `feature/toss-payments-pg-integration` | `abdc575` | clean |
| Infra | `feature/toss-payments-pg-integration` | `e6ae78f` | clean |

주의:

- Customer의 기존 untracked `build/`를 삭제하거나 stage하지 않는다.
- API의 untracked `docs/api/openapi.yaml.orig`도 통합 전에 출처를 확인하며 임의로 stage하지 않는다.
- `meme-overlay-timeline-seek` 작업은 별도 작업이므로 수정하지 않는다.
- `operator-jwt-expiry-test` 브랜치 작업은 현재 `origin/dev`에 이미 포함된 것으로 확인됐지만 해당 worktree 자체는 수정하지 않는다.
- 위 PG 커밋들은 로컬 완료 상태이며 push·merge·deploy 완료 상태로 간주하지 않는다.

## 4. Phase 기준 진행 상태

### 완료

- Phase 1~4: PG, 가격·크레딧·이용권, 관리자 운영, 환불 기능 구현 및 기능 worktree 자동 검증
- 최종 정책 변경분 구현과 재검증
- Phase 5 일부: `BILLING_DELETED`의 exact candidate와 extant-previous 상태 repository-backed 통합 테스트 및 커밋

### 미완료

- Phase 5 나머지: 상점 테스트 MID를 사용한 결제·웹훅·가상계좌 실제 흐름 검증
- Phase 6: 최신 `dev` 통합, 실제 기존 데이터 호환 검증, 전체 회귀 검증, 배포 전 검증, 운영 인프라 및 전환 준비
- 라이브 단계: 라이브키와 실제 결제수단을 사용한 최소 실거래·취소 검증 및 공개 전환

## 5. 카드사 심사 통과 전 할 수 있는 일

### 다음 세션의 최우선 작업: 최신 dev 통합

1. 런칭에 포함될 UI·UX, 메모리 최적화, meme overlay 작업이 어느 커밋까지인지 확인하고 각 repository의 통합 기준 SHA를 고정한다.
2. 로컬 main checkout의 현재 브랜치를 기준으로 삼지 않고, 새로 fetch한 정확한 `origin/dev`에서 repository별 통합 브랜치와 worktree를 만든다.
3. 기존 PG worktree는 비교·참조용으로 보존한다.
4. API와 OpenAPI를 먼저 통합하고, Admin·Customer, Desktop NestJS·Angular·Electron, Infra 순으로 계약을 맞춘다.
5. repository별로 작은 검증 단위를 만들고 테스트 후 커밋한다.
6. 통합이 모두 끝나도 `dev`에는 merge하거나 배포하지 않는다.

권장 브랜치 성격은 `integration/toss-payments-pg-YYYYMMDD`와 같은 별도 release-candidate 통합 브랜치다. 실제 이름은 다음 세션 시작 시 기존 브랜치 규칙을 확인해 정한다.

### Repository별 통합 방식

| Repository | `origin/dev` 전용 커밋 / PG 전용 커밋 | 권장 방식 | 이유 |
| --- | ---: | --- | --- |
| Web API | 57 / 139 | PG 브랜치 전체를 통합 브랜치에 merge하고 의미 단위로 충돌 해결 | 결제 도메인, migration, OpenAPI 역사를 통째로 보존해야 함 |
| Web Customer | 0 / 31 | 전체 merge 후 API 계약과 화면 회귀 검증 | 현재 Git 충돌 가능성은 낮지만 통합 API 검증 필요 |
| Web Admin | 10 / 21 | 전체 merge 후 모델·mock·navigation 충돌을 양쪽 기능의 합으로 해결 | 최신 admin 변경과 PG 운영 화면이 모두 필요 |
| Desktop Angular | 694 / 6 | 최신 dev에 유효한 PG 변경만 선별해 forward-port | PG 브랜치 기준점이 너무 오래되어 전체 merge의 의미 충돌 위험이 큼 |
| Desktop NestJS | 357 / 7 | 최신 dev에 유효한 PG 변경만 선별해 forward-port | 최신 렌더링·메모리·operation 구조를 우선 보존해야 함 |
| Desktop Electron | 50 / 3 | 최신 dev에 유효한 PG 변경만 선별해 forward-port | 변경량은 작지만 최신 main process 구조를 기준으로 반영해야 함 |
| Infra | 0 / 6 | 전체 merge 후 현재 5대 서버 구조에 맞게 별도 수정·검증 | Git 병합은 단순하지만 문서와 주소가 현재 운영 구상과 다름 |

현재 raw merge conflict가 확인된 주요 영역:

- API: `openapi.yaml`, `app.module.ts`, admin/user datasource, media search, operations service와 operation definitions
- Admin: API mock interceptor, API models, header spec
- Desktop Angular: routes, settings, plugin card/detail
- Desktop NestJS: app module, plugin service, shortform render orchestrator

특히 API의 operation 영역은 최신 dev의 렌더링·작업 실행 변경과 PG의 크레딧 차감·실패 복구가 만나는 지점이다. `ours` 또는 `theirs` 일괄 선택을 금지한다.

### DB와 migration 검증

- 새 빈 user/admin/release DB에 전체 migration을 처음부터 적용한다.
- 현재 개발 DB를 직접 변경하지 않고, 별도 컨테이너에 복제한 폐기 가능한 DB에서 forward migration을 검증한다.
- migration 전후 사용자 수, 결제·이용권·크레딧 관련 핵심 데이터, FK와 unique constraint를 비교한다.
- 실패·중단·재실행 및 복구 절차를 검증한다.

중요 위험:

`1786800000000-DropLegacyBilling` migration은 기존 무통장 입금 기반의 `plans`, `purchase_requests`, `licenses`, `token_usage`, `credit_ledger` 테이블을 삭제한다. 새 PG 테이블이 존재하는지만 확인하며 기존 행을 새 구조로 이관하지 않는다. 또한 `down`은 빈 테이블만 복원하고 삭제된 행을 복구하지 못한다.

따라서 현재 내부 사용자의 이용권·크레딧 데이터를 유지해야 한다면 별도 데이터 이관 설계가 먼저 필요하다. 이 migration을 현재 개발 DB에 바로 적용해서는 안 된다.

### 통합 후 자동·로컬 검증

- 7개 repository 전체 테스트와 build 재실행
- OpenAPI와 Customer/Admin/Desktop 모델의 계약 일치 확인
- 정기 결제, 갱신, 실패 재시도, 추가 크레딧, 즉시·예약 요금제 변경, 환불의 fake-provider 통합 테스트
- 동일 요청·동시 요청·timeout·provider 성공 후 내부 처리 실패·재실행 검증
- 관리자 권한, 로그의 개인정보·키 노출, 감사 이력 검증
- 운영용 compose와 환경변수 schema의 정적 검증
- 최신 정책과 충돌하는 오래된 테스트·문구·runbook 제거 또는 폐기 표시

### 테스트키로 가능한 상점 연동 검증

토스 공식 문서상 계약과 카드사 심사 전에도 개발 연동 체험 상점의 테스트키로 가상 결제, 테스트 결제내역, 웹훅을 사용할 수 있다. 가상계좌는 개발자센터에서 테스트 입금·취소 처리도 가능하다. 자동결제도 테스트 환경에서는 본인인증 없는 방식으로 흐름을 검증할 수 있다.

따라서 아래 항목은 원칙적으로 라이브키를 기다릴 필요가 없다. 다만 문서 공용 키가 아니라 우리 계정의 테스트 상점 MID와 키 세트, 외부에서 접근 가능한 HTTPS 웹훅 URL이 필요하다.

- `PAYMENT_STATUS_CHANGED` 수신과 중복 전달 처리
- `DEPOSIT_CALLBACK` 수신과 중복 전달 처리
- 가상계좌 발급 후 입금 전 `WAITING_FOR_DEPOSIT` 및 크레딧 미지급
- 테스트 입금 후 `DONE`과 크레딧 정확히 한 번 지급
- 미입금 만료 또는 취소 후 크레딧 미지급
- 테스트 카드 결제·결제 취소와 내부 상태 동기화
- 테스트 환경 자동결제 등록·청구 흐름

웹훅 검증에는 임시 ngrok URL을 다시 사용할 수 있지만 필수는 아니다. 외부 HTTPS 접근이 가능한 격리된 테스트 endpoint가 있으면 그것을 사용할 수 있다. 어느 방법이든 테스트용 webhook만 등록하고 운영 webhook과 혼용하지 않는다.

일부 결제수단과 실제 본인인증 자동결제는 계약·심사 후 상점 MID 또는 라이브 환경이 필요하므로 테스트 환경 통과가 라이브 환경을 완전히 보증하지는 않는다.

공식 근거:

- [토스페이먼츠 API 키](https://docs.tosspayments.com/reference/using-api/api-keys)
- [토스페이먼츠 개발자센터와 테스트 결제내역](https://docs.tosspayments.com/resources/glossary/dev-center)
- [가상계좌 결제창 연동과 테스트 입금](https://docs.tosspayments.com/guides/v2/payment-window/integration-virtual-account)
- [웹훅 연결](https://docs.tosspayments.com/guides/v2/webhook)
- [자동결제 테스트 환경](https://docs.tosspayments.com/resources/glossary/billing)
- [카드사 심사와 라이브 환경 FAQ](https://docs.tosspayments.com/resources/faq)

### 운영 인프라 사전 준비

카드사 심사 전에도 다음 준비는 가능하다.

- `m4-prod` 실제 LAN IP, OS, Docker, 디스크, 재시작 정책, 방화벽 확인
- 운영 이미지의 빌드·버전·배포·rollback 방식 확정
- `m2-db` 운영 DB 컨테이너·볼륨·포트·계정 설계와 접근 제어
- 운영 DB 백업 위치·주기·보존기간·복구 리허설 설계
- `m2-proxy`의 Nginx Proxy Manager route, TLS, health check 설계
- `clipper-web-monitor`의 실제 동작과 Slack 알림 소유자 확인 및 운영 대상 추가 설계
- 운영 secret 저장·주입·교체 절차 준비
- 운영 후보 stack을 외부 공개 없이 test key로 구동하고 health 및 네트워크 경로 검증
- 카드사 심사에서 실제 사이트·상품·정기결제·결제창 확인이 필요하면, 내부 사용자가 있는 개발서버 대신 검증된 release candidate를 별도 심사용 domain 또는 route로 공개하고 test key를 사용

실제 운영 DB 생성·migration과 외부 공개는 설계·백업·복구 절차를 승인한 후 별도 실행한다.

심사용 route 공개는 운영 서비스 공개와 구분한다. 심사 담당자가 접근할 수 있어야 하지만 개발 DB나 내부 사용자 데이터에 연결하지 않고, 운영 라이브키도 사용하지 않는다.

## 6. 카드사 심사·계약 완료와 라이브키 발급 후 할 일

- 일반결제용과 자동결제용 MID 및 각각에 대응하는 client/secret key 세트를 확인
- test/live 키 또는 서로 다른 MID의 키가 섞이지 않았는지 비밀값을 출력하지 않고 검증
- 라이브 callback URL, 허용 origin, 결제 UI, 결제수단, 정기결제 설정 확인
- 운영 HTTPS webhook URL 등록 및 실제 전달·중복·재시도 검증
- 운영 secret manager 또는 승인된 환경 파일에 라이브키 주입
- 명시적 승인 아래 최소 금액의 실제 카드 결제와 전액 취소 검증
- 최초 정기구독, 자동결제용 빌링키 발급, 갱신 청구, 결제 실패 흐름 확인
- 추가 크레딧 결제, 즉시 상향 차액 결제, 환불 후 이용권·크레딧 상태 확인
- 계약된 경우 실제 가상계좌 발급·입금·취소·만료 흐름 확인
- 토스 관리자 화면의 결제·취소 기록과 내부 DB·감사 이력 대조
- 카드사별·브라우저별·모바일 결제창 동작 확인
- 운영 백업 성공과 복구 가능성, 모니터링·Slack 알림, container 자동 재시작 확인
- 최종 배포 승인 후 DNS/NPM route를 `m4-prod`로 전환
- 공개 직후 health, 로그인, 결제 화면, webhook, 관리자 조회와 오류율 모니터링

라이브 결제와 취소는 실제 금전 거래이므로 테스트 계정·금액·담당자·시간·rollback 조건을 먼저 명시하고 실행한다.

## 7. 현재 인프라 문서와 실제 구상의 충돌

기존 인프라 문서는 3대 Mac mini 구조를 가정하며 proxy와 production app을 `192.168.0.2`에 함께 둔다. 현재 사용자가 설명한 5대 구조에서는 proxy는 `m2-proxy`, production app은 `m4-prod`로 분리된다.

PG Infra 브랜치에도 다음 과거 가정이 남아 있다.

- `env/stack.prod.env.example`의 app bind host가 `192.168.0.2`
- `proxy/routes.md`의 production upstream이 `192.168.0.2`
- `runbooks/deploy-prod.md`가 proxy/prod가 같은 Mac mini라고 가정

따라서 Infra 브랜치가 Git상 clean merge되더라도 그대로 운영 배포하면 안 된다. 다음 세션에서 실제 `m4-prod` IP와 현재 NPM 구성을 확인해 5대 서버 구조로 runbook과 설정을 다시 맞춰야 한다.

PG Infra가 제안한 운영 포트와 컨테이너 이름은 아직 배포된 사실이 아니라 검토할 후보값이다.

- App: `clipper-web-client-prod`, `clipper-web-admin-prod`, `clipper-web-api-prod`; 후보 포트 42202, 42302, 43202
- DB: `clipper-db-user-prod`, `clipper-db-admin-prod`, `clipper-db-release-prod`; 후보 포트 55202, 55212, 55222

실제 값은 기존 서버의 port·volume·backup·monitor 충돌을 먼저 조사한 뒤 확정한다.

## 8. 개발 DB와 운영 DB에 대한 권고

현재 개발서버에 내부 직원 계정과 업무 데이터가 있어도, 그 DB를 곧바로 운영 DB로 승격하는 것은 권장하지 않는다.

기본안:

- 개발 DB는 현재 상태로 유지
- 운영 DB는 `m2-db`에 별도 container·database·volume·credential로 신규 구성
- 런칭에 필요한 기준 데이터만 migration과 seed로 생성
- 내부 직원 계정 또는 기존 데이터의 운영 이관이 필요하면 대상·목적·정합성 규칙을 정한 별도 이관 작업으로 처리
- 테스트 결제, 문서 키 결제, 무통장 구매 요청 같은 개발 데이터는 운영으로 자동 복사하지 않음

운영 DB를 새로 만드는 경우에도 migration 전체 실행과 seed 결과를 동일한 빈 disposable DB에서 먼저 재현해야 한다.

## 9. 다음 세션 권장 범위

다음 세션의 목표는 “PG를 dev에 배포”가 아니라 “최신 출시 코드와 PG 기능을 하나의 검증 가능한 release candidate로 통합”하는 것이다.

권장 순서:

1. 이 문서와 최종 정책 delta 문서를 기준으로 source of truth 고정
2. 모든 repository fetch 후 런칭 기준 `origin/dev` SHA 기록
3. 진행 중인 UI·UX·메모리 최적화·meme overlay 작업의 포함 여부와 완료 SHA 확인
4. repository별 별도 integration worktree 생성
5. API와 migration/OpenAPI 통합
6. Admin과 Customer 통합
7. Desktop NestJS, Angular, Electron의 PG 변경 선별 반영
8. Infra 통합 후 5대 서버 구조에 맞게 설계 갱신
9. 빈 DB와 개발 DB 복제본 migration 검증
10. 전체 자동 테스트, build, 로컬 수동 시나리오 검증
11. 상점 테스트 MID를 사용한 webhook·가상계좌·취소 검증
12. 통합 검증 보고서 작성 후 운영 후보 환경 준비 여부 결정

이 범위가 끝나기 전에는 `dev` 또는 공개 production에 merge·deploy하지 않는다.

## 10. 다음 세션 시작 전에 확인할 정보

- 런칭에 포함할 최신 UI·UX 및 메모리 최적화 작업의 repository별 최종 브랜치와 SHA
- `m4-prod`의 실제 LAN IP와 현재 설치 상태
- production domain과 NPM의 현재 route·TLS 설정
- `clipper-web-monitor`의 실제 검사 대상, Slack channel, 유지보수 담당자
- 운영 이미지가 어디에서 build되고 어떤 registry 또는 전송 방식으로 `m4-prod`에 전달되는지
- 운영 DB backup 저장 위치, 암호화, 보존기간, 복구 담당자
- 현재 개발 DB의 내부 사용자·무통장 이용권·크레딧 중 운영으로 이관할 데이터가 있는지
- 우리 계정의 테스트 상점 MID에서 일반결제, 자동결제, 가상계좌 및 webhook을 사용할 수 있는지

## 11. 계속 유지할 안전 조건

- 현재 개발 DB와 기존 5433/5434/5435 DB에 직접 migration 또는 write 금지
- 고객 `build/` 삭제·stage 금지
- `meme-overlay-timeline-seek`와 다른 세션 worktree 수정 금지
- secret key, access token, 결제 자격증명, 원문 결제 데이터 출력·문서화 금지
- 라이브 결제·환불은 별도 명시 승인 전 금지
- `dev` 직접 병합·배포, production 공개, DNS 변경은 통합 및 검증 완료 전 금지
- destructive migration은 실제 데이터 복제본 검증과 backup/restore 확인 전 실행 금지

## 12. 더 이상 현재 배포 기준으로 사용하면 안 되는 문서

- `.codex/implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md`: 과거 review checkout, 단일 키와 예전 결제 구조를 전제로 하므로 현재 PG 배포 절차로 사용하지 않는다.
- `2026-08-31-toss-payments-pg-final-verification-rollout-plan.md`: 일부 task에 과거의 날짜 기준 만료와 연간 부분 환불 정책이 남아 있으므로 그대로 실행하지 않는다. 이 문서와 2026-09-02 최종 정책 delta를 우선한다.

## 13. 관련 최신 기록

- `.codex/main/2026-08-31-toss-payments-pg-completion-implementation-roadmap.md`
- `.codex/main/2026-08-31-toss-payments-pg-phase4-implementation-verification-report.md`
- `.codex/main/2026-09-02-toss-payments-pg-final-policy-delta.md`
- `.codex/main/2026-09-02-toss-payments-pg-final-policy-delta-implementation-plan.md`
- `.codex/main/2026-09-02-toss-payments-pg-final-policy-delta-verification-report.md`
- `.codex/main/2026-09-02-toss-payments-billing-deleted-exact-states-verification.md`
