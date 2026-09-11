# 플러그인 리소스 안전성 후속 패치 — 2026-09-10

구현·격리 검증 완료. **커밋·푸시·배포 없음. 실제 ML 플러그인 실행 없음. Build 5 전체 QA·실제 플러그인 QA HOLD 유지.**

작업본: `/private/tmp/clipper-resource-dashboard-review/{clipper_electron,clipper_angular,clipper_nestjs,clipper_python}`.

## 복구

- `manifest.json`에 저장소별 정확한 기준 HEAD, 패치 SHA-256, 37개 파일 목록을 기록했다.
- 이 패치는 **기존 CPU 7파일 개선을 포함한 전체 작업본**이다. Electron 2 / Angular 7 / Nest 25 / Python 3파일. CPU 보관본을 중복 적용하지 않는다.
- 원래 CPU 패치 디렉터리 `../2026-09-10-cpu-topology`는 수정하지 않았다. 시작 시 세 패치의 HEAD·SHA·diff byte 일치를 확인했고, 종료 시 원래 추가된 CPU 코드 블록이 모두 유지되는지 확인했다. Angular 테스트 앞에 안전성 테스트를 추가했기 때문에 원래 CPU 패치의 단순 역적용 context는 이동했다.
- 임시 폴더가 없으면 각 저장소를 별도 clean clone/checkout으로 준비하고 `manifest.json`의 baseCommit으로 이동한다. 공유 원본에 적용하지 않는다.
- `shasum -a 256 <patch>` 대조 → `git apply --check <patch 절대경로>` → `git apply <patch 절대경로>` 순서로 복구한다.
- 실제 기준 커밋에서 영향받는 파일을 별도 디렉터리에 추출해 각 패치를 적용하고, 모든 결과 파일을 작업본과 byte 단위 대조했다. 신규 테스트와 소스도 포함한다.
- 임시 clone의 origin은 로컬 경로다. 나중에 push할 때는 GitHub 대상·브랜치를 별도로 확인한다. 이번 작업에서는 새 커밋/branch 통합/push를 하지 않았다.

## 구현 범위

1. 작업별 고유 lease를 첫 await 전에 등록. 준비·실행·완료/실패까지 소유권 유지. 동일 런타임의 다른 lease는 해제하지 않는다.
2. idle timer 세대 무효화, health await 이후 소유권/세대 재검증, stop 확정과 신규 시작 사이 동기 경계. 확정된 stop 동안 신규 시작 대기.
3. 취소는 해당 job/stage DELETE만 요청. POST 등록 경합 시 DELETE 재시도, 이미 취소된 WebSocket·완료 저장 실패에서도 감시와 lease 종료. 무응답 job의 무조건 runtime kill은 하지 않는다.
4. TTS/Python executor/Dialog/직접 STT/렌더/텍스트 미리보기/LocalPluginJobRunner 및 수동 시작의 공통 admission. JobsService는 과금·소스 준비 전에 lease/admission을 확보한다.
5. 새 런타임 시작의 정리·측정·판정·ensureStarted를 전역 직렬화. 정리 후 RSS를 가용 RAM에 더하지 않고 재측정한다. 알려진 RAM 예상량이 있는데 측정 실패면 critical로 차단한다. manual confirm도 critical을 우회하지 못한다. 기존 noncritical 경고는 수동 확인/자동 작업 계속 정책을 유지한다.
6. Python SDK의 thread-safe 동기 요청 집계와 TTS 적용. health·idle watcher·shutdown 대기가 동기 요청을 포함하고, 완료/예외 시 idle clock 갱신.
7. 백엔드 pressure watchdog: 10초 간격, 가용 RAM <10% 3회 연속, 정리 후 목표15%, 60초 재정리 간격. 중첩 없음, 조회 실패 시 연속 횟수 초기화, 종료 시 timer 해제. `CLIPPER_PLUGIN_PRESSURE_WATCHDOG_ENABLED=false`로 비활성화. CPU는 종료 판단에 사용하지 않는다. RSS 없는 local 모드도 manifest 열거 후 소유권·health idle 확인으로 정리한다.
8. UI 조건부 정리: `POST /v1/plugins/:name/stop-idle` → `{ stopped: boolean }` (raw). 기존 `/stop`은 명시적 강제 중지 동작을 유지한다. lifecycle의 optional `activeOwners`는 **앱 job 개수가 아닌 준비/실행 lease 수**다. 중첩 호출은 2개 이상 소유권을 표시할 수 있다.
9. 대시보드: 원격 health 미확인/15초 이상 경과/소유권/조회 오류는 정리 제외. 일괄 중복 방지, 정리·보호/상태변경·실패 결과, 갱신 중첩 방지·오류 안내·수동 갱신·가용 RAM·빈 목록 안내. 기존 CPU 표시 보존.

