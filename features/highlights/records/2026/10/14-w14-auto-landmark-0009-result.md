# W14 자동 얼굴 정렬 0009 비교 — 일부 회복, 전면 적용 보류

작성: 2026-10-14 KST. 사용자 “진행해줘”로 승인한 자동 위치점 비교 실행 기록.

## 1. 쉽게 말한 결론

얼굴 사진을 비교하기 전에 눈·코·입을 같은 위치로 맞추는 과정이 있다. 이번에는 얼굴을 새로 고르거나 인식 모델을 바꾸지 않고, **그 다섯 위치를 찾는 모델만 YuNet의 출력에서 Intel 0009로 바꿨다.** 등록 사진 23장도 같은 방식으로 다시 처리했다.

- **좋아진 부분:** AuraFace가 오래 해결하지 못한 57–63초 대상을 혜인으로 배정했다. 앞 몸 경로에서 혜인으로 받아들인 얼굴은 0→8개, 뒤 경로는 28→30개다. 두 경로가 각각 혜인을 지지한다. 기존 13개 클립 대상의 이름도 유지하고 3개를 추가했다.
- **남은 문제:** 다른 영상에서 기존에 맞힌 해린 얼굴 2개를 더 이상 확정하지 못했다. 그 두 얼굴은 가장 가까운 후보도 혜인으로 바뀌었다. 또한 사용자가 다니엘로 확인한 25.759초 얼굴을 해린으로 확정하는 오류는 그대로다.
- **SFace에는 전체적으로 불리했다:** 기존 얼굴 정답 34개에서 정답 확정이 18→15, 다른 영상의 식별 가능한 19개에서는 15→14로 줄었다. 클립 이름 수가 16→17인 것만 보면 이 손실을 놓친다.

따라서 **0009를 모든 입력에 적용하거나 AuraFace를 제품 기본값으로 교체하지 않는다.** 일부 구간의 개선 근거는 확보했지만, 얼굴 매칭 문제 해결과 제품 적용을 마친 상태는 아니다. 현재 사용자에게 추가 라벨이나 확인을 요구하지 않는다.

