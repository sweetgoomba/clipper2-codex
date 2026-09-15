# 8개 저장소 병합안 갱신 — 2026-09-15

상태: 비교와 계획만 완료. 실제 merge/merge-tree, 새 integration 생성, 소스 수정, 테스트/빌드, commit/push/deploy 없음. 원격 fetch만 수행. 실제 서버 실행 SHA는 재조회하지 않았다.

기존 [9월11일 병합안](2026-09-11-main-integration-plan.md)의 파일별 조합 원칙을 유지하되 아래 최신 SHA와 추가 사항이 우선한다. main 고유 코드 제외, 옛 PG/밈 브랜치 자동 포함 금지. 대사 하이라이트 작업 브랜치도 별도로 유지. 전체 최신 dev가 대상이다.

제안 공통 브랜치 이름은 기존 `integration/main-unification-20260911`을 유지한다. 실제 생성 직전에 동일 이름 존재/최신 원격 SHA를 재확인한다. 운영 기준에서 시작하고 dev 양쪽 변경을 보존한다. 이번에는 브랜치를 만들지 않았다.

## 최신 기준

커밋 수는 운영/dev 각각에만 있는 이력 수이며 기능 수가 아니다. 공통 수정 파일 수는 실제 충돌 수가 아니다.

| 저장소 | 운영 기준 | dev 기준 | 운영 전용/dev 전용 | 양쪽 수정 파일 |
|---|---|---|---|---:|
| clipper_angular | c8b18677 | 019687d9 | 9 / 37 | 8 |
| clipper_electron | a34a39d5 | 0b43737c | 9 / 74 | 8 |
| clipper_nestjs | 780128a0 | e99b3962 | 8 / 43 | 1 |
| clipper_python | 260751d2 | 88b1da27 | 0 / 2 | 0 |
| clipper_infra | f948922c | 6cc7a379 | 15 / 2 | 6 |
| clipper_web_admin | cd3a3069 | beda584f | 41 / 26 | 9 |
| clipper_web_api | e0e5b356 | fdd0cb6b | 166 / 47 | 4 |
| clipper_web_client | 4d95a963 | 4b361efc | 57 / 0 | 0 |

Web Client만 dev 추가0이다. Python은 dev까지 fast-forward 가능하다. API·Admin·Infra·Angular·Electron·Nest는 운영과 dev가 갈라져 있어 양쪽 변경을 조합한다. **이전 계획의 Admin/Infra dev 추가0 판단은 더 이상 유효하지 않다.**

## 새로 추가된 조합 사항

### Angular

dev에 댓글 오버레이의 URL 프리필·영상 길이에 맞추기·Material 칩/모달과 베리에이션 전체선택·선택삭제가 추가됐다. 댓글 오버레이의 저장 계약은 Nest 신규 DTO와 함께 반영한다.

새 공통 수정3파일은 `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.ts`, 같은 spec, `src/features/variation-v2/state/variation-v2.store.ts`다. 운영의 렌더 전 크레딧 확인·실제 차감/잔액 표시·waitForPendingWrites를 유지하고 dev의 deleteMany/setAllSelected를 추가한다. 전체선택 직후 렌더에서도 저장 완료 후 선택 수로 크레딧을 확인해야 한다. 한쪽 파일 전체 채택은 금지한다.

기존 설정/프로젝트 화면의 운영 계정 링크 + dev 저장공간/동의 UI 조합은 유지한다. 복구50파일과 dev의 직접 겹침은 여전히 `src/core/bridge/clipper-bridge.ts` 하나다. dev telemetry/storage 계약과 복구 activeOwners를 함께 보존한다.

### Electron + Infra

**릴리스 설치본에 통계 수집 키가 없으면 빌드를 중단하는 dev 변경이 추가됐다.** buildInfo 유무로 릴리스를 판단한다. 이전 계획의 ‘키 없이 경고만’ 설명은 개발 빌드에만 적용한다. 이 검사를 없애지 않고 Infra runner의 releaseBuildEnv(job, env) 키 전달과 함께 반영한다. 실제 키 읽기/생성/수정은 이번 범위 밖이다.

