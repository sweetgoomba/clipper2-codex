# AI 숏폼 디렉터 — 무료 상용 렌더러와 지원 OS 결정

작성일: 2026-07-20 KST

상태: macOS arm64 source-checkout 및 Electron packaged 실영상 검증 완료, macOS x64·Windows x64 검증은 후속

## 결정 요약

Shortform Director의 범용 합성 기본 경로는 `director.adapter.motion-canvas-local.v1`로 전환한다.

- 사용자의 필수 조건은 **상용 사용 시 renderer 자체에 유료 라이선스나 사용량 과금이 없어야 한다**는 것이다.
- Motion Canvas core/2d/vite plugin `3.17.2`는 MIT, `puppeteer-core 25.3.0`은 Apache-2.0, `vite 5.4.21`은 MIT로 고정했다.
- isolated lockfile의 transitive package 133개를 `MIT | Apache-2.0 | BSD-2-Clause | BSD-3-Clause | ISC | 0BSD | CC0-1.0` allowlist로 검사했고 위반 0개를 확인했다.
- 기존 Remotion PoC와 application adapter 코드는 삭제하지 않는다. registry에서는 Motion Canvas 뒤의 명시적 fallback으로 보존한다.
- Remotion은 회사/사용 형태에 따라 유료 조건이 생길 수 있으므로 무료 상용 기본 renderer로 채택하지 않는다. 별도 사용자 결정과 라이선스 확인 없이는 packaged production 경로로 승격하지 않는다.
- Electron packaged build에는 source revision으로 고정한 Motion Canvas 정적 bundle, ncc 단일 worker, Puppeteer와 같은 revision의 Chrome for Testing `chrome-headless-shell 150.0.7871.24`를 넣는다.
- packaged runtime은 `npm install`, Vite build, browser download를 실행하지 않는다. FFmpeg/FFprobe는 새로 번들하지 않고 기존 Electron의 사용자 동의 후 `userData/bin` 설치·경로 전달을 그대로 재사용한다.
- 기존 `shortform_prompt`와 generic renderer는 변경하지 않는다.

이 결정은 “현재 사용 중인 모든 외부 실행 파일을 아무 조건 없이 재배포할 수 있다”는 뜻이 아니다. Node renderer dependency와 최종 browser/encoder 배포 책임을 분리한다.

## 구현 구조

```text
immutable Director execution bundle
  → exact staged input size/SHA-256 재검증
  → source-revision static bundle cache
     ├─ miss: Vite offline build + atomic promotion
     └─ hit: bundler 없이 immutable bundle 재사용
  → token-protected 127.0.0.1 static/asset server
  → Puppeteer + 지정된 Chrome/Chromium
  → Motion Canvas frame bridge
  → PNG frame image2pipe
  → 지정된 외부 FFmpeg H.264/AAC encode/audio alignment
  → FFprobe output contract
  → owner/project-scoped atomic MP4 materialization
```

Motion Canvas 공식 FFmpeg exporter인 `@motion-canvas/ffmpeg`는 포함하지 않는다.

- 현재 upstream source와 npm metadata 사이의 라이선스 표기가 일관되지 않고, exporter가 별도 FFmpeg binary 공급 경계를 가져오기 때문이다.
- 직접 구현한 frame bridge는 허용 라이선스 Node dependency만 사용한다.
- Motion Canvas worker는 FFmpeg를 직접 다운로드하거나 자체 runtime에 내장하지 않고, source에서는 명시적 executable을, packaged 앱에서는 기존 Electron downloader가 준비한 `userData/bin` path를 child process로 호출한다.

Vite는 runtime server로 사용하지 않는다. static source bundle을 만드는 offline build command로만 사용하며, 실제 렌더 중에는 custom loopback server가 method, Host, random token, asset id를 검증한다. Browser의 외부 network request도 차단한다.

packaged 경로는 source-checkout cache miss와 다르다.

```text
Electron build time
  → trusted repository source SHA-256
  → Vite static build + cache manifest
  → ncc worker bundle + npm license notices
  → pinned Chrome for Testing download/cache
  → browser ABOUT/LICENSE.headless_shell 수집
  → relocatable runtime.json
  → electron-builder extraResources

Electron installed runtime
  → runtime.json path boundary/readability/executable 검증
  → Electron → Nest env로 worker/browser/static 경로 전달
  → ELECTRON_RUN_AS_NODE=1 child worker
  → prebuilt static bundle 직접 사용(Vite/npm/network 없음)
  → 기존 app-managed FFMPEG_BIN/FFPROBE_BIN 사용
```

