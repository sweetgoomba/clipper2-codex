# W14 가까운 참조2장 정책의 현재 입력 검증 — 미채택, 문턱 반복 조정 종료

2026-10-14 KST. 직전 ‘여러 참조 사진의 점수 결합과 그에 맞는 판정 기준 검증’ 제안에 대한 사용자 “진행해줘”의 실행 결과다.

## 1. 쉽게 말한 결과와 결정

**이번 후보도 제품에 넣지 않는다.** SFace는 일부 얼굴을 더 맞히지만 기존에 맞힌 얼굴과 해린 메인을 놓쳤다. AuraFace는 추가 영상의 정답2개를 놓쳤고 다니엘을 해린으로 잘못 확정하는 오류가 남았다.

현재 비교는 한 멤버의 등록 사진들을 평균 특징 하나로 만든다. 후보는 그 멤버 사진 중 **가까운2장의 거리 평균**을 사용한다. 두 방식의 점수 분포가 다르므로 각 방식에 맞춰 과거 개발자료에서 정한 거리/1·2위차이 기준을 사용했다. 이번에 현재 사례에 맞춰 문턱을 새로 맞추지 않았다.

**‘그럼 문턱만 조금 완화하면 된다’도 성립하지 않는 반례를 확인했다.** Aura에서 놓친 두 얼굴을 받아들이는 모든 전역 거리/차이 기준은 과거 개발자료의 식별가능한 혜인→하니 오류도 받아들인다. SFace는 기존 개발정답51개를 모두 보존한다는 추가 조건에서 같은 종류의 반례가 있다. 이 범위를 넘어 모든 미래 인식방법이 불가능하다고 주장하는 것은 아니다.

현재 제품 기본 SFace를 유지한다. 공통 얼굴 모듈의 재사용 구조와 별개로 **인식 품질 개선/후보 모델 제품 채택은 아직 완료되지 않았다.** 이 점수 결합·문턱 조정 후보 실험은 종료하고, 동일 자료에서 성공하는 기준을 계속 골라내지 않는다. 사용자에게 추가 라벨/내보내기 요청은 없다.

