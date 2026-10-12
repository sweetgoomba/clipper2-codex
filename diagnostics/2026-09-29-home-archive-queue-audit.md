# W11 — 홈·보관함·큐 현행 정책과 변경 이력 조사

조사일: 2026-09-29 KST. **조사 및 기존 회귀 기준선 확인 완료 / 개선 방향은 사용자 선택 대기**.

## 범위와 기준선

사용자 요청에 따라 `handoff/WORKBOARD.md`와 `handoff/tasks/home-archive.md`부터 읽었다. Superpowers의 systematic-debugging으로 상태·표시·이력을 대조하고, 별도 읽기 전용 조사로 백엔드 생명주기와 프론트 변경 이력을 교차 확인했다. 개선 설계는 brainstorming의 기존 흐름에 대한 bounded 경로로 진행할 예정이다.

| repo | 조회 HEAD = 로컬 origin/dev | 작업 상태 |
|---|---|---|
| desktop/clipper_angular | `797782e8f8e1c8488d024d23e6291e91c2b1e30e` | dev, tracked/untracked clean |
| desktop/clipper_nestjs | `824a7a9f71dde8aa44c8692eadacb6ba6e4961b8` | dev, tracked/untracked clean |
| web/clipper_web_api | `31f448260148b11e61e9f53cad0ee9ac372345fe` | dev, tracked/untracked clean |

이번 조사는 fetch하지 않았다. **원격 최신성·실행 중 앱의 SHA·배포일은 미확인**이다. 제품 소스 수정·branch/worktree 생성·commit/push/merge/deploy·실제 ML/과금/환급 요청은 하지 않았다. Nest 빌드는 현재 소스를 dist로 컴파일·에셋 복사했으며 Git 변경은 없다. `.codex`의 기존 미커밋 문서는 보존하고 W11 관련 기록만 추가한다.

## 핵심 결론 — 코드로 확인한 사실

현재 홈과 보관함은 **동일한 `/projects` 화면**이다. nav 문구는 `홈`, 메타데이터 title은 `프로젝트 보관함`, 실제 그리드 제목은 `내 파일`이다. `/`와 `/home`도 `/projects`로 보낸다. 별도 완료 전용 보관함 화면은 없다.

현재 정책은 **준비·시작·실행 중 작업은 그리드 카드, 실행 순서를 기다리는 queued 작업은 상단 큐**다. 실행 중 작업을 보관함에 표시하는 것은 우연한 렌더 타이밍만이 아니라 명시적인 프론트 정책 변경이다. 큐가 비면 백엔드가 자동으로 실행 슬롯을 잡으므로 queued 표시가 아주 짧을 수 있다. 이 두 원인이 함께 사용자 관측을 설명한다.

근거:

- `desktop/clipper_angular/src/core/plugins/plugin-route.guards.ts:9`: landing은 `/projects`.
- `desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts:207`: 홈 label, 보관함 title.
- `desktop/clipper_angular/src/shell/projects/projects/projects.component.ts:218`: `preparing/starting/running` → runningCards.
- 같은 파일 `:225`: `queued`만 waitingQueueRows/상단 큐. `:269`: 완료·실패·취소만 일반 cards 재료.
- 같은 폴더 `projects.component.html:39`: 종료 cards와 runningCards를 별도 입력으로 같은 그리드에 전달.
- `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:134`: 전역 동시 실행 1개. `:244`: queued 저장·큐 등록·snapshot 발행 후 `:256`에서 즉시 drain. 일반 start도 `:427`, `:438`에서 발행·등록·drain. `:685`의 drain이 빈 슬롯을 즉시 점유.

**queued를 생략한다고 단정하지 않는다.** 정상 경로는 queued를 저장/발행한 후 starting으로 바뀐다. 9/18 커밋 및 화면 주석의 “queued를 거치지 않아”는 현재 백엔드 상태 전이의 엄밀한 설명이 아니다. 눈에 보이는 대기 구간이 거의 없다는 효과와 내부 전이를 구분한다. 실제 사용자 앱에서 몇 ms 노출되는지는 측정하지 않았다.

