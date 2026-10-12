# W07 — 삭제된 프로필의 결과 액션·공통 확인창 초기 포커스 (2026-09-30)

**현재 동작:** 삭제된 원본의 복제 버튼은 표시·비활성화하고 이유는 툴팁으로만 안내한다. [최신 변경·앱](2026-09-30-storyboard-disabled-duplicate-tooltip.md).

소스: `feat/storyboard-followups-20260929`의 Angular 격리 worktree, 미커밋. 원본 dev·기존 앱·실행 Web API·실데이터는 건드리지 않았다.

## 현상과 원인

사용자가 ‘냉장고 속 재료로 한 끼’ 프로필을 실제 삭제한 뒤, 해당 스토리보드가 홈에 남고 결과 페이지가 열리는 것까지 확인했다. 결과 페이지는 생성 당시의 `profileSnapshot`으로 프로필 카드를 그리므로 삭제 뒤에도 카드·결과가 보인다. 그러나 ‘이 프로필로 또 만들기’는 그 스냅샷을 복제하는 버튼이 아니라 `/shortform/director/profiles?duplicate=<profileId>`로 이동시킨다. 목록 페이지는 현존 프로필 목록에서 ID를 찾지 못하면 쿼리만 지우고 아무 동작도 하지 않아, 사용자가 보고한 빈 이동이 발생했다.

공통 `ConfirmDialogService`는 Angular Material `MatDialog`의 기본 초기 포커스(`first-tabbable`)를 사용했다. 실제 오버레이 테스트에서 창을 열자 첫 번째 tab 대상인 text형 취소 버튼에 `cdk-program-focused`가 붙고 `document.activeElement`가 취소 버튼임을 재현했다. Material text 버튼은 focus와 hover가 같은 상태 레이어를 사용해, 자동 포커스 배경이 열린 직후 보이고 그 위에 hover해도 변화가 없게 보였다. 모달 내부 클릭으로 포커스가 빠지면 일반 hover가 다시 눈에 띈다. 이전의 ‘hover가 원래 옅다’는 설명은 이 초기 포커스 현상을 놓쳤다.

## 수정

- 결과 화면이 원본 프로필을 조회해 404이면 복제 버튼을 비활성화하고 툴팁으로만 이유를 알린다. 일시적인 조회 오류는 삭제로 단정하지 않는다. 복제 클릭 직전에도 다시 조회해 화면을 연 뒤 삭제된 경우의 빈 이동을 막는다. 모두 실패한 배치의 재생성 버튼도 원본 프로필이 없으면 비활성화한다. 결과 스냅샷·스토리보드/파일은 변경하지 않았다.
- 공통 확인창의 `MatDialog` 옵션을 `autoFocus: 'dialog'`로 바꿔 첫 버튼이 아닌 대화상자 컨테이너에 초기 포커스를 둔다. Tab 이동·Esc·취소/삭제의 결과 계약과 text/tonal 버튼 스타일은 그대로다. 홈 삭제창과 스토리보드 삭제창에 함께 적용된다.

## 검증·영향

- 삭제 프로필 복제의 TDD RED 2건/27, 초점 RED 1건/7, 모두 실패한 배치 재생성 RED 1건/28을 확인한 뒤 수정했다.
- 관련 결과/시나리오/공통 모달 **52/52**, 전체 Angular ChromeHeadlessNoSandbox **5409/5409 종료0**, 스타일 **6/6**, `git diff --check` 통과.
- macOS arm64 `npm run build:app:mac:arm64:local-api` 종료0. 패키지 renderer 86개 파일 전부 Angular packaged 산출물과 SHA256 일치, `packaged-runtime-config.json`은 `http://127.0.0.1:3000`. 새 앱: `/Users/jina/project/adlight/.worktrees/storyboard-deleted-profile-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`.
- 사용자가 실제 프로필 삭제·홈 결과 보존·열기까지 확인했다. 이번 새 앱의 삭제 프로필 버튼 상태와 모달 포커스를 사용자가 아직 실기 확인한 것은 아니다. 삭제 기능 전체 완료 판정은 보류한다. 원장 실행 Web API 반영, 실제 생성 시간 단축·실공급자 비교도 여전히 미완료다.
- 공통 `src/shared/ui/confirm-dialog/confirm-dialog.service.ts` 변경은 홈을 포함한 앱 전체 확인창에 적용되므로 W10 공통 UI 작업과 겹치는 경로다. 스토리보드 결과 화면·테스트는 W07 소유. 새 앱 빌드 미러는 기존 테스트 앱을 덮지 않는다.
- 로그: `output/storyboard/2026-09-30/deleted-profile-red.log`, `deleted-profile-generation-red.log`, `dialog-focus-red.log`, `deleted-profile-dialog-focused.log`, `deleted-profile-dialog-full.log`, `deleted-profile-dialog-app-build.log`.
