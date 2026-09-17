# 다음 세션 시작 안내

최신 갱신: 2026-09-18 KST.

최신 W04 비-ML 로컬 acceptance: Desktop Nest build 및 과금·outbox·재시작·취소·preflight·process lifecycle 115+41+37 PASS, Angular 과금/recovery/account/projects 202 PASS, Web API build와 대상 61/107/63 PASS, Electron build·전체 975 PASS. 새 폐기 DB `clipper-pg-w04-20260918-*`의 Admin64/Release3/User10 migration과 access/credit 정책 e2e 1 PASS, 모든 tier `entitlement_mode=all` 확인 뒤 컨테이너 중지·전용 volume 보존. 기존 5433–5435/57433–57435와 원격 DB는 변경하지 않았다. 후속 리뷰에서 release 성공 보고의 installer 종류 교차검증과 Windows 최종 package/feed/cache 검증 누락을 보완했다. 운영 package/cache도 사용자 승인으로 `clipper-studio` / `clipper-studio-updater`로 통일했다. 변경 후 Electron build·전체 975, Web API build·전체 2,884 PASS(21 SKIP), Web Admin build·전체 571 PASS, Infra 전체 36 PASS. 사용자 승인으로 Electron `d95c050`, Web API `36b049f`, Web Admin `01d0b93`, Infra `f0af3f5`에 로컬 커밋했고 네 저장소는 clean/ahead1이다. 아직 push·병합·배포하지 않았다. [상세 증거와 남은 게이트](../implementation/2026-09-18-w04-non-ml-local-acceptance.md). 다음은 개발 DB 복제본 rehearsal 전, 설치형 offline/online 경계를 실제 ML 없이 더 실기할지 사용자와 범위를 확인하는 단계다. 실제 ML/Build5, 서버 접속·배포는 HOLD다.

최신 사용자 결정: 옛 개발판의 프로젝트·소재관리·작업 이력을 새 독립 개발판으로 복제하거나 자동 이관하는 기능은 만들지 않는다. 새 개발판은 해당 데이터가 없는 상태로 시작하며, 필수 이관 대상은 이미 실기 완료한 사용자 생성 템플릿뿐이다. 옛 개발판 데이터 루트는 삭제·수정하지 않고 보존하되 새 앱은 읽거나 공유하지 않는다. 폴더 직접 복사·절대경로 치환·owner UUID 재매핑도 수행하지 않는다.

2026-09-18 macOS session 실기 PASS: 로그인 상태에서 앱 완전 종료·재실행 후 동일 계정, 무료 체험, 사용 가능 크레딧 400, 템플릿 17개 유지. 로그아웃 후 종료·재실행에서는 로그인 화면 유지. Google 재로그인 연결창에 `Clipper Studio (dev).app`이 표시됐고 동일 계정·무료 체험·400·템플릿 17개 복원까지 사용자 확인했다. 다음은 W04 남은 비-ML PG 로컬 acceptance다.

최신 실기 완료: 새 독립 개발판에서 실제 Google 로그인·무료 체험 400·계정/access/credit 표시와 필수 템플릿 이관을 확인했다. 옛 번들의 기본 제공 16개가 사용자 복사본으로 중복되는 결함을 발견해 Angular/Nest 양쪽을 보완했고, 중복 16개만 백업 후 정상 API로 제거했다. 같은 17개 번들을 다시 가져온 뒤 **기본 16 + 사용자 1 = 총 17**, 복제본 0, 내보내기에는 사용자 템플릿만 표시됨을 사용자 UI와 로컬 API에서 확인했다. 로컬 커밋은 Angular `19b407a7`, Nest `884fa8bc`; 두 branch는 원격보다 1커밋 앞서며 clean이다. Nest build·대상69·전체 suite exit0, Angular 대상31·전체4,494 PASS. [상세 결과](../implementation/2026-09-17-template-transfer-dedup-validation.md). 코드 push·추가 병합·dev/main 변경·배포·원격 DB 변경 없음. 다음은 남은 비-ML PG 로컬 acceptance, 이후 개발 DB 복제본 rehearsal이다. Windows 실기는 사용자 장비, 실제 ML/Build5 HOLD 유지. 아래 템플릿 실기 대기·코드 미커밋 표현은 과거 체크포인트다.

