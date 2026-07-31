# Next Handoff

최신 갱신: 2026-07-31 KST

## 현재 목표

AI 디렉터는 운영 프로필부터 실제 조사·레퍼런스 정밀 분석·영상 후보·영상 기획·소재
준비·최종 렌더까지 실제 provider E2E를 완료했다. 운영 프로필에 `꾸미기`와 `방 구하기`
같은 서로 다른 목적이 함께 있어도 이를 하나의 긴 YouTube 검색어로 합치지 않고, 최대
2개의 독립된 조사 범위로 나누도록 2026-07-31에 보완했다. 다음 목표는 새 앱에서 새
조사를 실행해 실제 query-plan과 YouTube 결과가 의도별로 분리되는지 확인하고, 이어서
부분 레퍼런스 성공 분기와 2026-07-30 시각 구성 보완을 실제로 재검증하는 것이다.

## 먼저 읽을 문서

1. `.codex/AGENTS.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/records/sessions/2026/07/31.md`
4. `.codex/design/SHORTFORM_DIRECTOR_MULTI_INTENT_RESEARCH_QUERY_DESIGN_2026-07-31.md`
5. `.codex/design/SHORTFORM_DIRECTOR_MULTI_INTENT_RESEARCH_QUERY_IMPLEMENTATION_PLAN_2026-07-31.md`
6. `.codex/design/SHORTFORM_DIRECTOR_PARTIAL_REFERENCE_CONTINUATION_DESIGN_2026-07-31.md`
7. `.codex/design/SHORTFORM_DIRECTOR_PARTIAL_REFERENCE_CONTINUATION_EXECUTION_PLAN_2026-07-31.md`
8. `.codex/records/sessions/2026/07/30.md`
9. `.codex/design/SHORTFORM_DIRECTOR_VISUAL_COMPOSITION_QUALITY_REPAIR_DESIGN_2026-07-30.md`
10. `.codex/design/SHORTFORM_DIRECTOR_VISUAL_COMPOSITION_QUALITY_REPAIR_IMPLEMENTATION_PLAN_2026-07-30.md`
11. `.codex/records/sessions/2026/07/29.md`
12. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_DESIGN_2026-07-29.md`
13. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_IMPLEMENTATION_PLAN_2026-07-29.md`

이전 품질 입력 아키텍처 맥락이 필요할 때만 2026-07-24 문서들을 추가로 읽는다.

## 확정된 사용자 흐름

```text
운영 프로필
  → 최신 조사 사전 점검과 사용자 비용 승인
  → Google Trends RSS + 네이버 뉴스·DataLab + YouTube를 함께 조사
  → 확인된 Shorts 전체 표시
  → 사용자가 정밀 분석 영상 0~5개 선택
      ├─ 0개: 시장 근거만으로 주제 생성
      └─ 1~5개: 비용 승인 후 실제 영상 정밀 분석
  → 조사 주제
  → 주제별 최소 10개 영상 후보
  → 영상 후보 선택
  → VideoPlan·장면별 매체 결정·소재 준비
  → 렌더
  → 기존 보관함 큐
```

- 정밀 분석은 선택 사항이다. 기본 선택은 0개이며 추천 영상도 자동 선택하지 않는다.
- 사용자가 분석을 건너뛰어도 source-normalization의 시장 근거 전체가 topic synthesis와
  후보 생성에 전달된다.
- 정밀 분석을 하면 실제 영상, 기존 로컬 STT, 댓글과 프레임을 사용한 분석 결과가
  reference pattern으로 추가된다.
- 조사·검증·LLM 호출 결과는 기존 로컬 파일시스템 JSON 저장소에 남는다.
- 화면은 사람이 읽는 요약을 먼저 보여주고 기술 정보와 원본 JSON은 기본 접힘 상태다.
- AI 디렉터의 기존 크레딧 차감과 새 크레딧 차감은 없다. 비용 사전 점검과 provider 사용량
  기록은 크레딧 차감과 별개로 유지한다.

## YouTube discovery의 현재 계약

