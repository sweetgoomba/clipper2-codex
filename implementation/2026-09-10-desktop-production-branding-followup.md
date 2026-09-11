# 운영판 Clipper 이름 후속 수정 — 2026-09-10

현재 상태: 격리된 Electron/Angular checkout에서 수정·관련 테스트·빌드·화면 확인 완료. 후속 배포 요청으로 Electron `a34a39d`/Angular `c8b18677` 커밋·push·원격 SHA 대조 완료. 새 Windows 설치 파일은 아직 만들지 않았다. 상세 최신 상태는 [모달·CPU·브랜딩 배포](./2026-09-10-modal-cpu-branding-deployment.md)를 우선한다. 아래 미커밋 표기는 구현 당시 기록이다.

## 사용자 확인과 원인

- 실제 개발 파일: `clipperstudio Setup 0.0.16.exe`. 운영 파일: `clipperstudio Setup 0.0.2.exe`. 사용자 후속 제공으로 이름·버전 확인. Build 번호·소스 스냅샷·파일 SHA 대조는 별도 남음.
- 개발판 종료 안내 없이 운영판 설치, 두 앱 동시 실행, 같은 계정의 양쪽 로그인 유지까지 사용자 확인 완료. 업데이트·제거·플러그인 검증 완료로 확대하지 않는다.
- 작업 표시줄은 개발 `Clipper Studio`/운영 `Clipper`로 구분됐지만 창 제목은 renderer의 고정 HTML 제목에 따라 모두 `Clipper Studio`였다.
- 운영 builder는 productName/appId/protocol을 분리했으나 NSIS artifactName·DMG 이름/제목·설명에는 개발판 이름이 남아 있었다. 로그인 화면과 종료 안내도 별도 하드코딩이었다.

## 수정

- 메인 창의 기본 제목 및 페이지 제목 갱신 방지를 `app.getName()`에 연결. 기존 YouTube 창 제목 유지 함수를 `fixed-window-title.ts`로 추출해 재사용.
- 종료 확인·필수 구성 요소 실패 안내·쿠키 파일 생성자도 실행 앱 이름 사용.
- 운영 builder 파일명은 Windows `Clipper Setup ${version}.${ext}`, Mac `Clipper-${version}-${arch}.${ext}`. DMG 제목/저작권/패키지 설명도 Clipper. 기본 개발 builder 유지.
- Angular의 기존 `/app/info` 조회/타입을 core `AppInfoService`로 추출. 설정 서비스 공개 계약을 보존하고 로그인에서도 재사용하여 로그인/문서 제목 표시. 운영 `Clipper 시작하기`, 개발 `Clipper Studio 시작하기`. 정보 조회 실패가 로그인을 막지 않음.
- 다른 두 안내의 고정 제품명은 `앱`/`데스크톱 앱`으로 정리.
- appId, userData/sessionData, 프로토콜, API 주소, 업데이트 식별자 유지. runner는 확장자로 파일을 수집하고 실제 basename을 보고하며 업데이트/다운로드 API는 저장된 artifact URL을 제공하므로 과거 파일명 접두사에 의존하지 않음을 읽기 전용 확인.

## 브라우저 로그인 안내

- 운영 API의 `/auth/google/callback`이 desktop 로그인 완료 HTML을 직접 반환하고 앱 프로토콜을 연다. 따라서 `api.clipperstudio.ai에서 이 애플리케이션을 열려고 합니다`는 현재 흐름과 맞음.
- `Clipper 열기`는 대상 앱 이름, API 도메인은 요청한 페이지 출처. 브라우저 확인 UI이며 브랜딩 때문에 API/프로토콜을 변경하지 않음.
- 근거: API 배포 checkout의 `src/modules/auth/presentation/auth.controller.ts`, [Chromium external_protocol_dialog.cc](https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/ui/views/external_protocol_dialog.cc).

## 검증

- Electron: 수정 전 창 제목·종료 안내·패키지 브랜딩 실패 재현 후 관련 104개 통과. TypeScript 빌드 및 실제 NSIS 설치/제거 매크로 컴파일 통과.
- Angular: 서비스 추출 후 기존 5개 통과. 로그인 제목/정보 실패 및 문서 제목의 수정 전 실패 확인 후 최종 관련 73개 통과. packaged 빌드 통과.
- 실제 packaged Angular bundle을 임시 로컬 HTTP 서버에서 렌더하여 운영/개발 로그인 제목과 문서 제목 확인. Electron bridge·앱 정보는 로컬 fixture, 플러그인 목록은 빈 배열. 실제 OAuth/DB/플러그인 실행 없이 renderer의 실제 provider/라우트를 확인한 범위. 임시 탭/서버 종료 완료.
- 양쪽 `git diff --check` 통과. 기존 Electron 전체 suite의 sibling 산출물 부재 실패와 구분하며 이번에 전체 suite 성공으로 기록하지 않음. 새 Windows 실기 검증은 새 빌드 후 필요.

## 작업 위치와 다음 단계

- Electron `/private/tmp/clipper-isolation-fix-electron`, 기준 `2d492fee3284263a2207a8a76d11aa035d01d9b0`.
- Angular `/private/tmp/clipper-branding-angular`, 기준 `7ae7366d51a997ee009f73a825467db061daca2b`.
- 원본 Electron/Angular clean, 원본 API8/Admin7/Customer10/Infra2 tracked 및 기존 untracked 보존 확인. `.env` 수정 없음.
- 다음 배포 요청 시 두 저장소의 변경을 커밋·푸시하고 새 릴리즈 스냅샷에 두 SHA를 함께 고정. 게시된 0.0.2 파일을 이름만 바꾸거나 덮어쓰지 않음. 새 Windows 빌드의 다운로드 파일명, 창/종료 안내/로그인 제목과 개발판 공존 확인 필요. 웹3종 재배포·DB migration 불필요.
- 기존 Build 5 전체 QA·플러그인 검증 보류 유지. 남은 PG 환불 및 웹 표시/필터/영수증 확인도 별도 유지.
