# W13 — 비공개 상용 제품용 포즈 모델 교체 조사 (2026-10-01)

## 사용자 선택과 결론 범위

사용자는 Adlight 제품 소스 공개가 불가능하다고 밝혔다. 이어서 Google **MoveNet MultiPose Lightning을 1차 비교 후보**로 두자는 제안에 `응`이라고 답했다. 이는 후보 선택으로 기록한다. 실제 모델 다운로드, 제품 코드 변경, 원본 영상 ML 실행의 세부 범위 승인으로 넓혀 해석하지 않는다.

현재 설치형 Dance Python의 `PoseEngine`은 `ultralytics.YOLO("yolov8s-pose.pt")`를 호출한다. [Ultralytics 현재 라이선스 안내](https://www.ultralytics.com/license)는 AGPL 공개 의무와 별도 Enterprise 라이선스를 구분하고 비공개 상용 제품을 후자의 사례로 든다. 과거 사용권 검토·별도 계약은 저장소에서 확인되지 않았고, 사용자는 당시 사용 가능 여부를 확인한 기억이 있다. 따라서 현재 제품의 위반 여부를 단정하지 않는다. 다만 제품 소스를 공개할 수 없다는 새 제약 때문에 AGPL 조건만을 전제로 한 신규 YOLO 평가·최신 YOLO 교체는 추천하지 않는다.

## 확인한 무료 상용 후보

| 후보 | 코드·가중치 권리 | 안무 입력과 기술적 맞음 | 현재 결론 |
| --- | --- | --- | --- |
| **Google MoveNet MultiPose Lightning, TensorFlow 2 v1** | [Google 배포 모델 페이지](https://www.kaggle.com/models/google/movenet/tensorFlow2/multipose-lightning/1?tfhub-redirect=true)는 해당 variation에 Apache 2.0을 명시한다. [TensorFlow 코드](https://github.com/tensorflow/tensorflow/blob/master/LICENSE)도 Apache 2.0. Apache 2.0은 상업 이용과 비공개 제품 배포를 허용하며 라이선스·저작권 표시와 해당하는 경우 NOTICE 유지 의무가 남는다. | [Google 모델 카드](https://storage.googleapis.com/movenet/MoveNet.MultiPose%20Model%20Card.pdf)는 17개 COCO 관절, 최대 6명, bbox와 점수 `[1,6,56]`, 움직임이 많은 fitness/dance 영상 대상이라고 설명한다. 원본 1920×1012 무대에서 작은 인물을 놓칠 위험과 6명 초과 컷은 미측정. | **1차 비교 후보**. 이 특정 TF2 variation의 실제 파일/revision/hash는 다운로드 전이라 미고정. 정확도 향상·제품 처리 시간 개선은 미검증. |
| Intel Open Model Zoo `human-pose-estimation-0007` | [저장소](https://github.com/openvinotoolkit/open_model_zoo)는 Intel pretrained 모델을 포함하고 Apache 2.0을 표시한다. 선택한 바이너리의 배포 조건·notice를 다시 대조해야 한다. | [모델 문서](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/intel/human-pose-estimation-0007/README.md)는 다중 인물·17개 관절을 명시한다. [OpenVINO 2026 환경 표](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino/system-requirements.html)는 Windows x64/macOS arm64 CPU를 포함한다. | 백업 후보. 가중치 파일별 조건과 통합 난이도·우리 영상 성능 미검증. |
| OpenMMLab RTMO/RTMPose | [MMPose 코드](https://github.com/open-mmlab/mmpose)는 Apache 2.0이다. 다만 [정확한 checkpoint의 상업 사용·재배포 문의](https://github.com/open-mmlab/mmpose/issues/3273)는 2026-10-01 현재 공개 답변으로 해결되지 않았다. | RTMO는 다중 인물 포즈 후보지만 RTMPose top-down은 별도 사람 detector가 필요하다. | 이번의 **확정 무료 후보로 분류하지 않음**. 코드 라이선스만으로 가중치 이용권을 추정하지 않는다. |

## Python 평가 설계

1. 현행 W13 격리 worktree의 export 없는 평가 경로를 바탕으로, **포즈 관측만 기록하는 별도 adapter 설계**를 둔다. 모델 선택 외에 main selector·IoU tracker·그룹/보존 정책을 바꾸지 않는다. Google 모델 출력을 원본 좌표의 `bbox xyxy`와 17×2 관절·관절 confidence로 변환한다. 리사이즈/패딩을 역변환해 원본 좌표와 일치시키고, 최대 6명·confidence 기준·누락 사유를 남긴다. 현재 Python adapter에는 이 경로가 구현돼 있지 않다.
2. [이미 받은 전체 원본](01-w13-existing-app-input-inventory.json) **0~133.654059초**를 대상으로 한다. 메인·공동 메인·보류의 독립 익명 사람별 정답표는 아직 없다. 기존 19구간 초안은 점수용 라벨이 아니다. 멤버 이름과 참조 이미지는 1차 포즈·메인 평가에 쓰지 않는다.
3. 포즈 관측의 인물 검출 누락/오검출과, 동일한 downstream 규칙을 통과한 **메인 집합 정확도·전환 지연·공동 메인/보류 coverage**를 분리한다. 얼굴 identity precision/unknown 오배정률은 이번 포즈 비교의 점수로 합치지 않는다. `pose_energy`가 시간상 움직임이 아닌 같은 프레임 관절 거리 합이고 현행 selector가 메인 하나를 고르는 점 때문에, 포즈 모델만 교체해서 다중 메인 요구가 해결되지는 않는다.
4. 신규 Ultralytics 추론은 과거 사용권 범위가 확인되기 전 실행하지 않는다. 이미 앱에서 만든 YOLO 결과는 **역사적 참고 기준**이며, 그 결과에는 프레임별 원본 pose 출력이 없어 MoveNet과 통제된 동일 조건 A/B 정확도 비교가 아니다. 따라서 새 MoveNet 실행만으로 `YOLO보다 정확하다`고 발표하지 않는다.
5. 실제 제품 적용은 평가 뒤 별도 결정한다. Python 3.11/macOS arm64·Windows x64용 [TensorFlow 설치 가이드](https://www.tensorflow.org/install/pip)는 CPU wheel을 제공한다. [LiteRT 2.2.0 배포 파일](https://pypi.org/project/ai-edge-litert/)도 두 OS의 CPython 3.11 wheel을 게시하지만, **선택한 TF2 모델을 LiteRT 파일로 변환·패키징·실행할 수 있는지는 별도 검증**이다. TF2 CPU 평가 성공을 배포용 GPU/MPS/CUDA 성능으로 바꾸어 말하지 않는다.

[별도 MoveNet 실험 manifest 초안](01-w13-movenet-comparison-manifest.yaml)에 입력과 미확정 gate를 적었다. 이 조사에서 모델/의존성 다운로드, 새 ML, 제품 코드 변경, Build5, commit/push/merge/deploy는 하지 않았다.

후속 진행에서 [MoveNet 출력 변환·포즈 전용 평가 경로와 익명 메인 검토표](01-w13-movenet-adapter-and-label-prep.md)를 준비했다. 이 문서의 "현재 adapter 미구현"은 후보 선택 당시 상태이며, 후속 기록의 가짜 입력 검증 상태가 최신이다.
