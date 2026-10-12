# 9월 18일 대사 제목 생성·보정 변경의 정확한 이전/이후

조사일: 2026-09-29 KST. 사용자 annotation 5 후속 조사. commit과 바로 이전 parent의 git show/diff, 현행 파일, 관련 설계 문서 검색만 수행했다. 제품 수정, 실제 ML, 유료 API, fetch, 서버/build/test는 수행하지 않았다. 조사 결과와 사용자 방향은 `.codex` 인계 문서에 반영했다. 이 문서의 예시는 명시한 경우에만 원본 지시문이며, 나머지는 설명용 가상 사례다.

## 1. 먼저 이해할 변경

**두 줄과 줄당 18자 요구는 이전에도 있었다.** 9월 18일에는 제목의 역할을 바꾸고 조건부 재작성 기능을 추가했다.

- 이전: 장면 위의 편집 캡션. 두 줄에 서로 다른 구체 정보를 담고, 명사구나 짧은 절로 장면을 설명하도록 지시했다.
- 이후: 두 줄이 이어지는 숏폼 제목. 윗줄은 상황·궁금증·대상의 훅, 아랫줄은 핵심·반전·결과를 담도록 지시했다.
- 새 보정: 본문 생성이 성공한 뒤, 규칙상 나열형으로 잡힌 제목만 모아 추가 요청 한 번으로 다시 쓴다. 모든 제목이나 모든 품질 오류를 검사하는 기능은 아니다.

이 지시문이 실제 제목 품질을 얼마나 바꿨는지는 이번 조사에서 측정하지 않았다. 원본 주석은 예전 규칙이 키워드 나열을 낳았다고 설명하지만, 그것은 작성자의 변경 이유 기록이다. 동일 입력 A/B 성능 결과로 읽지 않는다.

## 2. Git 근거

| 항목 | 확인 값 |
|---|---|
| 변경 commit | af664d760a935c2f9660533ed408d343c77f0b0b |
| 바로 이전 parent | 9886f9681718b26ef4959aeab4e156bbb9fdaf5e |
| Author / Committer | 곽민준 <gwak0214@naver.com> — 분해형 Unicode 이름이며 본문에서는 곽민준으로 표기 |
| AuthorDate / CommitDate | 2026-09-18 22:23:04 +09:00 |
| subject | feat(dialog-highlight): overlay_title을 숏폼 제목처럼 + 나열형 제목 보정 패스 |
| Coauthor trailer | Claude Opus 5 (1M context) <noreply@anthropic.com>; 실제 Git author와 구분 |
| 변경 규모 | 6 files, 498 insertions / 34 deletions; 제품 파일 3개와 test 파일 3개 |
| 조사 당시 현행 WA HEAD | 31f448260148b11e61e9f53cad0ee9ac372345fe |

parent는 2026-09-18 15:13:01 +09:00, metabuzz-jinahan <jinahan@metabuzz.co.kr>의 auth 변경 commit이다. parent author를 제목 변경 author로 귀속시키지 않는다. 이 세 제품 파일은 af664d7과 현행 HEAD 사이 diff가 없었다.

직접 대조한 제품 파일:

1. [dialog-highlight-llm.prompts.ts](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:210)
2. [dialog-highlight-llm.service.ts](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:64)
3. [overlay-title-quality.ts](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:1) — parent에는 없던 새 파일

재현 가능한 읽기 명령:

    git show --format=fuller --stat af664d760a935c2f9660533ed408d343c77f0b0b
    git show 9886f9681718b26ef4959aeab4e156bbb9fdaf5e:src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts
    git diff 9886f9681718b26ef4959aeab4e156bbb9fdaf5e af664d760a935c2f9660533ed408d343c77f0b0b -- src/modules/dialog-highlight/application

아래 “이전 행”은 parent의 git show 출력 행이다. 파일 링크는 현행 파일이므로 역사 행을 현행 행이라고 혼동하지 않도록 함수명과 revision을 함께 적었다.

## 3. 생성 지시문은 무엇이 달라졌나

### 3.1 highlight_metadata: 제목의 관점이 변경됐다

