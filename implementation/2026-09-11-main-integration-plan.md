# 8개 저장소 main 통합 준비 계획 — 2026-09-11

> 실행 담당: 이 문서는 비교·병합 제안이다. 사용자 확인 전 브랜치 생성·병합·충돌 해결을 실행하지 않는다. 향후 실행은 Superpowers executing-plans 방식으로 합의한 단계만 진행한다.

**목표:** 현재 운영 기준 + 최신 원격 dev + 실제 미반영 작업을 동일 이름의 integration 브랜치에 모을 구체적인 안을 검토한다. main의 고유 코드는 사용자 지시로 대상에서 제외한다.

**구조:** 저장소별 운영 기준 SHA에서 시작하고, dev 전체 이력을 병합할 계획이다. 공통 조상의 변경 차이를 사용하여 운영 변경을 유지하면서 dev 변경을 더한다. CPU·리소스50파일 등 미커밋 수정은 dev 통합 후 기준 패치로 별도 반영한다.

**도구·범위:** Git 읽기·별도 임시 bare clone의 원격 객체 fetch·diff·patch-id 대조. 원본/작업본 수정 없음. 테스트·빌드·실제 merge/merge-tree·커밋·푸시·배포·운영 DB 작업 없음.

## 1. 확정된 사용자 기준

- main 존재 여부만 확인한다. 오래된 main 고유 기능은 수집하거나 병합하지 않는다.
- 현재 운영용 브랜치와 최신 원격 dev가 우선이다. 특정 파일에서 서로 다른 기능을 추가했으면 한쪽 파일 전체를 선택하지 않고 두 기능을 조합한다.
- 8개 저장소 모두 같은 integration 브랜치 이름을 사용한다. **제안: `integration/main-unification-20260911`**. 이번 조회에서 8개 모두 같은 이름의 로컬/원격 브랜치가 없었다. 생성은 아직 안 했다.
- 지금 결과물은 계획이다. main 최종 반영·기존 main 이력 처리·push/배포는 이번 승인 범위가 아니다.

## 2. main 존재 여부

| 저장소 | 로컬 main | 원격 main | 이번 처리 |
|---|---|---|---|
| clipper_web_api | 0eab2509 | 0eab2509 | 존재 확인만; 고유 코드 제외 |
| clipper_web_admin | db26f4d8 | db26f4d8 | 존재 확인만; 고유 코드 제외 |
| clipper_web_client | 7bdaeaec | 7bdaeaec | 존재 확인만; 고유 코드 제외 |
| clipper_electron | df36a6e6 | df36a6e6 | 존재 확인만; 고유 코드 제외 |
| clipper_angular | df399a8d | d2f2475f | 존재 확인만; 고유 코드 제외 |
| clipper_nestjs | 63e32f1c | ad719cab | 존재 확인만; 고유 코드 제외 |
| clipper_python | 786a6fd5 | cf774489 | 존재 확인만; 고유 코드 제외 |
| clipper_infra | 없음 | 없음 | 존재 확인만; 고유 코드 제외 |

7개에 로컬/원격 main이 있고 Infra는 둘 다 없다. Angular·Nest·Python은 로컬 main과 원격 main의 SHA가 다르지만 이번 계획에는 영향이 없다. main을 변경·삭제하지 않았다.

## 3. 저장소별 통합 기준

| 저장소 | 출발 운영 SHA | 추가할 dev SHA | 운영 전용 / dev 전용 커밋 | 공통 변경 파일 수 | 미커밋 새 작업 |
|---|---|---|---:|---:|---|
| clipper_web_api | e0e5b356 | 37318b0f | 166 / 17 | 4 | 로컬 PG compose1파일 검토; 기존 M은 재적용하지 않음 |
| clipper_web_admin | cd3a3069 | eae522f4 | 41 / 0 | 0 | 새 코드 없음; 기존 M은 이미 통합됨 |
| clipper_web_client | 4d95a963 | 4b361efc | 57 / 0 | 0 | 새 코드 없음; 기존 M은 이미 통합됨 |
| clipper_electron | a34a39d5 | 3977142c | 9 / 69 | 8 | CPU·R5 8파일 |
| clipper_angular | c8b18677 | 84628f4f | 9 / 28 | 5 | CPU·안전성 UI 7파일 |
| clipper_nestjs | 780128a0 | 4a22f0b0 | 8 / 42 | 1 | CPU 모델·R1~R5·watchdog 30파일 |
| clipper_python | 260751d2 | 88b1da27 | 0 / 2 | 0 | R1 TTS/SDK·R5 5파일 |
| clipper_infra | f948922c | 4d320226 | 15 / 0 | 0 | 운영 문서5파일 |

