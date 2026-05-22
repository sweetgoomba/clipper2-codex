# 플러그인 스토어/대시보드 설계 리뷰

작성일: 2026-04-27

## 읽은 문서

`/Users/jina/project/adlight/.claude` 아래의 모든 파일을 읽었다.

- `CLAUDE.md`
- `PLUGIN_RUNTIME_GUIDE.md`
- `TASK.md`
- `ARCHITECTURE_REVIEW.md`
- `BUILD_GUIDE.md`
- `NEXT_SESSION_PROMPT.md`
- `WORKLOG.md`
- `settings.local.json`
- `PLUGIN_STORE_DASHBOARD_DESIGN.md`

추가로 설계와 실제 구현의 접점을 확인하기 위해 다음 코드를 확인했다.

- `clipper_electron/src/shared/ipc-contract.ts`
- `clipper_electron/src/main/plugin/plugin-ipc.ts`
- `clipper_electron/src/main/plugin/plugin-manager.ts`
- `clipper_electron/src/main/plugin/plugin-process.ts`
- `clipper_electron/src/main/plugin/manifest-loader.ts`
- `clipper_electron/src/main/model-download-ipc.ts`
- `clipper_electron/src/preload/preload.ts`
- `clipper_angular/src/core/plugin-locator.ts`
- `clipper_angular/src/core/pipeline-feature-registry.ts`
- `clipper_angular/src/core/model-download.service.ts`
- `clipper_angular/src/app/app.routes.ts`
- `clipper_angular/src/app/app.component.html`
- `clipper_angular/src/shell/home/*`
- `clipper_python/plugins/*/manifest.json`

## 총평

큰 방향은 맞다. 현재 홈 화면의 "등록된 파이프라인"과 "런타임 가용"은 사용자가 기대하는 설치/실행 상태를 설명하지 못하므로, `/store`와 `/dashboard`를 분리하는 판단은 타당하다.

다만 기존 설계는 "플러그인이 설치됐다"는 말의 의미가 섞여 있고, 대시보드가 보여야 할 런타임 오류 상태를 현재 Electron 코드가 저장하지 않는다. 그대로 구현하면 UI는 생기지만 상태가 거짓으로 보일 수 있다. 특히 모델 설치 마커와 실제 모델 파일 판정은 반드시 먼저 정리해야 한다.

## 잘 잡힌 부분

- 스토어와 대시보드를 분리한 점은 좋다. 스토어는 사용 가능 상태를 만드는 화면이고, 대시보드는 이미 설치된 런타임을 운영하는 화면이어야 한다.
- 기존 `ModelDownloadService`와 `ModelConsentComponent`를 재사용하는 방향은 맞다. 다운로드 UX를 하나로 유지할 수 있다.
- `plugin.getStatus`, `plugin.start`, `plugin.stop`을 Electron IPC로 추가하는 방향도 맞다. Angular가 직접 프로세스를 판단하면 안 된다.
- 대시보드 polling을 먼저 쓰는 판단은 현실적이다. 현재는 플러그인 수가 적고, IPC push 이벤트를 설계할 만큼 복잡하지 않다.

## 반드시 보완할 부분

### 1. "설치됨"의 의미가 모호하다

현재 플러그인 코드는 앱 번들 안에 이미 들어 있다. 사용자가 스토어에서 설치한다고 느끼는 대상은 플러그인 패키지 자체가 아니라 실행에 필요한 모델/런타임 파일이다.

따라서 Phase 1에서 `installState: 'installed'`는 다음 뜻으로 고정해야 한다.

> 플러그인 manifest가 존재하고, 실행에 필요한 모델 sentinel 파일들이 실제로 디스크에 존재한다.

향후 플러그인 CDN/레지스트리가 생기면 `packageState`와 `assetState`를 분리해야 한다. 지금부터 문서와 코드 주석에 이 경계를 명시하지 않으면, 나중에 외부 플러그인 설치를 붙일 때 상태 모델이 깨진다.

### 2. 현재 `modelsNeeded` 판정식은 stale marker를 설치 완료로 오판할 수 있다

`clipper_electron/src/main/model-download-ipc.ts`의 현재 로직은 다음 형태다.

```ts
const needed = !allFilesPresent && !markerExists;
```

이 식은 `.ready` 마커가 남아 있는데 실제 모델 파일이 삭제된 경우 `needed=false`가 된다. 즉 실제 파일이 없는데도 설치 완료로 보일 수 있다.

정상 설계는 다음이어야 한다.

- 실제 모델 파일 존재 여부가 source of truth다.
- 마커는 UX 캐시이자 빠른 확인용 힌트일 뿐이다.
- 모든 실제 파일이 있으면 설치 완료다. 마커가 없으면 자동 복구한다.
- 하나라도 실제 파일이 없으면 미설치다. 마커가 있어도 stale marker로 보고 무시한다.

이 로직은 `getInstallState(pluginName)` 헬퍼로 추출해서 `modelsNeeded`와 `plugin.getStatus`가 같이 써야 한다.

### 3. 대시보드의 `error` 상태는 현재 매니저만으로 구현할 수 없다

현재 `PluginProcess`는 exit 시 내부 `proc`를 `null`로 만들지만, `PluginManager`는 "사용자가 stop해서 종료된 것"과 "프로세스가 크래시난 것"을 구분해 저장하지 않는다.

