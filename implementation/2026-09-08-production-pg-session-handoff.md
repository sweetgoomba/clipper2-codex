# 2026-09-08 Clipper 운영 구축·PG 검증 세션 인수인계

> **후속 세션 종료 업데이트:** 현재 배포·테스트 완료/잔여는 [2026-09-08 종료 인수인계](./2026-09-08-production-pg-session-closeout.md)와 [TASKS](./TASKS.md)를 우선한다. 아래는 초기 운영 구축 시점 기록이다. Customer888c2b9/Adminfb3e532/API2710301까지 배포됐으며, 추가충전 기본 검증·해지재개·카드변경·월→연·환불1건이 진행됐다. 오래된 미배포/첫 추가충전 대기 표시는 현재 상태가 아니다.

작성일: 2026-09-08 KST. 다음 세션은 **이 문서부터** 읽는다.
목적: 긴 대화의 재탐색 없이 현재 상태·사용자 결정·남은 전체 작업을 복원한다.
이는 진행 상태 기록이며 서버 변경/DB 삭제/라이브 결제의 새 승인서가 아니다.

> 9/8 최신 진행: 추가크레딧400/5,900원 지급·잔액1,800 확인 후 상품명 한글화、C안 지급표·사용기한/KST·단일잔액·결제예정표기를 구현했다. Customer `6e951cd`/Admin `31ad799`/API `8195a35` 커밋·푸시 및 사용자 운영배포 완료. 전체 Customer243/Admin372/API2424 tests 통과(API10 skipped), 빌드·리뷰 확인. m4-prod 빌드→상품명 migration→앱 교체 후 실행 revision3개 일치, 내부 HTTP200/API DB3개 ok, 공개 HTTPS 카탈로그 한글명3개·기존 가격/수량/30일 기한 유지 확인. 다음은 고객 /my/credits C표·단일잔액·KST 사용기한, 고객/Admin 결제예정 실제 화면 확인이다. 서버명령은 계속 사용자가 직접 실행한다. 아래 Git표는 이전 인수인계 시점이며 최신 상태는 [WORKLOG](./WORKLOG.md) 첫 항목과 [TASKS](./TASKS.md)를 우선한다.

## 1. 한눈에 보는 현재 위치

> 추가 최신화: 지급표 열 간격 후속 수정으로 Customer 최종 커밋은 `e8462ca`다. 사용자 web 배포 후 실행 revision/running·공개 HTTPS health HTTP200 및 열 간격 실제 화면 사용자 확인 완료. Admin `31ad799`/API `8195a35` 유지. 다음은 추가크레딧400 지급건의 실제 KST 사용기한/현재잔액 확인 후 DB/Toss/중복지급 검증 재개다. 배포를 반복하지 않는다.

큰 목표는 **기존 개발 서비스와 내부 사용자 데이터를 보호하면서 PG가 통합된 운영 웹·API·DB·설치형 앱 배포 체계를 완성하고, 이후 개발 환경에도 검증된 변경을 반영하는 것**이다.

현재 완료한 지점:
- 별도 운영 웹/관리자/API/DB 구축과 운영 도메인 HTTPS 연결.
- 운영 Google 고객 로그인, 최고 관리자 생성·로그인.
- Toss 테스트키로 최초 월간 구독 결제·이용권 활성화 확인.
- 실제 테스트 중 발견한 회원 조회/checkout 재진입 오류 수정.
- 결제 실패 안내/고객 결제시도 내역/Admin 상세 표시와 /my 경로 정리.
- 마지막 작업: 마이페이지 '현재 이용기간 종료'에 한국 시간 시·분 표시, 운영 확인 완료.
- 팀원용 운영 문서 작성 완료. **Infra 문서 5개는 아직 미커밋·미푸시**.

아직 아닌 것:
- PG 전체 시나리오가 운영 환경에서 검증 완료된 것은 아니다.
- 운영 도메인이 열렸다고 라이브키/실청구로 전환한 것은 아니다.
- 운영 desktop 앱/runner/S3 다운로드·자동 업데이트 환경 분리는 완료되지 않았다.
- 개발 서버·개발 DB에 이번 PG 전환을 적용한 것은 아니다.
- 백업/복구/모니터링/부팅 자동 복구가 운영 준비 완료인 것은 아니다.

