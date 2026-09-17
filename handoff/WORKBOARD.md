# 작업 현황판

## 최신 실기: 독립 개발판 로그인·필수 템플릿 이관

새 macOS 개발판의 실제 Google 로그인·무료 체험/access/credit 표시를 사용자 확인했고, 필수 `.cliptpl` 이관 중 기본 제공 16개가 중복 복제되는 결함을 발견·수정했다. 옛 17개 번들 재가져오기 후 기본16+사용자1=총17, 잘못된 복제본0, 내보내기 사용자 템플릿만 표시를 UI와 로컬 API에서 확인했다. Angular `19b407a7`, Nest `884fa8bc` 로컬 커밋, 두 repo clean/ahead1. Nest build·대상69·전체 suite exit0, Angular 대상31·전체4,494 PASS. [상세 결과](../implementation/2026-09-17-template-transfer-dedup-validation.md). push·추가 병합·배포·원격 DB 변경 없음. W09의 Mac 필수 템플릿 이관은 완료했고 Windows 실기와 선택 데이터 이관은 남는다. 다음 주 작업축은 W04 남은 비-ML 로컬 PG acceptance이며 이후 개발 DB 복제본 rehearsal이다. 실제 ML/Build5 HOLD 유지.

## 최신 사용자 조건: 개발판 독립 분리 설계

DB 최신 단계: 사용자 로컬 실행 승인 후 새 58433–58435의 `clipper-identity-check-20260917-*` 3개 생성, migration 및 실제 DB **9 PASS**. 새 컨테이너는 정상 중지·전용 볼륨 보존. 기존 dev/오늘 로그인 DB와 실 env/원격 서버는 변경 없음. [결과·미완료 실기](../implementation/2026-09-17-independent-dev-real-db-validation.md). 다음은 실제 앱용 환경 범위 확인 후 재패키징/Google/동시 실행/템플릿 이관. 아래 DB 승인 대기 표현은 이전 체크포인트.

2026-09-17 후속: 앱 identity·로그인 결속 후 release API/runner/Admin Task 1–3 코드·자동 검증 완료. **Web API build/2,882 PASS·21 SKIP, Infra 51 PASS·1 SKIP, Admin build/50 PASS.** [최신 결과·리뷰·남은 작업](../implementation/2026-09-17-independent-dev-release-validation.md). Electron은 이번에 수정하지 않았으며 이전 build/975 PASS 기록 유지. 다음은 **새 격리 DB 대상과 영향 제시→별도 승인→nullable migration/실제 트랜잭션 검증**, 이어 새 설치본 Google 로그인·동시 실행·필수 템플릿 export/import 실기. 실제 환경파일·DB·앱 재패키징/기동·커밋/푸시/병합/배포 변경 없음. Electron/API/Infra/Admin/문서 미커밋이며 아래 clean/구현 전 표현은 과거 단계다. Mac 공개·자동빌드·업데이트 HOLD, ZIP 제외, ML/Build5 HOLD 유지. 주간 잔여 96% 기록, reset credit 사용 없음.

새 개발판 빈 데이터 허용, 템플릿 이관 필수(.cliptpl 기존 기능 우선), 소재/프로젝트 보존은 선택. 기존 개발 앱 대치/데이터 경로 유지 필수 아님. 운영/새 개발판 Mac·Windows 동시 실행과 데이터 격리 필수, 옛 개발판이 남거나 재실행돼도 새 로그인 연결 영향 금지. 자동 옛 앱 탐색/삭제를 안전성 전제로 삼지 않는다. `ai.clipperstudio.dev` / `clipperstudio-dev` / `Clipper Studio Dev` / 채널 `dev` 및 연결 변경 범위 승인 후 조사·세부 계획 작성 완료. [정확한 값·변경 경계·검증 설계](../implementation/2026-09-17-independent-dev-identity-design.md), [작업카드](tasks/app-window-name.md) 참조. 아래 identity 유지 방침은 과거 구현 기록이다.

## 2026-09-17 macOS 개발 앱 로그인 실기 후속

사용자가 새 개발 앱 이름·실제 Google 로그인·무료 체험 400 표시를 확인했다. 옛 개발 앱으로 향하던 OS 기본 핸들러를 등록 정리 후 새 빌드로 변경했고 브라우저 앱 열기 이름도 사용자 재확인 완료. 파일/DB 삭제 없음. 단, 구·신 개발 앱의 파일명 차이로 /Applications에서도 공존하므로 일반 배포의 교체·중복 설치·인스턴스별 로그인 복귀 설계와 실기는 미완료다. [진단 명령과 후속 검증 목록](../implementation/2026-09-17-macos-dev-oauth-handler-validation.md), [앱 이름 카드](tasks/app-window-name.md)를 따른다. 이 상태는 아래 실제 Google 로그인 대기 표현보다 우선하며 제품 코드 변경·배포는 없다.

