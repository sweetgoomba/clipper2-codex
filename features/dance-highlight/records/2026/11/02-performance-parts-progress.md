# 실행 기록 — 02-performance-parts-plan

- 기준 source snapshot 166파일 보존. 커밋/푸시/기존 dirty 제거 없음.
- 단계 1: performance_parts.py 추가, pipeline 최종 조립 블록 추출. 원본 identity scopes/얼굴 증거를 변경하지 않고 projection·재매핑·검증된 병합·이름 경계교정을 실행한다. 입력 scopes와 출력 parts 출처/새 이름 시간 기록. preparation 별도 유지.
- RED: 신규 계약 테스트 6개 ModuleNotFound 실패 확인. GREEN: 6통과, 관련 통합 191통과(2.94초).
- 단계 2 실험: distant formation의 가로 퍼짐 제약 삭제만으로는 ANT4.57–6.14 사용자 확인 main이 group이 되는 회귀. 그 안은 거절.
- 보완: 새 compact group 후보만, 전체 관측에서 지속되는 중앙 torso가 있는 경우 보호한다. 중앙 구도는 main/이름의 증명으로 사용하지 않고 새로운 group 제외의 veto로만 사용. 이 증명은 group 후보와 독립적으로 계산해 발목 관측 누락으로 잘리지 않게 했다.
- RED: 사용자 Hong 실사 fixture와 중앙구도/pose-dropout 두 회귀 실패 확인. GREEN: scene eligibility/context/native 관련133통과(1.64초).
- 현재 cached whole3 classification 변화: MMN4프레임/1구간0.2669초, ANT11프레임/2구간0.7341초, NEON23프레임/3구간1.5349초. 원본 contact sheet 확인, Astra 독립 검토 요청. 아직 실제 앱 품질/시간 개선으로 주장하지 않는다.
- uv는 sandbox 캐시 접근 실패. 설치된 동일 .venv/bin/python -m pytest로 검사했다.
- 진행 중: MMN 빠른 줌, ANT 조명 전환에서 source-cut 거절이 부당한지 source-pair 검증 및 메인 역할 증거 검토. 실제 컷/반대 얼굴/원경 경쟁을 blanket 완화하지 않는다.

## 독립 검토 후 수정 — 실행 계속 중

- Astra가 추가 반례 두 개를 재현했다. (1) 새 compact 양끝에서 짧은 공백을 메울 때 중앙 torso 보호가 사라져 group이 됨. (2) 보호 규칙을 기존 base-group과 compact가 겹치는 양끝에도 적용해 기존 group이 main으로 변함.
- 두 반례를 제품 테스트에서 RED 확인하고 수정했다. protected_central을 공백 처리까지 유지하고 compact는 `added and not base`인 신규 근거만 사용한다. 최종 Dance 990개 통과(7.54초). cached whole3의 6개 변화 범위는 같다.
- 6개 범위의 합계 2.5359초는 분류 후보의 변화이며 최종 품질 개선 시간이 아니다. NEON 229.229–229.762867은 기존에도 최종 group이며 main 출력이 없다. 실제 main 출력과 교차하는 후보 시간은 2.002초다. 이름 복원에 의한 개선은 아니다.
- 전체 검사 직전판: 2580통과, 6skip, 기존 render golden 6실패. 마지막 신규근거 구분 수정은 Dance990통과하고 전체 재검사 중이다.
- 최종 build 성공, 패키지55 Python 소스 해시 일치. UI의 종료 확인을 완료하고 새 프로세스로 시작했다. 실제 같은3영상 실행은 아직 시작 전이다. 시간 측정과 무거운 테스트를 동시에 실행하지 않는다.

## 실제 앱 1차 실패와 보완 — 아직 최종 앱 재검증 전

