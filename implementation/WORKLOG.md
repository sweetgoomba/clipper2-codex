# Clipper PG Worklog

## 2026-09-18 — PG 통합 종료 감사와 source 정리

- 8repo 원격을 fresh fetch해 모든 정식 PG integration ref가 현재 `origin/dev`에 포함됨을 확인했다. 개발 DB/서비스 Gate A–G, 독립 개발판, Windows 0.0.35 Build54 게시와 공개 다운로드/update feed까지를 완료 범위로 확정했다.
- 실제 카드 결제/webhook/환불, 유료 operation 차감·환급, 30–60분 로그 관찰, Windows 설치 후 실기, macOS 서명·공증 배포를 잔여 범위로 분리했다. Release 생성 폼 입력값 유지와 0.0.34 폐기 상태도 미완료로 기록했다.
- 최신 정본: [정식 PG 통합 종료 감사와 남은 작업](./2026-09-18-pg-integration-closeout-and-remaining-work.md). WORKBOARD·통합 카드·앱 카드·Release Coordinator 설계 상단에서 이 문서로 연결했다.
- Angular 진행 차단 UI는 원본 checkout을 `feature/billable-operation-blocking-progress-20260918`로 전환해 `6ec58054d894e4f6171dc47329e8ef06bf2520ab`로 커밋했다. Angular 원격 push·dev merge·배포는 하지 않았다.

## 2026-09-18 — 설치형 유료 작업 대기 구간 전체 화면 차단 구현

- Angular 공용 UI `shared/ui/blocking-progress`에 페이지 전체 입력을 막는 어두운 배경과 중앙 스피너를 추가했다. 화면 문구·카드 없이 스피너만 표시한다.
- 과금 작업 버튼을 누른 직후부터 사전 검사·저장·파일 확인·견적 조회가 끝날 때까지 표시하고, 과금 확인창이 열리기 직전에 숨긴다. 취소하면 원래 화면으로 복구하고, 승인하면 다시 표시하여 작업 생성·서버 응답·보관함 이동이 끝날 때까지 유지한다. 오류·예외 경로는 `finally`에서 닫는다.
- 적용 범위는 숏폼 프롬프트/URL/붙여넣기 생성, 대사 하이라이트, 댄스 하이라이트, Variation 일괄 생성, Variation 단건 재시도, 보관함의 유료 작업 재시도다. 댓글·순위 등 무료 재시도는 제외했다.
- 공용 과금 확인 서비스에는 확인창 직전/직후 생명주기 훅만 추가했다. 과금액·과금 정책·API·DB·서버 코드는 변경하지 않았다.
- 검증: 영향 범위 Angular 458/458, 전체 Angular 4678/4678, 스타일 6/6 통과. TypeScript spec compile, production build, `git diff --check`도 통과했다.
- 후속 사용자 요청으로 `feature/billable-operation-blocking-progress-20260918` 브랜치에 `6ec58054d894e4f6171dc47329e8ef06bf2520ab`로 커밋했다. 원격 push·dev merge·배포는 수행하지 않았다.

## 2026-09-09 — 다음 작업을 PG 테스트와 운영 구축 두 세션으로 분리

- 사용자 요청으로 시작 문구를 A(PG 기능 테스트/결함수정), B(TASKS5번의 개발 전환 제외 운영 구축)로 분리했다.
- NEXT_SESSION_PG_TESTS.md/NEXT_SESSION_PRODUCTION_SETUP.md 신규, NEXT_SESSION_PROMPT.md는 두 버전 진입점으로 변경. TASKS6절에 소유범위/조율 기준 추가.
- 공용 코드·배포·재시작 충돌 방지, 전용 진행기록, 라이브/desktop 식별자 별도 승인과 개발 전환 보류 조건을 유지했다.
- 이번 작업은 문서만 변경. 새 작업 생성·서버 명령·코드 수정·commit/push 없음.

## 2026-09-08 — 세션 종료: 환불·결제내역 UI까지 운영 배포

최신 정본: [종료 인수인계](./2026-09-08-production-pg-session-closeout.md), [TASKS](./TASKS.md), [다음 시작 문구](./NEXT_SESSION_PROMPT.md).
아래 시간순 과거 기록의 “미배포”는 당시 상태이며 최신 배포 판정은 이 항목을 우선한다.

- Customer888c2b96d818857306e9376c3436563c394971b1 / Adminfb3e532b3e9b195c5c149a207fbcbf5673932245 / API27103011e2e0672199721c6c3974c5bfc4e0d741까지 커밋·푸시·사용자 운영배포. Customer/Admin running/revision/HTTP200, API 앞선 health/DB3개ok. 앱 코드 미배포분 없음.
- Customer dashboard/payment-history/credits/header: 중립 모달·상태/주기표시·요금제모달, 환불상태 우선/종료구독관리숨김, 결제내역nav·표·24px제목·결제금액문구, 출처6색일치. Admin payment-operations/member-detail: 복사아이콘/스낵바/열폭/회원한줄, 한글결제유형, 환불 돈·내부완료 기반 표시. API subscriptionTerms 이후 추가 backend 변경 없음.
- 실제 검증: 추가400 정상구매 DB/Toss/정확30일/지급1·원장1, 취소·재개/카드변경 정상흐름, Pro월→연72,017 성공, 환불case61d6c4bc-b2b3-4328-835f-b27f3eb98807 돈·내부완료 및 구독1000회수. BILLING_DELETED 성공전송/DELETE200 사용자 확인.
- 환불 후5,200=topup4,800+trial400. 추가충전은 별도주문/30일기한이고 구독환불 자동회수 아님. 실제 사용 가능 여부는 OperationsService/credit 차감 코드를 확인했으며 desktop 운영실작업 검증과 구분.
- 후반 대상 tests: 결제운영24, 환불Customer57/Admin20, 표/header/credits26, 최종배지11 PASS. 각 prod빌드·diffcheck, mock Chrome desktop/mobile 검증. Admin 초기 번들565.89kB 경고. 최종 전체suite 재실행으로 표현하지 않음.
- 남은 위험/검증: 마지막 UI 실제확인, 완료환불 read-only DB대조, 다른환불/예약/갱신/실패/웹훅중복·복구, 자연종료와환불 동시경계, desktop/runner·운영안정성·live. 자동화/서버상태변경/DB초기화 없이 종료 문서5개 작성·갱신.
- 문서 작성 전 원본 Git: 앱3개clean/upstream표시차이없음, Infra5문서dirty, desktop3통합branch clean/upstream표시없음, Python별도branch clean, .codexmain25ahead+기존수정. 이번 문서화에서 commit/push 안 함.

## 2026-09-08 — 요금제 모달·주기 배지 Customer 푸시 완료

- 사용자 `배포 ㄱㄱ` 승인 후 Customer4파일 선택커밋 및 기존 integration 브랜치 푸시: `90bbb86d1182fb8710af3e5d47648eeab574f5f4`. 작업트리 clean/upstream 일치. 전체259 tests/prod빌드/diff --check 통과.
- 반영: 구독 상태 배지 파란 대비, 배포 기준 구독/결제수단 배치 유지, 오른쪽 변경 가능한 요금제 보기 모달, 현재상품 및 상향/하향 설명. 이용권 상단은 구독 출처+동일등급+유효한 구독 상태 확인 시 월간/연간 표시. trial/admin/정보누락은 추정하지 않음.
- m4-prod 사용자 직접 deploy-prod.sh web 실행 대기. 이번90bbb86 운영 배포/health/실화면 아직 미확인. API/Admin/DB 변경·migration 없음.

## 2026-09-08 — 구독 카드 최종 재배치 시안: 배포 기준 복원·요금제 모달

