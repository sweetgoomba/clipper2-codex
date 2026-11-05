# 메인 역할 연속성 개선 — 설계·실행 계획

2026-11-03 KST. 사용자 승인: 같은 메인 파트의 관측 공백/개인·단체 판정으로 생긴 단편화를 고치되, 실제 교대와 짧은 파트는 보존한다. 반복 설계 질문 없이 구현·독립 검증을 계속하라는 세션 지시를 따른다.

## 기준과 선택

최신 앱 MMN1793639096353 / ANT1793639190408 / NEON1793639268565. 전체409개, 1초 미만226개(멤버69/204, 미확인79/88, 단체78/117). 실제 시간5:15/7:12/7:41. 이전 대비91초 증가는 아직 원인 미확정이다.

최소 길이 강제/이웃 이름으로 일괄 흡수는 실제 교대를 잃으므로 제외한다. 작은 후처리 조건만 누적하는 방법도 효과가 부족했다. 선택한 방향은 최초 메인 역할의 실제 관측/이전 선택 유지/관측 공백을 구별하고, 동일 파트의 지속 근거와 진짜 개인·단체 전환을 구분하는 것이다. 얼굴 이름과 메인 역할은 서로 다른 판단이며 단체 출력과 개인 메인은 동시에 성립할 수 있다.

## 제약

- 안무 모듈에만 변경. 인물 하이라이트, 공유 모델, SDK 동작 보존.
- 무거운 SAM mask/joint 몸 추적은 계속 OFF.
- 3초 제한, 임의 최소 클립 길이, 무조건 단체→개인 변환 금지.
- 기존 프로젝트/자동 결과/사용자 정답 보존. 새 결과로 비교.
- 원본 Python 기존 fix/dance-gpu-performance-20261102 미커밋을 이어가며 커밋·푸시·병합 안 함. 기존 전체 변경을 되돌리지 않음.
- 품질 변화가 원본 face/role 자료 변화를 필요로 한다면 허용하되, 정답 보존·근거 정확성으로 평가. 원본 관측 불변 자체를 목표로 삼지 않음.
- 새 추론·디코딩은 비용과 필요성을 먼저 입증. Windows에서 동작하는 순수 Python/NumPy 처리 우선.

## 구현 계획 (writing-plans)

- [ ] 1. 실제 조각에서 최초 잘못 생긴 경계를 재현한다. 긴 동일 identity가 잘린19개, 같은 이름 사이 group15개, incumbent 실측 누락 유지 분기를 분리 조사한다. 기존 사용자 정답과 실제 원본 화면을 대조한다.
- [ ] 2. 공통 원인이 확인되면 해당 production 단계의 실패 회귀 테스트를 먼저 만든다. 실측 메인/연속성 유지/미관측 구분을 구현하고 새 관측을 앵커로 무한 전파하지 않게 한다. 세 영상의 동일 저장 입력으로 효과와 추가 비용을 비교한다.
- [ ] 3. Astra xhigh 독립 세션이 인물 교대, 관측 누락, 큰 경쟁자 가림, 실제 원경 단체, 카메라 컷을 검토한다. 테스트 수를 품질 정확도로 해석하지 않는다.
- [ ] 4. 효과가 확인된 변경만 원본 앱에 빌드하고 같은3 YouTube 프로젝트를 새로 실행한다. 사용자 정답 사례와 변경 구간의 실제 영상, 클립 수·길이·미확인·단계별 시간을 비교한다. 속도 차이는 조건 통제 없이 코드 효과로 단정하지 않는다.
- [ ] 5. 결과·실패 실험·남은 문제와 소스 스냅샷을 .codex에 보존한다.

## 검증 초점

1. 얼굴이 안 잡힌 incumbent와 새로 분명해진 후보의 실제 교대.
2. 같은 인물이 유지되지만 한 관측의 얼굴/몸 일부만 사라진 경우.
3. 양끝 이름은 같아도 가운데 다른 메인 또는 진짜 단체가 있는 경우.
4. 카메라 컷·줌아웃·가림을 단순 시간 길이로 합치는 오류.
5. 다른 모델의 경쟁 이름, 소스 프레임과 경계 소수점 오차.

시작 소스 스냅샷: /private/tmp/dance-role-continuity-20261103/before-manifest.json. Astra 독립 세션 01a19bab-62d3-7c52-8538-54703f0fc96a에 읽기 전용 원인·설계 검토를 전달했다.

