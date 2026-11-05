# MMN 실제 앱의 잔여 짧은 main clip — JSON 감사

기준: 프로젝트 `1793649506337`, `json/dance_meta.json`와 `diagnostics/face_evidence.json`. 현재 ANT/NEON 벤치마크 중에 수행한 JSON/소스 읽기만의 분석이다. 영상 decode, 모델, 테스트, 파이프라인 replay, 제품 수정은 수행하지 않았다. 구간은 초 단위 반개구간이며 표의 소수는 표시용으로 반올림했다. 정확한 값과 전체 근거는 `short-evidence.json`에 있다.

이번 실제 앱은 사쿠라 35.435400–42.976267을 한 part로 복원했다. 전체 unknown은 6.807200→5.672633초다. 남은 main의 1초 미만은 named 6개(2.402300초), unknown 14개(4.437967초)다. 나머지 unknown 한 개는 1.234667초다. 최종 출력은 68개/short 27개이고, group 중복 출력 제거 전 진단은 85개/short 39개다. 중복 group 제거는 이름 회복으로 세지 않는다.

named 6개를 모두 불필요한 조각으로 볼 수 없다. 4개는 다른 멤버의 독립 얼굴 및 cut/handoff가 있는 보호 대상이고, 68초 홍은채는 같은 이름 사이 관측 공백 때문에 분리된 실제 조사 대상이다. 50.6506의 2프레임 김채원은 긴 identity와 순간 main eligibility의 교집합이다. 여기에는 실제 얼굴이 있지만 독립적인 개인 주역 우위는 확인되지 않았다.

## Named short 6개

| 구간 | 이름 / 길이 | 실제 근거와 해석 |
|---|---|---|
| 26.142783–26.393033 | 카즈하 / 0.250250 | f1568/1572/1576/1580 모두 joint accepted 카즈하. 독립 원본 support f1568·1580(0.2002초). 시작 cut f1567, 뒤 f1580→1584 confirmed handoff. 양옆은 김채원·홍은채다. 다른 이름을 잇기 위해 삭제할 근거가 없다. |
| 50.650600–50.683967 | 김채원 / 0.033367 | 원래 identity [50.283667,50.683967] 중 scene main이 시작된 뒤의 2프레임만 남았다. f3036에 confirmed owned face 및 직접 role face가 존재한다. 다만 5인 전신군무에서 group 규모 조건이 탈락하여 main으로 넘어간 경계이며 개인 주역 우위의 독립 증거는 부족하다. 아래 상세 참조. |
| 68.835533–69.436033 | 홍은채 / 0.600500 | 앞 홍은채 part와 사이에 unknown [68.301467,68.835533]이 있다. f4136–4160의 7개 joint accepted 및 원본 support는 확실하다. 오른쪽 경계는 cut f4162와 허윤진으로의 변경이므로 왼쪽 공백만 조사 대상이다. |
| 88.421667–88.855433 | 허윤진 / 0.433767 | f5304–5324 6개 joint accepted; 원본 support f5312·5324. 앞은 김채원/unknown, 뒤는 카즈하. 앞 body handoff f5292, 내부 cut f5315. 같은 이름 part의 분열로 볼 수 없다. |
| 102.936167–103.253150 | 카즈하 / 0.316983 | f6184·6188 accepted 카즈하. f6172는 홍은채 best의 conflict, f6176은 detector 0.771, f6180은 insufficient여서 시작 부분은 덜 확실하다. 그래도 body handoff f6172 및 끝 cut f6189와 실제 카즈하 양성 얼굴이 있어 양옆 홍은채로 무조건 합치면 안 된다. |
| 103.253150–104.020583 | 홍은채 / 0.767433 | f6192–6232 11개가 모두 joint accepted 및 원본 support. 시작·끝 cut f6189/6191·6235, 뒤는 허윤진. 교대 보호 근거가 있는 짧은 part다. |

이 표의 ‘교대 보호’는 저장된 양성 증거를 뜻한다. 이번 JSON 감사만으로 영상상 실제 교대를 새로 확정한 것은 아니다. joint 상태도 원래 primary/timeline 결정과 동일한 단일 판정기가 아니므로, insufficient의 best 이름을 확정 이름으로 취급하지 않는다.

## Unknown short 14개 — 9개 국소 문제

