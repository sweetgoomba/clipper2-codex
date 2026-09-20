# 스토리보드 UI/UX 재설계

최종 확인: 2026-09-21 KST. **별도 worktree의 코드 3개 저장소 미커밋 / `.codex` 문서만 커밋·푸시 승인.** 사용자가 생성 결과를 확인하고 후속 UI 수정을 요청했다. 아래 검증 수치는 각 수정 시점의 기록이며 최신 원격 dev 통합 후 재검증 결과가 아니다. 운영 배포 검증은 미실행.

[전체 작업 현황](../WORKBOARD.md) · [구현·검증 결과](../../implementation/2026-09-21-storyboard-implementation-verification.md) · [구현 계획](../../implementation/2026-09-21-storyboard-implementation-plan.md) · [9/21 세션](../../records/sessions/2026/09/21.md)

## 현재 결과

W07은 이번 세션 선택이며 다른 작업보다 영구 우선하지 않는다. 프로필→주제→시나리오→상세 생성 의존성을 유지하고 사용자 조작을 무료 프로필 저장→수량·크레딧 동의→하나의 홈 큐로 통합했다.

- 기본3×5, 주제1~5/주제별2~10, 완료 문서1개5크레딧. 서버 quote/수량 정산, 미완성 환급, 서버 확인 전 환급 완료 표시 금지.
- 성공 stage·문서 저장/재개, 실패 stage 최대3회 내부 재시도. 재시도·API비용·기술ID는 새 화면에 노출하지 않음. 새 흐름에서 local 대체 결과 성공 처리 금지.
- 21/128 분야, 분야별 목적5개+직접입력, 스타일8→16→24, Enter만 태그 확정. AI 목적·스타일 추천은 고도화로 보류.
- 프로필 카드 아이콘/삭제 제거, 레이블·값/반응형, 복제·수정 메뉴. 완료1개 이상 수정/재생성 잠금; 완료0개 전액환급 confirmed 뒤 새 동의로 재사용.
- 최초4단계 설명, 내부 스크롤 모달, 결과의 뒤로가기/전체 프로필 카드, 주제별 가로 시나리오(타입/타이틀/훅).
- 주제 필수3항목을 생성/API/저장까지 연결. 최종3열 대본 중심, 화면문구 유지, 소재 검색어→영상프롬프트→이미지프롬프트 모두 표시.
- 실제 PDF 다운로드 구현: 프로필·주제·선택 문서 전체, 요약표/대본표/구간별 제작시트, 한글 번들폰트, 가변 페이지. 기존 v1 다중 컷은 원본·시간을 보존한 읽기 전용 조회/PDF.

## 작업 공간

branch `feature/storyboard-ux-overhaul-20260920`, root `/Users/jina/project/adlight/.worktrees/storyboard-ux-overhaul-20260920/`.

|저장소|변경 없는 HEAD|
|---|---|
|desktop/clipper_angular|b511e15824eb7ac20d4802e145a6c3a5923f4eb4|
|desktop/clipper_nestjs|c2e227c244e786af4dfa51bd132692eb38cd1cd2|
|web/clipper_web_api|9304cec77b30b72a9b89355393878a84896dcd86|

원본 checkout 5개는 모두 깨끗하며 기존 브랜치를 유지한다. 9/21 원격 dev를 fetch해 재확인한 결과:

| 작업 저장소 | 기존 파일 변경 | 신규 파일 | 합계 | HEAD 대비 원격 dev 추가 커밋 |
|---|---:|---:|---:|---:|
| desktop/clipper_angular | 42 | 26 | 68 | 162 |
| desktop/clipper_nestjs | 45 | 54 | 99 | 64 |
| web/clipper_web_api | 18 | 15 | 33 | 3 |
| desktop/clipper_electron | 0 | 0 | 0 | 5 |
| desktop/clipper_python | 0 | 0 | 0 | 11 |

