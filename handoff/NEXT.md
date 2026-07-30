# Next Handoff

최신 갱신: 2026-07-30 KST

## 현재 목표

AI 디렉터는 운영 프로필부터 실제 조사·레퍼런스 정밀 분석·영상 후보·영상 기획·소재
준비·최종 렌더까지 실제 provider E2E를 완료했다. 다음 목표는 2026-07-30에 구현한
시각 구성 보완을 새 앱에서 다시 검증해, 모든 장면에 실제 기본 시각 소재가 보이고 내부
선택 이유가 화면에 노출되지 않는 결과 영상을 확인하는 것이다.

## 먼저 읽을 문서

1. `.codex/AGENTS.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/records/sessions/2026/07/30.md`
4. `.codex/design/SHORTFORM_DIRECTOR_VISUAL_COMPOSITION_QUALITY_REPAIR_DESIGN_2026-07-30.md`
5. `.codex/design/SHORTFORM_DIRECTOR_VISUAL_COMPOSITION_QUALITY_REPAIR_IMPLEMENTATION_PLAN_2026-07-30.md`
6. `.codex/records/sessions/2026/07/29.md`
7. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_DESIGN_2026-07-29.md`
8. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_IMPLEMENTATION_PLAN_2026-07-29.md`

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

- LLM이 운영 프로필, 집중 키워드, 관련 Google Trends 신호를 바탕으로 YouTube 검색어
  하나를 만든다. `shorts`, `쇼츠`, `챌린지`를 코드에서 강제로 덧붙이지 않는다.
- 동일 검색어로 최근 30일 범위의 `viewCount`와 `relevance` lane을 각각 요청한다.
- 각 lane은 `maxResults=40`, `videoDuration=short`, `regionCode=KR`,
  `relevanceLanguage=ko`다.
- 최대 80개 검색 결과를 중복 제거하고, 중복 제거된 모든 video ID를
  `https://www.youtube.com/shorts/{videoId}`로 확인한다.
- `200 + redirect 없음`만 Shorts로 포함한다. 해당 ID의 `/watch?v=`로 리다이렉트되면
  일반 영상으로 제외하며 나머지는 `unverified`로 기록한다.
- 길이 3분/4분 같은 임의 컷으로 Shorts 여부를 결정하지 않는다.
- 확인된 Shorts는 임의로 6개만 자르지 않고 모두 JSON과 화면에 남긴다.
- 분석 선택 상한은 5개다. 추천은 참고 표시일 뿐 자동 선택되지 않는다.

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
- Desktop Nest: `34f0635`, `24d6422`, `bde4edc`, `b99cd59`
- Angular: `a3c50c6`

## 최신 자동 검증

2026-07-30 KST에 외부 provider 호출 없이 다음을 새로 실행했다.

- Web API 전체: `120` suite, `1003` test 통과, `npm run build` 통과
- Desktop Nest AI 디렉터 전체: `687` test 중 `685` 통과, 실패 `0`,
  환경 의존 로컬 렌더 `2`개 의도적 skip, `npm run build` 통과
- Motion Canvas production bundle build 통과
- Angular 전체: `1813/1813` 통과, `npm run build` 통과

## 바로 다음 실제 E2E

1. Web API를 재시작하고 Electron 앱을 다시 빌드한다.
2. 기존 조사·주제·후보는 재사용한다.
3. 기존 영상 후보 하나를 다시 선택해 `영상 기획 만들기`부터 새 프로젝트를 생성한다.
   기존 완료 프로젝트는 구형 장면 결정이 저장돼 있으므로 단순 재렌더만 하지 않는다.
4. OpenAI 두 호출 범위와 예상 비용을 화면에서 확인하고 사용자가 승인한다.
5. 새 기획의 각 장면에 외부 기본 시각 소재 요구사항이 있는지 확인한다.
6. 소재 준비 preflight에서 실제 장면별 Naver/Gemini 호출 수와 예상 비용을 확인하고
   사용자가 승인한다.
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
| `web/clipper_web_api` | `feat/shortform-director-foundation` | `0150966` | origin보다 24 commit ahead |
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` | `b99cd59` | origin보다 54 commit ahead |
| `desktop/clipper_angular` | `feat/shortform-director-foundation` | `a3c50c6` | origin보다 26 commit ahead |
| `desktop/clipper_electron` | `dev` | `4cd7f98` | origin과 동기화 |
| `web/clipper_web_admin` | `feat/shortform-director-foundation` | `d8b2580` | origin과 동기화 |
| `clipper_docs` | `main` | `993d054` | origin과 동기화 |
| `.codex` | `main` | 이 NEXT와 세션 기록을 포함한 로컬 commit | commit 전 origin보다 13 commit ahead |

코드 저장소는 최신 확인 시 clean이다. `.codex`만 이 handoff와 세션 기록 변경을 커밋한다.
push는 하지 않는다.

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