| 최종 출력 구간 (길이) | 현재 거부 이유 / 정확히 부족한 관측 |
|---|---|
| 34.434400–34.734700 (0.300300), 34.734700–34.834800 (0.100100) | 양옆 사쿠라이지만 body 후보 전체 [34.4344,35.4354]는 `conflicting_face_evidence`; member edge는 `unconfirmed_main_role`; unknown join은 `visual_cut`. f2064는 낮은 score, f2076 face missing, f2084는 허윤진 best의 joint conflict. cut f2078도 존재한다. 후반은 group이 가린다. 원본 얼굴/역할 공백과 충돌을 양끝 이름으로 덮을 수 없다. |
| 42.976267–43.143100 (0.166833) | 사쿠라→허윤진 사이. f2576 face missing, f2580 head unconfirmed, f2584는 김채원 best conflict. f2584→2588 confirmed handoff. 양쪽 member edge는 `unconfirmed_main_role` / `main_handoff`. incoming 멤버의 accepted 얼굴이 이 구간 안에는 없다. |
| 49.866483–50.250200 (0.383717) | 시작 cut f2989. f2992 홍은채 best insufficient, f2996 face ambiguous, f3000/3008 head unconfirmed, f3004 score 0.291. 이후 group과 f3020 handoff. 원래 주역의 소유 얼굴·head 및 역할 연결이 부족하다. |
| 52.485767–52.652600 (0.166833), 53.119733–53.420133 (0.300400) | **한 unknown identity span** [52.485767,53.420133]을 중간 group [52.6526,53.119733]이 나눈 두 출력이다. 앞 f3148 score 0.363, f3152 face missing; 직전 cut f3144. 뒤 f3184–3196 insufficient(허윤진/사쿠라 best 혼재), f3200 사쿠라 best conflict. 오른쪽 member edge는 `unconfirmed_main_role`. 왼쪽 available high-score support f3120·3124·3128은 0.133467초 범위여서 기존 독립 support 0.15초를 충족하지 못한다. 두 개의 별도 얼굴 실패로 중복 집계하지 않는다. |
| 57.791067–57.891067 (0.100000) | f3464 카즈하 best insufficient, f3468 face missing. 앞은 group, 뒤는 긴 unknown. 내부 cut f3467; unknown join `visual_cut`. 구간을 이름 붙일 직접 근거와 cut을 넘는 연결 근거가 없다. |
| 68.301467–68.835533 (0.534067) | 양쪽 홍은채, source cut/handoff 없음, scene main과 candidate body 35 유지. body bridge는 `unconfirmed_body_continuity`이고 f4092 pose fallback만 기록됐다. f4096 face missing, f4100–4120 여섯 관측은 head unconfirmed, f4124 score 0.551. **몸 bbox/torso가 사라진 것이 아니라 head에 의존한 고유 몸 대응이 부족하다.** 아래 상세 참조. |
| 88.254833–88.288200 (0.033367), 88.288200–88.421667 (0.133467) | 한 unknown identity span을 confirmed body handoff f5292가 나눴다. 첫 2프레임에는 원래 분석 샘플 자체가 없다. 두 번째는 f5292 허윤진 best insufficient, f5296 face ambiguous. 양쪽 member edge `main_handoff`, unknown join `missing_boundary_observation`. 샘플 없는 경계 조각과 실제 관측된 몸 교대를 구별해야 한다. |
| 96.346250–97.030267 (0.684017), 97.030267–97.297200 (0.266933), 97.297200–97.847750 (0.550550) | 카즈하→홍은채 사이 세 identity span. 시작 cut f5775. f5776에는 **accepted 허윤진** 한 관측이 있으나 이어 face missing/low-score, 카즈하 best conflict/insufficient, ambiguous, 후반 head missing 및 홍은채 best conflict가 섞인다. 양쪽 member edge `conflicting_original_face`; unknown joins `conflicting_original_names` / `unconfirmed_body_continuity`. 서로 다른 양성 얼굴 증거를 포함하므로 단순한 하나의 harmless unknown gap이 아니다. |
| 111.861750–112.579133 (0.717383) | 시작 cut f6705. f6708 score 0.749; f6712–6740 여덟 유효 얼굴은 김채원 best지만 모두 joint insufficient, f6744 face ambiguous. 왼쪽 member edge `unconfirmed_main_role`; 이후 group을 지나 김채원 named가 시작한다. 일관된 best는 존재하나 현재 accepted identity 및 역할 연결 증거가 부족하다. |

14개는 원래 12개 identity span에서 나온다. 52초의 group projection과 88초의 handoff projection이 각각 한 span을 둘로 만든다.

최종 14개 안의 원본 owned observation 66개 중 24개는 unassigned다(head unconfirmed 13, face missing 7, face ambiguous 4). 나머지 42개 중 7개는 detector score <0.8이다. joint 평가가 가능한 35개는 insufficient 25, conflict 9, accepted 1(f5776 허윤진)이다. 주요 손실은 원본 소유 얼굴/head 결측과 얼굴 근거 부족·충돌이며, 이름을 출력 형식만 바꾸어 회복할 수는 없다.

## 50.6506의 2프레임: 이름 관측은 있으나 독립 역할 우위는 부족

f3036의 원본 owned face는 association confirmed, detector score 0.845이며 role feature도 `source=detected`, size 29.492, reason `measured_face_composition`이다. torso 4점 confidence는 모두 0.981 이상이다. 따라서 ‘아무 얼굴/역할 관측도 없는 가짜 이름’이라고 설명하면 틀리다.

