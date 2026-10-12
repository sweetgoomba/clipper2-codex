# W13 첫 비교 준비: 모델 파일과 원본 장면 표 — 2026-10-01

## 현재 한 일

- 사용자가 지정한 `yFTAYXDTjqI` 기존 앱 원본 MP4만 읽었다. 입력은 **0~133.654059초 전체**, SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`다. 영상이나 기존 앱 결과를 수정하지 않았다.
- [Google 공식 MoveNet MultiPose Lightning TF2 v1 카드](https://www.kaggle.com/models/google/movenet/tensorFlow2/multipose-lightning/1)에서 Apache-2.0 weight와 최대 6명·17관절·bbox 출력 표기를 재확인하고, 해당 버전의 공식 배포 archive를 W13 격리 worktree의 `output/model-assets/`에 받았다. archive는 18,612,451 bytes, SHA-256 `f01b9e5e8c3bc31f82e9ca7fa4a2876f25d7a54b65c83da5df2eca3e1632cec8`이다. 압축 안의 SavedModel 파일 목록을 확인한 뒤 추출했고, 실행기의 `sha256_tree` 기준 디렉터리 hash는 `ea71312368f39053ed7b9b2e4fac3bcecd94c667f679830a0a999b31ccaf705c`다. archive에는 별도 LICENSE 파일이 없으므로 제품 포함 시 공식 카드의 라이선스 표시와 Apache-2.0 고지 처리를 별도로 확인한다.
- TensorFlow는 현재 Python 환경에 없다. 모델 **로드·signature 확인·추론은 0회**다. 제품 기본 YOLO 경로와 W14 공통 얼굴 파일은 변경하지 않았다.
- [TensorFlow 공식 설치표](https://www.tensorflow.org/install/pip)에는 Python 3.11/macOS Arm64용 CPU wheel이 있고, [PyPI TensorFlow 2.21.0 파일 목록](https://pypi.org/project/tensorflow/2.21.0/)에는 해당 wheel 약 223.4 MB가 표시된다. 이는 설치 가능성의 문서 확인이며, 이 SavedModel과 현재 평가 코드의 실제 호환 검증은 아니다. 런타임을 받거나 설치하지 않았다.
- 원본에서 `analyze_skip=4`에 맞는 프레임을 추출해 [15개 시점 관찰과 3프레임×5명 위치 초안](01-w13-source-frame-observations.json)을 작성했다. 옷 색은 이름 확인 요청이 아니라 같은 영상의 익명 `P1`~`P5`를 구분하기 위한 임시 시각 단서다. 18초 `P1`, 22초 `P2`, 29~32초 `P3`, 56초 `P4`, 61초 `P5`가 앞서는 장면을 볼 수 있다. 38·46·74·86·96초는 동시 군무라 중앙 사람 하나를 강제하지 않는다. 100~112초는 대형 변화와 종료 포즈가 섞여 있어 [19구간 표](01-w13-anonymous-main-review.json)의 넓은 `group_review` 범위를 그대로 확정하면 안 된다.

## 이 자료로 할 수 있는 것과 아직 할 수 없는 것

현재 위치 사각형은 픽셀 단위의 **대략적인 육안 초안**이다. 전체 영상을 연속 재생해 모든 교체 경계를 확인하지 않았고, 기존 앱 결과가 검토자에게 이미 보였으므로 기존 결과와 독립적인 채점 정답이라고 주장하지 않는다. 멤버 실명이나 참조 얼굴 이미지는 첫 **포즈/메인 비교**에는 필요하지 않다. 공동 메인과 보류 장면은 버리지 않는 정책을 유지한다.

[실행 manifest](01-w13-movenet-comparison-manifest.yaml)는 모델 경로와 hash만 채웠고 `approved_for_execution`이 아니다. 현재 실행기를 호출하면 모델 추론 전에 거절한다. 다음 잠금값은 사람별 위치/메인 정답의 독립 검토, TensorFlow 런타임과 SavedModel signature, 최종 코드 fingerprint, CPU·최대 3회·pass당 600초/전체 1800초·worker RSS 12 GiB·metadata 250 MiB·격리 출력 경로에 대한 실행 범위 확정이다. 새 YOLO pass는 제안하지 않는다. 실제 정확도·처리시간·메모리 수치는 아직 없다.

이번 변경은 문서와 격리 `output/` 파일뿐이다. commit/push/merge/deploy, 앱 재빌드, clip export, 얼굴/ML 영상 평가는 하지 않았다.
