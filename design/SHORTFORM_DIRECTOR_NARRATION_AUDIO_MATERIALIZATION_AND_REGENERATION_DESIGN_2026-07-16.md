# AI 숏폼 디렉터 — 나레이션 오디오 materialization과 재생성 lifecycle 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`

## 목적

앞 단계는 측정된 TTS duration을 받아 VideoPlan을 재배치하는 순수 domain 경계까지만 만들었다. 이번 단계는 새 `shortform_director` 플러그인 안에서 실제 Supertonic provider를 호출할 수 있는 application lifecycle을 연결한다.

```text
estimated VideoPlan
  + voice / speed 선택
            ↓
cue별 Supertonic WAV 순차 합성
            ↓
project-scoped local audio artifact
  artifactId / checksum / duration만 저장
            ↓
exact-set timing alignment
            ↓
tts_aligned VideoPlan + narration-audio-pack.v1
```

기존 `shortform_prompt`의 project, TTS service, API와 UI는 변경하지 않는다. 공유하는 것은 이미 공용 모듈로 분리된 `SupertonicShortformTtsProvider`뿐이다.

## 핵심 결정

### 1. project 정본

`ShortformDirectorProject`에 `narrationAudio`를 추가한다.

```ts
interface NarrationAudioPackV1 {
  schemaVersion: 'narration-audio-pack.v1';
  videoPlanId: string | null;
  status: 'empty' | 'ready';
  generationId?: string;
  voice?: {
    providerId: 'tts.supertone';
    speakerId: string;
    speed: number;
  };
  artifacts: NarrationAudioArtifactV1[];
  summary: {
    total: number;
    ready: number;
  };
}
```

artifact metadata:

```ts
interface NarrationAudioArtifactV1 {
  schemaVersion: 'narration-audio-artifact.v1';
  cueId: string;
  artifactId: string;
  textFingerprint: `sha256:${string}`;
  durationMs: number;
  checksum: `sha256:${string}`;
  mediaType: 'audio/wav';
  sizeBytes: number;
  providerId: 'tts.supertone';
  speakerId: string;
}
```

project JSON에는 절대 경로, 상대 경로, URL, provider request/response, credential을 저장하지 않는다.

### 2. 로컬 파일 위치

파일은 `CLIPPER_DATA_DIR` 아래 director 전용 root에 둔다.

```text
shortform-director/
  narration-audio/
    <owner hash>/
      <project hash>/
        <artifactId>.wav
```

owner/project 원문을 경로 segment로 직접 쓰지 않고 SHA-256 기반 storage segment로 변환한다. project JSON과 API에는 이 경로가 노출되지 않는다.

### 3. provider

- provider는 현재 제품 결정에 따라 Supertonic으로 고정한다.
- 기존 공용 `SupertonicShortformTtsProvider`를 재사용한다.
- speaker는 provider preset catalog에 실제로 존재해야 한다.
- speed는 선택한 preset의 허용 범위와 지원 목록 안이어야 한다.
- cue는 plan 순서대로 하나씩 합성한다. 로컬 모델에 동시 요청을 쏟지 않는다.
- 이 작업은 로컬 TTS이므로 web operation charge를 시작하지 않는다.

### 4. 원자적 교체

새 generation의 모든 cue가 성공하고 timing alignment까지 성공해야 project를 한 번 저장한다.

```text
old project / old audio 유지
          ↓
new generation artifact들을 staging처럼 생성
          ↓
모든 cue validation + alignment
          ├─ 실패 → 새 파일 정리, project 저장 없음
          └─ 성공 → project 1회 upsert
                         ↓
                  이전 generation 파일 best-effort 정리
```

재생성 중 하나라도 실패하면 이전 `tts_aligned` plan과 이전 audio pack을 그대로 유지한다.

### 5. estimated baseline 보존

voice 또는 speed를 바꿔 재생성할 때 이미 aligned된 시간을 다시 비율 변환하면 rounding drift가 누적된다.

따라서 `tts-timing-alignment.v1`에 최초 estimated timing의 compact baseline을 함께 저장한다.

```ts
interface VideoPlanTimingBaselineV1 {
  schemaVersion: 'video-plan-timing-baseline.v1';
  durationMs: number;
  scenes: TimingNode[];
  narrationCues: TimingLeaf[];
}
```

baseline은 Scene/Beat/Shot/Layer와 narration cue의 id/start/duration만 보존한다. copy, grounding, asset strategy는 현재 plan 정본을 계속 사용한다.

재생성:

```text
current tts_aligned plan
  → baseline으로 estimated timing 복원
  → 새 WAV duration으로 다시 align
```

이미 aligned된 숫자를 baseline으로 사용하지 않는다.

## lifecycle

### project 생성

