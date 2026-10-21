# W13 — ANTIFRAGILE RTM 단독 최신 규칙 대조

상태: **저장 관측으로 두 규칙 결과를 비교했으나 개선 입증 실패, 제품 미채택.** [67번 첫 결과](10/14-w13-antifragile-first-pose-and-role-result.md)의 후속이다.

## 무엇을 비교했나

같은 ANTIFRAGILE 원본 전체 `[0, 220.837283초)`와 기존 저장 RTMDet Nano+RTMPose-m 포즈 3,310시점을 썼다. 원본 SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`, pose SHA-256 `ab31eef8c2e9ca92abb5027bb9cf2e665da20942c7a235ead0dbf0b038d372fb`이다. [승인 입력 manifest](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-preflight-v1/manifest-approved.json)에 고정된 입력과 OS/기기/모델 해시를 그대로 재사용했다.

- **67 기준:** 같은 포즈에 이전 35번 역할 규칙 적용.
- **68 비교안:** 67 결과를 출발점으로 55번의 움직임 이력 재설정·단독 인물 선택 보호와 65번의 자세 일치 근거·새 공동 메인 0.2초 지속 확인 중 **RTM 포즈만으로 가능한 부분**을 적용. 별도 YOLO 결과는 사용하지 않았다.

과거 영상의 최종 **65B 전체는 RTM 포즈 + YOLO26s 보조 군무 관측**을 사용했다. 따라서 이번 비교안은 동일한 모델 조합도, 동일한 65B 결과의 새 영상 재현도 아니다. 얼굴·이름 매칭은 W14 작업이다.

## 결과

| 지표 | 67 기준 | 68 RTM 비교안 |
|---|---:|---:|
| 역할 구간 | 487 | 475 |
| 1초 미만 역할 구간 | 432 | 418 |
| 단독 메인 시점 | 1,551 | 1,571 |
| 공동 메인 시점 | 16 | 26 |
| 군무 시점 | 550 | 489 |
| 판단 보류 시점 | 1,193 | 1,224 |

역할이 달라진 시점은 69개, 화면에 선택된 몸이 달라진 시점은 59개다. 두 집합을 합치면 90시점, 시간상 이어진 범위 18개다. 구간이 조금 덜 쪼개졌지만 군무 61시점이 줄고 보류 31시점이 늘었다. 이 영상에는 W13 역할·구간 사람 정답표가 없으므로 **어느 변경이 맞는지와 정확도 향상 여부는 알 수 없다.** 군무 수치 감소 자체를 악화로 확정하지도 않는다.

[68번 노트북](http://127.0.0.1:8899/lab/workspaces/auto-q/tree/notebooks/w13_dance_iteration_lab_68_antifragile_rtm_only_comparison.ipynb)에서 같은 영상 시각의 67 기준/비교안을 버튼으로 바꾸고 18개 차이 범위로 이동할 수 있다. 00:25.89 버튼 이동과 두 조건 전환을 실제 UI에서 확인했다. 빨간 상자는 단독, 주황 상자는 공동, 파란 영상 테두리는 군무, 표시 없음은 판단 보류다. 이 표시는 멤버 이름 판정이 아니다.

## 실행·검증과 다음 판단

[비교 계산](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtm-compatible-55-65-v1/summary.json)은 저장 포즈 재생 1회, 17.522초/peak RSS 707,608,576바이트다. 새 모델 추론·얼굴 추론·클립 export는 각 0회. [비교 수치](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtm-compatible-55-65-v1/comparison.json)과 최종 [역할 계약](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/rtmpose-m-v1/roles-rtm-compatible-55-65-v1/65b_rtm_only-contract.json)(SHA-256 `135d476dc0c3ba8fb962cd3ca2843f1f78ddc01494a80aedde989011ebd39f13`)을 보존했다. 재생은 source/PTS 동일성을 확인하고 입력 불일치 시 거부한다.

저장 관측 진단에서 판단 보류 시작 224곳 중 203곳에는 사람이 검출돼 있었다. `sequence_observation_break`가 기록된 1,134시점 중 검출 후 사람이 없는 시점은 263개이고, 나머지 871개에는 사람이 있지만 유효 움직임 관측 비율이 0.6 미만이다. 이는 **보류의 분기 위치**를 가리키며 포즈 검출/추적/규칙 가운데 어느 쪽이 근본 원인인지 확정하지 않는다. 단일 보류 연결 조건은 9곳을 복구했지만 전체 짧은 보류를 없애지 못했다.

다음은 68번의 18개 변경 범위에서 실제 군무·메인 손실을 원본으로 확인하고, 유효 움직임 부족을 만드는 포즈 관절·트랙 연결·컷 경계를 분리해 검증한다. 이 검토 전에는 비교안을 제품이나 W14의 확정 역할 입력으로 교체하지 않는다. W14가 사용하는 기존 고정 몸 계약은 그대로 보존한다. 제품 코드·앱·공통 얼굴 파일·기존 노트북·기존 결과·Git publishing은 변경하지 않았다.
