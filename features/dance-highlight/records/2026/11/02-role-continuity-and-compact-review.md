# 역할 연속성과 compact group — 독립 검토

2026-11-02 · 읽기 전용 · MMN1793617663026 / ANT1793617753764 / NEON1793617837063

**최신 판정(10절): 최종 실제 앱 세 실행을 독립 대조했다. 출력 변경은 ANT146.613–146.880 / NEON143.677–144.077 두 군무 경계에 한정됐고, 기존 이름·사용자 확인 14구간·존속 썸네일에 추가 퇴행을 발견하지 못했다. 71개 감사 조건을 통과했고 SAM OFF·native 추론 요청 수가 유지됐다. 전체 실행시간은 1132.067→1187.940초(+4.94%, 조건별 1회)로 늘었다. 진단 화면의 group 박스까지 전부 동일한 것은 아니며, NEON229초대의 관측 출처 변경을 10.3절에 별도로 기록한다.**

이전 6곳 compact 확장 실험은 실제 앱에서 원본 3~4프레임짜리 미확인 잔여를 만들어 실패했다. 그 감사와 anchor-only 안의 한계는 6~7절, 후속 bridge 초안의 두 P2 반례는 8절에 보존했다. 최종 수정본의 저장자료 변화는 ANT/NEON의 2곳뿐이며, 이전 실패 실험과 구분한다.

앱 검증 전 판정: compact group의 6개 변경은 화면상 타당한 후보다. 발견한 두 P2 반례는 부모가 수정했고, 최종 소스를 독립 실행해 두 반례 해소와 세 영상 캐시 결과 보존을 확인했다. 당시 검토 범위에서 추가로 실제 앱 검증을 막을 결함은 찾지 못했다. MMN38/ANT10 자동 복원은 luma·absolute-flow 기준만 완화해서 적용하면 안 된다. ANT615→616의 짧은 조명 전환에 대한 별도 전경 픽셀 검증이 다음 최소 실험이며, 이번 검토에서 그 새 검증기를 구현·승인한 것은 아니다. 이전 ANT117 경계 교정 앱 검증과 이번 구조/compact 검증은 구분한다.

## 1. 발견한 두 P2와 최종 수정 재검증

검토한 `segment.py` SHA-256: `794f4b2d9bf9dd0a0f0a79c07cb84301703a7f66531c124ae245ff867804f028`.

`_compact_ensemble_runs`는 중앙 torso의 0.15초 이상 연속 관측을 계산하지만, 해당 compact 후보 run만 False로 바꾸고 보호 정보는 반환하지 않는다. 이후 `classify_main_scenes`의 `bounded[start:i] = [True] * ...`(검토본 438행)는 새 compact-group 구간을 양끝으로 사용해 보호되어야 할 짧은 구간을 다시 group으로 만들 수 있다.

**합성 반례를 실제 제안 함수로 재현했다.** 1920×1080, 0.1초 간격 관측에서 양쪽에는 새 compact 후보 3명이 있고, 0.8/0.9/1.0초에는 중앙 torso가 측정되는 작은 한 몸만 있다. 중앙 몸은 화면 중앙을 가로지르고 이전 대형의 몸과 IoU 1/3이어서 기존 dropout 보간 조건을 만족한다. 중앙 torso는 0.2초간 이어지지만, 최종 결과는 보호 구간까지 전부 group이다. 기준 코드는 해당 구간을 main으로 유지한다. 이 반례는 새 group 후보가 보호 veto를 간접적으로 우회하는 것으로, 단순한 기존 동작 유지가 아니다.

최소 수정은 **보호 범위를 후보 제거에만 사용하지 않고 새 group 추가의 보간·debounce·최종 판정까지 전달하는 것**이다. 기존 group 판정은 보존하되, 새 compact 후보 때문에 추가되는 group이 보호 구간을 덮지 못하게 한다. 이 반례를 RED→GREEN 회귀로 넣으면 수정 범위를 검증할 수 있다. 현재 6개 실영상에서는 이 반례가 발생하지 않았다는 사실만으로 일반 계약이 안전해지지는 않는다.

**후속 수정 확인:** 부모는 `protected_central`을 반환하고 bounded fill의 양끝에 compact가 있으면 보호 인덱스를 검사하도록 수정했다. SHA-256 `545dc1e179b0bf38940f0688d6a8feb07c4c0c14e5e4709debf2d9dfdb608583`을 직접 실행해 첫 반례의 중앙 구간이 main으로 유지됨을 확인했다. 같은 세 영상 전체의 6개 변경도 첫 제안과 정확히 같았다.

**[P2·후속 수정에서 해소] compact 후보와 새로 추가된 compact 근거를 구분해야 한다.** 첫 수정은 `compact[start-1] or compact[i]`만 검사했다. 그러나 기존 base의 small-wide 조건과 새 compact 조건은 동시에 참일 수 있다. 원래 세 개의 측정된 compact 몸에 옆쪽의 작은 low-confidence 몸 하나를 추가하면, base는 전체 bbox spread로 원래부터 group이고 compact는 측정된 세 몸으로도 참이다. 동일한 중앙 구간 0.8/0.9/1.0초는 **기준 코드에서 group인데 첫 수정본에서는 main으로 바뀌었다.** 독립 합성 실행으로 재현했다. 이는 '기존 group 유지, 새 compact 제외에만 veto'라는 범위를 벗어났다.

최소 반례는 기존 base 후보와 compact 후보의 교집합을 별도로 다루면 해결할 수 있다. 더 명확한 계약은 **기존 base의 보간·debounce까지 끝난 group mask를 먼저 보존하고, 새 compact가 추가한 결과에만 보호 veto를 적용하는 것**이다. 최종 `base_group`은 삭제하지 않고 `new_group` 중 보호 구간만 차단하면 두 방향의 불변 조건을 직접 검사할 수 있다. 판정 함수의 관측 자료를 재사용하는 작은 배열 계산이며 새 모델이 필요하지 않다. 원래 반례와 이번 기존-group 반례를 함께 유지한다.

**최종 수정 독립 확인:** 부모는 `compact = [added and not base ...]`로 새 근거를 분리한 뒤 bounded veto와 compact reason에 사용하도록 수정했다. 최종 `segment.py` SHA-256은 `6782f647e99ec66cd46dea0cd4d2f15d6cb72e7aa8bb44435df033e96220329c`이다. 이 소스를 다시 동결해 두 독립 반례와 세 영상 전체 저장 pose를 재실행했다. 첫 반례의 보호 구간은 main을 유지하고, 두 번째 반례의 기존 group→main 변화는 0건이다. 실제 영상의 38개 변경 관측과 6개 구간은 최초 제안과 정확히 같으며 기존 group 역전 0건, ANT4.571–6.139 유지도 확인했다. 위 최종 base-mask 보존 방식은 더 강한 계약을 표현하는 대안이지 이번에 적용한 구현은 아니다. 두 반례와 현재 세 영상에 대한 검증을 모든 가능한 입력의 일반 증명으로 확대하지 않는다.

