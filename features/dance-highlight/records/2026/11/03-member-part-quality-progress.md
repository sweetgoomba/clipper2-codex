# 멤버 구간 품질 개선 진행 — 2026-11-03

이 문서는 개발 중간 기록이다. 이후 보완·폐기 및 실제 앱 재실행까지 완료했으므로 **[최종 결과](03-member-part-quality-results.md)를 우선 참조한다.** 아래의6쌍 unknown 초안은 반복 얼굴 변화 보호를 추가해5쌍으로 줄였고, camera 예외는 폐기했다. baseline은424 clips /240 short /unknown38.976067초다.

## 독립 검증으로 확인한 원인
- 인접한 동일 이름의 미병합 short는 0개. named short73중33개는 unknown에 닿고, unknown short88·group short79가 있다.
- 기존 MMN카즈하89–93은 이미한행, Sakura45–48도이미포함. 원래 incoming preparation의Yunjin겹침은의도된출력으로 보존한다.
- 단순한 양끝동일이름 gap만수정하면 대부분의short는남는다. unknown 한쪽경계28블록/다른이름양끝19블록/동일이름양끝14블록으로구분한다(정답/안전병합가능량아님).
- NEON185.251733–185.318467: 같은head+torso의중복검출을인원수에는하나로, 규모비교에는서로다른몸으로쓰는불일치. 잘못늘어난발때문에group→unknown2frame+Merci2frame→group.
- NEON154–157원경군무는native발견누락/장식물부분포즈/크기검증이원인이며현재단계의한수정으로전체가해결되지는않음.

## 채택 중인 수정과 구분해야 할 성과
1. observed_member_edges: 원래독립얼굴2개와관측된selected main경로로한쪽unknown경계를복원한다. 중앙의미관측경쟁자/duet/역할양성없는원경은제외. 원래얼굴검출에서확인한전경근거+torso규모관계,source전체cut,실제cadence,역할handoff모두검증한다. 새label은얼굴anchor가되지않는다.
   - 초기4후보2.969833초는독립검증에서3개역할근거부족으로폐기.
   - 현재저장증거replay: ANT48.081367–48.415033 김채원0.333667초만. 영상당0.03–0.33초.
   - 동시record/observation누락과퇴화torso반례를RED→GREEN으로수정. 독립Astra22조건pass.
2. unknown-unknown연결: 이름은unknown그대로,같은실제selectedbody가원본영상에서계속이어지는불필요한내부경계만제거. 19쌍중6쌍통과/13쌍보존. 예상clip6개/short7개감소, unknown시간감소0·새멤버복원0. 독립원본overlay검증완료. 외곽cut/handoff/group경계보존.
3. scene중복규모정규화: 원본pose/body/identity/진단을삭제하지않고distributed_full_body_ensemble의local규모계산만정규화. 기존+새99회귀pass. 전체재생과코드독립검증진행중.

## 폐기·보류
- native주변전신관측확장: 저장3영상에서신규지원0으로제품수정되돌림. 실험만tmp보관.
- unknown3후보(ANT149,181/NEON38)에이름을무리하게붙이는초안은폐기.
- globalSIFT/국소SIFT/KLT만으로MMN38줌구간을안전하게해소하지못함. threshold완화없이계속보류.
- ANT9.9조명/줌은원본카메라변화양성증거추가연구중. 아직제품적용아님.

## 검증·다음
- 새edge단위16pass,부분통합24pass,첫Dance전체1025pass(그후unknown7/scene9추가중).
- SAM 두단계는계속주석처리/off. Person/sharedSDK는이번변경없음.
- 소스확정→독립코드감사→최종Dance/full검사→원본Electron build:app:mac:arm64:local-api→같은3YouTube실제앱순차측정. 이름복원/단순unknown연결/잘못된개인조각의group환원을별도로집계한다.
- 현재남은대부분의short/오분류가해결됐다고주장하지않는다.

실험루트: /private/tmp/dance-member-part-20261102
독립Astra: /private/tmp/dance-member-part-review-20261102
scene하위검증: /private/tmp/dance-member-scene-proposal-20261103
source변화하위검증: /private/tmp/dance-member-source-proof-20261103
