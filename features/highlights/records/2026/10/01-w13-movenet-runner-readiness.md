# W13 MoveNet 평가 실행기 준비 — 2026-10-01

**후속 상태:** 사용자가 고정 범위를 승인해 실제 metadata 평가 3회를 완료했다. [실행·표본 결과](01-w13-movenet-first-real-metadata-evaluation.md)가 현재 상태이며, 아래 준비/거절 기록은 실행 전 시점의 증거다.

## 무엇을 만들었나

W13 Python 격리 worktree `feature/w13-dance-metadata-eval-20261001`의 `tools/w13_movenet_runner.py`를 추가했다. 이것은 제품 앱의 모델 교체가 아니라, 별도로 실행하는 **포즈 metadata 평가 전용 명령**이다. 기존 앱 영상이나 clip을 수정하지 않는다.

명령은 먼저 manifest가 실행 승인 상태인지 검사한다. 이후 원본 MP4, 로컬 SavedModel 디렉터리 전체, 사람별 정답 JSON의 SHA-256, 정답 원본 hash와 0~133.654059초의 구간 연속성, 평가 코드 fingerprint, OS/Python 및 런타임 버전, CPU, 분석 간격, 추론 점수 기준, 횟수, 시간·메모리·출력 상한, 빈 출력 디렉터리가 모두 고정된 경우에만 worker를 시작한다. 실행 전 당시 [manifest](01-w13-movenet-comparison-manifest.yaml)는 `ready_for_user_scope_review_no_inference`이며 실행 승인값 둘도 `false`라 **추론 시작 전에 거절**했다. 완료 후에는 `completed_scoped_metadata_run`으로 다시 닫았다.

승인된 실행을 가정한 테스트에서는 pass당 별도 worker를 실행하고, 원본 소스의 포즈 관측 JSON과 실행시간·최대 worker RSS를 기록한다. 얼굴 판정, 참조 이미지, clip/썸네일 export 경로는 호출하지 않는다. worker는 이 격리 worktree의 Python 패키지 경로를 우선 사용한다. 시간·RSS·출력량 초과 또는 모니터 중단 시 worker를 죽인다. macOS sandbox에서는 자식 프로세스 목록 열람이 막혀 있어 **직접 worker PID의 RSS**만 감시한다. 현재 TensorFlow 추론은 그 단일 프로세스의 스레드에서 실행하는 설계다. RSS를 읽을 수 없으면 실행을 중단하도록 했다. 상한은 50ms 간격 관측으로 강제하므로 그 사이 일시적 초과 가능성은 있다.

## 검증

- `tests/test_dance_movenet_runner.py`: **22 passed**. 승인 전 거절, 원본/정답 hash·정답 구간 불일치, 분석 간격 미고정, 런타임 패키지 누락, 시간/RSS/출력 초과 및 취소 중단, metadata 전용 worker, 지정 횟수, 합계 출력 한도 등을 가짜 모델 파일·가짜 worker로 확인했다. 후속 3개 테스트는 부분 runtime lock 거절과 직접 import하는 `protocols.py`·`dance_meta.py` 변경 시 코드 fingerprint 변화를 확인한다.
- 첫 비 e2e 전체 재실행은 **571 passed, 1 skipped, 5 errors**였다. 오류 5개는 이 sandbox에서 로컬 HTTP 서버의 `127.0.0.1` bind가 거부된 fixture다. 해당 5개만 제외한 재실행은 **571 passed, 1 skipped, 5 deselected**였다. 전체 suite green이라고 주장하지 않는다.
- 실제 CLI: `python tools/w13_movenet_runner.py <현재 manifest> --execute` → exit 2, `evaluation refused: manifest must have status approved_for_execution`. 모델 로드는 시작하지 않았다.
- 확인한 코드 fingerprint 초안: `333b11306a8edea2a0339d91b26da2e0ef1b6f76d6be49ed8582a255ae7df2b1` (이후 코드 변경 시 재계산). OS `macOS-27.0-arm64-arm-64bit`, Python `3.11.12`.
- 위 22개는 준비 도구의 합성 테스트이지 성능 평가가 아니다. 이 기록의 첫 작성 뒤 공식 MoveNet archive를 확보했고, 후속 [런타임·signature 확인](01-w13-movenet-runtime-signature-lock.md)에서 TensorFlow로 모델을 **입출력 형식 확인 목적으로만 로드**했다. 추론 함수·실영상 추론은 0회이며 실제 입력의 정확도·처리시간·메모리 사용량 결과는 없다. [모델·원본 프레임 기록](01-w13-model-file-and-source-label-progress.md)에 hash와 육안 초안 범위를 적었다.

