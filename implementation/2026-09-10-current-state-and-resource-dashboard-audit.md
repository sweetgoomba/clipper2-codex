# 현재 상태 감사와 플러그인 대시보드 점검 — 2026-09-10

> **후속 우선:** 이 문서의 리소스 ‘구현 전’ 상태는 [R1~R4·watchdog·UI 후속](./2026-09-10-plugin-resource-safety-followup.md)과 [R5 후속](./2026-09-10-windows-owned-process-tree-followup.md)에서 갱신되었다. 최신 완료·보류 구분과 Build7 증거·SDK/venv 조건은 [문서 정리](./2026-09-10-documentation-source-reconciliation.md) 및 [TASKS](./TASKS.md)를 따른다. 아래 본문은 당시 감사 이력으로 보존한다.

## 읽기 순서와 증거 범위

이 문서는 9/10 PG·운영 구축 후속 작업의 현재 상태 정본이다. 과거 문서의 미커밋·미푸시·미배포·검증 대기 문구보다 이 표와 이후 날짜의 후속 결과를 우선한다. 상세 이력은 [PG 종료](./2026-09-10-pg-session-closeout.md), [운영 구축 종료](./2026-09-10-production-setup-session-closeout.md), 각 후속 문서에 보존한다.

- 이번에 원본 8개 저장소와 사용한 격리 checkout의 HEAD/branch/status/diff를 읽기 전용 조회했다. 기존 8개 GitHub origin의 브랜치 SHA도 새로 조회했다.
- 운영 컨테이너는 직접 접속해 재조회하지 않았다. 아래 실행 revision/HTTP/DB 상태는 사용자가 제공한 마지막 서버 출력이다. 커밋 push와 컨테이너 교체·실제 화면 확인을 구분한다.
- 최신 사용자 `둘다 잘 되는거 확인했어`로 요금제 변경 예약 취소 확인창과 관리자 회원 연결 결제 이동의 운영 화면 확인 완료.
- 사용자에게 현재 Windows 버전·Build를 확인하여 **0.0.3.7(버전 0.0.3 / Build 7)**로 기록. 이 앱에서 CPU 사용률이 21.3%/25.5% 등으로 표시되고 논리 프로세서 20이 나온다는 실기 증거를 받았다. 해당 Build의 source snapshot·설치 파일 SHA·서명·정식 지정은 별도 직접 대조하지 않았다.
- 공유 미커밋 변경 보존. Build 5 전체 QA·실제 플러그인 실행 HOLD 유지. 이번 대시보드 점검은 코드·격리 테스트이며 실제 ML 플러그인 실행/메모리 고갈/실행 중 프로세스 종료를 의미하지 않는다.

## 1. Git·배포 대조

| 저장소 | 원격 배포 브랜치 | 새로 확인한 원격 HEAD | 운영 적용 증거 |
|---|---|---|---|
| API | release/pg-expiry-20260910 | e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5 | 사용자 출력 running/restarts0/HTTP200, DB user/release/admin ok |
| Admin | release/pg-expiry-20260910 | cd3a3069310bdae13f123615e1a1a2a8972187cd | 사용자 출력 running/restarts0/HTTP200/WEB_DEPLOY_OK + 최신 두 UI 중 연결 결제 확인 |
| Customer | integration/toss-payments-pg-20260903 | 4d95a963cde6f4e4067244c6cc8c148bb66709ce | 사용자 출력 running/restarts0/HTTP200/WEB_DEPLOY_OK + 예약 취소 확인창 확인 |
| Electron | integration/toss-payments-pg-20260909 | a34a39d510bca51bf8b3e527d433ff9112c686fc | 소스 push 완료. 현재 설치 0.0.3.7의 CPU 표시 확인, 정확한 소스 snapshot 대조는 남음 |
| 앱 Angular | integration/toss-payments-pg-20260909 | c8b186770ae6f77294a2a1689226834f05a8944a | 위와 같음 |
| Nest | integration/toss-payments-pg-20260909 | 780128a069c38a9df6438cc64d79f7a2e42bc1ea | 원격/원본 HEAD 일치. 현재 Build 7 snapshot 대조는 남음 |
| Python | integration/toss-payments-pg-20260909 | 260751d2fa5be8a5a9cd8e346c60ba22d1512ed9 | 원본 dev HEAD와 배포 integration HEAD 일치. 원격 dev는 88b1da2로 별도 진전했으므로 자동 통합하지 않음 |
| Infra | integration/toss-payments-pg-20260903 | f948922c812ab583a84e4a64c5d8faa423afe294 | 원본 HEAD 일치. 미커밋 runbook 2개/미추적 문서 3개 별도 |