또한 현재 코드는 매 관측에서 “어떤 torso든 중앙을 가로지르는가”를 이어 붙인다. **같은 인물의 연속성 검증은 아니다.** 서로 다른 중앙 몸이나 카메라 컷도 .15초 run을 만들 수 있다. 새 group 제외를 보수적으로 보류하는 veto로는 타당하지만, 이를 solo/main 증명이나 이름 승격에 재사용하면 안 된다. 이전에 거절한 central-closeup 양성 규칙과 이번 음성 veto는 이 점에서 구분된다.

## 2. 6개 변경의 독립 확인과 개선량 해석

동결한 기준 `segment.py`와 제안본을 최신 저장 pose에 각각 실행했다. **4/11/23개 관측, 합계 38개**가 main→group으로 바뀌어 부모의 6개 구간과 정확히 일치했다. 기존 group의 역전은 없고 ANT4.571–6.139의 사용자 확인 구간도 유지됐다. 부모 썸네일에 더해 원본에서 각 변경의 시작·중간·마지막 프레임을 직접 추출해 확인했다.

|영상|변경 범위|시각 검토|
|---|---|---|
|MMN|49.916533–50.183467|여러 명의 전신을 담은 군무 화면. group 후보 타당|
|ANT|99.833067–100.300200|무대와 여러 전경·뒤 인물을 함께 담은 넓은 대형. group 후보 타당|
|ANT|146.613133–146.880067|동등한 크기의 여러 전신을 함께 보여 주는 대형. group 후보 타당|
|NEON|76.409667–77.077000|밀집 군무 전체를 보여 주는 원경. group 후보 타당|
|NEON|143.743600–144.077267|여러 명의 군무 대형. group 후보 타당|
|NEON|229.229000–229.762867|명확한 전체 군무. 기존 앱에도 main 출력은 없고 group 출력이 있음|

**2.535867초는 scene 판정이 바뀐 관측 범위이지 최종 앱 품질 개선량이 아니다.** 현재 최종 main과의 교집합은 2.002000초이며, 그중 named 0.533867초·unknown 1.468133초다. NEON 마지막 0.533867초는 이미 최종 group이며 main이 없다. NEON76초의 일부도 기존 표시용 group과 겹친다. 최종 앱에서 main 제거·group 보존/추가·카드·썸네일·총시간을 다시 확인해야 실제 개선량을 확정할 수 있다.

## 3. MMN38/ANT10: 원본과 기존 몸 검사의 결과

최신 프로젝트 `diagnostics/source.mp4` SHA-256은 각 실행의 원본 영상 해시와 모두 일치했다. 원본 연속 프레임을 읽고 `_check_source_chain`을 그대로 재실행했다. 그와 별도로 색상 거절 뒤에도 남은 기존 appearance/pose 단계를 검사했다. 이는 새 이름을 적용한 실행이 아니다.

|항목|MMN38.204733–39.339300|ANT9.909800–10.276933|
|---|---|---|
|원본 seed|2284 / 2364|588 / 616|
|관측과 몸 연결|21개 관측·20개 연결 모두 appearance 또는 pose 통과|8개 관측·7개 연결 모두 appearance 또는 pose 통과|
|기존 거절|isolated_visual_change|visual_cut|
|최대 전역 luma 차이|20.703125, 2297→2298|33.195313, 615→616|
|luma 중앙값 / MMN spike 상한|1.893229 / 6.0|5.208767 / —|
|직접 본 원본 변화|여러 프레임에 걸친 빠른 줌아웃 후 줌인|같은 몸·구도에서 강한 푸른 조명/연무 변화|
|저장 handoff|없음|없음|

MMN의 spike 조건을 넘는 pair는 줌아웃 부근 2287–2303과 줌인 부근 2358–2363에 걸쳐 있다. **isolated라는 reason과 달리 실제로는 단일 프레임 점프만 검사하는 로직이 아니다.** `max > max(6, 3×median)` 때문에 영상 전체 luma가 많이 변하는 연속 줌도 거절된다. MMN 구간에는 표시용 group 38.705333–39.506133과의 겹침도 있다. 저장 pose의 strict scene은 해당 몸 경로에서 main이지만, 이 사실만으로 넓은 군무 속 개인 메인 역할이 적극적으로 입증되는 것은 아니다.

ANT615→616은 같은 전경 몸과 무대 구도가 이어지는 강한 조명 변화로 보인다. 전역 색상 차이가 컷 후보가 되는 것은 설명되지만, 이 pair를 편집컷 확정으로 다루는 것은 지나치다. 반대로 육안으로 컷 오탐 가능성을 확인한 것만으로 이름 복원을 자동 승인하지는 않는다.

## 4. absolute flow만 바꾸는 대안도 통과하지 않음

현재 `structural_continuity`와 같은 SIFT mutual matching·RANSAC을 exact 원본 pair에서 실행했다. 추가로 similarity transform의 scale과 보정 잔차를 계산했다. 아래는 **검토용 기하 진단**이며 신규 승인 규칙의 성능 실측이 아니다.

|pair|inliers / matches|비율|raw p90 이동|scale|선택된 inlier의 보정 후 p90 잔차|
|---|---:|---:|---:|---:|---:|
|MMN2297→2298|17 / 58|0.293|48.057px|0.867|2.580px|
|MMN2359→2360|56 / 140|0.400|82.810px|1.230|2.558px|
|ANT615→616|148 / 331|0.447|5.550px|0.999|2.406px|
|NEON4911→4912 실제 원경 컷|2 / 3|0.667|기존 함수는 대응점 부족 거절|0.801|약 0px|
|MMN2406→2407 실제 뷰 전환|4 / 10|0.400|기존 함수는 대응점 부족 거절|0.511|2.048px|

MMN은 raw 이동뿐 아니라 inlier 수/비율도 실패한다. ANT의 이동은 기존 21.6px 한계보다 이미 작고, 비율이 0.6 미만이라 실패한다. 따라서 **absolute flow를 residual로 교체하거나 이동 한계만 늘리는 수정으로 두 사례를 해결할 수 없다.** 또한 RANSAC이 선택한 소수 점의 residual은 실제 컷에서도 낮을 수 있다. residual만 승인 조건으로 쓰거나 두 양성에 맞춰 ratio/점 개수를 낮추면 안 된다.

NEON81.9485–82.8494는 4911→4912에서 실제로 closeup→원경 화면이 바뀌고, 그 관측의 몸 연결도 실패한다. 기존 repeated alien face veto도 있다. 이 구간은 계속 보호해야 한다. 같은 의상·배경의 전경 교대나 duo에서는 전역 영상이 연속적이어도 선택한 몸/메인 역할이 바뀔 수 있다는 반례도 별도로 필요하다.

## 5. 바로 다음 최소 구현과 적용 판정

