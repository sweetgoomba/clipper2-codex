# 개발 DB 복제본 PG 전환 리허설 결과

검증일: 2026-09-18 KST

후속 상태: 아래 catalog 보완 9파일은 이후 `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f`로 commit되어 원격 `integration/dev-pg-local-validation-20260917`과 일치한다. 같은 dump의 2차 clone 검증 결과는 그대로 유효하다. 다음 단계의 실제 개발서버 명령·중단·복구 절차는 [개발서버 정식 PG 전환 실행 런북](2026-09-18-development-pg-cutover-runbook.md)에 분리했다. 실제 개발 DB·서비스 변경·배포는 여전히 0건이다.

## 결론

실제 개발 DB 3개의 read-only custom dump를 별도 로컬 PostgreSQL 16 컨테이너에 복원하고, 현재 통합 브랜치 migration을 적용한 뒤 반복 실행 no-op, API 기동, 핵심 데이터 보존, dump 복원 rollback을 검증했다. 실제 개발 DB·개발서버·원격 서비스는 변경하지 않았다.

Migration 자체와 사용자·로그인·프로젝트·운영자·provider credential·release 데이터 보존은 통과했다. 기존 개발 금융·이용권·operation 이력은 승인된 출시 전 정책대로 제거되고 새 PG 금융 원장은 빈 상태로 시작한다. 기존 20명에게 무료체험이 소급 지급되지 않는 것도 API 기동 전후 수치로 확인했다.

첫 리허설에서 공개 `/catalog`가 `entitlement_mode=all`인데도 과거 allowlist row를 Basic5/Pro6/Business0으로 노출하는 의미상 불일치를 발견했다. 사용자 승인 후 Web API가 `all` tier를 현재 등록된 전체 6개 plugin key로 파생해 반환하도록 고치고, `all` tier의 저장된 allowlist row를 제거하는 migration을 추가했다. 같은 원본 dump를 새 59533–59535 clone에 다시 복원한 2차 리허설에서 migration·반복 no-op·보존 해시·API health·catalog 계약·기존 사용자 무료체험 비소급을 모두 통과했다.

## 원본 dump

- 실행 장비: `metabuzz@metabuzzui-Macmini`의 개발 DB 컨테이너. 에이전트가 서버에 접속하지 않고 사용자가 명령을 실행했다.
- 원본 경로: `/Users/metabuzz/clipper-backups/dev-pg-rehearsal-20260918-023009`.
- 로컬 보관 경로: `/Users/jina/clipper-backups/dev-pg-rehearsal-20260918-023009`.
- 형식: `pg_dump -Fc --no-owner --no-acl`; 세 파일 모두 `pg_restore --list` 통과.
- 로컬 수신 뒤 크기와 SHA256이 원본 출력과 정확히 일치했다. 보관 폴더 mode 700, dump mode 600.

| DB | bytes | SHA256 |
|---|---:|---|
| user | 483458 | `a5a30118b1fc4b304a28fa0a390cc5e5c885f88ff786f17b22cbb205ed009946` |
| admin | 129824 | `2f9dbdbc58fbe9bb3e2d72298d446aeb171001ff95552076205bfe837c040b28` |
| release | 76420 | `1f7fb82638240ce3f777086e93148a9e0c09d1c594bdb244c3e943e45a890202` |

개발 DB 세 개의 dump는 한 트랜잭션으로 묶인 분산 snapshot이 아니라 순차 snapshot이다. 이번 데이터 크기에서는 1초 안에 연속 생성됐지만, 실제 cutover 전에는 Web API를 중지하거나 쓰기를 차단한 뒤 최종 dump를 만들어 DB 간 결제·지급 참조가 같은 시점인지 보장해야 한다.

## 로컬 복제 환경

기존 5433–5435, 57433–57435, 과거 56433–56435 DB를 재사용하지 않고 다음 전용 컨테이너·볼륨을 만들었다.

| 용도 | 컨테이너 | loopback port | DB |
|---|---|---:|---|
| User | `clipper-pg-dev-clone-20260918-user` | 59435 | `clipper_user_dev_clone_20260918` |
| Admin | `clipper-pg-dev-clone-20260918-admin` | 59433 | `clipper_admin_dev_clone_20260918` |
| Release | `clipper-pg-dev-clone-20260918-release` | 59434 | `clipper_release_dev_clone_20260918` |

