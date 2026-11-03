# macOS owned child identity 수정 계획

> 실행: 이 세션에서 직접 구현. 사용자 요청에 따라 커밋·푸시·원격 dev 병합은 하지 않는다.

**목표:** 시작 직후 macOS `ps eww`의 일시적 환경 필드가 사라져도 같은 owned child를 종료하고, PID 재사용·owner/출생/명령 변경은 계속 거절한다.

**근거:** [W20 인계](03-macos-owned-child-identity-investigation-handoff.md). 최신 원격 dev `7f57ff1b`, 격리 브랜치 `fix/macos-owned-child-identity-20261103`.

**변경 파일:** `desktop/clipper_nestjs/src/core/process/owned-child-process-registry.ts`의 POSIX identity 조회와 `test/owned-child-process-registry.test.js`의 회귀. 결과 문서는 이 기록과 W20 카드, WORKBOARD에 둔다.

- [x] 자체 생성 child의 기존 회귀 실패를 재확인하고 `ps` 두 출력의 안정 부분만 비교한다. 환경 원문은 출력하지 않는다.
- [x] 제어된 `ps` 응답으로 일시적 환경 필드 제거 시 정상 TERM, 출생·명령·owner token 변경 시 거절하는 회귀를 먼저 작성하고 실패를 확인한다.
- [x] POSIX child identity에서 환경 포함 조회는 owner token 확인에 사용하고, 환경 제외 조회의 시작 시각·명령을 해시한다. 두 조회가 같은 시작 시각·명령을 나타내지 않으면 identity를 반환하지 않는다. Windows 분기는 보존한다.
- [x] 대상 테스트, 실제 POSIX tree 종료, 전체 Node 테스트, 빌드와 diff를 검증한다. ffmpeg가 PATH에 있는 환경을 유지한다.
- [x] 별도 관점으로 안전성·범위 검토를 수행하고 W20 카드와 WORKBOARD에 결과·한계를 기록한다.

검토 초점: 같은 owner token을 가진 다른 출생/명령, owner token 소실, child가 조회 사이 종료, descendant의 출생/owner 변경, Windows 분기 미검증.
