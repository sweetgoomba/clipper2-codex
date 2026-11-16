# Resend → SES 독립 검토 2차

검토일: 2026-11-10 (Asia/Seoul). 기존 보고서를 보존하고 최종 미커밋 코드·새 파일·설정을 다시 읽은 뒤 새 검증을 실행했다.

**결론: 새로 재현한 조건부 P2 1건 — 기존 불확실 발송의 제공자/스키마 전환 처리 누락. 최초 검토의 만료 경합 P2는 최종 코드에서 해소된 상태를 다시 확인했다.** P0/P1은 이번 검토에서 확인하지 못했다. 전체 테스트 통과가 아래 전환 경계의 안전성을 보장하지는 않는다.

## 대상 및 스냅샷

| 대상 | 절대 경로 | HEAD/base | 미커밋 검토 파일 |
|---|---|---|---|
| API | `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api` | `130c81e8e2fd3e7759072be6ba22fb269c5f128b` | tracked 17개 + untracked 2개 |
| Infra | `/Users/jina/.codex/worktrees/mail-integration-infra-261109/clipper_infra` | `50b2038c97afea62bf75603feb33efbbf876c5d8` | tracked 5개 + untracked 1개 |

양쪽 브랜치는 `feat/resend-to-ses-261110`. 실제 `git diff`를 다시 검토했고, 새 `1794270000000-InquiryDeliveryOutcomes.ts`, `inquiry-delivery.module.ts`, `scripts/mail-env.test.mjs`도 별도로 읽었다. 공통 SES sender, 기존 migration/문의 coordinator, 운영자 서비스·템플릿, 고객 자동발송 큐와 관련 Nest 모듈도 대조했다.

Coordinator SHA-256: `7e48339c65bb7db208b4d881ca465b3c90fb3856f0470f34a83280916b664b50`.

전체 변경 파일별 SHA-256 manifest: `/private/tmp/clipper-ses-independent-round2-source-manifest.json`, manifest 자체 SHA-256: `90b1fb7e95098f3e4475c6639f8de8bd5ae05fa091388e0f50cf6c74347ca60d`. 검증 후 API 19개/Infra 6개의 파일 목록과 바이트 해시, HEAD, 브랜치가 시작 시점과 같음을 다시 확인했다. 파일별 해시는 문서 끝에도 보존한다.

## 새 발견 사항

### [P2] 이전 불확실 발송을 migration에서 빈 fence로 전환해 같은 문의를 다른 제공자로 재발송한다

