# 기존 body continuity 계약 안의 torso 픽셀 보완 — 미구현 설계와 상한

결정: **이번 제품에는 구현하지 않는다.** 현재 source freeze와 실제 앱 벤치마크를 유지한다. 이 문서는 JSON/소스만으로 분류한 원인, 향후 검증 가능한 좁은 계약, 반례와 효과 상한이다. 픽셀의 성공 여부나 비용을 측정하지 않았으므로 회복 예상치가 아니다.

대상은 같은 original named face 양끝을 잇는 기존 body candidate 중 `unconfirmed_body_continuity`로 보류된 경우다. 그룹을 main으로 만들거나 새로운 이름을 만들지 않는다. SAM, 모델 재추론, 범용 tracking, 시간 범위 확대, 짧은 clip 삭제, 이름/time/video 특례를 포함하지 않는다.

## 현재 3영상 inventory

MMN은 최신 통합 앱 `1793649506337`. ANT `1793645767403`, NEON `1793645871567`은 직전 canonical-only 앱이다. 따라서 아래 합계는 동일 최신 버전의 성능 수치가 아니라 요청된 저장 자료의 후보 상한이다. 원본 observation 요약과 candidate 전체는 `body-candidate-inventory.json`에 보존했다.

| body 후보의 현재 이유 | MMN | ANT | NEON |
|---|---:|---:|---:|
| confirmed_body_continuity | 2 | 3 | 5 |
| unconfirmed_body_continuity | 1 | 1 | 3 |
| visual_cut | 1 | 3 | 0 |
| conflicting_face_evidence | 2 | 2 | 6 |
| conflicting_face_name | 0 | 1 | 1 |
| 합계 | 6 | 10 | 15 |

`visual_cut`과 두 identity conflict 이유는 이 보완 대상이 아니다. 이미 성공한 후보도 추가 회복으로 세지 않는다.

| 보류된 candidate | 원래 identity gap | 현재 main unknown과의 교집합 | JSON상 추가 제약 |
|---|---:|---:|---|
| MMN 68.301467–68.835533 | 0.534067초 | 0.534067초 | selected torso가 전 관측에서 강함(min≥0.903); head 공통점 부족 8 edges. 4132 단일 joint conflict 포함. 직접 조사 우선. |
| ANT 48.081367–48.415033 | 0.333667초 | **0초** | 현재 최종 출력은 group에 가려짐. selected head 공통점 부족 edge가 없고 torso도 모두 ≥0.5. head-only 실패라고 부를 수 없다. 실제 appearance/motion 또는 competitor ambiguity를 구별할 로그가 부족함. |
| NEON 30.063267–30.797533 | 0.734267초 | 0.734267초 | head 부족 외에 f1844 torso 최소 0.199, f1848 0.415. 독립 torso 4점 가정부터 실패한다. 현재 좁은 설계로 복원 상한에 넣지 않음. |
| NEON 130.697133–131.097733 | 0.400600초 | 0.100200초 | torso는 기존 ≥0.5지만 f7824 0.654·f7832 0.749. f7820/7852/7856/7860 face ownership ambiguous, 후속 joint conflicts 여러 개. 원래 소유자 모호성이 있으므로 MMN과 동등한 성공 후보로 볼 수 없음. |
| NEON 161.194367–161.728233 | 0.533867초 | 0.533867초 | selected torso 모두 강함(min≥0.875), head 부족 6 edges. f9692 joint conflict도 경로에 포함. 독립 양끝 seed 9660/9708. 직접 조사 우선. |

다섯 identity gap 합은 2.536467초다. 최종 main unknown 교집합의 이론적 상한은 1.902400초다. 이 수치에는 torso 자체 결측과 소유자 ambiguity가 있어 좁은 제안의 예상 효과로 사용할 수 없다.

안정적인 torso와 head 결측을 함께 가진 우선 후보 **MMN68 + NEON161**의 합은 **1.067933초**다. 둘 다 실제 pixel/경쟁자/전체 source 검사에 성공해야만 가능한 최대 범위다. 아직 확정된 추가 회복은 0초다. MMN은 성공 시 unknown 하나와 같은 홍은채 뒤쪽 named short 하나를 연결할 가능성이 있지만, 전체 main short 대량 문제의 해법은 아니다. ANT48의 group 구간을 이름 복원 성과로 세면 안 된다.

## 현재 계약을 그대로 상속할 부분

`bridge_main_face_gaps`는 원래 같은 이름 양끝, 서로 이어지는 원래 segment, gap 양쪽 0.6초 안의 유효 원본 얼굴을 요구한다. 유효 얼굴은 confirmed association, failure 없음, embedding 존재, detector score≥0.8이다. recovered 결과는 새로운 face anchor가 되지 않는다.

