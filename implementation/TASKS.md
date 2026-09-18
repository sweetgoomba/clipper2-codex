# Clipper 운영 구축·PG 전환 Tasks
전체 작업의 현재 상태와 재개 위치는 [작업 현황판](../handoff/WORKBOARD.md)을 따른다. 이 파일은 PG·리소스의 상세 증거/체크리스트이며 전체 프로젝트 우선순위표가 아니다.

## 2026-09-18 PG 통합 종료 감사

[정식 PG 통합 종료 감사와 남은 작업](./2026-09-18-pg-integration-closeout-and-remaining-work.md)을 최신 정본으로 사용한다.

- [x] 8repo 통합 결과의 원격 `dev` 포함 여부 확인.
- [x] 개발 DB Gate A–G, 보존 hash, migration/no-op, 기존 사용자 비소급, 신규 Trial/400 정책 확인.
- [x] 독립 개발판 identity·Mac 로그인/session·필수 템플릿 이관 확인.
- [x] Windows Build54 `0.0.35` 게시, 공개 다운로드와 dev update feed 확인.
- [ ] Windows 0.0.35 실제 설치·로그인·운영판 공존·업데이트 실기.
- [ ] 전환된 개발환경의 실제 카드 결제/webhook/환불 핵심 E2E.
- [ ] 실제 유료 operation 차감·환급 E2E와 30–60분 로그 관찰.
- [ ] macOS 공개 배포가 필요할 때 서명·공증·설치 검증. 자동 업데이트는 승인 전까지 HOLD.
- [ ] Release 생성 폼 입력값 초기화 UX 보완과 0.0.34 폐기 상태 확인.

## 2026-09-18 설치형 유료 작업 진행 차단

- [x] 과금 확인창 전후 비동기 대기 중 전체 화면 스피너와 입력 차단을 공용 UI로 구현하고, 확인된 여섯 유료 작업 진입점에 적용했다. 설계와 계획은 각각 `../design/2026-09-18-billable-operation-blocking-progress-design.md`, `../plans/2026-09-18-billable-operation-blocking-progress.md`를 따른다. 과금 확인창이 열려 있는 동안에는 차단 UI를 숨기며, 취소·오류 시 즉시 복구한다.

최신 운영 상태(2026-09-15): [카드사 심사용 운영 전환·복원 런북](./2026-09-15-pg-review-production-cutover-and-rollback.md), [실행 명령 부록](./2026-09-15-pg-review-production-cutover-commands.md). 운영 도메인은 개발 기준 심사 Client/Admin/API와 m4-prod의 별도 복사 DB로 전환됨. 사용자 단건·정기결제 및 주소 유지·로고 수정 확인. 기존 운영 컨테이너/DB/이미지 태그 보존. 웹훅 수신은 심사 버전에 없음. 복원은 미실행. 사용자 PC 원본8repo는 후속 요청으로 최신 dev로 전환했고 로컬 API·설치형 앱 정상 실행 보고. 이 상태가 아래 과거 상태보다 우선함.

최신 integration 진행(2026-09-15): [8개 저장소 반영 결과](./2026-09-15-main-integration-result.md). 별도 공통 integration에 운영+dev+보관 개선을 조합하고 충돌 해결/stage 완료. 후속 사용자 승인으로 7repo merge commit 및 8repo 원격 SHA 확인 완료, Client 추가 변경0. 원본 보존. 테스트·빌드·배포 미실행, Build5/실제 ML HOLD 유지.

**현재 정본(2026-09-10 문서 정리 후속):** [문서·Build7 증거·SDK/venv 조건 정리](./2026-09-10-documentation-source-reconciliation.md), [R5 후속](./2026-09-10-windows-owned-process-tree-followup.md), [R1~R4 안전성 후속](./2026-09-10-plugin-resource-safety-followup.md)을 우선한다. CPU·R1~R4·기본 RAM watchdog·조건부 정리 UI·R5는 구현과 각 후속에 명시한 격리검증까지 완료했으며, **당시 미커밋이던 네 저장소50파일은 이후 recovery/integration 브랜치에 커밋·푸시해 보존했다. 실제ML/Windows 검증은 별도 보류**다. 실제 Windows·ML 실행 검증 및 Build5 전체 QA는 보류다. PG·웹 배포/운영 확인은 [전체 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)를 유지한다. 기존 공유 원본 M은 배포 누락을 의미하지 않으며 Infra 문서5개/로컬 compose는 별도 보존한다. 아래 날짜별 기록과 ‘최신’ 표현은 당시 이력이다.

## CPU·플러그인 리소스 후속 — 현재 단계