## 상태별 표시 표

아래는 일반 단일 잡 기준이다. 홈과 보관함은 같은 화면이므로 ‘홈 전체 노출’과 ‘내 파일 그리드’를 구분했다. 그리드에는 유형 필터가 적용된다.

| 상태 | 의미 | 홈 전체 | 보관함/내 파일 그리드 | 상단 큐 | 동작 |
|---|---|---|---|---|---|
| preparing | 예약·과금 연결·렌더 재료 준비, 아직 실행 큐에 없을 수도 있음 | 노출 | 준비 중 카드, 맨 앞 고정 | 없음 | 취소; 삭제 선택 불가 |
| queued | 실행 가능한 작업이 순서를 기다림 | 노출 | 없음 | 대기 행, 대기 N개 포함 | 맨 앞으로·취소 |
| starting | 실행 슬롯 점유 후 플러그인/원본 준비 | 노출 | 시작 중 카드, 맨 앞 고정 | 없음 | 취소; 삭제 선택 불가 |
| running | 실제 workflow executor 실행 | 노출 | 실행 중 카드, 맨 앞 고정 | 없음 | 진행률·message·취소 |
| completed | 정상 종료 | 노출 | 일반 결과 카드, 시간순 정렬 | 없음 | 모듈별 열기·편집·재생·다운로드·삭제 |
| failed | 실패 종료 | 노출 | 실패 카드, 시간순 정렬 | 없음 | 일반 잡 재시도·삭제 등 |
| cancelled | 사용자 취소 종료 | 노출 | 취소 카드, 시간순 정렬 | 없음 | 일반 잡 재시도·삭제 등 |
| 앱 종료로 중단 | 별도 enum 없음; 재시작 시 failed + interruptedFromStatus | 노출 | 실패 카드 | 자동 재등록 없음 | 일반 재시도; 스토리보드는 전용 재개 |

상태 enum/전이 계약: `desktop/clipper_nestjs/src/modules/jobs/domain/job.model.ts:30`. 일반 흐름은 `[preparing →] queued → starting → running → completed`, 활성 상태에서 failed/cancelled 종료도 허용한다.

### 중요한 예외

1. **preparing은 실제 실행과 다르다.** 큐 슬롯을 차지하지 않으며, 베리에이션의 뒤 배치는 앞 배치의 준비가 끝날 때까지 preparing에 머물 수 있다. 렌더러가 쉬어도 가능하다. 화면의 ‘생성 중’은 실제 CPU/ML 실행보다 넓은 개념이다. `variation-v2-render.service.ts:520`의 준비 직렬화 기록 참조.
2. **베리에이션 활성 카드/큐 행은 renderId 단위**, 종료 결과 카드는 variation projectId 단위다. 잡 N개가 카드/행 1개가 되므로 대기 N개는 원시 job 개수가 아니다. `queue-view.ts:74`, `projects.component.ts:352`.
3. 베리에이션 배치에 끝난 잡과 미종료 잡이 섞여 있으면, 다른 행에서 실제 running/starting이 없는 동안 행 상태를 running으로 유지한다. 변형 사이의 찰나에 그리드↔큐가 깜빡이지 않게 한 표시 규칙이다. 다른 행이 실행 중이면 대표 queued/preparing 상태를 따른다. `queue-view.ts:198`.
4. **베리에이션 결과 카드는 해당 프로젝트의 모든 잡이 종료될 때까지 숨긴다.** 일부 영상이 나왔어도 일반 결과 카드가 점점 늘지 않게 한다. 전부 실패/취소해도 종료 후 결과 화면 입구는 남는다. 이와 별개로 활성 배치 카드는 표시된다. `projects.component.ts:286`, `:454`.
5. 생성 중 카드도 **모듈 필터를 따른다**. 다른 유형을 선택하면 실행 카드가 그리드에서 가려지고, queued가 아니므로 큐에도 없을 수 있다. `projects-grid.component.ts:243`.
6. 일반 재시도는 새 jobId와 retryOf를 만든다. 기존 실패/취소 조상은 화면에서 숨기지만 기록은 남는다. `projects.component.ts:263`. 스토리보드는 홈 카드에서 열기만 제공하고, 전용 batch 화면에서 동일 job을 재개한다. `project-card.builder.ts:72`, `jobs.service.ts:275`, `:321`.
7. 성공·실패 잡이 같은 결과 그룹에 있으면 대표는 최신 성공분이다. 더 최신 실패가 있어도 그 그룹 카드 전체가 실패로 바뀌지는 않는다. `project-card.builder.ts:146`.

