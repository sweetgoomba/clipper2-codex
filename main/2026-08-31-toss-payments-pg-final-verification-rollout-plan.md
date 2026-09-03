# TossPayments PG 최종 검증·출시 준비 계획

- 작성일: 2026-08-31
- 상태: 구현 전 검증 계획
- 선행 조건: 크레딧 정책, 환불 백엔드, Admin/Customer 화면 구현 완료
- 결과 기록 위치: `.codex/main`의 후속 검증 보고서

> 이 계획의 자동 테스트와 일회용 DB 검증도 구현 완료 후 별도 실행 승인을 받는다. 특히 기존 5433·5434·5435 DB, 운영 DB, 운영 토스 결제·환불, merge·push·deploy는 이 문서로 승인되지 않는다.

## Goal

- 7개 PG feature 저장소가 같은 OpenAPI·상태 모델을 사용하는지 확인한다.
- 신규 DB와 현재 상태를 복제한 일회용 DB에서 migration 안전성을 검증한다.
- 결제·갱신·상향·추가 구매·환불·크레딧 복구가 함께 동작하는지 확인한다.
- 불확실한 토스 결과와 일부 성공을 재현하고 운영자가 복구할 수 있는지 확인한다.
- 토스 테스트키 검증과 운영 적용을 명확히 분리한다.

## Task 1 — 검증 시작점 동결

**Read-only 대상**

- 7개 `toss-payments-pg-integration` worktree
- 다른 active worktree
- listener 3000/4201
- 기존 DB 5433/5434/5435

- [ ] 각 feature worktree에서 branch, HEAD, status, tracked diff, staged diff를 기록한다.
- [ ] Customer web의 기존 untracked `build/`를 별도 표시하고 건드리지 않는다.
- [ ] `meme-overlay-timeline-seek`, `operator-jwt-expiry-test`와 겹친 파일을 기록한다.
- [ ] 3000/4201 listener cwd와 health를 확인한다. main 디렉터리 process를 feature 검증 결과로 간주하지 않는다.
- [ ] 5433/5434/5435에 read-only query로 연결 대상, migration count, 마지막 migration을 다시 기록한다.
- [ ] 계획의 기준 HEAD와 달라졌으면 이 검증을 시작하지 않고 변경 원인을 먼저 대조한다.

검증 보고서에 secret, access token, billing key, raw paymentKey, raw billing data를 넣지 않는다.

## Task 2 — 신규 빈 DB 3개를 기존 DB와 분리해 생성

**사용할 일회용 자원**

```text
Admin:   container clipper-pg-refund-admin-test, port 55433
Release: container clipper-pg-refund-release-test, port 55434
User:    container clipper-pg-refund-user-test, port 55435
```

- [ ] 먼저 세 포트와 container 이름이 사용 중이 아닌지 read-only로 확인한다.
- [ ] 다음과 같이 명시적 이름과 포트로 PostgreSQL 16 일회용 container를 만든다. 기존 compose와 기존 volume을 사용하지 않는다.

일회용 DB의 임의 비밀번호는 실행 시 process 환경에만 넣고 문서·shell history·검증 보고서에는 기록하지 않는다. Container에는 명시적 이름·포트와 tmpfs 데이터 디렉터리를 사용하고 기존 volume은 mount하지 않는다.

- [ ] `pg_isready`가 통과한 뒤 feature API worktree에서 새 포트만 명시해 전체 migration을 적용한다.

명령 실행 때는 각 연결의 host, port, database name, user, password를 모두 process 환경으로 명시한다. 포트만 덮어써서 `.env`의 기존 host나 database로 fallback하는 방식은 금지한다.

- [ ] 각 DB의 migration count, 마지막 migration, schema constraint/index를 read-only query로 검증한다.
- [ ] 신규 DB seed 결과를 확인한다.

- 무료 체험 400크레딧, 30일
- 추가 구매 상품 30일
- Basic/Pro/Business 플러그인 차등 없음
- 기존 정확한 유료 동작 가격은 migration이 임의 변경하지 않음

- [ ] API를 3000/4201과 다른 임시 포트에서 실행한다. 세 DB의 모든 연결 필드를 명시하고 실제 DB identity가 일회용 DB임을 교차 확인한 뒤 `/health`를 확인한다.

실패 시 기존 DB로 fallback하지 않는다. 환경 변수가 빠지면 즉시 중단한다.

## Task 3 — 현재 상태의 일회용 복제 DB에서 forward migration 검증

