# W14 — SeetaFace6 Light 실제 비교 결과와 미채택 결정

2026-10-14. 사용자 “그래 계속 진행해줘”는 직전에 제시한 원본·ONNX 약 10MB, 전체 forward 600회·20분·4GiB, 새 설치·제품 적용 제외의 격리 시험 승인으로 기록했다. [직전 범위](14-w14-next-recognition-candidate-preflight.md)의 승인 대기는 이번 답변으로 해소됐다. Superpowers spike의 결과이며 평가 코드는 제품 backend가 아니다.

## 1. 결론과 모델 상태

**이번 SeetaFace6 Light 도입 경로를 교체 후보에서 제외한다.** 작은 모델이라는 배포 이점은 있지만, 같은 자료에서 기존 두 모델보다 정답을 훨씬 적게 확정했고 혜인→하니 오류가 발생했다. 이 결론은 이번 YuNet 5점 + 명시한 전처리 + centroid + 개발 문턱의 조합에 대한 것이다. 모든 Seeta 모델·모든 입력에서의 성능이나 원래 native SDK의 성능을 판정한 것은 아니다.

| 모델 | 이번 상태 | 근거 |
|---|---|---|
| YuNet + SFace | 제품 기본값·대조군 유지 | 기존 동작 보존. 현재 자료에도 미매칭이 많아 품질 문제가 해결된 것은 아님 |
| YuNet + AuraFace-v1 | 비교 후보 유지·제품 교체 보류 | 다른 영상의 식별 가능한 19얼굴은 가장 많이 맞혔으나 다니엘→해린 오류와 기존 정답 손실이 남음. 영구 폐기 결정 아님 |
| YuNet + SeetaFace6 Light ONNX | 이번 도입 경로 미채택 | 안무 34얼굴 3정답/1오류/30보류, 추가 19얼굴 12정답/7보류. 기존 모델을 대체할 개선 근거 없음 |

새 모델을 실제 실행했지만 **인물 매칭 품질을 개선하는 데 성공한 결과는 아니다.** 이번에 이룬 것은 공식 파일에서 실행까지의 연결 확인, 제한된 실제 비교, 부적합 후보 배제와 재현 가능한 근거 보존이다. 현재 어떤 새 모델도 안무 제품에 바로 교체할 만큼 검증되지 않았다.