## 현재 기능 지도

| 영역 | 현재 기능 | 근거 |
|---|---|---|
| 진입/내비게이션 | `/`, `/home` → `/projects`; 좌측 최상단 홈. 설치 0개여도 같은 홈 | `app/app.routes.ts:25`, `plugin-route.guards.ts:9`, `app-navigation-metadata.ts:110` |
| 그리드 | 안무·대사·숏폼·댓글 오버레이·랭킹·베리에이션·스토리보드 7유형; 실행 카드 상단 고정 + 종료 카드 | `projects-view.ts:63`, `projects.component.html:39` |
| 필터/정렬 | 데이터에 존재하는 유형 + 개수, 미설치 표시; 최신/과거순; type/sort URL 보존; 종료 카드 60개씩 점진 렌더, 고정 카드 상한 예외 | `projects-grid.component.ts:181`, `:243`, `:258`, `projects.component.ts:515`, `:574` |
| 검색 | 홈·큐에 텍스트 검색 입력/검색 로직 없음. 유형 필터만 존재 | `projects.component.html`, `projects-grid.component.html`, 두 컴포넌트 TS의 search/검색 조회 |
| 카드 액션 | 클릭하면 1장만 액션 오버레이. 바깥 클릭/Esc/필터·정렬/상태 전환으로 닫힘 | `projects-grid.component.ts:105`, `:284` |
| 생성 중 카드 | 아이콘, 상태, 백엔드 message, progress; preparing/starting 또는 progress=0은 흐르는 막대; 취소/전체 취소만 | `running-card.builder.ts:23`, `:38`, `:72` |
| 종료 카드 | 단일 영상은 재생·편집·다운로드·삭제; 묶음은 결과 보기·ZIP·삭제; 실패/취소는 일반 재시도 포함. 스토리보드는 열기만 | `project-card.builder.ts:69` |
| 결과/편집 목적지 | 안무·대사 `/projects/:id`; 숏폼 입력모드 편집; 댓글 편집; 랭킹 편집; 베리에이션 `/variation/:id/results`; 스토리보드 `/shortform/director/batches/:id` | `projects.component.ts:769`, `:821` |
| 하이라이트 결과 | 안무 인물별 클립 보기/숨김/이동, 대사 클립 보기/트림, 미리보기·ZIP·프로젝트 삭제; 하이라이트 생성 숏폼의 편집은 원본 결과로 복귀 | `projects-detail-page.component.html`, `projects.component.ts:802` |
| 큐 | 대기 행만; 0개여도 바 상시 노출; 펼침 목록의 맨 앞으로·취소; 다른 작업 뒤에 queued일 때만 자동 펼침 | `projects-queue.component.html:47`, `projects.component.ts:751`, `:1953` |
| 다중 삭제 | 삭제 모드→현재 유형의 종료 카드 전체 선택→확인→순차 삭제. 진행 중 제외; 부분 실패분 선택 유지; 베리에이션 영상 먼저→프로젝트 기록 나중 | `projects.component.ts:163`, `:1008`, `:1044`, `:1179` |
| 빈 홈/오류 | 로딩·오류·대기·생성 중이 없을 때 빈 안내와 설치 모듈 바로가기. 잡 오류 별도 표시 | `projects.component.ts:488`, `projects.component.html:35` |
| 우측 패널 | 계정·이용권·크레딧·로컬 리소스·버전; 접힘 기억; 이용관리/원장/리소스/로그아웃 진입 | `home-side-panel`, `projects.component.ts:645` |

