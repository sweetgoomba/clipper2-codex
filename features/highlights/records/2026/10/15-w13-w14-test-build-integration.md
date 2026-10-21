# 10/15 W13·W14 안무 시험 빌드 입력 통합

## 소스와 범위

통합 checkout은 `/Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015`이다. 여섯 형제 저장소는 각각 `test/w13-w14-build-20261015` 브랜치다. 현재 HEAD는 Angular `a05b38bd`, Nest `0c3ac31`, Electron `b162592`, Python `e636a5f`, Web API `a306ec4`, Web Admin `aa59c33`이다. 안무 사용성 세션의 완료된 Angular·Nest·Web API 변경을 fast-forward했다. Web API의 마지막 수집 감사 수정 `a306ec4`는 세션의 별도 완료 브랜치에서 가져왔다. 새 커밋·푸시·dev 병합은 하지 않았다. W13 원본 미커밋 변경은 별도 `/Users/jina/project/adlight/.worktrees/w13-stage-shared-clips-20261015/desktop`에 그대로 두었다.

- Python: W14 `clipper_face_core` 0.2.0, Dance 참조 얼굴 매칭 adapter, 사용자가 넣은 로컬 참조 사진 검증과 알 수 없는 인물 표시. W13 Python 72번 노트북 후보는 가져오지 않았다.
- Nest: 사용성 개선의 아티스트 별칭·한글 우선 후보와 중앙 Web API 카탈로그 연결, 참조 사진 검증·캐시, 멤버 QID 유지. 게시 목록에 없는 그룹 직접 입력은 Web API의 이름→QID 조회로 멤버를 찾는다. 기존 선택 기록의 원격 사진을 내려받을 때 Node DNS `all` 모드에 맞는 주소 목록을 반환하도록 보정했다. W13의 저장된 `lists.main`과 `lists.group` 노출, `stageRole`/`personIds` 및 수동 배정 overlay, 여러 인물 ZIP·숏폼 소속 검증도 포함한다. group 원자료의 오래된 단일 `person_id`는 자동 수신자로 삼지 않도록 회귀 테스트로 확인하고 보정했다.
- Angular: 사용성 개선의 한글 우선 아티스트 표시·수동 입력 제안, QID 기반 멤버 선택, 참조 사진 업로드·사전 검증, 이미지 검색 오류 표시·재시도. 선택한 아티스트 이름을 이미지 선택과 준비 완료 단계까지 유지하고, 화면 문구와 사진 버튼 정렬을 보정했다. W13의 역할 배지·배정 대기·복수 인물 선택 및 저장/되돌리기도 포함한다. 새 대화상자는 프로젝트 규칙대로 TS/HTML/SCSS/spec으로 분리했다.
- Electron: W14 공통 core 패키징 연결, W13의 `CLIPPER_LOCAL_API_PORT`와 로컬 Mac arm64 Electron 바이너리 재사용 옵션. 기존 패키징 fixture의 사라진 `dance/data` 기대값을 실제 번들 폰트 자산 검사로 정정했다.
- Web API: 안무 카탈로그 artist 탐지·검색과 group 멤버 조회, 관리자 카탈로그 관리 API, DB migration과 초기 한국 artist 데이터 및 수집 취소 기능을 포함한다. 그룹 수집 출신 국가는 한국으로 한정한다. 이름이 없는 Wikidata 항목은 건너뛰고, 게시 목록 밖 그룹의 직접 입력 이름은 QID로 확인해 명단을 조회한다. 이름→QID 조회의 DB 캐시, 공통 User-Agent 및 외부 서비스 429 응답 처리도 포함한다. 마지막 수집 감사 수정은 Wikidata의 뒤늦게 반환된 QID·`mul` 라벨을 보존하고, 이전 게시 목록의 적격 항목이 누락되면 게시 검증을 실패시키며, 별칭 순서만 다른 차이를 제외한다. `KATSEYE`·`캣츠아이`는 직접 입력 경로의 예시이며 한국 한정 자동 후보에는 포함되지 않는다. Desktop Nest의 카탈로그 호출 대상이다.
- Web Admin: 카탈로그 운영 화면·수집 취소, 실행 중인 그룹 작업의 최근 작업 상태 갱신 및 수집 중 비활성 버튼 표시를 포함한다. `environment.local.ts`의 API 주소는 Web API 기본 포트 `http://localhost:3000`으로 맞췄다.

W13의 Angular `app.config.ts`, `local-api-auth.interceptor.ts`, `environment.local.ts` 미리보기 인증 우회·127.0.0.1:3001 설정은 제외했다. Web API의 현재 `origin/dev`에만 있는 별개 LLM·숏폼 후속 변경은 이 시험 입력에 합치지 않았다. AuraFace/Intel/Seeta, W14 실험용 추가 참조 사진, 시간 이름 전파, 새로운 영상 추론·모델 다운로드·유료 API·배포도 제외했다. 같은 YuNet/SFace 입력에서 실제 정확도 개선은 아직 입증되지 않았다.