5개 작업 브랜치는 모두 upstream이 없고 원격에 같은 이름의 브랜치도 없다. HEAD에만 있는 커밋은 모두 0개이며 표의 변경은 전부 미커밋이다. 원격 dev와 수정 파일 경로가 겹치는 것은 Angular 17개, Nest 3개, Web API 0개다. 경로 중복은 실제 merge conflict 확정을 의미하지 않는다. 소스 병합/rebase는 실행하지 않았다. `.env` 등 로컬 설정과 빌드 산출물은 Git 제외 상태를 유지한다.

`.codex`는 별도 저장소의 main이며 이번 사용자 승인은 문서 커밋·푸시에만 적용한다. 코드 커밋·푸시·통합은 별도 승인 전 수행하지 않는다.

## 검증과 다음 단계

- Angular704/704, SCSS6/6, Nest853/853, Web API516/516 통과. 세 저장소 build 및 Nest ncc bundle 통과.
- 임시 PostgreSQL migration up/down·동시정산·rollback·성공응답 JSONB replay 통과. 운영DB 변경 없음.
- 실제 Angular+가짜 API로 프로필→동의→홈큐→결과 이동, 화면 폭/테마/모달 확인. 실제 임시 디스크2회 재시작 복구와 수량 최소·최대/부분실패 검증.
- 실제 PDFKit6쪽·9쪽 예시 전 페이지 렌더/한글·필드 확인. 예시 데이터는 fixture이며 실제 AI 출력 아님.
- 최종 전체검토에서 지적된 오류분류/응답유실/정산새로고침/후보길이 및 카드/PDF누락 수정 후 회귀 통과. 보류한 minor 없음.

다음은 사용자의 구현 화면/결과 확인이다. 실제 ML·Build5는 별도 승인 없이는 실행하지 않는다. 실제 AI 품질/검색 적합성·Electron 전체 패키지·운영 DB/배포는 검증 완료로 간주하지 않는다. 서버 직접 접속·배포 금지. **이번에는 `.codex` 문서만 커밋·푸시 승인. 코드 commit/push는 별도 승인 전 금지.**

## 과거 근거와 변경 이력

아래 항목은 각 작업 당시의 기록이다. 문서 미커밋·승인 대기 등 과거 상태는 위 최신 상태와 이후 기록을 우선한다.

[8/25 TODO](../../todos/2026-08-25-storyboard-followups.md), [8/25 세션](../../records/sessions/2026/08/25.md), [9/20 기록](../../records/sessions/2026/09/20.md), [9/21 설계](../../implementation/2026-09-21-storyboard-ui-design-draft.md), [목적·스타일](../../implementation/2026-09-21-storyboard-purpose-style-catalog-draft.md), [최종 상세 재검토](../../implementation/2026-09-21-storyboard-final-detail-reassessment.md).

과거 TODO 전부를 미완료로 간주하지 않았다. 품질 경고·복제·archive 제거의 기존 구현은 유지하고 새 정책과 연결했다. 옛 영상/render 코드는 호환 경로에 남아 있으며 새 batch는 영상 렌더를 실행하지 않는다. 9/4 제거됐던 검색어는 승인된 v2 계약으로 다시 도입했다. 과거 공급자 단가·환율을 현재 값으로 인용하지 않았다. 제품 미적용/Task2 진행이라는 이전 카드 내용은 이번 구현 결과로 대체한다.


## 로컬 앱 확인 준비 (9/21 후속)

원본 Electron 빌드는 원본 형제 폴더를 참조하므로 별도 구현이 반영되지 않았다. 기존 storyboard 작업 공간에 Electron/Python worktree와 Git 제외 로컬 설정·키·uv 바이너리를 준비했다. 실행 명령은 동일하며 cwd만 새 `desktop/clipper_electron`, `web/clipper_web_api`로 바꾼다. 자세한 명령은 작업 공간 `LOCAL-PREVIEW.md`. Electron/Python 소스 변경 없음, Electron 설정테스트41개/tsc 통과. 전체 앱 빌드는 사용자 실행 대기.