- 사용자 디자인 재요청에 따라 미커밋 좌우 대칭/카드정보 표 시안 폐기. 배포 Customer76fd82a의 구독 정보 상단 전체폭·결제수단 하단 왼쪽 구조로 복원. 결제내역과 하단 바로가기 위치 유지. 상태 배지는 기존 위치에서 active 테마의 푸른 배경·테두리·글자로 대비 강화.
- 하단 오른쪽에 요금제 변경하기 버튼, 기존 표는 TemplateRef 기반 MatDialog로 이동. 모달에서 상품 선택 후 닫힘을 기다리고 기존 서버 견적/필수 동의 확인창으로 연결. 단순 닫기는 견적·결제 요청 없음. 월/연 선택과 연간→월간 제한 유지.
- Customer dashboard4파일 미커밋. 전체255 tests PASS, prod빌드·diff --check 및 외부차단 로컬 mock 모달 열기/닫기/견적 전환/모바일 검증. 스크린샷 /private/tmp/clipper-picker-preview/. 현재 배포 버전은76fd82a, 이번 시안 커밋/푸시/배포 없음. API/DB/개발서버 변경 없음.

## 2026-09-08 — 요금제 표·문구 수정 Customer 배포 준비

- 사용자 `배포해줘` 승인 후 Customer7파일 선택커밋 및 기존 integration 브랜치 푸시 완료: `76fd82a42cc2b10d952faf64a606759fe73a8782`. 작업트리 clean/upstream 일치. 직전 prod빌드 통과, 커밋 전 전체253 테스트 재통과.
- API/Admin/Infra 변경·푸시 없음. 사용자가 m4-prod에서 deploy-prod.sh web 직접 실행하는 단계 대기. 운영 배포/health/실제 화면 완료로 간주하지 않음. DB migration 없음.

## 2026-09-08 — 운영 화면 피드백 일괄 반영: 문구 간소화·요금제 표

- 직전 배포 사용자 출력 확인: API27103011e2e0672199721c6c3974c5bfc4e0d741 running/public health·DB3개 ok, Customer9049d1de3470b0b1d2a4083eb4be946d256ce87e running/public /my HTTP200. 최초구독 월간/연간, 정상카드변경, 즉시 Business연간 견적, Basic연간 예약, 추가충전 화면 사용자 확인. 체크 전 비활성화 사용자 확인. 갱신재개는 운영 상태 변경 없이 로컬 mock 검증.
- 사용자 `그래 진행해` 승인으로 모은 변경 구현. Customer dashboard/payment-checkout 7파일만 수정. 최초구독 중복 소제목/파란 강조 제거, 두 안내 li를 체크박스 위로 분리. 동의문 매월/매년 간소화. 정상카드변경은 새 결제수단 사용에만 동의, 미납 카드변경은 즉시 미납금 동의 유지. 중단된 자동갱신은 재개를 암시하지 않음. 모달 KST/순차문구 삭제(시각 계산 KST 유지), 계산결과 중복행 삭제, 추가충전 단건 안내 간소화.
- 요금제 변경은 등급별 표/모바일 세로 행, 가격·현재상품·변경시점·액션 구분. 월간 이용자는 월/연 선택 가능, 연간 이용자는 연간만 노출하며 월간 변경 API 호출도 차단. 버튼 힌트는 Catalog upgradeRank/주기 기반, 최종 quote는 기존 서버가 결정. 서버 NOT_ALLOWED 409를 견적만료로 표시하던 문제를 원인별 문구로 수정. 연간→월간 정책 변경 없음.
- 테스트: 신규6실패 재현 후 Customer 전체253 PASS. prod빌드 통과, diff --check 통과, 독립 읽기전용 리뷰 주요 지적 없음. 최종 prod빌드로 외부연결 차단/local mock 데스크톱·390px 모바일·카드변경/갱신재개 필수 gate 검증. 스크린샷 /private/tmp/clipper-ux-preview/.
- 현 상태: 미커밋·미푸시·미배포. 다음 배포 대상 Customer만, API/Admin/DB/migration 변경 없음. 개발서버·개발DB 작업/라이브 전환/desktop 식별자 변경 없음. 기존주문 재진입·미납 카드변경 실제 운영 예외 E2E와 upgrade DB/Toss 대조는 잔여 검증 유지.

## 2026-09-08 — 결제 안내 변경 배포 준비·푸시 완료

- 사용자 `배포하자` 승인으로 이번 변경만 선택커밋/기존 integration 브랜치 GitHub 푸시. Customer `9049d1de3470b0b1d2a4083eb4be946d256ce87e`, API `27103011e2e0672199721c6c3974c5bfc4e0d741`. 두 원본 작업트리 clean/upstream 일치. Admin/Infra/기타 문서 푸시 없음.
- 커밋 전 전체 재검증: Customer250 PASS, API2427 PASS/16 SKIP. 직전 prod/Nest 빌드와 로컬 시각검증 유지. migration 없음.
- 운영 실행 대기. 사용자 직접 m4-prod에서 API build-only → API start-only/health → Customer build/start/health 순으로 한 단계씩 진행. 아직 실제 운영 배포 완료 아님.

## 2026-09-08 — 결제 안내·필수 동의 보완 로컬 구현 완료

- 사용자 `응 그렇게 보완해줘. 수정해줘.` 승인 범위 구현. 최초구독/기존주문 재진입에 금액·주기·해지 전까지 자동결제·취소 경로를 필수 동의문에 표시. API CheckoutSession은 초기 billing 주문 snapshot의 subscriptionTerms 제공, 불완전한 조건은 발급 실패.
- 차액 확인창: 새상품가격−기존구독공제=청구액, 작은 공제액 선택 이유, 펼침 산식(연간은 미래 지급분을 포함한 계약 전체 크레딧 기준), 새기간·구독크레딧 교체·다음청구 안내. 즉시/예약변경·갱신재개·카드변경에 필수 checkbox gate 추가. 정상 카드변경 무청구/연체 변경 미납금 즉시청구 구분. 추가충전은 1회결제/자동갱신 없음.
- 예약 변경이 있으면 그 상품의 반복결제 조건 사용. 리뷰 발견 재개 일정 누락을 currentPeriodEnd로 보완(취소 시 nextBillingAt=null). 청구정책/DB구조 변경 없음. 새로운 동의 이력 저장 API, 약관·FAQ 본문 추가 없음.
- 검증: Customer 신규 RED 확인 후 전체250 PASS, API2427 PASS/16 SKIP(옵트인 PostgreSQL 미실행), Customer prod/API Nest build 통과. 독립 diff 리뷰 및 diff --check 통과. 실제 prod 빌드를 로컬 파일/가짜 응답만으로 렌더링해 데스크톱·390px 모바일, 필수동의 전후 버튼, 펼침·스크롤·가로넘침 없음 확인. 외부 통신 차단. 스크린샷 `/private/tmp/clipper-disclosure-preview/`.
- 원본 Customer12파일/API3파일 미커밋. Admin 변경 없음, 기존 Infra 문서 보존. 커밋·푸시·서버배포 미실행. 배포 시 API와 Customer 모두 필요, migration 없음. 실제 배포 확인 전 전략팀 배포완료 보고 금지. 개발서버/DB/운영DB초기화/라이브키 전환 없음.

## 2026-09-08 — 전략팀 제7조 관련 최종 결제 동의 UI 재점검