[세 모델 비교 화면](http://127.0.0.1:58261/seeta-light-v1/index.html). 기존 탭을 재사용했다. 멤버 카드 → 해당 모델이 분류한 클립 → 고정 안무 메인 위치/원본 재생 → 같은 얼굴의 세 모델 판정을 볼 수 있다. 기존 실험 페이지·사용자 정답은 보존했다.

## 2. 같은 조건에서의 판정 결과

각 칸은 **정답 / 다른 멤버로 오확정 / 보류**다. 얼굴당 점수 1위와 실제 확정을 구분했다.

| 확인 자료 | SFace | AuraFace | SeetaFace Light |
|---|---:|---:|---:|
| 고정 안무 얼굴 34개 | 18 / 0 / 16 | 19 / 0 / 15 | **3 / 1 / 30** |
| 그중 식별 가능한 28개 | 15 / 0 / 13 | 17 / 0 / 11 | **3 / 1 / 24** |
| 다른 두 영상의 식별 가능한 19개 | 15 / 0 / 4 | 17 / 0 / 2 | **12 / 0 / 7** |
| 별도로 확인한 메인 2지점 | 1 / 0 / 1 | 0 / 1 / 1 | **0 / 0 / 2** |

추가 영상의 등록 멤버 23개 전체에서는 SFace 15/0/8, Aura 17/0/6, Seeta 12/0/11이다. 별도 등록 외 인물 5개와 얼굴 아님 1개는 세 모델 모두 이름을 붙이지 않았다. 신원 판단 어려움 5개도 모두 보류했으나 정답 거부로 세지 않는다.

개발 자료의 등록 멤버 128개 분모도 오류를 보존했다. SFace 59정답/0오류/69보류, Aura 34/0/93 + 정렬 실패1, Seeta 19/0/108 + 정렬 실패1이다. 이 숫자는 개발 자료에 문턱을 맞춘 결과여서 독립 정확도 수치가 아니다. 전체 개발 135행에서 정렬 실패는2개이며 다른1개는 이름 판단 어려움이다.

Seeta는 native34에서 SFace 기존 정답15개, Aura 기존 정답16개를 잃었고 어느 모델 대비도 새 정답 회복은0이다. 추가 식별가능19에서는 SFace 대비1개 회복/4개 손실, Aura 대비0개 회복/5개 손실이다. 총점만으로 개별 손실을 숨기지 않았다.

## 3. 구체적인 오류와 구간 판정

- **61.6616초 `s0043-p0-f3696`: 정답 혜인 → Seeta 하니.** 하니 cosine distance0.526437, 혜인0.674226. 개발에서 고정한 최대 거리0.556652를 잘못된 하니가 통과했다. 같은 얼굴에서 SFace는 보류, Aura는 혜인을 확정했다.
- `s0043-p0-r1`(59.4594–63.063초)은 하니 확정 얼굴6개가 모여 하니로 합의됐다. 그 결과는 기존 혜인 정답4지점과 모순된다. 이4개 정답을 주변 모든 프레임의 정답으로 전파하지 않았다.
- 전체 `s0043-p0`는 앞 경로의 근거가 부족해 보류였다. **전체 클립 오분류0처럼 보여도 내부 몸 경로 오분류는 남는다.** 얼굴·경로·최종 구간을 따로 확인해야 한다.
- 사용자 확인 메인105.105초 해린은 SFace만 확정, Aura/Seeta 보류.25.759초 다니엘은 SFace/Seeta 보류, Aura 해린 오확정이다.

고정35대상/37몸 경로의 이름 배정 수는 SFace16, Aura13, Seeta12다. 이는 정답 구간 수나 전체 구간 정확도가 아니다. 전체 구간 정답은 아직 없다.

## 4. 실제 모델 파일·라이선스·변환 확인

공식 [SeetaFace6Open 인덱스](https://github.com/SeetaFace6Open/index)가 연결하는 Dropbox에서 Light CSTA를 받았다. 제공자는 오픈 버전의 무료 상업·개인 사용을 명시하며 [BSD 2-Clause](https://github.com/SeetaFace6Open/index/blob/master/LICENSE)를 게시한다. 이 명시와 정확한 공식 배포 경로를 해당 파일의 근거로 연결했다. 코드가 공개돼 있다는 사실만으로 가중치 조건을 추정하지 않았다.

| 파일 | bytes | SHA-256 |
|---|---:|---|
| 공식 `face_recognizer_light.csta` | 4,730,388 | `10816905fd8d7b8857b2750db137383bdf99b4afc6fc5dc1648d26252043d0c9` |
| 제3자 `face_recognizer_light.onnx` | 4,714,634 | `2c29eb8743ddf09ce5d887520161eab0655728224119c935a37d898693c80bb2` |

합계9,445,022bytes로15MiB 상한 안이다. 공식 CSTA의 Git blob SHA-1이 변환 저장소 원본 미러 `1a6a23d95adcffbbfd660832c776ec0c608185e8`과 일치했다. ONNX도 고정 revision의 blob SHA-1과 일치한다. [변환 저장소](https://github.com/SeetaFace6Sharp/SeetaFace6Onnx)의 revision은 `3cefcf6896a2e7268add82ea89f720271a825157`, 코드 MIT이며 원래 Seeta 조건도 함께 지키도록 안내한다. 로컬 Python 경로는 C#/.NET/SkiaSharp를 도입하지 않는다.

공식 원본 설정을 직접 파싱해 `112×112`, BGR 채널 유지, 외부float32×0.003921568859368563, CHW,512차원, arcface 정렬 template을 확인했다. ONNX 실제 graph는 opset19, float32 `1×3×112×112 → 1×512`, Cast/Conv/Relu/Add/Reshape이다. 내부 중복 `/255` 연산은 없다.

공식 `FaceRecognizer6` revision `55506482e72bb14b3bb0df7a91249dceebb3ebaf`의 destination→source 최소제곱 변환을 사용했다. OpenCV bilinear inverse warp로 샘플링하므로 원래 TenniS sampler와의 완전한 픽셀 일치를 주장하지 않는다. 평가의 cosine 비교를 위해 출력은 L2 정규화했고 공식 similarity clipping/0.7 문턱을 가져오지 않았다. 모델·정렬·전처리·런타임·출력 정규화·정책은 별도 산출물로 분리했다.

원본 CSTA의 그래프를 읽는 검토된 NumPy 인터프리터와 ONNX를 랜덤 입력/실제 참조 한 장에서 대조했다. 최대 절대 오차는 각각7.93e-7/1.64e-6, 정규화 후 cosine 차이0이었다. 이는 **제3자 변환 구현 내부의 수치 일치 확인**이며 원래 native TenniS 런타임에 대한 독립적인 증명은 아니다. 제품 배포를 승인한 것으로 읽지 않는다.

## 5. 입력·정책·실행 상한

출력 루트:
`/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/seeta-light-v1/`

`plan.json` SHA-256: `70a8082bccdb65cd76fc3182a60bd582363b723cb5d99e636538c558373dc328`.

- 참조23장: 다니엘5/민지5/하니4/해린5/혜인4.
- 개발135행: 원래1080 자료 및 기존 사용자 export.
- native353행:309얼굴, 원래 연결 미확보44 보존.
- 추가 두 영상34행: 기존 사용자 확인 자료.
- 총545행, 정렬 가능한 실제 입력499개. 개발 `face-109`, `face-202`는 뒤집힌 눈/입 위치점으로 정렬 실패; 기존 Aura에서도 같은 실패였다.
- 원본 경로·SHA, 프레임/시간·ROI·bbox/5점, 원본 픽셀 hash, 모델에 넣는 tensor hash, 정렬 이미지 hash, 사용자 정답과 코드 hash605개를 실행 전 고정했다. 기존 detection/main/track/segment는 재추론하지 않았다.

native 원본: `main-face-57-63-diagnosis-v1/source-native4k.webm`,3840×2026, SHA`74e4769a59b0f73bf9e5f909549f441f38e95dc7691905c419bfdc52510d4013`.
개발 원본: W13 `runtime-preview/sources/youtube/yFTAYXDTjqI/source.mp4`,1920×1012, SHA`7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`.
추가 영상의 정확한 경로·hash·구간/프레임은 `input.json.sources`와 해당행에 있다. 선택 구간 전체의 새 모델 재추론을 한 것은 아니다.

판정은 centroid 한 종류다. 개발의 알려진 멤버128개 중 정렬 가능한127개에서 오확정0 조건 아래 정답 최대, 동률이면 작은 거리·작은 후보 차이 순으로 선택했다. 선택값은 최대 거리0.5566520094871521, 최소 차이0(정확 동점은 거부). `frozen-policy.json`을 저장한 뒤 native/추가 자료를 점수화했다. 새자료에 맞춰 다시 조정하지 않았다. SFace/Aura는 기존 저장값을 재사용해 새 ML0이다.

환경: Apple M4, macOS27.0 arm64, Python3.11.12, ORT1.24.4 CPU, OpenCV4.13.0.92, NumPy2.4.4, ONNX1.20.1, batch1, ORT내부스레드2/인터스레드1. 작업repo HEAD`47782953228861f4bdbdc135265d067c2a826b0e`; 새 실행 스크립트는 파일별 hash로 고정했다.

실제 forward **503회 = 입력499 + ORT 대조2 + CSTA NumPy 대조2**.600회 상한 안, worker12.80초/감독13.61초, RSS 피크222,756,864bytes(약212.4MiB). 입력 추출·hash 준비 최종27.01초는 추론시간과 별개다. 전체 대화/설계 시간도 이 숫자에 포함되지 않는다.

모델 생성28.62ms; warm forward+L2+ledger p50 1.93ms/p95 3.00ms. 디코딩/정렬 제외이며 기존 모델과 같은 타이밍 재시험은 하지 않았으므로 속도 우승을 주장하지 않는다. 새 패키지 설치0, 새 검출/pose/body모델0.

## 6. 검증과 시행착오를 포함한 실제 기록

1. 실제 graph checker, 색상/정규화 fixture, 동일·이동/확대 변환 fixture, 잘못된 위치점 거부를 확인했다. float32 공식 연산의 변환 오차1.125e-4px 때문에 synthetic fixture 허용치를2e-4px로 수정했다. ML 전 수정이며 실데이터에 맞춘 조정이 아니다.
2. preparation은 sysctl sandbox 제한으로 마지막 환경 기록에서 한 번 실패했다. 기존 crop을 byte 검증한 뒤 허용된 장치 조회로 다시 준비했으며 ML은0이었다.
3. 실행 전 독립 코드 검토로 정책 고정 전 extra 점수화를 제거하고, 원자적 partial checkpoint와 개발/평가 이유 분리를 추가했다.
4. ML503회와 정책 고정은 완료됐지만, **후처리 baseline Aura 실패명을 바꾸는 코드가 기존 `inference_error:1`을 중복 계산해 합계128 검사에서 종료코드1**로 끝났다. 기존 캐시에 오류가 누락됐다는 리뷰 지적은 재확인 결과 잘못이었다. 원 실행·log·정책·임베딩을 보존하고 `postprocess.py`에서 키를 옮기는 집계만 고쳤다. 새 ML0, 정책 hash·임베딩 hash 불변을 확인했다. 초기 worker 전체가 성공했다고 주장하지 않는다.
5. 독립 감사가 코드와 캐시를 새로 읽어 평가387행/개발135행,499벡터, 후보 거리·정책 선택·분모·35scope/37run을 재계산했다. 숫자 비교34,078건 차이0. 원래 개발/추가 정답, 고정 W13 scope, 입력605개 hash 보존을 확인했다. 이 검산 수는 모델 정확도 표본 수가 아니다.
6. UI 초기 JS 문법오류2곳을 수정한 뒤 `node --check`와 브라우저 실제 표시로 확인했다. 모델 선택, SFace 민지8클립 필터,25.759 다니엘/61.6616 혜인 판정, 원본 재생과27.293933초 종료, 짧은 선택 구간 seek, 깨진 이미지0을 확인했다. 최종 화면은 로컬 결과물이며 앱 제품 UI를 수정한 것이 아니다.

핵심 산출물: `downloads.json`, `license-provenance.json`, `static-inspection.json`, `plan.json`, `input.json`, `forward-ledger.jsonl`, `conversion-check.json`, `inference.json`, `supervisor.json`, `frozen-policy.json`, `postprocess-repair.json`, `result.json`, `independent-audit.json`.

## 7. 한계·남은 작업·소유권

- native34 라벨은 개발과 같은 프레임/인물이다. 다른 두 영상도 이미 여러 실험에 노출됐다. 새 모델의 일반화·낮은 오확정률을 입증한 자료가 아니다.
- exact main2는 해당시점 정답이며 인접 얼굴·전체 클립의 정답이 아니다. 이름 붙은35대상/37경로의 전체 정확도는 미검증이다.
- CSTA↔ONNX의 native TenniS 런타임/샘플러 일치, Windowsx64 및 깨끗한 Mac arm64 Electron 패키징, 서명/native 의존성/고지 번들은 미검증이다. 성능이 부적합한 이번 후보를 제품화하기 위해 이 비용을 쓰지 않는다.
- 기존 모델 점수를 같은 영상에 더 맞추는 문턱/사진 조합 반복은 종료한 결정을 유지한다. **다음 제품 교체 판단에는 현재보다 나은 인식 근거가 먼저 필요하다.** 다른 가중치가 개선되었다면 그 뒤 새 촬영자료의 독립 평가와 양쪽OS 배포 검증으로 넘어간다. 기존3영상 반복 정답만으로 교체하지 않는다.
- SeetaFace6의 큰 모델이나 다른 후보를 이 승인으로 추가 다운로드하지 않았다. 새 가중치는 파일/용량/라이선스/시간 범위를 별도로 구체화해야 한다. 현재 사용자에게 얼굴 이름 재작성·export·재생 확인을 요구할 사항은 없다.
- W14는 공통 얼굴 API·fixture·격리 평가, W13은 main/몸/구간/mapping/crop/안무 제품 adapter 소유다. 이번 core/publicAPI/W13/SDK/의존성/제품 모델 수정0, 새 W13 수락이나 다른 채팅 발신0, commit/push/merge/Build5 0.
- 향후 유효 후보가 나올 때만 공통 입출력/space·cache 계약 확인 → 소비자 compatibility test → 선택venv/모델 준비 → Mac arm64·Windowsx64 패키징 → 합의한 merge 순서로 진행한다. Mac Intel은 제외한다.
