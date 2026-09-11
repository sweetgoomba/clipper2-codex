# 2026-09-08 운영 PG 세션 종료 인수인계

기준: 2026-09-08 이번 대화 종료 시점. **현재 상태는 이 문서와 TASKS.md를 우선한다.**
과거 세션 인수인계·WORKLOG의 “미배포/다음은 최초 추가충전 테스트”는 당시 상태다.
서버 상태는 사용자가 직접 실행해 제공한 출력 기준이며, 문서 작성 중 서버/DB를 다시 조회하거나 변경하지 않았다.

## 1. 현재 위치

**운영 웹·API·DB·HTTPS·로그인 구축을 마쳤고, 운영 환경에서 Toss TEST키로 주요 결제 흐름을 검증 중이다.**
최초 구독, 추가충전 기본 구매, 자동갱신 취소/재개, 카드변경, Pro 월간→연간 즉시변경, 연간 구독 환불 1건까지 확인했다.
전체 PG E2E, 운영 desktop/runner 배포, 지속운영 점검, 라이브 전환은 아직 완료하지 않았다.
운영 도메인 공개/HTTP200은 라이브 결제 운영 완료나 모든 기능 검증을 뜻하지 않는다.

- 작업 정본: `/Users/jina/project/adlight/web/*`, `desktop/*` 원본 저장소.
- `.integration-clones`와 기존 worktree는 초기 통합 보존본. 새 수정/덮어쓰기/삭제 대상 아님.
- 서버 명령은 **사용자가 직접 실행**. 실행 장비·경로·영향을 설명하고 한 단계씩 안내한다.
- 운영 DB 재생성은 이미 끝났으므로 다시 초기화하지 않는다.
- 개발 서버·개발 DB 작업은 보류. 라이브키/실결제 및 desktop 앱 식별자 변경은 별도 승인 전 금지.
- 이번 문서화는 추가 배포·결제·환불·상태 변경 승인이 아니다.

## 2. 마지막 배포 상태

| 대상 | 현재 확인된 운영 revision | 증거 |
| --- | --- | --- |
| Customer | `888c2b96d818857306e9376c3436563c394971b1` | 사용자 docker inspect running/revision 일치, 공개 /my/payment-history HTTP200 |
| Admin | `fb3e532b3e9b195c5c149a207fbcbf5673932245` | 사용자 docker inspect running/revision 일치, 공개 /payment-operations HTTP200 |
| API | `27103011e2e0672199721c6c3974c5bfc4e0d741` | 이번 대화 앞부분 사용자 running/revision 일치, /health status ok 및 user/release/admin DB ok; 후속 API 변경 없음 |
| Infra | `088e520260eb8f806f662c76e0732100aabfbcb5` | 로컬 원본 HEAD. 운영 최신화 로그는 있으나 종료 시 별도 원격 HEAD 조회는 안 함 |

Customer/Admin 최신 수정은 모두 커밋·푸시·사용자 배포됐다. **현재 미배포 앱 코드 수정 없음.**
최신 Customer888c2b9의 문구/배지 및 Adminfb3e532의 환불 완료 표시를 배포 후 최종 확인했다는 명시적 답변은 아직 없다.
UI 결함을 발견하고 추가 수정한 사실과 최종 수정본의 직접 확인을 구분한다. 다음 세션 첫 단계는 실제 화면 확인이다.

배포 방식: m4-prod의 현재 checkout/upstream을 fast-forward 후 로컬 Docker build. GHCR pull/강제 main·dev checkout 방식이 아니다.
`deploy-prod.sh web|admin|api|all`은 선택한 앱만 빌드/교체하며 DB migration은 별도다.
이번 후반 UI 배포에는 API/DB/migration 변경이 없었다.
이번 세션 초 Admin migration `LocalizeCreditProductNames1788900000000`는 적용 완료. 다시 실행할 작업으로 나열하지 않는다.

## 3. 이번 세션 구현 및 배포

