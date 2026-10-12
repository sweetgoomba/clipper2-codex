# W07 완료 카드 세로 중앙 복구 — 2026-09-29

사용자 피드백의 “결과 보기만 삭제하고 완료 개수 표시를 위쪽에 남겼다”를 확인했다. origin/dev 카드 전체 align-items:center를 이번 세션의 설정 컬럼 정렬에서 start로 바꾼 것이 원인이다. 결과 보기 문구를 제거하면서 이 부수 변화까지 복구하지 못했다.

- product 변경: `operating-profile-card.component.scss`의 `.profile-card__actions`에 `align-self:center`를 적용했다. 완료 개수·생성 액션 영역이 데스크톱 카드의 세로 중앙에 놓인다. 설정 요약 컬럼의 정렬과 요청한 hover primary6% 배경은 유지한다.
- 실제 Chrome fixture RED: 완료 라벨 중앙이 카드 중앙보다42.28125px 위였고, 중앙 오차1px미만 검증 실패. GREEN: dark/light1440에서 오차1px미만 PASS. hover/mouseout·추가outline없음·border/레이아웃불변·키보드focus-visible2px·768/390가로넘침없음·JSerror0 모두 PASS.
- 스타일6/6·diff check·packaged Angular/native PASS. renderer86파일/Nest bundle hash 일치, 실제 package align-self:center 및6% hover규칙 존재, 결과 보기 element 부재 확인. 기존 앱/원본/타세션 변경 없음.
- 사용자 레거시 질문은 코드감사와 [철거 정리안](2026-09-29-storyboard-legacy-retirement-plan.md)으로 별도 답했다. 이번 build에는 세로 정렬 복구만 추가했고 레거시 API/전환UI의 추가 철거는 아직 구현하지 않았다.

최신 테스트 앱(기존 앱을 사용자가 종료한 뒤):

```sh
open "/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron/dist-app/card-alignment/mac-arm64/Clipper Studio (dev).app"
```

미리보기/근거: output/storyboard/2026-09-29/card-alignment-{dark,light}-{before,after}.png, card-alignment-light-{768,390}.png, card-alignment-browser-results.json, card-alignment-packaged-files.json, card-alignment-{red,green,angular,native}.log, card-alignment-browser-qa.cjs. 실제 서버저장/AI/DB/과금/물리IME 실행 없음. 미커밋.
