# 개발·운영 웹 서버 직접 빌드와 DB migration 분리

> 승인 범위: 원본 저장소의 integration 브랜치에서 로컬 구현·검증만 한다. 서버 명령은 사용자가 실행한다. dev/main merge, push, 배포, 실제 DB 접근은 하지 않는다.

## 목표와 결정

- `deploy-dev.sh web|admin|api|all`, `deploy-prod.sh web|admin|api|all`로 동일하게 선택한다. 기본값 all, 기존 client/web-client/web-admin 별칭을 유지한다.
- 공통 실행부는 Node(기존 PG 환경 검증도 Node 필요)를 사용한다. Git/Docker만 외부 명령으로 실행하고 비밀이 포함된 Compose 설정은 메모리에서 검증하며 출력하지 않는다.
- 서버 원본 저장소는 개발 dev, 운영 main을 사용한다. 다른 브랜치 또는 미커밋 변경은 자동으로 바꾸지 않고 중단한다. 소스는 fast-forward로만 갱신한다.
- 잘못된 인자는 Git 갱신 전 거절한다. 대상 저장소 전체를 점검한 다음 갱신·순차 빌드한다. infra 갱신 시 새 실행부로 한 번 재실행한다.
- 개발 이미지는 기존 로컬 이름과 dev 태그, 운영 이미지는 같은 이름과 prod 태그. 이미지에 소스 SHA 라벨과 환경-SHA 보조 태그를 자동으로 붙인다. 사용자 입력 명령은 매번 동일하다.
- `--build-only`는 앱을 시작하지 않는다. 기본 배포는 빌드 후 선택한 서비스만 재생성하며 migration을 실행하지 않는다.
- 검증 중 추가한 `--start-only`는 소스 갱신·재빌드 없이 이미 준비한 로컬 이미지만 시작한다. migration 직후 새 커밋을 받아 코드/DB 검증 기준이 달라지는 것을 방지한다.
- Angular의 기존 production 설정(최적화된 개발 서버용)을 유지한다. `production,deployment-prod` 조합에서만 운영 API로 교체한다. Docker ARG 기본 production으로 기존 개발 빌드 호환성을 유지한다.
- `migrate-db.sh dev|prod`: 해당 환경의 이미 빌드된 로컬 API 이미지로 User → Admin → Release migration만 실행한다. pull/build/up/seed/revert를 하지 않는다. 이미지 없으면 중단한다. DB 이름/호스트/포트 누락과 dev/prod 이름 불일치를 거절한다. 명시적인 터미널 확인 후 실행한다.
- migration은 DB별 적용 이력을 따르며 3개 DB를 하나의 트랜잭션으로 묶지 못한다. 실패하면 다음 DB를 실행하지 않는다. 앱 중단 여부/백업/실제 DB 대상 검토는 실행자가 사전에 결정한다.
- 운영 앱 이름·아이콘·프로토콜 및 Windows runner 분리는 이번 작업에서 제외한다. 기존 개발판은 변경하지 않는다.

## TDD 순서

1. `web/clipper_infra/scripts/deployment.test.mjs`에서 실제 실행 스크립트를 임시 fixture에 복사하고, git/docker 외부 경계만 가짜 실행파일로 대체한다. 잘못된 입력, 잘못된 브랜치/dirty, dev/prod 빌드 인자, 단일 서비스, all, 빌드 실패, build-only, migration 확인/순서/중단/환경 오류를 테스트한다. 먼저 실패를 확인한다.
2. 같은 디렉터리에 `deployment.mjs`, `deploy-prod.sh`, `migrate-db.sh`를 추가하고 `deploy-dev.sh`를 얇은 공통 실행부 호출로 바꾼다. Node 테스트를 재실행한다.
3. 웹 Customer/Admin의 Dockerfile에 ANGULAR_CONFIGURATION 인자를 추가한다. angular.json에 deployment-prod 파일 교체, environment.deployment-prod.ts에 운영 API를 추가한다. 실제 Angular 빌드를 임시 출력 경로로 실행하여 API 문자열 포함/배제를 검사하는 테스트를 먼저 작성한다.
4. API Dockerfile에 기존 `scripts/typeorm-run-migration.mjs`를 runtime으로 복사한다. runtime에서 재빌드 없이 그 실행기를 호출한다. TypeScript 빌드 및 runtime 파일 경로·의존성 확인. 실제 migration은 실행하지 않는다.
5. infra 운영 env example의 GHCR 이미지 이름을 로컬 이미지 이름으로, bind IP를 관찰된 m4-prod IP로 수정한다. 비밀값은 만들지 않는다.
6. 검증: `node --test scripts/deployment.test.mjs`, 웹 dev/prod 실제 빌드와 결과 URL 검사, `npm run build`(API), Compose 예제 구성 검사(가짜 값만), 쉘 문법, 저장소별 `git diff --check`. 실제 Docker 빌드/서버 재시작/DB migration을 수행한 것으로 주장하지 않는다.
7. `.codex/main`에 사용법·결과·남은 수동 검증을 기록한다. 원격 서버의 env/secret, main 브랜치 준비, 새 운영 DB, PG/Google callback, 프록시/TLS는 별도 수동 단계로 유지한다.

## 로컬 실행 결과

- 1–7 로컬 구현 및 검증 수행. 별도 코드 리뷰 후 보완 사항은 사용법 문서와 조사 로그에 남긴다.
- 배포 22개 + PG/Compose 71개 + 실제 Angular 빌드 4개 = 97개 통과. 별도 코드 리뷰에서 Critical/Important 지적 없음. 제안된 infra 재실행 경로 테스트 2개도 추가하고 통과했다.
- API 빌드 통과, datasource 3 suite/6 tests 통과. 실제 DB 연결 없음.
- 서버 실행 단계는 수행하지 않음. Docker runtime 전체 빌드는 아직 검증하지 않음.
- [사용법과 남은 검증](./2026-09-07-web-dev-prod-local-build-deployment-guide.md)
