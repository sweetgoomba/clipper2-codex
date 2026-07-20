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

## Task 6 — 2026-07-20 실제 peak RSS evidence 후속 적용

- [x] benchmark Node process와 recursive descendant를 같은 snapshot에서 합산한다.
- [x] Chrome/Remotion compositor child가 포함되고 unrelated sibling/sampler가 제외되는 RED/GREEN test를 추가한다.
- [x] 100ms sample의 aggregate peak를 candidate `peakRssBytes`로 연결한다.
- [x] PID/raw command/path 없이 sample/peak/process-kind만 portable summary에 기록한다.
- [x] actual full benchmark에서 Chrome, Remotion compositor와 FFmpeg 관측을 확인한다.
- [x] raw metric을 automated performance threshold나 순위로 승격하지 않는다.
- [x] Windows sampler와 packaged runtime은 후속 gate로 남긴다.

실행 결과:

- environment: `darwin-arm64-node24-remotion4.0.489-local`
- sample interval/count: 100ms / 725
- process-tree peak RSS: 2,296,545,280 bytes
- candidate benchmark metadata check: pass
- full automated conformance: 7/7 pass
- manual review: pending

## Task 7 — 2026-07-20 Motion Canvas cache/RSS evidence

- [x] Motion Canvas static source bundle에 SHA-256 revision cache를 적용한다.
- [x] 같은 revision의 actual full rerun에서 bundler가 생략되고 `reused`가 기록되는지 확인한다.
- [x] worker root와 Chrome/FFmpeg recursive descendants의 동시 RSS peak를 측정한다.
- [x] PID/command/path 없이 portable evidence를 남긴다.
- [x] representative output/frame count/media contract를 검증한다.
- [x] raw elapsed/RSS를 Remotion과의 자동 순위나 threshold로 사용하지 않는다.

실행 결과:

- source revision: `sha256:aad28738ac9d7cb12a2603681e593b933d04b7dbc810970cdb97f5cc8c0cf271`
- cache: `reused`
- elapsed: 21,037ms
- output: 2,072,173 bytes, 41.2초, 1,236 frame, 1080×1920, H.264/AAC
- sample count: 106
- process-tree peak RSS: 1,941,848,064 bytes
- observed child: Chrome, FFmpeg, other
- manual review: synthetic input이므로 pending