**이번 제품 검증으로 넘길 후보는 두 veto 범위 반례를 해결한 compact-group 변경이다.** 6개 구간의 화면 근거와 최종 소스의 독립 캐시 재생은 타당하며, 실제 세 영상 앱 검증으로 진행할 수 있다. cache scene 변화 2.535867초를 앱 품질 개선 완료로 보고하지 않는다.

MMN38/ANT10은 개선 가능성은 있지만 **현재 검사값만으로 자동 복원 적용을 승인할 수 없다.** 가장 작은 다음 실험은 ANT615→616 한 pair의 모델 없는 전경 픽셀 검증이다. 전체 luma 검사를 제거하거나 기존 mask 기반 함수를 bbox 가짜 mask로 통과시키지 않는다.

권장 verifier 계약은 `verify_selected_subject_transition(exact_source_pair, observed_body_path, all_competitors) -> supported / rejected / unproved + proof`다.

1. 원본 양끝 이름·기존 반대 이름/반복 alien veto를 먼저 유지한다. 의심스러운 인접 source pair만 검사하고 기존 source cache를 재사용한다.
2. 전역/지역 기하와 밝기 보정은 **움직임 제안**으로 사용한다. 선택된 몸의 head와 torso 각각에서 원본 텍스처의 양방향 대응·왕복 일치를 검증하고, 모든 경쟁 몸으로의 대응과 비교한다. 배경·로고의 일치나 같은 좌표에 남은 bbox를 사람 소유 증명으로 쓰지 않는다. 가려진 경쟁자·부족한 텍스처·큰 잔차는 unproved다.
3. 바로 앞뒤 source pair에서도 같은 경로가 이어져야 한다. 실제 편집컷, 비슷한 의상 교차, 같은 배경에서 다른 몸으로 바뀐 장면을 음성으로 둔다. 숫자 임계값은 이 두 양성에 맞춰 완화하지 않는다.
4. 이 verifier가 증명하는 것은 해당 몸의 영상 연속성이다. 개인 main 역할은 별도 temporal proof로 요구한다. reason 문자열·중앙 좌표·양끝 이름만으로 main을 승인하지 않으며, duo/원경·strict group 제외·handoff를 보존한다. 현재 저장 자료에는 일반적인 적극적 역할 증명이 충분하지 않아, source 검증 성공만으로 새 named main을 내보낼 수는 없다.

실험 우선순위는 ANT의 짧은 조명 pair다. MMN은 모션 블러와 큰 scale 변화, 원경 역할 맥락까지 있어 더 약한 전역 대응만으로는 충분하지 않다. 위 독립 전경/역할 검사가 통과하지 않으면 두 공백은 이번 적용에서 유지하는 것이 맞다. SAM OFF·Person/shared 불변·3초 상한 및 짧은 클립 일괄 병합 금지는 그대로 유지한다.

근거: [소스 창 검사](02-role-continuity-review-evidence/source-window-inspection.json), [exact pair 구조 수치](02-role-continuity-review-evidence/structural-pair-checks.json), [수정본 compact 독립 재생](02-role-continuity-review-evidence/compact-scene-independent-review.json), [최초 veto 우회](02-role-continuity-review-evidence/compact-scene-before-veto-fix.json), [첫 반례 재현 스크립트](02-role-continuity-review-evidence/review_compact_scenes.py), [기존-group 반례](02-role-continuity-review-evidence/veto-existing-group-counterexample.json), [두 번째 재현 스크립트](02-role-continuity-review-evidence/reproduce_existing_group_change.py), [MMN 원본](02-role-continuity-review-evidence/MMN-source-contact.jpg), [ANT 원본](02-role-continuity-review-evidence/ANT-source-contact.jpg), [NEON 원경 컷](02-role-continuity-review-evidence/NEON-source-contact.jpg), [변경 3구간 원본](02-role-continuity-review-evidence/MMN-ANT-compact-original-sequences.jpg), [NEON 변경 3구간 원본](02-role-continuity-review-evidence/NEON-compact-original-sequences.jpg).

수정 이력: [첫 수정에서 남았던 기존-group 반례](02-role-continuity-review-evidence/veto-existing-group-before-second-fix.json), [첫 수정의 전체 재생](02-role-continuity-review-evidence/compact-scene-first-veto-fix.json), [최종 수정 검증 요약](02-role-continuity-review-evidence/final-review-verification.json), [검토한 기준·제안 소스 보관](02-role-continuity-review-evidence/reviewed-source.zip).

제품 수정·앱 재분석·추가 ML/SAM 추론 없음. 부모가 보고한 최신 dance 990개 테스트를 이 검토에서 다시 실행했다고 주장하지 않는다. 캐시 함수 재생, 원본 디코딩, 기존 몸 검사, SIFT/기하 계산과 독립 반례만 실행했다.

## 6. 실제 앱 후속 감사 — 예상 범위 일치, 짧은 잔여 퇴행으로 미통과

부모가 실행한 세 작업의 완료를 기다린 뒤 앱의 project/job, `dance_meta.json`, `face_evidence.json`만 직접 읽었다. 이전 ANT117 경계 교정 검사를 재실행하지 않았다. 실행 중에는 상태와 완료된 영상의 JSON만 읽었고, ML·영상 디코딩·제품 테스트를 실행하지 않았다. 새 메타데이터의 `segment` 해시는 위 최종 검토본 `6782f647…20329c`와 일치한다. 기준 metadata/face evidence 해시도 앞선 독립 검토에서 동결한 값과 모두 같다.

|영상|기준 프로젝트|이번 프로젝트|main / group|1초 미만 클립|
|---|---|---|---|---|
|MMN|1793617663026|1793625050124|57 / 32 → 58 / 33|42 → 44|
|ANT|1793617753764|1793625132795|102 / 32 → 100 / 33|79 → 78|
|NEON|1793617837063|1793625224514|150 / 56 → 150 / 56|124 → 125|
|합계|—|—|309 / 120 → 308 / 122|245 → 247|

### 6.1. 출력 범위와 인물 보존

예상 6곳 밖에서 main/group의 시간별 포함 범위나 인물 이름 변화는 0건이다. 새 main 추가나 이름 교체, 기존 group 삭제도 없다. clip ID·썸네일 경로의 순번 재배치를 제외하면 기존 429개 중 417개 행은 내용이 그대로다. 바뀐 인물 카드 정보는 clip ID 목록과 미확인 클립 수뿐이며, 각 ID가 실제로 같은 인물의 클립을 참조하는 것도 확인했다.