- [x] 기존 Git·배포 상태 감사 및 공유 변경 보존 대조 완료. 최신 원본8repo/원격8repo 대조 결과는 R5 후속에 보관. 이번 문서 정리에서 원격/운영 상태를 새로 조회한 것은 아님.
- [x] Admin cd3a306 / Customer 4d95a96 배포 및 예약 취소 확인창·연결 결제 이동 사용자 확인 완료.
- [x] CPU `사용률 / 물리 코어·스레드` 구현·기존 격리검증·패치 보관 완료. 현재 설치0.0.3.7의 기존 CPU 사용률 표시 확인과 새 코드 반영은 구분.
- [x] R1~R3 실행 소유권·취소 격리·안전한 조건부 종료 구현·격리검증 완료.
- [x] R4 공통 admission·정리 후 가용량 재측정, 기본 RAM pressure watchdog 구현·격리검증 완료.
- [x] 조건부 idle 정리·작업 보호·조회 오류·갱신 중첩 방지·정리 결과·가용 RAM·빈 상태 UI 구현·격리검증 완료.
- [x] R5 Windows 소유 Job Object·종료 확인·실패 시 소유권/포트 보존·재시작 차단 구현·격리검증 완료. 실제 Windows API 실행 통과를 의미하지 않음.
- [x] 누적 [4repo/50파일 패치](./patches/2026-09-10-windows-owned-process-tree/README.md) 보관 및 clean 기준 복구 대조 완료. CPU7/안전성37/R5포함50은 누적본이며 중복 적용 금지. 기존 보관본은 보존.
- [x] 이번 문서 정리: 최신 완료·보류 상태 반영, 기존 Build7 증거의 확보/미확보 구분, snapshot·SDK/venv 갱신 조건 문서화. 새 테스트·빌드 없음.
- [ ] Build7 source snapshot·저장소별 SHA·설치 파일 해시/서명·정식 지정 대조. 로컬 기록에는 설치0.0.3.7·CPU 표시 증거만 있고 직접 연결 자료는 미확보. Build5 증거 재사용 금지.
- [ ] 새 CPU의 실제 Windows CIM 및 R5 Job Object·uv 제어 stdin·자손 종료·설치본 확인. 실제 ML 플러그인 실행 HOLD 유지.
- [ ] 작업별 증분 RAM/VRAM 예산·GPU telemetry 신선도·무응답 작업 정책·종료 실패 상세 UI 및 넓은 실기 검증.
- [ ] 후속 검증: 누적 변경 커밋·push는 완료. 새 source snapshot·appVersion/venv 조건 확인 및 Windows 빌드/설치는 별도 검증/HOLD 범위를 따른다.
- [x] Infra 문서5개와 로컬 compose의 출처·보존 정리 및 integration 커밋·push 완료. Build5 전체 QA HOLD는 별도 유지.

<details>
<summary>날짜별 진행 이력 — 이후 배포로 해소된 과거 대기 상태 포함</summary>

당시 웹 배포 완료·운영 화면 확인 대기: [변경 예약 취소 확인·회원 연결 결제 이동](./2026-09-10-reservation-confirm-payment-link-fixes.md). Customer 예약 취소에 기존 공통 확인창(예약 유지/예약 취소) 추가, 확인 전·닫기 API 미호출·중복 클릭 차단. Admin 연결 결제는 회원상세 경로를 유지하며 대상 결제 행으로 스크롤·포커스·강조, 직접 주소 진입/재클릭 처리. Customer285/Admin424 전체 테스트·두 prod 빌드 및 로컬 CUA 검증 완료. Customer4d95a96/Admincd3a306 커밋·일반 push·기존 배포 브랜치 원격 SHA 확인 완료. 사용자 m4-prod 출력으로 두 이미지 빌드·운영 교체·각 HTTP200/running/restarts0/예상 revision 일치 및 WEB_DEPLOY_OK 확인. 실제 예약 취소 확인창·유지/확정과 연결 결제 이동 화면 확인은 당시 남음. 원본 공유 변경 보존, 자동 승인 차단 해결. API/DB migration/앱 빌드 불필요. 이전 CPU·브랜딩 새 앱 빌드 대기 및 Build5 QA·플러그인 HOLD 유지.

운영 화면 후속 확인: 사용자 `확인했어`로 Admin 상품 모달의 텍스트 드래그 유지·배경 클릭/Escape 닫기와 설치 파일 Build 내림차순 확인 완료. Customer 다운로드 안내 모달 실기·앱 새 빌드/Windows 확인은 남음. 앱 Electron/Angular 소스 push 완료로 서버 추가 배포는 불필요하나, 기존 릴리즈의 고정 스냅샷 재빌드는 수정 전 소스를 사용하므로 새 릴리즈·새 소스 스냅샷으로 빌드해야 함. 상세 최신 상태는 [모달·CPU·브랜딩 배포](./2026-09-10-modal-cpu-branding-deployment.md) 참조. Build5 QA·플러그인 HOLD 유지.

최신 웹 배포 완료: [모달·CPU·브랜딩 배포](./2026-09-10-modal-cpu-branding-deployment.md). Admin87c4424/Customer9fff91a/Electrona34a39d/Angularc8b18677 커밋·일반 push·원격 전체 SHA 확인 완료. 최종 테스트 Admin422/Customer280/앱 Angular83/Electron94 및 네 빌드 통과. 사용자 m4-prod 출력으로 Admin/Customer 이미지 빌드·운영 교체·각 HTTP200/running/restarts0/예상 revision 일치·WEB_DEPLOY_OK 확인. 공유 원본 브랜치·HEAD·diff 보존. 실제 모달·정렬 화면 확인과 앱 새 빌드·Windows 실기 확인은 대기. API/DB migration 대상 없음, 기존 게시 파일/정식 지정 변경 없음. Build5 QA·플러그인 HOLD 유지. 아래 미커밋·미푸시·웹 배포 대기는 후속 배포 이전 기록이다.

최신 관리자 모달 전체 추상화: [공통 ModalComponent 전환](./2026-09-10-admin-modal-component-refactor.md). 사용자가 닫힘 directive만의 공통화를 범위 축소로 정정. Admin 내부 `src/app/components/modal`에 재사용 모달을 만들고 13개 모달/상세창의 배경·제목·닫기·본문/하단 배치·Escape·포커스·스크롤을 통합. 화면은 본문과 작업 template/업무 로직만 제공. 새 공유 패키지/alias 없음. Admin422 전체 테스트 및 prod빌드, 로컬 실제 입력 드래그/Tab/Escape/오류 drawer 확인 완료. 미커밋·미푸시·미배포, 공유 변경/이전 CPU·브랜딩·정렬 및 Build5 QA·플러그인 HOLD 유지. 아래 directive-only 검토는 이 후속 이전 기록.

