## Task 6: 소비 예제·호환 확인과 품질 평가 인계

**Files:** Create `clipper_face_core/examples/reference_matching.py`, `clipper_face_core/tests/test_consumer_contract.py`; Update core README 및 `.codex` W14 카드/WORKBOARD/날짜별 기록/W13 공통 계약 인계. **W13 `plugins/dance_highlight/**`는 이 task의 수정 대상이 아니다.**

**Interfaces:** 예제 `classify_selected_faces(references: Sequence[ReferenceSample], queries: Sequence[QueryEvidence], *, space: EmbeddingSpace, policy: MatchPolicy) -> tuple[ReferenceGallery, tuple[ReferenceMatch,...], tuple[ConsensusResult,...]]`; 예제 한 호출의 queries는 동일 analysis/source로 제한하고 다르면 ValueError다. scope가 있는 query만 해당 scope로 결합하고 없는 것은 개별 결과로 보존한다. 앱/SDK/job 객체를 요구하지 않는 소비 예제다.

- [ ] **1.** 가짜 소비자가 참조2명/개별 얼굴/같은 사람 scope를 전달하는 test를 작성한다. 동일 인물 여러 구간, 선택 얼굴 불명, 비교 실패, 한 scope의 상충 표본을 함께 넣어 결과 상태·근거를 검사한다. 입력 구간/track/관측 ID가 변경되지 않고 구간 생성/삭제가 발생하지 않는지 검사한다.
- [ ] **2.** `python -m pytest clipper_face_core/tests/test_consumer_contract.py -q` → 구현 전 FAIL 확인 후 위 공개 함수만으로 예제를 구현하고 PASS를 확인한다. SDK나 Dance 내부 타입을 import하지 않는다.
- [ ] **3.** 최종 선택 검증: `python -m pytest clipper_face_core/tests evaluation/reference_matching/tests -q`, `python -m ruff check clipper_face_core evaluation/reference_matching` → PASS. donor의 기존 core 10개+Person 17개 테스트는 **새 core를 PYTHONPATH 선두에 두고** 별도로 실행해 API 호환을 확인한다. donor 파일은 수정하지 않고 cache/pyc를 생성하지 않는다. interpreter의 실제 import 경로를 출력해 donor core를 잘못 테스트하지 않았음을 증명한다.
- [ ] **4.** W13 인계에 package 경로/version·공개 호출 예제·baseline/new 차이·입력 provenance·코드 hash·호환 결과를 기록한다. 실제 W13 adapter 소비는 그 세션의 branch에서 수행하며 새 API 수용/연결 완료는 문서만으로 주장하지 않는다. 소비 플러그인 pyproject/uv lock과 Electron 설치 fingerprint를 연결할 때 해당 세션과 단일 수정 소유를 정한다. 이 계획에서는 Electron·Nest·Angular·Web API를 수정하지 않는다.
- [ ] **5.** 후속 **제품 품질 판정**에 필요한 입력을 실행 기록에 명시한다: 모델 결과를 보기 전에 고정한 새 원본 얼굴 bbox/대상 몸 연결/익명 ID/가림·해상도 상태 라벨, 같은 참조 gallery, source/model/config/code hash. 현재18표본은 진단용으로 표시한다. 올바른 얼굴 제공/실제 안무 대상 제공을 분리하고 맞음·다른 멤버·미배정·모호·실패 및 멤버별 편차를 모두 보고한다. 모델 교체·새 얼굴 선택 규칙·제품 적용은 이 검증을 거쳐 별도 판단한다.

## 최종 검토 및 실행 방식

설계의 import/공개 계약은 Task1, 참조 평균/실패는 Task2, 개별 독립 매칭은 Task3, 같은 사람 표본/충돌은 Task4, 원인별 재현은 Task5, 재사용/소유권/제품 판정 한계는 Task6이 담당한다. 얼굴 소유 선택의 새 알고리즘과 새 모델의 성능 개선은 이번 구현 완료 주장에 포함하지 않는다.

실행 권고는 **이 세션에서 순서대로 직접 구현(Native)**이다. 여섯 task가 같은 DTO와 지문을 차례로 소비하므로 구현자를 매번 바꾸는 이득이 적다. 실행 계획 검토 후 `superpowers:executing-plans`를 적용하고 마지막에 독립 리뷰를 받는다. 사용자 요청 없는 새 작업 세션 생성이나 W13 메시지 발송은 하지 않는다.

이 계획은 아직 실행하지 않았다. 계획 검토와 실행 방식 선택 후 실제 코드 작업을 시작한다.