- 주 위치: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/core/database/migrations/admin/1794270000000-InquiryDeliveryOutcomes.ts:6` (6–11행)
- 관련 복구 조건: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/modules/mail-events/inquiry-receipt-coordinator.ts:59` (59–61행 및 74–87행)
- 관련 rollback: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/core/database/migrations/admin/1794270000000-InquiryDeliveryOutcomes.ts:18`

**발생 조건:** 기존 Resend가 문의를 수락했지만 API가 응답을 받거나 `forwarded_at`을 저장하기 전에 중단되어, staging에 `pending`, `attempts>0`, `forwarded_at=NULL`인 행이 남아 있는 상태에서 새 버전으로 전환한다.

기준 코드는 Resend의 `Idempotency-Key: inquiry-<id>`를 이용하므로 이런 행을 같은 제공자로 재시도할 여지가 있었다. 새 migration은 기존 모든 행의 `send_started_at`을 NULL로 만들고, 이전 시도 여부에 따른 보호나 분류를 하지 않는다. 새 복구는 이 NULL을 아직 발송을 시작하지 않은 상태로 간주해 SES를 호출한다. Resend에서 이미 수락한 발송과 SES 발송 사이에는 기존 idempotency key가 작동하지 않아 같은 회사 문의가 두 번 전송될 수 있다.

**독립 재현 절차와 관측:**

1. 허용된 테스트 DB의 별도 스키마에 실제 기존 `AutomaticInquiryReceipts1794180300000` migration을 적용했다.
2. 기준 커밋의 실제 coordinator를 `git show`로 읽어 메모리에서 컴파일하고, 기존 실제 ResendInquiryMailer와 함께 별도 Node 프로세스에서 실행했다. 네트워크는 메모리 스텁이며, 스텁이 요청 수락을 기록한 직후 프로세스를 종료했다. 실제 Resend/SES 요청은 하지 않았다.
3. 실제 DB에 `pending`, `attempts=1`, `forwarded_at=NULL`, 기존 lease가 남는 것을 확인했다.
4. 실제 새 migration을 적용했다. `send_started_at=NULL`인 것을 확인하고, 이전 2분 lease가 경과한 조건만 DB 시간으로 모의했다.
5. 최종 coordinator, SesInquiryMailer, SesMailSender를 실행하되 SES client만 메모리 스텁으로 대체했다. `recover()`가 동일 문의를 SES에 1회 추가 제출했고 행은 `settled`, `attempts=2`가 됐다.

```json
{"legacyFixtureAccepted":1,"sesCalls":1,"events":1,"migrated":{"status":"pending","attempts":1,"forwarded_at":null,"send_started_at":null,"last_error_code":null},"post":{"status":"settled","attempts":2,"payload":null}}
```

이는 실제 운영에서 중복이 발생했다고 주장하는 것이 아니다. **이전 제공자 수락이 있었던 durable 상태에서 새 코드가 재전송하는 조건부 결함을 재현한 것**이다. 전환 시 그런 행이 전혀 없다면 영향은 없다. 운영 DB는 요청에 따라 조회하지 않았으므로 그 전제의 충족 여부는 확인하지 않았다. 현재 runbook에는 기존 recovery가 SES로 바뀐다고만 쓰여 있으며 해당 행의 해소/격리 조건은 없다.

**같은 정보 손실을 rollback에서도 확인:** 새 버전에서 uncertain timeout을 만든 뒤 새 migration을 down/up 하면 pending 행의 `send_started_at`이 다시 NULL이 된다. 재시도 시각 도래 조건을 만든 뒤 복구하면 client 호출이 1회에서 2회로 늘었다. 이 경우 실제 수락 여부가 불명확하므로 중복 도착 자체를 입증한 것은 아니지만, 현재 fence가 보장하던 자동 재전송 금지가 스키마 전환만으로 사라짐은 입증했다. 하나의 전환 보호 문제로 묶어 별도 중복 finding은 만들지 않았다.

**수정 방향:** 제공자 전환 전 기존 미확정 시도를 안전하게 소진/확인하거나, 기존 시도 이력이 있는 unforwarded 행을 자동 재전송 대상에서 보수적으로 격리하는 migration/전환 절차가 필요하다. rollback도 pending uncertain 정보를 잃어 재발송하지 않도록 처리하거나 명시적 안전 전제와 검증 절차가 있어야 한다. SNS 등 새 기능을 반드시 도입해야 한다는 요구는 아니다.

증거: `/private/tmp/clipper-ses-independent-round2-transition.cjs`, `/private/tmp/clipper-ses-independent-round2-transition-final.log`.

## 전 범위 재검토 및 정상 확인

| 검토 항목 | 이번에 확인한 근거와 결과 |
|---|---|
| 문의 제출/복구 SES 바인딩 | 실제 InquiriesModule을 Nest TestingModule로 컴파일. InquiriesService.mailer와 InquiryReceiptCoordinator.recoveryMailer가 같은 InquiryMailer 인스턴스이며 SES sender를 사용함을 assertion으로 확인 |
| 운영자 초대/재초대/재설정 | AuthModule의 실제 provider factory를 찾아 실제 OperatorAccountsService와 연결. 세 호출의 수신자·제목·발급 링크를 실제 SES command에서 확인. 실패 시 `mailSent=false`와 링크 반환 계약도 유지 |
| env-only 주소 | 실제 MailModule/InquiryDeliveryModule factory와 sender 실행. From/회사 To/방문자 Reply-To가 fixture env를 따름. From 또는 To가 없으면 네트워크 호출 전에 실패하고 Resend/과거 발신 주소로 fallback하지 않음 |
| 내부 메일 이력/비밀 | 내부 provider는 queue/campaign 의존 없이 SES를 직접 호출. 실제 command에 campaign/delivery tag가 없고, 운영자 audit fixture에 원문 토큰이 없음을 확인. 실제 PostgreSQL 전체 테스트에서도 내부 전달과 고객 접수 안내 캠페인만의 분리가 통과 |
| 일반 재시도·중복 방지 | 전체 기존 테스트 및 새 경계 probe에서 확인. 같은 ID 8개 동시 재요청/이후 복구/재제출은 회사 발송 1회·고객 안내 등록 1회 |
| uncertain/프로세스 중단 | 새 스키마에서 send-start가 있는 unforwarded 행은 자동 복구에서 제외. uncertain과 확정 거절을 실제 adapter가 구분. 위 migration 경계만 별도 결함 |
| 원문 만료/늦은 성공 | 실제 시간 400ms/500ms 경합을 새로 실행. 성공 응답 전에 payload NULL. 늦은 성공과 첫 완료 쓰기 실패 모두 최종 `receipt_expired`, forwarded_at 있음, 고객 안내 신규 등록 0회 |
| 늦은 거절/uncertain | 만료 정리 후 각각 최종 forward_expired 유지, 성공으로 오분류하지 않음. 이후 복구에서 재발송 없음 |
| 완료 쓰기와 안내 등록 사이 만료 | 성공 쓰기 후 소유권 잠금 전에 만료 정리하면 receipt_expired, 원문 NULL, 안내 등록 0회 |
| 기존 정상 상태 이관 | old-shaped never-attempted/forwarded-pending/settled 세 행의 복구에서 발송은 never-attempted 1건만, 안내 등록은 pending 두 건만, 모두 원문 NULL. 이미 forwarded인 문의는 재발송하지 않음 |
| migration 구조 | admin datasource 등록 및 적용 순서, 실제 up/down/up의 SQL 동작은 확인. 새 terminal 상태 rollback 변환도 전체 PG 테스트 통과. 데이터 의미 보존의 빈틈은 위 finding |
| Compose/예시/설정 | base/dev/stage/prod YAML 파싱. dev/stage/prod 각각 명시 주소/빈 주소 두 경우 실제 `docker compose config --format json` 실행: API에만 주소 전달, 빈 값은 빈 값 유지, Resend 두 env 제거 확인. 실제 컨테이너 실행/배포는 하지 않음 |

미사용 Resend 클래스는 남아 있지만 활성 Nest 바인딩이나 자동 fallback은 발견하지 못했다. SES 전용 키 두 개의 동시 설정 검사 및 기본 credential chain 동작은 기존 구현대로이며 이번 전체 테스트에 포함됐다. 고객 접수 안내의 기존 별도 queue/template/history 경로는 유지됐다.

## 새로 실행한 명령과 결과

API cwd: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api`

