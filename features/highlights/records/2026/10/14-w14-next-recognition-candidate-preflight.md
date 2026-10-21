# W14 — 다음 인식 후보 선정과 실행 전 준비

2026-10-14. 사용자 요청: “진행해줘 다음단계”. 이번 결과는 조사와 실행 범위 준비다. **새 모델 실행 결과가 아니며, 제품의 얼굴 매칭 품질이 개선됐다고 주장하지 않는다.**

## 1. 결정

다음 조사 후보를 **SeetaFace6 Light (`face_recognizer_light`) 한 개**로 좁혔다. 기존 SFace를 대조군으로 유지한다. 이 후보는 최신 모델이라는 이유로 선택한 것이 아니다. 다른 학습 가중치, 작은 배포물, 공식 무료 상업 이용 안내, 기존 ONNX Runtime을 재사용할 가능성이 선택 이유다.

제품 채택과 실행 승인은 별개다. 공식 원본과 제3자 ONNX 변환본의 관계, 정확한 파일의 조건, 변환·입력 처리를 확인해야 한다. 사용자에게 가중치 두 파일 약 10MB와 제한된 CPU 비교를 하나의 범위로 제시했다. 답변 수신 전에는 가중치 다운로드와 ML을 시작하지 않는다. 이는 사용자가 처음 지정한 “새 모델 다운로드는 별도 범위” 및 Superpowers의 새 실험 승인 절차에 따른 것이다.

## 2. 기존 작업에서 이어받은 근거

- 가까운 참조 두 장의 점수 결합은 미채택이다. SFace는 일부 회복과 기존 하니·해린 손실이 함께 있었고, Aura는 추가 영상 정답이 17→15로 감소했다. 다니엘→해린 오류도 남았다. [직전 결과](14-w14-two-reference-transfer-result.md)
- 참조 사진 보강도 이미 시험했다. 다른 영상의 확인 얼굴 8장을 추가해 일부 근거가 늘었지만, 새로 붙인 하니 이름이 실제 해린 메인과 모순됐다. 이를 다시 새 개선책으로 제안하지 않는다. [참조 보강](14-w14-cross-video-reference-append-result.md), [사용자 확인 후 오류 확정](14-w14-confirmed-main-errors-and-opposition-result.md)
- 현재 안무 GT 34장은 과거 개발 자료와 같은 프레임·같은 이름이다. 두 추가 영상도 이미 여러 실험에 노출됐다. 새 후보가 좋아지더라도 이 자료만으로 새 영상 일반화나 제품 교체를 확정하지 않는다.

## 3. 세 경로의 비교

| 경로 | 얻을 수 있는 것 | 비용과 한계 | 이번 선택 |
|---|---|---|---|
| 새로운 인식 가중치 한 개 비교 | 기존 모델이 구분하지 못하는 얼굴에 새로운 특징 제공 가능 | 파일 조건·전처리·CPU 호환 검증 필요. 개선은 미확인 | SeetaFace6 Light의 실행 가능성부터 확인 |
| 사용자 참조 사진 등록 방식 변경 | 다른 각도·촬영 조건의 근거 보충 가능 | 사용자의 추가 등록 부담. 기존 8장 보강에서도 오분류 발생 | 같은 보강/조합 반복은 하지 않음 |
| 별도 학습·미세조정 | 무대 영상에 맞춘 특징 학습 가능 | 적법한 학습 자료·독립 검증·학습/배포 범위가 새로 필요 | 현재 범위에서 제외 |

성능이 확인되지 않은 새 모델들을 동시에 여러 개 추가하지 않는다. 참조 사진·검출기·메인 선택·합의 규칙을 한 번에 바꾸지 않는다.

## 4. 후보별 공식 자료 재확인

### SeetaFace6 Light — 조건부 시험 후보

