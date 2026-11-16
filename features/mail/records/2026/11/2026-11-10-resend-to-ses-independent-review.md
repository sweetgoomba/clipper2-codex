# Resend → SES 독립 검토

- 검토일: 2026-11-10 (Asia/Seoul)
- 결론: **P2 재현 결함 1건. 수정 후 재검증 필요.** P0/P1 결함은 이번 검토에서 확인하지 못했다.
- 검토자는 제품 소스·브랜치·커밋을 수정하지 않았다. 실제 서버, 운영/개발 DB, AWS, 실제 메일 발송을 사용하지 않았다.
- 먼저 인계 문서를 읽고, 아래 두 작업공간의 실제 미커밋 diff와 untracked 파일을 모두 확인했다.

## 검토 대상

| 대상 | 작업공간 | 확인한 HEAD/base |
|---|---|---|
| API | `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api` | `130c81e8e2fd3e7759072be6ba22fb269c5f128b` |
| Infra | `/Users/jina/.codex/worktrees/mail-integration-infra-261109/clipper_infra` | `50b2038c97afea62bf75603feb33efbbf876c5d8` |

API tracked 17개 파일, untracked 마이그레이션 `1794270000000-InquiryDeliveryOutcomes.ts`와 `inquiry-delivery.module.ts`, Infra tracked 5개 파일 및 untracked `scripts/mail-env.test.mjs`를 검토했다. 초기 전체 테스트 이후 다른 세션에서 `mail-postgres.integration.spec.ts`에 `lets a leased in-flight send settle before expiry cleanup` 테스트가 추가된 것을 관찰했다. 아래 전체 테스트 통과 수에는 이 후속 테스트가 포함되지 않는다. 해당 추가 파일은 검토자가 수정하지 않았다.

아래 결함을 재현한 `inquiry-receipt-coordinator.ts` 소스 SHA-256은 `f2ad26773e0d68b163a87f3b5b826e5e5746adac8bdd46a848ff7455df0ccd61`이다. 보고서는 이 소스를 기준으로 한다. 검토 중 해당 제품 소스의 변경은 관찰하지 않았다.

## 발견 사항

### [P2] 만료 정리가 진행 중인 발송의 소유권까지 지워 확정 성공을 회사 전달 만료로 남긴다

- 주 위치: `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/modules/mail-events/inquiry-receipt-coordinator.ts:51` (51–56행)
- 관련 위치: 같은 파일 89행 및 92–94행
- 발생 조건: 24시간 기한 직전에 복구 발송이 시작되고, SES 응답을 기다리는 동안 다른 API 인스턴스의 `recover()`가 기한을 지난 행을 정리한다. SES 응답 제한인 10초 안에서도 가능한 순서다.

만료 UPDATE는 유효한 발송 lease도 조건 없이 NULL로 만든다. 이후 메일러가 성공 반환해도 `forwarded_at` UPDATE는 기존 lease token과 일치하는 행을 찾지 못한다. 이 0행 갱신을 검사하지 않으며, 이어지는 트랜잭션은 새 소유권 검사에서 반환한다. 결과적으로 발송 성공을 알고 있는 프로세스가 존재하지만 영구 행은 `forward_expired`, `forwarded_at=NULL`, `INQUIRY_SEND_UNCERTAIN`으로 남고 고객 접수 안내도 등록되지 않는다. 최초 accept는 정상 반환하지만 같은 ID의 재제출은 `FORWARD_RETRY_EXPIRED`가 된다. 이는 요구한 회사 전달 만료와 고객 안내 등록 만료의 구분을 틀리게 하며, 전달이 실패했다고 판단한 수동 재발송을 유발할 수 있다.

**독립 재현:** 허용된 `127.0.0.1:55439/clipper_mail_admin_test`에 별도 `ses_independent_review_261110` 스키마를 만들고 두 실제 마이그레이션을 적용했다. 실제 코디네이터 두 인스턴스와 성공을 반환하는 메모리 메일러를 사용했다. 문의 기한을 400ms 뒤로 설정하고 발송을 보류한 뒤 500ms 후 두 번째 인스턴스에서 복구 정리를 실행하고 성공 응답을 해제했다. 실제 SES를 호출하지 않았다.

관측 결과:

```json
{"sends":1,"events":0,"row":{"status":"forward_expired","forwarded_at":null,"payload":null,"last_error_code":"INQUIRY_SEND_UNCERTAIN"}}
```

