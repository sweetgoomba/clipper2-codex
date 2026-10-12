# W13 MoveNet 평가 준비 — 2026-10-01

## 이번에 준비한 것

사용자의 `진행해`는 앞서 제시한 **익명 메인 정답표 검토와 MoveNet metadata 평가 도구 준비** 범위로 적용했다. 기존 W13 Python 격리 worktree `feature/w13-dance-metadata-eval-20261001`에서만 코드를 바꿨다. 제품 기본 `PoseEngine`과 앱 실행 경로는 여전히 YOLO를 사용하며, 자동으로 MoveNet으로 전환하지 않았다. W14 공통 얼굴 파일은 수정하지 않았다.

1. `services/movenet_pose_eval.py`: 이미 로컬에 존재하는 TensorFlow 2 SavedModel만 열 수 있는 함수와 MoveNet MultiPose `[1,6,56]` 출력을 기존 `bbox xyxy`·17×2 관절 형식으로 변환하는 `MoveNetPoseAnalyzer`를 추가했다. 256×256 RGB 입력·비율 유지 패딩을 쓰고, 결과 좌표를 실제 리사이즈 치수 기준으로 원본 화면에 되돌린다. 인물 점수/관절 점수와 6개 slot 중 수락·저점수·잘못된 상자 수를 남긴다. `tensorflow` import는 로컬 모델 로드 시점까지 미룬다. 의존성 설치나 모델 다운로드는 수행하지 않았다.
2. `DancePipeline.analyze_pose_for_evaluation(input_video)`: 기존 `MainSelector`·`TrackAssigner`·`analyze_skip` 경로를 그대로 쓰면서, 분석한 각 프레임의 **모든 인물 bbox·관절·점수**, 선택한 단일 main track/bbox, group 상태, raw main/group 구간을 JSON 직렬화 가능한 dict로 반환한다. 얼굴 분석, 참조 이미지, clip·썸네일·제품 metadata export를 호출하지 않는다. 기존 제품 `run()`의 호출 계약은 유지했다.
3. [익명 메인 검토표](01-w13-anonymous-main-review.json): 전체 0~133.654059초의 19개 연속 구간에 5명의 솔로 후보를 `P1`~`P5`로 연결했다. 이 ID는 무대 영상의 시각적 사람 표식이지 멤버 이름·얼굴 신원·확정 track이 아니다. 단체 안무·교체·입장·종료는 공동 메인 또는 보류 검토 상태로 남겼다. 기존 앱 출력도 검토자가 이미 본 상태라 완전히 blind한 독립 정답으로 부르지 않는다.

## 검증과 정확한 한계

- 실모델 대신 가짜 `[1,6,56]` 출력으로 좌표 역변환, BGR→RGB, score/invalid box 필터, 잘못된 출력 shape, 로컬 SavedModel 경로와 CPU 호출 계약을 테스트했다.
- 가짜 12프레임 입력으로 4프레임 간격 관측, 모든 인물 기록, main/group 기록, 얼굴·렌더 경로 미호출을 확인했다. 기존 W13 평가 테스트도 함께 통과했다.
- MoveNet 신규 테스트 7개와 기존 W13 평가 테스트 5개를 포함한 집중 실행은 **12 passed**다. Python 전체 `pytest -q`는 **549 passed, 3 skipped, 4 failed, 16 errors**였다. 실패 4개와 오류 16개는 이 sandbox에서 `127.0.0.1` 포트 bind가 `PermissionError`로 거부되는 e2e/원격 에셋 fixture다. 이 20개만 제외한 비 e2e 실행은 **494 passed, 1 skipped, 5 deselected**다. skip 1개는 격리 Python worktree 옆에 Angular checkout이 없는 parity 테스트다. 따라서 전체 suite green이라고 쓰지 않는다.
- 변경 Python 파일의 `ruff check`, `py_compile`, `git diff --check`는 통과했다.
- **실제 Google weight는 다운로드·로드하지 않았다. 실제 영상 추론, 정확도·처리시간·메모리 측정, clip 생성은 0회다.** TensorFlow 파일의 실제 signature/배포 환경 동작과 얼굴/identity 비교는 검증하지 않았다. 현재 기존 YOLO 앱 산출물은 프레임별 pose가 없어 통제된 모델 A/B 기준선이 아니다.
- 이번 검토표는 정지화면 2fps, 두 전환 구간 4fps에 근거한다. 연속 영상 재검토, 공동 메인 집합, 프레임별 사람 위치/상자, 기존 예측을 보지 않은 별도 점검이 없어 scoring용 정답으로 고정하지 않았다. 그룹 장면의 `main_ids_draft: null`은 **폐기 대상이 아니라 검토 필요**를 뜻한다.

## 실제 평가 전에 남은 것

1. 전체 영상의 연속 재생과 사람별 위치 표식으로 검토표를 보강하고, 단독/공동 메인·보류 기준을 고정한다. 멤버 이름이나 참조 이미지는 포즈/메인 평가에 필요하지 않다.
2. 선택한 모델 artifact의 정확한 revision·로컬 경로·SHA-256과 배포 notice를 확보한다. 현재 `tensorflow` 런타임도 이 worktree에 설치하지 않았다.
3. 가짜 입력 외 실제 SavedModel 로드 계약 검증 후, 코드 fingerprint·CPU/반복·시간·RSS·출력 상한을 강제하는 runner를 만든다. manifest의 제안값을 실행값으로 확정하기 전에는 영상 추론을 호출하지 않는다.

[MoveNet 실행 조건 초안](01-w13-movenet-comparison-manifest.yaml)을 갱신했다. commit/push/merge/deploy, Build5, 외부 과금은 수행하지 않았다.

후속으로 [상한 강제 runner와 15개 합성 테스트](01-w13-movenet-runner-readiness.md)를 준비했다. 위 3번의 runner 미구현 설명은 이 문서 작성 시점의 상태이며, 실모델 파일·실영상 평가·독립 정답은 여전히 없다.
