# W13 최신 YOLO Pose와 MoveNet 두 계열 평가 검토 — 2026-10-13

## 사용자 요청과 현재 상태

사용자는 기존 YOLO Pose 계열을 비교 대상에 남기고, 출시된 더 최신 자세 모델로 갱신해 MoveNet과 두 계열을 평가하자고 했다. 제품 기본 모델 변경과 실제 ML 성능 우위가 이미 결정됐다는 뜻으로 해석하지 않는다. 사람별 얼굴 이름 매칭은 별도 인물 하이라이트/공통 얼굴 작업 범위이며, W13 비교는 몸 검출·메인 선택·구간 경계·군무·복수 메인이다.

현재 Python 앱 기본은 `plugins/dance_highlight/dance_highlight/services/config.py`의 `yolov8s-pose.pt`, `pose_engine.py`의 `ultralytics.YOLO` 호출이다. 로컬 설치된 Ultralytics는 `8.4.38`이고 YOLO26 Pose 아키텍처 YAML은 있으나, W13 격리 worktree와 기존 Python checkout에서 `yolo26s-pose.pt` 또는 해당 ONNX weight는 확인되지 않았다. 저장 MoveNet MultiPose Lightning 256·512는 **한 모델 weight에 서로 다른 입력 크기**를 준 결과다. W13 격리 Python worktree HEAD는 `47782953228861f4bdbdc135265d067c2a826b0e`, 추적/미추적 변경을 보존한다.

## 공식 모델·사용권 확인

- [Ultralytics 모델 목록](https://docs.ultralytics.com/models)은 2026-10-13 확인 시 **YOLO26(2026년 1월 출시)**을 최신 공개 배포 계열로 설명한다. [YOLO27 페이지](https://docs.ultralytics.com/models/yolo27)는 예고 상태이며 weight와 실행 코드가 아직 배포되지 않았다고 명시한다. 따라서 시험 가능한 최신 동일 크기 등급은 [YOLO26s-pose](https://docs.ultralytics.com/tasks/pose)다.
- 공식 COCO keypoint 표는 구형 `yolov8s-pose` pose mAP50-95 **60.0**과 새 `yolo26s-pose` **63.0(e2e)**을 각각 제시한다([v8 문서](https://docs.ultralytics.com/models/yolov8), [YOLO26 Pose 문서](https://docs.ultralytics.com/tasks/pose)). 벤치마크 실행 체계와 우리 공연 영상·선택기 지표는 다르다. 이 숫자를 W13 정확도 향상으로 환산하지 않는다.
- [Ultralytics 공개 라이선스 안내](https://www.ultralytics.com/license)에 따르면 비공개 SaaS의 YOLO 사용은 Enterprise 계약이 필요하다. [별도 R&D 계약](https://www.ultralytics.com/legal/ultralytics-rd-license-terms-single-project)은 내부 실험만 허용하고 고객/운영/상업 사용을 허용하지 않는다. 기존 사용자 진술은 Enterprise 계약 없음·소스 공개 불가·구매 계획 없음이었다. 이번 문의가 계약 실제 체결을 뜻하지는 않으므로 **YOLO26 weight 획득·새 추론·제품 적용은 계약 상태 확인 전 0회**다. 기존 YOLOv8 완성 결과와 로그의 정적 조회만 허용 범위로 유지한다.

## 지금까지 얻은 성과와 미달성

사용자가 같은 133.654초 원본의 정답표 21행(main 15/group 4/exclude 2)을 확정했다. 이 기준으로 9/29 기존 YOLO 앱 완성 결과와 10/2 MoveNet 256 실험 완성 결과를 비교하면 정답 멤버 출력 **36.68/82.50초→25.81/82.50초**, 다른 멤버 출력 **28.97→54.19초**다. MoveNet 256은 기존보다 완성 결과가 나쁘다는 사용자 평가와 같은 방향이다. 다만 이 수치는 포즈 모델, 후처리, 얼굴 이름 매핑을 모두 포함해 **YOLO와 MoveNet 자세 모델 단독 우위는 미검증**이다.

MoveNet 입력만 256→512로 바꾼 잠금 사람 표본은 **33/45→45/45 검출**로 늘었지만 기존 단독 메인 18장은 **6/18→6/18**이었다. 512 저장 자세의 메인 점수 정규화 후보는 사용자 메인 경계 11곳 적중 **5→8**이었으나 큰 상자 이동 **14→33**, 예측 경계 **16→20**으로 늘어 제품 미채택이다. 사용자 전체 영상 검토에서 22·28·54·59~61초 메인 튐과 65초 이후 군무 실패를 특정했다. 정적 관절 길이 점수, 중앙 위치 편향, 기존 선택 유지, 원본 FPS로 센 `skip4` streak, 군무의 점수/크기 gate, 일부 IoU track 사람 교체가 분리된 원인 후보다. 얼굴 매칭 개선으로 대신 해결할 문제로 보지 않는다.

**아직 얻지 못한 것:** 두 자세 계열의 동일 원본·동일 후처리 pose-only 직접 비교, 안정적인 새 메인/군무 선택기, 실제 앱의 개선된 완성 클립. 모델 업데이트만으로 이 문제가 해결된다는 증거는 없다.

## 제안하는 다음 평가 단계 — 아직 실행 전

1. 비교 후보를 `yolo26s-pose` 한 조건과 저장 MoveNet 256·512 두 입력 조건으로 잠근다. 기존 `yolov8s-pose`는 새 추론 없이 과거 앱 결과/로그 기준선으로 보존한다. 한 번에 모델과 선택기 규칙을 같이 바꾸지 않는다.
2. **유료 사용권의 실제 체결·계약 범위 확인 후** YOLO26 weight 획득과 checksum을 기록하고, 별도 격리 adapter로 동일 원본 전체 `skip4` 자세 metadata를 만든다. 원본/정답표/실행 SHA, 모델 hash, OS·장치, 횟수·시간·메모리·출력 상한을 실행 manifest에 잠근다. 기본 제품 config는 변경하지 않는다.
3. 동일 schema와 동일 사람/메인/그룹 후처리로 MoveNet 저장 metadata와 비교한다. 사람 검출률, 정답 메인 위치 선택, 전환 지연·불필요한 경계, 군무 오판, 복수 메인 보존을 분리한다. 기존 21행 정답표와 노트북에서 구간별 결과를 확인한다.
4. 특정 계열이 검출은 좋아도 메인 선정이 나쁘면 모델보다 선택·추적 규칙을 수정한다. 전체 게이트를 통과한 뒤에만 실제 새 clip을 앱에서 같은 영상으로 비교한다. 앱 기본 모델 교체·얼굴 모델 작업은 별도 결정이다.

이번 기록은 공식 정보와 기존 로컬 artifact의 **읽기 전용 확인**이다. 새 weight/런타임 다운로드, 새 YOLO·MoveNet 추론, 클립 export, 제품 코드 수정, commit/push/merge/deploy는 없다.
