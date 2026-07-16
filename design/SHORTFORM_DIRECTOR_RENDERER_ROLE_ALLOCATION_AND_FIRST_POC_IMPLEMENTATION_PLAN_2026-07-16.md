# AI 숏폼 디렉터 — Renderer 역할 분담과 첫 PoC 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_DECISION_2026-07-16.md`

## Task 1 — Isolated Remotion harness 경계

- [x] production Nest `ncc` bundle과 분리된 PoC package 위치를 정한다.
- [x] pinned Remotion/React revision과 lockfile을 둔다.
- [ ] prebuilt composition bundle과 per-render input props를 분리한다.
- [x] current representative execution bundle을 path-safe private harness input으로 투영한다.
- [x] production Director adapter token은 계속 빈 배열로 유지한다.

검증:

- regular Nest build가 PoC native package를 bundle하려 하지 않는다.
- 기존 `shortform_prompt`, generic provider와 Python renderer diff가 0이다.

## Task 2 — Representative composition RED/GREEN

- [x] staged image/video/WAV exact set을 source id로 해소한다.
- [x] visual timeline 9개와 composition layer 20개를 frame-accurate하게 투영한다.
- [x] subtitle 7개와 text overlay role을 구현한다.
- [x] `diagram.sequence-card.v1`을 current normalized sampler로 구현한다.
- [x] start/reveal/hold/exit/end 5개 still을 생성한다.

검증:

- current conformance profile의 timeline count와 motion semantic checkpoint가 일치한다.
- report와 fixture에는 absolute path, URL, provider secret이 없다.

## Task 3 — Media render와 operation bridge

- [x] MP4/H.264/AAC 1080×1920 30fps를 렌더한다.
- [x] Remotion progress callback을 Director 0..1 progress로 투영한다.
- [x] AbortSignal을 Remotion cancel signal에 연결한다.
- [x] ffprobe로 duration, stream, codec, dimensions와 fps를 관측한다.
- [x] elapsed와 output bytes를 같은 environment id로 기록한다.
- [ ] Chrome/compositor child process를 포함하는 신뢰 가능한 peak RSS 측정을 추가한다.

검증:

- current candidate evaluator가 automated pass/fail을 산출한다.
- duration drift가 한 frame 이하인지 확인한다.
- cancel smoke는 orphan browser/render process를 남기지 않는다.

## Task 4 — Offline과 packaging feasibility

- [ ] composition bundle 재사용 시 source build가 반복되지 않음을 확인한다.
- [x] browser/compositor native resource와 실제 disk size를 기록한다.
- [x] preinstalled Chrome과 local compositor를 명시해 runtime auto-download 경로 없이 재실행한다.
- [x] Electron `extraResources` 후보 구조와 runtime path injection을 문서화한다.
- [x] macOS arm64 뒤 Windows x64와 supported macOS 범위 검증 계획을 만든다.
- [x] Remotion license 적용 여부와 production gate를 사용자 결정 항목으로 남긴다.

검증:

- PoC 성공을 production packaging 성공으로 과장하지 않는다.
- Electron 앱과 개발 서버를 자동 실행하지 않는다.

## Task 5 — Manual review와 다음 선택

- [ ] full MP4와 5개 still을 manual 7축으로 검토한다.
- [x] text clipping, Korean font, mobile safe zone과 motion continuity의 renderer spot check를 기록한다.
- [ ] automated result와 manual review를 합쳐 accepted/rejected를 결정한다.
- [ ] Remotion pass 시 production adapter 설계 여부를 결정한다.
- [ ] Remotion fail 시 Motion Canvas PoC를 다음 vertical slice로 승격한다.
- [ ] complex technical diagram 요구가 생기면 Manim materialization PoC를 별도 설계한다.

## 공통 금지

