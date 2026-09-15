# 대사 하이라이트 개선

최종 확인: 2026-09-15 KST. 상태: **재개 가능 — 감사·작업 공간 준비 이후**.

[전체 작업 현황](../WORKBOARD.md)

## 목표와 중단 지점

대사 하이라이트의 전체 실행 구조·메모리·후보 품질·UI/UX 개선. [9/4 전체 감사](../../main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md) §13 개선 후보, §14 작업 공간이 출처다.

5개 worktree HEAD가 감사 문서의 준비 기준과 정확히 같고 clean이다. 현재 로컬 origin/dev 참조에 없는 고유 커밋도 0개다. 따라서 이 브랜치들에 **준비 이후 별도 커밋된 개선 작업은 확인되지 않았다.** 다른 브랜치/dev에 개선이 전혀 없다는 뜻은 아니다.

## 작업 공간

공통 branch `feature/dialog-highlight-overhaul-20260904`, 같은 이름의 origin branch 추적. 루트 `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904`.

| repo | 하위 경로 | HEAD | dev에만 있는 커밋 수 |
|---|---|---|---:|
|clipper_web_api|web/clipper_web_api|`557da3fd22c47009d222d18a231a2b4848d9e5e9`|47|
|clipper_angular|desktop/clipper_angular|`566b1d398e54930b3edc59faa41b7927a69ee9fe`|124|
|clipper_python|desktop/clipper_python|`7d9a470c6c1ab25111badd04407fa56133a42712`|18|
|clipper_nestjs|desktop/clipper_nestjs|`cffa4ee2ee4137a91e139c6934a9ddce24d4d54f`|91|
|clipper_electron|desktop/clipper_electron|`768b8767ba4d6ab3d6dc11242a9e80e91382ddc2`|89|

커밋 수는 기능 수가 아니며, 이번 정리에서는 fetch하지 않고 당일 갱신된 로컬 원격참조로 비교했다. 재개 시 다시 확인한다.

## 다음 행동

1. 사용자에게 감사 후보 중 이번에 해결할 범위를 확인한다. 감사 전체를 자동 구현 범위로 취급하지 않는다.
2. 기준 dev가 많이 전진했으므로 5repo의 최신 차이를 확인하고 작업 branch 갱신 방법을 정한다. 지금은 merge/rebase하지 않았다.
3. warmup 표시와 실제 모델 load, 긴 영상 waveform/mel/STT 메모리, LLM 재시도·checkpoint·비용, 후보 점수/경계, 단계별 진행·실패 UX 후보를 최신코드와 대조한다.
4. CPU/리소스 안전성 작업과 겹치는 기능은 integration 쪽 보존 코드를 먼저 확인하고 중복 구현하지 않는다.

## 검증과 제약

이번에는 코드 수정·테스트·실제 ML 실행 없음. Build5/실제 ML HOLD 유지. 9/4 감사의 메모리 측정과 현시점 신규 검증을 혼동하지 않는다. 형제 desktop 경로 구조를 유지한다.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
