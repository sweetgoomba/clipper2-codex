# 안무 하이라이트 독립 품질 검토

2026-11-02 · 요청된 Astra 검토 결과 · 제품 수정·커밋·푸시 없음

> 최신 후속 결과는 **10절**에 있다. 초기 one-sided 미확인 복원안은 제품에 적용하지 않았다. 실제 적용은 ANT 이름 경계 0.283617초 교정 한 곳이며, 실제 앱 세 영상 비교에서도 해당 경계·썸네일 외의 출력 변화나 SAM 재활성화는 없었다. 아래 초기 제안은 검토 이력으로 보존한다.

## 결론과 먼저 적용할 후보

현재 문제는 얼굴 모델 하나의 실패로 설명되지 않는다. **얼굴 근거의 공백을 먼저 출력 경계로 바꾸고, 단체임을 입증하지 못한 관측을 개인 메인으로 남긴 다음, 여러 복원 단계가 이를 다시 연결하는 구조**가 품질의 주요 병목이다. 기존 미확인·컷 거절 조건을 일괄 완화하면 원경 메인 오선택을 강화하는 반례가 실제로 나온다.

기존 관측만으로 부모가 먼저 구현할 최소 후보는 **동결된 원본 얼굴 pair에서 한 방향으로 unknown 전체 구간을 검증하는 몸 경로**다. 현재의 “같은 이름의 양쪽 클립에서 각각 seed를 가져오기” 제약을 바꾸고, 얼굴·몸·원본 컷 검사는 유지한다. 아래 4개 구간, 총2.636167초의 신원 후보를 재현했다. 그중 ANT48초·75초는 원본 시퀀스에서도 선택 몸과 개인 메인이 명확하다. 나머지2개는 신원 근거와 메인 역할의 타당성을 구분해 검토해야 한다.

**이 최소 후보는 큰 품질 해결이 아니다.** 사용자 핵심 잔여 사례인 ANT4.57–6.14, ANT9.91–10.28, MMN38.20–39.34는 그대로 남는다. 이 후보를 적용한 작은 증분을 전체 목표 달성으로 보고하지 않는 것이 중요하다. 중기적으로는 ‘얼굴 증거 범위·몸 경로·메인 역할·공연 파트’를 분리하고, 불확실한 역할에 필요한 관측을 보강해야 한다.

## 1. 조사 범위와 재현성

- 정본: `/Users/jina/project/adlight/desktop/clipper_python`, HEAD `4b54bced17e13aadbeb97be75259b7f7213a9b24`의 **미커밋 현재 파일**. HEAD 버전만 읽지 않았다.
- 최신 실제 프로젝트: MMN `1793610108675`, ANT `1793610363935`, NEON `1793610789306`. 앱의 `dance_meta.json`, `face_evidence.json`, 원본 MP4, 실제 reference 이미지, 저장된 ROI/fullframe 얼굴 정렬 비교를 확인했다.
- 원본 영상 SHA256을 직접 계산하여 각 진단의 `runtime.video_sha256`과 세 영상 모두 일치함을 확인했다.
- 원본에서 직접 추출한 연속 프레임과 시간별 시퀀스를 시각 검토했다. 전체 영상 재생을 통한 모든 클립 정답 판정은 하지 않았다. 사용자의 기존 판정과 이번 분석자의 시각 판정을 구분한다.
- 조사 시작/마지막에 services의50개 파일 SHA256이 동일했다. 재현용 패키지 스냅샷을 scratch의 `source-snapshot/dance_highlight`에 보존했다. 본 세션은 제품 파일을 쓰지 않았다. SAM 두 호출은 계속 주석이며 인물/shared 소스는 건드리지 않았다.
- scratch: [독립 진단 폴더](/private/tmp/dance-astra-review-20261102). 모델 신규 설치·다운로드·앱 재실행은 없었다. 원본 디코딩·OpenCV 구조 검사와 저장된 벡터 계산만 수행했다.

핵심 산출물:

|파일|내용|
|---|---|
|[manifest.json](/private/tmp/dance-astra-review-20261102/manifest.json)|실제 앱 JSON·원본 경로, FPS, saved config|
|[input-hashes.json](/private/tmp/dance-astra-review-20261102/input-hashes.json)|입력 JSON 해시, 저장된/실측 영상 해시|
|[case-outputs.json](/private/tmp/dance-astra-review-20261102/case-outputs.json)|사용자 확인 구간의 현재 실제 출력|
|[output-metrics.json](/private/tmp/dance-astra-review-20261102/output-metrics.json)|최신 구간 수·길이·중첩 직접 재계산|
|[one_sided_replay.py](/private/tmp/dance-astra-review-20261102/one_sided_replay.py)|최소 후보의 읽기 전용 재현 코드|
|[one-sided-attempts.json](/private/tmp/dance-astra-review-20261102/one-sided-attempts.json)|양쪽 후보 경로와 거절 이유|
|[shadow-joins.json](/private/tmp/dance-astra-review-20261102/shadow-joins.json)|검증된 방향의 인접 구간과 실제로 연결한 shadow 범위|
|[regression-fixtures.json](/private/tmp/dance-astra-review-20261102/regression-fixtures.json)|양성·음성 사례의 원본 포즈/얼굴/joint/출력/컷/교대 스냅샷|
|[source-boundary-peaks.json](/private/tmp/dance-astra-review-20261102/source-boundary-peaks.json)|연속 원본 프레임의 차이와 SIFT 검사값|

## 2. 현재 결과: 무엇이 고쳐졌고 무엇이 남았는가

세 최신 JSON을 직접 재계산한 결과다. subsecond 개수는 오류 개수가 아니다.

|영상|개인/단체 클립|1초 미만 개인/단체|미확인 개인 수/합산 초|개인 길이 중앙값|개인 길이 최솟값/최댓값|
|---|---:|---:|---:|---:|---:|
|MMN|57 /32|21 /21|16 /6.807200|1.801800|0.033367 /10.660650|
|ANT|102 /32|54 /25|33 /16.017800|0.884167|0.066733 /8.842167|
|NEON|150 /56|90 /34|51 /16.751667|0.734167|0.033267 /8.274933|

개인 합산/union 초는 MMN135.001533/133.900433, ANT191.891700/191.457933, NEON177.243733/177.243733이다. MMN1.101100초, ANT0.433767초의 개인 간 중첩이 있다. 개인-단체 중첩은 각각15.598917/12.212200/4.270933초다. 준비 맥락과 허용되는 개인/단체 공존이 있으므로 중첩을 모두 오류로 세면 안 된다.

기존14개 사용자 사례에 대한 현재 상태:

|사용자 기준|현재 확인|
|---|---|
|MMN1.9–약2.3 타이틀 intro|개인 없음. 그러나 `0–4.371033` 단체 클립에 포함된다. 타이틀 중심 구간의 출력 제외 문제는 남음.|
|MMN2.3–4.37 단체|단체, 개인 없음. 일치.|
|MMN10.91–11.31 카즈하 또는 단체|단체. 허용 범위 내.|
|MMN34.73–35.44 사쿠라 또는 단체|34.73–34.8348의 약0.1048초는 미확인 개인. 이후 대부분 단체이고35.4354부터 사쿠라. 부분적으로 남음.|
|MMN37.738–39.339 사쿠라|38.204733까지 사쿠라, 이후39.339300까지 미확인. 남음.|
|MMN45–약48 사쿠라 준비·마무리|사쿠라45.361983–47.981267. 준비1.1011초를 이미 추가했다. ‘전부 누락’은 아님. 정확한 시작은 사용자의 근사 경계와 재대조 필요.|
|MMN89–93 카즈하 연속|88.855433–96.346250 한 구간. 과거 분할 문제는 현재 해결.|
|ANT4.571–6.139 홍은채|4.571233–6.139467 미확인. 남음.|
|ANT8.375–약9 홍은채|8.975633까지 홍은채. 약9초 교대와 부합.|
|ANT9.4–10.277 김채원|9.909800까지 김채원, 이후10.276933까지 미확인. 남음.|
|ANT32.633–33.433 전환은 양쪽 허용|32.665967에서 홍은채→김채원. 허용 범위 내.|
|NEON78.378–79.680 시리|77.377400–81.948533 시리 구간 안. 일치.|
|NEON150.617–152.619 단체|개인 없음, 단체. 일치.|
|NEON183.15–184.82 단체|개인 없음, 단체. 앞182.5초 원본·출력은 오아. 일치.|

추가 관찰: MMN79.8798에서 카즈하→김채원으로 넘어가지만 김채원 구간이88.254833까지 이어져81초대 원경에도 개인 출력이 남는다. NEON81.95–82.85에는 원경 단체 형상인데 일부 미확인 개인 출력이 남는다. 이는 분석자의 원본 관찰이며 새 사용자 정답으로 등록한 것은 아니다.

과거 ‘김채원30/42’ 등 번호는 옛 출력 기준이다. 이번 검토에서 그 번호를 최신 번호로 억지 대응하지 않았다. 그 모든 과거 오명을 현재 수정 완료/잔존이라고 선언할 근거는 부족하다.

## 3. 확인한 원인과 가설의 구분

### 3.1 얼굴의 불확실성과 파트 종료가 결합돼 있다 — 코드와 출력으로 확인

[member_timeline._identity_boundaries](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/member_timeline.py:134)는 얼굴 공백>.6초, 앞뒤 coverage 부족, 반복 embedding 변화 등을 경계로 만든다. `face_coverage_gap`의 strength는3으로 반복 reference 변경의2보다 높다. `_select_boundaries`는 .15초 간격만 요구한다. 이 경계들이 이후 출력에 투영되므로 1초 미만 구간은 의도적인 최대 길이 설정 없이도 발생한다.

[refine_unresolved_with_names](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/member_timeline.py:267)는 확정 구간을 고정하고 미확인만 재검토한다. 이어 body→scene→focal→projection→face edge→coalesce→preparation이 서로 다른 근거로 복원한다. 현재 카메라 episode가 MMN5개, ANT/NEON0개라는 점도 확인했다. 좁은 push-in/foreground crossing 증명만으로 일반적인 역할 유지까지 다룰 수는 없다.

**가설:** 구간을 증거 조각과 공연 파트로 분리하면 많은 불필요한 경계를 줄일 수 있다. 이번 단순 tracklet 실험은 그 가능성과 위험을 둘 다 보였으며, 전체 정확도 개선을 입증한 것은 아니다.

### 3.2 ‘단체 입증 실패’가 ‘메인 입증’처럼 취급된다 — 코드로 확인, 원경 반례 관찰

[segment.classify_main_scenes](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/segment.py:318)는 sustained/distributed group 조건이 실패하고 선택 몸이 있으면 `main_eligible_composition`을 남긴다. 이 문자열은 적극적인 카메라 초점·솔로 동작 증명과 같지 않다. 포즈의 head/torso/ankle 누락, LED 오검출이 group의 엄격한 증명을 깨면 메인이 남을 수 있다.

