# 플러그인 스토어/대시보드 보완 설계

작성일: 2026-04-27

## 목표

현재 `/home`을 `/store`로 교체하고, 설치된 플러그인 런타임을 조작하는 `/dashboard`를 추가한다.

- `/store`: 사용자가 플러그인을 사용할 준비를 하는 화면
- `/dashboard`: 설치된 플러그인 프로세스를 시작/중지하고 상태를 보는 화면
- `/dance`, `/dialog`: 기존 파이프라인 UI 유지

## 용어 정의

### Plugin package

앱 번들 안에 포함된 Python 플러그인 소스와 manifest다. 현재 Phase 1에서는 이미 앱에 포함되어 있으므로 사용자가 별도로 설치하지 않는다.

### Plugin assets

플러그인 실행에 필요한 모델 파일과 런타임 데이터다. 현재 사용자가 "설치"한다고 느끼는 대상은 이것이다.

예:

- `dance_highlight`: `yolov8s-pose.pt`, `insightface buffalo_l`
- `dialog_highlight`: `faster-whisper-small`, `open-clip ViT-B-32`

### Install state

Phase 1의 `installState`는 plugin package 설치 여부가 아니라 plugin assets 준비 여부를 뜻한다.

```ts
export type PluginInstallState = 'not_installed' | 'installed';
```

미래 CDN 플러그인 설치를 붙일 때는 아래처럼 분리한다.

```ts
type PluginPackageState = 'not_present' | 'present' | 'update_available';
type PluginAssetState = 'missing' | 'ready';
```

### Runtime state

대시보드가 보여주는 프로세스 상태다. 기존 3-state로는 UI command pending과 crash를 정확히 표현하기 어렵기 때문에 5-state를 쓴다.

```ts
export type PluginRuntimeState =
  | 'stopped'
  | 'starting'
  | 'running'
  | 'stopping'
  | 'error';
```

## IPC 계약

`clipper_electron/src/shared/ipc-contract.ts`에 추가한다.

```ts
export const IPC = {
  plugin: {
    list: 'clipper:plugin:list',
    getUrl: 'clipper:plugin:getUrl',
    getManifest: 'clipper:plugin:getManifest',
    getStatus: 'clipper:plugin:getStatus',
    start: 'clipper:plugin:start',
    stop: 'clipper:plugin:stop',
  },
  // ...
} as const;

export interface PluginManifestView {
  name: string;
  version: string;
  displayName: string;
  description: string;
  author?: string;
  models: Array<{
    name: string;
    source?: 'library' | 'cdn' | 'local';
    sizeBytes?: number;
  }>;
  totalModelSizeBytes?: number;
}

export interface PluginStatus {
  name: string;
  installState: PluginInstallState;
  runtimeState: PluginRuntimeState;
  port?: number;
  pid?: number;
  message?: string;
  lastExitCode?: number | null;
  startedAt?: string;
  updatedAt: string;
}
```

IPC 메서드 의미는 다음으로 고정한다.

| 메서드 | spawn 여부 | 의미 |
|---|---:|---|
| `plugin.list()` | 아니오 | 디스크에서 발견된 plugin package 이름 목록 |
| `plugin.getManifest(name)` | 아니오 | Renderer용 manifest DTO 반환 |
| `plugin.getStatus(name)` | 아니오 | asset 설치 상태 + runtime 상태 snapshot 반환 |
| `plugin.start(name)` | 예 | 이미 설치된 플러그인만 시작. 미설치면 실패 |
| `plugin.stop(name)` | 아니오 | 실행 중이면 중지. 이미 중지 상태면 no-op |
| `plugin.getUrl(name)` | 예 | 기존 파이프라인 실행 경로. ensureStarted 후 URL 반환 |

중요한 제약:

- `plugin.getStatus`는 절대 프로세스를 시작하지 않는다.
- `plugin.start`는 절대 모델 다운로드 동의를 우회하지 않는다.
- 모델 설치를 동반하는 spawn은 `modelDownload.startPlugin`만 허용한다.

## 설치 상태 판정

`clipper_electron/src/main/model-download-ipc.ts`에 있는 모델 파일 확인 로직을 공유 헬퍼로 뺀다.

권장 파일:

```text
clipper_electron/src/main/plugin/plugin-install-state.ts
```

권장 타입:

```ts
export interface PluginInstallStateSnapshot {
  pluginName: string;
  installState: PluginInstallState;
  markerPath: string;
  markerExists: boolean;
  modelPaths: string[];
  presentFiles: string[];
  missingFiles: string[];
}

export function getPluginInstallState(pluginName: string): PluginInstallStateSnapshot;
```

판정 규칙:

| 실제 모델 파일 | 마커 | 결과 |
|---|---|---|
| 모두 있음 | 있음 | `installed` |
| 모두 있음 | 없음 | marker 자동 복구 후 `installed` |
| 하나 이상 없음 | 없음 | `not_installed` |
| 하나 이상 없음 | 있음 | stale marker로 보고 `not_installed` |

