# W07 스토리보드 후속 수정·검증 — 2026-09-29

상태: 요청한 후속 기능·입력/선택·표시/원장 소스 수정 및 로컬 회귀/화면 검증 완료. 생성 단계 계측·기존 로그 분석·오프라인 전후 비교와 최적화 후보 검토 완료. **실공급자로 같은 입력의 전후 시간·품질·정산 비교는 미실행**이다. 아래 성공은 서버 배포나 실제 과금 성공을 뜻하지 않는다.

## 기준·작업 공간

`.codex/handoff/WORKBOARD.md`, `tasks/storyboard.md`를 먼저 읽고, 민준님 설계 `desktop/clipper_angular/docs/superpowers/specs/2026-09-21-storyboard-v2-ui-refinement-design.md` D6–D13/§5 및 FE plan 단계4–6을 최신 코드와 대조했다. 이전 구현이 dev에 포함됐으나 선택 삭제·레거시 잠금/화면 철거·초기 진행 메시지/미터는 빠져 있었다. 기존 수량 동의·완료 결과의 영구 수정/생성 잠금·복제·복구·수량 정산은 유지했다.

세 repo `git fetch origin dev` 성공 후 새 공통 branch `feat/storyboard-followups-20260929`를 생성했다. 작업 루트는 `/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929`이며 아래 상대경로를 보존했다. 루트는 Git repo가 아니므로 대상 repo별 `git worktree add`를 사용했다.

| repo | fetch한 origin/dev 기준 SHA |
| --- | --- |
| desktop/clipper_angular | 797782e8f8e1c8488d024d23e6291e91c2b1e30e |
| desktop/clipper_nestjs | 824a7a9f71dde8aa44c8692eadacb6ba6e4961b8 |
| web/clipper_web_api | 31f448260148b11e61e9f53cad0ee9ac372345fe |

최종 원본 세 checkout은 dev·clean·origin/dev 대비0/0, 같은 SHA였다. 각 새 worktree에만 미커밋 소스가 있다. 기존 node_modules를 symlink로 재사용하고 로컬 `.git/info/exclude`에 해당 경로만 추가했으며 의존성 설치/lockfile 변경은 없다. Nest PDF 검증용 기존 Python 폰트6개는 ignored dist로만 복사했다. Electron/Python 소스·옛 삭제된 worktree·다른 세션의 checkout/branch/worktree는 변경하지 않았다. commit/push/merge/deploy/DB 변경은 없다.

## 요구별 변경과 검증

| 요구 | 결과 |
| --- | --- |
| 민준님 선택 삭제 | 목록 헤더의 선택 모드·전체 선택·혼합 상태·삭제 수/보존 수·진행/정산 제외 안내, 확인1회, 순차 DELETE, 실패 행만 재선택/재시도. 화면 이탈 후 다음 호출 중단. 확인 전에 ID/보존 수를 고정하고 매 호출 직전 busy 재검사. |
| DELETE/데이터 보존 | `DELETE /v1/projects/shortform-director/profiles/:profileId`:204 빈 응답, 없는/다른 owner404, 실행/시작/commit/정산 pending409 `STORYBOARD_PROFILE_BUSY`. 생성·복구와 동일 profile lock, 삭제가 먼저면 기존 동의로 생성404이고 quote/차감하지 않음. 삭제 의도를 기존 profile 위치의 영속 tombstone에 저장해 index 복구 후 되살아나지 않음. batch/artifact/job/billing/project/legacy 원본과 profile 설정은 보존. |
| 레거시 | legacy completion 조회·잠금·공개 count 제거, 레거시 화면/라우트/셸/reader/PDF export 철거. settingsV2 없는 프로필은 새 형식 전환 CTA, 생성 미노출; preflight는400. 기존 역사 데이터 자동 삭제 없음. 기존 backend legacy production API의 일괄 철거는 하지 않음. |
| 진행 상태 | JobHistoryService의 job 상태/진행률을 카드에 연결. 초기 조사·주제·시나리오·작성 단계 메시지, running이며 progress>0일 때만 퍼센트, 완료 시 결과 CTA. 겹친 terminal 알림 중 배치 재조회도 누락 없이 처리. |
| 한글 누락 | 공유 `ImeEnterDirective`를 사용하고 feature 폼에서 실제 composition 수명 및 compositionend 직후 최종 input 전의 Enter를 방어. 관련/금지 키워드 모두 검사. 조합 중 submit 차단. |
| 목적 해제/저장 | Material 칩이 마지막 선택 해제 때 내보내는 null/undefined를 무시하던 원인을 수정. 빈 custom purpose를 폼에 반영해 submit 비활성·save 미발행. 다시 입력하면 objective와 settingsV2.purpose가 같게 저장됨. saving 중 이벤트 차단. |
| 설정 정렬 | 카드 제목/설정/액션의 폭과 세로 기준을 고정하고 긴 값 줄바꿈, 레이블을 폼과 일치시킴. 1920/1280/768/390의 다크·라이트 캡처/목록 overflow 검사. |
| 원장 명칭 | 서버 operation `shortform_director.generate`가 read-time 표시 map에서 빠졌음. `스토리보드 생성 · 크레딧 사용/반환`으로 다른 플러그인 계약과 일치. 역사 차감 reason/run join도 반영하며 원본 reason/delta/수량 정산은 바꾸지 않음. |
| 속도 | 불필요한 legacy N+1 조회 제거. 성공/실패/취소·retry wait·source·checkpoint queue/storage·document storage의 안전한 시간 사건 추가. 호출 의존성과 병렬/캐시/모델 후보의 비용·품질·취소/복구/정산 위험 분석. 실제 생성 지연 감소를 주장하지 않음. |

