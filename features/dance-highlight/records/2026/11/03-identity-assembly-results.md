# 이름·메인 구간 교차의 중복 경계 수정

2026-11-03. 사용자 요청에 따라 **단체 조건 탈락→개인 메인 판정은 변경하지 않았다.** 이번 변경은 안무의 최종 구간 조립과 잘린 이름 근거 검증에 한정한다. 원본 Python `fix/dance-gpu-performance-20261102`, HEAD `4b54bced17e13aadbeb97be75259b7f7213a9b24`; 기존 미커밋 작업 위 변경이며 커밋·푸시·병합·앱 재빌드는 하지 않았다.

## 수정한 동작

1. 얼굴 신원 변경은 두 관측의 중간 시각, 메인 교대/단체 전환은 첫 새 관측 시각을 쓰면서 하나의 사건이 두 경계가 되는 구조를 수정했다. `part_boundary_events.coalesce_boundary_events`는 정확히 같은 원본 관측 쌍의 중복 경계만 최종 조립한다. 이름·메인 관측 자체를 retime하지 않는다. 모든 기존 복원·경계 보정 후, preparation 전에 실행하므로 새 출력 경계가 앞 단계의 인식 근거가 되지 않는다.
2. 내부 관측이 없는 unknown 조각만 대상이다. source cut, 정밀 frame 경계, main eligibility 구멍, 실제 이름 있는 짧은 B, 다른 교대 bracket, 누락된 근거는 유지한다. unknown→unknown이면 이름을 새로 부여하지 않는다. 이름 구간을 늘릴 때는 마지막 원래 얼굴의 joint 채택, 시간 간격을 둔 지지 얼굴, 원래 갤러리의 반대 양성 없음, 선택 몸의 원래 관측 연속성을 모두 확인한다. 모델 추론·영상 읽기는 추가하지 않았다.
3. 잘린 조각의 모든 유효 얼굴이 다른 이름으로 독립 채택됐는데, 제외된 앞 구간의 부모 이름을 물려받는 오류도 차단했다. 해당 조각은 unknown으로 유지하며 한 프레임으로 다른 멤버를 추측하지 않는다. 거부한 부모 이름의 출력 tuple/fallback vote도 제거해 후속 얼굴 복원이 같은 이름을 되살리지 못하게 했다. 원래 identity, FaceObservation, embedding과 다른 독립 이름은 보존한다.

## 세 영상 저장 결과 비교

**실제 앱을 새로 실행한 측정이 아니다.** 직전 실제 앱의 JSON·보관 embedding·메인 관측을 동결한 뒤 새 순수 조립 함수와 projection guard를 실행한 비교다. 전체 앱 속도 개선이나 전체 파이프라인 E2E 동등성을 주장하지 않는다. 기존 앱 결과 파일은 수정하지 않았고 비교본은 별도 scratch에만 저장했다.

| 영상 / 기준 프로젝트 | 표시 전체 클립 | 표시 1초 미만 | 미확인 시간 |
|---|---:|---:|---:|
| Made My Night / 1793649506337 | 68 → 67 | 27 → 26 | 5.672633 → 5.639267초 |
| ANTIFRAGILE / 1793649573540 | 116 → 116 | 60 → 60 | 14.349067 → 14.349067초 |
| NEON / 1793649654322 | 190 → 187 | 108 → 105 | 16.784933 → 16.785033초 |
| 합계 | **374 → 370** | **195 → 191** | **36.806633 → 36.773367초** |

표는 기존 단체 중복 카드 제거가 적용된 표시 목록 기준이다. 원시 main+group 기준은400→396, short216→212이다. 네 개 감소는 전부 중복 경계에 의해 생성된 unknown 조각의 병합이다. 이름 있는 초단편을 대량 복원한 결과가 아니다. 이름 있는 short는64→63, unknown short는80→77이며 추가 이름 거부1개가 포함된다.

- MMN88.254833–88.288200: 김채원 끝을 기존 first-observed-new-main 경계에 맞춤. unknown 0.033367초를 김채원 출력에 포함한다. 새 얼굴 인식 성공이 아니라 기존 경계 정책의 정렬이다.
- NEON42.609233–42.642600 및221.854967–221.888333: 앞 unknown에 합침. 이름/미확인 시간 불변. group 시작과 이후 incoming 관측은 그대로다.
- NEON189.956433–189.989800: 메르시 끝을 첫 제외 관측에 맞춤. unknown 0.033367초를 기존 메르시 출력에 포함한다.
- NEON34.334300–34.367667: 마지막 outgoing 얼굴이 conflict여서 시리 연장 거부.
- NEON187.720867–187.754333: 부모 영의 지지는 제외된 group에 있고, 내부 f11252는 아이찡 joint accepted다. 영을 계승하지 않고0.033467초를 unknown으로 유지한다. 새 아이찡 확정이 아니다.

