# 정식 PG 로컬 통합·검증 최종 결과

기준일: **2026-09-17 KST**

상태: **병합·후속 구현 커밋 및 아래 실행 증거 보존 / Astra 재감사에서 안전성 완료 판정 정정**

## 최신 정정 — 이 문서의 이전 완료 판정보다 우선

재감사 후 승인된 수정도 진행됐다. 현재 정본은 [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)이며, 코드4repo는 미커밋이고 설치형 실기가 남는다. 아래 clean·수정 전 판정은 각 checkpoint 당시 기록이다.

[2026-09-17 Astra 독립 재감사](2026-09-17-astra-independent-review.md)에서 P1 7건/P2 6건을 확인했다. 따라서 아래 구현·테스트·smoke 기록은 그 시나리오가 실행됐다는 증거이며, 후속 수정이 모두 끝났거나 DB 복제본 리허설로 즉시 넘어가도 된다는 근거가 아니다. 현재 다음 행동은 발견 사항 수정 범위 확인과 회귀검증이다. 이번 감사는 코드/commit/서버/DB를 변경하지 않았다.

## 결론

최신 `origin/dev`, `origin/integration/main-unification-20260911`, Electron 앱 이름 변경을 별도 통합 worktree에 결합했고, 대화에서 확정한 PG 안전성 보완까지 로컬 커밋으로 보존했다. 8개 worktree는 모두 clean이다.

개발서버·개발 DB·운영서버·운영 DB에는 접근하거나 변경하지 않았다. 원격 push·main/dev 직접 변경·배포도 하지 않았다. 실제 ML 플러그인 실행과 Build 5 전체 QA는 계속 HOLD다.

## 작업 공간과 현재 HEAD

- worktree 루트: `.worktrees/dev-pg-local-validation-20260917/`
- 공통 branch: `integration/dev-pg-local-validation-20260917`

| 저장소 | 현재 HEAD | 상태 |
|---|---|---|
| Angular | `ac8793299b75834868e89afe6889764cb0939844` | clean |
| Electron | `827fcda8b12a34232c2574983afff6284b69d949` | clean |
| NestJS | `f452b6f892dfa77d22e971c746daa94285c04a3c` | clean |
| Python | `60417ce865499df519971650a43a7ca1a82d9867` | clean |
| Infra | `f975f34924bcf6c483dc16ba7acb08917b127fd4` | clean |
| Web Admin | `3d47536b9f8c3e8bf0dfd71dd78805a98f775475` | clean |
| Web API | `73921471d9126c85bb669fbfd477f8673531c719` | clean |
| Web Client | `a4bc54b5852e82d0699f63e6198d409746dd0ee0` | clean |

## 통합 뒤 구현한 핵심 보완

### Web API

- operation 시작 요청에 안정적인 idempotency key와 DB 유일성을 적용했다. 동일 attempt의 응답 유실·재전송은 한 번만 차감되고, 사용자가 명시적으로 다시 시도하면 새 attempt로 처리된다.
- operation 시작은 활성 구독이 없어도 유효한 보유 크레딧으로 허용된다는 기존 제품 정책에 OpenAPI 설명과 계약 테스트를 맞췄다.
- 날짜에 따라 깨지던 구독 갱신 테스트를 고정 시각으로 안정화했다.

### Desktop NestJS·Angular

- access/credit 원격 응답을 런타임에서 검사·정규화하고 잘못된 계약은 502로 명확히 실패시킨다.
- job attempt와 operation 연결정보를 사용자 PC의 기존 로컬 데이터 영역에 영속 저장한다. 원격 DB에 프로젝트나 미디어를 업로드하지 않는다.
- terminal 명령을 durable outbox에 먼저 기록하고 네트워크 복구·앱 재시작 뒤 안전하게 재전송한다.
- Shortform·Dance·Dialog·Variation의 과금 성공/실패/환급 종결을 공통 수명주기로 모았다.
- 사용자 재시도는 새 견적·확인·새 operation의 별도 유료 attempt다. 실패·취소된 원시도는 전액 환급한다.
- `preparing → queued → starting → running → completed|failed|cancelled` 상태를 enum으로 명시했다. 신규 데이터는 `render_prepare_pending` 호환 필드를 읽거나 쓰지 않는다.
- 앱 재시작 시 진행 중 유료 작업을 자동 재개하지 않는다. 자동 판정 가능한 실패는 종결·환급하고, 결과가 모호한 항목만 Admin recovery 안전망으로 남긴다.
- Shortform 최종 렌더 전에 줄별 TTS·미디어·파일 무결성을 검사한다. 누락을 숨기기 위한 sample 음성·무음 fallback 렌더 경로는 제거했다.
- 옛 `CurrentLicenseSummary/currentLicense/_license` adapter를 제거하고 access·credit 원형 모델로 정리했다.
- 해결되지 않은 attempt/outbox는 삭제하지 않는다. 서버 종결 확인이 끝난 metadata와 tombstone만 확인 시점부터 30일 뒤 정리한다.

