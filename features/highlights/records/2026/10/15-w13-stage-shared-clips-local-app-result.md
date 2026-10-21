# W13 무대 하이라이트 공유 클립 첫 로컬 앱 결과 (10/15)

## 사용자 결정과 이번 완료 범위

사용자는 클립을 `단독 메인`·`공동 메인`·단체 장면의 세 종류로 구분하고, 한 장면이 여러 출연자의 결과에 중복해서 나타나도록 요청했다. 단체 장면의 표시 문구는 춤 여부를 가정하지 않는 `함께 등장`으로 정했다. 화면에 나오지 않은 인물을 자동으로 포함하지 않는다. 정확도 실험을 계속 늘리기보다 검증 가능한 첫 앱 범위를 빨리 만들고 남은 한계를 적으라는 지시를 받았다.

10/15 최신 `origin/dev`에서 격리한 Nest/Angular worktree에 다음을 구현했다.

- 기존 Python 결과의 `lists.main`과 이미 export된 `lists.group`를 모두 결과 화면에 노출한다. 예전 앱은 group MP4가 있어도 결과 상세에서 읽지 않았다. group은 우선 `함께 등장 · 배정 대기`에 두므로, 자동으로 모든 멤버에게 잘못 주지 않는다.
- 클립별 역할 배지와 여러 인물 선택 창을 추가했다. `single`은 1명, `joint`는 2명 이상, `together`는 0명 이상의 수신자를 허용한다. 수신자 전체를 한 번에 저장하고 바로 되돌릴 수 있다. 같은 원본 MP4 경로를 여러 인물의 클립 목록에서 참조한다.
- 인물별 ZIP/전체 ZIP의 폴더와 숏폼 선택 검증도 같은 수신자 목록을 사용한다. 공유 배정 후 기존 단일 이동 버튼은 숨겨 두어 두 종류의 저장 기록이 충돌하지 않게 했다. 배정되지 않은 group은 인물별 ZIP·숏폼에 넣지 않는다.
- 클립 숨김/되돌리기와 기존 프로젝트의 main 단일 배정 계약을 유지한다. group에는 사진 대신 그룹 아이콘을 표시한다.