커밋 수는 merge·문서·기존 테스트 변경도 포함한다. 이는 실행한 테스트 수나 기능 수가 아니다. 원격 HEAD는 직전 8repo 감사와 같은 값이다.

운영 브랜치 매핑:

- `clipper_web_api`: `release/pg-expiry-20260910` (`e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5`); dev `37318b0f21f196f88d10bc794482895d0667a80b`.
- `clipper_web_admin`: `release/pg-expiry-20260910` (`cd3a3069310bdae13f123615e1a1a2a8972187cd`); dev `eae522f4908c65a55680be09353dd95df2a71190`.
- `clipper_web_client`: `integration/toss-payments-pg-20260903` (`4d95a963cde6f4e4067244c6cc8c148bb66709ce`); dev `4b361efc742db797e85848c5aea90eb1736194c5`.
- `clipper_electron`: `integration/toss-payments-pg-20260909` (`a34a39d510bca51bf8b3e527d433ff9112c686fc`); dev `3977142c9460ee1442205fdac208094098afd5a1`.
- `clipper_angular`: `integration/toss-payments-pg-20260909` (`c8b186770ae6f77294a2a1689226834f05a8944a`); dev `84628f4f5615d9e419784b65db51442faa4571c9`.
- `clipper_nestjs`: `integration/toss-payments-pg-20260909` (`780128a069c38a9df6438cc64d79f7a2e42bc1ea`); dev `4a22f0b09350691eb93fd332312d4e4ba578fa72`.
- `clipper_python`: `integration/toss-payments-pg-20260909` (`260751d2fa5be8a5a9cd8e346c60ba22d1512ed9`); dev `88b1da277922cc5734a3e72e32425aa4054fa158`.
- `clipper_infra`: `integration/toss-payments-pg-20260903` (`f948922c812ab583a84e4a64c5d8faa423afe294`); dev `4d3202263d84de9d046a1abc6eb51826a47009ae`.

**권장 방식:** API·Electron·Angular·Nest는 운영 기준에 dev를 3-way 병합하는 안이다. 커밋을 일부만 골라 빠뜨리지 않도록 전체 dev 이력과 최종 변경을 통합 대상으로 삼는다. Python은 운영 기준이 dev의 조상이므로 두 커밋을 fast-forward로 반영 가능한 관계다. Admin·Customer·Infra는 dev가 운영 기준의 조상이므로 dev를 다시 병합할 내용이 없다.

실제 웹 서버 실행 SHA는 이번에 직접 재조회하지 않았다. 위 웹 운영 SHA는 마지막 사용자 배포 확인값과 현재 원격 운영 브랜치가 일치하는 기준이다. Desktop Build7 설치본의 정확한 snapshot은 미확인이다.

## 4. 파일별 차이와 권장 조정

### Web API — PG 체계와 텔레메트리 조립

- `src/app.module.ts`: 운영은 예전 Billing/ReferenceAnalysis 모듈을 제거하고 Catalog·Access·Credits·Members·AdminDashboard와 스케줄러를 등록했다. dev는 DesktopTelemetry와 스케줄러를 등록했다. **운영 모듈 목록을 유지하고 DesktopTelemetry를 추가하며 ScheduleModule.forRoot()는 한 번만 둔다.** dev 파일 전체 선택으로 제거된 모듈을 되살리지 않는다.
- `src/core/database/admin.datasource.ts`: 운영의 PG 엔티티·migration 등록을 보존하면서 dev의 DesktopSession 엔티티와 `1788950000000-CreateDesktopSessions`, `1788950100000-AddDesktopErrorReportOrigin`을 추가한다. 이미 운영 적용된 migration은 재작성하거나 재실행하지 않는다. 새 migration 등록/적용 검토와 실제 DB 실행은 분리한다.
- `package.json`: 양쪽 최종 내용이 byte 동일하다(`@nestjs/schedule ^6.1.3`). 중복 의존성을 만들지 않는다.
- `package-lock.json`: 양쪽 최종 차이는 `@types/luxon` 3.7.4(운영) ↔ 3.7.5(dev) 한 항목이다. **dev의3.7.5를 채택하는 안**을 권한다. 계획 단계에서는 lock 재생성·npm 설치를 하지 않았다.

