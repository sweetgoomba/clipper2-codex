# W14 — 이웃 얼굴 보류 해제 규칙의 다른 촬영 자료 반례 검사

**결정: 이웃 확정 얼굴 두 장으로 보류 얼굴을 자동 배정하는 규칙은 제품에 적용하지 않는다.** 르세라핌 ANTIFRAGILE의 S02·S06에서 보인 탐색적 회복을 다른 촬영 뉴진스 영상의 저장 SFace 결과로 대조했다. 사전에 규칙·전체 입력·34개 직접 얼굴 라벨·7개 시각적 몸 교대 자료와 자원 상한을 [잠갔다](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/temporal-cross-video-stress-v1/plan.json). 이 뉴진스 영상은 앞서 여러 정책의 개발에 사용했으므로 **새 독립 holdout이 아니다.**

기존 35 participant scope/37 몸 run/353 얼굴 관측 전체에서 기존 확정은 그대로 두고, 보류 얼굴에만 같은 run·동일 모델/참조/정책 공간·앞뒤 1초·서로 다른 확정 프레임 두 개·반대 이름 없음·대상 원시 1위 일치를 적용했다. 정확한 사용자 얼굴 라벨 34지점에서는 SFace 정답18/오확정0/보류16 → 탐색 후보 정답23/오확정0/보류11. 새 이름 24행 중 직접 라벨이 있는 것은 5행뿐이다. **34지점에서 신규 오확정 0이라는 수치로 안전하다고 결론내릴 수 없다.**

구체적 반례는 59.46–63.06초 `s0043-p0-r1`이다. 59.526–60.594초의 보류 얼굴 8개에 **하니** 후보가 새로 생겼다. 58.925·61.528·61.662·61.862초에 사용자가 직접 지정한 얼굴은 **혜인**이다. 같은 4K 원본 SHA `74e4769a…d4013`의 7개 검토 프레임에서 보라색 의상·긴 머리·헤드셋 출연자가 계속 이어지고 후보 얼굴 crop도 그 출연자로 보인다. 8개 프레임마다 사용자가 신원을 라벨링한 것은 아니므로 **채점된 오답 8개라고 보고하지 않는다.** 다만 확정된 SFace의 하니 표본 3개가 같은 run 안에서 보류 얼굴을 하니로 끌어간다는 안전성 반례 가능성이 강하다. 7개 옛 시각적 몸 track 교대 자료에서도 4개 경로에 합계 18개 새 후보가 생겼지만, 신원 GT가 없어 그 자체를 오류 수로 세지 않았다.

[전체 결과·원본 7장·검토·감사·다음 조건](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/temporal-cross-video-stress-v1/decision.md). 평가 코드 unit 5개 통과, 저장 353행·34라벨·7교대의 별도 재계산과 원본/검토 프레임 SHA 감사 통과. 새로운 ML 0, 원본에서 JPEG 7장 디코드 6.88초/946,783바이트, 제품·공통 얼굴 core·W13 소비자·참조 cache/threshold 변경 0. 기존 YuNet+SFace 제품 경로와 보류 상태를 유지한다.

## 후속 원인 분리: 잘못된 확정 근거가 먼저 있었다

저장된 [시간 규칙 입력](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/sequence-score-v1/input.json)을 다시 조사했다. 이 입력은 4K 영상 SHA `74e4769a…d4013`, SFace 가중치 SHA `0ba9fbfa…84087c34e79`, 원래 등록 참조 23장 gallery 지문 `77beda6b…e275`와 고정 거리·후보차이 기준을 사용한다. 위험 run의 `f3572`(59.593초), `f3576`(59.660초), `f3588`(59.860초)은 얼굴 연결 상태가 모두 `confirmed`이고 **시간 규칙을 적용하기 전부터** SFace가 하니로 확정했다. 하니와 2위의 cosine distance 차이는 각각 약 `0.138`, `0.148`, `0.137`로 당시 최소차이 `0.1353`을 근소하게 넘는다. `f3568/f3580/f3584/f3592/f3612/f3624/f3628/f3632`은 기존 `ambiguous`였고 이 세 확정을 근거로 하니 후보가 되었다. 직접 사용자 라벨이 있는 `f3688/f3696/f3708`은 혜인이다. 따라서 **시간 투표가 새로운 오인식 근거를 만든 것이 아니라, 기존 확정의 신뢰도를 검사하지 못하고 이름을 전파한 것**은 저장 점수만으로 확인된다.

