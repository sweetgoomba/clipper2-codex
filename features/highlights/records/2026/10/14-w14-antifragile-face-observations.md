# 2026-10-14 W14 지정 무대의 얼굴 후보 관측

상태: **전체 영상의 고정 격자 얼굴 검출 완료. 메인 인물 연결·멤버 매칭·정확도 평가는 아직 하지 않음.** 사용자 지정 [M2 ANTIFRAGILE 무대](https://www.youtube.com/watch?v=p_XdZdg9oGc)의 [고정 원본](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/input-manifest.json) SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`만 사용했다. 이전 릴레이 구간·옛 W13 메인/track은 사용하지 않았다.

## 실행 범위와 실제 결과

- [사전 고정 실행 계획](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-observations-v2/plan.json): 13,237 원본 프레임 중 `0, 12, …, 13236`의 1,104시점. 원본 영상 PTS를 전수 확인했으며 `frame_index × 1001`, time base `1/60000`이다. W13의 이전 `4프레임마다` 격자와 인덱스가 겹치지만, W13이 새 영상에서 같은 격자를 쓴다는 보장은 아직 없다. 모든 유효 검출을 보존하고 얼굴 품질·이름·메인 역할로 미리 거르지 않았다.
- 모델은 기존 OpenCV YuNet `face_detection_yunet_2023mar.onnx`, SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`. 원본 1920×1080 픽셀, score 0.6, NMS 0.3, topK 5000. Python 3.11.14, macOS 27 arm64, OpenCV 4.13.0.92, NumPy 2.4.4, psutil 7.2.2, CPU 1 OpenCV thread. 코드 SHA와 모델·소스 SHA는 계획에 있다. 새 모델 다운로드·의존성 설치 없음.
- 사전 상한: 1,104회 검출, 600초, RSS 4GiB, 출력 50MiB. [실행 영수증](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-observations-v2/supervisor.json): 검출 1,104회, 작업자 136.545초, 감독 포함 137.193초, 측정 피크 RSS 370,671,616바이트, 상한 종료 없음. [관측 결과](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-observations-v2/result.json) SHA-256 `93967024e0d79b0fa8276aa59cce22dc3a1a26878db3234ab2a63dad64949544`.
- [독립 검산](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-observations-v2/audit.json): 1,104시점에서 **얼굴 검출 후보 3,450개**, 유효 후보 0인 시점 86개, 동시에 2개 이상 후보인 시점 850개, 5개 이상인 시점 341개. bbox 짧은 변 중앙값 69px, 40px 미만 후보 554개. 행 형태·유한값·score·원본 bbox 경계·PTS·호출 수·plan/result/영수증 해시를 확인했다. 이 개수는 실제 얼굴 3,450개가 맞게 검출됐거나 인물 식별에 성공했다는 뜻이 아니다.
- [7시점 좌표 원본 대조](../../../../../../.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-observations-v2/qa-contact.jpg): 먼 5인 군무의 작은 얼굴, 가까운 단독 얼굴, 한 화면의 다중 얼굴을 표시했다. 약 112초에는 손 주변을 얼굴로 잡은 후보도 보여 **오검출 가능성을 실제로 확인**했다. QA 7장은 편의 표본이며 전수 정확도 정답은 아니다.

## 첫 실행 실패와 수정

첫 `face-observations-v1` 계획은 사전 고정 후 감독 프로세스가 `/bin/ps`로 RSS를 읽으려다 이 작업 환경의 `Operation not permitted`를 받아 중단됐다. `worker.log`는 비어 있고 result 파일은 없다. `/bin/ps` 자체가 같은 권한 오류로 재현됐고, 이미 설치된 psutil이 자식 PID의 RSS를 읽을 수 있음을 별도로 확인했다. 자식 RSS 확인 테스트를 실패시킨 뒤 `psutil`로 감시 방식을 바꾸고, 코드/런타임 해시를 새로 고정한 **v2** 계획을 만들어 실행했다. v1 파일은 덮어쓰지 않았다. 관련 `unittest` 4개, Ruff, compileall 통과. 제품 코드·W13 코드 변경 없음.

## 해석과 다음 연결

이 관측에는 **멤버 이름, 참조 비교 점수, 얼굴 embedding, W13 메인 몸, 안무 구간, 사용자 정답이 없다.** 따라서 현재 모델 매칭률·잘못된 멤버 확정률 또는 SFace/Aura 우열을 계산할 수 없다. 86개 무검출 시점이 실제 얼굴 부재인지 검출 누락인지도 정답 없이 구별하지 않는다.

다음에는 W13이 **같은 source SHA**로 산출한 메인 bbox/track·역할·구간/교대 경계를 받아 프레임 인덱스/PTS와 영상 좌표계를 검사한다. 같은 시점의 여러 얼굴 중 메인 몸에 연결할 얼굴을 고르되, 겹치거나 불확실하면 무리하게 하나를 확정하지 않는다. 그 뒤 같은 연결 얼굴과 21장 참조 사진에 SFace 및 후보별 올바른 전처리와 각자의 기준을 적용한다. 얼굴 검출 실패·몸↔얼굴 연결 실패·인식 보류·잘못된 확정을 따로 기록한다. 기존 사용자의 릴레이 18구간 답변 요청은 철회 상태를 유지한다.
