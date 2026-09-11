# Source Control 저장소·워크트리 현황 — 2026-09-11

사용자 요청: .codex 변경 커밋·푸시, 나머지 저장소/워크트리 전체 조사. 코드 병합·pull·push·삭제·prune는 미승인/미실행. 밈 오버레이와 operator-jwt-expiry-test는 유지한다.

## 핵심 구분

- 원본: desktop/4개 + web/4개. 연결 worktree는 원본의 Git 이력·브랜치 정보를 공유하지만 작업 파일은 별도다.
- `.integration-clones/toss-payments-pg-20260903/` 7개는 별도 clone이다. 원본과 Git 관리 디렉터리도 별도여서 같은 브랜치명이어도 위치가 다르다.
- 모든 숫자는 최신 원격 이력을 별도 감사 bare 저장소에 fetch하여 계산했다. 원본/기존 작업본의 remote-tracking ref는 갱신하지 않아 VS Code 숫자와 다를 수 있다.
- 아래 ↑/↓는 미커밋 파일 수가 아닌 설정된 upstream과의 커밋 차이다. origin/dev를 추적하는 feature/integration 브랜치의 ↑는 운영 미반영 작업을 뜻하지 않는다.
- 별도 clone 7개는 전부 clean이며 HEAD가 현재 운영 브랜치의 조상이다. 이 복제본을 추가 push/pull할 필요는 없다. 삭제하지 않았다.

## 전체 작업 폴더