- 사용자 차액 모달 설명 개선안에 동의하고, 전략팀에 약속한 최종 동의 항목의 금액·주기·자동갱신 표시가 현재 구현됐는지 재점검 요청.
- Customer checkout: reviewTerms가 있는 정상 product 진입은 상품/결제금액 및 매월·매년 자동결제 안내 있음. 필수 checkbox와 미동의 버튼 차단은 있으나 동의문은 `카드 등록과 구독 결제 진행에 동의합니다.`로 금액/주기/자동갱신·해지 전까지 지속 여부를 직접 담지 않음.
- receipt 기존주문 재진입 billing_auth 경로는 CheckoutSession에 billingIntervalMonths/자동갱신 조건이 없어 reviewTerms 없이 ready가 됨. 금액/상품은 표시되나 반복결제 안내는 reviewTerms 조건문 때문에 빠질 수 있음. 현재 상품 카탈로그값을 주문약정으로 추정해 채우지 말고 주문 snapshot 기반 API 응답 보완이 필요.
- 즉시 요금제변경 ConfirmDialog는 차액2개/선택액/첫월크레딧만 표시, 새상품 정기금액/주기/자동갱신 및 최종 동의 체크박스 없음. 예약변경 확인창은 다음 갱신부터 적용 안내와 다음 결제금액은 있으나 구체적 주기/자동갱신 동의 항목 없음. 따라서 전략팀에 약속한 `최종 동의 항목에도 금액·결제주기·자동갱신 여부 명확 표시` 보완 완료로 보고할 수 없음.
- 보완 설계: 최초구독 동의문에 최초청구금액+주기+반복금액+자동갱신/다음결제취소 명시. 변경모달은 승인된 가격-공제 요약/상세 산식과 별도로 지금 차액청구 및 이후 새 정기금액/주기를 동의문에 명시. 명시적 미동의시 진행 차단. API 기존주문 재진입용 계약값은 snapshot 출처로 보완. 아직 제품 코드/약관/FAQ 수정·커밋·배포하지 않음. 이 기록은 구현 상태 감사이며 법적 적합성 결론이 아님.

## 2026-09-08 — Pro 연간 즉시 변경 성공 및 결제 설명 UX 피드백

- 사용자 결제결과: upgrade_6f4152490ae182a69e8080940e280eb112c7790a437394935e850375, Pro연간/72017원/2026-09-08 13:50, 변경·결제완료. /my Pro연간82800원/12개월/월1000, 활성 자동갱신, 이용기간종료·다음결제2027-09-08 13:50 확인.
- 지급표/원장: 기존 구독1000 회수(-1000/잔여0), 새 첫월1000 지급(+1000/잔여1000, 기한2026-10-08 13:50), 추가충전400와 무료체험400 유지하여 총1800. 무료체험 실제 표시기한2026-10-08 06:03 확인. 이 upgrade 주문의 DB/Toss 대조·중복방지 검증은 아직 별도 남음.
- 사용자 질문: TEST에서 카드알림이 없고 라이브 첫 구독/차액청구 알림 여부, 기간/크레딧 차액72017/71900 계산 이유 및 모달 설명 부족. 공식 Toss 테스트환경 문서는 실제 청구 없음, billing은 카드등록과 승인 분리/추가 인증 없이 승인 가능 설명. 라이브 실승인과 카드사 알림 수신은 구분해 설명할 것(알림설정·카드사 조건에 따라 수신, 보장 금지).
- 코드 산식 재확인: 기간 공제=floor(10900×남은기간/전체기간)=10783, 차액82800-10783=72017. 구독크레딧 사용0/계약1000이므로 공제10900/차액71900. 둘 중 큰 차액 또는 작은 공제액 적용. trial/topup 제외, 날짜가 아닌 timestamp 비율 사용. 현재 정책 설명이지 변경 정책 승인 아님.
- UX 개선 제안 준비: 모달에 새상품가격/기존구독공제/지금결제액을 중심 표시하고 공제 기준 규칙과 적용 기준을 명시, 상세 펼침에 두 산식·선택 이유 제공. 새기간 시작/첫월 크레딧 교체/다음 정기결제금액도 결제 전 고지. 약관·FAQ는 상세 예시와 정책 정본 연결 역할, 핵심 조건을 링크만으로 대체하지 않는 방향. 아직 구현·커밋·배포하지 않음.

## 2026-09-08 — Pro 월간→연간 즉시 변경 견적 사용자 확인

- 사용자 확인창: 현재 Pro월간→Pro연간, 기간기준 차액72017원/정기구독 크레딧 사용량기준71900원, 청구72017원, 새 이용기간 첫 월1000크레딧. `₩72,017 결제하고 변경`/취소. 확정 실행은 아직 미확인.
- 코드 확인: 동일 등급 월간→연간 immediate, 두 차액 중 큰 값 선택. 기본 Pro연간82800원, 사용량기준 월간 잔존10900원으로71900원. 기간 경과로 기간기준 잔존10783원/차액72017원. 견적 TTL5분.
- 성공 시 내부 paidAt 기준12개월 새 이용기간 및 다음청구 설정, 기존 구독 잔여크레딧 회수 후 첫 월1000 새지급. trial/topup 유지. 현재 사용없으면 기존 구독1000→새1000으로 총1800 예상. 연간→월간 직접변경은 현 정책 forbidden이므로 확정 안내에 이 효과 포함. 결제는 현재 Billing TEST키 흐름 유지. 실제 결제결과·기간·원장 검증 대기.

## 2026-09-08 — 카드변경 후 권한·잔액·일정 유지 및 추가결제 없음 확인

- 사용자 `응`으로 직전 확인목록 전체 확인: Pro 활성/자동갱신중, 사용가능1800, 이용기간 종료·다음결제예정2026-10-08 06:06 유지, 카드변경으로 생긴 신규 결제완료 건 없음.
- 활성 구독 카드변경 기본 시나리오 통과. 기존 빌링키 정리/실제 다음청구 새키 사용/실패·취소 경로는 별도 잔여 검증 유지.
- 다음은 요금제 변경 가능 상품/견적·적용 시점 확인부터 진행. 신규 결제나 변경 확정 전에 화면의 실제 금액/즉시·예약 구분을 확인하고 사용자에게 설명할 것. 운영 DB 시각 변경이나 갱신 강제실행 없음.

## 2026-09-08 — 활성 구독 결제수단 변경 성공 사용자 확인

- 사용자 테스트 카드 변경 결과: 변경 완료/결제수단 변경 완료, 다음 결제부터 새 결제수단 사용 안내 표시. /my 복귀 후 변경된 카드 표시 확인.
- 카드변경 성공 화면 및 고객 카드 표시 반영 확인 완료. 다음은 Pro 활성/사용가능1800/종료 및 다음결제2026-10-08 06:06 유지, 신규 결제완료 건 없음 확인. 기존 빌링키 정리/실제 다음청구 새키 사용/취소·실패 경로는 이 결과만으로 완료 처리하지 않음.

## 2026-09-08 — 해지·재개 후 추가 결제 없음 사용자 확인

- 사용자 결제내역 정상 확인: 직전 안내의 기존 Pro월간10900원/9월8일06:06 및 추가충전400/5900원/10:23 외 해지·재개로 생긴 새 결제완료 건 없음.
- 해지예약→재개 고객 화면·권한/잔액 유지·신규결제 없음 확인 완료. 관리자/DB 사후 상태 직접 확인은 별도 남음.
- 다음은 활성 구독 결제수단 변경 테스트 안내 준비. 현재 past_due가 아닌 active 상태에서 카드 등록 변경은 즉시 결제가 없는 흐름인지 고객 코드 확인. 실제 카드변경 실행/결과는 아직 미확인.

## 2026-09-08 — 구독 자동 갱신 재개 고객 화면 확인

- 사용자 자동 갱신 다시 시작 실행 후 /my: Pro 이용권 활성/정기구독/사용가능1800 유지, 자동 갱신 중 복구. Pro월간10900원/월1000 유지. 현재 이용기간 종료와 다음 결제 예정 모두2026-10-08 06:06, 한국시간 및 예정시각 이후 순차결제 안내 표시. 다음 자동 결제 취소 버튼 복구.
- 해지예약→재개의 고객 화면 동작 확인 완료. 다음은 /my/payment-history에서 이 조작으로 신규 결제완료 주문이 발생하지 않았는지 확인. 기존 확인 주문은 Pro월간10900원(9/8 06:06)과 추가충전400/5900원(9/8 10:23). 사용자가 별도 결제를 하지 않았다면 두 건 유지 예상. 결제내역/관리자·DB 사후 상태를 화면만으로 확인했다고 간주하지 않음.

## 2026-09-08 — 구독 해지 예약 고객 화면 확인