```sh
CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent > /private/tmp/clipper-ses-independent-round2-full-api.log 2>&1
npm run build > /private/tmp/clipper-ses-independent-round2-build.log 2>&1
git diff --check
```

- 전체 API: **exit 0, 540 suites / 6,281 tests 통과**, 30 suites / 524 tests skip, snapshots 5 통과. 고정 `localhost:55439`의 실제 PostgreSQL 메일 통합 테스트 포함. 이번 실행 결과이며 기존 로그를 재인용하지 않았다.
- 빌드 exit 0. diff 공백 검사 출력 없이 통과.

Infra cwd: `/Users/jina/.codex/worktrees/mail-integration-infra-261109/clipper_infra`

```sh
node --test scripts/deployment.test.mjs scripts/mail-env.test.mjs scripts/deploy-aws-prod.test.mjs scripts/validate-toss-payments-env.test.mjs > /private/tmp/clipper-ses-independent-round2-infra.log 2>&1
git diff --check
```

- **exit 0, 135 tests 통과**, 실패/skip 0. 배포 테스트는 로컬 fixture/stub 기반이며 실제 서버/AWS 배포는 하지 않았다.
- base/dev/stage/prod 4개 YAML은 설치된 js-yaml `load()`로 파싱 통과. diff 공백 검사 통과.

추가 스크립트(제품 소스 변경 없이 임시 경로에 작성/실행):