| 항목 | 이전(parent, highlightMetadataPrompt) | 이후(현행) |
|---|---|---|
| 역할 | 장면 위 편집 캡션이며 영상 제목·요약 문장이 아니라고 명시(이전231–237행) | 영상 위 상·하단에 크게 얹는 숏폼 제목이라고 명시 |
| 두 줄 관계 | 두 줄에 서로 다른 정보를 담아 하나의 장면 설명 구성(이전239–242행) | line1 훅 + line2 핵심/반전/결과; 이어 읽으면 자연스러운 한 문장/한 구절 |
| 문장 형태 | 명사구 또는 짧은 절; 문장처럼 끝내기·마침표·종결 어미 금지(이전244–247행) | 구어체, 과하지 않은 물음표·느낌표 허용; 마침표는 금지 |
| 내용 | 추상 개념/일반화 금지; 실제 인물·숫자·행동·발언·실수·반응 우선(이전249–256행) | 근거 있는 이름 허용; 단어 나열/번호/해시태그/이모지/따옴표로 감싸기 금지 |
| 줄 수/길이 | 출력 강제 규칙상 line1/line2 두 줄. 입력 rules.titles 기본 lines=2,max_chars_per_line=18(이전227,287–288행) | 두 줄 요구 유지; 공통 작성 규칙에 줄당18자도 직접 명시 |
| 출력 key | highlights[].overlay_title.line1 / line2 | 그대로 유지 |
| count/range/canonical | 지정 highlights 수, clip_index/cand_index/start/end, candidate 맥락, 확실하지 않은 이름 금지 | 그대로 유지 |

현재 규칙과 변경 이유 주석은 [OVERLAY_TITLE_RULES](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:271)에 있다. 본문 생성은 [highlightMetadataPrompt](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:219)에서 이 공통 규칙을 펼친다. 기존 입력의 lines/max_chars_per_line 기본값도 [입력 rules](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:261)에 남아 있다.

원본 지시문의 짧은 요지: “편집 캡션·명사구”에서 “훅과 핵심을 이어 읽는 제목”으로 바뀌었다. 숫자나 구체 정보가 금지된 것으로 확대해 읽지 않는다. 번호를 매긴 나열을 금지하고, 확실한 이름과 근거 있는 결과를 사용하도록 한다.

출력 JSON 모양은 바뀌지 않았다. 두 revision 모두 highlights 항목에 clip_index, cand_index, start, end, content_summary, overlay_title, selection_reason, corrections_used를 보여주고, 최상위 video_summary도 요청한다. prompt는 이 모양을 요구하지만 Responses 요청 자체는 json_object 형식이므로 모든 highlight 필드를 strict schema로 강제하는 것은 아니다. [스키마 지시문](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:233), [Responses 형식](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:69).

### 3.2 define_highlight_topics: key·18자 제한은 유지하고 설명을 바꿨다

이전168–169행의 topic title_line1/title_line2는 “짧은 캡션 라인, 최대18자”였다. 이후에는 title_line1을 “윗줄 훅”, title_line2를 “아랫줄 핵심·반전”으로 설명하고 나열·기호 금지 문구를 추가했다. topics/summary/start_phrase/end_phrase JSON key, 선택 수와 STT 실제 phrase/25–55초 조건은 그대로다. [현재 topic schema](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:155).

### 3.3 select_highlights의 title은 이번에 변경되지 않았다

선택 응답은 selected[].cand_id, title, hook, reason을 요청한다. 이 지시문은 af664d7에서 변경되지 않았다. [selectHighlightsPrompt](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:183). 아래 UI에서 쓰는 최종 clip title과 이 selected[].title을 같은 필드라고 설명하면 안 된다.

## 4. 어떤 제목만 보정하는가

서비스는 highlight_metadata의 본 호출 성공 뒤에만 repairKeywordListTitles를 부른다. topics나 select_highlights는 이 보정을 받지 않는다. [분기](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:80).

각 highlights 항목을 모두 살펴보되, 다음 조건을 모두 만족한 항목만 items에 넣는다.

1. overlay_title.line1과 line2가 둘 다 string이다.
2. 둘 중 하나라도 looksLikeKeywordList가 true다.

따라서 전체 제목을 재작성하지 않는다. 의심 항목 여러 개를 한 배열에 모아 한 번 요청한다. 한 항목에서 한 줄만 의심돼도 두 줄 모두 repair 입력/응답에 포함한다. [수집 조건](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:171).

### 4.1 detector는 의미 판단 모델이 아니라 문자 규칙이다

lineLooksLikeList는 다음 중 하나면 true다. [정규식·상수](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:12), [판정 함수](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:23).