모달 SOLID 후속 검토: 같은 [모달·CPU·정렬 기록](./2026-09-10-modal-cpu-artifact-followup.md) 최하단 참조. directive 내부 메서드 protected·출력 readonly, 개별 모달의 중복 stopPropagation12곳 제거. SRP/이벤트 계약과 소비 화면별 닫힘 제한 유지, 모달 인스턴스 분리 검증. 최종 Admin416/Customer280 테스트·두 prod 빌드·로컬 실제 모달 드래그 확인 완료. 저장소별 공통화이며 두 웹을 묶는 공유 패키지는 아님. 미커밋·미푸시·미배포 및 기존 보류 유지.

최신 수정: [모달 드래그·Windows CPU·설치 파일 정렬](./2026-09-10-modal-cpu-artifact-followup.md). Admin13/Customer1 직접 구현 모달의 배경 닫힘을 저장소별 공통 directive로 통합, 실제 내부→외부 드래그에서 열림 유지·배경 클릭 닫힘 확인. Customer Material 공통 모달도 정상 확인. Windows의 미지원 loadavg 대신 논리 CPU 시간차 사용률 표시, 설치 파일 Build 숫자 내림차순 정렬. Admin413/Customer278 전체 테스트, 앱 관련 테스트 및 네 빌드 통과. 미커밋·미푸시·미배포이며 이전 Clipper 브랜딩 변경 함께 보존. 적용에는 웹 Admin/Customer 배포와 새 앱 빌드 필요(API/DB migration 불필요). Windows 실기 확인 및 기존 Build5 QA·플러그인 HOLD 유지.

최신 브랜딩 후속: [운영판 Clipper 이름 수정](./2026-09-10-desktop-production-branding-followup.md). 창/로그인/문서 제목·종료 안내와 운영 설치 파일명을 Clipper로 통일, 공통 앱 정보 재사용. 격리 checkout의 Electron104/Angular73 관련 테스트와 빌드·로컬 화면 확인 완료, 미커밋·미푸시·새 Windows 빌드 대기. 브라우저의 api.clipperstudio.ai 표시는 로그인 완료 페이지 출처로 정상이며 API/프로토콜 유지. 웹 재배포·DB migration 불필요. 공유 변경 및 Build5 QA·플러그인 보류 유지.

Windows 후속 실기 확인: 새 설치에서 개발판 종료 안내 없음·두 앱 동시 실행·기존 개발판 로그인 유지 및 metabuzz2023 동일 계정으로 개발판/운영판 양쪽 동시 로그인 유지까지 사용자 확인 완료. 실제 파일명은 개발 `clipperstudio Setup 0.0.16.exe`, 운영 `clipperstudio Setup 0.0.2.exe`로 후속 제공받음. Build 번호/소스·파일 SHA 대조 및 업데이트/제거 공존 확인은 별도 남음. 기존Build5 전체QA·플러그인 보류 유지.

최신 요청 우선: [크레딧 공통 표시·결제내역 필터·Windows 설치 충돌](./2026-09-10-credit-payment-windows-isolation-followup.md). 사용자 명시적 승인 후 API e0e5b35/Admin59b7903/Customer0512173/Electron2d492fe 커밋·일반push·원격전체SHA 확인 완료. 자동 승인 검토 차단은 해결됨. API/Admin/Customer 전체 테스트 및 빌드 통과, Windows 관련48테스트 및 실제 NSIS 설치·제거 컴파일 통과. 사용자 출력으로 웹3종 운영교체/running/restarts0/예상SHA·HTTP200 및 API DB3항목ok 확인, 웹배포 완료. 신규 표시·필터·영수증 화면확인 및 사용자 직접0.0.2 새 릴리즈·스냅샷·빌드·정식지정 후 Windows 재시험 대기. 기존 Build5 QA·플러그인 검증 보류 유지. 기존 환불 테스트보다 이 후속을 먼저 진행한다.

최신 고객 화면 후속 완료: 이용권 충돌 안내 및 버튼 폭40px 초과 수정·충돌 화면의 요금 링크 숨김은 266테스트/prod빌드 통과. Customer8c723c3 커밋·GitHub push·운영 배포 및 revision/running/restarts0/HTTP200 확인 완료. 사용자 `확인 완료`로 버튼 폭 정상·복귀 링크 숨김 실제 화면까지 확인. 상세는 아래 QA 수정 배포 기록 최종 절 참조. Admin 자동 갱신 운영 검증 및 남은 이용권 테스트는 별도 유지.

최신 배포 완료: [고객·관리자 QA 수정 배포](./2026-09-10-web-manual-qa-fixes-deployment.md). Customer aa26eed/Admin3747eb0 GitHub push·운영 이미지 빌드 및 start-only 완료. 두 컨테이너 running/restarts0/예상 revision 일치와 각각 HTTP200 사용자 확인. 실제 수정 화면 검증 대기이며 아래 미커밋·미푸시·미배포 표기는 이전 상태다.