| 영역 | 최종 반영 내용 |
| --- | --- |
| 상품/추가충전 | 추가 크레딧 400 / 1,000 / 4,000으로 상품명 한글화. 가격 5,900 / 10,900 / 29,900원, 30일 유지. 기존 주문·원장 snapshot의 영어 이름을 소급 수정하지 않음 |
| 크레딧 | 보유/사용가능 중복 대신 사용가능 잔액 중심. 지급표 출처/지급/잔여/상태/사용 기한, 날짜+시각 표기, 열 간격 개선. 지급표·원장·상단 출처 잔액 모두 동일 출처 색상 |
| 결제 예정 | 고객/Admin 날짜+시각. 예정 시각 이후 worker가 처리하므로 정확히 그 순간 카드 승인을 보장한다는 안내 아님 |
| 최종 동의 | 최초 월/연 구독, 즉시/예약 변경, 갱신재개, 카드변경의 금액·주기·자동갱신 조건과 필수 동의 보완. 최초구독 기존 주문 재진입은 API의 저장된 subscriptionTerms 사용. 미동의 버튼 차단 |
| 문구 정리 | 카드 등록 안내·자동갱신 취소 경로를 체크박스 위 목록으로 분리. 정상 카드변경은 새 카드 사용 동의, 연체 즉시청구 경로는 별도. 중복 소제목/과한 모달 KST·순차처리 문구 제거. 추가충전은 1회결제임을 명시 |
| 요금제 변경 | 마이페이지 오른쪽 요금제 변경 패널→비교 표 모달→서버 견적/동의. 연간→월간 직접변경 노출·요청 차단. NOT_ALLOWED409를 견적만료로 오인하던 안내 수정. 차액은 새가격−공제액, 두 기준과 선택 이유 상세 설명 |
| 마이페이지 | 월/연 구독 배지, 읽기 쉬운 자동갱신 배지, 중립 다크 모달/이용권 배경, 76% 어두운 backdrop. 결제내역 바로가기 유지 |
| Admin 결제 운영 | 주문번호 ellipsis + Material 복사 아이콘(hover/focus/touch), 전체 값 복사 및 2.5초 Snackbar. 이메일·이름 1줄. 별도 한글 결제 유형. 상품 코드 제거, 경고/작업 줄바꿈 방지. **주문 행 상세 펼침은 사용자 요청으로 제거** |
| 환불 표시 | 고객 이전 구독 상품·환불 종료 시각, 종료/환불 중 관리 패널 숨김. 고객/Admin 전액·부분 환불 상태 우선 및 강조. Admin 구독 환불 완료는 대응 환불 건 돈/내부 상태 확인. 토스 상태 열을 저장된 응답으로 명확화 |
| 결제내역 디자인 | nav 요금제→결제내역→크레딧. 제목24px, 카드 반복 대신 단일 표. 일시/상품·주문번호/금액/결제·환불 상태/영수증. 전체 주문번호 줄바꿈, 모바일 표 스크롤, 실패/입금 안내 유지. 상단 KST 안내 제거, 원결제→결제금액 |

주요 커밋 흐름:
- Customer: `6e951cd` → `e8462ca` → `9049d1d` → `76fd82a` → `90bbb86` → `fa0d25c` → `cbb263c` → `0626940` → `1be5157` → `888c2b9`.
- Admin: `31ad799` → `47e6904` → `fb3e532`.
- API: `8195a35` → `2710301`.
- 여러 UI 시안 중 폐기한 좌우 대칭 구독 카드, 주문 상세 펼침 등을 다시 구현하지 않는다.
- 자동 승인 검토가 여러 번 GitHub push를 차단했고, 사용자가 해당 커밋·repo·branch 푸시를 명시 승인해 해소했다. 현재 push 차단/미푸시 커밋 없음. 재차 차단되면 실제 사유를 설명하고 우회하지 않는다.

## 4. 실제 테스트 — 완료와 한계

### 확인한 시나리오