기존 5433·5434·5435에는 read-only `pg_dump`만 수행한다. 복원 대상은 별도 일회용 container다. dump 파일과 raw row를 문서·terminal에 출력하지 않는다.

**사용할 별도 자원**

```text
Admin clone:   clipper-pg-refund-admin-clone, port 56433
Release clone: clipper-pg-refund-release-clone, port 56434
User clone:    clipper-pg-refund-user-clone, port 56435
```

- [ ] 이름·포트 충돌이 없는지 먼저 확인한다.
- [ ] PostgreSQL 16 container를 명시적 이름·포트·tmpfs 데이터 디렉터리로 생성한다. 기존 volume을 mount하지 않는다.
- [ ] 기존 DB에서 custom format dump를 stdout으로 읽어 clone DB의 `pg_restore` stdin으로 직접 전달한다. shell history나 로그에 row를 남기지 않는다.
- [ ] 복원 직후 다음 count만 기록한다.

- migration history 행 수
- 사용자·결제·구독·access grant·credit grant·ledger 행 수
- 결제 목적·상태별 집계
- dangling FK count

- [ ] clone 포트로만 환경을 지정해 미적용 migration을 순서대로 실행한다.
- [ ] 전후 count와 무결성을 비교한다.
- [ ] 특히 다음을 확인한다.

- `1786800000000-DropLegacyBilling`을 포함한 기존 history를 수정하지 않음
- `1788100000000-CreateFreeTrialPolicy`가 적용된 DB에서도 후속 정책 migration 성공
- `eligible_from` 제거 또는 무효화 후 무료 체험 repository 정상
- 기존 결제의 nullable refund snapshot이 migration을 막지 않음
- 기존 크레딧 status와 새 refund status check 제약 호환
- 기존 취소 감지 행을 임의 환불 완료로 변환하지 않음
- [ ] migration 실패 시 clone만 폐기하고 기존 DB에는 어떤 수정도 하지 않는다.

복제 명령은 실행 세션에서 실제 local 인증 방법을 읽어 구성하되 자격증명을 계획·보고서에 적지 않는다.

## Task 4 — 저장소별 자동 검증

### Web API

- [ ] focused refund/credit suites
- [ ] 전체 unit tests
- [ ] 전체 e2e tests
- [ ] production build
- [ ] OpenAPI contract

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
npm test -- --runInBand
npm run test:e2e -- --runInBand
npm run build
```

### Admin web

- [ ] 전체 Karma tests
- [ ] production build

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

### Customer web

- [ ] 전체 Karma tests
- [ ] production build
- [ ] 기존 untracked `build/` 보호 확인

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

### Desktop Angular

- [ ] 전체 Karma/style tests
- [ ] production build
- [ ] 플러그인 route smoke
- [ ] 크레딧 부족 dialog smoke

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_angular-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

### Desktop NestJS

- [ ] TypeScript build와 asset copy
- [ ] access/credit/operation/plugin 관련 node tests
- [ ] 전체 node tests

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_nestjs-toss-payments-pg-integration
npm run build
node --test test/*.test.js test/*.test.mjs
```

### Desktop Electron

직접 변경이 없더라도 bridge와 packaging 회귀를 확인한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_electron-toss-payments-pg-integration
npm test
npm run build
```

### Infra

- [ ] 토스 환경변수 fail-closed 검사
- [ ] 기존 removed key 차단
- [ ] compose render에서 secret 값 출력 금지

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_infra-toss-payments-pg-integration
node --test scripts/validate-toss-payments-env.test.mjs
```

실패한 suite를 생략하거나 성공으로 요약하지 않는다. 기존 실패와 신규 실패를 구분해 원문 test name과 exit code를 보고한다.

## Task 5 — fake provider 기반 전체 업무 시나리오

- [ ] 회원가입 즉시 무료 체험 지급과 지연 복구
- [ ] 30일 한국 날짜 만료
- [ ] 월간·연간 구독 첫 결제와 매월 크레딧
- [ ] 자동 갱신 성공·실패·재결제
- [ ] 다음 결제 취소·재개
- [ ] 결제수단 변경
- [ ] Basic→Pro→Business 다중 상향과 차액 결제 연결
- [ ] 다음 월 하향
- [ ] 추가 구매와 구독 종료 후 사용
- [ ] 충전 시점 우선 차감과 실패 작업 복구
- [ ] 월간·추가 구매 전액 환불
- [ ] 연간 부분 환불 두 종료 방식
- [ ] 다중 결제 일부 성공과 재처리
- [ ] 수동 취소 검증
- [ ] 외부 취소 경고와 연결
- [ ] 토스 성공 후 내부 DB 실패 복구
- [ ] 일반 운영자 실행 차단
- [ ] Customer/Admin 상태 일치