### Electron — 운영 설치 분리와 dev 텔레메트리

- `scripts/build-app.mjs`: 운영의 NSIS 프로세스 확인·운영 builder config 생성·출력 삭제 재시도와 dev의 runtime config 허용목록 검사를 모두 보존한다. 설정 생성 → 허용목록 검사/키 부재 안내 → 설정 저장 → 기존 운영/NSIS 준비가 누락되지 않게 조합한다.
- **문자 충돌 외에 확인한 호환 문제:** 운영 config에는 `identity: production`이 생기지만 dev의 `scripts/assert-no-packaged-secrets.mjs`의 `ALLOWED_PACKAGED_KEYS`는 webApiBaseUrl/autoUpdateDisabled/buildInfo/telemetryIngestKey만 허용한다. 그대로 조합하면 production config가 거부된다. **`identity`를 이유와 함께 허용 목록에 추가하고 값의 production 제한은 기존 reader에서 유지하는 안**을 권한다. 검사를 통째로 없애거나 운영 identity를 삭제하지 않는다. 이는 소스 판독으로 확인한 조합 문제이며 빌드를 실행하여 재현한 결과는 아니다.
- `scripts/build-runtime-config.mjs`, `src/main/config/packaged-runtime-config.ts`: 운영 API URL/identity/userData 분리와 dev telemetryIngestKey를 함께 유지한다. 운영 API 주소가 dev 기본값으로 돌아가지 않게 한다.
- `src/main/main.ts`, `src/main/auth/deeplink.ts`: 운영 identity와 userData를 로그·단일 인스턴스 락보다 먼저 적용하는 순서, 운영/개발 프로토콜 구분을 보존한다. dev의 sessionLifecycle·flush scheduler·로그 observer·storage/telemetry IPC도 조립한다. 기존 세션 종료 함수와 새 lifecycle을 둘 다 호출해 종료 이벤트를 중복 발행하지 않는다.
- `test/build-runtime-config.test.mjs`, `test/main-boot-order-boundary.test.js`, `test/quit-coordinator.test.js`: 두 브랜치의 테스트 소스를 함께 보존하되 새 조립에 맞춰 기대값과 정적 소스 앵커를 조정할 계획이다. 특히 dev의 `initDeepLink()` 문자 앵커와 운영의 protocol 인자 호출 차이를 그대로 두면 통합 코드와 어긋난다. **이번에는 테스트 수정·실행 없음.**

### Angular — 운영 계정 화면과 저장공간·동의 UI

- `src/shell/settings/settings/settings.component.{ts,html,spec.ts}`: 운영 `/pricing`, `/my/payment-history`, `/my/credits` 링크·출처별 크레딧 표시를 유지하면서 dev 저장공간/개인정보 진입과 상태를 추가한다.
- `src/shell/projects/projects/projects.component.{ts,spec.ts}`: 운영 요금 링크와 앱 로그인 문구를 보존하고 dev의 보관함 다중 선택·삭제·실패 항목 선택 유지 로직을 추가한다.
- 위5파일은 두 브랜치 모두 수정했지만 확인한 기준 행 구간은 서로 분리되어 있다. **동일 파일 변경이 곧 실제 Git 충돌이라는 뜻은 아니다.**
- 미커밋 리소스 패치와 dev가 겹치는 파일은 `src/core/bridge/clipper-bridge.ts` 하나다. dev의 telemetry/storage API와 미커밋의 `PluginLifecycleStatus.activeOwners?: number`는 서로 다른 위치이므로 모두 보존한다. CPU·작업 보호 UI를 덮어쓰지 않는다.

### Nest — 모듈 조립과 메모리/디스크 정리 경계

- 운영/dev 공통 변경은 `src/app.module.ts` 하나다. 운영 `AccessModule`·`CreditsModule`을 보존하고 dev `StorageModule`을 추가한다. 예전 `LicensesModule`을 다시 등록하지 않는다.
- 미커밋 리소스30파일과 dev 변경 파일은 직접 겹치지 않는다. 다만 storage의 디스크 캐시 회수와 R1~R4/watchdog의 런타임 메모리 회수는 함께 실행될 수 있으므로, 작업 소유권·사용 중 파일 보호·취소 시 정리 시점을 연결해서 확인할 계획이다. 파일 겹침0이 동작 충돌0을 증명하지 않는다.

