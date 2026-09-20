# W07 스토리보드 구현·검증 결과

> 이 문서는 설계·구현 당시의 결정과 검증 이력을 보존한다. 이후 수정 및 최신 Git/승인 상태는 [스토리보드 작업 카드](../handoff/tasks/storyboard.md)를 우선한다. 9/21 현재 제품 구현은 별도 worktree에 미커밋이며, 사용자는 `.codex` 문서만 커밋·푸시하도록 승인했다.

2026-09-21 KST. **승인 범위 구현 및 로컬 검증 완료, 코드·문서 모두 미커밋.** 실제 AI/ML·Build5·배포·운영 DB 검증은 실행하지 않았다. W07의 영구 우선순위는 변경하지 않았다.

## 실제 사용자 흐름

1. 최초 설명 화면에서 프로필 추천 또는 직접 생성. 프로필 저장은 무료이며 생성/과금 요청을 하지 않는다.
2. 프로필 목록에서 스토리보드 생성하기 → 주제/시나리오 수와 크레딧 확인 → 동의 → 홈 큐 하나.
3. 기본3×5=15개/75크레딧. 주제1~5, 시나리오2~10, 1개5크레딧. 최소10/최대250크레딧. 서버 quote가 금액·프로필 버전을 확정한다.
4. 조사/주제 생성 후 각 주제 후보를 만들고, 각 후보의 대본→소재→최종 문서를 순서대로 저장한다. 모든 주제의 후보가 끝날 때까지 기다리는 전체 barrier는 없다. 초기 실행 동시성은1이다.
5. 완료 카드 → 주제별 가로 시나리오 → 개요/대본 흐름/선택 대본 세부 내용의3열 화면. 검색어→AI영상→AI이미지 순서, 전체 대본 복사와 PDF.
6. 실패 stage만 최대3회 내부 재시도. 성공한 부모/문서와 서버의 검증된 생산 응답을 보존한다. 재시도 상태/기술 ID/API 비용은 새 사용자 흐름에 표시하지 않는다. 로컬 상투 대체 문서는 새 흐름에서 성공으로 인정하지 않는다.
7. 완성 문서만 과금하고 미완성 수량은 서버의 수량 정산으로 환급한다. 정산 pending 동안 완료로 표시하지 않으며 상세 새로고침으로 재조정한다. 완성1개 이상이면 수정/재생성 잠금·복제만; 완성0개이고 전액 환급 확인 후에만 수정 또는 새 동의/새batch로 생성 가능.

## 화면과 데이터

- 21개 1뎁스/128개 2뎁스, 분야별 목적5개+항상 보이는 직접 입력, 스타일24개를8→16→24개로 표시. 예시·툴팁·목적/스타일 AI 추천 없음.
- 분야/연령 전체와 개별 선택은 배타적. 키워드는 공백을 보존하며 Enter로 추가, IME 조합 Enter는 확정 동작과 분리. 입력중 태그를 버리지 않도록 저장·취소 경계 검증.
- 프로필 카드 아이콘/삭제 제거, 레이블과 값, 넓은 한 줄·좁은 줄바꿈, 메뉴 복제/수정 정책. 모달은 제한 높이+내부 스크롤+하단 버튼.
- 주제에는 추천 이유/시청자의 궁금증/기획 포인트를 응답 계약부터 필수 제공. 간결성/중복 검증, 없으면 성공 처리하지 않는다.
- 최종v2는 대본 중심 구간마다 화면 문구·시각 설명·한영 검색어·영상/이미지 프롬프트를 저장한다. 근거는 제목/요약/안전한 링크로 제공하며 기술ID를 숨긴다. TTS 시간 등 품질 경고는 생성 완료를 막지 않는다.
- v1 결과는 읽기 전용 원본을 유지한다. 옛 장면/여러 컷/프롬프트/컷별 시간은 그대로 PDF로 보존하며 없는 새 검색어나 이미지 프롬프트를 만들어 넣지 않는다.
- PDF는 저장 당시 프로필·주제·선택 문서 전체를 요약표→전체대본표→구간별 제작시트로 구성한다. PDFKit, 기존 번들 한글 폰트 임베딩, 긴 문서 페이지 분리, 선택 구간과 관계없이 전 구간 포함. 인증된 생성 요청 뒤5분/1회용 다운로드 주소, 기존 FileDownloadService 사용. AI 실행 없음.

