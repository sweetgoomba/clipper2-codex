# 정식 PG 로컬 통합 — 병합 및 기준선 검증 결과

기준일: **2026-09-17 KST**

상태: **역사적 병합 기준선 기록 — 후속 구현·최종 검증 완료**

> 이 문서는 후속 안전성 구현 전의 병합 기준선을 보존한다. 현재 HEAD, 해결된 테스트 문제, 최종 identity와 로컬 DB/API/Web/macOS 앱 검증은 [정식 PG 로컬 통합·검증 최종 결과](2026-09-17-local-pg-integration-validation-result.md)를 우선한다. 아래의 “승인 대기”, 옛 HEAD, 운영 identity 값은 현재 상태가 아니다.

## 변경 내용

사용자가 승인한 범위대로 `.worktrees/dev-pg-local-validation-20260917/`에 저장소별 `integration/dev-pg-local-validation-20260917` 브랜치를 만들었다. 각 최신 `origin/dev`에 `origin/integration/main-unification-20260911`을 `--no-ff`로 병합했고, Electron은 앱 이름 브랜치 `feature/app-window-name-20260915`를 두 번째 `--no-ff` 병합으로 추가했다. Git 텍스트 충돌은 0건이었다.

| 저장소 | 로컬 병합 HEAD |
|---|---|
| Angular | `d9b5064c01b3973d62c288ba3979829bbc9e01c8` |
| Electron | `b34bbcf33e79bc04756336011797960d9ae61bf4` |
| NestJS | `3683e83568964ce04471bed146ee1e1bca38f809` |
| Python | `60417ce865499df519971650a43a7ca1a82d9867` |
| Infra | `f975f34924bcf6c483dc16ba7acb08917b127fd4` |
| Web Admin | `04c5b4832631276f46987c583863bae2984149ae` |
| Web API | `73eded05ff3272f955af348e2255c99647bde077` |
| Web Client | `a4bc54b5852e82d0699f63e6198d409746dd0ee0` |

원본 8개 checkout의 branch/HEAD와 미커밋 상태는 바꾸지 않았다. push·배포·서버 접속·DB 변경은 0건이다.

## 기준선 검증 결과

- Angular: CI persistent cache 비활성 build PASS. 대상 351 tests PASS. 기본 persistent cache build의 LMDB native double-free는 worktree가 원본 checkout의 `.angular/cache`를 공유하는 환경 문제로 분리했다.
- Electron: TypeScript build PASS, 이름/identity/boot/secret 대상 71 tests PASS.
- NestJS: build PASS, access/credit·operation·Shortform·Variation·Dialog·retry·runtime safety 대상 159 tests PASS. 최초 2건 실패는 sandbox localhost bind 차단이었고 정상 호스트 조건 재실행에서 전부 통과했다.
- Python: SDK/TTS/process safety 대상 84 tests PASS. 실제 ML 모델은 실행하지 않았다.
- Infra: node tests 138 PASS, Windows 전용 1 SKIP. monitor 6 PASS. Web Client/Admin local/dev/prod/default 번들 API 격리 8 PASS.
- Web Admin: build PASS(초기 bundle budget warning 1건), 562 tests PASS.
- Web Client: build PASS, 285 tests PASS.
- Web API: build PASS. 전체 unit 2,787 PASS, 21 SKIP, 3 FAIL.

## 새로 발견한 Web API 기준선 문제

Web API는 최신 `origin/dev`가 formal-PG integration의 조상이므로 병합 결과의 파일 트리는 `origin/integration/main-unification-20260911`과 같다. 아래는 이번 merge가 새로 만든 코드 충돌이 아니라 formal-PG 기준선에 이미 남아 있던 테스트 문제다.

1. `subscription-renewal.service.spec.ts` 2건
   - fixture는 2026-09-13을 `now`로 넘기지만 production code의 `freshNow()`는 지연 실행 안전성을 위해 `max(reference, Date.now())`를 쓴다.
   - 실제 날짜가 2026-09-17이라 유예기간 종료 경로로 들어가 예상과 달라졌다.
   - 권장 수정: production code는 유지하고 해당 테스트에서 시스템 시계를 2026-09-13으로 고정한다. 이렇게 해야 미래 어느 날짜에 실행해도 같은 정책을 검증한다.
2. `admin.datasource.spec.ts` 1건
   - formal-PG entity와 최신 dev의 `DesktopSession`, `DesktopSignatureGroup`이 함께 등록됐지만 테스트가 `FreeTrialPolicyEntity`, `UserFreeTrialEntity`가 배열의 마지막 두 항목이라고 가정한다.
   - 실제 entity 누락은 없고 순서 가정만 낡았다.
   - 권장 수정: 두 free-trial entity와 두 telemetry entity가 모두 포함되는지 이름별로 검사하고 배열 끝 순서 가정을 제거한다.

두 수정 모두 테스트 전용이며 runtime 동작·DB schema·결제 정책을 바꾸지 않는다. 사용자의 신규 문제 승인 규칙에 따라 아직 수정하지 않았다.

## 앱 이름 실제 패키징

- macOS 개발 app-dir PASS: `Clipper Studio (dev).app`; `CFBundleIdentifier=ai.clipperstudio.desktop`; protocol `clipper`; local API runtime config.
- macOS 운영 DMG PASS: `Clipper Studio.app`, `Clipper Studio-0.0.1-arm64.dmg`; `CFBundleIdentifier=ai.clipperstudio.app`; protocol `clipperstudio`; production API/identity.
- Windows 개발 app-dir PASS: `Clipper Studio (dev).exe`.
- Windows NSIS는 이 arm64 Mac에서 electron-builder가 받은 x64 `makensis`를 실행할 Rosetta가 없어 OS error `-86`으로 중단됐다. builder config/단위 테스트상 개발 설치파일 `Clipper Studio (dev) Setup ${version}.exe`, 운영 설치파일 `Clipper Studio Setup ${version}.exe` 계약은 통과했다. 실제 installer 산출은 Windows runner에서 확인해야 한다.

패키징에 필요한 기존 ignored `.env.packaged`, 공개키, uv target binary는 원본에서 통합 worktree의 ignored 위치로만 복사했다. 값은 출력·수정하지 않았고 커밋 대상이 아니다.

## 남은 작업

1. 위 Web API 테스트 전용 3건 수정 승인.
2. 수정 후 Web API 전체 unit 재실행으로 기준선 완료.
3. 승인된 후속 PG 안전성 구현 계획의 Task 2부터 TDD로 진행.
4. 코드 통합 검증 완료 뒤에만 별도 로컬 DB migration 단계로 이동.

실제 ML 플러그인 실행과 Build 5 전체 QA는 계속 HOLD다.
