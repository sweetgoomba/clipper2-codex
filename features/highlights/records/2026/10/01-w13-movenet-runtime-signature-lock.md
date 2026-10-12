# W13 MoveNet 실행 환경·입출력 형식 확인 — 2026-10-01

이 문서는 **실행 전 준비 상태**의 기록이다. 이후 사용자가 범위를 승인해 CPU metadata 평가 3회를 완료했다. [실제 결과](01-w13-movenet-first-real-metadata-evaluation.md)가 현재 상태다.

## 이번에 확인한 것

- 격리 W13 Python worktree의 `.venv`에 Python **3.11.12**, TensorFlow **2.21.0**과 평가 경로의 의존성을 설치했다. 제품 Python 환경이나 기본 안무 모델 설정은 바꾸지 않았다.
- 공식 PyPI의 `tensorflow-2.21.0-cp311-cp311-macosx_12_0_arm64.whl`을 받아 SHA-256 **`51f46f4806139d01fc7920cc72a4c75876f80649bf40ff083ab6212ceb43ca88`**와 크기 **223,405,849 bytes**를 확인했다. 격리 경로 `output/runtime-wheels/`에 남겼다. 모델 archive/추출 디렉터리 hash는 기존 [manifest](01-w13-movenet-comparison-manifest.yaml) 값과 다시 일치했다.
- 로컬 `saved_model.pb`의 정적 서명과 실제 `tf.saved_model.load()` 결과 모두 `serving_default` 입력 **`input: int32 [1, None, None, 3]`**, 출력 **`output_0: float32 [1, 6, 56]`**을 보였다. W13 `load_local_saved_model()`도 로컬 모델을 열고 callable을 반환했다. **추론 함수는 호출하지 않았고 영상 프레임도 넣지 않았다.** 실제 프레임 전처리→모델 출력→selector 결합은 미검증이다.
- `pip check`는 **No broken requirements found**였다. [manifest](01-w13-movenet-comparison-manifest.yaml)에 현재 설치된 **36개 패키지 버전**을 기록하고 실제 설치 버전과 전부 대조했다. `idna`와 `packaging` 버전은 YAML 숫자 변환을 막도록 문자열로 적었다.
- 평가 코드 지문은 **`333b11306a8edea2a0339d91b26da2e0ef1b6f76d6be49ed8582a255ae7df2b1`**이다. 기준 Git HEAD `47782953228861f4bdbdc135265d067c2a826b0e`에서 격리 worktree의 미커밋 평가 파일까지 포함한 파일 hash 조합이다. OS 지문 `macOS-27.0-arm64-arm-64bit`, 장치는 Mac mini M4 CPU 제안이다. 코드가 바뀌면 재계산해야 한다.

## 실행 차단 확인

실행 전 당시 manifest는 `ready_for_user_scope_review_no_inference`였고 실행 횟수 승인·출력 위치 승인값은 모두 `false`였다. 그때 실제 runner CLI는 **exit 2, `evaluation refused: manifest must have status approved_for_execution`**으로 worker 시작 전에 멈췄다. 별도의 메모리 안 복사본에서 승인 플래그만 임시로 바꿔 `check_execution_manifest()`를 **읽기 전용으로** 실행했을 때, 원본/모델/라벨·코드·설치 버전·시간/RSS/출력 상한 검사에 통과했다. 그 복사본은 저장하거나 실행하지 않았다.

원본 전체 133.654059초, 참조 이미지 없음, 새 MoveNet 최대 3회, CPU `analyze_skip=4`, 회당 600초·전체 1800초, worker RSS 12,288MiB, metadata 250MiB, 격리 출력 경로는 [한 장 실행 범위](01-w13-movenet-execution-scope-one-page.md)에 있다. 이 수치를 고정한 뒤 별도의 사용자 실행 선택을 받았다. 기존 YOLO 신규 pass는 0회다. 평가 결과의 해석은 [후속 기록](01-w13-movenet-first-real-metadata-evaluation.md)에 있다.
