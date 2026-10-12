# W14 공식 ArcFace 특징 공간 격리 비교 — 실제 결과

2026-10-01 KST. 사용자는 [범위를 잠근 제안](01-w14-alternative-face-embedding-probe-proposal.md)에 **「승인」**했다. 이 기록은 그 승인으로 수행한 한 모델·한 영상·150초의 비교다. **제품 적용 gate는 실패했다.** 기존 완료 카드, 사용자 편집, Person/Dance 모델·공용 API·기본 검출 0.60/묶기 0.55는 그대로다.

## 입력·모델·실행 경계

- 원본: `desktop/clipper_nestjs/.clipper_data/sources/youtube/0KQDhi7ddrk/source.mp4`, SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`. 기존 5 fps manifest SHA-256 `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`. YuNet SHA-256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`, 검출 점수 0.60 고정.
- [Open Model Zoo 공식 `model.yml`](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/face-recognition-resnet100-arcface-onnx/model.yml)의 원본 ONNX **1개** 261,036,388 B를 격리 폴더에 받았다. 공식 SHA-384 `4bceb34ee96c7c0b544012be53870d757f332d9d2972962065618de6942cf60f63b94f702f85fcc31844b21de326ec72`가 일치했다. 실제 SHA-256 `f0a2e278b430372d308fef67c1aea308c2baf37f32e8908d9bfce035c26a3fb4`. [공식 카드](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/face-recognition-resnet100-arcface-onnx/README.md)는 원본 모델 Apache-2.0, 112×112 RGB, 512차원이라고 명시한다. 제품 재배포의 고지·패키징 권리는 별도 검토 전이다.
- 초기 ONNX Runtime 1.24.4 CPU는 첫 얼굴의 `stage1_unit1_bn1` BatchNormalization에서 `Invalid input scale: NumDimensions() != 3`으로 실패했다. 생성 embedding 0개. 같은 오류가 [ONNX Runtime 공식 이슈](https://github.com/microsoft/onnxruntime/issues/2447)에 기록돼 있다. 동일 weight를 기존 OpenCV 4.13 DNN CPU로 로드해 `fc1` `(1,512)` 유한값 스모크를 통과한 후 **백엔드가 다른 config/runner SHA로 계획을 다시 잠갔다.** 이는 제품용 OpenVINO/ONNX Runtime 패키징 성공을 뜻하지 않는다.
- 최종 embedding 공간: 모델 SHA-256 위 값 + config SHA-256 `e43af94246ef297e484a05a6dcc8c1d79dea2abfa8ba05ebf7ceaede8ba42d74`; runner SHA-256 `7f8d16353501cb0fdbce656d219ac51ecab911372475659e310ce5f5d0d11a20`. YuNet 5 landmarks를 기존 bbox에 일대일 IoU≥0.5로 대응하고 [원 저자 정렬 좌표](https://github.com/deepinsight/insightface/blob/master/recognition/subcenter_arcface/common/face_align.py)의 112×112 템플릿으로 similarity 정렬했다. 112×112 RGB `float32` 0–255 NCHW → `fc1` L2 정규화는 [원 모델 추론 예제](https://github.com/onnx/models/blob/main/validated/vision/body_analysis/arcface/dependencies/arcface_inference.ipynb)의 순서와 일치한다. SFace 벡터/cache/0.55 기준과 섞지 않았다.
- [잠금 실행 계획과 산출물](../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-arcface-probe/plan.json): 개발 `[985,1015)`, `[1526,1556)`, `[1623,1653)` 90초, 독립 `[359,379)`, `[1843,1863)`, `[1949,1969)` 60초. 개발 원본 우선 GT SHA `ea8f89480dd71d73b05495269d40e00573921b0f35bbdbb7040986370585fd07`, 독립 GT SHA `073605988de39c95f75655da0405ebc34ec435862399fff52661c470b9866f97`. 개발 기준을 잠근 뒤 독립 라벨을 채점했다. Mac CPU, 750 표본 프레임·최대1,500 얼굴·45분·RSS4GiB·출력200MiB 경계였다.

## 실제 측정

| 항목 | SFace 기존 관측의 같은 창 재묶기 | ArcFace 새 특징, 개발에서 고정한 cosine 0.30 |
| --- | ---: | ---: |
| 개발 104개 명확한 얼굴, pairwise precision/recall | 1.000 / 0.881 | 1.000 / 0.881 |
| 개발 B-cubed precision/recall, 과분리 여분 그룹 | 1.000 / 0.890, 4 | 1.000 / 0.890, 4 |
| 독립 63개 명확한 얼굴, pairwise precision/recall | 0.933 / 0.938 | 0.933 / 0.938 |
| 독립 B-cubed precision/recall, 과분리 여분 그룹 | 0.951 / 0.931, 2 | 0.951 / 0.931, 2 |
| 독립 다른 인물 오합침 쌍 | 14 | **14** |

개발 기준은 사전 명시한 0.20–0.85 격자에서 **라벨 오합침 쌍 최소 → 동일인 합침 쌍 최대 → 더 낮은 문턱** 순으로 0.30을 택해 [freeze 파일](../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-arcface-probe/development-threshold.json) SHA-256 `31ade8f43ab9d8617685a88ea026141e3f5f72b770989960f45135614f01a2c3`로 잠갔다. 독립 창에서 기준을 재조정하지 않았다. 역사적 전체 영상 SFace 결과도 독립 라벨에서는 같은 요약 점수였으나, 공정한 모델 비교는 위의 **같은 관측·같은 창 재묶기** 열이다.

개발/독립 1,074관측 모두 같은 상자와 IoU 1.0으로 대응해 새 특징 1,074개가 나왔다. 실패 0, 라벨 명확 얼굴 167/167 대응, W1 배경 인물 G/H 모두 명확 얼굴이 남았고 각 1그룹이다. 여섯 창의 **동시 출연 다른 track의 같은 그룹 0쌍**이었다. I1의 다른 두 남성 A/D는 서로 다른 track인데도 같은 그룹으로 합쳐졌고, 이들의 라벨 얼굴 평균 ArcFace cosine은 약 **0.671**이다. 즉 이 오류는 이 창에서 같은 track 강제 연결이 아니라 새 embedding/현행 greedy 묶기 판단에도 남은 것이다. 검출 상자가 완전히 같으므로 기존 확인된 비얼굴 관측 개발12·독립5는 제거되지 않는다.

실제 750 프레임, embedding 1,074회, 두 단계 합산 60.633초, 최대 프로세스 RSS 1,859,944,448 B, 모델 제외 출력 약 12.1MB로 승인 상한 이내였다. [독립 채점](../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-arcface-probe/validation-report.json)·[대응/자원 감사](../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-arcface-probe/posthoc-audit.json)에 세부 수치를 남겼다. 계획에 정한 **독립 오합침 0 + 같은 사람 합침 개선** gate가 모두 충족되지 않아 **이 모델/전처리/문턱 조합을 기각**한다. 제품 재분석·새 MP4·앱 프로젝트·모델 설치는 0회다.

## 다음 판단의 경계

새 특징만 바꿔서는 확인된 다른 인물 오합침과 동일인 과분리가 나아지지 않았다. 다른 모델을 제품 기본값으로 들이거나 SFace/ArcFace 기준을 섞지 않는다. 기존 사용자가 지적한 짧은 scene 중 원본 컷 자체가 짧은 539개, 흐린/작은 대표 얼굴, 검출의 음식 오인식은 이번 고정 관측 비교가 해결할 수 없는 별도 문제다. 다음 단계는 **오합침·과분리의 track/shot/embedding 원인 사례를 분리한 뒤**, 원본 장면 경계 GT와 다른 영상의 익명 인물 GT를 잠그는 것이다. 추가 백엔드/모델, 37분 재실행, 과금/권한 계약은 이 결과로 자동 승인되지 않는다. 연속 interval recall, 대표 이미지 품질·수정 횟수/탐색 시간, 내보내기 중복·수정 보존, Windows/패키징, W13 Dance adapter 호환은 아직 미검증이다.