따라서 `runtimeState: 'error'`를 정확히 보여주려면 `ManagedPlugin`에 런타임 상태를 저장해야 한다.

- `starting`
- `running`
- `stopping`
- `stopped`
- `error`

그리고 exit 이벤트가 발생했을 때 다음처럼 분류해야 한다.

- `stopping` 중 exit: `stopped`
- 사용자가 요청하지 않은 exit: `error`
- health check 전 exit: `error`

### 4. `plugin.start`는 모델 동의 UX를 우회하면 안 된다

설계 문서에는 `plugin.start`가 "모델은 이미 있음"을 전제로 한다고 되어 있다. 이 전제를 IPC 핸들러에서 강제해야 한다.

`plugin.start(name)`는 `getInstallState(name)`를 먼저 호출하고, 미설치면 즉시 실패해야 한다. 여기서 플러그인을 spawn하면 라이브러리가 조용히 모델을 다운로드할 수 있고, 기존 동의 UX가 깨진다.

모델 설치를 동반하는 시작은 오직 `modelDownload.startPlugin` 경로만 허용해야 한다.

### 5. Store의 "실행하기"는 런타임 start가 아니라 화면 열기여야 한다

스토어와 대시보드를 분리한다면 스토어의 주 액션은 다음처럼 잡는 편이 안전하다.

- 미설치: `설치`
- 설치 중: 진행 표시, 취소 없음
- 설치됨: `열기`
- 실행 중: `열기`
- 오류: `대시보드에서 확인`

스토어에서 "실행하기"가 실제 `plugin.start`를 호출하면 대시보드의 역할과 섞인다. 플러그인 런타임을 수동으로 켜고 끄는 액션은 대시보드에만 두는 편이 명확하다.

### 6. 설치 중 취소는 현재 구현 범위에 없다

기존 설계의 카드 상태 표에는 `installing` 액션으로 "취소"가 적혀 있지만, 현재 `ModelDownloadService`와 Electron IPC에는 설치 취소 계약이 없다.

Phase 1에서는 설치 중 취소를 제공하지 않는 것이 맞다. 취소를 넣으려면 별도 설계가 필요하다.

- 진행 중인 `modelDownload.startPlugin` 요청 취소
- child process kill
- 부분 다운로드 파일 처리
- marker 기록 방지
- Angular progress listener 정리

### 7. Manifest 타입 매핑이 빠져 있다

Python manifest는 `display_name`이고 Angular/IPC 설계는 `displayName`이다. Electron의 `ManifestLoader` 인터페이스에는 `author`도 빠져 있다.

`plugin.getManifest`는 원본 manifest를 그대로 노출하지 말고, Renderer 전용 DTO로 변환해야 한다.

- `display_name` -> `displayName`
- `description` 기본값 처리
- `author` optional 처리
- `models[].sizeBytes` 하드코딩 보정
- `totalModelSizeBytes` 계산

### 8. Local/dev 모드 fallback이 필요하다

Angular는 Electron 밖에서도 실행된다. `window.clipperBridge`가 없을 때 `PluginStatusService`가 터지면 `npm start` UX가 깨진다.

Local/dev 모드에서는 다음처럼 단순화한다.

- `environment.pluginUrls`에 URL이 있으면 `installState='installed'`
- runtime 제어는 불가하므로 start/stop 버튼은 비활성화
- manifest 상세는 Angular의 `PipelineFeatureRegistry` 정보와 정적 모델 용량 테이블로 최소 구성

### 9. 문서 안에 실제 경로와 다른 경로가 있다

설계 문서의 일부 경로는 현재 코드와 다르다.

- `app.routes.ts` -> 실제 경로는 `clipper_angular/src/app/app.routes.ts`
- `app.component.html` -> 실제 경로는 `clipper_angular/src/app/app.component.html`
- `src/core/plugin-status.service.ts` -> 실제 경로 기준으로는 `clipper_angular/src/core/plugin-status.service.ts`

구현 문서에서는 현재 레포 구조 기준으로 경로를 적어야 한다.

### 10. `.claude/PLUGIN_RUNTIME_GUIDE.md`의 "Angular가 직접 Python에 연결하지 않는다"는 표현은 부정확하다

현재 구조에서 Angular는 `PluginLocator`로 URL을 받은 뒤 Python 플러그인의 `/jobs`와 WebSocket에 직접 HTTP/WS로 연결한다. Angular가 하지 않는 일은 프로세스 spawn/관리다.

문서 표현은 다음처럼 바꾸는 것이 정확하다.

> Angular는 Python 프로세스를 직접 관리하지 않는다. Electron IPC로 플러그인 URL만 받고, job 실행과 progress WebSocket은 로컬 Python 플러그인 HTTP API에 직접 연결한다.

## 결론

스토어/대시보드 방향은 유지하되, 구현 전에 상태 모델을 닫아야 한다. 특히 `getInstallState` 공유 헬퍼, 런타임 상태 저장, `plugin.start`의 동의 우회 방지, Store 액션의 의미 정리가 선행되어야 한다.

보완된 기준 설계는 `PLUGIN_STORE_DASHBOARD_SPEC.md`에 정리했다.