업데이트: 2026-09-10 PG 세션 종료. PG 현재 상태는 [최신 PG 인수인계](./2026-09-10-pg-session-closeout.md)를 우선한다. 운영 구축은 별도 종료문서를 참조한다.
후속 표시 수정·운영 확인: [Admin 표시 후속 기록](./2026-09-10-admin-display-followup.md)을 우선한다. API9b1b395/Adminfa7e67a 배포 및 아래 명시된 실제 화면 확인 완료, Customer b5dc797 유지.
체크는 명시된 범위만 완료를 뜻한다. 구현·배포·운영 E2E·실제 화면 확인을 구분한다.
추가 요청: [미사용 상품 정리·이력 표시 후속 기록](./2026-09-10-admin-catalog-audit-followup.md). 삭제 migration 운영 적용 및 APIa0a78db/Admin597c5b6 커밋·푸시·배포, HTTP/DB 확인과 상품·이력 실제 화면 사용자 확인 완료. 수동 지급·충돌·사용분 환불 차단 E2E는 미완료.
과거 작업/시안/검증 이력은 [WORKLOG](./WORKLOG.md)와 [이전 인수인계](./2026-09-08-production-pg-session-handoff.md)에 보존한다.
최신 수동 지급 후속: [관리자 지급 사유 누락](./2026-09-10-admin-credit-grant-reason-followup.md). API3299a73 배포·health와 기존 지급100 사유/원장+100/고객 총5900 사용자 확인 완료. 지급ID307ff59f 기준 부분·전액 수동회수 및 초과회수 차단 검증 대기.
최신 회수 후속: [상단 지급표 갱신 누락](./2026-09-10-admin-manual-action-refresh-followup.md). 지급100/부분회수40/잔여전액회수60·원장순합0·회수버튼 제거·Admin/고객5800 복귀 확인 완료. 상단 표 자동 갱신 수정은 Admin 로컬401테스트/빌드 통과, 미커밋·미배포. 다음은 별도 이용권 없는 TEST 회원의 관리자 이용권 지급.
최신 이용권 검증: [관리자 Basic 지급 및 신규 결제 안내](./2026-09-10-admin-access-grant-test.md). 한진아 고객800=관리자 이용권400+무료400 확인. 이용권 보유 중 신규 결제의 일반 오류 문구/카드창 미열림 확인. 안내 문구와 마이페이지 이동 수정은 Customer 로컬266테스트/prod빌드 통과, 미커밋·미배포.

</details>

## 1. 배포 확인 이력과 연결된 잔여

현재 최종 배포는 API e0e5b35 / Admin cd3a306 / Customer 4d95a96이며, 아래 이전 revision은 해당 검증 시점의 이력이다.

- [x] 이 PG세션 최종 API `923c9cb`/Admin `62a5669` 배포·정상응답 및 전액환불 안내 실제화면 확인.
- [x] 원격 최신 읽기전용 확인: API release `8e1ce22`/Admin release `62a5669`, Customer integration `ae75f51`. 운영 구축 보고로 API8e1ce22 후속 배포 확인. Git상 PG923c9cb 자손·표시 관련6파일만 변경 확인. Customer 후속 배포는 미확인. 병렬 작업 대조와 설정/제공자 키 미확정 사항은 PG 종료문서 8절 참조.
- [x] API/Admin 브랜치 통합 및 Customer 미커밋 개선 커밋·push: API ab86b3d, Admin8980eab, Customer b5dc797. 전체 테스트2486/394/265 및 빌드 통과. OpenAPI 중복key 해결.
- [x] 통합3커밋 운영 배포: API ab86b3d/Admin8980eab/Customer b5dc797 revision·running/restarts0·HTTP200. 관리자DB AddNaverUsageApis1789000000000 단일SQL 적용 COMMIT, 네이버2키 유지, API DB3항목ok.
- [x] 배포 후 사용자 네이버 용도 저장 완료 보고·Customer 지급일시/사유/환불회수 유형 표시 확인. 합계4800 유지.
- [x] Customer 결제내역 링크·환불회수 필터·초기화·좁은 화면 표시/조작/스크롤 사용자 확인. 합계4800=무료400+추가4400 유지.
- [x] ab86b3d 실행 상태에서 redirect/runner URL 및 양방향 토큰 해시 일치, runner health200/idle, 실패주입 변수0개 확인.
- [x] API9b1b395/Adminfa7e67a 후속 표시 수정 커밋·push·운영 배포: revision/running/restarts0/HTTP200 및 API DB3개ok. 전체 테스트 API2493통과/16skip, Admin399통과, 두 빌드 통과. Customer 과거400 Credits 한글 표시 및 잔액 사용자 확인.
- [ ] 네이버 실제 호출, 연간 월간탭 및 재시도실패 운영 검증. 9b1b395 재배포 후 redirect/runner/token·실패주입 제거 추가 재조회는 별도. 공유 원본 M표시 보존, reset 금지.
- [x] 제공자 키 소실 조사 종료: 사용자 정정으로 운영에 아직 등록하지 않았던 것으로 판단. 장애 원인 조사 불필요.
- [ ] 환불 접수 성공 후 상세 자동이동의 운영 실행 확인. 코드4367fa8 배포·테스트 완료, 다음 필요한 TEST환불에서 확인.
- [x] Admin 기존 취소 TEST 구독의 예약표시 제거·현재 구독 월 종료 해당 없음·환불 완료, Trial 유효권한과 관리할 지급기록 없음 실제 화면 사용자 확인. API access/accessGrant 계약 분리 및 Admin/mock 동기화. 실제 종료시각을 추정하여 추가하지 않음.
- [ ] 만료원장·종료감사이력 정책, 임시override파일 정리. a12/a13 파일 존재 확인, 삭제/재적용 없음.