최종 확인: **2026-09-17 KST**. 이 문서는 여러 세션에 걸친 작업의 **현재 상태와 재개 위치**를 찾는 시작점이다. 행 순서는 우선순위가 아니다. 사용자 선택 없이 마지막 작업을 전체 프로젝트의 다음 작업으로 지정하지 않는다.

## 작업 목록

| ID | 작업 | 상태 | 다음 행동 / 상세 인계 |
|---|---|---|---|
| W01 | 대사 하이라이트 개선 | 감사·5worktree 준비 이후 | [최신dev 대조 후 개선 범위 결정](tasks/dialog-highlight.md) |
| W02 | 밈 오버레이·seek | 사용자 작업 보존 | [기존 수정·추가요구 확인](tasks/meme-overlay.md) |
| W03 | 카드사 심사·임시 운영 | 심사 결과 대기 | [결과 후 기존운영 복원 또는 integration 배포](tasks/pg-card-review.md) |
| W04 | 운영·dev 통합 | 원본8repo dev 최신·clean. 통합8repo push 완료·원격 SHA 일치·clean. 설치형 실기 남음 | [최신 Git 결과](../implementation/2026-09-17-integration-commit-proposal.md) · [상세 인계](tasks/integration.md) |
| W05 | CPU·리소스 안전성 | 구현·원격보존 완료, 실기 HOLD | [Windows/Build7 증거·SDK조건 확인](tasks/resource-safety.md) |
| W06 | 정식PG·운영 구축 잔여 | 기록상 미완료, 최신성 확인 | [환불/구독/웹훅·runner/운영 항목 선택](tasks/pg-production-followups.md) |
| W07 | 스토리보드 후속 | 8월기록, 재확인 필요 | [TODO와 최신코드 대조](tasks/storyboard.md) |
| W08 | 기타 장기보류 후보 | 재평가 대상 | [첫실행UX·stdout·보안·쇼츠분석 등](tasks/historical-backlog.md) |
| W09 | 운영·개발 앱 표시 이름·독립 개발판 | Mac 실제 로그인·무료체험/access/credit 및 필수 템플릿 이관 PASS. 중복 방지 Angular/Nest 로컬 커밋 완료·미push. Windows/선택 데이터 실기 남음 | [템플릿 실기](../implementation/2026-09-17-template-transfer-dedup-validation.md) · [다음 단계](tasks/app-window-name.md) |

## 공통 작업 공간과 보존

최신 checkout 결정: 사용자 승인으로 원본8repo가 모두 `integration/dev-pg-local-validation-20260917`이며 clean, origin 통합 참조와 0/0이다. 원본 폴더에서 다음 검증을 수행한다. 기존 통합8worktree는 동일 SHA detached로 유지, dev 브랜치 참조는 변경하지 않았다. 기존 ignored 환경파일11개 해시 불변. Nest `.env.local` 비-loopback DB 설정·실행 환경 로딩과 의존성/산출물 확인이 다음 단계다. 기존 통합 Nest cwd의 Node4프로세스는 건드리지 않았으며 새 기동 전 포트/소유권 확인 필요. 아래 원본dev 표현은 전환 전 기록이다.

옛 PG 보완은 Nest `000414f`·Web API `3c33268`로 커밋·push·원격 SHA 확인 후 두 fix worktree 제거 완료. 앱 이름 feature `7aed9f6`도 push 완료했고 해당 worktree는 유지했다. 로컬/원격 브랜치와 커밋은 보존, 재병합 없음. [최종 정리 결과](../implementation/2026-09-17-old-pg-worktree-disposition.md)를 따른다.

최신 push 상태는 위 W04와 최신 Git 결과를 따른다. 아래 커밋 시점의 “원본 유지/코드 push 없음”은 후속 사용자 승인 이전 기록이다. 문서 작성 위치는 사용자 지시에 따라 `.codex`로 한정하며 잘못 추가한 `clipper_docs` TODO는 이동 완료했다.

