# AI 숏폼 디렉터 계보 Breadcrumb 설계

## 목표

AI 숏폼 디렉터의 왼쪽 단계 사이드바를 제거하고, 사용자가 실제로 선택한
운영 프로필·조사 주제·영상 후보와 현재 페이지를 상단 breadcrumb로
표시한다. 필수 선택값이 없는 하위 페이지는 inbox 빈 상태를 보여주지 않고
가장 가까운 유효한 이전 단계로 이동한다. 프로젝트 보관함의 Director
작업은 정확한 Director 프로젝트와 최종 렌더를 직접 연다.

## Breadcrumb

- 공통 시작 항목은 `AI 숏폼 디렉터`이며 운영 프로필 목록으로 이동한다.
- 아이디어 찾기: `AI 숏폼 디렉터 > {운영 프로필명} > 아이디어 찾기`
- 영상 후보: `AI 숏폼 디렉터 > {운영 프로필명} > {조사 주제명} > 영상 후보`
- 스토리보드:
  `AI 숏폼 디렉터 > {운영 프로필명} > {조사 주제명} > {영상 후보명} > 스토리보드`
- `아이디어 찾기`와 `영상 후보`는 현재 페이지일 때만 표시한다.
- 이전 항목은 해당 선택 식별자를 유지한 링크이고 현재 항목은 텍스트다.
- 긴 이름은 한 줄에서 말줄임하며 `title` 속성으로 전체 내용을 확인한다.
- 실행 기록과 운영 프로필 페이지도 각각 현재 페이지 breadcrumb를 표시한다.

## 유효하지 않은 단계 처리

라우트가 활성화되기 전에 다음 규칙으로 이동시킨다.

- `ideas`에 `profileId`가 없으면 `profiles`로 이동한다.
- `candidates`에 `profileId`, `researchRunId`, `topicId` 중 하나라도 없으면
  `profileId`가 있을 때 해당 프로필의 `ideas`, 없으면 `profiles`로 이동한다.
- `storyboard`는 완전한 후보 선택
  (`candidateRunId`, `candidateId`, `profileId`) 또는 완전한 보관함 선택
  (`projectId`, `storyboardRevisionId`, `finalRenderId`) 중 하나가 필요하다.
- 스토리보드 후보 선택이 불완전하지만
  `profileId`, `researchRunId`, `topicId`가 있으면 해당 `candidates`로,
  `profileId`만 있으면 `ideas`로, 모두 없으면 `profiles`로 이동한다.
- 위 규칙으로 컴포넌트 자체가 활성화되지 않으므로 선택 누락 inbox 화면은
  렌더링되지 않는다.

실제 데이터가 0개인 상태(운영 프로필이 하나도 없음, 생성된 영상 후보가
아직 없음)는 정상적인 데이터 상태이므로 기존 안내를 유지한다.

## 프로젝트 보관함 딥링크

현재 작업 메타데이터의 `origin_storyboard_revision_id`는 후보 제작 실행 ID가
아니라 `videoPlan.id`다. 기존 구현은 이를 실행 ID로 조회해 실패했다.

보관함에서는 다음 값을 전달한다.

- `origin_director_project_id` → `projectId`
- `origin_storyboard_revision_id` → `storyboardRevisionId`
- `origin_render_revision_id` → `finalRenderId`

스토리보드 페이지는 프로젝트 ID로 Director 프로젝트를 직접 조회하고,
프로젝트의 `videoPlan.id`가 전달된 revision과 같은지 검증한다. 프로젝트를
표시한 뒤 정확한 최종 렌더를 선택하고 `3. 최종 영상 만들기`로 스크롤한다.

## 오류 처리

- 유효한 보관함 식별자로 프로젝트 조회가 실패하면 기존 오류 배너와
  다시 시도를 사용한다. 선택 누락 inbox로 변환하지 않는다.
- 프로젝트 ID 또는 storyboard revision이 응답과 다르면 계보 불일치
  오류로 처리한다.
- 보관함에서 연 프로젝트는 후보 계보가 없어도 기존 스토리보드·영상·렌더
  확인 기능을 제공한다. 새 스토리보드 생성 버튼은 완전한 후보 선택이 있을
  때만 표시한다.

## 검증

- Director 셸에는 사이드바가 없고 breadcrumb를 포함한 페이지가 표시된다.
- 각 페이지 breadcrumb가 실제 프로필·주제·후보 이름과 보존된 링크를
  표시한다.
- 불완전한 하위 URL은 inbox를 렌더링하지 않고 예상한 이전 단계로 이동한다.
- 보관함 상세 URL은 `projectId`를 사용해 프로젝트와 정확한 렌더를 열고
  최종 영상 영역으로 스크롤한다.
- 관련 Angular 테스트와 전체 Angular 테스트를 통과시킨다.