## 2. 상세 문서를 중복 작성하지 않고 연결

아래 Infra 문서는 바로 이전 작업에서 작성했다. 명령과 콘솔 필드는 여기를 읽는다.

| 용도 | 문서 |
| --- | --- |
| 서버 조사→최초 구축→수정 배포→DB 재생성→최종 검증 이력 | [구축·수정 이력](../../web/clipper_infra/runbooks/production-setup-history-20260908.md) |
| 팀원 반복 배포, migration, health, 이미지 확인, 수동 복구 | [운영 배포 매뉴얼](../../web/clipper_infra/runbooks/production-deployment-team-guide.md) |
| HostingKR·NPM·ipTIME·Google OAuth·Toss·DBeaver 설정 | [외부 관리 화면](../../web/clipper_infra/runbooks/production-console-settings.md) |
| 문서 진입점 — 옛 GHCR pull 안내 대체 | [deploy-prod.md](../../web/clipper_infra/runbooks/deploy-prod.md) |
| 별도 승인 시에만 DB 전체 삭제·재생성·최고 관리자 seed | [DB 재생성 절차](../../web/clipper_infra/runbooks/recreate-prod-databases.md) |

다음 작업별로 필요한 과거 근거:
- [9/3 통합 로그와 개발 데이터 전환 정책](../main/2026-09-03-toss-payments-pg-release-candidate-integration-log.md)
- [운영 앱 이름·아이콘·식별자 결정 대기](../main/2026-09-07-desktop-dev-prod-app-identity-decision-pending.md)
- [콜백/웹훅 및 runner 환경 분리 설계](../main/2026-09-07-toss-payments-pg-server-callback-webhook-design.md)
- [웹 배포 구현·검증 안내](../main/2026-09-07-web-dev-prod-local-build-deployment-guide.md)
- [초기 인프라 관찰값](../main/2026-09-07-toss-payments-pg-production-infrastructure-discovery-log.md)
- [문서 작성 규칙](../standards/DOCUMENTATION_POLICY.md)

**오래된 문서의 시점에 주의**:
9/3 문서의 '통합 미완료', 9/7 설계의 '운영 미구축/개발 우선 배포', /app 결과 URL, main/dev 브랜치 강제,
GHCR pull 절차를 현재 미완료 작업이나 배포 명령으로 되살리지 않는다.
과거 설계와 현재 사용자 결정이 충돌하면 이 문서와 최신 코드/사용자 확인을 우선한다.

## 3. 작업 정본과 로컬 Git 상태 — 세션 종료 시 관찰값

워크스페이스는 `/Users/jina/project/adlight`. 루트 하나가 전체 Git 저장소인 것이 아니라 하위 저장소별로 관리한다.
**작업 정본은 web/ 및 desktop/ 원본 저장소**다.
IDE에 열린 `.integration-clones/toss-payments-pg-20260903/...`는 초기 임시 복제본/보존본이다.
그곳에서 새 작업을 하거나 원본 변경을 덮어쓰거나 삭제하지 않는다.
기존 PG worktree도 승인 없이 수정·삭제하지 않는다.

| 로컬 저장소 | 현재 branch | HEAD | 상태 |
| --- | --- | --- | --- |
| web/clipper_web_client | integration/toss-payments-pg-20260903 | 06a3977 | clean, 로컬 upstream 표시에 차이 없음 |
| web/clipper_web_admin | 동일 | 71da3b9 | clean, 로컬 upstream 표시에 차이 없음 |
| web/clipper_web_api | 동일 | 9733be3 | clean, 로컬 upstream 표시에 차이 없음 |
| web/clipper_infra | 동일 | 088e520 | 아래 문서 5개 미커밋 |
| desktop/clipper_angular | 동일 | 7f34704b | clean, branch 출력에 upstream 없음 |
| desktop/clipper_nestjs | 동일 | 19c667e | clean, branch 출력에 upstream 없음 |
| desktop/clipper_electron | 동일 | dbf55c8 | clean, branch 출력에 upstream 없음 |
| desktop/clipper_python | merge/meme-overlay-into-dev | f8274ac | clean, 별도 작업 branch 유지 |
| .codex | main | 이 세션에서 HEAD 변경 안 함 | 시작 당시 origin/main보다 25 ahead, 아래 주의 |

