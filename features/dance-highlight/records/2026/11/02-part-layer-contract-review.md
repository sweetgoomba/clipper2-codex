# 공연 파트 계층 1단계 — 독립 설계 검토

2026-11-02 · 제품 구현 전 검토 · 현재 dirty 소스와 최신 실제 앱 저장 결과 기준

**권고는 얼굴 근거 구간을 그대로 보존하면서 최종 공연 파트를 별도로 조립하는 것이다. `face_coverage_gap`만 제거하는 변경은 채택하면 안 된다.** 일부 얼굴의 일치가 전체 시간의 신원·몸 연속성·메인 역할까지 증명하지는 않는다. 1단계에서는 이 계약과 단일 출력 조립 지점을 만들고, 증명이 없는 구간의 이름 승격은 보류한다. 2단계가 적극적 메인 역할 근거를 공급하면 같은 계약으로 적용할 수 있다.

## 확인 범위

- 정본: `/Users/jina/project/adlight/desktop/clipper_python`의 미커밋 소스. 검토 시작 시 안무 Python 54개를 scratch에 동결했다. `named_boundaries`를 포함한다. 검토 중 제품 파일은 변경하지 않았다.
- 실제 자료: MMN `1793617663026`, ANT `1793617753764`, NEON `1793617837063`의 metadata·원본 얼굴/pose·joint 판정·역할 관측·몸 연속성 진단. 아래 수치는 이 저장 자료를 직접 집계한 것이다.
- 동결 코드에서 합성 입력 5개를 실행했다. matcher는 단순 벡터 fixture이며 모델 추론이 아니다. 앱 재분석·SAM·모델 추가 추론·새 영상 시각 판정은 하지 않았다. 새 구조의 실제 품질 개선량이나 실행시간은 아직 측정하지 않았다.

## 1. 공백 후보만 제거하면 생기는 문제

현재 흐름은 `_refine_member_scopes` → `_identity_boundaries` → `split_segment` → `_assign_piece`다. `_assign_piece`는 유효 얼굴의 반복 이름·상위 품질 얼굴 평균·반복되는 다른 얼굴을 검사하지만, 시간 전체의 얼굴 가시성이나 메인 역할을 증명하지 않는다. `insufficient_named_coverage`도 aggregate/anchor가 같은 이름을 지지하면 적용되지 않는다. 공백 분할은 이 함수가 보지 못하는 시간을 별도 unknown으로 남기는 안전장치다.

동결 코드의 경계 선택 직전에서 `face_coverage_gap` 후보만 제외해 다음을 재현했다. 원본 관측은 그대로이고, 다른 경계 규칙·matcher는 바꾸지 않았다.

|합성 입력|기존 결과|공백 후보 제거 후|
|---|---|---|
|0.1/0.3초에만 A 얼굴, 전체 3초|A 0–0.4 / unknown 0.4–3|**A 0–3**|
|0.1/0.3 및 2.1/2.3초 A, 전체 2.5초|A / unknown 0.4–2 / A|**A 0–2.5**|
|2.9/3.1초에만 A 얼굴, 전체 6초|unknown / A 2.8–3.2 / unknown|**A 0–6**|

이미 이름이 붙으면 `_named_evidence_boundaries`의 실패 구간 재분할을 타지 않고, 후속 `refine_unresolved_with_names`도 원칙적으로 기존 named 구간을 고정한다. 최종 projection은 출력 자격 마스크이지 신원 재검증이므로, 잘못 넓어진 이름을 자동으로 되돌려 주지 않는다. 대조 fixture인 관측된 A→B→A의 0.3초 B와 관측이 이어지는 30초 A는 두 조건 모두 보존됐다. 즉 “실제 교대 테스트는 통과한다”만으로 이 오류를 잡을 수 없다.