## 의존성과 사전 준비

Desktop의 세 Node 저장소 `package-lock.json` SHA-256은 W13·W14·통합 checkout 사이에서 각각 동일하다. 통합 checkout의 `node_modules`는 기존 로컬 설치에서 APFS copy-on-write로 복제해 독립시켰으며 Git 변경에는 포함되지 않는다. Python은 격리 checkout에서 `uv sync --frozen --offline --no-dev --no-editable`로 설치했고 core·Dance·SDK가 모두 site-packages에서 import됨을 확인했다. 모델 파일은 새로 받지 않았다.

패키징 전제 파일인 Nest/Python `.env.packaged`, Electron 로컬 JWT **공개키**와 Mac arm64 `uv`는 기존 로컬 파일을 가리키는 무시된 symlink로 통합 checkout에 준비했다. 파일 내용은 이 기록에 담지 않는다. `assertNoPackagedSecrets`와 런타임 설정 허용 키 검사 통과. Electron `prepare-uv.mjs darwin arm64` 통과. Web API와 Web Admin의 `node_modules`도 원본 로컬 설치에서 독립적으로 복제했다. 통합 Web API의 무시된 `.env`와 `.secrets`는 기존 로컬 파일로 연결했다. 비밀 값은 출력·복사·커밋하지 않았으며, 로컬 `.env`가 관리자 화면 origin `http://localhost:4202`를 허용하는지만 확인했다.

## 실제 검증

| 대상 | 실행 결과 |
|---|---|
| Python Dance+core | 관련 pytest 115/115 통과. `--no-editable --offline` 설치 후 재실행도 115/115 통과. |
| Nest | 참조 사진 DNS 보정 후 `npm run build`, `npm run bundle`, 관련 `node --test` 96/96 통과. 형제 Python 폰트 6개가 번들에 복사됨. |
| Angular | Node 24.19, `NG_BUILD_CACHE_STORE=sqlite`에서 `build:packaged` 통과, 안무 흐름·W13 결과 관련 ChromeHeadless 182/182 통과. |
| Electron | `npm run build`, 로컬 API 설정 39/39, 전체 기본 `npm test` 한 번 1049/1049 통과. 독립 의존성 복제 후 `node --test --test-concurrency=1 "test/*.js" "test/*.mjs"` 1049/1049 통과. |
| Web API | Node 22, 수집 감사·이름 조회 보호 반영 후 `npm run build` 통과. 안무 카탈로그 및 admin migration 관련 Jest 13 suites/76 tests 통과. 초기 artist JSON이 `dist`에 포함됨. |
| Web Admin | Node 24.19, 후속 상태 표시 반영 후 `NG_BUILD_CACHE_STORE=sqlite npm run build -- --configuration local` 통과. 관련 ChromeHeadless 41/41 통과. 로컬 빌드의 API 주소는 `http://localhost:3000`. |

Angular 기본 LMDB 캐시가 native Node abort(134)를 내고, 재사용된 SQLite 캐시가 esbuild `contents` 오류를 냈다. `npx ng cache clean` 후 SQLite 캐시 설정으로 빌드·테스트가 통과했다. ChromeHeadless Karma의 임시 localhost 포트와 Electron 자식 프로세스 종료 시험은 샌드박스 권한 밖에서 실행했다. 최초 Electron 전체 suite의 2실패 중 자식 종료는 권한 문제였고, 패키징 fixture는 현재 Nest 소스에 없는 `dance/data`를 기대한 오래된 검사였다. fixture 정정 후 전체 suite를 다시 통과시켰다.

독립 Node 의존성 복제 뒤 기본 병렬 `npm test` 재실행에서는 자식 프로세스 종료 시험만 간헐적으로 실패해 1048/1049였다. 그 시험 단독 6/6과 전체 직렬 실행 1049/1049은 통과했다. 이는 이번 W13/W14 코드 경로의 실패로 확인되지 않았지만, 기본 병렬 suite가 항상 안정적이라는 주장은 하지 않는다.

앞선 읽기 전용 확인에서 로컬 admin DB에는 카탈로그 생성·수집 취소 migration, 활성 catalog version 1개, group 2,082개, solo 5,386개가 있었다. 이번 후속 통합에서 이름→QID 캐시를 위한 유일한 미적용 admin migration `CacheDanceGroupNameResolutions1792200000000`을 실행하고 테이블·migration 기록을 재확인했다. 카탈로그를 다시 수집하거나 게시하지 않았다. 사용성 세션에서 이전 수집기로 만든 검증 완료 작업 `b7d77ef7-9eeb-4d1a-9c54-64069c7222d7`은 게시하지 않았으며, 새 검증은 해당 누락 수집본의 게시를 거부한다. 새 코드를 실행한 뒤 전체 목록을 다시 수집·검토해야 한다. 한국만 수집하는 새 규칙이 기존 활성 버전의 데이터에 반영됐다고 주장하지 않는다.