관측 사이의 실제 정확한 교대 프레임을 새로 검출한 것이 아니다. audit에 원래 두 관측의 uncertainty bracket, 출력 경계, named/unknown 시간 변화와 근거를 기록한다. 14개 기존 사용자 확인 구간의 집계는 모두 그대로이고, main 시간 합집합·group 목록·관측 frame 순서도 불변이다. 남아 있던 사용자 정답 실패를 통과로 재분류하지 않았다.

순수 canonical 조립은 영상당 약2–17ms, projection guard 전체는 약3–13ms였다. 저장 자료 로드/재구성은 별도이며 모델 추론·영상 decode 추가0이다. 앱 전체 started→completed 시간은 이번에 측정하지 않았다.

## 검증과 독립 검토

- TDD: 새 helper 미구현/통합 누락/부모 이름 누수/후속 복원 재발/반대 primary 무시를 실제 함수의 실패로 재현한 뒤 수정.
- 실제 앱 원본5개 경계 fixture와 NEON187 반대 이름 fixture. 원본 JSON SHA와 추출 범위 보존. 테스트 matcher의 primary 결과는 보관 원본 gallery/embedding으로 계산했고, 세 영상 replay에서는 실제 `ReferenceObservationMatcher`를 사용한다.
- Dance 테스트 최종 **1,339 통과**,14.99초. `git diff --check` 통과. 전체 Python suite는 이번에 실행하지 않았다.
- 독립 Astra가 발견한 후속 복원 재발과 반대 primary 반례를 보강했다. 최종 독립 재검토 기록은 evidence 폴더에 함께 보존한다.
- Person/Dialog/shared face·speech·SDK 수정 없음. 상류 scene/group/main role 파일과 heavy SAM OFF 경로는 이번 턴 시작 SHA와 동일하다. GPU 설정·의존성도 이번 턴에 변경하지 않았다.

## 아직 해결되지 않은 부분

전체 main short144개 중 교집합에서 짧아진 것은55개(named26/unknown29)다. named26개 가운데 원래 이름 span이1초 이상인 것은16개이다. 그러나 동일 이름의 인접 출력 경계는 이미0개다. 23개의 같은 이름 parent 분할에는 고정 eligibility 밖의 실제 시간 구멍이 있다. 이런 구간은 지금 요청대로 역할 영역을 동결하면 무조건 연결할 수 없다.

MMN50.650600–50.683967의2프레임 김채원은 그대로 남는다. 마지막얼굴의 존재와 이름 독립 채택은 다르며, 다음 허윤진 근거는 컷 뒤에 있다. 동일 사건 경계로 합칠 근거가 없어 이번 규칙에 넣지 않았다. 원래 얼굴 변화 창이 카메라 컷을 가로질러 다른 샷의 관측을 경계 결정에 섞는 문제는 별도 후속 후보다. 단체→main 정책을 바꾸거나 반대 이름 구간을 지우는 임의 해결을 하지 않는다.

**초단편 전체 문제는 미해결이다.** 이번 성과는 중복 경계4곳과 명확한 부모 이름 누수1곳의 제한적인 수정이다. 다음 검증은 원래 얼굴 경계 후보를 만들 때 shot/cut별 지지 범위를 분리하는 방향이며, source frame과 기존 교대 정답으로 검증한 뒤 적용해야 한다. 새 앱 전체 실행·빌드 결과는 아직 없다.

## 증거

- [설계/계획](03-identity-assembly-plan.md)
- [세 영상 비교](03-identity-assembly-evidence/replay-results.json), [14개 사용자 구간](03-identity-assembly-evidence/reviewed-14.json), [재현 코드](03-identity-assembly-evidence/replay.py)
- [원인 전수 분석](03-identity-assembly-evidence/fragmentation-report.md), [독립 최소 계약](03-identity-assembly-evidence/independent-minimum-contract.txt)
- [최종 테스트](03-identity-assembly-evidence/dance-tests-final.log), [이번 턴 변경 diff](03-identity-assembly-evidence/turn.diff)
- [GPU·ONNX 별도 세션 조사](../../../../../operations/accelerators/records/2026/11/03-windows-onnx-trial-and-highlight-gpu-review.md). 사용자 첨부 키트의 후속 분석 결과와 초기 부분 로그 해석을 구별해야 한다.