- 사용자 /my 다음 자동 결제 취소 확정 후 화면: 이용권 활성/Pro/정기구독, 사용가능1800 유지. 상태 다음 결제 취소됨, 현재 결제기간 종료일까지 이용 안내, Pro월간10900원/월1000 유지, 현재 이용기간 종료2026-10-08 06:06 유지, 다음 결제 예정 중단됨, 자동 갱신 다시 시작 버튼 표시.
- 해지예약의 고객 화면 기대 동작 확인. 다음은 자동 갱신 다시 시작을 사용자 실행하여 기존 결제예정/활성상태·권한·잔액 유지 확인. 재개 결과/DB 상태 확인은 아직 미수신.

## 2026-09-08 — 관리자 상태 재확인 반복 사용자 확인

- 직전 안내(Admin 해당 추가충전 주문 상태 재확인→응답 후 다시 실행→결제/지급 완료 및 잔액1800 유지)에 사용자 `응`으로 확인.
- 추가충전 정상구매·현재 지급/원장1건·정확한30일·Toss paymentKey 대조·Admin 상태 재조회 반복 검증 완료. 웹훅/콜백 재전달 및 실제 지급함수 재시도 멱등성은 별도 미검증 유지.
- 다음은 테스트 구독 해지예약/재개 동작 검증 안내 준비. 사용자 실행 전 UI와 효과 확인하며 서버/DB 직접 조작하지 않음.

## 2026-09-08 — Toss paymentKey 직접조회 성공·금액/상태 대조 완료

- 사용자 m4-prod 동일 Widget TEST키 paymentKey 조회 HTTP200. orderId topup_2b66981ddc5c41a7b05ddc1245d862e2 일치, status DONE, totalAmount5900/balanceAmount5900, approvedAt2026-09-08T10:23:07+09:00.
- 기존 DB paid/succeeded/5900 및 지급1건·원장1건·400/잔여400과 대조 완료. Toss 승인시각10:23:07과 내부 paid_at/granted_at10:23:08.126은1.126초 차이이며 동일시각이라고 기록하지 않음. 크레딧은 확인된 내부 지급시각부터 정확히30일.
- 동일키 orderId 경로404 NOT_FOUND_MERCHANT, paymentKey 경로200이라는 관찰로 범위를 좁힘. 공용키 전체 조회불가/주문부재 아님. 결제복구 코드 PaymentReconciliationService는 저장된 paymentKey가 있으면 이미 paymentKey 조회를 우선함. 키가 없는 주문번호 fallback 경로의 공용키 제한/원인은 별도 미확정.
- 다음 사용자 Admin /payment-operations 해당 주문 `상태 재확인`을 응답 완료 후 한 번 더 실행하여 실제 앱 재조회 경로와 잔액 유지 확인. paid 상태는 조회/대조 후 조기 반환하므로 이는 상태 재조회 반복 검증이며 fulfillment 재실행/웹훅 재전달 멱등성 전체 검증과 구분. 지급 재처리는 paid+failed일 때만 노출되므로 이번 succeeded 주문에는 요청하지 않음.

## 2026-09-08 — Toss 조회404 NOT_FOUND_MERCHANT 확인

- 사용자 오류코드 응답: HTTP404/NOT_FOUND_MERCHANT. NOT_FOUND_PAYMENT가 아님. 공식 오류표는 상점 정보가 없다는 뜻으로 설명함. 공용키는 모든 조회가 불가능하다고 단정할 근거는 아직 없음.
- 다음 진단: 같은 Widget TEST키를 유지하고, 운영 DB의 해당 주문 payment_key를 프로세스 내부에서 읽어 GET /v1/payments/{paymentKey}로 조회. orderId 조회와 경로를 달리해 비교, paymentKey/비밀키는 출력하지 않음. DB는 read-only, 결제/취소/reconcile/지급 실행 없음. 성공 시 orderId/금액/시각과 기존 DB 대조, 동일 상점 오류 시 키/상점 연동 문제 범위로 추가 조사.

## 2026-09-08 — Toss 주문번호 직접조회 HTTP404 진단 시작

- 사용자 m4-prod Widget TEST키 GET /v1/payments/orders/topup_2b66981ddc5c41a7b05ddc1245d862e2 결과 HTTP404. 직전 진단 스크립트가 실패 응답 body를 출력하지 않아 오류 code는 아직 모름.
- 공식 API 문서에서 주문번호 조회 경로 확인, 결제조회 오류표에404 NOT_FOUND_PAYMENT/NOT_FOUND 존재. 404만으로 결제부재/공용키 조회불가/키변경을 단정하지 않음. 로컬 API 역시404와 NOT_FOUND_PAYMENT 조합만 payment-not-found로 분류함.
- 다음 사용자 실행은 같은 GET에서 HTTP와 오류 code만 출력하는 읽기 전용 진단. 승인/취소/reconcile/재지급은 실행하지 않음. DB paid/succeeded·지급1건·원장1건·정확한30일 확인 사실은 유지하되 Toss 직접 대조는 미완료.

## 2026-09-08 — Toss 테스트키 구분 사용자 정정·단건 조회 경로 변경

- 사용자 확인: 정기결제는 본인 상점 테스트 결제내역에서 보이나, 단건결제는 Toss 공용 테스트키를 사용하여 본인 상점 콘솔에서 볼 수 없음. 앞선 단건 콘솔 대조 안내는 이 키 구분을 반영하지 못했으므로 철회.
- 기존 API HttpTossPaymentsProvider의 getPaymentByOrderId 구현 확인: Widget secret으로 GET https://api.tosspayments.com/v1/payments/orders/{orderId}, Basic secret: 인증. 다음은 사용자가 m4-prod 실행 중 API 컨테이너에서 같은 방식으로 해당 주문만 조회하고 orderId/status/totalAmount/balanceAmount/approvedAt만 출력. TEST키 확인 후 실행, 키/카드/paymentKey 출력 및 DB/결제 변경 없음.
- 아직 토스 직접조회 결과 미수신. 공용 Widget 상점의 콘솔·웹훅 설정/수신 검증 가능 범위는 본인 Billing 상점과 구분한다.

## 2026-09-08 — 추가충전400 운영 DB 주문·지급·원장 정합성 확인

- 사용자 m2-db Admin 읽기 전용 SQL 출력: topup_2b66981ddc5c41a7b05ddc1245d862e2 status paid/fulfillment_status succeeded, amount_krw/paid_amount_krw5900, grant_count1/grant_ledger_count1/granted_credits400.
- topup grant active, initial/remaining400, paid_at 및 granted_at 모두2026-09-08 10:23:08.126+09, expires_at2026-10-08 10:23:08.126+09, validity30 days. 화면 분 단위 표시와 DB 시각 기준30일 정책 일치. READ ONLY 트랜잭션 ROLLBACK 완료.
- 이 주문의 현재 중복 지급 없음과 정합성 확인 완료. 재전달/재시도 멱등성 전체 E2E를 검증한 것은 아님. 다음은 Toss 테스트 상점에서 동일 orderNo의 결제상태/금액 대조. 비밀키/paymentKey/카드정보 공유 불필요. 이후 중복 콜백/웹훅 재처리 검증은 별도 절차에 따라 진행.

## 2026-09-08 — 추가충전400 사용기한·현재잔액 사용자 확인

- 사용자 `맞아`로 /my/credits 사용가능 잔액1,800 및 추가충전400 사용기한2026-10-08 10:23(KST) 확인.
- 다음은 m2-db 운영 Admin 컨테이너에서 해당 topup 주문 한 건의 결제/지급상태, grant 개수, grant 원장 개수·합계, granted_at/expires_at 및 정확한 유효기간을 읽기 전용 조회. 대상 order_no `topup_2b66981ddc5c41a7b05ddc1245d862e2`. SQL은 실제 payment_orders/credit_grants/credit_ledger_entries 엔티티 컬럼 및 payment_order_id 연결에 근거함.
- 아직 DB 조회 출력 미수신, 정합성/중복지급 검증 완료로 처리하지 않음. Toss 직접 대조/재전달 등 E2E 검증도 별도 남음.

