# TossPayments PG release candidate 통합 계획

> 실행 규칙: 이 계획은 `superpowers:executing-plans`, `superpowers:test-driven-development`,
> `superpowers:systematic-debugging`, `superpowers:verification-before-completion` 순서로 따른다.
> 사용자의 명시적 지시에 따라 새 worktree나 별도 복제본을 작업 정본으로 쓰지 않고,
> 각 원본 저장소에서 integration 브랜치를 만들어 사용한다.

- 작성일: 2026-09-03 (Asia/Seoul)
- 목표: 7개 PG 기능 브랜치의 필요한 변경을 각 저장소의 최신 `origin/dev`에 통합하고,
  실제 배포 전까지 반복 검증할 수 있는 로컬 release candidate를 만든다.
- 정본 정책:
  - `2026-09-03-toss-payments-pg-session-handoff-and-integration-readiness.md`
  - `2026-09-02-toss-payments-pg-final-policy-delta.md`
  - `2026-09-02-toss-payments-pg-final-policy-delta-implementation-plan.md`
  - `2026-09-02-toss-payments-pg-final-policy-delta-verification-report.md`
- 통합 기록: `2026-09-03-toss-payments-pg-release-candidate-integration-log.md`

## 반드시 지킬 경계

- 기존 7개 PG worktree와 그 브랜치는 조회만 한다. 수정, rebase, merge, commit하지 않는다.
- 원본 저장소의 로컬 `dev` ref는 최신 `origin/dev`와 같은 상태로 유지하며 새 기능을 합치지 않는다.
- 실제 통합은 각 원본 저장소에서 `dev`가 아니라
  `integration/toss-payments-pg-20260903` 브랜치를 checkout한 상태로 진행한다.
- 기존 7개 PG worktree는 그대로 두며, 새 worktree나 별도 repository 복제본을 통합 작업 장소로
  만들지 않는다.
- `meme-overlay-timeline-seek`와 `origin/feat/ai-video-generation-merge`는 통합하지 않는다.
- Customer의 기존 untracked `build/`와 API의 `docs/api/openapi.yaml.orig`는 건드리거나
  stage하지 않는다.
- 현재 개발 DB 및 5433/5434/5435 DB에는 migration이나 쓰기를 하지 않는다.
- migration 검증이 필요하면 이번 통합만을 위해 만든 빈 DB 또는 폐기 가능한 복제 DB만 쓴다.
- 서버 접속, 배포, production DB 생성, DNS/NPM 변경, 라이브 결제·환불은 하지 않는다.
- 서버별 확인과 설정은 사용자가 해당 PC에 직접 접속한 상태에서만 진행한다. Codex는 실행할
  명령과 확인 기준을 제공하고, 사용자가 실행해 전달한 결과만 해석한다.
- secret, token, 결제 자격증명 및 민감한 결제 데이터는 터미널이나 문서에 출력하지 않는다.
- 계획과 진행 로그 등 세션 문서는 `.codex` 아래에만 만든다.

## 쉽게 보는 전체 순서

1. 원본 7개 저장소가 깨끗한지 다시 확인한다.
2. 원본 저장소를 `dev`로 바꾸고 최신 `origin/dev`까지 fast-forward한다.
3. 같은 원본 저장소에서 최신 `origin/dev`를 시작점으로 integration 브랜치를 만들고 checkout한다.
   기존 PG worktree는 그대로 둔다.
4. API를 가장 먼저 통합한다. API 계약과 DB 등록 목록이 다른 화면들의 기준이기 때문이다.
5. Admin과 Customer를 API 계약에 맞춰 통합한다.
6. Angular, NestJS, Electron은 오래된 브랜치를 통째로 합치지 않고 현재 구조에도 필요한 PG
   변경만 골라 옮긴다.
7. Infra 파일은 원본 저장소의 integration 브랜치에 후보 설정으로만 합치고, 실제 PC에는 적용하지
   않는다. 서버 확인이나 설정은 사용자가 각 PC에서 직접 명령을 실행할 때만 안내한다.
8. 저장소마다 작은 단위로 테스트하고 checkpoint commit을 만든다.
9. 마지막에 7개 저장소가 같은 API 계약과 정책을 쓰는지 함께 검증한다.

## API 충돌을 쉬운 말로 설명

### OpenAPI 문서

`openapi.yaml`은 웹 화면과 서버가 서로 어떤 주소와 데이터 형식을 쓸지 정한 메뉴판이다.
최신 `dev`는 스토리보드 메뉴를, PG 브랜치는 결제 메뉴를 추가했다. 한쪽 파일을 선택하면 다른
기능의 메뉴가 사라지므로 두 메뉴와 데이터 형식을 한 문서에 함께 넣고 검사한다.

### 서버 시작 목록