이름 veto는 그대로 유지한다. 유효한 다른 accepted 이름이 있으면 거부한다. 양 seed와 모두 먼 원본 얼굴들 중 0.15–0.6초 간격으로 서로 일치하는 두 관측이 있으면 `conflicting_face_evidence`로 거부한다. 새 body 픽셀 증명이 이 검사를 우회해서는 안 된다. 반대로 joint `conflict`라는 진단 enum만 보고 새 generic veto를 추가하지 않는다. 기존 계약이 구분하는 불확실한 얼굴과 확정된 타인을 그대로 구분한다.

source 검증도 유지한다. 관측 간격은 기존 한도 0.200001초 이내, 각 sampled body owner는 원래 bbox와 유일하게 대응해야 한다. 모든 source frame의 color-cut 검사, 뒤쪽 isolated visual change 검사, source 읽기 실패를 모두 통과해야 한다. 저장된 cut/handoff를 넘는 경로도 새로운 예외로 허용하지 않는다. 현재 body loop는 첫 실패에서 끝나므로, 앞부분의 no-cut 결과를 전체 경로의 no-cut으로 주장하면 안 된다.

기존 appearance link는 모든 경쟁 몸을 포함한 bbox/색상 대응을 양방향 유일성으로 검사한다. 실패하면 현재 strict pose는 공통 head≥2와 torso 4점, 크기/거리 및 양방향 uniqueness, 불완전한 겹치는 경쟁자 veto를 사용한다. 새 증명의 책임은 이 물리적 몸 연결을 독립 원본 pixel 관측으로 입증하는 것뿐이다. track id 동일, 높은 torso confidence, 양끝 이름 동일은 그 자체로 연결 증명이 아니다.

## 한정된 대안과 선택

1. 기존 strict head 기준을 낮추거나 torso만으로 거리 매칭: 계산은 싸지만, head가 안 보이는 겹친 몸과 같은 의상 경쟁자를 구별할 독립 근거가 없다. 채택하지 않는다.
2. 양끝 얼굴과 body id로 gap 흡수: 현재 누락된 물리적 경로를 입증하지 못한다. 채택하지 않는다.
3. **실패 edge에 한정된 원본 torso texture의 독립 양방향 경로**: 원본 포즈를 변경하지 않고 새 관측을 검증할 수 있는 유일한 좁은 조사안이다. 성공은 아직 증명되지 않았고 이번에는 구현하지 않는다.

## 향후 조사한다면 필요한 긍정 증거

- 원본 selected torso 4점이 양쪽 sample에 실제로 존재하고 유효한 해부학적 영역을 만든다. 관절이나 bbox를 보간해 관측으로 만들지 않는다. 기존 body owner 모호성은 먼저 보류한다.
- strict pose가 안 되는 **인접 원래 관측 사이**에서만 원본 frame 전부를 읽는다. 현재 대상은 sample stride 4라 edge당 source frame 최대 5개다. 실제 한도를 넘는 edge는 확장하지 않고 보류한다.
- 첫 원본 torso와 끝 원본 torso에서 각각 독립적으로 texture points를 뽑아 forward/backward path를 만든다. 한 방향의 최종 위치를 반대 방향 seed로 재사용하지 않는다. 전 sample에서 독립 점을 계속 재시작해 전혀 다른 몸으로 갈아타는 것도 금지한다.
- 점들이 한 선이나 옷 무늬 한 조각으로 퇴화하지 않고 torso 여러 영역에 분포해야 한다. 매 중간 source frame에서 양쪽 출발 경로가 같은 공간 지지를 유지하고 왕복 일관성 및 endpoint torso 소유가 확인되어야 한다. 전체 torso를 강체 affine로 강제할 필요는 없지만, 점 생존 몇 개나 단일 NCC 점수로 신체 연속성을 대체해서도 안 된다.
- 경쟁 몸은 삭제하거나 matching에서 제외하지 않는다. 원본 경쟁자 영역과 path가 겹치거나 다른 몸으로도 동일하게 대응하면 보류한다. overlapping bbox만으로 실제 occlusion을 단정하지는 않되, 해소되지 않은 owner ambiguity는 통과시키지 않는다.
- 실측 torso가 빠진 interval, texture가 없어 독립 경로를 만들 수 없는 interval, 가림 뒤 새 texture로 재시작해야 하는 interval은 보류한다. 모든 source frame이 있어도 다른 사람으로 넘어간 경로를 구별하지 못하면 실패다.
- 모든 실패 edge와 양쪽 named face까지의 전체 경로가 통과해야 한다. 한 edge 성공으로 나머지를 추정하지 않고, 기존 나머지 identity/cut/appearance guard를 모두 끝까지 수행한다.

