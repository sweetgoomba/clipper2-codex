# AI 숏폼 디렉터 — Renderer 역할 분담과 첫 PoC 결정

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_CONFORMANCE_AND_BENCHMARK_ACCEPTANCE_DESIGN_2026-07-16.md`

## 결론

이번 단계에서 production renderer를 확정하지 않는다. 대신 역할과 검증 순서를 다음처럼 고정한다.

| 역할 | 현재 결정 |
|---|---|
| 범용 영상 합성 | **Remotion을 첫 비프로덕션 PoC 후보**로 검증 |
| 범용 영상 합성 대안 | Motion Canvas는 Remotion의 packaging·license·quality gate 실패 시 두 번째 PoC |
| 최종 probe·thumbnail·필요한 mux/normalize | 기존 app-managed FFmpeg/ffprobe 유지 |
| 간단한 diagram·text motion | 메인 합성기가 `programmaticMotion`을 직접 구현 |
| 정밀한 기술·수학·관계 도식 | Manim을 **선행 artifact materializer** 후보로 유지 |
| 자동 graph layout | SVG + Graphviz/Mermaid 계열을 diagram source generator로 검토 |
| 반복형 브랜드 모션 | Lottie/Rive를 재사용 motion asset으로 검토 |

Remotion, Motion Canvas, FFmpeg를 서로 대체하는 세 선택지로 보지 않는다. 메인 합성, 전문 도식 생성, 최종 미디어 처리라는 서로 다른 역할로 나눈다.

## 현재 Clipper2 runtime 감사

### Angular

- Angular 19이며 React dependency가 없다.
- Director preview는 RenderRecipe의 `programmaticMotion`을 읽는 Angular DOM/CSS inspector다.
- `diagram.sequence-card.v1`의 start/reveal/hold/exit/end semantic frame을 이미 같은 계약에서 소비한다.

따라서 첫 PoC에서 `@remotion/player`를 Angular에 넣지 않는다. React preview를 제품 UI에 섞기 전에 final render 적합성을 먼저 검증한다.

### NestJS

- packaged app에서는 NestJS가 `ncc` single bundle로 만들어져 Electron `utilityProcess`에서 실행된다.
- Director adapter는 immutable execution bundle만 소비하며 production registration은 0개다.
- current simplified FFmpeg provider는 영상·이미지 concat, TTS/BGM audio mix, 일부 title과 caption은 처리하지만 arbitrary composition layer와 `programmaticMotion`은 처리하지 않는다.

Remotion runtime과 native compositor package를 현재 Nest `ncc` bundle 안에 바로 넣지 않는다. Remotion 공식 문서도 composition bundle은 소스 변경 시 한 번 만들고 영상마다 다시 만들지 말라고 하며, Electron 같은 bundled 환경에서는 별도 binaries directory가 필요할 수 있다고 설명한다.

### Electron

- Angular SPA, Nest bundle, Python source는 모두 ASAR 밖의 `extraResources`로 패키징된다.
- Electron은 app-managed FFmpeg/ffprobe를 사용자 동의 경계 뒤에서 설치하고 Nest와 Python plugin에 경로를 전달한다.
- macOS arm64/x64와 Windows x64 패키징 경로가 존재한다.

따라서 후보 renderer가 브라우저나 native binary를 런타임에 몰래 내려받아서는 안 된다. production 전환 시 renderer bundle과 platform binary를 build-time resource로 넣거나, 별도의 명시적 설치 동의 흐름을 설계해야 한다.

### Python plugin

- packaged Python plugin은 plugin별 독립 venv를 사용할 수 있다.
- Manim을 도입하더라도 공용 Python base environment나 기존 `clipper_video_render`에 바로 섞을 필요는 없다.
- Manim Community는 현재 Python/uv 설치를 지원하지만 Cairo/Pango 계열 dependency와 optional LaTeX가 packaging 비용이 된다.

## 후보 비교

### Remotion

Remotion은 React component를 시간에 따라 frame으로 평가하고 Chromium 기반으로 렌더한 뒤 media로 encode한다.

현재 Director와 맞는 점:

- `RenderRecipe`를 JSON input props로 전달할 수 있다.
- image/video/audio, typography, SVG, Canvas, captions와 layered composition을 한 renderer에서 다루기 쉽다.
- Node API가 full media와 still/frame render를 제공한다.
- progress callback과 cancel signal이 공식 API에 있다.
- `diagram.sequence-card.v1`처럼 normalized motion state를 frame number에 투영하기 쉽다.
- composition source가 같다면 다양한 project 입력을 같은 prebuilt bundle로 렌더할 수 있다.

주의점:

- Angular 제품에 React preview를 바로 공유할 수 없다.
- Chromium, Remotion compositor binary와 native library의 packaged resource 구성이 필요하다.
- 공식 current system requirement는 macOS 15+, Linux glibc 2.35+이며 Alpine/nixOS를 지원하지 않는다.
- 공식 문서상 Electron은 `binariesDirectory`가 필요한 bundled/unsupported 환경의 예다.
- 회사 규모와 사용 형태에 따라 Company License가 필요하고 자동 영상 생성 앱은 usage-based 조건을 검토해야 한다.
- Remotion 내부 FFmpeg 명령을 `ffmpegOverride`로 app-managed FFmpeg에 강제로 맞추는 방식은 공식 문서가 변경 위험을 경고하므로 사용하지 않는다.

판정:

- **첫 메인 합성 PoC에 가장 적합하다.**
- production 채택은 license, packaged binary size, offline startup, Windows와 지원 macOS 범위 검증 뒤에만 가능하다.

공식 근거:

- [Remotion server-side rendering](https://www.remotion.dev/docs/ssr)
- [Remotion renderMedia](https://www.remotion.dev/docs/renderer/render-media)
- [Remotion bundle](https://www.remotion.dev/docs/bundle)
- [Remotion Player](https://www.remotion.dev/docs/player)
- [Remotion system requirements](https://www.remotion.dev/docs/)
- [Remotion license and pricing](https://www.remotion.dev/docs/license/pricing)

### Motion Canvas

Motion Canvas는 TypeScript generator와 Canvas 기반 scene graph로 정보 전달형 vector animation을 만든다.

현재 Director와 맞는 점:

- node, connector, path, chart, text처럼 도식 중심 장면을 표현하기 좋다.
- TypeScript로 현재 normalized motion contract를 옮기기 쉽다.
- browser editor에서 real-time preview를 제공한다.
- MIT License다.

주의점:

- 공식 구조는 Vite development server와 browser runtime/editor의 결합이다.
- 공식 기본 rendering은 browser에서 image sequence를 만들고, FFmpeg exporter가 Node 쪽에서 영상을 만드는 구조다.
- FFmpeg exporter는 공식 문서에서도 비교적 새 기능이며 필요한 모든 기능이 없을 수 있다고 명시한다.
- packaged Electron 안에서 headless automation, progress/cancel, output probing을 제품 수준으로 묶는 경로가 Remotion Node API보다 덜 직접적이다.
- 공식 repository가 표시하는 최신 tagged release는 현재 v3.17.2, 2024-12-14이므로 production 채택 전 release와 dependency health를 별도 확인해야 한다.

판정:

- **좋은 도식 renderer이자 메인 합성 대안**이다.
- 첫 PoC에서 Remotion과 동시에 전체 adapter를 두 개 만들지 않는다.
- Remotion이 packaging·license·manual quality gate를 통과하지 못하거나 vector scene authoring이 병목일 때 두 번째 PoC로 올린다.

공식 근거:

- [Motion Canvas introduction](https://motioncanvas.io/docs/)
- [Motion Canvas rendering](https://motioncanvas.io/docs/rendering/)
- [Motion Canvas FFmpeg exporter](https://motioncanvas.io/docs/rendering/video/)
- [Motion Canvas plugin architecture](https://motioncanvas.io/docs/plugins/)
- [Motion Canvas repository](https://github.com/motion-canvas/motion-canvas)

### 기존 FFmpeg

FFmpeg는 현재 앱에서 가장 검증된 media runtime이다.

현재 Director와 맞는 점:

- app-managed 설치와 Nest/Python 경로 주입이 이미 있다.
- codec, mux, audio mix, normalization, thumbnail, probe에 적합하다.
- process signal로 취소할 수 있고 stderr/progress를 application progress로 바꿀 수 있다.
- current local providers가 filter graph와 output artifact materialization 선례를 제공한다.

한계:

- 복잡한 layer hierarchy와 reusable motion primitive를 filter expression으로 표현하면 유지보수 비용이 급격히 커진다.
- browser preview와 동일한 typography/layout engine이 아니다.
- current simplified provider는 Director composition layer와 sequence-card motion을 지원하지 않는다.

판정:

- **메인 quality-first compositor 후보에서는 제외한다.**
- codec/output baseline, 최종 probe, thumbnail, 필요한 audio mux/normalize 역할은 유지한다.
- Remotion 결과가 이미 MP4/H.264/AAC 계약을 만족하면 불필요한 재인코딩은 하지 않고 probe와 thumbnail만 수행할 수 있다.

공식 근거:

- [FFmpeg filter documentation](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg command documentation](https://ffmpeg.org/ffmpeg.html)

### Manim

Manim은 Python scene, mobject와 animation을 이용해 정밀한 기술·수학 애니메이션을 만든다.

현재 Director와 맞는 점:

- graph/network, plot, chart, table, formula, geometry transformation에 강하다.
- frame rate, resolution, output format과 deterministic seed를 제어할 수 있다.
- Python plugin별 독립 venv라는 현재 Electron 경계와 연결할 수 있다.

메인 compositor로 쓰지 않는 이유:

- 일반 UGC footage, 광고형 subtitle, CTA, brand layout, 다중 media timeline 전체를 맡기기에는 과하다.
- browser 기반 live preview와 직접 공유되지 않는다.
- Cairo/Pango와 optional LaTeX는 packaged install과 앱 크기를 키운다.

가장 중요한 실행 경계:

```text
잘못된 경계
  main renderer가 final render 중 Manim을 즉석 호출
    → retry 때 결과가 바뀔 수 있음
    → immutable stage fingerprint에 생성 bytes가 없음