|예상 범위|실제 출력 변화|
|---|---|
|MMN49.916533–50.183467|unknown main 0.266933초 제거, 같은 범위 group 추가|
|ANT99.833067–100.300200|김채원 0.066733초·카즈하 0.400400초를 main에서 제외, group 추가|
|ANT146.613133–146.880067|홍은채 0.066733초·unknown 0.200200초 제외, 뒤의 기존 group 시작 확장|
|NEON76.409667–77.077000|unknown 0.667333초 제외, 기존 표시용 group 양끝 확장|
|NEON143.743600–144.077267|unknown 0.333667초 제외, 뒤의 기존 group 시작 확장|
|NEON229.229000–229.762867|기존에도 main이 없고 group이므로 최종 출력 변화 없음|

main 제외 합계는 **2.002000초 = named 0.533867 + unknown 1.468133**이다. unknown 총량은 39.576667→38.108533초다. 이는 군무 화면 제외량이며 이름 인식 개선량이나 전체 품질 개선을 뜻하지 않는다.

원본 face segments, references, identity/secondary/body/mask/visible-member 진단과 pose의 몸·관절·시각 측정값은 같다. actual 저장 pose의 scene_kind 변화는 4/11/15개다. 캐시 classifier의 NEON 추가 8개는 기존 앱의 native 단계에서도 이미 group이었던 마지막 구간이므로 실제 최종 scene 변화량에 더하지 않는다. NEON215.348467의 `scene_reason`은 sustained-wide→compact로 바뀌었지만 scene_kind와 출력은 같다. 주 역할 관측의 차이도 `preparation_context`에 한정된다.

이번 감사는 JSON만 읽었다. 순번이 바뀐 썸네일 경로는 확인했지만 이미지 바이트·픽셀을 다시 검사하지 않았으므로 **새 썸네일 품질까지 통과했다고 주장하지 않는다.**

### 6.2. [P2] 새 group 경계가 원본 3~4프레임짜리 미확인 잔여를 만듦

|영상 / 새 클립|남은 범위|길이|원본 프레임 수|
|---|---|---:|---:|
|MMN main_0016|49.866483–49.916533|0.050050초|3|
|MMN main_0017|50.183467–50.250200|0.066733초|4|
|NEON main_0079|143.676867–143.743600|0.066733초|4|

MMN의 기존 unknown49.866483–50.250200 중간만 group이 되어 양쪽 잔여가 생긴다. NEON의 기존 unknown143.676867–143.843800도 앞 4프레임만 남는다. NEON76초의 기존 1.5016초 unknown은 0.533867초·0.300400초 두 조각으로 나뉜다. 원래 짧은 오류가 남아 있다는 수준을 넘어 **새 적용이 매우 짧은 최종 클립을 만든 회귀**다. 전체 클립 수는 429→430, 1초 미만은 245→247, 0.1초 미만은 24→26이다. ANT에서 기존 작은 클립 하나가 없어졌기 때문에 0.1초 미만의 순증은 2이지만, 새로 작아진 잔여는 위 3개다.

MMN50.183467의 저장 bbox 최대 높이는 366px로 1080/3=360px를 넘는다. 해당 1관측 양쪽에는 group이 있다. 부모는 이 관측이 중앙 보호 veto 대상은 아니며 `small_people=False`가 bounded fill을 막는다고 확인했다. 독립 JSON 검사에서도 해당 몸 크기와 양끝 group을 확인했으나 함수의 모든 내부 조건을 이번 앱 감사에서 새로 실행한 것은 아니다.

MMN 시작쪽에는 `cut_frames`에 2989가 있고 scene-boundary의 적용 `changes`/`output_edge_changes`에는 해당 경계가 없다. 저장 JSON만으로 원인이 검사 미실행인지 source-proof 거절인지 단정할 수 없다. 이후 부모는 원본 proof에서 gray 0.79435가 0.8 미만이고 SIFT 대응점 4개라 실패했다고 전달했다. 이는 **부모의 추가 원본 검사 결과**이며, 이 감사에서 영상을 다시 디코딩해 독립 재현한 값은 아니다. 특정 한 사례를 맞추려고 해당 임계값을 낮추는 것은 권고하지 않는다.

### 6.3. SAM OFF와 실행시간

기준·이번 여섯 실행 모두 mask/joint 정책 `disabled_runtime_cost_v1`, mask 사유 `disabled_runtime_cost`, 두 단계 시간·mask 후보 수·복원/교정량 0이다. 기록된 모델은 YuNet/AuraFace이며 SAM 항목이 없다. SAM OFF 요구는 유지됐다.

|영상|기준 실행시간|이번 실행시간|변화|이번 대기열 시간|
|---|---:|---:|---:|---:|
|MMN|295.082초|320.610초|+8.65%|0.087초|
|ANT|397.721초|470.742초|+18.36%|238.107초|
|NEON|439.264초|458.606초|+4.40%|617.461초|
|합계|1132.067초|1249.958초|+10.41%|—|

`job.startedAt`→`project.completedAt`이며 job 종료 시각과도 일치한다. 여섯 job/project는 모두 completed·error 없음이다. 이번 관측은 **18:52.067→20:49.958, 117.891초 증가**이며 속도 개선이라고 보고할 수 없다. 각 조건 1회 관측이므로 증가 원인을 compact 계산에 귀속시키거나 반복 측정된 성능 회귀로 확정할 수는 없다. 대기열은 분리했고 겹치는 대기시간을 합계에 더하지 않았다.

이 검토의 42개 감사 조건은 모두 통과했지만 `quality_pass=false`로 명시했다. 조건 통과에는 위 퇴행이 실제로 재현된다는 검사도 포함된다. 이것은 제품 테스트 42개 통과나 기능 품질 통과가 아니다.

근거: [독립 앱 감사 스크립트](02-role-continuity-review-evidence/audit_compact_actual_app.py), [전체 JSON 비교](02-role-continuity-review-evidence/actual-app-compact-independent-audit.json), [진단 필드 차이](02-role-continuity-review-evidence/actual-app-compact-diagnostic-diffs.json), [42개 조건 확인 스크립트](02-role-continuity-review-evidence/verify_compact_app_audit.py), [조건 결과와 퇴행 판정](02-role-continuity-review-evidence/actual-app-compact-independent-verification.json).

## 7. 후속 최소안 검토 — 기존 strict group에 이어지는 확장만 허용

제안 계약은 **기존 classifier의 gap fill/debounce 완료 mask를 보존하고, 새 compact가 만든 연속 group run이 그 기존 strict group 관측을 포함할 때만 확장**하는 것이다. 독립 group 섬을 만들지 않으므로 MMN49.9·ANT99·NEON76의 내부 절단을 보류하는 데는 효과가 있다. 기존 base mask의 보존, 시간 샘플 연속성, 중앙 보호, 실제 cut/foreign-face 보호도 유지해야 한다. bbox 길이나 clip 길이로 단순 선별하는 안은 아니다.

동결한 기존 classifier와 검토본을 저장 pose에 재생하고, 이 계약을 최종 group run에 적용하는 별도 시뮬레이션을 수행했다. 영상 디코딩·ML·앱 재분석·제품 코드 수정을 하지 않았다. 결과는 다음과 같다.

