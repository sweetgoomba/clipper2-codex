# Identity span × main eligibility: 최신 실제 앱의 조립 경계 감사

대상은 MMN `1793649506337`, ANT `1793649573540`, NEON `1793649654322`다. 상류 main/group 판정, main eligibility, 원래 identity span과 원본 관측을 바꾸지 않는 범위로 분석했다. 영상·모델을 열거나 추론하지 않았고 제품 코드를 수정하지 않았다. 저장된 JSON과 reference embedding의 대조 산술만 사용했다.

현재 최종 main 출력은 288개(named 200, unknown 88), main의 1초 미만은 144개(named 64, unknown 80)다. group 포함 최종 출력 374개/short 195개와 구별한다. 이 감사에서 short는 분석용 집계 기준이며 삭제·승격 기준이 아니다.

## 1. 교집합이 만든 짧은 조각의 양

| 구분 | MMN | ANT | NEON | 합계 |
|---|---:|---:|---:|---:|
| named short 전체 | 6 | 23 | 35 | 64 |
| 단일 identity span이 eligibility에서 잘린 named short | 1 | 11 | 14 | **26** |
| 위 중 원래 identity span 길이 ≥1초 | 0 | 6 | 10 | **16** |
| 원래부터 짧았던 named identity span | 5 | 12 | 20 | 37 |
| 후속 여러 span 조립 결과인 named short | 0 | 0 | 1 | 1 |
| unknown short 전체 | 14 | 22 | 44 | 80 |
| identity × eligibility의 정확한 교집합인 짧아진 unknown | 5 | 6 | 18 | **29** |
| 위 중 원래 identity span 길이 ≥1초 | 0 | 2 | 8 | 10 |
| handoff/후속 분할로 단일 span에서 다시 나뉜 unknown short | 2 | 3 | 4 | 9 |
| 원래부터 짧았던 unknown identity span | 7 | 12 | 20 | 39 |
| 후속 여러 span 조립 결과인 unknown short | 0 | 1 | 2 | 3 |

즉 144개 main short 중 **55개(26 named +29 unknown)**가 원래 span과 고정된 eligibility를 교차하여 짧아진 정확한 결과다. 그러나 그 사실만으로 잘못된 조각이거나 없애도 되는 출력은 아니다. 나머지 handoff 분할을 eligibility 교집합 효과로 섞지 않았다.

`inventory.json`의 `exact_identity_eligibility_intersection`은 실제 최종 main coverage union과 원래 identity 범위의 교집합이 해당 출력 범위와 같은지 확인한 값이다. 영상이나 scene classifier를 다시 평가하지 않았다.

## 2. 얼굴 존재와 이름의 독립 채택을 분리한 결과

증거를 다음처럼 구분했다.

- 원본 query 한 시점의 AuraFace 직접 reference 채택과 원본 frozen-video anchor 대조.
- 저장된 SFace 원본 query의 reference/video 채택. `secondary_*_window_match`는 이 범주에 넣지 않는다.
- 저장된 joint accepted 이름.
- 주변 window 또는 timeline 문맥으로 붙은 이름은 별도 보존한다.

같은 source frame에 두 모델이 답해도 한 관측으로만 센다. ‘pair’는 기존 시간 독립성인 서로 0.15초 이상 떨어진 두 관측이 fragment 안에 있다는 진단이며 새 출력 요구 조건이 아니다. 같은 query의 다른 모델/윈도우를 독립 시점으로 중복 집계하지 않았다. 서로 충돌하는 채택과 joint conflict는 JSON에 별도로 남겼다.

원본 reference 벡터의 직접 판정은 원래 `ReferenceObservationMatcher`로 fragment 관련 137개 관측을 재대조했고, 진단 산술의 이름과 137/137 일치했다(`cached-primary-source-comparison.json`). 원본 primary frozen-video 대조는 공개된 anchor/거리 규칙을 저장 벡터에 적용한 진단이다. SFace 및 joint는 저장된 결과를 그대로 읽었다. 새 모델 실행은 없다.

| eligibility에서 잘린 named short 26개 | MMN | ANT | NEON | 합계 |
|---|---:|---:|---:|---:|
| 조각 안에 시간 독립적인 per-frame 이름 pair | 0 | 3 | 5 | **8** |
| 조각 안에 per-frame 이름은 있으나 pair 시간폭 부족 | 0 | 6 | 4 | **10** |
| 해당 이름의 per-frame 채택이 조각 밖에만 있음 | 1 | 2 | 5 | **8** |

