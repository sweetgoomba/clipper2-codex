# AI 숏폼 디렉터 — Supertonic 실측 TTS 타이밍 정렬 구현 계획

작성일: 2026-07-16 KST

정본 설계: `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_DESIGN_2026-07-16.md`

## Task 1 — synthetic acceptance와 RED

- [x] 대표 45초 cue별 Supertonic-shaped measurement fixture를 추가한다.
- [x] 45,000ms → 41,200ms 기대 Scene/Beat/Shot timing을 고정한다.
- [x] id/order/copy/grounding/asset strategy 불변성을 검증한다.
- [x] missing/duplicate/unknown/stale/invalid measurement 실패를 검증한다.
- [x] fallback과 입력 불변성을 검증한다.

## Task 2 — Nest domain contract

- [x] `estimated | tts_aligned` timing basis와 alignment metadata model을 추가한다.
- [x] narration text fingerprint helper를 추가한다.
- [x] exact-set measurement validator를 구현한다.
- [x] Beat/Scene/plan timing reflow를 구현한다.
- [x] weighted Shot allocation과 Layer relative projection을 구현한다.
- [x] all-or-nothing fallback helper를 구현한다.

## Task 3 — lifecycle compatibility

- [x] 기존 estimated project JSON이 그대로 hydrate되는지 확인한다.
- [x] aligned plan이 저장 model에서 손실되지 않는지 확인한다.
- [x] aligned plan으로 AssetPack을 재계산해도 refs/bindings/acquisitions/readiness가 유지되는지 검증한다.
- [x] provider draft validator는 계속 `timingBasis: estimated`만 수용하게 유지한다.

## Task 4 — Angular summary

- [x] Angular VideoPlan model을 timing basis union으로 확장한다.
- [x] VideoPlan summary에 `예상 타이밍 | TTS 실측 정렬`을 표시한다.
- [x] TTS 실행, provider, render control이 생기지 않음을 회귀 검증한다.

## Task 5 — 검증과 문서

- [x] Nest director 전체 테스트와 build를 실행한다.
- [x] Angular director 전체 테스트와 production build를 실행한다.
- [x] 기존 Angular/Nest/web shortform 경로 diff 0을 확인한다.
- [x] whitespace, raw color, 고신뢰 secret-like pattern을 검사한다.
- [x] session/handoff/상위 방향 문서를 갱신한다.
- [x] Supertonic, server/Electron, migration, DB, runner, commit/push/deploy를 실행하지 않는다.

## 구현 결과

- 대표 synthetic measurement 7개로 45,000ms estimated plan을 41,200ms `tts_aligned` plan으로 재배치했다.
- narration text의 `trim + NFC + SHA-256` fingerprint와 WAV artifact id/checksum/provider/speaker metadata를 검증한다.
- 누락, 중복, unknown cue, stale text, unsafe artifact id, 잘못된 checksum, 손상된 duration을 부분 적용 없이 거부한다.
- Scene/Beat/Shot은 contiguous하게 재계산하고 Layer는 Shot 안의 상대 구간을 보존한다.
- 이미 aligned인 plan과 stale alignment metadata를 거부해 누적 rounding drift를 막는다.
- aligned JSON hydration과 AssetPack refs/bindings/acquisitions/readiness 보존 회귀가 통과했다.
- Angular는 `예상 타이밍`과 `TTS 실측 정렬`만 표시하며 실행 control은 추가하지 않았다.
- desktop Nest director 50/50, Angular director 20/20, 두 production build 통과
- 기존 Angular/Nest/web shortform 경로 `origin/dev` 대비 diff 0
- 실제 Supertonic 합성, server/Electron, migration, commit/push 없음
