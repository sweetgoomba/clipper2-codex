# W12 — 사용자 피드백 반영: 얼굴·제목 변경과 인물 MVP

일자: 2026-09-29 KST. 코드·Git·문서 읽기와 인계 문서 수정만 수행했다. 제품 구현·ML·모델 다운로드·유료 API·빌드·fetch·commit은 실행하지 않았다.

[종합 인계](29-pipeline-design-handoff.md) · [새 세션 프롬프트](../../../../../handoff/prompts/2026-09-29-highlight-sessions.md) · [7/1 얼굴 변경 상세](29-face-change-detail.md) · [9/18 제목 변경 상세](29-title-change-detail.md)

## 확정한 사용자 방향

- 인물 결과는 배경 인물을 포함해 찾아낸 모든 인물 그룹을 기본 목록에 표시한다. 결과가 많다는 이유로 자동 숨김·자동 제외·중요도 제한을 하지 않는다. 불확실한 관측도 확인 필요 결과로 보존한다.
- 배경 soft filter, 최소 등장 시간·반복 횟수·얼굴 크기로 카드 표시를 제한하는 정책은 후속으로 미룬다. 검출되지 않은 실제 인물까지 모두 발견한다는 정확도 보장은 아니다.
- 얼굴 공통 도구는 안무·인물에 종속되지 않는 플러그인 공용 모듈을 목표로 한다. 두 기능은 초기 소비자이며 향후 다른 플러그인도 공개된 입력·출력 규칙을 통해 사용할 수 있어야 한다.

## 1. 7/1 얼굴 변경의 근거

별도 [변경 전후·작성자·설계·검증 기록 조사](29-face-change-detail.md)에 커밋과 원본 설계 문서 경로를 기록했다. 구현 교체, 설정 유지, 문서의 평가 계획, 실제 확인 가능한 평가 결과를 구분한다. 모델 교체만으로 정확도가 낮아졌다는 인과관계는 아직 입증하지 않았다.

## 2. 위치 기록은 픽셀 좌표다

앞선 대화의 왼쪽/가운데/오른쪽은 설명용 표현이었다. 현행 [PoseEngine](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pose_engine.py:40)은 `bbox=[x1,y1,x2,y2]`와 관절별 `(x,y)`를 `float32` 좌표로 가져온다. bbox는 OpenCV가 읽은 프레임에서 사람을 둘러싼 사각형의 왼쪽 위·오른쪽 아래 모서리다.

예를 들어 `t=10.0, bbox=[420.5,180.2,780.8,960.1], track_id=7`이라면 10초 시점의 7번 추적 대상 위치를 뜻한다. 이 숫자는 설명용이며 실제 영상 측정값이 아니다. 좌표는 세밀한 모델 추정값이지 위치 정답 보장은 아니다. track ID도 실명이나 영구 인물 ID가 아니다.

[analyze_video_to_records](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py:89)는 기본 4프레임마다 분석하고 `t=frame_index/fps`로 원본 시간을 계산해 메인 bbox와 track ID를 기록한다. 30fps라면 약 0.133초 간격이다. [Segment.bboxes](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/segment.py:180)는 `(time,bbox,track_id)`를 누적한다. 모든 인물의 모든 프레임을 저장하는 경로는 아니다.

최종 [DanceMetaBuilder](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/dance_meta.py:67)는 구간 시작/끝·clip 경로·person ID만 내보내고 이 bbox 시계열을 저장하지 않는다. 추적 crop용 저장안을 구현한다면 프레임 width/height/rotation을 함께 기록하고, 픽셀 좌표 또는 크기로 나눈 정규화 좌표 중 명시한 규칙을 사용해야 한다. 정규화 좌표는 현재 저장 구현이 아니라 제안이다.

## 3. 화면이 따라간다는 표현의 정정

이 표현은 미래의 추적 crop, 즉 잘라낼 창을 대상의 위치에 맞춰 움직이는 기능을 뜻했다. 현재 결과 화면이 인물 카드를 따라 이동하거나 재생 위치가 바뀐다는 뜻이 아니다. 현재 렌더는 기본 중심 crop이며 인물 추적 crop이 구현돼 있다는 설명도 아니다.