- 사용자 PC 원본8repo(`desktop/*`4, `web/*`4)는 dev와 clean. 사용자 명시 요청 후 Angular를 `98d449584055b324f223678f058e255c7d464c80`, Nest를 `4c32e03c327003e85ec5da248e362d4e85b49fb7`로 fast-forward pull했다. 원본8repo 모두 origin/dev와 0/0이다.
- integration/main-unification-20260911은 8repo 원격보존. recovery/resource-safety-20260915는4repo 원격보존. 두 작업의 중복worktree 제거 완료.
- 정식 PG 통합 결과는 `.worktrees/dev-pg-local-validation-20260917/`의 8개 저장소별 `integration/dev-pg-local-validation-20260917` branch에 있다. Astra R01–R13+A14 및 추가 환급 보완은 사용자 승인 후 Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Web API `8b074a5`로 로컬 커밋했다. fresh 빌드·테스트 통과, 통합8repo clean이며 원본8repo는 기존 dev HEAD 그대로 clean이다. 설치형 실기·잔여 위험 검증 전 전체 로컬 완료로 판정하지 않는다. 옛 feature/PG 보완 및 다른 작업 worktree의 변경은 보존한다. 이번 추가 병합·코드 push·원본 dev 갱신·배포는 없다. `.codex`는 별도 사용자 요청으로 커밋·푸시한다.
- 옛feature/toss-payments-pg-integration, fix/operator-jwt-expiry-test 등 보존branch는 현재할일로 자동승격하지 않는다.
- 원격 상태는 2026-09-17 Astra 감사에서 8repo `git ls-remote`로 dev/integration 참조를 재확인했고 로컬 origin 참조와 같았다. fetch/branch 이동 없이 통합 HEAD가 모두 포함함을 확인했다. 배포 서버 상태는 재조회하지 않았다.
- 앱정리와 별개로 `.codex` 문서변경은 아직 미커밋일 수 있다. 세션 마무리에서 git status 확인.
- 정식 PG 통합용 8repo worktree는 `.worktrees/dev-pg-local-validation-20260917/`이며 각 branch는 `integration/dev-pg-local-validation-20260917`이다. 원본 checkout은 그대로다. 현재 HEAD, 전체 테스트·빌드, 별도 로컬 DB migration, API/Web/macOS 앱 smoke와 한계는 [2026-09-17 최종 로컬 검증 결과](../implementation/2026-09-17-local-pg-integration-validation-result.md)에 기록했다.

## 상태를 읽는 법

- **대기:** 다음 행동은 있지만 사용자 선택/외부 결과를 기다림.
- **HOLD:** 명시적으로 보류. 자동재개 금지.
- **재확인 필요:** 과거 TODO의 최신 유효성 미검증. 미구현이라고 단정하지 않음.
- **보존 완료:** 코드가 남아 있다는 의미. 배포/기능검증 완료와 다름.

## 매 세션의 규칙

1. 이 현황판에서 사용자 요청에 해당하는 작업카드만 우선 읽는다.
2. 실제 branch/HEAD/미커밋과 카드 날짜를 확인한다. 서버실행SHA는 로컬Git으로 추정하지 않는다.
3. 작업 범위·제약을 유지한다. 서버는 사용자가 실행하고 에이전트는 안내만 한다. 실제ML/Build5 HOLD 유지.
4. 새 작업은 재개할 필요가 있을 때만 카드/행을 추가한다. 소규모 변경마다 별도관리체계를 늘리지 않는다.
5. 종료 시 해당카드의 상태/다음행동/검증한계 및 이 표를 함께 갱신한다. [카드양식](tasks/TEMPLATE.md)을 사용한다.
6. 실행명령·결과는 날짜별 session/implementation 기록에 남긴다. 현재카드에 오래된 상태를 계속 덧붙여 충돌시키지 않는다.
7. 다른 작업의 우선순위를 바꾸거나 과거미완료를 자동완료 처리하지 않는다. 커밋·푸시는 사용자 승인 범위에서만 한다.

## 이번 W04 검증 범위

최신 판정은 [취소·삭제 환급 및 Dialog 수정 결과](../implementation/2026-09-17-archive-refund-fix-result.md)다. 사용자 승인 후 삭제 전 확정 가능한 환급 의도/outbox를 보존하고, 옛 params의 attempt ID fallback을 제거해 정확한 owner+job만 사용한다. Dialog는 제품 기본 1초 제한을 유지하고 HTTP 요청/timeout 테스트를 분리했다. 최종 Nest 전체 2,678/2,678, 대상 70/70, Dialog 새 프로세스 20회×11건, 격리 부팅 PASS. 독립 재리뷰 잔여 지적 없음. 다음은 수정본 설치형 로컬 실기이며 Google/Windows는 사용자 실행, ML/Build5 HOLD다. 기존 4repo 미커밋 변경·8repo HEAD·원본 checkout은 보존했다. 새 커밋·push·배포·실제 DB 변경은 없으며 DB 리허설로 자동 진행하지 않는다.

이전 세션은 8repo 통합, 전체/대상 테스트·빌드, 별도 로컬 User/Admin/Release migration, 과거 schema fixture, migration 누락-table guard, dump restore, 로컬 API 정책, Web Client 브라우저, macOS 개발 설치형 앱을 확인했다. 이는 실행한 시나리오의 증거이며 이번 결함을 부정하지 않는다. Windows NSIS, 실제 ML, Build 5 전체 QA, 실제 Toss 결제, 개발 DB 복제본·실제 개발서버 전환은 수행하지 않았다. [이전 로컬 검증 기록](../implementation/2026-09-17-local-pg-integration-validation-result.md) 참조.