## 검증

- Nest 관련 **131/131**: 소유권, 발화 timer, health 지연, 취소 POST 경합, terminal 저장 실패, 과금 전 차단, 정리 후 재측정, 직렬 시작, watchdog, conditional stop, DI 및 기존 작업/재시도/직접 STT 회귀.
- Angular **48/48**: 기존 CPU 포함 Dashboard / PluginStatus / ResourceStatus, 조건부 HTTP 계약·unknown/stale/owner 제외·중복/부분 실패·조회 중첩.
- Python **14/14**: 실제 모델 없는 TTS route/runtime·동시 요청 health·실패 후 집계/clock·SDK idle/cancel.
- Nest build, Angular packaged build, Python 변경 소스 py_compile 통과. Electron은 새 변경이 없어 이전 CPU 테스트/빌드를 반복하지 않았다.
- Python 테스트는 원본 venv의 의존성만 사용하고 PYTHONPATH를 격리 checkout의 SDK/TTS로 지정했다. 모델 로드·다운로드·실제 합성·실제 플러그인 subprocess 실행 없음.
- 일부 Nest 테스트는 모의 HTTP/WebSocket loopback 서버를 사용. Angular는 모의 서비스/HttpTestingController + Headless Chrome을 사용.
- 샌드박스 loopback EPERM과 Angular 빌드134 중단은 로컬 권한으로 재실행해 최종 통과. 시스템 Node24.3은 Angular CLI 최소 버전 미달이라 설치된 Node24.19 사용. Karma 테스트 폰트404 경고는 기존 harness 자산 경고이며 테스트 실패 없음.
- 독립 코드 리뷰 3회: 취소 경합·telemetry 실패·WebSocket 소유권 누수를 보완한 뒤 마지막 변경 blocker 없음. 전체 ML/Windows 실기 승인 의미가 아니다.
- `evidence/`에 RED 및 최종 GREEN·빌드·원본 Git/remote 읽기 전용 증거를 보존했다.

## 남은 범위와 제한

- **R5 Windows owned process tree / ffmpeg 자손 종료**: 이번 수정 대상 아님. 실제 Windows 새 CPU CIM·설치 파일·Build7 snapshot 대조, Build5 전체 QA·실제 ML 실행은 계속 보류.
- admission의 RAM/VRAM estimate는 **런타임 cold-start 예산**이다. 이미 running인 런타임은 같은 예상량을 이중 차감하지 않는다. 작업별 증분 RAM/VRAM 예약, 모델 로드 후 추가 메모리 증가, GPU 60초 cache의 신선도는 보장하지 않는다.
- 전역 시작 직렬화는 다른 cold start의 완료를 기다릴 수 있다. 무응답 job은 다른 작업 보호를 우선해 health가 busy/unknown이면 강제 종료하지 않는다. 별도 강제 종료 정책은 남음.
- 자동/조건부 정리는 로컬 소유권 + health 계약을 전제로 한다. 사용자 직접 강제 stop/uninstall·앱 종료·외부 OS 종료는 소유권을 무시할 수 있다. Windows 자손 잔존·모든 외부 클라이언트의 원자적 health-to-stop은 이 격리 검증으로 보장하지 않는다.
- 광범위 GPU별 UI·GPU cache 시각, 모든 종료 사유/이력·watchdog 상태 표시, 개별 강제 stop의 직접 요청 경고 개선은 잔여. 새 UI의 별도 다크/라이트 실기 스모크는 수행하지 않았다(컴포넌트 격리 렌더 및 packaged 빌드만).
- PG·운영 완료 항목 재실행, DB·migration·결제·운영 서버 접속/변경 없음. 공유 원본 8개 저장소 branch/HEAD/status/추적 diff SHA-256 보존 재확인.
