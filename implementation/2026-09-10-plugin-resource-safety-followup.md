# 플러그인 리소스 안전성 후속 — 2026-09-10

이 문서는 [현재 상태 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md), [리소스 검토](./2026-09-10-plugin-resource-management-review.md), [TASKS](./TASKS.md)의 **R1~R4 구현 전 / watchdog 부재** 상태를 갱신하는 후속 기록이다. PG·운영·Windows 설치 상태 등 다른 항목은 이전 최신 감사를 유지한다.

**이번 결과: R1~R4와 기본 RAM watchdog·대시보드 조건부 정리를 구현하고 격리 검증했다. 전부 미커밋·미푸시·미배포. 실제 ML 플러그인·운영 배포·Build5 전체 QA는 실행하지 않았다.**

## 선행 대조

요청 문서 3개를 끝까지 읽고 관련 CPU 보관·PG/운영 인수인계의 필요한 범위를 대조했다. 과거 완료환불/배포/운영 화면 검증을 재실행하지 않았다. Superpowers debugging/TDD/verification/code-review 및 pragmatic guardrails 적용.

- 원본 8개 repo의 branch/HEAD/status/추적 diff SHA-256을 작업 전후 대조해 보존 확인.
- GitHub `ls-remote`로 배포 브랜치 8개 HEAD를 새로 조회해 이전 감사와 일치 확인. fetch/merge/reset/stash/commit/push 없음. 별도로 진전된 dev는 통합하지 않음.
- 임시 CPU checkout 존재 확인. 원래 세 repo HEAD·패치 SHA-256·diff byte 일치 후 작업 시작. 원래 CPU 패치 보관본 수정 없음.
- Python은 기존 integration 기준 `260751d2fa5be8a5a9cd8e346c60ba22d1512ed9`를 별도 clone에 checkout. 원본 dev 작업트리에 직접 적용하지 않음.

## 변경과 검증

- **R1:** 첫 await 전에 lease 등록, 준비부터 응답/실행 종료까지 보호. Python SDK/TTS 동기 요청을 health와 idle 판단에 포함.
- **R2:** 세대 무효화·health 응답 후 재검증·stop 확정과 시작의 동기 경계. 이미 확정된 stop은 끝날 때까지 새 시작 대기.
- **R3:** 취소한 job/stage만 DELETE. 등록 경합 시 DELETE 재시도, 다른 runtime 작업 강제 종료 제거. 실패/이미 취소된 감시에서도 lease 해제.
- **R4:** 수동·자동·직접 cold start의 공통 정리/재측정/판정/시작. JobsService의 과금·소스 준비보다 먼저 적용. RSS 합산 추정 제거, 동시 cold start 직렬화, 알려진 RAM 예상량의 측정 실패·critical 차단은 confirm으로 우회 불가.
- **Watchdog:** 백엔드가 10초마다 관찰. 가용 RAM10% 미만 3회 연속 후 idle만 정리, 회복 목표15%·재정리60초. UI와 무관하게 동작하며 busy/unknown/소유 중 런타임 보호.
- **UI:** 서버 조건부 idle-stop, 상태 미확인/오래됨/소유권 표시와 정리 제외, 중복 정리·조회 중첩 방지, 정리 결과·조회 오류·가용 RAM·빈 목록. CPU 주값/코어·스레드 보존.

검증: **Nest131 / Angular48 / Python14 전부 통과. Nest·Angular packaged 빌드 및 Python 구문 컴파일 통과.** 새 실패 테스트로 원래 결함 재현 후 수정. 독립 검토 지적 보완 후 마지막 blocker 없음. Electron 새 변경 없음으로 과거 CPU 검증은 반복하지 않음.

검증은 fake host/fetch/timer/HTTP/WS와 모의 TTS 엔진 범위이며 실모델 로드·플러그인 실행·프로세스 강제 종료·운영 배포가 아니다. 일부 테스트의 샌드박스 bind 제한과 Angular 빌드 중단은 로컬 권한 재실행으로 최종 통과했다.

## 보관·재개

[패치·복구 안내와 상세 정책](./patches/2026-09-10-resource-safety/README.md), [기준 커밋·SHA-256·파일 목록](./patches/2026-09-10-resource-safety/manifest.json), 같은 폴더 `evidence/`.

- 작업본: `/private/tmp/clipper-resource-dashboard-review/`.
- **4repo/37파일 전체 보관본** = 기존 CPU 개선 + 이번 안전성 변경. 새 safety 변경은 Nest24/Angular6/Python3파일이며 CPU 파일과 일부 겹친다.
- clean 기준 파일에 전체 패치를 적용하고 작업본 37파일과 byte 일치 확인. 기존 CPU 패치를 이미 적용한 checkout에 전체 패치를 중복 적용하지 않는다.
- 다음 반영은 사용자 요청 시 별도 commit/push → 새 source snapshot → 새 Windows 빌드/설치 절차. 이번 작업에서 배포 단계 진행 없음.

## 남은 항목

R5 Windows 소유 프로세스 트리, Windows 새 CPU CIM/Build7 소스·artifact 대조, 작업별 증분 RAM/VRAM 예산·GPU telemetry 신선도, 무응답 작업 강제 종료 정책, 더 넓은 GPU/종료 이력/UI 실기 검증은 남았다. running runtime에 이미 배정된 cold-start 예상량을 중복 예약하지 않는 기존 정책을 유지한다. 명시적 개별 force-stop/uninstall/앱 종료는 조건부 자동 정리와 별도다.

**Build5 전체 QA·실제 ML 플러그인 실행 HOLD, 공유 미커밋 보존, commit/push/deploy 모두 미실행.**