별도 [몸·얼굴 위치 진단](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-57-63-diagnosis-v1/geometry-and-saved-matches.json)의 해당 시점은 모두 같은 보라색 출연자 얼굴을 메인 몸에 연결한 것으로 기록돼 있다. 다만 몸 track ID는 59.459초에 68→69로 바뀌고, 위치 진단은 1920×1012 영상의 저장 몸/얼굴 좌표를 사용했다. `confirmed`는 알고리즘의 연결 상태이지 사람 신원 정답이 아니다. 원본 7프레임의 시각적 연속성이 연결 오류보다 **얼굴 비교/참조 분리 실패**를 더 강하게 시사하지만, 후보 여덟 얼굴의 직접 사용자 신원 라벨이 없어 최종 오류 수로 확정할 수 없다.

앞선 [실제 4K 비교](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-57-63-diagnosis-v1/native-source-comparison-v1/manifest.json)는 다른 gallery 지문(SFace `2d8af20c…`, Aura `2c178335…`)을 쓴 별도 실험이다. 그 실험의 `f3588`은 4K SFace에서 하니 `0.585` 대 혜인 `0.586`으로 **거절**됐고, 직접 혜인 라벨 `f3688/f3696/f3708`은 Aura에서 혜인으로 확정됐다. 다른 gallery·모델의 거리를 위 `77beda6b…` 점수에 섞어 새 문턱을 정할 수 없다. 이 비교는 입력/참조/모델 조합에 따라 판정이 바뀐다는 근거이며, Aura의 전체 제품 우위나 단순한 해상도 개선의 입증은 아니다.

동일한 353관측을 담은 [기존 참조 비교 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-append-cross-video-v1/results.json)에서는 Aura가 위험한 `f3572/f3576/f3588` 세 얼굴을 모두 후보차이 부족으로 거절하고, 직접 혜인 라벨인 `f3688/f3696/f3708`은 혜인으로 확정했다. 이는 **이 사례에서 모델별 얼굴 비교가 다르다**는 근거다. SFace와 Aura의 embedding·gallery 지문·문턱은 서로 달라 거리값을 합산하지 않는다. 앞서 다른 확인 얼굴에서 모델 반대만으로 보류시키는 정책은 정답도 잃어 [미채택](../10/14-w14-confirmed-main-errors-and-opposition-result.md)했으므로, 이 한 사례를 근거로 Aura 교체나 교차모델 veto를 제품에 넣지 않는다.

같은 비교 결과에는 **SFace 모델·영상 얼굴·문턱을 고정하고 다른 촬영에서 사용자가 확인한 참조 8장을 보탠 조건**도 있다. 이때 세 하니 확정이 모두 `ambiguous`로 바뀌었다. 후보차이는 `0.138/0.148/0.137`에서 `0.130/0.119/0.111`로 내려갔고, 기준 `0.1353`보다 작아졌다. 즉 이 사례의 **참조 gallery 구성 민감도는 한 요인만 바꾼 저장 결과로 확인**된다. 그러나 세 얼굴의 1위는 여전히 하니이며, 다른 얼굴의 회귀도 기존 비교에 있으므로 참조 8장 추가 자체를 제품 해결책으로 채택할 수 없다.

**다음 수정 위치:** 보류 얼굴을 이웃 확정 이름으로 자동 채우는 변경은 중단한다. 먼저 각 확정 근거와 메인 얼굴 연결·실제 컷/몸 교대·참조 gallery 출처를 함께 보존하는 회귀 입력을 W14 평가 계약으로 묶는다. W13이 안정된 메인/컷/교대 출력을 제공하면 같은 고정 입력으로 `오확정`, `정답 회복`, `미매칭`을 모두 세고, 직접 라벨이 없는 얼굴은 채점에서 분리한다. 이 결과가 나오기 전에는 새 문턱, gallery 교체, Aura 제품 전환을 하지 않는다.

**남은 입력:** 다른 촬영에서 메인 몸↔얼굴·실제 컷/교대·등록 외 인물의 직접 라벨, W13의 안정된 메인/구간 출력, 양 OS 설치 검증이다. 혜인 앵커와 중간 8개 하니 후보는 미래 규칙의 필수 회귀 사례로 보존한다. 컷·몸 경로 ID와 얼굴 확정을 독립적인 정답으로 혼동하지 않으며, W14 공통 얼굴 API/평가 → W13 Dance adapter/main/mapping/crop compatibility → 병합 순서를 유지한다. 이번 결과를 W13의 적용 승인이나 클립 정확도로 해석하지 않는다.
