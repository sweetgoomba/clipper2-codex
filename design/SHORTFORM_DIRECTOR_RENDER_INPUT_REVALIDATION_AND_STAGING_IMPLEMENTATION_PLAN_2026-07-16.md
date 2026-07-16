# AI 숏폼 디렉터 — Render input 재검증과 immutable staging 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`

## Task 1 — Bind snapshot RED/GREEN

- [x] binding 시 선택한 로컬 artifact의 kind/media type/size/checksum snapshot을 저장한다.
- [x] candidate API에는 path/checksum을 추가하지 않는다.
- [x] AssetPack rebuild/hydration이 optional snapshot을 보존한다.
- [x] 기존 snapshot 없는 AssetRef를 계속 읽는다.

## Task 2 — Staging domain/storage RED

- [x] stage identity가 project/recipe/input checksum에 결정적으로 묶이는지 검증한다.
- [x] visual/narration input summary와 verification mode를 검증한다.
- [x] 임시 directory 복사 뒤 staged file checksum을 다시 검증한다.
- [x] 같은 snapshot 재요청이 기존 stage를 재사용하는지 검증한다.
- [x] partial failure가 ready stage를 남기지 않는지 검증한다.

## Task 3 — Application/API RED/GREEN

- [x] current project를 다시 compile한 뒤 sourceAssetIds와 narration track을 exact set으로 stage한다.
- [x] source ProjectManifest owner/artifact/access/media kind를 재검증한다.
- [x] bound snapshot 또는 manifest metadata와 actual file을 비교한다.
- [x] narration pack과 actual WAV size/checksum을 비교한다.
- [x] POST owner-scoped endpoint를 추가하고 path/URL/provider 정보를 응답하지 않는다.
- [x] project upsert, operation charge, renderer/provider 호출을 추가하지 않는다.

## Task 4 — Angular RED/GREEN

- [x] Director service에 encoded staging POST를 추가한다.
- [x] compiled recipe가 있을 때만 staging action을 활성화한다.
- [x] visual/narration/byte summary와 renderer 미실행 안내를 표시한다.
- [x] project mutation 뒤 recipe/stage preview를 함께 무효화한다.
- [x] render/provider/queue control과 operation confirmation을 추가하지 않는다.

## Task 5 — 회귀와 문서

- [x] Nest Director 전체 테스트와 build를 실행한다.
- [x] Angular Director 전체 테스트와 production build를 실행한다.
- [x] 기존 shortform 경로 working-tree 변경 0을 확인한다.
- [x] whitespace, raw color, path/URL response, secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] renderer/provider/server/Electron/migration/DB/runner/commit/push/deploy를 실행하지 않는다.
