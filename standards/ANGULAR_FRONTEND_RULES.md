# Angular Frontend Rules

작성일: 2026-05-06

이 문서는 `clipper_angular/.claude/CLAUDE.md`와 `clipper_angular/.claude/DESIGN_DECISIONS.md`의 Angular 결정사항을 Codex 작업 표준으로 옮긴 것이다. Angular 작업 전 반드시 확인한다.

## 1. Zoneless Is Required

`clipper_angular`는 Angular 19 standalone + zoneless 앱이다.

기준:

- App bootstrap은 `bootstrapApplication(AppComponent, appConfig)`를 사용한다.
- `appConfig`는 `provideExperimentalZonelessChangeDetection()`을 제공한다.
- `angular.json`의 build/test `polyfills`에는 `zone.js`를 넣지 않는다.

금지:

- `import 'zone.js'`
- `import 'zone.js/testing'`
- `NgZone` 기반 상태 갱신
- `provideZoneChangeDetection`
- `fakeAsync`, `tick`, `waitForAsync` 같은 zone 기반 테스트 helper
- 외부 라이브러리 도입을 이유로 zone.js를 다시 로드하는 것

테스트 규칙:

- Standalone component `TestBed` spec은 provider에 `provideExperimentalZonelessChangeDetection()`을 명시한다.
- async 동작은 `await component.method()` 또는 실제 signal/observable 상태 변화 확인으로 검증한다.
- 테스트가 `NG0908: In this configuration Angular requires Zone.js`로 실패하면 `zone.js/testing`을 import하지 말고 zoneless provider 누락을 고친다.

## 2. State Management

기준:

- Local component state: Angular `signal()`, `computed()`, `input()`, `output()`.
- Shared cross-feature state: `@ngrx/signals` SignalStore.
- RxJS는 HTTP, realtime stream, interop에 사용하되, UI 상태를 숨긴 mutable subscription 필드로 소유하지 않는다.

금지:

- 공유 필요가 없는 로컬 상태에 Store 껍데기를 씌우는 것.
- 여러 컴포넌트가 알아야 하는 상태를 임의 service public mutable field로 흩뿌리는 것.
- Angular component가 backend orchestration state machine을 직접 소유하는 것.

## 3. Component Defaults

기준:

- Standalone component를 사용한다.
- `ChangeDetectionStrategy.OnPush`를 기본으로 한다.
- API 호출은 Angular service에서 수행하고 component는 사용자 interaction/view state를 맡는다.
- Angular의 기본 backend 대상은 NestJS API다. Native-only 기능만 Electron IPC를 사용한다.

## 4. Importing Legacy UI Code

기존 Angular/third-party 코드를 가져올 때 확인한다.

- Zone.js 의존 패턴이 있으면 이식 전에 리팩토링한다.
- Quill/Swiper 등 DOM/event-heavy 라이브러리는 zoneless 호환성을 먼저 확인한다.
- 호환이 애매한 라이브러리는 wrapper/service boundary 뒤에 격리하고, component state는 signal로 정규화한다.
