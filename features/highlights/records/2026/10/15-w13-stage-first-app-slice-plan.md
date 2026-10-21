# 무대 하이라이트 첫 앱 적용 계획

**목표:** 기존에 만들어진 단독·단체 클립에 역할 뱃지를 달고, 한 장면을 실제 등장한 여러 인물의 목록·ZIP·숏폼에 공유한다.

**설계:** [첫 앱 적용 범위](2026-10-15-w13-stage-first-app-slice-design.md). Nest 상세에서 기존 `dance_meta.lists.main/group`를 읽고 인물 소속 배열을 제공한다. Angular는 배정 대기와 다중 배정을 표시한다. 제품 Python과 W14 공통 얼굴 경로는 수정하지 않는다.

**기준:** Nest `origin/dev` 956b4f80, Angular `origin/dev` 6918b643을 10/15 fetch 후 새 격리 worktree에서 시작했다. 기존 작업 트리와 미커밋 파일을 보존한다.

1. Nest 모델/상세: `ProjectClipItem.stageRole/personIds`와 `ProjectPersonItem.sharedReview`를 추가한다. main 단일과 group 배정 대기/다중 소속을 구성한다. 구형 프로젝트 결과가 그대로 보이는 테스트를 먼저 추가한다.
2. Nest 저장/API: `PUT /projects/:projectId/dance/clip-recipients/:clipId`로 `stageRole`과 `personIds` 전체를 저장하고 이전 상태로 되돌릴 수 있게 한다. 클립·인물 ID, 역할별 인원 조건을 검사한다. 같은 클립의 기존 단일 이동과 우선순위를 명시해 테스트한다.
3. Nest 소비자: 인물별 ZIP과 숏폼 검증은 `personIds`를 사용한다. 전체 ZIP은 같은 파일 경로가 여러 인물 폴더에 들어가도 정상이다. 배정 대기 그룹은 인물별 출력에 넣지 않는다.
4. Angular: 인물 목록의 `배정 대기`, 클립의 `단독 메인/공동 메인/함께 등장` 뱃지, 여러 인물 선택과 저장/되돌리기를 구현한다. 기존 클립 이동·숨김 기능의 UI 동작을 유지한다.
5. 검증/빌드: 각 저장소의 관련 unit 테스트, TypeScript 검사와 앱 빌드를 실행한다. 실제 `a` 단독, `b+c` 공동, `a+b+c` 함께 등장, `d` 미등장을 fixture로 검증한다. 이후 기존 완료 프로젝트에서 결과 목록을 읽어 확인하고, 새 분석·설치형 앱 빌드는 실행 조건을 별도로 기록한다.

**남는 작업:** 72번 자동 판정 3번 오선택 및 일반화, 얼굴 이름 매칭, 자동 다중 인물 식별, 정확한 장면 경계, 실제 새 원본 분석과 설치형 배포. 이 첫 빌드는 자동 정확도 개선으로 보고하지 않는다.
