# 이용권·크레딧 구조 교체 검증 기록

- 검증일: 2026-08-13 (Asia/Seoul)
- 코드 브랜치: 각 레포지토리 `feat/access-credit-system-replacement`
- 문서 브랜치: `.codex/main`
- 범위: `clipper_web_api`, `clipper_web_client`, `clipper_web_admin`, `clipper_nestjs`, `clipper_angular`, `clipper_electron`, `clipper_infra`
- 제외: `dev` 병합, 개발 서버 배포, 운영 데이터 마이그레이션

## 검증된 결과

### API와 DB

- Node.js 22.22.2
- `npm test -- --runInBand`: 125 suites, 687 tests 통과
- `npm run build`: 통과
- OpenAPI 3.1 YAML 파싱: 통과, 79 paths
- 실행 코드에서 구형 무통장 구매 API와 `/licenses`, `/license-requests` 참조가 남지 않았음을 검색으로 확인
- `fix/operator-jwt-expiry-test`의 `a1d91b6`을 기능 브랜치에 병합해 날짜가 지나면 깨지는 운영자 세션 테스트를 함께 검증
- 관리자 회원 목록의 사용자별 access·credit N+1 조회를 사용자 페이지·배치 조회로 교체
- 기본 조회는 DB 페이지네이션을 사용하고 상태·만료 정렬 스캔은 최대 1,000명으로 제한
- 결제 완료 후 상품 지급 실패 주문 전용 조회·재시도 API를 추가하고, 재시도는 결제 재승인 없이 idempotent fulfillment만 실행
- 오래 실행 중인 AI 작업은 로컬 job/project와 서버 provider request 증거를 영속 저장하고, 운영자가 기록된 증거를 선택해야만 성공 확정 또는 실패 환불 가능
- 실행 생성·크레딧 차감·최초 로컬 job/project 증거 저장을 같은 DB 트랜잭션으로 처리해 증거 없는 차감 실행 방지
- Dance Naver 검색은 실행 전 사전설정 경로임을 확인하고 실제 실행 정책의 provider scope를 빈 목록으로 정합화

PostgreSQL 16 일회용 컨테이너에서 Node.js 22로 빈 admin DB에 33개 마이그레이션을 처음부터 적용했다.

- 최신 적용 마이그레이션: `1787000000000`
- 두 번째 실행 결과: `No pending migrations.`
- 존재 확인: `plan_tiers`, `billing_products`, `user_access_grants`, `credit_grants`, `credit_ledger_entries`, `subscriptions`, `operation_resolution_events`, `operation_run_evidence`
- 컬럼 확인: `operation_resolution_events.evidence_id`
- 제거 확인: `plans`, `purchase_requests`, `licenses`, `token_usage`, `credit_ledger`
- 검증 후 일회용 컨테이너 삭제

### 고객 웹

- Node.js 22.22.2
- `npm test -- --watch=false`: 104 tests 통과
- `npm run build`: 통과

### 관리자 웹

- Node.js 22.22.2
- `npm test -- --watch=false`: 193 tests 통과
- `npm run build`: 통과
- 기존 초기 번들 예산 경고: 500 kB 기준 대비 33.74 kB 초과, 총 533.74 kB. 빌드는 성공했으며 이번 기능의 실패 조건은 아니다.
- 결제 후 지급 실패 복구 화면과 AI 작업 증거 기반 복구 화면을 서로 분리해 검증

### 로컬 Nest 게이트웨이

- Node.js 24.19.0
- `npm run build`: 통과
- `node --test test/*.test.js`: 748 tests 통과
- billable workflow 시작 전 로컬 job/project 증거 기록과 성공·실패 상태 갱신을 검증

### Angular 데스크톱 UI

- Node.js 24.19.0
- `CI=true ./node_modules/.bin/ng test --watch=false`: 1,968 tests 통과
- `npm run test:styles`: 6 tests 통과
- `CI=true npm run build:devapp`: 통과
- 일반 `ng test`는 Angular 22 업그레이드 후 로컬 LMDB 네이티브 `Abort trap: 6`가 재현된다. 프로젝트 캐시 설정이나 백엔드를 변경하지 않았고, CI 모드의 동일 Angular 테스트·빌드 경로로 검증했다.

### Electron

- Node.js 24.19.0
- `npm run build`: 통과
- `npm test`: 219 tests 통과

### Infra

- dev 앱 compose example 조합 `config --quiet`: 통과
- dev DB compose example `config --quiet`: 통과
- `bash -n scripts/deploy-dev.sh`: 통과

## 검증 시점 브랜치 HEAD

- `clipper_web_api`: `a45416d`
- `clipper_web_client`: `7180d32`
- `clipper_web_admin`: `0f2746d`
- `clipper_nestjs`: `2abc490`
- `clipper_angular`: `7938350`
- `clipper_electron`: `7f5d4d3`
- `clipper_infra`: `89920f8`

## 배포 전 주의

- `1786800000000-DropLegacyBilling`은 출시 전 구형 무통장 데이터와 구형 이용권·단일 잔액 테이블을 제거하는 파괴적 마이그레이션이다.
- 개발 서버에서는 코드 컨테이너를 교체하기 전에 admin DB 백업과 마이그레이션 대상 확인이 필요하다.
- 현재 검증은 기능 브랜치 기준이며 `dev` 병합과 배포는 수행하지 않았다.
