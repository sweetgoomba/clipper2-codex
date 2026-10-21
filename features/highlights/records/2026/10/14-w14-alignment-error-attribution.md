# W14 얼굴 매칭 오류 원인 분리 — 참조 평균의 민감도와 남는 인식 오류

작성: 2026-10-14 KST. 사용자 “진행해줘”에 따라 직전 0009 자동 정렬 실험의 해린 2개 손실/다니엘 오판정 원인을 조사했다.

## 1. 쉽게 말한 결론

**이번에 매칭이 개선된 새 제품을 만든 것은 아니다. 잘못된 결과를 만드는 두 가지 양상을 분리했고, 효과가 있어 보였던 단순 수정이 다른 얼굴을 망가뜨리는 것을 확인했다.**

현재는 한 멤버의 등록 사진 여러 장을 각각 숫자 특징으로 바꾼 뒤 평균을 내고 영상 얼굴과 비교한다. 새 정렬에서 놓친 해린 2장은 **개별 등록 사진과 비교하면 해린이 가장 가깝지만, 평균 특징과 비교하면 혜인이 앞선다.** 참조 사진의 자세/촬영 조건이 다양한 상황에서 평균 하나로 대표하는 방식의 민감도가 드러난 사례다. 특정 사진이 잘못 등록됐다고 입증한 것은 아니다.

반면 25.759초 다니엘은 AuraFace가 **해린의 등록 사진 여러 장과 더 가깝다고 계산**한다. 사진을 한 장씩 빼 본 23가지 경우에도 해린이 1위다. 평균 계산만 바꾸거나 문제 사진 한 장을 지우면 해결될 오류라는 근거는 없다. 같은 얼굴의 SFace 1위는 다니엘이어서, 모든 모델에서 구별 불가능하다고 결론내리지도 않는다.

가장 가까운 사진 하나로 비교하면 앞의 해린 2장은 1위를 회복하지만, 기존에 구분하던 다른 얼굴 3개에서 1위를 잃는다. 그래서 **그 규칙을 제품에 적용하지 않았다.** 정렬 일괄 교체/모델 교체도 보류한다. 새 모델 추론 없이 저장된 특징으로 진단했고, 정답/참조 사진/제품 코드를 바꾸지 않았다.