메인 선택은 얼굴 크기·중앙성·foreground와 제한적인 camera episode를 이용한다. 무대에서 같은 동작을 하는 여러 사람 중 중앙이라는 이유만으로 개인 파트를 결정할 수 없다는 사용자 기준과 간극이 있다. 단체 판정에 필요한 관절 하나를 완화하는 정도로 이 구조가 해결되지는 않는다.

### 3.3 같은 이름의 양쪽 클립을 요구하는 bridge는 올바른 seed를 못 쓰기도 한다 — 재현

[bridge_main_face_gaps](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/body_continuity.py:145)는 unknown 양쪽에 같은 확정 이름이 있고 각각 가까운 얼굴이 있어야 후보를 만든다. 그 사이 원본 경로를 검사한다. 다음 파트로 교대하는 unknown prefix, 한쪽 얼굴만 충분한 tail, unknown 밖의 컷을 건너야 하는 seed는 구조적으로 불리하다.

ANT48.081367–48.415033은 기존 양방향 bracket에서 `unconfirmed_body_continuity`로 실패하지만, **오른쪽 원본 dual pair2908/2920에서 frame2880까지의 경로**는 기존 source 검사를 그대로 통과한다. ANT75는 이전 파트가 허윤진이어서 같은 이름 양쪽 조건을 충족하지 못하지만, 새 카즈하의 원본 경로가 unknown prefix를 포함한다. 이것이 최소 후보의 직접 근거다.

### 3.4 카메라 거절 이유는 실제 편집 컷 정답이 아니다 — 원본 연속 프레임으로 확인

[_check_source_chain](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/body_continuity.py:99)의 마지막 검사는 `max(diff)>max(6,3*median(diff))`다. 이름은 `isolated_visual_change`지만 높은 차이가 정말 한 프레임에 고립됐는지 검사하지 않는다. 여러 프레임의 빠른 줌도 이 조건에 걸릴 수 있다.

[structural_continuity](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/camera_transitions.py:12)는 affine을 추정한 다음 변환 잔차가 아니라 **원래 대응점의 이동량 p90**을 `.02*min(H,W)`와 비교한다. 따라서 잘 맞는 카메라 이동도 실패할 수 있다. 그러나 이 한 줄을 residual 기준으로 바꾸는 것만으로 주요 실패가 풀리지는 않는다.

|원본 pair|기존 구조 검사 결과|의미|
|---|---|---|
|MMN2297→2298,38.338300초|inlier17/58=.293, p90 이동48.06px|inlier수30 및 ratio.6도 실패. 이동량 조건만 바꿔도 실패.|
|ANT615→616,10.276933초|inlier148/331=.447, p90 이동5.55px|이동량은 이미 작다. ratio 조건 실패.|
|ANT578→579,9.659650초|inlier402/538=.747, p90 이동32.74px|큰 카메라 이동량 조건이 실제로 추가 거절을 만드는 사례.|

[MMN 연속 프레임](/private/tmp/dance-astra-review-20261102/MMN-consecutive-details.jpg), [ANT 연속 프레임](/private/tmp/dance-astra-review-20261102/ANT-consecutive-details.jpg)을 직접 봤다. MMN2296–2302와2357–2359는 여러 프레임에 걸친 줌 변화가 보인다. ANT615→616에는 연속된 몸·구도에서 조명·연무 변화가 보인다. MMN2406→2407의 분명한 다른 뷰도 음성 비교로 남겼다.

인계에서 MMN2298을 ‘실제 물리적 edit 확정’으로 취급한 설명은 저빈도 contact와 scalar 차이만으로는 유지하기 어렵다. 그렇다고 모든 물리적 촬영/편집 전환이 없다고 확정한 것도 아니다. **큰 차이/구조검사 실패를 cut 정답으로, cut=False를 몸 연속성 증명으로 사용하는 양쪽 오류를 피해야 한다.**

### 3.5 SAM 비활성화는 이름 재검증도 함께 껐다 — 확인, 현재 대량 오명은 입증하지 못함

[pipeline.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py:1011)의 `recover_mask_names`와1030행의 `revalidate_named_segments`가 모두 주석이다. 이후 frozen joint 후보표가 존재해도 일반적인 확정 이름 재검증은 실행되지 않는다.

최신 출력에서 “다른 이름의 반복 accepted joint 얼굴”을 독립 조사한 결과, MMN45.36–46.46의 사쿠라 준비 중첩만 발견됐다. 이 시기 selected-main 얼굴은 허윤진이고 준비 대상은 사쿠라이므로 이것을 오명으로 수정하면 오히려 준비 기능을 손상시킨다. 이번 검사만으로 현재 잘못된 확정 이름이 대량 존재한다고 말할 수는 없다. 기존 확정 이름을 정답이라고 가정할 수도 없다. 역할별 얼굴 소유를 갖춘 재검증이 필요하다.

### 3.6 얼굴 관측과 임계값 — 한 가지 수치 완화는 근거 없음

saved config의 analyze_skip4와59.94fps는 약15Hz 포즈 관측이다. 등록 경로는 얼굴5프레임 제한이 아니라 모든 main 관측을 보존한다. group 최소.15/merge_gap0도 확인했다. config의1.2초 최소 길이가 등록 경로 전체에 적용된다고 해석하면 안 된다.

기존8시점 ROI/fullframe의 원본·정렬 이미지를 직접 확인했다. ANT 얼굴은 작은 픽셀/연무·조명·움직임, MMN은 옆얼굴과 강한 분홍빛·정렬 변화가 보인다. 기존 계산의 fullframe 신규 채택0/8을 새로 추론 실행한 것은 아니지만, 저장된 후보표와 이미지가 그 결론에 부합한다. 다만8시점으로 전체 얼굴 모델의 한계를 확정할 수는 없다.

ANT의 거절된 top1이 김채원인 사례가 있는데 사용자 정답은 홍은채다. distance ceiling을 느슨하게 해 top1을 채우는 것은 위험하다. detector>=.8/.9는 얼굴 검출 품질 조건이지 신원 정답 확률이 아니다. 현재 thresholds에 대한 held-out calibration 자료는 찾지 못했다. 모델/갤러리를 바꿀 때는 source frame·shot 단위 holdout에서 오명과 거절을 함께 측정해야 한다.

## 4. 1순위 최소 구현안: 동결 얼굴에서 검증한 한 방향 몸 경로

### 함수와 적용 지점

`body_continuity.py`에 아래의 후보 생성/검증 함수와 적용 함수를 둔다. 새 후처리 규칙을 계속 더하기보다 기존 bridge의 seed 선택 단위를 clip-label bracket에서 **원본 얼굴 pair와 검증 경로**로 옮기는 첫 단계다.

```
propose_face_seeded_paths(
    output, frame_records, original_face_rows, frozen_joint_matches,
    matcher, group_intervals, eligible_main, handoffs, video_path, fps
) -> proposals, audit

apply_proven_paths(output, proposals) -> output, provenance
```

`pipeline.py`에서 최종 projection/edge/coalesce 다음, `_include_incoming_preparation` 이전에 호출한다. 이 위치에서 output은 실제 eligible 개인 범위이고 준비 중첩은 아직 추가되지 않았다. 원본 face rows는 `all_face_results`가 해제되기 전에 고정해 사용한다. 최종 role은 `recs`, 얼굴 소유는 원본 body geometry와 대조한다. group_intervals는 그 시점의 실제 group_segs를 전달한다.

### 입력·판정 계약

1. 기존 eligible 개인의 **unknown 전체 구간 U**만 대상. 일부 sample만 채워 새 자투리를 만들지 않는다. 새 시간, 새 main eligibility, 단체/intro 전환을 만들지 않는다.
2. U에 바로 맞닿은 named scope는 검색 범위일 뿐 신원 근거가 아니다. 그 안의 original owned face에서 frozen joint `accepted` 이름이 scope 이름과 일치하는 pair를 선택한다. `_valid`, detector>=.9, 시간차.15–.6초와 기존 joint 거리·margin을 유지한다.
3. source frame이 같은 모델/정렬 두 대안은 독립 pair가 아니다. original frame index로 deduplicate한다.
4. 좌우 각각 가장 가까운 독립 pair 하나, 최대2경로를 검사한다. **양쪽 모두 평가한 뒤** 성공 이름이 다르면 U는 미확인 유지. 최초 성공에서 중단하지 않는다. nearest pair 실패 후 먼 pair를 계속 탐색해 우연히 통과시키지 않는다.
5. proof 범위는 U 시작 이전/같은 sampled row와 U 끝 이후/같은 sampled row까지 bracket하고 pair까지 포함한다. 모든 sampled row가 존재해야 하며 각 얼굴 row의 body_bbox가 그 프레임 selected-main과 일치해야 한다.
6. **U뿐 아니라 seed~target 전체 proof 범위**에서 `scene_kind=main`, no_person 없음, 실제 단체 구간과 비중첩, handoff 없음, 누락 관측 없음이어야 한다. 준비 인물/숨겨진 역할 프레임은 이 버전에서 다루지 않는다.
7. 전체 범위의 다른 accepted joint 이름, 다른 direct primary 이름, 기존 `.65` alien-vector 독립 pair를 veto로 유지한다. 실패 얼굴의 top1만 보고 반대 이름을 확정하지도 않는다.
8. 기존 `_check_source_chain`을 그대로 호출한다. 정확한 seek/FPS, 모든 원본 프레임, 색상 cut, 큰 시각 변화, 유일한 몸 대응 검사를 유지한다. SAM이나 mask proof를 호출하지 않는다.
9. `proposals`에는 원본 pair, 실제 source frame 범위, side, 소유/role/cut/handoff/face 검사와 거절 이유를 저장한다. recovered label/embedding은 anchors, gallery, fallback_names에 추가하지 않는다. 후속 후보는 항상 원본 frozen 입력에서 만든다.
10. 이 첫 단계가 기존 확정 이름을 바꾸지 않는 이유는 변경 효과를 분리하기 위해서다. 기존 이름을 정답으로 선언하는 정책은 아니다. 확정 이름 수정은 역할별 원본 얼굴·몸 증명을 갖춘 별도 평가에서 허용해야 한다.

### 연결 규칙: 이름만 채워 같은 이름 조각을 더 만들지 않는다

채택된 U는 **검증한 seed 방향의 인접 named 구간과 경계 하나를 제거**한다. 기존 named 부분의 끝과 내부 근거는 유지하고, U의 body-path provenance를 추가한다. 새로운 얼굴 관측을 발명하지 않는다. 얼굴이 없는 U를 기존 `_assign_piece`로 다시 판정해 원래 미확인으로 되돌리는 순환을 만들지 않는다.