같은 순서를 기준 커밋 소스에도 실행했다. 기준 소스는 `git show`로 읽고 메모리에서 컴파일했으며 체크아웃은 바꾸지 않았다. 기준 결과는 발송 1회, 접수 안내 등록 호출 1회였다. 새 코드의 소유권 검사에 따라 안내 등록이 사라진 회귀와 새 만료 상태 오분류를 확인했다.

**수정 방향:** 원문 보관 기한과 자동 재발송 fence는 유지하면서, 이미 시작한 발송의 확정 응답을 만료 정리 뒤에도 최소 메타데이터에 반영할 수 있어야 한다. 성공이 확인된 건을 계속 회사 전달 실패로 취급하지 말고, 안내 등록이 기한을 넘겼다면 그 결과로 분류해야 한다. 단순히 유효 lease 행의 원문 삭제를 무조건 미루면 보관 기한이 늘어나므로 그 정책도 함께 검증해야 한다.

재현 스크립트: `/private/tmp/clipper-ses-independent-probes.cjs`
재현 로그: `/private/tmp/clipper-ses-independent-probes.log`

## 확인된 정상 동작

- 제출과 정기 복구가 `InquiryDeliveryModule`의 동일한 SES InquiryMailer provider를 주입받는다. AuthModule은 SesOperatorMailer를 주입한다. 활성 provider 경로에 Resend fallback은 없었다. 남아 있는 Resend 구현은 활성 바인딩이 아니다.
- 회사 목적지는 `INQUIRY_TO_EMAIL`, 발신자는 `MAIL_FROM_EMAIL`에서만 가져온다. MailModule과 Compose의 실행 가능한 기본 발신 주소가 제거됐다. API/Infra 예시의 회사 수신 주소는 `clipper@metabuzz.co.kr`이다.
- 문의의 회사 수신/방문자 Reply-To, 운영자 수신/제목/링크와 boolean 실패 계약이 유지된다. 내부 전송은 SesMailSender를 직접 사용하여 campaign/delivery 등록 경로를 통과하지 않는다. 고객 접수 안내만 기존 AutomaticMailEventsService/AutomaticMailQueue를 사용한다. 운영자 링크 본문을 새 캠페인이나 문의 staging에 저장하는 경로는 발견하지 못했다.
- 확정 거절은 send-start fence를 해제하여 재시도하며, timeout 등 불확실 결과는 동일 ID 재요청과 복구에서 재발송하지 않는다. send-start 후 프로세스 중단 상태도 자동 재발송하지 않는다.
- 첫 `forwarded_at` 쓰기만 실패하는 경우 catch 경로가 성공을 보존하여, 다음 복구는 접수 안내 등록만 한다. 등록 트랜잭션의 소유권 검사와 캠페인 고유 키를 확인했다.
- 독립 실제 PostgreSQL probe에서 발송을 보류한 상태로 같은 ID 재요청 8개를 동시에 실행하고 이후 복구했다. 발송 1회, 안내 등록 1회, `settled`, 원문 NULL이었다. 8개의 진행 중 재요청은 uncertain 오류로 거절됐으며 중복 발송은 없었다.
- 만료 시 원문을 삭제하고 정상 완료/회사 전달 만료/접수 안내 등록 만료를 별도 상태로 저장하는 스키마는 유효했다. 새 migration의 up/down/reapply 테스트가 포함되어 있고, admin datasource에 등록됐다. 기존 상태를 무리하게 재분류하지 않으며 down은 새 terminal 상태를 settled로 변환한다.
- Compose/예시/운영 문서가 SES 전환 및 migration 선행 실행을 설명한다. 내부 전송은 MAIL_WORKER_ENABLED와 독립적이다.

## 독립 실행 결과

API 작업공간에서:

```sh
CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent > /private/tmp/clipper-ses-independent-full-test.log 2>&1
npm run build > /private/tmp/clipper-ses-independent-build.log 2>&1
git diff --check
```

- 전체 테스트: exit 0. **540 suites / 6,279 tests 통과**, 30 suites / 524 tests skip, snapshots 5 통과. 고정 localhost 테스트 설정의 실제 PostgreSQL 메일 테스트를 포함한다. 초기 샌드박스 실행은 HTTP 테스트의 `listen` EPERM으로 중단됐고, 확장 실행에서 위 결과를 얻었다. 이는 제품 테스트 실패가 아니다.
- 빌드: exit 0.
- diff 공백 검사: 출력 없이 통과.

Infra 작업공간에서:

```sh
node --test scripts/deployment.test.mjs scripts/mail-env.test.mjs scripts/deploy-aws-prod.test.mjs scripts/validate-toss-payments-env.test.mjs > /private/tmp/clipper-ses-independent-infra-test.log 2>&1
git diff --check
```

