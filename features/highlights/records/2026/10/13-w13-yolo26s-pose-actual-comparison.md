# W13 · YOLO26s Pose 실제 전체 영상 평가 (2026-10-13)

## 범위와 사용자 결정

사용자가 최신 YOLO Pose와 MoveNet을 실험 후보로 함께 두고, YOLO26s는 성능을 먼저 시험하라고 지시했다. 이는 제품에 YOLO를 채택하거나 Enterprise 계약을 보유한다는 뜻이 아니다. W13의 이번 비교는 **자세 검출→메인 선택→IoU track→군무 표시**만 다룬다. 얼굴 검출·멤버 이름 매칭은 W14/인물 하이라이트 작업으로 분리하며 이 실행에서는 얼굴 참조 이미지 0장, 얼굴 추론 0회다. 실험 결과를 제품 앱에 반영하지 않았다.

## 고정한 입력과 실행

| 항목 | 값 |
|---|---|
| 원본 | 기존 완료 앱과 같은 `yFTAYXDTjqI/source.mp4`, 전체 0~133.654059초 |
| 원본 SHA-256 | `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4` |
| 사용자 정답 | 기존 `confirmed` 21행(main 15, group 4, exclude 2), SHA-256 `d451572c00142fc8b110678da974665b26d9d058938c5be2e7115e6080e00ab0` |
| 모델 | 공식 Ultralytics assets v8.4.0 `yolo26s-pose.pt`, SHA-256 `a083adb42303728ae14c4bd6bd56d80da46f82fb2564dbd6f31dcc92ea321646` |
| 실행 | Mac mini M4 / macOS-27.0-arm64 / Python 3.11.12 / Ultralytics 8.4.38 / torch 2.11.0 / CPU / `analyze_skip=4` / conf 0.25 / IoU 0.7 |
| 한도 | 전체 영상 새 추론 1회, 600초·RSS 12 GiB·metadata 250 MiB; 다운로드는 해당 모델 파일 1개 23 MiB |
| 코드 | Python HEAD `4778295`; 격리 `feature/w13-dance-metadata-eval-20261001`; 평가 runner SHA는 [실행 manifest](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/tools/w13_yolo26s_execution_manifest.yaml)에 기록 |

평가 전용 `DancePipeline.analyze_pose_for_evaluation()`을 사용해 같은 메인 점수·선택 유지·IoU track·군무 규칙을 유지했다. `run()`의 얼굴 분석·클립 export를 호출하지 않았다. 새 모델을 절대경로로 전달해 다른 weight를 자동으로 받지 않게 했다. [실행 manifest](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/tools/w13_yolo26s_execution_manifest.yaml), [run summary](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/yolo26s-pose-v1/summary.json), [자세 metadata](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/yolo26s-pose-v1/run-01/pose.json)를 보존했다. 실제 실행은 **90.122초**, 최고 worker RSS **596,393,984 bytes**, 2,002개 관측 프레임, 자세 JSON **7,015,189 bytes**로 한도 안이었다.

## 같은 원본·동일 선택기의 비교

| 저장 자세 조건 | 고정 45명 검출 | 메인 선택 18장 | 명시적 군무 안 군무 표시 | 군무와 겹치지 않는 메인에서 군무 오표시 | 1초 미만 raw 메인 조각 |
|---|---:|---:|---:|---:|---:|
| MoveNet 256 | 33/45 | 6/18 | 711/963 | 544/642 | 266 |
| MoveNet 512 | 45/45 | 6/18 | 419/963 | 238/642 | 6 |
| YOLO26s | **45/45** | **9/18** | **160/963** | **0/642** | **17** |

YOLO26s의 메인 표본 적중은 MoveNet 두 조건보다 3장 많지만 **전체 영상 메인 정확도는 아니다**. 사람별 위치 정답이 잠긴 18장에 한정된다. 사용자의 21행은 메인·군무가 일부 겹치므로 군무 표시율과 단독 오표시율을 합쳐 단일 정확도라고 하지 않는다. YOLO26s 군무 구간별 표시는 5.6~13.2초 **0/114**, 35.0~49.8초 **120/222**, 63.7~78.8초 **0/226**, 85.9~112.7초 **40/401**이다. raw 메인 조각은 47개로 MoveNet 512의 29개보다 많다. 이 수는 최종 클립 수와 다르다.

[실행된 11차 노트북](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_11_yolo26s_vs_movenet.ipynb)과 [동일 프레임 그림](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/yolo26s-pose-v1/selected-frame-comparison.png)에서 22·28초 세 조건 모두 파란 의상 사람을 선택해 사용자가 원하는 노란 의상 사람으로 바로 넘어가지 못함, 54초 세 조건 모두 중앙 연두 의상 선택, 60초 YOLO26s의 왼쪽 보라 의상 선택, 68·90초 YOLO26s 군무 표시 꺼짐을 확인했다. 이것은 얼굴 이름 판정이 아니라 원본 화면에서 선택된 **몸 위치**의 관찰이다.

## 기준값만 낮추는 시험과 판단

새 모델 추론 없이 저장 자세를 이용해 기존 군무 규칙의 상위 두 점수차·전체 상자 크기 비율·진입 streak 36조합을 재계산했다. YOLO26s의 기본 `(점수차 0.10, 상자비 1.9, 진입 20관측)`은 군무 **160/963**, 메인 전용 오표시 **0/642**다. 진입만 10관측으로 줄이면 **464/963**이지만 오표시도 **195/642**로 증가한다. 가장 느슨한 시험 조건 `(0.14, 2.5, 5관측)`은 군무 **853/963**이나 메인 전용 **642/642 전부**를 군무로 오표시한다. 단일 문턱 완화 조건은 제품에 채택하지 않는다. 다음은 시간에 따른 복수 인물 움직임·가림/인물 교체를 반영한 군무/메인 판정을 **서로 분리해** 저장 자세에서 비교해야 한다.

## 검증과 남은 일

- 공식 모델 파일 SHA와 원본/정답표 SHA를 실행 전에 검사했다. 새 runner의 hash 변조 차단·얼굴/클립 실행 차단·직접 CLI 시작 테스트 **3개 통과**. 로컬 테스트 포트를 허용해 전체 Python suite를 다시 실행한 결과 **633 passed, 5 skipped**. 처음 제한 환경의 포트 bind 오류와 잘못된 editable package import 경로를 구분하고 `PYTHONPATH`를 격리 작업본에 맞췄다.
- 노트북 **9셀·코드 4셀·실행 오류 0**, 비교 점수 JSON과 프레임 그림을 저장했다.
- 동일 원본의 제품 앱 새 클립, 메인 전체 정답, 공동 메인, 다른 영상 일반화, W14 얼굴 매칭 결과와의 결합은 **아직 평가하지 않았다**.
- 앱 기본 `yolov8s-pose.pt`, 기존 사용자 프로젝트, 공통 얼굴 파일, commit/push/merge/deploy는 변경하지 않았다. 비공개 상업 제품 적용 시 사용권 결정은 별도다.
