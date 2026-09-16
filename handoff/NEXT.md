# 다음 세션 시작 안내

최신 갱신: 2026-09-17 KST.

Git 후속 상태: 사용자 승인으로 원본 Angular/Nest dev fast-forward 완료, 원본8repo 최신·clean. 통합 push는 Angular/Electron/Web API 완료, 나머지5repo는 자동 권한 검토 거절로 정확한 목적지 승인 대기. [상세 최신 결과](../implementation/2026-09-17-integration-commit-proposal.md)를 아래 이전 단계 표현보다 우선한다. 출시 후 API 호환 TODO는 사용자 지시대로 [`.codex/todos`](../todos/2026-09-16-post-launch-desktop-api-compatibility.md)로 이동했다.

**먼저 [작업 현황판](WORKBOARD.md)을 읽고, 사용자가 선택한 작업카드로 이동한다.** 여러 작업이 병행 중이며 이 파일은 특정 작업을 자동으로 최우선 지정하지 않는다.

1. 사용자 요청과 현황판을 대조한다. 애매하면 후보를 짧게 확인한다.
2. 해당 작업카드의 branch/worktree/HEAD와 실제 Git 상태를 읽기 전용으로 확인한다.
3. 상세 이력은 카드가 연결한 문서만 필요한 범위로 읽는다. 과거 체크박스만으로 새 작업을 만들지 않는다.
4. 서버에는 직접 접속하지 않는다. 서버 명령은 사용자가 실행한다.
5. 실제ML·Build5 전체QA HOLD를 유지한다. 명시된 사용자후속이 있을 때만 범위를 바꾼다.
6. 종료 시 작업카드·현황판·세션기록을 갱신하고 문서의 미커밋 상태를 알린다.

현재 사용자PC 원본8repo는 dev. 통합branch와 복구branch는 원격보존. 운영주소는 임시 카드사심사판이다. 로컬dev와 서버심사판/integration을 혼동하지 않는다.

- [이번 세션 요약](../records/sessions/2026/09/15.md)
- [2026-09-17 Git 정리·코드 커밋 결과](../implementation/2026-09-17-integration-commit-proposal.md): 사용자 승인 후 코드4repo 로컬 커밋 완료, 통합8repo clean. `.codex` 커밋·푸시는 사용자 요청 범위이며 원본 dev 갱신/코드 push는 별도 승인.
- [PG 통합 전 결정·누락 감사](../implementation/2026-09-17-pre-merge-decisions-and-gap-audit.md)
- [Astra 수정·재검증 — 현재 우선 판정](../implementation/2026-09-17-astra-fix-result.md)
- [Astra 독립 재감사 — 수정 전 증거](../implementation/2026-09-17-astra-independent-review.md)
- [PG 로컬 통합·검증 최종 결과](../implementation/2026-09-17-local-pg-integration-validation-result.md)
- [운영 복원 런북](../implementation/2026-09-15-pg-review-production-cutover-and-rollback.md)
- [이전 NEXT 전체 원문](archive/2026/09/next-before-task-board-2026-09-15.md): 기존스토리보드와 이전작업 기록을 삭제하지 않고 보존했다.

W04는 **R01–R13+A14 및 추가 환급 누락·Dialog 테스트 수정 검증·로컬 커밋 후 설치형 로컬 실기 단계**다. [최신 수정 결과](../implementation/2026-09-17-archive-refund-fix-result.md)와 위 커밋 결과를 먼저 읽는다. preparing/queued 취소의 정확한 근거와 환급 outbox를 삭제 전에 보존하고, stale attempt fallback을 제거했다. Dialog는 테스트만 분리했다. 이번 fresh 검증은 Angular 관련226, Electron955, Nest2,678, Web API2,802 PASS와 4repo build PASS다. 새 HEAD는 Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Web API `8b074a5`이며 코드 push·원본 dev 갱신·추가 병합·배포는 없다. 다음은 새 수정본 설치형 앱의 offline/online·재시작·계정전환·환급/잔액 UI 실기다. Google 로그인과 Windows 빌드/설치는 사용자 실행이며 ML/Build5 HOLD 유지. DB 복제본 리허설은 그 뒤이며 dump 명령은 사용자 실행 장비·DB 정보를 확인한 뒤 안내한다. 서버 직접 접속·실제 DB migration·배포 금지와 별도 승인 게이트를 유지한다.