잡 기록이 없고 완료 프로젝트만 남은 경우 synthetic completed job을 만들어 표시한다. 삭제 후 jobs와 projects를 모두 갱신하지 않으면 유령 카드가 생기므로 현재 코드는 두 목록을 갱신한다. `projects.component.ts:250`, `:1470`, `:965`.

## 변경 커밋·날짜·기록된 이유

날짜는 아래 커밋의 author/committer KST이다. Git 포함·병합 기록을 앱 배포일로 해석하지 않는다.

| 시점 KST | repo / commit | 실제 변화 | 기록된 이유와 한계 |
|---|---|---|---|
| 2026-08-18 10:09:10 | Angular `f233162a` | 홈을 보관함 `/projects`로 고정, 섹션 더보기 라우트 제거 | 당시 grid 설계 D1/D3는 홈=보관함, **진행·대기는 큐에만**, 그리드는 종료 작업. `2026-08-18-projects-home-grid-design.md:27` |
| 2026-08-18 11:19:23 / 11:58:06 | Angular `1b6674e8` / `727fe15d` | 모듈별 섹션→단일 그리드, 필터/정렬 URL 유지·완료 딥링크 강조 | 유형 필터가 더보기/섹션 역할을 흡수하고 상세 진입 후 보던 상태를 유지. 같은 spec D4/D8/D11 |
| 2026-08-18 15:40:55 | Angular `c9b55d04` | 계정·이용권·크레딧·리소스·버전 우측 패널 | 자기 상태 확인을 위해 설정 화면까지 가지 않도록 기존 설정 데이터를 홈에 배치. `2026-08-18-home-side-panel-design.md:9` |
| 2026-09-02 | Angular `1012ae3` / `398beaa` / `f1fd8ea` | 베리에이션 render 단위 큐 묶음, project 단위 결과 카드, 미종료 결과 숨김 | 여러 변형이 다른 작업을 파묻거나 동일 결과 화면으로 가는 카드가 반복되는 문제. 일부 종료 결과가 진행률처럼 그리드에 새어 나오지 않게 함. 9/18 실행 카드 변경보다 먼저인 별도 축 |
| 2026-09-17 03:06:50/51 | Nest `0e2a08d8` / Angular `ac01d6f` | preparing/queued/starting/running 명시적 생명주기, 기존 waiting 대체 | 준비·대기·실행과 과금 복구 경계 구분. 이 enum 변경 자체가 실행 카드의 그리드 이동은 아님 |
| 2026-09-17 03:25:39 | Nest `644c0c0a` | fresh render retry attempt 준비 | 기존 준비 payload를 그대로 재실행하지 않고 소유 모듈의 재준비 경로 사용 |
| 2026-09-17 04:14:22 / 08:21:05 | Nest `f452b6f8` / `fda1eda5` | 재시작 reconciliation; 취소 출처·삭제 전 환급 outbox 보존 | process crash/취소 후 삭제 때문에 환급 근거가 사라지는 경계 보정. `.codex/implementation/2026-09-17-archive-refund-fix-result.md`에 기록 |
| 2026-09-18 14:19:08 | Angular `a4304f5b` | ‘생성 중 카드·대기 전용 큐’ 설계 추가 | 생성 중 작업은 얇은 큐 행, 완료 작업은 카드라 같은 화면의 표현 방식이 갈라져 있었음. 카드 오버레이 재사용·중복 표시 방지. **기록된 이유**, 추정 아님 |
| 2026-09-18 15:24:33 | Angular `6fd329f6` | preparing/starting/running → 고정 그리드 카드; queued → 큐; 빈 홈/배치 취소 배선 변경 | 위 설계 구현. 사용자 관측의 직접 원인. 작성/커밋자 곽민준, Claude 공동 작성 표기 |
| 2026-09-18 15:43:37 | Angular `537994f6` | 큐에서 진행률·실행중 그룹 제거 | 순서와 취소를 맡는 대기 큐로 표시 정리 |
| 2026-09-18 16:24:45 | Angular `3a1db3ba` | 대기 0개일 때도 큐 바 상시 표시로 변경 | 숨기면 대기 작업 확인 입구가 없어지고 1개씩 실행할 때 바가 거의 보이지 않는 문제. 원래 spec의 빈 큐 숨김 규칙을 후속 수정 |
| 2026-09-18 16:51:41 | Angular `d86a646c` | 생성 중 카드 기능 브랜치 병합 기록 | 이것만으로 당시 dev 반영·앱 배포를 단정하지 않음 |
| 2026-09-18 21:04:33 / 21:28:59 | Angular `53596654` / `8af00475` | 삭제 모드·현재 필터 전체 선택·취소·N개 삭제 선택 바 | 베리에이션 목록과 삭제 흐름 통일. 필터 뒤 숨겨진 선택을 풀어 보이지 않는 프로젝트를 삭제하지 않도록 함. `2026-09-18-home-bulk-select-delete-design.md:28` |
| 2026-09-19 22:42:07 | Angular `ae2572ee` | 딥링크·queued 스트림·재시도에서 다른 작업 뒤 대기일 때만 큐 자동 펼침 | 즉시 실행되는 작업에서도 빈 큐가 선택/강조되던 사용자 피드백 보정 |
| 2026-09-21 07:31:38 | Angular `757d5e63` | `integration/jason-dev` → dev 병합 | 현재 dev의 first-parent 이력에서 위 실행 카드 변경이 들어온 명시적 merge. 부모 `b511e158`에는 `6fd329f6` 없음, 부모 `f352813c`에는 있음. **개발 커밋은 9/18, 이 dev 병합 기록은 9/21** |
| 2026-09-21 08:20:14 | Nest `693edf61` / Angular `18006cb0` | 스토리보드 배치 재개·홈 카드 연결 | 전용 checkpoint/부분 정산을 보존하는 재개 경로. 일반 retry와 구분 |

