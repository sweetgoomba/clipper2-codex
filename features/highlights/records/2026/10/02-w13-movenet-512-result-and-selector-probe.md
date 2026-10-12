# W13 동일 영상 MoveNet 512 결과와 메인 선택 탐색 — 2026-10-02

## 사용자에게 보여줄 결론

사용자가 같은 원본·같은 로컬 MoveNet weight의 **입력 512 평가를 승인**했다(“몇 회든 상관없이 진행해도 돼”). [잠근 manifest](02-w13-movenet-512-manifest.yaml)의 **1회만** 실행했다. 더 큰 입력은 원본 표본의 사람 검출을 늘렸지만 **메인 댄서를 더 잘 고르지 못했다**. 512만 바꾼 새 앱 클립은 만들지 않았다. 저장 자세에 점수 규칙을 얹은 후속 탐색도 파랑 리드 P4를 지속적으로 놓치거나 화면 선택을 자주 튀게 해 **제품 채택 근거가 없다**. 기존 보수적 앱 비교본과 제품 기본 모델은 유지한다.

## 실제 실행 범위와 결과

원본은 이미 다운로드된 `yFTAYXDTjqI` 전체 0–133.654059초, SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`. MoveNet MultiPose Lightning TF2 v1은 기존 로컬 tree SHA-256 `ea71312368f39053ed7b9b2e4fac3bcecd94c667f679830a0a999b31ccaf705c`, Apache-2.0 표시 weight다. Mac mini M4 CPU, 분석 간격 원본 4프레임, 입력 512×512, 참조 이미지·얼굴 추론·clip export 0. 코드 fingerprint `541065292178c11b4f40445ad9d3f1c654d3984ff45cdcdc0c62c938301f7cf0`. 실행 상한 1회/600초/RSS 12,288MiB/metadata 250MiB. 실제 wall **96.365초**, 최고 RSS **1,104,887,808 bytes**, 출력 폴더 약 **9.1MiB**. 저장 pose 2,002 분석 프레임 SHA-256 `369e2fea3f04bee0a1158aa47d7988bb7f9a4b3cd95a9fe4e12eb5fd61a908d0`; [summary JSON](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-512-v1/summary.json) SHA-256 `77452ec7e4979507db8bd8b682246c4131b09b4b8811d183498b3096c0bac700`. Manifest는 `completed_scoped_metadata_run`으로 닫혀 같은 실행기가 재실행을 거절한다. 새 다운로드·과금·Build5는 없었다.

| 같은 원본의 잠긴 제한 표본 | 기존 256 | 512만 변경 |
| --- | ---: | ---: |
| 원본 45명 사람 bbox IoU≥0.30 | 33/45 | **45/45** |
| 기존 단독 메인 18장 선택 IoU≥0.30 | 6/18 | **6/18** |
| 10/2 추가 단독 메인 17장 | 7/17 | **6/17** |
| 위 추가 표본 중 과거 동일 인덱스 제외 14장 | 6/14 | **5/14** |
| 원본 4장 메인 앵커 | 1/4 | **1/4** |
| 원본 4장 그룹 표본의 그룹 flag | 4/4 | **4/4** |
| 기존 단독 18장 중 그룹 flag 오검출 | 15/18 | **5/18** |
| 추가 단독 17장 중 그룹 flag 오검출 | 14/17 | **5/17** |
| 자세 metadata의 raw group 구간 총합* | 84.952초 | **43.844초** |

\* raw group 합계는 최종 MP4 그룹 길이나 실제 그룹 GT가 아니다. [512 기초 점수 JSON](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-512-v1/score-v1.json) SHA-256 `b3205462bc909b2485acad7d502ba25469019035abcde9ace9fa50d65accaa6b`. 원본 45명 표본이 모두 검출된다고 해서 누락 없는 전체 영상 검출을 뜻하지 않는다. 메인 선정은 실행 전 잠근 최소 조건인 **기존 18장과 추가 비중복 14장 모두 개선**을 충족하지 못했다. 따라서 512 단독 제품 교체는 기각한다.

## 추가 메인 점수 탐색: 채택 보류

512 저장 pose에서 중앙 점수 계수를 기존 0.45에서 0.20으로 낮추고 나머지 정적 항을 유지하면 앞선 단독 표본의 일치는 기존 18장 11/18, 추가 17장 12/17, 별도 15장 10/15가 되었다. 하지만 그룹 flag까지 이 점수로 계산하면 원본 솔로 표본에서도 대부분 그룹이 된다. 그룹 계산을 기존 0.45 점수 경로로 고정한 상태에서, bbox 정규화 관절의 20원본프레임 사이 중앙값 움직임을 `0.80×` 보태는 탐색 후보를 과거 세 표본에서 골랐다(각각 **14/18, 14/17, 11/15**). 이는 같은 원본의 개발 점수이며 독립 검증이 아니다.

후보 점수 확인 전에 별도 원본 프레임 28장을 [계획](02-w13-center-weight-source-reserve-plan.json)하고 source-only [몸통 점 라벨](02-w13-center-weight-source-reserve-labels.json)을 고정했다. 계획 SHA-256 `65a6560f9255a52a5e6703c3f74dfa502277ec70e0670f84b2d2ff6317d6fddd`, 라벨 SHA-256 `42369380a9d37cf787b70155535313041dd85cdee868c127cb7f820a7c1bb5fe`. 이후 [후보·판정 gate](02-w13-motion-assisted-reserve-check-plan.json)를 기록하고 20개 명확 단독 몸통 점의 선택 bbox 포함 여부를 비교했다. 이 점 표기는 원본 1/3 크기 contact sheet에서 수작업했으며, 사람 bbox IoU 점수와 분모·판정이 다르다. 같은 영상·가까운 프레임·앞선 실패를 아는 한 검토자의 탐색 결과다.

| 예약 원본 20장 | 512 현행 | 중앙 0.20만 | 중앙 0.20 + 움직임 0.80 |
| --- | ---: | ---: | ---: |
| 전체 몸통 점 포함 | 8/20 | 11/20 | **15/20** |
| P1 초록 | 3/4 | 3/4 | 3/4 |
| P2 노랑 | 0/4 | 2/4 | 4/4 |
| P3 빨강 | 3/4 | 3/4 | 4/4 |
| **P4 파랑** | **0/4** | **0/4** | **0/4** |
| P5 연보라 | 2/4 | 3/4 | 4/4 |

후보는 사전 gate인 **P4 최소 2/4**를 실패했다. 그룹 판정은 기존 512 경로와 전체 2,002프레임 불일치 0으로 의도대로 보존했지만, 솔로 20장 중 6장에 그룹 flag가 여전히 켜졌다. 또한 인접 선택 bbox IoU<0.1의 큰 점프는 512 현행 16→후보 **28**, raw main 구간 수는 29→**41**이다. [후보 행별 JSON](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-512-v1/score-motion-assisted-reserve-v1.json) SHA-256 `9aaa6c53ed9754aba49cdaeb15671c33a7656e50097d1ebe22eb3db1ad37ca61`. 예약 점수를 본 **뒤** 움직임 계수를 2.0까지 높이면 P4가 2/4로 올라가지만 큰 점프가 **66**으로 늘었다. 이는 사후 튜닝이며 채택하지 않는다. 원본 fps 대신 분석 fps로 전환 streak를 줄여도 P4는 0/4이고 점프는 49여서 채택하지 않는다.

## 다음 판단

이 영상의 핵심 실패는 이제 **사람 미검출만의 문제가 아니다**. 512에서 45/45와 예약 20/20 검출에도 P4가 0/4이고, P2도 기존 단일 선택에서 0/4였다. 점수만 강하게 바꾸면 보존성과 시간 연속성이 나빠진다. 다음은 별도 허가된 상업 이용 가능 다인 pose 후보를 한 번에 하나씩 비교하거나, 512 pose의 **전체 사람 궤적별 안정적인 메인 선택**을 원본 전환 라벨과 함께 설계·검증하는 것이다. 기존 YOLO weight는 폐쇄형 SaaS 제품 후보로 재도입하지 않는다. 현재 제품·앱 프로젝트·W14 공통 얼굴 코드·참조 매핑·crop에는 이 탐색 결과를 적용하지 않았다. 사용자에게 기존보다 좋아진 새 완료 앱 결과라고 표현할 수 없다.