전체 named short 64개로 범위를 넓히면 pair 42개, pair 없는 per-frame hit 14개, 내부 per-frame name 없음 8개다. 따라서 ‘짧으니 직접 이름이 없을 것’이라는 가정은 맞지 않는다.

### 내부에 해당 이름의 per-frame 채택이 없는 8개

합계 1.918683초다. 아래 표는 이름 정확성의 최종 판정이나 일괄 거부 목록이 아니다.

| 영상 / 최종 구간 | 이름 | 원래 identity 범위·근거 | 독립 이름 support의 위치와 보호 사항 |
|---|---|---|---|
| MMN 50.650600–50.683967 | 김채원 | [50.283667,50.683967], timeline consensus | 유일한 원본 per-frame Kim 채택 f3032는 group 안/main eligibility 밖. 내부 f3036은 ROI face가 있지만 SFace window 이름이다. 상세 아래. |
| ANT 156.156000–156.756600 | 카즈하 | [156.122633,160.293467], timeline consensus | 뒤쪽 다른 main 조각에 다수 accepted 얼굴. 현재 9개 얼굴은 joint conflict/insufficient; 내부 cut f9373. 가까운 다른 main evidence가 있다는 이유로 cut을 넘겨 연결할 수 없다. |
| ANT 160.877383–161.561400 | 카즈하 | [160.877383,164.931333], timeline consensus | 뒤쪽 다른 main 조각에 support; f9704 일부는 group. 내부는 face/head 결측·낮은 score·joint conflict/insufficient. 시작 source cut f9643. |
| NEON 82.849433–83.016267 | 시리 | [82.849433,84.984800], timeline consensus | support는 뒤 group 및 다른 main 조각. 내부 f4968·4972는 joint conflict. |
| NEON 86.352933–86.419667 | 보라 | [84.984800,89.589400], timeline consensus | support는 다른 group/main 시점. 내부 유일한 f5176은 joint conflict. |
| NEON 150.283467–150.550400 | 시리 | [150.283467,151.684867], timeline consensus | **모든 원래 per-frame Xili 채택 11개(f9036–9088)가 main eligibility 밖**. 내부 f9008/9012/9016/9020은 insufficient/conflict. |
| NEON 187.720867–187.754333 | 영 | [186.753133,187.754333], timeline consensus | **모든 원래 per-frame Young 채택 f11236/11240/11244가 main eligibility 밖**. 내부 유일한 f11252는 Young이 아닌 **아이찡 joint accepted**. 단순 face 존재로 parent Young을 계승한 모순 사례다. |
| NEON 210.877333–210.944067 | 영 | [209.375833,211.077533], **member_body_continuity** | 내부 f12640은 joint conflict이고 named face는 밖이지만, 이 parent는 이미 별도 몸 연속성 증명을 거친 결과다. 직접 얼굴 없는 fragment라는 이유만으로 기존 독립 몸 proof를 무시하면 안 된다. |

이 중 ‘원래 span의 모든 per-frame name support가 eligibility 밖’인 것은 정확히 **MMN50, NEON150, NEON187의 3개/0.333767초**다. 나머지 5개는 같은 parent의 다른 main 부분에 support가 있다. 특히 몸 연속성으로 인정된 NEON210은 timeline consensus와 별도 계약이다.

이 8개의 이름을 단순 unknown으로 바꾸는 것은 clip 축소 성과가 아니다. 기존 main coverage는 그대로 남으므로 unknown이 증가할 수 있고, 다른 검증 없이 unknown 이웃으로 합치면 handoff/cut을 감출 수 있다.

## 3. MMN50의 구체적인 독립 증거

f3036(50.6506)은 confirmed owned ROI face, detector score 0.845010이다. 그러나 이름 결과는 다음과 같다.

| 원본 시점 | 원본 직접 AuraFace | joint | SFace 결과 | scene |
|---|---|---|---|---|
| f3020 | 직접 이름 없음 | insufficient | Kim **reference window** | group |
| f3024 | 직접 이름 없음 | insufficient | Kim **reference window** | group |
| f3028 | 직접 이름 없음 | insufficient | Kim **reference window** | group |
| f3032 | 직접 이름 없음 | insufficient | Kim **직접 reference match** | group |
| f3036 | 직접 이름 없음 | insufficient | Kim **reference window** | main |