새 정산용 DB migration은 아직 미실행이며 개발전용DB 여부/적용 승인을 질문했다. API/앱/실제AI를 임의로 실행하지 않음. 원본checkout 유지, commit/push 없음.


### 로컬 실행 선행조건 정정

실제 API 시작에서 plugin_key 부재 확인. 로컬Docker DB metadata 읽기전용 조사 결과 Admin38/User3/Release1 미적용(신규스토리보드 포함). 기존plugin entitlement migration도 미적용이며, 과거이력삭제/구형테이블제거 migration이 포함돼 자동전체적용하지 않았다. 기존DB보존+복제DB 적용 또는 백업후개발DB갱신 선택을 사용자에게 질문한 상태. 이 결정/DB정렬 전 로컬 API 실행 문제는 미해결이며, 기존 코드의 로컬단위·임시DB검증통과와 구분한다. 코드변경/DB변경/commit/push없음.


### 로컬 실행 선행조건 해결

사용자가 개발DB 백업 없이 갱신 승인. 동일 로컬Docker DB에 User3/Admin38/Release1건 적용 완료, 미적용0건. plugin_key와스토리보드정산schema 확인, 실제API 초기화/정책seed 및 /health HTTP200(3DBok) 검증. 위 승인대기/시작문제미해결 상태는 이 기록으로 대체. 기존DB를사용하며복제DB/백업생성없음. 검증용서버는종료, 사용자start:dev 재실행가능. 기존종료훅defaultDataSource문제는 별도이며 이번수정범위제외. 코드·문서미커밋,commit/push/실제ML/Build5/원격운영DB작업없음.


## W07 프로필 없는 첫 화면 버튼 위치 조정 (9/21)

사용자 요청대로 첫 화면 하단의 `프로필 추천`·`프로필 생성하기`를 상단 actions로 이동하고 기존 상단 생성 버튼과 중복되지 않도록 했다. 프로필이 있는 화면은 기존 생성 버튼 유지. 사용하지 않는 하단 actions CSS 제거. 기존 빈 상태 테스트를 보완해 수정 전 1실패/10성공 확인 후 스토리보드 Angular253/253 통과, packaged Angular build 통과. 실행 중인 Electron 패키지에는 재빌드가 필요하며 전체 Electron 패키징/실제ML/Build5는 실행하지 않았다. 작업 branch 유지, 코드·문서 모두 미커밋, commit/push 없음.


## W07 생성 동의 모달의 반복 실패 조사·안내 보완 (9/21)

실행 중인 앱 로그에서 storyboard-quote의503과 StoryboardBatchPreflight 서비스 준비 검사 실패 확인. 로컬 개발Admin DB를 READ ONLY로 확인한 결과 OpenAI 활성키는 복호화 가능하지만 기존 네이버 키들의 naver_usage_apis가 모두 빈 배열이다. 기존1789000000000-AddNaverUsageApis migration은 기존키에 권한을 추정하지 않고 빈 배열을 설정한다. 검색/데이터랩이 둘 다 준비 안 됨으로 판정되어 과금quote 전에 차단된다. 실제 네이버 개발자센터 권한은 확인하지 않았으며 사용자에게 관리자페이지 API 키의 사용 API 설정 확인을 안내했다. 사용자가 관리자페이지에서 직접 확인 예정. DB 설정/공급자 키/잔액을 임의로 변경하지 않았다.

Nest preflight는 준비되지 않은 provider 이름과 안정코드 STORYBOARD_SERVICES_NOT_READY를 반환하도록 보완, Angular 동의 모달은 일반 수량·크레딧 조회실패 대신 생성 서비스 설정 확인·관리자 문의·미차감 안내를 표시한다. 준비검사 및 동의 전 차단 유지, 사용자 화면에 provider 기술정보나 서버 원문 미노출. 누락설정 HTTP필터 회귀와 UI 차단 회귀를 RED 확인 후 구현. Nest 집중81/81, Angular 스토리보드254/254 및 양쪽 build(Angular packaged) 통과. 실제 생성/차감/외부 공급자 호출/Build5/전체 Electron 패키징 없음. 설정 해결 및 사용자 재확인 대기이며 생성 성공으로 보고하지 않는다. 코드·문서 미커밋, commit/push 없음.


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


