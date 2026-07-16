# AI 숏폼 디렉터 — Supertonic 실측 TTS 타이밍 정렬 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`

## 목적

LLM이 만든 native VideoPlan의 시간은 캠페인 목표 길이에 맞춘 추정값이다. 실제 Supertonic WAV 길이가 나오면 narration cue를 기준으로 Scene/Beat/Shot/Layer를 다시 배치하고 `timingBasis`를 `estimated`에서 `tts_aligned`로 바꾼다.

```text
estimated VideoPlan
  Scene → Beat → Shot → Layer
             │
             └─ narration cue text
                       ↓
                 Supertonic WAV
                       ↓
       Nest가 측정한 cue별 전체 duration
                       ↓
        exact-set validation + reflow
                       ↓
tts_aligned VideoPlan
  ├─ cue/Beat는 실측 WAV 길이
  ├─ Scene/plan은 하위 길이의 합
  └─ Shot/Layer는 기존 시각 비율을 보존
```

이 단계는 실제 Supertonic을 실행하지 않는다. 이미 합성·측정된 결과를 안전하게 받아 재정렬하는 순수 domain 경계를 먼저 만든다.

## 현재 코드 감사 결과

현재 `desktop/clipper_python/plugins/tts_supertonic`의 `/tts` 응답은 WAV 상대 경로만 반환한다. word 또는 sentence timestamp는 반환하지 않는다.

`desktop/clipper_nestjs/src/modules/tts-synthesis/tts-synthesis.provider.ts`는 생성된 WAV를 읽어 다음을 계산한다.

- 전체 `durationMs`
- `sha256` checksum
- `artifactId`
- `providerId`
- `speakerId`

따라서 이번 계약은 word alignment가 아니다. VideoPlan narration cue 1개와 Supertonic WAV 1개를 대응시킨 cue-level measured alignment다.

## 입력 계약

```ts
interface VideoPlanTtsAlignmentInputV1 {
  schemaVersion: 'video-plan-tts-alignment-input.v1';
  measurements: Array<{
    cueId: string;
    textFingerprint: `sha256:${string}`;
    durationMs: number;
    audioArtifact: {
      artifactId: string;
      checksum: `sha256:${string}`;
      providerId: string;
      speakerId: string;
    };
  }>;
}
```

`textFingerprint`는 저장된 narration text를 `trim + NFC` 정규화한 뒤 UTF-8 SHA-256으로 계산한다. TTS 생성 뒤 사용자가 문장을 바꾸거나 오래된 음성 결과가 섞이는 것을 막는다.

입력에는 파일 경로, URL, provider credential, 원문 request/response를 넣지 않는다.

## 출력 계약

draft VideoPlan의 `timingBasis`를 다음 union으로 확장한다.

```ts
type VideoPlanTimingBasis = 'estimated' | 'tts_aligned';
```

정렬 성공 plan에는 다음 metadata를 둔다.

```ts
interface VideoPlanTtsAlignmentV1 {
  schemaVersion: 'tts-timing-alignment.v1';
  source: 'measured_tts_audio';
  measurements: VideoPlanNarrationTimingMeasurementV1[];
}
```

metadata에는 정렬 시각을 넣지 않는다. 같은 plan과 같은 measurement는 같은 결과를 만드는 결정적 domain 변환으로 유지한다.

## 검증 규칙

정렬은 all-or-nothing이다.

1. 입력 plan은 `draft`이고 `timingBasis: estimated`여야 한다.
2. 모든 narration cue에 measurement가 정확히 1개 있어야 한다.
3. 누락, 중복, 알 수 없는 cue id를 거부한다.
4. `textFingerprint`가 현재 cue text와 정확히 같아야 한다.
5. duration은 양의 정수이며 Beat와 Shot 최소 길이를 유지할 수 있어야 한다.
6. artifact/provider/speaker id는 opaque id만 허용하고 path 또는 URL 모양을 허용하지 않는다.
7. checksum과 fingerprint는 정확한 `sha256:<64 lowercase hex>` 형식이어야 한다.
8. 정렬된 전체 길이는 손상된 측정치를 막는 넓은 안전 범위 10~90초 안에 있어야 한다. 이는 품질 점수나 목표 길이 강제가 아니다.

하나라도 실패하면 부분 정렬 plan을 만들지 않는다. fallback helper는 원본 `estimated` plan과 정제된 실패 사유를 반환한다.

## 타임라인 재배치

### Beat와 narration cue

- Beat duration = 대응 WAV의 실측 `durationMs`
- cue start/duration = 대응 Beat start/duration
- cue text와 id는 유지

### Scene과 plan

- Scene start는 앞 Scene 끝
- Scene duration은 포함된 aligned Beat 길이의 합
- plan duration은 모든 aligned Scene 길이의 합

### Shot

Beat 안의 Shot id, order, intent는 유지한다.