| 조건 | 범위 |
|---|---|
| 구분 기호/해시 문자 | ·, •, ASCII/전각 세로줄, /, # 중 하나라도 포함 |
| 원문자 번호 | ①–⑳ 또는 ❶–❿ 포함 |
| 번호형식 | 숫자 뒤 점/쉼표 나열 기호, 또는 공백/줄 시작 뒤 숫자와 “.”/“)” 및 공백 |
| emoji | Unicode Extended_Pictographic 포함 |
| comma tokens | ASCII/전각 쉼표로 나눈 토큰이3개 이상이며, 전부 비어 있지 않고 각각8 Unicode code points 이하 |

looksLikeKeywordList는 두 줄의 OR다. [두 줄 OR](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:32).

**설명용 가상 판정 사례(실제 모델 출력 아님)**:

| 제목의 한 줄 | 규칙 판정 | 의미 |
|---|---|---|
| 메모 · 회의 · 시간 | true | 단어 나열 |
| 입력/출력 비교 | true | 자연스러운 주제여도 slash 때문에 걸림 |
| C# 첫 수업 | true | 언어명이어도 # 때문에 걸림 |
| 1,000원으로 해본 일 | true | 천 단위 쉼표도 숫자+쉼표 규칙에 걸림 |
| 메모, 회의, 준비 | true | 짧은 comma 토큰3개 |
| 근데, 왜 줄었을까 | false | 일반적인 쉼표 하나는 해당 comma 조건이 아님 |
| 준비 시간이 줄었다. | false | 일반 마침표만으로는 detector가 잡지 않음 |
| 내용이 이어지는 장문의 제목 | 길이만으로 true가 되지 않음 | 18자 초과 여부는 이 detector의 호출 조건이 아님 |

이런 false positive는 코드 주석에서도 감수한다고 기록했다. 다만 “정상 제목 하나를 다시 쓸 뿐”이라는 주석은 비용·의미 변화 위험을 없앤다는 증명이 아니다. 현재 detector는 기호가 제목에서 어떤 의미인지 해석하지 않는다. 실제 false positive/negative 비율은 동일 evidence 평가로 측정해야 한다. [주석](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:2).

빈 줄, 누락된 줄, 길이 초과, 따옴표나 일반 마침표, 사실과 다른 내용만으로는 자동 repair 대상이 되지 않는다. 특히 한 줄이 string이 아니면 다른 줄이 나열형이어도 수집하지 않는다.

## 5. repair에 무엇을 보내고 무엇을 바꾸나

본 호출이 받은 전체 STT/canonical/candidate JSON을 다시 보내지는 않는다. 다음 항목을 보낸다.

- index: highlights 배열의 현재 위치 번호. clip_index/cand_index와 다른 이름이며 원본 위치를 매칭하는 용도다.
- content_summary: 해당 highlight의 내용 요약. 없거나 string이 아니면 빈 문자열.
- line1, line2: 현재 제목 두 줄.

[TitleRepairItem](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:300), [입력 수집](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:173).

titleRepairPrompt는 content_summary를 참고해 다시 쓰라고 하고, 본 호출과 같은 OVERLAY_TITLE_RULES를 사용한다. 응답은 titles[{index,line1,line2}]를 요구하며 입력에 없는 사실을 만들지 말라고 지시한다. [repair prompt](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:311). 요약에 오류가 있으면 원본 STT 대조 없이 따라갈 수 있으므로 “근거를 검증하는 독립 단계”라고 부르지 않는다.

**설명용 가상 입출력 예시(실제 API 결과 아님)**. “회의 메모 구조를 바꾼 뒤 준비 시간이 줄었다”라는 근거가 있는 고정 요약을 가정한다.

    repair 입력
    {"items":[{"index":0,"content_summary":"회의 메모 구조를 바꾼 뒤 준비 시간이 줄었다.","line1":"메모 · 회의 · 시간","line2":"준비 시간을 줄인 방법"}]}

    repair 응답 예시
    {"titles":[{"index":0,"line1":"회의 메모를 바꾸니","line2":"준비 시간이 줄었다"}]}

교체는 response index가 의심 항목 집합에 들어가고, 두 줄이 string이며, trim 뒤 nonempty/각18 code points 이내/나열형 아님일 때만 한다. [채택 검사](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:209), [isRepairedTitleAcceptable](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:37).

최종 payload는 highlights 해당 항목의 overlay_title.line1/line2만 바꾸고 나머지를 보존한다. clip_index, cand_index, start/end, content_summary, selection_reason, video_summary를 다시 생성하지 않는다. 좋은 항목과 불량/누락 replacement 항목의 기존 제목은 유지한다. [부분 교체](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:227).

