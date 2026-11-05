# Dialog Source Range Implementation Plan

**Goal:** 대사 하이라이트를 기존 클립 바깥으로 확장·축소하며 가까운 범위를 먼저 보여주는 공통 편집기로 개선한다.
**Architecture:** SourceSceneOverlayComponent/ClipTrimmerComponent 재사용, 기존 상대 trim 저장 계약 유지, 원본에서 편집 파일 재생성.
**Spec:** /Users/jina/project/adlight/.codex/features/dialog-highlight/records/2026/11/2026-11-04-source-range-design.md
**Constraints:** 사용자 명시 요청 없이 커밋/푸시하지 않음. 신규 Markdown은 .codex에만. 원본 manifest 불변. 클립 상대 초 호환. UI 시맨틱 토큰·Material·분리 템플릿. Karma는 하나만 실행. 테스트는 실패 먼저 확인.

## Task 1: Backend source range
- [x] 기존 clip-trim 테스트와 원본 ticket/STT/detail/render 소비 경로 확인.
- [x] 원본 기준 앞뒤 확장/경계/상대 기록/전체 STT/원본 파일 권한 회귀 테스트를 추가하고 실패 확인.
- [x] ClipTrimService의 원본 다운로드 재절단 경로, TrimClipDto 숫자 검증, __source__ 허용 범위, 상세 STT를 구현. 원본이 없을 때 기존 동작 유지.
- [x] 빌드·관련 테스트 및 실제 ffmpeg 통합 검증. 원본 데이터에 영향 없이 기존 백필/렌더와 호환 확인.

## Task 2: Shared viewport and dialog UI
- [x] 공통 원본 편집기에 초기 편집 상태·선택 체크박스 숨김·최소 길이·필드 옵션과 보기 확대/축소를 검증하는 실패 테스트 추가.
- [x] 클립 주변 5초/최소 12초 viewport를 기본으로 하고 단계적 줌과 팬에서 draft를 유지.
- [x] 대사 버튼에서 공통 편집기 사용, 절대 UI 범위와 기존 상대 저장 범위 변환, 원본 없으면 기존 편집기로 fallback. 저장/복원/클립 전환/폴링 중 UI 상태 보존.
- [x] 대사 프로젝트의 sourceVideoUrl와 __source__ 티켓 지원. 기존 인물·안무 테스트 포함.

## Task 3: Integration and review
- [x] 두 레포 변경을 대조하고 전체 테스트·빌드·런타임 스모크.
- [x] 읽기 전용 코드 리뷰, 필요한 보완 및 영향 범위 재검증.
- [x] 완료 내용을 기록하고 변경 파일·검증·한계·미병합 상태 보고.