## 라이선스 경계

| 구성 | 현재 판단 | 제품 정책 |
|---|---|---|
| Motion Canvas core/2d/vite plugin 3.17.2 | MIT | 무료 상용 기본 합성기로 허용 |
| puppeteer-core 25.3.0 | Apache-2.0 | 허용 |
| Vite 5.4.21 | MIT | offline build에만 허용 |
| isolated npm dependency graph | 133개 모두 permissive allowlist 통과 | lockfile 변경 시 자동 재검사 |
| Remotion 4.0.489 | 사용 형태에 따라 유료 조건 가능 | 코드만 보존, 기본/packaged production 경로에서 제외 |
| Chrome for Testing headless shell 150.0.7871.24 | Chromium 계열 허용 라이선스, 배포물에 `ABOUT`과 `LICENSE.headless_shell` 포함 | Puppeteer revision과 함께 고정해 macOS arm64 package에 포함 |
| 기존 Electron app-managed FFmpeg/FFprobe | 기능 접근 시 사용자 동의 뒤 `userData/bin`에 다운로드 | Motion Canvas가 새 binary를 공급하지 않고 기존 경로를 재사용; 현재 공급물의 GPL/notice/source 의무는 앱 공통 release gate |
| 현재 로컬 FFmpeg 8.0 + libx264 | GPL 기능이 활성화된 외부 executable | source/package smoke용 실행 경로로 사용, 설치물에 새로 복제하지 않음 |

현재 FFmpeg를 subprocess로 실행해 로컬에서 상용 영상을 만드는 데 renderer 사용료가 붙는 것은 아니다. 이 앱에는 이미 `eugeneware/ffmpeg-static`의 `b6.1.1` tag와 `@ffprobe-installer` package를 기능 접근 시 내려받는 공통 설치 경계가 있다. 이번 작업은 그 downloader, 동의 UX, 파일 또는 공급 URL을 변경하지 않고 Electron이 계산한 exact path를 Nest/Motion worker에 전달했다.

따라서 “Motion Canvas 때문에 encoder를 새로 골라야 한다”가 남은 구현 단계는 아니다. 다만 기존 app-managed 공급물 자체의 GPL 고지·해당 소스 제공 방식·버전 pin/checksum과 H.264 특허 검토는 앱 전체 release compliance 항목으로 여전히 남는다. 준수 배포를 유지할지 LGPL/platform encoder로 교체할지는 별도 제품·법무 결정이며, 이 결정 전에도 실제 영상 생성 구현과 packaged 기술 smoke는 완료로 기록할 수 있지만 최종 배포 라이선스 승인은 완료로 표현하지 않는다.

## dependency 보안 잔여 조건

Motion Canvas `3.17.2`의 peer 범위 때문에 Vite 5를 사용한다. 현재 `npm audit`은 Vite/esbuild 계열 advisory 3개를 보고하며 그중 high 1개가 있다.

- 위험한 Vite development server를 실행하지 않는다.
- untrusted source code를 bundle하지 않고 repository의 고정 source만 offline build한다.
- render asset은 별도 strict loopback server가 전달한다.
- upstream이 patched Vite를 허용하면 pin을 올리고 license/conformance를 다시 실행한다.

따라서 이 항목은 현재 source renderer를 막지는 않지만 packaged release dependency gate에 남긴다.

## 지원 OS 판단

Clipper Electron의 현재 build target은 macOS arm64, macOS x64, Windows x64다. Linux는 worker 탐색 코드가 있어도 현재 제품 배포 target은 아니다.

| OS/arch | 코드 경로 | 실제 검증 | 현재 판정 |
|---|---|---|---|
| macOS arm64 | packaged ncc worker + prebuilt static + Chrome headless shell, existing FFmpeg/FFprobe path | `.app`/DMG build, `.app` 내부 resource 실제 MP4 smoke | packaged 기술 경로 검증 완료 |
| macOS x64 | 동일 build script가 `mac` Chrome target을 준비 | 미검증 | target machine packaged smoke 필요 |
| Windows x64 | 동일 build script가 `win64` Chrome target을 준비 | 미검증 | packaged smoke와 Windows process-tree sampler 필요 |
| Linux | `/usr/bin/google-chrome|chromium` 탐색 | 미검증, Electron 제품 target 아님 | 보장하지 않음 |