```sh
node /private/tmp/clipper-ses-independent-recheck-probes.cjs > /private/tmp/clipper-ses-independent-round2-boundaries.log 2>&1
node /private/tmp/clipper-ses-independent-round2-transition.cjs > /private/tmp/clipper-ses-independent-round2-transition-final.log 2>&1
node /private/tmp/clipper-ses-independent-round2-wiring.cjs > /private/tmp/clipper-ses-independent-round2-wiring.log 2>&1
node /private/tmp/clipper-ses-independent-round2-db-failures.cjs > /private/tmp/clipper-ses-independent-round2-db-failures.log 2>&1
node /private/tmp/clipper-ses-independent-round2-compose.cjs > /private/tmp/clipper-ses-independent-round2-compose.log 2>&1
```

모두 최종 exit 0. 첫 스크립트는 기존 재현 코드를 최종 새 빌드에 **새로 실행**해 6개 경계 assertion을 재확인했다. 전환 스크립트는 결함이 발생한다는 assertion의 통과이며 제품 성공 판정이 아니다. 이 스크립트의 최초 실행(`/private/tmp/clipper-ses-independent-round2-transition.log`)은 마지막 down/up 검사에서 backoff 도래 전 즉시 재시도를 기대해 assertion이 실패했다. 재시도 시각을 도래 조건으로 보정한 뒤 위 final 로그에서 모두 재현했다. 제품 코드는 변경하지 않았다.

## 결함과 구분한 실제 장애 관측/한계

이번에는 이전 보고서에서 추론으로 남긴 다음 DB 장애도 별도로 주입했다.

- send-start 쓰기가 커밋 전에 실패하면 최초 네트워크 호출 0회. 복구 후 발송/안내 등록 각 1회로 정상 완료했다.
- send-start는 커밋됐지만 응답만 유실된 조건이면 실제 발송 전이어도 fence가 남고 자동 발송은 0회로 멈춘다. 프로세스 중단/불확실 수락에 대해 중복 방지를 우선하는 현재 정책의 손실 가능성이다.
- 회사 발송 성공 후 첫 완료 쓰기와 catch 보완 쓰기가 모두 실패하면 최초 accept는 정상 반환하지만 DB는 불확실 pending에 남는다. 복구는 재발송하지 않고 안내 등록도 못 하며 만료 후 forward_expired/원문 NULL이 된다. 발송 1회, 안내 등록 0회를 실제로 확인했다. 이는 durable 수락 증거를 잃은 상황에서 현재 선택한 at-most-once 한계이며, 단일 DB 쓰기 실패 보완을 모든 연속 장애의 완전 복구로 해석하면 안 된다. 새 기능 확대를 별도 버그 수정으로 요구하지 않는다.
- 동일 submissionId 밖의 새 요청/페이지 재로드를 내용만으로 병합하지 않는다. 실제 SES 수락/반송, IAM, configuration set, SNS, 운영 환경변수와 migration 적용 상태는 검증하지 않았다.
- 실제 제공자 수락은 메모리 fixture로 모의했다. 전환 결함의 증명 대상은 그 durable 상태에서 실제 새 코드가 재발송한다는 제어 흐름이며 실제 이메일 중복 도착이나 현재 운영 행 존재 여부가 아니다.

## 작업 경계와 종료 상태

읽기 및 허용된 검증 외 제품 코드 수정, 브랜치 변경, 커밋/푸시/병합, 서버 접속/배포, 개발·운영 DB/AWS 수정, 실제 이메일 발송은 하지 않았다. 사용한 DB는 `127.0.0.1:55439`, role `clipper_mail_test`, DB `clipper_mail_user_test`/`clipper_mail_admin_test`뿐이다. 추가 probes의 독립 스키마는 finally에서 삭제됐다. 모든 테스트/빌드/child 프로세스는 종료했으며 클러스터는 유지했다. 이전 보고서는 수정하지 않았다.

## 파일별 소스 SHA-256