기존 후속 수정에서 **아직 푸시하지 않은 구현 커밋은 발견하지 못했다.** 원본의 M표시를 미배포로 해석하면 안 된다. 이번 사용자 요청 이후 새로 만드는 CPU 표시 개선은 아래 5절의 별도 단계다.

### 공유 원본 미커밋의 실제 의미

- API: 추적 8파일, 미추적 `docker-compose.pg-local.yml` 1개. 추적 8개 중 7개는 이미 통합·배포한 ab86b3d의 파일과 byte 단위 일치. OpenAPI 1개도 diff 대조 완료: displayName/displayDescription 선언 위치와 displayName 설명을 system grants까지 넓힌 통합 정리 차이뿐이다. 미배포 업무 로직 없음. ab86b3d는 현재 원격 e0e5b35의 조상이다. 로컬 compose는 출처/용도 미확정으로 제외·보존.
- Admin: 추적 7개 모두 통합·배포 8980eab의 파일과 byte 단위 일치. 현재 cd3a306은 그 자손이다. M표시를 다시 커밋할 필요 없음.
- Customer: 추적 10개 모두 통합·배포 b5dc797의 파일과 byte 단위 일치. 현재4d95a96은 그 자손이다. 원본은 과거 상태 보존본.
- Infra: `runbooks/deploy-prod.md`, `runbooks/recreate-prod-databases.md` 미커밋; `production-console-settings.md`, `production-deployment-team-guide.md`, `production-setup-history-20260908.md` 미추적. **문서 변경은 실제 미커밋·미푸시 상태**이며 현재 앱 기능 누락과 구분한다. 이번 감사에서 임의 커밋·삭제하지 않음.
- 원본 Electron/Angular/Nest/Python은 clean. 원본 Electron dd4e9d6, Angular7ae7366은 배포 소스보다 오래됐고 수정 정본은 위 원격 및 격리 checkout에 있다. 원본이 clean이라고 최신 배포 소스인 것은 아니다.
- API/Electron 격리 checkout의 미추적 node_modules는 원본 의존성 디렉터리 symlink이며 소스 미커밋이 아니다.
- 기계 증거: `/private/tmp/clipper-full-audit-start.json`, `/private/tmp/clipper-full-audit-remotes.json`. 임시 파일 소실에 대비해 핵심 SHA와 판단은 이 문서에 기재했다.
- 최종 보존 재검사: 기존 원본·배포 checkout 13곳 모두 감사 시작 시점과 branch/HEAD/status/추적 diff hash 일치. 새 코드 세 저장소의 `git diff --check`도 통과.

## 2. 변경 묶음별 도달 단계