실제 첫 identity audit의 경계 기록은 MMN 70, ANT 125, NEON 152개다. 합계 347개 중 `face_coverage_gap`은 **38개(11.0%)**, `repeated_face_change` 130개, `repeated_reference_change` 128개, `named_evidence_edge` 51개다. 이는 첫 추론의 후보/경계 기록이며 최종 클립 수나 제거 가능한 경계 수가 아니다. 공백 한 종류만 없애는 것으로 전체 분절 문제가 해결된다고 볼 근거도 없다.

## 2. 저장 자료가 요구하는 반례

|실제 사례|현재 저장 근거|새 계층의 요구|
|---|---|---|
|MMN 38.204733–39.339300, 앞뒤 사쿠라|body 검사 `isolated_visual_change`; 일부 역할 관측은 `incomplete_incumbent_geometry`|같은 양끝 이름이나 선택 몸만으로 연결 금지. 컷/몸 대응을 별도로 증명|
|ANT 9.909800–10.276933, 앞뒤 김채원|`visual_cut` 거절|얼굴 공백으로 취급해 컷 거절을 삭제하지 않음|
|NEON 81.948533–82.849433, 앞뒤 시리|`conflicting_face_evidence` 거절|미확인 속 반복되는 다른 얼굴은 이름이 없어도 보존|
|MMN intro 1.9–2.3 및 NEON group 150.617–152.619|기존 출력은 group인데 역할 로그에는 `measured_face_composition` 등이 존재|reason 문자열 하나를 적극적 main 증명으로 사용하지 않음. scene/intro 자격과 역할을 함께 확인|
|MMN 45–48|별도 preparation이 다른 인물 main과 겹침|메인 파트와 preparation의 subject·근거·출력 경로를 혼합하지 않음|
|ANT 117초|현재 사쿠라→홍은채 경계 117.600817초|직전 검토에서 승인한 교정을 보존. accepted 반대 이름은 detector 0.8–0.9도 veto 대상|

현재 최종 출력에서 **같은 이름으로 양쪽이 둘러싸인 연속 unknown 묶음은 14곳, 총 11.379133초**다. 그중 11곳은 기존 몸 검사에 명시적 거절이 있고 3곳은 해당 연결 검사가 없다. 이는 병합 가능한 14개 후보가 아니다. 단지 “A–unknown–A면 하나의 A 파트”라는 규칙의 위험을 보여 준다. 위의 14곳은 이전 사용자 피드백 14구간과 다른 집합이다.

카메라 주체 episode는 MMN 5개, ANT/NEON은 0개다. 이 episode만으로 세 영상 전체의 적극적 역할 증명을 만들 수 없다. `main_bbox` 존재, tracking ID 동일, fallback 유지, 중앙의 큰 몸, 같은 얼굴 이름은 서로 다른 정보다. 앞서 거절한 one-sided 복원+central-closeup을 새 이름으로 다시 넣지 않는다.

## 3. 최소 계약과 연결 위치

외부 metadata·Person/shared 계약을 바꾸지 않는 내부 안무 계층이면 충분하다. 새로운 대형 그래프/모델보다 다음 값 계약을 먼저 고정한다.

|값|최소 내용|보존 규칙|
|---|---|---|
|Identity span|원본 span ID, `[start,end)`, 현재 신원 판정, 원본 observation 참조, support/gap/conflict 사유|얼굴 관측·실패·반대 이름·추론 경계를 읽기 전용으로 보존. 출력 part의 이름으로 덮어쓰지 않음|
|Boundary evidence|left/right 원본 프레임과 시각, 종류, 원인, 증거 참조|coverage 경계, 신원 변화, 역할 교대, scene 제외, source cut을 구분. coverage 기록을 지워서 다른 경계도 잃지 않음|
|Performance part|포함 span/부분 범위의 참조, 최종 이름 또는 unknown, 역할·몸 경로·경계 증거 참조|넓어진 시간의 정당성을 추적 가능하게 유지. 중간 unknown을 담은 part에 A 하나를 붙이는 것은 단순 그룹화가 아니라 이름 복원으로 집계|

