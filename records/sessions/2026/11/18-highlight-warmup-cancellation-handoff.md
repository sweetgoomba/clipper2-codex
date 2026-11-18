# 2026년 11월 18일 대사·안무 엔진 예열 제거와 취소 정리

대사·안무의 공통 준비 단계에서 조건부 자동 예열을 제거했다. 안무의 참조 사진 검사는 기존처럼 크레딧 확인 전에 수행한다. 취소한 작업은 카드에 먼저 `취소됨`으로 표시하고, 실제 종료를 확인할 때까지 해당 작업이 쓰던 큐 자리를 유지한다.

2026년 11월 18일(KST) GitHub에서 세 PR이 모두 `dev` 대상이고 열린 상태이며 충돌이 없음을 확인했다. 이 세션은 구현·독립 검토·커밋·푸시·PR 작성까지 진행했다. 머지와 배포는 보류했으며, 실행 중인 PC와 기존 설치 파일은 보존했다.

## 왜 바꿨나

- 화면에 들어갈 때의 `check()`는 상태를 조회한다. 수정 전에도 이미 `ready`인 버튼은 바로 진행했다. `ready`가 아니어서 `ensureReady()`에 들어갈 때는 도구와 모델을 준비한 뒤 `warm`이 `/plugins/:name/start`를 호출했다. 따라서 대사의 영상 불러오기나 안무의 아티스트 감지처럼 입력을 준비하는 단계에서도 엔진이 먼저 켜질 수 있었다.
- 예열 경로는 분석 큐에 등록하기 전에 타므로 다른 작업이 실행되는 동안 시작할 수 있었다. 사용자가 영상 확인 화면에서 돌아가거나 크레딧 확인에서 취소하면, 실제 분석에 쓰이지 않는 기동 대기와 리소스 점유가 생길 수 있었다. 대사는 startup에서 주로 Whisper·OpenCLIP 파일을 확보하고, 실제 분석 모델 로딩은 분석 단계의 자식 프로세스에서 수행했다. 안무는 startup에서 얼굴·포즈 모델을 준비했다. 두 엔진의 기동 비용과 모델 재사용을 같게 볼 수 없다.
- 취소 전의 큐는 카드에 `취소됨`을 기록한 뒤 실제 실행이 끝나기 전에 다음 작업을 꺼낼 수 있었다. 원본 다운로드에는 취소 신호가 전달되지 않는 경로가 있었고, Python의 `cancelling` 응답은 중단 요청 접수를 뜻했다. 예를 들어 A 다운로드 중 취소하면 B가 시작됐는데 A가 계속 파일을 쓰는 순서가 가능했다.

## 사용자 흐름과 범위

| 흐름 | 수정 후 |
|---|---|
| 대사 하이라이트 | 영상 정보 확인 → 크레딧 확인 → 큐 등록 → 실행 차례에 엔진 기동. 엔진이 꺼져 있으면 기동 대기는 홈의 `시작 중` 단계에서 생긴다. |
| 안무 하이라이트 | 아티스트 감지·멤버 사진 선택 → 추출 버튼 → 스피너 동안 사진 검사 → 크레딧 확인 → 큐 등록. 새 사진을 판정해야 하면 검사 단계에서 안무 엔진을 켠다. |
| 실행 중 취소 | 카드에는 먼저 `취소됨`을 보여 준다. 원본 다운로드·분석·렌더가 정리됐다는 확인을 받아야 그 자리를 다음 작업에 넘긴다. 확인되지 않으면 다음 작업은 대기한다. |
| 대기 중 취소 | 큐에서 해당 작업을 제거한다. |

이미 검증해 저장한 사진은 파일·소유권을 확인해 재사용한다. 새 사진의 얼굴 판정은 CPU와 RAM을 사용하고 판정은 사진별로 직렬 진행한다. 다른 분석과 겹치면 지연 가능성이 있으나, 이 세션에서 실제 PC별 자원 사용이나 지연량을 측정하지 않았다. 사용자 결정에 따라 사진 검사 시점과 판정을 유지했고, 검사나 TTS 미리듣기를 분석 큐 뒤로 이동하는 변경은 범위에서 제외했다. 인물의 준비 동작과 TTS 미리듣기도 그대로다.