선택한 경계
  complex diagram spec
    → Manim materialization job
    → checksum을 가진 video/image-sequence artifact
    → AssetPack binding
    → immutable render-input stage
    → main compositor는 staged artifact만 소비
```

`diagram.sequence-card.v1`은 메인 compositor가 직접 처리할 만큼 단순하므로 첫 41.2초 benchmark에서 Manim을 호출하지 않는다. graph, formula, plot 또는 복잡한 관계 변화가 필요한 두 번째 전문 diagram fixture가 생길 때 Manim 전용 PoC를 수행한다.

공식 근거:

- [Manim Community documentation](https://docs.manim.community/en/stable/)
- [Manim installation](https://docs.manim.community/en/stable/installation.html)
- [Manim configuration and rendering](https://docs.manim.community/en/stable/guides/configuration.html)
- [Manim graph API](https://docs.manim.community/en/stable/reference/manim.mobject.graph.Graph.html)

## 선택한 hybrid rendering 흐름

```text
PlanningContext + ContentStrategy
                ↓
             VideoPlan
                ↓
    RenderRecipe compiler / asset router
       │
       ├─ footage·image·audio
       │      → AssetPack binding
       │
       ├─ simple text·sequence-card
       │      → RenderRecipe programmaticMotion
       │
       └─ future complex technical diagram
              → Manim or specialist materializer
              → checksummed project artifact
              → AssetPack binding
                ↓
        immutable render-input stage
                ↓
   main compositor adapter — first PoC: Remotion
       ├─ staged image/video/WAV
       ├─ captions and text roles
       ├─ simple programmatic motion
       └─ staged specialist diagram artifact
                ↓
        candidate MP4/H.264/AAC
                ↓
     ffprobe contract verification
       ├─ compliant → thumbnail + materialize
       └─ needs finalization → FFmpeg mux/normalize
