# 요금제 변경 예약 취소 확인·회원 연결 결제 이동 — 2026-09-10

현재 상태: **두 수정의 구현·커밋·push·운영 배포·사용자 운영 화면 확인 완료**. Admin cd3a306·Customer4d95a96으로 m4-prod HTTP200/running/restarts0/revision/WEB_DEPLOY_OK 확인 후 사용자 `둘다 잘 되는거 확인했어`로 예약 취소 확인창과 연결 결제 이동까지 확인했다. 예외/동시성 전체 검증으로 확대하지 않는다. 전체 현재 상태는 [9/10 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)를 우선한다.

## 수정 범위와 원인

1. Customer 마이페이지의 변경 예약 취소
   - `DashboardComponent.cancelScheduledPlanChange`가 확인 없이 API를 직접 호출하던 것이 원인.
   - 기존 `ConfirmDialogComponent`를 재사용. 제목 `요금제 변경 예약을 취소할까요?`, 취소할 예약/유지할 현재 요금제, 이용권·크레딧 유지와 자동 결제 중단 상태 유지 안내를 표시한다. 버튼은 `예약 유지` / `예약 취소`.
   - 확인 결과가 정확히 true일 때만 기존 API를 실행. 확인창 열림부터 요청 완료까지 pending으로 중복 클릭 차단. 취소/닫기/예약 없음은 API 미호출, 요청 실패 시 기존 예약 유지 및 기존 오류 안내, pending 해제.
   - 새로운 공용 UI 패키지나 별도 확인창을 추가하지 않았다. 기존 결제/구독 API 계약과 상태 갱신 경로를 사용한다.
2. Admin 회원상세 크레딧 지급 건의 연결 결제
   - `<base href="/">`에서 경로 없는 `href="#payment-…"`가 사이트 루트로 해석되고 대시보드로 이동하던 것이 원인. 대상 결제 행 ID 자체는 이미 존재했다.
   - 회원 ID를 포함한 RouterLink와 fragment로 변경: `/members/<회원 ID>#payment-<결제 ID>`.
   - 현재 회원상세의 paymentRows만 조회하여 해당 행으로 스크롤·포커스, 기존 활성 색상 토큰으로 행 강조. fragment와 렌더된 행을 감시하므로 직접 주소 진입/새로고침 후 데이터가 늦게 도착해도 이동한다.
   - 동일 fragment를 다시 클릭하면 Router 변경 이벤트가 없으므로 해당 경우도 행 이동을 처리. Ctrl/Meta/Shift/Alt 클릭 등 브라우저 새 탭 동작은 가로채지 않는다. 전역 라우터 스크롤 설정은 변경하지 않았다.

## 검증

- 최초 실제 RED: Customer 새 회귀 4개 실패/47개 성공(확인 전·닫기에도 취소 요청), Admin 새 회귀 2개 실패/31개 성공(루트 fragment 링크/포커스 없음). 처음 sandbox Karma 포트 바인딩 EPERM은 테스트 실행 전 제한으로 구분하고 로컬 실행 권한으로 재실행했다.
- GREEN: Customer Dashboard51, Admin MemberDetail33 통과. 같은 링크 재클릭 회귀를 추가하여 Admin1실패 재현 후 보완했다.
- 최종 전체 **Customer285·Admin424 통과**, 두 prod 빌드 통과. 최종 행 강조 스타일 보완 후 Admin prod 빌드 재확인. Admin initial576.57kB로 기존 500kB warning 유지, hard error budget 이내.
- 로그 `/private/tmp/clipper-confirm-payment-link-{red,green,repeat-red,final}-{client,admin}-test.log`, 최종 빌드 `/private/tmp/clipper-confirm-payment-link-final-{client,admin}-build.log`, 결과 JSON `/private/tmp/clipper-confirm-payment-link-final-results.json`.
- CUA 실제 브라우저: Customer 버튼 클릭→공통 확인창 표시→예약 유지/ESC 시 Basic 예약 유지→예약 취소 확정 후 예약 제거 및 성공 문구. Admin 연결 결제 클릭 시 회원상세 URL 유지와 정확한 결제 fragment, 대상 행 스크롤·포커스 확인. 해당 주소 새로고침 후에도 같은 행 포커스·파란 강조 표시 확인.
- UI 검증은 `/private/tmp/clipper-confirm-link-smoke-scq67wte/{admin,client}`의 실제 소스 복사본과 mock fixture로 실행. 운영 API로 연결하지 않도록 mock 외 요청을 오류로 차단. 운영 결제/예약/DB/키 변경 없음. 검증 탭과 포트59342/59343 서버 종료 완료.
- 최종 두 repo `git diff --check` 통과. 원본 Admin/Customer HEAD·status·diff SHA256이 시작 시점과 동일함을 확인하여 공유 미커밋 변경 보존.

## 위치·남은 적용