- image: `postgres:16-alpine`
- bind: `127.0.0.1`만 사용
- DB별 무작위 비밀번호, 별도 named volume, restart policy 없음
- 빈 DB의 public table 0개를 확인한 뒤 `pg_restore --no-owner --no-acl --exit-on-error --single-transaction`으로 복원했다.

## migration 전 데이터 분류

### User DB

- users 20, user_sessions 162, desktop_auth_codes 161
- shortform_projects 1,481, shortform_clips 8
- 기존 migration history 9

### Admin DB

- 옛 licenses 24, purchase_requests 35
- 옛 credit_ledger 253: charge 210 / 62,880 credits, refund 43 / 10,850 credits
- 옛 operation_runs 210: succeeded 159, running 38, failed 13
- payment_orders 37, payment_events 49
- 완료된 paid 주문은 9건 모두 `toss_mode=TEST`; `LIVE` 또는 non-TEST paid 후보는 0건이었다.
- 운영자 3, operator sessions 26, provider credentials 7, desktop sessions 7, 오류/telemetry 데이터는 보존 대상이었다.

### Release DB

- release versions 33, builds 51, artifacts 33, events 134
- 기존 migration history 2

개별 사용자 이메일·결제키·billing key·provider secret 값은 출력하거나 문서에 기록하지 않았다.

## migration 실행과 실제 영향

- 현재 Web API build PASS 뒤 User/Release/Admin migration을 복제본에만 실행했다.
- User: 현재 소스 10개 중 신규 2개 적용. DB history는 과거 이름이 다른 1개를 포함해 최종 11행.
- Admin: 현재 소스 migration은 64개. 복제 DB history는 과거 `CreateOperators1750400000000`, `CreateOpenAiKeys1752000000000` 두 이력을 추가로 보존해 최종 66행이다. 이는 pending migration이 아니라 역사 행 차이다.
- Release: 현재 소스 3개 중 신규 `AddArtifactDesktopProfile1789600000000` 적용, 최종 3행.
- 같은 명령을 두 번째 실행했을 때 세 DB 모두 pending migration 없음.

### 보존 결과

| 데이터 | 전/후 결과 |
|---|---|
| users | 20, ID 집합 해시 `c65c1d1eab23af5f43d51c9fc7b9b0bc` 동일 |
| user_sessions | 162, `4ac59aded4a21ee2870b157e8b18969e` 동일 |
| desktop_auth_codes | 161, `f9b741ebb4bda8e6e79d08e61ad5c9f1` 동일 |
| shortform_projects | 1,481, `368c2eb0a0b85caeae949770fc2182b5` 동일 |
| operators | 3, `aab82ec52b6a3c5a68bb20c3b0f416dd` 동일 |
| provider_credentials | 7, `5df6f4adcb83121fbd1b94a7eca42e9d` 동일 |
| release_versions | 33, `aad52cac44ba1fb4ee3d617f31ea235c` 동일 |
| release_builds | 51, `d0b1032cd7ee66cb647183645c835316` 동일 |
| release_artifacts | 33, `6746e34b581aff0ec1174aa63d1b35c7` 동일 |
| release_events | 134, `3de578b215124f83297d0bbabd6fb674` 동일 |

User의 기존 auth code에는 신규 `desktop_target`, `request_id`, `code_challenge`가 NULL로 추가된다. 옛 code를 새 독립 개발판 로그인에 재사용하지 않고 새 Google 로그인 binding을 발급받는 정책과 일치한다.

### 의도적으로 제거·초기화된 데이터

- `DropLegacyBilling`이 옛 `licenses`, `purchase_requests`, `plans`, `credit_ledger`, `token_usage` 테이블을 제거했다.
- review 목적의 옛 payment order/event는 새 정식 PG 원장으로 이관하지 않고 제거했다. 복제본의 새 `payment_orders`, `payment_events`, `subscriptions`는 0행이다.
- `ResetLegacyOperationHistory`가 옛 operation run 210건과 resolution event를 제거했다. 신규 `operation_runs`와 `credit_ledger_entries`는 0행이다.
- 새 `user_access_grants`, `credit_grants`, `user_free_trials`는 모두 0행이다.

