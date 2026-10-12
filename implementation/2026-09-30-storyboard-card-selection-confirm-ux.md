# W07 — 프로필 선택 카드·삭제 확인 모달 후속 (2026-09-30)

작업 소스: `/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_angular` (`feat/storyboard-followups-20260929`, 미커밋). 기존 격리 worktree에서 이어 작업했고 원본 dev·실행 중 Web API·기존 테스트 앱은 교체하지 않았다.

## 변경

- 프로필 추천의 아이콘을 목록 헤더와 빈 화면 모두 `auto_awesome`→Material Symbols `lightbulb`로 변경.
- 삭제 모드의 카드 전체를 클릭하거나 Enter/Space를 누르면 카드 왼쪽 체크박스와 같은 선택을 토글한다. 기존 체크박스는 그대로 유지한다. 선택 카드에는 primary 테두리와 옅은 배경, 키보드 포커스 링과 `aria-pressed`를 적용했다. 만들기/정산 중 등 잠긴 카드는 클릭·키보드 선택이 되지 않는다. 평소 완료 카드 클릭은 기존 결과 보기 동작을 유지한다.
- 프로필 삭제 확인창의 부정 버튼을 ‘그대로 두기’→‘취소’로 변경. 확인/취소의 동작·DELETE API·보존 정책은 바꾸지 않았다.

## 확인 모달과 hover 원인

스토리보드 `profiles-page.component.ts`와 홈 `projects.component.ts`는 둘 다 `ConfirmDialogService` → `ConfirmDialogComponent`를 사용한다. 홈 삭제 확인은 `cancelLabel`을 지정하지 않아 공통 기본값 ‘취소’를 보여주고, W07 스토리보드가 ‘그대로 두기’를 직접 넘기고 있었다. 이 문구는 [베리에이션 선택 삭제 설계](/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/specs/2026-09-15-variation-project-delete-design.md)의 보존 강조 표현을 [스토리보드 후속 설계](/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/specs/2026-09-21-storyboard-v2-ui-refinement-design.md)에 가져온 것이다. 공통 부품 자체의 기본 문구는 6/25 처음부터 ‘취소’다.

공통 모달은 부정 버튼에 `matButton`(text), 위험 확인 버튼에 `matButton="tonal"`+`.danger`를 사용한다. [9/7 tonal-surface 규칙 R1-1](/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/specs/2026-09-07-tonal-surface-ui-redesign.md)이 아무것도 변경하지 않는 취소·닫기를 text, 위험한 확인을 danger tonal로 구분했다. `ae3bddae` 커밋이 공통 취소 버튼을 outlined에서 text로 바꾸며 이 근거를 명시했다. 공통 모달 SCSS에 취소 버튼의 hover를 끄는 코드나 별도 hover 선언은 없다. Material text 버튼에는 기본 hover 상태 레이어가 있지만 투명 바탕 위의 옅은 변화라 눈에 덜 띈다. danger tonal은 원래 붉은 면을 가져 변화가 더 잘 보인다. **‘취소에는 hover를 넣지 않는다’는 별도 의도나 문서는 확인되지 않았다.** 이 후속에서는 앱 전체에 영향을 주는 공통 버튼 표현을 바꾸지 않았다.

**9/30 추가 확인:** 열린 직후 취소 버튼에 보이는 배경과 hover 무반응은 단순히 옅은 hover 때문이 아니라 Material 기본 `first-tabbable` 자동 포커스가 취소 버튼에 머물기 때문이었다. 실제 오버레이 테스트로 확인하고 공통 모달 초기 포커스를 대화상자로 변경했다. [재현·수정·새 앱](2026-09-30-storyboard-deleted-profile-and-dialog-focus.md).

## 검증·제한

- TDD RED: 변경 전 집중 테스트 40개 중 5개 실패(아이콘·문구·카드 선택). GREEN: 최종 집중 테스트 **41/41**.
- 최종 전체 Angular ChromeHeadlessNoSandbox **5405/5405, 종료 0**. 첫 전체 재실행은 5405 성공을 출력했으나 프로세스가 종료되지 않아 중단했고, 종료 0으로 처리하지 않았다. 스타일 **6/6**, `git diff --check` 통과.
- macOS arm64 local-api 앱은 Angular/Nest/Electron/uv 단계를 거쳐 패키징했다. electron-builder의 GitHub 다운로드가 오프라인 `ENOTFOUND`라 로컬 설치 Electron으로 `--dir` 패키징했다. 패키지 renderer 86개 파일의 상대 경로·SHA256이 현재 Angular dist와 모두 동일했다.
- 새 앱: `/Users/jina/project/adlight/.worktrees/storyboard-card-select-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 실행 명령: `open "/Users/jina/project/adlight/.worktrees/storyboard-card-select-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"`.
- 이 후속의 새 앱은 컴퓨터 UI 도구의 실행 시간 초과로 직접 화면을 열어 확인하지 못했다. 실제 프로필 삭제·보관함 결과, Web API 원장 실행 서버 반영, 실공급자 속도 개선은 기존 W07 미완료 상태다.
- 로그: `output/storyboard/2026-09-30/storyboard-card-select-red.log`, `storyboard-card-select-final-focused.log`, `storyboard-card-select-final-full-retry.log`, `storyboard-card-select-styles.log`, `storyboard-card-select-native-build.log`, `storyboard-card-select-local-builder.log`.
