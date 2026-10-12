# W14 인물 하이라이트 개발 앱 시험용 MVP — 2026-10-01 KST

## 사용자 결정과 구현 범위

10/1 사용자가 빠른 시험용 구현을 요청했다. 기존 영상 입력(YouTube URL/로컬 파일)→영상 확인→홈 작업 큐→완료 카드 결과 열기 흐름을 사용한다. 결과는 인물/해당 클립/원본 재생의 3열 한 페이지다. 모든 **검출된 얼굴** 그룹을 Person 1/2…로 표시하고 불확실한 관측은 `확인 필요`로 남긴다. 각 인물 hover ZIP, 각 클립 hover MP4, 상단 전체 ZIP을 제공한다. 체크박스·선택 연결 MP4·숏폼은 없다. 보기 타임라인은 구간 내 seek만, `구간 편집` 뒤 같은 타임라인의 양끝 핸들을 조절한다. 숫자 직접 입력은 결과 화면에서 숨긴다. 이름/그룹 병합/클립 재배정/대표 이미지 후보 변경/제외·복원은 결과에 보존한다.

`clipper_docs/AGENTS.md` §3, Angular Material foundation 정본에 맞춰 `<app-page>`, Material 버튼/폼/메뉴, 기존 타임라인 컴포넌트, 시맨틱 토큰을 사용했다. 신규 Angular SCSS raw hex/rgba 검사 0건. 공용 디자인 언어를 새로 만들지 않았다.

## 격리 경로와 계약

원격 `origin/dev` fetch 후 각 repo 0/0 확인. 작업 브랜치 `feature/person-highlight-mvp-20261001`, 미커밋. 격리 경로: `/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/{clipper_python,clipper_nestjs,clipper_angular,clipper_electron}`. 기준 SHA: Python `47782953228861f4bdbdc135265d067c2a826b0e`, Nest `60a777181c2c9822415f40482c30b6904564a2aa`, Angular `705c49c18c4a9114d1d36cc93de7a653ca1c36fb`, Electron `9d5ea55daf5641921912ef9085fe63079e45d5de`. 원본 Angular의 다른 세션 미커밋 문서 변경은 건드리지 않았다. 커밋/푸시/병합/패키징 없음.

- Python: 독립 `clipper_face_core`(공개 API는 [README](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/clipper_face_core/README.md)), Person 전용 선택 venv, 검증된 기존 YuNet/SFace. 모든 얼굴→shot-local 1:1 track→embedding→동시 출연 cannot-link grouping→interval/대표 후보/MP4와 원본 오디오. 실명·화자 판정 없음.
- Nest: `category=person`, clip의 다중 `personIds`, source scene ID와 경계, person edit overlay, 원본 source ticket, 인물/전체 ZIP에서 정확히 같은 source `[start,end]` 구간만 중복 제거. 편집 경계가 다른 동일 scene은 유지한다. 플러그인 catalog의 설치 게이트와 개발 로컬 호스트의 기존 얼굴 파일/Person 전용 readiness marker 판정을 Electron과 맞췄다.
- Angular: 설치 guard·준비 상태·기존 source input/확인·큐, 완료 결과 3열 및 핸들, 다운로드 액션. 보기 mode native player도 선택 경계 밖 재생을 다시 안쪽으로 돌린다.
- Electron: 플러그인 검색/모델 상태/venv fingerprint. 기존 안무 모델 파일을 읽고 Person marker만 독립 관리; 제거해도 공유 weight는 삭제하지 않는다. SDK 기본 시작 경로에 ML 의존성을 추가하지 않았다.
- 과금/권한: 신규 Web API operation 계약이 없으므로 **운영 `NODE_ENV=production` Person job 시작은 차단**. 개발 앱 시험은 신규 차감 없이 실행한다. 출시 전 가격·취소/환불·재개/보존 정책과 Web API 계약 필요.

## 실제 검증과 한계

