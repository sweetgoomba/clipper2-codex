# MMN45–48 잔여 결과: JSON/소스 읽기 전용 진단

대상은 통합 앱 MMN1793649506337이다. 원본 JSON과 코드만 읽었으며 pytest, 제품 함수 재실행, 영상 디코딩, 모델, 벤치 변경은 하지 않았다. 사용자45–48은 근사 범위로 취급했다.

## 결론

저장 증거 기준으로 주된 문제는 얼굴 이름 혼동이나 결측 hold가 아니다. 원래 선택된 **허윤진 몸**과 별도로 추적한 **사쿠라 준비 동작 몸**이 같은 화면에 있고, 준비 동작을 사쿠라 클립 앞에 추가하는 후처리가 기존 허윤진 클립을 보존하여 **1.1011초 중복**을 만든다. 다음 장면의 사쿠라 준비 동작을 사용자가 메인 맥락으로 원하는 문제와, 현재 중심·얼굴 크기 기반 메인 역할의 선택 기준이 다르다.

실제 픽셀은 열지 않았으므로 사람 정답이나 연출 의도를 새로 확정하지 않는다. 기존 frozen joint/pose 기록이 각각 어떤 몸을 지지하는지 분리한 결과다.

## 세 단계의 실제 범위

| 단계 | 허윤진 | 사쿠라 |
|---|---|---|
| identity_spans |43.143100–46.463083|46.463083–47.981267|
| performance_parts/incoming boundary 이후 |43.143100–46.463083|46.463083–47.981267|
| 최종 meta, preparation 이후 |43.143100–46.463083|45.361983–47.981267|

최종 사쿠라 클립은 이미 약45–48 요청 범위를 포함한다. 남은 겹침은45.361983–46.463083이며, 준비 맥락 확장량과 정확히 같다. 45.0–45.361983을 추가로 사쿠라라고 단정할 근거는 이 분석에서 만들지 않았다. 해당 앞 장면의 원래 selected joint는 계속 허윤진을 지지한다.

## main 선택과 얼굴 이름

2719컷(45.361983)부터2785컷(46.463083) 사이에는2720..2784의17샘플이 있다.

- 17/17에서 원래 selected와 preparation target의 몸 index/box가 다르다.
- 원래 FaceObservation.body_bbox는17/17에서 selected role box와 정확히 같다.
- 원래 selected feature source는17/17 `detected`; role reason은16 `measured_face_composition`,1 `corroborated_foreground_subject`이다. incomplete incumbent, pending, near-tie hold가 원인은 아니다.
- 선택된 몸의 원본 joint는14회 허윤진 accepted,2회 insufficient,1회 conflict이다. 사쿠라 accepted는0회다.
- 별도 preparation 몸에서는 사쿠라 accepted가6회이며, detector .9 이상 positive seed는2768/2772/2780/2784이다. 17샘플 전부 사쿠라 얼굴을 직접 읽은 것은 아니다. 원본 preparation audit의 몸 경로가 이를 연결하며,2768→2772는 독립 이름을 가진 양끝으로 보강된 edge로 기록돼 있다.
- 사쿠라 준비 몸의 role feature source는12 detected/5 repeated_same_pose_geometry다. 이것을 원래 선택된 메인 얼굴이나 새 naming gallery anchor로 바꾸지는 않았다.

대표적으로2752(45.912533)에서 원래 selected index0의 joint는 허윤진 accepted(primary .482632, secondary .372352), 별도 context index2는 사쿠라 accepted(.534994/.436339)다.2768/2772도 두 다른 몸이 각 이름을 동시에 지지한다. 따라서 한 몸의 이름 경계가 늦어진 ANT154와 구조가 다르다.

저장된 x/size에 코드의 `size/height × (1−abs(x−width/2)/(width/2))²`만 산술 적용하면 허윤진이 사쿠라보다17/17 높고, 비율은1.575–2.231배다. 이는 choose_roles 재실행이 아니라 저장 수치에 대한 설명이다. 후반 일부 샘플에서 사쿠라 얼굴 size가 더 커져도 화면 중심 가중치가 허윤진 쪽을 계속 우세하게 만든다. 다음 단독 장면의 주인공/준비 동작 의도는 이 점수에 포함되지 않는다.

## 경계 조립이 겹침을 만드는 정확한 위치

`pipeline.py:1184` 부근에서 build_performance_parts가 끝난 뒤 `_include_incoming_preparation`을 호출한다. 사쿠라 incoming cut2785 앞의 formation shot2719..2785를 별도 context로 인정했다.

`incoming_context.py:341`의 `apply_preparation_contexts`는 docstring부터 “다른 사람의 role을 대체하지 않고 준비 맥락을 앞에 붙인다”고 정의한다. `:363`은 사쿠라 segment.start만45.361983으로 바꾸고, 원래 허윤진 segment.end는 수정하지 않는다. 새 context evidence 이름은 None으로 남고, 별도 audit에 사쿠라 joint를 기록한다.