```json
{
  "api": {
    "HEAD": "130c81e8e2fd3e7759072be6ba22fb269c5f128b",
    "files": {
      ".env.example": "149884b6e717ab9dbbe8d8e524a2f54961ce6a290723e3299b207b7000ba7783",
      "docs/api/openapi.yaml": "e22b4baa608b82568d26f568c26205f62d1938ec01c19ce7ea712eb6a5c806cf",
      "src/core/database/admin.datasource.ts": "0d62856773444e50a4ab4ee0d41412478298081fa34b8fdd6d2e9927cbc6d6ed",
      "src/core/database/migrations/admin/1794270000000-InquiryDeliveryOutcomes.ts": "6966669e1b47531fdec77a763a894e4b6d36a721ffdac82256486068fa3f2ca6",
      "src/core/mail/legacy-mail-adapters.spec.ts": "a7a557655ef743c4c913bd1692941ae54f1eb95c21bfbb6da8a11e4c7dcecba0",
      "src/core/mail/mail.module.spec.ts": "ba1b234d6a64d4aa1c5b921bab13b1228108ef601f2741314a671f96bc5b9f2f",
      "src/core/mail/mail.module.ts": "6652c9da51a05f9f1d0744e1beebbb8e46230c582bb93acf5733a7b536de1d1f",
      "src/modules/auth/application/operator-mailer.ts": "f601c783002b6c7699d11ba26d129c9736723c4be77fed2228c874326b351622",
      "src/modules/auth/auth.module.ts": "18d04950bcd080fc97fea3eb1bb970d940e649b9b979ea286593725b25bae6e3",
      "src/modules/inquiries/application/inquiries.service.ts": "14768b8051ec5321ab272be9fbb709c1487a74b9fb39f70aca052d32f59f0402",
      "src/modules/inquiries/application/inquiry-mailer.ts": "bb44b743097b5fb92ff9078c966df166332c7139dbe387d8c030dd7d9f1b4eed",
      "src/modules/inquiries/infrastructure/inquiry-delivery.module.ts": "dd82ab3290ac42adbdf6c62e32203b96945cad581e80237e4c9eac0df7734e5b",
      "src/modules/inquiries/infrastructure/ses-inquiry-mailer.ts": "95fe76c7af10d7878cf251fa2eb5c22dc8a9febc6885dba0ba3da50d3f6126a6",
      "src/modules/inquiries/inquiries.module.spec.ts": "767d6ec1949548174d64c2b0c14d27501db8b05cf7e8aa0d3501d6c2b3d58d74",
      "src/modules/inquiries/inquiries.module.ts": "0730c5b2cb8c93cfaa0260bd5756b2eaf189e9c696433f2daf7c22904f1a7c78",
      "src/modules/mail-events/inquiry-receipt-coordinator.spec.ts": "ec7f6f47acec3360a15e9ce216447a8dfc6ab0492d8ba5dc1e7312aa6becceaf",
      "src/modules/mail-events/inquiry-receipt-coordinator.ts": "7e48339c65bb7db208b4d881ca465b3c90fb3856f0470f34a83280916b664b50",
      "src/modules/mail-events/mail-events.module.ts": "3ff05234e8bd3d1ff5b82cc35ed04480f0f3b5e5fa8ebc2f71f8aa38cc9a007a",
      "src/modules/mail/infrastructure/mail-postgres.integration.spec.ts": "7551ed32564c34dc52841d2f2aac725fe648cbd518f87b844028925f58760dc1"
    }
  },
  "infra": {
    "HEAD": "50b2038c97afea62bf75603feb33efbbf876c5d8",
    "files": {
      "apps/compose.yml": "fcfef3cb89bbec054d21d62e42e74cefdbb118d6a68a919017ccd171696c3de9",
      "env/stack.dev.env.example": "7248f61c11b705cbf430f0f94274251712dfd4d36f0874c37a0a5c86aba45f68",
      "env/stack.prod.env.example": "ffbf322917603d713ea6b46d0bca3b55a390b8e314e87946c363b5abb964f947",
      "env/stack.stage.env.example": "a47fcdf9016926ee3db207e412a4d5135b3bb69ee95f341499a34a02be249712",
      "runbooks/deploy-dev.md": "9218601bb765f6fa2adf1a9369429b95fc130e3ee865433c4fdcbecf5a821e91",
      "scripts/mail-env.test.mjs": "cbfcdb36a3b8ba0ae536d43028ee3349cec06aab1c3ec481bf96d5ce4b8d0c36"
    }
  }
}
```