## 작업 공간과 주요 파일

세 저장소 branch `feature/storyboard-ux-overhaul-20260920`, root `/Users/jina/project/adlight/.worktrees/storyboard-ux-overhaul-20260920`.

|저장소|HEAD(변경 없음)|미커밋 변경 경로 수|
|---|---|---|
|Angular|b511e15824eb7ac20d4802e145a6c3a5923f4eb4|55|
|Nest|c2e227c244e786af4dfa51bd132692eb38cd1cd2|95|
|Web API|9304cec77b30b72a9b89355393878a84896dcd86|33|

마지막 읽기 전용 확인에서 각 HEAD와 로컬 origin/dev 참조는0/0. 네트워크 fetch는 하지 않았으므로 원격의 현재 상태를 새로 확인했다는 의미는 아니다. 원본 세 checkout은 기존 branch/HEAD를 유지하며 clean. 원본 기준 origin/dev 관계는 Angular3/4, Nest0/4, Web0/2였다. 다른 worktree·환경 파일·Electron 코드는 수정하지 않았다.

- Angular `src/features/shortform-director/models/storyboard-profile-catalog.ts`, `components/operating-profile-form/`, `operating-profile-card/`, `storyboard-generation-dialog/`: 입력·프로필정책·동의.
- Angular `pages/profiles-page/`, `batch-results-page/`, `scenario-page/`, `legacy-results-page/`, `state/shortform-director-batch.store.ts`, `services/shortform-director-batch.service.ts`, `storyboard-export.service.ts`: 조회/이동/복사/다운로드. `src/shell/projects/`는 공통 큐/보관함 연결.
- Nest `src/modules/shortform-director/domain/storyboard-{v2,production-v2,batch,batch.repository,profile-settings}.ts`: 계약. `infrastructure/json-storyboard-batch.repository.ts`: owner별 영속 manifest/잠금.
- Nest 같은 module `application/storyboard-batch.service.ts`, `storyboard-batch-stage-adapter.ts`, `storyboard-batch-pipeline.ts`, `storyboard-batch-discovery.ts`, `storyboard-batch-checkpoints.ts`, `storyboard-batch-document-store.ts`, `storyboard-batch-settlement.ts`, `storyboard-batch-recovery.service.ts`, `storyboard-batch-read.service.ts`: 생성·중단복구·정산·조회. `storyboard-batch.executor.ts`는 기존 Jobs 실행기 연결.
- Nest `application/storyboard-{pdf-model,pdf-renderer,pdf.service,legacy-export-reader}.ts`, presentation PDF controller: 저장값 PDF. 기존 artifact registry와 v1 service 재사용.
- Web API `src/modules/operations/`의 storyboard quote/receipt/settlement, `src/modules/shortform-director-inference/`의 v2 prompt/schema; `src/core/database/migrations/admin/1790000000000-AddStoryboardOperationSettlement.ts`: 운영 migration **미실행**.

## 검증 결과

Node24.19 PATH로 실행. 실제 provider·운영 서버·운영 DB를 사용하지 않았다. 아래는 각각의 계층을 연결/분리해 확인한 결과이며, 실제 AI를 포함한 하나의 운영 end-to-end 실행을 뜻하지 않는다.