```

## Preview 결정

첫 PoC에서는 preview와 final renderer component를 합치지 않는다.

```text
같은 RenderRecipe + same motion contract
        ├─ Angular DOM/CSS preview
        └─ Remotion final/still render
```

- Angular preview는 현재 구현을 유지한다.
- Remotion Player를 Angular application dependency로 추가하지 않는다.
- preview/final parity는 5개 reference frame의 semantic checksum과 candidate still 비교로 검증한다.
- Remotion이 production 후보가 된 뒤에만 isolated React player, Web Component/iframe 또는 rendered still preview 중 어떤 방식이 필요한지 재검토한다.

## 첫 PoC 범위

첫 PoC는 production adapter가 아니라 명시적으로 실행하는 isolated benchmark harness다.

### 입력

- current representative 41.2초 private execution bundle fixture
- staged image 4, video 2, narration WAV 7
- visual timeline 9, subtitle 7, overlay 11, composition layer 20
- `diagram.sequence-card.v1` semantic checkpoint 5개

### 구현 원칙

- Remotion project는 Nest `ncc` bundle과 분리한다.
- composition bundle은 source revision당 한 번 build하고 render마다 다시 bundle하지 않는다.
- benchmark process에만 private staged path를 전달하고 report에는 opaque staged input id만 남긴다.
- browser/compositor/native binary revision을 고정한다.
- runtime auto-download를 production path로 허용하지 않는다.
- full MP4와 5개 checkpoint still을 생성한다.
- progress와 cancel을 adapter contract에 연결할 수 있는지 확인한다.
- ffprobe observed output과 current conformance evaluator를 사용한다.
- 같은 environment id에서 elapsed, output bytes와 peak RSS를 기록한다.
- production registry, JobsService, API, Angular render button과 operation charge를 연결하지 않는다.

### 통과 gate

1. current automated conformance exact pass
2. checkpoint still에서 text clipping과 mobile safe-zone 치명 오류 없음
3. manual 7축 review 완료
4. runtime network download 없이 재실행 가능
5. macOS arm64 dev benchmark 재현
6. production 검토 전 Windows x64와 supported macOS 범위 packaging plan이 설명 가능
7. Remotion commercial license 적용 여부와 예상 운영비 확인

## 첫 PoC 실제 결과

같은 날 isolated package와 representative benchmark harness를 구현해 다음 흐름을 실제로 검증했다.

```text
immutable representative recipe/stage
        ↓