| 시나리오 | 확인한 결과 | 아직 증명하지 않은 부분 |
| --- | --- | --- |
| 최초 Pro 월간 | 10,900원 TEST 결제, 월1,000 지급, Trial400 포함1,400, 활성/다음결제2026-10-08 06:06 | 라이브 실제 승인·알림, 다음 회차 자동청구 |
| 추가충전400 | 5,900원 결제, 400지급, 총1,800. 운영 DB paid/succeeded/지급1건/원장1건 및 정확히30일 확인. Toss GET paymentKey HTTP200/DONE/금액일치. Admin 상태재확인2회 후 잔액유지 | 웹훅·콜백 재전달, 실제 지급함수 재실행, 동시 요청 멱등성 |
| 다음 자동결제 취소→재개 | 기간/현재권한/1,800 유지, 다음청구 중단→동일시각 복구, 추가 결제완료 건 없음 | 별도 Admin/DB 대조, 경계시각·실패 경로 |
| 카드변경 | 완료화면/새카드 표시, 기간·다음청구·잔액 유지, 새 결제 없음 | 이전키 정리, 다음 실제 청구의 새키 사용, 취소·실패·연체 시나리오 |
| Pro 월간→연간 | 차액72,017 성공, 새연간기간/다음결제2027-09-08 13:50, 기존 구독1000회수·새1000지급, 총1800 유지 | 변경 성공 당시 DB/Toss 전 항목 대조 및 중복지급 검증 |
| Business 연간 견적 | 234,000−82,792=151,208, 기간/크레딧 공제 설명 및 필수 동의 화면 확인 | 성공 결제 미확인. 생성된 upgrade 주문만으로 Business 전환 성공 처리 금지 |
| Basic 연간 하향 예약 | 58,800원·다음 갱신부터 적용·필수 동의 모달 확인 | 예약 확정, 취소, 실제 갱신 적용 미확인 |
| 연간→Business 월간 금지 | API409 NOT_ALLOWED 실제 관찰, UI 노출/요청 제한 및 에러 문구 수정 | 최종 배포본 금지조합 전체 수동 확인 |
| 연간 구독 환불 | 아래 특정72,017원 건 Toss 취소·환불 돈/내부 완료·구독 종료·크레딧 회수 확인 | 다른 종류/사용량조건/부분실패/재시도/중복 환불 전체 검증 아님 |
| 빌링키 삭제 웹훅 | Toss BILLING_DELETED 성공 전송 기록 및 DELETE200 사용자 확인 | BILLING_DELETED는 결제취소 이벤트가 아님. 앱 이벤트 저장·다른 이벤트·중복·재시도 검증 별도 |

### 추적할 주문·환불 건

- 회원: `metabuzz2023@gmail.com`, `f47e0e29-217d-40e7-bc66-b22bf4c58c72`.
- 최초 구독: `sub_de417bf7b408406b8d358e7f893016c0`.
- 정확한 DB/Toss 대조가 끝난 추가충전: `topup_2b66981ddc5c41a7b05ddc1245d862e2`.
  - 내부 지급/paid 시각: 2026-09-08 10:23:08.126+09 → 만료2026-10-08 10:23:08.126+09.
  - Toss 승인: 2026-09-08 10:23:07+09. 내부시각과 같다고 쓰지 않는다.
  - 공용 Widget TEST키로 orderId 조회는404 NOT_FOUND_MERCHANT, 저장된 paymentKey 조회는200. 키 자체를 출력/문서화하지 않는다.
- 성공 후 환불한 상향 주문: `upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375`, 72,017원.
- 환불 case: `61d6c4bc-b2b3-4328-835f-b27f3eb98807` (annual_subscription).
  - 이용 종료/생성2026-09-08 16:34:11 KST, 내부 완료16:34:21, 취소금액72,017/잔액0.
  - 돈 완료, 내부 처리 완료, refund_internal_effects 완료를 사용자 제공 Admin 상세로 확인.
  - BILLING_DELETED/DELETE200 16:35:00 KST. 빌링키 문자열은 저장하지 않는다.
- Business 연간의 생성 주문 예: `upgrade_551fd92dcc8f3d87eaf964cabb136b780354e1ce2ce35d5d70342913` (151,208원). 성공 여부 미확인.

### 환불 후 회원 잔액과 현재 정책

