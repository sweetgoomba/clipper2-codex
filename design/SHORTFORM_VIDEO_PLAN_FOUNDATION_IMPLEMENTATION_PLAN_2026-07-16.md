# 숏폼 VideoPlan foundation — 구현 계획

> **상태: superseded / 구현 제거 완료.** 체크 항목은 당시 TDD 수행 이력이며 현재 코드 상태를 뜻하지 않는다. 사용자 결정에 따라 기존 `shortform_prompt`용 변경을 커밋 전에 제거했고, 후속 구현은 `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`로 이동했다.

> 정본 설계: `.codex/design/SHORTFORM_VIDEO_PLAN_FOUNDATION_DESIGN_2026-07-16.md`

**Goal:** 기존 숏폼 렌더 계약을 바꾸지 않고 legacy clip을 `video-plan.v1`으로 backfill/refresh한다.

## Task 1 — adapter 계약을 실패 테스트로 고정

- [x] `test/shortform-legacy-video-plan-adapter.test.js` 추가
- [x] clip 정렬/절대 scene 시간/beat 정규화 검증
- [x] source/search/local/unknown/missing asset routing 검증
- [x] 구현 전 테스트가 module missing으로 실패하는지 확인

## Task 2 — VideoPlan 모델과 순수 adapter 구현

- [x] `shortform-core.model.ts`에 plan/scene/beat/shot/layer/audio 타입 추가
- [x] `LegacyClipVideoPlanAdapter` 구현 및 core index export
- [x] Task 1 테스트 GREEN

## Task 3 — 서비스 read/write 호환 경계 구현

- [x] 구형 project read가 write 없이 plan을 backfill하는 실패 테스트 추가
- [x] write가 최신 clips로 plan을 refresh하는 실패 테스트 추가
- [x] `ShortformProjectService.list/get/upsertProject`에 adapter 적용
- [x] 기존 렌더 경로에 plan 참조가 추가되지 않았는지 diff 검토

## Task 4 — 검증과 finishing

- [x] 관련 node tests 실행
- [x] `npm run build` 및 전체 `node --test` 실행
- [x] git diff/status와 `.codex` main 유지 확인
- [x] 커밋·push 없이 결과 보고

## 검증 메모

- 새 adapter/호환 테스트: 5/5 통과.
- 숏폼 API 테스트(격리 local-auth 설정): 10/10 통과.
- TypeScript build: 통과.
- 전체 suite: 현재 브랜치 534 passed / 31 failed / 565 total.
- 동일 설정 `origin/dev` 기준선: 528 passed / 32 failed / 560 total.
- 새 테스트 5개는 전부 통과했고 새 실패는 없다. 기존 축약 project fixture 1건은 defensive legacy 변환으로 통과 전환됐다.
- 남은 실패는 dev에도 존재하는 constructor fixture drift, media-search paging fixture drift, variation/TTS fixture drift 등으로 이번 범위에서 수정하지 않았다.
- 이후 기존 shortform 비침범 결정을 적용해 위 adapter/model/test 변경을 제거했고, 기존 Nest shortform 경로는 `origin/dev`와 동일함을 다시 확인했다.

## Vira 현재 코드 감사 후 확인

- 실제 Vira `main` 감사 결과는 `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`에 기록했다.
- 현재 활성 `shorts_*` signal과 legacy format/hook/viral pipeline을 분리해야 하지만, Phase 1a adapter/model은 Vira 필드를 가정하지 않아 구현 변경이 없다.
- 다음 구현은 이 브랜치에 임의로 섞지 않고 `PlanningContext`/`vira-evidence.v1` runtime validation을 별도 spec·TDD 범위로 시작한다.