### Python / Admin / Customer / Infra

- Python dev의 `plugins/tts_supertonic/tts_supertonic/synthesis.py` 공백200ms 변경과 미커밋의 TTS app/SDK active-request·Windows supervisor는 파일이 겹치지 않는다. 둘 다 유지한다.
- Admin·Customer는 운영 기준이 dev를 포함하므로 운영 소스를 그대로 출발점으로 삼는다.
- Infra 역시 운영 기준이 dev를 포함한다. 새 문서5파일은 기록 문서로 별도 반영할 후보이며, 과거 배포 이력과 향후 main/integration 운영 절차를 혼동하지 않게 정리한다.

## 5. 미커밋·보관본 처리

- 누적 CPU·R1~R5/기본 watchdog/UI는 Electron8 + Angular7 + Nest30 + Python5 = **50파일**이다. 작업본의 전체 diff SHA-256이 [최신 보관 manifest](./patches/2026-09-10-windows-owned-process-tree/manifest.json)와 네 저장소 모두 일치했다. 이전 CPU7·안전성37 패치를 추가로 중복 적용하지 않는다.
- 파일 전체 복사로 dev 기능을 지우지 않는다. dev 통합 후 운영 기준 대비의 변경 패치를 반영하는 계획이다. 겹치는 Angular bridge는 두 계약을 함께 유지한다.
- 원본 Admin7/Customer10/API7파일은 각각 이미 통합된8980eab/b5dc797/ab86b3d의 해당 파일과 byte 동일함을 재확인했다. 최신 운영이 이 이력을 포함하므로 과거 원본 파일을 다시 덮어쓰지 않는다.
- 원본 API `docs/api/openapi.yaml`은 통합본 대비 displayName/displayDescription 선언 위치와 displayName의 system grants 설명 범위 차이다. 더 넓은 설명이 있는 운영 정본을 유지하는 안이다.
- 원본 API `docker-compose.pg-local.yml`: PG용 PostgreSQL3개를 loopback56435/56433/56434 및 named volume으로 구성한 로컬 파일이다. 출처/샘플 자격값·기존 로컬 환경과의 중복을 확인해 **로컬 개발용으로 반영할 후보**다. 운영 compose로 사용하거나 컨테이너를 실행하지 않는다.
- Infra 후보: `runbooks/deploy-prod.md`, `runbooks/recreate-prod-databases.md`, `runbooks/production-console-settings.md`, `runbooks/production-deployment-team-guide.md`, `runbooks/production-setup-history-20260908.md`. 현재 변경·이력을 보존하고, 이력을 재실행 지침으로 바꾸지 않는다.
- 등록된 기존 worktree와 이전 인수인계 checkout도 목록 확인했다. `.orig`, `build/`, node_modules symlink는 별도 원본/산출물/의존성으로 기록하고 기능 변경에 섞지 않는다. 삭제하지 않았다. 이미 사라진 임시 worktree6개는 등록만 남아 있으며 복원·prune하지 않았다.

## 6. 별도 과거 브랜치 — 제외 확정

사용자가 다음 브랜치는 과거 기록으로 보존하고 이번 통합에서 제외하도록 확정했다. 삭제·병합·재적용하지 않는다.

| 저장소 | 보존할 과거 브랜치 | 확인한 tip |
|---|---|---|
| clipper_electron | feature/toss-payments-pg-integration | abdc5753 |
| clipper_angular | feature/toss-payments-pg-integration | f02bf221 |
| clipper_nestjs | feature/toss-payments-pg-integration | 60a4f072 |
| clipper_angular | fix/meme-overlay-timeline-seek | 9568f436 |

PG 기능은 최신 코드에 맞게 옮긴 9월 3일 integration을 거쳐 9월 9일 integration에 반영됐다. 옛 커밋 SHA/patch-id가 다르다는 사실을 기능 미반영으로 해석하지 않는다. Angular/Nest의 옛 플러그인별 권한 제한은 옛 feature 브랜치 자체에서도 9월 2일 checkpoint에서 제거됐다.

사용자 확인: 현재 요금제 차이는 지급 크레딧 수량이며 사용 가능한 플러그인에는 차이가 없다. 따라서 옛 Electron의 요금제별 플러그인 제한도 복원 대상으로 삼지 않는다. 현재 인증·크레딧 처리는 유지한다.