|영상|보완 계약이 허용하는 추가 group|
|---|---|
|MMN|없음|
|ANT|146.613133–146.880067|
|NEON|143.743600–144.077267, 229.229000–229.762867|

**반례: NEON143.743600–144.077267은 기존 strict group144.077267 이후와 바로 이어지므로 이 조건을 통과하지만, unknown143.676867–143.743600 0.066733초를 여전히 남긴다.** 원래 main 행에서 허용 범위를 빼서 직접 재현했다. 따라서 “독립 group 섬을 막으면 짧은 잔여도 없어진다”는 주장은 성립하지 않는다. 예상 실제 main 제외량은 ANT0.266933+NEON0.333667=0.600600초이고, 마지막 NEON 구간은 기존처럼 최종 개선량이 없다. 이것은 보완안의 계약 시뮬레이션이며 새 제품 함수나 새 실제 앱 실행 결과가 아니다.

현재 안전한 최소 조치는 **이 보완안만으로 품질 통과를 선언하지 않고 compact 적용을 보류하는 것**이다. 개선을 유지하려면 추가 group의 진입·이탈 경계에 근거가 필요하다. MMN 뒤쪽이나 NEON143의 1관측 공백은 모든 관련 몸이 양끝의 입증된 group 대형에 대응하고, 크기 변화·중앙 보호·샘플 연속성·실제 cut/반대 역할을 함께 검사하는 bounded bridge의 후보가 될 수 있다. 그러나 단순 공간 근접이나 중앙에 없다는 사실만으로 group을 승인해서는 안 된다. 대응이 유일하지 않거나 관측이 부족하면 보류한다. 이 bridge는 MMN 시작쪽의 원본 컷 정렬 문제까지 해결하지는 않는다.

우선 기존 cut proof가 실제 전환을 거절한 근거를 조사하고, 이 1관측 공백에서도 역할이 바뀌는 반례를 보존한 채 경계 검증을 별도 확인하는 것이 맞다. 증명이 없으면 해당 후보를 적용하지 않는다. 3~4프레임을 길이만으로 삭제하거나 이웃 named main에 붙이지 않는다. 새 anchor 조건은 탐색 범위를 줄이는 보수적 필터로는 타당하지만 경계 품질의 충분조건은 아니다.

근거: [anchor 계약 시뮬레이션](02-role-continuity-review-evidence/review_anchored_compact_proposal.py), [세 영상 결과와 NEON 잔여 반례](02-role-continuity-review-evidence/anchored-compact-contract-review.json).

## 8. native 이후 bounded bridge 초안 — 근거 출처와 전경/누락 보호

검토본 `segment.py` SHA-256: `d7eb92801c26d9f643db12ae1bf15641511cf2d51652214efbba3aa822a45379`. 실제 fixture SHA-256: `a1b71f24bc75f5d8a59dd4c99bee516e7180ca2db9ed15bf9354c50f9f005029`. 이 절은 아직 새 실제 앱 실행을 거치지 않은 `bridge_compact_group_gaps` 초안의 독립 함수 검토다.

### 8.1. 실제 양끝 근거는 일반 pose와 native를 구분해야 함

부모가 제공한 기존 contact 이미지를 직접 확인했다. NEON143.4–144.077은 연속 원경 군무로 보이며 8612 한 관측의 main 분류는 화면과 맞지 않는다. 새 영상 디코딩은 하지 않았다.

“직전 native 관측에 x≈738의 실제 몸이 없어 여러 프레임으로 창을 넓혀야 한다”는 전제는 저장 자료와 다르다. 일반 `pose_heads`의 8608에는 해당 몸이 없지만, **동일 프레임 native 관측에는 bbox[741.5,643.5,798.5,826.5]가 있다.** native accepted run8596–8608에 속하고, 기존 `_geometry`를 저장 관측에만 적용하면 full=True·extent164.674이다.

|8612 gap 실제 몸|8608 native 양끝 IoU|8616 compact 양끝 IoU|
|---|---:|---:|
|[1117.5,611.25,1189.5,819]|0.617406|0.820902|
|[738,636,811.5,810]|0.691249|0.865900|

즉 두 실제 몸은 단일 직전/직후 관측에 대응한다. `native_scene`가 group을 확정할 때 사용한 native 측정/`group_bboxes`를 사용하지 않고 원래 `person_bboxes`만 사용하면 이 근거가 사라진다. 우선 그 출처를 바로잡는 편이 더 작고 보수적인 수정이다.

gap의 조형물 bbox[239.625,354,453,753]는 native 왼쪽과 IoU0이며, 오른쪽의 조형물과만 0.825697이다. head max0.16687·torso min0.55957로, gap의 실제 x738 몸(head max0.28979라도 torso min0.85840)과 신뢰도가 다르다. group 프레임에 있다는 이유로 모든 raw bbox가 확정된 사람인 것은 아니다. 조형물 박스를 새 사람의 양성 근거로 재사용해서는 안 된다.

### 8.2. [P2] 새 전경 인물을 과거 조형물 박스에 대응시켜 group으로 지움

현재 `correspond`(검토본 535–549행)는 모든 gap `person_bboxes`를 anchor의 모든 raw `person_bboxes`와 IoU/높이 비율로만 비교한다. gap의 pose는 중앙 torso veto에만 사용한다. 따라서 신뢰할 수 있는 새 전경 몸이 과거의 비신뢰 조형물 박스와 위치·크기가 같으면 신규 몸으로 인식하지 못한다.

실제 fixture의 bbox·시간·양끝을 그대로 두고, gap8612의 399px 조형물 박스에만 신뢰도 .99의 정상 head/torso/ankle 관측을 넣는 합성 반례를 만들었다. 모두 bbox 안에 있고 중앙 밖이다. 기존 `_large_observed_foreground`는 **True**가 되어 이 몸을 보호하지만, 새 bridge는 계속 main→group으로 바꾼다. 중앙 veto는 False, 조형물과의 크기 비율은 1이라 그대로 통과한다. 현재 “새 몸”/“scale jump” 음성 테스트는 좌표나 크기를 바꾸므로 이 출처 전환을 검증하지 못한다.

최소 요구는 기존 관측 전경 보호를 새 bridge에서도 유지하고, 양끝 대응의 사람 근거를 native/strict/compact가 실제로 측정한 신뢰 몸과 연결하는 것이다. raw 박스의 존재만으로 그 박스를 사람 근거로 승격하지 않는다. 기존 크기 임계값을 완화할 필요가 없다.

### 8.3. [P2] gap pose가 전부 없어도 bridge가 통과함

동일 fixture에서 `target.person_pose_keypoints=[]`만 바꾸면 역시 main→group이다. `_observed_central_torso`는 측정이 없을 때 False를 반환하지만, 이는 중앙 역할이 없다는 증명이 아니다. 현재 정보 누락 테스트는 `cut_frames=None`만 검사해 이 경로를 놓친다.

