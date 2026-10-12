# W14 인물용 몸 검출 후보와 등장 구간 연결 규칙 — 2026-10-02

상태: **공식 자료 조사와 설계 제안. 모델 선정·다운로드·추론·제품 적용·성능 검증 아님.** 사용자는 Dance의 기존 YOLOv8 pose를 W14에서 사용할 수 없다고 결정했다. Dance의 대체 모델은 아직 미정이며, W14는 별도로 인물 등장 구간 문제에 맞는 후보를 고른다. 성공 기준은 얼굴이 잠깐 가려지거나 화면 밖으로 나가도 **같은 편집 shot 안에서 몸이 계속 보이는 동일 인물의 등장 구간을 이어 주고**, 동시에 있는 다른 사람·컷 뒤의 별도 인물을 잘못 잇지 않는 것이다. 얼굴 앵커 없는 몸 상자로 Person 카드·클립·`확인 필요` 그룹을 만들지 않는 기존 사용자 결정은 유지한다.

## 모델 역할과 후보

인물 검출기는 프레임마다 `person` 상자만 제안한다. **동일인 판정·연속 구간·컷 경계는 검출 모델만으로 나오지 않는다.** 첫 비교는 모델을 하나씩 검출기로 교체하고, 동일한 shot-local 1:1 추적·얼굴 앵커 연결 규칙을 적용한다. 자세 관절 추정은 이 목적의 필수 입력이 아니다. COCO 전체 객체 AP는 우리 영상의 작은 배경 사람·부분 몸·동시 출연 성능이 아니며, 서로 다른 제작사의 latency 표를 직접 순위로 비교하지 않는다.

과거 37분 결과의 3초 미만 clip 601개 중 539개는 원본 shot 자체가 3초 미만이었다. 따라서 몸 추적이 같은 shot 안의 **얼굴 누락 때문에 생긴 분할**은 줄일 수 있어도, 실제 편집 컷 때문에 짧아진 원본 구간을 길게 만들지는 못한다. [원본 컷·기존 pose 시험의 한계](02-w14-existing-pose-continuity-feasibility.md).

| 후보 | 공식 공개 수치·시기 | 이 작업에서 볼 이점과 위험 | 공개 코드/weight 조건 |
| --- | --- | --- | --- |
| **D-FINE-S COCO-only** | 2024 공개/ICLR 2025; COCO box AP 48.5, 10M params, 25 GFLOPs. T4 TensorRT 10.4 FP16 batch1 3.49ms | 경량과 정확도의 첫 균형 후보. 얼굴 없는 몸/배경 사람 recall은 미측정. ONNX 변환/CPU 경로는 공식 제공하나 Mac·Windows 패키징 실기 미확인 | 공식 GitHub 코드 Apache-2.0, 제작자 Hugging Face COCO checkpoint 저장소 Apache-2.0. **Objects365·obj2coco checkpoint는 공식 주의 문구상 별도 dataset terms 가능성이 있어 후보에서 제외** |
| **D-FINE-N COCO-only** | 2024.11 공개; COCO box AP 42.8, 4M params, 7 GFLOPs. 같은 T4 조건 2.12ms | 가장 작은 계산량 대조군. 작거나 부분만 보이는 배경 인물 누락이 늘 수 있음 | 공식 GitHub Apache-2.0 경로의 COCO checkpoint만 검토. 정확한 weight URL/hash와 배포 파일별 라이선스는 취득 전에 재확인 |
| **RF-DETR-S** | ICLR 2026; 공식 COCO AP50:95 53.0, 32.1M params, 512px 입력, T4 TensorRT FP16 batch1 3.5ms | 품질 대조군. 상대적으로 무겁고 우리 긴 영상 CPU 시간·메모리 미확인 | 공식 `rfdetr` 코드와 Apache 지정 Small weight 모두 Apache-2.0. Plus/XL/2XL 검출 모델의 PML 1.0과 구분 |
| **RF-DETR-N** | ICLR 2026; 공식 COCO AP50:95 48.4, 30.5M params, 384px 입력, 같은 T4 조건 2.3ms | 새 계열의 저지연 대조. 이름은 Nano지만 30.5M params로 D-FINE-N보다 메모리가 작다고 단정 불가; 384px에서 작은 배경 사람 누락 가능 | 공식 `rfdetr` 코드와 Apache 지정 Nano weight 모두 Apache-2.0 |
| **RTMDet-tiny / MMDetection 경로** | 2022 계열; 공식 COCO box AP 41.1, 4.8M params, 8.1 GFLOPs; T4 TensorRT FP16 2.34ms | 성숙한 경량 기준선. 최신 품질 후보보다 구형; 우리 영상 정확도 미확인 | MMDetection 코드 Apache-2.0, 공식 개발자 답변은 RTMDet 배포에 Apache-2.0 적용 가능하다고 설명. MMYOLO의 GPL 학습 구성요소는 이 경로에 섞지 않음. 정확한 checkpoint와 runtime 의존성 고정 후 최종 확인 |