- LLM이 운영 프로필, 집중 키워드, 관련 Google Trends 신호를 바탕으로 서로 겹치지 않는
  YouTube 조사 범위를 1~2개 만든다. 여러 목적을 하나의 긴 검색어로 이어 붙이지 않으며,
  `focusKeyword`가 있으면 가장 우선한다.
- 각 조사 범위는 사람이 읽는 이름, 실제 검색어, 이 검색어를 고른 이유를 가진다.
  `shorts`, `쇼츠`, `챌린지`를 코드에서 강제로 덧붙이지 않는다.
- 각 범위마다 같은 검색어로 최근 30일 범위의 `viewCount`와 `relevance` lane을 모두
  요청한다. 한 범위가 0건이어도 다음 범위를 생략하지 않는다.
- 각 lane은 `maxResults=40`, `videoDuration=short`, `regionCode=KR`,
  `relevanceLanguage=ko`다. 최대 2개 범위이므로 `search.list`는 최대 4회다.
- 최대 160개 검색 결과를 중복 제거하고, 중복 제거된 모든 video ID를
  `https://www.youtube.com/shorts/{videoId}`로 확인한다.
- `200 + redirect 없음`만 Shorts로 포함한다. 해당 ID의 `/watch?v=`로 리다이렉트되면
  일반 영상으로 제외하며 나머지는 `unverified`로 기록한다.
- 길이 3분/4분 같은 임의 컷으로 Shorts 여부를 결정하지 않는다.
- 확인된 Shorts는 임의로 6개만 자르지 않고 모두 JSON과 화면에 남긴다.
- 분석 선택 상한은 5개다. 추천은 참고 표시일 뿐 자동 선택되지 않는다.
- 화면의 조사 근거에는 각 범위의 이름·검색어·선정 이유와 각 API 호출의 실제 `q`,
  정렬 기준, 최대 요청 수, 실제 결과 수를 표시한다. 후보 카드의 `수집 근거 보기`에서도
  같은 정보를 사람이 읽는 형태로 확인하고 원본 JSON은 접어서 열 수 있다.
- 아직 레퍼런스를 한 개도 선택하지 않은 정상 실행의 분석 목록은 404가 아니라 빈 배열이다.
  존재하지 않는 조사 실행만 404다.

## 2026-07-31 다중 목적 조사 범위 구현

- Web API query-plan을 `shortform-director.query-plan.v3`로 올렸다.
- Naver 뉴스 검색어와 YouTube 조사 범위를 분리했으며 YouTube 범위는 1~2개다.
- Desktop Nest가 범위마다 조회수순 40개와 관련도순 40개를 수집하고, 최대 160개의 모든
  고유 video ID를 Shorts URL로 확인한다.
- Shorts 검증 artifact는 v2로 확장해 모든 조사 범위를 저장하되, 기존 v1 artifact와 후보
  스냅샷은 계속 읽을 수 있다.
- 같은 영상이 여러 범위에서 발견되면 영상 검증은 한 번만 하고, 발견된 모든 source-call
  artifact 연결은 보존한다.
- 후보 관련도는 실제로 그 영상을 발견한 검색어들을 기준으로 계산한다.
- 기존 실행 JSON은 수정하지 않는다. 새 계약은 새 조사 실행부터 적용된다.

구현 커밋:

- Web API: `29871e7`
- Desktop Nest: `9bf6205`, `d661edd`, `d239795`, `a578dce`
- Angular: `c82489a`

### 바로 다음 실제 앱 재검증

1. 최신 Desktop Nest와 Angular/Electron을 빌드해 앱을 실행한다.
2. `꾸미기 + 방 구하기`처럼 목적이 둘인 프로필로 새 조사 사전 점검을 연다.
3. 조사 근거에서 `원룸 인테리어·수납`과 `자취방 구하기 체크리스트`처럼 의미가 다른
   범위가 각각의 짧은 검색어로 분리됐는지 확인한다.
4. 각 범위에 조회수순·관련도순 호출이 있고, 실제 `q`, 최대 40개 요청, 실제 결과 수가
   표시되는지 확인한다.
