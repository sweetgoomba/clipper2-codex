# W13 — ANTIFRAGILE 첫 포즈 획득과 역할 기준선

상태: **승인된 영상 전체의 포즈 추론 1회와 저장 결과의 역할 재생 완료. 정확도 개선·제품 적용 판정 전.** 이 기록은 [실행 준비](10/14-w13-antifragile-runner-preparation.md)의 후속이다.

## 실행 범위와 재현 근거

- 사용자는 준비된 범위에 대해 “이 범위로 실행해”라고 승인했다. [승인 manifest](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-preflight-v1/manifest-approved.json)의 SHA-256은 `80e05131aa7b70a45127ed0d4451098d0e8e43e85c19a7ba0569cd84c1ed1162`이다.
- 원본 SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`, 전체 영상 `[0,220.837283초)`, 13,237프레임, 4프레임 간격 3,310시점을 대상으로 했다. 실행 HEAD는 `47782953228861f4bdbdc135265d067c2a826b0e`; OS macOS arm64, Python 3.11.12, CPU. RTMDet Nano 모델 SHA `b8585adb…facbd`, RTMPose-m SHA `5c0a4bf6…5683e3c`는 승인 manifest에 전체 경로·해시로 고정되어 있다.
- 30분·8GiB·500MiB 상한 내에서 원본 디코딩/모델 처리 **1회**를 완료했다. [실행 요약](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/summary.json): 357.163초, peak RSS 2,047,508,480바이트, 반환 코드 0. [pose.json](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/run-01/pose.json) SHA `ab31eef8c2e9ca92abb5027bb9cf2e665da20942c7a235ead0dbf0b038d372fb`.
- [독립 pose 검사](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/pose-audit.json)는 3,310관측의 원본 프레임·PTS·픽셀 좌표 구조와 W14의 1,104 얼굴 관측 시점 정렬을 확인했다. 사람 상자 관측은 합계 14,039개, 사람 미검출 표본은 220개다. 이 수는 실제 인물 검출 정확도나 멤버 식별 성공률이 아니다.

## 저장 포즈에서 첫 역할 기준선

- 새 추론 없이 약 7.061초에 기존 35번 역할 설정을 RTMPose 단독 포즈에 적용했다. 원본 크기/길이만 새 영상으로 바꾸고, 이전 영상의 YOLO 보조 근거·55/65 후처리·정답 라벨은 넣지 않았다. [역할 요약](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtmpose-only-35-v1/summary.json)과 [W14용 몸 계약](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtmpose-only-35-v1/w14-contract.json)(SHA `18686ec3439cbcb2334ee06295c8e136952385ca86704b11a751ff09ee8533e2`)을 보존했다.
- **구성 선택의 의미:** 35번은 새 원본에서 RTMPose 단독 몸 관측을 빠르게 계약 형식으로 투영하기 위한 독립 재생 기준선이었다. 이전 영상에서 개선한 55/65번의 최신 품질 구성은 아니며, 그 구성에는 새 영상에서 아직 획득하지 않은 YOLO26s 보조 관측과 후속 단계가 있다. 따라서 이 결과를 55/65번의 새 영상 성능이나 제품 후보로 제시하면 안 된다. 구간이 잘게 끊긴 원인을 단지 “오래된 규칙 때문”으로 단정할 수도 없다. 모델 관측·유효 움직임 기준·추적·역할 연결을 따로 확인해야 한다.
- 3,310시점의 임시 역할: 단독 메인 1,551, 공동 메인 16, 군무 550, 판단 보류 1,193. [구조 검사](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtmpose-only-35-v1/structure-audit.json)는 전체 시간에 빈틈 없는 487구간을 확인했지만, **432구간이 1초 미만**이다. 매우 잦은 역할 전환이므로 현재 상태를 앱 클립 기준으로 채택하지 않는다. 1,583개의 선택된 가시 몸에는 bbox가 있었고 원시 track과 유일하게 연결됐다.
- 저장 구간을 추가 집계하면 짧은 432개는 보류 214·단독 171·군무 38·공동 9개이고, 219개는 0.2초 미만이다. 인접 구간의 단독→보류 163회, 보류→단독 161회가 전환의 큰 부분이다. 보류 구간의 시작 사유 224개는 모두 `sequence_observation_break`로 기록됐으며 그중 214개가 1초 미만이다. 이는 **어느 단계에서 흔들림이 드러나는지** 보여줄 뿐, 실제 검출 누락·track 단절·장면 컷 중 무엇이 근본 원인인지는 아직 판명하지 않는다.
- [67번 검토 노트북](http://127.0.0.1:8899/lab/workspaces/auto-Q/tree/notebooks/w13_dance_iteration_lab_67_antifragile_role_review.ipynb)의 셀을 실제 실행해 원본 영상·역할 상자·전체 구간 버튼을 표시했다. 00:03.20 구간 버튼을 눌러 영상 시각과 원본 프레임 192/PTS 192192, 단독 메인 상자가 함께 이동하는 것을 확인했다. 빨간 상자=단독 메인, 주황 상자=공동 메인, 파란 테두리=군무, 표시 없음=판단 보류다. 영상은 독립 복사본이며 원본 SHA와 같다. 열린 66/67번 노트북 파일은 외부에서 다시 쓰지 않았다.

## 해석과 다음 결정

이 영상에는 사용자 W13 메인·군무·구간 정답표가 없다. 따라서 **맞힌 비율, 이전 65번보다 나아진 정도, 모델 교체 효과는 계산하지 않았다.** 원래 21행 정답표는 다른 영상의 것으로 옮겨 쓰지 않는다. 현재의 뚜렷한 문제는 짧은 구간 432개와 판단 보류 1,193시점이다. 다음은 이 저장 포즈만 재사용해 흔들림의 원인을 역할 근거·track 단절·장면 컷으로 분리하고, 동일 입력에서 시간 연결 조건을 소수만 비교하는 것이다. 사람/군무가 실제로 맞는지는 사용자 원본 검토나 별도 라벨이 필요하다.

얼굴·이름 매칭은 W14 소관이다. 이번 실행에서 얼굴 추론·멤버 배정·클립 생성·모델 다운로드·외부 과금은 없었다. 제품 코드, 설치 앱, 기존 W13/W14 결과, 공통 얼굴 파일, Git publishing은 변경하지 않았다.
