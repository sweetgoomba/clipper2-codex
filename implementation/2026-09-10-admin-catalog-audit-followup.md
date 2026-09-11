# 미사용 상품 정리·이용권 이력 표시 추가 요청

최신 후속: [관리자 크레딧 지급 사유 누락 수정](./2026-09-10-admin-credit-grant-reason-followup.md). 지급100/총5900 사용자 확인 이후 사유 공란이 발견됐으며 API3299a73 수정·검증·커밋·푸시·운영 배포/health 확인 완료, 기존 지급분 사유·원장·고객 화면 확인 대기.

2026-09-10. [앞선 배포·운영 확인](./2026-09-10-admin-display-followup.md) 이후 요청이다. **삭제 migration 운영 적용과 APIa0a78db/Admin597c5b6 커밋·푸시·배포 및 상품 목록·이력 실제 화면 확인까지 완료**했다. 마지막 확인된 운영 앱 버전은 APIa0a78db/Admin597c5b6/Customerb5dc797. 수동 지급·결제 충돌·사용분 환불 차단 운영 E2E는 별도 미완료다.

## 구현

- API 관리자 migration `RemoveObsoleteCreditProducts1789100000000`을 datasource에 등록했다. 비활성 기본 상품 `credits_100`(100 Credits/100/5900), `credits_500`(500 Credits/500/27900)만 삭제한다. 대상 행을 잠그고 활성 여부·이름·수량·가격 변경이나 연결 주문이 있으면 전체 삭제를 중단한다. 기간은 기존 초기값과 현재30일 모두 허용한다. 다른 상품과 주문은 수정하지 않는다. 재실행은 no-op이며 삭제된 원래 ID를 재구성할 수 없어 down은 명시적으로 중단한다. 적용 전 백업 필요.
- API 이용권 이력 읽기에서 같은 admin DB의 operators를 LEFT JOIN하여 현재 계정 이메일을 optional nullable `operatorEmail`로 추가했다. 원본 operatorId/eventType/reason 및 이력 쓰기는 보존했다. OpenAPI·Admin 모델·mock을 함께 수정했다.
- Admin 회원 상세의 13개 알려진 이용권 변경 유형을 한국어로 표시한다. `subscription initial payment fulfilled`는 구독 시작 이벤트에서만 `구독 최초 결제 완료`로 표시한다. 사용자 지정 사유·미지 유형은 원문 유지.
- 운영자 ID가 없으면 시스템, 있으면 계정 이메일, 과거 계정을 찾지 못하면 운영자 정보 없음. UUID는 API 원본과 셀 title에 보존한다. 이메일은 현재 계정값이며 당시 이메일 스냅샷을 새로 만든 것은 아니다.

## 기존 정책 확인 및 사용자 질문

- SubscriptionPaymentsService.createCheckout은 현재 또는 예정 상태의 구독/관리자 이용권이 있으면 ACTIVE_ACCESS_CONFLICT/409로 신규 주문 생성 전 차단한다. 예정 이용권도 포함한다. 무료체험은 별도이므로 이 차단 대상이 아니다. 기존 구독의 요금제 변경은 별도 경로다.
- 환불은 아무 사용내역이나 있는지를 보는 것이 아니라 대상 결제의 지급분을 본다. 월간·연간은 대상 grant별 operation_charge/operation_refund 순사용량, 추가충전은 해당 지급분의 원래·잔여 수량/상태를 검사한다. 무료체험만 사용했다고 다른 미사용 결제가 자동 차단되는 것은 아니다.
- 기존 자동 테스트에 월간/연간/추가충전 사용 시 CREDITS_USED, 무료체험 사용과의 구분, 접수 시 잠금 안에서 사용량 재검사 후 case 미생성이 있다. 이 경로들을 다시 실행하여 통과했다.
- 현재 TASKS에는 관리자 이용권·크레딧 수동 지급 운영 테스트가 독립적으로 없었다. 신규 결제 충돌·사용분 환불 차단과 함께 미완료 항목으로 추가했다. 실제 운영 실행을 완료했다고 기록하지 않는다.

## 검증