| 저장소 | 종류 | 경로 | 브랜치 | 비교 대상 | 최신 ↑/↓ | 미커밋 파일 수 |
|---|---|---|---|---|---|---:|
| clipper_angular | original | `/Users/jina/project/adlight/desktop/clipper_angular` | `integration/toss-payments-pg-20260909` | `origin/integration/toss-payments-pg-20260909` | 0/1 | 0 |
| clipper_angular | worktree | `/Users/jina/project/adlight/.worktrees/clipper_angular-meme-overlay-timeline-seek` | `fix/meme-overlay-timeline-seek` | `origin/fix/meme-overlay-timeline-seek` | 0/0 | 0 |
| clipper_angular | worktree | `/Users/jina/project/adlight/.worktrees/clipper_angular-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 0 |
| clipper_angular | worktree | `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_angular` | `feature/dialog-highlight-overhaul-20260904` | `origin/dev` | 0/115 | 0 |
| clipper_angular | worktree | `/Users/jina/project/adlight/.worktrees/production-pg-refresh-20260909/desktop/clipper_angular` | `(detached)` | `(none)` | 없음 | 0 |
| clipper_angular | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_angular` | `integration/toss-payments-pg-20260903` | `origin/dev` | 2/146 | 0 |
| clipper_electron | original | `/Users/jina/project/adlight/desktop/clipper_electron` | `integration/toss-payments-pg-20260909` | `origin/integration/toss-payments-pg-20260909` | 0/2 | 0 |
| clipper_electron | worktree | `/Users/jina/project/adlight/.worktrees/clipper_electron-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 0 |
| clipper_electron | worktree | `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_electron` | `feature/dialog-highlight-overhaul-20260904` | `origin/dev` | 0/84 | 0 |
| clipper_electron | worktree | `/Users/jina/project/adlight/.worktrees/production-pg-refresh-20260909/desktop/clipper_electron` | `(detached)` | `(none)` | 없음 | 0 |
| clipper_electron | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_electron` | `integration/toss-payments-pg-20260903` | `origin/dev` | 1/90 | 0 |
| clipper_infra | original | `/Users/jina/project/adlight/web/clipper_infra` | `integration/toss-payments-pg-20260903` | `origin/integration/toss-payments-pg-20260903` | 0/0 | 5 |
| clipper_infra | worktree | `/Users/jina/project/adlight/.worktrees/clipper_infra-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 0 |
| clipper_infra | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_infra` | `integration/toss-payments-pg-20260903` | `origin/dev` | 7/0 | 0 |
| clipper_nestjs | original | `/Users/jina/project/adlight/desktop/clipper_nestjs` | `integration/toss-payments-pg-20260909` | `origin/integration/toss-payments-pg-20260909` | 0/0 | 0 |
| clipper_nestjs | worktree | `/Users/jina/project/adlight/.worktrees/clipper_nestjs-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 0 |
| clipper_nestjs | worktree | `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_nestjs` | `feature/dialog-highlight-overhaul-20260904` | `origin/dev` | 0/90 | 0 |
| clipper_nestjs | worktree | `/Users/jina/project/adlight/.worktrees/production-pg-refresh-20260909/desktop/clipper_nestjs` | `(detached)` | `(none)` | 없음 | 0 |
| clipper_nestjs | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_nestjs` | `integration/toss-payments-pg-20260903` | `origin/dev` | 4/106 | 0 |
| clipper_python | original | `/Users/jina/project/adlight/desktop/clipper_python` | `dev` | `origin/dev` | 0/2 | 0 |
| clipper_python | worktree | `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904/desktop/clipper_python` | `feature/dialog-highlight-overhaul-20260904` | `origin/dev` | 0/18 | 0 |
| clipper_python | worktree | `/Users/jina/project/adlight/.worktrees/production-pg-refresh-20260909/desktop/clipper_python` | `integration/toss-payments-pg-20260909` | `origin/integration/toss-payments-pg-20260909` | 0/0 | 0 |
| clipper_web_admin | original | `/Users/jina/project/adlight/web/clipper_web_admin` | `integration/toss-payments-pg-20260903` | `origin/integration/toss-payments-pg-20260903` | 0/0 | 7 |
| clipper_web_admin | worktree | `/Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 0 |
| clipper_web_admin | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_web_admin` | `integration/toss-payments-pg-20260903` | `origin/dev` | 22/0 | 0 |
| clipper_web_api | original | `/Users/jina/project/adlight/web/clipper_web_api` | `integration/toss-payments-pg-20260903` | `origin/integration/toss-payments-pg-20260903` | 0/0 | 9 |
| clipper_web_api | worktree | `/private/tmp/clipper-credit-prod-20260910` | `(detached)` | `(none)` | 없음 | 1 |
| clipper_web_api | worktree | `/Users/jina/project/adlight/.worktrees/clipper_web_api-operator-jwt-expiry-test` | `fix/operator-jwt-expiry-test` | `origin/fix/operator-jwt-expiry-test` | 0/0 | 0 |
| clipper_web_api | worktree | `/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `origin/feature/toss-payments-pg-integration` | 3/0 | 1 |
| clipper_web_api | worktree | `/Users/jina/project/adlight/.worktrees/dialog-highlight-overhaul-20260904/web/clipper_web_api` | `feature/dialog-highlight-overhaul-20260904` | `origin/dev` | 0/17 | 0 |
| clipper_web_api | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_web_api` | `integration/toss-payments-pg-20260903` | `origin/dev` | 140/21 | 0 |
| clipper_web_client | original | `/Users/jina/project/adlight/web/clipper_web_client` | `integration/toss-payments-pg-20260903` | `origin/integration/toss-payments-pg-20260903` | 0/6 | 10 |
| clipper_web_client | worktree | `/Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration` | `feature/toss-payments-pg-integration` | `(none)` | 없음 | 2 |
| clipper_web_client | clone | `/Users/jina/project/adlight/.integration-clones/toss-payments-pg-20260903/clipper_web_client` | `integration/toss-payments-pg-20260903` | `origin/dev` | 32/0 | 0 |

## 사용자 지정 브랜치

