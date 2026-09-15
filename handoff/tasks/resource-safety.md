# CPU·플러그인 리소스 안전성

최종 확인: 2026-09-15 KST. 상태: **구현·보존 완료 / 실기 검증 보류**.

[전체 작업 현황](../WORKBOARD.md)

## 현재 상태

CPU/R1~R4·기본pressure watchdog·조건부정리UI·R5 Windows 소유프로세스 종료 누적50파일이 복구 branch와 integration 양쪽에 보존됐다. **미커밋/미푸시 작업이 아니다.**

`recovery/resource-safety-20260915` 원격보존 후4worktree 제거. 현재 원본dev에 이 개선이 모두 포함됐다고 가정하지 않는다.

## 근거

- [복구 branch SHA와 정리](../../implementation/2026-09-15-resource-workspace-recovery.md)
- [R1~R4 안전성](../../implementation/2026-09-10-plugin-resource-safety-followup.md)
- [R5 후속](../../implementation/2026-09-10-windows-owned-process-tree-followup.md)
- [검증·SDK/venv 정리](../../implementation/2026-09-10-documentation-source-reconciliation.md)

## 다음 행동·보류

실제 Windows 소유 Job Object/자손종료·CIM CPU·모델 환경, Build7 source snapshot/앱버전/SDK·venv 조건을 확인해야 한다. Build5전체QA·실제ML실행은 HOLD. 복구 이전 CPU7/안전성37패치를 다시 중복 적용하지 않는다. 이후 메모리/VRAM 예산과GPU관측·무응답정책은 별도후속 후보다.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