|대상|최종 결과|
|---|---|
|Angular 스토리보드/홈/다운로드/안내|704/704 PASS|
|Angular SCSS 검사|6/6 PASS|
|Angular production build|PASS|
|Nest 스토리보드/billing/jobs 집중 회귀|853/853 PASS|
|Nest build, ncc bundle|PASS; 기존 한글 폰트6개 asset 복사 확인|
|Web API inference/operations/credits|516/516 PASS,36 suites|
|Web API build|PASS|
|별도 임시 PostgreSQL|1/1 PASS: 실제 migration up/down,rollback,동시 부분정산,JSONB 성공응답 저장 후 새 service에서 재사용|
|실제 Angular+가짜 HTTP 브라우저 흐름|무료프로필→4×4/80동의→단일홈큐→완료프로필→주제→시나리오 PASS,JS오류0|
|영속 저장 복구|실제 임시 artifact/manifest와 가짜 추론으로2회 프로세스 재시작,완료 부모/문서 재생성 없음|
|생성 수량/실패 경계|1×2,5×10,15요청12완료,부모부족,취소,전부실패 및 정산 확인 상태 검증|
|PDF|현재 렌더러로6쪽/9쪽 생성,텍스트 추출·전 페이지 Poppler 시각 검사 PASS|

대표 명령:
```sh
# Angular
npx ng test --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/**/*.spec.ts' --include='src/shell/projects/**/*.spec.ts' --include='src/core/download/*.spec.ts' --include='src/core/navigation/page-guide-content.spec.ts'
npm run test:styles
npm run build
# Nest
npm run build
node --test test/shortform-director*.test.js test/storyboard*.test.js test/billing-*.test.js test/billable-job-attempt-coordinator.test.js test/jobs*.test.js
npm run bundle
# Web API
npm test -- --runInBand shortform-director-inference operations credits
npm run build
node --test test/storyboard-settlement-postgres.test.cjs
```

sandbox에서 로컬 포트 사용이 막힌 초기 실행과 Angular 빌더 중단은 로컬 테스트 권한으로 재실행했다. 테스트 의미를 완화하지 않았다. 실제 사용자 프로필/크레딧은 사용하지 않았다. Angular fixture 데이터로1920/1280/768/390 폭의 다크/라이트 상세, 모달 스크롤/포커스, 긴 대본/PDF를 확인했다. 가짜 홈 계정/리소스 응답 때문에 오른쪽 계정 정보는 실제 서비스 검증 대상이 아니다.

증거 파일: `/Users/jina/project/adlight/output/storyboard/2026-09-21/`에 화면 PNG, 브라우저 QA 스크립트, 최종 테스트/빌드 로그. PDF는 `/Users/jina/project/adlight/output/pdf/storyboard-implemented-sample.pdf` 및 `storyboard-implemented-long-sample.pdf`. 예시 내용은 테스트 fixture이며 실제 생성 결과가 아니다.

## 전체 변경 검토와 보완

새 맥락의 검토1회 수행. 실제 WebApi 오류 분류, 응답 유실 시 성공 응답 재사용, 상세 새로고침의 정산 복구, 후보 훅1000자 경계 불일치를 실패 테스트로 재현하고 수정했다. 홈 완료 개수, 전체 실패 상세의 동작하지 않는 생성 버튼, legacy PDF 컷 시간 누락도 명시 요구와 직접 연결돼 같은 수정 pass에서 보완했다. 보류한 검토 minor는 없다. 최종 회귀 테스트는 이 수정 뒤 실행했다.

## 구현 판단과 제한

실행 ledger 원본은 Nest `.superpowers/sdd/2026-09-21-storyboard-implementation-plan/progress.md`에 보존한다. 기록을 커밋하지 않았으므로 삭제하지 않았다.