| 항목 | 관측 |
| --- | --- |
| Python | 인공 관측/다중 track/동시 출연 5개 테스트 PASS, ruff PASS, `uv sync --frozen --package clipper-plugin-person-highlight --no-dev` PASS. 가짜 detector를 쓴 4초 합성 소스 job 스모크에서 2그룹·1클립·MP4 영상+오디오 확인. **실제 영상 얼굴 추론 아님.** |
| 모델 | Mac dev userData의 YuNet SHA `8f2383e4…2552fa4`, SFace SHA `0ba9fbfa…84087c34`가 기존 안무 코드의 기대값과 일치. OpenCV 4.13.0 backend 생성 PASS. 신규 다운로드 0. |
| Nest | 빌드 PASS, 인물 상세/편집/ZIP/운영 차단/모델 설치 상태 및 기존 billing 선택 테스트 25개 PASS, 설치 게이트/catalog 포함 선택 테스트 16개 PASS(중복 포함). 개발 서버 `/v1/health` 응답 `ok`. |
| Angular | devapp 빌드 PASS, Chrome Headless 타임라인·결과 15개 테스트 PASS, 스타일 test 6개 PASS, 개발 UI HTTP 200. Angular 공유 cache LMDB 문제는 `CI=1 NG_BUILD_CACHE_STORE=sqlite`로 격리. |
| Electron | 빌드 PASS, 모델·venv 관련 23개 테스트 PASS. 개발 앱 창 기동 로그 확인. |

실제 소스 3건의 GT, 정확한 입력 경로/원본 SHA·익명 인물·동시 출연·배경 라벨·자원/시간 상한·출력 위치가 아직 확정되지 않아 **실제 영상 ML 평가 0회**. pairwise/B-cubed, 인물/interval recall, false merge/split, 대표 이미지 수정 시간, 실영상 다운로드/수정 보존 성능값은 없다. Mac/Windows 패키징·Windows 경로·장시간 취소/재개도 미검증이다. 얼굴이 보이지 않거나 검출기가 놓친 사람은 이 face-only MVP에서 그룹으로 나타나지 않는다. shot cut은 단순 프레임 차이, 소스 시각은 OpenCV frame index/FPS 기준이어서 VFR/rotation 보장은 없다. 공통 API의 원본 PTS/landmark/품질 세부 필드와 edit revision/CAS, 별도 export job은 후속 계약이다.

