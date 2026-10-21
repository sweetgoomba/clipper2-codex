# W14 — 영상 얼굴 입력 분리 진단과 기존 ArcFace의 동일 구간 비교

작성: 2026-10-13 KST. 사용자 「진행해」와 기존 반복 얼굴 추론 승인 범위에서 수행. Superpowers systematic-debugging / verification-before-completion에 따라 입력 고정 → 원인별 대조 → 별도 수치 재검산 → 화면 확인 순서로 진행했다.

**10/14 원인 정정:** 아래 후속 대상 중14/18의 보류는 멤버 충돌이 아니라 각각 지지 표본1개로 최소2개 미달이다. 실제 충돌은8/16에 있다.221얼굴 중169미매칭, 원본 얼굴 가로 중앙값41.5px,3/19의 추적 경로 표본 누락을 [재집계](14-w14-poor-result-diagnosis.md)했다. 저장 결과 불변·새 추론 없음.

## 1. 결론과 정확한 범위

- **클립10 개발 사례는 이번 ArcFace 시험에서 혜인으로 분류됐다.** 앞선 SFace 개별 표본 합의 방식은 확인 필요다. 사용자가 확인한 선택 메인의 이름은 혜인이다. 마지막 두 표본이 혜인 거리 기준을 통과하고 다른 멤버를 확정한 표본은 없어서 구간 이름이 붙었다.
- 같은 메인 몸·구간·선택 얼굴·참조 사진에서 인식 모델과 각 모델의 거리 기준을 분리해 비교했다. **앱의 모델은 YuNet/SFace 그대로**다. 이번 시험은 예전에 내려받은 ArcFace ResNet100 ONNX를 재사용했으며 새 다운로드·유료 API·YOLO/pose 추론은 없다.
- 원본 ROI/전체 프레임 좌표와 2배 확대만 바꾸는 SFace 대조로는 클립10을 해결하지 못했다. 2배 확대 재검출은 귀/머리 쪽으로 얼굴 위치가 옮겨지는 사례와 하니 오확정을 만들었으므로 기각했다.
- ArcFace 전체 대조는 저장된 **20구간·240시점·선택 얼굴221장**이다. 이름 배정은 SFace11 → ArcFace9, 확인 필요8 → 7, 미매칭0 → 3, 얼굴 없음1 → 1. **전체 정확도가 좋아졌다는 결론은 낼 수 없다.** 나머지19구간의 선택 얼굴 identity GT가 없으며 구간·몸 선택 자체도 최신 W13 결과가 아니다.
- 클립10은 이미 피드백과 후속 선택에 사용한 개발 사례다. 독립 평가/holdout으로 부르지 않는다. 마지막 2표본은 0.133초 간격의 인접 프레임이며 독립적인 증거 두 개가 아니다.

## 2. 비교 화면과 실행 파일