DB 후속 **승인·실행 완료**: 새 로컬 `clipper-identity-check-20260917-{admin,release,user}` / 58433–58435 / 전용 볼륨에서 migration과 실제 DB 검증 **9 PASS**. User10/Admin64/Release3 및 별도 로컬 production fixture3 migration, 반복 실행 pending 없음. 새 컨테이너 3개는 정상 중지·볼륨 보존. 기존 5433–5435 및 57433–57435는 계속 실행 중이며 SQL/데이터 변경 없음. [실행 결과·다음 단계](../implementation/2026-09-17-independent-dev-real-db-validation.md). 다음은 실제 앱용 로컬 API/DB 연결·환경 설정 범위를 설명한 뒤 새 패키징 앱의 Google 로그인/공존/필수 템플릿 이관 실기다. 실 env·원격 서버·commit/push/deploy 변경 없음. 주간 잔여 95% 기록. 아래 DB 승인 대기/미실행 표현은 이전 체크포인트다.

최신 후속: 앱 identity·로그인 결속에 이어 [release 계획](../implementation/2026-09-17-independent-dev-release-plan.md) Task 1–3(API dev 채널/profile/오게시 방어, runner 산출물 대조, Admin 명시 채널 선택, 배포 예제) 코드·자동 검증 완료. **API build/2,882 PASS·21 SKIP, Infra 51 PASS·1 SKIP, Admin build/50 PASS.** 독립 리뷰의 잠금 순서/direct CLI 플랫폼 검증 지적 수정 후 추가 중요 지적 없음. [최신 실행 결과·남은 게이트](../implementation/2026-09-17-independent-dev-release-validation.md). Electron은 이번에 수정하지 않았으며 이전 build/975 PASS 증거는 [앱 실행 결과](../implementation/2026-09-17-independent-dev-app-validation.md) 참조. 다음은 **새 격리 DB의 정확한 대상·영향을 제시하고 승인받은 뒤** User/Release nullable migration 및 실제 트랜잭션 검증, 이어 새 설치본 Google 로그인/동시 실행/필수 템플릿 이관이다. 실제 `.env`·DB·dist-app/OS 등록 변경 없음. Electron/API/Infra/Admin/문서 미커밋, 새 commit/push/merge/deploy 없음. **Mac 공개·자동빌드·업데이트 HOLD, ZIP 제외**, 실제 ML/Build5 HOLD 유지. 주간 한도 마지막 잔여 96%; reset credit 호출 없음. 재개 시 실제 Git diff와 현재 한도를 다시 확인한다.

현재 요구사항: `ai.clipperstudio.dev` / `clipperstudio-dev` / 데이터 `Clipper Studio Dev` / 업데이트 채널 `dev`. 템플릿 이관은 필수 실기 완료했고 프로젝트·소재·작업 이력 이관은 하지 않는다. [코드 조사 및 연결 변경안](../implementation/2026-09-17-independent-dev-identity-design.md)을 따른다. 아래 개발 identity 유지·실기 대기 표현은 과거 단계이며, 사용자의 과거 Google 로그인 및 무료 체험 400 표시는 이번 독립 전환의 검증 증거로 재사용하지 않는다. 현재 구현 상태는 맨 위 후속과 연결된 실행 결과가 정본이다.

최신 작업 위치: 사용자 승인으로 원본 `desktop/*`, `web/*` 8repo를 `integration/dev-pg-local-validation-20260917`로 checkout했다. 이제 로컬 검증은 원본 폴더에서 한다. 기존 `.worktrees/dev-pg-local-validation-20260917/`는 같은 SHA의 detached HEAD로 보존했다. 원본8repo clean, 환경파일11개 해시 불변, dev 참조 불변. Nest `.env.local`의 비-loopback DB 설정은 실제 사용/로딩 순서 확인 전 실행 금지. 앱 기동·의존성 설치·build·DB 변경은 이번 전환에서 하지 않았다. 아래 원본dev/워크트리 검증 지시는 과거 상태다.