## 2026-09-08 — 지급표 열 간격 사용자 화면 확인 완료

- 사용자 `응 괜찮아졌어. 이제 뭐하지`로 배포 후 열 간격 개선 확인. Customer e8462ca 간격 수정 구현·배포·health·사용자 화면 확인 완료.
- 다음은 원래 우선순위인 추가크레딧 구매 검증 재개: /my/credits 현재 사용가능 잔액과 추가충전400 지급건의 KST 사용기한 실제 표시 확인. 구매 당시 잔액1800/결제시각9월8일10:23, 30일 정책상10월8일10:23 예상이나 실제 grant시각/만료값은 별도 확인해야 함.
- 확인 이후 DB/Toss 주문·지급 정합성 및 중복 지급 검증으로 이어갈 것. 단순 화면 새로고침만으로 webhook/서버 중복방지 E2E 완료 처리하지 않음. 고객/Admin 결제예정 실제 화면 확인과 나머지 PG 시나리오도 TASKS에 유지.

## 2026-09-08 — Customer 열 간격 수정 실행 revision·공개 health 통과

- 사용자 최종 출력: status=running, revision=e8462cab16be56d42de12643259362ad5e16333d, https://clipperstudio.ai/health HTTP200. Customer 열 간격 수정 배포 및 기본 점검 완료.
- /my/credits 강력 새로고침 후 실제 열 간격에 대한 사용자 확인은 아직 없음. 다음은 이 화면 확인을 받고 고객/Admin 결제예정 표시 및 추가크레딧 PG 잔여 검증 재개. 추가 서버 변경 명령 불필요.

## 2026-09-08 — 지급표 열 간격 수정 Customer 운영 교체 출력 확인

- 사용자 m4-prod `deploy-prod.sh web` 실행. Customer e8462cab16be56d42de12643259362ad5e16333d 빌드 및 clipper-web-client-prod 새 컨테이너 Up/운영42202 포트 확인. Admin/API/DB 추가 변경 없음.
- 다음은 고객 웹 컨테이너 revision·공개 HTTPS health 읽기 전용 확인, /my/credits 강력 새로고침 후 열 간격 실제 화면 확인. 교체 출력만으로 화면 확인 완료 처리하지 않음.

## 2026-09-08 — 지급표 열 간격 수정 승인·Customer 푸시 완료

- 사용자 수정 예시 확인 후 `반영ㄱㄱ` 승인. Customer credits.component.scss만 `e8462ca`(fix(credits): balance grant table column spacing) 선택커밋 후 기존 GitHub origin/integration/toss-payments-pg-20260903 정상 push(exit0). 직전 로컬 렌더링·prod빌드 통과 소스와 동일, staged diff check 통과.
- 다음 사용자 m4-prod 실행: `sh /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/deploy-prod.sh web`. 고객 웹 소스 fast-forward/운영 이미지 빌드/고객 웹 컨테이너 교체만 수행, 짧은 웹 접속 중단 가능. Admin/API/DB migration 불필요. 서버 실행 결과 및 실제 화면 확인 대기.

## 2026-09-08 — 지급 표 열 간격 후속 수정(로컬)

- 사용자 운영 화면 피드백: 출처–지급 간격 과다, 잔여–상태 붙어 보임. 실제 SCSS로 로컬 Chrome 예시 재현 시 1440px viewport에서 해당 텍스트 간격246px/24px 확인. 자동 열 배분 및 숫자 우측/상태 좌측 정렬 조합이 원인.
- Customer 원본 `credits.component.scss` 한 파일 수정. 761px 이상에서 table-layout fixed, 열 비율18/16/16/22/나머지28%, 패딩 포함 너비 계산, 숫자/상태 가운데 정렬. 모바일 기존 grid 배치 유지. 동일 재현에서168px/143px로 조정.
- 검증: 실제 SCSS 컴파일한 독립 예시를 Playwright/Chrome으로1440/1024/820/761/760/390px 확인, 가로 넘침·셀 잘림 없음. 999,999/환불 처리 중/기한 없음 포함. desktop/mobile screenshot 시각 확인. Node22 Angular prod빌드 성공(exit0), git diff --check 통과. CSS만 변경하여 구현을 반복하는 단위테스트 추가/전체 단위테스트 재실행은 하지 않음.
- 로컬 예시 `/private/tmp/clipper-grant-spacing-after.html`, screenshot `/private/tmp/clipper-grant-spacing-after-1440.png` 및390.png. 운영 데이터 연결 없음. Customer1파일 미커밋·미푸시·미배포. 서버/DB 변경 없음. 운영 표 수정 재배포는 Customer만 필요.

## 2026-09-08 — 공개 운영 카탈로그 상품명·상품조건 확인

- 사용자 m4-prod `curl -fsS https://api.clipperstudio.ai/catalog/credit-products` 성공 응답 확인. 추가 크레딧400/1,000/4,000 한글 이름 반영, 각각 credits400/1000/4000 및 priceKrw5900/10900/29900, validityDays30, isActive true 유지.
- 운영 세 앱 배포·기본 health·상품명 실제값 확인 완료. 고객 /my/credits의 C표·단일잔액·KST 날짜시각과 /my 및 Admin 결제예정 표기의 실제 화면 확인은 아직 남음. 과거 주문 snapshot 이름은 보존하며 한글화 성공 여부 판단에 사용하지 않음.
- 다음 사용자 확인은 /my/credits 새로고침 후 지급 표와 사용 기한 값 전달. 마지막 잔액1,800은 이후 사용/환불 등 변동이 없다면 유지될 예상값이지 이번 응답으로 재확인된 값은 아님. DB/Toss/중복 방지 등 PG 잔여 검증 유지.

## 2026-09-08 — 운영 실행 revision·내부 health 통과

- 사용자 출력: Customer6e951cd8d84a6a8b89b24f79556b61e5dd245e4b/Admin31ad799925c4256dbc2ed4d2962aad2dd338f462/API8195a351f3316e5711028f45ad0c8e94cd2565b5 모두 running으로 목표 revision 일치.
- 내부42202/42302/43202 health 모두 HTTP200, API status ok 및 db.user/release/admin 모두 ok. 세 앱 운영 교체와 기본 점검 완료.
- 다음: 공개 HTTPS `/catalog/credit-products` 읽기 전용 조회로 상품명3개·가격·수량·기한 실제값 확인, 고객/Admin 변경 화면 확인. 추가크레딧 전체 E2E/정확한 만료시각·중복방지 등은 별도 잔여 검증 유지.

## 2026-09-08 — 운영 세 앱 컨테이너 교체 출력 확인

- 사용자 m4-prod `deploy-prod.sh all --start-only` 실행. clipper-web-client-prod/admin-prod/api-prod 세 컨테이너 모두 새로 생성되어 Up, 운영 LAN 포트42202/42302/43202 확인. `Selected containers started.` 출력 확인.
- 아직 기동 직후 상태만 확인했으며 health/실행 revision/상품명 실제값·migration 이력/UI 확인은 남음. 다음은 m4-prod 읽기 전용 컨테이너 revision 및 내부 HTTP/API health 점검.

## 2026-09-08 — 운영 migration 명령 완료 사용자 출력 확인

- 사용자 m4-prod `migrate-db.sh prod` 실행. USER192.168.0.7:55202/clipper_user_prod, ADMIN55212/clipper_admin_prod, RELEASE55222/clipper_release_prod 대상 확인 및 `migrate prod` 입력.
- User/Admin/Release 각각 `migration command completed.` 확인. 직전 pending 조회는 Admin LocalizeCreditProductNames1788900000000 한 건. 상품명 실제값·적용 이력 사후 조회는 아직 남음.
- 다음 사용자 실행은 `deploy-prod.sh all --start-only`: 준비된 세 prod 이미지로 앱 컨테이너 강제 재생성(짧은 접속 중단 가능), 소스 pull/재빌드/DB migration 없음. 이후 revision/health/상품명·UI 검증 예정. 아직 앱 교체 결과는 받지 않음.