[현재 결과와 바뀐 얼굴 보기](http://127.0.0.1:58261/auto-landmark-v1/index.html#two-reference). 기존 페이지 앞에 이번 결과를 추가했고, 아래0009정렬 기록은 별도 이전 실험으로 보존했다.

## 2. 중복 실험을 피하기 위해 바꾼 실행 방식

실행 전에 과거 `gallery-diagnosis-v1`을 조사하니 `centroid/nearest/best_two` 자체는 이미128개 등록멤버 라벨을 사용해 비교되어 있었다. 따라서 재구현·재튜닝 대신 **당시 저장된 wrong_budget0 operating point를 가져와 현재4K얼굴/메인경로와 추가 두 영상에 적용하는 미완료 검증**을 수행했다.

| 모델/정책 | 최대 거리 | 최소1·2위차이 | 과거 개발128의 정답 / 오확정 / 보류 / 추론실패 |
|---|---:|---:|---:|
| SFace 평균 |0.723967|0.135333|59 /0 /69 /0|
| SFace 가까운2장 |0.582331|0.095796|51 /0 /77 /0|
| Aura 평균 |0.616395|0.049802|34 /0 /93 /1|
| Aura 가까운2장 |0.603525|0.032359|25 /0 /102 /1|

이는 개발자료 안에서 찾은 낙관적 기준이며 검증된 제품 threshold/FAR가 아니다. 두 방식에 동일한 개발자료/오류예산을 사용했지만 **집계+각자의threshold 결합정책 비교**다. 결과 증감을 집계 함수 하나의 효과로 귀속하지 않는다. 단순1위 변화는 결과 JSON에서 별도 기록한다.

추가로 사전 독립리뷰에서 **현재 native GT34개 모두가 과거 개발자료와 정확히 동일한 프레임·같은 멤버 라벨**임을 확인했다. 현재의 해상도/얼굴추출 경로는 달라졌어도 새 독립 정답이 아니다. 직전 기록의 ‘같은 source/인접프레임’보다 강한 중복이므로 이번 자료와 화면에 명시했다. 두 추가영상은 source가 다르지만 이미 여러 결과를 살펴보았으므로 새 blind holdout으로 부르지 않는다.

## 3. 입력·모델·범위

- 모델은 기존 SFace/AuraFace, YuNet 위치점과 각 모델의 원래 정렬/전처리다. 0009와 합치지 않았다.
- 등록23사진/5멤버(5/5/4/5/4), reference/영상 embedding은 모델별공간을 분리했다. 원래사진 삭제/추가/사용자이름변경0.
- 현재 고정 W13 40B snapshot: 안무353관측(얼굴309,미확보44),35main대상/37몸경로. 선택얼굴/몸/구간/시간/좌표를 바꾸지 않았다.
- 추가 두 source의34얼굴: 등록멤버23(식별가능19),등록외5,신원미확인5,얼굴아님1.
- body run의 최소확정근거2,확정된서로다른이름 충돌보류,모든run동의시scope배정 조건을 유지. 빈관측/연결불확실을 다른멤버근거로 바꾸지 않았다.
- 두참조 사진이 가까워도 서로 독립적인 사진이라는 보장은 없고, 각 사진이 개별확정됐다는 뜻도 아니다. 모델크기/성능/배포런타임을 바꾼 실험이 아니다.
- 새ML0·다운로드0·설치0·제품/W13/core/API변경0. 기존 격리worktree를 사용했다. 새fetch/rebase/branch/commit/push/merge/Build5 없음.

정확한 입력·코드54개 hash와 정책: [plan.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/plan.json), SHA `590c56f8170f587096ba2ca2506c8189739cbe9cb38dc4eae2d55f34bdbdd177`. 원래 source/model/전처리 정보는 잠근 기존manifest/space metadata로 연결된다. 실행구현은 폐기 가능한 평가용 [probe.py](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/probe.py)다.

## 4. 실제 현재 얼굴 결과

각 칸은 **올바른 확정 / 잘못된 확정 / 보류**다. 처리실패를 보류에 숨기지 않았다. 아래 라벨표본에서는 모델추론을 새로 하지 않았고 모두 저장벡터가 있다.

| 그룹 | SFace 평균→2장 | Aura 평균→2장 |
|---|---|---|
| native34 개발프레임 재평가 |18/0/16 →20/0/14|19/0/15 →21/0/13|
| 그중 식별가능28 |15/0/13 →17/0/11|17/0/11 →19/0/9|
| 별도원본메인 확인2 |1/0/1 →0/0/2|0/1/1 →0/1/1|
| 추가영상 등록멤버23 |15/0/8 →15/0/8|17/0/6 →15/0/8|
| 그중 식별가능19 |15/0/4 →15/0/4|17/0/2 →15/0/4|

등록외5/신원미확인5/얼굴아님1은 네 조건 모두 이름을 붙이지 않았다. 신원미확인 보류를 올바른 인식으로 세지 않는다. native34의 얼굴단독식별어려움6,메인2의 crop식별가능성미확인도 분리했다. 전체관측의 미확보44와 연결불확실 상태는 원래reason으로 보존했다.

### 새로 맞힌 것과 놓친 것

- **SFace:** native34에서 혜인3696,민지4852/6176 3개를 회복했지만 하니2008을 잃었다. 별도105.105초 해린6300도 보류로 바뀌었다. 둘다1위는 정답이나 후보차이가 기준 아래다. 추가19는 새회복/손실 모두0.
- **Aura:** native34에서 민지436/4852 2개를 회복. 추가영상 `6bVUjsUi9sw`45초 해린,`J9DlrnNlgfE`180초 민지를 잃었다. 둘다1위는 정답이지만 거리기준 초과로 보류한다.
- **다니엘25.759초:** Aura평균/2장 모두 해린으로 오확정. SFace평균/2장 모두 다니엘1위이나 보류. ‘확정되지 않음’과 ‘다른 멤버로 확정됨’을 구분한다.

세부 ID/사진/후보점수/사용한2사진: [result.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/result.json). 사후 좋은 사진이나 사례만 선택해 결과를 바꾸지 않았다.

## 5. 얼굴에서 몸경로/클립으로 올린 결과

| 지표 | SFace 평균→2장 | Aura 평균→2장 |
|---|---:|---:|
| 이름배정된main대상/35 |16→16|13→14|
| 기존대상배정 손실 |2|0|
| 새로운대상배정 |2|1|
| 기존이름변경 |0|0|
| 알려진정답지점과run/scope이름모순 |0→0|0→0|

SFace 손실은 clip9/51 민지,추가는 clip29 해린/52 하니. Aura 추가는 clip42 민지다. 정답이 없는 전체클립을 새로 정답으로 계산하지 않았다. 부분GT지점에서모순0이어도 **Aura의25.759초 얼굴 오확정은 구간보류에 가려진 채 남는다.** 전체클립합의만 보고 인식이 안전하다고 판단할 수 없다.

## 6. 문턱만 완화하는 것의 정확한 한계

고정 점수에서 수락 조건은 `거리 d ≤ D` 및 `1·2위차이 m ≥ M`이다. 정답A를 수락하려면 D≥dA,M≤mA가 필요하다. 다른 오답B가 dB≤dA,mB≥mA라면 그B도 반드시 수락된다. 이는 다른 품질/연결정책이나 새로운모델 일반에 대한 불가능성주장이 아니다.

### Aura: 손실얼굴만 받아들여도 생기는 반례

| 사례 | 거리 | 차이 |
|---|---:|---:|
| 추가45초 해린·1위해린 |0.636305|0.057881|
| 추가180초 민지·1위민지 |0.618176|0.079866|
| 개발3532 혜인·1위하니(식별가능yes) |0.605364|0.128953|

오답의 점수가 두정답보다 거리/차이 모두 유리하다. 따라서 어느손실얼굴을복구해도 개발3532혜인이 하니로확정된다. 이 반례를 무시한 문턱완화는 개선으로채택하지 않는다.

### SFace: 기존개발정답51개를 모두 보존할 때의 조건부 반례

두손실각각에 대한 단독지배오답은 발견하지 못했다. 하지만 기존best_two개발정답51개를유지하려면 `face-183` 때문에D≥0.582331이다. 손실하니/해린을각각복구하려면M≤0.085019/0.092297이어야한다. 이때 `face-014`(혜인정답,하니1위,d0.566457,m0.094918)가통과한다.

이 `face-014`는 식별가능여부가null이다. 원래이름라벨을쓰되 ‘사람도명확히식별가능한얼굴’이라고과장하지않는다. SFace정답복구가모든조건에서불가능하다고주장하지않는다. **기존51개보존+현재손실복구+개발오확정0을 이두문턱만으로동시에달성불가**라는조건부근거다.

[rejection_witness.py](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/rejection_witness.py), [rejection-witness.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/rejection-witness.json), [supplement-rejection-audit.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/supplement-rejection-audit.json). 새문턱검색/새분류정책/ML추론은하지않은 사후설명이다.

## 7. 실제 검증·실행

- 기존centroid2모델×387=774판정 상태·이름·reason,35scope/37run의 이름·근거·reason 재현.
- 독립검산: 4조건×387=**1548판정**,유효후보거리**6860**,best_two기여참조쌍3430,4×35scope/37run재현.
- 원래best_two구현의float32재정규화/clip과현재계산 최대차이1.79e-7. 임계경계최소간격2.07e-4이상으로 현재판정변화0. 정책을다른공간과섞지않았다.
- 저장개발frontier의선택·분모도재현. Aura추론실패1은보류와분리. native34/34의개발프레임중복독립확인.
- 주실행본문0.132초·최고RSS82,690,048bytes,상한180초/4GiB/100MiB이내. 기존AppleM4/24GiB의격리Python3.11/NumPy환경. 이시간은cached판정계산이며신규ML벤치마크아님.
- 원문 [independent-audit.py](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/independent-audit.py), [independent-audit.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/independent-audit.json), [run.log](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/run.log). 제품코드테스트성공수로인식품질을대신하지않는다.
- 화면은같은URL에이번결과/11개변경·잔여사례/반례설명을추가. 이전앱JS/데이터/정렬진단JSON은hash보존. [viewer-change.json](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/two-reference-transfer-v1/viewer-change.json).

## 8. 다음 방향과 W13 인계

**이번후보의실험은끝났다.** 모델/정렬/참조점수결합·문턱의사후조합을계속늘리는것은 다음작업으로삼지않는다. 현재결정은제품SFace유지,Aura/0009/최근접1장/가까운2장 정책미채택이다. 단일모델이전모든표본에서우수하다고입증한것은아니다.

남은과제는새로운인식근거를얻는경로의재설계다. 후보를추가하려면(1)현재작은무대얼굴/옆얼굴에대한동일입력개선근거,(2)정확가중치상업재배포조건,(3)Macarm64/Windowsx64 CPU배포,(4)개발프레임과분리된평가자료를갖춰야한다. 참조사진변경도실제사용자등록방식으로재현되어야하며정답영상을보고자동으로참조로쓰는oracle을제품으로대체하지않는다. 이문서로새모델다운로드/새의존성/제품모델전환을실행하지않았다.

W14공통API/평가/fixture,W13main/몸/구간/mapping/crop/제품adapter소유유지. 이번공개API/제품/의존성/사용자라벨·편집변경0. 계약상호확인→source/time/좌표/observation/scope/failure/space호환→선택venv/model준비→Macarm64/Windowsx64→합의merge순서유지. 다른채팅발신/새W13수락/새세션은없다. macOSIntel제외.
