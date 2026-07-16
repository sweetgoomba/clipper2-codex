# 데스크톱 첫 실행 Runtime UX와 Plugin Store 초기 로딩 개선 TODO

작성일: 2026-07-16  
상태: deferred / 구현 전 측정 필요  
우선순위: P1, clean Windows에서 앱 무창·장기 hang 또는 실행 실패가 재현되면 P0 release blocker로 승격  
상세 분석: `.codex/design/DESKTOP_FIRST_LAUNCH_RUNTIME_AND_PLUGIN_STORE_LOADING_ANALYSIS_2026-07-16.md`

## 해결할 문제

- clean packaged 첫 실행의 관리 Python/base venv/yt-dlp/EJS 준비가 오래 걸릴 때 사용자가 진행 상태를 볼 수 없다.
- 현재 base runtime 준비는 메인 창보다 먼저 완료돼야 하므로, 설치 중 Angular UI를 사용할 수 없다.
- UI가 표시된 뒤 Plugin Store는 NestJS 최초 기동, plugin 목록과 resource/status 조회를 하나의 `불러오는 중…` 상태로 기다린다.
- `PluginStatusService.refreshAll()`이 app initializer, Store, Dashboard 등에서 겹쳐 실행될 수 있다.
- Plugin 목록의 필수 응답 경로에 host resource와 model/cache 상태 조회가 포함돼 있다.
- 장기 지연 시 단계별 상태, 명시적 timeout과 화면 내 재시도가 부족하다.

## 다음 작업 순서

### 1. 재현과 baseline

- [ ] 저사양 Windows packaged clean userData에서 첫 실행을 측정한다.
- [ ] 같은 환경의 두 번째 warm launch를 측정한다.
- [ ] 정상 네트워크, 느린 네트워크와 offline을 분리한다.
- [ ] Windows Defender 기본 상태에서 runtime 설치 파일 검사 영향을 관찰한다.
- [ ] 다음 구간을 비밀값 없이 timestamp/span으로 남긴다.
  - base runtime inspect/install/venv/package/verification
  - main window create/show
  - Nest process spawn/health ready
  - Angular `refreshAll()` caller/start/end
  - Nest `/plugins` registry/resource/status 구간
- [ ] 사용자가 보고한 `불러오는 중…` 장기 유지가 어느 구간에서 멈추는지 확정한다.

### 2. 제품 결정

- [ ] base runtime을 앱 진입 전 필수 hard gate로 유지할지 결정한다.
- [ ] hard gate 유지 시 native/splash first-run 준비 화면의 단계·재시도·종료 UX를 설계한다.
- [ ] UI 선진입을 허용한다면 runtime 미준비 상태에서 허용할 화면과 비활성화할 기능을 별도로 정의한다.

### 3. Plugin Store 로딩 경량화

- [ ] `PluginStatusService.refreshAll()`에 single-flight 또는 동등한 중복 방지 계약을 추가한다.
- [ ] app initializer, Store와 Dashboard 중 최초 목록 로드 owner를 하나로 정한다.
- [ ] Plugin catalog의 필수 manifest/status와 host resource assessment를 분리할 수 있는지 측정 후 결정한다.
- [ ] model/cache 파일 탐색을 목록 응답에서 지연시킬 수 있는지 검토한다.
- [ ] 창 표시 후 NestJS를 background warm-up하는 방식과 최초 요청 지연 시작 방식을 비교한다.
- [ ] `runtime 준비`, `로컬 API 시작`, `plugin 목록 조회`를 서로 다른 UI 상태로 표시한다.
- [ ] timeout, 오류 상태와 화면 내 재시도를 추가한다.

### 4. 검증

- [ ] Electron startup 순서와 first-run 상태 전이를 자동 테스트한다.
- [ ] Angular에서 동시 refresh가 하나의 backend 요청으로 합쳐지는지 검증한다.
- [ ] 중첩 refresh 성공/실패 순서가 `loading`, `loaded`, `error`, `items`를 오염시키지 않는지 검증한다.
- [ ] Nest `/plugins`의 단계별 latency를 기록하고 무거운 작업 분리 전후를 비교한다.
- [ ] clean/warm/offline/부분 설치 복구를 Windows packaged 앱에서 수동 QA한다.
- [ ] 지원 macOS packaged 동작이 회귀하지 않는지 확인한다.

## 완료 기준

- 첫 실행 장기 준비에는 사용자가 이해할 수 있는 진행 상태가 즉시 표시된다.
- base runtime과 Plugin Store/NestJS 준비 상태가 섞이지 않는다.
- optional plugin별 dependency 설치가 앱 최초 창 표시를 막지 않는다.
- 동일 시점 plugin 목록 refresh가 중복 실행되지 않는다.
- plugin catalog의 빠른 필수 경로와 느릴 수 있는 diagnostics가 분리된다.
- 장기 지연과 실패가 무한 placeholder가 아니라 timeout·오류·재시도로 종료된다.
- warm launch에서 불필요한 Python/package 재설치가 없다.
- Windows clean install에서 측정한 목표 시간과 결과를 문서에 남긴다.
- cookie, env 값, JWT key, provider secret, Authorization과 민감한 사용자 입력을 로그나 fixture에 넣지 않는다.

## 비범위

- 이 TODO 등록 시 코드 수정이나 packaged 실행을 하지 않는다.
- 측정 전 임의의 성능 최적화를 하지 않는다.
- 사용자 요청 없이 build, 앱 실행, userData 초기화, commit/push, 배포를 하지 않는다.