## 전환 P2 수정 후 독립 재검증 — 2026-11-10

**최종 판정: 이 보고서의 provider/schema 전환 P2는 아래 수정 스냅샷과 문서화된 전환 조건 아래 해소됐다. 수정 범위에서 새 actionable 결함은 발견하지 못했다.** 최초 발견과 당시 증거는 위에 보존하며 현재 판정은 이 후속 절을 따른다. 최초 만료 경합 P2도 재발하지 않았다.

### 재검토한 변경 범위와 해시

이전 2차 스냅샷의 전체 파일 manifest와 실제 현재 바이트를 비교했다. 바뀐 파일은 아래 3개뿐이며 coordinator를 포함한 나머지 검토 파일은 같았다.

| 파일 | 현재 SHA-256 |
|---|---|
| `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/core/database/migrations/admin/1794270000000-InquiryDeliveryOutcomes.ts` | `093c3b68061859285a015e671956de0972169fb995ee52fccf7a1ac1160a7354` |
| `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/modules/mail/infrastructure/mail-postgres.integration.spec.ts` | `3ff0c9fa9fe80e185326ab2b1fadf06a0e7494a5ac88fa60ea5012ca2554580a` |
| `/Users/jina/.codex/worktrees/mail-integration-infra-261109/clipper_infra/runbooks/deploy-dev.md` | `61ec7e8063701a3a94db63623cde93597aba889debd970119f203cac9068f62a` |

Coordinator SHA-256은 계속 `7e48339c65bb7db208b4d881ca465b3c90fb3856f0470f34a83280916b664b50`이다.
새 전체 manifest: `/private/tmp/clipper-ses-independent-cutover-recheck-source-manifest.json`, 자체 SHA-256 `f8e576eea5947a14ad6cf7b74eb0626eb05eeda1eb6f63fb4f29fd581b4cf7fb`.
검증 종료 시 API/Infra의 전체 미커밋 파일 목록과 각 파일 해시가 이 새 manifest와 같음을 확인했고 양쪽 `git diff --check`도 통과했다.

### 코드·운영 절차 재검토

- 실제 migration up을 다시 읽었다. 기존 `pending AND attempts>0 AND forwarded_at IS NULL` 행만 `LEGACY_FORWARD_UNCERTAIN`/send-start fence로 격리한다. never-attempted/이미 forwarded/기존 settled 행은 격리하지 않는다. 받은 시각이나 원문 만료 기한을 바꾸지 않는다. 새 timestamp는 이관 격리 시각이며 과거 네트워크 시작 시각으로 해석하지 않는다.
- 실제 migration down은 pending + send-start 있음 + forwarded_at 없음 행이 있으면 `INQUIRY_UNCERTAIN_FORWARDING_BLOCKS_ROLLBACK`으로 DDL 전에 거절한다. 만료 정리된 terminal 행 및 이미 전달 확인된 행은 이 차단 조건에서 제외된다.
- runbook의 모든 이전 API 중지 후 migration/새 API 시작 순서, 구/신 worker 동시 운영 금지, 불확실 행이 남아 있을 때 스키마 유지 여부와 무관한 구버전 binary rollback 금지, 제공자/회사 수신함 확인 전 강제 재시도 금지를 읽었다.
- 이번 판정은 이 문서화된 전환 절차를 포함한다. schema 사전 검사가 임의 구버전 binary 실행이나 동시 운영을 자동으로 차단한다고 판정하지 않는다. 실제 운영 API 중지 상태와 provider 기록은 접근 금지 범위에 따라 확인하지 않았다.
- 통합 테스트의 수동 QueryRunner가 `finally`에서 release되도록 정리된 부분도 검토했다. 이번 단독 실제 PG 실행은 대기/풀 고갈 없이 종료했다.

### 새로 실행한 검증

