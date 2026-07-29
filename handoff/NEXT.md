# Next Handoff

최신 갱신: 2026-07-29 KST

## 현재 목표

AI 디렉터를 운영 프로필 생성부터 최신 시장 조사, 선택적 레퍼런스 정밀 분석, 최소 10개
영상 후보, 장면 설계·소재 준비·렌더·보관함 큐까지 실제 앱에서 끝까지 검증한다.

입력단의 새 Shorts discovery 구현과 자동 회귀 검증, 새 macOS arm64 앱 패키징은
완료했다. 다음 작업은 fixture나 더미 응답이 아니라 사용자가 화면에서 비용을 승인한 실제
provider E2E다.

## 먼저 읽을 문서

1. `.codex/AGENTS.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/records/sessions/2026/07/29.md`
4. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_DESIGN_2026-07-29.md`
5. `.codex/design/SHORTFORM_DIRECTOR_VERIFIED_SHORTS_DISCOVERY_AND_OPTIONAL_REFERENCE_ANALYSIS_IMPLEMENTATION_PLAN_2026-07-29.md`
6. `.codex/design/SHORTFORM_DIRECTOR_DISCOVERY_RELEVANCE_AND_QUERY_ROUTING_DESIGN_2026-07-29.md`
7. `.codex/design/SHORTFORM_DIRECTOR_REFERENCE_VIDEO_DEEP_ANALYSIS_DESIGN_2026-07-29.md`

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

## 최신 자동 검증

2026-07-29 KST에 Node 22로 다음을 새로 실행했다.

- Web API shortform research/inference: `408/408` 통과, `npm run build` 통과
- Desktop Nest shortform 전체: `670` 통과, 실패 `0`, 의도적 skip `2`,
  `npm run build` 통과
- Angular AI Director 전체: `303/303` 통과, `npm run build` 통과
- Electron `npm run build:app:mac:arm64:local-api` 통과
- 새 앱:
  `desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio.app`

샌드박스 안의 Web/Nest/Karma HTTP 경계 테스트는 로컬 포트 바인딩 `EPERM`이 발생해
동일 명령을 권한 환경에서 재실행했다. 코드 실패는 없었다.

Angular의 로컬 영속 캐시는 32.39GB이며 LMDB가 종료 시 SIGABRT를 냈다. 파일을 삭제하지
않고 `CI=1`로 해당 검증·패키징 실행에서만 영속 캐시를 껐고 빌드는 통과했다. 별도 유지보수
작업에서 캐시 정리 여부를 사용자에게 확인한다.

## 바로 다음 실제 E2E

Web Admin과 Web API 개발 서버는 사용자가 실행 중이다. Clipper 앱 프로세스는 마지막 확인
시 실행 중이지 않았다. 실행 중인 서버를 임의 종료하거나 재시작하지 않는다.

1. 새로 패키징된 `Clipper Studio.app`을 연다.
2. 기존 운영 프로필에서 `아이디어 찾기`로 이동한다.
3. 집중 키워드를 입력하고 discovery 비용 사전 점검 내용을 사용자에게 보여준다.
4. 사용자가 화면에서 승인한 뒤 실제 discovery를 실행한다.
5. 다음을 화면과 로컬 JSON 양쪽에서 확인한다.
   - YouTube 두 lane이 각각 40개·최근 30일 조건으로 호출됐는지
   - 중복 제거된 모든 ID의 Shorts URL 검증 결과
   - 확인된 Shorts 전체 목록
   - Google Trends·네이버 뉴스·DataLab·YouTube·LLM 근거의 사람이 읽는 요약
6. 사용자가 다음 둘 중 실제로 검증할 경로를 고른다.
   - 0개 선택 후 `정밀 분석 없이 계속`
   - 1~5개 선택 후 정밀 분석 비용 승인
7. 주제와 최소 10개 영상 후보가 실제 근거 내용을 사용했는지 확인한다.
8. 영상 후보 하나를 골라 VideoPlan → 소재 준비 → 렌더 → 보관함 큐까지 검증한다.

유료 provider 호출 직전에는 앱의 사전 점검에 표시된 provider·모델·최대 호출 수·예상
비용을 사용자에게 먼저 보여주고 화면 승인을 받는다.

## 저장소 기준점

| 저장소 | branch | expected HEAD | upstream 상태 |
|---|---|---|---|
| `web/clipper_web_api` | `feat/shortform-director-foundation` | `0239779` | origin보다 19 commit ahead |
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` | `569576a` | origin보다 43 commit ahead |
| `desktop/clipper_angular` | `feat/shortform-director-foundation` | `9341050` | origin보다 24 commit ahead |
| `desktop/clipper_electron` | `dev` | `4cd7f98` | origin과 동기화 |
| `web/clipper_web_admin` | `feat/shortform-director-foundation` | `d8b2580` | origin과 동기화 |
| `clipper_docs` | `main` | `993d054` | origin과 동기화 |
| `.codex` | `main` | 이 NEXT와 세션 기록을 포함한 로컬 commit | commit 전 origin보다 7 commit ahead |

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
