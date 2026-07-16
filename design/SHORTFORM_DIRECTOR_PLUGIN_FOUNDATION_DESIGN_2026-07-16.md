# AI 숏폼 디렉터 플러그인 foundation — 설계

작성일: 2026-07-16 KST

## 결정

새로운 source-grounded planning, Vira evidence, native `VideoPlan`, hybrid rendering 작업은 기존 `shortform_prompt`에 추가하지 않는다.

```text
기존 shortform_prompt
  clips 중심 생성·편집·렌더
  변경하지 않음

새 shortform_director
  PlanningContext
    → ContentStrategy
    → native VideoPlan
    → 향후 RenderRecipe compiler
```

working plugin identity:

- plugin id: `shortform_director`
- 표시명: `AI 숏폼 디렉터`
- Angular route: `/shortform/director`
- Nest API root: `/projects/shortform-director/projects`
- runtime: install-gated `virtual_workflow`

표시명은 제품 명명 결정 후 바꿀 수 있지만, 첫 구현에서는 위 identity를 일관되게 사용한다.

## 기존 플러그인 비침범 경계

- `src/features/shortform/**` 변경 금지
- `src/modules/shortform/**`, `src/modules/shortform-core/**` 변경 금지
- 기존 `/projects/shortform/**` API와 `shortform_prompt` catalog/route 동작 변경 금지
- 기존 clips/project JSON store를 읽거나 migration하지 않음
- 새 project는 별도 API, 타입, repository, JSON store를 사용
- renderer/compiler가 준비되기 전까지 기존 렌더 경로를 호출하지 않음

이전에 구현한 `clips → VideoPlan` backfill은 이 결정과 충돌하므로 커밋 전 제거한다. 새 플러그인은 legacy clip을 창작 정본으로 삼지 않고 native plan을 처음부터 소유한다.

## 첫 vertical slice

첫 구현의 목표는 새 플러그인의 독립된 end-to-end 뼈대를 실제로 여는 것이다.

```text
Plugin Store
  → shortform_director 설치
  → /shortform/director 진입
  → campaign prompt 입력
  → POST /projects/shortform-director/projects
  → 별도 JSON store에 planning draft 저장
  → PlanningContext + 빈 native VideoPlan 응답
  → 화면에서 프로젝트 목록과 foundation 상태 확인
```

이 단계는 LLM planner, asset generation, renderer를 실행하지 않는다. 버튼이나 상태가 실제로 하지 않는 일을 했다고 표현하지 않는다.

## 프로젝트 모델

```text
ShortformDirectorProject
  schemaVersion: shortform-director-project.v1
  workflowKind: shortform-director
  status: draft
  planningContext
    schemaVersion: planning-context.v1
    campaignBrief.prompt
    marketEvidence[]: vira-evidence.v1
  videoPlan
    schemaVersion: video-plan.v1
    derivation.kind: native
    durationMs: 0
    scenes: []
    audioTimeline.narrationCues: []
```

빈 native `VideoPlan`은 생성이 완료됐다는 뜻이 아니라 새 플러그인이 소유하는 draft container다.

## Vira evidence runtime boundary

첫 validator는 payload의 모든 세부 필드를 동결하지 않고 envelope과 lifecycle 정합성을 검사한다.

- `schemaVersion`, id, kind, evidenceClass
- source surface와 lifecycle
- stable subject의 `youtube_shorts` platform
- materializedAt, `sufficient/partial/insufficient/unavailable` state, window/sample metadata
- method id/version
- object payload
- current/lab/on-demand/legacy surface와 lifecycle의 허용 조합

허용 lifecycle:

| surface | lifecycle |
|---|---|
| `shorts-market` | `active` |
| `shorts-growth-lab` | `lab` |
| `video-analysis-8d` | `on_demand` |
| `legacy-intel-market` | `legacy_unregistered` |
| `legacy-intel-viral` | `legacy_unregistered` |

8차원 compact payload와 Vira exporter/API는 다음 단계에서 확정한다.

## 저장 경계

```text
기존: <CLIPPER_DATA_DIR>/shortform/projects.json
신규: <CLIPPER_DATA_DIR>/shortform-director/projects.json
```

두 repository는 타입과 파일을 공유하지 않는다. owner subject filter를 동일하게 적용하되 데이터는 교차 조회하지 않는다.

## UI 경계

새 Angular feature는 `features/shortform-director/**` 아래에만 둔다.

- `<app-page>` 사용
- Material form/button 사용
- semantic token만 사용
- campaign prompt 입력과 planning draft 생성
- 저장된 director project 목록 표시
- evidence 개수, scene 개수, 현재 상태 표시
- 기존 shortform editor component를 import하거나 감싸지 않음

## 수용 기준

1. plugin catalog/store/nav/route에 `shortform_director`가 독립 항목으로 존재한다.
2. install 전 직접 진입은 기존 plugin guard로 store에 redirect된다.
3. 새 화면은 기존 shortform page/component를 사용하지 않는다.
4. 생성 API는 별도 project store에 `PlanningContext`와 native `VideoPlan` draft를 저장한다.
5. 잘못된 Vira envelope/lifecycle은 400으로 거부한다.
6. 기존 `shortform_prompt` metadata와 API/feature 파일은 `origin/dev` 대비 변경이 없다.
7. 관련 Angular/Nest tests와 build가 통과한다.

## 비범위

- Vira 네트워크 연동·DB 직접 접근·exporter
- LLM `ContentStrategy`/native scene 생성
- asset router/provider 호출
- `VideoPlan → RenderRecipe` compiler
- preview/editor/render/queue/billing
- renderer 및 image/video provider 선정

## 구현 상태 — 2026-07-16

foundation vertical slice를 `desktop/clipper_nestjs`, `desktop/clipper_angular`의 각 `feat/shortform-director-foundation` 브랜치에 구현했다.

```text
Angular shortform-director feature
  → dedicated director API
  → Vira envelope validation
  → owner-scoped director repository
  → <CLIPPER_DATA_DIR>/shortform-director/projects.json
  → PlanningContext + empty native VideoPlan
```

현재 화면은 campaign prompt로 기획 draft를 만들고 evidence/scene 개수와 저장 상태를 보여준다. Vira exporter/API, LLM planner, asset generation, renderer 호출은 아직 없으며 실제로 수행하지 않는 생성·렌더 UI도 두지 않았다.

후속 수직 기능에서는 수동 `vira-evidence.v1` JSON handoff, current payload validation, lifecycle admission과 `ContentStrategy | null` 경계를 추가했다. 정본은 다음 문서다.

- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_IMPLEMENTATION_PLAN_2026-07-16.md`
