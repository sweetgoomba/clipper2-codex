# 이용권·크레딧 구조 교체 검증 기록

- 검증일: 2026-08-13 (Asia/Seoul)
- 코드 브랜치: 각 레포지토리 `feat/access-credit-system-replacement`
- 문서 브랜치: `.codex/main`
- 범위: `clipper_web_api`, `clipper_web_client`, `clipper_web_admin`, `clipper_nestjs`, `clipper_angular`, `clipper_electron`, `clipper_infra`
- 제외: `dev` 병합, 개발 서버 배포, 운영 데이터 마이그레이션

## 검증된 결과

### API와 DB

- Node.js 22.22.2
- `npm test -- --runInBand`: 120 suites, 666 tests 통과
- `npm run build`: 통과
- OpenAPI YAML 파싱: 통과
- 실행 코드에서 구형 무통장 구매 API와 `/licenses`, `/license-requests` 참조가 남지 않았음을 검색으로 확인
- `fix/operator-jwt-expiry-test`의 `a1d91b6`을 기능 브랜치에 병합해 날짜가 지나면 깨지는 운영자 세션 테스트를 함께 검증

PostgreSQL 16 일회용 컨테이너에서 빈 admin DB에 31개 마이그레이션을 처음부터 적용했다.

- 최신 적용 마이그레이션: `1786800000000`
- 두 번째 실행 결과: `No pending migrations.`
- 존재 확인: `plan_tiers`, `billing_products`, `user_access_grants`, `credit_grants`, `credit_ledger_entries`, `subscriptions`, `operation_resolution_events`
- 제거 확인: `plans`, `purchase_requests`, `licenses`, `token_usage`, `credit_ledger`
- 검증 후 일회용 컨테이너 삭제

### 고객 웹

- Node.js 22.22.2
- `npm test -- --watch=false`: 104 tests 통과
- `npm run build`: 통과

### 관리자 웹

- Node.js 22.22.2
- `npm test -- --watch=false`: 188 tests 통과
- `npm run build`: 통과
- 기존 초기 번들 예산 경고: 500 kB 기준 대비 33.49 kB 초과, 총 533.49 kB. 빌드는 성공했으며 이번 기능의 실패 조건은 아니다.

### 로컬 Nest 게이트웨이

- Node.js 24.19.0
- `npm run build`: 통과
- `node --test test/*.test.js`: 748 tests 통과

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

- `clipper_web_api`: `3e5bfbb`
- `clipper_web_client`: `7180d32`
- `clipper_web_admin`: `47d8e48`
- `clipper_nestjs`: `d9f4110`
- `clipper_angular`: `7938350`
- `clipper_electron`: `7f5d4d3`
- `clipper_infra`: `89920f8`

## 배포 전 주의

- `1786800000000-DropLegacyBilling`은 출시 전 구형 무통장 데이터와 구형 이용권·단일 잔액 테이블을 제거하는 파괴적 마이그레이션이다.
- 개발 서버에서는 코드 컨테이너를 교체하기 전에 admin DB 백업과 마이그레이션 대상 확인이 필요하다.
- 현재 검증은 기능 브랜치 기준이며 `dev` 병합과 배포는 수행하지 않았다.