`app.module.ts`는 서버 시작 시 켤 기능의 목록이다. 최신 `dev`의 AI 디렉터·스토리보드 기능과
PG 브랜치의 상품·크레딧·결제·환불 기능을 모두 등록한다. 중복 등록과 빠진 등록을 테스트한다.

### DB 등록 목록

`admin.datasource.ts`와 `user.datasource.ts`는 서버가 알고 있어야 할 DB 표와 migration의
목록이다. 최신 `dev`의 스토리보드 표와 PG 브랜치의 결제 표를 함께 등록한다. 이 단계에서는
목록과 순서만 검사하며 현재 DB에는 절대 실행하지 않는다.

### 이미지 검색 처리

최신 `dev`는 사용자가 고른 정확한 API 키와 버전을 사용하도록 보호한다. PG 브랜치는 크레딧이
들어가는 작업이 실제로 시작·성공·실패했는지 근거를 남긴다. 최종 코드는 정확한 키를 사용하면서
동시에 과금 근거도 남겨야 한다.

### 작업 종류와 크레딧 계산

최신 `dev`는 AI 디렉터의 설정·준비 동작을 무료로 유지하고 더 이상 쓰지 않는 작업 종류를
정리한다. PG 브랜치는 실제 유료 렌더링을 입력 방식별 작업 종류로 나누고 새 크레딧 장부에서
차감·실패 복구·근거 저장을 처리한다. 무료 준비 동작은 계속 무료로 두고, 실제 유료 렌더링만
새 장부를 쓰게 합친다.

### 테스트 파일

각 브랜치가 자기 기능을 기준으로 예상 결과를 바꿨기 때문에 테스트도 충돌한다. 한쪽 테스트를
버리지 않고, 최신 기능과 PG 기능을 동시에 확인하는 테스트로 다시 구성한다.

## 저장소별 실행 계획

### Task 1: 원본 저장소 최신화와 integration 브랜치 준비

대상 저장소:

- `web/clipper_web_api`
- `web/clipper_web_admin`
- `web/clipper_web_client` (Customer)
- `desktop/clipper_angular`
- `desktop/clipper_nestjs`
- `desktop/clipper_electron`
- `web/clipper_infra`

실행:

1. 원본과 PG worktree의 branch, HEAD, status를 다시 기록한다.
2. 각 원본에서 `git fetch origin dev`, `git switch dev`,
   `git merge --ff-only origin/dev`를 실행한다.
3. 원본 `dev` HEAD가 `origin/dev`와 같은지 확인한다.
4. 같은 원본 저장소에서 `origin/dev`를 출발점으로
   `integration/toss-payments-pg-20260903` 브랜치를 만들고 checkout한다.
5. 원본 저장소의 integration 브랜치가 맞는지, 로컬 `dev` ref는 계속 `origin/dev`와 같은지 확인한다.
6. 기존 PG worktree의 `feature/toss-payments-pg-integration` HEAD가 인수인계 문서의 값과 같은지
   다시 확인한다.
7. 결과를 통합 로그에 기록하고 `.codex` checkpoint commit을 만든다.

브랜치 준비 명령은 원본 저장소마다 아래 순서로 실행한다. 기존 PG worktree에서는 실행하지 않는다.

```bash
git fetch origin dev
git switch dev
git merge --ff-only origin/dev
git switch -c integration/toss-payments-pg-20260903 origin/dev
```

### 공통 검증 명령

| 저장소 | 좁은 테스트 뒤 실행할 전체 검증 |
|---|---|
| Web API | `npm test -- --runInBand`, `npm run build` |
| Web Admin | `npm test -- --watch=false`, `npm run build` |
| Web Customer | `npm test -- --watch=false`, `npm run build` |
| Angular | `npm test -- --watch=false`, `npm run build` |
| NestJS | `npm run build`, 그 다음 `node --test test/*.test.js` |
| Electron | `npm test`, `npm run build` |
| Infra root | `node --test scripts/validate-toss-review-env.test.mjs runner/release-runner.test.mjs runner/release-runner-server.test.mjs runner/windows/windows-scripts.test.mjs` |
| Infra monitor | `ops/monitor`에서 `npm test` |

의존성 설치 직후의 최신 `origin/dev` 기준선에서도 같은 명령을 실행한다. 기준선부터 실패하면
PG 통합 실패와 섞지 않고 원인과 기존 실패 여부를 로그에 먼저 기록한다. 테스트 명령 자체가
현재 설정과 맞지 않으면 실패를 숨기지 않고 해당 저장소 지침에 맞는 명령으로 고친 뒤 계획과
로그를 함께 갱신한다.

### Task 2: Web API 계약과 시작 목록 통합

주요 파일:

- `docs/api/openapi.yaml`
- `src/app.module.ts`
- `src/core/database/admin.datasource.ts`
- `src/core/database/user.datasource.ts`
- 각 datasource spec