Git 후속 상태: 사용자 승인으로 원본 Angular/Nest dev fast-forward 완료, 원본8repo 최신·clean. 나머지5repo의 정확한 목적지 승인 후 통합8repo push 완료·원격 SHA 일치·clean 확인. 다음은 수정본 설치형 로컬 실기다. [상세 최신 결과](../implementation/2026-09-17-integration-commit-proposal.md)를 아래 이전 단계 표현보다 우선한다. 출시 후 API 호환 TODO는 사용자 지시대로 [`.codex/todos`](../todos/2026-09-16-post-launch-desktop-api-compatibility.md)로 이동했다.

**먼저 [작업 현황판](WORKBOARD.md)을 읽고, 사용자가 선택한 작업카드로 이동한다.** 여러 작업이 병행 중이며 이 파일은 특정 작업을 자동으로 최우선 지정하지 않는다.

1. 사용자 요청과 현황판을 대조한다. 애매하면 후보를 짧게 확인한다.
2. 해당 작업카드의 branch/worktree/HEAD와 실제 Git 상태를 읽기 전용으로 확인한다.
3. 상세 이력은 카드가 연결한 문서만 필요한 범위로 읽는다. 과거 체크박스만으로 새 작업을 만들지 않는다.
4. 서버에는 직접 접속하지 않는다. 서버 명령은 사용자가 실행한다.
5. 실제ML·Build5 전체QA HOLD를 유지한다. 명시된 사용자후속이 있을 때만 범위를 바꾼다.
6. 종료 시 작업카드·현황판·세션기록을 갱신하고 문서의 미커밋 상태를 알린다.

현재 사용자PC 원본8repo는 dev. 통합branch와 복구branch는 원격보존. 운영주소는 임시 카드사심사판이다. 로컬dev와 서버심사판/integration을 혼동하지 않는다.

- [이번 세션 요약](../records/sessions/2026/09/15.md)
- [2026-09-17 Git 정리·코드 커밋 결과](../implementation/2026-09-17-integration-commit-proposal.md): 사용자 승인 후 코드4repo 로컬 커밋 완료, 통합8repo clean. `.codex` 커밋·푸시는 사용자 요청 범위이며 원본 dev 갱신/코드 push는 별도 승인.
- [PG 통합 전 결정·누락 감사](../implementation/2026-09-17-pre-merge-decisions-and-gap-audit.md)
- [Astra 수정·재검증 — 현재 우선 판정](../implementation/2026-09-17-astra-fix-result.md)
- [Astra 독립 재감사 — 수정 전 증거](../implementation/2026-09-17-astra-independent-review.md)
- [PG 로컬 통합·검증 최종 결과](../implementation/2026-09-17-local-pg-integration-validation-result.md)
- [운영 복원 런북](../implementation/2026-09-15-pg-review-production-cutover-and-rollback.md)
- [이전 NEXT 전체 원문](archive/2026/09/next-before-task-board-2026-09-15.md): 기존스토리보드와 이전작업 기록을 삭제하지 않고 보존했다.

W04는 **R01–R13+A14 및 추가 환급 누락·Dialog 테스트 수정 검증·로컬 커밋 후 설치형 로컬 실기 단계**다. [최신 수정 결과](../implementation/2026-09-17-archive-refund-fix-result.md)와 위 커밋 결과를 먼저 읽는다. preparing/queued 취소의 정확한 근거와 환급 outbox를 삭제 전에 보존하고, stale attempt fallback을 제거했다. Dialog는 테스트만 분리했다. 이번 fresh 검증은 Angular 관련226, Electron955, Nest2,678, Web API2,802 PASS와 4repo build PASS다. 새 HEAD는 Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Web API `8b074a5`이며 코드 push·원본 dev 갱신·추가 병합·배포는 없다. 다음은 새 수정본 설치형 앱의 offline/online·재시작·계정전환·환급/잔액 UI 실기다. Google 로그인과 Windows 빌드/설치는 사용자 실행이며 ML/Build5 HOLD 유지. DB 복제본 리허설은 그 뒤이며 dump 명령은 사용자 실행 장비·DB 정보를 확인한 뒤 안내한다. 서버 직접 접속·실제 DB migration·배포 금지와 별도 승인 게이트를 유지한다.