## W07 프로필 상단 두 버튼 표시 조건 정정

사용자는추천·생성두버튼유지를요청했으나이전수정은빈화면에만표시해프로필생성후추천이사라졌다. 상단프로필수조건및openPresetDialog의빈목록조건제거. 프로필유무와무관하게 `프로필 추천`·`프로필 생성하기` 유지, busy비활성/편집중추천전환차단유지,모달안추천버튼없음. 기존프로필상태에서두버튼표시와클릭후추천/생성다이얼로그열림회귀를RED확인후수정. Angular스토리보드254/254·packaged build·diff check통과. 과거빈화면한정권고·기록은이결정으로대체. 실행중패키지에는재빌드필요. 코드·문서미커밋,commit/push없음.


## W07 사이드바 도움말의 구형 기능 설명 정정

사용자지적대로스토리보드사이드바도움말의레퍼런스영상분석설명제거. 같은잘못된문구를쓰던공통플러그인subtitle도현재흐름으로통일: “프로필에 맞는 주제와 시나리오를 제안해 다음 영상을 기획하도록 돕습니다. 대본과 이미지·영상 검색어, AI 생성 프롬프트를 함께 제공합니다.” 기존설명단언만갱신,동작변경없음. 관련Angular27/27·packaged build·diff check통과,대상에서구형문구잔존없음. 앱재빌드후반영,코드·문서미커밋,commit/push없음.


## W07 홈 스토리보드 카드 너비·글자 크기 조정

사용자 요청에 따라 홈 스토리보드 카드만 기존 152px에서 304px로 확대했다. 높이 270px는 유지하고, 공간이 좁으면 부모 너비 이내로 축소한다. 타이틀 16→13px, 본문 12→11px, 라벨 11→10px 및 카드 배지·하단 제목/날짜 글씨도 축소했다. 상단 칩과 하단 개수 배지를 위한 여백, 설명 목록 기본 margin 제거, 긴 단어 줄바꿈을 적용했다. 다른 플러그인 카드 규칙과 API/데이터 동작은 변경하지 않았다.

관련 Angular 단위 테스트 87/87, packaged build, git diff --check 통과. 실제 컴포넌트 SCSS를 사용한 별도 샘플 렌더에서 다크/라이트 304×270px 및 240px 좁은 컨테이너 확인, 샘플 텍스트 잘림·배지 겹침 없음. 실행 중 Electron 앱의 실제 데이터 화면은 재빌드 후 사용자 확인 필요. 로그: /private/tmp/storyboard-card-size-test.log, /private/tmp/storyboard-card-size-build.log. 코드·문서는 미커밋이며 커밋/푸시, 실제 AI 호출, Build5, 배포는 하지 않았다.


## W07 홈 카드 250px·전체 스토리보드 복사·PDF 패키징 오류 수정