- empty VideoPlan
- empty AssetPack
- `narrationAudio.status: empty`
- total 0

### ContentStrategy 재생성

- 이전 VideoPlan과 visual AssetPack을 비움
- 이전 narrationAudio도 비움
- 기존 audio file 삭제는 이번 request의 정본 변경 이후 best-effort cleanup 대상

### 새 VideoPlan 생성

- `narrationAudio.status: empty`
- total = narration cue 개수
- 아직 artifact 없음

### 나레이션 생성 성공

- cue 전체 artifact 생성
- `tts_aligned` plan 저장
- `narrationAudio.status: ready`
- ready = total
- visual AssetPack은 기존 ref/binding/acquisition을 같은 layer id로 재계산

### voice/speed 재생성 성공

- baseline estimated plan에서 재정렬
- generation id와 artifact set 원자적 교체
- 기존 visual AssetPack 보존

### 생성 실패

- HTTP 오류 반환
- project JSON 변경 없음
- 이전 plan/audio pack 유지
- 현재 generation에서 생성된 새 파일 정리
- raw provider 오류나 로컬 경로를 응답·로그에 노출하지 않음

## API

```text
GET  /v1/projects/shortform-director/narration-presets
POST /v1/projects/shortform-director/projects/:projectId/narration-audio
GET  /v1/projects/shortform-director/projects/:projectId/narration-audio/:artifactId/file
```

생성 request:

```json
{
  "speakerId": "F2",
  "speed": 1.2
}
```

응답은 갱신된 raw `ShortformDirectorProject`다.

file endpoint는 owner 확인과 현재 audio pack에 artifact가 실제 포함되는지 검증한 뒤 WAV를 반환한다. 임의 artifact id나 다른 owner project 파일은 열 수 없다.

## Angular UX

VideoPlan이 생긴 project 카드에 작은 나레이션 패널을 둔다.

- Supertonic voice 선택
- 지원 speed 선택
- `나레이션 생성·정렬`
- ready 이후 `음성 다시 생성·정렬`
- `나레이션 7 / 7 · F2 · 1.2x`

실행 중에는 해당 project의 버튼만 loading 상태로 둔다. 로컬 TTS이므로 credit confirmation dialog를 열지 않는다.

이번 단계에는 audio player, cue별 재생성, waveform, render 버튼을 추가하지 않는다.

## 실패 검증

다음은 project를 저장하지 않는다.

- empty VideoPlan
- 알 수 없는 speaker
- 지원하지 않는 speed
- provider artifact id/path/provider/speaker 불일치
- WAV duration 누락 또는 비정상
- checksum/media type/size 불일치
- cue 일부 합성 실패
- baseline 복원 또는 timing alignment 실패

## 수용 기준

1. director 전용 preset API가 Supertonic voice와 지원 speed만 반환한다.
2. draft plan의 모든 cue를 순차 합성해 project-scoped WAV artifact를 만든다.
3. project JSON에는 path/URL이 없고 opaque artifact metadata만 저장된다.
4. 성공 시 plan이 `tts_aligned`, narrationAudio가 `ready`가 된다.
5. aligned plan 재생성은 최초 estimated baseline에서 수행된다.
6. voice/speed 변경 성공 시 generation 전체가 교체된다.
7. 중간 실패 시 이전 project/audio가 유지되고 새 partial file이 정리된다.
8. visual AssetPack refs/bindings/acquisitions/readiness가 유지된다.
9. legacy project read는 narrationAudio를 메모리에서 보강하고 read만으로 rewrite하지 않는다.
10. Angular가 voice/speed와 생성·재생성 상태를 표시하며 operation charge/render control을 추가하지 않는다.
11. 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- 실제 Supertonic 모델 실행 검증
- cue별 편집 또는 부분 재생성
- audio media ticket과 browser `<audio>` playback
- BGM/SFX/mix
- compiler, preview, renderer, render 실행
- queue/background job/concurrency lock
- operation charge
- server/Electron 실행, migration, commit/push/deploy

## 구현 결과

2026-07-16에 위 계약을 `shortform_director` 전용 NestJS/Angular 수직 슬라이스로 구현했다.

- compact estimated baseline 복원과 재정렬
- `narration-audio-pack.v1` lifecycle/hydration
- owner/project hash 기반 local WAV storage
- 공용 `SupertonicShortformTtsProvider`를 재사용한 cue 순차 합성
- 전체 성공 뒤 1회 project upsert, 실패 시 새 artifact cleanup
- preset/synthesis/file API
- Angular voice/speed 생성·재생성 패널

검증은 실제 모델 호출 없이 fake Supertonic WAV fixture로 수행했으며 Nest director 57/57, Angular director 22/22와 양쪽 production build가 통과했다.
