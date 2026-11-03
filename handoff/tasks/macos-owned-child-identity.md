# W20 macOS 보조 프로세스 종료 소유권 오인

2026-11-03 사용자 요청: W19에서 별도 이관, **새 세션에서 원인 분석·해결**. 프로모션/배지 변경과 별개이며100원 최소 청구 문제도 아니다.

[재현·원인·제약·증거 정본](../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-investigation-handoff.md).

대상: desktop/clipper_nestjs의 OwnedChildProcessRegistry. 동일 프로세스의 macOS 시작 메타데이터가 사라지며 `ps eww` 전체 해시가 바뀌어 종료를 거절한다. 원격 dev에도 존재하고 단독 재현됐다. W19 소스·실행 환경을 건드리지 않고 최신 dev의 별도 브랜치/격리 공간에서 해결한다.

단순 검사 제거/fixture 대기로 숨김 금지. 출생·owner/PID 재사용 보호와 TERM→KILL·자식 트리 처리를 유지하며 최소 수정·회귀·문서화한다. 별도 요청 없는 원격 통합은 하지 않는다. 새 세션 생성 후 식별자를 이 카드에 추가한다.

새 세션: **macOS 보조 프로세스 종료 오류 수정** / `01a19dcf-acaf-7371-9d72-58b3fce5f985` / host local. 사용자 요청에 따라 생성·초기 작업 전달 완료. W19에서 이 제품 코드는 수정하지 않는다.

2026-11-03 로컬 수정·검증 완료. `fix/macos-owned-child-identity-20261103` 격리 브랜치에서 `ps eww`는 owner token 확인에만 쓰고 환경 제외 시작 시각·명령을 identity로 해시한다. 두 조회의 앞부분 불일치는 거절한다. 대상10/10, 실제 child tree 10회 반복, 전체5,283통과/8건너뜀/0실패, 빌드·diff 검사 통과. Windows 실기는 미검증. **미커밋·미푸시·미병합·미배포.** [원인·수정·검증 상세](../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-fix-result.md).

최신 원격 `dev` `f2cc17a9` 병합 전 점검: W20 파일 충돌 없음. 일회용 합성본 빌드·전체5,287/5,295 통과(8건너뜀·0실패). 집중 실행의 fixture 초기 저장 실패 1회는 이어진 20회 반복과 전체 실행에서 재현되지 않았으며 원인 미확정. 실제 병합과 커밋은 하지 않았다. [점검 상세](../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-fix-result.md#최신-원격-dev-병합-전-점검).

**현재 상태 — 사용자 승인으로 원격 dev 병합 완료:** 코드 `5708ee5e`, dev 병합 `c8b71e7f`. 최신 dev에서 충돌 없이 병합하고 실제 병합 커밋의 빌드·전체5,289통과/8skip/0실패(총5,297)를 확인해 원격 dev에 푸시했다. Sol/xhigh [독립 검증](../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-independent-sol-xhigh-01a19fb6.md)을 반영해 1초 polling을 순차 ps callback fixture와 실제 identityReady 대기로 교체했고 snapshot 불일치·초기 조회 실패의 무신호 보존을 검증했다. 최초 자연 실패 원인과 Windows 실기는 여전히 미확정/미검증이며 앱 배포는 하지 않았다. [커밋·병합 상세](../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-fix-result.md#사용자-승인-커밋원격-dev-병합-완료).
