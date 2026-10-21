# W14 — 얼굴 확정 근거 회귀 검사

**결정: 참조 사진 8장 추가·AuraFace 전환·시간 이웃 자동 배정을 제품에 적용하지 않는다.** 저장된 얼굴 결과를 다시 계산하는 [평가 코드](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/evaluation/candidate_comparison/face_evidence_regression.py)와 [테스트](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/evaluation/candidate_comparison/test_face_evidence_regression.py)를 격리 W14 Python worktree에 추가했다. [입력 계획·전수 결과·판정](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-evidence-regression-v1/decision.md)은 기존 결과의 해시를 고정하고, 새 ML 호출 없이 사용자 직접 얼굴 정답과 원본 시각 위험 사례를 분리한다.

뉴진스 직접 정답 34얼굴에서 SFace 기존23참조는 정답18/오확정0/보류16, 다른 촬영의 사용자 확인8장 추가는 **19/0/15**다. AuraFace는 **19/0/15 → 20/0/14**다. 두 모델 모두 **보류→정답 2개와 정답→보류 1개**가 있어 단순 총합 증가는 무손실 개선이 아니다. 다른 두 촬영의 멤버 정답23얼굴은 SFace 15/0/8, AuraFace 17/0/6으로 사진 추가 전후 변화가 없다. 등록 외 인물5얼굴은 네 조건 모두 미배정이다. 이 숫자는 이미 개발에 사용한 자료의 재채점이며 독립 정확도 검증이 아니다.

이전 시간 규칙의 위험 구간에서 기존 SFace의 하니 확정 3개는 참조8장 추가 시 모두 보류가 됐다. AuraFace는 같은 세 시점 중 2개를 혜인으로 확정하고 1개를 보류했다. 이 세 얼굴과 주변 전파 대상8얼굴에는 직접 사용자 얼굴 라벨이 없어 정확도 개선·오답으로 채점하지 않는다. 원본 시각 연속성상 안전성 경고로 남긴다. 임베딩 공간/참조 gallery/문턱별 거리 혼합은 금지한다.

**검증:** 테스트를 먼저 실패시킨 뒤 8개 통과. 저장 입력 SHA 확인, 현재 코드 재실행의 결과 바이트 일치, [독립 26항목 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-evidence-regression-v1/audit.json), `py_compile`, Ruff 확인. 결과 19,762바이트, 재실행 약0.029초/프로세스 RSS 약46MB. 전체 pytest suite는 평가 venv에 pytest가 없어 실행되지 않았다. 제품/core/W13 파일·사용자 결과·모델 준비/의존성 변경0.

**다음 gate:** 새 독립 촬영에서 직접 확인된 메인 얼굴과 등록 외/동시 출연, 컷·몸 track 교대의 라벨로 정답 회복/타인 오확정/미매칭을 함께 비교한다. W14는 얼굴 API·평가/fixture, W13은 메인 몸/구간/컷·mapping/crop/제품 adapter를 소유한다. W13의 안정 출력이 오면 계약·소비자 compatibility → 선택 venv/모델 준비 → Mac arm64/Windows x64 설치 검증 → 합의 merge 순서를 따른다. 이번 기록은 W13 새 수락이나 제품 적용 승인이 아니다.
