# 18개 `unconfirmed_main_role`의 정확한 하위 조건

원본 JSON과 현재 source만 읽었다. 제품/앱 변경, 모델 실행, GPU, 영상 디코딩, 해시 계산 없음. 기존 얼굴벡터의 primary 비교가 필요한 shot 진입 점검은 표준 라이브러리 수치 연산만 사용했으며, 새 얼굴/새 gallery를 생성하지 않았다. 아래는 gate 진단이지 복원 확정이 아니다.

## 핵심 결론

**메인을 선택한 근거와 unknown 이름을 복원할 때 요구하는 근거가 다르다.** `choose_roles`는 중앙 가중 얼굴 점수로도 main을 선택한다. 반면 `recover_observed_member_edges`는 직접 검출된 foreground 역할 anchor와, 모든 새 표본에서 중앙 경쟁자보다1.08배 큰 몸통을 요구한다. 기존 main의 이름 복원에 필요한 역할 연속성보다 전경 우세 조건이 강하게 적용되는 설계상 병목 후보다. 다만 이름 복원에는 별도의 원본 식별 증거가 필요하므로, `measured_face_composition` enum을 허용 목록에 추가하는 것만으로 해결하거나 안전해지지 않는다.

- 대상은 **18클립 /17unknown 블록 /22방향 시도**다.
- 18개 **전부** 몸통 foreground gate에 실패한다. 독립 하위 조건 재계산 결과는 선택 몸통1.08배 미달17개, torso confidence<0.75가11개, torso가몸bbox/화면밖8개, torso높이<화면8%가4개다(중복).
-10개는 직접 `detected` foreground anchor가 없고,4개는 anchor와의 거리0.600001초도 넘는다. 이들은 몸통 조건 실패와 중복된다.
- 모든109개 unknown 표본은 `scene_kind=main`, `scene_reason=main_eligible_composition`이다. role box·owned body·candidate box·원본 retained competitor 목록 불일치 **0건**. 픽셀/정규화 단위나 frame/초 배선 오류 증거도 없다.
- 실제 original role feature는 `detected`60표본 /`missing`37 /`repeated_same_pose_geometry`12다. 현재 shot 경로의 `_fresh_main_role`까지 통과하는 표본은48/109이며, 블록 전체가 fresh인 것은4/17뿐이다.
- 원본 owned 얼굴은57/109표본에서 유효하지만 unknown 내부 accepted joint는0개다(`insufficient`27/`conflict`30/없음52). 얼굴이 존재하는 것과 원본 이름이 확정된 것은 다르다.

## 최초18개 추림의 의미 보정

최초 목록은 **기존 observed_member_edges의 원본충돌/handoff 감사와 겹치지 않고, 클립 내 적어도 한 유효 얼굴이 있는18개**였다. 모든 표본에 얼굴이 있거나 모든 모델에 경쟁 이름이 없는 목록이 아니다. 실제4블록에서는 양쪽에서 서로 다른 이름으로 복원을 제안한다(5클립). 또한 현재 shot 경로가 추가로 읽는 원본 direct-secondary에는 다음 경쟁 증거가 있다.

- ANT148.381467–148.8487, frame8908: 원본 direct-secondary **홍은채**, 제안 이름은 오른쪽 **허윤진**.
- ANT164.931333–165.331833, frame9900: 원본 direct-secondary **사쿠라**, 양쪽 제안은 카즈하/허윤진.
- NEON149.883067–150.283467, frame8992: 원본 direct-secondary **시리**, 왼쪽 제안은 아윤.
- ANT82.182–82.6826의 frames4944/4948 direct-secondary 카즈하는 제안과 일치하나, 역할·경로와 두 얼굴의 독립 간격 조건을 별도로 확인해야 한다.

이 direct-secondary 결과는 저장된 원본 결과다. window/video 복원 이름을 독립 seed로 세지 않았다. 따라서 기존 observer gate에 없던 경쟁자를 지우는 방향의 완화는 부적절하다.

## 공통 코드 원인 후보

