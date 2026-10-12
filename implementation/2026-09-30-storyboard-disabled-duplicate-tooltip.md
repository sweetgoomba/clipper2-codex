# W07 — 삭제된 프로필의 복제 버튼·툴팁 (2026-09-30)

사용자 피드백에 따라 직전의 ‘원본 삭제 시 복제 버튼 숨김’ 결정을 바꿨다. 결과 화면은 저장된 스냅샷으로 계속 읽을 수 있고, 원본 프로필이 없으면 상단 ‘이 프로필로 또 만들기’ 버튼을 **표시한 채 비활성화**한다. 마우스오버 또는 키보드 포커스에서 ‘프로필이 삭제되어 복제할 수 없어요.’라는 Material 툴팁을 띄운다. 원본 상태를 확인하는 동안이나 조회 오류 때도 버튼은 보이지만 비활성화하고 상태별 툴팁을 제공한다. 원본 프로필이 있으면 종전처럼 클릭해 복제 흐름으로 들어간다. 클릭 직전 재조회와 삭제된 프로필의 빈 이동 방지는 유지했다. 추가 안내 블록은 제거하고 저장된 스토리보드 열람은 유지했다.

Material disabled 버튼은 포인터/포커스 이벤트를 받지 않으므로 툴팁을 감싼 `span`에 붙이고 비활성 상태에서는 감싼 요소를 Tab으로 선택할 수 있게 했다. 실제 버튼은 `[disabled]`로 비활성화했다. 공통 `ConfirmDialogService`의 `autoFocus: 'dialog'` 수정은 직전 후속에 있으며 이번 변경에서 건드리지 않았다. 홈 삭제창과 스토리보드 삭제창에 적용되는 공통 모달 수정이라는 점을 확인했다.

TDD: 삭제 시 버튼 숨김을 기대하던 테스트를 버튼 표시/disabled/실제 hover 툴팁으로 변경해 RED를 확인한 뒤 구현. 관련 결과 화면 28/28, 전체 Angular ChromeHeadlessNoSandbox **5409/5409 종료0**, 스타일 **6/6**, `git diff --check` 통과. macOS arm64 `npm run build:app:mac:arm64:local-api` 종료0, renderer 86/86 파일 SHA256 일치, local Web API `http://127.0.0.1:3000` 설정 확인. 최신 앱: `/Users/jina/project/adlight/.worktrees/storyboard-disabled-duplicate-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 이전 앱은 덮지 않았다. 사용자의 이 새 앱 실기 확인은 아직 없다. 원본 dev/실행 Web API/실데이터/정산은 변경하지 않았고 W07 소스는 미커밋이다. 로그: `output/storyboard/2026-09-30/disabled-duplicate-red.log`, `disabled-duplicate-green.log`, `disabled-duplicate-full.log`, `disabled-duplicate-build.log`.


## 최신 문구·화면 정리

사용자가 선택한 툴팁 문구로 교체했다. 삭제된 원본을 설명하던 별도 결과 화면 블록과 조회 오류용 블록, 후자 전용 재확인 메서드를 제거했다. 관련 테스트 28/28, 전체 Angular **5409/5409 종료0**, 스타일 **6/6**, `git diff --check` 통과. 새 macOS arm64 local-api 앱 빌드 종료0, renderer 86/86 파일 해시 일치. 앱의 JS에서 제거 대상 문장들이 없고 선택한 툴팁 문구가 포함됨을 확인했다. 최신 앱: `/Users/jina/project/adlight/.worktrees/storyboard-tooltip-only-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 기존 앱은 덮지 않았고 소스는 미커밋. 로그: `output/storyboard/2026-09-30/tooltip-only-red.log`, `tooltip-only-green.log`, `tooltip-only-full.log`, `tooltip-only-build.log`.