## 실제 로컬 앱 확인

 [격리 앱의 기존 뉴진스 결과 복사본](http://127.0.0.1:4200/#/projects/1790659628130)을 Chrome에서 열어 확인했다. 앱은 수정한 Angular/Nest 코드로 실행 중이며, 프로젝트 목록·해당 120MB 출력 폴더·76MB 원본 영상을 `/private/tmp/w13-stage-preview-20261015`에 COW 복사하고 경로를 그 복사본으로 바꿨다. 저장·삭제 등의 미리보기 조작은 이전 W13 작업본과 설치 앱 데이터에 닿지 않는다. 로그인에는 외부 계정·DB를 쓰지 않는 127.0.0.1:3001 임시 fixture를 사용했다. 이 미리보기 연결을 위한 Angular `environment.local.ts`·`app.config.ts`·`local-api-auth.interceptor.ts` 변경은 **로컬 미리보기 전용**이며 제품 패키지용 환경에는 `w13IsolatedPreview` 설정이 없다.

기존 결과는 main 19개와 group 1개를 실제로 보유한다. 수정 API에서 20개가 노출되고 group은 처음 `personIds=[]`인 배정 대기 1개로 나타났다. 23.357~33.433초 group MP4를 브라우저에서 재생해 화면에 다섯 멤버가 있는 것을 보았고, **격리 복사본에서만** 다섯 인물을 직접 선택했다. 저장 뒤 인물별 클립 수는 다니엘 4→5, 민지 8→9, 하니 3→4, 해린 4→5, 혜인 0→1이며 동일한 group_0000 MP4가 각 목록에 보인다. 앱 새로고침 후에도 유지된다. 다른 API 시험에서는 세 명을 선택했을 때 나머지 두 인물은 소속되지 않았고, DELETE로 배정 대기에 되돌아갔다. 이 확인은 여러 인물 목록/재생/저장 동작의 증거이며 **자동 인물 인식 정확도나 새 영상 분석 성능의 증거는 아니다**.

Nest `npm run build`, 관련 테스트 **73/73**; Angular ChromeHeadless 관련 테스트 **174/174**, `build:packaged` 성공. Nest 독립 worktree 빌드는 Python 형제 폴더가 없어 템플릿 폰트 복사를 건너뛰었으며, 실제 Electron 설치 파일 빌드와 OS별 설치 실행은 아직 하지 않았다. 기존 Python 제품 모델·W14 얼굴 코드·기존 설치 앱/사용자 프로젝트는 수정하지 않았다. 이번 새 ML·모델 다운로드·새 clip export·과금은 0회. 새 커밋/푸시/병합/배포도 없다.

## 남은 결함과 다음 출하선

- 72번 후보는 평가 노트북에만 있다. 15.816초 사람 오선택, 르세라핌의 카메라 이동·줌인 영상에서 판정 보류/분절, 장면 3·4의 연속 구간 결합은 미해결이다. 이번 UI는 현행 YOLOv8s Pose 기반의 자동 메인 선택을 바꾸지 않았다.
- 새로 분석한 무대의 `함께 등장`에 **누가 실제 등장했는지 자동으로 정하지 않는다.** 사용자가 영상을 보고 직접 선택한다. 149.883초 르세라핌 3인 공유 요구는 아직 완성 MP4/인물별 실제 앱 결과로 검증되지 않았다.
- 한 클립씩 수신자를 저장한다. 복수 클립 일괄 적용, edit revision 충돌 방지, 재분석 시 수동 override 이전 정책은 후속 설계/구현 과제다. 실제 OS 설치 앱 패키징·현재 사용자 데이터로의 적용은 별도 통합 단계다.
- 결과 카드의 과거 요약 클립 숫자는 새로 노출한 group을 반영하지 않을 수 있다. 상세 화면의 실제 목록으로 검증한다. 제품 표시 이름 `안무 하이라이트`를 `무대 하이라이트`로 바꾸는 일도 후속이다.
- 모델 사용권·배포 조건이 해결되지 않은 YOLO26s/YOLOv8s를 상용 설치본에 새로 포함한다고 결정하지 않는다. W14 얼굴 이름 매칭은 별도 세션 범위다.

**보고 가능한 내용:** 기존에 파일로 저장돼도 앱에서 빠졌던 단체 장면을 결과에 표시하고, 장면 유형·여러 출연자 소속을 직접 수정해 각 인물 결과/ZIP/숏폼 입력으로 활용하는 첫 로컬 앱 화면을 확인했다. 자동 판정 정확도 개선은 아직 주장할 수 없다.

## 10/15 설치 앱 직접 테스트 준비

기존 3000번 Web API는 다른 작업이 사용 중이므로, 별도 3017번을 지정했다. Electron·Python·Web API의 `origin/dev`를 새 형제 worktree에 배치하고, 기존 Angular·Nest 수정본과 동일한 `desktop` 경로 아래에서 빌드했다. Electron의 `--local-api`에 `CLIPPER_LOCAL_API_PORT=3017` 선택을 추가했다. 기본값 3000은 그대로다. 로컬 빌드는 설치된 Electron 배포본을 이용해 GitHub 재다운로드 없이 패키징한다. Electron 설정 테스트 39/39, Electron TypeScript 검사, Nest bundle, Node 22 Web API 빌드, 패키지용 env 검사 통과. **arm64 미서명 `.app` 빌드는 성공했고, 앱 실행과 로그인·실제 프로젝트 테스트는 아직 하지 않았다.**

Web API 터미널:

```bash
cd /Users/jina/project/adlight/.worktrees/w13-stage-shared-clips-20261015/web/clipper_web_api
source ~/.nvm/nvm.sh
nvm use 22
PORT=3017 GOOGLE_CALLBACK_URL=http://localhost:3017/auth/google/callback npm run start:dev
```

Electron 빌드 터미널:

```bash
cd /Users/jina/project/adlight/.worktrees/w13-stage-shared-clips-20261015/desktop/clipper_electron
source ~/.nvm/nvm.sh
nvm use 24
CLIPPER_LOCAL_API_PORT=3017 npm run build:app:mac:arm64:local-api
open -n "/Users/jina/project/adlight/.worktrees/w13-stage-shared-clips-20261015/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"
```

이 명령은 `--dir` 미서명 로컬 앱을 만든다. 설치용 DMG는 생성하지 않는다. 실제 빌드 결과는 `dist-app/mac-arm64/Clipper Studio (dev).app`(423 MB)이고, 앱 내부 runtime config에서 `http://127.0.0.1:3017`을 확인했다. Google 로그인을 새로 해야 한다면 OAuth 승인 redirect URI에도 `http://localhost:3017/auth/google/callback`이 등록돼 있어야 한다. 기존 제품의 자동 메인 선정 규칙 및 모델은 이번 빌드 준비로 변경되지 않았다.

### 10/15 사용자 실행 오류 수정

사용자가 위 명령으로 격리 Web API를 실행하자 `.secrets/user-jwt-public.pem` ENOENT가 발생했다. 원인은 `.env`가 상대경로로 참조하는 `.secrets` 3개 파일을 worktree 생성 시 옮기지 않은 준비 누락이다. 원본 Web API의 `user-jwt-public.pem`, `user-jwt-private.pem`, `operator-jwt-secret`을 권한을 유지해 격리 worktree에 복사했다. 세 파일의 바이트 일치와 키 파싱을 확인했다. 로컬 DB 접속을 허용한 검증에서 Web API가 3017번으로 부팅했고 `/health`가 `status: ok`, user/release/admin DB 모두 `ok`를 반환했다. 사용자가 직접 터미널에서 실행하겠다고 명확히 했으므로 검증 서버는 즉시 종료했고 3017번 listener가 없는 것을 확인했다.