1. 문서/ledger 유지와 미커밋 작업 검토: 사용자 no-commit 지시 우선. 비용: 승인 전 Git 커밋으로 복구 불가.
2. 기존 generic artifact registry/codec 재사용: owner 격리와 영속 기능이 이미 있음. 비용: 신규 v2 boundary 검증에 의존.
3. 기존 profile card 재사용, toneKeywords20→24: 승인된 스타일 모두 보존. 비용: 구버전 소비자의20개 제한은 별도 배포호환 검토 대상.
4. 생성 요청보다 적은 근거 있는 결과는 허용: 가짜 내용으로 채우지 않음. 비용: 제한적 보완 후 미완성 환급 가능.
5. 새 batch adapter로 기존 inference client 사용: 옛 수동승인 DTO를 위조하지 않음. 비용: v1/v2 실행 경로를 둘 다 유지.
6. 시도 수는 호출 전에 저장, 성공 checkpoint는 저장 완료 후: 저장 오류를 provider 재시도로 오인하지 않음. 비용: 응답 불명 호출은 시도 수와 실제 공급자 비용을 소비할 수 있음.
7. 정산 migration은 admin connection: 실제 operation/credit 소유 DB에 맞춤. 비용: 배포 시 해당 migration 적용 필요.
8. immutable artifact+batch manifest 사용: v1 이력 불변. 비용: 중단 시 index/manifest 재조정 필요.
9. 기존 수집·근거 normalization 재사용, 옛 v1 fallback 미변경: 새 batch만 local 성공 차단. 비용: 옛 경로는 별도 정리 과제.
10. owner-bound read-only operation status API 추가: 복구가 시작 API를 재호출하지 않도록 함. 비용: API 표면 추가.
11. 새 결과 DTO/route와 읽기 전용 legacy reader 분리: 기존 다중 컷 보존. 비용: 두 버전 표시 코드 유지.
12. PDF 인증된 생성+1회용 capability: 다운로드 bridge에 bearer query를 넣지 않음. 비용: 취소/만료 후 PDF 주소 재발급. 폰트는 기존 번들 경로 재사용, worktree에만 원본 폰트 읽기 symlink.
13. generic admin 성공/실패 복구에서 storyboard 제외: 전액정산으로 부분 결과를 덮지 않음. 비용: 향후 전용 관리자 수량정산 UI/API가 필요할 수 있음.
14. 서버 production receipt에 검증된 전체응답/요청hash 보존: 응답 유실 뒤 새 생성 없이 복구. 비용: JSONB 저장량 증가, 겹친 미확정 요청의 외부 exactly-once 보장 없음.
15. 전체 실패 상세 카드에 동일 수량/동의창 연결: 실제 새 생성 보장. 비용: 화면은 과거 snapshot, quote는 현재 프로필을 다시 검증.
16. 극소폭 카드에서 세부정보2행 이상 허용, 상세3열은 내부 가로스크롤: 텍스트 읽기 우선. 비용: 작은 화면에서 스크롤 증가.
17. worktree/ledger 보존: 승인 전 commit/push/merge/cleanup 하지 않음. 비용: 작업 공간 유지.

실제 AI 생성 품질·검색어 적합성·실제 공급자 지연/오류율은 미검증이다. Electron/Build5 전체 배포 패키지 실행, 서버 migration/배포, 운영 크레딧 사용·환급은 하지 않았다. 단위·영속 저장·DB·브라우저 검증을 통과했다고 이들을 완료한 것으로 간주하지 않는다. 커밋·푸시는 전체 결과를 본 사용자의 명시 승인 이후에만 가능하다.


## W07 큐 직후 실패: 추론 입력 경계 수정 (9/21)

사용자 오류번호 b2722b30 보고. 첨부30줄은 이전quote503이고 해당번호 자체는 첨부/현재로그/오류보고DB에서 찾지 못했다. 실제 앱 기록의22:18:34 시작→22:18:35 실패한 shortform_director_ff413bfa-130d-4b0e-839c-3ea87de5089d 작업 확인. batch는source:trends 성공, discovery:queries 1회 직후 종료. 로컬 manifest와서버operation_runs(58e8870f-578c-4248-9654-d16ecbbe4842) 모두요청4/완료0/차감20/환급20/정산confirmed(22:18:35.302Z) 확인. 읽기전용조회, 수동환급/재생성 없음.

저장된 실제프로필과 실제ResearchInputBuilder로 첫요청 재구성 후 Web API 실제input guard에넣어 SHORTFORM_DIRECTOR_INFERENCE_INPUT_INVALID 재현. batchContext.stageKey='discovery:queries'가 URI탐지에걸리며 그필드만빼면통과. 오류원문은executor의최종환급처리로보존되지않아 과거HTTP본문을확보한것은아니지만 동일입력검사실패를로컬에서재현했다. 서버에서소비하지않는로컬체크포인트이름을discovery·topic/candidate/editorial/material 전송에서제거. 로컬체크포인트키/배치·과금·slot연결은유지하고 Web API입력방어는완화하지않았다.