path-safe Remotion input props
        ↓
5 checkpoint still + raw MP4
        ↓
ffprobe
        ├─ exact contract
        │     → final candidate
        └─ AAC padding 등 finalization 필요
              → FFmpeg video copy
              + audio trim/re-encode
              + remux
                    ↓
          final ffprobe + conformance evaluator
```

결과:

- Remotion `4.0.489`, React/React DOM `19.2.7`을 Nest root와 분리된 nested private package에 고정했다.
- synthetic staged image 4, video 2, WAV 7의 exact 13개 입력을 loopback-only asset server로 제공했다.
- 41.2초, 30fps, 1080×1920, MP4/H.264/AAC 최종 출력이 만들어졌다.
- visual 9, TTS 7, subtitle 7, overlay 11, composition layer 20이 profile과 일치했다.
- sequence-card 5개 semantic checksum이 current sampler와 exact match했다.
- progress와 AbortSignal cancel bridge가 실제 render에서 동작했다.
- 자동 check 7개는 모두 pass했고 상태는 의도대로 `manual_review_required`다.
- raw Remotion 결과의 video는 41.2초였지만 AAC/container가 41.258667초여서 한 frame tolerance를 넘었다.
- 이 경우에만 FFmpeg가 video stream을 copy하고 audio를 41.2초로 trim/re-encode해 remux했다. 따라서 FFmpeg를 조건부 finalizer로 둔 역할 결정이 실제 필요로 확인됐다.
- renderer spot check에서 Korean glyph clipping, mobile safe-zone 이탈과 sequence-card state 파손은 보이지 않았다.
- synthetic media/tone 기반이므로 콘텐츠 품질 manual 7축 전체 pass로 간주하지 않는다.

현재 PoC 관찰값:

- pipeline elapsed 74,257ms
- final output 8,082,314 bytes
- render progress callback 1,244회
- nested install tree 약 270MB
- macOS arm64 compositor package 약 17MB
- development composition bundle 약 20MB

PoC 성공은 production 채택이 아니다. composition bundle cache/reuse, child-process RSS, Electron packaged resource, Windows와 지원 macOS 범위, license와 실제 asset 기반 manual review가 남아 있다.

### Electron packaging 후보 경계

아직 구현하지 않지만 production 검토 시 resource ownership은 다음 모양을 우선한다.

```text
Electron extraResources
  renderer/
    remotion/
      composition/<source-revision>/
      compositor/<platform-arch>/
      browser/<platform-arch>/        # bundled 또는 명시적 설치 동의