- 홈 스토리보드 카드 너비를 사용자 요청대로 304px에서 250px로 축소했다. 기존 축소 폰트와 좁은 컨테이너 대응은 유지한다. 실제 SCSS 샘플 렌더에서 다크/라이트 250×270px 및 240px 컨테이너, 샘플 글자 잘림 없음 확인.
- `전체 대본 복사`를 `스토리보드 복사`로 바꾸었다. 프로필(타겟·목적·스타일·키워드), 주제 및 기획 3항목, 개요(타입·타이틀·훅·길이), 모든 대본 구간의 시간·대본·화면 문구·보여줄 화면·한/영 검색어·영상/이미지 프롬프트, 조사 근거와 참고사항을 텍스트로 구성한다. 선택한 구간과 관계없이 전체를 순서대로 복사하며 기술 ID는 제외한다. 구간별 복사는 유지했다.
- PDF 실제 앱 로그 2026-09-20T22:41:07Z/15Z의 POST 오류는 `Cannot find module '#standard-fonts/Helvetica'`였다. PDFKit 생성자에서 기본 Helvetica를 동적 로드하는 과정이 ncc 패키징 상태에서 실패해, 문서 생성과 저장 창 이전에 중단됐다. 앱에 포함된 한글 글꼴을 생성자부터 지정하도록 수정했다. 실제 ncc 번들 재현 테스트에서 동일 오류 RED를 확인한 후 수정하여 PDF 및 임베디드 글꼴 생성 통과. 저장 흐름은 기존 문서 조회·PDF 생성·일회성 다운로드 티켓·Electron 저장 창/저장 순이며, AI 재생성이나 추가 과금은 없다.
- 검증: Angular 스토리보드/카드 275/275 및 packaged build, Nest 스토리보드 67/67 및 build/ncc bundle, 양쪽 diff check 통과. 샘플 PDF 3페이지 생성 후 기획 개요·세부내용 페이지의 한글과 표 배치를 확인했다. 실행 중 패키지의 실제 저장 창부터 파일 저장까지는 재빌드 후 사용자 확인 필요.
- 로그: /private/tmp/storyboard-copy-red.log, /private/tmp/storyboard-export-copy-green.log, /private/tmp/storyboard-export-copy-build.log, /private/tmp/storyboard-pdf-fix-red.log, /private/tmp/storyboard-pdf-fix-green.log, /private/tmp/storyboard-pdf-fix-build.log, /private/tmp/storyboard-pdf-fix-bundle.log. 코드와 문서는 전부 미커밋. 커밋/푸시·실제 AI 호출·Build5·서버 접속/배포 없음.


## W07 추천 프리셋 새 입력 구조 전환·추천 모달 디자인 정리

기존 추천 10개는 자유입력 `domain`/대상 문자열만 갖고 `settingsV2`가 없어, 새 생성 폼의 분야 ID가 비어 있었다. 이번에 기존 추천 내용을 모두 새 프리셋으로 교체했다: 뉴스 뒤의 맥락, 월급 지키는 돈 공부, 바로 써먹는 AI 도구, 알고 보면 더 재밌는 K-POP, 오늘 볼 작품 골라드립니다, 게임 입문 길잡이, 냉장고 속 재료로 한 끼, 주말에 떠나는 국내 여행, 덜 힘들게 사는 자취 살림, 일상 속 왜 그럴까.

각 프리셋은 현행 카탈로그의 분야·세부 분야 ID, 성별·연령, 해당 분야 제작 목적, 스타일, 관련/금지 키워드를 갖는다. 수동 폼과 같은 buildProfileWorkflow로 기존 API 필드를 함께 구성하고 선택 시 settingsV2를 깊은 복사한다. 길이 표시는 제거하되 기존 생성 contract의 내부 기본값 30초는 유지한다. 기존 저장 프로필은 수정하지 않았다.

추천 모달은 폭 최대 880px, 제목 18px·카드 제목 14px·본문 12px·레이블 11px로 정리했다. 분야/대상/목적/스타일의 레이블과 값을 정렬하고 키워드는 펼침 영역에 표시한다. 헤더는 유지하고 카드 목록만 스크롤하며, 좁은 화면은 1열이다. 좁은 화면에서 사이드바가 모달을 가리던 쌓임 순서도 해당 모달에서 수정했다.

검증: 실제 추천 버튼→10개 각각 이 프로필 사용→실제 Material 생성 폼→저장 경로의 카테고리·타겟·목적·스타일·태그 보존 회귀 RED 후 GREEN. Angular 스토리보드 256/256, 스타일 검사 6/6, packaged build, diff check 통과. 외부 API를 모두 가짜 응답으로 차단한 실제 Chrome에서 다크/라이트 1280/390px, 내부 스크롤·가로 넘침·사이드바 가림 없음 확인 및 10개 각각 분야명 표시/생성 버튼 활성화 확인. 로그 /private/tmp/storyboard-presets-{red,green,build,styles}.log, 스크린샷 /private/tmp/storyboard-presets-{dark,light}-{1280,390}.png.