| 변경 | 구현·커밋·push·배포 | 실제 확인 / 남은 범위 |
|---|---|---|
| 예약 취소 확인창·연결 결제 이동 | Customer4d95a96/Admincd3a306까지 완료 | 최신 사용자 두 동작 확인 완료. 모든 예외/동시성 검증으로 확대하지 않음 |
| Admin 13개 모달의 ModalComponent 전환·Build 숫자 정렬 | Admin87c4424에 배포, 최신 배포에도 포함 | 상품 편집 모달 드래그/닫기·정렬 확인. 모든 13개 업무의 제출까지 실기 통과한 것은 아님 |
| Customer 다운로드 안내 모달 드래그 유지 | Customer9fff91a에 배포 | 로컬 CUA 완료, 해당 모달의 운영 실기는 별도 남음 |
| Windows CPU 0 고정 수정·Clipper 브랜딩 | Electrona34a39d/Angularc8b18677 push 완료 | 설치0.0.3.7 CPU 값 표시 확인. Clipper 창/로그인/설치 파일명 전체·Build snapshot 대조는 남음 |
| Windows 개발/운영 설치 충돌 | Electron2d492fe push, 새 운영0.0.2 설치 실기 | 개발판 종료 안내 제거·동시 실행·동일 계정 양쪽 로그인 유지 완료. 업데이트/제거 공존은 남음 |
| 크레딧 사유 공통화·고객 결제 카테고리·영수증 표시 | APIe0e5b35/Admin59b7903/Customer0512173 배포 | 구현·배포 완료, 이 세 항목의 운영 실기 확인 기록은 남음. 기존 환불회수 필터 확인과 구분 |
| 이용권 보유 중 신규 결제 안내·마이페이지 버튼 폭·요금 링크 숨김 | Customeraa26eed→8c723c3 배포 | 사용자 확인 완료. 모든 활성/예정 구독 조합·DB 주문 불변은 별도 |
| Admin 수동 처리 후 상단 지급표 갱신 | Admin3747eb0 배포 | 상하단600/1400 일치 확인. 무새로고침이었다는 명시 확인만 남음 |
| 관리자 지급 사유 누락·수동 크레딧 지급/회수 | API3299a73 배포 | +100/초과101 UI차단/-40/-60/잔여0/원장순합0/고객Admin5800 복귀 확인. 직접 API 초과·동시성 별도 |
| 관리자 이용권 지급·기간·등급·회수 | 기존 기능 운영 정상 흐름 검증 | Basic400→기간 연장→Pro추가600→권한회수·Trial 복귀, 총1400·관리자 크레딧1000 보존 확인. 예정/하향/경합 등 남음 |
| 구형 상품100/500 삭제 migration·이용권 이력 한글/운영자 이메일 | APIa0a78db/Admin597c5b6 배포, migration1789100000000 적용 | 백업 생성·두상품0개·현행3상품 보존·한글/이메일 UI 확인. migration 재실행 불필요 |
| PG·네이버 통합·크레딧 내역/KST/회수 표시 | APIab86b3d/Admin8980eab/Customerb5dc797 및 후속9b1b395/fa7e67a 배포 | 네이버 migration·키2개 유지·용도 저장, 고객 내역·필터·좁은 화면, 종료구독 UI 확인. 최신 통합 후 네이버 실제 호출 별도 |

세부 증거는 `2026-09-10-*-followup.md`, `*-deployment.md`, `admin-access-grant-test.md`에 보존한다. 새 표시 필터와 과거 필터를 묶어 완료 처리하지 않는다.

## 3. 완료된 TEST PG와 실제 남은 작업

### 완료 범위

추가구매400/4000·미사용 추가/월간 전액환불·하향 예약/취소/재예약·압축갱신·월간→연간 차액·압축 연간 월별지급·그 후 환불·취소 웹훅 중복·과거 manual_review 복구·주문 미도착 재시도 소진·A12 수동복구·A13 자동재시도/유예종료·수정후 해지예약 자동만료·완료환불 재접수 안내. 실제 월경과나 모든 실패/경합 검증과 구분한다. 완료 환불 재실행 금지.

### 남은 검증·운영 작업