동시에 전신 관측은 5명이고 다른 네 사람의 직접 face size는 31.48–40.41로 선택자의 29.49보다 크다. cropped foreground도 없다. group→main은 f3032에서 모두 360px(H/3) 이하였던 head-to-ankle extent가 f3036에서 다른 몸 하나 363px로 올라간 시점과 일치한다. 수평 spread 0.410은 다른 distributed 조건의 0.5에도 미달한다. 이 구조에서는 `distributed_full_body_ensemble=False` 뒤 selected body가 있으면 `main_eligible_composition`으로 내려온다. 이 순간 group 불합격이 개인 주역의 독립 양성 증명이 되는 것은 아니다.

원래 김채원 identity는 [50.283667,50.683967]이며 f3036이 그 안에 실제로 존재한다. main mask 시작 50.6506과 교차하여 마지막 0.033367초(2 source frames)가 남는다. `validate_identity_padding`은 원래 유효 얼굴 범위 밖에만 생긴 projection을 검사하므로, f3036을 포함하는 이 조각에는 적용되지 않는다. 해당 padding audit가 빈 것은 추가 role proof를 통과했다는 뜻이 아니다.

group은 바로 양옆에 붙어 있지 않다. 왼쪽 group은 [50.2502,50.6506], 다음 오른쪽 group은 [52.6526,53.119733]이다. group continuity가 검사하는 사이 전체 [50.6506,52.6526]에는 실제 cut f3047(50.834117), f3144(52.4524)가 있어 연결을 보류한다. 이는 f3036의 단독 주역 우위를 검증한 결과가 아니라 넓은 group-gap의 cut guard 결과다. 원본 cut 50.834117은 반드시 보존해야 한다.

결론: 이 조각은 실제 얼굴을 가진 긴 identity와 scene mask 경계가 만드는 projection 잔여이며, 현재 JSON의 독립 개인 주역 근거는 약하다. 짧아서 삭제하거나 identity가 틀렸다고 처리할 문제가 아니다.

## 68초 홍은채: 남은 관측 공백과 증명 범위

body 후보는 unknown [68.301467,68.835533]이며 독립 named face seed는 f4088(68.201467)와 f4136(69.002267)이다. 원본 source frame 전체 경로는 4088–4136, 49프레임이다. output gap만 검사하면 안 된다.

| 원본 프레임 | 실제 관측 |
|---|---|
| 4088 | owned face score 0.891, joint accepted 홍은채; torso min 0.931 |
| 4092 | pose face missing; body pose fallback 통과가 audit에 기록됨 |
| 4096 | face missing. f4092와 공통 confidence≥0.5 head는 귀 하나뿐; strict pose의 head 2점 요구 불충족 |
| 4100–4120 | six head-unconfirmed samples. head confidence≥0.5는 각 0–1개지만 torso 4점은 모두 ≥0.903 |
| 4124 / 4128 | owned face는 있으나 detector score 0.551 / 0.411 |
| 4132 | confirmed owned face score 0.858, joint conflict/name null. 이 관측은 output unknown 밖이나 **필수 seed-to-seed 경로 안** |
| 4136 | owned face score 0.933, joint accepted 홍은채; 뒤 accepted support 계속 |

몸 bbox와 torso는 전 관측에 존재하며 scene은 main이고 candidate track id는 35로 유지된다. 이는 이름/몸 연속성의 결론 자체는 아니지만, ‘몸을 검출하지 못해 생긴 공백’과는 구별된다. 원본 head는 f4092→4096부터 공통 2점이 부족하고 f4100–4120에서는 코/눈/귀의 유효점 자체가 0–1개다. JSON만으로 등을 돌렸는지, 실제 가림인지 시각적 원인을 단정하지 않았다.

현재 audit에는 body appearance가 최초 실패한 edge가 저장되지 않는다. 따라서 ‘4096에서 실제 첫 실패’라고 확정할 수 없다. 확인되는 것은 f4092에서 appearance 대신 pose가 성공했고, 그 이후 body continuity가 보류됐으며, 위 head 부족 edge에서는 strict pose fallback이 성립하지 않는다는 점이다. selected torso의 존재만으로 경쟁 몸과의 고유 대응까지 입증된 것은 아니다.

4132의 primary best는 홍은채(0.8118), secondary best는 카즈하(0.6709; 홍은채 0.6967)다. accepted 타인 이름이 있는 것은 아니다. 원래 AuraFace embedding과 양 seed의 거리는 각각 0.8504/0.8681로 단일 alien 관측이다. 기존 body contract는 (1) 유효한 다른 accepted 이름 또는 (2) 0.15–0.6초 간격의 서로 일치하는 alien 두 관측을 거부한다. 이 후보는 그 검사를 이미 통과했다. 보완 설계는 이 계약을 완화하지도, generic joint-conflict veto를 새로 추가하지도 않는다. 4132의 충돌을 삭제하거나 조사 경로 밖으로 빼서는 안 된다.

추가 torso pixel 검증의 안전 계약과 3영상 후보 상한은 `bounded-torso-design.md` 및 `body-candidate-inventory.json`에 따로 남겼다. 이번에는 구현하지 않기로 결정했다.