이는 원격을 새로 fetch한 전 저장소 최신성 확인이 아니다. desktop 원격 푸시/빌드 가능 상태를 가정하지 않는다.
Python을 통합 브랜치로 자동 변경하지 않는다.

### Infra에 반드시 보존할 변경

수정:
- runbooks/deploy-prod.md
- runbooks/recreate-prod-databases.md

신규:
- runbooks/production-console-settings.md
- runbooks/production-deployment-team-guide.md
- runbooks/production-setup-history-20260908.md

앞선 문서화에서 앱 코드·서버·DB를 바꾸지 않았고 문서 커밋·푸시도 하지 않았다.
팀 공유를 위한 검토·선택 커밋·푸시는 후속 작업이다. `git add .`로 다른 변경까지 묶지 않는다.

### .codex 주의

기존 untracked:
`main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md`.
본 세션의 PG 문서로 취급하거나 삭제/함께 stage하지 않는다.
이번 인수인계에서 작성하는 문서와 TASKS/WORKLOG/다음 프롬프트도 미커밋이다.
이미 25개 ahead인 기존 커밋을 사용자 요청 없이 일괄 push하지 않는다.
다른 PC/새 worktree에서는 미커밋 문서가 없을 수 있다. 같은 로컬 작업 경로에서 시작하거나 승인된 방식으로 문서를 옮긴다.

## 4. 실제 배포 토폴로지와 서버 상태

| 장비 | 역할 | 주소/경로 |
| --- | --- | --- |
| m4-prod | 운영 웹3개, 직접 Docker build, API one-off migration/seed | 192.168.0.47; /Users/m4-prod/Documents/projects/clipperstudio |
| m2-db | 개발·운영 PostgreSQL | 192.168.0.7; /Users/metabuzz/Desktop/project/clipper2/clipper_infra |
| m2-proxy | NPM HTTPS 진입 | 192.168.0.2; 장비 브라우저 http://localhost:81/nginx/proxy |
| m2-stage | 기존 개발 웹3개 | 192.168.0.23 |
| storage | 기존 Windows 개발 runner PC | 운영 runner 미구축 |

- 운영 앱 project: clipper-prod.
- Customer clipper-web-client-prod: 192.168.0.47:42202 → 80.
- Admin clipper-web-admin-prod: 192.168.0.47:42302 → 80.
- API clipper-web-api-prod: 192.168.0.47:43202 → 43202.
- 운영 DB project: clipper-db-prod.
- User clipper_user_prod:55202 / Admin clipper_admin_prod:55212 / Release clipper_release_prod:55222.
- 운영 DB 사용자 이름: clipper_user_prod_user / clipper_admin_prod_user / clipper_release_prod_user.
- dev DB 포트55203/55213/55223, 기존 데이터·컨테이너 유지.
- 운영 환경파일: m4-prod infra/env/stack.prod.env; m2-db infra/env/db.prod.env.
- 운영 secret: m4-prod의 /Users/m4-prod/Documents/projects/clipperstudio/.secrets/web-api-prod.
- m4-prod Node는 Homebrew22.23.1, Docker ARM64/약7.75GiB/10CPU 관찰.
- monitor는 m4-prod에서 기존 dev 대상 감시. 운영 대상 추가 완료 아님.

### 외부 관리 화면

