# 숏폼 VideoPlan foundation — 설계 (Spec)

> **상태: 2026-07-16 후속 결정으로 superseded.** 아래 내용은 기존 `shortform_prompt`에 legacy `clips → VideoPlan` 호환 계층을 넣었던 설계 이력이다. 해당 uncommitted 구현은 제거했으며, 현재 정본은 `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`다. 기존 플러그인은 변경하지 않고 새 `shortform_director`가 native `VideoPlan`을 처음부터 소유한다.

> 작성일: 2026-07-16 · 대상 레포: `clipper_nestjs` · 상위 working design: `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md` · Vira 현재 코드 감사: `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`

## 목표와 범위

현재 `ShortformProject.clips`를 잃지 않고 `VideoPlan → Scene → NarrationBeat → Shot → Layer` 형태의 provider-neutral planning IR을 도입한다. Phase 1a는 현재 clip을 plan으로 투영하는 호환 계층이며 렌더 실행 경로는 바꾸지 않는다.

범위:

- `video-plan.v1` 타입과 `ShortformProject.videoPlan?`
- legacy clip에서 plan을 만드는 순수·결정적 adapter
- 서비스 read/write 경계의 plan backfill/refresh
- adapter와 서비스 호환 테스트

비범위:

- `PlanningContext`/`vira-evidence.v1`, web_api prompt/structured output, Vira exporter/API, Angular UI
- `VideoPlan → RenderRecipe` compiler
- renderer/image/video provider 선택 또는 실행
- 기존 `ProjectManifest → RenderRecipe → clipper_payload → FFmpeg` 변경

## 결정

| 결정 | 내용 |
|---|---|
| IR 역할 | `VideoPlan`은 창작 의도 IR, 기존 `RenderRecipe`는 실행 IR |
| 호환 정본 | Phase 1a에서는 `clips`가 편집·렌더 정본 |
| 변환 | clip 1개=scene 1개, narration line 1개=beat 1개, media slot 1개=shot 1개 |
| 시간 | 모든 plan 시간은 프로젝트 시작 기준 절대 millisecond |
| 레이어 | shot마다 visual layer, 텍스트가 있으면 caption layer |
| 미디어 없음 | scene 전체를 덮는 `unresolved` shot/visual layer 생성 |
| 에셋 전략 | `owned/source/search/generated-image/generated-video/programmatic/existing/unresolved` |
| 정보 최소화 | plan에는 artifact/provider 참조만 보존; 로컬 path/원본 URL 복제 금지 |
| 구형 데이터 | `videoPlan` optional; read에서 메모리 backfill, read-only 디스크 migration 없음 |
| stale 방지 | 모든 service write 전에 현재 clips로 plan 재생성 |

## 모델 요약

```text
ShortformVideoPlan
  schemaVersion = video-plan.v1
  derivation = legacy-clips + projectId + projectUpdatedAt
  durationMs
  scenes[]
    startMs/endMs/sourceClipId
    beats[]: text + sourceNarrationLineId + startMs/endMs
    shots[]
      startMs/endMs/sourceMediaSlotId?
      layers[]
        visual: asset route/ref + fit + motionPreset
        caption: string[]
  audioTimeline
    narrationCues[]
    bgmCue?
```

Beat timing은 각 line의 유효한 `durationMs`를 weight로 사용해 scene 길이에 맞춰 정규화한다. 마지막 beat의 `endMs`는 scene 끝으로 고정해 rounding gap을 없앤다. scene은 `clip.order` 순서로 배치한다.

에셋 route 분류:

- `media.shortform.source_url_*` → `source`
- `media.local_user.*` → `owned`
- `media.search.*` 또는 provider id에 `.search.` 포함 → `search`
- 명시적 generated provider → asset kind에 따라 `generated-image`/`generated-video`
- 알려지지 않은 기존 asset → `existing`
- asset 없음 → `unresolved`

## 서비스 경계

- `list/get`: 저장된 `videoPlan` 유무와 관계없이 현재 clips 기반 plan을 응답에 제공하되 저장하지 않는다.
- `upsertProject`: transient TTS URL 제거와 함께 현재 clips 기반 plan을 저장한다.
- repository 파일 version은 올리지 않는다. JSON의 optional field 추가이므로 기존 store reader와 호환된다.
- 렌더 manifest/recipe/payload 생성 코드는 plan을 읽지 않는다.

## 수용 기준

1. clip 정렬, scene 누적 시간, beat/shot/layer 매핑이 결정적이다.
2. source/search/local/unknown/missing asset route가 정확하다.
3. empty media clip도 유효한 unresolved shot을 가진다.
4. 구형 project get은 plan을 반환하지만 repository upsert를 호출하지 않는다.
5. clip이 바뀐 project 저장 시 plan duration/asset ref가 함께 갱신된다.
6. 관련 node tests, 전체 NestJS build/test가 통과한다.

## 과거 구현 결과 — 현재 코드에서는 제거됨

2026-07-16 `feat/shortform-video-plan-foundation` 브랜치에서 Phase 1a를 한 차례 구현했으나, 새 플러그인 격리 결정에 따라 커밋 전에 모두 제거했다.

- `ShortformProject.videoPlan?`과 scene/beat/shot/layer/audio 타입을 추가했다.
- `LegacyClipVideoPlanAdapter`는 완전한 현재 project와 필드가 빠진 legacy project를 모두 결정적으로 변환한다.
- `list/get`은 write 없이 plan을 backfill하고, 모든 service upsert는 최신 clips로 plan을 refresh한다.
- 렌더 manifest/recipe/payload와 Python renderer는 수정하지 않았다.
- 제거 전 새 테스트 5개, 격리 숏폼 API 테스트 10개와 build가 통과했었다.
- 현재 기존 `shortform`/`shortform-core` 경로는 `origin/dev` 대비 diff가 0이며, 이 설계의 adapter/model은 남아 있지 않다.

## Vira 현재 코드 감사 후 영향

2026-07-16 `/Users/jina/project/vira`의 실제 `main`을 감사한 결과, PDF에서 가정했던 format/hook/viral 필드 일부는 현재 활성 `shorts_*` 세대가 아니라 등록 해제된 legacy pipeline에 속한다.

Phase 1a는 Vira schema를 `VideoPlan`에 포함하거나 추정하지 않았으므로 코드 수정이 필요하지 않다.

- Vira의 현재 관측·파생·AI 추론·legacy evidence는 상위 `PlanningContext`에서 분리한다.
- legacy clip에서 만든 plan에 Vira 근거를 소급 생성하지 않는다.
- native planner가 도입될 때 evidence/strategy reference를 별도 version으로 추가한다.