현재 코드의 `needed = !allFilesPresent && !markerExists`는 고쳐야 한다. 정상식은 모델 파일 기준이다.

```ts
const installState = allFilesPresent ? 'installed' : 'not_installed';
const needed = installState === 'not_installed';
```

개발 모드에서는 라이브러리가 개발자 로컬 캐시를 쓰므로 모델 설치 UX를 강제하지 않는다.

```ts
if (!app.isPackaged) {
  return {
    installState: 'installed',
    markerExists: false,
    modelPaths: [],
    presentFiles: [],
    missingFiles: [],
  };
}
```

## 모델 용량

Phase 1에서는 Electron에 하드코딩한다. 총량만 넣지 말고 모델별로 넣어야 상세 패널이 자연스럽다.

```ts
const MODEL_SIZE_BYTES: Record<string, Record<string, number>> = {
  dance_highlight: {
    'yolov8s-pose': 22_000_000,
    'insightface-buffalo_l': 500_000_000,
  },
  dialog_highlight: {
    'faster-whisper-small': 500_000_000,
    'open-clip-ViT-B-32': 600_000_000,
  },
};
```

이 값은 사용자에게 "약 N MB/GB"로 표시한다. 정확한 billing/검증 값이 아니라 다운로드 동의 UX를 위한 안내값이다.

## PluginManager 런타임 상태

현재 `ManagedPlugin`에 상태 이력이 없으므로 추가해야 한다.

```ts
interface ManagedPlugin {
  readonly manifest: PluginManifest;
  readonly pluginDir: string;
  process: PluginProcess | null;
  port: number | null;
  runtimeState: PluginRuntimeState;
  lastError?: string;
  lastExitCode?: number | null;
  startedAt?: string;
  stoppingByRequest: boolean;
}
```

`PluginProcess`에는 `pid` getter를 추가한다.

```ts
get pid(): number | undefined {
  return this.proc?.pid;
}
```

상태 전이는 다음을 따른다.

```text
stopped --start--> starting --health ok--> running
starting --health fail/exit--> error
running --unexpected exit--> error
running --stop--> stopping --exit--> stopped
error --start--> starting
```

`PluginManager` 또는 `LocalPluginManager`는 status snapshot 메서드를 제공한다.

```ts
async getRuntimeStatus(name: string): Promise<{
  runtimeState: PluginRuntimeState;
  port?: number;
  pid?: number;
  message?: string;
  lastExitCode?: number | null;
  startedAt?: string;
}>;
```

`plugin-ipc.ts`는 manager의 private map에 직접 접근하지 말고 이 snapshot 메서드만 사용한다.

## Store 화면

라우트:

```ts
{ path: '', redirectTo: 'store', pathMatch: 'full' },
{ path: 'store', loadComponent: () => import('../shell/store/store.component').then(m => m.StoreComponent) },
{ path: 'dashboard', loadComponent: () => import('../shell/dashboard/dashboard.component').then(m => m.DashboardComponent) },
{ path: 'home', redirectTo: 'store' },
```

Store의 목록 소스:

1. Electron 모드: `plugin.list()`로 발견된 manifest를 기준으로 한다.
2. Angular에 route가 있는 플러그인은 `열기` 액션을 제공한다.
3. manifest는 있지만 Angular route가 없는 플러그인은 `지원되지 않는 UI` 상태로 표시하고 실행 버튼은 비활성화한다.
4. Local/dev 모드: `PipelineFeatureRegistry.declaredFeatures`와 `environment.pluginUrls`를 기준으로 최소 표시한다.

카드 상태와 액션:

| 상태 | 표시 | 주 액션 |
|---|---|---|
| `not_installed` | 미설치 | `설치` |
| 설치 진행 중 | 진행률 overlay | 카드 버튼 비활성화 |
| `installed` + `stopped` | 설치됨 | `열기` |
| `installed` + `running` | 실행 중 | `열기` |
| `error` | 오류 | `대시보드에서 확인` |

스토어의 `열기`는 런타임 start가 아니라 Angular feature route 이동이다.

```ts
dance_highlight -> /dance
dialog_highlight -> /dialog
```

설치 흐름:

```text
설치 클릭
  -> ModelDownloadService.check(pluginName)
  -> needed=true면 기존 ModelConsentComponent 표시
  -> confirm은 modelDownload.startPlugin 호출
  -> 완료 후 marker 기록, 플러그인 running 상태
  -> PluginStatusService.refreshOne(pluginName)
```

설치 중 취소는 Phase 1에 넣지 않는다. 취소 버튼을 보여주면 안 된다.

## Dashboard 화면

대시보드는 모든 known plugin을 보여준다. 미설치 플러그인도 회색 상태로 보여주되 start는 비활성화한다.

