# Next Handoff

최신 갱신: 2026-06-12

이 문서는 다음 세션이 가장 먼저 읽는 압축 인계문이다. 긴 과거 인계는 [archive/2026/05/next-session-prompt-legacy.md](archive/2026/05/next-session-prompt-legacy.md)에 보관한다.

## 2026-06-12 Clipper2 Modal Inventory

Clipper2 앱 전체의 모달/오버레이 사용처를 조사했고, 현재는 추가 교체를 진행하지 않기로 했다. 나중에 공통 모달로 교체할 때는 아래 문서를 먼저 본다.

- [../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)

현재 판단:

- 이미 생성된 숏폼 클립 재생성 확인은 shared confirmation modal 사용 대상으로 남긴다.
- 바로 교체하기 좋은 후보는 Template Builder의 native `window.confirm` dirty-cancel prompt와 템플릿 삭제 확인이다.
- Dashboard admission dialog는 detail rows/badge가 있어 shared modal 확장 후 검토한다.
- ffmpeg/model consent, 숏폼 생성 진행, 템플릿 샘플 렌더, 프로젝트/이미지 preview, 입력 form overlays는 단순 confirmation modal로 교체하지 않는다.

## 2026-06-12 Template Simplification Decision

숏폼 제작 페이지의 템플릿/레이아웃 작업에 들어가기 전, Template Builder와 shortform template 사용 방향이 크게 바뀌었다.

먼저 읽을 문서:

- [../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)

확정 기준:

- 기존 full Template Builder 구현은 단순화 작업 전 archive branch로 보존한다.
- active branch에서는 기존 Template Builder를 simplified model로 직접 교체한다. product-visible full Template Builder route를 병행 유지하지 않는다.
- 새 템플릿은 `main_title1`, `main_title2`, `caption`만 사용한다.
- `sub_title`, `bottom_title`, `logo`는 새 템플릿/숏폼 제작 flow에서 제거한다.
- 메인타이틀은 두 줄 구조를 유지한다.
- 템플릿 하나는 ratio 하나만 가진다. 허용 ratio는 `1:1`, `4:3`이다.
- 기존 official legacy 템플릿은 새 숏폼 제작 템플릿 목록에서 사용하지 않는다.
- 숏폼 제작 페이지의 `레이아웃` 섹션은 `템플릿`으로 바꾸고, ratio 선택과 타이틀 체크박스는 제거한다.
- 선택한 템플릿의 ratio가 preview와 최종 render payload/recipe를 결정한다.
- 새 preview는 legacy still preview가 아니라 timeline preview여야 한다. 재생/seek, TTS, BGM, media, main title lines, caption overlay가 필요하다.
- 브라우저 preview만으로 FFmpeg/Python 최종 렌더와 pixel-identical 보장은 불가능하다. 빠른 interactive preview와 render-engine confirmation preview를 분리하는 hybrid 방향을 기준으로 한다.

## 2026-06-11 Latest Product Terminology Decision

2026-06-10의 `workspace -> project` 정정 이후, 2026-06-11에 사용자-facing 제품 용어 기준을 다시 확정했다.

먼저 읽을 문서:

- [../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
- [../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)

확정 기준:

- 유저가 알아야 하는 핵심 개념은 `플러그인`과 `프로젝트` 두 개다.
- 플러그인은 스토어에 보이는 설치/실행 단위다.
- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 독립된 사용자 플러그인이다. 하나의 shortform 플러그인 안의 입력 모드로 취급하지 않는다.
- 프로젝트는 플러그인을 열어 사용자가 만들기 시작한 작업물이다.
- 큐에 들어가는 사용자 단위도 프로젝트이고, 완료 후 보관함/프로젝트 페이지에 남는 단위도 프로젝트다.
- `workflow`, `job`, `pipeline`, `runtime`, `worker`는 유저에게 노출하지 않는다. 기존 코드와 기술 문서에서 현재 구현을 설명할 때만 쓴다.
- `Plugin catalog`는 개발자 입장에서 플러그인 목록의 원본 데이터/registry를 뜻한다. 사용자 플러그인 목록과 숨김 runtime worker 목록을 분리해야 한다.
- `clipper1_video_render`는 유저가 직접 여는 플러그인이 아니라 숏폼 플러그인들이 의존하는 hidden `RuntimeWorker`다.
- `task`라는 단어는 신규 제품/문서 용어로 쓰지 않는다. 내부 실행 기록은 `ProjectRun`, worker 원본 진행은 `RuntimeProgress`, 사용자 표시 진행은 `ProjectProgress`/`ProgressStep`으로 구분한다.
- 하이라이트 분석 진행 단계는 유저에게 자세히 보여줄 수 있다. 예: `문장 위치를 영상과 맞추고 있습니다`.
- 숏폼/ffmpeg 렌더 세부 단계는 유저에게 그대로 보여주지 않는다. `영상 생성 중`, `영상 생성 완료`, `영상 생성 실패`처럼 단순화한다.
- 목표 구조는 `/jobs` 중심이 아니라 Project-first다: `Project 생성 -> ProjectRun 생성 -> 큐 대기/실행 -> 같은 Project 상태/결과 갱신`.
- 기존 `/jobs`, `VideoRenderJob`, Python runtime `/jobs`는 당장 삭제하지 않고 compatibility/internal 실행 계층으로 다룬다.
- Project-first 구현 계획은 Project-first facade를 추가하는 방식이다. 전역 `WorkflowExecutor` rename이나 `/jobs` 삭제는 첫 구현 범위가 아니다.
- 단, Project-first / Plugin / Queue 모델 변경은 아직 시작하지 않았다. 현재 진행 순서는 먼저 shortform legacy UI/pre-render parity를 끝내고, 그 다음에 Project-first / Plugin / Queue 정리를 시작하는 것이다.

2026-06-10 기준 주요 repo 확인:

```text
.codex:           clipper1-input-workflow-docs @ 77dcb9c docs(shortform): add phase 3 session handoff
clipper_angular:  work/clipper1-input-workflow-split @ 993efb2 refactor(shortform): use project terminology
clipper_nestjs:   work/clipper1-input-workflow-split @ 8ac76d5 refactor(shortform): rename workspace state to project
clipper_python:   main @ 535131c Render sample images as cover
clipper_electron: main @ f701677 Revert "Update electron builder"
```

2026-06-11 `.codex` 문서 작업 시작 시 기존 `implementation/*` 삭제 상태가 이미 있었다. 이 삭제들은 이번 용어 문서 작업에서 만든 변경이 아니므로 임의 복구하지 않는다.

2026-06-11 후속 shortform legacy parity 구현 이후 로컬 확인 기준:

```text
clipper_angular:  work/clipper1-input-workflow-split @ 8d9d0a5 Fix shortform legacy font sizing
clipper_nestjs:   work/clipper1-input-workflow-split @ 06e3123 Implement shortform clip generation providers
.codex:           clipper1-input-workflow-docs @ 3594f97 Merge branch 'project-first-plugin-queue-docs' into clipper1-input-workflow-docs
```

`clipper_angular`와 `clipper_nestjs`는 이 확인 시점에 working tree가 clean이고 tracking branch 대비 ahead 표시가 없었다. `.codex`는 이 문서 갱신 전까지 clean이었다.

## Current Execution Order

현재 합의된 작업 순서:

1. 숏폼 제작 레거시 UI/pre-render parity 먼저 완료.
   - 기준: `work/clipper1-input-workflow-split`
   - 유지: 세 shortform 플러그인 분리, `workspace -> project` 정정, 현재 NestJS shortform API
   - 목표: `adlight_angular` 레거시 UI/스타일/영상 생성 전 동작과 동일하게 맞추기
   - 금지: 큐/프로젝트/잡 모델 대수술, render/queue 연결, `/projects` navigation
2. 그 다음 Project-first / Plugin / Queue / terminology 정리.
   - 큐에 들어가는 유저 단위를 Project로 정리
   - `/projects`, `/jobs`, `VideoRenderJob`, plugin catalog, ProjectRun, ProjectProgress 정리
   - Angular Project card와 archive/queue 표시 모델 정리

2번은 아직 구현하지 않았다. 현재 작성된 Project-first 문서는 다음 단계 계획서이며 완료 기록이 아니다.

## 2026-06-11 Shortform Legacy Port State

이번 세션에서 완료/반영된 것:

- `.worktrees` 임시 작업 공간은 필요한 변경 반영 후 제거했다.
- `clipper_nestjs/.clipper_data/`는 로컬 NestJS runtime data로 확인했고 gitignore에 추가했다. packaged app runtime data는 macOS 기준 `/Users/jina/Library/Application Support/Clipper2` 아래에 저장되는 것이 기준이다.
- `shortform_url`, `shortform_paste`, `shortform_prompt`는 계속 별도 user-visible plugin이다.
- Shortform editor는 Clipper2 shell 안에서 열리며, 왼쪽 Clipper2 sidebar가 유지된다.
- Plugin Store는 카드 클릭 후 오른쪽 detail panel에서 플러그인을 여는 기존 Clipper2 동작으로 복구했다.
- Legacy Clipper1 shortform UI/assets/styles를 Clipper2 shortform editor에 가져왔다.
- Legacy reset/common/edit CSS가 Store/Dashboard/Projects/Template Builder에 영향을 주지 않도록 shortform editor scope로 분리했다.
- Legacy `.actions` CSS와 Store detail action 영역 충돌을 수정했다.
- Clip drag/drop, subtitle drag/drop, subtitle hover action 잔상 개선, clip drag 중 scrollbar 생김 방지를 반영했다.
- Shortform clip-generation modal은 NestJS WebSocket event로 갱신한다. Clipper2 pre-render clip generation은 SSE를 쓰지 않는다.
- NestJS shortform clip generation은 normal path에서 고정 dummy data를 쓰지 않고 configured LLM script provider, Naver Clova TTS, Naver image search를 사용한다.
- `숏폼 생성하기`는 아직 Phase 1 boundary 그대로다. legacy video-create payload를 console log만 하고 render/queue/navigation은 호출하지 않는다.
- Shortform left panel font-size 깨짐은 scoped px CSS variables로 수정했다. legacy global `html { font-size: 62.5%; }` reset은 재도입하지 않았다.

검증 완료:

- Angular focused tests passed.
- Angular build passed.
- NestJS build passed.
- NestJS shortform/WebSocket event tests passed.
- Browser computed style check: shortform left panel tab `16px`, input `13px`, button `16px`, root `html` `16px`.

알려진 gap:

- Full Angular suite에는 기존 Template Builder snapshot 계열 실패가 남아 있었다. `layoutImage` undefined 관련으로, 이번 shortform parity 작업 범위에서는 수정하지 않았다.

다음에 우선 볼 것:

- 실제 브라우저/Electron에서 Plugin Store -> shortform plugin 선택 -> detail panel -> 열기 플로우를 세 플러그인 모두 확인한다.
- URL/prompt/paste 입력, clip-generation modal stage progression, generated clip card, thumbnail fallback, TTS/BGM controls, title/logo/style controls, preview panel을 legacy `adlight_angular` 기준으로 비교한다.
- 모달 첫 단계는 `텍스트 분석`부터 켜져야 한다. 이후 단계는 backend WebSocket event로 진행되어야 한다.
- `숏폼 생성하기`는 계속 log-only인지 확인한다. render/video/queue request와 `/projects` navigation이 있으면 Phase 1 scope violation이다.
- local/devapp/packaged mode별 LLM/Naver Clova TTS/Naver image env 로딩을 정리하고, 누락 시 앱에서 이해 가능한 에러를 보여주도록 개선한다.
- packaged app에서 runtime data path, bundled env, WebSocket delivery, provider availability를 별도로 검증한다.
- UI/pre-render parity가 사용자에게 승인된 뒤에만 Project-first / Plugin / Queue 정리를 시작한다. 실제 video generation과 queue/archive 연동은 그 다음 단계로 다룬다.

## 먼저 읽기

1. [../README.md](../README.md)
2. [../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
3. [../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)
4. [../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
5. [../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)
6. [../README.ARCHITECTURE.md](../README.ARCHITECTURE.md)
7. [../README.RUNTIME.md](../README.RUNTIME.md)
8. [../README.OPERATIONS.md](../README.OPERATIONS.md)
9. [../operations/env-runtime/README.md](../operations/env-runtime/README.md)
10. [../operations/windows-packaging/README.md](../operations/windows-packaging/README.md)
11. [../features/template-builder/README.md](../features/template-builder/README.md)
12. [../features/dance-highlight/README.md](../features/dance-highlight/README.md)
13. [../features/clipper-studio/README.md](../features/clipper-studio/README.md)
14. [../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port.md](../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port.md)
15. [../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port-plan.md](../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port-plan.md)
16. [../design/TEAM_ARCHITECTURE_OVERVIEW.md](../design/TEAM_ARCHITECTURE_OVERVIEW.md)
17. [../design/TEAM_DEVELOPMENT_GUIDE.md](../design/TEAM_DEVELOPMENT_GUIDE.md)
18. [../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
19. [../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
20. [../design/CLIPPER2_INFRA_EASY_GUIDE.md](../design/CLIPPER2_INFRA_EASY_GUIDE.md)
21. [../design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md](../design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md)
22. [../design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md](../design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md)
23. [../records/sessions/2026/06/12.md](../records/sessions/2026/06/12.md)
24. [../records/sessions/2026/06/11.md](../records/sessions/2026/06/11.md)
25. [../records/sessions/2026/06/08.md](../records/sessions/2026/06/08.md)
26. [../records/sessions/2026/06/05.md](../records/sessions/2026/06/05.md)
27. [../records/sessions/2026/06/02.md](../records/sessions/2026/06/02.md)
28. [../records/sessions/2026/06/04.md](../records/sessions/2026/06/04.md)
29. [../records/sessions/2026/05/29.md](../records/sessions/2026/05/29.md)
30. [../records/sessions/2026/05/27.md](../records/sessions/2026/05/27.md)

## Historical Repo Heads

최신 2026-06-10 repo 기준은 위 `2026-06-11 Latest Product Terminology Decision` 섹션을 우선한다. 아래 내용은 과거 세션 기록이다.

2026-06-11 로컬 세션에서 직접 재확인한 기준:

```text
clipper_angular: work/clipper1-input-workflow-split @ 993efb2 refactor(shortform): use project terminology
clipper_nestjs:  work/clipper1-input-workflow-split @ 8ac76d5 refactor(shortform): rename workspace state to project
```

위 두 브랜치가 shortform plugin split과 최근 project terminology 정정을 포함하는 현재 기준이다. `feature/initial-scaffold`로 돌아가면 필요한 변경이 너무 많이 사라진다.

2026-06-04 로컬 세션에서 문서 수정 전에 직접 재확인한 이전 기준:

```text
clipper_angular:  main @ 70d6e58 Improve template sample render flow
clipper_nestjs:   design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch
clipper_python:   main @ 535131c Render sample images as cover
clipper_electron: main @ f701677 Revert "Update electron builder"
clipper2-codex:   workflow-executor-design @ 31e2ce0 docs: document Clipper infra initial setup (문서 수정 전 기준)
```

세션 시작 시 반드시 각 repo에서 `git status -sb`와 `git log -1 --oneline`을 다시 확인한다. `.codex`는 별도 git repo다.

2026-06-02 기준 추가 확인:

```text
clipper_infra:      feature/infra-initial-setup @ 8226879 feat: add Clipper infra initial setup
clipper_web_admin:  main, no commits yet; origin/main gone
clipper_web_api:    main, no commits yet; origin/main gone
clipper_web_client: main, no commits yet; origin/main gone
```

`clipper_web_admin`, `clipper_web_api`, `clipper_web_client` 3개 repo는 생성/클론만 된 상태로 확인됐다. `git log -1 --oneline`은 첫 커밋이 없어 실패하는 것이 정상이다.

2026-06-04 로컬 세션에서도 위 앱 repo/infra repo 상태를 재확인했다. `clipper_web_admin`, `clipper_web_api`, `clipper_web_client`는 여전히 첫 커밋이 없다.

2026-06-05 기준 추가 확인:

```text
clipper_infra:      feature/infra-initial-setup @ 49faa91 feat: split Clipper DB stack into user admin release
clipper_web_admin:  main @ fef456a feat: add minimal web admin scaffold
clipper_web_api:    main @ ec13be7 feat: add minimal web API scaffold
clipper_web_client: main @ 791c935 feat: add minimal web client scaffold
```

위 4개 repo는 commit/push 완료됐다. `.codex`의 이전 문서 commit `e09fa2e docs: record Clipper web scaffold and DB split`은 사용자가 직접 push했다.

2026-06-08 기준 추가 확인:

```text
.codex:             workflow-executor-design, contains m2-stage dev deploy documentation; verify latest with git log -1
clipper_infra:      feature/infra-initial-setup @ decdfa0 docs: document Clipper dev server-side deployment
clipper_web_admin:  origin/main @ e21cabe fix: include Angular zone polyfill
clipper_web_api:    origin/main @ 8386865 feat: verify database connections in health checks
clipper_web_client: origin/main @ e2102db fix: include Angular zone polyfill
```

위 5개 repo의 2026-06-08 변경은 commit/push 완료됐다. 이후 m2-stage 서버
세션 시작 당시에는 `/Users/metabuzz/Desktop/project/clipper2` 아래에
`clipper_infra`만 있었고 그 repo도 최신이 아니었다. 그 서버 세션에서
`clipper_infra` pull과 `clipper_web_client`, `clipper_web_admin`,
`clipper_web_api` sibling clone이 완료됐다.

이후 m2-stage 서버 세션에서 위 배치 작업과 real dev service 배포가 완료됐다.
`clipper_web_client`와 `clipper_web_admin`은 Angular blank screen 원인이던
`zone.js` polyfill 누락을 각각 `e2102db`, `e21cabe`로 수정했고, 두 commit
모두 `origin/main`에 push 완료된 것을 로컬에서 `git fetch` 후 확인했다.
`clipper_web_api`는 이후 `8386865`에서 `/healthz`와 `/v1/health`가 세 DB에
`SELECT 1`을 실행하는 readiness check를 갖게 됐다. 이 API commit은
m2-stage에 재배포됐고 dev API health에서 `userConnected`, `adminConnected`,
`releaseConnected`가 모두 `true`로 확인됐다.

DBeaver 관련 주의:

- 사용자가 로컬 Mac mini에서 `192.168.0.7:55203` DBeaver test connection과
  `nc -vz 192.168.0.7 55203`을 시도했지만 timeout이었다.
- 이는 password 문제가 아니라 로컬 Mac mini에서 m2-db LAN IP/port로 TCP
  도달이 안 되는 문제다.
- m2-stage에서는 DB 접근이 되고, dev API health도 세 DB connected를
  확인했다.
- 이후 사용자는 dohit과 같은 편의성을 위해 Clipper dev DB만 임시로 ipTIME
  WAN port forwarding 방식으로 열기로 결정했다.
- 임시 포워딩 규칙:
  - `clipper_dev_user_db` TCP `55203` -> `192.168.0.7:55203`
  - `clipper_dev_admin_db` TCP `55213` -> `192.168.0.7:55213`
  - `clipper_dev_release_db` TCP `55223` -> `192.168.0.7:55223`
- 로컬 DBeaver/로컬 `clipper_web_api`는 `metabuzz.iptime.org:55203/55213/55223`을 사용한다.
- 사용자가 로컬 Mac mini에서 `nc -vz metabuzz.iptime.org 55203/55213/55223`
  성공을 확인했고, 로컬 DBeaver에서도 3개 DB 모두 연결 완료했다.
- 이 방식은 나중에 VPN/SSH tunnel로 교체한다. stage/prod DB ports는 WAN에 열지 않는다.

2026-06-08 세션 마무리 기준 추가 변경:

```text
clipper_infra:      feature/infra-initial-setup @ f0cb1f1 fix: use per-database password envs
clipper_web_admin:  origin/main @ db26f4d chore: move local admin port to 4701
clipper_web_api:    origin/main @ 0eab250 fix: require per-database passwords
clipper_web_client: origin/main @ 7bdaeae chore: move local web port to 4700
.codex:             workflow-executor-design, verify latest with git log -1
```

- 로컬 개발 포트는 web `4700`, admin `4701`, API `43203`이다.
- API DB env는 URL 3개 방식에서 split 변수 방식으로 바뀌었다.
- app DB password는 DB별 변수로 관리한다:
  - local API: `USER_DATABASE_PASSWORD`, `ADMIN_DATABASE_PASSWORD`, `RELEASE_DATABASE_PASSWORD`
  - m2-stage app env: `CLIPPER_USER_DATABASE_PASSWORD`, `CLIPPER_ADMIN_DATABASE_PASSWORD`, `CLIPPER_RELEASE_DATABASE_PASSWORD`
- `CLIPPER_DATABASE_PASSWORD` 하나짜리 공통 password 변수는 default/example shape에서 제거됐다.
- `clipper_infra/scripts/deploy-dev.sh`는 이제 실행 초기에 `clipper_infra`를 pull하고, infra가 업데이트되면 새 스크립트로 다시 실행한다.
- m2-stage의 실제 `clipper_infra/env/stack.dev.env`는 git-tracked 파일이 아니므로 직접 per-DB password split 변수 형식으로 바꿔야 한다. secret 값은 채팅/로그에 출력하지 않는다.

### Main Branch Consolidation Notes

아래는 2026-05-29 main branch consolidation 당시의 히스토리 설명이다. 2026-06-02 직접 확인 기준으로 `clipper_python`은 `main...origin/main` ahead/behind가 `0/0`이다.

- `clipper_nestjs`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 3커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_electron`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 1커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_angular`
  - 로컬 `main`을 `feature/initial-scaffold`에서 생성했다.
  - 현재 `main`과 `feature/initial-scaffold`는 같은 commit이다.
- `clipper_python`
  - 기존 `main`은 `origin/main`의 `1e94974 Initial commit`에 머물러 있었다.
  - 로컬 `main`을 `feature/windows-packaging`까지 fast-forward했다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이고, `feature/plugin-architecture` 변경도 포함한다.
  - 그래서 `git status -sb`는 `main...origin/main [ahead 103]`로 보인다.
  - 이 `ahead 103`은 미커밋 변경이나 파일 103개가 아니라, `origin/main..main` 범위의 103개 commit이다.
  - Sync/push하면 그동안 feature 브랜치에 쌓인 Python plugin architecture, render worker, Template Builder fixture/render, env/windows packaging 관련 이력이 `origin/main`으로 올라간다.

## Active Decisions

- 사용자-facing 핵심 개념은 `플러그인`과 `프로젝트`다.
- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 독립된 사용자 플러그인이다.
- 큐/보관함의 사용자 단위는 Project다. `/jobs`, `VideoRenderJob`, Python runtime `/jobs`는 내부 실행/호환 계층으로 취급한다.
- 하이라이트 분석 단계 메시지는 유저에게 보여줄 수 있지만, 숏폼/ffmpeg 렌더 세부 메시지는 `영상 생성 중`으로 단순화한다.
- Shortform production의 현재 1차 작업은 strict legacy parity port다.
- `shortform_url`, `shortform_paste`, `shortform_prompt`는 별도 user-visible plugin으로 유지한다.
- 레거시 Clipper shortform UI/스타일/영상 생성 전 동작은 `adlight_angular`와 완전히 동일해야 한다. 차이는 버그다.
- 1차 작업에서 `숏폼 생성하기` 버튼은 legacy `adlight_python` video-create payload를 console log만 한다.
- 1차 작업에서 ffmpeg 호출, render job 생성, queue insertion, `/projects` navigation은 금지다.
- 실행 모드는 `local`, `devapp`, `packaged`.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>` 파일에 optional blank placeholder를 넣지 않는다.
- plugin별 고정 포트는 사용하지 않는다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- Windows packaged build 중 PowerToys `Command Palette`를 끈다.
- `win.asar: false`, electron-builder retry, build script lock handling을 EBUSY 우회로 다시 넣지 않는다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.
- Template Builder sample render는 Angular 버튼/UI, NestJS recipe/assets, Python ffmpeg renderer가 함께 동작한다.
- 샘플 렌더의 콘텐츠 이미지는 콘텐츠 영역을 `cover` 방식으로 꽉 채운다. 빈 여백을 만들지 않고 넘친 부분을 중앙 crop한다.
- root `README.*.md`는 정해진 top-level guide만 둔다.
  - 현재 root README guide: `README.ARCHITECTURE.md`, `README.RUNTIME.md`, `README.FRONTEND.md`, `README.OPERATIONS.md`, `README.DOCS.md`.
  - 팀 설명용/심화 분석 문서는 `design/` 또는 domain folder 아래에 둔다.

## Last Completed Work

- 팀원 온보딩/Notion import용 개발 가이드를 추가했다.
  - `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
  - 구조, repo별 책임, `local`/`devapp`/`packaged` 실행 방법, branch 운영, env 첨부 섹션을 한 문서에 정리했다.
  - 명령어는 팀원이 각자 `PROJECT_ROOT`를 지정해 실행할 수 있게 작성했다.
- NestJS-native workflow도 Plugin Store/job history/start-stop 모델에 통합하기 위한 설계를 추가했다.
  - `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
  - 쉬운 standalone 설명 문서로 `.codex/design/WORKFLOW_PLUGIN_JOB_EASY_EXPLANATION.md`도 추가됐다.
  - 이 쉬운 설명 문서는 전체 문서 인덱스나 다음 세션 필수 읽기 목록에 넣지 않아도 된다.
  - 현재 Python runtime plugin 중심 구조의 한계를 정리했다.
  - `WorkflowExecutor`, executor registry, Python adapter, NestJS-native ffmpeg executor 방향을 정의했다.
  - 작업 브랜치:
    - `.codex`: `workflow-executor-design`
    - `clipper_nestjs`: `design/workflow-executor`
- `clipper_nestjs` `design/workflow-executor`에서 WorkflowExecutor 초기 구현을 진행했다.
  - commit: `ceaa6ab Add workflow executor runtime dispatch`
  - `src/workflows/`에 executor interface, registry, Python adapter, virtual workflow executor, `simple_ffmpeg_transform` NestJS-native executor를 추가했다.
  - `JobsService`는 `PluginHost` 직접 호출 대신 `WorkflowExecutorRegistry`로 dispatch한다.
  - `PluginsService`는 Python, NestJS-native, virtual workflow를 registry 기반 list/status/start/stop으로 통합한다.
  - `PluginManifestView.runtimeKind`를 추가하고 기존 catalog/local manifests에 runtime kind를 명시했다.
  - 검증:
    - `clipper_nestjs npm run build`: passed.
    - `clipper_nestjs npm run bundle`: passed.
    - `clipper_nestjs node --test test/workflow-executor-registry.test.js`: passed (`2 passed`).
    - `simple_ffmpeg_transform` direct executor start smoke: passed locally with `runtimeState=running`.
    - `clipper_nestjs git diff --check`: passed.
- WorkflowExecutor 기준을 기존 아키텍처 문서들에도 반영했다.
  - `README.ARCHITECTURE.md`, `README.RUNTIME.md`
  - `design/TEAM_ARCHITECTURE_OVERVIEW.md`
  - `design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
  - `design/TEAM_DEVELOPMENT_GUIDE.md`
  - `design/BACKEND_ROLE_SPLIT_CURRENT.md`
  - `design/NESTJS_CONTROL_PLANE_REDESIGN.md`
  - `design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
  - `design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
  - `design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
  - `design/CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`
  - `design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
  - `operations/env-runtime/README.md`
- 로컬 앱 repo의 최종 작업 상태를 `main` 브랜치로 모았다.
  - 코드 내용은 새로 수정하지 않았다.
  - `clipper_nestjs`, `clipper_electron`, `clipper_angular`는 없던 로컬 `main`을 생성했다.
  - `clipper_python`은 기존 로컬 `main`을 `feature/windows-packaging`로 fast-forward했다.
  - branch 포함 관계 확인:
    - `clipper_nestjs`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_electron`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_python`: `feature/windows-packaging`가 `feature/plugin-architecture`와 기존 `main`을 포함.
  - 원격에는 아직 push하지 않았다.
- Template Builder sample render UX와 렌더 동작을 수정했다.
  - `clipper_angular` `70d6e58 Improve template sample render flow`
    - 상단 `샘플 렌더` 버튼은 결과 화면을 여는 역할만 한다.
    - 실제 최초 렌더/재렌더는 화면 안의 `렌더 시작` 버튼이 담당한다.
    - 샘플 렌더 화면에는 "이 화면을 닫아도 진행 중인 샘플 렌더는 계속 진행됩니다." 안내를 둔다.
    - 샘플 렌더는 가능한 네 비율을 모두 순차 렌더한다.
    - 플레이어는 shorts 비율로 표시한다.
    - 샘플 렌더 UI를 inspector에서 page header/overlay로 이동했다.
    - 편집 저장 시 사용자 템플릿 카드 썸네일은 저장 당시 선택 ratio를 사용한다.
    - 공식 템플릿 등록 직전에는 4:3 기준 카드 썸네일을 다시 생성한다.
  - `clipper_nestjs` `73c2519 Stage template sample media`
    - 샘플 렌더용 기본 콘텐츠 이미지를 `src/projects/assets/template-builder/sample-media.jpg`로 stage한다.
    - 해당 파일이 없으면 기존 generated PNG fallback을 쓴다.
    - 단색 `layoutImage`도 render layout layer로 전달해 content 영역 밖 흰 배경 문제를 보정했다.
  - `clipper_python` `535131c Render sample images as cover`
    - `effects: [{ type: "none" }]`을 실제로 존중해 자동 팬/줌을 끈다.
    - 샘플/정지 이미지 기본 렌더를 `contain + pad`가 아니라 `cover + crop`으로 변경했다.
    - 콘텐츠 영역을 꽉 채우고 넘친 부분은 중앙 crop한다.
- 검증:
  - `clipper_angular`: targeted tests `220 SUCCESS`, page-only `60 SUCCESS`, `npm run build` passed, `git diff --check` passed.
  - `clipper_nestjs`: `npm run build` passed, render payload targeted tests passed, sample render targeted tests passed, `git diff --check` passed.
  - `clipper_python`: `uv run pytest tests/test_clipper1_video_render_media_looping.py -q` passed (`27 passed`), `git diff --check` passed.
- main branch consolidation 직후 앱 코드 repo는 위 커밋들까지 clean 상태였다. 이후 `clipper_nestjs` `design/workflow-executor`의 WorkflowExecutor 구현은 `ceaa6ab`로 커밋 완료했다.
- 2026-06-02에는 dohit 인프라 참고 문서 3개를 읽고 Clipper2 설치형 앱 인프라를 이해하기 위한 문서를 시작했다.
  - 참고 문서:
    - `/Users/jina/project/dohit-infra/.codex/dohit-infra-easy-guide.md`
    - `/Users/jina/project/dohit-infra/.codex/dohit-infra-technical-guide.md`
    - `/Users/jina/project/dohit-infra/.codex/clipper-infra-recommendations.md`
  - 이해용/기술 문서:
    - `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
    - `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
  - 원칙:
    - dohit은 웹 리워드 서비스라 web/API 서버가 서비스 본체다.
    - Clipper2는 설치형 Electron 앱이라 서버는 다운로드 페이지, 설치파일 저장소, 업데이트 정보, 계정/API/관리자 기능을 담당한다.
    - Electron 설치파일은 Docker infra 서버가 아니라 self-hosted CI runner에서 빌드한다.
    - Windows 설치형 빌드는 code signing 인증서가 설치된 사무실 Windows PC self-hosted runner에서 수행한다.
    - macOS 설치형 빌드는 별도 Mac mini self-hosted runner에서 수행하는 방향이다.
    - 코드 push/main merge만으로 설치파일 release가 되면 안 된다.
    - Windows release는 Windows PC runner에서 `npm run build:app:win:x64`, macOS release는 Mac mini runner에서 `npm run build:app:mac:arm64` 같은 명시적 release build trigger로 실행한다.
    - Windows/macOS release와 version/update metadata는 플랫폼별로 따로 관리한다.
    - 설치파일 저장소는 기존처럼 S3를 유지한다.
    - dev/stage/prod 3환경을 설계한다.
    - stage/prod는 web/API 배포뿐 아니라 stage/prod 설치파일과 update feed를 나누는 문제다.
    - 3대 Mac mini 기본 배치는 proxy/prod app, dev/stage app, DB/backup/monitor다.
    - 문서는 `clipper_infra` repo가 아니라 `.codex`에 둔다.
    - `clipper_infra`에는 2026-06-02 초기 compose/env/runbook 구성을 생성했다.
    - 실제 IP, 도메인, S3 bucket, image tag, DB password는 아직 placeholder다.
    - 검증: dev/stage/prod app compose config, DB compose config, release metadata JSON, monitor JSON passed.
- 2026-06-04에는 다음 실제 서버 세션의 접속지와 첫 환경을 정했다.
  - 첫 서버 Codex 세션은 `m2-proxy`에서 read-only inventory/preflight로 진행했다.
  - 첫 실제 Clipper 배포 대상 환경은 `dev`다.
  - `stage`는 dev health와 DB/backup/proxy route 확인 뒤 진행한다.
  - `prod`는 stage 검증과 release/update feed 정책 확정 전에는 건드리지 않는다.
  - `m2-proxy`는 `192.168.0.2`, NPM은 `/Users/metabeojeu/Desktop/infra/proxy-server`에서 실행 중이다.
  - `m2-stage` 후보는 `192.168.0.23`, `m2-db` 후보는 `192.168.0.7`이다.
  - NPM active dohit route는 access list 없이 설정되어 있고, NPM admin `81`은 `0.0.0.0`에 bind되어 있으므로 ipTIME에서 WAN 공개 여부를 확인해야 한다.
  - Clipper 예약 port는 m2-proxy/m2-stage/m2-db 후보에서 충돌이 확인되지 않았다.
  - `m2-db` preflight도 완료됐다.
  - `m2-db`는 `192.168.0.7`, dohit DB compose는 `/Users/metabuzz/Desktop/project/dohit-infra/database/postgres/docker-compose.yml`이다.
  - dohit DB `55101/55102/55103`은 `0.0.0.0`에 bind되어 있고, 기존 Clipper DB 예약 port `55201/55202/55203`은 충돌이 없다.
  - 2026-06-05 기준 목표 DB 모델은 user/admin/release split이다.
    - user DB ports: dev `55203`, stage `55201`, prod `55202`
    - admin DB ports: dev `55213`, stage `55211`, prod `55212`
    - release DB ports: dev `55223`, stage `55221`, prod `55222`
  - Clipper dev DB는 `CLIPPER_DB_BIND_HOST=192.168.0.7`, source allow `192.168.0.23 -> 192.168.0.7:55203/55213/55223` 방향이 권장된다.
  - `m2-stage` preflight도 완료됐다.
  - `m2-stage`는 `192.168.0.23`, dohit dev/stage compose roots are `/Users/metabuzz/Desktop/project/dohit-infra-dev` and `/Users/metabuzz/Desktop/project/dohit-infra-stg`.
  - dohit dev/stage app ports `42103/43103/42101/43101` are in use, while Clipper app 예약 port `42201/42202/42203`, `42301/42302/42303`, `43201/43202/43203` are free.
  - Split dev DB deployment is complete on m2-db:
    - `clipper-db-user-dev` healthy on `192.168.0.7:55203`
    - `clipper-db-admin-dev` healthy on `192.168.0.7:55213`
    - `clipper-db-release-dev` healthy on `192.168.0.7:55223`
  - m2-stage network verification to all three dev DB ports succeeded.
  - User said not to spend time on dev DB password rotation for this deployment session. Do not print secrets in chat/logs.
  - Clipper web/admin/API Angular 19/NestJS corrections are committed and pushed.
  - m2-stage `stack.dev.env` was created server-locally from `stack.dev.env.example`; secrets were not printed.
  - Real web/admin/API dev services are deployed and healthy on m2-stage.
  - `clipper_infra/runbooks/deploy-db.md` documents deploying the dev DB stack with `docker compose --env-file ../env/db.dev.env -f compose.yml up -d`.
  - `clipperstudio.ai` authoritative DNS is Cloudflare (`adele.ns.cloudflare.com`, `owen.ns.cloudflare.com`), while Hosting.KR is the registrar.
  - m2-proxy/office WAN IPv4 is `112.169.113.138`, but ipTIME reports it as dynamic DHCP.
  - ipTIME DDNS `metabuzz.iptime.org` points to `112.169.113.138`.
  - ipTIME forwards `80/443` to m2-proxy `192.168.0.2`; router remote management is not configured.
  - Existing WAN forwards `55101/55102/55103` go to dohit DB on `192.168.0.7`.
  - Later decision: add temporary WAN forwarding for Clipper dev DB ports `55203/55213/55223` only. Do not add Clipper stage/prod DB ports `55201/55202/55211/55212/55221/55222` to WAN forwarding.
  - Legacy records `api.clipperstudio.ai -> 3.34.33.3` and `demo.clipperstudio.ai -> 121.138.93.3` must not be changed until legacy cutover.
  - Clipper dev records should be `dev.clipperstudio.ai`, `dev-admin.clipperstudio.ai`, `dev-api.clipperstudio.ai`, initially DNS-only.
  - Because the WAN IP is dynamic, prefer Cloudflare CNAME records to `metabuzz.iptime.org`; A records to `112.169.113.138` are acceptable only while the WAN IP remains unchanged.
  - The three dev CNAME records have been created and verified with `dig`; each resolves through `metabuzz.iptime.org` to `112.169.113.138`.
  - Temporary `nginx:alpine` containers on m2-stage verified `42203/42303/43203`.
  - NPM dev proxy hosts were added and external HTTPS checks returned `HTTP/2 200` for all three dev domains.
  - Observed `strict-transport-security: max-age=63072000; preload`; user decided to keep HSTS enabled for dev.
  - Prod web/download target is `clipperstudio.ai`/`www.clipperstudio.ai` after replacing the current Cloudflare Pages holding page.
  - `api.clipperstudio.ai` moves to Clipper2 prod API only after legacy Clipper is retired or cutover is approved.
  - `clipper_infra/proxy/routes.md` and `env/stack.*.env.example` were updated locally to use `clipperstudio.ai` domains and known server LAN IPs.
  - Next step is Clipper web client/admin/API scaffold and dev Docker image preparation.
  - 기록: `.codex/records/sessions/2026/06/04.md`

## Next Work

1. 세션 시작 시 `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python`의 `git status -sb`, `git log -1 --oneline`을 확인한다.
2. 현재 작업 branch 상태를 먼저 정리한다.
   - `.codex`: `workflow-executor-design`, 이번 문서 커밋 이후 clean이어야 한다.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인:
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
   - 필요한 경우 Angular Plugin Store/job start UI에서 `runtimeKind` 표시/버튼 정책 연결.
4. Clipper2 dev/stage/prod 인프라 구현을 이어간다.
   - 먼저 `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`와 `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`를 읽는다.
   - `m2-proxy` read-only preflight는 완료됐다.
   - `m2-db` read-only preflight는 완료됐다.
   - `m2-stage` read-only preflight는 완료됐다.
   - Split dev DBs are deployed and healthy:
     - `clipper-db-user-dev` on `192.168.0.7:55203`
     - `clipper-db-admin-dev` on `192.168.0.7:55213`
     - `clipper-db-release-dev` on `192.168.0.7:55223`
     - DB Compose projects are environment-scoped: `clipper-db-dev`, `clipper-db-stage`, and optional self-hosted `clipper-db-prod`.
     - Prod DB can also be an external PostgreSQL service; in that case DB Compose is not used for prod and app env DB URLs point to the external DB endpoints.
     - DB containers create Postgres databases/users and persistent Docker volumes, not app tables. Tables come from app migrations/seed scripts.
     - `55201/55202/55211/55212/55221/55222` remain closed until stage/prod are ready.
     - m2-stage `nc` verification to `55203/55213/55223` succeeded.
     - User said not to spend time on dev DB password rotation for this deployment session. Do not print secrets in chat/logs.
   - Cloudflare dev route DNS is created.
     - `dev.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - `dev-admin.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - `dev-api.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - legacy `api.clipperstudio.ai`와 `demo.clipperstudio.ai`는 건드리지 않는다.
   - NPM dev proxy hosts are already created.
     - `dev.clipperstudio.ai` -> `192.168.0.23:42203`
     - `dev-admin.clipperstudio.ai` -> `192.168.0.23:42303`
     - `dev-api.clipperstudio.ai` -> `192.168.0.23:43203`
     - HSTS is enabled for dev by user decision.
     - User reported the temporary nginx test containers have already been removed.
     - Public dev domains now route to real m2-stage dev services.
   - 2026-06-08 dev app deployment strategy decision:
     - Use server-side build on m2-stage.
     - Do not use GHCR/registry push for this first dev deployment.
     - Expected m2-stage layout:
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_client`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_admin`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_api`
     - App repos are siblings of `clipper_infra`, not ignored subdirectories inside infra.
   - `clipper_web_api`, `clipper_web_client`, and `clipper_web_admin` 2026-06-08 framework corrections are committed and pushed.
     - `clipper_web_client`: Angular 19 placeholder app, Docker image serves Angular build output with Nginx, latest `origin/main` `7bdaeae chore: move local web port to 4700`.
     - `clipper_web_admin`: Angular 19 placeholder app, Docker image serves Angular build output with Nginx, latest `origin/main` `db26f4d chore: move local admin port to 4701`.
     - `clipper_web_api`: NestJS scaffold with `/healthz`, `/v1/health`, `/v1/info`, and `/v1/releases/latest` 501 placeholder. Latest `origin/main` `0eab250 fix: require per-database passwords` verifies all three PostgreSQL connections with `SELECT 1` and uses per-DB password env variables.
     - m2-stage repo layout is complete under `/Users/metabuzz/Desktop/project/clipper2`.
     - m2-stage server-local `env/stack.dev.env` exists.
     - Real dev services are deployed with server-side built local images.
     - Final containers:
       - `clipper-web-client-dev` healthy on `192.168.0.23:42203->80`
       - `clipper-web-admin-dev` healthy on `192.168.0.23:42303->80`
       - `clipper-web-api-dev` healthy on `192.168.0.23:43203->43203`
     - Final public checks:
       - `https://dev.clipperstudio.ai` shows `C / CLIPPER2 WEB / Coming Soon`
       - `https://dev-admin.clipperstudio.ai` shows `A / CLIPPER2 ADMIN / Coming Soon`
       - `https://dev-api.clipperstudio.ai/v1/health` returns API health JSON
   - 첫 실제 배포 환경 `dev`는 완료됐다. `stage`는 dev app 기능/migration 흐름 확인 후, `prod`는 stage 검증과 승인 후 진행한다.
   - 실제 도메인, 서버 IP, proxy, dev DB 접속정보는 dev 기준 반영됐다. S3 bucket/prefix와 release artifact/update feed 연동은 아직 남았다.
   - dev `stack.dev.env`는 m2-stage에 생성 완료됐다. stage/prod env는 아직 아니다.
   - DB env files are split by environment: `db.dev.env`, `db.stage.env`, and optional `db.prod.local.env`.
   - backup worker는 아직 README placeholder만 있으므로 실제 backup image/script를 결정해야 한다.
   - Detailed session design doc: `.codex/design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md`
5. Clipper2 web/API 후속 구현을 진행한다.
   - 먼저 m2-stage에서 `clipper_infra`를 최신화하고 실제 `env/stack.dev.env`를 per-DB password split 변수 형식으로 수정한다.
   - 그 다음 `./scripts/deploy-dev.sh all`로 최신 infra/app image를 재배포하고 health/browser smoke를 확인한다.
   - `clipper_web_api` migration tooling 결정.
   - user/admin/release DB 첫 schema migration 작성.
   - `/v1/releases/latest` 실제 release metadata 구현.
   - client download/login/signup 실제 페이지 merge 시 dev 배포 반영.
   - admin 운영 기능 범위 결정.
6. Template Builder sample render smoke를 다시 할 경우 아래를 확인한다.
   - 새 템플릿 생성 후 단색/이미지 layout 변경 저장.
   - 샘플 렌더 화면 열기와 `렌더 시작`.
   - 네 비율 모두 생성.
   - 콘텐츠 이미지가 각 ratio의 content area를 빈 여백 없이 꽉 채우는지.
   - content area 밖 layout image 또는 단색 background가 흰색으로 빠지지 않는지.
   - 화면을 닫아도 렌더 진행이 계속되는지.
   - 공식 템플릿 등록 후 카드 썸네일이 4:3 기준인지.
7. Windows packaged smoke가 필요하면 기존 운영 문서 기준을 따른다.
   - PowerToys `Command Palette` off.
   - `.env.local` packaged read/copy 금지.
   - plugin별 env port 나열 금지.

## Next Session Prompt

```text
Using Superpowers.

지금 세션은 Clipper dev web/admin/API 배포 완료 이후의 후속 작업이다.
먼저 아래 상태를 기준으로 현재 repo/server 상태를 확인해줘.

배포 완료된 m2-stage layout:

/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/

현재 기준:
- dev 배포 방식은 server-side build다. GHCR/registry push 방식은 이번 dev 배포에 쓰지 않았다.
- app repo 3개는 clipper_infra와 sibling이다.
- m2-stage `clipper_infra/env/stack.dev.env`는 생성되어 있고 secret 값은 채팅/로그에 출력하지 않는다.
- latest pushed commits:
  - clipper_infra: feature/infra-initial-setup @ f0cb1f1
  - clipper_web_client: main @ 7bdaeae
  - clipper_web_admin: main @ db26f4d
  - clipper_web_api: main @ 0eab250
- clipper_web_client는 Angular 19 placeholder app이고 `zone.js` polyfill 포함 상태여야 한다.
- clipper_web_admin은 Angular 19 placeholder app이고 `zone.js` polyfill 포함 상태여야 한다.
- clipper_web_api는 NestJS scaffold이고 `/healthz`, `/v1/health`에서 세 DB에 `SELECT 1`을 실행한다.
- clipper_web_api DB env는 URL 방식이 아니라 split 변수 방식이다.
- m2-stage `stack.dev.env`는 반드시 DB별 password 변수를 사용해야 한다:
  - `CLIPPER_USER_DATABASE_PASSWORD`
  - `CLIPPER_ADMIN_DATABASE_PASSWORD`
  - `CLIPPER_RELEASE_DATABASE_PASSWORD`
- `CLIPPER_DATABASE_PASSWORD` 하나짜리 공통 password 변수는 쓰지 않는다.
- Angular web/admin Docker image는 Angular build output을 컨테이너 내부 Nginx로 서빙한다.
- API Docker image는 Node/NestJS runtime이고 Nginx를 포함하지 않는다.
- m2-db dev DB 3개는 이미 배포 완료:
  - user DB: 192.168.0.7:55203
  - admin DB: 192.168.0.7:55213
  - release DB: 192.168.0.7:55223
- DB password rotate는 이번 세션에서 신경쓰지 않는다. 다만 secret 값은 채팅/로그에 출력하지 않는다.
- DBeaver로 DB를 볼 때 로컬 Mac mini에서 `192.168.0.7:55203` timeout이면 password 문제가 아니라 네트워크 도달성 문제다.
- 권장 DB GUI 접근은 m2-stage 안에서 DBeaver를 실행하는 방식이다. 로컬 DBeaver는 VPN/SSH tunnel 없이는 안 될 수 있다.
- legacy api.clipperstudio.ai, demo.clipperstudio.ai는 건드리지 않는다.
- dohit 관련 파일/컨테이너/포트는 건드리지 않는다.
- Clipper dev DB 포트 `55203/55213/55223`은 임시로 ipTIME 포트포워딩을 사용한다. stage/prod DB 포트는 WAN 공개하지 않는다.

해야 할 일:
1. `.codex/handoff/NEXT.md`, `.codex/records/sessions/2026/06/08.md`,
   `.codex/design/CLIPPER_DEV_TEAM_GUIDE.md`,
   `.codex/design/CLIPPER2_DEV_DEPLOYMENT_NOTION.md`를 먼저 읽는다.
2. m2-stage에서 아래를 먼저 실행해 `clipper_infra`를 최신화한다:
   - `cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra`
   - `git status --short --branch`
   - `git pull --ff-only origin feature/infra-initial-setup`
3. m2-stage의 실제 secret 파일을 확인하되 secret 값은 출력하지 않는다:
   - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/stack.dev.env`
   - 기존 `CLIPPER_*_DATABASE_URL` 또는 `CLIPPER_DATABASE_PASSWORD`가 있으면 제거하고 per-DB password split 변수로 바꾼다.
4. 관련 repo의 상태를 확인한다:
   - clipper_infra
   - clipper_web_client
   - clipper_web_admin
   - clipper_web_api
5. `./scripts/deploy-dev.sh all`을 실행해 최신 image/service를 재배포한다.
6. dev service health/browser smoke를 재확인한다:
   - https://dev.clipperstudio.ai
   - https://dev-admin.clipperstudio.ai
   - https://dev-api.clipperstudio.ai/v1/health
7. 다음 구현 단계는 infra wiring이 아니라 app 기능이다:
   - clipper_web_api migration tooling 결정
   - user/admin/release DB schema 첫 migration 작성
   - `/v1/releases/latest` 실제 release metadata 구현
   - client download/login/signup 실제 페이지 merge 시 배포 반영 방식 정리
   - admin 운영 기능 범위 결정
8. stage/prod 배포는 dev 기능과 migration 흐름이 정해진 뒤 진행한다.

문서 기준:
- if available, read clipper_infra/runbooks/deploy-dev.md,
  clipper_infra/apps/compose.yml, clipper_infra/apps/compose.dev.yml,
  clipper_infra/env/stack.dev.env.example first.
- Do not touch dohit containers/files/ports.
```

## Legacy Local Session Prompt

```text
Using Superpowers.

먼저 `/Users/jina/project/adlight/.codex`가 별도 git repo라는 점을 기준으로 아래 문서를 순서대로 읽고 현재 상태를 파악해줘.

1. `.codex/README.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/README.ARCHITECTURE.md`
4. `.codex/README.RUNTIME.md`
5. `.codex/README.OPERATIONS.md`
6. `.codex/operations/env-runtime/README.md`
7. `.codex/operations/windows-packaging/README.md`
8. `.codex/features/template-builder/README.md`
9. `.codex/features/dance-highlight/README.md`
10. `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`
11. `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
12. `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
13. `.codex/design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
14. `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
15. `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
16. `.codex/design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md`
17. `.codex/records/sessions/2026/06/05.md`
18. `.codex/records/sessions/2026/06/02.md`
19. `.codex/records/sessions/2026/06/04.md`
20. `.codex/records/sessions/2026/05/29.md`
21. `.codex/records/sessions/2026/05/27.md`

현재 repo HEAD는 세션 시작 시 직접 `git status -sb`와 `git log -1 --oneline`으로 재확인한다.

현재 기준:
- `clipper_angular`: `main @ 70d6e58 Improve template sample render flow`
- `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`
- `clipper_python`: `main @ 535131c Render sample images as cover`
- `clipper_electron`: `main @ f701677 Revert "Update electron builder"`
- `.codex`: `workflow-executor-design`, 2026-06-05 Clipper web DB split/session closeout docs 포함. 세션 시작 시 `git log -1 --oneline`으로 직접 재확인.
- `clipper_infra`: `feature/infra-initial-setup @ 49faa91 feat: split Clipper DB stack into user admin release`
- `clipper_web_admin`: `main @ fef456a feat: add minimal web admin scaffold`
- `clipper_web_api`: `main @ ec13be7 feat: add minimal web API scaffold`
- `clipper_web_client`: `main @ 791c935 feat: add minimal web client scaffold`

다음에 할 일:
1. `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python` 상태를 확인한다.
2. WorkflowExecutor 작업 branch들을 먼저 확인한다.
   - `.codex`: `workflow-executor-design`, clean after this documentation commit.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인을 진행한다.
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
   - Angular Plugin Store/job UI에서 `runtimeKind` 표시/버튼 정책이 필요한지 검토한다.
4. Clipper2 dev/stage/prod 인프라 구현을 이어간다.
   - `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
   - `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
   - dohit 참고 문서 3개:
     - `/Users/jina/project/dohit-infra/.codex/dohit-infra-easy-guide.md`
     - `/Users/jina/project/dohit-infra/.codex/dohit-infra-technical-guide.md`
     - `/Users/jina/project/dohit-infra/.codex/clipper-infra-recommendations.md`
   - dohit은 웹 리워드 서비스이고, Clipper2는 설치형 Electron 앱이라는 차이를 먼저 맞춘다.
   - Windows installer는 사무실 Windows PC runner, macOS installer는 Mac mini runner, 설치파일 저장소는 S3라는 현재 전제를 유지한다.
   - 코드 push/main merge를 설치파일 release trigger로 삼지 않는다.
   - 플랫폼별 명시적 release build trigger와 release metadata 구조를 먼저 정한다.
   - dev/stage/prod 3환경을 기준으로 서버/컨테이너/DB/release/update feed 구조를 정한다.
   - `clipper_infra`에는 초기 compose/env/runbook 구성이 있다.
   - `m2-proxy`, `m2-db`, `m2-stage` preflight는 완료됐다.
   - `clipper-db-dev`도 m2-db에서 배포 완료됐고, m2-stage에서 `192.168.0.7:55203/55213/55223` 접근 확인이 끝났다.
   - dev Cloudflare DNS와 NPM dev proxy hosts도 완료됐다. 사용자는 임시 `nginx:alpine` 컨테이너를 이미 제거했다고 보고했다.
   - 2026-06-08 Angular 19/NestJS 전환 변경은 commit/push 완료됐다. m2-stage에서 `clipper_infra`를 pull하고 app repo 3개를 clone한 뒤 server-side build로 real dev service를 배포한다.
   - 첫 실제 Clipper 배포 환경은 `dev`다. `stage`는 dev 확인 후, `prod`는 stage 검증과 승인 후 진행한다.
   - 사용자가 dev DB password rotate는 이번 배포 세션에서 신경쓰지 말라고 했다. secret 값은 채팅/로그에 출력하지 않는다.
   - 서버 IP, 도메인, proxy, secret 주입, DB/백업 경로를 실제 값으로 채운다.
5. 사용자가 요청하면 로컬 main들을 repo별로 push한다.
6. Template Builder sample render 관련 후속 버그가 입력되면 아래 전제를 유지한다.
   - 샘플 렌더 UI는 Angular, recipe/assets는 NestJS, 실제 MP4 합성은 Python renderer가 담당한다.
   - 샘플 이미지는 콘텐츠 영역을 `cover + center crop`으로 꽉 채워야 한다.
   - layout image/단색 background는 content area 밖에서 흰색으로 빠지면 안 된다.
   - 공식 등록 전 카드 썸네일은 4:3 기준이어야 한다.
7. 새 분석 문서는 `.codex/design/` 아래에 둔다.

주의:
- `.codex`는 별도 git repo다.
- 앱 코드 repo 변경과 `.codex` 문서 변경을 같은 커밋에 섞지 않는다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- Windows build 중 PowerToys `Command Palette`를 끈다.
```

## Notes

- `.codex`는 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
- root `README.*.md`를 새로 늘리지 않는다. cross-cutting design 문서는 `design/`, feature 문서는 `features/<feature>/`, operations 문서는 `operations/<domain>/` 아래에 둔다.