## 진행 중 증거 (완료 보고 아님)

- 최초 부분 fresh 역할 복원은 새 작은 island를 늘려 폐기했다. 독립 검증에서 cold equal-scale 3명 단체 중앙을 메인으로 만드는 반례도 발견했다. 현재 초안은 기존 메인 anchor + 원래 group episode 전체 검증을 요구하며 이름 투표로 역할을 만들지 않는다.
- whole-only 저장 결과 투영은 409→405 / short226→222이나 unknown +0.233567초. 실제 앱 재실행 결과가 아니며 아직 채택 완료하지 않았다. NEON48 연속 파트 재현 test는 여전히 RED.
- NEON53 원본에서 동일 전신 중복이 얼굴 소유권과 strict temporal uniqueness를 동시에 막는 것을 확인했다. 얼굴3점·몸통4점·다리 관측이 함께 일치하는 원본 대표만 유지하고 raw index/관측을 audit에 보존하는 Dance 전용 pose_observations.py 초안 추가. 메인 판정 전 적용하여 이후 모든 단계가 동일 관측을 사용한다.
- 현재 추가 leg guard 포함 전체 저장 자료 scan: MMN13 / ANT29 / NEON110 프레임 정규화, 순수 계산 각각0.119/0.182/0.343초. 앞선 torso-only 후보 inventory와 수가 다름. 정확한 이름/클립 개선량으로 해석하지 않는다.
- tests/test_dance*.py: 1163 passed, 1 failed (NEON48 원인 재현). 중복 관측 테스트9개 통과. 빌드/실앱 3영상 실행은 아직 시작 전.
- Astra 독립 검토 및 기존 진단 agent의 NEON48 supported-continuation 탐색 진행 중. 제품 수정은 root만.
- scratch 근거: /private/tmp/dance-role-continuity-20261103/; 별도 리뷰 /private/tmp/dance-role-continuity-20261103-review/.

## 미채택과 적용 분리

2026-11-03 추가 검토: 역할유지 초안은 NEON48 실패를 해결하지 못하고 전수 whole-part 추가 효과0인 보완규칙만 남았다. 해당 초안/실패 test/fixture를 /private/tmp/dance-role-continuity-20261103/unadopted-role-retention/에 보존하고 role_state.py를 이번 turn 시작 snapshot으로 복원했다. 실패를 통과로 바꾼 것이 아니며 NEON48 미해결이다. 앱에 미사용 초안을 넣지 않는다.

현재 채택 후보는 canonical full-body observations 하나. Astra가 발견한 약한귀 분모확장, 잘못된legs, 비추이적 A~B~C, 실제 MMN1724 두사람 hybrid, 외부사람 반대쪽 관절 결측의5유형을 각각 RED→GREEN 회귀로 보완했다. 특히 hybrid의 경우 독립 머리와 같은쪽 knee+ankle 관측만으로도 소유권 충돌을 보류하며 반대쪽 결손을 무시하지 않는다. 모순있는 component가있으면 프레임 전체를 보존해 원본 witness가 다른 병합으로 사라지지 않게 했다. audit.deferred에 원본 후보, 외부 주인, 관절, 거리와 이유를 저장한다.

안무1163 tests passed(9.14초; 이후 singleton 조기종료만 추가). 현재 기존 파일 변경은 Dance pipeline.py/face_evidence.py뿐이며 신설 pose_observations.py와 테스트/fixture가 추가된다. Person/공유/SDK 시작 manifest 변동0. heavy mask/joint-body 단계 계속 비활성. 실제 앱 비교는 아직전이며 runtime/quality 개선을 주장하지 않는다.

## 실제 앱 검증과 별도 출력 정책

Canonical-only 원본 앱 빌드가 성공했고 원본 저장소 Electron에서 새로 실행했다. 같은 URL·대표 이미지로 새 프로젝트 MMN1793645653627, ANT1793645767403, NEON1793645871567을 실행한다. 앞선 두 영상은 완료: MMN314.119초/88개/1초미만41개(출력 동일), ANT435.051초/125개/71개(이전126/72). ANT 미확인0.667533초 감소와 두 경계 이동은 정확성 독립검증 전이며 단순 감소를 정답으로 간주하지 않는다. NEON은 기록 시점 진행 중이다.