1. 웹 운영 화면: 사유 공통화/결제 카테고리/영수증 링크, 다운로드 안내 모달, Admin 무새로고침 갱신, 연간 월간탭 비활성·갱신 재시도 실패문구, 다음 필요한 TEST환불의 상세 자동이동.
2. TEST PG: **사용분이 있는 추가 크레딧/연간 환불 차단·부분환불**(관리자 회수는 사용분 테스트가 아님), 환불실패·내부복구·권한별 차단, worker 중복/동시성·재기동·자연 날짜경계, 수정후 past_due 만료 재현, 카드변경 이전키 정리·다음청구, 웹훅 성공복구/경합·환불중 자연종료.
3. 관리자 이용권: 예정 지급·하향·변경실패/경합·DB/PG 무청구 대조. 한진아 계정 관리자 이용권1000 크레딧은 권한 회수 후 유지되는 정책을 검증한 데이터이므로 임의 회수하지 않음.
4. 운영 설정: 최신 API 배포 후 redirect/runner URL·양방향 토큰·실패주입 변수0 재확인(상세 확인은 과거ab86 기준), A12/A13 임시 override 파일 정리 여부, MID/옛ngrok 등록, 만료원장·종료 감사 정책.
5. Windows/runner: Build7 소스 snapshot·artifact SHA/서명 대조, 브랜드 전체 실기, 개발/운영 업데이트·제거 공존, safe.directory 재생성 자동화·보관정리·재부팅복구. 현재 플러그인 대시보드 점검은 아래 별도 범위.
6. 전체 운영: 모니터/알림, 백업 실제 복원훈련(덤프 생성 성공과 구분), 정전/재부팅, 접근·로그·비밀관리, Google/Toss 심사·live 전환, 약관/FAQ·최종 동의 증거·팀 전달.
7. 계속 보류: Build5 전체 QA, 실제 플러그인 실행 검증, 개발DB 전환, Mac 공개. 설치/동시 로그인 성공을 정식 출시 전체 완료로 확대하지 않음.
8. Git: 위 보존본·Infra 문서의 선택 통합/정리는 별도. 새 원격 dev 전체를 운영 integration에 섞지 않음. Admin 번들576.57kB/500kB 경고 및 캐시 정책 점검은 잔여.

## 4. 검증 해석

최신 웹 테스트 Customer285/Admin424와 두 빌드 통과, 실제 화면은 사용자가 확인했다. 이전 앱 검증은 Electron 관련94/Angular관련83으로 **Electron 전체 suite 성공이 아니다**. 과거 전체 suite 1실패는 sibling packaged 산출물 부재였고, 관련 테스트 통과로 덮어 쓰지 않는다.

## 5. 이번 CPU 표시 수정·검토 완료 — 새 코드 미커밋/미배포