### Electron 앱 이름과 identity

- 운영 표시/패키지 이름: `Clipper Studio`
- 개발 표시/패키지 이름: `Clipper Studio (dev)`
- 운영은 기존 `appId=ai.clipperstudio.app`, protocol `clipperstudio://`, `Application Support/Clipper`를 유지한다.
- 개발은 기존 `appId=ai.clipperstudio.desktop`, protocol `clipper://`, `Application Support/Clipper Studio`를 유지한다.
- 캐시·포트·업데이트 구조도 유지한다.
- macOS에서는 표시명 변경으로 기존 암호화 로그인 토큰을 복호화하지 못할 수 있으며, 사용자가 승인한 정책대로 첫 실행 1회 재로그인을 허용한다. 프로젝트·설정 경로는 바뀌지 않는다.
- Nest child process 종료를 intentional shutdown으로 정리하고 앱 종료 시 남는 프로세스가 없도록 보완했다.
- 중간 커밋 `1930ad4`가 운영 identity를 개발 identity로 통일했던 결함은 사용자 지적 뒤 `827fcda`에서 정정했다. 잘못된 상태는 push·배포되지 않았다.

## 검증 결과

### 정적·단위·빌드

- Angular: 관련 테스트와 production build PASS.
- Electron: 전체 **950/950 PASS**, TypeScript/build PASS.
- NestJS: 전체 **2,592/2,592 PASS**, build PASS.
- Python: 승인된 비-ML 대상 테스트 PASS. 실제 모델 실행은 HOLD.
- Infra: 대상 Node/monitor/API 격리 테스트 PASS. Windows 전용 1건은 플랫폼상 SKIP.
- Web Admin: 전체 **562/562 PASS**, production build PASS. 최신 dev의 telemetry entity와 formal-PG entity가 모두 등록되는 계약을 검사한다.
- Web API: 전체 **258 suites PASS, 5 SKIP / 2,799 tests PASS, 21 SKIP**, build PASS.
- Web Client: 전체 **285 SUCCESS**, production build PASS.

### 별도 로컬 PostgreSQL migration

격리 PostgreSQL(`/private/tmp/clipper-pg-validation-20260917.a9EppO`, 검증 당시 port `55489`)의 User/Admin/Release 세 DB에 migration을 실행했다.

- 세 DB 모두 최초 migration PASS.
- 같은 migration 재실행은 no-op PASS.
- runtime policy seeder가 현행 여섯 operation을 생성함을 확인했다.
  - `shortform_url.create`, `shortform_paste.create`, `shortform_prompt.create`: 50
  - `dialog_highlight.extract`, `dance_highlight.extract`: 입력 분당 50
  - `variation.render`: 영상당 20
- 모든 현재 tier는 `entitlement_mode=all`이며 플러그인별 차등을 적용하지 않는다. 남아 있는 allowlist 행은 이 모드에서 접근을 제한하지 않는다.

과거 schema fixture도 실제 migration 순서로 추가 검증했다.

- 빈 fixture DB에 `CreateLicenseSchema1750118400000`부터 `CreateOperationRecoveryAudit1786750000000`까지 실제 migration class를 순서대로 적용해 `DropLegacyBilling` 직전 상태를 재현했다.
- migration 전 fixture: 옛 테이블 5개, legacy review 주문/이벤트 각 1개, operation run 2개, resolution event 1개, 폐기 대상 policy 1개, 새 PG `credit_grants`/`credit_ledger_entries` 각 1개.
- 정식 runner로 나머지 migration을 끝까지 적용한 결과: 옛 테이블·review 주문/이벤트·operation run/resolution·폐기 policy는 모두 0, 허용 policy와 새 PG grant/ledger는 각각 1개로 보존됐다.
- 같은 DB 재실행은 `No pending migrations`였다.
- replacement `credit_ledger_entries`를 의도적으로 누락시킨 별도 fixture에서는 `replacement billing table credit_ledger_entries is missing`으로 실패했고, 옛 테이블 5개와 migration 미적용 상태가 그대로 남았다. 즉 guard가 파괴적 drop 전에 동작했다.
- 별도 rollback fixture의 사전 custom-format dump를 만든 뒤 migration을 적용하고 DB를 다시 생성해 `pg_restore`했다. 핵심 테이블 row-count checksum이 사전·복원 후 모두 `c716dbc86c50549d686d065714d57c7e`로 일치했다.
- 검증용 fixture DB와 dump는 삭제했고 임시 PostgreSQL도 종료했다.

중요한 실제 migration 영향:

- `1786800000000-DropLegacyBilling`은 옛 review payment 행을 삭제하고 `credit_ledger`, `token_usage`, `licenses`, `purchase_requests`, `plans`를 drop한다.
- `1786850000000-ResetLegacyOperationHistory`는 operation resolution event/run과 허용 목록 밖 policy를 삭제한다.

따라서 빈 로컬 DB에서는 안전했지만, 개발 DB에는 바로 실행하지 않는다. 먼저 복제본에서 구·신 금융 데이터 건수와 FK 삭제 순서, live provider 거래 의심 행을 조사하고 dump 복원 rollback을 검증해야 한다.

특히 fixture가 증명한 핵심은 **migration은 옛 금융 상태를 제거하지만 이미 존재하는 새 PG grant/ledger를 자동 초기화하지 않는다**는 점이다. 사용자 결정대로 개발 금융 상태 전체를 비우려면 개발 DB 복제본의 실제 FK를 본 뒤 별도 transaction reset SQL이 필요하다.

### 로컬 API 정책 검증

- 무료 체험 사용자: access 조회, 400크레딧 지급, Variation 2개 견적 40, 실제 차감, 같은 idempotency key 재전송 시 중복 차감 없음, fail 시 정확히 1회 환급, success 시 차감 유지 PASS.
- 구독 없이 추가구매 크레딧만 남은 사용자: 작업 차감·환급 PASS, 신규 추가구매 checkout은 `NO_ACTIVE_ACCESS`로 거부 PASS.
- evidence와 immutable ledger에서 작업명·사유·금액·operation 연결을 확인했다.

### 실제 UI smoke

- macOS arm64 local-api 개발 앱 `Clipper Studio (dev).app`을 실제 실행했다.
- 표시명, 로그인 화면, 검증용 일회성 desktop auth code session, `/projects`, Variation, 설정의 무료체험·400/400 잔액·grant 기록 표시를 확인했다. 격리 API에는 Google OAuth client ID/secret을 넣지 않았으므로 실제 Google OAuth 재로그인은 검증하지 않았다.
- 종료 뒤 Electron/Nest 자식 프로세스가 남지 않음을 확인했다.
- 격리 smoke 계정에는 기존 프로젝트가 없었으므로, 특정 기존 프로젝트가 실제 목록에 보이는지는 아직 증명하지 않았다. 데이터 경로 identity와 저장 경로 계약은 별도로 통과했다.
- Web Client 실제 브라우저에서 검증용 일회성 access-token relay, `/my`, `/my/credits`, 무료체험 access·400크레딧·ledger 표시를 확인했다. 실제 Google OAuth는 같은 이유로 검증하지 않았다.
- 검증 중 브라우저에 열린 `client=web&returnUrl=http://127.0.0.1:4201/auth/callback...` 주소는 Web Client 로그인 코드가 만든 것이다. Electron 로그인 코드는 항상 `client=desktop`을 사용한다. 격리 API가 Google OAuth 자격증명 없이 기동됐기 때문에 해당 Web Client 요청은 `503 Google OAuth is not configured on this server`로 끝났다.
- 검증용 API/Web/PostgreSQL 프로세스와 브라우저 탭은 모두 종료했다.

## 의도적으로 하지 않은 검증

- Windows NSIS 설치파일 실제 생성·설치·업그레이드: 사용자가 Windows 서버에서 직접 검증해야 한다.
- 실제 Toss 결제·웹훅, 운영 결제수단 사용.
- 실제 ML 플러그인 실행.
- Build 5 전체 QA.
- 개발서버 배포, 개발 DB migration, 운영서버/운영 DB 접근.

## 재감사 수정·재검증 이후 승인 지점: 개발 DB 복제본 리허설

아래 절차는 Astra 재감사 결함 수정·재검증 이후에 재개한다. 실제 개발 DB 변경이 아니라, 사용자가 DB 접근이 가능한 실행 장비에서 User/Admin/Release DB dump를 만든 뒤 로컬 격리 PostgreSQL에 복원하는 작업이다.

1. dump 생성 장비·접속 방식·세 DB 이름을 먼저 사용자와 확인한다.
2. 사용자가 실행할 read-only dump 명령을 목적·영향과 함께 제시한다.
3. 로컬 복제본에서 표별/user별 건수, source/reason, 생성 시각, payment/subscription 연결, operation/ledger FK를 inventory한다.
4. 승인된 개발 금융 상태 초기화 범위와 정확한 삭제 순서를 복제본에서만 rehearsal한다.
5. migration 후 사용자·로그인 보존, 구·신 금융 상태 정리 결과를 비교한다.
6. 사전 dump 복원으로 rollback rehearsal을 통과시킨다.
7. 결과를 사용자에게 보여주고 별도 승인을 받은 뒤에만 실제 개발 DB 변경·배포 계획으로 이동한다.

현재 시점의 commit은 모두 로컬 통합 branch에만 있으며 **push 0, 배포 0, 개발 DB 변경 0, 서버 접속 0**이다.