현재 process-tree RSS sampler는 macOS/Linux `ps` 형식이다. Windows에서는 동일한 의미의 root+recursive child 동시 RSS 합계를 별도 구현해야 한다.

지원 OS를 과장하지 않는다. macOS arm64는 packaged 기술 경로까지 검증했지만 현재 산출물은 Developer ID 서명·notarization이 없는 로컬 build다. macOS x64와 Windows x64는 target-specific packaged/offline smoke 뒤에 제품 지원을 선언한다.

## 실제 검증 결과

현재 Motion Canvas 최소 application integration:

- staged PNG 1개 + WAV 1개
- 1.0초, 15fps, 320×568
- MP4/H.264/AAC와 progress `→ 1` 재검증

대표 실행:

- 41.2초, 30fps, 1080×1920, 1,236 frame
- visual 9, narration 7, subtitle 7, text 10, sequence-card 1
- MP4/H.264/AAC, 2,072,173 bytes
- source revision `sha256:aad28738ac9d7cb12a2603681e593b933d04b7dbc810970cdb97f5cc8c0cf271`
- 첫 fixed-source run cache `created`, 동일 revision 재실행 cache `reused`
- cache-hit elapsed 21,037ms
- 106 samples, peak process count 9
- root+Chrome+FFmpeg child-tree peak RSS 1,941,848,064 bytes
- representative frame 4개를 확인했고 초기 text line-height 겹침을 수정한 뒤 headline/diagram/subtitle safe separation을 재확인

자동 검증:

- Motion Canvas PoC/adapter tests 포함 Director suite: 105개 중 103 pass, 2 opt-in integration skip, fail 0
- 실제 source runtime Motion Canvas integration: 1 pass
- 실제 `.app` 내부 worker/static/browser + Electron Node mode Motion Canvas integration: 1 pass
- Electron 전체: 165/165
- Angular Director focused suite: 29/29
- isolated license gate: 133 packages, violation 0
- Nest TypeScript build와 `ncc` bundle, Electron TypeScript, Angular packaged build, macOS arm64 `.app`/DMG: pass
- packaged Motion Canvas resource: 약 209MB(browser 약 203MB, worker 약 1.6MB, static 약 204KB, notices 약 3.7MB)
- built `.app`: 약 590MB, DMG 약 272MB
- Nest 전체 659개 baseline은 Director 밖 기존 fixture/config/mock 문제 61개가 남아 596 pass, 61 fail, 2 skip이다. Director 105개는 독립적으로 fail 0이며 이 작업에서 legacy plugin 실패를 수정하지 않았다.

## 다음 release 경계

1. macOS x64와 Windows x64에서 이미 구현한 managed Chromium package를 실제 build/run하고 offline MP4 smoke를 수행한다.
2. Windows recursive process-tree RSS sampler를 구현한다.
3. macOS signing/notarization 환경에서 nested headless-shell 실행과 third-party notice 포함을 다시 확인한다.
4. 기존 app-managed FFmpeg/FFprobe downloader의 license/source notice, exact version/checksum과 H.264 compliance를 앱 공통 release gate로 감사한다.
5. 약 1.94GB인 대표 peak RSS와 package 증분 약 209MB를 낮추되 output/conformance를 유지하는지 측정한다. Electron 내장 Chromium 재사용은 별도 refactor 후보일 뿐 현재 verified 경로를 삭제하지 않는다.
6. 실제 브랜드 asset/audio로 manual 7축을 수행한다.
7. 위 결과가 안정될 때까지 Remotion 코드는 fallback/비교 증거로 보존하며 삭제하지 않는다.

## 공식 근거

- [Motion Canvas repository license](https://github.com/motion-canvas/motion-canvas/blob/main/LICENSE)
- [Motion Canvas rendering](https://motioncanvas.io/docs/rendering/)
- [Motion Canvas video rendering](https://motioncanvas.io/docs/rendering/video/)
- [Puppeteer license](https://github.com/puppeteer/puppeteer/blob/main/LICENSE)
- [Vite license](https://github.com/vitejs/vite/blob/main/LICENSE)
- [Remotion license and pricing](https://www.remotion.dev/docs/license/pricing)
- [FFmpeg legal information](https://ffmpeg.org/legal.html)
- [FFmpeg license and legal considerations](https://ffmpeg.org/doxygen/trunk/md_LICENSE.html)
- [Chromium license](https://chromium.googlesource.com/chromium/src/+/main/LICENSE)
