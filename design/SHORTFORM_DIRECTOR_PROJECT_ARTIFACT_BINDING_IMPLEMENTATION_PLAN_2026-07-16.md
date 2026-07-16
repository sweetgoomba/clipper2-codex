# AI 숏폼 디렉터 — 프로젝트 artifact 연결 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`

## Task 1 — RED 계약

- [x] project-scoped locator와 sanitized candidate 계약 테스트를 추가한다.
- [x] owned/source 분류, 원격·검색·render 제외, 파일 검증 실패 제외 테스트를 추가한다.
- [x] 권리 미확인, origin 불일치, unknown layer 연결 거부 테스트를 추가한다.
- [x] 연결 후 resolved, 해제 후 missing, orphan ref 정리 테스트를 추가한다.
- [x] Angular 전용 API URL과 picker 동작 RED를 추가한다.

## Task 2 — NestJS candidate와 binding

- [x] AssetRef의 단일 artifact ID를 project artifact locator로 교체한다.
- [x] candidate 조회 service를 추가한다.
- [x] local project/source file availability를 서버에서 검증한다.
- [x] deterministic AssetRef 등록과 layer binding upsert를 구현한다.
- [x] binding 해제와 orphan AssetRef 정리를 구현한다.
- [x] controller DTO와 GET/PUT/DELETE endpoint를 추가한다.
- [x] `ProjectsModule`만 director module에 연결하고 provider/render 의존성은 추가하지 않는다.

## Task 3 — Angular picker UX

- [x] candidate, locator, binding request 타입을 반영한다.
- [x] candidate 조회·binding·해제 service 메서드를 추가한다.
- [x] owned/source pending requirement에만 lazy picker를 표시한다.
- [x] 권리 확인 checkbox와 연결 action을 추가한다.
- [x] 연결된 AssetRef label과 연결 해제를 표시한다.
- [x] search/generated/unresolved/provider/render control 부재를 회귀 검증한다.

## Task 4 — 검증과 문서

- [x] Nest director 집중 테스트와 build를 실행한다.
- [x] Angular director 집중 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로가 `origin/dev` 대비 변경 없는지 확인한다.
- [x] path/URL 저장·응답 방지와 secret-like token, trailing whitespace를 검사한다.
- [x] foundation 설계, session, handoff, 상위 방향 문서를 갱신한다.
- [x] provider/server/Electron/migration/commit/push를 실행하지 않는다.