몸/pose 목록의 불일치, 잘못된 shape, 유효하지 않은 관측 등으로 보호 판단이 불가능하면 hold해야 한다. head 일부의 낮은 신뢰도로 생긴 dropout과 pose 자체가 전부 없는 입력은 구분한다. 무조건 모든 head가 높아야 한다는 새 조건이나 head를 합성하는 규칙을 제안하는 것이 아니다.

독립 실행에서 원래 양성·새 전경 인물 반례·pose 누락 반례는 모두 left8604/right8616을 근거로 같은 bridge를 만들었다. 제품 파일 수정이나 추가 추론 없이 동결한 실제 제안 함수를 호출해 확인했다. **이 두 반례가 수정되기 전 최종 빌드 승인은 보류한다.**

### 8.4. 유지할 계약과 추가 음성 범위

초안이 서로 다른 프레임의 몸들을 합성하지 않고, 각 방향의 한 프레임 안에서 모든 gap 몸을 유일하게 대응시키는 점은 맞다. `recs`를 동결 입력으로 읽고 `output`에만 적용하므로 bridge 결과를 다음 bridge의 anchor로 재사용하지 않는 점도 유지해야 한다. 양끝 context까지 포함한 cut/handoff/camera episode 검사, 정확한 sample cadence, 중앙 torso 한 관측 veto, no_person 보류도 적절하다.

추가 확인은 새 기능의 실패 경로에 집중한다. (1) 위 신뢰 전경/pose 누락 반례, (2) 서로 다른 시각에만 각각 대응하는 두 몸을 한 프레임의 ensemble처럼 합치지 않음, (3) 양끝 여러 몸에 동시에 대응되는 교차/중복을 보류함, (4) gap 밖이지만 사용한 anchor 문맥 안의 cut/역할 교대도 차단함, (5) 확장으로 새로 추가된 compact 근거를 명시해 기존 main 전체가 새 bridge의 대상이 되지 않음이다. reason 문자열만 사람의 근거나 신원 증명으로 쓰지 않는다. 대응 실패를 통과시키기 위해 anchor 창을 늘리는 것보다 실제 판정에 사용된 측정 출처를 먼저 확인한다.

근거: [native 단일 양끝의 실제 대응](02-role-continuity-review-evidence/NEON-bridge-endpoint-evidence.json), [동결 초안](02-role-continuity-review-evidence/bridge-draft-segment.py), [동결 실제 fixture](02-role-continuity-review-evidence/bridge-draft-fixture.json), [독립 반례 스크립트](02-role-continuity-review-evidence/reproduce_bridge_foreground.py), [세 실행 결과](02-role-continuity-review-evidence/bridge-foreground-counterexamples.json), [부모가 추출한 원본 contact 확인](02-role-continuity-review-evidence/NEON-bridge-source-contact.jpg).

## 9. 후속 최종 소스 재검증 — 발견 반례 해소, 실제 앱 검증 진행 가능

최종 검토 `segment.py` SHA-256: `f52481e26c55b9bc573c8188352e474034331e2bda00947375261d319da157af`. fixture SHA-256: `5505c35ef3dbe0a45a764a0f39251eeed06c0dba895efb2cd914863d70212a1a`.

부모가 일반 detector의 기존 reliable head/torso 판단을 `_observed_body_joints`로 공통 추출했다. bridge는 형식이 유효한 관측만 사용하며, pose 누락·손상·몸과 개수 불일치, 관측된 큰 전경/화면 잘림을 보류한다. gap의 몸은 바로 앞뒤 한 프레임에서 각각 유일하게 대응해야 하고, 시간 창을 넓히거나 서로 다른 시각의 몸을 합성하지 않는다. cut/handoff/camera episode·정확한 샘플 간격·한 관측의 중앙 torso veto도 유지된다.

첫 수정 `60978e…25329`에서는 실제 native `group_bboxes`를 사용해 8절의 두 반례가 해소됐지만, 해당 목록에 full=False의 작은 불완전 박스가 남을 수 있다는 출처 문제가 있었다. `native_scene`는 세 명 이상의 전신으로 frame의 group을 확정해도 `group_bboxes`에는 측정된 다른 박스를 함께 넣기 때문이다. 최종본은 같은 프레임의 기존 native observations에서 `_geometry(full=True)`이며 실제 `group_bboxes`와 좌표가 정확히 같은 몸만 anchor로 사용한다. 근거가 없으면 raw 박스로 대체하지 않는다. pipeline은 기존 native audit을 전달하며 새 추론을 추가하지 않는다.

### 9.1. 독립 재검증 결과

직접 작성한 순수 함수 검사 **24개(실제 양성 1, 음성 23)**가 통과했다. 새 전경 인물/pose 누락 원래 반례, 배열·shape·비유한 관측, 중앙 한 관측, 신규 몸·중복/애매한 대응, 화면 잘림, 컷·역할 교대·샘플 누락을 검사했다. native 측면에서는 관측 없음, 관절 불명, 대응 몸의 head가 사라진 partial 관측, 다른 frame, `group_bboxes`와 0.001 좌표 불일치도 모두 hold한다.

실제 양성은 **native8608 → gap8612 → compact8616**으로 통과했다. 최종 group 근거에는 실제 몸 2개만 들어가며 조형물 1개는 unobserved로 audit에 기록된다. 원래 입력의 main 선택과 bbox는 수정되지 않는다. 단순한 `group_bboxes` 중복만으로는 새로운 관측 사람이 생기지 않으므로, 최종 모호성 음성은 native 관절 관측 자체를 중복시켜 실제 competing anchor를 만들었다.

세 영상 전체 9,266개 관측에서 공통 helper 추출 전후 **기존 distributed predicate의 변화는 0건**이었다. 원래 classifier와 최종 classifier 각각에 저장 native 관측을 적용한 뒤 최종 bridge까지 재생했다. 결과는 아래 두 변화뿐이며 기존 group→main 역전은 0건이다.

|영상|최종 저장자료 재생의 main→group 변화|bridge|
|---|---|---|
|MMN|없음|없음|
|ANT|146.613133–146.880067, 4관측|없음|
|NEON|143.676867–144.077267, 6관측|8612 한 관측만, 143.676867–143.743600|

범위 합계는 **0.667333초**다. 첫 실제 앱 실험의 6곳/2.002초와 다르다. NEON 마지막 구간은 baseline native에서도 이미 group이어서 최종 차이에 들어가지 않는다. 기준 출력의 unknown 두 행143.676867–144.077267 전체가 이 범위에 포함되므로, 앞선 4프레임 잔여를 만들었던 시작점은 저장자료 재생에서 해소됐다. 이것을 새 실제 앱의 출력 개수나 썸네일 검증 완료로 표현하지 않는다.

### 9.2. 적용 판단과 남은 검증

