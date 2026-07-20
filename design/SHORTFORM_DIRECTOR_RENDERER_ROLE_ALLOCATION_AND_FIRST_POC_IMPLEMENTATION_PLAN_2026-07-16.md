# AI 숏폼 디렉터 — Renderer 역할 분담과 첫 PoC 구현 계획

작성일: 2026-07-16 KST

정본 설계:

- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_DECISION_2026-07-16.md`

## Task 1 — Isolated Remotion harness 경계

- [x] production Nest `ncc` bundle과 분리된 PoC package 위치를 정한다.
- [x] pinned Remotion/React revision과 lockfile을 둔다.
- [x] source revision 기반 cached composition bundle과 per-render input props를 분리한다.
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
- [x] Chrome/compositor child process를 포함하는 process-tree peak RSS 측정을 추가한다.

검증:

- current candidate evaluator가 automated pass/fail을 산출한다.
- duration drift가 한 frame 이하인지 확인한다.
- cancel smoke는 orphan browser/render process를 남기지 않는다.

## Task 4 — Offline과 packaging feasibility

- [x] composition bundle 재사용 시 source build가 반복되지 않음을 확인한다.
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

## 2026-07-20 실행 순서 변경

- [x] manual review 전에 source-checkout local Remotion adapter를 구현한다.
- [x] existing JobsService executor/progress/cancel/retry에 연결한다.
- [x] owner-scoped output materialization과 API/Angular MP4 저장을 구현한다.
- [x] 실제 staged PNG/WAV에서 H.264/AAC MP4를 생성한다.
- [ ] 실제 representative asset/audio manual 7축을 수행한다.
- [ ] Electron packaged/offline runtime과 supported OS를 검증한다.
- [ ] Company License/Automator 비용을 판단한다.

이 순서 변경으로 기존 `Task 5`의 manual/release 판정이 삭제된 것은 아니다. 구현 가능성을 먼저 닫고 그 출력으로 품질과 release 적합성을 검토한다.

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

## 2026-07-20 cache/RSS 후속 실행 결과

구현:

- composition source revision은 nested PoC `src/**`, `package.json`, `package-lock.json`과 bundle-options revision의 SHA-256이다.
- cache miss는 임시 디렉터리 build와 manifest 검증 뒤 fingerprint 디렉터리로 원자 승격한다.
- cache hit는 bundler를 호출하지 않고 같은 bundle을 재사용하며 portable summary에는 path 없이 revision/status만 남긴다.
- process-tree monitor는 100ms마다 benchmark Node root와 모든 live descendant의 RSS를 합산한다.
- sampler process와 unrelated process는 제외하고 PID/command/path는 report에 저장하지 않는다.
- candidate report에는 aggregate `peakRssBytes`, private-safe run summary에는 표본/peak/process-kind evidence를 남긴다.

실행:

- 첫 cancel smoke: cache `created`, 42 samples, Chrome/Remotion compositor 관측, cancel 성공, partial output 없음
- 같은 revision 두 번째 cancel smoke: cache `reused`, 31 samples, bundler 재호출 없음, cancel 성공
- full benchmark: cache `reused`, 725 samples, Chrome/Remotion compositor/FFmpeg 관측
- full process-tree peak RSS: 2,296,545,280 bytes
- full pipeline elapsed/output: 70,914ms / 8,053,591 bytes
- final output: 41.2초, 30fps, 1080×1920, MP4/H.264/AAC
- automated conformance: 7/7 pass, manual review pending

회귀:

- Nest Director + generic renderer boundary: 87/87
- Angular Director: 30/30
- web API Director: 18/18
- Angular/Nest/web API build: pass
- `git diff --check`: pass

남은 핵심 gate:

1. 실제 representative asset/audio로 manual 7축 검토
2. Electron `extraResources` packaged smoke와 offline startup
3. Windows x64와 지원할 macOS 범위 검증
4. Company License/Automator 비용 판단
5. 위 gate 뒤에만 production adapter 설계 여부 결정

## 2026-07-20 무료 상용 조건 정정 — Motion Canvas 구현 결과

사용자의 무료 상용 renderer 요구를 hard constraint로 다시 적용했다. 위 Remotion 결과와 코드는 삭제하지 않고 fallback/비교 증거로 보존한다.

### Task 6 — Permissive dependency gate

- [x] isolated Motion Canvas package와 exact lockfile을 추가한다.
- [x] Motion Canvas `3.17.2`, Puppeteer `25.3.0`, Vite `5.4.21`을 exact pin한다.
- [x] transitive dependency license allowlist를 자동 검사한다.
- [x] GPL/unknown synthetic package를 거부한다.
- [x] official `@motion-canvas/ffmpeg` exporter를 dependency에서 제외한다.

결과: installed package 133개, violation 0.

### Task 7 — Custom headless Motion Canvas worker

- [x] RenderRecipe visual/audio/subtitle/text/sequence-card를 투영한다.
- [x] static source revision fingerprint와 atomic bundle cache를 구현한다.
- [x] strict loopback Host/method/token/source id와 video byte-range를 구현한다.
- [x] browser outbound network를 차단한다.
- [x] PNG frame stream을 external FFmpeg `image2pipe`로 전달한다.
- [x] narration delay/mix와 MP4/H.264/AAC FFprobe contract를 구현한다.
- [x] progress/cancel/sanitized failure를 연결한다.

### Task 8 — Application adapter와 Remotion 보존

- [x] `director.adapter.motion-canvas-local.v1`을 추가한다.
- [x] registry order를 `[motionCanvas, remotion]`으로 바꾼다.
- [x] Remotion package/worker/adapter/test를 삭제하거나 되돌리지 않는다.
- [x] output storage/job executor/API/Angular 계약을 재사용한다.
- [x] cancel 시 temporary output workspace를 폐기하는 회귀를 추가한다.

### Task 9 — Actual render/cache/RSS

- [x] 최소 PNG+WAV case에서 실제 1초 H.264/AAC MP4를 만든다.
- [x] 대표 41.2초/1,236 frame full MP4를 만든다.
- [x] 같은 source revision 재실행에서 cache `reused`를 확인한다.
- [x] Chrome/FFmpeg descendants 포함 process-tree peak RSS를 측정한다.
- [x] 대표 frame의 text/diagram/subtitle 겹침을 확인하고 수정한다.

최종 cache-hit 결과:

- output: 41.2초, 30fps, 1080×1920, MP4/H.264/AAC
- bytes: 2,072,173
- elapsed: 21,037ms
- samples: 106
- peak RSS: 1,941,848,064 bytes

### Task 10 — 회귀와 문서

- [x] Director 103 tests에서 fail 0을 확인한다.
- [x] actual Motion Canvas integration 1/1을 확인한다.
- [x] Angular Director focused 29/29를 확인한다.
- [x] Nest/Angular/web API와 isolated Motion Canvas build를 확인한다.
- [x] 전체 Nest baseline의 Director 밖 61개 실패를 별도로 기록하고 범위 밖 코드를 수정하지 않는다.
- [x] session/design/handoff에 무료 상용·OS·FFmpeg 배포 경계를 기록한다.
- [x] commit/push/PR/deploy/server/Electron/DB/migration/provider call을 실행하지 않는다.

다음 구현 gate:

1. macOS x64·Windows x64 packaged/offline actual MP4 smoke
2. Windows recursive RSS sampler
3. 기존 app-managed FFmpeg/FFprobe 공급물의 release compliance audit
4. 대표 peak RSS와 package 크기 최적화
5. 실제 asset/audio manual 7축

## 2026-07-20 Electron packaging 실행 결과

### Task 11 — Build-time immutable runtime

- [x] source revision으로 Motion Canvas static bundle을 build time에 생성한다.
- [x] packaged worker를 ncc ESM bundle로 만들고 nested `node_modules` 전체를 복사하지 않는다.
- [x] Puppeteer revision과 같은 Chrome for Testing `chrome-headless-shell 150.0.7871.24`를 target별 cache한다.
- [x] `runtime.json`을 root-relative path와 source/browser revision으로 작성한다.
- [x] npm package license 목록/원문과 Chromium `ABOUT`/`LICENSE.headless_shell`을 resource에 넣는다.
- [x] runtime에서 Vite/npm/browser download 없이 prebuilt static bundle을 사용한다.

지원 target mapping:

- `darwin/arm64 → mac_arm`
- `darwin/x64 → mac`
- `win32/x64 → win64`
- Linux는 현재 Electron 제품 target이 아니므로 build script가 거부한다.

### Task 12 — Electron/Nest 실행 경계

- [x] Electron이 packaged manifest path boundary와 필수 파일을 검증한다.
- [x] worker/browser/static exact path를 Nest utility process env로 전달한다.
- [x] utility process가 Electron executable로 worker를 spawn할 때 `ELECTRON_RUN_AS_NODE=1`을 설정한다.
- [x] 기존 Electron `getFfmpegPaths()`의 `FFMPEG_BIN`/`FFPROBE_BIN` 전달을 그대로 유지한다.
- [x] Motion Canvas용 FFmpeg binary/downloader/동의 UX를 새로 만들지 않는다.
- [x] Remotion source/worker/adapter/test를 삭제하거나 바꾸지 않는다.

### Task 13 — Package와 actual MP4 smoke

- [x] `npm run prepare:shortform-director -- darwin arm64`
- [x] `npm run build:app:mac:arm64`
- [x] `.app` 내부 runtime manifest와 executable bit 확인
- [x] GUI를 띄우지 않는 built Electron Node mode에서 `.app` 내부 worker/static/browser 실제 실행
- [x] 1.0초, 15fps, 320×568 MP4/H.264/AAC probe
- [x] Electron full test 165/165
- [x] Director 105개 중 103 pass, 2 opt-in skip, fail 0
- [x] source runtime actual integration 1/1
- [x] packaged Electron resource actual integration 1/1
- [x] Nest/Angular packaged/Electron/Nest ncc build

관찰 크기:

- browser 약 203MB
- worker 약 1.6MB
- static 약 204KB
- license/notice 약 3.7MB
- Shortform Director runtime 합계 약 209MB
- built `.app` 약 590MB
- DMG 약 272MB

현재 macOS arm64 산출물은 Developer ID identity가 없어 unsigned/unnotarized local build다. macOS x64/Windows x64 actual package, signed nested executable, Windows RSS, 기존 FFmpeg downloader compliance와 actual asset manual 품질은 다음 release gate다.
