# Shortform Plugin Split and Shared Core Design

작성일: 2026-05-06
상태: 사용자 방향 승인 완료, 구현 계획 작성 중

## 목적

현재 `workflow.clipper_studio` 1차 구현은 Clipper1을 Clipper2에 붙이기 위한 내부 추상화와 provider boundary를 만드는 데에는 도움이 됐지만, 사용자 흐름과 UI/UX가 실제 목표와 맞지 않는다.

특히 지금 구현은 사용자가 프롬프트를 입력한 뒤 버튼을 누르면 보관함에 `completed` 상태의 프로젝트 shell이 생기고, 제작 화면 안에서 클립을 확인하고 수정한 뒤 최종 `숏폼 생성`을 누르는 Clipper1의 핵심 흐름을 제공하지 못한다. 이 문서는 그 방향을 폐기하고, Clipper2에서 새로 가져갈 Clipper1/Variation 구조를 정의한다.

이 문서는 `CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`의 이전 Clipper Studio 화면 방향을 대체한다. NestJS control plane, provider/capability 분리, render recipe/provider 원칙은 기존 설계를 유지한다.

## 핵심 결정

1. 사용자-facing workflow plugin은 둘로 분리한다.
   - `Clipper1` plugin: URL/프롬프트/붙여넣기/수동 시작으로 하나의 숏폼을 제작한다.
   - `Variation` plugin: 정해진 시나리오와 asset pool을 기반으로 여러 변형 영상을 batch 생성한다.
2. 두 plugin은 내부 구현을 공유한다.
   - clip, narration, TTS, media pool, media slot, template, preview timeline, render recipe는 공통 Shortform Core 모델을 사용한다.
   - workflow별 UI와 시작 방식은 다르지만 render/preview/provider 계약은 같아야 한다.
3. `클립 생성`은 최종 렌더 큐 진입이 아니다.
   - 입력을 기반으로 클립 초안을 만들거나 수동 blank clip workspace를 여는 단계다.
   - 보관함/완료 목록에는 아직 들어가지 않는다.
4. `숏폼 생성`을 눌렀을 때만 render job이 queue에 쌓인다.
   - 최종 MP4 생성은 NestJS job/queue/project history 흐름으로 승격한다.
   - 초안 편집 중인 workspace는 library completed project가 아니다.
5. 기존 Clipper1의 clip당 media 1개 제한은 제거한다.
   - clip은 여러 media asset을 가질 수 있고, narration/TTS duration에 맞춰 media slot timeline을 가진다.
6. preview는 Angular-native로 만든다.
   - React/Remotion Player를 Clipper2 Angular 앱에 직접 들이지 않는다.
   - Remotion Angular 문서는 React wrapper를 Angular에서 사용하는 방식이므로 현재 방향에서는 제외한다.

## Workflow Surface

### Clipper1 Plugin

목표는 기존 Clipper1의 제작 흐름을 Clipper2에 맞게 다시 만드는 것이다.

첫 화면은 작업 보관함이 아니라 제작 workspace다. 왼쪽 입력 영역은 항상 남아 있고 탭으로 전환한다.

- `URL`: 기사, 블로그, 일반 웹페이지 URL을 입력한다.
- `프롬프트`: 사용자가 만들고 싶은 영상 설명을 직접 입력한다.
- `붙여넣기`: 임의 사이트나 문서에서 복사한 rich content를 붙여넣는다.
- `수동 시작`: 사용자 입력/AI 초안 없이 바로 blank clip 하나로 시작한다.

입력 영역의 primary action label은 `클립 생성`이다. 이 버튼은 AI script generation, URL ingestion, paste normalization을 거쳐 workspace 안에 clip draft를 만든다. 수동 시작은 blank clip 하나를 즉시 만든다.

중앙은 clip editor다.

- clip 추가, 삭제, 복제, 재정렬
- clip 제목 또는 메모
- narration line 추가, 삭제, 재정렬, 텍스트 수정
- narration line별 TTS artifact 재생/재생성 상태
- clip별 search hint/keyword 수정
- media pool 관리
- media slot timeline 자동 배치 및 1차 수동 조정

오른쪽은 9:16 숏폼 preview와 전역 설정이다.

- 전체 숏폼 preview 재생
- 현재 template, TTS voice, speed, BGM, logo, title visibility
- render 가능 여부와 provider 상태
- 최종 action `숏폼 생성`