| 출처 | 지급 | 잔여 | 상태 | 기한(KST, 화면 분 단위) |
| --- | ---: | ---: | --- | --- |
| 추가충전 | 4,000 | 4,000 | 사용 가능 | 2026-10-08 15:53 |
| 추가충전 | 400 | 400 | 사용 가능 | 2026-10-08 15:52 |
| 정기구독(연간 첫월) | 1,000 | 0 | 회수 | 2026-10-08 13:50 |
| 추가충전 | 400 | 400 | 사용 가능 | 2026-10-08 10:23 |
| 정기구독(월간) | 1,000 | 0 | 회수(즉시변경 당시) | 2026-10-08 06:06 |
| 무료체험 | 400 | 400 | 사용 가능 | 2026-10-08 06:03 |

5,200 = topup4,800 + trial400. 추가4,000/400 구매는 지급표의 존재를 확인했으며 각 주문 DB/Toss 대조를 끝낸 것은 아니다.
구독 환불은 해당 subscription 출처를 회수하고, 별도 topup 결제나 Trial을 자동 환불/회수하지 않는다.
topup은 `subscriptionId/accessGrantId=null`로 해당 구매 주문에 연결, 결제시각 기준 상품 snapshot의 정확한30일 기한을 갖는다.
추가충전의 별도 환불은 해당 구매 지급 건이 대상이다. 구독 종료만으로 topup 기한을 줄이지 않는다.
현재 Web API OperationsService의 quote/start와 CreditGrantsService 차감은 유효 잔액을 확인하고 활성 구독을 필수조건으로 삼지 않는다.
따라서 구독/무료체험 이용권이 끝나도 유효한 topup 잔액은 서버 차감 기준 사용 가능하다. 별도 desktop 운영앱 실작업 E2E는 미완료.
구매 자격(추가충전 신규 구매에 유료 구독 필요)과 이미 보유한 크레딧 사용 자격을 구분한다.
EffectiveAccess의 spendableCreditSources만 읽고 실제 차감 정책을 판단하지 않는다.

근거 코드:
- [환불 대상 지급 건](../../web/clipper_web_api/src/modules/payments/application/payment-refund-eligibility.service.ts)
- [topup 지급/기한](../../web/clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts)
- [작업 견적·실행](../../web/clipper_web_api/src/modules/operations/application/operations.service.ts)
- [크레딧 합계·차감](../../web/clipper_web_api/src/modules/credits/application/credit-grants.service.ts)

주의: 주문 paid는 원승인 기록이고 refundStatus/누적환불/잔액은 별도다. paid를 일괄 canceled로 덮어쓰는 데이터 보정 금지.
refundProcessingCaseId는 완료 후에도 남는 구조. 이름만 보고 DB 불일치/처리중으로 단정하지 않는다.
Admin은 현재 공개 DTO에 caseId 직접연결이 없어 종류/종료모드/동일 종료시각으로 대응 환불을 찾고, 단일 대응 건의 money/internal 모두 completed일 때 완료로 표시한다. 대응 건이 없거나 모호하면 확인 필요로 표시한다.
환불 목록은 제한이 있어 오래된 건 매칭은 향후 API의 명시적 환불상태 projection으로 개선 검토 가능.
Customer의 기존 refundCompleted는 canceled/ended + refundProcessing 추론이다. 환불 처리 중 자연 기간종료(ended)가 겹치는 경계는 별도 검증 대상으로 남긴다. 이번 확인 건은 canceled+immediate+돈/내부완료다.

## 5. 남은 테스트와 권장 순서

1. 최신 운영 화면 확인: Customer /my/payment-history의 결제금액·KST안내 제거·표·메뉴, /my/credits의 지급/원장/요약 출처색 일치; 환불 회원 /my의 종료 표시 및 Admin 완료 표시.
2. 완료한 환불 1건을 운영 읽기 전용 조회로 교차 확인: case/item/internal event, 주문 누적환불·잔액, 구독/이용권 종료, 지급 건·원장. 이미 취소된 결제를 다시 환불하지 않는다.
3. 별도 추가충전 환불 또는 월간 환불 테스트 준비. 해당 회원은 이제 유료 구독이 없으므로 예전 active Pro연간을 전제로 카드/요금제 변경 안내 금지. 테스트 계정/주문과 예상 영향 확인 후 사용자가 실행.
4. 예약 변경 확정/취소/실제 적용, 금지조합, 즉시변경 실패·중복·기존권한 유지.
5. 카드변경 취소/실패/연체, 이전키 정리와 다음청구 새키 사용. 갱신·실패재시도·유예/기간 만료·worker 재기동 복구.
6. 웹훅 PAYMENT_STATUS_CHANGED/DEPOSIT_CALLBACK/BILLING_DELETED 저장·중복·재시도 및 콜백 재전달, 지급함수 재시도 멱등성. 가상계좌는 실제 제공할 경우만 입금대기/입금/만료 검증.

