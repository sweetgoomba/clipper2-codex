# W14 기존 YuNet 점수·얼굴 크기 조건의 교차 검증 — 2026-10-02

## 가설과 입력 잠금

사용자 37분 영상에서 음식 소스를 큰 얼굴로 오검출한 사례의 YuNet score는 `0.685`, 상자 짧은 변은 547px이다. **큰 상자이면서 낮은 검출 점수**만 제외하면 비얼굴을 줄이고 작은 배경·단역 얼굴은 유지할 수 있다는 한 가지 가설을 검증했다. 이는 점수 조건을 제품에 넣기 위한 승인이나 기존 결과 수정이 아니다. 앞선 전역 0.82/0.85 문턱, SFace 전역 완화, ArcFace 교체, 동일 shot track 추가 연결이 각자 품질 gate에 실패했으므로 새 제품 수정은 보류한 상태다.

[실행 계획](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/plan.json) SHA-256 `571842e30b5c8067d9318947caa6abcce8e4ff9b43b7d9d5c7f5a92721c3bda1`에 다음을 실행 전 고정했다.

- 기존 사용자 원본 SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`, 1280×720/30fps; 기존 5fps manifest SHA-256 `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`. 새 다운로드·완료 카드·MP4 없음.
- 기존 YuNet SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`, 0.60/NMS0.3/top-k5000. **검출기만** 재실행하고 SFace embedding/그룹을 재계산하지 않았다. Mac CPU/OpenCV4.13.
- 이미 원본 우선 고정된 개발 90개 정수 초 프레임, 명확 얼굴 104셀과 사람 없는 초의 검출 상자 6개, 그리고 별도 원본 우선 확인한 음식 화면 1810.8초 1프레임을 개발에 넣었다. 개발 GT SHA `ea8f89480dd71d73b05495269d40e00573921b0f35bbdbb7040986370585fd07`; 음식 GT SHA `31c39be4cbfef64619da07276db9fcf4bd9a8cfc7bf42c3a4bc2042d904b677c`.
- 이전에 별도 원본 라벨로 고정했지만 이미 다른 규칙 평가에 사용된 **재사용 검증** 60개 정수 초 프레임, 명확 얼굴 63셀·수동 확인 비얼굴 5개. GT SHA `073605988de39c95f75655da0405ebc34ec435862399fff52661c470b9866f97`. 이 검증을 새 블라인드 홀드아웃으로 부르지 않는다.
- 후보 9개를 `상자 짧은 변 ≥160/300/500px` × `score <0.70/0.75/0.80`로 사전 고정했다. 개발에서 **명확 얼굴 손실 0 우선→확실한 비얼굴 제거 최대**로 단일 조건을 고정한 뒤 재사용 검증에 적용한다. 재사용 검증도 명확 얼굴 손실 0과 비얼굴 제거 개선이 필수다. 실행당 최대 100프레임/180초/RSS2GiB/출력10MiB, 검출 상자 30개/프레임이다. 출력은 W14 격리 평가 폴더다.

## 실행·채점

[검출 runner](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/run_detector_scores.py) SHA-256 `d2b8902aa37679cc54ed1eff5e934fbbc1997eda01c023c012ff8a45b8ab80d4`는 원본/GT/모델/manifest/자기 코드 SHA를 확인했고 두 단계 dry run이 통과했다. 실제 [개발 실행](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/development-run-report.json): 91프레임/121검출, 2.501초, 최대 RSS224,002,048B, 출력28,370B. [재사용 검증 실행](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/holdout-run-report.json): 60프레임/87검출, 1.727초, 최대 RSS226,557,952B, 출력19,952B. 총 151프레임/208검출, 기존 검출기 호출 2회다. H.264 decoder 경고 `mmco: unref short failure`가 출력됐지만 해당 프레임 읽기·저장 관측 상자 대응은 완료됐다.

[채점 코드](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/score_locked_grids.py)는 현재 검출 상자를 기존 저장 관측과 IoU≥0.95로 대응했고 모든 167개 명확 얼굴 셀이 대응됐다. 후보 적용 전후의 **검출 유지/제거만** 계산했다. 그룹 pairwise·B-cubed 또는 전체 인물 interval 결과를 계산한 실험이 아니다.

| 구간 | 고정 후보: 짧은 변 ≥160px이고 score <0.80 제거 | 판정 |
| --- | --- | --- |
| 개발 91프레임 | 명확 얼굴 **104/104 유지**, 확실한 비얼굴 **2/7 제거**(음식 화면 1 포함) | 개발 기준으로 조건 고정 |
| 재사용 검증 60프레임 | 명확 얼굴 **62/63 유지**, 확실한 비얼굴 **2/5 제거** | **실제 얼굴 1개 손실로 gate 실패** |

[개발 점수](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/development-grid-score.json) SHA-256 `9ed203a2950c1d2d3d478da8bb3c5d0c76c1e9c7b34fe210b495257b47e1f285`에서 9개 조건 중 개발 얼굴 손실 0인 규칙을 [별도 고정](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/development-choice.json) SHA-256 `5e87b2d639d4cfa4b1e8ae4d3cb84406078b9c140641a09a1bebe50b3ea9b297`한 뒤 검증했다. [검증 점수](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-large-low-score-audit/holdout-grid-score.json) SHA-256 `cc6e85fb75fade35e62c6ff86dc95772b01cf22a18fa477222978ecafe07ab10`의 손실은 `I1_B@371` 실제 얼굴: 상자 짧은 변 **374px**, score **0.704**다. 앞선 0.82 전역 조건에서 놓친 370초 실제 얼굴도 짧은 변318px/score0.819로 확인됐다. 음식 오검출 score0.685와 손실 실제 얼굴 score0.704의 차이는 약 **0.019**뿐이다. 검증을 본 뒤 0.70 등 다른 격자점으로 바꾸는 것은 사전 고정 선택이 아니므로 제품 채택 근거가 아니다.

## 결정과 다음 범위

**후보 기각.** 기존 YuNet 0.60/Person 묶기0.55, 모든 검출 그룹 기본 표시, 불확실 그룹 확인 필요, 대표 이미지 사용자 교체, 기존 완료 프로젝트·수정 overlay는 그대로다. 앱 코드·모델·공통 API·W13 Dance adapter와 MP4/ZIP을 변경하지 않았다. 이전 공식 ArcFace도 다른 방송 영상의 오합침/과분리 gate에 실패했으므로 단일 score·크기·landmark 또는 embedding 문턱을 또 조정해 제품에 넣지 않는다.

이번 라벨은 1초 얼굴 셀과 일부 확실한 비얼굴 상자이며 연속 등장/배경 단역 전체 recall, 모든 오검출률, false merge/split 변화, 대표 품질을 측정하지 않는다. 이미 봤던 검증 창 재사용이라 **새 독립 성능 추정값이 아니다**. 다음 실질적 개선에는 source-first 연속 인물/장면 GT와 얼굴 외 증거 또는 더 신뢰할 수 있는 검출 경로의 **별도 설계·범위**가 필요하다. 새 모델 다운로드/유료 API/Build5는 이번 승인에 포함되지 않으며, 기존 모델 반복 추론 승인은 유지한다. W13에는 공통 detector score를 신뢰도/ID로 직접 사용하지 말고 기존 main/ROI/mapping/crop 소비 계약과 별도 검증을 유지하라고 인계한다.