[새 SFace / ArcFace 비교 화면](http://127.0.0.1:58261/segments-v3/index.html). 처음 열면 ArcFace → 혜인 → 클립10 → 마지막 얼굴을 보여준다. 멤버를 누르면 그 모델의 해당 클립 목록, 클립을 누르면 원본 메인 상자·동일 얼굴·5명별 거리 근거를 확인한다. 모델 버튼은 클립 목록과 각 얼굴 판정을 함께 바꾼다. 기존 비교 화면은 보존했다.

로컬 출력 루트:

`/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/comparison-review-20261013/`

| 경로 | 내용 |
| --- | --- |
| `input-path-audit/clip10/` | 원본 ROI, 전체 프레임, 픽셀 확대, 확대 재검출 대조 |
| `input-path-audit/alignment-jitter/` | 112px 정렬 이미지의 ±2px 평행이동 민감도 대조 |
| `input-path-audit/arcface-control/` | 23참조·11얼굴의 별도 ArcFace 공간, 최초 기준 실패 및 후보 순위 대조 |
| `segments-v3/` | 같은20구간 두 모델 결과·공통 기준 산정 대조·브라우저 화면 |
| `input-path-audit/verify_replay.py` | 공통 매칭 함수를 사용하지 않는 float64 재계산 |
| `segments-v3/verification.json` | 3,315거리·75트랙 판정·60구간 조건 판정 재검산 결과 |
| `segments-v3/checks.json` | 실제 추론 횟수·시간·RSS·기존 SFace 벡터 재현 |
| `segments-v3/manifest.json` | 재실행 전에 고정한 입력·모델·코드 hash·구간·시점·상한 |
| `segments-v3/calibration-frozen-before-replay.json` | 두 모델별 참조 전용 기준의 계산 근거 |

`segments-v3`의 ArcFace 벡터는512차원, SFace는128차원이다. 참조/영상 벡터, gallery fingerprint, embedding space, threshold를 섞지 않는다. raw embedding은 로컬 평가 파일에만 저장한다.

## 3. 사전 고정 입력·모델·환경

원본: `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/runtime-preview/sources/youtube/yFTAYXDTjqI/source.mp4` — 1920×1012, fps60000/1001, 133.654059초.

| 입력 | SHA-256 |
| --- | --- |
| 원본 영상 | `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4` |
| 저장 MoveNet512 안무 face baseline | `d376886310728da8aa6209c5b54233026bd0e8711c0d381bb147430a94bb8164` |
| 저장 pose | `369e2fea3f04bee0a1158aa47d7988bb7f9a4b3cd95a9fe4e12eb5fd61a908d0` |
| 참조/증거 dataset | `f0446ba41ce18213983d6ab19d7d35ce4d037b1f2d32e1d6054d3fe84a2fa246` |
| 기존 SFace 참조23벡터 | `f0c06b3e49e953bb823f9dddb6d81c97df1f15749a4673e3036301056b4557a9` |
| YuNet 2023mar | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| SFace 2021dec | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |
| 기존 ArcFace ResNet100 ONNX | `f0a2e278b430372d308fef67c1aea308c2baf37f32e8908d9bfce035c26a3fb4` |

ArcFace 파일은 `.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-arcface-probe/arcfaceresnet100-8.onnx`(261,036,388 bytes)를 읽었다. 10/1의 Person 영상 군집 평가에서 제품 채택에 실패한 이력은 그대로 유지한다. 이번 과제는 고정된5명 참조와 Dance 메인 얼굴 매칭이므로 별도 대조다.

실행은 Mac CPU, OpenCV4.13.0 CPU backend/1thread, Python3.11.12, NumPy2.4.4. 정확한 OS 문자열은 각 manifest에 있다. 작업 branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` + 기존 미커밋 W14 파일의 개별 hash를 잠갔다. 제품/core 파일은 이번 단계에서 수정하지 않았다.

GT 범위: 사용자 확인상 클립10 선택 인물은 혜인이고 이전 표시5얼굴 중4개는 혜인이다. 이를 221개 전체 얼굴의 정답으로 확대하지 않는다. 기존 시간대별 desired-main 정답은 화면 문맥으로만 사용하며 실제 선택 얼굴 identity GT로 대체하지 않는다.

## 4. SFace 입력 경로 진단 — 해결되지 않은 접근도 보존

클립10 `[62.5291333333,64.1307333333)`의 같은11얼굴, 몸 track13을 고정했다. 앞선 pose 연결에서 보류한1시점은 새로 정답 처리하지 않았다.

| 조건 | 표본 판정 | 구간 판정 |
| --- | --- | --- |
| 저장 ROI/landmark 재현 | 혜인1·하니1·미매칭9 | 확인 필요 |
| 원본 전체 프레임으로 landmark 좌표만 이동 | 혜인1·하니1·미매칭9 | 확인 필요 |
| 2배 영상 확대 + 같은 landmark의 pixel-center 변환 | 혜인1·하니1·미매칭9 | 확인 필요 |
| 2배 검출 후 원본 좌표/픽셀로 매핑 | 하니3·미매칭7·연결 보류1 | **하니 오확정** |

ROI/전체 프레임 정렬 결과의 평균 픽셀 차이는 255스케일에서 약0.0003~0.0014 수준, 판정은 동일했다. ROI 재현11벡터는 기존 값과 일치했다. 확대 재검출에서는 옆얼굴109의 landmark 평균 위치가 약30.3px 이동하며 얼굴 앞쪽 대신 귀/머리 쪽을 선택하는 문제를 원본 crop에서 확인했다. 이 대조는 전체20구간으로 확장하지 않았다.

추가로 동일112×112 정렬 이미지11장에 x/y 각각-2,0,+2px의9조합을 적용했다. 새 검출/pose 없이 SFace99특징만 계산했다. 이는 합성 민감도 시험이다. 평균 특징으로도 혜인1·하니2·미매칭8로 확인 필요였고, **마지막 얼굴119는9/9이 하니를 더 가깝게 판정**했다. 단순 위치 흔들림 평균만으로 해결되지 않았다.

## 5. ArcFace 동일 픽셀 대조와 기준 결정 순서

1. 위 접근 실패 후 사용자에게 기존 로컬 ArcFace를 별도 대조로 확대한다고 알렸다. 모델 교체/제품 반영을 선언하지 않았다.
2. 참조23사진은 앞선 점검에서 저장한 lossless aligned PNG, query11장은 이번 ROI 재현의 lossless PNG를 사용했다. 동일112px 정렬 이미지에서 recognizer만 변경했다.
3. ArcFace 입력은 RGB float32 0..255 NCHW, 출력`fc1`512차원 L2정규화다. OpenCV의 [실제 alignCrop/feature 구현](https://raw.githubusercontent.com/opencv/opencv/4.13.0/modules/objdetect/src/face_recognize.cpp)과 [공식 Open Model Zoo 모델 명세](https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/models/public/face-recognition-resnet100-arcface-onnx/README.md)를 확인했다. ONNX Runtime으로 바꾸지 않았다.
4. **최초 참조 기준은 실패했다.** 자기 멤버를 모두 받아들이면서 다른 멤버 참조를 모두 거절할 분리점이 없었다(자기 거리 최대0.560802 > 다른 멤버 거리 최소0.536438). 이 결과를 `threshold-frozen-before-queries.json`에 보존하고 자동 이름 배정을 하지 않았다.
5. 그 후 별도 query-plan을 잠그고11장에 대해 후보 순위만 확인했다. 클립10 후반4장(116~119)의 가장 가까운 이름은 SFace에서 혜인1/하니2/해린1, ArcFace에서 혜인4였다. 이는 후보 순위이며 이때는 전부`not_calibrated` 결과였다.
6. 그 다음 후속 규칙을 택했다. 참조 사진의 다른 멤버 centroid 거리 최솟값에서1e-6을 뺀 값을 상한으로 하여 일부 자기 참조 미매칭을 허용한다. 동일한 산정 규칙을 **두 모델 각각**에 적용하고, 전체20구간 실행 전에 고정했다. 이 순서와 클립10 개발 사용 사실을 manifest에 명시했다.

| 참조 전용 기준 | SFace | ArcFace |
| --- | --- | --- |
| 거리 상한 | 0.5468149914 | 0.5364374055 |
| 자기 참조 통과 | 21/23 | 22/23 |
| 다른 멤버 참조 통과 | 0 | 0 |
| 영상·등록 외 인물 안전성 | 미검증 | 미검증 |

모든 참조를 사용한 기준 설정 내부 점검이므로0오배정 숫자를 독립 검증 성능으로 발표하지 않는다. 과적합/일반화 검증은 남는다. 최초 기준 실패를 지우지 않았다.

## 6. 같은20구간 결과

| 조건 | 이름 배정 | 확인 필요 | 미매칭 | 얼굴 없음 | 클립10 |
| --- | ---: | ---: | ---: | ---: | --- |
| 앞선 수정 SFace/0.60 | 11 | 8 | 0 | 1 | 확인 필요 |
| SFace/참조 기준0.546815 | 12 | 7 | 0 | 1 | 확인 필요 |
| ArcFace/참조 기준0.536437 | 9 | 7 | 3 | 1 | **혜인** |

구간·메인 몸·240시점·선택 얼굴은 모두 유지했다. 추론210장은 원본 프레임/같은 landmark로 lossless PNG를 다시 만들고 SFace도 재계산하여 **기존 저장 특징과 최대 차이0**을 확인했다. 클립10의11개 ArcFace 결과는 위 probe 값을 재사용했다. 따라서 새 ArcFace query 추론은210개다.

앞선 SFace 수정 대비8구간에서 판정이 바뀌었다:

- 6: 확인 필요→민지, 7: 확인 필요→혜인, **10: 확인 필요→혜인(개발 정답과 일치)**.
- 2·12·17: 하니→미매칭.
- 14: 하니→확인 필요, 18: 민지→확인 필요.
- 나머지12구간은 상태/이름 동일. 마지막20번 얼굴 없음도 보존.

이름을 잃은5구간이 오확정 회피인지 실제 recall 악화인지는 선택 얼굴의 독립 정답 전에는 구별할 수 없다. 특히 짧은12/17구간의 근거 부족과14/18구간의 충돌은 다음 진단 대상으로 보존한다. 바뀐8개를 개선8개로 세지 않는다.

클립10 최종 근거: ArcFace11표본 중119(63.9972667초, 혜인 거리0.495286)와118(63.8638초,0.520511)이 통과,9표본 미매칭. 116/117은 혜인이 최근접이지만 거리0.566971/0.555797로 상한을 넘는다. 최소 지지2, 다른 멤버 확정0으로 혜인이 됐다. 같은119의 SFace 결과는 하니0.489158 < 혜인0.578864였다. 서로 다른 모델의 점수 절대 크기를 직접 비교하지 않는다.

## 7. 실제 실행·상한·검증

각 단계 manifest는 추론 전에 입력/모델/코드 hash와 범위/상한을 저장했다. 파일별 exact 시점·bbox·모델경로는 manifest에 있다. 자원 감시는 CPU1thread, RSS4GiB 공통 상한이다.

| 실제 실행 단계 | 얼굴 검출 | SFace 특징 | ArcFace 특징 | 벽시계 초 | 최대 RSS bytes | 사전 시간/출력 상한 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| clip10 입력4조건 | 11 | 43 | 0 | 2.229 | 625098752 | 240초/250MiB |
| clip10 ±2px9조건 | 0 | 99 | 0 | 1.325 | 299188224 | 120초/50MiB |
| ArcFace 참조 | 0 | 0 | 23 | 3.230 | 1733132288 | 180초/100MiB |
| ArcFace11얼굴 순위 | 0 | 0 | 11 | 2.310 | 1744027648 | 180초/100MiB |
| 동일20구간 후속 | 0 | 210 | 210 | 43.133 | 1941094400 | 300초/250MiB |

합계 YuNet11, SFace352, ArcFace244 호출. pose0, 새 모델 다운로드0, 유료API0, 제품 빌드0. 실험 횟수와 얼굴 특징 호출 개수를 구분한다. 첫 대조는 상한44특징 중 확대검출 한 시점 연결 보류로 실제43개다.

사전 manifest SHA:

- 입력 대조: `0c2f621abb1b29f78ad8f809b4b6fe1a19ab01d0564d589f1a63d1979fa01134`
- 위치 흔들림: `62b64fffc7f4e954124da84fe773e86e1fc278526917dacf1760d0bd6ae7aacc`
- ArcFace 초기: `9561ec09e91748a3fdc87963f2a47252d1aa397f3c827c4e36dc3005f88bdb76`
- 20구간: `06c188678d648594d4667908ed116f0b44476625591bcf2c84b0ca4ba6910e2c`
- 참조 기준 freeze: `83ed43a95f6895f05c889c0f9f575e719a9fd307a2cd8b7ae5772f282211c8d6`

**이번에 실제로 통과한 검증:**

- 공통 matching/consensus 함수를 호출하지 않는 NumPy float64 별도 계산:221얼굴×5멤버×3조건=3,315거리, 트랙25×3, 구간20×3의 모든 판정 일치. 최대 거리 오차9.57e-8미만.
- 입력240시점·frame index·ROI·landmarks·선택 face index·track·전체구간 정보 이전과 동일. SFace210재생성 벡터 최대차이0. 서로 다른 model space fingerprint 확인.
- 참조 기준의 LOO 자기 비교/다른 멤버 거리·통과 수 별도 재현. 전체221 ArcFace/128D SFace 차원·finite·정규화 확인.
- 화면486개 이미지 참조 파일 존재. 브라우저에서 멤버 필터, SFace/ArcFace 전환 후 표본·점수 변경, 미매칭2/12/17목록, 얼굴 없는20번 보존, 원본1920×1012 재생과 선택 끝64.11405초에서 자동 정지 확인.
- 수치 검산의 첫 출력 시 NumPy int64 JSON 직렬화 오류가 있었고, Python int 변환 후 새 검산 전체를 실행해 통과했다. 모델 추론 재실행은 없다.

최종 산출물은 `segments-v3/artifact-manifest.json`에 두 신규 폴더312파일/13,654,203bytes를 잠갔고 전 파일 SHA를 다시 확인했다. manifest SHA는 `d0b5447505734f0e4108a835fadc77dfa610ee5bceaa4e7b9a7765808a7b9472`다. `browser-verification.json`에 실제 UI 관찰을, `proof-summary.png`에 native 화면을 보존했다. 전체 페이지 캡처는 브라우저 stitching/레이아웃 아티팩트가 있어 `proof-clip10.png`를 주 증거로 사용하지 않는다. 브라우저 표시 요청은 Codex에서 queued로 반환됐으며 링크와 deliverable 탭을 남겼다.

이전73/82/633개 pytest 숫자는 이번 실행의 새 테스트 결과로 재사용하지 않는다. 이번은 격리 평가 스크립트·비교 UI를 만들었으며 제품/core 동작은 바꾸지 않았다. 위 재현 검증과 실제 identity 품질 검증을 구별한다.

## 8. W13 인계·다음 작업

파일 소유권과 merge 순서는 유지한다: **W14 공통 API → 두 소비자 compatibility fixture → W13 main/mapping/crop adapter 소비**. 이번의 실험 runner나 ArcFace 모델/기준을 W13에 자동 이식하지 않는다. 별도 세션 생성·메시지·W13 파일 수정·merge/push는 없다.

공통 모듈은 두 embedding 공간 모두를 같은 공개 gallery/match/consensus API로 비교했다. ArcFace 채택 여부와 optional backend/venv·모델 준비·Windows/한글경로·Electron fingerprint의 제품 구현은 아직 하지 않았다. 기본 SDK import에 ML을 추가하지 않는다.

다음 판단에 남은 입력/검증:

1. 클립10을 제외한 실제 선택 얼굴의 identity/불명확 라벨. 사용자 desired-main 정답과 선택된 사람의 정답을 분리해 다른 멤버 오배정·미매칭을 채점한다.
2. 특히2/12/17의 미매칭,14/18의 충돌과6/7 신규 배정의 원인. 현재 출력은 사람이 검토할 수 있도록 보존했고 이름 수만으로 기준을 완화하지 않는다.
3. 여러 영상·참조 갤러리와 미등록 인물에서 threshold를 개발/독립 평가로 분리 검증. 근접 표본2개 지지의 시간적 독립성과 얼굴 소유 오류에 대한 강건성 확인.
4. 후보가 실제 오배정/미배정 gate를 통과한 뒤 최신 W13 선택 결과에 계약 fixture로 연결. main 선택·구간 분리 개선은 W13 경계다.

현재 판정: **SFace 입력 확대/위치 평균 대안 기각. 기존 ArcFace는 클립10 개선을 보인 후속 후보이며 제품 채택/전체 성능 검증은 미완료.**