정상결제1건·상태재조회 반복을 전체 멱등성 검증으로 기록하지 않는다. 운영 DB 날짜변경/강제 worker실행/실결제는 이 권장순서 자체로 승인되지 않는다.
전략팀 제7조 요청: 최종동의 금액·주기·자동갱신 안내는 구현·배포됨. 최종 화면 증거/안내 전달 여부는 별도 확인. 약관·FAQ 계산정책 설명과 법무 확인을 완료했다고 기록하지 않는다.

## 6. 운영 PG 전체 흐름과 남은 구축

| 단계 | 현재 상태 | 잔여 |
| --- | --- | --- |
| 원본 저장소 PG 통합 후보 | 준비됨 | 최종 통합 대상 브랜치/PR, desktop 원격 상태 확인 |
| 운영 웹/API/DB, DNS·NPM HTTPS, Google/Admin 로그인 | 기본 구축·동작 확인 | OAuth 게시/지원메일/소유자, 운영 보안 점검 |
| TEST PG 주요 정상 흐름 | 여러 건 확인, 이번 문서4절 | 예외·예약·갱신·환불 매트릭스·중복/복구 검증 |
| 고객/Admin UI와 운영 조회 | 최신 수정 배포 | 마지막 화면 확인, 과거/경계 환불 표시 검증 |
| 운영 desktop 앱 | 환경·식별자 결정/구현 남음 | 이름/아이콘 승인, appId/protocol/userData/keychain/캐시·모델/포트/API/JWT/업데이트 분리 |
| 운영 runner·배포 파일 | 미구축/전체 경로 미검증 | 컨테이너/포트/env/작업·output/S3 prefix/Release 분리, Admin→빌드→S3→다운로드→Win/Mac 설치·업데이트 |
| 개발 환경 PG 전환 | 보류 | 추후 복제DB 보존·삭제 정책 검증→별도 승인. 사용자/로그인 보존, 무단 dev migration 금지 |
| 지속운영 | 미완료/팀 결정 대기 | 운영 모니터·알림, 백업주기/복원, 재부팅·정전 복구, DB 접근/로그/비밀 권한 관리 |
| 라이브/정식 공개 | 미전환 | Toss 계약·심사·키/MID, 테스트데이터 정책, 명시 승인된 실결제/취소, 담당자·롤백 |
| 문서·팀 공유 | 로컬 작성됨 | Infra5개 및 .codex 변경 검토·선택커밋/공유. 기존 ahead 커밋 일괄 push 금지 |

운영 desktop은 기존 개발판과 공존하는 방향. `ai.clipperstudio.app`, `clipperstudio://` 등 과거 후보는 확정값이 아니다.
개발 DB 데이터 전환 세부 정책과 토폴로지/명령은 [이전 인수인계](./2026-09-08-production-pg-session-handoff.md)의 해당 절을 참고하되, 진행률은 이 문서를 우선한다.

## 7. 검증 기록과 한계

