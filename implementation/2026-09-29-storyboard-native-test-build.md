최신 앱은 [완료 카드 정렬 복구](2026-09-29-storyboard-card-alignment.md)의 `dist-app/card-alignment/mac-arm64/Clipper Studio (dev).app`이다.

# W07 스토리보드 테스트 앱 — 2026-09-29

최신 목적150자·이름50자·카드hover 옅은 배경을 포함한 앱은 [hover 후속 빌드](2026-09-29-storyboard-card-hover.md)의 `dist-app/hover-tint/mac-arm64/Clipper Studio (dev).app`이다. 아래는 해당 변경 전 최초 앱 빌드 기록이다.

최초 W07 Angular/Nest 변경으로 macOS arm64 local-api 앱 빌드 성공(exit0).

```sh
open "/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"
```

같은 dev 앱 identity를 사용하므로 기존 Clipper 앱을 종료한 뒤 실행한다. 앱을 에이전트가 실행하거나 기존 앱을 종료하지는 않았다. Web API는 `http://127.0.0.1:3000`을 사용하며 현재 원본 `web/clipper_web_api`의 기존 프로세스를 보존했다. W07 원장 표시명 Web 소스는 새 worktree에 있으므로 기존 원본 API에 해당 변경이 반영됐다는 의미는 아니다. 서버 재시작/DB 변경/실AI 실행은 하지 않았다.

재빌드:

```sh
cd /Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron
nvm use 24.19.0
NG_BUILD_MAX_WORKERS=2 npm run build:app:mac:arm64:local-api
```

## 빌드 입력·검증

- W07 Angular `797782e8`, Nest `824a7a9f` 기반 미커밋 변경 포함. 다른 W10 세션의 미커밋 변경은 통합하지 않았다.
- Electron fetch origin/dev `0cd7ed7b9444bb00c6372bdcff47a356f5520c35`, 공통 branch `feat/storyboard-followups-20260929` 새 격리 worktree. 제품 소스 변경 없음.
- Python fetch origin/dev `47782953228861f4bdbdc135265d067c2a826b0e`, git archive로 Git 없는 격리 빌드 소스 복사본. .git 파일이 앱에 복사되는 기존 builder 필터 한계를 피했다. 제품 소스 수정 없음.
- Angular/Nest 의존성 symlink 재사용. Electron은 실제 APFS clone copy 디렉터리이며 npm production dependency problems0 확인. 기존 packaged 설정·local public key·uv arm64를 값 출력 없이 복사. 새 의존성 설치/lockfile 변경 없음.
- 전체 Angular packaged build → Nest ncc bundle + 폰트 → Electron TypeScript → uv → electron-builder --dir --publish never 성공. renderer86파일 전체 hash 및 Nest bundle hash가 실제 .app resources와 같음. Python .git 없음, uv/auth/config 존재, local API/자동업데이트 비활성 확인.
- 실제 packaged Electron의 Node 모드에서 electron-updater/fs-extra 로딩 성공. UI 실행/물리 IME/실생성은 사용자의 테스트 대상.
- evidence: `/Users/jina/project/adlight/output/storyboard/2026-09-29/native-build.log`, `packaged-runtime-smoke.log`, `packaged-files.json`.

## 주석 질문의 코드 근거

- 프로필과 결과는 profileId로 연결되지만 배치에는 생성 시점 profileSnapshot이 별도로 저장된다. 결과 화면은 이를 읽어 프로필을 표시한다. Nest693edf6/Angular18006cb0(2026-09-21) 기존 구현이며 민준님 설계 D7이 프로필 삭제 후 보관함 결과 보존을 명시한다.
- 앞서 말한 저장소 복구는 프로필 상세 파일에서 목록 색인을 다시 투영하는 정합성 처리다. Nest repo onModuleInit에서 시작 시 실행, loaded=false/dirty=true일 때 후속 접근에서도 실행. 원래7ed33e77(2026-07-27 23:09:40 KST, Git author metabuzz-jinahan). 이번 삭제 표시/tombstone 대응은 이 세션에서 추가한 미커밋 코드다. 삭제 표시 저장과 index 제거 사이 종료된 경우 다음 시작에 active 목록을 바로잡는다. 사용자 데이터나 스토리보드를 다시 생성하는 처리가 아니다.
- 레거시는 v2 이전의 장면/컷 중심 v1 문서와 settingsV2 없는 기존 프로필이다. 옛 /shortform/director/legacy/:profileId 뷰어는 Angular18006cb0(9/21)에 추가돼 이미 dev에 있었다. 이번에 뷰어/라우트/reader/PDF/legacy count 잠금을 제거했다. 새 호환 뷰어/변환·재생성 계층을 추가하지 않았으며 디스크 원본은 D12에 따라 자동 삭제하지 않았다. 기존 프로필의 필수 설정을 채워 저장하는 기존 폼으로 안내하는 CTA만 추가했다. Git author 표기는 실제 작성 주체(사람/에이전트)를 단독으로 증명하지 않는다.
