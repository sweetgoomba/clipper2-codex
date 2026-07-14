# YouTube 인증 디버그 도구 설계

- 작성일: 2026-07-13
- 대상 브랜치: `.codex/main`, `clipper_angular/dev`, `clipper_electron/dev`, `clipper_nestjs/dev`
- 대상 런타임: Clipper Studio 개발자 모드, Electron 35.7.0/Node.js 22.16.0
- 비대상: `clipper_web_api`, `clipper_python`, 운영 배포/DB/runner 작업

## 1. 목적

YouTube URL 처리 중 yt-dlp가 로그인 또는 브라우저 쿠키를 요구하는 문제를 앱 안에서 재현하고 비교한다. 개발자는 하이라이트 워크플로를 반복해서 오가지 않고 다음 상태를 한 화면에서 확인할 수 있어야 한다.

- Electron이 관리하는 YouTube 쿠키 파일의 존재 여부와 원문
- Electron 내장 YouTube 세션의 잔존 여부
- NestJS가 실제 운영 경로에서 인식하는 yt-dlp 인증 설정
- 쿠키 없음, 앱 관리 쿠키, 브라우저 쿠키별 메타데이터 및 다운로드 결과
- yt-dlp가 반환한 로그인 필요 여부, 종료 코드, stderr와 실행 시간

이 도구는 문제 관찰과 재현을 위한 개발자 전용 기능이다. 실제 YouTube 인증 흐름 개선은 진단 결과를 확보한 뒤 별도 작업으로 진행한다.

## 2. 현재 동작과 문제

현재 하이라이트 화면은 Angular가 로컬 NestJS의 `/v1/sources/inspect`를 호출하고, NestJS `SourceService`가 yt-dlp로 메타데이터를 가져온다. 작업이 큐에 들어가면 NestJS가 다시 yt-dlp를 실행해 영상을 로컬 캐시에 내려받은 뒤 Python 플러그인에 `video_path`를 전달한다.

로그인 버튼은 Electron의 `persist:youtube-auth` 파티션으로 `BrowserWindow`를 열고, 창을 닫을 때 YouTube/Google 쿠키를 `userData/www.youtube.com_cookies.txt`로 내보낸다. 패키지 실행에서는 이 경로가 NestJS 환경에 주입되지만, 수동 NestJS를 사용하는 devapp에서는 기본적으로 같은 경로가 연결되지 않는다.

현재 구조만으로는 다음 원인을 빠르게 분리하기 어렵다.

1. 쿠키 파일이 없어서 실패했는지
2. 파일은 있지만 NestJS가 다른 경로를 보고 있는지
3. Electron 내장 세션은 남았지만 파일만 삭제된 상태인지
4. 앱 관리 쿠키는 실패하고 시스템 브라우저 쿠키는 성공하는지
5. 메타데이터는 성공하지만 실제 미디어 다운로드만 실패하는지
6. 일반 403을 로그인 필요로 잘못 분류했는지

## 3. 사용자 진입과 화면 구조

설정 페이지에서 빌드 번호를 5회 누르면 기존과 동일하게 개발자 모드가 활성화된다. 사이드바 유틸리티 영역은 다음 순서로 표시한다.

1. `YouTube 디버그`
2. `디버그 로그`
3. 기존 대시보드와 설정 메뉴

`YouTube 디버그`는 기존 `devOnly` 내비게이션 규칙을 사용한다. 페이지 라우트는 `/youtube-debug`이고, Clipper 계정용 `authGuard` 아래에 둔다.

페이지는 `<app-page>`를 사용하며 중첩 카드 대신 구분선으로 나눈 네 영역으로 구성한다.

### 3.1 쿠키 상태

- Electron 관리 쿠키 파일 존재 여부
- 절대 경로
- 파일 크기, 수정 시각, 파싱 가능한 쿠키 수
- Electron 내장 인증 세션의 쿠키 수
- NestJS에 설정된 쿠키 파일 경로와 실제 존재 여부
- NestJS의 `cookies-from-browser`, 자동 브라우저 fallback 설정 여부
- `원문 표시` 토글을 켰을 때만 Netscape 쿠키 원문 표시

쿠키 상태 영역의 제목과 상태 정보 가까이에 `folder_open` 아이콘 버튼을 둔다. 디버그 로그 페이지가 사용하는 Electron `shell.openPath` 계열의 폴더 열기 구현 패턴과 Material 아이콘 버튼을 재사용하되, 페이지 헤더 액션 위치는 그대로 복제하지 않는다. 파일이 있으면 Finder/파일 탐색기에서 해당 파일을 선택하고, 파일이 없으면 생성 예정 디렉터리를 연다.