## 2026-09-08 — 운영 미적용 migration 읽기 전용 확인

- 사용자 m4-prod 새 API 이미지 one-off/read-only 조회 결과: user 미적용 없음, admin `LocalizeCreditProductNames1788900000000` 한 건, release 미적용 없음.
- 다음 사용자 실행은 `migrate-db.sh prod`. 확인된 한 건은 기본 상품 code/name 일치 조건의 이름 UPDATE만 수행하므로 기존 앱과 호환되고 전체 서비스 중단 없이 적용 가능. 가격/수량/기한/과거 주문·원장 변경 및 DB 초기화 없음. 실행 대상 출력이 운영 DB3개와 일치할 때 `migrate prod` 입력 안내. 적용 완료 출력은 아직 받지 않음.

## 2026-09-08 — m4-prod 세 앱 이미지 빌드 사용자 출력 확인

- `deploy-prod.sh all --build-only` 사용자 실행 완료. Customer6e951cd8d84a6a8b89b24f79556b61e5dd245e4b/Admin31ad799925c4256dbc2ed4d2962aad2dd338f462/API8195a351f3316e5711028f45ad0c8e94cd2565b5 이미지 빌드 및 `Images built. No application or DB changes performed.` 확인.
- 실행 중인 앱은 아직 이전 이미지. migration/재시작 미실행. 다음은 새 API 이미지에서 운영 DB별 미적용 migration 목록을 읽기 전용 조회하여 User/Release 없음, Admin LocalizeCreditProductNames1788900000000 한 건인지 확인. 기존 migration runner는 show를 지원하지 않으며 임의 show 인자를 주면 실제 migration을 실행하므로 사용하지 않음.

## 2026-09-08 — m4-prod 배포 사전 점검 사용자 출력 확인

- 사용자 실행 hostname `m4-produi-Macmini.local`, 저장소 경로 `/Users/m4-prod/Documents/projects/clipperstudio/{clipper_infra,clipper_web_client,clipper_web_admin,clipper_web_api}` 확인.
- 네 저장소 모두 integration/toss-payments-pg-20260903/upstream 설정 및 clean. 서버 HEAD Infra088e520/Customer06a3977/Admin71da3b9/API9733be3으로 업데이트 전 기준과 일치.
- 다음 사용자 실행은 `deploy-prod.sh all --build-only`: 현재 upstream fast-forward와 세 앱 이미지 빌드만 수행. 실행 중인 앱/DB 변경 없음. 빌드 결과·SHA 확인 후 migration 단계 안내 예정. 아직 빌드 실행 결과는 받지 않음.

## 2026-09-08 — 명시 승인 후 세 앱 GitHub 푸시 완료

- 사용자 `푸시해줘`로 직전 질문의 세 저장소/커밋/브랜치 외부전송 승인. Customer `6e951cd`, Admin `31ad799`, API `8195a35`를 각 GitHub `OhMyMetabuzz/clipper_web_*` origin의 `integration/toss-payments-pg-20260903`에 정상 push 완료(exit0). 강제 push/다른 브랜치 병합 없음.
- `git ls-remote --exit-code origin refs/heads/integration/toss-payments-pg-20260903`로 세 원격 HEAD가 각 로컬 커밋과 일치함을 확인. 세 작업트리 clean/upstream 일치. 직전 승인 검토 차단은 명시 승인으로 해소됨.
- 변경 내용 및 검증은 바로 아래 배포 준비 기록과 동일. Infra/.codex 변경은 푸시하지 않음.
- 서버·DB 작업 미실행. 다음은 사용자가 m4-prod에서 hostname/네 저장소 경로·브랜치·상태·HEAD를 읽기 전용으로 확인하고 출력 전달 → build-only → migration 확인/적용 → start-only 및 화면 확인을 매뉴얼에 따라 한 단계씩 진행. DB 재생성/개발 작업/라이브 전환/desktop 식별자 변경 금지 유지.

## 2026-09-08 — 배포 승인·앱 선택커밋 완료, GitHub 푸시 승인 검토 차단

- 사용자 `배포하자` 요청으로 검증한 앱 변경만 기존 `integration/toss-payments-pg-20260903`에 선택커밋. Customer `6e951cd`(6파일), Admin `31ad799`(5파일), API `8195a35`(4파일). 세 작업트리 clean, 각 upstream보다 1 ahead. Infra 문서5개와 .codex 기존 변경/ahead25 커밋은 포함하지 않음.
- 세 origin을 fetch해 기존 HEAD와 원격 일치 확인 후 검증. Customer 전체243, Admin 전체372, API 전체2424 통과/10 skipped. Angular 명령은 위 후속 구현과 동일, API는 `CATALOG_TEST_PG_SOCKET=/private/tmp/clipper-credit-name-test.eW0mOS node node_modules/jest/bin/jest.js --runInBand`. 임시 로컬 Unix socket 전용 PG를 사용한 catalog 실제 SQL 검증 포함. 검증 후 임시 PG 종료. 기존 개발·운영 DB 접근 없음.
- 독립 read-only 리뷰: Critical/Important/Minor 발견 없음. 세 staged diff check 통과. 직전 동일 소스 Customer/Admin prod빌드·API빌드 성공 결과 유지.
- GitHub `OhMyMetabuzz/clipper_web_client`에 대한 첫 `git push origin HEAD:refs/heads/integration/toss-payments-pg-20260903` 실행 요청이 자동 승인 검토에서 거절됨. 사유: 배포 승인은 있으나 특정 저장소/커밋의 GitHub 외부 전송 명시 승인이 부족함. 명령 실행 전 차단되어 세 repo 모두 푸시되지 않음. 우회/재시도하지 않음.
- 다음: 위 세 커밋을 각 기존 GitHub origin의 같은 integration 브랜치로 전송할 명시 승인 요청 → 승인 후 정상 push/원격 hash 확인 → 사용자에게 m4-prod hostname/저장소 상태 읽기 명령부터 한 단계씩 안내. 서버 배포·migration은 아직 실행하지 않음. 운영 TEST키 유지, DB 재생성/개발 환경/desktop 식별자 변경 금지 유지.

## 2026-09-08 — 단일 잔액·결제 예정 시각 표시 후속 승인 구현

- 사용자 `진행해줘`로 직전 제안의 잔액 단일화와 고객/Admin 결제예정 표기 통일 승인.
- Customer dashboard/credits: 사용 가능 크레딧 한 번만 표시, 2개/1개 항목에 맞춰 grid 조정. dashboard 다음결제를 `다음 결제 예정`, `yyyy-MM-dd HH:mm` +0900으로 변경. 유효한 예정값이 있고 중단되지 않은 경우에만 KST/예정시각 이후 순차결제 안내.
- Admin 회원목록/상세: 다음 결제 예정 명칭/KST 분단위 표시 통일, 구독월 경계도 같은 timezone 적용. 상세의 구독관련 해지예약/예약변경도 +0900 적용. 중단건은 순차결제 안내 숨김. 상세 수동크레딧 요약도 사용가능 하나로 변경.
- 범위: API heldBalance/spendableBalance 계약과 실제 청구/크레딧 집계/만료 정책은 유지. 운영 서버명령·개발 DB 작업 없음.
- 검증: Customer 회귀 기대 먼저 변경하여8실패/37통과, Admin3실패/23통과 확인 후 구현. Customer 잔액2칸/공백에 의존한 기존 테스트2건 수정. 최종 Customer전체243/Admin전체372 통과. Admin관련26통과. UTC 기본시간대에서 KST 표시, 결제중단시 안내숨김 검증 포함.
- 명령: Node22.22.3 `node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless --progress=false` 각 repo, `CI=1 node node_modules/@angular/cli/bin/ng.js build --configuration prod --progress=false` 각 repo. 두 prod빌드 성공, Admin 기존 initial bundle 경고557.09kB/500kB 유지. `git diff --check` 통과. 처음 Admin 테스트의 `--port=9877`은 CLI 미지원으로 실패, 옵션 제거하고 테스트 순차실행.
- 현재 원본 미커밋: Customer6파일(C안 포함), Admin5파일, API상품명4파일. 커밋/푸시/운영배포 미진행. Infra 기존 문서5개와 .codex 기존 변경 보존.
- 다음: 로컬 화면 검토 후 승인된 선택커밋/푸시, m4-prod 이미지 준비→사용자 migration/배포를 장비·영향과 함께 단계별 안내, 추가크레딧 DB/Toss/중복방지 검증 이어가기.