이는 운영 DB 전체 초기화 절차를 개발 DB에 복사한 것이 아니다. 사용자·로그인·프로젝트·운영자·provider·release 데이터는 보존하고, 승인된 출시 전 금융/이용권/operation 범위만 migration 자체가 제거한 결과다.

## 정책 seed 결과

- trial/basic/pro/business 모두 `entitlement_mode=all`.
- 무료체험: 신규 가입자 400 credits / 30일 / enabled.
- 정기상품: Basic 5,900/58,800원, Pro 10,900/82,800원, Business 29,900/234,000원.
- top-up: 400/5,900원, 1,000/10,900원, 4,000/29,900원, 모두 30일.
- operation 단가: Shortform 3경로, Dance, Dialog 각 50; Variation은 영상당 20.

## 기존 사용자 무료체험 소급 방지

- `CreateUserOnboardingJobs`는 빈 job table만 만들며 기존 user를 backfill하지 않는다.
- Google 로그인은 `googleSub` 기존 user를 찾으면 그대로 반환한다.
- 신규 user 생성 트랜잭션에서만 `free_trial_provisioning` job을 함께 만든다.
- credit 조회의 repair도 이미 존재하는 해당 user job만 claim한다.
- 관련 집중 테스트 5 suites / 31 PASS.
- 복제본 API 기동 전과 health/catalog 호출 뒤 모두 users 20, onboarding jobs 0, access grants 0, credit grants 0, user free trials 0, subscriptions/payment orders/operation runs 0이었다.

따라서 기존 개발 사용자는 계정과 로그인 기록은 남지만 새 무료체험·access·credit을 자동으로 받지 않는다. 신규 가입자만 새 무료체험을 받는다.

## API smoke

- 기존 `.env` 파일을 수정하지 않고 process env에서 DB 연결만 59433–59435 복제본으로 덮어썼다.
- 별도 로컬 port 3011에서 현재 통합 Web API를 기동했다.
- `/health`: user/release/admin 모두 `ok`.
- `/catalog`: 신규 가격·크레딧 정책 응답 확인.
- 기동한 3011 API는 검사 후 정상 종료했다.

### 새로 발견한 catalog 의미 불일치

DB의 네 tier는 모두 `entitlement_mode=all`이고 operation 시작 경로는 access/allowlist를 보지 않아 유효 크레딧만 있으면 등록된 유료 작업을 시작할 수 있다. 따라서 실제 Basic·Business 기능이 제한되는 런타임 결함은 확인되지 않았다.

하지만 과거 `plan_plugin_entitlements` row가 남아 공개 응답은 다음처럼 보였다.

- Basic: 다섯 plugin key만 노출되고 `variation` 누락
- Pro: 여섯 plugin key 노출
- Business: 빈 `pluginKeys`

웹 가격 화면은 이미 “모든 요금제에서 같은 기능”만 표시해 현재 이 배열을 고객 기능표로 쓰지 않는다. Admin UI도 plugin 편집을 노출하지 않는다. 그럼에도 API 모델과 DB에는 차등처럼 보이는 값이 남아 있어 계약이 모호했다.

### catalog 계약 보완 및 2차 clone 재검증

사용자 승인 뒤 다음 최소 보완을 적용했다.

- `entitlement_mode=all`이면 공개 catalog, Admin catalog, 현재 access 응답이 DB allowlist row가 아니라 현재 등록된 6개 plugin key를 정렬해 반환한다.
- allowlist tier는 저장된 목록을 계속 사용한다. 장래 요금제 차등 여부가 미정이므로 allowlist 스키마 자체는 삭제하지 않았다.
- 관리 API가 tier row를 pessimistic lock으로 잠근 같은 transaction에서 모드 변경·plugin row 정리를 수행한다. 따라서 동시 요청도 `all` tier에 plugin row를 다시 남길 수 없고, allowlist에서 all로 바꿀 때 기존 row가 원자적으로 비워진다.
- `NormalizeAllTierPluginEntitlements1789300000000` migration이 현재 `all` tier의 `plan_plugin_entitlements` row만 삭제한다. 삭제된 과거 파생 목록은 정본이 아니므로 down에서 임의 복원하지 않는다.