상태 새로고침은 페이지 헤더에 두지 않는다. 쿠키 파일을 Finder/파일 탐색기에서 직접 수정하거나 삭제한 뒤 다시 읽을 필요가 있으므로 쿠키 상태 영역 안에 작은 `refresh` 아이콘 버튼을 제공한다. 로그인, 삭제, 세션 초기화가 끝난 경우에는 사용자가 누르지 않아도 상태를 자동으로 갱신한다.

### 3.2 쿠키와 세션 제어

- `쿠키 파일 삭제`: yt-dlp가 읽는 Netscape 파일만 삭제
- `내장 세션 초기화`: `persist:youtube-auth` 파티션 저장소를 삭제
- `전체 초기화`: 위 두 작업을 함께 실행

각 삭제 동작은 확인 다이얼로그를 거치고, 완료 후 상태를 즉시 다시 읽는다. 파일만 삭제한 경우 내장 세션이 남아 있음을 화면에서 구분할 수 있어야 한다.

### 3.3 로그인 방식 실행

- `Electron 로그인`: 현재 `BrowserWindow` 기반 로그인을 실행하고 닫힌 뒤 쿠키를 다시 읽는다.
- `외부 브라우저 열기`: OS 기본 브라우저로 YouTube를 연다. 이 동작만으로 앱 쿠키 파일이 만들어지지는 않는다.
- 브라우저 쿠키 진단용 선택 항목: Chrome, Edge, Firefox, Brave, Safari

Google OAuth 토큰은 yt-dlp의 YouTube 쿠키를 대체하지 않으므로 Clipper 계정 로그인 IPC는 재사용하지 않는다.

### 3.4 yt-dlp 진단

기존 하이라이트 `app-source-input` 컴포넌트를 YouTube 전용 모드로 재사용한다. 기본 URL은 다음 값이다.

```text
https://youtu.be/9cS2wv6AfHk?si=alPbLCGjV_2OMD9E
```

진단 종류는 명시적으로 분리한다.

- `메타데이터 확인`: `--dump-json --skip-download --no-playlist` 경로 검사
- `실제 다운로드`: 운영 다운로드 형식으로 미디어 스트림까지 검사

인증 방식은 다음 네 가지다.

- `운영 설정`: 현재 `SourceService`가 사용하는 쿠키 파일/브라우저 설정 그대로
- `쿠키 없음`: 설정된 쿠키가 있어도 인증 인자를 넣지 않음
- `앱 쿠키 파일`: Electron이 반환한 관리 파일을 명시적으로 사용
- `브라우저 쿠키`: 선택한 브라우저의 `--cookies-from-browser` 사용

실제 다운로드 진단은 기존 YouTube 소스 캐시를 사용하지 않는다. 실행별 임시 디렉터리에 강제로 다운로드하고, 파일 존재와 크기를 확인한 뒤 성공·실패와 관계없이 정리한다. 작업 시작 전 확인 다이얼로그로 네트워크와 디스크 사용을 알린다.

## 4. 프로세스별 책임

### 4.1 clipper_angular

- 내비게이션 메타데이터와 `/youtube-debug` 라우트 추가
- `youtube-debug` Angular 컴포넌트 4파일 구성
- 기존 `SourceInputComponent`에 기본 동작을 보존하는 YouTube 전용 표시 옵션 추가
- Electron IPC 상태/제어를 감싸는 `YoutubeAuthService` 확장
- NestJS 진단 API 클라이언트 추가
- 쿠키 원문, 설정 비교, 실행 결과와 에러 표시
- 모든 파괴적 동작과 실제 다운로드에 기존 `ConfirmDialogService` 사용

### 4.2 clipper_electron

기존 `youtubeAuth` IPC 도메인에 다음 계약을 추가한다.

- `getDebugState`
- `openCookiesLocation`
- `deleteCookieFile`
- `clearEmbeddedSession`
- `resetDebugState`
- `openExternalLogin`

`getDebugState`는 파일 상태, 원문, 쿠키 수, 내장 세션 쿠키 수를 반환한다. 쿠키 값은 main 로그에 기록하지 않는다. 쿠키 파일은 POSIX에서 owner-only 권한을 적용하고, 렌더러에는 디버그 화면에서 필요한 상태만 반환한다.

패키지 앱의 yt-dlp JavaScript 런타임은 개발 셸의 `.nvmrc` Node.js가 아니라 Electron 실행 파일을 `ELECTRON_RUN_AS_NODE=1`로 실행해 제공한다. 따라서 패키지 앱은 yt-dlp EJS가 요구하는 Node.js 버전을 포함해야 한다.