기본 FIFO 자동 drain이 언제 처음 도입됐는지는 이번 표시 정책 원인 조사에서 모든 이전 이름까지 추적하지 않았다. 따라서 9/18에 백엔드 자동 실행도 새로 생겼다고 주장하지 않는다. 9/18 running-card spec은 프론트 단독·백엔드 계약 변경 없음이라고 명시한다.

### 문서/주석 불일치

- 8/18 spec의 ‘진행/대기는 큐에만’은 **당시 정책**이며 9/18에 대체됐다.
- 9/18 running-card spec `:20`, §4.3의 ‘대기 0개면 바 숨김’은 같은 날 `3a1db3ba`로 바뀌었지만 문서가 따라가지 않았다. 현재 코드·diff가 우선이다.
- `projects.component.ts:301`의 ‘진행 상황은 실행 큐가 보여줌’은 베리에이션 결과 숨김의 과거 설명이다. 현재 active 표시는 runningCards가 맡는다.
- `projects.component.ts:1249`의 ‘실행 시작 때 차감’ 주석도 현행 과금 연결과 다르다. 유료 start/준비에서 이미 run을 확정하고 queued가 될 수 있다. 큐에 있다고 미차감이라고 판정하면 안 된다.
- nav help에는 생성 중과 완성 프로젝트가 모두 모이는 곳이라고 설명하지만 파일 머리말 `nav-help-content.ts:10`은 사용자 확정 전 초안이라고 밝힌다. 이 도움말을 사용자 승인 근거로 삼지 않는다.
- 정책을 왜 ‘보관함’ 용어와 함께 유지했는지, 사용자가 이번 변경을 직접 승인했는지, 실제 언제 앱에서 체감됐는지는 증거가 없으므로 **미확인**이다. 현재 명칭과 범위가 기대 차이를 만들었을 가능성은 **추정**이다.

## 재시작·재시도·취소·삭제·차감/환급 경계

