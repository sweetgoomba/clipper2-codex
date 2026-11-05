# 동일 멤버 파트의 구도·컷 연속성 개선 — 진행 기록
> 이 진행 기록은 [최종 실제 앱 검증](03-shot-context-quality-results.md)으로 대체됐다. 아래 내용은 진행 당시 상태이며 최종 판정은 연결 문서를 기준으로 한다.


2026-11-03 KST. 사용자 `남은거 계속 진행해줘. 계속 개선해줘`의 후속 작업이다. 이전 최종 결과는 [멤버 구간 실제 앱 검증](03-member-part-quality-results.md). 이 문서는 아직 새 앱 실행 완료 보고가 아니다.

## 기준과 범위

기준 실제 앱 프로젝트: MMN1793633624877 / ANT1793633679903 / NEON1793633791815. 전체414 / 1초 미만230 / 미확인38.608933초. 짧은 항목은 named71·unknown80·group79이며 group22개는 이미 같은 named main과 완전히 겹친다. 총량만 줄이기 위해 삭제하지 않는다. 원본Python fix/dance-gpu-performance-20261102 (4b54bced17e13aadbeb97be75259b7f7213a9b24)의 미커밋 변경을 이어간다. Person/shared/SDK 변경, SAM 재활성화, min/max 클립 길이 강제, commit/push/merge는 하지 않는다.

## 현재 채택 후보

- scene_context bounded 경로에 실제 앞쪽 인물 근거를 추가했다. 원래 확인된 얼굴 이름 양쪽과 엄격한 몸 대응·경쟁자·컷·유효 scene·근거 만료 조건을 유지한다. 정확히 화면중앙선을 몸통이 덮어야 한다는 조건의 대안으로, 원래 role의 fresh detected face+얼굴/몸통 동시 우위+얼굴 없는 중앙 경쟁자 veto+.15초 독립 관측을 요구한다. 새로운 이름을 얼굴 갤러리로 올리지 않는다.
- 기록 전수에서 NEON98.2982–98.531767의4관측만 추가 main. MMN/ANT 변화0. 현재16개 신규 검사 포함 관련89개 통과; 독립 Astra 전수17조건 및 기존 helper8696관측 동등성 확인. 원래 단체 run 모든 관측이 위의 강한 전경 증명을 갖춘 경우만 별도 group export를 해제한다. 기존 중앙/context 경로의 이중 자격은 유지한다. 이 마지막 group-export 조건은 독립 재검토 중이다.
- 실제 각도 컷 ANT64.430933–64.898267은 shot별 새 후보를 조사 중이다. 같은 이름인 양쪽을 후보로만 삼고, cut 이후 새 미확인 시간은 그 shot의 원래 직접 얼굴로 증명하며 컷을 가로질러 몸/track identity를 전달하지 않는다. 현재 scratch 후보0.467333초이지 앱 개선 확정치가 아니다.

## 적용하지 않은 시도

- source foreground patch+gradient 재시도: 실제 ANT589/590만 통과하고591 및MMN은 blur/변형으로 양성 근거가 부족했다. 실제 다른 인물·동일색 옷·noise/mirror16변형/32전환과 실제handoff38검사를 거절했으나 전체복원0초. 제품 미적용.
- 원경 partial torso를 원래 전신 양쪽의 유일 대응으로 참여자로 세는 제안: 저장975 native frames/2863몸 중 NEON156.5564–156.689867 한 곳만 후보. group2→1, unknown/이름0변화, 추가2.513초. torso-only 소유와 관측 사이 전경 보호에 한계가 있어 독립 검토 전 제품에 넣지 않았다.
- ANT174의 두 관측은 얼굴과 몸통 규모의 동시 우위를 입증하지 못했고 MMN104도 단순히 같은 이름이 계속 보인다는 것뿐이라 엄격 경로에서는 보류했다. 임의 중앙 허용폭 변경도 전수 재생에서 추가효과0이며 미적용.

## 구조적 해석

기존 전체 파이프라인이 camera cut을 모두 main 경계로 취급하는 것은 아니다. 이미 이름이 확정된 인접 output은 원래 얼굴 합의로 합친다. 문제는 얼굴 공백 복구에서 `_check_source_chain`의 전역 색/luma 검사를 충분조건으로 사용하며, 줌/조명을 거절하고 다른 앵글의 shot별 identity/role을 별도 증명하지 못하는 부분이다. 배경 optical flow나 보간 pose만으로 이 조건을 우회하면 전경을 관측하지 않은 허점이 생긴다. 이전noise/mirror 한 프레임 반례는 이 허점을 입증한 것이지 실제 다른 멤버로 교대했다는 정답은 아니다. .15초 지지 기준을 짧은 실제 삽입 컷 삭제의 근거로 쓰지 않는다.

## 검증과 다음 작업

전체 Python 현재2650passed /6skipped /기존 무관한 실패6개(자막golden5,fadeblack1),166.61초. 이 실행 뒤 group export 국소 변경은 관련64검사로 재확인했고 최종 Dance 검사를 다시 할 예정이다. 실제 앱 빌드와 같은3YouTube 실행, 얼굴/pose/참조/설정/썸네일·구간 대조는 아직 남았다.

독립 Astra 스레드01a19bab-62d3-7c52-8538-54703f0fc96a. 작업scratch `/private/tmp/dance-continuity-next-20261103`, 독립검토 `/private/tmp/dance-episode-review-20261103`, source픽셀시도 `/private/tmp/dance-foreground-proof-20261103`, partial참여자 `/private/tmp/dance-partial-presence-20261103`, shot후보 `/private/tmp/dance-shot-gap-20261103`. 최종 보고 때 핵심증거를 이 문서 저장소에 지속보존한다.