f3036 원본 AuraFace centroid의 best는 홍은채 0.760297, 김채원은 0.808987로 직접 이름은 거부된다. 두-photo fallback도 채택하지 않는다. 저장된 joint의 Kim best 평균 거리는 0.677584, margin 0.030357로 `insufficient/name=null`이다. 이는 ROI face 존재와 Kim의 독립 채택이 다름을 수치로 보여준다.

원래 `member_timeline_consensus` [50.283667,50.683967]이 main eligibility [50.6506,…]와 만나 2 source-frame 조각을 만든다. 현재 `validate_identity_padding`은 parent의 **어떤 유효 얼굴이든** 실제 관측 범위 안에 fragment가 있으면 검사하지 않는다. 따라서 f3036 face가 있는 이 조각은 gate를 실행하지 않는다. 이것이 Kim 직접 증명을 통과했다는 뜻은 아니다. 상류 group/main 판정을 고칠 필요 없이, 출력 조립이 소비한 identity evidence의 종류를 구별해야 하는 사례다.

## 4. 같은 이름 인접 span을 합치는 잔여 효과

원래 같은 이름으로 맞닿은 identity 경계는 MMN 10개, ANT 3개, NEON 2개, 총 15개다. **13개는 이미 최종 출력에서 합쳐졌다.** 남은 MMN70.820750과 NEON140.039800은 group mask 안으로 들어가는 경계여서 양쪽 named 출력이 서로 맞닿아 있지 않다.

최종 결과에 그대로 남은 ‘맞닿은 같은 이름 출력 경계’는 **0개**다. 단순 adjacent same-name merge로 얻을 잔여 효과도 0이다.

한 named parent가 여러 출력으로 나뉘어 남는 경우는 MMN 1개, ANT 10개, NEON 12개, 총 23개 parent다. 여러 원래 span을 합친 출력의 provenance도 포함한 수치다. 그 사이에 eligibility의 실제 구멍이 있으므로 이를 연속 시간 clip으로 합치면 main 영역 확대/group 흡수가 된다. 현재 승인 범위에서는 해당 구멍을 유지해야 한다.

## 5. 같은 관측 사건에 두 경계를 적용한 5개

다음은 ‘작아서’ 찾은 후보가 아니다. 원래 identity의 미확정 midpoint와 handoff의 첫 새 관측 또는 첫 제외 scene 관측이 **같은 원래 4-frame bracket**을 가리키며, 그 사이 fragment에 원본 샘플이 하나도 없는 경우다. 원래 source-refined boundary frame이 있으면 제외했고, bracket 안에 saved source/scene cut이 없는 것을 확인했다.

| 구간 | 중복 사건 | 원본 근거 | 조립상 취급 후보 |
|---|---|---|---|
| MMN 88.254833–88.288200 | f5288↔5292 midpoint + f5292 first-observed handoff | outgoing f5288 Kim joint accepted, detector 0.912707; incoming body handoff는 f5292에서 유지 | 같은 bracket의 경계를 88.2882로 통일하고 outgoing Kim 끝을 그 시각까지 유지하는 후보. 이후 incoming unknown/handoff는 보존. |
| NEON 34.334300–34.367667 | f2056↔2060 midpoint + f2060 handoff | outgoing f2056은 joint conflict, best 아이찡; 시리의 새 독립 근거가 아님 | **시리 이름 연장 금지.** 동일 bracket이라는 사실만으로 이름을 복원하면 안 되는 실제 negative. |
| NEON 42.609233–42.642600 | f2552↔2556 midpoint + f2556 첫 group 관측 | 기존 outgoing은 unknown. incoming Oa의 직접 얼굴 f2560/2564는 group 관측으로, main fragment의 직접 support가 아님. 현재 tiny는 unsupported padding으로 이미 unknown | 고정 main 끝 42.6426까지 outgoing unknown을 유지하는 후보. 새 이름·main 시간 없음. |
| NEON 189.956433–189.989800 | f11384↔11388 midpoint + f11388 첫 group 관측 | outgoing f11384 메르시 joint accepted | 고정 main 끝 189.9898까지 outgoing 메르시를 유지하는 추가 후보. incoming group/이름을 흡수하지 않음. |
| NEON 221.854967–221.888333 | f13296↔13300 midpoint + f13300 첫 group 관측 | 기존 outgoing unknown, f13296 joint conflict | outgoing unknown을 고정 main 끝까지 유지하는 후보. outgoing 이름을 만들지 않음. |