기존discovery/stage테스트에API경계허용필드회귀추가, 수정전3실패후 Nest스토리보드64/64통과. discovery·stage의생성요청을실제Web API입력guard에연결한임시교차검증6/6통과(가짜공급자; 실제AI없음). Nest build/ncc bundle와git diff --check통과. 이전Angular254/254검증이후이번UI변경없음. 현재실행앱은기존패키지이므로작업Electron에서재빌드필요. 실제AI/Build5/전체앱패키징/원격접속/DB변경/commit/push없음. 코드·문서모두미커밋.


## W07 두 번째 생성 실패5898ca76: 상세 진단 보완·단일 호출 승인검토 대기

22:24:29 시작한 batch run.director.2f963e2c4f844fdc85c88d796a815218은 source:trends 성공 후 discovery:queries 3회 시도,22:24:43 실패. 로컬기록과서버operation_runs cf63dec0-1b65-4461-b12b-d067604606a6에서30차감/30환급확인. 오류번호 자체나세부실패응답은기록되지않았고사용자도Web API터미널로그없음을확인. 첫실패(stageKey입력검사)와달리이번실패원인은미확정.

누락된진단을수정: stage 재시도경계에 batch/stage/시도수/오류분류/HTTP·provider상태/검증통과여부/안정코드만구조화로그로기록. 키·프롬프트·응답원문미노출,사용자화면에재시도미노출. 로그기록실패는원래오류·정산을변경하지않음. query-plan로컬검증원인보존. RED후Nest스토리보드66/66·build/bundle·diff check통과.

실패프로필의검색어생성1회만실행하는진단스크립트 /private/tmp/storyboard-query-diagnostic.cjs 준비. 기본dry run으로입력guard통과및네트워크/DB호출0확인. 사용자가단일실제AI진단승인했으나auto-review가구체제공자/전송payload명시부족사유로실행전거절했다. 우회/재시도하지않았고실제AI호출0회. OpenAI Responses URL/model/profile입력/시스템지시/응답schema를자격증명없이 /private/tmp/storyboard-query-openai-request.json에미리보기작성. 구체전송범위를보여주고추가확인필요. 아직원인수정완료아님. 코드·문서미커밋,commit/push없음.


## W07 5898ca76 단일 AI 진단·관련 키워드 검증 결함 수정

사용자가구체OpenAI제공자/model/프로필전송payload 확인후다시승인. 단일진단스크립트실행: 실제OpenAI Responses API 정확히1회, HTTP200/공급자출력검증통과/데스크톱응답projection통과, projectResearchQueryPlan에서거절됨확인. 앱크레딧차감·operation상태변경·후속검색/생성없음. 기존실패작업30전액환급유지.

코드비교에서inferenceProfile은settingsV2.relatedKeywords(etf·용어해설)를AI에전달하지만projectResearchQueryPlan의derivedFrom근거는이름/분야/대상/목적/focusKeyword만포함하는불일치발견. 관련키워드를근거로한정상ETF검색어가거절되는회귀를RED로재현한뒤관련키워드도검증근거에포함. 키워드없는프로필의ETF근거거절및근거없는계약논란첨가거절유지. Nest스토리보드/조사관련148/148·build·ncc bundle·diff check통과.

정확한한계: 단일실제호출진단은실패지점만출력하고생성된검색어원문은저장하지않았으므로그응답의어느항목이실패했는지는확보하지못했다. 관련키워드누락은별도재현으로확인한명확한결함이며, 이것이해당실제응답의유일한실패원인인지또는수정후전체생성이완료되는지는미검증. 추가실제AI호출하지않음. 실패원인로그보완과함께작업Electron재빌드후사용자확인필요. 코드·문서미커밋,commit/push/Build5/배포없음.