채택 검사는 18자와 나열 여부를 확인하지만 자연스러운 연결, 훅의 매력, 원문 사실성, 따옴표·일반 마침표 금지를 모두 프로그램으로 검사하지는 않는다. main 생성 결과 전체의18자 제한도 이 함수로 검증하지 않는다.

## 6. 횟수·모델·시간·실패 처리

### 6.1 모델을 교체한 변경은 아니다

본 metadata는 HIGH 모델을 쓰고 default는 gpt-5-mini, medium effort, max_output_tokens16,000, timeout300초다. DIALOG_HIGHLIGHT_OPENAI_HIGH_MODEL 및 DIALOG_HIGHLIGHT_HIGH_TIMEOUT_MS로 override할 수 있다. 이 기본 모델/티어/상한은 af664d7에서 바뀌지 않았다. 실제 배포 env는 조회하지 않았다. [기본값](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:24), [modelFor](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:238), [timeoutMs](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:316).

repair는 **본 metadata가 실제 사용한 같은 model과 credential**을 받고, supportsReasoning일 때 minimal effort/max_output_tokens1,500을 붙인다. 일반 티어 env 모델을 새로 선택하는 게 아니다. 비추론 model이면 reasoning과 max_output_tokens를 붙이지 않는 현행 gating도 유지된다. [repair body](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:190).

### 6.2 한 번의 batched call

- 이전 metadata 요청: main provider call1회.
- 이후 metadata 요청: main1회 + 의심 제목이 있고 시간이 남을 때 repair 최대1회.
- 의심 제목이 여러 개여도 clip당 한 번씩 호출하지 않는다.
- repair 내부 retry/재귀 repair는 없다. 다른 계층의 Nest timeout retry로 main metadata 요청 자체가 반복되는 것은 별도다.

성공 로그에는 main usage와 repair replaced=N/M/usage가 각각 남는다. 본문과 보정을 합쳐 provider 비용을 평가해야 한다. 추가 요청을 “비용 없는 후처리”로 설명하지 않는다. [main 로그](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:82), [repair 로그](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:222).

### 6.3 repair 시간은 main token 잔량과 별개다

코드가 계산하는 예산은 시간이다.

    deadline = main startedAt + main timeoutMs + 15,000ms
    repair timeout = min(45,000ms, deadline - 현재시각)
    repair timeout < 5,000ms이면 skip

[deadline 계산](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:80), [남은 시간 계산](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:184).

default main300초 기준: 빠르게 끝나면 repair45초, main에290초가 걸렸으면25초, deadline까지3초만 남았으면 skip이다. “main의 남은16k tokens를 쓰는 단계”가 아니며 별도 요청에 출력1,500 token 상한을 준다. default Desktop330초보다 여유를 남기려는 설계다. env timeout을 바꾸거나 credential resolution/왕복/기타 overhead가 달라지면 전체 end-to-end 시간이315초로 엄격 보장되는 것은 아니다.

### 6.4 실패해도 본 성공 결과를 버리지 않는다

- 의심 항목 없음: 추가 요청 없이 main 결과 반환.
- 잔여시간5초 미만: 경고 로그 후 main 결과 반환.
- repair HTTP 실패/timeout/예외/JSON 파싱 실패/불완전 결과: catch 경고 후 main 결과 반환.
- titles 배열 없음/잘못된 index/비문자열/빈 줄/18자 초과/계속 나열형: 해당 replacement를 채택하지 않음.
- 일부만 적합: 해당 제목만 교체, 나머지 원문 유지.

[fail fallback](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:200), [replacement 필터](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:209). main 호출 자체 실패는 이 fallback의 대상이 아니며 기존 provider_failed 처리를 따른다.

## 7. 화면의 title과 overlay_title을 어떻게 소비하나

이 commit은 Web API3개 제품 파일만 바꿨다. 아래 소비자 변경은 같은 시기의 별도 Python/Nest/Angular commit에서 이루어졌으며 af664d7에 모두 들어 있는 것으로 설명하지 않는다.

| 필드 | 현재 흐름 |
|---|---|
| topics[].title_line1/2 | topic 설명·문맥의 제목. 이 이름을 화면 clip.title로 직접 읽지는 않음 |
| selected[].title | selection 응답 필드. metadata 입력을 만들 때 selected ID로 원본 candidates를 찾으며 이 title을 전달하지 않음 |
| highlights[].overlay_title.line1/2 | metadata가 생성/보정한 최종 두 줄. Python이 manifest.clip_titles에 복사 |
| ProjectClipItem.title | Nest가 highlights_meta.overlay_title 두 줄을 공백으로 이어 만든 목록/클립 정보용 문자열. 없으면 “클립 N” |
| ProjectClipItem.overlayTitle | manifest.clip_titles 우선, 없을 때 legacy highlights_meta 두 줄. 빈 manifest 값도 존중 |
| 숏폼 topTitle/bottomTitle | Angular가 선택 clip.overlayTitle에서 처음 seed; 사용자 편집 후 Map 값을 유지 |