5. 확인된 Shorts와 각 후보의 `수집 근거 보기`에서 어느 범위·정렬 결과로 발견됐는지
   확인한다.
6. 유료 provider 호출 전에는 앱 preflight의 범위·호출 수·예상 비용을 확인하고 사용자
   화면 승인 뒤에만 실행한다.

## 2026-07-31 부분 레퍼런스 성공 자동 진행

- 선택한 레퍼런스의 정밀 분석 중 하나 이상이 검증을 통과하면, 성공한 분석만
  `reference-pattern-synthesis` 입력에 포함해 주제 종합을 자동으로 계속한다.
- 이때 child 분석 attempt는 실제 결과대로 `partial`로 남아도 부모 조사는 자체 discovery
  실패가 없는 한 `succeeded`로 끝난다.
- 선택한 모든 분석이 실패하면 부모 조사는 `awaiting_reference_selection`에 남는다. 사용자는
  실패 영상 재시도, 다른 영상 선택, 또는 정밀 분석 없이 계속(시장 근거만 사용)을 선택할 수
  있다.
- 화면은 모든 분석이 끝난 뒤 `레퍼런스 N개 중 M개 분석 성공 · K개 실패` 요약을 보여준다.
  성공 0개일 때는 위 세 선택지를 설명한다. 부분 성공 뒤 부모 종합 중에는 Angular가 계속
  폴링하며, 분석 목록 요청이 일시적으로 실패하면 현재 상태를 지우지 않고 재시도한다.
- 부모 종합·완료 확인이 진행 중인 동안에는 명시적인 reconciliation 잠금이 유지되어, child가
  이미 `partial`이어도 레퍼런스 선택 변경으로 현재 폴링이 취소되지 않는다. 정상적인
  `레퍼런스 선택 대기` 상태에서는 그대로 편집할 수 있다.
- reconciliation 잠금 중에는 기존 승인 preflight가 화면에 남아 있어도 정밀 분석 시작을
  다시 요청할 수 없다. 스토어의 직접 호출과 화면 승인 버튼 모두 같은 잠금을 사용한다.
- 부모가 완료된 뒤 분석 목록의 로컬 조회만 실패하면 부모·attempt·topic을 다시 조회하지
  않는다. 목록만 최대 3회 재시도하며, 성공 또는 한도 소진 뒤 잠금과 타이머를 해제한다.
- 구현·자동 검증은 외부 provider를 호출하지 않았다. 실제 앱 재검증은 새 partial attempt 또는
  기존 재현 가능한 조사에서 아래 순서대로 한다.

### 바로 다음 실제 앱 재검증

1. 최신 Desktop Nest와 Angular/Electron 빌드로 앱을 실행하고 운영 프로필에서 조사를 시작한다.
2. Shorts 2~5개를 선택해 정밀 분석을 승인한다.
3. 일부만 성공한 경우, 성공 분석만으로 자동 종합되어 `조사 결과 주제`가 표시되는지 확인한다.
   부모 조사는 `완료`, 개별 attempt는 `부분 완료`일 수 있으며 화면에는 성공/실패 요약이 남아야
   한다.
4. 전부 실패한 경우, 부모가 `레퍼런스 선택 대기`에 머무르고 `정밀 분석 없이 계속`, 재시도,
   교체 중 하나를 선택할 수 있는지 확인한다.
5. 각 재검증 전 실제 외부 provider 호출 범위·모델·예상 비용을 앱 preflight에서 확인하고
   사용자 승인 뒤에만 실행한다.

## 2026-07-29 구현 커밋

`web/clipper_web_api`

- `0a80e14` `feat: expand shortform YouTube discovery`
- `c8696c8` `feat: expand shortform video details batch`
- `0239779` `feat: support market-only topic synthesis`

`desktop/clipper_nestjs`

- `abf49ec` `feat: verify public YouTube Shorts`
- `f841266` `feat: collect all verified Shorts references`
- `8416bb5` `feat: retain all verified Shorts candidates`
- `817fabc` `feat: support one to five reference analyses`
- `569576a` `feat: continue research without reference analysis`