별도 신규 정책: 같은 원본 source_ranges 표현에서 단일 기존 matched 멤버 main이 group의 전체 실제 범위를 포함하고, 다른 matched 멤버와 부분 중첩도 없는 경우에만 group 출력 카드를 생략한다. 여러 main 합집합/부분 포함/unknown/수동 배정 group/다른 표현은 보존한다. 길이 제한이 아니다. 원본 group 세그먼트·판정·recipients·진단·통계는 그대로, 마지막 meta_builder에 전달할 출력 목록만 투영한다. audit에 original group ID와 covering main ID/범위를 저장하고 ID를 재번호화하지 않는다. main 자체와 unknown은 불변이다. 이 정책은 올바른 main 선택/신원 복원 성과가 아니며 원래 품질평가와 별도 집계한다.

TDD: helper 부재18 RED→18 GREEN. 실제 pipeline 진단/출력 분리 테스트와 기존 이미지/source_ranges 테스트 합37 passed. edge float 3.000000000000001을3.0으로 임의 허용하지 않으며, 통합fixture의 명백한 포함 구간3.1–4.0으로 검증한다. NEON48 역할 복원 초안은 앞선 실제 foreground anchor가 없고 중앙가중에 의존해 여전히 미채택. 원경 단체 유지 실험 및 사용자확인 MMN37.738–39.339 미확인 원인을 별도 독립 에이전트가 조사한다. 현재 benchmark 중 모델/decode/replay 부하는 보류한다.

## Canonical-only 앱 결과 및 채택 차단

세 실제 앱 실행 완료: MMN314.119초, ANT435.051초, NEON492.170초. 이전 합1207.958초→1241.340초(+33.382초), main/face/IO 여러 단계가 변동해 원인을 새 정규화 비용으로 단정하지 않는다(정규화 자체 합0.885초). 출력409→408, 1초미만226→224, unknown38.1416→37.874567초. 기존 사용자14구간의 출력은 모두 같아 해당 사례 개선0. 독립 검증에서 source/config/setup/대표사진bytes동일, 의미상같은394행 썸네일bytes동일, heavy SAM/mask/joint-body 모델·시간0 확인했다.

**현재 이 빌드를 최종 채택하지 않는다.** 독립 검증이 NEON42.609233–42.6426의 실제 이름 관측 전 padding만으로 생긴 0.033초 멤버 조각, ANT154.687867–154.821333의 실제 다른 몸을 지나친 이름 산술중점 경계 문제를 찾았다. 정규화의 국소 관측 개선만으로 최종 결과 정확성을 보장할 수 없다.

후속 수정은 원본 관측/이름/출력을 분리한 다음 계약으로 좁힌다.

- identity_projection: 부모 consensus 자체를 이름 근거로 쓰지 않는다. 최종 part가 원래 얼굴 관측 밖 padding으로만 남으면, 직접 primary 또는 원래 accepted joint의 같은 이름 anchor까지 선택몸의 reciprocal pose 경로를 검증한다. 실제 cut/누락/다른몸/경로내다른긍정이름/명시적 joint conflict는 보류한다. 관측이 있는 진짜 짧은 클립은 길이로 제거하지 않는다. 16개 전용테스트 및 Astra 독립반례 검증 통과. 실제 frozen projection은 NEON42/93 두 조각만 거부, MMN/ANT 변경0. 실제 앱 통합 결과는 아직 전이다.
- group_continuity: 세 개의 독립 원본 몸 경로와 gap 사이 모든 source frame의 cut 검사를 통해 group 출력만 연결. main/identity는 불변이며 최종 인물 조립 이후 수행한다. 원래6gap은 source134frames/API약0.59초로 검증했으나 partial shared-head 반례를 더 강하게 막는 중이다. 원본 머리관측이 부족한 ANT134를 보류해5gap이 될 수 있으며 최종 수치 재검증이 필요하다.
- bounded_face_path: 기존 body/cut/name 검증 모두 통과한 뒤 isolated_visual_change에만 원래 얼굴 픽셀의 최대5 source frame 창을 앞/뒤 독립 왕복 검증한다. 모든 높은차이 edge를 덮어야하며,타인/삽입/가림/실제cut은 기존 실패 유지. MMN38의7창/35추가프레임,약1.308초로 1.134567초 사쿠라 복원 및35.4354–42.976267 한 파트를 저장자료 재생으로 확인. ANT/NEON의31개 body후보 중 다른 판정변경0. 새모델/SAM은 없고,OpenCV오류/Noneflow는보류한다. 관련48tests와Astra독립24tests 통과. 최종 앱 검증은 별도 진행한다.
- group_output: 원래 main/name/범위와 원래group진단을 보존하는 완전포함 중복출력 생략. canonical-only frozen metadata 투영408→381/short224→201, sourcecoverageunion동일. 이는27개group출력중복제거이지정답복원27개가 아니다. 후속group연결/face복원과 합친 최종 수치가 아니다.

