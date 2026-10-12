# W13 모델 관계와 Intel 후보 보류 — 2026-10-02

설치 앱 기본은 `yolov8s-pose.pt`(Ultralytics YOLOv8s Pose)다. 영상 속 사람과 관절을 찾는 단계이며, 그 다음의 **메인 댄서 선정·IoU 추적·얼굴/멤버 연결·클립 생성**은 별도 코드다. 기존 앱 모델을 정확도 측정으로 폐기한 적은 없다. 다만 사용자가 비공개 상업 SaaS를 만들고 있어 [Ultralytics 공식 라이선스 설명](https://www.ultralytics.com/license)의 AGPL/Enterprise 조건을 다시 검토했고, Enterprise 계약 확인 전에는 이를 앞으로의 비공개 제품 대체 후보로 계속 확대하지 않기로 했다.

첫 대체 **실험**은 로컬 MoveNet MultiPose Lightning이다. 256 입력으로 같은 원본 전체를 분석한 뒤, 같은 가중치의 입력만 512로 바꿔 한 번 더 평가했다. MoveNet은 앱 기본 모델이 아니다. 512에서 고정 원본 표본의 사람은 45/45 검출됐지만, 단독 메인 선정은 18장 중 6장으로 256과 같고 추가 17장은 7→6으로 떨어졌다. 즉 이 영상에서는 사람을 찾는 문제만 해결해도 메인 선택이 좋아지지 않았다. 사전 점수의 화면 중앙 선호·전환 유지·단일 메인 가정이 실패와 연결된다. 선택 점수의 `pose_energy`도 시간상 움직임이 아닌 한 프레임 관절 거리 합이다. [실행·후속 판단](02-w13-movenet-512-result-and-selector-probe.md).

Intel Open Model Zoo `human-pose-estimation-0007`은 또 다른 **다인 자세 검출 모델 후보**다. [공식 모델 파일 정보](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/models/intel/human-pose-estimation-0007/model.yml)는 Apache-2.0 사용권을 가리켜 비공개 제품 후보 조사 대상으로 골랐다. 하지만 이것이 MoveNet이나 기존 YOLO보다 이 영상에서 정확하거나 빠르다는 실측은 없다. MoveNet 다음의 **두 번째 대체 자세 모델 후보**였을 뿐이며, 얼굴 인식 모델도 메인 인물 선택 알고리즘도 아니다. 공식 벤치마크는 우리 안무 영상의 메인 선택 품질을 증명하지 않는다.

따라서 Intel 파일·런타임 다운로드와 평가를 **보류**한다. 앞서 요청한 다운로드 확인은 현재 다음 단계로 필요하지 않다. 저장된 MoveNet 512 사람별 상자·관절 결과와 기존 원본을 이용해, 중앙/인계/가림/그룹 장면의 **연속 메인 인물·공동 메인·보류 정답**을 먼저 만들고 선택·추적 규칙을 검증한다. 그 과정에서 검출 자체가 다시 병목임이 확인될 때 Intel 같은 두 번째 자세 모델을 대조한다. Intel 어댑터·평가 도구는 격리 작업본에 보존하되 제품 경로에 연결하지 않는다. 새 Intel 추론/완료 MP4/앱 기본 모델 변경은 0회다.