- 실제 원본 빌드3 URL 실행 완료: MMN1793625050124 / ANT1793625132795 / NEON1793625224514. 기준 동일 URL·대표이미지 선택/bytes·임베딩·원본SHA·config 보존. 사용자14사례 보존. 얼굴 원본관측/pose측정 보존, SAM2개단계0초.
- 시간(대기열 제외): 295.082→320.610 / 397.721→470.742 / 439.264→458.606초. 합계1132.067→1249.958초(+10.41%). 각1회, 변경하지 않은 검출/얼굴 단계도 느려져 원인을 compact 계산으로 단정하지 않지만 성능 개선으로 주장하지 않는다.
- 품질 회귀 확인: 총429→430클립, 1초미만245→247. MMN3·4프레임, NEON4프레임 unknown 잔여. 미확인1.468초 감소만으로 성공 판정하지 않고 이 버전 채택을 보류했다. 첫 실행 자료는 /private/tmp/dance-part-timeline-20261102/app에 보존.
- 새 compact는 기존 debounce 완료된 strict group run과 관측상 이어질 때만 확장하도록 제한. 독립 group 섬 생성 보류. 누락 샘플/중앙 역할/기존 group 보존 반례 유지. 이 제한만으로는 NEON4프레임 잔여가 남아 추가 보완 필요함을 Astra가 지적.
- 실제 원본 MMN2989는 컷이지만 gray0.79435가 기존0.8screen에 못 미침. 특정 사례에 맞춘 임계값 변경이나 미확인 조각 삭제는 하지 않았다. MMN compact 후보는 보류.
- NEON8612는 연속 원경 군무. 일반 detector에는 실제 한 몸이 없어 보였으나, 기존 native8608 관측에 이미 존재함을 Astra가 확인. 여러 과거 프레임의 raw bbox를 모으는 초안은 폐기. stage art bbox를 실제 전경 인물의 anchor로 재사용하는 반례와 pose누락 반례를 RED→GREEN으로 추가.
- 현재 보완은 immediate native8608/compact8616 단일양끝에서, 기존 reliable head/torso 계약의 실제관측몸 2개가 유일하게 대응할 때만 연결한다. 컷·handoff·camera episode·중앙 몸·큰 전경/잘린 몸·배열누락/손상은 보류. 추가 모델/SAM추론 없음. 세 영상 저장 native+regular 관측 재생은 MMN변화0, ANT146.613133–146.880067, NEON143.676867–144.077267 두 범위만 변화, 기존group역전0. bridge 순수계산0.0003–0.0009초. 아직 실제 앱 결과가 아님.
- 현재 코드의 native anchor가 partial 측정까지 신뢰하지 않는지 독립 최종 검토 중. 최종 코드 전체검사·재빌드·세 URL 실제 재실행이 남았다. /private/tmp/dance-part-timeline-20261102/app-final은 다음 실행 기록용이며 아직 job등록 전.

## 최종 소스 확정과 실제 앱 2차 검증 시작

- native anchor는 정확한 같은 프레임, 저장된 group bbox와 정확한 동일 좌표, 원본 native 관절에서 `full`인 몸만 채택한다. 다른 프레임·좌표 불일치·누락·partial은 보류하며 raw bbox로 대체하지 않는다.
- Astra 최종 독립 검토: 실제 양성1+음성23 통과, 기존 reliable-body predicate는9266관측에서 변경0. 최종 저장자료 재생은 앞서 기록한 ANT/NEON 두 범위 합계0.667333초뿐이다. 최종 보고서9절: `02-role-continuity-and-compact-review.md`.
- 제품 Dance1010통과(7.67초). 전체2601통과,6skip, 기존 무관한 renderer golden6실패(196.11초). `git diff --check` 통과.
- 원본 Electron의 지정 npm빌드 성공. 최종 패키지의 Dance55소스SHA 일치. 이번 변경은기존4파일+신규5파일이며 Person/shared/SDK변경없음. 최종source/격리/패키지증거는 scratch의 final4-*.
- 1차실패 앱 정상종료 후 최종 빌드 실행. 2026-11-02T14:01:08Z부터 MMN1793628067111 실제 UI YouTube 실행 시작, 다른2영상 등록중. 앱측정중 무거운테스트/빌드/추가ML동시실행없음. 최종실행 자료는 app-final에 별도보관하며 1차실패 app 자료를 덮어쓰지않는다.

## 최종 앱 실행 완료

- MMN1793628067111 / ANT1793628143826 / NEON1793628225716 모두 완료. 실제 UI 최신 완료 카드도 확인. 세 영상 302.607 / 421.038 / 464.295초, 합계1187.940초(+4.94%).
- 최종 짧은 클립은 예상 집계241보다 한 개 더 줄어 **240개**다. NEON에서 양쪽 group 두 개가 하나로 합쳐져 추가로 한 개 감소한 정상 결과다. 예상 두 범위 밖 분류 변화는 없다. 전체429→424, 미확인39.5767→38.9761초. 이름 있는 짧은 멤버73개는 그대로다.
- 사용자14구간 보존, 동일 구간421썸네일 일치. 원본 얼굴/pose측정/reference/영상/config 동일, native135/299/541프레임과 관측 동일. SAM 두 단계 모두0초. 새 group_context 연결은0.000468/0.000521/0.001545초.
- [최종 결과](02-performance-parts-results.md)에 실패한 첫 실험, 변경 제한, 남은 핵심 과제까지 정리. 최종증거는02-performance-parts-evidence에 복사했다. 소스는 최종 빌드 이후 변화 없으며 커밋·푸시·병합 없음.

- 최종 독립 감사 후속 예외: NEON229.229–229.696초 8관측의 group_bodies 표시가 native→compact 출처 변경으로 달라진다. 출력 분류·구간·썸네일과 raw 몸/얼굴 측정은 동일하다. 진단 viewer 전체 동일이라고 표현하지 않도록 최종 보고서에 명시하고 전용 감사 JSON을 보존했다.