- Electron은 `35.7.0`으로 고정하고 내장 Node.js `22.16.0`을 사용한다.
- `process.execPath`를 `CLIPPER_YTDLP_NODE_BIN`으로 local NestJS에 전달한다.
- 관리 venv에는 plain `yt-dlp`가 아니라 `yt-dlp[default]>=2025.12.8`을 설치해 `yt-dlp-ejs`를 포함한다.
- 기존 관리 venv는 `.clipper-ytdlp-ejs-v1` marker가 없으면 다음 패키지 앱 실행 시 한 번 보강한다.
- 패키지 빌드 서버의 `.nvmrc` Node.js와 Electron 내장 Node.js는 서로 다른 런타임이다. 빌드 서버는 `npm ci`로 lockfile의 Electron을 설치한 뒤 패키징해야 한다.

### 4.3 clipper_nestjs

기존 `sources` feature 안에 개발 진단용 presentation/application 계약을 추가한다. 백엔드 import는 상대경로를 유지하고 응답은 raw 객체로 반환한다.

예상 엔드포인트는 다음과 같다.

```text
GET  /v1/sources/diagnostics/youtube/config
POST /v1/sources/diagnostics/youtube/run
```

`run` 요청은 URL, `metadata | download`, 인증 전략과 선택 브라우저를 받는다. 브라우저 이름과 진단 종류는 서버에서 허용 목록으로 검증하며 렌더러가 임의의 yt-dlp 인자를 전달할 수 없게 한다.

진단 결과는 다음 정보를 포함한다.

- `ok`
- 진단 종류와 인증 전략
- 시작/종료 시각과 소요 시간
- yt-dlp 종료 코드
- 로그인 필요 판정
- 성공 시 영상 ID, 제목, 다운로드 파일 크기
- 실패 시 사용자 메시지와 길이가 제한된 stdout/stderr

실제 쿠키 값과 외부 API secret은 응답·로그에 포함하지 않는다. 앱 쿠키 파일 경로는 Electron이 알려준 현재 관리 파일을 진단할 때만 사용하며, 파일명과 존재 여부를 검증한다.

## 5. 오류와 상태 처리

- Electron 브리지가 없는 브라우저 개발 모드에서는 쿠키 상태 영역을 `Electron 앱에서만 사용 가능`로 표시하되 NestJS 진단은 계속 허용한다.
- yt-dlp 실행 파일이 없으면 도구 미준비 상태와 실행 오류를 구분한다.
- 브라우저 프로필을 읽지 못하면 로그인 필요와 별도로 `브라우저 쿠키 읽기 실패`를 표시한다.
- `Sign in to confirm`, `LOGIN_REQUIRED`, 연령 확인 등은 로그인 필요로 표시한다.
- `Join this channel`, `members-only` 같은 회원 전용 오류는 단순 로그인보다 강한 `로그인 + 채널 멤버십 필요` 상태다.
- 일반 403은 원문 stderr와 함께 보여 주되 진단 페이지가 임의로 성공 처리하지 않는다.
- 실행 중에는 동일 진단 버튼을 비활성화한다. 메타데이터와 다운로드 결과는 서로 덮어쓰지 않고 최근 결과를 각각 유지한다.
- 외부 브라우저를 연 뒤에는 사용자가 돌아와 선택 브라우저 쿠키 진단을 직접 실행한다. YouTube 로그인 완료를 OAuth callback처럼 자동 판정하지 않는다.

성공한 메타데이터 JSON에서는 `availability`와 `age_limit`이 접근 제한 판단의 보조 정보다. `availability`는 `public`, `unlisted`, `needs_auth`, `private`, `subscriber_only`, `premium_only` 등을 가질 수 있다. 다만 회원 전용·비공개·anti-bot 상황은 JSON 생성 전에 실패할 수 있으므로 stderr/종료 코드 판정을 함께 유지해야 한다. `Made for Kids`는 공개 범위를 제한하는 인증 상태가 아니며 공개 영상이라면 메타데이터와 다운로드가 인증 없이 성공하는 것이 정상이다.

현재 구현은 `not a bot`, `sign in to confirm`, `login_required`, cookies 안내, 연령 확인 문구를 `authRequired`로 판정한다. `Join this channel`/`members-only` 분류와 성공 JSON의 `availability`/`age_limit` 구조화 표시는 후속 보완 항목이다.

## 6. 보안

쿠키 파일은 Google/YouTube 계정 자격 증명으로 취급한다.

- 원문은 개발자 모드 페이지의 명시적 토글 뒤에서만 렌더링
- 원문을 renderer/main/NestJS 로그에 기록하지 않음
- 클립보드 복사 기능은 이번 범위에 추가하지 않음
- 실제 쿠키 값을 테스트 fixture, 문서, 커밋에 포함하지 않음
- 쿠키 삭제/세션 초기화는 확인 후 실행
- 임시 다운로드 파일은 항상 정리
- 진단 API는 임의 명령, 임의 yt-dlp 옵션, 임의 브라우저 이름을 받지 않음

## 7. 테스트

### 7.1 Angular

