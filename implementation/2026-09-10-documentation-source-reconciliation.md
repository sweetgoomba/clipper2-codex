# 문서·소스 정합성 정리 — 2026-09-10

이번 작업은 기존 기록과 소스의 읽기·문서 갱신만 수행했다. 테스트·빌드·플러그인 실행·커밋·푸시·배포·운영 DB/API 조회는 실행하지 않았다. 아래 검증 횟수는 이전 작업의 증거이며 이번에 재실행한 결과가 아니다.

## 최신 상태와 읽기 순서

1. [TASKS](./TASKS.md): 현재 완료·잔여의 진입점.
2. [Windows 소유 프로세스 트리 후속](./2026-09-10-windows-owned-process-tree-followup.md): R5 구현·격리검증, 실제 Windows 보류.
3. [리소스 안전성 후속](./2026-09-10-plugin-resource-safety-followup.md): R1~R4·RAM watchdog·조건부 정리 UI 구현·격리검증.
4. [현재 상태 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md): PG·운영·원본 공유 변경·설치 증거. 리소스 구현 전이라는 당시 표현은 위 후속이 갱신한다.

| 변경 묶음 | 현재 도달 단계 | 계속 남은 범위 |
|---|---|---|
| CPU 사용률·물리 코어/스레드 | 구현·격리검증·패치 보관 완료 | 실제 Windows CIM 및 새 설치본 반영 확인 |
| R1~R3 | 실행 소유권·취소 격리·조건부 종료 구현·격리검증 완료 | 실제 ML 작업 검증 HOLD |
| R4·RAM watchdog | 공통 admission·정리 후 가용량 재측정·기본 RAM 감시 구현·격리검증 완료 | 작업별 추가 RAM/VRAM 예산·GPU 신선도 |
| 리소스 UI | 안전한 idle 정리·작업 보호·조회 오류·정리 결과·가용 RAM 등 구현·격리검증 완료 | 종료 실패/재시작 차단의 상세 안내·넓은 UI 실기 |
| R5 | Job Object 소유 트리·종료 확인·실패 시 소유권 보존/재시작 차단 구현·격리검증 완료 | 실제 Windows Job Object·uv 제어 stdin·자손 종료·설치본 검증 |

이 변경들은 전부 미커밋·미푸시·미배포다. 최신 누적 보관본은 [4repo/50파일 패치](./patches/2026-09-10-windows-owned-process-tree/README.md)와 [manifest](./patches/2026-09-10-windows-owned-process-tree/manifest.json)다. CPU7 → 안전성37 → R5포함50은 단계별 누적 파일 수이며 더해서 계산하거나 순서대로 중복 적용하지 않는다. 과거 CPU·안전성 패치와 로그는 그대로 보존했다.

## Build7: 기존 증거 대조 결과

검색 범위는 `.codex/implementation`의 기존 감사·후속·운영 구축 기록과 워크스페이스 내 snapshot/release/artifact 관련 파일 목록이다. 운영 Admin/API·S3·Windows 장비에 새로 접속하지 않았다. 따라서 아래의 ‘자료 없음’은 **이번 로컬 기록에서 확보하지 못했다**는 뜻이다.

| 항목 | 확보한 기존 기록 | 판단 |
|---|---|---|
| 설치 버전 | 사용자 보고 `0.0.3.7` = release `0.0.3`, Build7 | 기존 설치 보고 있음 |
| CPU 표시 | 사용률21.3%/25.5%, 논리 프로세서20 표시 사용자 확인 | 기존 CPU 사용률 표시 확인. 새 물리 코어 표시 반영 증거는 아님 |
| Build7 release/build/job 식별자·snapshot ID | Build7에 직접 연결되는 원자료 미확보 | 대조 미완료 |
| 저장소별 sourceRevisions 전체 SHA | 감사의 원격 HEAD는 있음. Build7 고정 snapshot 목록은 미확보 | 원격 HEAD를 Build7 소스 SHA로 대입하지 않음 |
| 설치 파일 경로·크기·SHA256·서명 | Build7 원자료 미확보 | 파일 동일성·서명 대조 미완료 |
| 정식 지정·다운로드 연결 | Build7 직접 증거 미확보 | 설치 성공만으로 정식 지정 완료 처리하지 않음 |

Build5는 별도 기록이다: release `0.0.1`, snapshot `snapshot-20260909T210055Z`, job `e1320707-205d-4557-9d4e-a28e7eb1ae43`, 파일 SHA256 `7DDE536A1A5AE9172D43745DE50C3B6168BE47A3D8EB1DA145D8A9160D2D9C7D`, Authenticode Valid/Meta Buzz Co., Ltd. 해당 값들은 [운영 구축 종료 6절](./2026-09-10-production-setup-session-closeout.md)의 **Build5 증거이며 Build7에 재사용할 수 없다**.

