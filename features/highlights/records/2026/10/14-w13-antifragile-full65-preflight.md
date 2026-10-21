# W13 — ANTIFRAGILE 65B 전체 구성 재시험 준비

상태: **2026-10-14 사용자 승인 후 실행 완료.** 이 문서는 실행 전 고정 범위와 준비 검증의 기록이다. 실제 실행·69번 결과는 [후속 결과](10/14-w13-antifragile-full65-result.md)를 참조한다. [68번 RTM 단독 비교](10/14-w13-antifragile-rtm-only-rules-comparison.md)의 후속이다.

## 사용자 요청과 비교 구성

사용자는 67/68 결과의 메인 박스가 사람을 놓치고 자주 튄다고 보고했다. 군무 정답 확인은 뒤로 미루고, 뉴진스 영상에서 가장 좋았던 65B **전체 구성**을 르세라핌 영상에 적용해 보라고 요청했다. 이전 설명의 중요한 정정: 67은 RTM+35, 68은 RTM만으로 가능한 55/65 일부다. 이번 준비 구성은 **RTMDet Nano+RTMPose-m 메인 관측 + YOLO26s 관절 신뢰도 포함 군무 보조 관측 + 55 움직임 이력 보정 + 65 자세 근거·새 공동 메인 지속 확인**이다. YOLO 관측은 군무 보조이며 RTM이 고른 메인 박스를 직접 대체하지 않으므로, 박스 튐을 자동으로 해결한다고 약속할 수 없다.

## 새 영상 YOLO 추론의 제안 범위

- 원본: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/source.mp4`; SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`; 전체 `[0, 220.83728333333335초)`, 원본 13,237프레임, 4프레임 간격 3,310관측, PTS 기준 `1/60000`·1001씩 증가.
- RTM 기존 저장 pose SHA-256 `ab31eef8c2e9ca92abb5027bb9cf2e665da20942c7a235ead0dbf0b038d372fb`를 재사용. YOLO26s Pose 로컬 가중치 SHA-256 `a083adb42303728ae14c4bd6bd56d80da46f82fb2564dbd6f31dcc92ea321646`; confidence 0.25/IoU 0.7. 모델 다운로드 없음.
- 새 영상의 W13 메인·군무 사람 정답표는 **없음**. 얼굴 참조 이미지나 얼굴 분석도 사용하지 않는다. 실험은 이름이 없는 몸/역할 metadata 비교다.
- 실행기준 Python HEAD `47782953228861f4bdbdc135265d067c2a826b0e` + [준비 manifest](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/p_XdZdg9oGc/yolo26s-preflight-v1/manifest-prepared.json)에 적힌 각 파일 해시. Mac mini M4/macOS arm64, Python 3.11.12, CPU, **1회**, 최대 600초·RSS 8GiB·출력 250MiB. 저장 예정 위치는 같은 W13 worktree의 `output/evaluation/p_XdZdg9oGc/yolo26s-pose-v1/`. 외부 과금·클립 생성·제품 적용 없음.

이 범위에 대한 사용자의 실행 전 확인을 요청했다. 준비 manifest의 상태는 `prepared`이며 승인 기록 없이는 실행기가 추론을 거부한다. 실제 실행과 결과를 완료했다고 표현하지 않는다.

## 이미 검증한 부분

기존 뉴진스 영상의 저장 RTM 자세·YOLO26s **관절 신뢰도 포함** 자세로 65B를 다시 계산하자, 고정된 65B의 역할·선택 박스·구간과 정확히 일치했다. YOLO 최초 일반 pose 파일은 관절 신뢰도를 버리므로 이 재현에 쓸 수 없음을 확인했고, 당시 65B가 사용한 confidence 파일로 보조 근거 전 2,002관측도 정확히 재현했다. 새 수집기는 같은 관절 신뢰도와 원본 PTS를 함께 저장하도록 작성했다. 새 영상 입력 manifest의 비실행 검증과 관련 18개 unittest, Ruff, Python 컴파일 검사는 통과했다.

승인 후에는 새 YOLO pose 1회 → 저장 RTM+YOLO로 55/65A/65B 캐시 재생 → 67/68/전체65B를 같은 시각에서 바꿔 보는 **69번 노트북** 생성 순서다. 이 영상의 역할 정답표가 없으므로 구간 수나 군무 수만으로 정확도 향상을 주장하지 않는다. 실제 박스 튐과 군무 손실을 별도로 보고, 제품·W14 입력 채택은 검토 후 결정한다. 기존 67/68 노트북과 출력, 얼굴 공통 파일, 제품 코드, Git publishing은 보존한다.