## 2026-09-08 — C안 지급 표 구현 및 크레딧·갱신 시각 설명

- 사용자 선택: C안 표. 길었던 정기구독 기한 문구와 유효기간 문구 통일 요청.
- Customer 원본 `credits.component.html/scss/spec.ts` 변경: 출처/지급/잔여/상태/사용 기한의 semantic table, 모바일 지급건별 재배치, 환불잠금 상태 유지, 기한 `yyyy-MM-dd HH:mm` +0900, 한국시간 안내, 기한없음 `제한 없음`. 기존 benefitPeriodEnd 우선/expiresAt fallback 데이터 선택은 유지.
- 테스트 먼저 수정해 3실패/8통과 확인 → 구현 후11통과. 전체 `node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless --progress=false`:241통과. Node22.22.3 prod빌드 성공. 초기 sandbox 빌드 exit134, 비대화형 재실행에서 Google Fonts DNS 제한 확인 후 권한 있는 동일 prod빌드 성공. `git diff --check` 통과.
- 정책 진단: `CreditGrantsService.summaryWithManager`는 `spendableBalance: heldBalance`로 두값 동일. sumCurrentBySource는 active/양수/지급시각도래/미만료만 합산하므로 만료·회수·환불잠금은 양쪽 합계 제외. 이력은 보존. 8/12 과거 설계의 이용권종료시 사용정지 정책은 8/31 이후 유효크레딧만 검사하는 정책으로 변경됨. 보유/사용가능 두 UI 숫자는 현재 차이가 없어 단일 사용가능 잔액 권장, 아직 변경하지 않음.
- 갱신 진단: API ScheduleModule과 PaymentRecoveryScheduler 등록, EVERY_MINUTE, running 재진입 방지, 만료된 카드등록/후보키 정리 후 dueSubscriptionIds(now,100)를 순차처리. 조건 nextBillingAt<=now, renewal 직전 isDue 재확인 후 Toss chargeBillingKey 호출. 표시 시각 정각 실행/성공 보장이 아니며 초·선행처리·부하·장애에 따라 늦어짐. 실제 운영 worker/E2E는 여전히 미검증.
- 화면 차이: Customer dashboard 다음결제는 날짜만/+0900, Admin 회원상세는 분까지/브라우저 기본 timezone. 같은 nextBillingAt의 포맷 차이. 두화면 `다음 결제 예정`+KST 날짜시각 및 예정시각이후 순차처리 설명 권장. 이 두화면은 이번에 수정하지 않음.
- 기한 표현 이유: 구독 credit benefitPeriodEnd는 연간구독에서도 월별 크레딧의 종료로 전체 이용기간과 다를 수 있음. 지급내역에서는 출처가 이미 보이므로 `사용 기한` 통일이 정확함.
- 기존 비교화면은 `credit-grants-options-v3.html`로 갱신, C 기본선택/기한표현 통일. 실제 DB/API 연결 없는 예시 화면이라는 표시는 유지. 제품 변경과 구분.
- 현재 Customer3파일/API상품명4파일 미커밋·미푸시·미배포. 운영/개발 DB 조작 없음. 다음 단계는 사용자 로컬 확인과 승인된 선택커밋/배포, 추가크레딧 만료시각·DB/Toss 대조·중복방지 계속.

## 2026-09-08 — 추가 크레딧 첫 구매 확인·상품명 migration·UI 비교안

- 사용자 실행으로 운영 API의 Widget/Billing 키4개 `TEST` 확인. 활성 Pro월간, 구독1,000+무료체험400, 구매전1,400.
- 사용자 브라우저 보고: `topup_2b66981ddc5c41a7b05ddc1245d862e2`, 5,900원/400크레딧, 2026-09-08 10:23 KST, 지급완료, 잔액1,800. 추가충전400/400와 2026-10-08 표시. DB/Toss 대조·초 단위 만료값·중복방지·웹훅은 미검증.
- 발견: 상품 카탈로그 기본명이 `400 Credits` 등으로 남아 주문 snapshot에 복사됨. 지급 내역은 DB/API의 시각을 유지하지만 Customer template이 `yyyy-MM-dd`만 표시함. `grant-row > div`의 가로 flex와 meta nowrap으로 수량/상태/기한의 시각적 구분 부족.
- API 원본 로컬 변경: `1788900000000-LocalizeCreditProductNames.ts` 추가 및 Admin datasource 등록. 기존 기본명과 code가 일치하는 3개 상품만 `추가 크레딧 400`, `추가 크레딧 1,000`, `추가 크레딧 4,000`으로 변경. 가격·수량·기한·맞춤이름·과거주문·원장 보존. down도 변경된 이름과 일치할 때만 원복.
- 검증: 새 migration 테스트와 datasource 등록 테스트 실패3건 확인 후 구현. `CATALOG_TEST_PG_SOCKET=<이번 작업 임시 소켓> node node_modules/jest/bin/jest.js --runInBand src/core/database/migrations/admin/1788900000000-LocalizeCreditProductNames.spec.ts src/core/database/admin.datasource.spec.ts src/core/database/migrations/admin/1788800000000-LocalizeBillingProductNames.spec.ts`: 3 suites/10 tests 통과. Node22.22.3 `node node_modules/@nestjs/cli/bin/nest.js build` 성공, `git diff --check` 통과.
- 검증 DB는 `/private/tmp/clipper-credit-name-test.eW0mOS`의 새 PostgreSQL15, Unix socket 전용/TCP 비활성, 임시 테이블 사용. 검증 후 서버 종료 완료. 기존 개발·운영 DB 접속/변경 없음.
- UI는 제품 소스 변경 없이 Superpowers 로컬 비교 화면 작성: A 항목별 열정렬(추천), B 잔액강조 카드, C 표. 각 안 KST 날짜·시각 및 모바일 배치. 미리보기 무료체험06:06은 예시이며, topup10:23은 paidAt+30일의 예상값. 실제 API 값 검증으로 혼동하지 않음.
- 현재 세션 미리보기: `/Users/jina/.codex/visualizations/2026/09/08/01a07e71-a9df-7c51-91bf-c8c90f1a0e1a/.superpowers/brainstorm/69270-1788831395/content/credit-grants-options-v2.html`. 서버 localhost:64602, 세션 URL은 같은 디렉터리 상위 `state/server-info` 확인. 다른 PC에서 실행 중이라고 가정하지 않음.
- 다음: 사용자의 UI안 선택 반영, 실제 Customer 코드에서 KST `yyyy-MM-dd HH:mm` 및 가독성 개선. 검증/선택커밋·푸시 후 사용자에게 m4-prod 배포와 migration을 한 단계씩 안내. 현재 API 변경 미커밋·미푸시·미배포. Infra 기존 문서5개와 .codex 기존 변경 보존.

## 2026-09-08 — 운영 구축/수정 배포 종료 및 다음 세션 인계