운영 identity/프로토콜/userData·설치 분리, NSIS 검사, runner의 작업별 소스/의존성 분리 코드는 보존한다. dev의 GPU 벤더 조회 배선을 최신 telemetry wiring에 유지한다. 기존 production identity 허용목록 호환 조정도 여전히 필요하다.

Infra는 이제 양쪽 수정6파일: apps/compose.yml, env/stack.{dev,prod,stage}.env.example, runbooks/deploy-dev.md, runner/release-runner.mjs. 운영 PG 환경과 runner 격리를 유지하면서 서버 CLIPPER_DESKTOP_INGEST_KEYS 전달 및 빌드 CLIPPER_DESKTOP_TELEMETRY_INGEST_KEY 전달을 추가한다.

**미커밋 runbooks/deploy-prod.md와 새 dev 배포 문서가 겹친다.** 현재 운영 절차와 dev의 migration 설명을 조합해야 한다. migration 컨테이너의 실제 DB 네트워크·인증키 mount 등 운영 연결 조건을 확인해 문서로 맞춘 뒤 반영하며, 가져온 명령을 이번에 실행하지 않는다.

### Web API

진단 대시보드용 통계·기기 분포·서명 그룹 API가 추가됐다. 기존 PG 엔티티/마이그레이션을 보존하면서 DesktopSession, DesktopSignatureGroup과 dev 마이그레이션4개(1788950000000, 1788950100000, 1789000000000, 1789000100000)를 등록한다. 실제 DB 실행은 별도다.

package.json은 이제 양쪽 최종본이 동일하지 않다. 새 `test:tz` 스크립트를 보존한다. AppModule의 운영 PG 모듈과 DesktopTelemetry 모듈을 함께 유지하고 스케줄러 등록은 중복하지 않는다. 기존 lockfile 비교 원칙을 유지한다.

### Web Admin

진단 대시보드26커밋이 추가됐다. 기존 PG 회원/환불/상품/복구 화면과 접근 제한을 유지하면서 dev 진단 route/nav/API 모델/mock을 추가한다. 제거된 approvals 메뉴를 다시 살리지 않는다.

`desktop-errors.component.ts`에서는 운영의 공통 ModalComponent 사용을 보존하면서 dev의 바이트 포맷 개선을 적용한다. models.ts는 PG 결제/크레딧 타입과 진단 타입을 함께 유지한다. mock handler와 fixture는 새 진단 응답을 추가하되 운영 PG mock을 덮어쓰지 않는다. API와 Admin의 overview/devices 응답 계약을 같은 최신 기준으로 반영한다.

### Nest / Python / Web Client

Nest의 댓글 오버레이 맞추기 상태 DTO를 Angular와 함께 반영한다. 기존 Access/Credits 모듈 + dev StorageModule 조합은 유지한다. 복구 리소스30파일과 dev의 직접 겹침0이나 디스크 정리와 실행 중 런타임/파일 보호의 동작 연계 확인은 여전히 필요하다.

Python dev 기준은 이전과 동일하며2커밋을 전진 반영하는 관계다. TTS 개선과 복구5파일을 함께 유지한다. Web Client는 최신 운영에 dev가 포함돼 있어 dev 추가 변경이 없다.

## 미커밋과 실행 순서

1. 위 최신 운영/dev 기준을 확정한 뒤 공통 integration 작업 공간을 준비한다. 원본 공유 폴더는 다시 병합 작업 공간으로 사용하지 않는다.
2. 운영과 dev를 조합한다. 이번 문서는 승인 전 비교안이며 실제 충돌 발생 여부는 아직 확인하지 않았다.
3. 복구 worktree의 누적50파일 패치를 조합된 기준 위에 적용한다. 현재50파일 SHA-256이 복구 완료 기록과 모두 일치함을 재확인했다. 이전 CPU7·안전성37을 중복 적용하지 않는다.
4. Infra 미커밋5문서와 API 로컬 DB compose1을 반영할 범위로 보존한다. 이미 해소한 Admin/Client/API tracked 중복 변경은 다시 적용하지 않는다.
5. 사용자 승인 범위 내 검증/기록 후 별도 commit/push/main 승격을 판단한다. 현재는 테스트·빌드 미실행, 실제 ML·Build5 QA HOLD, 배포 금지 상태를 유지한다.

