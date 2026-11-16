# Codex Workspace

**2026-11-10 메일 세션 종합:** [구현·전체 Git·검증·개발 배포·운영 준비 기록](features/mail/records/2026/11/2026-11-10-mail-session-summary.md). 자동10종·광고 동의·공통 디자인·SES와 후속 수정은 4repo dev 반영/푸시 완료이며 사용자는 개발 배포 완료를 보고했다. **운영은 SES/SNS/IAM 생성만 완료, 이번 메일 코드/DB는 미배포**다. [메일 현재 기준](features/mail/README.md) · [10종 전체 문구](features/mail/records/2026/11/2026-11-10-automatic-mail-template-snapshot.md).

**2026-11-04 고객 환불 기본 제공:** [플래그 제거·dev 전 독립 검증 절차](features/payments/records/2026/11/04-customer-refunds-default-and-pre-dev-review.md). API `b924ca5`/Client `b90eedc` dev 반영, API5403·Client637·빌드 통과. 고객 신청은 기본 제공하되 관리자 승인 뒤 토스 취소한다. 별도 검증 결과를 받은 뒤에만 dev 반영하도록 인계에 명시했다. 전용 API3311·웹4203/4204는 현재 정지 상태다.

**2026-11-04 PG 두 세션 최종 정리:** [고객 환불·PG 통합 인계](features/payments/records/2026/11/04-two-session-pgops-summary.md). 환불 승인·외부 취소 자동 정리·운영 UI·앱 정산 복구·가격/크레딧·무료체험365일 상한은 dev 반영 완료다. 실제 Toss 전체 E2E·조건부 DB86개·운영 배포/문구·로컬API3311 재기동은 별도다. 웹4203/4204는 종료했고 API/DB는 보존했다. [결제 색인](features/payments/README.md).

**2026-11-04 하이라이트 Mac 가속:** [현재 모델·실측·사용·재현](operations/accelerators/README.md). 원격·원본 dev에 Python 17259bc와 Electron 849a51b를 반영했다. Made My Night 안무 335초 → 266초, 63개 목록·설정·집계 동일, 관련 Python 2,073개·Electron 1,977개 통과다. local-api Mac 앱·설치 환경·기동까지 확인했다. SFace·일부 얼굴 영역·Whisper는 CPU가 남아 있으며 Windows와 다른 플러그인 전체 검증은 별도다. [종합 인계](records/sessions/2026/11/04-highlight-mac-acceleration-handoff.md). 아래 과거 상태와 SHA는 당시 이력이다.

**2026-11-03 W19 최종 dev:** [가입 프로모션·Free·요금제별 플러그인·스토어 배지의6repo 커밋/검증/통합](features/plugin-catalog/records/2026/11/03-store-plan-badges-dev-merge.md). 작업 브랜치와 원격 dev가 일치하며 충돌0/clean이다. 기존 macOS 보조 프로세스 종료 오류는 사용자 요청으로 [W20 새 세션](handoff/tasks/macos-owned-child-identity.md)에 분리했다. 아래 미커밋 표시는 이전 단계 기록이다.

**2026-11-03 프로모션 세션 종합:** [현재 범위·구현·PG 논의·보류·Git/로컬 인계](records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md). 가입 프로모션·참여 조건·지속 Free·가격 카드·일괄 플러그인 설정·감사 표시까지 로컬 구현/검증, 미커밋·미푸시·미배포다. 유료 예약/레퍼럴 성과/XLSX는 보존 후 현재 코드에서 제거했다. [PG 별도 정리](features/payments/records/2026/11/03-session-pg-discussions-and-changes.md). **100원 업그레이드 문제는 다른 세션 담당으로 이번 작업에서 제외한다.**

**2026-10-29 남은 기능 재점검:** [W19 가입·크레딧형·기본 상태·요금제 허용과 가격 카드 데이터 연동](features/promotions/records/2026/10/29-remaining-scope-after-plugin-sync-deferral.md). [W18 앱 목록 동기화](handoff/tasks/plugin-catalog-sync.md)는 후속 작업으로 WORKBOARD에 별도 등록했다.