반대편 named 구간까지 자동으로 합치지 않는다. 별도의 원본 face pair·role/handoff/연속성 근거가 있어야 한다. 그 경계가 남으면 동일인 과분할을 완전히 해결한 것은 아니다. 이후 일반 coalescer를 실행할 때는 body proof가 있는 join과 얼굴 근거만의 join을 구분해야 한다.

shadow 적용은 이미 수행했다. 전체 출력 시간 합, 기존 named 시간의 이름·커버리지를 보존한다는 assertion을 통과했다. 새 출력 시간을 만들거나 unknown을 삭제한 것이 아니다.

|영상|U와 이름|pair / 전체 proof frame|검증한 방향으로 연결한 shadow 결과|
|---|---|---|---|
|ANT|48.081367–48.415033 김채원|2908,2920 /2880–2920|48.081367–53.720333 김채원|
|ANT|75.141733–75.375300 카즈하|4552,4564 /4504–4564|75.141733–82.182000 카즈하|
|ANT|180.880600–182.682600 사쿠라|10956,10968 /10840–10968|180.880600–189.255733 사쿠라|
|NEON|38.204833–38.471767 아이찡|2308,2324 /2288–2324|38.204833–40.907533 아이찡|

MMN 변화0. shadow 개인 클립 수는 ANT102→99, NEON150→149다. 미확인 초는 ANT16.017800→13.648567, NEON16.751667→16.484733이다. **이 값은 신원 후보와 연결의 기계적 재현량이며 정답률이 아니다.**

[ANT 후보 원본](/private/tmp/dance-astra-review-20261102/ant-proposed-paths.jpg): ANT48은 측면에서 정면으로 돌아오는 같은 김채원 몸, ANT75는 카즈하의 새 클로즈업과 같은 몸이다. ANT180은 동일 중심 몸은 이어지지만 원경 전체 안무에서 개인 메인 역할이 계속 타당한지는 별도 판정이 필요하다.

[NEON 후보 원본](/private/tmp/dance-astra-review-20261102/neon-proposed-paths.jpg): NEON38은 앞쪽 두 인물이 함께 춤추므로 선택된 몸의 아이찡 신원 확인과 단일 메인 역할의 정답을 구분해야 한다. NEON194는 초기 제안에서 제외했다. 전체 proof 범위 뒤쪽에 group이 있어 대상 U만 검사하면 잘못 통과한다.

### 계산 비용과 플랫폼

최종 양방향 replay의 후보 계산+원본 검사 시간은 MMN0.676초, ANT1.587초, NEON1.862초, 합4.125초였다. JSON 로드·matcher 구성은 타이머 밖이며 저장된 벡터를 사용했다. 반복 실행으로 디코드 캐시가 따뜻한 로컬 측정이다. 앱 실행 시간이나 Windows 성능 측정이 아니다.

재현 스크립트는 pair 열거가 O(n²)인 연구 코드다. 제품은 정렬된 시간에 two-pointer를 사용하여 방향별 최근접 독립 pair 하나를 선형으로 찾는다. matcher 결과와 원본 source-pair/pose 대응은 한 작업 내 캐시를 재사용한다. source 증거의 캐시 키에는 video hash, frame 범위, evidence/policy 버전이 필요하다. 판정 provenance에는 실제 모델·config 해시를 보존한다.

NumPy/OpenCV와 기존 decoder만 필요하므로 추가 GPU/추론 모델 의존성은 없다. Mac/Windows에서 같은 source frames/FPS·codec seek·실수 경계를 검증해야 한다. Windows 실기 측정은 수행하지 않았다.

### 회귀 fixture와 부모의 확인 순서

`regression-fixtures.json`은 실제 입력에서 잘라낸 스냅샷이며 원본 MP4의 frame 범위·hash를 갖는다. 다음을 제품 테스트로 옮긴다.

|종류|fixture/기대|
|---|---|
|우선 양성|ANT48.081367–48.415033: right pair2908/2920에서 검증, right join 하나, 실제 source 범위 보존|
|실제 교대 직후 prefix|ANT75.141733–75.375300: 카즈하 prefix 회복, 이전 허윤진과 합치지 않음|
|역할 추가 검토|ANT180.8806–182.6826, NEON38.204833–38.471767: 신원 proposal과 role verdict를 별도 저장|
|원경 전파 음성|NEON81.95–82.85: 단순 pose+joint는 시리 후보를 만들지만 group 경로 gate로 거절|
|전체 경로 gate 음성|NEON194.0938–194.260733: 대상 안의 검사만으로 통과시키지 않음|
|사용자 실제 교대|ANT8.975633 홍은채→김채원 유지;32.633–33.433의 허용 전환 존중|
|실제 연속 파트|MMN89–93 카즈하 한 구간 보존, 최대3초 제한 금지|
|준비 소유 구분|MMN45.361983–46.463083: selected-main 허윤진 얼굴로 준비 사쿠라를 오명 처리하지 않음|
|보수적 잔여|MMN38.20/ANT4.57/ANT9.91을 이름 추측으로 채우지 않음|
|합성 음성 보강|타인 accepted pair, 반복 alien 얼굴, overlapping body, missing pose/source, 부정확한 seek, 양쪽 다른 이름, 같은 프레임 두 대안|
|비간섭|SAM 호출 시 테스트 실패, Person/shared 경로 호출 없음, gallery/anchors/원본 observation 불변|

현재 `tests/test_dance_body_continuity.py`의6초 파트, 양방향 유일성, 부분 관측 경쟁 몸, 정확한 seek, 반복 타인 얼굴 테스트를 유지한다. one-sided를 허용하면 기존 unbounded-gap 거절 테스트를 무조건 지우지 말고 **원본 pair와 완전한 경로가 없는 unbounded gap**은 계속 거절하도록 조건을 분리한다.

제품 구현 후 body/output/member_timeline/camera/scene/incoming/pipeline 관련 pytest를 먼저 실행한다. 다음 앱 세 영상 재실행에서 원본 해시·입력/모델/config를 맞추고,4개 제안과 음성 사례의 before/after 범위·이름·썸네일을 비교한다. 본 검토는 제품을 바꾸지 않았으므로 전체 pytest와 빌드를 다시 실행하지 않았다. 인계의2548passed 등 수치는 이번 검토에서 새로 확인한 결과가 아니다.

## 5. 이후 구조적 개선안 두 가지

### 2순위: 얼굴 증거와 메인 파트를 분리한 타임라인

최소 후보가 반복될수록 최종 단계에 예외가 늘어난다. 중기 변경은 `member_timeline`이 만드는 face evidence scopes를 유지하되 그것을 곧바로 출력 segment로 삼지 않는 것이다.

- 몸 경로는 한 샷 내 소유·연속성, 신원은 frozen face 근거, 역할은 main/group/both/unresolved/intro, 파트는 출력 단위로 분리한다. preparation은 별도의 context 범위와 대상 몸 소유를 갖는다.
- face coverage gap은 ‘관측 없음’이지 새로운 인물·새 파트의 양성 증거가 아니다. 반복되는 다른 멤버 얼굴, 확인된 몸 교대, 역할 변화는 경계 증거다.
- 물리적 컷은 몸 tracking edge를 끊되 공연 part를 무조건 끊지 않는다. 양쪽 샷이 독립적으로 같은 멤버와 역할을 지지하면 part edge를 만들 수 있다. 양쪽의 같은 출력 이름만으로는 부족하다.
- `observed_main`에서 단일 body를 일찍 버리지 말고 경쟁 후보와 camera/foreground/동작 근거를 남긴다. 단체 조건 실패를 적극적인 개인 메인 확률로 바꾸지 않는다. 역할을 알 수 없으면 unresolved를 유지한다.
- 부분적으로 관측이 없는 구간, 잠깐 넓어진 구간은 검증된 part context 안에서 유지할 수 있지만 실제 단체/intro를 삭제하거나 임의 이름으로 채우면 안 된다.
- 최종 emitter 한 곳에서 part와 허용 가능한 준비/group context를 출력한다. 원본 face rows와 body-only 범위는 provenance로 구분한다.

처음부터 가중치 많은 전체 Viterbi/새 학습 모델을 제품에 넣는 것은 권하지 않는다. 먼저 최소 후보의 `body_path` 및 `same_identity_across_shots` 같은 **검증 가능한 edge**를 명시하고 현재 출력을 shadow 재구성한다. 역할 점수나 duration prior를 학습하려면 별도 정답이 필요하다. 임의 길이 벌점으로 clip 수를 줄이는 것은 사용자의 목표와 다르다.

**SAM 없이 확정 이름을 재검증하는 구체 경로도 이 단계에 포함한다.** 기존 `revalidate_named_segments` 전체를 다시 켜거나 `verify_track`를 항상 True로 대체하지 않는다. 새 `plan_identity_corrections(output, owned_face_runs, frozen_joint, proven_body_paths, role_scopes)`가 먼저 correction proposal만 만든다.

- 이미 계산된 joint 결과를 시간순으로 순회하여 현재 이름과 다른 accepted 이름의 독립 pair를 찾는다. raw nearest/top1·동일 프레임 대안·출력 이름은 증거가 아니다.
- 얼굴 소유가 검토 대상 역할의 몸과 일치해야 한다. selected-main과 incoming preparation은 다른 `subject_ref`다. MMN45.36–46.46의 허윤진 main 얼굴은 사쿠라 preparation을 반박하지 않는다. preparation은 그 단계에서 얻은 별도 incoming query/proof를 참조한다.
- 후보 pair와 수정할 원래 구간의 source path를 최소안의 정확한 원본·경쟁 몸·role/handoff 검사로 검증한다. 원래 clip 전체를 새 이름으로 덮지 않고, 직접 얼굴 근거와 검증된 경로가 지지하는 시간만 수정한다. 나머지는 기존 결정 또는 명시적 conflict로 남긴다.
- 서로 다른 accepted 얼굴 run을 하나로 평균하지 않는다. 확인된 A→B 전환은 경계로 남기고 A→B→A는 B를 건너 A끼리 합치지 않는다. 새 correction은 다음 correction의 seed가 되지 않는다.
- 구현은 `joint_identity.py`의 frozen match 계산 및 범위 적용 구조를 재사용할 수 있지만 SAM verifier와 분리한다. 최초 테스트는 잘못된 named A 안의 실제 B pair, 원경 group, competing body, prep/main 중첩, 진짜 교대, 단일 noisy face를 포함한다.
- 이미 저장된 joint 표를 순회하는 계산은 작다. 추가 source 검사는 correction 후보에만 수행하고 기존 캐시를 쓴다. **현재 세 영상에서 prep를 제외한 다른 이름의 반복 joint conflict는 발견하지 못했으므로, 이 단계가 현재 오명을 얼마나 고칠지는 아직 입증되지 않았다.**