- Admin: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn/clipper_web_admin`, HEAD `cd3a3069310bdae13f123615e1a1a2a8972187cd` (base `87c4424d050d3a6f2acf50c8692c2d2ef2a464cf`). 회원상세 ts/html/scss/spec 4파일 커밋.
- Customer: 같은 경로의 `clipper_web_client`, HEAD `4d95a963cde6f4e4067244c6cc8c148bb66709ce` (base `9fff91a475c5ef61fd8a6ee121d090fb3aca07b6`). dashboard ts/spec 2파일 커밋.
- 기존 GitHub 대상 Admin `release/pg-expiry-20260910`, Customer `integration/toss-payments-pg-20260903`에 일반 push·원격 SHA 대조 완료. m4-prod 웹 두 이미지 빌드·revision 대조·운영 교체 및 health 확인도 사용자 제공 출력으로 완료. API/DB migration/앱 빌드 불필요.
- 배포 후 고객 변경 예약 취소의 유지/닫기/확정 및 관리자 실제 결제 링크를 확인한다. 이번 로컬 mock 검증을 운영 실행 완료로 확대하지 않는다.
- 이전 Electron/Angular CPU·Clipper 브랜딩 소스 push 및 새 설치 파일 빌드 대기는 유지. **Build 5 전체 QA·플러그인 실행 HOLD**, 남은 TEST PG 환불 검증 유지.

## 배포 준비 후 자동 승인 검토 차단·해결 이력

- GitHub 원격 브랜치를 읽기 전용으로 확인해 위 base SHA와 일치함을 확인. 검증한 smoke 소스와 6파일이 동일하고 새 코드 변경이 없어 이미 통과한 전체 테스트를 반복하지 않았다. 정확히 해당 파일만 커밋했고 두 격리 checkout은 clean.
- 일반 push가 실행 전에 거절됨. 원본 저장소의 기존 origin URL과 과거 운영 배포 브랜치를 추가 대조한 뒤 Admin 커밋 1개를 명시해 재시도했으나 다시 실행 전 거절됨. 두 저장소 모두 푸시되지 않았다.
- 검토 사유: 기존 프로젝트와 원격이 일치해도 해당 외부 GitHub 목적지로 소스 커밋을 전송한다는 명시적 사용자 승인이 필요함. 대상은 `https://github.com/OhMyMetabuzz/clipper_web_admin.git` 및 `https://github.com/OhMyMetabuzz/clipper_web_client.git`. 해당 주소로 푸시 승인 후에만 재시도.
- 커밋 manifest `/private/tmp/clipper-reservation-link-deployment-commits.json`; m4-prod 명령 `/private/tmp/clipper-reservation-link-prod-deploy.sh` 준비 및 `bash -n` 통과. 명령은 아직 실행하지 않았고 사용자에게 실행 지시도 하지 않음. 푸시·원격 확인 이후 서버 배포 진행.
- 커밋 후 원본 Admin/Customer 브랜치·HEAD·status·diff SHA256이 시작 시점과 동일함을 다시 확인. 공유 미커밋 변경 보존.

## 명시적 승인 후 푸시 완료

- 사용자가 두 기존 GitHub 목적지로 수정 커밋을 푸시하는 질문에 `승인함`으로 응답했다. 이후 두 push 실행이 허용됐고 기존 브랜치로 각각 1커밋 fast-forward 전송 완료. force push 없음.
- `git ls-remote --heads`로 Admin `cd3a3069310bdae13f123615e1a1a2a8972187cd` / Customer `4d95a963cde6f4e4067244c6cc8c148bb66709ce`가 각 배포 브랜치와 일치함을 확인했다.
- 푸시 후에도 원본 공유 checkout의 브랜치·HEAD·status·diff SHA256 보존 확인. 배포 스크립트는 두 새 SHA가 정확함과 `bash -n` 통과를 재확인했다.
- m4-prod에서 사용자가 실행할 Admin/Customer build-only → 이미지 SHA 대조 → 순차 start-only → HTTP200/running/restarts0/실행 revision 확인 명령을 전달한다. 아직 운영 서버 실행 결과를 받지 않았으므로 운영 배포 완료로 표시하지 않는다.

## m4-prod 운영 배포 완료 — 사용자 실행 결과

- Admin 이미지 및 실행 컨테이너 `clipper-web-admin-prod`: `cd3a3069310bdae13f123615e1a1a2a8972187cd`, HTTP200, running, restarts0.
- Customer 이미지 및 실행 컨테이너 `clipper-web-client-prod`: `4d95a963cde6f4e4067244c6cc8c148bb66709ce`, HTTP200, running, restarts0.
- 두 build-only와 순차 start-only 완료, 마지막 `WEB_DEPLOY_OK`. DB migration 미실행 메시지 확인. 서버에 직접 접속해 조회한 결과가 아니라 사용자가 제공한 실행 출력이다.
- 남은 운영 화면 확인: 고객 `/my`에서 변경 예약 취소 클릭 시 확인창이 먼저 표시되고 `예약 유지` 또는 Escape로 닫으면 예약이 유지되는지 확인. 실제 취소할 TEST 예약에서만 `예약 취소` 확정 후 반영 확인. 관리자 `/members/<회원 ID>`의 크레딧 지급 건 → 연결 결제 클릭 시 같은 회원상세의 해당 결제 행으로 이동·강조되는지 확인.
- 공유 변경 보존, Build5 QA·플러그인 HOLD 및 이전 앱 빌드 대기 상태 유지. 위 서버 배포 대기 표기는 이 후속 결과 이전 이력이다.

## 운영 화면 확인 완료

사용자가 `둘다 잘 되는거 확인했어`라고 응답했다. 직전 안내한 고객 예약 취소 확인창·예약 유지/확정 동작과 관리자 회원상세 연결 결제 행 이동의 실제 동작 확인으로 기록한다. 완료 작업 재실행 불필요. 이후 CPU 표시·대시보드 전체 점검은 별도 [감사/후속 문서](./2026-09-10-current-state-and-resource-dashboard-audit.md)에서 추적한다.