근거:

- [selected ID만으로 metadata 후보 준비](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/dialog-highlight/application/dialog-highlight-selection-metadata.ts:1)
- [Python overlay title 위치 매칭·clip_titles 복사](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/staged_artifacts.py:590)
- [manifest 제목 계약](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/pipeline/common.py:407)
- [Nest 목록 title 결합](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/projects/application/project-detail-builder.ts:122)
- [Nest overlayTitle 우선순위](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/projects/application/project-detail-builder.ts:251)
- [Angular 목록의 clip.title](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/dialog-result-detail/dialog-result-detail.component.html:32)
- [Angular 클립 정보의 clip.title](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/projects/dialog-result-detail/dialog-result-detail.component.html:76)
- [Angular 숏폼 기본값 seed](/Users/jina/project/adlight/desktop/clipper_angular/src/features/highlight-shortform/services/highlight-shortform-draft.ts:138)

설명용 가상 예시의 두 줄은 목록에서 “회의 메모를 바꾸니 준비 시간이 줄었다”로 이어 보이고, 숏폼에는 topTitle/bottomTitle로 분리된다. 사용자가 숏폼 제목을 편집해도 원래 highlights_meta와 목록 title이 자동으로 함께 바뀌는 계약은 아니다. 새 raw clip은 제목을 영상 파일에 미리 태우지 않는다.

## 8. 관련 설계 문서 검색 결과

검색 범위는 .codex와 Web API/Nest/Angular/Python의 docs 아래 Markdown, filename의 dialog/highlight/title, 내용의 titleRepair/TITLE_REPAIR/나열형/편집 캡션/overlay_title/제목 보정이다. Web API docs에는 이 검색어의 일치가 없었다. 이 범위에서 **af664d7의 prompt/repair 규칙을 따로 정한 전용 Web API spec/plan은 찾지 못했다**. “어디에도 문서가 없다”라고 확대하지 않는다.

관련 소비자 설계는 존재한다. [2026-09-18 highlight-to-shortform-design](/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/specs/2026-09-18-highlight-to-shortform-design.md:9)는 제목을 입힌 숏폼 생성 목적과 상·하단 제목의 template main_title1/main_title2 mapping(:20), 입력칸(:29), topTitle/bottomTitle(:69)을 정의한다. [phase1 plan](/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/plans/2026-09-18-highlight-to-shortform-phase1.md:11)도 이 설계를 참조한다. 이 문서는 나열형 detector/repair 모델·45초/1,500token을 설명하는 전용 spec은 아니다.

원본 Git commit 본문, [prompt 변경 이유 주석](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.ts:271), [detector 주석](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.ts:2), [repair budget 주석](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.ts:159)이 현재 확인한 직접 설계 이유다. 9/29 W12 기록은 후행 조사 자료다.

코드에 추가된 tests는 규칙·조건·fallback·시간 계산을 검증하도록 작성돼 있다. [prompt spec](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.prompts.spec.ts:9), [detector spec](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/overlay-title-quality.spec.ts:3), [repair service spec](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts:371), [시간 계산 spec](/Users/jina/project/adlight/web/clipper_web_api/src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts:513). 이번 후속 조사는 test 내용을 읽었고 실행하지 않았다.

## 9. 사용자에게 설명할 때의 표현

“원래도 두 줄18자였습니다. 예전에는 구체적인 장면 캡션을 만들라고 했고, 지금은 윗줄 훅과 아랫줄 핵심이 이어지는 숏폼 제목을 만들라고 합니다. 생성 뒤 나열형으로 판정된 제목만 한 번에 다시 쓰지만, 사실성이나 모든 길이 오류를 자동 검수하는 기능은 아닙니다.”

품질 비교는 같은 STT·canonical·candidate·범위를 고정하고 이전 지시문, 새 지시문만, 새 지시문+repair를 나눠 봐야 한다. 실제 title grounding/가독성/훅/18자 준수/false positive와 추가 지연·provider 비용의 개선·악화는 아직 미측정이다.