### Variation Plugin

Variation plugin은 Clipper1 plugin과 별도 entry를 가진다. 사용자가 Clipper1 제작 화면 안에서 variation 기능을 억지로 찾게 하지 않는다.

Variation plugin의 기본 surface는 scenario와 variation set이다.

- base scenario clips
- clip별 asset folder/pool 연결
- variation card 목록
- voice/template/ratio/speed lock 또는 randomize
- variation별 script/title/media selection 차이
- batch render queue
- 완료물 다운로드 또는 zip

`adlight_angular`/`adlight_nestjs`의 `feature/variation-module` branch에서 확인한 구조는 그대로 복사하지 않는다. 다만 다음 개념은 Shortform Core로 흡수한다.

- `Clip.assetPoolFolderIds`
- `AssetFolder`
- `Asset`
- `Variation`
- `VariationLocks`
- clip asset pool 기반 media selection
- seeded shuffle / min slot duration 기반 image sequencing
- NestJS orchestrator의 job/SSE/output 흐름

## Shared Shortform Core

공통 core는 workflow UI를 알지 않고, 숏폼 제작에 필요한 domain contract만 가진다.

```text
ShortformWorkspace
  id
  workflowKind: clipper1 | variation
  sourceSession?
  clips[]
  renderSettings
  previewTimeline
  variationSet?

ShortformClip
  id
  order
  title?
  narrationLines[]
  mediaPool
  mediaSlots[]
  searchHints[]
  durationMs

NarrationLine
  id
  text
  ttsArtifactId?
  durationMs?
  subtitleTiming?

MediaPool
  assets[]
  folders?
  selectionPolicy

MediaSlot
  id
  assetId
  startMs
  endMs
  fit
  motionPreset?

RenderSettings
  ratio
  templateId
  ttsVoiceId
  ttsSpeed
  bgmArtifactId?
  logoArtifactId?
  titleVisibility
```

Provider output은 모두 artifact 또는 typed DTO로 정규화한다.

- URL/paste/prompt ingestion -> `SourceDocument`
- LLM script generation -> `ShortformDraft`
- TTS -> `audio.tts` artifact + duration
- media search/import/generation -> `media.image` / `media.video` artifact
- template catalog -> `TemplatePreset`
- final render -> `video.rendered` artifact

## Media Model

기존 Clipper1의 “clip 하나에 media 하나”는 더 이상 core schema가 아니다.

기본 자동 배치는 다음 규칙을 따른다.

1. clip duration은 narration line TTS duration 합으로 계산한다.
2. media pool에 여러 asset이 있으면 clip duration을 slot으로 나눈다.
3. video asset은 가능한 원본 duration을 사용하고, image/gif는 slot duration 동안 motion preset을 적용한다.
4. asset이 부족하면 반복하되, 같은 asset이 길게 고정되지 않도록 seeded shuffle을 사용한다.
5. variation mode에서는 folder/pool selection과 variation seed로 slot을 재계산한다.

1차 구현에서는 full timeline editor까지 만들지 않는다. 대신 자동 slot 배치, slot별 media 교체, slot 삭제/추가 정도까지를 목표로 둔다.

## Preview

최종 목표는 사용자가 `숏폼 생성`을 누르기 전에 만들어질 영상을 신뢰할 수 있게 보는 것이다.

1차 preview는 Angular-native full shortform preview다.

- MP4를 미리 ffmpeg로 생성하지 않는다.
- `PreviewTimeline`을 기반으로 전체 숏폼을 처음부터 끝까지 재생한다.
- HTML video/img/audio element와 CSS overlay로 media, TTS, subtitle, title/template layer를 동기화한다.
- 실제 final render와 같은 `RenderRecipe`에서 파생된 timeline을 사용해 preview/render 차이를 줄인다.
- preview viewport는 항상 9:16 숏폼 비율이다.

WASM ffmpeg는 1차 preview의 기본 경로로 쓰지 않는다. bundle size, 성능, worker 관리, 파일 IO 비용이 크고 편집 중 즉시성에 불리하다. 다만 나중에 “브라우저 안에서 빠른 proof MP4 생성” 같은 별도 capability가 필요하면 `PreviewRenderer` interface 뒤에서 실험할 수 있다.

WebCodecs도 1차 필수 조건이 아니다. browser 지원과 구현 복잡도를 고려해, 먼저 DOM/CSS/audio 기반 renderer로 계약을 잡고 필요할 때 내부 renderer를 교체한다.

