# W14 다른 얼굴 특징 공간의 격리 비교 제안 — 미승인·미실행

**후속 상태(10/1):** 사용자가 이 범위를 「승인」했고 격리 실행을 마쳤다. 독립 60초에서 오합침·과분리가 개선되지 않아 제품 적용 gate 실패. 아래 문단의 미승인·미실행 표현은 **제안 작성 당시 상태**다. [실제 입력·SHA·결과](01-w14-arcface-isolated-probe-result.md).

2026-10-01 KST. **제안만 작성했다. 새 weight 다운로드·설치·추론·제품 변경은 0회다.** 기존 YuNet 점수 0.85/0.82는 잠금 얼굴 GT에서 실제 사람을 놓쳐 기각했다. 동일인 분리의 SFace cosine과 서로 다른 사람의 범위가 겹치며, 독립 창에서는 서로 다른 두 사람이 한 그룹으로 합쳐졌다. 대표 48px 미만 134개 중 80px 이상 대안은 1개뿐이고 짧은 장면 다수는 원본 컷이 짧다. 따라서 이 제안은 **인물 묶기 한 문제의 가능성 시험**이며 오검출·흐린 원본·짧은 컷까지 해결한다는 주장이 아니다. [실제 근거](01-w14-source-first-holdout-and-threshold-audit.md).

## 비교 후보와 권리·실행 경로

Open Model Zoo의 [`face-recognition-resnet100-arcface-onnx` 모델 카드](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/face-recognition-resnet100-arcface-onnx/README.md)는 원본 weight를 Apache-2.0으로 명시한다. 112×112 RGB 원본 입력, 512차원 embedding, 24.2115 GFLOPs/65.132M parameters로 현행 SFace보다 무거운 후보이며 카드의 LFW 정확도는 본 영상 성능으로 해석하지 않는다. 공식 [`model.yml`](https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/face-recognition-resnet100-arcface-onnx/model.yml)은 원본 ONNX 크기 **261,036,388B**, checksum `4bceb34ee96c7c0b544012be53870d757f332d9d2972962065618de6942cf60f63b94f702f85fcc31844b21de326ec72`(96 hex, SHA-384 형식)와 공개 모델 source를 명시한다. 다운로드한다면 이 checksum을 검증하고 파일의 SHA-256을 따로 확정한 뒤에만 모델을 호출한다. 제품 배포용 attribution/notice와 source weight 권리는 실제 받은 파일을 다시 대조한다.

[OpenVINO 2026 시스템 요구사항](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino/system-requirements.html)은 macOS arm64 및 Windows x64의 CPU 실행 경로를 제공한다. 이 문서가 **우리 Electron plugin venv에서 실행·패키징 성공을 입증하지는 않는다**. 비교 단계는 격리 평가 venv의 Mac CPU만 대상으로 하고, 기본 SDK·기존 Dance venv나 제품 앱에 OpenVINO/ML을 추가하지 않는다. CUDA/MPS·Windows 실기는 별도 gate다. 공식 ONNX는 원본 RGB 입력이고 OpenVINO 변환 모델의 BGR 설명과 혼동하지 않는다. 다른 정렬/색순서/정규화가 새로운 `embeddingSpaceId`이며 SFace cosine threshold 0.55, cache, centroid와 섞지 않는다.

## 승인 대상으로 제안하는 좁은 실험

1. **다운로드 1개:** 위 원본 ONNX 1개만 격리 평가 폴더에 받고, 전송 300MiB/디스크 600MiB/15분을 상한으로 둔다. 공식 SHA-384와 계산한 SHA-256이 맞지 않으면 종료하고 실행하지 않는다. 새 유료 API·Build5·다른 모델 다운로드·기존 프로젝트 재처리는 없다.
2. **동일 관측 비교:** 원본 `source.mp4` SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`, 기존 YuNet/SFace weight SHA와 5 fps manifest SHA `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`를 잠근다. 개발 90초 `[985,1015)`, `[1526,1556)`, `[1623,1653)`과 모델 출력 미열람 60초 `[359,379)`, `[1843,1863)`, `[1949,1969)`만 사용한다. YuNet 검출 기준 **0.60 유지**, 같은 얼굴 box/관측을 새 모델의 five-landmark 정렬과 매칭해 embedding만 바꾼다. 탐지 실패나 작은 배경 얼굴은 분모에서 숨기지 않는다. 새 모델의 사전처리·alignment/config/model/code hash와 실제 observation IDs를 산출물에 기록한다. 현행 모델의 0.55를 새 512차원 공간에 복사하지 않는다.
3. **자원과 출력:** 150초/5 fps 총 최대 750 표본 프레임, 새 특징 추론 최대 1,500개 얼굴, Mac CPU 총 45분/RSS 4GiB/결과 200MiB. frame decode·정렬이 실패한 관측은 실패 상태로 남기고 제외 개수를 보고한다. 출력은 격리 JSON/진단 crop이며 MP4·앱 카드 생성 없음. 시간·메모리·출력 한도 위반 시 중단한다. 정확한 실행 code SHA와 새 weight SHA-256은 다운로드·실행 직전 계획 JSON에 고정한다.
4. **결정 기준:** 90초 잠금 개발 GT에서 새 공간의 grouping 기준을 하나 정하고, 미열람 모델 결과 60초 잠금 GT에서 별도 채점한다. Pairwise와 B-cubed precision/recall, 사람별 false split, I1의 다른 두 남성 false merge, 동시 출연 cannot-link, 배경/단역의 확실한 얼굴 대응, 오검출 별도 수치를 남긴다. **얼굴 누락/다른 사람 오합침이 증가하면 기각**한다. 같은 사람 과분리가 줄고 I1 오합침이 해소되어도 동일 방송 한 편의 희소 프레임 검증일 뿐 제품 기본값 채택·전체 37분 재생성으로 자동 넘어가지 않는다. 다른 인터뷰 영상/연속 interval/대표 이미지·편집 시간과 Windows/패키징을 그다음 별도 gate로 둔다.

이 제안은 사용자가 원래 별도로 범위를 정하라고 한 **새 모델 다운로드**를 포함한다. 현재의 무제한 *기존 얼굴 추론* 승인이 이 ONNX 다운로드·새 embedding 모델 실행 승인으로 확장됐다고 해석하지 않는다. 사용자가 이 구체적 범위를 선택해야 실행한다.