[기존 비교 화면의 원인 진단](http://127.0.0.1:58261/auto-landmark-v1/index.html#diagnosis)에 검사 얼굴, 가까운 등록 사진, 멤버별 거리와 손실 근거를 추가했다. 사용자에게 새 이름 라벨이나 재내보내기를 요구하지 않는다.

## 2. 실행 범위와 고정 입력

- 기존 isolated worktree `shared-reference-face-matching-20261013`, Python branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` 유지. 새 fetch/rebase/제품 checkout 변경 없음.
- 앞 실험 입력: 원래 등록23, 안무353관측(얼굴309/미확보44), 추가영상34. 총410행/벡터366. 안무 source/main/구간은 기존40B 스냅샷이다.
- SFace/AuraFace × YuNet/0009의 **4개 임베딩 공간을 각각 독립 비교**. 같은 공간의 참조·영상만 내적. 새 ML0, 다운로드0, 의존성 설치0.
- 이번 [plan.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/plan.json): 37개 입력 경로/hash, plan SHA `95f501556cd16fa65e1a35370acbb71a2358a77d43389cd0a611c9583be9a294`. 직전0009 plan의88개 입력도 시작 시 확인했다.
- 기본 진단 본문 0.182초, 최고 RSS 74,317,824bytes. 180초/4GiB/출력100MiB 제한. 이는 저장 특징 계산 시간이며 모델 속도 벤치마크가 아니다.
- 초기 shell1회는 잘못된 작업 디렉터리로 파일 생성 전에 실패했고, 올바른 worktree 경로로 수정했다. 모델 실행/원본 변경은 없었다.

## 3. 대표 사례의 실제 근거

아래 거리는 모두 **AuraFace+0009 내부의 cosine distance**다. 작을수록 가까우며 확률이 아니다. 평균 특징 거리와 개인 사진 거리를 서로 직접 비교하여 성능 우열을 판단하면 안 된다. 각 방식 안의 후보 순위를 비교한다.

| 사례 | 평균 특징의 1위 | 가장 가까운 등록 사진 | 사진을 하나씩 뺀23경우의 정답1위 | 현재 최종 판정 |
|---|---|---|---:|---|
| J9 영상95.028초 해린 | 혜인0.5490, 해린0.5511 | 해린 ref-17, 0.5232 | 5/23 | 확인 필요 |
| J9 영상140.007초 해린 | 혜인0.5487, 해린0.5733 | 해린 ref-18, 0.5507 | 1/23 | 확인 필요 |
| 안무25.759초 다니엘 | 해린0.4862, 다니엘0.5797 | 해린 ref-16, 0.5445 | 0/23 | 해린으로 오확정 |

140초의 정확한 source 시각은 viewer/input의 PTS/프레임 원문을 정본으로 한다. 해린 두 얼굴의 원본 bbox 크기는 각각148×188px,191×246px 정도다. 이 두 사례를 작은 배경 얼굴이라 무시하거나 결과에서 숨길 근거는 없다.

해린95초에서 ref-14/16(해린) 또는 ref-19/20/21(혜인)을 각각 제외하면 해린1위로 바뀐다.140초는 혜인ref-20을 뺐을 때만 그렇다. 이는 **민감도 진단**이며 이 사진들을 삭제하라는 근거가 아니다. 사진 수는 다니엘5/민지5/하니4/해린5/혜인4로 같지 않다.

다니엘25.759초의 새 정렬에서는 해린ref-16(0.5445),15(0.5462),18(0.5640),14(0.6072)가 가장 가까운 다니엘 사진ref-00(0.6235)보다 모두 가깝다. 기존 YuNet 정렬에서도 개별 사진/평균/23가지 제외 모두 해린이 앞선다. 한 사진/평균 연산만의 문제는 아니다.

SFace는 같은 시점에서 두 정렬 모두 다니엘1위다. 새 정렬에서1·2위 차이가0.1209→0.1515가 되어 고정 기준상 보류→다니엘로 변했다. 따라서 모델 간 점수의 질이 다르다는 단일 사례 근거이며, SFace 전체 우수/교차모델 fallback 제품정책까지 입증하지 않는다.

25.759초 정답은 사용자가 **원본의 그 시점 메인 인물**을 확인한 것이다. 기존 얼굴 연결 점검을 통해 이 표본과 연결했으며, crop만 보고 다시 식별 가능한지 판정한 GT가 아니다. 주변 시점이나 전체클립 정답으로 전파하지 않았다.

### 다른 영상의 확인 얼굴과 비교한 보조 진단

동일 공간에서 다른 source의 사용자 확인·식별가능 얼굴들과 거리도 비교했다. 해린 두 사례는 여전히 다른 영상 해린이 최근접이다. 다니엘은 Aura 기존 정렬에서는 해린,새 정렬에서는 민지가 최근접이다. 이 데이터는 이미 알고 있는 라벨을 쓰는 **설명용 비교**이며, 자동 참조 선택/독립 평가/제품 분류기를 새로 만든 것이 아니다.

비교 pool은 J9 대상37개(다니엘2/민지9/하니6/해린9/혜인11), native 대상19개(3/4/3/8/1)로 불균형하다. 최근접 이름 하나로 모델의 보편적 성능을 추론하지 않는다.

## 4. 단순 수정의 회귀를 함께 확인

사례 확인 뒤 별도 질문과 입력을 [rank-control-plan.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/rank-control-plan.json)에 고정하고, **멤버 평균→가장 가까운 등록 사진**의 1위만 모든 기존 이름 라벨에서 비교했다. 사후 진단이므로 독립 평가가 아니다.

| 모델·정렬 | 안무 얼굴34 | 별도 메인2 | 추가 식별가능 얼굴19 |
|---|---:|---:|---:|
| SFace·YuNet |27→27|2→2|17→18|
| SFace·0009 |29→29|2→2|19→18|
| Aura·YuNet |32→29|1→0|18→19|
| Aura·0009 |29→27|1→0|17→19|

**표는 올바른 이름이1위인 수다. 거리/후보차이 기준을 통과한 확정 정답 수가 아니다.** 앞 실행 기록의18/19/21 등 확정 정답 수와 다른 지표다. 안무34에는 crop 식별 어려움6이 포함되고, 별도메인2는 crop 식별가능 라벨이 없다. 세 그룹을 합쳐 새 정확도를 발표하지 않는다. 인접프레임 독립성도 보장하지 않는다.

Aura0009는 해린95/140초 두1위를 회복하나, `s0035-p0-f2008`(하니),`s0057-p0-f6272`(민지·식별어려움),`s0058-p0-f6300`(원본메인해린)에서 올바른1위를 잃는다. SFace도 합계가 같아 보이는34안에서 서로 다른2개씩 회복/손실이 있다. 합계만으로 기존 결과 보존을 판단하면 안 된다.

원문: [rank-control.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/rank-control.json). 관측 없음44/연결 불확실/비얼굴/등록 외 인물/신원불명은 기존 판정 재현에서는 보존했고, 이 **이름 순위 표**의 분모에 억지로 넣지 않았다.

## 5. 위치점/참조 자체에 대해 확인한 것과 한계

- 실제 기존/새5점과 모델 입력 crop을 나란히 확인했다: [targets.png](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/targets.png), [references.png](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/references.png). 좌표 뒤집힘이나 빈 crop이라는 근거를 발견하지 않았다. 모델 예측으로 참조 사진의 사용자 이름을 수정하지 않았다.
- 모든366얼굴의5점을 고정112px ArcFace template에 similarity fit했다. 다니엘1544의 RMS0.545→5.059px, 혜인3512는2.280→1.222px, 해린95는2.871→2.951px,140은2.785→3.722px다.
- **template residual은 해부학적 위치점 정답과 다르다.** 전문가5점 GT가 없어 새점이 잘못됐다고 확정하거나 이 잔차로 정렬을 자동 선택할 수 없다. 네 사례에서 유리한 기준을 사후 만들어 적용하지 않았다.
- 각 등록 사진을 자기 멤버 평균에서 뺀 참조 내부 점검: SFaceYuNet23/23, SFace0009 22/23, Aura양쪽22/23 top1. 일부 민지 사진이 하니에 가깝지만 모델의 유사도만으로 사진 이름/등록 오류를 확정하지 않는다.

## 6. 검증 증거

- 4공간×387query = **1,548개 판정**의 상태·이름·reason을 저장 결과와 재현. 유효query343×5후보×4 = **6,860거리**, 최대오차0.
- 문제/대조4얼굴×4공간: 등록사진368거리,368개 사진1장 제외 순위(각5후보),타source448거리. 동일공간만 사용.
- 독립 감사: [independent-audit.py](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/independent-audit.py), [independent-audit.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/independent-audit.json). 기존 최종판정 전체 재현에는 원래추가영상34개도 포함된다.
- 추가 독립 감사 [supplemental-audit.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/supplemental-audit.json):220개1위 비교 전행/증감 일치,366얼굴×2정렬×3기하값2196개 최대오차1.51e-14. 기하는 별도 complex least-squares로 검산했다.
- 새 viewer 진단3카드/등록사진18개 로드,해린추가얼굴 및다니엘원본메인 연결,등록사진별거리 펼침 확인. 로드오류0,console error/warn0. 기존 `app.js`/`data.json` hash 유지. [screenshot.png](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/screenshot.png), [viewer-change.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/alignment-error-attribution-v1/viewer-change.json).
- 이번에는 제품 코드를 수정하지 않아 새 제품테스트 통과 수를 내세우지 않는다. 이전62tests는 직전 정렬 실험 검증이며 이번 진단의 새 테스트 수가 아니다.

## 7. 결정과 다음 실행안

1. **0009 일괄교체, 가장 가까운 참조1장만 사용, 특정 참조 삭제 모두 미채택.** 현재제품 기본 SFace 경로를 유지한다.
2. 다음 비교는 기존에 실제 확보된 특징으로 **여러 등록 사진의 지지를 합치는 방식**에 집중한다. 원래 YuNet 정렬을 고정한 SFace/Aura에 대해 기존평균과 후보1개(멤버별 가까운2사진 거리평균)를 비교하고, 기존 문턱값을 그대로 새 방식에 재사용하지 않는다. 사진추가·삭제·인식모델추가·시간순규칙 변경을 묶지 않는다.
3. 개발 자료에서만 거리/후보차이 기준을 정하고, 두 추가영상에는 고정 적용해 잘못된 확정·식별가능 얼굴 미매칭·기존정답손실·각 실패상태를 기록한다. **세 영상 모두 이미 본 자료여서 이 비교는 회귀시험이며 새로운 blind holdout이 아니다.** 아주 낮은 오확정률/제품일반화 입증에는 별도 촬영자료와 정답이 여전히 필요하다.
4. 얼굴의 순위 개선이 있더라도 동일35main/37run으로 다시 올려 관측→몸경로→구간의 오판정/보류가 무엇인지 확인해야 한다. 정확한메인2/얼굴34/전체구간정답미확인을 계속 분리한다.
5. 개선이 없거나 새 오확정/기존정답손실이 생기면 미채택하고, 이 사례에 맞춘 문턱/사진/모델혼합을 반복해 성공값만 고르지 않는다. 이번 문서는 다음후보를 실행했다는 결과가 아니며, 새로운 모델 다운로드나 제품전환 승인으로도 쓰지 않는다.

현재 사용자에게 필요한 추가 조작은 없다. 기존 저장자료를 이용한 다음후보 준비는 가능하다. 제품채택은 여전히 미완료다.

## 8. W13 인계 / 보존

W14는 공통 얼굴 API/평가/fixture, W13은 main/몸추적/구간/mapping/crop/제품adapter 소유다. 이번 변경은 격리평가 artifact와 기존결과 설명 UI/기록뿐이다. 공개API·SDK시작·선택venv·모델준비·제품/의존성·W13 코드 변경0, 이름라벨/참조/사용자편집 보존.

계약상호확인 → source/time/bbox/observation/scope/failure/embedding space compatibility → 선택venv/model 준비와 consumer adapter → Macarm64/Windowsx64 검증 → 합의된merge 순서를 유지한다. 이번에 새W13 수락,다른채팅발신,신규세션,commit/push/merge/Build5를 수행하지 않았다. macOS Intel은 범위밖이다.