[전후 비교 화면](http://127.0.0.1:58261/auto-landmark-v1/index.html): 인식 모델 선택 → 멤버 카드 → 클립 → 얼굴을 누르면 기존/새 위치점, 실제 모델 입력 사진, 후보별 거리를 볼 수 있다. 아래에는 다른 두 영상의 34개 확인 얼굴도 모두 표시했다.

## 2. 고정한 입력과 달라진 것

| 항목 | 실제 조건 |
|---|---|
| 안무 입력 | 기존 W13 40B 스냅샷의 35메인 대상/37몸 경로, 353관측. W13의 최신 작업을 다시 실행하거나 수정하지 않음 |
| 원본 | 기존 native 3840×2026 영상. 화면 재생은 기존 1920×1012 표시본, 분석 픽셀과 구분 |
| 추가 영상 | 사용자 제공 `6bVUjsUi9sw`, `J9DlrnNlgfE`의 저장 1920×1080 얼굴 34개 |
| 참조 | 원래 등록 사진 23장/5멤버. 이후 시험했던 추가 8개 참조는 이번 비교에 쓰지 않음 |
| 유효 입력 | 참조23 + 안무309 + 추가34 = 366. 안무의 원래 얼굴 미확보44도 결과에서 보존 |
| 변경 | 같은 bbox의 tight integer crop → 0009로 5점 추정 → 원본 좌표 복원. 참조와 영상 양쪽 모두 적용 |
| 고정 | 선택 얼굴/bbox/source/frame/association/main/경로/구간, SFace·Aura 가중치, 각 인식 모델의 정렬 template·전처리, 기존 거리·후보차이·support 기준, 몸 경로별 합의 |
| 적용하지 않은 것 | 시간순 DP, 참조8장 보충, 모델 간 voting/veto, 실패 fallback, threshold 튜닝, 인물/클립 숨김 |

410행 전체를 기록했다. 새 결과에서는 44개가 `upstream_unavailable`; 새 landmark/recognizer 오류는 0. 검출/연결 단계의 실패를 모델의 정상 미매칭과 구분한다.

원본/모델/참조/코드/정답/기준의 정확한 파일 경로·해시는 [plan.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/plan.json)의 88개 입력에 잠갔다. plan SHA-256: `7023f65acda69a25bae6b18a2b1d227ffa05ddd73347f26ecabc88e828212d02`. 정답은 추론·표본 선택·threshold 결정에 넣지 않았다.

## 3. 모델 파일·라이선스·정렬 계약

정확한 신규 모델은 `landmarks-regression-retail-0009`, OMZ `2023.0/models_bin/1/.../FP32`의 XML/BIN이다. 얼굴 인식 모델이나 Intel Mac 지원을 뜻하지 않는다. 이번 실행 장비는 Apple Silicon이다.

- 공식 저장소 고정 revision: `af810de42bcf460a18610481f639dcdc86249e69`.
- XML 43,654 bytes, SHA-256 `636c547fd4d784d81be1be7bafc6376396aae60fa8e91664566ddc562f993f2c`.
- BIN 762,464 bytes, SHA-256 `0700711ab6d1a738cc16fafda2b040de8e9e0cc8b13430ee3ddd6abbe8c81969`.
- 두 파일의 SHA-384가 공식 `model.yml`과 일치. 해당 manifest는 Apache-2.0 LICENSE로 연결되며 원문을 저장했다. 앱 전체 패키징 의무/제3자 라이선스 검증 완료라는 뜻은 아니다.
- [공식 파일 manifest](https://github.com/openvinotoolkit/open_model_zoo/blob/af810de42bcf460a18610481f639dcdc86249e69/models/intel/landmarks-regression-retail-0009/model.yml), [공식 추론 예제](https://github.com/openvinotoolkit/open_model_zoo/blob/af810de42bcf460a18610481f639dcdc86249e69/demos/face_recognition_demo/python/landmarks_detector.py), [download-receipt.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/download-receipt.json).

입력은 원본 bbox를 공식 예제처럼 두 모서리 각각 정수 변환·화면 내 clip한 crop. `cv2.INTER_LINEAR` 48×48, raw BGR float32 NCHW `1×3×48×48`; 외부 RGB 변환이나 `/255`를 중복 적용하지 않았다. 실제 XML의 내부 전처리 metadata도 확인했다. 출력 `1×10×1×1`의 정규화 5점을 **실제 잘라낸 정수 crop의 원점/폭/높이**로 원본 좌표에 돌린다. 좌우 순서·유한값·범위·퇴화 검사를 하고 재정렬/값 자르기/fallback은 하지 않는다.

기존 SFace와 Aura의 인식 template·크기·색상/정규화는 유지했다. 새 정렬의 space fingerprint에 0009 hash/전처리 버전을 반영하고 **같은 새 공간으로 참조23과 query를 모두 재생성**했다. 같은512차원이라도 타 모델이나 이전 정렬 캐시와 비교하지 않았다. 기존 threshold를 그대로 쓴 이유는 통제 진단이며 **새 정렬용 제품 threshold가 검증됐다는 뜻이 아니다.**

## 4. 실제 결과 — 분모를 나눠 읽기

| 평가 항목 | SFace 기존→0009 | AuraFace 기존→0009 |
|---|---:|---:|
| 기존 안무 얼굴 정답34: 올바른 확정 | 18→15 | 19→21 |
| 같은34: 잘못된 멤버 확정 | 0→0 | 0→0 |
| 같은34: 미확정 | 16→19 | 15→13 |
| 별도 사용자 메인 확인2: 정답/오답/보류 | 1/0/1→2/0/0 | 0/1/1→0/1/1 |
| 추가 영상 등록멤버23: 정답/오답/보류 | 15/0/8→14/0/9 | 17/0/6→15/0/8 |
| 그중 식별 가능한19: 정답/오답/보류 | 15/0/4→14/0/5 | 17/0/2→15/0/4 |
| 안무 대상35: 이름 배정 | 16→17 | 13→16 |
| 기존 배정 손실 / 새 배정 / 기존 이름 변경 | 2 / 3 / 0 | 0 / 3 / 0 |

추가34의 나머지는 등록 외 인물5, 판단 어려움5, 얼굴 아님1이다. 두 모델의 기존/새 모두 이름을 확정하지 않았다. 얼굴 아님은 비얼굴 거부로, 신원을 모르는5개는 정답 판정 불가능으로 따로 계산했다. 흐린 표본의 보류를 인식 개선으로 세지 않는다.

34개 안무 얼굴 정답은 이전 사용자 라벨에 동일 프레임/유일 bbox overlap으로 연결한 것이며 새 crop 자체를 전부 다시 라벨링한 것은 아니다. 별도2개는 사용자가 원본의 메인 인물을 확인한 답변이고 crop 단독 식별가능 GT가 아니다. 이를34에 합산하거나 주변/전체클립 정답으로 전파하지 않았다.

### 달라진 안무 대상

- SFace 추가: clip15 하니, clip29 해린, clip52 하니. 손실: clip6 민지, clip51 민지. 새 얼굴 정답은2개 회복/5개 손실이다.
- Aura 추가: clip6 민지, clip42 민지, clip43 혜인. 얼굴 정답은3개 회복/1개 손실이다.
- **대상에 이름이 생긴 수는 정답 클립 수가 아니다.** 부분 정답34+별도2에서 새 scope/run 이름 모순은 모두0이나 미라벨 시점과 클립 전체는 검증되지 않았다.

### 그대로 남거나 악화한 핵심 사례

1. **25.759초 다니엘**: Aura는 해린 확정을 유지한다. 해린 거리0.5245→0.4862, 다니엘0.6036→0.5797. 순위가 바뀌지 않았고 잘못된 후보와의 차이도 커졌다. SFace는 다니엘1위의 차이가0.1209→0.1515로 벌어져 보류→다니엘이 됐다. 같은 구간 내 개별 얼굴 오류가 최종 구간 보류에 가려질 수 있어 얼굴/경로/구간을 따로 평가한다.
2. **105.105초 해린**: SFace는 전후 모두 해당 얼굴을 해린으로 확정. Aura는 해린1위를 유지하지만 여전히 보류다. 구간 합의와 개별 얼굴 판정은 다르다.
3. **추가 영상95.028초·140.007초 해린**: Aura가 원래 해린으로 확정하던 두 얼굴의1위가 혜인으로 바뀌며 보류. 95초의 새 혜인0.5490/해린0.5511,140초 새 혜인0.5487/해린0.5733이다. 거부 기준만 완화하면 잘못된 멤버를 확정할 위험이 있어 완화하지 않았다.
4. **혜인57–63초**: 앞/뒤 경로가 각각 혜인8개/30개 근거를 얻어 최종 혜인. 일부 관측은 여전히 미확정/연결보류. 앞 경로의 정답 확인3512는 거리0.615536으로 고정 기준0.616395에 가깝다. 다른7개 근거도 있으므로 그1개에만 의존하는 배정은 아니다. 전체클립을 새로 사용자 확인한 것은 아니다.

정확한 각 ID/시각·전후 상태·회복/손실 목록: [scores.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/scores.json). 원본 추론 결과는 [sface/result.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/sface/result.json) / [aura/result.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/aura/result.json).

## 5. 실제 실행과 검증

장비: Apple M4, RAM24GiB, macOS27 arm64, Python3.11.12. 기존 격리 uv 평가환경의 NumPy2.4.4/OpenCV4.13.0.92/ORT1.24.4/OpenVINO2026.4.1 사용. 의존성 설치·업그레이드 없음. Windows 실행/배포 검사 아님.

| 단계 | 실제 모델 호출 | worker 본문 시간 | 프로세스 최고 RSS |
|---|---:|---:|---:|
| 0009 OpenVINO CPU | 366 | 23.40초 | 450,969,600 bytes |
| SFace OpenCV CPU | 366 | 24.32초 | 493,338,624 bytes |
| AuraFace ORT CPU | 366 | 45.69초 | 1,538,310,144 bytes |

총 새 ML 호출 **1,098회**. 각 단계 CPU1thread/batch1,10분/4GiB,산출물250MiB 상한 감시. 세 감독 결과 exit0, 상한 초과0. 시간에는 해당 worker 내부의 모델 로드·원본 decode·crop 저장·후처리가 들어가며 시작 전 import/입력hash 확인은 제외된다. 반복 평균/순수 추론 벤치마크/cold-start 보장으로 읽지 않는다.

검증:

- 공식 모델2파일 SHA-384,88개 잠금입력 hash 재확인.
- crop/좌표/전처리/중간 provenance의 TDD 및 기존 adapter/run 합의 회귀 포함 **62tests 통과**. 코드 테스트가 얼굴 정확도 검증을 대신하지 않는다.
- 새 중간 결과는 plan SHA,410개 ID의 중복·완전성,kind,upstream 상태,원본 bbox→bounds,raw output→source points,참조 실패 목록을 검사. 인식 worker 시작/끝 intermediate SHA 고정,원본 crop 픽셀도 검사.
- 독립 검산에서 모델당 참조23→5centroid,366저장 embedding,387query(44upstream포함),1,715거리,35scope/37run의 최종 상태·이름·reason·margin 일치. 두 모델 총3,430거리 최대오차0.
- 기존 native353×2의 match 핵심필드706개 재현. 추가34×2는 기존 후보 거리/순위68개를 재생했으며 **기존 최종 결정 전체 재현이라고 쓰지 않음**.
- 실제5점 오버레이/참조·문제 query를 시각 확인. 사용자 정답을 새로 생성하지 않음.
- 브라우저: 모델 전환,멤버→클립,혜인회복 얼굴,다니엘오류,추가영상회귀,정렬이미지/원본재생 확인. 영상57.257→62.684초 진행,이미지로드오류0. [screenshot.png](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/screenshot.png).

검산/검증 원문: [independent-audit.py](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/independent-audit.py), [independent-audit.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/independent-audit.json), [verification-receipt.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/verification-receipt.json), [ui-receipt.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/ui-receipt.json).

### 사전/사후 검토에서 바로잡은 것

실행 전 cached 후보의 tuple/list JSON 표현과 설치 distribution명(opencv-python vs headless) 때문에 준비 검증이 멈춘 두 시도가 있었다. 새 모델 추론 전에 수정했고 원문은 [preparation-failure.txt](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/auto-landmark-0009-v1/preparation-failure.txt)에 보존했다. 독립 사전 검토에서 중간 landmark 결과의 provenance 검사가 부족해 실패 테스트→수정→재잠금했다. `preflight-v1-*`을 남겼으며 실제 모델 실행은 새 plan 한 벌만 사용했다.

사후 채점 리뷰에서는 ‘얼굴 아님’을 단순 신원불명으로 계산하는 표현 문제를 발견했다. 별도 `false_face_accept`/`nonface_rejected`와 regression test를 추가했다. 현재 실제 해당1건은 모두 거부여서 정답/오답 숫자 영향은 없다. 모델 입력/추론/threshold는 바꾸지 않았다.

## 6. 결정·후속·소유권

**결정:** 0009 일괄 적용 미채택, Aura 모델 제품교체 보류. SFace 기존경로는 기준선으로 유지한다. 0009는 혜인 개선 가능성을 가진 실험 후보로 보존한다. 정확한5점 정답을 확보한 것은 아니므로 “위치점 자체가 더 정확하다”까지 입증한 것도 아니다.

**다음 작업의 초점:** 새 모델 후보를 늘리기보다, (a) 개선된 혜인과 악화한 해린의 원본/기존·새5점/참조 변화를 나란히 분해해 어떤 입력에서 정렬이 유리·불리한지 확인하고, (b) 양쪽 정렬에서 남는25.759초 다니엘→해린은 인식/참조 증거 문제로 별도 다룬다. 현재 자료에서 성공한 정렬을 정답 보고 얼굴별로 고르는 oracle 선택이나 threshold 완화를 제품규칙으로 쓰지 않는다. 후속 비교도 사전조건과 회귀 사례를 고정해야 한다.

**제품 연결 전 남음:** 새 정렬용 기준의 개발/촬영단위 분리 평가,독립 메인·구간 정답,새로 배정된/기존 배정 전체 검증,여러 참조 구성의 안정성,Mac arm64와Windows x64 패키징·런타임·제3자 고지,실제 소비자 호환. macOS Intel은 지원 범위에서 제외한다.

W14는 공통 얼굴 API·평가·fixture를, W13은 main/몸추적/구간/mapping/crop·제품 adapter를 소유한다. 공통 공개 API에 Dance 구간/UI/job를 넣지 않았고 이번에는 독립 평가 artifact만 추가했다. 기존 공통 core/API/제품/W13 코드·의존성·사용자 정답/편집을 보존했다. 기본 SDK ML import나 모델 다운로드 경로도 바꾸지 않았다.

상호 계약확인→source/time/좌표/scope/failure/space compatibility→선택 venv·모델준비·consumer adapter→Mac arm64/Windows x64 검증→합의된 merge 순서가 남는다. 새 W13 수락이나 제품연결을 수행했다는 뜻이 아니며, 다른 채팅 발신/새 채팅 생성/commit/push/merge/Build5는 없다.

작업 경로: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/desktop/clipper_python`. branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`. 기존 격리 checkout을 재사용했으며 이번에 origin fetch나 rebase를 하지 않았다.