방법:

1. 전체 PG 브랜치를 `--no-commit`으로 merge해 충돌 지점을 고정한다.
2. 최신 `dev`와 PG 브랜치의 관련 테스트를 먼저 모아 실행하고 실패를 확인한다.
3. OpenAPI에는 최신 스토리보드 계약과 PG 결제 계약을 모두 보존한다.
4. module과 datasource에는 양쪽 기능을 모두 등록하고 중복·누락을 막는 테스트를 먼저 고친다.
5. OpenAPI 검사, 관련 단위 테스트, TypeScript build 순으로 통과시킨다.
6. 현재 DB에는 접속하지 않는다.
7. 충돌 원인, 보존 기능, 해결 방식, 테스트, 남은 위험을 로그에 쓰고 merge checkpoint를 만든다.

### Task 3: Web API 작업·과금 흐름 통합

주요 파일:

- `src/modules/api-keys/presentation/media-search.controller.ts`
- `src/modules/operations/application/operations.service.ts`
- `src/modules/operations/domain/operation-definitions.ts`
- 위 파일의 spec

TDD 순서:

1. 정확한 credential ID/revision과 과금 근거 기록이 한 요청에서 함께 지켜지는 테스트를 작성해
   먼저 실패시킨다.
2. 무료 AI 디렉터 동작과 유료 렌더링 작업이 올바르게 나뉘는 테스트를 먼저 실패시킨다.
3. 새 크레딧 장부 차감, 잔액 부족, 실패 시 복구, 성공·실패 근거 저장 테스트를 먼저 실패시킨다.
4. 필요한 최소 코드만 수정해 각 테스트를 통과시킨다.
5. API 전체 테스트와 build를 실행한다.
6. migration은 정적 검사 후 별도 빈 DB 검증 계획을 세운다.
7. API checkpoint commit과 로그 checkpoint를 만든다.

### Task 4: Web Admin 통합

보존할 기능:

- 최신 `dev`: Gemini/YouTube/Director 자격증명 관리, 최신 화면 구조, desktop 오류 추적
- PG: 상품·가격·크레딧·결제·구독·환불 운영 화면

방법:

1. PG 브랜치 전체를 merge한다.
2. mock API, API model, header 충돌에 대해 양쪽 화면을 모두 여는 테스트를 먼저 실패시킨다.
3. 최신 화면 메뉴와 PG 운영 메뉴를 함께 보존한다.
4. 관련 단위 테스트, 전체 테스트, build를 실행한다.
5. 로그와 checkpoint commit을 만든다.

### Task 5: Web Customer 통합

보존할 기능:

- 최신 고객 화면과 로그인·계정 흐름
- PG의 상품 보기, 무료 체험, 결제, 구독 변경, 크레딧, 취소·환불 상태 표시

방법:

1. 원본 저장소의 integration 브랜치에서 PG 브랜치 전체를 merge한다. 기존 PG worktree의
   untracked `build/`는 건드리지 않는다.
2. API OpenAPI 계약과 화면 요청 형식이 맞는지 테스트를 먼저 실행한다.
3. 정책별 상태와 오류 표시 테스트를 보강한 뒤 구현을 맞춘다.
4. 단위 테스트, 전체 테스트, build를 실행한다.
5. 로그와 checkpoint commit을 만든다.

### Task 6: Desktop Angular 변경 선별 이식

원칙:

- 694개 최신 `dev` 전용 commit을 오래된 PG 브랜치로 되돌리지 않는다.
- 최신 UI foundation, 메모리 최적화, 현재 plugin/settings 구조를 기준으로 한다.
- PG 브랜치의 6개 commit 중 현재도 필요한 결제 포털 연결과 표시만 골라 옮긴다.
- meme overlay와 AI video merge는 포함하지 않는다.

TDD와 검증:

1. 현재 settings/plugin 화면에서 필요한 PG 진입 동작을 테스트로 먼저 표현한다.
2. 실패를 확인한 뒤 필요한 최소 변경만 이식한다.
3. 관련 Angular 테스트, 전체 테스트, build를 실행한다.
4. 로그와 checkpoint commit을 만든다.

### Task 7: Desktop NestJS 변경 선별 이식

원칙:

- 최신 module/plugin/render 구조와 메모리 최적화를 유지한다.
- PG 브랜치의 7개 commit을 파일 단위가 아니라 동작 단위로 검토한다.
- API의 최종 접근·크레딧 정책과 맞는 portal handoff만 이식한다.
- 모든 플랜에서 같은 플러그인을 쓸 수 있고 크레딧이 없는 기능은 구독과 무관하게 쓸 수 있다는
  최종 정책을 깨는 plugin 차단은 넣지 않는다.

TDD와 검증:

1. 무료 기능이 구독 상태 때문에 차단되지 않는 테스트를 먼저 둔다.
2. 결제·크레딧 포털 이동 계약이 필요하면 그 테스트를 먼저 실패시킨다.
3. 필요한 최소 코드만 이식한다.
4. 관련 NestJS 테스트, 전체 테스트, build를 실행한다.
5. 로그와 checkpoint commit을 만든다.

### Task 8: Desktop Electron 변경 선별 이식

원칙:

- 최신 Electron 보안·메모리·프로세스 구조를 유지한다.
- PG 브랜치의 3개 commit에서 현재도 유효한 연결 부분만 고른다.
- 플러그인 실행이나 모델 설치를 구독 상태로 일괄 차단하는 과거 구현은 최종 정책과 충돌하므로
  이식하지 않는다.

TDD와 검증:

1. 무료 기능이 결제 상태 때문에 막히지 않는 테스트를 먼저 둔다.
2. 필요하다면 `/app/credits` 같은 일반 포털 연결 계약만 테스트로 고정한다.
3. 필요한 최소 코드만 이식한다.
4. 관련 Electron 테스트와 build를 실행한다.
5. 로그와 checkpoint commit을 만든다.

### Task 9: Infra 로컬 후보 설정 통합

원칙:

- PG 브랜치 전체를 로컬 integration 브랜치에 merge한다.
- 과거 3대 서버 가정을 현재 `m2-db`, `m2-proxy`, `m2-stage`, `m4-prod`, `storage`에 자동으로
  대응시키지 않는다.
- 어떤 서버에도 SSH 접속하거나 명령을 실행하지 않는다.
- 실제 확인이 필요한 항목은 PC별로 “사용자가 실행할 읽기 전용 명령, 가려야 할 출력, 판단
  기준” 형식의 체크리스트만 `.codex`에 작성한다.
- 사용자가 결과를 전달하기 전에는 서버 설정 파일 수정·배포 절차를 확정하지 않는다.

검증:

1. 로컬 설정 문법과 정적 테스트만 실행한다.
2. secret 값이 파일이나 diff에 들어가지 않았는지 확인한다.
3. 서버별 미확인 사항을 로그의 남은 위험으로 남긴다.
4. 로그와 checkpoint commit을 만든다.

### Task 10: 폐기 가능한 DB에서 migration 검증

진입 조건:

- 사용할 DB가 현재 개발 DB 및 5433/5434/5435가 아님을 명확히 증명할 수 있어야 한다.
- 접속 문자열에 secret을 출력하지 않아야 한다.
- 조건을 만족하지 못하면 실행하지 않고 미검증 위험으로 남긴다.

검증 내용:

1. 빈 DB에서 전체 migration을 처음부터 끝까지 실행한다.
2. `1785100000000` 중복 timestamp 두 개가 runner에서 모두 안전하게 처리되는지 확인한다.
3. `1786560000000`, `1786650000000`, `1786800000000`의 데이터 삭제 조건을 fixture로 검증한다.
4. 기존 무통장 주문·이벤트·장부 데이터가 어떤 조건에서 삭제되는지 정확히 기록한다.
5. 실제 운영 이관 전 별도 백업·변환 절차가 필요하다는 점을 release blocker로 판단한다.

### Task 11: 전체 release candidate 검증

1. 7개 통합 브랜치의 status와 commit을 기록한다.
2. 각 저장소의 전체 테스트와 build를 새로 실행해 결과를 저장한다.
3. API 계약과 Admin/Customer/Desktop 호출이 맞는지 교차 확인한다.
4. 제외하기로 한 meme overlay와 AI video merge가 들어오지 않았는지 확인한다.
5. 기존 PG worktree가 처음과 같은 branch/HEAD/status인지 다시 확인한다.
6. 현재 개발 DB와 서버에 변경이 없었음을 확인한다.
7. 남은 수동 검증과 배포 전 위험을 로그에 정리한다.
8. `superpowers:requesting-code-review`와 `superpowers:verification-before-completion` 절차를 거친다.
9. 사용자가 별도로 승인하기 전에는 `dev` merge, push, 배포를 하지 않는다.

## 저장소별 완료 기록 형식

각 checkpoint에서 통합 로그에 아래 다섯 항목을 쉬운 문장으로 적는다.

1. 충돌 원인: 두 브랜치가 왜 같은 부분을 다르게 바꿨는가.
2. 보존 기능: 최신 `dev`에서 지킬 기능과 PG에서 가져올 기능은 무엇인가.
3. 해결 방식: 어느 코드를 어떻게 합쳤는가.
4. 실행한 테스트: 실제 명령, 성공/실패, 테스트 개수 또는 핵심 결과는 무엇인가.
5. 남은 위험: 자동 테스트로 확인하지 못했거나 사용자 확인이 필요한 것은 무엇인가.
