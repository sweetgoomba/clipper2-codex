## Task 4: 같은 사람 표본의 합의·충돌과 중복 방지

**Files:** Create `clipper_face_core/clipper_face_core/consensus.py`, `clipper_face_core/tests/test_consensus.py`; Modify core `__init__.py`.

**Interfaces:** `combine_reference_matches(scope_id: str, evidence: Sequence[QueryEvidence], matches: Sequence[ReferenceMatch], policy: MatchPolicy) -> ConsensusResult`. evidence/matches는 observation ID로 연결한다. 구조 오류(누락 대응·다른 analysis/source/scope·상충 중복 ID·다른 gallery/space/policy)는 ValueError로 명시적 실패.

- [ ] **1.** `test_conflicting_references_are_preserved`에서 같은 scope의 A/B matched 두 표본은 ambiguous/conflicting_references, reference_id null이며 두 근거가 남아야 한다. A matched 2개+failed 1개는 support=2에서 A, failed도 excluded 사유로 남긴다. A 1개+ambiguous 1개는 support=2에서 insufficient_support다.
- [ ] **2.** 동일 observation을 두 번 전달해도 support=2를 만족하지 않는 테스트, 다른 gallery/policy 결과 혼합 거부, 다른 source/analysis의 같은 track ID 거부를 작성한다. 모두 invalid/모두 거리미달/모호 표본만/빈 입력을 각각 invalid/unmatched/ambiguous/invalid(no_evidence)로 확인한다.
- [ ] **3.** `python -m pytest clipper_face_core/tests/test_consensus.py -q` → 구현 전 FAIL 확인.
- [ ] **4.** 중복을 제거한 뒤 matched 참조 ID 집합의 충돌을 먼저 검사한다. 지지 ID가 하나이고 고유 지지 수≥minimum_support인 경우만 배정한다. 후보 점수 평균으로 충돌을 지우지 않고 각 결과를 matches에 유지한다. used IDs는 해당 최종 배정의 지지 표본, excluded에는 나머지 사유를 남긴다. 미배정 집계에서는 used IDs를 비워도 matches 전체를 보존한다.
- [ ] **5.** 같은 명령 → PASS. Task 3+4 결합 테스트로 다른 사람/구간을 추가해 기존 scope 결과가 변하지 않는지 확인한다.

