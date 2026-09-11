# Windows 소유 프로세스 트리 후속 — 2026-09-10

[직전 리소스 안전성 후속](./2026-09-10-plugin-resource-safety-followup.md)의 남은 항목 R5를 이어 진행했다. 최신 상태는 **R1~R4·watchdog·UI 구현 유지 + R5 구현·격리검증 완료, Windows 실환경 검증 보류**다. 다른 PG·운영·Build5/Build7 상태는 이전 감사·후속 기록을 유지한다.

R5는 실행별 Windows Job Object에 생성 시점부터 실제 플러그인과 자손을 묶고, 정리 후 활성 프로세스 수가 0인지 확인하도록 구현했다. Electron/Nest는 부모 exit만으로 완료 처리하지 않는다. 종료 확인이 없으면 소유 process·port를 보존하고 재시작을 차단한다. 원본 공유 작업본에 적용하지 않았으며 모든 변경은 별도 임시 checkout에 있다.

- **이번 검증:** Electron19 / Nest66 / Python10 테스트 통과. Electron·Nest 빌드와 Python 구문 컴파일 통과. 모의 프로세스·WinAPI 및 로컬 테스트만 실행했다.
- **보존:** 이전 CPU·안전성 보관본의37파일은 byte 동일. 원본8repo branch/HEAD/status/tracked diff hash와 원격 dev·배포 HEAD가 직전 기록과 동일. Angular는 새 변경 없음.
- **보관:** [복구·설계·검증 안내](./patches/2026-09-10-windows-owned-process-tree/README.md), [기준 커밋·SHA-256·파일 목록](./patches/2026-09-10-windows-owned-process-tree/manifest.json). 기존37파일+이번13파일 = 네 저장소50파일 전체 패치. clean 기준에 패치 적용 후 작업본 byte 대조 통과. 이전 패치 위에 중복 적용하지 않는다.

실제 Windows Job Object/uv 제어 stdin/자손 종료는 미검증이다. 향후 설치본 검증에는 새 SDK가 포함된 source snapshot·appVersion·venv 갱신 확인도 필요하다. CPU CIM·Build7 artifact 대조, RAM/VRAM 작업별 예산, GPU 신선도·넓은 UI 실기 검증은 남아 있다.

**커밋·푸시·배포 없음. 실제 ML 플러그인 실행과 Build5 전체 QA HOLD 유지.**
