# AI 숏폼 디렉터 플러그인 foundation — 구현 계획

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`

## Task 1 — 기존 플러그인 비침범 기준 고정

- [x] Nest의 기존 Phase 1a uncommitted backfill/model 변경 제거
- [x] `src/modules/shortform/**`, `src/modules/shortform-core/**`가 `origin/dev`와 동일한지 확인
- [x] Angular `src/features/shortform/**`가 `origin/dev`와 동일한지 확인

## Task 2 — 실패 테스트 작성

- [x] Nest catalog/registry가 `shortform_director`를 별도 virtual workflow로 요구하는 테스트
- [x] Vira envelope lifecycle validator RED 테스트
- [x] director service/repository의 별도 store·native draft RED 테스트
- [x] Angular central metadata와 별도 route/service RED 테스트

## Task 3 — Nest foundation 구현

- [x] `shortform_director` plugin catalog 등록
- [x] director domain model과 Vira envelope validator 구현
- [x] 별도 repository/service/controller/module 구현
- [x] `AppModule`에 새 module 조립
- [x] focused tests GREEN

## Task 4 — Angular plugin shell 구현

- [x] `shortform_director` metadata/provider/route 등록
- [x] 별도 model/service 구현
- [x] 4파일 분리된 director page 구현
- [x] campaign prompt → planning draft 생성과 목록 표시
- [x] focused tests GREEN

## Task 5 — 검증·문서화

- [x] Nest build/focused tests
- [x] Angular focused tests/build
- [x] 기존 shortform 경로 diff 0 확인
- [x] 전체 diff/status/whitespace 확인
- [x] `.codex` session/handoff 갱신
- [x] commit/push 없이 보고

## 구현·검증 결과

- Nest `shortform-director-foundation` 4개 계약 테스트 통과
- Nest plugin catalog/install/workflow registry 관련 테스트 포함 16개 통과
- Angular director 등록·API·화면 테스트 4개 통과
- Angular plugin status 회귀를 포함한 집중 테스트 17개 통과
- Nest TypeScript build, Angular production build 통과
- Nest 기존 `src/modules/shortform/**`, `src/modules/shortform-core/**`는 `origin/dev` 대비 diff 0
- Angular 기존 `src/features/shortform/**`는 `origin/dev` 대비 diff 0
- 커밋·push·서버 실행 없이 작업 유지