### 아래는 9/8~9/9 당시 배포 이력 (현재값 아님)

2026-09-09 세션 A: [PG 기능 테스트 기록](./2026-09-09-pg-functional-test-log.md). 실행revision 3개 일치, 완료환불 전체 DB 대조、고객/Admin 최종 화면 사용자 확인 완료. 유효 잔액5,200 유지. 후기 추가충전 주문 DB/Toss 대조 및 현재 Toss 상태 조회는 남음.

- [x] Customer `888c2b96d818857306e9376c3436563c394971b1`: 커밋·푸시·사용자 배포, running/revision/HTTP200.
- [x] Admin `fb3e532b3e9b195c5c149a207fbcbf5673932245`: 커밋·푸시·사용자 배포, running/revision/HTTP200.
- [x] API `27103011e2e0672199721c6c3974c5bfc4e0d741`: 배포·health/DB3개ok 확인, 이후 변경 없음.
- [x] 앱 원본3repo 작업트리 clean, 로컬 추적 upstream 차이 없음. 이번에 새 원격 fetch는 안 함.
- [x] 마지막 수정본 실제 화면 확인: 결제내역 메뉴/표/결제금액/KST문구제거, 크레딧 지급·원장·요약 배지색 일치. 9/9 사용자 확인, 크레딧 화면 잔액5,200.
- [x] 환불 회원의 최종 Customer 이전상품/종료시각/관리패널숨김 및 Admin 환불완료 표시 실제 화면 확인. 9/9 사용자 확인: Admin 결제표·환불표·환불상세 완료 표시와 Customer 마이페이지 Trial·이전 Pro연간·환불 종료시각·관리 버튼 숨김 확인.

## 2. 운영 기반 및 이번 세션 구현 — 완료

- [x] 원본 web/desktop에 PG 통합 후보 준비. .integration-clones를 작업 정본으로 사용하지 않음.
- [x] m4-prod 직접 Docker build/현재 upstream/선택 배포, local/dev/prod 분리, migration 별도 실행.
- [x] 운영 웹/API/DB3개, DNS·NPM HTTPS, Google고객/최고관리자 로그인 기본 검증.
- [x] 별도 승인된 운영 테스트 DB 재생성 및 migration/관리자등록 완료. 재초기화 금지.
- [x] 추가상품명 한글화 migration 및 카탈로그3종 가격·수량·30일 확인.
- [x] 크레딧 표/열간격/시각/단일 사용가능잔액, 결제예정 날짜+시각 안내.
- [x] 최종동의 금액·주기·자동갱신/미동의차단, API 저장된 subscriptionTerms.
- [x] 요금제 변경 표 모달·차액 공제 설명·연간→월간 제한·409문구 구분, 카드등록/변경 안내 정리.
- [x] 중립 다크 모달/이용권 배경, 강한 backdrop, 월/연 배지.
- [x] Admin 주문 ellipsis/Material복사/Snackbar/한줄회원/한글결제유형/열폭 개선. 상세펼침 제거.
- [x] 환불 표시 보완: 결제·환불 종합상태 우선, 종료구독 관리영역 숨김, Admin 대응case 돈/내부완료 확인.
- [x] Customer 결제내역 nav/단일표/작은제목, 출처6종 배지색 및 표·요약 간 일치, 문구 간소화.

## 3. TEST PG — 실제 확인 완료 범위

- [x] 최초 Pro월간10,900 결제, 구독1000+Trial400 지급/활성.
- [x] 추가400/5,900 정상구매·DB paid/succeeded·지급1/원장1·정확30일·Toss paymentKey 조회200 대조.
- [x] 위 추가충전 Admin 상태재확인2회, 잔액1800 유지. 실제 지급 재실행과 구분.
- [x] 자동갱신 취소→재개 고객화면·기간/권한/잔액 유지·신규결제없음.
- [x] 정상 활성구독 카드변경 성공·새카드 표시·기간/잔액/청구일 유지·신규결제없음.
- [x] Pro월간→연간 차액72,017 성공·새기간·기존1000회수/새1000지급 확인.
- [x] Business연간151,208 견적과 Basic연간58,800 예약 모달 확인. 실제 확정/적용 성공으로 확대하지 않음.
- [x] 연간→Business월간409 NOT_ALLOWED 실제 관찰, 금지 UI/문구 수정.
- [x] 연간 구독의 상향72,017 주문 환불1건: Toss취소/돈·내부완료/권한종료/구독크레딧회수 사용자 확인.
- [x] 해당 환불 후5,200 잔액=topup4,800+Trial400, 구독지급 잔여0 확인. 별도 topup/Trial 유지가 현 코드 정책임을 확인.
- [x] 빌링키 DELETE200 및 BILLING_DELETED 성공전송16:35:00 기록 사용자 확인.

## 4. TEST PG — 남은 검증