**2026-10-29 플러그인 목록 동기화 후속 이관:** 사용자 지시로 이번 세션의 구현에서 제외했다. [논의·정책·구현 상태](features/plugin-catalog/records/2026/10/29-admin-store-sync-discussion-and-deferral.md) · [후속 TODO](todos/2026-10-29-plugin-catalog-admin-store-sync.md). 이전의 자동 동기화 추천/실험은 구현 승인이나 제품 완료가 아니다.

**2026-10-23 최종 dev:** Person·무대 사용성·무대 파이프라인의 구현 커밋을 데스크톱 네 저장소 원격 dev에 통합하고 작업 브랜치와 일치를 확인했다. Angular `975e16f6`, Electron `dfc84d4`, Nest `15f534b9`, Python `584d76b`. [최종 원격 검증·전체 테스트·실영상/Windows 경계](features/highlights/records/2026/10/23-stage-person-integration-dev-merge-result.md). 아래 각 병합 SHA는 단계별 이력이다.

**2026-10-23 무대 사용성 완료:** 원본 구간 저장 전환과 결과 편집·선택·숏폼 구성·묶음 드래그·미확인 인물 썸네일을 구현하고 원격 `dev`에 반영했다. Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`; 충돌 없는 fast-forward, Electron 변경 없음. [이번 세션 구현·검증·병합 기록](features/highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md). 아래 Person 병합 SHA는 이 작업의 이전 기준이다.

이 저장소는 Clipper2 작업 중 Codex가 읽고 갱신하는 설계, 구현 기록, 다음 세션 인계 문서다.

앱 소스 코드는 각 repo에 있고, 이 저장소는 판단과 작업 이력을 추적한다.

## Current Repo Layout

2026-06-23 기준 `/Users/jina/project/adlight` 루트 자체는 git repo가 아니다.
앱 소스는 하위 repo로 나뉘고, 모든 active app repo의 기본 작업 브랜치는 `dev`다.

```text
desktop/
  clipper_angular/
  clipper_nestjs/
  clipper_python/
  clipper_electron/

web/
  clipper_infra/
  clipper_web_client/
  clipper_web_api/
  clipper_web_admin/

legacy/
  adlight_python/
  adlight_angular/
  adlight_nestjs/
