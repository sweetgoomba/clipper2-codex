# AI 숏폼 디렉터 — Renderer adapter와 operation foundation 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_DESIGN_2026-07-16.md`

## Task 1 — Private stage recipe RED/GREEN

- [x] stage private manifest에 exact RenderRecipe를 저장한다.
- [x] public stage 응답은 변경하지 않는다.
- [x] stored recipe canonical checksum과 stage recipe checksum을 검증한다.
- [x] 기존 recipe 없는 stage는 unsafe execution bundle로 읽지 않는다.

## Task 2 — Execution bundle RED/GREEN

- [x] recipe visual/TTS source exact set과 stage input을 검증한다.
- [x] sourceId 기반 private staged input resolver를 제공한다.
- [x] unknown source, tampered staged file, recipe/stage mismatch를 거부한다.
- [x] original project/source path를 bundle metadata에 넣지 않는다.

## Task 3 — Adapter registry RED/GREEN

- [x] Director 전용 adapter descriptor/interface/token을 추가한다.
- [x] explicit id, claim, availability와 automatic resolution을 검증한다.
- [x] production adapter는 빈 배열로 등록한다.
- [x] 기존 generic VideoRenderProvider를 자동 포함하지 않는다.

## Task 4 — Job reference와 retention RED/GREEN

- [x] bundle/adapter에서 opaque durable job reference를 만든다.
- [x] path/URL/raw recipe/provider payload가 reference에 없음을 검증한다.
- [x] retry가 같은 stage/recipe reference를 재사용할 수 있게 한다.
- [x] JobsService status를 active-job/retry-source/completed-source로 매핑한다.
- [x] cleanup duration이나 삭제 worker는 추가하지 않는다.

## Task 5 — 회귀와 문서

- [x] Nest Director 전체 테스트와 build를 실행한다.
- [x] 기존 renderer registry boundary와 generic renderer 회귀를 실행한다.
- [x] 기존 shortform 경로 working-tree 변경 0을 확인한다.
- [x] whitespace와 secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] API/Angular render control, operation charge, renderer/provider 실행을 추가하지 않는다.
- [x] server/Electron/migration/DB/runner/commit/push/deploy를 실행하지 않는다.