따라서 현재 겹침은 우발적인 산술 midpoint 오류가 아니라 기존 preparation contract의 직접 결과다. 두 클립 모두 main 목록으로 내보내므로 UI에서는 canonical main과 준비 맥락 확장이 구분되지 않는다. 겹치는 허윤진 클립까지 줄이려면 원래 역할/출력 의미에 대한 별도 수정이 필요하다. 다른 몸의 긍정적인 허윤진 얼굴 증거를 사쿠라로 덮어쓰는 수정은 근거에 반한다.

## incoming_identity_boundary가 적용되지 않은 이유

실제 audit는 corrections=[], candidates=[], source reads0이다. 이 함수는 후보 생성 전 단계의 개별 거부 원인을 저장하지 않아, 이번 읽기만으로 실제 실행한 첫 거부 줄을 재현했다고 주장하지 않는다.

다만 저장 컷과 코드상 적용 불가 조건은 확정할 수 있다.

1. `performance_parts.py:121`에서 preparation 확장 전에 실행된다. 당시 Y/S 경계는 정확히cut2785/fps=46.463083이다.
2. 사쿠라 원래 selected 관측은 컷 뒤2788(46.513133)부터다. 어느 incoming seed를 택하더라도 원래 selected 몸의 역방향 경로는2788→2784 사이 source cut2785를 건널 수 없다(`incoming_identity_boundary.py:197`).
3. 가장 이른 가능한 B 관측2788은 기존 경계보다 뒤여서, 경계를 앞당길 후보가 될 수 없다(`:206`). 컷 이전 selected 몸에는14개 허윤진 accepted joint가 있으므로 이쪽을 사쿠라 몸으로 이름만 바꾸는 것도 금지 조건이다.
4. 나중 preparation이 별도 몸을 앞에 붙여 만든 겹침은 함수 실행 후에 발생한다. 다시 호출해도1.1011초 겹치는 두 part는 adjacent guard(`:178`)를 통과하지 못한다. 이 guard를 풀어도 몸/얼굴 증거가 달라 근본 해결이 아니다.

## 다음 개선의 정확한 범위

이 구간은 단편을 무조건 합치거나 최소 길이를 적용해서 해결할 문제가 아니다. 얼굴이름 경계 교정기는 현재 선택된 몸을 정당하게 유지하며, preparation은 다른 몸의 맥락을 따로 추가한다. 남은 병목은 **현재 중심 위주의 main 선택과 다음 장면의 준비 동작 맥락을 어떻게 하나의 사용자용 클립 범위로 조립할지**다.

벤치 종료 후 검증할 대상으로는 저장된 두 몸을 같은 소수 원본 프레임에서 비교하고, 준비 맥락의 겹침을 의도적으로 유지할지 또는 증명된 role 전환을 별도 판단할지를 들 수 있다. 사용자 근사 시각이나 사쿠라 이름 자체로 선택 몸을 바꾸거나, 컷/반대 신원 veto를 완화할 근거는 없다.

수치·원본 row·단계별 범위는 `mmn45-current-json-audit.json`에 보존했다. 제품 파일은 수정하지 않았다.

## 후속 의미 개선에 필요한 핵심 연결점 두 곳 (이번 freeze 변경 없음)

1. **현재 구도와 다음 파트 의도를 구별할 입력 연결이 없다.** `stage_prominence.foreground_subject`는 같은 프레임에서 얼굴 크기와 torso 길이가 모두 다른 사람보다1.08배 이상인 전경 몸만 보강한다. `choose_roles`는 그것 또는 얼굴 크기×중앙 가중치를 사용한다. `focal_composition.camera_focal_evidence`도 컷 안에서 안정된 중앙 몸·push-in·옆으로 지나가는 더 큰 몸이라는 좁은 구도만 증명한다. 다음 컷의 주인공이나 군무 내 준비 동작은 이 역할 판단의 입력이 아니다. 실제 window에는 camera episode가 없고, 사쿠라 preparation x는1170→1384로 이동해 후반에는 focal의 중앙±.12width 조건 밖이다. 이 증거가 기존 방식의 결측으로 사라진 것이 아니라, 애초 해당 방식이 다루지 않는 연출 유형이다.

2. **이미 확인한 전후 파트/자리 이동 증거는 preparation에서만 쓰인다.** `incoming_context._formation`, `_repositions`, 다음 샷의 independently named foreground anchors는 앞 formation의 자리 이동과 다음 단독 파트를 연결한다. 실제 accepted audit에는2719/2785 두 컷,17개 visible target,4개 강한 사쿠라 named frame,2816/2820/2824/2828의 incoming front proof가 남아 있다. 하지만 `apply_preparation_contexts`는 의도적으로 outgoing role을 보존하고 incoming clip만 확장한다. 이 충분히 구체적인 맥락을 exclusive-main 우선순위로 승격하는 규칙이나 UI에서 준비 맥락 범위를 구분하는 정책은 현재 없다. 근거가 audit에서 유실된 것은 아니며, role/출력 의미에 연결되지 않은 상태다.

이 두 지점은 향후 구도·안무·전후 파트 선호를 검토할 위치이지, 현재 명명된 허윤진 관측을 부정하는 사유가 아니다. existing overlap을 일괄 잘라버리면 의미 기준이 바뀌므로 이번 freeze에는 손대지 않는다.