예: 원본 가로 영상에 왼쪽 A·오른쪽 B가 함께 있다. 같은 10~20초 clip을 A 카드에서 B 카드로 옮기는 것은 분류를 바꾸는 일이다. B를 중심에 두고 정사각형 영상을 만드는 것은 B의 위치 경로로 잘라내는 별도 작업이다. 현재 재배정은 [사용자 배정 override](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts:200)를 바꾸고, [중심 crop](/Users/jina/project/adlight/desktop/clipper_python/plugins/clipper_video_render/clipper_video_render/filter_graph.py:70)이 B의 위치 경로를 읽는 연결은 없다.

앞선 대화에서 카드 이름 변경과 clip 재배정을 섞어 표현했다. 인물 카드 이름을 바꾸는 행위, clip을 다른 인물 카드로 옮기는 행위, crop 대상 인물을 바꾸는 행위는 각각 구분한다. 향후 한 번의 사용자 조작으로 묶을 수는 있지만 대상 위치 데이터와 렌더 계약을 먼저 구현해야 한다.

## 4. 인물 MVP와 평가안 수정

자동 배경 숨김 제안을 철회했다. 결과는 첫 등장 순 등 단순 정렬로 전부 표시하고, 얼굴이 흐리거나 그룹 판정이 어려운 결과에는 확인 필요 표시를 사용한다. 모델의 검출·임베딩 실패 상태와 UI에서 숨기는 정책을 구분하며, 품질이 낮아 신원을 확정하지 못한 검출을 조용히 버리지 않는다.

첫 평가 제안은 원본 3개×120초 이하를 유지한다. 다중 얼굴 관측 추론은 최대 3회, 같은 관측/임베딩을 재사용해 인물 묶기 기준 하나를 대조하면 최대 6개의 조건 결과다. soft-filter 대조 3회 계획은 제거한다. 등장한 인물 누락, 서로 다른 인물을 하나로 합친 오류, 한 인물이 여러 카드로 나뉜 오류, 대표 사진·수정 시간·중복 export를 평가한다. 배경 인물 카드가 나타나는 것은 오류로 세지 않는다.

## 5. 9/18 제목 변경의 근거

별도 [제목 지시문·보정 전후 조사](29-title-change-detail.md)에 이전·이후 prompt와 detector/repair 실제 동작을 기록했다. raw clip/제목 데이터 분리와 제목 문구 품질 변경은 관련되지만 서로 다른 구현 변화다. 모든 어색한 제목이 자동 수정된다는 보장은 없다.

## 6. 향후 플러그인도 쓰는 얼굴 공통 모듈

목표는 플러그인 공용 얼굴 모듈이다. 공개 API가 안무 Segment나 인물 PersonGroup에 직접 의존하지 않아야 한다. 초기 검증에 안무와 인물을 사용하되, 소비자 등록을 두 이름으로 제한하지 않는다.

공통 후보는 모델 파일 검증·로딩, 다중 얼굴 검출과 좌표/landmark, 얼굴 정렬, 임베딩·거리 비교, 품질 정보와 대표 이미지 후보, 묶기 계산의 독립 함수다. 입력·출력에 시간·좌표 기준·모델 ID/hash·임베딩 차원·실패 상태를 명시한다. 모듈 버전·모델 backend 교체 규칙·선택 의존성을 정하고, 각 플러그인 venv/model 설치·기존 runtime 격리를 유지한다.

각 플러그인은 자기 목적의 판단을 소유한다. 안무의 메인 선정·멤버 참조 매핑, 인물의 장면 관계·결과 표시, 미래 플러그인의 얼굴 검색 등 정책은 공유 기본 도구를 이용해 구성한다. 향후 기능 이름은 활용 예시일 뿐 구현 결정이 아니다.

W14를 초기 공통 모듈 작업 소유 세션으로 둔 것은 수정 충돌을 줄이기 위한 제안이다. 모듈의 기능·이용 대상을 W14나 두 플러그인에 제한하는 소유권이 아니다. 공개 API·패키지 경로·호환성 검증을 먼저 정하고 동일 파일은 한 소유자가 수정한다.

## 검증 범위

사용자 방향은 종합 인계·인물/안무/전체 카드·WORKBOARD·새 세션 프롬프트·날짜 기록에 반영한다. 링크·문서 일관성·제품 저장소 clean 상태를 검증한다. 실제 인물 검출·제목 개선·추적 crop·새 공통 모듈의 실행 검증은 하지 않았다.