코드 검증은 build PASS, 관련 72 PASS, 전체 Web API 2,892 PASS / 21 SKIP이다. 샌드박스 전체 실행의 80개 `listen EPERM`은 로컬 HTTP bind 허용 환경에서 재실행해 전부 통과했다. 독립 코드 리뷰에서 발견한 관리 요청 경쟁 조건은 repository transaction·tier row lock·bound manager 재사용으로 수정한 뒤 전체 검증을 다시 통과했다.

2차 리허설은 기존 첫 clone을 수정하지 않고 새 `clipper-pg-dev-clone-v2-20260918-{user,admin,release}`와 59535/59533/59534를 사용했다. 같은 dump SHA를 확인하고 빈 DB에 다시 복원한 뒤 전체 migration을 적용했으며 두 번째 실행은 세 DB 모두 `No pending migrations`였다. 결과는 다음과 같다.

- trial/basic/pro/business: 모두 `all`, 저장된 plugin entitlement row 0.
- `/catalog`: Basic/Pro/Business 모두 `dance_highlight`, `dialog_highlight`, `shortform_paste`, `shortform_prompt`, `shortform_url`, `variation` 여섯 key 반환.
- `/health`: user/release/admin 모두 `ok`.
- users 20, sessions 162, auth codes 161, projects 1,481 및 문서의 기존 ID 해시가 모두 동일.
- operators 3, provider credentials 7, release versions/builds/artifacts/events 및 ID 해시가 모두 동일.
- onboarding jobs, access grants, credit grants, free trials, subscriptions, payment orders, operation runs는 API 호출 뒤에도 0.

임시 3012 API와 2차 clone 컨테이너는 검증 후 종료했다. 2차 clone volume과 dump는 다음 확인을 위해 보존했다. 실제 개발 DB·서버에는 접속하거나 변경하지 않았다.

## rollback 리허설

- migrated clone DB는 그대로 보존했다.
- 같은 세 컨테이너 안에 별도 `*_rollback_check_20260918` DB를 만들고 원본 dump를 `--single-transaction`으로 복원했다.
- 사용자·세션·auth code·프로젝트, 운영자·provider·옛 금융 테이블, release version/build/artifact/event의 핵심 건수와 ID 집합 해시가 migration 전 기준과 모두 일치했다.
- 검증 뒤 rollback-check DB만 삭제했다. 원본 dump와 migrated clone volume은 유지했다.

따라서 실제 전환 rollback은 migration down이 아니라, 서비스를 멈추고 전환 직전 dump로 세 DB를 함께 복원하는 절차여야 한다. `DropLegacyBilling`과 `ResetLegacyOperationHistory`의 down은 삭제된 행을 복구하지 못한다.

## 남은 게이트

1. 실제 개발서버 전환 명령과 정지 시간, 최종 dump, 순서, post-check, restore rollback 명령을 문서화하고 사용자 확인.
2. 확인 뒤에만 사용자가 개발 DB migration·Web API/웹/새 개발판 배포를 실행.
3. Windows 설치형 실기는 사용자 Windows 서버에서 수행.
4. 실제 ML 플러그인과 Build 5 전체 QA HOLD 유지.

## 변경 상태

- 리허설 종료 시점에는 Web API 제품 코드·테스트·Admin migration 9파일이 미커밋이었다. 이후 사용자 승인으로 `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f`에 commit하고 같은 원격 통합 branch에 push·SHA 확인했다. 새 병합은 없다.
- 실제 개발 DB 변경 0, 개발서버 배포 0.
- 1차·2차 clone 컨테이너는 검증 후 중지했고 전용 volume·dump는 보존했다. 1차 rollback-check DB는 검증 후 제거했다.
- `.codex`의 이전 결과 `c83d20c`까지 사용자 승인으로 `origin/main`에 push됐다. 이번 전환 런북과 최신 handoff 갱신은 현재 문서 커밋 대상이다.