- 사용자 승인된 표시: 제목 `CPU 사용률`, 주값 `21.3%`, 보조값 `12코어 · 20스레드`. OS/아키텍처는 이 카드에서 제거. macOS의 기존 1분 평균 부하 단위는 유지하고 CPU 구성은 별도 표시.
- 기존 `os.cpus().length`는 논리 CPU 수다. 물리 코어 수를 반으로 추정하지 않는다. Windows Win32_Processor.NumberOfCores 및 macOS hw.physicalcpu를 OS에서 읽고, 실패 시 코어 미확인 표시를 사용한다. [Node](https://nodejs.org/api/os.html#oscpus), [Microsoft](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processor).
- 새 변경 위치: `/private/tmp/clipper-resource-dashboard-review/{clipper_electron,clipper_angular,clipper_nestjs}`. 위 원격 배포 HEAD에서 별도 로컬 clone, 의존성만 원본 symlink. 이전 원본·배포 checkout은 변경하지 않음.
- 영구 보관: [CPU 패치와 복구 안내](./patches/2026-09-10-cpu-topology/README.md)에 세 저장소 패치, 기준 커밋 및 SHA-256 manifest를 저장했다. 임시 작업 폴더 소실 시에도 clean checkout에 복구할 수 있다. 기존 공유 원본에는 바로 적용하지 않는다.
- 수정: Electron 호스트 수집에 optional physicalCores 추가. Windows CIM의 NumberOfCores를 다중 소켓 합산하고 macOS sysctl 값을 사용. 별도 실행 스케줄 없이 기존 수집 경로에서 최대60초 cache/진행 중 Promise 재사용, 조회 timeout과 Windows 콘솔 숨김 적용. 실패는 undefined로 반환해 CPU/메모리 수집을 유지. logical 수는 os.cpus() 기반으로 보존. Nest 전달 모델의 physicalCores/utilizationPercent와 Angular 모델을 정렬.
- UI: Windows `%`만 주값, `물리코어 · 논리스레드`를 보조값으로 표시. OS명/arch 제거. unknown은 `코어 수 확인 불가 · 20스레드`, 논리 수도 없으면 `CPU 구성 확인 불가`. macOS는 기존 `CPU 부하 · 1분 평균`/부하값 유지.
- 검증 RED: Electron 새3테스트 실패(physicalCores 부재), Angular 새/변경3테스트 실패(슬래시와 OS 표시). Angular 첫 시도는 Karma sandbox bind EPERM으로 실행 전 중단, 로컬 실행 권한으로 재시도해 실제 RED를 확인.
- GREEN: Electron CPU **8/8**, Angular Dashboard/ResourceStatus/PluginStatus **42/42**. Electron TypeScript·Nest TypeScript·Angular packaged 빌드 모두 통과. Mac 실제 OS 수집도 **10코어/10스레드** 반환. 최초 sandbox sysctl 차단 때 undefined fallback 유지됨을 확인하고 읽기 권한으로 실제 조회를 재확인했다.
- CUA 실제 컴포넌트: 모의 Windows12/20·21.3%의 다크/라이트 화면과 코어 조회 실패 표시 확인. 별도 소스 복사본 `/private/tmp/clipper-resource-dashboard-smoke`를 사용해 실제 API·플러그인 연결 없이 검증. 탭/59344 서버 정리 완료. 원격 Windows CIM 실제12/20 조회 및 새 설치 파일 검증은 남음.
- 독립 코드 검토: actionable finding 없음. 새 cache 만료/동시호출의 별도 테스트, 실제 Windows CIM 실행은 이번 증거에 포함하지 않는다. 실제 코드 경계·timeout/캐시/다중소켓/fallback은 검토했다.
- 로그 `/private/tmp/clipper-resource-review-{red,green}-{electron,angular}.log`, `clipper-resource-review-{electron,nestjs,angular}-build.log`. 이미 성공한 과거 웹 전체 테스트는 새 변경이 없어 반복하지 않았다.
- **새 변경은 3개 repo/7개 파일(Electron2·Angular4·Nest1), 미커밋·미푸시·미배포.** 이 요청의 과거 배포 감사와 새 CPU 개선 단계를 구분한다. 이후 반영 시 앱 소스 커밋·push → 새 릴리즈 source snapshot → 새 Windows 설치 파일 빌드/설치가 필요. 이번 변경 때문에 웹/API·DB migration은 필요하지 않다.

## 6. 대시보드 전체 점검 결과와 다음 단계

[리소스 관리 검토](./2026-09-10-plugin-resource-management-review.md)에 현재 watcher/정리 조건·CPU/RAM/GPU/프로세스 표시·종료 정책·기존 테스트 범위·정확한 재현과 우선순위를 기록했다.

- **수정 완료:** 위 CPU 카드/물리 코어 수집만. 아직 새 코드 commit/push/deploy 전.
- **결함 재현 완료·구현 전:** TTS active 누락, 발화한 timer와 새 작업 경합, 취소의 공용 runtime 종료, job 실행의 admission 우회. 기존 순수 lifecycle8/stop2는 통과하지만 새4케이스에서 결함을 재현했다.
- **정적 감사 완료·실기 전:** Windows 자손 프로세스 종료 보장 부족, local모드 pressure 후보 없음, GPU60초cache, UI idle 미확인/강제batch-stop/조회실패·갱신 중첩 표시 문제.
- **설계/구현 전:** 지속적인 pressure watchdog. 기존 화면 polling과 혼동하지 않는다. 먼저 실행 소유권·안전한 조건부 정리·공통 admission을 수정하고 그 위에 watch를 붙이는 순서를 권장한다.
- UI 권장 후속: 가용 RAM·작업 수/보호 사유·상태 갱신 여부·정리 이유/결과·GPU별 사용량·빈 상태/오류 안내. 화면만 바꿔 안전성이 확보된 것처럼 표현하지 않는다.
- 실제 플러그인 QA 및 Build5 HOLD는 계속 유지. 이번에 미구현 리소스 결함을 전부 해결했다고 보고하지 않는다.