발견한 전경/관측 누락 두 반례와 native anchor 출처 문제는 최종본에서 해소됐다. 현재 검토 범위에서 추가 차단 결함은 찾지 못했으며, 이 소스로 빌드·실제 앱 비교를 진행할 수 있다. MMN38/ANT10의 개인 main 자동 복원은 여전히 별도 근거가 필요하고 이번 변경으로 승인하지 않는다.

이 검토는 최종 소스를 동결한 함수 호출과 저장된 일반/native 관측 재생이다. 제품 전체 테스트나 새 앱 실행, 영상 디코딩, 새 ML/SAM 추론을 하지 않았다. 부모의 관련 테스트·전체 suite 결과를 독립 실행한 것으로 주장하지 않는다. 실제 앱에서 최종 main/group 범위, 기존 이름·카드·썸네일, 작은 잔여 재발 여부, SAM OFF와 전체 실행시간을 다시 확인해야 한다. 이전 실제 앱 실험의 품질 실패 기록은 삭제하거나 통과로 바꾸지 않았다.

근거: [최종 소스 동결본](02-role-continuity-review-evidence/bridge-full-anchor-segment.py), [native 근거를 포함한 fixture](02-role-continuity-review-evidence/bridge-full-anchor-fixture.json), [독립 재검증 스크립트](02-role-continuity-review-evidence/verify_bridge_full_anchor.py), [24개 사례·세 영상 전체 재생 결과](02-role-continuity-review-evidence/bridge-full-anchor-independent-verification.json). 중간 19개 사례 결과는 [첫 수정 검증](02-role-continuity-review-evidence/bridge-final-independent-verification.json)에 별도로 보존했다.

## 10. 최종 실제 앱 독립 감사 — 두 경계 개선, 출력 추가 퇴행 미발견

2026-11-02 최종 `app-final` 실행을 기준으로 한다. 6절의 실패한 첫 실험 `app`과 구분하며, 앞선 ANT117 경계 교정은 [별도 감사 10절](02-astra-quality-review.md)에 보존돼 있다. 이번 기준 실행에는 그 ANT117 교정이 이미 포함돼 있다.

|영상|기준 project ID|최종 project ID|
|---|---|---|
|MMN|1793617663026|1793628067111|
|ANT|1793617753764|1793628143826|
|NEON|1793617837063|1793628225716|

여섯 job/project는 모두 completed·error 없음이며 job 종료와 project 완료 시각이 일치했다. 기준 metadata/evidence 해시는 이전에 동결한 감사 자료와 같고, 원본 MP4를 직접 해시해 두 실행의 기록값과 일치함을 확인했다. 입력 설정과 dance setup도 동일하다. 최종 실행이 로드한 `segment.py`는 9절의 `f52481e26c55b9bc573c8188352e474034331e2bda00947375261d319da157af`, `pipeline.py`는 `15a5df668a57b90deface88d119baa6a784f9eaaeb061b8d3cc1451332ba0589`이며 기록된 설치 파일의 바이트와도 일치했다.

### 10.1. 이름·구간·출력 수

최종 main/group 전체를 ID 재번호와 분리해 인물·시간으로 비교했다. **변경은 아래 두 범위뿐이며, 새로운 named main이나 다른 이름으로의 치환, 기존 group 범위 삭제는 없다.**

- **MMN:** 89개 출력 행 전체가 동일하다.
- **ANT146.613133–146.880067:** Hong Eunchae main60의 끝이 146.679867→146.613133으로 당겨져 named main 0.066733초가 group으로 바뀐다. unknown main61·62의 총 0.200200초도 group으로 바뀌어 두 행이 삭제된다. group21은 시작만 146.880067→146.613133으로 바뀌고 끝149.149는 유지한다. ANT99초대는 최종 출력 변경이 없다.
- **NEON143.676867–144.077267:** unknown main78·79의 총 0.400400초가 group으로 바뀌고 두 행이 삭제된다. 양쪽 group28·29가 `[142.442300, 144.344200]` 하나로 합쳐진다. 따라서 group 수가 56→55가 되는 것은 이 동일한 경계 교정의 결과다.

main에서 빠진 총량은 **0.667333초(named 0.066733 + unknown 0.600600)**다. 제거 구간의 실제 화면은 여러 명의 전신 군무이며 앞서 확인한 원본 contact 및 아래 썸네일과 일치한다. 모든 장면의 정답을 새로 판독한 결과로 확대하지 않는다.

|영상|main 수|group 수|전체 출력 수|1초 미만 출력 수|unknown main 초|
|---|---:|---:|---:|---:|---:|
|MMN|57→57|32→32|89→89|42→42|6.807200→6.807200|
|ANT|102→100|32→32|134→132|79→77|16.017800→15.817600|
|NEON|150→148|56→55|206→203|124→121|16.751667→16.351267|
|합계|309→305|120→119|429→424|245→240|39.576667→38.976067|

0.1초 미만 출력은 24→23이며 **새로 생기거나 변경된 0.1초 미만 잔여는 0개**다. 앞선 실패 실험의 3~4프레임 잔여는 재발하지 않았다. 이름이 붙은 1초 미만 main은 **73→73**으로 그대로다.

이전 사용자 확인 14구간(MMN 7 / ANT 4 / NEON 3)은 이름·교차 범위·원래 행 경계가 동일하다. MMN1.9–2.3, 2.3–4.37, 10.91–11.31, 34.73–35.44, 37.738–39.339, 45–48, 89–93; ANT4.571–6.139, 8.375–9, 9.4–10.277, 32.633–33.433; NEON78.378–79.68, 150.617–152.619, 183.15–184.82를 각각 비교했다. 인물 카드의 설명은 같고, clip ID/개수는 실제 같은 인물 출력에 정확히 연결된다. **기존 MMN38·ANT9.9 등의 미해결 공백이 고쳐졌다는 뜻은 아니다.**

### 10.2. 썸네일과 진단 이미지 바이트 대조

전체 이미지 파일을 해시했다. MMN359→359, ANT604→599, NEON813→804로 총 **1776→1762개**다. 차이는 출력 썸네일 5개와 삭제된 unknown 네 행의 query 이미지 9개가 줄어든 것으로 모두 설명된다.

출력 썸네일은 429→424개다. 같은 종류·인물·시작점으로 대응되는 **존속 423개는 바이트까지 동일**하다. 완전히 같은 의미의 출력 행 421개 외에 끝만 바뀐 ANT main60과 합쳐진 NEON group28도 기존 썸네일을 그대로 유지하기 때문에 423개다. 부모의 완전 동일 행 기준 421개 집계와 모순되지 않는다.

새 시작점 때문에 달라진 썸네일은 **ANT group0021 하나**다. 이전146.880067·최종146.613133에서 실제 앱과 같은 FFmpeg·소수 셋째 자리 seek·JPEG 설정으로 원본 프레임을 각각 다시 추출했고, 두 파일 모두 해당 앱 썸네일과 바이트가 같았다. 이전/이후 그림을 직접 보아 여러 명의 전신 군무 화면임을 확인했다. 최종 NEON group0028의 142.4423초 썸네일도 직접 확인했다.

