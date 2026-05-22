# Clipper1 Pre-Template Checkpoint

작성: 2026-05-06 18:59 KST

## 현재 상태

Clipper1 workspace flow는 prompt-only completed project 생성 흐름에서 벗어나, `클립 생성`으로 workspace draft를 만들고 `숏폼 생성`에서만 render queue/project로 승격하는 구조로 전환됐다.

구현된 핵심:

- 왼쪽 입력 panel: URL/prompt/paste/manual tab 기반 `클립 생성`.
- 가운데 clip editor: clip/대사 편집, media search 후보 선택, local upload/drag-drop/Electron file picker, media 삭제/교체/순서 변경, 다른 clip media 재사용.
- media slot: clip당 multiple media slots, slot duration/boundary/fit/motion preset 편집, thumbnail timeline 표시.
- 오른쪽 preview: 9:16 pre-render preview, slot별 fit 반영, motion preset transform 반영.
- render promotion: `숏폼 생성` 전 workspace 저장 후 NestJS render job/project 생성.
- backend render path: workspace media/TTS/layout/logo/output materialization, render manifest detail slots, render recipe media slot/effects mapping.

## 중요한 방향 수정

최근 작업은 media slot editor와 preview에 깊게 들어갔다. 사용자의 지적대로, 이제 template/TTS/BGM/logo/title visibility 같은 `숏폼 생성` 전 설정 화면을 먼저 채워야 한다.

다음 우선순위:

1. 오른쪽 panel에 render settings 영역 추가.
2. Template preset catalog 조회/선택 UI 추가.
3. 선택한 `templateId`를 workspace `renderSettings`에 반영하고 render 전 저장 경로와 연결.
4. TTS voice/speed, BGM/logo/title visibility 설정 UI를 이어서 추가.
5. 이후에 timeline drag/crop/position 같은 editor 고도화로 돌아간다.

## Template 현재 구현 상태

이미 있는 것:

- NestJS `GET /v1/template-presets` / `GET /v1/template-presets/:presetId`.
- Legacy Clipper1 template JSON catalog source.
- `ShortformWorkspace.renderSettings.templateId`.
- workspace render manifest `output.templatePresetId` / detail edit state mapping.
- legacy render recipe provider에서 template preset 사용.

아직 없는 것:

- 새 Clipper1 workspace 화면에서 template catalog를 조회하는 Angular service.
- 오른쪽 panel의 template 선택 UI.
- template 선택 시 preview에 template visual style이 즉시 반영되는 UX.
- template catalog DB/remote source.

## 커밋 대상

이번 checkpoint 이후 `clipper_nestjs`, `clipper_angular`의 누적 구현 변경을 각각 커밋한다.

`.codex` 문서는 상위 작업 디렉터리에 있으며 현재 git repo가 아니므로 코드 커밋에는 포함되지 않는다.