- **재시작:** 일반 활성 잡은 `failed + interruptedFromStatus`로 보존하며 자동 큐 복원 없음. committing 단계는 결과 복구 후 completed/failed, 복구 예외면 다음 부팅에 재확인. `json-job-repository.ts:99`, `jobs.service.ts:1359`.
- **재시도:** failed/cancelled에 새 jobId/retryOf 생성. render 소유 모듈은 fresh preparing/output/paid attempt를 만들고, 일반 fallback은 project_id/output_root를 유지할 수도 있다. 모든 재시도가 새 projectId라는 식으로 일반화하지 않는다. `jobs.service.ts:287`, `:321`, `projects.service.ts:616`.
- **취소:** queue에서 제거하고 cancelled를 저장한 뒤 abort/실행 슬롯 해제. cancelled 저장은 abort보다 먼저다. terminal/committing/committed는 취소로 되감지 않는다. 베리에이션 batch 취소는 미종료분만; 이미 만든 영상은 보존. `jobs.service.ts:458`, `projects.component.ts:1268`.
- **삭제:** 활성 job archive 삭제는 거부. 종료 잡·종료 retry 조상 삭제; 공유 project는 마지막 참조까지 유지. 베리에이션 홈 삭제는 영상→프로젝트 기록 순서. 외부 output root는 임의 삭제하지 않는다. `jobs.service.ts:515`, `projects.service.ts:540`, `projects.component.ts:1179`.
- **차감:** paid start handshake가 실행 큐 진입보다 먼저일 수 있다. job.status와 billing attempt.state는 별개이며 queued/preparing라도 이미 차감했을 수 있다. `jobs.service.ts:397`, `billable-job-attempt.coordinator.ts:43`.
- **환급:** 일반 알려진 실패/취소는 durable fail intent를 저장하고 인증/온라인 경로로 전달한다. 오프라인에서는 pending이며 UI 삭제 성공을 원격 환급 완료로 해석하지 않는다. 서버 fail은 한 번만 환급하고 성공 run을 실패로 되돌리지 않는다. `billing-terminal-finalizer.ts:47`, `billing-terminal-outbox.service.ts:163`, Web API `operations.service.ts:235`.
- **중단의 불명확성:** 재시작 전 running이면 금융 결과를 ambiguous로 두고 자동 환급을 추론하지 않는다. preparing/queued/starting 중단은 fail intent 처리. 스토리보드는 전용 부분 정산/재개로 일반 규칙에서 제외. `billing-restart-reconciliation.service.ts:53`.
- **취소 후 즉시 삭제:** 정확히 owner + desktop_job ID에 묶인 attempt에만 삭제 표시. 명백한 실행 전 취소 근거를 outbox에 먼저 내구성 있게 저장한 다음 삭제한다. stale attemptId/project fallback으로 다른 시도의 환급을 건드리지 않는다. `jobs.service.ts:536`, `billable-job-attempt.coordinator.ts:160`.

## 이번에 실행한 검증

### Angular — 기존 홈/큐 집중 회귀 362/362 PASS, exit 0

Node `v24.19.0`으로 현재 소스의 6개 spec 실행:

```sh
/Users/jina/.nvm/versions/node/v24.19.0/bin/node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless \
  --include='src/shell/projects/projects/projects.component.spec.ts' \
  --include='src/shell/projects/models/queue-view.spec.ts' \
  --include='src/shell/projects/models/running-card.builder.spec.ts' \
  --include='src/shell/projects/models/project-card.builder.spec.ts' \
  --include='src/shell/projects/projects-queue/projects-queue.component.spec.ts' \
  --include='src/shell/projects/projects-grid/projects-grid.component.spec.ts'
```

cwd: `desktop/clipper_angular`. 기본 cwd PATH의 Homebrew Node24.3은 CLI 최소 버전 미달(exit3)이어서 이미 설치된 Node24.19를 명시했다. 샌드박스의 시험 빌드가 진단 없이 exit134로 중단돼, 허용된 로컬 권한으로 동일 테스트를 실행했다. 로컬 loopback Karma/Chrome만 사용. 폰트 fixture 404 경고 2개가 있었지만 362건 통과. 원본 로그 `/private/tmp/adlight-w11-angular-baseline-20260929.log`.