권장 인터페이스는 `build_performance_parts(identity_spans, *, eligibility, frozen_evidence, continuity_proofs, role_proofs, source_boundaries) -> (existing_output_arrays, audit)` 수준이다. `frozen_evidence`에는 원본 owned observations와 primary/joint 판정, 원본 anchors가 들어간다. 모델 서비스는 입력받지 않는다. matcher가 필요한 기존 판단은 동결 임베딩 비교 adapter로 제한한다. `continuity_proofs`에는 범위·양끝 원본 seed·전 구간 frame/owner 대응·거절 이유가 있어야 하며 bool 하나로 축약하지 않는다. `role_proofs`는 affirmative / excluded / unproved를 구분하고 빠진 증거를 affirmative로 해석하지 않는다.

**조립 위치는 현재 projection→edge recovery→coalesce→named boundary 교정 블록이다.** 이 순서를 보존한 adapter부터 추출하고, 그 블록을 최종 main 경계의 책임 지점으로 만든다. `_refine_member_scopes`의 결과는 identity span이지 즉시 사용자에게 내보낼 공연 파트가 아니다. 이미 있는 뒤처리 뒤에 독립적인 병합 pass를 하나 더 쌓는 방식은 피한다. `_include_incoming_preparation`은 이 블록 뒤의 별도 경로로 유지한다.

원본 observations는 final projection으로 잘린 evidence와 별도로 계속 접근 가능해야 한다. ANT 117초처럼 필요한 얼굴 근거가 옛 출력 경계 밖에 있을 수 있다. 단, 외부 문맥 얼굴을 출력 구간 내부의 실제 관측인 것처럼 복사하거나 새 anchor로 추가해서는 안 된다. 조립 후 기존 `segments/decisions/labels/evidence/previews/preview_sources/accurate_indices`를 한 번에 재매핑하고, 부분 구간의 evidence·bbox·이미지는 해당 시간과 subject로 다시 제한한다.

## 4. 병합 승인·거절 규칙

1. **공백 경계는 후보일 뿐 자동 삭제 대상이 아니다.** 관측이 없는 prefix/suffix와 한쪽 얼굴만 있는 구간은 기존 이름을 확장하지 않는다. 새 근거가 없으면 기존 출력 유지.
2. **같은 이름은 필요조건 중 하나다.** 새로 이름 붙일 모든 시간에는 frozen 원본 신원 근거, 전체 몸 경로, 그 몸의 main 역할 근거가 각각 필요하다. 기존 `_assign_piece(union)`은 신원 충돌 검사로 활용할 수 있지만 시간 전체를 허가하는 증명으로 쓰지 않는다.
3. **반대 증거는 누적 union 전체에서 검사한다.** accepted primary/joint의 다른 이름은 seed보다 낮은 유효 detector 점수라도 건너뛰지 않는다. 반복되는 coherent alien 얼굴도 veto다. 단일 약한 이상값을 곧바로 새 B 파트로 확정하는 규칙과는 구분한다.
4. **경로의 누락과 경쟁 몸을 보존한다.** 원본 관측 간격/누락, bidirectional owner 대응, 겹치는 불완전 경쟁자, handoff bracket을 확인한다. track ID나 선택 박스의 단순 유지로 경로를 대체하지 않는다. handoff audit 없음과 complete·빈 목록은 다르다.
5. **source cut은 역할 교대와 별개다.** 컷을 넘어 몸 경로를 그대로 연장하지 않는다. A의 다른 카메라 화면을 한 파트로 묶으려면 양쪽 shot의 신원/역할과 연결을 독립적으로 증명해야 한다. 그런 증명이 없으면 새 연결을 하지 않는다. 모든 camera cut에 무조건 새 클립을 만드는 규칙도 추가하지 않는다.
6. **최종 자격 마스크를 보존한다.** 실제 제외된 group/intro/no-person 시간이나 빠진 출력 시간을 건너지 않는다. 기존 표시용 group 클립은 main/preparation과 겹칠 수 있으므로 모든 group 썸네일 구간을 일괄 hard mask로 쓰지 말고 `eligible_main`과 scene 근거를 사용한다.
7. **복원된 이름으로 다음 복원을 증명하지 않는다.** 입력 span·anchors·경로 증명을 동결하고 모든 제안을 그 입력에서 만든다. 인접 pair가 각각 통과해도 누적 part에 반대 얼굴이 있으면 병합하지 않는다.
8. **출력 보존과 변화량을 별도 계수한다.** final main 합집합·group·preparation의 정당한 겹침, 원본 얼굴/참조 임베딩은 보존한다. 변경된 이름 시간·unknown 감소·실제 파트 교대·경계 원인을 함께 보고한다. 클립 수 감소만 성공 기준으로 삼지 않는다. 3초 상한이나 1초 미만 일괄 병합은 넣지 않는다. 기존 0.15/0.6초는 얼굴 지지의 독립성·간격 조건이며 공연 파트의 길이 제한으로 전용하지 않는다.