- [x] 관리자 이용권 정상 흐름 운영 UI 검증: [한진아 TEST 진행 기록](./2026-09-10-admin-access-grant-test.md). Basic 지급/고객800·기간 연장·Pro 상향/차액600/고객Pro1400·16:51 이용권 회수 확인. 최종 Admin/고객 모두 Trial 및 총1400=관리자1000+무료400, 기존 지급분/기한 보존 확인. 변경·회수 이력/사유/운영자 이메일 확인. 완료된 흐름 재실행 불필요.
- [ ] 관리자 이용권 추가 검증: 예정 지급·하향 등 미실행 조합과 운영 DB/PG 신규 청구 없음 대조. 상단 자동 갱신의 실제 새로고침 여부 확인은 아래 별도 항목 유지.
- [x] 관리자 크레딧 지급·회수 정상 경로 운영 검증: 지급100/사유/원장+100/고객5900, 101 초과 입력 버튼 차단, 부분회수40 후 잔여60, 나머지60 회수 후 잔여0 및 회수버튼 제거. 원장+100/-40/-60 순합0 및 Admin/고객5800 복귀·기존 구독/다른출처 유지 사용자 확인. 직접 API 초과요청·동시성·사유미입력 제출차단은 이 완료 범위에 포함하지 않음.
- [ ] 수동 작업 후 상단 지급표 자동 갱신 운영 확인 마무리. Admin3747eb0 배포/401테스트/빌드 통과. Pro 상향 후 상단 신규600/하단총1400/원장+600 일치 사용자 출력 확인. 새로고침 전 확인 요청에 대한 응답이나 실제 새로고침 여부 명시 확인은 별도 남음.
- [x] 관리자 지급/결제표 과거 시스템 문구 공통 한글 표시 구현·배포: APIe0e5b35/Admin59b7903/Customer0512173에 포함. 원본 사유/결제 스냅샷 보존. [후속 기록](./2026-09-10-credit-payment-windows-isolation-followup.md) 참조.
- [ ] 위 사유 공통화 및 고객 결제 카테고리/영수증 링크의 운영 실제 화면 확인. 과거 환불회수 필터 확인과 구분.
- [ ] 현재/예정 구독·관리자 이용권 보유 중 신규 정기결제 차단 운영 확인: ACTIVE_ACCESS_CONFLICT/409, 새 주문·PG 결제 없음。한진아 관리자 Basic 보유 상태에서 일반 오류 문구/카드창 미열림 사용자 확인, 실제 응답 및 DB 주문 불변/다른 조합 검증은 남음. 무료체험만 보유한 경우 및 기존 구독 요금제 변경은 별도 경로.
- [x] Customer 이용권 보유 결제 차단 안내 및 버튼 스타일 배포·운영 확인: 전용 안내 + /my 링크, 카드 등록 버튼 제거, 버튼 폭 정상 및 요금 복귀 링크 숨김. Customer8c723c3 배포/266테스트/prod빌드 및 사용자 실제 화면 확인 완료.
- [ ] 사용 크레딧 환불 차단 운영 E2E: TEST 월간·연간·추가충전의 대상 지급분 사용 시 CREDITS_USED 및 환불 접수/PG 취소 없음. 다른 무료체험 사용만 있는 경우와 작업 실패로 사용량 전액 복구된 경우 구분. 자동 테스트의 자격 판정/접수 잠금 재검증은 통과. 실제 대상 지급분 차감·화면/API/DB 대조는 미실행이며 플러그인 보류 유지.
- [x] 비활성 기본 상품 credits_100/credits_500 삭제 migration 운영 적용: 참조 주문0 사전 조회·백업 및 archive 읽기 성공·COMMIT·삭제 대상0·적용기록1 확인. 판매중400/1000/4000만 유지, 가격5900/10900/29900·모두30일/활성. 로컬 migration5테스트 및 적용 SQL 원자성5경로 통과. 적용 재실행 불필요.
- [x] 운영자 이메일/이력 한글 표시 실제 화면 확인. APIa0a78db/Admin597c5b6 배포·HTTP200/DB3개ok 및 사용자 상품 목록/회원 상세 한글 유형·최초결제 사유·운영자 이메일/시스템 확인 완료. 전체 API2494/Admin400 테스트 및 두 빌드 통과. 15:23 신규 구독 시작 이력 관찰로 다음 수동 테스트 전 현재 권한/잔액 기준값 확인 필요.

