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

## 2026-07-20 실제 영상 생성 확장

사용자 결정으로 manual review보다 end-to-end implementation을 먼저 완료했다. 아래 항목은 원래 foundation의 후속 vertical slice다.

### Task 6 — Job-only executor와 opaque persistence

- [x] public virtual workflow를 대체하지 않는 job-only executor registry를 추가한다.
- [x] JobsService run/cancel만 job-only executor를 해석한다.
- [x] Director reference에 generic output path를 주입하지 않는다.
- [x] Director 완료 job을 generic project history로 중복 materialize하지 않는다.
- [x] exact stage/recipe/checksum/adapter identity mismatch를 실행 전에 거부한다.

### Task 7 — Local Remotion adapter와 output storage

- [x] pinned isolated Remotion worker를 application adapter로 연결한다.
- [x] private recipe/path는 stdin pipe로만 전달한다.
- [x] source-revision composition cache를 재사용한다.
- [x] dynamic width/height/fps/duration composition metadata를 지원한다.
- [x] progress와 AbortSignal/SIGTERM/Remotion cancel을 연결한다.
- [x] ffprobe와 조건부 FFmpeg finalization 뒤 MP4를 원자적으로 materialize한다.
- [x] public artifact에는 opaque id와 검증된 media metadata만 둔다.

### Task 8 — Owner-scoped API

- [x] start/list/get/cancel/retry endpoint를 Director controller에만 추가한다.
- [x] operation DTO에서 raw job params/history/path/auth를 제거한다.
- [x] output id가 owned project operation에 연결된 경우에만 MP4를 stream한다.
- [x] local render에 새 operation credit를 추가하지 않는다.

### Task 9 — Angular actual render UX

- [x] immutable stage 뒤 `MP4 영상 생성` action을 추가한다.
- [x] waiting/starting/running progress를 polling한다.
- [x] active cancel과 failed/cancelled retry를 제공한다.
- [x] completed output metadata와 authenticated blob MP4 저장을 제공한다.
- [x] 기존 `features/shortform/**`와 React dependency를 변경하지 않는다.

### Task 10 — 실제 render와 회귀

- [x] staged PNG+WAV로 실제 H.264/AAC MP4를 생성한다.
- [x] output format/codec/dimension/duration/size/progress를 검증한다.
- [x] Nest Director/Jobs, Angular Director, web API Director 회귀를 실행한다.
- [x] 세 저장소 build를 실행한다.
- [x] session/design/handoff를 현재 구현 상태로 갱신한다.
- [x] server/Electron/provider/DB/migration/commit/push/deploy는 실행하지 않는다.

### Task 11 — 무료 상용 Motion Canvas 기본 adapter

- [x] Remotion worker/adapter/PoC를 삭제하지 않고 그대로 보존한다.
- [x] isolated Motion Canvas worker와 `director.adapter.motion-canvas-local.v1`을 추가한다.
- [x] adapter registry 순서를 `[motionCanvas, remotion]`으로 고정한다.
- [x] 기존 output storage/job-only executor/operation API/Angular UX를 그대로 재사용한다.
- [x] worker cancellation 시 temporary output workspace 폐기를 검증한다.
- [x] 실제 staged PNG+WAV에서 MP4/H.264/AAC를 생성한다.
- [x] Director 103 tests fail 0, actual Motion Canvas integration 1 pass를 확인한다.
- [x] packaged browser/encoder와 OS smoke는 release gate로 분리한다.
