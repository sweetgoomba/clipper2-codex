# W13 — ANTIFRAGILE 원본 평가 실행 준비

상태: **원본·PTS·모델·실행기 사전 검증 완료. 새 영상의 포즈 추론·메인/군무 판정·얼굴 매칭·클립 생성은 미실행.** 실행 manifest는 `prepared`이며 `--execute`는 잠겨 있다.

## 무엇을 준비했나

- W14와 같은 [M2 ANTIFRAGILE 원본](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/source.mp4)을 읽기 전용으로 재확인했다. SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`, 150,370,135바이트, 1920×1080, 60000/1001fps이다.
- ffprobe가 표시한 영상 13,237프레임의 실제 PTS는 `0,1001,…,13249236`, time base `1/60000`으로 일정하다. 영상 구간 끝(끝 제외)은 PTS `13250237`, **220.837283초**다. 오디오를 포함한 컨테이너 220.891429초를 영상 끝으로 사용하지 않는다. ffprobe PTS 원시 출력 SHA는 [사전 점검 파일](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-preflight-v1/pts-preflight.json)에 기록했다.
- 4프레임마다 한 번이면 3,310개 포즈 관측이며, W14의 12프레임 간격 1,104개 얼굴 시점은 전부 그 부분집합이다. W14 얼굴 결과 SHA `93967024e0d79b0fa8276aa59cce22dc3a1a26878db3234ab2a63dad64949544`와 원본/시각을 검사한다.
- [새 실행기](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/tools/w13_antifragile_runner.py)를 기존 2,002시점 전용 실행기와 분리했다. 한 번의 순차 디코딩에서 RTMDet Nano 사람 상자와 RTMPose-m 관절을 관측하고, 원본 frame index·PTS·time base·원본 픽셀 좌표를 저장한다. 얼굴·멤버 이름·메인 역할은 판정하지 않으며 클립도 내보내지 않는다. `frame_index/fps` 추정 대신, 이 SHA의 원본에 대해 ffprobe로 전수 확인한 PTS 격자를 적용한다. 디코더가 다른 크기나 프레임 수를 반환하면 실패한다.
- [준비 manifest](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-preflight-v1/manifest-prepared.json)은 원본·모델 2개·W14 얼굴 관측·코드·런타임의 경로와 해시, CPU 1회, 전체 영상, 30분/8GiB/500MiB 상한 및 새 출력 위치를 고정한다. manifest SHA `ee96e38ce5fd0194712be25fa97a955c3d39b0e23518a6356b109b78ca61c42c`.
- [66번 사전 확인 노트북](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_66_antifragile_preflight.ipynb)은 준비된 입력/실행 범위만 읽는다. 기존에 열린 노트북 파일은 수정하지 않았다. 기존 `tools/start_w13_human_review.sh`로 JupyterLab을 재시작했고 API에서 새 노트북 3셀을 HTTP 200으로 확인했다.

## 검증과 한계

- 새 실행기 단위 검사 4개 통과, Ruff·Python 컴파일 통과, 준비 manifest 검증 `validated; inference not run`. 실행 명령의 `--execute`는 `user_approved`와 승인 기록이 없어서 거절되며 출력 디렉터리는 생성되지 않았다.
- 포즈 모델 `5c0a4bf67953e6d2ac43ce15e77dc9d5d354ae18430a47d2c5963a7bc5683e3c`, 사람 검출 모델 `b8585adb6d1352796f6e86337e09c3459b830645a7e7192d9381670bea2facbd`; 두 파일은 이미 로컬에 있다. 이번에는 다운로드·모델 추론·제품 수정 0회다.
- 이것은 **사람/관절 관측 획득기**다. W14에 전달할 메인 몸 track·단독/공동/군무 역할·구간은 후속 캐시 처리에서 생성해야 한다. 기존 55/65의 보조 YOLO 근거와 옛 영상 전용 값은 새 입력에 자동으로 복사하지 않는다. 이 영상의 W13 메인/군무 정답도 아직 없으므로 새 영상 정확도 수치는 없다.
- 기존 W13 영상 결과와 W14 파일은 보존했다. 제품 코드/공통 얼굴 Python 파일은 수정하지 않았다.

## 실행 전 확정할 정확한 범위

사용자의 최초 '실제 ML 전 실행 범위 확정' 지시에 따라 이 **새 원본**에 대해 준비 manifest 그대로 실행해도 되는지 확인한다: 위 SHA 원본 영상 전체 `[0,220.837283초)`, 저장 RTMDet Nano+RTMPose-m CPU 1회, 3,310시점, macOS arm64/Python 3.11.12, 현재 격리 worktree HEAD `47782953228861f4bdbdc135265d067c2a826b0e`와 manifest의 코드 해시, 상한 30분/8GiB/500MiB, 출력 `output/evaluation/p_XdZdg9oGc/rtmpose-m-v1`. 영상/모델 다운로드·얼굴 처리·클립 export·외부 과금은 없다. 실행 완료 후 같은 캐시에서 역할/구간 처리와 새 노트북을 준비하며, 사용자 정답 없는 수치를 정확도로 부르지 않는다.
