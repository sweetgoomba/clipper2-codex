# W14 원본 우선 홀드아웃·검출 기준 진단

2026-10-01 KST. **결론: 품질 불합격 유지. 제품 기본 설정·완료 프로젝트·사용자 수정은 변경하지 않았다.** 사용자는 기존 얼굴 모델의 후속 추론 횟수를 제한 없이 승인했다. 새 모델 다운로드, 외부 유료 API, Build5, 기존 프로젝트 덮어쓰기는 실행하지 않았다.

## 고정 입력과 평가 순서

- 원본: `/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_nestjs/.clipper_data/sources/youtube/0KQDhi7ddrk/source.mp4`; SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`, 실제 1280×720/30 fps/약 2239초. 재다운로드 없음.
- 기존 별도 완료 결과: `w14-5fps-1790848488264`의 manifest SHA-256 `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`, YuNet/SFace weight SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` / `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`. 기존 config SHA-256 `c4c4ce232d3ec490e2595bc48fbb39571b6bf45456ddfe4528867328e2c47097`. macOS 27 arm64, OpenCV 4.13 CPU.
- 먼저 기존 평가와 30초 이상 떨어진 `[985,1015)`, `[1526,1556)`, `[1623,1653)`초를 원본 SHA 기반 고정 난수로 선정했다. 모델 overlay 열람 전 원본의 정수 초 프레임만 보고 익명 인물/배경/동시 출연·판정 불가를 기록한 [90초 잠금 GT](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/source-grid-gt.json)의 SHA-256은 `ea8f89480dd71d73b05495269d40e00573921b0f35bbdbb7040986370585fd07`이다. 확실한 얼굴 104시점, 인물 없는 정수 초 프레임 27개, 얼굴/동일성 불확실 인물 시점 10개다. 여러 얼굴이 한 프레임에 함께 있고 배경 인물도 포함된다. 이는 **1초 간격의 희소 라벨**이며 연속 등장 interval GT가 아니다.
- 이후 0.82 설정을 고른 개발 표본과 분리하려고 SHA 난수 seed를 달리해 `[359,379)`, `[1843,1863)`, `[1949,1969)`초 60초를 별도로 선택했다. 기존 결과·후보 overlay를 열기 **전에** [독립 창 잠금 GT](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/independent-source-grid-gt.json) SHA-256 `073605988de39c95f75655da0405ebc34ec435862399fff52661c470b9866f97`로 확실한 얼굴 63시점과 작은/등진 얼굴 불확실 시점을 기록했다. 다른 원본 영상이 아니라 **같은 방송 영상의 미열람 구간**이다.

## 실제 검증

| 구간·설정 | 확실한 얼굴 대응 | 확인된 사람 아닌 관측 | 라벨된 오합침 | 판정 |
| --- | ---: | ---: | --- | --- |
| 개발 90초, 기존 YuNet 0.60 | 104/104 | 정수 초 12개 | 세 창에서 0 | 이미 저장된 결과. 그룹 과분리는 W1/W2에서 각각 두 인물에게 남음 |
| 같은 90초, YuNet 0.85 | 103/104 | 1개 | 0 | **사전 gate 실패**: 1001초 실제 얼굴 누락 |
| 같은 90초, YuNet 0.82 | 104/104 | 3개 | 0 | 개발 gate 통과. 이 라벨을 보고 설정한 값이므로 독립 성능 증거 아님 |
| 독립 60초, 기존 YuNet 0.60 | 63/63 | 확실한 비얼굴 5개 | I1의 서로 다른 두 남성 같은 그룹 | 기존 결과도 불합격 |
| 독립 60초, YuNet 0.82 | **61/63** | 위 5개 중 0개 남음 | 같은 두 남성 오합침 지속 | **사전 gate 실패**: 370·371초 실제 얼굴 누락 |

[기존 90초 채점](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/heldout-grid-baseline.json), [0.85 실행·채점](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/yunet085-scored.json), [0.82 개발 채점](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/yunet082-scored.json), [독립 계획](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/yunet082-independent-plan.json)과 [독립 채점](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/yunet082-independent-scored.json)에 입력·config hash, 정확한 frame 구간, 실행 시간/RSS/출력 경로와 세부 매칭을 남겼다. 0.85/0.82는 각각 다른 config·embedding cache 공간으로 취급했다. 5개 프레임 점수 진단 1회와 각 세 창씩 0.85·0.82 개발·0.82 독립 추론 **9회**를 실행했다. 세 창 실행들은 각각 12.709초/약423MB, 11.142초/약425MB, 7.544초/약418MB peak RSS로 사전 한도(각 창 90~120초, 총 270~360초, 4GiB, 100MiB 출력) 안이었다. 앱 MP4/완료 카드는 새로 만들지 않았다.