1. **선택 기준과 복원 기준의 차이** — `main_role_timeline.py:12`의 face×center 점수와 `observed_member_edges.py:101–113`/`stage_prominence.py:72–73`의 절대 전경 우세 조건. 알려진 이름을 유지하는 group→main 경로와 unknown 이름을 복원하는 경로를 같은 증거로 취급하면 안 된다. 같은 몸의 역할 유지 증거가 foreground 우세와 다른 방식으로 입증될 수 있는지가 향후 제한 실험 대상이다.
2. **실제 경쟁 몸 관측 부족** — 중앙에 걸친 모든 몸통의 confidence/경계를 검사하므로 작은 부분 몸이라도 미관측 경쟁자로 남으면 차단된다. 이는 단순 배선 실패가 아니라 안전하게 해소해야 할 원본 관측 부족이다. 얼굴이 없는 몸을 경쟁자 목록에서 빼면 안 된다.
3. **서로 다른 관측 채널** — full-frame role feature는 missing인데 owned ROI face는 유효한 표본이3개(ANT612/9624, NEON2280) 있다. `collect_geometry`의 전체화면 얼굴 측정과 이후 owned ROI 얼굴 추출은 별도 경로다. 현재 박스 소유권은 맞으므로 자동으로 배선 버그라 부를 수 없다. ROI 얼굴의 새 측정치를 원래 role anchor로 소급 승격하면 원본 증거 의미가 바뀐다.
4. **부차적 source-frame 정밀도 민감성** — ANT160 구간은36프레임=0.6006초여서0.600001초를0.000599초 초과한다.60fps의 동일36프레임은 통과한다. source-frame budget 의미인지 엄밀한0.6초 의미인지 검토할 가치가 있지만, 이 사례는 다른 몸통/shot 증거도 실패하므로 단독 수정의 복원 효과는0이다.

## 대표3범위

### 1. ANT148.381467–148.8487 — 선택 기준 차이와 숨은 경쟁 식별

-7/7표본이 `measured_face_composition`+직접 `detected`, 몸5–6개, 모든 표본이 기존 main이다. weighted face 점수비는1.254–1.548로 선택 몸이 우세하지만, torso비는0.986–1.033으로 모든 표본이1.08 기준에 못 미친다. 직접 foreground anchor도 없다.
- 원본 joint는6conflict/1insufficient, margin0.00174–0.02142이며 accepted0이다. frame8908에는 direct-secondary 홍은채가 있다. 따라서 윤진 이름을 채울 원본 식별 증거가 더 필요하다.
- **현재 shot 경로:** 양쪽 이름이 카즈하/허윤진으로 달라 진입 대상이 아니다. fresh main role은7/7이어도 두쪽 동일 이름과 경쟁 식별 조건을 대신할 수 없다.
- 분류: 배선/단위 문제가 아니라 **선택/복원 역할 기준 차이 + 원본 경쟁 식별**. 가장 대표적인 공통 설계 조사 사례지만 복원 후보 확정은 아니다.

### 2. NEON161.194367–161.728233 — 같은 역할의 몸 경로와 미관측 경쟁자

- original seed쌍9640/9660 및9700/9712는 아이찡. foreground anchor가 존재하고 거리도0.6초 이내다.8개 표본 모두 선택 torso비1.283–1.778로1.08기준을 넘는다.
- 오직 frames9680/9692의 **다른 몸** torso confidence가 차단한다.9680의경쟁몸0은왼어깨0.74414;9692의경쟁몸3은어깨0.74561/골반0.54541·0.67236. 둘 다 얼굴 missing이고 중앙절반과 겹친다. 단순 소수점 여유로 모두 해결되는 상황은 아니다.
- fresh main role은1/8뿐이다. 나머지는 missing/borrowed-size 기반 incumbent 유지다. unknown 내부 joint accepted0:9664는아이찡 insufficient(distance0.63889, margin0.13030),9692는시리 conflict(distance0.80211, margin0.00317).
- **현재 shot 경로:** 양쪽 동일 이름, 원본 양쪽 얼굴 있음. 그러나 사이cut이 없어 `no_source_cut_between_original_faces`에서 거절된다. JSON상 같은 shot의 독립얼굴pair는21개, 표본 지원거리 최대0.333667초다. 이것은 몸 경로 증명 완료를 뜻하지 않는다. 현 코드의 전체 neighbor union 경쟁검사에는 frame9636의 primary영도 걸린다(원본벡터 진단 재계산; 임계값근접아님). 이 프레임은 observer의 왼seed창9640보다 앞에 있어 기존 observer 감사에는 포함되지 않았다.
- 분류: **실제 부분 몸/경쟁자 관측 부족**이 핵심. 같은shot 전용 역할 연속성 실험을 설계할 때 경계/경쟁범위도 함께 검증해야 한다. source chain은 실행하지 않았다.