코드·문서 모두 미커밋. 커밋/푸시·실제 AI 호출·Build5·서버 접속/배포 없음. 실행 중 Electron 앱에는 재빌드 후 반영된다.


## W07 홈 카드 200px·PDF 파일명 타이틀만 사용

사용자 요청에 따라 홈 스토리보드 카드 너비를 250→200px로 변경했다. PDF 다운로드 이름은 현재/이전 결과 모두 프로필 이름이나 접두사 없이 `스토리보드 타이틀.pdf`로 구성한다. 파일명에 사용할 수 없는 문자 치환, 길이 제한, 빈 이름 기본값은 유지하며 문서 본문과 제목 원본은 변경하지 않는다.

파일명 회귀 RED(프로필 접두사로 실패) 후 수정해 PDF 집중 테스트 5/5 통과. Angular 카드·다운로드 관련 21/21, Angular packaged build, Nest build/ncc bundle, 양쪽 diff check 통과. 실제 SCSS 샘플로 다크/라이트 200×270px, 샘플 텍스트 잘림 없음, 180px 컨테이너 축소 확인. 로그: /private/tmp/storyboard-title-filename-{red,green,build,bundle}.log 및 /private/tmp/storyboard-200-title-angular-{test,build}.log. 실행 앱에는 재빌드 후 반영. 코드·문서 미커밋, commit/push·실제 AI·Build5·서버 접속/배포 없음.


## W07 홈 스토리보드 카드 성별·연령층·스타일 표시

사용자 요청대로 홈 카드에서 합쳐진 시청 타겟을 제거하고, 분야 아래 구분선 다음에 성별과 연령층을 가로 한 줄로 배치했다. 이어서 제작 목적과 스타일을 표시한다. 잡 결과의 profileSnapshot.settingsV2에서 성별/연령/스타일을 읽고 기존 공통 카탈로그 레이블을 사용한다. 구조화된 타겟 정보가 없는 과거 결과는 임의 추정하지 않고 정보 없음으로 표시하며, 스타일은 기존 toneKeywords를 사용할 수 있다.

카드 너비 200px와 기존 글자 크기는 유지한다. 긴 스타일과 설명이 잘리지 않도록 줄바꿈하고 카드 높이는 최소 270px에서 내용에 맞춰 늘어난다. 성별/연령/스타일 매핑 및 표시 회귀 2건 RED 후 수정. Angular 관련 196/196, 스타일 6/6, packaged build, diff check 통과. 실제 카드 SCSS로 다크/라이트 샘플에서 구분선·성별/연령 같은 행·텍스트 잘림 없음·180px 축소 확인. 로그 /private/tmp/storyboard-card-demographics-{red,green,build,styles}.log.

백엔드/API/저장 contract 변경 없음. 실행 앱에는 재빌드 후 반영된다. 코드·문서 전부 미커밋이며 commit/push·실제 AI·Build5·서버 접속/배포 없음.


## W07 주제 목록 조사 근거 표시 제거

사용자 요청으로 주제 결과 카드의 `조사 근거` 펼침 영역 및 전용 스타일을 제거했다. 주제에는 기존 추천 이유·시청자의 궁금증·기획 포인트를 유지한다. 범위는 주제 화면 표시이며 저장 데이터, API, PDF 및 스토리보드 복사 내용은 변경하지 않았다. 근거가 있는 데이터로 기존 화면 테스트를 보완해 RED 확인 후 수정, 관련 Angular 4/4·packaged build·diff check 통과. 로그 /private/tmp/storyboard-hide-evidence-{red,green,build}.log. 앱 재빌드 후 반영. 코드·문서 미커밋, 커밋/푸시·실제 AI·Build5·배포 없음.