ANT154는 incoming 이름의 원래 반복 joint와 원래 선택몸 경로로 첫 관측된 incoming 몸까지 경계를 당기는 별도 좁은 수정을 검토 중이다. 실제 body교대 bracket154.621133–154.687867, 원래 incoming카즈하 support9308/9320 간격0.2002초. photo matcher미확정과반대이름긍정은구분한다. 이 수정이검증되기전canonical최종채택보류.

전체 검사 기록: 최초 full pytest2735passed/4skip/10fail/17error. 로컬 socket제한 관련 테스트만 권한있는 환경에서 다시 실행해23passed/2skip. 남는6개는 이번변경밖의 renderer golden5개와fadeblack1개다. 전체 통과로 보고하지 않는다. 이후 출력정책 포함 Dance1182passed, 신규후속모듈은전용검사중이며최종Dance전체를한번더확인한다.

## 통합본 동결 및 실제 앱 재검증 시작

모든 후속 모듈의 독립 검토를 통과한 통합본으로 최종 Dance 회귀검사1306 passed(45.87초), git diff --check를 확인했다. group_continuity는 독립 머리 근거가 부족한 ANT134를 보류하여 최종5연결/105sourceframes이다. incoming_identity_boundary는 실제 ANT154 경계를154.821333→154.687867초로 앞당기고 남는김채원 파트와 들어오는카즈하 파트를 각각 원래 얼굴/몸 관측으로 확인한다. bounded_face_path는 양끝 얼굴 사전검사로 불필요한 디코딩을 막고, shot_member_gaps는 추가 얼굴재읽기까지 기존240actualread 한도에 포함한다. 이 제한은전체실행시간상한이아니며,무거운SAM은계속OFF다.

원본Electron에서 npm run build:app:mac:arm64:local-api 성공. 패키지64개DancePython모듈SHA가동결source와전부일치한다. 같은계정/같은3YouTubeURL/같은대표이미지로 새프로젝트를실행중이며, 최종실앱수치와남은문제는완료후별도기록한다. 동결 manifest와실행자료: /private/tmp/dance-role-continuity-20261103/app-final/. 기존canonical-only결과와혼동하지않는다. 벤치마크중추가모델/테스트/소스디코딩중지.

## 통합 앱 반복 검증 결과

새 프로젝트 MMN1793649506337, ANT1793649573540, NEON1793649654322 모두 완료했다. 같은URL·설정·사진바이트·원본영상SHA를 확인했다. 실제분류409→400개/1초미만226→216개,단체26개중복표시를생략한최종374개/1초미만195개다. 미확인38.141600→36.806633초. MMN사쿠라35.435400–42.976267이하나로이어졌고사용자14검토구간중해당1개가개선됐다. 나머지13개지표는동일하며기존미해결도포함한다. 실행시간합계1207.958→1326.930초로늘었다. 외부원격화면프로세스의높은CPU부하를기록했으나시간차이원인을확정하지않는다.

독립Astra최종검토에서신규후속보정의예상밖변화는발견하지못했으나NEON43.777067–44.110733메인역할주의점은미해결이다. 전체품질퇴행없음이나전체문제해결을선언하지않는다. 추가torso픽셀검증은효과상한두후보1.067933초여서미구현. 주요후속은group조건탈락을main양성으로쓰는경로,역할구간과이름구간의projection,준비맥락과실제main범위의분리다. 독립설계제안은구현성과와구분한다.

이번반복의상세결과는[03-role-continuity-app-results.md](03-role-continuity-app-results.md),영구근거는03-role-continuity-evidence/에저장했다. 원본저장소빌드앱은실행된상태이고최신3프로젝트완료를화면에서도확인했다. 커밋·푸시·병합은하지않았다.