**후속 실기 확인:** 사용자가 `npm run build:app:mac:arm64:local-api`로 `.app`을 생성·실행했다. 런타임 설정의 Web API 주소는 `http://127.0.0.1:3000`이고, 로컬 Web API는 로그인 시작 요청에 302로 응답하며 Google callback URI도 `http://localhost:3000/auth/google/callback`이다. 직접 앱의 Google 로그인 버튼을 누른 후 Chrome의 오류 상세에서 `NG04002: Cannot match any routes`를 확인했다. Web API의 `WEB_BASE_URL=http://localhost:4200`은 가입 동의 티켓을 4200으로 보내는데, 현재 4200에는 W13 Desktop Angular 개발 서버가 떠 있다. 가입 동의 라우트는 별도 Web Client에 있고 기본 포트는 4201이다. 즉 이번 화면 오류의 직접 원인은 콜백 대상 프런트엔드가 잘못된 것이다. 앱 로그에 별도로 `Not primary instance — quitting` 기록도 있었으나, 이후 `forwarding to renderer: token=[redacted]` 기록이 있어 URL scheme 충돌을 이번 화면 오류의 단일 원인으로 단정하지 않는다. 현재 Web Client 소스의 로컬 실행은 `ChangeDetectionStrategy.Eager` 컴파일 오류로 실패했다. 아래 명령은 빌드·기동용이며 로그인 성공을 보장하지 않는다. 사용자 영상 재분석·실제 clip 품질/정확도와 Windows 패키징도 미검증이다. 이 결과만으로 배포 가능 또는 얼굴 매칭 개선을 주장하지 않는다.

## 사용자가 직접 실행할 명령

먼저 빌드 터미널에서 Node 24를 고르고 Angular 캐시를 비운다. `nvm use 24`가 이 Mac의 24.19.0을 선택해야 한다. 현재 checkout에는 Node 의존성이 독립 복제돼 있다. 의존성 폴더를 다시 설치해야 한다면 통합 checkout의 Angular/Nest/Electron 각 폴더에서 `npm ci`를 실행한다. 로컬 앱 빌드는 별도 포트 옵션 없이 패키지 앱의 Web API 접속 주소를 기본값 `127.0.0.1:3000`으로 정한다. 앱 내부 Nest 서비스는 별도 포트를 할당받는다.

```bash
cd /Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015/desktop/clipper_angular
source ~/.nvm/nvm.sh
nvm use 24
npx ng cache clean
cd ../clipper_electron
NG_BUILD_CACHE_STORE=sqlite npm run build:app:mac:arm64:local-api
```

Web API는 별도 터미널에서 사용자가 직접 실행한다. 통합 checkout에 연결된 기존 로컬 환경 파일과 DB가 필요하다. 현재 로컬 admin DB에는 이름 조회 캐시 migration까지 적용돼 있다. 새 DB라면 통합 Web API 디렉터리에서 `npm run db:migrate:admin`을 먼저 실행해야 한다. 기존 Web API 서버가 떠 있다면 종료한 뒤 아래 통합 checkout 명령으로 다시 실행해야 새 코드가 적용된다. 연결된 로컬 `.env`는 기본 포트 3000과 `http://localhost:3000/auth/google/callback`을 설정한다. OAuth 공급자에도 이 redirect URI가 등록돼 있어야 새 로그인이 완료된다. 3000 포트가 비어 있어야 한다.

```bash
cd /Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015/web/clipper_web_api
source ~/.nvm/nvm.sh
nvm use 22
npm run start:dev
```

카탈로그 운영 화면을 쓸 경우 별도 터미널에서 통합 Web Admin을 로컬 설정으로 실행한다. Web API가 먼저 떠 있어야 한다.

```bash
cd /Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015/web/clipper_web_admin
source ~/.nvm/nvm.sh
nvm use 24
npx ng cache clean
NG_BUILD_CACHE_STORE=sqlite npm start -- --configuration local
```

빌드가 성공하면 생성될 경로는 `/Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`이다. 미서명 `--dir` 로컬 앱이며 DMG는 만들지 않는다. 사용자가 직접 실행할 때:

```bash
open -n "/Users/jina/project/adlight/.worktrees/w13-w14-build-test-20261015/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"
```

앱에서 동일 영상·동일 참조 사진으로 새 분석을 한 뒤 기존 결과와 클립·이름·보류 상태를 비교해야 W14의 실제 효과를 판정할 수 있다. W13 단체 클립은 자동 등장 인물 판별이 아니므로 사용자가 화면을 보고 수신자를 선택한다.