- DNS: HostingKR 관리. apex A는 당시112.169.113.138, www CNAME apex.
- admin/api CNAME은 최종적으로 metabuzz.iptime.org. 개발 레코드 유지.
- ipTIME 기존80/443→192.168.0.2 NPM 유지. DB 외부접속용55202/55212/55222 매핑 추가 흐름 뒤 DBeaver연결 완료 보고.
- NPM에서 운영 도메인을 각 m4-prod 포트로 연결. HTTPS4개 health200/TLS0, 브라우저 경고 없음 확인.
- 운영 Google OAuth 구성 후 로그인 성공. 프로젝트ID/최종게시상태/NPM토글/공유기추가후캡처는 미확인으로 기록.
- 운영 Toss키는 m2-stage에서 가져온4개 테스트키. test_ 접두사와 preflight 통과.
- 운영 웹훅명 clipper-prod-test-webhook, URL https://api.clipperstudio.ai/payments/tosspayments/webhook.
- 선택 이벤트 BILLING_DELETED, DEPOSIT_CALLBACK, PAYMENT_STATUS_CHANGED.
- 기존 로컬 ngrok webhook도 목록에 있었음. 제거 여부/실제운영웹훅전달검증은 미확인.
- Google callback: https://api.clipperstudio.ai/auth/google/callback.
- WEB_BASE_URL=https://clipperstudio.ai, TOSS_PAYMENTS_RETURN_BASE_URL=https://api.clipperstudio.ai.
- 운영 Admin https://admin.clipperstudio.ai, 고객 마이페이지 https://clipperstudio.ai/my.

콘솔 상세는 별도 문서에서 **입력 기준**과 **최종 저장값 확인 여부**를 구분한다.
보안 토글을 추정한 값으로 자동 덮어쓰지 않는다.

## 5. 이번 세션의 구현·배포 요약

| 묶음 | 한 일 | 영향 |
| --- | --- | --- |
| 공통 배포 | deploy-dev/prod 선택어 통일, build-only/start-only, 별도 migrate-db | 현재 checkout/upstream으로 실행, DB 자동변경 없음 |
| 프런트 환경 | local/dev/prod와 environment 파일 명확화 | 운영 API/개발 API 분리, npm start4201/4202 유지 |
| 회원조회 오류 | varchar=uuid 비교 수정 + Admin 오류/재시도 UI | 운영 회원목록500 해결 |
| 상품/가격 UI | 요금제카드 정보순서·간격, 추가크레딧카드/기한·구매안내 | 사용자 로컬 검토 후 운영반영 |
| 상품명 | Basic Monthly 등을 한글화하는 migration | 기존 주문 snapshot과 카탈로그 구분 |
| checkout 중단/재진입 | 미완료 시도의 긴 차단 해소, 최종 확인단계 생성, 안전한 재시도 | 카드등록창 이탈 후 재시도 허용 |
| 실패·결제내역 | 안전한 failure code 문구, 고객 결제시도 카드, Admin 펼침 상세·회원정보 | 실패사유/지급대상아님 등 표시 |
| 경로 | /app 및 하위 사용경로 → /my | 호환 alias 없음, API redirect도 반영 |
| 날짜 표시 | 이용권 만료 → 현재 이용기간 종료, KST yyyy-MM-dd HH:mm | DB 기간/다음결제일 계산 변경 없음 |

초기 장기차단 재현 오류: SUBSCRIPTION_IN_PROGRESS.
최초 실패 테스트 저장코드: NOT_SUPPORTED_CARD_TYPE.
결제금액 예시: Basic 월간5,900원, test키로 지급완료. 실제카드정보를 썼어도 라이브실청구로 기록하지 않는다.

### DB 전체 재생성은 이미 끝난 과거 작업

사용자 승인으로 테스트 운영DB3개와 각 볼륨을 백업 없이 삭제했다.
이후 빈 DB3개 재생성 → API 이미지의 User/Admin/Release migration → 최고관리자seed → 앱3개재시작 → health/로그인/새결제 확인까지 마쳤다.
현재 DB는 빈 상태가 아니다. 새 회원과 구독 테스트 데이터가 존재한다.