Electron/Nest-owned worker launch
  → composition bundle path
  → browserExecutable
  → binariesDirectory
  → private staged input resolver
```

- Nest `ncc` bundle 안에 Remotion native package나 browser를 인라인하지 않는다.
- production runtime에서 renderer가 임의로 browser/native binary를 내려받지 않는다.
- macOS arm64 이후 Windows x64, 실제 지원할 macOS 최소 버전 순으로 packaged smoke한다.
- app-managed browser를 새로 공급할지 기존 설치 동의 흐름과 통합할지는 아직 결정하지 않는다.

## 순차 비교를 택한 이유

처음부터 Remotion과 Motion Canvas adapter를 모두 production 수준으로 만들면 다음 중복이 생긴다.

- input mapping 두 벌
- media path resolver 두 벌
- progress/cancel bridge 두 벌
- packaging binary 두 벌
- frame capture/report bridge 두 벌

현재 가장 큰 불확실성은 “Remotion이 Clipper2 packaged runtime에서 실제로 성립하는가”다. 이를 먼저 작은 harness로 제거한다.

```text
Remotion viability pass
  → manual quality 확인
  → production candidate 검토
  → 비교가 실제 의사결정에 필요할 때만 Motion Canvas PoC

Remotion packaging/license/quality fail
  → Motion Canvas PoC 승격

simple diagram은 pass하지만 technical diagram 품질 부족
  → main compositor는 유지
  → Manim specialist materialization PoC 추가
```

## 아직 확정하지 않은 것

- Remotion production 채택
- Remotion Company License 필요 여부와 계약
- packaged browser/compositor binary 공급 방식과 앱 크기
- minimum supported macOS version 조정 여부
- renderer process를 Electron이 직접 소유할지 Nest child worker로 둘지
- Motion Canvas 두 번째 benchmark 실행 여부
- Manim artifact media format을 transparent video와 image sequence 중 무엇으로 할지
- complex diagram contract와 materialization operation
- output artifact retention과 stage GC

## 역할 결정 이후에도 남은 비범위

- production adapter 등록
- 기존 `shortform_prompt`와 기존 Python renderer 변경
- Angular React dependency 추가
- JobsService/API/UI/operation charge 연결
- Electron packaged build와 앱 실행
- composition bundle production cache와 artifact retention/GC
- Windows x64와 지원 macOS 범위 packaged smoke
- 실제 asset/audio 기반 manual 7축 최종 판정
- commit/push/deploy