중요 소스는 Angular `components/operating-profile-{form,card,list}/`, `pages/profiles-page/`, profile gateway/service, routes/config; Nest `application/storyboard-{profile-lock,batch-discovery,batch-pipeline,batch.executor,stage-retry,batch-checkpoints,batch-document-store}.ts`, profile service/repository/controller; Web `src/modules/credits/domain/credit-ledger-display.ts`다. cloud OpenAPI에는 desktop profile/batch API 섹션이 없어 desktop DELETE를 잘못 추가하지 않았고 위에 인터페이스를 명시했다.

## 재현·회귀 증거

- 폼 기준21/21 → 목적 해제/IME 신규 사례 RED → GREEN. compositionend가 최종 input보다 먼저 오는 '독'→'독서' 순서도 RED를 재현하고 수정했다. 실제 Material 칩 클릭·submit·payload 검사를 포함한다.
- 관리 UI 없는 상태에서 신규 회귀 RED, 레거시 route 잔존 RED. 이후 신규 v2 조건을 갖추지 못한 기존 생성 fixture는 명시 settingsV2로 보정했다.
- 겹친 terminal 배치 재조회 누락 RED→GREEN. native fake promise가 whenStable 추적 밖이어서 테스트에서 continuation을 drain한 뒤 검사했다.
- 브라우저가 edit 이후 메뉴 backdrop 때문에 클릭할 수 없는 문제를 찾았다. portal 메뉴 항목의 stopPropagation 제거, 해당 MatMenuTrigger의 닫힘 회귀 및 브라우저 통과. 전역 overlay query는 다른 fixture 영향을 받아 해당 trigger 검사로 좁혔다.
- 삭제 체크박스 host의 attr만 지정해 실제 input에 이름이 없는 문제를 화면 자동화가 찾았다. input 접근성 회귀 RED→GREEN, Material `[aria-label]` input 사용.
- 독립 리뷰가 확인창 표시1개/실제삭제2개 race를 실제 메서드로 재현했다. deferred confirmation 회귀 RED→GREEN, 확인 이전 ID 고정. 취소 실행 시간 누락도 RED→GREEN, 원래 abort reason identity와 요청1/예약1/wait0 및 logger 실패를 검증했다. 재검토 후 unresolved finding 없음.
- Nest는 HTTP 인터페이스, owner/busy, 시작/삭제 race, durable index crash repair, 역사 artifact byte 보존, profile 없이 batch/PDF 읽기, 초기 진행/복구/취소, bounded retry와 정산까지 fixture로 검증했다.

| 최종 검사 | 결과 | evidence (output/storyboard/2026-09-29 아래) |
| --- | --- | --- |
| Angular 전체 Karma/ChromeHeadless | **5395/5395 PASS**, exit0 | angular-full-tests.log |
| Angular local AOT build | PASS, exit0 | angular-build.log |
| Angular SCSS validation | **6/6 PASS**, exit0 | angular-styles.log |
| Nest 최종 build + storyboard/shortform/billing/jobs 회귀 | build PASS, **875/875 PASS**, exit0 | nest-final-tests.log; backend-results.md |
| Web credits/operations/inference | **33 suites/503 tests PASS**, build PASS | performance.md |
| Web 전체 unit | 277 suites pass/2 fail/5 skip; 2959 pass/**7 fail**/21 skip | performance.md; Web 실행 output은 담당 agent tool transcript(파일 미저장) |
| 브라우저 fixture | PASS, JS error0, 외부 요청 모두 mock | browser-results.json; browser-qa.log; storyboard-browser-qa.cjs |
| 3repo diff check/독립 리뷰 | whitespace PASS, 두 발견 보완 재검토 완료 | review.md |

Web 기존7개 실패는 원본 checkout에서 동일 재현했다(43 pass/7 fail). ProductCatalogService5개와 EffectiveAccessService2개에서 expected registeredPluginKeys에 shortform_director가 빠진 기존 기대값이다. 관련 소스/spec을 이번 원장 표시 변경 범위에 포함하지 않았다. 상세 이름은 성능 보고서에 있다.