- 기존 개발 DB는 삭제하지 않았다.
- 운영 JWT/env, NPM/DNS/OAuth/Toss URL, 이미지/monitor는 유지.
- Toss상점의 외부결제/빌링키/S3파일은 DB삭제로 없어지지 않았다.
- reset-prod-test-payments.sql 및 관련 코드/스크립트는 폐기했다. 복원하거나 실행하지 않는다.
- 최고관리자 재생성 로그: created operator: superadmin@gmail.com (role super-admin).
- 임시 env/operator-seed.prod.env는 사용자 삭제 완료.
- 이 한 번의 승인으로 향후 운영DB를 다시 초기화하지 않는다.

## 6. 전체 남은 작업 지도

| ID | 작업 | 상태 | 다음에 할 일 / 완료 판단 |
| --- | --- | --- | --- |
| A | 운영 기반 웹·API·DB·HTTPS | 완료, 후속 운영점검 남음 | 초기구축 재실행 금지; 변경 시 health/기능검증 |
| B | Google 고객/최고관리자 로그인 | 기본검증 완료 | 일반사용자 공개 전 OAuth게시·검증상태/계정관리 확인 |
| C | 최초 구독/실패·재시도 | 테스트키 기본검증 완료 | 전체PG검증 완료로 확대 해석하지 않음 |
| D | 추가크레딧 구매 | 운영 E2E 미완료 | 활성구독으로 구매, 정확한지급수량/기한/내역/중복방지 확인 |
| E | 구독 변경 | 운영 E2E 미완료 | 즉시상향/차액, 예약하향, 월→연, 금지조합, 실패 시 기존권한 유지 |
| F | 해지/재개/카드변경 | 운영 E2E 미완료 | 다음청구중단과 현재권한 유지, 재개와 카드연결 결과 |
| G | 환불 | 운영 E2E 미완료 | 월/연/추가크레딧/상향 환불정책, 크레딧사용 여부, 취소·회수·상태일치 |
| H | 갱신·비동기처리 | 운영 E2E 미완료 | 다음회차·실패재시도·유예/만료, worker실행·복구 검증 |
| I | 웹훅·가상계좌 | 등록만 확인, E2E 미완료 | 실제전달/중복/재시도/옛ngrok; 가상계좌 제공 시 입금대기·입금·만료 |
| J | desktop 운영앱 환경 분리 | 설계/결정 대기 | API/JWT/로그인/업데이트/데이터/캐시/모델/포트 일관성 |
| K | 운영 runner·S3·Release·다운로드 | 미구축/미검증 | dev와 독립컨테이너·포트·작업/env/output, 운영Admin→runner→S3→운영Customer→앱 |
| L | 개발 환경 전환 | 현재 보류 | 복제DB검증·내부사용자조율 후 별도 승인, 서버/DB/desktop 연계반영 |
| M | 운영 보안·지속운영 | 미완료/팀결정대기 | 백업/복원, 모니터Slack, 재부팅복구, DB외부접근, OAuth/PG로그·키관리 |
| N | 라이브·정식공개 | 미전환 | 계약/심사/live키·MID/OAuth상태, 승인된 소액실결제·취소, 테스트데이터정책 |
| O | 브랜치 통합·팀공유·문서 | 일부 미완료 | 문서검토/푸시, desktop원격상태, 최종통합대상/PR·배포기록 확인 |

### D~I: 다음에 권장한 작업 순서

1. 추가크레딧 구매 테스트.
2. 구독 변경/해지/카드변경/환불을 케이스별 확인.
3. 웹훅/갱신/실패복구와 필요 시 가상계좌.
4. 운영desktop/runner, 개발전환, 운영안정성은 사용자 우선순위에 따라 병행 계획.
5. 라이브 전환은 마지막 별도 승인.

각 케이스는 **기대결과·환경/키 확인 → 사용자 조작 → UI/Network/DB·Toss 결과 대조 → 증거기록**.
실패하면 먼저 진단하고 수정 요청/승인 범위에서 구현한다.
운영 DB 시간을 무작정 과거로 바꾸거나 청구 endpoint를 호출해서 갱신을 강제하지 않는다.
결제시도 API가 성공해도 웹훅 전달 완료를 증명하는 것은 아니다.