공식 자료 10/1 재확인: [YuNet 모델 문서](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md)는 디렉터리 MIT와 2026may dynamic-shape 재export를 명시하고 정확도 개선은 입증하지 않는다. [SFace 모델 문서](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)는 디렉터리 Apache-2.0과 2021dec weight를 명시한다. [opencv-python 공식 배포 문서](https://github.com/opencv/opencv-python/blob/4.x/README.md)는 Mac/Windows 일반 데스크톱 wheel과 CPU-only를 명시하며 CUDA는 custom build가 필요하다. [InsightFace 공식 모델 규정](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md)은 SDK MIT와 제공 pretrained weight 비상업 연구용 조건을 구분한다. 따라서 이번 시험 범위에서 교체하지 않았다. SFace weight 학습 데이터 권리와 실제 Windows 구동은 배포 전 확인이 남는다.

## 사용자가 지금 시험하는 경로

이 기록 작성 시 개발 서버와 Electron 개발 앱을 격리 worktree에서 띄웠다. 앱의 스토어에서 `인물 하이라이트`가 미설치로 보이면 설치를 눌러 **이미 있는** 얼굴 모델 파일로 readiness marker를 만든다. 영상 파일 또는 YouTube URL → 영상 확인 → `인물 분석 시작` → 홈 큐의 완료 카드 → 결과를 연다. 인물 행과 클립 행에 마우스를 올려 다운로드를 누르고, 클립을 선택해 재생 타임라인 및 `구간 편집` 핸들을 확인한다. 앱 화면 전체를 사람이 끝까지 조작한 판정은 아직 하지 않았다. 사용자가 발견한 구체적 오류를 이 W14 브랜치에서 수정한다.

재시작이 필요하면: Nest worktree에서 `CLIPPER_EXECUTION_MODE=devapp CLIPPER_NESTJS_ENV_FILE=/Users/jina/project/adlight/desktop/clipper_nestjs/.env.devapp CLIPPER_AUTH_JWT_PUBLIC_KEY_PATH=/Users/jina/project/adlight/web/clipper_web_api/.secrets/user-jwt-public.pem CLIPPER_ELECTRON_USER_DATA_DIR='/Users/jina/Library/Application Support/Clipper Studio Dev' CLIPPER_PERSON_FACE_MODEL_DIR='/Users/jina/Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight' CLIPPER_YTDLP_COOKIES='/Users/jina/Library/Application Support/Clipper Studio Dev/www.youtube.com_cookies.txt' node dist/main.js`; Angular worktree에서 Node 24.19, `CI=1 NG_BUILD_CACHE_STORE=sqlite npm run start:devapp`; Electron worktree에서 `CLIPPER_PYTHON_ROOT=/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python CLIPPER_ELECTRON_ENV_FILE=/Users/jina/project/adlight/desktop/clipper_electron/.env.devapp npm run start:devapp`. 원본 repo의 설정/공개키 파일은 읽기만 하며, 앱 사용 기록과 Person readiness marker 등 정상 실행 데이터는 기존 개발용 userData에 저장된다. 다른 세션의 원본 checkout은 건드리지 않는다.

## W13 인계와 다음 결정

[W13 공통 계약 인계](../09/30-w14-to-w13-face-contract-handoff.md)에 실제 API와 제안 대비 누락 필드, 파일 소유권/merge 순서, Dance compatibility gate를 추가했다. W13 상호 확인은 아직 없다. 3건×120초 이하 GT 입력·출력/자원 한계를 먼저 고정한 뒤 실제 face-only 추론 최대3회/동일 관측 grouping 기준 하나 대조 최대6조건을 실행한다. 배경/단역을 숨기는 soft filter 대조는 하지 않는다. 새 모델 다운로드, 외부 유료 API, Build5는 별도 범위다.

## 10/1 15:44 KST 사용자 시험 실패와 수정

사용자가 YouTube ID `0KQDhi7ddrk`를 입력해 source metadata 확인까지 성공했고, `person_1790837044223` 작업은 시작 직후 약 68ms에 실패했다. Nest 로그의 직접 원인은 `Plugin assets are not installed: `이다. 기존 YuNet/SFace 파일은 모두 있었으나 Person 전용 `person_highlight.ready`가 없었다. 개발 API의 `/v1/plugins/person_highlight/status`도 `not_installed, assetsPresent=true`를 반환했다. 이 시점의 실제 영상 추론은 **0회**다.

Angular Person setup은 화면의 낡은 `ready` 상태면 큐 등록 직전 `ensureReady`를 건너뛰었다. 큐 등록 시 `refreshOne('person_highlight')` 뒤 항상 `ensureReady`를 거치고, 완료되지 않으면 작업을 만들지 않도록 수정했다. 공용 ModelDownloadService의 다른 플러그인 `done`/동의 상태가 Person `check`를 막는 조건도 플러그인별로 제한했다. 두 회귀 테스트를 먼저 실패로 확인하고 수정 후 5개 통과; 전체 Angular 5,446개 통과, devapp 빌드 통과. 새 Person 메뉴에 실제 예시 영상 링크가 없는데 모든 메뉴에 링크를 요구하던 기존 navigation 테스트도 의도(링크는 plugin 항목에만)대로 갱신했다.

실제 개발 앱 UI에서 스토어의 Person `미설치` → 기존 파일 2개 `이미 설치됨` → 설치를 진행했다. Electron 모델 로그는 2개 파일 PRESENT, plugin health 200, 모델 로드 및 Person marker 작성 성공을 기록했다. **신규 모델 다운로드 0건**. 이후 스토어 `설치됨`, Nest status `installed`, 개발 API `POST /v1/plugins/person_highlight/start` 201, Python plugin `/health` 200 `status=ok`를 직접 확인했다. 이전 실패 카드는 홈에 남고 상세에 `다시 시도` 버튼이 있다. 사용자 영상의 재시도나 실제 얼굴 추론은 GT/구간/자원 한계가 확정되지 않아 이 세션에서 실행하지 않았다.

## 10/1 16:00 KST YouTube 로그인 반복 안내 원인

사용자는 실패 카드 `다시 시도` 뒤 YouTube 로그인 안내가 반복돼 두 번 로그인했다. Electron 로그는 각각 `authenticated=true`, 쿠키 33/48개 저장 성공을 기록했고, 쿠키 파일은 개발 앱 userData에 0600 권한으로 존재한다. 반면 두 Person retry의 Nest 로그는 `managedCookieAvailable=false`, `strategy=none`인 채 미디어 요청 403(`YOUTUBE_MEDIA_ACCESS_FORBIDDEN`)이었다. 원인은 **수동 실행한 개발 Nest 프로세스에 `CLIPPER_YTDLP_COOKIES` 경로를 전달하지 않은 실행 설정 누락**이다. 패키징 앱에서는 Electron의 `NestManager`가 이 값을 전달하지만 개발 앱은 별도 Nest를 실행한다.

07:01 UTC 개발 Nest를 같은 쿠키 파일 경로와 함께 재시작했다. 읽기 전용 `/v1/sources/diagnostics/youtube/config`는 `cookiesPathExists=true`를 반환했다. 사용자가 선택한 동일 영상 ID의 **메타데이터만** 진단한 결과 `resolvedAuthStrategy=managed_file`, `ok=true`, 10개 format 확인, 약 3.6초였다. 쿠키 내용은 출력·복사하지 않았고 영상 파일 다운로드/실제 얼굴 추론은 실행하지 않았다. 따라서 미디어 다운로드의 최종 성공은 사용자의 다음 재시도 결과를 봐야 한다. 쿠키 경로는 고정되어 있어 같은 개발 서버가 계속 실행되면 재로그인 시에도 파일을 다시 읽는다.

## 10/1 사용자 시험 중 진행 문구 개선

사용자 재시도에서 Nest 로그는 같은 YouTube 영상의 `managed_file` 다운로드 성공을 기록했고, Python Person job의 얼굴 분석이 시작됐다. 사용자 요청으로 기존 `얼굴 관측 중`을 선택한 문구 **`등장 인물 분석 중`**으로 바꿨다. 실제 처리 경계에서 `같은 인물 묶는 중`(관측 cluster), `등장 구간 정리 중`(출력 구간 계산), `대표 얼굴 고르는 중`(대표 crop·후보), `등장 구간 내보내는 중`(클립 렌더)을 순서대로 보고한다. 진행률은 10–60% 분석, 61% 묶기, 64% 구간, 67% 대표 이미지, 70–98% 클립 내보내기, 100% 완료로 단조 증가한다. Nest WebSocket 진행 이벤트와 홈 카드의 기존 message 필드를 그대로 사용한다.

합성 프레임·가짜 얼굴 검출기로 단계별 문구 순서와 진행률 단조 증가를 먼저 실패하는 테스트로 확인한 뒤 수정했다. 공통 그룹 API의 `on_intervals_start` 콜백이 실제 interval 계산 **전**에 발생하는 회귀 테스트도 추가했다. Person 및 공통 얼굴 단위 테스트 **7개 통과**, Python `compileall` 통과. 실제 사용자 작업의 완료 결과·인물 정확도·처리 시간은 아직 확인하지 않았다. 이 작업은 이미 실행 중인 Python 프로세스가 이전 코드를 읽어 시작했으므로 새 문구는 다음 프로세스 시작 이후 작업부터 적용된다. 현재 작업은 중단하지 않는다.

## 10/1 후속 상태 정정

위 단락의 작업 `person_highlight_retry_1790838316793`은 Nest 로그에서 약 658초 뒤 **완료**됐고 사용자가 결과를 확인했다. 따라서 이 문서의 앞선 “실영상 추론 0회”, “실영상 완료 미확인”, “실행 중 작업 보존”은 각각 **해당 시점 기록**이며 현재 상태가 아니다. 사용자는 결과를 불합격으로 판정했다. 실제 artifact 분석, 입력 해상도/원본 SHA, 수정·테스트·남은 품질 문제는 [첫 결과 진단](01-w14-first-result-debug.md)을 기준으로 한다. 새 코드에 대한 실영상 재분석/GT 평가는 아직 없다.