독립 GT의 I1 363–365초를 `no_visible_person_seconds` 배열에 넣은 기록 오류가 있다. 같은 잠금 파일의 문장에는 **손이 보이는 음식 화면**이라 사람 없는 화면으로 채점하지 않는다고 명시했다. 잠금 파일은 수정하지 않았고 채점에서 세 프레임을 person-free 분모에서 제외해 [채점 erratum](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/yunet082-independent-scored.json)에 드러냈다. I1 370·371초의 큰 얼굴 누락이나 두 남성의 오합침 판정에는 영향을 주지 않는다.

## 원인 분리

[저장 결과 읽기 전용 audit](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/saved-result-audit.json)에서 동일 인물인데 갈라진 카드의 개별 SFace cosine은 W1_C 0.083–0.325, W1_D 0.219–0.585, W2_B 0.009–0.272, W2_D 0.198–0.333이다. 같은 창의 **서로 다른 사람** 최대값은 W1 0.390, W2 0.400, W3 0.443이다. 분포가 겹치므로 전역 grouping 기준 0.55를 한 번에 낮춰 같은 사람을 합치는 것은 별도 오합침 위험이 있다. 과거 전체 저장 관측 0.40 대조에서도 실제 다른 인물 오합침을 눈으로 확인해 제품에 적용하지 않았다. 현행 0.55와 0.60 검출 설정을 유지한다.

499개 그룹의 대표 crop 짧은 변 중앙값은 77px이며 134개는 48px 미만, 258개는 80px 미만이다. **48px 미만 대표 134개 중 같은 그룹에 80px 이상 대안이 있는 것은 1개뿐**이다. 현재 sharpness 0.2 미만 112개, 0.4 미만 187개이며 24개 그룹의 대표는 같은 그룹에서 가장 큰 얼굴의 절반 미만 크기다(그중 23개 그룹은 관측이 5개 이상). [대표 crop 표본](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-next-stage/representative-audit/)에서 실제 얼굴의 큰 대안이 있는 카드도 있지만 음식/장식 자체를 얼굴로 분류한 카드에는 좋은 후보가 없다. 수치만으로 사용자 대표 이미지 품질 향상을 주장하지 않는다. 사용자 교체 override는 보존한다.

전체 811개 클립 중 3초 미만 601개다. 원본 컷 재계산에서 그중 539개는 속한 shot 자체가 3초 미만이었다. 저장 클립을 원본 시간순으로 놓았을 때 연속 경계이고 그룹을 공유하는 인접 쌍은 810쌍 중 80쌍(짧은 clip을 포함한 쌍 71)뿐이다. 이 80쌍도 같은 사람의 연속 장면이라고 확인한 GT가 아니므로 자동으로 이어 붙이지 않는다. 같은 scene ID의 서로 다른 편집 경계와 사용자 수정은 계속 보존한다.

## 결정과 남은 일

0.82와 0.85 모두 **앱 기본값으로 채택하지 않는다**. 재추론 횟수를 더 늘려 같은 얼굴 score만 조정해도 검출 누락·음식/장식 오검출·동일인 과분리·다른 사람 오합침·짧은 컷을 동시에 해결한다는 근거가 없다. 현재 시험 결과는 사용자 불합격 상태로 둔다. 다음 개발은 (1) 대표 후보에 실제 선명한 얼굴이 있는 그룹과 없는 오검출 그룹을 구분해 작은 이미지 랭킹 변경을 별도 검증, (2) 얼굴 검출/동일성·shot 컷/등장 interval을 각각 독립 GT에서 검증, (3) W13 공용 DTO/embedding 공간·compatibility fixture 합의 순서다. 배경/단역 포함 연속 interval recall, 전체 영상 false merge/split, 대표 이미지 수정 시간, 다른 입력·Windows/패키징은 여전히 미검증이다. 새 모델·body/화자 결합·ReID·유료 API·Build5는 여기서 시작하지 않았다.