`desktop/clipper_angular`

- `29f0a00` `feat: make reference analysis optional`
- `9341050` `feat: explain YouTube Shorts validation`

## 2026-07-30 실제 E2E와 시각 구성 보완

- 사용자가 실제 credential과 화면 비용 승인을 사용해 조사부터 최종 렌더까지 실행했다.
- 코딩·엔터테인먼트 프로필의 최종 영상에서 다음 문제가 확인됐다.
  - 코딩 영상: 도식 과다, 내부 매체 선택 이유가 화면 문구로 노출
  - 엔터테인먼트 영상: 다수 장면에 외부 시각 소재가 없어 빈 배경처럼 표시
- 원인은 Naver 검색 실패가 아니라 단일 `medium` 계약이 도식·텍스트를 장면의 유일한
  매체로 선택하게 한 구조였다.
- 신규 장면 계약은 `baseMedium + overlayMode`로 분리했다.
- 모든 신규 장면은 외부 기본 시각 소재를 하나 가지며 도식·kinetic typography는
  overlay로만 사용한다.
- `decision.rationale`은 감사 기록에만 남고 화면 문구로 컴파일되지 않는다.
- 도식은 비교·순서·루프·수치별 실제 레이아웃을 사용하며 수량과 연속 배치가 제한된다.

구현 커밋:

- Web API: `0150966`
- Desktop Nest: `34f0635`, `24d6422`, `bde4edc`, `b99cd59`, `9a19219`
- Angular: `a3c50c6`

실제 소재 준비에서 source layer 전체 실패를 추가로 확인해 보완했다.

- 내부 production source ID가 이미지 검색어로 사용된 것이 직접 원인이었다.
- 여러 ID가 합쳐진 요청은 Web API 100자 제한으로 HTTP 400이 됐다.
- 짧은 요청도 내부 ID 검색이라 결과가 없었다.
- 뉴스 이미지 CDN 호스트가 기사 호스트와 달라 정상 후보가 제거되는 문제도 있었다.
- 이제 실제 출처 제목으로 100자 이내 검색하며, 기사 도메인으로 검색된 CDN 이미지도
  후보로 허용한다.
- 기존 실패 프로젝트의 acquisition은 retryable이므로 새 앱에서 그대로 재시도할 수 있다.

같은 프로필의 신규 후보 영상 기획에서 장면 미디어 결정 응답 검증 실패도 확인해
보완했다.

- 실제 실패 실행:
  `run.director.5e2deb81cf1e40b0b3e5fbcbc4048247`
- 첫 상세 영상 기획 호출은 성공했고, 두 번째 장면 미디어 결정 호출의
  `/decisions/2/programmaticBrief/values`만 계약 불일치로 거절됐다.
- provider schema는 비수치 도식에도 숫자 배열을 허용하지만 로컬 검증은 null만
  허용하던 불일치가 원인이었다.
- 이제 비교·순서·루프는 `values: null`, 수치 도식만 숫자 배열을 낼 수 있도록
  provider schema 자체를 variant별로 분리했다.
- Web API 커밋: `9c53d8e`

## 최신 자동 검증

2026-07-31 KST에 외부 provider 호출 없이 다음을 새로 실행했다.

- Web API 전체: `120` suite, `1004` test 통과, `npm run build` 통과
- Desktop Nest AI 디렉터 전체: `699` test 중 `697` 통과, 실패 `0`,
  환경 의존 로컬 렌더 `2`개 의도적 skip, `npm run build` 통과
- Angular 전체: `1825/1825` 통과, `npm run build` 통과
- Web API 전체 테스트를 Desktop Nest와 동시에 처음 실행했을 때 구현과 무관한 인증
  선행검사 1개가 5초 timeout을 넘겼다. Web API만 단독으로 즉시 재실행했을 때
  `1004/1004`가 통과해 재현되지 않았다.

## 바로 다음 실제 E2E

