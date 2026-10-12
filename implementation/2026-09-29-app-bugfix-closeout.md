# W10 — dev 반영 및 작업 공간 정리 완료

2026-09-29 KST. 사용자 요청으로 커밋 → 작업 브랜치 푸시 → dev 병합/푸시 → 관련 worktree 정리. 배포/새 native 앱 빌드는 하지 않았다.

| 저장소 | 작업 브랜치 커밋 | dev 병합 커밋 | 원격 확인 |
|---|---|---|---|
| clipper_angular | 48155221501822d9ac594e16e0735e8d280f2e87 | 3850ece85cad8f59a07e87a2af34af3e9b8333ee | dev/작업 브랜치 ls-remote SHA 일치 |
| clipper_electron | 776fd282d23fcf1dfe41a3d2c4e904ee1f3ef040 | 9d5ea55daf5641921912ef9085fe63079e45d5de | dev/작업 브랜치 ls-remote SHA 일치 |

두 repo의 원격 `fix/app-bugfix-20260929`는 기록용으로 남겨두었다. 원본 checkout은 dev, tracked/untracked clean, origin/dev와 0/0. 작업 커밋이 origin/dev의 조상인지 확인. 충돌 없는 --no-ff 병합이며 병합 tree는 검증한 작업 tree와 동일하다. Nest 소스/원격 브랜치는 변경 없음.

## 최종 반영 범위

- 최초 설치 동의 취소 후 버튼/카드·재시도 복원(공통 도구/AI 모델 경로).
- 산출물 없는 실패 묶음에 결과 보기 숨김, 기존 부분 결과 접근 유지.
- 숏폼 대본 삭제 후 clip/preview 길이 및 media slots 갱신.
- 스토리보드 짧은 구성에도 대본 N, 시간 비례 너비 유지.
- 안무 버튼 `모든 클립 다운로드`, tooltip `모든 인물의 전체 클립을 인물별 폴더로 묶어 다운로드합니다.`, 기존 프로젝트 삭제 옆 위치.
- 로그 소스 칩 전체/개별/전체 해제 동작 정상화.
- 제거 시 선택 모델 삭제 및 미설치 후 남은 모델 별도 삭제, 고정 대상/링크 경계/실행 직렬화 보호.
- 모델 예상용량과 fresh 실제 파일 상태 구분, 파일 없으면 삭제 UI 숨김. 프로젝트 보존 안내는 작업물 보존/보관함 프로젝트·생성 영상 유지 두 문장. 설치 정보 tooltip/import 제거.

## 검증

커밋 전 feature 및 병합 후 실제 원본 dev에서 전체 Angular 5,404/스타일 6, Electron 991 성공(각 exit0). Electron TS compile 성공. diff check 및 독립 final review blocker 없음. 전체 테스트의 기존 fixture 미디어 404 경고는 있으나 실패 없음.

로그: /private/tmp/w10-closeout-{angular-full,electron-full,style}.log, /private/tmp/w10-dev-merged-{angular-full,electron-full,style}.log. 이전 UI106/native/packaged smoke 성공은 마지막 빌드 기록이며 이번 dev 반영 요청에서는 새 패키징/실행 없음. 사용자 모델 취소 실기 성공; ffmpeg 미설치의 최초 다운로드 필요 취소 실기는 아직 미보고이며 코드/자동검증과 구분한다.

## 정리

- .worktrees/app-bugfix-20260929의 Angular/Electron/Nest worktree 3개를 git worktree remove로 제거(--force 없음). 해당 repo의 로컬 작업 브랜치는 merged -d로 제거.
- Git 없는 Python 빌드 복사본은 기준 47782953228861f4bdbdc135265d067c2a826b0e의 tracked 250파일과 동일함을 검증 후 제거.
- 이 세션의 ignored 설정/의존성/모든 테스트 .app 등 빌드 산출물도 작업 공간과 함께 제거. 사용자 AppData/프로젝트/실제 모델 cache 및 원본 의존성은 보존.
- 유일한 LOCAL-BUILD.md는 [빌드 이력](../records/builds/2026/09/29-app-bugfix-local-build-history.md)으로 보존. 이전 worktree 앱 경로는 더 이상 사용하지 않는다.
- 원본과 다른 worktree 등록 보존을 확인(Angular9/Electron6/Nest9, 원본 및 이전 stale 등록 포함). 글로벌 prune/다른 세션 source 수정 없음.

## 이후 재빌드

```sh
cd /Users/jina/project/adlight/desktop/clipper_electron
nvm use 24.19.0
npm run build:app:mac:arm64:local-api
open "dist-app/mac-arm64/Clipper Studio (dev).app"
```

local-api 앱은 기존 로컬 Web API http://127.0.0.1:3000에 연결한다. 사용자 요청 전 추가 빌드하지 않는다. 다음 소스 수정은 현재 origin/dev에서 필요한 repo만 새 branch/worktree로 준비한다.