- [x] 기존 `shortform_prompt`를 변경하지 않는다.
- [x] 기존 generic renderer가 Director recipe를 claim하게 만들지 않는다.
- [x] Manim을 final render 중 즉석 실행하지 않는다.
- [x] renderer/browser binary를 사용자 모르게 production runtime에서 내려받지 않는다.
- [x] public API/project JSON/job params에 path나 credential을 넣지 않는다.
- [x] production adapter/API/UI/과금/배포를 이번 PoC에 섞지 않는다.
- [x] commit/push/deploy/개발 서버/Electron 실행을 하지 않는다.

## 2026-07-16 실행 결과

구현 위치:

- `desktop/clipper_nestjs/tools/shortform-director-remotion-poc`
- `desktop/clipper_nestjs/test/shortform-director-remotion-poc.test.js`

고정 revision:

- Remotion packages `4.0.489`
- React / React DOM `19.2.7`
- nested private package와 lockfile 사용
- root Nest package에는 Remotion/React dependency를 추가하지 않음

실제 실행 흐름:

```text
representative ready project
  → RenderRecipe 41.2s / 30fps / 1080×1920
  → synthetic staged input 13개
     ├─ image 4
     ├─ video 2
     └─ narration WAV 7
  → loopback-only staged asset server
  → path-safe Remotion projection
  → checkpoint still 5개
  → raw Remotion MP4
  → ffprobe
  → AAC padding drift가 한 frame 초과할 때만
       FFmpeg audio trim + video stream copy + remux
  → final ffprobe
  → current candidate evaluator
```

대표 결과:

- final output: 41.2초, 30fps, 1080×1920, MP4/H.264/AAC, audio stream 1개
- timeline: visual 9, TTS 7, subtitle 7, overlay 11, composition layer 20
- motion semantic checksum: start/reveal/hold/exit/end 5개 exact match
- render progress callback: 1,244회, `0 → 1`
- Director progress projection: `0 → 1`
- benchmark environment: `darwin-arm64-node24-remotion4.0.489-local`
- pipeline elapsed: 74,257ms
- final output bytes: 8,082,314
- automated checks 7개 전부 pass
- final status: `manual_review_required`

duration finalization 관찰:

- raw video stream: 41.2초
- raw AAC/container: 41.258667초
- 한 frame tolerance `0.033333...`초를 넘으므로 조건부 FFmpeg finalization 적용
- 영상은 재인코딩하지 않고 copy하며 audio만 41.2초로 trim/re-encode해 최종 video/audio/container를 모두 41.2초로 맞춤

취소 smoke:

- 2% progress에서 `AbortSignal`을 Remotion cancel signal로 전달
- cancellation 관측 성공
- partial output 없음
- 종료 뒤 Remotion/headless Chrome 잔여 process 없음

renderer spot check:

- 5개 sequence-card still과 timeline 5개 추가 추출 frame을 확인했다.
- Korean glyph clipping, mobile safe-zone 이탈, sequence-card state 파손은 보이지 않았다.
- start/end frame은 계약대로 완전히 숨겨진 상태이고 reveal/hold/exit가 연속적으로 변한다.
- 합성 test pattern과 tone audio를 사용했으므로 source faithfulness, hook, script, narration/visual fit을 포함한 manual 7축 전체는 아직 판정하지 않는다.

현재 크기 관찰:

- nested PoC install tree: 약 270MB
- macOS arm64 compositor package: 약 17MB
- development composition bundle: 약 20MB
- 이 수치는 source map과 개발 dependency를 포함한 PoC 관찰값이며 production packaged 증분 크기가 아니다.

남은 핵심 gate:

1. source revision fingerprint 기반 prebuilt composition bundle 재사용
2. Chrome/compositor child tree peak RSS 측정
3. 실제 representative asset/audio로 manual 7축 검토
4. Electron `extraResources` packaged smoke와 offline startup
5. Windows x64와 지원할 macOS 범위 검증
6. Company License/Automator 비용 판단
7. 위 gate 뒤에만 production adapter 설계 여부 결정
