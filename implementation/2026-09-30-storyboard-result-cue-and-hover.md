# W07 완료 카드 결과 안내와 호버 범위 — 2026-09-30

사용자 최신 요청으로 완료 카드에 `결과 보기 →`를 다시 추가했다. 이전 D10 문구의 단순 재적용이 아니라, 완료 개수 아래에 작고 별도 배경이 없는 시각 안내로 배치했다. 클릭 대상은 기존 카드 전체이며 별도 버튼·중첩 링크는 만들지 않았다. 완료 개수와 안내를 액션 칼럼의 세로 중앙에 유지한다. 카드의 접근성 이름은 기존 `프로필명 스토리보드 보기`를 사용한다.

옅은 primary 6% 배경은 `.profile-card--clickable:hover`에만 적용한다. 즉 결과를 열 수 있는 완료 카드만 호버로 물들고, 생성 전·생성 중·선택 모드·상세 카드·pending 카드에는 적용되지 않는다. 삭제 선택 모드의 선택 표시 배경은 별도 상태로 유지한다.

코드: W07 Angular 격리 worktree의 `operating-profile-card.component.html/.scss/.spec.ts` 세 파일만 이번 후속에서 수정했다. 기존 W07의 다른 미커밋 변경과 이전 앱 빌드는 보존했다. `dev` 병합·푸시는 하지 않았다.

검증: 완료 카드 안내 추가 테스트를 수정 전 **RED**(`Expected undefined to contain '결과 보기'`)로 확인하고 수정 후 집중 8/8 **GREEN**. 전체 Angular ChromeHeadless **5410/5410**, 스타일 6/6, packaged Angular build와 `git diff --check` 통과.

**패키징 수정 (사용자 실행 오류 후):** 최초 별도 빌드 폴더의 Electron `node_modules`를 이전 폴더에 대한 심볼릭 링크로 두었다. `electron-builder`가 `fs-extra` 등 전이 의존성의 경로를 찾지 못한다는 경고를 내면서도 종료 0을 반환했고, `app.asar`에는 이전 정상 앱의 `fs-extra` 42개 대신 0개만 들어 있었다. 실제 패키지의 Electron 바이너리로 `electron-updater/out/main.js`를 로드해 사용자가 본 `Cannot find module 'fs-extra'`를 재현했다. **따라서 최초 앱은 실행 불가였으며 아래 앱 경로는 같은 위치에서 재빌드한 수정본이다.**

Electron `node_modules`를 실물 APFS 복사본으로 바꿔 macOS arm64 `build:app:mac:arm64:local-api`를 재실행했다(종료 0, 누락 경고 없음). 새 `app.asar`는 이전 정상 앱과 같은 560개 파일 및 `fs-extra` 42개를 포함한다. 새 앱의 Electron 바이너리에서 `electron-updater`와 `fs-extra` `require()`가 모두 성공했다. renderer 디렉터리와 Angular 산출물은 `diff -qr`로 동일, Nest bundle은 `cmp`로 동일하다. 이후 빌드 절차에는 **Electron `node_modules` 심볼릭 링크를 사용하지 않고**, 패키징 종료 코드 외에 실제 패키지 런타임 의존성 로드 검사를 추가해야 한다.

현재 카드 SCSS와 다크·라이트 토큰을 사용한 **정적 샘플 데이터 미리보기**에서 1440px와 430px 배치를 확인했다: `output/storyboard/2026-09-30/result-cue-style-preview.png`, `result-cue-mobile-preview.png`. 실제 앱의 메인 프로세스는 새 빌드에서 실행 후 유지됐으나 UI 접근성 도구가 시간 초과되어 로그인 후 실데이터 카드 화면은 확인하지 못했다. 이 미리보기는 실제 앱 화면 캡처가 아니다.

새 테스트 앱(기존 앱 산출물 덮지 않음):

```sh
open -n -a "/Users/jina/project/adlight/.worktrees/storyboard-result-cue-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"
```

이 앱에는 아직 `dev`에 병합되지 않은 W07의 다른 변경도 포함된다. Web API 원장 수정은 별도 실행 서버에 반영되지 않았고, 실제 생성·정산 테스트는 하지 않았다.