공식 자료: [D-FINE 모델 표·Objects365 주의·배포](https://github.com/Peterande/D-FINE/blob/master/README.md), [D-FINE 코드 라이선스](https://github.com/Peterande/D-FINE/blob/master/LICENSE), [D-FINE 제작자 checkpoint 저장소](https://huggingface.co/Peterande/D-FINE), [RF-DETR 모델·weight별 라이선스](https://github.com/roboflow/rf-detr), [RTMDet 모델 표](https://github.com/open-mmlab/mmdetection/blob/main/configs/rtmdet/README.md), [MMDetection 배포 경로·사용권 답변](https://github.com/open-mmlab/mmdetection/discussions/10006).

두 사람의 상자가 자주 겹쳐 1:1 추적이 무너진다는 **원본 증거가 생기면**, 별도 상향 후보로 RF-DETR-Seg-N/S의 사람 instance mask를 검토할 수 있다. 공식 표의 Seg-N/S는 33.6M/33.7M params, COCO mask AP 40.3/43.1이며 Apache 지정 모델이다. 이것도 동일인 인식 모델은 아니고, 작은 입력 해상도·추론 비용/패키징 때문에 첫 detector 비교에는 넣지 않는다. [공식 segmentation 표와 라이선스](https://github.com/roboflow/rf-detr).

Apache-2.0/MIT 후보는 라이선스 자체가 SaaS의 자체 소스 공개를 요구하지 않는다. 배포 시 라이선스/NOTICE·수정 고지 등 해당 조건은 보존한다. **무료 라이선스는 실행 자원 비용이 0이라는 뜻이 아니다.** D-FINE의 Objects365 계열, RF-DETR Plus/PML, Ultralytics AGPL 계열은 이번 **무료·비공개 소스** shortlist에 넣지 않는다. 새 weight를 가져오기 전에 정확한 URL·버전·파일 SHA-256·코드/weight/의존성/학습 데이터 조건을 다시 잠근다.

공식 D-FINE은 ONNX Runtime·TensorRT·Torch 추론/ONNX export를 제공하고, RF-DETR은 CPU에서 ONNX export 및 ONNX Runtime 경로를 설명하며, RTMDet은 MMDetection/MMDeploy 추론 경로가 있다. [ONNX Runtime 플랫폼 표](https://onnxruntime.ai/docs/get-started/with-python.html)는 Windows/macOS CPU와 Windows/Linux CUDA 배포를 다루지만 **각 export 모델이 그 조합에서 정확히 작동하고 제품 패키징 가능한지는 아직 검증하지 않았다**. 특히 D-FINE의 Windows DirectML은 공식 저장소에 정확도 문제 보고가 있어 GPU 일반 지원으로 표기하지 않는다. [RF-DETR export 안내](https://github.com/roboflow/rf-detr/blob/develop/docs/index.md), [D-FINE export 안내](https://github.com/Peterande/D-FINE/blob/master/README.md), [D-FINE DirectML 문제 보고](https://github.com/Peterande/D-FINE/issues/327).

## 제안하는 판단 순서

1. **shot와 원본 시간축 고정:** 원본 프레임 PTS/time base에 얼굴·몸 관측을 놓는다. 편집 컷에서 몸 track을 끝내고 다른 shot의 몸만으로 identity를 잇지 않는다. 한 scene에 여러 PersonGroup이 속할 수 있다.
2. **모든 사람 몸 상자 → shot-local 1:1 추적:** 같은 시간의 중복 상자를 정리하고, 인접 위치/크기·운동 예측·겹침·옷 색/질감 같은 *약한* 외형 단서를 함께 써서 전역 1:1로 배정한다. 검출 점수가 낮아도 기존 track과 일치하는 상자는 재검토하는 ByteTrack 방식이 누락 감소의 비교 후보지만 새 인물을 낮은 점수 하나로 확정하지 않는다. [원 ByteTrack 설명](https://github.com/FoundationVision/ByteTrack), [MIT 코드 라이선스](https://github.com/FoundationVision/ByteTrack/blob/main/LICENSE). 이 방식도 사람 ID 정답을 보장하지 않는다.
3. **얼굴↔몸 연결:** 얼굴 상자 중심 포함만으로 결정하지 않는다. 같은 프레임에서 얼굴이 몸 상단의 합리적인 위치인지, 다른 얼굴/몸 후보가 없는지, 이전·다음 프레임의 궤적과 얼굴 임베딩 그룹이 모순 없는지 보고 1:1 대응한다. 여러 후보이면 `ambiguous`, 연결 불가면 `unanchored`로 기록하며 자동 Person 배정은 보류한다.
4. **등장 구간:** 이미 얼굴로 앵커된 몸 track이 같은 shot에서 계속 보이면 얼굴이 잠깐 안 보여도 그 사람의 **관측된 등장 interval**을 이어 준다. 검출 한두 프레임 실패는 앞뒤 같은 track·동시 경쟁 없음·원본 영상 확인 등으로만 제한적으로 보간하고 `inferred` 근거를 별도 기록한다. 몸까지 완전히 사라진 시간은 화면에 등장한 것으로 자동 계산하지 않는다. 숫자 gap/점수 문턱은 지금 정하지 않고 GT에서 false merge와 interval recall을 함께 보며 고정한다.
5. **컷 뒤 재등장과 그룹:** 컷 뒤에는 새로운 interval/track이다. 동일 PersonGroup으로 묶을지는 신뢰 가능한 얼굴 증거 또는 사용자 수정으로 정한다. 몸의 옷차림만 같다는 이유로 컷 사이 그룹을 합치지 않는다. 사용자 이름·대표 이미지·병합/재배정/제외·경계 override가 새 분석으로 덮어써지지 않게 한다.

## 반드시 분리해 검증할 예외

| 원본 상황 | 원하는 처리 | 실패를 막는 조건 |
| --- | --- | --- |
| 고개 돌림·뒷모습·얼굴이 화면 밖, 몸은 계속 보임 | 같은 shot의 **이미 얼굴로 확인한** 한 사람의 등장 interval 유지 | 얼굴 앵커와 몸 track이 유일하고 동시 다른 사람과 충돌하지 않아야 함 |
| 얼굴도 몸도 화면 밖으로 완전히 나감 | 보이는 마지막 시점에서 등장 종료. 돌아오면 새 interval | 짧은 검출 실패 보간과 실제 퇴장을 구분; 몸이 없는 시간을 무조건 채우지 않음 |
| 기둥/타인에 잠깐 가려졌다 재등장 | 짧은 gap은 동일 궤적·외형·전후 얼굴이 일치할 때만 연결 후보 | 가려진 동안 다른 사람이 경로를 차지하거나 얼굴 충돌이면 보류 |
| 두 사람이 교차·겹침·자리 바꿈 | 둘의 ID/PersonGroup을 분리, 오배정 의심이면 보류 | 전역 1:1 배정·동시 출연 cannot-link·앵커 충돌 기록; IoU 최고값만 사용 금지 |
| 한 사람에게 몸 상자 둘, 또는 한 상자에 얼굴 둘 | 중복 몸 상자는 통합 후보, 얼굴 대응은 `ambiguous` | 얼굴 중심 포함/최고 score 하나로 자동 선택 금지 |
| 같은 몸 track에 서로 다른 얼굴 그룹 둘 | 자동 병합 금지. 얼굴 분류 오류/몸 ID switch 둘 다 점검 | 실제 동시 인물·앞뒤 원본 확인, 추적 분기 또는 사용자 수정 |
| 동일 인물이 다른 shot에 재등장 | PersonGroup은 같을 수 있지만 interval은 각각 유지 | 얼굴 embedding/확인된 수정으로 그룹 연결; 편집 컷을 건넌 몸 track 사용 금지 |
| 실제로 다른 인물인데 옷이 비슷하거나 같은 위치에 교대 등장 | 다른 그룹/interval 유지 | 얼굴 충돌, 시간상 동시 등장, 진입/퇴장, 컷을 강한 분리 증거로 사용 |
| 먼 배경·잠깐 지나간 사람·부분 몸 | 검출과 얼굴 인식 가능 여부를 별도 측정. 검출된 얼굴 그룹은 기본 목록에 표시 | 작은 사람 recall 평가; 얼굴 앵커 없는 몸만으로 카드·`확인 필요` 그룹 생성 금지 |
| 카메라 pan/zoom·빠른 움직임 | 실제 사람이 이어지면 track 유지 | 고정 화면 IoU만으로 끊지 않되 카메라 이동 보정의 오합침 별도 시험 |
| 흐린 프레임·저해상도·압축 잡음 | 불확실성을 보존, 좋은 프레임에서 재확인 | 저품질 얼굴의 identity 단정 금지; 대표 사진은 별도 품질 선별 |
| 거울·TV 속 인물·포스터/광고 얼굴 | 실제 사람과 자동 동일 그룹으로 합치지 않음. 화면 속 표현의 포함 정책은 GT에서 따로 정의 | 동시 존재 규칙의 예외를 라벨하고, 정적 사진을 출연 interval로 자동 확대하지 않음 |
| shot 전환 효과·플래시/블랙 프레임 | 원본 편집 경계 검토 후 track 종료/재시작 | 단순 빈 프레임으로 컷과 가림을 혼동하지 않음 |
| 여러 PersonGroup이 같은 scene에 등장 | 각 인물의 실제 등장 interval 유지 | Scene↔PersonGroup 다대다 및 동시 출연 분리 |
| 동일 scene ID지만 서로 다른 편집 경계의 구간 | 각각의 source interval 유지 | scene ID만으로 합치거나 중복 제거하지 않음; export 중복은 동일 편집 source 구간 기준 |

## 선정 전에 필요한 실제 비교

- 모델 호출 전 원본 path/SHA-256, 3개 이하 짧은 사례의 정확한 PTS 범위, 얼굴 보임/안 보임·몸 보임/완전 퇴장·컷·동시 출연·배경/단역·거울/화면 속 인물의 **독립 GT**를 잠근다. 앞선 30초 감사에서 음악 6프레임의 복사 좌표 라벨 오류가 있었으므로 이동하는 사람은 프레임별 확인한다.
- 동일 원본 프레임·해상도·샘플링과 동일 tracking/face-anchor 규칙으로 **D-FINE-S/N, RF-DETR-S/N**, 가능하면 RTMDet-tiny를 비교한다. 모델별 weight/code/config SHA, 전처리, OS/device, 횟수·시간·RAM/VRAM 상한, 출력 경로를 먼저 정하고 새 다운로드·유료 API·Build5는 별도 범위로 둔다. 어떤 후보도 아직 받거나 실행하지 않았다.
- 모델 검출 recall을 **전경/배경·작은 사람·부분 몸·동시 출연**으로 나눈다. 별도로 track ID switch, 몸↔얼굴 미연결/오연결, 동시 다른 사람 false merge, 동일인 false split, **가시 등장 interval recall/경계 오차**, 대표 이미지/편집 수정 보존을 본다. 얼굴만 보이는 경우와 몸만 보이는 경우를 같은 성공으로 세지 않는다.
- Mac arm64 CPU, Windows CPU, 해당 시 CUDA 실기를 각각 재고 모델 로드·decode·pre/postprocess·추적을 포함한 **전체 작업 시간**과 peak 자원을 비교한다. 공식 GPU 단일 프레임 수치로 긴 영상 처리 시간이나 제품 정확도를 주장하지 않는다.

**선정 전 잠정 권고:** 첫 정확도·자원 균형 비교는 D-FINE-S COCO-only와 RF-DETR-S, 저자원 대조는 D-FINE-N을 우선한다. RTMDet-tiny는 오래된 경량 기준선이다. 어느 모델도 지금 제품 채택 상태가 아니다. 얼굴 없는 몸을 같은 사람의 구간으로 잇는 것은 **검출기 선택보다 얼굴 앵커·shot-local 추적·보류 규칙·원본 GT**에 좌우된다.
