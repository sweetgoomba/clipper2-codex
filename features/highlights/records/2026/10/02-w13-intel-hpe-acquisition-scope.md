# W13 다음 후보: Intel 다인 자세 모델 확보 범위 — 2026-10-02

상태: **Intel 모델/runtime 다운로드·실행 보류.** 공식 문서·합성 adapter 확인은 마쳤으나, MoveNet 512에서 사람 검출 45/45에도 메인 선정이 나아지지 않아 [원인 우선순위](02-w13-why-intel-deferred.md)를 바로잡았다. 아래는 보류된 후보의 상한/공식 표기이며 우리 영상의 성능 결과가 아니다.

| 항목 | 잠정 범위 |
| --- | --- |
| 모델 | Intel Open Model Zoo `human-pose-estimation-0007` FP32 IR, 2023.0 고정 URL |
| weight 사용권 | [공식 model.yml](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/models/intel/human-pose-estimation-0007/model.yml)의 `license`가 [OMZ Apache-2.0 LICENSE](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/LICENSE)를 가리킴. 폐쇄형 상용 배포 때도 라이선스/NOTICE 보존 의무는 따로 확인한다. |
| 정확한 weight 파일 | [XML](https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/human-pose-estimation-0007/FP32/human-pose-estimation-0007.xml) 850,306 bytes, 공식 SHA-384 `52b32d13c47ce42db642283128b439ee9eadcc68c8bd32e8edcc574c849b3cde702cf0ee033378b37dd9671e236842ff`; [BIN](https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/human-pose-estimation-0007/FP32/human-pose-estimation-0007.bin) 32,601,720 bytes, 공식 SHA-384 `5711b763909990db35f20ce3dc82710001d030ea600ae81b8187d908d9f751ded6dd9bdbbdc2182225dc79cac92ffb1d` |
| 입력·출력 | [공식 카드](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/models/intel/human-pose-estimation-0007/README.md): 448×448 NCHW BGR 기본 IR, 17 keypoint의 다인 heatmap+embedding. Model API는 원본 화면비에 맞춰 입력을 reshape하고 추론 후 좌표를 원본 크기로 돌림. |
| 런타임 | [OpenVINO 2026 지원표](https://docs.openvino.ai/2026/about-openvino/release-notes-openvino/system-requirements.html)는 Apple silicon/macOS ARM64 CPU와 Windows x64 CPU를 지원. 공식 OMZ Model API의 `HPE-assosiative-embedding` decoder 사용. 정확한 패키지 버전·다운로드 hash는 설치 전 고정. |
| 허가 요청 | 공식 weight 2개와 OpenVINO/decoder 격리 실행 환경 확보. 총 신규 다운로드 **250MB 이내**, 외부 과금 0, 다른 작업 공간/기존 앱 미수정. 출력은 W13 Python 평가 worktree 내부에만 둠. |

사전 준비: 격리 `IntelHpePoseAnalyzer`는 공식 Model API decoder가 돌려주는 pose와 score를 현행 Dance pose 인터페이스로 바꾼다. [공식 decoder](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/demos/common/python/model_zoo/model_api/models/hpe_associative_embedding.py)와 [Model API 호출 계약](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/demos/common/python/model_zoo/model_api/models/model.py)을 재확인해, 관절별 출력이 좌표·신뢰도·태그의 **4값**이고 모델 호출 반환값이 `(decoded, preprocessing_meta)`인 점을 adapter에 반영했다. 소스 파일·실제 weight/runtime 로딩은 아직 검증하지 않았고 **실영상 Intel 추론 0회**다. 모델 파일 SHA-384·decoder Python tree SHA-256·원본/라벨·코드/런타임·CPU/시간/RSS/출력을 검사하고 승인 전 실행을 거절하는 별도 runner를 작성했다. 관련 **50개 테스트**가 통과했고 `--execute`는 현재 manifest를 거절한다. [실행 manifest 초안](02-w13-intel-hpe-manifest.yaml)은 모델/런타임 미확보와 사용자 확인 전이라 실행 불가다. 다음 단계는 사용자의 모델/runtime 확보 승인 → 공식 파일 hash와 설치 버전/코드 SHA 고정 → 같은 로컬 원본 전체, CPU, metadata 전용 1회/시간·RSS·용량 상한의 별도 실행 범위 확인이다. 실제 Intel 결과를 보기 전에는 upstream COCO AP54.3을 우리 메인 정확도나 MoveNet 대비 우위로 환산하지 않는다.

## 같은 원본에서 비교할 기준

아래 비교 기준은 Intel 평가를 재개할 때만 사용한다. 현재 우선순위는 [메인 선택 원인 진단](02-w13-why-intel-deferred.md)이며, 모델 다운로드 확인을 기다리는 상태가 아니다.

`w13_compare_pose_candidates.py`는 저장된 두 자세 분석 결과를 **모델 실행 없이** 같은 원본 프레임 라벨에 대조한다. Intel 파일이 아직 없으므로 MoveNet 512 결과를 양쪽 입력으로 넣어 채점 경로를 자체 점검했고, 두 점수가 동일했다. 이 자체 점검은 새 모델 평가가 아니다.

| 원본 우선 표본 | 저장 MoveNet 512 기준 | Intel 비교 항목 |
| --- | ---: | --- |
| 사람 상자 45명 | IoU≥0.30 대응 45/45 | 같은 위치에 사람을 검출했는지 |
| 단독 메인 18장 | 6/18 | 실제 앞사람의 상자를 골랐는지 |
| 추가 단독 메인 17장 | 6/17 | 같은 기준, 일부 앞선 조사와 겹침 |
| 예약 단독 메인 20장 | 몸통점 포함 8/20, 파랑 `P4` 0/4 | 고른 상자에 정답 몸통점이 있는지 |
| 그룹 원본 프레임 | 세 표본 묶음 모두 4/4 그룹 표시 | 그룹 누락과 단독 오표시를 함께 기록 |

후보를 완료 클립 제작 대상으로 **검토**하려면 단독 메인 세 묶음이 각각 6/18, 6/17, 8/20보다 좋아야 하고, 파랑 `P4` 4장 중 최소 2장을 맞혀야 한다. 단독을 그룹으로 표시한 수와 원본 전체 raw group 시간은 기준선보다 늘지 않아야 한다. 이 프레임 표본은 한 영상·한 검토자의 작은 표본이므로 통과해도 전체 영상 정확도나 최종 클립 품질을 증명하지 않는다. 메인 전환 지연은 연속 정답 구간이 없어 이번 점수로 계산할 수 없다. 멤버 신원·얼굴 매핑·crop은 별도 평가이며, 그룹 장면에 개별 메인이 함께 있는 것을 곧바로 오류로 세지 않는다. 이후 선택된 구간의 실제 MP4를 기존 결과와 나란히 보고 제품 반영 여부를 결정한다.