- **135 tests 통과**, 실패/skip 0, exit 0. 배포 테스트는 로컬 스텁 기반이며 실제 서버 배포를 실행하지 않았다.
- `apps/compose.yml`, `apps/compose.dev.yml`, `apps/compose.prod.yml`을 설치된 js-yaml의 `load()`로 각각 파싱하여 모두 통과.
- diff 공백 검사: 출력 없이 통과.

추가 독립 재현:

```sh
node /private/tmp/clipper-ses-independent-probes.cjs > /private/tmp/clipper-ses-independent-probes.log 2>&1
```

- exit 0: 위 만료 경합 결함 assertion, 기준 커밋 비교, 동시 재요청/복구 단일 발송 assertion 모두 관측한 결과와 일치했다. 결함 재현 assertion의 통과는 제품 동작이 올바르다는 의미가 아니다.
- 별도 테스트 스키마는 finally에서 삭제했고 PostgreSQL 클러스터 자체는 중지하지 않았다.

## 결함과 구분한 한계

- send-start를 저장한 직후 네트워크 호출 전에 프로세스가 죽어도 자동 복구가 멈춘다. 반대로 실제 수락 후 응답/완료 쓰기가 유실되어도 수락 여부를 자동 확정하지 못한다. 이는 현재 at-most-once 방향의 의도적 선택이며 exactly-once 보장은 아니다. 내부 문의용 SNS 상관키/조정 경로도 없다. 독립적으로 검토한 fence 구조에서 확인한 한계이며, 이를 중복 없는 완전 복구로 해석하면 안 된다.
- SES 성공 후 최초 완료 쓰기와 catch의 보완 쓰기가 모두 실패하면, 다음 프로세스가 볼 수 있는 것은 불확실 fence뿐이다. 첫 쓰기만 실패하는 기존 통합 테스트는 이 연속 DB 장애까지 증명하지 않는다. 이 경우 안내 등록 유실 가능성은 코드로 추론되지만 이번 검토에서 별도로 장애 주입 실행하지 않았다.
- 중복 억제는 같은 submissionId에 한정된다. 현재 클라이언트는 같은 내용의 화면 내 재시도에서 ID를 유지하지만, 새 ID/페이지 재로드까지 내용 기반으로 합치는 구조는 아니다.
- 이번 검증은 실제 SES 수락/반송, IAM 권한, configuration set 존재 여부, SNS 구독, 실제 환경변수, 서버 migration 적용 여부를 증명하지 않는다. 이 부분은 요청한 접근 금지 범위에 따라 실행하지 않았다. 전체 admin migration 역사 전체를 처음부터 적용하는 테스트도 실행하지 않았으며, 메일 통합 스키마와 새 migration의 up/down/reapply를 검증했다.
- 검토 중 추가된 후속 테스트는 전체 테스트 통과 수에 포함되지 않는다. 위 소스 해시 이후 수정은 이 보고서의 검증 범위가 아니며 별도 재실행이 필요하다.

## 수정 후 독립 재검증 — 2026-11-10 11:45 KST

**최종 결론: 최초 P2는 아래 수정 스냅샷에서 해소됐다. 수정 범위에서 새로운 actionable 결함은 발견하지 못했다.** 앞 절의 최초 발견·재현 증거·검증 수치는 당시 기록으로 보존한다. 현재 판정은 이 후속 절을 따른다. 위에서 구분한 exactly-once, 연속 DB 장애 및 외부 운영 환경 검증의 한계는 계속 유효하다.

### 다시 검토한 코드

- `/Users/jina/.codex/worktrees/mail-integration-api-261109/clipper_web_api/src/modules/mail-events/inquiry-receipt-coordinator.ts:55`: 만료 정리는 계속 `payload=NULL`을 실행하고, 늦은 결과를 식별할 opaque `lease_token`은 남긴다. 원문 삭제를 유효 lease 종료까지 미루는 변경은 없다.
- 같은 파일 90–96행: 같은 발송 시도의 확정 성공은 `forwarded_at`을 기록하고 `forward_expired`를 `receipt_expired`로 바꾼다. 이미 만료 정리된 건은 고객 안내를 신규 등록하지 않고 반환한다.
- 같은 파일 112–119행: 첫 완료 쓰기가 실패했을 때의 성공 보완 쓰기도 위 상태 전환과 `RECEIPT_RETRY_EXPIRED`를 반영한다. 미확정/확정 거절은 성공으로 승격하지 않는다.
- 관련 unit/실제 PostgreSQL 테스트와 실제 SQL의 조건·결과 처리를 다시 읽었다. 검증 전후 coordinator 및 두 테스트 파일의 해시가 같아, 이번 검증 중 수정은 관찰하지 않았다.