### J~K: desktop/runner의 중요 결정

기존 개발판은 개발팀과 다른 팀이 동일 PC/Mac에서 사용·QA 중이다.
최대한 기존 앱을 변경하지 않고 별도 운영 앱을 공존시키는 방향이다.

기존 개발판:
productName Clipper Studio / appId ai.clipperstudio.desktop / protocol clipper:// /
기본 userData Clipper Studio.
운영 이름 Clipper 또는 Clipper Studio, 기존 아이콘 사용 여부는 결정권자 답변 대기.
ai.clipperstudio.app, clipperstudio://, 별도 데이터 경로 등은 **후보**, 확정 아님.
과거 제안했던 개발데이터 전부이전 스크립트나 clipper-dev:// 전환은 현재 실행안이 아니다.

분리할 항목:
- 앱/설치·실행파일·바로가기 식별값, userData·Keychain·로그·세션·캐시·모델.
- API base URL, JWT공개키, 로그인 protocol, 업데이트 조회/캐시.
- runner컨테이너/호스트포트/작업·출력폴더/env와권한/S3 prefix/Release DB.
- 두앱 동시실행의 로컬API/플러그인 포트와 프로세스종료 범위.
- Hugging Face cache는 실제 모델파일을 포함한다. 공용 캐시를 무단이동/삭제하지 않는다.
- Windows/Mac 설치·실행·로그인·업데이트·삭제 시 상대앱 영향 없음 검증.

Admin sourceBranch는 코드선택일 뿐 환경선택이 아니다.
5개 snapshot대상은 당시 설계상 clipper_angular/nestjs/python/electron/web_api.
운영Admin에서 dev를 선택한다고 무조건 개발API/운영API가 자동결정되는 구조가 아니다.
별도의 환경주입 구현과 산출물검증을 끝내기 전 운영용 설치파일을 배포가능하다고 하지 않는다.
기존 storage runner의 dev/prod 이름 변경도 사용자/사용팀 영향 확인 없이 하지 않는다.

### L: 개발 서버·DB에 추후 해야 하는 일

최신 사용자 결정: **개발쪽은 아직 아무것도 하지 않는다.**
운영 테스트 준비를 위해 m2-db의 Infra checkout은 전환했지만 dev 컨테이너/데이터를 migration한 것은 아니다.

9/4 승인된 개발 데이터 정책은 별도 근거를 읽고 유지한다:
- 보존: 기존 사용자 계정과 로그인 관련 데이터.
- 초기화 대상: 옛 요금제/구매신청/이용권/크레딧/유효기간/옛장부, 과거 operation_runs 및 연결 복구기록.
- 현재 작업정책 6개만 유지; 폐기된 작업정책 제거.
- 기존 사용자에게 무료체험/이용권/크레딧을 소급 자동지급하지 않음.
- 신규 사용자만 정상가입 흐름 무료체험; 기존 사용자 새권한은 정상PG결제로 취득.
- 폐기 가능한 복제DB에서 보존/삭제/외래키/신규schema/동작을 검증하고 결과 승인 후 실제개발적용.
- 실제개발적용 직전 백업/복구 및 내부사용자 공지·점검시간을 조율. 현재는 개발DB백업도 실행하지 않기로 했던 상태.

이는 옛크레딧을 그대로 새PG로 변환·승계하라는 요구가 아니다.
운영의 'DB3개 전부삭제'를 개발에 적용하면 사용자/로그인 보존을 깨므로 금지.
이후 dev웹/API의 local/dev/prod 설정·배포스크립트, PG환경/웹훅, desktop소스·runner와서버의 호환성도 함께검증해야 한다.
운영에서 수정한 코드가 integration에 있다는 것과 dev branch/개발서버에 반영됐다는 것은 다르다.

### M~N: 팀 결정과 최종 공개 전 확인

