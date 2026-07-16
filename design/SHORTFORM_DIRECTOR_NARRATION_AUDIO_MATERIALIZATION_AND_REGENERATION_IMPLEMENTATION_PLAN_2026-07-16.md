# AI 숏폼 디렉터 — 나레이션 오디오 materialization과 재생성 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_NARRATION_AUDIO_MATERIALIZATION_AND_REGENERATION_DESIGN_2026-07-16.md`

## Task 1 — baseline과 audio pack RED

- [x] timing alignment metadata에 compact estimated baseline 기대값을 추가한다.
- [x] aligned plan을 baseline으로 estimated plan에 복원하는 회귀를 추가한다.
- [x] empty/ready narration audio pack 계약과 hydration 회귀를 추가한다.
- [x] 기존 `shortform_prompt`와 독립된 storage root를 검증한다.

## Task 2 — synthesis orchestration RED

- [x] fake Supertonic provider로 cue 순차 합성과 1회 atomic upsert를 검증한다.
- [x] artifact metadata에 path/URL이 없음을 검증한다.
- [x] visual AssetPack 보존을 검증한다.
- [x] voice/speed 재생성이 baseline에서 새 generation을 만드는지 검증한다.
- [x] partial failure가 project를 저장하지 않고 새 파일을 정리하는지 검증한다.
- [x] invalid provider result와 owner/artifact file access 거부를 검증한다.

## Task 3 — Nest implementation

- [x] `narration-audio-pack.v1` model과 pure lifecycle helper를 추가한다.
- [x] director 전용 local narration audio storage를 추가한다.
- [x] Supertonic preset/synthesis/resolve application service를 추가한다.
- [x] DTO와 narration controller를 추가한다.
- [x] `TtsSynthesisModule`을 director module에 연결한다.
- [x] create/strategy/video-plan/repository hydration lifecycle을 연결한다.

## Task 4 — Angular RED와 UI

- [x] director preset/synthesis 전용 API service 테스트를 추가한다.
- [x] project model에 narrationAudio를 추가한다.
- [x] voice/speed 선택과 생성·재생성 component RED를 추가한다.
- [x] operation charge와 render/audio-player control 부재를 검증한다.
- [x] Material token 기반 나레이션 패널을 구현한다.

## Task 5 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] whitespace, raw color, 고신뢰 secret-like pattern을 검사한다.
- [x] session/handoff/상위 설계 문서를 갱신한다.
- [x] 실제 Supertonic, server/Electron, migration, DB, runner, commit/push/deploy를 실행하지 않는다.