각 시나리오는 DB 사실, API 응답, 화면 표시를 같은 case ID로 대조한다.

## Task 6 — 동시성·장애 주입 검증

- [ ] 같은 결제를 두 최고 관리자가 동시에 환불 생성
- [ ] 환불 확정 transaction과 유료 동작 차감 동시 실행
- [ ] 환불과 월별 크레딧 scheduler 동시 실행
- [ ] 환불과 자동 갱신 charge claim 동시 실행
- [ ] 환불과 예약 요금제 변경 동시 실행
- [ ] 환불 잠금 뒤 실행 중 작업 실패 복구
- [ ] 첫 토스 취소 성공 직후 process 종료
- [ ] 응답 유실 뒤 같은 키 재시도
- [ ] DB update 실패 뒤 provider 재조회
- [ ] 두 recovery scheduler 인스턴스 동시 claim
- [ ] 수동 취소와 자동 재시도 경합

검증할 불변식:

- 원결제보다 누적 환불액이 클 수 없음
- 한 provider 취소 거래키가 두 항목에 연결될 수 없음
- 완료 항목을 다시 취소하지 않음
- 환불 잠긴 지급 건을 새 작업이 차감하지 않음
- 토스 성공 후 내부 실패가 원결제를 다시 청구하지 않음
- money status와 internal status가 사실과 일치

## Task 7 — 토스 테스트키 사전 점검

실제 테스트키 결제·취소 전 사용자에게 실행 범위와 예상 테스트 거래를 보여주고 별도 승인을 받는다.

- [ ] 현재 공식 Toss API 문서와 provider endpoint/header/field를 다시 대조한다.
- [ ] widget key와 billing key가 test mode이고 서로 올바르게 분리됐는지만 boolean/fingerprint 수준으로 확인한다. 값을 출력하지 않는다.
- [ ] API server가 운영 DB가 아니라 disposable test DB를 가리키는지 process environment와 실제 connection을 교차 확인한다.
- [ ] webhook callback도 test server를 가리키는지 확인한다.
- [ ] test payment를 쉽게 식별할 전용 사용자와 order prefix를 사용한다.
- [ ] 관리자/고객 화면에 raw provider payload가 보이지 않는지 확인한다.

중단 조건:

- live key 가능성이 있음
- DB 연결 대상이 불명확함
- callback이 운영 서버임
- 이미 존재하는 실제 사용자 결제를 대상으로 선택함
- 결제수단별 취소 조건을 확인하지 못함

## Task 8 — 승인된 토스 테스트키 시나리오

승인 후에도 테스트 거래만 사용한다.

- [ ] 월간 구독 첫 결제 → 미사용 전액 취소
- [ ] 월간 구독 + 상향 차액 → 두 결제 순차 전액 취소
- [ ] 연간 구독 첫 결제 → 관리자가 입력한 일부 금액 부분 취소
- [ ] 추가 구매 결제 → 미사용 전액 취소
- [ ] 같은 항목에 같은 중복 방지 키 재요청
- [ ] 결제 재조회에서 `balanceAmount`, `cancels`, 거래키·시각 확인
- [ ] 토스 dashboard test 영역에서 수동 취소 → Web API 검증
- [ ] test webhook와 동기 응답 순서가 달라도 한 결과로 수렴

네트워크 timeout은 실제 provider를 불안정하게 만들지 말고 controllable proxy 또는 fake provider 통합 테스트에서 주로 검증한다.

가상계좌 발급·입금·만료와 user-MID webhook은 환불 첫 검증에 섞지 않는다. 다만 전체 PG 완료 판정 전에는 아래 Task 8A에서 별도로 검증한다.

## Task 8A — 기존 PG TODO의 별도 완료 검증

환불 시나리오가 안정된 뒤 다음을 독립된 test run으로 수행한다.

