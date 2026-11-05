# 웹 API 로컬 로그인 주소 변경 보관 기록

2026-10-29 사용자가 원본 8개 저장소를 최신 원격 `dev`와 동일하게 맞춰 앱을 빌드하도록 요청했다. 원본 `/Users/jina/project/adlight/web/clipper_web_api`의 기존 미커밋 변경을 삭제하지 않고, dev pull 전에 Git stash로 보관했다. 2026-11-02 확인 시 아래 stash가 존재한다.

- 저장소: `/Users/jina/project/adlight/web/clipper_web_api`
- stash 메시지: `before-original-dev-sync-20261029`
- stash 커밋: `c93aff4ea930cd9300f3716297d1ac708744f5ba` (확인 당시 `stash@{0}`; 번호는 바뀔 수 있다)
- 내용: `.env.example`의 `WEB_BASE_URL` 기본값과 `src/modules/auth/presentation/auth.controller.ts`의 동일 설정 폴백을 각각 `http://localhost:4200`에서 `http://localhost:4201`로 변경한다. 실제 `.env` 값이나 비밀정보의 백업은 아니다.
- pull 이후 stash는 다시 적용하지 않았다. 이 stash는 해당 저장소의 **로컬 Git 보관본**이며 원격에 푸시된 백업은 아니다.

## 나중에 확인·복원할 때

먼저 `git -C /Users/jina/project/adlight/web/clipper_web_api stash list`에서 메시지와 커밋을 확인하고, `git -C /Users/jina/project/adlight/web/clipper_web_api diff c93aff4ea930cd9300f3716297d1ac708744f5ba^1 c93aff4ea930cd9300f3716297d1ac708744f5ba -- .env.example src/modules/auth/presentation/auth.controller.ts`로 보관 내용을 살핀다. 적용 전 현재 작업 내용과 최신 코드, 실제 로컬 웹 주소·환경 설정을 비교한다. 현재 설정이 이미 다른 방식으로 구성됐을 수 있고 충돌할 수 있으므로 자동으로 적용하거나 삭제하지 않는다. 10/23의 비슷한 로컬 인증 주소 stash들과는 별도 보관본이다.