Angular CLI는 설치된 Node24.19.0을 명시했다. npm/npx가 Homebrew24.3.0을 선택하면 Angular22 최소 버전 검사에 실패한다. Nest/Web은24.3.0. Karma/Playwright 및 Nest ephemeral localhost HTTP는 sandbox 밖의 승인된 로컬 테스트 실행을 사용했다. 최종 Nest의 sandbox 1차 실행은 listen EPERM으로 실패해 같은 명령을 허용 환경에서 재실행했다. 폰트 fixture404/의도적 장애 로그는 제품 운영 실패와 구별한다.

재현 명령(해당 격리 repo cwd):

```sh
# Angular
/Users/jina/.nvm/versions/node/v24.19.0/bin/node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless
/Users/jina/.nvm/versions/node/v24.19.0/bin/node node_modules/@angular/cli/bin/ng.js build --configuration=local
node --test test/breakpoints-scss-class-validation.test.mjs
# Nest
npm run build
node --test test/storyboard*.test.js test/shortform-director*.test.js test/billing*.test.js test/jobs*.test.js
node scripts/storyboard-stage-timing-benchmark.js
# Web
npm run build
npm test -- --runInBand
```

브라우저 재현은 Angular local serve를127.0.0.1:4208에 띄운 뒤 output의 storyboard-browser-qa.cjs를 실행한다. 브라우저 모든 backend 호출은 fixture이며 실제 DB/provider/사용자 정보는 쓰지 않는다.

## 화면·성능·충돌 경로

화면: `profiles-{dark,light}-{1920,1280,768,390}.png`, `purpose-cleared.png`, `delete-selection.png`, `delete-retry.png`, `preserved-results.png`, `preserved-scenario.png`. 조합 이벤트 역순 replay와 Chrome CDP 실제 composition engine, 저장 payload를 확인했다. **macOS 물리 한글 키보드/Electron 설치형 IME는 미검증**이다. 긴 목적·스타일·키워드, 메뉴·토큰 danger 색, 실행 미터·locked 행·실패/결과 보존도 캡처했다.

성능은 [상세 보고서](../diagnostics/2026-09-29-storyboard-performance.md)에 있다. 기존 실제 로그의 작업 총시간610563ms/142428ms는 서로 다른 조건의 작업이므로 전후 개선으로 비교하지 않는다. 성공 단계/수량 로그가 없어 병목 비중은 특정할 수 없다. 오프라인 전후20-profile에서 obsolete reads180→0(100-profile900→0), profile 개수/필수 조회는 같음. retry/cancel/restart fixture의 요청/예약·논리시간·결과 hash, document 저장/복구 호출과 output hash는 같았다. nested document load와 inclusive save 시간은 합산하지 않는다.

다른 세션과 잠재 겹침:

| 세션 | 겹칠 수 있는 경로 | 이번 선택 |
| --- | --- | --- |
| W10 공통 UI/폼 | shared/forms, shortform scenario UI, credits | shared ImeEnter 원본은 변경하지 않고 사용. 이번 입력/카드/관리 범위만 변경; W10 scenario UI는 건드리지 않음. |
| W11 홈/보관함 | Angular shell/projects; Nest jobs/archive | shared UI/lifecycle 원본 변경 없음. 기존 JobHistoryService와 JobsService.get 사용. |
| TC4 생성시간 로그 | Nest core/logging/jobs | 새 로그 메뉴/전역 job 계약 변경 없음. 기존 job elapsedMs와 feature timing 사용. |
| 하이라이트/Web | Web inference/operations/credits | Web read-time credit 표시 map 한 항목만 변경. inference/operation 실행 계약 변경 없음. |
| 인계 문서 | .codex 보드/9월29일 세션 | W07 행/카드·본 보고서·성능/계획/리뷰·W07 세션 append만 갱신. 타 세션 미커밋 내용 보존. |

## 남은 검증

실제 AI/실차감·환급/DB/서버 배포/패키징과 macOS 물리 IME는 실행하지 않았다. 실성능 다음 단계는 같은 profile snapshot·수량·모델·retry/cold-warm 조건에서 계측한 단계 duration·완료 수·근거/대본 품질·정산·요청 비용을 비교하는 것이다. 병렬 후보는 Trends/query-plan 및 독립 검색, 서로 다른 slot의 editorial→materials chain이다. 응답 합치는 순서/근거 ID/receipt hash/attempt budget을 보존하고, 취소 시 in-flight가 끝난 뒤 저장 문서 계수·정산이 일치해야 한다. 같은 slot의 editorial→materials는 의존하므로 순서를 유지한다. 병렬화·모델 교체·통합 normalization·추가 캐시는 이번에 적용하지 않았다.

진행상황은 소스/로컬 완료와 실성능 미확인으로 분리해 기록한다. 원본 dev에 병합하거나 배포한 상태가 아니다.


## 후속 native 테스트 앱

사용자의 후속 빌드 요청으로 macOS arm64 local-api 전체 .app 빌드/패키지 확인을 완료했다. 위 초기 기록의 패키징 미실행은 후속에서 해소됐다. [실행·정확한 빌드 범위·근거](2026-09-29-storyboard-native-test-build.md). UI/실AI/물리 IME는 미실행. 기존 Web API 프로세스는 보존했다.