API cwd: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api`

```sh
CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent inquiry-receipt-coordinator mail-postgres.integration > /private/tmp/clipper-ses-independent-cutover-recheck-tests.log 2>&1
npm run build > /private/tmp/clipper-ses-independent-cutover-recheck-build.log 2>&1
```

- **exit 0, 2 suites / 44 tests 통과**(실제 PG 37개와 coordinator 7개), skip 없음. 새 legacy 격리/rollback 거절 회귀 테스트 포함.
- **빌드 exit 0.**
- 이번 요청대로 수정 범위 중심으로 실행했다. 전체 6,283개 테스트와 Infra 전체를 이번 후속 검토에서 독립 재실행했다고 주장하지 않는다.

별도 독립 재현:

```sh
node /private/tmp/clipper-ses-independent-cutover-recheck-transition.cjs > /private/tmp/clipper-ses-independent-cutover-recheck-transition.log 2>&1
node /private/tmp/clipper-ses-independent-recheck-probes.cjs > /private/tmp/clipper-ses-independent-cutover-recheck-boundaries.log 2>&1
```

두 명령 모두 **exit 0**. 실제 현재 빌드와 실제 migration을 사용했고 네트워크 전송 부분만 메모리 스텁으로 대체했다. 이전 script/로그는 덮어쓰지 않았다.

| 독립 재현 | 실제 관측 및 assertion |
|---|---|
| 기존 Resend 수락 직후 기준 프로세스 종료 → 새 up migration | 최초 발견과 같은 자식 프로세스 종료 순서. 남은 실제 pending 행이 격리되고 복구 및 동일 ID 재요청에서도 해당 문의의 SES 추가 발송 0회 |
| 정상 old-shaped 행 동시 이관 | never-attempted만 회사 발송 1회, 이미 forwarded는 안내만 등록, historic settled는 재전송 없음. pending 정상 두 행의 안내 등록만 2회 |
| 이관 metadata/로그 개인정보 | 경고 1건은 격리 건수 1만 포함하며 email/문의 본문/ID 없음. received_at/expires_at과 보관 중 payload가 migration 전후 동일 |
| legacy 격리 행 rollback 시도 | 실행 SQL은 SELECT 1개뿐. 정확한 오류로 거절됐고 두 metadata 열 및 fence가 보존됨. DDL 실행 0회 |
| legacy 격리 행 만료 및 이후 안전한 down/up | forward_expired, payload NULL, LEGACY_FORWARD_UNCERTAIN 보존. 이후 down/up/recover해도 추가 전송 없음 |
| 신규 SES uncertain timeout 후 rollback 시도 | 동일한 DDL 전 거절. 최초 send-start가 그대로 남고 재시도 시각 도래 후에도 네트워크 호출 수 1회 유지 |
| 신규 uncertain의 원문 만료 후 down/up | 원문 삭제/terminal 변환 후 down/up이 가능하며 추가 발송 없음 |
| never-attempted/이미 forwarded pending의 down/up | 둘은 정상 통과. 이후 회사 발송은 never-attempted 1회뿐이고 안내 등록은 두 건. 이미 확인된 전달 재발송 없음 |
| 기존 실제 시간 만료 경합 등 6개 probe 재실행 | 늦은 성공/첫 완료 DB 쓰기 실패/늦은 uncertain/늦은 거절/8개 동시 재요청/성공 쓰기와 안내 잠금 사이 만료 모두 통과. 원문 삭제 및 정상·forward_expired·receipt_expired 구분 유지 |

기존 제공자의 확정 거절과 수락을 과거 행에서 구별할 근거가 없으므로, 이미 시도했지만 전달 확인이 없는 행을 보수적으로 격리하는 것은 명시한 정책이다. 과거에 실제 전송되지 않았던 행도 자동 복구가 보류될 수 있으며 이는 허위 수락 이력 복원이 아니다. 기존 보고서의 at-most-once/연속 DB 장애/운영 환경 미검증 한계는 계속 유효하다.

검증자는 제품 코드를 수정하거나 서버/AWS/실제 메일에 접근하지 않았다. 사용한 DB는 허용된 `127.0.0.1:55439`의 테스트 DB뿐이다. 별도 임시 스키마는 finally에서 삭제했고 모든 테스트·빌드·자식 프로세스는 종료했다. PostgreSQL 클러스터는 유지했다.
