# Storyboard Legacy Retirement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. 사용자 검토용 정리안이며 **미구현**이다. 이번 턴에 실행한 제품 수정은 완료 카드 세로 정렬 복구뿐이다.

**Goal:** 현행 대본 중심 v2만 지원하고, 사용하지 않는 옛 장면/컷 생성·조회·전환 코드와 등록을 제거한다.

**Architecture:** 현행도 사용하는 검색/정규화/조회/저장 함수를 옛 workflow 파일에서 먼저 분리한다. 그 다음 옛 화면·provider·독립 API와 구프로필 전환 UX를 제거한다. 디스크 원본 보존은 제품 런타임의 옛 형식 지원과 별도 운영 작업이다.

**Tech Stack:** Angular22/Material, Nest11, local JSON repositories and existing billing/jobs infrastructure.

**Spec:** 사용자9/29 주석2(옛 예외 데이터의 지속 지원 필요성과 처리 방향 질문), 기존 팀원 설계 D12/D13. D13 전환 UI 유지는 기존 설계의 방침이며 이번 **현행v2전용 제안은 해당 방침을 바꾸는 제안**이다. 실행 완료/지원 데이터 존재가 확인됐다는 뜻이 아니다.

## Global Constraints

- 실제 오래된 사용자 데이터/실행 중 옛 작업의 존재와 사용은 이번 코드감사에서 확인하지 않았다. 존재를 이유로 호환 지원을 정당화하지 않는다.
- 저장 원본을 자동 삭제하지 않는다. 실제 구레코드가 있다면 읽기 전용 집계 후 제품 코드와 별도의 일회성 퇴역 절차로 활성 저장 범위에서 분리하는 방식을 검토한다. 존재하지 않으면 변환/호환 계층을 만들지 않는다. 이 절차의 실제 사용자 데이터 변경은 이번 정리안에서 실행하지 않는다.
- v2 snapshot/artifact/index 저장과 취소·재시도·복구·정산을 보존한다. 기존 저장값 name120/purpose500과 신규 쓰기50/150 정책 차이는 버전별 UI 지원과 다른 문제다.
- 이름에 v1/legacy가 있다는 이유만으로 삭제하지 않는다. 현재 operating profile 자체도 schemaVersion.v1이므로 settingsV2/호출그래프로 구분한다.
- source는 W07 공통 브랜치의 Angular/Nest worktree에만 수정, 원본·타세션 경로 보존. 사용자 요청 전 commit/push/merge/deploy 및 실제 과금 테스트 없음.

## 감사 결과와 제거 대상

1. Angular `app.routes.ts:138~158`의 현행 profile/batch/scenario만 활성 라우트다. 하지만 `app.config.ts:70~72`의 옛research/candidate/production gateway 등록, `production-page`, scene/shot 뷰어·store/service 및 닿지 않는 과거 페이지가 남았다. 현행 scenario의 clipboard.copy는 남기고 옛 포맷팅 메서드만 제거한다.
2. Nest `shortform-director-candidate-production.controller.ts`에는 preflight/create/resume/runs/storyboard/history API가 아직 등록돼 있다. 관련 service/preflight/assembler/read-adapter도 module의 providers에 남았다. 이 경로는 v1 editorial/shot과 earlier 형식의 결과를 만들거나 변환하며 v2 pipeline에서 호출하지 않는다.
3. 옛 research/candidates controllers도 남았지만 `storyboard-batch-read.service.ts:7`의 parsePersistedCandidate, `storyboard-batch-discovery.ts:11`의 groundNormalizationResult/researchWindow는 현행v2가 옛 service 파일에서 가져다 쓰는 공용 함수다. inference client/source collector/topic/input builder/candidate validator도 v2 공용이다.
4. `operating-profile-card.component.html:15`의 “새 형식으로 전환”, form의 objective/toneKeywords 자동채움이 실제 구프로필 지원 코드다. v2 snapshot/preflight는 settingsV2를 요구하고 누락 시400이다.
5. `shortform-director-run-recovery.service.ts:64`에는 옛 scene/shot 복구와 공용 artifact/run index reconciliation이 섞였다. v2 document-store와 batch recovery는 같은 artifact registry/JSON 저장을 사용한다. 공용 초기화·v2 recovery를 제거하면 안 된다.

## Review Focus

- 현행v2 조회/PDF/복사 및 생성·resume checkpoint가 옛 함수 추출 뒤에도 동일한 문서/스냅샷을 읽는지.
- 구프로필 퇴역 시 이름 충돌·활성 index·삭제 tombstone·완료 batch snapshot 보존이 일관되는지.
- 옛 API 중단 시 미완료 run/reservation이 확인될 경우 기존 취소/정산 경계를 거쳐야 하는지. 운영 상태를 확인하지 않고 registry/recovery를 일괄 제거하지 않는다.
- “옛파일보존”을 이유로 runtime에 자동변환/전환CTA/별도조회기를 다시 넣지 않는지.
- 공급자 요청/예약/재시도/취소의 횟수 및 차감/환급 상태가 공용코드분리 전후 일치하는지.

## Tasks

### 1. 공용 함수와 초기화 분리

- [ ] 호출 그래프로 batch-read/discovery/document-store/recovery가 쓰는 함수를 확정하고 독립 파일로 옮긴다. 새 변환 계층 없이 기존 함수를 동일하게 이동한다.
- [ ] batch discovery/read/snapshot/PDF/recovery fixtures로 이동 전후 결과 hash, 저장 순서, checkpoints와 정산 횟수를 확인한다.

### 2. 닿지 않는 옛 화면·provider·API 철거

- [ ] Angular active v2 라우트/DI를 기준으로 옛 pages/components/store/gateway 등록과 전용 테스트를 제거한다. 공용 clipboard.copy와 현행 research evidence UI는 호출 그래프 확인 후 필요한 부분을 남긴다.
- [ ] Nest 독립 candidate-production/research/candidates controllers와 service/assembler/adapter/preflight 등록을 제거한다. 옛 endpoint404, 현행 batch endpoint·DI smoke 및 v2 생성/결과/조회/PDF 흐름을 검증한다.

### 3. 구프로필 전환 지원 제거

- [ ] 신규 create/settings save에서 settingsV2 필수로 계약을 강화하고, 전환CTA·옛필드자동채움·전용 테스트를 제거한다.
- [ ] 실제 구레코드 유무를 확인하고, 있다면 별도 보관/활성목록 분리의 구체적 데이터 처리안을 만든다. 새로 만드는 v2 프로필과 기존 v2 결과 스냅샷을 훼손하지 않는다. 지원할 데이터가 없으면 이 예외 때문에 runtime 코드를 만들지 않는다.

### 4. 회귀·화면·빌드·리뷰

- [ ] Angular 전체/스타일·Nest storyboard/profile/billing/jobs 관련·빌드와 DI smoke를 실행한다. 옛 endpoint404와 현행 batch/export/취소/복구/정산 fixture를 포함한다.
- [ ] 프로필 새 생성/복제/목적/선택 해제/IME/삭제/완료 결과, dark/light 반응형 브라우저 검증 및 새 native app을 패키징한다.
- [ ] 독립 리뷰 후 `.codex` W07에 제거 목록과 실제 검증/데이터 처리 여부를 기록한다.

정리안의 결론: **옛 기능을 계속 지원하도록 코드를 보강하는 방향이 아니라, 현행v2에 필요한 공용 부분만 남기고 옛 지원 경로를 철거하는 방향**이다. 이 문서는 질문에 대한 구체적 제거범위/순서를 제시하며, 실제 추가 철거 완료를 주장하지 않는다.
