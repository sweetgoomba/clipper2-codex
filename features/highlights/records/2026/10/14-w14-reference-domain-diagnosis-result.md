# W14 — SFace 보류 원인·영상 참조 영향 진단

2026-10-14 KST. **이번 시험도 제품 개선안으로 채택하지 않는다.** 자동 영상 참조는 혜인 참조를 확보하지 못해 오확정이 늘었다. 사용자 답변으로 만든 참조는 같은 영상의 일부 얼굴 구별을 개선했으나 다른 촬영 영상에서 악화됐다. 모델·얼굴 위치를 고정해 참조 영향과 거부 원인을 좁힌 진단 결과이며, 제품 정확도 개선 완료가 아니다.

- [얼굴·실제 참조 사진 비교](http://127.0.0.1:58261/reference-domain-v1/index.html)
- [계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/docs/superpowers/plans/2026-10-14-reference-domain-diagnosis.md)
- [입력 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/manifest.json) / [전수 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/result.json) / [독립 검산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/verification.json)
- [테스트](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/tests.log) / [독립 리뷰·판정](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/review.json) / [UI 검증](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/ui-verification.json) / [화면](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/reference-domain-v1/review-screen.png)

## 1. 실행 범위와 입력

- 기존 격리 branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`. 평가 helper/runner/test/audit/보고서와 요청된 문서만 변경. 공통 public core/API, 제품 adapter, W13 main/mapping/crop, 기존 입력·GT·결과 보존. commit/push/새 채팅/다른 세션 메시지 없음.
- 새 ML 추론 **0회**. 새 모델 다운로드/설치/API/Build5 없음. 저장 SFace 128차원 특징만 재계산. Apple M4/macOS27 arm64/Python3.11.12/NumPy2.4.4. 처리 시간·RSS 제품 벤치마크는 이번에 측정하지 않았다.
- SFace `face_recognition_sface_2021dec.onnx`, SHA256 `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`; 기존 YuNet 5점/SFace 정렬·BGR·L2 normalization·1-cosine 유지. 다른 모델 특징과 혼용하지 않았다.
- 원본 `yFTAYXDTjqI/source.mp4`, 1920×1012, 133.654059초, 60000/1001fps. SHA256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`. 프레임에서 유도한 시간이며 새 PTS 검증 주장은 하지 않는다.
- 기존 사용자135답변(알려진 멤버128/그중 식별가능102), 최신 W13 iteration27 연결 평가161행(기존 정답과 같은 프레임·얼굴 위치 연결34/식별가능28), 추가 두 영상15행(멤버7/등록외2/판단어려움5/비얼굴1). **311행을 3조건 모두 보존**. 기존/최신 자료는 같은 영상으로 상관돼 있어 독립 사례처럼 합산하지 않는다.
- 추가 영상 `J9DlrnNlgfE`, `6bVUjsUi9sw`: 이전에도 결과를 본 표본 재사용이며 새로운 블라인드 평가가 아니다. 혜인·하니 정답 없음. 사용자 얼굴 GT를 track/구간 전체 정답으로 전파하지 않았다.
- manifest SHA256 `0ea21ca82cf5ed491cd777b5da9840729d909360a9458afe2e8b002761da54a1`. 20 입력/계획/실행 코드 해시 고정. parent 최신/추가영상 manifest 연결. 원본 GT SHA256 `684cbd4d1a40904e64b43b9b9efeeaad52a94e7dafebee1a7ecfd2f4399b2aec`.

## 2. 미리 고정한 조건

1. **등록 사진**: 기존23사진 평균 centroid.
2. **자동 영상 참조**: 원래 등록사진 기준의 거리·후보차이 gate를 통과한 원본 영상 얼굴. 사용자 인물/식별가능 답변을 선정에 사용하지 않으며 반복 자가학습도 없다.
3. **확인된 영상 참조**: 사용자가 이미 인물 및 식별가능=yes로 답한 원본 영상 얼굴. 수동 정보가 들어간 진단 대조군으로, 자동 인식 성능으로 보고하지 않는다.

각 멤버·1초 bucket에서 중앙에 가까운 얼굴 1개를 선택(동률 ID), 평균 후 L2 정규화한다. 영상 참조가 없는 멤버도 경쟁 후보에서 빼지 않고 등록사진 centroid를 유지한다. 원본 영상 query는 해당20초 block 및 앞뒤5초의 모든 얼굴을 ID와 관계없이 참조에서 제외한다. 추가영상 query의 참조는 원본 영상에서만 가져온다. 각 gallery 구성·ID·fallback을 저장했다.

기존 최대거리0.7239670157432556/최소후보차이0.13533276319503784를 고정 적용했다. **새 참조에 보정된 배포 threshold가 아니며 민감도 비교**다. 이번 얼굴 단위 실험에서 구간 합의/최소지지 조건은 바꾸지 않았다.

## 3. 실제 결과

### 최신 안무 메인 얼굴: 연결된 멤버 정답34개

| 참조 | 점수1위 정답 | 정답 확정 | 다른 멤버 오확정 | 보류 |
|---|---:|---:|---:|---:|
| 등록 사진 | 28/34 | 9 | 0 | 25 |
| 자동 영상 참조 | 22/34 | 17 | 3 | 14 |
| 확인된 영상 참조(수동 진단) | 28/34 | 18 | 1 | 15 |

- 식별가능28개 점수1위 정답:24→17→24. 확정 정답9→14→17, 오확정0→3→1.
- 혜인10개: 등록사진 점수1위7/확정0, 자동 점수1위0/정답확정0/오확정3, 수동 점수1위7/정답확정3/오확정1.
- 나머지127행은 인물 정답이 없어 정확도 분모에서 제외하되 결과 목록에 남겼다. 이 중32개는 얼굴 연결 보류(`unavailable`)이며 모델 처리 오류가 아니다. 실제 inference/alignment 오류0.

### 기존 사용자 확인 얼굴: 멤버128개

| 참조 | 점수1위 정답 | 정답 확정 | 오확정 | 보류 |
|---|---:|---:|---:|---:|
| 등록 사진 | 93/128 | 58 | 0 | 70 |
| 자동 영상 참조 | 95/128 | 72 | 9 | 47 |
| 확인된 영상 참조(수동 진단) | 115/128 | 75 | 2 | 51 |

식별가능102개 점수1위 정답82→79→95. 수동 참조의 같은 영상 회복 효과는 있지만 최신34에서 순위 총량 개선이 없고 오확정이 생겼다. 원본 멤버외7행(미입력2/판단어려움5)도 보존했으며 이들의 배정을 정답으로 세지 않았다.

기존 낙관적 threshold 개발 결과59확정과 이번58확정의 차이는 `face-010` 경계값이다. 재정규화된 거리0.7239670753479004가 threshold0.7239670157432556보다 약5.96e-8 크다. 같은 nearest이며 품질 변화로 해석하지 않는다. `extra-segment-03-3-884`의 margin도 threshold와 같아 수치 경계로 기록했다. 기준 조정으로 이 표본을 맞추지 않았다. 최신9개/추가영상5개 baseline 확정은 이전과 그대로 일치한다.

### 다른 두 촬영 영상: 멤버7개

| 참조 | 점수1위 정답 | 정답 확정 | 오확정 | 보류 |
|---|---:|---:|---:|---:|
| 등록 사진 | 6/7 | 5 | 0 | 2 |
| 자동 영상 참조 | 7/7 | 3 | 0 | 4 |
| 확인된 영상 참조(수동 진단) | 5/7 | 2 | 0 | 5 |

등록외2/비얼굴1/판단어려움5는 세 조건 모두 보류했다. 7개로 일반화나 낮은 오확정률을 보장하지 않으며, 새로운 영상의 개선 근거는 얻지 못했다.

## 4. 실패 원인 분리와 판단

- 최신34 baseline: 정답이 점수1위인28개 중9확정,18개는 후보차이만 부족,1개는 거리·차이 모두 부족. 다른 멤버가 점수1위인6개는 후보차이만3/거리·차이 모두3으로 모두 보류.
- 거리 gate 유지·후보차이 gate만 제거한 진단은 **정답9→27, 오확정0→3, 보류25→4**. 단순 기준 완화로 두 목표를 함께 해결하지 못해 미채택.
- 자동 참조는 모든 시간 분할에서 혜인0개였다. 추가영상용 전체 원본 참조 수: 다니엘20/민지23/하니25/해린18/혜인0. 혜인은 등록사진 fallback을 유지하는 동안 다른 멤버만 영상에 가까운 참조를 얻었다. 최신 혜인 순위가7/10→0/10으로 악화돼 무조건 자동 확장이 위험하다는 실제 사례다. 이것을 모든 실패의 유일한 원인으로 단정하지 않는다.
- 수동 참조는 전체 원본 기준16/13/17/15/12개이나, 원본 query block 제외 뒤 혜인 참조가2개만 남는 구간도 있다. 예:58.258초 혜인 얼굴은 수동 참조에서도 해린 오확정. 참조가 올바른 인물이라는 사실만으로 촬영 조건/각도/특징 분리 문제가 해결되지 않는다.
- 같은 영상에서 일부 순위 회복은 등록 사진과 영상 얼굴의 차이가 영향을 준다는 근거다. 다른 영상의 악화 때문에 일반 개선 또는 수동 참조 도입 성공이라고 말할 수 없다.

## 5. 검증과 시행착오

- 관련 테스트178개 통과(0.53초). 새8개 회귀는 RED→GREEN 확인: 시간 제외, 다른source, 정답비사용 자동선정, 실패/불명확 anchor 제외,1초 균형, 멤버 fallback, 알려진/unknown 분모, 연결보류와 오류 분리.
- 별도 float64/scalar 검산4,185거리, 최대차1.313914107514691e-7,21gallery,311×3행, seed/fallback/time 제외/분모/판정 확인. 기존406얼굴 ranking 재현. 20입력 hash 일치.
- 독립 리뷰: Critical/Important/Minor 지적0, 제한된 진단 수용·미채택 결론. identity GT 자체/새영상 일반화/제품통합은 검증 범위 밖. 부모가 실제 브라우저 렌더링, 세조건 참조사진, 필터·빈상태, 회복/악화사례를 확인했다.
- 초기 캐시 로더는24중복ID에서 **점수 계산 전에 중단**했다. 이전 main-owned-face 수정분의 의도된 덮어쓰기임을 추적하고 기존 cache 순서를 복원했다. 원래 runner/manifest를 저장하고 새 manifest를 고정한 뒤 계산했다. 원본 캐시는 수정하지 않았다.
- 첫 결과에서 연결보류32개를 errors로 합산하던 문제는 회귀시험 후 `unavailable`로 분리했다. 초안 결과/manifest를 보존하고 재계산했으며 거리·순위는 불변. 검산 코드의 provenance 비교에서도 재계산 대상 ranking을 원본과 같다고 요구하던 assertion을 수정했다. 새 추론은 모두0.
- 보고서는 실제 query/참조 이미지만 복사하며 raw embedding·사용자 답변을 수정하지 않는다. 회복 버튼은 확정 회복이 아닌 **점수1위 회복**이라고 표시한다.

## 6. 파일 소유권·미검증·다음 방향

W14가 평가 code와 공통 얼굴 API/fixture 작업을 소유한다. W13 main 선택·물리적 동일인scope·mapping·crop 소비자 권한은 유지한다. 공개계약/fixture → W13 scope/실패 compatibility → 소비adapter·선택venv → Mac arm64/Windows x64 패키징 → 합의 후 merge 순서도 유지한다. 이번에는 계약 상호수용/통합/배포 완료를 새로 주장하지 않는다. 별도 ML 선택 의존성과 lazy import 계약도 그대로다.

남은 문제는 혜인/해린 분리, 후보별 참조 대표성, 별도자료에서 거리·차이 기준 보정, 실제 최종 안무 구간 판정이다. 다음 작업은 **각 멤버의 참조가 어떤 각도·촬영 조건을 대표하는지와 오분류 얼굴의 특징 분포를 확인해, 현재 특징에서 분리가 가능한 실패와 불가능한 실패를 나누는 것**이다. 무제한 자동참조 확장·이미 본 정답에 맞춘 threshold 반복탐색은 채택하지 않는다.

새로운 일반화 주장을 하려면 혜인·하니를 포함한 다른 촬영의 식별가능 정답과 참조/보정/평가 분리가 필요하다. 현재 추가15답변으로는 그 두 멤버를 검증할 수 없다. 이번 진단 마무리에 사용자 추가 입력은 필요하지 않았다. Windows/macOS clean packaging·최신W13 iteration27 이후 변경 소비·전체구간GT·실제 제품속도는 미검증이다.