- 개발자 모드 전에는 두 디버그 메뉴가 숨고 활성화 후 `YouTube 디버그`가 `디버그 로그`보다 먼저 표시됨
- 기본 URL 렌더링
- Electron 브리지 유무에 따른 상태 표시
- 원문 표시 토글
- 쿠키 상태 영역의 수동 새로고침과 각 변경 동작 후 자동 새로고침
- 파일 삭제, 세션 초기화, 전체 초기화 후 상태 새로고침
- 내장/외부 브라우저 버튼 IPC 호출
- 네 인증 전략별 메타데이터 요청
- 다운로드 확인 다이얼로그와 중복 실행 방지
- 성공/로그인 필요/도구 없음/브라우저 쿠키 오류 결과 표시

### 7.2 Electron

- 파일 없음/있음 상태 조회
- Netscape 쿠키 줄 집계
- 파일 삭제의 ENOENT 멱등 처리
- 전체 초기화가 파일과 파티션 저장소를 모두 제거
- 파일이 있으면 `showItemInFolder`, 없으면 상위 디렉터리 열기
- 쿠키 원문이나 값이 로그로 출력되지 않음

### 7.3 NestJS

- 진단 DTO 허용 목록 검증
- 인증 전략별 yt-dlp 인자 생성
- 메타데이터와 실제 다운로드 인자 분리
- 쿠키 없음 전략이 운영 쿠키 설정을 우회
- 앱 쿠키 파일 검증
- 인증 필요 stderr 판정
- 다운로드 임시 파일 크기 반환과 성공/실패 시 정리
- 기존 `/sources/inspect`, `/sources/ingest`, 작업 준비 경로 회귀 테스트

### 7.4 통합 스모크

다음 조합을 macOS devapp과 Windows packaged 환경에서 확인한다.

1. 전체 초기화 후 쿠키 없음 메타데이터 진단
2. Electron 로그인 후 앱 쿠키 메타데이터 진단
3. 외부 브라우저 로그인 후 해당 브라우저 쿠키 진단
4. 각 인증 전략의 실제 다운로드 진단
5. 쿠키 파일만 삭제한 상태와 내장 세션까지 초기화한 상태 비교
6. Finder/파일 탐색기 파일 위치 열기

## 8. 완료 조건

- 개발자 모드에서만 `YouTube 디버그` 메뉴가 노출되고 `디버그 로그` 바로 위에 위치한다.
- 쿠키 파일과 Electron 세션 상태를 구분하여 조회·삭제할 수 있다.
- Finder/파일 탐색기에서 관리 쿠키 파일 또는 상위 폴더를 열 수 있다.
- 기본 URL로 메타데이터와 실제 다운로드를 독립 실행할 수 있다.
- 네 인증 전략을 동일 URL에 대해 비교할 수 있다.
- 로그인 필요 여부와 yt-dlp 원문 진단 정보가 페이지에 표시된다.
- 쿠키 값이 로그·문서·테스트 fixture에 남지 않는다.
- Angular, Electron, NestJS 관련 빌드와 테스트가 통과한다.

## 9. 2026-07-13 macOS packaged local-api 실측

검증 경로:

```text
clipper_web_api: npm run start:dev
clipper_electron: npm run build:app:mac:arm64:local-api
Clipper Studio packaged app: 개발자 모드 > YouTube 인증 디버그
```

확인 결과:

1. `전체 초기화` 후 기본 공개 URL을 `인증 없음 + 메타데이터 확인`으로 실행해 성공했다.
2. 같은 상태에서 실제 다운로드가 종료 코드 `0`, 약 `3.9초`, 약 `97.6 MB`로 성공했다. 진단 파일은 임시 디렉터리에서 크기를 확인한 뒤 정리된다.
3. 회원 전용 영상 `k_TGyt6E29w`는 `인증 없음 + 메타데이터 확인`에서 종료 코드 `1`과 `Join this channel to get access to members-only content` 오류로 실패했다. 접근 제한 재현에는 성공했지만 현재 `authRequired` 정규식은 이 문구를 별도 회원 전용 상태로 분류하지 않는다.
4. 아동용(`Made for Kids`) 공개 영상은 메타데이터와 실제 다운로드가 모두 성공했다. 이는 인증 제한이 아닌 콘텐츠 분류이므로 기대 동작이다.

아직 확인하지 못한 항목:

- Electron 내장 로그인 후 관리 쿠키 파일 생성과 멤버 권한 계정 성공 경로
- 외부 브라우저 로그인 후 선택 브라우저 쿠키 읽기
- 연령 제한 영상의 로그인/연령 확인 경로
- IP·guest session·요청량에 따라 발생하는 anti-bot 로그인 요구
- macOS 외 Windows packaged app 동일 동작
- 최초 실행/업데이트 시 관리 venv 설치가 오프라인에서 실패할 때 명시적 안내, 앱 진입 차단, 재시도, 불완전 venv 복구가 구현되어 있는지에 대한 별도 감사