- 삭제 migration: 테스트용 로컬 PostgreSQL에서 정상 삭제/재실행, 활성/맞춤/주문 참조 시 전체 중단, rollback 중단 5개 통과. 실패하는 구현을 먼저 확인하고 수정했다.
- 이력: API 이메일/누락 계정/시스템 매핑과 원본 보존, Admin 실제 렌더 한글/이메일/시스템/누락 계정/미지 유형 회귀 테스트를 실패 확인 후 수정하여 통과했다.
- API 전체 2494 통과/21 skip. 이 중 새 migration opt-in 5개는 별도 로컬 PG 실행에서 통과했고 기존 선택 테스트16개는 이번 전체 실행에서도 skip이다.
- Admin 전체 ChromeHeadless400 통과. API build 및 Admin prod build 성공. 기존 초기번들500kB 경고 지속(567.26kB).
- 운영 PG/DB/앱은 이번 검사에서 변경하지 않았다. 실제 사용 후 환불 차단과 수동 지급 E2E는 아직 미실행이다.

## 작업 위치와 다음 단계

### 운영 사전 조회 확인 — 사용자 m2-db 출력

- clipper_admin_prod / transaction_read_only=on, 마지막 ROLLBACK 확인.
- credits_100: d9ed317b-475b-4389-a89c-e1854f1ff418, 100 Credits/100/5900/30일/비활성/연결 주문0.
- credits_500: 30951f30-71f5-41e0-954e-0b078323054e, 500 Credits/500/27900/30일/비활성/연결 주문0.
- migration58개가 등록되어 있으며 LocalizeCreditProductNames1788900000000 및 AddNaverUsageApis1789000000000까지 적용됨. 이번 삭제 migration은 미적용. 코드 기존 목록과 일치하여 새 등록분은 삭제 migration1개다.
- 삭제 조건 충족. 이후 사용자 m2-db 출력에서 BACKUP_OK 확인: `/Users/metabuzz/clipper-backups/before-credit-cleanup.7VyDnk/clipper_admin_prod.dump`, SHA256 `91834fe7c29a0802d9d0bb797e33e7d8b006cedbcc441cce6771f4a1a3eb3a11`. pg_dump custom-format 생성 및 pg_restore --file=/dev/null 읽기 성공이며 실제 복원 실행은 아니다.
- [단일 적용 SQL](./2026-09-10-remove-obsolete-credit-products.sql) 준비: 원본 migration up SQL과 내용 일치 확인. 같은 트랜잭션에서 삭제와 TypeORM migrations 기록을 저장하고, DB명/중복 적용 확인 및 lock timeout을 둔다. 별도 로컬 PG 임시 테이블에서 정상 삭제·기존 주문 보존·연결 주문/상품 변경/적용기록 INSERT 실패/중복 실행 시 롤백5경로 통과.
- 사용자 m2-db 실행 결과 COMMIT·삭제 대상0·RemoveObsoleteCreditProducts1789100000000 적용기록1행 확인. 나머지는 credits_400/1000/4000 세 상품이며 각각400/1000/4000, 5900/10900/29900원, 모두30일/활성이다. 운영 삭제 migration 적용 완료. DB 적용 재실행 불필요.

### 커밋 및 GitHub 푸시 완료

- API migration: 57ff67a51344c441df39002109e7b3e1fe2f9457.
- API 운영자 이메일: a0a78dbca9e2be26bb5bbffb90e2c77590f0a032.
- Admin 이력 한글·운영자 이메일: 597c5b61bbe5e6ef4fe0a1fc21542a73d0e7b5cb.
- 커밋 직전 GitHub release/pg-expiry-20260910 읽기전용 조회는 API9b1b395/Adminfa7e67a로 기준과 일치했다. 검증 이후 코드 변경 없이 커밋했으며 API node_modules 심볼릭링크는 추가하지 않았다. 공유 원본 API8수정+compose 미추적/Admin7수정 유지.
- 최초 API 푸시는 자동 승인 검토가 대상 저장소의 사용자 승인 확인 불가 사유로 실행 전 거절했다. 사용자에게 두 GitHub URL과 release 브랜치를 명시하여 승인을 요청했고, 이후 사용자 ‘승인’ 응답을 받아 정상 재실행했다. 우회 없음.
- 명시적 GitHub URL로 API9b1b395→a0a78db, Adminfa7e67a→597c5b6 일반 fast-forward 푸시 성공. 두 저장소 release/pg-expiry-20260910의 ls-remote가 위 전체 커밋값과 일치함을 확인했다. 공유 원본 로컬 repo에 푸시하거나 포인터를 변경하지 않았다.
- 사용자 m4-prod 이미지 조회 결과 API `a0a78dbca9e2be26bb5bbffb90e2c77590f0a032`, Admin `597c5b61bbe5e6ef4fe0a1fc21542a73d0e7b5cb` 일치 확인. 두 이미지 빌드 완료.
- 이후 사용자 API start-only 출력: clipper-web-api-prod running/restarts0/revision a0a78dbca9e2be26bb5bbffb90e2c77590f0a032, health HTTP200/status ok/user·release·admin DB 모두ok 확인. DB migration 재실행 없음.
- 이후 사용자 Admin start-only 출력: clipper-web-admin-prod running/restarts0/revision 597c5b61bbe5e6ef4fe0a1fc21542a73d0e7b5cb, 공개 HTTPS HTTP200 확인. Admin 배포 완료.
- 사용자 /plans 확인 응답으로 구형100/500 제거 및 추가상품400/1000/4000 세 상품 표시 확인 완료.
- 사용자 회원 상세 이력 붙여넣기에서 구독 시작/구독 갱신/이전 구독 이용권 종료/환불에 따른 구독 종료, 구독 최초 결제 완료, 직접 처리 운영자 이메일 및 자동 처리 시스템 표시 확인. 원본 UUID/영어 코드 대신 의도한 표시가 적용됨.
- 같은 이력에 2026-09-10 15:23 신규 구독 시작 행이 관찰됨. 현재 구독 활성 여부·상품·유효 권한·잔액은 이 이력만으로 확정하지 않는다. 이전 Trial/잔액4800 상태를 새 테스트 기준으로 재사용하지 않으며, 수동 지급 전 현재 회원 패널의 기준값 확인 대기. 새 결제 성공의 DB/PG 대조 완료를 뜻하지 않는다.