| installState | runtimeState | 표시 | 액션 |
|---|---|---|---|
| `not_installed` | any | 모델 미설치 | `스토어에서 설치` |
| `installed` | `stopped` | 중지됨 | `시작` |
| `installed` | `starting` | 시작 중 | 비활성화 |
| `installed` | `running` | 실행 중, port/pid 표시 | `중지` |
| `installed` | `stopping` | 중지 중 | 비활성화 |
| `installed` | `error` | 오류, message 표시 | `다시 시작` |

갱신 정책:

- 페이지 진입 시 `refreshAll()`
- 3초 polling
- start/stop 클릭 후 즉시 `refreshOne(name)`
- 컴포넌트 destroy 시 polling 정리
- `plugin.getUrl`은 사용하지 않는다. 대시보드 조회가 플러그인을 시작하면 안 된다.

## Angular 서비스

권장 파일:

```text
clipper_angular/src/core/plugin-status.service.ts
```

역할:

- manifest와 status 캐시
- `refreshAll()`
- `refreshOne(name)`
- `start(name)`
- `stop(name)`
- store/dashboard가 공유하는 signals 제공

권장 상태:

```ts
interface PluginStoreItem {
  name: string;
  manifest: PluginManifestView;
  status: PluginStatus;
  route?: string;
  uiSupported: boolean;
}
```

Electron bridge가 없을 때는 local fallback을 제공한다.

- status 조회 실패가 앱 전체 오류가 되면 안 된다.
- start/stop은 Electron 전용 기능으로 처리한다.

## Navigation

`clipper_angular/src/app/app.component.html`에 상단 nav를 둔다.

```html
<app-nav />
<router-outlet />
```

`NavComponent`는 다음만 책임진다.

- `/store` 링크
- `/dashboard` 링크
- 현재 route active 표시

파이프라인 화면의 기존 `홈` 버튼은 `/store`로 바꾼다.

```ts
void this.router.navigate(['/store']);
```

## 구현 순서

### Phase 1: Electron 상태 계약

1. `ipc-contract.ts`에 manifest/status/start/stop 타입과 채널 추가
2. `plugin-install-state.ts` 추가
3. `model-download-ipc.ts`가 새 install state helper를 사용하도록 변경
4. `PluginProcess.pid` getter 추가
5. `PluginManager` runtime state 저장과 snapshot 메서드 추가
6. `plugin-ipc.ts`에 `getManifest`, `getStatus`, `start`, `stop` 핸들러 추가
7. `preload.ts` bridge 확장

### Phase 2: Angular 상태 서비스와 Store

1. `plugin-locator.ts`의 `ClipperBridge` 타입 확장
2. `plugin-status.service.ts` 추가
3. `shell/store/*` 추가
4. 기존 `ModelConsentComponent`를 store에서도 표시
5. `/` -> `/store`, `/home` -> `/store` 라우팅 변경

### Phase 3: Dashboard

1. `shell/dashboard/*` 추가
2. start/stop 액션 연결
3. 3초 polling과 destroy cleanup 구현
4. 오류 상태 message 표시

### Phase 4: 정리

1. `shell/home/*` 제거
2. dance/dialog의 `홈` 버튼을 `/store`로 변경
3. `.claude/PLUGIN_RUNTIME_GUIDE.md`의 Angular/Python 직접 연결 표현 수정

## 테스트 체크리스트

Electron:

- marker 없음 + 모델 파일 있음 -> marker 복구, `installed`
- marker 있음 + 모델 파일 없음 -> `not_installed`
- `plugin.getStatus`가 plugin을 spawn하지 않음
- 미설치 상태에서 `plugin.start` 호출 -> 실패
- `modelDownload.startPlugin` 완료 후 marker 기록 및 status `installed/running`
- running plugin stop -> `stopped`
- running plugin unexpected exit -> `error`

Angular:

- `/` 진입 시 `/store`로 이동
- Store 설치 버튼이 기존 모델 동의 overlay를 띄움
- 설치 완료 후 Store 상태가 갱신됨
- Store `열기`가 `/dance` 또는 `/dialog`로 이동하고 runtime start를 직접 호출하지 않음
- Dashboard start/stop 버튼이 상태별로 활성/비활성 처리됨
- Dashboard polling이 destroy 시 정리됨
- Electron bridge 없는 `npm start`에서도 Store가 렌더링됨

수동 E2E:

1. Application Support의 marker와 모델 파일을 모두 제거
2. `/store`에서 `dance_highlight` 설치
3. 설치 완료 후 `/dashboard`에서 running 상태와 port/pid 확인
4. `중지` 클릭 후 stopped 확인
5. `시작` 클릭 후 running 확인
6. `/dance` 진입 후 기존 파이프라인 실행 흐름이 깨지지 않는지 확인