- 상세 기록: [현재 인수인계](./2026-09-08-production-pg-session-handoff.md), [운영 구축 이력](../../web/clipper_infra/runbooks/production-setup-history-20260908.md).
- 변경 저장소: Web API(회원조회 타입불일치/checkout 재진입/실패 안내·내역계약), Customer(환경/가격·추가크레딧 UI/결제내역·실패안내/my경로/기간종료시각), Admin(환경/조회오류/실패상세·회원정보), Infra(배포·migration 분리 및 운영문서).
- 의미: 소스 브랜치와 배포 환경을 분리하고, 운영 후보를 개발 DB와 별도 구축. 서버에서는 현재 checkout upstream을 ff-only로 갱신 후 직접 build. DB migration은 별도 승인 단계.
- 사용자 실행: m4-prod 앱3개, m2-db 운영3개, NPM/DNS/OAuth/Toss웹훅, 관리자seed 구성. 사용자 승인 테스트 DB재생성 완료 후 새회원/결제 확인.
- 최신 Customer06a3977: 현재 이용기간 종료와 KST 시·분, 다음 결제일·DB 계산 변경 없음. 운영 화면 사용자 확인 완료.
- 최근 검증: Dashboard32 tests, Customer전체240 및 prod빌드 성공. Infra deployment.test.mjs 24 tests, 문서5개 shell문법54블록/로컬링크14개 확인. 원격 서버명령을 실행한 문서검증이 아님.
- 이전 기능배포 검증: API2418통과/13skip, Admin370통과, Infra103통과 기록. 이번 문서화에서 전체를 다시 실행한 것은 아님.
- 미완료: PG나머지E2E, desktop/runner분리, 개발전환(현재보류), 운영안정성, 라이브전환. TASKS에 분리.
- 문서상태: Infra5개 미커밋; 이번 .codex 인수인계도 미커밋. 기존 .codex ahead25커밋/다른untracked 보존, 임의push금지.
- 다음 시작: [NEXT_SESSION_PROMPT](./NEXT_SESSION_PROMPT.md). 우선 추가크레딧 테스트 안내, 초기구축·DB삭제 재실행 금지.

## 과거 기록 — 2026-08 심사용 Checkout (당시 상태)

## Changed repositories

- `.codex`: 설계, 구현 계획, 작업 추적 문서
- `web/clipper_web_api`: 결제 도메인·영속성·Toss adapter·공개 API·callback·migration·설정
- `web/clipper_web_client`: 요금 페이지 결제 CTA·공개 결과/취소 화면·API client
- `web/clipper_infra`: dev/stage/prod Compose 환경변수 전달

## Meaningful changes

- 토스페이 심사용 checkout 설계와 구현 계획을 확정했다.
- `.codex`, `clipper_web_api`, `clipper_web_client`, `clipper_infra`를 `feat/toss-pay-review-checkout` 브랜치로 분리했다.
- 심사 설정이 유효한 dev에서만 비로그인 단건·정기결제 버튼을 표시하고, 비활성 환경은 기존 무통장 구매 요청 동선을 유지한다.
- 1·3개월은 단건/정기, 12개월은 단건만 서버와 UI 양쪽에서 허용한다.
- 단건결제 callback과 빌링키 활성화/최초 결제를 Toss Pay 상태 조회로 재검증하고, `TEST` 결과만 저장한다.
- 주문·결제 이벤트를 admin DB에 저장하는 migration과 repository를 추가하고, 조회 토큰은 hash, 빌링키는 암호문으로만 저장한다.
- 공개 완료 페이지는 2초 간격 최대 10회만 조회한다. 취소 페이지는 provider reconcile을 먼저 수행하고 브라우저 도착만으로 취소 처리하지 않는다.
- 최초 빌링 청구를 transaction-scoped advisory lock과 조건부 상태 전이로 직렬화하고, 불확실한 응답은 동일 주문번호 상태 조회로 복구한다.
- Nginx reverse proxy 한 홉 신뢰와 IP별 checkout/result rate limit를 적용했다.
- capability를 `checkout | local_notice | legacy_purchase`로 확장했다. 로컬 요금 페이지는 dev와 동일한 Toss 버튼을 표시하지만 클릭 시 API를 호출하지 않고 dev 테스트 안내를 표시한다.

## Verification

- Client baseline: `npm test -- --watch=false --browsers=ChromeHeadless` — 66/66 PASS.
- API baseline: `npm test -- --runInBand` — 500/501 PASS, 기존 날짜 고정 session fixture 1건 FAIL.
- API 결제 집중 테스트: `npm test -- --runInBand src/modules/payments src/core/config/trust-proxy.spec.ts` — 75/75 PASS.
- API 전체 테스트: `npm test -- --runInBand` — 578/579 PASS. 유일한 실패는 기준선과 동일한 날짜 고정 session fixture다.
- Client 전체 테스트: `npm test -- --watch=false --browsers=ChromeHeadless` — 82/82 PASS.
- API build: `npm run build` — PASS.
- Client production build: `npm run build` — PASS.
- OpenAPI YAML parse: `OPENAPI_OK`.
- dev/stage/prod Compose config: 모두 PASS. review mode는 각각 `true/false/false`이고 실제 키 대신 placeholder만 렌더링됐다.
- 공용 테스트 키 실제 문자열 전체 저장소 검색: 0건. Client의 `TOSS_PAY_API_KEY`, `sk_test_`, `sk_live_` 검색: 0건.
- 네 저장소 `git diff --check`: PASS. 모두 `feat/toss-pay-review-checkout` 브랜치다.
- 독립 코드 리뷰: Critical 0, Important 0, merge 준비 가능 판정.
- 실행 중인 로컬 API `GET /payments/review/config`: HTTP 200, `{ "mode": "local_notice" }` 확인.
- 실행 중인 로컬 `/pricing`: HTTP 200 및 headless 렌더링에서 1·3개월 정기/단건, 12개월 단건 버튼과 로컬 안내 문구 확인.

## Remaining risks

- 실제 토스페이 공용 테스트 키 checkout·callback은 dev 배포 후 수동 스모크 테스트가 필요하다.
- 기준선 API 실패는 토스페이 범위 밖의 기존 테스트 픽스처 문제다.
- 이번 범위에서는 결제 완료 후 이용권·크레딧 지급, 회원 연결, 반복 청구, 해지, 환불을 의도적으로 연결하지 않았다.
- API가 Toss callback 재시도 기간 내내 중단되면 자동 scheduler가 없으므로 해당 주문은 수동 상태 재검증이 필요할 수 있다.

## Deployment handoff

- `implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md`에 m2-stage 수동 배포 순서를 작성했다.
- 이 배포는 m2-stage의 API와 web client만 recreate하고, m2-proxy는 변경하지 않으며, m2-db의 DB container를 재시작하지 않는다.
- admin migration은 Compose one-off API container로 `clipper_admin_dev`를 먼저 확인한 뒤 적용하도록 정리했다.
- 현재 로컬 작업 환경에서 사설망 m2-stage/m2-proxy/m2-db SSH는 timeout이었다. 공개 dev web/API/admin URL은 모두 HTTP 200이고 API health의 user/release/admin DB는 모두 `ok`였다.

## Recurring review retry follow-up

- 최초 정기결제는 `billing_key_created → billing_activated → billing_paid`와 `paid`까지 성공했다.
- 후속 세 건은 Toss 직접 상태 조회에서 `FAIL`, `CANCEL`, `CANCEL`이었지만 실패 callback이 없어 로컬 `checkout_ready`로 남는 현상을 확인했다.
- 공용 테스트 상점에서 동일 결제수단을 반복 등록할 수 있도록 각 주문의 `orderNo`를 Toss `displayId`로 생성·상태 조회·callback 검증에 전달한다.
- receipt-token 재검증에서 빌링키 `CREATE`, `ACTIVE`, `CANCEL`, `FAIL`, `REMOVE`를 조회하고, 주문·빌링키 일치 검증 후 로컬 주문과 deduplicated event에 반영한다.
- `ACTIVE` 재검증은 기존 advisory lock 기반 최초 청구 경로를 재사용한다. 크레딧·이용권 지급은 추가하지 않았다.
- API 결제 모듈 테스트: 86/86 PASS.
- API build: PASS.
- API 전체 테스트: 590/591 PASS. 유일한 실패는 별도 브랜치로 분리한 기존 운영자 JWT 고정 날짜 fixture다.
- 후속 배포는 API 이미지 빌드와 API container recreate만 필요하다. migration, web client, web admin, infra, proxy, DB restart는 필요하지 않다.
