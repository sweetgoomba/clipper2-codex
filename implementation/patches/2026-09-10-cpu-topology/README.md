# CPU 표시 변경 보관본

2026-09-10 사용자 요청으로 구현·검증한 변경이다. 아직 커밋·푸시·배포하지 않았다. 원본 공유 변경을 보존하기 위해 별도 checkout에서 작업했다.

- 현재 작업본: `/private/tmp/clipper-resource-dashboard-review/` 아래 세 저장소.
- 기준 커밋과 패치 SHA-256: [manifest.json](./manifest.json).
- 패치는 각 저장소 기준 커밋에 대한 `git diff --binary HEAD`이다. 새로 만든 clean checkout에서 기준 커밋을 확인하고 `git apply --check <패치 절대 경로>`로 검사한 뒤 적용한다. 공유 원본에 바로 적용하지 않는다.
- 복구 후에도 별도 커밋·push·새 릴리즈 source snapshot·Windows 빌드/설치가 필요하다. 임시 clone의 origin은 로컬 경로이므로 배포 대상 GitHub 저장소와 브랜치를 확인해야 한다.
- 검증: Electron 관련 8개, Angular 관련 42개, 세 저장소 빌드, 모의 Windows CPU 카드 다크/라이트/조회불가 표시, 실제 Mac 10코어·10스레드 조회. 실제 Windows 새 코드 검증은 남음.
- 리소스 관리 검토에서 발견한 R1~R5와 지속 watchdog은 이 패치에 포함하지 않는다.

상세 상태는 [전체 감사](../../2026-09-10-current-state-and-resource-dashboard-audit.md), 리소스 문제는 [검토 기록](../../2026-09-10-plugin-resource-management-review.md)을 참조한다.
