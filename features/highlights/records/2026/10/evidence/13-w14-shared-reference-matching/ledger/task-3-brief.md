## Task 3: query별 독립 참조 비교

**Files:** Create `clipper_face_core/clipper_face_core/matching.py`, `clipper_face_core/tests/test_matching.py`; Modify core `__init__.py`.

**Interfaces:** `match_reference(query: QueryEvidence, gallery: ReferenceGallery, policy: MatchPolicy) -> ReferenceMatch`. 개별 입력 실패는 `invalid`로 반환하며 한 query의 실패가 다른 query에 영향을 주지 않는다.

- [ ] **1.** 다음 테스트를 작성한다: 같은 A 특징의 q1/q2가 모두 A에 배정, q3 추가 후 q1 결과 불변, 두 query 호출 순서 교환 후 각 결과 불변. 2D 단위벡터 fixture에서 A=(1,0), B=(0,1), q=(1,0), policy=(0.60,0,1)을 사용한다.
- [ ] **2.** 경계 테스트: `distance==max_distance` 허용, `margin==min_margin` 허용, 정확한 동률은 `min_margin=0`이어도 ambiguous. `test_single_reference_still_requires_distance`는 한 참조에서 q=(-1,0) 미배정, q=(1,0) 배정과 margin null을 검사한다. 차원/space mismatch·NaN/Inf·영벡터는 invalid; association ambiguous/unassigned는 어떤 거리여도 배정하지 않되 후보는 보존한다.
- [ ] **3.** `python -m pytest clipper_face_core/tests/test_matching.py -q` → 구현 전 FAIL 확인.
- [ ] **4.** 입력 space 검증 후 `1-float(np.dot(query, centroid))`를 계산하며 수치 오차만 [0,2]로 clamp한다. float32 입력을 다시 정규화하지 않는다. 후보를 `(distance, reference_id)`로 정렬하되 동률을 ID순 승자로 확정하지 않는다. 우선순위는 invalid → association 불명 ambiguous → 거리 미달 unmatched → 동률/격차 미달 ambiguous → matched. 각 상태·한 참조의 거리만 판단한 경우를 reason으로 명시한다.
- [ ] **5.** 같은 명령 → PASS. 결과가 observation/space/gallery/policy 지문을 포함하고 embedding 벡터는 포함하지 않는지 확인한다.