복구 작업본: `.worktrees/resource-safety-recovery-20260915/desktop/`의4repo, 브랜치 `recovery/resource-safety-20260915`. 상세는 [복구 기록](2026-09-15-resource-workspace-recovery.md). 원본 변경 정리는 [정리 기록](2026-09-15-source-control-cleanup.md).

## 전체 SHA와 공통 파일 증거

### clipper_angular

- 운영: `integration/toss-payments-pg-20260909` / `c8b186770ae6f77294a2a1689226834f05a8944a`
- dev: `019687d973bf988f85beee7a3756ec97a7d2d7df`
- 공통 수정 파일: `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.spec.ts`, `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.ts`, `src/features/variation-v2/state/variation-v2.store.ts`, `src/shell/projects/projects/projects.component.spec.ts`, `src/shell/projects/projects/projects.component.ts`, `src/shell/settings/settings/settings.component.html`, `src/shell/settings/settings/settings.component.spec.ts`, `src/shell/settings/settings/settings.component.ts`

### clipper_electron

- 운영: `integration/toss-payments-pg-20260909` / `a34a39d510bca51bf8b3e527d433ff9112c686fc`
- dev: `0b43737ca22fe0bf48ea46a73fcf95068cf538f5`
- 공통 수정 파일: `scripts/build-app.mjs`, `scripts/build-runtime-config.mjs`, `src/main/auth/deeplink.ts`, `src/main/config/packaged-runtime-config.ts`, `src/main/main.ts`, `test/build-runtime-config.test.mjs`, `test/main-boot-order-boundary.test.js`, `test/quit-coordinator.test.js`

### clipper_nestjs

- 운영: `integration/toss-payments-pg-20260909` / `780128a069c38a9df6438cc64d79f7a2e42bc1ea`
- dev: `e99b3962956343eb9272f7e9d4869f472d8ab180`
- 공통 수정 파일: `src/app.module.ts`

### clipper_python

- 운영: `integration/toss-payments-pg-20260909` / `260751d2fa5be8a5a9cd8e346c60ba22d1512ed9`
- dev: `88b1da277922cc5734a3e72e32425aa4054fa158`
- 공통 수정 파일: 없음

### clipper_infra

- 운영: `integration/toss-payments-pg-20260903` / `f948922c812ab583a84e4a64c5d8faa423afe294`
- dev: `6cc7a3796409b931b7e13240826496fd3e8f5b73`
- 공통 수정 파일: `apps/compose.yml`, `env/stack.dev.env.example`, `env/stack.prod.env.example`, `env/stack.stage.env.example`, `runbooks/deploy-dev.md`, `runner/release-runner.mjs`

### clipper_web_admin

- 운영: `release/pg-expiry-20260910` / `cd3a3069310bdae13f123615e1a1a2a8972187cd`
- dev: `beda584fde924a9a97aa69f1856cbddafe69c94c`
- 공통 수정 파일: `src/app/core/api/mock/mock-api.interceptor.spec.ts`, `src/app/core/api/mock/mock-api.interceptor.ts`, `src/app/core/api/mock/mock-data.ts`, `src/app/core/api/models.ts`, `src/app/features/portal/desktop-errors/desktop-errors.component.ts`, `src/app/features/portal/portal.routes.spec.ts`, `src/app/features/portal/portal.routes.ts`, `src/app/shared/layout/app-header/app-header.component.spec.ts`, `src/app/shared/layout/app-header/app-header.component.ts`

### clipper_web_api

- 운영: `release/pg-expiry-20260910` / `e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5`
- dev: `fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6`
- 공통 수정 파일: `package-lock.json`, `package.json`, `src/app.module.ts`, `src/core/database/admin.datasource.ts`

### clipper_web_client

- 운영: `integration/toss-payments-pg-20260903` / `4d95a963cde6f4e4067244c6cc8c148bb66709ce`
- dev: `4b361efc742db797e85848c5aea90eb1736194c5`
- 공통 수정 파일: 없음