- [x] 완료 환불case `61d6c4bc-b2b3-4328-835f-b27f3eb98807` 운영 read-only DB 대조: case/item/event/order/subscription/access/grant/ledger. 9/9 사용자 출력으로 전액72,017·권한종료·구독1000 회수1건·유효잔액5,200 확인. 현재 Toss GET/실제 화면/재실행 멱등성은 별도.
- [ ] 월간·추가충전·사용량있는연간·부분/실패/복구 등 환불 매트릭스. 이미 환불완료 주문 재취소 금지.
- [x] 미사용 Pro월간10,900 전액환불1건: case `c7aa3c09-6a9c-48a2-b3e9-4aa1fd9ae16a`, Admin/DB 돈·내부완료·구독/이용권종료·청구중단·구독1000 회수원장1건·나머지4800/기한 유지. Toss 관리자 해당주문 취소 확인, 고객 Trial/잔액4800/해당10900 전액환불 표시 확인. 재실행·실패복구 검증은 별도.
- [x] 미사용 추가충전400 전액환불1건: case `6ae2147f-5a19-474a-8dae-e3c656445127`, Admin/DB 돈·내부완료5,900·회수400원장1건·다른크레딧4,800/기한 유지. 9/10 00:20 KST Toss GET CANCELED/취소5,900/잔액0, 후기4,000 결제 유지 확인. 고객웹 잔액4,800 및 해당 주문 전액환불 표시도 사용자 확인.
- [x] 후기 추가충전4,000/400의 각 주문 DB/Toss 대조. DB 금액29,900/5,900·paid/succeeded·지급/원장 각1건·미사용·정확30일 확인. 9/10 00:08 KST 사용자 Toss GET 출력으로 두 건 모두200/DONE·주문/결제일치·동일금액/잔액·취소0 확인.
- [ ] 즉시변경 성공 당시 DB/Toss·중복처리, 변경실패 시 기존권한/크레딧 유지.
- [ ] 하향 예약 확정/취소/다음갱신 적용, 금지조합 최종화면 검증. 9/10 Basic월간 예약확정/미동의차단/취소/재예약 UI·DB 확인. 승인된 기간압축 후01:01 자동갱신5900 완료를 고객/DB/Toss관리자에서 대조, Basic전환/월400 지급원장1건/유효5200 확인. Admin 표시·금지조합·실패/중복은 대기. 기존Pro1000은 조정SQL 정밀도 차이로 active 잔존하나 기한 경과로 가용 제외; 만료상태 정리/정상경계 재검증 별도.
- [x] 기간압축 TEST Basic월간 갱신1건: renewal-mq8vZp1uBPcFrXET_pcFYPpJ, 5900 결제·Basic전환·월400지급1건·유효5200 고객/Admin/DB/Toss관리자 대조. 정상 한달경과/실패/강제중복 검증과 구분.
- [x] Admin 상·하단 지급표 만료표시 수정 배포·운영확인 완료. 기존 테스트 지급건 단일행 상태정리 완료. 수정 API의 해지예약 자동만료 경로도 별도 통과. 유예종료 수정후 재현/동시성은 남음.
- [ ] 해지/재개 Admin/DB 대조, 경계/실패 상황.
- [ ] 카드변경 이전키 정리·실제 다음청구 새키사용·취소/실패/연체 경로.
- [ ] 정기갱신·연간월별지급·실패재시도·유예/만료·worker재기동/복구.
- [x] API37cdcdb 자동만료 회귀검증(해지예약·시간압축): 신규 TEST 구독65a5a240, 종료경계09-10 04:47:46.828 후04:52:51 DB에서 subscription/access ended, grant c6d4a96f expired/rem400, 최초5900주문1건만/가용무료400 확인. 상태수동변경없음. 수정후유예종료경로실환경재현·동시실행순서 검증은별도.
- [x] A13 TEST 자동 재시도2회 소진·유예만료: 한진아 be09b51b, 시각압축 후 scheduled 실패2회/index2/retry NULL, 유예경계04:08:41.667 이후 stopped/access ended/청구중단/무료400 유지. 고객 Trial·갱신실패로정지·새구독안내·다음결제중단 확인. 실패 override 제거/API8acbb90 health200 확인. 실제1·2·3일 경과 및 다른 PG 오류/동시성 검증과 구분.
- [x] TEST 갱신 거절 후 수동 재시도 복구(A12): 한진아 구독be09b51b, 기존 주문renewal-3KcBcj7YTkOLDKkK69TK07NS가 API8acbb90 적용 후5900 paid/succeeded로 복구. 고객 활성/800, DB 유예·재시도 해제/월400 원장1건, Toss09-10 03:44:43 승인5900 대조. 자동D+1/D+2·최종유예만료·동시성 검증은 별도.
- [x] 연간 월별 지급 기간압축 DB·Admin·고객 지급내역 검증(9/10 02:10 이후): Basic연간 기존400 자동만료/새400 원장1건, DB/Admin 유효5200 유지, 신규결제없음, 다음월지급10/10·다음연간청구2027/9/10 유지. 고객 두 지급 상태·기한 및 +400 원장 확인. 실제한달경과·강제재실행/동시성은 별도.
- [ ] 환불 처리 중 자연 기간종료가 겹치는 상태표시/실제 내부처리 검증. 기존 Customer 상태추론 한계 확인.
- [ ] 웹훅/콜백 실제 앱저장·중복전달·재시도, 지급함수 재실행·동시요청 멱등성. 월간환불 PAYMENT_STATUS_CHANGED 및 BILLING_DELETED processed 저장확인, 삭제이벤트의 카드등록이력 일치/구독canceled/키삭제succeeded 대조. 같은 월간processed 이벤트 loopback2회 전송은 기존inbox1건 유지. 다른전송ID1회는01:26 processed, 01:26/01:27 DB에서 환불10900/원장2건·순합0/현재Basic·유효5200 불변 확인. 동시성/실패재시도는 미검증. 연간상향 one_time/billing을 recurring으로 요구한 API 결함 로컬 수정, 관련166테스트/빌드 통과. 배포·해당웹훅 복구는 대기, 완료환불 재실행 없음.
- [x] 주문미도착 합성웹훅 재시도·소진: inbox41151647-ec2b-40ec-8853-7e55bce8ef40, 1/4/16/64분 예약 후02:59:00.045 KST manual_review/WEBHOOK_RETRY_EXHAUSTED/retry4/next_retry NULL. 03:17:41 READ ONLY로 확인. 실제주문/PG호출 없음. 성공복구·다른오류·동시성은 별도.
- [ ] TEST Widget/Billing MID·키별 웹훅 및 옛ngrok 등록 정리 여부 확인.
- [x] 현재 공용TEST Widget 가상계좌 미제공 확인: 사용자 결제창에 퀵계좌이체/신용체크카드/토스페이/페이코/카카오페이/네이버페이만 표시. 이 설정의 입금대기/입금/만료 E2E는 제외. 향후키/설정변경시 재확인, DEPOSIT_CALLBACK 기능통과를 뜻하지 않음.
- [ ] 최종동의 운영화면 증거 정리 및 전략팀 전달. 약관·FAQ 정책 설명/법무 확인은 별도 미완료.