기대 효과는 동일 멤버 과분할·진짜 교대 혼합·준비 경계의 일관된 처리다. 위험은 긴 오명 전파, group 흡수, 같은 복장의 몸 교차다. 새 track ID는 이름 근거로 쓰지 않고 모든 propagation은 frozen seed와 competing-body 증거로 제한한다. 신규 모델 없이 graph 계산 자체는 작지만 몸 대응/역할 관측 비용과 오류가 실제 병목이다.

### 3순위: 불확실성 원인별 추가 관측과 모델 비교

ANT4.57의 작은 흐린 얼굴, MMN38의 급격한 뷰/정렬 변화, NEON 원경의 장식물·부분 관절은 같은 검사를 반복해서 해결될 유형이 아니다.

- 얼굴 부족: 같은 몸 경로에서 품질이 높은 새 시점·새 시야를 선택해 기존 두 모델로 먼저 비교한다. gallery는 동결하고 동일 frame 정렬 대안을 독립 투표로 세지 않는다. 전역 fullframe 교체나 threshold 인하를 기본으로 삼지 않는다.
- 몸 대응 부족: 필요한 경계 인근에만 해상도를 높인 pose/appearance 관측을 추가하고, 전체 인물을 경쟁 후보로 유지한다. 카메라 이동 보상과 appearance를 결합하는 접근은 [BoT-SORT 원 논문](https://arxiv.org/abs/2206.14651)이 참고가 되지만, 보행자 MOT 성능이 방송 안무의 신원·메인 정답률을 보장하지 않는다. tracker ID를 멤버 이름으로 승격하지 않는다.
- 카메라 사건 부족: [TransNet V2 공식 저장소](https://github.com/soCzech/TransNetV2/)의 shot detector를 현재 color/structure 검사와 **후보 생성 수준에서** 비교할 수 있다. 컷 detector가 같은 멤버의 파트 연속성이나 foreground 소유를 결정하는 것은 아니다. 새 의존성·실기 비용 검증이 필요하므로1순위는 아니다.
- 역할 부족: 작은 시간창의 원본 영상에서 focus/solo/ensemble/intro를 판정하는 별도 관측이 필요하다. pose geometry만으로 중앙 솔로와 전체 군무를 항상 구별할 수 있다고 가정하지 않는다. 저빈도 video model/VLM은 우선 offline 보조 판정으로 비교하고, clip 전체를 이름짓는 최종 권한을 주지 않는다. 품질·비용은 아직 측정하지 않았다.

[ActionFormer 논문](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136640485.pdf)은 순간별 분류와 시간 경계를 함께 추정하는 구조의 참고다. 사전학습된 일반 action class가 이 제품의 ‘무대 메인 역할’을 바로 풀어준다는 근거는 없으므로 즉시 교체 모델로 추천하지 않는다.

## 6. 품질·속도 비교의 합격 기준

전체 정확도 숫자는 현재 낼 수 없다. 기존14사례는 개발 중 반복 사용됐고 모호함도 허용한다. 각 구간에 **허용 이름 집합·허용 역할 집합·경계 허용 범위·연속 파트 ID**를 따로 저장해 평가한다.

다음을 각각 before/after로 보고한다.

1. 잘못된 확정 이름의 시간/사례, 원경의 잘못된 개인 메인 시간.
2. 실제 교대가 섞인 클립 수와 교대 경계 오차.
3. 동일한 정답 part ID에 생긴 불필요한 출력 경계 수.
4. 준비·마무리의 누락 시간, 실제 유효 파트의 미출력 시간.
5. unknown 시간·구간 길이 분포·main/group/context 중첩. 앞4개를 대신하는 지표로 쓰지 않는다.
6. 총 실행시간, stage별 시간, 추가 decode frame/pose/face 호출 수, peak 메모리. Mac과 Windows를 분리한다.

첫 적용의 필수 조건은 사용자 확인 사례에서 새 오명·새 원경 개인·새 교대 혼합·유효 시간 손실이 없고, 실제 양성 후보가 의도한 한 경계와 함께 개선되는 것이다. 새로운 source observations를 얻지 않은 경우 unknown 감소는 성능 개선의 단독 근거가 아니다.

추가 사람 판정은 범위를 좁힌다. ANT47.9–48.8,75.0–76.2,180.7–183.2와 NEON38.0–38.8,81.8–83.4,194.0–194.4, MMN79.7–82.2를 우선 대상으로 삼는다. 특히 ANT180/NEON38의 role, NEON82의 원경 처리, MMN81의 개인 유지 여부가 현재 제안의 채택을 크게 바꾼다. 후보 이름을 먼저 보여주지 않는 원본 판정과 before/after 비교를 분리하면 확인 편향을 줄일 수 있다.

재현 명령(제품 파일 쓰기 없음):

```sh
cd /Users/jina/project/adlight/desktop/clipper_python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/dance-astra-review-20261102/source-snapshot .venv/bin/python /private/tmp/dance-astra-review-20261102/one_sided_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/dance_highlight .venv/bin/python /private/tmp/dance-astra-review-20261102/package_evidence.py
```

## 7. 이번 검토가 확정하지 않은 것

- 전체 영상의 정답률, 기존 확정 이름 전체의 정확성, 옛 clip30/42 등의 최신 대응.
- 4개 신원 후보 모두의 개인 메인 역할 정답과 실제 앱의 최종 카드/썸네일 결과.
- source 구조 실패가 물리적 컷이라는 주장 또는 모든 급격한 줌이 연속 촬영이라는 주장.
- 새 tracker/shot/video/face 모델의 이 데이터셋에서의 향상과 Windows 실기 속도.

확정한 것은 현재 잔여 오류의 구체 위치, seed 선택의 구조적 제약, 단순 pose 전파의 원경 반례, raw-flow 완화만으로 해결되지 않는 이유, 그리고 기존 검사를 유지한 최소 후보의 재현과 한계다. 부모 세션은 ANT48/75부터 한 가지씩 구현·회귀·실제 앱 비교를 진행할 수 있다.


## 8. 추가 검토 — SAM의 증분 가치, 짧은 실행 예산, 역할 조건

2026-11-02 추가 요청에 따른 별도 검토다. 제품 코드는 수정하지 않았다. SAM 추론도 새로 실행하지 않았다. [기존 비용 보고서](/Users/jina/project/adlight/.codex/features/dance-highlight/records/2026/11/02-mask-cost-reduction-results.md), 최적화 앱의 원본 `face_evidence.json` 세 개, 실행별 비교 JSON, 현재 보존된 SAM 구현을 읽고 시도 단위로 다시 집계했다. 세 원본 영상 해시는 이번 검토의 최신 프로젝트와 일치한다. 아래 비용은 과거의 같은 Mac 실행값이며, 새 부분 실행·cold start·Windows 성능 예측값이 아니다.

**권고: SAM 기본 OFF를 유지한다. 기존 전체 호출에 시간 조건만 붙여 재활성화하지 않는다.** SAM은 사용자 확인 공백을 실제로 복원했으므로 무가치하지 않지만, 그 효과가 SAM만 가능한 효과라는 증명은 없다. 우선 기존 얼굴·몸 관측으로 가능한 복원을 분리하고, 남은 어려운 사례에만 독립 작업자의 짧은 검증을 연구한다. 또한 역할이 애매한 두 one-sided 후보는 `main_eligible_composition`을 유지한다는 이유로 자동 채택하지 않는다.

### 8.1. 실제 비용과 복원 효과

| 영상 | SAM 복원 stage | 전체 시도 / 통과 | 통과 시도 시간 합 | 실패 시도 시간 합 | 해당 stage가 실제 main에 더한 이름 시간 |
|---|---:|---:|---:|---:|---:|
| MMN | 77.968초 | 40 / 8 | 37.363초 | 40.174초 | 2.386초 |
| ANT | 234.226초 | 86 / 15 | 82.251초 | 151.517초 | 7.842초 |
| NEON | 1163.121초 | 146 / 22 | 111.714초 | 1050.835초 | 4.738초 |

시도 수에는 즉시 얼굴 충돌로 탈락해 별도 시간값이 없는 시도도 포함했다. 시도 시간은 한 후보의 partial retry 등을 포함하므로 mask 한 번의 순수 추론 시간이 아니다. stage 시간에서 시도 시간 합을 뺀 값은 각각 0.430/0.459/0.572초지만 이를 cold 모델 초기화 시간으로 해석하면 안 된다. lazy tracker 생성은 시도 타이머 밖이고 다른 공통 비용도 섞여 있다.

`mask_continuity.recovered_seconds` 원값은 3.387/9.244/8.643초다. main projection 전의 회복량이므로 위 표의 main 증분이나 품질 개선으로 대신 쓰면 부풀려진다. 최종 ON/OFF 비교의 named→unknown 차이는 MMN 2.453, ANT 7.842, NEON 4.738초이며, MMN은 후속 연결 때문에 stage 증분과 약 0.067초 다르다. ANT에는 별도 `joint_identity` 단계의 홍은채→사쿠라 0.3003초 교정도 있었다. 이 단계 시간은 MMN 0.007, ANT 2.095, NEON 0.693초였다.

SAM 설정은 이미 **SAM2.1 tiny, 입력 512, CPU**였다. 앱의 얼굴 GPU 개선과 SAM의 장치를 혼동하면 안 된다. 이미지 feature 캐시 512MiB, 완성 mask 캐시 128MiB, 역순 decode 블록 128MiB와 전체 원본 transition 재사용도 들어가 있다. mask 캐시 hit/miss는 0/50, 2/103, 2/171에 그쳤다. ‘tiny로 바꾸기’, ‘캐시 추가’, ‘실패 조기 종료’는 새 해결책이 아니다. predictor의 메모리·모델까지 포함한 실제 peak RSS는 이 수치만으로 알 수 없다.

NEON의 `context_face`와 `joint_context_face` 시도는 합계 **1014.037초**를 썼다. 그중 통과 시도는 각각 1개/3개다. `main_face`+`joint_face` 시도도 148.513초여서, context 경로를 통째로 빼는 것만으로 60초 이내가 되지는 않는다. 더구나 NEON34.334–35.135,157.958–158.558에는 context seed만 통과한 후보가 있으므로, 비용 절감을 위해 빼면 해당 복원을 포기하는 별도 정책이 된다. 모든 성공을 미리 안다는 비현실적 가정으로 실패를 제거해도 NEON 통과 시도 합만 111.714초다. 이 합은 중복 성공도 포함하며 최소 필요 계산량의 하한은 아니다.

### 8.2. 중요한 세 공백에서 SAM이 추가한 증거

| 현재 남은 공백 | 과거 통과한 SAM 경로 | 기록된 비용 | 해석 |
|---|---|---:|---|
| MMN38.204733–39.339300 사쿠라 | 오른쪽 frozen face 2364 → 2292, 19개 trace, 양방향 mask cycle | 3.596초 | 이 경로에는 camera link가 없다. 현재 간단한 픽셀 변화 veto를 넘어 몸 연속성을 검증한 사례다. 왼쪽 경로도 별도로 8.745초에 통과했다. |
| ANT4.571233–6.139467 홍은채 | 184 → 364, 50개 trace, 185/186 및289/290 경계 검증 | 19.105초 | 첫 경계는 exact face 검사가 약해 184/188의 sampled face 대응으로 재검증했고, 두 번째는 exact face 대응을 통과했다. 단순 mask만의 효과가 아니다. |
| ANT9.909800–10.276933 김채원 | 616 → 596, 7개 trace, 616/615 exact face 대응 | 2.324초 | 짧은 경계 검증의 실제 성공 사례다. source chain의 color-cut veto가 남긴 공백을 해결했다. |

이 세 공백의 이름 복원 합은 3.070초다. MMN 후보 전체 탐색은 경쟁 context 실패까지 합쳐 14.253초였다. 위의 빠른 성공 하나만 골라 전체 비용으로 제시하면 안 된다. 또한 값들은 기존 실행 순서와 warm cache 아래의 측정이므로, 새 worker에서 같은 경로를 실행하는 비용은 아직 모른다.

최신 출력에서 과거 ON/OFF의 named→unknown 차이 중 아직 unknown인 시간은 14.866초다. 이번 one-sided 후보 네 개와 이름까지 일치하며 겹치는 부분은 2.403초이고 ANT75의 0.234초는 과거 SAM 증분 밖이다. 그러나 네 후보 중 두 개는 역할이 미확정이므로 이 2.403초를 채택 가능한 정확도 개선으로 보고하지 않는다. 과거 SAM 출력 자체도 전체 정답 검수를 통과한 자료는 아니다.

### 8.3. 가장 싼 대체 관측과 부분 실행의 우선순위

1. **이미 있는 증거 재사용.** one-sided 몸 경로 및 원본 joint pair를 먼저 사용한다. 별도 모델·추론이 필요 없다. 복원된 이름을 seed로 재투입하지 않는다. 역할 검증은 별도 조건이다.
2. **named clip 경계 교정.** 다음 절의 ANT117 사례처럼, 출력 clip 경계에 잘린 동일 인물의 독립 pair를 찾는다. 출력 경계 바깥의 바로 인접한 원본 face run도 검색하되 다른 accepted 인물 run·handoff·group을 넘지 않는다. 새 특징 추출 없이 되는 교정을 먼저 분리한다.
3. **실패 경계의 실제 증거만 보충.** ANT616/615처럼 명확한 한 경계는 그 원본 두 프레임과 인접 pose 샘플의 face 소유·경쟁 얼굴·양방향 픽셀 대응을 검증하는 작은 단위가 우선 실험 대상이다. 현재 `CutFaceLink`/`SampledFaceLink`는 dual face 비교, 실제 head pixels, mask 소유 조건이 묶여 있다. mask 인자를 bbox로 채우거나 전부 True로 바꿔 같은 검증이라고 부르면 안 된다. 모든 경쟁 몸을 보존하는 독립적인 소유 증명을 만들고 비슷한 의상·교차·줌·조명 변화·실제 컷 반례로 재검증해야 한다. 부분 연산별 비용이 기록되지 않아 ‘face 부분만 실행하면 몇 초’라는 수치는 현재 낼 수 없다.
4. **정말 필요한 짧은 SAM 경로만 선택적 연구.** frozen face pair와 대상 몸이 이미 있고, 역할·경쟁 얼굴 조건은 통과했지만 body/transition 한 조건만 미확정인 후보를 대상으로 한다. 가장 가까운 원본 seed, 상한이 있는 경로·후보 수, 전체 양방향 검증을 고정한다. 긴 same-shot context 전체를 탐색하지 않는다. MMN의 19-sample 경로와 ANT의 7-sample 경계 경로는 연구 fixture가 되지만, 5초 같은 작은 총 예산에서도 둘이 항상 완료된다고 주장할 근거는 없다. ANT4.57의 과거 19.1초 경로는 작은 예산에서 그대로 완료될 것으로 기대할 수 없다.

image encoder만 돌리면 이미지를 위한 feature를 얻을 뿐, 멤버 신원·연속 몸 경로·메인 역할 증거는 아직 없다. mask decoder만 떼어내도 source-specific feature가 없으면 encoder 비용이 다시 필요하고, 시간 memory와 역방향 cycle을 생략하면 현재 합격 조건과 달라진다. 앞방향 몇 프레임만 끝났다고 이름을 채우는 부분 실행은 권하지 않는다. 메모리 캐시에 저장된 긴 경로의 prefix를 그대로 짧은 경로의 증거로 재사용하는 것도 현재 `SamMasks` 계약과 다르다. 경로 길이·순서·prompt를 포함한 완성 결과만 재사용하도록 구현되어 있다.

### 8.4. 총 wall-time 상한에 필요한 취소 구조

현재 `MaskTracker`에는 deadline/취소 토큰이 없다. `_cuts`, 원본 decode, 모델 초기화, predictor inference, 역방향 검증이 동기 호출이며 progress는 대략 8 trace마다 발생한다. 더구나 앱의 cancel flag는 progress 전달을 생략할 뿐 pipeline을 중단하지 않고, pipeline `_progress`는 callback 예외를 삼킨다. progress callback에 timeout 예외를 넣는 방법으로는 이 예산을 구현할 수 없다.

`Future.result(timeout=...)`는 기다리는 시간을 제한한다. 이미 실행 중인 작업을 `cancel()`로 종료하지 못한다. [Python 3.11 Future 문서](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel). `Popen.communicate(timeout=...)`도 timeout만으로 자식 프로세스를 죽이지 않는다. [subprocess 문서](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen.communicate).

권고 구조는 다음과 같다. 이는 설계 제안이며 구현·강제 종료 실험을 한 결과가 아니다.

- 부모가 선택적 단계 전체의 monotonic deadline을 소유한다. 후보 선정·IPC·import·모델 파일 확인/로딩·warmup·decode·두 방향 추론·결과 수신·종료 확인을 같은 예산으로 집계한다. `recover_mask_names`와 `joint_identity`에 각각 별도 예산을 주어 총량을 배로 만들지 않는다. 예산 0/OFF에서는 worker와 모델을 생성하지 않는다.
- SAM 전용 자식 프로세스로 격리한다. 전체 Dance plugin 프로세스를 죽여 이미 끝난 분석을 잃지 않는다. source와 frozen 근거만 읽고, 갤러리·출력 프로젝트·부모의 mutable cache를 직접 수정하지 않도록 한다. worker가 공유 mutex를 잡지 않게 하고 IPC 결과 크기에도 상한을 둔다.
- 모든 큰 호출 전후에 협조적 deadline을 검사하고, 부모 watchdog은 남은 시간을 넘겨 기다리지 않는다. deadline보다 앞선 별도 계산 마감으로 종료 여유를 남기며, 미응답 시 terminate 후 제한된 유예만 기다리고 필요하면 kill한다. 실패한 IPC 채널을 다음 작업에 재사용하지 않는다. 자식이 또 프로세스를 만들지 못하게 하거나 process tree까지 관리한다. 강제 종료는 finally를 실행하지 않으며 공유 lock/queue를 망가뜨릴 수 있다. [multiprocessing 종료 규약](https://docs.python.org/3.11/library/multiprocessing.html#multiprocessing.Process.terminate).
- 결과는 **완료된 후보 단위**로만 받는다. 한 후보의 필요한 양방향 검증 및 사전에 정한 경쟁 경로 검사가 모두 끝나기 전에 예산이 소진되면 그 후보 전체를 버린다. 첫 방향이 성공했다는 이유로 아직 검사하지 않은 반대 이름을 생략해 확정하지 않는다. 중간 mask·partial retry·늦게 도착한 결과는 이름 근거로 쓰지 않는다. timeout은 원래 출력으로 복귀하며 다음 실행의 seed/cache를 오염시키지 않는다.
- 응답시간 상한과 CPU/GPU 작업이 실제 종료된 시간은 별도로 계측한다. 모델 로딩 정지, source read 정지, forward/reverse 중 정지, 결과 전송 정지, worker crash, cancel과 deadline 동시 발생, 연속 timeout 후 재실행을 검증한다. timeout 후 남은 worker가 없는지, 메모리 회수 및 기존 출력 불변도 확인한다.

일반 OS에서 프로세스 생성·종료·장치 작업의 즉시 완료를 수학적으로 보장할 수는 없다. `subprocess.run(timeout)`도 초기 프로세스 생성은 여러 플랫폼에서 중단할 수 없다고 명시한다. [Python 프로세스 생성의 제한](https://docs.python.org/3.11/library/subprocess.html#subprocess.run). 따라서 **‘어떤 상황에서도 총 B초를 0초도 넘지 않음’이 문자 그대로의 요구라면 현 구조에서는 SAM OFF가 유일한 검증된 선택**이다. 선택적 모드를 만들려면 시작·종료 여유와 허용 오차를 포함한 SLA를 먼저 정의하고 측정해야 한다. worker를 미리 띄워도 비용을 지운 것이 아니므로 숨겨진 warmup 시간·메모리를 따로 보고한다. 현재 증거로 재활성화를 승인하지 않는다.

### 8.5. 두 역할 모호 후보의 채택 조건

**기존 main eligibility가 변하지 않았다는 사유만으로 ANT180.881–182.683 사쿠라와 NEON38.205–38.472 아이찡을 확정 이름으로 내보내는 데 반대한다.** unknown main이 특정 멤버의 확정 main 카드로 바뀌면 제품의 주장도 바뀐다. 실제 원경 군무·두 명 전경에서 이름만 맞춘 것으로 메인 역할까지 입증되지 않는다. 이는 SAM을 써도 동일하다.

저장된 진단을 네 후보의 **전체 proof path**에 다시 대조했다.

| 후보 | proof 내 관측 수 | scene reason | 명시적 camera episode | 선택 변경 기록 |
|---|---:|---|---:|---:|
| ANT48.081–48.415 | 11 | 전부 `main_eligible_composition` | 0 | 0 |
| ANT75.142–75.375 | 16 | 전부 동일 | 0 | 0 |
| ANT180.881–182.683 | 33 | 전부 동일 | 0 | 0 |
| NEON38.205–38.472 | 10 | 전부 동일 | 0 | 0 |

`segment.classify_main_scenes`의 마지막 else가 이 reason을 만든다. 적극적 solo/focal 증거가 아니다. `changes`가 비어 있는 것도 원래 선택을 바꿀 일이 없었다는 기록이지 확정 메인 역할의 증거는 아니다. 따라서 **현재 저장된 명시적 reason 필터 하나로 명확한 두 후보만 채택하는 방법은 확인되지 않았다.** camera episode만 허용하면 네 개 모두 탈락한다.

일반화 가능한 방향은 `observed_main`에서 이미 계산하는 full-frame 얼굴 크기·모든 몸의 torso/pose·경쟁 전경·시간 연속성 근거를 역할 proof로 보존하는 것이다. `main_role_timeline.choose_roles`의 `dominant_face`, `corroborated_foreground_subject`, `camera_focal_evidence`는 재사용 후보지만 reason 이름 하나만 통과시켜서는 안 된다. foreground 통과자·가려진 경쟁자·검출 누락·일시적으로 큰 얼굴·실제 두 명 전경을 고려하고, 동일한 선택 몸에 지속된 양성 근거가 있는 범위만 허용해야 한다. 기존 `foreground_subject`는 측정 가능한 여러 몸 및 얼굴·torso의 동시 우위를 요구하므로 모든 closeup을 해결하는 만능 조건도 아니다.

이 설계는 새 모델 호출 없이 가능한 관측 보존 개선이지만, 네 사례만 보고 새 크기 비율/최소 길이 임계값을 맞추는 것은 권하지 않는다. ANT48/75를 양성, ANT180/NEON38을 역할 보류, NEON82 원경·194초 group 경계·MMN 준비 중첩·실제 handoff를 거절/유지 fixture로 두고 세 영상 전체의 새 이름을 검사한다. 일반 role proof가 아직 없다면 네 개 모두 자동 적용을 보류하고 identity proposal/audit만 남기는 것이 일관된 선택이다. 명확한 두 사례의 육안 판정은 회귀 정답 후보로 활용하되 제품에 영상명·시간 허용 목록을 넣지 않는다.

부모가 제안한 ‘모든 프레임의 선택 reason/box를 보존하고 seed pair에서 명시적 역할을 요구’하는 방향은 증거 보존 측면에서 맞다. 다만 **seed 두 프레임에만 긍정적 역할이 있어서는 unknown 전체를 채울 수 없다.** identity continuity는 role continuity가 아니다. 같은 사람의 몸이 유지되면서 카메라가 솔로에서 군무로 빠질 수 있다. 최초 좁은 적용은 unknown의 관측 범위에도 같은 selected body의 긍정적 역할 근거를 요구하고, 빠진 프레임을 허용하려면 별도의 명시적 role-continuity proof를 요구해야 한다. 오른쪽 seed의 role을 거꾸로 연장하지 않는다.

또한 `choose_roles`의 `dominant_face`는 `size/x`가 있는 feature들만 비교한다. 보이지 않는 얼굴의 경쟁 몸은 그 크기 순위에서 빠진다. `foreground_subject`도 얼굴 크기가 없는 feature는 건너뛴다. 따라서 reason 문자열만으로 ‘모든 경쟁자를 배제한 solo proof’가 되지는 않는다. geometry 보충 과정은 `source='repeated_same_pose_geometry'`도 만들므로 `detected`와 구분해 남겨야 한다. 최소한 target/competitor 관측 가용성·선택 box·직접/보충 근거를 함께 기록하고, 명백한 foreground passer/duo 반례를 검증한다. 이 조건으로 명확한 두 후보도 통과하지 않으면 자동 적용하지 않는 것이 합리적이다.

부모의 추가 로컬 검사에서는 네 후보의 실제 pair reason도 모두 `measured_face_composition`으로 나왔다고 전달받았다(이 재추론은 부모 수행). 이어 제안된 ‘중앙 x 0.25–0.75, bbox 높이 > 화면2/3, owned face 두 시점’ 조건은 **shadow 후보 필터로는 가능하나 role proof로 바로 채택하는 것은 권하지 않는다.** ensemble 거절 조건의 반대가 solo의 충분조건은 아니다. 이 검토에서 저장된 pose를 직접 계산하면 ANT48의 전체11개 관측 모두에 다른 높이2/3 초과 몸이 있고, seed 두 시점에는 각각3명/2명이다. ANT75도 전체16개 중8개에서 그런 경쟁 몸이 있다. 따라서 ‘큰 경쟁 몸 없음’을 붙이면 양성도 사라진다. 반대로 경쟁자를 고려하지 않으면 중앙 큰 몸이 있는 duo·근거리 군무·foreground crossing도 통과한다. 네 사례를 잘 분리하는 것과 그 범주의 거짓 양성을 막는 것은 별도 검증이다. 추가 모델 없이 실제 초점/구도 증거를 얻지 못한다면 자동 적용 보류를 유지한다. [크기·경쟁 몸 원값](/private/tmp/dance-astra-review-20261102/central-closeup-candidate-audit.json).

### 8.6. 앞선 이름 교정 조사에 대한 보완: ANT117초

5절의 **“prep를 제외한 다른 이름의 반복 joint conflict는 발견하지 못했다”는 문장은 clip 안쪽의 pair 조사에 한정되며, 경계 밖의 원본 run을 포함한 일반 주장으로는 철회한다.** SAM의 실제 이름 재검증 기록에서 다음 반례를 확인했다.

- 과거 SAM은 ANT117.317200–117.617500을 홍은채에서 사쿠라로 바꾸고 이후 홍은채를 유지했다. 시작 seed는 7028, run의 마지막 사쿠라 얼굴은7048이며 6개 몸 관측을 추적했다. cycle IoU 최솟값은0.95965다.
- 최신 출력도117.317200–119.686233 전체를 홍은채로 두고 있다. 원본 joint7028(117.250467)·7048(117.584133)은 사쿠라 accepted 독립 pair이고7052(117.650867)는 홍은채다. pair의 첫 프레임이 clip 밖이라 내부만 검색하면 놓친다.
- 최신 원본 영상의7028/7036/7048에서 selected body는 동일한 사쿠라이고7052에서 홍은채로 바뀌는 것을 직접 확인했다. [선택 몸 표시 contact sheet](/private/tmp/dance-astra-review-20261102/ANT117-sam-revalidation.jpg).
- 동결된 기존 `_check_source_chain`에7028–7048의 최신 원본 관측을 넣은 read-only 실행은 **0.154초에 통과**했다. 그 범위에서 모든 관측의 몸 소유 일치, main 상태, group/handoff 없음, accepted 다른 이름 없음, primary 확정 다른 이름 없음도 확인했다. JSON 로딩·matcher 준비와 실제 앱 emit 비용은 이 타이머 밖이다.

따라서 SAM의 과거0.3003초 교정 효과를 얻기 위해 SAM 재활성화가 필수라고 결론 내릴 수 없다. 우선5절의 non-SAM correction planner가 clip 경계를 가로지르는 원본 pair를 처리하도록 검토하는 것이 더 싼 다음 실험이다. 다만 이 검사는 **몸 경로의 통과**이며, 117.6175라는 최종 출력 경계와 메인 역할의 정답을 제품 수준에서 모두 확정한 것은 아니다. 다음 홍은채 얼굴을 넘겨 사쿠라를 전파하거나 전체2.369초 clip을 교체하면 안 된다. 경계 적용·role proof·실제 emitter 검증은 별도로 필요하다.

### 8.7. 새 `face_seeded_paths.py` 읽기 전용 검토

부모가 요청한 미연결 구현과 테스트를 확인했다. 검토한 함수 SHA-256은 `28948d1668ba90326bdde552caa3bd8fb36a816d6656ef0243c3e42055955a21`이다. 검토 중 부모가 추가한 반대 이름 양방향·FPS 테스트까지 포함해 관련 테스트 **17개 통과**를 직접 확인했다. 이 결과는 pipeline 연결·실제 앱 검증을 포함하지 않는다.

두 방향 결과의 이름 충돌 거절, frozen pair/원본 관측 사용, 전체 경로의 group·handoff·몸 소유·얼굴 반대 증거 검사, 검증한 쪽 경계만 합치는 구조는 최소안과 부합한다. 다음 두 사항은 연결 전에 해결해야 한다.

1. **역할 조건 미충족:** 현재 `scene_kind == 'main'`만 검사하고 결과를 즉시 join한다. 8.5의 모호한 두 후보까지 그대로 확정한다. 신원 제안과 적용을 분리하거나 일반적인 positive role proof를 입력받아 적용을 제한해야 한다. 네 후보 모두의 기존 main 상태를 유지한다는 설명으로 이 조건을 대체하지 않는다.
2. **대상 내부 관측 0개도 복원되는 범위 확대:** `recover_face_seeded_paths`는 start 이전/이후 경계 관측을 찾지만 `start <= row.time_seconds < end`인 대상 관측이 존재하는지 검사하지 않는다. 연구 재생은 `no_samples`로 제외했다. 기존 synthetic fixture에서 unknown2.05–2.15, 이름A2.15–6.0으로 구성하고 대상 내부 관측을0개로 만들면, 현재 함수는2.05–6.0 이름A로 합친다. 최소안의 계약을 유지하려면 대상 내부 원본 관측이 없는 후보를 거절하는 검사와 회귀 사례가 필요하다. [재현 결과](/private/tmp/dance-astra-review-20261102/empty-target-review.json).

최신 코드가 이후 바뀌면 위 hash와 재비교해야 한다. 기존 dirty diff 전체를 이 변경의 diff로 취급하지 않았다. 이 검토에서 제품 파일·Person/shared 코드 수정, pipeline 호출 추가, SAM 실행, 앱 재빌드는 하지 않았다.

추가 근거: [시도별 재집계 및 역할 대조](/private/tmp/dance-astra-review-20261102/sam-addendum-evidence.json), [집계 스크립트](/private/tmp/dance-astra-review-20261102/sam_addendum_analysis.py), [ANT117 source 검사](/private/tmp/dance-astra-review-20261102/sam-correction-substitute.json), [해당 검사 재현 스크립트](/private/tmp/dance-astra-review-20261102/check_sam_correction_substitute.py), [검토 소스 해시](/private/tmp/dance-astra-review-20261102/addendum-reviewed-source-hashes.json).

### 8.8. 부모 후속 요청: ANT117의 구현 가능한 좁은 교정안

부모는 새 central-closeup 역할 조건을 shadow로 남기고 자동 적용하지 않겠다고 전달했다. 새 `observed_role_proof`가 전체 경로의 동일 몸을 검사하도록 바뀐 것은 seed 두 시점만 보는 문제를 줄인다. 하지만 중앙1/3의 점 좌표만으로 경쟁자를 제외하면 동일 크기의 두 전경 중 한 명이 바로 그 바깥에 있는 경우도 통과한다. 실제 함수에 x=600/320, 동일 높이500, 화면1000×600인 두 몸을 주면 `closeup_subject=True`였다. 왼쪽 몸 bbox는 중앙1/3과 겹친다. [실제 함수 반례](/private/tmp/dance-astra-review-20261102/central-closeup-duo-counterexample.json). shadow 유지 권고는 그대로다. 이는 8.7의 최초 hash 이후 생긴 후속 구현에 대한 추가 검토다.

실제 제품에 넣을 작은 변경이 필요하다면, **현재 main으로 출력되어 이미 이름이 있는 인접 두 구간의 잘못된 신원 경계만 교정**하는 안이 더 직접적인 증거를 갖는다. unknown→named, main/group 선택, preparation 추가와는 별도 기능으로 둔다. 이 안도 구현·앱 검증 완료를 뜻하지 않는다.

제안 함수는 `plan_named_prefix_corrections(output, original_observations, frozen_joint, final_records, matcher, *, video_path, fps, group_segments, handoffs)`다. frozen 입력에서 proposal을 다 만든 후 한 번 적용한다. 등록 Dance, 최종 main projection/기존 coalesce 뒤, incoming preparation 전에 배치하면 selected main과 preparation 대상 혼동을 피할 수 있다.

1. 이름A의 왼쪽 clip과 다른 이름B의 오른쪽 clip이 정확히 맞닿은 경계만 후보로 한다. 출력 이름은 검색 범위일 뿐 신원 표가 아니다. 왼쪽 끝부분의 원본 얼굴과 오른쪽 앞부분의 원본 얼굴이 같은A를 독립적으로 지지하는 pair를 찾는다. 두 프레임이 서로 다르고0.15–0.6초 간격이며 `_valid`, detector≥0.9, joint accepted, 원본 selected-body 소유 조건을 만족해야 한다. **한 얼굴은 경계 밖, 다른 하나는 안**이어야 하며 오른쪽 clip 전체를 A로 바꾸지 않는다.
2. 시간순 accepted 원본 face run을 사용한다. pair 사이에 다른 accepted 이름이 하나라도 있으면 거절하고, 다음 다른 accepted 이름은 확장 종료점으로 취급한다. 이름 없는 joint conflict/insufficient를 통과한 표로 승격하지 않는다. 원본 primary의 확정 반대 이름 및 기존 반복 alien-face 검사는 그대로 veto한다. 새로 교정한 A나 현재 출력 label을 다음 pair의 증거로 만들지 않는다.
3. source path는 경계 밖 seed부터 마지막A 지지 프레임까지 완전히 검증한다. 모든 원본 관측 존재, selected body 일치, main 상태, group 겹침 없음, 경로 내 확인된 handoff 없음, 정확한 원본 decode, 기존 `_check_source_chain`의 몸 경쟁·색/구조 veto를 유지한다. 실제 unknown/빈 관측 prefix를 이 기능의 대상으로 확장하지 않는다.
4. 교정 범위는 현재 B 시작부터 검증한 마지막A 관측의 시간 셀까지만이다. 기존 `joint_identity.revalidate_named_segments`의 샘플 중간점 partition을 재사용하되, 다음 다른 accepted 얼굴·다른 몸·cut/handoff 너머로 A를 확장하지 않는다. 이 사례에서 A7048과 다음 B7052의 중간점7050/fps가117.617500이다. **이 중간점은 출력의 표본화 규약이며 실제 연출 교대의 정답 시각이 직접 측정된 것은 아니다.** exact boundary가 필요하면7050 부근을 별도 판정한다. 증거가 부족하면 더 좁게 수정하거나 보류한다.
5. 검증된 prefix와 왼쪽A 사이의 경계만 제거하고 오른쪽B 나머지는 유지한다. 서로 충돌하는 proposal은 적용 순서로 해결하지 않고 거절한다. 전체 시간·기존 main/group 범위·원본 얼굴·gallery는 보존하고, audit에 old/new 이름·pair·source 경로·종료를 막은 다음 이름·변경 구간을 남긴다.

이 사례의 실제 입력과 예상 결과:

| 항목 | 값 |
|---|---|
| 기존 출력 | 사쿠라110.977533–117.317200 / 홍은채117.317200–119.686233 |
| 원본A pair | 7028/7048, 간격0.333667초, detector0.906176/0.911887 |
| path | 7028,7032,7036,7040,7044,7048; 같은 selected body; 기존 source 검사 통과 |
| 반대 증거 | path 안 accepted 다른 이름·primary 확정 다른 이름·반복 alien pair 없음; group/handoff 없음 |
| 다음 다른 이름 | 7052 홍은채 accepted. 이 프레임으로 A 몸 경로를 연장하지 않음 |
| 제한된 proposal | 117.317200–117.617500 홍은채→사쿠라,0.300300초 |
| 적용 시 출력 | 사쿠라110.977533–117.617500 / 홍은채117.617500–119.686233 |

이름과 selected body가 서로 맞지 않는 구체적 모순을 고치는 안이다. 현재 selected body 자체가 연출상 올바른 메인인지까지 새로 입증하지는 않는다. 원본 두 인물의 실제 교대 주변을 보고 확인해야 하며, 결과를 전체 main-role 문제의 해결이라고 보고하지 않는다.

필수 회귀는 실제 ANT117 fixture 외에도: 정상 A→B에서 B의 첫 독립 얼굴이 있는 경우 유지, A→B→A 중 B를 건너 pair 금지, 단일/중복A 얼굴 거절, pair 사이 acceptedB 거절, 불완전 경쟁 몸·source cut·handoff·group 경로 거절, preparation 다른 subject 거절, 반대 방향 prefix/suffix의 시간 보존, 전체 B clip 치환 금지, 반복 실행 불변이다. 기존17개 one-sided 테스트가 이 교정을 검증하는 것은 아니다. 저장된 source·face·pose와 변경될 exact prefix를 회귀 fixture로 분리하고 실제 세 영상 앱 결과에서 다른 이름 경계가 함께 바뀌었는지도 확인한다.


## 9. 후속 제품 변경 검토 — `named_boundaries` 및 pipeline 연결

부모는 실험적 one-sided 자동 복원과 central-closeup 조건을 제품에서 제거하고 `/private/tmp/dance-quality-paths-20261102/experimental`에 보존했다. 실제 제품 변경은 인접한 **기존 named A→B의 앞당겨진 이름 경계**만 `reconcile_named_boundaries`로 교정하는 것으로 축소됐다. 8.7의 실험 함수 관련 지적은 이 새 제품 함수에 그대로 적용되는 미해결 목록이 아니다.

새 구현은 마지막 확인된 원본 프레임의 끝 `(frame+1)/fps`까지만 이동하며 중간점 추정을 하지 않는다. 이번 ANT 사례의 적용값은117.600817초다. 8.8의 초기 설계 예시117.617500초보다 좁은 범위이며, 이 보수적 선택을 지지한다.

### 9.1. 발견한 결함과 수정 확인

**[P2] seed 품질 조건으로 accepted 반대 이름까지 제외하면 안 된다.** `named_boundaries.py`의 `accepted` 목록은 `_valid`에 더해 `detector_score >= .9`를 요구한다. 이 목록을 seed 선정뿐 아니라 before/after run 구성과 `conflicting_joint_face` 검사에도 재사용한다. 그러나 `joint_video_matches`는 `_valid`인0.8–0.9 얼굴도 accepted 이름을 낼 수 있다. 그 결과 seed 사이의 유효한 acceptedB가 누락되어 A→B→A를 A로 덮을 수 있다.

기존 테스트 fixture에 detector0.85, joint acceptedB인40번 프레임을 두고 주변36/44번은A로 유지하자, 함수는A를2.25초까지 연장했다. 중간 얼굴의 photo-primary가 모호한 경우에도 이를 재현해 primary veto가 자동으로 막아주지 않음을 확인했다. [독립 재현](/private/tmp/dance-astra-review-20261102/named-boundary-low-detector-conflict.json). 부모가 추가한 같은 취지의 회귀 테스트도 직접 실행 시 실패했다.

초기 검증은 **1 실패·25 통과**였고 실패 테스트는 `test_usable_joint_conflict_below_seed_quality_still_blocks_boundary_correction`이었다. 부모가 이를 수정해 seed 후보만0.9 이상으로 제한하고, 시간순 원본 run/반대 이름에 의한 종료/경로 conflict는 **모든 `_valid` accepted joint 얼굴**로 검사하도록 분리했다. 수정본을 다시 읽고, 독립 재현 사례가 기존 출력을 그대로 유지하며 거절되는 것까지 확인했다. [수정 후 독립 재현](/private/tmp/dance-astra-review-20261102/named-boundary-low-detector-conflict-fixed.json).

최종 검토한 `named_boundaries.py` SHA-256은 `62047bf9ec86bc138dffa8c6948c2ec7d7f3e14f26c380de9ba9f4bde42aeab5`다. named boundaries·observed main·joint seed pipeline·observed main pipeline·incoming context pipeline의 관련 테스트를 실행해 **37개 통과**를 확인했다. [실행 로그](/private/tmp/dance-astra-review-20261102/named-boundary-final-tests.log), [전체 검토 대상 해시](/private/tmp/dance-astra-review-20261102/boundary-final-source-hashes.json). 전체 저장소 테스트를 독립 실행하거나 모두 통과했다고 주장하지 않는다.

### 9.2. 직접 재생한 실제 세 영상 결과

부모의 replay 스크립트를 검토한 뒤 출력 위치만 이 검토 디렉터리로 바꾸어 제품 함수를 직접 실행했다. 최신 저장 프로젝트의 원본 face·pose·joint·reference·source video를 입력했다. 새로운 얼굴/pose/SAM 추론은 없다.

| 영상 | 변경 | 함수 내부 경과시간 |
|---|---|---:|
| MMN | 없음 | 0.005초 |
| ANT | 사쿠라/홍은채 경계117.317200→117.600817,0.283617초 교정 | 0.148초 |
| NEON | 없음 | 0.013초 |

위 값은 충돌 누락 수정 후 다시 실행한 결과다. 독립 replay는 각 clip의 이름을 유지하면서 ANT49/50번 인덱스의 맞닿은 경계만 이동했다. 각 영상 main clip 수57/102/150, 모든 unknown 구간, 총 출력 시간은 그대로다. group 출력은 이 함수가 받는 읽기 전용 veto 입력이며 함수가 만들거나 변경하지 않는다. [출력 불변 조건 검사](/private/tmp/dance-astra-review-20261102/named-boundary-invariants.json), [재생 스크립트](/private/tmp/dance-astra-review-20261102/named_boundary_product_replay.py), [최종 재생 로그](/private/tmp/dance-astra-review-20261102/named-boundary-final-replay.log), [ANT 상세 결과](/private/tmp/dance-astra-review-20261102/ANT-named-boundaries-replay.json).

이 타이머는 JSON 로딩과 matcher 준비를 제외한 단일 로컬 재생이다. 실제 앱 전체 속도·모델 비용·Windows 수치가 아니다. 저장된 최종 결과에는 기존 preparation도 포함되어 있지만 제품 호출 위치는 preparation 전이므로, 최종 앱 출력·카드·썸네일과 통합 동작은 부모의 실제 재실행에서 별도 확인해야 한다.

### 9.3. 연결 위치 및 범위 검토

`pipeline.py`에서 최종 `coalesce_named_output` 뒤, `_include_incoming_preparation` 앞에 호출되어 있다. 이 시점의 `face_results`는 원래 `all_face_results`를 참조하며 아직 `release_person_thumbnails` 전이다. 따라서 원본 경계 밖 pair를 검색할 수 있고, 새로 만들어진 preparation 얼굴을 main 신원 근거로 섞지 않는다. 완전한 main-role audit가 없으면 `handoffs=None`으로 넘어가 함수가 적용하지 않는다.

함수는 frozen 입력에서 모든 correction을 수집한 뒤 한 번 적용하며, 기존 named clip만 대상으로 한다. 실제 범위 적용은 두 인접 clip의 시작/끝·bbox·evidence·preview를 재분배한다. clip 개수와 이름 목록을 유지하고 unknown/group를 새로 승격하지 않는다. 새 역할 관측 저장은 진단용이며 central-closeup 승인 조건은 남아 있지 않다. SAM의 두 호출은 여전히 비활성화 상태다.

검토 결론은 **발견한 accepted 반대 얼굴 누락이 수정됐고, 검토 범위에서 추가로 빌드·실제 앱 비교를 막을 사항을 찾지 못했다**는 것이다. 세 영상의 실제 앱 결과·카드·썸네일·총 실행시간은 부모가 이어서 확인한다. SAM은 OFF를 유지한다. 이 검토에서 제품 파일을 수정하거나 앱을 빌드·실행하지 않았다. 이후 수정본은 위 source hash와 함께 다시 검토해야 한다.


## 10. 실제 앱 세 영상 결과의 독립 검토

부모의 비교표를 그대로 인용하지 않고, 앱이 보존한 여섯 프로젝트의 `projects/items`, `jobs/items`, `json/dance_meta.json`, `diagnostics/face_evidence.json`과 이미지 파일을 직접 읽어 새 비교 스크립트로 검증했다. **ANT의 경계 교정과 그에 따른 썸네일·진단 표본 재배분 외에 이름·구간·이미지 퇴행을 발견하지 못했다. SAM은 계속 OFF다.** 이 결론은 저장된 실제 앱 산출물 비교이며, 이번 검토에서 앱이나 모델 분석을 새로 실행한 것은 아니다.

### 10.1. 비교 대상과 원본 추적

|영상|기준 프로젝트|새 프로젝트|main / group|클립 썸네일|검사한 전체 이미지|
|---|---|---|---:|---:|---:|
|MMN|1793610108675|1793617663026|57 / 32|89|359|
|ANT|1793610363935|1793617753764|102 / 32|134|604|
|NEON|1793610789306|1793617837063|150 / 56|206|813|

모든 앱 원본 JSON은 부모가 보관한 baseline/new 스냅샷과 정확히 같았다. 기준 프로젝트의 metadata·face evidence SHA-256은 **앞선 독립 검토에서 동결한 해시**와도 일치한다. 새 결과에 맞춰 비교 기준이 바뀐 흔적이 없다. 원본 MP4 해시를 다시 계산해 기준·새 실행·이전 독립 검토 기록과 일치함을 확인했다. 설정, 아티스트/멤버 선택, 참조 이미지 바이트와 얼굴 임베딩도 같다.

새 앱이 기록한 `named_boundaries`, `pipeline`, `observed_main` 해시는 9절의 최종 검토 소스와 같고, 현재 앱 venv 파일 및 저장소 소스와도 일치한다. `face_evidence`도 앱/저장소 해시가 같으며 작업 전 스냅샷과의 차이는 새 모듈의 해시 기록을 추가한 두 곳뿐이다.

### 10.2. 전체 출력과 썸네일 확인

429개 클립의 전체 행을 비교했다. MMN·NEON은 모든 행이 동일하며, ANT는 아래 두 값만 달랐다. clip ID·순서·인물 이름·개수는 같다.

|ANT 클립|항목|기준|새 결과|
|---|---|---:|---:|
|main_0049 / 사쿠라|end|117.317200|117.600817|
|main_0050 / 홍은채|start|117.317200|117.600817|

이동량은 **0.283617초, 원본 17프레임**이다. 두 구간의 접점이 함께 이동하므로 새 공백·겹침이 생기지 않는다. 영상별 main 구간의 합집합, 모든 unknown 행, 단체 행, 인물 카드가 정확히 보존됐다. 진단에선 기존 50번 클립의 앞쪽 몸 표본 4개가 49번 뒤로 옮겨졌고, 49번의 `match_reason`만 `original_face_run_boundary`로 바뀌었다. 표본의 좌표나 원본 얼굴 근거를 새로 만든 것은 아니다.

**1,776개 이미지의 경로·SHA-256을 전수 비교해 추가·삭제 없이 한 장만 바뀐 것을 확인했다.** 이 중 클립 썸네일은 429장, 진단 얼굴 이미지는 1,245장, 참조 이미지는 102장이다. 변경은 ANT `clips/dance/main/main_0050.jpg` 한 장뿐이다. 이전/새 이미지를 직접 열어 확인했고, 앱의 FFmpeg와 같은 추출 인자로 원본에서 각각 117.317초·117.601초 이미지를 scratch에 다시 추출했다. 두 재추출 결과 모두 해당 앱 썸네일과 **바이트까지 일치**한다. 변경은 시작점 이동에 따른 정상 재생성이며 다른 원본·잘못된 캐시·인코딩 방식 교체의 흔적은 없다. 인물 대표 이미지도 유지됐다.

세 영상의 원본 face segments·pose heads·9,266개 진단 프레임은 완전히 동일하다. face evidence의 비실행정보 차이는 전체 역할 관측 및 경계 교정 진단의 추가와 두 경과시간 값뿐이다. 역할 관측을 추가하면서 기존 선택 몸·판정을 바꾼 증거가 없다.

기존 사용자 14개 검토 구간은 원본 JSON에서 교집합을 다시 계산해 전부 동일함을 확인했다. 이는 기존 오류가 해결됐다는 의미가 아니다. **미확인 39.577초, 1초 미만 클립 245개**, ANT 4.57–6.14/9.91–10.28 및 MMN 38.20–39.34의 공백은 남아 있다. 전체 영상의 모든 메인 역할을 새 정답표로 판정한 검토도 아니므로, 절대 품질을 보증하는 결론으로 확대하지 않는다.

### 10.3. SAM OFF와 추가 비용

기준·새 실행 모두 mask/joint 정책은 `disabled_runtime_cost_v1`이고 이유는 `disabled_runtime_cost`다. 두 단계의 후보 목록·수정/복원량·기록된 실행시간은 모두 0이다. 기록된 모델 목록에 SAM이 없으며, 실제 로드된 해시와 같은 `pipeline.py`에서도 두 SAM 호출은 주석 처리되어 있다. 0초 타이머만으로 비활성화를 추정한 것이 아니다.

|영상|새 경계 검사|기존 가벼운 몸 연속성|SAM mask / joint|
|---|---:|---:|---:|
|MMN|0.019656초|0.457844초|0 / 0초|
|ANT|0.152669초|0.610763초|0 / 0초|
|NEON|0.009955초|0.958882초|0 / 0초|

가벼운 몸 연속성 검사는 SAM 추적이 아니다. 신규 경계 검사 합계는 0.182280초다. 이는 `cluster_map` 안에서 수행되므로 별도 시간으로 더하면 중복 계산된다. 현재 metadata의 `nested_stages.cluster_map` 목록에는 `named_boundaries`가 빠져 있다. 실제 동작을 막는 문제는 아니지만, 시간 집계 도구가 이 목록만 신뢰하면 중복 합산할 수 있어 진단 표기의 보완 여지가 있다. 부모 보고서는 이 한계를 이미 명시하고 있다.

### 10.4. 실행시간 독립 재계산

라이브 job의 `startedAt`부터 project의 `completedAt`까지 계산했다. `job.finishedAt`도 같은 완료 시각이며, 여섯 job/project 모두 completed·error 없음이다.

|영상|기준 실행|새 실행|감소|새 대기열 시간|새 pipeline 내부 시간|
|---|---:|---:|---:|---:|---:|
|MMN|314.043초 (5:14.043)|295.082초 (4:55.082)|6.04%|0.098초|285.712초|
|ANT|422.293초 (7:02.293)|397.721초 (6:37.721)|5.82%|204.343초|394.556초|
|NEON|483.083초 (8:03.083)|439.264초 (7:19.264)|9.07%|519.026초|435.730초|
|실행 합계|1219.419초 (20:19.419)|1132.067초 (18:52.067)|7.16%|—|—|

합계 87.352초 단축은 부모 수치와 일치한다. 다만 **각 조건 1회, 다운로드 캐시 재사용 조건의 관측값**이다. 이번 기능이 7.16% 속도 향상을 만들었다고 입증하지 않는다. OS/모델 캐시·발열 등 환경 변동은 통제된 반복 실험으로 분리하지 않았다. cold-start·Windows 실측도 아니다.

제출 시점과 앞 작업의 남은 시간이 달라져, 대기열까지 포함하면 ANT는 481.064→602.064초, NEON은 539.285→958.290초였다. 따라서 실행시간 개선을 사용자가 제출 후 기다린 시간의 개선으로 표현하면 안 된다. 이는 분석 자체가 느려졌다는 증거도 아니다. 본 표는 대기열을 분리했고, 서로 겹치는 대기시간을 실행 합계에 더하지 않았다.

### 10.5. 독립 검토 결론과 증거

검사 범위에서 **추가로 적용을 막을 품질 퇴행을 찾지 못했다.** ANT 한 경계의 제한된 교정은 실제 앱에서도 그대로 재현됐고, 다른 출력·참조·원본 관측은 유지됐다. SAM OFF 요구도 충족했다. 기존 품질 과제는 미해결이며, 속도 수치는 한 번의 관측 결과로 제한한다.

직접 작성한 비교와 70개 불변 조건 검사를 모두 통과했다. 이는 앱 산출물 감사이며, 제품 단위 테스트 70개를 새로 실행했다는 뜻이 아니다. 제품 수정·앱 빌드·SAM 추론·커밋·푸시는 하지 않았다. 썸네일 재추출과 보고서·증거 저장만 수행했다.

- [독립 비교 스크립트](02-astra-independent-app-evidence/audit_actual_app.py), [직접 계산한 전체 비교와 이미지 해시](02-astra-independent-app-evidence/actual-app-independent-audit.json).
- [불변 조건 검사 스크립트](02-astra-independent-app-evidence/verify_actual_app_audit.py), [70개 검사 결과](02-astra-independent-app-evidence/actual-app-independent-verification.json).
- [썸네일 원본 재추출 검증](02-astra-independent-app-evidence/actual-app-thumbnail-reproduction.json), [기준 썸네일 재추출](02-astra-independent-app-evidence/ANT-main0050-before-reextracted.jpg), [새 썸네일 재추출](02-astra-independent-app-evidence/ANT-main0050-after-reextracted.jpg).