### Nest — 현재 소스 build PASS + 기존 경계 회귀 117/117 PASS, exit 0

cwd: `desktop/clipper_nestjs`. 명시적 Node24.19의 npm CLI로 `npm run build`, 이후 아래 13개 파일을 `node --test`로 실행했다.

```text
test/job-status-lifecycle.test.js
test/jobs-queued-order.test.js
test/render-retry-prepare.test.js
test/archive-delete-entry.test.js
test/projects-service-delete-for-job.test.js
test/jobs-confirmed-billing.test.js
test/billing-restart-reconciliation.test.js
test/billing-crash-boundaries.test.js
test/billing-archive-cancellation.test.js
test/jobs-billing-outbox-replay.test.js
test/jobs-commit-phase.test.js
test/variation-v2-initial-billing-restart.integration.test.js
test/variation-v2-retry-billing-restart.integration.test.js
```

0 fail/cancel/skip/todo. 13 warning/1 error 기록은 offline/ambiguous/실패한 projection/꺼진 plugin 등 테스트의 의도적 장애 주입이다. 원본 명령·exit·타임스탬프·출력: `/private/tmp/adlight-w11-nest-baseline-20260929.log`.

**한계:** mock 실행기·가짜 금융 원장·임시 JSON 저장소로 상태 및 경계 검증. 실제 사용자 앱의 시각 스모크, 실제 ML, OS 강제 종료, 원격 Web API/DB, 실차감·환급·잔액 반영, 현재 서버 배포 상태는 검증하지 않았다. 전체 테스트/production 빌드 통과로 확대하지 않는다.

## 사용자 선택 후 개선 작업의 회귀 기준

수정 방향은 아직 선택되지 않았다. 현행 정책을 자동으로 되돌리지 않는다. 코드 수정 전에 대상 repo만 fetch하고 최신 origin/dev SHA를 기록한 뒤 동일 새 branch명·격리 worktree를 만들며 `desktop/clipper_*`, 필요 시 `web/clipper_*` 형제 관계를 보존한다.

| 경계 | 개선 후 반드시 확인할 기대값 |
|---|---|
| 빈 큐 신규 작업 | preparing/queued/starting/running 이동·카드 개수·빈 안내가 선택한 정책과 일치 |
| 실행 중 추가 작업 | 실제 queued 표시, 대기 개수/순서/맨 앞으로, preparing과 실제 실행 구분 |
| 베리에이션 | render별 active 묶음/project별 결과, 혼합 상태·변형 사이·다른 배치 실행 시 올바른 위치 |
| 재시도 | 새 job/retryOf, 조상 중복 카드 없음, fresh render/attempt, 과금 확인 거절 시 무동작; 스토리보드 전용 재개 유지 |
| 취소 | preparing/queued/starting/running, 저장 후 abort, 뒤늦은 completion 차단, 완료된 배치 산출물 보존 |
| 삭제 | 활성 삭제 거부, retry 조상 cascade, 공유 결과 마지막 참조, 부분 실패 선택 유지, 베리에이션 영상→기록 순서 |
| 차감/환급 | 이미 차감된 대기 취소·즉시 삭제, 정확한 owner/job/attempt, outbox 저장 실패 시 삭제 중단, 재시작·offline replay 중복 환급 없음 |
| 실행 결과 불명 | 재시작 running ambiguous 유지, 삭제만으로 환급 추론 금지, 스토리보드 checkpoint/부분 정산 유지 |
| 필터/정렬/진입 | 생성 카드 가림·개수·완료 후 정렬·딥링크·자동 큐 펼침·미설치 진입·다중 삭제 제외 규칙 확인 |

선택 가능한 표시 개선 예시는 (1) 준비/실행 영역과 종료 보관함 분리, (2) 과거처럼 준비·대기·실행을 큐에 모으고 그리드는 종료만, (3) 현행 배치를 유지하면서 명칭/안내를 현재 범위에 맞추기다. 이는 **미선택 제안**이며 구현/합의된 설계가 아니다.