후속 점검에서 실행 코드가 직접 import하는 `protocols.py`와 `dance_meta.py`가 원래 fingerprint 목록에서 빠진 것을 확인하고 포함했다. 또한 TensorFlow만 적힌 manifest로 실행할 수 없도록 NumPy·OpenCV·psutil·PyYAML·requests 버전도 필수로 고정한다. 수정 전에는 각각의 변경을 놓치는 테스트가 실패했고, 수정 후 새 테스트 3개가 통과했다. 이는 같은 코드를 다시 실행할 조건을 좁힌 것이며 실제 모델 성능 검증은 아니다.

## 실제 평가 전에 남은 잠금값

1. Google 배포 TF2 v1 weight의 로컬 경로·archive/디렉터리 hash와 공식 PyPI TensorFlow 2.21.0 wheel hash를 [manifest](01-w13-movenet-comparison-manifest.yaml)에 채웠다. 격리 `.venv`의 36개 패키지 버전, SavedModel 입출력 signature와 어댑터 로더 동작을 [후속 기록](01-w13-movenet-runtime-signature-lock.md)에서 확인했다. 실제 추론 함수 호출은 아직 없다.
2. [제한된 채점 라벨](01-w13-pose-scoring-labels-v1.json)과 [독립 표본 감사](01-w13-independent-label-audit.md)는 고정했다. 18초의 명확한 솔로 **기준 창**은 있지만 사람 위치가 확인된 메인 채점 프레임은 P1~P4 각 1장, **4장뿐**이다. P5는 기준 창은 있어도 채점 위치 상자가 없다. 사람 검출 표본은 공연 9프레임×5명=45개와 빈 화면 2프레임이다. [채점 규칙](01-w13-pose-scoring-policy-v1.md)은 이 제한을 명시한다. 전체 133.654059초의 익명 사람별 위치·단독/공동 메인 정답은 아직 없으므로 전체 영상/18초 매 프레임 정확도, 공동 메인 precision/recall, 전환 지연 수치는 낼 수 없다. 멤버 이름이나 의상 정보를 사용자에게 받을 필요는 없다. runner는 제한된 라벨도 읽을 수 있지만 manifest 미승인으로 계속 거절한다.
3. 코드 fingerprint, CPU, 최대 3회, pass당 600초·전체 1800초, worker RSS 12 GiB, 출력 총 250 MiB, 격리 worktree 출력 디렉터리를 **manifest 값**으로 채웠다. 해시·버전의 읽기 전용 사전 검사는 통과했지만 이 수치는 아직 사용자 승인값이 아니다. 새 YOLO pass는 0회다.

사용자가 [한 장 실행 범위](01-w13-movenet-execution-scope-one-page.md)를 선택하기 전에는 기존 YOLO 산출물과 라벨의 정적 비교만 가능하다. 기존 YOLO 앱 결과에는 같은 프레임의 pose 관측이 남아 있지 않아 MoveNet과 통제된 정확도 A/B라고 부를 수 없다. 제품 기본 모델, W14 공통 얼굴 코드, 기존 프로젝트/원본은 건드리지 않았다. commit/push/merge/deploy도 하지 않았다.