1. Web API의 새 장면 미디어 response schema가 반영되도록 개발 서버의 재로딩 상태를
   확인한다. `start:dev`라면 파일 변경으로 자동 재시작된다.
2. 후보
   `candidate.director.5a030ee6707f4980b84cfa8168c1ac8d`의 `영상 기획 만들기`를
   다시 승인한다. 기존 실패 run은 보존되고 새 run/project가 생성된다.
3. Electron 앱을 최신 Desktop Nest 코드로 다시 빌드하고 실행한다.
4. 실패했던 프로젝트
   `shortform_director_project_2e526ca7-b590-4934-901e-273845c1e7de`의 소재 준비를
   그대로 다시 실행한다. 새 VideoPlan이나 OpenAI 호출은 필요 없다.
5. 새 사전 점검과 Naver 호출 범위를 확인하고 사용자가 승인한다.
6. 검색된 source 이미지는 권리 확인 후 렌더 가능 상태가 되는지 확인한다.
7. 렌더 후 다음을 확인한다.
   - 모든 장면에 실제 이미지 또는 영상 기본 배경이 있다.
   - 내부 매체 선택 이유가 화면 문구로 나오지 않는다.
   - 도식은 일부 장면의 overlay로만 보인다.
   - 비교·순서·루프·수치 도식은 서로 다른 레이아웃이다.
   - 준비되지 않은 시각 소재가 있으면 렌더를 시작하지 않는다.

유료 provider 호출 직전에는 앱의 사전 점검에 표시된 provider·모델·최대 호출 수·예상
비용을 사용자에게 먼저 보여주고 화면 승인을 받는다.

## 저장소 기준점

| 저장소 | branch | expected HEAD | upstream 상태 |
|---|---|---|---|
| `web/clipper_web_api` | `feat/shortform-director-foundation` | `29871e7` | origin보다 26 commit ahead |
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` | `a578dce` | origin보다 61 commit ahead |
| `desktop/clipper_angular` | `feat/shortform-director-foundation` | `c82489a` | origin보다 34 commit ahead |
| `desktop/clipper_electron` | `dev` | `4cd7f98` | origin과 동기화 |
| `web/clipper_web_admin` | `feat/shortform-director-foundation` | `d8b2580` | origin과 동기화 |
| `clipper_docs` | `main` | `993d054` | clean, origin보다 1 commit behind |
| `.codex` | `main` | 이 handoff를 포함한 현재 HEAD | push 전 `git rev-list --left-right --count '@{upstream}...HEAD'`로 재확인 |

코드 저장소는 최신 확인 시 clean이다. `.codex`만 이 handoff와 세션 기록 변경을 커밋한다.
push는 하지 않는다.

다음 세션에서 기준점을 확인할 때는 각 저장소에서 `git status --short`,
`git rev-parse --short HEAD`, `git rev-list --left-right --count '@{upstream}...HEAD'`를 실행한다.

`legacy/adlight_python`의 `fastapi_server.spec` 기존 변경은 사용자 변경이다. 절대
reset/revert하거나 이번 작업에 포함하지 않는다.

## 안전 경계

- 기존 `shortform_prompt` 플러그인은 수정하지 않는다.
- Vira 서비스·DB는 이번 실제 조사 경로에 연결하지 않는다.
- Google Trends 공식 API는 사용자가 alpha 선정 사실을 알려주기 전까지 사용하지 않는다.
- Google Trends는 공식 Trending RSS만 사용하며 관련 신호가 없으면 주제 근거로 억지
  채택하지 않는다.
- 실제 키, JWT, cookie, env 값은 출력하거나 JSON artifact에 저장하지 않는다.
- API 키는 Electron/env에 직접 넣지 않고 기존 관리자 페이지 → Web API credential
  구조만 사용한다.
- 새 문서는 `.codex`에만 작성한다.
- 예상 밖 변경은 reset/revert하지 않고 먼저 보고한다.
- 실제 유료 provider 호출은 화면 사전 점검과 사용자 승인 뒤에만 실행한다.
