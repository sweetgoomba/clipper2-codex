최신 완료 표시 세로 중앙 복구까지 포함한 앱은 [정렬 후속](2026-09-29-storyboard-card-alignment.md)의 card-alignment 경로다. 아래는 직전 hover 빌드 기록이다.

# W07 프로필 카드 hover 배경 — 2026-09-29

사용자가 요청한 “마우스오버 외곽선 대신 거의 투명한 형광초록 배경”을 기존 W07 worktree에 적용하고 macOS 테스트 앱을 빌드했다. 최신 실행 명령:

```sh
open "/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron/dist-app/hover-tint/mac-arm64/Clipper Studio (dev).app"
```

같은 dev identity이므로 기존 앱을 사용자가 종료한 뒤 위 경로를 실행한다. 에이전트는 앱 UI를 실행하거나 기존 앱/서버를 종료하지 않았다. 이전 result-label-reverted 앱에는 이번 hover 변경이 없다.

## 변경

- product source: Angular `src/features/shortform-director/components/operating-profile-card/operating-profile-card.component.scss`의 hover 규칙만 변경.
- 모든 프로필 카드의 hover 배경을 `color-mix(in srgb, var(--primary) 6%, var(--surface-container))`로 지정했다. 기존 primary 토큰을 쓰므로 dark/light accent와 기본 카드 배경을 따른다. 새 색상 상수/전역토큰 없음.
- 기존 `.profile-card--clickable:hover, ...:focus-visible`에서 hover를 분리했다. hover가 border색·추가outline을 바꾸지 않는다. 완료 카드의 기본border는 기존대로이며 키보드focus-visible에는 기존2px outline을 유지한다.
- 마우스가 벗어나면 원래 배경으로 돌아온다. 텍스트/크기/행 정렬/저장/생성/정산에 변경 없음. 이전 결과 보기 문구 제거와 이름·목적50/150 변경을 포함한 현재 소스로 빌드했다.

## 검증·미리보기

- 실제 Chrome fixture: dark/light1440에서 완료 카드와 미생성 카드 모두 hover 배경 변경/복귀, hover outline-style none, border/좌표/크기 동일 PASS. 키보드 focus-visible2px solid 유지. 768/390 가로 넘침 없음, JSerror0. 모든 백엔드 응답은 fixture이며 저장/실AI 요청 없음.
- 첫 검증 조건은 outline-width0px를 기대해 실패했다. Chrome의 기본 computed outline-width는3px이나 outline-style none이면 외곽선을 그리지 않는다. 실제 style과 CSS를 확인하고 검증을 outline-style none으로 수정했으며 제품 코드 추가 수정 없이 PASS했다.
- 스타일 기존6/6, git diff --check PASS. 이번 reversible CSS 변경에 신규 유닛테스트/전체5400회귀 반복은 하지 않았고 실제 브라우저 computed style·이미지로 검증했다.
- Angular packaged build exit0 → 기존 검증된 Nest/Electron 입력을 사용한 electron-builder --dir --publish never exit0. 새 renderer86파일/Nest bundle hash 일치, 실제 package의6% hover규칙/기존 hover outline selector 및 결과 보기 element 부재 확인. package CSS 검증에서는 Angular의 emulated-selector와 NS placeholder를 정규화했다.
- preview: output/storyboard/2026-09-29/hover-tint-{dark,light}-{before,after}.png, hover-tint-light-{768,390}.png. after 이미지의 가운데 카드가 hovered 상태다.
- evidence: hover-tint-browser-results.json, hover-tint-packaged-files.json, hover-tint-{angular,native,browser}.log 및 hover-tint-browser-qa.cjs.

W07 격리 경로만 수정했다. W10 공통폼/UI 및 W11 shell과 주제 경계가 있으나 해당 세션 worktree/원본 source에는 변경 없음. .codex의 W07 행·카드·자체 후속 보고서·세션 기록만 갱신. 미커밋이며 commit/push/merge/deploy/DB/실공급자 성능 측정 없음.