현재 역할 관측이 충분하지 않으면 1단계는 기존 named 구간의 증명된 조립과 진단 계약까지만 활성화할 수 있다. 이는 구조 변경의 검증과 품질 개선량을 구분하기 위한 순서다. 2단계의 새 역할 근거 없이 unknown 복원을 먼저 켜면 기존 역할 오류를 더 긴 클립으로 만들 위험이 있다.

## 5. 최소 회귀 묶음과 완료 판단

- 위 3개 공백 반례는 확장 금지. 반대로 독립적인 양끝 신원·전체 몸 경로·affirmative 역할이 모두 있는 동일인 공백 fixture는 파트 조립을 허용하되 얼굴 근거가 늘어나지 않아야 한다.
- A→B→A의 짧은 B, unknown 속 반복되는 다른 얼굴, accepted B detector 0.85, 부모 span 양쪽에 하나씩 분산된 B 관측을 보존한다. 전역 다수결·top-quality 평균만으로 없애지 않는다.
- handoff / source cut / group·intro 제외 / 누락 pose / 불완전 경쟁 몸 / 역할 unproved를 각각 차단한다. 카메라만 바뀐 같은 A는 별도의 shot 연결 증명이 있을 때만 조립한다.
- 연속 A 6/10/30초는 임의 길이 제한 없이 한 파트 가능. A–unknown–A의 양끝 이름만으로는 병합 불가. 단일 샘플 사이 projection 찌꺼기와 실제 짧은 교대는 구분한다.
- 누적 union 충돌, 중복 observation, 반복 적용 불변성, source provenance와 원본 anchors 불변, final 배열 인덱스·thumbnail·preparation 분리 및 ANT 117.600817 경계를 확인한다.
- 실제 세 영상은 위 최신 프로젝트를 고정 기준으로 삼고, 변화한 구간마다 근거를 확인한다. SAM 두 단계 OFF·Person/shared 해시 유지·추가 모델 호출 없음·총 실행시간도 별도로 검증한다. 이번 설계 검토는 이 구현·앱 검증을 대신하지 않는다.

근거: [저장 자료 집계](02-part-layer-review-evidence/saved-evidence-inventory.json), [집계 스크립트](02-part-layer-review-evidence/inventory_saved_evidence.py), [공백 제거 반례](02-part-layer-review-evidence/gap-deletion-counterexamples.json), [독립 재현 스크립트](02-part-layer-review-evidence/reproduce_gap_deletion.py), [동결 소스 해시](02-part-layer-review-evidence/source-hashes.json), [동결 소스 묶음](02-part-layer-review-evidence/reviewed-dance-source.zip), [검증 기록](02-part-layer-review-evidence/verification.json). 검토 종료 시 실제 소스 54개도 동결 해시와 모두 같았다.

주요 코드 위치(검토 스냅샷): `member_timeline.py:134,197,260,431,554`, `segment.py:491,656`, `scene_boundaries.py:22,54`, `output_continuity.py:205,284`, `pipeline.py:1138–1214`. 직접 재현 및 저장 자료 확인과 설계 권고를 구분했으며, 새로운 body/role 판정 로직을 구현하거나 성능 향상을 주장하지 않는다.