기동 시점이 뒤로 이동하므로 첫 작업 전체 완료 시간은 별도 측정이 필요하다. 설치판 기본값에서 보인 인물의 유휴 종료 설정만으로 2·3·8번 PC의 실제 설정이나 부하를 판단할 수 없다.

## 구현과 PR

세 작업 트리는 `/Users/jina/project/adlight/.worktrees/highlight-queue-cancellation-20261118/desktop` 아래에 있다. 각 저장소에서 최신 `origin/dev`로부터 `fix/highlight-queue-cancellation`을 분기했다. 커밋·푸시 후 세 PR의 head가 아래 커밋과 일치하고 서로 연결돼 있음을 확인했다. Python은 조사 기준 `53c7fccc`이며 별도 구현 커밋은 없다.

| 저장소 | 기준 dev | 구현 커밋 | PR |
|---|---|---|---|
| Angular | `e01cd780` | `457d67e6` | [Angular #20](https://github.com/OhMyMetabuzz/clipper_angular/pull/20) |
| Nest | `c6050407` | `a205854b` | [Nest #21](https://github.com/OhMyMetabuzz/clipper_nestjs/pull/21) |
| Electron | `16faddbc` | `172946e` | [Electron #7](https://github.com/OhMyMetabuzz/clipper_electron/pull/7) |

- **Angular**의 `readiness-requirements.ts`에서 대사·안무의 `warm`만 제거했다. 도구·모델 확인은 유지한다. `dialog-setup.component.ts`와 `dance-setup.component.ts`는 메모리 경고를 기존 크레딧 확인창에 전달한다. 안무는 새 사진 검사에서 엔진이 켜지기 전에 메모리 상태를 읽고, 용량 부족으로 사진 검사에 실패하면 화면에도 이유를 표시한다.
- **Nest**의 `JobsService`는 실행 경로가 끝날 때까지 큐 자리를 유지한다. 취소 상태를 저장한 뒤 중단 신호를 전달한다. 정리·크레딧 마감 중인 취소 카드와 재시도 원본 기록의 삭제를 차단한다. `SourceService`는 다운로드에 중단 신호를 전달하고, 병합 중 남은 `.temp.mp4`를 완성 소스에서 제외한다.
- **Nest**의 `plugin-job-cancellation.ts`는 Python의 작업 종료와 정리 상태를 확인한다. 접수 응답 유실, 연결 단절 및 중단 신호보다 저장소의 취소가 먼저 보이는 경우도 처리한다. 확인이 지연되면 원래 관리 프로세스에만 종료를 요청한다. FFmpeg는 같은 자식 프로세스에 중단을 다시 시도하고 `close`까지 기다린다.
- **Electron**의 `plugin-host-bridge.ts`는 기동 요청을 ID로 추적한다. 취소 쪽 확인이 먼저 도착하면 같은 ID의 늦은 요청을 차단한다. `plugin-manager.ts`는 실패한 기동의 원래 프로세스 핸들 또는 포트·PID가 일치하는 프로세스만 조건부로 정리한다. Windows 패키지에서 Nest의 취소 가능한 `yt-dlp` 실행은 기존 감독기로 하위 프로세스 종료까지 확인한다.

## 독립 검토와 검증

- 조사 단계의 독립 Codex 채팅 `01a1eb30-ca84-7702-8008-82d430dada57`에서 조건부 예열, 새 사진과 저장된 사진의 판정 차이, 취소와 실제 종료의 차이를 대조했다. 이 결과로 사진 검사를 변경 범위에서 제외했다.
- 구현 단계의 별도 읽기 전용 Codex 채팅 `01a1ed7e-dfa9-71b2-9d0c-77e835038c73`에서 정리 중 카드 삭제, 미완성 병합 파일, 접수 응답 유실, 기동 등록 경합, 구버전 브리지의 명시적 404, 저장소 취소와 중단 신호 간 경합, FFmpeg 종료 신호 실패를 검토했다. 지적된 경로를 수정하고 재검토했다. 마지막에 확인된 테스트 정리 훅의 누락 import는 보완했고 해당 테스트를 포함한 회귀 묶음을 다시 통과했다.
- PR 생성 전 재실행 결과는 Angular **231개**, Nest **225개**, Electron **38개** 통과였다. Nest·Electron TypeScript 빌드와 세 저장소의 `git diff --check`가 통과했다. Nest–Electron 로컬 연동에서 기동 전 확인 중과 실제 기동 중의 취소를 각각 시험했다.
- Windows 감독기의 제어 파이프와 종료 확인 이벤트는 모의 환경에서 검증했다. 변경된 설치본을 실제 Windows PC에 올려 취소하거나, 실행 시간·RAM 차이를 재측정하는 일은 이번 세션 범위 밖이다.

### 회귀 테스트 재현

각 명령은 해당 저장소의 작업 트리에서 실행한다. Angular는 Node 24.19.0과 로컬 Chrome을 사용했다.

```sh
# Angular
node ./node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadlessNoSandbox \
  --include=src/core/readiness/readiness.service.spec.ts \
  --include=src/core/readiness/readiness-requirements.spec.ts \
  --include=src/core/resources/memory-warning/memory-warning.service.spec.ts \
  --include=src/features/dance-highlight/pages/dance-setup/dance-setup.component.spec.ts \
  --include=src/features/dance-highlight/flow/dance-flow.store.spec.ts \
  --include=src/features/dialog-highlight/pages/dialog-setup/dialog-setup.component.spec.ts

# Nest
npm run build && node --test --test-concurrency=1 --test-timeout=15000 \
  test/jobs-flow-lifecycle.test.js test/idle-foreground-workflow.test.js test/sources-ingest-progress.test.js \
  test/dialog-highlight-workflow-executor.test.js test/dialog-highlight-python-stage-runner.test.js \
  test/sources-ytdlp-runtime.test.js test/jobs-commit-phase.test.js test/billing-archive-cancellation.test.js \
  test/storyboard-jobs-integration.test.js test/owned-child-process-registry.test.js \
  test/plugin-runtime-lifecycle-participation.test.js test/simplified-shortform-render-recipe-provider.test.js \
  test/simplified-shortform-local-ffmpeg-render-provider.test.js test/plugin-start-heartbeat.test.js \
  test/plugin-start-timeout.test.js test/local-plugin-host-start-stop-serialization.test.js \
  test/python-runtime-lifecycle-policy.test.js test/workflow-executor-registry.test.js \
  test/local-plugin-host-install-state.test.js test/local-plugin-host-exit-listener.test.js

# Electron
npm run build && node --test --test-concurrency=1 \
  test/plugin-host-bridge-error-code.test.js test/plugin-host-bridge-start-heartbeat.test.js \
  test/plugin-manager-start-stop-serialization.test.js test/plugin-manager-start-failure-reason.test.js \
  test/plugin-host-bridge-youtube-runtime.test.js test/plugin-manager-start-stall.test.js \
  test/plugin-manager-exit-listener.test.js
```

## 이어받을 때

머지·배포 보류는 사용자 지시다. 이후 승인으로 설치본을 만들 때는 Nest와 Electron 변경을 같은 앱 번들에 포함한다. 새 Nest의 기동 확인 요청을 구버전 Electron 브리지는 지원하지 않는다. 변경 번들의 Windows 실기 검증에서는 다운로드·기동·분석·렌더 중 각각 취소한 뒤, 기존 프로세스의 종료를 확인하고 다음 작업이 시작되는 순서를 본다.

팀원에게 보낼 요약은 작성했다. 전달 작업은 사용자에게 맡겼다. PR 본문에는 사용자에게 달라지는 점, 확인한 테스트와 나머지 두 PR 링크를 담았다.