- `fix/meme-overlay-timeline-seek`: Angular 연결 worktree, clean, 최신 원격 같은 이름과 HEAD 9568f436 일치. 보존.
- `fix/operator-jwt-expiry-test`: Web API 연결 worktree, clean, 최신 원격 같은 이름과 HEAD a1d91b61 일치. 보존.
- `feature/toss-payments-pg-integration`: Python 제외 **총7개** 연결 worktree다. 사용자 열거6개 외 Web Client도 있다. 같은 이름의 원격 브랜치는 Web API에만 있다. 다른6개는 현재 같은 이름의 원격/추적 대상이 없다(과거 푸시 여부를 뜻하지 않음).
- Web API old PG ↑3: `7a0d7fd` phase4 billing/refund checkpoint, `2d93338` 최종 환불/요금제 변경 정책, `4ef2268` BILLING_DELETED 정확한 키 상태 테스트. 세 커밋 모두 현재 운영 release의 조상이다. 같은 옛 원격 브랜치에 미푸시지만 운영 미반영은 아니다. 추가 푸시하지 않았다.
- 옛 PG Web API에는 untracked `docs/api/openapi.yaml.orig` 1개, Web Client에는 `build/d2x_logo.icns`, `build/d2x_logo.ico` 2개가 있다. 다른5개는 clean. 모두 보존.
- 옛 PG Infra/Admin/Client/API HEAD는 현재 운영 이력에 포함된다. 옛 PG desktop3개는 이전 조사처럼 역사 보존/통합 제외. 요금제별 플러그인 제한 복원 안 함.

## dialog-highlight-overhaul의 pull 표시

5개 모두 clean이며 같은 이름의 원격 브랜치는 없다. 설정된 upstream은 **origin/dev**다. 로컬 전용 커밋0, 최신 dev까지 Angular115/Electron84/Nest90/Python18/Web API17커밋 뒤다. 현재 각 운영 브랜치에도 HEAD가 포함된다.

받게 될 내용은 해당 브랜치 이름의 별도 원격 작업이 아니라 이후 dev 전체 변경이다. Angular 저장공간/자동정리/보관함·동의 UI, Electron 통계 전송/개인정보 마스킹/저장공간 IPC, Nest 저장공간/로그 개선, Python TTS 묵음/속도/간격 및 ffmpeg pipe, Web API 데스크톱 통계 수집/검증/보존 처리 등이 포함된다. pull하지 않았다.

## 원본8개와 운영의 거리

원본 모두 미푸시 커밋0(각 설정 upstream 기준). Angular는 동일 운영 브랜치보다1, Electron2, Python은 dev보다2, Client는 동일 integration보다6커밋 뒤다. Nest/Infra는 동일 upstream과 일치한다. API/Admin은 동일 integration20260903 원격과 일치하지만 실제 운영 기준은 release/pg-expiry-20260910으로 각각10/11커밋 앞서 있다.

원본 미커밋: Angular/Electron/Nest/Python0, Admin7, Client10, API9(기존8+compose1), Infra5. 기존 웹 수정의 다수는 최신 운영에 이미 반영된 작업이며 파일을 되덮거나 다시 push 대상으로 취급하지 않는다. CPU/리소스50파일은 별도 `/private/tmp/clipper-resource-dashboard-review/`에서 보존 중이다.

## 추가 정리 후보 — 이번에 제거 안 함

- production-pg-refresh-20260909 desktop4개: Angular/Electron/Nest는 브랜치에 연결하지 않고 특정 커밋을 열어 둔 detached 상태, Python은 integration20260909. 모두 clean이며 현재 운영 이력에 포함된다.
- `/private/tmp/clipper-credit-prod-20260910`: 과거 API 작업용 detached worktree, untracked node_modules 링크 보존.
- Angular/Nest/Python의 6월 임시 worktree는 각2개씩 총6개 디렉터리가 없어지고 Git 등록만 남았다. prune하지 않았다.
- VS Code 표시만 정리한다면 `.integration-clones`와 보관용 `.worktrees` 저장소들을 Source Control의 Close Repository로 닫고, 원본8개와 현재 작업중인 밈/operator만 표시하는 방안을 권한다. 이것은 파일·브랜치 삭제가 아니다. 이번에는 VS Code 설정/표시 변경도 실행하지 않았다.

## .codex 저장 범위

기존 변경79파일: Markdown37, SQL1, patch11, JSON7, log23. 실행 산출물의 기록/패치 보관이며 실제 앱 저장소 커밋/배포와 다르다. 이번 보고서를 추가해 총80파일을 문서 저장소 main에 커밋 대상으로 삼는다. 기존 미푸시25커밋도 정상 fast-forward push에 포함된다. SQL/테스트는 실행하지 않는다. 완료 여부/커밋 SHA는 최종 응답의 Git 결과를 따른다.