향후 Build7 출처 대조에 필요한 자료는 해당 release/build/job 관계, snapshot ID와 모든 저장소의 sourceRevisions, artifact 저장 경로·크기·전체 해시, 해당 파일의 서명 정보 및 다운로드 연결 기록이다. 이번에 새 자료를 확보한 것으로 기록하지 않는다. 과거 설치 성공을 재실행하거나 새 빌드를 만들 필요 없이 기존 자료부터 대조하는 항목으로 남긴다.

## 소스 snapshot과 SDK·venv 갱신 조건

읽은 소스:

- [API releases.service.ts](../../web/clipper_web_api/src/modules/releases/application/releases.service.ts): `freezeSourceSnapshot`, `startBuildForPlatforms`.
- [runner release-runner.mjs](../../web/clipper_infra/runner/release-runner.mjs): `captureSourceSnapshot`, `prepareJobSources`, `runReleaseJob`, `withElectronPackageVersion`.
- [Electron plugin-venv.ts](../../desktop/clipper_electron/src/main/plugin/plugin-venv.ts): `buildPluginVenvSyncArgs`, `isPluginDependencyMarkerFresh`, `ensurePluginVenv`; 같은 파일의 격리 작업본도 참조.
- 격리 작업본 `/private/tmp/clipper-resource-dashboard-review/clipper_electron/src/main/main.ts`: `ensurePluginVenv`에 전달되는 `appVersion: app.getVersion()`.
- 격리 Python SDK `clipper_plugin_sdk/pyproject.toml`: SDK 버전 `0.1.0`, Python `>=3.11,<3.12`.

### Snapshot

API는 이미 고정된 release snapshot의 재고정을 거부하고 빌드에 저장된 sourceRevisions를 사용한다. runner는 snapshot 수집 시 원격 브랜치 SHA를 고정하고, 작업 소스는 그 SHA를 checkout한다. **이 코드를 읽었을 뿐 snapshot capture나 fetch를 실행하지 않았다.** 새 미커밋 패치는 기존 Build7이나 기존 snapshot 재빌드에 자동 포함되지 않는다.

### Venv

- 저장 위치: `userData/venvs/plugins/<pluginName>`; marker: `userData/plugin-dependencies/<pluginName>.json`.
- Python 실행 파일이 존재하고 marker의 `pluginName`, `pluginVersion`, `pluginPackageName`, `pythonRoot`, `platform`, `arch`, `pythonRequirement`, `appVersion`이 모두 일치하면 기존 venv를 재사용한다.
- marker 불일치/누락 또는 Python 실행 파일 부재 시 `uv sync --package … --frozen --no-dev --no-editable --python 3.11 --managed-python` 경로로 진입하고 성공 후 marker를 기록한다.
- `--no-editable` 설치는 번들 소스를 직접 따라가는 방식이 아니므로 번들에 새 supervisor 파일이 있다는 사실만으로 기존 venv에 그 파일이 있다고 판단하면 안 된다.
- marker는 **Build 번호, artifactVersion, SDK 자체 버전, 소스 commit/content hash를 직접 비교하지 않는다**. 다른 비교 항목이 같다면 Build 번호만 변경해도 재사용 분기를 벗어나지 않는다.
- runner는 `job.payload.version`을 Electron package 버전에 적용하고 Build/artifact 값은 별도 환경변수로 전달한다. 따라서 표시 `0.0.3.7`만 보고 venv marker의 `appVersion`도 반드시 `0.0.3.7`이라고 추정하지 않는다. 실제 Build7의 package/marker 값은 미확보다.
- 새로운 appVersion이나 다른 marker 항목의 변경은 sync 진입 조건이다. **sync 진입 자체가 최신 SDK 파일 반영을 검증한 결과는 아니다.** 설치되는 SDK 내용 및 캐시 영향은 향후 설치본 확인 항목이다.

향후 반영 조건은 새 CPU·R1~R5를 함께 포함한 desktop 네 저장소의 변경 SHA를 포함한 전체 source snapshot(Infra 등 나머지 기록 포함), 이전 설치와 구분되는 appVersion/marker 조건, 갱신된 venv에 `clipper_plugin_sdk/windows_supervisor.py`가 포함되는지 확인하는 것이다. 이번에는 버전 변경·의존성 설치·marker 삭제·venv 삭제/재생성을 하지 않았다. SDK 해시 기반 무효화 등의 코드 보완 여부도 별도 결정할 잔여다.

## 이번 문서 변경과 제약

TASKS 상단을 최신 누적 상태로 갱신하고, 당시 감사·리소스 검토에는 최신 후속 링크를 추가했다. 과거 검증 수치와 배포 이력·패치 보관본은 수정하지 않았다. Build7 자료 대조는 미확보 항목을 명시한 상태이며 완료로 체크하지 않는다.

**이번 새 테스트·빌드·커밋·푸시·배포 없음. Build5 전체 QA·실제 ML 플러그인 실행 HOLD 유지. 공유 소스와 기존 미커밋 변경 보존.**