![ANT 이전 군무 썸네일](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-role-continuity-review-evidence/ANT-final-group0021-before-reextracted.jpg)

![ANT 최종 군무 썸네일](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-role-continuity-review-evidence/ANT-final-group0021-after-reextracted.jpg)

query 이미지는 clip 번호 재정렬 때문에 경로만 비교하면 대량 변경처럼 보인다. 소유 클립·시각으로 대응시키면 **모든 존속 query 이미지 시퀀스가 바이트 동일**하다. 1245→1236개의 차이는 ANT main61·62에서 3개, NEON main78·79에서 6개 삭제된 것뿐이다. reference 등 나머지 102개 이미지는 경로와 바이트 모두 같다. 최종 이미지1762개 중1761개는 기준의 동일 바이트 대응물이 있고, 한 개만 위의 정상적인 시작점 재추출이다.

### 10.3. 원시 근거 보존과 진단 화면의 표시 차이

원시 face segments, references, identity·secondary·body·mask·visible-member refinement는 동일하다. pose 관절·몸 측정도 같고 scene 종류/이유만 바뀐다. main role 선택 내용은 실행 준비 기록인 `preparation_context`를 제외하면 세 영상 모두 완전히 같다.

**진단 viewer frames 전체가 동일하다고 보고하지 않는다.** ANT는 위 변경 범위의 4관측, NEON은 위 변경 범위의 6관측에서 main 표시가 group 표시로 바뀐다. 이때 group용 몸/얼굴 박스도 해당 역할로 표시된다. 원래 `bodies`·`faces` 측정은 모든 프레임에서 동일하다.

별도로 **NEON229.229–229.696초의 8관측은 전후 모두 group이지만 `group_bodies` 표시가 달라진다.** 원래 native 판정 전에 compact 판정이 group을 확정하면서 이유가 `native_distant_ensemble`→`compact_distant_ensemble`로 바뀌고 일반 pose의 박스를 쓰기 때문이다. 예를 들어 첫 관측의 표시 박스 수는 7→6이다. 이 범위의 변경 필드는 `group_bodies`뿐이며 이름·main 선택·얼굴 측정·출력 구간·썸네일은 그대로다. 이는 출력 클립의 추가 퇴행을 뜻하지 않지만, 진단 표시까지 무변경이라는 보장에는 포함할 수 없다. 관측 출처 차이를 숨기지 않고 [진단 표시 전용 감사](02-role-continuity-review-evidence/final-app-viewer-routing-audit.json)에 보존했다.

### 10.4. SAM OFF·추론 수·실행시간

기준·최종 여섯 실행 모두 mask/joint 정책 `disabled_runtime_cost_v1`, mask 사유 `disabled_runtime_cost`다. 두 단계 실행시간·mask 후보·복원/교정량은 0이고, 기록된 모델은 YuNet/AuraFace이며 SAM 항목은 없다.

native 요청 프레임과 실제 저장 관측은 전후 정확히 같고 모델 설정도 같다. **MMN135, ANT299, NEON541, 합계975→975회**다. NEON의 native changes68→60은 앞서 compact가 확정한 8관측 때문에 감소한 적용 기록이며, 추론 요청이 8회 줄었다는 뜻은 아니다. 새 `group_context` 단계는 세 영상 합계 **0.002534초(약2.53ms)**이며 모델 호출을 추가하지 않는다. 기존 native 단계 시간 합계는72.114659→77.647093초로 관측됐다.

|영상|기준 실제 실행시간|최종 실제 실행시간|변화|최종 대기열 시간|
|---|---:|---:|---:|---:|
|MMN|295.082초|302.607초|+2.55%|0.078초|
|ANT|397.721초|421.038초|+5.86%|226.899초|
|NEON|439.264초|464.295초|+5.70%|566.117초|
|합계|1132.067초|1187.940초|+4.94%|—|

시간은 `job.startedAt`→`project.completedAt`이다. **18:52.067→19:47.940, 55.873초 증가**이며 속도 개선으로 보고할 수 없다. 조건별 한 번이므로 반복 측정된 성능 회귀 또는 새 compact 계산의 인과 효과로 확정하지 않는다. 대기열은 제외하고, 겹치는 대기시간이나 포함 관계인 하위 단계 시간을 합계에 더하지 않았다.

### 10.5. 검증 범위와 최종 판정

직접 작성한 **71개 최종 앱 감사 조건은 모두 통과**했다. 진단 표시의 추가 대조도 통과했다. 이번 범위에서 두 의도한 군무 경계 개선 외에 이름·출력 구간·썸네일의 추가 퇴행이나 첫 실패 실험의 짧은 잔여 재발을 발견하지 못했다. SAM OFF와 기존 추론 요청 수도 유지됐다.

남은 unknown38.976초, 짧은 출력240개, named short73개와 기존 역할 공백은 해결된 것으로 표시하지 않는다. 모든 장면에 대한 새 정답 평가, 반복 성능 측정, 전체 제품 테스트를 이 독립 감사가 대신하지 않는다. 부모가 보고한 제품 테스트를 재실행한 것으로 주장하지 않는다. 실제 앱 분석은 부모가 실행했고, 이 감사는 완료된 결과·설정·로그·원본 해시를 대조했다. 실행 중에는 상태와 완료 결과만 확인했고, 세 실행이 끝난 뒤 이미지/원본 해시 및 변경 썸네일의 두 프레임 추출을 수행했다. 추가 ML/SAM 추론이나 제품 코드 수정은 하지 않았다.

근거: [실행 목록](02-role-continuity-review-evidence/final-app-run-manifest.json), [MMN 비교](02-role-continuity-review-evidence/final-app-MMN-audit.json), [ANT 비교](02-role-continuity-review-evidence/final-app-ANT-audit.json), [NEON 비교](02-role-continuity-review-evidence/final-app-NEON-audit.json), [이미지 전체 해시와 대응](02-role-continuity-review-evidence/final-app-thumbnail-audit.json), [원본 썸네일 재현](02-role-continuity-review-evidence/final-app-thumbnail-reproduction.json), [native 요청·시간](02-role-continuity-review-evidence/final-app-native-cost-audit.json), [71개 조건 결과](02-role-continuity-review-evidence/final-app-independent-verification.json).

재현 스크립트: [앱 JSON 감사](02-role-continuity-review-evidence/audit_final_app.py), [이미지 해시 감사](02-role-continuity-review-evidence/audit_final_thumbnails.py), [query 의미 대응](02-role-continuity-review-evidence/audit_final_query_images.py), [native 비용](02-role-continuity-review-evidence/audit_final_native_cost.py), [진단 표시](02-role-continuity-review-evidence/audit_final_viewer_routing.py), [감사 조건 검증](02-role-continuity-review-evidence/verify_final_app.py).
