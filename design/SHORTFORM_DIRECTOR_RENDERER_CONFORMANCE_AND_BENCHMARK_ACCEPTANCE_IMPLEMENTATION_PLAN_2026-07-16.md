# AI 숏폼 디렉터 — Renderer conformance와 benchmark acceptance 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_CONFORMANCE_AND_BENCHMARK_ACCEPTANCE_DESIGN_2026-07-16.md`

## Task 1 — Representative profile RED/GREEN

- [x] execution bundle에서 deterministic profile id와 input fingerprint를 만든다.
- [x] 대표 41.2초 recipe/stage counts와 output expectation을 고정한다.
- [x] recipe 구조에서 provider-neutral required capability를 도출한다.
- [x] path/URL/provider/model/credential을 profile에 넣지 않는다.

## Task 2 — Motion checkpoint RED/GREEN

- [x] sequence-card의 5개 reference frame을 semantic state checksum으로 만든다.
- [x] overlay/primitive/sampler/frame identity를 보존한다.
- [x] unsupported/malformed motion contract를 조용히 무시하지 않는다.

## Task 3 — Candidate automated evaluator RED/GREEN

- [x] profile/report/adapter identity를 검증한다.
- [x] required capability와 exact staged input set을 검증한다.
- [x] output/timeline expectation을 검증한다.
- [x] duration tolerance를 정확히 1 frame으로 계산한다.
- [x] missing/extra/duplicate/mismatch를 자동 실패로 보고한다.

## Task 4 — Benchmark/manual boundary RED/GREEN

- [x] environment/revision/elapsed/output bytes/optional peak RSS metadata를 검증한다.
- [x] 성능 metric을 pass/fail threshold나 순위에 사용하지 않는다.
- [x] 기존 manual 7축을 single source of truth로 재사용한다.
- [x] automated_failed/manual_review_required/manual_rejected/accepted를 결정한다.
- [x] 평균·가중치·100점 총점을 추가하지 않는다.

## Task 5 — 회귀와 문서

- [x] production Director adapter가 계속 0개임을 검증한다.
- [x] Nest Director 전체와 generic renderer boundary 회귀를 실행한다.
- [x] Nest build와 `git diff --check`를 실행한다.
- [x] 기존 shortform/shortform-core와 code-repo docs 변경 0을 확인한다.
- [x] secret-like pattern과 path/URL 노출을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] renderer/provider/API/UI/Jobs executor/server/Electron/DB/migration/runner를 실행하지 않는다.
- [x] commit/push/deploy를 실행하지 않는다.
