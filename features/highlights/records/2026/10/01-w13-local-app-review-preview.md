# W13 같은 영상의 실제 앱 화면 확인

2026-10-01 KST. 사용자가 「실제 앱에 반영해서 내가 확인」을 요청했다. W13 격리 worktree의 Angular/Nest 앱을 로컬 포트 4201/9021에서 실행하고, 9/29 기존 완료 프로젝트의 **별도 복사본**을 연결했다. Chrome의 `http://localhost:4201/#/projects/1790659628130`에서 결과 화면을 열었다. 기존 설치본 데이터와 W14의 4200/9019 서버는 그대로 뒀다.

## 화면에 담긴 자료와 의미

- `runtime-preview/projects`에는 기존 완료 프로젝트의 출력물 19개 메인 MP4·1개 그룹 MP4와 카탈로그 복사본이 있다. 제목은 `W13 확인용 복사본 · 기존 안무 결과 · NewJeans`이다. 원본 영상도 격리 경로로 복사했다.
- 복사본의 `json/dance_review_candidates.json`에 9/29 원래 `dance_highlight.log` 334–335행의 그룹 중첩 탈락 후보 **20.487–30.030초, 30.030–34.835초**를 기록했다. 이는 당시 로그의 backfill이며 새 분석에서 생성한 sidecar가 아니다. 두 후보 모두 `group_0000`과 겹친다. 원래 로그에 보이지 않는 얼굴 탈락 후보는 추가하지 않았다.
- [복사본 manifest](/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/runtime-preview/preview-manifest.json)에 입력 SHA, 완료 meta SHA, 로그 SHA와 출처를 기록했다. 입력 SHA-256은 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`; 완료 `dance_meta.json` SHA-256은 `274eddd3f4a7777987d29a34517abf39c4af344c65155efc6209e5ea03110450`이다.
- 기존 클립/인물/숏폼 열에 **원본 장면 검토 2건**을 더 표시하는 읽기 전용 화면이다. 새 MP4·멤버 배정·정확도 향상을 뜻하지 않는다. 저장 MoveNet 관측은 기존보다 메인 후보 coverage가 훨씬 낮아 제품 기본 모델에 적용하지 않았다.

## 실행·검증

1. `CLIPPER_DATA_DIR=<runtime-preview> NEST_PORT=9021 npm run start:local`로 W13 Nest를 실행했다. 상세 API `GET /v1/projects/1790659628130/detail`은 200, `reviewScenes` 2개, `reviewTimelineClips` 20개, 기존 `clips` 19개, `persons` 5개, `reviewSourcePath`를 반환했다.
2. W13 Angular local 빌드를 4201에서 실행했다. 공유 web API 3000은 개발 로그인을 허용하지 않으므로, 격리 복사본의 `preview-auth.py`를 127.0.0.1:3001에서 **화면 로그인 전용**으로 실행했다. 이 fixture는 DB·외부 계정에 접근하지 않는다. Angular `environment.local.ts`만 9021/3001을 가리키고 `w13PreviewReadOnly`가 결제 복구 호출과 401 세션 무효화를 막는다. 패키지용 환경에는 이 flag가 없고, 이 인증 fixture를 실제 사용자 인증으로 간주하지 않는다.
3. Chrome에서 프로젝트 카드 → 결과 보기를 열어 `원본 장면 검토 2개`, 두 시간 버튼, 기존 5명/19클립, 타임라인, 원본 player를 확인했다. 원본 player `duration=133.654059`, `videoWidth=1920`, `readyState=4`, `error=null`; 첫 버튼 뒤 `currentTime=20.487`, 두 번째 버튼 뒤 `30.03`을 확인했다. clip 썸네일도 화면에 표시됐다.
4. 실제 화면에서 카드의 `pane-card` 공통 스타일이 검토 panel을 세로로 뒤집어 넓은 빈 공간을 만든 것을 발견했다. `.review-panel.pane-card`에 행 방향을 명시한 뒤 같은 화면을 다시 확인했다. Angular 패키지용 `ng build --configuration=packaged`는 종료 코드 0이었다.
5. 확인 당시 4201/9021/3001만 W13이 쓰고, 다른 세션의 4200/9019는 유지됐다. 원본 Dev 프로젝트·meta·원본 영상은 읽기만 했다. 새 ML·얼굴 추론·clip export·모델 다운로드·Build5·commit/push/merge/deploy는 없다.

## 사용자 확인과 남은 일

사용자는 열려 있는 Chrome 탭 또는 `http://localhost:4201/#/projects/1790659628130`에서 `원본 장면 검토`의 두 버튼을 눌러 9/29 결과에서 빠진 메인 후보의 원본 장면을 볼 수 있다. 앱은 로컬 W13 작업본이며 설치된 Dev 앱을 교체한 것은 아니다. 로컬 프로세스가 종료되면 위 세 서버를 다시 실행해야 한다. 기존 clip은 완료 결과지만, 2개 검토 후보는 아직 clip이 아니다. 메인/identity/crop 품질 개선과 최종 MP4의 동일 입력 전후 평가는 다음 범위로 남는다. W14 공통 얼굴 파일은 수정하지 않았다.