별도 checkout:

- API: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn/clipper_web_api`
- Admin: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn/clipper_web_admin`

공유 원본 미커밋 변경을 보존한다. 임시 clone의 origin은 원본 로컬 repo이므로 GitHub push에 사용하지 말고 명시적 GitHub URL과 release/pg-expiry-20260910 대상으로 확인한다.

운영 조회·백업·삭제 migration, 커밋·GitHub 푸시, API/Admin 배포 및 상품·이력 화면 확인은 완료했다. 다음은 현재 회원의 정기구독/유효권한·지급출처/잔액을 확인한 뒤 TEST 계정으로 관리자 지급·보유 중 결제 차단·사용분 환불 차단을 하나씩 확인하는 단계다. 현재/예정 구독이 있으면 관리자 이용권 중복 지급은 차단되므로 별도 이용권 없는 TEST 회원에서 지급 경로를 검증한다. 기존 구독을 테스트 편의로 취소·회수하지 않는다. 삭제 migration·완료된 표시 검증은 반복하지 않는다.

Build5 QA 대기, 플러그인 검증 보류, Mac 준비중, 개발DB·live 결제·정식공개 보류 유지. 실제 차감 테스트를 위해 보류된 플러그인 검증을 임의로 재개하거나 수동 회수를 정상 사용으로 간주하지 않는다.

## 수동 지급 테스트 기준값 — 사용자 화면 확인

- 기존 회원은 Pro 연간/활성. 이용기간 2026-09-10 15:23~2027-09-10 15:23 KST, 현재 구독 월 종료·다음 지급 2026-10-10 15:23, 다음 결제 2027-09-10 15:23. 해지 예약/예약 변경/환불 없음.
- 현재 유효 권한 Pro·정기결제, 지급 출처 정기결제/활성/사유 결제 구독.
- 사용 가능5800=무료400+구독1000+추가4400. 새 구독 지급1000/잔여1000. 과거 회수/만료 지급분은 표에 남아 있지만 가용 잔액에서 제외되어 있다. 이것은 사용자 화면 기준값이며 새 연간 주문의 DB/PG 대조 완료를 뜻하지 않는다.
- 현재 구독이 있으므로 같은 회원의 관리자 이용권 지급 경로는 사용하지 않는다. 별도 이용권 없는 TEST 회원에서 검증 예정.
- 다음 사용자 단계는 현재 TEST 회원의 크레딧 수동 지급100: 유효일시2026-09-11 23:59 KST, 사유 `운영 검증 - 관리자 크레딧 수동 지급 100`. 사유 미입력 시 확인 비활성화, 입력 후1회 지급, 예상 총5900/관리자 조정100/지급100·잔여100 및 원장+100 확인. 기존 구독·다른 출처는 유지 예상. 실제 지급 실행/결과는 아직 미확인. 이후 고객 표시 및 해당 지급분 회수 검증을 별도로 진행한다.
