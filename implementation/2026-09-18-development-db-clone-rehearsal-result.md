# 개발 DB 복제본 PG 전환 리허설 결과

검증일: 2026-09-18 KST

## 결론

실제 개발 DB 3개의 read-only custom dump를 별도 로컬 PostgreSQL 16 컨테이너에 복원하고, 현재 통합 브랜치 migration을 적용한 뒤 반복 실행 no-op, API 기동, 핵심 데이터 보존, dump 복원 rollback을 검증했다. 실제 개발 DB·개발서버·원격 서비스는 변경하지 않았다.

Migration 자체와 사용자·로그인·프로젝트·운영자·provider credential·release 데이터 보존은 통과했다. 기존 개발 금융·이용권·operation 이력은 승인된 출시 전 정책대로 제거되고 새 PG 금융 원장은 빈 상태로 시작한다. 기존 20명에게 무료체험이 소급 지급되지 않는 것도 API 기동 전후 수치로 확인했다.

단, 공개 `/catalog` 응답에는 `entitlement_mode=all`과 함께 과거 allowlist row가 그대로 노출되어 Basic에서 `variation`이 빠지고 Business는 빈 `pluginKeys`로 보이는 의미상 불일치가 발견됐다. 실제 operation 시작은 access/allowlist가 아니라 유효 크레딧을 기준으로 하므로 현재 코드에서 기능을 막지는 않지만, API 소비자와 미래 작업자를 오도할 수 있다. 새 코드 수정 범위를 사용자에게 설명하고 승인받기 전까지 실제 개발 DB 전환 계획 확정으로 넘어가지 않는다.

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

웹 가격 화면은 이미 “모든 요금제에서 같은 기능”만 표시해 현재 이 배열을 고객 기능표로 쓰지 않는다. Admin UI도 plugin 편집을 노출하지 않는다. 그럼에도 API 모델과 DB에는 차등처럼 보이는 값이 남아 있어 계약이 모호하다. 현재 사용자 결정은 장래 차등 사용 여부가 미정이므로 allowlist 스키마를 즉시 삭제하지 않되, 현 정책의 네 tier가 동일하게 보이도록 seed/API 계약을 정리하는 최소 수정안을 우선 제안한다. 승인 전 코드는 변경하지 않는다.

## rollback 리허설

- migrated clone DB는 그대로 보존했다.
- 같은 세 컨테이너 안에 별도 `*_rollback_check_20260918` DB를 만들고 원본 dump를 `--single-transaction`으로 복원했다.
- 사용자·세션·auth code·프로젝트, 운영자·provider·옛 금융 테이블, release version/build/artifact/event의 핵심 건수와 ID 집합 해시가 migration 전 기준과 모두 일치했다.
- 검증 뒤 rollback-check DB만 삭제했다. 원본 dump와 migrated clone volume은 유지했다.

따라서 실제 전환 rollback은 migration down이 아니라, 서비스를 멈추고 전환 직전 dump로 세 DB를 함께 복원하는 절차여야 한다. `DropLegacyBilling`과 `ResetLegacyOperationHistory`의 down은 삭제된 행을 복구하지 못한다.

## 남은 게이트

1. catalog의 stale `pluginKeys`를 네 tier 동일 계약으로 정리할지 사용자 승인 후 코드·migration·테스트 보완.
2. 보완 후 dump에서 새 clone을 다시 만들어 migration/API smoke를 처음부터 재실행.
3. 실제 개발서버 전환 명령과 정지 시간, 최종 dump, 순서, post-check, restore rollback 명령을 문서화하고 사용자 확인.
4. 확인 뒤에만 사용자가 개발 DB migration·Web API/웹/새 개발판 배포를 실행.
5. Windows 설치형 실기는 사용자 Windows 서버에서 수행.
6. 실제 ML 플러그인과 Build 5 전체 QA HOLD 유지.

## 변경 상태

- 이번 단계의 제품 코드 변경 0, 새 병합 0, 코드 commit/push 0.
- 실제 개발 DB 변경 0, 개발서버 배포 0.
- 로컬 clone DB와 rollback-check DB만 사용했고 rollback-check DB는 검증 후 제거했다.
- clone 컨테이너 3개는 검증 후 중지했고, 재검증을 위해 컨테이너·전용 volume·dump는 보존했다.
- `.codex` 결과/인계 문서만 갱신한다.