공식 프로젝트는 무료 상업 이용을 안내하고 BSD 2-Clause 조건을 게시한다. Light는 Mobile FaceNet, 512차원 특징으로 설명된다. 공식 배포는 `face_recognizer_light.csta`이고, Windows 빌드 안내는 있지만 Apple Silicon용 완제품 패키지가 확인된 것은 아니다. C++ 원본 경로에는 OpenRoleZoo·SeetaAuthorize·TenniS가 있다. [공식 프로젝트](https://github.com/SeetaFace6Open/index), [공식 라이선스](https://github.com/SeetaFace6Open/index/blob/master/LICENSE)

별도 프로젝트 `SeetaFace6Sharp/SeetaFace6Onnx`는 ONNX 변환 코드와 원본 미러를 공개한다. 해당 프로젝트의 라이선스는 MIT이며, 모델은 SeetaFace6Open 조건을 함께 따르도록 안내한다. 이를 공식 모델 공급자의 ONNX 배포라고 부르지 않는다. [변환 프로젝트](https://github.com/SeetaFace6Sharp/SeetaFace6Onnx)

읽은 변환 저장소 revision: `3cefcf6896a2e7268add82ea89f720271a825157`.

| 파일 | GitHub 메타데이터 크기 | Git blob SHA-1 |
|---|---:|---|
| `scripts/weights/face_recognizer_light.csta` | 4,730,388 bytes | `1a6a23d95adcffbbfd660832c776ec0c608185e8` |
| `scripts/onnx/fp32/face_recognizer_light.onnx` | 4,714,634 bytes | `37f99e7b5fa857fd683c7959c8d6616bfea0eecb` |

두 파일 합계는 9,445,022 bytes다. **이 수치는 미러 메타데이터이며, 실제 공식 원본의 SHA-256 확인이나 다운로드 완료를 의미하지 않는다.** 파일 크기로 메모리·속도를 예측하지 않는다. 원본은 공식 인덱스가 연결하는 [공식 배포 링크](https://www.dropbox.com/s/d296i7efnz5evbx/face_recognizer_light.csta?dl=0)와 대조해야 한다.

### dlib / Taguchi dlib — 예비 후보 유지

dlib 작성자는 모델의 public domain 배포를 명시하며, Taguchi 가중치도 공식 모델 저장소에서 연결된다. Taguchi 버전은 기존 예비 목록에 없던 추가 발견이다. 다만 저자가 설명한 학습 구성만으로 이 영상에서 더 정확하다고 판단할 수 없다. 공식 저장소에 추가된 날짜는 2024-05-21이며 최신 모델이라고 소개하지 않는다. [dlib 모델 저장소](https://github.com/davisking/dlib-models), [Taguchi 원문](https://github.com/TaguchiModels/dlibModels/blob/main/README_EN.md)

현재 공식 PyPI `dlib 20.0.1` 배포 목록은 소스 압축 파일 하나다. Clipper에서 쓰려면 Mac arm64 / Windows x64용 내부 wheel 준비가 필요할 수 있다. 소스 빌드를 사용자 PC에 요구하는 경로는 채택하지 않는다. 작은 무대 얼굴 개선 근거와 배포 부담 때문에 이번 우선 후보에서 제외한다. [공식 PyPI](https://pypi.org/project/dlib/20.0.1/#files)

### EdgeFace / CVLFace / FaceX — 지금 추가하지 않음

- EdgeFace-XS의 기관 배포는 CC BY-NC-SA 4.0을 명시한다. [기관 모델 카드](https://huggingface.co/Idiap/EdgeFace-XS-GAMMA)
- CVLFace AdaFace IR18 WebFace4M 카드는 학습 데이터 라이선스 준수를 요구한다. 코드 라이선스로 가중치 상업 배포를 확정하지 않는다. [작성자 모델 카드](https://huggingface.co/minchul/cvlface_adaface_ir18_webface4m)
- 새로 찾은 FaceX는 작성자가 자체 가중치 Apache-2.0을 주장하지만, native ARM 전체 빌드는 로드맵 상태로 설명한다. MS1M 학습·가중치 출처 조건과 실제 파일별 검토도 필요하다. 현 Clipper 경로에 넣을 우선 근거가 부족하다. [작성자 저장소](https://github.com/facex-engine/facex)

최근에 나온 wrapper가 기존 AuraFace/SFace를 다시 포장한 경우도 확인했다. 예를 들어 LibreFaceRec은 AuraFace-v1 인식 가중치를 사용한다. 이를 새로운 학습 모델로 세지 않는다. [제공자 설명](https://www.libreyolo.com/docs/models/librefacerec)

## 5. 전처리에서 이미 확인한 주의점

제3자 변환 메타데이터와 C# 소비 코드는 Light의 정렬을 112×112, 출력 512차원, 외부 스케일을 약 1/255로 설명한다. C# 정렬 경로는 BGR 저장을 사용한다. **‘ArcFace 형식 정렬’이라고 해서 기존 AuraFace의 RGB·127.5 정규화를 복사하면 안 된다.** 원본 CSTA의 실제 설정과 ONNX 내부 연산을 확인해 스케일이 두 번 적용되지 않도록 해야 한다.

공식 `FaceRecognizer6` 소스는 전처리·출력 정규화·유사도 변환을 모델 설정에서 읽는다. 읽은 소스 revision은 `55506482e72bb14b3bb0df7a91249dceebb3ebaf`다. 따라서 wrapper의 상수만 믿고 구현하지 않는다. [공식 소비 코드](https://github.com/SeetaFace6Open/FaceRecognizer6/blob/55506482e72bb14b3bb0df7a91249dceebb3ebaf/FaceRecognizer/src/seeta/FaceRecognizer.cpp), [변환 메타데이터](https://github.com/SeetaFace6Sharp/SeetaFace6Onnx/blob/3cefcf6896a2e7268add82ea89f720271a825157/scripts/onnx/fp32/models_meta.json)

변환 코드가 사용하는 NumPy 인터프리터와 ONNX의 일치는 원래 TenniS 런타임과의 독립적인 일치 검증을 대체하지 못한다. native 대조가 없으면 그 제한을 명시하며 제품 채택을 보류한다. 현재 어떤 모델 바이너리도 열거나 추론하지 않았다.

## 6. 제시한 실행 범위

1. **파일 준비:** 위 원본·ONNX 두 파일만, 모델 다운로드 총 15MiB 상한. 공식 원본/미러 일치, SHA-256, 라이선스·추가 조건을 기록한다. 조건이 불명확하면 추론 전 중지한다.
2. **격리 환경:** 현재 평가용 Python 3.11 / ONNX Runtime 1.24.4 CPU 경로를 재사용한다. batch 1, 스레드 2. 새 패키지 설치·프레임워크 도입·제품 의존성 변경은 제외한다.
3. **실행 전 고정:** 실제 graph shape/dtype/opset/operators, BGR/RGB, 정렬점 의미·순서, 내외부 스케일, 정규화, 원본 픽셀/landmark hash, 모델 hash, 평가 코드 SHA, OS/device 정보를 잠근다. 현재 준비 JSON에 없는 모델 SHA를 추정해서 채우지 않는다.
4. **CPU 상한:** sanity·변환 대조·시간 측정을 포함해 총 forward 최대 600회, 20분, RSS 4GiB. 상한에 도달하면 부분 결과와 실패를 남기고 중단한다. 무제한 추론 승인을 이유로 자원 상한을 없애지 않는다.
5. **비교 입력:** 기존 참조 23장, 개발 export 135행, 현재 고정 안무의 유효 얼굴 309개, 추가 두 영상 34개. 중복·무효 처리 전 최대 501개 얼굴 입력이며, 원래 안무 미확보 44개는 실패 사유와 함께 보존한다. 원래 검출·메인·몸 경로·구간은 고정한다.
6. **판정:** 새 모델의 참조 특징과 캐시는 완전히 분리한다. 집계는 centroid 한 개다. threshold는 개발 자료에서만 정하고 평가 전에 고정한다. 기존 SFace/Aura 문턱을 복사하지 않는다. 같은 모델의 추가 집계·정렬 조합을 늘리지 않는다.
7. **결과:** 얼굴별 오확정·식별가능 미매칭·확정 정답·후보 점수, 멤버별 혼동과 손실/회복을 먼저 기록한다. 그 뒤 같은 35대상/37몸 경로 합의 결과를 따로 표시한다. 얼굴 수를 독립 영상 수로 세지 않는다.

통과 기준은 일부 실패 사진의 회복만으로 정하지 않는다. 기존 정답 손실, 다니엘/혜인 오분류, 추가 영상의 멤버와 등록 외 결과를 함께 비교한다. 현재 자료에서 개선 여지가 확인된 뒤에만 새로운 촬영 자료의 독립 평가와 두 OS 패키징을 진행할 근거가 생긴다. **이번 준비로 제품 적용을 승인한 것은 아니다.**

## 7. 현재 구조와 소유권

공통 core 0.2.0은 Python 3.11이며 기본 의존성은 NumPy, OpenCV는 선택 의존성이다. `EmbeddingSpace`는 모델 SHA, 정렬·전처리·정규화·backend 버전과 차원을 구분한다. 새 시험은 기존 `evaluation/candidate_comparison` 옆의 격리 adapter로 시작할 수 있으며, core API 변경은 필요하다고 확인되지 않았다.

W14는 평가·공통 API/fixture, W13은 안무 main/몸/구간/mapping/crop/제품 adapter 소유를 유지한다. 향후 채택 시 계약 확인 → 소비자 compatibility test → 선택 환경/모델 준비 → Mac arm64·Windows x64 패키징 → 합의한 merge 순서다. 기본 SDK에 ML import/모델 준비를 추가하지 않는다. Mac Intel은 제외한다.

## 8. 이번에 실제 한 것과 하지 않은 것

공식 자료와 고정 revision 소스·메타데이터 10개를 읽어 hash를 기록했고, 기존 평가 입력 54개 hash를 재확인했다. 원래 참조 보강과 결합 실험 결과를 대조했다. 준비 산출물은 다음 폴더에 있다.

`/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/recognition-next-evidence-v1/`

- `candidate-readiness.json`: 파일 식별, 알려진 명세와 미확인 항목, 실행 범위. 실행 승인을 대신하는 파일이 아니다.
- `sources/manifest.json`: 읽은 문서 URL·revision·내용 SHA-256. 외부 코드는 실행하지 않았다.
- `research-verification.json`: 조사 파일 10개와 기존 입력 54개 검증 기록.

새 모델 다운로드 0, ML 0, 의존성 설치 0, 제품/core/W13 수정 0, 새 세션/외부 메시지/commit/push/Build5 0이다. 기존 비교 화면도 바꾸지 않았다. 남은 사용자 입력은 제시한 신규 모델 실험 범위의 승인 하나이며, 얼굴 이름 재작성이나 새 export 요청은 없다.