검증한 coordinator SHA-256:

```text
7e48339c65bb7db208b4d881ca465b3c90fb3856f0470f34a83280916b664b50
```

테스트 소스 SHA-256:

```text
mail-postgres.integration.spec.ts 7551ed32564c34dc52841d2f2aac725fe648cbd518f87b844028925f58760dc1
inquiry-receipt-coordinator.spec.ts ec7f6f47acec3360a15e9ce216447a8dfc6ab0492d8ba5dc1e7312aa6becceaf
```

### 독립 실행 결과

API 작업공간에서 새로 실행했다:

```sh
CLIPPER_MAIL_PG_TEST=true npm test -- --runInBand --silent inquiry-receipt-coordinator mail-postgres.integration > /private/tmp/clipper-ses-independent-recheck-tests.log 2>&1
npm run build > /private/tmp/clipper-ses-independent-recheck-build.log 2>&1
git diff --check
```

- **2 suites / 42 tests 통과, exit 0.** 추가된 늦은 성공/첫 완료 쓰기 실패 두 사례와 기존 회사 전달·안내 등록·중복 방지·만료·메일 통합 테스트를 포함한다.
- **빌드 exit 0**, diff 공백 검사 통과.
- 요청에 따라 이번에는 수정 범위 중심으로 실행했다. 전체 6,281개 테스트 및 Infra 135개 테스트를 이번 후속 검토에서 다시 실행했다고 주장하지 않는다. 최초 독립 전체 검증은 위에 보존되어 있다.

기존 독립 재현의 **실제 시간 조건(기한 400ms 뒤, 발송 보류, 500ms 후 별도 인스턴스에서 만료 정리, 이후 응답 해제)** 을 유지한 새 스크립트를 별도로 작성했다. 허용된 테스트 DB에 `ses_independent_recheck_261110` 스키마를 만들고 실제 새 빌드와 두 migration을 사용했으며, 메일은 전부 메모리 스텁이다.

```sh
node /private/tmp/clipper-ses-independent-recheck-probes.cjs > /private/tmp/clipper-ses-independent-recheck-probes.log 2>&1
```

**exit 0, 다음 6개 독립 시나리오의 assertion 통과:**

| 시나리오 | 관측 결과 |
|---|---|
| 만료 정리 후 늦은 성공 | 성공 응답 해제 전에 원문 NULL 확인. 이후 `receipt_expired`, `forwarded_at` 있음, `RECEIPT_RETRY_EXPIRED`, 발송 1회, 안내 등록 0회 |
| 위 순서 + 첫 완료 DB 쓰기 실패 | 장애 주입이 실제 실행됐음을 확인. catch 보완 쓰기 후 같은 올바른 상태, 원문 NULL, 발송 1회, 안내 등록 0회 |
| 만료 정리 후 늦은 uncertain 오류 | `forward_expired`, `forwarded_at=NULL`, 원문 NULL. 성공으로 오분류하지 않고 복구/동일 ID 재요청에서도 추가 발송 없음 |
| 만료 정리 후 늦은 확정 거절 | `forward_expired`, `forwarded_at=NULL`, 원문 NULL. 거절 코드 보존, 추가 발송 없음 |
| 정상 발송 중 같은 ID 8개 동시 재요청 + 이후 복구/재제출 | 발송 1회, 안내 등록 1회, `settled`, 원문/lease token NULL |
| 성공 쓰기 직후, 안내 등록의 소유권 잠금 직전에 만료 정리 | `receipt_expired`, `forwarded_at` 있음, 원문 NULL, 안내 등록 0회 |

늦은 성공 두 사례에서 추가 `recover()`와 동일 ID `accept()`를 실행해도 추가 발송·안내 등록은 발생하지 않았다. 최초 결함의 잘못된 회사 전달 실패 상태와 재제출 오류는 이 조건에서 재발하지 않는다. 만료된 건의 고객 안내 등록을 생략하는 것은 이번 수정에서 명시한 정책에 따른 정상 결과다.

검토자는 제품 소스를 수정하지 않았고, 이전 재현 스크립트/로그도 덮어쓰지 않았다. 새 임시 스키마는 finally에서 삭제했다. `localhost:55439` 클러스터는 중지하지 않았으며 모든 검증 프로세스는 종료했다. 실제 서버·AWS·운영/개발 DB·실제 메일 발송은 사용하지 않았다.