- monitor현재dev대상 → 운영대상추가/알림발송 확인.
- 운영DB백업주기·보존·외부위치·복원리허설은 팀회의 이후 결정하기로 보류.
- m4-prod autorestart0/자동로그인미설정, Docker자동시작불명. 재부팅복구 보장 안 됨.
- 방화벽Off/FileVaultOff 관찰. 편의상 설정을 임의로 바꾸거나 자동로그인을 강제하지 않음.
- DB외부포워딩 접근범위/SSL·VPN·SSH대안 검토.
- Google지원메일/프로젝트소유자/게시상태, NPMSSL·로그정책, 비밀회전·권한인계 정리.
- Test/live키 및 Widget/Billing MID매핑 검증; 개발과 공유한 테스트상점 분리 여부 확인.
- 라이브 실제금전거래는 계정/금액/시간/취소조건 정한 별도승인 이후.
- 공개 후 장애대응/rollback·로그·알림 담당 정하기.

## 7. 테스트 증거와 한계

이번 세션의 이전 기능배포 시 검증 기록:
- API 2,418 passed / 13 skipped, 229 suites passed / 3 skipped 및 build.
- Admin 370 tests 및 build; 기존 initial bundle 크기 경고 존재.
- Customer 240 tests.
- Infra 전체 103 tests 기록(실제웹환경빌드 포함).
위 수치는 이전 실행 기록이며 모든 것을 이번 인수인계 작성 때 재실행한 것이 아니다.

마지막 문구수정에서 실제 실행:
- `npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/features/portal/dashboard/dashboard.component.spec.ts`: 실패 재현2개 → 수정 후32통과.
- Customer 전체240통과.
- `npm run build -- --configuration prod`: 성공.
- 최초에 폐기된 deployment-prod 설정명으로 실행한 빌드는 설정없음 실패; 올바른 prod로 재실행 성공. 코드회귀가 아님.
- 문서작성 때 `node --test scripts/deployment.test.mjs`:24통과.
- 운영문서5개: shell block54개 bash문법, 로컬링크14개 존재 확인. 서버명령을 실행한 검증이 아님.

운영 실증은 사용자 제공 출력/브라우저 보고 기반이다.
다음 세션에서 전체DB/서버가 아직 같은 상태인지 필요 범위만 read-only로 확인한다.

## 8. 다음 세션 첫 작업과 안전 경계

1. 이 문서, TASKS, Infra문서진입점과 필요한 세부문서를 읽는다.
2. 각 원본repo git status/branch/HEAD와 위 미커밋문서를 확인한다.
3. 전체를 재구축하지 말고 완료/보류/이번에할일을 짧게 정리한다.
4. 우선 후보는 **활성 구독 계정의 추가크레딧 구매 테스트**. 사용자가 다른 우선순위를 주면 그에 따른다.
5. 사용자에게 현재 코드의 구매전제와 기대수량/기한·확인위치를 설명하고 한 단계씩 진행한다.
6. 미커밋Infra문서의 팀공유 필요성도 알려주되 기존 .codex ahead커밋을 무단push하지 않는다.

서버 조작은 지금까지처럼 사용자가 지정 장비에서 명령을 직접 실행하고 결과를 공유한다.
무단 SSH/원격DB접속/계정설정 변경을 가정하지 않는다.
안내는 장비명과 절대경로, 해당 명령의 영향과 기대결과를 함께 제공한다.
vi를 사용한다. 비밀값은 출력하지 않는다.
운영DB재삭제/개발migration/라이브결제/desktop식별자변경은 별도승인 없이 하지 않는다.
UI 수정은 필요하면 로컬4201에서 확인 후 승인받아 검증·선택커밋·푸시·사용자서버배포로 진행한다.
현재 로컬preview가 실행 중이라고 가정하지 않는다.

## 9. 새 세션 시작 문구

[NEXT_SESSION_PROMPT.md](./NEXT_SESSION_PROMPT.md)를 그대로 사용한다.
새 세션/다른 PC는 이전 대화를 자동으로 모두 알고 있다고 가정하지 않고 문서 경로를 명시한다.