### 3. ANT160.293467–160.877383 — source-frame 경계와 독립 shot 증거 부족

-9표본 중 role source는직접3/borrowed2/missing4; fresh main role3/9. 선택 torso높이비0.07684–0.09304, 경쟁대비비1.0415–1.1489다.3표본은높이8%미달,4표본은1.08배미달이다.
- 마지막frame9640은마지막direct foreground9604에서36sourceframes 떨어져0.6006초다. 시간 기준 정밀도에 민감하나, 같은9640 torso비1.07804가 별도로실패한다.
- 원래named Kazuha seeds9576/9604는 acceptedjoint이고 margin0.21148/0.18641. unknown내부 acceptedjoint는없고, 현재unknown shot에서원본직접같은이름얼굴은0개다.
- **현재 shot 경로:** 양쪽출력이카즈하이지만 오른쪽0.6초창안 원본확정얼굴이없어 `missing_original_two_sided_faces`. cuts9608/9643이새unknown shot을둘러싸므로 왼쪽seed를그 shot에빌려쓸수없다. 해당shot의독립facepair0개다. 단체중첩도0.05005초 존재한다.
- 분류: **부차적 시간정밀도 민감성 + 실제 shot별 식별지원부족 + torso조건 실패**. 시간창만고치는것은복원근거가되지않는다.

## 현재 shot 경로 전체 요약

17블록 중14개는 인접한 양쪽 동일이름 조건부터 불충족이다. 나머지3개는 다음과 같다.

| 범위 | 첫 진입 결과 | 그 뒤 JSON으로 보이는 추가 미충족 |
|---|---|---|
| ANT9.9098–10.276933 | cut616이 있으므로 cut조건 통과 | fresh role0/5; unknown이속한shot의독립동명얼굴은588한개라pair0. 전체neighbor union에는frame724윤진 원본경쟁이름도 있음 |
| ANT160.293467–160.877383 | 오른쪽원본얼굴없음 | unknown shot직접얼굴0/pair0; fresh3/9; group중첩 |
| NEON161.194367–161.728233 | 같은shot이라cut없음 | pair21개와표본지원.333667초는있으나 fresh1/8,경쟁몸confidence2표본,전체union경쟁이름 |

현재shot의 모든 새source-frame 지원, `_identity_boundaries`/반복 alien 판정, 경계관측, handoff on support path, 실제소스body/colorchain은 이번에 실행하지 않았다. 이들을 통과했다고 주장하지 않는다. 특히 단순 `cutrequired` 제거는 안전성 증명이 아니다.

## 산출물과 검증

- `role-gate-18-details.json`:22방향 시도와 각원본표본의 역할·선택source·body수·비율·margin·torso실패,0건의박스/목록불일치.
- `role-gate-18-shot-entry.json`:17블록의fresh role,양쪽이름,원본face/pair/support,shot진입조건,추가경쟁식별.
- `audit_role_gates.py`, `audit_role_shot_json.py`:표준라이브러리JSON 진단스크립트. 원본 프로젝트는읽기만하며 scratch에만결과기록.
- primary참조 재계산은기존JSON embedding의거리계산이며 float64진단이다. 임계값1e-5근처는민감값으로표시했으며 위3개shot진입후보에서는그러한값이없었다.5개unknown direct-secondary이름은계산이아닌원본저장결과다.

**제품 변경 없이 후속 실험용 원인 후보만 정리했다. 새 복원 확정은0개다.**