## Source Ingestion

URL 입력은 provider boundary로 분리한다.

```text
source.ingestion.url
  -> legacy selector/news/blog adapters
  -> readability/extractor adapter
  -> scrapling adapter candidate
  -> remote company parser proxy
```

기존 Clipper1의 언론사 selector, Naver Blog, Tistory, Brunch parser는 fallback 자산으로 유지할 수 있지만 새 core에 규칙이 새면 안 된다.

Scrapling은 검토 대상 provider다. 도입 여부는 POC로 판단한다.

- 한국 뉴스/블로그 URL에서 제목/본문/대표 이미지 추출 품질
- JS-heavy page 처리
- desktop packaged mode 배포 난이도
- Python/NestJS process boundary
- 실패 시 fallback과 사용자 수정 UX

붙여넣기 입력은 Quill에 고정하지 않는다. 필요한 것은 editor brand가 아니라 pasted HTML/text/image를 `SourceDocument`와 local artifacts로 정규화하는 것이다. Tiptap 또는 custom contenteditable 모두 후보가 될 수 있다.

## Queue and Project State

상태 전이는 명확히 나눈다.

```text
Open plugin
  -> create local/server workspace draft
  -> input/manual start
  -> clip generation or blank clip
  -> user edits clips/settings/preview
  -> user clicks 숏폼 생성
  -> render job enqueued
  -> project/output history updated after render result
```

금지되는 흐름:

```text
prompt submit
  -> create completed project shell in library
```

workspace draft 저장은 가능하지만 completed project 또는 output으로 보이면 안 된다. 사용자가 작업을 나갔다가 돌아올 수 있는 draft persistence는 별도 상태로 표현한다.

## Error Handling

- URL/paste parsing 실패: 입력 탭 안에서 실패 사유와 fallback paste/manual option을 제공한다.
- LLM script 실패: workspace는 유지하고 재시도/수동 시작을 제공한다.
- media search/import 실패: clip별 media pool 상태로 표시하고 다른 provider나 local upload로 대체한다.
- TTS 실패: narration line별 실패 상태를 표시하고 voice 변경/재시도를 제공한다.
- preview sync 실패: final render queue에 넣기 전에 문제가 보이도록 timeline validation error를 보여준다.
- render 실패: queue/project job 실패로 남기고 workspace draft로 돌아가 수정 후 재시도할 수 있게 한다.

## Testing and Verification

1차 구현 계획을 쓰기 전에 아래 검증 축을 포함해야 한다.

- Shortform Core model/unit test
- media slot scheduler deterministic test
- Clipper1 workspace state transition test
- `클립 생성`이 completed project를 만들지 않는 API test
- `숏폼 생성`만 render queue에 job을 넣는 API test
- Angular 3-panel layout smoke
- 9:16 full preview timeline smoke
- TTS/media provider fake adapter test
- packaged Electron file dialog/media import smoke

## Phasing

Phase 1 목표:

- 기존 prompt-only Clipper Studio 화면을 Clipper1 workspace shell로 교체
- 왼쪽 tabbed input과 `클립 생성`
- manual blank clip start
- center clip editor 1차
- clip당 multi media pool/slot schema 1차
- right 9:16 full preview 1차
- `숏폼 생성`에서만 render queue 생성

Phase 2 목표:

- URL ingestion provider 개선 및 Scrapling POC
- paste ingestion 개선
- clip/media slot 수동 편집 강화
- template preview parity 개선
- voice/template 변경 시 TTS/render recipe 재계산 UX 보강

Phase 3 목표:

- Variation plugin 별도 surface
- asset folder/pool library
- variation set/card/locks
- batch render/zip
- shared Shortform Core를 통한 Clipper1/Variation render path 통합

## Pending Review

이 설계는 사용자 대화에서 확인한 방향을 반영한 현재 기준 문서다. 구현으로 넘어가기 전 사용자가 이 문서를 리뷰하고, 특히 다음 항목을 확인해야 한다.

- Clipper1과 Variation을 별도 plugin으로 노출하는 것
- shared Shortform Core의 책임 범위
- Phase 1에 Variation UI를 넣지 않고 core schema만 준비하는 것
- preview를 Angular-native full shortform preview로 시작하는 것
- Scrapling은 즉시 의존성이 아니라 provider POC로 검토하는 것