## 7. 사용자가 병합안을 확인한 뒤의 순서

- [ ] **범위 확정:** 과거 브랜치 제외와 공통 브랜치명 사용은 확정됐다. 이 문서의 파일별 조합·로컬 compose 반영안을 확인한 뒤 실제 통합을 시작한다.
- [ ] **별도 checkout 준비:** 8repo 각각 위 운영 SHA에서 동일 이름 integration을 만든다. desktop 형제 경로를 유지하며 원본 공유 checkout은 변경하지 않는다. main은 출발점으로 쓰지 않는다.
- [ ] **운영 + dev 통합:** API/Electron/Angular/Nest는 양쪽 이력을 유지하며 통합하고4절 규칙으로 충돌을 해결한다. Python은 dev까지 fast-forward 관계를 이용한다. Admin/Customer/Infra는 dev 추가0을 기록한다. 계획에 없는 동작 선택이 생기면 해결 전에 다시 알린다.
- [ ] **미커밋 기능 반영:** 보관된50파일 변경을 기준 diff로 추가한다. dev-only API/클래스/모듈을 과거 파일로 덮어쓰지 않는다.
- [ ] **문서/로컬 도구 반영:** Infra5문서와 합의한 로컬 compose를 별도 묶음으로 정리한다. 이미 통합된 웹 원본 M은 중복 적용하지 않는다. .codex 인계 기록을 임의의8개 repo에 복사하지 않는다.
- [ ] **결과 보고:** 각 저장소의 포함 SHA·미커밋 반영 목록·충돌 해결 내용·남은 정책 결정을 보여준다. 테스트·빌드·commit·push는 별도 실행 범위로 확인한다.
- [ ] **main 승격은 별도:** 기존 main7개와 신규 main이 필요한 Infra를 구분한다. 최종 코드 기준은 승인된 integration 결과이며 오래된 main 코드를 다시 섞지 않는다. 기존 main 이력 유지 방식/보호 규칙/원격 갱신은 그때 결정한다. main 삭제나 force-push를 이번 계획으로 승인받은 것으로 보지 않는다.

## 8. 스냅샷·출시와 통합의 구분

앱 snapshot 대상은 **desktop4 + Web API**다. Admin·Infra는 snapshot5개 대상이 아니지만 관리 일관성을 위해 동일 integration 이름을 사용한다. 새 integration/main을 사용하더라도 기존 고정 release snapshot이 자동 갱신되는 것은 아니다. API11커밋 차이는 API 최신 운영 e0e5b356에서 시작함으로써 이번 새 통합 소스에 포함하는 안이다.

텔레메트리는 기능을 통합하는 것과 운영에서 수집/전송을 켜는 것을 구분한다. dev 동의 UI 소스에는 아직 예시 문구라는 표시가 있고, 서버 인제스트 키·migration·운영 전송 조건도 별도다. CPU CIM/Windows R5 실검증, SDK·venv 새 내용 반영, Build7 출처 대조 및 기존 Build5/실제 ML HOLD는 유지한다.

**현재 실행 결과: 비교·계획 작성만 완료. integration 생성0, 병합0, 소스 수정0, 테스트/빌드0, commit/push/deploy0.**

## 9. 사용자 범위 확정 후 재확인

- 2026-09-11 원격 `ls-remote` 재조회: 8개 모두 운영/dev SHA가 3절과 동일하다. 원격 main은 7개 존재, Infra는 없다. 제안 integration 이름은 원격 8개 모두 미존재다.
- 공유 원본 8개: HEAD·미커밋 파일 목록·tracked diff SHA-256이 직전 감사와 동일하다. 별도 리소스 작업본의 50개 파일 SHA-256도 직전 감사와 모두 일치한다.
- 실제 운영 서버·설치 앱을 다시 조회한 결과는 아니다. 브랜치 기준 통합안이며 서버 실행 SHA/Build7 snapshot의 기존 확인 한계는 유지한다.
- 이번 갱신은 계획 문서만 변경했다. 실제 브랜치 생성·병합·테스트·빌드·커밋·푸시·배포는 실행하지 않았다.
- 향후 승인된 통합에서도 커밋 금지 조건이 유지되면 병합 결과는 별도 checkout의 미커밋 상태로 준비한다. 승인 없이 merge commit을 자동 생성하지 않는다.