- [ ] controllable fake provider와 실제 PostgreSQL repository를 사용해 `BILLING_DELETED` issued-candidate 정확 일치 상태를 서비스 경로로 만든다.
- [ ] 같은 방식으로 extant-previous 정확 일치 상태를 만든다.
- [ ] raw billing key를 DB에 직접 넣지 않고 두 상태의 terminal transition과 중복 전달을 검증한다.
- [ ] user-MID test widget key로 `PAYMENT_STATUS_CHANGED` 전달과 동일 transmission 중복을 검증한다.
- [ ] user-MID test widget key로 `DEPOSIT_CALLBACK` 전달과 중복을 검증한다.
- [ ] 가상계좌 발급 시 입금 전 `waiting_for_deposit`, 크레딧 0건을 검증한다.
- [ ] 입금 뒤 provider `DONE`, 내부 `paid`, 크레딧 지급 1건을 검증한다.
- [ ] 미입금 만료 뒤 terminal 상태와 크레딧 0건을 검증한다.

실제 key·계좌번호·고객 식별값은 결과 문서에 기록하지 않는다. 이 Task는 환불 구현 세션이 아니라 별도 검증 세션으로 진행한다.

## Task 9 — 민감정보·감사·관측성 검증

- [ ] source와 built artifact에서 secret 문자열·raw billing key·Authorization log를 검색한다.
- [ ] refund attempt에는 안전한 error code/message와 필요한 거래 식별값만 저장된다.
- [ ] 관리자 API는 전체 paymentKey/customerKey/billingKey를 반환하지 않는다.
- [ ] 고객 API는 내부 관리자 ID·메모·시도 이력을 반환하지 않는다.
- [ ] 모든 실행·재시도·수동 검증·내부 재처리에 관리자 ID와 시각이 남는다.
- [ ] 같은 사건을 application log와 refund case ID로 연관 지을 수 있다.
- [ ] raw DB row나 토스 원문 payload를 검증 보고서에 복사하지 않는다.

## Task 10 — 출시 전 최종 차이 검토

- [ ] 승인 설계의 각 항목을 구현 파일과 테스트에 연결한 traceability 표를 만든다.
- [ ] 7개 저장소의 최종 diff를 파일별로 검토한다.
- [ ] 관련 없는 formatting, 자동 생성 artifact, 기존 사용자 변경이 없는지 확인한다.
- [ ] migration 파일의 `up/down`, 제약, index, backfill을 별도 review한다.
- [ ] OpenAPI와 Admin/Customer/Desktop 모델을 대조한다.
- [ ] 여전히 열려 있는 TODO와 런칭 차단 이슈를 구분한다.
- [ ] commit·push·merge·deploy 전 사용자에게 다음을 보고한다.

- 구현된 범위
- 통과한 자동/수동 검증과 실제 명령
- 실행하지 않은 검증
- 기존 DB에 손대지 않았다는 근거
- 토스 test/live 호출 여부
- 남은 위험과 rollback 경계

## Task 11 — 운영 적용은 별도 승인 후에만

다음은 이 계획의 자동 실행 대상이 아니다.

- 운영 DB 백업·migration
- 운영 토스 결제·환불
- 운영 secret 설정
- merge·push·PR
- deploy
- 고객 공지 또는 외부 연락

운영 적용을 승인받으면 별도 runbook을 `.codex/main`에 새 문서로 작성하고, 정확한 대상·백업·중단 조건·rollback·사후 확인을 다시 승인받는다.

## Task 12 — 일회용 자원 정리

검증 결과와 필요한 집계만 기록한 뒤 사용자가 정리를 승인하면 명시적 이름의 일회용 container만 제거한다. 기존 container·volume·5433/5434/5435는 대상이 아니다.

정리 대상 후보:

```text
clipper-pg-refund-admin-test
clipper-pg-refund-release-test
clipper-pg-refund-user-test
clipper-pg-refund-admin-clone
clipper-pg-refund-release-clone
clipper-pg-refund-user-clone
```

삭제 직전에 `docker inspect`로 정확한 이름·port·mount를 다시 확인한다. 승인 후 위 명시적 container 이름만 제거하며 volume 정리도 그 container에 연결된 일회용 volume만 대상으로 한다. broad glob이나 workspace 경로 삭제를 사용하지 않는다.

## 최종 완료 기준

- 신규 DB와 일회용 복제 DB migration 검증 통과
- 7개 저장소 관련 전체 테스트·build 통과
- fake provider로 정상·부분 성공·불확실·수동 취소 시나리오 통과
- 승인된 경우에만 Toss test key 시나리오 통과
- Admin/Customer/Desktop와 Web API 계약 일치
- 민감정보 노출 없음
- 기존 DB·운영 토스·다른 worktree 무변경
- 기존 PG TODO가 환불 첫 작업과 분리된 상태로 Task 8A에서 완료됨
- 운영 적용 전 별도 승인 대기