새 Beat 길이를 각 Shot의 기존 duration 비율로 나눈다. 비례 결과가 250ms보다 작아지는 Shot만 최소값으로 고정하고 나머지를 다시 비례 배분한다. 정수 나머지는 fractional remainder가 큰 순서, 동률이면 기존 order 순서로 배분한다.

### Layer

Layer id, order, kind, role, content, assetStrategy는 유지한다. 기존 Shot 안의 상대 시작/끝 비율을 새 Shot에 투영한다.

- Shot 전체를 덮던 Layer는 새 Shot 전체를 정확히 덮는다.
- 부분 Layer는 최소 1ms를 유지하고 새 Shot 밖으로 나가지 않는다.

## AssetPack과의 관계

이 단계는 visual layer id와 asset strategy를 바꾸지 않는다. 따라서 기존 AssetRef, binding, acquisition은 동일 layer에 계속 유효하다.

aligned plan으로 `buildAssetPack()`을 다시 실행해도 다음은 보존되어야 한다.

- requirement id와 layer mapping
- local/manual/provider binding
- acquisition 상태
- production readiness 판정

TTS audio artifact는 현재 visual-only AssetPack에 넣지 않는다. 향후 compiler의 audio input 계약에서 별도로 연결한다.

## 대표 synthetic acceptance

대표 45초 plan의 7개 narration cue에 synthetic Supertonic-shaped measurement를 제공한다.

```text
estimated 45,000ms
  5,000 + 7,000 + 7,500 + 7,500 + 5,500 + 5,500 + 7,000

tts_aligned 41,200ms
  4,600 + 6,400 + 6,900 + 7,200 + 5,000 + 4,900 + 6,200
```

기대 Scene 길이:

```text
hook    4,600
context 6,400
value  14,100
proof   9,900
cta     6,200
```

id, order, copy, grounding, asset strategy와 AssetPack readiness는 변하지 않아야 한다.

## Angular UX

현재 화면에는 실행 버튼을 추가하지 않는다. 저장된 plan의 timing basis만 명확히 표시한다.

- `estimated`: `예상 타이밍`
- `tts_aligned`: `TTS 실측 정렬`

duration summary는 aligned plan의 실제 총 길이를 그대로 표시한다.

## 실패와 재정렬 정책

- validation 실패: 기존 `estimated` plan 유지
- 일부 cue 성공: 저장하지 않음
- duration 측정 불가: 저장하지 않음
- 이미 `tts_aligned`인 plan의 재정렬: 이번 slice에서는 거부

voice/speed 변경 뒤 반복 정렬은 estimated baseline 보존 방식까지 함께 정한 후 별도 lifecycle로 추가한다. 누적 비율 변환으로 rounding drift가 생기는 구현은 넣지 않는다.

## 수용 기준

1. 대표 45초 plan이 synthetic 7개 measurement로 41.2초 `tts_aligned` plan이 된다.
2. Scene/Beat/Shot은 0-based contiguous이고 plan 전체를 정확히 덮는다.
3. narration cue와 Beat timing이 일치한다.
4. Shot/Layer 최소 길이와 containment를 유지한다.
5. id/order/copy/grounding/asset strategy는 불변이다.
6. missing/duplicate/unknown/stale/invalid measurement는 all-or-nothing으로 실패한다.
7. fallback은 원본 plan을 변경하지 않는다.
8. aligned plan으로 AssetPack을 재계산해도 binding/acquisition/readiness가 유지된다.
9. Angular가 예상/실측 timing basis를 구분해 표시한다.
10. 기존 `shortform_prompt` 경로는 변경하지 않는다.

## 비범위

- 실제 Supertonic 합성 호출과 음성 파일 저장 endpoint
- word/phoneme timestamp
- 자막 단어 강조와 SFX sync
- voice/speed 선택 UI와 TTS 재생성 lifecycle
- audio artifact file serving
- compiler, preview, renderer, render 실행
- provider operation charge
- server/Electron 실행, migration, commit/push/deploy

## 구현 결과

2026-07-16에 새 `shortform_director` domain과 Angular summary에 이 계약을 구현했다.

- `video-plan-tts-alignment-input.v1` exact-set validator와 narration fingerprint helper를 추가했다.
- 대표 45초 plan은 synthetic measured duration으로 41.2초가 됐다.
- Shot은 기존 duration 비율로 재분배하고 Layer는 Shot 상대 위치를 보존한다.
- 실패 시 원본 estimated plan을 그대로 반환하는 all-or-nothing fallback을 추가했다.
- aligned plan 저장/hydration과 기존 visual AssetPack 보존을 회귀로 고정했다.
- Angular에는 timing basis label만 추가했고 실제 합성·재생성·render control은 넣지 않았다.

검증:

- desktop Nest director 50/50, TypeScript build 통과
- Angular director 20/20, production build 통과
- 기존 Angular/Nest/web shortform 경로 `origin/dev` 대비 diff 0
- raw color, whitespace, 고신뢰 secret-like pattern 검사 통과