### 9/10 PG 최종 추가 완료 및 잔여 구분

- [x] 기존 연간상향 manual_review 웹훅 복구: processed/환불72017·원장2건/합계0 유지. 과거 ‘배포·복구 대기’ 문구는 해소됨.
- [x] 연간변경 후 월별지급 포함52906 전액환불: 고객/Admin/DB/Toss/취소웹훅 대조 완료,총4800.
- [x] 전액환불 완료 건 재접수 차단·잘못된 일부취소/0원안내 수정, API923c9cb/Admin62a5669 배포·화면확인.
- [ ] 실제 부분환불 건 검증은 미실행. d8782ce3는 전액환불 완료 건이므로 부분환불 검증으로 계산하지 않음.
- [ ] 상기 정상·복구 테스트를 제외한 남은 매트릭스(사용량/환불실패/권한/경합/자연기간/카드변경)는 계속 미완료.

## 5. 전체 운영 구축 — 남은 범위

**현재 구분:** 운영 식별자·runner 소스 push/빌드·다운로드/설치·개발판 공존/동시 로그인은 후속 수행됐다. 아래 9/9 세션B 문단은 당시 기록이다. 남은 것은 업데이트·제거 공존, Build/artifact 출처 재대조, 운영 안정성/live심사 등이며 [현재 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md) 3절을 따른다.

> 2026-09-10 세션 종료: Windows Build 5의 Admin→runner→서명→S3 업로드→다운로드→설치·로그인 유지 확인. QA 대기이며 플러그인 검증은 사용자 보류. 하위 항목은 전체 검증이 끝나지 않아 체크 유지. 상세 완료/잔여/오류 해결은 [운영 구축 세션 정리](2026-09-10-production-setup-session-closeout.md) 참조. 후속 작업으로 월 지급 한국어 표시 운영 API 8e1ce22 배포, health/3개 DB 정상 및 사용자 과거 내역 표시 확인 완료.

2026-09-09 세션 B: [운영 구축 기록·분류·결정안](./2026-09-09-production-setup-log.md). 운영 이름 Clipper/기존 아이콘 재사용은 잠정 전제, 식별자 적용 미승인. 최신 desktop dev+PG를 별도 worktree의 새 `integration/toss-payments-pg-20260909`에 로컬 통합·검증(상세 7절), Python은 사용자 결정대로 최신 dev만 사용. 기존 원본/미커밋 보존, 새 branch 미푸시. 같은 Windows PC에 dev/prod runner와 작업폴더를 각각 분리하기로 결정. 운영도 Windows 다운로드만 제공하고 Mac은 준비 중 유지. Windows 자동업데이트는 코드상 기본 ON이나 실제 설치본/Release DB 설정은 확인 필요. 실제 운영 빌드·배포·설치·공존은 미검증이며 아래 완료 체크는 유지한다.

- [ ] 운영 desktop 이름/아이콘/appId/protocol 확정 (별도 승인), API/JWT/로그인/업데이트/userData/keychain/모델·캐시/포트 분리.
- [ ] 운영 runner 컨테이너·포트·env·작업/output·S3/Release 분리 및 build 검증.
- [ ] 운영 Admin→runner→S3→Customer Windows 다운로드→설치·개발판 공존 검증. Windows 자동업데이트 실제 상태/정책 확인. **Mac 다운로드는 준비 중 유지(사용자 결정), Mac 공개·자동빌드·업데이트 구현 보류.**
- [ ] 개발 전환: 복제DB에서 사용자/로그인 보존 및 승인된 옛데이터 초기화 검증. **개발 서버·DB 실제 작업 보류**.
- [ ] 운영 모니터/알림, 백업·복원, 정전·재부팅 복구, DB접근·로그·비밀관리 (팀결정 포함).
- [ ] Google 게시/검증·지원메일/소유자, Toss 계약·심사·live키/MID·테스트데이터정책.
- [ ] 명시 승인된 실결제/취소 검증 및 정식공개 판단. 현재 TEST 유지.
- [ ] 최종 branch/PR 통합, desktop 원격 상태, Infra5문서/.codex 기록 검토·선택커밋·팀공유.

## 6. 다음 세션 분리와 제약

2026-09-09 사용자 결정: 두 세션으로 분리하며 개발 전환은 양쪽 모두 제외한다.

- **세션 A — PG 기능 테스트:** 1번 실제 화면 확인과 3·4번 검증/발견 결함 수정. 최신 화면과 완료환불 읽기전용 대조부터 시작한다. [시작 문구](./NEXT_SESSION_PG_TESTS.md)
- **세션 B — 전체 운영 구축:** 5번 중 개발 전환을 제외한 desktop/runner/지속운영/라이브 준비/통합·문서. 현황·미정사항 확인 후 진행 가능한 작업부터 수행한다. 실제 라이브 전환·식별자 변경은 별도 승인이다. [시작 문구](./NEXT_SESSION_PRODUCTION_SETUP.md)
- 서로 다른 전용 진행기록을 사용하고 이 체크리스트는 각 담당 항목만 갱신한다. 공용 파일 수정·운영 배포·재시작·키 변경은 세션 간 조율한다.

서버명령은 장비·영향 설명 후 사용자가 한 단계씩 실행. 개발DB/운영DB초기화/live결제/desktop식별자 변경 금지.
이 체크리스트의 남은 항목은 실행 승인이 아니다. 과거8월 심사용 checkout의 미배포 상태를 현재 상태로 되살리지 않는다.