- 앞부분 전체 검증: Customer243/Admin372/API2424 PASS(API10 skipped); 결제동의 변경 시 Customer250/API2427 PASS(API16 skipped); 요금제 모달 변경 시 Customer259 PASS.
- 후반: Admin 복사/표 대상24, 환불 표시 Customer57/Admin20, 결제내역 표+header+credits26, 최종 배지11 tests PASS. 수정 단계별 기록이며 **최종 전체 suite를 모두 다시 실행했다는 뜻 아님**.
- Customer/Admin 각 변경의 prod build 및 git diff --check 확인. Admin 초기 번들565.89kB로500kB 경고 존재, 빌드는 통과.
- 가짜 API를 사용하는 로컬 Chrome에서 모바일/데스크톱 레이아웃, 복사/알림 자동닫힘, 모달/표/환불 화면을 확인. 운영 결제 실행 증거와 구분한다.
- 테스트 실행: Node22 + Angular CLI `test --watch=false --browsers=ChromeHeadless --include=...`, 빌드는 `build --configuration=prod`. `production` 설정명 사용 금지.
- 임시 미리보기는 `/private/tmp/clipper-history-table-preview`, `/private/tmp/clipper-refund-preview` 등이며 영구 인수인계 근거가 아님. 문서의 동작/검증 기록과 Git 소스를 우선한다.
- 전체 테스트 단순 반복, 개발 서버 실행, 서버 직접접속은 이번 종료 문서화에서 하지 않았다.

## 8. 로컬 Git 종료 스냅샷

2026-09-08 문서 작성 직전 로컬 조회. 원격 전체 fetch를 새로 수행한 결과는 아니다.

| repo | branch | HEAD | 상태 |
| --- | --- | --- | --- |
| web/clipper_web_client | integration/toss-payments-pg-20260903 | 888c2b9 | clean, 추적 upstream 차이 없음 |
| web/clipper_web_admin | 동일 | fb3e532 | clean, 추적 upstream 차이 없음 |
| web/clipper_web_api | 동일 | 2710301 | clean, 추적 upstream 차이 없음 |
| web/clipper_infra | 동일 | 088e520 | 아래5개 문서 미커밋 |
| desktop/clipper_angular | 동일 | 7f34704b | clean, branch upstream 표시 없음 |
| desktop/clipper_nestjs | 동일 | 19c667e | clean, branch upstream 표시 없음 |
| desktop/clipper_electron | 동일 | dbf55c8 | clean, branch upstream 표시 없음 |
| desktop/clipper_python | merge/meme-overlay-into-dev | f8274ac | clean, 추적 upstream 차이 없음 |
| .codex | main | 40beeda | 기존25 ahead + 아래 문서 수정/신규; 이번에 commit/push 안 함 |

Infra 보존 문서: 수정 `runbooks/deploy-prod.md`, `runbooks/recreate-prod-databases.md`; 신규 `production-console-settings.md`, `production-deployment-team-guide.md`, `production-setup-history-20260908.md` (모두 runbooks 아래).
.codex 기존 수정: TASKS/WORKLOG, main/2026-09-03-toss-payments-pg-release-candidate-integration-log.md, main/2026-09-03-toss-payments-pg-session-handoff-and-integration-readiness.md.
기존 신규: 2026-09-08-payment-disclosure-plan.md, 이전 handoff, NEXT_SESSION_PROMPT.md, 별개 main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md.
이번 작성: 본 closeout 신규 + TASKS/NEXT_SESSION_PROMPT 최신화 + WORKLOG 최신요약 + 이전handoff 우선순위 안내.
다른 PC/새 worktree에는 미커밋 문서가 없을 수 있다. 같은 작업 경로에서 시작하거나 승인된 방식으로 전달한다.

## 9. 상세 매뉴얼

- [작업 체크리스트](./TASKS.md), [다음 세션 시작 문구](./NEXT_SESSION_PROMPT.md), [시간순 기록](./WORKLOG.md)
- [팀원 운영 배포 매뉴얼](../../web/clipper_infra/runbooks/production-deployment-team-guide.md)
- [운영 콘솔 설정](../../web/clipper_infra/runbooks/production-console-settings.md)
- [운영 구축 이력](../../web/clipper_infra/runbooks/production-setup-history-20260908.md)
- [배포 진입점](../../web/clipper_infra/runbooks/deploy-prod.md)
- [desktop 식별자 결정 대기](../main/2026-09-07-desktop-dev-prod-app-identity-decision-pending.md)
- [runner·콜백/웹훅 환경 분리 설계](../main/2026-09-07-toss-payments-pg-server-callback-webhook-design.md)