예상 4개가 전체 보호 조건을 통과한다면 조립만의 변화는 main clip 288→284, main short 144→140이다. named clip 200개 및 named short 64개는 **그대로**다. unknown clip 88→84, unknown short 80→76, unknown duration은 두 named 사례의 합계 **0.066733초**만 줄어든다. 두 unknown 사례는 unknown 시간을 그대로 유지한다. 이는 아직 구현/replay 결과가 아닌 정확한 후보별 산술 상한이다.

현재 source cut, incoming owned frame, 실제 handoff를 바꾸지 않는 계약이 전제다. 같은 시간 폭이라는 이유만으로 무관한 midpoint와 다른 몸의 handoff를 합칠 수 없다. original left/right frame이 정확히 일치하고, 원본 owner가 일치하며, source-refined cut이 없고, named 연장에는 outgoing 독립 이름 관측이 있어야 한다. 이번 fixture는 그 조건을 검토하는 재현 자료이며 제품 코드는 작성하지 않았다.

## 6. 짧아도 보호해야 할 원본 교대

64개 named short 중 38개는 eligibility에 의해 잘려 생긴 named short가 아니다. 이 중 34개에는 fragment 안에서 독립 per-frame name pair가 있다. 예를 들어 MMN26.142783–26.393033 카즈하, MMN103.253150–104.020583 홍은채, ANT149.916433–150.383567 카즈하, NEON177.076900–177.410567 영은 서로 다른 이웃 이름/원본 얼굴/handoff 또는 cut 근거를 가진다.

전체 named short 중 saved source cut이 구간 안 또는 정확한 끝에 있는 것은 31개, handoff bracket과 닿는 것은 10개다(서로 중복 가능). 두 조건 중 하나 이상은 37개다. 이는 실제 영상 ground truth를 새로 확정한 숫자가 아니라 함부로 경계를 제거할 수 없다는 원본 보호 근거다.

또 eligibility에서 잘린 조각 자체에도 직접 이름이 있는 반례가 있다. ANT97.2972–97.4974는 0.2002초지만 f5832/5840의 직접 Kim 채택과 끝 cut f5844가 있다. NEON52.8528–53.119733은 f3180 Oa 채택이 있다. pair 시간폭이 부족하다는 이유로 이들을 삭제하거나 무조건 unknown으로 바꾸는 것은 이번 분석에서 정당화되지 않는다.

## 산출물 및 재현

- `classified-shorts.json`: 144개 main short 전수, parent span, 원본 관측별 per-frame/window 이름, source cut/handoff, 조립 분류.
- `inventory.json`: 전체 main parts 및 cached per-frame 비교 진단. 모델 벡터를 새로 만들지 않음.
- `coincident-boundary-events.json`: 동일 bracket 사건 5개와 보호 조건.
- `coincident-fixture.json`: 5개 원본 회귀 fixture. 각 bracket 직전 0.6초부터 우측 0.1초까지 pose 11개와 owned observation 11개(원래 embedding 포함), joint 원본 scalar 결과, cut/handoff/출력 범위/이름/근거. 큰 model candidate 배열은 생략.
- `coincident-fixture-provenance.json`: 원본 JSON 경로·SHA-256, fixture SHA, 추출 스크립트 경로.
- `cached-primary-source-comparison.json`: 137개 원본 matcher와 저장 벡터 진단의 이름 일치 확인.

Fixture SHA-256: `6854cc4ace7f30b11441b0f484cf50e04764dc7806cbd5949d18e0440f2e93c3`.

상류 메인/단체 판정 변경, main 확대, group 흡수, 짧은 출력 삭제, 새로운 identity 생성, 원본 span 수정은 제안하거나 수행하지 않았다. 이번 범위에서 정량화된 구조적 조립 후보는 위 네 개이고, MMN50 등 이름 support가 제외 영역에만 있는 조각은 별도의 identity evidence 계승 문제로 기록했다.