```

작업은 각 repo에서 새 브랜치를 만들고 검증 후 `dev`에 merge한다. `.codex`는
별도 문서 repo이며 앱 코드 repo와 commit을 섞지 않는다.

과거 session record와 archive 문서에는 경로 이동 전의
`/Users/jina/project/adlight/clipper_*` 또는 `adlight_*` 절대 경로가 남아 있을 수 있다.
새 작업과 현재 runbook에서는 위 새 경로를 기준으로 한다.

## Current Focus

2026-10-23 **W14 인물 하이라이트**: 사용자 승인으로 충돌을 해결하고 데스크톱 4개 저장소를 원격 `dev`에 병합·푸시했다(Angular `8f45aef8`, Electron `43319ab8`, Nest `a577c8b6`, Python `153bb695`). 이전의 dev 병합 보류는 해제됐다. [병합·검증·후속 세션 인계](features/highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md)가 최신 기준이며, [기능 구현·모델·복귀점](features/highlights/records/2026/10/23-person-highlight-checkpoint-and-shared-face-model.md)은 병합 전 체크포인트다. 공통 AuraFace를 사용하는 안무의 품질 후속은 무대 파이프라인 세션, 결과 화면 기능 이식은 무대 사용성 세션이 맡는다. 사용성 후속은 위 기록과 같이 구현·원격 dev 반영을 완료했다. Web API 과금·권한도 후속 커밋 `ba68b2b`로 원격 dev 반영 및 로컬 DB 확인을 완료했다([기록](features/highlights/records/2026/10/23-person-highlight-web-api-billing-dev-merge.md)). 실제 영상 정확도·Windows 검증은 별도다.

2026-10-16 기준 고정 스레드 1~5·7~9와 8개 앱 저장소의 원격 `dev` 반영 상태를 다시 대조했다. 다음 세션은 [WORKBOARD](handoff/WORKBOARD.md)와 [NEXT](handoff/NEXT.md), [스레드·브랜치 감사](handoff/2026-10-16-pinned-thread-dev-reconciliation.md), [W13/W14 실험 회고](features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md)에서 시작한다. W13 72번은 평가 전용·제품 미채택이고, W14 공통 얼굴 연결과 공유 클립의 일부 UX는 `dev`에 반영됐지만 실제 새 영상 정확도는 미확인이다. W06 개발 MID/DB 초기화는 실행됐으며 QA 원 제보의 수동 검증과 시험 tree 미커밋 코드가 남아 있다.

## Historical Focus — 2026-09-29

2026-09-29 기준 작업별 새 세션으로 재개한다. 우선순위는 사용자 선택에 따른다.

- 시작: [작업 현황판](handoff/WORKBOARD.md)
- 재개 규칙: [NEXT](handoff/NEXT.md)
- 새 세션 프롬프트 5개: [공통 수정・PG・스토리보드・홈・하이라이트](handoff/prompts/2026-09-29-new-sessions.md)
- 최근 종료 기록: [2026-09-29](records/sessions/2026/09/29.md)

원본8repo는 조회 당시 dev·clean·로컬 origin/dev와 0/0이며, 새 개발 전 필요한 repo의 원격 최신성을 다시 확인한다.
기존 스토리보드 작업은 dev에 포함됐고 storyboard/dev-merge 옛 worktree 폴더는 제거했다. 브랜치는 보존했다.
카드사 심사 완료·새 MID와 테스트/라이브 키 발급은 사용자 보고 단계이며, 실제 키 전환/운영 배포/실결제 결과는 아직 확인하지 않았다.
임시 심사판의 현재 서버 상태는 PG 세션에서 다시 확인한다. 과거 날짜별 기록은 현재 상태나 우선순위가 아니다.

## Historical Focus — 2026-06 기록


2026-06-30 기준 `web/clipper_infra`, `web/clipper_web_api`,
`web/clipper_web_admin`의 `feat/release-management-runtime` 작업은 `dev`에 병합됐다.
Admin `Windows 빌드 시작` -> `clipper_web_api` -> Windows runner container `/jobs/start`
direct flow가 m2-stage와 Windows new runner PC에서 dry-run upload mode로 검증됐다.
다음 세션의 우선순위는 S3 upload mode 전환, `desktop/clipper_electron` output dir 공식 지원,
runner output cleanup, macOS direct runner 설계다.

2026-06-26 기준 `desktop/*` 4개 repo의 `feature/plugin-runtime-memory-management`
작업은 `dev`에 반영된 상태다. 여러 plugin/runtime을 연달아 실행할 때 메모리 부족으로
Clipper2 앱 또는 다른 앱까지 freeze되는 문제를 줄이기 위해 Python runtime lifecycle,
idle peer stop, child process stop, dashboard diagnostics, Template Builder official
DB/S3 remnants 제거, preview artifact health-wait exit listener cleanup을 포함했다.

현재 `desktop/clipper_angular`, `desktop/clipper_electron`, `desktop/clipper_nestjs`,
`desktop/clipper_python` 원본 checkout은 모두 `dev...origin/dev` clean 상태다. 2026-06-26
fetch 시 `origin/dev`가 이미 검증한 merge commit을 가리키고 있어 로컬 `dev`만
fast-forward했다. push는 이 세션에서 수행하지 않았다.

먼저 [handoff/NEXT.md](handoff/NEXT.md),
[records/sessions/2026/06/30.md](records/sessions/2026/06/30.md),
[records/sessions/2026/06/26.md](records/sessions/2026/06/26.md),
[design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md),
[records/sessions/2026/06/19.md](records/sessions/2026/06/19.md),
[design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md](design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md)를 본다.

Project-first / Plugin / Queue 대정리는 아직 별도 작업으로 둔다.

## Current Design Notes

- [design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md)
  - plugin/runtime memory pressure 완화를 위한 2026-06-23 초기 구현 상태 문서다.
  - `PythonRuntimeLifecyclePolicy`의 현재 범위, env 옵션, 검증 결과, 아직 실제 앱에서
    확인해야 할 runtime gap을 정리했다.
  - 완료 문서가 아니라 다음 세션의 이어받기 기준이다.
- [design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md](design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md)
  - `web/clipper_web_admin` 앱 버전 관리 mock 화면(`/versions`, `/versions2`) 비교 후,
    2026-06-26 확정된 공통 product version + OS별 artifact 정책을 기록한 문서다.
  - 최종 방식은 `/versions`다. macOS/Windows 독립 버전 스트림(`/versions2`)은 채택하지 않는다.
  - `dev -> alpha`, `stage/release -> rc`, `production/tag -> stable` 채널 기준과 SemVer bump 기준을 기록했다.
  - `release_versions` / `release_builds` / `release_artifacts` 분리, release coordinator 배치, desktop release branch, git tag/source snapshot, build runner, stable publish 조건, rollback/pulled/superseded 상태, platform별 auto update suppression 정책을 정리했다.

## 먼저 읽을 문서

1. [handoff/NEXT.md](handoff/NEXT.md)
2. [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
3. [README.RUNTIME.md](README.RUNTIME.md)
4. [README.OPERATIONS.md](README.OPERATIONS.md)
5. [README.DOCS.md](README.DOCS.md)

## Top-Level Guides

- [standards/GIT_COMMIT_MESSAGE_POLICY.md](standards/GIT_COMMIT_MESSAGE_POLICY.md)
  - 모든 app repo와 `.codex` repo 커밋 메시지는 Conventional Commit 형식을 따른다.
  - type 없는 `Add ...`, `Remove ...`, `Update ...` 메시지는 금지한다.
- [README.ARCHITECTURE.md](README.ARCHITECTURE.md)
  - repo 역할, backend/frontend/process boundary, plugin/project 구조.
- [README.RUNTIME.md](README.RUNTIME.md)
  - `local` / `devapp` / `packaged`, env 파일 소유권, port/runtime 정책.
- [README.FRONTEND.md](README.FRONTEND.md)
  - Angular standalone/signal/component/style/event 기준.
- [README.OPERATIONS.md](README.OPERATIONS.md)
  - Windows packaging, PowerToys EBUSY, smoke, ffmpeg/model 설치 운영 기준.
- [README.DOCS.md](README.DOCS.md)
  - 이 저장소 문서 구조와 날짜별 기록 규칙.

## Domain Indexes

- [features/payments/README.md](features/payments/README.md)
- [features/template-builder/README.md](features/template-builder/README.md)
- [features/dance-highlight/README.md](features/dance-highlight/README.md)
- [features/highlights/README.md](features/highlights/README.md)
- [features/shortform-director/README.md](features/shortform-director/README.md)
- [features/clipper-studio/README.md](features/clipper-studio/README.md)
- [operations/windows-packaging/README.md](operations/windows-packaging/README.md)
- [operations/env-runtime/README.md](operations/env-runtime/README.md)
- [records/README.md](records/README.md)

## Current Product Terms

- [design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
  - 2026-06-11 확정 기준. 유저에게 노출되는 핵심 개념은 `플러그인`과 `프로젝트`다.
  - `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 사용자 플러그인이다.
  - 큐/보관함의 사용자 단위는 `Project`이며, 기존 `workflow`/`job`은 현재 코드와 내부 실행 설명에서만 사용한다.
- [design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)
  - 위 제품 용어 기준을 코드에 반영하기 위한 Phase 1 구현 계획이다.

## Current UI References

- [design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
  - 2026-06-12 확정된 Template Builder 단순화와 숏폼 제작 템플릿/미리보기 방향.
  - 새 템플릿은 `main_title1`, `main_title2`, `caption`만 사용하고, ratio는 `1:1` 또는 `4:3` 단일 ratio다.
- [design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)
  - Clipper2 앱 전체의 모달/오버레이 사용처와 shared confirmation modal 교체 후보를 정리한 인벤토리다.

## Current Legacy Areas

아직 이관 중인 기존 폴더다. 새 문서는 가능하면 domain index 아래에 추가한다.

- `context/`: 프로젝트 히스토리와 현재 상태 배경.
- `design/`: 오래된 설계 초안과 아직 이관하지 않은 설계 문서.
- `implementation/`: 오래된 구현 계획, 체크포인트, runbook.
- `diagnostics/`: 긴 원인 분석 기록.
- `standards/`: 반복 적용할 개발/문서화 규칙.

`imports/`는 legacy asset / DB backup 성격이므로 git 추적에서 제외한다.

## Repo Notes

- 이 저장소는 `/Users/jina/project/adlight/.codex` 자체가 git root다.
- 원격은 `git@github.com-personal:sweetgoomba/clipper2-codex.git`.
- 기존 앱 repo와 별도로 commit/push한다.