이 조건들의 현실적인 판별력은 원본 픽셀로 검증해야 한다. 특히 같은 의상·완전 가림 뒤 교대는 torso texture만으로 해결되지 않을 수 있다. 명확한 반례를 통과시키는 설계라면 후보가 두 개라는 이유로 유지하지 않는다.

## 4132의 범위와 의미

MMN unknown 출력은 [68.301467,68.835533]이다. 실제 원본 named seed는 f4088(68.201467)와 f4136(69.002267)이므로 전체 증명은 4088–4136을 포함한다. f4132(68.935533)는 **출력 unknown 밖이지만 증명 경로 안**이다. 이를 빼거나 오른쪽의 낮은 detector f4128을 독립 named anchor로 바꿔서 경로를 줄여서는 안 된다.

f4132의 joint status는 conflict, name은 null이다. primary best 홍은채 거리 0.811767, secondary best 카즈하 0.670899(홍은채 0.696712)이다. 원본 AuraFace와 양 seed의 거리는 0.850380/0.868064라 한 개의 alien 관측이다. 그러나 기존 body identity guard는 이것 하나만으로 거부하지 않으며, 이 후보는 이미 기존 이름 조건을 통과했다. 새 generic conflict veto도 추가하지 않고 기존 identity guard도 완화하지 않는다.

따라서 독립 몸 픽셀 경로는 4132도 포함한 물리적 소유자를 증명해야 한다. 그 결과가 좋더라도 4132의 얼굴 이름을 accepted로 바꾸거나 얼굴 증거로 재사용하지 않는다. 이는 얼굴 인식 결과를 고치는 연구가 아니다.

## 필수 반례와 보존 대상

| 사례 | 전체 계약에서 요구할 결과 |
|---|---|
| 같은 옷 두 사람이 겹쳐 지나며 selected body가 바뀜 | texture 양방향 owner/경쟁자 uniqueness 실패 또는 handoff에서 보류 |
| 완전 가림 뒤 비슷한 옷의 다른 사람이 같은 위치에 등장 | 가림을 가로지르는 원본 점 경로가 없으므로 보류; 재시작 seed로 복구 금지 |
| 원본 한 frame에 타인 또는 no-person 삽입 | 모든 source frame 검사 및 독립 경로 실패; sampled endpoints가 같아도 보류 |
| 조명 flash, 저질 texture, blur | 충분한 비퇴화 경로가 없으면 보류; 성능 목적의 자동 통과 금지 |
| source cut 또는 기존 color-cut, 실제 main handoff | 기존 guard 보존. 배경 전환 helper 단독 성공으로 cut guard를 우회하지 않음 |
| 유효한 다른 accepted 이름, 또는 원래 coherent alien 두 관측 | 기존 face guard에서 거부, body helper 미호출 |
| MMN4132처럼 단일 uncertain joint conflict | 원래 identity 계약 그대로 평가하고 전체 물리 경로에 포함; 진단을 삭제하거나 새 이름으로 승격 금지 |
| selected torso 결측, 불완전한 겹치는 경쟁자 | head 결측만으로 분류하지 않음; 독립 owner 증거가 부족하면 보류 |
| 얼굴과 몸은 같지만 실제 wide group / native group | scene mask 불변. 숨겨진 group identity를 새 main으로 출력하지 않음 |
| 실제 zoom/춤의 비강체 움직임 | 전역 affine 불일치만으로 거부할 필요는 없으나 독립 양방향 torso 경로가 실제로 성립해야 함 |

## 비용과 우선순위

MMN68 및 NEON161은 각각 seed-to-seed 49 source frames다. 이미 읽는 source 검사 안에서 buffer를 재사용할 수 있지만, 현재는 첫 body 실패에서 조기 종료하므로 전체 49프레임 검사를 완료하면 기존보다 추가 decode와 계산이 생긴다. 실제 비용은 미측정이며 ‘추가 비용 0’ 또는 ‘5초 이내’를 보장할 수 없다. 향후 조사 시 decode count, 재사용 count, 실패 edge, 양방향 잔존점/오차/분포, 경쟁자 판정, 전체 wall time을 분리 기록해야 한다.

최대 약 1.07초/두 후보의 이득은 현재 짧은 named part와 잘못된 main eligibility의 큰 원인을 해소하지 못한다. MMN50의 예처럼 group gate 탈락이 곧 main 역할로 취급되고 긴 identity가 scene mask에서 잘리는 경로가 별개의 우선 과제다. 이번 결과는 좁은 픽셀 규칙을 더 누적할 근거가 아니라, 이 작은 후보군을 정확히 보존하고 role-eligibility/projection 문제를 우선할 근거로 사용한다.
